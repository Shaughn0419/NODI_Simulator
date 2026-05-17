"""
Calibration table helpers and boundary diagnostics.

This module centralizes lightweight CSV/JSON loading, manifest inspection, and
schema checks for calibration inputs. Runtime paths still decide how much of a
table may be applied; helpers here only make the data contract explicit.
"""

from __future__ import annotations

import csv
import json
import math
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SYNTHETIC_CALIBRATION_ROLE = "synthetic_fixture_not_experimental"
UNSPECIFIED_CALIBRATION_ROLE = "unspecified_user_table"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

_SYNTHETIC_ROLE_ALIASES = {
    "synthetic",
    "synthetic_fixture",
    SYNTHETIC_CALIBRATION_ROLE,
    "template",
    "example",
    "demo",
    "simulated",
}

_CALIBRATION_FIELD_GROUPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "reference_blank_channel": (
        ("width_nm",),
        ("depth_nm",),
        ("wavelength_nm", "lambda_nm"),
        ("g_ref", "A_ref"),
    ),
    "collection_operator": (
        (
            "theta_center_rad",
            "theta_rad",
            "theta_sigma_rad",
            "sigma_effective_rad",
            "collection_sigma_rad",
            "phi_sigma_rad",
            "collection_phi_sigma_rad",
            "slit_phi_limit_rad",
            "slit_phi_rad",
            "throughput_scale",
            "absolute_throughput",
            "optical_throughput",
        ),
    ),
    "standard_particle": (
        ("K_sca", "K_sca_scale", "K_sca_detector_scale", "global_phase_offset_rad"),
    ),
    "blank_false_positive": (
        (
            "threshold_sigma_nodi",
            "threshold_sigma_pod",
            "empirical_peak_false_alarm_rate_per_minute",
            "peak_false_alarm_rate_per_minute",
            "empirical_pair_false_alarm_rate_per_minute",
            "pair_false_alarm_rate_per_minute",
            "blank_trace_autocorrelation_time_s",
            "autocorrelation_time_s",
        ),
    ),
    "bfp_roi_mask": (
        ("pixel_x",),
        ("pixel_y",),
        ("theta_rad",),
        ("phi_rad",),
        ("mask_weight",),
        ("solid_angle_weight",),
    ),
}

_MEASURED_ROLE_ALIASES = {
    "measured",
    "measured_experimental",
    "experimental",
    "experimental_measurement",
    "calibrated_measurement",
}


def optional_calibration_float(
    row: Mapping[str, Any],
    *keys: str,
    default: float | None = None,
) -> float | None:
    """Return the first finite float found in a calibration row."""
    for key in keys:
        value = row.get(key)
        if value is None or value == "":
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            return numeric
    return default


def optional_calibration_string(
    row: Mapping[str, Any],
    *keys: str,
    default: str | None = None,
) -> str | None:
    """Return the first non-empty string found in a calibration row."""
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default


def normalise_calibration_rows(raw: Any) -> list[dict[str, Any]]:
    """Normalize CSV/JSON calibration payloads to a list of string-keyed rows."""
    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, dict):
        for key in ("rows", "operators", "standards", "blank_summaries"):
            if isinstance(raw.get(key), list):
                candidates = raw[key]
                break
        else:
            candidates = [raw]
    else:
        raise ValueError("calibration payload must be a row list or mapping")

    rows = [
        {str(key): value for key, value in item.items()}
        for item in candidates
        if isinstance(item, Mapping)
    ]
    if not rows:
        raise ValueError("calibration payload has no usable rows")
    return rows


def _resolve_calibration_path(path: str) -> Path:
    """Resolve calibration paths while blocking relative traversal outside the repo."""
    raw = Path(path).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    resolved = (PROJECT_ROOT / raw).resolve()
    if not resolved.is_relative_to(PROJECT_ROOT.resolve()):
        raise ValueError(f"Calibration path outside project root: {path!r}")
    return resolved


