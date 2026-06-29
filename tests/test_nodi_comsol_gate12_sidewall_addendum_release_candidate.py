from __future__ import annotations

import json
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate12_sidewall_addendum_release_candidate as gate12


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate12_payload_passes_release_candidate_thresholds() -> None:
    payload = gate12.build_payload(gate12.DEFAULT_COMSOL_ROOT)

    assert gate12.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate12.DISPOSITION
    assert payload["summary"]["nodi_gate11_commit"] == gate12.NODI_GATE11_COMMIT
    assert payload["summary"]["comsol_gate11_commit_expected"] == gate12.COMSOL_GATE11_COMMIT
    assert payload["summary"]["comsol_gate12_commit_expected"] == gate12.COMSOL_GATE12_COMMIT
    assert payload["summary"]["comsol_project_head_actual"] == gate12.COMSOL_GATE12_COMMIT
    assert payload["summary"]["comsol_receipt_rows"] == 11
    assert payload["summary"]["comsol_receipt_blocking_drift"] == 0
    assert payload["summary"]["comsol_receipt_missing_required"] == 0
    assert payload["summary"]["comsol_validation_rows"] == 17
    assert payload["summary"]["comsol_validation_failures"] == 0
    assert payload["summary"]["dirty_delta_open_count"] == 0
    assert payload["summary"]["release_field_rows"] == 29
    assert payload["summary"]["descriptor_dryrun_rows"] == 11
    assert payload["summary"]["descriptor_dryrun_failures"] == 0
    assert payload["summary"]["mutation_fixture_rows"] == 720
    assert payload["summary"]["unexpected_pass_count"] == 0
    assert payload["summary"]["forbidden_promotion_count"] == 0
    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert payload["summary"]["qch_state"] == "ABSENT"
    assert payload["summary"]["binding_state"] == "FAIL_CLOSED"


def test_comsol_gate11_receipt_and_dirty_delta_are_closed() -> None:
    payload = gate12.build_payload(gate12.DEFAULT_COMSOL_ROOT)

    assert all(
        row["receipt_status"]
        in {"MATCH", "OPTIONAL_NOT_IN_MANIFEST_READABLE"}
        for row in payload["comsol_receipt"]
    )
    assert not any(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in payload["comsol_receipt"])
    assert not any(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in payload["comsol_receipt"])
    assert len(payload["dirty_delta_closure"]) == 23
    assert all(row["open_after_gate12"] == "false" for row in payload["dirty_delta_closure"])
    assert any(
        row["closure_status"] == "CLOSED_BY_NODI_GATE11_RELEASE_E29501C"
        for row in payload["dirty_delta_closure"]
    )


def test_release_lockfile_is_review_only_no_auth_and_hash_bound() -> None:
    payload = gate12.build_payload(gate12.DEFAULT_COMSOL_ROOT)
    lockfile = payload["release_lockfile"]

    assert lockfile["release_candidate"] == gate12.RELEASE_NAME
    assert lockfile["nodi_gate11_commit"] == gate12.NODI_GATE11_COMMIT
    assert lockfile["comsol_gate11_commit"] == gate12.COMSOL_GATE11_COMMIT
    assert lockfile["comsol_gate12_commit"] == gate12.COMSOL_GATE12_COMMIT
    assert lockfile["comsol_descriptor_rows"] == 11
    assert lockfile["gate11_mutation_unexpected_pass"] == 0
    assert lockfile["gate2d_rows"] == 4
    assert lockfile["review_only"] is True
    assert lockfile["historical_freeze_rewrite"] is False
    assert lockfile["runtime_schema"] is False
    assert lockfile["production_contract"] is False
    assert lockfile["evidence_authorization"] is False
    assert lockfile["release_root_hash"] == payload["release_hash_tree"][-1]["sha256"]


def test_descriptor_dryrun_harness_accepts_only_review_quarantine() -> None:
    payload = gate12.build_payload(gate12.DEFAULT_COMSOL_ROOT)
    dryrun = payload["descriptor_dryrun_results"]
    ledger = payload["descriptor_review_ledger"]

    assert len(dryrun) == 11
    assert all(row["formula_hash_validation"] == "PASS" for row in dryrun)
    assert all(row["accepted_prs_eas_numeric_response"] == "false" for row in dryrun)
    assert all(row["edge_jrc_qch_authorized"] == "false" for row in dryrun)
    assert all(row["runtime_production_authorized"] == "false" for row in dryrun)
    assert sum(row["receipt_verdict"] == "REVIEW_ONLY_DESCRIPTOR_RECEIPT_CANDIDATE" for row in dryrun) == 10
    assert sum(row["receipt_verdict"] == "MICRO_REVIEW_ONLY_UNBOUND_NOT_NANO_BINDING" for row in dryrun) == 1
    assert sum(row["ledger_status"] == "REVIEW_ONLY_DESCRIPTOR_RECEIPT_CANDIDATE" for row in ledger) == 10
    assert sum(row["ledger_status"] == "MICRO_REVIEW_ONLY_UNBOUND_NOT_NANO_BINDING" for row in ledger) == 1
    assert all(row["can_enter_prs_eas_numeric_ingestion"] == "false" for row in ledger)
    assert all(row["can_enter_runtime"] == "false" for row in ledger)
    assert all(row["can_enter_production"] == "false" for row in ledger)


