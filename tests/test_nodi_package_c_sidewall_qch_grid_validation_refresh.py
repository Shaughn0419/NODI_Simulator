from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_qch_grid_validation_refresh as builder


def test_sidewall_qch_grid_validation_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["grid_rows"] == 9
    assert summary["convergence_rows"] == 6
    assert summary["promotion_update_rows"] == 1
    assert summary["split_candidate_pass_rows"] == 6
    assert summary["max_split_fraction_abs_delta_vs_reference"] <= 0.01
    assert summary["absolute_q_review_rows"] >= 1
    assert summary["split_candidate_current"] is True
    assert summary["absolute_qch_calibration_current"] is False
    assert summary["formal_qch_weighting_current"] is False
    assert summary["route_score_current"] is False
    assert summary["yield_detection_probability_current"] is False


def test_sidewall_qch_grid_validation_rows_keep_exact_geometry_and_closed_control() -> None:
    payload = builder.build_payload()
    rows = payload["grid_rows"]

    assert {row["top_width_nm"] for row in rows} == {"500"}
    assert {row["depth_nm"] for row in rows} == {"900"}
    assert {
        (row["case_id"], row["grid_nx"], row["qch_grid_validation_status"])
        for row in rows
    } >= {
        ("rectangle_limit_theta90_D900_W500", "41", "grid_refinement_candidate_row"),
        ("taper_theta85_D900_W500", "41", "grid_refinement_candidate_row"),
        ("closed_theta70_D900_W500", "41", "blocked_source_geometry_closed"),
    }
    for row in rows:
        assert row["formal_qch_weighting_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["yield_detection_probability_current"] == "false"
        assert row["claim_boundary"] == builder.SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY


def test_sidewall_qch_grid_validation_promotion_update_is_qch_only() -> None:
    update = builder.build_payload()["promotion_update_rows"][0]

    assert update["target_ledger_lane"] == "flow_split_qch"
    assert update["new_context_status"] == (
        "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation"
    )
    assert update["target_claim_current"] == "false"
    assert "formal_qch_weighting" in update["blocked_promotion"]
    assert "route_score" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["hard_fail_if"] == (
        "grid_refined_split_candidate_promoted_to_formal_qch_or_route_score"
    )


def test_sidewall_qch_grid_validation_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_GRID_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CONVERGENCE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "533_NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
