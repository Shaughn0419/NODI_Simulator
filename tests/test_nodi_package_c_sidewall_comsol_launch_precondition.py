from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_comsol_launch_precondition as builder,
)


def test_comsol_launch_precondition_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert "COMSOL Multiphysics" in summary["comsolbatch_version"]
    assert summary["precondition_rows"] == 5
    assert summary["context_rows"] == 4
    assert summary["claim_guard_rows"] == 6
    assert summary["toolchain_passed_rows"] == 1
    assert summary["launch_allowed_now_rows"] == 0
    assert summary["mph_load_allowed_now_rows"] == 0
    assert summary["target_model_bound_rows"] == 0
    assert summary["launch_command_hash_bound_rows"] == 0
    assert summary["claim_promotion_allowed_guard_rows"] == 0
    assert summary["stale_legacy_mirror_context_rows"] >= 1


def test_precondition_rows_require_target_model_before_launch() -> None:
    rows = builder.build_payload()["precondition_rows"]
    by_lane = {row["lane"]: row for row in rows}

    assert by_lane["toolchain_detection"]["precondition_passed"] is True
    assert by_lane["target_model_binding"]["precondition_passed"] is False
    assert by_lane["target_model_binding"]["target_mph_or_model_bound"] is False
    assert by_lane["launch_command_binding"]["launch_command_hash_bound"] is False
    assert {row["launch_allowed_now"] for row in rows} == {False}
    assert {row["mph_load_allowed_now"] for row in rows} == {False}
    assert {row["claim_boundary"] for row in rows} == {builder.CLAIM_BOUNDARY}


def test_context_rows_bind_toolchain_project_and_stale_mirror() -> None:
    rows = builder.build_payload()["context_rows"]
    by_kind = {row["context_kind"]: row for row in rows}

    assert by_kind["toolchain"]["context_status"] == "detected"
    assert by_kind["sibling_project"]["context_status"] == "detected"
    assert by_kind["legacy_mirror_request"]["context_status"] == "stale_for_current_head"
    assert by_kind["target_model_binding"]["context_status"] == (
        "missing_target_mph_or_solver_script"
    )


def test_claim_guards_do_not_promote_outputs() -> None:
    rows = builder.build_payload()["claim_guard_rows"]

    assert len(rows) == 6
    for row in rows:
        assert row["implementation_authorized"] is True
        assert row["claim_promoted_current"] is False
        assert row["claim_promotion_allowed_now"] is False
        assert row["required_evidence_before_true"]
        assert row["hard_fail_if_missing_evidence"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_comsol_launch_precondition_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_PRECONDITION_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CONTEXT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CLAIM_GUARD_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "558_NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_comsol_launch_precondition.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-comsol-launch-precondition is required" in result.stderr
