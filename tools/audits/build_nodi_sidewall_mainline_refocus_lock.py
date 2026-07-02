#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import (  # noqa: E402
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_MAINLINE_REFOCUS_LOCK"
ARTIFACT_ID = "NODI_SIDEWALL_MAINLINE_REFOCUS_LOCK_20260702"
DISPOSITION = "NODI_SIDEWALL_MAINLINE_REFOCUS_LOCK_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_MAINLINE_REFOCUS_LOCK_FAIL_CLOSED"
CLAIM_BOUNDARY = (
    "sidewall_angle_effect_on_recommendation_annulus_interference_not_route_winner"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

SOURCE_FILES = {
    "comsol_v4_upper_alignment_status": OUTPUT_DIR
    / "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_STATUS_20260702.json",
    "comsol_v4_alignment_extension_status": OUTPUT_DIR
    / "NODI_COMSOL_V4_ALIGNMENT_EXTENSION_STATUS_20260702.json",
    "sidewall_simulation_release_envelope": REPORT_DIR
    / "585_NODI_PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE_20260701.md",
    "sidewall_route_correction": REPORT_DIR
    / "580_NODI_PACKAGE_C_SIDEWALL_SIMULATION_ASSUMPTION_ROUTE_CORRECTION_20260702.md",
    "sidewall_selected_annulus_context": PROJECT_ROOT
    / "nodi_simulator/sidewall_selected_annulus_context.py",
    "sidewall_reference_surrogate_candidate": PROJECT_ROOT
    / "nodi_simulator/sidewall_reference_surrogate_candidate.py",
    "sidewall_optical_reference_smoke": PROJECT_ROOT
    / "nodi_simulator/sidewall_optical_reference_smoke.py",
    "position_response_surface_validator": PROJECT_ROOT
    / "tools/audits/validate_nodi_position_response_surface.py",
    "sidewall_integrated_promotion_ledger": PROJECT_ROOT
    / "nodi_simulator/sidewall_integrated_promotion_ledger.py",
    "sidewall_winner_jrc_policy_review": PROJECT_ROOT
    / "nodi_simulator/sidewall_winner_jrc_policy_review.py",
    "mainline_refocus_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_mainline_refocus_lock.py",
    "mainline_refocus_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_mainline_refocus_lock.py",
}

ALLOWED_USE = (
    "govern sidewall-angle work toward dimension recommendation drift, "
    "selected-annulus remapping, and interference-enhancement sensitivity"
)
BLOCKED_USE = (
    "route winner as the primary question; score-board driven comparison; "
    "waiting for real experiments before simulation progress; collapsing "
    "ideal rectangle and trapezoid into one geometry"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the sidewall-angle mainline refocus lock."
    )
    parser.add_argument(
        "--confirm-sidewall-mainline-refocus-lock",
        action="store_true",
    )
    return parser


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={PROJECT_ROOT.as_posix()}", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_head() -> str:
    return run_git(["rev-parse", "HEAD"])


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def git_path_from_status_line(line: str) -> str:
    return line[2:].strip().replace("\\", "/") if len(line) > 2 else line


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    output_prefix = f"reports/joint_interface_{DATE_STAMP}/{PREFIX}_"
    output_report = f"reports/588_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_mainline_refocus_lock.py",
        "tests/test_nodi_sidewall_mainline_refocus_lock.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "mainline_refocus_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "mainline_refocus_output"
            release_decision = "included_or_rewritten_by_mainline_refocus_builder"
        else:
            classification = "non_mainline_refocus_dirty_context"
            release_decision = "ignored_for_mainline_refocus_lock"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def mainline_axis_rows() -> list[dict[str, Any]]:
    return [
        {
            "axis_id": "AXIS-001",
            "axis_name": "dimension_recommendation_sensitivity",
            "primary_question": (
                "Does adding sidewall angle move the recommended NODI channel "
                "width/depth family or tolerable geometry window?"
            ),
            "must_compare_against": "ideal_rectangle_baseline",
            "required_inputs": (
                "W_top_nm;depth_nm;sidewall_deg_comsol;W_bottom_unclipped_nm;"
                "closure_status;center_accessible_area;220_300nm_support;"
                "formal_qch_transport_input_only"
            ),
            "required_outputs": (
                "recommended_dimension_shift_nm;dimension_family_stability_band;"
                "geometry_closure_blockers;tail_particle_support_delta;"
                "baseline_scope_not_extrapolated"
            ),
            "not_primary": "route_winner_or_scoreboard",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "axis_id": "AXIS-002",
            "axis_name": "selected_annulus_sidewall_remap",
            "primary_question": (
                "Does sidewall angle change the selected annulus coordinate range, "
                "bin validity, or center-accessible support?"
            ),
            "must_compare_against": "rectangle_selected_annulus_basis",
            "required_inputs": (
                "annulus_id;old_rectangle_basis;x_nm;u_nm;x_local_norm;"
                "u_norm;d_nearest_wall_nm;bin_accessible"
            ),
            "required_outputs": (
                "annulus_remap_status;annulus_range_shift;blocked_bins;"
                "new_trapezoid_annulus_basis;no_neighbor_fill_for_blocked_bins;"
                "small_n_context_not_recommendation"
            ),
            "not_primary": "ranking_route_families",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "axis_id": "AXIS-003",
            "axis_name": "interference_enhancement_sidewall_sensitivity",
            "primary_question": (
                "Does sidewall angle change the interference-enhancement proxy "
                "or response map through particle position, reference field, "
                "or detector overlap assumptions?"
            ),
            "must_compare_against": "rectangle_response_map",
            "required_inputs": (
                "response_map_basis;reference_field_model;detector_operator_id;"
                "particle_position_distribution;near_wall_response_bins"
            ),
            "required_outputs": (
                "enhancement_delta_map;near_wall_response_shift;"
                "reference_field_solver_needed_flags;annulus_response_delta;"
                "true_W_eff_not_claimed"
            ),
            "not_primary": "bare_detection_probability",
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]


def work_package_rows() -> list[dict[str, Any]]:
    return [
        {
            "package_id": "SW-MAIN-001",
            "package_name": "dimension_recommendation_drift_matrix",
            "depends_on_axis": "AXIS-001",
            "scope": "theta/depth/top-width/particle-tail sweep against rectangle baseline",
            "first_output": "dimension_recommendation_shift_rows",
            "hard_checks": (
                "keeps_ideal_rectangle_baseline;preserves_unclipped_bottom_width;"
                "reports_blocked_closed_geometries;does_not_emit_route_winner;"
                "W500_D900_not_extrapolated_to_full_size_space;"
                "formal_qch_transport_input_only"
            ),
        },
        {
            "package_id": "SW-MAIN-002",
            "package_name": "selected_annulus_trapezoid_remap",
            "depends_on_axis": "AXIS-002",
            "scope": "map rectangle annulus bins into trapezoid local-width coordinates",
            "first_output": "annulus_remap_rows",
            "hard_checks": (
                "all_bins_have_coordinate_basis;blocked_bins_no_numeric_response;"
                "no_neighbor_fill;old_annulus_names_do_not_hide_geometry_basis;"
                "small_n_smoke_rows_context_only"
            ),
        },
        {
            "package_id": "SW-MAIN-003",
            "package_name": "interference_enhancement_response_sensitivity",
            "depends_on_axis": "AXIS-003",
            "scope": "response/enhancement proxy maps over rectangle and trapezoid distributions",
            "first_output": "interference_enhancement_delta_rows",
            "hard_checks": (
                "separates_position_distribution_effect_from_reference_field_effect;"
                "marks_solver_required_for_true_reference_change;"
                "does_not_reduce_to_detection_probability_only;"
                "trapezoid_effective_aperture_surrogate_not_true_W_eff"
            ),
        },
        {
            "package_id": "SW-MAIN-004",
            "package_name": "v4_assumption_overlay_for_axes",
            "depends_on_axis": "AXIS-001;AXIS-002;AXIS-003",
            "scope": "overlay COMSOL V4 LOW/MID/HIGH/EXTREME assumptions on the three axes",
            "first_output": "v4_axis_overlay_rows",
            "hard_checks": (
                "keeps_v4_id_version_sha;extreme_branch_not_default_merged;"
                "uses_simulation_assumptions_not_experimental_waiting"
            ),
        },
    ]


def drift_guard_rows() -> list[dict[str, Any]]:
    return [
        {
            "guard_id": "DRIFT-001",
            "forbidden_primary_frame": "which_route_wins_or_loses",
            "replacement_frame": "which_dimensions_annuli_and_response_maps_shift",
            "hard_fail_if": "master_report_or_status_makes_route_winner_the_primary_question",
        },
        {
            "guard_id": "DRIFT-002",
            "forbidden_primary_frame": "waiting_for_real_experimental_data",
            "replacement_frame": "extreme_simulation_from_NODI_COMSOL_assumptions",
            "hard_fail_if": "work_package_is_blocked_only_because_project_measurement_is_missing",
        },
        {
            "guard_id": "DRIFT-003",
            "forbidden_primary_frame": "single_scalar_sidewall_score",
            "replacement_frame": "dimension_shift_annulus_shift_interference_delta",
            "hard_fail_if": "output_has_score_without_axis_specific_delta_fields",
        },
        {
            "guard_id": "DRIFT-004",
            "forbidden_primary_frame": "trapezoid_replaces_rectangle",
            "replacement_frame": "rectangle_baseline_and_sidewall_geometry_coexist",
            "hard_fail_if": "ideal_rectangle_baseline_is_removed_or_overwritten",
        },
        {
            "guard_id": "DRIFT-005",
            "forbidden_primary_frame": "q_ch_eta_or_q_ch_weighted_recommendation_score",
            "replacement_frame": "formal_qch_transport_input_only",
            "hard_fail_if": "q_ch_is_multiplied_into_eta_detection_or_recommendation_score",
        },
        {
            "guard_id": "DRIFT-006",
            "forbidden_primary_frame": "small_n_smoke_as_recommendation_evidence",
            "replacement_frame": "small_n_smoke_context_only_until_full_matrix",
            "hard_fail_if": "small_n_rows_change_recommended_dimension_or_annulus_without_full_matrix",
        },
    ]


def source_hint_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_hint_id": "SOURCE-HINT-001",
            "source_path": "nodi_simulator/sidewall_selected_annulus_context.py",
            "preferred_axis": "AXIS-002",
            "source_role": "selected_annulus_context_fields",
            "usable_fields": (
                "channel_cross_section_model;sidewall_deg_comsol;"
                "selected_annulus_edge_norm_min;selected_annulus_edge_norm_max;"
                "selected_annulus_mean_edge_norm"
            ),
            "use_limit": "context_for_annulus_remap_not_detection_probability",
        },
        {
            "source_hint_id": "SOURCE-HINT-002",
            "source_path": "nodi_simulator/sidewall_reference_surrogate_candidate.py",
            "preferred_axis": "AXIS-001;AXIS-003",
            "source_role": "effective_aperture_surrogate_input",
            "usable_fields": "A_ref;g_ref;effective_aperture_factor;sidewall_angle",
            "use_limit": "surrogate_only_not_true_W_eff_or_full_wave_solution",
        },
        {
            "source_hint_id": "SOURCE-HINT-003",
            "source_path": "nodi_simulator/sidewall_optical_reference_smoke.py",
            "preferred_axis": "AXIS-003",
            "source_role": "optical_reference_smoke_context",
            "usable_fields": "reference_geometry;phi_ref_source;reference_smoke_status",
            "use_limit": "smoke_context_only_not_detector_response_claim",
        },
        {
            "source_hint_id": "SOURCE-HINT-004",
            "source_path": "tools/audits/validate_nodi_position_response_surface.py",
            "preferred_axis": "AXIS-003",
            "source_role": "response_surface_schema_validator_prototype",
            "usable_fields": "response_surface_artifact_version;row_scope;bin_id;edge_norm_min;edge_norm_max",
            "use_limit": "schema_ancestor_not_finished_sidewall_response_map",
        },
        {
            "source_hint_id": "SOURCE-HINT-005",
            "source_path": "nodi_simulator/sidewall_integrated_promotion_ledger.py",
            "preferred_axis": "AXIS-001;AXIS-002;AXIS-003",
            "source_role": "downstream_ledger_consumer",
            "usable_fields": "next_evidence_focus;claim_boundary;ledger_status",
            "use_limit": "consume_delta_lock_as_context_not_claim_unlock",
        },
    ]


