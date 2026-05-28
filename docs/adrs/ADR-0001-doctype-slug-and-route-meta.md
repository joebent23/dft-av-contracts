# ADR-0001 — `doctype_slug` and `RouteMeta` as the cross-repo coordination surface

Date: 2026-05-28  
Status: Accepted  
Deciders: cockpit/platform alignment workstream

## Context

The live ADLS landing zone `stdftavsourcesdevswc/bronze` already exposes 12 `by-doctype/<snake_case>/` folders, while contract YAMLs in this repo use kebab-case filenames. Three downstream consumers (`dft-av-platform` Functions, `dft-av-platform` APIM Bicep, `dft-av-cockpit` API) all need the same answers for "where does this doctype write to in ADLS?", "which APIM route is canonical?", and "does it emit a CloudEvent and of what type?". Today these answers are duplicated and drift.

Lane-4 today writes to `<container>/year=YYYY/month=MM/day=DD/<ingest_id>.json`; Fabric shortcuts require a flat single-folder target.

## Decision

1. Each bronze YAML gains a top-level `doctype_slug: <snake_case>` field that matches the live ADLS folder name (e.g. `asde_r155_inc`).
2. Each bronze YAML gains `publishes_event: bool` and, when true, an `event:` block with `type` (CloudEvents 1.0) and `source_urn`.
3. Codegen emits a frozen `RouteMeta` dataclass instance per doctype next to the Pydantic model, exposing `apim_route`, `adls_path`, `publishes_event`, `event_type`, `source_urn`, `contract_version`.
4. All write paths in Functions are computed from `RouteMeta.adls_path` (= `f"by-doctype/{doctype_slug}/"`) — never hard-coded.
5. Codegen also emits a per-doctype JSON Schema file and an APIM Bicep operation fragment so APIM op shape stays lockstep with the Pydantic model.
6. YAML filenames stay kebab-case; only the new `doctype_slug` field carries the snake_case form. This avoids a noisy rename in git history while accepting the cosmetic mismatch as the price of stability.

## Consequences

Positive:
- Adding a doctype = single PR in this repo; platform + cockpit consume on bump.
- ADLS path is a single source of truth — Fabric shortcuts cannot drift.
- APIM op + Pydantic model + JSON Schema cannot disagree because all derive from one YAML.

Negative:
- YAML filename vs `doctype_slug` is a cosmetic mismatch that humans must keep in sync (lint check added).
- Codegen now produces three artefact kinds instead of one; second-run idempotency must be enforced in CI.

## Alternatives considered

- **Rename YAML filenames to snake_case** — rejected: noisy git history, breaks vendor copies in platform repo.
- **Hard-code APIM route shape in `dft-av-platform`** — rejected: re-introduces drift the moment contracts move.
- **Generate `RouteMeta` from a separate routing table** — rejected: separating routing from schema is the drift we are trying to eliminate.

## References

- Spec: `docs/specs/2026-05-multi-doctype-ingest.md`
- Memory: `/memories/session/phase0-inventory.md` decisions 1, 4, 5
