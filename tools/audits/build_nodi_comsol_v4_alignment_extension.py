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
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_COMSOL_V4_ALIGNMENT_EXTENSION"
ARTIFACT_ID = "NODI_COMSOL_V4_ALIGNMENT_EXTENSION_20260702"
DISPOSITION = "NODI_COMSOL_V4_ALIGNMENT_EXTENSION_READY_DIRTY_SOURCE_AWARE"
BLOCKED_DISPOSITION = "NODI_COMSOL_V4_ALIGNMENT_EXTENSION_FAIL_CLOSED"
CLAIM_BOUNDARY = "comsol_v4_bound_simulation_extension_dirty_source_aware"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

COMSOL_PROJECT_ROOT = (
    PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
)
V4_ALIGNMENT_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_STATUS_20260702.json"
)
V4_ALIGNMENT_ROUTE_BINDINGS = (
    OUTPUT_DIR
    / "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_ROUTE_BINDING_ROWS_20260702.csv"
)
V4_ALIGNMENT_SCENARIOS = (
    OUTPUT_DIR
    / "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_V4_SCENARIO_ROWS_20260702.csv"
)

NODI_SOURCE_FILES = {
    "nodi_noise_readout_bundle": PROJECT_ROOT
    / "configs/realism_v2/noise_readout_scenario_bundle.yaml",
    "nodi_ev_sample_profiles": PROJECT_ROOT
    / "configs/realism_v2/ev_sample_profiles.yaml",
    "nodi_route_role_vocabulary": PROJECT_ROOT
    / "configs/realism_v2/route_role_vocabulary.yaml",
    "nodi_forbidden_claims_lexicon": PROJECT_ROOT
    / "configs/realism_v2/forbidden_claims_lexicon.yaml",
    "nodi_candidate_universe_manifest": PROJECT_ROOT
    / "results/post_v2_mandatory_audit/candidate_universe_manifest.json",
    "nodi_top_candidate_audit": PROJECT_ROOT
    / "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv",
    "nodi_physical_ceiling_manifest": PROJECT_ROOT
    / "results/post_v2_physical_ceiling/physical_ceiling_contract_manifest.json",
    "nodi_full_wave_green_tensor_diagnostic": PROJECT_ROOT
    / "results/post_v2_physical_ceiling/full_wave_green_tensor_diagnostic.csv",
    "nodi_vector_jones_polarization_diagnostic": PROJECT_ROOT
    / "results/post_v2_physical_ceiling/vector_jones_polarization_diagnostic.csv",
    "nodi_roughness_leakage_diagnostic": PROJECT_ROOT
    / "results/post_v2_physical_ceiling/roughness_leakage_diagnostic.csv",
    "nodi_transport_residence_time_diagnostic": PROJECT_ROOT
    / "results/post_v2_physical_ceiling/transport_residence_time_diagnostic.csv",
    "nodi_simulation_route_correction": PROJECT_ROOT
    / "reports/580_NODI_PACKAGE_C_SIDEWALL_SIMULATION_ASSUMPTION_ROUTE_CORRECTION_20260702.md",
    "nodi_simulation_release_envelope": PROJECT_ROOT
    / "reports/585_NODI_PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE_20260701.md",
}

