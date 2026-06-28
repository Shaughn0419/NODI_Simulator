#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


DATE_STAMP = "20260628"
PARTIAL_STATUS = "PARTIAL_PENDING_COMSOL_GATE2C_ERRATA_NO_WEIGHTING_NO_JRC"
PASS_STATUS = "PASS_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_NO_WEIGHTING_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT"

OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
REPORT_202 = f"202_NODI_COMSOL_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_{DATE_STAMP}.md"

CONSISTENCY_AUDIT = f"NODI_COMSOL_GATE2D_COMSOL_GATE2C_PACKAGE_CONSISTENCY_AUDIT_{DATE_STAMP}.csv"
STATUS_RECONCILIATION = f"NODI_COMSOL_GATE2D_COMSOL_GATE2C_STATUS_COUNT_RECONCILIATION_{DATE_STAMP}.csv"
REDUCED_SCOPE_VERDICT = f"NODI_COMSOL_GATE2D_REDUCED_SCOPE_CANDIDATE_ROW_VERDICT_{DATE_STAMP}.csv"
ACCEPTANCE_PREFLIGHT = f"NODI_COMSOL_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_{DATE_STAMP}.csv"
EXCLUSION_REGISTER = f"NODI_COMSOL_GATE2D_EXCLUSION_AND_BLOCKER_REGISTER_{DATE_STAMP}.csv"
SELF_REVIEW = f"NODI_COMSOL_GATE2D_SELF_REVIEW_FINDINGS_{DATE_STAMP}.csv"
REPORT_JSON = f"NODI_COMSOL_GATE2D_ACCEPTANCE_PREFLIGHT_REPORT_{DATE_STAMP}.json"
REPORT_MD = f"NODI_COMSOL_GATE2D_ACCEPTANCE_PREFLIGHT_REPORT_{DATE_STAMP}.md"

DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
NODI_REPORT_201 = PROJECT_ROOT / "reports/201_NODI_COMSOL_GATE2C_REQUIREMENT_REVIEW_AND_EVIDENCE_STABILIZATION_20260628.md"
NODI_GATE2C_ACCEPTANCE = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2C_ACCEPTANCE_CHECKLIST_20260628.csv"
NODI_GATE2C_PRS_VERDICT = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2C_PRS_COVERAGE_VERDICT_20260628.csv"
NODI_GATE2C_ALLOWED_ACCEPTANCE = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2C_ALLOWED_SUPPORT_ROW_ACCEPTANCE_20260628.csv"
NODI_GATE2C_PARENT_CHILD = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2C_LEDGER_SUPPORT_PARENT_CHILD_MAP_20260628.csv"

