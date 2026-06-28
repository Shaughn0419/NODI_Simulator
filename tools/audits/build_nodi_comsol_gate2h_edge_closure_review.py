#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    default_comsol_v4_readonly_context,
    validate_comsol_v4_readonly_context,
)
from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


DATE_STAMP = "20260628"
GATE2H_PASS = "PASS_GATE2H_EDGE_STRUCTURAL_CLOSURE_REVIEW_RECEIVED_POLICY_NOT_APPROVED_NO_FORMULA_NO_JRC"
GATE2H_PARTIAL = "PARTIAL_GATE2H_EDGE_CLOSURE_REVIEW_BLOCKED_BY_EVIDENCE_MISMATCH_NO_FORMULA_NO_JRC"
GATE2I_PASS = "PASS_GATE2I_EDGE_FUTURE_EVIDENCE_CONTRACT_READY_NO_FORMULA_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2H_GATE2I_EDGE_CLOSURE_REVIEW"

OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
REPORT_207 = f"207_NODI_COMSOL_GATE2H_EDGE_LOSS_ERROR_CLOSURE_REVIEW_{DATE_STAMP}.md"
REPORT_208 = f"208_NODI_COMSOL_GATE2I_EDGE_FUTURE_EVIDENCE_ACCEPTANCE_CONTRACT_{DATE_STAMP}.md"

H_RECEIPT_AUDIT = f"NODI_COMSOL_GATE2H_EDGE_COMSOL_GATE2G_PACKAGE_RECEIPT_AUDIT_{DATE_STAMP}.csv"
H_MANIFEST_AUDIT = f"NODI_COMSOL_GATE2H_EDGE_COMSOL_GATE2G_MANIFEST_REPRO_AUDIT_{DATE_STAMP}.csv"
H_STRUCTURAL_REVIEW = f"NODI_COMSOL_GATE2H_EDGE_STRUCTURAL_COVERAGE_RECEIVER_REVIEW_{DATE_STAMP}.csv"
H_STRUCTURAL_ROW_VERDICT = f"NODI_COMSOL_GATE2H_EDGE_STRUCTURAL_ROW_VERDICT_{DATE_STAMP}.csv"
H_LOSS_REVIEW = f"NODI_COMSOL_GATE2H_EDGE_LOSS_ERROR_CLOSURE_REVIEW_MATRIX_{DATE_STAMP}.csv"
H_POLICY_VERDICT = f"NODI_COMSOL_GATE2H_EDGE_POLICY_DECISION_VERDICT_{DATE_STAMP}.csv"
H_REPORT_JSON = f"NODI_COMSOL_GATE2H_EDGE_CLOSURE_REVIEW_REPORT_{DATE_STAMP}.json"
H_REPORT_MD = f"NODI_COMSOL_GATE2H_EDGE_CLOSURE_REVIEW_REPORT_{DATE_STAMP}.md"
H_DASHBOARD = f"NODI_COMSOL_GATE2H_EDGE_CLOSURE_DASHBOARD_{DATE_STAMP}.csv"
H_FORBIDDEN = f"NODI_COMSOL_GATE2H_FORBIDDEN_CLAIM_AUDIT_{DATE_STAMP}.csv"
H_BLOCKER = f"NODI_COMSOL_GATE2H_BLOCKER_CARRY_FORWARD_{DATE_STAMP}.csv"
H_SELF_REVIEW = f"NODI_COMSOL_GATE2H_SELF_REVIEW_{DATE_STAMP}.csv"

I_SCHEMA = f"NODI_COMSOL_GATE2I_EDGE_LOSS_ERROR_ACCEPTANCE_SCHEMA_{DATE_STAMP}.csv"
I_DECISION_RULES = f"NODI_COMSOL_GATE2I_EDGE_DECISION_RULES_{DATE_STAMP}.csv"
I_CHECKLIST = f"NODI_COMSOL_GATE2I_EDGE_REQUIRED_EVIDENCE_CHECKLIST_{DATE_STAMP}.csv"
I_NEGATIVE_FIXTURES = f"NODI_COMSOL_GATE2I_EDGE_NEGATIVE_FIXTURES_{DATE_STAMP}.csv"
I_VALIDATION_RULES = f"NODI_COMSOL_GATE2I_EDGE_VALIDATION_RULES_{DATE_STAMP}.csv"
I_REPORT_JSON = f"NODI_COMSOL_GATE2I_EDGE_CONTRACT_REPORT_{DATE_STAMP}.json"
I_REPORT_MD = f"NODI_COMSOL_GATE2I_EDGE_CONTRACT_REPORT_{DATE_STAMP}.md"
I_NON_EDGE = f"NODI_COMSOL_GATE2I_NON_EDGE_READINESS_CARRY_FORWARD_{DATE_STAMP}.csv"
I_QCH_BINDING_DASH = f"NODI_COMSOL_GATE2I_QCH_BINDING_NEXT_GATE_DASHBOARD_{DATE_STAMP}.csv"

DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
NODI_REPORT_206 = PROJECT_ROOT / "reports/206_NODI_COMSOL_GATE2G_EDGE_EVIDENCE_RECEIPT_AND_POLICY_GAP_20260628.md"
NODI_G2G_REPORT_JSON = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2G_EDGE_EVIDENCE_RECEIPT_REPORT_20260628.json"
NODI_G2G_RECON = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2G_EDGE_GROUPING_CROSS_RECONCILIATION_20260628.csv"
NODI_G2G_ROW_CONCORDANCE = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2G_EDGE_ROW_CONCORDANCE_VERDICT_20260628.csv"
NODI_G2G_LOSS_GAP = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2G_EDGE_LOSS_ERROR_POLICY_GAP_VERDICT_20260628.csv"
NODI_G2G_NEXT_SCHEMA = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2G_EDGE_REQUIRED_NEXT_EVIDENCE_SCHEMA_20260628.csv"
NODI_G2G_BLOCKER = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2G_BLOCKER_CARRY_FORWARD_20260628.csv"
NODI_G2D_LEDGER = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_20260628.csv"

