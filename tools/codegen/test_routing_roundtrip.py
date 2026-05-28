"""Round-trip tests for Phase-2 routing codegen.

Validates that for every routed contract:
1. A ``RouteMeta`` entry exists in ``dft_av_contracts.ROUTES``.
2. The on-disk JSON Schema matches the Pydantic model's live schema
   (ignoring generator-injected provenance keys).
3. The APIM operation Bicep module exists in the sibling platform repo
   (test is skipped with a clear message if the sibling is absent).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_PKG_PARENT = REPO_ROOT / "python"
JSON_SCHEMAS_DIR = REPO_ROOT / "schemas" / "json"

if str(PYTHON_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(PYTHON_PKG_PARENT))

from dft_av_contracts import ROUTES, RouteMeta  # noqa: E402

EXPECTED_SLUGS = {"si-inv", "nuico-ccav-kpi", "dvsa-aps-perf", "si-ismr"}

PROVENANCE_KEYS = {"$id", "$schema", "x-dft-av-contract"}


def _default_apim_ops_dir() -> Path:
    override = os.environ.get("DFT_AV_APIM_OPS_OUT")
    if override:
        return Path(override)
    return REPO_ROOT.parent / "dft-av-platform" / "iac" / "bicep" / "modules" / "apim-ops"


def test_expected_slugs_present():
    missing = EXPECTED_SLUGS - set(ROUTES)
    assert not missing, f"Missing routes for slugs: {sorted(missing)}"
    assert len(ROUTES) >= len(EXPECTED_SLUGS)


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_route_meta_shape(slug: str):
    route = ROUTES[slug]
    assert isinstance(route, RouteMeta)
    assert route.doctype_slug == slug
    assert route.contract_id
    assert route.contract_version
    assert route.apim_route.startswith("/")
    assert route.http_method
    assert route.json_schema_filename == f"{slug}.schema.json"


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_json_schema_matches_model(slug: str):
    route = ROUTES[slug]
    schema_path = JSON_SCHEMAS_DIR / route.json_schema_filename
    assert schema_path.is_file(), f"Missing JSON schema: {schema_path}"

    on_disk = json.loads(schema_path.read_text(encoding="utf-8"))
    live = route.pydantic_model.model_json_schema(mode="validation")

    stripped = {k: v for k, v in on_disk.items() if k not in PROVENANCE_KEYS}
    assert stripped == live, (
        f"JSON schema drift for {slug}: regenerate via "
        f"tools/codegen/generate_pydantic.py"
    )


@pytest.mark.parametrize("slug", sorted(EXPECTED_SLUGS))
def test_apim_op_bicep_exists(slug: str):
    bicep_dir = _default_apim_ops_dir()
    if not bicep_dir.parent.exists():
        pytest.skip(
            f"Sibling platform repo not found at {bicep_dir.parent}; "
            "set DFT_AV_APIM_OPS_OUT to override."
        )
    bicep_path = bicep_dir / f"{slug}.bicep"
    assert bicep_path.is_file(), f"Missing APIM op Bicep: {bicep_path}"
    text = bicep_path.read_text(encoding="utf-8")
    assert "resource op" in text
    assert ROUTES[slug].apim_route in text
