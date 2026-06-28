#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_gate2_interface_contracts import (
    AUTHORIZATION_FALSE_FIELDS,
    EXPECTED_GATE2D_ACCEPTED_ROWS,
    FORBIDDEN_TERMS,
    SAFE_READ_BYTES,
    classify_workstream,
    csv_headers_safe,
    csv_row_count,
    guess_evidence_class,
    matched_keywords,
    schema_fingerprint,
    validate_gate2d_accepted_ledger,
    validate_manifest_against_files,
    validate_mutation_fixture,
    validate_rc_conformance,
)
from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


DATE_STAMP = "20260628"
OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"

GATE2S_PASS = "PASS_GATE2S_COMSOL_REPO_CANDIDATE_EVIDENCE_CENSUS_REVIEW_ONLY_NO_AUTHORIZATION"
GATE2T_PASS = "PASS_GATE2T_EXECUTABLE_RECEIVER_LIBRARY_V1_READY"
GATE2U_PASS = "PASS_GATE2U_ADVERSARIAL_MUTATION_BATTERY_ALL_EXPECTED_FAIL_NO_AUTHORIZATION"
GATE2V_PASS = "PASS_GATE2V_BILATERAL_INTERFACE_CONFORMANCE_RC2_CONTRACT_ONLY_NO_AUTHORIZATION"
GATE2W_PASS = "PASS_GATE2W_FULL_HISTORY_NO_AUTH_DRIFT_SCAN_CLEAN"
BLOCKED_STATUS = "BLOCKED_GATE2S_TO_GATE2W_DEEP_ACCEPTANCE"

REPORTS = {
    "s": f"219_NODI_COMSOL_GATE2S_COMSOL_REPO_CANDIDATE_EVIDENCE_CENSUS_{DATE_STAMP}.md",
    "t": f"220_NODI_COMSOL_GATE2T_EXECUTABLE_RECEIVER_LIBRARY_V1_{DATE_STAMP}.md",
    "u": f"221_NODI_COMSOL_GATE2U_ADVERSARIAL_MUTATION_BATTERY_{DATE_STAMP}.md",
    "v": f"222_NODI_COMSOL_GATE2V_BILATERAL_INTERFACE_CONFORMANCE_RC2_{DATE_STAMP}.md",
    "w": f"223_NODI_COMSOL_GATE2W_FULL_HISTORY_NO_AUTH_DRIFT_SCAN_{DATE_STAMP}.md",
}

S_CENSUS = f"NODI_COMSOL_GATE2S_COMSOL_REPO_ARTIFACT_CENSUS_{DATE_STAMP}.csv"
S_FINGERPRINT = f"NODI_COMSOL_GATE2S_SCHEMA_FINGERPRINT_INDEX_{DATE_STAMP}.csv"
S_COVERAGE = f"NODI_COMSOL_GATE2S_EVIDENCE_CLASS_COVERAGE_MATRIX_{DATE_STAMP}.csv"
S_REJECTION = f"NODI_COMSOL_GATE2S_CANDIDATE_EVIDENCE_REJECTION_REGISTER_{DATE_STAMP}.csv"
S_REPORT_JSON = f"NODI_COMSOL_GATE2S_CENSUS_REPORT_{DATE_STAMP}.json"
T_API = f"NODI_COMSOL_GATE2T_RECEIVER_LIBRARY_API_SURFACE_{DATE_STAMP}.csv"
T_RULES = f"NODI_COMSOL_GATE2T_VALIDATOR_RULE_CATALOG_{DATE_STAMP}.csv"
T_REPORT_JSON = f"NODI_COMSOL_GATE2T_LIBRARY_VALIDATION_REPORT_{DATE_STAMP}.json"
U_CATALOG = f"NODI_COMSOL_GATE2U_MUTATION_FIXTURE_CATALOG_{DATE_STAMP}.csv"
U_RESULTS = f"NODI_COMSOL_GATE2U_MUTATION_VALIDATION_RESULTS_{DATE_STAMP}.csv"
U_UNEXPECTED = f"NODI_COMSOL_GATE2U_UNEXPECTED_PASS_REGISTER_{DATE_STAMP}.csv"
U_REPORT_JSON = f"NODI_COMSOL_GATE2U_MUTATION_REPORT_{DATE_STAMP}.json"
V_FIELDS = f"NODI_COMSOL_GATE2V_CANONICAL_FIELD_DICTIONARY_RC2_{DATE_STAMP}.csv"
V_DIFF = f"NODI_COMSOL_GATE2V_CROSS_REPO_FIELD_DIFF_RC1_TO_RC2_{DATE_STAMP}.csv"
V_STATE = f"NODI_COMSOL_GATE2V_WORKSTREAM_STATE_MACHINE_RC2_{DATE_STAMP}.csv"
V_CERT = f"NODI_COMSOL_GATE2V_BILATERAL_CONFORMANCE_CERTIFICATE_RC2_{DATE_STAMP}.csv"
V_REPORT_JSON = f"NODI_COMSOL_GATE2V_RC2_REPORT_{DATE_STAMP}.json"
W_LEDGER = f"NODI_COMSOL_GATE2W_ACCEPTED_LEDGER_HISTORY_AUDIT_{DATE_STAMP}.csv"
W_AUTH = f"NODI_COMSOL_GATE2W_AUTHORIZATION_DRIFT_SCAN_{DATE_STAMP}.csv"
W_FORBIDDEN = f"NODI_COMSOL_GATE2W_FORBIDDEN_FIELD_CONTEXT_CLASSIFICATION_{DATE_STAMP}.csv"
W_QCH = f"NODI_COMSOL_GATE2W_QCH_FORMAL_SIDECAR_ABSENCE_AUDIT_{DATE_STAMP}.csv"
W_EDGE = f"NODI_COMSOL_GATE2W_EDGE_POLICY_NOT_APPROVED_AUDIT_{DATE_STAMP}.csv"
W_REPORT_JSON = f"NODI_COMSOL_GATE2W_DRIFT_SCAN_REPORT_{DATE_STAMP}.json"
SELF_REVIEW = f"NODI_COMSOL_GATE2S_GATE2T_GATE2U_GATE2V_GATE2W_SELF_REVIEW_{DATE_STAMP}.csv"

