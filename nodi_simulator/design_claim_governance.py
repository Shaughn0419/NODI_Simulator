"""Package-local minimum output schema and claim gate governance."""

from __future__ import annotations

from collections.abc import Mapping
from math import isnan
from numbers import Real
from types import MappingProxyType
from typing import Any

from .data_objects import Channel, OpticalSystem, Particle, SimulationConfig


MINIMUM_OUTPUT_SCHEMA_FIELDS = (
    "case_id",
    "manifest_id",
    "particle_preset_id",
    "particle_size_convention",
    "particle_radius_m",
    "particle_diameter_m",
    "W_nm",
    "H_nm",
    "lambda_nm",
    "objective_candidate_id",
    "normalization_scope",
    "wavelength_ranking_claim_level",
    "detector_forward_model",
    "detector_operator_disagreement_band",
    "readout_semantics",
    "readout_observable_mode",
    "polarity_claim_allowed",
    "E_ref_route",
    "reference_operating_band",
    "particle_channel_perturbation_mode",
    "double_counting_risk_band",
    "unit_axis_convention_status",
    "mie_validation_status",
    "event_qc_pass_fraction",
    "selection_bias_warning",
    "safe_power_claim_level",
    "ev_integrity_claim_level",
    "calibration_state",
    "output_claim_level_resolved",
    "relative_design_eligible",
    "within_lambda_design_eligible",
    "absolute_global_green_eligible",
    "final_recommendation_band",
    "final_green_eligible",
    "primary_blocker_summary",
)

DESIGN_CLAIM_GOVERNANCE_FIELDS = (
    *MINIMUM_OUTPUT_SCHEMA_FIELDS,
    "minimum_output_schema_version",
    "minimum_output_schema_status",
    "minimum_output_schema_missing_fields",
    "minimum_output_schema_columns_present",
    "detector_operator_gate_passed",
    "detector_operator_caution_flag",
    "detector_operator_caution_reason",
    "detector_resolved_relative_design_eligible",
    "relative_design_with_detector_caution",
    "double_counting_gate_passed",
    "no_double_count_guard_passed",
    "synthetic_calibration_not_unlocking_absolute",
    "recompute_manifest_gate_passed",
    "event_qc_status",
    "event_qc_gate_passed",
    "selection_function_status",
    "selection_bias_gate_passed",
    "ev_integrity_status",
    "ev_integrity_gate_passed",
    "reference_operating_point_status",
    "final_green_gate_blockers",
)

PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1 = "tsuyama_2022_nodi_table_s1"


def _freeze_governance_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_governance_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        {
            key: _freeze_governance_value(item)
            for key, item in value.items()
        }
    )


