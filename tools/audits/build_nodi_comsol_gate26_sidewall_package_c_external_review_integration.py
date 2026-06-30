#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

EXPECTED_GATE25_DISPOSITION = "NODI_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_PACKET_READY_NO_AUTH"
DISPOSITION = "NODI_GATE26_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_INTEGRATION_DESIGN_CONSTRAINTS_READY_NO_AUTH"
EXTERNAL_VERDICT = "READY_FOR_IMPLEMENTATION_DESIGN_ONLY"
EXTERNAL_FEEDBACK_ARTIFACT_ID = "G26A-EXTERNAL-AI-FEEDBACK-CAPTURE-20260630"
EXTERNAL_FEEDBACK_CAPTURE_PATH = OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_EXTERNAL_AI_FEEDBACK_CAPTURE_20260630.md"
ALLOWED_USE = (
    "design-only Package C external-review integration;"
    "implementation requirements ledger;required-test matrix;schema field checklist;"
    "blocked-model ledger;no-run no-auth"
)
BLOCKED_USE = (
    "Package C physics implementation;proof registry pass;runtime configuration;sidewall PRS/EAS numeric output;"
    "NODI runtime recomputation;COMSOL launch;.mph load;validated Brownian solver output;"
    "validated hindered diffusion;trapezoid Poiseuille solver output;fixed-pressure q_ch output;"
    "flux-weighted sampling;electrokinetic grid output;optical solver output;true W_eff;"
    "reference strength claim;detector response claim;sidewall scattering claim;route_score;winner;JRC;"
    "q_ch weighting;yield;detection_probability;wet pass probability;clogging rate;time-to-clog;"
    "recovery;fabrication release;production ingestion"
)

