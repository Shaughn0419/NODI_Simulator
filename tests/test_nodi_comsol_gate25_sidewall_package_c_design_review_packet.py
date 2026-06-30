from __future__ import annotations

import csv
import json
import subprocess
import sys

from tools.audits import build_nodi_comsol_gate25_sidewall_package_c_design_review_packet as gate25


def test_gate25_payload_passes_design_review_validation() -> None:
    payload = gate25.build_payload()

    assert gate25.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate25.DISPOSITION
    assert payload["summary"]["gate24_head_is_ancestor_of_current"] is True
    assert payload["summary"]["gate24_disposition"] == gate25.EXPECTED_GATE24_DISPOSITION
    assert payload["summary"]["gate24_no_auth"] is True
    assert payload["summary"]["gate24_review_only"] is True


def test_gate25_locks_gate24_sources_without_missing_inputs() -> None:
    payload = gate25.build_payload()

    assert payload["summary"]["gate24_source_lock_rows"] == len(gate25.GATE24_FILES)
    assert payload["summary"]["gate24_missing_sources"] == 0
    assert {row["lock_status"] for row in payload["gate24_source_locks"]} == {"MATCH"}


def test_gate25_design_scope_is_review_only_and_covers_package_c_components() -> None:
    payload = gate25.build_payload()
    components = {row["package_c_component"] for row in payload["design_scope"]}

    assert {
        "trajectory_boundary",
        "near_wall_diffusion",
        "flow_model",
        "electrokinetic_transport",
        "optical_reference_field",
    } <= components
    assert payload["summary"]["implementation_permission_rows"] == 0
    for row in payload["design_scope"]:
        assert row["implementation_permission"] == "false"
        assert "explicit_future_authorization" in row["required_before_implementation"]


def test_gate25_external_prompt_is_self_contained_for_github_only_review() -> None:
    prompt = gate25.external_prompt_text()

    assert "Visibility note: you may only see files on GitHub" in prompt
    assert "nodi_simulator/cross_section_geometry.py" in prompt
    assert "nodi_simulator/trajectory.py" in prompt
    assert "authorized_now=false" in prompt
    assert "sidewall_projection_boundary_surrogate_not_specular_reflection" in prompt
    assert "W(u) = W_top - 2*k*u" in prompt
    assert "W_bottom_unclipped = W_top - 2*k*H" in prompt
    assert "a*sqrt(1+k^2)" in prompt
    assert "Do not request or assume NODI recomputation" in prompt
    assert "BLOCKED_PHYSICS_UNSAFE" in prompt


def test_gate25_no_auth_firewall_remains_closed() -> None:
    payload = gate25.build_payload()
    firewall = payload["no_auth_firewall"][0]

    assert firewall["firewall_status"] == "PASS_NO_AUTH_DESIGN_REVIEW_ONLY"
    assert firewall["package_c_physics_implementation_authorized"] == "false"
    assert firewall["package_c_proof_registry_pass_authorized"] == "false"
    assert firewall["runtime_configuration_authorized"] == "false"
    assert firewall["sidewall_prs_eas_numeric_output_authorized"] == "false"
    assert firewall["nodi_runtime_recompute_authorized"] == "false"
    assert firewall["comsol_launch_authorized"] == "false"
    assert firewall["mph_load_authorized"] == "false"
    assert firewall["qch_weighting_authorized"] == "false"
    assert firewall["jrc_authorized"] == "false"
    assert firewall["route_score_authorized"] == "false"
    assert firewall["winner_authorized"] == "false"
    assert firewall["yield_authorized"] == "false"
    assert firewall["detection_probability_authorized"] == "false"
    assert firewall["fabrication_release_authorized"] == "false"


def test_gate25_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate25-package-c-design-review is required" in result.stderr


def test_gate25_cli_confirmed_write_outputs_remain_review_only() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py",
            "--confirm-gate25-package-c-design-review",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert gate25.DISPOSITION in result.stdout

    output_dir = gate25.OUTPUT_DIR
    status_path = output_dir / "NODI_COMSOL_GATE25_SIDEWALL_STATUS_20260630.json"
    manifest_path = output_dir / "NODI_COMSOL_GATE25_SIDEWALL_MANIFEST_20260630.csv"
    prompt_path = output_dir / "NODI_COMSOL_GATE25_SIDEWALL_EXTERNAL_AI_PROMPT_20260630.md"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))

    assert status["disposition"] == gate25.DISPOSITION
    assert status["review_only"] is True
    assert status["no_auth"] is True
    assert status["summary"]["implementation_permission_rows"] == 0
    assert status["summary"]["no_auth_firewall_failures"] == 0
    assert prompt_path.exists()
    assert "Visibility note" in prompt_path.read_text(encoding="utf-8")
    assert len(manifest) >= 8
    assert all((gate25.PROJECT_ROOT / row["path"]).exists() for row in manifest)
    assert all(row["policy_impact"] == "none_no_auth" for row in manifest)
