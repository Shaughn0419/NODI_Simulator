from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file
from nodi_simulator.sidewall_yield_detection_claim_value_review import (
    SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_BOUNDARY,
    build_yield_detection_claim_value_review,
    detection_claim_value_template_rows,
    yield_claim_value_template_rows,
)


def _winner_rows() -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_geometry_family": "ideal_rectangle",
            "route_score_current": "True",
            "winner_current": "True",
            "JRC_current": "True",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "route_geometry_family": "trapezoid_tapered_sidewalls",
            "route_score_current": "True",
            "winner_current": "False",
            "JRC_current": "False",
        },
    ]


def _source_artifact(tmp_path: Path, name: str, text: str) -> tuple[str, str]:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path), sha256_file(path)


def _detection_row(
    route_id: str = "ROUTE-CAND-001",
    *,
    source_artifact_path: str = "",
    source_artifact_sha256: str = "",
) -> dict[str, str]:
    return {
        "route_candidate_id": route_id,
        "detection_probability_estimate": "0.91",
        "detection_probability_ci_low": "0.86",
        "detection_probability_ci_high": "0.95",
        "n_positive_control_events": "5",
        "detector_probability_model_id": "detector-prob-v1",
        "threshold_policy_id": "threshold-policy-v1",
        "controls_status": "controls_pass",
        "uncertainty_model": "binomial_interval",
        "pre_registered_rule_status": "pre_registered",
        "source_geometry_match_level": "sidewall_specific",
        "source_artifact_path": source_artifact_path,
        "source_artifact_sha256": source_artifact_sha256,
    }


def _yield_row(
    route_id: str = "ROUTE-CAND-001",
    *,
    source_artifact_path: str = "",
    source_artifact_sha256: str = "",
) -> dict[str, str]:
    return {
        "route_candidate_id": route_id,
        "yield_estimate": "0.72",
        "yield_ci_low": "0.66",
        "yield_ci_high": "0.78",
        "wet_pass_probability_estimate": "0.81",
        "wet_pass_probability_ci_low": "0.74",
        "wet_pass_probability_ci_high": "0.88",
        "n_wet_trials": "5",
        "yield_model_id": "yield-model-v1",
        "controls_status": "controls_pass",
        "uncertainty_model": "binomial_interval",
        "pre_registered_rule_status": "pre_registered",
        "source_geometry_match_level": "sidewall_specific",
        "source_artifact_path": source_artifact_path,
        "source_artifact_sha256": source_artifact_sha256,
    }


def test_claim_value_review_defaults_to_missing_no_claims() -> None:
    rows, guards = build_yield_detection_claim_value_review(
        winner_jrc_rows=_winner_rows()
    )

    assert len(rows) == 2
    assert len(guards) == 4
    for row in rows:
        assert row.detection_probability_current is False
        assert row.yield_current is False
        assert row.wet_pass_probability_current is False
        assert row.production_ingestion_current is False
        assert row.claim_value_review_status == (
            "blocked_until_real_detection_and_yield_value_rows_accepted"
        )
        assert row.claim_boundary == (
            SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_BOUNDARY
        )
    assert {guard.activation_allowed_now for guard in guards} == {False}


