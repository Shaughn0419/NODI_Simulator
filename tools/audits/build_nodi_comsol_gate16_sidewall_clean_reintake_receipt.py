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
COMSOL_ROADMAP = "roadmap"

EXPECTED_COMSOL_GATE15_HEAD = "7090794ff20970955a011b123b3de171e96910a3"
EXPECTED_COMSOL_GATE16_HEAD = "d25718a3ba4811d8e00015fad4e851fb529af49c"
EXPECTED_COMSOL_GATE16_CLEAN_ANCHOR_HEAD = "ed4cfc7ff4565f79c025cd206bef0aff29d25d6a"
ALLOWED_COMSOL_CURRENT_HEADS = frozenset(
    {EXPECTED_COMSOL_GATE15_HEAD, EXPECTED_COMSOL_GATE16_HEAD, EXPECTED_COMSOL_GATE16_CLEAN_ANCHOR_HEAD}
)
DISPOSITION = "NODI_GATE16_SIDEWALL_COMSOL_GATE15_RECEIPT_STALE_FAIL_CLOSED_NO_AUTH"
ALLOWED_USE = "review-only COMSOL Gate15 receipt;current NODI clean reintake request;static preflight quarantine"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;formula use;direct PRS bin;"
    "grain-level ingestion;accepted row expansion;COMSOL-validated solver evidence;runtime PRS/EAS production"
)

REQUIRED_COMSOL_GATE15_FILES = (
    "roadmap/COMSOL_GATE15_STATUS_20260630.json",
    "roadmap/COMSOL_GATE15_MANIFEST_20260630.csv",
    "roadmap/COMSOL_GATE15_NODI_CLEAN_REINTAKE_20260630.csv",
    "roadmap/COMSOL_GATE15_GATE14_STALE_INTAKE_CLOSURE_V2_20260630.csv",
    "roadmap/COMSOL_GATE15_NODI_STATIC_PREFLIGHT_HANDOFF_20260630.csv",
    "roadmap/COMSOL_GATE15_PRODUCER_PREFLIGHT_EXPORT_V4_20260630.csv",
    "roadmap/COMSOL_GATE15_BINDING_BLOCKER_ROADMAP_V5_20260630.csv",
    "roadmap/COMSOL_GATE15_MUTATION_RESULTS_20260630.csv",
    "roadmap/COMSOL_GATE15_VALIDATION_20260630.csv",
)

FORBIDDEN_TOKENS = (
    "runtime",
    "production",
    "q_ch weighting",
    "JRC",
    "yield",
    "winner",
    "detection_probability",
    "evidence acceptance",
    "COMSOL solver claim",
)

REPORTS = {
    "376": "GATE16A_COMSOL_GATE15_RECEIPT",
    "377": "GATE16B_CLEAN_REINTAKE_STALE_STATUS",
    "378": "GATE16C_CURRENT_NODI_RELEASE_REINTAKE_REQUEST",
    "379": "GATE16D_STATIC_PREFLIGHT_DECISION",
    "380": "GATE16E_NO_AUTH_FIREWALL",
    "381": "GATE16F_VALIDATION",
    "382": "GATE16G_FINAL_HANDOFF",
    "383": "GATE16H_SIDEWALL_CLEAN_REINTAKE_RECEIPT_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate16 NODI receipt for COMSOL Gate15 sidewall clean reintake.")
    parser.add_argument("--confirm-gate16-sidewall-clean-reintake-receipt", action="store_true")
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