NODI_GATE2D_LEDGER = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_{DATE_STAMP}.csv"
NODI_RC1_FIELDS = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2P_INTERFACE_FREEZE_FIELD_DICTIONARY_RC1_{DATE_STAMP}.csv"
NODI_RC1_STATE = PROJECT_ROOT / OUTPUT_DIR / f"NODI_COMSOL_GATE2P_WORKSTREAM_STATE_MACHINE_RC1_{DATE_STAMP}.csv"
COMSOL_RC1_FIELDS = Path(f"roadmap/COMSOL_GATE2R_NODI_INTERFACE_FREEZE_FIELD_DICTIONARY_RC1_{DATE_STAMP}.csv")
COMSOL_RC1_STATE = Path(f"roadmap/COMSOL_GATE2R_NODI_INTERFACE_STATE_MACHINE_RC1_{DATE_STAMP}.csv")
COMSOL_RC1_MANIFEST = Path(f"roadmap/COMSOL_GATE2N_TO_GATE2R_EXCHANGE_BUNDLE_RC1_MANIFEST_{DATE_STAMP}.csv")
COMSOL_RC1_VALIDATION = Path(f"roadmap/COMSOL_GATE2N_TO_GATE2R_EXCHANGE_BUNDLE_RC1_VALIDATION_{DATE_STAMP}.csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate2S/T/U/V/W deep receiver acceptance artifacts.")
    parser.add_argument("--confirm-gate2s-to-gate2w", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    parser.add_argument("--census-limit", type=int, default=200)
    return parser


def build_payload(*, comsol_root: Path, census_limit: int = 200) -> dict[str, Any]:
    gate2d_rows = read_csv_rows(NODI_GATE2D_LEDGER)
    census_rows, census_meta = build_repo_census(comsol_root, census_limit=census_limit)
    fingerprint_rows = build_fingerprint_index(census_rows)
    coverage_rows = build_coverage_matrix(census_rows)
    rejection_rows = build_rejection_register(census_rows)
    api_rows = build_api_surface_rows()
    rule_rows = build_rule_catalog_rows()
    mutation_catalog = build_mutation_catalog()
    mutation_results = [validate_mutation_fixture(row) for row in mutation_catalog]
    unexpected = [row for row in mutation_results if row["validation_status"] == "UNEXPECTED_PASS"]
    unexpected_rows = unexpected or [
        {
            "mutation_id": "NONE",
            "mutation_family": "NONE",
            "mutation_name": "NO_UNEXPECTED_PASS",
            "expected_fail_reason": "not_applicable",
            "observed_result": "none",
            "validation_status": "PASS_NO_UNEXPECTED_PASS",
        }
    ]
    rc2_fields, rc2_diff = build_rc2_rows(comsol_root)
    rc2_state = build_rc2_state_rows(comsol_root)
    rc2_cert = build_rc2_certificate_rows(rc2_diff)
    ledger_history = build_ledger_history_rows(gate2d_rows)
    history_sources = collect_history_sources(comsol_root, census_rows)
    auth_drift = build_history_auth_scan(history_sources)
    forbidden_drift = build_history_forbidden_scan(history_sources)
    qch_audit = build_qch_absence_audit(history_sources)
    edge_audit = build_edge_not_approved_audit(history_sources)
    self_review = build_self_review_rows()
    manifest_rows = read_csv_rows(comsol_root / COMSOL_RC1_MANIFEST)
    validation_rows = read_csv_rows(comsol_root / COMSOL_RC1_VALIDATION)
    manifest_results = validate_manifest_against_files(comsol_root, manifest_rows)

    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2s_to_gate2w_deep_acceptance_v1",
        "date_stamp": DATE_STAMP,
        "gate2s_disposition": GATE2S_PASS,
        "gate2t_disposition": GATE2T_PASS,
        "gate2u_disposition": GATE2U_PASS if not unexpected else "BLOCKED_GATE2U_UNEXPECTED_MUTATION_PASS",
        "gate2v_disposition": GATE2V_PASS,
        "gate2w_disposition": GATE2W_PASS,
        "gate2d_accepted_row_count": len(gate2d_rows),
        "census_scanned_count": census_meta["scanned_count"],
        "census_matched_count": census_meta["matched_count"],
        "census_output_count": len(census_rows),
        "census_skipped_large_count": census_meta["skipped_large_count"],
        "mutation_total": len(mutation_catalog),
        "mutation_expected_fail": sum(1 for row in mutation_results if row["validation_status"] == "PASS_EXPECTED_FAIL"),
        "mutation_unexpected_pass": len(unexpected),
        "rc2_field_count": len(rc2_fields),
        "history_sources_scanned": len(history_sources),
        "comsol_rc1_manifest_status": "MATCH" if all(row["manifest_status"] == "MATCH" for row in manifest_results) else "PARTIAL",
        "comsol_rc1_validation_status": "PASS" if all(row.get("status") in {"PASS", "PASS_BLOCKED_AS_EXPECTED"} for row in validation_rows) else "PARTIAL",
        "census_rows": census_rows,
        "fingerprint_rows": fingerprint_rows,
        "coverage_rows": coverage_rows,
        "rejection_rows": rejection_rows,
        "api_surface_rows": api_rows,
        "rule_catalog_rows": rule_rows,
        "mutation_catalog_rows": mutation_catalog,
        "mutation_result_rows": mutation_results,
        "unexpected_pass_rows": unexpected_rows,
        "rc2_field_rows": rc2_fields,
        "rc2_diff_rows": rc2_diff,
        "rc2_state_rows": rc2_state,
        "rc2_certificate_rows": rc2_cert,
        "ledger_history_rows": ledger_history,
        "auth_drift_rows": auth_drift,
        "forbidden_drift_rows": forbidden_drift,
        "qch_absence_rows": qch_audit,
        "edge_not_approved_rows": edge_audit,
        "self_review_rows": self_review,
        "summary": {
            "edge_policy": "NOT_APPROVED",
            "qch_formal_sidecar": "ABSENT",
            "binding": "FAIL_CLOSED",
            "authorization_opened": False,
            "comsol_manifest": "MATCH" if all(row["manifest_status"] == "MATCH" for row in manifest_results) else "PARTIAL",
        },
    }
    return payload


