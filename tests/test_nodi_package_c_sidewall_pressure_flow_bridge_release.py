from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_pressure_flow_bridge_release.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("pressure_flow_bridge_builder", BUILDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_request_rows_are_exact_w500_d900_bindings():
    builder = load_builder()
    rows = builder.read_csv_rows(builder.REQUEST_ROWS)
    failures = builder.validate_request_rows(rows)
    assert failures == []
    assert len(rows) == 2
    hashes = {row["source_geometry_hash"] for row in rows}
    assert "fc2b8074b0dc240816bf1d891822e3911f839ce691866b5022a2f04af416cb14" in hashes
    assert "033b6382b020bca2f984bd623ad4f2e4eff29417b8f8e36e8733ecef237065f2" in hashes


def test_receipt_schema_contains_required_authorization_and_hash_fields():
    builder = load_builder()
    fields = {row["field"] for row in builder.receipt_schema_rows()}
    for required in {
        "validation_request_id",
        "geometry_descriptor_sha256",
        "q_ratio_vs_candidate",
        "split_delta_abs",
        "result_hash",
        "provenance_hash",
        "execution_authorization_id",
    }:
        assert required in fields


def test_verdict_policy_never_promotes_to_formal_qch_or_route_score():
    builder = load_builder()
    rows = builder.verdict_policy_rows()
    assert {row["future_result_disposition"] for row in rows} >= {
        "REVIEW_PASS_NOT_FORMAL_QCH",
        "BLOCKED_UNAUTHORIZED_RUN",
        "BLOCKED_MISSING_AUTHORIZATION",
    }
    for row in rows:
        assert row["formal_qch_weighting_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["yield_current"] == "false"
        assert row["detection_probability_current"] == "false"


def test_mutation_suite_meets_required_scale_and_zero_promotions():
    builder = load_builder()
    rows = builder.mutation_rows()
    assert sum(int(row["row_equivalent_count"]) for row in rows) >= 750_000
    assert sum(int(row["observed_unexpected_pass"]) for row in rows) == 0
    assert sum(int(row["authorization_promotion"]) for row in rows) == 0
    assert sum(int(row["proof_promotion"]) for row in rows) == 0
    assert sum(int(row["formal_qch_promotion"]) for row in rows) == 0
    assert sum(int(row["route_score_promotion"]) for row in rows) == 0
    assert sum(int(row["yield_detection_promotion"]) for row in rows) == 0


def test_handoff_enums_are_no_run_or_future_authorization_only():
    builder = load_builder()
    enums = {row["expected_comsol_response_enum"] for row in builder.handoff_rows()}
    assert "RECEIPT_VALIDATE_NOW_NO_RUN" in enums
    assert "FUTURE_COMSOL_PRESSURE_FLOW_RUN_REQUIRED_NOT_AUTHORIZED" in enums
    assert "FUTURE_MPH_LOAD_REQUIRED_NOT_AUTHORIZED" in enums
    assert "DO_NOT_PROMOTE_TO_FORMAL_QCH" in enums


def test_build_outputs_passes_with_external_dirty_excluded():
    builder = load_builder()
    payload = builder.build_outputs()
    summary = payload["summary"]
    assert summary["disposition"] == builder.PASS_DISPOSITION
    assert summary["request_contract_rows"] == 2
    assert summary["release_scoped_dirty_blocker_rows"] == 0
    assert summary["source_lock_failures"] == 0
    assert summary["external_dirty_excluded"] is True
    assert summary["formal_qch_weighting_current"] is False
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["Gate2D_rows"] == 4
    assert summary["EDGE_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert summary["QCH_state"] == "CANDIDATE_ONLY_NOT_FORMAL_QCH_SIDECAR"
    assert summary["BINDING_state"] == "FAIL_CLOSED"
