from __future__ import annotations

from pathlib import Path

from nodi_simulator.nodi_comsol_gate4_interop import compare_expected_to_actual, decide_comsol_gate3_row, expected_label_to_disposition
from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate4a_to_gate4h_interop_dry_run as gate4


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate4_payload_thresholds_and_no_auth_invariants() -> None:
    payload = gate4.build_payload(gate4.DEFAULT_COMSOL_ROOT)

    assert gate4.validate_payload(payload) == []
    assert payload["summary"]["producer_spec_rows"] == 35
    assert payload["summary"]["probe_rows"] == 120
    assert payload["summary"]["go_no_go_rows"] == 36
    assert payload["summary"]["dependency_nodes"] == 160
    assert payload["summary"]["dependency_edges"] == 220
    assert payload["summary"]["mutation_rows"] == 760
    assert payload["summary"]["mutation_unexpected_pass"] == 0
    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["no_auth_sweep_failures"] == 0


def test_package_specs_are_template_only_not_evidence() -> None:
    rows = read_csv_rows(OUT / "NODI_COMSOL_GATE4A_PRODUCER_PACKAGE_SPEC_RECEIPT_20260629.csv")

    assert len(rows) == 35
    assert all(row["not_evidence"] == "true" for row in rows)
    assert all(row["template_only"] == "true" for row in rows)
    assert all(row["evidence_accepted"] == "false" for row in rows)
    assert all(row["authorization_opened"] == "false" for row in rows)


def test_probe_conformance_has_no_policy_relevant_mismatch() -> None:
    actuals = read_csv_rows(OUT / "NODI_COMSOL_GATE4C_COMSOL_PROBE_ACTUAL_VS_EXPECTED_20260629.csv")
    mismatches = read_csv_rows(OUT / "NODI_COMSOL_GATE4C_PROBE_MISMATCH_REGISTER_20260629.csv")

    assert len(actuals) == 120
    assert all(row["mismatch_class"] != "policy_relevant_mismatch" for row in actuals)
    assert all(row["evidence_accepted"] == "false" for row in actuals)
    assert any(row["conformance_status"] == "ADAPTER_REQUIRED" for row in actuals)
    assert all(row["mismatch_class"] != "policy_relevant_mismatch" for row in mismatches)


def test_adapter_label_mapping_and_forbidden_hard_fail() -> None:
    assert expected_label_to_disposition("EXPECTED_PREAUTH_REQUIRED_NO_RUN") == "PREAUTH_REQUIRED"
    assert compare_expected_to_actual("EXPECTED_REJECT_BLOCKED", "REJECT_BLOCKED")["conformance_status"] == "MATCH"
    row = {"probe_category": "review_only", "not_evidence": "true", "template_only": "true", "forbidden_auth_flag_state": "true"}
    assert decide_comsol_gate3_row(row, row_kind="probe")["disposition"] == "HARD_FAIL_FORBIDDEN_AUTHORIZATION"


def test_critical_path_dependency_and_recipe_are_no_run() -> None:
    go = read_csv_rows(OUT / "NODI_COMSOL_GATE4D_COMSOL_GO_NO_GO_RECEIPT_20260629.csv")
    nodes = read_csv_rows(OUT / "NODI_COMSOL_GATE4E_DEPENDENCY_NODE_RECEIPT_20260629.csv")
    edges = read_csv_rows(OUT / "NODI_COMSOL_GATE4E_DEPENDENCY_EDGE_RECEIPT_20260629.csv")
    recipes = read_csv_rows(OUT / "NODI_COMSOL_GATE4E_FUTURE_COMMAND_RECIPE_GUARD_20260629.csv")

    assert len(go) == 36
    assert len(nodes) == 160
    assert len(edges) == 220
    assert len(recipes) == 6
    assert all(row["current_execution_allowed"] == "false" for row in [*go, *nodes, *edges, *recipes])
    assert all(row["execution_performed"] == "false" for row in recipes)
    assert all(row["future_authorization_required"] == "true" for row in recipes)


def test_mutation_cross_validation_and_rc5_contract_only() -> None:
    mutations = read_csv_rows(OUT / "NODI_COMSOL_GATE4F_COMSOL_MUTATION_V3_RECEIPT_20260629.csv")
    unexpected = read_csv_rows(OUT / "NODI_COMSOL_GATE4F_UNEXPECTED_PASS_CROSS_REGISTER_20260629.csv")
    rc5 = read_csv_rows(OUT / "NODI_COMSOL_GATE4G_CANONICAL_FIELD_DICTIONARY_RC5_20260629.csv")

    assert len(mutations) == 760
    assert all(row["unexpected_pass"] == "false" for row in mutations)
    assert unexpected
    assert all(row["nodi_cross_status"] in {"PASS_NO_UNEXPECTED_PASS", "REVIEW"} for row in unexpected)
    assert rc5
    assert any(row["field_category"] == "forbidden_positive_authorization" for row in rc5)
    assert all(row["gate2d_freeze_inherited"] == "true" for row in rc5)


def test_gate4h_freeze_and_forbidden_sweep_clean() -> None:
    ledger = read_csv_rows(OUT / "NODI_COMSOL_GATE4H_ACCEPTED_LEDGER_FREEZE_AUDIT_20260629.csv")
    sweep = read_csv_rows(OUT / "NODI_COMSOL_GATE4H_FORBIDDEN_AUTH_SWEEP_20260629.csv")

    assert ledger[0]["actual_rows"] == "4"
    assert ledger[0]["audit_status"] == "PASS"
    assert sweep
    assert all(row["sweep_status"] == "PASS_NO_AUTH" for row in sweep)
