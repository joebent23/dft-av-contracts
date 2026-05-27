
"""Auto-generated from schemas/bronze/bronze-ccav-tx-log-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: bronze-ccav-tx-log
Version:  1.0.0
Entity:   bronze_ccav_tx_log
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BronzeCcavTxLogRow(BaseModel):
    """Row model for ``bronze_ccav_tx_log`` (bronze layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

process: str = Field(
        ...,
        alias="process",
        description='AV Act regulatory process this transaction belongs to. Closed vocabulary per synth-rules table 2. Source CSV header "Process".\n',
    )
transaction_count: int = Field(
        ...,
        alias="transaction_count",
        description='Always 1 per row — each row represents exactly one transaction. Source CSV header "Transaction Count".\n',
    )
dt_references_observed: str = Field(
        ...,
        alias="dt_references_observed",
        description='Single DT reference (e.g. "internal-dt-ref") drawn from the per-process pool defined in the analyst synth-rules. Source CSV header "DT References Observed".\n',
    )
invoice_id: str = Field(
        ...,
        alias="invoice_id",
        description='Invoice / case reference. The hero invoice SI-INV-2025-0001 MUST appear exactly once; all other rows match the synthetic INV-YYYY-NNNNNN-XXXXXX pattern.\n',
    )
vehicle_id: Optional[str] = Field(
        None,
        alias="vehicle_id",
        description='Vehicle natural key — either a 17-char ISO-3779 VIN or the hero UK registration plate "EXAMPLEPLATE01" (kept verbatim once per synth-rules). May be null for non-vehicle-bound transactions.\n',
    )
recall_id: Optional[str] = Field(
        None,
        alias="recall_id",
        description='Optional VCA recall reference if the transaction is linked to an active recall. ~98% of rows are null; the hero VCA-REC-2025-NVR-001 MUST appear at least once.\n',
    )
tx_date: datetime = Field(
        ...,
        alias="tx_date",
        description='UTC timestamp the transaction was recorded by CCAV. Hero row = 2025-07-14T14:30:00Z.\n',
    )
payment_date: Optional[datetime] = Field(
        None,
        alias="payment_date",
        description='UTC timestamp of any associated fee/fine payment. Must be >= tx_date when present. Hero row = 2025-07-15T09:00:00Z.\n',
    )
amount_gbp: Optional[Decimal] = Field(
        None,
        alias="amount_gbp",
        description='Money amount in GBP for any associated fee or fine. Hero row = 12500.00. May be null for no-charge transactions.\n',
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

