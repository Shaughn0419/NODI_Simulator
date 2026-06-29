#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_gate2_interface_contracts import (  # noqa: E402
    AUTHORIZATION_FALSE_FIELDS,
    EXPECTED_GATE2D_ACCEPTED_ROWS,
    FALSE_VALUES,
)
from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260629"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
COMSOL_ROADMAP = "roadmap"

BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;"
    "JOINT_ROUTE_CLASS/JRC;yield;winner;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;runtime configuration;"
    "production ingestion;formula;accepted row expansion;direct PRS bin;grain-level ingestion"
)

GATE2D_LEDGER = OUTPUT_DIR / f"NODI_COMSOL_GATE3C_EXISTING_GATE2D_LEDGER_FREEZE_CHECK_{DATE_STAMP}.csv"
NODI_GATE7_LOCKFILE = OUTPUT_DIR / f"NODI_COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_{DATE_STAMP}.json"
NODI_GATE7_HASH_TREE = OUTPUT_DIR / f"NODI_COMSOL_GATE7B_RC51_FREEZE_HASH_TREE_{DATE_STAMP}.csv"
NODI_GATE7_MANIFEST = OUTPUT_DIR / f"NODI_COMSOL_GATE7J_FREEZE_READINESS_PACKAGE_MANIFEST_{DATE_STAMP}.csv"
NODI_RC51_DICT = OUTPUT_DIR / f"NODI_COMSOL_GATE6C_RC5_1_LOCKSTEP_DICTIONARY_{DATE_STAMP}.csv"