def load_calibration_rows(path: str) -> list[dict[str, Any]]:
    """Load a calibration table from CSV or JSON."""
    resolved = _resolve_calibration_path(path)
    suffix = resolved.suffix.lower()
    if suffix == ".json":
        with resolved.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return normalise_calibration_rows(raw)
    if suffix == ".csv":
        with resolved.open("r", encoding="utf-8", newline="") as handle:
            return normalise_calibration_rows(list(csv.DictReader(handle)))
    raise ValueError(f"Unsupported calibration file format: {path}. Use .csv or .json.")


def candidate_manifest_paths(table_path: str) -> list[str]:
    """Return conventional manifest sidecar paths for a calibration table."""
    root, _ = os.path.splitext(table_path)
    return [
        f"{table_path}.manifest.json",
        f"{root}_manifest.json",
    ]


def load_calibration_manifest(
    table_path: str,
    *,
    explicit_manifest_path: str | None = None,
) -> dict[str, Any]:
    """Load an optional manifest sidecar; return a status dict when absent."""
    candidates = (
        [explicit_manifest_path]
        if explicit_manifest_path is not None
        else candidate_manifest_paths(table_path)
    )
    for candidate in candidates:
        if candidate:
            resolved = _resolve_calibration_path(candidate)
        else:
            continue
        if resolved.exists():
            with resolved.open("r", encoding="utf-8") as handle:
                manifest = json.load(handle)
            if not isinstance(manifest, dict):
                raise ValueError(f"Calibration manifest must be a JSON object: {candidate}")
            manifest = {str(key): value for key, value in manifest.items()}
            manifest.setdefault("manifest_path", str(resolved))
            manifest.setdefault("manifest_status", "loaded")
            return manifest
    return {
        "manifest_path": None,
        "manifest_status": "missing_manifest",
    }


def _normalise_data_role(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text


def resolve_calibration_data_role(
    *,
    row: Mapping[str, Any] | None = None,
    manifest: Mapping[str, Any] | None = None,
) -> str:
    """Resolve data role with row-level metadata taking precedence."""
    row = row or {}
    manifest = manifest or {}
    for source in (row, manifest):
        role = _normalise_data_role(
            source.get("calibration_data_role")
            or source.get("data_role")
            or source.get("source_role")
        )
        if role is not None:
            return role
    return UNSPECIFIED_CALIBRATION_ROLE


def is_synthetic_calibration(
    *,
    row: Mapping[str, Any] | None = None,
    manifest: Mapping[str, Any] | None = None,
) -> bool:
    """Return True for templates/examples that must not unlock claims."""
    row = row or {}
    manifest = manifest or {}
    role = resolve_calibration_data_role(row=row, manifest=manifest)
    if role.lower() in _SYNTHETIC_ROLE_ALIASES:
        return True
    for source in (row, manifest):
        flag = source.get("synthetic_fixture") or source.get("is_synthetic")
        if isinstance(flag, bool):
            return flag
        if isinstance(flag, str) and flag.strip().lower() in {"1", "true", "yes"}:
            return True
    return False


def is_measured_calibration_role(role: str | None) -> bool:
    """Return True for data roles allowed to unlock measured-calibration lanes."""
    if role is None:
        return False
    return role.strip().lower() in _MEASURED_ROLE_ALIASES


def validate_calibration_table(path: str, kind: str) -> dict[str, Any]:
    """
    Validate a calibration table against the minimal contract for a route.

    The validator is intentionally non-throwing for schema content so callers
    can expose validation status in dashboards without changing runtime behavior.
    File I/O or JSON/CSV parse errors are still surfaced as normal exceptions.
    """
    rows = load_calibration_rows(path)
    field_groups = _CALIBRATION_FIELD_GROUPS.get(kind, ())
    row_keys = set().union(*(set(row.keys()) for row in rows))
    missing_groups = [
        "|".join(group)
        for group in field_groups
        if not any(key in row_keys for key in group)
    ]
    return {
        "calibration_kind": kind,
        "validation_status": (
            "valid_minimal_schema" if not missing_groups else "missing_required_fields"
        ),
        "row_count": len(rows),
        "required_field_groups_missing": missing_groups,
        "table_columns": sorted(row_keys),
    }


def validate_calibration_manifest(
    manifest: Mapping[str, Any],
    *,
    kind: str,
) -> dict[str, Any]:
    """Validate the lightweight manifest contract used by templates."""
    required = ("calibration_kind", "calibration_data_role", "units")
    missing = [key for key in required if key not in manifest]
    kind_status = (
        "matches_table_kind"
        if str(manifest.get("calibration_kind", kind)) == str(kind)
        else "manifest_kind_mismatch"
    )
    if missing:
        validation_status = "missing_manifest_fields"
    elif kind_status != "matches_table_kind":
        validation_status = kind_status
    else:
        validation_status = "valid_minimal_manifest"
    return {
        "manifest_status": str(manifest.get("manifest_status", "loaded")),
        "manifest_path": manifest.get("manifest_path"),
        "manifest_validation_status": validation_status,
        "manifest_missing_fields": missing,
        "manifest_kind_status": kind_status,
    }


def _inline_manifest_from_json(path: str, *, kind: str) -> dict[str, Any] | None:
    """Return a manifest-like JSON object when the path itself is a manifest."""
    resolved = _resolve_calibration_path(path)
    if resolved.suffix.lower() != ".json":
        return None
    try:
        with resolved.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, Mapping):
        return None
    if str(raw.get("calibration_kind", "")) != str(kind):
        return None
    manifest = {str(key): value for key, value in raw.items()}
    manifest.setdefault("manifest_path", str(resolved))
    manifest.setdefault("manifest_status", "loaded_inline_manifest")
    return manifest


