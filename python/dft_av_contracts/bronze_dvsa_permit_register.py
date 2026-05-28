
"""Auto-generated from schemas/bronze/bronze-dvsa-permit-register-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: bronze-dvsa-permit-register
Version:  1.0.0
Entity:   bronze_dvsa_permit_register
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BronzeDvsaPermitRegisterRow(BaseModel):
    """Row model for ``bronze_dvsa_permit_register`` (bronze layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    permit_reference: str = Field(
        ...,
        alias="permit_reference",
        description='DVSA-issued APS permit reference (PK). Year + 3-digit sequence. Source CSV header "Permit Reference".\n',
    )
    nuico_name: str = Field(
        ...,
        alias="nuico_name",
        description='NUiCO operating under this permit. Joins to bronze_dvsa_fleet_audit.nuico_name in Silver. Source CSV header "NUiCO Name".\n',
    )
    issue_date: str = Field(
        ...,
        alias="issue_date",
        description='British human-readable issue date (e.g. "12 August 2024"). Track D parses into a typed date at Silver. Source CSV header "Issue Date".\n',
    )
    expiry_date: str = Field(
        ...,
        alias="expiry_date",
        description='British human-readable expiry date — three years after issue per the seed pattern. Source CSV header "Expiry Date".\n',
    )
    local_authority: str = Field(
        ...,
        alias="local_authority",
        description='UK local authority where the permit operates. Drawn from the closed 14-entry pool defined in synth-rules table 6. Source CSV header "Local Authority".\n',
    )
    region: str = Field(
        ...,
        alias="region",
        description='UK ITL1 region. MUST be consistent with local_authority. Source CSV header "Region".\n',
    )
    routes: str = Field(
        ...,
        alias="routes",
        description='Semicolon-separated list of 2–3 route refs (e.g. "FR-001; FR-002") covered by the permit. Silver explodes this into the permit↔route bridge. Source CSV header "Routes".\n',
    )
    status: str = Field(
        ...,
        alias="status",
        description='Permit status. Closed vocabulary per synth-rules table 6. Source CSV header "Status".\n',
    )
    ingested_at_utc: datetime = Field(
        ...,
        alias="_ingested_at_utc",
        description='Audit column — UTC timestamp when the row landed in Bronze.',
    )
    source_file: Optional[str] = Field(
        None,
        alias="_source_file",
        description='Audit column — source CSV filename or URI.',
    )
    correlation_id: str = Field(
        ...,
        alias="_correlation_id",
        description='Audit column — UUID linking the row to the pipeline run.',
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