def governance_to_jsonable(value: Any) -> Any:
    """Return frozen governance tables as plain JSON-serializable containers."""
    if isinstance(value, Mapping):
        return {
            str(key): governance_to_jsonable(item) for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [governance_to_jsonable(item) for item in value]
    return value


PAPER_ALIGNMENT_TARGETS: Mapping[str, Mapping[str, Any]] = _freeze_mapping({
    PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1: {
        "description": (
            "Tsuyama 2022 NODI Table S1 wavelength, channel-geometry, "
            "gold/silver signal-ratio, and gold-size-response audit target."
        ),
        "paper": "Tsuyama 2022",
        "assay_family": "NODI",
        "comparable_dims": (
            "wavelength_nm",
            "channel_width_nm",
            "channel_depth_nm",
            "particle_material",
            "particle_diameter_nm",
        ),
        "particle_types": ("gold", "silver"),
        "wavelengths_nm": (488, 532, 660),
        "channel_geometries_nm": ((800, 550), (1200, 550)),
        "required_metadata_fields": {
            "nodi_lockin_frequency_Hz": {
                "aliases": ("nodi_lockin_frequency_Hz", "lockin_freq_Hz"),
                "range": (2500.0, 3500.0),
            },
            "threshold_sigma": {"allowed": (5.0, 10.0)},
            "min_peak_width_s": {"range": (0.0020, 0.0030)},
            "readout_observable_mode": {"allowed": ("magnitude",)},
            "pulse_detection_mode": {"allowed": ("positive",)},
        },
    },
})

CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS = (
    "paper_aligned_2022_nodi_proxy_lens"
)
CLAIM_LEVEL_ENGINEERING_RELATIVE = "engineering_relative"
CLAIM_LEVELS: Mapping[str, Mapping[str, Any]] = _freeze_mapping({
    CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS: {
        "description": (
            "Selected-annulus engineering proxy lens for Tsuyama 2022 NODI "
            "paper-alignment audits; not an absolute experimental calibration."
        ),
        "comparable_dims": (
            "within_declared_paper_alignment_target",
            "within_selected_annulus_source",
            "within_recorded_edge_norm_bounds",
        ),
        "absolute_claim_allowed": False,
    },
    CLAIM_LEVEL_ENGINEERING_RELATIVE: {
        "description": "Engineering relative comparison without paper-aligned calibration.",
        "comparable_dims": ("within_same_model_contract",),
        "absolute_claim_allowed": False,
    },
})


def require_paper_alignment_target(value: str) -> str:
    if value not in PAPER_ALIGNMENT_TARGETS:
        raise ValueError(f"Unknown paper_alignment_target: {value!r}")
    return value


def require_claim_level(value: str) -> str:
    if value not in CLAIM_LEVELS:
        raise ValueError(f"Unknown claim_level: {value!r}")
    return value


def assert_paper_alignment_target_metadata(
    target: str,
    metadata: Mapping[str, Any],
) -> None:
    """Validate readout metadata required by a paper-alignment target."""
    target = require_paper_alignment_target(target)
    constraints = PAPER_ALIGNMENT_TARGETS[target].get("required_metadata_fields", {})
    for field, rule in constraints.items():
        value = _metadata_value(metadata, field, tuple(rule.get("aliases", ())))
        if _is_missing(value):
            raise ValueError(
                f"paper_alignment_target {target!r} requires metadata field {field!r}"
            )
        if "allowed" in rule and not _value_in_allowed(value, rule["allowed"]):
            raise ValueError(
                f"paper_alignment_target {target!r} metadata {field!r}={value!r} "
                f"is outside allowed values {tuple(rule['allowed'])!r}"
            )
        if "range" in rule and not _value_in_range(value, rule["range"]):
            raise ValueError(
                f"paper_alignment_target {target!r} metadata {field!r}={value!r} "
                f"is outside range {tuple(rule['range'])!r}"
            )


CLAIM_COMPATIBILITY_FIELDS: dict[str, tuple[str, ...]] = {
    "within_declared_paper_alignment_target": ("paper_alignment_target",),
    "within_selected_annulus_source": ("selected_annulus_source",),
    "within_recorded_edge_norm_bounds": (
        "selected_annulus_edge_norm_min",
        "selected_annulus_edge_norm_max",
    ),
    "within_same_model_contract": ("schema", "analysis_lane"),
}


def assert_claim_compatibility(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    claim_level: str,
) -> None:
    """Assert two result metadata payloads are comparable under a claim level."""
    claim_level = require_claim_level(claim_level)
    if "claim_level" in left and str(left["claim_level"]) != claim_level:
        raise ValueError("left metadata claim_level does not match requested claim")
    if "claim_level" in right and str(right["claim_level"]) != claim_level:
        raise ValueError("right metadata claim_level does not match requested claim")
    for dim in CLAIM_LEVELS[claim_level].get("comparable_dims", ()):
        for field in CLAIM_COMPATIBILITY_FIELDS.get(str(dim), (str(dim),)):
            left_value = _metadata_value(left, field)
            right_value = _metadata_value(right, field)
            if _is_missing(left_value) or _is_missing(right_value):
                raise ValueError(
                    f"claim_level {claim_level!r} requires comparable field {field!r}"
                )
            if not _values_equal(left_value, right_value):
                raise ValueError(
                    f"claim_level {claim_level!r} incompatible field {field!r}: "
                    f"{left_value!r} != {right_value!r}"
                )


def _metadata_value(
    metadata: Mapping[str, Any],
    field: str,
    aliases: tuple[str, ...] = (),
) -> Any:
    for key in (field, *aliases):
        if key in metadata and not _is_missing(metadata[key]):
            return metadata[key]
    return None


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, Real):
        return isnan(value)
    return False


