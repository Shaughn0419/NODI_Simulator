from __future__ import annotations

import csv
import json
import subprocess
import sys

from nodi_simulator.nodi_comsol_next_artifacts import (
    AUTHORIZATION_GATE_PASS_STATUS,
    FUTURE_AUTHORIZATION_PHRASE_MATCH_BLOCKED_NO_EXECUTION,
)
from tools.audits import build_nodi_comsol_gate24_sidewall_package_c_authorization_ledger as gate24


def test_gate24_payload_passes_package_c_authorization_ledger_validation() -> None:
    payload = gate24.build_payload()

    assert gate24.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate24.DISPOSITION
    assert payload["summary"]["gate23_head_is_ancestor_of_current"] is True
    assert payload["summary"]["gate23_disposition"] == gate24.EXPECTED_GATE23_DISPOSITION
    assert payload["summary"]["gate23_no_auth"] is True
    assert payload["summary"]["gate23_review_only"] is True


def test_gate24_locks_gate23_sources_without_drift() -> None:
    payload = gate24.build_payload()

    assert payload["summary"]["gate23_source_lock_rows"] >= 10
    assert payload["summary"]["gate23_source_drift"] == 0
    assert payload["summary"]["gate23_missing_sources"] == 0
    assert {row["lock_status"] for row in payload["gate23_source_locks"]} == {"MATCH"}


def test_gate24_package_c_authorization_gate_stays_not_authorized() -> None:
    payload = gate24.build_payload()
    row = payload["authorization_gate"][0]

    assert row["record_status"] == AUTHORIZATION_GATE_PASS_STATUS
    assert row["authorization_gate_decision"] == "not_authorized_pending_explicit_future_request"
    assert row["package_c_physics_authorized"] == "false"
    assert row["proof_registry_update_authorized"] == "false"
    assert row["runtime_configuration_authorized"] == "false"
    assert row["nodi_runtime_recompute_authorized"] == "false"
    assert row["comsol_launch_authorized"] == "false"
    assert row["mph_load_authorized"] == "false"
    assert row["sidewall_prs_eas_numeric_output_authorized"] == "false"


def test_gate24_exact_future_phrase_is_recorded_but_not_execution_authorization() -> None:
    payload = gate24.build_payload()
    exact = next(row for row in payload["phrase_evaluations"] if row["phrase_eval_id"] == "G24C-PHRASE-001")
    generic = next(row for row in payload["phrase_evaluations"] if row["phrase_eval_id"] == "G24C-PHRASE-002")

    assert exact["phrase_exact_match"] == "true"
    assert exact["evaluation_status"] == FUTURE_AUTHORIZATION_PHRASE_MATCH_BLOCKED_NO_EXECUTION
    assert exact["authorized_now"] == "false"
    assert exact["package_c_physics_authorized"] == "false"
    assert exact["proof_registry_update_authorized"] == "false"
    assert exact["nodi_runtime_recompute_authorized"] == "false"
    assert exact["comsol_launch_authorized"] == "false"
    assert exact["mph_load_authorized"] == "false"
    assert generic["phrase_exact_match"] == "false"
    assert generic["authorized_now"] == "false"


def test_gate24_no_auth_firewall_remains_closed() -> None:
    payload = gate24.build_payload()
    firewall = payload["no_auth_firewall"][0]

    assert firewall["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED"
    assert firewall["package_c_physics_authorized"] == "false"
    assert firewall["proof_registry_update_authorized"] == "false"
    assert firewall["runtime_configuration_authorized"] == "false"
    assert firewall["production_ingestion_authorized"] == "false"
    assert firewall["comsol_launch_authorized"] == "false"
    assert firewall["mph_load_authorized"] == "false"
    assert firewall["nodi_runtime_recompute_authorized"] == "false"
    assert firewall["qch_weighting_authorized"] == "false"
    assert firewall["jrc_authorized"] == "false"
    assert firewall["route_score_authorized"] == "false"
    assert firewall["winner_authorized"] == "false"
    assert firewall["yield_authorized"] == "false"
    assert firewall["detection_probability_authorized"] == "false"
    assert firewall["fabrication_release_authorized"] == "false"


def test_gate24_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate24-package-c-authorization-ledger is required" in result.stderr


def test_gate24_cli_confirmed_write_outputs_remain_no_auth() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py",
            "--confirm-gate24-package-c-authorization-ledger",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert gate24.DISPOSITION in result.stdout

    output_dir = gate24.OUTPUT_DIR
    status_path = output_dir / "NODI_COMSOL_GATE24_SIDEWALL_STATUS_20260630.json"
    manifest_path = output_dir / "NODI_COMSOL_GATE24_SIDEWALL_MANIFEST_20260630.csv"
    report_path = output_dir / "NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_REPORT_20260630.md"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))

    assert status["disposition"] == gate24.DISPOSITION
    assert status["review_only"] is True
    assert status["no_auth"] is True
    assert status["summary"]["phrase_authorized_now_rows"] == 0
    assert status["summary"]["package_c_physics_authorized_rows"] == 0
    assert status["summary"]["proof_registry_update_authorized_rows"] == 0
    assert status["summary"]["runtime_allowed_rows"] == 0
    assert status["summary"]["comsol_launch_authorized_rows"] == 0
    assert status["summary"]["mph_load_authorized_rows"] == 0
    assert len(manifest) >= 8
    assert all((gate24.PROJECT_ROOT / row["path"]).exists() for row in manifest)
    assert all(row["policy_impact"] == "none_no_auth" for row in manifest)
    assert report_path.exists()
