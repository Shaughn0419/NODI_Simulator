"""
NODI Interferometric Simulator — Interferometric Trace Module

This is the CORE of the NODI detection model.

Combines reference field E_ref with scattering field E_sca(t) to produce
the interferometric detection signal:

    E_det(t) = E_ref + E_sca(t)
    I_det(t) = |E_det(t)|²
    signal_trace(t) = I_det(t) - |E_ref|²

Physical interpretation:
    signal_trace = |E_sca|² + 2·Re(E_ref · E_sca*)

In the weak scattering limit (|E_sca| ≪ |E_ref|):
    signal_trace ≈ 2·Re(E_ref · E_sca*)

This interference cross-term is what makes NODI sensitive to weak scatterers.
"""

import numpy as np

from .data_objects import SimulationConfig


def generate_interferometric_trace(
    trajectory: dict,
    reference: dict,
    scattering_trace: dict,
    sim_cfg: SimulationConfig,
    *,
    export_full_diagnostics: bool = True,
) -> dict:
    """
    Generate the interferometric detection signal.

    Args:
        trajectory: dict from simulate_particle_trajectory (provides time_s).
        reference: dict from compute_reference_field.
        scattering_trace: dict from compute_scattering_field_trace.
        sim_cfg: Simulation configuration.
        export_full_diagnostics: When False, omit alternate diagnostic arrays
            that are not consumed by stream-summary block paths.

    Returns:
        dict with:
            time_s: np.ndarray — time array
            E_det_complex: np.ndarray (complex) — total detected field
            I_det: np.ndarray (float >= 0) — detected intensity
            I_baseline: float — background intensity |E_ref|²
            signal_trace: np.ndarray (float) — baseline-subtracted signal
    """
    overlap_factor = complex(
        reference.get("interference_overlap_factor_complex", 1.0 + 0.0j)
    )

    if (
        not export_full_diagnostics
        and "A_ref_trace" in reference
        and "phi_ref_trace_rad" in reference
        and "A_sca" in scattering_trace
        and (
            "phi_sca_unwrapped_rad" in scattering_trace
            or "phi_sca_rad" in scattering_trace
        )
    ):
        A_ref = np.asarray(reference["A_ref_trace"], dtype=float)
        phi_ref = np.asarray(reference["phi_ref_trace_rad"], dtype=float)
        A_sca = np.asarray(scattering_trace["A_sca"], dtype=float)
        phi_sca_source = (
            scattering_trace["phi_sca_unwrapped_rad"]
            if "phi_sca_unwrapped_rad" in scattering_trace
            else scattering_trace["phi_sca_rad"]
        )
        phi_sca = np.asarray(phi_sca_source, dtype=float)
        if A_ref.ndim == 0:
            A_ref = np.full_like(A_sca, float(A_ref), dtype=float)
        if phi_ref.ndim == 0:
            phi_ref = np.full_like(A_sca, float(phi_ref), dtype=float)
        if A_ref.shape != A_sca.shape or phi_ref.shape != A_sca.shape:
            raise ValueError(
                "Reference amplitude/phase trace shapes must match A_sca. "
                f"Got A_ref {A_ref.shape}, phi_ref {phi_ref.shape}, "
                f"and A_sca {A_sca.shape}."
            )
        if phi_sca.shape != A_sca.shape:
            raise ValueError(
                "Scattering phase trace shape must match A_sca. "
                f"Got phi_sca {phi_sca.shape} and A_sca {A_sca.shape}."
            )

        if not sim_cfg.reference_interference_on:
            A_ref = np.zeros_like(A_sca, dtype=float)

        I_baseline_trace = A_ref * A_ref
        I_baseline = float(np.mean(I_baseline_trace))
        scattering_only_intensity = A_sca * A_sca
        phase_delta = phi_ref - phi_sca
        if sim_cfg.interference_overlap_mode == "joint_overlap_integrated":
            interference_cross_term = (
                2.0
                * float(abs(overlap_factor))
                * A_ref
                * A_sca
                * np.cos(phase_delta + float(np.angle(overlap_factor)))
            )
            interference_cross_term_mode = "joint_overlap_integrated"
        else:
            interference_cross_term = 2.0 * A_ref * A_sca * np.cos(phase_delta)
            interference_cross_term_mode = "collapsed_then_multiplied"
        if sim_cfg.background_subtraction_on:
            signal_trace = scattering_only_intensity + interference_cross_term
            I_det = I_baseline_trace + signal_trace
        else:
            signal_trace = (
                I_baseline_trace
                + scattering_only_intensity
                + interference_cross_term
            )
            I_det = signal_trace
        return {
            "I_det": I_det,
            "I_baseline": I_baseline,
            "I_baseline_trace": I_baseline_trace,
            "signal_trace": signal_trace,
            "interference_cross_term": interference_cross_term,
            "interference_cross_term_mode": interference_cross_term_mode,
            "interference_overlap_factor_complex": overlap_factor,
            "interference_overlap_factor_abs": float(abs(overlap_factor)),
            "interference_overlap_factor_phase_rad": float(np.angle(overlap_factor)),
            "interference_overlap_status": str(
                reference.get(
                    "interference_overlap_status",
                    "unavailable_no_reference_angular_field",
                )
            ),
        }

    E_ref = (
        reference["E_ref_trace_complex"]
        if "E_ref_trace_complex" in reference
        else reference["E_ref_complex"]
    )
    E_sca = np.asarray(scattering_trace["E_sca_complex"], dtype=complex)
    E_ref = np.asarray(E_ref, dtype=complex)
    if E_ref.ndim == 0:
        E_ref = np.full_like(E_sca, complex(E_ref), dtype=complex)
    elif E_ref.shape != E_sca.shape:
        raise ValueError(
            "Reference field trace shape must match E_sca_complex. "
            f"Got E_ref shape {E_ref.shape} and E_sca shape {E_sca.shape}."
        )

    if not sim_cfg.reference_interference_on:
        E_ref = np.zeros_like(E_sca, dtype=complex)

    I_baseline_trace = np.abs(E_ref) ** 2
    I_baseline = float(np.mean(I_baseline_trace))
    scattering_only_intensity = (E_sca * np.conj(E_sca)).real

    if not export_full_diagnostics:
        if sim_cfg.interference_overlap_mode == "joint_overlap_integrated":
            interference_cross_term = 2.0 * np.real(
                overlap_factor * E_ref * np.conj(E_sca)
            )
            interference_cross_term_mode = "joint_overlap_integrated"
        else:
            interference_cross_term = 2.0 * np.real(E_ref * np.conj(E_sca))
            interference_cross_term_mode = "collapsed_then_multiplied"
        if sim_cfg.background_subtraction_on:
            signal_trace = scattering_only_intensity + interference_cross_term
            I_det = I_baseline_trace + signal_trace
        else:
            signal_trace = (
                I_baseline_trace
                + scattering_only_intensity
                + interference_cross_term
            )
            I_det = signal_trace
        return {
            "I_det": I_det,
            "I_baseline": I_baseline,
            "I_baseline_trace": I_baseline_trace,
            "signal_trace": signal_trace,
            "interference_cross_term": interference_cross_term,
            "interference_cross_term_mode": interference_cross_term_mode,
            "interference_overlap_factor_complex": overlap_factor,
            "interference_overlap_factor_abs": float(abs(overlap_factor)),
            "interference_overlap_factor_phase_rad": float(np.angle(overlap_factor)),
            "interference_overlap_status": str(
                reference.get(
                    "interference_overlap_status",
                    "unavailable_no_reference_angular_field",
                )
            ),
        }

    # Total detected scalar surrogate field. In joint-overlap mode this remains
    # an amplitude diagnostic; the selected intensity is assembled from the
    # overlap integral below and is not guaranteed to satisfy I=|E_det|^2.
    E_det = E_ref + E_sca

    # Collapsed scalar intensity
    I_det_collapsed_scalar = (E_det * np.conj(E_det)).real

    interference_cross_term_collapsed = 2.0 * np.real(E_ref * np.conj(E_sca))
    interference_cross_term_joint = 2.0 * np.real(overlap_factor * E_ref * np.conj(E_sca))
    if sim_cfg.background_subtraction_on:
        signal_trace_collapsed_scalar = (
            scattering_only_intensity + interference_cross_term_collapsed
        )
        I_det_collapsed_scalar = I_baseline_trace + signal_trace_collapsed_scalar
        signal_trace_joint_overlap = (
            scattering_only_intensity + interference_cross_term_joint
        )
        I_det_joint_overlap = I_baseline_trace + signal_trace_joint_overlap
    else:
        signal_trace_collapsed_scalar = (
            I_baseline_trace
            + scattering_only_intensity
            + interference_cross_term_collapsed
        )
        I_det_collapsed_scalar = signal_trace_collapsed_scalar
        signal_trace_joint_overlap = (
            I_baseline_trace
            + scattering_only_intensity
            + interference_cross_term_joint
        )
        I_det_joint_overlap = signal_trace_joint_overlap

    if sim_cfg.interference_overlap_mode == "joint_overlap_integrated":
        interference_cross_term = interference_cross_term_joint
        interference_cross_term_mode = "joint_overlap_integrated"
        E_det_complex_physical_status = (
            "scalar_surrogate_not_intensity_consistent_joint_overlap_selected"
        )
    else:
        interference_cross_term = interference_cross_term_collapsed
        interference_cross_term_mode = "collapsed_then_multiplied"
        E_det_complex_physical_status = "scalar_field_intensity_consistent"

    if sim_cfg.background_subtraction_on:
        signal_trace = (
            signal_trace_joint_overlap
            if sim_cfg.interference_overlap_mode == "joint_overlap_integrated"
            else signal_trace_collapsed_scalar
        )
        I_det = I_baseline_trace + signal_trace
    else:
        signal_trace = (
            signal_trace_joint_overlap
            if sim_cfg.interference_overlap_mode == "joint_overlap_integrated"
            else signal_trace_collapsed_scalar
        )
        I_det = signal_trace

    return {
        "time_s": trajectory["time_s"].copy(),
        "E_det_complex": E_det,
        "E_det_complex_scalar_surrogate": E_det,
        "E_det_complex_physical_status": E_det_complex_physical_status,
        "E_ref_complex": E_ref,
        "I_det": I_det,
        "I_det_collapsed_scalar_surrogate": I_det_collapsed_scalar,
        "I_det_joint_overlap": I_det_joint_overlap,
        "I_baseline": I_baseline,
        "I_baseline_trace": I_baseline_trace,
        "signal_trace": signal_trace,
        "signal_trace_collapsed_scalar_surrogate": signal_trace_collapsed_scalar,
        "signal_trace_joint_overlap": signal_trace_joint_overlap,
        "scattering_only_intensity": scattering_only_intensity,
        "interference_cross_term": interference_cross_term,
        "interference_cross_term_collapsed": interference_cross_term_collapsed,
        "interference_cross_term_joint": interference_cross_term_joint,
        "interference_cross_term_mode": interference_cross_term_mode,
        "interference_overlap_factor_complex": overlap_factor,
        "interference_overlap_factor_abs": float(abs(overlap_factor)),
        "interference_overlap_factor_phase_rad": float(np.angle(overlap_factor)),
        "interference_overlap_status": str(
            reference.get("interference_overlap_status", "unavailable_no_reference_angular_field")
        ),
    }
