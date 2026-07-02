from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_integrated_simulation_route_review as builder,
)


def test_integrated_simulation_route_review_builds_ready_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["review_rows"] == 2
    assert summary["simulation_ready_rows"] == 2
    assert summary["simulation_route_score_current_rows"] == 2
    assert summary["simulation_winner_current_rows"] == 1
    assert summary["simulation_JRC_current_rows"] == 2
    assert summary["simulation_yield_current_rows"] == 2
    assert summary["simulation_detection_probability_current_rows"] == 2
    assert summary["simulation_wet_pass_probability_current_rows"] == 2
    assert summary["top_route_candidate_id"] == "ROUTE-CAND-001"
    assert summary["top_route_geometry_family"] == "ideal_rectangle"
    assert summary["final_current_total_rows"] == 0


def test_integrated_review_rows_keep_simulation_current_separate_from_final() -> None:
    rows = {row["route_candidate_id"]: row for row in builder.build_payload()["review_rows"]}

    assert rows["ROUTE-CAND-001"]["simulation_winner_current"] is True
    assert rows["ROUTE-CAND-001"]["simulation_JRC_value"] == "SIMULATION_TOP_ROUTE"
    assert rows["ROUTE-CAND-002"]["simulation_winner_current"] is False
    assert rows["ROUTE-CAND-002"]["simulation_JRC_value"] == "SIMULATION_RANK_2"
    for row in rows.values():
        assert row["simulation_route_score_current"] is True
        assert row["simulation_yield_current"] is True
        assert row["simulation_detection_probability_current"] is True
        assert row["simulation_wet_pass_probability_current"] is True
        assert row["route_score_current"] is False
        assert row["winner_current"] is False
        assert row["JRC_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False
        assert row["wet_pass_probability_current"] is False
        assert row["production_ingestion_current"] is False


def test_integrated_review_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_REVIEW_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert f"584_{builder.PREFIX}_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names


def test_integrated_review_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_integrated_simulation_route_review.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-integrated-simulation-route-review is required" in (
        result.stderr + result.stdout
    )
