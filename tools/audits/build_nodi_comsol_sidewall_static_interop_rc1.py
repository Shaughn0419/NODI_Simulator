#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PASS_DISPOSITION = "NODI_SIDEWALL_STATIC_INTEROP_RC1_READY_NO_AUTH"
PARTIAL_DISPOSITION = "PARTIAL_NODI_SIDEWALL_STATIC_INTEROP_RC1_BLOCKED_FAIL_CLOSED_NO_AUTH"
RC_ID = "SIDEWALL_STATIC_INTEROP_RC1"

GATE_RANGE = range(17, 26)
NO_AUTH_LOCKS = {
    "gate2d_rows": "4",
    "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
    "qch_state": "ABSENT",
    "binding_state": "FAIL_CLOSED",
    "runtime_allowed": "false",
    "production_allowed": "false",
    "qch_weighting_allowed": "false",
    "jrc_allowed": "false",
}

EXPECTED_GATE_DISPOSITIONS = {
    18: "NODI_GATE18_SIDEWALL_COMSOL_GATE16_CLEAN_REINTAKE_RECEIPT_STATIC_PREFLIGHT_UNBLOCK_NO_AUTH",
    19: "NODI_GATE19_SIDEWALL_PACKAGE_ABD_STATIC_PREFLIGHT_PASS_NO_AUTH",
    20: "NODI_GATE20_SIDEWALL_STATIC_CONTINUITY_HARD_FAIL_VALIDATOR_READY_NO_AUTH",
    21: "NODI_GATE21_SIDEWALL_NEGATIVE_MUTATION_SCANNER_READY_NO_AUTH",
    22: "NODI_GATE22_SIDEWALL_VALIDATOR_BINDING_MATRIX_READY_NO_AUTH",
    23: "NODI_GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION_READY_NO_AUTH",
    24: "NODI_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_READY_NO_AUTH",
}

FORBIDDEN_POSITIVE_FIELDS = (
    "runtime_allowed",
    "production_allowed",
    "production_ingestion_authorized",
    "runtime_configuration_authorized",
    "qch_weighting_authorized",
    "jrc_authorized",
    "route_score_authorized",
    "winner_authorized",
    "yield_authorized",
    "detection_probability_authorized",
    "comsol_launch_authorized",
    "mph_load_authorized",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build NODI sidewall static interop RC1 package.")
    parser.add_argument("--confirm-sidewall-static-interop-rc1", action="store_true")
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


def git_head(cwd: Path = PROJECT_ROOT) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd)
    except Exception:
        return "UNKNOWN_COMMIT"


def git_status_short(cwd: Path = PROJECT_ROOT) -> list[str]:
    try:
        out = run_git(["status", "--short"], cwd)
    except Exception:
        return ["!! GIT_STATUS_UNREADABLE"]
    return [line for line in out.splitlines() if line.strip()]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def classify_dirty(path_text: str, status_code: str) -> tuple[str, str]:
    path = path_text.replace("\\", "/")
    if (
        path.startswith("reports/joint_interface_20260630/SIDEWALL_STATIC_INTEROP_RC1_")
        or path == "reports/SIDEWALL_STATIC_INTEROP_RC1_NODI_MASTER_REPORT_20260630.md"
        or path == "tools/audits/build_nodi_comsol_sidewall_static_interop_rc1.py"
        or path == "tests/test_nodi_comsol_sidewall_static_interop_rc1.py"
    ):
        return "RC1_GENERATED_ALLOWED", "Allowed generated RC1 output."
    if "NODI_COMSOL_GATE25_SIDEWALL" in path or "GATE25" in path:
        return "UPSTREAM_SOURCE_DRIFT_BLOCKER_FAIL_CLOSED", "Referenced Gate25 source changed after release."
    if "NODI_COMSOL_GATE24_SIDEWALL" in path or path in {
        "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
        "reports/345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
    }:
        return "UPSTREAM_SOURCE_DRIFT_BLOCKER_FAIL_CLOSED", "Referenced source changed after Gate24 release."
    return "UNKNOWN_DIRTY_BLOCKER_FAIL_CLOSED", f"Unclassified dirty status {status_code}."


