from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_selected_annulus_context as builder


def test_sidewall_selected_annulus_context_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_promotion_ledger_disposition"] == (
        "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_READY_PREFLIGHT_ONLY"
    )
    assert summary["context_rows"] == 2
    assert summary["selected_annulus_context_current_rows"] == 2
    assert summary["small_n_synthetic_context"] is True
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False


def test_sidewall_selected_annulus_context_rows_are_context_only() -> None:
    rows = builder.build_payload()["context_rows"]

    assert {row["case_id"] for row in rows} == {
        "rectangle_limit_theta90_D900_W500",
        "taper_theta85_D900_W500",
    }
    for row in rows:
        assert row["selected_annulus_context_status"] == (
            "selected_annulus_context_available_small_n_not_probability"
        )
        assert int(row["selected_annulus_n_events"]) > 0
        assert row["selected_annulus_context_current"] == "true"
        assert row["small_n_synthetic_context"] == "true"
        assert row["detection_probability_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["claim_boundary"] == builder.SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY


def test_sidewall_selected_annulus_context_promotion_update_is_narrow() -> None:
    updates = builder.build_payload()["promotion_update_rows"]

    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "selected_annulus_detection_context"
    assert update["previous_status"] == "selected_annulus_context_missing_rerun_required"
    assert update["new_context_status"] == (
        "selected_annulus_context_available_small_n_not_probability"
    )
    assert update["blocked_promotion"] == "detection_probability;route_score;winner"
    assert update["hard_fail_if"] == (
        "selected_annulus_context_promoted_to_detection_probability"
    )


def test_sidewall_selected_annulus_context_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_CONTEXT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "531_NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
