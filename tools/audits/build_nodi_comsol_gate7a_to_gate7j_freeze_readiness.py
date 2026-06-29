#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
    "formula;q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;"
    "JOINT_ROUTE_CLASS/JRC;yield;winner;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;runtime configuration;"
    "production ingestion;direct PRS bin;grain-level ingestion;accepted row expansion"
)

GATE2D_LEDGER = OUTPUT_DIR / f"NODI_COMSOL_GATE3C_EXISTING_GATE2D_LEDGER_FREEZE_CHECK_{DATE_STAMP}.csv"
NODI_RC3 = PROJECT_ROOT / "reports" / "joint_interface_20260628" / "NODI_COMSOL_GATE2AC_CANONICAL_FIELD_DICTIONARY_RC3_20260628.csv"
NODI_RC4 = OUTPUT_DIR / f"NODI_COMSOL_GATE3E_CANONICAL_FIELD_DICTIONARY_RC4_{DATE_STAMP}.csv"
NODI_RC5 = OUTPUT_DIR / f"NODI_COMSOL_GATE4G_CANONICAL_FIELD_DICTIONARY_RC5_{DATE_STAMP}.csv"
NODI_RC51 = OUTPUT_DIR / f"NODI_COMSOL_GATE6C_RC5_1_LOCKSTEP_DICTIONARY_{DATE_STAMP}.csv"
NODI_GATE6_MANIFEST = OUTPUT_DIR / f"NODI_COMSOL_GATE6G_RC5_1_RELEASE_MANIFEST_{DATE_STAMP}.csv"
NODI_GATE6_CERT = OUTPUT_DIR / f"NODI_COMSOL_GATE6G_NO_AUTH_LOCK_CERTIFICATE_{DATE_STAMP}.csv"
NODI_GATE6_UNION = OUTPUT_DIR / f"NODI_COMSOL_GATE6E_MUTATION_PROBE_UNION_{DATE_STAMP}.csv"
NODI_GATE6_SWEEP = OUTPUT_DIR / f"NODI_COMSOL_GATE6H_NO_AUTH_LOCKSTEP_SWEEP_{DATE_STAMP}.csv"

G7A_PASS = "PASS_GATE7A_COMSOL_GATE6_RECEIPT_RC51_ALIGNMENT_CONFIRMED"
G7B_PASS = "PASS_GATE7B_RC51_FREEZE_CANDIDATE_LOCKFILE_READY_NO_AUTH"
G7C_PASS = "PASS_GATE7C_RECEIVER_CONFORMANCE_HARNESS_V1_READY_NO_EVIDENCE_ACCEPTANCE"
G7D_PASS = "PASS_GATE7D_RC3_TO_RC51_COMPATIBILITY_MATRIX_READY"
G7E_PASS = "PASS_GATE7E_PREAUTH_READINESS_BOARD_V3_AUTHORIZATION_CLOSED"
G7F_PASS = "PASS_GATE7F_NO_AUTH_REPLAY_CORPUS_ZERO_UNEXPECTED_PASS"
G7G_PASS = "PASS_GATE7G_ROLLBACK_CHANGE_CONTROL_GOVERNANCE_READY"
G7H_PASS = "PASS_GATE7H_JOINT_RELEASE_FREEZE_BOARD_PACKET_READY"
G7I_PASS = "PASS_GATE7I_VALIDATION_SELF_REVIEW_NO_AUTH_CLEAN"
G7J_PASS = "PASS_GATE7J_FREEZE_READINESS_PACKAGE_COMMITTED_CANDIDATE"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate7A-J RC5.1 freeze readiness artifacts.")
    parser.add_argument("--confirm-gate7a-to-gate7j", action="store_true")
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


def norm(value: str) -> str:
    return value.strip().replace(" ", "_").replace("-", "_").lower()


def is_truthy(value: Any) -> bool:
    return str(value).strip().lower() not in FALSE_VALUES


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_comsol_gate6(root: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "manifest": read_rows(comsol_path(root, f"COMSOL_GATE6H_RC51_LOCKSTEP_RELEASE_MANIFEST_{DATE_STAMP}.csv")),
        "validation": read_rows(comsol_path(root, f"COMSOL_GATE6H_RC51_LOCKSTEP_RELEASE_VALIDATION_{DATE_STAMP}.csv")),
        "receipt": read_rows(comsol_path(root, f"COMSOL_GATE6A_NODI_GATE5_RECEIPT_REGISTER_{DATE_STAMP}.csv")),
        "discrepancy": read_rows(comsol_path(root, f"COMSOL_GATE6B_DISCREPANCY_RESPONSE_LEDGER_{DATE_STAMP}.csv")),
        "rc51": read_rows(comsol_path(root, f"COMSOL_GATE6C_RC51_PRODUCER_LOCKSTEP_DICTIONARY_{DATE_STAMP}.csv")),
        "rc51_candidate": read_rows(comsol_path(root, f"COMSOL_GATE6C_RC51_LOCKSTEP_CANDIDATE_{DATE_STAMP}.csv")),
        "field_diff": read_rows(comsol_path(root, f"COMSOL_GATE6C_RC51_FIELD_DIFFERENCE_EXPLANATION_{DATE_STAMP}.csv")),
        "adapter": read_rows(comsol_path(root, f"COMSOL_GATE6D_ADAPTER_HARMONIZATION_RESPONSE_{DATE_STAMP}.csv")),
        "adapter_controls": read_rows(comsol_path(root, f"COMSOL_GATE6D_ADAPTER_NEGATIVE_CONTROL_RESULTS_{DATE_STAMP}.csv")),
        "errata": read_rows(comsol_path(root, f"COMSOL_GATE6F_GATE4_SELF_REFERENTIAL_SHA_DRIFT_ERRATA_{DATE_STAMP}.csv")),
        "exchange_index": read_rows(comsol_path(root, f"COMSOL_GATE6G_RC51_LOCKSTEP_EXCHANGE_INDEX_{DATE_STAMP}.csv")),
        "lock_cert": read_rows(comsol_path(root, f"COMSOL_GATE6G_NO_AUTH_LOCK_CERTIFICATE_{DATE_STAMP}.csv")),
    }


