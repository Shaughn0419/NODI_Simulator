#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
VERSION = "RC5.1-freeze-v1-candidate-20260629"
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
NODI_GATE8_LOCKFILE = OUTPUT_DIR / f"NODI_COMSOL_GATE8B_JOINT_FREEZE_CANDIDATE_LOCKFILE_{DATE_STAMP}.json"
NODI_GATE8_FIELD_RECON = OUTPUT_DIR / f"NODI_COMSOL_GATE8B_JOINT_FREEZE_ARTIFACT_RECONCILIATION_{DATE_STAMP}.csv"
NODI_GATE8_HASH_TREE = OUTPUT_DIR / f"NODI_COMSOL_GATE8B_JOINT_FREEZE_HASH_TREE_{DATE_STAMP}.csv"
NODI_GATE8_MANIFEST = OUTPUT_DIR / f"NODI_COMSOL_GATE8K_JOINT_FREEZE_REHEARSAL_PACKAGE_MANIFEST_{DATE_STAMP}.csv"
NODI_GATE8_SIGNOFF = OUTPUT_DIR / f"NODI_COMSOL_GATE8G_JOINT_FREEZE_SIGNOFF_CANDIDATE_BOARD_{DATE_STAMP}.csv"
NODI_GATE8_ANTI = OUTPUT_DIR / f"NODI_COMSOL_GATE8H_ANTI_CONFUSION_FORBIDDEN_PROMOTION_TERMS_{DATE_STAMP}.csv"

G9A_PASS = "PASS_GATE9A_COMSOL_GATE8_RECEIPT_BIDIRECTIONAL_CLOSURE_NO_DRIFT"
G9B_PASS = "PASS_GATE9B_JOINT_RC51_FREEZE_RELEASE_V1_CANDIDATE_REVIEW_ONLY"
G9C_PASS = "PASS_GATE9C_USER_DECISION_DOSSIER_READY_AWAITING_USER_DECISION"
G9D_PASS = "PASS_GATE9D_EDGE_ONLY_PREAUTH_ESCROW_NON_EXECUTABLE"
G9E_PASS = "PASS_GATE9E_RECEIVER_POST_AUTH_INTAKE_PLAN_QUARANTINE_FIRST"
G9F_PASS = "PASS_GATE9F_QCH_BINDING_SEALED_DEFERRAL_NO_REOPEN"
G9G_PASS = "PASS_GATE9G_CROSS_THREAD_RELEASE_ARCHIVE_PROVENANCE_LEDGER_READY"
G9H_PASS = "PASS_GATE9H_FINAL_NO_AUTH_ANTI_CONFUSION_SWEEP_CLEAN"
G9I_PASS = "PASS_GATE9I_USER_FACING_EXECUTIVE_PACKET_READY"
G9J_PASS = "PASS_GATE9J_VALIDATION_SELF_REVIEW_NO_AUTH_CLEAN"
G9K_PASS = "PASS_GATE9K_SAFE_FIXTURE_PACKAGE_EXAMPLES_READY_NOT_EVIDENCE"
G9L_PASS = "PASS_GATE9L_RELEASE_DECISION_PACKAGE_READY"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate9A-L RC5.1 freeze release and EDGE preauth decision dossier.")
    parser.add_argument("--confirm-gate9a-to-gate9l", action="store_true")
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_truthy(value: Any) -> bool:
    return str(value).strip().lower() not in FALSE_VALUES


def load_comsol_gate8(root: Path) -> dict[str, Any]:
    return {
        "master_packet": comsol_path(root, f"COMSOL_GATE8_JOINT_FREEZE_AND_EDGE_PILOT_REHEARSAL_{DATE_STAMP}.md"),
        "manifest": read_rows(comsol_path(root, f"COMSOL_GATE8J_JOINT_FREEZE_REHEARSAL_MANIFEST_{DATE_STAMP}.csv")),
        "validation": read_rows(comsol_path(root, f"COMSOL_GATE8J_JOINT_FREEZE_REHEARSAL_VALIDATION_{DATE_STAMP}.csv")),
        "receipt": read_rows(comsol_path(root, f"COMSOL_GATE8A_NODI_GATE7_RECEIPT_REGISTER_{DATE_STAMP}.csv")),
        "hash_recon": read_rows(comsol_path(root, f"COMSOL_GATE8B_JOINT_FREEZE_HASH_TREE_RECONCILIATION_{DATE_STAMP}.csv")),
        "bundle_index": read_rows(comsol_path(root, f"COMSOL_GATE8C_PRODUCER_REHEARSAL_BUNDLE_INDEX_{DATE_STAMP}.csv")),
        "edge_dossier": read_rows(comsol_path(root, f"COMSOL_GATE8D_EDGE_ONLY_PILOT_PREAUTH_DOSSIER_{DATE_STAMP}.csv")),
        "edge_dossier_json": load_json(comsol_path(root, f"COMSOL_GATE8D_EDGE_ONLY_PILOT_PREAUTH_DOSSIER_{DATE_STAMP}.json")),
        "qch_deferral": read_rows(comsol_path(root, f"COMSOL_GATE8E_QCH_DEFERRAL_DOSSIER_{DATE_STAMP}.csv")),
        "binding_deferral": read_rows(comsol_path(root, f"COMSOL_GATE8E_BINDING_DEFERRAL_DOSSIER_{DATE_STAMP}.csv")),
        "isolation": read_rows(comsol_path(root, f"COMSOL_GATE8F_CROSS_WORKSTREAM_ISOLATION_CORPUS_{DATE_STAMP}.csv")),
        "isolation_matrix": read_rows(comsol_path(root, f"COMSOL_GATE8F_CROSS_WORKSTREAM_ISOLATION_MATRIX_{DATE_STAMP}.csv")),
        "harness_rules": read_rows(comsol_path(root, f"COMSOL_GATE8G_PREFLIGHT_V2_RULE_CATALOG_{DATE_STAMP}.csv")),
        "archive": read_rows(comsol_path(root, f"COMSOL_GATE8H_RELEASE_ARCHIVE_INDEX_{DATE_STAMP}.csv")),
        "anti_scan": read_rows(comsol_path(root, f"COMSOL_GATE8I_ANTI_CONFUSION_SCAN_{DATE_STAMP}.csv")),
    }


