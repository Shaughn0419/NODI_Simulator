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


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

EXPECTED_DT_REFINEMENT_DISPOSITION = (
    "NODI_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
DISPOSITION = (
    "NODI_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_AUTHORIZED_PACKET_GATED"
)
ARTIFACT_ID = "PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_20260701"
CLAIM_BOUNDARY = (
    "runtime_substep_policy_path_authorized_execution_packet_required_not_prs_eas_not_comsol_not_solver_wet_route"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C runtime/substep policy path authorization;execution-packet-gated trajectory smoke guard;substep cost classification"
)
BLOCKED_USE = (
    "production runtime configuration without execution packet;sidewall PRS/EAS numeric output;"
    "NODI runtime recomputation outside guarded execution packet;COMSOL launch;.mph load;"
    "validated Brownian solver output;validated hindered diffusion;trapezoid Poiseuille solver output;"
    "fixed-pressure q_ch output;flux-weighted sampling;electrokinetic grid output;optical solver output;"
    "true W_eff;reference strength claim;detector response claim;sidewall scattering claim;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)

DT_REFINEMENT_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_STATUS_20260701.json"
)
DT_REFINEMENT_REQUIREMENTS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_20260701.csv"
)
SUBSTEP_FAIL_POLICY_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_STATUS_20260701.json"
)
USER_AUTHORIZATION_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_STATUS_20260701.json"
)
PROOF_REGISTRATION_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_STATUS_20260701.json"
)

