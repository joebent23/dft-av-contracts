
"""Auto-generated from schemas/bronze/bronze-dvla-type-approval-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: bronze-dvla-type-approval
Version:  1.0.0
Entity:   bronze_dvla_type_approval
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BronzeBronzeDvlaTypeApprovalRow(BaseModel):
    """Row model for ``bronze_dvla_type_approval`` (bronze layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

model_code: str = Field(
        ...,
        alias="model_code",
        description='AV model natural key (e.g. "MER-SUV-01"). 3-letter manufacturer prefix + 3-letter body-style + sequence. Source CSV header "Model Code".\n',
    )
model_name: str = Field(
        ...,
        alias="model_name",
        description='Manufacturer marque + commercial model name + body style (e.g. "Meridian Horizon SUV"). Source CSV header "Model Name".\n',
    )
manufacturer: str = Field(
        ...,
        alias="manufacturer",
        description='Legal name of the vehicle manufacturer. Drawn from the closed seven-entry pool defined in synth-rules table 3. Source CSV header "Manufacturer".\n',
    )
asde: str = Field(
        ...,
        alias="asde",
        description='Legal name of the Authorised Self-Driving Entity. Most rows asde == manufacturer; for some Apex models the ASDE is Crestline AV Solutions Ltd. Source CSV header "ASDE".\n',
    )
approval_date: str = Field(
        ...,
        alias="approval_date",
        description='British human-readable approval date (e.g. "14 February 2024"). internal data lineage parses into a typed date at Silver. Source CSV header "Approval Date".\n',
    )
certificate_reference: str = Field(
        ...,
        alias="certificate_reference",
        description='VCA type-approval certificate reference (PK). Year matches approval_date year; MFR + TYPE match model_code. Source CSV header "Certificate Reference".\n',
    )
max_speed_kmh: int = Field(
        ...,
        alias="max_speed_kmh",
        description='Maximum approved operating speed of the AV model in km/h. Closed vocabulary {70, 80, 90, 100, 110, 120} per synth-rules table 3. Source CSV header "Max Speed km/h".\n',
    )
weather_exclusions: str = Field(
        ...,
        alias="weather_exclusions",
        description='Authorised weather envelope exclusions. Closed vocabulary per synth-rules table 3. Source CSV header "Weather Exclusions".\n',
    )
status: str = Field(
        ...,
        alias="status",
        description='Type-approval status of the model. Closed vocabulary per synth-rules. Source CSV header "Status".\n',
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

