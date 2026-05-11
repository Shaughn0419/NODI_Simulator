"""Package-local design-row metrics for postprocessing."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any

from .type_coerce import positive_ratio as _ratio


DESIGN_METRIC_MATCH_KEYS = (
    "width_m",
    "depth_m",
    "wavelength_m",
    "reference_model",
    "reference_solver_route",
    "readout_preset",
    "detector_forward_model",
)

DESIGN_METRIC_DIAGNOSTIC_FIELDS = (
    "Au20_anchor_available",
    "Au20_anchor_geometry_matched",
    "Au20_equivalent_peak_ratio",
    "Au20_equivalent_margin_ratio",
    "Au20_equivalent_stable_rate_ratio",
    "Au20_equivalent_detectability_band",
    "reference_design_score",
    "reference_design_score_status",
    "fluidic_practicality_score",
    "fluidic_practicality_score_status",
)


def finite_float_or_none(value: Any) -> float | None:
    """Return a finite float or None for missing/non-numeric values."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def clamp01(value: float | None, default: float = 0.0) -> float:
    """Clamp a possibly missing numeric value into the closed [0, 1] interval."""
    if value is None:
        return float(default)
    return float(min(1.0, max(0.0, value)))


def get_result_metric_value(
    row: Mapping[str, Any],
    field: str,
    default: Any = None,
) -> Any:
    """Read a metric from summary/reference/intrinsic/top-level payloads."""
    for source_name in ("summary", "reference", "intrinsic"):
        source = row.get(source_name)
        if isinstance(source, Mapping) and field in source:
            return source[field]
    return row.get(field, default)


def write_result_metric_payload(
    row: MutableMapping[str, Any],
    payload: Mapping[str, Any],
) -> None:
    """Attach diagnostics to both summary and top-level row payloads."""
    summary = row.get("summary")
    if not isinstance(summary, MutableMapping):
        summary = {}
        row["summary"] = summary
    summary.update(payload)
    row.update(payload)


def design_metric_match_key(row: Mapping[str, Any]) -> tuple[str, ...]:
    """Build the geometry/readout/reference key used for design-row matching."""
    return (
        _float_key(get_result_metric_value(row, "width_m")),
        _float_key(get_result_metric_value(row, "depth_m")),
        _float_key(get_result_metric_value(row, "wavelength_m")),
        _str_key(get_result_metric_value(row, "reference_model", "unknown_reference_model")),
        _str_key(
            get_result_metric_value(
                row,
                "reference_solver_route",
                "unknown_reference_solver_route",
            )
        ),
        _str_key(get_result_metric_value(row, "readout_preset", "unknown_readout_preset")),
        _str_key(
            get_result_metric_value(
                row,
                "detector_forward_model",
                "unknown_detector_forward_model",
            )
        ),
    )


def attach_anchor_equivalent_metrics(
    results: Iterable[MutableMapping[str, Any]],
) -> list[MutableMapping[str, Any]]:
    """Attach Au20-equivalent ratios by exact design-metric match key."""
    rows = list(results)
    anchor_rows = [row for row in rows if _is_au20_anchor_row(row)]
    anchors_by_key: dict[tuple[str, ...], MutableMapping[str, Any]] = {}
    for anchor in anchor_rows:
        key = design_metric_match_key(anchor)
        current: MutableMapping[str, Any] | None = anchors_by_key.get(key)
        if current is None:
            anchors_by_key[key] = anchor
        elif _peak_height(anchor) > _peak_height(current):
            anchors_by_key[key] = anchor

    any_anchor_available = bool(anchor_rows)
    for row in rows:
        key = design_metric_match_key(row)
        anchor_row = anchors_by_key.get(key)
        payload = _anchor_equivalent_payload(
            row,
            anchor_row,
            any_anchor_available=any_anchor_available,
        )
        write_result_metric_payload(row, payload)
    return rows


def attach_reference_operating_metrics(
    results: Iterable[MutableMapping[str, Any]],
) -> list[MutableMapping[str, Any]]:
    """Attach bounded reference operating scores derived from P0 reference fields."""
    rows = list(results)
    rank_values = [
        value
        for value in (
            finite_float_or_none(
                get_result_metric_value(row, "reference_design_width_rank_metric")
            )
            for row in rows
        )
        if value is not None and value > 0.0
    ]
    max_rank = max(rank_values) if rank_values else None
    for row in rows:
        rank = finite_float_or_none(
            get_result_metric_value(row, "reference_design_width_rank_metric")
        )
        band = str(get_result_metric_value(row, "reference_operating_band", "unknown"))
        base_score = (rank / max_rank) if rank is not None and max_rank else 0.0
        if band == "reference_too_weak":
            score = 0.0
            status = "blocked_reference_too_weak"
        elif band in {"reference_saturation_risk", "rin_or_leakage_risk"}:
            score = min(clamp01(base_score), 0.25)
            status = "capped_by_reference_operating_risk"
        elif band == "shot_noise_limited_no_gain":
            score = min(clamp01(base_score), 0.65)
            status = "capped_by_reference_gain_limit"
        elif rank is None:
            score = 0.0
            status = "missing_reference_rank_metric"
        else:
            score = clamp01(base_score)
            status = "relative_reference_score_active"
        write_result_metric_payload(
            row,
            {
                "reference_design_score": score,
                "reference_design_score_status": status,
            },
        )
    return rows


