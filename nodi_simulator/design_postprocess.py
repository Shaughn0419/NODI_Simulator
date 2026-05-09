"""Package-local EV ensemble design postprocessing diagnostics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any

import numpy as np

from .design_metrics import (
    clamp01,
    design_metric_match_key,
    finite_float_or_none,
    get_result_metric_value,
    write_result_metric_payload,
)


EV_DESIGN_POSTPROCESS_FIELDS = (
    "ev_member_count",
    "ev_score_min",
    "ev_score_p10",
    "ev_score_median",
    "ev_gate_pass_fraction",
    "ev_min_margin_z",
    "ev_max_phase_flip_fraction",
    "au20_equivalent_peak_ratio",
    "reference_design_score",
    "reference_operating_band",
    "fluidic_practicality_penalty",
    "EV_contaminant_overlap_fraction",
    "route_disagreement_flag",
    "reference_route_consensus_status",
    "physics_model_disagreement_flag",
    "physics_model_consensus_status",
    "EV_design_detector_caution_flag",
    "EV_design_detector_caution_summary",
    "EV_design_detector_resolved_pass_fraction",
    "final_EV_design_score",
    "EV_design_recommendation_band",
    "EV_design_recommendation_band_relative",
    "EV_design_recommendation_band_absolute",
    "EV_design_claim_text",
    "EV_design_claim_allowed_text",
    "EV_design_claim_forbidden_text",
    "EV_design_claim_boundary_status",
    "EV_design_hard_blocker_flag",
    "EV_design_primary_blockers",
    "EV_design_group_key",
)

_EV_GATE_PASS_FRACTION_FIELD = "ev_gate_pass_fraction"


def compute_reference_route_consensus(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return route-consensus diagnostics for one design group."""
    grouped_rows = list(rows)
    route_fields = (
        "reference_model",
        "reference_route",
        "reference_solver_route",
        "detector_forward_model",
    )
    unique_by_field = {
        field: _unique_values(grouped_rows, field) for field in route_fields
    }
    disagreement = any(len(values) > 1 for values in unique_by_field.values())
    return {
        "route_disagreement_flag": bool(disagreement),
        "reference_route_consensus_status": (
            "route_disagreement_requires_review"
            if disagreement
            else "route_consensus_within_design_key"
        ),
    }


