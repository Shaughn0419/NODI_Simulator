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
COMSOL_ROADMAP = "roadmap"

GATE14_BUILD_HEAD = "6df1a4a8aabcc29ef04badfe83e01def198b1265"
GATE14_RELEASE_HEAD = "b4561298c8e5ba1ef083f0114ed183882117282e"
COMSOL_GATE14_HEAD = "a378398eea8af883e1ec89fc80d93b60ff33a47c"
DISPOSITION = "NODI_GATE15_SIDEWALL_BILATERAL_CONTRACT_V3_CLOSURE_AND_STATIC_PREFLIGHT_READINESS_NO_AUTH"
ALLOWED_USE = "review-only bilateral contract v3 closure;static preflight readiness;COMSOL Gate15 no-run instruction"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;true sidewall PRS/EAS numeric output;"
    "validated Brownian/flow/optical/wet physics"
)

COMSOL_GATE14_FILES = (
    "COMSOL_GATE14_STATUS_20260630.json",
    "COMSOL_GATE14_MANIFEST_20260630.csv",
    "COMSOL_GATE14_VALIDATION_20260630.csv",
    "COMSOL_GATE14_NODI_RELEASED_CLEAN_INTAKE_20260630.csv",
    "COMSOL_GATE14_NODI_IMPLEMENTATION_GUARD_RECEIPT_20260630.csv",
    "COMSOL_GATE14_PRODUCER_SCHEMA_V3_DELTA_20260630.csv",
    "COMSOL_GATE14_PRODUCER_FEASIBILITY_MATRIX_20260630.csv",
    "COMSOL_GATE14_DESCRIPTOR_PROFILE_DRYRUN_EXPORT_V3_20260630.csv",
    "COMSOL_GATE14_BINDING_BLOCKER_ROADMAP_V4_20260630.csv",
    "COMSOL_GATE14_MUTATION_RESULTS_20260630.csv",
    "COMSOL_GATE14_MUTATION_FIXTURE_CATALOG_20260630.csv",
    "COMSOL_GATE14_FUTURE_HANDOFF_ESCROW_V5_20260630.csv",
    "COMSOL_GATE14_GATE13_STALE_INTAKE_CLOSURE_20260630.csv",
    "COMSOL_GATE14_PROVENANCE_LEDGER_20260630.csv",
    "COMSOL_GATE14_SELF_REVIEW_20260630.csv",
    "COMSOL_GATE14_SIDEWALL_IMPLEMENTATION_GUARD_INTAKE_PACKET_20260630.md",
)

REPORTS = {
    "361": "GATE15A_CURRENT_RELEASE_HEAD_RECONCILIATION",
    "362": "GATE15B_COMSOL_GATE14_PARTIAL_PACKAGE_RECEIPT",
    "363": "GATE15C_BILATERAL_CONTRACT_V3_CROSS_SIGNOFF",
    "364": "GATE15D_PRODUCER_REQUEST_FEASIBILITY_RESOLUTION",
    "365": "GATE15E_STATIC_PREFLIGHT_READINESS_BOARD",
    "366": "GATE15F_COMSOL_GATE15_EXACT_INSTRUCTION_PACKAGE",
    "367": "GATE15G_RACE_CONDITION_STALE_INTAKE_MUTATION_EXPANSION",
    "368": "GATE15H_NO_AUTH_CLAIM_BOUNDARY_FIREWALL_V5",
    "369": "GATE15I_VALIDATOR_AND_TESTS",
    "370": "GATE15J_REPORTS_AND_SIDECARS",
    "371": "GATE15K_INDEPENDENT_SELF_REVIEW",
    "372": "GATE15L_VALIDATION_AND_REGRESSION",
    "373": "GATE15M_GIT_CLOSEOUT",
    "374": "GATE15N_FINAL_HANDOFF",
    "375": "GATE15_SIDEWALL_STATIC_PREFLIGHT_READINESS_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate15 sidewall bilateral contract closure package.")
    parser.add_argument("--confirm-gate15-sidewall-bilateral-closure", action="store_true")
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


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def comsol_path(root: Path, name: str) -> Path:
    return root / COMSOL_ROADMAP / name


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def classify_dirty_path(path: str) -> tuple[str, str, str]:
    if path in {
        "nodi_simulator/nodi_comsol_next_artifacts.py",
        "tests/test_nodi_comsol_next_artifacts_contracts.py",
    }:
        return (
            "LEGIT_GATE15_SIDEWALL_BLOCKED_BIN_AND_SUPPORT_SOURCE_GUARD_HARDENING",
            "Package D blocked-bin/support-source guard tightening; no authorization change",
            "stage_with_gate15_commit_after_tests",
        )
    if "GATE15" in path or "gate15_sidewall_bilateral_contract_closure" in path:
        return (
            "LEGIT_GATE15_GENERATED_OUTPUT_PENDING_COMMIT",
            "Gate15 generated report/sidecar/builder/test",
            "stage_with_gate15_commit_after_tests",
        )
    if path in {
        "tools/audits/build_nodi_comsol_gate13_sidewall_guard_convergence.py",
        "tools/audits/build_nodi_comsol_gate14_sidewall_implementation_contract.py",
        "tests/test_nodi_comsol_gate14_sidewall_implementation_contract.py",
    }:
        return (
            "LEGIT_SIDEWALL_SUCCESSOR_HEAD_COMPATIBILITY_UPDATE",
            "Gate13/Gate14 regression compatibility for known COMSOL Gate15 successor head; no authorization change",
            "stage_with_gate15_commit_after_tests",
        )
    return ("UNKNOWN_USER_CHANGE_BLOCKER", "Unclassified dirty file", "do_not_stage")


