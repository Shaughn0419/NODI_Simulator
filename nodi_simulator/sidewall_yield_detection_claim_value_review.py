"""Yield and detection-probability claim-value review for sidewall routes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_VERSION = (
    "sidewall_yield_detection_claim_value_review_v1"
)
SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_BOUNDARY = (
    "yield_detection_claim_value_review_requires_real_value_rows"
)

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
    "source_artifact_sha256",
)


@dataclass(frozen=True)
class SidewallYieldDetectionClaimValueReviewRow:
    claim_row_id: str
    review_version: str
    route_candidate_id: str
    route_geometry_family: str
    winner_current: bool
    JRC_current: bool
    detection_value_row_present: bool
    detection_value_validation_status: str
    detection_probability_current: bool
    detection_probability_value_current: str
    detection_probability_ci_low_current: str
    detection_probability_ci_high_current: str
    yield_value_row_present: bool
    yield_value_validation_status: str
    yield_current: bool
    yield_value_current: str
    yield_ci_low_current: str
    yield_ci_high_current: str
    wet_pass_probability_current: bool
    wet_pass_probability_value_current: str
    wet_pass_probability_ci_low_current: str
    wet_pass_probability_ci_high_current: str
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
        detection_status = _detection_validation_status(detection)
        yield_status = _yield_validation_status(wet_yield)
        detection_current = detection_status == "detection_probability_value_accepted"
        yield_current = yield_status == "yield_wet_value_bundle_accepted"
        rows.append(
            SidewallYieldDetectionClaimValueReviewRow(
                claim_row_id=f"YIELD-DETECTION-CLAIM-VALUE-{route_id}",
                review_version=SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_VERSION,
                route_candidate_id=route_id,
                route_geometry_family=str(winner.get("route_geometry_family", "")),
                winner_current=_bool(winner.get("winner_current")),
                JRC_current=_bool(winner.get("JRC_current")),
                detection_value_row_present=bool(detection),
                detection_value_validation_status=detection_status,
                detection_probability_current=detection_current,
                detection_probability_value_current=(
                    str(detection.get("detection_probability_estimate", ""))
                    if detection_current
                    else ""
                ),
                detection_probability_ci_low_current=(
                    str(detection.get("detection_probability_ci_low", ""))
                    if detection_current
                    else ""
                ),
                detection_probability_ci_high_current=(
                    str(detection.get("detection_probability_ci_high", ""))
                    if detection_current
                    else ""
                ),
                yield_value_row_present=bool(wet_yield),
                yield_value_validation_status=yield_status,
                yield_current=yield_current,
                yield_value_current=(
                    str(wet_yield.get("yield_estimate", "")) if yield_current else ""
                ),
                yield_ci_low_current=(
                    str(wet_yield.get("yield_ci_low", "")) if yield_current else ""
                ),
                yield_ci_high_current=(
                    str(wet_yield.get("yield_ci_high", "")) if yield_current else ""
                ),
                wet_pass_probability_current=yield_current,
                wet_pass_probability_value_current=(
                    str(wet_yield.get("wet_pass_probability_estimate", ""))
                    if yield_current
                    else ""
                ),
                wet_pass_probability_ci_low_current=(
                    str(wet_yield.get("wet_pass_probability_ci_low", ""))
                    if yield_current
                    else ""
                ),
                wet_pass_probability_ci_high_current=(
                    str(wet_yield.get("wet_pass_probability_ci_high", ""))
                    if yield_current
                    else ""
                ),
                route_score_current=_bool(winner.get("route_score_current")),
                production_ingestion_current=False,
                claim_value_review_status=_claim_status(
                    detection_current=detection_current,
                    yield_current=yield_current,
                    winner_current=_bool(winner.get("winner_current")),
                ),
                next_required_evidence=_next_required_evidence(
                    detection_status=detection_status,
                    yield_status=yield_status,
                ),
                hard_fail_if=(
                    "yield_or_detection_probability_current_true_without_real_validated_value_rows"
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
            "source_artifact_sha256": "",
        }
        for row in winner_jrc_rows
    ]


def _detection_validation_status(row: Mapping[str, Any]) -> str:
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
    if not _common_metadata_ok(row):
        return "detection_probability_value_rejected_metadata_or_controls"
    return "detection_probability_value_accepted"


def _yield_validation_status(row: Mapping[str, Any]) -> str:
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
    if not _common_metadata_ok(row):
        return "yield_wet_value_bundle_rejected_metadata_or_controls"
    return "yield_wet_value_bundle_accepted"


def _common_metadata_ok(row: Mapping[str, Any]) -> bool:
    return (
        str(row.get("controls_status", "")) == "controls_pass"
        and str(row.get("pre_registered_rule_status", "")) == "pre_registered"
        and str(row.get("source_geometry_match_level", ""))
        in {"sidewall_specific", "validated_transfer"}
        and _valid_sha256(row.get("source_artifact_sha256"))
        and bool(str(row.get("uncertainty_model", "")).strip())
    )


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
    detection_current: bool,
    yield_current: bool,
    winner_current: bool,
) -> str:
    if detection_current and yield_current and winner_current:
        return "yield_detection_values_ready_for_integrated_route_claim_review"
    if detection_current and yield_current:
        return "yield_detection_values_ready_waiting_winner_jrc"
    return "blocked_until_real_detection_and_yield_value_rows_accepted"


def _next_required_evidence(*, detection_status: str, yield_status: str) -> str:
    items = []
    if detection_status != "detection_probability_value_accepted":
        items.append("real detection probability value row with controls and uncertainty")
    if yield_status != "yield_wet_value_bundle_accepted":
        items.append("real yield and wet-pass value row with controls and uncertainty")
    return "; ".join(items) or "integrated route/yield/detection review"


def _guard_rows(
    rows: list[SidewallYieldDetectionClaimValueReviewRow],
) -> list[SidewallYieldDetectionClaimValueGuardRow]:
    detection_ready = bool(rows) and all(row.detection_probability_current for row in rows)
    yield_ready = bool(rows) and all(row.yield_current for row in rows)
    wet_ready = bool(rows) and all(row.wet_pass_probability_current for row in rows)
    specs = [
        (
            "detection_probability",
            detection_ready,
            "accepted detection probability value rows for every route",
            "detection_probability_true_without_value_rows",
        ),
        (
            "yield",
            yield_ready,
            "accepted yield value rows for every route",
            "yield_true_without_value_rows",
        ),
        (
            "wet_pass_probability",
            wet_ready,
            "accepted wet-pass value rows for every route",
            "wet_pass_probability_true_without_value_rows",
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
