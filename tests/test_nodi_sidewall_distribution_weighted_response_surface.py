from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_sidewall_distribution_weighted_response_surface as builder,
)


def test_transport_bins_cover_220_and_300_without_exact_pxu_claim() -> None:
    rows = builder.transport_bin_rows()

    assert len(rows) == 8
    assert {int(row["source_particle_diameter_nm"]) for row in rows} == {220, 300}
    assert all(row["probability_grid_available"] is False for row in rows)
    assert all(row["not_exact_pxu_probability_grid"] is True for row in rows)
    assert all(
        row["edge4_exact_annulus_mapping_status"]
        == "not_exact_0p5_0p8_annulus_mapping"
        for row in rows
    )


def test_window_weights_show_comsol_flux_shifts_mass_inward() -> None:
    rows = builder.window_weight_rows()
    lookup = {
        (
            int(row["source_particle_diameter_nm"]),
            row["annulus_window_id"],
            row["weighting_mode"],
        ): float(row["window_probability_mass_surrogate"])
        for row in rows
    }

    assert lookup[(220, "0p4_0p7", "comsol_outlet_flux_fraction")] > lookup[
        (220, "0p5_0p8", "comsol_outlet_flux_fraction")
    ]
    assert lookup[(220, "0p5_0p8", "comsol_outlet_flux_fraction")] > lookup[
        (220, "0p6_0p9", "comsol_outlet_flux_fraction")
    ]
    assert lookup[(300, "0p4_0p7", "comsol_residence_fraction")] > lookup[
        (300, "0p5_0p8", "comsol_residence_fraction")
    ]
    assert abs(lookup[(220, "0p5_0p8", "uniform_edge_mass")] - 0.3) < 1e-12


def test_weighted_response_expands_603_events_by_three_weighting_modes() -> None:
    rows = builder.weighted_window_response_rows()

    assert len(rows) == 208 * len(builder.WEIGHTING_MODES)
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert all(row["decision_use_allowed"] is False for row in rows)


def test_route_synthesis_covers_six_routes_and_shows_annulus_activity() -> None:
    rows = builder.route_weighted_synthesis_rows()

    assert len(rows) == 6 * len(builder.WEIGHTING_MODES)
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert any(
        row["weighting_mode"] != "uniform_edge_mass"
        and row["annulus_context_after_weighting"]
        == "weighted_mass_context_shifts_from_canonical"
        for row in rows
    )
    assert all(row["dimension_context_after_weighting"].endswith("full_nodi_recompute_required") for row in rows)


def test_question_rows_preserve_user_mainline() -> None:
    route_rows = builder.route_weighted_synthesis_rows()
    rows = builder.question_result_rows(route_rows)

    assert {
        row["question_id"] for row in rows
    } == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    assert all(row["decision_use_allowed"] is False for row in rows)
    assert rows[0]["next_action"] == "607_full_nodi_recompute_over_distribution_weighted_queue"


def test_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["source_event_rows_603"] == 208
    assert summary["transport_bin_rows"] == 8
    assert summary["weighted_window_response_rows"] == 624
    assert summary["route_weighted_synthesis_rows"] == 18
    assert summary["exact_pxu_probability_grid_available_now"] is False
    assert summary["failed_validation_rows"] == 0


def test_weighted_response_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload()

    assert builder.no_forbidden_primary_columns(payload) is True


def test_weighted_response_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_WINDOW_WEIGHT_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_ROUTE_WEIGHTED_SYNTHESIS_ROWS_20260703.csv" in names
    assert f"606_{builder.PREFIX}_20260703.md" in names


def test_weighted_response_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_distribution_weighted_response_surface.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-distribution-weighted-response-surface is required" in (
        result.stderr + result.stdout
    )
