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
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

DISPOSITION = "NODI_PACKAGE_C_USER_AUTHORIZATION_LEDGER_ACCEPTED_NO_RESULT_PROMOTION"
ARTIFACT_ID = "PACKAGE_C_USER_AUTHORIZATION_LEDGER_20260701"
CLAIM_BOUNDARY = "user_authorization_ledger_accepted_not_package_c_proof_pass_not_runtime_result"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

USER_AUTHORIZATION_TEXT = (
    "对于 manual authorization ledger、runtime/substep policy 授权、solver/wet 分支授权，都授权。"
)

ALLOWED_USE = (
    "Package C user authorization ledger;proof-registration path authorization;"
    "runtime/substep policy path authorization;solver/wet branch path authorization"
)
BLOCKED_USE = (
    "automatic Package C proof/pass;unreviewed package_C_validation_status pass;"
    "unreviewed runtime result;sidewall PRS/EAS numeric output without Package D precheck;"
    "NODI runtime recomputation without execution packet;COMSOL launch without execution packet;"
    ".mph load without execution packet;validated Brownian solver output without proof artifact;"
    "validated hindered diffusion without solver evidence;trapezoid Poiseuille solver output without solver;"
    "electrokinetic grid output without solver;optical solver output without solver;true W_eff without optical evidence;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)

AUTHORIZATION_PREFLIGHT_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_STATUS_20260701.json"
)
RUNTIME_SUBSTEP_POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json"
)
PROOF_READINESS_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_STATUS_20260701.json"
)

