from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate18_sidewall_comsol_gate16_receipt as gate18


def test_gate18_payload_passes_comsol_gate16_receipt_thresholds() -> None:
    payload = gate18.build_payload(gate18.DEFAULT_COMSOL_ROOT)

    assert gate18.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate18.DISPOSITION
    assert payload["summary"]["comsol_head_actual"] == gate18.EXPECTED_COMSOL_GATE16_HEAD
    assert payload["summary"]["comsol_gate16_receipt_rows"] == 9
    assert payload["summary"]["comsol_gate16_blocking_drift"] == 0
    assert payload["summary"]["comsol_gate16_missing_required"] == 0
    assert payload["summary"]["comsol_gate16_claim_firewall_drift"] == 0


def test_gate18_accepts_clean_anchor_reintake_and_closed_gate15_stale_state() -> None:
    payload = gate18.build_payload(gate18.DEFAULT_COMSOL_ROOT)
    rows = {row["field"]: row for row in payload["clean_reintake_acceptance"]}

    assert {row["acceptance_status"] for row in rows.values()} == {"MATCH"}
    assert rows["comsol_gate16_status"]["actual_value"] == gate18.EXPECTED_COMSOL_GATE16_STATUS
    assert rows["anchor_semantic_digest_sha256"]["actual_value"] == gate18.EXPECTED_ANCHOR_DIGEST
    assert rows["clean_current_nodi_consumed"]["actual_value"] == "True"
    assert rows["stale_gate15_closure_status"]["actual_value"] == "CLOSED_SUPERSEDED_BY_GATE16_CURRENT_NODI_CLEAN_REINTAKE"


def test_gate18_static_preflight_board_allows_only_package_a_b_d_precheck() -> None:
    payload = gate18.build_payload(gate18.DEFAULT_COMSOL_ROOT)
    board = {row["package"]: row for row in payload["static_preflight_board"]}

    assert board["Package A"]["nodi_gate18_status"] == "STATIC_PREFLIGHT_PRECHECK_ALLOWED_NO_AUTH"
    assert board["Package B"]["nodi_gate18_status"] == "STATIC_PREFLIGHT_PRECHECK_ALLOWED_NO_AUTH"
    assert board["Package D"]["nodi_gate18_status"] == "STATIC_PREFLIGHT_PRECHECK_ALLOWED_NO_AUTH"
    assert board["Package C"]["nodi_gate18_status"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"
    for row in board.values():
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"
        assert row["validated_physics_claim"] == "false"
        assert row["qch_or_jrc_allowed"] == "false"


def test_gate18_no_auth_firewall_preserves_locks() -> None:
    payload = gate18.build_payload(gate18.DEFAULT_COMSOL_ROOT)
    firewall = payload["no_auth_firewall"][0]

    assert firewall["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED"
    assert firewall["positive_authorization_count"] == "0"
    assert firewall["runtime_configuration_authorized"] == "false"
    assert firewall["production_ingestion_authorized"] == "false"
    assert firewall["qch_weighting_authorized"] == "false"
    assert firewall["jrc_authorized"] == "false"
    assert firewall["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert firewall["qch_state"] == "ABSENT"
    assert firewall["binding_state"] == "FAIL_CLOSED"


def test_gate18_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate18_sidewall_comsol_gate16_receipt.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate18-comsol-gate16-receipt is required" in result.stderr