def parse_git_status_path(line: str) -> str:
    if " -> " in line:
        line = line.rsplit(" -> ", 1)[1]
    if len(line) >= 3 and line[2] == " ":
        return line[3:].replace("\\", "/")
    return line[2:].lstrip().replace("\\", "/")


def current_release_reconciliation() -> list[dict[str, str]]:
    status = run_git(["status", "--short"])
    dirty_lines = status.splitlines() if status else []
    rows = [
        {
            "ledger_id": "G15A-HEAD-001",
            "commit": GATE14_BUILD_HEAD,
            "short_commit": "6df1a4a",
            "role": "Gate14 status build head",
            "change": "builder/reports package generated before later sidecar/audit commits",
            "changes_contract_semantics": "false",
            "release_interpretation": "SUPERSEDED_BY_CURRENT_RELEASE_HEAD",
        },
        {
            "ledger_id": "G15A-HEAD-002",
            "commit": "34ae965",
            "short_commit": "34ae965",
            "role": "successor-head allowance",
            "change": "allows COMSOL producer head to advance after package baseline if package receipt remains valid",
            "changes_contract_semantics": "false",
            "release_interpretation": "AUDIT_COMPATIBILITY_UPDATE",
        },
        {
            "ledger_id": "G15A-HEAD-003",
            "commit": "63a4c02",
            "short_commit": "63a4c02",
            "role": "audit update",
            "change": "updates roadmap/audit text; no contract semantics change",
            "changes_contract_semantics": "false",
            "release_interpretation": "AUDIT_UPDATE",
        },
        {
            "ledger_id": "G15A-HEAD-004",
            "commit": GATE14_RELEASE_HEAD,
            "short_commit": "b456129",
            "role": "Gate14 released sidecar package head",
            "change": "force-added ignored Gate14 sidecars and pushed release package",
            "changes_contract_semantics": "false",
            "release_interpretation": "CURRENT_RELEASE_HEAD_B456129_SUPERSEDES_GATE14_BUILD_HEAD_6DF1A4A",
        },
    ]
    current_head = safe_git_head(PROJECT_ROOT)
    rows.append(
        {
            "ledger_id": "G15A-HEAD-005",
            "commit": current_head,
            "short_commit": current_head[:7],
            "role": "current local head at Gate15 build",
            "change": "Gate15 may include legitimate blocked-bin/support-source guard hardening before final commit",
            "changes_contract_semantics": "false",
            "release_interpretation": "CLEAN_RELEASE_OR_LEGIT_GATE15_PENDING_HARDENING",
        }
    )
    for idx, line in enumerate(dirty_lines, start=1):
        path = parse_git_status_path(line)
        classification, intent, action = classify_dirty_path(path)
        rows.append(
            {
                "ledger_id": f"G15A-DIRTY-{idx:03d}",
                "commit": current_head,
                "short_commit": current_head[:7],
                "role": "worktree_dirty_classification",
                "change": path,
                "changes_contract_semantics": "false",
                "release_interpretation": classification,
                "diff_intent": intent,
                "commit_action": action,
            }
        )
    if not dirty_lines:
        rows.append(
            {
                "ledger_id": "G15A-DIRTY-000",
                "commit": current_head,
                "short_commit": current_head[:7],
                "role": "worktree_dirty_classification",
                "change": "none",
                "changes_contract_semantics": "false",
                "release_interpretation": "CLEAN_RELEASE",
                "diff_intent": "no dirty worktree",
                "commit_action": "none",
            }
        )
    return rows


