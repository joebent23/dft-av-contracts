
"""Auto-generated from schemas/bronze/bronze-dvla-vehicle-registry-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: bronze-dvla-vehicle-registry
Version:  1.0.0
Entity:   bronze_dvla_vehicle_registry
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BronzeDvlaVehicleRegistryRow(BaseModel):
    """Row model for ``bronze_dvla_vehicle_registry`` (bronze layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    vin: str = Field(
        ...,
        alias="vin",
        description='17-character Vehicle Identification Number (PK). Mirror column `vin`. Hero VIN for the an internal scenario scenario is `NVR07250000000032`.\n',
    )
    registration_mark: str = Field(
        ...,
        alias="registration_mark",
        description='Current GB vehicle registration mark (e.g. "AV24 PEN"). Mirror column `registration_mark`.\n',
    )
    model_code: str = Field(
        ...,
        alias="model_code",
        description='AV model natural key — joins to bronze_dvla_type_approval.model_code. Mirror column `model_code`.\n',
    )
    manufacturer: str = Field(
        ...,
        alias="manufacturer",
        description='Legal name of the vehicle manufacturer. Mirror column `manufacturer`.\n',
    )
    asde: str = Field(
        ...,
        alias="asde",
        description='Legal name of the Authorised Self-Driving Entity. Mirror column `asde`.\n',
    )
    keeper_category: str = Field(
        ...,
        alias="keeper_category",
        description='Registered-keeper classification. Closed vocabulary. Mirror column `keeper_category`.\n',
    )
    first_registered_date: str = Field(
        ...,
        alias="first_registered_date",
        description='ISO-8601 date the vehicle was first registered with DVLA. Mirror column `first_registered_date`.\n',
    )
    status: str = Field(
        ...,
        alias="status",
        description='Current registration status. Closed vocabulary. Mirror column `status`.\n',
    )
    ingested_at_utc: datetime = Field(
        ...,
        alias="_ingested_at_utc",
        description='Audit column — UTC timestamp when the row landed in Bronze.',
    )
    source_lane: str = Field(
        ...,
        alias="_source_lane",
        description='Audit column — internal ingest lane that delivered this row.',
    )
    correlation_id: str = Field(
        ...,
        alias="_correlation_id",
        description='Audit column — UUID linking the row to the mirroring batch.',
    )
    raw_blob_path: str = Field(
        ...,
        alias="_raw_blob_path",
        description='Audit column — source identifier for the row. For mirror-fed Bronze this is the synthetic URI `mirror:dvla_vehicle_registry`.\n',
    )
    contract_version: str = Field(
        ...,
        alias="_contract_version",
        description='Audit column — semver of the Bronze ODCS contract under which this row was written (matches metadata.version).\n',
    )

