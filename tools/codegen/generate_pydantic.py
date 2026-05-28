#!/usr/bin/env python3
"""Generate Pydantic v2 BaseModel stubs from ODCS-flavoured YAML contracts.

Walks ``schemas/bronze/`` and ``schemas/source/``. For each YAML contract,
emits one Python module per top-level entity (table) into
``python/dft_av_contracts/<kind>_<entity>.py`` and re-exports the generated
classes from ``python/dft_av_contracts/__init__.py`` (preserving the existing
``__version__`` declaration).

Type mapping (ODCS primitive -> Python):
  string      -> str
  text        -> str
  uuid        -> str
  timestamp   -> datetime
  datetime    -> datetime
  date        -> date
  bool/boolean-> bool
  int*/long   -> int
  decimal/numeric -> Decimal
  float/double -> float
  bytes/binary -> bytes

Nullable columns become ``Optional[T]`` with default ``None``.

For Bronze contracts, the five mandatory audit columns documented in
``schemas/bronze/README.md`` are added automatically if not already declared:
  _ingested_at_utc   (timestamp, required)
  _source_lane       (string, required)
  _correlation_id    (string, required)
  _raw_blob_path     (string, optional)
  _contract_version  (string, required)
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"
PYTHON_PKG_DIR = REPO_ROOT / "python" / "dft_av_contracts"
JSON_SCHEMAS_DIR = REPO_ROOT / "schemas" / "json"
# Default APIM op Bicep output: sibling platform repo's modules dir.
# Override via --apim-ops-out or DFT_AV_APIM_OPS_OUT env var when the platform
# repo lives elsewhere (e.g. CI vendoring).
DEFAULT_APIM_OPS_OUT = REPO_ROOT.parent / "dft-av-platform" / "iac" / "bicep" / "modules" / "apim-ops"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

CONTRACT_KINDS = ("bronze", "source")

TYPE_MAP: dict[str, str] = {
    "string": "str",
    "str": "str",
    "text": "str",
    "varchar": "str",
    "char": "str",
    "uuid": "str",
    "timestamp": "datetime",
    "timestamp_ntz": "datetime",
    "datetime": "datetime",
    "date": "date",
    "bool": "bool",
    "boolean": "bool",
    "int": "int",
    "int4": "int",
    "int8": "int",
    "integer": "int",
    "bigint": "int",
    "smallint": "int",
    "long": "int",
    "decimal": "Decimal",
    "numeric": "Decimal",
    "float": "float",
    "float4": "float",
    "float8": "float",
    "double": "float",
    "real": "float",
    "bytes": "bytes",
    "binary": "bytes",
}

BRONZE_AUDIT_COLUMNS: list[dict[str, Any]] = [
    {
        "name": "_ingested_at_utc",
        "logicalType": "timestamp",
        "required": True,
        "description": "UTC timestamp when this row was ingested into the Bronze layer.",
    },
    {
        "name": "_source_lane",
        "logicalType": "string",
        "required": True,
        "description": "Identifier of the upstream source lane that produced this row.",
    },
    {
        "name": "_correlation_id",
        "logicalType": "string",
        "required": True,
        "description": "Correlation id used to trace this row across pipeline stages.",
    },
    {
        "name": "_raw_blob_path",
        "logicalType": "string",
        "required": False,
        "description": "Optional path to the raw upstream blob that produced this row.",
    },
    {
        "name": "_contract_version",
        "logicalType": "string",
        "required": True,
        "description": "Semantic version of the contract this row was validated against.",
    },
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

_PY_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
}


def to_snake(name: str) -> str:
    s = re.sub(r"[^0-9A-Za-z]+", "_", name).strip("_")
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", s)
    s = re.sub(r"__+", "_", s)
    return s.lower()


def to_pascal(name: str) -> str:
    parts = re.split(r"[^0-9A-Za-z]+", name)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def safe_py_name(name: str) -> str:
    snake = to_snake(name)
    if not snake:
        snake = "field"
    if snake[0].isdigit():
        snake = f"f_{snake}"
    if snake in _PY_KEYWORDS:
        snake = f"{snake}_"
    return snake


def py_literal(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, str):
        # Use repr() so newlines, tabs, embedded quotes and non-ASCII chars
        # are all safely escaped into a single-line Python string literal.
        return repr(value)
    return repr(value)


def map_type(logical: str | None) -> str:
    if not logical:
        return "str"
    key = str(logical).strip().lower()
    # strip parameters such as decimal(10,2)
    key = re.split(r"[\s(]", key, maxsplit=1)[0]
    return TYPE_MAP.get(key, "str")


# --------------------------------------------------------------------------- #
# Data shapes
# --------------------------------------------------------------------------- #

@dataclass
class FieldSpec:
    source_name: str
    py_name: str
    py_type: str            # already wrapped in Optional[...] if nullable
    base_type: str          # the inner type (str, int, Decimal, ...)
    nullable: bool
    description_literal: str
    default_literal: str    # the literal text used as Field(default, ...)


@dataclass
class RoutingSpec:
    """Phase-2 ingest routing metadata pulled from a contract YAML's
    top-level ``routing:`` block. Drives RouteMeta emission, JSON Schema
    publication, and the APIM ingest-API operation Bicep snippet.
    Only set on contracts that participate in APIM ingest (Lanes 4/5).
    """
    doctype_slug: str
    lane: int
    apim_api: str
    apim_route: str
    http_method: str
    required_personas: list[str]
    required_headers: list[str]
    publishes_event: bool
    event_type: str | None
    event_subject_template: str | None
    event_grid_topic_name: str | None


@dataclass
class EntitySpec:
    kind: str               # bronze | source
    contract_id: str
    contract_version: str
    entity_name: str
    class_name: str
    module_name: str
    source_relpath: str
    fields: list[FieldSpec]
    routing: RoutingSpec | None = None

    @property
    def needs_datetime(self) -> bool:
        return any(f.base_type in {"datetime", "date"} for f in self.fields)

    @property
    def needs_decimal(self) -> bool:
        return any(f.base_type == "Decimal" for f in self.fields)


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

def iter_contract_files() -> Iterable[Path]:
    for kind in CONTRACT_KINDS:
        root = SCHEMAS_DIR / kind
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*.yaml")):
            if p.name.lower() == "readme.yaml":
                continue
            yield p
        for p in sorted(root.rglob("*.yml")):
            yield p


def extract_entities(doc: dict) -> list[tuple[str, list[dict]]]:
    """Return list of (entity_name, raw_property_list).

    Handles a few common ODCS-ish shapes:
      schema: [ {name, properties|columns|fields: [...]}, ... ]
      schema: {columns|properties|fields: [...], location: {table:...}, name: ...}
      models: {<name>: {properties|columns|fields: [...]}}
      properties|columns|fields: [...]   # single implicit entity at top level
    """
    entities: list[tuple[str, list[dict]]] = []
    metadata = doc.get("metadata") or {}

    def _derive_name_from_mapping(mapping: dict) -> str | None:
        loc = mapping.get("location") if isinstance(mapping.get("location"), dict) else {}
        return (
            (loc or {}).get("table")
            or mapping.get("name")
            or mapping.get("table")
            or mapping.get("entity")
            or metadata.get("id")
            or metadata.get("name")
        )

    schema = doc.get("schema")
    if isinstance(schema, list):
        for item in schema:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("table") or item.get("entity")
            props = item.get("properties") or item.get("columns") or item.get("fields") or []
            if name and isinstance(props, list):
                entities.append((str(name), props))
    elif isinstance(schema, dict):
        props = schema.get("columns") or schema.get("properties") or schema.get("fields") or []
        if isinstance(props, list) and props:
            name = _derive_name_from_mapping(schema)
            if not name:
                # Fall back to filename stem stripped of -vN suffix; caller will
                # have stamped metadata.id when present, so this is rarely hit.
                name = "row"
            entities.append((str(name), props))

    models = doc.get("models")
    if isinstance(models, dict):
        for name, body in models.items():
            if isinstance(body, dict):
                props = body.get("properties") or body.get("columns") or body.get("fields") or []
                if isinstance(props, list):
                    entities.append((str(name), props))

    if not entities:
        props = doc.get("properties") or doc.get("columns") or doc.get("fields")
        if isinstance(props, list):
            implicit = (
                doc.get("name")
                or metadata.get("name")
                or metadata.get("id")
                or "row"
            )
            entities.append((str(implicit), props))

    return entities


def is_nullable(prop: dict) -> bool:
    if "required" in prop:
        return not bool(prop["required"])
    if "nullable" in prop:
        return bool(prop["nullable"])
    if "optional" in prop:
        return bool(prop["optional"])
    return True  # default: nullable


def field_logical_type(prop: dict) -> str | None:
    return (
        prop.get("logicalType")
        or prop.get("logical_type")
        or prop.get("type")
        or prop.get("physicalType")
    )


def merge_audit_columns(props: list[dict]) -> list[dict]:
    existing = {str(p.get("name", "")).lower() for p in props if isinstance(p, dict)}
    merged = list(props)
    for col in BRONZE_AUDIT_COLUMNS:
        if col["name"].lower() not in existing:
            merged.append(dict(col))
    return merged


def build_field(prop: dict) -> FieldSpec | None:
    if not isinstance(prop, dict):
        return None
    raw_name = prop.get("name") or prop.get("field")
    if not raw_name:
        return None
    source_name = str(raw_name)
    base = map_type(field_logical_type(prop))
    nullable = is_nullable(prop)
    py_type = f"Optional[{base}]" if nullable else base
    description = prop.get("description") or prop.get("comment") or ""
    default_literal = "None" if nullable else "..."
    return FieldSpec(
        source_name=source_name,
        py_name=safe_py_name(source_name),
        py_type=py_type,
        base_type=base,
        nullable=nullable,
        description_literal=py_literal(str(description)),
        default_literal=default_literal,
    )


def parse_routing(doc: dict) -> RoutingSpec | None:
    raw = doc.get("routing")
    if not isinstance(raw, dict):
        return None
    event = raw.get("event") if isinstance(raw.get("event"), dict) else {}
    return RoutingSpec(
        doctype_slug=str(raw["doctype_slug"]),
        lane=int(raw["lane"]),
        apim_api=str(raw.get("apim_api", "ingest")),
        apim_route=str(raw["apim_route"]),
        http_method=str(raw.get("http_method", "POST")).upper(),
        required_personas=list(raw.get("required_personas") or []),
        required_headers=list(raw.get("required_headers") or []),
        publishes_event=bool(raw.get("publishes_event", False)),
        event_type=(event or {}).get("type"),
        event_subject_template=(event or {}).get("subject_template"),
        event_grid_topic_name=(event or {}).get("grid_topic_name"),
    )


def build_entities_for_file(path: Path) -> list[EntitySpec]:
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    metadata = doc.get("metadata") or {}
    contract_id = (
        metadata.get("id")
        or metadata.get("name")
        or doc.get("id")
        or path.stem
    )
    contract_version = str(metadata.get("version") or doc.get("version") or "0.0.0")
    rel = path.relative_to(REPO_ROOT).as_posix()
    kind = path.relative_to(SCHEMAS_DIR).parts[0]  # bronze | source

    specs: list[EntitySpec] = []
    for entity_name, props in extract_entities(doc):
        working_props = list(props)
        if kind == "bronze":
            working_props = merge_audit_columns(working_props)

        fields: list[FieldSpec] = []
        seen: set[str] = set()
        for prop in working_props:
            fs = build_field(prop)
            if fs is None:
                continue
            if fs.py_name in seen:
                continue
            seen.add(fs.py_name)
            fields.append(fs)

        if not fields:
            continue

        kind_pascal = to_pascal(kind)
        entity_pascal = to_pascal(entity_name)
        # Avoid double-prefixing when the entity name already begins with the layer kind
        # (e.g. kind="bronze" + entity_name="bronze_asde_incident_push" → "BronzeAsdeIncidentPushRow")
        if entity_pascal.lower().startswith(kind_pascal.lower()):
            class_name = f"{entity_pascal}Row"
        else:
            class_name = f"{kind_pascal}{entity_pascal}Row"
        kind_snake = to_snake(kind)
        entity_snake = to_snake(entity_name)
        if entity_snake.startswith(f"{kind_snake}_"):
            module_name = entity_snake
        else:
            module_name = f"{kind_snake}_{entity_snake}"
        specs.append(
            EntitySpec(
                kind=kind,
                contract_id=str(contract_id),
                contract_version=contract_version,
                entity_name=str(entity_name),
                class_name=class_name,
                module_name=module_name,
                source_relpath=rel,
                fields=fields,
            )
        )

    # Attach the contract-level routing block (if any) to the first/primary
    # entity. We require single-entity ingest contracts so routing semantics
    # stay unambiguous; raise if a multi-entity contract carries routing.
    routing = parse_routing(doc)
    if routing is not None:
        if not specs:
            raise ValueError(
                f"{path}: declares routing: but no entities were extracted"
            )
        if len(specs) > 1:
            raise ValueError(
                f"{path}: routing: block requires a single entity contract; "
                f"got {len(specs)} entities ({[s.entity_name for s in specs]})"
            )
        specs[0].routing = routing
    return specs


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render_modules(entities: list[EntitySpec]) -> None:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    template = env.get_template("model.py.j2")
    PYTHON_PKG_DIR.mkdir(parents=True, exist_ok=True)

    for spec in entities:
        rendered = template.render(
            source_relpath=spec.source_relpath,
            contract_id=spec.contract_id,
            contract_version=spec.contract_version,
            entity_name=spec.entity_name,
            class_name=spec.class_name,
            kind=spec.kind,
            fields=spec.fields,
            needs_datetime=spec.needs_datetime,
            needs_decimal=spec.needs_decimal,
        )
        out = PYTHON_PKG_DIR / f"{spec.module_name}.py"
        out.write_text(rendered, encoding="utf-8")


_VERSION_RE = re.compile(r'^__version__\s*=\s*".*"\s*$', re.MULTILINE)
_GENERATED_BEGIN = "# --- BEGIN GENERATED RE-EXPORTS (do not edit) ---"
_GENERATED_END = "# --- END GENERATED RE-EXPORTS ---"


def render_routes_module(entities: list[EntitySpec]) -> list[EntitySpec]:
    """Emit ``_routes.py`` containing RouteMeta dataclass and ROUTES dict
    keyed by doctype_slug. Returns the list of entities that contributed a
    route (for downstream JSON Schema + Bicep emission).
    """
    routed = [e for e in entities if e.routing is not None]
    routed_sorted = sorted(routed, key=lambda e: e.routing.doctype_slug)  # type: ignore[union-attr]

    # Detect duplicate slugs eagerly so the failure mode is obvious.
    seen: dict[str, str] = {}
    for e in routed_sorted:
        slug = e.routing.doctype_slug  # type: ignore[union-attr]
        if slug in seen:
            raise ValueError(
                f"Duplicate routing.doctype_slug '{slug}' in "
                f"{seen[slug]} and {e.source_relpath}"
            )
        seen[slug] = e.source_relpath

    lines: list[str] = [
        '"""Auto-generated. DO NOT EDIT BY HAND.',
        "",
        "Ingest route registry compiled from contract YAML ``routing:`` blocks.",
        "Regenerate via ``tools/codegen/generate_pydantic.py``.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass, field",
        "from typing import Type",
        "",
        "from pydantic import BaseModel",
        "",
    ]
    for e in routed_sorted:
        lines.append(f"from .{e.module_name} import {e.class_name}")
    lines.append("")
    lines.append("")
    lines.append("@dataclass(frozen=True)")
    lines.append("class RouteMeta:")
    lines.append('    """Ingest route metadata for one contract doctype_slug."""')
    lines.append("    doctype_slug: str")
    lines.append("    contract_id: str")
    lines.append("    contract_version: str")
    lines.append("    lane: int")
    lines.append("    apim_api: str")
    lines.append("    apim_route: str")
    lines.append("    http_method: str")
    lines.append("    required_personas: tuple[str, ...]")
    lines.append("    required_headers: tuple[str, ...]")
    lines.append("    publishes_event: bool")
    lines.append("    event_type: str | None")
    lines.append("    event_subject_template: str | None")
    lines.append("    event_grid_topic_name: str | None")
    lines.append("    pydantic_model: Type[BaseModel]")
    lines.append("    json_schema_filename: str")
    lines.append("")
    lines.append("")
    lines.append("ROUTES: dict[str, RouteMeta] = {")
    for e in routed_sorted:
        r = e.routing  # type: ignore[assignment]
        lines.append(f'    "{r.doctype_slug}": RouteMeta(')
        lines.append(f'        doctype_slug="{r.doctype_slug}",')
        lines.append(f'        contract_id="{e.contract_id}",')
        lines.append(f'        contract_version="{e.contract_version}",')
        lines.append(f"        lane={r.lane},")
        lines.append(f'        apim_api="{r.apim_api}",')
        lines.append(f'        apim_route="{r.apim_route}",')
        lines.append(f'        http_method="{r.http_method}",')
        lines.append(f"        required_personas={tuple(r.required_personas)!r},")
        lines.append(f"        required_headers={tuple(r.required_headers)!r},")
        lines.append(f"        publishes_event={r.publishes_event!r},")
        lines.append(f"        event_type={r.event_type!r},")
        lines.append(f"        event_subject_template={r.event_subject_template!r},")
        lines.append(f"        event_grid_topic_name={r.event_grid_topic_name!r},")
        lines.append(f"        pydantic_model={e.class_name},")
        lines.append(f'        json_schema_filename="{r.doctype_slug}.schema.json",')
        lines.append("    ),")
    lines.append("}")
    lines.append("")
    lines.append('__all__ = ["RouteMeta", "ROUTES"]')
    lines.append("")

    (PYTHON_PKG_DIR / "_routes.py").write_text("\n".join(lines), encoding="utf-8")
    return routed_sorted


