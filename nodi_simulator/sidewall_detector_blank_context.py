"""Detector/blank context refresh for sidewall route candidates.

The refresh joins the current wet/optical detection context with sidewall
selected-annulus and qch-ledger updates. It records what detector/blank evidence
is now available as context, without converting nearest-geometry blank evidence
or small-N selected-annulus rows into a detection probability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping


SIDEWALL_DETECTOR_BLANK_CONTEXT_VERSION = (
    "sidewall_detector_blank_context_refresh_w500_d900_v1"
)
SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY = (
    "detector_blank_context_not_detector_validation_not_detection_probability"
)


@dataclass(frozen=True)
class SidewallDetectorBlankContextRow:
    route_candidate_id: str
    detector_blank_context_version: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    geometry_match_level: str
    nearest_detection_width_nm: int
    nearest_detection_depth_nm: int
    geometry_distance_nm: int
    min_blank_false_positive_wilson_ub_per_trace: float
    source_detection_context_status: str
    source_optical_context_status: str
    source_wet_context_status: str
    selected_annulus_context_status: str
    selected_annulus_n_events: int
    selected_annulus_n_detected: int
    selected_annulus_context_rate: float
    qch_flow_split_context_status: str
    blank_false_positive_context_status: str
    detector_response_context_status: str
    optical_calibration_context_status: str
    detector_blank_lane_status: str
    detector_response_validation_current: bool
    sidewall_specific_blank_trace_current: bool
    sidewall_specific_optical_calibration_current: bool
    detection_probability_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_detector_blank_context_rows(
    wet_context_rows: list[Mapping[str, Any]],
    selected_annulus_rows: list[Mapping[str, Any]],
    promotion_lane_rows: list[Mapping[str, Any]],
    optical_readiness_rows: list[Mapping[str, Any]],
) -> list[SidewallDetectorBlankContextRow]:
    selected_by_case = {
        str(row.get("case_id", "")): row for row in selected_annulus_rows
    }
    qch_by_route = {
        str(row.get("route_candidate_id", "")): str(row.get("current_status", ""))
        for row in promotion_lane_rows
        if str(row.get("evidence_lane", "")) == "flow_split_qch"
    }
    optical_by_lane = {
        str(row.get("evidence_lane", "")): str(row.get("current_status", ""))
        for row in optical_readiness_rows
    }
    output: list[SidewallDetectorBlankContextRow] = []
    for row in wet_context_rows:
        source_case_id = str(row.get("source_case_id", ""))
        selected = selected_by_case.get(source_case_id, {})
        selected_status = str(
            selected.get(
                "selected_annulus_context_status",
                "selected_annulus_context_missing",
            )
        )
        blank_ub = _float_value(row.get("min_blank_false_positive_wilson_ub_per_trace"))
        geometry_match_level = str(row.get("geometry_match_level", ""))
        blank_context_status = _blank_context_status(
            blank_ub=blank_ub,
            geometry_match_level=geometry_match_level,
        )
        detector_response_status = _detector_response_status(
            optical_by_lane.get("detector_response_bridge", "")
        )
        optical_calibration_status = _optical_calibration_status(
            optical_by_lane.get("blank_channel_reference_amplitude_phase", "")
        )
        lane_status = _lane_status(
            selected_status=selected_status,
            blank_context_status=blank_context_status,
            detector_response_status=detector_response_status,
        )
        output.append(
            SidewallDetectorBlankContextRow(
                route_candidate_id=str(row.get("route_candidate_id", "")),
                detector_blank_context_version=SIDEWALL_DETECTOR_BLANK_CONTEXT_VERSION,
                route_key=str(row.get("route_key", "")),
                source_case_id=source_case_id,
                qch_sidecar_id=str(row.get("qch_sidecar_id", "")),
                geometry_match_level=geometry_match_level,
                nearest_detection_width_nm=_int_value(row.get("nearest_detection_width_nm")),
                nearest_detection_depth_nm=_int_value(row.get("nearest_detection_depth_nm")),
                geometry_distance_nm=_int_value(row.get("geometry_distance_nm")),
                min_blank_false_positive_wilson_ub_per_trace=blank_ub,
                source_detection_context_status=str(row.get("detection_context_status", "")),
                source_optical_context_status=str(row.get("optical_context_status", "")),
                source_wet_context_status=str(row.get("wet_context_status", "")),
                selected_annulus_context_status=selected_status,
                selected_annulus_n_events=_int_value(selected.get("selected_annulus_n_events")),
                selected_annulus_n_detected=_int_value(selected.get("selected_annulus_n_detected")),
                selected_annulus_context_rate=_float_value(
                    selected.get("selected_annulus_context_rate")
                ),
                qch_flow_split_context_status=qch_by_route.get(
                    str(row.get("route_candidate_id", "")),
                    "qch_flow_split_context_missing",
                ),
                blank_false_positive_context_status=blank_context_status,
                detector_response_context_status=detector_response_status,
                optical_calibration_context_status=optical_calibration_status,
                detector_blank_lane_status=lane_status,
                detector_response_validation_current=False,
                sidewall_specific_blank_trace_current=False,
                sidewall_specific_optical_calibration_current=False,
                detection_probability_current=False,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                claim_boundary=SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY,
            )
        )
    return sorted(output, key=lambda item: item.route_candidate_id)


def detector_blank_promotion_update_rows(
    rows: list[SidewallDetectorBlankContextRow],
) -> list[dict[str, Any]]:
    if not rows:
        return []
    return [
        {
            "target_ledger_lane": "blank_false_positive_trace",
            "previous_status": "blank_trace_validation_missing_for_sidewall_geometry",
            "new_context_status": (
                "nearest_blank_context_available_not_sidewall_specific_validation"
            ),
            "target_claim_current": False,
            "blocked_promotion": "detection_probability;route_score;winner;yield",
            "hard_fail_if": "nearest_blank_context_promoted_to_detection_probability",
            "next_required_evidence": (
                "sidewall-specific blank traces or validated transferable blank false-positive model"
            ),
            "claim_boundary": SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY,
        },
        {
            "target_ledger_lane": "detector_response_bridge",
            "previous_status": "not_detector_response_validation",
            "new_context_status": (
                "detector_identity_context_available_not_sidewall_response_validation"
            ),
            "target_claim_current": False,
            "blocked_promotion": "detection_probability;route_score;winner;yield",
            "hard_fail_if": "detector_identity_context_promoted_to_response_validation",
            "next_required_evidence": (
                "detector operator, ROI/slit throughput, and standard-particle calibration consuming sidewall reference field"
            ),
            "claim_boundary": SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY,
        },
    ]


def _blank_context_status(*, blank_ub: float, geometry_match_level: str) -> str:
    if not math.isfinite(blank_ub):
        return "blank_false_positive_context_missing"
    if geometry_match_level.startswith("exact_width_depth"):
        return "exact_width_depth_blank_context_not_sidewall_specific_validation"
    return "nearest_blank_context_available_not_sidewall_specific_validation"


def _detector_response_status(readiness_status: str) -> str:
    if readiness_status == "not_detector_response_validation":
        return "detector_identity_context_available_not_sidewall_response_validation"
    return readiness_status or "detector_response_context_missing"


def _optical_calibration_status(readiness_status: str) -> str:
    if readiness_status == "synthetic_seed_available_not_experimental":
        return "synthetic_reference_seed_available_not_blank_channel_calibration"
    return readiness_status or "optical_calibration_context_missing"


def _lane_status(
    *,
    selected_status: str,
    blank_context_status: str,
    detector_response_status: str,
) -> str:
    if "available_small_n_not_probability" not in selected_status:
        return "blocked_selected_annulus_context_missing"
    if blank_context_status == "blank_false_positive_context_missing":
        return "blocked_blank_false_positive_context_missing"
    if "validation" not in detector_response_status:
        return "blocked_detector_response_context_missing"
    return "detector_blank_context_available_not_probability"


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _int_value(value: Any) -> int:
    numeric = _float_value(value)
    return int(numeric) if math.isfinite(numeric) else 0