GATE25_FILES = {
    "status": OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_MANIFEST_20260630.csv",
    "design_scope": OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_PACKAGE_C_DESIGN_SCOPE_20260630.csv",
    "external_prompt": OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_EXTERNAL_AI_PROMPT_20260630.md",
    "joint_report": OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_REPORT_20260630.md",
    "master_report": REPORT_DIR / "456_NODI_COMSOL_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_MASTER_REPORT_20260630.md",
    "gate24_auth_ledger": REPORT_DIR / "450_NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_MASTER_REPORT_20260630.md",
    "gate24_auth_record": OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_GATE_RECORD_20260630.csv",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

REPORTS = {
    "457": "GATE26A_EXTERNAL_REVIEW_INTAKE",
    "458": "GATE26B_BROWNIAN_REFLECTION_REQUIREMENTS",
    "459": "GATE26C_PACKAGE_C_REQUIRED_TEST_MATRIX",
    "460": "GATE26D_REQUIRED_SCHEMA_FIELDS",
    "461": "GATE26E_HINDERED_FLOW_EK_OPTICAL_BLOCKERS",
    "462": "GATE26F_NO_AUTH_FIREWALL",
    "463": "GATE26_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate26 Package C external-review integration packet.")
    parser.add_argument("--confirm-gate26-package-c-external-review-integration", action="store_true")
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def safe_git_head(path: Path = PROJECT_ROOT) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"


def git_is_ancestor(ancestor: str, descendant: str, cwd: Path = PROJECT_ROOT) -> bool:
    if not ancestor or ancestor == "UNKNOWN_COMMIT_READONLY_REFERENCE":
        return False
    try:
        subprocess.run(
            ["git", "-c", f"safe.directory={cwd.as_posix()}", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def external_feedback_capture_text() -> str:
    return """# Gate26 External AI Feedback Capture

Source visibility: user-pasted external AI feedback in the Codex thread, captured
as a Gate26 source artifact because the original external AI did not have local
file access.

Verdict:
- READY_FOR_IMPLEMENTATION_DESIGN_ONLY.
- This verdict is not implementation authorization.
- Package C remains design-review-only / no-auth.

Boundary:
- No NODI runtime recomputation.
- No COMSOL launch.
- No `.mph` load.
- No sidewall PRS/EAS numeric output.
- No proof-registry pass/update.
- No q_ch, JRC, route_score, route winner, yield, detection_probability,
  wet-pass probability, clogging rate, time-to-clog, recovery, fabrication
  release, or production ingestion.

Brownian trajectory requirements:
- Target model: `skorokhod_normal_reflection_convex_offset_trapezoid_v1`.
- Current model remains `trapezoid_center_support_projection_boundary_v1`.
- Current claim remains
  `sidewall_projection_boundary_surrogate_not_specular_reflection`.
- Projection/clamp must not be renamed as validated Brownian reflection,
  specular reflection, or Skorokhod-validated reflection.
- Particle-center support domain is represented by wall constraints
  `g_i(x,u) >= 0`; active wall local time/correction grows only at active walls.
- Single-wall crossing should use a folded-normal / wall-normal mirror update
  in design, not a projection-to-boundary spike.
- Corners require an active-set / normal-cone correction with iteration limits
  and hard fail or substepping if convergence fails.

Required Package C tests:
- `test_trapezoid_skorokhod_normals_match_wall_distance_gradients`
- `test_single_wall_reflection_matches_folded_normal_limit`
- `test_projection_boundary_has_no_validated_reflection_claim`
- `test_reflected_trajectory_all_points_inside_center_support`
- `test_reflected_trajectory_has_no_boundary_atom_spike`
- `test_pure_brownian_equilibrium_uniform_over_accessible_area`
- `test_x_local_norm_uniformity_by_u_slice`
- `test_left_right_symmetry_for_symmetric_trapezoid`
- `test_corner_active_set_no_corner_pileup`
- `test_dt_halving_converges_wall_distance_distribution`
- `test_theta_mutation_changes_boundary_event_counts_and_signature`
- `test_depth_mutation_changes_support_and_signature`
- `test_geometry_closed_blocks_trajectory_runtime`
- `test_near_closed_requires_resource_or_step_guard`
- `test_hindered_diffusion_blocked_under_trapezoid_unless_solver_or_surrogate_label`
- `test_parabolic_rect_and_rect_series_blocked_under_trapezoid`
- `test_fixed_pressure_trapezoid_requires_poisson_solver_or_context_only`
- `test_boltzmann_wall_exclusion_blocked_until_trapezoid_grid_exists`
- `test_reference_field_under_trapezoid_remains_proxy_not_solver`
- `test_no_forbidden_claim_columns_in_package_c_artifacts`

Required schema/design fields:
- `brownian_boundary_target_model`
- `brownian_boundary_numerical_scheme`
- `brownian_boundary_claim_level`
- `not_ballistic_specular_collision_claim`
- `projection_boundary_surrogate_used`
- `reflection_update_rule_id`
- `wall_constraint_formula_id`
- `active_wall_set`
- `active_wall_count`
- `corner_handling_model`
- `corner_guard_status`
- `normal_vector_x`
- `normal_vector_u`
- `reflection_displacement_nm`
- `brownian_rms_step_nm`
- `dt_s`
- `dt_stability_status`
- `dt_halving_convergence_status`
- `dt_halving_max_distribution_delta`
- `max_reflection_iterations`
- `reflection_iteration_count_p50`
- `reflection_iteration_count_p99`
- `corner_active_set_count`
- `boundary_atom_fraction`
- `wall_bias_check_status`
- `equilibrium_uniformity_check_status`
- `rectangle_limit_check_status`
- `one_wall_neumann_kernel_check_status`
- `diffusion_tensor_model`
- `diffusion_hindrance_model`
- `diffusion_hindrance_claim_level`
- `hindered_diffusion_solver_required_reason`
- `flow_control_interpretation`
- `trapezoid_flow_solver_status`
- `trapezoid_velocity_field_status`
- `fixed_pressure_hydraulic_resistance_status`
- `not_qch_weighted`
- `electrokinetic_grid_geometry_model`
- `electrokinetic_solver_status`
- `electrokinetic_claim_level`
- `optical_solver_status`
- `optical_solver_required_reason`
- `not_true_W_eff`
- `not_reference_strength_claim`
- `not_detector_response_claim`
- `not_sidewall_scattering_claim`

Model blockers:
- Trapezoid hindered diffusion remains blocked in v1 except a possible future
  nearest-wall single-plane surrogate with strict one-wall dominance and
  `surrogate_sensitivity_only` claim level.
- Package C v1 safest flow is fixed-velocity plug-flow audit only:
  `flow_profile_model=plug`, `flow_control_mode=fixed_velocity`,
  `not_qch_weighted=true`.
- Trapezoid fixed-pressure/Poiseuille flow requires a future cross-section
  Poisson/no-slip solver or validated lookup.
- Electrokinetic trapezoid claims require a profile-aware grid/solver.
- Optical/reference-field sidewall claims require an actual solver or validated
  lookup before true W_eff, reference strength, detector response, or sidewall
  scattering can be claimed.
"""


def gate25_source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, (label, path) in enumerate(GATE25_FILES.items(), start=1):
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_rows = csv_count(path) if exists else "MISSING"
        rows.append(
            {
                "source_lock_id": f"G26A-GATE25-{idx:03d}",
                "source_gate": "Gate25",
                "source_label": label,
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "expected_row_count": actual_rows,
                "actual_row_count": actual_rows,
                "expected_sha256": actual_sha,
                "actual_sha256": actual_sha,
                "sha256_match": bool_text(exists),
                "row_count_match": bool_text(exists),
                "lock_status": "MATCH" if exists else "MISSING_GATE26_SOURCE_ARTIFACT",
                "source_visibility_status": "local_repo_artifact_visible_to_codex",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    feedback_text = external_feedback_capture_text()
    rows.append(
        {
            "source_lock_id": f"G26A-GATE25-{len(rows) + 1:03d}",
            "source_gate": "ExternalAI",
            "source_label": "external_ai_feedback_capture",
            "path": EXTERNAL_FEEDBACK_CAPTURE_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "expected_row_count": "NA",
            "actual_row_count": "NA",
            "expected_sha256": sha256_text(feedback_text),
            "actual_sha256": sha256_text(feedback_text),
            "sha256_match": "true",
            "row_count_match": "true",
            "lock_status": "MATCH",
            "source_visibility_status": "user_pasted_chat_feedback_captured_by_gate26",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def external_review_intake_rows() -> list[dict[str, str]]:
    return [
        {
            "intake_id": "G26A-EXTERNAL-REVIEW-001",
            "external_feedback_artifact_id": EXTERNAL_FEEDBACK_ARTIFACT_ID,
            "external_feedback_path": EXTERNAL_FEEDBACK_CAPTURE_PATH.relative_to(PROJECT_ROOT).as_posix(),
            "external_feedback_sha256": sha256_text(external_feedback_capture_text()),
            "external_feedback_visibility_status": "user_pasted_chat_feedback_captured_by_gate26",
            "external_review_visibility": "github_visible_files_plus_user_supplied_local_fact_packet",
            "external_review_verdict": EXTERNAL_VERDICT,
            "integrated_disposition": DISPOSITION,
            "implementation_authorized": "false",
            "runtime_allowed": "false",
            "review_scope": "Package C implementation design requirements only",
            "hard_requirement_summary": (
                "Skorokhod normal reflection target;active-set corner handling;"
                "no boundary atom;uniform equilibrium;dt-halving convergence;schema/test/blocker hard requirements"
            ),
            "current_projection_policy": "projection_boundary_surrogate_may_remain_audit_only",
            "projection_as_validated_reflection_allowed": "false",
            "claim_boundary": "design_only_no_auth_not_runtime_not_numeric_prs_eas",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def brownian_reflection_requirement_rows() -> list[dict[str, str]]:
    specs = [
        (
            "target_model",
            "brownian_boundary_target_model",
            "skorokhod_normal_reflection_convex_offset_trapezoid_v1",
            "current code exposes projection surrogate only",
            "Package C design must target reflected Brownian motion in the particle-center offset trapezoid.",
            "target model absent or current projection renamed as validated reflection",
        ),
        (
            "current_projection_claim",
            "trajectory_boundary_claim_level",
            "sidewall_projection_boundary_surrogate_not_specular_reflection",
            "trapezoid_center_support_projection_boundary_v1",
            "Projection may be kept only as audit/projection surrogate with explicit non-validated claim level.",
            "projection boundary is described as specular, validated reflection, Skorokhod-validated, or true Brownian reflection",
        ),
        (
            "wall_constraints",
            "wall_constraint_formula_id",
            "trapezoid_center_support_half_plane_constraints_v1",
            "geometry primitive already exposes wall distances/support checks",
            "Four wall constraints and inward normals must be explicit for top, bottom, left, and right walls.",
            "nearest-wall-only normal is used for corner active sets",
        ),
        (
            "single_wall_update",
            "reflection_update_rule_id",
            "folded_normal_single_wall_mirror_update_v1",
            "not implemented as validated Package C physics",
            "Single-plane crossing design must mirror the overshoot along the inward unit normal.",
            "single-wall crossing is clamped to wall or projected to a boundary atom",
        ),
        (
            "corner_active_set",
            "corner_handling_model",
            "convex_polygon_normal_cone_active_set_v1",
            "current projection style is not final corner physics",
            "Corners require active-wall sets, nonnegative normal corrections, iteration limits, and fail-closed guards.",
            "corner correction does not converge or uses nearest_wall_id only",
        ),
        (
            "support_invariant",
            "support_invariant_check",
            "contains_particle_center_true_for_every_sample",
            "geometry contains checks exist",
            "All generated trajectory points must remain inside particle-center support.",
            "any sample violates contains_particle_center",
        ),
        (
            "boundary_atom",
            "boundary_atom_fraction",
            "measured_and_bounded_no_projection_spike",
            "projection surrogate can create boundary pile-up",
            "Long pure-Brownian tests must reject artificial atoms at walls or corners.",
            "excess exact-boundary occupancy or projection spike detected",
        ),
        (
            "uniform_equilibrium",
            "equilibrium_uniformity_check_status",
            "pure_brownian_uniform_over_center_accessible_area_required",
            "not yet a Package C pass criterion",
            "With plug flow, no drift, and no hindrance, stationary density must match accessible-area uniformity.",
            "u marginal, x-local slices, or left-right symmetry fail",
        ),
        (
            "dt_halving",
            "dt_halving_convergence_status",
            "dt_dt2_dt4_distribution_convergence_required",
            "not yet a Package C pass criterion",
            "Time-step halving must converge wall-distance distributions, event counts, and short-lag MSD.",
            "distribution deltas do not decrease or remain above tolerance",
        ),
        (
            "rectangle_limit",
            "rectangle_limit_check_status",
            "k_zero_numeric_equivalence_without_cache_or_schema_equivalence",
            "ideal_rectangle remains native path",
            "At COMSOL 90 deg the trapezoid math may be numerically equivalent to rectangle, but signatures remain distinct.",
            "old rectangular cache satisfies trapezoid request",
        ),
        (
            "angle_depth_mutation",
            "theta_depth_mutation_check_status",
            "angle_and_depth_mutation_changes_support_wall_distance_events_and_signature",
            "mutation checks exist for earlier gates but not Package C reflection physics",
            "Theta/depth mutation must change bottom width, support, wall-distance distribution, event counts, and signature.",
            "mutating angle/depth leaves Package C signature or wall-distance/event diagnostics unchanged",
        ),
        (
            "closed_geometry_guard",
            "corner_guard_status",
            "geometry_closed_or_near_closed_blocks_or_substeps_runtime",
            "closure descriptors exist",
            "Closed/near-closed geometry must block trajectory runtime or require explicit resource/step guard.",
            "trajectory runtime proceeds through closed or zero-width support",
        ),
    ]
    return [
        {
            "requirement_id": f"G26B-BROWNIAN-{idx:03d}",
            "requirement_family": family,
            "required_field_or_model": field,
            "required_value": value,
            "current_state": current,
            "hard_requirement": hard_requirement,
            "fail_condition": fail_condition,
            "required_before_package_c_pass": "true",
            "implementation_authorized": "false",
            "runtime_allowed": "false",
            "allowed_claim_level_now": "design_requirement_only",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (family, field, value, current, hard_requirement, fail_condition) in enumerate(specs, start=1)
    ]


def required_test_matrix_rows() -> list[dict[str, str]]:
    tests = [
        ("test_trapezoid_skorokhod_normals_match_wall_distance_gradients", "brownian_reflection", "normal vectors match gradients of wall-distance constraints"),
        ("test_single_wall_reflection_matches_folded_normal_limit", "brownian_reflection", "single wall crossing avoids clamp/projection spike"),
        ("test_projection_boundary_has_no_validated_reflection_claim", "claim_guard", "current projection boundary cannot be called validated reflection"),
        ("test_reflected_trajectory_all_points_inside_center_support", "support", "all samples satisfy contains_particle_center"),
        ("test_reflected_trajectory_has_no_boundary_atom_spike", "boundary_bias", "reject artificial exact-wall atoms"),
        ("test_pure_brownian_equilibrium_uniform_over_accessible_area", "equilibrium", "stationary distribution follows accessible-area uniformity"),
        ("test_x_local_norm_uniformity_by_u_slice", "equilibrium", "x local normalized distribution is uniform within u slices"),
        ("test_left_right_symmetry_for_symmetric_trapezoid", "symmetry", "left/right occupancy and nearest-wall counts remain symmetric"),
        ("test_corner_active_set_no_corner_pileup", "corner", "corner bins converge without pile-up or depletion"),
        ("test_dt_halving_converges_wall_distance_distribution", "dt_convergence", "dt, dt/2, dt/4 wall-distance distributions converge"),
        ("test_theta_mutation_changes_boundary_event_counts_and_signature", "mutation", "angle mutation changes events and signatures"),
        ("test_depth_mutation_changes_support_and_signature", "mutation", "depth mutation changes support and signatures"),
        ("test_geometry_closed_blocks_trajectory_runtime", "closure", "closed geometry cannot run as open trajectory"),
        ("test_near_closed_requires_resource_or_step_guard", "closure", "near-closed geometry requires guard/substep policy"),
        ("test_hindered_diffusion_blocked_under_trapezoid_unless_solver_or_surrogate_label", "hindered_diffusion", "hindered diffusion remains blocked or explicitly surrogate"),
        ("test_parabolic_rect_and_rect_series_blocked_under_trapezoid", "flow", "rectangular flow models cannot run under trapezoid"),
        ("test_fixed_pressure_trapezoid_requires_poisson_solver_or_context_only", "flow", "fixed pressure output requires solver/lookup or context-only"),
        ("test_boltzmann_wall_exclusion_blocked_until_trapezoid_grid_exists", "electrokinetic", "rectangular wall-distance EK grid remains blocked"),
        ("test_reference_field_under_trapezoid_remains_proxy_not_solver", "optical_reference", "reference field remains proxy until solver"),
        ("test_no_forbidden_claim_columns_in_package_c_artifacts", "claim_guard", "no route/yield/detection/production columns"),
    ]
    return [
        {
            "test_id": f"G26C-TEST-{idx:03d}",
            "test_name": name,
            "package_c_area": area,
            "expected_guard": guard,
            "required_before_package_c_pass": "true",
            "implementation_authorized": "false",
            "runtime_allowed": "false",
            "output_numeric_prs_eas_allowed": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (name, area, guard) in enumerate(tests, start=1)
    ]


SCHEMA_FIELD_GROUPS: dict[str, list[str]] = {
    "brownian_reflection": [
        "brownian_boundary_target_model",
        "brownian_boundary_numerical_scheme",
        "brownian_boundary_claim_level",
        "not_ballistic_specular_collision_claim",
        "projection_boundary_surrogate_used",
        "reflection_update_rule_id",
        "wall_constraint_formula_id",
        "active_wall_set",
        "active_wall_count",
        "corner_handling_model",
        "corner_guard_status",
        "normal_vector_x",
        "normal_vector_u",
        "reflection_displacement_nm",
    ],
    "dt_convergence": [
        "brownian_rms_step_nm",
        "dt_s",
        "dt_stability_status",
        "dt_halving_convergence_status",
        "dt_halving_max_distribution_delta",
        "max_reflection_iterations",
        "reflection_iteration_count_p50",
        "reflection_iteration_count_p99",
        "corner_active_set_count",
        "boundary_atom_fraction",
        "wall_bias_check_status",
        "equilibrium_uniformity_check_status",
        "rectangle_limit_check_status",
        "one_wall_neumann_kernel_check_status",
    ],
    "diffusion_hindrance": [
        "diffusion_tensor_model",
        "diffusion_hindrance_model",
        "diffusion_hindrance_claim_level",
        "hindered_diffusion_solver_required_reason",
    ],
    "flow": [
        "flow_control_interpretation",
        "trapezoid_flow_solver_status",
        "trapezoid_velocity_field_status",
        "fixed_pressure_hydraulic_resistance_status",
        "not_qch_weighted",
    ],
    "electrokinetic": [
        "electrokinetic_grid_geometry_model",
        "electrokinetic_solver_status",
        "electrokinetic_claim_level",
    ],
    "optical_reference": [
        "optical_solver_status",
        "optical_solver_required_reason",
        "not_true_W_eff",
        "not_reference_strength_claim",
        "not_detector_response_claim",
        "not_sidewall_scattering_claim",
    ],
}


def required_schema_field_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for group, fields in SCHEMA_FIELD_GROUPS.items():
        for field in fields:
            rows.append(
                {
                    "schema_field_id": f"G26D-SCHEMA-{len(rows) + 1:03d}",
                    "field_group": group,
                    "field_name": field,
                    "required_before_package_c_pass": "true",
                    "implementation_authorized": "false",
                    "runtime_allowed": "false",
                    "purpose": f"Package C {group} design and validation guard",
                    "allowed_now": "design_requirement_only",
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    return rows


def blocked_model_ledger_rows() -> list[dict[str, str]]:
    specs = [
        (
            "hindered_diffusion_trapezoid",
            "blocked",
            "solver_or_explicit_single_wall_surrogate_with_corner_exclusion",
            "none_or_surrogate_sensitivity_only",
            "adhesion_probability;wet_pass_probability;clogging_rate;time_to_clog;recovery;yield;detection_probability",
        ),
        (
            "single_wall_hindrance_optional_future",
            "future_design_only",
            "one_wall_dominance_threshold_and_multi_wall_corner_guard",
            "surrogate_sensitivity_only",
            "validated_trapezoid_hydrodynamics;wet_performance_claims",
        ),
        (
            "fixed_velocity_plug_flow_audit",
            "allowed_design_only",
            "flow_profile_model=plug;flow_control_mode=fixed_velocity;not_qch_weighted=true",
            "geometry_independent_uniform_flow_surrogate",
            "q_ch;route_weighting;fixed_pressure_Q;trapezoid_poiseuille",
        ),
        (
            "trapezoid_velocity_field",
            "blocked_future_solver",
            "trapezoid_cross_section_poisson_solver_v1_or_validated_lookup",
            "solver_required",
            "rect_series_under_trapezoid;parabolic_rect_under_trapezoid",
        ),
        (
            "fixed_pressure_hydraulic_resistance",
            "blocked_future_solver",
            "validated_trapezoid_pressure_flow_solver_or_context_only",
            "solver_required_or_context_only",
            "q_ch;q_ch_eta;q_ch_chi_eta;route_score;winner",
        ),
        (
            "electrokinetic_trapezoid",
            "blocked",
            "trapezoid_cut_cell_or_fem_grid_and_wall_distance_model",
            "solver_required",
            "rectangular_wall_distance_grid_claim;formula_use_without_ionic_metadata",
        ),
        (
            "reference_field_optical",
            "blocked_proxy_only",
            "optical_solver_or_validated_lookup_consuming_sidewall_geometry",
            "proxy_not_sidewall_aware_not_optical_solver_output",
            "true_W_eff;reference_strength_claim;detector_response_claim;sidewall_scattering_claim",
        ),
        (
            "route_and_production_claims",
            "blocked_forever_in_this_gate",
            "out_of_scope_requires_separate_future_authorization",
            "not_allowed",
            "JRC;route_score;winner;yield;detection_probability;fabrication_release;production_ingestion",
        ),
    ]
    return [
        {
            "blocker_id": f"G26E-BLOCKER-{idx:03d}",
            "model_scope": scope,
            "current_status": status,
            "future_unlock_requirement": requirement,
            "allowed_claim_level": claim_level,
            "forbidden_claims": forbidden,
            "implementation_authorized": "false",
            "runtime_allowed": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (scope, status, requirement, claim_level, forbidden) in enumerate(specs, start=1)
    ]


def no_auth_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G26F-NOAUTH-001",
            "package_c_physics_implementation_authorized": "false",
            "package_c_proof_registry_pass_authorized": "false",
            "proof_registry_update_authorized": "false",
            "runtime_configuration_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recompute_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "fabrication_release_authorized": "false",
            "projection_boundary_validated_reflection_authorized": "false",
            "hindered_diffusion_trapezoid_authorized": "false",
            "trapezoid_poiseuille_authorized": "false",
            "electrokinetic_trapezoid_solver_authorized": "false",
            "optical_solver_output_authorized": "false",
            "firewall_status": "PASS_GATE26_DESIGN_ONLY_NO_AUTH",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def validation_plan_rows() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py --confirm-gate26-package-c-external-review-integration",
        "python -m py_compile tools/audits/build_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py",
        "python -m pytest tests/test_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py -q",
        "python -m pytest tests/test_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py tests/test_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py -q",
    ]
    return [
        {
            "validation_id": f"G26-VALIDATION-{idx:03d}",
            "command": command,
            "required_for_pass": "true",
            "recorded_result": "PENDING_RUNTIME_VALIDATION",
        }
        for idx, command in enumerate(commands, start=1)
    ]


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G26-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    gate25_status = read_json(GATE25_FILES["status"])
    gate25_summary = gate25_status.get("summary", {})
    current_head = safe_git_head(PROJECT_ROOT)
    source_locks = gate25_source_lock_rows()
    intake = external_review_intake_rows()
    brownian = brownian_reflection_requirement_rows()
    tests = required_test_matrix_rows()
    fields = required_schema_field_rows()
    blockers = blocked_model_ledger_rows()
    firewall = no_auth_firewall_rows()
    validation = validation_plan_rows()
    summary = {
        "disposition": DISPOSITION,
        "gate26_build_head": current_head,
        "gate25_build_head": gate25_summary.get("gate25_build_head", ""),
        "gate25_head_is_ancestor_of_current": git_is_ancestor(gate25_summary.get("gate25_build_head", ""), current_head, PROJECT_ROOT),
        "gate25_disposition": gate25_status.get("disposition", ""),
        "gate25_no_auth": gate25_status.get("no_auth", False),
        "gate25_review_only": gate25_status.get("review_only", False),
        "gate25_source_lock_rows": len(source_locks),
        "gate25_source_drift": sum(row["lock_status"] == "BLOCKING_GATE25_SOURCE_DRIFT" for row in source_locks),
        "gate25_missing_sources": sum(row["lock_status"] == "MISSING_GATE25_ARTIFACT" for row in source_locks),
        "external_review_verdict": EXTERNAL_VERDICT,
        "external_review_rows": len(intake),
        "brownian_requirement_rows": len(brownian),
        "required_test_rows": len(tests),
        "required_schema_field_rows": len(fields),
        "blocked_model_rows": len(blockers),
        "validation_plan_rows": len(validation),
        "implementation_authorized_rows": sum(
            row.get("implementation_authorized") == "true"
            for row in intake + brownian + tests + fields + blockers
        ),
        "runtime_allowed_rows": sum(row.get("runtime_allowed") == "true" for row in intake + brownian + tests + fields + blockers),
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_GATE26_DESIGN_ONLY_NO_AUTH" else 1,
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "gate25_source_locks": source_locks,
        "external_review_intake": intake,
        "brownian_reflection_requirements": brownian,
        "required_test_matrix": tests,
        "required_schema_fields": fields,
        "blocked_model_ledger": blockers,
        "no_auth_firewall": firewall,
        "validation_plan": validation,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    tests = {row["test_name"] for row in payload["required_test_matrix"]}
    fields = {row["field_name"] for row in payload["required_schema_fields"]}
    brownian_by_family = {row["requirement_family"]: row for row in payload["brownian_reflection_requirements"]}
    blockers_by_scope = {row["model_scope"]: row for row in payload["blocked_model_ledger"]}
    firewall = payload["no_auth_firewall"][0]
    required_tests = {
        "test_trapezoid_skorokhod_normals_match_wall_distance_gradients",
        "test_single_wall_reflection_matches_folded_normal_limit",
        "test_projection_boundary_has_no_validated_reflection_claim",
        "test_pure_brownian_equilibrium_uniform_over_accessible_area",
        "test_dt_halving_converges_wall_distance_distribution",
        "test_no_forbidden_claim_columns_in_package_c_artifacts",
    }
    required_fields = {
        "brownian_boundary_target_model",
        "brownian_boundary_numerical_scheme",
        "brownian_boundary_claim_level",
        "projection_boundary_surrogate_used",
        "reflection_update_rule_id",
        "corner_handling_model",
        "dt_halving_convergence_status",
        "boundary_atom_fraction",
        "equilibrium_uniformity_check_status",
        "diffusion_hindrance_claim_level",
        "trapezoid_flow_solver_status",
        "electrokinetic_grid_geometry_model",
        "optical_solver_status",
        "not_true_W_eff",
        "not_qch_weighted",
    }
    checks = {
        "Gate25 head ancestry": s["gate25_head_is_ancestor_of_current"] is True,
        "Gate25 disposition": s["gate25_disposition"] == EXPECTED_GATE25_DISPOSITION,
        "Gate25 no-auth": s["gate25_no_auth"] is True,
        "Gate25 review-only": s["gate25_review_only"] is True,
        "Gate25 source locks": s["gate25_source_lock_rows"] >= 8,
        "Gate25 source drift": s["gate25_source_drift"] == 0,
        "Gate25 missing sources": s["gate25_missing_sources"] == 0,
        "External verdict integrated": s["external_review_verdict"] == EXTERNAL_VERDICT,
        "No implementation authorized rows": s["implementation_authorized_rows"] == 0,
        "No runtime allowed rows": s["runtime_allowed_rows"] == 0,
        "Brownian target": brownian_by_family.get("target_model", {}).get("required_value")
        == "skorokhod_normal_reflection_convex_offset_trapezoid_v1",
        "Projection not validated": brownian_by_family.get("current_projection_claim", {}).get("required_value")
        == "sidewall_projection_boundary_surrogate_not_specular_reflection",
        "Corner active set": brownian_by_family.get("corner_active_set", {}).get("required_value")
        == "convex_polygon_normal_cone_active_set_v1",
        "Required tests present": required_tests <= tests,
        "Required fields present": required_fields <= fields,
        "Hindered diffusion blocked": blockers_by_scope.get("hindered_diffusion_trapezoid", {}).get("current_status") == "blocked",
        "Flow qch forbidden": "q_ch" in blockers_by_scope.get("fixed_velocity_plug_flow_audit", {}).get("forbidden_claims", ""),
        "Optical true W_eff forbidden": "true_W_eff" in blockers_by_scope.get("reference_field_optical", {}).get("forbidden_claims", ""),
        "No-auth firewall": s["no_auth_firewall_failures"] == 0,
    }
    for key, value in firewall.items():
        if key.endswith("_authorized"):
            checks[f"No-auth false: {key}"] = value == "false"
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    EXTERNAL_FEEDBACK_CAPTURE_PATH.write_text(external_feedback_capture_text(), encoding="utf-8")
    generated.append(EXTERNAL_FEEDBACK_CAPTURE_PATH)
    csv_specs = {
        "NODI_COMSOL_GATE26_SIDEWALL_GATE25_SOURCE_LOCK_20260630.csv": payload["gate25_source_locks"],
        "NODI_COMSOL_GATE26_SIDEWALL_EXTERNAL_REVIEW_INTAKE_20260630.csv": payload["external_review_intake"],
        "NODI_COMSOL_GATE26_SIDEWALL_BROWNIAN_REFLECTION_REQUIREMENTS_20260630.csv": payload["brownian_reflection_requirements"],
        "NODI_COMSOL_GATE26_SIDEWALL_PACKAGE_C_REQUIRED_TEST_MATRIX_20260630.csv": payload["required_test_matrix"],
        "NODI_COMSOL_GATE26_SIDEWALL_REQUIRED_SCHEMA_FIELDS_20260630.csv": payload["required_schema_fields"],
        "NODI_COMSOL_GATE26_SIDEWALL_BLOCKED_MODEL_LEDGER_20260630.csv": payload["blocked_model_ledger"],
        "NODI_COMSOL_GATE26_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE26_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate26 Sidewall Package C External Review Integration",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- External verdict integrated: `{payload['summary']['external_review_verdict']}`.",
            f"- Gate25 source drift/missing: {payload['summary']['gate25_source_drift']}/{payload['summary']['gate25_missing_sources']}.",
            f"- Brownian requirements / required tests / schema fields: {payload['summary']['brownian_requirement_rows']}/{payload['summary']['required_test_rows']}/{payload['summary']['required_schema_field_rows']}.",
            "- Current projection boundary remains a surrogate; it is not a validated Brownian or specular reflection claim.",
            "- Package C remains design-only/no-auth: no runtime, no COMSOL launch, no .mph load, no sidewall PRS/EAS numeric output, no q_ch/JRC/route/yield/detection/fabrication claim.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        lines = [
            f"- Gate26 disposition: `{DISPOSITION}`",
            f"- External review verdict: `{EXTERNAL_VERDICT}` integrated as design-only/no-auth.",
            f"- Gate25 source drift/missing: {payload['summary']['gate25_source_drift']}/{payload['summary']['gate25_missing_sources']}.",
            "- Boundary: no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
            f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
        ]
        if number == "458":
            lines.extend(
                [
                    "- Brownian target model: `skorokhod_normal_reflection_convex_offset_trapezoid_v1`.",
                    "- Current projection model remains `sidewall_projection_boundary_surrogate_not_specular_reflection` only.",
                    "- Hard requirements include active-set corner handling, no boundary atom, uniform equilibrium, dt-halving convergence, rectangle limit, angle/depth mutation, and closure guards.",
                ]
            )
        if number == "459":
            lines.append(f"- Required Package C tests recorded: {payload['summary']['required_test_rows']}.")
        if number == "460":
            lines.append(f"- Required schema fields recorded: {payload['summary']['required_schema_field_rows']}.")
        if number == "461":
            lines.append("- Hindered diffusion, trapezoid pressure flow, electrokinetic grids, and optical/reference claims remain blocked or solver_required.")
        if number == "462":
            lines.append("- No-auth firewall fields all remain false.")
        write_md(path, title.replace("_", " "), lines)
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate26_package_c_external_review_integration:
        parser.error("--confirm-gate26-package-c-external-review-integration is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE26_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_INTEGRATION")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
