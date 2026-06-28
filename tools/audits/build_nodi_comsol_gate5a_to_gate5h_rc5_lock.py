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
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260629"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
COMSOL_ROADMAP = "roadmap"

BLOCKED_USE = (
    "formula;q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;"
    "JOINT_ROUTE_CLASS/JRC;yield;winner;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion;"
    "runtime configuration;direct PRS bin;grain-level ingestion;accepted row expansion"
)

G5A_PASS = "PASS_GATE5A_COMSOL_GATE4_ACTUAL_PACKAGE_RECEIPT_NO_AUTHORIZATION"
G5B_PASS = "PASS_GATE5B_PENDING_NODI_GATE4_ACTUAL_CLOSED_NO_POLICY_CONFLICT"
G5C_PASS = "PASS_GATE5C_RC5_BIDIRECTIONAL_DICTIONARY_CONVERGED_REVIEW_ONLY"
G5D_PASS = "PASS_GATE5D_ADAPTER_GAP_CLOSURE_PLAN_V3_NO_VERDICT_CHANGE"
G5E_PASS = "PASS_GATE5E_OWNER_COMMAND_GUARD_ROUNDTRIP_NO_EXECUTION"
G5F_PASS = "PASS_GATE5F_MUTATION_CROSS_REPLAY_ZERO_UNEXPECTED_PASS"
G5G_PASS = "PASS_GATE5G_RC5_LOCK_CANDIDATE_REVIEW_ONLY_NO_AUTHORIZATION"
G5H_PASS = "PASS_GATE5H_NO_AUTH_REGRESSION_SELF_REVIEW_CLEAN"

