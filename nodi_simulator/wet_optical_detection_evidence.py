"""Wet, optical, and detection evidence context for sidewall route candidates.

This module binds existing Tsuyama-aligned detection lane artifacts to Package C
route candidates. The output is evidence context for the downstream branches; it
does not promote any route to final route_score, winner, wet yield, or detection
probability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Any, Mapping


WET_OPTICAL_DETECTION_EVIDENCE_VERSION = (
    "wet_optical_detection_evidence_context_from_tsuyama_lane_v1"
)
WET_OPTICAL_DETECTION_EVIDENCE_CLAIM_BOUNDARY = (
    "wet_optical_detection_context_not_final_detection_not_yield_not_route_score"
)


@dataclass(frozen=True)
class WetOpticalDetectionEvidenceContextRow:
    route_candidate_id: str
    evidence_context_version: str
    qch_sidecar_id: str
    route_key: str
    source_case_id: str
    source_width_nm: int
    source_depth_nm: int
    sidewall_deg_comsol: float
    route_decision_candidate_metric: float
    geometry_match_level: str
    nearest_detection_width_nm: int
    nearest_detection_depth_nm: int
    geometry_distance_nm: int
    detection_context_status: str
    optical_context_status: str
    wet_context_status: str
    detection_context_rows: int
    feasible_context_rows: int
    ev_panel_context_rows: int
    ranking_context_rows: int
    max_gold_detection_rate: float
    max_gold_stable_detection_rate: float
    min_blank_false_positive_wilson_ub_per_trace: float
    best_ev_weighted_stable_detection_rate: float
    detection_context_weight: float
    wet_context_weight: float
    route_detection_context_candidate_metric: float
    selected_annulus_context_status: str
    sidewall_specific_optical_solver_current: bool
    sidewall_specific_wet_evidence_current: bool
    detection_probability_current: bool
    yield_current: bool
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_wet_optical_detection_context_rows(
    route_candidate_rows: list[Mapping[str, Any]],
    gold_rows: list[Mapping[str, Any]],
    blank_rows: list[Mapping[str, Any]],
    feasible_rows: list[Mapping[str, Any]],
    ev_panel_rows: list[Mapping[str, Any]],
    ranking_rows: list[Mapping[str, Any]],
) -> list[WetOpticalDetectionEvidenceContextRow]:
    """Build context rows by mapping route candidates to existing detection evidence."""
    output: list[WetOpticalDetectionEvidenceContextRow] = []
    for route in route_candidate_rows:
        source_case_id = str(route.get("source_case_id", ""))
        source_width_nm = _parse_named_int(source_case_id, "W")
        source_depth_nm = _parse_named_int(source_case_id, "D")
        sidewall_deg_comsol = _parse_theta(source_case_id)
        nearest_width, nearest_depth, distance = _nearest_width_depth(
            source_width_nm, source_depth_nm, gold_rows + feasible_rows + ev_panel_rows
        )
        match_level = (
            "exact_width_depth_context_not_sidewall_specific"
            if distance == 0
            else "nearest_width_depth_context_only"
        )
        gold_context = _filter_width_depth(gold_rows, nearest_width, nearest_depth)
        feasible_context = _filter_width_depth(feasible_rows, nearest_width, nearest_depth)
        ev_context = _filter_width_depth(ev_panel_rows, nearest_width, nearest_depth)
        ranking_context = list(ranking_rows)

        max_gold_detection = _max_float(gold_context, "detection_rate")
        max_gold_stable = _max_float(gold_context, "stable_detection_rate")
        min_blank_ub = _min_blank_wilson(blank_rows)
        best_ev_stable = _max_float(ev_context, "weighted_stable_detection_rate")
        detection_weight = _detection_context_weight(
            match_level=match_level,
            gold_count=len(gold_context),
            blank_ub=min_blank_ub,
        )
        wet_weight = 0.25 if ev_context else 0.0
        route_metric = _float_value(route.get("route_decision_candidate_metric"))
        context_metric = route_metric * detection_weight * wet_weight
        output.append(
            WetOpticalDetectionEvidenceContextRow(
                route_candidate_id=str(route.get("route_candidate_id", "")),
                evidence_context_version=WET_OPTICAL_DETECTION_EVIDENCE_VERSION,
                qch_sidecar_id=str(route.get("qch_sidecar_id", "")),
                route_key=str(route.get("route_key", "")),
                source_case_id=source_case_id,
                source_width_nm=source_width_nm,
                source_depth_nm=source_depth_nm,
                sidewall_deg_comsol=sidewall_deg_comsol,
                route_decision_candidate_metric=route_metric,
                geometry_match_level=match_level,
                nearest_detection_width_nm=nearest_width,
                nearest_detection_depth_nm=nearest_depth,
                geometry_distance_nm=distance,
                detection_context_status=_detection_context_status(
                    match_level, len(gold_context), min_blank_ub
                ),
                optical_context_status=(
                    "paper_aligned_reference_context_available_not_sidewall_optical_solver"
                    if gold_context
                    else "optical_context_missing"
                ),
                wet_context_status=(
                    "ev_weighted_panel_surrogate_context_available_not_wet_experiment"
                    if ev_context
                    else "wet_ev_panel_context_missing"
                ),
                detection_context_rows=len(gold_context),
                feasible_context_rows=len(feasible_context),
                ev_panel_context_rows=len(ev_context),
                ranking_context_rows=len(ranking_context),
                max_gold_detection_rate=max_gold_detection,
                max_gold_stable_detection_rate=max_gold_stable,
                min_blank_false_positive_wilson_ub_per_trace=min_blank_ub,
                best_ev_weighted_stable_detection_rate=best_ev_stable,
                detection_context_weight=detection_weight,
                wet_context_weight=wet_weight,
                route_detection_context_candidate_metric=context_metric,
                selected_annulus_context_status=_selected_annulus_status(ranking_context),
                sidewall_specific_optical_solver_current=False,
                sidewall_specific_wet_evidence_current=False,
                detection_probability_current=False,
                yield_current=False,
                route_score_current=False,
                winner_current=False,
                JRC_current=False,
                claim_boundary=WET_OPTICAL_DETECTION_EVIDENCE_CLAIM_BOUNDARY,
            )
        )
    return sorted(
        output,
        key=lambda row: (-row.route_detection_context_candidate_metric, row.route_candidate_id),
    )


def _parse_named_int(source_case_id: str, name: str) -> int:
    match = re.search(rf"{re.escape(name)}(\d+)", source_case_id)
    return int(match.group(1)) if match else 0


def _parse_theta(source_case_id: str) -> float:
    match = re.search(r"theta(\d+(?:p\d+)?)", source_case_id)
    if not match:
        return math.nan
    return float(match.group(1).replace("p", "."))


def _nearest_width_depth(
    source_width_nm: int,
    source_depth_nm: int,
    rows: list[Mapping[str, Any]],
) -> tuple[int, int, int]:
    candidates: set[tuple[int, int]] = set()
    for row in rows:
        width = int(_float_value(row.get("width_nm")))
        depth = int(_float_value(row.get("depth_nm")))
        if width > 0 and depth > 0:
            candidates.add((width, depth))
    if not candidates:
        return 0, 0, 0
    best = min(
        candidates,
        key=lambda item: (
            abs(item[0] - source_width_nm) + abs(item[1] - source_depth_nm),
            abs(item[0] - source_width_nm),
            abs(item[1] - source_depth_nm),
            item[0],
            item[1],
        ),
    )
    distance = abs(best[0] - source_width_nm) + abs(best[1] - source_depth_nm)
    return best[0], best[1], distance


def _filter_width_depth(
    rows: list[Mapping[str, Any]], width_nm: int, depth_nm: int
) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if int(_float_value(row.get("width_nm"))) == width_nm
        and int(_float_value(row.get("depth_nm"))) == depth_nm
    ]


def _detection_context_weight(
    *, match_level: str, gold_count: int, blank_ub: float
) -> float:
    if gold_count <= 0:
        return 0.0
    if not math.isfinite(blank_ub):
        return 0.0
    if match_level.startswith("exact_width_depth"):
        return 0.50
    return 0.25


def _detection_context_status(
    match_level: str, gold_count: int, blank_ub: float
) -> str:
    if gold_count <= 0:
        return "tsuyama_detection_context_missing"
    if not math.isfinite(blank_ub):
        return "tsuyama_detection_context_without_blank_guard"
    if match_level.startswith("exact_width_depth"):
        return "tsuyama_detection_lane_exact_width_depth_context_not_sidewall_specific"
    return "tsuyama_detection_lane_nearest_geometry_context_not_sidewall_specific"


def _min_blank_wilson(blank_rows: list[Mapping[str, Any]]) -> float:
    values = [
        _float_value(row.get("blank_false_positive_wilson_ub_per_trace"))
        for row in blank_rows
        if str(row.get("blank_stage", "")).lower() in {"final", "empirical_summary"}
    ]
    finite_values = [value for value in values if math.isfinite(value)]
    if finite_values:
        return min(finite_values)
    all_values = [
        _float_value(row.get("blank_false_positive_wilson_ub_per_trace"))
        for row in blank_rows
    ]
    finite_all = [value for value in all_values if math.isfinite(value)]
    return min(finite_all) if finite_all else math.nan


def _selected_annulus_status(rows: list[Mapping[str, Any]]) -> str:
    statuses = {
        str(row.get("selected_annulus_lens_status", "")).strip()
        for row in rows
        if str(row.get("selected_annulus_lens_status", "")).strip()
    }
    if not statuses:
        return "selected_annulus_context_missing"
    if statuses == {"missing_selected_annulus_columns_rerun_ev_panel_required"}:
        return "selected_annulus_context_missing_rerun_required"
    return ";".join(sorted(statuses))


def _max_float(rows: list[Mapping[str, Any]], key: str) -> float:
    values = [_float_value(row.get(key)) for row in rows]
    finite_values = [value for value in values if math.isfinite(value)]
    return max(finite_values) if finite_values else math.nan


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
