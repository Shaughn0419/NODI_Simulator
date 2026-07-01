from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_reference_surrogate_smoke as builder


def test_sidewall_reference_surrogate_smoke_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_reference_surrogate_disposition"] == (
        "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_READY_NOT_OPTICAL_SOLVER"
    )
    assert summary["smoke_rows"] == 8
    assert summary["comparison_rows"] == 4
    assert summary["theta85_legacy_reference_not_propagated_rows"] == 2
    assert summary["theta85_sidewall_reference_propagated_rows"] == 2
    assert 0.0 < summary["theta85_404_effective_aperture_factor"] < 1.0
    assert summary["optical_solver_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False


def test_sidewall_reference_surrogate_smoke_rows_capture_reference_propagation() -> None:
    rows = builder.build_payload()["smoke_rows"]
    by_key = {
        (row["case_id"], row["reference_model"], row["wavelength_nm"]): row
        for row in rows
    }

    legacy = by_key[
        ("taper_theta85_D900_W500", "channel_angular_surrogate", "404")
    ]
    sidewall = by_key[
        (
            "taper_theta85_D900_W500",
            "trapezoid_effective_aperture_surrogate",
            "404",
        )
    ]

    assert legacy["geometry_not_propagated_to_reference_field"] == "true"
    assert legacy["reference_geometry_propagation_status"] == (
        "blocked_trapezoid_geometry_not_propagated_to_reference_field"
    )
    assert sidewall["geometry_not_propagated_to_reference_field"] == "false"
    assert sidewall["reference_geometry_propagation_status"] == (
        "trapezoid_geometry_propagated_to_effective_aperture_reference_surrogate"
    )
    assert sidewall["reference_solver_status"] == (
        "trapezoid_effective_aperture_surrogate_active"
    )
    assert float(sidewall["trapezoid_effective_aperture_factor"]) < 1.0
    for row in rows:
        assert row["not_optical_solver_output"] == "true"
        assert row["true_W_eff_current"] == "false"
        assert row["detection_probability_current"] == "false"
        assert row["route_score_current"] == "false"


def test_sidewall_reference_surrogate_smoke_comparisons_are_context_only() -> None:
    payload = builder.build_payload()
    comparisons = payload["comparison_rows"]
    assert len(comparisons) == 4
    theta85_404 = next(
        row
        for row in comparisons
        if row["case_id"] == "taper_theta85_D900_W500"
        and row["wavelength_nm"] == "404"
    )

    assert theta85_404["legacy_geometry_not_propagated_to_reference_field"] == "true"
    assert theta85_404["sidewall_geometry_not_propagated_to_reference_field"] == "false"
    assert theta85_404["delta_interpretation"] == (
        "small_n_synthetic_context_not_detection_probability"
    )
    assert theta85_404["claim_boundary"] == (
        builder.SIDEWALL_REFERENCE_SURROGATE_SMOKE_CLAIM_BOUNDARY
    )


def test_sidewall_reference_surrogate_smoke_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_COMPARISON_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_GAPS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "528_NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
