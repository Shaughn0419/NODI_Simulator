from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_recommended_dimension_update_packet as builder


def test_route_diameter_update_rows_cover_primary_theta85_grid() -> None:
    rows = builder.route_diameter_update_rows()

    assert len(rows) == 78
    assert {row["sidewall_deg_comsol"] for row in rows} == {85.0}
    assert len({row["route_id_nodi"] for row in rows}) == 6
    assert len({row["diameter_nm"] for row in rows}) == 13
    assert all(row["route_id_role"] == "join_key_only_not_selection" for row in rows)


def test_route_diameter_update_rows_encode_dimension_annulus_response_actions() -> None:
    rows = builder.route_diameter_update_rows()

    assert any(
        row["dimension_update_action"] == "widen_or_shallow_for_particle_support"
        for row in rows
    )
    assert any(
        row["annulus_update_action"] == "filter_0p5_0p8_by_particle_center_support"
        for row in rows
    )
    assert any(
        row["interference_update_action"] == "bounded_event_context_shift_observed"
        for row in rows
    )
    assert all(row["not_selection_metric_claim"] is True for row in rows)


def test_route_summary_rows_do_not_select_a_route() -> None:
    update_rows = builder.route_diameter_update_rows()
    rows = builder.route_summary_rows(update_rows)

    assert len(rows) == 6
    assert all(row["route_summary_not_selection"] is True for row in rows)
    assert any(
        row["route_dimension_update_status"]
        == "tail_sensitive_dimension_update_required"
        for row in rows
    )


def test_dimension_update_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["route_diameter_update_rows"] == 78
    assert summary["route_summary_rows"] == 6
    assert summary["bounded_event_context_rows"] == 12
    assert summary["source_missing_rows"] == 0
    assert summary["failed_alignment_check_rows"] == 0


def test_dimension_update_packet_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload()
    forbidden_exact = {
        "winner",
        "route_score",
        "rank",
        "detection_probability",
        "yield",
        "W_eff",
        "q_ch_eta",
        "rank_under_surrogate",
        "not_route_score",
    }

    for table_name in ("route_diameter_update_rows", "route_summary_rows"):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_dimension_update_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_STATUS_20260702.json" in names
    assert f"{builder.PREFIX}_ROUTE_DIAMETER_UPDATE_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ROUTE_SUMMARY_ROWS_20260702.csv" in names
    assert f"594_{builder.PREFIX}_20260702.md" in names


def test_dimension_update_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_recommended_dimension_update_packet.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-recommended-dimension-update-packet is required" in (
        result.stderr + result.stdout
    )
