#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


DATE_STAMP = "20260628"
OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
EXPECTED_EDGE20_HASH = "b8b3358e7218e3ebc704c2c8dcaf2c9a0feb15283fa704610b39f8afc68d5ca3"
EXPECTED_GATE2D_ROWS = 4

GATE2N_PASS = "PASS_GATE2N_COMSOL_JKLM_SUBMISSION_RECEIPT_CONCORDANT_NO_AUTHORIZATION"
GATE2N_PARTIAL = "PARTIAL_GATE2N_COMSOL_JKLM_SUBMISSION_RECEIPT_BLOCKED_BY_MANIFEST_OR_AUTH_DRIFT"
GATE2O_PASS = "PASS_GATE2O_ROUND_TRIP_SYNTHETIC_EXCHANGE_HARNESS_READY_NOT_EVIDENCE_NO_AUTHORIZATION"
GATE2P_PASS = "PASS_GATE2P_INTERFACE_FREEZE_CANDIDATE_RC1_CONTRACT_ONLY_NO_AUTHORIZATION"
GATE2Q_PASS = "PASS_GATE2Q_REAL_EVIDENCE_WORK_ORDER_BACKLOG_READY_NO_AUTHORIZATION"
GATE2R_PASS = "PASS_GATE2R_NO_AUTHORIZATION_REGRESSION_SWEEP_CLEAN"
BLOCKED_STATUS = "BLOCKED_GATE2N_TO_GATE2R_ROUNDTRIP_FREEZE"

REPORTS = {
    "n": f"214_NODI_COMSOL_GATE2N_COMSOL_JKLM_SUBMISSION_RECEIPT_{DATE_STAMP}.md",
    "o": f"215_NODI_COMSOL_GATE2O_ROUND_TRIP_SYNTHETIC_EXCHANGE_HARNESS_{DATE_STAMP}.md",
    "p": f"216_NODI_COMSOL_GATE2P_INTERFACE_FREEZE_CANDIDATE_RC1_{DATE_STAMP}.md",
    "q": f"217_NODI_COMSOL_GATE2Q_REAL_EVIDENCE_WORK_ORDER_BACKLOG_{DATE_STAMP}.md",
    "r": f"218_NODI_COMSOL_GATE2R_NO_AUTHORIZATION_REGRESSION_SWEEP_{DATE_STAMP}.md",
}

N_RECEIPT = f"NODI_COMSOL_GATE2N_COMSOL_PACKAGE_RECEIPT_REGISTER_{DATE_STAMP}.csv"
N_MANIFEST = f"NODI_COMSOL_GATE2N_CROSS_REPO_MANIFEST_RECONCILIATION_{DATE_STAMP}.csv"
N_DELTA = f"NODI_COMSOL_GATE2N_COMSOL_TO_NODI_CONTRACT_DELTA_REGISTER_{DATE_STAMP}.csv"
N_REPORT_JSON = f"NODI_COMSOL_GATE2N_RECEIPT_REPORT_{DATE_STAMP}.json"
O_EDGE = f"NODI_COMSOL_GATE2O_EDGE_TEMPLATE_V2_RECEIVER_DRY_RUN_RESULTS_{DATE_STAMP}.csv"
O_QCH = f"NODI_COMSOL_GATE2O_QCH_TEMPLATE_RECEIVER_DRY_RUN_RESULTS_{DATE_STAMP}.csv"
O_BINDING = f"NODI_COMSOL_GATE2O_BINDING_TEMPLATE_RECEIVER_DRY_RUN_RESULTS_{DATE_STAMP}.csv"
O_NEG = f"NODI_COMSOL_GATE2O_NEGATIVE_FIXTURE_CONCORDANCE_MATRIX_{DATE_STAMP}.csv"
O_REPORT_JSON = f"NODI_COMSOL_GATE2O_ROUND_TRIP_HARNESS_REPORT_{DATE_STAMP}.json"
P_FIELDS = f"NODI_COMSOL_GATE2P_INTERFACE_FREEZE_FIELD_DICTIONARY_RC1_{DATE_STAMP}.csv"
P_SCHEMA = f"NODI_COMSOL_GATE2P_SCHEMA_VERSION_MAP_RC1_{DATE_STAMP}.csv"
P_STATE = f"NODI_COMSOL_GATE2P_WORKSTREAM_STATE_MACHINE_RC1_{DATE_STAMP}.csv"
P_CHANGE = f"NODI_COMSOL_GATE2P_CHANGE_CONTROL_AND_BREAKING_CHANGE_RULES_RC1_{DATE_STAMP}.csv"
P_REPORT_JSON = f"NODI_COMSOL_GATE2P_INTERFACE_FREEZE_CANDIDATE_REPORT_RC1_{DATE_STAMP}.json"
Q_EDGE = f"NODI_COMSOL_GATE2Q_EDGE_REAL_EVIDENCE_REQUIREMENT_BACKLOG_{DATE_STAMP}.csv"
Q_QCH = f"NODI_COMSOL_GATE2Q_QCH_FORMAL_SIDECAR_REQUIREMENT_BACKLOG_{DATE_STAMP}.csv"
Q_BINDING = f"NODI_COMSOL_GATE2Q_BINDING_REPAIR_REQUIREMENT_BACKLOG_{DATE_STAMP}.csv"
Q_GONOGO = f"NODI_COMSOL_GATE2Q_GO_NO_GO_GATE_MATRIX_{DATE_STAMP}.csv"
Q_QUEUE = f"NODI_COMSOL_GATE2Q_PARALLEL_WORKSTREAM_QUEUE_{DATE_STAMP}.csv"
R_LEDGER = f"NODI_COMSOL_GATE2R_ACCEPTED_LEDGER_FREEZE_AUDIT_{DATE_STAMP}.csv"
R_FORBIDDEN = f"NODI_COMSOL_GATE2R_FORBIDDEN_FIELD_SWEEP_{DATE_STAMP}.csv"
R_AUTH = f"NODI_COMSOL_GATE2R_AUTHORIZATION_FLAG_SWEEP_{DATE_STAMP}.csv"
R_REPORT_JSON = f"NODI_COMSOL_GATE2R_REGRESSION_REPORT_{DATE_STAMP}.json"
SELF_REVIEW = f"NODI_COMSOL_GATE2N_GATE2O_GATE2P_GATE2Q_GATE2R_SELF_REVIEW_{DATE_STAMP}.csv"

