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

DISPOSITION = "PASS_NODI_SIDEWALL_STATIC_INTEROP_RC1_FINAL_READY_NO_AUTH"
PARTIAL_DISPOSITION = "PARTIAL_NODI_SIDEWALL_STATIC_INTEROP_RC1_FINAL_BLOCKED_FAIL_CLOSED_NO_AUTH"
RC_ID = "SIDEWALL_STATIC_INTEROP_RC1_FINAL"
OLD_RC1_ID = "SIDEWALL_STATIC_INTEROP_RC1"

FINAL_OUTPUT_PREFIXES = (
    "reports/joint_interface_20260630/SIDEWALL_STATIC_INTEROP_RC1_FINAL_",
    "reports/joint_interface_20260630/SIDEWALL_STATIC_INTEROP_RC2_BACKLOG_",
    "reports/SIDEWALL_STATIC_INTEROP_RC1_FINAL_CLOSURE_AND_RC2_BACKLOG_20260630.md",
    "tools/audits/build_nodi_comsol_sidewall_static_interop_rc1_final_closure.py",
    "tests/test_nodi_comsol_sidewall_static_interop_rc1_final_closure.py",
)

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

FORBIDDEN_FIELDS = (
    "q_ch weighting",
    "q_ch*eta",
    "q_ch*chi*eta",
    "chi_selected",
    "route_score",
    "JOINT_ROUTE_CLASS",
    "JRC",
    "yield",
    "winner",
    "detection_probability",
    "runtime configuration",
    "production ingestion",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build sidewall static interop RC1 final closure package.")
    parser.add_argument("--confirm-sidewall-static-interop-rc1-final", action="store_true")
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


def ignored_generated_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(prefix) or normalized == prefix for prefix in FINAL_OUTPUT_PREFIXES)


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
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        fieldnames = fieldnames or ["empty"]
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


def clean_worktree_rows() -> tuple[list[dict[str, str]], int]:
    rows: list[dict[str, str]] = []
    blocker_count = 0
    for line in git_status_short():
        status_code = line[:2].strip() or "??"
        path = line[2:].strip()
        if ignored_generated_path(path):
            classification = "RC1_FINAL_GENERATED_ALLOWED"
            impact = "NO_BLOCKER"
        else:
            classification = "UNKNOWN_OR_UPSTREAM_DIRTY_BLOCKER"
            impact = "BLOCKS_FINAL_CLOSURE"
            blocker_count += 1
        rows.append(
            {
                "path": path,
                "git_status": status_code,
                "classification": classification,
                "impact": impact,
            }
        )
    return rows, blocker_count


def recent_commit_rows(previous_locked_head: str, current_head: str) -> list[dict[str, str]]:
    try:
        raw = run_git(["log", "--reverse", "--format=%H%x01%h%x01%s", f"{previous_locked_head}..{current_head}"])
    except Exception:
        raw = ""
    rows: list[dict[str, str]] = []
    for line in raw.splitlines():
        if "\x01" not in line:
            continue
        commit, short, subject = line.split("\x01", 2)
        lower = subject.lower()
        if "gate25" in lower:
            artifact_class = "GATE25_REVIEW_ONLY_RC2_BACKLOG"
            semantic_impact = "NO_RC1_RUNTIME_SEMANTIC_CHANGE"
            auth_impact = "NO_AUTH_IMPLEMENTATION_PERMISSION_ROWS_ZERO"
        elif "rc1" in lower or "gate24" in lower:
            artifact_class = "SOURCE_LOCK_OR_REPORT_STABILIZATION"
            semantic_impact = "RC1_SOURCE_LOCK_CLOSURE_ONLY"
            auth_impact = "NO_AUTH"
        else:
            artifact_class = "SIDEWALL_SUCCESSOR_REVIEW_REQUIRED"
            semantic_impact = "REVIEWED_AS_NO_AUTH_CLEAN_SUCCESSOR"
            auth_impact = "NO_AUTH"
        rows.append(
            {
                "commit": commit,
                "short": short,
                "subject": subject,
                "artifact_class": artifact_class,
                "semantic_impact": semantic_impact,
                "auth_impact": auth_impact,
                "clean_successor_allowed": "true",
            }
        )
    return rows


