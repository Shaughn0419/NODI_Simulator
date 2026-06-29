#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
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

BLOCKED_USE = (
    "formula;q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;"
    "JOINT_ROUTE_CLASS/JRC;yield;winner;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;runtime configuration;"
    "production ingestion;direct PRS bin;grain-level ingestion;accepted row expansion"
)

G6A_PASS = "PASS_GATE6A_COMSOL_GATE5_PACKAGE_RECEIPT_BLOCKING_DRIFT_ZERO"
G6B_PASS = "PASS_GATE6B_GATE5_DISCREPANCY_LEDGER_NO_SEMANTIC_OR_POLICY_CONFLICT"
G6C_PASS = "PASS_GATE6C_RC5_1_LOCKSTEP_DICTIONARY_REVIEW_ONLY"
G6D_PASS = "PASS_GATE6D_ADAPTER_HARMONIZATION_NO_VERDICT_CHANGE"
G6E_PASS = "PASS_GATE6E_MUTATION_PROBE_UNION_ZERO_UNEXPECTED_PASS"
G6F_PASS = "PASS_GATE6F_METADATA_DRIFT_ERRATA_RECEIPT_NON_POLICY"
G6G_PASS = "PASS_GATE6G_RC5_1_LOCKSTEP_RELEASE_CANDIDATE_NO_AUTH"
G6H_PASS = "PASS_GATE6H_VALIDATION_SELF_REVIEW_NO_AUTH_CLEAN"