def _value_in_allowed(value: Any, allowed: tuple[Any, ...]) -> bool:
    return any(_values_equal(value, candidate) for candidate in allowed)


def _value_in_range(value: Any, bounds: tuple[Any, Any]) -> bool:
    try:
        numeric = float(value)
        lower = float(bounds[0])
        upper = float(bounds[1])
    except (TypeError, ValueError):
        return False
    return lower <= numeric <= upper


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, Real) and isinstance(right, Real):
        return abs(float(left) - float(right)) <= 1e-12
    return left == right


def _as_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return value if value is not None else {}


def _get(
    primary: Mapping[str, Any],
    secondary: Mapping[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    if key in primary and primary[key] is not None:
        return primary[key]
    if key in secondary and secondary[key] is not None:
        return secondary[key]
    return default


def _as_bool(value: Any, default: bool = False) -> bool:
    """Interpret optional gate values without treating NaN as truthy."""
    if value is None:
        return default
    if isinstance(value, Real) and isnan(value):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "passed", "pass"}:
            return True
        if normalized in {
            "false",
            "0",
            "no",
            "n",
            "failed",
            "fail",
            "nan",
            "none",
            "null",
            "na",
            "n/a",
            "",
        }:
            return False
        if normalized.startswith(
            (
                "unavailable",
                "unknown",
                "missing",
                "not_available",
                "not_configured",
            )
        ):
            return False
        return default
    return bool(value)


def _case_id(
    particle: Particle,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
) -> str:
    wavelength_nm = round(float(optical.wavelength_m) * 1e9)
    width_nm = round(float(channel.width_m) * 1e9)
    depth_nm = round(float(channel.depth_m) * 1e9)
    return (
        f"{particle.name}|W={width_nm}nm|H={depth_nm}nm|lambda={wavelength_nm}nm"
        f"|objective={sim_cfg.objective_candidate_id}"
        f"|normalization={sim_cfg.normalization_mode}"
        f"|readout={sim_cfg.readout_preset}"
    )


def _final_band(final_green_eligible: bool, blockers: list[str]) -> str:
    if final_green_eligible:
        return "green_eligible_pending_design_score"
    if any(
        blocker
        in {
            "double_counting_guard_not_passed",
            "recompute_manifest_missing",
        }
        for blocker in blockers
    ):
        return "exploratory_only"
    if blockers == ["detector_operator_gate_not_passed"]:
        return "yellow_detector_operator_caution"
    return "yellow_max_pending_gate_closure"


def build_design_claim_governance_diagnostics(
    particle: Particle,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    *,
    reference: Mapping[str, Any] | None = None,
    summary: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """Build roadmap-43 minimum-schema fields and the conservative green gate."""
    reference_map = _as_mapping(reference)
    summary_map = _as_mapping(summary)

    detector_disagreement = _get(
        reference_map,
        summary_map,
        "detector_operator_disagreement_band",
        "unavailable_no_roi_mode_overlap_lane",
    )
    detector_gate = _as_bool(
        _get(reference_map, summary_map, "detector_operator_gate_passed", False)
    )
    detector_operator_caution_flag = bool(
        (not detector_gate)
        or str(detector_disagreement)
        in {"large", "unavailable_no_roi_mode_overlap_lane"}
    )
    detector_operator_caution_reason = (
        "none"
        if not detector_operator_caution_flag
        else (
            "detector_operator_large_or_missing_blocks_absolute_claim_only"
            if str(detector_disagreement)
            in {"large", "unavailable_no_roi_mode_overlap_lane"}
            else "detector_operator_gate_blocks_absolute_claim_only"
        )
    )

    perturbation_mode = str(
        _get(
            reference_map,
            summary_map,
            "particle_induced_channel_perturbation_model",
            sim_cfg.particle_induced_channel_perturbation_model,
        )
    )
    double_counting_risk = _get(
        reference_map,
        summary_map,
        "double_counting_risk_band",
        (
            "unavailable_no_particle_channel_double_count_guard"
            if perturbation_mode == "not_applied"
            else "unavailable_particle_channel_perturbation_guard_required"
        ),
    )
    raw_double_counting_guard = _as_bool(
        _get(reference_map, summary_map, "no_double_count_guard_passed", False)
    )
    double_counting_gate = raw_double_counting_guard and str(
        double_counting_risk
    ) not in {
        "high",
        "unavailable_particle_channel_guard_required",
        "unavailable_particle_channel_perturbation_guard_required",
        "unavailable_mie_forward_reference",
        "unavailable_model_not_implemented",
    }

    manifest_id = _get(
        reference_map,
        summary_map,
        "manifest_id",
        "unavailable_no_recompute_manifest",
    )
    manifest_gate = _as_bool(
        _get(reference_map, summary_map, "recompute_manifest_gate_passed", False)
    )

    event_qc_pass_fraction = _get(
        reference_map,
        summary_map,
        "event_qc_pass_fraction",
        None,
    )
    event_qc_status = _get(
        reference_map,
        summary_map,
        "event_qc_status",
        "unavailable_no_event_qc_lane",
    )
    event_qc_gate = _as_bool(
        _get(reference_map, summary_map, "event_qc_gate_passed", False)
    )

    selection_bias_warning = _get(
        reference_map,
        summary_map,
        "selection_bias_warning",
        "unavailable_selection_function_not_implemented",
    )
    selection_status = _get(
        reference_map,
        summary_map,
        "selection_function_status",
        "unavailable_no_selection_function_lane",
    )
    selection_gate = _as_bool(
        _get(reference_map, summary_map, "selection_bias_gate_passed", False)
    )

    ev_integrity_claim = _get(
        reference_map,
        summary_map,
        "ev_integrity_claim_level",
        "unavailable_ev_integrity_diagnostic_not_implemented",
    )
    ev_integrity_status = _get(
        reference_map,
        summary_map,
        "ev_integrity_status",
        "unavailable_no_ev_integrity_lane",
    )
    ev_integrity_gate = _as_bool(
        _get(reference_map, summary_map, "ev_integrity_gate_passed", False)
    )

    reference_operating_band = _get(
        reference_map,
        summary_map,
        "reference_operating_band",
        "unavailable_no_reference_operating_point_metrics",
    )
    reference_operating_status = _get(
        reference_map,
        summary_map,
        "reference_operating_point_status",
        "unavailable_no_reference_operating_point_metrics",
    )

    synthetic_calibration_active = _as_bool(
        _get(reference_map, summary_map, "calibration_synthetic_fixture_active", False)
    )
    output_claim = str(
        _get(
            reference_map,
            summary_map,
            "output_claim_level_resolved",
            _get(reference_map, summary_map, "output_claim_level", "unknown"),
        )
    )
    synthetic_gate = not (
        synthetic_calibration_active
        and output_claim
        in {
            "absolute_calibrated",
            "reference_calibrated_absolute",
            "detector_unit_absolute",
        }
    )

    exposure_gate = _as_bool(
        _get(reference_map, summary_map, "optical_exposure_safety_gate_passed", False)
    ) and _as_bool(_get(reference_map, summary_map, "exposure_safety_not_red", False))

    # Keys describe the failure condition; True means the gate is met and not a blocker.
    gate_checks = {
        "unit_axis_convention_gate_not_passed": _as_bool(
            _get(
                reference_map,
                summary_map,
                "unit_axis_convention_hard_gate_passed",
                False,
            )
        ),
        "mie_validation_gate_not_passed": _as_bool(
            _get(reference_map, summary_map, "mie_validation_hard_gate_passed", False)
        ),
        "cross_wavelength_claim_gate_not_passed": _as_bool(
            _get(reference_map, summary_map, "cross_wavelength_claim_gate_passed", False)
        ),
        "readout_semantics_gate_not_passed": _as_bool(
            _get(reference_map, summary_map, "nodi_readout_semantics_gate_passed", False)
        ),
        "detector_operator_gate_not_passed": detector_gate,
        "double_counting_guard_not_passed": double_counting_gate,
        "objective_profile_gate_not_passed": _as_bool(
            _get(reference_map, summary_map, "objective_profile_gate_passed", False)
        ),
        "optical_exposure_safety_gate_not_passed": exposure_gate,
        "synthetic_calibration_unlock_guard_not_passed": synthetic_gate,
        "recompute_manifest_missing": manifest_gate,
    }
    blockers = [code for code, passed in gate_checks.items() if not passed]

    if reference_operating_band == "unavailable_no_reference_operating_point_metrics":
        blockers.append("reference_operating_band_unavailable")
    elif reference_operating_band in {
        "reference_too_weak",
        "reference_saturation_risk",
        "rin_or_leakage_risk",
    }:
        blockers.append("reference_operating_band_risk")
    if event_qc_pass_fraction is None or not event_qc_gate:
        blockers.append("event_qc_unavailable")
    if not selection_gate:
        blockers.append("selection_function_unavailable")
    if not ev_integrity_gate:
        blockers.append("ev_integrity_unavailable")

    final_green_eligible = not blockers
    engineering_gate_passed = _as_bool(
        _get(reference_map, summary_map, "engineering_gate_passed", False)
    )
    within_lambda_ranking_allowed = _as_bool(
        _get(
            reference_map,
            summary_map,
            "within_lambda_geometry_ranking_allowed",
            False,
        )
    )
    readout_semantics_gate = _as_bool(
        _get(reference_map, summary_map, "nodi_readout_semantics_gate_passed", False)
    )
    relative_design_eligible = bool(
        engineering_gate_passed
        and readout_semantics_gate
        and double_counting_gate
        and manifest_gate
        and event_qc_gate
        and selection_gate
        and ev_integrity_gate
    )
    within_lambda_design_eligible = bool(
        relative_design_eligible and within_lambda_ranking_allowed
    )
    # Historical schema name: this only says the detector-operator gate did not
    # block relative/proxy design ranking. It must not be read as permission to
    # publish a detector-resolved or absolute wavelength winner.
    detector_resolved_relative_design_eligible = bool(
        relative_design_eligible and detector_gate
    )
    relative_design_with_detector_caution = bool(
        relative_design_eligible and detector_operator_caution_flag
    )
    absolute_global_green_eligible = bool(final_green_eligible)
    final_recommendation_band = _final_band(final_green_eligible, blockers)

    payload: dict[str, object] = {
        "case_id": _case_id(particle, channel, optical, sim_cfg),
        "manifest_id": manifest_id,
        "particle_preset_id": str(particle.name),
        "particle_size_convention": _get(
            reference_map,
            summary_map,
            "particle_size_convention",
            "unavailable",
        ),
        "particle_radius_m": float(
            _get(reference_map, summary_map, "particle_radius_m", particle.radius_m)
        ),
        "particle_diameter_m": float(
            _get(
                reference_map,
                summary_map,
                "particle_diameter_m",
                2.0 * particle.radius_m,
            )
        ),
        "W_nm": round(float(channel.width_m) * 1e9),
        "H_nm": round(float(channel.depth_m) * 1e9),
        "lambda_nm": round(float(optical.wavelength_m) * 1e9),
        "objective_candidate_id": _get(
            reference_map,
            summary_map,
            "objective_candidate_id",
            sim_cfg.objective_candidate_id,
        ),
        "normalization_scope": str(sim_cfg.normalization_mode),
        "wavelength_ranking_claim_level": _get(
            reference_map,
            summary_map,
            "wavelength_ranking_claim_level",
            "unavailable",
        ),
        "detector_forward_model": _get(
            reference_map,
            summary_map,
            "detector_forward_model",
            sim_cfg.detector_forward_model,
        ),
        "detector_operator_disagreement_band": detector_disagreement,
        "readout_semantics": _get(
            reference_map,
            summary_map,
            "nodi_readout_semantics",
            sim_cfg.nodi_readout_semantics,
        ),
        "readout_observable_mode": str(sim_cfg.readout_observable_mode),
        "polarity_claim_allowed": bool(
            _get(
                reference_map,
                summary_map,
                "readout_phase_locked_claim_allowed",
                False,
            )
        ),
        "E_ref_route": _get(
            reference_map,
            summary_map,
            "reference_route",
            _get(reference_map, summary_map, "reference_solver_route", "unavailable"),
        ),
        "reference_operating_band": reference_operating_band,
        "particle_channel_perturbation_mode": perturbation_mode,
        "double_counting_risk_band": double_counting_risk,
        "unit_axis_convention_status": _get(
            reference_map,
            summary_map,
            "unit_axis_convention_status",
            "unavailable",
        ),
        "mie_validation_status": _get(
            reference_map,
            summary_map,
            "mie_validation_status",
            "unavailable",
        ),
        "event_qc_pass_fraction": event_qc_pass_fraction,
        "selection_bias_warning": selection_bias_warning,
        "safe_power_claim_level": _get(
            reference_map,
            summary_map,
            "safe_power_claim_level",
            "unavailable",
        ),
        "ev_integrity_claim_level": ev_integrity_claim,
        "calibration_state": _get(
            reference_map,
            summary_map,
            "calibration_state_machine_status",
            "unavailable",
        ),
        "output_claim_level_resolved": output_claim,
        "relative_design_eligible": relative_design_eligible,
        "within_lambda_design_eligible": within_lambda_design_eligible,
        "absolute_global_green_eligible": absolute_global_green_eligible,
        "final_recommendation_band": final_recommendation_band,
        "final_green_eligible": final_green_eligible,
        "primary_blocker_summary": "none" if not blockers else " / ".join(blockers),
        "minimum_output_schema_version": "roadmap_43_minimum_v1",
        "minimum_output_schema_status": "present_with_blockers",
        "minimum_output_schema_missing_fields": [],
        "minimum_output_schema_columns_present": True,
        "detector_operator_gate_passed": detector_gate,
        "detector_operator_caution_flag": detector_operator_caution_flag,
        "detector_operator_caution_reason": detector_operator_caution_reason,
        "detector_resolved_relative_design_eligible": (
            detector_resolved_relative_design_eligible
        ),
        "relative_design_with_detector_caution": relative_design_with_detector_caution,
        "double_counting_gate_passed": double_counting_gate,
        "no_double_count_guard_passed": double_counting_gate,
        "synthetic_calibration_not_unlocking_absolute": synthetic_gate,
        "recompute_manifest_gate_passed": manifest_gate,
        "event_qc_status": event_qc_status,
        "event_qc_gate_passed": event_qc_gate,
        "selection_function_status": selection_status,
        "selection_bias_gate_passed": selection_gate,
        "ev_integrity_status": ev_integrity_status,
        "ev_integrity_gate_passed": ev_integrity_gate,
        "reference_operating_point_status": reference_operating_status,
        "final_green_gate_blockers": tuple(blockers),
    }

    missing_fields = [
        field for field in MINIMUM_OUTPUT_SCHEMA_FIELDS if field not in payload
    ]
    payload["minimum_output_schema_missing_fields"] = tuple(missing_fields)
    payload["minimum_output_schema_columns_present"] = not missing_fields
    if missing_fields:
        payload["minimum_output_schema_status"] = "schema_hard_fail_missing_columns"
    elif blockers:
        payload["minimum_output_schema_status"] = "present_with_blockers"
    else:
        payload["minimum_output_schema_status"] = "present_green_gate_clear"

    return payload