def calibration_contract_summary(
    *,
    table_path: str | None,
    kind: str,
    row: Mapping[str, Any] | None = None,
    explicit_manifest_path: str | None = None,
) -> dict[str, Any]:
    """Return table/manifest/role diagnostics for one calibration source."""
    if not table_path:
        return {
            "calibration_kind": kind,
            "calibration_table_validation_status": "not_configured",
            "calibration_manifest_status": "not_configured",
            "calibration_manifest_path": None,
            "calibration_data_role": UNSPECIFIED_CALIBRATION_ROLE,
            "synthetic_fixture_active": False,
        }

    validation = validate_calibration_table(str(table_path), kind)
    manifest = load_calibration_manifest(
        str(table_path),
        explicit_manifest_path=explicit_manifest_path,
    )
    manifest_validation = validate_calibration_manifest(manifest, kind=kind)
    data_role = resolve_calibration_data_role(row=row, manifest=manifest)
    synthetic = is_synthetic_calibration(row=row, manifest=manifest)
    return {
        "calibration_kind": kind,
        "calibration_table_validation_status": validation["validation_status"],
        "calibration_required_field_groups_missing": ";".join(
            validation["required_field_groups_missing"]
        ),
        "calibration_manifest_status": manifest_validation["manifest_status"],
        "calibration_manifest_validation_status": manifest_validation[
            "manifest_validation_status"
        ],
        "calibration_manifest_kind_status": manifest_validation[
            "manifest_kind_status"
        ],
        "calibration_manifest_path": manifest_validation["manifest_path"],
        "calibration_data_role": data_role,
        "synthetic_fixture_active": bool(synthetic),
    }