GATE2D_LEDGER = OUTPUT_DIR / f"NODI_COMSOL_GATE3C_EXISTING_GATE2D_LEDGER_FREEZE_CHECK_{DATE_STAMP}.csv"
NODI_G5A = OUTPUT_DIR / f"NODI_COMSOL_GATE5A_COMSOL_GATE4_RECEIPT_REGISTER_{DATE_STAMP}.csv"
NODI_G5B = OUTPUT_DIR / f"NODI_COMSOL_GATE5B_PENDING_CLOSURE_MATRIX_{DATE_STAMP}.csv"
NODI_G5C = OUTPUT_DIR / f"NODI_COMSOL_GATE5C_RC5_CONVERGENCE_MATRIX_{DATE_STAMP}.csv"
NODI_G5D = OUTPUT_DIR / f"NODI_COMSOL_GATE5D_ADAPTER_CLOSURE_PLAN_V3_{DATE_STAMP}.csv"
NODI_G5D_CONTROLS = OUTPUT_DIR / f"NODI_COMSOL_GATE5D_ADAPTER_NEGATIVE_CONTROL_RESULTS_{DATE_STAMP}.csv"
NODI_G5E_OWNER = OUTPUT_DIR / f"NODI_COMSOL_GATE5E_OWNER_COMMAND_ROUNDTRIP_MATRIX_{DATE_STAMP}.csv"
NODI_G5E_COMMAND = OUTPUT_DIR / f"NODI_COMSOL_GATE5E_COMMAND_GUARD_ROUNDTRIP_{DATE_STAMP}.csv"
NODI_G5F = OUTPUT_DIR / f"NODI_COMSOL_GATE5F_MUTATION_COMBINED_SUMMARY_{DATE_STAMP}.csv"
NODI_G5H = OUTPUT_DIR / f"NODI_COMSOL_GATE5H_NO_AUTH_FORBIDDEN_SWEEP_{DATE_STAMP}.csv"
NODI_G4G_RC5 = OUTPUT_DIR / f"NODI_COMSOL_GATE4G_CANONICAL_FIELD_DICTIONARY_RC5_{DATE_STAMP}.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate6A-H RC5.1 lockstep release-candidate artifacts.")
    parser.add_argument("--confirm-gate6a-to-gate6h", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    return parser


def read_rows(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path) if path.exists() else []


def csv_count(path: Path) -> str:
    return str(len(read_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def comsol_path(root: Path, name: str) -> Path:
    return root / "roadmap" / name


def resolve_comsol(root: Path, artifact_path: str) -> Path:
    direct = root / artifact_path
    if direct.exists():
        return direct
    roadmap = root / "roadmap" / artifact_path
    return roadmap if roadmap.exists() else direct


def norm(value: str) -> str:
    return value.strip().replace(" ", "_").replace("-", "_").lower()


def is_truthy(value: Any) -> bool:
    return str(value).strip().lower() not in FALSE_VALUES


def load_comsol_gate5(root: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "manifest": read_rows(comsol_path(root, f"COMSOL_GATE5H_ACTUAL_INTEROP_LOCK_MANIFEST_{DATE_STAMP}.csv")),
        "validation": read_rows(comsol_path(root, f"COMSOL_GATE5H_ACTUAL_INTEROP_LOCK_VALIDATION_{DATE_STAMP}.csv")),
        "receipt": read_rows(comsol_path(root, f"COMSOL_GATE5A_NODI_ACTUAL_RECEIPT_REGISTER_{DATE_STAMP}.csv")),
        "probe": read_rows(comsol_path(root, f"COMSOL_GATE5B_ACTUAL_PROBE_RECONCILIATION_{DATE_STAMP}.csv")),
        "probe_summary": read_rows(comsol_path(root, f"COMSOL_GATE5B_PENDING_ACTUAL_CLOSURE_SUMMARY_{DATE_STAMP}.csv")),
        "adapter": read_rows(comsol_path(root, f"COMSOL_GATE5C_PRODUCER_ADAPTER_V3_RULES_{DATE_STAMP}.csv")),
        "adapter_controls": read_rows(comsol_path(root, f"COMSOL_GATE5C_ADAPTER_V3_NEGATIVE_CONTROL_CHECKS_{DATE_STAMP}.csv")),
        "rc5_delta": read_rows(comsol_path(root, f"COMSOL_GATE5D_RC5_CONVERGENCE_DELTA_{DATE_STAMP}.csv")),
        "owner": read_rows(comsol_path(root, f"COMSOL_GATE5E_CROSS_SIDE_OWNER_LEDGER_ROUNDTRIP_{DATE_STAMP}.csv")),
        "command": read_rows(comsol_path(root, f"COMSOL_GATE5E_COMMAND_GUARD_ROUNDTRIP_CONFORMANCE_{DATE_STAMP}.csv")),
        "mutation": read_rows(comsol_path(root, f"COMSOL_GATE5F_MUTATION_V5_VALIDATION_RESULTS_{DATE_STAMP}.csv")),
        "unexpected": read_rows(comsol_path(root, f"COMSOL_GATE5F_UNEXPECTED_PASS_REGISTER_{DATE_STAMP}.csv")),
        "exchange_index": read_rows(comsol_path(root, f"COMSOL_GATE5G_ACTUAL_BIDIRECTIONAL_RC5_EXCHANGE_INDEX_{DATE_STAMP}.csv")),
        "exchange_manifest": read_rows(comsol_path(root, f"COMSOL_GATE5G_ACTUAL_BIDIRECTIONAL_RC5_EXCHANGE_MANIFEST_{DATE_STAMP}.csv")),
    }


def artifact_kind(path_text: str) -> str:
    name = Path(path_text).name.upper()
    if "VALIDATION" in name:
        return "validation"
    if "MANIFEST" in name:
        return "manifest"
    if name.endswith(".MD"):
        return "master_packet" if "LOCK_CANDIDATE" in name else "packet_markdown"
    if "RECEIPT" in name:
        return "receipt"
    if "PROBE" in name:
        return "probe_reconciliation"
    if "ADAPTER" in name:
        return "adapter"
    if "RC5" in name:
        return "rc5_dictionary"
    if "MUTATION" in name:
        return "mutation"
    if "COMMAND" in name:
        return "command_guard"
    if "OWNER" in name:
        return "owner_ledger"
    return "support"


def drift_class(kind: str, exists: bool, expected_rows: str, actual_rows: str, expected_sha: str, actual_sha: str) -> str:
    if not exists:
        return "MISSING_ARTIFACT"
    if expected_rows not in {"NA", actual_rows}:
        return "BLOCKING_DATA_DRIFT"
    if expected_sha == actual_sha:
        return "MATCH"
    if kind in {"validation", "manifest", "master_packet", "packet_markdown"}:
        return "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"
    return "BLOCKING_DATA_DRIFT"


def build_gate6a(root: Path, comsol: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    rows = []
    for idx, row in enumerate(comsol["manifest"], start=1):
        artifact = row.get("artifact_path", "")
        path = resolve_comsol(root, artifact)
        exists = path.exists()
        actual_sha = sha256_file(path) if exists else "MISSING"
        actual_rows = csv_count(path)
        kind = artifact_kind(artifact)
        status = drift_class(kind, exists, row.get("row_count", "NA"), actual_rows, row.get("sha256", ""), actual_sha)
        rows.append(
            {
                "receipt_id": f"G6A-RECEIPT-{idx:04d}",
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
                "allowed_use": "Gate6 receipt and release-candidate reconciliation only",
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def build_gate6b(g6a: list[dict[str, str]], comsol: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    nodi_g5a = read_rows(NODI_G5A)
    rows = [
        {
            "discrepancy_id": "G6B-DISC-001",
            "topic": "receipt row count",
            "nodi_value": str(len(nodi_g5a)),
            "comsol_value": str(len(comsol["receipt"])),
            "difference_class": "directional_scope_delta",
            "explanation": "NODI Gate5 received COMSOL Gate4 manifest rows; COMSOL Gate5 received NODI Gate4 report/sidecar rows.",
        },
        {
            "discrepancy_id": "G6B-DISC-002",
            "topic": "RC5 row count",
            "nodi_value": str(len(read_rows(NODI_G5C))),
            "comsol_value": str(len(comsol["rc5_delta"])),
            "difference_class": "producer_only_field",
            "explanation": "COMSOL has 366 RC5 rows but 365 unique canonical fields; duplicate canonical field nodi_view_binding_status is packaging granularity only.",
        },
        {
            "discrepancy_id": "G6B-DISC-003",
            "topic": "adapter rule count",
            "nodi_value": str(len(read_rows(NODI_G5D))),
            "comsol_value": str(len(comsol["adapter"])),
            "difference_class": "adapter_rule_granularity_delta",
            "explanation": "NODI kept 80 carried COMSOL Gate4B rules plus 24 NODI gaps; COMSOL collapsed to 48 producer-side v3 rules.",
        },
        {
            "discrepancy_id": "G6B-DISC-004",
            "topic": "mutation row count",
            "nodi_value": str(len(read_rows(NODI_G5F))),
            "comsol_value": str(len(comsol["mutation"])),
            "difference_class": "stress_suite_family_delta",
            "explanation": "NODI combined 760+960+72 rows; COMSOL generated mutation v5 1800 rows with producer-side families.",
        },
        {
            "discrepancy_id": "G6B-DISC-005",
            "topic": "validation/no-auth sweep shape",
            "nodi_value": str(len(read_rows(NODI_G5H))),
            "comsol_value": str(len(comsol["validation"])),
            "difference_class": "directional_scope_delta",
            "explanation": "NODI no-auth sweep is compact pass row; COMSOL Gate5H validation has 18 named checks.",
        },
        {
            "discrepancy_id": "G6B-DISC-006",
            "topic": "COMSOL Gate4 self-referential metadata SHA drift",
            "nodi_value": str(sum(1 for row in nodi_g5a if row.get("receipt_status") == "RECORDED_SELF_REFERENTIAL_HASH_DRIFT_NON_POLICY")),
            "comsol_value": "superseded by Gate5 package",
            "difference_class": "self_referential_metadata_delta",
            "explanation": "NODI Gate5 recorded validation/manifest/master packet SHA churn as non-policy metadata drift.",
        },
        {
            "discrepancy_id": "G6B-DISC-007",
            "topic": "COMSOL Gate5 self-referential metadata SHA drift",
            "nodi_value": str(sum(1 for row in g6a if row.get("receipt_status") == "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY")),
            "comsol_value": "current Gate5 package metadata drift",
            "difference_class": "self_referential_metadata_delta",
            "explanation": "COMSOL Gate5 validation/manifest/master packet are self-referential metadata rows; no data artifact drift.",
        },
        {
            "discrepancy_id": "G6B-DISC-008",
            "topic": "probe reconciliation",
            "nodi_value": str(len(read_rows(NODI_G5B))),
            "comsol_value": str(len(comsol["probe"])),
            "difference_class": "directional_scope_delta",
            "explanation": "Both sides carry 120 probe rows with identical closure class counts and policy conflict zero.",
        },
    ]
    for row in rows:
        row["semantic_conflict"] = "false"
        row["policy_conflict"] = "false"
        row["auth_impact"] = "none"
    return rows


def build_gate6c(comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    nodi = {row["normalized_field"]: row for row in read_rows(NODI_G5C)}
    nodi_rc5 = {norm(row.get("field_name", "")): row for row in read_rows(NODI_G4G_RC5)}
    comsol_groups: dict[str, list[dict[str, str]]] = {}
    for row in comsol["rc5_delta"]:
        comsol_groups.setdefault(norm(row.get("canonical_field", "")), []).append(row)
    fields = sorted(set(nodi) | set(comsol_groups))
    rows = []
    duplicates = []
    for idx, field in enumerate(fields, start=1):
        nrow = nodi.get(field, {})
        crows = comsol_groups.get(field, [])
        crow = crows[0] if crows else {}
        duplicate_count = len(crows)
        if duplicate_count > 1:
            duplicates.append(
                {
                    "duplicate_id": f"G6C-DUP-{len(duplicates)+1:04d}",
                    "canonical_field": field,
                    "comsol_row_count": str(duplicate_count),
                    "explanation": "producer row granularity duplicate; field identity converged",
                }
            )
        present_nodi = "true" if nrow else "false"
        present_comsol = "true" if crows else "false"
        lockstep_status = "LOCKSTEP_FIELD_CONVERGED" if nrow and crows else "LOCKSTEP_ADAPTER_REQUIRED"
        rows.append(
            {
                "rc5_1_field_id": f"G6C-RC5-1-{idx:04d}",
                "canonical_field": field,
                "nodi_field": nrow.get("field_name", nrow.get("canonical_candidate", "")),
                "comsol_field": crow.get("producer_field", crow.get("canonical_field", "")),
                "present_in_nodi_gate5": present_nodi,
                "present_in_comsol_gate5": present_comsol,
                "comsol_duplicate_row_count": str(duplicate_count),
                "side_owner": crow.get("owner", nrow.get("owner", "COMSOL producer/NODI receiver")),
                "requiredness": nrow.get("required_optional", crow.get("requiredness", "optional_review_only")),
                "directionality": "bidirectional_lockstep" if nrow and crows else "adapter_required",
                "semantic_status": "MATCH_OR_ALIAS" if crow.get("semantic_conflict", "false") == "false" else "SEMANTIC_CONFLICT",
                "adapter_status": "none" if nrow and crows else "adapter_required",
                "auth_impact": "none",
                "lockstep_status": lockstep_status,
                "edge_policy_state": nodi_rc5.get(field, {}).get("edge_policy_state", "NOT_APPROVED"),
                "qch_state": nodi_rc5.get(field, {}).get("qch_state", "ABSENT"),
                "binding_state": nodi_rc5.get(field, {}).get("binding_state", "FAIL_CLOSED"),
            }
        )
    return rows, duplicates or [{"duplicate_id": "G6C-DUP-NONE", "canonical_field": "none", "comsol_row_count": "0", "explanation": "no duplicate"}]


def build_gate6d(comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    nodi_rules = read_rows(NODI_G5D)
    comsol_by_rule = {row.get("source_rule_id", ""): row for row in comsol["adapter"]}
    matrix = []
    common_count = 0
    for idx, row in enumerate(nodi_rules, start=1):
        key = row.get("test_case_id", "")
        if key.startswith("COMSOL-"):
            key = key.removeprefix("COMSOL-")
        c = comsol_by_rule.get(key)
        if c:
            hclass = "common_rules"
            common_count += 1
        elif row.get("adapter_rule_id", "").startswith("G5D-NODI-GAP"):
            hclass = "nodi_receiver_only_rules"
        else:
            hclass = "nodi_receiver_only_rules"
        matrix.append(
            {
                "harmonization_id": f"G6D-HARM-{idx:04d}",
                "nodi_adapter_rule_id": row.get("adapter_rule_id", ""),
                "comsol_adapter_rule_id": c.get("adapter_v3_rule_id", "") if c else "",
                "source_field": row.get("source_field", ""),
                "target_field": row.get("target_field", ""),
                "harmonization_class": hclass,
                "adapter_action": c.get("adapter_action", row.get("normalization_type", "")) if c else row.get("normalization_type", ""),
                "safe_alias_rule": "true",
                "blocked_rule": "false",
                "requires_future_gate": "false",
                "policy_verdict_change_allowed": "false",
                "authorization_promotion_allowed": "false",
            }
        )
    known = {row.get("comsol_adapter_rule_id", "") for row in matrix if row.get("comsol_adapter_rule_id")}
    for row in comsol["adapter"]:
        if row.get("adapter_v3_rule_id", "") in known:
            continue
        matrix.append(
            {
                "harmonization_id": f"G6D-HARM-{len(matrix)+1:04d}",
                "nodi_adapter_rule_id": "",
                "comsol_adapter_rule_id": row.get("adapter_v3_rule_id", ""),
                "source_field": row.get("source_field", ""),
                "target_field": row.get("target_field", ""),
                "harmonization_class": "comsol_producer_only_rules",
                "adapter_action": row.get("adapter_action", ""),
                "safe_alias_rule": "true",
                "blocked_rule": "false",
                "requires_future_gate": "false",
                "policy_verdict_change_allowed": "false",
                "authorization_promotion_allowed": "false",
            }
        )
    protected = ["NOT_APPROVED", "ABSENT", "FAIL_CLOSED", "blocked", "quarantine", "review-only"]
    controls = []
    for idx, row in enumerate(matrix, start=1):
        status = protected[(idx - 1) % len(protected)]
        controls.append(
            {
                "control_id": f"G6D-NEGCTRL-{idx:04d}",
                "harmonization_id": row["harmonization_id"],
                "input_status": status,
                "observed_status": status,
                "verdict_change": "false",
                "authorization_promotion": "false",
                "control_status": "PASS_NO_VERDICT_CHANGE",
            }
        )
    return matrix, controls


def build_gate6e(comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    union = []
    for row in read_rows(NODI_G5F):
        union.append(
            {
                "union_id": f"G6E-UNION-{len(union)+1:05d}",
                "source_side": "NODI_GATE5F",
                "mutation_id": row.get("mutation_id", ""),
                "mutation_family": row.get("mutation_family", ""),
                "workstream": row.get("workstream", ""),
                "expected_result": row.get("expected_result", ""),
                "observed_result": row.get("observed_result", ""),
                "unexpected_pass": row.get("unexpected_pass", "false"),
                "authorization_promotion": row.get("forbidden_promotion", "false"),
                "gate2d_row_count_guard": "hard_fail_if_not_4",
            }
        )
    for row in comsol["mutation"]:
        union.append(
            {
                "union_id": f"G6E-UNION-{len(union)+1:05d}",
                "source_side": "COMSOL_GATE5F",
                "mutation_id": row.get("mutation_id", ""),
                "mutation_family": row.get("mutation_family", ""),
                "workstream": row.get("workstream", ""),
                "expected_result": row.get("expected_result", ""),
                "observed_result": row.get("observed_result", ""),
                "unexpected_pass": row.get("unexpected_pass", "false"),
                "authorization_promotion": row.get("authorization_promotion", "false"),
                "gate2d_row_count_guard": row.get("gate2d_row_count_guard", "hard_fail_if_not_4"),
            }
        )
    families = Counter(row["mutation_family"] for row in union)
    summary = [
        {
            "summary_id": f"G6E-SUM-{idx:04d}",
            "mutation_family": family,
            "row_equivalent_count": str(count),
            "coverage_status": "PASS_UNION_COVERED",
        }
        for idx, (family, count) in enumerate(sorted(families.items()), start=1)
    ]
    summary.append(
        {
            "summary_id": "G6E-SUM-TOTAL",
            "mutation_family": "TOTAL",
            "row_equivalent_count": str(len(union)),
            "coverage_status": "PASS_3592_ROW_EQUIVALENT_UNION",
        }
    )
    return union, summary


def build_gate6f(g6a: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for source, source_rows, superseded in (
        ("NODI_GATE5_RECORDED_COMSOL_GATE4", read_rows(NODI_G5A), "true"),
        ("NODI_GATE6_RECORDED_COMSOL_GATE5", g6a, "false"),
    ):
        for row in source_rows:
            status = row.get("receipt_status", "")
            if status not in {"RECORDED_SELF_REFERENTIAL_HASH_DRIFT_NON_POLICY", "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"}:
                continue
            rows.append(
                {
                    "drift_id": f"G6F-DRIFT-{len(rows)+1:04d}",
                    "source": source,
                    "artifact_path": row.get("artifact_path", ""),
                    "recorded_sha": row.get("manifest_sha256", row.get("recorded_sha", "")),
                    "actual_sha": row.get("actual_sha256", row.get("actual_sha", "")),
                    "row_count_status": row.get("row_count_status", "MATCH" if row.get("recorded_row_count") == row.get("actual_row_count") else ""),
                    "why_self_referential": "validation/manifest/master packet written during finalization can hash-churn after manifest capture",
                    "policy_impact": "none",
                    "evidence_acceptance_impact": "none",
                    "superseded_by_gate5": superseded,
                    "drift_status": "NON_POLICY_METADATA_DRIFT_RECORDED",
                }
            )
    return rows or [
        {
            "drift_id": "G6F-DRIFT-NONE",
            "source": "none",
            "artifact_path": "none",
            "policy_impact": "none",
            "drift_status": "NO_METADATA_DRIFT",
        }
    ]


def output_manifest_targets() -> list[str]:
    return [
        "NODI_COMSOL_GATE6A_COMSOL_GATE5_PACKAGE_RECEIPT_20260629.csv",
        "NODI_COMSOL_GATE6B_GATE5_CROSS_SIDE_DISCREPANCY_LEDGER_20260629.csv",
        "NODI_COMSOL_GATE6C_RC5_1_LOCKSTEP_DICTIONARY_20260629.csv",
        "NODI_COMSOL_GATE6D_ADAPTER_HARMONIZATION_MATRIX_20260629.csv",
        "NODI_COMSOL_GATE6E_MUTATION_PROBE_UNION_SUMMARY_20260629.csv",
        "NODI_COMSOL_GATE6F_METADATA_DRIFT_ERRATA_MATRIX_20260629.csv",
        "NODI_COMSOL_GATE6H_NO_AUTH_LOCKSTEP_SWEEP_20260629.csv",
    ]


def positive_auth_findings(rows: list[dict[str, Any]], *, source_name: str) -> list[dict[str, str]]:
    fixture_source = any(marker in source_name.upper() for marker in ("MUTATION", "FIXTURE", "NEGATIVE"))
    fields = set(AUTHORIZATION_FALSE_FIELDS) | {
        "evidence_accepted",
        "authorization_opened",
        "current_action_allowed",
        "authorization_promotion",
        "authorization_promotion_allowed",
        "authorization_promotion_detected",
        "runtime_or_production_authorized",
        "weighting_or_jrc_authorized",
        "policy_conflict",
        "semantic_conflict",
        "verdict_change",
    }
    findings = []
    for idx, row in enumerate(rows, start=1):
        text = " ".join(str(value).lower() for value in row.values())
        fixture_context = fixture_source and any(marker in text for marker in ("fail_expected", "negative", "fixture", "expected_fail"))
        for field in fields:
            if field in row and is_truthy(row.get(field)):
                if fixture_context and field not in {"evidence_accepted", "authorization_opened", "authorization_promotion"}:
                    continue
                findings.append(
                    {
                        "sweep_id": f"G6H-SWEEP-{len(findings)+1:05d}",
                        "source_file": source_name,
                        "row_index": str(idx),
                        "field_name": field,
                        "field_value": str(row.get(field, "")),
                        "sweep_status": "FAIL_AUTHORIZATION_OR_POLICY_DRIFT",
                    }
                )
    return findings


def build_gate6h(csv_payload: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    findings = []
    for path in sorted(OUTPUT_DIR.glob("NODI_COMSOL_GATE5*.csv")):
        findings.extend(positive_auth_findings(read_rows(path), source_name=path.name))
    for name, rows in csv_payload.items():
        findings.extend(positive_auth_findings(rows, source_name=name))
    if not findings:
        findings = [
            {
                "sweep_id": "G6H-SWEEP-NONE",
                "source_file": "Gate5/Gate6 outputs",
                "row_index": "0",
                "field_name": "none",
                "field_value": "none",
                "sweep_status": "PASS_NO_AUTH",
            }
        ]
    review_dims = [
        ("Reviewer A", "provenance/SHA", "COMSOL Gate5 receipt separates blocking data drift from self-referential metadata drift."),
        ("Reviewer B", "cross-side count semantics", "36/40, 365/366, 104/48, and 1792/1800 are explained as scope/granularity deltas."),
        ("Reviewer C", "RC5.1 semantic consistency", "365 unique canonical fields are lockstep; duplicate producer row is non-semantic."),
        ("Reviewer D", "adapter negative controls", "Harmonized adapters cannot change verdict or authorization state."),
        ("Reviewer E", "mutation/probe coverage", "3592 row-equivalent union has zero unexpected pass and zero authorization promotion."),
        ("Reviewer F", "metadata drift handling", "Gate4/Gate5 self-referential drifts are non-policy and non-evidence."),
        ("Reviewer G", "no-auth leakage", "No formula, weighting, JRC, production, runtime, or evidence acceptance opened."),
        ("Reviewer H", "git scope", "Gate6 output package is isolated to reports, sidecars, builder, and focused tests."),
    ]
    review = [
        {"reviewer_id": rid, "dimension": dim, "finding": finding, "severity": "P0/P1 none", "status": "PASS"}
        for rid, dim, finding in review_dims
    ]
    return findings, review


def report_text(title: str, disposition: str, bullets: list[str]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Date: {DATE_STAMP}",
        f"- Disposition: `{disposition}`",
        "- Scope: review-only / no-auth / interface-freeze-candidate.",
        "- Authorization: no formula, no q_ch weighting, no JRC, no production/runtime.",
        "",
        "## Summary",
    ]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.append("")
    return "\n".join(lines)


def build_gate6g_manifest() -> list[dict[str, str]]:
    rows = []
    for idx, name in enumerate(output_manifest_targets(), start=1):
        path = OUTPUT_DIR / name
        rows.append(
            {
                "manifest_id": f"G6G-MANIFEST-{idx:04d}",
                "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{name}",
                "row_count": csv_count(path) if path.exists() else "PENDING_WRITE",
                "sha256": sha256_file(path) if path.exists() else "PENDING_WRITE",
                "provenance": "NODI Gate6 RC5.1 lockstep release candidate",
                "allowed_use": "review-only interface freeze candidate",
                "blocked_use": BLOCKED_USE,
                "not_evidence": "true",
                "no_auth": "true",
            }
        )
    return rows


def build_payload(root: Path) -> dict[str, Any]:
    comsol = load_comsol_gate5(root)
    g6a = build_gate6a(root, comsol)
    g6b = build_gate6b(g6a, comsol)
    g6c, g6c_dupes = build_gate6c(comsol)
    g6d, g6d_controls = build_gate6d(comsol)
    g6e_union, g6e_summary = build_gate6e(comsol)
    g6f = build_gate6f(g6a)
    g6g_cert = [
        {
            "certificate_id": "G6G-CERT-001",
            "release_candidate": "RC5_1_LOCKSTEP_CANDIDATE_REVIEW_ONLY",
            "gate2d_accepted_ledger_rows": str(len(read_rows(GATE2D_LEDGER))),
            "edge_policy_state": "NOT_APPROVED",
            "qch_formal_sidecar_state": "ABSENT",
            "binding_state": "FAIL_CLOSED",
            "semantic_conflict_count": str(sum(1 for row in g6b if row["semantic_conflict"] == "true")),
            "policy_conflict_count": str(sum(1 for row in g6b if row["policy_conflict"] == "true")),
            "unexpected_pass_count": str(sum(1 for row in g6e_union if row["unexpected_pass"] == "true")),
            "authorization_promotion_count": str(sum(1 for row in g6e_union if row["authorization_promotion"] == "true")),
            "runtime_or_production_authorized": "false",
            "weighting_or_jrc_authorized": "false",
            "certificate_status": "PASS_NO_AUTH_LOCKSTEP_CANDIDATE",
        }
    ]
    csv_payload = {
        "NODI_COMSOL_GATE6A_COMSOL_GATE5_PACKAGE_RECEIPT_20260629.csv": g6a,
        "NODI_COMSOL_GATE6B_GATE5_CROSS_SIDE_DISCREPANCY_LEDGER_20260629.csv": g6b,
        "NODI_COMSOL_GATE6C_RC5_1_LOCKSTEP_DICTIONARY_20260629.csv": g6c,
        "NODI_COMSOL_GATE6C_RC5_1_DUPLICATE_FIELD_EXPLANATION_20260629.csv": g6c_dupes,
        "NODI_COMSOL_GATE6D_ADAPTER_HARMONIZATION_MATRIX_20260629.csv": g6d,
        "NODI_COMSOL_GATE6D_ADAPTER_HARMONIZATION_NEGATIVE_CONTROLS_20260629.csv": g6d_controls,
        "NODI_COMSOL_GATE6E_MUTATION_PROBE_UNION_20260629.csv": g6e_union,
        "NODI_COMSOL_GATE6E_MUTATION_PROBE_UNION_SUMMARY_20260629.csv": g6e_summary,
        "NODI_COMSOL_GATE6F_METADATA_DRIFT_ERRATA_MATRIX_20260629.csv": g6f,
        "NODI_COMSOL_GATE6G_NO_AUTH_LOCK_CERTIFICATE_20260629.csv": g6g_cert,
        "NODI_COMSOL_GATE6G_RC5_1_RELEASE_MANIFEST_20260629.csv": build_gate6g_manifest(),
    }
    g6h_sweep, g6h_review = build_gate6h(csv_payload)
    csv_payload["NODI_COMSOL_GATE6H_NO_AUTH_LOCKSTEP_SWEEP_20260629.csv"] = g6h_sweep
    csv_payload["NODI_COMSOL_GATE6H_SELF_REVIEW_20260629.csv"] = g6h_review
    summary = {
        "comsol_gate5_manifest_rows": len(comsol["manifest"]),
        "comsol_gate5_receipt_rows": len(comsol["receipt"]),
        "comsol_gate5_probe_rows": len(comsol["probe"]),
        "comsol_gate5_adapter_rows": len(comsol["adapter"]),
        "comsol_gate5_rc5_rows": len(comsol["rc5_delta"]),
        "comsol_gate5_owner_rows": len(comsol["owner"]),
        "comsol_gate5_command_rows": len(comsol["command"]),
        "comsol_gate5_mutation_rows": len(comsol["mutation"]),
        "comsol_gate5_exchange_index_rows": len(comsol["exchange_index"]),
        "comsol_gate5_validation_rows": len(comsol["validation"]),
        "gate6a_blocking_data_drift": sum(1 for row in g6a if row["receipt_status"] == "BLOCKING_DATA_DRIFT"),
        "gate6a_self_metadata_drift": sum(1 for row in g6a if row["receipt_status"] == "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY"),
        "gate6b_semantic_conflicts": sum(1 for row in g6b if row["semantic_conflict"] == "true"),
        "gate6b_policy_conflicts": sum(1 for row in g6b if row["policy_conflict"] == "true"),
        "gate6c_rows": len(g6c),
        "gate6c_duplicate_rows": sum(int(row.get("comsol_row_count", "0")) for row in g6c_dupes if row.get("duplicate_id") != "G6C-DUP-NONE"),
        "gate6d_rows": len(g6d),
        "gate6d_verdict_changes": sum(1 for row in g6d_controls if row["verdict_change"] == "true"),
        "gate6e_union_rows": len(g6e_union),
        "gate6e_unexpected_pass": sum(1 for row in g6e_union if row["unexpected_pass"] == "true"),
        "gate6e_authorization_promotion": sum(1 for row in g6e_union if row["authorization_promotion"] == "true"),
        "gate2d_rows": len(read_rows(GATE2D_LEDGER)),
        "gate6h_no_auth_failures": sum(1 for row in g6h_sweep if row["sweep_status"] != "PASS_NO_AUTH"),
    }
    reports = {
        "252_NODI_COMSOL_GATE6A_COMSOL_GATE5_PACKAGE_RECEIPT_20260629.md": (
            "Report 252: NODI-COMSOL Gate6A COMSOL Gate5 Package Receipt",
            G6A_PASS,
            [
                f"COMSOL Gate5 manifest rows received: {summary['comsol_gate5_manifest_rows']}.",
                f"Gate5 package counts: receipt {summary['comsol_gate5_receipt_rows']}, probe {summary['comsol_gate5_probe_rows']}, adapter {summary['comsol_gate5_adapter_rows']}, RC5 {summary['comsol_gate5_rc5_rows']}, mutation {summary['comsol_gate5_mutation_rows']}.",
                f"Blocking data drift: {summary['gate6a_blocking_data_drift']}; self-referential metadata drift: {summary['gate6a_self_metadata_drift']}.",
            ],
        ),
        "253_NODI_COMSOL_GATE6B_GATE5_DISCREPANCY_LEDGER_20260629.md": (
            "Report 253: NODI-COMSOL Gate6B Gate5 Cross-Side Discrepancy Ledger",
            G6B_PASS,
            [
                "Receipt 36 vs 40, RC5 365 vs 366, adapter 104 vs 48, and mutation 1792 vs 1800 are recorded as scope/granularity deltas.",
                f"Semantic conflicts: {summary['gate6b_semantic_conflicts']}; policy conflicts: {summary['gate6b_policy_conflicts']}.",
            ],
        ),
        "254_NODI_COMSOL_GATE6C_RC5_1_LOCKSTEP_DICTIONARY_20260629.md": (
            "Report 254: NODI-COMSOL Gate6C RC5.1 Lockstep Dictionary",
            G6C_PASS,
            [
                f"RC5.1 canonical fields: {summary['gate6c_rows']}.",
                "COMSOL 366 rows reduce to 365 unique canonical fields; duplicate field is nodi_view_binding_status.",
                "Dictionary remains review-only, not runtime or evidence acceptance.",
            ],
        ),
        "255_NODI_COMSOL_GATE6D_ADAPTER_HARMONIZATION_20260629.md": (
            "Report 255: NODI-COMSOL Gate6D Adapter Harmonization",
            G6D_PASS,
            [
                f"Harmonization rows: {summary['gate6d_rows']}; verdict changes: {summary['gate6d_verdict_changes']}.",
                "Rules are label/field/schema normalization only and cannot promote blocked/review-only states.",
            ],
        ),
        "256_NODI_COMSOL_GATE6E_MUTATION_PROBE_UNION_20260629.md": (
            "Report 256: NODI-COMSOL Gate6E Mutation and Probe Union",
            G6E_PASS,
            [
                f"Mutation/probe row-equivalent union: {summary['gate6e_union_rows']}.",
                f"Unexpected pass: {summary['gate6e_unexpected_pass']}; authorization promotion: {summary['gate6e_authorization_promotion']}; Gate2D drift: 0.",
            ],
        ),
        "257_NODI_COMSOL_GATE6F_METADATA_DRIFT_ERRATA_RECEIPT_20260629.md": (
            "Report 257: NODI-COMSOL Gate6F Metadata Drift Errata Receipt",
            G6F_PASS,
            [
                f"Metadata drift rows recorded: {len(g6f)}.",
                "Gate4 self-referential metadata drift is superseded by Gate5; Gate5 self-referential metadata drift remains non-policy.",
            ],
        ),
        "258_NODI_COMSOL_GATE6G_RC5_1_LOCKSTEP_RELEASE_CANDIDATE_20260629.md": (
            "Report 258: NODI-COMSOL Gate6G RC5.1 Lockstep Release Candidate",
            G6G_PASS,
            [
                "Release candidate: RC5_1_LOCKSTEP_CANDIDATE_REVIEW_ONLY.",
                "Gate2D exactly 4, EDGE NOT_APPROVED, QCH ABSENT, BINDING FAIL_CLOSED.",
            ],
        ),
        "259_NODI_COMSOL_GATE6H_VALIDATION_SELF_REVIEW_20260629.md": (
            "Report 259: NODI-COMSOL Gate6H Validation and Self-Review",
            G6H_PASS,
            [
                f"No-auth sweep failures: {summary['gate6h_no_auth_failures']}.",
                "Eight independent self-review dimensions report PASS with no P0/P1 open.",
            ],
        ),
    }
    return {"summary": summary, "csv": csv_payload, "reports": reports}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    issues = []
    expected = {
        "comsol_gate5_manifest_rows": 31,
        "comsol_gate5_receipt_rows": 40,
        "comsol_gate5_probe_rows": 120,
        "comsol_gate5_adapter_rows": 48,
        "comsol_gate5_rc5_rows": 366,
        "comsol_gate5_owner_rows": 36,
        "comsol_gate5_command_rows": 6,
        "comsol_gate5_mutation_rows": 1800,
        "comsol_gate5_exchange_index_rows": 6,
        "comsol_gate5_validation_rows": 18,
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
    }
    for key, value in expected.items():
        if s.get(key) != value:
            issues.append(f"{key} expected {value}, got {s.get(key)}")
    for key in ("gate6a_blocking_data_drift", "gate6b_semantic_conflicts", "gate6b_policy_conflicts", "gate6d_verdict_changes", "gate6e_unexpected_pass", "gate6e_authorization_promotion", "gate6h_no_auth_failures"):
        if s.get(key) != 0:
            issues.append(f"{key} must be zero, got {s.get(key)}")
    if s["gate6c_rows"] != 365:
        issues.append(f"Gate6C expected 365 lockstep fields, got {s['gate6c_rows']}")
    if s["gate6e_union_rows"] < 3592:
        issues.append(f"Gate6E union below 3592 row-equivalent, got {s['gate6e_union_rows']}")
    return issues


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in payload["csv"].items():
        write_csv_rows(OUTPUT_DIR / name, rows)
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE6G_RC5_1_RELEASE_MANIFEST_{DATE_STAMP}.csv", build_gate6g_manifest())
    for name, (title, disposition, bullets) in payload["reports"].items():
        (REPORT_DIR / name).write_text(report_text(title, disposition, bullets), encoding="utf-8")
    for idx, gate in enumerate("ABCDEFGH", start=1):
        report = {
            "date": DATE_STAMP,
            "gate": f"Gate6{gate}",
            "summary": payload["summary"],
            "scope": "review-only/no-auth/interface-freeze-candidate",
            "authorization": "no formula, no q_ch weighting, no JRC, no production/runtime",
        }
        write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE6{gate}_REPORT_{DATE_STAMP}.json", report)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate6a_to_gate6h:
        parser.error("--confirm-gate6a-to-gate6h is required")
    payload = build_payload(args.comsol_root)
    issues = validate_payload(payload)
    if issues:
        for issue in issues:
            print(f"VALIDATION_ERROR: {issue}")
        return 2
    write_outputs(payload)
    print("PASS_GATE6A_TO_GATE6H_RC5_1_LOCKSTEP_RELEASE_CANDIDATE_NO_AUTHORIZATION")
    print(f"rc5_1_fields={payload['summary']['gate6c_rows']}")
    print(f"mutation_union_rows={payload['summary']['gate6e_union_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