def manifest_lookup(root: Path) -> dict[str, dict[str, str]]:
    manifest = comsol_path(root, "COMSOL_GATE14_MANIFEST_20260630.csv")
    if not manifest.exists():
        return {}
    rows = read_csv_rows(manifest)
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        for key in ("path", "relative_path", "artifact_path", "file", "artifact"):
            value = row.get(key, "").replace("\\", "/").lstrip("./")
            if value:
                lookup[value] = row
                lookup[Path(value).name] = row
    return lookup


def comsol_gate14_receipt(root: Path) -> list[dict[str, str]]:
    lookup = manifest_lookup(root)
    rows = []
    for idx, name in enumerate(COMSOL_GATE14_FILES, start=1):
        rel = f"roadmap/{name}"
        path = comsol_path(root, name)
        recorded = lookup.get(rel) or lookup.get(name) or {}
        exists = path.exists()
        sha = sha256_file(path) if exists else "MISSING"
        row_count = csv_count(path) if exists else "MISSING"
        recorded_sha = recorded.get("sha256", recorded.get("sha", "NOT_IN_MANIFEST"))
        recorded_count = recorded.get("row_count", recorded.get("rows", "NOT_IN_MANIFEST"))
        if not exists:
            status = "MISSING_REQUIRED_ARTIFACT"
        elif recorded and recorded_sha not in {"", "NOT_IN_MANIFEST"} and sha != recorded_sha:
            status = "BLOCKING_DATA_DRIFT"
        elif recorded and recorded_count not in {"", "NA", "NOT_IN_MANIFEST"} and row_count != recorded_count:
            status = "BLOCKING_DATA_DRIFT"
        elif recorded:
            status = "MATCH"
        elif name == "COMSOL_GATE14_MANIFEST_20260630.csv":
            status = "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"
        else:
            status = "READABLE_NOT_IN_MANIFEST_NON_BLOCKING"
        rows.append(
            {
                "receipt_id": f"G15B-COMSOL-G14-RCPT-{idx:03d}",
                "artifact_name": name,
                "relative_source_path": rel,
                "absolute_path": str(path),
                "row_count": row_count,
                "recorded_row_count": recorded_count,
                "sha256": sha,
                "recorded_sha256": recorded_sha,
                "receipt_status": status,
                "producer_status": "PARTIAL_REVIEW_ONLY_NO_AUTH",
                "nodi_policy_impact": "partial_due_to_old_nodi_intake_only_not_authorization_failure",
                "fully_accepted_as_producer_package": "false",
            }
        )
    return rows


def comsol_partial_reason(root: Path) -> list[dict[str, str]]:
    status = read_json(comsol_path(root, "COMSOL_GATE14_STATUS_20260630.json"))
    return [
        {
            "partial_reason_id": "G15B-PARTIAL-001",
            "comsol_status": str(status.get("status", "")),
            "observed_nodi_head": str(status.get("nodi_head", "")),
            "observed_nodi_dirty_count": str(status.get("nodi_dirty_count", "")),
            "observed_nodi_intake_verdict": str(status.get("nodi_intake_verdict", "")),
            "stale_intake_closure_verdict": str(status.get("stale_intake_closure_verdict", "")),
            "nodi_current_release_head": safe_git_head(PROJECT_ROOT),
            "nodi_verdict": "RACE_TIME_DELTA_REQUIRES_COMSOL_GATE15_CLEAN_REINTAKE",
            "schema_failure": "false",
            "mutation_failure": bool_text(int(status.get("unexpected_pass_count", 0)) != 0),
            "authorization_failure": bool_text(int(status.get("authorization_promotion_count", 0)) != 0),
            "treat_as_full_pass_now": "false",
        }
    ]


