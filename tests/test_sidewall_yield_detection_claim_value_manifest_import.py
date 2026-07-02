from __future__ import annotations

from pathlib import Path

from nodi_simulator.realism_v2_io import sha256_file
from nodi_simulator.sidewall_yield_detection_claim_value_manifest_import import (
    DETECTION_CLAIM_VALUE_BRANCH,
    IMPORT_READY_STATUS,
    YIELD_CLAIM_VALUE_BRANCH,
    build_yield_detection_claim_value_rows_from_manifest,
)
from nodi_simulator.sidewall_yield_detection_claim_value_review import (
    build_yield_detection_claim_value_review,
)
from tests.test_sidewall_yield_detection_claim_value_review import _winner_rows


def _source_file(tmp_path: Path, name: str) -> Path:
    path = tmp_path / "claim_value_sources" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("route,value\nROUTE-CAND-001,1\n", encoding="utf-8")
    return path


def _manifest_rows(tmp_path: Path) -> list[dict[str, str]]:
    detection_source = _source_file(tmp_path, "detection.csv")
    yield_source = _source_file(tmp_path, "yield.csv")
    rows: list[dict[str, str]] = []
    for route_id in ("ROUTE-CAND-001", "ROUTE-CAND-002"):
        rows.append(
            {
                "claim_value_branch": DETECTION_CLAIM_VALUE_BRANCH,
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
                "source_geometry_match_level": "validated_transfer",
                "source_artifact_path": str(detection_source.relative_to(tmp_path)),
            }
        )
        rows.append(
            {
                "claim_value_branch": YIELD_CLAIM_VALUE_BRANCH,
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
                "source_geometry_match_level": "validated_transfer",
                "source_artifact_path": str(yield_source.relative_to(tmp_path)),
            }
        )
    return rows


def test_manifest_import_binds_hashes_and_passes_existing_claim_value_review(
    tmp_path: Path,
) -> None:
    detection_rows, yield_rows, audit_rows = (
        build_yield_detection_claim_value_rows_from_manifest(
            manifest_rows=_manifest_rows(tmp_path),
            artifact_root=tmp_path,
        )
    )

    assert len(detection_rows) == 2
    assert len(yield_rows) == 2
    assert {row.import_status for row in audit_rows} == {IMPORT_READY_STATUS}
    for row in detection_rows + yield_rows:
        assert row["source_artifact_sha256"] == sha256_file(
            tmp_path / row["source_artifact_path"]
        )

    review_rows, guard_rows = build_yield_detection_claim_value_review(
        winner_jrc_rows=_winner_rows(),
        detection_value_rows=detection_rows,
        yield_value_rows=yield_rows,
        artifact_root=tmp_path,
    )

    assert {row.detection_probability_simulation_candidate_current for row in review_rows} == {
        True
    }
    assert {row.yield_simulation_candidate_current for row in review_rows} == {True}
    assert {row.wet_pass_probability_simulation_candidate_current for row in review_rows} == {
        True
    }
    assert {row.detection_probability_current for row in review_rows} == {False}
    assert {row.yield_current for row in review_rows} == {False}
    assert {row.wet_pass_probability_current for row in review_rows} == {False}
    assert {
        row.activation_allowed_now
        for row in guard_rows
        if row.promotion_target in {"detection_probability", "yield", "wet_pass_probability"}
    } == {False}
    assert {
        row.activation_allowed_now
        for row in guard_rows
        if row.promotion_target
        in {"simulation_detection_probability_candidate", "simulation_yield_wet_candidate"}
    } == {True}


def test_manifest_import_rejects_missing_source_artifact(tmp_path: Path) -> None:
    manifest_rows = _manifest_rows(tmp_path)
    manifest_rows[0]["source_artifact_path"] = "missing.csv"

    detection_rows, yield_rows, audit_rows = (
        build_yield_detection_claim_value_rows_from_manifest(
            manifest_rows=manifest_rows,
            artifact_root=tmp_path,
        )
    )

    assert len(detection_rows) == 1
    assert len(yield_rows) == 2
    rejected = [
        row for row in audit_rows if row.import_rejection_reason == "source_artifact_missing"
    ]
    assert len(rejected) == 1


def test_manifest_import_rejects_duplicate_route_branch(tmp_path: Path) -> None:
    manifest_rows = _manifest_rows(tmp_path)
    manifest_rows.append(dict(manifest_rows[0]))

    detection_rows, _yield_rows, audit_rows = (
        build_yield_detection_claim_value_rows_from_manifest(
            manifest_rows=manifest_rows,
            artifact_root=tmp_path,
        )
    )

    assert len(detection_rows) == 2
    assert any(row.import_rejection_reason == "duplicate_route_branch" for row in audit_rows)
