"""Sidewall-aware reference surrogate candidate rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import math
from typing import Any

from ._exports import Channel, OpticalSystem, DEFAULT_SIM_CFG, compute_reference_field


SIDEWALL_REFERENCE_SURROGATE_VERSION = (
    "trapezoid_effective_aperture_reference_surrogate_candidate_v1"
)
SIDEWALL_REFERENCE_SURROGATE_CLAIM_BOUNDARY = (
    "sidewall_reference_surrogate_not_full_optical_solver_not_detection_probability"
)


@dataclass(frozen=True)
class SidewallReferenceSurrogateCase:
    case_id: str
    channel_cross_section_model: str
    sidewall_taper_angle_deg_nodi: float
    sidewall_deg_comsol: float
    width_nm: int = 500
    depth_nm: int = 900


@dataclass(frozen=True)
class SidewallReferenceSurrogateRow:
    row_id: str
    surrogate_version: str
    case_id: str
    reference_model: str
    channel_cross_section_model: str
    width_nm: int
    depth_nm: int
    sidewall_taper_angle_deg_nodi: float
    sidewall_deg_comsol: float
    wavelength_nm: int
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
    geometry_not_propagated_to_reference_field: bool
    reference_uses_rectangular_width_depth_surrogate: bool
    not_optical_solver_output: bool
    optical_solver_current: bool
    true_W_eff_current: bool
    detection_probability_current: bool
    route_score_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_sidewall_reference_cases() -> list[SidewallReferenceSurrogateCase]:
    return [
        SidewallReferenceSurrogateCase(
            case_id="rectangle_limit_theta90_D900_W500",
            channel_cross_section_model="ideal_rectangle",
            sidewall_taper_angle_deg_nodi=0.0,
            sidewall_deg_comsol=90.0,
        ),
        SidewallReferenceSurrogateCase(
            case_id="taper_theta85_D900_W500",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_taper_angle_deg_nodi=5.0,
            sidewall_deg_comsol=85.0,
        ),
    ]


def build_sidewall_reference_surrogate_rows(
    *,
    cases: list[SidewallReferenceSurrogateCase] | None = None,
    wavelengths_nm: tuple[int, ...] = (404, 660),
) -> list[SidewallReferenceSurrogateRow]:
    """Compute sidewall-aware effective-aperture reference surrogate rows."""
    case_list = default_sidewall_reference_cases() if cases is None else list(cases)
    rows: list[SidewallReferenceSurrogateRow] = []
    for case in case_list:
        channel = Channel(
            width_m=float(case.width_nm) * 1.0e-9,
            depth_m=float(case.depth_nm) * 1.0e-9,
        )
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
                reference_model="trapezoid_effective_aperture_surrogate",
                reference_spatial_mode="cross_section_surrogate",
                channel_cross_section_model=case.channel_cross_section_model,
                sidewall_taper_angle_deg=case.sidewall_taper_angle_deg_nodi,
                include_diffusion=False,
                flow_profile_model="plug",
                diffusion_hindrance_model="none",
            )
            reference = compute_reference_field(channel, optical, sim_cfg)
            rows.append(
                SidewallReferenceSurrogateRow(
                    row_id=f"REFSUR-{case.case_id}_{wavelength_nm}",
                    surrogate_version=SIDEWALL_REFERENCE_SURROGATE_VERSION,
                    case_id=case.case_id,
                    reference_model="trapezoid_effective_aperture_surrogate",
                    channel_cross_section_model=case.channel_cross_section_model,
                    width_nm=case.width_nm,
                    depth_nm=case.depth_nm,
                    sidewall_taper_angle_deg_nodi=case.sidewall_taper_angle_deg_nodi,
                    sidewall_deg_comsol=case.sidewall_deg_comsol,
                    wavelength_nm=int(wavelength_nm),
                    A_ref=_float_value(reference.get("A_ref")),
                    g_ref=_float_value(reference.get("g_ref")),
                    g_ref_geometry=_float_value(reference.get("g_ref_geometry")),
                    trapezoid_effective_aperture_factor=_float_value(
                        reference.get("trapezoid_effective_aperture_factor")
                    ),
                    trapezoid_effective_aperture_width_nm=(
                        _float_value(
                            reference.get("trapezoid_effective_aperture_width_m")
                        )
                        * 1.0e9
                    ),
                    bottom_width_runtime_clipped_nm=(
                        _float_value(
                            reference.get(
                                "trapezoid_effective_aperture_bottom_width_m"
                            )
                        )
                        * 1.0e9
                    ),
                    bottom_width_unclipped_nm=(
                        _float_value(
                            reference.get(
                                "trapezoid_effective_aperture_bottom_width_unclipped_m"
                            )
                        )
                        * 1.0e9
                    ),
                    closure_status=str(
                        reference.get("trapezoid_effective_aperture_closure_status", "")
                    ),
                    na_cutoff_condition_met=bool(
                        reference.get("na_cutoff_condition_met", False)
                    ),
                    na_cutoff_active=bool(reference.get("na_cutoff_active", False)),
                    reference_geometry_propagation_status=str(
                        reference.get("reference_geometry_propagation_status", "")
                    ),
                    reference_geometry_claim_level=str(
                        reference.get("reference_geometry_claim_level", "")
                    ),
                    geometry_not_propagated_to_reference_field=bool(
                        reference.get("geometry_not_propagated_to_reference_field", False)
                    ),
                    reference_uses_rectangular_width_depth_surrogate=bool(
                        reference.get(
                            "reference_uses_rectangular_width_depth_surrogate", False
                        )
                    ),
                    not_optical_solver_output=bool(
                        reference.get("not_optical_solver_output", True)
                    ),
                    optical_solver_current=False,
                    true_W_eff_current=False,
                    detection_probability_current=False,
                    route_score_current=False,
                    claim_boundary=SIDEWALL_REFERENCE_SURROGATE_CLAIM_BOUNDARY,
                )
            )
    return rows


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
