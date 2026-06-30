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


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

EXPECTED_GATE24_DISPOSITION = "NODI_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_READY_NO_AUTH"
DISPOSITION = "NODI_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_PACKET_READY_NO_AUTH"
ALLOWED_USE = "review-only sidewall Package C physics design packet;external review prompt;no-run no-auth"
BLOCKED_USE = (
    "Package C physics implementation;proof registry pass;runtime configuration;sidewall PRS/EAS numeric output;"
    "NODI runtime recomputation;COMSOL launch;.mph load;validated Brownian solver claim;validated hindered diffusion;"
    "trapezoid Poiseuille/q_ch;flux-weighted sampling;electrokinetic grid output;optical solver output;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;clogging rate;"
    "time-to-clog;recovery;fabrication release;production ingestion"
)

GATE24_FILES = {
    "status": OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_MANIFEST_20260630.csv",
    "auth_gate": OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_GATE_RECORD_20260630.csv",
    "phrase_eval": OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_AUTHORIZATION_PHRASE_EVALUATION_20260630.csv",
    "firewall": OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_NO_AUTH_FIREWALL_20260630.csv",
}

REPORTS = {
    "451": "GATE25A_GATE24_SOURCE_LOCK",
    "452": "GATE25B_PACKAGE_C_PHYSICS_DESIGN_SCOPE",
    "453": "GATE25C_MODEL_RISK_AND_TEST_QUESTIONS",
    "454": "GATE25D_EXTERNAL_AI_REVIEW_PROMPT",
    "455": "GATE25E_NO_AUTH_AND_FUTURE_GO_NO_GO",
    "456": "GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate25 Package C design review packet.")
    parser.add_argument("--confirm-gate25-package-c-design-review", action="store_true")
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