def resolve_calibration_state_machine(
    *,
    lanes: Mapping[str, str],
    output_claim_level: str,
    synthetic_fixture_active: bool = False,
) -> dict[str, Any]:
    """Resolve a compact lane-state summary without upgrading claims."""
    blockers: list[str] = []
    if synthetic_fixture_active:
        blockers.append("synthetic_calibration_fixture_not_experimental")
    for lane, status in lanes.items():
        if any(token in str(status) for token in ("missing", "not_", "surrogate", "unavailable")):
            blockers.append(f"{lane}:{status}")

    return {
        "calibration_state_machine_schema": "calibration_state_machine_v2",
        "calibration_state_resolver_status": (
            "blocked_by_unresolved_lanes" if blockers else "all_lanes_resolved"
        ),
        "calibration_lane_summary": dict(lanes),
        "calibration_state_blocker_summary": (
            "none" if not blockers else " / ".join(blockers)
        ),
        "calibration_synthetic_fixture_active": bool(synthetic_fixture_active),
        "output_claim_level_resolved": output_claim_level,
    }


def build_raw_blank_trace_bootstrap_boundary(
    *,
    raw_blank_trace_path: str | None = None,
) -> dict[str, Any]:
    """Describe the future raw-blank bootstrap API without consuming traces."""
    return {
        "raw_blank_trace_bootstrap_schema": "raw_blank_trace_bootstrap_v1",
        "raw_blank_trace_path_configured": bool(raw_blank_trace_path),
        "raw_blank_trace_bootstrap_supported": False,
        "raw_blank_trace_bootstrap_status": (
            "api_boundary_defined_waiting_for_trace_loader"
            if raw_blank_trace_path
            else "not_configured_summary_table_or_gaussian_iid_only"
        ),
        "raw_blank_trace_required_columns": (
            "time_s,lockin_nodi,lockin_pod,optional_blank_id,optional_lane"
        ),
        "raw_blank_trace_bootstrap_outputs": (
            "lane_sigma,autocorrelation_time,effective_samples,peak_FP,pair_FP"
        ),
    }