COMSOL_FILES = {
    "master_packet": Path("roadmap/COMSOL_GATE2C_BINDING_ALIGNMENT_MASTER_PACKET_20260628.md"),
    "candidate_export": Path("roadmap/COMSOL_GATE2C_NODI_BOUND_CONTEXT_EXPORT_CANDIDATE_20260628.csv"),
    "validation": Path("roadmap/COMSOL_GATE2C_BINDING_ALIGNMENT_VALIDATION_20260628.csv"),
    "reduced_scope_decision": Path("roadmap/COMSOL_GATE2C_REDUCED_SCOPE_DECISION_TABLE_20260628.csv"),
    "schema_alignment": Path("roadmap/COMSOL_GATE2C_TPD_BINDING_SCHEMA_ALIGNMENT_20260628.csv"),
    "manifest": Path("roadmap/COMSOL_GATE2C_BINDING_ALIGNMENT_MANIFEST_20260628.csv"),
}
OPTIONAL_COMSOL_FILES = {
    "errata": Path("roadmap/COMSOL_GATE2C_BINDING_ALIGNMENT_ERRATA_20260628.md"),
    "status_reconciliation": Path("roadmap/COMSOL_GATE2C_CANDIDATE_EXPORT_STATUS_RECONCILIATION_20260628.csv"),
    "gate2d_candidate": Path("roadmap/COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_CANDIDATE_20260628.csv"),
    "gate2d_validation": Path("roadmap/COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_VALIDATION_20260628.csv"),
    "gate2d_manifest": Path("roadmap/COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_MANIFEST_20260628.csv"),
}
EXPECTED_ACTUAL_COUNTS = {
    "BLOCKED_220NM_NO_DIRECT_MATCH": 72,
    "BLOCKED_D1200_EXACT_GRAIN_UNCERTAIN": 36,
    "BLOCKED_UNBOUND_NODI_VIEW": 16,
    "CANDIDATE_FOR_NODI_REVIEW_NOT_ACCEPTED": 4,
    "REVIEW_ONLY_EDGE_POLICY_REQUIRED": 16,
    "QUARANTINE_QCH_PROVENANCE_ONLY": 1,
}
FORBIDDEN_FLAG_FIELDS = (
    "grain_level_ingestion_authorized",
    "qch_weighting_authorized",
    "jrc_authorized",
    "chi_selected_authorized",
    "production_ingestion_authorized",
    "runtime_configuration_authorized",
    "decision_use_allowed",
    "can_enter_weighting",
    "can_enter_jrc",
    "is_chi_selected",
    "is_production_ingestion",
    "is_runtime_configuration",
    "is_formal_gate2_qch_sidecar",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build NODI Gate2D reduced-scope acceptance preflight outputs."
    )
    parser.add_argument("--confirm-gate2d-acceptance-preflight", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_gate2d_payload(
    *,
    comsol_root: Path,
    output_dir: Path,
    nodi_prs_verdict_path: Path = NODI_GATE2C_PRS_VERDICT,
    nodi_acceptance_path: Path = NODI_GATE2C_ACCEPTANCE,
    nodi_allowed_acceptance_path: Path = NODI_GATE2C_ALLOWED_ACCEPTANCE,
    nodi_parent_child_path: Path = NODI_GATE2C_PARENT_CHILD,
    nodi_report_201_path: Path = NODI_REPORT_201,
) -> dict[str, Any]:
    paths = {name: comsol_root / rel for name, rel in COMSOL_FILES.items()}
    optional_paths = {name: comsol_root / rel for name, rel in OPTIONAL_COMSOL_FILES.items()}
    candidate_rows = read_csv_rows(paths["candidate_export"])
    validation_rows = read_csv_rows(paths["validation"])
    decision_rows = read_csv_rows(paths["reduced_scope_decision"])
    schema_rows = read_csv_rows(paths["schema_alignment"])
    manifest_rows = read_csv_rows(paths["manifest"])
    prs_rows = read_csv_rows(nodi_prs_verdict_path)
    nodi_acceptance_rows = read_csv_rows(nodi_acceptance_path)
    nodi_allowed_rows = read_csv_rows(nodi_allowed_acceptance_path)
    nodi_parent_child_rows = read_csv_rows(nodi_parent_child_path)
    report_201_text = nodi_report_201_path.read_text(encoding="utf-8")

    errata_exists = optional_paths["errata"].exists()
    optional_status_rows = _read_optional_csv(optional_paths["status_reconciliation"])
    optional_gate2d_candidate_rows = _read_optional_csv(optional_paths["gate2d_candidate"])
    optional_gate2d_validation_rows = _read_optional_csv(optional_paths["gate2d_validation"])
    optional_gate2d_manifest_rows = _read_optional_csv(optional_paths["gate2d_manifest"])
    optional_existing = {
        name: str(path)
        for name, path in optional_paths.items()
        if path.exists()
    }
    master_counts = parse_master_candidate_counts(paths["master_packet"].read_text(encoding="utf-8"))
    actual_counts = Counter(_value(row, "candidate_status") for row in candidate_rows)
    validation_counts = parse_validation_candidate_counts(validation_rows)
    status_rows = build_status_reconciliation_rows(master_counts, actual_counts, validation_counts)
    manifest_audit_rows = build_manifest_audit_rows(comsol_root, manifest_rows)
    optional_audit_rows = build_optional_file_audit_rows(optional_paths)
    consistency_rows = build_consistency_rows(
        status_rows=status_rows,
        manifest_audit_rows=manifest_audit_rows,
        errata_exists=errata_exists,
        optional_existing=optional_existing,
        optional_audit_rows=optional_audit_rows,
    )
    reduced_rows = identify_reduced_scope_candidates(candidate_rows)
    verdict_rows = build_reduced_scope_verdict_rows(reduced_rows, prs_rows, errata_exists)
    optional_semantic_audit_rows = build_optional_semantic_audit_rows(
        optional_status_rows=optional_status_rows,
        optional_gate2d_candidate_rows=optional_gate2d_candidate_rows,
        optional_gate2d_validation_rows=optional_gate2d_validation_rows,
        optional_gate2d_manifest_rows=optional_gate2d_manifest_rows,
        verdict_rows=verdict_rows,
    )
    consistency_rows.extend(optional_semantic_audit_rows)
    preflight_rows = build_acceptance_preflight_rows(verdict_rows, errata_exists)
    exclusion_rows = build_exclusion_rows(candidate_rows)
    count_consistent = all(_value(row, "count_match") == "true" for row in status_rows)
    manifest_consistent = all(_value(row, "audit_status").startswith("PASS") for row in manifest_audit_rows)
    self_review_rows = build_self_review_rows(errata_exists, count_consistent)
    status = PASS_STATUS if count_consistent and manifest_consistent and errata_exists else PARTIAL_STATUS

    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2d_acceptance_preflight_report_v1",
        "date_stamp": DATE_STAMP,
        "status": status,
        "gate2d_disposition": status,
        "comsol_gate2c_count_consistent": count_consistent,
        "comsol_manifest_consistent": manifest_consistent,
        "comsol_errata_exists": errata_exists,
        "optional_comsol_files_found": optional_existing,
        "candidate_export_row_count": len(candidate_rows),
        "validation_row_count": len(validation_rows),
        "reduced_scope_decision_row_count": len(decision_rows),
        "schema_alignment_row_count": len(schema_rows),
        "manifest_row_count": len(manifest_rows),
        "comsol_gate2c_status_reconciliation_row_count": len(optional_status_rows),
        "comsol_gate2d_candidate_row_count": len(optional_gate2d_candidate_rows),
        "comsol_gate2d_validation_row_count": len(optional_gate2d_validation_rows),
        "comsol_gate2d_manifest_row_count": len(optional_gate2d_manifest_rows),
        "nodi_gate2c_acceptance_row_count": len(nodi_acceptance_rows),
        "nodi_gate2c_allowed_acceptance_row_count": len(nodi_allowed_rows),
        "nodi_gate2c_parent_child_row_count": len(nodi_parent_child_rows),
        "report201_pass_gate2c_present": "PASS_GATE2C_REQUIREMENT_REVIEW_EVIDENCE_STABILIZED_NO_WEIGHTING_NO_JRC"
        in report_201_text,
        "actual_candidate_status_counts": dict(actual_counts),
        "master_candidate_status_counts": dict(master_counts),
        "validation_candidate_status_counts": dict(validation_counts),
        "status_reconciliation_rows": status_rows,
        "manifest_audit_rows": manifest_audit_rows,
        "optional_file_audit_rows": optional_audit_rows,
        "optional_semantic_audit_rows": optional_semantic_audit_rows,
        "comsol_gate2d_candidate_rows": optional_gate2d_candidate_rows,
        "comsol_gate2d_validation_rows": optional_gate2d_validation_rows,
        "comsol_gate2d_manifest_rows": optional_gate2d_manifest_rows,
        "comsol_gate2c_status_reconciliation_rows": optional_status_rows,
        "consistency_audit_rows": consistency_rows,
        "reduced_scope_candidate_rows": verdict_rows,
        "acceptance_preflight_rows": preflight_rows,
        "exclusion_rows": exclusion_rows,
        "self_review_rows": self_review_rows,
        "edge4_policy_approved": False,
        "qch_formal_sidecar_exists": False,
        "weighting_or_jrc_allowed": False,
    }
    return payload


