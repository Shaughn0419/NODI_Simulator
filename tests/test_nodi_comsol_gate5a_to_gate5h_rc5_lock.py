from __future__ import annotations

from collections import Counter
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate5a_to_gate5h_rc5_lock as gate5


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate5_payload_thresholds_and_dispositions() -> None:
    payload = gate5.build_payload(gate5.DEFAULT_COMSOL_ROOT)

    assert gate5.validate_payload(payload) == []
    assert payload["summary"]["comsol_artifact_receipt_rows"] == 15
    assert payload["summary"]["comsol_rc5_field_map_rows"] == 351
    assert payload["summary"]["comsol_probe_rows"] == 120
    assert payload["summary"]["comsol_rc5_index_rows"] == 8
    assert payload["summary"]["comsol_authorization_dependency_rows"] == 36
    assert payload["summary"]["comsol_command_guard_rows"] == 6
    assert payload["summary"]["comsol_mutation_v4_rows"] == 960
    assert payload["summary"]["comsol_validation_rows"] == 13
    assert payload["summary"]["comsol_manifest_rows"] == 36
    assert payload["summary"]["gate2d_rows"] == 4


def test_gate5a_receipt_register_is_not_evidence_no_auth() -> None:
    rows = read_csv_rows(OUT / "NODI_COMSOL_GATE5A_COMSOL_GATE4_RECEIPT_REGISTER_20260629.csv")
    statuses = Counter(row["receipt_status"] for row in rows)

    assert len(rows) == 36
    assert statuses["BLOCKING_MISMATCH"] == 0
    assert statuses["MATCH"] == 33
    assert statuses["RECORDED_SELF_REFERENTIAL_HASH_DRIFT_NON_POLICY"] == 3
    assert all(row["evidence_bearing"] == "false" for row in rows)
    assert all(row["authorization_trigger"] == "false" for row in rows)
    assert any(row["artifact_kind"] == "rc5_field_map_draft" for row in rows)
    assert any(row["artifact_kind"] == "mutation_v4" for row in rows)


def test_gate5b_closes_all_pending_rows_without_policy_conflict() -> None:
    closure = read_csv_rows(OUT / "NODI_COMSOL_GATE5B_PENDING_CLOSURE_MATRIX_20260629.csv")
    blockers = read_csv_rows(OUT / "NODI_COMSOL_GATE5B_PENDING_CLOSURE_BLOCKER_REGISTER_20260629.csv")
    counts = Counter(row["closure_classification"] for row in closure)

    assert len(closure) == 120
    assert all(row["pending_closed"] == "true" for row in closure)
    assert all(row["true_policy_conflict"] == "false" for row in closure)
    assert counts["EXACT_MATCH"] == 72
    assert counts["HARMLESS_LABEL_DELTA"] == 24
    assert counts["ADAPTER_GAP_CLOSED"] == 24
    assert blockers[0]["blocker_status"] == "PASS_TRUE_POLICY_CONFLICT_ZERO"


def test_gate5c_rc5_convergence_has_no_semantic_conflict() -> None:
    matrix = read_csv_rows(OUT / "NODI_COMSOL_GATE5C_RC5_CONVERGENCE_MATRIX_20260629.csv")
    conflicts = read_csv_rows(OUT / "NODI_COMSOL_GATE5C_RC5_SEMANTIC_CONFLICT_REGISTER_20260629.csv")

    assert len(matrix) >= 351
    assert all(row["semantic_conflict"] == "false" for row in matrix)
    assert conflicts[0]["status"] == "PASS_SEMANTIC_CONFLICT_ZERO"
    assert any(row["difference_class"] == "MATCH" for row in matrix)
    assert all(row["auth_impact"] == "none" for row in matrix)