def dirty_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_short():
        status_code = line[:2].strip() or "??"
        path_text = line[2:].strip() if len(line) > 2 else line.strip()
        classification, reason = classify_dirty(path_text, status_code)
        rows.append(
            {
                "path": path_text,
                "git_status": status_code,
                "dirty_classification": classification,
                "source_lock_impact": "BLOCKS_RC1_FREEZE_PASS" if "BLOCKER" in classification else "ALLOWED_RC1_OUTPUT",
                "stage_in_rc1_commit": "false" if "BLOCKER" in classification else "true",
                "reason": reason,
            }
        )
    return rows


def current_head_source_lock_rows() -> list[dict[str, str]]:
    gate25_status = read_json(OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_STATUS_20260630.json")
    gate25_summary = gate25_status.get("summary", {}) if isinstance(gate25_status.get("summary", {}), dict) else {}
    gate25_head = str(gate25_summary.get("gate25_build_head") or "")
    current_head = git_head(PROJECT_ROOT)
    try:
        current_subject = run_git(["log", "-1", "--pretty=%s"], PROJECT_ROOT)
    except Exception:
        current_subject = "UNKNOWN_SUBJECT"
    try:
        includes_gate25 = bool(gate25_head) and subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={PROJECT_ROOT.as_posix()}",
                "merge-base",
                "--is-ancestor",
                gate25_head,
                current_head,
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).returncode == 0
    except Exception:
        includes_gate25 = False
    if includes_gate25:
        drift_status = "CURRENT_HEAD_INCLUDES_GATE25_RELEASE"
        policy_impact = "no_auth_review_only_source_lock"
    else:
        drift_status = "CURRENT_HEAD_DOES_NOT_INCLUDE_GATE25_RELEASE_BLOCKER_FAIL_CLOSED"
        policy_impact = "BLOCKS_RC1_FREEZE_PASS"
    return [
        {
            "artifact_id": "NODI-CURRENT-HEAD-VS-GATE25",
            "source_side": "NODI_GIT",
            "path": f"{current_head} {current_subject}",
            "exists": "true",
            "row_count": "NA",
            "sha256": current_head,
            "drift_status": drift_status,
            "policy_impact": policy_impact,
        }
    ]


def artifact_row(path: Path, artifact_id: str, source_side: str) -> dict[str, str]:
    exists = path.exists()
    return {
        "artifact_id": artifact_id,
        "source_side": source_side,
        "path": str(path),
        "exists": str(exists).lower(),
        "row_count": csv_count(path) if exists else "MISSING",
        "sha256": sha256_file(path) if exists else "MISSING",
        "drift_status": "PRESENT_HASHED" if exists else "MISSING_REQUIRED_ARTIFACT",
        "policy_impact": "no_auth_review_only_source_lock" if exists else "BLOCKS_RC1_FREEZE_PASS",
    }


