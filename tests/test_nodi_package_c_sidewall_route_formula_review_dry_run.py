from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_package_c_sidewall_route_formula_review_dry_run as builder


def test_route_formula_review_dry_run_builds_current_blocked_component_rows() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert summary["disposition"] == builder.DISPOSITION
    assert summary["dry_run_rows"] == 2
    assert summary["route_formula_ready_for_claim_review_rows"] == 0
    assert summary["component_vector_ready_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0


def test_route_formula_review_dry_run_rows_hold_qch_components_only_currently() -> None:
    rows = builder.build_payload()["dry_run_rows"]

    assert {row["qch_component_ready"] for row in rows} == {True}
    assert {row["detector_component_ready"] for row in rows} == {False}
    assert {row["wet_component_ready"] for row in rows} == {False}
    assert {row["diagnostic_component_ready_count"] for row in rows} == {1}
    assert {row["route_formula_review_dry_run_status"] for row in rows} == {
        "blocked_until_detector_wet_evidence_accepted"
    }
    assert all(float(row["diagnostic_qch_component_value"]) > 0 for row in rows)
    assert all(row["route_score_current"] is False for row in rows)


def test_route_formula_review_dry_run_writes_outputs(tmp_path: Path) -> None:
    original_output = builder.OUTPUT_DIR
    original_report = builder.REPORT_DIR
    try:
        builder.OUTPUT_DIR = tmp_path
        builder.REPORT_DIR = tmp_path
        payload = builder.build_payload()
        outputs = builder.write_outputs(payload)
    finally:
        builder.OUTPUT_DIR = original_output
        builder.REPORT_DIR = original_report

    names = {path.name for path in outputs}
    assert f"{builder.PREFIX}_DRY_RUN_ROWS_20260701.csv" in names
    assert f"572_{builder.PREFIX}_20260701.md" in names


def test_route_formula_review_dry_run_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_route_formula_review_dry_run.py",
        ],
        cwd=builder.PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-route-formula-review-dry-run is required" in (
        result.stderr + result.stdout
    )