def test_gate5d_adapter_controls_do_not_change_verdict_or_authorize() -> None:
    plan = read_csv_rows(OUT / "NODI_COMSOL_GATE5D_ADAPTER_CLOSURE_PLAN_V3_20260629.csv")
    controls = read_csv_rows(OUT / "NODI_COMSOL_GATE5D_ADAPTER_NEGATIVE_CONTROL_RESULTS_20260629.csv")

    assert len(plan) == 104
    assert len(controls) == 104
    assert sum(1 for row in plan if row["adapter_rule_id"].startswith("G5D-NODI-GAP")) == 24
    assert all(row["policy_change_allowed"] == "false" for row in plan)
    assert all(row["accepted_or_authorized_after_adapter"] == "false" for row in controls)
    assert all(row["negative_control_status"] == "PASS_NO_VERDICT_CHANGE" for row in controls)


def test_gate5e_owner_and_command_guard_are_fail_closed_no_execution() -> None:
    owner = read_csv_rows(OUT / "NODI_COMSOL_GATE5E_OWNER_COMMAND_ROUNDTRIP_MATRIX_20260629.csv")
    command = read_csv_rows(OUT / "NODI_COMSOL_GATE5E_COMMAND_GUARD_ROUNDTRIP_20260629.csv")

    assert len(owner) == 36
    assert len(command) == 6
    assert all(row["current_action_allowed"] == "false" for row in owner)
    assert all(row["roundtrip_status"] == "PASS_FAIL_CLOSED" for row in owner)
    assert all(row["current_execution_allowed"] == "false" for row in command)
    assert all(row["execution_performed"] == "false" for row in command)
    assert all(row["guard_status"] == "PASS_TEXT_ONLY_NO_EXECUTION" for row in command)


def test_gate5f_mutation_cross_replay_has_zero_unexpected_pass() -> None:
    receipt = read_csv_rows(OUT / "NODI_COMSOL_GATE5F_MUTATION_CROSS_REPLAY_RECEIPT_20260629.csv")
    combined = read_csv_rows(OUT / "NODI_COMSOL_GATE5F_MUTATION_COMBINED_SUMMARY_20260629.csv")
    adapter_cases = read_csv_rows(OUT / "NODI_COMSOL_GATE5F_MUTATION_ADAPTER_NEW_CASES_20260629.csv")
    sources = Counter(row["source_side"] for row in combined)

    assert len(receipt) == 960
    assert len(combined) == 1792
    assert len(adapter_cases) == 72
    assert sources["NODI_GATE4F"] == 760
    assert sources["COMSOL_GATE4G"] == 960
    assert sources["NODI_SYNTHETIC_ADAPTER_CONTROL"] == 72
    assert all(row["unexpected_pass"] == "false" for row in combined)
    assert all(row["forbidden_promotion"] == "false" for row in combined)


def test_gate5g_lock_candidate_and_gate5h_no_auth_sweep() -> None:
    manifest = read_csv_rows(OUT / "NODI_COMSOL_GATE5G_RC5_LOCK_CANDIDATE_MANIFEST_20260629.csv")
    cert = read_csv_rows(OUT / "NODI_COMSOL_GATE5G_INTEROP_CERTIFICATE_20260629.csv")
    sweep = read_csv_rows(OUT / "NODI_COMSOL_GATE5H_NO_AUTH_FORBIDDEN_SWEEP_20260629.csv")
    review = read_csv_rows(OUT / "NODI_COMSOL_GATE5H_SELF_REVIEW_20260629.csv")

    assert len(manifest) == 7
    assert all(row["sha256"] != "PENDING_WRITE" for row in manifest)
    assert all(row["not_evidence"] == "true" for row in manifest)
    assert cert[0]["gate2d_accepted_ledger_rows"] == "4"
    assert cert[0]["edge_policy_state"] == "NOT_APPROVED"
    assert cert[0]["qch_formal_sidecar_state"] == "ABSENT"
    assert cert[0]["binding_state"] == "FAIL_CLOSED"
    assert cert[0]["runtime_or_production_authorized"] == "false"
    assert cert[0]["weighting_or_jrc_authorized"] == "false"
    assert sweep[0]["sweep_status"] == "PASS_NO_AUTH"
    assert len(review) == 6
    assert all(row["status"] == "PASS" for row in review)
