from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_package_c_proof_readiness_index as readiness


@lru_cache(maxsize=1)
def _payload() -> dict:
    return readiness.build_payload()


def test_readiness_index_payload_is_single_entrypoint_without_promotion() -> None:
    payload = _payload()
    failures = readiness.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == readiness.DISPOSITION
    assert summary["readiness_index_rows"] == 9
    assert summary["open_blocker_rows"] >= 4
    assert summary["external_research_question_rows"] >= 4
    assert summary["proof_readiness_index_status"] == (
        "single_entrypoint_ready_not_proof_registered"
    )
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_readiness_index_covers_current_package_c_artifacts() -> None:
    rows = _payload()["readiness_index"]
    roles = {row["artifact_role"] for row in rows}

    assert roles == {
        "metric_hardening_consolidation",
        "timeseries_ess_candidate",
        "stationarity_ensemble_refinement",
        "one_wall_wall_pileup_refinement",
        "near_boundary_expected_band_method",
        "substep_fail_policy_hardening",
        "substep_dt_refinement_requirements",
        "runtime_substep_policy_design",
        "proof_threshold_table",
    }
    by_role = {row["artifact_role"]: row for row in rows}
    assert "max_required_substeps=526" in by_role[
        "substep_dt_refinement_requirements"
    ]["key_values"]
    assert "prohibitive_rows=1" in by_role[
        "runtime_substep_policy_design"
    ]["key_values"]
    assert "runtime_policy_auth=missing_not_authorized" in by_role[
        "runtime_substep_policy_design"
    ]["key_values"]
    assert "min_independent_ess=32768.0" in by_role[
        "stationarity_ensemble_refinement"
    ]["key_values"]
    assert "max_one_wall_ks=" in by_role["one_wall_wall_pileup_refinement"]["key_values"]
    assert "max_wall_pileup_ratio=" in by_role[
        "one_wall_wall_pileup_refinement"
    ]["key_values"]
    assert "max_abs_z=" in by_role["near_boundary_expected_band_method"]["key_values"]
    assert "expected_band_rows=24" in by_role[
        "near_boundary_expected_band_method"
    ]["key_values"]
    assert "proof_gap_rows=0" in by_role["proof_threshold_table"]["key_values"]
    assert all(row["claim_boundary"] == readiness.CLAIM_BOUNDARY for row in rows)


def test_readiness_blockers_keep_fail_closed_next_actions() -> None:
    blockers = _payload()["blockers"]
    blocker_ids = {row["blocker_id"] for row in blockers}

    assert "manual_authorization_ledger_missing" in blocker_ids
    assert "clean_reviewed_commit_binding_pending" in blocker_ids
    assert "proof_threshold_gaps_present" not in blocker_ids
    assert "proof_method_gaps_present" not in blocker_ids
    assert "runtime_policy_gaps_present" in blocker_ids
    assert {row["blocker_status"] for row in blockers} == {"open_fail_closed"}


def test_readiness_external_questions_are_research_scoped() -> None:
    questions = _payload()["external_research_questions"]
    question_ids = {row["question_id"] for row in questions}

    assert "stationarity_ess_method" in question_ids
    assert "substep_runtime_cost" in question_ids
    assert "one_wall_wall_pileup_method_binding" in question_ids
    assert "near_boundary_expected_band_external_review" in question_ids
    assert all("no" in row["scope_guard"].lower() for row in questions)
    assert all(row["claim_boundary"] == readiness.CLAIM_BOUNDARY for row in questions)


def test_readiness_firewall_keeps_authorization_false() -> None:
    firewall = readiness.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_PROOF_READINESS_INDEX_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_readiness_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = readiness.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_INDEX_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_BLOCKERS_20260701.csv" in artifacts
    assert (
        "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_EXTERNAL_RESEARCH_QUESTIONS_20260701.csv"
        in artifacts
    )
    assert "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_STATUS_20260701.json" in artifacts
    assert "509_NODI_COMSOL_PACKAGE_C_PROOF_READINESS_INDEX_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact["NODI_COMSOL_PACKAGE_C_PROOF_READINESS_MANIFEST_20260701.csv"][
        "sha256"
    ] == readiness.SELF_MANIFEST_SHA256


def test_readiness_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        readiness,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}], "blockers": []},
    )
    monkeypatch.setattr(readiness, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(readiness, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_proof_readiness_index.py",
            "--confirm-package-c-proof-readiness-index",
        ],
    )

    assert readiness.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_PROOF_READINESS_INDEX" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_readiness_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-proof-readiness-index is required" in result.stderr
