from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .data_objects import resolve_reference_route_name


MINIMAL_CONFIG_TRACE_FIELDS = (
    "reference_model",
    "reference_route",
    "reference_na_edge_policy",
    "noise_std",
    "shot_noise_scale",
    "post_readout_noise_std",
    "field_coordinate_measure",
    "bfp_to_angle_jacobian_applied",
    "interference_overlap_mode",
    "interference_overlap_status",
    "scattering_projection_mode",
    "NA_collection",
    "rho",
    "threshold_sigma",
    "normalization_view",
)


@dataclass(frozen=True)
class MinimalConfigTrace:
    runtime_config_subset: dict[str, Any]
    manifest_field_origins: dict[str, str]
    manifest_field_sources: dict[str, str]
    manifest_field_confidence: dict[str, str]
    unresolved_fields: tuple[str, ...]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_minimal_config_trace(
    *,
    cfg: Any,
    optical_template: Any | None = None,
    normalization_view: str | None,
    config_trace_status: str,
    interference_overlap_status: str | None = None,
    backfilled_at: str | None = None,
    field_origin_overrides: dict[str, str] | None = None,
    field_source_overrides: dict[str, str] | None = None,
    field_confidence_overrides: dict[str, str] | None = None,
) -> MinimalConfigTrace:
    """Build a per-field-auditable minimal runtime-config trace payload."""
    resolved_reference_route = resolve_reference_route_name(
        str(cfg.reference_model),
        str(getattr(cfg, "reference_route", "auto")),
    )
    na_collection = getattr(
        optical_template,
        "NA_collection",
        getattr(cfg, "NA_collection", None),
    )
    unresolved_fields: list[str] = []
    if interference_overlap_status is None:
        unresolved_fields.append("interference_overlap_status")

    runtime_config_subset = {
        "reference_model": str(cfg.reference_model),
        "reference_route": str(resolved_reference_route),
        "reference_na_edge_policy": str(cfg.reference_na_edge_policy),
        "noise_std": float(cfg.noise_std),
        "shot_noise_scale": float(cfg.shot_noise_scale),
        "post_readout_noise_std": float(cfg.post_readout_noise_std),
        "field_coordinate_measure": str(cfg.field_coordinate_measure),
        "bfp_to_angle_jacobian_applied": bool(cfg.bfp_to_angle_jacobian_applied),
        "interference_overlap_mode": str(cfg.interference_overlap_mode),
        "interference_overlap_status": interference_overlap_status,
        "scattering_projection_mode": str(cfg.scattering_projection_mode),
        "NA_collection": (
            None if na_collection is None else float(na_collection)
        ),
        "rho": float(cfg.rho),
        "threshold_sigma": float(cfg.threshold_sigma),
        "normalization_view": normalization_view,
        "config_trace_status": str(config_trace_status),
        "manifest_field_origins": {},
        "manifest_field_sources": {},
        "manifest_field_confidence": {},
    }
    if backfilled_at is not None:
        runtime_config_subset["backfilled_at"] = str(backfilled_at)
    elif str(config_trace_status) != "original_runtime_record":
        runtime_config_subset["backfilled_at"] = _utc_now_iso()

    manifest_field_origins = {
        "reference_model": "cfg",
        "reference_route": "cfg_resolved_route",
        "reference_na_edge_policy": "cfg",
        "noise_std": "cfg",
        "shot_noise_scale": "cfg",
        "post_readout_noise_std": "cfg",
        "field_coordinate_measure": "cfg",
        "bfp_to_angle_jacobian_applied": "cfg",
        "interference_overlap_mode": "cfg",
        "interference_overlap_status": (
            "reference"
            if interference_overlap_status is not None
            else "unavailable_without_case_reference_context"
        ),
        "scattering_projection_mode": "cfg",
        "NA_collection": (
            "optical_template"
            if hasattr(optical_template, "NA_collection")
            else "cfg"
        ),
        "rho": "cfg",
        "threshold_sigma": "cfg",
        "normalization_view": (
            "runner_args"
            if normalization_view is not None
            else "unavailable_without_lane_context"
        ),
    }
    manifest_field_sources = {
        "reference_model": "cfg.reference_model",
        "reference_route": "resolve_reference_route_name(cfg.reference_model, cfg.reference_route)",
        "reference_na_edge_policy": "cfg.reference_na_edge_policy",
        "noise_std": "cfg.noise_std",
        "shot_noise_scale": "cfg.shot_noise_scale",
        "post_readout_noise_std": "cfg.post_readout_noise_std",
        "field_coordinate_measure": "cfg.field_coordinate_measure",
        "bfp_to_angle_jacobian_applied": "cfg.bfp_to_angle_jacobian_applied",
        "interference_overlap_mode": "cfg.interference_overlap_mode",
        "interference_overlap_status": (
            "reference.interference_overlap_status"
            if interference_overlap_status is not None
            else "not_available_without_case_reference_evaluation"
        ),
        "scattering_projection_mode": "cfg.scattering_projection_mode",
        "NA_collection": (
            "optical_template.NA_collection"
            if hasattr(optical_template, "NA_collection")
            else "cfg.NA_collection"
        ),
        "rho": "cfg.rho",
        "threshold_sigma": "cfg.threshold_sigma",
        "normalization_view": "runner_args.normalization_lane_or_backfill_lane",
    }
    manifest_field_confidence = {
        "reference_model": "high",
        "reference_route": "high",
        "reference_na_edge_policy": "high",
        "noise_std": "high",
        "shot_noise_scale": "high",
        "post_readout_noise_std": "high",
        "field_coordinate_measure": "high",
        "bfp_to_angle_jacobian_applied": "high",
        "interference_overlap_mode": "high",
        "interference_overlap_status": (
            "high" if interference_overlap_status is not None else "low"
        ),
        "scattering_projection_mode": "high",
        "NA_collection": "high" if na_collection is not None else "low",
        "rho": "high",
        "threshold_sigma": "high",
        "normalization_view": "high" if normalization_view is not None else "low",
    }

    for overrides, target in (
        (field_origin_overrides, manifest_field_origins),
        (field_source_overrides, manifest_field_sources),
        (field_confidence_overrides, manifest_field_confidence),
    ):
        if overrides:
            target.update({str(key): str(value) for key, value in overrides.items()})

    runtime_config_subset["manifest_field_origins"] = manifest_field_origins
    runtime_config_subset["manifest_field_sources"] = manifest_field_sources
    runtime_config_subset["manifest_field_confidence"] = manifest_field_confidence

    return MinimalConfigTrace(
        runtime_config_subset=runtime_config_subset,
        manifest_field_origins=manifest_field_origins,
        manifest_field_sources=manifest_field_sources,
        manifest_field_confidence=manifest_field_confidence,
        unresolved_fields=tuple(unresolved_fields),
    )