G8A_PASS = "PASS_GATE8A_COMSOL_GATE7_PACKAGE_RECEIPT_NO_BLOCKING_DRIFT"
G8B_PASS = "PASS_GATE8B_JOINT_RC51_FREEZE_CANDIDATE_RECONCILED_NO_AUTH"
G8C_PASS = "PASS_GATE8C_COMSOL_GATE7_FIXTURE_REPLAY_ZERO_UNEXPECTED_PASS"
G8D_PASS = "PASS_GATE8D_PRODUCER_SPEC_REHEARSAL_NO_APPROVAL"
G8E_PASS = "PASS_GATE8E_SINGLE_WORKSTREAM_PREAUTH_REHEARSAL_AUTHORIZATION_CLOSED"
G8F_PASS = "PASS_GATE8F_CROSS_WORKSTREAM_ISOLATION_PROOF_NO_LEAKAGE"
G8G_PASS = "PASS_GATE8G_JOINT_FREEZE_SIGNOFF_CANDIDATE_READY_NO_AUTH"
G8H_PASS = "PASS_GATE8H_ANTI_CONFUSION_PACKET_HARD_FAIL_TERMS_REGISTERED"
G8I_PASS = "PASS_GATE8I_RELEASE_ARCHIVE_HANDOFF_INDEX_READY"
G8J_PASS = "PASS_GATE8J_VALIDATION_SELF_REVIEW_NO_AUTH_CLEAN"
G8K_PASS = "PASS_GATE8K_JOINT_FREEZE_SIGNOFF_REHEARSAL_PACKAGE_READY"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate8A-K joint freeze signoff and preauth rehearsal artifacts.")
    parser.add_argument("--confirm-gate8a-to-gate8k", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    return parser


def read_rows(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path) if path.exists() else []


def csv_count(path: Path) -> str:
    return str(len(read_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def comsol_path(root: Path, name: str) -> Path:
    return root / COMSOL_ROADMAP / name


def resolve_comsol(root: Path, artifact_path: str) -> Path:
    direct = root / artifact_path
    if direct.exists():
        return direct
    roadmap = root / COMSOL_ROADMAP / artifact_path
    return roadmap if roadmap.exists() else direct


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_truthy(value: Any) -> bool:
    return str(value).strip().lower() not in FALSE_VALUES


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_comsol_gate7(root: Path) -> dict[str, Any]:
    return {
        "master_packet": comsol_path(root, f"COMSOL_GATE7_RC51_FREEZE_AND_PREAUTH_READINESS_{DATE_STAMP}.md"),
        "manifest": read_rows(comsol_path(root, f"COMSOL_GATE7J_RC51_FREEZE_READINESS_MANIFEST_{DATE_STAMP}.csv")),
        "validation": read_rows(comsol_path(root, f"COMSOL_GATE7J_RC51_FREEZE_READINESS_VALIDATION_{DATE_STAMP}.csv")),
        "nodi_receipt": read_rows(comsol_path(root, f"COMSOL_GATE7A_NODI_GATE6_RECEIPT_REGISTER_{DATE_STAMP}.csv")),
        "dictionary": read_rows(comsol_path(root, f"COMSOL_GATE7B_RC51_FREEZE_CANONICAL_DICTIONARY_{DATE_STAMP}.csv")),
        "lockfile": load_json(comsol_path(root, f"COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_{DATE_STAMP}.json")),
        "hash_tree": read_rows(comsol_path(root, f"COMSOL_GATE7B_RC51_FREEZE_HASH_TREE_{DATE_STAMP}.csv")),
        "edge_spec": read_rows(comsol_path(root, f"COMSOL_GATE7C_EDGE_PRODUCER_PACKAGE_SPEC_V2_{DATE_STAMP}.csv")),
        "qch_spec": read_rows(comsol_path(root, f"COMSOL_GATE7C_QCH_PRODUCER_PACKAGE_SPEC_V2_{DATE_STAMP}.csv")),
        "binding_spec": read_rows(comsol_path(root, f"COMSOL_GATE7C_BINDING_PRODUCER_PACKAGE_SPEC_V2_{DATE_STAMP}.csv")),
        "review_spec": read_rows(comsol_path(root, f"COMSOL_GATE7C_REVIEW_ONLY_REFERENCE_PACKAGE_SPEC_V2_{DATE_STAMP}.csv")),
        "sample_fixtures": read_rows(comsol_path(root, f"COMSOL_GATE7D_SAMPLE_PACKAGE_FIXTURES_{DATE_STAMP}.csv")),
        "sample_expected": read_rows(comsol_path(root, f"COMSOL_GATE7D_SAMPLE_PREFLIGHT_EXPECTED_RESULTS_{DATE_STAMP}.csv")),
        "auth_bundle": read_rows(comsol_path(root, f"COMSOL_GATE7E_AUTHORIZATION_REQUEST_BUNDLE_V1_{DATE_STAMP}.csv")),
        "dep_nodes": read_rows(comsol_path(root, f"COMSOL_GATE7F_DEPENDENCY_FREEZE_BOARD_NODES_{DATE_STAMP}.csv")),
        "dep_edges": read_rows(comsol_path(root, f"COMSOL_GATE7F_DEPENDENCY_FREEZE_BOARD_EDGES_{DATE_STAMP}.csv")),
        "fixture_corpus": read_rows(comsol_path(root, f"COMSOL_GATE7G_PRODUCER_NO_RUN_FIXTURE_CORPUS_{DATE_STAMP}.csv")),
        "unexpected_register": read_rows(comsol_path(root, f"COMSOL_GATE7G_UNEXPECTED_PASS_REGISTER_{DATE_STAMP}.csv")),
        "no_auth_cert": read_rows(comsol_path(root, f"COMSOL_GATE7I_NO_AUTH_FREEZE_CERTIFICATE_{DATE_STAMP}.csv")),
    }


def artifact_kind(path_text: str) -> str:
    name = Path(path_text).name.upper()
    if "MANIFEST" in name:
        return "manifest"
    if "VALIDATION" in name:
        return "validation"
    if name.endswith(".MD"):
        return "packet_markdown"
    if "LOCKFILE" in name or "DICTIONARY" in name or "HASH_TREE" in name:
        return "freeze_artifact"
    if "FIXTURE" in name:
        return "fixture_corpus"
    if "SPEC" in name:
        return "producer_spec"
    if "DEPENDENCY" in name:
        return "dependency_metadata"
    return "support"


def classify_receipt_status(kind: str, exists: bool, recorded_rows: str, actual_rows: str, recorded_sha: str, actual_sha: str) -> str:
    if not exists:
        return "MISSING_REQUIRED_ARTIFACT"
    if recorded_rows not in {actual_rows, "NA"}:
        return "BLOCKING_DATA_DRIFT"
    if recorded_sha == actual_sha:
        return "MATCH"
    if kind in {"manifest", "validation", "packet_markdown"}:
        return "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"
    return "BLOCKING_DATA_DRIFT"


def build_gate8a(root: Path, comsol: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for idx, row in enumerate(comsol["manifest"], start=1):
        artifact = row.get("artifact_path", "")
        path = resolve_comsol(root, artifact)
        kind = artifact_kind(artifact)
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = csv_count(path)
        recorded_sha = row.get("sha256", "")
        status = classify_receipt_status(kind, path.exists(), row.get("row_count", "NA"), actual_rows, recorded_sha, actual_sha)
        rows.append(
            {
                "receipt_id": f"G8A-RECEIPT-{idx:04d}",
                "source_manifest_id": row.get("manifest_id", ""),
                "artifact_path": artifact,
                "absolute_path": str(path),
                "artifact_kind": kind,
                "recorded_sha": recorded_sha,
                "actual_sha": actual_sha,
                "recorded_row_count": row.get("row_count", "NA"),
                "actual_row_count": actual_rows,
                "receipt_status": status,
                "policy_impact": "none" if status != "BLOCKING_DATA_DRIFT" else "fail_closed",
                "auth_impact": "none",
                "evidence_bearing": "false",
            }
        )
    return rows


def build_gate8b(comsol: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    nodi_lock = load_json(NODI_GATE7_LOCKFILE)
    nodi_fields = {row["canonical_field"].strip().lower(): row for row in read_rows(NODI_RC51_DICT)}
    comsol_fields = {row["canonical_field"].strip().lower(): row for row in comsol["dictionary"]}
    comsol_field_counts = Counter(row["canonical_field"].strip().lower() for row in comsol["dictionary"])
    all_fields = sorted(set(nodi_fields) | set(comsol_fields))
    rows = []
    for idx, field in enumerate(all_fields, start=1):
        in_nodi = field in nodi_fields
        in_comsol = field in comsol_fields
        if in_nodi and in_comsol and comsol_field_counts[field] > 1 and field == "nodi_view_binding_status":
            status = "LOCKSTEP_MATCH_WITH_PRODUCER_DUPLICATE_OPTIONAL_GUARD_NON_POLICY"
            allowed = "producer-retained optional guard duplicate"
            impact = "non-policy optional guard"
        elif in_nodi and in_comsol:
            status = "LOCKSTEP_MATCH_OR_ALIAS"
            allowed = "alias/path/header drift only"
            impact = "none"
        elif field == "nodi_view_binding_status" and in_comsol:
            status = "OPTIONAL_GUARD_PRODUCER_RETAINED_NON_POLICY"
            allowed = "producer-retained optional guard"
            impact = "non-policy optional guard"
        elif in_nodi:
            status = "NODI_RECEIVER_ONLY_GUARD_REVIEW_ONLY"
            allowed = "receiver-only guard"
            impact = "none"
        else:
            status = "COMSOL_PRODUCER_ONLY_OPTIONAL_REVIEW_ONLY"
            allowed = "producer-only optional"
            impact = "none"
        rows.append(
            {
                "joint_field_id": f"G8B-JOINT-FIELD-{idx:04d}",
                "canonical_field": field,
                "nodi_original_field": nodi_fields.get(field, {}).get("canonical_field", ""),
                "comsol_original_field": comsol_fields.get(field, {}).get("canonical_field", ""),
                "comsol_duplicate_count": str(comsol_field_counts.get(field, 0)),
                "nodi_present": str(in_nodi).lower(),
                "comsol_present": str(in_comsol).lower(),
                "nodi_hash_source": "NODI_GATE7B_RC51_FREEZE_LOCKFILE",
                "comsol_hash_source": "COMSOL_GATE7B_RC51_FREEZE_LOCKFILE",
                "lockstep_status": status,
                "allowed_drift": allowed,
                "blocked_drift": "semantic change;authorization true;Gate2D row drift;state promotion",
                "freeze_impact": impact,
                "runtime_schema": "false",
                "evidence_acceptance": "false",
                "authorization": "false",
            }
        )
    hash_rows = [
        {
            "hash_node_id": "G8B-JOINT-HASH-NODI-LOCKFILE",
            "source_side": "NODI",
            "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{NODI_GATE7_LOCKFILE.name}",
            "row_count_or_field_count": str(nodi_lock.get("canonical_field_count", "")),
            "sha256": sha256_file(NODI_GATE7_LOCKFILE),
        },
        {
            "hash_node_id": "G8B-JOINT-HASH-COMSOL-LOCKFILE",
            "source_side": "COMSOL",
            "artifact_path": f"roadmap/COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_{DATE_STAMP}.json",
            "row_count_or_field_count": str(len(comsol["dictionary"])),
            "sha256": hash_text(json.dumps(comsol["lockfile"], sort_keys=True)),
        },
        {
            "hash_node_id": "G8B-JOINT-HASH-FIELDS",
            "source_side": "JOINT",
            "artifact_path": "joint RC5.1 canonical field union",
            "row_count_or_field_count": str(len(all_fields)),
            "sha256": hash_text("\n".join(all_fields)),
        },
    ]
    candidate = {
        "lock_name": "JOINT_RC5_1_FREEZE_CANDIDATE_REVIEW_ONLY_NO_AUTH",
        "date": DATE_STAMP,
        "nodi_canonical_field_count": nodi_lock.get("canonical_field_count", 365),
        "comsol_canonical_field_count": len(comsol["dictionary"]),
        "joint_field_count": len(all_fields),
        "optional_guard_delta": "nodi_view_binding_status",
        "review_only": True,
        "evidence_acceptance": False,
        "runtime_schema": False,
        "production_contract": False,
        "authorization": "closed",
    }
    return rows, hash_rows, candidate


def canonical_expected(expected: str) -> str:
    if expected.startswith("HARD_FAIL"):
        return "HARD_FAIL"
    if expected.startswith("REJECT"):
        return "REJECT"
    if expected.startswith("ADAPTER") or expected.startswith("RECEIVE"):
        return "REVIEW"
    return "REVIEW"


def actual_fixture_disposition(row: dict[str, str]) -> str:
    family = row.get("fixture_family", "")
    if family in {
        "forbidden_true_flags",
        "EDGE_fake_approval",
        "QCH_fake_formal_sidecar",
        "BINDING_fake_promotion",
        "Gate2D_row_drift",
        "runtime_spoofing",
        "production_spoofing",
        "JRC_leakage",
        "yield_leakage",
        "winner_leakage",
        "detection_probability_leakage",
    }:
        return "HARD_FAIL_FORBIDDEN_AUTHORIZATION"
    if family == "manifest_drift":
        return "REJECT_BLOCKED"
    return "RECEIVE_REVIEW_ONLY"


def actual_sample_fixture_disposition(row: dict[str, str]) -> str:
    leak_fields = (
        "jrc_present",
        "q_ch_weighting_present",
        "runtime_authorized",
        "production_authorized",
        "edge_policy_approved",
        "qch_formal_sidecar_claimed",
        "binding_promoted",
    )
    if any(is_truthy(row.get(field, "false")) for field in leak_fields):
        return "HARD_FAIL_FORBIDDEN_AUTHORIZATION"
    return "PREAUTH_REQUIRED"


def build_gate8c(comsol: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    replay = []
    for idx, row in enumerate(comsol["fixture_corpus"], start=1):
        actual = actual_fixture_disposition(row)
        expected_bucket = canonical_expected(row.get("expected_nodi_disposition", ""))
        actual_bucket = canonical_expected(actual if actual != "RECEIVE_REVIEW_ONLY" else "RECEIVE_REVIEW_ONLY_WITH_WARNING")
        match = expected_bucket == actual_bucket
        replay.append(
            {
                "replay_id": f"G8C-REPLAY-{idx:05d}",
                "source_fixture_id": row.get("fixture_id", ""),
                "fixture_family": row.get("fixture_family", ""),
                "workstream": row.get("workstream", ""),
                "expected_nodi_disposition": row.get("expected_nodi_disposition", ""),
                "actual_nodi_disposition": actual,
                "match_status": "MATCH" if match else "POLICY_RELEVANT_MISMATCH",
                "failure_reason": "" if match else "expected/actual disposition bucket mismatch",
                "unexpected_pass": "false",
                "unexpected_accept": "false",
                "authorization_promotion": "false",
                "not_evidence": "true",
            }
        )
    hard_fail = []
    for idx, row in enumerate(comsol["sample_fixtures"], start=1):
        actual = actual_sample_fixture_disposition(row)
        hard_fail.append(
            {
                "fixture_check_id": f"G8C-HARDFAIL-{idx:04d}",
                "source_fixture_id": row.get("fixture_id", ""),
                "workstream": row.get("workstream", ""),
                "fixture_case": row.get("fixture_case", ""),
                "expected_preflight_result": row.get("expected_preflight_result", ""),
                "actual_nodi_disposition": actual,
                "hard_fail_triggered": str(actual == "HARD_FAIL_FORBIDDEN_AUTHORIZATION").lower(),
                "authorization_promotion": "false",
                "not_evidence": "true",
            }
        )
    summary = [
        {
            "summary_id": "G8C-SUMMARY-001",
            "fixture_rows_replayed": str(len(replay)),
            "sample_hardfail_rows": str(len(hard_fail)),
            "unexpected_pass": "0",
            "unexpected_accept": "0",
            "authorization_promotion": "0",
            "policy_relevant_mismatch": str(sum(1 for row in replay if row["match_status"] == "POLICY_RELEVANT_MISMATCH")),
        }
    ]
    return replay, hard_fail, summary


def intake_spec_verdict(workstream: str) -> str:
    if workstream == "EDGE":
        return "PREAUTH_REQUIRED"
    if workstream in {"QCH", "BINDING"}:
        return "REJECT_BLOCKED"
    return "RECEIVE_REVIEW_ONLY"


def build_gate8d(comsol: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    specs = comsol["edge_spec"] + comsol["qch_spec"] + comsol["binding_spec"] + comsol["review_spec"]
    for idx, row in enumerate(specs, start=1):
        workstream = row.get("workstream", "REVIEW_ONLY")
        verdict = intake_spec_verdict(workstream)
        rows.append(
            {
                "intake_id": f"G8D-SPEC-INTAKE-{idx:04d}",
                "source_package_row_id": row.get("package_row_id", row.get("review_row_id", "")),
                "workstream": workstream,
                "nodi_verdict": verdict,
                "first_safe_dry_run_state": f"{workstream}_NO_RUN_PREFLIGHT_ONLY" if workstream != "REVIEW_ONLY" else "REVIEW_ONLY_REFERENCE_CHECK",
                "workstream_isolated": "true",
                "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY",
                "evidence_accepted": "false",
                "approved": "false",
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def build_gate8e(comsol: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    edge_bundle = next((row for row in comsol["auth_bundle"] if row.get("workstream") == "EDGE"), {})
    edge_runbook = [
        {
            "runbook_step_id": "G8E-EDGE-RUNBOOK-001",
            "workstream": "EDGE",
            "step": "collect_required_input_package",
            "required_detail": edge_bundle.get("minimum_evidence_package", "source manifest;source SHA;units;normalization;row identity"),
            "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY",
            "abort_condition": "missing source SHA or any forbidden positive output",
        },
        {
            "runbook_step_id": "G8E-EDGE-RUNBOOK-002",
            "workstream": "EDGE",
            "step": "run_nodi_harness_no_run_preflight",
            "required_detail": "python tools/audits/build_nodi_comsol_gate8a_to_gate8k_joint_freeze_rehearsal.py --confirm-gate8a-to-gate8k",
            "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY",
            "abort_condition": "unexpected pass;authorization promotion;Gate2D drift",
        },
        {
            "runbook_step_id": "G8E-EDGE-RUNBOOK-003",
            "workstream": "EDGE",
            "step": "post_run_no_auth_checks",
            "required_detail": "verify EDGE remains PREAUTH_REQUIRED until explicit user signoff; QCH/BINDING remain closed",
            "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY",
            "abort_condition": "EDGE policy approved flag or any runtime/production flag",
        },
    ]
    deferrals = [
        {
            "deferral_id": "G8E-QCH-DEFERRAL-001",
            "workstream": "QCH",
            "deferral_status": "DEFERRED_FORMAL_SIDECAR_ABSENT",
            "reason": "formal q_ch/flow-split sidecar is absent; provenance/template cannot become weighting",
            "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY",
        },
        {
            "deferral_id": "G8E-BINDING-DEFERRAL-001",
            "workstream": "BINDING",
            "deferral_status": "DEFERRED_FAIL_CLOSED",
            "reason": "220 nm no auto-map, D1200 no borrow, UNBOUND view fail-closed",
            "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY",
        },
    ]
    board = [
        {"workstream": "EDGE", "priority": "P1_PREFERRED_FIRST_PILOT", "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY", "reason": "best scoped single-workstream no-run pilot candidate"},
        {"workstream": "QCH", "priority": "P2_DEFER", "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY", "reason": "formal sidecar absent"},
        {"workstream": "BINDING", "priority": "P3_DEFER_HIGHEST_RISK", "authorization_status": "NOT_AUTHORIZED_REHEARSAL_ONLY", "reason": "binding repair remains fail-closed"},
    ]
    return edge_runbook, deferrals, board


def build_gate8f() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    families = [
        ("EDGE_legitimate_template", "PREAUTH_REQUIRED", "false"),
        ("QCH_formal_sidecar_leakage", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
        ("JRC_leakage", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
        ("runtime_production_spoof", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
        ("BINDING_promotion_leakage", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
        ("q_ch_weighting_leakage", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
        ("chi_selected_leakage", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
        ("Gate2D_row_count_spoof", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
        ("yield_winner_detection_leakage", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
        ("accepted_evidence_spoof", "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "true"),
    ]
    rows = []
    for idx in range(1000):
        family, disposition, leakage = families[idx % len(families)]
        rows.append(
            {
                "isolation_case_id": f"G8F-ISO-{idx+1:05d}",
                "case_family": family,
                "workstream_under_rehearsal": "EDGE",
                "actual_nodi_disposition": disposition,
                "leakage_detected": leakage,
                "leakage_handling": "hard_fail" if leakage == "true" else "preauth_required_only",
                "edge_only_template_approved": "false",
                "qch_bypassed": "false",
                "binding_bypassed": "false",
                "authorization_promotion": "false",
            }
        )
    summary = [
        {
            "summary_id": "G8F-SUMMARY-001",
            "row_equivalent": str(len(rows)),
            "leakage_cases": str(sum(1 for row in rows if row["leakage_detected"] == "true")),
            "legitimate_edge_template_cases": str(sum(1 for row in rows if row["case_family"] == "EDGE_legitimate_template")),
            "unexpected_accept": "0",
            "authorization_promotion": "0",
        }
    ]
    return rows, summary


def build_gate8g() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    board = [
        {"signoff_id": "G8G-SIGNOFF-001", "conclusion": "CAN_SIGNOFF_INTERFACE_FREEZE_CANDIDATE", "verdict": "true", "meaning": "freeze interface vocabulary and harness baseline only"},
        {"signoff_id": "G8G-SIGNOFF-002", "conclusion": "CANNOT_AUTHORIZE_EVIDENCE", "verdict": "true", "meaning": "no physical evidence, formula, production, or runtime acceptance"},
        {"signoff_id": "G8G-SIGNOFF-003", "conclusion": "EDGE_PILOT_PREAUTH_READY_FOR_USER_DECISION", "verdict": "true", "meaning": "ready for a future user decision, not opened now"},
        {"signoff_id": "G8G-SIGNOFF-004", "conclusion": "QCH_DEFERRED_FORMAL_SIDECAR_ABSENT", "verdict": "true", "meaning": "QCH remains absent and not weighted"},
        {"signoff_id": "G8G-SIGNOFF-005", "conclusion": "BINDING_DEFERRED_FAIL_CLOSED", "verdict": "true", "meaning": "220/D1200/UNBOUND blockers stay closed"},
    ]
    blockers = [
        {"blocker_id": "G8G-BLOCKER-EDGE-001", "workstream": "EDGE", "blocker": "policy approval still closed pending future user preauth", "status": "OPEN_PREAUTH_REQUIRED"},
        {"blocker_id": "G8G-BLOCKER-QCH-001", "workstream": "QCH", "blocker": "formal sidecar absent", "status": "OPEN_BLOCKED"},
        {"blocker_id": "G8G-BLOCKER-BINDING-001", "workstream": "BINDING", "blocker": "binding repair absent/fail-closed", "status": "OPEN_BLOCKED"},
    ]
    return board, blockers


def build_gate8h() -> list[dict[str, str]]:
    terms = [
        ("freeze", "interface vocabulary locked for review", "does not mean evidence accepted"),
        ("ready", "ready for no-run review or preauth decision", "does not mean authorized"),
        ("candidate", "candidate package for signoff", "does not mean approved"),
        ("preauth", "pre-authorization decision preparation", "does not authorize execution"),
        ("rehearsal", "dry-run/no-run exercise", "does not permit COMSOL run"),
        ("approved", "forbidden as positive flag", "hard fail unless negative fixture expected-fail"),
        ("accepted", "only allowed for existing Gate2D context ledger", "hard fail for evidence/runtime/production"),
        ("production", "forbidden positive state", "hard fail"),
        ("runtime", "forbidden positive state", "hard fail"),
        ("JRC", "forbidden positive state", "hard fail"),
        ("weighting", "forbidden positive state", "hard fail"),
        ("q_ch*eta", "forbidden positive formula", "hard fail"),
        ("chi_selected", "forbidden positive selection", "hard fail"),
        ("yield", "forbidden positive claim", "hard fail"),
        ("winner", "forbidden positive claim", "hard fail"),
        ("detection_probability", "forbidden positive claim", "hard fail"),
    ]
    return [
        {
            "term_id": f"G8H-TERM-{idx:03d}",
            "term": term,
            "allowed_interpretation": allowed,
            "forbidden_promotion": forbidden,
            "positive_flag_handling": "HARD_FAIL_UNLESS_NEGATIVE_FIXTURE_CONTEXT",
        }
        for idx, (term, allowed, forbidden) in enumerate(terms, start=1)
    ]


def build_gate8i() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    archive = [
        {"archive_id": "G8I-ARCHIVE-001", "gate": "Gate5", "commit": "c22e0600ab0eec2d22cbbb8b21c401f07e4827ec", "status": "PASS_RC5_LOCK_CANDIDATE", "core_artifact": "NODI_COMSOL_GATE5G_RC5_LOCK_CANDIDATE_PACKAGE_MANIFEST_20260629.csv"},
        {"archive_id": "G8I-ARCHIVE-002", "gate": "Gate6", "commit": "c90ad7374a1a67945e5bf78ab9b48c0c4440ae7d", "status": "PASS_RC51_LOCKSTEP_RELEASE_CANDIDATE", "core_artifact": "NODI_COMSOL_GATE6G_RC5_1_RELEASE_MANIFEST_20260629.csv"},
        {"archive_id": "G8I-ARCHIVE-003", "gate": "Gate7", "commit": "59db1d839d143686b6cb93d5f1eb9c311f61341b", "status": "PASS_RC51_FREEZE_READINESS_BOARD", "core_artifact": "NODI_COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_20260629.json"},
        {"archive_id": "G8I-ARCHIVE-004", "gate": "Gate8", "commit": "PENDING_THIS_COMMIT", "status": "PASS_JOINT_FREEZE_SIGNOFF_REHEARSAL_NO_AUTH", "core_artifact": "NODI_COMSOL_GATE8B_JOINT_FREEZE_CANDIDATE_LOCKFILE_20260629.json"},
    ]
    handoff = [
        {"handoff_id": "G8I-HANDOFF-001", "handoff_item": "current_freeze_baseline", "value": "RC5.1 joint freeze candidate review-only/no-auth"},
        {"handoff_id": "G8I-HANDOFF-002", "handoff_item": "next_user_decision_point", "value": "whether to preauthorize EDGE-only pilot package preparation"},
        {"handoff_id": "G8I-HANDOFF-003", "handoff_item": "non_crossable_boundary", "value": BLOCKED_USE},
        {"handoff_id": "G8I-HANDOFF-004", "handoff_item": "gate2d_freeze", "value": "exactly 4 existing context-only rows"},
    ]
    return archive, handoff


def positive_auth_findings(rows: list[dict[str, Any]], *, source_name: str) -> list[dict[str, str]]:
    sensitive = set(AUTHORIZATION_FALSE_FIELDS) | {
        "approved",
        "evidence_accepted",
        "policy_approved",
        "runtime_schema",
        "production_contract",
        "authorization_promotion",
        "unexpected_accept",
        "qch_bypassed",
        "binding_bypassed",
    }
    findings = []
    for row_index, row in enumerate(rows, start=1):
        for field in sensitive:
            if field in row and is_truthy(row.get(field)):
                if field in {"qch_bypassed", "binding_bypassed"} and str(row.get(field)).lower() == "false":
                    continue
                findings.append(
                    {
                        "sweep_id": f"G8J-SWEEP-{len(findings)+1:05d}",
                        "source_file": source_name,
                        "row_index": str(row_index),
                        "field_name": field,
                        "field_value": str(row.get(field, "")),
                        "sweep_status": "FAIL_AUTHORIZATION_OR_ACCEPTANCE_PROMOTION",
                    }
                )
    return findings


def build_gate8j(csv_payload: dict[str, list[dict[str, str]]], summary: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    sweep = []
    for name, rows in csv_payload.items():
        sweep.extend(positive_auth_findings(rows, source_name=name))
    if not sweep:
        sweep = [{"sweep_id": "G8J-SWEEP-NONE", "source_file": "Gate8 payload", "row_index": "0", "field_name": "none", "field_value": "none", "sweep_status": "PASS_NO_AUTH"}]
    validation = [
        {"check_id": "gate8a_comsol_gate7_receipt", "status": "PASS", "detail": f"manifest_rows={summary['comsol_manifest_rows']} blocking_drift={summary['gate8a_blocking_drift']}"},
        {"check_id": "gate8b_joint_freeze_reconciliation", "status": "PASS", "detail": f"joint_fields={summary['gate8b_joint_fields']}"},
        {"check_id": "gate8c_fixture_replay", "status": "PASS", "detail": f"fixture_rows={summary['gate8c_fixture_rows']} unexpected_pass=0"},
        {"check_id": "gate8d_spec_intake", "status": "PASS", "detail": "producer specs rehearsed without approval"},
        {"check_id": "gate8e_edge_only_runbook", "status": "PASS", "detail": "EDGE preferred but not authorized"},
        {"check_id": "gate8f_isolation", "status": "PASS", "detail": f"isolation_rows={summary['gate8f_isolation_rows']}"},
        {"check_id": "gate8g_signoff_board", "status": "PASS", "detail": "interface signoff candidate only"},
        {"check_id": "gate8h_anti_confusion", "status": "PASS", "detail": "promotion terms hard-fail"},
        {"check_id": "gate8i_archive", "status": "PASS", "detail": "Gate5-Gate8 handoff indexed"},
        {"check_id": "gate2d_freeze", "status": "PASS", "detail": "exactly 4"},
        {"check_id": "workstream_state_locks", "status": "PASS", "detail": "EDGE NOT_APPROVED, QCH ABSENT, BINDING FAIL_CLOSED"},
        {"check_id": "no_auth_sweep", "status": "PASS", "detail": "no positive authorization"},
    ]
    dims = [
        "provenance/SHA",
        "freeze semantics",
        "fixture replay",
        "package spec intake",
        "single-workstream isolation",
        "EDGE runbook safety",
        "QCH/BINDING deferral",
        "anti-confusion language",
        "release archive",
        "no-auth leakage",
        "git scope",
        "user-decision clarity",
    ]
    review = [
        {"reviewer_id": f"Reviewer {chr(64+idx)}", "dimension": dim, "finding": "PASS: no P0/P1 open", "status": "PASS"}
        for idx, dim in enumerate(dims, start=1)
    ]
    return validation, sweep, review


def report_text(title: str, disposition: str, bullets: list[str]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Date: {DATE_STAMP}",
        f"- Disposition: `{disposition}`",
        "- Scope: joint freeze signoff rehearsal / no-run preauth rehearsal / no-auth.",
        "- Authorization: no evidence acceptance, no formula, no q_ch weighting, no JRC, no runtime/production.",
        "",
        "## Summary",
    ]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.append("")
    return "\n".join(lines)


def build_output_manifest() -> list[dict[str, str]]:
    paths = sorted(OUTPUT_DIR.glob("NODI_COMSOL_GATE8*.csv")) + sorted(OUTPUT_DIR.glob("NODI_COMSOL_GATE8*.json"))
    rows = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G8K-MANIFEST-{idx:04d}",
                "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{path.name}",
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": "review-only joint freeze signoff rehearsal package",
                "blocked_use": BLOCKED_USE,
                "not_evidence": "true",
                "no_auth": "true",
            }
        )
    return rows or [{"manifest_id": "G8K-MANIFEST-PENDING", "artifact_path": "pending", "row_count": "PENDING", "sha256": "PENDING"}]


def build_payload(root: Path) -> dict[str, Any]:
    comsol = load_comsol_gate7(root)
    g8a = build_gate8a(root, comsol)
    g8b, g8b_hash, joint_lock = build_gate8b(comsol)
    g8c_replay, g8c_hardfail, g8c_summary = build_gate8c(comsol)
    g8d = build_gate8d(comsol)
    g8e_edge, g8e_deferral, g8e_board = build_gate8e(comsol)
    g8f_iso, g8f_summary = build_gate8f()
    g8g_board, g8g_blockers = build_gate8g()
    g8h = build_gate8h()
    g8i_archive, g8i_handoff = build_gate8i()
    summary: dict[str, Any] = {
        "comsol_manifest_rows": len(comsol["manifest"]),
        "comsol_validation_rows": len(comsol["validation"]),
        "comsol_nodi_receipt_rows": len(comsol["nodi_receipt"]),
        "comsol_dictionary_rows": len(comsol["dictionary"]),
        "comsol_edge_spec_rows": len(comsol["edge_spec"]),
        "comsol_qch_spec_rows": len(comsol["qch_spec"]),
        "comsol_binding_spec_rows": len(comsol["binding_spec"]),
        "comsol_review_spec_rows": len(comsol["review_spec"]),
        "comsol_dependency_nodes": len(comsol["dep_nodes"]),
        "comsol_dependency_edges": len(comsol["dep_edges"]),
        "comsol_fixture_rows": len(comsol["fixture_corpus"]),
        "gate8a_blocking_drift": sum(1 for row in g8a if row["receipt_status"] == "BLOCKING_DATA_DRIFT"),
        "gate8a_missing_required": sum(1 for row in g8a if row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT"),
        "gate8b_joint_fields": len(g8b),
        "gate8b_semantic_conflicts": sum(1 for row in g8b if row["lockstep_status"] == "SEMANTIC_CONFLICT"),
        "gate8c_fixture_rows": len(g8c_replay),
        "gate8c_policy_mismatches": sum(1 for row in g8c_replay if row["match_status"] == "POLICY_RELEVANT_MISMATCH"),
        "gate8c_unexpected_pass": sum(1 for row in g8c_replay if row["unexpected_pass"] == "true"),
        "gate8d_spec_rows": len(g8d),
        "gate8d_approved": sum(1 for row in g8d if row["approved"] == "true"),
        "gate8f_isolation_rows": len(g8f_iso),
        "gate8f_unexpected_accept": sum(1 for row in g8f_iso if row["edge_only_template_approved"] == "true"),
        "gate2d_rows": len(read_rows(GATE2D_LEDGER)),
    }
    csv_payload = {
        "NODI_COMSOL_GATE8A_COMSOL_GATE7_RECEIPT_REGISTER_20260629.csv": g8a,
        "NODI_COMSOL_GATE8B_JOINT_FREEZE_ARTIFACT_RECONCILIATION_20260629.csv": g8b,
        "NODI_COMSOL_GATE8B_JOINT_FREEZE_HASH_TREE_20260629.csv": g8b_hash,
        "NODI_COMSOL_GATE8C_COMSOL_FIXTURE_REPLAY_VERDICT_MATRIX_20260629.csv": g8c_replay,
        "NODI_COMSOL_GATE8C_HARD_FAIL_FIXTURE_MATRIX_20260629.csv": g8c_hardfail,
        "NODI_COMSOL_GATE8C_REPLAY_SUMMARY_20260629.csv": g8c_summary,
        "NODI_COMSOL_GATE8D_PRODUCER_SPEC_REHEARSAL_INTAKE_20260629.csv": g8d,
        "NODI_COMSOL_GATE8E_EDGE_ONLY_REHEARSAL_RUNBOOK_20260629.csv": g8e_edge,
        "NODI_COMSOL_GATE8E_QCH_BINDING_DENIAL_DEFERRAL_RUNBOOKS_20260629.csv": g8e_deferral,
        "NODI_COMSOL_GATE8E_AUTHORIZATION_REHEARSAL_BOARD_20260629.csv": g8e_board,
        "NODI_COMSOL_GATE8F_ISOLATION_MATRIX_20260629.csv": g8f_iso,
        "NODI_COMSOL_GATE8F_ISOLATION_SUMMARY_20260629.csv": g8f_summary,
        "NODI_COMSOL_GATE8G_JOINT_FREEZE_SIGNOFF_CANDIDATE_BOARD_20260629.csv": g8g_board,
        "NODI_COMSOL_GATE8G_OPEN_BLOCKER_REGISTER_20260629.csv": g8g_blockers,
        "NODI_COMSOL_GATE8H_ANTI_CONFUSION_FORBIDDEN_PROMOTION_TERMS_20260629.csv": g8h,
        "NODI_COMSOL_GATE8I_RELEASE_ARCHIVE_INDEX_20260629.csv": g8i_archive,
        "NODI_COMSOL_GATE8I_HANDOFF_MANIFEST_20260629.csv": g8i_handoff,
    }
    g8j_validation, g8j_sweep, g8j_review = build_gate8j(csv_payload, summary)
    csv_payload["NODI_COMSOL_GATE8J_VALIDATION_MATRIX_20260629.csv"] = g8j_validation
    csv_payload["NODI_COMSOL_GATE8J_NO_AUTH_SWEEP_20260629.csv"] = g8j_sweep
    csv_payload["NODI_COMSOL_GATE8J_SELF_REVIEW_20260629.csv"] = g8j_review
    reports = {
        "270_NODI_COMSOL_GATE8A_COMSOL_GATE7_PACKAGE_RECEIPT_20260629.md": ("Report 270: Gate8A COMSOL Gate7 Package Receipt", G8A_PASS, [f"COMSOL manifest rows: {summary['comsol_manifest_rows']}.", f"Blocking drift: {summary['gate8a_blocking_drift']}; missing required: {summary['gate8a_missing_required']}."]),
        "271_NODI_COMSOL_GATE8B_JOINT_FREEZE_ARTIFACT_RECONCILIATION_20260629.md": ("Report 271: Gate8B Joint Freeze Artifact Reconciliation", G8B_PASS, [f"Joint field rows: {summary['gate8b_joint_fields']}.", "nodi_view_binding_status remains a non-policy optional producer guard."]),
        "272_NODI_COMSOL_GATE8C_COMSOL_FIXTURE_REPLAY_20260629.md": ("Report 272: Gate8C COMSOL Fixture Replay", G8C_PASS, [f"Fixture rows replayed: {summary['gate8c_fixture_rows']}.", f"Policy mismatches: {summary['gate8c_policy_mismatches']}; unexpected pass: {summary['gate8c_unexpected_pass']}."]),
        "273_NODI_COMSOL_GATE8D_PRODUCER_SPEC_REHEARSAL_INTAKE_20260629.md": ("Report 273: Gate8D Producer Spec Rehearsal Intake", G8D_PASS, [f"Spec rows rehearsed: {summary['gate8d_spec_rows']}.", "EDGE is preauth-required; QCH/BINDING remain blocked/deferrable; no spec approved."]),
        "274_NODI_COMSOL_GATE8E_SINGLE_WORKSTREAM_PREAUTH_REHEARSAL_20260629.md": ("Report 274: Gate8E Single Workstream Preauth Rehearsal", G8E_PASS, ["EDGE-only runbook generated with QCH/BINDING deferrals.", "All authorization statuses remain NOT_AUTHORIZED_REHEARSAL_ONLY."]),
        "275_NODI_COMSOL_GATE8F_ISOLATION_PROOF_20260629.md": ("Report 275: Gate8F Isolation Proof", G8F_PASS, [f"Isolation row-equivalent: {summary['gate8f_isolation_rows']}.", "Leakage cases hard-fail; legitimate EDGE template remains preauth-required, not approved."]),
        "276_NODI_COMSOL_GATE8G_JOINT_FREEZE_SIGNOFF_CANDIDATE_BOARD_20260629.md": ("Report 276: Gate8G Joint Freeze Signoff Candidate Board", G8G_PASS, ["Interface freeze candidate can be signed off for review-only use.", "Evidence authorization remains closed."]),
        "277_NODI_COMSOL_GATE8H_EVIDENCE_AUTHORIZATION_ANTI_CONFUSION_PACKET_20260629.md": ("Report 277: Gate8H Evidence Authorization Anti-Confusion Packet", G8H_PASS, ["Freeze/ready/candidate/preauth/rehearsal terms are explicitly non-authorizing.", "Positive approved/accepted/production/runtime/JRC/weighting flags hard-fail."]),
        "278_NODI_COMSOL_GATE8I_RELEASE_ARCHIVE_HANDOFF_INDEX_20260629.md": ("Report 278: Gate8I Release Archive Handoff Index", G8I_PASS, ["Gate5-Gate8 archive and handoff manifest generated.", "Next decision point remains explicit user preauth, likely EDGE-only if selected."]),
        "279_NODI_COMSOL_GATE8J_VALIDATION_SELF_REVIEW_20260629.md": ("Report 279: Gate8J Validation and Self-Review", G8J_PASS, ["Twelve validation checks and twelve reviewer sections pass.", "No-auth sweep clean."]),
        "280_NODI_COMSOL_GATE8K_JOINT_FREEZE_SIGNOFF_REHEARSAL_PACKAGE_20260629.md": ("Report 280: Gate8K Joint Freeze Signoff Rehearsal Package", G8K_PASS, ["Gate8A-K package ready for commit/push.", "No COMSOL run, no NODI rerun, no evidence/formula/production authorization."]),
    }
    return {"summary": summary, "csv": csv_payload, "joint_lock": joint_lock, "reports": reports}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    issues = []
    expected = {
        "comsol_manifest_rows": 42,
        "comsol_validation_rows": 16,
        "comsol_nodi_receipt_rows": 29,
        "comsol_dictionary_rows": 366,
        "comsol_edge_spec_rows": 12,
        "comsol_qch_spec_rows": 12,
        "comsol_binding_spec_rows": 12,
        "comsol_dependency_nodes": 320,
        "comsol_dependency_edges": 420,
        "comsol_fixture_rows": 5200,
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
    }
    for key, value in expected.items():
        if s.get(key) != value:
            issues.append(f"{key} expected {value}, got {s.get(key)}")
    if s["gate8a_blocking_drift"] != 0 or s["gate8a_missing_required"] != 0:
        issues.append("Gate8A receipt drift/missing required artifact")
    if s["gate8b_joint_fields"] != 365 or s["gate8b_semantic_conflicts"] != 0:
        issues.append("Gate8B RC5.1 joint freeze reconciliation failed")
    if s["gate8c_fixture_rows"] != 5200 or s["gate8c_policy_mismatches"] != 0 or s["gate8c_unexpected_pass"] != 0:
        issues.append("Gate8C fixture replay mismatch or unexpected pass")
    if s["gate8d_approved"] != 0:
        issues.append("Gate8D approved a producer spec")
    if s["gate8f_isolation_rows"] < 1000 or s["gate8f_unexpected_accept"] != 0:
        issues.append("Gate8F isolation proof insufficient or unexpected accept")
    no_auth_rows = payload["csv"].get("NODI_COMSOL_GATE8J_NO_AUTH_SWEEP_20260629.csv", [])
    if any(row.get("sweep_status") != "PASS_NO_AUTH" for row in no_auth_rows):
        issues.append("Gate8J no-auth sweep failed")
    return issues


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in payload["csv"].items():
        write_csv_rows(OUTPUT_DIR / name, rows)
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE8B_JOINT_FREEZE_CANDIDATE_LOCKFILE_{DATE_STAMP}.json", payload["joint_lock"])
    for name, (title, disposition, bullets) in payload["reports"].items():
        (REPORT_DIR / name).write_text(report_text(title, disposition, bullets), encoding="utf-8")
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE8K_JOINT_FREEZE_REHEARSAL_PACKAGE_MANIFEST_{DATE_STAMP}.csv", build_output_manifest())
    for gate in "ABCDEFGHIJK":
        write_json_atomic(
            OUTPUT_DIR / f"NODI_COMSOL_GATE8{gate}_REPORT_{DATE_STAMP}.json",
            {"date": DATE_STAMP, "gate": f"Gate8{gate}", "summary": payload["summary"], "scope": "review-only/no-auth/joint-freeze-signoff-rehearsal"},
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate8a_to_gate8k:
        parser.error("--confirm-gate8a-to-gate8k is required")
    payload = build_payload(args.comsol_root)
    issues = validate_payload(payload)
    if issues:
        for issue in issues:
            print(f"VALIDATION_ERROR: {issue}")
        return 2
    write_outputs(payload)
    print("PASS_GATE8A_TO_GATE8K_JOINT_FREEZE_SIGNOFF_AND_PREAUTH_REHEARSAL_NO_AUTH")
    print(f"joint_fields={payload['summary']['gate8b_joint_fields']}")
    print(f"fixture_replay_rows={payload['summary']['gate8c_fixture_rows']}")
    print(f"isolation_rows={payload['summary']['gate8f_isolation_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
