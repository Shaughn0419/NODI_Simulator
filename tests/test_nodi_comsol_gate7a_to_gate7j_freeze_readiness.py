from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate7a_to_gate7j_freeze_readiness as gate7


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate7_payload_thresholds_and_no_auth_summary() -> None:
    payload = gate7.build_payload(gate7.DEFAULT_COMSOL_ROOT)

    assert gate7.validate_payload(payload) == []
    assert payload["summary"]["comsol_gate6_receipt_rows"] == 35
    assert payload["summary"]["comsol_gate6_discrepancy_rows"] == 6
    assert payload["summary"]["comsol_gate6_rc51_rows"] == 366
    assert payload["summary"]["comsol_gate6_adapter_rows"] == 86
    assert payload["summary"]["comsol_gate6_errata_rows"] == 3
    assert payload["summary"]["comsol_gate6_validation_rows"] == 14
    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["gate7f_corpus_rows"] == 5100
    assert payload["summary"]["gate7i_no_auth_failures"] == 0


def test_gate7a_receipt_and_rc51_alignment() -> None:
    receipt = read_csv_rows(OUT / "NODI_COMSOL_GATE7A_COMSOL_GATE6_RECEIPT_REGISTER_20260629.csv")
    alignment = read_csv_rows(OUT / "NODI_COMSOL_GATE7A_RC51_ALIGNMENT_CONFIRMATION_20260629.csv")
    counts = Counter(row["receipt_status"] for row in receipt)

    assert len(receipt) == 30
    assert counts["MATCH"] == 27
    assert counts["SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"] == 3
    assert counts["BLOCKING_DATA_DRIFT"] == 0
    assert alignment[0]["canonical_field"] == "nodi_view_binding_status"
    assert alignment[0]["alignment_status"] == "PASS_NON_POLICY_OPTIONAL_GUARD"


def test_gate7b_lockfile_hash_tree_and_state_locks() -> None:
    lockfile = json.loads((OUT / "NODI_COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_20260629.json").read_text(encoding="utf-8"))
    index = read_csv_rows(OUT / "NODI_COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_INDEX_20260629.csv")
    hash_tree = read_csv_rows(OUT / "NODI_COMSOL_GATE7B_RC51_FREEZE_HASH_TREE_20260629.csv")

    assert lockfile["lock_name"] == "NODI_RECEIVER_RC5_1_FREEZE_CANDIDATE"
    assert lockfile["canonical_field_count"] == 365
    assert lockfile["gate2d_accepted_ledger_rows"] == 4
    assert lockfile["edge_policy_state"] == "NOT_APPROVED"
    assert lockfile["qch_formal_sidecar_state"] == "ABSENT"
    assert lockfile["binding_state"] == "FAIL_CLOSED"
    assert lockfile["runtime_schema"] is False
    assert lockfile["production_contract"] is False
    assert lockfile["evidence_acceptance"] is False
    assert len(index) == 7
    assert hash_tree[0]["hash_node_id"] == "G7B-HASH-ROOT"
    assert all(row["no_auth"] == "true" for row in index)


def test_gate7c_receiver_harness_contract_covers_required_checks() -> None:
    api = read_csv_rows(OUT / "NODI_COMSOL_GATE7C_RECEIVER_HARNESS_API_SURFACE_20260629.csv")
    schema = read_csv_rows(OUT / "NODI_COMSOL_GATE7C_EXPECTED_INPUT_PACKAGE_SCHEMA_20260629.csv")
    disp = read_csv_rows(OUT / "NODI_COMSOL_GATE7C_DISPOSITION_CATALOG_20260629.csv")

    assert len(api) == 8
    assert {row["api_name"] for row in api} >= {"manifest_receipt", "forbidden_authorization_check", "gate2d_freeze_check"}
    assert len(schema) == 10
    assert {row["disposition"] for row in disp} == {
        "ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY",
        "RECEIVE_REVIEW_ONLY",
        "PREAUTH_REQUIRED",
        "REJECT_BLOCKED",
        "HARD_FAIL_FORBIDDEN_AUTHORIZATION",
    }
    assert all(row["authorization_effect"] == "none" for row in api)


