
"""Auto-generated from schemas/bronze/bronze-asde-incident-push-v1.yaml.

DO NOT EDIT BY HAND. Regenerate via ``tools/codegen/generate_pydantic.py``.

Contract: bronze-asde-incident-push
Version:  1.0.0
Entity:   bronze_asde_incident_push
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BronzeBronzeAsdeIncidentPushRow(BaseModel):
    """Row model for ``bronze_asde_incident_push`` (bronze layer)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

schema_version: str = Field(
        ...,
        alias="schema_version",
        description='ASDE-partner package schema version (currently "1.0"). Source JSON key "schema_version".\n',
    )
document_type: str = Field(
        ...,
        alias="document_type",
        description='Fixed payload discriminator. Source JSON key "document_type".\n',
    )
investigation_reference: str = Field(
        ...,
        alias="investigation_reference",
        description='Statutory Inspector investigation reference (PK). The hero SI-INV-2025-0001 MUST round-trip verbatim. Source JSON key "investigation_reference".\n',
    )
incident_date: date = Field(
        ...,
        alias="incident_date",
        description='ISO date the incident occurred. Source JSON key "incident_date".\n',
    )
incident_location: str = Field(
        ...,
        alias="incident_location",
        description='Free-text human-readable location of the incident. Source JSON key "incident_location".\n',
    )
dt_references: str = Field(
        ...,
        alias="dt_references",
        description='Array of Data Tracker DT references the incident touches. Source JSON key "dt_references".\n',
    )
vehicle_vin: str = Field(
        ...,
        alias="vehicle_vin",
        description='Vehicle Identification Number — either a 17-char ISO-3779 VIN for sister packages or the hero UK plate "EXAMPLEPLATE01" / "an internal scenario" for SI-INV-2025-0001. Source JSON key "vehicle.vin".\n',
    )
vehicle_registration_mark: Optional[str] = Field(
        None,
        alias="vehicle_registration_mark",
        description='UK registration mark of the vehicle. Source JSON key "vehicle.registration_mark".\n',
    )
vehicle_model_code: str = Field(
        ...,
        alias="vehicle_model_code",
        description='FK to bronze_dvla_type_approval.model_code. Source JSON key "vehicle.model_code".\n',
    )
vehicle_model_name: str = Field(
        ...,
        alias="vehicle_model_name",
        description='Human-readable model name. Source JSON key "vehicle.model_name".\n',
    )
asde_reference: str = Field(
        ...,
        alias="asde_reference",
        description='ASDE reference. Source JSON key "entities.asde.reference".\n',
    )
asde_name: str = Field(
        ...,
        alias="asde_name",
        description='Legal name of the ASDE. Source JSON key "entities.asde.name".\n',
    )
nuico_reference: str = Field(
        ...,
        alias="nuico_reference",
        description='FK to bronze_dvsa_fleet_audit.licence_reference. Source JSON key "entities.nuico.reference".\n',
    )
nuico_name: str = Field(
        ...,
        alias="nuico_name",
        description='Legal name of the NUiCO. Source JSON key "entities.nuico.name".\n',
    )
speed_kmh: Decimal = Field(
        ...,
        alias="speed_kmh",
        description='Vehicle speed at incident in km/h. Source JSON key "technical_data.speed_kmh".\n',
    )
emergency_braking_pct: Decimal = Field(
        ...,
        alias="emergency_braking_pct",
        description='Emergency braking application percentage (0.0–100.0). Source JSON key "technical_data.emergency_braking_pct".\n',
    )
ads_state: str = Field(
        ...,
        alias="ads_state",
        description='ADS engagement state at incident. Source JSON key "technical_data.ads_state".\n',
    )
failure_mode: str = Field(
        ...,
        alias="failure_mode",
        description='ADS failure-mode tag (e.g. FAIL_PLANNER, FAIL_CYBER_AUTH, FAIL_PERCEPTION, FAIL_V2X). Source JSON key "technical_data.failure_mode".\n',
    )
odd_road_type_compliance: str = Field(
        ...,
        alias="odd_road_type_compliance",
        description='Road-type ODD compliance verdict. Source JSON key "odd_assessment.road_type_compliance".\n',
    )
