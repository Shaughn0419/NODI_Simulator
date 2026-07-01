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
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

DISPOSITION = "NODI_PACKAGE_C_AUTHORIZATION_PREFLIGHT_CANDIDATE_READY_NO_AUTHORIZATION"
ARTIFACT_ID = "PACKAGE_C_AUTHORIZATION_PREFLIGHT_20260701"
CLAIM_BOUNDARY = "authorization_preflight_candidate_not_package_c_proof_registered_not_runtime"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C authorization preflight;clean commit candidate binding;manual ledger placeholder;"
    "no-proof-registration"
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

READINESS_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_STATUS_20260701.json"
)
READINESS_INDEX = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_INDEX_20260701.csv"
)
READINESS_BLOCKERS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_BLOCKERS_20260701.csv"
)
RUNTIME_SUBSTEP_POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json"
)

SOURCE_FILES = {
    "proof_readiness_status": READINESS_STATUS,
    "proof_readiness_index": READINESS_INDEX,
    "proof_readiness_blockers": READINESS_BLOCKERS,
    "runtime_substep_policy_design_status": RUNTIME_SUBSTEP_POLICY_STATUS,
    "authorization_preflight_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_authorization_preflight.py",
    "authorization_preflight_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_authorization_preflight.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C authorization preflight artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-authorization-preflight",
        action="store_true",
    )
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def safe_git(args: list[str]) -> str:
    try:
        return run_git(args)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def raw_url(path: Path) -> str:
    return f"{GITHUB_RAW_BASE}/{rel(path)}"


def blob_url(path: Path) -> str:
    return f"{GITHUB_BLOB_BASE}/{rel(path)}"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


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
                "github_visibility_status": GITHUB_VISIBILITY_STATUS,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_PACKAGE_C_AUTHORIZATION_PREFLIGHT_NO_AUTHORIZATION",
            "package_c_proof_artifact_registered": "false",
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_configuration_authorized": "false",
            "substep_runtime_policy_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "validated_brownian_solver_output_authorized": "false",
            "hindered_diffusion_claim_authorized": "false",
            "trapezoid_flow_solver_claim_authorized": "false",
            "electrokinetic_solver_claim_authorized": "false",
            "optical_solver_claim_authorized": "false",
            "true_w_eff_authorized": "false",
            "wet_claim_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "production_ingestion_authorized": "false",
        }
    ]


