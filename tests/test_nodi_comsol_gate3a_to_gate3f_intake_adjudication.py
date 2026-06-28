from __future__ import annotations

from pathlib import Path

from nodi_simulator.nodi_comsol_gate3_intake import DISPOSITIONS, decide_intake
from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate3a_to_gate3f_intake_adjudication as gate3


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate3_payload_counts_and_policy_states() -> None:
    payload = gate3.build_payload(gate3.DEFAULT_COMSOL_ROOT)

    assert gate3.validate_payload(payload) == []
    assert payload["summary"]["nodi_dossiers"] == 75
    assert payload["summary"]["comsol_dossiers"] == 180
    assert payload["summary"]["comsol_closure_trials"] == 60
    assert payload["summary"]["gate3a_adjudication_rows"] == 315
    assert payload["summary"]["gate2d_accepted_rows"] == 4
    assert payload["summary"]["edge_policy"] == "NOT_APPROVED"
    assert payload["summary"]["qch_formal_sidecar"] == "ABSENT"
    assert payload["summary"]["binding_state"] == "FAIL_CLOSED"


def test_intake_emulator_disposition_coverage_and_forbidden_hard_fail() -> None:
    assert set(DISPOSITIONS) == {
        "ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY",
        "RECEIVE_REVIEW_ONLY",
        "PREAUTH_REQUIRED",
        "REJECT_BLOCKED",
        "HARD_FAIL_FORBIDDEN_AUTHORIZATION",
    }
    ledger = decide_intake({"context_only_acceptance_allowed": "true"}, row_kind="gate2d_ledger")
    template = decide_intake({"template_only": "true", "not_evidence": "true"}, row_kind="template")
    dossier = decide_intake({"workstream": "EDGE", "source_sha256": "abc"}, row_kind="dossier")
    blocked = decide_intake({"workstream": "BINDING", "blocked_use": "220 nm blocked"}, row_kind="dossier")
    hard_fail = decide_intake({"formula_use_authorized": "true"}, row_kind="dossier")

    assert ledger.disposition == "ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY"
    assert template.disposition == "RECEIVE_REVIEW_ONLY"
    assert dossier.disposition == "PREAUTH_REQUIRED"
    assert blocked.disposition == "REJECT_BLOCKED"
    assert hard_fail.disposition == "HARD_FAIL_FORBIDDEN_AUTHORIZATION"


def test_comsol_dry_run_accepts_no_evidence_and_freezes_gate2d() -> None:
    dossiers = read_csv_rows(OUT / "NODI_COMSOL_GATE3C_COMSOL_DOSSIER_DRY_RUN_RESULTS_20260629.csv")
    trials = read_csv_rows(OUT / "NODI_COMSOL_GATE3C_CLOSURE_TRIAL_DRY_RUN_RESULTS_20260629.csv")
    ledger = read_csv_rows(OUT / "NODI_COMSOL_GATE3C_EXISTING_GATE2D_LEDGER_FREEZE_CHECK_20260629.csv")

    assert len(dossiers) == 180
    assert len(trials) == 60
    assert all(row["evidence_accepted"] == "false" for row in [*dossiers, *trials])
    assert len(ledger) == 4
    assert {row["disposition"] for row in ledger} == {"ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY"}
    assert all(row["gate2d_ledger_expansion"] == "false" for row in [*dossiers, *trials, *ledger])


def test_mutation_v3_and_fixture_controls_zero_unexpected_pass() -> None:
    catalog = read_csv_rows(OUT / "NODI_COMSOL_GATE3F_MUTATION_V3_FIXTURE_CATALOG_20260629.csv")
    results = read_csv_rows(OUT / "NODI_COMSOL_GATE3F_MUTATION_V3_RESULTS_20260629.csv")
    unexpected = read_csv_rows(OUT / "NODI_COMSOL_GATE3F_UNEXPECTED_PASS_REGISTER_20260629.csv")
    rejected = read_csv_rows(OUT / "NODI_COMSOL_GATE3C_REJECTED_OR_PREAUTH_REQUIRED_REGISTER_20260629.csv")

    assert len(catalog) >= 650
    assert all(row["validation_status"] != "UNEXPECTED_PASS" for row in results)
    assert unexpected[0]["validation_status"] == "PASS_NO_UNEXPECTED_PASS"
    assert any(row["mutation_family"] == "false_positive_blocked_mention" for row in catalog)
    assert any(row["mutation_family"] == "false_negative_authorization_leak" for row in catalog)
    assert len([row for row in rejected if row["disposition"] == "HARD_FAIL_FORBIDDEN_AUTHORIZATION"]) > 0


def test_rc4_and_preauth_board_remain_contract_only() -> None:
    rc4 = read_csv_rows(OUT / "NODI_COMSOL_GATE3E_CANONICAL_FIELD_DICTIONARY_RC4_20260629.csv")
    edge = read_csv_rows(OUT / "NODI_COMSOL_GATE3D_EDGE_PREAUTH_DECISION_TEMPLATE_20260629.csv")
    qch = read_csv_rows(OUT / "NODI_COMSOL_GATE3D_QCH_PREAUTH_DECISION_TEMPLATE_20260629.csv")
    binding = read_csv_rows(OUT / "NODI_COMSOL_GATE3D_BINDING_PREAUTH_DECISION_TEMPLATE_20260629.csv")

    assert rc4
    assert any(row["field_category"] == "forbidden_positive_authorization" for row in rc4)
    assert {row["verdict"] for row in [*edge, *qch, *binding]} == {"AUTHORIZATION_CLOSED"}
    assert all(row["allowed_next_state"] == "PREAUTH_REVIEW_ONLY" for row in [*edge, *qch, *binding])