def test_prs_eas_contract_release_board_has_package_statuses_without_numeric_output() -> None:
    board = gate12.contract_release_board()

    assert len(board) == 19
    assert all(row["numeric_output_generated"] == "false" for row in board)
    assert all(row["authorization_opened"] == "false" for row in board)
    by_id = {row["board_id"]: row for row in board}
    assert by_id["G12E-PACKAGE-A"]["gate12_release_category"] == "implemented_contract_guard"
    assert by_id["G12E-PACKAGE-B"]["gate12_release_category"] == "requires_future_runtime_solver"
    assert by_id["G12E-PACKAGE-C"]["gate12_release_category"] == "blocked_by_no_auth"
    assert by_id["G12E-PACKAGE-D"]["gate11_coverage_status"] == "CONTRACT_GUARDS_COMPLETE_NO_NUMERIC_OUTPUT"
    assert any(
        row["required_guard"] == "closed geometry propagation rejection" for row in board
    )


def test_cross_project_handshake_closes_dirty_delta_with_no_semantic_conflict() -> None:
    payload = gate12.build_payload(gate12.DEFAULT_COMSOL_ROOT)
    rows = payload["handshake_matrix"]

    assert len(rows) == 31
    assert not any(row["semantic_conflict"] == "true" for row in rows)
    assert not any(row["dirty_delta_open"] == "true" for row in rows)
    assert not any(row["required_missing"] == "true" for row in rows)
    assert any(
        row["resolution"] == "CLOSED_BY_NODI_GATE11_E29501C_AND_GATE12_RECEIPT"
        for row in rows
    )
    assert sum(row["resolution"] == "COMSOL_EXTRA_RETAINED_REVIEW_ONLY_METADATA" for row in rows) == 5


def test_decision_dossier_has_three_unapproved_mutually_exclusive_choices() -> None:
    decisions = gate12.decision_dossier()

    assert {row["choice_id"] for row in decisions} == {
        "FREEZE_SIDEWALL_ADDENDUM_ONLY_NO_EVIDENCE_AUTH",
        "AUTHORIZE_DESCRIPTOR_RECEIPT_DRYRUN_ONLY_NEXT_GATE",
        "DEFER_SIDEWALL_ADDENDUM",
    }
    assert all(row["default_state"] == "AWAITING_USER_DECISION" for row in decisions)
    assert all(row["approved"] == "false" for row in decisions)
    assert all(row["mutually_exclusive"] == "true" for row in decisions)


def test_executive_brief_marks_trajectory_diagnostic_as_not_passability() -> None:
    brief = gate12.executive_brief_support()

    row = next(row for row in brief if row["topic"] == "trajectory_diagnostic_scope")
    assert "config-only" in row["verdict"]
    assert "not a closure or passability verdict" in row["verdict"]
    assert "PRS/EAS validators" in row["support"]


def test_mutation_expansion_and_no_auth_sweep_are_clean() -> None:
    payload = gate12.build_payload(gate12.DEFAULT_COMSOL_ROOT)

    assert len(payload["mutation_catalog"]) == 720
    assert len(payload["mutation_results"]) == 720
    assert payload["unexpected_pass_register"][0]["unexpected_pass_count"] == "0"
    assert payload["unexpected_pass_register"][0]["forbidden_promotion_count"] == "0"
    assert all(row["match_status"] == "MATCH_EXPECTED" for row in payload["mutation_results"])
    assert all(row["forbidden_promotion"] == "false" for row in payload["mutation_results"])
    assert all(row["sweep_status"] == "PASS_NO_AUTH" for row in payload["no_auth_sweep"])


def test_written_gate12_outputs_have_expected_shape_after_builder_run() -> None:
    report_json = OUT / "NODI_COMSOL_GATE12_SIDEWALL_REPORT_20260629.json"
    if not report_json.exists():
        return

    report = json.loads(report_json.read_text(encoding="utf-8"))
    manifest = read_csv_rows(OUT / "NODI_COMSOL_GATE12_SIDEWALL_MANIFEST_20260629.csv")
    dryrun = read_csv_rows(
        OUT / "NODI_COMSOL_GATE12_SIDEWALL_DESCRIPTOR_RECEIPT_DRYRUN_RESULTS_20260629.csv"
    )
    mutations = read_csv_rows(
        OUT / "NODI_COMSOL_GATE12_SIDEWALL_MUTATION_RESULTS_20260629.csv"
    )

    assert report["summary"]["descriptor_dryrun_rows"] == 11
    assert report["summary"]["mutation_result_rows"] == 720
    assert len(manifest) == 35
    assert len(dryrun) == 11
    assert len(mutations) == 720
    assert all(row["not_evidence"] == "true" for row in manifest)
    assert all(row["no_auth"] == "true" for row in manifest)