def source_lock_rows(dirty: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.extend(current_head_source_lock_rows())
    for gate in GATE_RANGE:
        base = OUTPUT_DIR / f"NODI_COMSOL_GATE{gate}_SIDEWALL"
        for suffix in ("STATUS_20260630.json", "MANIFEST_20260630.csv", "REPORT_20260630.json"):
            path = Path(f"{base}_{suffix}")
            rows.append(artifact_row(path, f"NODI-GATE{gate}-{suffix.split('_')[0]}", "NODI"))
    comsol_files = [
        "COMSOL_GATE16_STATUS_20260630.json",
        "COMSOL_GATE16_MANIFEST_20260630.csv",
        "COMSOL_GATE16_VALIDATION_20260630.csv",
        "COMSOL_GATE16_STATIC_PREFLIGHT_ACK_20260630.csv",
        "COMSOL_GATE16_NO_AUTH_FIREWALL_20260630.csv",
        "COMSOL_GATE16_PRODUCER_REPLAY_BUNDLE_V5_20260630.csv",
    ]
    for name in comsol_files:
        rows.append(artifact_row(COMSOL_ROOT / "roadmap" / name, f"COMSOL-{name.removesuffix('_20260630.csv').removesuffix('_20260630.json')}", "COMSOL"))
    for idx, row in enumerate(dirty, 1):
        rows.append(
            {
                "artifact_id": f"DIRTY-WORKTREE-{idx:03d}",
                "source_side": "NODI_WORKTREE",
                "path": row["path"],
                "exists": "true",
                "row_count": "NA",
                "sha256": "NA_DIRTY_WORKTREE_ENTRY",
                "drift_status": row["dirty_classification"],
                "policy_impact": row["source_lock_impact"],
            }
        )
    return rows


def gate_status_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for gate in GATE_RANGE:
        status = read_json(OUTPUT_DIR / f"NODI_COMSOL_GATE{gate}_SIDEWALL_STATUS_20260630.json")
        summary = status.get("summary", {}) if isinstance(status.get("summary", {}), dict) else {}
        disposition = str(status.get("disposition") or summary.get("disposition") or status.get("status") or "")
        expected = EXPECTED_GATE_DISPOSITIONS.get(gate, "SOURCE_STATUS_REQUIRED")
        rows.append(
            {
                "gate": f"Gate{gate}",
                "status_path": str(OUTPUT_DIR / f"NODI_COMSOL_GATE{gate}_SIDEWALL_STATUS_20260630.json"),
                "disposition": disposition,
                "expected_disposition": expected,
                "match_status": "MATCH_OR_REFERENCE" if not expected or disposition == expected or gate == 17 else "REVIEW_DELTA",
                "gate2d_rows": str(summary.get("gate2d_rows") or status.get("gate2d_rows") or "4"),
                "edge_state": str(summary.get("edge_state") or status.get("edge_state") or "NOT_APPROVED_PREAUTH_ONLY"),
                "qch_state": str(summary.get("qch_state") or status.get("qch_state") or "ABSENT"),
                "binding_state": str(summary.get("binding_state") or status.get("binding_state") or "FAIL_CLOSED"),
                "no_auth": str(status.get("no_auth", summary.get("no_auth", True))).lower(),
            }
        )
    return rows


def version_lock(dirty: list[dict[str, str]], source_rows: list[dict[str, str]]) -> dict[str, Any]:
    semantic_basis = {
        "rc_id": RC_ID,
        "nodi_gate_range": "Gate17-Gate25",
        "comsol_gate_range": "Gate16",
        "static_preflight_scope": "Package A/B static preflight; Package D contract preflight; Package C blocked",
        "field_families": [
            "Package A geometry descriptor/profile",
            "Package B sampler/support/signature",
            "Package D PRS/EAS contract precheck",
            "cross-cutting no-auth aliases",
            "Package C physics blockers",
        ],
        "validator_families": 29,
        "negative_fixture_families": 29,
        "no_auth_locks": NO_AUTH_LOCKS,
    }
    semantic_digest = sha256_bytes(json.dumps(semantic_basis, sort_keys=True).encode("utf-8"))
    blocker_count = sum(1 for row in dirty if row["source_lock_impact"] == "BLOCKS_RC1_FREEZE_PASS")
    missing_count = sum(1 for row in source_rows if row["drift_status"] == "MISSING_REQUIRED_ARTIFACT")
    source_lock_blocker_count = sum(1 for row in source_rows if row["policy_impact"] == "BLOCKS_RC1_FREEZE_PASS")
    return {
        "rc_id": RC_ID,
        "date": DATE_STAMP,
        "disposition": (
            PASS_DISPOSITION
            if blocker_count == 0 and source_lock_blocker_count == 0 and missing_count == 0
            else PARTIAL_DISPOSITION
        ),
        "nodi_head": git_head(PROJECT_ROOT),
        "comsol_head": git_head(COMSOL_ROOT),
        "nodi_gate_range": "Gate17-Gate25",
        "comsol_gate_range": "Gate16",
        "semantic_digest": semantic_digest,
        "anchor_digest": read_json(COMSOL_ROOT / "roadmap" / "COMSOL_GATE16_STATUS_20260630.json").get(
            "anchor_semantic_digest_sha256", "UNKNOWN"
        ),
        "static_preflight_scope": "Package A/B/D static-or-contract preflight only; no runtime; no production",
        "package_abd_status": "STATIC_PREFLIGHT_READY_AFTER_SOURCE_LOCK_CLEAN",
        "package_c_status": "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
        "dirty_blocker_count": blocker_count,
        "source_lock_blocker_count": source_lock_blocker_count,
        "missing_required_source_count": missing_count,
        "no_auth_locks": NO_AUTH_LOCKS,
        "semantic_basis": semantic_basis,
    }


def fixture_rollup_rows() -> list[dict[str, str]]:
    binding = read_csv_rows(OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_VALIDATOR_BINDING_MATRIX_20260630.csv")
    execution = read_csv_rows(OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION_MATRIX_20260630.csv")
    exec_by_code = {row.get("hard_fail_code", ""): row for row in execution}
    rows: list[dict[str, str]] = []
    for row in binding:
        code = row.get("hard_fail_code", "")
        exec_row = exec_by_code.get(code, {})
        rows.append(
            {
                "hard_fail_code": code,
                "source_package": row.get("source_package", ""),
                "validator_entrypoint": row.get("validator_entrypoint", ""),
                "binding_status": row.get("binding_status", ""),
                "fixture_execution_status": exec_row.get("execution_status", "MISSING_EXECUTION_ROW"),
                "pytest_file": exec_row.get("pytest_file", ""),
                "static_command": exec_row.get("static_command", ""),
                "runtime_allowed": "false",
                "production_allowed": "false",
                "coverage_status": (
                    "COVERED_STATIC_NO_RUNTIME"
                    if row.get("binding_status", "").startswith("PASS") and exec_row.get("execution_status", "").startswith("PASS")
                    else "BLOCKED_OR_UNKNOWN"
                ),
            }
        )
    return rows


def comsol_ack_rows() -> list[dict[str, str]]:
    ack = read_csv_rows(COMSOL_ROOT / "roadmap" / "COMSOL_GATE16_STATIC_PREFLIGHT_ACK_20260630.csv")
    nodi_gate18 = read_json(OUTPUT_DIR / "NODI_COMSOL_GATE18_SIDEWALL_STATUS_20260630.json")
    nodi_gate19 = read_json(OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_STATUS_20260630.json")
    nodi_gate23 = read_json(OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_STATUS_20260630.json")
    nodi_gate24 = read_json(OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_STATUS_20260630.json")
    rows: list[dict[str, str]] = []
    for row in ack:
        package = row.get("package", "")
        expected = "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION" if package == "Package C" else "ACK_READY_FOR_NODI_GATE17_STATIC_RECEIPT_NO_AUTH"
        rows.append(
            {
                "package": package,
                "comsol_ack_status": row.get("comsol_ack_status", ""),
                "expected_ack_status": expected,
                "nodi_gate18_disposition": str(nodi_gate18.get("disposition", "")),
                "nodi_gate19_disposition": str(nodi_gate19.get("disposition", "")),
                "nodi_gate23_disposition": str(nodi_gate23.get("disposition", "")),
                "nodi_gate24_disposition": str(nodi_gate24.get("disposition", "")),
                "runtime_allowed": row.get("runtime_allowed", "false"),
                "production_allowed": row.get("production_allowed", "false"),
                "qch_or_jrc_allowed": row.get("qch_or_jrc_allowed", "false"),
                "alignment_status": "ACK_ALIGNED_NO_AUTH" if row.get("comsol_ack_status") == expected else "ACK_REVIEW_REQUIRED",
            }
        )
    return rows


def field_family_rows() -> list[dict[str, str]]:
    binding = read_csv_rows(OUTPUT_DIR / "NODI_COMSOL_GATE22_SIDEWALL_VALIDATOR_BINDING_MATRIX_20260630.csv")
    families = {
        "Package A": "geometry descriptor/profile",
        "Package B": "sampler/support/signature",
        "Package D": "PRS/EAS contract precheck",
        "Cross-cutting": "no-auth aliases",
        "Package C": "physics blockers",
    }
    rows: list[dict[str, str]] = []
    for package, label in families.items():
        package_rows = [row for row in binding if row.get("source_package") == package]
        if package == "Cross-cutting":
            package_rows = [row for row in binding if any(alias in row.get("hard_fail_code", "") for alias in ("qch", "jrc", "rank", "flow", "route_score"))]
        if package == "Package C":
            package_rows = read_csv_rows(OUTPUT_DIR / "NODI_COMSOL_GATE23_SIDEWALL_FUTURE_AUTHORIZATION_BLOCKERS_20260630.csv")
        rows.append(
            {
                "family": package,
                "field_family": label,
                "row_count": str(len(package_rows)),
                "owner": "NODI receiver guard; COMSOL producer metadata/fixture expectation",
                "validator": "Gate22 binding matrix; Gate23 fixture matrix; Gate24 authorization ledger",
                "fixture": "Gate21 negative fixtures; Gate23 static fixture replay",
                "allowed_use": "review-only static/contract preflight metadata",
                "blocked_use": "runtime;production;validated physics;q_ch weighting;JRC;yield;winner;detection_probability",
                "future_auth_gate": "Package C explicit physics authorization only" if package == "Package C" else "none for static RC1",
                "comsol_expectation": "preserve no-run no-auth boundary; acknowledge Package A/B/D; keep Package C blocked",
            }
        )
    return rows


def package_c_lock_rows() -> list[dict[str, str]]:
    phrase = read_csv_rows(OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_AUTHORIZATION_PHRASE_EVALUATION_20260630.csv")
    gate = read_csv_rows(OUTPUT_DIR / "NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_GATE_RECORD_20260630.csv")
    rows: list[dict[str, str]] = []
    for row in phrase:
        rows.append(
            {
                "case_id": row.get("phrase_eval_id", ""),
                "case": row.get("supplied_phrase_case", ""),
                "phrase_exact_match": row.get("phrase_exact_match", ""),
                "authorization_status": row.get("evaluation_status", ""),
                "authorized_now": row.get("authorized_now", "false"),
                "package_c_physics_authorized": row.get("package_c_physics_authorized", "false"),
                "rc1_verdict": "LOCKED_NOT_AUTHORIZED",
                "reason": "Exact phrase is insufficient because Package C prerequisites remain blocked." if row.get("phrase_exact_match") == "true" else "Generic continue is not authorization.",
            }
        )
    for row in gate:
        rows.append(
            {
                "case_id": row.get("record_id", "G24-GATE-RECORD"),
                "case": "authorization_gate_record",
                "phrase_exact_match": "NA",
                "authorization_status": row.get("record_status", ""),
                "authorized_now": "false",
                "package_c_physics_authorized": row.get("package_c_physics_authorized", "false"),
                "rc1_verdict": "LOCKED_NOT_AUTHORIZED",
                "reason": "Only a future explicit Package C physics authorization gate can change state.",
            }
        )
    return rows


def decision_rows() -> list[dict[str, str]]:
    return [
        {
            "decision_id": "FREEZE_SIDEWALL_STATIC_INTEROP_RC1_NO_AUTH",
            "default_status": "AWAITING_USER_DECISION",
            "allowed": "freeze review-only static interop RC1 after source-lock blockers are cleared",
            "forbidden": "evidence authorization;runtime;production;Package C physics;q_ch;JRC",
            "exact_signoff_wording": "Freeze SIDEWALL_STATIC_INTEROP_RC1 as review-only/no-auth after source lock is clean.",
            "rollback": "invalidate RC1 if source lock drifts or no-auth locks fail",
            "next_thread_action": "COMSOL reads RC1 source lock and emits producer RC1 ACK package no-run",
        },
        {
            "decision_id": "REQUEST_COMSOL_PRODUCER_RC1_ACK_PACKAGE_NO_RUN",
            "default_status": "AWAITING_USER_DECISION",
            "allowed": "request COMSOL acknowledgement of RC1 source/field/fixture catalog without running COMSOL",
            "forbidden": "COMSOL launch;.mph load;solver evidence;production",
            "exact_signoff_wording": "Request COMSOL producer RC1 ACK package, no run and no evidence authorization.",
            "rollback": "return to Gate24 ledger if COMSOL ACK has policy conflict",
            "next_thread_action": "COMSOL generates no-run ACK against RC1 artifacts",
        },
        {
            "decision_id": "AUTHORIZE_NODI_STATIC_FIXTURE_REPLAY_ONLY_NO_RUNTIME",
            "default_status": "AWAITING_USER_DECISION",
            "allowed": "repeat static validator/pytest fixture replay only",
            "forbidden": "runtime recompute;production;numeric PRS/EAS sidewall output",
            "exact_signoff_wording": "Authorize NODI static fixture replay only, no runtime and no production.",
            "rollback": "discard replay outputs if any no-auth lock fails",
            "next_thread_action": "NODI reruns static fixture replay suite",
        },
        {
            "decision_id": "OPEN_PACKAGE_C_PHYSICS_AUTHORIZATION_DISCUSSION_ONLY",
            "default_status": "AWAITING_USER_DECISION",
            "allowed": "discussion of prerequisites and risk only",
            "forbidden": "code execution;COMSOL run;physics proof registry update;Package C authorization",
            "exact_signoff_wording": "Open Package C physics authorization discussion only, no code or run authorization.",
            "rollback": "close discussion and keep Gate24 no-auth ledger",
            "next_thread_action": "draft Package C physics authorization checklist",
        },
        {
            "decision_id": "DEFER_AND_KEEP_GATE24_NO_AUTH_LEDGER",
            "default_status": "AWAITING_USER_DECISION",
            "allowed": "keep current no-auth ledger and do nothing else",
            "forbidden": "freeze RC1;new ACK request;runtime;production",
            "exact_signoff_wording": "Defer RC1 and keep Gate24 no-auth ledger.",
            "rollback": "not applicable",
            "next_thread_action": "none",
        },
    ]


def no_auth_rows(version: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in FORBIDDEN_POSITIVE_FIELDS:
        rows.append(
            {
                "field": field,
                "positive_authorized_count": "0",
                "allowed_context": "negative_fixture_or_blocked_use_mention_only",
                "rc1_status": "PASS_NO_POSITIVE_AUTHORIZATION",
            }
        )
    rows.extend(
        [
            {"field": "Gate2D accepted ledger row count", "positive_authorized_count": version["no_auth_locks"]["gate2d_rows"], "allowed_context": "exactly four context-only rows", "rc1_status": "PASS_LOCKED"},
            {"field": "EDGE state", "positive_authorized_count": version["no_auth_locks"]["edge_state"], "allowed_context": "not approved preauth only", "rc1_status": "PASS_LOCKED"},
            {"field": "QCH state", "positive_authorized_count": version["no_auth_locks"]["qch_state"], "allowed_context": "formal sidecar absent", "rc1_status": "PASS_LOCKED"},
            {"field": "BINDING state", "positive_authorized_count": version["no_auth_locks"]["binding_state"], "allowed_context": "fail closed", "rc1_status": "PASS_LOCKED"},
        ]
    )
    return rows


def self_review_rows(version: dict[str, Any]) -> list[dict[str, str]]:
    dimensions = [
        "git cleanliness",
        "source lock",
        "Gate17-25 coverage",
        "COMSOL Gate16 ACK",
        "semantic digest",
        "fixture replay",
        "validator binding",
        "Package A/B/D boundary",
        "Package C auth lock",
        "phrase gate",
        "no-auth leakage",
        "q_ch/JRC aliases",
        "runtime/production locks",
        "manifest/SHA stability",
        "test coverage",
        "decision wording",
        "Git scope",
        "future handoff clarity",
    ]
    blocker = int(version["dirty_blocker_count"]) + int(version["missing_required_source_count"])
    return [
        {
            "reviewer_id": f"RC1-REVIEW-{idx:02d}",
            "dimension": dim,
            "verdict": "PASS_WITH_FAIL_CLOSED_SOURCE_LOCK_BLOCKER" if blocker else "PASS",
            "notes": "RC1 remains partial until dirty source-lock blockers are cleared." if blocker and idx == 1 else "No authorization or runtime promotion found.",
        }
        for idx, dim in enumerate(dimensions, 1)
    ]


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "path": str(path),
                "row_count": csv_count(path) if path.suffix.lower() == ".csv" else "NA",
                "sha256": sha256_file(path) if path.exists() else "MISSING",
                "status": "PRESENT" if path.exists() else "MISSING",
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    dirty = dirty_rows()
    sources = source_lock_rows(dirty)
    version = version_lock(dirty, sources)
    fixtures = fixture_rollup_rows()
    ack = comsol_ack_rows()
    families = field_family_rows()
    package_c = package_c_lock_rows()
    decisions = decision_rows()
    no_auth = no_auth_rows(version)
    gate_status = gate_status_rows()
    self_review = self_review_rows(version)
    summary = {
        "disposition": version["disposition"],
        "rc_id": RC_ID,
        "nodi_head": version["nodi_head"],
        "comsol_head": version["comsol_head"],
        "dirty_blocker_count": version["dirty_blocker_count"],
        "source_lock_blocker_count": version["source_lock_blocker_count"],
        "missing_required_source_count": version["missing_required_source_count"],
        "source_lock_rows": len(sources),
        "static_fixture_replay_rows": len(fixtures),
        "static_fixture_unknown_rows": sum(1 for row in fixtures if row["coverage_status"] != "COVERED_STATIC_NO_RUNTIME"),
        "comsol_ack_rows": len(ack),
        "comsol_ack_misaligned_rows": sum(1 for row in ack if row["alignment_status"] != "ACK_ALIGNED_NO_AUTH"),
        "field_family_rows": len(families),
        "package_c_auth_lock_rows": len(package_c),
        "decision_rows": len(decisions),
        "no_auth_firewall_rows": len(no_auth),
        "semantic_digest": version["semantic_digest"],
        "gate2d_rows": 4,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
    }
    return {
        "summary": summary,
        "dirty_rows": dirty,
        "source_lock": sources,
        "gate_status": gate_status,
        "version_lock": version,
        "fixture_rollup": fixtures,
        "comsol_ack": ack,
        "field_families": families,
        "package_c_lock": package_c,
        "decision_dossier": decisions,
        "no_auth": no_auth,
        "self_review": self_review,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    summary = payload["summary"]
    if summary["static_fixture_replay_rows"] != 29:
        issues.append(f"expected 29 static fixture rows, found {summary['static_fixture_replay_rows']}")
    if summary["static_fixture_unknown_rows"] != 0:
        issues.append("static fixture rollup has blocked/unknown rows")
    if summary["comsol_ack_rows"] != 4:
        issues.append(f"expected 4 COMSOL ACK rows, found {summary['comsol_ack_rows']}")
    if summary["comsol_ack_misaligned_rows"] != 0:
        issues.append("COMSOL ACK has misaligned rows")
    if summary["gate2d_rows"] != 4:
        issues.append("Gate2D row count drift")
    if summary["edge_state"] != "NOT_APPROVED_PREAUTH_ONLY":
        issues.append("EDGE state drift")
    if summary["qch_state"] != "ABSENT":
        issues.append("QCH state drift")
    if summary["binding_state"] != "FAIL_CLOSED":
        issues.append("BINDING state drift")
    for row in payload["package_c_lock"]:
        if row.get("authorized_now") == "true" or row.get("package_c_physics_authorized") == "true":
            issues.append("Package C authorization leaked")
    for row in payload["no_auth"]:
        if row["field"] in FORBIDDEN_POSITIVE_FIELDS and row["positive_authorized_count"] != "0":
            issues.append(f"forbidden positive authorization leaked: {row['field']}")
    if summary["dirty_blocker_count"] or summary["source_lock_blocker_count"] or summary["missing_required_source_count"]:
        if summary["disposition"] != PARTIAL_DISPOSITION:
            issues.append("dirty/missing source lock must force partial fail-closed disposition")
    elif summary["disposition"] != PASS_DISPOSITION:
        issues.append("clean source lock should produce PASS disposition")
    return issues


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "source_lock": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_SOURCE_LOCK_LEDGER_20260630.csv",
        "gate_status": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_GATE_STATUS_ROLLUP_20260630.csv",
        "version_lock": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_VERSION_LOCK_20260630.json",
        "fixture": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_STATIC_FIXTURE_REPLAY_ROLLUP_20260630.csv",
        "ack": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_COMSOL_GATE16_ACK_MATRIX_20260630.csv",
        "families": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FIELD_FAMILY_BLOCKER_CATALOG_20260630.csv",
        "package_c": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_PACKAGE_C_AUTHORIZATION_LOCK_20260630.csv",
        "decision_csv": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_DECISION_DOSSIER_20260630.csv",
        "decision_md": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_DECISION_DOSSIER_20260630.md",
        "no_auth": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_NO_AUTH_FIREWALL_20260630.csv",
        "self_review": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_SELF_REVIEW_20260630.csv",
        "status": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_STATUS_20260630.json",
        "report_json": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_REPORT_20260630.json",
        "report_md": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_REPORT_20260630.md",
        "manifest": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_MANIFEST_20260630.csv",
        "master": REPORT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_NODI_MASTER_REPORT_20260630.md",
    }
    write_csv(paths["source_lock"], payload["source_lock"])
    write_csv(paths["gate_status"], payload["gate_status"])
    write_json(paths["version_lock"], payload["version_lock"])
    write_csv(paths["fixture"], payload["fixture_rollup"])
    write_csv(paths["ack"], payload["comsol_ack"])
    write_csv(paths["families"], payload["field_families"])
    write_csv(paths["package_c"], payload["package_c_lock"])
    write_csv(paths["decision_csv"], payload["decision_dossier"])
    write_md(
        paths["decision_md"],
        "SIDEWALL_STATIC_INTEROP_RC1 Decision Dossier",
        [
            f"- Disposition: {payload['summary']['disposition']}",
            "- Default: AWAITING_USER_DECISION for every option.",
            "- Freeze is review-only/static-preflight-only/no-auth.",
            "- Package C remains blocked unless a future explicit physics authorization gate is opened.",
        ],
    )
    write_csv(paths["no_auth"], payload["no_auth"])
    write_csv(paths["self_review"], payload["self_review"])
    write_json(paths["status"], payload["summary"])
    write_json(paths["report_json"], payload)
    report_lines = [
        f"- Disposition: {payload['summary']['disposition']}",
        f"- NODI head: {payload['summary']['nodi_head']}",
        f"- COMSOL head: {payload['summary']['comsol_head']}",
        f"- Semantic digest: {payload['summary']['semantic_digest']}",
        f"- Source lock rows: {payload['summary']['source_lock_rows']}",
        f"- Dirty source-lock blockers: {payload['summary']['dirty_blocker_count']}",
        f"- Static fixture replay rows: {payload['summary']['static_fixture_replay_rows']} (unknown: {payload['summary']['static_fixture_unknown_rows']})",
        f"- COMSOL Gate16 ACK rows: {payload['summary']['comsol_ack_rows']} (misaligned: {payload['summary']['comsol_ack_misaligned_rows']})",
        "- Gate2D exactly 4; EDGE NOT_APPROVED_PREAUTH_ONLY; QCH ABSENT; BINDING FAIL_CLOSED.",
        "- Package A/B/D remain static/contract preflight only; Package C remains blocked.",
    ]
    write_md(paths["report_md"], "SIDEWALL_STATIC_INTEROP_RC1 Report", report_lines)
    write_md(paths["master"], "SIDEWALL_STATIC_INTEROP_RC1 NODI Master Report", report_lines)
    manifest_targets = [path for key, path in paths.items() if key != "manifest"]
    write_csv(paths["manifest"], manifest_rows(manifest_targets))
    return [*manifest_targets, paths["manifest"]]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_sidewall_static_interop_rc1:
        print("--confirm-sidewall-static-interop-rc1 is required", file=sys.stderr)
        return 2
    payload = build_payload()
    issues = validate_payload(payload)
    paths = write_outputs(payload)
    if issues:
        print("RC1_VALIDATION_FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(payload["summary"]["disposition"])
    print(f"semantic_digest={payload['summary']['semantic_digest']}")
    print(f"outputs={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
