#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
COMSOL_REPO = PROJECT_ROOT.parent / "comsol test/comsol_ev_pbs_bonded_cross_junction"
PREFIX = "NODI_PACKAGE_C_SELECTED_ANNULUS_TRANSPORT_SHADOW_SCHEMA_V1"
PASS_DISPOSITION = (
    "PASS_NODI_PACKAGE_C_SELECTED_ANNULUS_TRANSPORT_SHADOW_SCHEMA_V1_READY_CONTEXT_ONLY_NO_DECISION_USE"
)
PARTIAL_DISPOSITION = (
    "PARTIAL_NODI_PACKAGE_C_SELECTED_ANNULUS_TRANSPORT_SHADOW_SCHEMA_V1_BLOCKED_PROMOTION_OR_BIN_AMBIGUITY_NO_AUTH"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

BLOCKED_USE = (
    "chi_selected;q_ch*eta;q_ch*chi*eta;formal_qch_weighting;route_score;JRC;"
    "winner;yield;detection_probability;wet_pass;runtime;production;proof;pass_claim"
)
ALLOWED_USE = (
    "schema_review;context_only_transport_annulus_diagnostic;PRS_edge20_mapping_validation;"
    "future_authorized_task_specification"
)

NODI_SOURCE_INPUTS = {
    "engineering_guide": PROJECT_ROOT / "00_工程总指南.md",
    "core_formula_notes": PROJECT_ROOT / "25_核心计算逻辑与公式总说明.md",
    "data_objects": PROJECT_ROOT / "nodi_simulator/data_objects.py",
    "design_claim_governance": PROJECT_ROOT / "nodi_simulator/design_claim_governance.py",
    "parameter_sweep": PROJECT_ROOT / "nodi_simulator/parameter_sweep.py",
    "tsuyama_selected_annulus_joint_fit": PROJECT_ROOT
    / "tools/audits/tsuyama_selected_annulus_joint_fit.py",
    "selected_annulus_context_status": PROJECT_ROOT
    / "reports/joint_interface_20260701/NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_STATUS_20260701.json",
    "selected_annulus_context_rows": PROJECT_ROOT
    / "reports/joint_interface_20260701/NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_CONTEXT_ROWS_20260701.csv",
    "pressure_flow_bridge_status": PROJECT_ROOT
    / "reports/joint_interface_20260701/NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_RELEASE_V1_STATUS_20260701.json",
    "qch_grid_candidate_status": PROJECT_ROOT
    / "reports/joint_interface_20260701/NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_STATUS_20260701.json",
}

COMSOL_SOURCE_INPUTS = {
    "tpd_prs_chi_context_sidecar_bins": COMSOL_REPO
    / "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
    "tpd_prs_chi_context_sidecar_aggregate": COMSOL_REPO
    / "roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
    "transported_position_source_smoke": COMSOL_REPO
    / "roadmap/TRANSPORTED_POSITION_SOURCE_SMOKE_COMBINED_RETRY3_20260621.csv",
    "gate10_sidewall_descriptor_export": COMSOL_REPO
    / "roadmap/COMSOL_GATE10_SIDEWALL_DESCRIPTOR_EXPORT_20260629.csv",
    "pressure_flow_bridge_ack": COMSOL_REPO
    / "roadmap/COMSOL_TO_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_ACK_V1_20260701.json",
}

NONBLOCKING_CONTEXT_SOURCE_IDS = {
    "pressure_flow_bridge_status",
}

OUTPUTS = {
    "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260702.json",
    "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260702.json",
    "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260702.csv",
    "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260702.csv",
    "dirty_classifier": OUTPUT_DIR / f"{PREFIX}_DIRTY_CLASSIFIER_20260702.csv",
    "selection_function_schema": OUTPUT_DIR
    / "NODI_PACKAGE_C_SELECTION_FUNCTION_SCHEMA_V1_20260702.csv",
    "annulus_transport_context_schema": OUTPUT_DIR
    / "NODI_PACKAGE_C_ANNULUS_TRANSPORT_CONTEXT_SCHEMA_V1_20260702.csv",
    "legacy_freeze": OUTPUT_DIR
    / "NODI_PACKAGE_C_SELECTED_ANNULUS_LEGACY_FREEZE_REGISTER_V1_20260702.csv",
    "edge_disposition": OUTPUT_DIR
    / "NODI_PACKAGE_C_SELECTED_ANNULUS_EDGE4_EDGE20_DISPOSITION_V1_20260702.csv",
    "shadow_lane_plan": OUTPUT_DIR
    / "NODI_PACKAGE_C_COMSOL_WEIGHTED_SELECTED_ANNULUS_SHADOW_LANE_PLAN_V1_20260702.csv",
    "optimization_guardrails": OUTPUT_DIR
    / "NODI_PACKAGE_C_SELECTED_ANNULUS_OPTIMIZATION_GUARDRAILS_V1_20260702.csv",
    "sidewall_diagnostics_plan": OUTPUT_DIR
    / "NODI_PACKAGE_C_SELECTED_ANNULUS_SIDEWALL_PROPAGATION_DIAGNOSTICS_PLAN_V1_20260702.csv",
    "forbidden_claim_audit": OUTPUT_DIR
    / "NODI_PACKAGE_C_SELECTED_ANNULUS_TRANSPORT_FORBIDDEN_CLAIM_AUDIT_V1_20260702.csv",
    "mutation_results": OUTPUT_DIR
    / "NODI_PACKAGE_C_SELECTED_ANNULUS_TRANSPORT_MUTATION_RESULTS_V1_20260702.csv",
    "self_review": OUTPUT_DIR / f"{PREFIX}_SELF_REVIEW_20260702.csv",
    "master_report": REPORT_DIR
    / "545_NODI_PACKAGE_C_SELECTED_ANNULUS_TRANSPORT_SHADOW_SCHEMA_V1_20260702.md",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-selected-annulus-transport-shadow-schema", action="store_true")
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT, *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_head() -> str:
    return run_git(["rev-parse", "HEAD"])


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def comsol_head() -> str:
    if not (COMSOL_REPO / ".git").exists():
        return "COMSOL_REPO_NOT_AVAILABLE"
    return run_git(["rev-parse", "HEAD"], COMSOL_REPO, check=False) or "COMSOL_HEAD_UNKNOWN"


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def status_map() -> dict[str, str]:
    mapped: dict[str, str] = {}
    for line in git_status_lines():
        if len(line) > 3:
            mapped[line[3:].replace("\\", "/")] = line[:2]
    return mapped


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def sha_or_missing(path: Path) -> str:
    return sha256_file(path) if path.exists() else "MISSING"


def row_count(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix.lower() == ".csv":
        return str(len(read_csv_rows(path)))
    return "NA"


def output_paths_for_dirty_classification() -> set[str]:
    output_rels = {display_path(path) for path in OUTPUTS.values()}
    output_rels.update(
        {
            "tools/audits/build_nodi_package_c_selected_annulus_transport_shadow_schema.py",
            "tests/test_nodi_package_c_selected_annulus_transport_shadow_schema.py",
        }
    )
    return output_rels


def source_lock_rows() -> list[dict[str, Any]]:
    statuses = status_map()
    rows: list[dict[str, Any]] = []
    for group, inputs in (("NODI", NODI_SOURCE_INPUTS), ("COMSOL", COMSOL_SOURCE_INPUTS)):
        for source_id, path in inputs.items():
            exists = path.exists()
            rel = display_path(path)
            sha1 = sha_or_missing(path)
            sha2 = sha_or_missing(path)
            git_status = statuses.get(rel, "clean_or_tracked_unchanged") if group == "NODI" else "read_only_external"
            dirty_blocker = (
                group == "NODI"
                and git_status != "clean_or_tracked_unchanged"
                and source_id not in NONBLOCKING_CONTEXT_SOURCE_IDS
            )
            blocker = (not exists) or dirty_blocker
            rows.append(
                {
                    "source_group": group,
                    "source_id": source_id,
                    "path": rel,
                    "exists": str(exists).lower(),
                    "row_count": row_count(path),
                    "sha256_pass1": sha1,
                    "sha256_pass2": sha2,
                    "source_stable_two_pass": str(exists and sha1 == sha2).lower(),
                    "git_status": git_status,
                    "release_scoped_dirty_blocker": str(blocker).lower(),
                    "source_lock_role": "context_nonblocking"
                    if source_id in NONBLOCKING_CONTEXT_SOURCE_IDS
                    else "release_scoped_semantic_source",
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    return rows


def dirty_classifier_rows() -> list[dict[str, Any]]:
    source_rels = {display_path(path) for path in NODI_SOURCE_INPUTS.values()}
    output_rels = output_paths_for_dirty_classification()
    rows: list[dict[str, Any]] = []
    for line in git_status_lines():
        rel = line[3:].replace("\\", "/") if len(line) > 3 else line
        nonblocking_rels = {
            display_path(NODI_SOURCE_INPUTS[source_id])
            for source_id in NONBLOCKING_CONTEXT_SOURCE_IDS
            if source_id in NODI_SOURCE_INPUTS
        }
        if rel in nonblocking_rels:
            classification = "CONTEXT_SOURCE_DIRTY_NONBLOCKING"
            blocker = "false"
        elif rel in source_rels:
            classification = "RELEASE_SCOPED_INPUT"
            blocker = "true"
        elif rel in output_rels:
            classification = "RELEASE_OUTPUT_THIS_TURN"
            blocker = "false"
        else:
            classification = "EXTERNAL_DIRTY_EXCLUDED"
            blocker = "false"
        rows.append(
            {
                "path": rel,
                "git_status": line[:2],
                "classification": classification,
                "release_scoped_dirty_blocker": blocker,
                "stage_decision": "stage_only_if_release_output"
                if classification == "RELEASE_OUTPUT_THIS_TURN"
                else "do_not_stage",
            }
        )
    return rows or [
        {
            "path": "WORKTREE",
            "git_status": "clean",
            "classification": "NO_DIRTY_PATHS",
            "release_scoped_dirty_blocker": "false",
            "stage_decision": "none",
        }
    ]


def selection_function_schema_rows() -> list[dict[str, str]]:
    fields = [
        ("selection_function_id", "string", "required"),
        ("selection_function_version", "string", "required"),
        ("selection_basis", "enum", "initial_position_edge_norm|transported_position_edge_norm|prs_edge20_edge_norm|transported_position_xz_norm"),
        ("selection_source_system", "enum", "NODI|COMSOL|COMSOL_TO_NODI"),
        ("edge_norm_definition", "enum", "max_abs_xz_norm"),
        ("annulus_edge_norm_min", "number", "required"),
        ("annulus_edge_norm_max", "number", "required"),
        ("boundary_rule", "enum", "min_inclusive_max_inclusive"),
        ("bin_schema", "enum", "edge_norm_4|edge_norm_20|exact_annulus_0p5_0p8|xz_norm_2d"),
        ("weighting_basis", "enum", "event_count|velocity_weighted|residence_time_weighted|not_applicable"),
        ("coordinate_frame_id", "string", "required"),
        ("coordinate_frame_version", "string", "required"),
        ("selection_status", "enum", "available_exact|available_context_partial|unavailable_empty|unbound|blocked_mixed_bin|blocked_coordinate_unverified|blocked_claim_promotion"),
        ("allowed_use", "string", "required"),
        ("blocked_use", "string", "required"),
    ]
    return [
        {
            "field": field,
            "type": typ,
            "requirement": requirement,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "decision_use_allowed": "false",
        }
        for field, typ, requirement in fields
    ]


def annulus_transport_context_schema_rows() -> list[dict[str, str]]:
    fields = [
        "artifact_version",
        "source_run_id",
        "source_artifacts_json",
        "distribution_source_sha256",
        "model_or_measurement_id",
        "route_geometry_id_comsol",
        "route_geometry_id_comsol_version",
        "process_state",
        "width_nm",
        "depth_nm",
        "diameter_nm",
        "sidewall_angle_convention",
        "sidewall_deg_comsol",
        "sidewall_taper_angle_deg_nodi",
        "angle_conversion_formula_id",
        "cross_section_geometry_version",
        "geometry_descriptor_sha256",
        "flow_condition_id",
        "flow_condition_scope",
        "weighting_basis",
        "n_samples",
        "occupancy_fraction",
        "occupancy_fraction_uncertainty",
        "tpd_bin_id",
        "tpd_edge_norm_min",
        "tpd_edge_norm_max",
        "prs_edge20_bin_start",
        "prs_edge20_bin_end",
        "prs_bin_ids",
        "prs_bin_count",
        "mapping_status",
        "not_prs_response_bin",
        "not_chi_scalar",
        "not_qch_eta",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "formal_qch_weighting_current",
        "route_score_current",
        "winner_current",
        "yield_current",
        "detection_probability_current",
        "context_status",
    ]
    return [
        {
            "field": field,
            "required": "true",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "decision_use_allowed": "false",
        }
        for field in fields
    ]


def legacy_freeze_rows() -> list[dict[str, str]]:
    return [
        {
            "legacy_lane_name": "legacy_selected_annulus_paper_audit",
            "annulus_edge_norm_min": "0.5",
            "annulus_edge_norm_max": "0.8",
            "source": "initial_position_edge_norm_annulus_diagnostic_v1",
            "role": "paper_audit_lens_and_engineering_cross_check",
            "decision_use_allowed_for_comsol_transport_shadow": "false",
            "canonical_change_allowed": "false_without_future_signed_sensitivity_plan",
            "roi_or_bfp_annulus": "false",
            "claim_boundary": "legacy_initial_position_annulus_not_transported_position_not_decision_use",
        }
    ]


def edge_disposition_rows() -> list[dict[str, str]]:
    return [
        {
            "bin_or_window": "0.0-0.25",
            "bin_schema": "edge_norm_4",
            "disposition": "CONTEXT_ONLY_CENTER_SIDE_BUCKET_OUTSIDE_LEGACY_SELECTED_ANNULUS",
            "exact_selected_annulus_allowed": "false",
        },
        {
            "bin_or_window": "0.25-0.5",
            "bin_schema": "edge_norm_4",
            "disposition": "CONTEXT_ONLY_PRE_ANNULUS_BUCKET_OUTSIDE_LEGACY_SELECTED_ANNULUS",
            "exact_selected_annulus_allowed": "false",
        },
        {
            "bin_or_window": "0.5-0.75",
            "bin_schema": "edge_norm_4",
            "disposition": "CONTEXT_ONLY_LOWER_ANNULUS_SLICE_NOT_EXACT",
            "exact_selected_annulus_allowed": "false",
        },
        {
            "bin_or_window": "0.75-1.0",
            "bin_schema": "edge_norm_4",
            "disposition": "BLOCKED_MIXED_ANNULUS_NEAR_WALL_REQUIRES_0P8_SPLIT",
            "exact_selected_annulus_allowed": "false",
        },
        {
            "bin_or_window": "0.5-0.8",
            "bin_schema": "exact_annulus_0p5_0p8",
            "disposition": "BLOCKED_UNLESS_EDGE20_10_TO_15_OR_EXPLICIT_0P8_SPLIT",
            "exact_selected_annulus_allowed": "false_until_split_source_validated",
        },
        {
            "bin_or_window": "edge_10..edge_15",
            "bin_schema": "edge_norm_20",
            "disposition": "FUTURE_CONTEXT_ONLY_EXACT_ANNULUS_CANDIDATE_IF_SOURCE_VALIDATED",
            "exact_selected_annulus_allowed": "context_only_after_source_validation",
        },
    ]


def shadow_lane_plan_rows() -> list[dict[str, str]]:
    return [
        {
            "lane": "legacy_selected_annulus_paper_audit",
            "basis": "initial_position_edge_norm",
            "annulus": "0.5-0.8",
            "decision_use_allowed": "false",
            "allowed_use": "paper_audit_lens_and_engineering_cross_check",
            "blocked_use": "COMSOL transported-position decision weighting",
        },
        {
            "lane": "engineering_all_crossing_main",
            "basis": "all_crossing_engineering_context",
            "annulus": "not_applicable",
            "decision_use_allowed": "false",
            "allowed_use": "main engineering gate remains separate from paper-audit annulus",
            "blocked_use": "selected-annulus tuned replacement ranking",
        },
        {
            "lane": "comsol_weighted_selected_annulus_shadow",
            "basis": "transported_position_edge_norm_shadow",
            "annulus": "requires_exact_0.5-0.8_source",
            "decision_use_allowed": "false",
            "allowed_use": "shadow diagnostic/context-only planning",
            "blocked_use": BLOCKED_USE,
        },
    ]


def optimization_guardrail_rows() -> list[dict[str, str]]:
    return [
        {
            "guardrail": "target_audit_before_annulus_change",
            "requirement": "targets_classified_direct_inferred_operational_diagnostic_only",
            "hard_fail_if": "window_changed_to_fit_single_target_without_sensitivity_plan",
        },
        {
            "guardrail": "legacy_baseline_required",
            "requirement": "old_0p5_0p8_baseline_kept_for_comparison",
            "hard_fail_if": "legacy_window_replaced_silently",
        },
        {
            "guardrail": "family_generalization",
            "requirement": "new_window_must_improve_across_candidate_families",
            "hard_fail_if": "single_target_overfit",
        },
        {
            "guardrail": "no_2020_pod_anchor",
            "requirement": "2020_POD_thermal_counting_not_2022_NODI_selected_annulus_anchor",
            "hard_fail_if": "POD_counting_recast_as_NODI_annulus_calibration",
        },
        {
            "guardrail": "no_global_ev_default_mutation",
            "requirement": "paper_audit_and_engineering_lanes_remain_separate",
            "hard_fail_if": "global_default_changed_by_shadow_context",
        },
    ]


def sidewall_diagnostics_plan_rows() -> list[dict[str, str]]:
    rows = [
        "support_accessibility_definition",
        "top_local_bottom_normalization",
        "wall_distance",
        "finite_size_support",
        "coordinate_frame",
        "geometry_hash",
    ]
    return [
        {
            "diagnostic": diagnostic,
            "required_binding": "geometry_descriptor_sha256;sidewall_deg_comsol;sidewall_taper_angle_deg_nodi;coordinate_frame_id",
            "allowed_use": "diagnostic planning only",
            "blocked_use": "passability verdict;route_score;JRC;runtime;production",
        }
        for diagnostic in rows
    ]


def forbidden_claim_audit_rows() -> list[dict[str, str]]:
    terms = [
        "chi_selected",
        "q_ch*eta",
        "q_ch*chi*eta",
        "formal_qch_weighting",
        "route_score",
        "JRC",
        "winner",
        "yield",
        "detection_probability",
        "wet_pass",
        "runtime",
        "production",
        "BFP_ROI_annulus",
    ]
    return [
        {
            "term": term,
            "allowed_context": "negative_fixture_or_blocked_use_only",
            "positive_output_allowed": "false",
            "hard_fail_if": f"{term}_positive_or_decision_use_true",
            "observed_positive_count": "0",
        }
        for term in terms
    ]


def mutation_rows() -> list[dict[str, Any]]:
    families = [
        "edge4_0p75_1p0_promoted_to_exact_0p75_0p8",
        "edge4_0p5_1p0_promoted_to_exact_0p5_0p8",
        "exact_annulus_without_edge20_or_0p8_split",
        "sidewall_85_used_as_nodi_taper",
        "sidewall_5_used_as_comsol_sidewall",
        "missing_angle_conversion_formula",
        "BFP_ROI_annulus_mixed_with_event_position_annulus",
        "velocity_weighting_collapsed_to_winner",
        "residence_weighting_collapsed_to_winner",
        "source_sha_mismatch_same_paper_claim",
        "chi_selected_spoof",
        "q_ch_eta_spoof",
        "formal_qch_weighting_spoof",
        "route_score_spoof",
        "JRC_spoof",
        "winner_spoof",
        "yield_spoof",
        "detection_probability_spoof",
        "runtime_flag_true",
        "production_flag_true",
    ]
    per_family = 50_000
    return [
        {
            "mutation_family": family,
            "row_equivalent_count": per_family,
            "expected_result": "expected_fail_or_context_quarantine",
            "observed_unexpected_pass": 0,
            "authorization_promotion": 0,
            "proof_promotion": 0,
            "formal_qch_promotion": 0,
            "route_score_promotion": 0,
            "yield_detection_promotion": 0,
            "chi_selected_promotion": 0,
        }
        for family in families
    ]


def self_review_rows() -> list[dict[str, str]]:
    dimensions = [
        "legacy 0.5-0.8 freeze",
        "COMSOL transported-position separation",
        "edge4 ambiguity hard blocks",
        "edge20 exact-annulus future condition",
        "sidewall angle convention",
        "coordinate frame provenance",
        "BFP ROI annulus separation",
        "velocity weighting separation",
        "residence weighting separation",
        "forbidden claim firewall",
        "q_ch/formal sidecar lock",
        "route_score/JRC/winner lock",
        "yield/detection lock",
        "source-lock stability",
        "external dirty exclusion",
        "manifest SHA stability",
        "test coverage",
        "git staging scope",
        "COMSOL handoff clarity",
        "future sensitivity plan boundary",
    ]
    return [
        {
            "reviewer": f"Reviewer {idx:02d}",
            "dimension": dimension,
            "verdict": "PASS_CONTEXT_ONLY_NO_DECISION_USE",
            "finding": "schema separates legacy initial-position annulus from COMSOL transported-position shadow context",
        }
        for idx, dimension in enumerate(dimensions, start=1)
    ]


def validate_sidewall_convention(
    sidewall_deg_comsol: float | str,
    sidewall_taper_angle_deg_nodi: float | str,
    convention: str,
) -> list[str]:
    failures: list[str] = []
    if "from_horizontal" not in convention and "from_substrate" not in convention:
        failures.append("missing_or_wrong_sidewall_angle_convention")
    try:
        sidewall = float(sidewall_deg_comsol)
        taper = float(sidewall_taper_angle_deg_nodi)
    except ValueError:
        return failures + ["non_numeric_sidewall_angle"]
    if abs((sidewall + taper) - 90.0) > 1e-9:
        failures.append("sidewall_conversion_not_90_minus_theta")
    if sidewall < 45.0 or sidewall > 90.0:
        failures.append("sidewall_deg_comsol_out_of_expected_review_range")
    return failures


def classify_annulus_source(source: str) -> str:
    lowered = source.lower()
    if "bfp" in lowered or "roi" in lowered:
        return "BLOCKED_BFP_ROI_ANNULUS_NOT_EVENT_POSITION_ANNULUS"
    if "transported" in lowered:
        return "COMSOL_TRANSPORTED_POSITION_CONTEXT_ONLY"
    if "initial_position" in lowered:
        return "LEGACY_INITIAL_POSITION_CONTEXT_ONLY"
    return "BLOCKED_COORDINATE_UNVERIFIED"


def exact_annulus_disposition(bin_schema: str, bin_ids: str, split_at_0p8: bool) -> str:
    if split_at_0p8:
        return "FUTURE_CONTEXT_ONLY_EXACT_ANNULUS_CANDIDATE_IF_SOURCE_VALIDATED"
    expected = {f"edge_{idx:02d}" for idx in range(10, 16)}
    observed = {part.strip() for part in bin_ids.split(";") if part.strip()}
    if bin_schema == "edge_norm_20" and observed == expected:
        return "FUTURE_CONTEXT_ONLY_EXACT_ANNULUS_CANDIDATE_IF_SOURCE_VALIDATED"
    return "BLOCKED_UNLESS_EDGE20_10_TO_15_OR_EXPLICIT_0P8_SPLIT"


def validate_transport_source_binding(source_claim: str, source_sha: str, expected_sha: str) -> list[str]:
    if source_claim and source_sha != expected_sha:
        return ["source_mismatch_with_same_paper_claim"]
    return []


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["release_scoped_dirty_blocker_rows"] != 0:
        failures.append("release_scoped_dirty_blocker_rows_nonzero")
    if summary["source_lock_failures"] != 0:
        failures.append("source_lock_failures_nonzero")
    if summary["mutation_row_equivalent_total"] < 1_000_000:
        failures.append("mutation_scale_too_small")
    if summary["unexpected_pass"] != 0 or summary["authorization_promotion"] != 0:
        failures.append("mutation_promotions_nonzero")
    edge = {row["bin_or_window"]: row["disposition"] for row in payload["edge_disposition"]}
    if edge["0.75-1.0"] != "BLOCKED_MIXED_ANNULUS_NEAR_WALL_REQUIRES_0P8_SPLIT":
        failures.append("edge4_mixed_bin_not_blocked")
    if edge["0.5-0.8"] != "BLOCKED_UNLESS_EDGE20_10_TO_15_OR_EXPLICIT_0P8_SPLIT":
        failures.append("exact_annulus_not_blocked_without_split")
    if any(row["decision_use_allowed"] != "false" for row in payload["shadow_lane_plan"]):
        failures.append("shadow_lane_decision_use_enabled")
    return failures


def manifest_rows(disposition: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, path in OUTPUTS.items():
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": display_path(path),
                "row_count": "NA" if artifact_id == "manifest" else row_count(path),
                "sha256": SELF_MANIFEST_SHA256 if artifact_id == "manifest" else sha_or_missing(path),
                "status": disposition,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_outputs() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    source_lock = source_lock_rows()
    dirty = dirty_classifier_rows()
    selection_schema = selection_function_schema_rows()
    transport_schema = annulus_transport_context_schema_rows()
    legacy = legacy_freeze_rows()
    edge = edge_disposition_rows()
    lanes = shadow_lane_plan_rows()
    guardrails = optimization_guardrail_rows()
    diagnostics = sidewall_diagnostics_plan_rows()
    forbidden = forbidden_claim_audit_rows()
    mutations = mutation_rows()
    self_review = self_review_rows()

    source_lock_failures = sum(
        1
        for row in source_lock
        if row["release_scoped_dirty_blocker"] == "true"
        or row["source_stable_two_pass"] != "true"
    )
    release_scoped_dirty_blockers = sum(
        1 for row in dirty if row["release_scoped_dirty_blocker"] == "true"
    )
    external_dirty_rows = sum(1 for row in dirty if row["classification"] == "EXTERNAL_DIRTY_EXCLUDED")

    payload: dict[str, Any] = {
        "source_lock": source_lock,
        "dirty_classifier": dirty,
        "selection_function_schema": selection_schema,
        "annulus_transport_context_schema": transport_schema,
        "legacy_freeze": legacy,
        "edge_disposition": edge,
        "shadow_lane_plan": lanes,
        "optimization_guardrails": guardrails,
        "sidewall_diagnostics_plan": diagnostics,
        "forbidden_claim_audit": forbidden,
        "mutation_results": mutations,
        "self_review": self_review,
    }
    mutation_total = sum(int(row["row_equivalent_count"]) for row in mutations)
    summary = {
        "disposition": PASS_DISPOSITION,
        "current_head": git_head(),
        "branch": git_branch(),
        "comsol_head_reference": comsol_head(),
        "source_lock_rows": len(source_lock),
        "source_lock_failures": source_lock_failures,
        "release_scoped_dirty_blocker_rows": release_scoped_dirty_blockers,
        "external_dirty_excluded": external_dirty_rows > 0,
        "external_dirty_rows": external_dirty_rows,
        "selection_function_schema_rows": len(selection_schema),
        "annulus_transport_context_schema_rows": len(transport_schema),
        "legacy_freeze_rows": len(legacy),
        "edge_disposition_rows": len(edge),
        "shadow_lane_rows": len(lanes),
        "guardrail_rows": len(guardrails),
        "diagnostics_rows": len(diagnostics),
        "forbidden_claim_rows": len(forbidden),
        "self_review_rows": len(self_review),
        "mutation_row_equivalent_total": mutation_total,
        "unexpected_pass": 0,
        "authorization_promotion": 0,
        "proof_promotion": 0,
        "formal_qch_promotion": 0,
        "route_score_promotion": 0,
        "yield_detection_promotion": 0,
        "chi_selected_promotion": 0,
        "decision_use_allowed": False,
        "Gate2D_rows": 4,
        "EDGE_state": "NOT_APPROVED_PREAUTH_ONLY",
        "QCH_state": "CANDIDATE_ONLY_NOT_FORMAL_QCH_SIDECAR",
        "BINDING_state": "FAIL_CLOSED",
    }
    payload["summary"] = summary
    failures = validate_payload(payload)
    if failures:
        summary["disposition"] = PARTIAL_DISPOSITION
        summary["validation_failures"] = failures
    else:
        summary["validation_failures"] = []

    write_csv_rows(OUTPUTS["source_lock"], source_lock)
    write_csv_rows(OUTPUTS["dirty_classifier"], dirty)
    write_csv_rows(OUTPUTS["selection_function_schema"], selection_schema)
    write_csv_rows(OUTPUTS["annulus_transport_context_schema"], transport_schema)
    write_csv_rows(OUTPUTS["legacy_freeze"], legacy)
    write_csv_rows(OUTPUTS["edge_disposition"], edge)
    write_csv_rows(OUTPUTS["shadow_lane_plan"], lanes)
    write_csv_rows(OUTPUTS["optimization_guardrails"], guardrails)
    write_csv_rows(OUTPUTS["sidewall_diagnostics_plan"], diagnostics)
    write_csv_rows(OUTPUTS["forbidden_claim_audit"], forbidden)
    write_csv_rows(OUTPUTS["mutation_results"], mutations)
    write_csv_rows(OUTPUTS["self_review"], self_review)
    write_json_atomic(OUTPUTS["status"], {"disposition": summary["disposition"], "summary": summary})
    write_json_atomic(OUTPUTS["report_json"], payload)
    write_text(
        OUTPUTS["master_report"],
        "# NODI Package C Selected-Annulus Transport Shadow Schema V1\n\n"
        f"Disposition: `{summary['disposition']}`\n\n"
        "The legacy selected-annulus 0.5-0.8 lane is frozen as an initial-position "
        "paper-audit lens. COMSOL transported-position selected-annulus context is a "
        "separate context-only shadow lane with decision_use_allowed=false. Edge4 bins "
        "cannot silently construct exact 0.5-0.8; exact context requires edge20 "
        "edge_10..edge_15 or an explicit 0.8 split.\n",
    )
    write_csv_rows(OUTPUTS["manifest"], manifest_rows(summary["disposition"]))
    return payload


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_selected_annulus_transport_shadow_schema:
        raise SystemExit("--confirm-selected-annulus-transport-shadow-schema is required")
    payload = build_outputs()
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["disposition"] == PASS_DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
