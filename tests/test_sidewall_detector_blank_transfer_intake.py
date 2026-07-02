from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file
from nodi_simulator.sidewall_detector_blank_transfer_intake import (
    ROUTE_MATRIX_ACCEPTED_STATUS,
    ROUTE_MATRIX_NO_TRANSFER_STATUS,
    TRANSFER_ACCEPTED_STATUS,
    TRANSFER_MISSING_STATUS,
    build_detector_blank_transfer_intake,
    detector_blank_transfer_promotion_update_rows,
    detector_blank_transfer_template_rows,
)


def _panel_rows() -> list[dict[str, str]]:
    return [
        {
            "matrix_row_id": f"DB-CAL-MATRIX-{route_id}",
            "route_candidate_id": route_id,
            "route_key": route_key,
            "source_case_id": source_case,
            "qch_sidecar_id": f"QCH-{route_id}",
            "total_selected_annulus_events": "168",
            "blank_guard_status": "nearest_blank_guard_finite_below_threshold_not_sidewall_specific",
            "detector_response_context_status": (
                "detector_identity_context_available_not_sidewall_response_validation"
            ),
            "route_evidence_matrix_status": (
                "detector_blank_route_evidence_matrix_candidate_ready_not_probability"
            ),
        }
        for route_id, route_key, source_case in (
            (
                "ROUTE-CAND-001",
                "route_rectangle_limit_theta90_D900_W500",
                "rectangle_limit_theta90_D900_W500",
            ),
            (
                "ROUTE-CAND-002",
                "route_taper_theta85_D900_W500",
                "taper_theta85_D900_W500",
            ),
        )
    ]


def test_detector_blank_transfer_intake_defaults_to_no_transfer_evidence() -> None:
    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows()
    )

    assert len(intake_rows) == 2
    assert len(matrix_rows) == 2
    assert {row.transfer_validation_status for row in intake_rows} == {
        TRANSFER_MISSING_STATUS
    }
    assert {row.route_transfer_matrix_status for row in matrix_rows} == {
        ROUTE_MATRIX_NO_TRANSFER_STATUS
    }
    for row in intake_rows:
        assert row.accepted_transfer_current is False
        assert row.detection_probability_current is False
        assert row.route_score_current is False
        assert row.yield_current is False


def test_detector_blank_transfer_intake_accepts_complete_sidewall_transfer() -> None:
    transfer_rows = [_complete_transfer_row()]
    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows(),
        transfer_input_rows=transfer_rows,
    )

    accepted = [
        row for row in intake_rows if row.transfer_validation_status == TRANSFER_ACCEPTED_STATUS
    ]
    assert len(accepted) == 1
    assert accepted[0].accepted_transfer_current is True
    assert accepted[0].transfer_rejection_reason == "accepted_transfer_candidate"
    assert accepted[0].detection_probability_current is False
    accepted_matrix = [
        row for row in matrix_rows if row.route_transfer_matrix_status == ROUTE_MATRIX_ACCEPTED_STATUS
    ]
    assert len(accepted_matrix) == 1


def test_detector_blank_transfer_intake_validates_source_artifact_hash(
    tmp_path: Path,
) -> None:
    blank_path, blank_sha = _source_artifact(tmp_path, "blank_trace.csv")
    detector_path, detector_sha = _source_artifact(tmp_path, "detector_response.csv")
    intake_rows, _matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows(),
        transfer_input_rows=[
            _complete_transfer_row(
                blank_trace_artifact_path=blank_path.name,
                blank_trace_sha256=blank_sha,
                detector_response_artifact_path=detector_path.name,
                detector_response_sha256=detector_sha,
            )
        ],
        artifact_root=tmp_path,
    )

    accepted = [
        row for row in intake_rows if row.transfer_validation_status == TRANSFER_ACCEPTED_STATUS
    ]
    assert len(accepted) == 1
    assert accepted[0].blank_trace_artifact_path == blank_path.name
    assert accepted[0].detector_response_artifact_path == detector_path.name


def test_detector_blank_transfer_intake_rejects_source_hash_mismatch(
    tmp_path: Path,
) -> None:
    blank_path, blank_sha = _source_artifact(tmp_path, "blank_trace.csv")
    detector_path, _detector_sha = _source_artifact(tmp_path, "detector_response.csv")
    intake_rows, _matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows(),
        transfer_input_rows=[
            _complete_transfer_row(
                blank_trace_artifact_path=blank_path.name,
                blank_trace_sha256=blank_sha,
                detector_response_artifact_path=detector_path.name,
                detector_response_sha256="f" * 64,
            )
        ],
        artifact_root=tmp_path,
    )

    rejected = [
        row for row in intake_rows if row.route_candidate_id == "ROUTE-CAND-001"
    ][0]
    assert (
        rejected.transfer_rejection_reason
        == "invalid_detector_response_artifact_or_sha256"
    )
    assert rejected.accepted_transfer_current is False


