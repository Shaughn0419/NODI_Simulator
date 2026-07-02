from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_route_formula_policy_review as builder,
)


def test_route_formula_policy_review_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.READY_DISPOSITION
    assert summary["policy_rows"] == 2
    assert summary["fixture_policy_rows"] == 2
    assert summary["guard_rows"] == 6
    assert summary["fixture_guard_rows"] == 6
    assert summary["current_formula_component_ready_rows"] == 2
    assert summary["fixture_formula_component_ready_rows"] == 2
    assert summary["route_score_current_rows"] == 0
    assert summary["route_score_candidate_ready_rows"] == 2
    assert summary["simulation_route_score_candidate_current_rows"] == 2
    assert summary["fixture_route_score_candidate_rows_not_evidence"] == 2
    assert summary["winner_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0


def test_current_rows_have_simulation_candidates_but_no_final_route_scores() -> None:
    payload = builder.build_payload()
    current = payload["policy_rows"]
    fixture = payload["fixture_policy_rows"]

    assert {row["route_candidate_id"] for row in current} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in current:
        assert row["source_evidence_class"] == builder.SIMULATION_ACCEPTED_EVIDENCE_CLASS
        assert row["route_formula_component_vector_ready"] is True
        assert row["simulation_route_score_candidate_current"] is True
        assert row["route_score_current"] is False
        assert row["route_score_value_current"] == ""
        assert row["route_formula_policy_review_status"] == (
            "simulation_route_score_candidate_ready_for_ranking_review"
        )
    by_route = {row["route_candidate_id"]: row for row in fixture}
    assert by_route["ROUTE-CAND-001"]["route_score_candidate_value"] > (
        by_route["ROUTE-CAND-002"]["route_score_candidate_value"]
    )
    for row in fixture:
        assert row["source_evidence_class"] == builder.FIXTURE_EVIDENCE_CLASS
        assert row["fixture_not_evidence"] is True
        assert row["simulation_route_score_candidate_current"] is False
        assert row["route_score_current"] is False
        assert row["route_formula_policy_review_status"] == (
            "fixture_route_score_candidate_path_passes_not_evidence"
        )


def test_route_formula_policy_review_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_POLICY_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_FIXTURE_POLICY_ROWS_NOT_EVIDENCE_20260701.csv" in names
    assert f"{builder.PREFIX}_GUARD_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert f"574_{builder.PREFIX}_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
