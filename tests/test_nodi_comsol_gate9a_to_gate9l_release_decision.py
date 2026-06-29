from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate9a_to_gate9l_release_decision as gate9


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate9_payload_thresholds_and_no_auth_summary() -> None:
    payload = gate9.build_payload(gate9.DEFAULT_COMSOL_ROOT)

    assert gate9.validate_payload(payload) == []
    assert payload["summary"]["comsol_manifest_rows"] == 35
    assert payload["summary"]["comsol_validation_rows"] == 14
    assert payload["summary"]["comsol_receipt_rows"] == 45
    assert payload["summary"]["comsol_hash_recon_rows"] == 21
    assert payload["summary"]["comsol_bundle_rows"] == 24
    assert payload["summary"]["comsol_edge_dossier_rows"] == 1
    assert payload["summary"]["comsol_isolation_rows"] == 1800
    assert payload["summary"]["gate2d_rows"] == 4


def test_gate9a_comsol_gate8_receipt_and_closure() -> None:
    receipt = read_csv_rows(OUT / "NODI_COMSOL_GATE9A_COMSOL_GATE8_RECEIPT_REGISTER_20260629.csv")
    closure = read_csv_rows(OUT / "NODI_COMSOL_GATE9A_BIDIRECTIONAL_CLOSURE_MATRIX_20260629.csv")
    counts = Counter(row["receipt_status"] for row in receipt)

    assert len(receipt) == 35
    assert counts["BLOCKING_DATA_DRIFT"] == 0
    assert counts["MISSING_REQUIRED_ARTIFACT"] == 0
    assert all(row["evidence_bearing"] == "false" for row in receipt)
    assert {row["closure_axis"] for row in closure} >= {"freeze_state", "edge_only_rehearsal", "qch_deferral", "binding_deferral", "anti_confusion"}
    assert all("CLOSED" in row["closure_status"] for row in closure)


def test_gate9b_release_lockfile_and_field_dictionary() -> None:
    fields = read_csv_rows(OUT / "NODI_COMSOL_GATE9B_RELEASE_FIELD_DICTIONARY_20260629.csv")
    hashes = read_csv_rows(OUT / "NODI_COMSOL_GATE9B_RELEASE_HASH_TREE_20260629.csv")
    lockfile = json.loads((OUT / "NODI_COMSOL_GATE9B_RELEASE_LOCKFILE_20260629.json").read_text(encoding="utf-8"))
    status = json.loads((OUT / "NODI_COMSOL_GATE9B_RELEASE_STATUS_20260629.json").read_text(encoding="utf-8"))

    assert len(fields) == 365
    assert lockfile["lock_name"] == "JOINT_RC5_1_FREEZE_RELEASE_V1_CANDIDATE_REVIEW_ONLY"
    assert lockfile["version"] == "RC5.1-freeze-v1-candidate-20260629"
    assert lockfile["review_only"] is True
    assert lockfile["evidence_acceptance"] is False
    assert lockfile["runtime_schema"] is False
    assert lockfile["authorization"] == "closed"
    assert status["no_auth"] is True
    assert len(hashes) == 4
    assert all(row["runtime_schema"] == "false" for row in fields)


def test_gate9c_decision_dossier_choices_are_mutually_exclusive_and_unapproved() -> None:
    choices = read_csv_rows(OUT / "NODI_COMSOL_GATE9C_USER_DECISION_DOSSIER_20260629.csv")
    signoffs = read_csv_rows(OUT / "NODI_COMSOL_GATE9C_USER_SIGNOFF_TEXTS_20260629.csv")
    status = json.loads((OUT / "NODI_COMSOL_GATE9C_DECISION_STATUS_20260629.json").read_text(encoding="utf-8"))

    assert {row["choice_id"] for row in choices} == {
        "FREEZE_INTERFACE_ONLY_NO_EVIDENCE_AUTH",
        "AUTHORIZE_EDGE_ONLY_PREAUTH_NEXT_GATE",
        "DEFER_ALL_EVIDENCE_AUTHORIZATION",
    }
    assert all(row["default_state"] == "AWAITING_USER_DECISION" for row in choices)
    assert all(row["approved"] == "false" for row in choices)
    assert all(row["mutually_exclusive"] == "true" for row in signoffs)
    assert status["approved_choice"] is None