def render_json_schemas(routed_entities: list[EntitySpec]) -> None:
    """Dump a Draft-2020-12 JSON Schema per routed entity.

    Imports the freshly written Pydantic modules to call
    ``model.model_json_schema()`` so the JSON contract stays byte-for-byte
    aligned with the Python model that ingest will actually validate
    against.
    """
    if not routed_entities:
        return
    JSON_SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    python_root = str(REPO_ROOT / "python")
    if python_root not in sys.path:
        sys.path.insert(0, python_root)
    # Force fresh import in case the script is re-run in the same process.
    pkg = importlib.import_module("dft_av_contracts")
    importlib.reload(pkg)
    for e in routed_entities:
        mod = importlib.import_module(f"dft_av_contracts.{e.module_name}")
        importlib.reload(mod)
        model = getattr(mod, e.class_name)
        schema = model.model_json_schema(mode="validation")
        schema["$id"] = (
            f"https://contracts.dft-av.example.gov.uk/json/"
            f"{e.routing.doctype_slug}.schema.json"  # type: ignore[union-attr]
        )
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["x-dft-av-contract"] = {
            "contract_id": e.contract_id,
            "contract_version": e.contract_version,
            "doctype_slug": e.routing.doctype_slug,  # type: ignore[union-attr]
            "source_relpath": e.source_relpath,
        }
        out = JSON_SCHEMAS_DIR / f"{e.routing.doctype_slug}.schema.json"  # type: ignore[union-attr]
        out.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


