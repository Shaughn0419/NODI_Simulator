from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_package_c_sidewall_route_evidence_input_packet as builder


def test_route_evidence_input_packet_builds_current_input_handoff() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert summary["disposition"] == builder.READY_DISPOSITION
    assert summary["input_rows"] == 4
    assert summary["command_rows"] == 11
    assert summary["route_formula_rows"] == 2
    assert summary["detector_template_rows"] == 2
    assert summary["wet_template_rows"] == 14
    assert summary["detection_value_template_rows"] == 2
    assert summary["yield_value_template_rows"] == 2
    assert summary["detector_accepted_transfer_rows_total"] == 2
    assert summary["input_branches_missing_current_acceptance"] == ""
    assert summary["route_formula_ready_for_claim_review_rows"] == 2
    assert summary["route_formula_ready_for_simulation_candidate_review_rows"] == 2
    assert summary["detection_probability_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["wet_pass_probability_current_rows"] == 0
    assert summary["detection_probability_simulation_candidate_rows"] == 2
    assert summary["yield_simulation_candidate_rows"] == 2
    assert summary["wet_pass_probability_simulation_candidate_rows"] == 2
    assert (
        summary["source_simulation_assumption_workspace_status_source"]
        == "simulation_assumption_workspace_status"
    )
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert "detector_blank_transfer" not in summary["next_high_leverage_step"]
    assert "accepted rows" in summary["next_high_leverage_step"]
    assert "eleven-step command chain" in summary["next_high_leverage_step"]
    by_branch = {row["input_branch"]: row for row in payload["input_rows"]}
    assert by_branch["wet_surface_observation"]["source_manifest_path"].endswith(
        "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_SOURCE_MANIFEST_20260701.csv"
    )
    assert by_branch["detection_probability_value"]["source_manifest_path"].endswith(
        "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_SOURCE_MANIFEST_20260701.csv"
    )
    assert by_branch["yield_wet_value"]["source_manifest_path"].endswith(
        "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_SOURCE_MANIFEST_20260701.csv"
    )


def test_route_evidence_input_packet_command_chain_order() -> None:
    payload = builder.build_payload()
    command_ids = [row["command_id"] for row in payload["command_rows"]]

    assert command_ids == [
        "detector_blank_transfer_intake",
        "wet_surface_observation_manifest_import",
        "wet_surface_observation_intake",
        "detector_wet_activation_runner",
        "route_formula_activation_closure",
        "route_formula_review_dry_run",
        "route_formula_policy_review",
        "winner_jrc_policy_review",
        "yield_detection_claim_value_manifest_import",
        "yield_detection_claim_value_review",
        "route_decision_execution_readiness",
    ]
    assert all("python tools\\audits\\" in row["command"] for row in payload["command_rows"])


def test_route_evidence_input_packet_source_lock_lists_optional_source_manifests() -> None:
    payload = builder.build_payload()
    by_source = {row["source_id"]: row for row in payload["source_lock_rows"]}

    assert by_source["simulation_assumption_workspace_status"]["exists"] in {
        "true",
        "false",
    }
    assert by_source["optional_wet_source_manifest"]["exists"] in {"true", "false"}
    assert by_source["optional_claim_value_source_manifest"]["exists"] in {
        "true",
        "false",
    }
    assert payload["summary"]["required_source_missing_rows"] == 0


def test_route_evidence_input_packet_writes_outputs(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_INPUT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_COMMAND_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_FORMULA_ROWS_20260701.csv" in names
    assert f"571_{builder.PREFIX}_20260701.md" in names


def test_route_evidence_input_packet_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_route_evidence_input_packet.py",
        ],
        cwd=builder.PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-route-evidence-input-packet is required" in (
        result.stderr + result.stdout
    )