COMSOL_SOURCE_FILES = {
    "comsol_model_root_lock": COMSOL_PROJECT_ROOT
    / "p0_model_package/model_contracts/MODEL_ROOT_LOCK.md",
    "comsol_wall_state_schema": COMSOL_PROJECT_ROOT
    / "p0_model_package/model_contracts/wall_state_schema.csv",
    "comsol_surface_interaction_priors": COMSOL_PROJECT_ROOT
    / "p0_model_package/model_contracts/surface_interaction_priors.csv",
    "comsol_parameter_priors": COMSOL_PROJECT_ROOT
    / "p0_model_package/model_contracts/parameter_priors.csv",
    "comsol_v4_route_design_winner_decision": COMSOL_PROJECT_ROOT
    / "roadmap/EV_PBS_V4_NORMAL_NANOCHANNEL_ROUTE_DESIGN_WINNER_BOUNDARY_V1_20260702_DECISION.csv",
    "comsol_v4_route_design_winner_blocked": COMSOL_PROJECT_ROOT
    / "roadmap/EV_PBS_V4_NORMAL_NANOCHANNEL_ROUTE_DESIGN_WINNER_BOUNDARY_V1_20260702_BLOCKED_STATEMENTS.csv",
    "comsol_v4_claim_promotion_quarantine_summary": COMSOL_PROJECT_ROOT
    / "roadmap/EV_PBS_V4_NORMAL_NANOCHANNEL_CLAIM_PROMOTION_V0_DEFECT_QUARANTINE_SUMMARY_20260630.csv",
    "comsol_v4_scenario_sensitivity": COMSOL_PROJECT_ROOT
    / "roadmap/EV_PBS_SAMPLE_SURFACE_CANONICAL_V4_SCENARIO_SENSITIVITY_TABLE_20260627.csv",
}

SOURCE_FILES = {
    "v4_alignment_status": V4_ALIGNMENT_STATUS,
    "v4_alignment_route_bindings": V4_ALIGNMENT_ROUTE_BINDINGS,
    "v4_alignment_scenarios": V4_ALIGNMENT_SCENARIOS,
    "extension_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_v4_alignment_extension.py",
    "extension_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_v4_alignment_extension.py",
    **NODI_SOURCE_FILES,
    **COMSOL_SOURCE_FILES,
}

