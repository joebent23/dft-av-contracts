"""Lane-4 dual-validator smoke for the ``si-inv`` slug.

Demonstrates that the generated JSON Schema (which APIM enforces at the
edge via ``validate-content``) and the generated Pydantic model (which
the Cockpit Function runs server-side) agree on the same payload:

* A valid ``si-inv`` row passes BOTH validators.
* A row missing a required field is rejected by BOTH validators.
* A row with an extra unknown field is rejected by BOTH validators
  (JSON schema sets ``additionalProperties: false``; Pydantic sets
  ``model_config = ConfigDict(extra="forbid")``).
* A row with a wrong-type field is rejected by BOTH validators.

This is the local stand-in for the cross-repo E2E smoke; once Phase-3
ships APIM + Functions, the same payload runs through real APIM and a
real Function and the parity must continue to hold.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "json" / "si-inv.schema.json"

# Make the generated Pydantic package importable without an install step.
sys.path.insert(0, str(REPO_ROOT / "python"))

from dft_av_contracts.bronze_asde_incident_push import (  # noqa: E402
    BronzeAsdeIncidentPushRow,
)


def _valid_payload() -> dict:
    """Build a minimal ``si-inv`` payload that satisfies all required fields.

    Values mirror the hero scenario ``SI-INV-2025-0001`` referenced in
    ``schemas/bronze/bronze-asde-incident-push-v1.yaml``.
    """
    return {
        "schema_version": "1.0",
        "document_type": "asde.incident.push",
        "investigation_reference": "SI-INV-2025-0001",
        "incident_date": "2025-09-14",
        "incident_location": "M40 J3, southbound, lane 2",
        "dt_references": "DT-2025-0042,DT-2025-0043",
        "vehicle_vin": "EXAMPLEPLATE01",
        "vehicle_model_code": "AV-MK1",
        "vehicle_model_name": "Example AV Mark I",
        "asde_reference": "ASDE-PARTNER-A",
        "asde_name": "Example ASDE Partner",
        "nuico_reference": "NUICO-OP-01",
        "nuico_name": "Example NUICO Operator",
        "speed_kmh": 48.5,
        "emergency_braking_pct": 92.0,
        "ads_state": "engaged",
        "failure_mode": "perception_dropout",
        "odd_road_type_compliance": "compliant",
        "odd_speed_compliance": "compliant",
        "odd_time_of_day_compliance": "compliant",
        "odd_weather_compliance": "compliant",
        "overall_odd_status": "in_odd",
        "primary_liability": "asde",
        "active_recall_at_incident": False,
        "insurance_notification_required": True,
        "generated_date": "2025-09-15",
        "status": "submitted",
        "raw_payload": "{\"document_type\":\"asde.incident.push\"}",
        "_ingested_at_utc": "2025-09-15T10:00:00Z",
        "_correlation_id": "11111111-1111-1111-1111-111111111111",
        "_dq_status": "ok",
        "_source_lane": "lane-4-asde",
        "_raw_blob_path": "raw/lane-4/SI-INV-2025-0001.json",
        "_contract_version": "1.0.0",
    }


@pytest.fixture(scope="module")
def json_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    # Enable format validation so ``format: date`` / ``date-time`` are enforced
    # at the edge — matches the Pydantic server behaviour and the APIM policy
    # config we ship in Phase-3 (validate-content with format-strict).
    return Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )


def _json_ok(validator: Draft202012Validator, payload: dict) -> bool:
    return not list(validator.iter_errors(payload))


def _pydantic_ok(payload: dict) -> bool:
    try:
        BronzeAsdeIncidentPushRow.model_validate(payload)
    except Exception:
        return False
    return True


def test_valid_payload_passes_both_validators(json_validator):
    payload = _valid_payload()
    assert _json_ok(json_validator, payload), (
        "Edge (JSON Schema) rejected the valid payload — APIM would 400 it."
    )
    assert _pydantic_ok(payload), (
        "Server (Pydantic) rejected the valid payload — Function would 422 it."
    )


@pytest.mark.parametrize(
    "mutation_id, mutate",
    [
        (
            "missing_required",
            lambda p: p.pop("investigation_reference"),
        ),
        (
            "wrong_type_boolean",
            lambda p: p.__setitem__("active_recall_at_incident", "not-a-bool"),
        ),
        (
            "extra_unknown_field",
            lambda p: p.__setitem__("definitely_not_in_contract", "boom"),
        ),
        (
            "wrong_format_date",
            lambda p: p.__setitem__("incident_date", "14/09/2025"),
        ),
    ],
)
def test_invalid_payload_rejected_by_both_validators(
    json_validator, mutation_id, mutate
):
    payload = _valid_payload()
    mutate(payload)
    edge_ok = _json_ok(json_validator, payload)
    server_ok = _pydantic_ok(payload)
    assert edge_ok == server_ok, (
        f"Dual-validator drift on mutation {mutation_id!r}: "
        f"edge_ok={edge_ok} server_ok={server_ok}"
    )
    assert not edge_ok, (
        f"Mutation {mutation_id!r} unexpectedly accepted by both validators."
    )


def test_payload_immutability_between_cases(json_validator):
    # Sanity: mutations above must not have polluted the fixture builder.
    base = _valid_payload()
    snapshot = copy.deepcopy(base)
    assert _json_ok(json_validator, base)
    assert _pydantic_ok(base)
    assert base == snapshot
