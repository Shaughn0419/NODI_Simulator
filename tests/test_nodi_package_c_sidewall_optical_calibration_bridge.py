from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_optical_calibration_bridge as builder


def test_sidewall_optical_calibration_bridge_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_reference_smoke_disposition"] == (
        "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_READY_NOT_OPTICAL_SOLVER"
    )
    assert summary["seed_rows"] == 4
    assert summary["readiness_rows"] == 6
    assert summary["synthetic_seed_rows"] == 4
    assert summary["calibrated_lookup_unlock_status"] == (
        "blocked_synthetic_fixture_not_experimental"
    )
    assert summary["true_W_eff_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False


def test_sidewall_optical_calibration_bridge_seed_rows_are_guarded() -> None:
    rows = builder.build_payload()["seed_rows"]

    assert len(rows) == 4
    assert {row["reference_model_source"] for row in rows} == {
        "trapezoid_effective_aperture_surrogate"
    }
    assert {row["calibration_data_role"] for row in rows} == {
        "synthetic_fixture_not_experimental"
    }
    theta85_404 = next(
        row
        for row in rows
        if row["case_id"] == "taper_theta85_D900_W500"
        and row["wavelength_nm"] == "404"
    )
    assert 0.0 < float(theta85_404["g_ref"]) < 1.0
    for row in rows:
        assert row["not_experimental_blank_channel_calibration"] == "true"
        assert row["not_full_wave_optical_solver"] == "true"
        assert row["not_true_W_eff"] == "true"
        assert row["not_detector_response_validation"] == "true"
        assert row["not_detection_probability"] == "true"


def test_sidewall_optical_calibration_bridge_readiness_rows_cover_claims() -> None:
    readiness = builder.build_payload()["readiness_rows"]
    lanes = {row["evidence_lane"] for row in readiness}
    targets = {row["target_claim"] for row in readiness}

    assert "blank_channel_reference_amplitude_phase" in lanes
    assert "detector_response_bridge" in lanes
    assert "blank_false_positive_trace" in lanes
    assert "wet_wall_interaction" in lanes
    assert "calibrated_or_full_wave_sidewall_optical_solver" in targets
    assert "detection_probability" in targets
    assert "yield" in targets
    assert "route_score_or_winner" in targets
    for row in readiness:
        assert row["target_claim_current"] == "false"
        assert row["hard_fail_if_promoted_without"]


def test_sidewall_optical_calibration_bridge_outputs_manifest(tmp_path: Path) -> None:
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
    assert builder.SEED_TABLE_NAME in names
    assert builder.SEED_MANIFEST_NAME in names
    assert f"{builder.PREFIX}_READINESS_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "529_NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
