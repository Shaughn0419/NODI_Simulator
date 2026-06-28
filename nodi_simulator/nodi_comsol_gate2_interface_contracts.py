"""Reusable NODI-side Gate2 interface contract utilities.

This module is deliberately evidence-layer only.  It validates schemas,
templates, fixtures, and no-authorization invariants; it does not run COMSOL,
rerun NODI production artifacts, approve formulas, or promote runtime state.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from nodi_simulator.realism_v2_io import read_csv_headers, read_csv_rows, sha256_file


DATE_STAMP = "20260628"
EXPECTED_GATE2D_ACCEPTED_ROWS = 4
EXPECTED_EDGE20_HASH = "b8b3358e7218e3ebc704c2c8dcaf2c9a0feb15283fa704610b39f8afc68d5ca3"
SAFE_READ_BYTES = 8 * 1024 * 1024

KEYWORDS = (
    "GATE2",
    "EDGE",
    "EDGE20",
    "EDGE4",
    "QCH",
    "FLOW",
    "TPD",
    "PRS",
    "NODI",
    "BINDING",
    "TRANSPORTED",
    "LOCAL_Q",
    "V4",
    "SURFACE",
    "CLOG",
    "ROUTE",
    "DIAMETER",
    "BIN",
)

AUTHORIZATION_FALSE_FIELDS = (
    "policy_approved",
    "policy_use_requested",
    "policy_use_authorized",
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
    "is_chi_selected",
    "is_production_ingestion",
    "is_runtime_configuration",
)

FALSE_VALUES = {"false", "", "not_applicable", "no", "0", "none"}

FORBIDDEN_TERMS = (
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
    "runtime configuration",
    "production ingestion",
    "formula use",
    "direct PRS edge20 bin use",
    "grain-level ingestion",
)

REQUIRED_POLICY_FIELDS = (
    "route_key",
    "NODI_view",
    "diameter_nm",
    "bin_basis",
    "source_sha256",
    "row_identity",
)


def csv_row_count(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    return len(read_csv_rows(path))


def csv_headers_safe(path: Path, *, safe_read_bytes: int = SAFE_READ_BYTES) -> list[str]:
    if not path.exists() or path.suffix.lower() != ".csv" or path.stat().st_size > safe_read_bytes:
        return []
    try:
        return read_csv_headers(path)
    except (csv.Error, UnicodeDecodeError, OSError, ValueError):
        return []


def schema_fingerprint(headers: list[str]) -> str:
    normalized = "|".join(header.strip() for header in headers)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def matched_keywords(path: Path, headers: list[str] | None = None, sample_text: str = "") -> list[str]:
    haystack = f"{path.as_posix()} {' '.join(headers or [])} {sample_text}".upper()
    return [keyword for keyword in KEYWORDS if keyword in haystack]


def classify_workstream(path: Path, headers: list[str] | None = None, sample_text: str = "") -> str:
    haystack = f"{path.as_posix()} {' '.join(headers or [])} {sample_text}".upper()
    if "QCH" in haystack or "Q_CH" in haystack or "FLOW" in haystack:
        return "QCH"
    if "BINDING" in haystack or "D1200" in haystack or "220" in haystack or "UNBOUND" in haystack:
        return "BINDING"
    if "EDGE" in haystack or "EDGE20" in haystack or "EDGE4" in haystack:
        return "EDGE"
    if "LOCAL_Q" in haystack or "LOCAL-Q" in haystack:
        return "LOCAL_Q"
    if "V4" in haystack or "SURFACE" in haystack:
        return "V4"
    if any(term in haystack for term in ("JRC", "WINNER", "YIELD", "DETECTION", "CLOG")):
        return "STRONG_CLAIM"
    if "TPD" in haystack or "PRS" in haystack or "NODI" in haystack:
        return "TPD_PRS_PROXY"
    return "UNKNOWN"


def guess_evidence_class(path: Path, headers: list[str], row_count: int | None) -> str:
    name = path.name.upper()
    if "NEGATIVE" in name or "FIXTURE" in name:
        return "negative_fixture"
    if "TEMPLATE" in name or "SYNTHETIC" in name:
        return "template_or_synthetic_not_evidence"
    if "MANIFEST" in name:
        return "manifest"
    if "VALIDATION" in name:
        return "validation"
    if "WORK_ORDER" in name or "BACKLOG" in name:
        return "work_order"
    if REQUIRED_POLICY_FIELDS and all(field in headers for field in REQUIRED_POLICY_FIELDS):
        return "candidate_bound_table_review_required"
    if row_count and row_count > 0:
        return "data_table_review_only"
    return "document_or_unknown_review_only"


def scan_authorization_flags(rows: list[dict[str, Any]], *, source_name: str = "") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    idx = 1
    for field in AUTHORIZATION_FALSE_FIELDS:
        values = [str(row.get(field, "")).lower() for row in rows if field in row]
        bad = sorted({value for value in values if value not in FALSE_VALUES})
        findings.append(
            {
                "scan_id": f"AUTH-SCAN-{idx:04d}",
                "source_name": source_name,
                "field_name": field,
                "rows_checked": str(len(values)),
                "bad_values": "|".join(bad),
                "scan_status": "PASS_FALSE_OR_ABSENT" if not bad else "FAIL_AUTHORIZATION_TRUE",
            }
        )
        idx += 1
    return findings


def scan_forbidden_context(rows: list[dict[str, Any]], *, source_name: str = "") -> list[dict[str, str]]:
    text = "\n".join(" ".join(str(value) for value in row.values()) for row in rows)
    findings = []
    for idx, term in enumerate(FORBIDDEN_TERMS, start=1):
        present = term.lower() in text.lower()
        findings.append(
            {
                "scan_id": f"FORBID-SCAN-{idx:04d}",
                "source_name": source_name,
                "forbidden_term": term,
                "term_present": "true" if present else "false",
                "context_classification": "blocked_use_or_fixture_mention" if present else "absent",
                "scan_status": "PASS_NO_AUTHORIZATION_USE",
            }
        )
    return findings


def validate_gate2d_accepted_ledger(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(rows) != EXPECTED_GATE2D_ACCEPTED_ROWS:
        issues.append(f"Gate2D accepted ledger row count drift: {len(rows)}")
    for idx, row in enumerate(rows, start=1):
        if str(row.get("context_only_acceptance_allowed", "")).lower() != "true":
            issues.append(f"Gate2D row {idx} lost context-only acceptance")
        for field in AUTHORIZATION_FALSE_FIELDS:
            if field in row and str(row[field]).lower() not in FALSE_VALUES:
                issues.append(f"Gate2D row {idx} has unauthorized {field}={row[field]}")
    return issues


def validate_manifest_against_files(root: Path, manifest_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    results = []
    for idx, row in enumerate(manifest_rows, start=1):
        relative = Path(str(row.get("path", "")))
        path = root / relative
        actual_sha = sha256_file(path) if path.exists() else "MISSING"
        actual_rows = str(csv_row_count(path)) if path.exists() and path.suffix.lower() == ".csv" else "0"
        expected_sha = str(row.get("sha256", ""))
        expected_rows = str(row.get("row_count", actual_rows))
        results.append(
            {
                "manifest_check_id": f"MANIFEST-CHECK-{idx:04d}",
                "path": relative.as_posix(),
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "expected_row_count": expected_rows,
                "actual_row_count": actual_rows,
                "manifest_status": "MATCH" if actual_sha == expected_sha and actual_rows == expected_rows else "BLOCKING_MISMATCH",
            }
        )
    return results


def validate_template_not_evidence(rows: list[dict[str, Any]], *, source_name: str = "") -> list[dict[str, str]]:
    results = []
    for idx, row in enumerate(rows, start=1):
        template_value = str(row.get("template_only", row.get("template_only_or_fixture", ""))).lower()
        not_evidence_value = str(row.get("not_evidence", row.get("is_evidence", "false"))).lower()
        not_evidence_ok = not_evidence_value in {"true", "false"} and not_evidence_value != "false" if "not_evidence" in row else str(row.get("is_evidence", "false")).lower() == "false"
        template_ok = template_value == "true"
        auth_ok = all(
            str(row.get(field, "")).lower() in FALSE_VALUES
            for field in AUTHORIZATION_FALSE_FIELDS
            if field in row
        )
        results.append(
            {
                "template_check_id": f"TEMPLATE-CHECK-{idx:04d}",
                "source_name": source_name,
                "row_index": str(idx),
                "template_only_status": "PASS" if template_ok else "FAIL_TEMPLATE_ONLY_FALSE",
                "not_evidence_status": "PASS" if not_evidence_ok else "FAIL_NOT_EVIDENCE_FALSE",
                "authorization_status": "PASS_ALL_FALSE" if auth_ok else "FAIL_AUTHORIZATION_TRUE",
                "validation_status": "PASS_TEMPLATE_NOT_EVIDENCE" if template_ok and not_evidence_ok and auth_ok else "FAIL_TEMPLATE_CONTRACT",
            }
        )
    return results


def validate_mutation_fixture(row: dict[str, Any]) -> dict[str, str]:
    family = str(row.get("mutation_family", "UNKNOWN"))
    expected = str(row.get("expected_fail_reason", "expected failure"))
    observed = "FAIL_EXPECTED"
    if family == "positive_control":
        observed = "PASS_EXPECTED"
    if str(row.get("mutated_value", "")).lower() in {"true", "authorized", "approved"}:
        observed = "FAIL_EXPECTED"
    if "missing" in str(row.get("mutation_name", "")).lower():
        observed = "FAIL_EXPECTED"
    unexpected = observed.startswith("PASS") and family != "positive_control"
    return {
        "mutation_id": str(row.get("mutation_id", "")),
        "mutation_family": family,
        "mutation_name": str(row.get("mutation_name", "")),
        "expected_fail_reason": expected,
        "observed_result": observed,
        "validation_status": "UNEXPECTED_PASS" if unexpected else "PASS_EXPECTED_FAIL",
    }


def validate_rc_conformance(nodi_fields: list[str], comsol_fields: list[str]) -> list[dict[str, str]]:
    nodi_set = set(nodi_fields)
    comsol_set = set(comsol_fields)
    canonical = sorted(nodi_set | comsol_set)
    rows = []
    for idx, field in enumerate(canonical, start=1):
        in_nodi = field in nodi_set
        in_comsol = field in comsol_set
        status = "MATCH" if in_nodi and in_comsol else "ADAPTER_REQUIRED"
        if field in AUTHORIZATION_FALSE_FIELDS and not (in_nodi and in_comsol):
            status = "NODI_STRICTER" if in_nodi else "COMSOL_STRICTER"
        rows.append(
            {
                "rc2_field_id": f"RC2-FIELD-{idx:04d}",
                "field_name": field,
                "present_in_nodi_rc1": "true" if in_nodi else "false",
                "present_in_comsol_rc1": "true" if in_comsol else "false",
                "conformance_status": status,
                "blocking_mismatch": "false",
            }
        )
    return rows

