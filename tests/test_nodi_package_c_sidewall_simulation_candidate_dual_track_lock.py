from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_simulation_candidate_dual_track_lock as builder,
)


def test_dual_track_lock_builds_candidate_ready_final_locked_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["lock_rows"] == 4
    assert summary["candidate_ready_rows"] == 4
    assert summary["final_locked_false_rows"] == 4
    assert summary["final_current_total_rows"] == 0
    assert summary["route_score_candidate_ready_rows"] == 2
    assert summary["winner_jrc_candidate_ready_rows"] == 2
    assert summary["yield_detection_values_ready_rows"] == 2
    assert summary["wet_accepted_observation_rows_total"] == 28


def test_dual_track_lock_rows_keep_candidate_and_final_tracks_distinct() -> None:
    rows = {row["track_id"]: row for row in builder.build_payload()["lock_rows"]}

    assert set(rows) == {
        "wet_surface_observation",
        "route_score",
        "winner_jrc",
        "yield_detection_values",
    }
    assert all(row["candidate_ready"] is True for row in rows.values())
    assert all(row["final_locked_false"] is True for row in rows.values())
    assert all(int(row["final_current_rows"]) == 0 for row in rows.values())
    assert rows["route_score"]["simulation_candidate_rows"] == 2
    assert rows["winner_jrc"]["simulation_candidate_rows"] == 1


def test_dual_track_lock_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_LOCK_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert f"583_{builder.PREFIX}_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names


def test_dual_track_lock_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_simulation_candidate_dual_track_lock.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-simulation-candidate-dual-track-lock is required" in (
        result.stderr + result.stdout
    )