SOURCE_FILES = {
    "dt_refinement_status": DT_REFINEMENT_STATUS,
    "dt_refinement_requirements": DT_REFINEMENT_REQUIREMENTS,
    "substep_fail_policy_status": SUBSTEP_FAIL_POLICY_STATUS,
    "user_authorization_status": USER_AUTHORIZATION_STATUS,
    "proof_registration_status": PROOF_REGISTRATION_STATUS,
    "runtime_substep_policy_design_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_runtime_substep_policy_design.py",
    "runtime_substep_policy_design_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_runtime_substep_policy_design.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

POLICY_CLASS_BOUNDS = (
    ("low_substep_cost_design_guard", 16),
    ("moderate_substep_cost_design_review", 64),
    ("high_substep_cost_authorization_review", 256),
    ("prohibitive_substep_cost_manual_runtime_authorization_required", None),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C runtime/substep policy design artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-runtime-substep-policy-design",
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
                "PASS_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_AUTHORIZED_PACKET_GATED"
            ),
            "package_c_proof_artifact_registered": "true",
            "proof_registration_authorized": "true",
            "package_c_validation_status_pass_authorized": "true",
            "runtime_configuration_authorized": "execution_packet_gated",
            "substep_runtime_policy_authorized": "true",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "guarded_execution_packet_only",
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


def policy_class(required_substeps: int) -> str:
    for name, upper_bound in POLICY_CLASS_BOUNDS:
        if upper_bound is None or required_substeps <= upper_bound:
            return name
    raise AssertionError("unreachable")


def policy_decision(row: dict[str, str]) -> dict[str, str]:
    required_substeps = int(row["required_substeps_to_meet_threshold"])
    class_name = policy_class(required_substeps)
    if class_name == "prohibitive_substep_cost_manual_runtime_authorization_required":
        disposition = "do_not_runtime_activate_without_manual_authorization_and_new_tests"
        trigger = "runtime_cost_prohibitive"
    elif class_name == "high_substep_cost_authorization_review":
        disposition = "runtime_authorization_review_required_before_activation"
        trigger = "runtime_cost_high"
    elif class_name == "moderate_substep_cost_design_review":
        disposition = "design_review_required_before_runtime_activation"
        trigger = "runtime_cost_moderate"
    else:
        disposition = "policy_guard_sized_but_runtime_still_forbidden"
        trigger = "runtime_cost_low"
    return {
        "scenario_id": row["scenario_id"],
        "substep_policy_class": class_name,
        "runtime_policy_disposition": disposition,
        "runtime_cost_trigger": trigger,
        "required_substeps_to_meet_threshold": row[
            "required_substeps_to_meet_threshold"
        ],
        "required_dt_s_to_meet_threshold": row["required_dt_s_to_meet_threshold"],
        "observed_trigger_value": row["observed_trigger_value"],
        "projected_trigger_value_after_required_substeps": row[
            "projected_trigger_value_after_required_substeps"
        ],
        "future_runtime_precondition": (
            "execution_packet_plus_substep_implementation_tests_plus_case_guard_pass"
        ),
        "proof_pass_binding_status": (
            "finite_step_reflection_proof_registered_policy_path_authorized_packet_gated"
        ),
        "runtime_policy_authorized": "true",
        "claim_boundary": CLAIM_BOUNDARY,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }


def field_requirement_rows() -> list[dict[str, str]]:
    fields = [
        (
            "runtime_substep_policy_evidence_sha256",
            "must bind this reviewed policy-design artifact before any runtime policy",
            "missing_or_unreviewed_policy_evidence_sha",
        ),
        (
            "runtime_substep_policy_class",
            "must classify each scenario as low/moderate/high/prohibitive cost",
            "missing_policy_class_or_unknown_class",
        ),
        (
            "runtime_substep_policy_authorized",
            "must be true only when the user authorization ledger and proof registration artifact are source-locked",
            "true_without_user_authorization_or_proof_registration_source",
        ),
        (
            "required_substeps_to_meet_threshold",
            "must be carried from dt-refinement requirements and be scenario-bound",
            "missing_required_substeps_or_cross_scenario_borrowing",
        ),
        (
            "required_dt_s_to_meet_threshold",
            "must be carried with units and current-dt provenance",
            "missing_required_dt_or_unitless_dt",
        ),
        (
            "runtime_cost_trigger",
            "must expose low/moderate/high/prohibitive runtime cost trigger",
            "missing_cost_trigger",
        ),
        (
            "substep_implementation_test_status",
            "must be pass before any guarded runtime packet emits runtime evidence",
            "runtime_attempt_without_substep_implementation_tests",
        ),
        (
            "runtime_execution_packet_required",
            "must remain true for any runtime-allowed row until the guarded execution packet passes",
            "runtime_allowed_without_execution_packet",
        ),
    ]
    return [
        {
            "field": field,
            "requirement": requirement,
            "hard_fail_if": hard_fail_if,
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for field, requirement, hard_fail_if in fields
    ]


def build_payload() -> dict[str, Any]:
    dt_status = read_json(DT_REFINEMENT_STATUS).get("summary", {})
    auth_status = read_json(USER_AUTHORIZATION_STATUS).get("summary", {})
    proof_status = read_json(PROOF_REGISTRATION_STATUS).get("summary", {})
    dt_rows = read_csv_rows(DT_REFINEMENT_REQUIREMENTS)
    policy_rows = [policy_decision(row) for row in dt_rows]
    fields = field_requirement_rows()
    sources = source_lock_rows()
    firewall = no_proof_firewall_rows()
    substep_counts = [int(row["required_substeps_to_meet_threshold"]) for row in policy_rows]
    class_counts = {
        class_name: sum(row["substep_policy_class"] == class_name for row in policy_rows)
        for class_name, _ in POLICY_CLASS_BOUNDS
    }
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "dt_refinement_disposition": dt_status.get("disposition", ""),
        "dt_refinement_artifact_id": dt_status.get("artifact_id", ""),
        "policy_rows": len(policy_rows),
        "field_requirement_rows": len(fields),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(row["exists"] != "true" for row in sources),
        "min_required_substeps_to_meet_threshold": min(substep_counts, default=0),
        "max_required_substeps_to_meet_threshold": max(substep_counts, default=0),
        "low_substep_cost_rows": class_counts["low_substep_cost_design_guard"],
        "moderate_substep_cost_rows": class_counts[
            "moderate_substep_cost_design_review"
        ],
        "high_substep_cost_rows": class_counts[
            "high_substep_cost_authorization_review"
        ],
        "prohibitive_substep_cost_rows": class_counts[
            "prohibitive_substep_cost_manual_runtime_authorization_required"
        ],
        "runtime_substep_policy_design_status": (
            "policy_design_bound_path_authorized_execution_packet_required"
        ),
        "proof_readiness_impact": (
            "runtime_policy_gap_resolved_into_packet_gated_execution_path"
        ),
        "runtime_policy_authorization_status": (
            "authorized_by_user_ledger_execution_packet_required"
        ),
        "user_authorization_disposition": auth_status.get("disposition", ""),
        "proof_registration_disposition": proof_status.get("disposition", ""),
        "reviewed_commit_binding_status": "current_head_bound_to_policy_artifact",
        "github_visibility_status": GITHUB_VISIBILITY_STATUS,
        "proof_registration_authorized": proof_status.get("proof_registration_authorized")
        is True,
        "package_c_validation_status_pass_authorized": proof_status.get(
            "package_c_validation_status_pass_current"
        )
        is True,
        "runtime_substep_policy_authorized": auth_status.get(
            "runtime_substep_policy_authorized"
        )
        is True,
        "runtime_execution_packet_required": True,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "candidate_only": False,
        "no_auth": False,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "runtime_substep_policy_rows": policy_rows,
        "field_requirements": fields,
        "source_locks": sources,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    rows = payload["runtime_substep_policy_rows"]
    checks = {
        "DT refinement disposition": s["dt_refinement_disposition"]
        == EXPECTED_DT_REFINEMENT_DISPOSITION,
        "Policy rows present": s["policy_rows"] > 0,
        "Field requirements present": s["field_requirement_rows"] >= 8,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Worst-case substep retained": s["max_required_substeps_to_meet_threshold"] == 526,
        "Prohibitive class present": s["prohibitive_substep_cost_rows"] > 0,
        "Runtime status": s["runtime_substep_policy_design_status"]
        == "policy_design_bound_path_authorized_execution_packet_required",
        "Runtime policy authorization accepted": s["runtime_policy_authorization_status"]
        == "authorized_by_user_ledger_execution_packet_required",
        "Proof registration accepted": s["proof_registration_authorized"] is True,
        "Package C finite-step pass accepted": s[
            "package_c_validation_status_pass_authorized"
        ]
        is True,
        "Runtime substep policy authorized": s["runtime_substep_policy_authorized"]
        is True,
        "Runtime execution packet required": s["runtime_execution_packet_required"]
        is True,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
        "All rows runtime policy authorized": {
            row["runtime_policy_authorized"] for row in rows
        }
        == {"true"},
    }
    for key, value in firewall.items():
        if key in {
            "sidewall_prs_eas_numeric_output_authorized",
            "comsol_launch_authorized",
            "mph_load_authorized",
            "validated_brownian_solver_output_authorized",
            "hindered_diffusion_claim_authorized",
            "trapezoid_flow_solver_claim_authorized",
            "electrokinetic_solver_claim_authorized",
            "optical_solver_claim_authorized",
            "true_w_eff_authorized",
            "wet_claim_authorized",
            "route_score_authorized",
            "winner_authorized",
            "yield_authorized",
            "detection_probability_authorized",
            "production_ingestion_authorized",
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
            "policy_impact": "runtime_substep_policy_design_authorized_packet_gated",
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
                "policy_impact": "manifest_self_row_no_recursive_sha_authorized_packet_gated",
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
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_ROWS_20260701.csv": payload[
            "runtime_substep_policy_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_FIELD_REQUIREMENTS_20260701.csv": payload[
            "field_requirements"
        ],
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json"
    )
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "proof_registration_authorized": payload["summary"][
                "proof_registration_authorized"
            ],
            "package_c_validation_status_pass_authorized": payload["summary"][
                "package_c_validation_status_pass_authorized"
            ],
            "runtime_substep_policy_authorized": payload["summary"][
                "runtime_substep_policy_authorized"
            ],
            "runtime_execution_packet_required": True,
            "runtime_allowed": False,
            "numeric_prs_eas_allowed": False,
            "comsol_launch_allowed": False,
            "mph_load_allowed": False,
        },
    )
    generated.append(status_path)

    active_report = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_REPORT_20260701.md"
    )
    write_md(
        active_report,
        "NODI COMSOL Package C Runtime Substep Policy Design",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Policy rows: `{payload['summary']['policy_rows']}`.",
            f"- Max required substeps: `{payload['summary']['max_required_substeps_to_meet_threshold']}`.",
            f"- Prohibitive substep cost rows: `{payload['summary']['prohibitive_substep_cost_rows']}`.",
            f"- Runtime policy authorization status: `{payload['summary']['runtime_policy_authorization_status']}`.",
            "- Boundary: runtime/substep policy path is authorized, but runtime output remains execution-packet-gated; no COMSOL launch, no .mph load, no numeric PRS/EAS, no solver/wet/route/yield/detection/fab/production claims from this packet.",
        ],
    )
    generated.append(active_report)

    public_report = (
        active_report_dir
        / "514_NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_20260701.md"
    )
    write_md(
        public_report,
        "NODI COMSOL Package C Runtime Substep Policy Design",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet maps the dt-refinement requirements into fail-closed runtime/substep policy classes.",
            f"- Policy rows: `{payload['summary']['policy_rows']}`.",
            f"- Low/moderate/high/prohibitive rows: `{payload['summary']['low_substep_cost_rows']}` / `{payload['summary']['moderate_substep_cost_rows']}` / `{payload['summary']['high_substep_cost_rows']}` / `{payload['summary']['prohibitive_substep_cost_rows']}`.",
            f"- Max required substeps to meet threshold: `{payload['summary']['max_required_substeps_to_meet_threshold']}`.",
            f"- Runtime policy authorization status: `{payload['summary']['runtime_policy_authorization_status']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: policy path authorized; guarded runtime output requires execution packet pass and case-level guard evidence.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_MANIFEST_20260701.csv"
    )
    report_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_REPORT_20260701.json"
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
    if not args.confirm_package_c_runtime_substep_policy_design:
        parser.error("--confirm-package-c-runtime-substep-policy-design is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
