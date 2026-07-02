from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_winner_jrc_policy_review as builder,
)


def test_winner_jrc_policy_review_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["review_rows"] == 2
    assert summary["fixture_review_rows"] == 2
    assert summary["guard_rows"] == 5
    assert summary["fixture_guard_rows"] == 5
    assert summary["route_score_current_rows"] == 0
    assert summary["winner_current_rows"] == 0
    assert summary["JRC_current_rows"] == 0
    assert summary["simulation_top_candidate_current_rows"] == 0
    assert summary["fixture_order_rows_not_evidence"] == 2
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0


def test_current_rows_blocked_and_fixture_order_is_not_evidence() -> None:
    payload = builder.build_payload()
    current = payload["review_rows"]
    fixture = payload["fixture_review_rows"]

    for row in current:
        assert row["source_evidence_class"] == builder.SIMULATION_ACCEPTED_EVIDENCE_CLASS
        assert row["route_score_current"] is False
        assert row["simulation_top_candidate_current"] is False
        assert row["winner_current"] is False
        assert row["JRC_current"] is False
        assert row["winner_jrc_policy_review_status"] == (
            "blocked_until_route_score_candidates_current"
        )
    assert [row["route_candidate_id"] for row in fixture] == [
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    ]
    for row in fixture:
        assert row["source_evidence_class"] == builder.FIXTURE_EVIDENCE_CLASS
        assert row["fixture_not_evidence"] is True
        assert row["winner_current"] is False
        assert row["JRC_current"] is False
        assert row["winner_jrc_policy_review_status"] == (
            "fixture_winner_order_path_passes_not_evidence"
        )


def test_winner_jrc_policy_review_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_REVIEW_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_FIXTURE_REVIEW_ROWS_NOT_EVIDENCE_20260701.csv" in names
    assert f"{builder.PREFIX}_GUARD_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert f"575_{builder.PREFIX}_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