def test_detector_blank_transfer_template_and_promotion_updates_are_not_claims() -> None:
    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows()
    )
    templates = detector_blank_transfer_template_rows(_panel_rows())
    updates = detector_blank_transfer_promotion_update_rows(matrix_rows)

    assert len(intake_rows) == 2
    assert len(templates) == 2
    assert {update["target_ledger_lane"] for update in updates} == {
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    assert {update["new_context_status"] for update in updates} == {
        ROUTE_MATRIX_NO_TRANSFER_STATUS
    }
    for update in updates:
        assert update["target_claim_current"] is False
        assert "detection_probability" in update["blocked_promotion"]
        assert "route_score" in update["blocked_promotion"]


def test_detector_blank_transfer_intake_rejects_bad_hash_and_probability_ci() -> None:
    bad_hash = _complete_transfer_row(blank_trace_sha256="not-a-sha")
    bad_ci = _complete_transfer_row(
        route_candidate_id="ROUTE-CAND-002",
        false_positive_rate_estimate="0.001",
        false_positive_rate_ci_low="0.002",
        false_positive_rate_ci_high="0.003",
    )

    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows(),
        transfer_input_rows=[bad_hash, bad_ci],
    )

    reasons = {
        row.route_candidate_id: row.transfer_rejection_reason for row in intake_rows
    }
    assert reasons == {
        "ROUTE-CAND-001": "invalid_blank_trace_sha256",
        "ROUTE-CAND-002": "invalid_false_positive_ci_order",
    }
    assert {row.transfer_validation_status for row in intake_rows} == {
        "detector_blank_transfer_rejected_missing_required_evidence"
    }
    assert {row.route_transfer_matrix_status for row in matrix_rows} == {
        ROUTE_MATRIX_NO_TRANSFER_STATUS
    }


def test_detector_blank_transfer_intake_rejects_low_sample_and_bad_controls() -> None:
    low_n = _complete_transfer_row(n_blank_traces="2")
    bad_controls = _complete_transfer_row(
        route_candidate_id="ROUTE-CAND-002",
        controls_status="controls_missing",
    )

    intake_rows, _matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows(),
        transfer_input_rows=[low_n, bad_controls],
    )

    reasons = {
        row.route_candidate_id: row.transfer_rejection_reason for row in intake_rows
    }
    assert reasons == {
        "ROUTE-CAND-001": "insufficient_blank_trace_count",
        "ROUTE-CAND-002": "controls_not_pass",
    }
    assert all(row.accepted_transfer_current is False for row in intake_rows)


def _complete_transfer_row(
    *,
    route_candidate_id: str = "ROUTE-CAND-001",
    blank_trace_artifact_path: str = "blank-trace.csv",
    blank_trace_sha256: str = "a" * 64,
    detector_response_artifact_path: str = "detector-response.csv",
    detector_response_sha256: str = "b" * 64,
    false_positive_rate_estimate: str = "0.0001",
    false_positive_rate_ci_low: str = "0.0",
    false_positive_rate_ci_high: str = "0.0004",
    n_blank_traces: str = "3",
    n_detector_calibration_runs: str = "3",
    controls_status: str = "controls_pass",
    pre_registered_rule_status: str = "pre_registered",
) -> dict[str, str]:
    return {
        "route_candidate_id": route_candidate_id,
        "transfer_artifact_id": f"transfer-{route_candidate_id}",
        "blank_trace_artifact_id": f"blank-{route_candidate_id}",
        "blank_trace_artifact_path": blank_trace_artifact_path,
        "blank_trace_sha256": blank_trace_sha256,
        "detector_response_artifact_id": f"detector-{route_candidate_id}",
        "detector_response_artifact_path": detector_response_artifact_path,
        "detector_response_sha256": detector_response_sha256,
        "blank_trace_geometry_match_level": "sidewall_specific",
        "detector_response_model_id": "detector-response-v1",
        "false_positive_rate_estimate": false_positive_rate_estimate,
        "false_positive_rate_ci_low": false_positive_rate_ci_low,
        "false_positive_rate_ci_high": false_positive_rate_ci_high,
        "n_blank_traces": n_blank_traces,
        "n_detector_calibration_runs": n_detector_calibration_runs,
        "controls_status": controls_status,
        "uncertainty_model": "wilson_interval",
        "pre_registered_rule_status": pre_registered_rule_status,
    }


def _source_artifact(tmp_path: Path, name: str) -> tuple[Path, str]:
    path = tmp_path / name
    path.write_text(
        "route_candidate_id,value\nROUTE-CAND-001,detector-blank-source\n",
        encoding="utf-8",
    )
    return path, sha256_file(path)
