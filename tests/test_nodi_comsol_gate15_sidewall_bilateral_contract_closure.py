from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate15_sidewall_bilateral_contract_closure as gate15


def test_gate15_payload_passes_bilateral_contract_closure_thresholds() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)

    assert gate15.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate15.DISPOSITION
    assert payload["summary"]["comsol_gate14_receipt_rows"] == 16
    assert payload["summary"]["comsol_gate14_blocking_drift"] == 0
    assert payload["summary"]["comsol_gate14_missing_required"] == 0


def test_gate15_keeps_comsol_gate14_partial_as_clean_reintake_requirement() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)
    partial = payload["comsol_partial_reason"][0]

    assert partial["treat_as_full_pass_now"] == "false"
    assert partial["nodi_verdict"] == "RACE_TIME_DELTA_REQUIRES_COMSOL_GATE15_CLEAN_REINTAKE"
    assert payload["summary"]["comsol_gate14_partial_is_time_delta"] is True


def test_gate15_no_auth_firewall_preserves_route_locks() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)
    firewall = payload["no_auth_firewall"][0]

    assert firewall["positive_authorization_count"] == "0"
    assert firewall["positive_runtime_or_production_count"] == "0"
    assert firewall["gate2d_rows"] == "4"
    assert firewall["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert firewall["qch_state"] == "ABSENT"
    assert firewall["binding_state"] == "FAIL_CLOSED"


def test_gate15_schema_cross_signoff_has_no_semantic_conflicts() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)
    statuses = {row["status"] for row in payload["schema_cross_signoff"]}

    assert payload["summary"]["schema_cross_signoff_rows"] == 33
    assert payload["summary"]["schema_semantic_conflicts"] == 0
    assert "SEMANTIC_CONFLICT_FAIL_CLOSED" not in statuses
    assert {"BILATERAL_EXACT_MATCH", "FUTURE_COMSOL_EXPORT_REQUIRED", "BLOCKED_AS_EXPECTED"} & statuses


def test_gate15_static_preflight_board_keeps_package_c_blocked() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)
    board = {
        row["package"]: row
        for row in payload["static_preflight_readiness_board"]
    }

    assert board["Package A"]["readiness"] == "READY_FOR_STATIC_PREFLIGHT_AFTER_COMSOL_CLEAN_REINTAKE"
    assert board["Package B"]["readiness"] == "READY_FOR_STATIC_PREFLIGHT_AFTER_COMSOL_CLEAN_REINTAKE"
    assert board["Package C"]["readiness"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"
    assert board["Package D"]["readiness"] == "READY_FOR_CONTRACT_PREFLIGHT_AFTER_COMSOL_CLEAN_REINTAKE"
    for row in board.values():
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"
        assert row["validated_physics_claim"] == "false"


def test_gate15_comsol_gate15_instruction_package_is_no_run_no_auth() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)
    actions = {row["action"]: row for row in payload["comsol_gate15_instruction_package"]}

    assert {
        "read_nodi_current_release",
        "close_old_dirty_intake",
        "rebuild_intake_receipt",
        "update_stale_intake_closure",
        "preserve_no_auth_locks",
        "emit_no_run_preflight_package",
        "avoid_unrelated_dirty",
    } <= actions.keys()
    for row in actions.values():
        assert row["comsol_run_allowed"] == "false"
        assert row["mph_load_allowed"] == "false"
        assert row["authorization_promotion_allowed"] == "false"


def test_gate15_mutation_rows_are_fail_closed_and_above_threshold() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)

    assert payload["summary"]["mutation_rows"] >= 100000
    assert payload["summary"]["mutation_unexpected_pass"] == 0
    assert payload["summary"]["mutation_forbidden_promotion"] == 0
    assert {row["unexpected_pass"] for row in payload["mutation_results"]} == {"false"}
    assert {row["forbidden_promotion"] for row in payload["mutation_results"]} == {"false"}


def test_gate15_dirty_path_classifier_rejects_unrelated_dirty() -> None:
    generated, _, generated_action = gate15.classify_dirty_path(
        "reports/joint_interface_20260630/NODI_COMSOL_GATE15_SIDEWALL_STATUS_20260630.json"
    )
    unknown, _, unknown_action = gate15.classify_dirty_path("unrelated/user_notes.txt")

    assert generated == "LEGIT_GATE15_GENERATED_OUTPUT_PENDING_COMMIT"
    assert generated_action == "stage_with_gate15_commit_after_tests"
    assert unknown == "UNKNOWN_USER_CHANGE_BLOCKER"
    assert unknown_action == "do_not_stage"


def test_gate15_git_status_path_parser_handles_porcelain_variants() -> None:
    assert gate15.parse_git_status_path(" M tests/example.py") == "tests/example.py"
    assert gate15.parse_git_status_path("M  tests/example.py") == "tests/example.py"
    assert gate15.parse_git_status_path("?? reports/example.csv") == "reports/example.csv"
    assert gate15.parse_git_status_path("R  old.py -> new.py") == "new.py"


def test_gate15_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate15-sidewall-bilateral-closure is required" in result.stderr
