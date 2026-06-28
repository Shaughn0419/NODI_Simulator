from __future__ import annotations

from pathlib import Path

from nodi_simulator import nodi_comsol_gate2_interface_contracts as lib
from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate2y_to_gate2ad_deep_dossier as gate2y


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260628"


def test_gate2y_outputs_meet_deep_census_and_dossier_thresholds() -> None:
    report = gate2y.build_payload(gate2y.DEFAULT_COMSOL_ROOT, census_limit=750)
    issues = gate2y.validate_payload(report)

    assert issues == []
    assert report["summary"]["census_fingerprinted"] >= 750
    assert report["summary"]["dossier_count"] >= 75
    counts = report["summary"]["dossier_counts_by_workstream"]
    assert counts["EDGE"] >= 25
    assert counts["QCH"] >= 20
    assert counts["BINDING"] >= 15
    assert report["summary"]["gate2d_accepted_rows"] == 4


def test_mutation_v2_property_controls_are_fail_closed() -> None:
    catalog, results, unexpected = gate2y.build_mutation_v2()

    assert len(catalog) >= 300
    assert sum(1 for row in results if row["validation_status"] == "UNEXPECTED_PASS") == 0
    assert unexpected[0]["validation_status"] == "PASS_NO_UNEXPECTED_PASS"
    assert any(row["validation_status"] == "PASS_FALSE_POSITIVE_CONTROL" for row in results)
    assert any(row["property_family"] == "false_negative_control" for row in results)
    leak = {
        "mutation_id": "X",
        "property_family": "false_negative_control",
        "mutation_name": "formal_qch_sidecar_true_without_sidecar",
        "mutated_value": "true",
        "expected_result": "EXPECTED_FAIL",
    }
    assert lib.validate_property_case(leak)["validation_status"] == "PASS_EXPECTED_FAIL"


def test_dossier_outputs_do_not_promote_proxy_or_review_only_evidence() -> None:
    dossier_rows = read_csv_rows(OUT / "NODI_COMSOL_GATE2Z_DEEP_EVIDENCE_DOSSIER_INDEX_20260628.csv")
    assert dossier_rows
    assert all(row["can_close_existing_work_order"] == "false" for row in dossier_rows)
    assert all("formula use" in row["blocked_use"] for row in dossier_rows)
    assert all("policy evidence" not in row["can_close_reason"].lower() for row in dossier_rows)


def test_pre_auth_board_closed_and_rc3_rejects_authorization_semantics() -> None:
    edge = read_csv_rows(OUT / "NODI_COMSOL_GATE2AB_EDGE_PRE_AUTH_REVIEW_CHECKLIST_20260628.csv")
    qch = read_csv_rows(OUT / "NODI_COMSOL_GATE2AB_QCH_PRE_AUTH_REVIEW_CHECKLIST_20260628.csv")
    binding = read_csv_rows(OUT / "NODI_COMSOL_GATE2AB_BINDING_PRE_AUTH_REVIEW_CHECKLIST_20260628.csv")
    assert all(row["authorization_open"] == "false" for row in [*edge, *qch, *binding])
    assert {row["review_board_verdict"] for row in [*edge, *qch, *binding]} == {"NOT_READY_FOR_AUTHORIZATION"}

    rc3_bad = lib.validate_rc3_semantic_compatibility(
        {
            "field_name": "formula_use_authorized",
            "nodi_semantics": "authorization flag; must remain false",
            "comsol_semantics": "authorized=true",
            "conformance_status": "MATCH",
        }
    )
    assert rc3_bad["semantic_conformance_status"] == "BLOCKING_MISMATCH"


def test_no_auth_regression_preserves_gate2d_edge_qch_binding_states() -> None:
    ledger = read_csv_rows(OUT / "NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_20260628.csv")
    policy = read_csv_rows(OUT / "NODI_COMSOL_GATE2AD_POLICY_STATE_AUDIT_20260628.csv")
    drift = read_csv_rows(OUT / "NODI_COMSOL_GATE2AD_DOSSIER_AUTHORIZATION_DRIFT_SCAN_20260628.csv")

    assert len(ledger) == 4
    assert lib.validate_gate2d_accepted_ledger(ledger) == []
    observed = {row["policy"]: row["observed_state"] for row in policy}
    assert observed["EDGE"] == "NOT_APPROVED"
    assert observed["QCH"] == "NO_FORMAL_QCH_SIDECAR_PRESENT"
    assert observed["BINDING"] == "FAIL_CLOSED"
    assert all(row["drift_status"] == "PASS_NO_AUTHORIZATION" for row in drift)
