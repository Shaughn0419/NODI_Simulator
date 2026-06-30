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

from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    APERTURE_SURROGATE_ARTIFACT,
    POSITION_RESPONSE_ARTIFACT,
    PRS_SIDEWALL_V2_PROPAGATED_SCOPE,
    SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_ID,
    SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_SHA256,
    SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_SHA256_BY_ID,
    SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_STATUS,
    SIDEWALL_PACKAGE_D_PRECHECK_ARTIFACT,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

EXPECTED_GATE22_DISPOSITION = "NODI_GATE22_SIDEWALL_VALIDATOR_BINDING_MATRIX_READY_NO_AUTH"
DISPOSITION = "NODI_GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION_READY_NO_AUTH"
ALLOWED_USE = "review-only Gate22-to-Gate23 static executable fixture packet;no-run no-auth"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;rank;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;formula use;direct PRS bin;"
    "grain-level ingestion;sidewall PRS/EAS numeric output;validated Brownian/flow/optical/wet physics;"
    "COMSOL launch;.mph load;NODI runtime recomputation;Package C physics authorization"
)

GATE22_FILES = {
    "status": OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_MANIFEST_20260630.csv",
    "bindings": OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_VALIDATOR_BINDING_MATRIX_20260630.csv",
    "coverage": OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_PYTEST_COVERAGE_MATRIX_20260630.csv",
    "readiness": OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_FIXTURE_EXECUTION_READINESS_20260630.csv",
}