def compute_physics_model_consensus(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return model-consensus diagnostics for one design group."""
    grouped_rows = list(rows)
    model_fields = (
        "particle_optical_model",
        "shape_model",
        "particle_induced_channel_perturbation_model",
        "channel_particle_coupling_model",
    )
    unique_by_field = {
        field: _unique_values(grouped_rows, field) for field in model_fields
    }
    disagreement = any(len(values) > 1 for values in unique_by_field.values())
    return {
        "physics_model_disagreement_flag": bool(disagreement),
        "physics_model_consensus_status": (
            "physics_model_disagreement_requires_review"
            if disagreement
            else "physics_model_consensus_within_design_key"
        ),
    }


def compute_pareto_front(rows: Iterable[Mapping[str, Any]]) -> list[bool]:
    """Compute a simple score-vs-fluidic-penalty Pareto mask."""
    grouped_rows = list(rows)
    points = [
        (
            finite_float_or_none(
                get_result_metric_value(row, "final_EV_design_score")
            )
            or finite_float_or_none(
                get_result_metric_value(row, "final_engineering_score")
            )
            or 0.0,
            finite_float_or_none(
                get_result_metric_value(row, "fluidic_practicality_penalty")
            )
            or 1.0,
        )
        for row in grouped_rows
    ]
    mask: list[bool] = []
    for idx, (score, penalty) in enumerate(points):
        dominated = False
        for other_idx, (other_score, other_penalty) in enumerate(points):
            if idx == other_idx:
                continue
            if (
                other_score >= score
                and other_penalty <= penalty
                and (other_score > score or other_penalty < penalty)
            ):
                dominated = True
                break
        mask.append(not dominated)
    return mask


def compute_ev_ensemble_design_score(
    results: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Compute one P0.10 EV design payload per geometry/reference group."""
    rows = list(results)
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if _is_ev_design_row(row):
            groups[design_metric_match_key(row)].append(row)
    return [
        _build_ev_group_payload(group_key, group_rows)
        for group_key, group_rows in groups.items()
    ]


def attach_ev_design_postprocess(
    results: Iterable[MutableMapping[str, Any]],
) -> list[MutableMapping[str, Any]]:
    """Attach EV ensemble design diagnostics to each row."""
    rows = list(results)
    groups: dict[tuple[str, ...], list[MutableMapping[str, Any]]] = defaultdict(list)
    for row in rows:
        write_result_metric_payload(row, _default_ev_postprocess_payload(row))
        if _is_ev_design_row(row):
            groups[design_metric_match_key(row)].append(row)

    for group_key, group_rows in groups.items():
        payload = _build_ev_group_payload(group_key, group_rows)
        for row in group_rows:
            write_result_metric_payload(row, payload)
    return rows


def generate_claim_text(payload: Mapping[str, Any]) -> str:
    """Generate a bounded design-claim text from an EV postprocess payload."""
    if int(payload.get("ev_member_count", 0) or 0) <= 0:
        return "Not an EV ensemble design target."
    if bool(payload.get("EV_design_hard_blocker_flag", False)):
        blockers = str(payload.get("EV_design_primary_blockers") or "hard blockers")
        return (
            "EV design remains exploratory despite score because hard blockers "
            f"remain: {blockers}."
        )
    if bool(payload.get("route_disagreement_flag")) or bool(
        payload.get("physics_model_disagreement_flag")
    ):
        return (
            "EV design is a review candidate, but route or model consensus must "
            "be resolved before claim freeze."
        )
    if bool(payload.get("EV_design_detector_caution_flag", False)):
        return (
            "EV design is ranked for relative/proxy model use with detector "
            "operator caution; detector-resolved and absolute/global green "
            "claims remain blocked pending ROI calibration or measured detector "
            "validation."
        )
    if str(payload.get("EV_design_recommendation_band_absolute")) == (
        "absolute_global_green_blocked"
    ):
        return (
            "EV design is ranked for relative model use; absolute/global green "
            "claims remain blocked pending calibration and measured controls."
        )
    return (
        "EV design is ranked by bounded ensemble score; biological specificity "
        "and calibrated quantitative claims remain outside this score."
    )


def generate_claim_boundary_text(payload: Mapping[str, Any]) -> dict[str, str]:
    """Return explicit allowed/disallowed claim text for design exports."""
    band = str(payload.get("EV_design_recommendation_band", "not_ev_design_target"))
    if band == "not_ev_design_target":
        allowed = "非 EV design target；不生成 EV 优先级 claim。"
    elif bool(payload.get("EV_design_hard_blocker_flag", False)):
        allowed = "该几何只能作为 exploratory EV design 复核候选，不能作为冻结结论。"
    elif bool(payload.get("EV_design_detector_caution_flag", False)):
        allowed = (
            "该几何可作为 relative/proxy EV design 候选复核；detector ROI "
            "差异仍需单独校准或实测验证。"
        )
    else:
        allowed = "该几何在当前 relative EV design model 下优先级较高，可作为候选复核。"
    forbidden = (
        "不可说该几何真实 detector voltage、absolute SNR、LOD 或生物特异性最高；"
        "这些需要 detector-unit calibration、blank controls 和实验验证。"
    )
    return {
        "EV_design_claim_allowed_text": allowed,
        "EV_design_claim_forbidden_text": forbidden,
        "EV_design_claim_boundary_status": "relative_model_claim_boundary_active",
    }


def _build_ev_group_payload(
    group_key: tuple[str, ...],
    rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    scores = [_row_score(row) for row in rows]
    margins = [
        value
        for value in (
            finite_float_or_none(get_result_metric_value(row, "mean_peak_margin_z"))
            for row in rows
        )
        if value is not None
    ]
    phase_flips = [
        value
        for value in (
            finite_float_or_none(get_result_metric_value(row, "phase_flip_fraction"))
            for row in rows
        )
        if value is not None
    ]
    route_consensus = compute_reference_route_consensus(rows)
    physics_consensus = compute_physics_model_consensus(rows)
    hard_blocked = any(_is_hard_blocked(row) for row in rows)
    absolute_green_eligible = all(_row_absolute_green_eligible(row) for row in rows)
    detector_caution = any(_row_detector_caution(row) for row in rows)
    detector_resolved_pass_fraction = (
        float(sum(_row_detector_resolved(row) for row in rows) / len(rows))
        if rows
        else 0.0
    )
    blockers = _join_blockers(rows)
    reference_score = min(
        (
            finite_float_or_none(get_result_metric_value(row, "reference_design_score"))
            or 0.0
            for row in rows
        ),
        default=0.0,
    )
    fluidic_penalty = max(
        (
            finite_float_or_none(
                get_result_metric_value(row, "fluidic_practicality_penalty")
            )
            or 0.0
            for row in rows
        ),
        default=0.0,
    )
    contaminant_overlap = max(
        (
            finite_float_or_none(
                get_result_metric_value(row, "EV_to_contaminant_signal_overlap")
            )
            or 0.0
            for row in rows
        ),
        default=0.0,
    )
    disagreement_penalty = 1.0 if (
        route_consensus["route_disagreement_flag"]
        or physics_consensus["physics_model_disagreement_flag"]
    ) else 0.0
    anchor_score, anchor_peak_ratio = _anchor_score(rows)
    ev_score_min = float(min(scores)) if scores else 0.0
    ev_score_p10 = float(np.percentile(scores, 10)) if scores else 0.0
    ev_score_median = float(np.median(scores)) if scores else 0.0
    gate_pass_fraction = (
        float(sum(_row_gate_passed(row) for row in rows) / len(rows))
        if rows
        else 0.0
    )
    final_score = clamp01(
        0.35 * ev_score_min
        + 0.15 * ev_score_median
        + 0.15 * anchor_score
        + 0.10 * reference_score
        + 0.10 * (1.0 - clamp01(contaminant_overlap))
        - 0.10 * clamp01(fluidic_penalty)
        - 0.10 * disagreement_penalty
    )
    payload: dict[str, Any] = {
        "ev_member_count": len(rows),
        "ev_score_min": ev_score_min,
        "ev_score_p10": ev_score_p10,
        "ev_score_median": ev_score_median,
        "ev_gate_pass_fraction": gate_pass_fraction,
        "ev_min_margin_z": float(min(margins)) if margins else None,
        "ev_max_phase_flip_fraction": float(max(phase_flips)) if phase_flips else None,
        "au20_equivalent_peak_ratio": anchor_peak_ratio,
        "reference_design_score": reference_score,
        "reference_operating_band": _worst_reference_band(rows),
        "fluidic_practicality_penalty": clamp01(fluidic_penalty),
        "EV_contaminant_overlap_fraction": clamp01(contaminant_overlap),
        "final_EV_design_score": final_score,
        "EV_design_hard_blocker_flag": hard_blocked,
        "EV_design_primary_blockers": blockers,
        "EV_design_group_key": "|".join(group_key),
        "EV_design_detector_caution_flag": detector_caution,
        "EV_design_detector_caution_summary": _join_detector_cautions(rows),
        "EV_design_detector_resolved_pass_fraction": (
            detector_resolved_pass_fraction
        ),
        **route_consensus,
        **physics_consensus,
    }
    payload["EV_design_recommendation_band_relative"] = _recommendation_band(payload)
    payload["EV_design_recommendation_band_absolute"] = _absolute_recommendation_band(
        payload,
        absolute_green_eligible=absolute_green_eligible,
    )
    payload["EV_design_recommendation_band"] = payload[
        "EV_design_recommendation_band_relative"
    ]
    payload["EV_design_claim_text"] = generate_claim_text(payload)
    payload.update(generate_claim_boundary_text(payload))
    return payload


def _default_ev_postprocess_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "ev_member_count": 0,
        "ev_score_min": None,
        "ev_score_p10": None,
        "ev_score_median": None,
        "ev_min_margin_z": None,
        "ev_max_phase_flip_fraction": None,
        "au20_equivalent_peak_ratio": get_result_metric_value(
            row,
            "Au20_equivalent_peak_ratio",
        ),
        "reference_design_score": get_result_metric_value(
            row,
            "reference_design_score",
        ),
        "reference_operating_band": get_result_metric_value(
            row,
            "reference_operating_band",
        ),
        "fluidic_practicality_penalty": get_result_metric_value(
            row,
            "fluidic_practicality_penalty",
        ),
        "EV_contaminant_overlap_fraction": get_result_metric_value(
            row,
            "EV_to_contaminant_signal_overlap",
        ),
        "route_disagreement_flag": False,
        "physics_model_disagreement_flag": False,
        "reference_route_consensus_status": "not_ev_design_target",
        "physics_model_consensus_status": "not_ev_design_target",
        "EV_design_detector_caution_flag": False,
        "EV_design_detector_caution_summary": None,
        "EV_design_detector_resolved_pass_fraction": None,
        "final_EV_design_score": None,
        "EV_design_recommendation_band": "not_ev_design_target",
        "EV_design_recommendation_band_relative": "not_ev_design_target",
        "EV_design_recommendation_band_absolute": "not_ev_design_target",
        "EV_design_claim_text": "Not an EV ensemble design target.",
        **generate_claim_boundary_text(
            {"EV_design_recommendation_band": "not_ev_design_target"}
        ),
        "EV_design_hard_blocker_flag": False,
        "EV_design_primary_blockers": None,
        "EV_design_group_key": None,
    }
    payload[_EV_GATE_PASS_FRACTION_FIELD] = None
    return payload


def _is_ev_design_row(row: Mapping[str, Any]) -> bool:
    family = str(get_result_metric_value(row, "particle_family", "")).lower()
    name = str(row.get("particle_name", get_result_metric_value(row, "particle_preset_id", "")))
    return family == "ev_sev" or "exosome" in name.lower() or name.lower().startswith("ev")


def _row_score(row: Mapping[str, Any]) -> float:
    for field in ("final_engineering_score", "engineering_score", "score"):
        value = finite_float_or_none(get_result_metric_value(row, field))
        if value is not None:
            return clamp01(value)
    return 0.0


def _row_gate_passed(row: Mapping[str, Any]) -> bool:
    value = get_result_metric_value(row, "relative_design_eligible")
    if value is not None:
        return bool(value)

    value = get_result_metric_value(row, "within_lambda_design_eligible")
    if value is not None:
        return bool(value)

    return bool(get_result_metric_value(row, "engineering_gate_passed", False))


def _is_hard_blocked(row: Mapping[str, Any]) -> bool:
    relative = get_result_metric_value(row, "relative_design_eligible")
    if relative is not None:
        return not bool(relative)

    engineering = get_result_metric_value(row, "engineering_gate_passed")
    if engineering is not None:
        return not bool(engineering)

    final_green = get_result_metric_value(row, "final_green_eligible")
    return final_green is False


def _row_absolute_green_eligible(row: Mapping[str, Any]) -> bool:
    value = get_result_metric_value(row, "absolute_global_green_eligible")
    if value is not None:
        return bool(value)

    value = get_result_metric_value(row, "final_green_eligible")
    if value is not None:
        return bool(value)

    return False


def _row_detector_caution(row: Mapping[str, Any]) -> bool:
    value = get_result_metric_value(row, "detector_operator_caution_flag")
    if value is not None:
        return bool(value)
    detector_gate = get_result_metric_value(row, "detector_operator_gate_passed")
    if detector_gate is not None:
        return not bool(detector_gate)
    band = str(
        get_result_metric_value(
            row,
            "detector_operator_disagreement_band",
            "",
        )
        or ""
    )
    return band in {"large", "unavailable_no_roi_mode_overlap_lane"}


def _row_detector_resolved(row: Mapping[str, Any]) -> bool:
    value = get_result_metric_value(row, "detector_resolved_relative_design_eligible")
    if value is not None:
        return bool(value)
    relative = bool(get_result_metric_value(row, "relative_design_eligible", False))
    detector_gate = bool(
        get_result_metric_value(row, "detector_operator_gate_passed", False)
    )
    return relative and detector_gate


def _join_blockers(rows: Iterable[Mapping[str, Any]]) -> str | None:
    blockers: list[str] = []
    for row in rows:
        blocker = str(get_result_metric_value(row, "primary_blocker_summary", "") or "")
        if blocker and blocker.lower() not in {"pass", "none", "n/a"}:
            blockers.append(blocker)
    if not blockers:
        return None
    return "; ".join(dict.fromkeys(blockers[:3]))


def _join_detector_cautions(rows: Iterable[Mapping[str, Any]]) -> str | None:
    cautions: list[str] = []
    for row in rows:
        reason = str(
            get_result_metric_value(row, "detector_operator_caution_reason", "") or ""
        )
        if reason and reason.lower() not in {"none", "pass", "n/a"}:
            cautions.append(reason)
            continue
        band = str(
            get_result_metric_value(row, "detector_operator_disagreement_band", "")
            or ""
        )
        if band in {"large", "unavailable_no_roi_mode_overlap_lane"}:
            cautions.append(f"detector_operator_disagreement_band={band}")
    if not cautions:
        return None
    return "; ".join(dict.fromkeys(cautions[:3]))


def _unique_values(rows: Iterable[Mapping[str, Any]], field: str) -> set[str]:
    values: set[str] = set()
    for row in rows:
        value = get_result_metric_value(row, field)
        if value is not None and str(value) != "":
            values.add(str(value))
    return values


def _anchor_score(rows: Iterable[Mapping[str, Any]]) -> tuple[float, float | None]:
    peak_ratios = _finite_group_values(rows, "Au20_equivalent_peak_ratio")
    margin_ratios = _finite_group_values(rows, "Au20_equivalent_margin_ratio")
    stable_ratios = _finite_group_values(rows, "Au20_equivalent_stable_rate_ratio")
    if not peak_ratios or not margin_ratios or not stable_ratios:
        return 0.0, None
    peak = min(peak_ratios)
    margin = min(margin_ratios)
    stable = min(stable_ratios)
    score = clamp01(0.40 * min(peak, 1.0) + 0.30 * min(margin, 1.0) + 0.30 * min(stable, 1.0))
    return score, float(peak)


def _finite_group_values(
    rows: Iterable[Mapping[str, Any]],
    field: str,
) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = finite_float_or_none(get_result_metric_value(row, field))
        if value is not None:
            values.append(value)
    return values


def _worst_reference_band(rows: Iterable[Mapping[str, Any]]) -> str:
    priority = {
        "reference_too_weak": 0,
        "reference_saturation_risk": 1,
        "rin_or_leakage_risk": 1,
        "shot_noise_limited_no_gain": 2,
        "electronics_noise_limited_useful": 3,
        "balanced": 4,
    }
    bands = [
        str(get_result_metric_value(row, "reference_operating_band", "unknown"))
        for row in rows
    ]
    if not bands:
        return "unknown"
    return min(bands, key=lambda band: priority.get(band, 2))


def _recommendation_band(payload: Mapping[str, Any]) -> str:
    if bool(payload.get("EV_design_hard_blocker_flag", False)):
        return "exploratory_only"
    if bool(payload.get("route_disagreement_flag")) or bool(
        payload.get("physics_model_disagreement_flag")
    ):
        return "review_required_consensus_gap"
    score = finite_float_or_none(payload.get("final_EV_design_score")) or 0.0
    gate_fraction = finite_float_or_none(payload.get("ev_gate_pass_fraction")) or 0.0
    if score >= 0.75 and gate_fraction >= 0.8:
        return "recommended_candidate"
    if score >= 0.5:
        return "screening_candidate"
    return "not_recommended"


def _absolute_recommendation_band(
    payload: Mapping[str, Any],
    *,
    absolute_green_eligible: bool,
) -> str:
    if int(payload.get("ev_member_count", 0) or 0) <= 0:
        return "not_ev_design_target"
    if not absolute_green_eligible:
        return "absolute_global_green_blocked"
    return str(payload.get("EV_design_recommendation_band_relative", "not_recommended"))
