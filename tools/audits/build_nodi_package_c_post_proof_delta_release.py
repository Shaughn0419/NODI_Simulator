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

DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1"
DISPOSITION = (
    "PASS_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_READY_FOR_COMSOL_CLEAN_MIRROR_NO_RUN"
)
BLOCKED_DISPOSITION = (
    "PARTIAL_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_FAIL_CLOSED_PROMOTION_OR_SOURCE_RISK"
)
ARTIFACT_ID = "PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_20260701"
CLAIM_BOUNDARY = (
    "post_proof_package_c_finite_step_reflection_surrogate_registered_"
    "not_runtime_not_comsol_not_solver_not_wet"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ALLOWED_USE = (
    "Post-proof Package C clean mirror release;finite-step reflection-surrogate "
    "proof-registration handoff;runtime-guard handoff;COMSOL clean mirror request;no-run "
    "source/evidence reconciliation"
)
BLOCKED_USE = (
    "runtime configuration;runtime execution;NODI runtime recomputation;sidewall PRS/EAS "
    "numeric output;COMSOL launch;.mph load;validated Brownian solver output beyond finite-step "
    "surrogate;validated hindered diffusion;trapezoid Poiseuille solver output;fixed-pressure "
    "q_ch output;flux-weighted sampling;electrokinetic grid output;optical solver output;true "
    "W_eff;reference strength claim;detector response claim;sidewall scattering claim;route_score;"
    "winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;clogging rate;"
    "time-to-clog;recovery;fabrication release;production ingestion"
)

PROOF_STATUS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_STATUS_20260701.json"
PROOF_MANIFEST = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_MANIFEST_20260701.csv"
PROOF_POST_GUARDS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_POST_GUARDS_20260701.csv"
PROOF_RUNTIME_BLOCKERS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_RUNTIME_BLOCKERS_20260701.csv"
RUNTIME_POLICY_STATUS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json"
RUNTIME_POLICY_ROWS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_ROWS_20260701.csv"
AUTH_LEDGER_STATUS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_STATUS_20260701.json"

SOURCE_FILES = {
    "proof_registration_status": PROOF_STATUS,
    "proof_registration_manifest": PROOF_MANIFEST,
    "proof_registration_post_guards": PROOF_POST_GUARDS,
    "proof_registration_runtime_blockers": PROOF_RUNTIME_BLOCKERS,
    "runtime_substep_policy_status": RUNTIME_POLICY_STATUS,
    "runtime_substep_policy_rows": RUNTIME_POLICY_ROWS,
    "user_authorization_ledger_status": AUTH_LEDGER_STATUS,
    "runtime_substep_policy_source": PROJECT_ROOT / "nodi_simulator/runtime_substep_policy.py",
    "trajectory_source": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "runtime_substep_policy_tests": PROJECT_ROOT / "tests/test_runtime_substep_policy.py",
    "proof_registration_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_proof_registration_artifact.py",
    "proof_registration_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_proof_registration_artifact.py",
    "post_proof_delta_release_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_post_proof_delta_release.py",
    "post_proof_delta_release_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_post_proof_delta_release.py",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}

OUTPUT_NAMES = {
    f"{PREFIX}_STATUS_20260701.json",
    f"{PREFIX}_SOURCE_LOCK_20260701.csv",
    f"{PREFIX}_RELEASE_SEAL_20260701.csv",
    f"{PREFIX}_POST_PROOF_GUARDS_20260701.csv",
    f"{PREFIX}_COMSOL_CLEAN_MIRROR_REQUEST_20260701.csv",
    f"{PREFIX}_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
    f"{PREFIX}_SUPERSEDED_CONTEXT_20260701.csv",
    f"{PREFIX}_SELF_REVIEW_20260701.csv",
    f"{PREFIX}_MANIFEST_20260701.csv",
    f"{PREFIX}_REPORT_20260701.json",
    "518_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_20260701.md",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "tools/audits/build_nodi_package_c_post_proof_delta_release.py",
    "tests/test_nodi_package_c_post_proof_delta_release.py",
}
UPSTREAM_RUNTIME_POLICY_PREFIX = (
    "reports/joint_interface_20260701/"
    "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_"
)
UPSTREAM_RUNTIME_POLICY_PUBLIC_REPORT = (
    "reports/514_NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_20260701.md"
)


def upstream_runtime_policy_output(path: str) -> bool:
    return path.startswith(UPSTREAM_RUNTIME_POLICY_PREFIX) or (
        path == UPSTREAM_RUNTIME_POLICY_PUBLIC_REPORT
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the post-proof Package C no-run clean mirror release."
    )
    parser.add_argument("--confirm-post-proof-delta-release", action="store_true")
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


def display_path(path: Path) -> str:
    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT).as_posix()
    return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def row_count(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix == ".csv":
        return str(len(read_csv_rows(path)))
    return "NA"


def git_path_from_status_line(line: str) -> str:
    return line[2:].strip().replace("\\", "/") if len(line) > 2 else line


def dirty_lines_for_release() -> list[str]:
    dirty: list[str] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if Path(path).name in OUTPUT_NAMES:
            continue
        if path in STALE_POST_RC2_PATHS:
            continue
        # The builder/test are dirty while constructing this package; the test suite
        # still validates all positive output flags before the files are committed.
        if path in BUILD_EDIT_PATHS:
            continue
        if upstream_runtime_policy_output(path):
            continue
        if not release_scoped_path(path):
            continue
        dirty.append(line)
    return dirty


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    if path in source_paths:
        return True
    return (
        path.startswith("tools/audits/build_nodi_package_c_post_proof_delta_release")
        or path.startswith("tests/test_nodi_package_c_post_proof_delta_release")
        or path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_")
        or path == "reports/518_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if Path(path).name in OUTPUT_NAMES:
            classification = "post_proof_release_output"
            release_decision = "included_or_rewritten_by_post_proof_release"
        elif path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock_recorded_separately"
        elif path in BUILD_EDIT_PATHS:
            classification = "post_proof_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif upstream_runtime_policy_output(path):
            classification = "source_locked_upstream_runtime_policy_dirty_context"
            release_decision = "included_in_chain_rebuild_not_post_proof_blocker"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_post_proof_release"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_post_proof_release_pass_not_source_locked"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def superseded_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    status_by_path = {git_path_from_status_line(line): line[:2] for line in git_status_lines()}
    for path in sorted(STALE_POST_RC2_PATHS):
        abs_path = PROJECT_ROOT / path
        exists = abs_path.exists()
        rows.append(
            {
                "path": path,
                "exists": str(exists).lower(),
                "git_status": status_by_path.get(path, "not_present"),
                "classification": "superseded_untracked_post_rc2_no_auth_no_proof_context",
                "release_decision": "excluded_from_post_proof_release_source_lock",
                "reason": "old no-auth/no-proof semantics conflict with current proof-registered status",
            }
        )
    return rows


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def release_seal_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "seal_id": ARTIFACT_ID,
            "current_head": summary["current_head"],
            "reviewed_evidence_commit_sha": summary["reviewed_evidence_commit_sha"],
            "proof_registration_authorized": str(summary["proof_registration_authorized"]).lower(),
            "package_c_proof_artifact_registered": str(summary["package_c_proof_artifact_registered"]).lower(),
            "package_c_validation_status_pass_current": str(
                summary["package_c_validation_status_pass_current"]
            ).lower(),
            "package_c_validation_status_pass_scope": summary[
                "package_c_validation_status_pass_scope"
            ],
            "runtime_allowed": "false",
            "nodi_runtime_recomputation_started": "false",
            "numeric_prs_eas_allowed": "false",
            "comsol_launch_allowed": "false",
            "mph_load_allowed": "false",
            "solver_wet_claim_allowed": "false",
            "route_yield_detection_claim_allowed": "false",
            "fabrication_or_production_release_allowed": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def post_proof_guard_rows() -> list[dict[str, str]]:
    guards = [
        ("runtime_allowed", "false", "runtime_execution_packet_required"),
        ("runtime_execution_started", "false", "no_runtime_started_by_post_proof_release"),
        ("nodi_runtime_recomputation_started", "false", "no_nodi_recompute_started"),
        ("sidewall_prs_eas_numeric_output_current", "false", "package_d_precheck_required"),
        ("numeric_prs_eas_allowed", "false", "package_d_precheck_required"),
        ("comsol_launch_allowed", "false", "separate_comsol_execution_packet_required"),
        ("comsol_launch_started", "false", "no_comsol_launch_started"),
        ("mph_load_allowed", "false", "separate_mph_inspection_packet_required"),
        ("mph_load_started", "false", "no_mph_load_started"),
        ("validated_brownian_solver_output_current", "false", "finite_step_surrogate_only"),
        ("validated_hindered_diffusion_claim_current", "false", "hydrodynamic_solver_required"),
        ("trapezoid_flow_solver_output_current", "false", "flow_solver_branch_required"),
        ("electrokinetic_solver_output_current", "false", "electrokinetic_solver_branch_required"),
        ("optical_solver_output_current", "false", "optical_solver_or_calibration_required"),
        ("wet_claim_current", "false", "wet_experimental_evidence_required"),
        ("route_yield_detection_claim_current", "false", "route_yield_detection_blocked"),
        ("fabrication_or_production_release_current", "false", "production_ingestion_blocked"),
    ]
    return [
        {
            "guard_field": field,
            "guard_value": value,
            "guard_status": status,
            "hard_fail_if": f"{field}_true_in_post_proof_delta_release",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for field, value, status in guards
    ]


def comsol_mirror_request_rows(current_head: str) -> list[dict[str, str]]:
    rows = [
        (
            "MIRROR_PROOF_REGISTERED_FINITE_STEP_SURROGATE_ONLY",
            "Mirror NODI Package C proof registration as finite-step reflection-surrogate evidence only.",
        ),
        (
            "MIRROR_RUNTIME_GUARD_NO_RUN",
            "Mirror the runtime/substep guard as a no-run policy handoff, not runtime execution.",
        ),
        (
            "FUTURE_COMSOL_RUN_REQUIRED_NOT_STARTED",
            "Classify future COMSOL solver evidence as a separate branch; do not launch COMSOL now.",
        ),
        (
            "FUTURE_MPH_LOAD_REQUIRED_NOT_STARTED",
            "Classify future .mph inspection as a separate branch; do not load any .mph now.",
        ),
        (
            "FUTURE_SOLVER_WET_BRANCH_REQUIRED_NOT_STARTED",
            "Keep flow/electrokinetic/optical/wet claims out of this post-proof release.",
        ),
        (
            "BLOCKED_AS_EXPECTED",
            "Treat route_score, winner, JRC, q_ch weighting, yield, detection_probability, and production claims as blocked.",
        ),
    ]
    return [
        {
            "request_id": f"POST-PROOF-MIRROR-{idx:03d}",
            "target_nodi_commit": current_head,
            "expected_comsol_response_enum": enum,
            "question": question,
            "allowed_action": "clean_mirror_no_run_no_mph_no_numeric_output",
            "forbidden_action": (
                "COMSOL launch;.mph load;runtime execution;new solver values;numeric PRS/EAS;"
                "q_ch/JRC/route/yield/detection/wet/fabrication/production claims"
            ),
        }
        for idx, (enum, question) in enumerate(rows, start=1)
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "proof registration status is positive but narrow",
        "runtime and COMSOL are still blocked",
        "runtime guard is handed off as policy, not execution",
        "old post-RC2 no-auth/no-proof files are excluded",
        "COMSOL mirror asks for no-run receipt only",
        "solver/wet branches remain future evidence branches",
        "forbidden route/yield/detection/q_ch fields remain blocked",
        "source lock covers code, tests, and proof artifacts",
    ]
    return [
        {
            "review_id": f"POST-PROOF-SELF-{idx:02d}",
            "dimension": topic,
            "verdict": "PASS_POST_PROOF_NO_RUN_BOUNDARY",
            "notes": "No runtime/COMSOL/solver/wet/route/yield/detection promotion accepted.",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "summary": {
            "proof": payload["summary"]["package_c_proof_artifact_registered"],
            "scope": payload["summary"]["package_c_validation_status_pass_scope"],
            "runtime": payload["summary"]["runtime_allowed"],
            "comsol": payload["summary"]["comsol_launch_allowed"],
            "mph": payload["summary"]["mph_load_allowed"],
        },
        "sources": [(row["source_id"], row["sha256"]) for row in payload["source_lock"]],
        "guards": [(row["guard_field"], row["guard_value"]) for row in payload["post_proof_guards"]],
        "mirror": [row["expected_comsol_response_enum"] for row in payload["comsol_request"]],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    proof = load_json(PROOF_STATUS)
    runtime_policy = load_json(RUNTIME_POLICY_STATUS)
    source_lock = source_lock_rows()
    dirty = dirty_lines_for_release()
    dirty_context = dirty_context_rows()
    current_head = git_head()
    required_false = [
        "runtime_allowed",
        "numeric_prs_eas_allowed",
        "comsol_launch_allowed",
        "mph_load_allowed",
        "runtime_execution_started",
        "nodi_runtime_recomputation_started",
        "comsol_launch_started",
        "mph_load_started",
        "validated_brownian_solver_output_current",
        "validated_hindered_diffusion_claim_current",
        "trapezoid_flow_solver_output_current",
        "electrokinetic_solver_output_current",
        "optical_solver_output_current",
        "wet_claim_current",
        "route_yield_detection_claim_current",
        "fabrication_or_production_release_current",
    ]
    guards_false = all(proof.get(field) is False for field in required_false)
    source_missing_rows = sum(row["exists"] != "true" for row in source_lock)
    stale_rows = superseded_context_rows()
    stale_present = sum(row["exists"] == "true" for row in stale_rows)
    status = (
        DISPOSITION
        if not dirty
        and source_missing_rows == 0
        and proof.get("package_c_proof_artifact_registered") is True
        and proof.get("package_c_validation_status_pass_current") is True
        and proof.get("package_c_validation_status_pass_scope")
        == "finite_step_reflection_surrogate_evidence_only"
        and guards_false
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": current_head,
        "branch": git_branch(),
        "reviewed_evidence_commit_sha": proof.get("reviewed_evidence_commit_sha", ""),
        "proof_registration_authorized": proof.get("proof_registration_authorized") is True,
        "proof_registration_authorization_source": proof.get(
            "proof_registration_authorization_source", ""
        ),
        "package_c_proof_artifact_registered": proof.get(
            "package_c_proof_artifact_registered"
        )
        is True,
        "package_c_validation_status_pass_current": proof.get(
            "package_c_validation_status_pass_current"
        )
        is True,
        "package_c_validation_status_pass_scope": proof.get(
            "package_c_validation_status_pass_scope", ""
        ),
        "proof_registration_disposition": proof.get("disposition", ""),
        "runtime_policy_disposition": runtime_policy.get("disposition", ""),
        "runtime_policy_gap_rows": proof.get("runtime_policy_gap_rows", ""),
        "runtime_guard_policy_version": "trapezoid_runtime_substep_guard_v1",
        "dirty_count_after_exclusions": len(dirty),
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": sum(
            row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
        ),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing_rows,
        "superseded_post_rc2_untracked_rows": stale_present,
        "runtime_allowed": False,
        "runtime_execution_started": False,
        "nodi_runtime_recomputation_started": False,
        "numeric_prs_eas_allowed": False,
        "sidewall_prs_eas_numeric_output_current": False,
        "comsol_launch_allowed": False,
        "comsol_launch_started": False,
        "mph_load_allowed": False,
        "mph_load_started": False,
        "validated_brownian_solver_output_current": False,
        "validated_hindered_diffusion_claim_current": False,
        "trapezoid_flow_solver_output_current": False,
        "electrokinetic_solver_output_current": False,
        "optical_solver_output_current": False,
        "wet_claim_current": False,
        "route_yield_detection_claim_current": False,
        "fabrication_or_production_release_current": False,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "source_lock": source_lock,
        "release_seal": release_seal_rows(summary),
        "post_proof_guards": post_proof_guard_rows(),
        "comsol_request": comsol_mirror_request_rows(current_head),
        "dirty_context": dirty_context,
        "superseded_context": stale_rows,
        "self_review": self_review_rows(),
        "dirty_lines": dirty,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": s["disposition"] == DISPOSITION,
        "source lock complete": s["source_missing_rows"] == 0,
        "dirty lines excluded": s["dirty_count_after_exclusions"] == 0,
        "proof registration authorized": s["proof_registration_authorized"] is True,
        "proof artifact registered": s["package_c_proof_artifact_registered"] is True,
        "finite-step pass current": s["package_c_validation_status_pass_current"] is True,
        "finite-step scope only": (
            s["package_c_validation_status_pass_scope"]
            == "finite_step_reflection_surrogate_evidence_only"
        ),
        "runtime blocked": s["runtime_allowed"] is False,
        "numeric PRS/EAS blocked": s["numeric_prs_eas_allowed"] is False,
        "COMSOL blocked": s["comsol_launch_allowed"] is False,
        "MPH blocked": s["mph_load_allowed"] is False,
        "solver/wet blocked": s["wet_claim_current"] is False
        and s["trapezoid_flow_solver_output_current"] is False
        and s["optical_solver_output_current"] is False,
    }
    for row in payload["post_proof_guards"]:
        checks[f"guard false: {row['guard_field']}"] = row["guard_value"] == "false"
    for label, ok in checks.items():
        if not ok:
            failures.append(label)
    return failures


def mirror_request_md(rows: list[dict[str, str]]) -> str:
    lines = [
        "# NODI Package C Post-Proof Delta Clean Mirror Request V1",
        "",
        "This request asks COMSOL-side readers to mirror the registered Package C finite-step reflection-surrogate proof boundary. It does not authorize COMSOL launch, `.mph` load, runtime execution, numeric PRS/EAS, solver/wet claims, or route/yield/detection conclusions.",
        "",
        "| request_id | expected_response | question |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['request_id']} | {row['expected_comsol_response_enum']} | {row['question']} |"
        )
    return "\n".join(lines) + "\n"


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Post-Proof Delta Release V1",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Reviewed evidence commit: `{s['reviewed_evidence_commit_sha']}`.",
            f"- Semantic digest: `{s['semantic_digest']}`.",
            "- Package C proof artifact registered: `true`.",
            "- Package C validation status pass current: `true`, scoped to `finite_step_reflection_surrogate_evidence_only`.",
            "- Runtime, NODI recomputation, COMSOL launch, `.mph` load, numeric PRS/EAS, solver/wet, route/yield/detection, fabrication, and production remain blocked.",
            f"- Runtime policy gap rows remain explicit: `{s['runtime_policy_gap_rows']}`.",
            f"- Release-scoped dirty blocker rows: `{s['release_scoped_dirty_blocker_rows']}`.",
            f"- Non-release dirty context rows recorded but not source-locked: `{s['non_release_dirty_context_rows']}`.",
            f"- Superseded untracked post-RC2 context rows excluded from source lock: `{s['superseded_post_rc2_untracked_rows']}`.",
            "",
        ]
    )


def artifact_manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "post_proof_clean_mirror_no_run",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    rows.append(
        {
            "artifact": manifest_path.name,
            "path": display_path(manifest_path),
            "sha256": SELF_MANIFEST_SHA256,
            "disposition": DISPOSITION,
            "policy_impact": "manifest_self_row_no_recursive_sha",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
    report_dir: Path = REPORT_DIR,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_RELEASE_SEAL_20260701.csv": payload["release_seal"],
        f"{PREFIX}_POST_PROOF_GUARDS_20260701.csv": payload["post_proof_guards"],
        f"{PREFIX}_COMSOL_CLEAN_MIRROR_REQUEST_20260701.csv": payload["comsol_request"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
        f"{PREFIX}_SUPERSEDED_CONTEXT_20260701.csv": payload["superseded_context"],
        f"{PREFIX}_SELF_REVIEW_20260701.csv": payload["self_review"],
    }
    for filename, rows in csv_payloads.items():
        path = output_dir / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = output_dir / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    mirror_md_path = output_dir / f"{PREFIX}_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md"
    mirror_md_path.write_text(
        mirror_request_md(payload["comsol_request"]),
        encoding="utf-8",
        newline="\n",
    )
    paths.append(mirror_md_path)

    report_json_path = output_dir / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_json_path, payload)
    paths.append(report_json_path)

    public_report = report_dir / "518_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = output_dir / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, artifact_manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_post_proof_delta_release:
        parser.error("--confirm-post-proof-delta-release is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
