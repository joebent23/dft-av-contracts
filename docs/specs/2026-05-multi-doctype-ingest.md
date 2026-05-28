# Spec — Multi-doctype ingest codegen (2026-05)

Status: draft  
Owner: platform/cockpit alignment workstream  
Locked decisions ref: `/memories/session/phase0-inventory.md` (Phase 0, 2026-05-28)

## Why

Today `dft-av-contracts` emits Pydantic v2 stubs per YAML contract. The platform Lane-4 Function validates with stand-alone `jsonschema` files and the new ingest Functions plus APIM ops have no shared source of truth. We need this repo to be the single producer of:

1. Pydantic v2 models (already done)
2. JSON Schema files consumable by APIM `<validate-content>` and by stand-alone validators
3. A `RouteMeta` constant per doctype that downstream Functions import to know where to write in ADLS and which CloudEvent type to emit
4. Per-doctype APIM Bicep operation fragments so adding a doctype = single PR to this repo

## Scope (in)

- Add `doctype_slug: <snake_case>` field at YAML top level (alongside `metadata`) for every bronze YAML
- Add `publishes_event: true|false` and (when true) `event:` block with `type: uk.gov.dft.av.<...>.v1` and `source_urn` to every bronze YAML
- Extend `tools/codegen/generate_pydantic.py` to also emit:
  - `python/dft_av_contracts/<kind>_<entity>_routemeta.py` exposing `ROUTE_META: RouteMeta`
  - `schemas/json/<doctype-slug>.schema.json` (Draft 2020-12) derived from the YAML
  - `iac/apim-ops/<doctype-slug>.bicep` operation+policy fragment with inlined schema ref
- Pytest fixtures: one round-trip sample JSON per doctype under `tests/fixtures/<doctype-slug>.json`; test asserts Pydantic and JSON Schema both accept the fixture and produce byte-stable serialisation
- `MANIFEST.yaml` gains a `route_meta_version` field for downstream lockstep

## Scope (out)

- No new bronze YAMLs in this PR; only the 9 existing ones get the new fields
- No silver/gold contract changes
- APIM Bicep fragments are *generated artefacts only* — `dft-av-platform` consumes them, not this repo

## Non-functional

- Generator must be deterministic (sorted keys, fixed timestamps) so `git diff` after re-run is clean
- `pytest -q` runtime budget: ≤ 10 s
- Python 3.11 baseline

## RouteMeta shape

```python
@dataclass(frozen=True)
class RouteMeta:
    doctype_slug: str           # e.g. "asde_r155_inc"
    apim_route: str             # e.g. "/asde-r155-inc"
    adls_path: str              # e.g. "by-doctype/asde_r155_inc/"
    publishes_event: bool
    event_type: str | None      # e.g. "uk.gov.dft.av.safety.incident.reported.v1"
    source_urn: str | None      # e.g. "urn:dft-av:ingest:lane4"
    contract_version: str       # e.g. "1.0.0"
```

## Doctype → slug → APIM route table (13 POST endpoints)

| YAML | doctype_slug | apim_route | publishes_event |
|---|---|---|---|
| bronze-asde-incident-push-v1 | `asde_r155_inc` | `/asde-r155-inc` | true (legacy type preserved) |
| (new) bronze-asde-safety-case | `asde_safety_case` | `/asde-safety-case` | true |
| (new) bronze-ccav-asde-authorisation | `ccav_asde_authorisation` | `/ccav-asde-authorisation` | true |
| (new) bronze-ccav-enforcement | `ccav_enforcement` | `/ccav-enforcement` | true |
| bronze-ccav-kpi-v1 | `nuico_ccav_kpi` | `/nuico-ccav-kpi` | true |
| bronze-ccav-tx-log-v1 | `nuico_tx_log` | `/nuico-tx-log` | true |
| (new) bronze-nuico-quarterly-return | `nuico_quarterly_return` | `/nuico-quarterly-return` | true |
| bronze-dvsa-aps-perf-v1 | `dvsa_aps_perf` | `/dvsa-aps-perf` | true |
| bronze-dvsa-fleet-audit-v2 | `dvsa_fleet_audit` | `/dvsa-fleet-audit` | true |
| bronze-dvsa-permit-register-v1 | `dvsa_permit_register` | `/dvsa-permit-register` | true |
| bronze-ismr-occurrences-v1 | `si_ismr` | `/si-ismr` | true |
| (new) bronze-si-inv | `si_inv` | `/si-inv` | true |
| bronze-dvla-vehicle-registry-v1 | `dvla_v5c` | n/a (SQL pull) | false |
| bronze-dvla-type-approval-v1 | `dvla_type_approval` | n/a (SQL pull) | false |
| (new) bronze-operator-stack-telemetry | `operator_stack_telemetry` | n/a (Eventstream) | false |

New YAMLs marked "(new)" are Phase 2 work; this Phase 1 ships codegen + the 9 existing YAMLs annotated.

## Acceptance criteria

- [ ] All 9 bronze YAMLs carry `doctype_slug` + `publishes_event` (+ event block when true)
- [ ] `python -m tools.codegen.generate_pydantic` produces no `git diff` on second run
- [ ] `pytest -q` green; round-trip test passes for each YAML
- [ ] `schemas/json/<slug>.schema.json` validates the fixture under `jsonschema` Draft 2020-12
- [ ] `iac/apim-ops/<slug>.bicep` compiles under `bicep build` standalone

## Out-of-band local verification gate (blocks Phase 3 deploy)

1. `pip install -e .` from this repo into the platform venv
2. `cd ../dft-av-platform/apps/ingest_lane4_asde && func start`
3. POST `tests/fixtures/asde_r155_inc.json` against local; assert both legacy jsonschema and shadow Pydantic validators log success

## ADR linkage

- ADR-0001 — `doctype_slug` + `RouteMeta` as the cross-repo coordination surface