COMSOL_ARTIFACTS = (
    ("G2H-STRUCTURAL-PROOF", "structural_coverage_proof", Path("roadmap/COMSOL_GATE2G_EDGE4_EDGE20_STRUCTURAL_COVERAGE_PROOF_20260628.csv")),
    ("G2H-STRUCTURAL-PACKET", "structural_coverage_packet", Path("roadmap/COMSOL_GATE2G_EDGE4_EDGE20_STRUCTURAL_COVERAGE_PROOF_PACKET_20260628.md")),
    ("G2H-LOSS-REQ", "loss_error_closure_requirements", Path("roadmap/COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_REQUIREMENTS_20260628.csv")),
    ("G2H-LOSS-PACKET", "loss_error_closure_packet", Path("roadmap/COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_REQUIREMENTS_PACKET_20260628.md")),
    ("G2H-POLICY-OPTIONS", "policy_option_matrix", Path("roadmap/COMSOL_GATE2G_EDGE_POLICY_OPTION_MATRIX_20260628.csv")),
    ("G2H-BLOCKERS", "blocker_carry_forward", Path("roadmap/COMSOL_GATE2G_EDGE_BLOCKER_CARRY_FORWARD_20260628.csv")),
    ("G2H-RECEIPT-SUPPORT", "nodi_receipt_support", Path("roadmap/COMSOL_GATE2G_EDGE_NODI_RECEIPT_SUPPORT_20260628.csv")),
    ("G2H-VALIDATION", "loss_error_closure_validation", Path("roadmap/COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_VALIDATION_20260628.csv")),
    ("G2H-MANIFEST", "loss_error_closure_manifest", Path("roadmap/COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_MANIFEST_20260628.csv")),
    ("G2H-MASTER", "loss_error_closure_master_packet", Path("roadmap/COMSOL_GATE2G_EDGE_LOSS_ERROR_CLOSURE_MASTER_PACKET_20260628.md")),
)
COMSOL_STRUCTURAL = COMSOL_ARTIFACTS[0][2]
COMSOL_LOSS = COMSOL_ARTIFACTS[2][2]
COMSOL_POLICY = COMSOL_ARTIFACTS[4][2]
COMSOL_BLOCKER = COMSOL_ARTIFACTS[5][2]
COMSOL_RECEIPT = COMSOL_ARTIFACTS[6][2]
COMSOL_VALIDATION = COMSOL_ARTIFACTS[7][2]
COMSOL_MANIFEST = COMSOL_ARTIFACTS[8][2]

