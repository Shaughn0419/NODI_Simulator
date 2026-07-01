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
from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    SIDEWALL_PACKAGE_C_PROOF_REQUIRED_SUBSTEP_POLICY_SCOPE,
    SIDEWALL_PACKAGE_C_PROOF_REQUIRED_SUBSTEP_POLICY_STATUS,
    SIDEWALL_PACKAGE_C_PROOF_REQUIRED_SUBSTEP_TRIGGER_METRIC,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

EXPECTED_TIMESERIES_DISPOSITION = (
    "NODI_PACKAGE_C_TIMESERIES_ESS_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
DISPOSITION = (
    "NODI_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_20260701"
CLAIM_BOUNDARY = (
    "substep_fail_policy_candidate_not_package_c_proof_registered_not_runtime"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
SUBSTEP_TRIGGER_METRIC = SIDEWALL_PACKAGE_C_PROOF_REQUIRED_SUBSTEP_TRIGGER_METRIC
SUBSTEP_TRIGGER_THRESHOLD = 1.0
SUBSTEP_POLICY_STATUS = SIDEWALL_PACKAGE_C_PROOF_REQUIRED_SUBSTEP_POLICY_STATUS
SUBSTEP_POLICY_SCOPE = SIDEWALL_PACKAGE_C_PROOF_REQUIRED_SUBSTEP_POLICY_SCOPE
VALIDATOR_HARDENING_STATUS = (
    "package_c_proof_pass_requires_substep_policy_fields"
)
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C substep/fail policy hardening candidate;proof/pass validator design;"
    "substep evidence binding;no-proof-registration"
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

TIMESERIES_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_STATUS_20260701.json"
)
TIMESERIES_SUBSTEP_POLICY = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_SUBSTEP_POLICY_20260701.csv"
)

SOURCE_FILES = {
    "timeseries_status": TIMESERIES_STATUS,
    "timeseries_substep_policy": TIMESERIES_SUBSTEP_POLICY,
    "package_c_contract_validator": PROJECT_ROOT
    / "nodi_simulator/nodi_comsol_next_artifacts.py",
    "package_c_contract_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_next_artifacts_contracts.py",
    "substep_policy_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_substep_fail_policy_hardening.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

PROOF_FIELD_REQUIREMENTS = (
    {
        "field": "substep_policy_evidence_sha256",
        "requirement": "must reference reviewed substep fail-or-reduce-dt policy evidence",
        "hard_fail_if": "missing_or_not_sha256",
    },
    {
        "field": "substep_policy_status",
        "requirement": "must close all triggered rms/gap scenarios with fail-or-reduce-dt policy",
        "hard_fail_if": "not_all_triggered_scenarios_have_fail_or_reduce_dt_policy",
    },
    {
        "field": "substep_policy_scope",
        "requirement": "must remain proof guard only, not runtime configuration",
        "hard_fail_if": "claims_runtime_config_or_production_use",
    },
    {
        "field": "substep_trigger_metric",
        "requirement": f"must equal {SUBSTEP_TRIGGER_METRIC}",
        "hard_fail_if": "metric_is_ambiguous_or_not_rms_over_gap",
    },
    {
        "field": "substep_trigger_threshold",
        "requirement": "must be numeric and in (0, 1]",
        "hard_fail_if": "missing_non_numeric_or_greater_than_one",
    },
    {
        "field": "substep_max_observed_trigger_value",
        "requirement": "must bind the max observed trigger value from reviewed evidence",
        "hard_fail_if": "missing_non_numeric_or_not_bound_to_evidence",
    },
    {
        "field": "substep_triggered_scenario_count",
        "requirement": "must bind the count of scenarios whose trigger metric exceeds threshold",
        "hard_fail_if": "missing_non_integer_negative_or_zero_when_max_trigger_exceeds_threshold",
    },
    {
        "field": "substep_policy_bound_trigger_count",
        "requirement": "must cover every triggered scenario before proof/pass can be accepted",
        "hard_fail_if": "missing_non_integer_negative_or_less_than_triggered_scenario_count",
    },
    {
        "field": "substep_review_required",
        "requirement": "must be false for Package C proof/pass rows",
        "hard_fail_if": "true_or_not_boolean",
    },
    {
        "field": "substep_runtime_policy_authorized",
        "requirement": "must be false because proof/pass does not authorize runtime policy",
        "hard_fail_if": "true_or_not_boolean",
    },
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C substep/fail policy hardening artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-substep-fail-policy-hardening",
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
                "PASS_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_NO_PROOF_REGISTRATION"
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


def proof_field_requirement_rows() -> list[dict[str, str]]:
    return [
        {
            "field": row["field"],
            "requirement": row["requirement"],
            "hard_fail_if": row["hard_fail_if"],
            "validator_issue_id": "SIDEWALL-D-PRECHECK-V03",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for row in PROOF_FIELD_REQUIREMENTS
    ]


def _policy_row(row: dict[str, str]) -> dict[str, str]:
    ratio = float(row["rms_step_over_surface_gap_p05"])
    triggered = ratio > SUBSTEP_TRIGGER_THRESHOLD
    return {
        "scenario_id": row["scenario_id"],
        "substep_trigger_metric": SUBSTEP_TRIGGER_METRIC,
        "substep_trigger_threshold": str(SUBSTEP_TRIGGER_THRESHOLD),
        "observed_trigger_value": row["rms_step_over_surface_gap_p05"],
        "observed_surface_gap_nm_p05": row["surface_gap_nm_p05"],
        "brownian_rms_step_nm": row["brownian_rms_step_nm"],
        "substep_triggered": bool_text(triggered),
        "required_future_policy": (
            "fail_or_reduce_dt_before_proof_pass_or_runtime"
            if triggered
            else "no_substep_trigger_from_candidate"
        ),
        "proof_pass_binding_status": (
            "hard_fail_until_fail_or_reduce_dt_policy_bound"
            if triggered
            else "no_candidate_trigger"
        ),
        "runtime_policy_authorized": "false",
        "claim_boundary": CLAIM_BOUNDARY,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }


def build_payload() -> dict[str, Any]:
    timeseries_status = read_json(TIMESERIES_STATUS).get("summary", {})
    substep_source_rows = read_csv_rows(TIMESERIES_SUBSTEP_POLICY)
    policy_rows = [_policy_row(row) for row in substep_source_rows]
    source_rows = source_lock_rows()
    firewall = no_proof_firewall_rows()
    triggered_rows = [row for row in policy_rows if row["substep_triggered"] == "true"]
    max_trigger = max(
        (float(row["observed_trigger_value"]) for row in policy_rows),
        default=0.0,
    )
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "timeseries_disposition": timeseries_status.get("disposition", ""),
        "timeseries_artifact_id": timeseries_status.get("artifact_id", ""),
        "timeseries_substep_review_rows": timeseries_status.get("substep_review_rows", 0),
        "policy_rows": len(policy_rows),
        "triggered_policy_rows": len(triggered_rows),
        "proof_field_requirement_rows": len(PROOF_FIELD_REQUIREMENTS),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "substep_trigger_metric": SUBSTEP_TRIGGER_METRIC,
        "substep_trigger_threshold": SUBSTEP_TRIGGER_THRESHOLD,
        "substep_max_observed_trigger_value": round(max_trigger, 9),
        "substep_triggered_scenario_count": len(triggered_rows),
        "substep_policy_bound_trigger_count": len(triggered_rows),
        "substep_policy_status": SUBSTEP_POLICY_STATUS,
        "substep_policy_scope": SUBSTEP_POLICY_SCOPE,
        "validator_hardening_status": VALIDATOR_HARDENING_STATUS,
        "proof_readiness_impact": (
            "future_package_c_proof_pass_hard_fails_without_substep_policy_evidence"
        ),
        "substep_review_required_for_current_candidate": bool(triggered_rows),
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
        "substep_fail_policy": policy_rows,
        "proof_field_requirements": proof_field_requirement_rows(),
        "source_locks": source_rows,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Timeseries disposition": s["timeseries_disposition"]
        == EXPECTED_TIMESERIES_DISPOSITION,
        "Policy row count": s["policy_rows"] > 0,
        "Triggered rows are preserved": s["triggered_policy_rows"] > 0,
        "Proof fields complete": s["proof_field_requirement_rows"]
        == len(PROOF_FIELD_REQUIREMENTS),
        "Source lock complete": s["source_missing_rows"] == 0,
        "Max trigger exceeds threshold": s["substep_max_observed_trigger_value"]
        > SUBSTEP_TRIGGER_THRESHOLD,
        "Triggered scenario count": s["substep_triggered_scenario_count"]
        == s["triggered_policy_rows"],
        "Bound trigger count covers triggered rows": s["substep_policy_bound_trigger_count"]
        >= s["substep_triggered_scenario_count"],
        "Substep policy scope": s["substep_policy_scope"] == SUBSTEP_POLICY_SCOPE,
        "GitHub visibility caveat": s["github_visibility_status"]
        == GITHUB_VISIBILITY_STATUS,
        "Validator hardening status": s["validator_hardening_status"]
        == VALIDATOR_HARDENING_STATUS,
        "Current candidate still needs substep review": (
            s["substep_review_required_for_current_candidate"] is True
        ),
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
            "policy_impact": "substep_fail_policy_hardening_no_proof_registration",
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
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_ROWS_20260701.csv": payload[
            "substep_fail_policy"
        ],
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_PROOF_FIELD_REQUIREMENTS_20260701.csv": payload[
            "proof_field_requirements"
        ],
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_STATUS_20260701.json"
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
        active_output_dir / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_REPORT_20260701.md"
    )
    write_md(
        active_report,
        "NODI COMSOL Package C Substep Fail Policy Hardening",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Policy rows: `{payload['summary']['policy_rows']}`; triggered rows: `{payload['summary']['triggered_policy_rows']}`.",
            f"- Trigger metric: `{SUBSTEP_TRIGGER_METRIC}`; threshold: `{SUBSTEP_TRIGGER_THRESHOLD}`.",
            f"- Max observed trigger value: `{payload['summary']['substep_max_observed_trigger_value']}`.",
            f"- Triggered scenario count: `{payload['summary']['substep_triggered_scenario_count']}`; bound trigger count: `{payload['summary']['substep_policy_bound_trigger_count']}`.",
            f"- Validator hardening: `{payload['summary']['validator_hardening_status']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: proof/pass validator hardening only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = (
        active_report_dir
        / "506_NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_20260701.md"
    )
    write_md(
        public_report,
        "NODI COMSOL Package C Substep Fail Policy Hardening",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet converts the timeseries substep review finding into future Package C proof/pass validator hard-fail requirements.",
            f"- Triggered policy rows: `{payload['summary']['triggered_policy_rows']}` of `{payload['summary']['policy_rows']}`.",
            f"- Max observed `{SUBSTEP_TRIGGER_METRIC}`: `{payload['summary']['substep_max_observed_trigger_value']}`.",
            f"- Triggered scenario count: `{payload['summary']['substep_triggered_scenario_count']}`; bound trigger count: `{payload['summary']['substep_policy_bound_trigger_count']}`.",
            f"- Required proof field rows: `{payload['summary']['proof_field_requirement_rows']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            f"- Validator hardening status: `{payload['summary']['validator_hardening_status']}`.",
            "- Boundary: this is candidate hardening only, not Package C proof registration or runtime authorization.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = (
        active_output_dir / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_MANIFEST_20260701.csv"
    )
    report_path = (
        active_output_dir / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_REPORT_20260701.json"
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
    if not args.confirm_package_c_substep_fail_policy_hardening:
        parser.error("--confirm-package-c-substep-fail-policy-hardening is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