def negative_context_rows() -> list[dict[str, Any]]:
    return [
        {
            "negative_context_id": "NEGATIVE-CONTEXT-001",
            "source_path": "nodi_simulator/sidewall_winner_jrc_policy_review.py",
            "negative_reason": "winner_JRC_policy_review_is_not_the_sidewall_mainline",
            "allowed_use": "prove_winner_JRC_fields_remain_non_primary_or_false",
            "blocked_use": "drive_dimension_annulus_or_interference_work",
        },
        {
            "negative_context_id": "NEGATIVE-CONTEXT-002",
            "source_path": "tools/audits/build_nodi_package_c_sidewall_simulation_candidate_dual_track_lock.py",
            "negative_reason": "simulation_candidate_dual_track_is_route_ranking_semantics",
            "allowed_use": "reuse_dual_track_pattern_only",
            "blocked_use": "inherit_route_ranking_as_primary_question",
        },
        {
            "negative_context_id": "NEGATIVE-CONTEXT-003",
            "source_path": "nodi_simulator/wet_optical_detection_evidence.py",
            "negative_reason": "wet_optical_detection_context_is_not_sidewall_specific_delta",
            "allowed_use": "historical_context_or_input_caveat",
            "blocked_use": "promote_to_sidewall_detection_probability",
        },
    ]


