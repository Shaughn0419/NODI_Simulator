"""Yield and detection-probability claim-value review for sidewall routes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from nodi_simulator.realism_v2_io import sha256_file


SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_VERSION = (
    "sidewall_yield_detection_claim_value_review_v1"
)
SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_BOUNDARY = (
    "yield_detection_claim_value_review_requires_simulation_value_rows"
)
SIMULATION_CLAIM_VALUE_EVIDENCE_CLASS = "simulation_claim_value_evidence"
# Backward-compatible import alias. In this simulation-only lane, "real" means
# hash-bound current simulation evidence, not experimental truth.
REAL_CLAIM_VALUE_EVIDENCE_CLASS = SIMULATION_CLAIM_VALUE_EVIDENCE_CLASS
FIXTURE_CLAIM_VALUE_EVIDENCE_CLASS = "fixture_not_evidence"

DETECTION_REQUIRED_FIELDS: tuple[str, ...] = (
    "route_candidate_id",
    "detection_probability_estimate",
    "detection_probability_ci_low",
    "detection_probability_ci_high",
    "n_positive_control_events",
    "detector_probability_model_id",
    "threshold_policy_id",
    "controls_status",
    "uncertainty_model",
    "pre_registered_rule_status",
    "source_geometry_match_level",
    "source_artifact_path",
    "source_artifact_sha256",
)

YIELD_REQUIRED_FIELDS: tuple[str, ...] = (
    "route_candidate_id",
    "yield_estimate",
    "yield_ci_low",
    "yield_ci_high",
    "wet_pass_probability_estimate",
    "wet_pass_probability_ci_low",
    "wet_pass_probability_ci_high",
    "n_wet_trials",
    "yield_model_id",
    "controls_status",
    "uncertainty_model",
    "pre_registered_rule_status",
    "source_geometry_match_level",
    "source_artifact_path",
    "source_artifact_sha256",
)


@dataclass(frozen=True)
class SidewallYieldDetectionClaimValueReviewRow:
    claim_row_id: str
    review_version: str
    route_candidate_id: str
    route_geometry_family: str
    source_evidence_class: str
    fixture_not_evidence: bool
    winner_current: bool
    JRC_current: bool
    detection_value_row_present: bool
    detection_value_validation_status: str
    detection_probability_simulation_candidate_current: bool
    detection_probability_simulation_candidate_value: str
    detection_probability_simulation_candidate_ci_low: str
    detection_probability_simulation_candidate_ci_high: str
    detection_probability_current: bool
    detection_probability_value_current: str
    detection_probability_ci_low_current: str
    detection_probability_ci_high_current: str
    detection_source_artifact_path_current: str
    yield_value_row_present: bool
    yield_value_validation_status: str
    yield_simulation_candidate_current: bool
    yield_simulation_candidate_value: str
    yield_simulation_candidate_ci_low: str
    yield_simulation_candidate_ci_high: str
    yield_current: bool
    yield_value_current: str
    yield_ci_low_current: str
    yield_ci_high_current: str
    wet_pass_probability_current: bool
    wet_pass_probability_simulation_candidate_current: bool
    wet_pass_probability_simulation_candidate_value: str
    wet_pass_probability_simulation_candidate_ci_low: str
    wet_pass_probability_simulation_candidate_ci_high: str
    wet_pass_probability_value_current: str
    wet_pass_probability_ci_low_current: str
    wet_pass_probability_ci_high_current: str
    yield_source_artifact_path_current: str
    route_score_current: bool
    production_ingestion_current: bool
    claim_value_review_status: str
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallYieldDetectionClaimValueGuardRow:
    guard_row_id: str
    review_version: str
    promotion_target: str
    implementation_authorized: bool
    activation_allowed_now: bool
    required_evidence_before_activation: str
    hard_fail_if_activated_early: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_yield_detection_claim_value_review(
    *,
    winner_jrc_rows: list[Mapping[str, Any]],
    detection_value_rows: list[Mapping[str, Any]] | None = None,
    yield_value_rows: list[Mapping[str, Any]] | None = None,
    artifact_root: str | Path | None = None,
    source_evidence_class: str = REAL_CLAIM_VALUE_EVIDENCE_CLASS,
) -> tuple[
    list[SidewallYieldDetectionClaimValueReviewRow],
    list[SidewallYieldDetectionClaimValueGuardRow],
]:
    detection_by_route = {
        str(row.get("route_candidate_id", "")): row
        for row in (detection_value_rows or [])
    }
    yield_by_route = {
        str(row.get("route_candidate_id", "")): row
        for row in (yield_value_rows or [])
    }
    rows: list[SidewallYieldDetectionClaimValueReviewRow] = []
    for winner in sorted(
        winner_jrc_rows, key=lambda row: str(row.get("route_candidate_id", ""))
    ):
        route_id = str(winner.get("route_candidate_id", ""))
        detection = detection_by_route.get(route_id, {})
        wet_yield = yield_by_route.get(route_id, {})
        detection_status = _detection_validation_status(detection, artifact_root)
        yield_status = _yield_validation_status(wet_yield, artifact_root)
        fixture_not_evidence = source_evidence_class == FIXTURE_CLAIM_VALUE_EVIDENCE_CLASS
        detection_valid = detection_status == "detection_probability_value_accepted"
        yield_valid = yield_status == "yield_wet_value_bundle_accepted"
        detection_candidate_current = (
            detection_valid
            and source_evidence_class == SIMULATION_CLAIM_VALUE_EVIDENCE_CLASS
            and not fixture_not_evidence
        )
        yield_candidate_current = (
            yield_valid
            and source_evidence_class == SIMULATION_CLAIM_VALUE_EVIDENCE_CLASS
            and not fixture_not_evidence
        )
        rows.append(
            SidewallYieldDetectionClaimValueReviewRow(
                claim_row_id=f"YIELD-DETECTION-CLAIM-VALUE-{route_id}",
                review_version=SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_VERSION,
                route_candidate_id=route_id,
                route_geometry_family=str(winner.get("route_geometry_family", "")),
                source_evidence_class=source_evidence_class,
                fixture_not_evidence=fixture_not_evidence,
                winner_current=_bool(winner.get("winner_current")),
                JRC_current=_bool(winner.get("JRC_current")),
                detection_value_row_present=bool(detection),
                detection_value_validation_status=detection_status,
                detection_probability_simulation_candidate_current=(
                    detection_candidate_current
                ),
                detection_probability_simulation_candidate_value=(
                    str(detection.get("detection_probability_estimate", ""))
                    if detection_candidate_current
                    else ""
                ),
                detection_probability_simulation_candidate_ci_low=(
                    str(detection.get("detection_probability_ci_low", ""))
                    if detection_candidate_current
                    else ""
                ),
                detection_probability_simulation_candidate_ci_high=(
                    str(detection.get("detection_probability_ci_high", ""))
                    if detection_candidate_current
                    else ""
                ),
                detection_probability_current=False,
                detection_probability_value_current="",
                detection_probability_ci_low_current="",
                detection_probability_ci_high_current="",
                detection_source_artifact_path_current=(
                    str(detection.get("source_artifact_path", ""))
                    if detection_candidate_current
                    else ""
                ),
                yield_value_row_present=bool(wet_yield),
                yield_value_validation_status=yield_status,
                yield_simulation_candidate_current=yield_candidate_current,
                yield_simulation_candidate_value=(
                    str(wet_yield.get("yield_estimate", ""))
                    if yield_candidate_current
                    else ""
                ),
                yield_simulation_candidate_ci_low=(
                    str(wet_yield.get("yield_ci_low", ""))
                    if yield_candidate_current
                    else ""
                ),
                yield_simulation_candidate_ci_high=(
                    str(wet_yield.get("yield_ci_high", ""))
                    if yield_candidate_current
                    else ""
                ),
                yield_current=False,
                yield_value_current="",
                yield_ci_low_current="",
                yield_ci_high_current="",
                wet_pass_probability_current=False,
                wet_pass_probability_simulation_candidate_current=(
                    yield_candidate_current
                ),
                wet_pass_probability_simulation_candidate_value=(
                    str(wet_yield.get("wet_pass_probability_estimate", ""))
                    if yield_candidate_current
                    else ""
                ),
                wet_pass_probability_simulation_candidate_ci_low=(
                    str(wet_yield.get("wet_pass_probability_ci_low", ""))
                    if yield_candidate_current
                    else ""
                ),
                wet_pass_probability_simulation_candidate_ci_high=(
                    str(wet_yield.get("wet_pass_probability_ci_high", ""))
                    if yield_candidate_current
                    else ""
                ),
                wet_pass_probability_value_current="",
                wet_pass_probability_ci_low_current="",
                wet_pass_probability_ci_high_current="",
                yield_source_artifact_path_current=(
                    str(wet_yield.get("source_artifact_path", ""))
                    if yield_candidate_current
                    else ""
                ),
                route_score_current=_bool(winner.get("route_score_current")),
                production_ingestion_current=False,
                claim_value_review_status=_claim_status(
                    detection_valid=detection_valid,
                    yield_valid=yield_valid,
                    detection_current=detection_candidate_current,
                    yield_current=yield_candidate_current,
                    winner_current=_bool(winner.get("winner_current")),
                    fixture_not_evidence=fixture_not_evidence,
                ),
                next_required_evidence=_next_required_evidence(
                    detection_status=detection_status,
                    yield_status=yield_status,
                ),
                hard_fail_if=(
                    "yield_or_detection_probability_current_true_without_simulation_validated_value_rows"
                ),
                claim_boundary=SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_BOUNDARY,
            )
        )
    return rows, _guard_rows(rows)


def detection_claim_value_template_rows(
    winner_jrc_rows: list[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": str(row.get("route_candidate_id", "")),
            "route_geometry_family": str(row.get("route_geometry_family", "")),
            "detection_probability_estimate": "",
            "detection_probability_ci_low": "",
            "detection_probability_ci_high": "",
            "n_positive_control_events": "",
            "detector_probability_model_id": "",
            "threshold_policy_id": "",
            "controls_status": "controls_pass | controls_missing",
            "uncertainty_model": "",
            "pre_registered_rule_status": "pre_registered | missing",
            "source_geometry_match_level": "sidewall_specific | validated_transfer",
            "source_artifact_path": "",
            "source_artifact_sha256": "",
        }
        for row in winner_jrc_rows
    ]


def yield_claim_value_template_rows(
    winner_jrc_rows: list[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": str(row.get("route_candidate_id", "")),
            "route_geometry_family": str(row.get("route_geometry_family", "")),
            "yield_estimate": "",
            "yield_ci_low": "",
            "yield_ci_high": "",
            "wet_pass_probability_estimate": "",
            "wet_pass_probability_ci_low": "",
            "wet_pass_probability_ci_high": "",
            "n_wet_trials": "",
            "yield_model_id": "",
            "controls_status": "controls_pass | controls_missing",
            "uncertainty_model": "",
            "pre_registered_rule_status": "pre_registered | missing",
            "source_geometry_match_level": "sidewall_specific | validated_transfer",
            "source_artifact_path": "",
            "source_artifact_sha256": "",
        }
        for row in winner_jrc_rows
    ]


def _detection_validation_status(
    row: Mapping[str, Any],
    artifact_root: str | Path | None,
) -> str:
    if not row:
        return "detection_probability_value_missing"
    missing = _missing_fields(row, DETECTION_REQUIRED_FIELDS)
    if missing:
        return "detection_probability_value_rejected_missing_required_fields"
    if not _probability_interval_ok(
        row.get("detection_probability_estimate"),
        row.get("detection_probability_ci_low"),
        row.get("detection_probability_ci_high"),
    ):
        return "detection_probability_value_rejected_invalid_interval"
    if _int(row.get("n_positive_control_events")) < 3:
        return "detection_probability_value_rejected_insufficient_positive_controls"
    metadata_rejection = _common_metadata_rejection(row, artifact_root)
    if metadata_rejection:
        return f"detection_probability_value_rejected_{metadata_rejection}"
    return "detection_probability_value_accepted"


def _yield_validation_status(
    row: Mapping[str, Any],
    artifact_root: str | Path | None,
) -> str:
    if not row:
        return "yield_wet_value_bundle_missing"
    missing = _missing_fields(row, YIELD_REQUIRED_FIELDS)
    if missing:
        return "yield_wet_value_bundle_rejected_missing_required_fields"
    if not _probability_interval_ok(
        row.get("yield_estimate"), row.get("yield_ci_low"), row.get("yield_ci_high")
    ):
        return "yield_wet_value_bundle_rejected_invalid_yield_interval"
    if not _probability_interval_ok(
        row.get("wet_pass_probability_estimate"),
        row.get("wet_pass_probability_ci_low"),
        row.get("wet_pass_probability_ci_high"),
    ):
        return "yield_wet_value_bundle_rejected_invalid_wet_pass_interval"
    if _int(row.get("n_wet_trials")) < 3:
        return "yield_wet_value_bundle_rejected_insufficient_wet_trials"
    metadata_rejection = _common_metadata_rejection(row, artifact_root)
    if metadata_rejection:
        return f"yield_wet_value_bundle_rejected_{metadata_rejection}"
    return "yield_wet_value_bundle_accepted"


def _common_metadata_rejection(
    row: Mapping[str, Any],
    artifact_root: str | Path | None,
) -> str:
    if (
        str(row.get("controls_status", "")) != "controls_pass"
        or str(row.get("pre_registered_rule_status", "")) != "pre_registered"
        or str(row.get("source_geometry_match_level", ""))
        not in {"sidewall_specific", "validated_transfer"}
        or not bool(str(row.get("uncertainty_model", "")).strip())
    ):
        return "metadata_or_controls"
    if not _source_artifact_hash_ok(row, artifact_root):
        return "source_artifact_missing_or_hash_mismatch"
    return ""


def _source_artifact_hash_ok(
    row: Mapping[str, Any],
    artifact_root: str | Path | None,
) -> bool:
    expected_sha = str(row.get("source_artifact_sha256", "")).strip()
    if not _valid_sha256(expected_sha):
        return False
    source_path_text = str(row.get("source_artifact_path", "")).strip()
    if not source_path_text:
        return False
    source_path = Path(source_path_text)
    if not source_path.is_absolute() and artifact_root is not None:
        source_path = Path(artifact_root) / source_path
    if not source_path.exists():
        return False
    try:
        return sha256_file(source_path).lower() == expected_sha.lower()
    except OSError:
        return False


def _probability_interval_ok(value: Any, low: Any, high: Any) -> bool:
    value_f = _float_or_none(value)
    low_f = _float_or_none(low)
    high_f = _float_or_none(high)
    return (
        value_f is not None
        and low_f is not None
        and high_f is not None
        and 0.0 <= low_f <= value_f <= high_f <= 1.0
    )


def _claim_status(
    *,
    detection_valid: bool,
    yield_valid: bool,
    detection_current: bool,
    yield_current: bool,
    winner_current: bool,
    fixture_not_evidence: bool,
) -> str:
    if detection_current and yield_current and winner_current:
        return "simulation_yield_detection_values_ready_for_integrated_route_candidate_review"
    if detection_current and yield_current:
        return "simulation_yield_detection_values_ready_waiting_simulation_top_candidate"
    if detection_valid and yield_valid and fixture_not_evidence:
        return "fixture_yield_detection_value_path_passes_not_evidence"
    return "blocked_until_simulation_detection_and_yield_value_rows_accepted"


def _next_required_evidence(*, detection_status: str, yield_status: str) -> str:
    items = []
    if detection_status != "detection_probability_value_accepted":
        items.append(
            "simulation-derived detection probability value row with assumptions, "
            "controls, and uncertainty"
        )
    if yield_status != "yield_wet_value_bundle_accepted":
        items.append(
            "simulation-derived yield and wet-pass value row with assumptions, "
            "controls, and uncertainty"
        )
    return "; ".join(items) or "integrated route/yield/detection review"


def _guard_rows(
    rows: list[SidewallYieldDetectionClaimValueReviewRow],
) -> list[SidewallYieldDetectionClaimValueGuardRow]:
    detection_ready = bool(rows) and all(
        row.detection_probability_simulation_candidate_current for row in rows
    )
    yield_ready = bool(rows) and all(
        row.yield_simulation_candidate_current for row in rows
    )
    wet_ready = bool(rows) and all(
        row.wet_pass_probability_simulation_candidate_current for row in rows
    )
    specs = [
        (
            "detection_probability",
            False,
            "accepted simulation-derived detection probability value rows for every route",
            "detection_probability_true_without_value_rows",
        ),
        (
            "yield",
            False,
            "accepted simulation-derived yield value rows for every route",
            "yield_true_without_value_rows",
        ),
        (
            "wet_pass_probability",
            False,
            "accepted simulation-derived wet-pass value rows for every route",
            "wet_pass_probability_true_without_value_rows",
        ),
        (
            "simulation_detection_probability_candidate",
            detection_ready,
            "accepted simulation-derived detection probability value rows for every route",
            "simulation_detection_candidate_true_without_value_rows",
        ),
        (
            "simulation_yield_wet_candidate",
            yield_ready and wet_ready,
            "accepted simulation-derived yield and wet-pass value rows for every route",
            "simulation_yield_wet_candidate_true_without_value_rows",
        ),
        (
            "production_ingestion",
            False,
            "separate fabrication/production release after integrated review",
            "production_ingestion_true_from_claim_value_review",
        ),
    ]
    return [
        SidewallYieldDetectionClaimValueGuardRow(
            guard_row_id=f"YIELD-DETECTION-CLAIM-VALUE-GUARD-{target}",
            review_version=SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            activation_allowed_now=allowed,
            required_evidence_before_activation=required,
            hard_fail_if_activated_early=hard_fail,
            claim_boundary=SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_BOUNDARY,
        )
        for target, allowed, required, hard_fail in specs
    ]


def _missing_fields(row: Mapping[str, Any], required: tuple[str, ...]) -> list[str]:
    return [field for field in required if not str(row.get(field, "")).strip()]


def _valid_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(char in "0123456789abcdefABCDEF" for char in text)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int(value: Any) -> int:
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))


def _float_or_none(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value))
    except ValueError:
        return None
