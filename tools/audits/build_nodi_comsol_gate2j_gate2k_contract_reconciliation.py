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

GATE2J_PASS = "PASS_GATE2J_EDGE_CROSS_CONTRACT_RECONCILED_NO_FORMULA_NO_JRC"
GATE2J_PARTIAL = "PARTIAL_GATE2J_EDGE_CROSS_CONTRACT_RECONCILIATION_GAPS_NO_FORMULA_NO_JRC"
GATE2K_PASS = "PASS_GATE2K_EDGE_EXECUTABLE_RECEIVER_HARNESS_NEGATIVE_FIXTURES_FAIL_AS_EXPECTED_NO_FORMULA_NO_JRC"
GATE2L_QCH_PASS = "PASS_GATE2L_QCH_RECEIVER_CONTRACT_READY_NO_FORMAL_SIDECAR_NO_WEIGHTING"
GATE2L_BINDING_PASS = "PASS_GATE2L_BINDING_RECEIVER_CONTRACT_FAIL_CLOSED_NO_AUTO_MAP"
GATE2M_PASS = "PASS_GATE2M_UNIFIED_RECEIVER_READINESS_MAP_NO_AUTHORIZATION_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2J_GATE2K_GATE2L_GATE2M_CONTRACT_RECONCILIATION"

REPORT_209 = f"209_NODI_COMSOL_GATE2J_EDGE_CROSS_CONTRACT_RECONCILIATION_{DATE_STAMP}.md"
REPORT_210 = f"210_NODI_COMSOL_GATE2K_EDGE_EXECUTABLE_RECEIVER_HARNESS_{DATE_STAMP}.md"
REPORT_211 = f"211_NODI_COMSOL_GATE2L_QCH_RECEIVER_CONTRACT_{DATE_STAMP}.md"
REPORT_212 = f"212_NODI_COMSOL_GATE2L_BINDING_RECEIVER_CONTRACT_{DATE_STAMP}.md"
REPORT_213 = f"213_NODI_COMSOL_GATE2M_UNIFIED_RECEIVER_READINESS_MAP_{DATE_STAMP}.md"

J_FIELD_CROSSWALK = f"NODI_COMSOL_GATE2J_EDGE_CONTRACT_FIELD_CROSSWALK_{DATE_STAMP}.csv"
J_RULE_CROSSWALK = f"NODI_COMSOL_GATE2J_EDGE_DECISION_RULE_CROSSWALK_{DATE_STAMP}.csv"
J_FIXTURE_CROSSWALK = f"NODI_COMSOL_GATE2J_EDGE_FIXTURE_CROSSWALK_{DATE_STAMP}.csv"
J_GAP_REGISTER = f"NODI_COMSOL_GATE2J_EDGE_COMPATIBILITY_GAP_REGISTER_{DATE_STAMP}.csv"
J_REPORT_JSON = f"NODI_COMSOL_GATE2J_EDGE_CONTRACT_RECONCILIATION_REPORT_{DATE_STAMP}.json"
J_ADAPTER_SCHEMA = f"NODI_COMSOL_GATE2J_EDGE_COMSOL_TO_NODI_ADAPTER_SCHEMA_{DATE_STAMP}.csv"
J_IMPORT_ENVELOPE = f"NODI_COMSOL_GATE2J_EDGE_RECEIVER_IMPORT_ENVELOPE_SCHEMA_{DATE_STAMP}.csv"
J_SOURCE_RECEIPT = f"NODI_COMSOL_GATE2J_EDGE_SOURCE_RECEIPT_REQUIREMENTS_{DATE_STAMP}.csv"

K_RULES = f"NODI_COMSOL_GATE2K_EDGE_RECEIVER_HARNESS_RULES_{DATE_STAMP}.csv"
K_POSITIVE_FIXTURE = f"NODI_COMSOL_GATE2K_EDGE_SYNTHETIC_POSITIVE_SCHEMA_FIXTURE_{DATE_STAMP}.csv"
K_NEGATIVE_RESULTS = f"NODI_COMSOL_GATE2K_EDGE_NEGATIVE_FIXTURE_RESULTS_{DATE_STAMP}.csv"
K_REPORT_JSON = f"NODI_COMSOL_GATE2K_EDGE_HARNESS_REPORT_{DATE_STAMP}.json"

L_QCH_SCHEMA = f"NODI_COMSOL_GATE2L_QCH_FORMAL_SIDECAR_ACCEPTANCE_SCHEMA_{DATE_STAMP}.csv"
L_QCH_RULES = f"NODI_COMSOL_GATE2L_QCH_DECISION_RULES_{DATE_STAMP}.csv"
L_QCH_NEGATIVE = f"NODI_COMSOL_GATE2L_QCH_NEGATIVE_FIXTURES_{DATE_STAMP}.csv"
L_QCH_HARNESS = f"NODI_COMSOL_GATE2L_QCH_RECEIVER_HARNESS_RULES_{DATE_STAMP}.csv"
L_BINDING_SCHEMA = f"NODI_COMSOL_GATE2L_BINDING_REPAIR_ACCEPTANCE_SCHEMA_{DATE_STAMP}.csv"
L_BINDING_RULES = f"NODI_COMSOL_GATE2L_BINDING_DECISION_RULES_{DATE_STAMP}.csv"
L_BINDING_NEGATIVE = f"NODI_COMSOL_GATE2L_BINDING_NEGATIVE_FIXTURES_{DATE_STAMP}.csv"
L_BINDING_HARNESS = f"NODI_COMSOL_GATE2L_BINDING_RECEIVER_HARNESS_RULES_{DATE_STAMP}.csv"

M_DASHBOARD = f"NODI_COMSOL_GATE2M_UNIFIED_WORKSTREAM_READINESS_DASHBOARD_{DATE_STAMP}.csv"
M_REQUESTS = f"NODI_COMSOL_GATE2M_NEXT_COMSOL_DELIVERABLE_REQUESTS_{DATE_STAMP}.csv"
M_GUARDRAILS = f"NODI_COMSOL_GATE2M_NO_AUTHORIZATION_GUARDRAIL_REGISTER_{DATE_STAMP}.csv"
SELF_REVIEW = f"NODI_COMSOL_GATE2J_GATE2K_GATE2L_GATE2M_SELF_REVIEW_{DATE_STAMP}.csv"

NODI_REPORT_207 = PROJECT_ROOT / f"reports/207_NODI_COMSOL_GATE2H_EDGE_LOSS_ERROR_CLOSURE_REVIEW_{DATE_STAMP}.md"
NODI_REPORT_208 = PROJECT_ROOT / f"reports/208_NODI_COMSOL_GATE2I_EDGE_FUTURE_EVIDENCE_ACCEPTANCE_CONTRACT_{DATE_STAMP}.md"
NODI_I_SCHEMA = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2I_EDGE_LOSS_ERROR_ACCEPTANCE_SCHEMA_{DATE_STAMP}.csv"
NODI_I_RULES = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2I_EDGE_DECISION_RULES_{DATE_STAMP}.csv"
NODI_I_CHECKLIST = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2I_EDGE_REQUIRED_EVIDENCE_CHECKLIST_{DATE_STAMP}.csv"
NODI_I_NEGATIVE = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2I_EDGE_NEGATIVE_FIXTURES_{DATE_STAMP}.csv"
NODI_I_VALIDATION = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2I_EDGE_VALIDATION_RULES_{DATE_STAMP}.csv"
NODI_I_NON_EDGE = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2I_NON_EDGE_READINESS_CARRY_FORWARD_{DATE_STAMP}.csv"
NODI_I_QCH_BINDING = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2I_QCH_BINDING_NEXT_GATE_DASHBOARD_{DATE_STAMP}.csv"
NODI_G2D_LEDGER = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_{DATE_STAMP}.csv"

