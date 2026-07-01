from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_reference_surrogate_candidate as builder,
)


def test_sidewall_reference_surrogate_candidate_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_optical_smoke_disposition"] == (
        "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_READY_NOT_OPTICAL_SOLVER"
    )
    assert summary["surrogate_rows"] == 4
    assert 0.0 < summary["theta85_404_effective_aperture_factor"] < 1.0
    assert summary["full_wave_or_calibrated_optical_solver_current"] is False
    assert summary["true_W_eff_current"] is False
    assert summary["detection_probability_current"] is False


def test_sidewall_reference_surrogate_rows_propagate_geometry_but_not_final_claims() -> None:
    rows = builder.build_payload()["surrogate_rows"]

    assert rows
    for row in rows:
        assert row["reference_model"] == "trapezoid_effective_aperture_surrogate"
        assert row["geometry_not_propagated_to_reference_field"] == "false"
        assert row["not_optical_solver_output"] == "true"
        assert row["optical_solver_current"] == "false"
        assert row["true_W_eff_current"] == "false"
        assert row["detection_probability_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["claim_boundary"] == builder.SIDEWALL_REFERENCE_SURROGATE_CLAIM_BOUNDARY

    theta85_404 = [
        row
        for row in rows
        if row["case_id"] == "taper_theta85_D900_W500"
        and row["wavelength_nm"] == "404"
    ][0]
    assert theta85_404["reference_geometry_propagation_status"] == (
        "trapezoid_geometry_propagated_to_effective_aperture_reference_surrogate"
    )
    assert float(theta85_404["trapezoid_effective_aperture_factor"]) < 1.0


def test_sidewall_reference_surrogate_promotion_gaps_are_explicit() -> None:
    gaps = builder.promotion_gap_rows()
    targets = {row["target"] for row in gaps}

    assert "full_wave_or_calibrated_sidewall_optical_solver" in targets
    assert "true_W_eff" in targets
    assert "detection_probability" in targets
    for row in gaps:
        assert row["current_value"] == "false"
        assert row["hard_fail_if"]


def test_sidewall_reference_surrogate_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_SURROGATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_GAPS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "527_NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
