from __future__ import annotations

from collections import Counter
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate6a_to_gate6h_lockstep_release as gate6


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate6_payload_thresholds_and_zero_conflicts() -> None:
    payload = gate6.build_payload(gate6.DEFAULT_COMSOL_ROOT)

    assert gate6.validate_payload(payload) == []
    assert payload["summary"]["comsol_gate5_manifest_rows"] == 31
    assert payload["summary"]["comsol_gate5_receipt_rows"] == 40
    assert payload["summary"]["comsol_gate5_probe_rows"] == 120
    assert payload["summary"]["comsol_gate5_adapter_rows"] == 48
    assert payload["summary"]["comsol_gate5_rc5_rows"] == 366
    assert payload["summary"]["comsol_gate5_owner_rows"] == 36
    assert payload["summary"]["comsol_gate5_mutation_rows"] == 1800
    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["gate6b_semantic_conflicts"] == 0
    assert payload["summary"]["gate6b_policy_conflicts"] == 0


def test_gate6a_receipt_classifies_only_self_referential_metadata_drift() -> None:
    rows = read_csv_rows(OUT / "NODI_COMSOL_GATE6A_COMSOL_GATE5_PACKAGE_RECEIPT_20260629.csv")
    counts = Counter(row["receipt_status"] for row in rows)

    assert len(rows) == 31
    assert counts["MATCH"] == 28
    assert counts["SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"] == 3
    assert counts["BLOCKING_DATA_DRIFT"] == 0
    assert all(row["auth_impact"] == "none" for row in rows)


def test_gate6b_explains_required_cross_side_discrepancies() -> None:
    rows = read_csv_rows(OUT / "NODI_COMSOL_GATE6B_GATE5_CROSS_SIDE_DISCREPANCY_LEDGER_20260629.csv")
    topics = {row["topic"] for row in rows}

    assert len(rows) == 8
    assert "receipt row count" in topics
    assert "RC5 row count" in topics
    assert "adapter rule count" in topics
    assert "mutation row count" in topics
    assert "COMSOL Gate4 self-referential metadata SHA drift" in topics
    assert all(row["semantic_conflict"] == "false" for row in rows)
    assert all(row["policy_conflict"] == "false" for row in rows)


def test_gate6c_rc51_dictionary_reconciles_365_366_as_duplicate_field() -> None:
    rows = read_csv_rows(OUT / "NODI_COMSOL_GATE6C_RC5_1_LOCKSTEP_DICTIONARY_20260629.csv")
    dupes = read_csv_rows(OUT / "NODI_COMSOL_GATE6C_RC5_1_DUPLICATE_FIELD_EXPLANATION_20260629.csv")

    assert len(rows) == 365
    assert dupes[0]["canonical_field"] == "nodi_view_binding_status"
    assert dupes[0]["comsol_row_count"] == "2"
    assert all(row["auth_impact"] == "none" for row in rows)
    assert all(row["lockstep_status"] == "LOCKSTEP_FIELD_CONVERGED" for row in rows)
    assert {row["edge_policy_state"] for row in rows} == {"NOT_APPROVED"}
    assert {row["qch_state"] for row in rows} == {"ABSENT"}
    assert {row["binding_state"] for row in rows} == {"FAIL_CLOSED"}


def test_gate6d_adapter_harmonization_has_negative_controls() -> None:
    rows = read_csv_rows(OUT / "NODI_COMSOL_GATE6D_ADAPTER_HARMONIZATION_MATRIX_20260629.csv")
    controls = read_csv_rows(OUT / "NODI_COMSOL_GATE6D_ADAPTER_HARMONIZATION_NEGATIVE_CONTROLS_20260629.csv")
    classes = Counter(row["harmonization_class"] for row in rows)

    assert len(rows) == 108
    assert classes["common_rules"] > 0
    assert classes["nodi_receiver_only_rules"] > 0
    assert classes["comsol_producer_only_rules"] > 0
    assert len(controls) == len(rows)
    assert all(row["policy_verdict_change_allowed"] == "false" for row in rows)
    assert all(row["authorization_promotion_allowed"] == "false" for row in rows)
    assert all(row["verdict_change"] == "false" for row in controls)
    assert all(row["authorization_promotion"] == "false" for row in controls)


def test_gate6e_mutation_probe_union_zero_unexpected_pass() -> None:
    union = read_csv_rows(OUT / "NODI_COMSOL_GATE6E_MUTATION_PROBE_UNION_20260629.csv")
    summary = read_csv_rows(OUT / "NODI_COMSOL_GATE6E_MUTATION_PROBE_UNION_SUMMARY_20260629.csv")
    sources = Counter(row["source_side"] for row in union)

    assert len(union) == 3592
    assert sources["NODI_GATE5F"] == 1792
    assert sources["COMSOL_GATE5F"] == 1800
    assert all(row["unexpected_pass"] == "false" for row in union)
    assert all(row["authorization_promotion"] == "false" for row in union)
    assert summary[-1]["mutation_family"] == "TOTAL"
    assert summary[-1]["row_equivalent_count"] == "3592"


def test_gate6f_gate6g_gate6h_lock_certificate_and_no_auth() -> None:
    drift = read_csv_rows(OUT / "NODI_COMSOL_GATE6F_METADATA_DRIFT_ERRATA_MATRIX_20260629.csv")
    cert = read_csv_rows(OUT / "NODI_COMSOL_GATE6G_NO_AUTH_LOCK_CERTIFICATE_20260629.csv")
    manifest = read_csv_rows(OUT / "NODI_COMSOL_GATE6G_RC5_1_RELEASE_MANIFEST_20260629.csv")
    sweep = read_csv_rows(OUT / "NODI_COMSOL_GATE6H_NO_AUTH_LOCKSTEP_SWEEP_20260629.csv")
    review = read_csv_rows(OUT / "NODI_COMSOL_GATE6H_SELF_REVIEW_20260629.csv")

    assert len(drift) == 6
    assert Counter(row["superseded_by_gate5"] for row in drift) == {"true": 3, "false": 3}
    assert cert[0]["release_candidate"] == "RC5_1_LOCKSTEP_CANDIDATE_REVIEW_ONLY"
    assert cert[0]["gate2d_accepted_ledger_rows"] == "4"
    assert cert[0]["edge_policy_state"] == "NOT_APPROVED"
    assert cert[0]["qch_formal_sidecar_state"] == "ABSENT"
    assert cert[0]["binding_state"] == "FAIL_CLOSED"
    assert cert[0]["runtime_or_production_authorized"] == "false"
    assert cert[0]["weighting_or_jrc_authorized"] == "false"
    assert len(manifest) == 7
    assert all(row["sha256"] != "PENDING_WRITE" for row in manifest)
    assert sweep[0]["sweep_status"] == "PASS_NO_AUTH"
    assert len(review) == 8
    assert all(row["status"] == "PASS" for row in review)
