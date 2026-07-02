from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_sidewall_comsol_cross_section_distribution_bridge as builder,
)


def test_bridge_marks_604_as_not_comsol_probability_weighted() -> None:
    rows = builder.route_distribution_binding_rows()

    assert len(rows) == 6
    assert all(
        row["current_604_probability_weighting_status"]
        == "not_comsol_cross_section_probability_weighted"
        for row in rows
    )
    assert all(row["full_nodi_recompute_required_after_trapezoid_geometry"] is True for row in rows)
    assert all(row["preserve_rectangle_baseline"] is True for row in rows)


def test_comsol_source_inventory_does_not_promote_descriptors_to_exact_pxu() -> None:
    rows = builder.comsol_source_inventory_rows()

    assert len(rows) == 4
    assert all(row["exists"] is True for row in rows)
    assert all(row["exact_pxu_grid_accepted_now"] is False for row in rows)
    assert all(row["probability_grid_available"] is False for row in rows)
    assert all(row["decision_use_allowed"] is False for row in rows)
    assert any(row["has_edge_norm_transport_bins"] is True for row in rows)
    assert any(row["has_near_wall_shell_volume_fraction"] is True for row in rows)
    assert any(row["has_targeted_field_descriptor"] is True for row in rows)
    assert all("x_nm" in row["missing_exact_probability_grid_columns_json"] for row in rows)


def test_distribution_models_keep_rectangle_trapezoid_and_comsol_axes_separate() -> None:
    rows = builder.distribution_model_rows()

    assert {
        row["distribution_basis_id"] for row in rows
    } == {
        "rectangle_uniform_accessible_baseline_v1",
        "trapezoid_uniform_accessible_surrogate_v1",
        "trapezoid_comsol_v4_transport_bin_reweighted_surrogate_v1",
        "comsol_v4_cross_section_probability_grid_exact_required_v1",
    }
    exact_rows = [
        row
        for row in rows
        if row["distribution_basis_id"]
        == "comsol_v4_cross_section_probability_grid_exact_required_v1"
    ]
    assert exact_rows[0]["feeds_full_nodi_recompute"] is False
    assert exact_rows[0]["exact_comsol_probability_grid_required"] is True
    assert exact_rows[0]["mapping_status"] == (
        "requires_exact_pxu_or_edge20_or_explicit_0p8_split"
    )
    assert all(row["decision_use_allowed"] is False for row in rows)
    assert {
        row["angle_geometry_alignment"] for row in rows
    } == {
        "rectangle_baseline_90deg_comsol_0deg_nodi_taper",
        "trapezoid_sidewall_85deg_comsol_5deg_nodi_taper",
    }


def test_recompute_queue_has_four_phases_per_route() -> None:
    route_rows = builder.route_distribution_binding_rows()
    queue_rows = builder.recompute_queue_rows(route_rows)

    assert len(queue_rows) == 24
    assert all(row["decision_use_allowed"] is False for row in queue_rows)
    assert all(row["selection_status"] == "queued_context_not_route_selection" for row in queue_rows)
    for route in route_rows:
        phases = {
            row["phase_id"]
            for row in queue_rows
            if row["source_route_id_nodi"] == route["source_route_id_nodi"]
        }
        assert phases == {
            "rectangle_baseline_relock",
            "trapezoid_uniform_accessible_recompute",
            "trapezoid_comsol_transport_bin_reweighted",
            "trapezoid_exact_comsol_pxu_pending",
        }


def test_edge4_context_requires_edge20_or_explicit_split_for_exact_annulus() -> None:
    inventory = builder.comsol_source_inventory_rows()
    edge_sources = [row for row in inventory if row["has_edge_norm_transport_bins"] is True]

    assert edge_sources
    assert all(
        row["edge4_exact_annulus_mapping_status"]
        == "not_exact_0p5_0p8_annulus_mapping"
        for row in edge_sources
    )
    assert all(
        row["edge20_or_0p8_split_required_for_exact_annulus"] is True
        for row in edge_sources
    )


def test_question_impacts_cover_user_mainline() -> None:
    route_rows = builder.route_distribution_binding_rows()
    rows = builder.question_impact_rows(route_rows)

    assert {
        row["question_id"] for row in rows
    } == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    assert all("604" in row["comsol_distribution_gap"] for row in rows)


def test_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["route_rows_604"] == 6
    assert summary["followup_event_rows_603"] == 208
    assert summary["route_distribution_binding_rows"] == 6
    assert summary["recompute_queue_rows"] == 24
    assert summary["current_604_comsol_cross_section_probability_weighted"] is False
    assert summary["exact_comsol_cross_section_probability_grid_available_now"] is False
    assert summary["failed_validation_rows"] == 0


def test_bridge_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload()

    assert builder.no_forbidden_primary_columns(payload) is True


def test_bridge_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_STATUS_20260703.json" in names
    assert f"{builder.PREFIX}_COMSOL_SOURCE_INVENTORY_20260703.csv" in names
    assert f"{builder.PREFIX}_DISTRIBUTION_MODEL_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_RECOMPUTE_QUEUE_ROWS_20260703.csv" in names
    assert f"605_{builder.PREFIX}_20260703.md" in names


def test_bridge_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_comsol_cross_section_distribution_bridge.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-comsol-cross-section-distribution-bridge is required" in (
        result.stderr + result.stdout
    )
