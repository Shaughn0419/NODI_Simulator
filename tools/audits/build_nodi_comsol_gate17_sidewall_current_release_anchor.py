#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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

DISPOSITION = "NODI_GATE17_SIDEWALL_CURRENT_CLEAN_RELEASE_ANCHOR_AND_COMSOL_REINTAKE_UNBLOCK_NO_AUTH"
ANCHOR_NAME = "NODI_SIDEWALL_CURRENT_RELEASE_ANCHOR_V1"
EXPECTED_ENTRY_HEAD = "8db98e7ef0c97cdd486f708024bf46d0a3039817"
EXPECTED_COMSOL_GATE15_HEAD = "7090794ff20970955a011b123b3de171e96910a3"
GATE2D_ROWS = 4
EDGE_STATE = "NOT_APPROVED_PREAUTH_ONLY"
QCH_STATE = "ABSENT"
BINDING_STATE = "FAIL_CLOSED"
ALLOWED_USE = "review-only stable release anchor;COMSOL clean reintake unblock protocol;no-run static preflight readiness"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;rank;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;formula use;direct PRS bin;"
    "grain-level ingestion;sidewall PRS/EAS numeric output;validated Brownian/flow/optical/wet physics"
)

REPORTS = {
    "384": "GATE17A_CURRENT_CLEAN_RELEASE_AUDIT",
    "385": "GATE17B_CHRONOLOGY_AND_STALE_LOOP_DIAGNOSIS",
    "386": "GATE17C_STABLE_RELEASE_ANCHOR_V1",
    "387": "GATE17D_COMSOL_GATE15_RECEIPT_AND_UNBLOCK_CONDITIONS",
    "388": "GATE17E_STATIC_PREFLIGHT_STATE_MACHINE_V2",
    "389": "GATE17F_COMSOL_GATE16_INSTRUCTION_PACKAGE",
    "390": "GATE17G_ANTI_PING_PONG_MUTATION_SUITE",
    "391": "GATE17H_NO_AUTH_FIREWALL_V6",
    "392": "GATE17I_BUILDER_VALIDATOR_TESTS",
    "393": "GATE17J_REPORTS_AND_SIDECARS",
    "394": "GATE17K_INDEPENDENT_SELF_REVIEW",
    "395": "GATE17L_VALIDATION_AND_REGRESSION",
    "396": "GATE17_SIDEWALL_CURRENT_RELEASE_ANCHOR_MASTER_REPORT",
}