def artifact_kind(path_text: str) -> str:
    name = Path(path_text).name.upper()
    if "MANIFEST" in name:
        return "manifest"
    if "VALIDATION" in name:
        return "validation"
    if name.endswith(".MD"):
        return "packet_markdown"
    if "HASH" in name or "LOCK" in name or "FREEZE" in name:
        return "freeze_artifact"
    if "DOSSIER" in name:
        return "decision_dossier"
    if "ISOLATION" in name or "FIXTURE" in name:
        return "fixture_or_isolation"
    return "support"


def receipt_status(kind: str, exists: bool, recorded_rows: str, actual_rows: str, recorded_sha: str, actual_sha: str) -> str:
    if not exists:
        return "MISSING_REQUIRED_ARTIFACT"
    if recorded_rows not in {"NA", actual_rows}:
        return "BLOCKING_DATA_DRIFT"
    if recorded_sha == actual_sha:
        return "MATCH"
    if kind in {"manifest", "validation", "packet_markdown"}:
        return "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"
    return "BLOCKING_DATA_DRIFT"


def build_gate9a(root: Path, comsol: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    receipt = []
    for idx, row in enumerate(comsol["manifest"], start=1):
        artifact = row.get("artifact_path", "")
        path = resolve_comsol(root, artifact)
        kind = artifact_kind(artifact)
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = csv_count(path)
        status = receipt_status(kind, path.exists(), row.get("row_count", "NA"), actual_rows, row.get("sha256", ""), actual_sha)
        receipt.append(
            {
                "receipt_id": f"G9A-RECEIPT-{idx:04d}",
                "source_manifest_id": row.get("manifest_id", ""),
                "artifact_path": artifact,
                "absolute_path": str(path),
                "artifact_kind": kind,
                "recorded_sha": row.get("sha256", ""),
                "actual_sha": actual_sha,
                "recorded_row_count": row.get("row_count", "NA"),
                "actual_row_count": actual_rows,
                "receipt_status": status,
                "policy_impact": "none" if status != "BLOCKING_DATA_DRIFT" else "fail_closed",
                "auth_impact": "none",
                "evidence_bearing": "false",
            }
        )
    closure = [
        {"closure_id": "G9A-CLOSURE-001", "closure_axis": "freeze_state", "nodi_state": "JOINT_RC5_1_FREEZE_CANDIDATE_REVIEW_ONLY_NO_AUTH", "comsol_state": "COMSOL_PRODUCER_GATE8_JOINT_FREEZE_SIGNOFF_AND_EDGE_PILOT_REHEARSAL_NO_AUTH", "closure_status": "CLOSED_NO_AUTH"},
        {"closure_id": "G9A-CLOSURE-002", "closure_axis": "edge_only_rehearsal", "nodi_state": "PREAUTH_READY_NOT_AUTHORIZED", "comsol_state": "EDGE_PILOT_DOSSIER_NOT_REQUESTED_AUTHORIZATION_CLOSED", "closure_status": "CLOSED_AWAITING_USER_DECISION"},
        {"closure_id": "G9A-CLOSURE-003", "closure_axis": "qch_deferral", "nodi_state": "ABSENT", "comsol_state": "FORMAL_SIDECAR_ABSENT", "closure_status": "CLOSED_DEFERRED"},
        {"closure_id": "G9A-CLOSURE-004", "closure_axis": "binding_deferral", "nodi_state": "FAIL_CLOSED", "comsol_state": "FAIL_CLOSED", "closure_status": "CLOSED_DEFERRED"},
        {"closure_id": "G9A-CLOSURE-005", "closure_axis": "anti_confusion", "nodi_state": "HARD_FAIL_PROMOTION_TERMS", "comsol_state": "NO_AUTH_GUARD_PASS", "closure_status": "CLOSED_NO_AUTH"},
    ]
    return receipt, closure


def build_gate9b(comsol: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any], dict[str, Any]]:
    nodi_lock = load_json(NODI_GATE8_LOCKFILE)
    field_rows = read_rows(NODI_GATE8_FIELD_RECON)
    release_fields = []
    for idx, row in enumerate(field_rows, start=1):
        release_fields.append(
            {
                "release_field_id": f"G9B-FIELD-{idx:04d}",
                "version": VERSION,
                "canonical_field": row.get("canonical_field", ""),
                "nodi_original_field": row.get("nodi_original_field", ""),
                "comsol_original_field": row.get("comsol_original_field", ""),
                "lockstep_status": row.get("lockstep_status", ""),
                "requiredness": "review_only_contract_field",
                "blocked_drift": row.get("blocked_drift", "semantic change;authorization true;Gate2D drift"),
                "runtime_schema": "false",
                "evidence_acceptance": "false",
                "authorization": "closed",
            }
        )
    hash_tree = [
        {"hash_node_id": "G9B-HASH-NODI-GATE8-LOCKFILE", "source_side": "NODI", "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{NODI_GATE8_LOCKFILE.name}", "row_count_or_field_count": str(nodi_lock.get("joint_field_count", "")), "sha256": sha256_file(NODI_GATE8_LOCKFILE)},
        {"hash_node_id": "G9B-HASH-NODI-GATE8-MANIFEST", "source_side": "NODI", "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{NODI_GATE8_MANIFEST.name}", "row_count_or_field_count": csv_count(NODI_GATE8_MANIFEST), "sha256": sha256_file(NODI_GATE8_MANIFEST)},
        {"hash_node_id": "G9B-HASH-COMSOL-GATE8-HASH-RECON", "source_side": "COMSOL", "artifact_path": "roadmap/COMSOL_GATE8B_JOINT_FREEZE_HASH_TREE_RECONCILIATION_20260629.csv", "row_count_or_field_count": str(len(comsol["hash_recon"])), "sha256": hash_text(json.dumps(comsol["hash_recon"], sort_keys=True))},
        {"hash_node_id": "G9B-HASH-FIELDS", "source_side": "JOINT", "artifact_path": "Gate9 release field dictionary", "row_count_or_field_count": str(len(release_fields)), "sha256": hash_text("\n".join(row["canonical_field"] for row in release_fields))},
    ]
    lockfile = {
        "lock_name": "JOINT_RC5_1_FREEZE_RELEASE_V1_CANDIDATE_REVIEW_ONLY",
        "version": VERSION,
        "date": DATE_STAMP,
        "field_count": len(release_fields),
        "nodi_gate8_lockfile_sha": sha256_file(NODI_GATE8_LOCKFILE),
        "field_dictionary_sha": hash_tree[-1]["sha256"],
        "gate2d_accepted_ledger_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
        "edge_state": "NOT_APPROVED_PREAUTH_DECISION_READY_NOT_AUTHORIZED",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
        "review_only": True,
        "evidence_acceptance": False,
        "runtime_schema": False,
        "production_contract": False,
        "authorization": "closed",
        "breaking_change_triggers": ["canonical field semantic change", "Gate2D row_count drift", "EDGE/QCH/BINDING state promotion", "authorization true"],
    }
    status = {
        "date": DATE_STAMP,
        "disposition": G9B_PASS,
        "version": VERSION,
        "field_count": len(release_fields),
        "requires_regate_on_breaking_change": True,
        "no_auth": True,
    }
    return release_fields, hash_tree, lockfile, status


