#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
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
from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    SIDEWALL_PACKAGE_C_PROOF_REQUIRED_SUBSTEP_TRIGGER_METRIC,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

EXPECTED_SUBSTEP_HARDENING_DISPOSITION = (
    "NODI_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
DISPOSITION = (
    "NODI_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_20260701"
CLAIM_BOUNDARY = (
    "substep_dt_refinement_requirements_candidate_not_package_c_proof_registered_not_runtime"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
SUBSTEP_TRIGGER_METRIC = SIDEWALL_PACKAGE_C_PROOF_REQUIRED_SUBSTEP_TRIGGER_METRIC
SUBSTEP_TRIGGER_THRESHOLD = 1.0
CURRENT_DT_S = 2.5e-5
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C substep dt-refinement requirement candidate;proof/pass policy planning;"
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

SUBSTEP_HARDENING_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_STATUS_20260701.json"
)
SUBSTEP_FAIL_POLICY_ROWS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_ROWS_20260701.csv"
)

SOURCE_FILES = {
    "substep_hardening_status": SUBSTEP_HARDENING_STATUS,
    "substep_fail_policy_rows": SUBSTEP_FAIL_POLICY_ROWS,
    "dt_refinement_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_substep_dt_refinement_requirements.py",
    "dt_refinement_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_substep_dt_refinement_requirements.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C substep dt-refinement requirement artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-substep-dt-refinement-requirements",
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
            "firewall_status": (
                "PASS_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_NO_PROOF_REGISTRATION"
            ),
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


def _refinement_row(row: dict[str, str]) -> dict[str, str]:
    ratio = float(row["observed_trigger_value"])
    required_substeps = max(1, math.ceil((ratio / SUBSTEP_TRIGGER_THRESHOLD) ** 2))
    required_dt_s = CURRENT_DT_S / required_substeps
    projected_ratio = ratio / math.sqrt(required_substeps)
    return {
        "scenario_id": row["scenario_id"],
        "substep_trigger_metric": SUBSTEP_TRIGGER_METRIC,
        "substep_trigger_threshold": str(SUBSTEP_TRIGGER_THRESHOLD),
        "current_dt_s": f"{CURRENT_DT_S:.12g}",
        "observed_trigger_value": row["observed_trigger_value"],
        "observed_surface_gap_nm_p05": row["observed_surface_gap_nm_p05"],
        "brownian_rms_step_nm": row["brownian_rms_step_nm"],
        "required_substeps_to_meet_threshold": str(required_substeps),
        "required_dt_s_to_meet_threshold": f"{required_dt_s:.12g}",
        "projected_trigger_value_after_required_substeps": f"{projected_ratio:.12g}",
        "dt_refinement_candidate_status": (
            "fail_or_reduce_dt_before_proof_pass_or_runtime"
        ),
        "runtime_policy_authorized": "false",
        "claim_boundary": CLAIM_BOUNDARY,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }


def build_payload() -> dict[str, Any]:
    hardening_status = read_json(SUBSTEP_HARDENING_STATUS).get("summary", {})
    source_rows = read_csv_rows(SUBSTEP_FAIL_POLICY_ROWS)
    refinement_rows = [_refinement_row(row) for row in source_rows]
    source_lock = source_lock_rows()
    firewall = no_proof_firewall_rows()
    required_substeps = [
        int(row["required_substeps_to_meet_threshold"]) for row in refinement_rows
    ]
    required_dt_values = [
        float(row["required_dt_s_to_meet_threshold"]) for row in refinement_rows
    ]
    projected_values = [
        float(row["projected_trigger_value_after_required_substeps"])
        for row in refinement_rows
    ]
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "substep_hardening_disposition": hardening_status.get("disposition", ""),
        "substep_hardening_artifact_id": hardening_status.get("artifact_id", ""),
        "refinement_rows": len(refinement_rows),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_lock),
        "substep_trigger_metric": SUBSTEP_TRIGGER_METRIC,
        "substep_trigger_threshold": SUBSTEP_TRIGGER_THRESHOLD,
        "current_dt_s": CURRENT_DT_S,
        "min_required_substeps_to_meet_threshold": min(required_substeps, default=0),
        "max_required_substeps_to_meet_threshold": max(required_substeps, default=0),
        "min_required_dt_s_to_meet_threshold": min(required_dt_values, default=0.0),
        "max_projected_trigger_value_after_required_substeps": max(
            projected_values,
            default=0.0,
        ),
        "dt_refinement_candidate_status": (
            "requirements_complete_not_runtime_policy_not_proof"
        ),
        "proof_readiness_impact": (
            "substep_review_rows_now_have_explicit_dt_refinement_requirements"
        ),
        "reviewed_commit_binding_status": "pending_future_authorization_not_clean_head_bound",
        "github_visibility_status": GITHUB_VISIBILITY_STATUS,
        "proof_registration_authorized": False,
        "package_c_validation_status_pass_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "candidate_only": True,
        "no_auth": True,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "dt_refinement_requirements": refinement_rows,
        "source_locks": source_lock,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Substep hardening disposition": s["substep_hardening_disposition"]
        == EXPECTED_SUBSTEP_HARDENING_DISPOSITION,
        "Refinement rows present": s["refinement_rows"] > 0,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Current dt positive": s["current_dt_s"] > 0.0,
        "Substep refinement required": s["max_required_substeps_to_meet_threshold"] > 1,
        "Projected trigger meets threshold": (
            s["max_projected_trigger_value_after_required_substeps"]
            <= SUBSTEP_TRIGGER_THRESHOLD
        ),
        "GitHub visibility caveat": s["github_visibility_status"]
        == GITHUB_VISIBILITY_STATUS,
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
            "policy_impact": "substep_dt_refinement_requirements_no_proof_registration",
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
                "policy_impact": "manifest_self_row_no_recursive_sha_no_proof_registration",
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
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_20260701.csv": payload[
            "dt_refinement_requirements"
        ],
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_STATUS_20260701.json"
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
        / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REPORT_20260701.md"
    )
    write_md(
        active_report,
        "NODI COMSOL Package C Substep DT Refinement Requirements",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Refinement rows: `{payload['summary']['refinement_rows']}`.",
            f"- Current dt: `{payload['summary']['current_dt_s']}` s.",
            f"- Max required substeps: `{payload['summary']['max_required_substeps_to_meet_threshold']}`.",
            f"- Min required dt: `{payload['summary']['min_required_dt_s_to_meet_threshold']}` s.",
            f"- Max projected trigger after required substeps: `{payload['summary']['max_projected_trigger_value_after_required_substeps']}`.",
            "- Boundary: dt refinement requirements only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = (
        active_report_dir
        / "507_NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_20260701.md"
    )
    write_md(
        public_report,
        "NODI COMSOL Package C Substep DT Refinement Requirements",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet turns substep-triggered scenarios into explicit dt/substep reduction requirements for future proof/pass policy review.",
            f"- Refinement rows: `{payload['summary']['refinement_rows']}`.",
            f"- Current dt: `{payload['summary']['current_dt_s']}` s.",
            f"- Max required substeps to meet threshold: `{payload['summary']['max_required_substeps_to_meet_threshold']}`.",
            f"- Min required dt to meet threshold: `{payload['summary']['min_required_dt_s_to_meet_threshold']}` s.",
            f"- Max projected trigger after required substeps: `{payload['summary']['max_projected_trigger_value_after_required_substeps']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: this is candidate planning evidence only, not Package C proof registration or runtime authorization.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_MANIFEST_20260701.csv"
    )
    report_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REPORT_20260701.json"
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
    if not args.confirm_package_c_substep_dt_refinement_requirements:
        parser.error("--confirm-package-c-substep-dt-refinement-requirements is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
