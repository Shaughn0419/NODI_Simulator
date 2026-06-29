from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate8a_to_gate8k_joint_freeze_rehearsal as gate8


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate8_payload_thresholds_and_no_auth_summary() -> None:
    payload = gate8.build_payload(gate8.DEFAULT_COMSOL_ROOT)

    assert gate8.validate_payload(payload) == []
    assert payload["summary"]["comsol_manifest_rows"] == 42
    assert payload["summary"]["comsol_validation_rows"] == 16
    assert payload["summary"]["comsol_nodi_receipt_rows"] == 29
    assert payload["summary"]["comsol_dictionary_rows"] == 366
    assert payload["summary"]["comsol_edge_spec_rows"] == 12
    assert payload["summary"]["comsol_qch_spec_rows"] == 12
    assert payload["summary"]["comsol_binding_spec_rows"] == 12
    assert payload["summary"]["comsol_dependency_nodes"] == 320
    assert payload["summary"]["comsol_dependency_edges"] == 420
    assert payload["summary"]["comsol_fixture_rows"] == 5200
    assert payload["summary"]["gate2d_rows"] == 4


def test_gate8a_receipt_has_no_blocking_drift_or_missing_artifacts() -> None:
    receipt = read_csv_rows(OUT / "NODI_COMSOL_GATE8A_COMSOL_GATE7_RECEIPT_REGISTER_20260629.csv")
    counts = Counter(row["receipt_status"] for row in receipt)

    assert len(receipt) == 42
    assert counts["BLOCKING_DATA_DRIFT"] == 0
    assert counts["MISSING_REQUIRED_ARTIFACT"] == 0
    assert all(row["auth_impact"] == "none" for row in receipt)
    assert all(row["evidence_bearing"] == "false" for row in receipt)


def test_gate8b_joint_freeze_reconciliation_keeps_optional_guard_non_policy() -> None:
    matrix = read_csv_rows(OUT / "NODI_COMSOL_GATE8B_JOINT_FREEZE_ARTIFACT_RECONCILIATION_20260629.csv")
    lockfile = json.loads((OUT / "NODI_COMSOL_GATE8B_JOINT_FREEZE_CANDIDATE_LOCKFILE_20260629.json").read_text(encoding="utf-8"))
    duplicate_rows = [row for row in matrix if row["canonical_field"] == "nodi_view_binding_status"]

    assert len(matrix) == 365
    assert lockfile["lock_name"] == "JOINT_RC5_1_FREEZE_CANDIDATE_REVIEW_ONLY_NO_AUTH"
    assert lockfile["review_only"] is True
    assert lockfile["evidence_acceptance"] is False
    assert lockfile["runtime_schema"] is False
    assert lockfile["authorization"] == "closed"
    assert duplicate_rows
    assert duplicate_rows[0]["lockstep_status"] == "LOCKSTEP_MATCH_WITH_PRODUCER_DUPLICATE_OPTIONAL_GUARD_NON_POLICY"
    assert duplicate_rows[0]["freeze_impact"] == "non-policy optional guard"


def test_gate8c_comsol_fixture_replay_zero_unexpected_pass() -> None:
    replay = read_csv_rows(OUT / "NODI_COMSOL_GATE8C_COMSOL_FIXTURE_REPLAY_VERDICT_MATRIX_20260629.csv")
    summary = read_csv_rows(OUT / "NODI_COMSOL_GATE8C_REPLAY_SUMMARY_20260629.csv")
    families = Counter(row["fixture_family"] for row in replay)

    assert len(replay) == 5200
    assert families["EDGE_fake_approval"] > 0
    assert families["QCH_fake_formal_sidecar"] > 0
    assert families["BINDING_fake_promotion"] > 0
    assert all(row["match_status"] == "MATCH" for row in replay)
    assert all(row["unexpected_pass"] == "false" for row in replay)
    assert all(row["unexpected_accept"] == "false" for row in replay)
    assert all(row["authorization_promotion"] == "false" for row in replay)
    assert summary[0]["policy_relevant_mismatch"] == "0"


def test_gate8d_producer_spec_rehearsal_intake_never_approves() -> None:
    intake = read_csv_rows(OUT / "NODI_COMSOL_GATE8D_PRODUCER_SPEC_REHEARSAL_INTAKE_20260629.csv")
    verdict_by_workstream = Counter((row["workstream"], row["nodi_verdict"]) for row in intake)

    assert len(intake) == 39
    assert verdict_by_workstream[("EDGE", "PREAUTH_REQUIRED")] == 12
    assert verdict_by_workstream[("QCH", "REJECT_BLOCKED")] == 12
    assert verdict_by_workstream[("BINDING", "REJECT_BLOCKED")] == 12
    assert all(row["authorization_status"] == "NOT_AUTHORIZED_REHEARSAL_ONLY" for row in intake)
    assert all(row["approved"] == "false" for row in intake)
    assert all(row["evidence_accepted"] == "false" for row in intake)