REPORTS = {
    "437": "GATE23A_GATE22_SOURCE_LOCK",
    "438": "GATE23B_STATIC_FIXTURE_EXECUTION_MATRIX",
    "439": "GATE23C_VALIDATOR_CLI_BOUNDARY_MATRIX",
    "440": "GATE23D_PACKAGE_C_PROOF_FAIL_CLOSED_LOCK",
    "441": "GATE23E_NO_AUTH_FIREWALL",
    "442": "GATE23F_VALIDATION_AND_REGRESSION_PLAN",
    "443": "GATE23G_FUTURE_AUTHORIZATION_BLOCKERS",
    "444": "GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate23 sidewall static fixture execution packet.")
    parser.add_argument("--confirm-gate23-static-fixture-execution", action="store_true")
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


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G23-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def gate22_source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    manifest = read_csv_rows(GATE22_FILES["manifest"]) if GATE22_FILES["manifest"].exists() else []
    for idx, item in enumerate(manifest, start=1):
        path = PROJECT_ROOT / item["path"]
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_rows = csv_count(path) if exists else "MISSING"
        expected_rows = item.get("row_count", "NA")
        row_match = expected_rows == "NA" or actual_rows == expected_rows
        sha_match = actual_sha == item.get("sha256", "")
        if not exists:
            status = "MISSING_GATE22_ARTIFACT"
        elif not sha_match or not row_match:
            status = "BLOCKING_GATE22_SOURCE_DRIFT"
        else:
            status = "MATCH"
        rows.append(
            {
                "source_lock_id": f"G23A-GATE22-{idx:03d}",
                "source_gate": "Gate22",
                "path": item["path"],
                "expected_row_count": expected_rows,
                "actual_row_count": actual_rows,
                "expected_sha256": item.get("sha256", ""),
                "actual_sha256": actual_sha,
                "sha256_match": bool_text(sha_match),
                "row_count_match": bool_text(row_match),
                "lock_status": status,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def static_fixture_execution_rows() -> list[dict[str, str]]:
    bindings = read_csv_rows(GATE22_FILES["bindings"])
    coverage = {row["family_id"]: row for row in read_csv_rows(GATE22_FILES["coverage"])}
    rows: list[dict[str, str]] = []
    for idx, binding in enumerate(bindings, start=1):
        coverage_row = coverage.get(binding["family_id"], {})
        pytest_file = coverage_row.get("pytest_file", "")
        pytest_marker = coverage_row.get("pytest_marker", "")
        executable = (
            binding.get("binding_status") == "PASS_CALLABLE_STATIC_BINDING"
            and coverage_row.get("coverage_status") == "PASS_PYTEST_MARKER_PRESENT"
            and bool(pytest_file)
            and bool(pytest_marker)
        )
        rows.append(
            {
                "fixture_execution_id": f"G23B-STATIC-FIXTURE-{idx:03d}",
                "family_id": binding["family_id"],
                "hard_fail_code": binding["hard_fail_code"],
                "source_package": binding["source_package"],
                "validator_entrypoint": binding["validator_entrypoint"],
                "expected_rule_family": binding["expected_rule_family"],
                "fixture_scope": binding["fixture_scope"],
                "pytest_file": pytest_file,
                "pytest_marker": pytest_marker,
                "static_command": f"python -m pytest {pytest_file} -q -k {pytest_marker}",
                "execution_mode": "static_pytest_or_validator_function_only",
                "execution_status": "PASS_STATIC_FIXTURE_EXECUTABLE_NO_RUNTIME" if executable else "BLOCKED_STATIC_FIXTURE_NOT_EXECUTABLE",
                "runtime_allowed": "false",
                "production_allowed": "false",
                "claim_promotion_allowed": "false",
                "sidewall_numeric_output_allowed": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def cli_boundary_rows() -> list[dict[str, str]]:
    cli_specs = [
        (
            POSITION_RESPONSE_ARTIFACT,
            "tools/audits/validate_nodi_position_response_surface.py",
            "PASS_CONTEXT_ONLY_NOT_PRODUCTION",
        ),
        (
            APERTURE_SURROGATE_ARTIFACT,
            "tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py",
            "PASS_CONTEXT_ONLY_NOT_PRODUCTION",
        ),
        (
            SIDEWALL_PACKAGE_D_PRECHECK_ARTIFACT,
            "tools/audits/validate_nodi_sidewall_package_d_precheck.py",
            "PASS_CONTEXT_ONLY_NOT_PRODUCTION",
        ),
    ]
    return [
        {
            "cli_boundary_id": f"G23C-CLI-{idx:03d}",
            "artifact": artifact,
            "cli_path": cli_path,
            "success_status_contract": status,
            "bare_PASS_allowed": "false",
            "runtime_allowed": "false",
            "production_allowed": "false",
            "claim_promotion_allowed": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (artifact, cli_path, status) in enumerate(cli_specs, start=1)
    ]


def package_c_proof_lock_rows() -> list[dict[str, str]]:
    fail_closed = (
        SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_ID == ""
        and SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_SHA256 == ""
        and len(SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_SHA256_BY_ID) == 0
        and "not_authorized" in SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_STATUS
    )
    scope_is_package_b_only = (
        PRS_SIDEWALL_V2_PROPAGATED_SCOPE
        == "particle_center_support_only_not_reference_fluidic_electrokinetic"
    )
    return [
        {
            "lock_id": "G23D-PACKAGE-C-PROOF-001",
            "lock_scope": "package_C_authorization_proof_registry",
            "proof_artifact_id": SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_ID,
            "proof_artifact_sha256": SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_SHA256,
            "proof_registry_entries": str(len(SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_SHA256_BY_ID)),
            "proof_artifact_status": SIDEWALL_PACKAGE_C_PROOF_ARTIFACT_STATUS,
            "package_C_validation_status_pass_allowed": bool_text(not fail_closed),
            "lock_status": "PASS_FAIL_CLOSED_NO_AUTH" if fail_closed else "FAIL_PACKAGE_C_PROOF_REGISTRY_OPEN",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "lock_id": "G23D-PACKAGE-C-PROOF-002",
            "lock_scope": "prs_sidewall_default_propagated_scope",
            "proof_artifact_id": "",
            "proof_artifact_sha256": "",
            "proof_registry_entries": "0",
            "proof_artifact_status": PRS_SIDEWALL_V2_PROPAGATED_SCOPE,
            "package_C_validation_status_pass_allowed": "false",
            "lock_status": "PASS_PACKAGE_B_CENTER_SUPPORT_ONLY" if scope_is_package_b_only else "FAIL_DEFAULT_SCOPE_PROMOTES_PACKAGE_C",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
    ]


def no_auth_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G23E-NOAUTH-001",
            "runtime_configuration_authorized": "false",
            "production_ingestion_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "nodi_runtime_recompute_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "fabrication_release_authorized": "false",
            "package_c_physics_authorized": "false",
            "firewall_status": "PASS_NO_AUTH_LOCKS_PRESERVED",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def future_authorization_blocker_rows() -> list[dict[str, str]]:
    blockers = [
        ("Package C trajectory", "validated sloped-wall reflection artifact absent"),
        ("Package C near-wall diffusion", "validated trapezoid hindered-diffusion artifact absent"),
        ("Package C flow", "compatible trapezoid flow field or flux-weighted sampler artifact absent"),
        ("Package C optical", "optical/reference-field solver output absent"),
        ("Production", "sidewall PRS/EAS remains context-only/not-production"),
    ]
    return [
        {
            "blocker_id": f"G23G-BLOCKER-{idx:03d}",
            "blocked_scope": scope,
            "blocker_reason": reason,
            "required_future_authorization": "explicit user-selected physics/runtime gate",
            "current_status": "BLOCKED_NO_AUTH",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (scope, reason) in enumerate(blockers, start=1)
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate23_sidewall_static_fixture_execution.py --confirm-gate23-static-fixture-execution",
        "python -m py_compile tools/audits/build_nodi_comsol_gate23_sidewall_static_fixture_execution.py",
        "python -m pytest tests/test_nodi_comsol_gate23_sidewall_static_fixture_execution.py -q",
        "python -m pytest tests/test_nodi_comsol_gate22_sidewall_validator_binding.py tests/test_nodi_comsol_gate23_sidewall_static_fixture_execution.py -q",
        "python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py tests/test_cross_section_geometry.py -q",
    ]
    return [
        {"validation_id": f"G23F-VALIDATION-{idx:03d}", "command": command, "required_for_pass": "true", "recorded_result": "PENDING_RUNTIME_VALIDATION"}
        for idx, command in enumerate(commands, start=1)
    ]


def build_payload() -> dict[str, Any]:
    gate22_status = read_json(GATE22_FILES["status"])
    gate22_summary = gate22_status.get("summary", {})
    current_head = safe_git_head(PROJECT_ROOT)
    source_locks = gate22_source_lock_rows()
    fixture_rows = static_fixture_execution_rows()
    cli_rows = cli_boundary_rows()
    package_c_locks = package_c_proof_lock_rows()
    firewall = no_auth_firewall_rows()
    blockers = future_authorization_blocker_rows()
    readiness_rows = read_csv_rows(GATE22_FILES["readiness"]) if GATE22_FILES["readiness"].exists() else []
    summary = {
        "disposition": DISPOSITION,
        "gate23_build_head": current_head,
        "gate23_package_expected_successor_policy": (
            "final package/report commit may be a clean successor to gate23_build_head; source semantics are pinned to Gate22 manifest hashes"
        ),
        "gate22_build_head": gate22_summary.get("gate22_build_head", ""),
        "gate22_head_is_ancestor_of_current": git_is_ancestor(gate22_summary.get("gate22_build_head", ""), current_head, PROJECT_ROOT),
        "gate22_disposition": gate22_status.get("disposition", ""),
        "gate22_no_auth": gate22_status.get("no_auth", False),
        "gate22_review_only": gate22_status.get("review_only", False),
        "gate22_source_lock_rows": len(source_locks),
        "gate22_source_drift": sum(row["lock_status"] == "BLOCKING_GATE22_SOURCE_DRIFT" for row in source_locks),
        "gate22_missing_sources": sum(row["lock_status"] == "MISSING_GATE22_ARTIFACT" for row in source_locks),
        "gate22_readiness_rows": len(readiness_rows),
        "gate22_readiness_blocked_scopes": sum(row.get("readiness_status") != "PASS_READY_FOR_GATE23_STATIC_FIXTURE_EXECUTION_PLAN" for row in readiness_rows),
        "static_fixture_execution_rows": len(fixture_rows),
        "static_fixture_execution_blocked": sum(row["execution_status"] != "PASS_STATIC_FIXTURE_EXECUTABLE_NO_RUNTIME" for row in fixture_rows),
        "cli_boundary_rows": len(cli_rows),
        "cli_boundary_failures": sum(row["success_status_contract"] != "PASS_CONTEXT_ONLY_NOT_PRODUCTION" for row in cli_rows),
        "package_c_proof_lock_rows": len(package_c_locks),
        "package_c_proof_lock_failures": sum(not row["lock_status"].startswith("PASS_") for row in package_c_locks),
        "future_authorization_blockers": len(blockers),
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED" else 1,
        "runtime_allowed_rows": sum(row["runtime_allowed"] == "true" for row in fixture_rows + cli_rows),
        "production_allowed_rows": sum(row["production_allowed"] == "true" for row in fixture_rows + cli_rows),
        "sidewall_numeric_output_rows": sum(row["sidewall_numeric_output_allowed"] == "true" for row in fixture_rows),
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "gate22_source_locks": source_locks,
        "static_fixture_execution": fixture_rows,
        "cli_boundary": cli_rows,
        "package_c_proof_locks": package_c_locks,
        "no_auth_firewall": firewall,
        "future_authorization_blockers": blockers,
        "validation_plan": validation_plan(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "Gate22 head ancestry": s["gate22_head_is_ancestor_of_current"] is True,
        "Gate22 disposition": s["gate22_disposition"] == EXPECTED_GATE22_DISPOSITION,
        "Gate22 no-auth": s["gate22_no_auth"] is True,
        "Gate22 review-only": s["gate22_review_only"] is True,
        "Gate22 source lock rows": s["gate22_source_lock_rows"] >= 10,
        "Gate22 source drift": s["gate22_source_drift"] == 0,
        "Gate22 missing sources": s["gate22_missing_sources"] == 0,
        "Gate22 readiness rows": s["gate22_readiness_rows"] == 4,
        "Gate22 readiness blocked scopes": s["gate22_readiness_blocked_scopes"] == 0,
        "Static fixture execution rows": s["static_fixture_execution_rows"] >= 29,
        "Static fixture execution blocked": s["static_fixture_execution_blocked"] == 0,
        "CLI boundary rows": s["cli_boundary_rows"] == 3,
        "CLI boundary failures": s["cli_boundary_failures"] == 0,
        "Package C proof locks": s["package_c_proof_lock_rows"] == 2,
        "Package C proof lock failures": s["package_c_proof_lock_failures"] == 0,
        "Future authorization blockers": s["future_authorization_blockers"] >= 5,
        "No-auth firewall": s["no_auth_firewall_failures"] == 0,
        "Runtime allowed rows": s["runtime_allowed_rows"] == 0,
        "Production allowed rows": s["production_allowed_rows"] == 0,
        "Sidewall numeric output rows": s["sidewall_numeric_output_rows"] == 0,
    }
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE23_SIDEWALL_GATE22_SOURCE_LOCK_20260630.csv": payload["gate22_source_locks"],
        "NODI_COMSOL_GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION_MATRIX_20260630.csv": payload["static_fixture_execution"],
        "NODI_COMSOL_GATE23_SIDEWALL_VALIDATOR_CLI_BOUNDARY_MATRIX_20260630.csv": payload["cli_boundary"],
        "NODI_COMSOL_GATE23_SIDEWALL_PACKAGE_C_PROOF_FAIL_CLOSED_LOCK_20260630.csv": payload["package_c_proof_locks"],
        "NODI_COMSOL_GATE23_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE23_SIDEWALL_FUTURE_AUTHORIZATION_BLOCKERS_20260630.csv": payload["future_authorization_blockers"],
        "NODI_COMSOL_GATE23_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate23 Sidewall Static Fixture Execution",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Static fixture execution rows: {payload['summary']['static_fixture_execution_rows']}",
            f"- Static fixture execution blocked: {payload['summary']['static_fixture_execution_blocked']}",
            f"- CLI boundary rows/failures: {payload['summary']['cli_boundary_rows']}/{payload['summary']['cli_boundary_failures']}",
            f"- Package C proof lock failures: {payload['summary']['package_c_proof_lock_failures']}",
            "- Package C proof registry is fail-closed; no Package C physics authorization is present.",
            "- Boundary: no runtime, no solver, no COMSOL launch, no .mph load, no production, no route/yield/detection claims.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate23 disposition: `{DISPOSITION}`",
                f"- Gate22 source drift/missing: {payload['summary']['gate22_source_drift']}/{payload['summary']['gate22_missing_sources']}.",
                f"- Static fixture execution rows/blocked: {payload['summary']['static_fixture_execution_rows']}/{payload['summary']['static_fixture_execution_blocked']}.",
                "- Validator CLI success status is `PASS_CONTEXT_ONLY_NOT_PRODUCTION`, never bare production PASS.",
                "- Package C proof registry remains empty/fail-closed; wall-distance/near-wall physics authorization remains blocked.",
                "- Boundary: no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate23_static_fixture_execution:
        parser.error("--confirm-gate23-static-fixture-execution is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
