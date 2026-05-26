"""Tests for contract-diff.py.

Run with: ``pip install pyyaml pytest && pytest tools/test_contract_diff.py -v``
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "contract-diff.py"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def write_contract(root: Path, relpath: str, body: str) -> None:
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def run_diff(base: Path, head: Path, *extra: str) -> tuple[int, dict, str]:
    cmd = [sys.executable, str(SCRIPT), "--base", str(base), "--head", str(head), "--json", *extra]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    try:
        payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    return proc.returncode, payload, proc.stderr


def make_pair(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "base"
    head = tmp_path / "head"
    (base / "schemas").mkdir(parents=True)
    (head / "schemas").mkdir(parents=True)
    return base, head


BRONZE_VRM = """
metadata:
  name: bronze-dvla-vehicle-registry
  version: 1.0.0
schema:
  - name: vehicle_registry
    columns:
      - name: vrm
        type: string
        primaryKey: true
        nullable: false
      - name: make
        type: string
        nullable: true
      - name: _ingested_at_utc
        type: timestamp
        nullable: false
      - name: _source_lane
        type: string
        nullable: false
      - name: _correlation_id
        type: string
        nullable: false
      - name: _raw_blob_path
        type: string
        nullable: false
      - name: _contract_version
        type: string
        nullable: false
"""


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_no_changes(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    write_contract(base, "schemas/bronze/x.yaml", BRONZE_VRM)
    write_contract(head, "schemas/bronze/x.yaml", BRONZE_VRM)
    rc, payload, _ = run_diff(base, head)
    assert rc == 0
    assert payload["summary"]["breaking"] == 0
    assert payload["summary"]["additive"] == 0
    assert payload["summary"]["patch"] == 0
    assert payload["required_bump"] == "none"


def test_add_contract_is_additive(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    write_contract(head, "schemas/bronze/x.yaml", BRONZE_VRM)
    rc, payload, _ = run_diff(base, head)
    assert rc == 0
    assert payload["summary"]["additive"] == 1
    assert payload["summary"]["breaking"] == 0
    assert payload["required_bump"] == "minor"
    assert any(c["kind"] == "additive" and "new contract" in c["what"] for c in payload["changes"])


def test_remove_contract_is_breaking(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    write_contract(base, "schemas/bronze/x.yaml", BRONZE_VRM)
    rc, payload, _ = run_diff(base, head, "--fail-on-breaking")
    assert rc == 1
    assert payload["summary"]["breaking"] == 1
    assert payload["required_bump"] == "major"
    assert any("contract removed" in c["what"] for c in payload["changes"])


def test_add_optional_column_is_additive(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    write_contract(base, "schemas/bronze/x.yaml", BRONZE_VRM)
    head_doc = BRONZE_VRM.rstrip() + "\n      - name: recall_flag\n        type: string\n        nullable: true\n"
    write_contract(head, "schemas/bronze/x.yaml", head_doc)
    rc, payload, _ = run_diff(base, head)
    assert rc == 0
    assert payload["summary"]["additive"] >= 1
    assert payload["summary"]["breaking"] == 0
    assert any("optional column" in c["what"] for c in payload["changes"])


def test_add_required_column_is_breaking(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    write_contract(base, "schemas/bronze/x.yaml", BRONZE_VRM)
    head_doc = BRONZE_VRM.rstrip() + "\n      - name: owner_id\n        type: string\n        required: true\n        nullable: false\n"
    write_contract(head, "schemas/bronze/x.yaml", head_doc)
    rc, payload, _ = run_diff(base, head, "--fail-on-breaking")
    assert rc == 1
    assert payload["summary"]["breaking"] >= 1
    assert any("required column" in c["what"] for c in payload["changes"])


def test_change_column_type_is_breaking(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    write_contract(base, "schemas/bronze/x.yaml", BRONZE_VRM)
    head_doc = BRONZE_VRM.replace("- name: vrm\n        type: string", "- name: vrm\n        type: int")
    write_contract(head, "schemas/bronze/x.yaml", head_doc)
    rc, payload, _ = run_diff(base, head, "--fail-on-breaking")
    assert rc == 1
    assert any("type" in c["what"] and c["kind"] == "breaking" for c in payload["changes"])


def test_nullable_tightening_is_breaking(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    write_contract(base, "schemas/bronze/x.yaml", BRONZE_VRM)
    # `make` was nullable: true; tighten to false
    head_doc = BRONZE_VRM.replace("- name: make\n        type: string\n        nullable: true",
                                  "- name: make\n        type: string\n        nullable: false")
    write_contract(head, "schemas/bronze/x.yaml", head_doc)
    rc, payload, _ = run_diff(base, head, "--fail-on-breaking")
    assert rc == 1
    assert any("nullable tightened" in c["what"] for c in payload["changes"])


def test_remove_bronze_audit_column_is_breaking(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    write_contract(base, "schemas/bronze/x.yaml", BRONZE_VRM)
    # Drop `_ingested_at_utc`
    head_doc = BRONZE_VRM.replace(
        "      - name: _ingested_at_utc\n        type: timestamp\n        nullable: false\n",
        ""
    )
    write_contract(head, "schemas/bronze/x.yaml", head_doc)
    rc, payload, _ = run_diff(base, head, "--fail-on-breaking")
    assert rc == 1
    assert any("bronze audit" in c["what"] for c in payload["changes"])


def test_numeric_widening_is_additive(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    body = """
    metadata:
      name: silver-x
      version: 1.0.0
    schema:
      - name: t
        columns:
          - name: count
            type: int
            nullable: true
    """
    widened = body.replace("type: int", "type: long")
    write_contract(base, "schemas/silver/x.yaml", body)
    write_contract(head, "schemas/silver/x.yaml", widened)
    rc, payload, _ = run_diff(base, head)
    assert rc == 0
    assert payload["summary"]["breaking"] == 0
    assert any("widened" in c["what"] for c in payload["changes"])


def test_loosen_nullable_is_additive(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    body = """
    metadata:
      name: silver-x
      version: 1.0.0
    schema:
      - name: t
        columns:
          - name: note
            type: string
            nullable: false
    """
    loosened = body.replace("nullable: false", "nullable: true")
    write_contract(base, "schemas/silver/x.yaml", body)
    write_contract(head, "schemas/silver/x.yaml", loosened)
    rc, payload, _ = run_diff(base, head)
    assert rc == 0
    assert any(c["kind"] == "additive" and "loosened" in c["what"] for c in payload["changes"])


def test_primary_key_change_is_breaking(tmp_path: Path) -> None:
    base, head = make_pair(tmp_path)
    body = """
    metadata:
      name: silver-x
      version: 1.0.0
    schema:
      - name: t
        primaryKey: [a]
        columns:
          - name: a
            type: string
          - name: b
            type: string
    """
    changed = body.replace("primaryKey: [a]", "primaryKey: [b]")
    write_contract(base, "schemas/silver/x.yaml", body)
    write_contract(head, "schemas/silver/x.yaml", changed)
    rc, payload, _ = run_diff(base, head, "--fail-on-breaking")
    assert rc == 1
    assert any("primary key" in c["what"] for c in payload["changes"])
