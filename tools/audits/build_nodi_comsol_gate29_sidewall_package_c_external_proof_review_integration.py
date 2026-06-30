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

EXPECTED_GATE28_DISPOSITION = (
    "NODI_GATE28_SIDEWALL_PACKAGE_C_PROOF_REVIEW_PACKET_READY_NO_PROOF_REGISTRATION"
)
EXTERNAL_VERDICT = "READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY"
DISPOSITION = (
    "NODI_GATE29_SIDEWALL_PACKAGE_C_EXTERNAL_PROOF_REVIEW_INTEGRATION_READY_NO_PROOF_REGISTRATION"
)
ALLOWED_USE = (
    "external proof-registration review integration;future hard-gate matrix;"
    "telemetry reproducibility field ledger;no-proof-registration"
)
BLOCKED_USE = (
    "Package C proof/pass registration;package_C_validation_status pass;runtime configuration;"
    "sidewall PRS/EAS numeric output;NODI runtime recomputation;COMSOL launch;.mph load;"
    "validated hindered diffusion;trapezoid Poiseuille solver output;fixed-pressure q_ch output;"
    "flux-weighted sampling;electrokinetic grid output;optical solver output;true W_eff;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)

GATE28_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_STATUS_20260630.json"
GATE28_REPORT = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_REPORT_20260630.json"
GATE28_EVIDENCE = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_20260630.json"
GATE28_SOURCE_LOCK = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_SOURCE_LOCK_20260630.csv"
GATE28_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
GATE28_PROMPT = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_EXTERNAL_REVIEW_PROMPT_20260630.md"
GATE27_PROOF_CONTRACT = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv"

SOURCE_FILES = {
    "gate28_status": GATE28_STATUS,
    "gate28_report": GATE28_REPORT,
    "gate28_evidence": GATE28_EVIDENCE,
    "gate28_source_lock": GATE28_SOURCE_LOCK,
    "gate28_no_proof_firewall": GATE28_FIREWALL,
    "gate28_external_review_prompt": GATE28_PROMPT,
    "gate27_proof_contract": GATE27_PROOF_CONTRACT,
    "next_artifacts_contract": PROJECT_ROOT / "nodi_simulator/nodi_comsol_next_artifacts.py",
    "gate29_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate29_sidewall_package_c_external_proof_review_integration.py",
    "gate29_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate29_sidewall_package_c_external_proof_review_integration.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

TELEMETRY_FIELDS = (
    "reflection_metric_schema_version",
    "reflection_algorithm_source_sha256",
    "reflection_test_script_sha256",
    "test_environment_lock_sha256",
    "dependency_lock_sha256",
    "rng_seed_matrix_sha256",
    "test_parameter_matrix_sha256",
    "dt_grid_s",
    "diffusion_coefficient_grid_m2_s",
    "particle_radius_grid_nm",
    "sidewall_angle_grid_deg_comsol",
    "depth_grid_nm",
    "tolerance_m",
    "max_reflection_iterations",
    "substep_policy",
    "boundary_atom_threshold",
    "equilibrium_test_method",
    "equilibrium_test_threshold",
    "corner_bias_test_threshold",
    "rectangle_limit_tolerance",
    "one_wall_limit_tolerance",
    "raw_metric_artifact_sha256",
    "summary_metric_artifact_sha256",
    "independent_reviewer_id_or_artifact_sha256",
)

FUTURE_HARD_GATES = (
    "package_C_proof_artifact_registered",
    "proof_registration_authorized",
    "implementation_commit_sha",
    "required_test_result_artifact_sha256",
    "dt_convergence_evidence_sha256",
    "equilibrium_uniformity_evidence_sha256",
    "no_boundary_atom_evidence_sha256",
    "corner_active_set_evidence_sha256",
    "angle_depth_mutation_evidence_sha256",
    "rectangle_limit_evidence_sha256",
    "external_review_artifact_sha256",
    "authorization_supersedes_no_auth_ledger_sha256",
    "package_C_proof_no_hindered_diffusion_claim",
    "package_C_proof_no_trapezoid_flow_solver_claim",
    "package_C_proof_no_electrokinetic_solver_claim",
    "package_C_proof_no_optical_solver_claim",
    "package_C_proof_no_wet_claim",
    "package_C_proof_no_prs_eas_numeric_output",
    "package_C_proof_no_route_yield_detection_claim",
)

REPORTS = {
    "475": "GATE29A_EXTERNAL_PROOF_REVIEW_INTAKE",
    "476": "GATE29B_PACKAGE_C_FUTURE_PROOF_HARD_GATES",
    "477": "GATE29C_PACKAGE_C_TELEMETRY_REPRODUCIBILITY_FIELDS",
    "478": "GATE29D_NO_PROOF_REGISTRATION_FIREWALL",
    "479": "GATE29_SIDEWALL_PACKAGE_C_EXTERNAL_PROOF_REVIEW_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate29 Package C external proof-review integration.")
    parser.add_argument("--confirm-gate29-package-c-external-proof-review-integration", action="store_true")
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


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
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "exists": bool_text(exists),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def gate27_proof_contract_fields() -> set[str]:
    if not GATE27_PROOF_CONTRACT.exists():
        return set()
    return {
        row.get("required_field", "")
        for row in read_csv_rows(GATE27_PROOF_CONTRACT)
        if row.get("required_field")
    }


def external_review_capture_text() -> str:
    return """# Gate29 External Proof-Review Feedback Capture

Verdict: READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY.

Meaning:
- Gate28 is sufficient as an external proof-registration review packet.
- This is not Package C proof/pass registration.
- This is not runtime authorization.
- This is not COMSOL launch or `.mph` authorization.
- This is not PRS/EAS numeric output authorization.
- This is not route/yield/detection/fabrication/production authorization.

Key reviewer constraints:
- Keep the model labeled as a skorokhod-target finite-step normal-reflection
  surrogate, not a validated Brownian solver output.
- Future proof registration needs independent sha-bound evidence for
  dt-halving convergence, equilibrium uniformity, no-boundary-atom behavior,
  corner active-set convergence/bias, angle/depth/radius mutation, rectangle
  limit, one-wall limit, closed/near-closed geometry blocking, raw metrics,
  summary metrics, source/environment locks, external review, and superseding
  authorization.
- Future proof/pass claim level should be
  `finite_step_reflection_surrogate_validated_by_required_tests`, not a
  hydrodynamic, wet, optical, route, yield, or detection claim.
"""


def review_intake_rows() -> list[dict[str, str]]:
    return [
        {
            "review_id": "G29-REVIEW-001",
            "external_verdict": EXTERNAL_VERDICT,
            "accepted_scope": "external_proof_registration_review_only",
            "not_authorized": (
                "proof_registration;runtime;numeric_prs_eas;comsol_launch;mph_load;"
                "hindered_diffusion;flow_solver;electrokinetic_solver;optical_solver;"
                "route_yield_detection_wet_fab_production"
            ),
            "required_next_action": "convert_feedback_to_future_hard_gates_no_proof_registration",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def hard_gate_rows() -> list[dict[str, str]]:
    rows = []
    for idx, gate in enumerate(FUTURE_HARD_GATES, start=1):
        rows.append(
            {
                "gate_id": f"G29-HARD-GATE-{idx:03d}",
                "future_required_gate": gate,
                "required_before_package_c_pass": "true",
                "current_status": "missing_or_not_authorized_no_proof_registration",
                "current_gate29_response": "hard_fail_future_registration",
                "can_register_package_c_proof_now": "false",
                "can_emit_runtime_now": "false",
                "can_emit_numeric_prs_eas_now": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def telemetry_rows() -> list[dict[str, str]]:
    rows = []
    for idx, field in enumerate(TELEMETRY_FIELDS, start=1):
        rows.append(
            {
                "field_id": f"G29-TELEMETRY-FIELD-{idx:03d}",
                "required_future_field": field,
                "required_before_package_c_pass": "true",
                "source": "external_proof_review_feedback",
                "current_status": "required_in_gate27_contract_no_registered_value",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_GATE29_EXTERNAL_REVIEW_INTEGRATED_NO_PROOF_REGISTRATION",
            "package_c_proof_artifact_registered": "false",
            "package_c_validation_status_pass_authorized": "false",
            "proof_registry_update_authorized": "false",
            "runtime_configuration_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
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


def build_payload() -> dict[str, Any]:
    gate28_status = read_json(GATE28_STATUS)
    gate28_summary = gate28_status.get("summary", {})
    contract_fields = gate27_proof_contract_fields()
    source_rows = source_lock_rows()
    hard_gates = hard_gate_rows()
    telemetry = telemetry_rows()
    firewall = firewall_rows()
    summary = {
        "disposition": DISPOSITION,
        "gate29_build_head": safe_git_head(),
        "external_verdict": EXTERNAL_VERDICT,
        "gate28_disposition": gate28_status.get("disposition", ""),
        "gate28_evidence_pass_rows": gate28_summary.get("evidence_pass_rows", 0),
        "gate28_evidence_fail_rows": gate28_summary.get("evidence_fail_rows", -1),
        "gate28_no_auth": gate28_status.get("no_auth") is True,
        "gate28_proof_registration_authorized": gate28_status.get(
            "proof_registration_authorized"
        )
        is True,
        "gate27_proof_contract_field_rows": len(contract_fields),
        "gate27_required_proof_contract_field_rows": len(REQUIRED_PROOF_CONTRACT_FIELDS),
        "gate27_missing_required_proof_contract_fields": sorted(
            REQUIRED_PROOF_CONTRACT_FIELDS - contract_fields
        ),
        "gate27_extra_proof_contract_fields": sorted(
            contract_fields - REQUIRED_PROOF_CONTRACT_FIELDS
        ),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "future_hard_gate_rows": len(hard_gates),
        "telemetry_field_rows": len(telemetry),
        "no_proof_firewall_failures": 0
        if firewall[0]["firewall_status"]
        == "PASS_GATE29_EXTERNAL_REVIEW_INTEGRATED_NO_PROOF_REGISTRATION"
        else 1,
        "proof_registration_authorized": False,
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
        "summary": summary,
        "source_locks": source_rows,
        "review_intake": review_intake_rows(),
        "future_hard_gates": hard_gates,
        "telemetry_fields": telemetry,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Gate28 disposition": s["gate28_disposition"] == EXPECTED_GATE28_DISPOSITION,
        "Gate28 evidence pass": s["gate28_evidence_pass_rows"] >= 6,
        "Gate28 evidence failures": s["gate28_evidence_fail_rows"] == 0,
        "Gate28 no-auth": s["gate28_no_auth"] is True,
        "Gate28 no proof registration": s["gate28_proof_registration_authorized"] is False,
        "Gate27 proof contract complete": s["gate27_proof_contract_field_rows"]
        == len(REQUIRED_PROOF_CONTRACT_FIELDS),
        "Gate27 proof contract no missing": not s[
            "gate27_missing_required_proof_contract_fields"
        ],
        "Gate27 proof contract no extra": not s["gate27_extra_proof_contract_fields"],
        "Sources present": s["source_missing_rows"] == 0,
        "Future hard gates present": s["future_hard_gate_rows"] >= len(FUTURE_HARD_GATES),
        "Telemetry fields present": s["telemetry_field_rows"] == len(TELEMETRY_FIELDS),
        "No-proof firewall": s["no_proof_firewall_failures"] == 0,
        "No proof registration": s["proof_registration_authorized"] is False,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
    }
    for key, value in firewall.items():
        if key.endswith("_authorized") or key == "package_c_proof_artifact_registered":
            checks[f"No-proof false: {key}"] = value == "false"
    return [label for label, ok in checks.items() if not ok]


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    return [
        {
            "artifact": path.name,
            "path": path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_file(path) if path.exists() else "",
            "disposition": DISPOSITION,
            "policy_impact": "none_no_proof_registration",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for path in paths
    ]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    feedback_path = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_EXTERNAL_REVIEW_CAPTURE_20260630.md"
    feedback_path.write_text(external_review_capture_text(), encoding="utf-8")
    generated.append(feedback_path)

    csv_specs = {
        "NODI_COMSOL_GATE29_SIDEWALL_SOURCE_LOCK_20260630.csv": payload["source_locks"],
        "NODI_COMSOL_GATE29_SIDEWALL_EXTERNAL_REVIEW_INTAKE_20260630.csv": payload["review_intake"],
        "NODI_COMSOL_GATE29_SIDEWALL_FUTURE_PROOF_HARD_GATES_20260630.csv": payload["future_hard_gates"],
        "NODI_COMSOL_GATE29_SIDEWALL_TELEMETRY_REPRODUCIBILITY_FIELDS_20260630.csv": payload["telemetry_fields"],
        "NODI_COMSOL_GATE29_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv": payload["no_proof_firewall"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)

    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)

    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(
        status_json,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "review_only": True,
            "no_auth": True,
            "proof_registration_authorized": False,
        },
    )
    generated.append(status_json)

    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_EXTERNAL_PROOF_REVIEW_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate29 Sidewall Package C External Proof Review Integration",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- External verdict: `{EXTERNAL_VERDICT}`",
            f"- Gate27 proof contract fields: {payload['summary']['gate27_proof_contract_field_rows']}/{payload['summary']['gate27_required_proof_contract_field_rows']}.",
            f"- Future hard gates / telemetry fields: {payload['summary']['future_hard_gate_rows']}/{payload['summary']['telemetry_field_rows']}.",
            "- Boundary: no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
        ],
    )
    generated.append(master_md)

    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)

    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate29 disposition: `{DISPOSITION}`",
                f"- External verdict: `{EXTERNAL_VERDICT}`",
                f"- Future hard gates / telemetry fields: {payload['summary']['future_hard_gate_rows']}/{payload['summary']['telemetry_field_rows']}.",
                "- Boundary: no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate29_package_c_external_proof_review_integration:
        parser.error("--confirm-gate29-package-c-external-proof-review-integration is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE29_SIDEWALL_PACKAGE_C_EXTERNAL_PROOF_REVIEW_INTEGRATION")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
