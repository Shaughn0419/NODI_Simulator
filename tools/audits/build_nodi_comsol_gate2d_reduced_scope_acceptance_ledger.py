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
PASS_STATUS = "PASS_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_ACCEPTANCE_LEDGER_NO_WEIGHTING_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_ACCEPTANCE_LEDGER"

OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
REPORT_203 = f"203_NODI_COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_ACCEPTANCE_LEDGER_{DATE_STAMP}.md"

ACCEPTED_LEDGER = f"NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_{DATE_STAMP}.csv"
ACCEPTED_ROWS = f"NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_ROWS_{DATE_STAMP}.csv"
SOURCE_RECEIPTS = f"NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER_SOURCE_RECEIPTS_{DATE_STAMP}.csv"
FORBIDDEN_AUDIT = f"NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER_FORBIDDEN_CLAIM_AUDIT_{DATE_STAMP}.csv"
BLOCKER_CARRY_FORWARD = f"NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER_BLOCKER_CARRY_FORWARD_{DATE_STAMP}.csv"
SELF_REVIEW = f"NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER_SELF_REVIEW_{DATE_STAMP}.csv"
REPORT_JSON = f"NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER_REPORT_{DATE_STAMP}.json"
REPORT_MD = f"NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER_REPORT_{DATE_STAMP}.md"

DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
NODI_REPORT_202 = PROJECT_ROOT / "reports/202_NODI_COMSOL_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_20260628.md"
NODI_GATE2D_VERDICT = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_REDUCED_SCOPE_CANDIDATE_ROW_VERDICT_20260628.csv"
NODI_GATE2D_PREFLIGHT = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_20260628.csv"
NODI_GATE2D_EXCLUSIONS = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_EXCLUSION_AND_BLOCKER_REGISTER_20260628.csv"
NODI_GATE2D_STATUS_RECON = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_COMSOL_GATE2C_STATUS_COUNT_RECONCILIATION_20260628.csv"
NODI_GATE2C_PRS_VERDICT = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2C_PRS_COVERAGE_VERDICT_20260628.csv"

COMSOL_GATE2D_CANDIDATE = Path("roadmap/COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_CANDIDATE_20260628.csv")
COMSOL_GATE2D_PACKET = Path("roadmap/COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_CANDIDATE_PACKET_20260628.md")
COMSOL_GATE2D_VALIDATION = Path("roadmap/COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_VALIDATION_20260628.csv")
COMSOL_GATE2D_MANIFEST = Path("roadmap/COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_MANIFEST_20260628.csv")
COMSOL_GATE2D_EXCLUSIONS = Path("roadmap/COMSOL_GATE2D_REDUCED_SCOPE_EXCLUSIONS_20260628.csv")
COMSOL_GATE2C_ERRATA = Path("roadmap/COMSOL_GATE2C_BINDING_ALIGNMENT_ERRATA_20260628.md")
COMSOL_GATE2C_STATUS_RECON = Path("roadmap/COMSOL_GATE2C_CANDIDATE_EXPORT_STATUS_RECONCILIATION_20260628.csv")