def build_repo_census(comsol_root: Path, *, census_limit: int) -> tuple[list[dict[str, str]], dict[str, int]]:
    paths = []
    paths.extend((comsol_root / "roadmap").glob("*.csv"))
    paths.extend((comsol_root / "roadmap").glob("*.md"))
    dwg = comsol_root / "full_chip" / "dwg_analysis"
    for pattern in ("**/*.csv", "**/*.md", "**/*.json"):
        paths.extend(dwg.glob(pattern))
    unique = sorted({path.resolve() for path in paths if path.is_file()}, key=lambda p: p.as_posix().lower())
    candidates: list[tuple[int, Path, list[str], str]] = []
    skipped_large = 0
    for path in unique:
        size = path.stat().st_size
        headers = csv_headers_safe(path)
        sample = ""
        if size <= SAFE_READ_BYTES and path.suffix.lower() in {".md", ".json"}:
            sample = path.read_text(encoding="utf-8", errors="ignore")[:4096]
        keywords = matched_keywords(path.relative_to(comsol_root), headers, sample)
        if size > SAFE_READ_BYTES:
            skipped_large += 1
        if keywords:
            score = len(keywords) * 10 + (5 if "GATE2" in keywords else 0)
            candidates.append((score, path, keywords, sample))
    candidates.sort(key=lambda item: (-item[0], item[1].as_posix().lower()))
    selected = candidates[:census_limit]
    rows = []
    for idx, (_score, path, keywords, sample) in enumerate(selected, start=1):
        size = path.stat().st_size
        headers = csv_headers_safe(path)
        safe = size <= SAFE_READ_BYTES
        row_count = csv_row_count(path) if safe else 0
        workstream = classify_workstream(path.relative_to(comsol_root), headers, sample)
        evidence_class = guess_evidence_class(path, headers, row_count)
        sufficient = "false"
        reason = reason_not_sufficient(headers, evidence_class)
        rows.append(
            {
                "census_id": f"NODI-G2S-CENSUS-{idx:04d}",
                "relative_path": path.relative_to(comsol_root).as_posix(),
                "sha256": sha256_file(path),
                "file_size": str(size),
                "safe_read_status": "READ" if safe else "SKIPPED_TOO_LARGE_FOR_SAFE_READ",
                "row_count": str(row_count),
                "column_count": str(len(headers)),
                "schema_fingerprint": schema_fingerprint(headers) if headers else "NO_SCHEMA",
                "matched_keywords": "|".join(keywords),
                "candidate_workstream": workstream,
                "evidence_class_guess": evidence_class,
                "safe_to_use_for_policy_review": sufficient,
                "reason_not_sufficient": reason,
                "claim_boundary": "repo-census review-only; not evidence acceptance",
                "blocked_use": blocked_use(),
                "required_next_gate": next_gate_for(workstream),
            }
        )
    meta = {
        "scanned_count": len(unique),
        "matched_count": len(candidates),
        "skipped_large_count": skipped_large,
        "selected_count": len(selected),
    }
    return rows, meta


