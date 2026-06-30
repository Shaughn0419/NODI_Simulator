from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate16_sidewall_clean_reintake_receipt as gate16


def test_gate16_payload_passes_stale_fail_closed_receipt_thresholds() -> None:
    payload = gate16.build_payload(gate16.DEFAULT_COMSOL_ROOT)

    assert gate16.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate16.DISPOSITION
    assert payload["summary"]["comsol_gate15_receipt_rows"] == 16
    assert payload["summary"]["comsol_gate15_blocking_drift"] == 0
    assert payload["summary"]["comsol_gate15_missing_required"] == 0
    assert payload["summary"]["comsol_gate15_claim_firewall_drift"] == 0


def test_gate16_detects_comsol_gate15_is_not_current_clean_reintake() -> None:
    payload = gate16.build_payload(gate16.DEFAULT_COMSOL_ROOT)
    status = {row["check"]: row for row in payload["clean_reintake_status"]}

    assert status["nodi_head_consumed_by_comsol_gate15"]["gate16_result"] == "STALE_NODI_HEAD_FAIL_CLOSED"
    assert status["comsol_reported_nodi_dirty_count"]["gate16_result"] == "DIRTY_NODI_REINTAKE_FAIL_CLOSED"
    assert status["comsol_reintake_verdict"]["gate16_result"] == "OBSERVED_UNRELEASED_FAIL_CLOSED"
    assert status["stale_intake_closure"]["gate16_result"] == "OPEN_FAIL_CLOSED_OBSERVED_UNRELEASED"
    assert status["clean_current_reintake_accepted"]["actual_value"] == "false"
    assert payload["summary"]["clean_current_reintake_accepted"] is False


def test_gate16_receipt_hashes_and_forbidden_claim_firewall_match_manifest() -> None:
    payload = gate16.build_payload(gate16.DEFAULT_COMSOL_ROOT)

    assert {row["receipt_status"] for row in payload["comsol_gate15_receipt"]} == {"MATCH"}
    assert all(row["sha256_match"] == "true" for row in payload["comsol_gate15_receipt"])
    assert all(row["row_count_match"] == "true" for row in payload["comsol_gate15_receipt"])
    assert all(row["blocked_use_has_forbidden_tokens"] == "true" for row in payload["comsol_gate15_receipt"])


def test_gate16_current_release_request_is_no_run_no_auth() -> None:
    payload = gate16.build_payload(gate16.DEFAULT_COMSOL_ROOT)

    assert payload["current_release_request"]
    for row in payload["current_release_request"]:
        assert row["comsol_run_allowed"] == "false"
        assert row["mph_load_allowed"] == "false"
        assert row["runtime_or_production_allowed"] == "false"
        assert row["authorization_promotion_allowed"] == "false"
        assert row["current_nodi_head"] == payload["summary"]["nodi_current_head_at_gate16_build"]


def test_gate16_static_preflight_decision_keeps_packages_waiting_or_blocked() -> None:
    payload = gate16.build_payload(gate16.DEFAULT_COMSOL_ROOT)
    rows = {row["package"]: row for row in payload["static_preflight_decision"]}

    assert rows["Package A"]["gate16_decision"] == "WAITING_FOR_COMSOL_CLEAN_REINTAKE_AGAINST_CURRENT_NODI_HEAD"
    assert rows["Package B"]["gate16_decision"] == "WAITING_FOR_COMSOL_CLEAN_REINTAKE_AGAINST_CURRENT_NODI_HEAD"
    assert rows["Package C"]["gate16_decision"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"
    assert rows["Package D"]["gate16_decision"] == "WAITING_FOR_COMSOL_CLEAN_REINTAKE_AGAINST_CURRENT_NODI_HEAD"
    assert all(row["static_preflight_allowed_now"] == "false" for row in rows.values())
    assert all(row["runtime_allowed"] == "false" for row in rows.values())
    assert all(row["production_allowed"] == "false" for row in rows.values())


def test_gate16_no_auth_firewall_preserves_route_locks() -> None:
    payload = gate16.build_payload(gate16.DEFAULT_COMSOL_ROOT)
    firewall = payload["no_auth_firewall"][0]

    assert firewall["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED"
    assert firewall["authorization_promotion_count"] == "0"
    assert firewall["manifest_rows_missing_runtime_block"] == "0"
    assert firewall["gate2d_rows"] == "4"
    assert firewall["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert firewall["qch_state"] == "ABSENT"
    assert firewall["binding_state"] == "FAIL_CLOSED"


def test_gate16_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate16_sidewall_clean_reintake_receipt.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate16-sidewall-clean-reintake-receipt is required" in result.stderr
