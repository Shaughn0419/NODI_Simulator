"""Sidewall selected-annulus NODI context rows.

The rows execute a small NODI W500/D900 smoke run and extract the selected
annulus diagnostics already emitted by the simulator. They are context for a
promotion blocker, not detection probability or route ranking.
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
    run_single_case_batch,
)


SIDEWALL_SELECTED_ANNULUS_CONTEXT_VERSION = (
    "sidewall_selected_annulus_context_w500_d900_v1"
)
SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY = (
    "selected_annulus_context_not_detection_probability_not_route_score"
)


@dataclass(frozen=True)
class SidewallSelectedAnnulusCase:
    case_id: str
    channel_cross_section_model: str
    sidewall_taper_angle_deg_nodi: float
    sidewall_deg_comsol: float
    width_nm: int = 500
    depth_nm: int = 900


@dataclass(frozen=True)
class SidewallSelectedAnnulusContextRow:
    row_id: str
    context_version: str
    case_id: str
    channel_cross_section_model: str
    sidewall_taper_angle_deg_nodi: float
    sidewall_deg_comsol: float
    width_nm: int
    depth_nm: int
    wavelength_nm: int
    reference_model: str
    n_events: int
    random_seed: int
    selected_annulus_source: str
    selected_annulus_edge_norm_min: float
    selected_annulus_edge_norm_max: float
    selected_annulus_n_events: int
    selected_annulus_n_detected: int
    selected_annulus_fraction: float
    selected_annulus_detection_context_rate: float
    selected_annulus_detection_rate_wilson_lb_context: float
    selected_annulus_mean_edge_norm: float
    all_crossing_detection_context_rate: float
    selected_detector_mode_candidate_detection_context_rate: float
    selected_annulus_context_status: str
    selected_annulus_context_current: bool
    small_n_synthetic_context: bool
    detection_probability_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_selected_annulus_cases() -> list[SidewallSelectedAnnulusCase]:
    return [
        SidewallSelectedAnnulusCase(
            case_id="rectangle_limit_theta90_D900_W500",
            channel_cross_section_model="ideal_rectangle",
            sidewall_taper_angle_deg_nodi=0.0,
            sidewall_deg_comsol=90.0,
        ),
        SidewallSelectedAnnulusCase(
            case_id="taper_theta85_D900_W500",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_taper_angle_deg_nodi=5.0,
            sidewall_deg_comsol=85.0,
        ),
    ]


def run_sidewall_selected_annulus_context(
    *,
    cases: list[SidewallSelectedAnnulusCase] | None = None,
    n_events: int = 16,
    random_seed: int = 531,
    wavelength_nm: int = 404,
) -> list[SidewallSelectedAnnulusContextRow]:
    """Run small sidewall NODI batches and extract selected-annulus context."""
    case_list = default_selected_annulus_cases() if cases is None else list(cases)
    theta_grid = np.linspace(1.0e-3, math.pi - 1.0e-3, 181)
    rows: list[SidewallSelectedAnnulusContextRow] = []
    for case in case_list:
        channel = Channel(
            width_m=float(case.width_nm) * 1.0e-9,
            depth_m=float(case.depth_nm) * 1.0e-9,
        )
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
            reference_model="trapezoid_effective_aperture_surrogate",
            reference_spatial_mode="cross_section_surrogate",
            channel_cross_section_model=case.channel_cross_section_model,
            sidewall_taper_angle_deg=case.sidewall_taper_angle_deg_nodi,
            readout_preset="tsuyama_2022_counting_10sigma",
            vectorized_event_engine="off",
        )
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
        annulus_n = int(summary.get("selected_detector_mode_annulus_n_events", 0) or 0)
        rows.append(
            SidewallSelectedAnnulusContextRow(
                row_id=f"SELANN-{case.case_id}_{wavelength_nm}",
                context_version=SIDEWALL_SELECTED_ANNULUS_CONTEXT_VERSION,
                case_id=case.case_id,
                channel_cross_section_model=case.channel_cross_section_model,
                sidewall_taper_angle_deg_nodi=case.sidewall_taper_angle_deg_nodi,
                sidewall_deg_comsol=case.sidewall_deg_comsol,
                width_nm=case.width_nm,
                depth_nm=case.depth_nm,
                wavelength_nm=int(wavelength_nm),
                reference_model="trapezoid_effective_aperture_surrogate",
                n_events=int(summary.get("n_events", n_events)),
                random_seed=int(random_seed),
                selected_annulus_source=str(
                    summary.get("selected_detector_mode_annulus_source", "")
                ),
                selected_annulus_edge_norm_min=_float_value(
                    summary.get("selected_detector_mode_annulus_edge_norm_min")
                ),
                selected_annulus_edge_norm_max=_float_value(
                    summary.get("selected_detector_mode_annulus_edge_norm_max")
                ),
                selected_annulus_n_events=annulus_n,
                selected_annulus_n_detected=int(
                    summary.get("selected_detector_mode_annulus_n_detected", 0) or 0
                ),
                selected_annulus_fraction=_float_value(
                    summary.get("selected_detector_mode_annulus_fraction")
                ),
                selected_annulus_detection_context_rate=_float_value(
                    summary.get("selected_detector_mode_annulus_detection_rate")
                ),
                selected_annulus_detection_rate_wilson_lb_context=_float_value(
                    summary.get(
                        "selected_detector_mode_annulus_detection_rate_wilson_lb"
                    )
                ),
                selected_annulus_mean_edge_norm=_float_value(
                    summary.get("selected_detector_mode_annulus_mean_edge_norm")
                ),
                all_crossing_detection_context_rate=_float_value(
                    summary.get("all_crossing_detection_rate")
                ),
                selected_detector_mode_candidate_detection_context_rate=_float_value(
                    summary.get("selected_detector_mode_candidate_detection_rate")
                ),
                selected_annulus_context_status=(
                    "selected_annulus_context_available_small_n_not_probability"
                    if annulus_n > 0
                    else "selected_annulus_context_empty_small_n_rerun_required"
                ),
                selected_annulus_context_current=annulus_n > 0,
                small_n_synthetic_context=True,
                detection_probability_current=False,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                claim_boundary=SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY,
            )
        )
    return rows


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
