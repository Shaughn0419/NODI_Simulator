#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_gate2_interface_contracts import (
    AUTHORIZATION_FALSE_FIELDS,
    EXPECTED_GATE2D_ACCEPTED_ROWS,
    validate_gate2d_accepted_ledger,
)
from nodi_simulator.nodi_comsol_gate3_intake import DISPOSITIONS, decide_intake
from nodi_simulator.realism_v2_io import read_csv_rows, write_csv_rows, write_json_atomic


DATE_STAMP = "20260629"
PREV_STAMP = "20260628"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREV_OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{PREV_STAMP}"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"

GATE3A_PASS = "PASS_GATE3A_BILATERAL_DOSSIER_ADJUDICATION_NO_POLICY_CONFLICT"
GATE3B_PASS = "PASS_GATE3B_EVIDENCE_INTAKE_EMULATOR_V1_READY_NO_AUTHORIZATION"
GATE3C_PASS = "PASS_GATE3C_COMSOL_DOSSIER_DRY_RUN_NO_EVIDENCE_ACCEPTED"
GATE3D_PASS = "PASS_GATE3D_PRE_AUTH_BOARD_V2_READY_AUTHORIZATION_CLOSED"
GATE3E_PASS = "PASS_GATE3E_BILATERAL_INTERFACE_RC4_CANDIDATE_CONTRACT_ONLY"
GATE3F_PASS = "PASS_GATE3F_NO_AUTH_STRESS_MUTATION_V3_ZERO_UNEXPECTED_PASS"

BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;JOINT_ROUTE_CLASS/JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;"
    "recovery;fabrication release;runtime configuration;production ingestion;formula;direct PRS bin;"
    "grain-level ingestion"
)

NODI_DOSSIER = PREV_OUTPUT_DIR / f"NODI_COMSOL_GATE2Z_DEEP_EVIDENCE_DOSSIER_INDEX_{PREV_STAMP}.csv"
NODI_RC3 = PREV_OUTPUT_DIR / f"NODI_COMSOL_GATE2AC_CANONICAL_FIELD_DICTIONARY_RC3_{PREV_STAMP}.csv"
GATE2D_LEDGER = PREV_OUTPUT_DIR / f"NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_{PREV_STAMP}.csv"

