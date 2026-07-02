from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_package_c_sidewall_simulation_release_envelope as builder


def test_simulation_release_envelope_builds_ready_candidate() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["envelope_rows"] == 2
    assert summary["simulation_release_candidate_rows"] == 1
    assert summary["simulation_fabrication_readiness_rows"] == 1
    assert summary["simulation_production_ingestion_candidate_rows"] == 1
    assert summary["actual_release_current_rows"] == 0
    assert summary["top_route_candidate_id"] == "ROUTE-CAND-001"
    assert summary["top_route_geometry_family"] == "ideal_rectangle"
    assert float(summary["top_route_score_value"]) > 0.8
    assert float(summary["top_yield_value"]) > 0.8
    assert float(summary["top_detection_probability_value"]) > 0.9
    assert float(summary["top_wet_pass_probability_value"]) > 0.9


def test_simulation_release_rows_keep_backup_and_actual_release_distinct() -> None:
    rows = {row["route_candidate_id"]: row for row in builder.build_payload()["envelope_rows"]}

    assert rows["ROUTE-CAND-001"]["simulation_release_candidate_current"] is True
    assert rows["ROUTE-CAND-001"]["simulation_release_label"] == (
        "SIMULATION_RELEASE_CANDIDATE"
    )
    assert rows["ROUTE-CAND-002"]["simulation_release_candidate_current"] is False
    assert rows["ROUTE-CAND-002"]["simulation_release_label"] == "SIMULATION_BACKUP_ROUTE"
    for row in rows.values():
        assert row["actual_fabrication_release_current"] is False
        assert row["actual_production_ingestion_current"] is False
        assert row["experimental_release_current"] is False


def test_simulation_release_envelope_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_ENVELOPE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert f"585_{builder.PREFIX}_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names


def test_simulation_release_envelope_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_simulation_release_envelope.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-simulation-release-envelope is required" in (
        result.stderr + result.stdout
    )