def test_gate7d_cross_version_compatibility_has_no_hard_incompatible() -> None:
    matrix = read_csv_rows(OUT / "NODI_COMSOL_GATE7D_CROSS_VERSION_COMPATIBILITY_MATRIX_20260629.csv")
    classes = Counter(row["compatibility_class"] for row in matrix)

    assert len(matrix) == 1460
    assert classes["backward-compatible alias"] > 0
    assert classes["receiver-only guard"] >= 1
    assert classes["hard incompatible"] == 0
    assert all(row["requires_user_authorization"] == "false" for row in matrix)


def test_gate7e_preauth_board_is_closed_and_prioritized() -> None:
    board = read_csv_rows(OUT / "NODI_COMSOL_GATE7E_PREAUTH_READINESS_BOARD_V3_20260629.csv")
    priority = read_csv_rows(OUT / "NODI_COMSOL_GATE7E_PREAUTH_PRIORITY_RECOMMENDATION_20260629.csv")

    assert len(board) == 3
    assert {row["workstream"] for row in board} == {"EDGE", "QCH", "BINDING"}
    assert all(row["authorization_status"] == "AUTHORIZATION_CLOSED" for row in board)
    assert priority[0]["recommended_first_trial"] == "EDGE"
    assert priority[1]["highest_risk"] == "BINDING"


def test_gate7f_replay_corpus_zero_unexpected_pass() -> None:
    corpus = read_csv_rows(OUT / "NODI_COMSOL_GATE7F_REPLAY_CORPUS_CATALOG_20260629.csv")
    results = read_csv_rows(OUT / "NODI_COMSOL_GATE7F_REPLAY_RESULTS_20260629.csv")
    unexpected = read_csv_rows(OUT / "NODI_COMSOL_GATE7F_UNEXPECTED_PASS_REGISTER_20260629.csv")

    assert len(corpus) == 5100
    assert len(results) == 5100
    assert any(row["case_family"] == "QCH_fake_formal_sidecar" for row in corpus)
    assert any(row["case_family"] == "BINDING_220_D1200_UNBOUND_promotion" for row in corpus)
    assert all(row["unexpected_pass"] == "false" for row in results)
    assert all(row["authorization_promotion"] == "false" for row in results)
    assert unexpected[0]["unexpected_pass_count"] == "0"


def test_gate7g_gate7h_gate7i_governance_and_release_board() -> None:
    change = read_csv_rows(OUT / "NODI_COMSOL_GATE7G_CHANGE_CONTROL_POLICY_20260629.csv")
    rollback = read_csv_rows(OUT / "NODI_COMSOL_GATE7G_ROLLBACK_MATRIX_20260629.csv")
    board = read_csv_rows(OUT / "NODI_COMSOL_GATE7H_RELEASE_FREEZE_BOARD_SUMMARY_20260629.csv")
    sweep = read_csv_rows(OUT / "NODI_COMSOL_GATE7I_NO_AUTH_SWEEP_20260629.csv")
    review = read_csv_rows(OUT / "NODI_COMSOL_GATE7I_SELF_REVIEW_20260629.csv")

    assert any(row["change_class"] == "breaking" for row in change)
    assert any(row["freeze_candidate_invalidated"] == "true" for row in rollback)
    assert {row["conclusion_class"] for row in board} >= {
        "CAN_FREEZE_INTERFACE_CANDIDATE",
        "CANNOT_AUTHORIZE_EVIDENCE",
        "REQUIRES_USER_PREAUTH_FOR_NEXT_GATE",
        "HARD_BLOCKED_WORKSTREAMS",
    }
    assert sweep[0]["sweep_status"] == "PASS_NO_AUTH"
    assert len(review) == 10
    assert all(row["status"] == "PASS" for row in review)
