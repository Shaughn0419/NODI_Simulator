"""Package-local polarization/Jones operator interface diagnostics."""

from __future__ import annotations

from .data_objects import SimulationConfig
from .type_coerce import blocker_summary as _blocker_summary
from .utils import resolve_polarization_coupling
import numpy as np


POLARIZATION_JONES_DIAGNOSTIC_FIELDS = (
    "polarization_jones_operator_mode",
    "polarization_jones_operator_status",
    "polarization_jones_operator_claim_level",
    "polarization_overlap_amplitude",
    "polarization_overlap_efficiency",
    "polarization_overlap_efficiency_source",
    "polarization_scattering_projection_mode",
    "polarization_illumination_effective_mode",
    "polarization_reference_effective_mode",
    "polarization_illumination_alignment_status",
    "polarization_reference_alignment_status",
    "polarization_cross_polarization_leakage",
    "measured_jones_matrix_path_configured",
    "measured_jones_matrix_validation_status",
    "measured_jones_matrix_loaded",
    "phase_polarization_quantitative_claim_allowed",
    "polarization_sensitive_classification_claim_allowed",
    "polarization_jones_gate_passed",
    "phase_polarization_claim_blocker_summary",
)


def _operator_status(mode: str, path_configured: bool) -> str:
    if mode == "scalar_projection":
        return "scalar_projection_active_jones_matrix_missing"
    if mode == "jones_pupil_surrogate":
        return "jones_pupil_surrogate_active_unmeasured"
    if path_configured:
        return "measured_jones_matrix_configured_not_loaded"
    return "measured_jones_matrix_declared_missing_path"


def _claim_level(mode: str, path_configured: bool) -> str:
    if mode == "scalar_projection":
        return "scalar_projection_surrogate_not_polarization_quantitative"
    if mode == "jones_pupil_surrogate":
        return "jones_pupil_surrogate_not_measured_matrix"
    if path_configured:
        return "measured_jones_matrix_configured_requires_p2_validator"
    return "measured_jones_matrix_missing"


def _coerce_numeric(value: object) -> float:
    if isinstance(value, (int, float, np.integer, np.floating, np.number)):
        return float(value)
    raise TypeError(f"Expected numeric scalar, got {type(value)!r}")


def build_polarization_jones_diagnostics(
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """
    Export the polarization/Jones operator claim boundary.

    P1 exposes the operator interface and scalar overlap efficiency only. It
    deliberately does not read `measured_jones_matrix_path`; measured matrix
    loading/validation belongs to the later calibration lane, so quantitative
    phase/polarization claims remain blocked here.
    """
    mode = str(sim_cfg.polarization_jones_operator_mode)
    scattering_mode = str(sim_cfg.scattering_projection_mode)
    illumination = resolve_polarization_coupling(
        str(sim_cfg.illumination_polarization_mode),
        scattering_mode,
        _coerce_numeric(sim_cfg.cross_polarization_leakage),
    )
    reference = resolve_polarization_coupling(
        str(sim_cfg.reference_projection_mode),
        scattering_mode,
        _coerce_numeric(sim_cfg.cross_polarization_leakage),
    )
    overlap_amplitude = _coerce_numeric(illumination["amplitude_factor"]) * _coerce_numeric(
        reference["amplitude_factor"]
    )
    overlap_efficiency = max(0.0, min(1.0, overlap_amplitude * overlap_amplitude))
    path_configured = bool(
        sim_cfg.measured_jones_matrix_path is not None
        and str(sim_cfg.measured_jones_matrix_path).strip()
    )

    blockers = ["measured_jones_matrix_not_validated"]
    if mode == "scalar_projection":
        blockers.append("scalar_projection_operator_not_jones_matrix")
    elif mode == "jones_pupil_surrogate":
        blockers.append("jones_pupil_surrogate_unmeasured")
    elif not path_configured:
        blockers.append("measured_jones_matrix_path_missing")

    return {
        "polarization_jones_operator_mode": mode,
        "polarization_jones_operator_status": _operator_status(
            mode,
            path_configured,
        ),
        "polarization_jones_operator_claim_level": _claim_level(
            mode,
            path_configured,
        ),
        "polarization_overlap_amplitude": overlap_amplitude,
        "polarization_overlap_efficiency": overlap_efficiency,
        "polarization_overlap_efficiency_source": (
            "scalar_projection_overlap_surrogate"
        ),
        "polarization_scattering_projection_mode": scattering_mode,
        "polarization_illumination_effective_mode": str(
            illumination["effective_mode"]
        ),
        "polarization_reference_effective_mode": str(reference["effective_mode"]),
        "polarization_illumination_alignment_status": str(
            illumination["alignment_status"]
        ),
        "polarization_reference_alignment_status": str(
            reference["alignment_status"]
        ),
        "polarization_cross_polarization_leakage": _coerce_numeric(
            illumination["cross_polarization_leakage"]
        ),
        "measured_jones_matrix_path_configured": path_configured,
        "measured_jones_matrix_validation_status": (
            "configured_but_not_loaded_or_validated_in_p1"
            if path_configured
            else "not_available_no_measured_matrix_path"
        ),
        "measured_jones_matrix_loaded": False,
        "phase_polarization_quantitative_claim_allowed": False,
        "polarization_sensitive_classification_claim_allowed": False,
        "polarization_jones_gate_passed": False,
        "phase_polarization_claim_blocker_summary": _blocker_summary(blockers),
    }
