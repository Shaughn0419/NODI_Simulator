"""Package-local BFP ROI detector-operator comparison diagnostics."""

from __future__ import annotations

import numpy as np

from .data_objects import SimulationConfig
from .utils import collapse_angular_field_with_operator


BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS = (
    "signal_detector_integrated",
    "cross_term_detector_integrated",
    "self_sca_detector_integrated",
    "I_ref_detector_integrated",
    "interference_overlap_efficiency",
    "roi_vs_scalar_signal_ratio",
    "roi_vs_scalar_phase_disagreement_rad",
    "mode_overlap_efficiency",
    "detector_operator_disagreement_band",
    "bfp_roi_mask_status",
    "detector_operator_gate_passed",
    "detector_operator_comparison_lane_status",
    "detector_forward_claim_level",
)


def _resample_complex_theta_field(
    source_theta_grid_rad: np.ndarray,
    field_theta_or_2d: np.ndarray,
    target_theta_grid_rad: np.ndarray,
) -> np.ndarray:
    source_theta = np.asarray(source_theta_grid_rad, dtype=float)
    target_theta = np.asarray(target_theta_grid_rad, dtype=float)
    field = np.asarray(field_theta_or_2d, dtype=complex)
    if field.ndim == 1:
        real = np.interp(target_theta, source_theta, np.real(field))
        imag = np.interp(target_theta, source_theta, np.imag(field))
        return real + 1j * imag

    cols = []
    for col_idx in range(field.shape[1]):
        real = np.interp(target_theta, source_theta, np.real(field[:, col_idx]))
        imag = np.interp(target_theta, source_theta, np.imag(field[:, col_idx]))
        cols.append(real + 1j * imag)
    return np.stack(cols, axis=1)


def _phi_vector_projection(
    theta_grid_rad: np.ndarray,
    phi_grid_rad: np.ndarray,
    scattering_projection_mode: str,
) -> np.ndarray:
    theta = theta_grid_rad[:, None]
    phi = phi_grid_rad[None, :]
    if scattering_projection_mode == "parallel":
        amplitude = np.cos(phi) * np.clip(np.sqrt((1.0 + np.cos(theta)) / 2.0), 0.0, None)
    elif scattering_projection_mode == "perpendicular":
        amplitude = np.sin(phi) * np.clip(np.sqrt((1.0 + np.cos(theta)) / 2.0), 0.0, None)
    else:
        amplitude = np.ones((len(theta_grid_rad), len(phi_grid_rad)), dtype=float)
    phase = np.exp(1j * 0.5 * np.sin(theta) * np.sin(phi))
    return amplitude * phase


