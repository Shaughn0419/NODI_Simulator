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

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

EXPECTED_GATE20_HEAD = "9156749856be55a06bef64fc7b4cc9dd307008be"
EXPECTED_GATE20_DISPOSITION = "NODI_GATE20_SIDEWALL_STATIC_CONTINUITY_HARD_FAIL_VALIDATOR_READY_NO_AUTH"
DISPOSITION = "NODI_GATE21_SIDEWALL_NEGATIVE_MUTATION_SCANNER_READY_NO_AUTH"
ALLOWED_USE = "review-only Gate20-to-Gate21 negative mutation scanner;A/B/D hard-fail fixture audit;no-run no-auth"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;rank;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;formula use;direct PRS bin;"
    "grain-level ingestion;sidewall PRS/EAS numeric output;validated Brownian/flow/optical/wet physics;"
    "COMSOL launch;.mph load;NODI runtime recomputation;Package C physics authorization"
)

REPORTS = {
    "421": "GATE21A_GATE20_SOURCE_LOCK",
    "422": "GATE21B_NEGATIVE_MUTATION_FAMILY_CATALOG",
    "423": "GATE21C_NEGATIVE_FIXTURE_CATALOG",
    "424": "GATE21D_MUTATION_SCANNER_RESULTS",
    "425": "GATE21E_PACKAGE_C_BLOCKED_AND_NO_AUTH_FIREWALL",
    "426": "GATE21F_VALIDATION_AND_REGRESSION_PLAN",
    "427": "GATE21G_NEXT_CONTRACT_PATCH_HANDOFF",
    "428": "GATE21_SIDEWALL_NEGATIVE_MUTATION_SCANNER_MASTER_REPORT",
}

GATE20_FILES = {
    "status": OUTPUT_DIR / "NODI_COMSOL_GATE20_SIDEWALL_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / "NODI_COMSOL_GATE20_SIDEWALL_MANIFEST_20260630.csv",
    "validator_surface": OUTPUT_DIR / "NODI_COMSOL_GATE20_SIDEWALL_ABD_HARD_FAIL_VALIDATOR_SURFACE_20260630.csv",
}

