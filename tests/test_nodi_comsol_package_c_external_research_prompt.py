from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_package_c_external_research_prompt as prompt


@lru_cache(maxsize=1)
def _payload() -> dict:
    return prompt.build_payload()


def test_external_research_prompt_payload_is_copyable_without_promotion() -> None:
    payload = _payload()
    failures = prompt.validate_payload(payload)
    summary = payload["summary"]
    markdown = payload["prompt_markdown"]

    assert failures == []
    assert summary["disposition"] == prompt.DISPOSITION
    assert summary["context_rows"] == prompt.EXPECTED_CONTEXT_ROWS
    assert summary["research_question_rows"] >= 4
    assert summary["blocker_rows"] >= 4
    assert summary["prompt_status"] == "copyable_external_research_prompt_ready"
    assert "github.com/Shaughn0419/NODI_Simulator" in markdown
    assert "Do not assume access to local Codex files" in markdown
    assert "Do not register Package C proof/pass" in markdown
    assert "Do not authorize runtime configuration" in markdown
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_external_research_context_rows_include_key_metrics() -> None:
    rows = _payload()["context_rows"]
    by_context = {row["context_id"]: row for row in rows}

    assert "entrypoint" in by_context
    assert "artifact_roles" in by_context
    assert by_context["substep_runtime_cost"]["context_value"] == "526"
    assert by_context["runtime_substep_policy_design"]["context_value"] == (
        "policy_design_bound_not_runtime_authorized"
    )
    assert "runtime remains unauthorized" in by_context[
        "runtime_substep_policy_design"
    ]["details"]
    assert "authorization_preflight" in by_context
    assert "ledger_status=missing_fail_closed" in by_context[
        "authorization_preflight"
    ]["context_value"]
    assert (
        float(by_context["one_wall_wall_pileup_refinement"]["context_value"])
        <= 0.01
    )
    assert "candidate-only" in by_context["one_wall_wall_pileup_refinement"]["details"]
    assert float(by_context["near_boundary_expected_band_method"]["context_value"]) <= 3.0
    assert "area(radius+band)" in by_context["near_boundary_expected_band_method"]["details"]
    assert all(row["claim_boundary"] == prompt.CLAIM_BOUNDARY for row in rows)


def test_external_research_questions_preserve_scope_guards() -> None:
    questions = _payload()["research_questions"]
    question_ids = {row["question_id"] for row in questions}

    assert "stationarity_ess_method" in question_ids
    assert "substep_runtime_cost" in question_ids
    assert all(row["scope_guard"] for row in questions)
    assert all(row["claim_boundary"] == prompt.CLAIM_BOUNDARY for row in questions)
    assert all(row["allowed_use"] == prompt.ALLOWED_USE for row in questions)
    assert all(row["blocked_use"] == prompt.BLOCKED_USE for row in questions)
    assert all(
        row["source_claim_boundary"]
        == "proof_readiness_index_candidate_not_package_c_proof_registered_not_runtime"
        for row in questions
    )


def test_external_research_firewall_keeps_authorization_false() -> None:
    firewall = prompt.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_external_research_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = prompt.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_CONTEXT_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_20260701.md" in artifacts
    assert "510_NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_20260701.md" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_STATUS_20260701.json" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact["NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_MANIFEST_20260701.csv"][
        "sha256"
    ] == prompt.SELF_MANIFEST_SHA256


def test_external_research_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        prompt,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}], "prompt_markdown": ""},
    )
    monkeypatch.setattr(prompt, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(prompt, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_external_research_prompt.py",
            "--confirm-package-c-external-research-prompt",
        ],
    )

    assert prompt.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_external_research_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_external_research_prompt.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-external-research-prompt is required" in result.stderr
