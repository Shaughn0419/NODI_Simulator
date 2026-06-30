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


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"

EXPECTED_COMSOL_GATE16_HEAD = "ed4cfc7ff4565f79c025cd206bef0aff29d25d6a"
EXPECTED_COMSOL_GATE16_STATUS = "COMSOL_GATE16_CURRENT_NODI_CLEAN_REINTAKE_CONSUMED_CONTEXT_ONLY_NO_AUTH"
EXPECTED_ANCHOR_DIGEST = "4255d9533a8d150d6a740d03ead267323e868b5560b7051ce5d5ccc0ed3c2c16"
DISPOSITION = "NODI_GATE18_SIDEWALL_COMSOL_GATE16_CLEAN_REINTAKE_RECEIPT_STATIC_PREFLIGHT_UNBLOCK_NO_AUTH"
ALLOWED_USE = "review-only COMSOL Gate16 receipt;Package A/B/D static preflight precheck;no-run no-auth"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;rank;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;formula use;direct PRS bin;"
    "grain-level ingestion;sidewall PRS/EAS numeric output;validated Brownian/flow/optical/wet physics"
)

REPORTS = {
    "397": "GATE18A_COMSOL_GATE16_CLEAN_REINTAKE_RECEIPT",
    "398": "GATE18B_STATIC_PREFLIGHT_UNBLOCK_BOARD",
    "399": "GATE18C_PACKAGE_C_PHYSICS_AUTHORIZATION_BLOCK",
    "400": "GATE18D_NO_AUTH_FIREWALL",
    "401": "GATE18E_VALIDATION_AND_TESTS",
    "402": "GATE18F_COMSOL_GATE16_TO_NODI_STATIC_PREFLIGHT_HANDOFF",
    "403": "GATE18G_FINAL_HANDOFF",
    "404": "GATE18_SIDEWALL_STATIC_PREFLIGHT_UNBLOCK_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate18 receipt for COMSOL Gate16 sidewall clean reintake.")
    parser.add_argument("--confirm-gate18-comsol-gate16-receipt", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
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


def safe_git_head(path: Path) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def comsol_path(root: Path, relative_path: str) -> Path:
    return root / relative_path


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G18-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def comsol_gate16_receipt(comsol_root: Path) -> list[dict[str, str]]:
    manifest = read_csv_rows(comsol_path(comsol_root, "roadmap/COMSOL_GATE16_MANIFEST_20260630.csv"))
    rows: list[dict[str, str]] = []
    for idx, item in enumerate(manifest, start=1):
        rel_path = item["path"]
        path = comsol_path(comsol_root, rel_path)
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = csv_count(path)
        expected_rows = item.get("row_count", "NA")
        sha_match = actual_sha == item.get("sha256", "")
        row_match = expected_rows == "NA" or actual_rows == expected_rows
        blocked = item.get("blocked_use", "")
        firewall = all(token in blocked for token in ["runtime", "production", "JRC", "q_ch weighting", "yield", "winner", "detection_probability"])
        if not path.exists():
            receipt_status = "MISSING_REQUIRED_ARTIFACT"
        elif not sha_match or not row_match:
            receipt_status = "BLOCKING_DATA_DRIFT"
        elif not firewall:
            receipt_status = "BLOCKING_CLAIM_FIREWALL_DRIFT"
        else:
            receipt_status = "MATCH"
        rows.append(
            {
                "receipt_id": f"G18A-RECEIPT-{idx:03d}",
                "path": rel_path,
                "expected_row_count": expected_rows,
                "actual_row_count": actual_rows,
                "expected_sha256": item.get("sha256", ""),
                "actual_sha256": actual_sha,
                "sha256_match": bool_text(sha_match),
                "row_count_match": bool_text(row_match),
                "claim_firewall_match": bool_text(firewall),
                "receipt_status": receipt_status,
                "allowed_use": item.get("allowed_use", ""),
                "blocked_use": blocked,
            }
        )
    return rows


def clean_reintake_acceptance(comsol_root: Path) -> list[dict[str, str]]:
    status = read_json(comsol_path(comsol_root, "roadmap/COMSOL_GATE16_STATUS_20260630.json"))
    validation = read_csv_rows(comsol_path(comsol_root, "roadmap/COMSOL_GATE16_VALIDATION_20260630.csv"))
    closure = read_csv_rows(comsol_path(comsol_root, "roadmap/COMSOL_GATE16_GATE15_STALE_INTAKE_CLOSURE_20260630.csv"))
    return [
        {
            "acceptance_id": "G18B-ACCEPT-001",
            "field": "comsol_head_actual",
            "actual_value": safe_git_head(comsol_root),
            "expected_value": EXPECTED_COMSOL_GATE16_HEAD,
            "acceptance_status": "MATCH" if safe_git_head(comsol_root) == EXPECTED_COMSOL_GATE16_HEAD else "HEAD_MISMATCH_FAIL_CLOSED",
        },
        {
            "acceptance_id": "G18B-ACCEPT-002",
            "field": "comsol_gate16_status",
            "actual_value": str(status.get("status", "")),
            "expected_value": EXPECTED_COMSOL_GATE16_STATUS,
            "acceptance_status": "MATCH" if status.get("status") == EXPECTED_COMSOL_GATE16_STATUS else "STATUS_MISMATCH_FAIL_CLOSED",
        },
        {
            "acceptance_id": "G18B-ACCEPT-003",
            "field": "anchor_semantic_digest_sha256",
            "actual_value": str(status.get("anchor_semantic_digest_sha256", "")),
            "expected_value": EXPECTED_ANCHOR_DIGEST,
            "acceptance_status": "MATCH" if status.get("anchor_semantic_digest_sha256") == EXPECTED_ANCHOR_DIGEST else "DIGEST_MISMATCH_FAIL_CLOSED",
        },
        {
            "acceptance_id": "G18B-ACCEPT-004",
            "field": "clean_current_nodi_consumed",
            "actual_value": str(status.get("clean_current_nodi_consumed", "")),
            "expected_value": "True",
            "acceptance_status": "MATCH" if status.get("clean_current_nodi_consumed") is True else "NOT_CONSUMED_FAIL_CLOSED",
        },
        {
            "acceptance_id": "G18B-ACCEPT-005",
            "field": "stale_gate15_closure_status",
            "actual_value": str(status.get("stale_gate15_closure_status", "")),
            "expected_value": "CLOSED_SUPERSEDED_BY_GATE16_CURRENT_NODI_CLEAN_REINTAKE",
            "acceptance_status": "MATCH"
            if status.get("stale_gate15_closure_status") == "CLOSED_SUPERSEDED_BY_GATE16_CURRENT_NODI_CLEAN_REINTAKE"
            else "STALE_CLOSURE_OPEN_FAIL_CLOSED",
        },
        {
            "acceptance_id": "G18B-ACCEPT-006",
            "field": "comsol_gate16_validation",
            "actual_value": ";".join(sorted({row["status"] for row in validation})),
            "expected_value": "PASS",
            "acceptance_status": "MATCH" if {row["status"] for row in validation} == {"PASS"} else "VALIDATION_NOT_ALL_PASS_FAIL_CLOSED",
        },
        {
            "acceptance_id": "G18B-ACCEPT-007",
            "field": "gate15_closure_row",
            "actual_value": closure[0]["closure_status"] if closure else "MISSING",
            "expected_value": "CLOSED_SUPERSEDED_BY_GATE16_CURRENT_NODI_CLEAN_REINTAKE",
            "acceptance_status": "MATCH"
            if closure and closure[0]["closure_status"] == "CLOSED_SUPERSEDED_BY_GATE16_CURRENT_NODI_CLEAN_REINTAKE"
            else "CLOSURE_ROW_MISMATCH_FAIL_CLOSED",
        },
    ]


def static_preflight_board(comsol_root: Path) -> list[dict[str, str]]:
    ack = read_csv_rows(comsol_path(comsol_root, "roadmap/COMSOL_GATE16_STATIC_PREFLIGHT_ACK_20260630.csv"))
    rows: list[dict[str, str]] = []
    for idx, item in enumerate(ack, start=1):
        package = item["package"]
        package_c = package == "Package C"
        rows.append(
            {
                "board_id": f"G18C-BOARD-{idx:03d}",
                "package": package,
                "comsol_ack_status": item["comsol_ack_status"],
                "nodi_gate18_status": "STATIC_PREFLIGHT_PRECHECK_ALLOWED_NO_AUTH" if not package_c else "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
                "runtime_allowed": "false",
                "production_allowed": "false",
                "validated_physics_claim": "false",
                "qch_or_jrc_allowed": "false",
                "next_allowed_action": "NODI static/schema/contract preflight only" if not package_c else "explicit Package C physics authorization required",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def no_auth_firewall(comsol_root: Path) -> list[dict[str, str]]:
    firewall = read_csv_rows(comsol_path(comsol_root, "roadmap/COMSOL_GATE16_NO_AUTH_FIREWALL_20260630.csv"))[0]
    return [
        {
            "firewall_id": "G18D-FIREWALL-001",
            "source_firewall_status": firewall["firewall_status"],
            "positive_authorization_count": firewall["positive_authorization_count"],
            "runtime_configuration_authorized": firewall["runtime_configuration_authorized"],
            "production_ingestion_authorized": firewall["production_ingestion_authorized"],
            "qch_weighting_authorized": firewall["qch_weighting_authorized"],
            "jrc_authorized": firewall["jrc_authorized"],
            "gate2d_rows": firewall["gate2d_rows"],
            "edge_state": firewall["edge_state"],
            "qch_state": firewall["qch_state"],
            "binding_state": firewall["binding_state"],
            "firewall_status": "PASS_NO_AUTH_LOCKS_PRESERVED"
            if firewall["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED"
            and firewall["positive_authorization_count"] == "0"
            and firewall["runtime_configuration_authorized"] == "false"
            and firewall["production_ingestion_authorized"] == "false"
            else "FAIL_CLOSED_FIREWALL_DRIFT",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate18_sidewall_comsol_gate16_receipt.py --confirm-gate18-comsol-gate16-receipt",
        "python -m py_compile tools/audits/build_nodi_comsol_gate18_sidewall_comsol_gate16_receipt.py",
        "python -m pytest tests/test_nodi_comsol_gate18_sidewall_comsol_gate16_receipt.py -q",
    ]
    return [
        {"validation_id": f"G18E-VALIDATION-{idx:03d}", "command": command, "required_for_pass": "true", "recorded_result": "PENDING_RUNTIME_VALIDATION"}
        for idx, command in enumerate(commands, start=1)
    ]


def build_payload(comsol_root: Path = DEFAULT_COMSOL_ROOT) -> dict[str, Any]:
    receipt = comsol_gate16_receipt(comsol_root)
    acceptance = clean_reintake_acceptance(comsol_root)
    board = static_preflight_board(comsol_root)
    firewall = no_auth_firewall(comsol_root)
    summary = {
        "disposition": DISPOSITION,
        "comsol_head_actual": safe_git_head(comsol_root),
        "comsol_gate16_receipt_rows": len(receipt),
        "comsol_gate16_blocking_drift": sum(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in receipt),
        "comsol_gate16_missing_required": sum(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in receipt),
        "comsol_gate16_claim_firewall_drift": sum(row["receipt_status"] == "BLOCKING_CLAIM_FIREWALL_DRIFT" for row in receipt),
        "clean_reintake_acceptance_failures": sum(row["acceptance_status"] != "MATCH" for row in acceptance),
        "package_abd_static_preflight_allowed": sum(
            row["package"] in {"Package A", "Package B", "Package D"} and row["nodi_gate18_status"] == "STATIC_PREFLIGHT_PRECHECK_ALLOWED_NO_AUTH"
            for row in board
        ),
        "package_c_state": next(row["nodi_gate18_status"] for row in board if row["package"] == "Package C"),
        "firewall_status": firewall[0]["firewall_status"],
        "edge_state": firewall[0]["edge_state"],
        "qch_state": firewall[0]["qch_state"],
        "binding_state": firewall[0]["binding_state"],
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "comsol_gate16_receipt": receipt,
        "clean_reintake_acceptance": acceptance,
        "static_preflight_board": board,
        "no_auth_firewall": firewall,
        "validation_plan": validation_plan(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "COMSOL Gate16 head": s["comsol_head_actual"] == EXPECTED_COMSOL_GATE16_HEAD,
        "COMSOL Gate16 receipt drift": s["comsol_gate16_blocking_drift"] == 0,
        "COMSOL Gate16 missing required": s["comsol_gate16_missing_required"] == 0,
        "COMSOL Gate16 claim firewall drift": s["comsol_gate16_claim_firewall_drift"] == 0,
        "clean reintake acceptance": s["clean_reintake_acceptance_failures"] == 0,
        "Package A/B/D static preflight": s["package_abd_static_preflight_allowed"] == 3,
        "Package C blocked": s["package_c_state"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
        "no auth firewall": s["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED",
        "EDGE lock": s["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY",
        "QCH lock": s["qch_state"] == "ABSENT",
        "BINDING lock": s["binding_state"] == "FAIL_CLOSED",
    }
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE18_SIDEWALL_COMSOL_GATE16_RECEIPT_20260630.csv": payload["comsol_gate16_receipt"],
        "NODI_COMSOL_GATE18_SIDEWALL_CLEAN_REINTAKE_ACCEPTANCE_20260630.csv": payload["clean_reintake_acceptance"],
        "NODI_COMSOL_GATE18_SIDEWALL_STATIC_PREFLIGHT_BOARD_20260630.csv": payload["static_preflight_board"],
        "NODI_COMSOL_GATE18_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE18_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE18_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE18_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE18_SIDEWALL_STATIC_PREFLIGHT_UNBLOCK_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate18 Sidewall Static Preflight Unblock",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- COMSOL Gate16 receipt rows: {payload['summary']['comsol_gate16_receipt_rows']}",
            f"- Package A/B/D static preflight precheck allowed: {payload['summary']['package_abd_static_preflight_allowed']}",
            f"- Package C state: `{payload['summary']['package_c_state']}`",
            "- Boundary: no runtime, no production, no JRC/q_ch/yield/detection claim.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE18_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate18 disposition: `{DISPOSITION}`",
                f"- COMSOL Gate16 head: `{payload['summary']['comsol_head_actual']}`.",
                f"- Receipt drift/missing/firewall drift: {payload['summary']['comsol_gate16_blocking_drift']}/{payload['summary']['comsol_gate16_missing_required']}/{payload['summary']['comsol_gate16_claim_firewall_drift']}.",
                "- Package A/B/D may proceed to NODI static/schema/contract preflight only.",
                "- Package C remains blocked pending explicit physics authorization.",
                "- Boundary: review-only/no-auth. No solver, no runtime/production.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate18_comsol_gate16_receipt:
        parser.error("--confirm-gate18-comsol-gate16-receipt is required")
    payload = build_payload(args.comsol_root)
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE18_SIDEWALL_COMSOL_GATE16_RECEIPT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
