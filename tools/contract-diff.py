#!/usr/bin/env python3
"""contract-diff: detect BREAKING vs ADDITIVE changes between two revisions of
ODCS-flavoured contract YAML.

Usage:
    python tools/contract-diff.py --base <ref-or-path> --head <ref-or-path>
                                  [--fail-on-breaking] [--json]

`<ref-or-path>` is either:
  * a git ref (e.g. ``origin/main``, ``HEAD``, ``v0.1.0``) — files are read
    via ``git show <ref>:<path>`` and enumerated via ``git ls-tree``.
  * a filesystem directory — used for offline tests.

Exit codes:
    0  OK (or no ``--fail-on-breaking``)
    1  Breaking changes detected and ``--fail-on-breaking`` was supplied
    2  Internal error (unreadable file, malformed YAML, etc.)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("error: pyyaml is required (pip install pyyaml)\n")
    sys.exit(2)


SCHEMAS_PREFIX = "schemas/"

# Mandatory Bronze audit columns — removing or weakening any of these is BREAKING.
BRONZE_AUDIT_COLUMNS = {
    "_ingested_at_utc",
    "_source_lane",
    "_correlation_id",
    "_raw_blob_path",
    "_contract_version",
}

# Loose numeric-widening ladder. Going right is widening (ADDITIVE),
# going left is narrowing (BREAKING).
NUMERIC_LADDER = ["byte", "short", "int", "integer", "long", "bigint", "float", "double", "decimal", "number"]


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #
@dataclass
class Change:
    file: str
    kind: str  # "breaking" | "additive" | "patch"
    what: str
    detail: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class DiffResult:
    changes: List[Change] = field(default_factory=list)
    files_changed: set = field(default_factory=set)

    def add(self, c: Change) -> None:
        self.changes.append(c)
        self.files_changed.add(c.file)

    def counts(self) -> Dict[str, int]:
        out = {"breaking": 0, "additive": 0, "patch": 0}
        for c in self.changes:
            out[c.kind] = out.get(c.kind, 0) + 1
        return out


# --------------------------------------------------------------------------- #
# Source adapters: ref vs path
# --------------------------------------------------------------------------- #
def _is_dir_source(src: str) -> bool:
    return os.path.isdir(src)


def _git(args: List[str]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


def list_contract_files(src: str) -> List[str]:
    """Return a sorted list of contract YAML files (paths relative to repo root)
    found under ``schemas/`` for the given source."""
    if _is_dir_source(src):
        root = Path(src)
        schemas_root = root / "schemas"
        if not schemas_root.is_dir():
            return []
        out = []
        for p in schemas_root.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".yaml", ".yml"):
                rel = p.relative_to(root).as_posix()
                out.append(rel)
        return sorted(out)

    # git ref
    rc, stdout, stderr = _git(["ls-tree", "-r", src, "--name-only", "--", "schemas/"])
    if rc != 0:
        raise RuntimeError(f"git ls-tree failed for {src}: {stderr.strip()}")
    files = [
        line.strip()
        for line in stdout.splitlines()
        if line.strip().endswith((".yaml", ".yml"))
    ]
    return sorted(files)


def read_contract(src: str, relpath: str) -> Optional[str]:
    """Return text contents of ``relpath`` at the given source, or ``None`` if absent."""
    if _is_dir_source(src):
        p = Path(src) / relpath
        if not p.is_file():
            return None
        try:
            return p.read_text(encoding="utf-8")
        except Exception as e:
            raise RuntimeError(f"cannot read {p}: {e}")
    # git ref
    rc, stdout, stderr = _git(["show", f"{src}:{relpath}"])
    if rc != 0:
        # Path doesn't exist at this ref
        return None
    return stdout


def parse_yaml(text: str, where: str) -> Any:
    try:
        return yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        raise RuntimeError(f"malformed YAML at {where}: {e}")


# --------------------------------------------------------------------------- #
# Contract model normalisation
# --------------------------------------------------------------------------- #
def _as_list(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def extract_entities(doc: Any) -> Dict[str, Dict[str, Any]]:
    """Normalise ODCS-flavoured shapes into {entity_name: {columns: {name: col}, raw: ...}}."""
    entities: Dict[str, Dict[str, Any]] = {}
    if not isinstance(doc, dict):
        return entities

    # ODCS v3 uses "schema:" with a list of entities/objects
    schema = doc.get("schema")
    candidates: List[Any] = []
    if isinstance(schema, list):
        candidates.extend(schema)
    elif isinstance(schema, dict):
        candidates.append(schema)

    # Some flavours use "entities", "tables", "datasets"
    for key in ("entities", "tables", "datasets", "models"):
        v = doc.get(key)
        if isinstance(v, list):
            candidates.extend(v)
        elif isinstance(v, dict):
            for name, body in v.items():
                if isinstance(body, dict):
                    body = dict(body)
                    body.setdefault("name", name)
                    candidates.append(body)

    for ent in candidates:
        if not isinstance(ent, dict):
            continue
        name = ent.get("name") or ent.get("table") or ent.get("entity") or "default"
        cols = _extract_columns(ent)
        entities[str(name)] = {"columns": cols, "raw": ent}

    # Fallback: doc itself is a single entity with `columns` / `properties`
    if not entities:
        cols = _extract_columns(doc)
        if cols:
            name = doc.get("name") or doc.get("entity") or "default"
            entities[str(name)] = {"columns": cols, "raw": doc}

    return entities


def _extract_columns(ent: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    cols: Dict[str, Dict[str, Any]] = {}
    raw_cols = (
        ent.get("columns")
        or ent.get("properties")
        or ent.get("fields")
        or ent.get("attributes")
        or []
    )
    if isinstance(raw_cols, dict):
        for cname, body in raw_cols.items():
            body = dict(body) if isinstance(body, dict) else {"type": body}
            body.setdefault("name", cname)
            cols[str(cname)] = body
    elif isinstance(raw_cols, list):
        for body in raw_cols:
            if not isinstance(body, dict):
                continue
            cname = body.get("name") or body.get("column")
            if cname is None:
                continue
            cols[str(cname)] = body
    return cols


def is_nullable(col: Dict[str, Any]) -> bool:
    # Default = nullable=True unless explicitly tightened.
    if "nullable" in col:
        return bool(col["nullable"])
    if col.get("required") is True:
        return False
    if col.get("optional") is False:
        return False
    return True


def is_required(col: Dict[str, Any]) -> bool:
    if col.get("required") is True:
        return True
    if "nullable" in col:
        return not bool(col["nullable"])
    return False


def col_type(col: Dict[str, Any]) -> str:
    t = col.get("type") or col.get("logicalType") or col.get("physicalType") or ""
    return str(t).lower()


def primary_key(ent_raw: Dict[str, Any]) -> List[str]:
    pk = ent_raw.get("primaryKey") or ent_raw.get("primary_key")
    if pk is None:
        # Derive from columns having primaryKey: true
        cols = _extract_columns(ent_raw)
        derived = [n for n, c in cols.items() if c.get("primaryKey") is True or c.get("primary_key") is True]
        return sorted(derived)
    if isinstance(pk, str):
        return [pk]
    if isinstance(pk, list):
        return sorted(str(x) for x in pk)
    return []


def supersedes_links(doc: Any) -> List[str]:
    if not isinstance(doc, dict):
        return []
    cp = doc.get("customProperties") or doc.get("custom_properties") or {}
    if isinstance(cp, list):
        # ODCS list-of-pairs style
        for item in cp:
            if isinstance(item, dict) and item.get("property") in ("dft-av.supersedes", "dft-av/supersedes"):
                return [str(x) for x in _as_list(item.get("value"))]
        return []
    if isinstance(cp, dict):
        block = cp.get("dft-av") or {}
        if isinstance(block, dict):
            return [str(x) for x in _as_list(block.get("supersedes"))]
    return []


def declared_version(doc: Any) -> Optional[str]:
    if not isinstance(doc, dict):
        return None
    md = doc.get("metadata") or {}
    if isinstance(md, dict) and md.get("version"):
        return str(md["version"])
    if doc.get("version"):
        return str(doc["version"])
    return None


def _major(version: Optional[str]) -> Optional[int]:
    if not version:
        return None
    head = version.lstrip("vV").split(".", 1)[0]
    try:
        return int(head)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Core diff
# --------------------------------------------------------------------------- #
def diff_contracts(base_src: str, head_src: str) -> DiffResult:
    result = DiffResult()
    base_files = set(list_contract_files(base_src))
    head_files = set(list_contract_files(head_src))

    # Removed files = BREAKING
    for f in sorted(base_files - head_files):
        result.add(Change(f, "breaking", "contract removed", f"{f} no longer exists at head"))

    # Added files = ADDITIVE
    for f in sorted(head_files - base_files):
        result.add(Change(f, "additive", "new contract", f"{f} added"))

    # Shared files: diff content
    for f in sorted(base_files & head_files):
        base_text = read_contract(base_src, f) or ""
        head_text = read_contract(head_src, f) or ""
        if base_text == head_text:
            continue
        base_doc = parse_yaml(base_text, f"base:{f}")
        head_doc = parse_yaml(head_text, f"head:{f}")
        _diff_one(f, base_doc, head_doc, result)

    return result


def _diff_one(file: str, base: Any, head: Any, result: DiffResult) -> None:
    base_entities = extract_entities(base)
    head_entities = extract_entities(head)

    semantic_change = False

    # Removed entity = BREAKING
    for name in sorted(set(base_entities) - set(head_entities)):
        result.add(Change(file, "breaking", "entity removed", f"entity `{name}` removed"))
        semantic_change = True

    # Added entity = ADDITIVE
    for name in sorted(set(head_entities) - set(base_entities)):
        result.add(Change(file, "additive", "new entity", f"entity `{name}` added"))
        semantic_change = True

    # Shared entities: diff columns + PK
    for name in sorted(set(base_entities) & set(head_entities)):
        b_ent = base_entities[name]
        h_ent = head_entities[name]
        sem = _diff_entity(file, name, b_ent, h_ent, result)
        semantic_change = semantic_change or sem

    # supersedes link removal = BREAKING
    base_super = set(supersedes_links(base))
    head_super = set(supersedes_links(head))
    for s in sorted(base_super - head_super):
        result.add(Change(file, "breaking", "supersedes link removed",
                          f"customProperties.dft-av.supersedes lost: {s}"))
        semantic_change = True
    for s in sorted(head_super - base_super):
        result.add(Change(file, "additive", "supersedes link added",
                          f"customProperties.dft-av.supersedes added: {s}"))
        semantic_change = True

    # Version sanity check: major bumped without schema change
    base_v = declared_version(base)
    head_v = declared_version(head)
    bm, hm = _major(base_v), _major(head_v)
    if bm is not None and hm is not None and hm > bm and not semantic_change:
        result.add(Change(file, "breaking", "spurious major version bump",
                          f"metadata.version major bumped {base_v} → {head_v} with no schema change"))

    # If no specific change emitted at all but text differs, count as patch
    if not semantic_change and base_v == head_v:
        # Could be whitespace/description-only
        result.add(Change(file, "patch", "non-semantic change",
                          "text changed but no schema-level diff detected"))


def _diff_entity(file: str, ename: str,
                 b_ent: Dict[str, Any], h_ent: Dict[str, Any],
                 result: DiffResult) -> bool:
    semantic = False
    b_cols: Dict[str, Dict[str, Any]] = b_ent["columns"]
    h_cols: Dict[str, Dict[str, Any]] = h_ent["columns"]
    b_names = list(b_cols.keys())
    h_names = list(h_cols.keys())

    removed = [n for n in b_names if n not in h_cols]
    added = [n for n in h_names if n not in b_cols]

    # Rename heuristic: same position, same type, paired removed+added => rename (BREAKING)
    renamed: List[Tuple[str, str]] = []
    for old in list(removed):
        try:
            pos = b_names.index(old)
        except ValueError:
            continue
        if pos < len(h_names):
            cand = h_names[pos]
            if cand in added and col_type(b_cols[old]) == col_type(h_cols[cand]):
                renamed.append((old, cand))
                removed.remove(old)
                added.remove(cand)

    for old, new in renamed:
        result.add(Change(file, "breaking", "column renamed",
                          f"{ename}: `{old}` → `{new}` (same position/type)"))
        semantic = True

    for n in removed:
        if n in BRONZE_AUDIT_COLUMNS:
            result.add(Change(file, "breaking", "bronze audit column removed",
                              f"{ename}: mandatory `{n}` removed"))
        else:
            result.add(Change(file, "breaking", "column removed",
                              f"{ename}: column `{n}` removed"))
        semantic = True

    for n in added:
        col = h_cols[n]
        if is_required(col):
            result.add(Change(file, "breaking", "new required column",
                              f"{ename}: required column `{n}` added"))
        else:
            result.add(Change(file, "additive", "new optional column",
                              f"{ename}: optional column `{n}` ({col_type(col) or 'any'}) added"))
        semantic = True

    # Shared columns
    for n in [x for x in b_names if x in h_cols]:
        b_col = b_cols[n]
        h_col = h_cols[n]
        bt, ht = col_type(b_col), col_type(h_col)
        if bt != ht:
            if _is_widening(bt, ht):
                result.add(Change(file, "additive", "column type widened",
                                  f"{ename}.{n}: {bt or '?'} → {ht or '?'} (widening)"))
            else:
                kind = "breaking"
                if n in BRONZE_AUDIT_COLUMNS:
                    result.add(Change(file, "breaking", "bronze audit weakened",
                                      f"{ename}.{n}: type changed {bt} → {ht}"))
                else:
                    result.add(Change(file, kind, "column type change",
                                      f"{ename}.{n}: {bt or '?'} → {ht or '?'}"))
            semantic = True

        # Nullability tightening: true -> false is BREAKING
        b_null = is_nullable(b_col)
        h_null = is_nullable(h_col)
        if b_null and not h_null:
            if n in BRONZE_AUDIT_COLUMNS:
                result.add(Change(file, "breaking", "bronze audit weakened",
                                  f"{ename}.{n}: nullability tightened (nullable true → false)"))
            else:
                result.add(Change(file, "breaking", "nullable tightened",
                                  f"{ename}.{n}: nullable true → false"))
            semantic = True
        elif not b_null and h_null:
            result.add(Change(file, "additive", "nullable loosened",
                              f"{ename}.{n}: nullable false → true"))
            semantic = True

        # Required tightening: adding required:true where previously not required
        b_req = is_required(b_col)
        h_req = is_required(h_col)
        if not b_req and h_req and b_null == h_null:
            # Only flag if not already caught by nullable transition
            result.add(Change(file, "breaking", "required tightened",
                              f"{ename}.{n}: required false → true"))
            semantic = True

    # Primary key change
    b_pk = primary_key(b_ent["raw"])
    h_pk = primary_key(h_ent["raw"])
    if b_pk != h_pk and (b_pk or h_pk):
        result.add(Change(file, "breaking", "primary key changed",
                          f"{ename}: primaryKey {b_pk or '[]'} → {h_pk or '[]'}"))
        semantic = True

    # Column reorder (patch warning)
    shared = [n for n in b_names if n in h_cols]
    shared_in_head_order = [n for n in h_names if n in b_cols]
    if shared and shared != shared_in_head_order and not (removed or added or renamed):
        result.add(Change(file, "patch", "columns reordered",
                          f"{ename}: column order changed"))

    return semantic


def _is_widening(b: str, h: str) -> bool:
    if not b or not h:
        return False
    if b in NUMERIC_LADDER and h in NUMERIC_LADDER:
        return NUMERIC_LADDER.index(h) > NUMERIC_LADDER.index(b)
    return False


# --------------------------------------------------------------------------- #
# Output formatting
# --------------------------------------------------------------------------- #
KIND_ICON = {"breaking": "🚨 BREAKING", "additive": "⚠ ADDITIVE", "patch": "· PATCH"}


def render_human(base: str, head: str, result: DiffResult,
                 declared_head_version: Optional[str], required_bump: str) -> str:
    lines: List[str] = []
    lines.append(f"📋 Contract diff: {base} → {head}")
    lines.append("")
    if not result.changes:
        lines.append("No contract changes detected.")
        return "\n".join(lines)
    by_file: Dict[str, List[Change]] = {}
    for c in result.changes:
        by_file.setdefault(c.file, []).append(c)
    for f in sorted(by_file):
        lines.append(f"{f}:")
        for c in by_file[f]:
            lines.append(f"  {KIND_ICON.get(c.kind, c.kind)}: {c.what} — {c.detail}")
        lines.append("")
    counts = result.counts()
    lines.append(
        f"Summary: {counts['breaking']} BREAKING, {counts['additive']} ADDITIVE, "
        f"{counts['patch']} PATCH across {len(result.files_changed)} contract(s)."
    )
    if required_bump == "major":
        decl = declared_head_version or "unknown"
        lines.append(f"❌ Major version bump required (current declared: {decl}).")
    elif required_bump == "minor":
        lines.append("➕ Minor version bump recommended.")
    elif required_bump == "patch":
        lines.append("· Patch version bump sufficient.")
    return "\n".join(lines)


def required_bump_for(counts: Dict[str, int]) -> str:
    if counts.get("breaking", 0) > 0:
        return "major"
    if counts.get("additive", 0) > 0:
        return "minor"
    if counts.get("patch", 0) > 0:
        return "patch"
    return "none"


def collect_head_version(head_src: str, files: Iterable[str]) -> Optional[str]:
    for f in files:
        txt = read_contract(head_src, f)
        if not txt:
            continue
        try:
            doc = parse_yaml(txt, f"head:{f}")
        except Exception:
            continue
        v = declared_version(doc)
        if v:
            return v
    return None


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Diff ODCS contracts and flag BREAKING vs ADDITIVE changes.")
    p.add_argument("--base", required=True, help="git ref or directory (baseline)")
    p.add_argument("--head", required=True, help="git ref or directory (proposed)")
    p.add_argument("--fail-on-breaking", action="store_true",
                   help="exit non-zero if any BREAKING change is detected")
    p.add_argument("--json", action="store_true", help="emit JSON for CI consumption")
    args = p.parse_args(argv)

    try:
        result = diff_contracts(args.base, args.head)
    except RuntimeError as e:
        sys.stderr.write(f"contract-diff: {e}\n")
        return 2
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"contract-diff: internal error: {e}\n")
        return 2

    counts = result.counts()
    bump = required_bump_for(counts)
    head_files = list_contract_files(args.head) if not _is_dir_source(args.head) or os.path.isdir(args.head) else []
    head_version = collect_head_version(args.head, head_files)

    if args.json:
        payload = {
            "summary": {
                "breaking": counts.get("breaking", 0),
                "additive": counts.get("additive", 0),
                "patch": counts.get("patch", 0),
                "files_changed": len(result.files_changed),
            },
            "changes": [c.to_dict() for c in result.changes],
            "required_bump": bump,
            "declared_head_version": head_version,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(render_human(args.base, args.head, result, head_version, bump))

    if args.fail_on_breaking and counts.get("breaking", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