def test_gate9d_edge_escrow_is_non_executable_and_does_not_open_qch_binding() -> None:
    escrow = read_csv_rows(OUT / "NODI_COMSOL_GATE9D_EDGE_PREAUTH_ESCROW_PACKAGE_20260629.csv")
    token = read_csv_rows(OUT / "NODI_COMSOL_GATE9D_AUTHORIZATION_TOKEN_SCHEMA_20260629.csv")
    status = json.loads((OUT / "NODI_COMSOL_GATE9D_EDGE_ESCROW_STATUS_20260629.json").read_text(encoding="utf-8"))

    assert len(escrow) == 5
    assert all(row["authorization_token_present"] == "false" for row in escrow)
    assert all(row["execution_allowed"] == "false" for row in escrow)
    assert all(row["evidence_acceptance_allowed"] == "false" for row in escrow)
    assert all(row["opens_qch_binding_jrc_runtime_production"] == "false" for row in token)
    assert status["authorization_token_present"] is False
    assert status["execution_allowed"] is False
    assert status["qch_binding_jrc_runtime_production_opened"] is False


def test_gate9e_state_machine_is_quarantine_first_and_never_production() -> None:
    machine = read_csv_rows(OUT / "NODI_COMSOL_GATE9E_POST_AUTH_INTAKE_STATE_MACHINE_20260629.csv")
    status = json.loads((OUT / "NODI_COMSOL_GATE9E_STATE_MACHINE_20260629.json").read_text(encoding="utf-8"))

    assert len(machine) == 5
    assert machine[0]["state"] == "RECEIPT"
    assert machine[0]["allowed_transition"] == "QUARANTINE"
    assert all(row["quarantine_first"] == "true" for row in machine)
    assert all(row["production_ingestion"] == "false" for row in machine)
    assert status["production_ingestion"] is False
    assert status["runtime_configuration"] is False


def test_gate9f_qch_binding_seals_keep_edge_from_reopening_them() -> None:
    seals = read_csv_rows(OUT / "NODI_COMSOL_GATE9F_QCH_BINDING_SEALED_DEFERRAL_REGISTER_20260629.csv")
    prereqs = read_csv_rows(OUT / "NODI_COMSOL_GATE9F_REOPEN_PREREQUISITES_20260629.csv")

    assert {row["workstream"] for row in seals} == {"QCH", "BINDING"}
    assert {row["current_state"] for row in seals} == {"ABSENT", "FAIL_CLOSED"}
    assert all(row["edge_pilot_can_reopen"] == "false" for row in seals)
    assert all(row["authorization_status"] == "SEALED_DEFERRED_AUTHORIZATION_CLOSED" for row in seals)
    assert all(row["hard_fail_if_missing"] == "true" for row in prereqs)


def test_gate9g_provenance_ledger_and_non_policy_deltas_are_complete() -> None:
    ledger = read_csv_rows(OUT / "NODI_COMSOL_GATE9G_JOINT_PROVENANCE_LEDGER_20260629.csv")
    deltas = read_csv_rows(OUT / "NODI_COMSOL_GATE9G_KNOWN_NON_POLICY_DELTAS_20260629.csv")

    assert len(ledger) == 8
    assert {row["side"] for row in ledger} == {"NODI", "COMSOL"}
    assert {row["gate"] for row in ledger} >= {"Gate5", "Gate6", "Gate7", "Gate8"}
    assert {row["classification"] for row in deltas} == {"non_policy_delta", "metadata_non_policy", "directional_scope_delta"}
    assert all(row["authorization_impact"] == "none" for row in deltas)


def test_gate9h_no_auth_and_anti_confusion_v2_are_clean() -> None:
    sweep = read_csv_rows(OUT / "NODI_COMSOL_GATE9H_NO_AUTH_SWEEP_V2_20260629.csv")
    anti = read_csv_rows(OUT / "NODI_COMSOL_GATE9H_ANTI_CONFUSION_V2_20260629.csv")

    assert sweep[0]["sweep_status"] == "PASS_NO_AUTH"
    assert {"freeze", "signoff", "ready", "pilot", "preauth", "escrow", "token", "runbook"} == {row["term"] for row in anti}
    assert all(row["positive_flag_handling"] == "HARD_FAIL_UNLESS_EXPLICIT_FUTURE_USER_AUTH" for row in anti)


def test_gate9i_gate9j_gate9k_support_validation_and_samples() -> None:
    brief = read_csv_rows(OUT / "NODI_COMSOL_GATE9I_EXECUTIVE_PACKET_SUPPORT_20260629.csv")
    validation = read_csv_rows(OUT / "NODI_COMSOL_GATE9J_VALIDATION_MATRIX_20260629.csv")
    review = read_csv_rows(OUT / "NODI_COMSOL_GATE9J_SELF_REVIEW_20260629.csv")
    samples = read_csv_rows(OUT / "NODI_COMSOL_GATE9K_SAFE_DRY_RUN_PACKAGE_EXAMPLES_20260629.csv")

    assert len(brief) == 5
    assert len(validation) == 12
    assert all(row["status"] == "PASS" for row in validation)
    assert len(review) == 12
    assert all(row["status"] == "PASS" for row in review)
    assert len(samples) == 5
    assert all(row["not_evidence"] == "true" for row in samples)
    assert all(row["approved"] == "false" for row in samples)