def build_bfp_roi_mask_contract(
    *,
    bfp_roi_mask_path: str | None = None,
    bfp_to_angle_jacobian_applied: bool = False,
) -> dict[str, Any]:
    """Describe the future BFP/ROI mask contract for collection calibration."""
    required_inputs = (
        "pixel_x,pixel_y,theta_rad,phi_rad,mask_weight,solid_angle_weight"
    )
    if not bfp_roi_mask_path:
        return {
            "bfp_roi_mask_schema": "bfp_roi_mask_v2",
            "bfp_roi_mask_path_configured": False,
            "bfp_roi_mask_calibrated": False,
            "bfp_roi_mask_source": "current_radian_surrogate_mask",
            "bfp_roi_mask_status": "not_configured_current_radian_surrogate_mask",
            "bfp_roi_mask_claim_level": (
                "surrogate_roi_not_pixel_calibrated"
            ),
            "bfp_roi_mask_data_role": "not_configured",
            "bfp_roi_mask_synthetic_fixture_active": False,
            "bfp_roi_mask_table_validation_status": "not_configured",
            "bfp_roi_mask_manifest_status": "not_configured",
            "bfp_roi_mask_manifest_validation_status": "not_configured",
            "bfp_roi_mask_manifest_path": None,
            "bfp_roi_mask_row_count": 0,
            "bfp_roi_mask_required_field_groups_missing": "",
            "bfp_roi_mask_gate_passed": False,
            "bfp_pixel_to_angle_status": (
                "not_calibrated_pixel_to_angle_mapping_missing"
            ),
            "slit_position_mapping_status": (
                "not_calibrated_slit_scan_or_image_required"
            ),
            "pinhole_projection_status": (
                "not_calibrated_projection_geometry_required"
            ),
            "bfp_roi_required_inputs": required_inputs,
        }

    table_path = str(bfp_roi_mask_path)
    validation = validate_calibration_table(table_path, "bfp_roi_mask")
    rows = load_calibration_rows(table_path)
    first_row = rows[0] if rows else {}
    manifest = load_calibration_manifest(table_path)
    if manifest.get("manifest_status") == "missing_manifest":
        inline_manifest = _inline_manifest_from_json(table_path, kind="bfp_roi_mask")
        if inline_manifest is not None:
            manifest = inline_manifest
    manifest_validation = validate_calibration_manifest(
        manifest,
        kind="bfp_roi_mask",
    )
    data_role = resolve_calibration_data_role(row=first_row, manifest=manifest)
    synthetic = is_synthetic_calibration(row=first_row, manifest=manifest)
    table_valid = validation["validation_status"] == "valid_minimal_schema"
    manifest_valid = (
        manifest_validation["manifest_validation_status"]
        == "valid_minimal_manifest"
    )
    measured_role = is_measured_calibration_role(data_role)
    calibrated = bool(table_valid and manifest_valid and measured_role and not synthetic)
    if calibrated:
        status = "calibrated_mask_contract_loaded"
        source = "calibrated_mask"
        claim_level = "calibrated_roi_mask_available_not_detector_unit_chain"
        pixel_status = "pixel_to_angle_mapping_table_available"
        slit_status = "roi_mask_or_slit_mapping_table_available"
        pinhole_status = "roi_mask_projection_table_available"
    elif synthetic:
        status = "synthetic_bfp_roi_mask_fixture_not_applied"
        source = "synthetic_fixture_contract_only"
        claim_level = "template_only_no_calibrated_mask_claim"
        pixel_status = "synthetic_pixel_to_angle_mapping_not_calibration"
        slit_status = "synthetic_slit_mapping_not_calibration"
        pinhole_status = "synthetic_projection_mapping_not_calibration"
    elif not table_valid:
        status = "configured_mask_missing_required_columns"
        source = "configured_mask_contract_invalid"
        claim_level = "invalid_mask_contract_no_calibration_claim"
        pixel_status = "configured_mask_missing_pixel_to_angle_columns"
        slit_status = "configured_mask_missing_slit_or_roi_columns"
        pinhole_status = "configured_mask_missing_projection_columns"
    elif not manifest_valid or not measured_role:
        status = "configured_mask_waiting_for_measured_manifest"
        source = "configured_mask_contract_not_measured"
        claim_level = "mask_rows_present_but_measured_role_not_verified"
        pixel_status = "pixel_to_angle_rows_present_role_not_measured"
        slit_status = "roi_rows_present_role_not_measured"
        pinhole_status = "projection_rows_present_role_not_measured"
    else:
        status = "configured_mask_not_applied"
        source = "configured_mask_contract_only"
        claim_level = "configured_mask_contract_no_calibration_claim"
        pixel_status = "pixel_to_angle_mapping_not_applied"
        slit_status = "slit_mapping_not_applied"
        pinhole_status = "projection_mapping_not_applied"

    return {
        "bfp_roi_mask_schema": "bfp_roi_mask_v2",
        "bfp_roi_mask_path_configured": True,
        "bfp_roi_mask_calibrated": calibrated,
        "bfp_roi_mask_source": source,
        "bfp_roi_mask_status": status,
        "bfp_roi_mask_claim_level": claim_level,
        "bfp_roi_mask_data_role": data_role,
        "bfp_roi_mask_synthetic_fixture_active": synthetic,
        "bfp_roi_mask_table_validation_status": validation["validation_status"],
        "bfp_roi_mask_manifest_status": manifest_validation["manifest_status"],
        "bfp_roi_mask_manifest_validation_status": manifest_validation[
            "manifest_validation_status"
        ],
        "bfp_roi_mask_manifest_path": manifest_validation["manifest_path"],
        "bfp_roi_mask_row_count": validation["row_count"],
        "bfp_roi_mask_required_field_groups_missing": ";".join(
            validation["required_field_groups_missing"]
        ),
        "bfp_roi_mask_gate_passed": calibrated,
        "bfp_pixel_to_angle_status": (
            "jacobian_flag_set_with_calibrated_mask"
            if calibrated and bfp_to_angle_jacobian_applied
            else pixel_status
        ),
        "slit_position_mapping_status": slit_status,
        "pinhole_projection_status": pinhole_status,
        "bfp_roi_required_inputs": required_inputs,
    }
