from __future__ import annotations

import numpy as np


DETECTOR_ROUTE_IDS = (
    "A_hybrid",
    "B_roi_intensity",
    "C_collapsed_coherent",
    "D_cross_only",
)


def compute_r_self(
    reference: dict,
    E_sca_unit_normalized: complex | float,
) -> float:
    """Return the case-level self-term scale factor between routes A and B."""
    self_collapsed = float(abs(complex(E_sca_unit_normalized)) ** 2)
    self_roi = reference.get("self_sca_detector_integrated")
    if self_roi is None or not np.isfinite(float(self_roi)) or self_collapsed <= 0.0:
        return float("nan")
    return float(self_roi) / self_collapsed


def assemble_route_signal(
    trace: dict,
    route: str,
    r_self: float,
    *,
    interference_overlap_mode: str,
) -> np.ndarray:
    """Build the signed detector-route signal trace from full diagnostics."""
    route_id = str(route)
    self_t = np.asarray(trace["scattering_only_intensity"], dtype=float)
    cross_joint = np.asarray(trace["interference_cross_term_joint"], dtype=float)
    cross_collapsed = np.asarray(trace["interference_cross_term_collapsed"], dtype=float)
    if route_id == "A_hybrid":
        cross_term = (
            cross_joint
            if str(interference_overlap_mode) == "joint_overlap_integrated"
            else cross_collapsed
        )
        return self_t + cross_term
    if route_id == "B_roi_intensity":
        return float(r_self) * self_t + cross_joint
    if route_id == "C_collapsed_coherent":
        return self_t + cross_collapsed
    if route_id == "D_cross_only":
        return cross_joint
    raise ValueError(f"unknown detector route: {route_id}")


def assemble_route_trace_payload(
    trace: dict,
    *,
    route: str,
    r_self: float,
    background_subtraction_on: bool,
    interference_overlap_mode: str,
) -> dict[str, object]:
    """Return the route-specific signal and detected intensity payload."""
    route_signal = assemble_route_signal(
        trace,
        route,
        r_self,
        interference_overlap_mode=interference_overlap_mode,
    )
    baseline_trace = np.asarray(trace["I_baseline_trace"], dtype=float)
    if background_subtraction_on:
        i_det = baseline_trace + route_signal
    else:
        i_det = route_signal
    return {
        "route_signal_trace": route_signal,
        "route_detected_intensity": i_det,
    }