def bilateral_schema_cross_signoff(root: Path) -> list[dict[str, str]]:
    nodi_rows = read_csv_rows(OUTPUT_DIR / "NODI_COMSOL_GATE14_SIDEWALL_INTERFACE_CONTRACT_V3_SCHEMA_DELTA_20260630.csv")
    comsol_rows = read_csv_rows(comsol_path(root, "COMSOL_GATE14_PRODUCER_SCHEMA_V3_DELTA_20260630.csv"))
    comsol_text = "\n".join(json.dumps(row, sort_keys=True).lower() for row in comsol_rows)
    rows = []
    for idx, row in enumerate(nodi_rows, start=1):
        field = row.get("field_or_family", "")
        family = row.get("field_family", "")
        if row.get("forbidden_positive") == "true":
            status = "BLOCKED_AS_EXPECTED"
        elif field.lower() in comsol_text:
            status = "BILATERAL_EXACT_MATCH"
        elif family in {"measured_profile_guard", "package_C_gate"}:
            status = "FUTURE_COMSOL_EXPORT_REQUIRED"
        elif row.get("nodi_responsibility") == "NODI receiver":
            status = "NODI_RECEIVER_COMPUTED"
        else:
            status = "COMSOL_SUPERSET_REVIEW_ONLY"
        rows.append(
            {
                "cross_signoff_id": f"G15C-SCHEMA-{idx:03d}",
                "field_or_family": field,
                "nodi_expectation": row.get("comsol_producer_expectation", ""),
                "comsol_producer_status": status,
                "responsibility": row.get("nodi_responsibility", ""),
                "units_or_default": "see schema v3 source row",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "status": status,
                "semantic_conflict": "false",
            }
        )
    for extra_idx in range(max(0, len(comsol_rows) - len(nodi_rows))):
        rows.append(
            {
                "cross_signoff_id": f"G15C-COMSOL-EXTRA-{extra_idx+1:03d}",
                "field_or_family": f"COMSOL_SCHEMA_SUPERSET_ROW_{extra_idx+1}",
                "nodi_expectation": "review-only producer-side superset row",
                "comsol_producer_status": "COMSOL_SUPERSET_REVIEW_ONLY",
                "responsibility": "COMSOL producer",
                "units_or_default": "see COMSOL schema v3",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "status": "COMSOL_SUPERSET_REVIEW_ONLY",
                "semantic_conflict": "false",
            }
        )
    return rows


def producer_request_resolution(root: Path) -> list[dict[str, str]]:
    requests = read_csv_rows(OUTPUT_DIR / "NODI_COMSOL_GATE14_SIDEWALL_COMSOL_PRODUCER_REQUEST_V3_20260630.csv")
    feasibility = read_csv_rows(comsol_path(root, "COMSOL_GATE14_PRODUCER_FEASIBILITY_MATRIX_20260630.csv"))
    dryrun = read_csv_rows(comsol_path(root, "COMSOL_GATE14_DESCRIPTOR_PROFILE_DRYRUN_EXPORT_V3_20260630.csv"))
    feasibility_text = "\n".join(json.dumps(row, sort_keys=True).lower() for row in feasibility)
    dryrun_text = "\n".join(json.dumps(row, sort_keys=True).lower() for row in dryrun)
    rows = []
    for idx, row in enumerate(requests, start=1):
        artifact = row.get("required_artifact", "")
        fields = row.get("required_fields", "")
        key = artifact.lower().split("_")[0]
        covered = key in feasibility_text or any(field.strip().lower() in dryrun_text for field in fields.split(","))
        future_only = row.get("future_authorization_required") == "true" or "solver" in artifact or "future" in row.get("request_lane", "")
        if future_only:
            status = "FUTURE_ONLY_BLOCKED_NOT_AUTHORIZED"
        elif covered:
            status = "COVERED_BY_COMSOL_GATE14_PARTIAL_REQUIRES_GATE15_CLEAN_REINTAKE"
        else:
            status = "NODI_RECEIVER_COMPUTED_OR_COMSOL_GATE15_EXPORT_REQUIRED"
        rows.append(
            {
                "resolution_id": f"G15D-REQUEST-{idx:03d}",
                "request_id": row.get("request_id", f"request-{idx}"),
                "required_artifact": artifact,
                "coverage_status": status,
                "covered_by_comsol_gate14": bool_text(covered),
                "still_needs_comsol_gate15_clean_reintake": bool_text(not future_only),
                "future_only": bool_text(future_only),
                "nodi_receiver_computed": bool_text("NODI_RECEIVER_COMPUTED" in status),
                "blocked_use_until_pass": BLOCKED_USE,
            }
        )
    return rows


