from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_pressure_flow_validation_context as builder


def test_pressure_flow_validation_context_packet_builds_without_formal_qch() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_qch_sidecar_disposition"] == (
        "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_READY_NOT_ROUTE"
    )
    assert summary["comsol_context_rows"] == 1
    assert summary["comparison_rows"] >= 2
    assert summary["formal_validation_candidate_rows"] == 0
    assert summary["formal_gate2_qch_sidecar_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_detection_probability_current"] is False
    assert summary["comsol_launch_started"] is False
    assert summary["mph_load_started"] is False


def test_pressure_flow_context_rows_are_source_locked_and_context_only() -> None:
    payload = builder.build_payload()
    context = payload["comsol_context"]
    comparisons = payload["comparison_rows"]

    assert context[0]["source_match_level"] == "geometry_family_context_only"
    assert context[0]["quality_gate"] == "pass"
    assert len(context[0]["source_sha256"]) == 64
    for row in comparisons:
        assert row["validation_status"] == "context_only_not_formal_validation"
        assert row["formal_qch_sidecar_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["yield_detection_probability_current"] == "false"
        assert row["claim_boundary"] == builder.PRESSURE_FLOW_CONTEXT_CLAIM_BOUNDARY


def test_pressure_flow_promotion_blockers_keep_exact_validation_path() -> None:
    blockers = builder.promotion_blockers()
    targets = {row["promotion_target"] for row in blockers}

    assert "formal_gate2_qch_sidecar" in targets
    assert "route_score" in targets
    assert "winner_or_JRC" in targets
    assert "yield_detection_probability" in targets
    for row in blockers:
        assert row["implementation_authorized"] == "true"
        assert row["current_value"] == "false"
        assert row["context_evidence_available"] == "true"
        assert row["hard_fail_if"].endswith("_true_from_context_only_comparison")


def test_pressure_flow_validation_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload()
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    try:
        builder.OUTPUT_DIR = tmp_path / "joint"
        builder.REPORT_DIR = tmp_path / "reports"
        paths = builder.write_outputs(payload)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir

    names = {path.name for path in paths}
    assert f"{builder.PREFIX}_COMSOL_CONTEXT_20260701.csv" in names
    assert f"{builder.PREFIX}_COMPARISON_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_BLOCKERS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "523_NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