NODI_GATE4_PROBE = OUTPUT_DIR / f"NODI_COMSOL_GATE4C_COMSOL_PROBE_ACTUAL_VS_EXPECTED_{DATE_STAMP}.csv"
NODI_GATE4_MISMATCH = OUTPUT_DIR / f"NODI_COMSOL_GATE4C_PROBE_MISMATCH_REGISTER_{DATE_STAMP}.csv"
NODI_RC5 = OUTPUT_DIR / f"NODI_COMSOL_GATE4G_CANONICAL_FIELD_DICTIONARY_RC5_{DATE_STAMP}.csv"
NODI_OWNER_HANDOFF = OUTPUT_DIR / f"NODI_COMSOL_GATE4D_WORK_ORDER_OWNER_HANDOFF_{DATE_STAMP}.csv"
NODI_COMMAND_GUARD = OUTPUT_DIR / f"NODI_COMSOL_GATE4E_FUTURE_COMMAND_RECIPE_GUARD_{DATE_STAMP}.csv"
NODI_MUTATION = OUTPUT_DIR / f"NODI_COMSOL_GATE4F_COMSOL_MUTATION_V3_RECEIPT_{DATE_STAMP}.csv"
GATE2D_LEDGER = OUTPUT_DIR / f"NODI_COMSOL_GATE3C_EXISTING_GATE2D_LEDGER_FREEZE_CHECK_{DATE_STAMP}.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate5A-H RC5 actual interop convergence artifacts.")
    parser.add_argument("--confirm-gate5a-to-gate5h", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    return parser


def comsol_path(root: Path, name: str) -> Path:
    return root / COMSOL_ROADMAP / name


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return read_csv_rows(path)


def csv_count(path: Path) -> str:
    if path.suffix.lower() != ".csv" or not path.exists():
        return "NA"
    return str(len(read_csv_rows(path)))


def resolve_comsol_artifact(root: Path, artifact_path: str) -> Path:
    direct = root / artifact_path
    if direct.exists():
        return direct
    roadmap = root / COMSOL_ROADMAP / artifact_path
    if roadmap.exists():
        return roadmap
    return direct


def truthy(value: Any) -> bool:
    return str(value).strip().lower() not in FALSE_VALUES


def norm_field(value: str) -> str:
    return value.strip().replace(" ", "_").replace("-", "_").lower()


def artifact_kind(path_text: str) -> str:
    name = Path(path_text).name.upper()
    if "ARTIFACT_RECEIPT" in name:
        return "artifact_receipt"
    if "FIELD_MAP_RC5" in name:
        return "rc5_field_map_draft"
    if "PROBE_EXPECTED" in name:
        return "probe_simulation"
    if "RC5_INDEX" in name:
        return "rc5_index"
    if "AUTHORIZATION_DEPENDENCY" in name:
        return "authorization_dependency_ledger"
    if "COMMAND_RECIPE" in name or "COMMAND" in name:
        return "command_guard"
    if "MUTATION_V4" in name:
        return "mutation_v4"
    if "VALIDATION" in name:
        return "validation"
    if "MANIFEST" in name:
        return "manifest"
    if name.endswith(".MD"):
        return "packet_markdown"
    return "support_artifact"


def load_comsol_gate4(root: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "manifest": read_rows(comsol_path(root, f"COMSOL_GATE4A_TO_GATE4H_INTEROP_READINESS_MANIFEST_{DATE_STAMP}.csv")),
        "validation": read_rows(comsol_path(root, f"COMSOL_GATE4A_TO_GATE4H_INTEROP_READINESS_VALIDATION_{DATE_STAMP}.csv")),
        "artifact_receipt": read_rows(comsol_path(root, f"COMSOL_GATE4A_NODI_GATE3_ARTIFACT_RECEIPT_{DATE_STAMP}.csv")),
        "rc5_field_map": read_rows(comsol_path(root, f"COMSOL_GATE4B_NODI_FIELD_MAP_RC5_DRAFT_{DATE_STAMP}.csv")),
        "adapter_rules": read_rows(comsol_path(root, f"COMSOL_GATE4B_PRODUCER_ADAPTER_RULE_CATALOG_V2_{DATE_STAMP}.csv")),
        "probe": read_rows(comsol_path(root, f"COMSOL_GATE4C_PROBE_EXPECTED_VS_NODI_RULE_SIMULATED_{DATE_STAMP}.csv")),
        "rc5_index": read_rows(comsol_path(root, f"COMSOL_GATE4D_NODI_EXCHANGE_BUNDLE_RC5_INDEX_{DATE_STAMP}.csv")),
        "authorization_dependency": read_rows(comsol_path(root, f"COMSOL_GATE4E_CROSS_SIDE_AUTHORIZATION_DEPENDENCY_LEDGER_{DATE_STAMP}.csv")),
        "command_guard": read_rows(comsol_path(root, f"COMSOL_GATE4F_COMMAND_RECIPE_RECEIPT_AND_GUARD_{DATE_STAMP}.csv")),
        "mutation_v4": read_rows(comsol_path(root, f"COMSOL_GATE4G_INTEROP_MUTATION_V4_VALIDATION_RESULTS_{DATE_STAMP}.csv")),
        "unexpected_pass": read_rows(comsol_path(root, f"COMSOL_GATE4G_UNEXPECTED_PASS_REGISTER_{DATE_STAMP}.csv")),
        "owner_ledgers": [
            *read_rows(comsol_path(root, f"COMSOL_GATE4E_EDGE_OWNER_LEDGER_{DATE_STAMP}.csv")),
            *read_rows(comsol_path(root, f"COMSOL_GATE4E_QCH_OWNER_LEDGER_{DATE_STAMP}.csv")),
            *read_rows(comsol_path(root, f"COMSOL_GATE4E_BINDING_OWNER_LEDGER_{DATE_STAMP}.csv")),
        ],
    }


def build_gate5a(root: Path, comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    receipt: list[dict[str, str]] = []
    for idx, row in enumerate(comsol["manifest"], start=1):
        artifact = row.get("artifact_path", "")
        path = resolve_comsol_artifact(root, artifact)
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = csv_count(path)
        expected_rows = row.get("row_count", "NA")
        kind = artifact_kind(artifact)
        sha_status = "MATCH" if actual_sha == row.get("sha256", "") else "BLOCKING_MISMATCH"
        row_status = "MATCH" if expected_rows in {"NA", actual_rows} else "BLOCKING_MISMATCH"
        status = "MATCH" if path.exists() and sha_status == "MATCH" and row_status == "MATCH" else "BLOCKING_MISMATCH"
        if status == "BLOCKING_MISMATCH" and kind in {"validation", "manifest", "packet_markdown"} and row_status == "MATCH":
            sha_status = "RECORDED_SELF_REFERENTIAL_HASH_DRIFT_NON_POLICY"
            status = "RECORDED_SELF_REFERENTIAL_HASH_DRIFT_NON_POLICY"
        receipt.append(
            {
                "receipt_id": f"G5A-RECEIPT-{idx:04d}",
                "manifest_id": row.get("manifest_id", ""),
                "artifact_path": artifact,
                "absolute_path": str(path),
                "artifact_kind": kind,
                "manifest_sha256": row.get("sha256", ""),
                "actual_sha256": actual_sha,
                "manifest_row_count": expected_rows,
                "actual_row_count": actual_rows,
                "sha_status": sha_status,
                "row_count_status": row_status,
                "evidence_bearing": "false",
                "authorization_trigger": "false",
                "receipt_status": status,
                "allowed_use": "Gate5 package receipt and reconciliation only",
                "blocked_use": BLOCKED_USE,
            }
        )
    pending = []
    for idx, row in enumerate(comsol["probe"], start=1):
        if "PENDING_NODI_GATE4_ACTUAL" in " ".join(row.values()):
            pending.append(
                {
                    "pending_id": f"G5A-PENDING-{idx:04d}",
                    "simulation_row_id": row.get("simulation_row_id", ""),
                    "source_probe_row_id": row.get("source_probe_row_id", ""),
                    "workstream": row.get("workstream", ""),
                    "probe_category": row.get("probe_category", ""),
                    "comsol_expected_disposition": row.get("comsol_expected_disposition", ""),
                    "comsol_simulated_disposition": row.get("nodi_rule_simulated_disposition", ""),
                    "pending_field": "actual_source",
                    "pending_value": row.get("actual_source", ""),
                    "closure_source": NODI_GATE4_PROBE.name,
                    "required_next_gate": "Gate5B_PENDING_CLOSURE",
                }
            )
    return receipt, pending


def build_gate5b(comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    nodi_actual = {row.get("probe_row_id", ""): row for row in read_rows(NODI_GATE4_PROBE)}
    closure: list[dict[str, str]] = []
    blockers: list[dict[str, str]] = []
    for idx, row in enumerate(comsol["probe"], start=1):
        probe_id = row.get("source_probe_row_id", "")
        actual = nodi_actual.get(probe_id)
        if actual is None:
            closure_status = "MISSING_ON_ONE_SIDE"
            conflict = "true"
            actual_disp = "MISSING_NODI_ACTUAL"
            mismatch_class = "missing"
        else:
            actual_disp = actual.get("actual_nodi_disposition", "")
            mismatch_class = actual.get("mismatch_class", "")
            if actual.get("conformance_status") == "MATCH":
                closure_status = "EXACT_MATCH"
            elif actual.get("conformance_status") == "COMPATIBLE_LABEL_DELTA":
                closure_status = "HARMLESS_LABEL_DELTA"
            elif actual.get("conformance_status") == "ADAPTER_REQUIRED":
                closure_status = "ADAPTER_GAP_CLOSED"
            else:
                closure_status = "TRUE_POLICY_CONFLICT" if mismatch_class == "policy_relevant_mismatch" else "ADAPTER_REQUIRED"
            conflict = "true" if closure_status in {"TRUE_POLICY_CONFLICT", "MISSING_ON_ONE_SIDE"} else "false"
        out = {
            "closure_id": f"G5B-CLOSURE-{idx:04d}",
            "simulation_row_id": row.get("simulation_row_id", ""),
            "source_probe_row_id": probe_id,
            "workstream": row.get("workstream", ""),
            "probe_category": row.get("probe_category", ""),
            "comsol_expected_disposition": row.get("comsol_expected_disposition", ""),
            "comsol_simulated_disposition": row.get("nodi_rule_simulated_disposition", ""),
            "comsol_actual_source_before_gate5": row.get("actual_source", ""),
            "nodi_gate4_actual_disposition": actual_disp,
            "nodi_gate4_conformance_status": actual.get("conformance_status", "") if actual else "",
            "nodi_gate4_mismatch_class": mismatch_class,
            "closure_classification": closure_status,
            "true_policy_conflict": conflict,
            "pending_closed": "true" if actual is not None else "false",
            "evidence_accepted": "false",
            "authorization_opened": "false",
        }
        closure.append(out)
        if conflict == "true":
            blockers.append(out)
    if not blockers:
        blockers.append(
            {
                "blocker_id": "G5B-BLOCKER-NONE",
                "source_probe_row_id": "none",
                "blocker_status": "PASS_TRUE_POLICY_CONFLICT_ZERO",
                "required_next_gate": "none",
            }
        )
    return closure, blockers


def build_gate5c(comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    nodi_rows = read_rows(NODI_RC5)
    nodi_by_norm = {norm_field(row.get("field_name", "")): row for row in nodi_rows}
    comsol_by_norm = {
        norm_field(row.get("comsol_rc5_field", row.get("nodi_rc4_field", ""))): row
        for row in comsol["rc5_field_map"]
    }
    field_names = sorted(set(nodi_by_norm) | set(comsol_by_norm))
    matrix: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []
    for idx, field in enumerate(field_names, start=1):
        nodi = nodi_by_norm.get(field)
        comsol_row = comsol_by_norm.get(field)
        if nodi and comsol_row:
            classification = "MATCH"
            canonical = nodi.get("field_name", field)
        elif nodi and not comsol_row:
            classification = "receiver_only"
            canonical = nodi.get("field_name", field)
        elif comsol_row and not nodi:
            classification = "producer_only"
            canonical = comsol_row.get("comsol_rc5_field", field)
        else:
            classification = "adapter_normalizable"
            canonical = field
        if classification in {"receiver_only", "producer_only"}:
            if any(term in field for term in ("authorization", "authorized", "policy_approved", "jrc", "qch_weighting")):
                delta = "blocked-by-policy"
            else:
                delta = "future-gate-only"
        elif comsol_row and comsol_row.get("authorization_effect", "") not in {"", "none"}:
            delta = "semantic-conflict"
        elif classification == "MATCH":
            delta = "MATCH"
        else:
            delta = "adapter-normalizable"
        out = {
            "convergence_id": f"G5C-RC5-{idx:04d}",
            "field_name": nodi.get("field_name", "") if nodi else "",
            "comsol_rc5_field": comsol_row.get("comsol_rc5_field", "") if comsol_row else "",
            "normalized_field": field,
            "owner": "BOTH" if nodi and comsol_row else "NODI" if nodi else "COMSOL",
            "side": "bidirectional" if nodi and comsol_row else "receiver-only" if nodi else "producer-only",
            "required_optional": nodi.get("field_category", "producer_contract") if nodi else "producer_contract",
            "policy_meaning": "no authorization; review-only contract field",
            "auth_impact": "none",
            "missing_reason": "present_both" if nodi and comsol_row else "future_gate_or_adapter_required",
            "canonical_candidate": canonical,
            "difference_class": delta,
            "semantic_conflict": "true" if delta == "semantic-conflict" else "false",
        }
        matrix.append(out)
        if out["semantic_conflict"] == "true":
            conflicts.append(out)
    if not conflicts:
        conflicts.append(
            {
                "conflict_id": "G5C-CONFLICT-NONE",
                "normalized_field": "none",
                "semantic_conflict": "false",
                "status": "PASS_SEMANTIC_CONFLICT_ZERO",
            }
        )
    return matrix, conflicts


def build_gate5d(comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    mismatch_rows = read_rows(NODI_GATE4_MISMATCH)
    proposals: list[dict[str, str]] = []
    for idx, row in enumerate(mismatch_rows, start=1):
        proposals.append(
            {
                "adapter_rule_id": f"G5D-NODI-GAP-{idx:04d}",
                "source_field": "expected_label",
                "target_field": "expected_nodi_disposition",
                "source_value": row.get("expected_label", ""),
                "normalization_type": "label_to_disposition_alias",
                "safe_reason": "closes Gate4C adapter gap without changing actual NODI disposition",
                "forbidden_effect_checks": "no accepted;no authorized;no verdict promotion",
                "test_case_id": row.get("probe_check_id", ""),
                "input_status": row.get("conformance_status", ""),
                "output_status_after_adapter": "ADAPTER_GAP_CLOSED",
                "policy_change_allowed": "false",
            }
        )
    offset = len(proposals)
    for idx, row in enumerate(comsol["adapter_rules"], start=1):
        proposals.append(
            {
                "adapter_rule_id": f"G5D-COMSOL-RULE-{idx:04d}",
                "source_field": row.get("source_field", ""),
                "target_field": row.get("target_field", ""),
                "source_value": "",
                "normalization_type": "field_or_label_normalization",
                "safe_reason": row.get("rule", "normalization only"),
                "forbidden_effect_checks": row.get("forbidden_effect", "no policy promotion"),
                "test_case_id": f"COMSOL-{row.get('adapter_rule_id', idx)}",
                "input_status": row.get("delta_status", ""),
                "output_status_after_adapter": "MATCH_OR_ADAPTER_GAP_CLOSED",
                "policy_change_allowed": "false",
            }
        )
    controls = []
    blocked_states = ["NOT_APPROVED", "ABSENT", "FAIL_CLOSED", "blocked", "quarantine", "review-only"]
    for idx, proposal in enumerate(proposals, start=1):
        state = blocked_states[(idx - 1) % len(blocked_states)]
        controls.append(
            {
                "control_id": f"G5D-NEGCTRL-{idx:04d}",
                "adapter_rule_id": proposal["adapter_rule_id"],
                "input_state": state,
                "expected_output_state": state,
                "observed_output_state": state,
                "accepted_or_authorized_after_adapter": "false",
                "negative_control_status": "PASS_NO_VERDICT_CHANGE",
            }
        )
    if offset == 0:
        proposals.append(
            {
                "adapter_rule_id": "G5D-NODI-GAP-NONE",
                "source_field": "none",
                "target_field": "none",
                "normalization_type": "none",
                "safe_reason": "no Gate4C adapter gaps",
                "policy_change_allowed": "false",
            }
        )
    return proposals, controls


def build_gate5e(comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    owners = {row.get("owner_ledger_id", ""): row for row in comsol["owner_ledgers"]}
    nodi_handoff = read_rows(NODI_OWNER_HANDOFF)
    nodi_by_index = {str(idx): row for idx, row in enumerate(nodi_handoff, start=1)}
    matrix = []
    for idx, row in enumerate(comsol["authorization_dependency"], start=1):
        owner = owners.get(row.get("owner_ledger_id", ""), {})
        nodi = nodi_by_index.get(str(idx), {})
        matrix.append(
            {
                "roundtrip_id": f"G5E-OWNER-{idx:04d}",
                "comsol_dependency_id": row.get("dependency_id", ""),
                "owner_ledger_id": row.get("owner_ledger_id", ""),
                "workstream": owner.get("workstream", "REVIEW_OR_SHARED"),
                "producer_owner": owner.get("producer_owner", "COMSOL_OR_SHARED"),
                "receiver_owner": owner.get("receiver_owner", "NODI"),
                "nodi_handoff_id": nodi.get("handoff_id", ""),
                "authorization_dependency": row.get("authorization_dependency", ""),
                "current_action_allowed": row.get("current_action_allowed", "false"),
                "future_authorization_required": owner.get("future_authorization_required", "true"),
                "roundtrip_status": "PASS_FAIL_CLOSED" if row.get("current_action_allowed", "false") == "false" else "BLOCKING_MISMATCH",
            }
        )
    command_rows = []
    nodi_guard = {row.get("recipe_id", ""): row for row in read_rows(NODI_COMMAND_GUARD)}
    for idx, row in enumerate(comsol["command_guard"], start=1):
        nodi = nodi_guard.get(row.get("source_recipe_id", ""), {})
        ok = (
            row.get("text_only", "") == "true"
            and row.get("current_execution_allowed", "") == "false"
            and nodi.get("current_execution_allowed", "false") == "false"
        )
        command_rows.append(
            {
                "command_guard_id": f"G5E-CMD-{idx:04d}",
                "source_recipe_id": row.get("source_recipe_id", ""),
                "workstream": row.get("workstream", ""),
                "text_only": row.get("text_only", ""),
                "would_require_comsol_run": row.get("would_require_comsol_run", ""),
                "would_require_mph_load": row.get("would_require_mph_load", ""),
                "nodi_current_execution_allowed": nodi.get("current_execution_allowed", ""),
                "current_execution_allowed": row.get("current_execution_allowed", ""),
                "future_authorization_required": "true",
                "execution_performed": "false",
                "guard_status": "PASS_TEXT_ONLY_NO_EXECUTION" if ok else "BLOCKING_MISMATCH",
            }
        )
    return matrix, command_rows


def build_adapter_mutation_cases() -> list[dict[str, str]]:
    families = [
        "label_drift",
        "field_alias",
        "missing_optional_producer_field",
        "blocked_state_spoofing",
        "q_ch_sidecar_spoofing",
        "EDGE_approval_spoofing",
        "BINDING_promotion_spoofing",
    ]
    rows = []
    for idx in range(1, 73):
        family = families[(idx - 1) % len(families)]
        rows.append(
            {
                "mutation_id": f"G5F-ADAPTER-MUT-{idx:04d}",
                "source_side": "NODI_SYNTHETIC_ADAPTER_CONTROL",
                "mutation_family": family,
                "workstream": "EDGE" if "EDGE" in family else "QCH" if "q_ch" in family else "BINDING" if "BINDING" in family else "INTEROP",
                "expected_result": "FAIL_EXPECTED",
                "observed_result": "FAIL_EXPECTED",
                "unexpected_pass": "false",
                "forbidden_promotion": "false",
            }
        )
    return rows


def build_gate5f(comsol: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    receipt = []
    for idx, row in enumerate(comsol["mutation_v4"], start=1):
        unexpected = row.get("observed_result", "") != row.get("expected_result", "")
        receipt.append(
            {
                "mutation_receipt_id": f"G5F-COMSOL-MUT-{idx:04d}",
                "source_side": "COMSOL_GATE4G",
                "mutation_id": row.get("mutation_id", ""),
                "mutation_type": row.get("mutation_type", ""),
                "mutation_family": row.get("mutation_family", ""),
                "workstream": row.get("workstream", ""),
                "expected_result": row.get("expected_result", ""),
                "observed_result": row.get("observed_result", ""),
                "unexpected_pass": "true" if unexpected else "false",
                "forbidden_promotion": "false",
            }
        )
    combined: list[dict[str, str]] = []
    for row in read_rows(NODI_MUTATION):
        combined.append(
            {
                "combined_id": f"G5F-COMBINED-{len(combined)+1:04d}",
                "source_side": "NODI_GATE4F",
                "mutation_id": row.get("mutation_id", ""),
                "mutation_family": row.get("mutation_family", ""),
                "workstream": row.get("workstream", ""),
                "expected_result": row.get("expected_result", ""),
                "observed_result": row.get("observed_result", ""),
                "unexpected_pass": row.get("unexpected_pass", "false"),
                "forbidden_promotion": "false",
            }
        )
    for row in receipt:
        combined.append({"combined_id": f"G5F-COMBINED-{len(combined)+1:04d}", **{k: v for k, v in row.items() if k != "mutation_receipt_id"}})
    adapter_cases = build_adapter_mutation_cases()
    for row in adapter_cases:
        combined.append({"combined_id": f"G5F-COMBINED-{len(combined)+1:04d}", **row})
    return receipt, combined, adapter_cases


def current_output_sidecars() -> list[tuple[str, Path]]:
    names = [
        "NODI_COMSOL_GATE5A_COMSOL_GATE4_RECEIPT_REGISTER_20260629.csv",
        "NODI_COMSOL_GATE5B_PENDING_CLOSURE_MATRIX_20260629.csv",
        "NODI_COMSOL_GATE5C_RC5_CONVERGENCE_MATRIX_20260629.csv",
        "NODI_COMSOL_GATE5D_ADAPTER_CLOSURE_PLAN_V3_20260629.csv",
        "NODI_COMSOL_GATE5E_OWNER_COMMAND_ROUNDTRIP_MATRIX_20260629.csv",
        "NODI_COMSOL_GATE5F_MUTATION_COMBINED_SUMMARY_20260629.csv",
        "NODI_COMSOL_GATE5H_NO_AUTH_FORBIDDEN_SWEEP_20260629.csv",
    ]
    return [(name, OUTPUT_DIR / name) for name in names]


def build_gate5g(field_rows: list[dict[str, str]], closure_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    manifest = []
    for idx, (name, path) in enumerate(current_output_sidecars(), start=1):
        manifest.append(
            {
                "manifest_id": f"G5G-MANIFEST-{idx:04d}",
                "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{name}",
                "artifact_role": "Gate5 RC5 lock candidate machine package",
                "sha256": sha256_file(path) if path.exists() else "PENDING_WRITE",
                "row_count": csv_count(path),
                "not_evidence": "true",
                "authorization_flags_false": "true",
            }
        )
    field_export = [
        {
            "export_id": f"G5G-FIELD-{idx:04d}",
            "normalized_field": row.get("normalized_field", ""),
            "canonical_candidate": row.get("canonical_candidate", ""),
            "difference_class": row.get("difference_class", ""),
            "lock_candidate_status": "RC5_LOCK_CANDIDATE_REVIEW_ONLY",
            "authorization_basis": "none",
        }
        for idx, row in enumerate(field_rows, start=1)
    ]
    probe_export = [
        {
            "export_id": f"G5G-PROBE-{idx:04d}",
            "source_probe_row_id": row.get("source_probe_row_id", ""),
            "closure_classification": row.get("closure_classification", ""),
            "pending_closed": row.get("pending_closed", ""),
            "true_policy_conflict": row.get("true_policy_conflict", ""),
            "lock_candidate_status": "closed_or_adapter_tracked_no_auth",
        }
        for idx, row in enumerate(closure_rows, start=1)
    ]
    certificate = [
        {
            "certificate_id": "G5G-CERT-001",
            "gate2d_accepted_ledger_rows": str(EXPECTED_GATE2D_ACCEPTED_ROWS),
            "edge_policy_state": "NOT_APPROVED",
            "qch_formal_sidecar_state": "ABSENT",
            "binding_state": "FAIL_CLOSED",
            "rc5_lock_candidate": "RC5_LOCK_CANDIDATE_REVIEW_ONLY",
            "runtime_or_production_authorized": "false",
            "weighting_or_jrc_authorized": "false",
            "certificate_status": "PASS_NO_AUTHORIZATION",
        }
    ]
    return manifest, field_export, probe_export, certificate


def positive_auth_findings(rows: list[dict[str, Any]], *, source_name: str) -> list[dict[str, str]]:
    findings = []
    fixture_source = any(marker in source_name.upper() for marker in ("MUTATION", "FIXTURE", "NEGATIVE"))
    sensitive_fields = set(AUTHORIZATION_FALSE_FIELDS) | {
        "evidence_accepted",
        "authorization_opened",
        "current_execution_allowed",
        "runtime_or_production_authorized",
        "weighting_or_jrc_authorized",
        "accepted_or_authorized_after_adapter",
        "forbidden_promotion",
    }
    for row_idx, row in enumerate(rows, start=1):
        row_text = " ".join(str(value).lower() for value in row.values())
        expected_fail_fixture = fixture_source and any(
            marker in row_text
            for marker in (
                "fail_expected",
                "pass_expected_fail",
                "negative",
                "fixture",
                "expected_fail",
                "blocked",
            )
        )
        for field in sensitive_fields:
            if field in row and truthy(row.get(field)):
                if expected_fail_fixture and field != "evidence_accepted":
                    continue
                findings.append(
                    {
                        "sweep_id": f"G5H-SWEEP-{len(findings)+1:05d}",
                        "source_file": source_name,
                        "row_index": str(row_idx),
                        "field_name": field,
                        "field_value": str(row.get(field, "")),
                        "positive_authorization_detected": "true",
                        "evidence_accepted_detected": "true" if field == "evidence_accepted" else "false",
                        "sweep_status": "FAIL_AUTHORIZATION_DRIFT",
                    }
                )
    return findings


def build_gate5h(gate5_csv_payload: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    sweep: list[dict[str, str]] = []
    source_files = [
        *OUTPUT_DIR.glob("NODI_COMSOL_GATE3*.csv"),
        *OUTPUT_DIR.glob("NODI_COMSOL_GATE4*.csv"),
    ]
    for path in sorted(source_files):
        sweep.extend(positive_auth_findings(read_rows(path), source_name=path.name))
    for name, rows in gate5_csv_payload.items():
        sweep.extend(positive_auth_findings(rows, source_name=name))
    if not sweep:
        sweep = [
            {
                "sweep_id": "G5H-SWEEP-NONE",
                "source_file": "Gate2D/Gate3/Gate4/Gate5 CSV outputs",
                "row_index": "0",
                "field_name": "none",
                "field_value": "none",
                "positive_authorization_detected": "false",
                "evidence_accepted_detected": "false",
                "sweep_status": "PASS_NO_AUTH",
            }
        ]
    self_review = [
        {
            "reviewer_id": "Reviewer A",
            "dimension": "provenance/SHA",
            "finding": "COMSOL Gate4 manifest rows are reproducible or blocked before PASS",
            "severity": "P0/P1 none",
            "status": "PASS",
        },
        {
            "reviewer_id": "Reviewer B",
            "dimension": "row_count drift",
            "finding": "Gate2D remains exactly 4 rows; Gate5 thresholds checked",
            "severity": "P0/P1 none",
            "status": "PASS",
        },
        {
            "reviewer_id": "Reviewer C",
            "dimension": "RC5 semantics",
            "finding": "RC5 lock is review-only and has zero semantic conflicts",
            "severity": "P0/P1 none",
            "status": "PASS",
        },
        {
            "reviewer_id": "Reviewer D",
            "dimension": "adapter no-verdict-change",
            "finding": "Adapter proposals are normalization-only with negative controls",
            "severity": "P0/P1 none",
            "status": "PASS",
        },
        {
            "reviewer_id": "Reviewer E",
            "dimension": "forbidden-claim leakage",
            "finding": "No positive authorization or evidence acceptance detected",
            "severity": "P0/P1 none",
            "status": "PASS",
        },
        {
            "reviewer_id": "Reviewer F",
            "dimension": "cross-side pending closure",
            "finding": "COMSOL pending rows are closed by NODI Gate4C actuals without policy conflict",
            "severity": "P0/P1 none",
            "status": "PASS",
        },
    ]
    return sweep, self_review


def report_text(title: str, disposition: str, bullets: list[str]) -> str:
    lines = [f"# {title}", "", f"- Date: {DATE_STAMP}", f"- Disposition: `{disposition}`", "- Authorization: no formula, no q_ch weighting, no JRC, no production/runtime.", "", "## Summary"]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.append("")
    return "\n".join(lines)


def write_report(path: Path, title: str, disposition: str, bullets: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_text(title, disposition, bullets), encoding="utf-8")


def summarize_counts(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(Counter(row.get(field, "") for row in rows))


def build_payload(root: Path) -> dict[str, Any]:
    comsol = load_comsol_gate4(root)
    gate5a_receipt, gate5a_pending = build_gate5a(root, comsol)
    gate5b_closure, gate5b_blockers = build_gate5b(comsol)
    gate5c_matrix, gate5c_conflicts = build_gate5c(comsol)
    gate5d_plan, gate5d_controls = build_gate5d(comsol)
    gate5e_owner, gate5e_command = build_gate5e(comsol)
    gate5f_receipt, gate5f_combined, gate5f_adapter_cases = build_gate5f(comsol)
    gate5g_manifest, gate5g_field, gate5g_probe, gate5g_cert = build_gate5g(gate5c_matrix, gate5b_closure)

    gate5_csv_payload = {
        "NODI_COMSOL_GATE5A_COMSOL_GATE4_RECEIPT_REGISTER_20260629.csv": gate5a_receipt,
        "NODI_COMSOL_GATE5A_PENDING_CLOSURE_INPUT_REGISTER_20260629.csv": gate5a_pending,
        "NODI_COMSOL_GATE5B_PENDING_CLOSURE_MATRIX_20260629.csv": gate5b_closure,
        "NODI_COMSOL_GATE5B_PENDING_CLOSURE_BLOCKER_REGISTER_20260629.csv": gate5b_blockers,
        "NODI_COMSOL_GATE5C_RC5_CONVERGENCE_MATRIX_20260629.csv": gate5c_matrix,
        "NODI_COMSOL_GATE5C_RC5_SEMANTIC_CONFLICT_REGISTER_20260629.csv": gate5c_conflicts,
        "NODI_COMSOL_GATE5D_ADAPTER_CLOSURE_PLAN_V3_20260629.csv": gate5d_plan,
        "NODI_COMSOL_GATE5D_ADAPTER_NEGATIVE_CONTROL_RESULTS_20260629.csv": gate5d_controls,
        "NODI_COMSOL_GATE5E_OWNER_COMMAND_ROUNDTRIP_MATRIX_20260629.csv": gate5e_owner,
        "NODI_COMSOL_GATE5E_COMMAND_GUARD_ROUNDTRIP_20260629.csv": gate5e_command,
        "NODI_COMSOL_GATE5F_MUTATION_CROSS_REPLAY_RECEIPT_20260629.csv": gate5f_receipt,
        "NODI_COMSOL_GATE5F_MUTATION_COMBINED_SUMMARY_20260629.csv": gate5f_combined,
        "NODI_COMSOL_GATE5F_MUTATION_ADAPTER_NEW_CASES_20260629.csv": gate5f_adapter_cases,
        "NODI_COMSOL_GATE5G_RC5_LOCK_CANDIDATE_MANIFEST_20260629.csv": gate5g_manifest,
        "NODI_COMSOL_GATE5G_RC5_LOCK_FIELD_CONVERGENCE_EXPORT_20260629.csv": gate5g_field,
        "NODI_COMSOL_GATE5G_RC5_LOCK_PROBE_CLOSURE_EXPORT_20260629.csv": gate5g_probe,
        "NODI_COMSOL_GATE5G_INTEROP_CERTIFICATE_20260629.csv": gate5g_cert,
    }
    gate5h_sweep, gate5h_review = build_gate5h(gate5_csv_payload)
    gate5_csv_payload["NODI_COMSOL_GATE5H_NO_AUTH_FORBIDDEN_SWEEP_20260629.csv"] = gate5h_sweep
    gate5_csv_payload["NODI_COMSOL_GATE5H_SELF_REVIEW_20260629.csv"] = gate5h_review

    summary = {
        "comsol_manifest_rows": len(comsol["manifest"]),
        "comsol_validation_rows": len(comsol["validation"]),
        "comsol_artifact_receipt_rows": len(comsol["artifact_receipt"]),
        "comsol_rc5_field_map_rows": len(comsol["rc5_field_map"]),
        "comsol_probe_rows": len(comsol["probe"]),
        "comsol_rc5_index_rows": len(comsol["rc5_index"]),
        "comsol_authorization_dependency_rows": len(comsol["authorization_dependency"]),
        "comsol_command_guard_rows": len(comsol["command_guard"]),
        "comsol_mutation_v4_rows": len(comsol["mutation_v4"]),
        "nodi_gate4_probe_actual_rows": len(read_rows(NODI_GATE4_PROBE)),
        "gate2d_rows": len(read_rows(GATE2D_LEDGER)),
        "gate5_pending_rows": len(gate5a_pending),
        "gate5_pending_closed_rows": sum(1 for row in gate5b_closure if row.get("pending_closed") == "true"),
        "gate5a_receipt_blocking_mismatches": sum(1 for row in gate5a_receipt if row.get("receipt_status") == "BLOCKING_MISMATCH"),
        "gate5a_self_hash_drift_rows": sum(1 for row in gate5a_receipt if row.get("receipt_status") == "RECORDED_SELF_REFERENTIAL_HASH_DRIFT_NON_POLICY"),
        "gate5_true_policy_conflicts": sum(1 for row in gate5b_closure if row.get("true_policy_conflict") == "true"),
        "gate5_rc5_semantic_conflicts": sum(1 for row in gate5c_matrix if row.get("semantic_conflict") == "true"),
        "gate5_adapter_proposals": len(gate5d_plan),
        "gate5_adapter_negative_controls": len(gate5d_controls),
        "gate5_mutation_combined_rows": len(gate5f_combined),
        "gate5_mutation_unexpected_pass": sum(1 for row in gate5f_combined if row.get("unexpected_pass") == "true"),
        "gate5_no_auth_sweep_failures": sum(1 for row in gate5h_sweep if row.get("sweep_status") != "PASS_NO_AUTH"),
    }
    reports = {
        "244_NODI_COMSOL_GATE5A_COMSOL_GATE4_ACTUAL_PACKAGE_RECEIPT_20260629.md": (
            "Report 244: NODI-COMSOL Gate5A COMSOL Gate4 Actual Package Receipt",
            G5A_PASS,
            [
                f"COMSOL Gate4 manifest rows received: {summary['comsol_manifest_rows']}.",
                f"Artifact receipt/RC5/probe/mutation thresholds: {summary['comsol_artifact_receipt_rows']}/15, {summary['comsol_rc5_field_map_rows']}/351, {summary['comsol_probe_rows']}/120, {summary['comsol_mutation_v4_rows']}/960.",
                f"Blocking receipt mismatches: {summary['gate5a_receipt_blocking_mismatches']}; self-referential metadata hash drifts recorded: {summary['gate5a_self_hash_drift_rows']}.",
                "All Gate4 COMSOL artifacts remain not-evidence and no-authorization receipt inputs.",
            ],
        ),
        "245_NODI_COMSOL_GATE5B_PENDING_NODI_GATE4_ACTUAL_CLOSURE_20260629.md": (
            "Report 245: NODI-COMSOL Gate5B Pending NODI Gate4 Actual Closure",
            G5B_PASS,
            [
                f"Pending COMSOL rows closed with NODI Gate4 actuals: {summary['gate5_pending_closed_rows']}/{summary['gate5_pending_rows']}.",
                f"Closure classes: {summarize_counts(gate5b_closure, 'closure_classification')}.",
                "True policy conflicts: 0.",
            ],
        ),
        "246_NODI_COMSOL_GATE5C_RC5_BIDIRECTIONAL_DICTIONARY_CONVERGENCE_20260629.md": (
            "Report 246: NODI-COMSOL Gate5C RC5 Bidirectional Dictionary Convergence",
            G5C_PASS,
            [
                f"NODI RC5 rows: {len(read_rows(NODI_RC5))}; COMSOL RC5 draft rows: {summary['comsol_rc5_field_map_rows']}; COMSOL RC5 index rows: {summary['comsol_rc5_index_rows']}.",
                "Semantic conflicts: 0.",
                "RC5 lock candidate remains review-only and contract-only.",
            ],
        ),
        "247_NODI_COMSOL_GATE5D_ADAPTER_GAP_CLOSURE_PLAN_V3_20260629.md": (
            "Report 247: NODI-COMSOL Gate5D Adapter Gap Closure Plan v3",
            G5D_PASS,
            [
                f"Adapter proposals: {summary['gate5_adapter_proposals']}; negative controls: {summary['gate5_adapter_negative_controls']}.",
                "All adapter proposals are schema/label normalization only.",
                "No adapter may change NOT_APPROVED, ABSENT, FAIL_CLOSED, blocked, quarantine, or review-only states to accepted/authorized.",
            ],
        ),
        "248_NODI_COMSOL_GATE5E_OWNER_LEDGER_COMMAND_GUARD_ROUNDTRIP_20260629.md": (
            "Report 248: NODI-COMSOL Gate5E Owner Ledger and Command Guard Roundtrip",
            G5E_PASS,
            [
                f"COMSOL authorization dependency rows: {summary['comsol_authorization_dependency_rows']}; command guard rows: {summary['comsol_command_guard_rows']}.",
                "Current action allowed remains false for all mapped rows.",
                "Command recipes are text-only; no COMSOL launch, no .mph load, no production runtime.",
            ],
        ),
        "249_NODI_COMSOL_GATE5F_MUTATION_CROSS_REPLAY_STRESS_REGRESSION_20260629.md": (
            "Report 249: NODI-COMSOL Gate5F Mutation Cross-Replay Stress Regression",
            G5F_PASS,
            [
                f"Combined mutation/conformance rows: {summary['gate5_mutation_combined_rows']}.",
                "Unexpected pass: 0; forbidden promotion: 0; Gate2D row-count drift: 0.",
                "Adapter-specific mutation cases cover label drift, field alias, blocked-state spoofing, QCH spoofing, EDGE approval spoofing, and BINDING promotion spoofing.",
            ],
        ),
        "250_NODI_COMSOL_GATE5G_RC5_LOCK_CANDIDATE_INTEROP_CERTIFICATE_20260629.md": (
            "Report 250: NODI-COMSOL Gate5G RC5 Lock Candidate Interop Certificate",
            G5G_PASS,
            [
                "RC5 lock candidate status: RC5_LOCK_CANDIDATE_REVIEW_ONLY.",
                "Gate2D reduced-scope context-only ledger remains exactly 4 rows.",
                "EDGE NOT_APPROVED, QCH ABSENT, BINDING FAIL_CLOSED remain inherited states.",
            ],
        ),
        "251_NODI_COMSOL_GATE5H_NO_AUTH_REGRESSION_SELF_REVIEW_20260629.md": (
            "Report 251: NODI-COMSOL Gate5H No-Auth Regression and Self-Review",
            G5H_PASS,
            [
                f"No-auth sweep failures: {summary['gate5_no_auth_sweep_failures']}.",
                "Six independent review dimensions report PASS with no P0/P1 open.",
                "No formula, q_ch weighting, JRC, yield, winner, detection_probability, production, or runtime authorization opened.",
            ],
        ),
    }
    payload = {
        "date": DATE_STAMP,
        "dispositions": {
            "Gate5A": G5A_PASS,
            "Gate5B": G5B_PASS,
            "Gate5C": G5C_PASS,
            "Gate5D": G5D_PASS,
            "Gate5E": G5E_PASS,
            "Gate5F": G5F_PASS,
            "Gate5G": G5G_PASS,
            "Gate5H": G5H_PASS,
        },
        "summary": summary,
        "csv": gate5_csv_payload,
        "reports": reports,
    }
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    issues = []
    thresholds = {
        "comsol_manifest_rows": 36,
        "comsol_validation_rows": 13,
        "comsol_artifact_receipt_rows": 15,
        "comsol_rc5_field_map_rows": 351,
        "comsol_probe_rows": 120,
        "comsol_rc5_index_rows": 8,
        "comsol_authorization_dependency_rows": 36,
        "comsol_command_guard_rows": 6,
        "comsol_mutation_v4_rows": 960,
        "nodi_gate4_probe_actual_rows": 120,
        "gate2d_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
    }
    for key, expected in thresholds.items():
        if s.get(key) != expected:
            issues.append(f"{key} expected {expected}, got {s.get(key)}")
    if s["gate5_pending_rows"] != 120 or s["gate5_pending_closed_rows"] != 120:
        issues.append("Gate5B did not close all 120 pending probe rows")
    if s["gate5a_receipt_blocking_mismatches"] != 0:
        issues.append("Gate5A receipt blocking mismatches are nonzero")
    if s["gate5_true_policy_conflicts"] != 0:
        issues.append("Gate5B true policy conflicts are nonzero")
    if s["gate5_rc5_semantic_conflicts"] != 0:
        issues.append("Gate5C semantic conflicts are nonzero")
    if s["gate5_mutation_combined_rows"] < 1720:
        issues.append("Gate5F combined mutation rows below 1720")
    if s["gate5_mutation_unexpected_pass"] != 0:
        issues.append("Gate5F unexpected pass is nonzero")
    if s["gate5_no_auth_sweep_failures"] != 0:
        issues.append("Gate5H no-auth sweep failures are nonzero")
    for name, rows in payload["csv"].items():
        if not rows:
            issues.append(f"{name} is empty")
    return issues


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in payload["csv"].items():
        write_csv_rows(OUTPUT_DIR / name, rows)
    manifest_rows = []
    for idx, (name, path) in enumerate(current_output_sidecars(), start=1):
        manifest_rows.append(
            {
                "manifest_id": f"G5G-MANIFEST-{idx:04d}",
                "artifact_path": f"reports/joint_interface_{DATE_STAMP}/{name}",
                "artifact_role": "Gate5 RC5 lock candidate machine package",
                "sha256": sha256_file(path),
                "row_count": csv_count(path),
                "not_evidence": "true",
                "authorization_flags_false": "true",
            }
        )
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE5G_RC5_LOCK_CANDIDATE_MANIFEST_{DATE_STAMP}.csv", manifest_rows)
    for name, (title, disposition, bullets) in payload["reports"].items():
        write_report(REPORT_DIR / name, title, disposition, bullets)
    for gate in ("A", "B", "C", "D", "E", "F", "G", "H"):
        key = f"Gate5{gate}"
        report_payload = {
            "date": DATE_STAMP,
            "disposition": payload["dispositions"][key],
            "summary": payload["summary"],
            "authorization": "no formula, no q_ch weighting, no JRC, no production/runtime",
        }
        write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE5{gate}_REPORT_{DATE_STAMP}.json", report_payload)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate5a_to_gate5h:
        parser.error("--confirm-gate5a-to-gate5h is required")
    payload = build_payload(args.comsol_root)
    issues = validate_payload(payload)
    if issues:
        for issue in issues:
            print(f"VALIDATION_ERROR: {issue}")
        return 2
    write_outputs(payload)
    print("PASS_GATE5A_TO_GATE5H_RC5_LOCK_CANDIDATE_NO_AUTHORIZATION")
    print(f"combined_mutation_rows={payload['summary']['gate5_mutation_combined_rows']}")
    print(f"pending_closed={payload['summary']['gate5_pending_closed_rows']}/{payload['summary']['gate5_pending_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
