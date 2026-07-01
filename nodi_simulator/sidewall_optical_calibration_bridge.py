"""Sidewall optical calibration bridge artifacts.

The bridge turns sidewall reference-surrogate smoke rows into a calibration
seed table and a readiness matrix. The seed table deliberately uses the
synthetic calibration role so that `calibrated_lookup` cannot mistake it for
measured blank-channel calibration.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .calibration_models import SYNTHETIC_CALIBRATION_ROLE
from .sidewall_reference_surrogate_smoke import (
    SIDEWALL_REFERENCE_SURROGATE_SMOKE_CLAIM_BOUNDARY,
    SidewallReferenceSurrogateSmokeRow,
    run_sidewall_reference_surrogate_smoke,
)


SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_VERSION = (
    "sidewall_optical_calibration_bridge_from_reference_surrogate_smoke_v1"
)
SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY = (
    "synthetic_calibration_seed_not_blank_channel_calibration_not_detection_probability"
)


@dataclass(frozen=True)
class SidewallOpticalCalibrationSeedRow:
    calibration_row_id: str
    bridge_version: str
    case_id: str
    width_nm: int
    depth_nm: int
    wavelength_nm: int
    A_ref: float
    g_ref: float
    phi_ref_rad: float
    phi_ref_source: str
    phi_ref_confidence: str
    phase_wrap_policy: str
    channel_cross_section_model: str
    sidewall_deg_comsol: float
    sidewall_taper_angle_deg_nodi: float
    reference_model_source: str
    source_smoke_row_id: str
    calibration_data_role: str
    not_experimental_blank_channel_calibration: bool
    not_full_wave_optical_solver: bool
    not_true_W_eff: bool
    not_detector_response_validation: bool
    not_detection_probability: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallOpticalCalibrationReadinessRow:
    readiness_id: str
    bridge_version: str
    evidence_lane: str
    current_status: str
    current_artifact_basis: str
    required_before_promotion: str
    hard_fail_if_promoted_without: str
    target_claim: str
    target_claim_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_calibration_seed_manifest() -> dict[str, Any]:
    return {
        "calibration_kind": "reference_blank_channel",
        "calibration_data_role": SYNTHETIC_CALIBRATION_ROLE,
        "synthetic_fixture": True,
        "bridge_version": SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_VERSION,
        "source_claim_boundary": SIDEWALL_REFERENCE_SURROGATE_SMOKE_CLAIM_BOUNDARY,
        "claim_boundary": SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY,
        "units": {
            "width_nm": "nm",
            "depth_nm": "nm",
            "wavelength_nm": "nm",
            "A_ref": "dimensionless_surrogate_amplitude",
            "g_ref": "dimensionless_surrogate_geometry_factor",
            "phi_ref_rad": "rad",
        },
        "not_experimental_blank_channel_calibration": True,
        "not_full_wave_optical_solver": True,
        "not_true_W_eff": True,
        "not_detector_response_validation": True,
        "not_detection_probability": True,
    }


def build_sidewall_optical_calibration_seed_rows(
    smoke_rows: Iterable[SidewallReferenceSurrogateSmokeRow] | None = None,
) -> list[SidewallOpticalCalibrationSeedRow]:
    """Build synthetic calibration seed rows from sidewall-surrogate smoke."""
    rows = list(smoke_rows) if smoke_rows is not None else run_sidewall_reference_surrogate_smoke()
    seed_rows: list[SidewallOpticalCalibrationSeedRow] = []
    for row in rows:
        if row.reference_model != "trapezoid_effective_aperture_surrogate":
            continue
        seed_rows.append(
            SidewallOpticalCalibrationSeedRow(
                calibration_row_id=f"SWCAL-SEED-{row.case_id}_{row.wavelength_nm}",
                bridge_version=SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_VERSION,
                case_id=row.case_id,
                width_nm=row.width_nm,
                depth_nm=row.depth_nm,
                wavelength_nm=row.wavelength_nm,
                A_ref=row.A_ref,
                g_ref=row.g_ref,
                phi_ref_rad=0.0,
                phi_ref_source="surrogate_zero_phase_not_measured",
                phi_ref_confidence="not_measured",
                phase_wrap_policy="not_applicable_surrogate_seed",
                channel_cross_section_model=row.channel_cross_section_model,
                sidewall_deg_comsol=row.sidewall_deg_comsol,
                sidewall_taper_angle_deg_nodi=row.sidewall_taper_angle_deg_nodi,
                reference_model_source=row.reference_model,
                source_smoke_row_id=row.row_id,
                calibration_data_role=SYNTHETIC_CALIBRATION_ROLE,
                not_experimental_blank_channel_calibration=True,
                not_full_wave_optical_solver=True,
                not_true_W_eff=True,
                not_detector_response_validation=True,
                not_detection_probability=True,
                claim_boundary=SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY,
            )
        )
    return seed_rows


def build_sidewall_optical_calibration_readiness_rows() -> list[SidewallOpticalCalibrationReadinessRow]:
    rows = [
        (
            "SWCAL-READY-001",
            "blank_channel_reference_amplitude_phase",
            "synthetic_seed_available_not_experimental",
            "528 sidewall reference surrogate smoke",
            "measured blank-channel amplitude and phase table or EM solver output for W500/D900 theta grid",
            "true_reference_calibration_from_synthetic_seed",
            "calibrated_or_full_wave_sidewall_optical_solver",
        ),
        (
            "SWCAL-READY-002",
            "sidewall_geometry_coverage",
            "single_W500_D900_theta85_and_rectangle_seed_only",
            "528 smoke plus 527 reference surrogate",
            "coverage for required widths/depths/angles or explicit interpolation/extrapolation guard",
            "geometry_generalization_from_single_seed",
            "true_W_eff",
        ),
        (
            "SWCAL-READY-003",
            "detector_response_bridge",
            "not_detector_response_validation",
            "BFP/noise context only",
            "detector operator, ROI/slit throughput, and standard-particle calibration consuming sidewall reference field",
            "detector_response_claim_from_reference_amplitude_only",
            "detection_probability",
        ),
        (
            "SWCAL-READY-004",
            "blank_false_positive_trace",
            "blank_trace_validation_missing_for_sidewall_geometry",
            "Tsuyama-context blank evidence nearest geometry only",
            "sidewall-specific blank traces or validated transferable blank false-positive model",
            "false_positive_rate_from_synthetic_smoke",
            "detection_probability",
        ),
        (
            "SWCAL-READY-005",
            "wet_wall_interaction",
            "wet_sidewall_evidence_missing",
            "wet/EV context rows only",
            "sidewall material/surface/wet EV adhesion, clogging, recovery, and passability evidence",
            "yield_or_wet_pass_from_geometry_surrogate",
            "yield",
        ),
        (
            "SWCAL-READY-006",
            "integrated_route_ledger",
            "route_score_not_authorized_from_seed",
            "q_ch, flow, pressure, optical, and wet candidate packets",
            "ledger binding calibrated optical, flow split, wet evidence, and route-selection policy",
            "route_winner_from_single_branch_smoke",
            "route_score_or_winner",
        ),
    ]
    return [
        SidewallOpticalCalibrationReadinessRow(
            readiness_id=readiness_id,
            bridge_version=SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_VERSION,
            evidence_lane=evidence_lane,
            current_status=current_status,
            current_artifact_basis=current_artifact_basis,
            required_before_promotion=required_before_promotion,
            hard_fail_if_promoted_without=hard_fail_if,
            target_claim=target_claim,
            target_claim_current=False,
            claim_boundary=SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY,
        )
        for (
            readiness_id,
            evidence_lane,
            current_status,
            current_artifact_basis,
            required_before_promotion,
            hard_fail_if,
            target_claim,
        ) in rows
    ]