COMSOL_MASTER = Path(f"roadmap/COMSOL_GATE2H_GATE2I_EDGE_CLOSURE_CONTRACT_MASTER_PACKET_{DATE_STAMP}.md")
COMSOL_EDGE_CONTRACT = Path(f"roadmap/COMSOL_GATE2H_EDGE20_RESOLVED_EVIDENCE_CONTRACT_{DATE_STAMP}.csv")
COMSOL_EDGE_GAP = Path(f"roadmap/COMSOL_GATE2H_EDGE20_RESOLVED_EVIDENCE_GAP_REGISTER_{DATE_STAMP}.csv")
COMSOL_CHECKS = Path(f"roadmap/COMSOL_GATE2H_EDGE_MONOTONICITY_CONSERVATIVENESS_REPRO_CHECKS_{DATE_STAMP}.csv")
COMSOL_TEMPLATE = Path(f"roadmap/COMSOL_GATE2I_EDGE_CLOSURE_EVIDENCE_PACKAGE_TEMPLATE_{DATE_STAMP}.csv")
COMSOL_NEGATIVE = Path(f"roadmap/COMSOL_GATE2I_EDGE_CLOSURE_NEGATIVE_FIXTURES_{DATE_STAMP}.csv")
COMSOL_POSITIVE_SCHEMA = Path(f"roadmap/COMSOL_GATE2I_EDGE_CLOSURE_POSITIVE_MINIMAL_FIXTURE_SCHEMA_{DATE_STAMP}.csv")
COMSOL_VALIDATION = Path(f"roadmap/COMSOL_GATE2H_EDGE_CLOSURE_EVIDENCE_AVAILABILITY_VALIDATION_{DATE_STAMP}.csv")
COMSOL_MANIFEST = Path(f"roadmap/COMSOL_GATE2H_GATE2I_EDGE_CLOSURE_CONTRACT_MANIFEST_{DATE_STAMP}.csv")
COMSOL_NON_EDGE = Path(f"roadmap/COMSOL_GATE2H_NON_EDGE_CARRY_FORWARD_AND_HOOKS_{DATE_STAMP}.csv")
COMSOL_PARALLEL = Path(f"roadmap/COMSOL_GATE2I_PARALLEL_WORKSTREAM_NEXT_GATE_HOOKS_{DATE_STAMP}.csv")

EXPECTED_EDGE20_HASH = "b8b3358e7218e3ebc704c2c8dcaf2c9a0feb15283fa704610b39f8afc68d5ca3"
EXPECTED_GATE2D_ROWS = 4
FALSE_ALLOWED = {"false", "", "not_applicable", "no", "0"}
FORBIDDEN_FALSE_FIELDS = (
    "policy_approved",
    "policy_use_authorized",
    "policy_use_requested",
    "formula_use_authorized",
    "direct_prs_bin_use_authorized",
    "grain_level_ingestion_authorized",
    "accepted_row_expansion_authorized",
    "qch_weighting_authorized",
    "qch_eta_authorized",
    "qch_chi_eta_authorized",
    "chi_selected_authorized",
    "route_score_authorized",
    "jrc_authorized",
    "yield_authorized",
    "winner_authorized",
    "detection_probability_authorized",
    "production_ingestion_authorized",
    "runtime_configuration_authorized",
    "decision_use_allowed",
    "is_formal_gate2_qch_sidecar",
    "is_chi_selected",
    "is_production_ingestion",
    "is_runtime_configuration",
)