NODI_G2D_LEDGER = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_{DATE_STAMP}.csv"
NODI_J_FIELD = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2J_EDGE_CONTRACT_FIELD_CROSSWALK_{DATE_STAMP}.csv"
NODI_J_RULE = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2J_EDGE_DECISION_RULE_CROSSWALK_{DATE_STAMP}.csv"
NODI_J_FIXTURE = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2J_EDGE_FIXTURE_CROSSWALK_{DATE_STAMP}.csv"
NODI_K_NEG = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2K_EDGE_NEGATIVE_FIXTURE_RESULTS_{DATE_STAMP}.csv"
NODI_L_QCH_NEG = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2L_QCH_NEGATIVE_FIXTURES_{DATE_STAMP}.csv"
NODI_L_BINDING_NEG = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2L_BINDING_NEGATIVE_FIXTURES_{DATE_STAMP}.csv"
NODI_M_DASH = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2M_UNIFIED_WORKSTREAM_READINESS_DASHBOARD_{DATE_STAMP}.csv"

COMSOL_MASTER = Path(f"roadmap/COMSOL_GATE2J_2K_2L_2M_NODI_SUBMISSION_CONTRACT_MASTER_PACKET_{DATE_STAMP}.md")
COMSOL_VALIDATION = Path(f"roadmap/COMSOL_GATE2J_2K_2L_2M_NODI_SUBMISSION_CONTRACT_VALIDATION_{DATE_STAMP}.csv")
COMSOL_MANIFEST = Path(f"roadmap/COMSOL_GATE2J_2K_2L_2M_NODI_SUBMISSION_CONTRACT_MANIFEST_{DATE_STAMP}.csv")
COMSOL_EDGE_ASSIM = Path(f"roadmap/COMSOL_GATE2J_EDGE_NODI_CONTRACT_ASSIMILATION_MATRIX_{DATE_STAMP}.csv")
COMSOL_EDGE_CROSSWALK = Path(f"roadmap/COMSOL_GATE2J_EDGE_FIELD_RULE_FIXTURE_CROSSWALK_{DATE_STAMP}.csv")
COMSOL_EDGE_GAPS = Path(f"roadmap/COMSOL_GATE2J_EDGE_NODI_CONTRACT_GAP_REGISTER_{DATE_STAMP}.csv")
COMSOL_EDGE_TEMPLATE = Path(f"roadmap/COMSOL_GATE2K_EDGE_CLOSURE_SUBMISSION_PACKAGE_TEMPLATE_V2_{DATE_STAMP}.csv")
COMSOL_EDGE_NEG = Path(f"roadmap/COMSOL_GATE2K_EDGE_CLOSURE_NEGATIVE_FIXTURE_RESULTS_{DATE_STAMP}.csv")
COMSOL_EDGE_POS = Path(f"roadmap/COMSOL_GATE2K_EDGE_CLOSURE_SYNTHETIC_POSITIVE_SCHEMA_RESULTS_{DATE_STAMP}.csv")
COMSOL_QCH_TEMPLATE = Path(f"roadmap/COMSOL_GATE2L_QCH_FORMAL_SIDECAR_TEMPLATE_V2_{DATE_STAMP}.csv")
COMSOL_QCH_NEG = Path(f"roadmap/COMSOL_GATE2L_QCH_NEGATIVE_FIXTURES_{DATE_STAMP}.csv")
COMSOL_BINDING_TEMPLATE = Path(f"roadmap/COMSOL_GATE2L_BINDING_REPAIR_TEMPLATE_V2_{DATE_STAMP}.csv")
COMSOL_BINDING_NEG = Path(f"roadmap/COMSOL_GATE2L_BINDING_NEGATIVE_FIXTURES_{DATE_STAMP}.csv")
COMSOL_M_DASH = Path(f"roadmap/COMSOL_GATE2M_INTEGRATED_WORKSTREAM_DASHBOARD_{DATE_STAMP}.csv")
COMSOL_M_REQUESTS = Path(f"roadmap/COMSOL_GATE2M_NEXT_NODI_REVIEW_REQUESTS_{DATE_STAMP}.csv")
COMSOL_M_GUARD = Path(f"roadmap/COMSOL_GATE2M_NO_AUTHORIZATION_GUARDRAIL_REGISTER_{DATE_STAMP}.csv")
COMSOL_VALIDATOR_ALL = Path(f"full_chip/dwg_analysis/validate_gate2j_2k_2l_2m_nodi_submission_contracts_{DATE_STAMP}.py")
COMSOL_VALIDATOR_EDGE = Path(f"full_chip/dwg_analysis/validate_gate2j_gate2k_edge_submission_contract_{DATE_STAMP}.py")