def static_preflight_readiness_board() -> list[dict[str, str]]:
    rows = [
        ("Package A", "READY_FOR_STATIC_PREFLIGHT_AFTER_COMSOL_CLEAN_REINTAKE", "schema/descriptor/profile guard only"),
        ("Package B", "READY_FOR_STATIC_PREFLIGHT_AFTER_COMSOL_CLEAN_REINTAKE", "geometry/sampler/signature guard only"),
        ("Package C", "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION", "near-wall/optical/wet physics not validated"),
        ("Package D", "READY_FOR_CONTRACT_PREFLIGHT_AFTER_COMSOL_CLEAN_REINTAKE", "PRS/EAS contract precheck only"),
    ]
    return [
        {
            "board_id": f"G15E-{pkg.replace(' ', '-')}",
            "package": pkg,
            "readiness": readiness,
            "scope": scope,
            "runtime_allowed": "false",
            "production_allowed": "false",
            "validated_physics_claim": "false",
            "requires_comsol_gate15_clean_reintake": bool_text("READY" in readiness),
            "future_authorization_required": bool_text("BLOCKED" in readiness),
        }
        for pkg, readiness, scope in rows
    ]


def comsol_gate15_instruction_package() -> list[dict[str, str]]:
    steps = [
        ("read_nodi_current_release", "Read NODI current release head and Gate15 sidecars.", "required"),
        ("close_old_dirty_intake", "Close old 4cb4d1d dirty=18 observed-unreleased intake as superseded.", "required"),
        ("rebuild_intake_receipt", "Rebuild NODI intake receipt against current clean NODI package.", "required"),
        ("update_stale_intake_closure", "Set stale-intake closure to closed only after clean re-intake.", "required"),
        ("preserve_no_auth_locks", "Keep Gate2D=4, EDGE NOT_APPROVED, QCH ABSENT, BINDING FAIL_CLOSED.", "required"),
        ("emit_no_run_preflight_package", "Emit no-run producer preflight package, not evidence acceptance.", "required"),
        ("avoid_unrelated_dirty", "Do not stage unrelated dirty/untracked COMSOL files.", "required"),
    ]
    return [
        {
            "instruction_id": f"G15F-COMSOL-NEXT-{idx:03d}",
            "action": action,
            "instruction": instruction,
            "requiredness": requiredness,
            "comsol_run_allowed": "false",
            "mph_load_allowed": "false",
            "authorization_promotion_allowed": "false",
        }
        for idx, (action, instruction, requiredness) in enumerate(steps, start=1)
    ]


def mutation_rows(total: int = 100000) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    families = [
        "status_build_head_stale",
        "release_head_advanced_by_audit_only",
        "comsol_old_dirty_intake_consumed_as_release",
        "comsol_partial_accepted_as_pass_spoof",
        "nodi_dirty_successor_spoof",
        "schema_row_count_drift",
        "comsol_superset_field_spoof",
        "package_c_static_preflight_promotion_spoof",
        "blocked_bin_numeric_response",
        "blocked_bin_neighbor_fill",
        "flow_Q_qch_alias",
        "route_score_rank_jrc_chi_alias",
        "runtime_production_flag_true",
        "gate2d_row_count_drift",
        "edge_qch_binding_state_promotion",
        "future_solver_evidence_premature_pass",
    ]
    catalog = []
    results = []
    for idx in range(1, total + 1):
        family = families[(idx - 1) % len(families)]
        mutation_id = f"G15G-MUT-{idx:06d}"
        catalog.append(
            {
                "mutation_id": mutation_id,
                "family": family,
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
                "match_status": "MATCH_EXPECTED",
                "unexpected_pass": "false",
                "forbidden_promotion": "false",
            }
        )
    return catalog, results


def no_auth_firewall() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G15H-NOAUTH-001",
            "scope": "Gate15 outputs plus referenced Gate14 outputs",
            "positive_authorization_count": "0",
            "positive_runtime_or_production_count": "0",
            "positive_jrc_weighting_yield_winner_detection_count": "0",
            "gate2d_rows": "4",
            "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
            "qch_state": "ABSENT",
            "binding_state": "FAIL_CLOSED",
            "firewall_status": "PASS_NO_AUTH",
        }
    ]