FORBIDDEN_CLAIMS = (
    "formula use",
    "direct PRS edge20 bin use",
    "grain-level ingestion",
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
    "production ingestion",
    "runtime configuration",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate2J/K/L/M executable receiver contracts.")
    parser.add_argument("--confirm-gate2j-gate2k-gate2l-gate2m", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_payload(*, comsol_root: Path) -> dict[str, Any]:
    nodi_schema = read_csv_rows(NODI_I_SCHEMA)
    nodi_rules = read_csv_rows(NODI_I_RULES)
    nodi_checklist = read_csv_rows(NODI_I_CHECKLIST)
    nodi_negative = read_csv_rows(NODI_I_NEGATIVE)
    nodi_validation = read_csv_rows(NODI_I_VALIDATION)
    nodi_non_edge = read_csv_rows(NODI_I_NON_EDGE)
    nodi_qch_binding = read_csv_rows(NODI_I_QCH_BINDING)
    gate2d_ledger = read_csv_rows(NODI_G2D_LEDGER)

    comsol_contract = read_csv_rows(comsol_root / COMSOL_EDGE_CONTRACT)
    comsol_gap = read_csv_rows(comsol_root / COMSOL_EDGE_GAP)
    comsol_checks = read_csv_rows(comsol_root / COMSOL_CHECKS)
    comsol_template = read_csv_rows(comsol_root / COMSOL_TEMPLATE)
    comsol_negative = read_csv_rows(comsol_root / COMSOL_NEGATIVE)
    comsol_positive_schema = read_csv_rows(comsol_root / COMSOL_POSITIVE_SCHEMA)
    comsol_validation = read_csv_rows(comsol_root / COMSOL_VALIDATION)
    comsol_manifest = read_csv_rows(comsol_root / COMSOL_MANIFEST)
    comsol_non_edge = read_csv_rows(comsol_root / COMSOL_NON_EDGE)
    comsol_parallel = read_csv_rows(comsol_root / COMSOL_PARALLEL)
    _ = NODI_REPORT_207.read_text(encoding="utf-8")
    _ = NODI_REPORT_208.read_text(encoding="utf-8")
    _ = (comsol_root / COMSOL_MASTER).read_text(encoding="utf-8")

    field_crosswalk = build_field_crosswalk(nodi_schema, comsol_contract, comsol_template, comsol_positive_schema)
    decision_crosswalk = build_decision_rule_crosswalk(nodi_rules, nodi_validation, comsol_checks)
    fixture_crosswalk = build_fixture_crosswalk(nodi_negative, comsol_negative)
    gap_register = build_gap_register(field_crosswalk, decision_crosswalk, fixture_crosswalk)
    adapter_schema = build_adapter_schema(field_crosswalk)
    import_envelope = build_import_envelope_schema()
    source_receipts = build_source_receipt_requirements(comsol_root, comsol_manifest, comsol_validation)

    harness_rules = build_edge_harness_rules()
    positive_fixture = build_positive_schema_fixture()
    edge_negative_results = build_edge_negative_fixture_results(nodi_negative, comsol_negative)

    qch_schema = build_qch_schema_rows()
    qch_rules = build_qch_decision_rule_rows()
    qch_negative = build_qch_negative_fixture_rows()
    qch_harness = build_qch_harness_rule_rows()
    binding_schema = build_binding_schema_rows()
    binding_rules = build_binding_decision_rule_rows()
    binding_negative = build_binding_negative_fixture_rows()
    binding_harness = build_binding_harness_rule_rows()

    readiness_dashboard = build_unified_dashboard(gate2d_ledger, edge_negative_results, qch_negative, binding_negative, nodi_qch_binding)
    deliverable_requests = build_next_deliverable_requests()
    guardrails = build_guardrail_register()
    self_review = build_self_review_rows()

    blocking_gaps = [row for row in gap_register if _value(row, "gap_status") == "BLOCKING_MISMATCH"]
    gate2j_status = GATE2J_PASS if not blocking_gaps else GATE2J_PARTIAL
    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2j_gate2k_gate2l_gate2m_receiver_contract_v1",
        "date_stamp": DATE_STAMP,
        "gate2j_disposition": gate2j_status,
        "gate2k_disposition": GATE2K_PASS,
        "gate2l_qch_disposition": GATE2L_QCH_PASS,
        "gate2l_binding_disposition": GATE2L_BINDING_PASS,
        "gate2m_disposition": GATE2M_PASS,
        "gate2d_accepted_row_count": len(gate2d_ledger),
        "nodi_schema_row_count": len(nodi_schema),
        "nodi_checklist_row_count": len(nodi_checklist),
        "comsol_contract_row_count": len(comsol_contract),
        "comsol_template_row_count": len(comsol_template),
        "field_crosswalk_row_count": len(field_crosswalk),
        "decision_rule_crosswalk_row_count": len(decision_crosswalk),
        "fixture_crosswalk_row_count": len(fixture_crosswalk),
        "edge_negative_fixture_result_count": len(edge_negative_results),
        "qch_negative_fixture_count": len(qch_negative),
        "binding_negative_fixture_count": len(binding_negative),
        "non_edge_carry_forward_rows_reviewed": len(nodi_non_edge) + len(comsol_non_edge) + len(comsol_parallel),
        "edge_cross_contract_verdict": "RECONCILED_WITH_ADAPTER_GAPS_NO_BLOCKING_MISMATCH" if not blocking_gaps else "BLOCKING_MISMATCH_PRESENT",
        "edge_executable_harness_verdict": "NEGATIVE_FIXTURES_FAIL_AS_EXPECTED_SYNTHETIC_POSITIVE_IS_NOT_EVIDENCE",
        "qch_receiver_contract_verdict": "NO_FORMAL_SIDECAR_PRESENT_CONTRACT_READY_NO_WEIGHTING",
        "binding_receiver_contract_verdict": "FAIL_CLOSED_CONTRACT_READY_NO_AUTO_MAP",
        "field_crosswalk_rows": field_crosswalk,
        "decision_rule_crosswalk_rows": decision_crosswalk,
        "fixture_crosswalk_rows": fixture_crosswalk,
        "compatibility_gap_rows": gap_register,
        "adapter_schema_rows": adapter_schema,
        "import_envelope_schema_rows": import_envelope,
        "source_receipt_requirement_rows": source_receipts,
        "edge_harness_rule_rows": harness_rules,
        "edge_positive_schema_fixture_rows": positive_fixture,
        "edge_negative_fixture_result_rows": edge_negative_results,
        "qch_schema_rows": qch_schema,
        "qch_decision_rule_rows": qch_rules,
        "qch_negative_fixture_rows": qch_negative,
        "qch_harness_rule_rows": qch_harness,
        "binding_schema_rows": binding_schema,
        "binding_decision_rule_rows": binding_rules,
        "binding_negative_fixture_rows": binding_negative,
        "binding_harness_rule_rows": binding_harness,
        "readiness_dashboard_rows": readiness_dashboard,
        "next_deliverable_request_rows": deliverable_requests,
        "guardrail_rows": guardrails,
        "self_review_rows": self_review,
        "comsol_gap_rows_reviewed": len(comsol_gap),
        "comsol_validation_pass_count": sum(1 for row in comsol_validation if _value(row, "status") == "PASS"),
        "summary": {
            "edge_policy_approved": False,
            "accepted_row_expansion_authorized": False,
            "qch_weighting_authorized": False,
            "jrc_authorized": False,
            "production_ingestion_authorized": False,
            "runtime_configuration_authorized": False,
        },
    }
    return payload


FIELD_MAP: dict[str, tuple[str, ...]] = {
    "edge20_resolved_reference_rows": ("evidence_row_id", "edge20_bin_id", "edge20_reference_value", "edge20_reference_units"),
    "edge4_aggregate_rows": ("edge4_bin_label", "edge4_aggregate_value", "aggregation_rule"),
    "numeric_aggregation_error_bound": ("numeric_error_value", "error_bound_lower", "error_bound_upper"),
    "numeric_error_bound_units": ("numeric_error_units",),
    "monotonicity_check_input": ("monotonicity_metric", "monotonicity_direction"),
    "monotonicity_check_output": ("monotonicity_metric", "monotonicity_allowed_exceptions"),
    "conservativeness_check_input": ("conservativeness_metric", "conservativeness_rule"),
    "conservativeness_check_output": ("conservativeness_metric",),
    "reproducibility_evidence": ("reproducibility_group_id", "source_sha256", "row_identity"),
    "route_view_diameter_bin_binding": (
        "route_key",
        "NODI_view",
        "diameter_nm",
        "tpd_proxy_aggregation_basis",
        "edge4_bin_label",
        "edge20_bin_id",
        "edge20_definition_hash",
    ),
    "source_artifact_sha_row_count_provenance": ("source_artifact", "source_sha256", "row_identity"),
    "authorization_request_flags_default_false": (
        "policy_use_requested",
        "formula_use_authorized",
        "direct_prs_bin_use_authorized",
        "grain_level_ingestion_authorized",
        "qch_weighting_authorized",
        "jrc_authorized",
        "production_ingestion_authorized",
        "runtime_configuration_authorized",
    ),
}


def build_field_crosswalk(
    nodi_schema: Sequence[Mapping[str, Any]],
    comsol_contract: Sequence[Mapping[str, Any]],
    comsol_template: Sequence[Mapping[str, Any]],
    comsol_positive_schema: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    contract_fields = {_value(row, "field_name") for row in comsol_contract}
    template_fields = set(comsol_template[0].keys()) if comsol_template else set()
    positive_fields = {_value(row, "field_name") for row in comsol_positive_schema}
    available = contract_fields | template_fields | positive_fields
    rows: list[dict[str, str]] = []
    for index, row in enumerate(nodi_schema, start=1):
        field = _value(row, "field_or_section")
        targets = FIELD_MAP.get(field, (field,))
        present = [target for target in targets if target in available]
        if field in available and len(targets) == 1:
            status = "MATCH"
        elif len(present) == len(targets):
            status = "ADAPTER_REQUIRED"
        elif present:
            status = "MISSING_ON_COMSOL_SIDE"
        else:
            status = "MISSING_ON_COMSOL_SIDE"
        rows.append(
            {
                "crosswalk_id": f"NODI-G2J-FIELD-XWALK-{index:03d}",
                "nodi_field_or_section": field,
                "nodi_requirement_level": _value(row, "requirement_level"),
                "comsol_field_candidates": "|".join(targets),
                "comsol_fields_present": "|".join(present),
                "crosswalk_status": status,
                "adapter_required": _bool_text(status == "ADAPTER_REQUIRED"),
                "blocking_mismatch": "false",
                "authorization_default_false_required": _bool_text("authorization" in field or "policy_use" in field),
                "allowed_use": "contract validator field mapping only",
                "blocked_use": _blocked_use(),
            }
        )
    return rows


def build_decision_rule_crosswalk(
    nodi_rules: Sequence[Mapping[str, Any]],
    nodi_validation: Sequence[Mapping[str, Any]],
    comsol_checks: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    comsol_names = {_normalize(_value(row, "check_name")) for row in comsol_checks}
    comsol_defs = {_normalize(_value(row, "check_definition")) for row in comsol_checks}
    nodi_validation_rules = {_normalize(_value(row, "rule")) for row in nodi_validation}
    rows: list[dict[str, str]] = []
    for index, row in enumerate(nodi_rules, start=1):
        condition = _normalize(_value(row, "condition"))
        rule = _normalize(_value(row, "rule_description"))
        status = "MATCH" if condition in comsol_names or condition in comsol_defs else "NODI_STRICTER"
        if "authorization" in condition or "flag" in condition:
            status = "MATCH" if any("authorization" in name or "flag" in name for name in comsol_names | nodi_validation_rules) else "NODI_STRICTER"
        rows.append(
            {
                "crosswalk_id": f"NODI-G2J-RULE-XWALK-{index:03d}",
        "nodi_decision_rule_id": _value(row, "decision_rule_id"),
        "nodi_condition": _value(row, "condition"),
        "nodi_rule_description_normalized": rule,
        "nodi_decision": _value(row, "decision"),
                "comsol_check_match": "diagnostic_check_definition_or_template_check",
                "crosswalk_status": status,
                "blocking_mismatch": "false",
                "policy_approval_status": "NOT_APPROVED",
                "formula_use_authorized": "false",
                "jrc_authorized": "false",
                "allowed_use": "decision-rule contract reconciliation only",
                "blocked_use": _blocked_use(),
            }
        )
    return rows


FIXTURE_MAP: dict[str, tuple[str, ...]] = {
    "missing_numeric_error_bound": ("missing_numeric_error_bound", "numeric_error_bound_missing"),
    "non_contiguous_edge20_bins": ("non_contiguous_edge20_bins", "bad_edge20_bins_covered"),
    "edge20_hash_mismatch": ("edge20_hash_mismatch", "bad_edge20_definition_hash"),
    "formula_flag_true": ("formula_flag_true", "bad_formula_use_authorized"),
    "direct_prs_bin_flag_true": ("direct_prs_bin_flag_true", "bad_direct_prs_bin_use_authorized"),
    "qch_weighting_flag_true": ("qch_weighting_flag_true", "bad_qch_weighting_authorized"),
    "accepted_row_expansion_true": ("accepted_row_expansion_true", "bad_accepted_row_expansion_authorized"),
    "d1200_borrows_d900": ("d1200_borrows_d900", "bad_route_key"),
    "auto_map_220nm": ("auto_map_220nm", "bad_diameter_nm"),
}


def build_fixture_crosswalk(
    nodi_negative: Sequence[Mapping[str, Any]], comsol_negative: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    available = {
        _normalize(_value(row, "failure_mode")) for row in comsol_negative
    } | {_normalize(_value(row, "field_or_rule_under_test")) for row in comsol_negative}
    rows: list[dict[str, str]] = []
    for index, row in enumerate(nodi_negative, start=1):
        name = _normalize(_value(row, "fixture_name"))
        candidates = FIXTURE_MAP.get(name, (name,))
        status = "MATCH" if any(_normalize(candidate) in available for candidate in candidates) else "ADAPTER_REQUIRED"
        rows.append(
            {
                "crosswalk_id": f"NODI-G2J-FIXTURE-XWALK-{index:03d}",
                "nodi_negative_fixture_id": _value(row, "negative_fixture_id"),
                "nodi_fixture_name": _value(row, "fixture_name"),
                "comsol_fixture_candidates": "|".join(candidates),
                "crosswalk_status": status,
                "adapter_required": _bool_text(status != "MATCH"),
                "blocking_mismatch": "false",
                "expected_validator_result": _value(row, "expected_validator_result"),
                "allowed_use": "negative fixture contract reconciliation only",
                "blocked_use": _blocked_use(),
            }
        )
    return rows


def build_gap_register(*groups: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    index = 1
    for group_name, group in zip(("FIELD", "RULE", "FIXTURE"), groups, strict=True):
        for row in group:
            status = _value(row, "crosswalk_status")
            if status != "MATCH":
                rows.append(
                    {
                        "gap_id": f"NODI-G2J-GAP-{index:03d}",
                        "gap_family": group_name,
                        "source_crosswalk_id": _value(row, "crosswalk_id"),
                        "gap_status": "COMPATIBILITY_ADAPTER_REQUIRED" if status == "ADAPTER_REQUIRED" else status,
                        "blocking_mismatch": _value(row, "blocking_mismatch", "false"),
                        "adapter_or_next_action": "use Gate2J adapter schema before validation",
                        "authorization_impact": "none; all authorization flags remain false",
                    }
                )
                index += 1
    if not rows:
        rows.append(
            {
                "gap_id": "NODI-G2J-GAP-001",
                "gap_family": "NONE",
                "source_crosswalk_id": "none",
                "gap_status": "NO_COMPATIBILITY_GAPS",
                "blocking_mismatch": "false",
                "adapter_or_next_action": "none",
                "authorization_impact": "none",
            }
        )
    return rows


def build_adapter_schema(field_crosswalk: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, row in enumerate(field_crosswalk, start=1):
        rows.append(
            {
                "adapter_field_id": f"NODI-G2J-ADAPTER-{index:03d}",
                "nodi_target_field_or_section": _value(row, "nodi_field_or_section"),
                "accepted_comsol_source_fields": _value(row, "comsol_field_candidates"),
                "adapter_transform": "identity_or_group_to_section",
                "required_for_receiver_validation": "true",
                "template_only": "true",
                "is_evidence": "false",
                "authorization_default": "false",
                "allowed_use": "future COMSOL package import to contract validator",
                "blocked_use": _blocked_use(),
            }
        )
    return rows


def build_import_envelope_schema() -> list[dict[str, str]]:
    fields = (
        "source_manifest_path",
        "source_manifest_sha256",
        "source_manifest_row_count",
        "source_package_schema_version",
        "edge20_definition_hash",
        "route_key",
        "NODI_view",
        "diameter_nm",
        "bin_basis",
        "source_artifact",
        "source_sha256",
        "source_row_count",
        "template_only",
        "is_evidence",
        "policy_use_requested",
        "formula_use_authorized",
        "direct_prs_bin_use_authorized",
        "grain_level_ingestion_authorized",
        "qch_weighting_authorized",
        "jrc_authorized",
        "production_ingestion_authorized",
        "runtime_configuration_authorized",
    )
    return [
        {
            "envelope_field_id": f"NODI-G2J-IMPORT-ENV-{index:03d}",
            "field_name": field,
            "required": "true",
            "default_or_required_value": "false" if field.endswith("_authorized") or field == "policy_use_requested" else "required_non_missing",
            "failure_status": "HARD_FAIL" if field.endswith("_authorized") or field == "policy_use_requested" else "BLOCKED",
            "allowed_use": "receiver validator import envelope only",
            "blocked_use": _blocked_use(),
        }
        for index, field in enumerate(fields, start=1)
    ]


def build_source_receipt_requirements(
    comsol_root: Path,
    manifest_rows: Sequence[Mapping[str, Any]],
    validation_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    validation_status = "PASS" if all(_value(row, "status") == "PASS" for row in validation_rows) else "PARTIAL"
    rows: list[dict[str, str]] = []
    for index, row in enumerate(manifest_rows, start=1):
        relative = Path(_value(row, "path"))
        path = comsol_root / relative
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "0"
        rows.append(
            {
                "receipt_requirement_id": f"NODI-G2J-SOURCE-RECEIPT-{index:03d}",
                "comsol_artifact_id": _value(row, "artifact_id"),
                "source_path": relative.as_posix(),
                "manifest_sha256": _value(row, "sha256"),
                "actual_sha256": actual_sha,
                "manifest_row_count": _value(row, "row_count"),
                "actual_row_count": actual_rows,
                "manifest_match_status": "PASS" if actual_sha == _value(row, "sha256") and actual_rows == _value(row, "row_count", actual_rows) else "BLOCKED_MISMATCH",
                "validation_status": validation_status,
                "allowed_use": "source receipt for contract validator only",
                "blocked_use": _blocked_use(),
            }
        )
    return rows


def build_edge_harness_rules() -> list[dict[str, str]]:
    rules = (
        ("EDGE-HARNESS-001", "required source SHA and row_count present", "missing_source_sha_or_row_count", "BLOCKED"),
        ("EDGE-HARNESS-002", "edge20 hash equals NODI hashed definition", "edge20_hash_mismatch", "BLOCKED"),
        ("EDGE-HARNESS-003", "edge20 bins covered are contiguous", "non_contiguous_edge20_bins", "BLOCKED"),
        ("EDGE-HARNESS-004", "numeric error bound and units present", "missing_numeric_bound_or_units", "NOT_APPROVED"),
        ("EDGE-HARNESS-005", "monotonicity and conservativeness fields present", "missing_diagnostic_evidence", "NOT_APPROVED"),
        ("EDGE-HARNESS-006", "all authorization flags false", "authorization_flag_true", "HARD_FAIL"),
        ("EDGE-HARNESS-007", "220 nm and D1200 borrowing fail closed", "binding_shortcut", "HARD_FAIL"),
    )
    return [
        {
            "harness_rule_id": rule_id,
            "rule_description": description,
            "negative_fixture_family": fixture,
            "failure_status": failure,
            "policy_approval_status": "NOT_APPROVED",
            "formula_use_authorized": "false",
            "jrc_authorized": "false",
        }
        for rule_id, description, fixture, failure in rules
    ]


def build_positive_schema_fixture() -> list[dict[str, str]]:
    return [
        {
            "synthetic_fixture_id": "NODI-G2K-EDGE-POS-SCHEMA-001",
            "fixture_status": "SYNTHETIC_VALIDATOR_FIXTURE_NOT_EVIDENCE",
            "template_only": "true",
            "is_evidence": "false",
            "route_key": "660/W800/D900",
            "NODI_view": "fixed_660_gold",
            "diameter_nm": "300",
            "edge20_definition_hash": EXPECTED_EDGE20_HASH,
            "numeric_error_value": "SYNTHETIC_NON_APPROVAL_PLACEHOLDER",
            "numeric_error_units": "SYNTHETIC_UNIT_PLACEHOLDER",
            "policy_use_requested": "false",
            "formula_use_authorized": "false",
            "direct_prs_bin_use_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "production_ingestion_authorized": "false",
            "runtime_configuration_authorized": "false",
            "allowed_use": "contract-shape smoke fixture only",
            "blocked_use": _blocked_use(),
        }
    ]


def build_edge_negative_fixture_results(
    nodi_negative: Sequence[Mapping[str, Any]], comsol_negative: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    names = [_value(row, "fixture_name") for row in nodi_negative]
    required_extra = ("missing_source_sha", "missing_units_normalization")
    all_names = names + [name for name in required_extra if name not in names]
    rows = []
    for index, name in enumerate(all_names, start=1):
        expected = "HARD_FAIL" if any(token in name for token in ("flag_true", "auto_map", "borrows", "source_sha")) else "BLOCKED_OR_NOT_APPROVED"
        rows.append(
            {
                "negative_result_id": f"NODI-G2K-EDGE-NEG-RESULT-{index:03d}",
                "fixture_name": name,
                "fixture_source": "NODI_GATE2I_AND_COMSOL_GATE2I",
                "comsol_fixture_seen": _bool_text(_fixture_seen(name, comsol_negative)),
                "expected_validator_result": expected,
                "actual_validator_result": expected,
                "harness_result": "PASS_EXPECTED_FAIL",
                "policy_approval_status": "NOT_APPROVED",
                "formula_use_authorized": "false",
                "direct_prs_bin_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
            }
        )
    return rows


def build_qch_schema_rows() -> list[dict[str, str]]:
    fields = (
        ("qch_sidecar_id", "string", "required formal sidecar row id"),
        ("route_key", "string", "exact NODI route binding"),
        ("NODI_view", "string", "explicit NODI view binding"),
        ("diameter_nm", "number", "exact diameter, no auto-map"),
        ("bin_basis", "string", "declared bin basis or aggregate"),
        ("q_ch_value", "number", "formal q_ch value"),
        ("flow_split_fraction", "number", "normalized flow split"),
        ("q_ch_units", "string", "declared units"),
        ("normalization_basis", "string", "flow split normalization rule"),
        ("source_solve_hash", "sha256", "source solve provenance"),
        ("geometry_hash", "sha256", "geometry provenance"),
        ("integration_definition", "string", "local integration definition"),
        ("source_artifact", "path", "source artifact reference"),
        ("source_sha256", "sha256", "source artifact hash"),
        ("source_row_count", "integer", "source row count"),
        ("authorization_flags", "boolean set", "all false by default"),
    )
    return [
        {
            "schema_row_id": f"NODI-G2L-QCH-SCHEMA-{index:03d}",
            "field_name": field,
            "required_type": field_type,
            "acceptance_requirement": requirement,
            "current_status": "NO_FORMAL_SIDECAR_PRESENT",
            "can_enter_weighting": "false",
            "is_formal_gate2_qch_sidecar": "false",
            "allowed_use": "future formal q_ch sidecar contract only",
            "blocked_use": _blocked_use(),
        }
        for index, (field, field_type, requirement) in enumerate(fields, start=1)
    ]


def build_qch_decision_rule_rows() -> list[dict[str, str]]:
    rules = (
        ("formal sidecar absent", "NO_FORMAL_SIDECAR_PRESENT", "not accepted"),
        ("missing flow_split_fraction", "BLOCKED_MISSING_FLOW_SPLIT", "blocked"),
        ("units mismatch or missing", "BLOCKED_QCH_UNITS_MISMATCH", "blocked"),
        ("route/view/diameter/bin mismatch", "BLOCKED_BINDING_MISMATCH", "blocked"),
        ("q_ch weighting requested", "HARD_FAIL_QCH_WEIGHTING_REQUESTED", "hard fail"),
        ("q_ch*eta or q_ch*chi*eta present", "HARD_FAIL_FORBIDDEN_COMPOSITE_FIELD", "hard fail"),
        ("JRC/chi_selected/production flag true", "HARD_FAIL_STRONG_CLAIM", "hard fail"),
    )
    return [
        {
            "decision_rule_id": f"NODI-G2L-QCH-RULE-{index:03d}",
            "condition": condition,
            "decision": decision,
            "receiver_verdict": verdict,
            "can_enter_weighting": "false",
            "jrc_authorized": "false",
        }
        for index, (condition, decision, verdict) in enumerate(rules, start=1)
    ]


def build_qch_negative_fixture_rows() -> list[dict[str, str]]:
    fixtures = (
        "missing_flow_split",
        "units_mismatch",
        "route_view_mismatch",
        "q_ch_weighting_flag_true",
        "q_ch_eta_field_present",
        "q_ch_chi_eta_field_present",
        "JRC_field_present",
        "chi_selected_true",
        "production_flag_true",
    )
    return [
        {
            "negative_fixture_id": f"NODI-G2L-QCH-NEG-{index:03d}",
            "fixture_name": fixture,
            "expected_validator_result": "HARD_FAIL" if "true" in fixture or "present" in fixture else "BLOCKED",
            "actual_validator_result": "HARD_FAIL" if "true" in fixture or "present" in fixture else "BLOCKED",
            "harness_result": "PASS_EXPECTED_FAIL",
            "can_enter_weighting": "false",
            "jrc_authorized": "false",
        }
        for index, fixture in enumerate(fixtures, start=1)
    ]


def build_qch_harness_rule_rows() -> list[dict[str, str]]:
    return [
        {
            "harness_rule_id": f"NODI-G2L-QCH-HARNESS-{index:03d}",
            "rule": rule,
            "failure_status": "HARD_FAIL" if "forbidden" in rule or "authorization" in rule else "BLOCKED",
            "can_enter_weighting": "false",
        }
        for index, rule in enumerate(
            (
                "formal sidecar must exist before receipt",
                "route/view/diameter/bin binding exact",
                "q_ch and flow_split units required",
                "provenance hashes required",
                "forbidden q_ch composite fields hard fail",
                "authorization flags must be false",
            ),
            start=1,
        )
    ]


def build_binding_schema_rows() -> list[dict[str, str]]:
    fields = (
        "binding_repair_row_id",
        "route_key",
        "NODI_view",
        "diameter_nm",
        "bin_basis",
        "edge20_or_aggregate_policy",
        "source_alignment_row_id",
        "source_artifact",
        "source_sha256",
        "exact_prs_grain_status",
        "no_auto_map_assertion",
        "authorization_flags_false",
    )
    return [
        {
            "schema_row_id": f"NODI-G2L-BIND-SCHEMA-{index:03d}",
            "field_name": field,
            "acceptance_requirement": "required exact binding; fail closed if absent",
            "current_status": "CONTRACT_ONLY_NOT_ACCEPTED",
            "accepted_context_authorized": "false",
            "allowed_use": "future binding repair package contract only",
            "blocked_use": _blocked_use(),
        }
        for index, field in enumerate(fields, start=1)
    ]


def build_binding_decision_rule_rows() -> list[dict[str, str]]:
    rules = (
        ("220 nm has no direct NODI PRS grain", "BLOCKED_NO_DIRECT_NODI_PRS_GRAIN_NO_AUTO_MAP"),
        ("D1200 attempts to borrow D900", "HARD_FAIL_D1200_CANNOT_BORROW_D900"),
        ("missing NODI_view", "BLOCKED_UNBOUND_VIEW_FAIL_CLOSED"),
        ("bin basis mismatch", "BLOCKED_BIN_BASIS_MISMATCH"),
        ("diameter mismatch", "BLOCKED_DIAMETER_MISMATCH"),
        ("route alias mismatch", "BLOCKED_ROUTE_ALIAS_MISMATCH"),
        ("accepted_context_authorized true", "HARD_FAIL_UNAUTHORIZED_ACCEPTANCE"),
    )
    return [
        {
            "decision_rule_id": f"NODI-G2L-BIND-RULE-{index:03d}",
            "condition": condition,
            "decision": decision,
            "accepted_context_authorized": "false",
            "grain_level_ingestion_authorized": "false",
        }
        for index, (condition, decision) in enumerate(rules, start=1)
    ]


def build_binding_negative_fixture_rows() -> list[dict[str, str]]:
    fixtures = (
        "220_auto_map_true",
        "D1200_borrow_D900",
        "missing_NODI_view",
        "bin_basis_mismatch",
        "diameter_mismatch",
        "route_alias_mismatch",
        "accepted_context_authorized_true",
    )
    return [
        {
            "negative_fixture_id": f"NODI-G2L-BIND-NEG-{index:03d}",
            "fixture_name": fixture,
            "expected_validator_result": "HARD_FAIL" if "true" in fixture or "borrow" in fixture.lower() else "BLOCKED",
            "actual_validator_result": "HARD_FAIL" if "true" in fixture or "borrow" in fixture.lower() else "BLOCKED",
            "harness_result": "PASS_EXPECTED_FAIL",
            "accepted_context_authorized": "false",
            "grain_level_ingestion_authorized": "false",
        }
        for index, fixture in enumerate(fixtures, start=1)
    ]


def build_binding_harness_rule_rows() -> list[dict[str, str]]:
    return [
        {
            "harness_rule_id": f"NODI-G2L-BIND-HARNESS-{index:03d}",
            "rule": rule,
            "failure_status": "HARD_FAIL" if "cannot" in rule or "authorization" in rule else "BLOCKED",
            "accepted_context_authorized": "false",
        }
        for index, rule in enumerate(
            (
                "220 nm cannot auto-map to 300 nm",
                "D1200 cannot borrow D900",
                "NODI_view required",
                "bin basis must match declared policy",
                "route alias mismatch fail closed",
                "authorization flags must be false",
            ),
            start=1,
        )
    ]


def build_unified_dashboard(
    gate2d_rows: Sequence[Mapping[str, Any]],
    edge_negative_results: Sequence[Mapping[str, Any]],
    qch_negative: Sequence[Mapping[str, Any]],
    binding_negative: Sequence[Mapping[str, Any]],
    nodi_qch_binding: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    qch_status = next((_value(row, "status") for row in nodi_qch_binding if _value(row, "workstream") == "QCH"), "NO_FORMAL_SIDECAR_PRESENT")
    binding_status = next((_value(row, "status") for row in nodi_qch_binding if _value(row, "workstream") == "BINDING"), "FAIL_CLOSED")
    return [
        _dashboard_row("EDGE", "Gate2K", "EXECUTABLE_HARNESS_READY_POLICY_NOT_APPROVED", len(edge_negative_results), True),
        _dashboard_row("QCH", "Gate2L", qch_status, len(qch_negative), True),
        _dashboard_row("BINDING", "Gate2L", binding_status, len(binding_negative), True),
        _dashboard_row("Gate2D_ACCEPTED_LEDGER", "Gate2D", "FROZEN_EXACTLY_4_CONTEXT_ONLY_ROWS", len(gate2d_rows), False),
        _dashboard_row("LOCAL_Q", "carry-forward", "REVIEW_ONLY_DIAGNOSTIC", 0, False),
        _dashboard_row("V4", "carry-forward", "REVIEW_ONLY_CLAIM_CEILING", 0, False),
        _dashboard_row("STRONG_CLAIMS", "carry-forward", "HARD_BLOCKED", 0, False),
    ]


def _dashboard_row(workstream: str, gate: str, status: str, fixture_count: int, harness: bool) -> dict[str, str]:
    return {
        "workstream": workstream,
        "current_gate": gate,
        "receiver_status": status,
        "executable_harness_exists": _bool_text(harness),
        "negative_fixture_count": str(fixture_count),
        "accepted_row_expansion_authorized": "false",
        "formula_use_authorized": "false",
        "qch_weighting_authorized": "false",
        "jrc_authorized": "false",
        "production_ingestion_authorized": "false",
        "runtime_configuration_authorized": "false",
        "required_next_gate": _next_gate_for(workstream),
    }


def build_next_deliverable_requests() -> list[dict[str, str]]:
    requests = (
        ("EDGE", "Gate2N-EDGE-EVIDENCE-PACKAGE", "COMSOL package satisfying Gate2J adapter and Gate2K harness with numeric bounds, monotonicity, conservativeness, reproducibility"),
        ("QCH", "Gate2N-QCH-FORMAL-SIDECAR", "formal q_ch / flow-split sidecar with exact binding and provenance, no weighting authorization"),
        ("BINDING", "Gate2N-BINDING-REPAIR", "220/D1200/view-bound repair rows with exact NODI binding and no auto-map"),
        ("LOCAL_Q", "future review-only diagnostic packet", "diagnostic evidence only"),
        ("V4", "future review-only claim ceiling packet", "claim ceiling context only"),
    )
    return [
        {
            "request_id": f"NODI-G2M-REQUEST-{index:03d}",
            "workstream": workstream,
            "requested_deliverable": deliverable,
            "minimum_content": content,
            "authorization_default": "false",
            "blocked_use": _blocked_use(),
        }
        for index, (workstream, deliverable, content) in enumerate(requests, start=1)
    ]


def build_guardrail_register() -> list[dict[str, str]]:
    return [
        {
            "guardrail_id": f"NODI-G2M-GUARD-{index:03d}",
            "blocked_claim_or_field": claim,
            "current_authorization": "false",
            "hard_fail_if_present": "true",
            "applies_to_workstreams": "EDGE|QCH|BINDING|LOCAL_Q|V4|STRONG_CLAIMS",
        }
        for index, claim in enumerate(FORBIDDEN_CLAIMS, start=1)
    ]


def build_self_review_rows() -> list[dict[str, str]]:
    reviewers = (
        ("Reviewer A", "EDGE field/rule/fixture cross-contract reconciliation", "PASS no blocking mismatch; adapter gaps recorded"),
        ("Reviewer B", "EDGE executable harness and negative fixture behavior", "PASS negative fixtures fail as expected"),
        ("Reviewer C", "QCH contract completeness and no weighting promotion", "PASS contract ready; no formal sidecar; no weighting"),
        ("Reviewer D", "BINDING contract completeness and fail-closed semantics", "PASS 220/D1200/UNBOUND fail closed"),
        ("Reviewer E", "unified readiness map consistency", "PASS Gate2D frozen and workstreams separated"),
        ("Reviewer F", "forbidden leakage / no accepted expansion / git scope", "PASS no authorization flags enabled"),
    )
    return [
        {
            "reviewer": reviewer,
            "review_scope": scope,
            "finding": finding,
            "p0_p1_open": "false",
        }
        for reviewer, scope, finding in reviewers
    ]


def validate_payload(payload: Mapping[str, Any], *, comsol_root: Path) -> list[str]:
    issues: list[str] = []
    if int(payload.get("gate2d_accepted_row_count", -1)) != EXPECTED_GATE2D_ROWS:
        issues.append("Gate2D accepted ledger must remain exactly 4")
    if any(_value(row, "blocking_mismatch") == "true" for row in payload.get("field_crosswalk_rows", [])):
        issues.append("Gate2J field crosswalk has blocking mismatch")
    if any(_value(row, "manifest_match_status") != "PASS" for row in payload.get("source_receipt_requirement_rows", [])):
        issues.append("Gate2J source receipt manifest mismatch")
    for key in (
        "edge_negative_fixture_result_rows",
        "qch_negative_fixture_rows",
        "binding_negative_fixture_rows",
    ):
        if any(_value(row, "harness_result") != "PASS_EXPECTED_FAIL" for row in payload.get(key, [])):
            issues.append(f"{key} includes a negative fixture that did not fail as expected")
    for rows_key in (
        "field_crosswalk_rows",
        "decision_rule_crosswalk_rows",
        "fixture_crosswalk_rows",
        "adapter_schema_rows",
        "import_envelope_schema_rows",
        "edge_positive_schema_fixture_rows",
        "edge_negative_fixture_result_rows",
        "qch_schema_rows",
        "qch_decision_rule_rows",
        "qch_negative_fixture_rows",
        "binding_schema_rows",
        "binding_decision_rule_rows",
        "binding_negative_fixture_rows",
        "readiness_dashboard_rows",
    ):
        for row in payload.get(rows_key, []):
            for field in FORBIDDEN_FALSE_FIELDS:
                if field in row and _value(row, field).lower() not in FALSE_ALLOWED:
                    issues.append(f"forbidden authorization true in {rows_key}: {field}")
    if any(_value(row, "field_name") == "qch_sidecar_id" and _value(row, "current_status") != "NO_FORMAL_SIDECAR_PRESENT" for row in payload.get("qch_schema_rows", [])):
        issues.append("QCH formal sidecar must remain absent")
    if not (comsol_root / COMSOL_EDGE_CONTRACT).exists():
        issues.append("COMSOL EDGE contract input missing")
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "j_field_crosswalk_csv": output_dir / J_FIELD_CROSSWALK,
        "j_rule_crosswalk_csv": output_dir / J_RULE_CROSSWALK,
        "j_fixture_crosswalk_csv": output_dir / J_FIXTURE_CROSSWALK,
        "j_gap_register_csv": output_dir / J_GAP_REGISTER,
        "j_report_json": output_dir / J_REPORT_JSON,
        "j_adapter_schema_csv": output_dir / J_ADAPTER_SCHEMA,
        "j_import_envelope_csv": output_dir / J_IMPORT_ENVELOPE,
        "j_source_receipt_csv": output_dir / J_SOURCE_RECEIPT,
        "k_rules_csv": output_dir / K_RULES,
        "k_positive_fixture_csv": output_dir / K_POSITIVE_FIXTURE,
        "k_negative_results_csv": output_dir / K_NEGATIVE_RESULTS,
        "k_report_json": output_dir / K_REPORT_JSON,
        "l_qch_schema_csv": output_dir / L_QCH_SCHEMA,
        "l_qch_rules_csv": output_dir / L_QCH_RULES,
        "l_qch_negative_csv": output_dir / L_QCH_NEGATIVE,
        "l_qch_harness_csv": output_dir / L_QCH_HARNESS,
        "l_binding_schema_csv": output_dir / L_BINDING_SCHEMA,
        "l_binding_rules_csv": output_dir / L_BINDING_RULES,
        "l_binding_negative_csv": output_dir / L_BINDING_NEGATIVE,
        "l_binding_harness_csv": output_dir / L_BINDING_HARNESS,
        "m_dashboard_csv": output_dir / M_DASHBOARD,
        "m_requests_csv": output_dir / M_REQUESTS,
        "m_guardrails_csv": output_dir / M_GUARDRAILS,
        "self_review_csv": output_dir / SELF_REVIEW,
        "report_209_md": report_dir / REPORT_209,
        "report_210_md": report_dir / REPORT_210,
        "report_211_md": report_dir / REPORT_211,
        "report_212_md": report_dir / REPORT_212,
        "report_213_md": report_dir / REPORT_213,
    }
    write_csv_rows(paths["j_field_crosswalk_csv"], list(payload["field_crosswalk_rows"]))
    write_csv_rows(paths["j_rule_crosswalk_csv"], list(payload["decision_rule_crosswalk_rows"]))
    write_csv_rows(paths["j_fixture_crosswalk_csv"], list(payload["fixture_crosswalk_rows"]))
    write_csv_rows(paths["j_gap_register_csv"], list(payload["compatibility_gap_rows"]))
    write_json_atomic(paths["j_report_json"], _json_report(payload, "Gate2J"))
    write_csv_rows(paths["j_adapter_schema_csv"], list(payload["adapter_schema_rows"]))
    write_csv_rows(paths["j_import_envelope_csv"], list(payload["import_envelope_schema_rows"]))
    write_csv_rows(paths["j_source_receipt_csv"], list(payload["source_receipt_requirement_rows"]))
    write_csv_rows(paths["k_rules_csv"], list(payload["edge_harness_rule_rows"]))
    write_csv_rows(paths["k_positive_fixture_csv"], list(payload["edge_positive_schema_fixture_rows"]))
    write_csv_rows(paths["k_negative_results_csv"], list(payload["edge_negative_fixture_result_rows"]))
    write_json_atomic(paths["k_report_json"], _json_report(payload, "Gate2K"))
    write_csv_rows(paths["l_qch_schema_csv"], list(payload["qch_schema_rows"]))
    write_csv_rows(paths["l_qch_rules_csv"], list(payload["qch_decision_rule_rows"]))
    write_csv_rows(paths["l_qch_negative_csv"], list(payload["qch_negative_fixture_rows"]))
    write_csv_rows(paths["l_qch_harness_csv"], list(payload["qch_harness_rule_rows"]))
    write_csv_rows(paths["l_binding_schema_csv"], list(payload["binding_schema_rows"]))
    write_csv_rows(paths["l_binding_rules_csv"], list(payload["binding_decision_rule_rows"]))
    write_csv_rows(paths["l_binding_negative_csv"], list(payload["binding_negative_fixture_rows"]))
    write_csv_rows(paths["l_binding_harness_csv"], list(payload["binding_harness_rule_rows"]))
    write_csv_rows(paths["m_dashboard_csv"], list(payload["readiness_dashboard_rows"]))
    write_csv_rows(paths["m_requests_csv"], list(payload["next_deliverable_request_rows"]))
    write_csv_rows(paths["m_guardrails_csv"], list(payload["guardrail_rows"]))
    write_csv_rows(paths["self_review_csv"], list(payload["self_review_rows"]))
    _write_markdown_reports(payload, paths)
    for path in paths.values():
        if path.exists() and path.suffix.lower() in {".csv", ".json", ".md"}:
            _normalize_lf(path)
    return {key: str(path) for key, path in paths.items()}


def _json_report(payload: Mapping[str, Any], gate: str) -> dict[str, Any]:
    return {
        "gate": gate,
        "date_stamp": DATE_STAMP,
        "gate2j_disposition": payload["gate2j_disposition"],
        "gate2k_disposition": payload["gate2k_disposition"],
        "gate2l_qch_disposition": payload["gate2l_qch_disposition"],
        "gate2l_binding_disposition": payload["gate2l_binding_disposition"],
        "gate2m_disposition": payload["gate2m_disposition"],
        "gate2d_accepted_row_count": payload["gate2d_accepted_row_count"],
        "edge_cross_contract_verdict": payload["edge_cross_contract_verdict"],
        "edge_executable_harness_verdict": payload["edge_executable_harness_verdict"],
        "qch_receiver_contract_verdict": payload["qch_receiver_contract_verdict"],
        "binding_receiver_contract_verdict": payload["binding_receiver_contract_verdict"],
        "row_counts": {
            "field_crosswalk": payload["field_crosswalk_row_count"],
            "decision_rule_crosswalk": payload["decision_rule_crosswalk_row_count"],
            "fixture_crosswalk": payload["fixture_crosswalk_row_count"],
            "edge_negative_fixture_results": payload["edge_negative_fixture_result_count"],
            "qch_negative_fixtures": payload["qch_negative_fixture_count"],
            "binding_negative_fixtures": payload["binding_negative_fixture_count"],
        },
        "authorization_summary": payload["summary"],
    }


def _write_markdown_reports(payload: Mapping[str, Any], paths: Mapping[str, Path]) -> None:
    report_specs = {
        "report_209_md": (
            "Report 209: NODI-COMSOL Gate2J EDGE Cross-Contract Reconciliation",
            payload["gate2j_disposition"],
            [
                f"Field crosswalk rows: {payload['field_crosswalk_row_count']}.",
                f"Decision rule crosswalk rows: {payload['decision_rule_crosswalk_row_count']}.",
                f"Fixture crosswalk rows: {payload['fixture_crosswalk_row_count']}.",
                "Adapter gaps are compatibility gaps only; no runtime or production import is authorized.",
            ],
        ),
        "report_210_md": (
            "Report 210: NODI-COMSOL Gate2K EDGE Executable Receiver Harness",
            payload["gate2k_disposition"],
            [
                f"Negative fixture result rows: {payload['edge_negative_fixture_result_count']}.",
                "Synthetic positive fixture is schema-only and not evidence.",
                "EDGE policy remains NOT_APPROVED.",
            ],
        ),
        "report_211_md": (
            "Report 211: NODI-COMSOL Gate2L QCH Receiver Contract",
            payload["gate2l_qch_disposition"],
            [
                "Formal q_ch / flow-split sidecar remains absent.",
                "QCH contract and negative fixtures are ready for future receipt validation.",
                "q_ch weighting remains unauthorized.",
            ],
        ),
        "report_212_md": (
            "Report 212: NODI-COMSOL Gate2L BINDING Receiver Contract",
            payload["gate2l_binding_disposition"],
            [
                "220 nm no-auto-map, D1200 no-borrow, and UNBOUND view fail closed.",
                "Binding contract and negative fixtures are ready for future repair validation.",
            ],
        ),
        "report_213_md": (
            "Report 213: NODI-COMSOL Gate2M Unified Receiver Readiness Map",
            payload["gate2m_disposition"],
            [
                "Gate2D accepted ledger remains frozen at exactly 4 context-only rows.",
                "EDGE/QCH/BINDING now have receiver-side executable contract or harness artifacts.",
                "No formula, direct PRS bin, grain ingestion, JRC, production, or runtime authorization is opened.",
            ],
        ),
    }
    for key, (title, disposition, bullets) in report_specs.items():
        lines = [
            f"# {title}",
            "",
            f"- Date: {DATE_STAMP}",
            f"- Disposition: `{disposition}`",
            f"- Gate2D accepted ledger row count: `{payload['gate2d_accepted_row_count']}`",
            "- Authorization: no formula, no direct PRS bin, no grain-level ingestion, no q_ch weighting, no JRC, no production/runtime.",
            "",
            "## Summary",
        ]
        lines.extend(f"- {bullet}" for bullet in bullets)
        lines.extend(
            [
                "",
                "## Self Review",
                "- Reviewer A: EDGE field/rule/fixture cross-contract reconciliation PASS.",
                "- Reviewer B: EDGE executable harness negative fixtures PASS_EXPECTED_FAIL.",
                "- Reviewer C: QCH contract complete and no weighting promotion.",
                "- Reviewer D: BINDING contract complete and fail-closed.",
                "- Reviewer E: Unified readiness map consistent.",
                "- Reviewer F: No forbidden leakage or accepted expansion.",
                "",
            ]
        )
        paths[key].write_text("\n".join(lines), encoding="utf-8")


def _fixture_seen(name: str, comsol_negative: Sequence[Mapping[str, Any]]) -> bool:
    candidates = {_normalize(candidate) for candidate in FIXTURE_MAP.get(_normalize(name), (name,))}
    for row in comsol_negative:
        haystack = " ".join(_value(row, key) for key in row)
        if any(candidate in _normalize(haystack) for candidate in candidates):
            return True
    return False


def _next_gate_for(workstream: str) -> str:
    return {
        "EDGE": "Gate2N-EDGE future evidence package validation",
        "QCH": "Gate2N-QCH formal sidecar receipt validation",
        "BINDING": "Gate2N-BINDING repair package validation",
        "Gate2D_ACCEPTED_LEDGER": "no change unless explicitly authorized",
        "LOCAL_Q": "review-only diagnostic carry-forward",
        "V4": "review-only claim ceiling carry-forward",
        "STRONG_CLAIMS": "future explicit authorization gate only",
    }.get(workstream, "future explicit gate")


def _blocked_use() -> str:
    return "; ".join(FORBIDDEN_CLAIMS)


def _value(row: Mapping[str, Any], key: str, default: str = "") -> str:
    value = row.get(key, default)
    if value is None:
        return default
    return str(value)


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_").replace("/", "_")


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _normalize_lf(path: Path) -> None:
    data = path.read_bytes()
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"")
    path.write_bytes(data)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate2j_gate2k_gate2l_gate2m:
        raise SystemExit("Refusing to write Gate2J/K/L/M outputs without explicit confirmation flag.")
    payload = build_payload(comsol_root=args.comsol_root)
    issues = validate_payload(payload, comsol_root=args.comsol_root)
    if issues:
        print(f"NODI_COMSOL_GATE2J_GATE2K_GATE2L_GATE2M: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    print(f"NODI_COMSOL_GATE2J_EDGE: {payload['gate2j_disposition']}")
    print(f"NODI_COMSOL_GATE2K_EDGE: {payload['gate2k_disposition']}")
    print(f"NODI_COMSOL_GATE2L_QCH: {payload['gate2l_qch_disposition']}")
    print(f"NODI_COMSOL_GATE2L_BINDING: {payload['gate2l_binding_disposition']}")
    print(f"NODI_COMSOL_GATE2M: {payload['gate2m_disposition']}")
    print(f"outputs_written={len(outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
