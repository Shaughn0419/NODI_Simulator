"""Preflight contract for sidewall-aware electrokinetic grids."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_VERSION = (
    "sidewall_electrokinetic_grid_preflight_v1"
)
SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_CLAIM_BOUNDARY = (
    "electrokinetic_grid_preflight_preserve_rectangle_not_solver_not_detection"
)
ELECTROKINETIC_GRID_PREFLIGHT_READY_STATUS = (
    "electrokinetic_grid_preflight_ready_profile_aware_grid_required"
)


@dataclass(frozen=True)
class SidewallElectrokineticGridPreflightRow:
    preflight_row_id: str
    preflight_version: str
    case_id: str
    source_solver_branch_row_id: str
    user_authorization_status: str
    channel_cross_section_model: str
    rectangle_baseline_preserved: bool
    sidewall_deg_comsol: float
    width_nm: float
    depth_nm: float
    electrokinetic_grid_geometry_model: str
    electrokinetic_wall_distance_model: str
    electrostatic_potential_model_required: str
    zeta_wall_model_required: bool
    zeta_particle_model_required: bool
    ionic_strength_required: bool
    debye_length_required: bool
    center_accessible_support_required: bool
    blocked_bins_excluded_required: bool
    rectangle_limit_test_required: bool
    theta_mutation_test_required: bool
    zeta_sign_mutation_test_required: bool
    ionic_strength_mutation_test_required: bool
    current_status: str
    current_claim_level: str
    legacy_rectangle_path_allowed: bool
    profile_aware_grid_current: bool
    electrokinetic_solver_output_current: bool
    electrokinetic_weight_current: bool
    route_score_current: bool
    detection_probability_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallElectrokineticClaimGuardRow:
    guard_row_id: str
    preflight_version: str
    promotion_target: str
    implementation_authorized: bool
    claim_promoted_current: bool
    claim_promotion_allowed_now: bool
    required_evidence_before_true: str
    hard_fail_if_missing_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_electrokinetic_grid_preflight(
    *,
    solver_branch_rows: list[Mapping[str, Any]],
) -> tuple[
    list[SidewallElectrokineticGridPreflightRow],
    list[SidewallElectrokineticClaimGuardRow],
]:
    source = _electrokinetic_solver_branch_row(solver_branch_rows)
    rows = [
        _preflight_row(
            source=source,
            case_id="rectangle_baseline_boltzmann_grid_diagnostic",
            channel_cross_section_model="ideal_rectangle",
            rectangle_baseline_preserved=True,
            sidewall_deg_comsol=90.0,
            grid_model="rectangular_grid_surrogate_v1",
            wall_distance_model="rectangular_nearest_wall_distance_grid_v1",
            current_status="rectangle_legacy_diagnostic_allowed_not_trapezoid_claim",
            current_claim_level="rectangle_native_or_baseline_diagnostic_not_sidewall_solver",
            legacy_rectangle_path_allowed=True,
            profile_aware_grid_current=False,
            next_required_evidence=(
                "rectangle-limit comparison when trapezoid grid is implemented"
            ),
            hard_fail_if="rectangle_baseline_cache_reused_for_trapezoid_request",
        ),
        _preflight_row(
            source=source,
            case_id="trapezoid_theta85_profile_aware_grid_required",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            rectangle_baseline_preserved=True,
            sidewall_deg_comsol=85.0,
            grid_model="trapezoid_cut_cell_or_fem_grid_v1_required",
            wall_distance_model="trapezoid_signed_wall_distance_v1_required",
            current_status="blocked_until_profile_aware_grid_implemented",
            current_claim_level="preflight_only_no_trapezoid_electrokinetic_solver_output",
            legacy_rectangle_path_allowed=False,
            profile_aware_grid_current=False,
            next_required_evidence=(
                "cut-cell/FEM mesh, center-accessible support, blocked-bin exclusion, "
                "rectangle-limit test, and theta mutation test"
            ),
            hard_fail_if="trapezoid_uses_rectangular_wall_distance_grid",
        ),
        _preflight_row(
            source=source,
            case_id="trapezoid_metadata_required_zeta_ionic_strength",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            rectangle_baseline_preserved=True,
            sidewall_deg_comsol=85.0,
            grid_model="trapezoid_cut_cell_or_fem_grid_v1_required",
            wall_distance_model="trapezoid_signed_wall_distance_v1_required",
            current_status="blocked_until_zeta_ionic_strength_and_debye_metadata_bound",
            current_claim_level="metadata_preflight_only_no_electrokinetic_weight",
            legacy_rectangle_path_allowed=False,
            profile_aware_grid_current=False,
            next_required_evidence=(
                "zeta_wall_model, zeta_particle_model, ionic_strength_M, Debye length, "
                "and mutation responses"
            ),
            hard_fail_if="electrokinetic_weight_true_without_zeta_or_ionic_strength",
        ),
        _preflight_row(
            source=source,
            case_id="trapezoid_blocked_bins_and_closed_geometry_guard",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            rectangle_baseline_preserved=True,
            sidewall_deg_comsol=70.0,
            grid_model="trapezoid_cut_cell_or_fem_grid_v1_required",
            wall_distance_model="trapezoid_signed_wall_distance_v1_required",
            current_status="blocked_until_closed_geometry_and_blocked_bins_excluded",
            current_claim_level="blocked_geometry_guard_no_solver_output",
            legacy_rectangle_path_allowed=False,
            profile_aware_grid_current=False,
            next_required_evidence=(
                "closed/near-closed geometry guard, blocked-bin exclusion, and no "
                "neighbor-fill policy"
            ),
            hard_fail_if="blocked_bin_or_closed_geometry_emits_numeric_electrokinetic_weight",
        ),
    ]
    return rows, _claim_guard_rows()


def _electrokinetic_solver_branch_row(
    rows: list[Mapping[str, Any]],
) -> Mapping[str, Any]:
    for row in rows:
        if str(row.get("branch_id", "")) == "electrokinetic_solver":
            return row
    return {}


def _preflight_row(
    *,
    source: Mapping[str, Any],
    case_id: str,
    channel_cross_section_model: str,
    rectangle_baseline_preserved: bool,
    sidewall_deg_comsol: float,
    grid_model: str,
    wall_distance_model: str,
    current_status: str,
    current_claim_level: str,
    legacy_rectangle_path_allowed: bool,
    profile_aware_grid_current: bool,
    next_required_evidence: str,
    hard_fail_if: str,
) -> SidewallElectrokineticGridPreflightRow:
    return SidewallElectrokineticGridPreflightRow(
        preflight_row_id=f"EK-GRID-PREFLIGHT-{case_id}",
        preflight_version=SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_VERSION,
        case_id=case_id,
        source_solver_branch_row_id=str(source.get("branch_row_id", "")),
        user_authorization_status=str(source.get("user_authorization_status", "")),
        channel_cross_section_model=channel_cross_section_model,
        rectangle_baseline_preserved=rectangle_baseline_preserved,
        sidewall_deg_comsol=sidewall_deg_comsol,
        width_nm=500.0,
        depth_nm=900.0,
        electrokinetic_grid_geometry_model=grid_model,
        electrokinetic_wall_distance_model=wall_distance_model,
        electrostatic_potential_model_required=(
            "linearized_poisson_boltzmann_or_poisson_boltzmann_solver_required"
        ),
        zeta_wall_model_required=True,
        zeta_particle_model_required=True,
        ionic_strength_required=True,
        debye_length_required=True,
        center_accessible_support_required=True,
        blocked_bins_excluded_required=True,
        rectangle_limit_test_required=True,
        theta_mutation_test_required=True,
        zeta_sign_mutation_test_required=True,
        ionic_strength_mutation_test_required=True,
        current_status=current_status,
        current_claim_level=current_claim_level,
        legacy_rectangle_path_allowed=legacy_rectangle_path_allowed,
        profile_aware_grid_current=profile_aware_grid_current,
        electrokinetic_solver_output_current=False,
        electrokinetic_weight_current=False,
        route_score_current=False,
        detection_probability_current=False,
        next_required_evidence=next_required_evidence,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_CLAIM_BOUNDARY,
    )


def _claim_guard_rows() -> list[SidewallElectrokineticClaimGuardRow]:
    specs = [
        (
            "trapezoid_electrokinetic_solver_output",
            "profile-aware grid, wall-distance model, PB/electrokinetic solver, and tests",
            "electrokinetic_solver_output_true_without_profile_aware_grid",
        ),
        (
            "trapezoid_boltzmann_wall_weighting",
            "trapezoid signed wall distances, blocked-bin exclusion, and metadata",
            "boltzmann_weighting_true_from_rectangular_grid_under_trapezoid",
        ),
        (
            "zeta_sign_response",
            "declared zeta wall/particle model and sign-mutation evidence",
            "zeta_response_true_without_zeta_sign_mutation_test",
        ),
        (
            "ionic_strength_debye_response",
            "ionic strength, Debye length, and ionic-strength mutation evidence",
            "debye_response_true_without_ionic_strength_metadata",
        ),
        (
            "route_score_or_detection_probability",
            "electrokinetic packet plus optical/detection and route policy packets",
            "route_or_detection_true_from_electrokinetic_preflight_only",
        ),
        (
            "production_or_fabrication_release",
            "separate production/fabrication release ledger",
            "production_release_true_from_electrokinetic_preflight",
        ),
    ]
    return [
        SidewallElectrokineticClaimGuardRow(
            guard_row_id=f"EK-GRID-GUARD-{target}",
            preflight_version=SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            claim_promoted_current=False,
            claim_promotion_allowed_now=False,
            required_evidence_before_true=required,
            hard_fail_if_missing_evidence=hard_fail,
            claim_boundary=SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_CLAIM_BOUNDARY,
        )
        for target, required, hard_fail in specs
    ]
