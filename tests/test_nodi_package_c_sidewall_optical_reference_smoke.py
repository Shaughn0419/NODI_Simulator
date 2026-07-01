from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_optical_reference_smoke as builder


def test_sidewall_optical_reference_smoke_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_wet_optical_context_disposition"] == (
        "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_READY_NOT_FINAL"
    )
    assert summary["smoke_rows"] == 2
    assert summary["trapezoid_reference_not_propagated_rows"] == 1
    assert summary["rectangle_native_reference_rows"] == 1
    assert summary["optical_solver_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False


def test_sidewall_optical_reference_smoke_rows_have_reference_guards() -> None:
    rows = builder.build_payload()["smoke_rows"]
    by_case = {row["case_id"]: row for row in rows}

    rectangle = by_case["rectangle_limit_theta90_D900_W500"]
    trapezoid = by_case["taper_theta85_D900_W500"]

    assert rectangle["geometry_not_propagated_to_reference_field"] == "false"
    assert rectangle["reference_geometry_propagation_status"] == (
        "rectangle_native_or_non_sidewall_geometry"
    )
    assert trapezoid["geometry_not_propagated_to_reference_field"] == "true"
    assert trapezoid["reference_geometry_propagation_status"] == (
        "blocked_trapezoid_geometry_not_propagated_to_reference_field"
    )
    for row in rows:
        assert row["not_optical_solver_output"] == "true"
        assert row["optical_solver_current"] == "false"
        assert row["detection_probability_current"] == "false"
        assert row["yield_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["claim_boundary"] == builder.SIDEWALL_OPTICAL_REFERENCE_SMOKE_CLAIM_BOUNDARY


def test_sidewall_optical_reference_smoke_promotion_gaps_are_explicit() -> None:
    gaps = builder.promotion_gap_rows()
    targets = {row["target"] for row in gaps}

    assert "sidewall_optical_solver_output" in targets
    assert "detection_probability" in targets
    assert "true_W_eff" in targets
    for row in gaps:
        assert row["current_value"] == "false"
        assert row["hard_fail_if"]


def test_sidewall_optical_reference_smoke_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_SMOKE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_GAPS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "526_NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