_BICEP_HEADER = (
    "// Auto-generated from {source_relpath}. DO NOT EDIT BY HAND.\n"
    "// Doctype slug:    {slug}\n"
    "// Contract:        {contract_id} v{contract_version}\n"
    "// Lane:            {lane}\n"
    "// APIM API:        {apim_api}\n"
    "// Regenerate via tools/codegen/generate_pydantic.py.\n"
)


def render_apim_ops_bicep(routed_entities: list[EntitySpec], out_dir: Path) -> None:
    """Emit one APIM operation Bicep module per ingest route.

    Each module is a thin, parameterised resource that the platform repo's
    apim-ingest API composes into its operation set. The module is
    deliberately decoupled from the API definition so platform owners can
    swap policies independently.
    """
    if not routed_entities:
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    for e in routed_entities:
        r = e.routing  # type: ignore[assignment]
        header = _BICEP_HEADER.format(
            source_relpath=e.source_relpath,
            slug=r.doctype_slug,
            contract_id=e.contract_id,
            contract_version=e.contract_version,
            lane=r.lane,
            apim_api=r.apim_api,
        )
        headers_block = "\n".join(
            f"      {{ name: '{h}', required: true, type: 'string', values: [] }}"
            for h in r.required_headers
        )
        display_name = f"Ingest {r.doctype_slug} ({e.contract_id} v{e.contract_version})"
        body = f"""{header}
@description('Name of the APIM service in this resource group.')
param apimName string

@description('Name of the parent ingest API inside APIM (defaults to apim-ingest).')
param apiName string = 'apim-ingest'

resource api 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' existing = {{
  name: '${{apimName}}/${{apiName}}'
}}

resource op 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {{
  parent: api
  name: '{r.doctype_slug}'
  properties: {{
    displayName: '{display_name}'
    method: '{r.http_method}'
    urlTemplate: '{r.apim_route}'
    description: 'Ingest doctype {r.doctype_slug}. Personas: {", ".join(r.required_personas) or "n/a"}.'
    request: {{
      headers: [
{headers_block}
      ]
      representations: [
        {{
          contentType: 'application/json'
          schemaId: '{r.doctype_slug}'
          typeName: '{e.class_name}'
        }}
      ]
    }}
    responses: [
      {{ statusCode: 202, description: 'Accepted for ingest' }}
      {{ statusCode: 400, description: 'Schema or header validation failed' }}
      {{ statusCode: 401, description: 'Missing or invalid persona subscription key' }}
      {{ statusCode: 413, description: 'Payload exceeds documented size cap' }}
    ]
  }}
}}

output operationName string = op.name
output urlTemplate string = '{r.apim_route}'
"""
        out = out_dir / f"{r.doctype_slug}.bicep"
        out.write_text(body, encoding="utf-8")


