from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_qch_sidecar_candidate as builder


def test_qch_sidecar_candidate_packet_builds_from_flow_solver_rows() -> None:
    payload = builder.build_payload(builder.PRESSURE_DROP_PA)
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["candidate_qch_sidecar_current"] is True
    assert summary["formal_gate2_qch_sidecar_current"] is False
    assert summary["formal_qch_weighting_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_detection_probability_current"] is False
    assert summary["candidate_qch_open_rows"] >= 2
    assert summary["blocked_qch_rows"] >= 1
    assert summary["candidate_flow_split_sum"] == 1.0


def test_qch_rows_have_provenance_and_blocked_claims() -> None:
    rows = builder.build_payload(builder.PRESSURE_DROP_PA)["qch_rows"]

    assert rows
    open_rows = [row for row in rows if row["qch_sidecar_status"] == "candidate_qch_sidecar_row"]
    assert len(open_rows) >= 2
    assert sum(float(row["candidate_flow_split_fraction"]) for row in rows) == 1.0
    for row in rows:
        assert row["source_artifact"].endswith(
            "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_SOLVER_ROWS_20260701.csv"
        )
        assert len(row["source_sha256"]) == 64
        assert len(row["source_solve_hash"]) == 64
        assert len(row["geometry_hash"]) == 64
        assert row["formal_qch_weighting_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["yield_detection_probability_current"] == "false"
        assert row["claim_boundary"] == builder.QCH_SIDECAR_CLAIM_BOUNDARY


def test_qch_promotion_contract_keeps_route_yield_detection_explicit() -> None:
    contract = builder.promotion_contract_rows()
    targets = {row["promotion_target"] for row in contract}

    assert "formal_gate2_qch_sidecar" in targets
    assert "route_score" in targets
    assert "winner_or_JRC" in targets
    assert "yield_detection_probability" in targets
    for row in contract:
        assert row["authorization_to_implement"] == "true"
        assert row["current_value"] == "false"
        assert row["hard_fail_if"].endswith("_true_without_required_evidence")


def test_qch_sidecar_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(builder.PRESSURE_DROP_PA)
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
    assert f"{builder.PREFIX}_QCH_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_CONTRACT_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "522_NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
