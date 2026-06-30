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

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits.build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight import (  # noqa: E402
    REQUIRED_PROOF_CONTRACT_FIELDS,
)


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

EXPECTED_GATE30_31_DISPOSITION = (
    "NODI_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
DISPOSITION = (
    "NODI_GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF_READY_NO_PROOF_REGISTRATION"
)
ALLOWED_USE = (
    "external AI research synthesis handoff;Gate30/31 candidate review intake;"
    "future authorization-supersession preflight;no-proof-registration"
)
BLOCKED_USE = (
    "Package C proof/pass registration;package_C_validation_status pass;runtime configuration;"
    "sidewall PRS/EAS numeric output;NODI runtime recomputation;COMSOL launch;.mph load;"
    "validated Brownian solver output;validated hindered diffusion;trapezoid Poiseuille solver output;"
    "fixed-pressure q_ch output;flux-weighted sampling;electrokinetic grid output;optical solver output;"
    "true W_eff;reference strength claim;detector response claim;sidewall scattering claim;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

GATE30_31_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_STATUS_20260630.json"
GATE30_31_REPORT = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_REPORT_20260630.json"
GATE30_31_RAW_METRICS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_RAW_METRICS_20260630.json"
GATE30_31_SUMMARY_METRICS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_SUMMARY_METRICS_20260630.json"
GATE30_31_CANDIDATE_MANIFEST = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_CANDIDATE_MANIFEST_20260630.csv"
GATE30_31_CANDIDATE_MANIFEST_JSON = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_CANDIDATE_MANIFEST_20260630.json"
GATE30_31_EVIDENCE_MAP = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_CANDIDATE_EVIDENCE_MAP_20260630.csv"
GATE30_31_PARAMETER_MATRIX = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_TEST_PARAMETER_MATRIX_20260630.csv"
GATE30_31_SEED_MATRIX = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_RNG_SEED_MATRIX_20260630.csv"
GATE30_31_SOURCE_LOCK = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_SOURCE_LOCK_20260630.csv"
GATE30_31_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
GATE30_31_PROMPT = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_EXTERNAL_REVIEW_PROMPT_20260630.md"
GATE30_31_MANIFEST = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_MANIFEST_20260630.csv"
GATE27_PROOF_CONTRACT = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv"
GATE29_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_STATUS_20260630.json"

SOURCE_FILES = {
    "gate30_31_status": GATE30_31_STATUS,
    "gate30_31_report": GATE30_31_REPORT,
    "gate30_31_raw_metrics": GATE30_31_RAW_METRICS,
    "gate30_31_summary_metrics": GATE30_31_SUMMARY_METRICS,
    "gate30_31_candidate_manifest": GATE30_31_CANDIDATE_MANIFEST,
    "gate30_31_candidate_manifest_json": GATE30_31_CANDIDATE_MANIFEST_JSON,
    "gate30_31_evidence_map": GATE30_31_EVIDENCE_MAP,
    "gate30_31_parameter_matrix": GATE30_31_PARAMETER_MATRIX,
    "gate30_31_seed_matrix": GATE30_31_SEED_MATRIX,
    "gate30_31_source_lock": GATE30_31_SOURCE_LOCK,
    "gate30_31_no_proof_firewall": GATE30_31_FIREWALL,
    "gate30_31_external_review_prompt": GATE30_31_PROMPT,
    "gate30_31_manifest": GATE30_31_MANIFEST,
    "gate27_proof_contract": GATE27_PROOF_CONTRACT,
    "gate29_status": GATE29_STATUS,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "trajectory": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "gate30_31_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
    "gate30_31_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
    "gate32_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate32_sidewall_package_c_external_review_handoff.py",
    "gate32_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate32_sidewall_package_c_external_review_handoff.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

ACCEPTABLE_EXTERNAL_VERDICTS = (
    "READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY",
    "NEEDS_MORE_CANDIDATE_EVIDENCE",
    "BLOCKED_CLAIM_PROMOTION",
)

RESEARCH_SYNTHESIS_QUESTIONS = (
    (
        "brownian_reflection_target",
        "Find and synthesize authoritative sources on reflected Brownian motion / Skorokhod reflection in convex polygonal domains; state what is and is not justified for a finite-step engineering surrogate.",
    ),
    (
        "finite_step_algorithms",
        "Compare active-set normal reflection, sequential half-plane reflection, projection/clamp, rejection/resampling, substepping, and exact/approximate reflected-kernel methods for polygonal domains.",
    ),
    (
        "one_wall_limit",
        "Identify the strongest one-wall Neumann/folded-normal sanity tests and what tolerances or diagnostics are appropriate for finite dt Brownian dynamics near a planar wall.",
    ),
    (
        "equilibrium_uniformity",
        "Recommend equilibrium uniformity tests for reflecting Brownian motion in a trapezoid center-accessible domain, including u-marginal, x-local normalized slices, symmetry, and sample-size requirements.",
    ),
    (
        "boundary_atom_bias",
        "Recommend diagnostics for boundary atoms, projection spikes, wall pile-up, and how to distinguish acceptable finite-step reflection contacts from artificial boundary clamping.",
    ),
    (
        "corner_active_set_bias",
        "Analyze corner active-set behavior in convex polygonal reflection, including normal-cone ambiguity, corner pile-up risks, dt/substep triggers, and convergence telemetry.",
    ),
    (
        "dt_convergence_thresholds",
        "Propose a proof-level dt-halving matrix and quantitative pass/fail thresholds for wall-distance distributions, local x/u distributions, nearest-wall counts, and reflection/corner event rates.",
    ),
    (
        "trapezoid_package_c_proof_schema",
        "Recommend additional proof artifact fields beyond the current 52-field candidate manifest, especially raw metric reproducibility, environment locks, seed policy, and reviewer/authorization records.",
    ),
    (
        "blocked_physics_boundaries",
        "Check whether hindered diffusion, hydrodynamic wall effects, trapezoid pressure-flow, electrokinetic grid/Poisson-Boltzmann, optical/reference-field effects, wet pass/clogging/recovery/yield/detection must remain blocked.",
    ),
    (
        "implementation_risks_and_next_steps",
        "Give an engineering go-forward plan that would let Codex proceed for several gates without repeated review loops, including which evidence to add next and which decisions require manual authorization.",
    ),
)

AUTHORIZATION_SUPERSESSION_FIELDS = (
    "external_review_verdict",
    "external_review_artifact_sha256",
    "external_review_confirms_no_claim_promotion",
    "reviewed_candidate_manifest_sha256",
    "reviewed_summary_metrics_sha256",
    "reviewed_raw_metrics_sha256",
    "reviewed_commit_sha",
    "authorization_supersedes_no_auth_ledger_id",
    "authorization_supersedes_no_auth_ledger_sha256",
    "manual_authorization_record_sha256",
    "proof_registry_update_plan_sha256",
    "package_C_proof_artifact_registered",
    "proof_registration_authorized",
    "package_C_validation_status_pass_authorized",
    "package_C_proof_no_hindered_diffusion_claim",
    "package_C_proof_no_trapezoid_flow_solver_claim",
    "package_C_proof_no_electrokinetic_solver_claim",
    "package_C_proof_no_optical_solver_claim",
    "package_C_proof_no_wet_claim",
    "package_C_proof_no_prs_eas_numeric_output",
    "package_C_proof_no_route_yield_detection_claim",
)

REPORTS = {
    "485": "GATE32A_EXTERNAL_REVIEW_HANDOFF",
    "486": "GATE32B_GITHUB_VISIBLE_ARTIFACT_MAP",
    "487": "GATE32C_AUTHORIZATION_SUPERSESSION_PREFLIGHT",
    "488": "GATE32D_NO_PROOF_REGISTRATION_FIREWALL",
    "489": "GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate32 Package C external review handoff packet."
    )
    parser.add_argument(
        "--confirm-gate32-package-c-external-review-handoff",
        action="store_true",
    )
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


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def raw_url(path: Path) -> str:
    return f"{GITHUB_RAW_BASE}/{rel(path)}"


def blob_url(path: Path) -> str:
    return f"{GITHUB_BLOB_BASE}/{rel(path)}"


def gate30_31_summary() -> dict[str, Any]:
    return read_json(GATE30_31_STATUS).get("summary", {})


def gate27_contract_fields() -> set[str]:
    if not GATE27_PROOF_CONTRACT.exists():
        return set()
    return {
        row.get("required_field", "")
        for row in read_csv_rows(GATE27_PROOF_CONTRACT)
        if row.get("required_field")
    }


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_label": label,
                "path": rel(path),
                "exists": bool_text(exists),
                "sha256": sha256_file(path) if exists else "",
                "github_raw_url": raw_url(path),
                "github_blob_url": blob_url(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def github_path_map_rows() -> list[dict[str, str]]:
    review_paths = {
        "start_here_prompt": GATE30_31_PROMPT,
        "gate30_31_status": GATE30_31_STATUS,
        "gate30_31_summary_metrics": GATE30_31_SUMMARY_METRICS,
        "gate30_31_raw_metrics": GATE30_31_RAW_METRICS,
        "gate30_31_candidate_manifest": GATE30_31_CANDIDATE_MANIFEST,
        "gate30_31_evidence_map": GATE30_31_EVIDENCE_MAP,
        "gate30_31_no_proof_firewall": GATE30_31_FIREWALL,
        "gate30_31_parameter_matrix": GATE30_31_PARAMETER_MATRIX,
        "gate30_31_seed_matrix": GATE30_31_SEED_MATRIX,
        "geometry_implementation": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
        "trajectory_integration": PROJECT_ROOT / "nodi_simulator/trajectory.py",
        "gate30_31_builder": PROJECT_ROOT
        / "tools/audits/build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
        "gate30_31_tests": PROJECT_ROOT
        / "tests/test_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
        "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
        "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
    }
    return [
        {
            "review_order": str(idx),
            "review_label": label,
            "path": rel(path),
            "github_raw_url": raw_url(path),
            "github_blob_url": blob_url(path),
            "sha256": sha256_file(path) if path.exists() else "",
            "why_read": _why_read(label),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (label, path) in enumerate(review_paths.items(), start=1)
    ]


def _why_read(label: str) -> str:
    reasons = {
        "start_here_prompt": "copyable external review prompt and expected verdict format",
        "gate30_31_status": "candidate status and no-auth flags",
        "gate30_31_summary_metrics": "compact metrics and candidate-pass statuses",
        "gate30_31_raw_metrics": "full deterministic raw scenario metrics",
        "gate30_31_candidate_manifest": "52-field candidate-only proof contract values",
        "gate30_31_evidence_map": "hash mapping for candidate evidence fields",
        "gate30_31_no_proof_firewall": "authorization firewall",
        "gate30_31_parameter_matrix": "angle/depth/radius/dt grid",
        "gate30_31_seed_matrix": "deterministic seed matrix",
        "geometry_implementation": "reflection geometry and active-set update",
        "trajectory_integration": "trajectory-level claim labels and propagation boundary",
        "gate30_31_builder": "artifact generation logic",
        "gate30_31_tests": "candidate regression tests",
        "roadmap": "current route and claim boundaries",
        "audit_packet": "implementation audit and verification history",
    }
    return reasons.get(label, "supporting review artifact")


def review_intake_rows(summary: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "review_intake_id": "G32-EXT-REVIEW-001",
            "review_status": "pending_external_ai_review",
            "acceptable_external_verdicts": ";".join(ACCEPTABLE_EXTERNAL_VERDICTS),
            "current_candidate_disposition": str(summary.get("disposition", "")),
            "candidate_artifact_id": str(summary.get("artifact_id", "")),
            "all_candidate_metric_statuses_pass": bool_text(
                all(
                    summary.get(field) == "candidate_pass"
                    for field in (
                        "support_invariance_status",
                        "boundary_atom_status",
                        "equilibrium_uniformity_status",
                        "dt_halving_status",
                        "corner_active_set_status",
                        "one_wall_limit_status",
                        "rectangle_limit_status",
                        "angle_depth_mutation_status",
                    )
                )
            ),
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def research_synthesis_rows() -> list[dict[str, str]]:
    return [
        {
            "research_question_id": f"G32-RESEARCH-{idx:03d}",
            "topic": topic,
            "question_for_external_ai": question,
            "expected_external_ai_action": (
                "perform literature/technical search; cite sources; compare alternatives; "
                "return engineering recommendation and claim-boundary risks"
            ),
            "required_output_style": (
                "answer once in enough detail to support several future implementation gates"
            ),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (topic, question) in enumerate(RESEARCH_SYNTHESIS_QUESTIONS, start=1)
    ]


def authorization_supersession_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, field in enumerate(AUTHORIZATION_SUPERSESSION_FIELDS, start=1):
        current_status = "pending_external_review_and_manual_authorization"
        required_value = "nonempty_reviewed_sha_or_true"
        if field in {
            "package_C_proof_artifact_registered",
            "proof_registration_authorized",
            "package_C_validation_status_pass_authorized",
        }:
            current_status = "false_current_gate"
            required_value = "true_only_after_future_manual_authorization"
        elif field.startswith("package_C_proof_no_"):
            current_status = "true_no_claim_guard_required"
            required_value = "true"
        rows.append(
            {
                "preflight_id": f"G32-AUTH-PREFLIGHT-{idx:03d}",
                "required_field": field,
                "required_before_any_proof_registry_update": "true",
                "required_value": required_value,
                "current_status": current_status,
                "can_register_proof_now": "false",
                "can_mark_package_c_pass_now": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_GATE32_EXTERNAL_HANDOFF_NO_PROOF_REGISTRATION",
            "external_review_received": "false",
            "authorization_supersedes_no_auth_ledger": "false",
            "package_c_proof_artifact_registered": "false",
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_configuration_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "validated_brownian_solver_output_authorized": "false",
            "hindered_diffusion_claim_authorized": "false",
            "trapezoid_flow_solver_claim_authorized": "false",
            "electrokinetic_solver_claim_authorized": "false",
            "optical_solver_claim_authorized": "false",
            "wet_claim_authorized": "false",
            "wet_pass_probability_authorized": "false",
            "clogging_rate_authorized": "false",
            "time_to_clog_authorized": "false",
            "recovery_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
        }
    ]


def handoff_prompt_text(
    summary: dict[str, Any],
    path_rows: list[dict[str, str]],
    research_rows: list[dict[str, str]],
) -> str:
    key_paths = "\n".join(
        f"- `{row['review_label']}`: {row['github_raw_url']}"
        for row in path_rows
    )
    research_questions = "\n".join(
        f"{row['research_question_id']}. {row['question_for_external_ai']}"
        for row in research_rows
    )
    return f"""# Gate32 External AI Research Synthesis Handoff: NODI Package C Sidewall Reflection Candidate

You can only rely on GitHub-visible files. Do not assume access to local
Codex files, COMSOL models, `.mph` files, or untracked workspace artifacts.

This is not a narrow audit request. Please use your ability to search and
compare broader technical/literature sources. The goal is to answer enough
methodology, evidence, and next-step questions in one pass that Codex can move
several implementation gates forward without repeated back-and-forth review.

## Current candidate

- Disposition: `{DISPOSITION}`
- Gate30/31 source disposition: `{summary.get('disposition', '')}`
- Candidate artifact id: `{summary.get('artifact_id', '')}`
- Claim boundary: `{summary.get('claim_boundary', '')}`
- Scenario/open/blocked metric rows: `{summary.get('scenario_metric_rows')}` /
  `{summary.get('open_candidate_metric_rows')}` / `{summary.get('blocked_candidate_rows')}`
- dt-halving rows: `{summary.get('dt_halving_rows')}`
- Max boundary atom fraction: `{summary.get('max_boundary_atom_fraction')}`
- Max equilibrium uniformity distance: `{summary.get('max_equilibrium_uniformity_distance')}`
- dt-halving max distribution delta: `{summary.get('dt_halving_max_distribution_delta')}`

Candidate metric statuses:
- support invariance: `{summary.get('support_invariance_status')}`
- no boundary atom: `{summary.get('boundary_atom_status')}`
- equilibrium uniformity proxy: `{summary.get('equilibrium_uniformity_status')}`
- dt halving: `{summary.get('dt_halving_status')}`
- corner active set: `{summary.get('corner_active_set_status')}`
- one-wall limit: `{summary.get('one_wall_limit_status')}`
- rectangle limit: `{summary.get('rectangle_limit_status')}`
- angle/depth mutation: `{summary.get('angle_depth_mutation_status')}`

## Hard boundary

This is not Package C proof/pass registration. It is not runtime authorization,
PRS/EAS numeric output, NODI recomputation, COMSOL launch, `.mph` load,
route/yield/detection/wet/fabrication/production authorization, validated
hindered diffusion, trapezoid Poiseuille, electrokinetic solver, optical solver,
or true W_eff evidence.

Current authorization fields are all false:
- `proof_registration_authorized=false`
- `package_c_validation_status_pass_authorized=false`
- `runtime_allowed=false`
- `numeric_prs_eas_allowed=false`
- `comsol_launch_allowed=false`
- `mph_load_allowed=false`

## GitHub-visible files to review

{key_paths}

## Research synthesis questions

Please answer all of these with source-backed analysis and concrete engineering
recommendations:

{research_questions}

## Requested external verdict

Return exactly one of:
- `READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY`
- `NEEDS_MORE_CANDIDATE_EVIDENCE`
- `BLOCKED_CLAIM_PROMOTION`

Please close with:
1. A ranked list of evidence to add next, grouped into work that Codex can do
   immediately versus work that requires manual authorization, COMSOL, measured
   profiles, optical/electrokinetic solvers, or wet experiments.
2. A threshold/test-matrix recommendation for no-boundary-atom, equilibrium
   uniformity, dt convergence, one-wall limit, rectangle limit, and corner bias.
3. A claim-boundary risk list: any term, field, metric, or report language that
   could be misread as proof/pass registration, runtime authorization, wet
   performance, route selection, yield, or detection probability.
4. A go-forward route that should minimize future review loops.
"""


def build_payload() -> dict[str, Any]:
    summary = gate30_31_summary()
    contract_fields = gate27_contract_fields()
    source_rows = source_lock_rows()
    path_rows = github_path_map_rows()
    review_rows = review_intake_rows(summary)
    research_rows = research_synthesis_rows()
    auth_rows = authorization_supersession_rows()
    firewall = firewall_rows()
    payload_summary = {
        "disposition": DISPOSITION,
        "gate32_build_head": safe_git_head(),
        "gate30_31_disposition": summary.get("disposition", ""),
        "gate30_31_expected_disposition": EXPECTED_GATE30_31_DISPOSITION,
        "gate30_31_candidate_artifact_id": summary.get("artifact_id", ""),
        "gate30_31_candidate_only": summary.get("candidate_only") is True,
        "gate30_31_no_auth": summary.get("no_auth") is True,
        "gate30_31_metric_statuses_pass": review_rows[0]["all_candidate_metric_statuses_pass"] == "true",
        "gate27_proof_contract_field_rows": len(contract_fields),
        "gate27_required_proof_contract_field_rows": len(REQUIRED_PROOF_CONTRACT_FIELDS),
        "gate27_missing_required_proof_contract_fields": sorted(
            REQUIRED_PROOF_CONTRACT_FIELDS - contract_fields
        ),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "github_path_map_rows": len(path_rows),
        "research_synthesis_question_rows": len(research_rows),
        "authorization_supersession_preflight_rows": len(auth_rows),
        "external_review_received": False,
        "authorization_supersedes_no_auth_ledger": False,
        "proof_registration_authorized": False,
        "package_c_validation_status_pass_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "review_only": True,
        "no_auth": True,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": payload_summary,
        "gate30_31_summary": summary,
        "source_locks": source_rows,
        "github_path_map": path_rows,
        "external_review_intake": review_rows,
        "research_synthesis_agenda": research_rows,
        "authorization_supersession_preflight": auth_rows,
        "no_proof_firewall": firewall,
        "handoff_prompt_text": handoff_prompt_text(summary, path_rows, research_rows),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Gate30/31 disposition": s["gate30_31_disposition"] == EXPECTED_GATE30_31_DISPOSITION,
        "Gate30/31 candidate only": s["gate30_31_candidate_only"] is True,
        "Gate30/31 no auth": s["gate30_31_no_auth"] is True,
        "Gate30/31 metric statuses pass": s["gate30_31_metric_statuses_pass"] is True,
        "Gate27 proof contract complete": s["gate27_proof_contract_field_rows"]
        == len(REQUIRED_PROOF_CONTRACT_FIELDS),
        "Gate27 proof contract no missing": not s["gate27_missing_required_proof_contract_fields"],
        "Sources present": s["source_missing_rows"] == 0,
        "Path map present": s["github_path_map_rows"] >= 12,
        "Research synthesis agenda present": s["research_synthesis_question_rows"]
        == len(RESEARCH_SYNTHESIS_QUESTIONS),
        "Authorization preflight present": s["authorization_supersession_preflight_rows"]
        == len(AUTHORIZATION_SUPERSESSION_FIELDS),
        "External review pending": s["external_review_received"] is False,
        "No authorization supersession": s["authorization_supersedes_no_auth_ledger"] is False,
        "No proof registration": s["proof_registration_authorized"] is False,
        "No package C pass": s["package_c_validation_status_pass_authorized"] is False,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
    }
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
            "authorization_supersedes_no_auth_ledger",
            "external_review_received",
        }:
            checks[f"Firewall false: {key}"] = value == "false"
    return [label for label, ok in checks.items() if not ok]


def artifact_manifest_rows(
    paths: list[Path],
    *,
    self_manifest_path: Path | None = None,
) -> list[dict[str, str]]:
    rows = [
        {
            "artifact": path.name,
            "path": rel(path),
            "sha256": sha256_file(path) if path.exists() else "",
            "disposition": DISPOSITION,
            "policy_impact": "external_review_handoff_only_no_proof_registration",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for path in paths
    ]
    if self_manifest_path is not None:
        rows.append(
            {
                "artifact": self_manifest_path.name,
                "path": rel(self_manifest_path),
                "sha256": SELF_MANIFEST_SHA256,
                "disposition": DISPOSITION,
                "policy_impact": (
                    "manifest_self_row_no_recursive_sha_no_proof_registration"
                ),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: Path | None = None,
    report_dir: Path | None = None,
) -> dict[str, Path]:
    active_output_dir = output_dir or OUTPUT_DIR
    active_report_dir = report_dir or REPORT_DIR
    active_output_dir.mkdir(parents=True, exist_ok=True)
    active_report_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    prompt_path = active_output_dir / "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_REVIEW_HANDOFF_PROMPT_20260630.md"
    prompt_path.write_text(payload["handoff_prompt_text"], encoding="utf-8")
    generated.append(prompt_path)

    csv_specs = {
        "NODI_COMSOL_GATE32_SIDEWALL_SOURCE_LOCK_20260630.csv": payload["source_locks"],
        "NODI_COMSOL_GATE32_SIDEWALL_GITHUB_PATH_MAP_20260630.csv": payload["github_path_map"],
        "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_REVIEW_INTAKE_20260630.csv": payload["external_review_intake"],
        "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_RESEARCH_SYNTHESIS_AGENDA_20260630.csv": payload["research_synthesis_agenda"],
        "NODI_COMSOL_GATE32_SIDEWALL_AUTHORIZATION_SUPERSESSION_PREFLIGHT_20260630.csv": payload["authorization_supersession_preflight"],
        "NODI_COMSOL_GATE32_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv": payload["no_proof_firewall"],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    report_path = active_output_dir / "NODI_COMSOL_GATE32_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(
        report_path,
        {
            "summary": payload["summary"],
            "outputs": [path.name for path in generated],
        },
    )
    generated.append(report_path)

    status_path = active_output_dir / "NODI_COMSOL_GATE32_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "review_only": True,
            "no_auth": True,
            "proof_registration_authorized": False,
            "package_c_validation_status_pass_authorized": False,
        },
    )
    generated.append(status_path)

    master_md = active_output_dir / "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_REVIEW_HANDOFF_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate32 Sidewall Package C External Review Handoff",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Gate30/31 source disposition: `{payload['summary']['gate30_31_disposition']}`",
            f"- GitHub-visible path map rows: {payload['summary']['github_path_map_rows']}.",
            f"- Research synthesis questions: {payload['summary']['research_synthesis_question_rows']}.",
            f"- Authorization-supersession preflight rows: {payload['summary']['authorization_supersession_preflight_rows']}.",
            "- Boundary: external research/review handoff only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(master_md)

    for number, title in REPORTS.items():
        path = active_report_dir / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate32 disposition: `{DISPOSITION}`",
                f"- Gate30/31 candidate artifact id: `{payload['summary']['gate30_31_candidate_artifact_id']}`",
                f"- GitHub path map rows: {payload['summary']['github_path_map_rows']}.",
                f"- Research synthesis questions: {payload['summary']['research_synthesis_question_rows']}.",
                f"- Authorization-supersession preflight rows: {payload['summary']['authorization_supersession_preflight_rows']}.",
                "- Boundary: external research/review handoff only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection/wet/fab/production claims.",
                f"- Machine-readable support: `{rel(active_output_dir)}`.",
            ],
        )
        generated.append(path)

    manifest_path = active_output_dir / "NODI_COMSOL_GATE32_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(generated, self_manifest_path=manifest_path),
    )

    return {
        "prompt": prompt_path,
        "report": report_path,
        "status": status_path,
        "manifest": manifest_path,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate32_package_c_external_review_handoff:
        parser.error("--confirm-gate32-package-c-external-review-handoff is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