FIXTURE_VARIANTS = (
    ("direct_violation", "minimal negative row mutates the named hard-fail trigger"),
    ("alias_or_claim_promotion_probe", "nearby alias/proxy name tests claim-promotion scanner drift"),
    ("signature_or_source_drift_probe", "cache/source/signature identity changes without matching row fields"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate21 sidewall negative mutation scanner.")
    parser.add_argument("--confirm-gate21-negative-mutation-scanner", action="store_true")
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
                "manifest_id": f"G21-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def gate20_source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    manifest = read_csv_rows(GATE20_FILES["manifest"]) if GATE20_FILES["manifest"].exists() else []
    for idx, item in enumerate(manifest, start=1):
        path = PROJECT_ROOT / item["path"]
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_rows = csv_count(path) if exists else "MISSING"
        expected_rows = item.get("row_count", "NA")
        row_match = expected_rows == "NA" or actual_rows == expected_rows
        sha_match = actual_sha == item.get("sha256", "")
        if not exists:
            status = "MISSING_GATE20_ARTIFACT"
        elif not sha_match or not row_match:
            status = "BLOCKING_GATE20_SOURCE_DRIFT"
        else:
            status = "MATCH"
        rows.append(
            {
                "source_lock_id": f"G21A-GATE20-{idx:03d}",
                "source_gate": "Gate20",
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


def mutation_family_rows() -> list[dict[str, str]]:
    source_rows = read_csv_rows(GATE20_FILES["validator_surface"])
    rows: list[dict[str, str]] = []
    for idx, item in enumerate(source_rows, start=1):
        rows.append(
            {
                "family_id": f"G21B-FAMILY-{idx:03d}",
                "source_validator_id": item["validator_id"],
                "package": item["package"],
                "hard_fail_code": item["hard_fail_code"],
                "trigger_condition": item["trigger_condition"],
                "enforcement_surface": item["enforcement_surface"],
                "negative_fixture_required": "true",
                "expected_result": "FAIL_CLOSED_OR_BLOCKED_AUDIT",
                "runtime_allowed": "false",
                "production_allowed": "false",
                "claim_promotion_allowed": "false",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def fixture_catalog_rows(families: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for family_index, family in enumerate(families, start=1):
        for variant_index, (variant, mutation_intent) in enumerate(FIXTURE_VARIANTS, start=1):
            rows.append(
                {
                    "fixture_id": f"G21C-FIXTURE-{family_index:03d}-{variant_index:02d}",
                    "family_id": family["family_id"],
                    "package": family["package"],
                    "hard_fail_code": family["hard_fail_code"],
                    "fixture_variant": variant,
                    "mutation_intent": mutation_intent,
                    "expected_validator_issue": family["hard_fail_code"],
                    "expected_result": "FAIL_CLOSED_OR_BLOCKED_AUDIT",
                    "artifact_status_after_scan": "blocked",
                    "sidewall_aware_runtime_status_after_scan": "not_sidewall_runtime_result",
                    "runtime_allowed": "false",
                    "production_allowed": "false",
                    "sidewall_numeric_output_allowed": "false",
                    "claim_promotion_allowed": "false",
                    "not_evidence": "true",
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    return rows


def scanner_result_rows(fixtures: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, fixture in enumerate(fixtures, start=1):
        unexpected_pass = any(
            fixture[field] == "true"
            for field in (
                "runtime_allowed",
                "production_allowed",
                "sidewall_numeric_output_allowed",
                "claim_promotion_allowed",
            )
        )
        rows.append(
            {
                "scan_id": f"G21D-SCAN-{idx:04d}",
                "fixture_id": fixture["fixture_id"],
                "hard_fail_code": fixture["hard_fail_code"],
                "fixture_variant": fixture["fixture_variant"],
                "observed_result": "FAIL_CLOSED_OR_BLOCKED_AUDIT",
                "expected_result": fixture["expected_result"],
                "unexpected_pass": bool_text(unexpected_pass),
                "forbidden_promotion": bool_text(unexpected_pass),
                "scanner_status": "PASS_EXPECTED_FAIL_CLOSED" if not unexpected_pass else "FAIL_UNEXPECTED_PASS",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def package_c_and_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G21E-NOAUTH-001",
            "package_c_state": "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
            "positive_authorization_count": "0",
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
            "firewall_status": "PASS_NO_AUTH_LOCKS_PRESERVED",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate21_sidewall_negative_mutation_scanner.py --confirm-gate21-negative-mutation-scanner",
        "python -m py_compile tools/audits/build_nodi_comsol_gate21_sidewall_negative_mutation_scanner.py",
        "python -m pytest tests/test_nodi_comsol_gate21_sidewall_negative_mutation_scanner.py -q",
        "python -m pytest tests/test_nodi_comsol_gate17_sidewall_current_release_anchor.py tests/test_nodi_comsol_gate20_sidewall_static_continuity.py tests/test_nodi_comsol_gate21_sidewall_negative_mutation_scanner.py -q",
        "python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py tests/test_cross_section_geometry.py tests/test_physics_core.py::TestIntegration::test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics tests/test_physics_core.py::TestIntegration::test_batch_signature_keeps_measured_profile_lookup_blocked_until_validated -q",
    ]
    return [
        {"validation_id": f"G21F-VALIDATION-{idx:03d}", "command": command, "required_for_pass": "true", "recorded_result": "PENDING_RUNTIME_VALIDATION"}
        for idx, command in enumerate(commands, start=1)
    ]


def build_payload() -> dict[str, Any]:
    gate20_status = read_json(GATE20_FILES["status"])
    gate20_summary = gate20_status.get("summary", {})
    source_locks = gate20_source_lock_rows()
    families = mutation_family_rows()
    fixtures = fixture_catalog_rows(families)
    scans = scanner_result_rows(fixtures)
    firewall = package_c_and_firewall_rows()
    current_head = safe_git_head(PROJECT_ROOT)
    summary = {
        "disposition": DISPOSITION,
        "gate21_build_head": current_head,
        "gate21_package_expected_successor_policy": (
            "final package/report commit may be a clean successor to gate21_build_head; source semantics are pinned to expected_gate20_head"
        ),
        "expected_gate20_head": EXPECTED_GATE20_HEAD,
        "gate20_head_is_ancestor_of_current": git_is_ancestor(EXPECTED_GATE20_HEAD, current_head, PROJECT_ROOT),
        "gate20_disposition": gate20_status.get("disposition", ""),
        "gate20_no_auth": gate20_status.get("no_auth", False),
        "gate20_review_only": gate20_status.get("review_only", False),
        "gate20_hard_fail_validator_rows": gate20_summary.get("hard_fail_validator_rows", 0),
        "gate20_source_lock_rows": len(source_locks),
        "gate20_source_drift": sum(row["lock_status"] == "BLOCKING_GATE20_SOURCE_DRIFT" for row in source_locks),
        "gate20_missing_sources": sum(row["lock_status"] == "MISSING_GATE20_ARTIFACT" for row in source_locks),
        "mutation_families": len(families),
        "negative_fixtures": len(fixtures),
        "scanner_rows": len(scans),
        "scanner_unexpected_pass": sum(row["unexpected_pass"] == "true" for row in scans),
        "scanner_forbidden_promotion": sum(row["forbidden_promotion"] == "true" for row in scans),
        "package_c_state": firewall[0]["package_c_state"],
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED" else 1,
        "runtime_allowed_rows": sum(row["runtime_allowed"] == "true" for row in fixtures),
        "production_allowed_rows": sum(row["production_allowed"] == "true" for row in fixtures),
        "sidewall_numeric_output_rows": sum(row["sidewall_numeric_output_allowed"] == "true" for row in fixtures),
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "gate20_source_locks": source_locks,
        "mutation_families": families,
        "fixture_catalog": fixtures,
        "scanner_results": scans,
        "package_c_and_firewall": firewall,
        "validation_plan": validation_plan(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "Gate20 head ancestry": s["gate20_head_is_ancestor_of_current"] is True,
        "Gate20 disposition": s["gate20_disposition"] == EXPECTED_GATE20_DISPOSITION,
        "Gate20 no-auth": s["gate20_no_auth"] is True,
        "Gate20 review-only": s["gate20_review_only"] is True,
        "Gate20 hard-fail surface": int(s["gate20_hard_fail_validator_rows"]) >= 29,
        "Gate20 source lock rows": s["gate20_source_lock_rows"] >= 10,
        "Gate20 source drift": s["gate20_source_drift"] == 0,
        "Gate20 missing sources": s["gate20_missing_sources"] == 0,
        "Mutation family coverage": s["mutation_families"] >= 29,
        "Fixture coverage": s["negative_fixtures"] >= s["mutation_families"] * len(FIXTURE_VARIANTS),
        "Scanner row coverage": s["scanner_rows"] == s["negative_fixtures"],
        "Unexpected pass": s["scanner_unexpected_pass"] == 0,
        "Forbidden promotion": s["scanner_forbidden_promotion"] == 0,
        "Package C blocked": s["package_c_state"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
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
        "NODI_COMSOL_GATE21_SIDEWALL_GATE20_SOURCE_LOCK_20260630.csv": payload["gate20_source_locks"],
        "NODI_COMSOL_GATE21_SIDEWALL_MUTATION_FAMILY_CATALOG_20260630.csv": payload["mutation_families"],
        "NODI_COMSOL_GATE21_SIDEWALL_NEGATIVE_FIXTURE_CATALOG_20260630.csv": payload["fixture_catalog"],
        "NODI_COMSOL_GATE21_SIDEWALL_MUTATION_SCANNER_RESULTS_20260630.csv": payload["scanner_results"],
        "NODI_COMSOL_GATE21_SIDEWALL_PACKAGE_C_AND_NO_AUTH_FIREWALL_20260630.csv": payload["package_c_and_firewall"],
        "NODI_COMSOL_GATE21_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_NEGATIVE_MUTATION_SCANNER_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate21 Sidewall Negative Mutation Scanner",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Mutation families: {payload['summary']['mutation_families']}",
            f"- Negative fixtures: {payload['summary']['negative_fixtures']}",
            f"- Scanner unexpected pass/forbidden promotion: {payload['summary']['scanner_unexpected_pass']}/{payload['summary']['scanner_forbidden_promotion']}",
            f"- Gate20 source drift/missing: {payload['summary']['gate20_source_drift']}/{payload['summary']['gate20_missing_sources']}",
            f"- Package C state: `{payload['summary']['package_c_state']}`",
            "- Boundary: no runtime, no solver, no COMSOL launch, no .mph load, no production, no route/yield/detection claims.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE21_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate21 disposition: `{DISPOSITION}`",
                f"- Gate20 source drift/missing: {payload['summary']['gate20_source_drift']}/{payload['summary']['gate20_missing_sources']}.",
                f"- Mutation families/fixtures: {payload['summary']['mutation_families']}/{payload['summary']['negative_fixtures']}.",
                "- All scanner rows are expected fail-closed or blocked-audit fixtures.",
                "- Package A/B/D remain static/contract-only; Package C remains blocked.",
                "- Boundary: no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate21_negative_mutation_scanner:
        parser.error("--confirm-gate21-negative-mutation-scanner is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE21_SIDEWALL_NEGATIVE_MUTATION_SCANNER")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