def clean_commit_binding_rows() -> list[dict[str, str]]:
    head = safe_git(["rev-parse", "HEAD"])
    origin_main = safe_git(["rev-parse", "origin/main"])
    status = safe_git(["status", "--porcelain"])
    return [
        {
            "binding_id": "candidate_reviewed_commit",
            "target_reviewed_commit_sha": head,
            "origin_main_sha": origin_main,
            "head_matches_origin_main": bool_text(bool(head) and head == origin_main),
            "current_worktree_clean": bool_text(status == ""),
            "current_worktree_status": (
                "clean"
                if status == ""
                else "dirty_preflight_generation_workspace_not_final_proof_binding"
            ),
            "binding_status": (
                "candidate_remote_commit_identified_not_final_authorization_binding"
                if head and head == origin_main
                else "blocked_head_not_equal_origin_main"
            ),
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def authorization_ledger_placeholder_rows() -> list[dict[str, str]]:
    return [
        {
            "ledger_field": "manual_authorization_ledger_id",
            "ledger_value": "",
            "ledger_status": "placeholder_empty_fail_closed",
            "hard_fail_if": "missing_when_attempting_proof_registration_or_runtime",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "ledger_field": "manual_authorization_ledger_sha256",
            "ledger_value": "",
            "ledger_status": "placeholder_empty_fail_closed",
            "hard_fail_if": "missing_when_attempting_proof_registration_or_runtime",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "ledger_field": "proof_registration_authorized",
            "ledger_value": "false",
            "ledger_status": "explicit_false_no_authorization",
            "hard_fail_if": "true_without_manual_authorization_ledger",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "ledger_field": "runtime_allowed",
            "ledger_value": "false",
            "ledger_status": "explicit_false_no_runtime_authorization",
            "hard_fail_if": "true_without_manual_runtime_ledger",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
    ]


def hard_fail_checklist_rows() -> list[dict[str, str]]:
    rules = [
        ("manual_authorization_ledger_missing", "proof_or_runtime_attempt"),
        ("target_reviewed_commit_sha_missing", "proof_registration_attempt"),
        ("head_not_equal_origin_main", "authorization_preflight_attempt"),
        ("proof_registration_authorized_true_without_ledger", "any_artifact"),
        ("package_c_validation_status_pass_without_ledger", "any_artifact"),
        ("runtime_allowed_true_without_runtime_ledger", "any_artifact"),
        ("sidewall_prs_eas_numeric_output_true_without_package_d_precheck", "any_artifact"),
        ("comsol_or_mph_authorized_from_package_c_preflight", "any_artifact"),
        ("route_yield_detection_wet_claim_from_package_c_preflight", "any_artifact"),
    ]
    return [
        {
            "hard_fail_rule": rule,
            "applies_to": applies_to,
            "required_resolution": "manual_ledger_or_keep_false_fail_closed",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for rule, applies_to in rules
    ]


def build_payload() -> dict[str, Any]:
    bindings = clean_commit_binding_rows()
    ledger = authorization_ledger_placeholder_rows()
    checklist = hard_fail_checklist_rows()
    sources = source_lock_rows()
    firewall = no_proof_firewall_rows()
    binding = bindings[0]
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": binding["target_reviewed_commit_sha"],
        "target_reviewed_commit_sha": binding["target_reviewed_commit_sha"],
        "origin_main_sha": binding["origin_main_sha"],
        "head_matches_origin_main": binding["head_matches_origin_main"] == "true",
        "current_worktree_clean": binding["current_worktree_clean"] == "true",
        "current_worktree_status": binding["current_worktree_status"],
        "clean_commit_binding_rows": len(bindings),
        "authorization_ledger_placeholder_rows": len(ledger),
        "hard_fail_checklist_rows": len(checklist),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(row["exists"] != "true" for row in sources),
        "authorization_preflight_status": (
            "candidate_commit_identified_authorization_missing_no_proof_registration"
        ),
        "clean_commit_binding_status": binding["binding_status"],
        "manual_authorization_ledger_status": "missing_fail_closed",
        "proof_registration_authorized": False,
        "package_c_validation_status_pass_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "candidate_only": True,
        "no_auth": True,
        "github_visibility_status": GITHUB_VISIBILITY_STATUS,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "clean_commit_binding": bindings,
        "authorization_ledger_placeholder": ledger,
        "hard_fail_checklist": checklist,
        "source_locks": sources,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Commit sha present": bool(s["target_reviewed_commit_sha"]),
        "Origin main sha present": bool(s["origin_main_sha"]),
        "Head matches origin/main": s["head_matches_origin_main"] is True,
        "Ledger placeholders present": s["authorization_ledger_placeholder_rows"] >= 4,
        "Hard-fail checklist present": s["hard_fail_checklist_rows"] >= 8,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Preflight status": s["authorization_preflight_status"]
        == "candidate_commit_identified_authorization_missing_no_proof_registration",
        "Manual ledger missing fail closed": s["manual_authorization_ledger_status"]
        == "missing_fail_closed",
        "No proof registration": s["proof_registration_authorized"] is False,
        "No Package C pass": s["package_c_validation_status_pass_authorized"] is False,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
    }
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
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
            "policy_impact": "authorization_preflight_no_proof_registration",
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
                "policy_impact": "manifest_self_row_no_recursive_sha_no_authorization",
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

    csv_specs = {
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_CLEAN_COMMIT_BINDING_20260701.csv": payload[
            "clean_commit_binding"
        ],
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_LEDGER_PLACEHOLDER_20260701.csv": payload[
            "authorization_ledger_placeholder"
        ],
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_HARD_FAIL_CHECKLIST_20260701.csv": payload[
            "hard_fail_checklist"
        ],
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_STATUS_20260701.json"
    )
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "proof_registration_authorized": False,
            "package_c_validation_status_pass_authorized": False,
            "runtime_allowed": False,
            "numeric_prs_eas_allowed": False,
            "comsol_launch_allowed": False,
            "mph_load_allowed": False,
        },
    )
    generated.append(status_path)

    active_report = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_REPORT_20260701.md"
    )
    write_md(
        active_report,
        "NODI COMSOL Package C Authorization Preflight",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Target reviewed commit: `{payload['summary']['target_reviewed_commit_sha']}`.",
            f"- Head matches origin/main: `{payload['summary']['head_matches_origin_main']}`.",
            f"- Manual authorization ledger status: `{payload['summary']['manual_authorization_ledger_status']}`.",
            f"- Hard-fail checklist rows: `{payload['summary']['hard_fail_checklist_rows']}`.",
            "- Boundary: authorization preflight only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = (
        active_report_dir
        / "515_NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_20260701.md"
    )
    write_md(
        public_report,
        "NODI COMSOL Package C Authorization Preflight",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Target reviewed commit: `{payload['summary']['target_reviewed_commit_sha']}`.",
            f"- Origin/main commit: `{payload['summary']['origin_main_sha']}`.",
            f"- Head matches origin/main: `{payload['summary']['head_matches_origin_main']}`.",
            f"- Clean commit binding status: `{payload['summary']['clean_commit_binding_status']}`.",
            f"- Manual authorization ledger status: `{payload['summary']['manual_authorization_ledger_status']}`.",
            f"- Hard-fail checklist rows: `{payload['summary']['hard_fail_checklist_rows']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: this is authorization preflight only, not Package C proof registration or runtime authorization.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_MANIFEST_20260701.csv"
    )
    report_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_REPORT_20260701.json"
    )
    report_outputs = [path.name for path in generated] + [report_path.name, manifest_path.name]
    write_json_atomic(report_path, {"summary": payload["summary"], "outputs": report_outputs})
    generated.append(report_path)
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(generated, self_manifest_path=manifest_path),
    )
    return {"status": status_path, "report": report_path, "manifest": manifest_path}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_package_c_authorization_preflight:
        parser.error("--confirm-package-c-authorization-preflight is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_AUTHORIZATION_PREFLIGHT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