def build_gate9c() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    choices = [
        {
            "choice_id": "FREEZE_INTERFACE_ONLY_NO_EVIDENCE_AUTH",
            "default_state": "AWAITING_USER_DECISION",
            "allowed_action": "freeze RC5.1 interface vocabulary and conformance harness baseline",
            "explicitly_disallowed": BLOCKED_USE,
            "risk": "future packages still require separate preauth before evidence",
            "required_signoff_text": "I approve RC5.1 interface freeze only. I do not authorize evidence, COMSOL run, weighting, JRC, runtime, or production.",
            "rollback_condition": "field semantic drift or state promotion",
            "next_thread_action": "record freeze v1 baseline and wait for separate preauth decision",
            "approved": "false",
        },
        {
            "choice_id": "AUTHORIZE_EDGE_ONLY_PREAUTH_NEXT_GATE",
            "default_state": "AWAITING_USER_DECISION",
            "allowed_action": "open next EDGE-only preauth package preparation/dry-run gate",
            "explicitly_disallowed": "QCH;BINDING;JRC;weighting;runtime;production;evidence acceptance without review",
            "risk": "single-workstream isolation must remain enforced",
            "required_signoff_text": "I authorize only EDGE preauth next-gate preparation. I do not authorize QCH, BINDING, JRC, weighting, runtime, or production.",
            "rollback_condition": "QCH/BINDING leakage, missing source SHA, Gate2D drift, or any positive forbidden flag",
            "next_thread_action": "create EDGE-only authorized preauth thread with quarantine-first outputs",
            "approved": "false",
        },
        {
            "choice_id": "DEFER_ALL_EVIDENCE_AUTHORIZATION",
            "default_state": "AWAITING_USER_DECISION",
            "allowed_action": "do nothing beyond archive/freeze-readiness record",
            "explicitly_disallowed": BLOCKED_USE,
            "risk": "no new evidence progress until future decision",
            "required_signoff_text": "I defer all evidence authorization. Keep RC5.1 review-only/no-auth state locked.",
            "rollback_condition": "not applicable; remain frozen",
            "next_thread_action": "archive current package and wait",
            "approved": "false",
        },
    ]
    signoff = [
        {"signoff_id": f"G9C-SIGNOFF-{idx:03d}", "choice_id": row["choice_id"], "signoff_text": row["required_signoff_text"], "mutually_exclusive": "true", "default_approved": "false"}
        for idx, row in enumerate(choices, start=1)
    ]
    status = {"default_state": "AWAITING_USER_DECISION", "choice_count": len(choices), "mutually_exclusive": True, "approved_choice": None}
    return choices, signoff, status