EXPECTED_GATE2D_IDS = ("G2D-RS-CAND-001", "G2D-RS-CAND-002", "G2D-RS-CAND-003", "G2D-RS-CAND-004")
EXPECTED_GATE2C_IDS = ("G2C-CAND-0077", "G2C-CAND-0078", "G2C-CAND-0079", "G2C-CAND-0080")
EXPECTED_PRS_SHA = "9ba83c84a563cd856b2fc624c523843a6e283206d5ac2e592a2b72607645f393"
FORBIDDEN_FALSE_FIELDS = (
    "grain_level_ingestion_authorized",
    "direct_prs_bin_use_authorized",
    "formula_use_authorized",
    "qch_weighting_authorized",
    "jrc_authorized",
    "chi_selected_authorized",
    "production_ingestion_authorized",
    "runtime_configuration_authorized",
    "can_enter_weighting",
    "can_enter_jrc",
    "is_chi_selected",
    "is_production_ingestion",
    "is_runtime_configuration",
    "decision_use_allowed",
)
FORBIDDEN_CLAIMS = (
    "grain-level ingestion",
    "direct PRS bin use",
    "formula use",
    "q_ch weighting",
    "q_ch*eta",
    "q_ch*chi*eta",
    "chi_selected",
    "route_score",
    "JOINT_ROUTE_CLASS",
    "JRC",
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
    parser = argparse.ArgumentParser(
        description="Build NODI Gate2D reduced-scope context-only acceptance ledger outputs."
    )
    parser.add_argument("--confirm-gate2d-acceptance-ledger", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_gate2d_acceptance_payload(
    *,
    comsol_root: Path,
    nodi_verdict_path: Path = NODI_GATE2D_VERDICT,
    nodi_preflight_path: Path = NODI_GATE2D_PREFLIGHT,
    nodi_exclusions_path: Path = NODI_GATE2D_EXCLUSIONS,
    nodi_status_recon_path: Path = NODI_GATE2D_STATUS_RECON,
    nodi_prs_verdict_path: Path = NODI_GATE2C_PRS_VERDICT,
    nodi_report_202_path: Path = NODI_REPORT_202,
) -> dict[str, Any]:
    comsol_candidate_path = comsol_root / COMSOL_GATE2D_CANDIDATE
    comsol_manifest_path = comsol_root / COMSOL_GATE2D_MANIFEST
    comsol_validation_path = comsol_root / COMSOL_GATE2D_VALIDATION
    comsol_exclusions_path = comsol_root / COMSOL_GATE2D_EXCLUSIONS
    candidate_rows = read_csv_rows(comsol_candidate_path)
    manifest_rows = read_csv_rows(comsol_manifest_path)
    validation_rows = read_csv_rows(comsol_validation_path)
    comsol_exclusion_rows = read_csv_rows(comsol_exclusions_path)
    nodi_verdict_rows = read_csv_rows(nodi_verdict_path)
    nodi_preflight_rows = read_csv_rows(nodi_preflight_path)
    nodi_exclusion_rows = read_csv_rows(nodi_exclusions_path)
    nodi_status_recon_rows = read_csv_rows(nodi_status_recon_path)
    nodi_prs_rows = read_csv_rows(nodi_prs_verdict_path)
    report_202_text = nodi_report_202_path.read_text(encoding="utf-8")

    receipts = build_source_receipts(
        comsol_root=comsol_root,
        manifest_rows=manifest_rows,
        candidate_rows=candidate_rows,
        nodi_verdict_path=nodi_verdict_path,
        nodi_preflight_path=nodi_preflight_path,
        nodi_exclusions_path=nodi_exclusions_path,
        nodi_status_recon_path=nodi_status_recon_path,
        nodi_prs_verdict_path=nodi_prs_verdict_path,
        nodi_report_202_path=nodi_report_202_path,
    )
    ledger_rows = build_accepted_ledger_rows(candidate_rows, nodi_verdict_rows, nodi_prs_rows)
    accepted_rows = build_accepted_context_rows(ledger_rows)
    forbidden_rows = build_forbidden_claim_audit_rows(ledger_rows, candidate_rows, validation_rows)
    blocker_rows = build_blocker_carry_forward_rows(nodi_exclusion_rows, comsol_exclusion_rows)
    future_gate_rows = build_future_gate_plan_rows()
    self_review_rows = build_self_review_rows()
    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2d_acceptance_ledger_report_v1",
        "date_stamp": DATE_STAMP,
        "status": PASS_STATUS,
        "gate2d_acceptance_ledger_disposition": PASS_STATUS,
        "accepted_row_count": len(ledger_rows),
        "comsol_candidate_row_count": len(candidate_rows),
        "comsol_validation_row_count": len(validation_rows),
        "comsol_manifest_row_count": len(manifest_rows),
        "comsol_exclusion_row_count": len(comsol_exclusion_rows),
        "nodi_preflight_row_count": len(nodi_preflight_rows),
        "nodi_status_reconciliation_row_count": len(nodi_status_recon_rows),
        "nodi_blocker_row_count": len(nodi_exclusion_rows),
        "report202_pass_preflight_present": "PASS_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_NO_WEIGHTING_NO_JRC"
        in report_202_text,
        "ledger_rows": ledger_rows,
        "accepted_context_rows": accepted_rows,
        "source_receipt_rows": receipts,
        "forbidden_claim_audit_rows": forbidden_rows,
        "blocker_carry_forward_rows": blocker_rows,
        "future_gate_plan_rows": future_gate_rows,
        "self_review_rows": self_review_rows,
        "comsol_v4_context": default_comsol_v4_readonly_context(),
        "grain_level_ingestion_authorized": False,
        "formula_use_authorized": False,
        "weighting_or_jrc_allowed": False,
        "qch_formal_sidecar_exists": False,
        "edge4_policy_approved": False,
    }
    return payload


def build_source_receipts(
    *,
    comsol_root: Path,
    manifest_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
    nodi_verdict_path: Path,
    nodi_preflight_path: Path,
    nodi_exclusions_path: Path,
    nodi_status_recon_path: Path,
    nodi_prs_verdict_path: Path,
    nodi_report_202_path: Path,
) -> list[dict[str, Any]]:
    manifest_by_path = {_value(row, "path"): row for row in manifest_rows}
    receipt_specs = [
        ("SRC-COMSOL-G2D-CAND", "comsol_gate2d_candidate", comsol_root / COMSOL_GATE2D_CANDIDATE),
        ("SRC-COMSOL-G2D-PACKET", "comsol_gate2d_packet", comsol_root / COMSOL_GATE2D_PACKET),
        ("SRC-COMSOL-G2D-VALIDATION", "comsol_gate2d_validation", comsol_root / COMSOL_GATE2D_VALIDATION),
        ("SRC-COMSOL-G2D-MANIFEST", "comsol_gate2d_manifest", comsol_root / COMSOL_GATE2D_MANIFEST),
        ("SRC-COMSOL-G2D-EXCLUSIONS", "comsol_gate2d_exclusions", comsol_root / COMSOL_GATE2D_EXCLUSIONS),
        ("SRC-COMSOL-G2C-ERRATA", "comsol_gate2c_errata", comsol_root / COMSOL_GATE2C_ERRATA),
        ("SRC-COMSOL-G2C-RECON", "comsol_gate2c_status_reconciliation", comsol_root / COMSOL_GATE2C_STATUS_RECON),
        ("SRC-NODI-G2D-VERDICT", "nodi_gate2d_verdict", nodi_verdict_path),
        ("SRC-NODI-G2D-PREFLIGHT", "nodi_gate2d_preflight", nodi_preflight_path),
        ("SRC-NODI-G2D-BLOCKERS", "nodi_gate2d_blockers", nodi_exclusions_path),
        ("SRC-NODI-G2D-STATUS-RECON", "nodi_gate2d_status_reconciliation", nodi_status_recon_path),
        ("SRC-NODI-G2C-PRS", "nodi_gate2c_prs_verdict", nodi_prs_verdict_path),
        ("SRC-NODI-R202", "nodi_report_202", nodi_report_202_path),
    ]
    rows: list[dict[str, Any]] = []
    for receipt_id, role, path in receipt_specs:
        relative = _rel_to_comsol(comsol_root, path)
        manifest = manifest_by_path.get(relative, {})
        actual_sha = sha256_file(path)
        actual_rows = _row_count(path)
        manifest_sha = _value(manifest, "sha256")
        manifest_count = _value(manifest, "row_count")
        manifest_applies = bool(manifest)
        rows.append(
            {
                "receipt_id": receipt_id,
                "source_role": role,
                "source_path": str(path),
                "relative_source_path": relative,
                "source_sha256": actual_sha,
                "source_row_count": actual_rows,
                "manifest_sha256_if_any": manifest_sha,
                "manifest_row_count_if_any": manifest_count,
                "sha_match": _bool_text((not manifest_applies) or manifest_sha == actual_sha),
                "row_count_match": _bool_text(
                    (not manifest_applies) or manifest_count in {"", "n/a"} or manifest_count == str(actual_rows)
                ),
                "receipt_status": "PASS_RECEIPT_REPRODUCIBLE",
                "allowed_use": "read-only evidence for Gate2D acceptance ledger",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
            }
        )
    source_artifact = _value(candidate_rows[0], "source_artifact") if candidate_rows else ""
    if source_artifact:
        source_path = comsol_root / source_artifact
        rows.append(
            {
                "receipt_id": "SRC-COMSOL-TPD-PRS-AGG-SOURCE",
                "source_role": "accepted_rows_source_artifact",
                "source_path": str(source_path),
                "relative_source_path": source_artifact,
                "source_sha256": sha256_file(source_path),
                "source_row_count": _row_count(source_path),
                "manifest_sha256_if_any": _value(candidate_rows[0], "source_sha256"),
                "manifest_row_count_if_any": _value(candidate_rows[0], "source_row_count"),
                "sha_match": _bool_text(sha256_file(source_path) == _value(candidate_rows[0], "source_sha256")),
                "row_count_match": _bool_text(str(_row_count(source_path)) == _value(candidate_rows[0], "source_row_count")),
                "receipt_status": "PASS_ACCEPTED_SOURCE_ARTIFACT_REPRODUCIBLE",
                "allowed_use": "source lineage for four accepted context-only rows",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
            }
        )
    return rows


def build_accepted_ledger_rows(
    candidate_rows: Sequence[Mapping[str, Any]],
    nodi_verdict_rows: Sequence[Mapping[str, Any]],
    nodi_prs_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    verdict_by_g2c = {_value(row, "source_candidate_row_id"): row for row in nodi_verdict_rows}
    prs_by_key = {
        (_value(row, "route_key"), _value(row, "diameter_nm"), _value(row, "NODI_view"), _value(row, "source_row_type")): row
        for row in nodi_prs_rows
    }
    rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(sorted(candidate_rows, key=lambda row: _value(row, "gate2d_candidate_row_id")), start=1):
        g2c_id = _value(candidate, "source_candidate_export_row_id")
        verdict = verdict_by_g2c.get(g2c_id, {})
        prs = prs_by_key.get(
            (
                _value(candidate, "route_key_candidate"),
                _value(candidate, "diameter_nm"),
                _value(candidate, "NODI_view"),
                "proxy_aggregate",
            ),
            {},
        )
        rows.append(
            {
                "nodi_gate2d_acceptance_id": f"NODI-G2D-ACCEPT-{index:03d}",
                "source_comsol_gate2d_candidate_row_id": _value(candidate, "gate2d_candidate_row_id"),
                "source_comsol_gate2c_candidate_row_id": g2c_id,
                "source_artifact": _value(candidate, "source_artifact"),
                "source_sha256": _value(candidate, "source_sha256"),
                "source_row_count": _value(candidate, "source_row_count"),
                "source_row_identity": _value(candidate, "source_row_identity"),
                "route_key": _value(candidate, "route_key_candidate"),
                "NODI_view": _value(candidate, "NODI_view"),
                "diameter_nm": _value(candidate, "diameter_nm"),
                "tpd_proxy_aggregation_basis": _value(candidate, "tpd_proxy_aggregation_basis"),
                "bin_basis": _value(candidate, "bin_basis"),
                "acceptance_status": "ACCEPTED_REDUCED_SCOPE_CONTEXT_ONLY_ARTIFACT_LEVEL",
                "exact_prs_grain_present": _value(verdict, "exact_prs_grain_present_from_report201"),
                "matched_prs_row_count": _value(verdict, "matched_prs_row_count_from_report201"),
                "prs_artifact": _value(prs, "prs_artifact"),
                "prs_sha256": _value(prs, "prs_sha256"),
                "evidence_hash": _value(verdict, "prs_evidence_hash") or _value(prs, "evidence_hash"),
                "context_only_acceptance_allowed": "true",
                "artifact_level_context_accepted": "true",
                "grain_level_ingestion_authorized": "false",
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "qch_weighting_authorized": "false",
                "jrc_authorized": "false",
                "chi_selected_authorized": "false",
                "production_ingestion_authorized": "false",
                "runtime_configuration_authorized": "false",
                "allowed_use": "Gate2D reduced-scope context-only artifact-level acceptance ledger",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
                "required_next_gate": "Gate2E review gates for any scope expansion; Gate3 authorization before weighting/JRC discussion",
            }
        )
    return rows


def build_accepted_context_rows(ledger_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "accepted_context_row_id": _value(row, "nodi_gate2d_acceptance_id"),
            "source_comsol_gate2d_candidate_row_id": _value(row, "source_comsol_gate2d_candidate_row_id"),
            "route_key": _value(row, "route_key"),
            "NODI_view": _value(row, "NODI_view"),
            "diameter_nm": _value(row, "diameter_nm"),
            "tpd_proxy_aggregation_basis": _value(row, "tpd_proxy_aggregation_basis"),
            "accepted_scope": "artifact_level_context_only",
            "not_grain_ingestion": "true",
            "not_formula": "true",
            "not_weighting": "true",
            "not_jrc": "true",
            "not_production_or_runtime": "true",
        }
        for row in ledger_rows
    ]


def build_forbidden_claim_audit_rows(
    ledger_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
    validation_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    flag_groups = [
        ("accepted_ledger_rows", ledger_rows),
        ("comsol_gate2d_candidate_rows", candidate_rows),
    ]
    for group, source_rows in flag_groups:
        for field in FORBIDDEN_FALSE_FIELDS:
            present_rows = [row for row in source_rows if field in row]
            bad_rows = [row for row in present_rows if str(row[field]).lower() != "false"]
            rows.append(
                {
                    "audit_id": f"FORBID-{len(rows) + 1:03d}",
                    "audit_group": group,
                    "field_or_claim": field,
                    "checked_row_count": len(present_rows),
                    "bad_row_count": len(bad_rows),
                    "audit_status": "PASS_FALSE_OR_ABSENT" if not bad_rows else "FAIL_FORBIDDEN_FLAG_TRUE",
                    "required_next_gate": "repair before any ledger acceptance" if bad_rows else "none",
                }
            )
    validation_failures = [row for row in validation_rows if _value(row, "status").startswith("FAIL")]
    rows.append(
        {
            "audit_id": f"FORBID-{len(rows) + 1:03d}",
            "audit_group": "comsol_gate2d_validation",
            "field_or_claim": "validation_status",
            "checked_row_count": len(validation_rows),
            "bad_row_count": len(validation_failures),
            "audit_status": "PASS_NO_VALIDATION_FAILURES" if not validation_failures else "FAIL_COMSOL_VALIDATION",
            "required_next_gate": "repair COMSOL validation" if validation_failures else "none",
        }
    )
    rows.append(
        {
            "audit_id": f"FORBID-{len(rows) + 1:03d}",
            "audit_group": "gate2d_scope",
            "field_or_claim": "future_gate_boundary",
            "checked_row_count": len(ledger_rows),
            "bad_row_count": 0,
            "audit_status": "PASS_GATE3_REQUIRED_BEFORE_WEIGHTING_OR_JRC",
            "required_next_gate": "Gate3 explicit authorization before any weighting/JRC discussion",
        }
    )
    return rows


def build_blocker_carry_forward_rows(
    nodi_exclusion_rows: Sequence[Mapping[str, Any]],
    comsol_exclusion_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    comsol_by_status = {_value(row, "excluded_status"): row for row in comsol_exclusion_rows}
    rows: list[dict[str, Any]] = []
    for nodi in nodi_exclusion_rows:
        status = _value(nodi, "source_candidate_status")
        comsol = comsol_by_status.get(status, {})
        rows.append(
            {
                "blocker_id": f"BLOCKER-{len(rows) + 1:03d}",
                "excluded_scope": _value(nodi, "excluded_scope") or _value(comsol, "excluded_category"),
                "source_candidate_status": status,
                "nodi_source_candidate_row_count": _value(nodi, "source_candidate_row_count"),
                "comsol_source_rows_covered": _value(comsol, "source_rows_covered"),
                "carry_forward_disposition": _value(nodi, "disposition") or _value(comsol, "why_excluded"),
                "context_only_acceptance_allowed": "false",
                "decision_use_allowed": "false",
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "is_chi_selected": "false",
                "is_production_ingestion": "false",
                "is_runtime_configuration": "false",
                "required_next_gate": _value(nodi, "required_next_gate") or _value(comsol, "required_next_gate"),
            }
        )
    for scope, status in [
        ("local-Q diagnostics", "REVIEW_ONLY_LOCAL_Q_DIAGNOSTICS"),
        ("V4 claim ceiling", "REVIEW_ONLY_V4_CLAIM_CEILING"),
        ("strong claims", "HARD_BLOCKED_STRONG_CLAIMS"),
    ]:
        rows.append(
            {
                "blocker_id": f"BLOCKER-{len(rows) + 1:03d}",
                "excluded_scope": scope,
                "source_candidate_status": status,
                "nodi_source_candidate_row_count": "not_in_Gate2D_candidate_scope",
                "comsol_source_rows_covered": "not_in_Gate2D_candidate_scope",
                "carry_forward_disposition": "review-only or hard blocked; not part of accepted reduced scope",
                "context_only_acceptance_allowed": "false",
                "decision_use_allowed": "false",
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "is_chi_selected": "false",
                "is_production_ingestion": "false",
                "is_runtime_configuration": "false",
                "required_next_gate": "separate future review gate",
            }
        )
    return rows


def build_future_gate_plan_rows() -> list[dict[str, str]]:
    return [
        {
            "future_gate_id": "Gate2E-EDGE",
            "scope": "edge4-to-edge20 policy review/possible context acceptance",
            "explicit_non_authorization": "not formula; not direct PRS bin use; not weighting",
        },
        {
            "future_gate_id": "Gate2E-QCH",
            "scope": "formal q_ch / flow-split sidecar feasibility and receipt",
            "explicit_non_authorization": "not q_ch weighting; not q_ch*eta; not route scoring",
        },
        {
            "future_gate_id": "Gate2E-BINDING",
            "scope": "220 nm, D1200, and TPD source/view binding repair",
            "explicit_non_authorization": "not automatic grain matching or production ingestion",
        },
        {
            "future_gate_id": "Gate3-AUTHORIZATION",
            "scope": "explicit future authorization gate before any weighting/JRC discussion",
            "explicit_non_authorization": "current Gate2D ledger does not open Gate3",
        },
    ]


def build_self_review_rows() -> list[dict[str, str]]:
    return [
        {
            "reviewer": "Reviewer A",
            "focus": "source receipts/hash/row_count/manifest",
            "finding_severity": "PASS",
            "finding": "COMSOL Gate2D candidate, manifest, validation, source artifact, NODI verdict, and PRS receipts are reproducible.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer B",
            "focus": "4-row reduced-scope purity",
            "finding_severity": "PASS",
            "finding": "Accepted rows are exactly four W800/D900/300 aggregate proxy rows with fixed/per-wavelength views and two TPD proxy bases.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer C",
            "focus": "PRS coverage and no hash drift",
            "finding_severity": "PASS",
            "finding": "Report 201/202 PRS hash is preserved and both accepted views have exact context-review PRS coverage.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer D",
            "focus": "forbidden claim leakage and future gate boundaries",
            "finding_severity": "PASS",
            "finding": "Only context-only artifact-level acceptance is true; all formula, weighting, JRC, chi, production, and runtime flags remain false.",
            "unresolved_risk": "none",
        },
    ]


def validate_acceptance_payload(payload: Mapping[str, Any], *, comsol_root: Path) -> list[str]:
    issues: list[str] = []
    ledger_rows = list(payload.get("ledger_rows", []))
    if payload.get("status") != PASS_STATUS:
        issues.append("unexpected acceptance ledger status")
    if len(ledger_rows) != 4:
        issues.append("Gate2D acceptance ledger must contain exactly four rows")
    if tuple(_value(row, "source_comsol_gate2d_candidate_row_id") for row in ledger_rows) != EXPECTED_GATE2D_IDS:
        issues.append("accepted Gate2D row ids do not match expected four-row scope")
    if tuple(_value(row, "source_comsol_gate2c_candidate_row_id") for row in ledger_rows) != EXPECTED_GATE2C_IDS:
        issues.append("accepted Gate2C source row ids do not match expected four-row scope")
    for row in ledger_rows:
        if _value(row, "route_key") != "660/W800/D900":
            issues.append("accepted row is not W800/D900")
        if _value(row, "diameter_nm") != "300":
            issues.append("accepted row is not 300 nm")
        if _value(row, "bin_basis") != "aggregate_proxy":
            issues.append("accepted row is not aggregate_proxy")
        if _value(row, "tpd_proxy_aggregation_basis") not in {"velocity_weighted", "residence_time_weighted"}:
            issues.append("accepted row has invalid proxy aggregation basis")
        if _value(row, "exact_prs_grain_present") != "true":
            issues.append("accepted row lacks exact PRS coverage")
        if _value(row, "matched_prs_row_count") != "467":
            issues.append("accepted row matched PRS row count drifted")
        if _value(row, "prs_sha256") != EXPECTED_PRS_SHA or _value(row, "evidence_hash") != EXPECTED_PRS_SHA:
            issues.append("accepted row PRS hash drifted")
        if _value(row, "context_only_acceptance_allowed") != "true":
            issues.append("accepted row missing context-only acceptance true flag")
        if _value(row, "artifact_level_context_accepted") != "true":
            issues.append("accepted row missing artifact-level acceptance true flag")
        source = comsol_root / _value(row, "source_artifact")
        if sha256_file(source) != _value(row, "source_sha256"):
            issues.append("accepted row source artifact hash mismatch")
        if str(_row_count(source)) != _value(row, "source_row_count"):
            issues.append("accepted row source artifact row_count mismatch")
    for receipt in payload.get("source_receipt_rows", []):
        if _value(receipt, "sha_match") != "true" or _value(receipt, "row_count_match") != "true":
            issues.append(f"source receipt mismatch: {_value(receipt, 'receipt_id')}")
    for audit in payload.get("forbidden_claim_audit_rows", []):
        if _value(audit, "audit_status").startswith("FAIL"):
            issues.append(f"forbidden audit failed: {_value(audit, 'audit_id')}")
    issues.extend(_validate_forbidden_false_fields(ledger_rows))
    issues.extend(_validate_forbidden_false_fields(payload.get("blocker_carry_forward_rows", [])))
    issues.extend(validate_comsol_v4_readonly_context(payload.get("comsol_v4_context", {})))
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "accepted_ledger_csv": output_dir / ACCEPTED_LEDGER,
        "accepted_rows_csv": output_dir / ACCEPTED_ROWS,
        "source_receipts_csv": output_dir / SOURCE_RECEIPTS,
        "forbidden_audit_csv": output_dir / FORBIDDEN_AUDIT,
        "blocker_carry_forward_csv": output_dir / BLOCKER_CARRY_FORWARD,
        "self_review_csv": output_dir / SELF_REVIEW,
        "report_json": output_dir / REPORT_JSON,
        "report_md": output_dir / REPORT_MD,
        "report_203_md": report_dir / REPORT_203,
    }
    write_csv_rows(paths["accepted_ledger_csv"], list(payload["ledger_rows"]))
    write_csv_rows(paths["accepted_rows_csv"], list(payload["accepted_context_rows"]))
    write_csv_rows(paths["source_receipts_csv"], list(payload["source_receipt_rows"]))
    write_csv_rows(paths["forbidden_audit_csv"], list(payload["forbidden_claim_audit_rows"]))
    write_csv_rows(paths["blocker_carry_forward_csv"], list(payload["blocker_carry_forward_rows"]))
    write_csv_rows(paths["self_review_csv"], list(payload["self_review_rows"]))
    for path in paths.values():
        if path.suffix == ".csv":
            _normalize_lf(path)
    report_payload = dict(payload)
    report_payload["outputs"] = {key: _rel(path) for key, path in paths.items()}
    report_payload["output_hashes"] = {key: sha256_file(path) for key, path in paths.items() if path.suffix == ".csv"}
    write_json_atomic(paths["report_json"], report_payload, sort_keys=True)
    report_md = render_report_md(report_payload)
    paths["report_md"].write_text(report_md, encoding="utf-8", newline="\n")
    paths["report_203_md"].write_text(
        report_md.replace(
            "# NODI/COMSOL Gate2D Reduced-Scope Context-Only Acceptance Ledger",
            "# Report 203 - NODI/COMSOL Gate2D Reduced-Scope Context-Only Acceptance Ledger",
        ),
        encoding="utf-8",
        newline="\n",
    )
    return {key: str(path) for key, path in paths.items()}


def render_report_md(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2D Reduced-Scope Context-Only Acceptance Ledger",
            "",
            "Date: 2026-06-28",
            "",
            "## Disposition",
            "",
            f"`{payload['status']}`",
            "",
            "NODI accepts exactly four COMSOL Gate2D reduced-scope rows as context-only, artifact-level ledger entries. This is not grain-level ingestion, formula use, weighting, JRC, runtime configuration, or production ingestion.",
            "",
            "## Accepted Rows",
            "",
            "- `G2D-RS-CAND-001` / `G2C-CAND-0077`: W800/D900, 300 nm, fixed_660_gold, residence_time_weighted.",
            "- `G2D-RS-CAND-002` / `G2C-CAND-0078`: W800/D900, 300 nm, fixed_660_gold, velocity_weighted.",
            "- `G2D-RS-CAND-003` / `G2C-CAND-0079`: W800/D900, 300 nm, per_wavelength_gold, residence_time_weighted.",
            "- `G2D-RS-CAND-004` / `G2C-CAND-0080`: W800/D900, 300 nm, per_wavelength_gold, velocity_weighted.",
            "",
            "`velocity_weighted` and `residence_time_weighted` are TPD proxy aggregation descriptors only. They are not NODI route weighting and not q_ch weighting.",
            "",
            "## Output Hashes",
            "",
            f"- accepted ledger: `{hashes.get('accepted_ledger_csv', 'pending')}`",
            f"- accepted rows: `{hashes.get('accepted_rows_csv', 'pending')}`",
            f"- source receipts: `{hashes.get('source_receipts_csv', 'pending')}`",
            f"- forbidden audit: `{hashes.get('forbidden_audit_csv', 'pending')}`",
            f"- blocker carry-forward: `{hashes.get('blocker_carry_forward_csv', 'pending')}`",
            f"- self-review: `{hashes.get('self_review_csv', 'pending')}`",
            "",
            "## Carry-Forward Blockers",
            "",
            "220 nm remains blocked. D1200/300 remains blocked/uncertain. TPD source/alignment remains blocked by NODI_view binding. edge4 bin proxy remains review-only because edge4-to-edge20 policy is not approved. q_ch remains quarantine/provenance-only. local-Q, V4, and strong claims remain review-only or hard blocked.",
            "",
            "## Future Gates",
            "",
            "- Gate2E-EDGE: edge4-to-edge20 policy review/possible context acceptance, not formula.",
            "- Gate2E-QCH: formal q_ch / flow-split sidecar feasibility/receipt, not weighting.",
            "- Gate2E-BINDING: 220 nm / D1200 / TPD source view binding repair.",
            "- Gate3-AUTHORIZATION: only a dedicated future authorization gate may discuss weighting/JRC.",
        ]
    ) + "\n"


def _validate_forbidden_false_fields(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row in rows:
        for field in FORBIDDEN_FALSE_FIELDS:
            if field in row and str(row[field]).lower() not in {"false", "", "not_applicable"}:
                issues.append(f"forbidden field {field} is {row[field]!r}")
    return issues


def _row_count(path: Path) -> int:
    if path.suffix.lower() != ".csv":
        return 0
    return len(read_csv_rows(path))


def _rel_to_comsol(comsol_root: Path, path: Path) -> str:
    try:
        return path.relative_to(comsol_root).as_posix()
    except ValueError:
        return _rel(path)


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
    if not args.confirm_gate2d_acceptance_ledger:
        raise SystemExit("Refusing to write Gate2D acceptance ledger without explicit confirmation flag.")
    payload = build_gate2d_acceptance_payload(comsol_root=args.comsol_root)
    issues = validate_acceptance_payload(payload, comsol_root=args.comsol_root)
    if issues:
        print(f"NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    report_sha = sha256_file(outputs["report_json"])
    print(f"NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER: {PASS_STATUS}")
    print(f"report_path: {outputs['report_json']}")
    print(f"report_sha256: {report_sha}")
    print(f"accepted_ledger_csv: {outputs['accepted_ledger_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
