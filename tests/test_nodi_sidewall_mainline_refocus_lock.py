from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_mainline_refocus_lock as builder


def test_mainline_refocus_lock_builds_ready_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["mainline_axis_rows"] == 3
    assert summary["work_package_rows"] == 4
    assert summary["drift_guard_rows"] == 6
    assert summary["source_hint_rows"] >= 5
    assert summary["negative_context_rows"] >= 3
    assert summary["forbidden_field_rows"] >= 12
    assert summary["failed_alignment_check_rows"] == 0
    assert summary["source_missing_rows"] == 0
    assert summary["primary_mainline"] == (
        "sidewall_angle_effect_on_recommended_dimensions_selected_annulus_and_"
        "interference_enhancement"
    )
    assert summary["not_primary_mainline"] == "route_winner_or_scoreboard"


def test_mainline_axes_are_dimensions_annulus_and_interference() -> None:
    rows = {row["axis_name"]: row for row in builder.mainline_axis_rows()}

    assert set(rows) == {
        "dimension_recommendation_sensitivity",
        "selected_annulus_sidewall_remap",
        "interference_enhancement_sidewall_sensitivity",
    }
    assert "recommended NODI channel" in rows[
        "dimension_recommendation_sensitivity"
    ]["primary_question"]
    assert "selected annulus coordinate range" in rows[
        "selected_annulus_sidewall_remap"
    ]["primary_question"]
    assert "interference-enhancement proxy" in rows[
        "interference_enhancement_sidewall_sensitivity"
    ]["primary_question"]
    for row in rows.values():
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY
        assert "route_winner" not in row["axis_name"]


def test_work_packages_follow_refocused_axes_not_winner_route() -> None:
    rows = {row["package_id"]: row for row in builder.work_package_rows()}

    assert rows["SW-MAIN-001"]["package_name"] == (
        "dimension_recommendation_drift_matrix"
    )
    assert rows["SW-MAIN-002"]["package_name"] == (
        "selected_annulus_trapezoid_remap"
    )
    assert rows["SW-MAIN-003"]["package_name"] == (
        "interference_enhancement_response_sensitivity"
    )
    assert "does_not_emit_route_winner" in rows["SW-MAIN-001"]["hard_checks"]
    assert "formal_qch_transport_input_only" in rows["SW-MAIN-001"]["hard_checks"]
    assert "small_n_smoke_rows_context_only" in rows["SW-MAIN-002"]["hard_checks"]
    assert "does_not_reduce_to_detection_probability_only" in rows[
        "SW-MAIN-003"
    ]["hard_checks"]
    assert "trapezoid_effective_aperture_surrogate_not_true_W_eff" in rows[
        "SW-MAIN-003"
    ]["hard_checks"]


def test_drift_guards_demote_route_winner_and_experimental_waiting() -> None:
    rows = {row["guard_id"]: row for row in builder.drift_guard_rows()}

    assert rows["DRIFT-001"]["forbidden_primary_frame"] == "which_route_wins_or_loses"
    assert rows["DRIFT-001"]["replacement_frame"] == (
        "which_dimensions_annuli_and_response_maps_shift"
    )
    assert rows["DRIFT-002"]["forbidden_primary_frame"] == (
        "waiting_for_real_experimental_data"
    )
    assert rows["DRIFT-002"]["replacement_frame"] == (
        "extreme_simulation_from_NODI_COMSOL_assumptions"
    )
    assert rows["DRIFT-004"]["replacement_frame"] == (
        "rectangle_baseline_and_sidewall_geometry_coexist"
    )
    assert rows["DRIFT-005"]["replacement_frame"] == (
        "formal_qch_transport_input_only"
    )
    assert rows["DRIFT-006"]["replacement_frame"] == (
        "small_n_smoke_context_only_until_full_matrix"
    )


def test_alignment_checks_are_all_hard_pass() -> None:
    payload = builder.build_payload()
    rows = payload["alignment_check_rows"]

    assert rows
    assert all(row["check_pass"] is True for row in rows)
    assert all(row["hard_fail_if_false"] is True for row in rows)
    assert any(row["check_name"] == "route_winner_not_primary" for row in rows)
    assert any(row["check_name"] == "simulation_not_experimental_waiting" for row in rows)
    assert any(row["check_name"] == "qch_is_transport_input_only" for row in rows)
    assert any(row["check_name"] == "small_n_smoke_is_context_only" for row in rows)
    assert any(
        row["check_name"] == "source_hints_cover_annulus_response_and_ledger"
        for row in rows
    )
    assert any(
        row["check_name"] == "forbidden_fields_include_aliases" for row in rows
    )


def test_source_hints_register_annulus_response_and_ledger_inputs() -> None:
    rows = {row["source_hint_id"]: row for row in builder.source_hint_rows()}

    assert rows["SOURCE-HINT-001"]["preferred_axis"] == "AXIS-002"
    assert rows["SOURCE-HINT-001"]["source_role"] == (
        "selected_annulus_context_fields"
    )
    assert rows["SOURCE-HINT-002"]["use_limit"] == (
        "surrogate_only_not_true_W_eff_or_full_wave_solution"
    )
    assert rows["SOURCE-HINT-005"]["use_limit"] == (
        "consume_delta_lock_as_context_not_claim_unlock"
    )


def test_negative_context_sources_do_not_drive_mainline() -> None:
    rows = {row["negative_context_id"]: row for row in builder.negative_context_rows()}

    assert rows["NEGATIVE-CONTEXT-001"]["blocked_use"] == (
        "drive_dimension_annulus_or_interference_work"
    )
    assert rows["NEGATIVE-CONTEXT-002"]["allowed_use"] == (
        "reuse_dual_track_pattern_only"
    )
    assert rows["NEGATIVE-CONTEXT-003"]["blocked_use"] == (
        "promote_to_sidewall_detection_probability"
    )


def test_forbidden_field_aliases_are_registered() -> None:
    fields = {
        row["forbidden_field_or_alias"]: row["allowed_replacement"]
        for row in builder.forbidden_field_rows()
    }

    assert fields["winner"] == "use_delta_status_or_annulus_remap_status"
    assert fields["route_score_norm"] == "use_axis_specific_delta_fields"
    assert fields["rank_under_surrogate"] == (
        "use_sensitivity_sort_index_only_if_non_primary"
    )
    assert fields["sidewall_score_value"] == "use_sidewall_geometry_sensitivity_delta"


def test_mainline_refocus_lock_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_AXIS_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_WORK_PACKAGE_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_DRIFT_GUARD_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_SOURCE_HINT_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_NEGATIVE_CONTEXT_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_FORBIDDEN_FIELD_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260702.json" in names
    assert f"588_{builder.PREFIX}_20260702.md" in names


def test_mainline_refocus_lock_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_mainline_refocus_lock.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-mainline-refocus-lock is required" in (
        result.stderr + result.stdout
    )
