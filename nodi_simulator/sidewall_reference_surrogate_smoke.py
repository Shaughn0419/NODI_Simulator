"""NODI smoke rows using the sidewall reference surrogate.

This module executes a small NODI batch matrix that compares the legacy
rectangular reference proxy with the trapezoid effective-aperture reference
surrogate. The rows are evidence that sidewall geometry reaches the reference
branch of a real NODI run; they are not optical-solver, detection-probability,
yield, or route-winner claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import math
from typing import Any

import numpy as np

from ._exports import (
    BASELINE_PARTICLE,
    DEFAULT_SIM_CFG,
    PBS_1X,
    Channel,
    OpticalSystem,
    compute_baseline_normalization_per_wavelength,
    compute_reference_field,
    run_single_case_batch,
)


SIDEWALL_REFERENCE_SURROGATE_SMOKE_VERSION = (
    "sidewall_reference_surrogate_smoke_w500_d900_v1"
)
SIDEWALL_REFERENCE_SURROGATE_SMOKE_CLAIM_BOUNDARY = (
    "nodi_reference_surrogate_smoke_not_optical_solver_not_detection_probability"
)


@dataclass(frozen=True)
class SidewallReferenceSurrogateSmokeCase:
    case_id: str
    channel_cross_section_model: str
    sidewall_taper_angle_deg_nodi: float
    sidewall_deg_comsol: float
    width_nm: int = 500
    depth_nm: int = 900


@dataclass(frozen=True)
class SidewallReferenceSurrogateSmokeRow:
    row_id: str
    smoke_version: str
    case_id: str
    reference_model: str
    channel_cross_section_model: str
    width_nm: int
    depth_nm: int
    sidewall_taper_angle_deg_nodi: float
    sidewall_deg_comsol: float
    wavelength_nm: int
    n_events: int
    random_seed: int
    detection_rate: float
    stable_detection_rate: float
    mean_peak_height: float
    mean_local_snr: float
    A_ref: float
    g_ref: float
    g_ref_geometry: float
    trapezoid_effective_aperture_factor: float
    trapezoid_effective_aperture_width_nm: float
    bottom_width_runtime_clipped_nm: float
    bottom_width_unclipped_nm: float
    closure_status: str
    na_cutoff_condition_met: bool
    na_cutoff_active: bool
    reference_geometry_propagation_status: str
    reference_geometry_claim_level: str
    reference_solver_status: str
    reference_solver_claim_level: str
    geometry_not_propagated_to_reference_field: bool
    reference_uses_rectangular_width_depth_surrogate: bool
    not_optical_solver_output: bool
    optical_solver_trigger_is_result: bool
    optical_solver_current: bool
    true_W_eff_current: bool
    detection_probability_current: bool
    yield_current: bool
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_sidewall_reference_surrogate_smoke_cases() -> list[SidewallReferenceSurrogateSmokeCase]:
    return [
        SidewallReferenceSurrogateSmokeCase(
            case_id="rectangle_limit_theta90_D900_W500",
            channel_cross_section_model="ideal_rectangle",
            sidewall_taper_angle_deg_nodi=0.0,
            sidewall_deg_comsol=90.0,
        ),
        SidewallReferenceSurrogateSmokeCase(
            case_id="taper_theta85_D900_W500",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_taper_angle_deg_nodi=5.0,
            sidewall_deg_comsol=85.0,
        ),
    ]


def run_sidewall_reference_surrogate_smoke(
    *,
    cases: list[SidewallReferenceSurrogateSmokeCase] | None = None,
    reference_models: tuple[str, ...] = (
        "channel_angular_surrogate",
        "trapezoid_effective_aperture_surrogate",
    ),
    wavelengths_nm: tuple[int, ...] = (404, 660),
    n_events: int = 8,
    random_seed: int = 528,
) -> list[SidewallReferenceSurrogateSmokeRow]:
    """Run NODI smoke batches for legacy and sidewall reference models."""
    case_list = (
        default_sidewall_reference_surrogate_smoke_cases()
        if cases is None
        else list(cases)
    )
    theta_grid = np.linspace(1.0e-3, math.pi - 1.0e-3, 181)
    rows: list[SidewallReferenceSurrogateSmokeRow] = []
    for case in case_list:
        channel = Channel(
            width_m=float(case.width_nm) * 1.0e-9,
            depth_m=float(case.depth_nm) * 1.0e-9,
        )
        for reference_model in reference_models:
            for wavelength_nm in wavelengths_nm:
                optical = OpticalSystem(
                    wavelength_m=float(wavelength_nm) * 1.0e-9,
                    peak_irradiance_W_m2=1.0,
                    beam_waist_x_m=300e-9,
                    beam_waist_y_m=700e-9,
                    beam_waist_z_m=300e-9,
                )
                sim_cfg = replace(
                    DEFAULT_SIM_CFG,
                    total_time_s=0.09,
                    sampling_rate_Hz=10_000.0,
                    mean_flow_velocity_m_s=2.0e-4,
                    n_events=int(n_events),
                    random_seed=int(random_seed),
                    include_diffusion=False,
                    flow_profile_model="plug",
                    diffusion_hindrance_model="none",
                    reference_model=str(reference_model),
                    reference_spatial_mode="cross_section_surrogate",
                    channel_cross_section_model=case.channel_cross_section_model,
                    sidewall_taper_angle_deg=case.sidewall_taper_angle_deg_nodi,
                    readout_preset="tsuyama_2022_counting_10sigma",
                    vectorized_event_engine="off",
                )
                reference_context = compute_reference_field(channel, optical, sim_cfg)
                e_sca_ref = compute_baseline_normalization_per_wavelength(
                    BASELINE_PARTICLE,
                    PBS_1X,
                    optical,
                    np.array([optical.wavelength_m]),
                    theta_grid,
                    channel=channel,
                    sim_cfg=sim_cfg,
                )[optical.wavelength_m]
                result = run_single_case_batch(
                    BASELINE_PARTICLE,
                    PBS_1X,
                    channel,
                    optical,
                    sim_cfg,
                    e_sca_ref,
                    theta_grid,
                    retain_event_traces=False,
                    stream_summary_only=True,
                )
                summary = dict(result.get("summary", {}))
                reference_summary = dict(result.get("reference", {}))
                rows.append(
                    SidewallReferenceSurrogateSmokeRow(
                        row_id=(
                            f"REFSMOKE-{case.case_id}_{reference_model}_{wavelength_nm}"
                        ),
                        smoke_version=SIDEWALL_REFERENCE_SURROGATE_SMOKE_VERSION,
                        case_id=case.case_id,
                        reference_model=str(reference_model),
                        channel_cross_section_model=case.channel_cross_section_model,
                        width_nm=case.width_nm,
                        depth_nm=case.depth_nm,
                        sidewall_taper_angle_deg_nodi=case.sidewall_taper_angle_deg_nodi,
                        sidewall_deg_comsol=case.sidewall_deg_comsol,
                        wavelength_nm=int(wavelength_nm),
                        n_events=int(summary.get("n_events", n_events)),
                        random_seed=int(random_seed),
                        detection_rate=_float_value(summary.get("detection_rate")),
                        stable_detection_rate=_float_value(
                            summary.get("stable_detection_rate")
                        ),
                        mean_peak_height=_float_value(summary.get("mean_peak_height")),
                        mean_local_snr=_float_value(summary.get("mean_local_snr")),
                        A_ref=_float_value(reference_summary.get("A_ref")),
                        g_ref=_float_value(reference_summary.get("g_ref")),
                        g_ref_geometry=_float_value(
                            reference_summary.get("g_ref_geometry")
                        ),
                        trapezoid_effective_aperture_factor=_float_value(
                            reference_context.get("trapezoid_effective_aperture_factor")
                        ),
                        trapezoid_effective_aperture_width_nm=(
                            _float_value(
                                reference_context.get(
                                    "trapezoid_effective_aperture_width_m"
                                )
                            )
                            * 1.0e9
                        ),
                        bottom_width_runtime_clipped_nm=(
                            _float_value(
                                reference_context.get(
                                    "trapezoid_effective_aperture_bottom_width_m"
                                )
                            )
                            * 1.0e9
                        ),
                        bottom_width_unclipped_nm=(
                            _float_value(
                                reference_context.get(
                                    "trapezoid_effective_aperture_bottom_width_unclipped_m"
                                )
                            )
                            * 1.0e9
                        ),
                        closure_status=str(
                            reference_context.get(
                                "trapezoid_effective_aperture_closure_status", ""
                            )
                        ),
                        na_cutoff_condition_met=bool(
                            reference_context.get("na_cutoff_condition_met", False)
                        ),
                        na_cutoff_active=bool(
                            reference_context.get("na_cutoff_active", False)
                        ),
                        reference_geometry_propagation_status=str(
                            summary.get("reference_geometry_propagation_status", "")
                        ),
                        reference_geometry_claim_level=str(
                            summary.get("reference_geometry_claim_level", "")
                        ),
                        reference_solver_status=str(
                            summary.get("reference_solver_status", "")
                        ),
                        reference_solver_claim_level=str(
                            summary.get("reference_solver_claim_level", "")
                        ),
                        geometry_not_propagated_to_reference_field=bool(
                            summary.get(
                                "geometry_not_propagated_to_reference_field", False
                            )
                        ),
                        reference_uses_rectangular_width_depth_surrogate=bool(
                            summary.get(
                                "reference_uses_rectangular_width_depth_surrogate",
                                False,
                            )
                        ),
                        not_optical_solver_output=bool(
                            summary.get("not_optical_solver_output", True)
                        ),
                        optical_solver_trigger_is_result=bool(
                            summary.get("optical_solver_trigger_is_result", False)
                        ),
                        optical_solver_current=False,
                        true_W_eff_current=False,
                        detection_probability_current=False,
                        yield_current=False,
                        route_score_current=False,
                        winner_current=False,
                        JRC_current=False,
                        claim_boundary=SIDEWALL_REFERENCE_SURROGATE_SMOKE_CLAIM_BOUNDARY,
                    )
                )
    return rows


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