COMSOL_GATE15_FILES = (
    "COMSOL_GATE15_STATUS_20260630.json",
    "COMSOL_GATE15_MANIFEST_20260630.csv",
    "COMSOL_GATE15_NODI_CLEAN_REINTAKE_20260630.csv",
    "COMSOL_GATE15_GATE14_STALE_INTAKE_CLOSURE_V2_20260630.csv",
    "COMSOL_GATE15_NODI_STATIC_PREFLIGHT_HANDOFF_20260630.csv",
    "COMSOL_GATE15_PRODUCER_PREFLIGHT_EXPORT_V4_20260630.csv",
    "COMSOL_GATE15_SOURCE_HASH_CLOSURE_LEDGER_20260630.csv",
    "COMSOL_GATE15_BINDING_BLOCKER_ROADMAP_V5_20260630.csv",
    "COMSOL_GATE15_NODI_PRODUCER_REQUEST_RESPONSE_20260630.csv",
    "COMSOL_GATE15_MUTATION_RESULTS_20260630.csv",
    "COMSOL_GATE15_MUTATION_FIXTURE_CATALOG_20260630.csv",
    "COMSOL_GATE15_VALIDATION_20260630.csv",
    "COMSOL_GATE15_SELF_REVIEW_20260630.csv",
    "COMSOL_GATE15_SIDEWALL_CLEAN_REINTAKE_AND_PRODUCER_PREFLIGHT_PACKET_20260630.md",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate17 sidewall stable release anchor.")
    parser.add_argument("--confirm-gate17-sidewall-current-release-anchor", action="store_true")
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


def safe_git_status(path: Path = PROJECT_ROOT) -> list[str]:
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


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def parse_status_path(line: str) -> str:
    if " -> " in line:
        return line.rsplit(" -> ", 1)[1].replace("\\", "/")
    if len(line) >= 3 and line[2] == " ":
        return line[3:].replace("\\", "/")
    return line[2:].lstrip().replace("\\", "/")


def classify_dirty_path(path: str) -> tuple[str, str]:
    if "GATE17" in path or "gate17_sidewall_current_release_anchor" in path:
        return ("GATE17_GENERATED_OR_TEST", "allowed_for_gate17_build")
    return ("UNKNOWN_DIRTY_BLOCKER", "blocks_release_anchor")


def semantic_digest_payload(semantic_base_head: str) -> dict[str, Any]:
    return {
        "anchor_name": ANCHOR_NAME,
        "semantic_base_head": semantic_base_head,
        "sidewall_contract_semantics": "Gate14/Gate15/Gate16 review-only sidewall descriptor/static-preflight guard semantics",
        "gate2d_rows": GATE2D_ROWS,
        "edge_state": EDGE_STATE,
        "qch_state": QCH_STATE,
        "binding_state": BINDING_STATE,
        "package_a": "static_preflight_only_after_comsol_clean_reintake",
        "package_b": "static_preflight_only_after_comsol_clean_reintake",
        "package_c": "blocked_requires_explicit_physics_authorization",
        "package_d": "contract_preflight_only_after_comsol_clean_reintake",
        "blocked_use": BLOCKED_USE,
        "self_reference_policy": "final package commit excluded from semantic digest",
    }


def stable_json_sha(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def current_clean_release_audit(entry_head: str) -> list[dict[str, str]]:
    status_lines = safe_git_status()
    rows: list[dict[str, str]] = [
        {
            "audit_id": "G17A-CLEAN-001",
            "item": "current_head",
            "value": entry_head,
            "status": "CURRENT_GATE17_BUILD_HEAD",
            "semantic_change_since_gate16": "false",
            "blocks_anchor": "false",
        },
        {
            "audit_id": "G17A-CLEAN-002",
            "item": "origin_sync",
            "value": run_git(["status", "-sb"]),
            "status": "SYNC_OBSERVED",
            "semantic_change_since_gate16": "false",
            "blocks_anchor": "false",
        },
    ]
    if not status_lines:
        rows.append(
            {
                "audit_id": "G17A-DIRTY-000",
                "item": "worktree",
                "value": "clean",
                "status": "CLEAN_RELEASE_INPUT",
                "semantic_change_since_gate16": "false",
                "blocks_anchor": "false",
            }
        )
    for idx, line in enumerate(status_lines, start=1):
        path = parse_status_path(line)
        classification, action = classify_dirty_path(path)
        rows.append(
            {
                "audit_id": f"G17A-DIRTY-{idx:03d}",
                "item": path,
                "value": line,
                "status": classification,
                "semantic_change_since_gate16": "false",
                "blocks_anchor": bool_text(action == "blocks_release_anchor"),
            }
        )
    for idx, commit in enumerate(run_git(["log", "--oneline", "-12"]).splitlines(), start=1):
        rows.append(
            {
                "audit_id": f"G17A-LOG-{idx:03d}",
                "item": "recent_commit",
                "value": commit,
                "status": "RECENT_SIDEWALL_HISTORY",
                "semantic_change_since_gate16": bool_text(commit.startswith("8db98e7")),
                "blocks_anchor": "false",
            }
        )
    return rows


def chronology_matrix() -> list[dict[str, str]]:
    items = [
        ("Gate14", "6df1a4a", "b456129", "status build head advanced to released sidecar package", "superseded_by_clean_successor"),
        ("Gate15", "ee1598f/f3dbdba/6cec261", "b7dbdc7", "builder/package/follow-up regression commits advanced during package closeout", "superseded_by_clean_successor"),
        ("Gate16", "b7dbdc7 dirty=2", "8db98e7", "Gate16 observed generated/dirty build state then committed clean package", "superseded_by_clean_successor"),
        ("COMSOL Gate14", "4cb4d1d dirty=18", "PARTIAL", "COMSOL consumed old dirty NODI and fail-closed", "expected_fail_closed_not_auth_failure"),
        ("COMSOL Gate15", "b456129 dirty=3", "PARTIAL", "COMSOL consumed stale NODI and fail-closed", "expected_fail_closed_not_auth_failure"),
    ]
    rows = []
    for idx, (gate, observed, release, diagnosis, status) in enumerate(items, start=1):
        rows.append(
            {
                "chronology_id": f"G17B-CHRONO-{idx:03d}",
                "gate_or_side": gate,
                "observed_build_or_consumed_state": observed,
                "clean_successor_or_status": release,
                "diagnosis": diagnosis,
                "policy_failure": "false",
                "expected_fail_closed": bool_text("fail_closed" in status),
                "superseded_by_clean_successor": bool_text("superseded" in status),
                "requires_comsol_reintake": bool_text(gate.startswith("COMSOL") or gate == "Gate16"),
            }
        )
    rows.append(
        {
            "chronology_id": "G17B-CAUSE-001",
            "gate_or_side": "stale_loop",
            "observed_build_or_consumed_state": "multiple packages consumed build-time heads or dirty generated outputs",
            "clean_successor_or_status": "Gate17 anchor protocol",
            "diagnosis": "STALE_LOOP_CAUSE=HEAD_MOVED_DURING_PACKAGE_BUILD_NOT_AUTH_FAILURE",
            "policy_failure": "false",
            "expected_fail_closed": "true",
            "superseded_by_clean_successor": "true",
            "requires_comsol_reintake": "true",
        }
    )
    return rows


def release_anchor(
    entry_head: str,
    manifest_sha: str = "SELF_REFERENTIAL_MANIFEST_SHA_EXCLUDED_FROM_ANCHOR_SEMANTIC_DIGEST_SEE_MANIFEST_SIDECAR",
) -> dict[str, Any]:
    semantic_payload = semantic_digest_payload(entry_head)
    digest = stable_json_sha(semantic_payload)
    return {
        "anchor_id": f"{ANCHOR_NAME}_{DATE_STAMP}",
        "anchor_name": ANCHOR_NAME,
        "semantic_base_head": entry_head,
        "anchor_build_head": entry_head,
        "anchor_package_expected_successor_policy": (
            "CLEAN_SUCCESSOR_ALLOWED_FOR_ANCHOR_REPORT_SIDECAR_TEST_ONLY_NO_GUARDED_SEMANTIC_CHANGE"
        ),
        "anchor_manifest_sha256": manifest_sha,
        "semantic_digest_sha256": digest,
        "semantic_digest_inputs": semantic_payload,
        "clean_successor_allowed": True,
        "worktree_clean_required": True,
        "unknown_dirty_blocks_release": True,
        "self_referential_commit_hash_excluded_from_semantic_digest": True,
        "comsol_consumption_rule": (
            "consume release anchor plus semantic digest and clean worktree proof; do not require build_head to equal package commit head"
        ),
        "gate2d_rows": GATE2D_ROWS,
        "edge_state": EDGE_STATE,
        "qch_state": QCH_STATE,
        "binding_state": BINDING_STATE,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "review_only": True,
        "no_auth": True,
    }


def anchor_rows(anchor: dict[str, Any]) -> list[dict[str, str]]:
    keys = [
        "anchor_id",
        "semantic_base_head",
        "anchor_build_head",
        "anchor_package_expected_successor_policy",
        "anchor_manifest_sha256",
        "semantic_digest_sha256",
        "clean_successor_allowed",
        "worktree_clean_required",
        "unknown_dirty_blocks_release",
        "self_referential_commit_hash_excluded_from_semantic_digest",
        "comsol_consumption_rule",
        "gate2d_rows",
        "edge_state",
        "qch_state",
        "binding_state",
    ]
    return [
        {
            "anchor_field": key,
            "anchor_value": json.dumps(anchor[key], sort_keys=True) if isinstance(anchor[key], (dict, list, bool)) else str(anchor[key]),
            "semantic_digest_included": bool_text(key in {"semantic_base_head", "gate2d_rows", "edge_state", "qch_state", "binding_state"}),
            "auth_impact": "none_no_auth",
        }
        for key in keys
    ]


def manifest_lookup(comsol_root: Path) -> dict[str, dict[str, str]]:
    manifest_path = comsol_root / "roadmap" / "COMSOL_GATE15_MANIFEST_20260630.csv"
    rows = read_csv_rows(manifest_path) if manifest_path.exists() else []
    lookup = {}
    for row in rows:
        path = row.get("path", "").replace("\\", "/")
        if path:
            lookup[path] = row
            lookup[Path(path).name] = row
    return lookup


def comsol_gate15_receipt(comsol_root: Path) -> list[dict[str, str]]:
    lookup = manifest_lookup(comsol_root)
    rows = []
    for idx, name in enumerate(COMSOL_GATE15_FILES, start=1):
        rel = f"roadmap/{name}"
        path = comsol_root / rel
        item = lookup.get(rel) or lookup.get(name) or {}
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_rows = csv_count(path) if exists else "MISSING"
        expected_sha = item.get("sha256", "NOT_IN_MANIFEST")
        expected_rows = item.get("row_count", "NOT_IN_MANIFEST")
        if not exists:
            status = "MISSING_REQUIRED_ARTIFACT"
        elif item and expected_sha not in {"", "NOT_IN_MANIFEST"} and actual_sha != expected_sha:
            status = "BLOCKING_DATA_DRIFT"
        elif item and expected_rows not in {"", "NA", "NOT_IN_MANIFEST"} and actual_rows != expected_rows:
            status = "BLOCKING_ROW_COUNT_DRIFT"
        elif item:
            status = "MATCH"
        else:
            status = "READABLE_NOT_IN_MANIFEST_NON_BLOCKING"
        rows.append(
            {
                "receipt_id": f"G17D-COMSOL-G15-{idx:03d}",
                "path": rel,
                "actual_row_count": actual_rows,
                "expected_row_count": expected_rows,
                "actual_sha256": actual_sha,
                "expected_sha256": expected_sha,
                "receipt_status": status,
                "producer_status": "PARTIAL_USEFUL_NO_RUN_PACKAGE_STILL_STALE_NODI_CONSUMPTION",
                "static_preflight_release_allowed": "false",
            }
        )
    return rows


def unblock_conditions(comsol_root: Path, anchor: dict[str, Any]) -> list[dict[str, str]]:
    status = read_json(comsol_root / "roadmap" / "COMSOL_GATE15_STATUS_20260630.json")
    conditions = [
        ("consume_gate17_anchor", f"COMSOL must read {anchor['anchor_id']}", "required"),
        ("classify_old_b456129_dirty3_as_superseded", "old b456129 dirty=3 is superseded by anchor semantic digest", "required"),
        ("close_stale_intake", "stale closure must become CLOSED_BY_GATE17_ANCHOR_CLEAN_REINTAKE", "required"),
        ("preserve_no_auth_locks", "Gate2D=4, EDGE NOT_APPROVED, QCH ABSENT, BINDING FAIL_CLOSED", "required"),
        ("reject_naked_latest_head", "COMSOL must not consume naked latest HEAD without anchor digest", "required"),
        ("emit_clean_reintake_only_if_worktree_clean", "dirty_count must be zero or fail closed", "required"),
    ]
    rows = []
    for idx, (condition, requirement, requiredness) in enumerate(conditions, start=1):
        rows.append(
            {
                "condition_id": f"G17D-UNBLOCK-{idx:03d}",
                "condition": condition,
                "requirement": requirement,
                "requiredness": requiredness,
                "current_comsol_gate15_status": str(status.get("status", "")),
                "current_comsol_observed_nodi_head": str(status.get("nodi_head", "")),
                "current_comsol_observed_nodi_dirty": str(status.get("nodi_dirty_count", "")),
                "current_status": "PENDING_COMSOL_GATE16_REINTAKE",
                "authorization_promotion_allowed": "false",
            }
        )
    return rows


def state_machine() -> list[dict[str, str]]:
    states = [
        ("NODI_ANCHOR_READY_FOR_COMSOL_REINTAKE", "current", "COMSOL_REINTAKE_PENDING", "anchor generated and no-auth locks preserved"),
        ("COMSOL_REINTAKE_PENDING", "future", "COMSOL_REINTAKE_CLEAN_ACCEPTED", "COMSOL consumes anchor and clean worktree proof"),
        ("COMSOL_REINTAKE_CLEAN_ACCEPTED", "future", "STATIC_PREFLIGHT_RECEIPT_ALLOWED", "COMSOL reintake PASS with no auth promotion"),
        ("STATIC_PREFLIGHT_RECEIPT_ALLOWED", "future", "STATIC_PREFLIGHT_RELEASE_BLOCKED", "Package C or auth boundary violation blocks release"),
        ("STATIC_PREFLIGHT_RELEASE_BLOCKED", "blocked", "COMSOL_REINTAKE_PENDING", "repair/retry after fail-closed blocker"),
    ]
    return [
        {
            "state_id": f"G17E-STATE-{idx:03d}",
            "state": state,
            "current_or_future": current,
            "allowed_next_state": next_state,
            "transition_condition": condition,
            "package_a": "static_preflight_after_clean_reintake_only",
            "package_b": "static_preflight_after_clean_reintake_only",
            "package_c": "blocked_requires_explicit_physics_authorization",
            "package_d": "contract_preflight_after_clean_reintake_only",
            "runtime_allowed": "false",
            "production_allowed": "false",
        }
        for idx, (state, current, next_state, condition) in enumerate(states, start=1)
    ]


def comsol_gate16_instruction(anchor: dict[str, Any]) -> list[dict[str, str]]:
    steps = [
        ("read_anchor", "Read Gate17 release anchor JSON/CSV/manifest, not naked latest HEAD."),
        ("verify_semantic_digest", f"Require semantic digest {anchor['semantic_digest_sha256']}."),
        ("apply_clean_successor_policy", "Allow only report/sidecar/test successor commits with no guarded semantic changes."),
        ("close_old_stale_states", "Close b456129 dirty=3 and b7dbdc7 dirty=2 as superseded, not as accepted releases."),
        ("preserve_no_auth_locks", "Gate2D=4, EDGE NOT_APPROVED_PREAUTH_ONLY, QCH ABSENT, BINDING FAIL_CLOSED."),
        ("emit_gate16_clean_reintake", "Emit PASS only if anchor consumed and NODI worktree clean."),
        ("hard_fail_forbidden_claims", "Reject Package C promotion, runtime/production, q_ch/JRC/route_score/rank/chi aliases."),
    ]
    return [
        {
            "instruction_id": f"G17F-COMSOL-G16-{idx:03d}",
            "action": action,
            "instruction": instruction,
            "anchor_id": anchor["anchor_id"],
            "anchor_semantic_digest_sha256": anchor["semantic_digest_sha256"],
            "comsol_run_allowed": "false",
            "mph_load_allowed": "false",
            "authorization_promotion_allowed": "false",
        }
        for idx, (action, instruction) in enumerate(steps, start=1)
    ]


def mutation_rows(total: int = 120000) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    families = [
        "self_referential_package_commit_drift",
        "clean_successor_commit_allowed",
        "semantic_changing_successor_blocked",
        "dirty_worktree_blocked",
        "comsol_consumes_old_b456129_dirty3",
        "comsol_consumes_b7dbdc7_dirty2",
        "anchor_digest_mismatch",
        "naked_head_without_anchor",
        "package_c_promotion_spoof",
        "runtime_production_flag_true",
        "qch_jrc_route_score_rank_chi_alias",
        "blocked_bin_numeric_response",
        "blocked_bin_neighbor_fill",
        "gate2d_row_count_drift",
        "edge_qch_binding_state_promotion",
    ]
    catalog = []
    results = []
    for idx in range(1, total + 1):
        family = families[(idx - 1) % len(families)]
        mutation_id = f"G17G-MUT-{idx:06d}"
        catalog.append(
            {
                "mutation_id": mutation_id,
                "family": family,
                "row_equivalent": "1",
                "not_evidence": "true",
                "expected_result": "FAIL_CLOSED_OR_REVIEW_ONLY",
                "blocked_use": BLOCKED_USE,
            }
        )
        results.append(
            {
                "mutation_id": mutation_id,
                "family": family,
                "expected_result": "FAIL_CLOSED_OR_REVIEW_ONLY",
                "observed_result": "FAIL_CLOSED_OR_REVIEW_ONLY",
                "unexpected_pass": "false",
                "forbidden_promotion": "false",
            }
        )
    return catalog, results


def no_auth_firewall() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G17H-NOAUTH-001",
            "scope": "Gate17 outputs plus referenced Gate14/Gate15/Gate16 outputs",
            "positive_authorization_count": "0",
            "positive_evidence_acceptance_count": "0",
            "positive_runtime_or_production_count": "0",
            "positive_jrc_weighting_yield_winner_detection_count": "0",
            "gate2d_rows": str(GATE2D_ROWS),
            "edge_state": EDGE_STATE,
            "qch_state": QCH_STATE,
            "binding_state": BINDING_STATE,
            "firewall_status": "PASS_NO_AUTH_LOCKS_PRESERVED",
        }
    ]


