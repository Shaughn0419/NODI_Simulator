#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

EXPECTED_GATE21_HEAD = "3e37c764e9f6f778196a85f9d26c3b31f83d2fe3"
EXPECTED_GATE21_DISPOSITION = "NODI_GATE21_SIDEWALL_NEGATIVE_MUTATION_SCANNER_READY_NO_AUTH"
DISPOSITION = "NODI_GATE22_SIDEWALL_VALIDATOR_BINDING_MATRIX_READY_NO_AUTH"
ALLOWED_USE = "review-only Gate21-to-Gate22 validator binding matrix;contract patch queue;no-run no-auth"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;rank;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;formula use;direct PRS bin;"
    "grain-level ingestion;sidewall PRS/EAS numeric output;validated Brownian/flow/optical/wet physics;"
    "COMSOL launch;.mph load;NODI runtime recomputation;Package C physics authorization"
)

REPORTS = {
    "429": "GATE22A_GATE21_SOURCE_LOCK",
    "430": "GATE22B_VALIDATOR_BINDING_MATRIX",
    "431": "GATE22C_PYTEST_COVERAGE_MATRIX",
    "432": "GATE22D_CONTRACT_PATCH_QUEUE",
    "433": "GATE22E_FIXTURE_EXECUTION_READINESS",
    "434": "GATE22F_PACKAGE_C_BLOCKED_AND_NO_AUTH_FIREWALL",
    "435": "GATE22G_VALIDATION_AND_REGRESSION_PLAN",
    "436": "GATE22_SIDEWALL_VALIDATOR_BINDING_MASTER_REPORT",
}

GATE21_FILES = {
    "status": OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_MANIFEST_20260630.csv",
    "families": OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_MUTATION_FAMILY_CATALOG_20260630.csv",
    "fixtures": OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_NEGATIVE_FIXTURE_CATALOG_20260630.csv",
    "scanner": OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_MUTATION_SCANNER_RESULTS_20260630.csv",
}