def test_gate8e_single_workstream_rehearsal_defers_qch_and_binding() -> None:
    edge = read_csv_rows(OUT / "NODI_COMSOL_GATE8E_EDGE_ONLY_REHEARSAL_RUNBOOK_20260629.csv")
    deferrals = read_csv_rows(OUT / "NODI_COMSOL_GATE8E_QCH_BINDING_DENIAL_DEFERRAL_RUNBOOKS_20260629.csv")
    board = read_csv_rows(OUT / "NODI_COMSOL_GATE8E_AUTHORIZATION_REHEARSAL_BOARD_20260629.csv")

    assert len(edge) == 3
    assert all(row["authorization_status"] == "NOT_AUTHORIZED_REHEARSAL_ONLY" for row in edge)
    assert {row["deferral_status"] for row in deferrals} == {
        "DEFERRED_FORMAL_SIDECAR_ABSENT",
        "DEFERRED_FAIL_CLOSED",
    }
    assert board[0]["workstream"] == "EDGE"
    assert board[0]["priority"] == "P1_PREFERRED_FIRST_PILOT"


def test_gate8f_isolation_proof_hard_fails_leakage_and_does_not_approve_edge() -> None:
    isolation = read_csv_rows(OUT / "NODI_COMSOL_GATE8F_ISOLATION_MATRIX_20260629.csv")
    summary = read_csv_rows(OUT / "NODI_COMSOL_GATE8F_ISOLATION_SUMMARY_20260629.csv")
    by_family = {row["case_family"]: row for row in isolation}

    assert len(isolation) == 1000
    assert by_family["EDGE_legitimate_template"]["actual_nodi_disposition"] == "PREAUTH_REQUIRED"
    assert by_family["QCH_formal_sidecar_leakage"]["actual_nodi_disposition"] == "HARD_FAIL_FORBIDDEN_AUTHORIZATION"
    assert by_family["BINDING_promotion_leakage"]["actual_nodi_disposition"] == "HARD_FAIL_FORBIDDEN_AUTHORIZATION"
    assert all(row["authorization_promotion"] == "false" for row in isolation)
    assert summary[0]["unexpected_accept"] == "0"


def test_gate8g_gate8h_signoff_and_anti_confusion_boundaries() -> None:
    board = read_csv_rows(OUT / "NODI_COMSOL_GATE8G_JOINT_FREEZE_SIGNOFF_CANDIDATE_BOARD_20260629.csv")
    terms = read_csv_rows(OUT / "NODI_COMSOL_GATE8H_ANTI_CONFUSION_FORBIDDEN_PROMOTION_TERMS_20260629.csv")

    assert {row["conclusion"] for row in board} >= {
        "CAN_SIGNOFF_INTERFACE_FREEZE_CANDIDATE",
        "CANNOT_AUTHORIZE_EVIDENCE",
        "EDGE_PILOT_PREAUTH_READY_FOR_USER_DECISION",
        "QCH_DEFERRED_FORMAL_SIDECAR_ABSENT",
        "BINDING_DEFERRED_FAIL_CLOSED",
    }
    assert all(row["verdict"] == "true" for row in board)
    assert {"freeze", "preauth", "approved", "production", "JRC", "weighting"} <= {row["term"] for row in terms}
    assert all(row["positive_flag_handling"] == "HARD_FAIL_UNLESS_NEGATIVE_FIXTURE_CONTEXT" for row in terms)


def test_gate8i_gate8j_archive_self_review_and_no_auth_sweep() -> None:
    archive = read_csv_rows(OUT / "NODI_COMSOL_GATE8I_RELEASE_ARCHIVE_INDEX_20260629.csv")
    handoff = read_csv_rows(OUT / "NODI_COMSOL_GATE8I_HANDOFF_MANIFEST_20260629.csv")
    validation = read_csv_rows(OUT / "NODI_COMSOL_GATE8J_VALIDATION_MATRIX_20260629.csv")
    sweep = read_csv_rows(OUT / "NODI_COMSOL_GATE8J_NO_AUTH_SWEEP_20260629.csv")
    review = read_csv_rows(OUT / "NODI_COMSOL_GATE8J_SELF_REVIEW_20260629.csv")

    assert len(archive) == 4
    assert any(row["gate"] == "Gate8" and row["commit"] == "PENDING_THIS_COMMIT" for row in archive)
    assert any(row["handoff_item"] == "gate2d_freeze" and "exactly 4" in row["value"] for row in handoff)
    assert len(validation) == 12
    assert all(row["status"] == "PASS" for row in validation)
    assert sweep[0]["sweep_status"] == "PASS_NO_AUTH"
    assert len(review) == 12
    assert all(row["status"] == "PASS" for row in review)