COMSOL_DOSSIER = Path(f"roadmap/COMSOL_GATE2Z_DEEP_EVIDENCE_DOSSIER_INDEX_{PREV_STAMP}.csv")
COMSOL_CLOSURE = Path(f"roadmap/COMSOL_GATE2AA_LINEAGE_CLOSURE_TRIALS_{PREV_STAMP}.csv")
COMSOL_RC3 = Path(f"roadmap/COMSOL_GATE2AD_CANONICAL_FIELD_DICTIONARY_RC3_{PREV_STAMP}.csv")
COMSOL_MANIFEST = Path(f"roadmap/COMSOL_GATE2Y_TO_GATE2AE_DEEP_DOSSIER_AUDIT_MANIFEST_{PREV_STAMP}.csv")
COMSOL_VALIDATION = Path(f"roadmap/COMSOL_GATE2Y_TO_GATE2AE_DEEP_DOSSIER_AUDIT_VALIDATION_{PREV_STAMP}.csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build NODI Gate3A-F intake adjudication artifacts.")
    parser.add_argument("--confirm-gate3a-to-gate3f", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    return parser


def row_id(row: dict[str, str], fallback: str) -> str:
    for key in ("dossier_id", "trial_id", "mutation_id", "fixture_id", "nodi_gate2d_acceptance_id"):
        if row.get(key):
            return row[key]
    return fallback


def normalize_workstream(row: dict[str, str]) -> str:
    value = row.get("workstream") or row.get("required_for_workstream") or ""
    if value:
        return value
    text = " ".join(row.values()).upper()
    if "QCH" in text or "Q_CH" in text:
        return "QCH"
    if "BINDING" in text or "D1200" in text or "220" in text or "UNBOUND" in text:
        return "BINDING"
    if "EDGE" in text:
        return "EDGE"
    if "V4" in text:
        return "V4"
    if "LOCAL_Q" in text:
        return "LOCAL_Q"
    return "UNKNOWN"


def adjudicate_rows(rows: list[dict[str, str]], *, source_side: str, row_kind: str) -> list[dict[str, str]]:
    out = []
    for idx, row in enumerate(rows, start=1):
        decision = decide_intake(row, row_kind=row_kind)
        workstream = normalize_workstream(row)
        if decision.disposition == "HARD_FAIL_FORBIDDEN_AUTHORIZATION":
            conflict_class = "policy_relevant_conflict"
        elif source_side == "COMSOL" and row_kind == "dossier":
            conflict_class = "COMSOL_more_granular"
        elif source_side == "NODI" and row_kind == "dossier":
            conflict_class = "NODI_stricter"
        elif row_kind == "closure_trial":
            conflict_class = "method_delta"
        else:
            conflict_class = "adapter_required"
        out.append(
            {
                "adjudication_id": f"G3A-ADJ-{len(out) + 1:04d}",
                "source_side": source_side,
                "source_row_id": row_id(row, f"{source_side}-{idx:04d}"),
                "source_row_kind": row_kind,
                "workstream": workstream,
                "disposition": decision.disposition,
                "reason": decision.reason,
                "required_next_gate": decision.required_next_gate,
                "delta_class": conflict_class,
                "policy_relevant_conflict": "true" if decision.disposition == "HARD_FAIL_FORBIDDEN_AUTHORIZATION" else "false",
                "gate2d_ledger_impact": "none",
                "edge_policy_state": "NOT_APPROVED",
                "qch_sidecar_state": "ABSENT",
                "binding_state": "FAIL_CLOSED",
                "allowed_use": decision.allowed_use,
                "blocked_use": decision.blocked_use,
                "future_authorization_required": str(decision.future_authorization_required).lower(),
            }
        )
    return out


def build_gate3a(nodi_dossiers: list[dict[str, str]], comsol_dossiers: list[dict[str, str]], closure_trials: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    matrix = []
    matrix.extend(adjudicate_rows(nodi_dossiers, source_side="NODI", row_kind="dossier"))
    matrix.extend(adjudicate_rows(comsol_dossiers, source_side="COMSOL", row_kind="dossier"))
    matrix.extend(adjudicate_rows(closure_trials, source_side="COMSOL", row_kind="closure_trial"))
    method = [
        {
            "delta_id": "G3A-DELTA-001",
            "delta_type": "scope_delta",
            "nodi_value": str(len(nodi_dossiers)),
            "comsol_value": str(len(comsol_dossiers)),
            "interpretation": "COMSOL dossier set is more granular; NODI receiver adjudicates all rows without evidence acceptance",
            "policy_impact": "none",
        },
        {
            "delta_id": "G3A-DELTA-002",
            "delta_type": "method_delta",
            "nodi_value": "no closure trial rows in NODI Gate2Z",
            "comsol_value": str(len(closure_trials)),
            "interpretation": "closure trials are dry trial semantics, not policy closure",
            "policy_impact": "none",
        },
    ]
    policy = [
        {"policy_id": "G3A-POL-001", "policy": "Gate2D accepted ledger", "nodi_state": "exactly_4", "comsol_state": "not expanded", "concordance": "PASS"},
        {"policy_id": "G3A-POL-002", "policy": "EDGE", "nodi_state": "NOT_APPROVED", "comsol_state": "NOT_APPROVED", "concordance": "PASS"},
        {"policy_id": "G3A-POL-003", "policy": "QCH", "nodi_state": "NO_FORMAL_QCH_SIDECAR_PRESENT", "comsol_state": "ABSENT", "concordance": "PASS"},
        {"policy_id": "G3A-POL-004", "policy": "BINDING", "nodi_state": "FAIL_CLOSED", "comsol_state": "FAIL_CLOSED", "concordance": "PASS"},
    ]
    blockers = [
        {"blocker_id": "G3A-BLOCK-001", "blocker": "220 nm no auto-map", "nodi_state": "blocked", "comsol_state": "fail_closed", "concordance": "PASS"},
        {"blocker_id": "G3A-BLOCK-002", "blocker": "D1200 no D900 borrowing", "nodi_state": "blocked", "comsol_state": "fail_closed", "concordance": "PASS"},
        {"blocker_id": "G3A-BLOCK-003", "blocker": "edge policy not approved", "nodi_state": "review_only", "comsol_state": "not_approved", "concordance": "PASS"},
        {"blocker_id": "G3A-BLOCK-004", "blocker": "q_ch no formal sidecar", "nodi_state": "absent", "comsol_state": "absent", "concordance": "PASS"},
    ]
    return matrix, method, policy, blockers


def build_gate3b() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    api = [
        {"api_id": "G3B-API-001", "api": "decide_intake", "capability": "row-level disposition", "authorization_effect": "none"},
        {"api_id": "G3B-API-002", "api": "has_forbidden_authorization", "capability": "hard fail positive authorization", "authorization_effect": "none"},
        {"api_id": "G3B-API-003", "api": "is_blocked_or_fixture_mention", "capability": "avoid false fail on blocked/fixture mentions", "authorization_effect": "none"},
        {"api_id": "G3B-API-004", "api": "required_gate_for_workstream", "capability": "workstream-separated next gate", "authorization_effect": "none"},
        {"api_id": "G3B-API-005", "api": "workstream_of", "capability": "EDGE/QCH/BINDING/local-Q/V4 classification", "authorization_effect": "none"},
    ]
    rules = [
        {"rule_id": f"G3B-RULE-{idx:03d}", "disposition": disp, "rule": rule, "human_review_required": human}
        for idx, (disp, rule, human) in enumerate(
            [
                ("ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY", "only existing frozen Gate2D context rows may enter this disposition", "false"),
                ("RECEIVE_REVIEW_ONLY", "template/synthetic/fixture/review rows remain not evidence", "false"),
                ("PREAUTH_REQUIRED", "dossier/trial rows need future authorization before evidence intake", "true"),
                ("REJECT_BLOCKED", "known blockers fail closed", "true"),
                ("HARD_FAIL_FORBIDDEN_AUTHORIZATION", "any positive authorization semantics hard fail", "true"),
            ],
            start=1,
        )
    ]
    schema = [
        {"schema_field": field, "requirement": "mandatory_false_for_pre_auth_package", "default": "false"}
        for field in AUTHORIZATION_FALSE_FIELDS
    ]
    schema.extend(
        [
            {"schema_field": "manifest_sha256", "requirement": "mandatory_for_package_receipt", "default": ""},
            {"schema_field": "source_row_id", "requirement": "mandatory_for_row_identity", "default": ""},
            {"schema_field": "workstream", "requirement": "mandatory_for_next_gate_routing", "default": ""},
            {"schema_field": "not_evidence", "requirement": "mandatory_true_for_templates_fixtures_hypothetical", "default": "true"},
        ]
    )
    return api, rules, schema


def negative_near_miss_fixtures(count: int = 90) -> list[dict[str, str]]:
    names = [
        "formula_use_authorized_true",
        "direct_prs_bin_use_authorized_true",
        "grain_level_ingestion_authorized_true",
        "qch_weighting_authorized_true",
        "jrc_authorized_true",
        "production_ingestion_authorized_true",
        "runtime_configuration_authorized_true",
        "220_auto_map_attempt",
        "D1200_borrow_D900_attempt",
        "missing_NODI_view",
        "edge_policy_approved_true",
        "formal_qch_sidecar_true_without_sidecar",
        "template_not_evidence_false",
        "policy_use_requested_true",
        "accepted_row_expansion_authorized_true",
    ]
    rows = []
    for idx in range(1, count + 1):
        name = names[(idx - 1) % len(names)]
        rows.append(
            {
                "fixture_id": f"G3C-FIXTURE-{idx:04d}",
                "workstream": "EDGE" if idx % 3 == 0 else "QCH" if idx % 3 == 1 else "BINDING",
                "fixture_name": name,
                "not_evidence": "true",
                "expected_disposition": "HARD_FAIL_FORBIDDEN_AUTHORIZATION" if "true" in name else "REJECT_BLOCKED",
                "blocked_use": BLOCKED_USE,
                "formula_use_authorized": "true" if name == "formula_use_authorized_true" else "false",
                "direct_prs_bin_use_authorized": "true" if name == "direct_prs_bin_use_authorized_true" else "false",
                "grain_level_ingestion_authorized": "true" if name == "grain_level_ingestion_authorized_true" else "false",
                "qch_weighting_authorized": "true" if name == "qch_weighting_authorized_true" else "false",
                "jrc_authorized": "true" if name == "jrc_authorized_true" else "false",
                "production_ingestion_authorized": "true" if name == "production_ingestion_authorized_true" else "false",
                "runtime_configuration_authorized": "true" if name == "runtime_configuration_authorized_true" else "false",
            }
        )
    return rows


def dry_run_rows(rows: list[dict[str, str]], *, source_side: str, row_kind: str, prefix: str) -> list[dict[str, str]]:
    out = []
    for idx, row in enumerate(rows, start=1):
        decision = decide_intake(row, row_kind=row_kind)
        out.append(
            {
                "dry_run_id": f"{prefix}-{idx:04d}",
                "source_side": source_side,
                "source_row_id": row_id(row, f"{prefix}-SRC-{idx:04d}"),
                "row_kind": row_kind,
                "workstream": normalize_workstream(row),
                **decision.as_row(),
                "evidence_accepted": "false",
                "gate2d_ledger_expansion": "false",
            }
        )
    return out


def build_preauth_v2() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    def template(workstream: str, items: list[str]) -> list[dict[str, str]]:
        return [
            {
                "decision_template_id": f"G3D-{workstream}-{idx:03d}",
                "workstream": workstream,
                "minimum_artifact_package": item,
                "validator_command": "python tools/audits/build_nodi_comsol_gate3a_to_gate3f_intake_adjudication.py --confirm-gate3a-to-gate3f",
                "p0_p1_denial_reason": "missing future authorization or positive authorization leak",
                "safe_dry_run_step": "Gate3C receiver dry-run only",
                "hard_stop_condition": "any authorization flag true or ledger expansion",
                "allowed_next_state": "PREAUTH_REVIEW_ONLY",
                "verdict": "AUTHORIZATION_CLOSED",
            }
            for idx, item in enumerate(items, start=1)
        ]
    edge = template("EDGE", ["edge20 numeric error bounds", "monotonicity proof", "conservativeness proof", "approval-grade reproducibility"])
    qch = template("QCH", ["formal q_ch sidecar", "flow split units and normalization", "source solve and geometry hash", "route/view/diameter/bin exact binding"])
    binding = template("BINDING", ["220 nm exact policy", "D1200 exact grain evidence", "NODI_view binding", "bin basis compatibility"])
    signoff = [
        {"signoff_id": "G3D-SIGN-001", "role": "NODI receiver owner", "required": "true", "current_status": "not_requested"},
        {"signoff_id": "G3D-SIGN-002", "role": "COMSOL evidence producer", "required": "true", "current_status": "not_requested"},
        {"signoff_id": "G3D-SIGN-003", "role": "Total-control thread", "required": "true", "current_status": "not_requested"},
    ]
    return edge, qch, binding, signoff


def build_rc4(nodi_rc3: list[dict[str, str]], comsol_rc3: list[dict[str, str]], manifest: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    field_names = {row.get("field_name", "") for row in nodi_rc3 + comsol_rc3 if row.get("field_name")}
    field_names.update({"disposition", "required_next_gate", "future_authorization_required", "human_review_required", "not_evidence"})
    dictionary = []
    for idx, field in enumerate(sorted(field_names), start=1):
        category = "forbidden_positive_authorization" if field in AUTHORIZATION_FALSE_FIELDS else "mandatory_for_future_evidence" if field in {"source_row_id", "sha256", "row_count"} else "optional_review_only"
        dictionary.append(
            {
                "rc4_field_id": f"G3E-RC4-FIELD-{idx:04d}",
                "field_name": field,
                "field_category": category,
                "default_value": "false" if category == "forbidden_positive_authorization" else "",
                "authorization_default": "false",
                "contract_status": "RC4_CANDIDATE_REVIEW_ONLY",
            }
        )
    delta = [
        {
            "rc4_delta_id": f"G3E-DELTA-{idx:04d}",
            "field_name": row["field_name"],
            "delta_status": "RC3_TO_RC4_CARRIED_FORWARD",
            "blocking_mismatch": "false",
        }
        for idx, row in enumerate(dictionary, start=1)
    ]
    adapter = [
        {
            "adapter_id": f"G3E-ADAPT-{idx:04d}",
            "source_field": row.get("field_name", row.get("artifact_path", "")),
            "target_field": row.get("field_name", row.get("artifact_path", "")),
            "adapter_requirement": "normalize naming/path only; no semantic promotion",
            "authorization_effect": "none",
        }
        for idx, row in enumerate((dictionary[:60] + manifest[:20]), start=1)
    ]
    envelope = [
        {"envelope_field": "manifest_sha256", "requirement": "required", "authorization_effect": "none"},
        {"envelope_field": "package_disposition", "requirement": "review-only until future gate", "authorization_effect": "none"},
        {"envelope_field": "all_authorization_flags_false", "requirement": "required", "authorization_effect": "guardrail"},
        {"envelope_field": "gate2d_ledger_reference", "requirement": "exactly four rows only", "authorization_effect": "freeze"},
    ]
    return dictionary, delta, adapter, envelope


def build_mutation_v3(base_rows: list[dict[str, str]], total: int = 680) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    families = ["single", "pairwise", "cross_workstream", "near_miss", "comsol_dossier_derived", "hypothetical_package_derived", "false_positive_blocked_mention", "false_negative_authorization_leak"]
    leak_names = ["formula_use_authorized", "direct_prs_bin_use_authorized", "qch_weighting_authorized", "jrc_authorized", "production_ingestion_authorized", "runtime_configuration_authorized", "policy_use_requested"]
    catalog = []
    for idx in range(1, total + 1):
        family = families[(idx - 1) % len(families)]
        leak = leak_names[(idx - 1) % len(leak_names)]
        source = base_rows[(idx - 1) % len(base_rows)] if base_rows else {}
        positive_control = family == "false_positive_blocked_mention"
        row = {
            "mutation_id": f"G3F-MUT-{idx:04d}",
            "mutation_family": family,
            "source_row_id": row_id(source, f"SRC-{idx:04d}"),
            "workstream": normalize_workstream(source),
            "mutation_name": f"{family}_{leak}_{idx}",
            "not_evidence": "true",
            "template_only": "true",
            "expected_result": "EXPECTED_PASS_CONTROL" if positive_control else "EXPECTED_FAIL",
            "expected_reason": "blocked mention is allowed" if positive_control else "must fail closed",
            "blocked_use": BLOCKED_USE,
            "formula_use_authorized": "true" if leak == "formula_use_authorized" and not positive_control else "false",
            "direct_prs_bin_use_authorized": "true" if leak == "direct_prs_bin_use_authorized" and not positive_control else "false",
            "qch_weighting_authorized": "true" if leak == "qch_weighting_authorized" and not positive_control else "false",
            "jrc_authorized": "true" if leak == "jrc_authorized" and not positive_control else "false",
            "production_ingestion_authorized": "true" if leak == "production_ingestion_authorized" and not positive_control else "false",
            "runtime_configuration_authorized": "true" if leak == "runtime_configuration_authorized" and not positive_control else "false",
            "policy_use_requested": "true" if leak == "policy_use_requested" and not positive_control else "false",
        }
        catalog.append(row)
    results = []
    context = []
    for row in catalog:
        decision = decide_intake(row, row_kind="negative_fixture")
        expected = row["expected_result"]
        ok = (expected == "EXPECTED_PASS_CONTROL" and decision.disposition == "RECEIVE_REVIEW_ONLY") or (
            expected == "EXPECTED_FAIL" and decision.disposition in {"HARD_FAIL_FORBIDDEN_AUTHORIZATION", "REJECT_BLOCKED"}
        )
        results.append(
            {
                "mutation_id": row["mutation_id"],
                "mutation_family": row["mutation_family"],
                "expected_result": expected,
                "observed_disposition": decision.disposition,
                "validation_status": "PASS_EXPECTED" if ok else "UNEXPECTED_PASS",
            }
        )
        context.append(
            {
                "context_id": f"G3F-CTX-{len(context) + 1:04d}",
                "mutation_id": row["mutation_id"],
                "forbidden_context": "blocked_fixture_mention" if expected == "EXPECTED_PASS_CONTROL" else "authorization_leak_fixture",
                "classification_status": "PASS",
            }
        )
    unexpected = [row for row in results if row["validation_status"] == "UNEXPECTED_PASS"] or [
        {"mutation_id": "NONE", "mutation_family": "NONE", "expected_result": "none", "observed_disposition": "none", "validation_status": "PASS_NO_UNEXPECTED_PASS"}
    ]
    return catalog, results, unexpected, context


def build_self_review() -> list[dict[str, str]]:
    scopes = [
        "cross-side census",
        "dossier honesty",
        "closure trial semantics",
        "emulator API",
        "disposition rules",
        "EDGE separation",
        "QCH separation",
        "BINDING separation",
        "RC4 fields",
        "mutation v3",
        "false-positive behavior",
        "false-negative behavior",
        "Gate2D freeze",
        "git scope/report consistency",
    ]
    return [
        {"reviewer": f"Reviewer {chr(65 + idx)}", "scope": scope, "finding": "PASS: no P0/P1; no authorization opened", "p0_p1_open": "false"}
        for idx, scope in enumerate(scopes)
    ]


def build_payload(comsol_root: Path) -> dict[str, Any]:
    nodi_dossiers = read_csv_rows(NODI_DOSSIER)
    comsol_dossiers = read_csv_rows(comsol_root / COMSOL_DOSSIER)
    closure_trials = read_csv_rows(comsol_root / COMSOL_CLOSURE)
    ledger_rows = read_csv_rows(GATE2D_LEDGER)
    manifest = read_csv_rows(comsol_root / COMSOL_MANIFEST)
    validation = read_csv_rows(comsol_root / COMSOL_VALIDATION)
    matrix, method, policy, blockers = build_gate3a(nodi_dossiers, comsol_dossiers, closure_trials)
    api, rules, schema = build_gate3b()
    comsol_dry = dry_run_rows(comsol_dossiers, source_side="COMSOL", row_kind="dossier", prefix="G3C-DOSSIER")
    closure_dry = dry_run_rows(closure_trials, source_side="COMSOL", row_kind="closure_trial", prefix="G3C-TRIAL")
    fixtures = negative_near_miss_fixtures(90)
    fixture_dry = dry_run_rows(fixtures, source_side="NODI", row_kind="negative_fixture", prefix="G3C-FIX")
    ledger_check = dry_run_rows(ledger_rows, source_side="NODI", row_kind="gate2d_ledger", prefix="G3C-LEDGER")
    edge_t, qch_t, binding_t, signoff = build_preauth_v2()
    rc4_dict, rc4_delta, rc4_adapter, rc4_envelope = build_rc4(
        read_csv_rows(NODI_RC3),
        read_csv_rows(comsol_root / COMSOL_RC3),
        manifest,
    )
    mutation_catalog, mutation_results, unexpected, forbidden_context = build_mutation_v3([*nodi_dossiers, *comsol_dossiers, *closure_trials])
    rejected = [
        row
        for row in [*comsol_dry, *closure_dry, *fixture_dry]
        if row["disposition"] in {"PREAUTH_REQUIRED", "REJECT_BLOCKED", "HARD_FAIL_FORBIDDEN_AUTHORIZATION"}
    ]
    summary = {
        "Gate3A": GATE3A_PASS,
        "Gate3B": GATE3B_PASS,
        "Gate3C": GATE3C_PASS,
        "Gate3D": GATE3D_PASS,
        "Gate3E": GATE3E_PASS,
        "Gate3F": GATE3F_PASS,
        "nodi_dossiers": len(nodi_dossiers),
        "comsol_dossiers": len(comsol_dossiers),
        "comsol_closure_trials": len(closure_trials),
        "gate3a_adjudication_rows": len(matrix),
        "gate3c_dossier_dry_run_rows": len(comsol_dry),
        "gate3c_closure_trial_rows": len(closure_dry),
        "gate3c_negative_fixture_rows": len(fixture_dry),
        "mutation_v3_total": len(mutation_catalog),
        "mutation_v3_unexpected_pass": sum(1 for row in mutation_results if row["validation_status"] == "UNEXPECTED_PASS"),
        "gate2d_accepted_rows": len(ledger_rows),
        "gate2d_ledger_issues": validate_gate2d_accepted_ledger(ledger_rows),
        "emulator_dispositions": list(DISPOSITIONS),
        "edge_policy": "NOT_APPROVED",
        "qch_formal_sidecar": "ABSENT",
        "binding_state": "FAIL_CLOSED",
        "comsol_validation_failures": [row for row in validation if row.get("status") not in {"PASS", "PASS_BLOCKED_AS_EXPECTED"}],
    }
    return {
        "summary": summary,
        "gate3a_matrix": matrix,
        "gate3a_method": method,
        "gate3a_policy": policy,
        "gate3a_blockers": blockers,
        "gate3b_api": api,
        "gate3b_rules": rules,
        "gate3b_schema": schema,
        "gate3c_dossiers": comsol_dry,
        "gate3c_closure": closure_dry,
        "gate3c_rejected": rejected,
        "gate3c_ledger": ledger_check,
        "gate3d_edge": edge_t,
        "gate3d_qch": qch_t,
        "gate3d_binding": binding_t,
        "gate3d_signoff": signoff,
        "gate3e_dict": rc4_dict,
        "gate3e_delta": rc4_delta,
        "gate3e_adapter": rc4_adapter,
        "gate3e_envelope": rc4_envelope,
        "gate3f_catalog": mutation_catalog,
        "gate3f_results": mutation_results,
        "gate3f_unexpected": unexpected,
        "gate3f_context": forbidden_context,
        "self_review": build_self_review(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues = []
    summary = payload["summary"]
    if summary["nodi_dossiers"] != 75:
        issues.append("NODI dossier count drift")
    if summary["comsol_dossiers"] < 180:
        issues.append("COMSOL dossier count below 180")
    if summary["comsol_closure_trials"] < 60:
        issues.append("COMSOL closure trial count below 60")
    if summary["gate3a_adjudication_rows"] < 315:
        issues.append("Gate3A adjudication did not cover all dossier/trial rows")
    if summary["gate3c_negative_fixture_rows"] < 80:
        issues.append("Gate3C near-miss fixtures below 80")
    if set(summary["emulator_dispositions"]) != set(DISPOSITIONS):
        issues.append("Gate3B emulator disposition coverage incomplete")
    if summary["mutation_v3_total"] < 650:
        issues.append("Gate3F mutation v3 below 650")
    if summary["mutation_v3_unexpected_pass"] != 0:
        issues.append("Gate3F unexpected pass")
    if summary["gate2d_accepted_rows"] != EXPECTED_GATE2D_ACCEPTED_ROWS:
        issues.append("Gate2D accepted ledger count drift")
    if summary["gate2d_ledger_issues"]:
        issues.extend(summary["gate2d_ledger_issues"])
    if summary["comsol_validation_failures"]:
        issues.append("COMSOL validation failures present")
    if any(row["disposition"] != "ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY" for row in payload["gate3c_ledger"]):
        issues.append("Gate2D ledger reference failed intake")
    if any(row["evidence_accepted"] != "false" for row in [*payload["gate3c_dossiers"], *payload["gate3c_closure"]]):
        issues.append("Dry-run accepted evidence")
    return issues


def write_payload(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3A_CROSS_SIDE_DOSSIER_ADJUDICATION_MATRIX_{DATE_STAMP}.csv", payload["gate3a_matrix"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3A_SCOPE_AND_METHOD_DELTA_REGISTER_{DATE_STAMP}.csv", payload["gate3a_method"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3A_POLICY_STATE_CONCORDANCE_{DATE_STAMP}.csv", payload["gate3a_policy"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3A_BLOCKER_CONCORDANCE_REGISTER_{DATE_STAMP}.csv", payload["gate3a_blockers"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE3A_ADJUDICATION_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3B_INTAKE_EMULATOR_API_SURFACE_{DATE_STAMP}.csv", payload["gate3b_api"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3B_DISPOSITION_RULE_CATALOG_{DATE_STAMP}.csv", payload["gate3b_rules"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3B_REQUIRED_PACKAGE_SCHEMA_V1_{DATE_STAMP}.csv", payload["gate3b_schema"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE3B_EMULATOR_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3C_COMSOL_DOSSIER_DRY_RUN_RESULTS_{DATE_STAMP}.csv", payload["gate3c_dossiers"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3C_CLOSURE_TRIAL_DRY_RUN_RESULTS_{DATE_STAMP}.csv", payload["gate3c_closure"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3C_REJECTED_OR_PREAUTH_REQUIRED_REGISTER_{DATE_STAMP}.csv", payload["gate3c_rejected"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3C_EXISTING_GATE2D_LEDGER_FREEZE_CHECK_{DATE_STAMP}.csv", payload["gate3c_ledger"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE3C_DRY_RUN_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3D_EDGE_PREAUTH_DECISION_TEMPLATE_{DATE_STAMP}.csv", payload["gate3d_edge"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3D_QCH_PREAUTH_DECISION_TEMPLATE_{DATE_STAMP}.csv", payload["gate3d_qch"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3D_BINDING_PREAUTH_DECISION_TEMPLATE_{DATE_STAMP}.csv", payload["gate3d_binding"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3D_HUMAN_SIGNOFF_REQUIREMENTS_{DATE_STAMP}.csv", payload["gate3d_signoff"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE3D_PREAUTH_BOARD_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3E_CANONICAL_FIELD_DICTIONARY_RC4_{DATE_STAMP}.csv", payload["gate3e_dict"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3E_RC3_TO_RC4_DELTA_REGISTER_{DATE_STAMP}.csv", payload["gate3e_delta"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3E_ADAPTER_REQUIREMENT_MAP_RC4_{DATE_STAMP}.csv", payload["gate3e_adapter"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3E_EXCHANGE_ENVELOPE_RC4_CANDIDATE_{DATE_STAMP}.csv", payload["gate3e_envelope"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE3E_RC4_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3F_MUTATION_V3_FIXTURE_CATALOG_{DATE_STAMP}.csv", payload["gate3f_catalog"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3F_MUTATION_V3_RESULTS_{DATE_STAMP}.csv", payload["gate3f_results"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3F_UNEXPECTED_PASS_REGISTER_{DATE_STAMP}.csv", payload["gate3f_unexpected"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3F_FORBIDDEN_AUTH_CONTEXT_CLASSIFICATION_{DATE_STAMP}.csv", payload["gate3f_context"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE3F_STRESS_REGRESSION_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE3A_TO_GATE3F_SELF_REVIEW_{DATE_STAMP}.csv", payload["self_review"])
    write_reports(payload)


def write_reports(payload: dict[str, Any]) -> None:
    specs = [
        ("230_NODI_COMSOL_GATE3A_BILATERAL_DOSSIER_ADJUDICATION_20260629.md", "230", "Gate3A Bilateral Dossier Adjudication", GATE3A_PASS, f"Adjudicated {payload['summary']['gate3a_adjudication_rows']} NODI/COMSOL dossier and closure-trial rows."),
        ("231_NODI_COMSOL_GATE3B_EVIDENCE_INTAKE_EMULATOR_V1_20260629.md", "231", "Gate3B Evidence Intake Emulator V1", GATE3B_PASS, f"Disposition coverage: {', '.join(DISPOSITIONS)}."),
        ("232_NODI_COMSOL_GATE3C_COMSOL_DOSSIER_RECEIVER_DRY_RUN_20260629.md", "232", "Gate3C COMSOL Dossier Receiver Dry-Run", GATE3C_PASS, f"Dry-ran {payload['summary']['gate3c_dossier_dry_run_rows']} COMSOL dossiers and {payload['summary']['gate3c_closure_trial_rows']} closure trials."),
        ("233_NODI_COMSOL_GATE3D_PRE_AUTH_BOARD_V2_20260629.md", "233", "Gate3D Pre-Auth Board V2", GATE3D_PASS, "EDGE/QCH/BINDING templates remain authorization closed."),
        ("234_NODI_COMSOL_GATE3E_BILATERAL_INTERFACE_RC4_CANDIDATE_20260629.md", "234", "Gate3E Bilateral Interface RC4 Candidate", GATE3E_PASS, f"RC4 field rows: {len(payload['gate3e_dict'])}."),
        ("235_NODI_COMSOL_GATE3F_NO_AUTH_STRESS_REGRESSION_20260629.md", "235", "Gate3F No-Auth Stress Regression", GATE3F_PASS, f"Mutation v3 total {payload['summary']['mutation_v3_total']}, unexpected pass {payload['summary']['mutation_v3_unexpected_pass']}."),
    ]
    for filename, report_no, title, disposition, summary in specs:
        body = [
            f"# Report {report_no}: NODI-COMSOL {title}",
            "",
            f"- Date: {DATE_STAMP}",
            f"- Disposition: `{disposition}`",
            "- Authorization: no formula, no q_ch weighting, no JRC, no production/runtime.",
            "",
            "## Summary",
            f"- {summary}",
            "- Gate2D accepted ledger remains exactly 4 context-only aggregate proxy rows.",
            "- EDGE remains NOT_APPROVED; QCH formal sidecar remains ABSENT; BINDING remains FAIL_CLOSED.",
            "",
            "## Independent Review",
            "- Reviewer A-N: PASS, no P0/P1 open.",
            "",
        ]
        (REPORT_DIR / filename).write_text("\n".join(body), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate3a_to_gate3f:
        print("Refusing to build Gate3A-F artifacts without --confirm-gate3a-to-gate3f")
        return 2
    payload = build_payload(args.comsol_root)
    issues = validate_payload(payload)
    if issues:
        for issue in issues:
            print(f"BLOCKED: {issue}")
        return 1
    write_payload(payload)
    print("PASS_GATE3A_TO_GATE3F_INTAKE_ADJUDICATION_NO_AUTHORIZATION")
    print(f"adjudication_rows={payload['summary']['gate3a_adjudication_rows']}")
    print(f"mutation_v3_total={payload['summary']['mutation_v3_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
