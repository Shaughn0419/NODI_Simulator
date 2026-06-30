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
    AUTHORIZATION_GATE_PASS_STATUS,
    SIDEWALL_PACKAGE_C_AUTHORIZATION_PHRASE,
    evaluate_sidewall_package_c_future_authorization_request,
    validate_sidewall_package_c_authorization_gate_record,
    write_sidewall_package_c_authorization_gate_record,
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

EXPECTED_GATE23_DISPOSITION = "NODI_GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION_READY_NO_AUTH"
DISPOSITION = "NODI_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_READY_NO_AUTH"
ALLOWED_USE = "review-only sidewall Package C future authorization ledger;no-run no-auth"
BLOCKED_USE = (
    "Package C physics authorization;proof registry update;trajectory boundary physics;"
    "near-wall diffusion;wall-distance PRS numeric output;trapezoid flow;flux-weighted sampling;"
    "electrokinetic grid;optical solver output;sidewall PRS/EAS numeric output;runtime configuration;"
    "production ingestion;NODI runtime recomputation;COMSOL launch;.mph load;q_ch weighting;JRC;"
    "route_score;winner;yield;detection_probability;fabrication release"
)

GATE23_FILES = {
    "status": OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_MANIFEST_20260630.csv",
}

REPORTS = {
    "445": "GATE24A_GATE23_SOURCE_LOCK",
    "446": "GATE24B_PACKAGE_C_AUTHORIZATION_GATE_RECORD",
    "447": "GATE24C_AUTHORIZATION_PHRASE_EVALUATION",
    "448": "GATE24D_PACKAGE_C_NO_AUTH_FIREWALL",
    "449": "GATE24E_VALIDATION_AND_REGRESSION_PLAN",
    "450": "GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate24 sidewall Package C authorization ledger.")
    parser.add_argument("--confirm-gate24-package-c-authorization-ledger", action="store_true")
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
                "manifest_id": f"G24-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def gate23_source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    manifest = read_csv_rows(GATE23_FILES["manifest"]) if GATE23_FILES["manifest"].exists() else []
    for idx, item in enumerate(manifest, start=1):
        path = PROJECT_ROOT / item["path"]
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_rows = csv_count(path) if exists else "MISSING"
        expected_rows = item.get("row_count", "NA")
        row_match = expected_rows == "NA" or actual_rows == expected_rows
        sha_match = actual_sha == item.get("sha256", "")
        if not exists:
            status = "MISSING_GATE23_ARTIFACT"
        elif not sha_match or not row_match:
            status = "BLOCKING_GATE23_SOURCE_DRIFT"
        else:
            status = "MATCH"
        rows.append(
            {
                "source_lock_id": f"G24A-GATE23-{idx:03d}",
                "source_gate": "Gate23",
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


def authorization_gate_record_rows(record: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "gate_record_id": "G24B-PACKAGE-C-AUTH-GATE-001",
            "record_status": str(record.get("status", "")),
            "authorization_gate_decision": str(record.get("authorization_gate_decision", "")),
            "required_future_authorization_phrase": str(record.get("required_future_authorization_phrase", "")),
            "package_c_physics_authorized": bool_text(record.get("package_c_physics_authorized") is True),
            "proof_registry_update_authorized": bool_text(record.get("package_c_proof_registry_update_authorized") is True),
            "runtime_configuration_authorized": bool_text(record.get("runtime_configuration_authorized") is True),
            "nodi_runtime_recompute_authorized": bool_text(record.get("nodi_runtime_recompute_authorized") is True),
            "comsol_launch_authorized": bool_text(record.get("comsol_launch_authorized") is True),
            "mph_load_authorized": bool_text(record.get("mph_load_authorized") is True),
            "sidewall_prs_eas_numeric_output_authorized": bool_text(record.get("sidewall_prs_eas_numeric_output_authorized") is True),
            "claim_boundary": str(record.get("claim_boundary", "")),
            "record_path": str(record.get("record_path", "")),
            "record_sha256": str(record.get("record_sha256", "")),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def phrase_evaluation_rows(record: dict[str, Any]) -> list[dict[str, str]]:
    exact = evaluate_sidewall_package_c_future_authorization_request(
        supplied_phrase=SIDEWALL_PACKAGE_C_AUTHORIZATION_PHRASE,
        gate_record=record,
    )
    generic = evaluate_sidewall_package_c_future_authorization_request(
        supplied_phrase="continue",
        gate_record=record,
    )
    return [
        {
            "phrase_eval_id": "G24C-PHRASE-001",
            "supplied_phrase_case": "exact_required_phrase",
            "phrase_exact_match": bool_text(exact["phrase_exact_match"]),
            "evaluation_status": exact["status"],
            "authorized_now": bool_text(exact["authorized_now"]),
            "package_c_physics_authorized": bool_text(exact["package_c_physics_authorized"]),
            "proof_registry_update_authorized": bool_text(exact["proof_registry_update_authorized"]),
            "nodi_runtime_recompute_authorized": bool_text(exact["nodi_runtime_recompute_authorized"]),
            "comsol_launch_authorized": bool_text(exact["comsol_launch_authorized"]),
            "mph_load_authorized": bool_text(exact["mph_load_authorized"]),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "phrase_eval_id": "G24C-PHRASE-002",
            "supplied_phrase_case": "generic_continue",
            "phrase_exact_match": bool_text(generic["phrase_exact_match"]),
            "evaluation_status": generic["status"],
            "authorized_now": bool_text(generic["authorized_now"]),
            "package_c_physics_authorized": bool_text(generic["package_c_physics_authorized"]),
            "proof_registry_update_authorized": bool_text(generic["proof_registry_update_authorized"]),
            "nodi_runtime_recompute_authorized": bool_text(generic["nodi_runtime_recompute_authorized"]),
            "comsol_launch_authorized": bool_text(generic["comsol_launch_authorized"]),
            "mph_load_authorized": bool_text(generic["mph_load_authorized"]),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
    ]


def no_auth_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G24D-NOAUTH-001",
            "package_c_physics_authorized": "false",
            "proof_registry_update_authorized": "false",
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
        "python tools/audits/build_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py --confirm-gate24-package-c-authorization-ledger",
        "python -m py_compile tools/audits/build_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py tools/audits/write_nodi_sidewall_package_c_authorization_gate.py",
        "python -m pytest tests/test_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py -q",
        "python -m pytest tests/test_nodi_comsol_gate23_sidewall_static_fixture_execution.py tests/test_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py -q",
        "python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k sidewall_package_c_authorization",
    ]
    return [
        {"validation_id": f"G24E-VALIDATION-{idx:03d}", "command": command, "required_for_pass": "true", "recorded_result": "PENDING_RUNTIME_VALIDATION"}
        for idx, command in enumerate(commands, start=1)
    ]


def build_payload() -> dict[str, Any]:
    gate23_status = read_json(GATE23_FILES["status"])
    gate23_summary = gate23_status.get("summary", {})
    current_head = safe_git_head(PROJECT_ROOT)
    source_locks = gate23_source_lock_rows()
    gate_output_dir = OUTPUT_DIR / "gate24_sidewall_package_c_authorization_gate"
    record = write_sidewall_package_c_authorization_gate_record(
        gate23_status_path=GATE23_FILES["status"],
        gate23_manifest_path=GATE23_FILES["manifest"],
        output_dir=gate_output_dir,
    )
    gate_record_rows = authorization_gate_record_rows(record)
    phrase_rows = phrase_evaluation_rows(record)
    firewall = no_auth_firewall_rows()
    summary = {
        "disposition": DISPOSITION,
        "gate24_build_head": current_head,
        "gate23_build_head": gate23_summary.get("gate23_build_head", ""),
        "gate23_head_is_ancestor_of_current": git_is_ancestor(gate23_summary.get("gate23_build_head", ""), current_head, PROJECT_ROOT),
        "gate23_disposition": gate23_status.get("disposition", ""),
        "gate23_no_auth": gate23_status.get("no_auth", False),
        "gate23_review_only": gate23_status.get("review_only", False),
        "gate23_source_lock_rows": len(source_locks),
        "gate23_source_drift": sum(row["lock_status"] == "BLOCKING_GATE23_SOURCE_DRIFT" for row in source_locks),
        "gate23_missing_sources": sum(row["lock_status"] == "MISSING_GATE23_ARTIFACT" for row in source_locks),
        "authorization_gate_status": record["status"],
        "authorization_gate_issues": len(record["issues"]),
        "phrase_eval_rows": len(phrase_rows),
        "phrase_exact_match_rows": sum(row["phrase_exact_match"] == "true" for row in phrase_rows),
        "phrase_authorized_now_rows": sum(row["authorized_now"] == "true" for row in phrase_rows),
        "package_c_physics_authorized_rows": sum(row["package_c_physics_authorized"] == "true" for row in gate_record_rows + phrase_rows),
        "proof_registry_update_authorized_rows": sum(row["proof_registry_update_authorized"] == "true" for row in gate_record_rows + phrase_rows),
        "runtime_allowed_rows": sum(row["runtime_configuration_authorized"] == "true" for row in gate_record_rows),
        "comsol_launch_authorized_rows": sum(row["comsol_launch_authorized"] == "true" for row in gate_record_rows + phrase_rows),
        "mph_load_authorized_rows": sum(row["mph_load_authorized"] == "true" for row in gate_record_rows + phrase_rows),
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED" else 1,
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "gate23_source_locks": source_locks,
        "authorization_gate": gate_record_rows,
        "phrase_evaluations": phrase_rows,
        "no_auth_firewall": firewall,
        "validation_plan": validation_plan(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "Gate23 head ancestry": s["gate23_head_is_ancestor_of_current"] is True,
        "Gate23 disposition": s["gate23_disposition"] == EXPECTED_GATE23_DISPOSITION,
        "Gate23 no-auth": s["gate23_no_auth"] is True,
        "Gate23 review-only": s["gate23_review_only"] is True,
        "Gate23 source lock rows": s["gate23_source_lock_rows"] >= 10,
        "Gate23 source drift": s["gate23_source_drift"] == 0,
        "Gate23 missing sources": s["gate23_missing_sources"] == 0,
        "Authorization gate status": s["authorization_gate_status"] == AUTHORIZATION_GATE_PASS_STATUS,
        "Authorization gate issues": s["authorization_gate_issues"] == 0,
        "Phrase rows": s["phrase_eval_rows"] == 2,
        "Phrase exact match rows": s["phrase_exact_match_rows"] == 1,
        "Phrase authorized rows": s["phrase_authorized_now_rows"] == 0,
        "Package C physics authorized rows": s["package_c_physics_authorized_rows"] == 0,
        "Proof registry update authorized rows": s["proof_registry_update_authorized_rows"] == 0,
        "Runtime allowed rows": s["runtime_allowed_rows"] == 0,
        "COMSOL launch authorized rows": s["comsol_launch_authorized_rows"] == 0,
        "MPH load authorized rows": s["mph_load_authorized_rows"] == 0,
        "No-auth firewall": s["no_auth_firewall_failures"] == 0,
    }
    gate_record = payload["authorization_gate"][0]
    if gate_record["record_path"]:
        gate_payload = read_json(Path(gate_record["record_path"]))
        for issue in validate_sidewall_package_c_authorization_gate_record(gate_payload):
            checks[f"Authorization gate record validation: {issue}"] = False
    else:
        checks["Authorization gate record path"] = False
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE24_SIDEWALL_GATE23_SOURCE_LOCK_20260630.csv": payload["gate23_source_locks"],
        "NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_GATE_RECORD_20260630.csv": payload["authorization_gate"],
        "NODI_COMSOL_GATE24_SIDEWALL_AUTHORIZATION_PHRASE_EVALUATION_20260630.csv": payload["phrase_evaluations"],
        "NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE24_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate24 Sidewall Package C Authorization Ledger",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Authorization gate status: {payload['summary']['authorization_gate_status']}",
            f"- Phrase exact-match rows / authorized-now rows: {payload['summary']['phrase_exact_match_rows']}/{payload['summary']['phrase_authorized_now_rows']}",
            f"- Package C physics authorized rows: {payload['summary']['package_c_physics_authorized_rows']}",
            "- Exact phrase matching is recorded, but still does not authorize runtime, proof-registry update, COMSOL launch, .mph load, or Package C physics.",
            "- Boundary: no runtime, no solver, no COMSOL launch, no .mph load, no production, no route/yield/detection claims.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate24 disposition: `{DISPOSITION}`",
                f"- Gate23 source drift/missing: {payload['summary']['gate23_source_drift']}/{payload['summary']['gate23_missing_sources']}.",
                f"- Authorization gate status/issues: {payload['summary']['authorization_gate_status']}/{payload['summary']['authorization_gate_issues']}.",
                f"- Phrase exact-match rows / authorized-now rows: {payload['summary']['phrase_exact_match_rows']}/{payload['summary']['phrase_authorized_now_rows']}.",
                "- Package C physics remains blocked; exact phrase matching is not execution authorization.",
                "- Boundary: no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate24_package_c_authorization_ledger:
        parser.error("--confirm-gate24-package-c-authorization-ledger is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
