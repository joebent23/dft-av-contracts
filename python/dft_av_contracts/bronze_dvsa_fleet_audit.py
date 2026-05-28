
"""Auto-generated from schemas/bronze/bronze-dvsa-fleet-audit-v2.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: bronze-dvsa-fleet-audit
Version:  2.0.0
Entity:   bronze_dvsa_fleet_audit
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BronzeDvsaFleetAuditRow(BaseModel):
    """Row model for ``bronze_dvsa_fleet_audit`` (bronze layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    nuico_name: str = Field(
        ...,
        alias="nuico_name",
        description='Registered legal name of the NUiCO (Numbered User in Charge of Operations) — the licensed AV operator under the AV Act. Source CSV header "NUiCO Name".\n',
    )
    licence_reference: str = Field(
        ...,
        alias="licence_reference",
        description='DVSA-issued NUiCO operator licence reference. Primary natural key across DVSA, NUiCO and Licensing release. Source CSV header "Licence Reference".\n',
    )
    fleet_size: int = Field(
        ...,
        alias="fleet_size",
        description='Count of vehicles operating under this NUiCO at audit time. Realistic range 3–25 per synth-rules table 5. Source CSV header "Fleet Size".\n',
    )
    inspections_passed: int = Field(
        ...,
        alias="inspections_passed",
        description='Count of vehicles in the fleet that passed inspection in the audit period. Must be <= fleet_size. Source CSV header "Inspections Passed".\n',
    )
    recall_exposure: str = Field(
        ...,
        alias="recall_exposure",
        description='Whether any vehicle in this fleet is in scope of an active VCA recall against its model. Tri-state flag; the actual recall join is performed in Silver. Source CSV header "Recall Exposure".\n',
    )
    status: str = Field(
        ...,
        alias="status",
        description='Operator licence status at audit time. Source CSV header "Status".\n',
    )
    ingested_at_utc: datetime = Field(
        ...,
        alias="_ingested_at_utc",
        description='Audit column — UTC timestamp when the row landed in Bronze.',
    )
    source_file: Optional[str] = Field(
        None,
        alias="_source_file",
        description='Audit column — source object URI (mirroring snapshot file).',
    )
    correlation_id: str = Field(
        ...,
        alias="_correlation_id",
        description='Audit column — UUID linking the row to the mirroring batch.',
    )
    dq_status: str = Field(
        ...,
        alias="_dq_status",
        description='Audit column — DQ Gate verdict set by internal data lineage.',
    )
    source_lane: str = Field(
        ...,
        alias="_source_lane",
        description='Audit column — internal ingest lane that delivered this row.',
    )
    raw_blob_path: str = Field(
        ...,
        alias="_raw_blob_path",
        description='Audit column — full ABFSS / S3 / queue URI of the raw payload as it landed in the source landing zone. Used for forensic replay and Purview lineage back to the raw blob. Supersedes the older _source_file audit column (kept for backward compatibility with ADR-002 v1 consumers); new ingest notebooks MUST set both to the same value when the source is file-shaped.\n',
    )
    contract_version: str = Field(
        ...,
        alias="_contract_version",
        description='Audit column — semver of the Bronze ODCS contract under which this row was written (matches metadata.version). Lets Silver and the DQ Gate detect contract drift without re-reading the YAML.\n',
    )