def forbidden_field_rows() -> list[dict[str, Any]]:
    fields = [
        ("winner", "use_delta_status_or_annulus_remap_status"),
        ("route_score", "use_axis_specific_delta_fields"),
        ("rank", "use_dimension_family_stability_band"),
        ("ranking", "use_recommendation_shift_candidate"),
        ("JRC", "use_ledger_context_status"),
        ("yield", "use_tail_particle_support_delta_or_wet_surface_context"),
        ("detection_probability", "use_interference_enhancement_delta_map"),
        ("wet_pass_probability", "use_wet_surface_assumption_context"),
        ("experimental_data_waiting", "use_extreme_simulation_source_gap"),
        ("route_score_norm", "use_axis_specific_delta_fields"),
        ("rank_under_surrogate", "use_sensitivity_sort_index_only_if_non_primary"),
        ("sidewall_score_value", "use_sidewall_geometry_sensitivity_delta"),
    ]
    return [
        {
            "forbidden_field_id": f"FORBIDDEN-FIELD-{index:03d}",
            "forbidden_field_or_alias": field,
            "allowed_replacement": replacement,
            "hard_fail_if_primary_output": True,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (field, replacement) in enumerate(fields, start=1)
    ]


def alignment_check_rows(
    axes: list[dict[str, Any]],
    packages: list[dict[str, Any]],
    guards: list[dict[str, Any]],
    source_hints: list[dict[str, Any]],
    negative_contexts: list[dict[str, Any]],
    forbidden_fields: list[dict[str, Any]],
    source_lock: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        (
            "three_axes_present",
            {row["axis_name"] for row in axes}
            == {
                "dimension_recommendation_sensitivity",
                "selected_annulus_sidewall_remap",
                "interference_enhancement_sidewall_sensitivity",
            },
            str(len(axes)),
        ),
        (
            "all_packages_map_to_refocused_axes",
            len(packages) == 4
            and all(row["depends_on_axis"].startswith("AXIS-") for row in packages),
            str(len(packages)),
        ),
        (
            "route_winner_not_primary",
            all("winner" not in row["axis_name"] for row in axes)
            and any("which_route_wins_or_loses" == row["forbidden_primary_frame"] for row in guards),
            "winner/ranking is a drift guard, not the route",
        ),
        (
            "simulation_not_experimental_waiting",
            any(
                row["replacement_frame"]
                == "extreme_simulation_from_NODI_COMSOL_assumptions"
                for row in guards
            ),
            "simulation assumptions are the active source",
        ),
        (
            "rectangle_and_trapezoid_coexist",
            any(
                row["replacement_frame"]
                == "rectangle_baseline_and_sidewall_geometry_coexist"
                for row in guards
            ),
            "ideal rectangle remains baseline",
        ),
        (
            "source_lock_complete",
            all(row["exists"] == "true" for row in source_lock),
            str(len(source_lock)),
        ),
        (
            "source_hints_cover_annulus_response_and_ledger",
            len(source_hints) >= 5
            and {"AXIS-002", "AXIS-003"}.issubset(
                {
                    axis
                    for row in source_hints
                    for axis in row["preferred_axis"].split(";")
                }
            ),
            str(len(source_hints)),
        ),
        (
            "negative_context_sources_registered",
            len(negative_contexts) >= 3
            and any("winner_JRC" in row["negative_reason"] for row in negative_contexts),
            str(len(negative_contexts)),
        ),
        (
            "forbidden_fields_include_aliases",
            {"route_score_norm", "rank_under_surrogate", "sidewall_score_value"}.issubset(
                {row["forbidden_field_or_alias"] for row in forbidden_fields}
            ),
            str(len(forbidden_fields)),
        ),
        (
            "qch_is_transport_input_only",
            any(
                row["replacement_frame"] == "formal_qch_transport_input_only"
                for row in guards
            ),
            "formal q_ch cannot become recommendation score",
        ),
        (
            "small_n_smoke_is_context_only",
            any(
                row["replacement_frame"] == "small_n_smoke_context_only_until_full_matrix"
                for row in guards
            ),
            "small-n smoke cannot change recommendation",
        ),
    ]
    return [
        {
            "check_id": f"MAINLINE-REFOCUS-CHECK-{index:03d}",
            "check_name": name,
            "check_pass": bool(passed),
            "check_detail": detail,
            "hard_fail_if_false": True,
        }
        for index, (name, passed, detail) in enumerate(checks, start=1)
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "mainline_axis_rows": payload["mainline_axis_rows"],
                "work_package_rows": payload["work_package_rows"],
                "drift_guard_rows": payload["drift_guard_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    axes = mainline_axis_rows()
    packages = work_package_rows()
    guards = drift_guard_rows()
    source_hints = source_hint_rows()
    negative_contexts = negative_context_rows()
    forbidden_fields = forbidden_field_rows()
    source_lock = source_lock_rows()
    checks = alignment_check_rows(
        axes, packages, guards, source_hints, negative_contexts, forbidden_fields, source_lock
    )
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    failed_checks = sum(not row["check_pass"] for row in checks)
    v4_upper = load_summary(SOURCE_FILES["comsol_v4_upper_alignment_status"])
    v4_extension = load_summary(SOURCE_FILES["comsol_v4_alignment_extension_status"])
    disposition = DISPOSITION
    if source_missing or failed_checks:
        disposition = BLOCKED_DISPOSITION
    summary = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "v4_upper_alignment_disposition": v4_upper.get("disposition", ""),
        "v4_extension_disposition": v4_extension.get("disposition", ""),
        "mainline_axis_rows": len(axes),
        "work_package_rows": len(packages),
        "drift_guard_rows": len(guards),
        "source_hint_rows": len(source_hints),
        "negative_context_rows": len(negative_contexts),
        "forbidden_field_rows": len(forbidden_fields),
        "alignment_check_rows": len(checks),
        "failed_alignment_check_rows": failed_checks,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_mainline_refocus_dirty_context_rows": sum(
            row["classification"] == "non_mainline_refocus_dirty_context"
            for row in dirty_context
        ),
        "primary_mainline": (
            "sidewall_angle_effect_on_recommended_dimensions_selected_annulus_and_"
            "interference_enhancement"
        ),
        "not_primary_mainline": "route_winner_or_scoreboard",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_high_leverage_step": (
            "build dimension recommendation drift matrix, selected-annulus remap, "
            "and interference-enhancement sensitivity artifacts as one coherent block"
        ),
    }
    payload = {
        "summary": summary,
        "mainline_axis_rows": axes,
        "work_package_rows": packages,
        "drift_guard_rows": guards,
        "source_hint_rows": source_hints,
        "negative_context_rows": negative_contexts,
        "forbidden_field_rows": forbidden_fields,
        "alignment_check_rows": checks,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append("mainline_refocus_not_ready")
    if summary["mainline_axis_rows"] != 3:
        failures.append("expected_three_mainline_axes")
    if summary["work_package_rows"] != 4:
        failures.append("expected_four_work_packages")
    if summary["source_hint_rows"] < 5:
        failures.append("source_hints_incomplete")
    if summary["negative_context_rows"] < 3:
        failures.append("negative_contexts_incomplete")
    if summary["forbidden_field_rows"] < 12:
        failures.append("forbidden_fields_incomplete")
    if summary["failed_alignment_check_rows"] != 0:
        failures.append("failed_alignment_checks_present")
    if summary["source_missing_rows"] != 0:
        failures.append("source_missing")
    if summary["not_primary_mainline"] != "route_winner_or_scoreboard":
        failures.append("route_winner_not_demoted")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "mainline_axes": OUTPUT_DIR / f"{PREFIX}_AXIS_ROWS_{DATE_STAMP}.csv",
        "work_packages": OUTPUT_DIR / f"{PREFIX}_WORK_PACKAGE_ROWS_{DATE_STAMP}.csv",
        "drift_guards": OUTPUT_DIR / f"{PREFIX}_DRIFT_GUARD_ROWS_{DATE_STAMP}.csv",
        "source_hints": OUTPUT_DIR / f"{PREFIX}_SOURCE_HINT_ROWS_{DATE_STAMP}.csv",
        "negative_contexts": OUTPUT_DIR
        / f"{PREFIX}_NEGATIVE_CONTEXT_ROWS_{DATE_STAMP}.csv",
        "forbidden_fields": OUTPUT_DIR
        / f"{PREFIX}_FORBIDDEN_FIELD_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR
        / f"{PREFIX}_ALIGNMENT_CHECK_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "master_report": REPORT_DIR / f"588_{PREFIX}_{DATE_STAMP}.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
    }
    write_json_atomic(
        outputs["status"],
        {
            "disposition": payload["summary"]["disposition"],
            "summary": payload["summary"],
        },
        sort_keys=True,
    )
    write_csv_rows(outputs["mainline_axes"], payload["mainline_axis_rows"])
    write_csv_rows(outputs["work_packages"], payload["work_package_rows"])
    write_csv_rows(outputs["drift_guards"], payload["drift_guard_rows"])
    write_csv_rows(outputs["source_hints"], payload["source_hint_rows"])
    write_csv_rows(outputs["negative_contexts"], payload["negative_context_rows"])
    write_csv_rows(outputs["forbidden_fields"], payload["forbidden_field_rows"])
    write_csv_rows(outputs["alignment_checks"], payload["alignment_check_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256
            if artifact_id == "manifest"
            else sha256_file(path),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for artifact_id, path in outputs.items()
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Sidewall Mainline Refocus Lock",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Primary mainline: `{s['primary_mainline']}`.",
            f"Not primary mainline: `{s['not_primary_mainline']}`.",
            f"Source hint rows: `{s['source_hint_rows']}`.",
            f"Negative context rows: `{s['negative_context_rows']}`.",
            f"Forbidden field rows: `{s['forbidden_field_rows']}`.",
            "",
            "The sidewall-angle mainline is now locked to three questions:",
            "",
            "1. Does sidewall angle change the recommended NODI channel dimensions?",
            "2. Does sidewall angle change the selected-annulus range or coordinate basis?",
            "3. Does sidewall angle change interference-enhancement or response maps?",
            "",
            "Route winner/ranking may appear only as a downstream diagnostic, not as "
            "the driver of this lane.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_mainline_refocus_lock:
        raise SystemExit("--confirm-sidewall-mainline-refocus-lock is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