def update_init(entities: list[EntitySpec]) -> None:
    init_path = PYTHON_PKG_DIR / "__init__.py"
    if init_path.is_file():
        original = init_path.read_text(encoding="utf-8")
    else:
        original = '__version__ = "0.1.0"\n'

    version_match = _VERSION_RE.search(original)
    version_line = version_match.group(0) if version_match else '__version__ = "0.1.0"'

    lines: list[str] = [
        '"""dft-av-contracts: generated Pydantic models for DfT AV data contracts."""',
        "",
        version_line,
        "",
        _GENERATED_BEGIN,
    ]
    exports: list[str] = []
    for spec in sorted(entities, key=lambda s: s.module_name):
        lines.append(f"from .{spec.module_name} import {spec.class_name}")
        exports.append(spec.class_name)
    lines.append("from ._routes import ROUTES, RouteMeta")
    lines.append("")
    lines.append("__all__ = [")
    lines.append('    "__version__",')
    lines.append('    "ROUTES",')
    lines.append('    "RouteMeta",')
    for name in exports:
        lines.append(f'    "{name}",')
    lines.append("]")
    lines.append(_GENERATED_END)
    lines.append("")

    init_path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    import argparse
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apim-ops-out",
        type=Path,
        default=Path(os.environ.get("DFT_AV_APIM_OPS_OUT", str(DEFAULT_APIM_OPS_OUT))),
        help=(
            "Directory for generated APIM operation Bicep modules. "
            f"Defaults to {DEFAULT_APIM_OPS_OUT} (sibling platform repo)."
        ),
    )
    args = parser.parse_args(argv)

    contracts = list(iter_contract_files())
    if not contracts:
        print(f"WARNING: no contracts found under {SCHEMAS_DIR}", file=sys.stderr)

    all_entities: list[EntitySpec] = []
    for path in contracts:
        try:
            entities = build_entities_for_file(path)
        except yaml.YAMLError as e:
            print(f"ERROR: failed to parse {path}: {e}", file=sys.stderr)
            return 2
        all_entities.extend(entities)

    render_modules(all_entities)
    update_init(all_entities)
    routed = render_routes_module(all_entities)
    render_json_schemas(routed)
    render_apim_ops_bicep(routed, args.apim_ops_out)

    apim_target = args.apim_ops_out
    try:
        apim_target = apim_target.resolve().relative_to(REPO_ROOT.parent)
    except ValueError:
        apim_target = args.apim_ops_out.resolve()
    print(
        f"Generated {len(all_entities)} models from {len(contracts)} contracts; "
        f"{len(routed)} routes, JSON schemas in {JSON_SCHEMAS_DIR.relative_to(REPO_ROOT)}, "
        f"APIM op Bicep in {apim_target}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