SOURCE_FILES = {
    "authorization_preflight_status": AUTHORIZATION_PREFLIGHT_STATUS,
    "runtime_substep_policy_design_status": RUNTIME_SUBSTEP_POLICY_STATUS,
    "proof_readiness_status": PROOF_READINESS_STATUS,
    "user_authorization_ledger_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_user_authorization_ledger.py",
    "user_authorization_ledger_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_user_authorization_ledger.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C user authorization ledger artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-user-authorization-ledger",
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


def read_json_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("summary", {})


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


def authorization_scope_rows() -> list[dict[str, str]]:
    scopes = [
        (
            "package_c_proof_registration_path",
            "authorized",
            "proof_artifact_registration_still_requires_evidence_and_source_lock",
        ),
        (
            "runtime_substep_policy_path",
            "authorized",
            "runtime_execution_still_requires_implementation_tests_and_execution_packet",
        ),
        (
            "solver_branch_path",
            "authorized",
            "solver_execution_still_requires_solver_packet_and_no_claim_guards",
        ),
        (
            "wet_branch_path",
            "authorized",
            "wet_claims_still_require_experimental_evidence_and_controls",
        ),
    ]
    return [
        {
            "scope_id": scope_id,
            "authorization_status": status,
            "authorization_source": "user_explicit_message_current_thread_20260701",
            "authorization_text": USER_AUTHORIZATION_TEXT,
            "not_result_promotion_reason": reason,
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for scope_id, status, reason in scopes
    ]


def result_promotion_guard_rows() -> list[dict[str, str]]:
    guards = [
        ("package_c_proof_artifact_registered", "false"),
        ("package_c_validation_status_pass_current", "false"),
        ("runtime_execution_started", "false"),
        ("sidewall_prs_eas_numeric_output_current", "false"),
        ("nodi_runtime_recomputation_started", "false"),
        ("comsol_launch_started", "false"),
        ("mph_load_started", "false"),
        ("validated_brownian_solver_output_current", "false"),
        ("validated_hindered_diffusion_claim_current", "false"),
        ("trapezoid_flow_solver_output_current", "false"),
        ("electrokinetic_solver_output_current", "false"),
        ("optical_solver_output_current", "false"),
        ("wet_claim_current", "false"),
        ("route_yield_detection_claim_current", "false"),
    ]
    return [
        {
            "guard_field": field,
            "guard_value": value,
            "guard_status": "authorization_does_not_promote_result",
            "hard_fail_if": f"{field}_true_without_required_evidence_packet",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for field, value in guards
    ]


def build_payload() -> dict[str, Any]:
    preflight = read_json_summary(AUTHORIZATION_PREFLIGHT_STATUS)
    runtime_policy = read_json_summary(RUNTIME_SUBSTEP_POLICY_STATUS)
    scopes = authorization_scope_rows()
    guards = result_promotion_guard_rows()
    sources = source_lock_rows()
    authorized_scopes = [
        row for row in scopes if row["authorization_status"] == "authorized"
    ]
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "authorization_source": "user_explicit_message_current_thread_20260701",
        "authorization_text_sha256": hashlib.sha256(
            USER_AUTHORIZATION_TEXT.encode("utf-8")
        ).hexdigest(),
        "authorization_scope_rows": len(scopes),
        "authorized_scope_rows": len(authorized_scopes),
        "result_promotion_guard_rows": len(guards),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(row["exists"] != "true" for row in sources),
        "preflight_artifact_id": preflight.get("artifact_id", ""),
        "preflight_target_commit_sha": preflight.get("target_reviewed_commit_sha", ""),
        "runtime_policy_artifact_id": runtime_policy.get("artifact_id", ""),
        "runtime_substep_policy_authorized": True,
        "solver_branch_authorized": True,
        "wet_branch_authorized": True,
        "package_c_proof_registration_path_authorized": True,
        "package_c_proof_artifact_registered": False,
        "package_c_validation_status_pass_current": False,
        "runtime_execution_started": False,
        "sidewall_prs_eas_numeric_output_current": False,
        "comsol_launch_started": False,
        "mph_load_started": False,
        "authorization_ledger_status": "accepted_scope_authorization_no_result_promotion",
        "proof_readiness_impact": "manual_authorization_blocker_resolved_paths_authorized",
        "candidate_only": True,
        "github_visibility_status": GITHUB_VISIBILITY_STATUS,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "authorization_scopes": scopes,
        "result_promotion_guards": guards,
        "source_locks": sources,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    guards = payload["result_promotion_guards"]
    checks = {
        "Authorization scopes": s["authorization_scope_rows"] == 4,
        "All scopes authorized": s["authorized_scope_rows"] == 4,
        "Promotion guards present": s["result_promotion_guard_rows"] >= 12,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Runtime path authorized": s["runtime_substep_policy_authorized"] is True,
        "Solver branch authorized": s["solver_branch_authorized"] is True,
        "Wet branch authorized": s["wet_branch_authorized"] is True,
        "Proof path authorized": s["package_c_proof_registration_path_authorized"] is True,
        "No proof artifact registered here": s["package_c_proof_artifact_registered"] is False,
        "No Package C pass here": s["package_c_validation_status_pass_current"] is False,
        "No runtime execution here": s["runtime_execution_started"] is False,
        "No numeric PRS/EAS here": s["sidewall_prs_eas_numeric_output_current"] is False,
        "No COMSOL launch here": s["comsol_launch_started"] is False,
        "No mph load here": s["mph_load_started"] is False,
        "Ledger accepted": s["authorization_ledger_status"]
        == "accepted_scope_authorization_no_result_promotion",
        "All guards false": {row["guard_value"] for row in guards} == {"false"},
    }
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
            "policy_impact": "authorization_ledger_accepted_no_result_promotion",
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
                "policy_impact": "manifest_self_row_no_recursive_sha_no_result_promotion",
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
        "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_SCOPES_20260701.csv": payload[
            "authorization_scopes"
        ],
        "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_RESULT_GUARDS_20260701.csv": payload[
            "result_promotion_guards"
        ],
        "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_STATUS_20260701.json"
    )
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "package_c_proof_registration_path_authorized": True,
            "runtime_substep_policy_authorized": True,
            "solver_branch_authorized": True,
            "wet_branch_authorized": True,
            "package_c_proof_artifact_registered": False,
            "runtime_execution_started": False,
            "comsol_launch_started": False,
            "mph_load_started": False,
        },
    )
    generated.append(status_path)

    active_report = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_REPORT_20260701.md"
    )
    write_md(
        active_report,
        "NODI COMSOL Package C User Authorization Ledger",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Authorized scope rows: `{payload['summary']['authorized_scope_rows']}`.",
            f"- Runtime/substep policy authorized: `{payload['summary']['runtime_substep_policy_authorized']}`.",
            f"- Solver branch authorized: `{payload['summary']['solver_branch_authorized']}`.",
            f"- Wet branch authorized: `{payload['summary']['wet_branch_authorized']}`.",
            "- Boundary: authorization is accepted for paths only; this packet does not register proof/pass, start runtime, launch COMSOL, load .mph, emit PRS/EAS numeric output, or make wet/route/yield/detection claims.",
        ],
    )
    generated.append(active_report)

    public_report = (
        active_report_dir
        / "516_NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_20260701.md"
    )
    write_md(
        public_report,
        "NODI COMSOL Package C User Authorization Ledger",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            f"- Authorization source: `{payload['summary']['authorization_source']}`.",
            f"- Authorized scope rows: `{payload['summary']['authorized_scope_rows']}`.",
            "- Authorized scopes: `package_c_proof_registration_path`, `runtime_substep_policy_path`, `solver_branch_path`, `wet_branch_path`.",
            f"- Result-promotion guard rows: `{payload['summary']['result_promotion_guard_rows']}`.",
            f"- Preflight target commit: `{payload['summary']['preflight_target_commit_sha']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: this ledger resolves authorization-path blockers only. It does not itself register proof/pass, start runtime, launch COMSOL, load `.mph`, emit sidewall PRS/EAS numeric output, or create route/yield/detection/wet/fabrication/production claims.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_MANIFEST_20260701.csv"
    )
    report_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_REPORT_20260701.json"
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
    if not args.confirm_package_c_user_authorization_ledger:
        parser.error("--confirm-package-c-user-authorization-ledger is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_USER_AUTHORIZATION_LEDGER")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
