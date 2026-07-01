"""Detector/blank calibration candidate panel for sidewall Package C routes.

The panel expands the small selected-annulus context into a multi-seed,
multi-wavelength diagnostic matrix and binds it to the current detector/blank
context rows. It is still a calibration candidate: it does not emit detection
probability, route score, winner, yield, or wet-pass claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping

from .sidewall_selected_annulus_context import (
    SidewallSelectedAnnulusContextRow,
    run_sidewall_selected_annulus_context,
)


SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_VERSION = (
    "sidewall_detector_blank_calibration_panel_v1"
)
SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY = (
    "detector_blank_calibration_panel_candidate_not_detection_probability_not_route_score"
)
PANEL_READY_STATUS = "detector_blank_calibration_panel_candidate_ready_not_probability"
PANEL_REVIEW_STATUS = "detector_blank_calibration_panel_needs_more_events_or_blank_guard"
PANEL_AGGREGATE_READY_STATUS = (
    "detector_blank_route_evidence_matrix_candidate_ready_not_probability"
)
PANEL_AGGREGATE_REVIEW_STATUS = (
    "detector_blank_route_evidence_matrix_needs_sidewall_blank_or_detector_validation"
)


@dataclass(frozen=True)
class SidewallDetectorBlankCalibrationPanelConfig:
    n_events_per_run: int = 64
    random_seeds: tuple[int, ...] = (601, 602, 603)
    wavelength_nm: tuple[int, ...] = (404, 660)
    min_selected_annulus_events_per_route: int = 50
    blank_false_positive_ub_threshold_per_trace: float = 0.001


@dataclass(frozen=True)
class SidewallDetectorBlankCalibrationPanelRow:
    panel_row_id: str
    panel_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    qch_flow_split_context_status: str
    geometry_match_level: str
    nearest_detection_width_nm: int
    nearest_detection_depth_nm: int
    geometry_distance_nm: int
    wavelength_nm: int
    random_seed: int
    n_events: int
    selected_annulus_n_events: int
    selected_annulus_n_detected: int
    selected_annulus_detection_context_rate: float
    selected_annulus_detection_rate_wilson_lb_context: float
    selected_annulus_detection_rate_wilson_ub_context: float
    min_blank_false_positive_wilson_ub_per_trace: float
    blank_guard_status: str
    detector_response_context_status: str
    optical_calibration_context_status: str
    selected_annulus_context_status: str
    panel_evidence_status: str
    panel_evidence_strength: float
    sidewall_specific_blank_trace_current: bool
    detector_response_validation_current: bool
    sidewall_specific_optical_calibration_current: bool
    detection_probability_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallDetectorBlankRouteEvidenceMatrixRow:
    matrix_row_id: str
    panel_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    panel_run_rows: int
    total_n_events: int
    total_selected_annulus_events: int
    total_selected_annulus_detected: int
    pooled_selected_annulus_detection_context_rate: float
    pooled_selected_annulus_detection_wilson_lb_context: float
    pooled_selected_annulus_detection_wilson_ub_context: float
    min_blank_false_positive_wilson_ub_per_trace: float
    blank_guard_status: str
    detector_response_context_status: str
    optical_calibration_context_status: str
    qch_flow_split_context_status: str
    calibration_evidence_strength: float
    route_evidence_matrix_status: str
    next_required_evidence: str
    sidewall_specific_blank_trace_current: bool
    detector_response_validation_current: bool
    sidewall_specific_optical_calibration_current: bool
    detection_probability_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_detector_blank_calibration_panel(
    *,
    detector_blank_context_rows: list[Mapping[str, Any]],
    config: SidewallDetectorBlankCalibrationPanelConfig | None = None,
) -> tuple[
    list[SidewallDetectorBlankCalibrationPanelRow],
    list[SidewallDetectorBlankRouteEvidenceMatrixRow],
]:
    """Run and aggregate the sidewall detector/blank calibration candidate panel."""
    panel_config = config or SidewallDetectorBlankCalibrationPanelConfig()
    context_by_case = {
        str(row.get("source_case_id", "")): row for row in detector_blank_context_rows
    }
    expanded_rows: list[SidewallSelectedAnnulusContextRow] = []
    for seed in panel_config.random_seeds:
        for wavelength in panel_config.wavelength_nm:
            expanded_rows.extend(
                run_sidewall_selected_annulus_context(
                    n_events=panel_config.n_events_per_run,
                    random_seed=seed,
                    wavelength_nm=wavelength,
                )
            )

    panel_rows: list[SidewallDetectorBlankCalibrationPanelRow] = []
    for expanded in expanded_rows:
        context = context_by_case.get(expanded.case_id, {})
        if not context:
            continue
        blank_ub = _float_value(
            context.get("min_blank_false_positive_wilson_ub_per_trace")
        )
        wilson_lb, wilson_ub = _wilson_interval(
            expanded.selected_annulus_n_detected,
            expanded.selected_annulus_n_events,
        )
        blank_guard = _blank_guard_status(
            blank_ub,
            panel_config.blank_false_positive_ub_threshold_per_trace,
            str(context.get("blank_false_positive_context_status", "")),
        )
        selected_status = (
            "expanded_selected_annulus_panel_available_not_probability"
            if expanded.selected_annulus_n_events > 0
            else "expanded_selected_annulus_panel_empty"
        )
        detector_status = str(context.get("detector_response_context_status", ""))
        optical_status = str(context.get("optical_calibration_context_status", ""))
        panel_status = _panel_status(
            selected_annulus_n=expanded.selected_annulus_n_events,
            blank_guard_status=blank_guard,
            detector_response_context_status=detector_status,
        )
        strength = _panel_strength(
            selected_annulus_n=expanded.selected_annulus_n_events,
            wilson_lb=wilson_lb,
            blank_ub=blank_ub,
            detector_response_context_status=detector_status,
        )
        panel_rows.append(
            SidewallDetectorBlankCalibrationPanelRow(
                panel_row_id=(
                    f"DB-CAL-PANEL-{context.get('route_candidate_id', '')}-"
                    f"{expanded.wavelength_nm}-{expanded.random_seed}"
                ),
                panel_version=SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_VERSION,
                route_candidate_id=str(context.get("route_candidate_id", "")),
                route_key=str(context.get("route_key", "")),
                source_case_id=expanded.case_id,
                qch_sidecar_id=str(context.get("qch_sidecar_id", "")),
                qch_flow_split_context_status=str(
                    context.get("qch_flow_split_context_status", "")
                ),
                geometry_match_level=str(context.get("geometry_match_level", "")),
                nearest_detection_width_nm=_int_value(
                    context.get("nearest_detection_width_nm")
                ),
                nearest_detection_depth_nm=_int_value(
                    context.get("nearest_detection_depth_nm")
                ),
                geometry_distance_nm=_int_value(context.get("geometry_distance_nm")),
                wavelength_nm=expanded.wavelength_nm,
                random_seed=expanded.random_seed,
                n_events=expanded.n_events,
                selected_annulus_n_events=expanded.selected_annulus_n_events,
                selected_annulus_n_detected=expanded.selected_annulus_n_detected,
                selected_annulus_detection_context_rate=(
                    expanded.selected_annulus_detection_context_rate
                ),
                selected_annulus_detection_rate_wilson_lb_context=wilson_lb,
                selected_annulus_detection_rate_wilson_ub_context=wilson_ub,
                min_blank_false_positive_wilson_ub_per_trace=blank_ub,
                blank_guard_status=blank_guard,
                detector_response_context_status=detector_status,
                optical_calibration_context_status=optical_status,
                selected_annulus_context_status=selected_status,
                panel_evidence_status=panel_status,
                panel_evidence_strength=strength,
                sidewall_specific_blank_trace_current=False,
                detector_response_validation_current=False,
                sidewall_specific_optical_calibration_current=False,
                detection_probability_current=False,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                claim_boundary=SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY,
            )
        )

    matrix_rows = _matrix_rows(panel_rows, panel_config)
    return (
        sorted(panel_rows, key=lambda row: row.panel_row_id),
        sorted(matrix_rows, key=lambda row: row.route_candidate_id),
    )


def detector_blank_calibration_promotion_update_rows(
    matrix_rows: list[SidewallDetectorBlankRouteEvidenceMatrixRow],
) -> list[dict[str, Any]]:
    route_ids = ";".join(sorted({row.route_candidate_id for row in matrix_rows}))
    return [
        {
            "target_ledger_lane": "selected_annulus_detection_context",
            "covered_route_candidate_ids": route_ids,
            "previous_status": "selected_annulus_context_available_small_n_not_probability",
            "new_context_status": "expanded_selected_annulus_panel_available_not_probability",
            "target_claim_current": False,
            "blocked_promotion": "detection_probability;route_score;winner",
            "hard_fail_if": "expanded_selected_annulus_panel_promoted_to_probability",
            "next_required_evidence": (
                "detector response validation and sidewall-specific blank transfer model"
            ),
            "claim_boundary": SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY,
        },
        {
            "target_ledger_lane": "blank_false_positive_trace",
            "covered_route_candidate_ids": route_ids,
            "previous_status": "nearest_blank_context_available_not_sidewall_specific_validation",
            "new_context_status": "nearest_blank_guard_bound_to_panel_not_sidewall_specific",
            "target_claim_current": False,
            "blocked_promotion": "detection_probability;route_score;winner;yield",
            "hard_fail_if": "nearest_blank_guard_promoted_to_sidewall_blank_fpr",
            "next_required_evidence": (
                "sidewall-specific blank traces or validated transferable blank false-positive model"
            ),
            "claim_boundary": SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY,
        },
        {
            "target_ledger_lane": "detector_response_bridge",
            "covered_route_candidate_ids": route_ids,
            "previous_status": "detector_identity_context_available_not_sidewall_response_validation",
            "new_context_status": "detector_response_panel_candidate_not_sidewall_calibrated",
            "target_claim_current": False,
            "blocked_promotion": "detection_probability;route_score;winner;yield",
            "hard_fail_if": "detector_panel_candidate_promoted_to_response_validation",
            "next_required_evidence": (
                "detector operator, ROI/slit throughput, and standard-particle calibration consuming sidewall reference field"
            ),
            "claim_boundary": SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY,
        },
    ]


def _matrix_rows(
    panel_rows: list[SidewallDetectorBlankCalibrationPanelRow],
    config: SidewallDetectorBlankCalibrationPanelConfig,
) -> list[SidewallDetectorBlankRouteEvidenceMatrixRow]:
    rows: list[SidewallDetectorBlankRouteEvidenceMatrixRow] = []
    route_ids = sorted({row.route_candidate_id for row in panel_rows})
    for route_id in route_ids:
        group = [row for row in panel_rows if row.route_candidate_id == route_id]
        if not group:
            continue
        first = group[0]
        total_selected = sum(row.selected_annulus_n_events for row in group)
        total_detected = sum(row.selected_annulus_n_detected for row in group)
        total_events = sum(row.n_events for row in group)
        pooled_rate = _ratio(total_detected, total_selected)
        pooled_lb, pooled_ub = _wilson_interval(total_detected, total_selected)
        blank_ub = min(
            (
                row.min_blank_false_positive_wilson_ub_per_trace
                for row in group
                if math.isfinite(row.min_blank_false_positive_wilson_ub_per_trace)
            ),
            default=math.nan,
        )
        blank_guard = _blank_guard_status(
            blank_ub,
            config.blank_false_positive_ub_threshold_per_trace,
            first.blank_guard_status,
        )
        strength = _panel_strength(
            selected_annulus_n=total_selected,
            wilson_lb=pooled_lb,
            blank_ub=blank_ub,
            detector_response_context_status=first.detector_response_context_status,
        )
        status = (
            PANEL_AGGREGATE_READY_STATUS
            if total_selected >= config.min_selected_annulus_events_per_route
            and blank_guard.startswith("nearest_blank_guard_finite")
            else PANEL_AGGREGATE_REVIEW_STATUS
        )
        rows.append(
            SidewallDetectorBlankRouteEvidenceMatrixRow(
                matrix_row_id=f"DB-CAL-MATRIX-{route_id}",
                panel_version=SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_VERSION,
                route_candidate_id=route_id,
                route_key=first.route_key,
                source_case_id=first.source_case_id,
                qch_sidecar_id=first.qch_sidecar_id,
                panel_run_rows=len(group),
                total_n_events=total_events,
                total_selected_annulus_events=total_selected,
                total_selected_annulus_detected=total_detected,
                pooled_selected_annulus_detection_context_rate=pooled_rate,
                pooled_selected_annulus_detection_wilson_lb_context=pooled_lb,
                pooled_selected_annulus_detection_wilson_ub_context=pooled_ub,
                min_blank_false_positive_wilson_ub_per_trace=blank_ub,
                blank_guard_status=blank_guard,
                detector_response_context_status=first.detector_response_context_status,
                optical_calibration_context_status=first.optical_calibration_context_status,
                qch_flow_split_context_status=first.qch_flow_split_context_status,
                calibration_evidence_strength=strength,
                route_evidence_matrix_status=status,
                next_required_evidence=(
                    "sidewall-specific blank traces, detector response calibration, "
                    "and wet/surface validation before probability or route claims"
                ),
                sidewall_specific_blank_trace_current=False,
                detector_response_validation_current=False,
                sidewall_specific_optical_calibration_current=False,
                detection_probability_current=False,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                claim_boundary=SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY,
            )
        )
    return rows


def _panel_status(
    *,
    selected_annulus_n: int,
    blank_guard_status: str,
    detector_response_context_status: str,
) -> str:
    if selected_annulus_n <= 0:
        return "blocked_empty_selected_annulus_panel"
    if not blank_guard_status.startswith("nearest_blank_guard_finite"):
        return PANEL_REVIEW_STATUS
    if "validation" not in detector_response_context_status:
        return PANEL_REVIEW_STATUS
    return PANEL_READY_STATUS


def _blank_guard_status(
    blank_ub: float,
    threshold: float,
    source_status: str,
) -> str:
    if not math.isfinite(blank_ub):
        return "blank_guard_missing"
    suffix = "below_threshold" if blank_ub <= threshold else "above_threshold_review"
    if "nearest" in source_status or "not_sidewall" in source_status:
        return f"nearest_blank_guard_finite_{suffix}_not_sidewall_specific"
    return f"blank_guard_finite_{suffix}"


def _panel_strength(
    *,
    selected_annulus_n: int,
    wilson_lb: float,
    blank_ub: float,
    detector_response_context_status: str,
) -> float:
    if selected_annulus_n <= 0 or not math.isfinite(wilson_lb):
        return 0.0
    blank_penalty = 0.5 if math.isfinite(blank_ub) else 0.0
    detector_penalty = 0.5 if "validation" in detector_response_context_status else 0.25
    n_factor = min(1.0, selected_annulus_n / 100.0)
    return max(0.0, min(1.0, wilson_lb * n_factor * blank_penalty * detector_penalty))


def _wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return math.nan, math.nan
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    margin = (
        z
        * math.sqrt((p * (1.0 - p) / total) + (z * z / (4.0 * total * total)))
        / denom
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def _ratio(numerator: int, denominator: int) -> float:
    return float(numerator) / float(denominator) if denominator else math.nan


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _int_value(value: Any) -> int:
    numeric = _float_value(value)
    return int(numeric) if math.isfinite(numeric) else 0