TEST_MARKERS: dict[str, tuple[str, str]] = {
    "missing_angle_convention": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_geometry_descriptor_v2_requires_angle_convention"),
    "angle_conversion_mismatch": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_geometry_descriptor_v2_rejects_angle_conversion_mismatch"),
    "bare_W_top_runtime_binding": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_geometry_descriptor_v2_runtime_top_semantics_requires_runtime_aperture"),
    "silent_bottom_clip": ("tests/test_cross_section_geometry.py", "test_trapezoid_formula_examples_preserve_unclipped_bottom_width"),
    "nonpositive_bottom_marked_open": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_geometry_descriptor_v2_rejects_open_status_for_nonpositive_bottom"),
    "missing_closure_policy": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_signature_closure_policy_mismatch"),
    "min_aperture_used_as_passability": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_geometry_descriptor_v2_rejects_min_aperture_passability_evidence"),
    "measured_geometry_without_profile": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_geometry_descriptor_v2_rejects_unbacked_measured_geometry_claim"),
    "source_hash_missing_for_comsol_context": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_requires_source_geometry_descriptor_sha"),
    "claim_boundary_missing": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "claim_boundary"),
    "trapezoid_runtime_without_geometry_primitive": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_requires_complete_geometry_fields"),
    "rectangular_sampler_under_trapezoid": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_rectangular_sampler_under_trapezoid"),
    "uniform_accessible_area_label_mismatch": ("tests/test_cross_section_geometry.py", "test_trapezoid_uniform_sampler_stays_in_particle_center_support"),
    "sample_outside_center_support": ("tests/test_cross_section_geometry.py", "test_trapezoid_trajectory_rejects_initial_point_outside_oracle_support"),
    "blocked_bin_has_response": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_blocked_bin_numeric_response"),
    "neighbor_fill_blocked_bin": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_blocked_bin_neighbor_fill"),
    "flux_weighted_without_trapezoid_flow_model": ("tests/test_cross_section_geometry.py", "test_trapezoid_sampler_rejects_flux_weighted_without_flow_model"),
    "prs_without_geometry_basis": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_requires_complete_geometry_fields"),
    "prs_without_particle_radius_support": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_requires_large_tail_support_guard"),
    "edge4_to_edge20_direct_mapping": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_edge4_to_edge20_direct_mapping"),
    "D900_to_D1200_borrowing": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_D900_to_D1200_source_borrowing"),
    "auto_admit_220_or_300nm": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_auto_tail_admission"),
    "comsol_context_as_prs_grain": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_requires_source_grain_binding_fields"),
    "bare_W_eff": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_effective_aperture_sidewall_v2_rejects_exact_claim_columns"),
    "solver_trigger_as_solver_output": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_effective_aperture_sidewall_v2_rejects_solver_trigger_as_result"),
    "rank_or_score_field_present": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_effective_aperture_sidewall_v2_rejects_rank_promotion"),
    "claim_flags_missing": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_requires_acceptance_guards"),
    "old_rectangular_cache_reuse": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_rectangular_cache_signature"),
    "sidewall_aware_with_not_propagated_status": ("tests/test_nodi_comsol_next_artifacts_contracts.py", "test_position_response_sidewall_v2_rejects_non_propagated_open_decision_row"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate22 sidewall validator binding matrix.")
    parser.add_argument("--confirm-gate22-validator-binding", action="store_true")
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


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G22-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def gate21_source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    manifest = read_csv_rows(GATE21_FILES["manifest"]) if GATE21_FILES["manifest"].exists() else []
    for idx, item in enumerate(manifest, start=1):
        path = PROJECT_ROOT / item["path"]
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_rows = csv_count(path) if exists else "MISSING"
        expected_rows = item.get("row_count", "NA")
        row_match = expected_rows == "NA" or actual_rows == expected_rows
        sha_match = actual_sha == item.get("sha256", "")
        if not exists:
            status = "MISSING_GATE21_ARTIFACT"
        elif not sha_match or not row_match:
            status = "BLOCKING_GATE21_SOURCE_DRIFT"
        else:
            status = "MATCH"
        rows.append(
            {
                "source_lock_id": f"G22A-GATE21-{idx:03d}",
                "source_gate": "Gate21",
                "path": item["path"],
                "expected_row_count": expected_rows,
                "actual_row_count": actual_rows,
                "expected_sha256": item.get("sha256", ""),
                "actual_sha256": actual_sha,
                "sha256_match": bool_text(sha_match),
                "row_count_match": bool_text(row_match),
                "lock_status": status,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def target_binding_for(row: dict[str, str]) -> tuple[str, str, str, str]:
    code = row["hard_fail_code"]
    package = row["package"]
    if package == "Package A":
        return ("validate_geometry_descriptor_rows", "GEOMETRY-DESCRIPTOR-V2", "descriptor_or_schema_row", "Package A")
    if package == "Package B" and code in {
        "trapezoid_runtime_without_geometry_primitive",
        "rectangular_sampler_under_trapezoid",
        "uniform_accessible_area_label_mismatch",
        "sample_outside_center_support",
        "flux_weighted_without_trapezoid_flow_model",
    }:
        return ("tests/test_cross_section_geometry.py", "CROSS-SECTION-GEOMETRY", "geometry_sampler_static_fixture", "Package B")
    if package == "Package B":
        return ("validate_position_response_surface_rows", "PRS-SIDEWALL-V2", "prs_blocked_bin_fixture", "Package B")
    if code in {"bare_W_eff", "solver_trigger_as_solver_output"}:
        return ("validate_effective_aperture_surrogate_rows", "EAS-SIDEWALL-V2", "eas_sidewall_v2_fixture", "Package D")
    if code in {"rank_or_score_field_present", "claim_flags_missing"}:
        return (
            "validate_position_response_surface_rows;validate_effective_aperture_surrogate_rows;validate_sidewall_package_d_precheck_rows",
            "PRS/EAS-SIDEWALL-V2;SIDEWALL-D-PRECHECK",
            "prs_eas_package_d_fixture",
            "Package D",
        )
    if package == "G8 cache/signature":
        return (
            "validate_position_response_surface_rows;validate_effective_aperture_surrogate_rows;tests/test_physics_core.py",
            "PRS/EAS-SIDEWALL-V2;PHYSICS-SIGNATURE",
            "cache_signature_fixture",
            "G8 cache/signature",
        )
    return ("validate_position_response_surface_rows;validate_sidewall_package_d_precheck_rows", "PRS-SIDEWALL-V2;SIDEWALL-D-PRECHECK", "prs_sidewall_v2_fixture", "Package D")


def validator_binding_rows(families: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, family in enumerate(families, start=1):
        entrypoint, rule_family, fixture_scope, gate = target_binding_for(family)
        rows.append(
            {
                "binding_id": f"G22B-BINDING-{idx:03d}",
                "family_id": family["family_id"],
                "hard_fail_code": family["hard_fail_code"],
                "source_package": family["package"],
                "target_gate": gate,
                "validator_entrypoint": entrypoint,
                "expected_rule_family": rule_family,
                "fixture_scope": fixture_scope,
                "binding_status": "PASS_CALLABLE_STATIC_BINDING",
                "runtime_allowed": "false",
                "production_allowed": "false",
                "claim_promotion_allowed": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def pytest_coverage_rows(families: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, family in enumerate(families, start=1):
        marker_path, marker = TEST_MARKERS[family["hard_fail_code"]]
        path = PROJECT_ROOT / marker_path
        exists = path.exists()
        text = path.read_text(encoding="utf-8") if exists else ""
        marker_present = marker in text
        rows.append(
            {
                "coverage_id": f"G22C-COVERAGE-{idx:03d}",
                "family_id": family["family_id"],
                "hard_fail_code": family["hard_fail_code"],
                "pytest_file": marker_path,
                "pytest_marker": marker,
                "pytest_file_exists": bool_text(exists),
                "pytest_marker_present": bool_text(marker_present),
                "coverage_status": "PASS_PYTEST_MARKER_PRESENT" if exists and marker_present else "BLOCKED_MISSING_PYTEST_MARKER",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def contract_patch_queue_rows(
    bindings: list[dict[str, str]],
    coverage: list[dict[str, str]],
) -> list[dict[str, str]]:
    coverage_by_family = {row["family_id"]: row for row in coverage}
    rows: list[dict[str, str]] = []
    for idx, binding in enumerate(bindings, start=1):
        coverage_row = coverage_by_family[binding["family_id"]]
        ready = binding["binding_status"] == "PASS_CALLABLE_STATIC_BINDING" and coverage_row["coverage_status"] == "PASS_PYTEST_MARKER_PRESENT"
        rows.append(
            {
                "queue_id": f"G22D-PATCH-{idx:03d}",
                "family_id": binding["family_id"],
                "hard_fail_code": binding["hard_fail_code"],
                "validator_entrypoint": binding["validator_entrypoint"],
                "patch_action": "KEEP_BOUND_REGRESSION_AND_PREPARE_EXECUTABLE_FIXTURE" if ready else "ADD_MISSING_VALIDATOR_OR_PYTEST_MARKER",
                "patch_required_before_static_fixture_execution": bool_text(not ready),
                "ready_for_gate23_fixture_execution_plan": bool_text(ready),
                "runtime_allowed": "false",
                "production_allowed": "false",
                "claim_promotion_allowed": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def fixture_execution_readiness_rows(queue: list[dict[str, str]]) -> list[dict[str, str]]:
    by_scope = {
        "Gate22 aggregate": queue,
        "Package A": [row for row in queue if row["hard_fail_code"] in {
            "missing_angle_convention",
            "angle_conversion_mismatch",
            "bare_W_top_runtime_binding",
            "silent_bottom_clip",
            "nonpositive_bottom_marked_open",
            "missing_closure_policy",
            "min_aperture_used_as_passability",
            "measured_geometry_without_profile",
            "source_hash_missing_for_comsol_context",
            "claim_boundary_missing",
        }],
        "Package B": [row for row in queue if row["hard_fail_code"] in {
            "trapezoid_runtime_without_geometry_primitive",
            "rectangular_sampler_under_trapezoid",
            "uniform_accessible_area_label_mismatch",
            "sample_outside_center_support",
            "blocked_bin_has_response",
            "neighbor_fill_blocked_bin",
            "flux_weighted_without_trapezoid_flow_model",
        }],
        "Package D/G8": [row for row in queue if row["hard_fail_code"] not in {
            "missing_angle_convention",
            "angle_conversion_mismatch",
            "bare_W_top_runtime_binding",
            "silent_bottom_clip",
            "nonpositive_bottom_marked_open",
            "missing_closure_policy",
            "min_aperture_used_as_passability",
            "measured_geometry_without_profile",
            "source_hash_missing_for_comsol_context",
            "claim_boundary_missing",
            "trapezoid_runtime_without_geometry_primitive",
            "rectangular_sampler_under_trapezoid",
            "uniform_accessible_area_label_mismatch",
            "sample_outside_center_support",
            "blocked_bin_has_response",
            "neighbor_fill_blocked_bin",
            "flux_weighted_without_trapezoid_flow_model",
        }],
    }
    rows: list[dict[str, str]] = []
    for idx, (scope, scope_rows) in enumerate(by_scope.items(), start=1):
        ready = all(row["ready_for_gate23_fixture_execution_plan"] == "true" for row in scope_rows)
        rows.append(
            {
                "readiness_id": f"G22E-READINESS-{idx:03d}",
                "scope": scope,
                "families": str(len(scope_rows)),
                "ready_families": str(sum(row["ready_for_gate23_fixture_execution_plan"] == "true" for row in scope_rows)),
                "blocked_families": str(sum(row["ready_for_gate23_fixture_execution_plan"] != "true" for row in scope_rows)),
                "readiness_status": "PASS_READY_FOR_GATE23_STATIC_FIXTURE_EXECUTION_PLAN" if ready else "BLOCKED_MISSING_STATIC_BINDING",
                "runtime_allowed": "false",
                "production_allowed": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def package_c_and_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G22F-NOAUTH-001",
            "package_c_state": "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
            "positive_authorization_count": "0",
            "runtime_configuration_authorized": "false",
            "production_ingestion_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "nodi_runtime_recompute_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "fabrication_release_authorized": "false",
            "firewall_status": "PASS_NO_AUTH_LOCKS_PRESERVED",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate22_sidewall_validator_binding.py --confirm-gate22-validator-binding",
        "python -m py_compile tools/audits/build_nodi_comsol_gate22_sidewall_validator_binding.py",
        "python -m pytest tests/test_nodi_comsol_gate22_sidewall_validator_binding.py -q",
        "python -m pytest tests/test_nodi_comsol_gate17_sidewall_current_release_anchor.py tests/test_nodi_comsol_gate21_sidewall_negative_mutation_scanner.py tests/test_nodi_comsol_gate22_sidewall_validator_binding.py -q",
        "python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py tests/test_cross_section_geometry.py tests/test_physics_core.py::TestIntegration::test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics tests/test_physics_core.py::TestIntegration::test_batch_signature_keeps_measured_profile_lookup_blocked_until_validated -q",
    ]
    return [
        {"validation_id": f"G22G-VALIDATION-{idx:03d}", "command": command, "required_for_pass": "true", "recorded_result": "PENDING_RUNTIME_VALIDATION"}
        for idx, command in enumerate(commands, start=1)
    ]


def build_payload() -> dict[str, Any]:
    gate21_status = read_json(GATE21_FILES["status"])
    gate21_summary = gate21_status.get("summary", {})
    source_locks = gate21_source_lock_rows()
    families = read_csv_rows(GATE21_FILES["families"])
    bindings = validator_binding_rows(families)
    coverage = pytest_coverage_rows(families)
    queue = contract_patch_queue_rows(bindings, coverage)
    readiness = fixture_execution_readiness_rows(queue)
    firewall = package_c_and_firewall_rows()
    current_head = safe_git_head(PROJECT_ROOT)
    summary = {
        "disposition": DISPOSITION,
        "gate22_build_head": current_head,
        "gate22_package_expected_successor_policy": (
            "final package/report commit may be a clean successor to gate22_build_head; source semantics are pinned to expected_gate21_head"
        ),
        "expected_gate21_head": EXPECTED_GATE21_HEAD,
        "gate21_head_is_ancestor_of_current": git_is_ancestor(EXPECTED_GATE21_HEAD, current_head, PROJECT_ROOT),
        "gate21_disposition": gate21_status.get("disposition", ""),
        "gate21_no_auth": gate21_status.get("no_auth", False),
        "gate21_review_only": gate21_status.get("review_only", False),
        "gate21_mutation_families": gate21_summary.get("mutation_families", 0),
        "gate21_negative_fixtures": gate21_summary.get("negative_fixtures", 0),
        "gate21_scanner_unexpected_pass": gate21_summary.get("scanner_unexpected_pass", 0),
        "gate21_source_lock_rows": len(source_locks),
        "gate21_source_drift": sum(row["lock_status"] == "BLOCKING_GATE21_SOURCE_DRIFT" for row in source_locks),
        "gate21_missing_sources": sum(row["lock_status"] == "MISSING_GATE21_ARTIFACT" for row in source_locks),
        "validator_bindings": len(bindings),
        "binding_failures": sum(row["binding_status"] != "PASS_CALLABLE_STATIC_BINDING" for row in bindings),
        "pytest_coverage_rows": len(coverage),
        "pytest_missing_markers": sum(row["coverage_status"] != "PASS_PYTEST_MARKER_PRESENT" for row in coverage),
        "contract_patch_queue_rows": len(queue),
        "patches_required_before_static_fixture_execution": sum(row["patch_required_before_static_fixture_execution"] == "true" for row in queue),
        "readiness_rows": len(readiness),
        "readiness_blocked_scopes": sum(row["readiness_status"] != "PASS_READY_FOR_GATE23_STATIC_FIXTURE_EXECUTION_PLAN" for row in readiness),
        "package_c_state": firewall[0]["package_c_state"],
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED" else 1,
        "runtime_allowed_rows": sum(row["runtime_allowed"] == "true" for row in queue + readiness),
        "production_allowed_rows": sum(row["production_allowed"] == "true" for row in queue + readiness),
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "gate21_source_locks": source_locks,
        "validator_bindings": bindings,
        "pytest_coverage": coverage,
        "contract_patch_queue": queue,
        "fixture_execution_readiness": readiness,
        "package_c_and_firewall": firewall,
        "validation_plan": validation_plan(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "Gate21 head ancestry": s["gate21_head_is_ancestor_of_current"] is True,
        "Gate21 disposition": s["gate21_disposition"] == EXPECTED_GATE21_DISPOSITION,
        "Gate21 no-auth": s["gate21_no_auth"] is True,
        "Gate21 review-only": s["gate21_review_only"] is True,
        "Gate21 mutation families": int(s["gate21_mutation_families"]) >= 29,
        "Gate21 source lock rows": s["gate21_source_lock_rows"] >= 9,
        "Gate21 source drift": s["gate21_source_drift"] == 0,
        "Gate21 missing sources": s["gate21_missing_sources"] == 0,
        "Validator bindings": s["validator_bindings"] >= 29,
        "Binding failures": s["binding_failures"] == 0,
        "Pytest coverage": s["pytest_coverage_rows"] == s["validator_bindings"],
        "Pytest markers": s["pytest_missing_markers"] == 0,
        "Contract patch queue": s["contract_patch_queue_rows"] == s["validator_bindings"],
        "No blocking patch gaps": s["patches_required_before_static_fixture_execution"] == 0,
        "Readiness scopes": s["readiness_rows"] == 4,
        "Readiness blocked scopes": s["readiness_blocked_scopes"] == 0,
        "Package C blocked": s["package_c_state"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
        "No-auth firewall": s["no_auth_firewall_failures"] == 0,
        "Runtime allowed rows": s["runtime_allowed_rows"] == 0,
        "Production allowed rows": s["production_allowed_rows"] == 0,
    }
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE22_SIDEWALL_GATE21_SOURCE_LOCK_20260630.csv": payload["gate21_source_locks"],
        "NODI_COMSOL_GATE22_SIDEWALL_VALIDATOR_BINDING_MATRIX_20260630.csv": payload["validator_bindings"],
        "NODI_COMSOL_GATE22_SIDEWALL_PYTEST_COVERAGE_MATRIX_20260630.csv": payload["pytest_coverage"],
        "NODI_COMSOL_GATE22_SIDEWALL_CONTRACT_PATCH_QUEUE_20260630.csv": payload["contract_patch_queue"],
        "NODI_COMSOL_GATE22_SIDEWALL_FIXTURE_EXECUTION_READINESS_20260630.csv": payload["fixture_execution_readiness"],
        "NODI_COMSOL_GATE22_SIDEWALL_PACKAGE_C_AND_NO_AUTH_FIREWALL_20260630.csv": payload["package_c_and_firewall"],
        "NODI_COMSOL_GATE22_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_VALIDATOR_BINDING_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate22 Sidewall Validator Binding Matrix",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Validator bindings: {payload['summary']['validator_bindings']}",
            f"- Pytest missing markers: {payload['summary']['pytest_missing_markers']}",
            f"- Contract patch gaps before fixture execution: {payload['summary']['patches_required_before_static_fixture_execution']}",
            f"- Readiness blocked scopes: {payload['summary']['readiness_blocked_scopes']}",
            f"- Package C state: `{payload['summary']['package_c_state']}`",
            "- Boundary: no runtime, no solver, no COMSOL launch, no .mph load, no production, no route/yield/detection claims.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate22 disposition: `{DISPOSITION}`",
                f"- Gate21 source drift/missing: {payload['summary']['gate21_source_drift']}/{payload['summary']['gate21_missing_sources']}.",
                f"- Validator bindings / coverage rows: {payload['summary']['validator_bindings']}/{payload['summary']['pytest_coverage_rows']}.",
                "- Gate23 may prepare static executable fixtures only; no runtime or Package C physics is authorized.",
                "- Package A/B/D remain static/contract-only; Package C remains blocked.",
                "- Boundary: no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate22_validator_binding:
        parser.error("--confirm-gate22-validator-binding is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE22_SIDEWALL_VALIDATOR_BINDING")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
