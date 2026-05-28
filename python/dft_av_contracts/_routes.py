"""Auto-generated. DO NOT EDIT BY HAND.

Ingest route registry compiled from contract YAML ``routing:`` blocks.
Regenerate via ``tools/codegen/generate_pydantic.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Type

from pydantic import BaseModel

from .bronze_dvsa_aps_perf import BronzeDvsaApsPerfRow
from .bronze_ccav_kpi import BronzeCcavKpiRow
from .bronze_asde_incident_push import BronzeAsdeIncidentPushRow
from .bronze_ismr_occurrences import BronzeIsmrOccurrencesRow


@dataclass(frozen=True)
class RouteMeta:
    """Ingest route metadata for one contract doctype_slug."""
    doctype_slug: str
    contract_id: str
    contract_version: str
    lane: int
    apim_api: str
    apim_route: str
    http_method: str
    required_personas: tuple[str, ...]
    required_headers: tuple[str, ...]
    publishes_event: bool
    event_type: str | None
    event_subject_template: str | None
    event_grid_topic_name: str | None
    pydantic_model: Type[BaseModel]
    json_schema_filename: str


ROUTES: dict[str, RouteMeta] = {
    "dvsa-aps-perf": RouteMeta(
        doctype_slug="dvsa-aps-perf",
        contract_id="bronze-dvsa-aps-perf",
        contract_version="1.0.0",
        lane=5,
        apim_api="ingest",
        apim_route="/dvsa/aps-performance",
        http_method="POST",
        required_personas=('nuico_compliance',),
        required_headers=('x-correlation-id', 'x-contract-version'),
        publishes_event=True,
        event_type='dft.av.dvsa-aps-perf.ingested.v1',
        event_subject_template='dvsaApsPerf/{route_ref}/{period_month}',
        event_grid_topic_name='dft-av-egt-{env}',
        pydantic_model=BronzeDvsaApsPerfRow,
        json_schema_filename="dvsa-aps-perf.schema.json",
    ),
    "nuico-ccav-kpi": RouteMeta(
        doctype_slug="nuico-ccav-kpi",
        contract_id="bronze-ccav-kpi",
        contract_version="1.0.0",
        lane=5,
        apim_api="ingest",
        apim_route="/ccav/kpi-quarterly",
        http_method="POST",
        required_personas=('ccav_analyst',),
        required_headers=('x-correlation-id', 'x-contract-version'),
        publishes_event=True,
        event_type='dft.av.nuico-ccav-kpi.ingested.v1',
        event_subject_template='ccavKpi/{quarter}',
        event_grid_topic_name='dft-av-egt-{env}',
        pydantic_model=BronzeCcavKpiRow,
        json_schema_filename="nuico-ccav-kpi.schema.json",
    ),
    "si-inv": RouteMeta(
        doctype_slug="si-inv",
        contract_id="bronze-asde-incident-push",
        contract_version="1.0.0",
        lane=4,
        apim_api="ingest",
        apim_route="/asde/incident-liability",
        http_method="POST",
        required_personas=('statutory_inspector',),
        required_headers=('x-correlation-id', 'x-contract-version'),
        publishes_event=True,
        event_type='dft.av.si-inv.ingested.v1',
        event_subject_template='siInv/{investigation_reference}',
        event_grid_topic_name='dft-av-egt-{env}',
        pydantic_model=BronzeAsdeIncidentPushRow,
        json_schema_filename="si-inv.schema.json",
    ),
    "si-ismr": RouteMeta(
        doctype_slug="si-ismr",
        contract_id="bronze-ismr-occurrences",
        contract_version="1.0.0",
        lane=5,
        apim_api="ingest",
        apim_route="/nuico/ismr-occurrences",
        http_method="POST",
        required_personas=('nuico_compliance',),
        required_headers=('x-correlation-id', 'x-contract-version'),
        publishes_event=True,
        event_type='dft.av.si-ismr.ingested.v1',
        event_subject_template='siIsmr/{period}',
        event_grid_topic_name='dft-av-egt-{env}',
        pydantic_model=BronzeIsmrOccurrencesRow,
        json_schema_filename="si-ismr.schema.json",
    ),
}

__all__ = ["RouteMeta", "ROUTES"]