def _prepare_projected_fields(
    theta_grid_rad: np.ndarray,
    reference_field_theta_or_2d: np.ndarray,
    scattering_field_theta_or_2d: np.ndarray,
    operator: dict,
    sim_cfg: SimulationConfig,
    *,
    phi_grid_rad: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    ref_field = np.asarray(reference_field_theta_or_2d, dtype=complex)
    sca_field = np.asarray(scattering_field_theta_or_2d, dtype=complex)
    theta_vals = np.asarray(theta_grid_rad, dtype=float)

    if (
        sim_cfg.collection_integration_mode != "pupil_slit_surrogate"
        and ref_field.ndim == 1
        and sca_field.ndim == 1
    ):
        return ref_field, sca_field, None

    phi_vals = (
        np.asarray(phi_grid_rad, dtype=float)
        if phi_grid_rad is not None
        else np.asarray(operator["phi_grid_rad"], dtype=float)
    )
    ref_2d = (
        ref_field
        if ref_field.ndim == 2
        else np.repeat(ref_field[:, None], len(phi_vals), axis=1)
    )
    sca_2d = (
        sca_field
        if sca_field.ndim == 2
        else np.repeat(sca_field[:, None], len(phi_vals), axis=1)
    )
    if sim_cfg.collection_integration_mode == "pupil_slit_surrogate":
        theta_center = float(operator["theta_center_rad"])
        projection_2d = _phi_vector_projection(
            theta_vals,
            phi_vals,
            sim_cfg.scattering_projection_mode,
        )
        theta_phase = np.exp(
            1j * (theta_vals[:, None] - theta_center) * np.sin(phi_vals[None, :])
        )
        ref_2d = ref_2d * projection_2d * theta_phase
        sca_2d = sca_2d * projection_2d * theta_phase
    return ref_2d, sca_2d, phi_vals


def _integrate_detector_terms(
    theta_grid_rad: np.ndarray,
    ref_field: np.ndarray,
    sca_field: np.ndarray,
    operator: dict,
    *,
    phi_grid_rad: np.ndarray | None,
) -> tuple[float, float, float, complex]:
    theta_vals = np.asarray(theta_grid_rad, dtype=float)
    theta_weights = np.asarray(operator["theta_weights"], dtype=float)
    throughput = float(operator.get("throughput_scale", 1.0))

    if ref_field.ndim == 1 and sca_field.ndim == 1:
        ref_int = np.trapezoid(theta_weights * np.abs(ref_field) ** 2, theta_vals)
        sca_int = np.trapezoid(theta_weights * np.abs(sca_field) ** 2, theta_vals)
        joint = np.trapezoid(
            theta_weights * ref_field * np.conj(sca_field),
            theta_vals,
        )
        return (
            float(ref_int * throughput),
            float(sca_int * throughput),
            float(2.0 * np.real(joint) * throughput),
            complex(joint * throughput),
        )

    if phi_grid_rad is None:
        raise ValueError("phi_grid_rad is required for 2D detector integration")
    phi_vals = np.asarray(phi_grid_rad, dtype=float)
    phi_weights = np.interp(
        phi_vals,
        operator["phi_grid_rad"],
        operator["phi_weights"],
        left=0.0,
        right=0.0,
    )
    ref_theta = np.trapezoid(np.abs(ref_field) ** 2 * phi_weights[None, :], phi_vals, axis=1)
    sca_theta = np.trapezoid(np.abs(sca_field) ** 2 * phi_weights[None, :], phi_vals, axis=1)
    joint_theta = np.trapezoid(
        ref_field * np.conj(sca_field) * phi_weights[None, :],
        phi_vals,
        axis=1,
    )
    ref_int = np.trapezoid(theta_weights * ref_theta, theta_vals)
    sca_int = np.trapezoid(theta_weights * sca_theta, theta_vals)
    joint = np.trapezoid(theta_weights * joint_theta, theta_vals)
    return (
        float(ref_int * throughput),
        float(sca_int * throughput),
        float(2.0 * np.real(joint) * throughput),
        complex(joint * throughput),
    )


def _wrap_phase_rad(value: float) -> float:
    return float((value + np.pi) % (2.0 * np.pi) - np.pi)


def _disagreement_band(signal_ratio: float | None, phase_disagreement_rad: float | None) -> str:
    if signal_ratio is None or phase_disagreement_rad is None:
        return "unavailable_no_roi_mode_overlap_lane"
    signal_error = abs(float(signal_ratio) - 1.0)
    phase_error = abs(float(phase_disagreement_rad))
    if signal_error <= 0.25 and phase_error <= 0.25:
        return "small"
    if signal_error <= 1.0 and phase_error <= 1.0:
        return "moderate"
    return "large"


def compute_detector_integrated_interference(
    theta_grid_rad: np.ndarray,
    reference_field_theta_or_2d: np.ndarray,
    scattering_field_theta_or_2d: np.ndarray,
    operator: dict,
    sim_cfg: SimulationConfig,
    *,
    reference_target_collapsed: complex | None = None,
    scattering_target_collapsed: complex | None = None,
    phi_grid_rad: np.ndarray | None = None,
    scattering_theta_grid_rad: np.ndarray | None = None,
) -> dict[str, object]:
    """Compare collapsed scalar and ROI-integrated detector interference."""
    theta_vals = np.asarray(operator.get("theta_grid_rad", theta_grid_rad), dtype=float)
    ref_eval = _resample_complex_theta_field(
        theta_grid_rad,
        reference_field_theta_or_2d,
        theta_vals,
    )
    sca_eval = _resample_complex_theta_field(
        theta_grid_rad if scattering_theta_grid_rad is None else scattering_theta_grid_rad,
        scattering_field_theta_or_2d,
        theta_vals,
    )

    ref_collapsed_raw = collapse_angular_field_with_operator(
        theta_vals,
        ref_eval,
        operator,
        sim_cfg,
        phi_grid_rad=phi_grid_rad,
    )
    sca_collapsed_raw = collapse_angular_field_with_operator(
        theta_vals,
        sca_eval,
        operator,
        sim_cfg,
        phi_grid_rad=phi_grid_rad,
    )
    if reference_target_collapsed is not None and abs(ref_collapsed_raw) > 1e-30:
        ref_eval = ref_eval * (complex(reference_target_collapsed) / ref_collapsed_raw)
    if scattering_target_collapsed is not None and abs(sca_collapsed_raw) > 1e-30:
        sca_eval = sca_eval * (complex(scattering_target_collapsed) / sca_collapsed_raw)

    ref_collapsed = collapse_angular_field_with_operator(
        theta_vals,
        ref_eval,
        operator,
        sim_cfg,
        phi_grid_rad=phi_grid_rad,
    )
    sca_collapsed = collapse_angular_field_with_operator(
        theta_vals,
        sca_eval,
        operator,
        sim_cfg,
        phi_grid_rad=phi_grid_rad,
    )
    projected_ref, projected_sca, projected_phi = _prepare_projected_fields(
        theta_vals,
        ref_eval,
        sca_eval,
        operator,
        sim_cfg,
        phi_grid_rad=phi_grid_rad,
    )
    i_ref, self_sca, cross_term, joint_overlap = _integrate_detector_terms(
        theta_vals,
        projected_ref,
        projected_sca,
        operator,
        phi_grid_rad=projected_phi,
    )
    signal_integrated = float(self_sca + cross_term)
    scalar_cross_complex = complex(ref_collapsed * np.conj(sca_collapsed))
    scalar_signal = float(abs(sca_collapsed) ** 2 + 2.0 * np.real(scalar_cross_complex))
    ratio = (
        float(abs(signal_integrated) / max(abs(scalar_signal), 1e-30))
        if np.isfinite(scalar_signal)
        else None
    )
    phase_disagreement = _wrap_phase_rad(
        float(np.angle(joint_overlap) - np.angle(scalar_cross_complex))
    )
    mode_overlap_efficiency = (
        float(abs(joint_overlap) / np.sqrt(max(i_ref * self_sca, 1e-30)))
        if i_ref > 0.0 and self_sca > 0.0
        else 0.0
    )
    band = _disagreement_band(ratio, phase_disagreement)

    return {
        "signal_detector_integrated": signal_integrated,
        "cross_term_detector_integrated": cross_term,
        "self_sca_detector_integrated": self_sca,
        "I_ref_detector_integrated": i_ref,
        "interference_overlap_efficiency": mode_overlap_efficiency,
        "roi_vs_scalar_signal_ratio": ratio,
        "roi_vs_scalar_phase_disagreement_rad": phase_disagreement,
        "mode_overlap_efficiency": mode_overlap_efficiency,
        "detector_operator_disagreement_band": band,
        "bfp_roi_mask_status": "surrogate_not_calibrated",
        "detector_operator_gate_passed": band in {"small", "moderate"},
        "detector_operator_comparison_lane_status": "roi_complex_mode_overlap_comparison_active",
        "detector_forward_claim_level": "relative_ranking_only",
    }


def build_bfp_detector_operator_diagnostics(
    reference: dict,
    collection: dict,
    sim_cfg: SimulationConfig,
    *,
    E_sca_unit_normalized_complex: complex,
) -> dict[str, object]:
    """Build detector-operator diagnostics from runtime angular fields."""
    if (
        "reference_angular_field" not in reference
        or "reference_theta_grid_rad" not in reference
        or "angular_field_theta" not in collection
        or "collection_operator" not in collection
    ):
        return {
            "detector_operator_disagreement_band": "unavailable_no_roi_mode_overlap_lane",
            "bfp_roi_mask_status": "unavailable_no_angular_roi_lane",
            "detector_operator_gate_passed": False,
            "detector_operator_comparison_lane_status": "unavailable_missing_reference_or_scattering_angular_field",
            "detector_forward_claim_level": reference.get(
                "detector_forward_claim_level",
                "coherent_surrogate_not_detector_unit",
            ),
            "signal_detector_integrated": None,
            "cross_term_detector_integrated": None,
            "self_sca_detector_integrated": None,
            "I_ref_detector_integrated": None,
            "interference_overlap_efficiency": None,
            "roi_vs_scalar_signal_ratio": None,
            "roi_vs_scalar_phase_disagreement_rad": None,
            "mode_overlap_efficiency": None,
        }

    diagnostics = compute_detector_integrated_interference(
        np.asarray(reference["reference_theta_grid_rad"], dtype=float),
        np.asarray(reference["reference_angular_field"], dtype=complex),
        np.asarray(collection["angular_field_theta"], dtype=complex),
        collection["collection_operator"],
        sim_cfg,
        reference_target_collapsed=complex(reference.get("E_ref_complex", 0.0 + 0.0j)),
        scattering_target_collapsed=complex(E_sca_unit_normalized_complex),
        phi_grid_rad=(
            np.asarray(reference["reference_phi_grid_rad"], dtype=float)
            if "reference_phi_grid_rad" in reference
            else None
        ),
        scattering_theta_grid_rad=np.asarray(collection["theta_grid_rad"], dtype=float),
    )
    mask_status = collection.get("bfp_roi_mask_status")
    if mask_status is not None:
        diagnostics["bfp_roi_mask_status"] = mask_status
    return diagnostics
