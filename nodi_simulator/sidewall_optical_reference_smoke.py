"""Sidewall optical/reference smoke evidence for W500/D900 route candidates.

The smoke executes a small NODI batch for rectangle-limit and tapered-sidewall
cases. It records reference-field geometry propagation diagnostics and synthetic
detection context, while keeping final optical/detection/yield/route claims
false.
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


SIDEWALL_OPTICAL_REFERENCE_SMOKE_VERSION = (
    "sidewall_optical_reference_smoke_w500_d900_v1"
)
SIDEWALL_OPTICAL_REFERENCE_SMOKE_CLAIM_BOUNDARY = (
    "synthetic_reference_detection_context_not_optical_solver_not_detection_probability"
)


@dataclass(frozen=True)
class SidewallOpticalReferenceSmokeCase:
    case_id: str
    channel_cross_section_model: str
    sidewall_taper_angle_deg_nodi: float
    sidewall_deg_comsol: float
    width_nm: int = 500
    depth_nm: int = 900


@dataclass(frozen=True)
class SidewallOpticalReferenceSmokeRow:
    case_id: str
    smoke_version: str
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
    reference_geometry_propagation_status: str
    reference_geometry_claim_level: str
    geometry_not_propagated_to_reference_field: bool
    reference_uses_rectangular_width_depth_surrogate: bool
    not_optical_solver_output: bool
    optical_solver_trigger_is_result: bool
    optical_solver_current: bool
    detection_probability_current: bool
    yield_current: bool
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_smoke_cases() -> list[SidewallOpticalReferenceSmokeCase]:
    return [
        SidewallOpticalReferenceSmokeCase(
            case_id="rectangle_limit_theta90_D900_W500",
            channel_cross_section_model="ideal_rectangle",
            sidewall_taper_angle_deg_nodi=0.0,
            sidewall_deg_comsol=90.0,
        ),
        SidewallOpticalReferenceSmokeCase(
            case_id="taper_theta85_D900_W500",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_taper_angle_deg_nodi=5.0,
            sidewall_deg_comsol=85.0,
        ),
    ]


def run_sidewall_optical_reference_smoke(
    *,
    cases: list[SidewallOpticalReferenceSmokeCase] | None = None,
    n_events: int = 8,
    random_seed: int = 526,
    wavelength_nm: int = 660,
) -> list[SidewallOpticalReferenceSmokeRow]:
    """Run small NODI batches for sidewall optical/reference diagnostics."""
    case_list = default_smoke_cases() if cases is None else list(cases)
    optical = OpticalSystem(
        wavelength_m=float(wavelength_nm) * 1.0e-9,
        peak_irradiance_W_m2=1.0,
        beam_waist_x_m=300e-9,
        beam_waist_y_m=700e-9,
        beam_waist_z_m=300e-9,
    )
    theta_grid = np.linspace(1.0e-3, math.pi - 1.0e-3, 181)
    rows: list[SidewallOpticalReferenceSmokeRow] = []
    for case in case_list:
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
            reference_model="channel_angular_surrogate",
            reference_spatial_mode="cross_section_surrogate",
            channel_cross_section_model=case.channel_cross_section_model,
            sidewall_taper_angle_deg=case.sidewall_taper_angle_deg_nodi,
            readout_preset="tsuyama_2022_counting_10sigma",
            vectorized_event_engine="off",
        )
        channel = Channel(
            width_m=float(case.width_nm) * 1.0e-9,
            depth_m=float(case.depth_nm) * 1.0e-9,
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
        rows.append(
            SidewallOpticalReferenceSmokeRow(
                case_id=case.case_id,
                smoke_version=SIDEWALL_OPTICAL_REFERENCE_SMOKE_VERSION,
                channel_cross_section_model=case.channel_cross_section_model,
                width_nm=case.width_nm,
                depth_nm=case.depth_nm,
                sidewall_taper_angle_deg_nodi=case.sidewall_taper_angle_deg_nodi,
                sidewall_deg_comsol=case.sidewall_deg_comsol,
                wavelength_nm=int(wavelength_nm),
                n_events=int(summary.get("n_events", n_events)),
                random_seed=int(random_seed),
                detection_rate=_float_value(summary.get("detection_rate")),
                stable_detection_rate=_float_value(summary.get("stable_detection_rate")),
                mean_peak_height=_float_value(summary.get("mean_peak_height")),
                mean_local_snr=_float_value(summary.get("mean_local_snr")),
                reference_geometry_propagation_status=str(
                    summary.get("reference_geometry_propagation_status", "")
                ),
                reference_geometry_claim_level=str(
                    summary.get("reference_geometry_claim_level", "")
                ),
                geometry_not_propagated_to_reference_field=bool(
                    summary.get("geometry_not_propagated_to_reference_field", False)
                ),
                reference_uses_rectangular_width_depth_surrogate=bool(
                    summary.get("reference_uses_rectangular_width_depth_surrogate", False)
                ),
                not_optical_solver_output=bool(
                    summary.get("not_optical_solver_output", True)
                ),
                optical_solver_trigger_is_result=bool(
                    summary.get("optical_solver_trigger_is_result", False)
                ),
                optical_solver_current=False,
                detection_probability_current=False,
                yield_current=False,
                route_score_current=False,
                winner_current=False,
                JRC_current=False,
                claim_boundary=SIDEWALL_OPTICAL_REFERENCE_SMOKE_CLAIM_BOUNDARY,
            )
        )
    return rows


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
