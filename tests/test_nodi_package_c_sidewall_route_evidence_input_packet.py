from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_package_c_sidewall_route_evidence_input_packet as builder


def test_route_evidence_input_packet_builds_current_input_handoff() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert summary["disposition"] == builder.DISPOSITION
    assert summary["input_rows"] == 4
    assert summary["command_rows"] == 9
    assert summary["route_formula_rows"] == 2
    assert summary["detector_template_rows"] == 2
    assert summary["wet_template_rows"] == 14
    assert summary["detection_value_template_rows"] == 2
    assert summary["yield_value_template_rows"] == 2
    assert summary["detector_accepted_transfer_rows_total"] == 2
    assert summary["input_branches_missing_current_acceptance"] == (
        "wet_surface_observation;detection_probability_value;yield_wet_value"
    )
    assert summary["route_formula_ready_for_claim_review_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["wet_pass_probability_current_rows"] == 0
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert "detector_blank_transfer" not in summary["next_high_leverage_step"]


def test_route_evidence_input_packet_command_chain_order() -> None:
    payload = builder.build_payload()
    command_ids = [row["command_id"] for row in payload["command_rows"]]

    assert command_ids == [
        "detector_blank_transfer_intake",
        "wet_surface_observation_intake",
        "detector_wet_activation_runner",
        "route_formula_activation_closure",
        "route_formula_review_dry_run",
        "route_formula_policy_review",
        "winner_jrc_policy_review",
        "yield_detection_claim_value_review",
        "route_decision_execution_readiness",
    ]
    assert all("python tools\\audits\\" in row["command"] for row in payload["command_rows"])


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
