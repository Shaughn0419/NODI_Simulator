from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_package_c_sidewall_route_accepted_evidence_smoke as builder


def test_route_accepted_evidence_smoke_builds_fixture_path_pass() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert summary["disposition"] == builder.DISPOSITION
    assert summary["detector_fixture_rows"] == 2
    assert summary["wet_fixture_rows"] == 14
    assert summary["smoke_rows"] == 2
    assert summary["fixture_path_pass_rows"] == 2
    assert summary["route_formula_ready_for_claim_review_rows"] == 2
    assert summary["component_vector_ready_rows"] == 2
    assert summary["fixture_not_evidence_rows"] == 2
    assert summary["route_score_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0


def test_route_accepted_evidence_smoke_rows_are_not_claims() -> None:
    rows = builder.build_payload()["smoke_rows"]

    assert {row["fixture_not_evidence"] for row in rows} == {True}
    assert {row["smoke_status"] for row in rows} == {
        "fixture_path_passes_chain_to_component_vector_not_evidence"
    }
    assert {row["route_score_current"] for row in rows} == {False}
    assert {row["winner_current"] for row in rows} == {False}
    assert {row["yield_current"] for row in rows} == {False}
    assert {row["detection_probability_current"] for row in rows} == {False}


def test_route_accepted_evidence_smoke_writes_outputs(tmp_path: Path) -> None:
    old_output = builder.OUTPUT_DIR
    old_report = builder.REPORT_DIR
    try:
        builder.OUTPUT_DIR = tmp_path
        builder.REPORT_DIR = tmp_path
        payload = builder.build_payload()
        outputs = builder.write_outputs(payload)
    finally:
        builder.OUTPUT_DIR = old_output
        builder.REPORT_DIR = old_report

    names = {path.name for path in outputs}
    assert f"{builder.PREFIX}_SMOKE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_DETECTOR_FIXTURE_ROWS_NOT_EVIDENCE_20260701.csv" in names
    assert f"{builder.PREFIX}_WET_FIXTURE_ROWS_NOT_EVIDENCE_20260701.csv" in names
    assert f"573_{builder.PREFIX}_20260701.md" in names


def test_route_accepted_evidence_smoke_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_route_accepted_evidence_smoke.py",
        ],
        cwd=builder.PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-route-accepted-evidence-smoke is required" in (
        result.stderr + result.stdout
    )