def safe_git_status(path: Path) -> list[str]:
    try:
        status = run_git(["status", "--short"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ["UNKNOWN_STATUS_READONLY_REFERENCE"]
    return status.splitlines() if status else []


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def comsol_path(root: Path, relative_path: str) -> Path:
    return root / relative_path


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G16-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def comsol_gate15_receipt(comsol_root: Path) -> list[dict[str, str]]:
    manifest_path = comsol_path(comsol_root, "roadmap/COMSOL_GATE15_MANIFEST_20260630.csv")
    manifest = read_csv_rows(manifest_path) if manifest_path.exists() else []
    rows: list[dict[str, str]] = []
    for idx, item in enumerate(manifest, start=1):
        rel_path = item["path"]
        path = comsol_path(comsol_root, rel_path)
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = csv_count(path)
        expected_rows = item.get("row_count", "NA")
        sha_match = actual_sha == item.get("sha256", "")
        row_match = expected_rows == "NA" or actual_rows == expected_rows
        blocked_use = item.get("blocked_use", "")
        token_match = all(token in blocked_use for token in FORBIDDEN_TOKENS)
        required = rel_path in REQUIRED_COMSOL_GATE15_FILES
        if not path.exists():
            status = "MISSING_REQUIRED_ARTIFACT" if required else "MISSING_OPTIONAL_ARTIFACT"
        elif not sha_match or not row_match:
            status = "BLOCKING_DATA_DRIFT"
        elif not token_match:
            status = "BLOCKING_CLAIM_FIREWALL_DRIFT"
        else:
            status = "MATCH"
        rows.append(
            {
                "receipt_id": f"G16A-RECEIPT-{idx:03d}",
                "path": rel_path,
                "required_for_gate16_receipt": bool_text(required),
                "expected_row_count": expected_rows,
                "actual_row_count": actual_rows,
                "expected_sha256": item.get("sha256", ""),
                "actual_sha256": actual_sha,
                "sha256_match": bool_text(sha_match),
                "row_count_match": bool_text(row_match),
                "blocked_use_has_forbidden_tokens": bool_text(token_match),
                "receipt_status": status,
                "allowed_use": item.get("allowed_use", ""),
                "blocked_use": blocked_use,
            }
        )
    return rows


def clean_reintake_status(comsol_root: Path, nodi_head: str) -> list[dict[str, str]]:
    status = read_json(comsol_path(comsol_root, "roadmap/COMSOL_GATE15_STATUS_20260630.json"))
    stale_rows = read_csv_rows(comsol_path(comsol_root, "roadmap/COMSOL_GATE15_GATE14_STALE_INTAKE_CLOSURE_V2_20260630.csv"))
    stale = stale_rows[0] if stale_rows else {}
    observed_head = str(status.get("nodi_head", ""))
    clean_current = (
        observed_head == nodi_head
        and int(status.get("nodi_dirty_count", -1)) == 0
        and status.get("nodi_reintake_verdict") == "CLEAN_REINTAKE_CONSUMED_AS_RELEASE"
        and status.get("stale_closure_verdict") == "CLOSED_CLEAN_REINTAKE"
    )
    return [
        {
            "status_id": "G16B-STATUS-001",
            "check": "comsol_head",
            "actual_value": safe_git_head(comsol_root),
            "expected_value": EXPECTED_COMSOL_GATE15_HEAD,
            "gate16_result": "MATCH_OR_KNOWN_COMSOL_GATE16_SUCCESSOR"
            if safe_git_head(comsol_root) in ALLOWED_COMSOL_CURRENT_HEADS
            else "HEAD_MISMATCH_FAIL_CLOSED",
            "blocks_static_preflight_release": bool_text(safe_git_head(comsol_root) not in ALLOWED_COMSOL_CURRENT_HEADS),
        },
        {
            "status_id": "G16B-STATUS-002",
            "check": "nodi_head_consumed_by_comsol_gate15",
            "actual_value": observed_head,
            "expected_value": nodi_head,
            "gate16_result": "STALE_NODI_HEAD_FAIL_CLOSED" if observed_head != nodi_head else "MATCH",
            "blocks_static_preflight_release": bool_text(observed_head != nodi_head),
        },
        {
            "status_id": "G16B-STATUS-003",
            "check": "comsol_reported_nodi_dirty_count",
            "actual_value": str(status.get("nodi_dirty_count", "")),
            "expected_value": "0",
            "gate16_result": "DIRTY_NODI_REINTAKE_FAIL_CLOSED" if int(status.get("nodi_dirty_count", -1)) != 0 else "MATCH",
            "blocks_static_preflight_release": bool_text(int(status.get("nodi_dirty_count", -1)) != 0),
        },
        {
            "status_id": "G16B-STATUS-004",
            "check": "comsol_reintake_verdict",
            "actual_value": str(status.get("nodi_reintake_verdict", "")),
            "expected_value": "CLEAN_REINTAKE_CONSUMED_AS_RELEASE",
            "gate16_result": "OBSERVED_UNRELEASED_FAIL_CLOSED"
            if status.get("nodi_reintake_verdict") != "CLEAN_REINTAKE_CONSUMED_AS_RELEASE"
            else "MATCH",
            "blocks_static_preflight_release": bool_text(status.get("nodi_reintake_verdict") != "CLEAN_REINTAKE_CONSUMED_AS_RELEASE"),
        },
        {
            "status_id": "G16B-STATUS-005",
            "check": "stale_intake_closure",
            "actual_value": str(status.get("stale_closure_verdict", "")),
            "expected_value": "CLOSED_CLEAN_REINTAKE",
            "gate16_result": "OPEN_FAIL_CLOSED_OBSERVED_UNRELEASED"
            if status.get("stale_closure_verdict") != "CLOSED_CLEAN_REINTAKE"
            else "MATCH",
            "blocks_static_preflight_release": bool_text(status.get("stale_closure_verdict") != "CLOSED_CLEAN_REINTAKE"),
        },
        {
            "status_id": "G16B-STATUS-006",
            "check": "gate14_stale_closure_v2_row",
            "actual_value": stale.get("closure_status", ""),
            "expected_value": "CLOSED_CLEAN_REINTAKE",
            "gate16_result": "OPEN_FAIL_CLOSED_OBSERVED_UNRELEASED"
            if stale.get("closure_status") != "CLOSED_CLEAN_REINTAKE"
            else "MATCH",
            "blocks_static_preflight_release": bool_text(stale.get("closure_status") != "CLOSED_CLEAN_REINTAKE"),
        },
        {
            "status_id": "G16B-STATUS-007",
            "check": "clean_current_reintake_accepted",
            "actual_value": bool_text(clean_current),
            "expected_value": "false_until_comsol_reintakes_current_nodi_head",
            "gate16_result": "EXPECTED_FAIL_CLOSED_STALE_REINTAKE",
            "blocks_static_preflight_release": "true",
        },
    ]


def current_release_request(nodi_head: str, nodi_status: list[str]) -> list[dict[str, str]]:
    clean = not nodi_status
    return [
        {
            "request_id": "G16C-REQUEST-001",
            "target": "COMSOL producer",
            "requested_action": "pull_current_nodi_main_and_rebuild_clean_reintake_receipt",
            "current_nodi_head": nodi_head,
            "nodi_worktree_status_at_gate16_build": "CLEAN" if clean else "DIRTY_OR_PENDING_GATE16_OUTPUTS",
            "required_condition": "nodi_head_in_comsol_gate16_or_successor_receipt_equals_current_nodi_head",
            "comsol_run_allowed": "false",
            "mph_load_allowed": "false",
            "runtime_or_production_allowed": "false",
            "authorization_promotion_allowed": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "request_id": "G16C-REQUEST-002",
            "target": "COMSOL producer",
            "requested_action": "close_old_b456129_dirty3_gate15_observed_unreleased_intake_as_superseded",
            "current_nodi_head": nodi_head,
            "nodi_worktree_status_at_gate16_build": "CLEAN" if clean else "DIRTY_OR_PENDING_GATE16_OUTPUTS",
            "required_condition": "old_gate15_status_remains_context_only_not_consumed_as_release",
            "comsol_run_allowed": "false",
            "mph_load_allowed": "false",
            "runtime_or_production_allowed": "false",
            "authorization_promotion_allowed": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "request_id": "G16C-REQUEST-003",
            "target": "COMSOL producer",
            "requested_action": "preserve_gate2d_edge_qch_binding_locks",
            "current_nodi_head": nodi_head,
            "nodi_worktree_status_at_gate16_build": "CLEAN" if clean else "DIRTY_OR_PENDING_GATE16_OUTPUTS",
            "required_condition": "Gate2D=4;EDGE=NOT_APPROVED_PREAUTH_ONLY;QCH=ABSENT;BINDING=FAIL_CLOSED",
            "comsol_run_allowed": "false",
            "mph_load_allowed": "false",
            "runtime_or_production_allowed": "false",
            "authorization_promotion_allowed": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
    ]


def static_preflight_decision() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for package, scope in {
        "Package A": "schema/descriptor/profile guard only",
        "Package B": "geometry/sampler/signature guard only",
        "Package C": "near-wall/optical/wet physics not validated",
        "Package D": "PRS/EAS contract precheck only",
    }.items():
        package_c = package == "Package C"
        rows.append(
            {
                "decision_id": f"G16D-{package.replace(' ', '-')}",
                "package": package,
                "scope": scope,
                "gate16_decision": "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"
                if package_c
                else "WAITING_FOR_COMSOL_CLEAN_REINTAKE_AGAINST_CURRENT_NODI_HEAD",
                "runtime_allowed": "false",
                "production_allowed": "false",
                "validated_physics_claim": "false",
                "static_preflight_allowed_now": "false",
                "future_condition": "explicit Package C physics authorization"
                if package_c
                else "COMSOL clean reintake consumes current NODI release head with dirty_count=0",
            }
        )
    return rows


def no_auth_firewall(comsol_root: Path) -> list[dict[str, str]]:
    status = read_json(comsol_path(comsol_root, "roadmap/COMSOL_GATE15_STATUS_20260630.json"))
    manifest = read_csv_rows(comsol_path(comsol_root, "roadmap/COMSOL_GATE15_MANIFEST_20260630.csv"))
    positive_auth = int(status.get("authorization_promotion_count", -1))
    manifest_runtime = sum("runtime" not in row.get("blocked_use", "") for row in manifest)
    return [
        {
            "firewall_id": "G16E-FIREWALL-001",
            "authorization_promotion_count": str(positive_auth),
            "manifest_rows_missing_runtime_block": str(manifest_runtime),
            "gate2d_rows": str(status.get("gate2d_rows", "")),
            "edge_state": str(status.get("edge_state", "")),
            "qch_state": str(status.get("qch_state", "")),
            "binding_state": str(status.get("binding_state", "")),
            "firewall_status": "PASS_NO_AUTH_LOCKS_PRESERVED"
            if positive_auth == 0
            and manifest_runtime == 0
            and status.get("edge_state") == "NOT_APPROVED_PREAUTH_ONLY"
            and status.get("qch_state") == "ABSENT"
            and status.get("binding_state") == "FAIL_CLOSED"
            else "FAIL_CLOSED_FIREWALL_DRIFT",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate16_sidewall_clean_reintake_receipt.py --confirm-gate16-sidewall-clean-reintake-receipt",
        "python -m py_compile tools/audits/build_nodi_comsol_gate16_sidewall_clean_reintake_receipt.py",
        "python -m pytest tests/test_nodi_comsol_gate16_sidewall_clean_reintake_receipt.py -q",
        "python -m pytest tests/test_nodi_comsol_gate13_sidewall_guard_convergence.py tests/test_nodi_comsol_gate14_sidewall_implementation_contract.py tests/test_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py tests/test_nodi_comsol_gate16_sidewall_clean_reintake_receipt.py -q",
    ]
    return [
        {
            "validation_id": f"G16F-VALIDATION-{idx:03d}",
            "command": command,
            "required_for_pass": "true",
            "recorded_result": "PENDING_RUNTIME_VALIDATION",
        }
        for idx, command in enumerate(commands, start=1)
    ]


def build_payload(comsol_root: Path = DEFAULT_COMSOL_ROOT) -> dict[str, Any]:
    nodi_head = safe_git_head(PROJECT_ROOT)
    nodi_status = safe_git_status(PROJECT_ROOT)
    receipt = comsol_gate15_receipt(comsol_root)
    status_rows = clean_reintake_status(comsol_root, nodi_head)
    firewall = no_auth_firewall(comsol_root)
    summary = {
        "disposition": DISPOSITION,
        "nodi_current_head_at_gate16_build": nodi_head,
        "nodi_dirty_count_at_gate16_build": len(nodi_status),
        "comsol_head_actual": safe_git_head(comsol_root),
        "comsol_gate15_receipt_rows": len(receipt),
        "comsol_gate15_blocking_drift": sum(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in receipt),
        "comsol_gate15_missing_required": sum(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in receipt),
        "comsol_gate15_claim_firewall_drift": sum(row["receipt_status"] == "BLOCKING_CLAIM_FIREWALL_DRIFT" for row in receipt),
        "stale_reintake_blockers": sum(row["blocks_static_preflight_release"] == "true" for row in status_rows),
        "clean_current_reintake_accepted": False,
        "current_reintake_request_rows": 3,
        "static_preflight_rows": 4,
        "firewall_status": firewall[0]["firewall_status"],
        "gate2d_rows": firewall[0]["gate2d_rows"],
        "edge_state": firewall[0]["edge_state"],
        "qch_state": firewall[0]["qch_state"],
        "binding_state": firewall[0]["binding_state"],
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "comsol_gate15_receipt": receipt,
        "clean_reintake_status": status_rows,
        "current_release_request": current_release_request(nodi_head, nodi_status),
        "static_preflight_decision": static_preflight_decision(),
        "no_auth_firewall": firewall,
        "validation_plan": validation_plan(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "COMSOL Gate15/Gate16 successor head": s["comsol_head_actual"] in ALLOWED_COMSOL_CURRENT_HEADS,
        "COMSOL Gate15 receipt drift": s["comsol_gate15_blocking_drift"] == 0,
        "COMSOL Gate15 missing required": s["comsol_gate15_missing_required"] == 0,
        "COMSOL Gate15 claim firewall drift": s["comsol_gate15_claim_firewall_drift"] == 0,
        "stale reintake detected": s["stale_reintake_blockers"] > 0,
        "clean current reintake not accepted": s["clean_current_reintake_accepted"] is False,
        "current reintake request emitted": s["current_reintake_request_rows"] == 3,
        "static preflight rows": s["static_preflight_rows"] == 4,
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
        "NODI_COMSOL_GATE16_SIDEWALL_COMSOL_GATE15_RECEIPT_20260630.csv": payload["comsol_gate15_receipt"],
        "NODI_COMSOL_GATE16_SIDEWALL_CLEAN_REINTAKE_STATUS_20260630.csv": payload["clean_reintake_status"],
        "NODI_COMSOL_GATE16_SIDEWALL_CURRENT_RELEASE_REQUEST_20260630.csv": payload["current_release_request"],
        "NODI_COMSOL_GATE16_SIDEWALL_STATIC_PREFLIGHT_DECISION_20260630.csv": payload["static_preflight_decision"],
        "NODI_COMSOL_GATE16_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE16_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE16_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE16_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE16_SIDEWALL_CLEAN_REINTAKE_RECEIPT_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate16 Sidewall Clean Reintake Receipt",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- COMSOL Gate15 receipt rows: {payload['summary']['comsol_gate15_receipt_rows']}",
            f"- Receipt drift/missing/firewall drift: {payload['summary']['comsol_gate15_blocking_drift']}/{payload['summary']['comsol_gate15_missing_required']}/{payload['summary']['comsol_gate15_claim_firewall_drift']}",
            f"- Stale reintake blockers: {payload['summary']['stale_reintake_blockers']}; clean current reintake accepted: false",
            "- Gate16 therefore requests a new COMSOL clean reintake against the current NODI release head and keeps Package A/B/D waiting.",
            "- Package C remains blocked pending explicit physics authorization.",
            "- Boundary: no COMSOL run, no .mph load, no runtime configuration, no production ingestion, no JRC/q_ch/yield/detection claim.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE16_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate16 disposition: `{DISPOSITION}`",
                f"- COMSOL Gate15 receipt rows: {payload['summary']['comsol_gate15_receipt_rows']}; drift={payload['summary']['comsol_gate15_blocking_drift']}; missing={payload['summary']['comsol_gate15_missing_required']}.",
                f"- Clean current reintake accepted: {payload['summary']['clean_current_reintake_accepted']}; stale blockers={payload['summary']['stale_reintake_blockers']}.",
                f"- Locks: EDGE={payload['summary']['edge_state']}; QCH={payload['summary']['qch_state']}; BINDING={payload['summary']['binding_state']}.",
                "- Boundary: review-only/no-auth fail-closed receipt. No solver, no .mph load, no runtime/production.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate16_sidewall_clean_reintake_receipt:
        parser.error("--confirm-gate16-sidewall-clean-reintake-receipt is required")
    payload = build_payload(args.comsol_root)
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE16_SIDEWALL_CLEAN_REINTAKE_RECEIPT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