ALLOWED_USE = (
    "extend the COMSOL V4 alignment into route-universe, readout/noise, "
    "physical-ceiling, wet/surface, and simulation state-machine bindings"
)
BLOCKED_USE = (
    "silent clean-source assumption; direct production/fabrication promotion; "
    "route-universe grain collapse; bypassing readout/noise or physical-ceiling "
    "diagnostics"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build extended NODI/COMSOL V4 alignment binding artifacts."
    )
    parser.add_argument(
        "--confirm-nodi-comsol-v4-alignment-extension",
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


def git_status_map() -> dict[str, str]:
    return {
        git_path_from_status_line(line): line[:2].strip() or "modified"
        for line in git_status_lines()
    }


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_summary(path: Path) -> dict[str, Any]:
    data = load_json(path)
    return data.get("summary", data) if isinstance(data, dict) else {}


def source_dependency_rows() -> list[dict[str, Any]]:
    status = git_status_map()
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rel = display_path(path) if exists else str(path)
        local_git_status = ""
        if exists and path.is_relative_to(PROJECT_ROOT):
            local_git_status = status.get(rel, "")
        rows.append(
            {
                "source_id": source_id,
                "path": rel,
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "source_project": "NODI" if path.is_relative_to(PROJECT_ROOT) else "COMSOL",
                "local_git_status": local_git_status,
                "clean_for_git_visible_external_review": str(
                    exists and (not path.is_relative_to(PROJECT_ROOT) or not local_git_status)
                ).lower(),
                "source_dependency_policy": (
                    "committed_or_external_hashable_source"
                    if not local_git_status
                    else "dirty_source_dependency_visible_not_promoted_as_clean"
                ),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def route_universe_crosswalk_rows() -> list[dict[str, Any]]:
    candidate_manifest = load_json(NODI_SOURCE_FILES["nodi_candidate_universe_manifest"])
    route_bindings = read_csv_rows(V4_ALIGNMENT_ROUTE_BINDINGS)
    return [
        {
            "crosswalk_row_id": "ROUTE-XWALK-COMSOL-V4-STAGE1-36",
            "source_system": "COMSOL_V4",
            "source_route_universe": "v4_stage1_36_candidate_descriptor_screen",
            "route_grain": "nano_entrance_descriptor_candidate",
            "route_count": 36,
            "maps_to_nodi_sidewall_candidate": "unmapped_by_design",
            "mapping_policy": "requires explicit adapter before merged scoring",
            "claim_level": "v4_descriptor_context_not_nodi_route_score",
        },
        {
            "crosswalk_row_id": "ROUTE-XWALK-COMSOL-V4-FIELD-12",
            "source_system": "COMSOL_V4",
            "source_route_universe": "v4_absorbed_12_field_descriptor_candidates",
            "route_grain": "smooth_wall_field_descriptor_candidate",
            "route_count": 12,
            "maps_to_nodi_sidewall_candidate": "unmapped_by_design",
            "mapping_policy": "requires explicit adapter before merged scoring",
            "claim_level": "v4_field_context_not_nodi_route_score",
        },
        {
            "crosswalk_row_id": "ROUTE-XWALK-NODI-POST-V2-572",
            "source_system": "NODI_POST_V2",
            "source_route_universe": candidate_manifest.get(
                "candidate_universe_scope_label", ""
            ),
            "route_grain": candidate_manifest.get("candidate_universe_route_dedup_key", ""),
            "route_count": int(candidate_manifest.get("candidate_universe_unique_routes", 0)),
            "maps_to_nodi_sidewall_candidate": "context_only_not_one_to_one",
            "mapping_policy": "do_not_collapse_572_routes_into_two_sidewall_candidates",
            "claim_level": candidate_manifest.get("candidate_universe_scope_claim_level", ""),
        },
        {
            "crosswalk_row_id": "ROUTE-XWALK-NODI-PACKAGE-C-2",
            "source_system": "NODI_PACKAGE_C_SIDEWALL",
            "source_route_universe": "ideal_rectangle_and_trapezoid_sidewall_pair",
            "route_grain": "route_candidate_id + route_geometry_family",
            "route_count": len(route_bindings),
            "maps_to_nodi_sidewall_candidate": ";".join(
                row["route_candidate_id"] for row in route_bindings
            ),
            "mapping_policy": "active_sidewall_simulation_candidate_pair",
            "claim_level": "simulation_current_route_candidate",
        },
    ]


def readout_noise_binding_rows() -> list[dict[str, Any]]:
    route_bindings = read_csv_rows(V4_ALIGNMENT_ROUTE_BINDINGS)
    noise_scenarios = required_scenario_ids(
        NODI_SOURCE_FILES["nodi_noise_readout_bundle"]
    )
    physical = load_json(NODI_SOURCE_FILES["nodi_physical_ceiling_manifest"])
    lanes = [contract.get("lane_id", "") for contract in physical.get("contracts", [])]
    rows: list[dict[str, Any]] = []
    for row in route_bindings:
        rows.append(
            {
                "readout_binding_row_id": f"READOUT-NOISE-BINDING-{row['route_candidate_id']}",
                "route_candidate_id": row["route_candidate_id"],
                "route_geometry_family": row["route_geometry_family"],
                "noise_readout_scenario_count": len(noise_scenarios),
                "noise_readout_scenarios_bound": ";".join(noise_scenarios),
                "physical_ceiling_lane_count": len(lanes),
                "physical_ceiling_lanes_bound": ";".join(lanes),
                "physical_ceiling_role": physical.get("physical_ceiling_role", ""),
                "calibrated_claim_allowed": bool(
                    physical.get("calibrated_claim_allowed", True)
                ),
                "solver_or_simulation_execution_authorized": bool(
                    physical.get("solver_or_simulation_execution_authorized", True)
                ),
                "readout_binding_status": "bound_to_noise_readout_and_physical_ceiling_registries",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def wet_surface_v4_binding_rows() -> list[dict[str, Any]]:
    route_bindings = read_csv_rows(V4_ALIGNMENT_ROUTE_BINDINGS)
    scenarios = read_csv_rows(V4_ALIGNMENT_SCENARIOS)
    rows: list[dict[str, Any]] = []
    for route in route_bindings:
        for scenario in scenarios:
            rows.append(
                {
                    "wet_surface_binding_row_id": (
                        f"WET-SURFACE-V4-BINDING-{route['route_candidate_id']}-"
                        f"{scenario['scenario_id']}"
                    ),
                    "route_candidate_id": route["route_candidate_id"],
                    "route_geometry_family": route["route_geometry_family"],
                    "scenario_id": scenario["scenario_id"],
                    "scenario_role": scenario["scenario_role"],
                    "surface_chemistry_contract_binding": route[
                        "surface_chemistry_contract_binding"
                    ],
                    "surface_state_contract_binding": route[
                        "surface_state_contract_binding"
                    ],
                    "wall_state_id_binding": route["wall_state_id_binding"],
                    "roughness_state_id_binding": route["roughness_state_id_binding"],
                    "sigma0_N_m": scenario.get("sigma0_N_m", ""),
                    "W_Fuchs": scenario.get("W_Fuchs", ""),
                    "aggregation_efficiency_alpha": scenario.get(
                        "aggregation_efficiency_alpha", ""
                    ),
                    "delta_corona_fouling_nm": scenario.get(
                        "delta_corona_fouling_nm", ""
                    ),
                    "fraction_above_220_nm": scenario.get("fraction_above_220_nm", ""),
                    "fraction_above_300_nm": scenario.get("fraction_above_300_nm", ""),
                    "v4_alignment_status": scenario["nodi_alignment_status"],
                    "binding_status": "v4_wet_surface_assumption_bound_to_sidewall_route",
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def state_machine_rows() -> list[dict[str, Any]]:
    states = [
        (
            1,
            "simulation_source_hash_locked",
            "source manifests and route rows carry hashes and V4 identity",
        ),
        (
            2,
            "simulation_candidate_metric",
            "route score, yield, detection, and wet-pass metrics are simulation-current",
        ),
        (
            3,
            "simulation_release_candidate",
            "one simulation route may be selected as simulation release candidate",
        ),
        (
            4,
            "solver_supported_candidate",
            "future solver branch may attach solver support without collapsing grains",
        ),
    ]
    rows = []
    for order, state, meaning in states:
        rows.append(
            {
                "state_order": order,
                "state_id": state,
                "state_meaning": meaning,
                "allowed_next_state": states[order][1] if order < len(states) else "",
                "final_or_production_state": False,
                "requires_v4_identity": True,
                "requires_source_hash": True,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def quarantine_guard_rows() -> list[dict[str, Any]]:
    path = COMSOL_SOURCE_FILES["comsol_v4_claim_promotion_quarantine_summary"]
    row_count = len(read_csv_rows(path)) if path.exists() else 0
    return [
        {
            "quarantine_guard_row_id": "V4-CLAIM-PROMOTION-QUARANTINE-GUARD",
            "source_path": display_path(path),
            "source_sha256": sha256_file(path) if path.exists() else "",
            "source_rows": row_count,
            "active_source_allowed": False,
            "negative_guard_allowed": True,
            "guard_status": "quarantine_artifact_retained_as_negative_guard_only",
            "claim_boundary": CLAIM_BOUNDARY,
        }
    ]


def alignment_check_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    source_rows = payload["source_dependency_rows"]
    dirty_count = sum(
        1
        for row in source_rows
        if row["source_project"] == "NODI" and row["local_git_status"]
    )
    checks = [
        (
            "v4_alignment_ready",
            payload["v4_alignment_summary"].get("disposition")
            == "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_READY",
            str(payload["v4_alignment_summary"].get("disposition", "")),
        ),
        (
            "route_universe_crosswalk_has_four_layers",
            len(payload["route_universe_crosswalk_rows"]) == 4,
            str(len(payload["route_universe_crosswalk_rows"])),
        ),
        (
            "readout_noise_physical_ceiling_bound_for_two_routes",
            len(payload["readout_noise_binding_rows"]) == 2
            and all(
                row["noise_readout_scenario_count"] == 8
                and row["physical_ceiling_lane_count"] == 4
                for row in payload["readout_noise_binding_rows"]
            ),
            str(len(payload["readout_noise_binding_rows"])),
        ),
        (
            "wet_surface_v4_bound_for_route_x_scenario_matrix",
            len(payload["wet_surface_v4_binding_rows"]) == 8,
            str(len(payload["wet_surface_v4_binding_rows"])),
        ),
        (
            "state_machine_has_four_simulation_states",
            len(payload["state_machine_rows"]) == 4,
            str(len(payload["state_machine_rows"])),
        ),
        (
            "quarantine_artifacts_not_active_sources",
            all(not row["active_source_allowed"] for row in payload["quarantine_guard_rows"]),
            str(len(payload["quarantine_guard_rows"])),
        ),
        (
            "dirty_source_dependencies_are_visible",
            dirty_count > 0,
            str(dirty_count),
        ),
        (
            "all_sources_exist",
            all(row["exists"] == "true" for row in source_rows),
            str(len(source_rows)),
        ),
    ]
    return [
        {
            "check_id": f"V4-EXT-CHECK-{index:03d}",
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
                "route_universe_crosswalk_rows": payload[
                    "route_universe_crosswalk_rows"
                ],
                "readout_noise_binding_rows": payload["readout_noise_binding_rows"],
                "wet_surface_v4_binding_rows": payload[
                    "wet_surface_v4_binding_rows"
                ],
                "state_machine_rows": payload["state_machine_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    source_rows = source_dependency_rows()
    payload: dict[str, Any] = {
        "v4_alignment_summary": load_summary(V4_ALIGNMENT_STATUS),
        "source_dependency_rows": source_rows,
        "route_universe_crosswalk_rows": route_universe_crosswalk_rows(),
        "readout_noise_binding_rows": readout_noise_binding_rows(),
        "wet_surface_v4_binding_rows": wet_surface_v4_binding_rows(),
        "state_machine_rows": state_machine_rows(),
        "quarantine_guard_rows": quarantine_guard_rows(),
    }
    payload["alignment_check_rows"] = alignment_check_rows(payload)
    failed_checks = sum(not row["check_pass"] for row in payload["alignment_check_rows"])
    source_missing = sum(row["exists"] != "true" for row in source_rows)
    dirty_source_rows = sum(
        1
        for row in source_rows
        if row["source_project"] == "NODI" and row["local_git_status"]
    )
    disposition = DISPOSITION
    if failed_checks or source_missing:
        disposition = BLOCKED_DISPOSITION
    summary = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_alignment_disposition": str(
            payload["v4_alignment_summary"].get("disposition", "")
        ),
        "source_dependency_rows": len(source_rows),
        "source_missing_rows": source_missing,
        "dirty_source_dependency_rows": dirty_source_rows,
        "route_universe_crosswalk_rows": len(payload["route_universe_crosswalk_rows"]),
        "readout_noise_binding_rows": len(payload["readout_noise_binding_rows"]),
        "wet_surface_v4_binding_rows": len(payload["wet_surface_v4_binding_rows"]),
        "state_machine_rows": len(payload["state_machine_rows"]),
        "quarantine_guard_rows": len(payload["quarantine_guard_rows"]),
        "alignment_check_rows": len(payload["alignment_check_rows"]),
        "failed_alignment_check_rows": failed_checks,
        "dirty_source_policy": (
            "dirty NODI source dependencies are visible and not treated as clean "
            "external-review inputs"
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_high_leverage_step": (
            "either commit/refresh dirty NODI upper-assumption sources or build "
            "scenario-expanded sidewall scoring using the dirty-source-aware "
            "bindings as explicit inputs"
        ),
    }
    payload["summary"] = summary
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append("alignment_extension_not_ready")
    if summary["source_missing_rows"] != 0:
        failures.append("source_missing")
    if summary["route_universe_crosswalk_rows"] != 4:
        failures.append("route_universe_crosswalk_incomplete")
    if summary["readout_noise_binding_rows"] != 2:
        failures.append("readout_noise_binding_incomplete")
    if summary["wet_surface_v4_binding_rows"] != 8:
        failures.append("wet_surface_binding_incomplete")
    if summary["failed_alignment_check_rows"] != 0:
        failures.append("failed_alignment_checks_present")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "source_dependencies": OUTPUT_DIR
        / f"{PREFIX}_SOURCE_DEPENDENCY_ROWS_{DATE_STAMP}.csv",
        "route_universe_crosswalk": OUTPUT_DIR
        / f"{PREFIX}_ROUTE_UNIVERSE_CROSSWALK_ROWS_{DATE_STAMP}.csv",
        "readout_noise_binding": OUTPUT_DIR
        / f"{PREFIX}_READOUT_NOISE_BINDING_ROWS_{DATE_STAMP}.csv",
        "wet_surface_binding": OUTPUT_DIR
        / f"{PREFIX}_WET_SURFACE_V4_BINDING_ROWS_{DATE_STAMP}.csv",
        "state_machine": OUTPUT_DIR
        / f"{PREFIX}_SIMULATION_STATE_MACHINE_ROWS_{DATE_STAMP}.csv",
        "quarantine_guard": OUTPUT_DIR
        / f"{PREFIX}_QUARANTINE_GUARD_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR
        / f"{PREFIX}_ALIGNMENT_CHECK_ROWS_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "master_report": REPORT_DIR / f"587_{PREFIX}_{DATE_STAMP}.md",
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
    write_csv_rows(outputs["source_dependencies"], payload["source_dependency_rows"])
    write_csv_rows(
        outputs["route_universe_crosswalk"], payload["route_universe_crosswalk_rows"]
    )
    write_csv_rows(outputs["readout_noise_binding"], payload["readout_noise_binding_rows"])
    write_csv_rows(outputs["wet_surface_binding"], payload["wet_surface_v4_binding_rows"])
    write_csv_rows(outputs["state_machine"], payload["state_machine_rows"])
    write_csv_rows(outputs["quarantine_guard"], payload["quarantine_guard_rows"])
    write_csv_rows(outputs["alignment_checks"], payload["alignment_check_rows"])
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
            "# NODI/COMSOL V4 Alignment Extension",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Source dependency rows: `{s['source_dependency_rows']}`.",
            f"Dirty NODI source dependency rows: `{s['dirty_source_dependency_rows']}`.",
            f"Route-universe crosswalk rows: `{s['route_universe_crosswalk_rows']}`.",
            f"Readout/noise binding rows: `{s['readout_noise_binding_rows']}`.",
            f"Wet/surface V4 binding rows: `{s['wet_surface_v4_binding_rows']}`.",
            f"State-machine rows: `{s['state_machine_rows']}`.",
            f"Quarantine guard rows: `{s['quarantine_guard_rows']}`.",
            "",
            "This extension keeps the NODI sidewall simulation branch aligned with "
            "COMSOL V4 without silently pretending that dirty local NODI sources "
            "are already clean, git-visible external-review inputs.",
            "",
        ]
    )


def required_scenario_ids(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict) and isinstance(data.get("required_scenario_ids"), list):
        return [str(item) for item in data["required_scenario_ids"]]
    ids: list[str] = []
    in_block = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "required_scenario_ids:":
            in_block = True
            continue
        if in_block and stripped.startswith("- "):
            ids.append(stripped[2:].strip().strip('"').strip("'"))
            continue
        if in_block and stripped and not stripped.startswith("#"):
            break
    return ids


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_nodi_comsol_v4_alignment_extension:
        raise SystemExit("--confirm-nodi-comsol-v4-alignment-extension is required")
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