def test_claim_value_review_accepts_valid_detection_and_yield_rows(
    tmp_path: Path,
) -> None:
    detection_path, detection_sha = _source_artifact(
        tmp_path, "detection-source.csv", "route,detection\n"
    )
    yield_path, yield_sha = _source_artifact(
        tmp_path, "yield-source.csv", "route,yield\n"
    )
    rows, guards = build_yield_detection_claim_value_review(
        winner_jrc_rows=_winner_rows(),
        detection_value_rows=[
            _detection_row(
                "ROUTE-CAND-001",
                source_artifact_path=detection_path,
                source_artifact_sha256=detection_sha,
            ),
            _detection_row(
                "ROUTE-CAND-002",
                source_artifact_path=detection_path,
                source_artifact_sha256=detection_sha,
            ),
        ],
        yield_value_rows=[
            _yield_row(
                "ROUTE-CAND-001",
                source_artifact_path=yield_path,
                source_artifact_sha256=yield_sha,
            ),
            _yield_row(
                "ROUTE-CAND-002",
                source_artifact_path=yield_path,
                source_artifact_sha256=yield_sha,
            ),
        ],
    )

    assert {row.detection_probability_current for row in rows} == {True}
    assert {row.yield_current for row in rows} == {True}
    assert {row.wet_pass_probability_current for row in rows} == {True}
    by_route = {row.route_candidate_id: row for row in rows}
    assert by_route["ROUTE-CAND-001"].claim_value_review_status == (
        "yield_detection_values_ready_for_integrated_route_claim_review"
    )
    assert by_route["ROUTE-CAND-002"].claim_value_review_status == (
        "yield_detection_values_ready_waiting_winner_jrc"
    )
    by_target = {guard.promotion_target: guard for guard in guards}
    assert by_target["detection_probability"].activation_allowed_now is True
    assert by_target["yield"].activation_allowed_now is True
    assert by_target["production_ingestion"].activation_allowed_now is False


def test_claim_value_review_rejects_bad_intervals_and_controls(tmp_path: Path) -> None:
    detection_path, detection_sha = _source_artifact(
        tmp_path, "detection-source.csv", "route,detection\n"
    )
    yield_path, yield_sha = _source_artifact(
        tmp_path, "yield-source.csv", "route,yield\n"
    )
    bad_detection = _detection_row(
        source_artifact_path=detection_path,
        source_artifact_sha256=detection_sha,
    )
    bad_detection["detection_probability_ci_low"] = "0.93"
    bad_yield = _yield_row(
        source_artifact_path=yield_path,
        source_artifact_sha256=yield_sha,
    )
    bad_yield["controls_status"] = "controls_missing"
    rows, guards = build_yield_detection_claim_value_review(
        winner_jrc_rows=_winner_rows(),
        detection_value_rows=[bad_detection],
        yield_value_rows=[bad_yield],
    )

    route = next(row for row in rows if row.route_candidate_id == "ROUTE-CAND-001")
    assert route.detection_value_validation_status == (
        "detection_probability_value_rejected_invalid_interval"
    )
    assert route.yield_value_validation_status == (
        "yield_wet_value_bundle_rejected_metadata_or_controls"
    )
    assert route.detection_probability_current is False
    assert route.yield_current is False
    assert {guard.activation_allowed_now for guard in guards} == {False}


def test_claim_value_review_rejects_source_hash_mismatch(tmp_path: Path) -> None:
    source_path, _source_sha = _source_artifact(
        tmp_path, "detection-source.csv", "route,detection\n"
    )
    rows, _guards = build_yield_detection_claim_value_review(
        winner_jrc_rows=_winner_rows(),
        detection_value_rows=[
            _detection_row(
                source_artifact_path=source_path,
                source_artifact_sha256="a" * 64,
            )
        ],
        yield_value_rows=[],
    )

    route = next(row for row in rows if row.route_candidate_id == "ROUTE-CAND-001")
    assert route.detection_value_validation_status == (
        "detection_probability_value_rejected_source_artifact_missing_or_hash_mismatch"
    )
    assert route.detection_probability_current is False


def test_claim_value_templates_track_routes() -> None:
    detection_templates = detection_claim_value_template_rows(_winner_rows())
    yield_templates = yield_claim_value_template_rows(_winner_rows())

    assert len(detection_templates) == 2
    assert len(yield_templates) == 2
    assert detection_templates[0]["detection_probability_estimate"] == ""
    assert yield_templates[0]["yield_estimate"] == ""
    assert "source_artifact_path" in detection_templates[0]
    assert "source_artifact_path" in yield_templates[0]