def attach_fluidic_practicality_metrics(
    results: Iterable[MutableMapping[str, Any]],
) -> list[MutableMapping[str, Any]]:
    """Attach a convenience score complement for fluidic practicality penalty."""
    rows = list(results)
    for row in rows:
        penalty = finite_float_or_none(
            get_result_metric_value(row, "fluidic_practicality_penalty")
        )
        if penalty is None:
            score = 0.0
            status = "missing_fluidic_practicality_penalty"
        else:
            score = 1.0 - clamp01(penalty)
            status = "fluidic_practicality_score_active"
        write_result_metric_payload(
            row,
            {
                "fluidic_practicality_score": score,
                "fluidic_practicality_score_status": status,
            },
        )
    return rows


def _float_key(value: Any) -> str:
    parsed = finite_float_or_none(value)
    return "unknown" if parsed is None else f"{parsed:.12e}"


def _str_key(value: Any) -> str:
    text = str(value if value is not None else "unknown")
    return text if text else "unknown"


def _peak_height(row: Mapping[str, Any]) -> float:
    return abs(finite_float_or_none(get_result_metric_value(row, "mean_peak_height")) or 0.0)


def _is_au20_anchor_row(row: Mapping[str, Any]) -> bool:
    name = str(get_result_metric_value(row, "particle_preset_id", row.get("particle_name", "")))
    family = str(get_result_metric_value(row, "particle_family", "")).lower()
    material = str(get_result_metric_value(row, "particle_material", "")).lower()
    is_gold = family == "gold" or "gold" in name.lower() or material == "gold"
    if not is_gold:
        return False

    diameter_nm = finite_float_or_none(get_result_metric_value(row, "particle_diameter_nm"))
    if diameter_nm is None:
        diameter_m = finite_float_or_none(get_result_metric_value(row, "particle_diameter_m"))
        if diameter_m is not None:
            diameter_nm = diameter_m * 1e9
    if diameter_nm is None:
        radius_m = finite_float_or_none(get_result_metric_value(row, "particle_radius_m"))
        if radius_m is not None:
            diameter_nm = 2.0 * radius_m * 1e9
    if diameter_nm is not None:
        return abs(diameter_nm - 20.0) <= 2.0

    compact_name = name.lower().replace("_", "").replace("-", "")
    return "20nm" in compact_name or "20.0nm" in compact_name


def _anchor_equivalent_payload(
    row: Mapping[str, Any],
    anchor: Mapping[str, Any] | None,
    *,
    any_anchor_available: bool,
) -> dict[str, Any]:
    if anchor is None:
        return {
            "Au20_anchor_available": any_anchor_available,
            "Au20_anchor_geometry_matched": False,
            "Au20_equivalent_peak_ratio": None,
            "Au20_equivalent_margin_ratio": None,
            "Au20_equivalent_stable_rate_ratio": None,
            "Au20_equivalent_detectability_band": (
                "unavailable_no_geometry_matched_Au20_anchor"
            ),
        }

    peak_ratio = _ratio(_peak_height(row), _peak_height(anchor))
    margin_ratio = _ratio(
        finite_float_or_none(get_result_metric_value(row, "mean_peak_margin_z")),
        finite_float_or_none(get_result_metric_value(anchor, "mean_peak_margin_z")),
    )
    stable_ratio = _ratio(
        finite_float_or_none(get_result_metric_value(row, "stable_detection_rate")),
        finite_float_or_none(get_result_metric_value(anchor, "stable_detection_rate")),
    )
    if peak_ratio is None or margin_ratio is None or stable_ratio is None:
        band = "anchor_metric_incomplete"
    elif peak_ratio >= 1.0 and margin_ratio >= 1.0 and stable_ratio >= 1.0:
        band = "anchor_matched_or_better"
    elif peak_ratio >= 0.5 and margin_ratio >= 0.5 and stable_ratio >= 0.5:
        band = "anchor_partial"
    else:
        band = "below_anchor"
    return {
        "Au20_anchor_available": True,
        "Au20_anchor_geometry_matched": True,
        "Au20_equivalent_peak_ratio": peak_ratio,
        "Au20_equivalent_margin_ratio": margin_ratio,
        "Au20_equivalent_stable_rate_ratio": stable_ratio,
        "Au20_equivalent_detectability_band": band,
    }