odd_speed_compliance: str = Field(
        ...,
        alias="odd_speed_compliance",
        description='Speed-band ODD compliance verdict. Source JSON key "odd_assessment.speed_compliance".\n',
    )
odd_time_of_day_compliance: str = Field(
        ...,
        alias="odd_time_of_day_compliance",
        description='Time-of-day ODD compliance verdict. Source JSON key "odd_assessment.time_of_day_compliance".\n',
    )
odd_weather_compliance: str = Field(
        ...,
        alias="odd_weather_compliance",
        description='Weather ODD compliance verdict. Source JSON key "odd_assessment.weather_compliance".\n',
    )
overall_odd_status: str = Field(
        ...,
        alias="overall_odd_status",
        description='Overall ODD verdict. Source JSON key "odd_assessment.overall_odd_status".\n',
    )
cyber_incident_reference: Optional[str] = Field(
        None,
        alias="cyber_incident_reference",
        description='Optional UN R155 cyber incident reference (e.g. R155-INC-NVR-2025-001). Present only when the package includes a cyber_incident block. Source JSON key "cyber_incident.reference".\n',
    )
cyber_incident_category: Optional[str] = Field(
        None,
        alias="cyber_incident_category",
        description='Optional cyber-incident category (e.g. UN_R155_CSMS_VULNERABILITY). Source JSON key "cyber_incident.category".\n',
    )
cyber_incident_vector: Optional[str] = Field(
        None,
        alias="cyber_incident_vector",
        description='Optional free-text description of the attack vector. Source JSON key "cyber_incident.vector".\n',
    )
cyber_ads_telemetry_anomaly: Optional[str] = Field(
        None,
        alias="cyber_ads_telemetry_anomaly",
        description='Optional free-text description of any related ADS telemetry anomaly. Source JSON key "cyber_incident.ads_telemetry_anomaly".\n',
    )
primary_liability: str = Field(
        ...,
        alias="primary_liability",
        description='Free-text statement of primary liability attribution. Source JSON key "liability_indicators.primary_liability".\n',
    )
contributing_liability: Optional[str] = Field(
        None,
        alias="contributing_liability",
        description='Free-text statement of any contributing liability. Source JSON key "liability_indicators.contributing_liability".\n',
    )
active_recall_at_incident: bool = Field(
        ...,
        alias="active_recall_at_incident",
        description='Whether a VCA recall was active against the vehicle\'s model at the incident date. Source JSON key "liability_indicators.active_recall_at_incident".\n',
    )
recall_reference: Optional[str] = Field(
        None,
        alias="recall_reference",
        description='Optional VCA recall reference if active_recall_at_incident is true. The hero VCA-REC-2025-NVR-001 MUST appear at least once (SI-INV-2025-0001). Source JSON key "liability_indicators.recall_reference".\n',
    )
insurance_notification_required: bool = Field(
        ...,
        alias="insurance_notification_required",
        description='Whether the package triggers a regulatory insurance notification. Source JSON key "liability_indicators.insurance_notification_required".\n',
    )
generated_date: date = Field(
        ...,
        alias="generated_date",
        description='ISO date the package was generated by the ASDE partner. Source JSON key "generated_date".\n',
    )
status: str = Field(
        ...,
        alias="status",
        description='Package status. Source JSON key "status".\n',
    )
raw_payload: str = Field(
        ...,
        alias="raw_payload",
        description='Verbatim JSON payload as received over APIM, preserved for replay and forensic audit. Silver re-parses if the schema evolves.\n',
    )
ingested_at_utc: datetime = Field(
        ...,
        alias="_ingested_at_utc",
        description='Audit column — UTC timestamp when the row landed in Bronze.',
    )
source_file: Optional[str] = Field(
        None,
        alias="_source_file",
        description='Audit column — APIM push URI / Event Grid event id.',
    )
correlation_id: str = Field(
        ...,
        alias="_correlation_id",
        description='Audit column — UUID linking the row to the APIM call.',
    )
dq_status: str = Field(
        ...,
        alias="_dq_status",
        description='Audit column — DQ Gate verdict set by internal data lineage.',
    )
source_lane: str = Field(
        ...,
        alias="_source_lane",
        description='Audit column — internal ingest lane (always "push" here).',
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

