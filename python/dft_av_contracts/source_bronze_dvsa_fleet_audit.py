
"""Auto-generated from schemas/source/dvsa-fleet-audit-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: dvsa-fleet-audit
Version:  1.0.0
Entity:   bronze_dvsa_fleet_audit
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceBronzeDvsaFleetAuditRow(BaseModel):
    """Row model for ``bronze_dvsa_fleet_audit`` (source layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

nuico_name: str = Field(
        ...,
        alias="nuico_name",
        description='Registered legal name of the NUiCO (Numbered User in Charge of Operations) — the licensed AV operator under the AV Act. Source CSV header "NUiCO Name".\n',
    )
licence_reference: str = Field(
        ...,
        alias="licence_reference",
        description='DVSA-issued NUiCO operator licence reference. Primary natural key for an operator across DVSA, NUiCO and Licensing release. Source CSV header "Licence Reference".\n',
    )
fleet_size: int = Field(
        ...,
        alias="fleet_size",
        description='Count of vehicles operating under this NUiCO at audit time. Range 0..10000. Source CSV header "Fleet Size".\n',
    )
inspections_passed: int = Field(
        ...,
        alias="inspections_passed",
        description='Count of vehicles in the fleet that passed inspection in the audit period. Must be <= fleet_size (enforced by DQ-CONS-FLEET-AUDIT-01). Source CSV header "Inspections Passed".\n',
    )
recall_exposure: str = Field(
        ...,
        alias="recall_exposure",
        description='Whether any vehicle in this fleet is in scope of an active VCA recall against its model. Flag-only summary; the join to VCA recall is performed in Silver. Source CSV header "Recall Exposure".\n',
    )
status: str = Field(
        ...,
        alias="status",
        description='Operator status at audit time. Source CSV header "Status".\n',
    )
ingested_at_utc: datetime = Field(
        ...,
        alias="_ingested_at_utc",
        description='Audit column — when the row landed in Bronze.',
    )
source_file: Optional[str] = Field(
        None,
        alias="_source_file",
        description='Audit column — source CSV path (e.g. s3://dvsa-data-exchange/fleet-audit/DVSA-FLEET-AUDIT-2025-001_fleet_data.csv).\n',
    )
correlation_id: str = Field(
        ...,
        alias="_correlation_id",
        description='Audit column — end-to-end ingestion correlation id.',
    )
dq_status: str = Field(
        ...,
        alias="_dq_status",
        description='Audit column — DQ engine verdict.',
    )

