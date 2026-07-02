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
PREFIX = "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT"
ARTIFACT_ID = "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_20260702"
DISPOSITION = "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_READY"
BLOCKED_DISPOSITION = "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_FAIL_CLOSED"
CLAIM_BOUNDARY = (
    "comsol_v4_bound_extreme_simulation_alignment_not_project_measurement"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

EXPECTED_V4_ID = "EV_PBS_SAMPLE_SURFACE_ASSUMPTION_SET_V4_20260627"
EXPECTED_V4_VERSION = "4.0.0"
EXPECTED_V4_GOVERNANCE_VERSION = "2026-06-27.1"
EXPECTED_V4_SHA256 = (
    "2bd97d7684a582343da05bc519f47d598baf29efa5e0157ea8330e9fae223d92"
)
EXPECTED_V4_SCENARIOS = {
    "EXTREV-SCEN-LOW",
    "EXTREV-SCEN-MID",
    "EXTREV-SCEN-HIGH",
    "EXTREV-SCEN-EXTREME",
}

COMSOL_PROJECT_ROOT = (
    PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
)
COMSOL_V4_CONTRACT = (
    COMSOL_PROJECT_ROOT
    / "roadmap/EV_PBS_SAMPLE_SURFACE_CANONICAL_CONTRACT_V4_20260627.json"
)
COMSOL_V4_BOOTSTRAP = (
    COMSOL_PROJECT_ROOT
    / "roadmap/EV_PBS_WET_MODEL_BOOTSTRAP_MANIFEST_V4_20260627.csv"
)
COMSOL_V4_MANIFEST = (
    COMSOL_PROJECT_ROOT
    / "roadmap/EV_PBS_SAMPLE_SURFACE_CANONICAL_CONTRACT_V4_MANIFEST_20260627.csv"
)
COMSOL_V4_SCHEMA = (
    COMSOL_PROJECT_ROOT
    / "p0_model_package/model_contracts/sample_surface_assumption_set.v4.schema.json"
)
COMSOL_AGENT_INSTRUCTIONS = COMSOL_PROJECT_ROOT / "AGENTS.md"

NODI_RELEASE_STATUS = (
    PROJECT_ROOT
    / "reports/joint_interface_20260701/"
    "NODI_PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE_STATUS_20260701.json"
)
NODI_RELEASE_ROWS = (
    PROJECT_ROOT
    / "reports/joint_interface_20260701/"
    "NODI_PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE_ENVELOPE_ROWS_20260701.csv"
)
NODI_INTEGRATED_STATUS = (
    PROJECT_ROOT
    / "reports/joint_interface_20260701/"
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW_STATUS_20260701.json"
)
NODI_INTEGRATED_ROWS = (
    PROJECT_ROOT
    / "reports/joint_interface_20260701/"
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW_REVIEW_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "bind NODI sidewall simulation candidates to the COMSOL V4 upper "
    "sample/surface/wet-rough-wall assumption contract"
)
BLOCKED_USE = (
    "unbound V4 scenario use; silent V4 hash drift; treating V4 assumptions as "
    "project measurement/calibration; overwriting COMSOL V4; actual fabrication "
    "or production without a separate simulation-to-fabrication handoff"
)

SOURCE_FILES = {
    "comsol_v4_contract_json": COMSOL_V4_CONTRACT,
    "comsol_v4_bootstrap_manifest": COMSOL_V4_BOOTSTRAP,
    "comsol_v4_contract_manifest": COMSOL_V4_MANIFEST,
    "comsol_v4_schema": COMSOL_V4_SCHEMA,
    "comsol_agent_instructions": COMSOL_AGENT_INSTRUCTIONS,
    "nodi_simulation_release_status": NODI_RELEASE_STATUS,
    "nodi_simulation_release_rows": NODI_RELEASE_ROWS,
    "nodi_integrated_simulation_status": NODI_INTEGRATED_STATUS,
    "nodi_integrated_simulation_rows": NODI_INTEGRATED_ROWS,
    "alignment_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_v4_upper_assumption_alignment.py",
    "alignment_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_v4_upper_assumption_alignment.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build NODI/COMSOL V4 upper-assumption alignment artifacts."
    )
    parser.add_argument(
        "--confirm-nodi-comsol-v4-upper-assumption-alignment",
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_summary(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if isinstance(data.get("summary"), dict):
        return data["summary"]
    return data


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
    output_report = f"reports/586_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_comsol_v4_upper_assumption_alignment.py",
        "tests/test_nodi_comsol_v4_upper_assumption_alignment.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "v4_alignment_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "v4_alignment_output"
            release_decision = "included_or_rewritten_by_v4_alignment_builder"
        else:
            classification = "non_alignment_dirty_context"
            release_decision = "ignored_for_v4_alignment"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def build_v4_scenario_rows(contract: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = contract.get("scenarios", [])
    bootstrap_by_scenario = {
        row.get("scenario_id", ""): row for row in read_csv_rows(COMSOL_V4_BOOTSTRAP)
    }
    rows: list[dict[str, Any]] = []
    for scenario in sorted(scenarios, key=lambda row: str(row.get("scenario_id"))):
        scenario_id = str(scenario.get("scenario_id", ""))
        descriptor = scenario.get("descriptor_closure", {})
        bootstrap = bootstrap_by_scenario.get(scenario_id, {})
        compute_authorized = str(scenario.get("compute_authorized_now", ""))
        extreme_preflight = str(bootstrap.get("extreme_preflight_status", ""))
        rows.append(
            {
                "v4_scenario_alignment_row_id": f"V4-SCENARIO-{scenario_id}",
                "assumption_set_id": scenario.get("assumption_set_id", ""),
                "assumption_set_version": scenario.get("assumption_set_version", ""),
                "assumption_set_sha256": bootstrap.get("assumption_set_sha256", ""),
                "governance_version": scenario.get("governance_version", ""),
                "scenario_id": scenario_id,
                "scenario_label": scenario.get("scenario_label", ""),
                "scenario_role": scenario.get("scenario_role", ""),
                "compute_authorized_now": compute_authorized,
                "use_authorized_now": scenario.get("use_authorized_now", ""),
                "bootstrap_status": bootstrap.get("bootstrap_status", ""),
                "extreme_preflight_status": extreme_preflight,
                "buffer_pH": scenario.get("buffer_pH", ""),
                "zeta_center_mV": scenario.get("zeta_center_mV", ""),
                "total_protein_center_mg_mL": scenario.get(
                    "total_protein_center_mg_mL", ""
                ),
                "fraction_above_220_nm": scenario.get("fraction_above_220_nm", ""),
                "fraction_above_300_nm": scenario.get("fraction_above_300_nm", ""),
                "PEG_QC_scope": scenario.get("PEG_QC_scope", ""),
                "sigma0_N_m": descriptor.get("sigma0_N_m", ""),
                "W_Fuchs": descriptor.get("W_Fuchs", ""),
                "aggregation_efficiency_alpha": descriptor.get(
                    "aggregation_efficiency_alpha", ""
                ),
                "delta_corona_fouling_nm": descriptor.get(
                    "delta_corona_fouling_nm", ""
                ),
                "roughness_mode_requirement": scenario.get("roughness_mode", ""),
                "geometry_root_requirement": scenario.get("geometry_root", ""),
                "hydraulic_anchor_requirement": scenario.get("hydraulic_anchor", ""),
                "surface_binding_policy": scenario.get("surface_binding", {}).get(
                    "binding_policy", ""
                ),
                "claim_boundary": scenario.get("claim_boundary", ""),
                "nodi_alignment_status": (
                    "aligned_to_nodi_simulation_overlay"
                    if compute_authorized == "local_python_scenario_only"
                    else "aligned_extreme_branch_preflight_required"
                ),
            }
        )
    return rows


def build_route_binding_rows(contract: dict[str, Any]) -> list[dict[str, Any]]:
    release_rows = read_csv_rows(NODI_RELEASE_ROWS)
    scenario_ids = ";".join(sorted(EXPECTED_V4_SCENARIOS))
    contract_boundary = str(contract.get("claim_boundary", ""))
    rows: list[dict[str, Any]] = []
    for row in sorted(release_rows, key=lambda item: _int(item.get("simulation_rank_index"))):
        geometry_family = str(row.get("route_geometry_family", ""))
        route_id = str(row.get("route_candidate_id", ""))
        is_top = _bool(row.get("simulation_release_candidate_current"))
        rows.append(
            {
                "route_v4_binding_row_id": f"ROUTE-V4-BINDING-{route_id}",
                "binding_version": "nodi_comsol_v4_upper_assumption_alignment_v1",
                "route_candidate_id": route_id,
                "route_geometry_family": geometry_family,
                "simulation_rank_index": _int(row.get("simulation_rank_index")),
                "simulation_release_candidate_current": is_top,
                "simulation_release_label": row.get("simulation_release_label", ""),
                "simulation_route_score_value": _float(
                    row.get("simulation_route_score_value")
                ),
                "simulation_yield_value": _float(row.get("simulation_yield_value")),
                "simulation_detection_probability_value": _float(
                    row.get("simulation_detection_probability_value")
                ),
                "simulation_wet_pass_probability_value": _float(
                    row.get("simulation_wet_pass_probability_value")
                ),
                "comsol_v4_assumption_set_id": contract.get("assumption_set_id", ""),
                "comsol_v4_assumption_set_version": contract.get(
                    "assumption_set_version", ""
                ),
                "comsol_v4_assumption_set_sha256": EXPECTED_V4_SHA256,
                "comsol_v4_governance_version": contract.get(
                    "governance_version", ""
                ),
                "comsol_v4_claim_boundary": contract_boundary,
                "comsol_v4_scenario_set_bound": scenario_ids,
                "geometry_root_binding": f"nodi_sidewall_geometry_family::{geometry_family}",
                "hydraulic_anchor_binding": (
                    "nodi_sidewall_simulation_fixed_velocity_route_formula_anchor_v1"
                ),
                "roughness_state_id_binding": _roughness_binding(geometry_family),
                "wall_state_id_binding": _wall_binding(geometry_family),
                "surface_chemistry_contract_binding": (
                    "PEG_silane_unverified_project_QC_contract_v4"
                ),
                "surface_state_contract_binding": (
                    "nodi_comsol_v4_simulation_surface_state_overlay_v1"
                ),
                "extreme_branch_policy": (
                    "bound_as_preflight_required_not_merged_into_low_mid_high_default"
                ),
                "simulation_claims_authorized_by_alignment": True,
                "actual_measurement_or_calibration_claim": False,
                "actual_fabrication_release_current": _bool(
                    row.get("actual_fabrication_release_current")
                ),
                "actual_production_ingestion_current": _bool(
                    row.get("actual_production_ingestion_current")
                ),
                "alignment_status": "aligned_to_comsol_v4_upper_assumptions",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_alignment_check_rows(
    contract: dict[str, Any],
    source_lock: list[dict[str, Any]],
    scenario_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    release = load_summary(NODI_RELEASE_STATUS)
    checks = [
        (
            "v4_contract_file_exists",
            COMSOL_V4_CONTRACT.exists(),
            display_path(COMSOL_V4_CONTRACT),
        ),
        (
            "v4_contract_sha_matches_agents_lock",
            sha256_file(COMSOL_V4_CONTRACT) == EXPECTED_V4_SHA256
            if COMSOL_V4_CONTRACT.exists()
            else False,
            EXPECTED_V4_SHA256,
        ),
        (
            "v4_identity_matches_expected",
            contract.get("assumption_set_id") == EXPECTED_V4_ID
            and contract.get("assumption_set_version") == EXPECTED_V4_VERSION,
            f"{contract.get('assumption_set_id')}@{contract.get('assumption_set_version')}",
        ),
        (
            "v4_governance_version_matches_expected",
            contract.get("governance_version") == EXPECTED_V4_GOVERNANCE_VERSION,
            str(contract.get("governance_version", "")),
        ),
        (
            "v4_scenario_set_complete",
            {row["scenario_id"] for row in scenario_rows} == EXPECTED_V4_SCENARIOS,
            ";".join(sorted(row["scenario_id"] for row in scenario_rows)),
        ),
        (
            "v4_bootstrap_sha_bound_on_all_scenarios",
            all(row["assumption_set_sha256"] == EXPECTED_V4_SHA256 for row in scenario_rows),
            str(len(scenario_rows)),
        ),
        (
            "extreme_branch_remains_preflight_separate",
            any(
                row["scenario_id"] == "EXTREV-SCEN-EXTREME"
                and row["nodi_alignment_status"]
                == "aligned_extreme_branch_preflight_required"
                for row in scenario_rows
            ),
            "EXTREV-SCEN-EXTREME",
        ),
        (
            "nodi_release_envelope_ready",
            release.get("disposition")
            == "NODI_PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE_READY",
            str(release.get("disposition", "")),
        ),
        (
            "nodi_route_bindings_cover_two_geometry_families",
            {row["route_geometry_family"] for row in route_rows}
            == {"ideal_rectangle", "trapezoid_tapered_sidewalls"},
            ";".join(sorted(row["route_geometry_family"] for row in route_rows)),
        ),
        (
            "nodi_route_rows_all_carry_v4_identity",
            all(
                row["comsol_v4_assumption_set_id"] == EXPECTED_V4_ID
                and row["comsol_v4_assumption_set_sha256"] == EXPECTED_V4_SHA256
                for row in route_rows
            ),
            str(len(route_rows)),
        ),
        (
            "simulation_claims_allowed_under_alignment",
            all(row["simulation_claims_authorized_by_alignment"] for row in route_rows),
            "simulation_route_score/yield/detection/wet_pass bound to V4 scenarios",
        ),
        (
            "no_actual_release_leakage",
            not any(
                row["actual_fabrication_release_current"]
                or row["actual_production_ingestion_current"]
                for row in route_rows
            ),
            "actual release remains separate from V4 simulation alignment",
        ),
        (
            "all_sources_exist",
            all(row["exists"] == "true" for row in source_lock),
            str(len(source_lock)),
        ),
    ]
    return [
        {
            "check_id": f"V4-ALIGN-CHECK-{index:03d}",
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
                "v4_scenario_rows": payload["v4_scenario_rows"],
                "route_binding_rows": payload["route_binding_rows"],
                "alignment_check_rows": payload["alignment_check_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    contract = load_json(COMSOL_V4_CONTRACT)
    release = load_summary(NODI_RELEASE_STATUS)
    source_lock = source_lock_rows()
    scenario_rows = build_v4_scenario_rows(contract)
    route_rows = build_route_binding_rows(contract)
    check_rows = build_alignment_check_rows(
        contract, source_lock, scenario_rows, route_rows
    )
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    failed_checks = sum(not row["check_pass"] for row in check_rows)
    top = next(
        (row for row in route_rows if row["simulation_release_candidate_current"]),
        {},
    )
    disposition = DISPOSITION
    if source_missing or failed_checks or len(scenario_rows) != 4 or len(route_rows) != 2:
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "comsol_project_root": str(COMSOL_PROJECT_ROOT),
        "comsol_v4_assumption_set_id": contract.get("assumption_set_id", ""),
        "comsol_v4_assumption_set_version": contract.get(
            "assumption_set_version", ""
        ),
        "comsol_v4_assumption_set_sha256": sha256_file(COMSOL_V4_CONTRACT)
        if COMSOL_V4_CONTRACT.exists()
        else "",
        "comsol_v4_expected_sha256": EXPECTED_V4_SHA256,
        "comsol_v4_sha_match": (
            sha256_file(COMSOL_V4_CONTRACT) == EXPECTED_V4_SHA256
            if COMSOL_V4_CONTRACT.exists()
            else False
        ),
        "nodi_release_envelope_disposition": str(release.get("disposition", "")),
        "v4_scenario_rows": len(scenario_rows),
        "v4_low_mid_high_rows": sum(
            row["compute_authorized_now"] == "local_python_scenario_only"
            for row in scenario_rows
        ),
        "v4_extreme_preflight_rows": sum(
            row["nodi_alignment_status"]
            == "aligned_extreme_branch_preflight_required"
            for row in scenario_rows
        ),
        "route_binding_rows": len(route_rows),
        "route_binding_aligned_rows": sum(
            row["alignment_status"] == "aligned_to_comsol_v4_upper_assumptions"
            for row in route_rows
        ),
        "simulation_release_candidate_rows": sum(
            row["simulation_release_candidate_current"] for row in route_rows
        ),
        "top_route_candidate_id": top.get("route_candidate_id", ""),
        "top_route_geometry_family": top.get("route_geometry_family", ""),
        "top_route_score_value": top.get("simulation_route_score_value", 0.0),
        "top_yield_value": top.get("simulation_yield_value", 0.0),
        "top_detection_probability_value": top.get(
            "simulation_detection_probability_value", 0.0
        ),
        "top_wet_pass_probability_value": top.get(
            "simulation_wet_pass_probability_value", 0.0
        ),
        "alignment_check_rows": len(check_rows),
        "failed_alignment_check_rows": failed_checks,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_alignment_dirty_context_rows": sum(
            row["classification"] == "non_alignment_dirty_context"
            for row in dirty_context
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_high_leverage_step": (
            "expand NODI sidewall simulation scoring into explicit COMSOL V4 "
            "LOW/MID/HIGH/EXTREME scenario overlays while preserving the V4 "
            "assumption-set identity and hash"
        ),
    }
    payload = {
        "summary": summary,
        "v4_scenario_rows": scenario_rows,
        "route_binding_rows": route_rows,
        "alignment_check_rows": check_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append("v4_alignment_not_ready")
    if summary["comsol_v4_sha_match"] is not True:
        failures.append("comsol_v4_sha_mismatch")
    if summary["v4_scenario_rows"] != 4:
        failures.append("expected_four_v4_scenarios")
    if summary["route_binding_rows"] != 2:
        failures.append("expected_two_nodi_route_bindings")
    if summary["simulation_release_candidate_rows"] != 1:
        failures.append("expected_one_simulation_release_candidate")
    if summary["failed_alignment_check_rows"] != 0:
        failures.append("failed_alignment_checks_present")
    if summary["source_missing_rows"] != 0:
        failures.append("source_missing")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "v4_scenarios": OUTPUT_DIR / f"{PREFIX}_V4_SCENARIO_ROWS_{DATE_STAMP}.csv",
        "route_bindings": OUTPUT_DIR / f"{PREFIX}_ROUTE_BINDING_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR
        / f"{PREFIX}_ALIGNMENT_CHECK_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "master_report": REPORT_DIR / f"586_{PREFIX}_{DATE_STAMP}.md",
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
    write_csv_rows(outputs["v4_scenarios"], payload["v4_scenario_rows"])
    write_csv_rows(outputs["route_bindings"], payload["route_binding_rows"])
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
            "# NODI/COMSOL V4 Upper-Assumption Alignment",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            "## Locked COMSOL V4 Source",
            "",
            f"- assumption set: `{s['comsol_v4_assumption_set_id']}`",
            f"- version: `{s['comsol_v4_assumption_set_version']}`",
            f"- expected sha256: `{s['comsol_v4_expected_sha256']}`",
            f"- observed sha256: `{s['comsol_v4_assumption_set_sha256']}`",
            f"- sha match: `{s['comsol_v4_sha_match']}`",
            "",
            "## NODI Route Binding",
            "",
            f"- route binding rows: `{s['route_binding_rows']}`",
            f"- simulation release candidate: `{s['top_route_candidate_id']}` (`{s['top_route_geometry_family']}`)",
            f"- simulation route score: `{s['top_route_score_value']}`",
            f"- simulation yield: `{s['top_yield_value']}`",
            f"- simulation detection probability: `{s['top_detection_probability_value']}`",
            f"- simulation wet-pass probability: `{s['top_wet_pass_probability_value']}`",
            "",
            "## V4 Scenario Mirror",
            "",
            f"- scenario rows: `{s['v4_scenario_rows']}`",
            f"- LOW/MID/HIGH local-python scenario rows: `{s['v4_low_mid_high_rows']}`",
            f"- EXTREME preflight rows: `{s['v4_extreme_preflight_rows']}`",
            "",
            "This packet does not rewrite COMSOL V4. It binds NODI's sidewall "
            "simulation-current route/yield/detection/wet-pass branch to the "
            "COMSOL V4 upper assumption identity, scenario set, and required "
            "external geometry/hydraulic/wall/roughness bindings.",
            "",
        ]
    )


def _roughness_binding(geometry_family: str) -> str:
    if geometry_family == "ideal_rectangle":
        return "ideal_smooth_wall_surrogate_v1"
    if geometry_family == "trapezoid_tapered_sidewalls":
        return "trapezoid_smooth_sidewall_surrogate_v1"
    return "unknown_geometry_family_requires_review"


def _wall_binding(geometry_family: str) -> str:
    if geometry_family == "ideal_rectangle":
        return "ideal_rectangle_smooth_wall_state_surrogate_v1"
    if geometry_family == "trapezoid_tapered_sidewalls":
        return "trapezoid_tapered_sidewall_state_surrogate_v1"
    return "unknown_geometry_family_requires_review"


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_nodi_comsol_v4_upper_assumption_alignment:
        raise SystemExit(
            "--confirm-nodi-comsol-v4-upper-assumption-alignment is required"
        )
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
