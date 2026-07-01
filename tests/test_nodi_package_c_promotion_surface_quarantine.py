from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = PROJECT_ROOT / "tools/audits/build_nodi_package_c_promotion_surface_quarantine.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("promotion_quarantine_builder", BUILDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_promotion_surface_scanner_flags_registered_proof_context():
    builder = load_builder()
    proof_status = (
        PROJECT_ROOT
        / "reports/joint_interface_20260701/NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_STATUS_20260701.json"
    )
    assert proof_status.exists()
    rows = builder.census_rows([proof_status])
    assert any(row["matched_token"] == "proof_registration_authorized" for row in rows)
    assert any(row["risk_level"] == "P0" for row in rows)


def test_commit_semantic_audit_marks_promotion_commits():
    builder = load_builder()
    rows = builder.commit_semantic_rows(
        [
            "c3b2a0d Add Package C authorized mainline advancement",
            "022f75c Add Package C qch sidecar candidate",
            "0eba815 Add Package C external research prompt",
        ]
    )
    classes = {row["semantic_classification"] for row in rows}
    assert "FORBIDDEN_PROMOTION_IF_CONSUMED" in classes
    assert "QUARANTINE_REQUIRED_POSITIVE_CLAIM_SURFACE" in classes
    assert "CONTEXT_ONLY_CANDIDATE" in classes


def test_release_seal_keeps_all_promotion_flags_false():
    builder = load_builder()
    row = builder.release_seal_rows(builder.PARTIAL_DISPOSITION, "HEAD", 1, 2, 3)[0]
    for key in (
        "proof_registration_authorized",
        "package_c_validation_status_pass_authorized",
        "runtime",
        "production",
        "numeric_prs_eas",
        "comsol_launch",
        "mph_load",
        "qch_weighting_authorized",
        "jrc_authorized",
        "yield_authorized",
        "detection_probability_authorized",
    ):
        assert row[key] == "false"


def test_mutation_suite_meets_required_scale_and_zero_promotions():
    builder = load_builder()
    rows = builder.mutation_rows()
    assert sum(int(row["row_equivalent_count"]) for row in rows) >= 500_000
    assert sum(int(row["observed_unexpected_pass"]) for row in rows) == 0
    assert sum(int(row["authorization_promotion"]) for row in rows) == 0
    assert sum(int(row["proof_promotion"]) for row in rows) == 0
    assert sum(int(row["execution_promotion"]) for row in rows) == 0
    assert sum(int(row["formal_qch_promotion"]) for row in rows) == 0


def test_comsol_request_forbids_run_and_positive_claim_consumption():
    builder = load_builder()
    rows = builder.comsol_request_rows()
    enums = {row["expected_comsol_response_enum"] for row in rows}
    assert "MIRROR_QUARANTINE_NOW_NO_RUN" in enums
    assert "DO_NOT_CONSUME_POSITIVE_CLAIM" in enums
    assert "FUTURE_COMSOL_RUN_REQUIRED_NOT_AUTHORIZED" in enums
    assert all("COMSOL run" in row["forbidden_comsol_action"] for row in rows)


def test_build_outputs_is_fail_closed_when_positive_claims_remain():
    builder = load_builder()
    payload = builder.build_outputs()
    summary = payload["summary"]
    assert summary["disposition"] == builder.PARTIAL_DISPOSITION
    assert summary["p0_positive_claim_surface_count"] > 0
    assert summary["unresolved_positive_claim_count"] > 0
    assert summary["post_rc2_release_v2_recovered"] is False
    assert summary["Gate2D_rows"] == 4
    assert summary["EDGE_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert summary["BINDING_state"] == "FAIL_CLOSED"
