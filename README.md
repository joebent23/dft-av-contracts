# dft-av-contracts

Single source of truth for **Department for Transport — Autonomous Vehicles (DfT-AV)** data contracts.

This repository is **schema-only**: it holds the ODCS-flavoured YAML contracts that describe source feeds and Bronze landing tables in the DfT-AV Fabric medallion. **No business logic, no live data, no environment-specific identifiers** ever land here.

## Repository layout

```
schemas/
├── source/           # Source-feed contracts (CSV / API / push payloads before ingestion)
├── bronze/           # Bronze Delta-table contracts (post-ingestion, with audit columns)
│   └── README.md     # ADR-002 + STORY-D-001 audit-column invariant
└── MANIFEST.yaml     # Machine-readable index (path, name, version, kind, supersedes, sha256)

python/
└── dft_av_contracts/ # Generated Pydantic model package (populated at release time)

.github/workflows/    # Release pipeline (codegen + zip + GitHub Release)
tools/                # Breaking-change linter + manifest helpers
```

## Consumer install

### Download the schema bundle from a release

```bash
gh release download v0.1.0 \
    -R joebent23/dft-av-contracts \
    -p contracts-v0.1.0.zip
unzip contracts-v0.1.0.zip -d .contracts/
```

### Install the generated Python models from the release artefact

The bundle published on each GitHub Release ships with `pyproject.toml` and the generated `dft_av_contracts/` package, so it is `pip install`-able directly:

```bash
gh release download v0.1.0 -R joebent23/dft-av-contracts -p contracts-v0.1.0.zip
unzip contracts-v0.1.0.zip -d .contracts
pip install ./.contracts/contracts-v0.1.0
```

```python
from dft_av_contracts import BronzeBronzeDvsaFleetAuditRow  # generated at release time
```

> PyPI publishing is intentionally deferred to a later release that ships with proper `PYPI_API_TOKEN` secret management.

## Versioning policy (semver)

| Change                                                                 | Bump                                        |
|------------------------------------------------------------------------|---------------------------------------------|
| Add an **optional** column, vocabulary entry or quality rule           | **MINOR** (e.g. `1.2.0 → 1.3.0`)            |
| Add a **required** column, tighten a type, remove or rename a field   | **MAJOR** (e.g. `1.3.0 → 2.0.0`)            |
| Fix a description, comment or non-normative example                    | **PATCH** (e.g. `1.3.0 → 1.3.1`)            |

Every PR runs the breaking-change linter (`tools/contract-diff.py`) against the PR target branch (typically `main`). A MAJOR-level diff requires the PR to bump the contract's `metadata.version` accordingly, otherwise CI fails.

When a contract is replaced by a new major version, the old file stays in `schemas/` and the new file sets `customProperties["dft-av.supersedes"]` to the old file's relative path (see `bronze/bronze-dvsa-fleet-audit-v2.yaml`).

## How to propose a change

1. Fork or branch, edit the YAML in `schemas/`.
2. Bump `metadata.version` per the table above.
3. Open a PR. CI will run the breaking-change linter and validate `MANIFEST.yaml`.
4. A `CODEOWNERS` reviewer must approve before merge.
5. Cutting a release: tag `vX.Y.Z` → the release workflow regenerates `MANIFEST.yaml`, generates Pydantic models, builds a wheel + `contracts-vX.Y.Z.zip`, and publishes a GitHub Release.

## Authoritative references

- **ADR-X-001** (in `joebent23/dft-av-platform`) — authoritative decision record for the contracts-distribution mechanism this repo implements.
- **ADR-002 + STORY-D-001** (in the platform repo) — defines the five mandatory Bronze audit columns; mirrored in `schemas/bronze/README.md`.
- **ODCS v3** — Open Data Contract Standard; the YAML files target `apiVersion: opendatacontractstandard.org/v3`.

## License

[MIT](./LICENSE). Schemas are non-sensitive metadata only.

## Security & hygiene

This repo is **public**. Contributors MUST NOT commit:

- real Microsoft Fabric workspace or capacity IDs (GUIDs),
- real VINs, registration marks, operator licence numbers, or driver UPNs,
- real ABFSS / `*.dfs.core.windows.net` URIs,
- real Key Vault names or secret references.

Use the documented placeholder values (`<workspace-id>`, `EXAMPLEVIN0000001`, `data.governance@<agency>.example.gov.uk`) in any `examples:` block. CI runs a hygiene scan on every PR.