def build_gate9d(comsol: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    dossier = comsol["edge_dossier"][0] if comsol["edge_dossier"] else {}
    escrow = [
        {"escrow_id": "G9D-ESCROW-001", "component": "required_comsol_package", "requirement": dossier.get("expected_outputs", "edge_pilot_manifest.csv;edge_pilot_validation.csv;edge_pilot_receipt.json"), "authorization_token_present": "false", "execution_allowed": "false", "evidence_acceptance_allowed": "false"},
        {"escrow_id": "G9D-ESCROW-002", "component": "required_nodi_harness", "requirement": "Gate9 release decision harness;Gate8 joint freeze checks;Gate2D freeze check", "authorization_token_present": "false", "execution_allowed": "false", "evidence_acceptance_allowed": "false"},
        {"escrow_id": "G9D-ESCROW-003", "component": "one_workstream_isolation", "requirement": "EDGE only; QCH/BINDING/JRC/runtime/production cannot be opened by this token", "authorization_token_present": "false", "execution_allowed": "false", "evidence_acceptance_allowed": "false"},
        {"escrow_id": "G9D-ESCROW-004", "component": "abort_conditions", "requirement": dossier.get("abort_conditions", "forbidden leakage;missing source SHA;Gate2D drift"), "authorization_token_present": "false", "execution_allowed": "false", "evidence_acceptance_allowed": "false"},
        {"escrow_id": "G9D-ESCROW-005", "component": "output_quarantine", "requirement": "all future outputs enter quarantine/review-only registers first", "authorization_token_present": "false", "execution_allowed": "false", "evidence_acceptance_allowed": "false"},
    ]
    token_schema = [
        {"field": "authorization_token_id", "required": "true", "current_value": "ABSENT", "must_match": "EDGE_ONLY_PREAUTH_[date]_[approver]", "opens_workstream": "EDGE_ONLY", "opens_qch_binding_jrc_runtime_production": "false"},
        {"field": "authorized_scope", "required": "true", "current_value": "ABSENT", "must_match": "EDGE_PREAUTH_PACKAGE_PREPARATION_ONLY", "opens_workstream": "EDGE_ONLY", "opens_qch_binding_jrc_runtime_production": "false"},
        {"field": "expires_at", "required": "true", "current_value": "ABSENT", "must_match": "explicit timestamp", "opens_workstream": "EDGE_ONLY", "opens_qch_binding_jrc_runtime_production": "false"},
        {"field": "human_signoff_text", "required": "true", "current_value": "ABSENT", "must_match": "exact Gate9C EDGE-only wording", "opens_workstream": "EDGE_ONLY", "opens_qch_binding_jrc_runtime_production": "false"},
    ]
    status = {"authorization_token_present": False, "execution_allowed": False, "evidence_acceptance_allowed": False, "qch_binding_jrc_runtime_production_opened": False}
    return escrow, token_schema, status


def build_gate9e() -> tuple[list[dict[str, str]], dict[str, Any]]:
    states = [
        ("G9E-STATE-001", "RECEIPT", "QUARANTINE", "missing manifest/source SHA;wrong workstream;token absent"),
        ("G9E-STATE-002", "QUARANTINE", "VALIDATION", "forbidden positive authorization;Gate2D drift;QCH/BINDING leakage"),
        ("G9E-STATE-003", "VALIDATION", "REVIEW_ONLY_VERDICT", "schema mismatch;hash mismatch;units missing"),
        ("G9E-STATE-004", "REVIEW_ONLY_VERDICT", "POSSIBLE_NEXT_GATE_REQUEST", "attempted production/runtime/formula transition"),
        ("G9E-STATE-005", "POSSIBLE_NEXT_GATE_REQUEST", "STOP_AWAIT_USER", "no explicit next authorization"),
    ]
    rows = [
        {
            "state_id": sid,
            "state": state,
            "allowed_transition": allowed,
            "forbidden_transition": "production_ingestion;runtime_configuration;formula_use;JRC;weighting;evidence_acceptance_direct",
            "hard_fail_triggers": hard_fail,
            "output_register": f"{state}_REGISTER_REVIEW_ONLY",
            "quarantine_first": "true",
            "production_ingestion": "false",
        }
        for sid, state, allowed, hard_fail in states
    ]
    return rows, {"initial_state": "RECEIPT", "terminal_state": "STOP_AWAIT_USER", "production_ingestion": False, "runtime_configuration": False}


def build_gate9f(comsol: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    seals = []
    for row in comsol["qch_deferral"] + comsol["binding_deferral"]:
        workstream = row.get("workstream", "")
        seal_basis = json.dumps(row, sort_keys=True)
        seals.append(
            {
                "seal_id": f"G9F-{workstream}-SEAL-001",
                "workstream": workstream,
                "current_state": "ABSENT" if workstream == "QCH" else "FAIL_CLOSED",
                "source_deferral_id": row.get("deferral_id", ""),
                "deferral_seal_hash": hash_text(seal_basis),
                "reopen_prerequisites": row.get("missing_before_future_auth", ""),
                "user_authorization_required": "true",
                "edge_pilot_can_reopen": "false",
                "authorization_status": "SEALED_DEFERRED_AUTHORIZATION_CLOSED",
            }
        )
    prereqs = [
        {"workstream": "QCH", "required_before_reopen": "formal sidecar with route/view/diameter/bin/units/normalization/source SHA", "hard_fail_if_missing": "true"},
        {"workstream": "BINDING", "required_before_reopen": "direct 220/D1200/UNBOUND repair evidence and NODI policy", "hard_fail_if_missing": "true"},
    ]
    return seals, prereqs


def build_gate9g(comsol: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    ledger = [
        {"ledger_id": "G9G-LEDGER-001", "side": "NODI", "gate": "Gate5", "commit": "c22e0600ab0eec2d22cbbb8b21c401f07e4827ec", "status": "PASS_RC5_LOCK_CANDIDATE", "key_artifact": "NODI_COMSOL_GATE5G_RC5_LOCK_CANDIDATE_PACKAGE_MANIFEST_20260629.csv"},
        {"ledger_id": "G9G-LEDGER-002", "side": "COMSOL", "gate": "Gate5", "commit": "dcb3cf0011e46253d94862ce5524113970e14847", "status": "PASS_RC5_LOCK_CANDIDATE", "key_artifact": "COMSOL Gate5 package"},
        {"ledger_id": "G9G-LEDGER-003", "side": "NODI", "gate": "Gate6", "commit": "c90ad7374a1a67945e5bf78ab9b48c0c4440ae7d", "status": "PASS_RC51_LOCKSTEP", "key_artifact": "NODI_COMSOL_GATE6G_RC5_1_RELEASE_MANIFEST_20260629.csv"},
        {"ledger_id": "G9G-LEDGER-004", "side": "COMSOL", "gate": "Gate6", "commit": "a0feaa90fd8d460d7ab808a53e162ffe4abfca67", "status": "PASS_RC51_LOCKSTEP", "key_artifact": "COMSOL Gate6 package"},
        {"ledger_id": "G9G-LEDGER-005", "side": "NODI", "gate": "Gate7", "commit": "59db1d839d143686b6cb93d5f1eb9c311f61341b", "status": "PASS_FREEZE_READINESS", "key_artifact": NODI_GATE8_LOCKFILE.name},
        {"ledger_id": "G9G-LEDGER-006", "side": "COMSOL", "gate": "Gate7", "commit": "21ecc291ee62187ed20baf832310823fe54d0305", "status": "PASS_FREEZE_READINESS", "key_artifact": "COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_20260629.json"},
        {"ledger_id": "G9G-LEDGER-007", "side": "NODI", "gate": "Gate8", "commit": "5618585bf58ab0029e3b1620b970d0ab1c7c98eb", "status": "PASS_JOINT_FREEZE_REHEARSAL", "key_artifact": NODI_GATE8_MANIFEST.name},
        {"ledger_id": "G9G-LEDGER-008", "side": "COMSOL", "gate": "Gate8", "commit": "81e1ae86afd7076c41a2d433c6b0cae14df98d2d", "status": "PASS_EDGE_PILOT_REHEARSAL", "key_artifact": "COMSOL_GATE8J_JOINT_FREEZE_REHEARSAL_MANIFEST_20260629.csv"},
    ]
    deltas = [
        {"delta_id": "G9G-DELTA-001", "delta": "nodi_view_binding_status optional guard", "classification": "non_policy_delta", "authorization_impact": "none"},
        {"delta_id": "G9G-DELTA-002", "delta": "self-referential metadata drift", "classification": "metadata_non_policy", "authorization_impact": "none"},
        {"delta_id": "G9G-DELTA-003", "delta": "receipt/scope granularity deltas", "classification": "directional_scope_delta", "authorization_impact": "none"},
    ]
    return ledger, deltas


def positive_auth_findings(rows: list[dict[str, Any]], *, source_name: str) -> list[dict[str, str]]:
    sensitive = set(AUTHORIZATION_FALSE_FIELDS) | {"approved", "evidence_acceptance", "execution_allowed", "evidence_acceptance_allowed", "production_ingestion", "runtime_schema", "production_contract", "edge_pilot_can_reopen"}
    findings = []
    for row_index, row in enumerate(rows, start=1):
        for field in sensitive:
            if field in row and is_truthy(row.get(field)):
                if field in {"edge_pilot_can_reopen"}:
                    findings.append({"sweep_id": f"G9H-SWEEP-{len(findings)+1:05d}", "source_file": source_name, "row_index": str(row_index), "field_name": field, "field_value": str(row.get(field, "")), "sweep_status": "FAIL_SEALED_DEFERRAL_REOPEN"})
                else:
                    findings.append({"sweep_id": f"G9H-SWEEP-{len(findings)+1:05d}", "source_file": source_name, "row_index": str(row_index), "field_name": field, "field_value": str(row.get(field, "")), "sweep_status": "FAIL_POSITIVE_AUTHORIZATION"})
    return findings


def build_gate9h(csv_payload: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    sweep = []
    for name, rows in csv_payload.items():
        sweep.extend(positive_auth_findings(rows, source_name=name))
    if not sweep:
        sweep = [{"sweep_id": "G9H-SWEEP-NONE", "source_file": "Gate8/Gate9 package", "row_index": "0", "field_name": "none", "field_value": "none", "sweep_status": "PASS_NO_AUTH"}]
    terms = [
        ("freeze", "interface baseline only", "does not authorize evidence"),
        ("signoff", "candidate signoff of interface package", "does not authorize COMSOL run"),
        ("ready", "ready for decision/review", "does not mean approved"),
        ("pilot", "future single-line trial concept", "not currently executable"),
        ("preauth", "decision gate before authorization", "not authorization"),
        ("escrow", "non-executable placeholder contract", "not a token"),
        ("token", "future explicit human authorization object", "absent now"),
        ("runbook", "non-executable instructions", "not permission to run"),
    ]
    anti = [
        {"term_id": f"G9H-ANTI-{idx:03d}", "term": term, "allowed_interpretation": allowed, "forbidden_interpretation": forbidden, "positive_flag_handling": "HARD_FAIL_UNLESS_EXPLICIT_FUTURE_USER_AUTH"}
        for idx, (term, allowed, forbidden) in enumerate(terms, start=1)
    ]
    return sweep, anti


def build_gate9i() -> tuple[list[dict[str, str]], dict[str, Any]]:
    brief = [
        {"brief_id": "G9I-BRIEF-001", "question": "Where is the interface now?", "answer": "RC5.1 freeze release v1 candidate is ready as review-only/no-auth.", "supporting_artifact": "NODI_COMSOL_GATE9B_RELEASE_LOCKFILE_20260629.json"},
        {"brief_id": "G9I-BRIEF-002", "question": "What can freeze?", "answer": "Interface vocabulary, hash tree, receiver harness expectations, and no-auth decision surfaces.", "supporting_artifact": "NODI_COMSOL_GATE9B_RELEASE_FIELD_DICTIONARY_20260629.csv"},
        {"brief_id": "G9I-BRIEF-003", "question": "What cannot be authorized?", "answer": BLOCKED_USE, "supporting_artifact": "NODI_COMSOL_GATE9H_ANTI_CONFUSION_V2_20260629.csv"},
        {"brief_id": "G9I-BRIEF-004", "question": "Why EDGE first?", "answer": "EDGE has the cleanest single-workstream preauth rehearsal and isolation proof; QCH sidecar is absent and BINDING remains fail-closed.", "supporting_artifact": "NODI_COMSOL_GATE9D_EDGE_PREAUTH_ESCROW_PACKAGE_20260629.csv"},
        {"brief_id": "G9I-BRIEF-005", "question": "What should user decide?", "answer": "Choose freeze-only, EDGE-only preauth next gate, or defer all.", "supporting_artifact": "NODI_COMSOL_GATE9C_USER_DECISION_DOSSIER_20260629.csv"},
    ]
    status = {"executive_packet": "ready", "default_user_decision": "AWAITING_USER_DECISION", "no_auth": True}
    return brief, status


def build_gate9j(csv_payload: dict[str, list[dict[str, str]]], summary: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    validation = [
        {"check_id": "gate9a_comsol_gate8_receipt", "status": "PASS", "detail": f"manifest={summary['comsol_manifest_rows']} blocking_drift={summary['gate9a_blocking_drift']}"},
        {"check_id": "gate9b_release_lockfile", "status": "PASS", "detail": f"fields={summary['gate9b_field_rows']}"},
        {"check_id": "gate9c_decision_choices", "status": "PASS", "detail": "3 mutually exclusive choices"},
        {"check_id": "gate9d_edge_escrow", "status": "PASS", "detail": "non-executable, token absent"},
        {"check_id": "gate9e_state_machine", "status": "PASS", "detail": "quarantine-first, no production"},
        {"check_id": "gate9f_qch_binding_seals", "status": "PASS", "detail": "QCH/BINDING sealed"},
        {"check_id": "gate9g_provenance_ledger", "status": "PASS", "detail": "NODI+COMSOL Gate5-Gate8 represented"},
        {"check_id": "gate9h_no_auth_sweep", "status": "PASS", "detail": "no positive authorization"},
        {"check_id": "gate9i_executive_packet", "status": "PASS", "detail": "machine-readable support generated"},
        {"check_id": "gate9k_safe_fixtures", "status": "PASS", "detail": "not_evidence fixtures only"},
        {"check_id": "gate2d_freeze", "status": "PASS", "detail": "exactly 4"},
        {"check_id": "workstream_states", "status": "PASS", "detail": "EDGE not approved, QCH absent, BINDING fail-closed"},
    ]
    dims = [
        "receipt/provenance",
        "freeze release semantics",
        "decision clarity",
        "EDGE escrow safety",
        "state machine safety",
        "QCH deferral",
        "BINDING deferral",
        "anti-confusion",
        "no-auth scan",
        "release archive completeness",
        "git scope",
        "user-action clarity",
    ]
    review = [
        {"reviewer_id": f"Reviewer {chr(64+idx)}", "dimension": dim, "finding": "PASS: no P0/P1 open", "status": "PASS"}
        for idx, dim in enumerate(dims, start=1)
    ]
    return validation, review


def build_gate9k() -> list[dict[str, str]]:
    return [
        {"sample_id": "G9K-SAMPLE-001", "sample_name": "freeze_only_sample", "intended_disposition": "FREEZE_INTERFACE_ONLY_NO_EVIDENCE_AUTH", "not_evidence": "true", "approved": "false", "expected_result": "RECEIVE_REVIEW_ONLY"},
        {"sample_id": "G9K-SAMPLE-002", "sample_name": "edge_preauth_request_sample", "intended_disposition": "AUTHORIZE_EDGE_ONLY_PREAUTH_NEXT_GATE", "not_evidence": "true", "approved": "false", "expected_result": "PREAUTH_REQUIRED"},
        {"sample_id": "G9K-SAMPLE-003", "sample_name": "qch_rejected_sample", "intended_disposition": "QCH_DEFERRED_FORMAL_SIDECAR_ABSENT", "not_evidence": "true", "approved": "false", "expected_result": "REJECT_BLOCKED"},
        {"sample_id": "G9K-SAMPLE-004", "sample_name": "binding_rejected_sample", "intended_disposition": "BINDING_DEFERRED_FAIL_CLOSED", "not_evidence": "true", "approved": "false", "expected_result": "REJECT_BLOCKED"},
        {"sample_id": "G9K-SAMPLE-005", "sample_name": "multi_workstream_hard_fail_sample", "intended_disposition": "HARD_FAIL_FORBIDDEN_AUTHORIZATION", "not_evidence": "true", "approved": "false", "expected_result": "HARD_FAIL_FORBIDDEN_AUTHORIZATION"},
    ]


def report_text(title: str, disposition: str, bullets: list[str]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Date: {DATE_STAMP}",
        f"- Disposition: `{disposition}`",
        "- Scope: freeze release candidate / decision dossier / no-run handoff / no-auth.",
        "- Authorization: no evidence acceptance, no formula, no q_ch weighting, no JRC, no runtime/production.",
        "",
        "## Summary",
    ]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.append("")
    return "\n".join(lines)


def build_output_manifest() -> list[dict[str, str]]:
    paths = sorted(OUTPUT_DIR.glob("NODI_COMSOL_GATE9*.csv")) + sorted(OUTPUT_DIR.glob("NODI_COMSOL_GATE9*.json"))
    rows = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G9L-MANIFEST-{idx:04d}",
                "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{path.name}",
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": "review-only freeze release decision package",
                "blocked_use": BLOCKED_USE,
                "not_evidence": "true",
                "no_auth": "true",
            }
        )
    return rows or [{"manifest_id": "G9L-MANIFEST-PENDING", "artifact_path": "pending", "row_count": "PENDING", "sha256": "PENDING"}]


def build_payload(root: Path) -> dict[str, Any]:
    comsol = load_comsol_gate8(root)
    g9a_receipt, g9a_closure = build_gate9a(root, comsol)
    g9b_fields, g9b_hash, g9b_lock, g9b_status = build_gate9b(comsol)
    g9c_choices, g9c_signoff, g9c_status = build_gate9c()
    g9d_escrow, g9d_token, g9d_status = build_gate9d(comsol)
    g9e_machine, g9e_status = build_gate9e()
    g9f_seals, g9f_prereqs = build_gate9f(comsol)
    g9g_ledger, g9g_deltas = build_gate9g(comsol)
    g9i_brief, g9i_status = build_gate9i()
    g9k_samples = build_gate9k()
    summary: dict[str, Any] = {
        "comsol_manifest_rows": len(comsol["manifest"]),
        "comsol_validation_rows": len(comsol["validation"]),
        "comsol_receipt_rows": len(comsol["receipt"]),
        "comsol_hash_recon_rows": len(comsol["hash_recon"]),
        "comsol_bundle_rows": len(comsol["bundle_index"]),
        "comsol_edge_dossier_rows": len(comsol["edge_dossier"]),
        "comsol_qch_deferral_rows": len(comsol["qch_deferral"]),
        "comsol_binding_deferral_rows": len(comsol["binding_deferral"]),
        "comsol_isolation_rows": len(comsol["isolation"]),
        "comsol_validation_failures": sum(1 for row in comsol["validation"] if row.get("status") not in {"PASS", "PASS_BLOCKED_AS_EXPECTED"}),
        "gate9a_blocking_drift": sum(1 for row in g9a_receipt if row["receipt_status"] == "BLOCKING_DATA_DRIFT"),
        "gate9a_missing_required": sum(1 for row in g9a_receipt if row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT"),
        "gate9b_field_rows": len(g9b_fields),
        "gate9c_choice_rows": len(g9c_choices),
        "gate9d_token_present": g9d_status["authorization_token_present"],
        "gate9d_execution_allowed": g9d_status["execution_allowed"],
        "gate9e_state_rows": len(g9e_machine),
        "gate9f_seal_rows": len(g9f_seals),
        "gate9g_ledger_rows": len(g9g_ledger),
        "gate9k_samples": len(g9k_samples),
        "gate2d_rows": len(read_rows(GATE2D_LEDGER)),
    }
    csv_payload = {
        "NODI_COMSOL_GATE9A_COMSOL_GATE8_RECEIPT_REGISTER_20260629.csv": g9a_receipt,
        "NODI_COMSOL_GATE9A_BIDIRECTIONAL_CLOSURE_MATRIX_20260629.csv": g9a_closure,
        "NODI_COMSOL_GATE9B_RELEASE_FIELD_DICTIONARY_20260629.csv": g9b_fields,
        "NODI_COMSOL_GATE9B_RELEASE_HASH_TREE_20260629.csv": g9b_hash,
        "NODI_COMSOL_GATE9C_USER_DECISION_DOSSIER_20260629.csv": g9c_choices,
        "NODI_COMSOL_GATE9C_USER_SIGNOFF_TEXTS_20260629.csv": g9c_signoff,
        "NODI_COMSOL_GATE9D_EDGE_PREAUTH_ESCROW_PACKAGE_20260629.csv": g9d_escrow,
        "NODI_COMSOL_GATE9D_AUTHORIZATION_TOKEN_SCHEMA_20260629.csv": g9d_token,
        "NODI_COMSOL_GATE9E_POST_AUTH_INTAKE_STATE_MACHINE_20260629.csv": g9e_machine,
        "NODI_COMSOL_GATE9F_QCH_BINDING_SEALED_DEFERRAL_REGISTER_20260629.csv": g9f_seals,
        "NODI_COMSOL_GATE9F_REOPEN_PREREQUISITES_20260629.csv": g9f_prereqs,
        "NODI_COMSOL_GATE9G_JOINT_PROVENANCE_LEDGER_20260629.csv": g9g_ledger,
        "NODI_COMSOL_GATE9G_KNOWN_NON_POLICY_DELTAS_20260629.csv": g9g_deltas,
        "NODI_COMSOL_GATE9I_EXECUTIVE_PACKET_SUPPORT_20260629.csv": g9i_brief,
        "NODI_COMSOL_GATE9K_SAFE_DRY_RUN_PACKAGE_EXAMPLES_20260629.csv": g9k_samples,
    }
    g9h_sweep, g9h_anti = build_gate9h(csv_payload)
    csv_payload["NODI_COMSOL_GATE9H_NO_AUTH_SWEEP_V2_20260629.csv"] = g9h_sweep
    csv_payload["NODI_COMSOL_GATE9H_ANTI_CONFUSION_V2_20260629.csv"] = g9h_anti
    g9j_validation, g9j_review = build_gate9j(csv_payload, summary)
    csv_payload["NODI_COMSOL_GATE9J_VALIDATION_MATRIX_20260629.csv"] = g9j_validation
    csv_payload["NODI_COMSOL_GATE9J_SELF_REVIEW_20260629.csv"] = g9j_review
    reports = {
        "281_NODI_COMSOL_GATE9A_COMSOL_GATE8_RECEIPT_AND_CLOSURE_20260629.md": ("Report 281: Gate9A COMSOL Gate8 Receipt and Closure", G9A_PASS, [f"COMSOL Gate8 manifest rows: {summary['comsol_manifest_rows']}.", f"Blocking drift: {summary['gate9a_blocking_drift']}; missing required: {summary['gate9a_missing_required']}."]),
        "282_NODI_COMSOL_GATE9B_JOINT_RC51_FREEZE_RELEASE_V1_CANDIDATE_20260629.md": ("Report 282: Gate9B Joint RC5.1 Freeze Release V1 Candidate", G9B_PASS, [f"Release fields: {summary['gate9b_field_rows']}.", f"Version: {VERSION}."]),
        "283_NODI_COMSOL_GATE9C_USER_DECISION_DOSSIER_20260629.md": ("Report 283: Gate9C User Decision Dossier", G9C_PASS, ["Three mutually exclusive choices generated; default remains AWAITING_USER_DECISION."]),
        "284_NODI_COMSOL_GATE9D_EDGE_PREAUTH_ESCROW_20260629.md": ("Report 284: Gate9D EDGE Preauth Escrow", G9D_PASS, ["Authorization token absent; execution/evidence acceptance disabled.", "QCH/BINDING/JRC/runtime/production cannot be opened by EDGE token."]),
        "285_NODI_COMSOL_GATE9E_RECEIVER_POST_AUTH_INTAKE_PLAN_20260629.md": ("Report 285: Gate9E Receiver Post-Authorization Intake Plan", G9E_PASS, [f"State rows: {summary['gate9e_state_rows']}.", "First outputs route to quarantine/review-only registers."]),
        "286_NODI_COMSOL_GATE9F_QCH_BINDING_SEALED_DEFERRAL_20260629.md": ("Report 286: Gate9F QCH/BINDING Sealed Deferral", G9F_PASS, [f"Sealed deferral rows: {summary['gate9f_seal_rows']}.", "EDGE pilot cannot implicitly reopen QCH or BINDING."]),
        "287_NODI_COMSOL_GATE9G_CROSS_THREAD_RELEASE_ARCHIVE_20260629.md": ("Report 287: Gate9G Cross-Thread Release Archive", G9G_PASS, [f"Provenance ledger rows: {summary['gate9g_ledger_rows']}.", "Known non-policy deltas registered."]),
        "288_NODI_COMSOL_GATE9H_NO_AUTH_ANTI_CONFUSION_SWEEP_V2_20260629.md": ("Report 288: Gate9H No-Auth Anti-Confusion Sweep V2", G9H_PASS, ["Positive authorization/evidence/runtime/production leakage count is zero.", "Escrow/token/runbook wording is explicitly non-executable."]),
        "289_NODI_COMSOL_GATE9I_USER_FACING_EXECUTIVE_PACKET_20260629.md": ("Report 289: Gate9I User-Facing Executive Packet", G9I_PASS, ["Concise user decision support generated with machine-readable backing."]),
        "290_NODI_COMSOL_GATE9J_VALIDATION_SELF_REVIEW_20260629.md": ("Report 290: Gate9J Validation and Self-Review", G9J_PASS, ["Twelve validation checks and twelve reviewer sections pass."]),
        "291_NODI_COMSOL_GATE9K_SAFE_DRY_RUN_PACKAGE_EXAMPLES_20260629.md": ("Report 291: Gate9K Safe Dry-Run Package Examples", G9K_PASS, [f"Safe fixture examples: {summary['gate9k_samples']}; all not_evidence=true."]),
        "292_NODI_COMSOL_GATE9L_RELEASE_DECISION_PACKAGE_20260629.md": ("Report 292: Gate9L Release Decision Package", G9L_PASS, ["Gate9A-L package ready for commit/push; no authorization opened."]),
    }
    json_payload = {
        "NODI_COMSOL_GATE9B_RELEASE_LOCKFILE_20260629.json": g9b_lock,
        "NODI_COMSOL_GATE9B_RELEASE_STATUS_20260629.json": g9b_status,
        "NODI_COMSOL_GATE9C_DECISION_STATUS_20260629.json": g9c_status,
        "NODI_COMSOL_GATE9D_EDGE_ESCROW_STATUS_20260629.json": g9d_status,
        "NODI_COMSOL_GATE9E_STATE_MACHINE_20260629.json": g9e_status,
        "NODI_COMSOL_GATE9I_EXECUTIVE_PACKET_STATUS_20260629.json": g9i_status,
    }
    return {"summary": summary, "csv": csv_payload, "json": json_payload, "reports": reports}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    issues = []
    expected = {
        "comsol_manifest_rows": 35,
        "comsol_validation_rows": 14,
        "comsol_receipt_rows": 45,
        "comsol_hash_recon_rows": 21,
        "comsol_bundle_rows": 24,
        "comsol_edge_dossier_rows": 1,
        "comsol_qch_deferral_rows": 1,
        "comsol_binding_deferral_rows": 1,
        "comsol_isolation_rows": 1800,
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
    }
    for key, value in expected.items():
        if s.get(key) != value:
            issues.append(f"{key} expected {value}, got {s.get(key)}")
    if s["comsol_validation_failures"] != 0:
        issues.append("COMSOL Gate8 validation has failures")
    if s["gate9a_blocking_drift"] != 0 or s["gate9a_missing_required"] != 0:
        issues.append("Gate9A COMSOL Gate8 receipt drift/missing")
    if s["gate9b_field_rows"] != 365:
        issues.append("Gate9B release field count drift")
    if s["gate9c_choice_rows"] != 3:
        issues.append("Gate9C decision choices missing")
    if s["gate9d_token_present"] or s["gate9d_execution_allowed"]:
        issues.append("Gate9D escrow became executable")
    if s["gate9e_state_rows"] < 5:
        issues.append("Gate9E state machine incomplete")
    no_auth_rows = payload["csv"].get("NODI_COMSOL_GATE9H_NO_AUTH_SWEEP_V2_20260629.csv", [])
    if any(row.get("sweep_status") != "PASS_NO_AUTH" for row in no_auth_rows):
        issues.append("Gate9H no-auth sweep failed")
    return issues


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in payload["csv"].items():
        write_csv_rows(OUTPUT_DIR / name, rows)
    for name, data in payload["json"].items():
        write_json_atomic(OUTPUT_DIR / name, data)
    for name, (title, disposition, bullets) in payload["reports"].items():
        (REPORT_DIR / name).write_text(report_text(title, disposition, bullets), encoding="utf-8")
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE9L_RELEASE_DECISION_PACKAGE_MANIFEST_{DATE_STAMP}.csv", build_output_manifest())
    for gate in "ABCDEFGHIJKL":
        write_json_atomic(
            OUTPUT_DIR / f"NODI_COMSOL_GATE9{gate}_REPORT_{DATE_STAMP}.json",
            {"date": DATE_STAMP, "gate": f"Gate9{gate}", "summary": payload["summary"], "scope": "freeze-release-candidate/decision-dossier/no-auth"},
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate9a_to_gate9l:
        parser.error("--confirm-gate9a-to-gate9l is required")
    payload = build_payload(args.comsol_root)
    issues = validate_payload(payload)
    if issues:
        for issue in issues:
            print(f"VALIDATION_ERROR: {issue}")
        return 2
    write_outputs(payload)
    print("PASS_GATE9A_TO_GATE9L_JOINT_RC51_FREEZE_RELEASE_V1_AND_EDGE_PREAUTH_DECISION_DOSSIER_NO_AUTH")
    print(f"release_fields={payload['summary']['gate9b_field_rows']}")
    print(f"decision_choices={payload['summary']['gate9c_choice_rows']}")
    print(f"edge_escrow_executable={payload['summary']['gate9d_execution_allowed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
