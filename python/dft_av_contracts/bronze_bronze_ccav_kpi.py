
"""Auto-generated from schemas/bronze/bronze-ccav-kpi-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: bronze-ccav-kpi
Version:  1.0.0
Entity:   bronze_ccav_kpi
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BronzeBronzeCcavKpiRow(BaseModel):
    """Row model for ``bronze_ccav_kpi`` (bronze layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

process: str = Field(
        ...,
        alias="process",
        description='AV Act regulatory process the KPI summarises. Closed vocabulary of six values per analyst synth-rules (table 1). Source CSV header "Process".\n',
    )
transaction_count: int = Field(
        ...,
        alias="transaction_count",
        description='Count of regulatory transactions of this process type in the reporting period. Realistic range 1–500 per process per quarter. Source CSV header "Transaction Count".\n',
    )
pct_of_total: Decimal = Field(
        ...,
        alias="pct_of_total",
        description='Share of the period\'s total transactions attributable to this process, rounded to one decimal place. All rows in a period MUST sum to 100.0 ± 0.5. Source CSV header "Pct of Total".\n',
    )
key_dt_references: str = Field(
        ...,
        alias="key_dt_references",
        description='Comma-separated list of Data Tracker DT references the analyst associates with this process (e.g. "internal-dt-ref" for Registration). Preserved verbatim from source. Source CSV header "Key DT References".\n',
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
        description='Audit column — UUID linking the row to the ingest batch / API call.',
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

