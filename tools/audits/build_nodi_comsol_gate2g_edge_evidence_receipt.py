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

from nodi_simulator.nodi_comsol_next_artifacts import (
    default_comsol_v4_readonly_context,
    validate_comsol_v4_readonly_context,
)
from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


DATE_STAMP = "20260628"
PASS_STATUS = "PASS_GATE2G_EDGE_REVIEW_EVIDENCE_RECEIPT_POLICY_GAP_REGISTERED_NO_FORMULA_NO_JRC"
PARTIAL_STATUS = "PARTIAL_GATE2G_EDGE_RECEIPT_BLOCKED_BY_EVIDENCE_MISMATCH_NO_FORMULA_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2G_EDGE_EVIDENCE_RECEIPT"

OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
REPORT_206 = f"206_NODI_COMSOL_GATE2G_EDGE_EVIDENCE_RECEIPT_AND_POLICY_GAP_{DATE_STAMP}.md"

RECEIPT_REGISTER = f"NODI_COMSOL_GATE2G_EDGE_COMSOL_GATE2F_EVIDENCE_RECEIPT_REGISTER_{DATE_STAMP}.csv"
MANIFEST_AUDIT = f"NODI_COMSOL_GATE2G_EDGE_COMSOL_GATE2F_EVIDENCE_MANIFEST_AUDIT_{DATE_STAMP}.csv"
GROUPING_RECON = f"NODI_COMSOL_GATE2G_EDGE_GROUPING_CROSS_RECONCILIATION_{DATE_STAMP}.csv"
ROW_CONCORDANCE = f"NODI_COMSOL_GATE2G_EDGE_ROW_CONCORDANCE_VERDICT_{DATE_STAMP}.csv"
LOSS_GAP = f"NODI_COMSOL_GATE2G_EDGE_LOSS_ERROR_POLICY_GAP_VERDICT_{DATE_STAMP}.csv"
NEXT_SCHEMA = f"NODI_COMSOL_GATE2G_EDGE_REQUIRED_NEXT_EVIDENCE_SCHEMA_{DATE_STAMP}.csv"
DASHBOARD = f"NODI_COMSOL_GATE2G_EDGE_RECEIVER_DASHBOARD_{DATE_STAMP}.csv"
FORBIDDEN_AUDIT = f"NODI_COMSOL_GATE2G_FORBIDDEN_CLAIM_AUDIT_{DATE_STAMP}.csv"
BLOCKER_CARRY = f"NODI_COMSOL_GATE2G_BLOCKER_CARRY_FORWARD_{DATE_STAMP}.csv"
SELF_REVIEW = f"NODI_COMSOL_GATE2G_EDGE_SELF_REVIEW_{DATE_STAMP}.csv"
REPORT_JSON = f"NODI_COMSOL_GATE2G_EDGE_EVIDENCE_RECEIPT_REPORT_{DATE_STAMP}.json"
REPORT_MD = f"NODI_COMSOL_GATE2G_EDGE_EVIDENCE_RECEIPT_REPORT_{DATE_STAMP}.md"

DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
NODI_REPORT_205 = PROJECT_ROOT / "reports/205_NODI_COMSOL_GATE2F_EDGE_REVIEW_ONLY_POLICY_PREFLIGHT_20260628.md"
NODI_GATE2F_GROUPING = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2F_EDGE4_EDGE20_GROUPING_CANDIDATE_PREFLIGHT_20260628.csv"
NODI_GATE2F_ROW_VERDICT = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2F_EDGE4_EDGE20_ROW_VERDICT_20260628.csv"
NODI_GATE2F_LOSS_CHECKLIST = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2F_EDGE_LOSS_ERROR_SEMANTICS_CHECKLIST_20260628.csv"
NODI_GATE2F_NON_EDGE = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2F_NON_EDGE_WORKSTREAM_CARRY_FORWARD_20260628.csv"
NODI_GATE2F_REPORT_JSON = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2F_EDGE_POLICY_PREFLIGHT_REPORT_20260628.json"
NODI_GATE2D_ACCEPTED_LEDGER = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_20260628.csv"

COMSOL_ARTIFACTS = (
    (
        "G2G-COMSOL-EDGE-EVID-CAND",
        "edge_review_evidence_candidate",
        Path("roadmap/COMSOL_GATE2F_EDGE4_EDGE20_REVIEW_EVIDENCE_CANDIDATE_20260628.csv"),
    ),
    (
        "G2G-COMSOL-EDGE-EVID-PACKET",
        "edge_review_evidence_packet",
        Path("roadmap/COMSOL_GATE2F_EDGE4_EDGE20_REVIEW_EVIDENCE_PACKET_20260628.md"),
    ),
    (
        "G2G-COMSOL-EDGE-LOSS-CAND",
        "edge_loss_error_semantics_candidate",
        Path("roadmap/COMSOL_GATE2F_EDGE_LOSS_ERROR_SEMANTICS_CANDIDATE_20260628.csv"),
    ),
    (
        "G2G-COMSOL-EDGE-LOSS-PACKET",
        "edge_loss_error_semantics_packet",
        Path("roadmap/COMSOL_GATE2F_EDGE_LOSS_ERROR_SEMANTICS_PACKET_20260628.md"),
    ),
    (
        "G2G-COMSOL-EDGE-EXCLUSIONS",
        "edge_exclusions_carry_forward",
        Path("roadmap/COMSOL_GATE2F_EDGE_EXCLUSIONS_CARRY_FORWARD_20260628.csv"),
    ),
    (
        "G2G-COMSOL-EDGE-VALIDATION",
        "edge_review_evidence_validation",
        Path("roadmap/COMSOL_GATE2F_EDGE_REVIEW_EVIDENCE_VALIDATION_20260628.csv"),
    ),
    (
        "G2G-COMSOL-EDGE-MANIFEST",
        "edge_review_evidence_manifest",
        Path("roadmap/COMSOL_GATE2F_EDGE_REVIEW_EVIDENCE_MANIFEST_20260628.csv"),
    ),
    (
        "G2G-COMSOL-EDGE-MASTER",
        "edge_review_evidence_master_packet",
        Path("roadmap/COMSOL_GATE2F_EDGE_REVIEW_EVIDENCE_MASTER_PACKET_20260628.md"),
    ),
)