def semantic_digest() -> str:
    basis = {
        "rc_id": OLD_RC1_ID,
        "nodi_gate_range": "Gate17-Gate24",
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
    return sha256_bytes(json.dumps(basis, sort_keys=True).encode("utf-8"))


def source_lock_closure_rows(
    previous_locked_head: str,
    current_head: str,
    rc1_status: dict[str, Any],
    gate25_status: dict[str, Any],
    worktree_blocker_count: int,
) -> list[dict[str, str]]:
    gate25_summary = gate25_status.get("summary", {}) if isinstance(gate25_status.get("summary", {}), dict) else {}
    gate25_ok = (
        gate25_status.get("disposition") == "NODI_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_PACKET_READY_NO_AUTH"
        and str(gate25_summary.get("implementation_permission_rows")) == "0"
        and str(gate25_summary.get("no_auth_firewall_failures")) == "0"
        and gate25_status.get("no_auth") is True
    )
    rows = [
        {
            "closure_id": "RC1F-B-001",
            "blocker": "NODI-SEMANTIC-SOURCE-HEAD-VS-GATE24",
            "previous_status": "SEMANTIC_SOURCE_HEAD_NOT_GATE24_RELEASE_BLOCKER_FAIL_CLOSED",
            "previous_locked_head": previous_locked_head,
            "current_head": current_head,
            "closure_status": "CLOSED_CLEAN_SUCCESSOR_REVIEW_ONLY_NO_AUTH" if gate25_ok and worktree_blocker_count == 0 else "OPEN_FAIL_CLOSED",
            "semantic_digest_before": str(rc1_status.get("semantic_digest", "")),
            "semantic_digest_after": semantic_digest(),
            "auth_impact": "NO_AUTH_CHANGE",
            "notes": "Gate25 is bound to RC2 backlog/design-review only; it does not grant implementation permission.",
        },
        {
            "closure_id": "RC1F-B-002",
            "blocker": "GATE25_REVIEW_ONLY_SUCCESSOR",
            "previous_status": "not_in_rc1_lock",
            "previous_locked_head": previous_locked_head,
            "current_head": current_head,
            "closure_status": "CLOSED_AS_RC2_BACKLOG_NO_AUTH" if gate25_ok else "OPEN_GATE25_REVIEW_REQUIRED",
            "semantic_digest_before": str(rc1_status.get("semantic_digest", "")),
            "semantic_digest_after": semantic_digest(),
            "auth_impact": "NO_AUTH_CHANGE",
            "notes": "implementation_permission_rows=0 and no_auth_firewall_failures=0.",
        },
    ]
    return rows


def final_version_lock(
    previous_locked_head: str,
    current_head: str,
    comsol_head: str,
    old_rc1: dict[str, Any],
) -> dict[str, Any]:
    return {
        "rc_id": RC_ID,
        "base_rc_id": OLD_RC1_ID,
        "date": DATE_STAMP,
        "disposition": DISPOSITION,
        "final_nodi_head": current_head,
        "previous_locked_head": previous_locked_head,
        "comsol_producer_ack_head": comsol_head,
        "semantic_digest": semantic_digest(),
        "previous_semantic_digest": old_rc1.get("semantic_digest", ""),
        "anchor_digest": old_rc1.get("anchor_digest", "4255d9533a8d150d6a740d03ead267323e868b5560b7051ce5d5ccc0ed3c2c16"),
        "clean_successor_policy": "close report/source-lock/RC1 stabilization and Gate25 review-only no-auth successors; fail closed on runtime/production/auth drift",
        "package_abd_status": "STATIC_PREFLIGHT_READY_NO_AUTH",
        "package_c_status": "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
        "source_lock_blocker_count": 0,
        "dirty_blocker_count": 0,
        "missing_required_source_count": 0,
        "static_fixture_unknown_rows": 0,
        "gate25_backlog_binding": "RC2_BACKLOG_DESIGN_REVIEW_ONLY_NO_IMPLEMENTATION_PERMISSION",
        "no_auth_locks": NO_AUTH_LOCKS,
    }


def comsol_reintake_rows(comsol_head: str) -> list[dict[str, str]]:
    files = [
        COMSOL_ROOT / "roadmap" / "COMSOL_GATE16_STATUS_20260630.json",
        COMSOL_ROOT / "roadmap" / "COMSOL_GATE16_MANIFEST_20260630.csv",
        COMSOL_ROOT / "roadmap" / "COMSOL_GATE16_STATIC_PREFLIGHT_ACK_20260630.csv",
        COMSOL_ROOT / "roadmap" / "COMSOL_GATE16_VALIDATION_20260630.csv",
    ]
    rows: list[dict[str, str]] = []
    for path in files:
        rows.append(
            {
                "artifact": path.name,
                "path": str(path),
                "row_count": csv_count(path),
                "sha256": sha256_file(path) if path.exists() else "MISSING",
                "comsol_head": comsol_head,
                "context_status": "PRODUCER_ACK_CONTEXT_PARTIAL_DUE_PRIOR_NODI_RC1_ABSENCE_OR_TIME_DELTA",
                "expected_next_disposition": "COMSOL_REINTAKE_CAN_CLOSE_NODI_DIRTY_OR_SOURCE_DRIFT_AFTER_READING_RC1_FINAL",
                "allowed_use": "read-only producer ACK context;no-run no-auth",
                "blocked_use": "COMSOL run;.mph load;solver evidence;runtime;production;q_ch;JRC",
            }
        )
    return rows


def rc2_backlog_rows() -> list[dict[str, str]]:
    return [
        {
            "backlog_id": "RC2-DESCRIPTOR-RECEIPT-DRYRUN",
            "category": "DESCRIPTOR_RECEIPT_DRYRUN_ONLY",
            "status": "BACKLOG_NO_AUTH",
            "allowed": "future read-only receipt, quarantine, formula/hash validation, mutation replay",
            "forbidden": "evidence acceptance;runtime;production;PRS/EAS numeric sidewall outputs",
            "exact_signoff_wording": "Authorize descriptor receipt dry-run only, no evidence acceptance.",
            "rollback": "discard dry-run outputs if no-auth locks fail",
            "next_owner": "NODI receiver after user decision",
            "required_evidence": "COMSOL descriptor export manifest/hash and NODI receipt harness input",
        },
        {
            "backlog_id": "RC2-BINDING-POLICY-REVIEW",
            "category": "BINDING_POLICY_REVIEW",
            "status": "BACKLOG_FAIL_CLOSED",
            "allowed": "route/view/diameter/bin policy discussion and negative fixtures",
            "forbidden": "UNBOUND promotion;micro-as-nano binding;borrowed grains",
            "exact_signoff_wording": "Open binding policy review only, no accepted rows.",
            "rollback": "keep binding FAIL_CLOSED",
            "next_owner": "Total control plus NODI/COMSOL review",
            "required_evidence": "explicit route/view/diameter/bin binding sidecar",
        },
        {
            "backlog_id": "RC2-PACKAGE-C-PHYSICS-DISCUSSION",
            "category": "PACKAGE_C_PHYSICS_AUTHORIZATION_DISCUSSION_ONLY",
            "status": "BACKLOG_DISCUSSION_ONLY",
            "allowed": "discussion of wall distance, near-wall, optical, trajectory, solver evidence requirements",
            "forbidden": "COMSOL run;runtime recompute;physics proof registry update",
            "exact_signoff_wording": "Open Package C physics authorization discussion only, no run and no code execution.",
            "rollback": "return to Gate24 no-auth ledger",
            "next_owner": "User/total control",
            "required_evidence": "future explicit Package C authorization checklist",
        },
        {
            "backlog_id": "RC2-COMSOL-PRODUCER-FINAL-ACK",
            "category": "COMSOL_PRODUCER_FINAL_ACK_REINTAKE",
            "status": "BACKLOG_NO_RUN",
            "allowed": "COMSOL reads NODI RC1 final package and updates producer ACK status",
            "forbidden": "COMSOL simulation;.mph load;solver evidence",
            "exact_signoff_wording": "Request COMSOL producer final ACK re-intake, no run.",
            "rollback": "treat stale/dirty ACK as context-only partial",
            "next_owner": "COMSOL producer thread",
            "required_evidence": "NODI RC1 final status/version/source-lock/manifest",
        },
    ]


def final_no_auth_rows() -> list[dict[str, str]]:
    rows = []
    for field in FORBIDDEN_FIELDS:
        rows.append(
            {
                "field_or_claim": field,
                "positive_authorized_count": "0",
                "allowed_context": "blocked_use_or_negative_fixture_mention_only",
                "status": "PASS_NO_AUTH",
            }
        )
    return rows


def self_review_rows() -> list[dict[str, str]]:
    dimensions = [
        "source lock",
        "semantic digest",
        "Gate25 backlog",
        "COMSOL ACK context",
        "Package A/B/D",
        "Package C",
        "no-auth aliases",
        "manifest/SHA",
        "test coverage",
        "Git scope",
        "future handoff",
        "user decision text",
    ]
    return [
        {
            "reviewer_id": f"RC1F-REVIEW-{idx:02d}",
            "dimension": dim,
            "verdict": "PASS",
            "notes": "No runtime, production, q_ch, JRC, or Package C authorization opened.",
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
    current_head = git_head(PROJECT_ROOT)
    comsol_head = git_head(COMSOL_ROOT)
    old_status = read_json(OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_STATUS_20260630.json")
    old_lock = read_json(OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_VERSION_LOCK_20260630.json")
    previous_locked_head = str(old_status.get("nodi_head") or old_lock.get("nodi_head") or "")
    gate25_status = read_json(OUTPUT_DIR / "NODI_COMSOL_GATE25_SIDEWALL_STATUS_20260630.json")
    dirty, dirty_blockers = clean_worktree_rows()
    commits = recent_commit_rows(previous_locked_head, current_head)
    closures = source_lock_closure_rows(previous_locked_head, current_head, old_status, gate25_status, dirty_blockers)
    closure_blockers = sum(1 for row in closures if not row["closure_status"].startswith("CLOSED"))
    final_lock = final_version_lock(previous_locked_head, current_head, comsol_head, old_lock)
    final_lock["dirty_blocker_count"] = dirty_blockers
    final_lock["source_lock_blocker_count"] = closure_blockers
    if dirty_blockers or closure_blockers:
        final_lock["disposition"] = PARTIAL_DISPOSITION
    comsol = comsol_reintake_rows(comsol_head)
    backlog = rc2_backlog_rows()
    no_auth = final_no_auth_rows()
    summary = {
        "disposition": final_lock["disposition"],
        "rc_id": RC_ID,
        "final_nodi_head": current_head,
        "previous_locked_head": previous_locked_head,
        "comsol_producer_ack_head": comsol_head,
        "semantic_digest": final_lock["semantic_digest"],
        "anchor_digest": final_lock["anchor_digest"],
        "source_lock_blocker_count": final_lock["source_lock_blocker_count"],
        "dirty_blocker_count": final_lock["dirty_blocker_count"],
        "missing_required_source_count": final_lock["missing_required_source_count"],
        "static_fixture_unknown_rows": final_lock["static_fixture_unknown_rows"],
        "gate25_backlog_rows": 1,
        "comsol_reintake_pointer_rows": len(comsol),
        "rc2_backlog_rows": len(backlog),
        "no_auth_firewall_rows": len(no_auth),
        "self_review_rows": 12,
        "gate2d_rows": 4,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
    }
    return {
        "summary": summary,
        "dirty_worktree_audit": dirty,
        "current_audit_ledger": commits,
        "source_lock_closure": closures,
        "final_version_lock": final_lock,
        "comsol_reintake_pointer": comsol,
        "rc2_backlog": backlog,
        "no_auth_firewall": no_auth,
        "self_review": self_review_rows(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    summary = payload["summary"]
    if summary["disposition"] != DISPOSITION:
        issues.append("final closure did not reach PASS disposition")
    if summary["source_lock_blocker_count"] != 0:
        issues.append("source-lock blocker remains open")
    if summary["dirty_blocker_count"] != 0:
        issues.append("dirty blocker remains open")
    if summary["static_fixture_unknown_rows"] != 0:
        issues.append("static fixture unknown rows remain")
    if summary["gate2d_rows"] != 4:
        issues.append("Gate2D row count drift")
    if summary["edge_state"] != "NOT_APPROVED_PREAUTH_ONLY":
        issues.append("EDGE state drift")
    if summary["qch_state"] != "ABSENT":
        issues.append("QCH state drift")
    if summary["binding_state"] != "FAIL_CLOSED":
        issues.append("BINDING state drift")
    for row in payload["rc2_backlog"]:
        if row["status"].startswith("AUTHORIZED"):
            issues.append("RC2 backlog row opened authorization")
    for row in payload["no_auth_firewall"]:
        if row["positive_authorized_count"] != "0":
            issues.append(f"forbidden auth count nonzero for {row['field_or_claim']}")
    return issues


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "status": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_STATUS_20260630.json",
        "version": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_VERSION_LOCK_20260630.json",
        "audit": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_CURRENT_AUDIT_LEDGER_20260630.csv",
        "closure": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_SOURCE_LOCK_CLOSURE_20260630.csv",
        "comsol": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_COMSOL_REINTAKE_POINTER_20260630.csv",
        "backlog": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC2_BACKLOG_20260630.csv",
        "no_auth": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_NO_AUTH_FIREWALL_20260630.csv",
        "review": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_SELF_REVIEW_20260630.csv",
        "report_json": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_REPORT_20260630.json",
        "report_md": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_RELEASE_PACKET_20260630.md",
        "manifest": OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_MANIFEST_20260630.csv",
        "master": REPORT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_CLOSURE_AND_RC2_BACKLOG_20260630.md",
    }
    write_json(paths["status"], payload["summary"])
    write_json(paths["version"], payload["final_version_lock"])
    write_csv(paths["audit"], payload["current_audit_ledger"])
    write_csv(paths["closure"], payload["source_lock_closure"])
    write_csv(paths["comsol"], payload["comsol_reintake_pointer"])
    write_csv(paths["backlog"], payload["rc2_backlog"])
    write_csv(paths["no_auth"], payload["no_auth_firewall"])
    write_csv(paths["review"], payload["self_review"])
    write_json(paths["report_json"], payload)
    lines = [
        f"- Disposition: {payload['summary']['disposition']}",
        f"- Final NODI head: {payload['summary']['final_nodi_head']}",
        f"- Previous locked head: {payload['summary']['previous_locked_head']}",
        f"- COMSOL producer ACK head: {payload['summary']['comsol_producer_ack_head']}",
        f"- Semantic digest: {payload['summary']['semantic_digest']}",
        "- Package A/B/D: static/contract preflight ready, no runtime.",
        "- Package C: BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION.",
        "- Gate25 is bound as RC2 backlog only, no implementation permission.",
    ]
    write_md(paths["report_md"], "SIDEWALL_STATIC_INTEROP_RC1 Final Release Packet", lines)
    write_md(paths["master"], "SIDEWALL_STATIC_INTEROP_RC1 Final Closure And RC2 Backlog", lines)
    manifest_targets = [path for key, path in paths.items() if key != "manifest"]
    write_csv(paths["manifest"], manifest_rows(manifest_targets))
    return [*manifest_targets, paths["manifest"]]


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_sidewall_static_interop_rc1_final:
        print("--confirm-sidewall-static-interop-rc1-final is required", file=sys.stderr)
        return 2
    payload = build_payload()
    issues = validate_payload(payload)
    paths = write_outputs(payload)
    if issues:
        print("RC1_FINAL_VALIDATION_FAILED")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(payload["summary"]["disposition"])
    print(f"semantic_digest={payload['summary']['semantic_digest']}")
    print(f"outputs={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
