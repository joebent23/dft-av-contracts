# Bronze table contracts

> **Status:** draft · **Owner:** internal data lineage / Data Governance WG · **Binding:** ADR-002, ADR-010, CD-14

ODCS-flavoured YAML contracts for the Delta tables that land in `lh_av_bronze` inside `AV-Medallion-{env}`.

## What lives here vs `../`

`../contracts/` holds **source-schema** contracts that describe a feed *before* ingestion (for example `../dvsa-fleet-audit-v1.yaml` describes the CSV on the source side). Contracts in **this** folder describe the **Bronze Delta tables** that internal data lineage materialises *after* ingestion — they add the platform-managed audit columns, the internal ingest lane, and the cross-table hero invariants downstream relies on. The Bronze companion supersedes the source contract for Bronze reads via `customProperties.dft-av.supersedes`.

## Mandatory Bronze audit columns (per ADR-002 + an internal story)

 an internal story defines the **five enforced mandatory** audit columns. The schema-enforcement helper in `tools/bronze/schema_enforce.py` fails any Bronze write that omits these or has the wrong primitive type:

| # | Column | Type | Nullable | Purpose |
|---|--------|------|----------|---------|
| 1 | `_ingested_at_utc` | timestamp | no | When the row landed in Bronze (UTC). |
| 2 | `_source_lane` | string | no | internal ingest lane (`shortcut`, `mirroring`, `pipeline`, `push`, `portal`, `eventstream`, `openmirroring`). |
| 3 | `_correlation_id` | string | no | UUID linking the row back to the ingest batch / APIM call / queue message. |
| 4 | `_raw_blob_path` | string | yes | Full ABFSS / S3 / queue URI of the raw payload. Supersedes `_source_file`. |
| 5 | `_contract_version` | string | no | Semver of this contract under which the row was written (matches `metadata.version`). |

The contracts additionally declare two **legacy ADR-002 audit columns** retained for backward compatibility and internal data lineage DQ Gate consumption — they are **not** enforced by the helper but internal data lineage notebooks SHOULD populate them:

- `_source_file` (string, nullable) — superseded by `_raw_blob_path`; notebooks set both to the same value when the source is file-shaped.
- `_dq_status` (string, not null, vocab `{PASS, QUARANTINE, FAIL}`) — DQ Gate verdict (set by internal data lineage ; Bronze writes default to `"PASS"`).

`../contract-spec.md` §5 still documents an older four-column quartet and is scheduled for rebase .

## How internal data lineage consumes these

internal data lineage reads `schema.location` + `schema.columns` and emits `CREATE TABLE` against `lh_av_bronze`. Pipeline / Portal / Push / Eventstream lanes populate the audit columns at write time; Mirroring and Open Mirroring lanes are conformed post-write by `nb_conform_bronze_*` notebooks.

## How internal data lineage consumes these

The `quality.rules` block feeds the DQ Gate rule generator. Any rule with `blocksRelease: true` and `severity: critical` halts Bronze → Silver promotion when its threshold is breached. The hero-invariant rules (internal-recall, hero invoice, ISMR hero IDs, SI-INV) are the internal scenarios cross-regulator gates.

## Value-space alignment

Every closed vocabulary, regex, range and hero identifier matches `../synth-rules.md`. Any divergence is a bug — raise a finding against the contract or the synthesis notebook, not both.