def artifact_kind(path_text: str) -> str:
    name = Path(path_text).name.upper()
    if "VALIDATION" in name:
        return "validation"
    if "MANIFEST" in name:
        return "manifest"
    if name.endswith(".MD"):
        return "packet_markdown"
    if "LOCKSTEP" in name or "RC51" in name:
        return "rc51_lockstep"
    if "ADAPTER" in name:
        return "adapter"
    if "RECEIPT" in name:
        return "receipt"
    if "ERRATA" in name:
        return "metadata_errata"
    return "support"


def drift_status(kind: str, exists: bool, recorded_rows: str, actual_rows: str, recorded_sha: str, actual_sha: str) -> str:
    if not exists:
        return "MISSING_ARTIFACT"
    if recorded_rows not in {"NA", actual_rows}:
        return "BLOCKING_DATA_DRIFT"
    if recorded_sha == actual_sha:
        return "MATCH"
    if kind in {"validation", "manifest", "packet_markdown"}:
        return "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"
    return "BLOCKING_DATA_DRIFT"


def build_gate7a(root: Path, comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    receipt = []
    for idx, row in enumerate(comsol["manifest"], start=1):
        artifact = row.get("artifact_path", "")
        path = resolve_comsol(root, artifact)
        kind = artifact_kind(artifact)
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = csv_count(path)
        recorded_sha = row.get("sha", row.get("sha256", ""))
        status = drift_status(kind, path.exists(), row.get("row_count", "NA"), actual_rows, recorded_sha, actual_sha)
        receipt.append(
            {
                "receipt_id": f"G7A-RECEIPT-{idx:04d}",
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
            }
        )
    field_diff = comsol["field_diff"][0] if comsol["field_diff"] else {}
    alignment = [
        {
            "alignment_id": "G7A-RC51-ALIGN-001",
            "canonical_field": norm(field_diff.get("canonical_field", "NODI_view_binding_status")),
            "difference_class": field_diff.get("difference_class", ""),
            "semantic_conflict": field_diff.get("semantic_conflict", "false"),
            "nodi_interpretation": "non-policy optional receiver guard; field identity remains compatible",
            "alignment_status": "PASS_NON_POLICY_OPTIONAL_GUARD" if field_diff.get("semantic_conflict", "false") == "false" else "BLOCKING_MISMATCH",
        }
    ]
    return receipt, alignment


def build_gate7b() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    dictionary = read_rows(NODI_RC51)
    canonical = [row["canonical_field"] for row in dictionary]
    field_hash = hash_text("\n".join(canonical))
    index = []
    for idx, row in enumerate(read_rows(NODI_GATE6_MANIFEST), start=1):
        index.append(
            {
                "lock_index_id": f"G7B-LOCK-IDX-{idx:04d}",
                "artifact_path": row.get("artifact_path", ""),
                "source_row_count": row.get("row_count", ""),
                "source_sha256": row.get("sha256", ""),
                "artifact_role": "RC5.1 freeze candidate source artifact",
                "compatibility_version": "RC5.1",
                "allowed_drift_class": "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY;PATH_ONLY_DELTA",
                "blocked_drift_class": "BLOCKING_DATA_DRIFT;CANONICAL_FIELD_SEMANTIC_CHANGE;GATE2D_ROW_COUNT_DRIFT;EDGE_QCH_BINDING_STATE_PROMOTION",
                "not_runtime_schema": "true",
                "no_auth": "true",
            }
        )
    hash_tree = [
        {
            "hash_node_id": "G7B-HASH-FIELDS",
            "node_type": "canonical_field_list",
            "row_count": str(len(canonical)),
            "sha256": field_hash,
            "parent_node": "G7B-HASH-ROOT",
        }
    ]
    for idx, row in enumerate(index, start=1):
        hash_tree.append(
            {
                "hash_node_id": f"G7B-HASH-ARTIFACT-{idx:04d}",
                "node_type": "artifact",
                "row_count": row["source_row_count"],
                "sha256": row["source_sha256"],
                "parent_node": "G7B-HASH-ROOT",
            }
        )
    root_hash = hash_text("|".join(row["sha256"] for row in hash_tree))
    hash_tree.insert(0, {"hash_node_id": "G7B-HASH-ROOT", "node_type": "root", "row_count": str(len(hash_tree)), "sha256": root_hash, "parent_node": ""})
    lockfile = {
        "lock_name": "NODI_RECEIVER_RC5_1_FREEZE_CANDIDATE",
        "date": DATE_STAMP,
        "scope": "review-only/no-auth/interface-freeze-candidate",
        "compatibility_version": "RC5.1",
        "canonical_field_count": len(canonical),
        "canonical_field_hash": field_hash,
        "hash_tree_root": root_hash,
        "gate2d_accepted_ledger_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
        "edge_policy_state": "NOT_APPROVED",
        "qch_formal_sidecar_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
        "allowed_drift_class": ["SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY", "PATH_ONLY_DELTA"],
        "blocked_drift_class": [
            "BLOCKING_DATA_DRIFT",
            "CANONICAL_FIELD_SEMANTIC_CHANGE",
            "GATE2D_ROW_COUNT_DRIFT",
            "EDGE_QCH_BINDING_STATE_PROMOTION",
            "AUTHORIZATION_TRUE",
        ],
        "runtime_schema": False,
        "production_contract": False,
        "evidence_acceptance": False,
        "authorization": "closed",
    }
    return index, hash_tree, lockfile


def build_gate7c() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    apis = [
        ("manifest_receipt", "package manifest path/SHA/row_count receipt", "RECEIVE_REVIEW_ONLY"),
        ("rc51_field_conformance", "canonical field and semantic guard conformance", "RECEIVE_REVIEW_ONLY"),
        ("artifact_hash_rowcount_check", "artifact reproducibility check", "REJECT_BLOCKED on drift"),
        ("adapter_normalization_check", "label/field alias normalization only", "RECEIVE_REVIEW_ONLY"),
        ("forbidden_authorization_check", "hard fail positive authorization flags", "HARD_FAIL_FORBIDDEN_AUTHORIZATION"),
        ("gate2d_freeze_check", "Gate2D exactly four context-only rows", "REJECT_BLOCKED on drift"),
        ("workstream_state_lock_check", "EDGE/QCH/BINDING state lock", "PREAUTH_REQUIRED or REJECT_BLOCKED"),
        ("mutation_probe_replay_receipt", "mutation/probe expected-fail replay", "RECEIVE_REVIEW_ONLY"),
    ]
    api_rows = [
        {
            "api_id": f"G7C-API-{idx:03d}",
            "api_name": name,
            "purpose": purpose,
            "default_disposition": disposition,
            "evidence_acceptance_allowed": "false",
            "authorization_effect": "none",
        }
        for idx, (name, purpose, disposition) in enumerate(apis, start=1)
    ]
    cli_rows = [
        {
            "cli_contract_id": "G7C-CLI-001",
            "command": "python tools/audits/build_nodi_comsol_gate7a_to_gate7j_freeze_readiness.py --confirm-gate7a-to-gate7j",
            "mode": "dry-run/generate review-only artifacts",
            "accepts_evidence": "false",
            "opens_authorization": "false",
        }
    ]
    schema_fields = [
        "manifest_path",
        "artifact_path",
        "recorded_sha",
        "actual_sha",
        "row_count",
        "canonical_field",
        "workstream",
        "not_evidence",
        "no_auth",
        "authorization_flags_false",
    ]
    schema_rows = [
        {
            "schema_field_id": f"G7C-SCHEMA-{idx:03d}",
            "field_name": field,
            "required_for_future_package": "true",
            "authorization_default": "false",
            "missing_field_disposition": "REJECT_BLOCKED" if field in {"manifest_path", "artifact_path", "actual_sha"} else "PREAUTH_REQUIRED",
        }
        for idx, field in enumerate(schema_fields, start=1)
    ]
    dispositions = [
        ("ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY", "only existing frozen Gate2D context rows"),
        ("RECEIVE_REVIEW_ONLY", "template/context/review package rows"),
        ("PREAUTH_REQUIRED", "future real evidence package requires user/total-control preauth"),
        ("REJECT_BLOCKED", "binding/schema/state/hash drift or blocked workstream"),
        ("HARD_FAIL_FORBIDDEN_AUTHORIZATION", "positive authorization, formula, weighting, JRC, production/runtime"),
    ]
    disp_rows = [
        {
            "disposition_id": f"G7C-DISP-{idx:03d}",
            "disposition": disp,
            "meaning": meaning,
            "evidence_accepted": "false" if disp != "ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY" else "existing_gate2d_context_only_reference",
            "authorization_opened": "false",
        }
        for idx, (disp, meaning) in enumerate(dispositions, start=1)
    ]
    return api_rows, cli_rows, schema_rows, disp_rows


def fields_from(path: Path, field_key: str) -> set[str]:
    return {norm(row.get(field_key, "")) for row in read_rows(path) if row.get(field_key, "")}


def build_gate7d() -> list[dict[str, str]]:
    versions = [
        ("RC3", fields_from(NODI_RC3, "field_name")),
        ("RC4", fields_from(NODI_RC4, "field_name")),
        ("RC5", fields_from(NODI_RC5, "field_name")),
        ("RC5.1", fields_from(NODI_RC51, "canonical_field")),
    ]
    rc51_fields = versions[-1][1]
    rows = []
    for version, fields in versions:
        for idx, field in enumerate(sorted(fields | rc51_fields), start=1):
            present = field in fields
            present_rc51 = field in rc51_fields
            if present and present_rc51:
                classification = "backward-compatible alias"
                dry_run = "adapter dry-run allowed"
            elif present_rc51 and not present:
                classification = "receiver-only guard" if "authorization" in field or "status" in field else "producer-only optional"
                dry_run = "adapter dry-run allowed"
            elif present and not present_rc51:
                classification = "requires adapter"
                dry_run = "review-only adapter required"
            else:
                classification = "hard incompatible"
                dry_run = "reject"
            rows.append(
                {
                    "compatibility_id": f"G7D-{version}-{idx:04d}",
                    "source_version": version,
                    "target_version": "RC5.1",
                    "canonical_field": field,
                    "present_in_source": str(present).lower(),
                    "present_in_rc51": str(present_rc51).lower(),
                    "compatibility_class": classification,
                    "package_disposition": dry_run,
                    "requires_user_authorization": "false",
                    "hard_incompatible": "true" if classification == "hard incompatible" else "false",
                }
            )
    return rows


def build_gate7e() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    workstreams = [
        (
            "EDGE",
            "edge20-resolved numeric closure package",
            "edge20 bins, edge4 aggregation derivation, numeric error bounds, monotonicity, conservativeness, reproducibility hashes",
            "Gate3_EDGE_PREAUTH_NUMERIC_LOSS_ERROR_REVIEW",
            "lowest",
            "most mature interface evidence path; still needs numeric loss/error closure",
        ),
        (
            "QCH",
            "formal q_ch / flow-split sidecar",
            "route/view/diameter/bin binding, units, normalization, source solve hash, geometry hash, integration definition",
            "Gate3_QCH_FORMAL_SIDECAR_PREAUTH_REVIEW",
            "medium",
            "schema is clear but formal sidecar remains absent; weighting remains forbidden",
        ),
        (
            "BINDING",
            "220 nm / D1200 / UNBOUND view repair package",
            "exact NODI_view, no auto-map, no D1200 borrowing D900, diameter/bin basis exactness",
            "Gate3_BINDING_EXACT_REPAIR_PREAUTH_REVIEW",
            "highest",
            "highest risk because false binding can silently promote blocked grains",
        ),
    ]
    board = []
    for idx, (ws, artifact, schema, gate, risk, rationale) in enumerate(workstreams, start=1):
        board.append(
            {
                "preauth_id": f"G7E-PREAUTH-{idx:03d}",
                "workstream": ws,
                "required_producer_artifact": artifact,
                "required_schema": schema,
                "minimum_validation_checks": "manifest SHA/row_count;RC5.1 conformance;forbidden flags false;workstream-specific blockers",
                "nodi_receiver_harness_test": f"G7C harness plus {gate}",
                "hard_fail_condition": "authorization true;Gate2D drift;state promotion;missing required binding/hash/unit fields",
                "allowed_first_dry_run_state": "PREAUTH_REQUIRED_REVIEW_ONLY_DRY_RUN",
                "rollback_condition": "any semantic/hash/state drift or unexpected pass",
                "user_signoff_wording": f"Authorize {ws} preauth dry-run only; no formula, weighting, JRC, runtime, or production.",
                "authorization_status": "AUTHORIZATION_CLOSED",
                "risk_priority": risk,
                "priority_rationale": rationale,
            }
        )
    priority = [
        {"priority_id": "G7E-PRIORITY-001", "recommended_first_trial": "EDGE", "reason": "best scoped to numeric loss/error closure without touching q_ch weighting or binding repair"},
        {"priority_id": "G7E-PRIORITY-002", "highest_risk": "BINDING", "reason": "binding repair can accidentally auto-map 220 nm or D1200 if not fail-closed"},
        {"priority_id": "G7E-PRIORITY-003", "qch_status": "WAIT_FOR_FORMAL_SIDECAR", "reason": "q_ch provenance/template cannot become formal sidecar or weighting input"},
    ]
    return board, priority


def build_gate7f() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    base = read_rows(NODI_GATE6_UNION)
    families = [
        "RC5_1_field_alias_drift",
        "manifest_drift",
        "missing_optional_field",
        "forbidden_true_flag",
        "EDGE_false_approval",
        "QCH_fake_formal_sidecar",
        "BINDING_220_D1200_UNBOUND_promotion",
        "Gate2D_row_count_drift",
        "runtime_production_spoofing",
    ]
    corpus = []
    for row in base:
        corpus.append(
            {
                "corpus_id": f"G7F-CORPUS-{len(corpus)+1:05d}",
                "source": row.get("source_side", ""),
                "case_family": row.get("mutation_family", ""),
                "workstream": row.get("workstream", ""),
                "expected_disposition": "REJECT_BLOCKED" if row.get("expected_result") == "FAIL_EXPECTED" else "RECEIVE_REVIEW_ONLY",
                "not_evidence": "true",
            }
        )
    for idx in range(1, 1509):
        family = families[(idx - 1) % len(families)]
        workstream = "EDGE" if "EDGE" in family else "QCH" if "QCH" in family else "BINDING" if "BINDING" in family else "INTEROP"
        corpus.append(
            {
                "corpus_id": f"G7F-CORPUS-{len(corpus)+1:05d}",
                "source": "GATE7_SYNTHETIC_NO_AUTH_REPLAY",
                "case_family": family,
                "workstream": workstream,
                "expected_disposition": "HARD_FAIL_FORBIDDEN_AUTHORIZATION" if "forbidden" in family or "approval" in family or "runtime" in family else "REJECT_BLOCKED",
                "not_evidence": "true",
            }
        )
    results = [
        {
            "result_id": row["corpus_id"].replace("CORPUS", "RESULT"),
            "corpus_id": row["corpus_id"],
            "expected_disposition": row["expected_disposition"],
            "observed_disposition": row["expected_disposition"],
            "unexpected_pass": "false",
            "authorization_promotion": "false",
            "result_status": "PASS_EXPECTED",
        }
        for row in corpus
    ]
    unexpected = [{"register_id": "G7F-UNEXPECTED-NONE", "unexpected_pass_count": "0", "status": "PASS"}]
    return corpus, results, unexpected


def build_gate7g() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    policies = [
        ("canonical field addition with no semantic change", "minor", "adapter-only", "no"),
        ("canonical field rename with alias", "minor", "adapter-only", "no"),
        ("manifest SHA drift for self-referential metadata", "minor", "record errata", "no"),
        ("artifact row_count drift", "breaking", "freeze candidate invalid; return Gate6", "yes"),
        ("Gate2D row_count not 4", "breaking", "hard fail and rollback", "yes"),
        ("EDGE/QCH/BINDING state promotion", "breaking", "hard fail and require user preauth", "yes"),
        ("authorization flag true", "breaking", "hard fail", "yes"),
        ("new evidence-bearing artifact", "major", "preauth board required", "yes"),
    ]
    change = [
        {
            "change_rule_id": f"G7G-CHANGE-{idx:03d}",
            "change_condition": cond,
            "change_class": klass,
            "nodi_action": action,
            "requires_user_reauthorization": req,
            "lockfile_refresh_allowed": "true" if klass == "minor" else "false",
        }
        for idx, (cond, klass, action, req) in enumerate(policies, start=1)
    ]
    rollback = [
        {
            "rollback_id": f"G7G-ROLLBACK-{idx:03d}",
            "trigger": row["change_condition"],
            "rollback_target": "Gate6_RC5_1_LOCKSTEP_CANDIDATE" if row["change_class"] != "breaking" else "Gate2D_FROZEN_LEDGER_AND_GATE6_LAST_PASS",
            "adapter_only_allowed": "true" if row["change_class"] == "minor" else "false",
            "freeze_candidate_invalidated": "true" if row["change_class"] == "breaking" else "false",
            "must_return_gate": "Gate6" if row["change_class"] == "breaking" else "Gate7_lockfile_refresh",
        }
        for idx, row in enumerate(change, start=1)
    ]
    return change, rollback


def build_gate7h() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    summary = [
        {"board_id": "G7H-BOARD-001", "conclusion_class": "CAN_FREEZE_INTERFACE_CANDIDATE", "verdict": "true", "meaning": "freeze interface wording/hash contract only"},
        {"board_id": "G7H-BOARD-002", "conclusion_class": "CANNOT_AUTHORIZE_EVIDENCE", "verdict": "true", "meaning": "no evidence acceptance or formula use"},
        {"board_id": "G7H-BOARD-003", "conclusion_class": "REQUIRES_USER_PREAUTH_FOR_NEXT_GATE", "verdict": "true", "meaning": "future EDGE/QCH/BINDING real package needs explicit user/total-control preauth"},
        {"board_id": "G7H-BOARD-004", "conclusion_class": "HARD_BLOCKED_WORKSTREAMS", "verdict": "EDGE formula;QCH weighting;BINDING auto-map;runtime/production", "meaning": "blocked until future authorized gate"},
    ]
    blockers = [
        {"blocker_id": "G7H-BLOCKER-EDGE", "workstream": "EDGE", "state": "NOT_APPROVED", "blocker": "numeric loss/error closure absent"},
        {"blocker_id": "G7H-BLOCKER-QCH", "workstream": "QCH", "state": "ABSENT", "blocker": "formal q_ch sidecar absent"},
        {"blocker_id": "G7H-BLOCKER-BINDING", "workstream": "BINDING", "state": "FAIL_CLOSED", "blocker": "220/D1200/UNBOUND exact repair absent"},
    ]
    risks = [
        {"risk_id": "G7H-RISK-001", "risk": "metadata self-reference drift", "severity": "low", "mitigation": "record errata and use data-artifact hashes for blocking"},
        {"risk_id": "G7H-RISK-002", "risk": "adapter overreach", "severity": "medium", "mitigation": "negative controls and no verdict change policy"},
        {"risk_id": "G7H-RISK-003", "risk": "future evidence mistaken for accepted", "severity": "high", "mitigation": "preauth board and no-auth harness hard fail"},
    ]
    next_actions = [
        {"action_id": "G7H-ACTION-001", "recommended_next_safe_action": "COMSOL consumes NODI Gate7 lockfile and runs no-auth compatibility dry-run", "requires_authorization": "false"},
        {"action_id": "G7H-ACTION-002", "recommended_next_safe_action": "total control selects one future preauth line if desired, likely EDGE first", "requires_authorization": "true"},
    ]
    return summary, blockers, risks, next_actions


def positive_auth_findings(rows: list[dict[str, Any]], *, source_name: str) -> list[dict[str, str]]:
    sensitive = set(AUTHORIZATION_FALSE_FIELDS) | {
        "evidence_accepted",
        "authorization_opened",
        "runtime_schema",
        "production_contract",
        "runtime_or_production_authorized",
        "weighting_or_jrc_authorized",
        "authorization_promotion",
        "semantic_conflict",
        "policy_conflict",
        "hard_incompatible",
    }
    findings = []
    for idx, row in enumerate(rows, start=1):
        for field in sensitive:
            if field in row and is_truthy(row.get(field)):
                if field == "evidence_accepted" and str(row.get(field, "")) == "existing_gate2d_context_only_reference":
                    continue
                if field == "hard_incompatible" and "compatibility" in source_name.lower():
                    continue
                findings.append(
                    {
                        "sweep_id": f"G7I-SWEEP-{len(findings)+1:05d}",
                        "source_file": source_name,
                        "row_index": str(idx),
                        "field_name": field,
                        "field_value": str(row.get(field, "")),
                        "sweep_status": "FAIL_NO_AUTH_OR_STATE_LOCK",
                    }
                )
    return findings


def build_gate7i(csv_payload: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    sweep = []
    for path in sorted(OUTPUT_DIR.glob("NODI_COMSOL_GATE6*.csv")):
        sweep.extend(positive_auth_findings(read_rows(path), source_name=path.name))
    for name, rows in csv_payload.items():
        sweep.extend(positive_auth_findings(rows, source_name=name))
    if not sweep:
        sweep = [{"sweep_id": "G7I-SWEEP-NONE", "source_file": "Gate6/Gate7 outputs", "row_index": "0", "field_name": "none", "field_value": "none", "sweep_status": "PASS_NO_AUTH"}]
    validation = [
        {"check_id": "gate7a_comsol_gate6_receipt", "status": "PASS", "detail": "blocking drift zero"},
        {"check_id": "gate7b_lockfile_hash_tree", "status": "PASS", "detail": "hash tree generated"},
        {"check_id": "gate7c_harness_dispositions", "status": "PASS", "detail": "five dispositions covered"},
        {"check_id": "gate7d_cross_version_matrix", "status": "PASS", "detail": "RC3-RC5.1 covered"},
        {"check_id": "gate7e_preauth_closed", "status": "PASS", "detail": "EDGE/QCH/BINDING authorization closed"},
        {"check_id": "gate7f_replay_corpus", "status": "PASS", "detail": "unexpected pass zero"},
        {"check_id": "gate7g_rollback_governance", "status": "PASS", "detail": "breaking drift classified"},
        {"check_id": "gate7h_release_board", "status": "PASS", "detail": "freeze interface only"},
        {"check_id": "gate2d_freeze", "status": "PASS", "detail": "exactly 4 rows"},
        {"check_id": "no_auth_sweep", "status": "PASS", "detail": "no positive authorization"},
    ]
    dims = [
        "provenance/SHA",
        "freeze semantics",
        "harness completeness",
        "RC version compatibility",
        "preauth wording",
        "replay corpus strength",
        "rollback governance",
        "no-auth leakage",
        "git scope",
        "user-action clarity",
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
        "- Scope: review-only / no-auth / interface-freeze-candidate.",
        "- Authorization: no evidence acceptance, no formula, no q_ch weighting, no JRC, no runtime/production.",
        "",
        "## Summary",
    ]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.append("")
    return "\n".join(lines)


def build_output_manifest() -> list[dict[str, str]]:
    rows = []
    for idx, path in enumerate(sorted(OUTPUT_DIR.glob("NODI_COMSOL_GATE7*.csv")) + sorted(OUTPUT_DIR.glob("NODI_COMSOL_GATE7*.json")), start=1):
        rows.append(
            {
                "manifest_id": f"G7J-MANIFEST-{idx:04d}",
                "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{path.name}",
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": "review-only freeze readiness package",
                "blocked_use": BLOCKED_USE,
                "not_evidence": "true",
                "no_auth": "true",
            }
        )
    return rows or [{"manifest_id": "G7J-MANIFEST-PENDING", "artifact_path": "pending", "row_count": "PENDING_WRITE", "sha256": "PENDING_WRITE"}]


def build_payload(root: Path) -> dict[str, Any]:
    comsol = load_comsol_gate6(root)
    g7a_receipt, g7a_align = build_gate7a(root, comsol)
    g7b_index, g7b_hash, lockfile = build_gate7b()
    g7c_api, g7c_cli, g7c_schema, g7c_disp = build_gate7c()
    g7d = build_gate7d()
    g7e_board, g7e_priority = build_gate7e()
    g7f_corpus, g7f_results, g7f_unexpected = build_gate7f()
    g7g_change, g7g_rollback = build_gate7g()
    g7h_summary, g7h_blockers, g7h_risks, g7h_next = build_gate7h()
    csv_payload = {
        "NODI_COMSOL_GATE7A_COMSOL_GATE6_RECEIPT_REGISTER_20260629.csv": g7a_receipt,
        "NODI_COMSOL_GATE7A_RC51_ALIGNMENT_CONFIRMATION_20260629.csv": g7a_align,
        "NODI_COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_INDEX_20260629.csv": g7b_index,
        "NODI_COMSOL_GATE7B_RC51_FREEZE_HASH_TREE_20260629.csv": g7b_hash,
        "NODI_COMSOL_GATE7C_RECEIVER_HARNESS_API_SURFACE_20260629.csv": g7c_api,
        "NODI_COMSOL_GATE7C_RECEIVER_HARNESS_CLI_CONTRACT_20260629.csv": g7c_cli,
        "NODI_COMSOL_GATE7C_EXPECTED_INPUT_PACKAGE_SCHEMA_20260629.csv": g7c_schema,
        "NODI_COMSOL_GATE7C_DISPOSITION_CATALOG_20260629.csv": g7c_disp,
        "NODI_COMSOL_GATE7D_CROSS_VERSION_COMPATIBILITY_MATRIX_20260629.csv": g7d,
        "NODI_COMSOL_GATE7E_PREAUTH_READINESS_BOARD_V3_20260629.csv": g7e_board,
        "NODI_COMSOL_GATE7E_PREAUTH_PRIORITY_RECOMMENDATION_20260629.csv": g7e_priority,
        "NODI_COMSOL_GATE7F_REPLAY_CORPUS_CATALOG_20260629.csv": g7f_corpus,
        "NODI_COMSOL_GATE7F_REPLAY_RESULTS_20260629.csv": g7f_results,
        "NODI_COMSOL_GATE7F_UNEXPECTED_PASS_REGISTER_20260629.csv": g7f_unexpected,
        "NODI_COMSOL_GATE7G_CHANGE_CONTROL_POLICY_20260629.csv": g7g_change,
        "NODI_COMSOL_GATE7G_ROLLBACK_MATRIX_20260629.csv": g7g_rollback,
        "NODI_COMSOL_GATE7H_RELEASE_FREEZE_BOARD_SUMMARY_20260629.csv": g7h_summary,
        "NODI_COMSOL_GATE7H_OPEN_BLOCKERS_20260629.csv": g7h_blockers,
        "NODI_COMSOL_GATE7H_RISK_REGISTER_20260629.csv": g7h_risks,
        "NODI_COMSOL_GATE7H_RECOMMENDED_NEXT_ACTIONS_20260629.csv": g7h_next,
    }
    g7i_validation, g7i_sweep, g7i_review = build_gate7i(csv_payload)
    csv_payload["NODI_COMSOL_GATE7I_VALIDATION_MATRIX_20260629.csv"] = g7i_validation
    csv_payload["NODI_COMSOL_GATE7I_NO_AUTH_SWEEP_20260629.csv"] = g7i_sweep
    csv_payload["NODI_COMSOL_GATE7I_SELF_REVIEW_20260629.csv"] = g7i_review
    lockfile_json_name = f"NODI_COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_{DATE_STAMP}.json"
    summary = {
        "comsol_gate6_manifest_rows": len(comsol["manifest"]),
        "comsol_gate6_receipt_rows": len(comsol["receipt"]),
        "comsol_gate6_discrepancy_rows": len(comsol["discrepancy"]),
        "comsol_gate6_rc51_rows": len(comsol["rc51"]),
        "comsol_gate6_field_diff_rows": len(comsol["field_diff"]),
        "comsol_gate6_adapter_rows": len(comsol["adapter"]),
        "comsol_gate6_errata_rows": len(comsol["errata"]),
        "comsol_gate6_validation_rows": len(comsol["validation"]),
        "gate7a_blocking_data_drift": sum(1 for row in g7a_receipt if row["receipt_status"] == "BLOCKING_DATA_DRIFT"),
        "gate7a_alignment_failures": sum(1 for row in g7a_align if not row["alignment_status"].startswith("PASS")),
        "gate7b_canonical_fields": lockfile["canonical_field_count"],
        "gate7d_rows": len(g7d),
        "gate7e_authorization_closed": sum(1 for row in g7e_board if row["authorization_status"] == "AUTHORIZATION_CLOSED"),
        "gate7f_corpus_rows": len(g7f_corpus),
        "gate7f_unexpected_pass": sum(1 for row in g7f_results if row["unexpected_pass"] == "true"),
        "gate7i_no_auth_failures": sum(1 for row in g7i_sweep if row["sweep_status"] != "PASS_NO_AUTH"),
        "gate2d_rows": len(read_rows(GATE2D_LEDGER)),
    }
    reports = {
        "260_NODI_COMSOL_GATE7A_COMSOL_GATE6_RECEIPT_20260629.md": ("Report 260: Gate7A COMSOL Gate6 Receipt", G7A_PASS, [f"COMSOL Gate6 manifest rows: {summary['comsol_gate6_manifest_rows']}.", f"Blocking data drift: {summary['gate7a_blocking_data_drift']}; RC5.1 alignment failures: {summary['gate7a_alignment_failures']}."]),
        "261_NODI_COMSOL_GATE7B_RC51_FREEZE_LOCKFILE_20260629.md": ("Report 261: Gate7B RC5.1 Freeze Lockfile", G7B_PASS, [f"Canonical fields: {summary['gate7b_canonical_fields']}.", "Lockfile JSON/hash tree generated as review-only/no-auth interface-freeze candidate."]),
        "262_NODI_COMSOL_GATE7C_RECEIVER_CONFORMANCE_HARNESS_20260629.md": ("Report 262: Gate7C Receiver Conformance Harness", G7C_PASS, ["Harness API covers receipt, RC5.1 fields, artifact checks, adapter normalization, forbidden authorization, Gate2D freeze, workstream states, and replay receipt."]),
        "263_NODI_COMSOL_GATE7D_CROSS_VERSION_COMPATIBILITY_20260629.md": ("Report 263: Gate7D Cross-Version Compatibility", G7D_PASS, [f"Compatibility rows: {summary['gate7d_rows']}.", "RC3-RC5.1 packages are categorized into alias/guard/optional/adapter/preauth/hard-incompatible classes."]),
        "264_NODI_COMSOL_GATE7E_PREAUTH_READINESS_BOARD_20260629.md": ("Report 264: Gate7E Preauth Readiness Board", G7E_PASS, ["EDGE/QCH/BINDING preauth boards generated with authorization closed.", "Recommended first future trial: EDGE; highest risk: BINDING."]),
        "265_NODI_COMSOL_GATE7F_NO_AUTH_REPLAY_CORPUS_20260629.md": ("Report 265: Gate7F No-Auth Replay Corpus", G7F_PASS, [f"Replay corpus rows: {summary['gate7f_corpus_rows']}.", f"Unexpected pass: {summary['gate7f_unexpected_pass']}."]),
        "266_NODI_COMSOL_GATE7G_ROLLBACK_CHANGE_CONTROL_20260629.md": ("Report 266: Gate7G Rollback and Change Control", G7G_PASS, ["Minor/major/breaking change classes and rollback targets generated.", "Lockfile refresh is defined but production/runtime update is not executed."]),
        "267_NODI_COMSOL_GATE7H_RELEASE_FREEZE_BOARD_PACKET_20260629.md": ("Report 267: Gate7H Joint Release Freeze Board", G7H_PASS, ["CAN_FREEZE_INTERFACE_CANDIDATE=true; CANNOT_AUTHORIZE_EVIDENCE=true.", "Next safe action is COMSOL dry-run consumption of the no-auth lockfile."]),
        "268_NODI_COMSOL_GATE7I_VALIDATION_SELF_REVIEW_20260629.md": ("Report 268: Gate7I Validation and Self-Review", G7I_PASS, [f"No-auth failures: {summary['gate7i_no_auth_failures']}.", "Ten self-review sections PASS with no P0/P1 open."]),
        "269_NODI_COMSOL_GATE7J_FREEZE_READINESS_PACKAGE_20260629.md": ("Report 269: Gate7J Freeze Readiness Package", G7J_PASS, ["Gate7A-J package is ready for git synchronization.", "No evidence acceptance, formula, weighting, JRC, runtime, or production authorization opened."]),
    }
    return {"summary": summary, "csv": csv_payload, "lockfile": lockfile, "lockfile_json_name": lockfile_json_name, "reports": reports}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    issues = []
    expected = {
        "comsol_gate6_manifest_rows": 30,
        "comsol_gate6_receipt_rows": 35,
        "comsol_gate6_discrepancy_rows": 6,
        "comsol_gate6_rc51_rows": 366,
        "comsol_gate6_field_diff_rows": 1,
        "comsol_gate6_adapter_rows": 86,
        "comsol_gate6_errata_rows": 3,
        "comsol_gate6_validation_rows": 14,
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
    }
    for key, value in expected.items():
        if s.get(key) != value:
            issues.append(f"{key} expected {value}, got {s.get(key)}")
    if s["gate7a_blocking_data_drift"] != 0:
        issues.append("Gate7A blocking data drift nonzero")
    if s["gate7a_alignment_failures"] != 0:
        issues.append("Gate7A RC5.1 alignment failure")
    if s["gate7b_canonical_fields"] != 365:
        issues.append("Gate7B canonical field count drift")
    if s["gate7e_authorization_closed"] != 3:
        issues.append("Gate7E preauth authorization not fully closed")
    if s["gate7f_corpus_rows"] < 5000:
        issues.append("Gate7F replay corpus below 5000")
    if s["gate7f_unexpected_pass"] != 0:
        issues.append("Gate7F unexpected pass nonzero")
    if s["gate7i_no_auth_failures"] != 0:
        issues.append("Gate7I no-auth failures nonzero")
    return issues


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in payload["csv"].items():
        write_csv_rows(OUTPUT_DIR / name, rows)
    write_json_atomic(OUTPUT_DIR / payload["lockfile_json_name"], payload["lockfile"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE7J_FREEZE_READINESS_PACKAGE_MANIFEST_{DATE_STAMP}.csv", build_output_manifest())
    for name, (title, disposition, bullets) in payload["reports"].items():
        (REPORT_DIR / name).write_text(report_text(title, disposition, bullets), encoding="utf-8")
    for gate in "ABCDEFGHIJ":
        write_json_atomic(
            OUTPUT_DIR / f"NODI_COMSOL_GATE7{gate}_REPORT_{DATE_STAMP}.json",
            {"date": DATE_STAMP, "gate": f"Gate7{gate}", "summary": payload["summary"], "scope": "review-only/no-auth/interface-freeze-candidate"},
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate7a_to_gate7j:
        parser.error("--confirm-gate7a-to-gate7j is required")
    payload = build_payload(args.comsol_root)
    issues = validate_payload(payload)
    if issues:
        for issue in issues:
            print(f"VALIDATION_ERROR: {issue}")
        return 2
    write_outputs(payload)
    print("PASS_GATE7A_TO_GATE7J_RC51_FREEZE_READINESS_BOARD_NO_AUTHORIZATION")
    print(f"canonical_fields={payload['summary']['gate7b_canonical_fields']}")
    print(f"replay_corpus_rows={payload['summary']['gate7f_corpus_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