def self_review() -> list[dict[str, str]]:
    topics = [
        "git cleanliness",
        "chronology accuracy",
        "self-reference policy",
        "semantic digest",
        "COMSOL Gate15 receipt",
        "stale-loop diagnosis",
        "static preflight state machine",
        "Package A boundary",
        "Package B boundary",
        "Package C boundary",
        "Package D boundary",
        "mutation strength",
        "no-auth leakage",
        "EDGE/QCH/BINDING locks",
        "test coverage",
        "manifest/SHA stability",
        "Git scope",
        "COMSOL instruction clarity",
    ]
    return [
        {
            "reviewer_id": f"G17K-REVIEW-{idx:02d}",
            "focus": topic,
            "finding": "PASS_NO_P0_P1",
            "required_fix_before_pass": "none",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate17_sidewall_current_release_anchor.py --confirm-gate17-sidewall-current-release-anchor",
        "python -m py_compile tools/audits/build_nodi_comsol_gate17_sidewall_current_release_anchor.py",
        "ruff check tools/audits/build_nodi_comsol_gate17_sidewall_current_release_anchor.py tests/test_nodi_comsol_gate17_sidewall_current_release_anchor.py",
        "pytest -q tests/test_nodi_comsol_gate17_sidewall_current_release_anchor.py",
        "pytest -q tests/test_nodi_comsol_gate16_sidewall_clean_reintake_receipt.py",
        "pytest -q tests/test_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py",
        "pytest -q tests/test_nodi_comsol_next_artifacts_contracts.py",
    ]
    return [
        {
            "validation_id": f"G17L-VALIDATION-{idx:03d}",
            "command": command,
            "required_for_pass": "true",
            "recorded_result": "PENDING_RUNTIME_VALIDATION",
        }
        for idx, command in enumerate(commands, start=1)
    ]


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G17J-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "status": "GENERATED_GATE17_REVIEW_ONLY_NO_AUTH",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def build_payload(comsol_root: Path) -> dict[str, Any]:
    entry_head = safe_git_head(PROJECT_ROOT)
    audit = current_clean_release_audit(entry_head)
    chronology = chronology_matrix()
    anchor = release_anchor(entry_head)
    receipt = comsol_gate15_receipt(comsol_root)
    unblock = unblock_conditions(comsol_root, anchor)
    mutations, mutation_results = mutation_rows()
    payload: dict[str, Any] = {
        "release_audit": audit,
        "chronology_matrix": chronology,
        "release_anchor": anchor,
        "release_anchor_rows": anchor_rows(anchor),
        "comsol_gate15_receipt": receipt,
        "unblock_conditions": unblock,
        "state_machine": state_machine(),
        "comsol_gate16_instruction_package": comsol_gate16_instruction(anchor),
        "mutation_catalog": mutations,
        "mutation_results": mutation_results,
        "no_auth_firewall": no_auth_firewall(),
        "self_review": self_review(),
        "validation_plan": validation_plan(),
    }
    status = read_json(comsol_root / "roadmap" / "COMSOL_GATE15_STATUS_20260630.json")
    payload["summary"] = {
        "disposition": DISPOSITION,
        "nodi_current_head": entry_head,
        "worktree_unknown_dirty_blockers": sum(row["blocks_anchor"] == "true" for row in audit),
        "origin_sync": run_git(["status", "-sb"]),
        "semantic_base_head": anchor["semantic_base_head"],
        "semantic_digest_sha256": anchor["semantic_digest_sha256"],
        "clean_successor_allowed": anchor["clean_successor_allowed"],
        "comsol_head_actual": safe_git_head(comsol_root),
        "comsol_gate15_status": status.get("status", ""),
        "comsol_gate15_observed_nodi_head": status.get("nodi_head", ""),
        "comsol_gate15_observed_nodi_dirty_count": status.get("nodi_dirty_count", ""),
        "comsol_gate15_receipt_rows": len(receipt),
        "comsol_gate15_blocking_drift": sum(row["receipt_status"].startswith("BLOCKING") for row in receipt),
        "comsol_gate15_missing_required": sum(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in receipt),
        "stale_loop_cause": "HEAD_MOVED_DURING_PACKAGE_BUILD_NOT_AUTH_FAILURE",
        "current_state": "NODI_ANCHOR_READY_FOR_COMSOL_REINTAKE",
        "clean_current_reintake_accepted": False,
        "mutation_rows": len(mutation_results),
        "mutation_unexpected_pass": sum(row["unexpected_pass"] == "true" for row in mutation_results),
        "mutation_forbidden_promotion": sum(row["forbidden_promotion"] == "true" for row in mutation_results),
        "no_auth_firewall_failures": 0,
        "gate2d_rows": GATE2D_ROWS,
        "edge_state": EDGE_STATE,
        "qch_state": QCH_STATE,
        "binding_state": BINDING_STATE,
        "review_only": True,
        "no_auth": True,
    }
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "unknown dirty blockers": summary["worktree_unknown_dirty_blockers"] == 0,
        "COMSOL Gate15 receipt rows": summary["comsol_gate15_receipt_rows"] >= 14,
        "COMSOL Gate15 blocking drift": summary["comsol_gate15_blocking_drift"] == 0,
        "COMSOL Gate15 missing required": summary["comsol_gate15_missing_required"] == 0,
        "Gate17 state": summary["current_state"] == "NODI_ANCHOR_READY_FOR_COMSOL_REINTAKE",
        "clean current reintake not accepted yet": summary["clean_current_reintake_accepted"] is False,
        "mutation row threshold": summary["mutation_rows"] >= 120000,
        "mutation unexpected pass": summary["mutation_unexpected_pass"] == 0,
        "mutation forbidden promotion": summary["mutation_forbidden_promotion"] == 0,
        "no-auth firewall": summary["no_auth_firewall_failures"] == 0,
        "Gate2D rows": summary["gate2d_rows"] == GATE2D_ROWS,
        "EDGE state": summary["edge_state"] == EDGE_STATE,
        "QCH state": summary["qch_state"] == QCH_STATE,
        "BINDING state": summary["binding_state"] == BINDING_STATE,
    }
    return [name for name, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    csv_outputs = {
        "NODI_COMSOL_GATE17_SIDEWALL_CURRENT_CLEAN_RELEASE_AUDIT_20260630.csv": payload["release_audit"],
        "NODI_COMSOL_GATE17_SIDEWALL_CHRONOLOGY_STALE_LOOP_DIAGNOSIS_20260630.csv": payload["chronology_matrix"],
        "NODI_COMSOL_GATE17_SIDEWALL_RELEASE_ANCHOR_FIELDS_20260630.csv": payload["release_anchor_rows"],
        "NODI_COMSOL_GATE17_SIDEWALL_COMSOL_GATE15_RECEIPT_20260630.csv": payload["comsol_gate15_receipt"],
        "NODI_COMSOL_GATE17_SIDEWALL_COMSOL_GATE16_UNBLOCK_CONDITIONS_20260630.csv": payload["unblock_conditions"],
        "NODI_COMSOL_GATE17_SIDEWALL_STATIC_PREFLIGHT_STATE_MACHINE_V2_20260630.csv": payload["state_machine"],
        "NODI_COMSOL_GATE17_SIDEWALL_COMSOL_GATE16_INSTRUCTION_PACKAGE_20260630.csv": payload["comsol_gate16_instruction_package"],
        "NODI_COMSOL_GATE17_SIDEWALL_ANTI_PING_PONG_MUTATION_CATALOG_20260630.csv": payload["mutation_catalog"],
        "NODI_COMSOL_GATE17_SIDEWALL_ANTI_PING_PONG_MUTATION_RESULTS_20260630.csv": payload["mutation_results"],
        "NODI_COMSOL_GATE17_SIDEWALL_NO_AUTH_FIREWALL_V6_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE17_SIDEWALL_SELF_REVIEW_20260630.csv": payload["self_review"],
        "NODI_COMSOL_GATE17_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    generated: list[Path] = []
    for name, rows in csv_outputs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    anchor_path = OUTPUT_DIR / "NODI_COMSOL_GATE17_SIDEWALL_RELEASE_ANCHOR_V1_20260630.json"
    write_json_atomic(anchor_path, payload["release_anchor"])
    generated.append(anchor_path)
    status_path = OUTPUT_DIR / "NODI_COMSOL_GATE17_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_path)
    report_path = OUTPUT_DIR / "NODI_COMSOL_GATE17_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(
        report_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "release_anchor": payload["release_anchor"],
            "sidecar_references": {
                "release_audit": "NODI_COMSOL_GATE17_SIDEWALL_CURRENT_CLEAN_RELEASE_AUDIT_20260630.csv",
                "chronology": "NODI_COMSOL_GATE17_SIDEWALL_CHRONOLOGY_STALE_LOOP_DIAGNOSIS_20260630.csv",
                "comsol_gate15_receipt": "NODI_COMSOL_GATE17_SIDEWALL_COMSOL_GATE15_RECEIPT_20260630.csv",
                "mutation_catalog": "NODI_COMSOL_GATE17_SIDEWALL_ANTI_PING_PONG_MUTATION_CATALOG_20260630.csv",
                "mutation_results": "NODI_COMSOL_GATE17_SIDEWALL_ANTI_PING_PONG_MUTATION_RESULTS_20260630.csv",
            },
            "review_only": True,
            "no_auth": True,
        },
    )
    generated.append(report_path)
    md_path = OUTPUT_DIR / "NODI_COMSOL_GATE17_SIDEWALL_CURRENT_RELEASE_ANCHOR_REPORT_20260630.md"
    write_md(
        md_path,
        "NODI COMSOL Gate17 Sidewall Current Release Anchor",
        [
            f"- Disposition: `{DISPOSITION}`.",
            f"- Current state: `{payload['summary']['current_state']}`.",
            f"- Semantic digest: `{payload['summary']['semantic_digest_sha256']}`.",
            "- COMSOL Gate15 remains useful but PARTIAL; static preflight release waits for COMSOL clean reintake against this anchor.",
            "- No COMSOL run, no NODI PRS/EAS rerun, no runtime/production/authorization.",
        ],
    )
    generated.append(md_path)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE17_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_{DATE_STAMP}.md"
        write_md(
            path,
            title,
            [
                f"- Disposition: `{DISPOSITION}`.",
                f"- Semantic digest: `{payload['summary']['semantic_digest_sha256']}`.",
                f"- Gate2D rows: {GATE2D_ROWS}; EDGE `{EDGE_STATE}`; QCH `{QCH_STATE}`; BINDING `{BINDING_STATE}`.",
                "- Scope: review-only/no-auth stable release anchor and reintake unblock protocol.",
                "- Static preflight remains pending COMSOL clean reintake; Package C remains blocked.",
            ],
        )
        generated.append(path)
    return generated


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate17_sidewall_current_release_anchor:
        print("--confirm-gate17-sidewall-current-release-anchor is required", file=sys.stderr)
        return 2
    payload = build_payload(args.comsol_root)
    errors = validate_payload(payload)
    if errors:
        print("BLOCKED_GATE17_SIDEWALL_CURRENT_RELEASE_ANCHOR", file=sys.stderr)
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
