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

PREFIX = "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT"
DISPOSITION = "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_READY_FOR_EXECUTION_PACKETS"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_FAIL_CLOSED"
ARTIFACT_ID = "PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_20260701"
CLAIM_BOUNDARY = (
    "authorized_to_implement_runtime_solver_wet_route_evidence_"
    "not_promoted_to_final_claims_without_branch_evidence"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ALLOWED_USE = (
    "Package C mainline advancement;runtime/substep execution packet planning;"
    "solver branch planning;wet evidence branch planning;route/yield/detection promotion planning"
)
BLOCKED_USE = (
    "unreviewed final claim promotion;unhashed runtime result promotion;unhashed COMSOL result promotion;"
    "unhashed .mph evidence promotion;unhashed solver output promotion;unhashed wet claim promotion;"
    "route_score/winner/JRC/q_ch/yield/detection_probability promotion without promotion contract pass;"
    "fabrication release;production ingestion"
)

POST_PROOF_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_STATUS_20260701.json"
POST_PROOF_GUARDS = OUTPUT_DIR / "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_POST_PROOF_GUARDS_20260701.csv"
POST_PROOF_MANIFEST = OUTPUT_DIR / "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_MANIFEST_20260701.csv"
PROOF_STATUS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_STATUS_20260701.json"
RUNTIME_POLICY_STATUS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json"
USER_AUTH_LEDGER_STATUS = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_STATUS_20260701.json"

SOURCE_FILES = {
    "post_proof_status": POST_PROOF_STATUS,
    "post_proof_guards": POST_PROOF_GUARDS,
    "post_proof_manifest": POST_PROOF_MANIFEST,
    "proof_registration_status": PROOF_STATUS,
    "runtime_substep_policy_status": RUNTIME_POLICY_STATUS,
    "user_authorization_ledger_status": USER_AUTH_LEDGER_STATUS,
    "runtime_substep_policy_source": PROJECT_ROOT / "nodi_simulator/runtime_substep_policy.py",
    "trajectory_source": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "authorized_mainline_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_authorized_mainline_advancement.py",
    "authorized_mainline_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_authorized_mainline_advancement.py",
}

OUTPUT_NAMES = {
    f"{PREFIX}_STATUS_20260701.json",
    f"{PREFIX}_BRANCH_ROADMAP_20260701.csv",
    f"{PREFIX}_EXECUTION_QUEUE_20260701.csv",
    f"{PREFIX}_PROMOTION_CONTRACT_20260701.csv",
    f"{PREFIX}_SOURCE_LOCK_20260701.csv",
    f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
    f"{PREFIX}_SELF_REVIEW_20260701.csv",
    f"{PREFIX}_MANIFEST_20260701.csv",
    f"{PREFIX}_REPORT_20260701.json",
    "519_NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_20260701.md",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "tools/audits/build_nodi_package_c_authorized_mainline_advancement.py",
    "tests/test_nodi_package_c_authorized_mainline_advancement.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}
UPSTREAM_RUNTIME_POLICY_PREFIX = (
    "reports/joint_interface_20260701/"
    "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_"
)
UPSTREAM_RUNTIME_POLICY_PUBLIC_REPORT = (
    "reports/514_NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_20260701.md"
)
UPSTREAM_POST_PROOF_PREFIX = (
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_"
)
UPSTREAM_POST_PROOF_PUBLIC_REPORT = (
    "reports/518_NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_20260701.md"
)


def upstream_runtime_policy_output(path: str) -> bool:
    return path.startswith(UPSTREAM_RUNTIME_POLICY_PREFIX) or (
        path == UPSTREAM_RUNTIME_POLICY_PUBLIC_REPORT
    )


def upstream_post_proof_output(path: str) -> bool:
    return path.startswith(UPSTREAM_POST_PROOF_PREFIX) or (
        path == UPSTREAM_POST_PROOF_PUBLIC_REPORT
    )

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C authorized mainline advancement packet."
    )
    parser.add_argument("--confirm-authorized-mainline-advancement", action="store_true")
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
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def git_path_from_status_line(line: str) -> str:
    return line[2:].strip().replace("\\", "/") if len(line) > 2 else line


def row_count(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix == ".csv":
        return str(len(read_csv_rows(path)))
    return "NA"


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    if path in source_paths or path in BUILD_EDIT_PATHS:
        return True
    return (
        path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_")
        or path == "reports/519_NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if Path(path).name in OUTPUT_NAMES:
            classification = "authorized_mainline_output"
            release_decision = "included_or_rewritten_by_mainline_advancement"
        elif path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "authorized_mainline_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif upstream_runtime_policy_output(path):
            classification = "source_locked_upstream_runtime_policy_dirty_context"
            release_decision = "included_in_chain_rebuild_not_mainline_blocker"
        elif upstream_post_proof_output(path):
            classification = "source_locked_upstream_post_proof_dirty_context"
            release_decision = "included_in_chain_rebuild_not_mainline_blocker"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_mainline_advancement"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_mainline_advancement_not_source_locked"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
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
                "row_count": row_count(path),
                "sha256": sha256_file(path) if exists else "",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def branch_roadmap_rows() -> list[dict[str, str]]:
    branches = [
        (
            "runtime_substep_execution",
            "1",
            "Build runtime execution packet and run the narrowest guarded NODI trajectory smoke/stress cases.",
            "runtime_execution_packet;trajectory_smoke_evidence;substep_guard_summary",
            "runtime_result_candidate",
        ),
        (
            "trapezoid_flow_solver",
            "2",
            "Create trapezoid flow solver evidence branch or COMSOL comparison branch before q_ch use.",
            "flow_solver_or_comsol_flow_evidence;no_qch_until_promoted",
            "trapezoid_flow_solver_output_candidate",
        ),
        (
            "electrokinetic_solver",
            "3",
            "Create profile-aware electrokinetic grid/field evidence branch before electrokinetic weighting.",
            "trapezoid_grid_or_pb_solver_evidence;ionic_strength_zeta_metadata",
            "electrokinetic_solver_output_candidate",
        ),
        (
            "optical_reference_solver",
            "4",
            "Create optical/reference solver or blank-channel calibration evidence before true W_eff/detection claims.",
            "optical_solver_or_calibration_evidence;detector_operator_binding",
            "optical_solver_output_candidate",
        ),
        (
            "wet_ev_evidence",
            "5",
            "Create wet/EV evidence schema and experiment/simulation crosswalk for passability, clogging, recovery, yield.",
            "wet_protocol_or_calibration_evidence;EV_characterization_controls",
            "wet_claim_candidate",
        ),
        (
            "route_yield_detection_decision",
            "6",
            "Only after branch evidence exists, bind q_ch/JRC/route_score/winner/yield/detection promotion contract.",
            "package_d_precheck;solver_wet_hashes;route_decision_audit",
            "route_yield_detection_candidate",
        ),
    ]
    return [
        {
            "branch_id": branch_id,
            "priority": priority,
            "authorized_to_implement": "true",
            "evidence_generation_allowed": "true",
            "candidate_numeric_output_allowed_after_branch_packet": "true",
            "final_claim_promoted_current": "false",
            "current_runtime_or_solver_started": "false",
            "objective": objective,
            "required_evidence_before_promotion": evidence,
            "first_allowed_output_status": first_status,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for branch_id, priority, objective, evidence, first_status in branches
    ]


def execution_queue_rows() -> list[dict[str, str]]:
    tasks = [
        (
            "Q001",
            "runtime_substep_execution_packet",
            "runtime_substep_execution",
            "Build execution packet that selects low-cost and blocked/prohibitive cases and records no PRS/EAS promotion.",
            "local_nodi_only",
            "next",
        ),
        (
            "Q002",
            "guarded_trajectory_smoke",
            "runtime_substep_execution",
            "Run guarded trajectory smoke for a low-cost trapezoid case and a blocked 526-substep stress case.",
            "local_nodi_allowed",
            "after_Q001",
        ),
        (
            "Q003",
            "comsol_clean_mirror_receipt",
            "trapezoid_flow_solver",
            "Ask COMSOL side to mirror post-proof status before solver launch; this can precede actual COMSOL execution.",
            "comsol_read_only_or_receipt",
            "parallel_after_Q001",
        ),
        (
            "Q004",
            "trapezoid_flow_solver_preflight",
            "trapezoid_flow_solver",
            "Define fixed-pressure/fixed-velocity flow solver inputs and acceptance before any q_ch weighting.",
            "solver_preflight",
            "after_Q003",
        ),
        (
            "Q005",
            "electrokinetic_grid_preflight",
            "electrokinetic_solver",
            "Define profile-aware grid, zeta/ionic-strength metadata, and blocked-bin handling.",
            "solver_preflight",
            "parallel_after_Q003",
        ),
        (
            "Q006",
            "optical_reference_preflight",
            "optical_reference_solver",
            "Define optical/reference solver or calibration evidence needed for true W_eff and detection response.",
            "solver_preflight",
            "parallel_after_Q003",
        ),
        (
            "Q007",
            "wet_ev_evidence_contract",
            "wet_ev_evidence",
            "Define passability/clogging/recovery/yield evidence fields and wet-control requirements.",
            "wet_contract",
            "parallel_after_Q001",
        ),
        (
            "Q008",
            "route_promotion_contract",
            "route_yield_detection_decision",
            "Bind q_ch/JRC/route_score/winner/yield/detection_probability to source hashes and branch pass states.",
            "decision_contract",
            "after_Q004_Q005_Q006_Q007",
        ),
    ]
    return [
        {
            "queue_id": queue_id,
            "task_id": task_id,
            "branch_id": branch_id,
            "task": task,
            "execution_mode": mode,
            "dependency": dependency,
            "authorized_to_prepare": "true",
            "authorized_to_execute_when_packet_passes": "true",
            "claim_promoted_by_this_task": "false",
        }
        for queue_id, task_id, branch_id, task, mode, dependency in tasks
    ]


def promotion_contract_rows() -> list[dict[str, str]]:
    promotions = [
        (
            "runtime_result",
            "runtime_execution_packet_pass;substep_guard_pass;trajectory_support_invariant_pass",
            "runtime_result_candidate",
        ),
        (
            "sidewall_prs_eas_numeric_output",
            "package_A_B_pass;runtime_execution_packet_pass;Package_D_precheck_pass;no_blocked_bin_numeric_response",
            "surrogate_sensitivity_only_or_context_only",
        ),
        (
            "trapezoid_flow_solver_output",
            "flow_solver_evidence_hash;fixed_pressure_or_fixed_velocity_mode_declared;not_qch_weighted_until_route_contract",
            "solver_output_candidate",
        ),
        (
            "electrokinetic_solver_output",
            "profile_aware_grid_hash;zeta_ionic_strength_metadata;rectangle_limit_check",
            "solver_output_candidate",
        ),
        (
            "optical_solver_output",
            "optical_solver_or_calibration_hash;detector_operator_binding;not_true_W_eff_until_pass",
            "solver_output_candidate",
        ),
        (
            "wet_claim",
            "wet_protocol_hash;EV_characterization_controls;replicate_summary;calibration_or_experiment_hash",
            "wet_evidence_candidate",
        ),
        (
            "route_score_winner_JRC_qch",
            "flow_evidence_pass;optical_or_detection_evidence_pass;Package_D_route_precheck;no_borrowing_guards",
            "route_decision_candidate",
        ),
        (
            "yield_detection_probability",
            "wet_evidence_pass;detection_calibration_pass;route_decision_audit;uncertainty_report",
            "decision_candidate",
        ),
    ]
    return [
        {
            "promotion_target": target,
            "implementation_authorized": "true",
            "candidate_evidence_authorized": "true",
            "claim_promoted_current": "false",
            "required_evidence_before_claim_true": evidence,
            "first_allowed_status": first_status,
            "hard_fail_if_missing_evidence": f"{target}_claim_true_without_required_hashes",
        }
        for target, evidence, first_status in promotions
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "all downstream branches authorized as implementation/evidence paths",
        "runtime/substep remains first executable local block",
        "solver branches are included without premature solver claims",
        "wet and route/yield/detection are included without premature final claims",
        "ideal rectangle remains first-class while trapezoid sidewall branch advances",
        "dirty context is recorded without source-locking unrelated generated artifacts",
    ]
    return [
        {
            "review_id": f"MAINLINE-SELF-{idx:02d}",
            "dimension": topic,
            "verdict": "PASS_AUTHORIZED_ADVANCEMENT_NOT_FINAL_CLAIM",
            "notes": "Authorized implementation/evidence generation is separated from final claim promotion.",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "branches": [
            (row["branch_id"], row["authorized_to_implement"], row["final_claim_promoted_current"])
            for row in payload["branch_roadmap"]
        ],
        "queue": [(row["queue_id"], row["task_id"], row["dependency"]) for row in payload["execution_queue"]],
        "promotions": [
            (row["promotion_target"], row["claim_promoted_current"])
            for row in payload["promotion_contract"]
        ],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    post_proof = load_json(POST_PROOF_STATUS)
    proof = load_json(PROOF_STATUS)
    user_auth = load_json(USER_AUTH_LEDGER_STATUS)
    dirty_context = dirty_context_rows()
    source_lock = source_lock_rows()
    branch_rows = branch_roadmap_rows()
    queue_rows = execution_queue_rows()
    promotion_rows = promotion_contract_rows()
    source_missing_rows = sum(row["exists"] != "true" for row in source_lock)
    release_scoped_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    required_branches = {
        "runtime_substep_execution",
        "trapezoid_flow_solver",
        "electrokinetic_solver",
        "optical_reference_solver",
        "wet_ev_evidence",
        "route_yield_detection_decision",
    }
    branch_ids = {row["branch_id"] for row in branch_rows}
    all_branches_authorized = all(
        row["authorized_to_implement"] == "true"
        and row["evidence_generation_allowed"] == "true"
        and row["final_claim_promoted_current"] == "false"
        for row in branch_rows
    )
    status = (
        DISPOSITION
        if source_missing_rows == 0
        and release_scoped_dirty_blockers == 0
        and required_branches <= branch_ids
        and all_branches_authorized
        and post_proof.get("package_c_proof_artifact_registered") is True
        and post_proof.get("package_c_validation_status_pass_current") is True
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "post_proof_disposition": post_proof.get("disposition", ""),
        "proof_registration_disposition": proof.get("disposition", ""),
        "user_authorization_disposition": user_auth.get("disposition", ""),
        "package_c_proof_artifact_registered": post_proof.get(
            "package_c_proof_artifact_registered"
        )
        is True,
        "package_c_validation_status_pass_current": post_proof.get(
            "package_c_validation_status_pass_current"
        )
        is True,
        "package_c_validation_status_pass_scope": post_proof.get(
            "package_c_validation_status_pass_scope", ""
        ),
        "authorized_downstream_branch_count": len(branch_rows),
        "execution_queue_rows": len(queue_rows),
        "promotion_contract_rows": len(promotion_rows),
        "all_downstream_branches_authorized_to_implement": all_branches_authorized,
        "runtime_substep_next": True,
        "solver_branches_authorized_to_prepare": True,
        "wet_branch_authorized_to_prepare": True,
        "route_yield_detection_branch_authorized_to_prepare": True,
        "runtime_execution_started": False,
        "comsol_launch_started": False,
        "mph_load_started": False,
        "solver_output_current": False,
        "wet_claim_current": False,
        "route_yield_detection_claim_current": False,
        "final_claim_promotion_current": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing_rows,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_scoped_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "branch_roadmap": branch_rows,
        "execution_queue": queue_rows,
        "promotion_contract": promotion_rows,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": s["disposition"] == DISPOSITION,
        "source lock complete": s["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": s["release_scoped_dirty_blocker_rows"] == 0,
        "proof registered": s["package_c_proof_artifact_registered"] is True,
        "finite-step proof pass current": s["package_c_validation_status_pass_current"] is True,
        "finite-step scope only": (
            s["package_c_validation_status_pass_scope"]
            == "finite_step_reflection_surrogate_evidence_only"
        ),
        "all branches authorized": s["all_downstream_branches_authorized_to_implement"] is True,
        "runtime next": s["runtime_substep_next"] is True,
        "no current runtime execution": s["runtime_execution_started"] is False,
        "no current COMSOL launch": s["comsol_launch_started"] is False,
        "no current MPH load": s["mph_load_started"] is False,
        "no current solver output": s["solver_output_current"] is False,
        "no current wet claim": s["wet_claim_current"] is False,
        "no current route/yield/detection claim": s["route_yield_detection_claim_current"] is False,
        "no final claim promotion": s["final_claim_promotion_current"] is False,
    }
    for row in payload["branch_roadmap"]:
        checks[f"branch authorized: {row['branch_id']}"] = (
            row["authorized_to_implement"] == "true"
            and row["final_claim_promoted_current"] == "false"
        )
    for row in payload["promotion_contract"]:
        checks[f"promotion guarded: {row['promotion_target']}"] = (
            row["implementation_authorized"] == "true"
            and row["claim_promoted_current"] == "false"
            and bool(row["required_evidence_before_claim_true"])
        )
    return [label for label, ok in checks.items() if not ok]


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    branch_lines = [
        f"- `{row['priority']}` `{row['branch_id']}`: authorized to implement/evidence; final claim current `false`."
        for row in payload["branch_roadmap"]
    ]
    return "\n".join(
        [
            "# NODI Package C Authorized Mainline Advancement",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Semantic digest: `{s['semantic_digest']}`.",
            "- Package C finite-step reflection proof remains registered and narrowly scoped.",
            "- Runtime/substep, solver, wet, and route/yield/detection paths are authorized for implementation and evidence generation.",
            "- Current final claim promotion remains `false` until branch evidence packets satisfy the promotion contract.",
            "",
            "## Branches",
            *branch_lines,
            "",
            "## Next Executable Block",
            "Build the runtime/substep execution packet, then run the guarded NODI trajectory smoke/stress cases. Solver/wet/route branches should proceed in parallel as evidence contracts/preflights, not as final route conclusions.",
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
                "policy_impact": "authorized_mainline_advancement",
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
        f"{PREFIX}_BRANCH_ROADMAP_20260701.csv": payload["branch_roadmap"],
        f"{PREFIX}_EXECUTION_QUEUE_20260701.csv": payload["execution_queue"],
        f"{PREFIX}_PROMOTION_CONTRACT_20260701.csv": payload["promotion_contract"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
        f"{PREFIX}_SELF_REVIEW_20260701.csv": payload["self_review"],
    }
    for filename, rows in csv_payloads.items():
        path = output_dir / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = output_dir / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_json_path = output_dir / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_json_path, payload)
    paths.append(report_json_path)

    public_report = report_dir / "519_NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = output_dir / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, artifact_manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_authorized_mainline_advancement:
        parser.error("--confirm-authorized-mainline-advancement is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
