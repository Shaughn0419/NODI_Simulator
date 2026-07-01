from __future__ import annotations

from functools import lru_cache
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_package_c_post_proof_delta_release as release


@lru_cache(maxsize=1)
def _payload() -> dict:
    return release.build_payload()


def test_post_proof_release_passes_with_registered_finite_step_scope() -> None:
    payload = _payload()
    failures = release.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == release.DISPOSITION
    assert summary["proof_registration_authorized"] is True
    assert summary["package_c_proof_artifact_registered"] is True
    assert summary["package_c_validation_status_pass_current"] is True
    assert (
        summary["package_c_validation_status_pass_scope"]
        == "finite_step_reflection_surrogate_evidence_only"
    )
    assert summary["runtime_guard_policy_version"] == "trapezoid_runtime_substep_guard_v1"
    assert summary["release_scoped_dirty_blocker_rows"] == 0


def test_post_proof_release_keeps_all_no_run_and_no_solver_guards_false() -> None:
    summary = _payload()["summary"]

    for key in [
        "runtime_allowed",
        "runtime_execution_started",
        "nodi_runtime_recomputation_started",
        "numeric_prs_eas_allowed",
        "sidewall_prs_eas_numeric_output_current",
        "comsol_launch_allowed",
        "comsol_launch_started",
        "mph_load_allowed",
        "mph_load_started",
        "validated_brownian_solver_output_current",
        "validated_hindered_diffusion_claim_current",
        "trapezoid_flow_solver_output_current",
        "electrokinetic_solver_output_current",
        "optical_solver_output_current",
        "wet_claim_current",
        "route_yield_detection_claim_current",
        "fabrication_or_production_release_current",
    ]:
        assert summary[key] is False


def test_post_proof_guards_are_machine_scannable_hard_fails() -> None:
    rows = _payload()["post_proof_guards"]
    fields = {row["guard_field"] for row in rows}

    assert len(rows) >= 17
    assert {
        "numeric_prs_eas_allowed",
        "sidewall_prs_eas_numeric_output_current",
        "comsol_launch_allowed",
        "comsol_launch_started",
        "mph_load_allowed",
        "mph_load_started",
    } <= fields
    assert {row["guard_value"] for row in rows} == {"false"}
    assert all(row["hard_fail_if"].endswith("_true_in_post_proof_delta_release") for row in rows)


def test_comsol_mirror_request_is_post_proof_no_run_only() -> None:
    rows = _payload()["comsol_request"]
    enums = {row["expected_comsol_response_enum"] for row in rows}

    assert "MIRROR_PROOF_REGISTERED_FINITE_STEP_SURROGATE_ONLY" in enums
    assert "MIRROR_RUNTIME_GUARD_NO_RUN" in enums
    assert "FUTURE_COMSOL_RUN_REQUIRED_NOT_STARTED" in enums
    assert "FUTURE_MPH_LOAD_REQUIRED_NOT_STARTED" in enums
    assert "FUTURE_SOLVER_WET_BRANCH_REQUIRED_NOT_STARTED" in enums
    assert "BLOCKED_AS_EXPECTED" in enums
    assert {row["allowed_action"] for row in rows} == {
        "clean_mirror_no_run_no_mph_no_numeric_output"
    }
    assert all("COMSOL launch" in row["forbidden_action"] for row in rows)


def test_stale_post_rc2_files_are_recorded_but_excluded_from_source_lock() -> None:
    payload = _payload()
    stale_rows = payload["superseded_context"]
    source_paths = {row["path"] for row in payload["source_lock"]}

    assert {row["path"] for row in stale_rows} == release.STALE_POST_RC2_PATHS
    assert all(row["release_decision"] == "excluded_from_post_proof_release_source_lock" for row in stale_rows)
    assert all(row["path"] not in source_paths for row in stale_rows)
    assert payload["summary"]["dirty_count_after_exclusions"] == 0


def test_non_release_dirty_context_does_not_block_release_scope() -> None:
    payload = _payload()
    rows = payload["dirty_context"]

    assert payload["summary"]["release_scoped_dirty_blocker_rows"] == 0
    assert all(
        row["classification"] != "release_scoped_dirty_blocker"
        for row in rows
        if row["release_decision"] != "blocks_post_proof_release"
    )


def test_written_outputs_manifest_contains_post_proof_release_files(tmp_path) -> None:
    payload = _payload()
    outputs = release.write_outputs(
        payload,
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    artifacts = {path.name for path in outputs}

    assert "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_STATUS_20260701.json" in artifacts
    assert "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_RELEASE_SEAL_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_POST_PROOF_GUARDS_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_DIRTY_CONTEXT_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_SUPERSEDED_CONTEXT_20260701.csv" in artifacts
    assert "518_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_20260701.md" in artifacts
    assert "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_MANIFEST_20260701.csv" in artifacts

    manifest_rows = read_csv_rows(
        tmp_path
        / "joint_interface"
        / "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_MANIFEST_20260701.csv"
    )
    by_artifact = {row["artifact"]: row for row in manifest_rows}
    assert by_artifact[
        "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_MANIFEST_20260701.csv"
    ]["sha256"] == release.SELF_MANIFEST_SHA256


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_post_proof_delta_release.py",
        ],
        cwd=release.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-post-proof-delta-release is required" in result.stderr