def parse_master_candidate_counts(master_text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    in_section = False
    for line in master_text.splitlines():
        if line.startswith("## NODI-Bound Export Candidate Summary"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        match = re.match(r"- `([^`]+)`: (\d+)", line.strip())
        if match:
            counts[match.group(1)] = int(match.group(2))
    return counts


def parse_validation_candidate_counts(validation_rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    for row in validation_rows:
        if _value(row, "check_name") == "candidate_export_status_coverage":
            observed = _value(row, "observed")
            try:
                parsed = ast.literal_eval(observed)
            except (SyntaxError, ValueError):
                return Counter()
            return Counter({str(key): int(value) for key, value in parsed.items()})
    return Counter()


def build_status_reconciliation_rows(
    master_counts: Counter[str],
    actual_counts: Counter[str],
    validation_counts: Counter[str],
) -> list[dict[str, Any]]:
    statuses = sorted(set(master_counts) | set(actual_counts) | set(validation_counts) | set(EXPECTED_ACTUAL_COUNTS))
    rows: list[dict[str, Any]] = []
    for status in statuses:
        actual = actual_counts.get(status, 0)
        master = master_counts.get(status, 0)
        validation = validation_counts.get(status, 0)
        rows.append(
            {
                "candidate_status": status,
                "master_packet_count": master,
                "candidate_csv_count": actual,
                "validation_observed_count": validation,
                "expected_actual_count_from_total_control": EXPECTED_ACTUAL_COUNTS.get(status, ""),
                "master_vs_csv_match": _bool_text(master == actual),
                "csv_vs_validation_match": _bool_text(actual == validation),
                "count_match": _bool_text(master == actual and actual == validation),
                "reconciliation_status": "PASS_COUNTS_MATCH"
                if master == actual and actual == validation
                else "FAIL_MASTER_PACKET_COUNT_DRIFT_REQUIRES_COMSOL_ERRATA",
                "required_next_gate": "COMSOL_GATE2C_ERRATA_OR_CORRECTED_MASTER_PACKET"
                if master != actual
                else "NODI_GATE2D_PREFLIGHT_REVIEW",
            }
        )
    return rows


def build_manifest_audit_rows(comsol_root: Path, manifest_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in manifest_rows:
        manifest_path = _value(row, "path")
        source = Path(manifest_path)
        if not source.is_absolute():
            source = comsol_root / source
        exists = source.exists()
        actual_sha = sha256_file(source) if exists else ""
        actual_rows = _row_count(source) if exists else ""
        manifest_sha = _value(row, "sha256")
        manifest_count = _value(row, "row_count")
        row_count_match = str(actual_rows) == manifest_count if exists and manifest_count not in {"", "n/a"} else exists
        sha_match = actual_sha == manifest_sha if manifest_sha else exists
        rows.append(
            {
                "audit_id": f"MANIFEST-{len(rows) + 1:03d}",
                "package_id": _value(row, "package_id"),
                "manifest_role": _value(row, "manifest_role"),
                "path": manifest_path,
                "source_exists": _bool_text(exists),
                "manifest_row_count": manifest_count,
                "actual_row_count": actual_rows,
                "row_count_match": _bool_text(bool(row_count_match)),
                "manifest_sha256": manifest_sha,
                "actual_sha256": actual_sha,
                "sha_match": _bool_text(bool(sha_match)),
                "audit_status": "PASS_MANIFEST_ROW_REPRODUCIBLE"
                if exists and row_count_match and sha_match
                else "FAIL_MANIFEST_DRIFT_OR_MISSING_PATH",
            }
        )
    return rows


def build_optional_file_audit_rows(optional_paths: Mapping[str, Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, path in optional_paths.items():
        exists = path.exists()
        rows.append(
            {
                "audit_id": f"G2D-OPTIONAL-{len(rows) + 1:03d}",
                "audit_item": f"optional_comsol_file_{name}",
                "audit_status": "PASS_OPTIONAL_FILE_PRESENT" if exists else "INFO_OPTIONAL_FILE_NOT_FOUND",
                "path": str(path),
                "row_count": _row_count(path) if exists else "",
                "sha256": sha256_file(path) if exists else "",
                "required_next_gate": "NODI_GATE2D_PREFLIGHT_REVIEW" if exists else "COMSOL_MAY_PROVIDE_IF_APPLICABLE",
            }
        )
    return rows


def build_consistency_rows(
    *,
    status_rows: Sequence[Mapping[str, Any]],
    manifest_audit_rows: Sequence[Mapping[str, Any]],
    errata_exists: bool,
    optional_existing: Mapping[str, str],
    optional_audit_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        {
            "audit_id": "G2D-CONSISTENCY-001",
            "audit_item": "master_packet_narrative_counts_vs_candidate_csv",
            "audit_status": "FAIL_REQUIRES_COMSOL_ERRATA"
            if any(_value(row, "master_vs_csv_match") != "true" for row in status_rows)
            else "PASS",
            "evidence": "status reconciliation matrix",
            "required_next_gate": "COMSOL_GATE2C_ERRATA_OR_CORRECTED_MASTER_PACKET",
        },
        {
            "audit_id": "G2D-CONSISTENCY-002",
            "audit_item": "candidate_csv_counts_vs_validation_observed_counts",
            "audit_status": "PASS"
            if all(_value(row, "csv_vs_validation_match") == "true" for row in status_rows)
            else "FAIL_VALIDATION_COUNT_DRIFT",
            "evidence": "COMSOL validation observed status counts",
            "required_next_gate": "NODI_GATE2D_PREFLIGHT_REVIEW",
        },
        {
            "audit_id": "G2D-CONSISTENCY-003",
            "audit_item": "manifest_sha_row_count_reproducibility",
            "audit_status": "PASS"
            if all(_value(row, "audit_status").startswith("PASS") for row in manifest_audit_rows)
            else "FAIL_MANIFEST_DRIFT",
            "evidence": f"{len(manifest_audit_rows)} manifest rows audited",
            "required_next_gate": "NODI_GATE2D_PREFLIGHT_REVIEW",
        },
        {
            "audit_id": "G2D-CONSISTENCY-004",
            "audit_item": "comsol_errata_or_reduced_scope_package_presence",
            "audit_status": "PASS_ERRATA_PRESENT" if errata_exists else "PARTIAL_NO_COMSOL_GATE2C_ERRATA_FOUND",
            "evidence": ";".join(f"{key}={value}" for key, value in optional_existing.items()) or "no optional errata/Gate2D package files found",
            "required_next_gate": "COMSOL_GATE2C_ERRATA_OR_GATE2D_REDUCED_SCOPE_EXPORT_PACKAGE",
        },
    ]
    rows.extend(dict(row) for row in optional_audit_rows)
    return rows


def build_optional_semantic_audit_rows(
    *,
    optional_status_rows: Sequence[Mapping[str, Any]],
    optional_gate2d_candidate_rows: Sequence[Mapping[str, Any]],
    optional_gate2d_validation_rows: Sequence[Mapping[str, Any]],
    optional_gate2d_manifest_rows: Sequence[Mapping[str, Any]],
    verdict_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    verdict_ids = {_value(row, "source_candidate_row_id") for row in verdict_rows}
    gate2d_ids = {_value(row, "source_candidate_export_row_id") for row in optional_gate2d_candidate_rows}
    candidate_flags_false = all(
        _value(row, "grain_level_ingestion_authorized") == "false"
        and _value(row, "formula_use_authorized") == "false"
        and _value(row, "qch_weighting_authorized") == "false"
        and _value(row, "jrc_authorized") == "false"
        and _value(row, "chi_selected_authorized") == "false"
        and _value(row, "production_ingestion_authorized") == "false"
        and _value(row, "runtime_configuration_authorized") == "false"
        for row in optional_gate2d_candidate_rows
    )
    candidate_scope_ok = all(
        _value(row, "route_key_candidate") == "660/W800/D900"
        and _value(row, "diameter_nm") == "300"
        and _value(row, "bin_basis") == "aggregate_proxy"
        and _value(row, "NODI_view") in {"fixed_660_gold", "per_wavelength_gold"}
        and _value(row, "tpd_proxy_aggregation_basis") in {"velocity_weighted", "residence_time_weighted"}
        for row in optional_gate2d_candidate_rows
    )
    validation_pass = bool(optional_gate2d_validation_rows) and all(
        not _value(row, "status").startswith("FAIL") for row in optional_gate2d_validation_rows
    )
    return [
        {
            "audit_id": "G2D-SEMANTIC-001",
            "audit_item": "comsol_gate2c_status_reconciliation_rows_present",
            "audit_status": "PASS" if len(optional_status_rows) == 6 else "INFO_OR_BLOCKED_RECONCILIATION_NOT_COMPLETE",
            "evidence": f"rows={len(optional_status_rows)}",
            "required_next_gate": "NODI_GATE2D_PREFLIGHT_REVIEW",
        },
        {
            "audit_id": "G2D-SEMANTIC-002",
            "audit_item": "comsol_gate2d_candidate_matches_nodi_verdict_rows",
            "audit_status": "PASS"
            if len(optional_gate2d_candidate_rows) == 4 and gate2d_ids == verdict_ids and candidate_scope_ok
            else "BLOCKED_GATE2D_CANDIDATE_SCOPE_MISMATCH",
            "evidence": f"gate2d_rows={len(optional_gate2d_candidate_rows)} source_ids={sorted(gate2d_ids)}",
            "required_next_gate": "NODI_GATE2D_PREFLIGHT_REVIEW",
        },
        {
            "audit_id": "G2D-SEMANTIC-003",
            "audit_item": "comsol_gate2d_candidate_authorization_flags_false",
            "audit_status": "PASS" if candidate_flags_false else "BLOCKED_FORBIDDEN_AUTHORIZATION_FLAG",
            "evidence": "all false" if candidate_flags_false else "one or more forbidden flags true",
            "required_next_gate": "NO_WEIGHTING_NO_JRC_NO_PRODUCTION",
        },
        {
            "audit_id": "G2D-SEMANTIC-004",
            "audit_item": "comsol_gate2d_validation_passes",
            "audit_status": "PASS" if validation_pass else "BLOCKED_GATE2D_VALIDATION_NOT_PASSING",
            "evidence": f"validation_rows={len(optional_gate2d_validation_rows)}",
            "required_next_gate": "NODI_GATE2D_PREFLIGHT_REVIEW",
        },
        {
            "audit_id": "G2D-SEMANTIC-005",
            "audit_item": "comsol_gate2d_manifest_present",
            "audit_status": "PASS" if len(optional_gate2d_manifest_rows) >= 1 else "INFO_GATE2D_MANIFEST_NOT_PRESENT",
            "evidence": f"manifest_rows={len(optional_gate2d_manifest_rows)}",
            "required_next_gate": "NODI_GATE2D_PREFLIGHT_REVIEW",
        },
    ]


def identify_reduced_scope_candidates(candidate_rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    rows = [
        row
        for row in candidate_rows
        if _value(row, "candidate_status") == "CANDIDATE_FOR_NODI_REVIEW_NOT_ACCEPTED"
        and _value(row, "source_family") == "TPD_PRS_PROXY_AGG"
        and _value(row, "route_key_candidate") == "660/W800/D900"
        and _value(row, "diameter_nm") == "300"
        and _value(row, "NODI_view") in {"fixed_660_gold", "per_wavelength_gold"}
        and _value(row, "bin_basis") == "aggregate_proxy"
    ]
    return sorted(rows, key=lambda row: _value(row, "candidate_export_row_id"))


def build_reduced_scope_verdict_rows(
    reduced_rows: Sequence[Mapping[str, Any]],
    prs_rows: Sequence[Mapping[str, Any]],
    errata_exists: bool,
) -> list[dict[str, Any]]:
    prs_by_view = {
        (_value(row, "route_key"), _value(row, "diameter_nm"), _value(row, "NODI_view"), _value(row, "source_row_type")): row
        for row in prs_rows
    }
    verdicts: list[dict[str, Any]] = []
    for row in reduced_rows:
        view = _value(row, "NODI_view")
        prs = prs_by_view.get(("660/W800/D900", "300", view, "proxy_aggregate"), {})
        exact = _value(prs, "exact_grain_present") == "true" and _value(prs, "coverage_verdict") == "EXACT_GRAIN_PRESENT_CONTEXT_ONLY_REVIEW"
        basis = _tpd_proxy_basis(_value(row, "source_row_identity"))
        can_enter = errata_exists and exact
        verdicts.append(
            {
                "source_candidate_row_id": _value(row, "candidate_export_row_id"),
                "source_identity": _value(row, "source_row_identity"),
                "source_family": _value(row, "source_family"),
                "route_key": _value(row, "route_key_candidate"),
                "NODI_view": view,
                "diameter_nm": _value(row, "diameter_nm"),
                "tpd_proxy_aggregation_basis": basis,
                "bin_basis": _value(row, "bin_basis"),
                "exact_prs_grain_present_from_report201": _bool_text(exact),
                "matched_prs_row_count_from_report201": _value(prs, "matched_prs_row_count", "0"),
                "prs_evidence_hash": _value(prs, "evidence_hash"),
                "decision_use_allowed": "false",
                "can_enter_context_only_acceptance_ledger": _bool_text(can_enter),
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "is_chi_selected": "false",
                "is_production_ingestion": "false",
                "is_runtime_configuration": "false",
                "acceptance_status": "READY_FOR_CONTEXT_ONLY_ACCEPTANCE_LEDGER_PREFLIGHT"
                if can_enter
                else "PENDING_COMSOL_GATE2C_ERRATA_PRS_COVERAGE_PRESENT"
                if exact
                else "BLOCKED_NO_EXACT_REPORT201_PRS_COVERAGE",
                "blocker_or_required_next_gate": "COMSOL_GATE2C_ERRATA_OR_CORRECTED_MASTER_PACKET"
                if exact and not errata_exists
                else "future explicit Gate2D reduced-scope context-only ledger authorization",
                "basis_note": "TPD proxy aggregation basis only; not NODI route weighting and not q_ch weighting",
            }
        )
    return verdicts


def build_acceptance_preflight_rows(
    verdict_rows: Sequence[Mapping[str, Any]],
    errata_exists: bool,
) -> list[dict[str, Any]]:
    exact_count = sum(_value(row, "exact_prs_grain_present_from_report201") == "true" for row in verdict_rows)
    can_enter_count = sum(_value(row, "can_enter_context_only_acceptance_ledger") == "true" for row in verdict_rows)
    return [
        {
            "preflight_check_id": "G2D-PREFLIGHT-001",
            "check_name": "reduced_scope_candidate_row_count",
            "status": "PASS" if len(verdict_rows) == 4 else "BLOCKED_UNEXPECTED_REDUCED_SCOPE_ROW_COUNT",
            "observed": len(verdict_rows),
            "expected": 4,
            "can_open_gate2d_context_only_ledger": _bool_text(errata_exists and len(verdict_rows) == 4 and can_enter_count == 4),
        },
        {
            "preflight_check_id": "G2D-PREFLIGHT-002",
            "check_name": "report201_prs_coverage_for_reduced_scope_rows",
            "status": "PASS_PREFLIGHT_COVERAGE_PRESENT" if exact_count == 4 else "BLOCKED_PRS_COVERAGE_MISSING",
            "observed": exact_count,
            "expected": 4,
            "can_open_gate2d_context_only_ledger": _bool_text(errata_exists and exact_count == 4),
        },
        {
            "preflight_check_id": "G2D-PREFLIGHT-003",
            "check_name": "comsol_gate2c_errata_required_for_automatic_acceptance",
            "status": "PASS_ERRATA_PRESENT" if errata_exists else "PARTIAL_PENDING_COMSOL_GATE2C_ERRATA",
            "observed": _bool_text(errata_exists),
            "expected": "true before NODI acceptance ledger can open",
            "can_open_gate2d_context_only_ledger": _bool_text(errata_exists and can_enter_count == 4),
        },
        {
            "preflight_check_id": "G2D-PREFLIGHT-004",
            "check_name": "no_weighting_no_jrc_no_production",
            "status": "PASS_BLOCKED",
            "observed": "all authorization flags false",
            "expected": "false for weighting, JRC, chi_selected, runtime, production",
            "can_open_gate2d_context_only_ledger": _bool_text(errata_exists and can_enter_count == 4),
        },
    ]


def build_exclusion_rows(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(_value(row, "candidate_status") for row in candidate_rows)
    specs = [
        ("EXCL-220", "220 nm", "BLOCKED_220NM_NO_DIRECT_MATCH", "blocked; no direct PRS match; no auto-map to 300/40/60"),
        ("EXCL-D1200", "W800/D1200 300 nm", "BLOCKED_D1200_EXACT_GRAIN_UNCERTAIN", "blocked/uncertain; cannot borrow D900 semantics"),
        ("EXCL-UNBOUND-VIEW", "TPD source/alignment", "BLOCKED_UNBOUND_NODI_VIEW", "blocked missing NODI_view / not NODI-bound"),
        ("EXCL-EDGE4", "edge4 bin proxy", "REVIEW_ONLY_EDGE_POLICY_REQUIRED", "review-only; edge4-to-edge20 policy not approved"),
        ("EXCL-QCH", "q_ch provenance", "QUARANTINE_QCH_PROVENANCE_ONLY", "quarantine; not formal q_ch sidecar; no weighting"),
        ("EXCL-LOCALQ-V4-STRONG", "local-Q/V4/strong claims", "not_in_reduced_scope", "review-only or hard blocked carry-forward"),
    ]
    return [
        {
            "exclusion_id": exclusion_id,
            "excluded_scope": scope,
            "source_candidate_status": status,
            "source_candidate_row_count": counts.get(status, 0) if status != "not_in_reduced_scope" else 0,
            "disposition": disposition,
            "decision_use_allowed": "false",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
            "is_chi_selected": "false",
            "is_production_ingestion": "false",
            "is_runtime_configuration": "false",
            "required_next_gate": "future explicit repair/export/policy gate",
        }
        for exclusion_id, scope, status, disposition in specs
    ]


def build_self_review_rows(errata_exists: bool, count_consistent: bool) -> list[dict[str, Any]]:
    return [
        {
            "reviewer": "Reviewer A",
            "focus": "COMSOL Gate2C count consistency",
            "finding_severity": "PASS_COUNTS_PARTIAL_NO_ERRATA"
            if count_consistent and not errata_exists
            else "PARTIAL"
            if not count_consistent
            else "PASS",
            "finding": "Master packet, candidate CSV, and validation status counts match."
            if count_consistent
            else "Master packet narrative counts drift from candidate CSV; validation matches actual CSV counts.",
            "unresolved_risk": "No explicit COMSOL errata/reduced-scope package found"
            if not errata_exists
            else "none",
        },
        {
            "reviewer": "Reviewer B",
            "focus": "4-row reduced-scope semantics",
            "finding_severity": "PASS_PREFLIGHT",
            "finding": "Four candidate rows are W800/D900/300 aggregate proxy rows with velocity/residence-time proxy basis only.",
            "unresolved_risk": "none" if errata_exists else "acceptance ledger pending errata",
        },
        {
            "reviewer": "Reviewer C",
            "focus": "PRS coverage/hash and blocker carry-forward",
            "finding_severity": "PASS_PREFLIGHT",
            "finding": "Report 201 PRS verdict confirms exact context-review grains for D900/300 fixed/per-wavelength views; 220, D1200/300, and edge4 remain blocked/review-only.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer D",
            "focus": "forbidden claim leakage",
            "finding_severity": "PASS",
            "finding": "All weighting, q_ch, JRC, chi_selected, winner, yield, detection, runtime, and production authorizations remain false.",
            "unresolved_risk": "none",
        },
    ]


def validate_gate2d_payload(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    errata_exists = bool(payload.get("comsol_errata_exists"))
    if not errata_exists and payload.get("status") != PARTIAL_STATUS:
        issues.append("missing COMSOL errata must force PARTIAL_PENDING status")
    if payload.get("candidate_export_row_count") != 145:
        issues.append("COMSOL Gate2C candidate export row count must be 145")
    if payload.get("actual_candidate_status_counts") != EXPECTED_ACTUAL_COUNTS:
        issues.append("actual candidate status counts do not match total-control expected counts")
    if len(payload.get("reduced_scope_candidate_rows", [])) != 4:
        issues.append("exactly four reduced-scope candidate rows must be identified")
    if payload.get("comsol_errata_exists"):
        if payload.get("comsol_gate2d_candidate_row_count") != 4:
            issues.append("COMSOL Gate2D candidate package must contain exactly four rows when errata exists")
        if payload.get("comsol_gate2d_validation_row_count", 0) < 1:
            issues.append("COMSOL Gate2D validation must be present when errata exists")
        for row in payload.get("optional_semantic_audit_rows", []):
            if _value(row, "audit_status").startswith("BLOCKED"):
                issues.append(f"optional COMSOL Gate2D semantic audit failed: {_value(row, 'audit_id')}")
    for row in payload.get("reduced_scope_candidate_rows", []):
        if _value(row, "route_key") != "660/W800/D900":
            issues.append("reduced-scope row is not W800/D900")
        if _value(row, "diameter_nm") != "300":
            issues.append("reduced-scope row is not 300 nm")
        if _value(row, "bin_basis") != "aggregate_proxy":
            issues.append("reduced-scope row is not aggregate_proxy")
        if _value(row, "tpd_proxy_aggregation_basis") not in {"velocity_weighted", "residence_time_weighted"}:
            issues.append("reduced-scope row has unexpected proxy aggregation basis")
        if _value(row, "exact_prs_grain_present_from_report201") != "true":
            issues.append("reduced-scope row lacks Report 201 exact PRS coverage")
    issues.extend(_validate_forbidden_flags(payload))
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "consistency_audit_csv": output_dir / CONSISTENCY_AUDIT,
        "status_reconciliation_csv": output_dir / STATUS_RECONCILIATION,
        "reduced_scope_verdict_csv": output_dir / REDUCED_SCOPE_VERDICT,
        "acceptance_preflight_csv": output_dir / ACCEPTANCE_PREFLIGHT,
        "exclusion_register_csv": output_dir / EXCLUSION_REGISTER,
        "self_review_csv": output_dir / SELF_REVIEW,
        "report_json": output_dir / REPORT_JSON,
        "report_md": output_dir / REPORT_MD,
        "report_202_md": report_dir / REPORT_202,
    }
    write_csv_rows(paths["consistency_audit_csv"], list(payload["consistency_audit_rows"]))
    write_csv_rows(paths["status_reconciliation_csv"], list(payload["status_reconciliation_rows"]))
    write_csv_rows(paths["reduced_scope_verdict_csv"], list(payload["reduced_scope_candidate_rows"]))
    write_csv_rows(paths["acceptance_preflight_csv"], list(payload["acceptance_preflight_rows"]))
    write_csv_rows(paths["exclusion_register_csv"], list(payload["exclusion_rows"]))
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
    paths["report_202_md"].write_text(
        report_md.replace(
            "# NODI/COMSOL Gate2D Reduced-Scope Acceptance Preflight",
            "# Report 202 - NODI/COMSOL Gate2D Reduced-Scope Acceptance Preflight",
        ),
        encoding="utf-8",
        newline="\n",
    )
    return {key: str(path) for key, path in paths.items()}


def render_report_md(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    consistency_sentence = (
        "The master packet, actual candidate export CSV, COMSOL reconciliation/errata, and validation observed counts agree. COMSOL Gate2D reduced-scope candidate files were found and included in this preflight."
        if payload["comsol_gate2c_count_consistent"] and payload["comsol_errata_exists"]
        else "The master packet, actual candidate export CSV, and COMSOL validation observed counts agree. No explicit COMSOL errata or Gate2D reduced-scope candidate package was found during this run, so NODI keeps the acceptance ledger pending."
        if payload["comsol_gate2c_count_consistent"]
        else "The actual candidate export CSV and COMSOL validation observed counts agree, but the master packet narrative counts drift from the actual candidate-status counts. No COMSOL errata or Gate2D reduced-scope candidate package was found during this run."
    )
    return "\n".join(
        [
            "# NODI/COMSOL Gate2D Reduced-Scope Acceptance Preflight",
            "",
            "Date: 2026-06-28",
            "",
            "## Disposition",
            "",
            f"`{payload['status']}`",
            "",
            "This is a reduced-scope acceptance preflight only. It does not open weighting, q_ch weighting, chi_selected, JRC, yield, winner, detection_probability, runtime configuration, or production ingestion.",
            "",
            "## Key Answers",
            "",
            f"- COMSOL Gate2C package counts consistent: `{payload['comsol_gate2c_count_consistent']}`.",
            f"- COMSOL errata found: `{payload['comsol_errata_exists']}`.",
            "- Four W800/D900/300 aggregate proxy candidates pass NODI PRS coverage preflight: `YES`.",
            "- Open Gate2D reduced-scope context-only acceptance ledger now: `PARTIAL/PENDING` unless COMSOL errata is present.",
            "- edge4 policy approved: `NO`.",
            "- formal q_ch sidecar exists: `NO`.",
            "- weighting/JRC/chi_selected/yield/winner/detection_probability allowed: `NO`.",
            "",
            "## Consistency Audit",
            "",
            consistency_sentence,
            "",
            "## 4-Row Candidate Verdict",
            "",
            "Rows `G2C-CAND-0077` through `G2C-CAND-0080` are W800/D900/300 aggregate proxy candidates for `fixed_660_gold` and `per_wavelength_gold`, with `velocity_weighted` or `residence_time_weighted` TPD proxy aggregation basis. These basis labels are context descriptors only, not NODI route weighting and not q_ch weighting.",
            "",
            "## Output Hashes",
            "",
            f"- consistency audit: `{hashes.get('consistency_audit_csv', 'pending')}`",
            f"- status reconciliation: `{hashes.get('status_reconciliation_csv', 'pending')}`",
            f"- reduced scope verdict: `{hashes.get('reduced_scope_verdict_csv', 'pending')}`",
            f"- acceptance preflight: `{hashes.get('acceptance_preflight_csv', 'pending')}`",
            f"- exclusion register: `{hashes.get('exclusion_register_csv', 'pending')}`",
            f"- self-review: `{hashes.get('self_review_csv', 'pending')}`",
            "",
            "## Carry-Forward Blockers",
            "",
            "220 nm remains blocked with no direct PRS match. D1200/300 remains blocked/uncertain. TPD source/alignment rows remain blocked by missing or unbound NODI view. edge4 bin proxy remains review-only because edge4-to-edge20 policy is not approved. q_ch remains provenance-only/quarantine; local-Q, V4, and strong claims stay review-only or hard blocked.",
        ]
    ) + "\n"


def _validate_forbidden_flags(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    row_groups = (
        payload.get("reduced_scope_candidate_rows", []),
        payload.get("acceptance_preflight_rows", []),
        payload.get("exclusion_rows", []),
    )
    for rows in row_groups:
        for row in rows:
            for key in FORBIDDEN_FLAG_FIELDS:
                if key in row and str(row[key]).lower() not in {"false", "", "not_applicable"}:
                    issues.append(f"forbidden flag {key}={row[key]!r} in row {row}")
    return issues


def _tpd_proxy_basis(source_identity: str) -> str:
    if "residence_time_weighted" in source_identity:
        return "residence_time_weighted"
    if "velocity_weighted" in source_identity:
        return "velocity_weighted"
    return "UNKNOWN_PROXY_BASIS"


def _row_count(path: Path) -> int:
    if path.suffix.lower() != ".csv":
        return 0
    return len(read_csv_rows(path))


def _read_optional_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.suffix.lower() != ".csv":
        return []
    return read_csv_rows(path)


def _value(row: Mapping[str, Any], key: str, default: str = "") -> str:
    value = row.get(key, default)
    if value is None:
        return default
    return str(value)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _normalize_lf(path: Path) -> None:
    data = path.read_bytes()
    while b"\r\n" in data:
        data = data.replace(b"\r\n", b"\n")
    data = data.replace(b"\r", b"")
    path.write_bytes(data)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate2d_acceptance_preflight:
        raise SystemExit("Refusing to write Gate2D outputs without explicit confirmation flag.")
    payload = build_gate2d_payload(comsol_root=args.comsol_root, output_dir=args.output_dir)
    issues = validate_gate2d_payload(payload)
    if issues:
        print(f"NODI_COMSOL_GATE2D_ACCEPTANCE_PREFLIGHT: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    report_sha = sha256_file(outputs["report_json"])
    print(f"NODI_COMSOL_GATE2D_ACCEPTANCE_PREFLIGHT: {payload['status']}")
    print(f"report_path: {outputs['report_json']}")
    print(f"report_sha256: {report_sha}")
    print(f"reduced_scope_verdict_csv: {outputs['reduced_scope_verdict_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
