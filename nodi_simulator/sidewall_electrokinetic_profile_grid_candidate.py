"""Profile-aware electrokinetic grid candidates for sidewall Package C."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

from .cross_section_geometry import (
    TRAPEZOID_WALL_DISTANCE_MODEL,
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
)


SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_VERSION = (
    "sidewall_electrokinetic_profile_grid_candidate_v1"
)
SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY = (
    "profile_aware_grid_candidate_not_electrokinetic_solver_not_route_detection"
)
SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_STATUS = (
    "profile_aware_grid_candidate_ready_grid_rows_not_solver_output"
)


@dataclass(frozen=True)
class ElectrokineticProfileGridCaseSpec:
    case_id: str
    channel_cross_section_model: str
    sidewall_deg_comsol: float
    top_width_nm: float
    depth_nm: float
    particle_radius_nm: float
    ionic_strength_M: float
    zeta_particle_mV: float
    zeta_wall_mV: float
    grid_size_x: int = 21
    grid_size_u: int = 21


@dataclass(frozen=True)
class ElectrokineticProfileGridCellRow:
    cell_row_id: str
    candidate_version: str
    case_id: str
    channel_cross_section_model: str
    sidewall_deg_comsol: float
    x_nm: float
    u_nm: float
    cell_area_nm2: float
    center_accessible: bool
    blocked_reason: str
    nearest_wall_id: str
    d_nearest_wall_nm: float | None
    surface_gap_nm: float | None
    electrostatic_weight_surrogate: float | None
    weight_claim_level: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ElectrokineticProfileGridCaseRow:
    case_id: str
    candidate_version: str
    channel_cross_section_model: str
    sidewall_deg_comsol: float
    sidewall_taper_angle_deg_nodi: float
    top_width_nm: float
    depth_nm: float
    particle_radius_nm: float
    ionic_strength_M: float
    debye_length_nm: float
    zeta_particle_mV: float
    zeta_wall_mV: float
    electrokinetic_grid_geometry_model: str
    electrokinetic_wall_distance_model: str
    center_accessible_support_model: str
    profile_aware_grid_current: bool
    electrokinetic_solver_output_current: bool
    electrokinetic_weight_current: bool
    route_score_current: bool
    detection_probability_current: bool
    grid_cell_rows: int
    accessible_cell_rows: int
    blocked_cell_rows: int
    blocked_cell_weight_rows: int
    center_accessible_area_nm2: float
    grid_accessible_area_fraction: float
    unweighted_mean_wall_distance_nm: float
    boltzmann_weighted_mean_wall_distance_nm: float
    near_wall_weight_surrogate_mean: float
    center_weight_surrogate_mean: float
    center_to_near_wall_weight_ratio: float | None
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ElectrokineticProfileGridMutationCheckRow:
    mutation_check_id: str
    candidate_version: str
    check_type: str
    baseline_case_id: str
    comparison_case_id: str
    baseline_metric: str
    comparison_metric: str
    baseline_value: float
    comparison_value: float
    absolute_delta: float
    pass_threshold: float
    mutation_check_passed: bool
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ElectrokineticProfileGridClaimGuardRow:
    guard_row_id: str
    candidate_version: str
    promotion_target: str
    implementation_authorized: bool
    candidate_grid_available: bool
    claim_promoted_current: bool
    claim_promotion_allowed_now: bool
    required_evidence_before_true: str
    hard_fail_if_missing_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_profile_grid_case_specs() -> list[ElectrokineticProfileGridCaseSpec]:
    return [
        ElectrokineticProfileGridCaseSpec(
            case_id="rectangle_theta90_baseline",
            channel_cross_section_model="ideal_rectangle",
            sidewall_deg_comsol=90.0,
            top_width_nm=500.0,
            depth_nm=900.0,
            particle_radius_nm=110.0,
            ionic_strength_M=1.0e-3,
            zeta_particle_mV=-25.0,
            zeta_wall_mV=-40.0,
        ),
        ElectrokineticProfileGridCaseSpec(
            case_id="trapezoid_theta85_base",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_deg_comsol=85.0,
            top_width_nm=500.0,
            depth_nm=900.0,
            particle_radius_nm=110.0,
            ionic_strength_M=1.0e-3,
            zeta_particle_mV=-25.0,
            zeta_wall_mV=-40.0,
        ),
        ElectrokineticProfileGridCaseSpec(
            case_id="trapezoid_theta80_theta_mutation",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_deg_comsol=80.0,
            top_width_nm=500.0,
            depth_nm=900.0,
            particle_radius_nm=110.0,
            ionic_strength_M=1.0e-3,
            zeta_particle_mV=-25.0,
            zeta_wall_mV=-40.0,
        ),
        ElectrokineticProfileGridCaseSpec(
            case_id="trapezoid_theta85_zeta_sign_flip",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_deg_comsol=85.0,
            top_width_nm=500.0,
            depth_nm=900.0,
            particle_radius_nm=110.0,
            ionic_strength_M=1.0e-3,
            zeta_particle_mV=-25.0,
            zeta_wall_mV=40.0,
        ),
        ElectrokineticProfileGridCaseSpec(
            case_id="trapezoid_theta85_high_ionic_strength",
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_deg_comsol=85.0,
            top_width_nm=500.0,
            depth_nm=900.0,
            particle_radius_nm=110.0,
            ionic_strength_M=1.0e-2,
            zeta_particle_mV=-25.0,
            zeta_wall_mV=-40.0,
        ),
    ]


def build_profile_grid_candidate(
    specs: list[ElectrokineticProfileGridCaseSpec] | None = None,
) -> tuple[
    list[ElectrokineticProfileGridCaseRow],
    list[ElectrokineticProfileGridCellRow],
    list[ElectrokineticProfileGridMutationCheckRow],
    list[ElectrokineticProfileGridClaimGuardRow],
]:
    case_specs = specs if specs is not None else default_profile_grid_case_specs()
    case_rows: list[ElectrokineticProfileGridCaseRow] = []
    cell_rows: list[ElectrokineticProfileGridCellRow] = []
    cells_by_case: dict[str, list[ElectrokineticProfileGridCellRow]] = {}
    for spec in case_specs:
        case_row, cells = _build_case(spec)
        case_rows.append(case_row)
        cell_rows.extend(cells)
        cells_by_case[spec.case_id] = cells
    mutation_rows = _mutation_rows(case_rows, cells_by_case)
    guard_rows = _claim_guard_rows(candidate_grid_available=bool(case_rows))
    return case_rows, cell_rows, mutation_rows, guard_rows


def _build_case(
    spec: ElectrokineticProfileGridCaseSpec,
) -> tuple[ElectrokineticProfileGridCaseRow, list[ElectrokineticProfileGridCellRow]]:
    taper_deg = comsol_sidewall_deg_to_nodi_taper_deg(spec.sidewall_deg_comsol)
    geometry = TrapezoidCrossSection(
        top_width_m=spec.top_width_nm * 1.0e-9,
        depth_m=spec.depth_nm * 1.0e-9,
        sidewall_taper_angle_deg=taper_deg,
    )
    debye_nm = _debye_length_nm(spec.ionic_strength_M)
    cell_width_nm = spec.top_width_nm / spec.grid_size_x
    cell_height_nm = spec.depth_nm / spec.grid_size_u
    cells: list[ElectrokineticProfileGridCellRow] = []
    total_weight = 0.0
    weighted_wall_distance_nm = 0.0
    unweighted_wall_distance_nm = 0.0
    accessible_count = 0
    blocked_weight_rows = 0
    center_weight_sum = 0.0
    center_count = 0
    near_weight_sum = 0.0
    near_count = 0
    center_threshold_nm = 0.4 * min(spec.top_width_nm, spec.depth_nm)
    near_gap_threshold_nm = max(
        2.0 * debye_nm,
        0.05 * min(spec.top_width_nm, spec.depth_nm),
    )

    for u_index in range(spec.grid_size_u):
        u_nm = (u_index + 0.5) * spec.depth_nm / spec.grid_size_u
        for x_index in range(spec.grid_size_x):
            x_nm = -0.5 * spec.top_width_nm + (x_index + 0.5) * cell_width_nm
            cell_id = f"{spec.case_id}-u{u_index:02d}-x{x_index:02d}"
            contains = geometry.contains_particle_center(
                x_nm * 1.0e-9,
                u_nm * 1.0e-9,
                spec.particle_radius_nm * 1.0e-9,
            )
            if contains:
                diagnostics = geometry.particle_wall_gap_diagnostics_m(
                    x_nm * 1.0e-9,
                    u_nm * 1.0e-9,
                    spec.particle_radius_nm * 1.0e-9,
                )
                nearest_wall_id = str(diagnostics["nearest_wall_id"])
                d_nearest_nm = float(diagnostics["d_nearest_wall_m"]) * 1.0e9
                surface_gap_nm = float(diagnostics["surface_gap_for_particle_m"]) * 1.0e9
                weight = _electrostatic_weight_surrogate(
                    geometry=geometry,
                    x_nm=x_nm,
                    u_nm=u_nm,
                    particle_radius_nm=spec.particle_radius_nm,
                    debye_nm=debye_nm,
                    zeta_particle_mV=spec.zeta_particle_mV,
                    zeta_wall_mV=spec.zeta_wall_mV,
                )
                accessible_count += 1
                total_weight += weight
                weighted_wall_distance_nm += weight * d_nearest_nm
                unweighted_wall_distance_nm += d_nearest_nm
                if d_nearest_nm >= center_threshold_nm:
                    center_weight_sum += weight
                    center_count += 1
                if surface_gap_nm <= near_gap_threshold_nm:
                    near_weight_sum += weight
                    near_count += 1
                blocked_reason = ""
            else:
                nearest_wall_id = ""
                d_nearest_nm = None
                surface_gap_nm = None
                weight = None
                blocked_reason = "outside_particle_center_support"
            if weight is not None and not contains:
                blocked_weight_rows += 1
            cells.append(
                ElectrokineticProfileGridCellRow(
                    cell_row_id=cell_id,
                    candidate_version=SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_VERSION,
                    case_id=spec.case_id,
                    channel_cross_section_model=spec.channel_cross_section_model,
                    sidewall_deg_comsol=spec.sidewall_deg_comsol,
                    x_nm=x_nm,
                    u_nm=u_nm,
                    cell_area_nm2=cell_width_nm * cell_height_nm,
                    center_accessible=contains,
                    blocked_reason=blocked_reason,
                    nearest_wall_id=nearest_wall_id,
                    d_nearest_wall_nm=d_nearest_nm,
                    surface_gap_nm=surface_gap_nm,
                    electrostatic_weight_surrogate=weight,
                    weight_claim_level=(
                        "boltzmann_wall_weight_surrogate_not_solver_output"
                        if contains
                        else "blocked_cell_no_weight"
                    ),
                    claim_boundary=SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY,
                )
            )

    center_weight = center_weight_sum / center_count if center_count > 0 else 0.0
    near_weight = near_weight_sum / near_count if near_count > 0 else 0.0
    case_row = ElectrokineticProfileGridCaseRow(
        case_id=spec.case_id,
        candidate_version=SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_VERSION,
        channel_cross_section_model=spec.channel_cross_section_model,
        sidewall_deg_comsol=spec.sidewall_deg_comsol,
        sidewall_taper_angle_deg_nodi=taper_deg,
        top_width_nm=spec.top_width_nm,
        depth_nm=spec.depth_nm,
        particle_radius_nm=spec.particle_radius_nm,
        ionic_strength_M=spec.ionic_strength_M,
        debye_length_nm=debye_nm,
        zeta_particle_mV=spec.zeta_particle_mV,
        zeta_wall_mV=spec.zeta_wall_mV,
        electrokinetic_grid_geometry_model="trapezoid_cut_cell_signed_distance_grid_candidate_v1",
        electrokinetic_wall_distance_model=TRAPEZOID_WALL_DISTANCE_MODEL,
        center_accessible_support_model="wall_normal_half_plane_offset_v1",
        profile_aware_grid_current=True,
        electrokinetic_solver_output_current=False,
        electrokinetic_weight_current=False,
        route_score_current=False,
        detection_probability_current=False,
        grid_cell_rows=len(cells),
        accessible_cell_rows=accessible_count,
        blocked_cell_rows=len(cells) - accessible_count,
        blocked_cell_weight_rows=blocked_weight_rows,
        center_accessible_area_nm2=geometry.center_accessible_area_m2(
            spec.particle_radius_nm * 1.0e-9
        )
        * 1.0e18,
        grid_accessible_area_fraction=accessible_count / len(cells) if cells else 0.0,
        unweighted_mean_wall_distance_nm=(
            unweighted_wall_distance_nm / accessible_count if accessible_count else 0.0
        ),
        boltzmann_weighted_mean_wall_distance_nm=(
            weighted_wall_distance_nm / total_weight if total_weight > 0.0 else 0.0
        ),
        near_wall_weight_surrogate_mean=near_weight,
        center_weight_surrogate_mean=center_weight,
        center_to_near_wall_weight_ratio=_ratio(center_weight, near_weight),
        claim_boundary=SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY,
    )
    return case_row, cells


def _mutation_rows(
    case_rows: list[ElectrokineticProfileGridCaseRow],
    cells_by_case: dict[str, list[ElectrokineticProfileGridCellRow]],
) -> list[ElectrokineticProfileGridMutationCheckRow]:
    by_id = {row.case_id: row for row in case_rows}
    rectangle = by_id["rectangle_theta90_baseline"]
    base = by_id["trapezoid_theta85_base"]
    theta = by_id["trapezoid_theta80_theta_mutation"]
    zeta = by_id["trapezoid_theta85_zeta_sign_flip"]
    ionic = by_id["trapezoid_theta85_high_ionic_strength"]
    expected_rectangle_area = (
        (rectangle.top_width_nm - 2.0 * rectangle.particle_radius_nm)
        * (rectangle.depth_nm - 2.0 * rectangle.particle_radius_nm)
    )
    blocked_weight_rows = float(
        sum(row.blocked_cell_weight_rows for row in case_rows)
    )
    return [
        _mutation_row(
            mutation_check_id="EK-GRID-MUTATION-rectangle-limit-area",
            check_type="rectangle_limit",
            baseline_case_id=rectangle.case_id,
            comparison_case_id="analytic_rectangle_center_accessible_area",
            baseline_metric="center_accessible_area_nm2",
            comparison_metric="analytic_rectangle_area_nm2",
            baseline_value=rectangle.center_accessible_area_nm2,
            comparison_value=expected_rectangle_area,
            pass_threshold=1.0e-6,
            hard_fail_if="theta90_profile_grid_area_does_not_match_rectangle_limit",
        ),
        _mutation_row(
            mutation_check_id="EK-GRID-MUTATION-theta-response",
            check_type="theta_mutation",
            baseline_case_id=base.case_id,
            comparison_case_id=theta.case_id,
            baseline_metric="accessible_cell_rows",
            comparison_metric="accessible_cell_rows",
            baseline_value=float(base.accessible_cell_rows),
            comparison_value=float(theta.accessible_cell_rows),
            pass_threshold=1.0,
            hard_fail_if="theta_mutation_does_not_change_profile_grid_accessibility",
        ),
        _mutation_row(
            mutation_check_id="EK-GRID-MUTATION-zeta-sign-response",
            check_type="zeta_sign_mutation",
            baseline_case_id=base.case_id,
            comparison_case_id=zeta.case_id,
            baseline_metric="center_to_near_wall_weight_ratio",
            comparison_metric="center_to_near_wall_weight_ratio",
            baseline_value=float(base.center_to_near_wall_weight_ratio or 0.0),
            comparison_value=float(zeta.center_to_near_wall_weight_ratio or 0.0),
            pass_threshold=1.0e-3,
            hard_fail_if="zeta_sign_mutation_does_not_change_weight_surrogate",
        ),
        _mutation_row(
            mutation_check_id="EK-GRID-MUTATION-ionic-strength-response",
            check_type="ionic_strength_mutation",
            baseline_case_id=base.case_id,
            comparison_case_id=ionic.case_id,
            baseline_metric="debye_length_nm",
            comparison_metric="debye_length_nm",
            baseline_value=base.debye_length_nm,
            comparison_value=ionic.debye_length_nm,
            pass_threshold=1.0e-3,
            hard_fail_if="ionic_strength_mutation_does_not_change_debye_length",
        ),
        _mutation_row(
            mutation_check_id="EK-GRID-MUTATION-blocked-bins-excluded",
            check_type="blocked_bin_exclusion",
            baseline_case_id="all_cases",
            comparison_case_id="all_cases",
            baseline_metric="blocked_cell_weight_rows",
            comparison_metric="expected_blocked_cell_weight_rows",
            baseline_value=blocked_weight_rows,
            comparison_value=0.0,
            pass_threshold=0.0,
            hard_fail_if="blocked_cell_emits_electrostatic_weight_surrogate",
        ),
    ]


def _mutation_row(
    *,
    mutation_check_id: str,
    check_type: str,
    baseline_case_id: str,
    comparison_case_id: str,
    baseline_metric: str,
    comparison_metric: str,
    baseline_value: float,
    comparison_value: float,
    pass_threshold: float,
    hard_fail_if: str,
) -> ElectrokineticProfileGridMutationCheckRow:
    absolute_delta = abs(baseline_value - comparison_value)
    if check_type in {"rectangle_limit", "blocked_bin_exclusion"}:
        passed = absolute_delta <= pass_threshold
    else:
        passed = absolute_delta > pass_threshold
    return ElectrokineticProfileGridMutationCheckRow(
        mutation_check_id=mutation_check_id,
        candidate_version=SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_VERSION,
        check_type=check_type,
        baseline_case_id=baseline_case_id,
        comparison_case_id=comparison_case_id,
        baseline_metric=baseline_metric,
        comparison_metric=comparison_metric,
        baseline_value=baseline_value,
        comparison_value=comparison_value,
        absolute_delta=absolute_delta,
        pass_threshold=pass_threshold,
        mutation_check_passed=passed,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY,
    )


def _claim_guard_rows(
    *, candidate_grid_available: bool
) -> list[ElectrokineticProfileGridClaimGuardRow]:
    specs = [
        (
            "electrokinetic_solver_output",
            "Poisson-Boltzmann or electrokinetic solver validation over profile-aware grid",
            "solver_output_true_from_profile_grid_candidate_only",
        ),
        (
            "electrokinetic_weight",
            "profile grid plus calibrated model and downstream weighting policy",
            "electrokinetic_weight_true_without_calibrated_model",
        ),
        (
            "route_score_winner_JRC",
            "detector/blank, wet, q_ch, electrokinetic policy, and route formula packet",
            "route_score_true_from_electrokinetic_grid_candidate",
        ),
        (
            "yield_or_detection_probability",
            "accepted wet and detector evidence plus route formula binding",
            "yield_or_detection_true_from_electrokinetic_grid_candidate",
        ),
        (
            "production_ingestion",
            "integrated closeout and production release ledger",
            "production_ingestion_true_from_electrokinetic_grid_candidate",
        ),
    ]
    return [
        ElectrokineticProfileGridClaimGuardRow(
            guard_row_id=f"EK-GRID-CANDIDATE-GUARD-{target}",
            candidate_version=SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            candidate_grid_available=candidate_grid_available,
            claim_promoted_current=False,
            claim_promotion_allowed_now=False,
            required_evidence_before_true=required,
            hard_fail_if_missing_evidence=hard_fail,
            claim_boundary=SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY,
        )
        for target, required, hard_fail in specs
    ]


def _debye_length_nm(ionic_strength_M: float) -> float:
    if ionic_strength_M <= 0.0:
        raise ValueError(f"ionic_strength_M must be positive, got {ionic_strength_M}")
    return 0.304 / math.sqrt(float(ionic_strength_M))


def _electrostatic_weight_surrogate(
    *,
    geometry: TrapezoidCrossSection,
    x_nm: float,
    u_nm: float,
    particle_radius_nm: float,
    debye_nm: float,
    zeta_particle_mV: float,
    zeta_wall_mV: float,
) -> float:
    distances = geometry.wall_distances_m(x_nm * 1.0e-9, u_nm * 1.0e-9)
    zeta_product_scale = float(zeta_particle_mV) * float(zeta_wall_mV) / 625.0
    potential_kbt = 0.0
    for distance_m in distances.values():
        surface_gap_nm = max(distance_m * 1.0e9 - particle_radius_nm, 0.0)
        potential_kbt += zeta_product_scale * math.exp(-surface_gap_nm / debye_nm)
    return math.exp(-max(min(potential_kbt, 50.0), -50.0))


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0.0:
        return None
    return numerator / denominator
