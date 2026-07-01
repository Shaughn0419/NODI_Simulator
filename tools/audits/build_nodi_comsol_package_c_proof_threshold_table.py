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

DISPOSITION = "NODI_PACKAGE_C_PROOF_THRESHOLD_TABLE_CANDIDATE_READY_NO_PROOF_REGISTRATION"
ARTIFACT_ID = "PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701"
CLAIM_BOUNDARY = "proof_threshold_table_candidate_not_package_c_proof_registered_not_runtime"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C proof-threshold table candidate;candidate/proof gap planning;"
    "external review context;no-proof-registration"
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

CONSOLIDATION_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_STATUS_20260701.json"
)
TIMESERIES_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_STATUS_20260701.json"
)
SUBSTEP_HARDENING_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_STATUS_20260701.json"
)
DT_REFINEMENT_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_STATUS_20260701.json"
)

SOURCE_FILES = {
    "consolidation_status": CONSOLIDATION_STATUS,
    "timeseries_status": TIMESERIES_STATUS,
    "substep_hardening_status": SUBSTEP_HARDENING_STATUS,
    "dt_refinement_status": DT_REFINEMENT_STATUS,
    "threshold_table_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_proof_threshold_table.py",
    "threshold_table_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_proof_threshold_table.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C candidate/proof threshold table artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-proof-threshold-table",
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


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_PACKAGE_C_PROOF_THRESHOLD_TABLE_NO_PROOF_REGISTRATION",
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


def _threshold_row(
    *,
    metric_id: str,
    observed_value: Any,
    candidate_acceptance: str,
    proof_acceptance: str,
    current_status: str,
    source_artifact: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "metric_id": metric_id,
        "observed_value": str(observed_value),
        "candidate_acceptance": candidate_acceptance,
        "proof_acceptance": proof_acceptance,
        "current_status": current_status,
        "source_artifact": source_artifact,
        "next_action": next_action,
        "claim_boundary": CLAIM_BOUNDARY,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }


def threshold_rows() -> list[dict[str, str]]:
    c = read_json_summary(CONSOLIDATION_STATUS)
    t = read_json_summary(TIMESERIES_STATUS)
    s = read_json_summary(SUBSTEP_HARDENING_STATUS)
    d = read_json_summary(DT_REFINEMENT_STATUS)
    rows = [
        _threshold_row(
            metric_id="support_violation_rows",
            observed_value=t.get("support_violation_rows", ""),
            candidate_acceptance="must_equal_0",
            proof_acceptance="must_equal_0",
            current_status="candidate_and_proof_threshold_met_not_registered",
            source_artifact="timeseries_ess_candidate",
            next_action="bind_to_clean_reviewed_commit_and_authorization",
        ),
        _threshold_row(
            metric_id="nonconverged_reflection_rows",
            observed_value=t.get("nonconverged_reflection_rows", ""),
            candidate_acceptance="must_equal_0",
            proof_acceptance="must_equal_0",
            current_status="candidate_and_proof_threshold_met_not_registered",
            source_artifact="timeseries_ess_candidate",
            next_action="bind_to_clean_reviewed_commit_and_authorization",
        ),
        _threshold_row(
            metric_id="max_exact_boundary_atom_fraction",
            observed_value=c.get("max_exact_boundary_atom_fraction", ""),
            candidate_acceptance="<=0.005",
            proof_acceptance="must_equal_0",
            current_status="candidate_and_proof_threshold_met_not_registered",
            source_artifact="metric_hardening_consolidation",
            next_action="bind_exact_atom_definition_and_raw_histogram_sha",
        ),
        _threshold_row(
            metric_id="max_near_boundary_band_fraction",
            observed_value=c.get("max_near_boundary_band_fraction", ""),
            candidate_acceptance="<=0.005",
            proof_acceptance="requires_area_expectation_plus_confidence_interval",
            current_status="candidate_pass_proof_method_gap",
            source_artifact="metric_hardening_consolidation",
            next_action="bind expected band mass method and uncertainty",
        ),
        _threshold_row(
            metric_id="max_one_wall_positive_control_ks",
            observed_value=c.get("max_one_wall_positive_control_ks", ""),
            candidate_acceptance="<=0.02",
            proof_acceptance="<=0.01",
            current_status="candidate_pass_proof_gap",
            source_artifact="metric_hardening_consolidation",
            next_action="tighten one-wall proof threshold or expand samples",
        ),
        _threshold_row(
            metric_id="projection_negative_control_status",
            observed_value=c.get("projection_negative_control_status", ""),
            candidate_acceptance="expected_fail_observed",
            proof_acceptance="expected_fail_observed",
            current_status="candidate_and_proof_threshold_met_not_registered",
            source_artifact="metric_hardening_consolidation",
            next_action="bind negative-control artifact sha",
        ),
        _threshold_row(
            metric_id="max_expanded_wall_pileup_ratio",
            observed_value=c.get("max_expanded_first_vs_adjacent_gap_band_smoothed_ratio", ""),
            candidate_acceptance="<=1.5",
            proof_acceptance="<=1.25",
            current_status="candidate_pass_proof_gap",
            source_artifact="metric_hardening_consolidation",
            next_action="expand or justify wall-pileup proof threshold",
        ),
        _threshold_row(
            metric_id="min_effective_sample_size",
            observed_value=t.get("min_effective_sample_size", ""),
            candidate_acceptance=">=20",
            proof_acceptance="effective_sample_size>=5000_or_confidence_interval_justified",
            current_status="candidate_pass_proof_gap",
            source_artifact="timeseries_ess_candidate",
            next_action="increase ESS or bind confidence interval method",
        ),
        _threshold_row(
            metric_id="max_u_accessible_cdf_l1_to_uniform",
            observed_value=t.get("max_u_accessible_cdf_l1_to_uniform", ""),
            candidate_acceptance="<=0.30",
            proof_acceptance="<=0.04_hard_target_<=0.03",
            current_status="candidate_pass_proof_gap",
            source_artifact="timeseries_ess_candidate",
            next_action="longer chains or proof-level stationarity method",
        ),
        _threshold_row(
            metric_id="max_x_local_norm_l1_to_uniform",
            observed_value=t.get("max_x_local_norm_l1_to_uniform", ""),
            candidate_acceptance="<=0.30",
            proof_acceptance="<=0.04_hard_target_<=0.03",
            current_status="candidate_pass_proof_gap",
            source_artifact="timeseries_ess_candidate",
            next_action="longer chains or proof-level stationarity method",
        ),
        _threshold_row(
            metric_id="substep_policy_bound_trigger_count",
            observed_value=s.get("substep_policy_bound_trigger_count", ""),
            candidate_acceptance="equals_triggered_scenario_count",
            proof_acceptance="equals_triggered_scenario_count_and_policy_evidence_sha_bound",
            current_status="candidate_pass_proof_authorization_gap",
            source_artifact="substep_fail_policy_hardening",
            next_action="bind policy evidence sha in future proof/pass row",
        ),
        _threshold_row(
            metric_id="max_required_substeps_to_meet_threshold",
            observed_value=d.get("max_required_substeps_to_meet_threshold", ""),
            candidate_acceptance="sized_and_reported",
            proof_acceptance="manual_runtime_cost_review_or_smaller_dt_policy_required",
            current_status="candidate_sized_runtime_policy_gap",
            source_artifact="substep_dt_refinement_requirements",
            next_action="manual authorization before runtime/substep policy",
        ),
        _threshold_row(
            metric_id="max_projected_trigger_value_after_required_substeps",
            observed_value=d.get("max_projected_trigger_value_after_required_substeps", ""),
            candidate_acceptance="<=1.0",
            proof_acceptance="<=1.0_with_validated_substep_tests",
            current_status="candidate_pass_proof_runtime_gap",
            source_artifact="substep_dt_refinement_requirements",
            next_action="validate substep implementation before runtime use",
        ),
    ]
    return rows


def build_payload() -> dict[str, Any]:
    rows = threshold_rows()
    source_rows = source_lock_rows()
    firewall = no_proof_firewall_rows()
    status_counts = {
        "candidate_pass_rows": sum("candidate_pass" in row["current_status"] for row in rows),
        "proof_gap_rows": sum("proof_gap" in row["current_status"] for row in rows),
        "runtime_policy_gap_rows": sum(
            "runtime" in row["current_status"] for row in rows
        ),
        "proof_threshold_met_not_registered_rows": sum(
            "proof_threshold_met_not_registered" in row["current_status"]
            for row in rows
        ),
    }
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "threshold_rows": len(rows),
        **status_counts,
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "threshold_table_status": "candidate_threshold_table_ready_not_proof_registered",
        "proof_readiness_impact": "proof_gaps_are_explicit_and_machine_readable",
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
        "threshold_rows": rows,
        "source_locks": source_rows,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Threshold rows present": s["threshold_rows"] >= 10,
        "Proof gaps explicit": s["proof_gap_rows"] > 0,
        "Runtime gaps explicit": s["runtime_policy_gap_rows"] > 0,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Threshold table status": s["threshold_table_status"]
        == "candidate_threshold_table_ready_not_proof_registered",
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
            "policy_impact": "proof_threshold_table_no_proof_registration",
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
        "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv": payload[
            "threshold_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_STATUS_20260701.json"
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

    active_report = active_output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_REPORT_20260701.md"
    write_md(
        active_report,
        "NODI COMSOL Package C Proof Threshold Table",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Threshold rows: `{payload['summary']['threshold_rows']}`.",
            f"- Candidate-pass rows: `{payload['summary']['candidate_pass_rows']}`; proof-gap rows: `{payload['summary']['proof_gap_rows']}`.",
            f"- Runtime-policy gap rows: `{payload['summary']['runtime_policy_gap_rows']}`.",
            "- Boundary: threshold planning only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = active_report_dir / "508_NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.md"
    write_md(
        public_report,
        "NODI COMSOL Package C Proof Threshold Table",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet makes candidate/proof thresholds and remaining proof gaps machine-readable.",
            f"- Threshold rows: `{payload['summary']['threshold_rows']}`.",
            f"- Candidate-pass rows: `{payload['summary']['candidate_pass_rows']}`; proof-gap rows: `{payload['summary']['proof_gap_rows']}`; runtime-policy gap rows: `{payload['summary']['runtime_policy_gap_rows']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: this is threshold planning evidence only, not Package C proof registration or runtime authorization.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_MANIFEST_20260701.csv"
    report_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_REPORT_20260701.json"
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
    if not args.confirm_package_c_proof_threshold_table:
        parser.error("--confirm-package-c-proof-threshold-table is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_PROOF_THRESHOLD_TABLE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
