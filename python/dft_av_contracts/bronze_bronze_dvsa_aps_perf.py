
"""Auto-generated from schemas/bronze/bronze-dvsa-aps-perf-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: bronze-dvsa-aps-perf
Version:  1.0.0
Entity:   bronze_dvsa_aps_perf
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BronzeBronzeDvsaApsPerfRow(BaseModel):
    """Row model for ``bronze_dvsa_aps_perf`` (bronze layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

route_ref: str = Field(
        ...,
        alias="route_ref",
        description='APS route natural key (e.g. "FR-001"). 2-letter operator prefix + sequence. FK to dim_permits.routes once Silver joins on the semicolon-split list. Source CSV header "Route Ref".\n',
    )
route_description: str = Field(
        ...,
        alias="route_description",
        description='Human-readable route description, typically "<Origin> to <Destination>". Source CSV header "Route Description".\n',
    )
journeys: int = Field(
        ...,
        alias="journeys",
        description='Count of completed passenger journeys on the route in the reporting month. Realistic range 3,000–6,000 per synth-rules table 4. Source CSV header "Journeys".\n',
    )
on_time_pct: Decimal = Field(
        ...,
        alias="on_time_pct",
        description='Share of journeys arriving within the DVSA-defined on-time window. Range 88.0–99.0. Source CSV header "On-Time Pct".\n',
    )
ads_interventions_per_1000km: Decimal = Field(
        ...,
        alias="ads_interventions_per_1000km",
        description='Number of ADS hand-back / safety driver intervention events per 1000 km of journey distance. Range 5.0–60.0. Lower is better. Source CSV header "ADS Interventions per 1000km".\n',
    )
passenger_satisfaction: Decimal = Field(
        ...,
        alias="passenger_satisfaction",
        description='Mean passenger satisfaction score on a 1.0–5.0 scale. Realistic range 3.0–5.0. Source CSV header "Passenger Satisfaction".\n',
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
        description='Audit column — UUID linking the row to the upload batch.',
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

