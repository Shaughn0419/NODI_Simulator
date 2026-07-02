from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_integrated_promotion_ledger_wet_observation_refresh as builder,
)


def test_integrated_promotion_ledger_wet_observation_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["refreshed_promotion_lane_rows"] == 18
    assert summary["wet_observation_delta_rows"] == 2
    assert summary["formal_qch_lane_rows_retained"] == 2
    assert summary["pressure_flow_validation_rows_retained"] == 2
    assert summary["expanded_selected_annulus_panel_rows_retained"] == 2
    assert summary["nearest_blank_guard_bound_rows_retained"] == 2
    assert summary["detector_response_panel_candidate_rows_retained"] == 2
    assert summary["wet_observation_intake_rows"] == 2
    assert summary["wet_pass_probability_current"] is False
    assert summary["clogging_rate_current"] is False
    assert summary["time_to_clog_current"] is False
    assert summary["recovery_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False


def test_wet_observation_refresh_updates_only_wet_lane() -> None:
    rows = builder.build_payload()["refreshed_promotion_lane_rows"]

    wet_rows = [row for row in rows if row["evidence_lane"] == "wet_wall_interaction"]
    assert len(wet_rows) == 2
    assert {row["current_status"] for row in wet_rows} == {
        "wet_surface_observation_intake_ready_no_observations"
    }
    assert all(
        row["source_disposition"]
        == "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_READY_SCHEMA_NO_OBSERVATIONS"
        for row in wet_rows
    )
    assert all(
        row["source_artifact"].endswith(
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_ROUTE_OBSERVATION_MATRIX_ROWS_20260701.csv"
        )
        for row in wet_rows
    )
    assert all(row["target_claim_current"] == "false" for row in wet_rows)
    assert all(row["not_yield"] == "true" for row in wet_rows)
    assert all(row["not_detection_probability"] == "true" for row in wet_rows)


def test_wet_observation_refresh_retains_upstream_progress() -> None:
    rows = builder.build_payload()["refreshed_promotion_lane_rows"]

    retained = {
        "flow_split_qch": "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting",
        "pressure_flow_validation": (
            "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
        ),
        "selected_annulus_detection_context": (
            "expanded_selected_annulus_panel_available_not_probability"
        ),
        "blank_false_positive_trace": (
            "nearest_blank_guard_bound_to_panel_not_sidewall_specific"
        ),
        "detector_response_bridge": (
            "detector_response_panel_candidate_not_sidewall_calibrated"
        ),
    }
    for lane, status in retained.items():
        assert {row["current_status"] for row in rows if row["evidence_lane"] == lane} == {
            status
        }


def test_wet_observation_delta_rows_keep_claims_false() -> None:
    deltas = builder.build_payload()["refresh_delta_rows"]

    assert len(deltas) == 2
    assert {delta["evidence_lane"] for delta in deltas} == {"wet_wall_interaction"}
    for delta in deltas:
        assert delta["target_claim_current"] == "false"
        assert "wet_pass_probability" in delta["blocked_use"]
        assert "clogging_rate" in delta["blocked_use"]
        assert "time_to_clog" in delta["blocked_use"]
        assert "recovery" in delta["blocked_use"]
        assert "detection_probability" in delta["blocked_use"]
        assert "route_score" in delta["blocked_use"]
        assert "yield" in delta["blocked_use"]
        assert delta["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_wet_observation_refresh_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_PROMOTION_LANE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_DELTA_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "544_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_OBSERVATION_REFRESH_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
