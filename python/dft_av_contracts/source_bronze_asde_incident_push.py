
"""Auto-generated from schemas/source/asde-incident-push-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: asde-incident-push
Version:  1.0.0
Entity:   bronze_asde_incident_push
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceBronzeAsdeIncidentPushRow(BaseModel):
    """Row model for ``bronze_asde_incident_push`` (source layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

asde_reference: str = Field(
        ...,
        alias="asde_reference",
        description='Operator-issued incident reference. Globally unique per operator. Used as the partner-side natural key for the incident. Source JSON field `asdeReference`.\n',
    )
incident_at_utc: datetime = Field(
        ...,
        alias="incident_at_utc",
        description='ISO-8601 UTC instant the incident occurred (NOT submission time). Source JSON field `incidentAtUtc`. Must be ≤ current UTC and ≥ 1970-01-01.\n',
    )
vehicle_vin: str = Field(
        ...,
        alias="vehicle_vin",
        description='17-character VIN of the vehicle involved (ISO 3779). Excludes I, O, Q. Source JSON field `vehicleVin`.\n',
    )
operator_licence_reference: str = Field(
        ...,
        alias="operator_licence_reference",
        description="Operator's NUiCO licence reference (joins to DVSA fleet audit). Source JSON field `operatorLicenceReference`.\n",
    )
incident_class: str = Field(
        ...,
        alias="incident_class",
        description='Coarse category for routing + DQ. Source JSON field `incidentClass`.\n',
    )
severity: str = Field(
        ...,
        alias="severity",
        description='Severity tier per ASDE Operator Code of Practice. Tier-1 = injury or fatality; Tier-2 = damage only; Tier-3 = no damage, behavioural anomaly. Source JSON field `severity`.\n',
    )
location_lat: Decimal = Field(
        ...,
        alias="location_lat",
        description='Incident latitude in WGS84. Range -90..90. Source JSON field `location.lat`.\n',
    )
location_lon: Decimal = Field(
        ...,
        alias="location_lon",
        description='Incident longitude in WGS84. Range -180..180. Source JSON field `location.lon`.\n',
    )
description: Optional[str] = Field(
        None,
        alias="description",
        description='Operator-supplied free-text incident description, ≤ 2000 chars. Not used for routing or DQ. Source JSON field `description`.\n',
    )
witnesses: Optional[str] = Field(
        None,
        alias="witnesses",
        description='Optional array of witness reference strings (NOT names — references already pseudonymised by operator). Source JSON field `witnesses`.\n',
    )
ingested_at_utc: datetime = Field(
        ...,
        alias="_ingested_at_utc",
        description='Audit column added by the Function — UTC instant the row landed in Bronze raw.\n',
    )
source_submitter_org: str = Field(
        ...,
        alias="_source_submitter_org",
        description='Audit column added by the Function from the `X-Submitter-Org` header set by APIM via product/subscription mapping. `unknown` if header absent.\n',
    )
correlation_id: str = Field(
        ...,
        alias="_correlation_id",
        description='Audit column. Echo of `X-Correlation-Id` request header if present, else a Function-generated UUID v4. Returned to the caller in the HTTP 202 body and `X-Correlation-Id` response header. Propagated into the CloudEvent as the `correlationid` extension.\n',
    )
ingest_id: str = Field(
        ...,
        alias="_ingest_id",
        description='Audit column. Function-generated UUID v4 used for the blob filename (safe by construction; partner-supplied correlation_id is never put on disk in the path).\n',
    )