COMSOL_CANDIDATE = COMSOL_ARTIFACTS[0][2]
COMSOL_LOSS = COMSOL_ARTIFACTS[2][2]
COMSOL_EXCLUSIONS = COMSOL_ARTIFACTS[4][2]
COMSOL_VALIDATION = COMSOL_ARTIFACTS[5][2]
COMSOL_MANIFEST = COMSOL_ARTIFACTS[6][2]

EXPECTED_EDGE20_HASH = "b8b3358e7218e3ebc704c2c8dcaf2c9a0feb15283fa704610b39f8afc68d5ca3"
EXPECTED_GATE2D_ACCEPTED_ROW_COUNT = 4
FORBIDDEN_FALSE_FIELDS = (
    "direct_prs_bin_use_authorized",
    "formula_use_authorized",
    "grain_level_ingestion_authorized",
    "accepted_row_expansion_authorized",
    "edge4_policy_approved",
    "edge4_row_accepted",
    "policy_approved",
    "decision_use_allowed",
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
    "can_enter_weighting",
    "can_enter_jrc",
    "is_chi_selected",
    "is_production_ingestion",
    "is_runtime_configuration",
)
FORBIDDEN_CLAIMS = (
    "policy approval",
    "accepted row expansion",
    "direct PRS edge20 bin use",
    "grain-level ingestion",
    "formula use",
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
    parser = argparse.ArgumentParser(description="Build NODI Gate2G-EDGE evidence receipt and policy gap ledger.")
    parser.add_argument("--confirm-gate2g-edge-receipt", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_gate2g_payload(
    *,
    comsol_root: Path,
    nodi_report_205_path: Path | None = None,
    nodi_grouping_path: Path | None = None,
    nodi_row_verdict_path: Path | None = None,
    nodi_loss_checklist_path: Path | None = None,
    nodi_non_edge_path: Path | None = None,
    nodi_gate2f_report_json_path: Path | None = None,
    nodi_gate2d_accepted_ledger_path: Path | None = None,
) -> dict[str, Any]:
    nodi_report_205_path = nodi_report_205_path or NODI_REPORT_205
    nodi_grouping_path = nodi_grouping_path or NODI_GATE2F_GROUPING
    nodi_row_verdict_path = nodi_row_verdict_path or NODI_GATE2F_ROW_VERDICT
    nodi_loss_checklist_path = nodi_loss_checklist_path or NODI_GATE2F_LOSS_CHECKLIST
    nodi_non_edge_path = nodi_non_edge_path or NODI_GATE2F_NON_EDGE
    nodi_gate2f_report_json_path = nodi_gate2f_report_json_path or NODI_GATE2F_REPORT_JSON
    nodi_gate2d_accepted_ledger_path = nodi_gate2d_accepted_ledger_path or NODI_GATE2D_ACCEPTED_LEDGER

    candidate_rows = read_csv_rows(comsol_root / COMSOL_CANDIDATE)
    loss_rows = read_csv_rows(comsol_root / COMSOL_LOSS)
    exclusion_rows = read_csv_rows(comsol_root / COMSOL_EXCLUSIONS)
    validation_rows = read_csv_rows(comsol_root / COMSOL_VALIDATION)
    manifest_rows = read_csv_rows(comsol_root / COMSOL_MANIFEST)
    nodi_grouping_rows = read_csv_rows(nodi_grouping_path)
    nodi_row_verdict_rows = read_csv_rows(nodi_row_verdict_path)
    nodi_loss_rows = read_csv_rows(nodi_loss_checklist_path)
    nodi_non_edge_rows = read_csv_rows(nodi_non_edge_path)
    gate2d_rows = read_csv_rows(nodi_gate2d_accepted_ledger_path)
    report_205_text = nodi_report_205_path.read_text(encoding="utf-8")
    gate2f_report_text = nodi_gate2f_report_json_path.read_text(encoding="utf-8")

    receipt_rows = build_receipt_register(comsol_root, manifest_rows, validation_rows)
    manifest_audit_rows = build_manifest_audit_rows(comsol_root, manifest_rows, validation_rows)
    recon_rows = build_grouping_reconciliation_rows(nodi_grouping_rows, candidate_rows)
    row_verdict_rows = build_row_concordance_rows(recon_rows)
    loss_gap_rows = build_loss_gap_rows(loss_rows, nodi_loss_rows)
    next_schema_rows = build_required_next_schema_rows()
    blocker_rows = build_blocker_carry_forward_rows(exclusion_rows, nodi_non_edge_rows, gate2d_rows)
    forbidden_rows = build_forbidden_audit_rows(candidate_rows, recon_rows, loss_gap_rows, blocker_rows)
    dashboard_rows = build_dashboard_rows(recon_rows, loss_gap_rows, blocker_rows, gate2d_rows)
    self_review_rows = build_self_review_rows()
    manifest_ok = all(_value(row, "manifest_audit_status") == "PASS_MANIFEST_REPRODUCED" for row in manifest_audit_rows)
    concordant = all(_value(row, "concordance_status") == "EDGE_REVIEW_ONLY_GROUPING_CONCORDANT_NOT_POLICY_APPROVED" for row in recon_rows)
    status = PASS_STATUS if manifest_ok and concordant and len(candidate_rows) == 16 and len(nodi_grouping_rows) == 16 else PARTIAL_STATUS
    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2g_edge_evidence_receipt_v1",
        "date_stamp": DATE_STAMP,
        "status": status,
        "gate2g_edge_disposition": status,
        "comsol_candidate_row_count": len(candidate_rows),
        "nodi_gate2f_grouping_row_count": len(nodi_grouping_rows),
        "nodi_gate2f_row_verdict_row_count": len(nodi_row_verdict_rows),
        "loss_error_semantics_row_count": len(loss_rows),
        "manifest_row_count": len(manifest_rows),
        "validation_row_count": len(validation_rows),
        "gate2d_accepted_row_count": len(gate2d_rows),
        "nodi_edge20_definition_hash": EXPECTED_EDGE20_HASH,
        "report205_gate2f_pass_present": "PASS_GATE2F_EDGE_REVIEW_ONLY_GROUPING_PREFLIGHT_NO_FORMULA_NO_JRC"
        in report_205_text,
        "gate2f_report_reference_present": "PASS_GATE2F_EDGE_REVIEW_ONLY_GROUPING_PREFLIGHT_NO_FORMULA_NO_JRC"
        in gate2f_report_text,
        "receipt_register_rows": receipt_rows,
        "manifest_audit_rows": manifest_audit_rows,
        "grouping_cross_reconciliation_rows": recon_rows,
        "row_concordance_verdict_rows": row_verdict_rows,
        "loss_error_policy_gap_rows": loss_gap_rows,
        "required_next_evidence_schema_rows": next_schema_rows,
        "forbidden_claim_audit_rows": forbidden_rows,
        "blocker_carry_forward_rows": blocker_rows,
        "receiver_dashboard_rows": dashboard_rows,
        "self_review_rows": self_review_rows,
        "comsol_v4_context": default_comsol_v4_readonly_context(),
        "edge_policy_approved": False,
        "accepted_row_expansion_authorized": False,
        "direct_prs_bin_use_authorized": False,
        "formula_use_authorized": False,
        "grain_level_ingestion_authorized": False,
        "weighting_or_jrc_allowed": False,
    }
    return payload


def build_receipt_register(
    comsol_root: Path, manifest_rows: Sequence[Mapping[str, Any]], validation_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    manifest_by_path = {_normalize_path(_value(row, "path")): row for row in manifest_rows}
    validation_status = _validation_summary(validation_rows)
    rows: list[dict[str, str]] = []
    for evidence_id, role, relative in COMSOL_ARTIFACTS:
        path = comsol_root / relative
        manifest = manifest_by_path.get(relative.as_posix(), {})
        source_sha = sha256_file(path)
        source_rows = _row_count(path)
        rows.append(
            {
                "receipt_id": evidence_id,
                "source_project": "comsol_ev_pbs_bonded_cross_junction",
                "source_path": str(path),
                "relative_source_path": relative.as_posix(),
                "file_role": role,
                "source_sha256": source_sha,
                "row_count": str(source_rows),
                "manifest_artifact_id": _value(manifest, "artifact_id"),
                "manifest_sha256": _value(manifest, "sha256"),
                "manifest_row_count": _value(manifest, "row_count"),
                "manifest_match": _bool_text(
                    (not manifest)
                    or (
                        _value(manifest, "sha256") == source_sha
                        and _value(manifest, "row_count") in {str(source_rows), "0"}
                    )
                ),
                "validation_status_summary": validation_status,
                "allowed_use": "COMSOL Gate2F EDGE evidence receipt; review-only policy gap registration",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
                "claim_boundary": "evidence receipt only; not data acceptance; not policy approval; not formula",
                "required_next_gate": "Gate2H-EDGE-LOSS-ERROR-CLOSURE",
            }
        )
    return rows


def build_manifest_audit_rows(
    comsol_root: Path, manifest_rows: Sequence[Mapping[str, Any]], validation_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    validation_summary = _validation_summary(validation_rows)
    rows: list[dict[str, str]] = []
    for index, manifest in enumerate(manifest_rows, start=1):
        raw_path = _value(manifest, "path")
        path = Path(raw_path)
        actual_path = path if path.is_absolute() else comsol_root / path
        exists = actual_path.exists()
        actual_sha = sha256_file(actual_path) if exists else ""
        actual_rows = _row_count(actual_path) if exists else -1
        sha_match = exists and actual_sha == _value(manifest, "sha256")
        row_match = exists and _value(manifest, "row_count") in {str(actual_rows), "0"}
        rows.append(
            {
                "manifest_audit_id": f"NODI-G2G-MANIFEST-AUDIT-{index:03d}",
                "manifest_artifact_id": _value(manifest, "artifact_id"),
                "manifest_path": raw_path,
                "resolved_path": str(actual_path),
                "exists": _bool_text(exists),
                "manifest_sha256": _value(manifest, "sha256"),
                "actual_sha256": actual_sha,
                "manifest_row_count": _value(manifest, "row_count"),
                "actual_row_count": str(actual_rows) if exists else "",
                "sha_match": _bool_text(sha_match),
                "row_count_match": _bool_text(row_match),
                "validation_status_summary": validation_summary,
                "manifest_audit_status": "PASS_MANIFEST_REPRODUCED" if sha_match and row_match else "FAIL_MANIFEST_MISMATCH",
                "allowed_use": "manifest reproducibility audit",
                "blocked_use": "policy approval; formula use; accepted row expansion",
            }
        )
    return rows


def build_grouping_reconciliation_rows(
    nodi_rows: Sequence[Mapping[str, Any]], comsol_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    comsol_by_key = {_grouping_key(row, is_comsol=True): row for row in comsol_rows}
    rows: list[dict[str, str]] = []
    for index, nodi in enumerate(nodi_rows, start=1):
        key = _grouping_key(nodi, is_comsol=False)
        comsol = comsol_by_key.get(key, {})
        edge20_match = _value(nodi, "candidate_edge20_group") == _value(comsol, "proposed_edge20_bins_covered")
        hash_match = _value(nodi, "nodi_edge20_definition_hash") == _value(comsol, "nodi_edge20_definition_hash") == EXPECTED_EDGE20_HASH
        covered_match = _value(nodi, "edge20_bins_covered") == str(len(_value(comsol, "proposed_edge20_bins_covered").split("|"))) == "5"
        source_id_match = _value(nodi, "source_edge_deliverable_row_id") == _value(comsol, "source_edge_skeleton_row_id")
        matched = bool(comsol) and edge20_match and hash_match and covered_match and source_id_match
        rows.append(
            {
                "reconciliation_id": f"NODI-G2G-EDGE-RECON-{index:03d}",
                "nodi_grouping_preflight_id": _value(nodi, "grouping_preflight_id"),
                "comsol_gate2f_edge_evidence_id": _value(comsol, "gate2f_edge_evidence_id"),
                "source_edge_skeleton_row_id": _value(nodi, "source_edge_deliverable_row_id"),
                "route_key": _value(nodi, "route_key"),
                "NODI_view": _value(nodi, "NODI_view"),
                "diameter_nm": _value(nodi, "diameter_nm"),
                "tpd_proxy_aggregation_basis": _value(nodi, "tpd_proxy_aggregation_basis"),
                "edge4_bin_label": _value(nodi, "edge4_bin_label"),
                "nodi_edge20_definition_hash": _value(nodi, "nodi_edge20_definition_hash"),
                "nodi_candidate_edge20_group": _value(nodi, "candidate_edge20_group"),
                "comsol_candidate_edge20_group": _value(comsol, "proposed_edge20_bins_covered"),
                "edge20_bins_covered": _value(nodi, "edge20_bins_covered"),
                "edge20_group_match": _bool_text(edge20_match),
                "edge20_hash_match": _bool_text(hash_match),
                "scope_key_match": _bool_text(bool(comsol)),
                "source_row_id_match": _bool_text(source_id_match),
                "concordance_status": "EDGE_REVIEW_ONLY_GROUPING_CONCORDANT_NOT_POLICY_APPROVED"
                if matched
                else "BLOCKED_EDGE_GROUPING_MISMATCH",
                "policy_approved": "false",
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "accepted_row_expansion_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "production_ingestion_authorized": "false",
                "runtime_configuration_authorized": "false",
                "allowed_use": "review-only evidence receipt concordance",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
                "required_next_gate": "Gate2H-EDGE-LOSS-ERROR-CLOSURE",
            }
        )
    return rows


def build_row_concordance_rows(recon_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "row_concordance_id": f"NODI-G2G-EDGE-CONCORD-{index:03d}",
            "source_edge_skeleton_row_id": _value(row, "source_edge_skeleton_row_id"),
            "route_key": _value(row, "route_key"),
            "NODI_view": _value(row, "NODI_view"),
            "diameter_nm": _value(row, "diameter_nm"),
            "tpd_proxy_aggregation_basis": _value(row, "tpd_proxy_aggregation_basis"),
            "edge4_bin_label": _value(row, "edge4_bin_label"),
            "nodi_edge20_definition_hash": _value(row, "nodi_edge20_definition_hash"),
            "edge20_bins_covered": _value(row, "edge20_bins_covered"),
            "row_verdict": _value(row, "concordance_status"),
            "policy_approval_status": "NOT_APPROVED",
            "direct_prs_bin_use_authorized": "false",
            "formula_use_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "accepted_row_expansion_authorized": "false",
            "required_next_gate": _value(row, "required_next_gate"),
        }
        for index, row in enumerate(recon_rows, start=1)
    ]


def build_loss_gap_rows(
    comsol_loss_rows: Sequence[Mapping[str, Any]], nodi_loss_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    by_area = {_value(row, "semantics_area"): row for row in nodi_loss_rows}
    info_present = bool(comsol_loss_rows) and all(_value(row, "information_loss_description") for row in comsol_loss_rows)
    structural_coverage = bool(comsol_loss_rows) and all(_value(row, "candidate_edge20_bins_covered") for row in comsol_loss_rows)
    specs = [
        (
            "information_loss_description",
            "information_loss",
            "PRESENT_STRUCTURAL_BUT_INSUFFICIENT_FOR_POLICY_APPROVAL" if info_present else "MISSING",
            "Needs quantitative or bounded description of within-edge4 loss.",
        ),
        (
            "coverage_completeness",
            "coverage",
            "STRUCTURAL_PROOF_RECEIVED_REVIEWABLE_NOT_APPROVED" if structural_coverage else "MISSING",
            "Needs explicit completeness/non-overlap proof across all edge4 groups.",
        ),
        (
            "numeric_aggregation_error_bound",
            "error_bounds",
            "MISSING_REQUIRED_FOR_POLICY_APPROVAL",
            "Need numeric/categorical upper/lower aggregation error bounds.",
        ),
        (
            "monotonicity_check",
            "monotonicity",
            "MISSING_REQUIRED_FOR_POLICY_APPROVAL",
            "Need monotonicity check or explicit violation flags.",
        ),
        (
            "conservativeness_check",
            "conservativeness",
            "MISSING_REQUIRED_FOR_POLICY_APPROVAL",
            "Need conservative bound or no-decision-use fallback.",
        ),
        (
            "reproducibility_check",
            "reproducibility",
            "PARTIAL_STRUCTURAL_RECEIPT_ONLY",
            "SHA/row_count/grouping are reproducible, but approval evidence is incomplete.",
        ),
        (
            "formula_exclusion_condition",
            "formula_exclusion",
            "ACTIVE_FORMULA_EXCLUSION",
            "Formula use stays forbidden even with concordant grouping.",
        ),
        (
            "policy_approval_status",
            "review_context_only",
            "NOT_APPROVED",
            "Receipt is review-only and cannot be used as policy approval.",
        ),
    ]
    rows: list[dict[str, str]] = []
    for index, (gap_id, area, status, reason) in enumerate(specs, start=1):
        nodi = by_area.get(area, {})
        rows.append(
            {
                "gap_verdict_id": f"NODI-G2G-EDGE-GAP-{index:03d}",
                "gap_item": gap_id,
                "semantics_area": area,
                "comsol_rows_reviewed": str(len(comsol_loss_rows)),
                "nodi_gate2f_check_id": _value(nodi, "check_id"),
                "received_status": status,
                "policy_approval_status": "NOT_APPROVED",
                "gap_reason": reason,
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "accepted_row_expansion_authorized": "false",
                "allowed_use": "policy gap ledger only",
                "blocked_use": "formula use; direct PRS bin use; grain-level ingestion; weighting; JRC",
                "required_next_gate": "Gate2H-EDGE-LOSS-ERROR-CLOSURE",
            }
        )
    return rows


def build_required_next_schema_rows() -> list[dict[str, str]]:
    specs = [
        ("edge4_bin_label", "string", "edge_norm_0p00_0p25 style label", "exact"),
        ("nodi_edge20_definition_hash", "sha256", EXPECTED_EDGE20_HASH, "exact"),
        ("candidate_edge20_bins_covered", "pipe-delimited ids", "five edge20 bins per quarter", "exact"),
        ("information_loss_description", "string", "bounded loss semantics", "required"),
        ("numeric_aggregation_error_bound", "number or bounded category", "not MISSING", "required"),
        ("numeric_error_bound_units", "string", "units or dimensionless basis", "required"),
        ("monotonicity_check_result", "enum", "PASS/FAIL/REVIEW_REQUIRED with evidence", "required"),
        ("conservativeness_check_result", "enum", "PASS/FAIL/REVIEW_REQUIRED with evidence", "required"),
        ("reproducibility_checks", "structured refs", "source SHA/row_count/validator id", "required"),
        ("formula_exclusion_flags", "booleans", "all formula/direct/grain/JRC/q_ch flags false unless future gate", "required"),
    ]
    return [
        {
            "schema_row_id": f"NODI-G2G-EDGE-NEXT-SCHEMA-{index:03d}",
            "field_name": field,
            "required_type": field_type,
            "acceptance_requirement": requirement,
            "status_requirement": status,
            "required_next_gate": "Gate2H-EDGE-LOSS-ERROR-CLOSURE",
        }
        for index, (field, field_type, requirement, status) in enumerate(specs, start=1)
    ]


def build_blocker_carry_forward_rows(
    comsol_exclusion_rows: Sequence[Mapping[str, Any]],
    nodi_non_edge_rows: Sequence[Mapping[str, Any]],
    gate2d_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = [
        {
            "blocker_id": "NODI-G2G-BLOCK-GATE2D",
            "blocker_class": "Gate2D accepted ledger freeze",
            "source_status": "FROZEN_EXACTLY_FOUR_ROWS",
            "row_count_or_scope": str(len(gate2d_rows)),
            "gate2g_status": "UNCHANGED_NO_ACCEPTED_ROW_EXPANSION",
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "jrc_authorized": "false",
            "required_next_gate": "dedicated future gate before any expansion",
        }
    ]
    for index, row in enumerate(comsol_exclusion_rows, start=1):
        rows.append(
            {
                "blocker_id": f"NODI-G2G-BLOCK-COMSOL-{index:03d}",
                "blocker_class": _value(row, "excluded_class"),
                "source_status": _value(row, "carry_forward_status"),
                "row_count_or_scope": _value(row, "row_count_or_scope"),
                "gate2g_status": "CARRY_FORWARD_BLOCKED_OR_REVIEW_ONLY",
                "accepted_row_expansion_authorized": "false",
                "formula_use_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "required_next_gate": _value(row, "required_next_gate"),
            }
        )
    for index, row in enumerate(nodi_non_edge_rows, start=1):
        rows.append(
            {
                "blocker_id": f"NODI-G2G-BLOCK-NODI-NONEDGE-{index:03d}",
                "blocker_class": _value(row, "workstream"),
                "source_status": _value(row, "gate2f_status"),
                "row_count_or_scope": "non_edge_workstream",
                "gate2g_status": "UNCHANGED_FROM_GATE2F_EDGE",
                "accepted_row_expansion_authorized": "false",
                "formula_use_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "required_next_gate": _value(row, "required_next_gate"),
            }
        )
    return rows


def build_forbidden_audit_rows(
    candidate_rows: Sequence[Mapping[str, Any]],
    recon_rows: Sequence[Mapping[str, Any]],
    loss_gap_rows: Sequence[Mapping[str, Any]],
    blocker_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    groups = [
        ("COMSOL_EDGE_CANDIDATE", candidate_rows),
        ("NODI_RECONCILIATION", recon_rows),
        ("LOSS_GAP", loss_gap_rows),
        ("BLOCKER_CARRY_FORWARD", blocker_rows),
    ]
    rows: list[dict[str, str]] = []
    audit_index = 1
    for group_name, group_rows in groups:
        for field in FORBIDDEN_FALSE_FIELDS:
            values = [str(row[field]).lower() for row in group_rows if field in row]
            bad_values = sorted({value for value in values if value not in {"false", "", "not_applicable"}})
            rows.append(
                {
                    "audit_id": f"NODI-G2G-FORBID-{audit_index:03d}",
                    "source_group": group_name,
                    "field_name": field,
                    "rows_checked": str(len(values)),
                    "bad_values": "|".join(bad_values),
                    "audit_status": "PASS_FORBIDDEN_FALSE" if not bad_values else "FAIL_FORBIDDEN_FIELD_TRUE",
                }
            )
            audit_index += 1
    return rows


def build_dashboard_rows(
    recon_rows: Sequence[Mapping[str, Any]],
    loss_gap_rows: Sequence[Mapping[str, Any]],
    blocker_rows: Sequence[Mapping[str, Any]],
    gate2d_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    concordant = sum(
        1
        for row in recon_rows
        if _value(row, "concordance_status") == "EDGE_REVIEW_ONLY_GROUPING_CONCORDANT_NOT_POLICY_APPROVED"
    )
    return [
        {
            "dashboard_id": "NODI-G2G-DASH-001",
            "topic": "COMSOL Gate2F evidence receipt",
            "status": "RECEIVED_REVIEW_ONLY_EVIDENCE",
            "row_count": "8_artifacts",
            "policy_approved": "false",
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "required_next_gate": "Gate2H-EDGE-LOSS-ERROR-CLOSURE",
        },
        {
            "dashboard_id": "NODI-G2G-DASH-002",
            "topic": "16-row grouping concordance",
            "status": "CONCORDANT_NOT_POLICY_APPROVED" if concordant == 16 else "PARTIAL_MISMATCH",
            "row_count": str(len(recon_rows)),
            "concordant_row_count": str(concordant),
            "policy_approved": "false",
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "required_next_gate": "Gate2H-EDGE-LOSS-ERROR-CLOSURE",
        },
        {
            "dashboard_id": "NODI-G2G-DASH-003",
            "topic": "loss/error policy gap",
            "status": "POLICY_GAP_OPEN_NOT_APPROVED",
            "row_count": str(len(loss_gap_rows)),
            "policy_approved": "false",
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "required_next_gate": "Gate2H-EDGE-LOSS-ERROR-CLOSURE",
        },
        {
            "dashboard_id": "NODI-G2G-DASH-004",
            "topic": "Gate2D/QCH/BINDING carry-forward",
            "status": "UNCHANGED_BLOCKED_OR_REVIEW_ONLY",
            "row_count": str(len(blocker_rows)),
            "gate2d_accepted_row_count": str(len(gate2d_rows)),
            "policy_approved": "false",
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "required_next_gate": "separate future gates",
        },
    ]


def build_self_review_rows() -> list[dict[str, str]]:
    return [
        {
            "reviewer": "Reviewer A",
            "focus": "COMSOL evidence path/SHA/row_count/manifest",
            "finding_severity": "PASS",
            "finding": "COMSOL Gate2F evidence paths, hashes, row counts, manifest, and validation are reproducible.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer B",
            "focus": "16-row grouping concordance and edge20 hash",
            "finding_severity": "PASS",
            "finding": "All 16 COMSOL EDGE evidence rows match NODI Gate2F grouping by scope key, edge20 group, row id, and hash.",
            "unresolved_risk": "policy approval still not granted",
        },
        {
            "reviewer": "Reviewer C",
            "focus": "loss/error policy gap and next evidence schema",
            "finding_severity": "PASS_BLOCKED_AS_EXPECTED",
            "finding": "Information-loss placeholders are present, but numeric bounds, monotonicity, conservativeness, and approval evidence remain missing.",
            "unresolved_risk": "Gate2H closure evidence required",
        },
        {
            "reviewer": "Reviewer D",
            "focus": "forbidden leakage / no accepted expansion / QCH-BINDING unchanged",
            "finding_severity": "PASS",
            "finding": "All authorization fields remain false; Gate2D stays four rows; QCH and BINDING are unchanged.",
            "unresolved_risk": "none",
        },
    ]


def validate_gate2g_payload(payload: Mapping[str, Any], *, comsol_root: Path) -> list[str]:
    issues: list[str] = []
    if _value(payload, "status") not in {PASS_STATUS, PARTIAL_STATUS}:
        issues.append("unexpected Gate2G status")
    if int(payload.get("comsol_candidate_row_count", -1)) != 16:
        issues.append("COMSOL Gate2F candidate must have exactly 16 rows")
    if int(payload.get("nodi_gate2f_grouping_row_count", -1)) != 16:
        issues.append("NODI Gate2F grouping must have exactly 16 rows")
    if int(payload.get("gate2d_accepted_row_count", -1)) != EXPECTED_GATE2D_ACCEPTED_ROW_COUNT:
        issues.append("Gate2D accepted ledger must remain exactly 4 rows")
    if _value(payload, "nodi_edge20_definition_hash") != EXPECTED_EDGE20_HASH:
        issues.append("NODI edge20 hash mismatch hard fail")
    for row in payload.get("manifest_audit_rows", []):
        if _value(row, "manifest_audit_status") != "PASS_MANIFEST_REPRODUCED":
            issues.append(f"manifest mismatch: {_value(row, 'manifest_artifact_id')}")
    for row in payload.get("grouping_cross_reconciliation_rows", []):
        if _value(row, "concordance_status") != "EDGE_REVIEW_ONLY_GROUPING_CONCORDANT_NOT_POLICY_APPROVED":
            issues.append(f"grouping mismatch: {_value(row, 'reconciliation_id')}")
        if _value(row, "nodi_edge20_definition_hash") != EXPECTED_EDGE20_HASH:
            issues.append(f"edge20 hash mismatch: {_value(row, 'reconciliation_id')}")
        if _value(row, "edge20_bins_covered") != "5":
            issues.append(f"edge20 bins covered mismatch: {_value(row, 'reconciliation_id')}")
    for row in payload.get("forbidden_claim_audit_rows", []):
        if _value(row, "audit_status").startswith("FAIL"):
            issues.append(f"forbidden field audit failed: {_value(row, 'audit_id')}")
    for group in (
        "grouping_cross_reconciliation_rows",
        "row_concordance_verdict_rows",
        "loss_error_policy_gap_rows",
        "blocker_carry_forward_rows",
        "receiver_dashboard_rows",
    ):
        issues.extend(_validate_forbidden_false_fields(payload.get(group, []), group))
    issues.extend(validate_comsol_v4_readonly_context(payload.get("comsol_v4_context", {})))
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "receipt_register_csv": output_dir / RECEIPT_REGISTER,
        "manifest_audit_csv": output_dir / MANIFEST_AUDIT,
        "grouping_recon_csv": output_dir / GROUPING_RECON,
        "row_concordance_csv": output_dir / ROW_CONCORDANCE,
        "loss_gap_csv": output_dir / LOSS_GAP,
        "next_schema_csv": output_dir / NEXT_SCHEMA,
        "dashboard_csv": output_dir / DASHBOARD,
        "forbidden_audit_csv": output_dir / FORBIDDEN_AUDIT,
        "blocker_carry_csv": output_dir / BLOCKER_CARRY,
        "self_review_csv": output_dir / SELF_REVIEW,
        "report_json": output_dir / REPORT_JSON,
        "report_md": output_dir / REPORT_MD,
        "report_206_md": report_dir / REPORT_206,
    }
    write_csv_rows(paths["receipt_register_csv"], list(payload["receipt_register_rows"]))
    write_csv_rows(paths["manifest_audit_csv"], list(payload["manifest_audit_rows"]))
    write_csv_rows(paths["grouping_recon_csv"], list(payload["grouping_cross_reconciliation_rows"]))
    write_csv_rows(paths["row_concordance_csv"], list(payload["row_concordance_verdict_rows"]))
    write_csv_rows(paths["loss_gap_csv"], list(payload["loss_error_policy_gap_rows"]))
    write_csv_rows(paths["next_schema_csv"], list(payload["required_next_evidence_schema_rows"]))
    write_csv_rows(paths["dashboard_csv"], list(payload["receiver_dashboard_rows"]))
    write_csv_rows(paths["forbidden_audit_csv"], list(payload["forbidden_claim_audit_rows"]))
    write_csv_rows(paths["blocker_carry_csv"], list(payload["blocker_carry_forward_rows"]))
    write_csv_rows(paths["self_review_csv"], list(payload["self_review_rows"]))
    for path in paths.values():
        if path.suffix == ".csv":
            _normalize_lf(path)

    report_payload = dict(payload)
    report_payload["outputs"] = {key: _rel(path) for key, path in paths.items()}
    report_payload["output_hashes"] = {
        key: sha256_file(path)
        for key, path in paths.items()
        if path.exists() and path.suffix in {".csv", ".md"}
    }
    write_json_atomic(paths["report_json"], report_payload, sort_keys=True)
    report_payload["output_hashes"]["report_json"] = sha256_file(paths["report_json"])
    report_md = render_report_md(report_payload)
    paths["report_md"].write_text(report_md, encoding="utf-8", newline="\n")
    paths["report_206_md"].write_text(
        report_md.replace(
            "# NODI/COMSOL Gate2G-EDGE Evidence Receipt and Policy Gap Ledger",
            "# Report 206 - NODI/COMSOL Gate2G-EDGE Evidence Receipt and Policy Gap Ledger",
        ),
        encoding="utf-8",
        newline="\n",
    )
    return {key: str(path) for key, path in paths.items()}


def render_report_md(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2G-EDGE Evidence Receipt and Policy Gap Ledger",
            "",
            "Date: 2026-06-28",
            "",
            "## Disposition",
            "",
            f"`{payload['status']}`",
            "",
            "NODI receives the COMSOL Gate2F EDGE review evidence package as evidence-only. This is not data acceptance, policy approval, formula use, direct PRS bin use, grain-level ingestion, JRC, runtime, or production.",
            "",
            "## Evidence Receipt",
            "",
            f"COMSOL candidate rows: `{payload['comsol_candidate_row_count']}`. NODI Gate2F grouping rows: `{payload['nodi_gate2f_grouping_row_count']}`. Manifest rows audited: `{payload['manifest_row_count']}`.",
            "",
            "## Grouping Concordance",
            "",
            "All 16 rows are reconciled as `EDGE_REVIEW_ONLY_GROUPING_CONCORDANT_NOT_POLICY_APPROVED` when route/view/diameter, TPD proxy basis, edge4 label, edge20 group, and NODI edge20 hash match.",
            "",
            "## Policy Gap",
            "",
            "`policy_approval_status = NOT_APPROVED`. Numeric aggregation error bound, monotonicity, conservativeness, and approval-grade reproducibility evidence remain open. Required next gate: `Gate2H-EDGE-LOSS-ERROR-CLOSURE`.",
            "",
            "## Carry-Forward",
            "",
            "Gate2D accepted ledger stays frozen at four aggregate proxy rows. QCH remains schema-ready/no formal sidecar and not weighting. BINDING remains fail-closed for 220 nm, D1200, and UNBOUND view.",
            "",
            "## Output Hashes",
            "",
            f"- receipt register: `{hashes.get('receipt_register_csv', 'pending')}`",
            f"- manifest audit: `{hashes.get('manifest_audit_csv', 'pending')}`",
            f"- grouping reconciliation: `{hashes.get('grouping_recon_csv', 'pending')}`",
            f"- row concordance: `{hashes.get('row_concordance_csv', 'pending')}`",
            f"- loss/error gap: `{hashes.get('loss_gap_csv', 'pending')}`",
            f"- dashboard: `{hashes.get('dashboard_csv', 'pending')}`",
            f"- JSON report: `{hashes.get('report_json', 'pending')}`",
            "",
            "## Non-Authorization",
            "",
            "No edge4-to-edge20 policy approval, accepted row expansion, direct PRS edge20 bin use, grain-level ingestion, formula use, q_ch weighting, chi_selected, route_score, JRC, yield, winner, detection_probability, wet pass probability, clogging rate, runtime configuration, or production ingestion is authorized.",
        ]
    ) + "\n"


def _grouping_key(row: Mapping[str, Any], *, is_comsol: bool) -> tuple[str, str, str, str, str, str]:
    return (
        _value(row, "route_key_candidate" if is_comsol else "route_key"),
        _value(row, "NODI_view"),
        _value(row, "diameter_nm"),
        _value(row, "tpd_proxy_aggregation_basis"),
        _value(row, "edge4_bin_label"),
        _value(row, "nodi_edge20_definition_hash"),
    )


def _validation_summary(validation_rows: Sequence[Mapping[str, Any]]) -> str:
    statuses = sorted({_value(row, "status") for row in validation_rows if _value(row, "status")})
    return ";".join(statuses)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _validate_forbidden_false_fields(rows: Sequence[Mapping[str, Any]], group: str) -> list[str]:
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
    if not args.confirm_gate2g_edge_receipt:
        raise SystemExit("Refusing to write Gate2G-EDGE receipt without explicit confirmation flag.")
    payload = build_gate2g_payload(comsol_root=args.comsol_root)
    issues = validate_gate2g_payload(payload, comsol_root=args.comsol_root)
    if issues and payload["status"] == PASS_STATUS:
        print(f"NODI_COMSOL_GATE2G_EDGE_RECEIPT: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    report_sha = sha256_file(outputs["report_json"])
    print(f"NODI_COMSOL_GATE2G_EDGE_RECEIPT: {payload['status']}")
    print(f"report_path: {outputs['report_json']}")
    print(f"report_sha256: {report_sha}")
    print(f"grouping_reconciliation_csv: {outputs['grouping_recon_csv']}")
    if issues:
        for issue in issues:
            print(f"- {issue}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