def gate24_source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, (label, path) in enumerate(GATE24_FILES.items(), start=1):
        exists = path.exists()
        rows.append(
            {
                "source_lock_id": f"G25A-GATE24-{idx:03d}",
                "source_gate": "Gate24",
                "source_label": label,
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "exists": bool_text(exists),
                "row_count": csv_count(path) if exists else "MISSING",
                "sha256": sha256_file(path) if exists else "MISSING",
                "lock_status": "MATCH" if exists else "MISSING_GATE24_SOURCE",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def design_scope_rows() -> list[dict[str, str]]:
    return [
        {
            "design_id": "G25B-DESIGN-001",
            "package_c_component": "trajectory_boundary",
            "current_nodi_state": "trapezoid_center_support_projection_boundary_v1",
            "current_claim_level": "sidewall_projection_boundary_surrogate_not_specular_reflection",
            "design_review_question": "Should Package C use reflected Brownian motion on the particle-center offset trapezoid with wall-normal reflection, and what time-step/corner rules preserve support and equilibrium?",
            "implementation_permission": "false",
            "required_before_implementation": "external_physics_review;unit_tests;mutation_tests;explicit_future_authorization",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "design_id": "G25B-DESIGN-002",
            "package_c_component": "near_wall_diffusion",
            "current_nodi_state": "blocked_when_diffusion_hindrance_model_not_none_under_trapezoid",
            "current_claim_level": "no_validated_hindered_diffusion",
            "design_review_question": "Which wall-normal hindered-diffusion approximation, if any, is acceptable for sloped walls, multi-wall corners, finite particle radius, and sharp/rounded profile uncertainty?",
            "implementation_permission": "false",
            "required_before_implementation": "claim_level_decision;corner_policy;validation_fixtures;explicit_future_authorization",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "design_id": "G25B-DESIGN-003",
            "package_c_component": "flow_model",
            "current_nodi_state": "plug_flow_allowed_as_geometry_independent_surrogate;parabolic_rect_and_rect_series_blocked",
            "current_claim_level": "not_trapezoid_poiseuille_not_qch",
            "design_review_question": "Can any trapezoid-compatible velocity field be introduced without becoming q_ch weighting or a false Poiseuille claim, and how must fixed-velocity versus fixed-pressure outputs be separated?",
            "implementation_permission": "false",
            "required_before_implementation": "flow_control_mode_contract;flow_field_validation;no_qch_guard;explicit_future_authorization",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "design_id": "G25B-DESIGN-004",
            "package_c_component": "electrokinetic_transport",
            "current_nodi_state": "rectangular wall-distance grid blocked under trapezoid",
            "current_claim_level": "blocked_trapezoid_geometry_not_propagated_to_electrokinetic_transport",
            "design_review_question": "What profile-aware grid or solver boundary is required before electrokinetic wall-distance metrics can be sidewall-aware rather than rectangular proxies?",
            "implementation_permission": "false",
            "required_before_implementation": "grid_geometry_design;profile_hash_binding;validation_fixtures;explicit_future_authorization",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "design_id": "G25B-DESIGN-005",
            "package_c_component": "optical_reference_field",
            "current_nodi_state": "rectangular/reference proxy or geometry-independent audit under trapezoid",
            "current_claim_level": "not_optical_solver_output",
            "design_review_question": "Which optical/reference-field effects require a real solver before W_eff, reference strength, sidewall scattering, or detector response can be claimed?",
            "implementation_permission": "false",
            "required_before_implementation": "solver_required_register;not_true_W_eff_guard;external_review;explicit_future_authorization",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
    ]


def review_question_rows() -> list[dict[str, str]]:
    questions = [
        (
            "G25C-QUESTION-001",
            "coordinate_and_geometry",
            "Confirm formulas: u=z+H/2, W(u)=W_top-2*u*tan(alpha), W_bottom_unclipped=W_top-2*H*tan(alpha), side distances divided by sqrt(1+k^2), and particle-center side exclusion a*sqrt(1+k^2).",
        ),
        (
            "G25C-QUESTION-002",
            "specular_or_skorokhod_reflection",
            "Decide whether specular reflection, projected Brownian reflection, or Skorokhod normal reflection is the right numerical model for particle-center boundaries in a trapezoid.",
        ),
        (
            "G25C-QUESTION-003",
            "equilibrium_and_time_step_tests",
            "Specify tests proving particle centers remain in support, equilibrium does not bias to walls or corners, and angle/depth mutation changes wall-distance distributions and signatures.",
        ),
        (
            "G25C-QUESTION-004",
            "claim_level",
            "State which outputs are descriptor_only, surrogate_sensitivity_only, solver_required, or still blocked; forbid wet/clogging/recovery/yield/detection claims.",
        ),
        (
            "G25C-QUESTION-005",
            "rectangle_preservation",
            "Confirm ideal_rectangle remains a native path and is not forced through trapezoid fields or Package C semantics.",
        ),
    ]
    return [
        {
            "question_id": qid,
            "question_family": family,
            "question": question,
            "review_required": "true",
            "implementation_permission": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for qid, family, question in questions
    ]


def no_auth_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G25E-NOAUTH-001",
            "package_c_physics_implementation_authorized": "false",
            "package_c_proof_registry_pass_authorized": "false",
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
            "firewall_status": "PASS_NO_AUTH_DESIGN_REVIEW_ONLY",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def external_prompt_text() -> str:
    return """# External AI Prompt - NODI Sidewall Package C Physics Design Review

You are reviewing a NODI sidewall-angle Package C design packet. Review only.
Do not request or assume NODI recomputation, COMSOL launch, `.mph` loading,
sidewall PRS/EAS numeric generation, q_ch weighting, JRC, route_score, route
winner, yield, detection_probability, wet-pass probability, clogging rate,
time-to-clog, recovery, fabrication release, or production ingestion.

Visibility note: you may only see files on GitHub. Treat the local facts below
as the verified local packet; do not assume unavailable COMSOL or local CSV
contents are absent.

Primary GitHub-visible files to inspect:
- `nodi_simulator/cross_section_geometry.py`
- `nodi_simulator/trajectory.py`
- `nodi_simulator/utils.py`
- `nodi_simulator/fluidic_resistance.py`
- `nodi_simulator/electrokinetic_transport.py`
- `nodi_simulator/reference_field.py`
- `nodi_simulator/nodi_comsol_next_artifacts.py`
- `reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md`
- `reports/345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md`
- `reports/450_NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_MASTER_REPORT_20260630.md`
- `reports/456_NODI_COMSOL_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_MASTER_REPORT_20260630.md`

Current verified NODI state:
- `ideal_rectangle` remains a native rectangular path.
- `trapezoid_tapered_sidewalls` exists for descriptor geometry, particle-center
  support, initial-position sampling, geometry-only wall-distance diagnostics,
  observation signatures, and PRS/EAS v2 no-claim validators.
- Current trapezoid trajectory diffusion uses
  `trapezoid_center_support_projection_boundary_v1` and is explicitly
  `sidewall_projection_boundary_surrogate_not_specular_reflection`.
- Trapezoid hindered diffusion is blocked when `diffusion_hindrance_model` is
  not `none`.
- Trapezoid flow currently allows only plug-flow geometry-independent surrogate
  semantics; `parabolic_rect` and `rect_series` are blocked under trapezoid.
- Electrokinetic rectangular wall-distance grids are blocked under trapezoid.
- Reference/optical fields under trapezoid are proxy or audit paths, not optical
  solver output and not true W_eff.
- Gate24 records the future phrase `authorize NODI sidewall Package C physics
  preauthorization`, but exact phrase matching still returns `authorized_now=false`.

Geometry conventions and formulas to review:
- Coordinates: x is channel width, y is flow direction, z is centered depth.
  Package C formulas use `u = z + H/2`, measured downward from the top.
- COMSOL sidewall angle `theta` is from the horizontal substrate; `90 deg` is
  vertical. NODI taper angle `alpha = 90 deg - theta` is from vertical.
- `k = tan(alpha)`.
- Symmetric trapezoid local width: `W(u) = W_top - 2*k*u`.
- Unclipped bottom width: `W_bottom_unclipped = W_top - 2*k*H`.
- Closure is `geometry_closed` when `W_bottom_unclipped <= 0` or
  `H >= W_top/(2*k)`. Negative bottom width must be preserved in descriptor
  space, not silently clipped into an open runtime aperture.
- Side-wall signed distances for centerline x and top-depth u use
  `h(u)=W(u)/2`, `d_left=(x+h(u))/sqrt(1+k^2)`, and
  `d_right=(h(u)-x)/sqrt(1+k^2)`.
- Particle radius `a` center support excludes top/bottom by `a` and sidewalls by
  `a*sqrt(1+k^2)`, so local center x bounds are
  `abs(x) <= h(u) - a*sqrt(1+k^2)` with blocked slices when the right side is
  nonpositive.

Please review:
1. For Brownian trajectories in the particle-center offset trapezoid, should
   Package C use specular reflection, projected Brownian reflection, or
   Skorokhod normal reflection? Give the correct wall-normal update rule,
   corner handling, and time-step stability tests.
2. What tests prove the reflected process stays inside support and does not
   create an artificial wall/corner bias? Include angle/depth mutation tests and
   equilibrium distribution checks.
3. Is any single-wall hindered-diffusion formula acceptable for sloped walls and
   finite particles, or must multi-wall/corner/roughness/profile cases remain
   `solver_required` or `surrogate_sensitivity_only`?
4. What is the safest Package C flow-model plan? Distinguish fixed-velocity
   plug-flow audit, trapezoid velocity-field surrogate, fixed-pressure hydraulic
   resistance, and forbidden q_ch weighting.
5. What electrokinetic grid/profile-aware requirements are needed before
   trapezoid wall-distance electrokinetic metrics can be claimed?
6. What optical/reference-field effects require an actual solver before any
   W_eff, reference strength, detector response, or sidewall scattering claim?
7. Are any schema fields or validators missing before implementation begins?

Return:
- `READY_FOR_IMPLEMENTATION_DESIGN_ONLY` if the design can be implemented later
  after explicit authorization, with required tests listed.
- `NEEDS_REVISION_BEFORE_IMPLEMENTATION` if formulas, claims, or tests are
  incomplete.
- `BLOCKED_PHYSICS_UNSAFE` if the proposed Package C path would create false
  physical claims or route/fabrication conclusions.
"""


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G25-MANIFEST-{idx:03d}",
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
    gate24_status = read_json(GATE24_FILES["status"])
    current_head = safe_git_head(PROJECT_ROOT)
    gate24_summary = gate24_status.get("summary", {})
    source_locks = gate24_source_lock_rows()
    scope = design_scope_rows()
    questions = review_question_rows()
    firewall = no_auth_firewall_rows()
    summary = {
        "disposition": DISPOSITION,
        "gate25_build_head": current_head,
        "gate24_build_head": gate24_summary.get("gate24_build_head", ""),
        "gate24_head_is_ancestor_of_current": git_is_ancestor(gate24_summary.get("gate24_build_head", ""), current_head, PROJECT_ROOT),
        "gate24_disposition": gate24_status.get("disposition", ""),
        "gate24_no_auth": gate24_status.get("no_auth", False),
        "gate24_review_only": gate24_status.get("review_only", False),
        "gate24_source_lock_rows": len(source_locks),
        "gate24_missing_sources": sum(row["lock_status"] == "MISSING_GATE24_SOURCE" for row in source_locks),
        "design_scope_rows": len(scope),
        "review_question_rows": len(questions),
        "implementation_permission_rows": sum(row.get("implementation_permission") == "true" for row in scope + questions),
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_NO_AUTH_DESIGN_REVIEW_ONLY" else 1,
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "gate24_source_locks": source_locks,
        "design_scope": scope,
        "review_questions": questions,
        "no_auth_firewall": firewall,
        "external_prompt": external_prompt_text(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "Gate24 head ancestry": s["gate24_head_is_ancestor_of_current"] is True,
        "Gate24 disposition": s["gate24_disposition"] == EXPECTED_GATE24_DISPOSITION,
        "Gate24 no-auth": s["gate24_no_auth"] is True,
        "Gate24 review-only": s["gate24_review_only"] is True,
        "Gate24 sources present": s["gate24_source_lock_rows"] == len(GATE24_FILES),
        "Gate24 missing sources": s["gate24_missing_sources"] == 0,
        "Design scope rows": s["design_scope_rows"] >= 5,
        "Review question rows": s["review_question_rows"] >= 5,
        "No implementation permission": s["implementation_permission_rows"] == 0,
        "No-auth firewall": s["no_auth_firewall_failures"] == 0,
    }
    prompt = payload["external_prompt"]
    required_prompt_terms = [
        "authorized_now=false",
        "sidewall_projection_boundary_surrogate_not_specular_reflection",
        "W_bottom_unclipped",
        "a*sqrt(1+k^2)",
        "Do not request or assume NODI recomputation",
        "READY_FOR_IMPLEMENTATION_DESIGN_ONLY",
    ]
    for term in required_prompt_terms:
        checks[f"External prompt contains {term}"] = term in prompt
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE25_SIDEWALL_GATE24_SOURCE_LOCK_20260630.csv": payload["gate24_source_locks"],
        "NODI_COMSOL_GATE25_SIDEWALL_PACKAGE_C_DESIGN_SCOPE_20260630.csv": payload["design_scope"],
        "NODI_COMSOL_GATE25_SIDEWALL_PACKAGE_C_REVIEW_QUESTIONS_20260630.csv": payload["review_questions"],
        "NODI_COMSOL_GATE25_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    prompt_path = OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_EXTERNAL_AI_PROMPT_20260630.md"
    prompt_path.write_text(payload["external_prompt"], encoding="utf-8")
    generated.append(prompt_path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs) + [prompt_path.name]})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate25 Sidewall Package C Design Review Packet",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Gate24 source missing rows: {payload['summary']['gate24_missing_sources']}",
            f"- Design scope rows / review question rows: {payload['summary']['design_scope_rows']}/{payload['summary']['review_question_rows']}",
            "- External AI prompt is self-contained and includes local geometry formulas, claim limits, and no-run boundaries.",
            "- Boundary: design review only; no Package C physics implementation, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        lines = [
            f"- Gate25 disposition: `{DISPOSITION}`",
            f"- Gate24 source missing rows: {payload['summary']['gate24_missing_sources']}.",
            f"- Design scope rows / review question rows: {payload['summary']['design_scope_rows']}/{payload['summary']['review_question_rows']}.",
            "- Package C remains design-review-only; external review is required before any implementation.",
            "- Boundary: no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
            f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
        ]
        if number == "454":
            lines.append("- Copyable prompt: `reports/joint_interface_20260630/NODI_COMSOL_GATE25_SIDEWALL_EXTERNAL_AI_PROMPT_20260630.md`.")
        write_md(path, title.replace("_", " "), lines)
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate25_package_c_design_review:
        parser.error("--confirm-gate25-package-c-design-review is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_PACKET")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
