#!/usr/bin/env python3
"""Validate schemas/MANIFEST.yaml against the contracts on disk.

Checks performed:
  1. Each manifest entry points to a file that exists.
  2. The sha256 of the file on disk matches the manifest-declared sha256.
  3. No contract YAML on disk is missing from the manifest (set diff).
  4. No manifest entry refers to a missing contract YAML (set diff).
  5. Every contract YAML declares metadata.version, and the major version
     matches the file-naming convention (``...-v<MAJOR>.yaml``).

Exits 0 on success, non-zero on first class of failure detected (after
reporting every issue found, so users see a complete picture).
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"
MANIFEST_PATH = SCHEMAS_DIR / "MANIFEST.yaml"

CONTRACT_DIRS = ("bronze", "source")
FILENAME_VERSION_RE = re.compile(r"-v(\d+)\.ya?ml$", re.IGNORECASE)


def sha256_of(path: Path) -> str:
    """SHA-256 of the file with line endings normalised to LF.

    Git on Windows may check files out with CRLF when autocrlf is enabled,
    while Linux CI runners get LF. Normalising before hashing ensures the
    same content yields the same hash on every platform.
    """
    h = hashlib.sha256()
    with path.open("rb") as fh:
        data = fh.read()
    h.update(data.replace(b"\r\n", b"\n"))
    return h.hexdigest()


def discover_contracts() -> set[Path]:
    found: set[Path] = set()
    for sub in CONTRACT_DIRS:
        root = SCHEMAS_DIR / sub
        if not root.is_dir():
            continue
        for p in root.rglob("*.yaml"):
            if p.name.lower() == "readme.yaml":
                continue
            found.add(p)
        for p in root.rglob("*.yml"):
            found.add(p)
    return found


def relpath(p: Path) -> str:
    return p.relative_to(REPO_ROOT).as_posix()


def schema_relpath(p: Path) -> str:
    """Path relative to schemas/ (the convention used by MANIFEST.yaml)."""
    return p.relative_to(SCHEMAS_DIR).as_posix()


def load_manifest() -> tuple[dict, list[dict]]:
    if not MANIFEST_PATH.is_file():
        print(f"ERROR: manifest not found at {relpath(MANIFEST_PATH)}", file=sys.stderr)
        sys.exit(2)
    with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    entries = data.get("contracts") or data.get("entries") or data
    if isinstance(entries, dict):
        # Allow `{path: {sha256: ...}}` shape too.
        entries = [{"relative_path": k, **(v or {})} for k, v in entries.items()]
    if not isinstance(entries, list):
        print(
            "ERROR: MANIFEST.yaml must contain a list under 'contracts' "
            "(or be a list / mapping of path -> metadata)",
            file=sys.stderr,
        )
        sys.exit(2)
    top = data if isinstance(data, dict) else {}
    return top, entries


def fmt_set(items: Iterable[str]) -> str:
    return "\n  - " + "\n  - ".join(sorted(items)) if items else " (none)"


def main() -> int:
    errors: list[str] = []
    top, entries = load_manifest()

    # S2: fail if MANIFEST is the staging-time placeholder.
    generator = str(top.get("generator", ""))
    if "(staging)" in generator:
        errors.append(
            "MANIFEST.yaml is the staging-time placeholder — release workflow must regenerate it "
            f"(generator='{generator}')."
        )

    manifest_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(f"manifest entry is not a mapping: {entry!r}")
            continue
        rel = entry.get("relative_path") or entry.get("path") or entry.get("file")
        declared = entry.get("sha256") or entry.get("digest")
        if not rel:
            errors.append(f"manifest entry missing 'relative_path': {entry!r}")
            continue
        manifest_paths.add(rel)
        # relative_path is relative to schemas/; prepend it for IO.
        abs_path = (SCHEMAS_DIR / rel).resolve()
        if not abs_path.is_file():
            errors.append(f"manifest references missing file: schemas/{rel}")
            continue
        actual = sha256_of(abs_path)
        if not declared:
            errors.append(f"manifest entry missing sha256: {rel}")
        elif declared.lower() != actual.lower():
            errors.append(
                f"sha256 mismatch for {rel}\n    declared: {declared}\n    actual:   {actual}"
            )

    disk_contracts = {schema_relpath(p) for p in discover_contracts()}
    missing_in_manifest = disk_contracts - manifest_paths
    missing_on_disk = manifest_paths - disk_contracts
    if missing_in_manifest:
        errors.append(
            "contracts on disk NOT in MANIFEST:" + fmt_set(missing_in_manifest)
        )
    if missing_on_disk:
        errors.append(
            "MANIFEST entries with NO file on disk:" + fmt_set(missing_on_disk)
        )

    # Per-contract metadata.version vs filename version check.
    for rel in sorted(disk_contracts):
        abs_path = SCHEMAS_DIR / rel
        m = FILENAME_VERSION_RE.search(abs_path.name)
        if not m:
            errors.append(
                f"{rel}: filename does not follow '<name>-v<MAJOR>.yaml' convention"
            )
            continue
        major = m.group(1)
        try:
            with abs_path.open("r", encoding="utf-8") as fh:
                doc = yaml.safe_load(fh) or {}
        except yaml.YAMLError as e:
            errors.append(f"{rel}: failed to parse YAML ({e})")
            continue
        metadata = doc.get("metadata") or {}
        version = metadata.get("version")
        if not version:
            errors.append(f"{rel}: missing metadata.version")
            continue
        if not str(version).startswith(f"{major}."):
            errors.append(
                f"{rel}: metadata.version='{version}' does not match filename major v{major}"
            )

    if errors:
        print("MANIFEST validation FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  * {e}", file=sys.stderr)
        return 1

    print(
        f"MANIFEST validation OK: {len(manifest_paths)}/{len(disk_contracts)} contracts match."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