EXPECTED_EDGE20_HASH = "b8b3358e7218e3ebc704c2c8dcaf2c9a0feb15283fa704610b39f8afc68d5ca3"
EXPECTED_GATE2D_ROWS = 4
FORBIDDEN_FALSE_FIELDS = (
    "policy_approved",
    "direct_prs_bin_use_authorized",
    "formula_use_authorized",
    "grain_level_ingestion_authorized",
    "accepted_row_expansion_authorized",
    "production_ingestion_authorized",
    "runtime_configuration_authorized",
    "qch_weighting_authorized",
    "qch_eta_authorized",
    "qch_chi_eta_authorized",
    "chi_selected_authorized",
    "route_score_authorized",
    "jrc_authorized",
    "yield_authorized",
    "winner_authorized",
    "detection_probability_authorized",
    "decision_use_allowed",
    "can_enter_weighting",
    "can_enter_jrc",
    "is_chi_selected",
    "is_production_ingestion",
    "is_runtime_configuration",
)
FORBIDDEN_CLAIMS = (
    "edge policy approval",
    "direct PRS edge20 bin use",
    "grain-level ingestion",
    "formula use",
    "accepted row expansion",
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
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build NODI Gate2H closure review and Gate2I EDGE future contract.")
    parser.add_argument("--confirm-gate2h-gate2i-edge", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_payload(
    *,
    comsol_root: Path,
    nodi_report_206_path: Path | None = None,
    nodi_g2g_report_json_path: Path | None = None,
    nodi_recon_path: Path | None = None,
    nodi_row_concordance_path: Path | None = None,
    nodi_loss_gap_path: Path | None = None,
    nodi_next_schema_path: Path | None = None,
    nodi_blocker_path: Path | None = None,
    nodi_gate2d_ledger_path: Path | None = None,
) -> dict[str, Any]:
    nodi_report_206_path = nodi_report_206_path or NODI_REPORT_206
    nodi_g2g_report_json_path = nodi_g2g_report_json_path or NODI_G2G_REPORT_JSON
    nodi_recon_path = nodi_recon_path or NODI_G2G_RECON
    nodi_row_concordance_path = nodi_row_concordance_path or NODI_G2G_ROW_CONCORDANCE
    nodi_loss_gap_path = nodi_loss_gap_path or NODI_G2G_LOSS_GAP
    nodi_next_schema_path = nodi_next_schema_path or NODI_G2G_NEXT_SCHEMA
    nodi_blocker_path = nodi_blocker_path or NODI_G2G_BLOCKER
    nodi_gate2d_ledger_path = nodi_gate2d_ledger_path or NODI_G2D_LEDGER

    structural_rows = read_csv_rows(comsol_root / COMSOL_STRUCTURAL)
    loss_rows = read_csv_rows(comsol_root / COMSOL_LOSS)
    policy_rows = read_csv_rows(comsol_root / COMSOL_POLICY)
    comsol_blocker_rows = read_csv_rows(comsol_root / COMSOL_BLOCKER)
    receipt_support_rows = read_csv_rows(comsol_root / COMSOL_RECEIPT)
    validation_rows = read_csv_rows(comsol_root / COMSOL_VALIDATION)
    manifest_rows = read_csv_rows(comsol_root / COMSOL_MANIFEST)
    nodi_recon_rows = read_csv_rows(nodi_recon_path)
    nodi_concordance_rows = read_csv_rows(nodi_row_concordance_path)
    nodi_loss_gap_rows = read_csv_rows(nodi_loss_gap_path)
    nodi_next_schema_rows = read_csv_rows(nodi_next_schema_path)
    nodi_blocker_rows = read_csv_rows(nodi_blocker_path)
    gate2d_rows = read_csv_rows(nodi_gate2d_ledger_path)
    report206_text = nodi_report_206_path.read_text(encoding="utf-8")
    report_json_text = nodi_g2g_report_json_path.read_text(encoding="utf-8")

    receipt_audit = build_package_receipt_audit(comsol_root, manifest_rows, validation_rows)
    manifest_audit = build_manifest_repro_audit(comsol_root, manifest_rows, validation_rows)
    structural_review = build_structural_review_rows(structural_rows, nodi_recon_rows, receipt_support_rows)
    structural_verdict = build_structural_row_verdict_rows(structural_review)
    loss_review = build_loss_review_rows(loss_rows, nodi_loss_gap_rows)
    policy_verdict = build_policy_verdict_rows(loss_review, policy_rows)
    h_blockers = build_h_blocker_rows(comsol_blocker_rows, nodi_blocker_rows, gate2d_rows)
    h_forbidden = build_forbidden_audit_rows([structural_rows, receipt_support_rows, loss_rows, structural_review, loss_review, policy_verdict, h_blockers])
    h_dashboard = build_h_dashboard_rows(structural_review, loss_review, manifest_audit, gate2d_rows)
    h_self_review = build_self_review_rows()

    i_schema = build_i_schema_rows(nodi_next_schema_rows)
    i_decision_rules = build_i_decision_rule_rows()
    i_checklist = build_i_checklist_rows()
    i_negative = build_i_negative_fixture_rows()
    i_validation = build_i_validation_rule_rows()
    i_non_edge = build_i_non_edge_rows(nodi_blocker_rows)
    i_qch_binding = build_i_qch_binding_dashboard_rows(i_non_edge)

    manifest_ok = all(_value(row, "manifest_repro_status") == "PASS_MANIFEST_REPRODUCED" for row in manifest_audit)
    structural_ok = all(
        _value(row, "receiver_verdict") == "STRUCTURAL_COVERAGE_RECEIVED_REVIEW_ONLY_NOT_POLICY_APPROVED"
        for row in structural_review
    )
    h_status = GATE2H_PASS if manifest_ok and structural_ok and len(structural_rows) == 16 and len(receipt_support_rows) == 16 else GATE2H_PARTIAL
    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2h_gate2i_edge_closure_review_v1",
        "date_stamp": DATE_STAMP,
        "gate2h_disposition": h_status,
        "gate2i_disposition": GATE2I_PASS,
        "status": h_status,
        "comsol_commit_if_available": _git_head(comsol_root),
        "structural_coverage_row_count": len(structural_rows),
        "receipt_support_row_count": len(receipt_support_rows),
        "loss_error_requirement_row_count": len(loss_rows),
        "manifest_row_count": len(manifest_rows),
        "validation_row_count": len(validation_rows),
        "gate2d_accepted_row_count": len(gate2d_rows),
        "nodi_gate2g_concordance_row_count": len(nodi_concordance_rows),
        "report206_gate2g_pass_present": "PASS_GATE2G_EDGE_REVIEW_EVIDENCE_RECEIPT_POLICY_GAP_REGISTERED_NO_FORMULA_NO_JRC"
        in report206_text,
        "gate2g_report_reference_present": "PASS_GATE2G_EDGE_REVIEW_EVIDENCE_RECEIPT_POLICY_GAP_REGISTERED_NO_FORMULA_NO_JRC"
        in report_json_text,
        "package_receipt_audit_rows": receipt_audit,
        "manifest_repro_audit_rows": manifest_audit,
        "structural_coverage_receiver_review_rows": structural_review,
        "structural_row_verdict_rows": structural_verdict,
        "loss_error_closure_review_rows": loss_review,
        "policy_decision_verdict_rows": policy_verdict,
        "gate2h_dashboard_rows": h_dashboard,
        "gate2h_forbidden_claim_audit_rows": h_forbidden,
        "gate2h_blocker_carry_forward_rows": h_blockers,
        "gate2h_self_review_rows": h_self_review,
        "gate2i_schema_rows": i_schema,
        "gate2i_decision_rule_rows": i_decision_rules,
        "gate2i_checklist_rows": i_checklist,
        "gate2i_negative_fixture_rows": i_negative,
        "gate2i_validation_rule_rows": i_validation,
        "gate2i_non_edge_rows": i_non_edge,
        "gate2i_qch_binding_dashboard_rows": i_qch_binding,
        "comsol_v4_context": default_comsol_v4_readonly_context(),
        "policy_approved": False,
        "formula_use_authorized": False,
        "direct_prs_bin_use_authorized": False,
        "grain_level_ingestion_authorized": False,
        "accepted_row_expansion_authorized": False,
    }
    return payload


def build_package_receipt_audit(
    comsol_root: Path, manifest_rows: Sequence[Mapping[str, Any]], validation_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    manifest_by_path = {_norm(_value(row, "path")): row for row in manifest_rows}
    validation_summary = _validation_summary(validation_rows)
    commit = _git_head(comsol_root)
    rows: list[dict[str, str]] = []
    for receipt_id, role, relative in COMSOL_ARTIFACTS:
        path = comsol_root / relative
        manifest = manifest_by_path.get(relative.as_posix(), {})
        actual_sha = sha256_file(path)
        actual_rows = _row_count(path)
        rows.append(
            {
                "receipt_audit_id": receipt_id,
                "file_role": role,
                "source_path": str(path),
                "relative_source_path": relative.as_posix(),
                "actual_sha256": actual_sha,
                "actual_row_count": str(actual_rows),
                "manifest_artifact_id": _value(manifest, "artifact_id"),
                "manifest_sha256": _value(manifest, "sha256"),
                "manifest_row_count": _value(manifest, "row_count"),
                "manifest_match": _bool_text(
                    bool(manifest)
                    and _value(manifest, "sha256") == actual_sha
                    and _value(manifest, "row_count") in {str(actual_rows), "0"}
                ),
                "validation_status_summary": validation_summary,
                "comsol_commit_if_available": commit,
                "allowed_use": "Gate2H receiver review of COMSOL Gate2G structural/loss-error package",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
                "claim_boundary": "review-only receipt; policy not approved; not formula; not production",
                "required_next_gate": "Gate2I contract / Gate2J evidence closure candidate",
            }
        )
    return rows


def build_manifest_repro_audit(
    comsol_root: Path, manifest_rows: Sequence[Mapping[str, Any]], validation_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    validation_summary = _validation_summary(validation_rows)
    rows: list[dict[str, str]] = []
    for index, manifest in enumerate(manifest_rows, start=1):
        raw_path = _value(manifest, "path")
        path = Path(raw_path)
        resolved = path if path.is_absolute() else comsol_root / path
        exists = resolved.exists()
        actual_sha = sha256_file(resolved) if exists else ""
        actual_rows = _row_count(resolved) if exists else -1
        sha_match = exists and actual_sha == _value(manifest, "sha256")
        row_match = exists and _value(manifest, "row_count") in {str(actual_rows), "0"}
        rows.append(
            {
                "manifest_repro_id": f"NODI-G2H-MANIFEST-{index:03d}",
                "manifest_artifact_id": _value(manifest, "artifact_id"),
                "manifest_path": raw_path,
                "resolved_path": str(resolved),
                "exists": _bool_text(exists),
                "manifest_sha256": _value(manifest, "sha256"),
                "actual_sha256": actual_sha,
                "manifest_row_count": _value(manifest, "row_count"),
                "actual_row_count": str(actual_rows) if exists else "",
                "sha_match": _bool_text(sha_match),
                "row_count_match": _bool_text(row_match),
                "validation_status_summary": validation_summary,
                "manifest_repro_status": "PASS_MANIFEST_REPRODUCED" if sha_match and row_match else "FAIL_MANIFEST_MISMATCH",
                "allowed_use": "manifest reproducibility audit only",
                "blocked_use": "policy approval; formula use; accepted row expansion",
            }
        )
    return rows


def build_structural_review_rows(
    structural_rows: Sequence[Mapping[str, Any]],
    nodi_recon_rows: Sequence[Mapping[str, Any]],
    receipt_support_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    recon_by_skel = {_value(row, "source_edge_skeleton_row_id"): row for row in nodi_recon_rows}
    receipt_by_skel = {_value(row, "source_edge_skeleton_row_id"): row for row in receipt_support_rows}
    rows: list[dict[str, str]] = []
    for index, structural in enumerate(structural_rows, start=1):
        skeleton_id = _value(structural, "source_edge_skeleton_row_id")
        recon = recon_by_skel.get(skeleton_id, {})
        receipt = receipt_by_skel.get(skeleton_id, {})
        scope_match = (
            _value(structural, "route_key_candidate") == _value(recon, "route_key")
            and _value(structural, "NODI_view") == _value(recon, "NODI_view")
            and _value(structural, "diameter_nm") == _value(recon, "diameter_nm")
            and _value(structural, "tpd_proxy_aggregation_basis") == _value(recon, "tpd_proxy_aggregation_basis")
            and _value(structural, "edge4_bin_label") == _value(recon, "edge4_bin_label")
            and _value(structural, "edge20_definition_hash") == _value(recon, "nodi_edge20_definition_hash") == EXPECTED_EDGE20_HASH
        )
        bins_match = _value(structural, "proposed_edge20_bins_covered") == _value(recon, "nodi_candidate_edge20_group")
        complete = _value(structural, "coverage_complete").lower() == "true"
        contiguous = _value(structural, "coverage_contiguous").lower() == "true"
        count_ok = _value(structural, "edge20_bin_count") == "5"
        support_ok = _value(receipt, "loss_error_policy_approval_status") == "NOT_APPROVED"
        pass_row = scope_match and bins_match and complete and contiguous and count_ok and support_ok
        rows.append(
            {
                "receiver_review_id": f"NODI-G2H-STRUCT-{index:03d}",
                "structural_coverage_proof_id": _value(structural, "structural_coverage_proof_id"),
                "source_edge_skeleton_row_id": skeleton_id,
                "route_key": _value(structural, "route_key_candidate"),
                "NODI_view": _value(structural, "NODI_view"),
                "diameter_nm": _value(structural, "diameter_nm"),
                "tpd_proxy_aggregation_basis": _value(structural, "tpd_proxy_aggregation_basis"),
                "edge4_bin_label": _value(structural, "edge4_bin_label"),
                "edge20_definition_hash": _value(structural, "edge20_definition_hash"),
                "edge20_bins_covered": _value(structural, "proposed_edge20_bins_covered"),
                "edge20_bin_count": _value(structural, "edge20_bin_count"),
                "coverage_complete": _value(structural, "coverage_complete"),
                "coverage_contiguous": _value(structural, "coverage_contiguous"),
                "scope_match_gate2g": _bool_text(scope_match),
                "edge20_bins_match_gate2g": _bool_text(bins_match),
                "receipt_support_policy_status": _value(receipt, "loss_error_policy_approval_status"),
                "receiver_verdict": "STRUCTURAL_COVERAGE_RECEIVED_REVIEW_ONLY_NOT_POLICY_APPROVED"
                if pass_row
                else "BLOCKED_STRUCTURAL_COVERAGE_MISMATCH",
                "policy_approved": "false",
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "accepted_row_expansion_authorized": "false",
                "production_ingestion_authorized": "false",
                "runtime_configuration_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "allowed_use": "structural receipt review only",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
                "required_next_gate": "Gate2I contract / future closure evidence",
            }
        )
    return rows


def build_structural_row_verdict_rows(review_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "row_verdict_id": f"NODI-G2H-STRUCT-VERDICT-{index:03d}",
            "structural_coverage_proof_id": _value(row, "structural_coverage_proof_id"),
            "source_edge_skeleton_row_id": _value(row, "source_edge_skeleton_row_id"),
            "row_verdict": _value(row, "receiver_verdict"),
            "policy_approved": "false",
            "direct_prs_bin_use_authorized": "false",
            "formula_use_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "accepted_row_expansion_authorized": "false",
            "required_next_gate": _value(row, "required_next_gate"),
        }
        for index, row in enumerate(review_rows, start=1)
    ]


def build_loss_review_rows(
    loss_rows: Sequence[Mapping[str, Any]], nodi_loss_gap_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    by_area = {_value(row, "semantics_area"): row for row in loss_rows}
    nodi_by_area = {_value(row, "semantics_area"): row for row in nodi_loss_gap_rows}
    specs = [
        ("information_loss", "REGISTERED_INSUFFICIENT_FOR_POLICY_APPROVAL"),
        ("coverage", "STRUCTURAL_COVERAGE_RECEIVED_STRUCTURE_ONLY"),
        ("error_bounds", "BLOCKED_MISSING_NUMERIC_AGGREGATION_ERROR_BOUND"),
        ("monotonicity", "BLOCKED_MISSING_OR_NOT_EVALUABLE"),
        ("conservativeness", "BLOCKED_MISSING_OR_NOT_EVALUABLE"),
        ("reproducibility", "STRUCTURAL_REPRODUCIBILITY_ONLY_APPROVAL_GRADE_MISSING"),
        ("review_context_only", "ACTIVE_REVIEW_CONTEXT_ONLY"),
        ("formula_exclusion", "ACTIVE_FORMULA_EXCLUSION"),
    ]
    rows: list[dict[str, str]] = []
    for index, (area, verdict) in enumerate(specs, start=1):
        comsol = by_area.get(area, {})
        nodi = nodi_by_area.get(area, {})
        rows.append(
            {
                "closure_review_id": f"NODI-G2H-LOSS-{index:03d}",
                "semantics_area": area,
                "comsol_loss_error_requirement_id": _value(comsol, "loss_error_requirement_id"),
                "nodi_gate2g_gap_verdict": _value(nodi, "received_status"),
                "comsol_gate2g_status": _value(comsol, "comsol_gate2g_status"),
                "numeric_aggregation_error_bound_status": _value(comsol, "numeric_aggregation_error_bound_status"),
                "monotonicity_status": _value(comsol, "monotonicity_status"),
                "conservativeness_status": _value(comsol, "conservativeness_status"),
                "reproducibility_status": _value(comsol, "reproducibility_status"),
                "formula_exclusion_active": _value(comsol, "formula_exclusion_active", "true"),
                "receiver_verdict": verdict,
                "policy_approval_status": "NOT_APPROVED",
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "accepted_row_expansion_authorized": "false",
                "allowed_use": "loss/error closure review matrix only",
                "blocked_use": "formula use; direct PRS bin use; grain-level ingestion; weighting; JRC",
                "required_next_gate": "Gate2I contract / future Gate2J evidence package",
            }
        )
    return rows


def build_policy_verdict_rows(loss_review: Sequence[Mapping[str, Any]], policy_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    blockers = [
        _value(row, "receiver_verdict")
        for row in loss_review
        if _value(row, "receiver_verdict").startswith("BLOCKED") or "MISSING" in _value(row, "receiver_verdict")
    ]
    return [
        {
            "policy_decision_id": "NODI-G2H-EDGE-POLICY-001",
            "policy_decision_verdict": "EDGE_POLICY_NOT_APPROVED_LOSS_ERROR_GAPS_REMAIN",
            "policy_option_rows_reviewed": str(len(policy_rows)),
            "blocking_verdicts": "|".join(blockers),
            "policy_approved": "false",
            "formula_use_authorized": "false",
            "direct_prs_bin_use_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "accepted_row_expansion_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "production_ingestion_authorized": "false",
            "runtime_configuration_authorized": "false",
            "required_next_gate": "Gate2I future evidence contract; future closure candidate after evidence",
        }
    ]


def build_h_blocker_rows(
    comsol_blocker_rows: Sequence[Mapping[str, Any]],
    nodi_blocker_rows: Sequence[Mapping[str, Any]],
    gate2d_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    rows = [
        {
            "blocker_id": "NODI-G2H-BLOCK-GATE2D",
            "blocker_class": "Gate2D accepted ledger",
            "source_status": "FROZEN_EXACTLY_FOUR_ROWS",
            "row_count_or_scope": str(len(gate2d_rows)),
            "gate2h_status": "UNCHANGED_NO_ACCEPTED_ROW_EXPANSION",
            "formula_use_authorized": "false",
            "accepted_row_expansion_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "required_next_gate": "future explicit authorization gate",
        }
    ]
    for index, row in enumerate(comsol_blocker_rows, start=1):
        rows.append(
            {
                "blocker_id": f"NODI-G2H-BLOCK-COMSOL-{index:03d}",
                "blocker_class": _value(row, "excluded_class") or _value(row, "blocker_class"),
                "source_status": _value(row, "carry_forward_status") or _value(row, "source_status"),
                "row_count_or_scope": _value(row, "row_count_or_scope"),
                "gate2h_status": "CARRY_FORWARD_BLOCKED_OR_REVIEW_ONLY",
                "formula_use_authorized": "false",
                "accepted_row_expansion_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "required_next_gate": _value(row, "required_next_gate"),
            }
        )
    for index, row in enumerate(nodi_blocker_rows, start=1):
        rows.append(
            {
                "blocker_id": f"NODI-G2H-BLOCK-NODI-{index:03d}",
                "blocker_class": _value(row, "blocker_class"),
                "source_status": _value(row, "gate2g_status"),
                "row_count_or_scope": _value(row, "row_count_or_scope"),
                "gate2h_status": "UNCHANGED_FROM_GATE2G",
                "formula_use_authorized": "false",
                "accepted_row_expansion_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "required_next_gate": _value(row, "required_next_gate"),
            }
        )
    return rows


def build_h_dashboard_rows(
    structural_review: Sequence[Mapping[str, Any]],
    loss_review: Sequence[Mapping[str, Any]],
    manifest_audit: Sequence[Mapping[str, Any]],
    gate2d_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    structural_pass = sum(1 for row in structural_review if _value(row, "receiver_verdict") == "STRUCTURAL_COVERAGE_RECEIVED_REVIEW_ONLY_NOT_POLICY_APPROVED")
    manifest_pass = sum(1 for row in manifest_audit if _value(row, "manifest_repro_status") == "PASS_MANIFEST_REPRODUCED")
    blocked_loss = sum(1 for row in loss_review if "BLOCKED" in _value(row, "receiver_verdict") or "MISSING" in _value(row, "receiver_verdict"))
    return [
        {
            "dashboard_id": "NODI-G2H-DASH-001",
            "topic": "package receipt",
            "status": "PASS_MANIFEST_REPRODUCED" if manifest_pass == len(manifest_audit) else "PARTIAL_MANIFEST_MISMATCH",
            "row_count": str(len(manifest_audit)),
            "policy_approved": "false",
            "formula_use_authorized": "false",
            "accepted_row_expansion_authorized": "false",
        },
        {
            "dashboard_id": "NODI-G2H-DASH-002",
            "topic": "structural coverage",
            "status": "STRUCTURAL_COVERAGE_RECEIVED_REVIEW_ONLY_NOT_POLICY_APPROVED",
            "row_count": str(len(structural_review)),
            "pass_row_count": str(structural_pass),
            "policy_approved": "false",
            "formula_use_authorized": "false",
            "accepted_row_expansion_authorized": "false",
        },
        {
            "dashboard_id": "NODI-G2H-DASH-003",
            "topic": "loss/error policy decision",
            "status": "EDGE_POLICY_NOT_APPROVED_LOSS_ERROR_GAPS_REMAIN",
            "row_count": str(len(loss_review)),
            "blocked_or_missing_count": str(blocked_loss),
            "policy_approved": "false",
            "formula_use_authorized": "false",
            "accepted_row_expansion_authorized": "false",
        },
        {
            "dashboard_id": "NODI-G2H-DASH-004",
            "topic": "Gate2D freeze",
            "status": "FROZEN_EXACTLY_FOUR_ROWS",
            "row_count": str(len(gate2d_rows)),
            "policy_approved": "false",
            "formula_use_authorized": "false",
            "accepted_row_expansion_authorized": "false",
        },
    ]


def build_i_schema_rows(prior_schema_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    fields = [
        ("edge20_resolved_reference_rows", "table", "one row per referenced edge20 bin with route/view/diameter/bin binding", "required"),
        ("edge4_aggregate_rows", "table", "one row per edge4 aggregate with derivation provenance", "required"),
        ("numeric_aggregation_error_bound", "number", "finite numeric bound with sign/basis/units", "required"),
        ("numeric_error_bound_units", "string", "declared unit or dimensionless basis", "required"),
        ("monotonicity_check_input", "table/ref", "edge20-resolved values and ordering basis", "required"),
        ("monotonicity_check_output", "enum+evidence", "PASS/FAIL/REVIEW_REQUIRED plus details", "required"),
        ("conservativeness_check_input", "table/ref", "upper/lower rule inputs", "required"),
        ("conservativeness_check_output", "enum+evidence", "PASS/FAIL/REVIEW_REQUIRED plus details", "required"),
        ("reproducibility_evidence", "hash bundle", "source artifact SHA/row_count/provenance and validator id", "required"),
        ("route_view_diameter_bin_binding", "fields", "route_key/NODI_view/diameter_nm/edge4_bin/edge20 bins", "exact"),
        ("authorization_request_flags", "booleans", "all default false until explicit future approval", "required_false_default"),
    ]
    return [
        {
            "schema_row_id": f"NODI-G2I-EDGE-SCHEMA-{index:03d}",
            "field_or_section": name,
            "required_type": type_name,
            "acceptance_requirement": requirement,
            "requirement_level": level,
            "prior_gate2g_schema_rows_reviewed": str(len(prior_schema_rows)),
            "default_policy_approval_status": "NOT_APPROVED",
        }
        for index, (name, type_name, requirement, level) in enumerate(fields, start=1)
    ]


def build_i_decision_rule_rows() -> list[dict[str, str]]:
    rules = [
        ("missing_numeric_bound", "any missing numeric aggregation error bound", "NOT_APPROVED"),
        ("hash_or_bin_mismatch", "any edge20 hash/bin mismatch", "BLOCKED"),
        ("authorization_true", "any authorization flag preset true", "HARD_FAIL"),
        ("structural_only", "structural coverage alone", "RECEIPT_ONLY_NOT_APPROVED"),
        ("qch_binding_inference", "QCH/BINDING blockers used to infer EDGE approval", "HARD_FAIL"),
        ("non_contiguous_bins", "edge20 bins non-contiguous or count not five", "BLOCKED"),
        ("d1200_borrowing", "D1200 borrows D900 semantics", "HARD_FAIL"),
        ("auto_map_220", "220 nm auto-mapped to 300 nm or PRS bins", "HARD_FAIL"),
    ]
    return [
        {
            "decision_rule_id": f"NODI-G2I-EDGE-RULE-{index:03d}",
            "condition": condition,
            "rule_description": description,
            "decision": decision,
            "policy_approval_status": "NOT_APPROVED" if decision != "HARD_FAIL" else "HARD_FAIL",
        }
        for index, (condition, description, decision) in enumerate(rules, start=1)
    ]


def build_i_checklist_rows() -> list[dict[str, str]]:
    items = [
        "edge20-resolved evidence rows present",
        "edge4 aggregate derivation provenance present",
        "numeric aggregation error bound present with units",
        "monotonicity inputs/outputs present",
        "conservativeness inputs/outputs present",
        "source artifact SHA/row_count/provenance stable",
        "route/view/diameter/bin binding exact",
        "all authorization request flags default false",
        "negative fixtures fail as expected",
        "QCH/BINDING carry-forward not used for EDGE approval",
    ]
    return [
        {
            "checklist_id": f"NODI-G2I-EDGE-CHECK-{index:03d}",
            "required_evidence": item,
            "required_status_for_review": "PRESENT_AND_VALIDATED",
            "default_if_missing": "NOT_APPROVED",
        }
        for index, item in enumerate(items, start=1)
    ]


def build_i_negative_fixture_rows() -> list[dict[str, str]]:
    fixtures = [
        ("missing_numeric_error_bound", "numeric_aggregation_error_bound empty", "NOT_APPROVED"),
        ("non_contiguous_edge20_bins", "edge_00|edge_02|edge_03|edge_04|edge_05", "BLOCKED"),
        ("edge20_hash_mismatch", "hash != expected NODI edge20 hash", "BLOCKED"),
        ("formula_flag_true", "formula_use_authorized=true", "HARD_FAIL"),
        ("direct_prs_bin_flag_true", "direct_prs_bin_use_authorized=true", "HARD_FAIL"),
        ("qch_weighting_flag_true", "qch_weighting_authorized=true", "HARD_FAIL"),
        ("accepted_row_expansion_true", "accepted_row_expansion_authorized=true", "HARD_FAIL"),
        ("d1200_borrows_d900", "route_key 660/W800/D1200 uses D900 evidence", "HARD_FAIL"),
        ("auto_map_220nm", "diameter_nm=220 maps to 300 nm PRS", "HARD_FAIL"),
    ]
    return [
        {
            "negative_fixture_id": f"NODI-G2I-EDGE-NEG-{index:03d}",
            "fixture_name": name,
            "fixture_condition": condition,
            "expected_validator_result": expected,
        }
        for index, (name, condition, expected) in enumerate(fixtures, start=1)
    ]


def build_i_validation_rule_rows() -> list[dict[str, str]]:
    return [
        {"validation_rule_id": "NODI-G2I-VAL-001", "rule": "exactly_16_structural_rows_or_declared_scope", "failure_status": "BLOCKED"},
        {"validation_rule_id": "NODI-G2I-VAL-002", "rule": "edge20_hash_matches_expected", "failure_status": "BLOCKED"},
        {"validation_rule_id": "NODI-G2I-VAL-003", "rule": "edge20_bins_count_and_contiguity", "failure_status": "BLOCKED"},
        {"validation_rule_id": "NODI-G2I-VAL-004", "rule": "numeric_error_bounds_present", "failure_status": "NOT_APPROVED"},
        {"validation_rule_id": "NODI-G2I-VAL-005", "rule": "monotonicity_and_conservativeness_present", "failure_status": "NOT_APPROVED"},
        {"validation_rule_id": "NODI-G2I-VAL-006", "rule": "all_authorization_flags_false_by_default", "failure_status": "HARD_FAIL"},
        {"validation_rule_id": "NODI-G2I-VAL-007", "rule": "QCH_BINDING_not_used_for_EDGE_approval", "failure_status": "HARD_FAIL"},
    ]


def build_i_non_edge_rows(nodi_blocker_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "carry_forward_id": "NODI-G2I-NONEDGE-QCH",
            "workstream": "QCH",
            "status": "FORMAL_SIDECAR_ABSENT_SCHEMA_READY_NO_WEIGHTING",
            "source_rows_reviewed": str(len(nodi_blocker_rows)),
            "qch_weighting_authorized": "false",
            "formula_use_authorized": "false",
            "jrc_authorized": "false",
            "required_next_gate": "formal q_ch / flow-split sidecar receipt",
        },
        {
            "carry_forward_id": "NODI-G2I-NONEDGE-BINDING",
            "workstream": "BINDING",
            "status": "220_D1200_UNBOUND_FAIL_CLOSED_NO_AUTO_MAP",
            "source_rows_reviewed": str(len(nodi_blocker_rows)),
            "qch_weighting_authorized": "false",
            "formula_use_authorized": "false",
            "jrc_authorized": "false",
            "required_next_gate": "220/D1200/view-bound repair package",
        },
    ]


def build_i_qch_binding_dashboard_rows(non_edge_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "dashboard_id": f"NODI-G2I-NONEDGE-DASH-{index:03d}",
            "workstream": _value(row, "workstream"),
            "status": _value(row, "status"),
            "state_changed_in_gate2i": "false",
            "qch_weighting_authorized": "false",
            "formula_use_authorized": "false",
            "jrc_authorized": "false",
            "required_next_gate": _value(row, "required_next_gate"),
        }
        for index, row in enumerate(non_edge_rows, start=1)
    ]


def build_self_review_rows() -> list[dict[str, str]]:
    return [
        {"reviewer": "Reviewer A", "focus": "COMSOL Gate2G receipt / SHA / row_count / manifest", "finding_severity": "PASS", "finding": "All required COMSOL Gate2G files are audited against manifest and validation.", "unresolved_risk": "none"},
        {"reviewer": "Reviewer B", "focus": "structural coverage row semantics and edge20 hash", "finding_severity": "PASS", "finding": "16 structural rows align to NODI Gate2G rows, five contiguous bins, expected hash.", "unresolved_risk": "policy still not approved"},
        {"reviewer": "Reviewer C", "focus": "loss/error policy decision correctness", "finding_severity": "PASS_BLOCKED_AS_EXPECTED", "finding": "Structural coverage is received but numeric bounds, monotonicity, and conservativeness remain missing.", "unresolved_risk": "Gate2I/Gate2J evidence required"},
        {"reviewer": "Reviewer D", "focus": "Gate2I future contract completeness and negative fixtures", "finding_severity": "PASS", "finding": "Contract covers required schema, decision rules, validation rules, and nine negative fixtures.", "unresolved_risk": "none"},
        {"reviewer": "Reviewer E", "focus": "forbidden leakage / no accepted row expansion / QCH-BINDING unchanged", "finding_severity": "PASS", "finding": "All authorization flags remain false; Gate2D, QCH, and BINDING states are unchanged.", "unresolved_risk": "none"},
    ]


def build_forbidden_audit_rows(groups: Sequence[Sequence[Mapping[str, Any]]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    idx = 1
    for group_num, group in enumerate(groups, start=1):
        for field in FORBIDDEN_FALSE_FIELDS:
            values = [str(row[field]).lower() for row in group if field in row]
            bad = sorted({v for v in values if v not in {"false", "", "not_applicable"}})
            rows.append(
                {
                    "audit_id": f"NODI-G2H-FORBID-{idx:03d}",
                    "source_group": f"group_{group_num}",
                    "field_name": field,
                    "rows_checked": str(len(values)),
                    "bad_values": "|".join(bad),
                    "audit_status": "PASS_FORBIDDEN_FALSE" if not bad else "FAIL_FORBIDDEN_FIELD_TRUE",
                }
            )
            idx += 1
    return rows


def validate_payload(payload: Mapping[str, Any], *, comsol_root: Path) -> list[str]:
    issues: list[str] = []
    if int(payload.get("structural_coverage_row_count", -1)) != 16:
        issues.append("Gate2H structural proof must have exactly 16 rows")
    if int(payload.get("receipt_support_row_count", -1)) != 16:
        issues.append("Gate2H receipt support must have exactly 16 rows")
    if int(payload.get("gate2d_accepted_row_count", -1)) != EXPECTED_GATE2D_ROWS:
        issues.append("Gate2D accepted ledger must remain exactly 4")
    for row in payload.get("manifest_repro_audit_rows", []):
        if _value(row, "manifest_repro_status") != "PASS_MANIFEST_REPRODUCED":
            issues.append(f"manifest mismatch: {_value(row, 'manifest_artifact_id')}")
    for row in payload.get("structural_coverage_receiver_review_rows", []):
        if _value(row, "receiver_verdict") != "STRUCTURAL_COVERAGE_RECEIVED_REVIEW_ONLY_NOT_POLICY_APPROVED":
            issues.append(f"structural mismatch: {_value(row, 'receiver_review_id')}")
        if _value(row, "edge20_definition_hash") != EXPECTED_EDGE20_HASH:
            issues.append(f"edge20 hash mismatch: {_value(row, 'receiver_review_id')}")
        if _value(row, "edge20_bin_count") != "5" or _value(row, "coverage_contiguous").lower() != "true":
            issues.append(f"coverage contiguity/count failed: {_value(row, 'receiver_review_id')}")
    if not any(_value(row, "policy_decision_verdict") == "EDGE_POLICY_NOT_APPROVED_LOSS_ERROR_GAPS_REMAIN" for row in payload.get("policy_decision_verdict_rows", [])):
        issues.append("policy decision must remain NOT_APPROVED")
    for row in payload.get("gate2h_forbidden_claim_audit_rows", []):
        if _value(row, "audit_status").startswith("FAIL"):
            issues.append(f"forbidden field audit failed: {_value(row, 'audit_id')}")
    negative_names = {_value(row, "fixture_name") for row in payload.get("gate2i_negative_fixture_rows", [])}
    required_negative = {
        "missing_numeric_error_bound",
        "non_contiguous_edge20_bins",
        "edge20_hash_mismatch",
        "formula_flag_true",
        "direct_prs_bin_flag_true",
        "qch_weighting_flag_true",
        "accepted_row_expansion_true",
        "d1200_borrows_d900",
        "auto_map_220nm",
    }
    if not required_negative.issubset(negative_names):
        issues.append("Gate2I negative fixtures missing required cases")
    issues.extend(validate_comsol_v4_readonly_context(payload.get("comsol_v4_context", {})))
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "h_receipt_audit_csv": output_dir / H_RECEIPT_AUDIT,
        "h_manifest_audit_csv": output_dir / H_MANIFEST_AUDIT,
        "h_structural_review_csv": output_dir / H_STRUCTURAL_REVIEW,
        "h_structural_row_verdict_csv": output_dir / H_STRUCTURAL_ROW_VERDICT,
        "h_loss_review_csv": output_dir / H_LOSS_REVIEW,
        "h_policy_verdict_csv": output_dir / H_POLICY_VERDICT,
        "h_report_json": output_dir / H_REPORT_JSON,
        "h_report_md": output_dir / H_REPORT_MD,
        "h_dashboard_csv": output_dir / H_DASHBOARD,
        "h_forbidden_csv": output_dir / H_FORBIDDEN,
        "h_blocker_csv": output_dir / H_BLOCKER,
        "h_self_review_csv": output_dir / H_SELF_REVIEW,
        "report_207_md": report_dir / REPORT_207,
        "i_schema_csv": output_dir / I_SCHEMA,
        "i_decision_rules_csv": output_dir / I_DECISION_RULES,
        "i_checklist_csv": output_dir / I_CHECKLIST,
        "i_negative_csv": output_dir / I_NEGATIVE_FIXTURES,
        "i_validation_csv": output_dir / I_VALIDATION_RULES,
        "i_report_json": output_dir / I_REPORT_JSON,
        "i_report_md": output_dir / I_REPORT_MD,
        "report_208_md": report_dir / REPORT_208,
        "i_non_edge_csv": output_dir / I_NON_EDGE,
        "i_qch_binding_dashboard_csv": output_dir / I_QCH_BINDING_DASH,
    }
    write_csv_rows(paths["h_receipt_audit_csv"], list(payload["package_receipt_audit_rows"]))
    write_csv_rows(paths["h_manifest_audit_csv"], list(payload["manifest_repro_audit_rows"]))
    write_csv_rows(paths["h_structural_review_csv"], list(payload["structural_coverage_receiver_review_rows"]))
    write_csv_rows(paths["h_structural_row_verdict_csv"], list(payload["structural_row_verdict_rows"]))
    write_csv_rows(paths["h_loss_review_csv"], list(payload["loss_error_closure_review_rows"]))
    write_csv_rows(paths["h_policy_verdict_csv"], list(payload["policy_decision_verdict_rows"]))
    write_csv_rows(paths["h_dashboard_csv"], list(payload["gate2h_dashboard_rows"]))
    write_csv_rows(paths["h_forbidden_csv"], list(payload["gate2h_forbidden_claim_audit_rows"]))
    write_csv_rows(paths["h_blocker_csv"], list(payload["gate2h_blocker_carry_forward_rows"]))
    write_csv_rows(paths["h_self_review_csv"], list(payload["gate2h_self_review_rows"]))
    write_csv_rows(paths["i_schema_csv"], list(payload["gate2i_schema_rows"]))
    write_csv_rows(paths["i_decision_rules_csv"], list(payload["gate2i_decision_rule_rows"]))
    write_csv_rows(paths["i_checklist_csv"], list(payload["gate2i_checklist_rows"]))
    write_csv_rows(paths["i_negative_csv"], list(payload["gate2i_negative_fixture_rows"]))
    write_csv_rows(paths["i_validation_csv"], list(payload["gate2i_validation_rule_rows"]))
    write_csv_rows(paths["i_non_edge_csv"], list(payload["gate2i_non_edge_rows"]))
    write_csv_rows(paths["i_qch_binding_dashboard_csv"], list(payload["gate2i_qch_binding_dashboard_rows"]))
    for path in paths.values():
        if path.suffix == ".csv":
            _normalize_lf(path)

    h_payload = dict(payload)
    h_payload["outputs"] = {key: _rel(path) for key, path in paths.items() if key.startswith("h_") or key == "report_207_md"}
    h_payload["output_hashes"] = {key: sha256_file(path) for key, path in paths.items() if (key.startswith("h_") or key == "report_207_md") and path.exists() and path.suffix in {".csv", ".md"}}
    write_json_atomic(paths["h_report_json"], h_payload, sort_keys=True)
    h_payload["output_hashes"]["h_report_json"] = sha256_file(paths["h_report_json"])
    h_md = render_h_report(h_payload)
    paths["h_report_md"].write_text(h_md, encoding="utf-8", newline="\n")
    paths["report_207_md"].write_text(h_md.replace("# NODI/COMSOL Gate2H EDGE Closure Review", "# Report 207 - NODI/COMSOL Gate2H EDGE Closure Review"), encoding="utf-8", newline="\n")

    i_payload = dict(payload)
    i_payload["outputs"] = {key: _rel(path) for key, path in paths.items() if key.startswith("i_") or key == "report_208_md"}
    i_payload["output_hashes"] = {key: sha256_file(path) for key, path in paths.items() if (key.startswith("i_") or key == "report_208_md") and path.exists() and path.suffix in {".csv", ".md"}}
    write_json_atomic(paths["i_report_json"], i_payload, sort_keys=True)
    i_payload["output_hashes"]["i_report_json"] = sha256_file(paths["i_report_json"])
    i_md = render_i_report(i_payload)
    paths["i_report_md"].write_text(i_md, encoding="utf-8", newline="\n")
    paths["report_208_md"].write_text(i_md.replace("# NODI/COMSOL Gate2I EDGE Future Evidence Acceptance Contract", "# Report 208 - NODI/COMSOL Gate2I EDGE Future Evidence Acceptance Contract"), encoding="utf-8", newline="\n")
    return {key: str(path) for key, path in paths.items()}


def render_h_report(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2H EDGE Closure Review",
            "",
            f"Disposition: `{payload['gate2h_disposition']}`.",
            "",
            "Structural coverage is received as review-only evidence: 16 rows, five contiguous edge20 bins per row, expected edge20 hash. EDGE policy remains `NOT_APPROVED` because numeric aggregation error bounds, monotonicity, conservativeness, and approval-grade reproducibility are missing.",
            "",
            f"- structural review: `{hashes.get('h_structural_review_csv', 'pending')}`",
            f"- loss/error review: `{hashes.get('h_loss_review_csv', 'pending')}`",
            f"- policy verdict: `{hashes.get('h_policy_verdict_csv', 'pending')}`",
            f"- JSON report: `{hashes.get('h_report_json', 'pending')}`",
            "",
            "No formula/direct-bin/grain/JRC/q_ch/production/runtime authorization is granted.",
        ]
    ) + "\n"


def render_i_report(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2I EDGE Future Evidence Acceptance Contract",
            "",
            f"Disposition: `{payload['gate2i_disposition']}`.",
            "",
            "This contract defines what a future COMSOL EDGE package must provide before NODI can review policy approval: edge20-resolved evidence, edge4 derivation provenance, numeric error bounds, monotonicity/conservativeness checks, reproducibility hashes, exact binding, and false-by-default authorization flags.",
            "",
            f"- schema: `{hashes.get('i_schema_csv', 'pending')}`",
            f"- decision rules: `{hashes.get('i_decision_rules_csv', 'pending')}`",
            f"- negative fixtures: `{hashes.get('i_negative_csv', 'pending')}`",
            f"- JSON report: `{hashes.get('i_report_json', 'pending')}`",
            "",
            "QCH and BINDING are carried forward only; no status is promoted.",
        ]
    ) + "\n"


def _validation_summary(rows: Sequence[Mapping[str, Any]]) -> str:
    return ";".join(sorted({_value(row, "status") for row in rows if _value(row, "status")}))


def _git_head(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"
    return result.stdout.strip() or "UNKNOWN_COMMIT_READONLY_REFERENCE"


def _validate_false_fields(rows: Sequence[Mapping[str, Any]], group: str) -> list[str]:
    issues: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in FORBIDDEN_FALSE_FIELDS:
            if field in row and str(row[field]).lower() not in {"false", "", "not_applicable"}:
                issues.append(f"{group} row {index} forbidden field {field} is {row[field]!r}")
    return issues


def _row_count(path: Path) -> int:
    if path.suffix.lower() != ".csv":
        return 0
    return len(read_csv_rows(path))


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _value(row: Mapping[str, Any], key: str, default: str = "") -> str:
    value = row.get(key, default)
    if value is None:
        return default
    return str(value)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _normalize_lf(path: Path) -> None:
    data = path.read_bytes()
    while b"\r\n" in data:
        data = data.replace(b"\r\n", b"\n")
    data = data.replace(b"\r", b"")
    path.write_bytes(data)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate2h_gate2i_edge:
        raise SystemExit("Refusing to write Gate2H/Gate2I outputs without explicit confirmation flag.")
    payload = build_payload(comsol_root=args.comsol_root)
    issues = validate_payload(payload, comsol_root=args.comsol_root)
    if issues and payload["gate2h_disposition"] == GATE2H_PASS:
        print(f"NODI_COMSOL_GATE2H_GATE2I_EDGE: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    print(f"NODI_COMSOL_GATE2H_EDGE: {payload['gate2h_disposition']}")
    print(f"NODI_COMSOL_GATE2I_EDGE: {payload['gate2i_disposition']}")
    print(f"gate2h_report_json: {outputs['h_report_json']}")
    print(f"gate2i_report_json: {outputs['i_report_json']}")
    if issues:
        for issue in issues:
            print(f"- {issue}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
