# Contributing to `dft-av-contracts`

> ⚠️ **This repository is PUBLIC.** Do not commit real workspace IDs, VINs, UPNs, ABFSS URIs, Key Vault names or any other production identifier. Use the documented placeholders in every `examples:` block. A hygiene scan runs on every PR.

## PR workflow

1. **Branch** off `main`: `git checkout -b feat/<contract>-<change>`.
2. **Edit** the relevant file under `schemas/source/` or `schemas/bronze/`.
3. **Bump `metadata.version`** per semver (see table below). Forgetting the bump on a breaking change is the most common CI failure.
4. **Open a PR** targeting `main`. CI runs:
   - `tools/contract-diff.py` — breaking-change linter, gated against the PR target branch (typically `main`).
   - Manifest validation — `schemas/MANIFEST.yaml` is regenerated and must match (it is regenerated authoritatively at release time).
   - Hygiene scan — fails the build on detected real-world identifiers (GUIDs, `*.dfs.core.windows.net`, real `.gov.uk` mailboxes without the `.example.` infix, the `NVR0725*` hero-VIN family, etc.).
5. A **CODEOWNERS reviewer** must approve before merge. Squash-merge is preferred to keep release diffs clean.

## Semver discipline

| Change                                                                | Bump  |
|-----------------------------------------------------------------------|-------|
| Add an **optional** column / vocab entry / quality rule               | MINOR |
| Add a **required** column, tighten a type, remove or rename a field   | MAJOR |
| Fix a description, comment or non-normative example                   | PATCH |

The breaking-change linter classifies your diff and fails the build if the version bump is smaller than the diff requires. A MAJOR replacement should keep the previous file in place and set `customProperties["dft-av.supersedes"]` to its relative path.

## Public-repo hygiene checklist

Before pushing, verify your diff contains **none** of:

- GUIDs in workspace / capacity / tenant context — use `<workspace-id>`, `<capacity-id>`.
- Real VINs — use `EXAMPLEVIN0000001` (17-char placeholder) or another synthetic value documented in `schemas/bronze/README.md`.
- Real operator UPNs / mailboxes — use `data.governance@<agency>.example.gov.uk`.
- ABFSS / `*.dfs.core.windows.net` URIs — use `abfss://<container>@<account>.dfs.core.windows.net/<path>` with all parts angle-bracketed.
- Key Vault references (`kv-*-dev`, `@Microsoft.KeyVault(...)`) — these belong in the platform repo, never in a contract.
- Connection strings, SAS tokens, OAuth client secrets — never, in any form.

## Reporting a problem with a published contract

Open an issue with the `contract:<name>` label and link to the affected `vX.Y.Z` release tag.
