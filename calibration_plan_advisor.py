"""Static blocker-to-experiment calibration advisor."""

from __future__ import annotations

from collections.abc import Mapping


CALIBRATION_PLAN_ADVISOR_FIELDS = (
    "calibration_plan_status",
    "calibration_plan_claim_level",
    "calibration_plan_calibrated_claim_unlocked",
    "calibration_plan_blocker_count",
    "required_calibration_experiments",
    "calibration_plan_priority_order",
    "calibration_plan_reason_codes",
    "calibration_plan_guidance",
)


_EXPERIMENT_PRIORITY = (
    "blank_channel_bfp_reference_image_by_W_H_lambda",
    "slit_scan_or_pinhole_roi_mapping",
    "multi_wavelength_power_responsivity_filter_reference_calibration",
    "Au20_Au30_Au40_standard_particle_trace_panel",
    "blank_buffer_trace_false_positive_bootstrap",
    "flow_velocity_and_pressure_drop_calibration",
    "probe_power_and_beam_waist_exposure_calibration",
    "lockin_electronics_transfer_function_measurement",
    "working_distance_and_chip_clearance_check",
    "orthogonal_ev_reporting_and_assay_control_panel",
)

_RULES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (
        (
            "cross_wavelength",
            "probe_power_by_wavelength",
            "detector_responsivity_by_wavelength",
            "filter_transmission_by_wavelength",
            "reference_calibration_by_wavelength",
            "wavelength_specific",
        ),
        "multi_wavelength_power_responsivity_filter_reference_calibration",
        "wavelength_lane_calibration_missing",
    ),
    (
        (
            "detector_operator",
            "bfp_roi",
            "bfp_pixel",
            "mode_overlap",
            "pinhole",
            "slit",
        ),
        "slit_scan_or_pinhole_roi_mapping",
        "detector_operator_or_bfp_mapping_missing",
    ),
    (
        (
            "reference_operating_band_unavailable",
            "reference_blank",
            "blank_channel",
            "calibrated_lookup",
            "requires_blank_or_fullwave",
            "g_ref",
        ),
        "blank_channel_bfp_reference_image_by_W_H_lambda",
        "blank_reference_calibration_missing",
    ),
    (
        (
            "standard_particle",
            "k_sca",
            "standard_calibration",
            "missing_standard",
            "au20",
            "au30",
            "au40",
        ),
        "Au20_Au30_Au40_standard_particle_trace_panel",
        "standard_particle_calibration_missing",
    ),
    (
        (
            "blank_false_positive",
            "raw_blank",
            "threshold_from_blank",
            "empirical_blank",
            "event_qc",
            "false_alarm",
        ),
        "blank_buffer_trace_false_positive_bootstrap",
        "blank_false_positive_or_event_qc_missing",
    ),
    (
        (
            "flow_velocity",
            "pressure_drop",
            "fluidic",
            "electrokinetic",
            "count_prediction",
            "wall_interaction",
        ),
        "flow_velocity_and_pressure_drop_calibration",
        "flow_or_transport_calibration_missing",
    ),
    (
        (
            "optical_exposure",
            "safe_power",
            "probe_power_missing",
            "photodamage",
            "beam_waist",
            "power_density",
        ),
        "probe_power_and_beam_waist_exposure_calibration",
        "exposure_safety_calibration_missing",
    ),
    (
        (
            "readout_semantics",
            "measured_transfer",
            "lockin",
            "sampling_hard_gate",
            "carrier_underresolved",
        ),
        "lockin_electronics_transfer_function_measurement",
        "readout_transfer_measurement_missing",
    ),
    (
        (
            "working_distance",
            "objective_profile",
            "chip_clearance",
        ),
        "working_distance_and_chip_clearance_check",
        "objective_hardware_clearance_missing",
    ),
    (
        (
            "ev_reporting",
            "assay_control",
            "ev_specificity",
            "biological_specificity",
        ),
        "orthogonal_ev_reporting_and_assay_control_panel",
        "ev_specificity_controls_missing",
    ),
)


def _flatten_blocker_text(diagnostics: Mapping[str, object]) -> str:
    parts: list[str] = []
    for key, value in diagnostics.items():
        key_text = str(key)
        if value is None or value is False:
            continue
        if isinstance(value, Mapping) or hasattr(value, "shape"):
            continue
        if isinstance(value, (list, tuple, set)):
            scalar_items = [
                str(item)
                for item in value
                if item is not None
                and not isinstance(item, Mapping)
                and not hasattr(item, "shape")
            ]
            value_text = " ".join(scalar_items[:16])
        else:
            value_text = str(value)
        if value_text.casefold() in {"", "none", "false", "pass"}:
            continue
        if any(
            marker in key_text.casefold()
            for marker in (
                "blocker",
                "status",
                "claim",
                "gate",
                "calibration",
                "threshold",
                "fluidic",
                "readout",
                "objective",
                "wavelength",
                "selection",
                "event_qc",
            )
        ):
            parts.append(f"{key_text} {value_text}")
    return " / ".join(parts).casefold()


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _priority_sort(experiments: list[str]) -> list[str]:
    priority = {name: index for index, name in enumerate(_EXPERIMENT_PRIORITY)}
    return sorted(experiments, key=lambda item: priority.get(item, len(priority)))


def build_calibration_plan_advisor(
    diagnostics: Mapping[str, object],
) -> dict[str, object]:
    """Map existing claim blockers to a minimal next-experiment checklist."""
    blocker_text = _flatten_blocker_text(diagnostics)
    experiments: list[str] = []
    reason_codes: list[str] = []
    for tokens, experiment, reason_code in _RULES:
        if any(token in blocker_text for token in tokens):
            experiments.append(experiment)
            reason_codes.append(reason_code)

    ordered_experiments = _priority_sort(_ordered_unique(experiments))
    ordered_reasons = _ordered_unique(reason_codes)
    status = (
        "experiments_recommended"
        if ordered_experiments
        else "no_blocker_specific_experiments"
    )
    guidance = (
        "Run the listed experiments before interpreting this lane as calibrated."
        if ordered_experiments
        else "No blocker-specific calibration experiment was inferred from inputs."
    )
    return {
        "calibration_plan_status": status,
        "calibration_plan_claim_level": (
            "next_step_guidance_only_does_not_unlock_calibration"
        ),
        "calibration_plan_calibrated_claim_unlocked": False,
        "calibration_plan_blocker_count": len(ordered_reasons),
        "required_calibration_experiments": ordered_experiments,
        "calibration_plan_priority_order": list(_EXPERIMENT_PRIORITY),
        "calibration_plan_reason_codes": ordered_reasons,
        "calibration_plan_guidance": guidance,
    }