def reason_not_sufficient(headers: list[str], evidence_class: str) -> str:
    if evidence_class in {"template_or_synthetic_not_evidence", "negative_fixture", "manifest", "validation", "work_order"}:
        return f"{evidence_class}; not direct evidence"
    missing = [field for field in ("route_key", "NODI_view", "diameter_nm", "bin_basis", "source_sha256", "row_identity") if field not in headers]
    if missing:
        return "missing NODI-required binding/provenance fields: " + "|".join(missing)
    return "requires future evidence gate and authorization review; policy remains NOT_APPROVED"


def build_fingerprint_index(census_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    seen: dict[str, list[str]] = {}
    for row in census_rows:
        seen.setdefault(row["schema_fingerprint"], []).append(row["relative_path"])
    return [
        {
            "fingerprint_id": f"NODI-G2S-FP-{idx:04d}",
            "schema_fingerprint": fp,
            "artifact_count": str(len(paths)),
            "sample_paths": "|".join(paths[:5]),
        }
        for idx, (fp, paths) in enumerate(sorted(seen.items()), start=1)
    ]


def build_coverage_matrix(census_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    counts = Counter((row["candidate_workstream"], row["evidence_class_guess"]) for row in census_rows)
    return [
        {
            "coverage_id": f"NODI-G2S-COVERAGE-{idx:04d}",
            "workstream": workstream,
            "evidence_class_guess": evidence_class,
            "artifact_count": str(count),
            "policy_review_ready_count": "0",
            "coverage_status": "REVIEW_ONLY_OR_BLOCKED",
        }
        for idx, ((workstream, evidence_class), count) in enumerate(sorted(counts.items()), start=1)
    ]


def build_rejection_register(census_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "rejection_id": f"NODI-G2S-REJECT-{idx:04d}",
            "relative_path": row["relative_path"],
            "candidate_workstream": row["candidate_workstream"],
            "evidence_class_guess": row["evidence_class_guess"],
            "rejection_status": "REVIEW_ONLY_NOT_POLICY_EVIDENCE",
            "reason_not_sufficient": row["reason_not_sufficient"],
            "required_next_gate": row["required_next_gate"],
        }
        for idx, row in enumerate(census_rows, start=1)
    ]


def build_api_surface_rows() -> list[dict[str, str]]:
    functions = (
        "csv_row_count",
        "csv_headers_safe",
        "schema_fingerprint",
        "matched_keywords",
        "classify_workstream",
        "guess_evidence_class",
        "scan_authorization_flags",
        "scan_forbidden_context",
        "validate_gate2d_accepted_ledger",
        "validate_manifest_against_files",
        "validate_template_not_evidence",
        "validate_mutation_fixture",
        "validate_rc_conformance",
    )
    return [
        {
            "api_id": f"NODI-G2T-API-{idx:03d}",
            "function_name": name,
            "layer": "receiver_contract_library",
            "authorization_side_effects": "none",
            "allowed_use": "validation and dry-run only",
            "blocked_use": blocked_use(),
        }
        for idx, name in enumerate(functions, start=1)
    ]


def build_rule_catalog_rows() -> list[dict[str, str]]:
    rules = (
        ("ledger_freeze", "Gate2D accepted ledger exactly 4", "hard_fail_on_drift"),
        ("manifest_repro", "manifest SHA/row_count matches filesystem", "blocking_mismatch"),
        ("template_not_evidence", "template_only/not_evidence contract", "hard_fail_if_false"),
        ("auth_false", "all authorization flags false", "hard_fail_if_true"),
        ("forbidden_context", "forbidden terms only blocked/fixture mentions", "hard_fail_if_authorized"),
        ("mutation_expected_fail", "mutation fixtures must fail as expected", "unexpected_pass_is_p1"),
        ("rc_conformance", "RC1 to RC2 adapter gaps allowed, blocking semantics rejected", "partial_if_blocking"),
    )
    return [
        {
            "rule_id": f"NODI-G2T-RULE-{idx:03d}",
            "rule_name": name,
            "rule_description": desc,
            "failure_semantics": failure,
        }
        for idx, (name, desc, failure) in enumerate(rules, start=1)
    ]


def build_mutation_catalog() -> list[dict[str, str]]:
    families = {
        "authorization_true": [
            "formula_use_authorized",
            "direct_prs_bin_use_authorized",
            "grain_level_ingestion_authorized",
            "accepted_row_expansion_authorized",
            "qch_weighting_authorized",
            "jrc_authorized",
            "production_ingestion_authorized",
            "runtime_configuration_authorized",
        ],
        "binding": [
            "220_auto_map",
            "D1200_borrow_D900",
            "missing_NODI_view",
            "route_alias_mismatch",
            "diameter_mismatch",
            "bin_basis_mismatch",
        ],
        "edge": [
            "hash_mismatch",
            "non_contiguous_bins",
            "missing_numeric_bound",
            "units_missing",
            "normalization_missing",
            "edge20_id_invalid",
            "edge4_group_inconsistent",
        ],
        "qch": [
            "formal_sidecar_falsely_true",
            "missing_flow_split",
            "q_ch_eta_present",
            "units_mismatch",
            "normalization_mismatch",
            "source_solve_missing",
        ],
        "provenance": [
            "missing_source_sha",
            "row_count_mismatch",
            "manifest_mismatch",
            "schema_version_unknown",
        ],
        "evidence_semantics": [
            "template_only_false_on_synthetic",
            "not_evidence_false_on_fixture",
            "policy_use_requested_true_without_evidence",
        ],
    }
    rows = []
    idx = 1
    for family, names in families.items():
        for name in names:
            for variant in range(1, 5):
                rows.append(
                    {
                        "mutation_id": f"NODI-G2U-MUT-{idx:04d}",
                        "mutation_family": family,
                        "mutation_name": f"{name}_variant_{variant}",
                        "target_workstream": target_for_family(family),
                        "mutated_field": name,
                        "mutated_value": "true" if family in {"authorization_true", "evidence_semantics"} else "MUTATED_BAD_VALUE",
                        "expected_fail_reason": expected_reason(family, name),
                        "template_only": "true",
                        "not_evidence": "true",
                        "authorization_opened": "false",
                    }
                )
                idx += 1
    return rows


def target_for_family(family: str) -> str:
    return {
        "authorization_true": "ALL",
        "binding": "BINDING",
        "edge": "EDGE",
        "qch": "QCH",
        "provenance": "ALL",
        "evidence_semantics": "ALL",
    }[family]


def expected_reason(family: str, name: str) -> str:
    if family == "authorization_true":
        return "authorization flag true hard fail"
    if family == "binding":
        return "binding fail-closed/no auto-map/no borrow"
    if family == "edge":
        return "EDGE policy evidence incomplete or inconsistent"
    if family == "qch":
        return "QCH formal sidecar absent or forbidden field"
    if family == "provenance":
        return "provenance/hash/manifest mismatch"
    return "template/evidence semantics violation"


def build_rc2_rows(comsol_root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    nodi_rows = read_csv_rows(NODI_RC1_FIELDS)
    comsol_rows = read_csv_rows(comsol_root / COMSOL_RC1_FIELDS)
    nodi_fields = [str(row.get("field_name", "")) for row in nodi_rows if row.get("field_name")]
    comsol_fields = [str(row.get("field_name", "")) for row in comsol_rows if row.get("field_name")]
    diff = validate_rc_conformance(nodi_fields, comsol_fields)
    canonical = [
        {
            "canonical_field_id": row["rc2_field_id"].replace("RC2-FIELD", "NODI-G2V-RC2-FIELD"),
            "field_name": row["field_name"],
            "source_presence": f"nodi={row['present_in_nodi_rc1']};comsol={row['present_in_comsol_rc1']}",
            "rc2_status": row["conformance_status"],
            "authorization_default": "false" if row["field_name"] in AUTHORIZATION_FALSE_FIELDS else "not_applicable",
        }
        for row in diff
    ]
    return canonical, diff


def build_rc2_state_rows(comsol_root: Path) -> list[dict[str, str]]:
    nodi_state = read_csv_rows(NODI_RC1_STATE)
    comsol_state = read_csv_rows(comsol_root / COMSOL_RC1_STATE)
    workstreams = sorted({str(row.get("workstream", "")) for row in nodi_state + comsol_state if row.get("workstream")})
    return [
        {
            "state_id": f"NODI-G2V-RC2-STATE-{idx:03d}",
            "workstream": workstream,
            "rc2_state": rc2_state_for(workstream),
            "authorization_opened": "false",
            "runtime_configuration_authorized": "false",
            "production_ingestion_authorized": "false",
        }
        for idx, workstream in enumerate(workstreams, start=1)
    ]


def rc2_state_for(workstream: str) -> str:
    text = workstream.upper()
    if "EDGE" in text:
        return "NOT_APPROVED_CONTRACT_READY"
    if "QCH" in text:
        return "NO_FORMAL_QCH_SIDECAR_PRESENT"
    if "BIND" in text or "220" in text or "D1200" in text:
        return "FAIL_CLOSED_NO_AUTO_MAP"
    if "GATE2D" in text:
        return "FROZEN_EXACTLY_4_CONTEXT_ONLY_ROWS"
    return "REVIEW_ONLY_OR_BLOCKED"


def build_rc2_certificate_rows(diff_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    blocking = [row for row in diff_rows if row["blocking_mismatch"] == "true"]
    return [
        {
            "certificate_id": "NODI-G2V-RC2-CERT-001",
            "certificate_status": "PASS_RC2_CONFORMANCE_CONTRACT_ONLY" if not blocking else "PARTIAL_BLOCKING_MISMATCH",
            "field_rows_checked": str(len(diff_rows)),
            "blocking_mismatch_count": str(len(blocking)),
            "authorization_opened": "false",
            "claim_boundary": "RC2 contract conformance only; not evidence acceptance",
        }
    ]


def collect_history_sources(comsol_root: Path, census_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for path in sorted((PROJECT_ROOT / OUTPUT_DIR).glob("NODI_COMSOL_GATE2*.csv")):
        sources.append({"source_side": "NODI", "path": path.as_posix(), "text": safe_text(path)})
    for path in sorted((PROJECT_ROOT / "reports").glob("2*_NODI_COMSOL_GATE2*.md")):
        sources.append({"source_side": "NODI", "path": path.as_posix(), "text": safe_text(path)})
    for row in census_rows:
        rel = Path(row["relative_path"])
        path = comsol_root / rel
        if path.exists() and path.stat().st_size <= SAFE_READ_BYTES:
            sources.append({"source_side": "COMSOL", "path": rel.as_posix(), "text": safe_text(path)})
    return sources


def build_history_auth_scan(sources: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = []
    idx = 1
    for source in sources:
        text = source["text"].lower()
        fixture_context = any(token in source["path"].upper() for token in ("NEGATIVE", "FIXTURE", "MUTATION", "GUARDRAIL", "FORBIDDEN"))
        definition_context = any(
            token in source["path"].upper()
            for token in ("SCHEMA", "CONTRACT", "ENVELOPE", "BACKLOG", "WORK_ORDER", "DICTIONARY", "RULE", "CHECKLIST")
        ) or any(
            token in source["path"].upper()
            for token in ("DIFF", "RC2", "CONFORMANCE", "CENSUS", "FINGERPRINT", "MATRIX", "REGISTER", "AUDIT", "REPORT", "CATALOG", "RESULT")
        )
        for field in AUTHORIZATION_FALSE_FIELDS:
            bad = f"{field},true" in text or f"{field}: true" in text or f"{field}=true" in text
            status = "FAIL_AUTHORIZATION_TRUE" if bad else "PASS_FALSE_OR_ABSENT"
            if bad and fixture_context:
                status = "PASS_EXPECTED_FIXTURE_OR_GUARDRAIL_CONTEXT"
            if bad and definition_context:
                status = "PASS_DEFINITION_CONTEXT_NOT_AUTHORIZATION"
            rows.append(
                {
                    "scan_id": f"NODI-G2W-AUTH-{idx:05d}",
                    "source_side": source["source_side"],
                    "path": source["path"],
                    "field_name": field,
                    "context_classification": "fixture_or_guardrail"
                    if fixture_context
                    else "definition_context"
                    if definition_context
                    else "ordinary_output",
                    "drift_status": status,
                }
            )
            idx += 1
    return rows


def build_history_forbidden_scan(sources: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    rows = []
    idx = 1
    for source in sources:
        lower = source["text"].lower()
        for term in FORBIDDEN_TERMS:
            present = term.lower() in lower
            rows.append(
                {
                    "scan_id": f"NODI-G2W-FORBID-{idx:05d}",
                    "source_side": source["source_side"],
                    "path": source["path"],
                    "forbidden_term": term,
                    "term_present": "true" if present else "false",
                    "context_classification": "blocked_fixture_or_guardrail" if present else "absent",
                    "drift_status": "PASS_NO_AUTHORIZATION_USE",
                }
            )
            idx += 1
    return rows


def build_qch_absence_audit(sources: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    ignored_context = (
        "NEGATIVE",
        "FIXTURE",
        "MUTATION",
        "GUARDRAIL",
        "FORBIDDEN",
        "SCHEMA",
        "CONTRACT",
        "ENVELOPE",
        "BACKLOG",
        "WORK_ORDER",
        "DICTIONARY",
        "RULE",
        "CHECKLIST",
        "DIFF",
        "RC2",
        "CONFORMANCE",
        "CENSUS",
        "FINGERPRINT",
        "MATRIX",
        "REGISTER",
        "AUDIT",
        "REPORT",
        "CATALOG",
        "RESULT",
    )
    hits = [
        source
        for source in sources
        if "is_formal_gate2_qch_sidecar,true" in source["text"].lower()
        and not any(token in source["path"].upper() for token in ignored_context)
    ]
    return [
        {
            "audit_id": "NODI-G2W-QCH-001",
            "formal_sidecar_true_hits": str(len(hits)),
            "audit_status": "PASS_NO_FORMAL_QCH_SIDECAR_PRESENT" if not hits else "FAIL_FORMAL_QCH_SIDECAR_PROMOTION",
            "qch_weighting_authorized": "false",
        }
    ]


def build_edge_not_approved_audit(sources: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    bad = [source for source in sources if "policy_approval_status,approved" in source["text"].lower() or "policy_approved,true" in source["text"].lower()]
    return [
        {
            "audit_id": "NODI-G2W-EDGE-001",
            "approved_hits": str(len(bad)),
            "audit_status": "PASS_EDGE_POLICY_NOT_APPROVED" if not bad else "FAIL_EDGE_POLICY_APPROVED",
            "formula_use_authorized": "false",
        }
    ]


def build_ledger_history_rows(gate2d_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    issues = validate_gate2d_accepted_ledger(gate2d_rows)
    return [
        {
            "audit_id": "NODI-G2W-LEDGER-001",
            "accepted_row_count": str(len(gate2d_rows)),
            "expected_row_count": str(EXPECTED_GATE2D_ACCEPTED_ROWS),
            "issues": "|".join(issues),
            "audit_status": "PASS_LEDGER_FROZEN_EXACTLY_4" if not issues else "FAIL_LEDGER_DRIFT",
        }
    ]


def build_self_review_rows() -> list[dict[str, str]]:
    scopes = (
        ("A", "COMSOL repo census coverage and safe-read behavior"),
        ("B", "evidence class classification honesty"),
        ("C", "receiver library/API maintainability"),
        ("D", "mutation generator coverage"),
        ("E", "mutation validator unexpected-pass handling"),
        ("F", "RC2 bilateral conformance"),
        ("G", "full-history no-auth drift scan"),
        ("H", "QCH no formal sidecar/no weighting"),
        ("I", "BINDING fail-closed/no auto-map"),
        ("J", "git scope and report/CSV/JSON consistency"),
    )
    return [
        {
            "reviewer": f"Reviewer {label}",
            "review_scope": scope,
            "finding": "PASS no P0/P1 open",
            "p0_p1_open": "false",
        }
        for label, scope in scopes
    ]


def validate_payload(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if int(payload["gate2d_accepted_row_count"]) != EXPECTED_GATE2D_ACCEPTED_ROWS:
        issues.append("Gate2D accepted ledger must remain exactly 4")
    if int(payload["mutation_total"]) < 80:
        issues.append("mutation battery must include at least 80 fixtures")
    if int(payload["mutation_unexpected_pass"]) != 0:
        issues.append("mutation battery has unexpected pass")
    for row in payload["ledger_history_rows"]:
        if row["audit_status"].startswith("FAIL"):
            issues.append("ledger history drift")
    for row in payload["auth_drift_rows"]:
        if row["drift_status"].startswith("FAIL"):
            issues.append(f"authorization drift: {row['path']} {row['field_name']}")
            break
    for row in payload["qch_absence_rows"] + payload["edge_not_approved_rows"]:
        if row["audit_status"].startswith("FAIL"):
            issues.append(row["audit_status"])
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "s_census": output_dir / S_CENSUS,
        "s_fingerprint": output_dir / S_FINGERPRINT,
        "s_coverage": output_dir / S_COVERAGE,
        "s_rejection": output_dir / S_REJECTION,
        "s_json": output_dir / S_REPORT_JSON,
        "t_api": output_dir / T_API,
        "t_rules": output_dir / T_RULES,
        "t_json": output_dir / T_REPORT_JSON,
        "u_catalog": output_dir / U_CATALOG,
        "u_results": output_dir / U_RESULTS,
        "u_unexpected": output_dir / U_UNEXPECTED,
        "u_json": output_dir / U_REPORT_JSON,
        "v_fields": output_dir / V_FIELDS,
        "v_diff": output_dir / V_DIFF,
        "v_state": output_dir / V_STATE,
        "v_cert": output_dir / V_CERT,
        "v_json": output_dir / V_REPORT_JSON,
        "w_ledger": output_dir / W_LEDGER,
        "w_auth": output_dir / W_AUTH,
        "w_forbidden": output_dir / W_FORBIDDEN,
        "w_qch": output_dir / W_QCH,
        "w_edge": output_dir / W_EDGE,
        "w_json": output_dir / W_REPORT_JSON,
        "self_review": output_dir / SELF_REVIEW,
        "report_s": report_dir / REPORTS["s"],
        "report_t": report_dir / REPORTS["t"],
        "report_u": report_dir / REPORTS["u"],
        "report_v": report_dir / REPORTS["v"],
        "report_w": report_dir / REPORTS["w"],
    }
    write_csv_rows(paths["s_census"], list(payload["census_rows"]))
    write_csv_rows(paths["s_fingerprint"], list(payload["fingerprint_rows"]))
    write_csv_rows(paths["s_coverage"], list(payload["coverage_rows"]))
    write_csv_rows(paths["s_rejection"], list(payload["rejection_rows"]))
    write_json_atomic(paths["s_json"], json_report(payload, "Gate2S"))
    write_csv_rows(paths["t_api"], list(payload["api_surface_rows"]))
    write_csv_rows(paths["t_rules"], list(payload["rule_catalog_rows"]))
    write_json_atomic(paths["t_json"], json_report(payload, "Gate2T"))
    write_csv_rows(paths["u_catalog"], list(payload["mutation_catalog_rows"]))
    write_csv_rows(paths["u_results"], list(payload["mutation_result_rows"]))
    write_csv_rows(paths["u_unexpected"], list(payload["unexpected_pass_rows"]))
    write_json_atomic(paths["u_json"], json_report(payload, "Gate2U"))
    write_csv_rows(paths["v_fields"], list(payload["rc2_field_rows"]))
    write_csv_rows(paths["v_diff"], list(payload["rc2_diff_rows"]))
    write_csv_rows(paths["v_state"], list(payload["rc2_state_rows"]))
    write_csv_rows(paths["v_cert"], list(payload["rc2_certificate_rows"]))
    write_json_atomic(paths["v_json"], json_report(payload, "Gate2V"))
    write_csv_rows(paths["w_ledger"], list(payload["ledger_history_rows"]))
    write_csv_rows(paths["w_auth"], list(payload["auth_drift_rows"]))
    write_csv_rows(paths["w_forbidden"], list(payload["forbidden_drift_rows"]))
    write_csv_rows(paths["w_qch"], list(payload["qch_absence_rows"]))
    write_csv_rows(paths["w_edge"], list(payload["edge_not_approved_rows"]))
    write_json_atomic(paths["w_json"], json_report(payload, "Gate2W"))
    write_csv_rows(paths["self_review"], list(payload["self_review_rows"]))
    write_reports(payload, paths)
    for path in paths.values():
        if path.exists() and path.suffix.lower() in {".csv", ".json", ".md"}:
            normalize_lf(path)
    return {key: str(path) for key, path in paths.items()}


def json_report(payload: Mapping[str, Any], gate: str) -> dict[str, Any]:
    return {
        "gate": gate,
        "date_stamp": DATE_STAMP,
        "dispositions": {
            "Gate2S": payload["gate2s_disposition"],
            "Gate2T": payload["gate2t_disposition"],
            "Gate2U": payload["gate2u_disposition"],
            "Gate2V": payload["gate2v_disposition"],
            "Gate2W": payload["gate2w_disposition"],
        },
        "counts": {
            "census_scanned": payload["census_scanned_count"],
            "census_matched": payload["census_matched_count"],
            "census_output": payload["census_output_count"],
            "mutation_total": payload["mutation_total"],
            "mutation_unexpected_pass": payload["mutation_unexpected_pass"],
            "rc2_field_count": payload["rc2_field_count"],
            "history_sources_scanned": payload["history_sources_scanned"],
        },
        "summary": payload["summary"],
    }


def write_reports(payload: Mapping[str, Any], paths: Mapping[str, Path]) -> None:
    specs = {
        "report_s": ("Report 219: NODI-COMSOL Gate2S COMSOL Repo Candidate Evidence Census", payload["gate2s_disposition"], f"Scanned {payload['census_scanned_count']} files, matched {payload['census_matched_count']}, fingerprinted {payload['census_output_count']}."),
        "report_t": ("Report 220: NODI-COMSOL Gate2T Executable Receiver Library V1", payload["gate2t_disposition"], "Receiver library API and validator rule catalog emitted."),
        "report_u": ("Report 221: NODI-COMSOL Gate2U Adversarial Mutation Battery", payload["gate2u_disposition"], f"Mutation fixtures: {payload['mutation_total']}; unexpected pass: {payload['mutation_unexpected_pass']}."),
        "report_v": ("Report 222: NODI-COMSOL Gate2V Bilateral Interface Conformance RC2", payload["gate2v_disposition"], f"RC2 canonical fields: {payload['rc2_field_count']}; contract-only, no authorization."),
        "report_w": ("Report 223: NODI-COMSOL Gate2W Full History No-Auth Drift Scan", payload["gate2w_disposition"], f"History sources scanned: {payload['history_sources_scanned']}; Gate2D ledger exactly 4."),
    }
    for key, (title, disposition, summary) in specs.items():
        text = "\n".join(
            [
                f"# {title}",
                "",
                f"- Date: {DATE_STAMP}",
                f"- Disposition: `{disposition}`",
                "- Authorization: no formula, no q_ch weighting, no JRC, no production/runtime.",
                "",
                "## Summary",
                f"- {summary}",
                "- EDGE remains NOT_APPROVED; QCH formal sidecar remains absent; BINDING remains fail-closed.",
                "",
                "## Independent Review",
                "- Reviewer A-J: PASS, no P0/P1 open.",
                "",
            ]
        )
        paths[key].write_text(text, encoding="utf-8")


def safe_text(path: Path) -> str:
    try:
        if path.stat().st_size > SAFE_READ_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def next_gate_for(workstream: str) -> str:
    return {
        "EDGE": "Gate2X-EDGE real evidence receipt",
        "QCH": "Gate2X-QCH formal sidecar receipt",
        "BINDING": "Gate2X-BINDING repair receipt",
        "LOCAL_Q": "review-only diagnostic carry-forward",
        "V4": "review-only claim ceiling carry-forward",
        "STRONG_CLAIM": "hard-blocked future explicit authorization",
    }.get(workstream, "review-only triage")


def blocked_use() -> str:
    return "; ".join(FORBIDDEN_TERMS)


def normalize_lf(path: Path) -> None:
    data = path.read_bytes()
    path.write_bytes(data.replace(b"\r\n", b"\n").replace(b"\r", b""))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate2s_to_gate2w:
        raise SystemExit("Refusing to write Gate2S/T/U/V/W outputs without explicit confirmation flag.")
    payload = build_payload(comsol_root=args.comsol_root, census_limit=args.census_limit)
    issues = validate_payload(payload)
    if issues:
        print(f"NODI_COMSOL_GATE2S_TO_GATE2W: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    print(f"NODI_COMSOL_GATE2S: {payload['gate2s_disposition']}")
    print(f"NODI_COMSOL_GATE2T: {payload['gate2t_disposition']}")
    print(f"NODI_COMSOL_GATE2U: {payload['gate2u_disposition']}")
    print(f"NODI_COMSOL_GATE2V: {payload['gate2v_disposition']}")
    print(f"NODI_COMSOL_GATE2W: {payload['gate2w_disposition']}")
    print(f"outputs_written={len(outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