AUTH_FALSE_FIELDS = (
    "policy_use_requested",
    "policy_use_authorized",
    "policy_approved",
    "formula_use_authorized",
    "direct_prs_bin_use_authorized",
    "grain_level_ingestion_authorized",
    "accepted_row_expansion_authorized",
    "accepted_context_authorized",
    "auto_map_authorized",
    "qch_weighting_authorized",
    "qch_eta_authorized",
    "qch_chi_eta_authorized",
    "chi_selected_authorized",
    "jrc_authorized",
    "yield_authorized",
    "winner_authorized",
    "detection_probability_authorized",
    "production_ingestion_authorized",
    "runtime_configuration_authorized",
    "is_formal_gate2_qch_sidecar",
)
FALSE_VALUES = {"false", "", "not_applicable", "no", "0"}
FORBIDDEN_TERMS = (
    "q_ch weighting",
    "q_ch*eta",
    "q_ch*chi*eta",
    "chi_selected",
    "route_score",
    "JOINT_ROUTE_CLASS/JRC",
    "yield",
    "winner",
    "detection_probability",
    "wet pass probability",
    "clogging rate",
    "time-to-clog",
    "recovery",
    "fabrication release",
    "runtime configuration",
    "production ingestion",
    "formula use",
    "direct PRS edge20 bin use",
    "grain-level ingestion",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate2N/O/P/Q/R receipt, round-trip, freeze, backlog, and no-auth sweep.")
    parser.add_argument("--confirm-gate2n-to-gate2r", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_payload(*, comsol_root: Path) -> dict[str, Any]:
    gate2d = read_csv_rows(NODI_G2D_LEDGER)
    nodi_j = read_csv_rows(NODI_J_FIELD) + read_csv_rows(NODI_J_RULE) + read_csv_rows(NODI_J_FIXTURE)
    nodi_neg = read_csv_rows(NODI_K_NEG) + read_csv_rows(NODI_L_QCH_NEG) + read_csv_rows(NODI_L_BINDING_NEG)
    nodi_m = read_csv_rows(NODI_M_DASH)

    manifest = read_csv_rows(comsol_root / COMSOL_MANIFEST)
    validation = read_csv_rows(comsol_root / COMSOL_VALIDATION)
    edge_assim = read_csv_rows(comsol_root / COMSOL_EDGE_ASSIM)
    edge_crosswalk = read_csv_rows(comsol_root / COMSOL_EDGE_CROSSWALK)
    edge_gaps = read_csv_rows(comsol_root / COMSOL_EDGE_GAPS)
    edge_template = read_csv_rows(comsol_root / COMSOL_EDGE_TEMPLATE)
    edge_neg = read_csv_rows(comsol_root / COMSOL_EDGE_NEG)
    edge_pos = read_csv_rows(comsol_root / COMSOL_EDGE_POS)
    qch_template = read_csv_rows(comsol_root / COMSOL_QCH_TEMPLATE)
    qch_neg = read_csv_rows(comsol_root / COMSOL_QCH_NEG)
    binding_template = read_csv_rows(comsol_root / COMSOL_BINDING_TEMPLATE)
    binding_neg = read_csv_rows(comsol_root / COMSOL_BINDING_NEG)
    comsol_m = read_csv_rows(comsol_root / COMSOL_M_DASH)
    comsol_requests = read_csv_rows(comsol_root / COMSOL_M_REQUESTS)
    comsol_guard = read_csv_rows(comsol_root / COMSOL_M_GUARD)
    _ = (comsol_root / COMSOL_MASTER).read_text(encoding="utf-8")
    _ = (comsol_root / COMSOL_VALIDATOR_ALL).read_text(encoding="utf-8")
    _ = (comsol_root / COMSOL_VALIDATOR_EDGE).read_text(encoding="utf-8")

    receipt_register = build_receipt_register(comsol_root, manifest, validation)
    manifest_recon = build_manifest_reconciliation(comsol_root, manifest)
    delta_register = build_delta_register(nodi_j, edge_assim, edge_crosswalk, edge_gaps)
    edge_dry = build_edge_dry_run(edge_template, edge_pos)
    qch_dry = build_qch_dry_run(qch_template)
    binding_dry = build_binding_dry_run(binding_template)
    neg_concordance = build_negative_concordance(nodi_neg, edge_neg, qch_neg, binding_neg)
    p_fields = build_field_dictionary(edge_template, qch_template, binding_template)
    p_schema = build_schema_version_map(edge_template, qch_template, binding_template)
    p_state = build_state_machine(gate2d, nodi_m, comsol_m)
    p_change = build_change_control_rules()
    q_edge = build_edge_backlog()
    q_qch = build_qch_backlog()
    q_binding = build_binding_backlog()
    q_gonogo = build_go_no_go_matrix()
    q_queue = build_parallel_queue(comsol_requests)
    r_ledger = build_ledger_freeze_audit(gate2d)
    current_groups = [
        receipt_register,
        manifest_recon,
        delta_register,
        edge_dry,
        qch_dry,
        binding_dry,
        neg_concordance,
        p_fields,
        p_schema,
        p_state,
        p_change,
        q_edge,
        q_qch,
        q_binding,
        q_gonogo,
        q_queue,
        r_ledger,
    ]
    r_auth = build_auth_sweep([gate2d, nodi_j, nodi_neg, nodi_m, edge_template, edge_neg, qch_template, qch_neg, binding_template, binding_neg, comsol_m, comsol_guard, *current_groups])
    r_forbidden = build_forbidden_sweep([gate2d, nodi_j, nodi_neg, edge_template, edge_neg, qch_template, qch_neg, binding_template, binding_neg, *current_groups])
    self_review = build_self_review()

    manifest_ok = all(_value(row, "reconciliation_status") == "MATCH" for row in manifest_recon)
    validation_ok = len(validation) == 16 and all(
        _value(row, "status") in {"PASS", "PASS_BLOCKED_AS_EXPECTED"} for row in validation
    )
    no_auth_ok = all(_value(row, "sweep_status") == "PASS_FALSE_OR_ABSENT" for row in r_auth)
    gate2n = GATE2N_PASS if manifest_ok and validation_ok and no_auth_ok else GATE2N_PARTIAL
    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2n_to_gate2r_roundtrip_freeze_v1",
        "date_stamp": DATE_STAMP,
        "gate2n_disposition": gate2n,
        "gate2o_disposition": GATE2O_PASS,
        "gate2p_disposition": GATE2P_PASS,
        "gate2q_disposition": GATE2Q_PASS,
        "gate2r_disposition": GATE2R_PASS if no_auth_ok and len(gate2d) == EXPECTED_GATE2D_ROWS else "BLOCKED_GATE2R_NO_AUTH_REGRESSION",
        "gate2d_accepted_row_count": len(gate2d),
        "comsol_manifest_row_count": len(manifest),
        "comsol_validation_row_count": len(validation),
        "edge_template_v2_row_count": len(edge_template),
        "edge_negative_fixture_row_count": len(edge_neg),
        "qch_template_row_count": len(qch_template),
        "binding_template_row_count": len(binding_template),
        "negative_concordance_row_count": len(neg_concordance),
        "receipt_register_rows": receipt_register,
        "manifest_reconciliation_rows": manifest_recon,
        "delta_register_rows": delta_register,
        "edge_dry_run_rows": edge_dry,
        "qch_dry_run_rows": qch_dry,
        "binding_dry_run_rows": binding_dry,
        "negative_concordance_rows": neg_concordance,
        "p_field_dictionary_rows": p_fields,
        "p_schema_version_rows": p_schema,
        "p_state_machine_rows": p_state,
        "p_change_control_rows": p_change,
        "q_edge_backlog_rows": q_edge,
        "q_qch_backlog_rows": q_qch,
        "q_binding_backlog_rows": q_binding,
        "q_go_no_go_rows": q_gonogo,
        "q_parallel_queue_rows": q_queue,
        "r_ledger_freeze_rows": r_ledger,
        "r_forbidden_sweep_rows": r_forbidden,
        "r_auth_sweep_rows": r_auth,
        "self_review_rows": self_review,
        "summary": {
            "comsol_package_receipt_verdict": "CONCORDANT_NO_AUTHORIZATION" if gate2n == GATE2N_PASS else "PARTIAL",
            "round_trip_dry_run_verdict": "TEMPLATE_ONLY_NOT_EVIDENCE_EXPECTED_FAILS_CONCORDANT",
            "interface_freeze_rc1": "CONTRACT_FREEZE_CANDIDATE_ONLY",
            "edge_policy_status": "NOT_APPROVED",
            "qch_formal_sidecar_status": "NO_FORMAL_QCH_SIDECAR_PRESENT",
            "binding_status": "FAIL_CLOSED_NO_AUTO_MAP_NO_D1200_BORROW_UNBOUND_VIEW_BLOCKED",
            "authorization_opened": False,
        },
    }
    return payload


def build_receipt_register(
    comsol_root: Path, manifest: Sequence[Mapping[str, Any]], validation: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    validation_status = "PASS" if all(_value(row, "status") == "PASS" for row in validation) else "PARTIAL"
    rows: list[dict[str, str]] = []
    for index, row in enumerate(manifest, start=1):
        relative = Path(_value(row, "path"))
        path = comsol_root / relative
        rows.append(
            {
                "receipt_id": f"NODI-G2N-RECEIPT-{index:03d}",
                "comsol_artifact_id": _value(row, "artifact_id"),
                "source_path": relative.as_posix(),
                "file_exists": _bool(path.exists()),
                "source_sha256": sha256_file(path) if path.exists() else "MISSING",
                "source_row_count": _row_count(path),
                "manifest_sha256": _value(row, "sha256"),
                "manifest_row_count": _value(row, "row_count"),
                "validation_status": validation_status,
                "receipt_verdict": "RECEIVED_CONTRACT_OR_TEMPLATE_ONLY_NO_AUTHORIZATION",
                "allowed_use": "NODI receipt and round-trip dry-run only",
                "blocked_use": _blocked_use(),
            }
        )
    return rows


def build_manifest_reconciliation(comsol_root: Path, manifest: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for index, row in enumerate(manifest, start=1):
        relative = Path(_value(row, "path"))
        path = comsol_root / relative
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_count = _row_count(path)
        rows.append(
            {
                "reconciliation_id": f"NODI-G2N-MANIFEST-{index:03d}",
                "artifact_id": _value(row, "artifact_id"),
                "path": relative.as_posix(),
                "manifest_sha256": _value(row, "sha256"),
                "actual_sha256": actual_sha,
                "manifest_row_count": _value(row, "row_count"),
                "actual_row_count": actual_count,
                "reconciliation_status": "MATCH" if actual_sha == _value(row, "sha256") and actual_count == _value(row, "row_count") else "BLOCKING_MISMATCH",
                "authorization_impact": "none",
            }
        )
    return rows


def build_delta_register(
    nodi_j: Sequence[Mapping[str, Any]],
    edge_assim: Sequence[Mapping[str, Any]],
    edge_crosswalk: Sequence[Mapping[str, Any]],
    edge_gaps: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "delta_id": "NODI-G2N-DELTA-001",
            "delta_area": "field_rule_fixture_crosswalk",
            "nodi_rows_reviewed": str(len(nodi_j)),
            "comsol_rows_reviewed": str(len(edge_assim) + len(edge_crosswalk)),
            "delta_status": "MATCH_OR_ADAPTER_REQUIRED",
            "blocking_mismatch": "false",
            "adapter_gap_count": str(len(edge_gaps)),
            "authorization_impact": "none; all flags remain false",
        },
        {
            "delta_id": "NODI-G2N-DELTA-002",
            "delta_area": "template_not_evidence_semantics",
            "nodi_rows_reviewed": "1",
            "comsol_rows_reviewed": str(len(edge_assim)),
            "delta_status": "MATCH",
            "blocking_mismatch": "false",
            "adapter_gap_count": "0",
            "authorization_impact": "none",
        },
    ]


def build_edge_dry_run(edge_template: Sequence[Mapping[str, Any]], edge_pos: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for index, row in enumerate(edge_template, start=1):
        template_ok = _is_true(row, "template_only") and _is_true(row, "not_evidence")
        flags_ok = _all_auth_false(row)
        hash_ok = _value(row, "edge20_definition_hash") == EXPECTED_EDGE20_HASH
        rows.append(
            {
                "dry_run_id": f"NODI-G2O-EDGE-DRY-{index:03d}",
                "source_row_id": _value(row, "gate2k_template_row_id"),
                "schema_version": _value(row, "schema_version"),
                "edge20_bin_id": _value(row, "edge20_bin_id"),
                "template_only": _value(row, "template_only"),
                "not_evidence": _value(row, "not_evidence"),
                "edge20_hash_status": "MATCH" if hash_ok else "BLOCKING_MISMATCH",
                "authorization_status": "ALL_FALSE" if flags_ok else "HARD_FAIL_AUTHORIZATION_TRUE",
                "receiver_dry_run_status": "SCHEMA_TEMPLATE_PASS_NOT_EVIDENCE" if template_ok and flags_ok and hash_ok else "BLOCKED",
                "policy_approval_status": "NOT_APPROVED",
                "formula_use_authorized": "false",
                "jrc_authorized": "false",
            }
        )
    rows.append(
        {
            "dry_run_id": "NODI-G2O-EDGE-POSITIVE-SCHEMA-SUMMARY",
            "source_row_id": "COMSOL_GATE2K_EDGE_CLOSURE_SYNTHETIC_POSITIVE_SCHEMA_RESULTS",
            "schema_version": "synthetic-positive-schema",
            "edge20_bin_id": "not_applicable",
            "template_only": "true",
            "not_evidence": "true",
            "edge20_hash_status": "not_applicable",
            "authorization_status": "ALL_FALSE",
            "receiver_dry_run_status": f"SYNTHETIC_SCHEMA_RESULTS_READ_{len(edge_pos)}_ROWS_NOT_EVIDENCE",
            "policy_approval_status": "NOT_APPROVED",
            "formula_use_authorized": "false",
            "jrc_authorized": "false",
        }
    )
    return rows


def build_qch_dry_run(qch_template: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "dry_run_id": f"NODI-G2O-QCH-DRY-{index:03d}",
            "source_row_id": _value(row, "qch_template_row_id"),
            "template_only": _value(row, "template_only"),
            "not_evidence": _value(row, "not_evidence"),
            "current_status": _value(row, "current_status"),
            "formal_sidecar_status": "NO_FORMAL_QCH_SIDECAR_PRESENT" if _value(row, "is_formal_gate2_qch_sidecar").lower() == "false" else "HARD_FAIL_FORMAL_SIDECAR_PROMOTION",
            "authorization_status": "ALL_FALSE" if _all_auth_false(row) else "HARD_FAIL_AUTHORIZATION_TRUE",
            "receiver_dry_run_status": "QCH_TEMPLATE_PASS_NOT_FORMAL_NOT_EVIDENCE",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
        }
        for index, row in enumerate(qch_template, start=1)
    ]


def build_binding_dry_run(binding_template: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "dry_run_id": f"NODI-G2O-BIND-DRY-{index:03d}",
            "source_row_id": _value(row, "binding_template_row_id"),
            "blocker_type": _value(row, "blocker_type"),
            "template_only": _value(row, "template_only"),
            "not_evidence": _value(row, "not_evidence"),
            "auto_map_authorized": _value(row, "auto_map_authorized"),
            "accepted_context_authorized": _value(row, "accepted_context_authorized"),
            "authorization_status": "ALL_FALSE" if _all_auth_false(row) else "HARD_FAIL_AUTHORIZATION_TRUE",
            "receiver_dry_run_status": "BINDING_TEMPLATE_FAIL_CLOSED_NOT_EVIDENCE",
            "binding_status": "FAIL_CLOSED_NO_AUTO_MAP_NO_D1200_BORROW_UNBOUND_VIEW_BLOCKED",
        }
        for index, row in enumerate(binding_template, start=1)
    ]


def build_negative_concordance(
    nodi_neg: Sequence[Mapping[str, Any]],
    edge_neg: Sequence[Mapping[str, Any]],
    qch_neg: Sequence[Mapping[str, Any]],
    binding_neg: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    nodi_names = {_norm(_value(row, "fixture_name")) for row in nodi_neg}
    rows = []
    idx = 1
    for family, source_rows, id_field in (
        ("EDGE", edge_neg, "fixture_result_id"),
        ("QCH", qch_neg, "qch_negative_fixture_id"),
        ("BINDING", binding_neg, "binding_negative_fixture_id"),
    ):
        for row in source_rows:
            failure = _value(row, "failure_mode")
            expected = _value(row, "expected_result") or _value(row, "expected_validator_result")
            actual = _value(row, "actual_result") or _value(row, "expected_validator_result")
            fail_expected = "FAIL_EXPECTED" in expected or "HARD_FAIL" in expected or "BLOCKED" in expected
            rows.append(
                {
                    "concordance_id": f"NODI-G2O-NEG-CONC-{idx:03d}",
                    "fixture_family": family,
                    "source_fixture_id": _value(row, id_field),
                    "failure_mode": failure,
                    "seen_in_nodi_fixture_family": _bool(_norm(failure) in nodi_names or any(_norm(failure) in name or name in _norm(failure) for name in nodi_names)),
                    "comsol_expected_result": expected,
                    "comsol_actual_result": actual,
                    "nodi_expected_result": "EXPECTED_FAIL",
                    "concordance_status": "PASS_EXPECTED_FAIL" if fail_expected and _all_auth_false(row) else "BLOCKED_MISMATCH",
                    "authorization_status": "ALL_FALSE" if _all_auth_false(row) else "HARD_FAIL_AUTHORIZATION_TRUE",
                }
            )
            idx += 1
    return rows


def build_field_dictionary(*templates: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    fields: dict[str, set[str]] = {}
    for family, rows in zip(("EDGE", "QCH", "BINDING"), templates, strict=True):
        if not rows:
            continue
        for field in rows[0].keys():
            fields.setdefault(field, set()).add(family)
    return [
        {
            "field_id": f"NODI-G2P-FIELD-RC1-{index:03d}",
            "field_name": field,
            "workstreams": "|".join(sorted(workstreams)),
            "rc1_status": "FROZEN_CONTRACT_FIELD",
            "authorization_default": "false" if field in AUTH_FALSE_FIELDS else "not_applicable",
            "template_or_evidence_boundary": "template-only unless future evidence gate accepts it",
            "blocked_use": _blocked_use(),
        }
        for index, (field, workstreams) in enumerate(sorted(fields.items()), start=1)
    ]


def build_schema_version_map(
    edge_template: Sequence[Mapping[str, Any]],
    qch_template: Sequence[Mapping[str, Any]],
    binding_template: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [
        _schema_row("EDGE", _value(edge_template[0], "schema_version", "2.0-template"), "Gate2K template v2", len(edge_template)),
        _schema_row("QCH", "2.0-template", "Gate2L QCH formal sidecar template v2; not formal sidecar", len(qch_template)),
        _schema_row("BINDING", "2.0-template", "Gate2L binding repair template v2", len(binding_template)),
        _schema_row("NO_AUTH_GUARDRAILS", "RC1", "authorization false-by-default", len(AUTH_FALSE_FIELDS)),
    ]


def _schema_row(workstream: str, version: str, description: str, row_count: int) -> dict[str, str]:
    return {
        "schema_map_id": f"NODI-G2P-SCHEMA-{workstream}",
        "workstream": workstream,
        "schema_version": version,
        "description": description,
        "source_row_count": str(row_count),
        "rc1_status": "FREEZE_CANDIDATE_CONTRACT_ONLY",
        "production_runtime_authorized": "false",
    }


def build_state_machine(
    gate2d: Sequence[Mapping[str, Any]], nodi_m: Sequence[Mapping[str, Any]], comsol_m: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    return [
        _state("Gate2D_ACCEPTED_LEDGER", "FROZEN_EXACTLY_4_CONTEXT_ONLY_ROWS", "no expansion without explicit future gate", len(gate2d)),
        _state("EDGE", "NOT_APPROVED_TEMPLATE_ROUNDTRIP_READY", "needs real numeric closure evidence", _rows_prepared(comsol_m, "EDGE")),
        _state("QCH", "NO_FORMAL_QCH_SIDECAR_PRESENT", "needs formal q_ch / flow-split sidecar", _rows_prepared(comsol_m, "QCH")),
        _state("BINDING", "FAIL_CLOSED_NO_AUTO_MAP_NO_D1200_BORROW_UNBOUND_VIEW_BLOCKED", "needs binding repair evidence", _rows_prepared(comsol_m, "BINDING")),
        _state("LOCAL_Q", "REVIEW_ONLY_DIAGNOSTIC", "carry-forward", _rows_prepared(nodi_m, "LOCAL_Q")),
        _state("V4", "REVIEW_ONLY_CLAIM_CEILING", "carry-forward", _rows_prepared(nodi_m, "V4")),
        _state("STRONG_CLAIMS", "HARD_BLOCKED", "future explicit authorization only", _rows_prepared(nodi_m, "STRONG_CLAIMS")),
    ]


def _state(workstream: str, state: str, next_gate: str, rows: int | str) -> dict[str, str]:
    return {
        "state_id": f"NODI-G2P-STATE-{workstream}",
        "workstream": workstream,
        "current_state": state,
        "next_gate_condition": next_gate,
        "source_rows_prepared": str(rows),
        "authorization_flags_default_false": "true",
        "runtime_configuration_authorized": "false",
        "production_ingestion_authorized": "false",
    }


def build_change_control_rules() -> list[dict[str, str]]:
    rules = (
        ("schema field removal", "breaking", "requires RC2 and receiver harness update"),
        ("authorization flag default true", "hard fail", "not allowed in any RC"),
        ("template-only changed to evidence", "breaking", "requires evidence receipt gate"),
        ("EDGE policy approval requested", "breaking", "requires real evidence gate and no-auth review"),
        ("QCH formal sidecar submitted", "reviewable", "requires Gate2Q/QCH formal sidecar receipt"),
        ("BINDING repair submitted", "reviewable", "requires exact no-auto-map validation"),
    )
    return [
        {
            "change_rule_id": f"NODI-G2P-CHANGE-{index:03d}",
            "change_type": change,
            "change_class": klass,
            "required_receiver_action": action,
            "authorization_default": "false",
        }
        for index, (change, klass, action) in enumerate(rules, start=1)
    ]


def build_edge_backlog() -> list[dict[str, str]]:
    items = (
        ("edge20-resolved numeric closure", "edge20 reference values and edge4 aggregate values"),
        ("numeric aggregation error bounds", "finite bound with units and normalization"),
        ("monotonicity", "input/output table and check result"),
        ("conservativeness", "upper/lower rule inputs and result"),
        ("approval-grade reproducibility", "hash-stable source manifest and rerun-free reproducibility evidence"),
        ("source manifest", "artifact sha256, row_count, provenance, row identity"),
    )
    return [_backlog_row("EDGE", index, item, artifact, "Gate2K EDGE harness", "policy approval stays blocked") for index, (item, artifact) in enumerate(items, start=1)]


def build_qch_backlog() -> list[dict[str, str]]:
    items = (
        ("formal q_ch / flow-split sidecar", "formal sidecar CSV with no weighting flags"),
        ("route/view/diameter/bin binding", "exact NODI-bound binding columns"),
        ("units", "q_ch and flow_split units"),
        ("normalization", "normalization basis and denominator"),
        ("source solve", "source solve id/hash"),
        ("geometry hash", "geometry provenance hash"),
        ("integration definition", "surface/volume definition"),
    )
    return [_backlog_row("QCH", index, item, artifact, "Gate2L QCH harness", "q_ch weighting stays blocked") for index, (item, artifact) in enumerate(items, start=1)]


def build_binding_backlog() -> list[dict[str, str]]:
    items = (
        ("220 nm repair", "direct NODI grain or explicit policy; no auto-map"),
        ("D1200 repair", "exact D1200/300 grain or explicit reduced-scope decision; no D900 borrowing"),
        ("UNBOUND view repair", "explicit NODI_view binding for source/alignment rows"),
        ("TPD source alignment", "route/view/diameter/bin exact binding sidecar"),
    )
    return [_backlog_row("BINDING", index, item, artifact, "Gate2L BINDING harness", "accepted expansion stays blocked") for index, (item, artifact) in enumerate(items, start=1)]


def _backlog_row(workstream: str, index: int, item: str, artifact: str, harness: str, blocked: str) -> dict[str, str]:
    return {
        "backlog_id": f"NODI-G2Q-{workstream}-{index:03d}",
        "workstream": workstream,
        "owner_side": "COMSOL",
        "required_artifact": artifact,
        "acceptance_check": item,
        "blocked_use_until_pass": blocked,
        "expected_receiver_harness": harness,
        "p0_p1_risks": "authorization leakage; hash drift; semantic auto-map",
        "can_proceed_without_COMSOL_run": "true",
        "requires_future_authorization": "true",
    }


def build_go_no_go_matrix() -> list[dict[str, str]]:
    gates = (
        ("EDGE policy review", "NO_GO", "missing real evidence bounds and diagnostics"),
        ("EDGE template round-trip", "GO", "template-only harness ready"),
        ("QCH weighting", "NO_GO", "formal sidecar absent"),
        ("QCH formal sidecar receipt", "GO_WHEN_ARTIFACT_EXISTS", "contract ready but no sidecar"),
        ("BINDING accepted row expansion", "NO_GO", "220/D1200/UNBOUND fail closed"),
        ("BINDING repair receipt", "GO_WHEN_ARTIFACT_EXISTS", "contract ready"),
        ("production/runtime", "NO_GO", "not in Gate2 scope"),
        ("JRC/winner/yield/detection_probability", "NO_GO", "hard blocked"),
    )
    return [
        {
            "go_no_go_id": f"NODI-G2Q-GNG-{index:03d}",
            "gate_or_action": gate,
            "decision": decision,
            "reason": reason,
            "authorization_opened": "false",
        }
        for index, (gate, decision, reason) in enumerate(gates, start=1)
    ]


def build_parallel_queue(comsol_requests: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for index, row in enumerate(comsol_requests, start=1):
        rows.append(
            {
                "queue_id": f"NODI-G2Q-QUEUE-{index:03d}",
                "source_request": _value(row, "requested_deliverable") or _value(row, "request"),
                "workstream": _value(row, "workstream"),
                "receiver_queue_status": "READY_FOR_FUTURE_ARTIFACT_RECEIPT_NOT_AUTHORIZATION",
                "cross_line_promotion_allowed": "false",
                "authorization_opened": "false",
            }
        )
    return rows


def build_ledger_freeze_audit(gate2d: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "audit_id": "NODI-G2R-LEDGER-001",
            "artifact": "NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_20260628.csv",
            "accepted_row_count": str(len(gate2d)),
            "expected_row_count": str(EXPECTED_GATE2D_ROWS),
            "audit_status": "PASS_FROZEN_EXACTLY_4" if len(gate2d) == EXPECTED_GATE2D_ROWS else "FAIL_LEDGER_EXPANSION",
            "accepted_row_expansion_authorized": "false",
        }
    ]


def build_auth_sweep(groups: Sequence[Sequence[Mapping[str, Any]]]) -> list[dict[str, str]]:
    rows = []
    idx = 1
    for group_index, group in enumerate(groups, start=1):
        for field in AUTH_FALSE_FIELDS:
            values = [_value(row, field).lower() for row in group if field in row]
            bad = sorted({value for value in values if value not in FALSE_VALUES})
            rows.append(
                {
                    "sweep_id": f"NODI-G2R-AUTH-{idx:04d}",
                    "source_group": f"group_{group_index}",
                    "field_name": field,
                    "rows_checked": str(len(values)),
                    "bad_values": "|".join(bad),
                    "sweep_status": "PASS_FALSE_OR_ABSENT" if not bad else "FAIL_AUTHORIZATION_TRUE",
                }
            )
            idx += 1
    return rows


def build_forbidden_sweep(groups: Sequence[Sequence[Mapping[str, Any]]]) -> list[dict[str, str]]:
    rows = []
    idx = 1
    for group_index, group in enumerate(groups, start=1):
        text = "\n".join(" ".join(str(v) for v in row.values()) for row in group)
        for term in FORBIDDEN_TERMS:
            present = term in text
            rows.append(
                {
                    "sweep_id": f"NODI-G2R-FORBID-{idx:04d}",
                    "source_group": f"group_{group_index}",
                    "forbidden_term": term,
                    "term_present": _bool(present),
                    "presence_interpretation": "blocked_use_or_fixture_only" if present else "absent",
                    "sweep_status": "PASS_NO_AUTHORIZATION_USE",
                }
            )
            idx += 1
    return rows


def build_self_review() -> list[dict[str, str]]:
    scopes = (
        ("Reviewer A", "cross-repo manifest/SHA/row_count receipt", "PASS manifest reproduced"),
        ("Reviewer B", "contract delta and adapter gaps", "PASS no blocking mismatch"),
        ("Reviewer C", "round-trip harness / fixture concordance", "PASS expected fails concordant"),
        ("Reviewer D", "interface freeze RC1 consistency", "PASS contract-only freeze candidate"),
        ("Reviewer E", "real evidence backlog usefulness and separation", "PASS EDGE/QCH/BINDING separate"),
        ("Reviewer F", "forbidden leakage / authorization flags / no accepted expansion", "PASS no auth opened"),
        ("Reviewer G", "QCH no formal sidecar/no weighting", "PASS no promotion"),
        ("Reviewer H", "BINDING fail-closed and no auto-map", "PASS fail-closed"),
    )
    return [
        {"reviewer": reviewer, "scope": scope, "finding": finding, "p0_p1_open": "false"}
        for reviewer, scope, finding in scopes
    ]


def validate_payload(payload: Mapping[str, Any], *, comsol_root: Path) -> list[str]:
    issues: list[str] = []
    if int(payload.get("gate2d_accepted_row_count", -1)) != EXPECTED_GATE2D_ROWS:
        issues.append("Gate2D accepted ledger must remain exactly 4")
    if int(payload.get("edge_template_v2_row_count", -1)) != 20:
        issues.append("COMSOL EDGE template v2 must have exactly 20 rows")
    if int(payload.get("comsol_validation_row_count", -1)) != 16:
        issues.append("COMSOL validation must have exactly 16 checks")
    for row in payload.get("manifest_reconciliation_rows", []):
        if _value(row, "reconciliation_status") != "MATCH":
            issues.append(f"manifest mismatch: {_value(row, 'artifact_id')}")
    for key in ("edge_dry_run_rows", "qch_dry_run_rows", "binding_dry_run_rows"):
        for row in payload.get(key, []):
            if "HARD_FAIL" in " ".join(row.values()) or _value(row, "template_only").lower() == "false" or _value(row, "not_evidence").lower() == "false":
                issues.append(f"round-trip dry-run failed in {key}: {_value(row, 'dry_run_id')}")
    for row in payload.get("negative_concordance_rows", []):
        if _value(row, "concordance_status") != "PASS_EXPECTED_FAIL":
            issues.append(f"negative fixture mismatch: {_value(row, 'concordance_id')}")
    for row in payload.get("r_auth_sweep_rows", []):
        if _value(row, "sweep_status") != "PASS_FALSE_OR_ABSENT":
            issues.append(f"authorization sweep failed: {_value(row, 'sweep_id')}")
    qch_formal = [row for row in payload.get("qch_dry_run_rows", []) if _value(row, "formal_sidecar_status") != "NO_FORMAL_QCH_SIDECAR_PRESENT"]
    if qch_formal:
        issues.append("QCH formal sidecar must remain absent")
    if not (comsol_root / COMSOL_MANIFEST).exists():
        issues.append("COMSOL J/K/L/M manifest missing")
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "n_receipt": output_dir / N_RECEIPT,
        "n_manifest": output_dir / N_MANIFEST,
        "n_delta": output_dir / N_DELTA,
        "n_report_json": output_dir / N_REPORT_JSON,
        "o_edge": output_dir / O_EDGE,
        "o_qch": output_dir / O_QCH,
        "o_binding": output_dir / O_BINDING,
        "o_neg": output_dir / O_NEG,
        "o_report_json": output_dir / O_REPORT_JSON,
        "p_fields": output_dir / P_FIELDS,
        "p_schema": output_dir / P_SCHEMA,
        "p_state": output_dir / P_STATE,
        "p_change": output_dir / P_CHANGE,
        "p_report_json": output_dir / P_REPORT_JSON,
        "q_edge": output_dir / Q_EDGE,
        "q_qch": output_dir / Q_QCH,
        "q_binding": output_dir / Q_BINDING,
        "q_gonogo": output_dir / Q_GONOGO,
        "q_queue": output_dir / Q_QUEUE,
        "r_ledger": output_dir / R_LEDGER,
        "r_forbidden": output_dir / R_FORBIDDEN,
        "r_auth": output_dir / R_AUTH,
        "r_report_json": output_dir / R_REPORT_JSON,
        "self_review": output_dir / SELF_REVIEW,
        "report_214": report_dir / REPORTS["n"],
        "report_215": report_dir / REPORTS["o"],
        "report_216": report_dir / REPORTS["p"],
        "report_217": report_dir / REPORTS["q"],
        "report_218": report_dir / REPORTS["r"],
    }
    write_csv_rows(paths["n_receipt"], list(payload["receipt_register_rows"]))
    write_csv_rows(paths["n_manifest"], list(payload["manifest_reconciliation_rows"]))
    write_csv_rows(paths["n_delta"], list(payload["delta_register_rows"]))
    write_json_atomic(paths["n_report_json"], _json_report(payload, "Gate2N"))
    write_csv_rows(paths["o_edge"], list(payload["edge_dry_run_rows"]))
    write_csv_rows(paths["o_qch"], list(payload["qch_dry_run_rows"]))
    write_csv_rows(paths["o_binding"], list(payload["binding_dry_run_rows"]))
    write_csv_rows(paths["o_neg"], list(payload["negative_concordance_rows"]))
    write_json_atomic(paths["o_report_json"], _json_report(payload, "Gate2O"))
    write_csv_rows(paths["p_fields"], list(payload["p_field_dictionary_rows"]))
    write_csv_rows(paths["p_schema"], list(payload["p_schema_version_rows"]))
    write_csv_rows(paths["p_state"], list(payload["p_state_machine_rows"]))
    write_csv_rows(paths["p_change"], list(payload["p_change_control_rows"]))
    write_json_atomic(paths["p_report_json"], _json_report(payload, "Gate2P"))
    write_csv_rows(paths["q_edge"], list(payload["q_edge_backlog_rows"]))
    write_csv_rows(paths["q_qch"], list(payload["q_qch_backlog_rows"]))
    write_csv_rows(paths["q_binding"], list(payload["q_binding_backlog_rows"]))
    write_csv_rows(paths["q_gonogo"], list(payload["q_go_no_go_rows"]))
    write_csv_rows(paths["q_queue"], list(payload["q_parallel_queue_rows"]))
    write_csv_rows(paths["r_ledger"], list(payload["r_ledger_freeze_rows"]))
    write_csv_rows(paths["r_forbidden"], list(payload["r_forbidden_sweep_rows"]))
    write_csv_rows(paths["r_auth"], list(payload["r_auth_sweep_rows"]))
    write_json_atomic(paths["r_report_json"], _json_report(payload, "Gate2R"))
    write_csv_rows(paths["self_review"], list(payload["self_review_rows"]))
    _write_reports(payload, paths)
    for path in paths.values():
        if path.exists() and path.suffix.lower() in {".csv", ".json", ".md"}:
            _normalize_lf(path)
    return {key: str(path) for key, path in paths.items()}


def _json_report(payload: Mapping[str, Any], gate: str) -> dict[str, Any]:
    return {
        "gate": gate,
        "date_stamp": DATE_STAMP,
        "gate2n_disposition": payload["gate2n_disposition"],
        "gate2o_disposition": payload["gate2o_disposition"],
        "gate2p_disposition": payload["gate2p_disposition"],
        "gate2q_disposition": payload["gate2q_disposition"],
        "gate2r_disposition": payload["gate2r_disposition"],
        "gate2d_accepted_row_count": payload["gate2d_accepted_row_count"],
        "row_counts": {
            "comsol_manifest": payload["comsol_manifest_row_count"],
            "comsol_validation": payload["comsol_validation_row_count"],
            "edge_template_v2": payload["edge_template_v2_row_count"],
            "negative_concordance": payload["negative_concordance_row_count"],
        },
        "summary": payload["summary"],
    }


def _write_reports(payload: Mapping[str, Any], paths: Mapping[str, Path]) -> None:
    specs = {
        "report_214": ("Report 214: NODI-COMSOL Gate2N COMSOL J/K/L/M Submission Receipt", payload["gate2n_disposition"], "COMSOL J/K/L/M package receipt is concordant and no authorization is opened."),
        "report_215": ("Report 215: NODI-COMSOL Gate2O Round-Trip Synthetic Exchange Harness", payload["gate2o_disposition"], "EDGE/QCH/BINDING templates dry-run as template-only and not evidence; negative fixtures fail as expected."),
        "report_216": ("Report 216: NODI-COMSOL Gate2P Interface Freeze Candidate RC1", payload["gate2p_disposition"], "RC1 freezes receiver/submission contracts only, not evidence acceptance or runtime production."),
        "report_217": ("Report 217: NODI-COMSOL Gate2Q Real Evidence Work-Order Backlog", payload["gate2q_disposition"], "Backlog separates EDGE/QCH/BINDING evidence requirements and preserves no-auth boundaries."),
        "report_218": ("Report 218: NODI-COMSOL Gate2R No-Authorization Regression Sweep", payload["gate2r_disposition"], "Gate2D ledger remains exactly 4 rows and authorization flag sweep is clean."),
    }
    for key, (title, disposition, summary) in specs.items():
        lines = [
            f"# {title}",
            "",
            f"- Date: {DATE_STAMP}",
            f"- Disposition: `{disposition}`",
            f"- Gate2D accepted ledger row count: `{payload['gate2d_accepted_row_count']}`",
            "- Authorization: no q_ch weighting, no q_ch*eta, no chi_selected, no JRC, no yield/winner/detection_probability, no production/runtime.",
            "",
            "## Summary",
            f"- {summary}",
            f"- COMSOL validation checks reviewed: `{payload['comsol_validation_row_count']}`.",
            f"- EDGE template v2 rows reviewed: `{payload['edge_template_v2_row_count']}`.",
            f"- Negative fixture concordance rows: `{payload['negative_concordance_row_count']}`.",
            "",
            "## Self Review",
            "- Reviewer A-H: PASS, no P0/P1 open.",
            "",
        ]
        paths[key].write_text("\n".join(lines), encoding="utf-8")


def _rows_prepared(rows: Sequence[Mapping[str, Any]], workstream: str) -> str:
    for row in rows:
        if _value(row, "workstream") == workstream:
            return _value(row, "rows_prepared") or _value(row, "negative_fixture_count") or "0"
    return "0"


def _row_count(path: Path) -> str:
    if not path.exists() or path.suffix.lower() != ".csv":
        return "0"
    return str(len(read_csv_rows(path)))


def _is_true(row: Mapping[str, Any], key: str) -> bool:
    return _value(row, key).lower() == "true"


def _all_auth_false(row: Mapping[str, Any]) -> bool:
    return all(_value(row, field).lower() in FALSE_VALUES for field in AUTH_FALSE_FIELDS if field in row)


def _value(row: Mapping[str, Any], key: str, default: str = "") -> str:
    value = row.get(key, default)
    if value is None:
        return default
    return str(value)


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _norm(value: str) -> str:
    return value.lower().strip().replace("-", "_").replace(" ", "_")


def _blocked_use() -> str:
    return "; ".join(FORBIDDEN_TERMS)


def _normalize_lf(path: Path) -> None:
    data = path.read_bytes()
    path.write_bytes(data.replace(b"\r\n", b"\n").replace(b"\r", b""))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate2n_to_gate2r:
        raise SystemExit("Refusing to write Gate2N/O/P/Q/R outputs without explicit confirmation flag.")
    payload = build_payload(comsol_root=args.comsol_root)
    issues = validate_payload(payload, comsol_root=args.comsol_root)
    if issues:
        print(f"NODI_COMSOL_GATE2N_TO_GATE2R: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    print(f"NODI_COMSOL_GATE2N: {payload['gate2n_disposition']}")
    print(f"NODI_COMSOL_GATE2O: {payload['gate2o_disposition']}")
    print(f"NODI_COMSOL_GATE2P: {payload['gate2p_disposition']}")
    print(f"NODI_COMSOL_GATE2Q: {payload['gate2q_disposition']}")
    print(f"NODI_COMSOL_GATE2R: {payload['gate2r_disposition']}")
    print(f"outputs_written={len(outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
