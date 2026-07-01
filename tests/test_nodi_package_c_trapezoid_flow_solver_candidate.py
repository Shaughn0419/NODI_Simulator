from __future__ import annotations

from functools import lru_cache
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_package_c_trapezoid_flow_solver_candidate as flow


@lru_cache(maxsize=1)
def _payload() -> dict:
    return flow.build_payload()


def test_flow_solver_candidate_packet_passes_without_qch() -> None:
    payload = _payload()
    failures = flow.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == flow.DISPOSITION
    assert summary["candidate_solver_output_rows"] >= 2
    assert summary["blocked_solver_rows"] >= 1
    assert summary["theta85_resistance_ratio_vs_rectangle_proxy"] > 1.0
    assert summary["trapezoid_flow_solver_candidate_output_current"] is True
    assert summary["trapezoid_flow_solver_final_claim_current"] is False
    assert summary["q_ch_weighting_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False


def test_solver_rows_include_rectangle_taper_and_closed_cases() -> None:
    rows = _payload()["solver_rows"]
    by_case = {row["case_id"]: row for row in rows}

    rectangle = by_case["rectangle_limit_theta90_D900_W500"]
    tapered = by_case["taper_theta85_D900_W500"]
    closed = by_case["closed_theta70_D900_W500"]

    assert rectangle["solver_status"] == "candidate_solver_output"
    assert tapered["solver_status"] == "candidate_solver_output"
    assert closed["solver_status"] == "blocked_geometry_closed"
    assert float(tapered["resistance_ratio_vs_rectangle_proxy"]) > 1.0
    assert int(tapered["active_cell_count"]) < int(rectangle["active_cell_count"])


def test_solver_rows_are_not_qch_or_route_outputs() -> None:
    for row in _payload()["solver_rows"]:
        assert row["not_qch_weighted"] == "true"
        assert row["q_ch_weighting_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["claim_boundary"] == "trapezoid_flow_solver_candidate_not_qch_not_route_not_wet"


def test_qch_promotion_blockers_remain_false_but_implementation_authorized() -> None:
    rows = _payload()["qch_blockers"]
    by_target = {row["blocked_target"]: row for row in rows}

    for target in [
        "q_ch_weighting",
        "route_score",
        "winner",
        "yield_detection_probability",
    ]:
        row = by_target[target]
        assert row["current_value"] == "false"
        assert row["implementation_authorized"] == "true"
        assert row["candidate_solver_evidence_available"] == "true"
        assert row["required_evidence_before_true"]
        assert row["hard_fail_if"].endswith("_true_without_required_evidence")


def test_written_outputs_manifest_contains_flow_candidate_artifacts(tmp_path) -> None:
    payload = _payload()
    outputs = flow.write_outputs(
        payload,
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    artifacts = {path.name for path in outputs}

    assert "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_STATUS_20260701.json" in artifacts
    assert "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_SOLVER_ROWS_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_QCH_PROMOTION_BLOCKERS_20260701.csv" in artifacts
    assert "521_NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_20260701.md" in artifacts

    manifest_rows = read_csv_rows(
        tmp_path
        / "joint_interface"
        / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_MANIFEST_20260701.csv"
    )
    by_artifact = {row["artifact"]: row for row in manifest_rows}
    assert by_artifact[
        "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_MANIFEST_20260701.csv"
    ]["sha256"] == flow.SELF_MANIFEST_SHA256


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_trapezoid_flow_solver_candidate.py",
        ],
        cwd=flow.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-trapezoid-flow-solver-candidate is required" in result.stderr