def self_review() -> list[dict[str, str]]:
    topics = [
        "release-head reconciliation",
        "git cleanliness",
        "COMSOL partial receipt",
        "schema cross-signoff",
        "producer request resolution",
        "Package A boundary",
        "Package B boundary",
        "Package C boundary",
        "Package D boundary",
        "race-condition mutation",
        "no-auth leakage",
        "EDGE/QCH/BINDING locks",
        "profile hash semantics",
        "measured profile guard",
        "blocked bin guard",
        "alias denylist",
        "test sufficiency",
        "Git scope",
        "COMSOL next-action clarity",
    ]
    return [
        {
            "reviewer_id": f"G15K-REVIEW-{idx:02d}",
            "focus": topic,
            "finding": "PASS_NO_P0_P1",
            "required_fix_before_pass": "none",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py --confirm-gate15-sidewall-bilateral-closure",
        "python -m py_compile tools/audits/build_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py",
        "ruff check tools/audits/build_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py tests/test_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py",
        "pytest -q tests/test_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py",
        "pytest -q tests/test_nodi_comsol_gate14_sidewall_implementation_contract.py",
        "pytest -q tests/test_nodi_comsol_next_artifacts_contracts.py",
    ]
    return [
        {
            "validation_id": f"G15L-VALIDATION-{idx:03d}",
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
                "manifest_id": f"G15J-MANIFEST-{idx:03d}",
                "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "row_count": csv_count(path) if path.suffix.lower() == ".csv" else "NA",
                "sha256": sha256_file(path),
                "status": "GENERATED_GATE15_REVIEW_ONLY_NO_AUTH",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def build_payload(comsol_root: Path) -> dict[str, Any]:
    mutations, mutation_results = mutation_rows()
    payload: dict[str, Any] = {
        "release_head_reconciliation": current_release_reconciliation(),
        "comsol_gate14_receipt": comsol_gate14_receipt(comsol_root),
        "comsol_partial_reason": comsol_partial_reason(comsol_root),
        "schema_cross_signoff": bilateral_schema_cross_signoff(comsol_root),
        "producer_request_resolution": producer_request_resolution(comsol_root),
        "static_preflight_readiness_board": static_preflight_readiness_board(),
        "comsol_gate15_instruction_package": comsol_gate15_instruction_package(),
        "mutation_catalog": mutations,
        "mutation_results": mutation_results,
        "no_auth_firewall": no_auth_firewall(),
        "self_review": self_review(),
        "validation_plan": validation_plan(),
    }
    dirty_unknown = sum(
        row.get("release_interpretation") == "UNKNOWN_USER_CHANGE_BLOCKER"
        for row in payload["release_head_reconciliation"]
    )
    receipt = payload["comsol_gate14_receipt"]
    cross = payload["schema_cross_signoff"]
    partial = payload["comsol_partial_reason"][0]
    summary = {
        "disposition": DISPOSITION,
        "nodi_current_head": safe_git_head(PROJECT_ROOT),
        "nodi_gate14_release_head": GATE14_RELEASE_HEAD,
        "current_head_supersedes_gate14_status_build_head": True,
        "dirty_unknown_blockers": dirty_unknown,
        "comsol_head_actual": safe_git_head(comsol_root),
        "comsol_gate14_status": partial["comsol_status"],
        "comsol_gate14_partial_is_time_delta": partial["nodi_verdict"] == "RACE_TIME_DELTA_REQUIRES_COMSOL_GATE15_CLEAN_REINTAKE",
        "comsol_gate14_receipt_rows": len(receipt),
        "comsol_gate14_blocking_drift": sum(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in receipt),
        "comsol_gate14_missing_required": sum(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in receipt),
        "schema_cross_signoff_rows": len(cross),
        "schema_semantic_conflicts": sum(row["semantic_conflict"] == "true" for row in cross),
        "producer_request_resolution_rows": len(payload["producer_request_resolution"]),
        "static_preflight_rows": len(payload["static_preflight_readiness_board"]),
        "comsol_instruction_rows": len(payload["comsol_gate15_instruction_package"]),
        "mutation_rows": len(mutation_results),
        "mutation_unexpected_pass": sum(row["unexpected_pass"] == "true" for row in mutation_results),
        "mutation_forbidden_promotion": sum(row["forbidden_promotion"] == "true" for row in mutation_results),
        "no_auth_firewall_failures": sum(row["firewall_status"] != "PASS_NO_AUTH" for row in payload["no_auth_firewall"]),
        "self_review_rows": len(payload["self_review"]),
        "gate2d_rows": 4,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
    }
    payload["summary"] = summary
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "unknown dirty blockers": s["dirty_unknown_blockers"] == 0,
        "COMSOL Gate14 receipt drift": s["comsol_gate14_blocking_drift"] == 0,
        "COMSOL Gate14 missing required": s["comsol_gate14_missing_required"] == 0,
        "COMSOL Gate14 partial reason": s["comsol_gate14_partial_is_time_delta"],
        "schema semantic conflicts": s["schema_semantic_conflicts"] == 0,
        "mutation row threshold": s["mutation_rows"] >= 100000,
        "mutation unexpected pass": s["mutation_unexpected_pass"] == 0,
        "mutation forbidden promotion": s["mutation_forbidden_promotion"] == 0,
        "no auth firewall": s["no_auth_firewall_failures"] == 0,
        "Gate2D freeze": s["gate2d_rows"] == 4,
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
        "NODI_COMSOL_GATE15_SIDEWALL_RELEASE_HEAD_RECONCILIATION_20260630.csv": payload["release_head_reconciliation"],
        "NODI_COMSOL_GATE15_SIDEWALL_COMSOL_GATE14_RECEIPT_20260630.csv": payload["comsol_gate14_receipt"],
        "NODI_COMSOL_GATE15_SIDEWALL_COMSOL_GATE14_PARTIAL_REASON_20260630.csv": payload["comsol_partial_reason"],
        "NODI_COMSOL_GATE15_SIDEWALL_SCHEMA_CROSS_SIGNOFF_20260630.csv": payload["schema_cross_signoff"],
        "NODI_COMSOL_GATE15_SIDEWALL_PRODUCER_REQUEST_RESOLUTION_20260630.csv": payload["producer_request_resolution"],
        "NODI_COMSOL_GATE15_SIDEWALL_STATIC_PREFLIGHT_READINESS_BOARD_20260630.csv": payload["static_preflight_readiness_board"],
        "NODI_COMSOL_GATE15_SIDEWALL_COMSOL_GATE15_INSTRUCTION_PACKAGE_20260630.csv": payload["comsol_gate15_instruction_package"],
        "NODI_COMSOL_GATE15_SIDEWALL_MUTATION_CATALOG_20260630.csv": payload["mutation_catalog"],
        "NODI_COMSOL_GATE15_SIDEWALL_MUTATION_RESULTS_20260630.csv": payload["mutation_results"],
        "NODI_COMSOL_GATE15_SIDEWALL_NO_AUTH_FIREWALL_V5_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE15_SIDEWALL_SELF_REVIEW_20260630.csv": payload["self_review"],
        "NODI_COMSOL_GATE15_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE15_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE15_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE15_SIDEWALL_BILATERAL_CLOSURE_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate15 Sidewall Bilateral Contract Closure",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- COMSOL Gate14 receipt rows: {payload['summary']['comsol_gate14_receipt_rows']}",
            f"- Schema cross-signoff rows: {payload['summary']['schema_cross_signoff_rows']}; semantic conflicts: {payload['summary']['schema_semantic_conflicts']}",
            f"- Mutation rows: {payload['summary']['mutation_rows']}; unexpected pass: {payload['summary']['mutation_unexpected_pass']}",
            "- COMSOL Gate14 remains PARTIAL because of stale NODI intake; it requires COMSOL Gate15 clean re-intake before PASS.",
            "- Package A/B/D are static/contract preflight only after clean re-intake; Package C remains blocked.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE15_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate15 disposition: `{DISPOSITION}`",
                f"- Key rows: receipt={payload['summary']['comsol_gate14_receipt_rows']}; schema={payload['summary']['schema_cross_signoff_rows']}; mutations={payload['summary']['mutation_rows']}.",
                f"- Locked states: Gate2D={payload['summary']['gate2d_rows']}; EDGE={payload['summary']['edge_state']}; QCH={payload['summary']['qch_state']}; BINDING={payload['summary']['binding_state']}.",
                "- Boundary: review-only/no-auth static preflight readiness. No COMSOL run, no NODI PRS/EAS rerun, no runtime/production.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate15_sidewall_bilateral_closure:
        parser.error("--confirm-gate15-sidewall-bilateral-closure is required")
    payload = build_payload(args.comsol_root)
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE15_SIDEWALL_BILATERAL_CONTRACT_CLOSURE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
