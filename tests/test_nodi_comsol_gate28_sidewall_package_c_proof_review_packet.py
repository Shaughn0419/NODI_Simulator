from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_comsol_gate28_sidewall_package_c_proof_review_packet as gate28


def test_gate28_payload_is_review_packet_without_proof_registration() -> None:
    payload = gate28.build_payload(execute_tests=False)
    failures = gate28.validate_payload(payload, require_evidence_pass=False)

    assert failures == []
    assert payload["summary"]["disposition"] == gate28.DISPOSITION
    assert payload["summary"]["gate27_disposition"] == gate28.EXPECTED_GATE27_DISPOSITION
    assert payload["summary"]["gate27_no_auth"] is True
    assert payload["summary"]["gate27_review_only"] is True
    assert payload["summary"]["gate27_proof_contract_rows"] == len(
        gate28.GATE27_REQUIRED_PROOF_CONTRACT_FIELDS
    )
    assert set(payload["gate27_proof_contract_fields"]) == (
        gate28.GATE27_REQUIRED_PROOF_CONTRACT_FIELDS
    )
    assert payload["summary"]["gate27_proof_contract_missing_required_fields"] == []
    assert payload["summary"]["gate27_proof_contract_extra_fields"] == []
    assert payload["summary"]["gate27_proof_artifact_registered_rows"] == 0
    assert payload["summary"]["gate27_can_update_proof_registry_rows"] == 0
    assert payload["summary"]["proof_registration_authorized"] is False
    assert payload["summary"]["runtime_allowed"] is False
    assert payload["summary"]["numeric_prs_eas_allowed"] is False
    assert payload["summary"]["comsol_launch_allowed"] is False
    assert payload["summary"]["mph_load_allowed"] is False


def test_gate28_firewall_keeps_all_authorization_flags_false() -> None:
    payload = gate28.build_payload(execute_tests=False)
    firewall = payload["no_proof_firewall"][0]

    assert firewall["firewall_status"] == "PASS_GATE28_REVIEW_PACKET_NO_PROOF_REGISTRATION"
    for key, value in firewall.items():
        if key.endswith("_authorized") or key == "package_c_proof_artifact_registered":
            assert value == "false", key


def test_gate28_evidence_commands_are_safe_unit_test_surfaces() -> None:
    payload = gate28.build_payload(execute_tests=False)
    commands = {" ".join(row["argv"]) for row in payload["test_evidence"]}
    joined = "\n".join(commands).lower()

    assert "pytest" in joined
    assert "py_compile" in joined
    assert "git diff --check" in joined
    assert "comsolbatch" not in joined
    assert ".mph" not in joined
    assert "nodi runtime recomputation" not in joined


def test_gate28_external_review_prompt_is_self_contained_and_no_claim() -> None:
    payload = gate28.build_payload(execute_tests=False)
    prompt = gate28.external_review_prompt_text(
        payload,
        evidence_sha256="a" * 64,
        source_lock_sha256="b" * 64,
    )

    assert "You cannot see local files" in prompt
    assert "skorokhod_normal_reflection_convex_offset_trapezoid_v1" in prompt
    assert "trapezoid_skorokhod_normal_reflection_euler_active_set_v1" in prompt
    assert "finite_step_reflection_surrogate_not_hindered_hydrodynamics" in prompt
    assert "Test evidence JSON sha256" in prompt
    assert "READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY" in prompt
    assert "NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv" in prompt
    for field in gate28.GATE27_REQUIRED_PROOF_CONTRACT_FIELDS:
        assert f"`{field}`" in prompt
    assert "Do not recommend NODI runtime recomputation" in prompt
    assert "does not register Package C proof/pass" in prompt


def test_gate28_validate_payload_requires_executed_evidence_by_default() -> None:
    payload = gate28.build_payload(execute_tests=False)

    failures = gate28.validate_payload(payload)

    assert "All evidence commands executed" in failures
    assert "All evidence commands passed" in failures


def test_gate28_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate28_sidewall_package_c_proof_review_packet.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate28-package-c-proof-review-packet is required" in result.stderr


def test_gate28_github_visible_review_files_are_not_ignored() -> None:
    for path in gate28.GATE28_GITHUB_VISIBLE_REVIEW_FILES:
        if Path(path).suffix.lower() not in {".csv", ".json"}:
            continue
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--no-index", path.as_posix()],
            cwd=gate28.PROJECT_ROOT,
            check=False,
        )
        assert result.returncode != 0, path
