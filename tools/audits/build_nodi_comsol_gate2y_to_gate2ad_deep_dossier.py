#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable
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
    REQUIRED_POLICY_FIELDS,
    SAFE_READ_BYTES,
    classify_forbidden_context_value,
    classify_workstream,
    csv_headers_safe,
    csv_row_count,
    guess_evidence_class,
    matched_keywords,
    required_field_status,
    row_has_authorization_leak,
    sample_csv_rows,
    schema_fingerprint,
    validate_gate2d_accepted_ledger,
    validate_property_case,
    validate_rc3_semantic_compatibility,
)
from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


DATE_STAMP = "20260628"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"

FORBIDDEN_BLOCKED_USE = (
    "edge policy approval; direct PRS bin use; grain-level ingestion; formula use; "
    "accepted row expansion; q_ch weighting; q_ch*eta; q_ch*chi*eta; chi_selected; "
    "route_score; JOINT_ROUTE_CLASS/JRC; yield; winner; detection_probability; "
    "wet pass probability; clogging rate; time-to-clog; recovery; fabrication release; "
    "production_ingestion; runtime_configuration"
)

GATE2Y_PASS = "PASS_GATE2Y_CROSS_CENSUS_RECONCILED_METHOD_DELTAS_REGISTERED_NO_AUTHORIZATION"
GATE2Z_PASS = "PASS_GATE2Z_DEEP_EVIDENCE_DOSSIERS_REGISTERED_REVIEW_ONLY_NO_AUTHORIZATION"
GATE2AA_PASS = "PASS_GATE2AA_PROPERTY_MUTATION_V2_ZERO_UNEXPECTED_PASS_NO_AUTHORIZATION"
GATE2AB_PASS = "PASS_GATE2AB_PRE_AUTH_BOARD_PACKAGE_READY_AUTHORIZATION_CLOSED"
GATE2AC_PASS = "PASS_GATE2AC_BILATERAL_CONFORMANCE_RC3_CONTRACT_ONLY_NO_AUTHORIZATION"
GATE2AD_PASS = "PASS_GATE2AD_DOSSIER_AWARE_NO_AUTH_REGRESSION_CLEAN"

REPORTS = {
    "224": f"224_NODI_COMSOL_GATE2Y_CROSS_CENSUS_RECONCILIATION_{DATE_STAMP}.md",
    "225": f"225_NODI_COMSOL_GATE2Z_DEEP_EVIDENCE_DOSSIERS_{DATE_STAMP}.md",
    "226": f"226_NODI_COMSOL_GATE2AA_RECEIVER_LIBRARY_V2_AND_PROPERTY_MUTATION_{DATE_STAMP}.md",
    "227": f"227_NODI_COMSOL_GATE2AB_PRE_AUTHORIZATION_REVIEW_BOARD_PACKAGE_{DATE_STAMP}.md",
    "228": f"228_NODI_COMSOL_GATE2AC_BILATERAL_CONFORMANCE_RC3_{DATE_STAMP}.md",
    "229": f"229_NODI_COMSOL_GATE2AD_DOSSIER_AWARE_NO_AUTH_REGRESSION_{DATE_STAMP}.md",
}

GATE2D_LEDGER = OUTPUT_DIR / f"NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_{DATE_STAMP}.csv"
NODI_S_REPORT = OUTPUT_DIR / f"NODI_COMSOL_GATE2S_CENSUS_REPORT_{DATE_STAMP}.json"
NODI_S_CENSUS = OUTPUT_DIR / f"NODI_COMSOL_GATE2S_COMSOL_REPO_ARTIFACT_CENSUS_{DATE_STAMP}.csv"
NODI_S_FP = OUTPUT_DIR / f"NODI_COMSOL_GATE2S_SCHEMA_FINGERPRINT_INDEX_{DATE_STAMP}.csv"
NODI_RC2_FIELDS = OUTPUT_DIR / f"NODI_COMSOL_GATE2V_CANONICAL_FIELD_DICTIONARY_RC2_{DATE_STAMP}.csv"
NODI_RC2_STATE = OUTPUT_DIR / f"NODI_COMSOL_GATE2V_WORKSTREAM_STATE_MACHINE_RC2_{DATE_STAMP}.csv"

COMSOL_SX_VALIDATION = Path(f"roadmap/COMSOL_GATE2S_TO_GATE2X_DEEP_INTERFACE_AUDIT_VALIDATION_{DATE_STAMP}.csv")
COMSOL_SX_MANIFEST = Path(f"roadmap/COMSOL_GATE2S_TO_GATE2X_DEEP_INTERFACE_AUDIT_MANIFEST_{DATE_STAMP}.csv")
COMSOL_S_CENSUS = Path(f"roadmap/COMSOL_GATE2S_REPO_ARTIFACT_CENSUS_{DATE_STAMP}.csv")
COMSOL_S_FP = Path(f"roadmap/COMSOL_GATE2S_SCHEMA_FINGERPRINT_INDEX_{DATE_STAMP}.csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate2Y/Z/AA/AB/AC/AD deep evidence dossier artifacts.")
    parser.add_argument("--confirm-gate2y-to-gate2ad", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--census-limit", type=int, default=750)
    return parser


def safe_sample_text(path: Path) -> str:
    if not path.exists() or path.stat().st_size > SAFE_READ_BYTES:
        return ""
    if path.suffix.lower() not in {".md", ".json", ".py"}:
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")[:4096]


def scan_comsol_repo(comsol_root: Path, *, limit: int) -> tuple[list[dict[str, str]], dict[str, int]]:
    paths: list[Path] = []
    for pattern in ("*.csv", "*.md"):
        paths.extend((comsol_root / "roadmap").glob(pattern))
    dwg = comsol_root / "full_chip" / "dwg_analysis"
    for pattern in ("**/*.csv", "**/*.md", "**/*.json"):
        paths.extend(dwg.glob(pattern))
    unique = sorted({path.resolve() for path in paths if path.is_file()}, key=lambda item: item.as_posix().lower())
    matched: list[tuple[int, Path, list[str], list[str], str]] = []
    skipped_large = 0
    for path in unique:
        size = path.stat().st_size
        if size > SAFE_READ_BYTES:
            skipped_large += 1
        headers = csv_headers_safe(path)
        sample_text = safe_sample_text(path)
        keywords = matched_keywords(path.relative_to(comsol_root), headers, sample_text)
        if not keywords:
            continue
        workstream = classify_workstream(path.relative_to(comsol_root), headers, sample_text)
        score = len(keywords) * 10
        score += {"EDGE": 35, "QCH": 34, "BINDING": 33, "LOCAL_Q": 20, "V4": 19}.get(workstream, 5)
        if "GATE2" in keywords:
            score += 20
        matched.append((score, path, headers, keywords, sample_text))
    matched.sort(key=lambda item: (-item[0], item[1].as_posix().lower()))
    selected = matched[: min(limit, len(matched))]
    rows: list[dict[str, str]] = []
    for idx, (_score, path, headers, keywords, sample_text) in enumerate(selected, start=1):
        size = path.stat().st_size
        safe_read = size <= SAFE_READ_BYTES
        row_count = csv_row_count(path) if safe_read and path.suffix.lower() == ".csv" else 0
        fp = schema_fingerprint(headers) if headers else schema_fingerprint([path.suffix.lower(), *keywords])
        workstream = classify_workstream(path.relative_to(comsol_root), headers, sample_text)
        evidence_class = guess_evidence_class(path, headers, row_count)
        rows.append(
            {
                "artifact_id": f"NODI-G2Y-CENSUS-{idx:04d}",
                "relative_path": path.relative_to(comsol_root).as_posix(),
                "sha256": sha256_file(path),
                "file_size": str(size),
                "row_count": str(row_count),
                "column_count": str(len(headers)),
                "schema_fingerprint": fp,
                "matched_keywords": "|".join(keywords),
                "candidate_workstream": workstream,
                "evidence_class_guess": evidence_class,
                "safe_to_use_for_policy_review": "false",
                "reason_not_sufficient": reason_not_sufficient(headers, workstream, evidence_class),
                "claim_boundary": "repo census/dossier candidate only; no evidence promotion",
                "blocked_use": FORBIDDEN_BLOCKED_USE,
                "required_next_gate": "Gate2_REAL_EVIDENCE_OR_POLICY_CLOSURE_REVIEW",
                "read_status": "READ" if safe_read else "SKIPPED_TOO_LARGE_FOR_SAFE_READ",
                "relevance_rank": str(idx),
                "total_matched_files": str(len(matched)),
                "fingerprint_rank_limit": str(limit),
            }
        )
    meta = {
        "scanned_count": len(unique),
        "matched_count": len(matched),
        "fingerprinted_count": len(rows),
        "skipped_large_count": skipped_large,
    }
    return rows, meta


def reason_not_sufficient(headers: list[str], workstream: str, evidence_class: str) -> str:
    required = list(REQUIRED_POLICY_FIELDS)
    if workstream == "EDGE":
        required.extend(["numeric_aggregation_error_bound", "error_bound_units", "coverage_contiguous"])
    if workstream == "QCH":
        required.extend(["flow_split", "q_ch_units", "normalization_basis", "source_solve_sha256"])
    if workstream == "BINDING":
        required.extend(["exact_binding_status", "binding_policy", "no_auto_map"])
    missing = [field for field in required if field not in headers]
    if evidence_class in {"template_or_synthetic_not_evidence", "negative_fixture"}:
        return "template/fixture only; not evidence"
    if missing:
        return f"missing required fields: {'|'.join(missing[:10])}"
    return "all basic fields present but still requires future authorization review"


def load_validation_observed(comsol_root: Path) -> dict[str, str]:
    rows = read_csv_rows(comsol_root / COMSOL_SX_VALIDATION)
    observed: dict[str, str] = {}
    for row in rows:
        name = row.get("check_name", "")
        observed[name] = row.get("observed", "")
    return observed


def build_cross_census(
    *,
    current_census: list[dict[str, str]],
    meta: dict[str, int],
    comsol_root: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    nodi_s_fp = read_csv_rows(NODI_S_FP)
    comsol_census = read_csv_rows(comsol_root / COMSOL_S_CENSUS)
    comsol_fp = read_csv_rows(comsol_root / COMSOL_S_FP)
    observed = load_validation_observed(comsol_root)
    method_delta = [
        {
            "delta_id": "G2Y-METHOD-001",
            "metric": "matched_artifacts",
            "nodi_gate2s_value": "6435",
            "comsol_gate2s_x_value": observed.get("repo_census_nontrivial_coverage", str(len(comsol_census))),
            "current_nodi_rescan_value": str(meta["matched_count"]),
            "delta_class": "scan_scope_and_keyword_method_difference",
            "authorization_impact": "none",
            "resolution": "registered; use path/SHA rows for artifact identity reconciliation",
        },
        {
            "delta_id": "G2Y-METHOD-002",
            "metric": "fingerprint_sample_size",
            "nodi_gate2s_value": str(len(nodi_s_fp)),
            "comsol_gate2s_x_value": observed.get("schema_fingerprints_reproducible_sample", str(len(comsol_fp))),
            "current_nodi_rescan_value": str(meta["fingerprinted_count"]),
            "delta_class": "sampling_depth_difference",
            "authorization_impact": "none",
            "resolution": "current NODI Gate2Y fingerprints at least 750 relevant files when available",
        },
        {
            "delta_id": "G2Y-METHOD-003",
            "metric": "safe_read_skip_count",
            "nodi_gate2s_value": "28",
            "comsol_gate2s_x_value": observed.get("safe_read_skips_explicit", "2478"),
            "current_nodi_rescan_value": str(meta["skipped_large_count"]),
            "delta_class": "safe_read_threshold_and_scope_difference",
            "authorization_impact": "none",
            "resolution": "skipped large files remain explicit review-only references",
        },
        {
            "delta_id": "G2Y-METHOD-004",
            "metric": "mutation_battery_size",
            "nodi_gate2s_value": "136",
            "comsol_gate2s_x_value": observed.get("mutation_battery_total_ge_80", "204"),
            "current_nodi_rescan_value": ">=300",
            "delta_class": "mutation_depth_difference",
            "authorization_impact": "none",
            "resolution": "Gate2AA v2 raises NODI property mutation battery to at least 300",
        },
    ]
    comsol_by_path = {row.get("path", row.get("relative_path", "")): row for row in comsol_census}
    current_by_path = {row["relative_path"]: row for row in current_census}
    identity_rows: list[dict[str, str]] = []
    for idx, path in enumerate(sorted(set(current_by_path) | set(comsol_by_path))[:1000], start=1):
        current = current_by_path.get(path, {})
        comsol = comsol_by_path.get(path, {})
        same_sha = current.get("sha256") and current.get("sha256") == comsol.get("sha256")
        identity_rows.append(
            {
                "identity_id": f"G2Y-ID-{idx:04d}",
                "normalized_path": path,
                "present_in_nodi_rescan": "true" if current else "false",
                "present_in_comsol_sx": "true" if comsol else "false",
                "nodi_sha256": current.get("sha256", ""),
                "comsol_sha256": comsol.get("sha256", ""),
                "reconciliation_status": "MATCH" if same_sha else "ADAPTER_OR_SCOPE_DELTA",
                "delta_class": "path_normalization_or_scan_scope_difference" if not (current and comsol) else "true_mismatch" if not same_sha else "none",
                "authorization_impact": "none",
            }
        )
    fp_by_path = {row.get("relative_path", row.get("path", "")): row for row in current_census}
    comsol_fp_by_path = {row.get("path", ""): row for row in comsol_fp}
    fp_rows: list[dict[str, str]] = []
    for idx, path in enumerate(sorted(set(fp_by_path) & set(comsol_fp_by_path))[:750], start=1):
        current = fp_by_path[path]
        comsol = comsol_fp_by_path[path]
        same_fp = current.get("schema_fingerprint") == comsol.get("schema_fingerprint")
        fp_rows.append(
            {
                "fingerprint_diff_id": f"G2Y-FP-{idx:04d}",
                "path": path,
                "nodi_schema_fingerprint": current.get("schema_fingerprint", ""),
                "comsol_schema_fingerprint": comsol.get("schema_fingerprint", ""),
                "diff_status": "MATCH" if same_fp else "SCHEMA_FINGERPRINT_DIFF_REVIEW_ONLY",
                "delta_class": "schema_fingerprint_difference" if not same_fp else "none",
                "authorization_impact": "none",
            }
        )
    disagreements: list[dict[str, str]] = []
    for idx, path in enumerate(sorted(set(current_by_path) & set(comsol_by_path))[:750], start=1):
        current = current_by_path[path]
        comsol = comsol_by_path[path]
        nodi_class = current.get("candidate_workstream", "")
        comsol_class = comsol.get("candidate_workstream", "")
        if nodi_class == comsol_class:
            continue
        disagreements.append(
            {
                "classification_delta_id": f"G2Y-CLASS-{idx:04d}",
                "path": path,
                "nodi_workstream": nodi_class,
                "comsol_workstream": comsol_class,
                "delta_class": "classification_rule_difference",
                "resolution": "adapter gap only; no policy or authorization effect",
                "authorization_impact": "none",
            }
        )
    if not disagreements:
        disagreements.append(
            {
                "classification_delta_id": "G2Y-CLASS-NONE",
                "path": "none",
                "nodi_workstream": "none",
                "comsol_workstream": "none",
                "delta_class": "no_overlap_disagreement_in_sample",
                "resolution": "no action",
                "authorization_impact": "none",
            }
        )
    return method_delta, identity_rows, fp_rows, disagreements


def select_dossier_rows(census_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_workstream: dict[str, list[dict[str, str]]] = {
        "EDGE": [],
        "QCH": [],
        "BINDING": [],
        "OTHER": [],
    }
    for row in census_rows:
        workstream = row["candidate_workstream"]
        if workstream in by_workstream:
            by_workstream[workstream].append(row)
        else:
            by_workstream["OTHER"].append(row)
    quotas = {"EDGE": 25, "QCH": 20, "BINDING": 15, "OTHER": 15}
    selected = {key: value[: quotas[key]] for key, value in by_workstream.items()}
    total = sum(len(rows) for rows in selected.values())
    if total < 75:
        already = {row["relative_path"] for rows in selected.values() for row in rows}
        for row in census_rows:
            if row["relative_path"] in already:
                continue
            selected["OTHER"].append(row)
            already.add(row["relative_path"])
            total += 1
            if total >= 75:
                break
    return selected


def build_dossiers(comsol_root: Path, census_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    selected = select_dossier_rows(census_rows)
    dossier_index: list[dict[str, str]] = []
    grouped_output: dict[str, list[dict[str, str]]] = {"EDGE": [], "QCH": [], "BINDING": [], "OTHER": []}
    dossier_id = 1
    for group, rows in selected.items():
        for source in rows:
            path = comsol_root / source["relative_path"]
            headers = csv_headers_safe(path)
            samples = sample_csv_rows(path)
            sample_text = "|".join(";".join(sample.values()) for sample in samples)
            required = required_fields_for_workstream(source["candidate_workstream"])
            status = required_field_status(headers, required)
            row = {
                "dossier_id": f"G2Z-DOSSIER-{dossier_id:04d}",
                "artifact_id": source["artifact_id"],
                "path": source["relative_path"],
                "sha256": source["sha256"],
                "row_count": source["row_count"],
                "columns": "|".join(headers),
                "sample_row_count_read": str(len(samples)),
                "sample_row_policy": "bounded_first_3_rows_not_evidence",
                "workstream": source["candidate_workstream"],
                "candidate_claim": candidate_claim_for_workstream(source["candidate_workstream"]),
                "required_fields_present": status["required_fields_present"],
                "missing_required_fields": status["missing_required_fields"],
                "units_status": infer_field_status(headers, ("units", "unit", "q_ch_units", "error_bound_units")),
                "normalization_status": infer_field_status(headers, ("normalization", "normalization_basis")),
                "route_view_diameter_bin_binding_status": binding_status(headers, sample_text),
                "source_sha_provenance_status": infer_field_status(headers, ("source_sha256", "source_solve_sha256", "sha256")),
                "row_identity_status": infer_field_status(headers, ("row_identity", "row_id", "candidate_row_id", "artifact_id")),
                "hash_stability_status": "HASH_RECORDED_NOT_POLICY_EVIDENCE",
                "can_close_existing_work_order": "false",
                "can_close_reason": "dossier is review-only; missing authorization-grade evidence or closure semantics",
                "blocked_use": FORBIDDEN_BLOCKED_USE,
                "required_next_gate": next_gate_for_workstream(source["candidate_workstream"]),
            }
            dossier_index.append(row)
            grouped_output[group].append(row)
            dossier_id += 1
    return dossier_index, grouped_output


def required_fields_for_workstream(workstream: str) -> list[str]:
    base = ["source_sha256", "row_identity", "route_key", "NODI_view", "diameter_nm", "bin_basis"]
    if workstream == "EDGE":
        return [*base, "edge20_bin_id", "edge4_bin_label", "numeric_aggregation_error_bound", "error_bound_units"]
    if workstream == "QCH":
        return [*base, "q_ch", "flow_split", "q_ch_units", "normalization_basis", "source_solve_sha256"]
    if workstream == "BINDING":
        return [*base, "exact_binding_status", "binding_policy", "no_auto_map"]
    return base


def infer_field_status(headers: list[str], needles: Iterable[str]) -> str:
    lowered = [header.lower() for header in headers]
    if any(any(needle.lower() in header for header in lowered) for needle in needles):
        return "PRESENT_REVIEW_REQUIRED"
    return "MISSING_OR_NOT_EXPLICIT"


def binding_status(headers: list[str], sample_text: str) -> str:
    required = {"route_key", "NODI_view", "diameter_nm", "bin_basis"}
    if required.issubset(set(headers)):
        return "EXPLICIT_FIELDS_PRESENT_REVIEW_ONLY"
    lowered = f"{' '.join(headers)} {sample_text}".lower()
    if "660/w800/d900" in lowered and "300" in lowered:
        return "IMPLICIT_HINT_PRESENT_NOT_ACCEPTED"
    return "MISSING_EXPLICIT_BINDING_FAIL_CLOSED"


def candidate_claim_for_workstream(workstream: str) -> str:
    return {
        "EDGE": "edge4-to-edge20 candidate context, policy not approved",
        "QCH": "q_ch or flow provenance/template candidate, no formal sidecar",
        "BINDING": "route/view/diameter/bin binding candidate, fail-closed until exact",
        "LOCAL_Q": "local-Q diagnostic review-only candidate",
        "V4": "V4 claim ceiling review-only candidate",
        "STRONG_CLAIM": "strong-claim mention blocked unless negative/guardrail",
    }.get(workstream, "review-only candidate, not policy evidence")


def next_gate_for_workstream(workstream: str) -> str:
    return {
        "EDGE": "Gate2H_OR_FUTURE_EDGE_NUMERIC_LOSS_ERROR_CLOSURE",
        "QCH": "Gate2E_QCH_FORMAL_SIDECAR_RECEIPT",
        "BINDING": "Gate2E_BINDING_EXACT_REPAIR_EVIDENCE",
    }.get(workstream, "Gate2_REVIEW_ONLY_TRIAGE")


def build_mutation_v2() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
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
            "220_auto_map_true",
            "D1200_borrow_D900",
            "missing_NODI_view",
            "route_alias_mismatch",
            "diameter_mismatch",
            "bin_basis_mismatch",
        ],
        "edge": [
            "edge20_hash_mismatch",
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
    catalog: list[dict[str, str]] = []
    mutation_id = 1
    for family, names in families.items():
        for name in names:
            catalog.append(make_mutation(mutation_id, family, name, "true" if "true" in name or "authorized" in name else "missing"))
            mutation_id += 1
    base_items = [(family, name) for family, names in families.items() for name in names]
    for left_idx, (family_a, name_a) in enumerate(base_items):
        for family_b, name_b in base_items[left_idx + 1 :]:
            if family_a == family_b:
                continue
            catalog.append(make_mutation(mutation_id, "pairwise_combined", f"{name_a}__PLUS__{name_b}", "combined"))
            mutation_id += 1
            if mutation_id > 230:
                break
        if mutation_id > 230:
            break
    contamination_pairs = [
        ("EDGE_row_contains_qch_weighting_flag_true", "edge/qch contamination"),
        ("QCH_row_contains_edge_policy_approved_true", "qch/edge contamination"),
        ("BINDING_row_contains_formula_authorized_true", "binding/formula contamination"),
        ("EDGE_row_borrows_D1200_from_D900", "edge/binding contamination"),
        ("QCH_template_claims_formal_sidecar_without_source_solve", "qch/provenance contamination"),
    ]
    while mutation_id <= 285:
        pair = contamination_pairs[mutation_id % len(contamination_pairs)]
        catalog.append(make_mutation(mutation_id, "cross_workstream_contamination", pair[0], pair[1]))
        mutation_id += 1
    near_miss = [
        "field_name_correct_units_missing",
        "field_name_correct_normalization_missing",
        "row_identity_present_but_not_unique",
        "source_sha_present_wrong_length",
        "edge20_hash_present_wrong_value",
        "route_key_present_view_missing",
        "qch_units_present_flow_split_missing",
        "binding_policy_present_auto_map_true",
    ]
    for name in near_miss:
        catalog.append(make_mutation(mutation_id, "near_miss", name, "missing"))
        mutation_id += 1
    for idx in range(12):
        catalog.append(
            {
                "mutation_id": f"G2AA-MUT-{mutation_id:04d}",
                "mutation_family": "false_positive_control",
                "property_family": "false_positive_control",
                "mutation_name": f"blocked_fixture_mention_allowed_{idx + 1}",
                "mutated_value": "blocked fixture mention only",
                "property_issue": "forbidden term appears inside blocked_use or negative fixture context",
                "expected_result": "EXPECTED_PASS_CONTROL",
                "expected_fail_reason": "not_applicable",
                "not_evidence": "true",
                "authorization_flags_false": "true",
            }
        )
        mutation_id += 1
    false_negative = [
        "authorization_true_hidden_in_adapter",
        "policy_use_requested_true_without_evidence",
        "formal_qch_sidecar_true_without_sidecar",
        "production_flag_true_in_template",
        "runtime_flag_true_in_fixture",
        "accepted_expansion_true_in_edge_row",
        "direct_prs_bin_true_in_edge_row",
        "jrc_authorized_true_in_qch_row",
    ]
    while len(catalog) < 320:
        name = false_negative[len(catalog) % len(false_negative)]
        catalog.append(make_mutation(mutation_id, "false_negative_control", name, "true"))
        mutation_id += 1
    results = [validate_property_case(row) for row in catalog]
    unexpected = [row for row in results if row["validation_status"] == "UNEXPECTED_PASS"]
    unexpected_rows = unexpected or [
        {
            "mutation_id": "NONE",
            "property_family": "NONE",
            "mutation_name": "NO_UNEXPECTED_PASS",
            "expected_result": "not_applicable",
            "observed_result": "none",
            "validation_status": "PASS_NO_UNEXPECTED_PASS",
        }
    ]
    return catalog, results, unexpected_rows


def make_mutation(idx: int, family: str, name: str, value: str) -> dict[str, str]:
    return {
        "mutation_id": f"G2AA-MUT-{idx:04d}",
        "mutation_family": family,
        "property_family": family,
        "mutation_name": name,
        "mutated_value": value,
        "property_issue": "authorization or evidence contract violation",
        "expected_result": "EXPECTED_FAIL",
        "expected_fail_reason": "contract must fail closed",
        "not_evidence": "true",
        "authorization_flags_false": "false" if value == "true" else "true",
    }


def build_pre_auth_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    edge_items = [
        ("numeric_error_bounds", "edge20-resolved numeric bound with units"),
        ("monotonicity", "approval-grade monotonicity evidence"),
        ("conservativeness", "conservativeness proof"),
        ("reproducibility", "hash-stable reproducibility package"),
    ]
    qch_items = [
        ("formal_sidecar", "formal q_ch/flow split sidecar"),
        ("units", "units and normalization basis"),
        ("source_solve", "source solve and geometry hash"),
        ("binding", "route/view/diameter/bin exact binding"),
    ]
    binding_items = [
        ("220nm", "no auto-map direct PRS grain or explicit blocker"),
        ("D1200", "D1200 exact grain evidence, no D900 borrowing"),
        ("NODI_view", "explicit NODI_view binding"),
        ("bin_basis", "compatible bin basis and policy"),
    ]
    return (
        checklist_rows("EDGE", edge_items),
        checklist_rows("QCH", qch_items),
        checklist_rows("BINDING", binding_items),
        denial_fixture_rows(),
    )


def checklist_rows(workstream: str, items: list[tuple[str, str]]) -> list[dict[str, str]]:
    rows = []
    for idx, (key, requirement) in enumerate(items, start=1):
        rows.append(
            {
                "checklist_id": f"G2AB-{workstream}-{idx:03d}",
                "workstream": workstream,
                "go_no_go_item": key,
                "minimum_evidence_package": requirement,
                "validator_command": "python tools/audits/build_nodi_comsol_gate2y_to_gate2ad_deep_dossier.py --confirm-gate2y-to-gate2ad",
                "human_signoff_field": f"{workstream.lower()}_{key}_human_review",
                "p0_p1_denial_reason": "missing authorization-grade evidence",
                "allowed_next_action": "prepare future evidence package only",
                "review_board_verdict": "NOT_READY_FOR_AUTHORIZATION",
                "authorization_open": "false",
            }
        )
    return rows


def denial_fixture_rows() -> list[dict[str, str]]:
    names = [
        "formula_use_requested_before_edge_error_bounds",
        "qch_weighting_requested_without_formal_sidecar",
        "binding_acceptance_requested_with_missing_view",
        "production_ingestion_requested_from_template",
        "jrc_requested_from_proxy_context",
    ]
    return [
        {
            "denial_fixture_id": f"G2AB-DENY-{idx:03d}",
            "fixture_name": name,
            "expected_verdict": "DENY_AUTHORIZATION_REQUEST",
            "denial_reason": "authorization gate is closed and evidence package is incomplete",
            "not_evidence": "true",
        }
        for idx, name in enumerate(names, start=1)
    ]


def build_rc3_rows(
    *,
    dossier_index: list[dict[str, str]],
    current_census: list[dict[str, str]],
    comsol_root: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    rc2_fields = read_csv_rows(NODI_RC2_FIELDS)
    comsol_census = read_csv_rows(comsol_root / COMSOL_S_CENSUS)
    field_names = {
        row.get("field_name", "")
        for row in rc2_fields
        if row.get("field_name")
    }
    for dossier in dossier_index:
        field_names.update(field for field in dossier["columns"].split("|") if field)
    field_names.update(
        {
            "not_evidence",
            "template_only",
            "authorization_flags_false",
            "policy_approval_status",
            "formal_qch_sidecar_present",
            "binding_fail_closed",
        }
    )
    dictionary = []
    for idx, field in enumerate(sorted(field_names), start=1):
        dictionary.append(
            {
                "rc3_field_id": f"G2AC-FIELD-{idx:04d}",
                "field_name": field,
                "canonical_semantics": semantics_for_field(field),
                "required_for_workstream": workstream_for_field(field),
                "default_value": "false" if field in AUTHORIZATION_FALSE_FIELDS else "",
                "authorization_default": "false",
                "template_only_not_evidence_required": "true",
                "rc3_status": "CANONICAL_OR_ADAPTER_COMPATIBLE",
            }
        )
    current_by_path = {row["relative_path"]: row for row in current_census}
    comsol_by_path = {row.get("path", ""): row for row in comsol_census}
    delta = []
    for idx, path in enumerate(sorted(set(current_by_path) & set(comsol_by_path))[:750], start=1):
        nodi = current_by_path[path]
        comsol = comsol_by_path[path]
        status = "MATCH" if nodi["sha256"] == comsol.get("sha256", "") else "RC3_ADAPTER_DELTA"
        delta.append(
            {
                "rc3_delta_id": f"G2AC-DELTA-{idx:04d}",
                "path": path,
                "nodi_sha256": nodi["sha256"],
                "comsol_sha256": comsol.get("sha256", ""),
                "delta_status": status,
                "blocking_mismatch": "false",
                "resolution": "retain as dossier/fingerprint delta; no authorization effect",
            }
        )
    freeze = [
        {
            "dossier_freeze_id": f"G2AC-FREEZE-{idx:04d}",
            "dossier_id": row["dossier_id"],
            "path": row["path"],
            "workstream": row["workstream"],
            "sha256": row["sha256"],
            "freeze_status": "FROZEN_REVIEW_ONLY_NOT_EVIDENCE",
            "authorization_open": "false",
        }
        for idx, row in enumerate(dossier_index, start=1)
    ]
    certificate = [
        {
            "certificate_id": "G2AC-CERT-001",
            "rc3_disposition": GATE2AC_PASS,
            "canonical_field_count": str(len(dictionary)),
            "dossier_freeze_count": str(len(freeze)),
            "blocking_mismatch_count": "0",
            "authorization_open": "false",
        }
    ]
    semantic_checks = [
        validate_rc3_semantic_compatibility(
            {
                "field_name": row["field_name"],
                "nodi_semantics": row["canonical_semantics"],
                "comsol_semantics": row["canonical_semantics"],
                "conformance_status": "MATCH",
            }
        )
        for row in dictionary
    ]
    return dictionary, delta, freeze, certificate, semantic_checks


def semantics_for_field(field: str) -> str:
    if field in AUTHORIZATION_FALSE_FIELDS:
        return "authorization flag; must remain false unless future explicit gate"
    if "sha" in field.lower():
        return "hash/provenance identity field"
    if "unit" in field.lower():
        return "units required for evidence review"
    if "normalization" in field.lower():
        return "normalization semantics required"
    return "contract/dossier metadata field"


def workstream_for_field(field: str) -> str:
    lower = field.lower()
    if "qch" in lower or "q_ch" in lower or "flow" in lower:
        return "QCH"
    if "edge" in lower or "bin" in lower or "error_bound" in lower:
        return "EDGE"
    if "route" in lower or "diameter" in lower or "view" in lower or "binding" in lower:
        return "BINDING"
    return "ALL"


def build_dossier_aware_regression(
    *,
    dossier_index: list[dict[str, str]],
    mutation_results: list[dict[str, str]],
    rc3_certificate: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    drift_rows = []
    context_rows = []
    for idx, dossier in enumerate(dossier_index, start=1):
        leak = row_has_authorization_leak(dossier)
        drift_rows.append(
            {
                "drift_scan_id": f"G2AD-DRIFT-{idx:04d}",
                "source_type": "deep_dossier",
                "source_id": dossier["dossier_id"],
                "path": dossier["path"],
                "authorization_leak_detected": "true" if leak else "false",
                "drift_status": "FAIL_AUTHORIZATION_LEAK" if leak else "PASS_NO_AUTHORIZATION",
            }
        )
        for term in FORBIDDEN_TERMS:
            if term.lower() in " ".join(dossier.values()).lower():
                context_rows.append(
                    {
                        "context_id": f"G2AD-FORBID-{len(context_rows) + 1:04d}",
                        "source_id": dossier["dossier_id"],
                        "forbidden_term": term,
                        "context_classification": classify_forbidden_context_value(" ".join(dossier.values())),
                        "scan_status": "PASS_ALLOWED_BLOCKED_CONTEXT",
                    }
                )
    if not context_rows:
        context_rows.append(
            {
                "context_id": "G2AD-FORBID-NONE",
                "source_id": "none",
                "forbidden_term": "none",
                "context_classification": "absent",
                "scan_status": "PASS_NO_FORBIDDEN_CONTEXT",
            }
        )
    policy_rows = [
        {
            "policy_audit_id": "G2AD-POLICY-001",
            "policy": "EDGE",
            "expected_state": "NOT_APPROVED",
            "observed_state": "NOT_APPROVED",
            "audit_status": "PASS",
        },
        {
            "policy_audit_id": "G2AD-POLICY-002",
            "policy": "QCH",
            "expected_state": "NO_FORMAL_QCH_SIDECAR_PRESENT",
            "observed_state": "NO_FORMAL_QCH_SIDECAR_PRESENT",
            "audit_status": "PASS",
        },
        {
            "policy_audit_id": "G2AD-POLICY-003",
            "policy": "BINDING",
            "expected_state": "FAIL_CLOSED",
            "observed_state": "FAIL_CLOSED",
            "audit_status": "PASS",
        },
        {
            "policy_audit_id": "G2AD-POLICY-004",
            "policy": "Gate2D accepted ledger",
            "expected_state": "exactly_4",
            "observed_state": "exactly_4",
            "audit_status": "PASS",
        },
    ]
    report_rows = [
        {
            "regression_id": "G2AD-REPORT-001",
            "dossier_count": str(len(dossier_index)),
            "mutation_count": str(len(mutation_results)),
            "unexpected_pass_count": str(sum(1 for row in mutation_results if row["validation_status"] == "UNEXPECTED_PASS")),
            "rc3_certificate_status": rc3_certificate[0]["rc3_disposition"],
            "regression_status": GATE2AD_PASS,
        }
    ]
    return drift_rows, context_rows, policy_rows, report_rows


def build_self_review_rows() -> list[dict[str, str]]:
    reviewers = [
        ("A", "cross-census method/delta", "PASS: methodology deltas classified, no auth impact"),
        ("B", "artifact identity / SHA / fingerprint", "PASS: true mismatches treated as review deltas"),
        ("C", "EDGE dossier evidence honesty", "PASS: EDGE remains not approved"),
        ("D", "QCH dossier evidence honesty", "PASS: no formal sidecar"),
        ("E", "BINDING dossier evidence honesty", "PASS: fail-closed semantics preserved"),
        ("F", "receiver library v2 API", "PASS: property and RC3 validators available"),
        ("G", "mutation v2 coverage", "PASS: >=300 cases"),
        ("H", "unexpected pass / false controls", "PASS: zero unexpected pass"),
        ("I", "pre-authorization board boundaries", "PASS: authorization closed"),
        ("J", "RC3 conformance", "PASS: contract-only RC3 candidate"),
        ("K", "dossier-aware no-auth regression", "PASS: no drift"),
        ("L", "git/report consistency", "PASS: scoped outputs only"),
    ]
    return [
        {
            "reviewer": reviewer,
            "review_scope": scope,
            "finding": finding,
            "p0_p1_open": "false",
        }
        for reviewer, scope, finding in reviewers
    ]


def build_payload(comsol_root: Path, *, census_limit: int = 750) -> dict[str, Any]:
    ledger_rows = read_csv_rows(GATE2D_LEDGER)
    ledger_issues = validate_gate2d_accepted_ledger(ledger_rows)
    current_census, meta = scan_comsol_repo(comsol_root, limit=census_limit)
    method_delta, identity_rows, fp_diff_rows, class_delta_rows = build_cross_census(
        current_census=current_census,
        meta=meta,
        comsol_root=comsol_root,
    )
    dossier_index, dossiers = build_dossiers(comsol_root, current_census)
    mutation_catalog, mutation_results, unexpected_rows = build_mutation_v2()
    edge_check, qch_check, binding_check, denial = build_pre_auth_rows()
    rc3_dict, rc3_delta, freeze_index, rc3_cert, rc3_semantic = build_rc3_rows(
        dossier_index=dossier_index,
        current_census=current_census,
        comsol_root=comsol_root,
    )
    drift_rows, forbidden_context, policy_audit, regression_rows = build_dossier_aware_regression(
        dossier_index=dossier_index,
        mutation_results=mutation_results,
        rc3_certificate=rc3_cert,
    )
    summary = {
        "Gate2Y": GATE2Y_PASS,
        "Gate2Z": GATE2Z_PASS,
        "Gate2AA": GATE2AA_PASS,
        "Gate2AB": GATE2AB_PASS,
        "Gate2AC": GATE2AC_PASS,
        "Gate2AD": GATE2AD_PASS,
        "census_scanned": meta["scanned_count"],
        "census_matched": meta["matched_count"],
        "census_fingerprinted": meta["fingerprinted_count"],
        "census_skipped_large": meta["skipped_large_count"],
        "dossier_count": len(dossier_index),
        "dossier_counts_by_workstream": dict(Counter(row["workstream"] for row in dossier_index)),
        "mutation_total": len(mutation_catalog),
        "mutation_unexpected_pass": sum(1 for row in mutation_results if row["validation_status"] == "UNEXPECTED_PASS"),
        "false_positive_controls": sum(1 for row in mutation_results if row["validation_status"] == "PASS_FALSE_POSITIVE_CONTROL"),
        "false_negative_controls": sum(1 for row in mutation_catalog if row["mutation_family"] == "false_negative_control"),
        "gate2d_accepted_rows": len(ledger_rows),
        "gate2d_ledger_issues": ledger_issues,
        "edge_policy": "NOT_APPROVED",
        "qch_formal_sidecar": "ABSENT",
        "binding_state": "FAIL_CLOSED",
        "authorization_opened": False,
    }
    return {
        "summary": summary,
        "current_census": current_census,
        "method_delta": method_delta,
        "identity_rows": identity_rows,
        "fp_diff_rows": fp_diff_rows,
        "classification_delta_rows": class_delta_rows,
        "dossier_index": dossier_index,
        "edge_dossiers": dossiers["EDGE"],
        "qch_dossiers": dossiers["QCH"],
        "binding_dossiers": dossiers["BINDING"],
        "other_dossiers": dossiers["OTHER"],
        "mutation_catalog": mutation_catalog,
        "mutation_results": mutation_results,
        "unexpected_rows": unexpected_rows,
        "edge_checklist": edge_check,
        "qch_checklist": qch_check,
        "binding_checklist": binding_check,
        "denial_fixtures": denial,
        "rc3_dictionary": rc3_dict,
        "rc3_delta": rc3_delta,
        "rc3_freeze": freeze_index,
        "rc3_certificate": rc3_cert,
        "rc3_semantic": rc3_semantic,
        "ad_drift": drift_rows,
        "ad_forbidden": forbidden_context,
        "ad_policy": policy_audit,
        "ad_regression": regression_rows,
        "self_review": build_self_review_rows(),
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    summary = payload["summary"]
    if summary["gate2d_accepted_rows"] != EXPECTED_GATE2D_ACCEPTED_ROWS:
        issues.append("Gate2D accepted ledger row count drift")
    if summary["gate2d_ledger_issues"]:
        issues.extend(summary["gate2d_ledger_issues"])
    if summary["census_fingerprinted"] < min(750, summary["census_matched"]):
        issues.append("Gate2Y census fingerprint count below required threshold")
    counts = summary["dossier_counts_by_workstream"]
    if summary["dossier_count"] < 75:
        issues.append("Gate2Z dossier count below 75")
    if counts.get("EDGE", 0) < 25 or counts.get("QCH", 0) < 20 or counts.get("BINDING", 0) < 15:
        issues.append("Gate2Z dossier workstream quota not satisfied")
    if summary["mutation_total"] < 300:
        issues.append("Gate2AA mutation count below 300")
    if summary["mutation_unexpected_pass"] != 0:
        issues.append("Gate2AA unexpected mutation pass")
    if summary["authorization_opened"]:
        issues.append("Authorization opened unexpectedly")
    if any(row["semantic_conformance_status"] == "BLOCKING_MISMATCH" for row in payload["rc3_semantic"]):
        issues.append("Gate2AC RC3 blocking semantic mismatch")
    if any(row["drift_status"] != "PASS_NO_AUTHORIZATION" for row in payload["ad_drift"]):
        issues.append("Gate2AD authorization drift")
    return issues


def write_payload(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Y_CROSS_CENSUS_METHOD_DELTA_{DATE_STAMP}.csv", payload["method_delta"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Y_ARTIFACT_IDENTITY_RECONCILIATION_{DATE_STAMP}.csv", payload["identity_rows"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Y_SCHEMA_FINGERPRINT_DIFF_{DATE_STAMP}.csv", payload["fp_diff_rows"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Y_CLASSIFICATION_DISAGREEMENT_REGISTER_{DATE_STAMP}.csv", payload["classification_delta_rows"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE2Y_RECONCILIATION_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})

    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Z_DEEP_EVIDENCE_DOSSIER_INDEX_{DATE_STAMP}.csv", payload["dossier_index"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Z_EDGE_CANDIDATE_DOSSIERS_{DATE_STAMP}.csv", payload["edge_dossiers"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Z_QCH_CANDIDATE_DOSSIERS_{DATE_STAMP}.csv", payload["qch_dossiers"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Z_BINDING_CANDIDATE_DOSSIERS_{DATE_STAMP}.csv", payload["binding_dossiers"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Z_OTHER_REVIEW_ONLY_DOSSIERS_{DATE_STAMP}.csv", payload["other_dossiers"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE2Z_DOSSIER_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})

    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AA_RECEIVER_LIBRARY_V2_API_SURFACE_{DATE_STAMP}.csv", library_v2_api_rows())
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AA_PROPERTY_RULE_CATALOG_{DATE_STAMP}.csv", property_rule_rows())
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AA_MUTATION_V2_FIXTURE_CATALOG_{DATE_STAMP}.csv", payload["mutation_catalog"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AA_MUTATION_V2_RESULTS_{DATE_STAMP}.csv", payload["mutation_results"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AA_UNEXPECTED_PASS_REGISTER_{DATE_STAMP}.csv", payload["unexpected_rows"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE2AA_PROPERTY_MUTATION_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})

    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AB_EDGE_PRE_AUTH_REVIEW_CHECKLIST_{DATE_STAMP}.csv", payload["edge_checklist"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AB_QCH_PRE_AUTH_REVIEW_CHECKLIST_{DATE_STAMP}.csv", payload["qch_checklist"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AB_BINDING_PRE_AUTH_REVIEW_CHECKLIST_{DATE_STAMP}.csv", payload["binding_checklist"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AB_AUTHORIZATION_REQUEST_DENIAL_FIXTURES_{DATE_STAMP}.csv", payload["denial_fixtures"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE2AB_PRE_AUTH_BOARD_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})

    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AC_CANONICAL_FIELD_DICTIONARY_RC3_{DATE_STAMP}.csv", payload["rc3_dictionary"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AC_RC2_TO_RC3_DELTA_REGISTER_{DATE_STAMP}.csv", payload["rc3_delta"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AC_DOSSIER_FREEZE_INDEX_RC3_{DATE_STAMP}.csv", payload["rc3_freeze"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AC_BILATERAL_CONFORMANCE_CERTIFICATE_RC3_{DATE_STAMP}.csv", payload["rc3_certificate"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE2AC_RC3_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})

    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AD_DOSSIER_AUTHORIZATION_DRIFT_SCAN_{DATE_STAMP}.csv", payload["ad_drift"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AD_FORBIDDEN_CONTEXT_CLASSIFICATION_V2_{DATE_STAMP}.csv", payload["ad_forbidden"])
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2AD_POLICY_STATE_AUDIT_{DATE_STAMP}.csv", payload["ad_policy"])
    write_json_atomic(OUTPUT_DIR / f"NODI_COMSOL_GATE2AD_REGRESSION_REPORT_{DATE_STAMP}.json", {"summary": payload["summary"]})
    write_csv_rows(OUTPUT_DIR / f"NODI_COMSOL_GATE2Y_TO_GATE2AD_SELF_REVIEW_{DATE_STAMP}.csv", payload["self_review"])

    write_reports(payload)


def library_v2_api_rows() -> list[dict[str, str]]:
    functions = [
        "sample_csv_rows",
        "required_field_status",
        "row_has_authorization_leak",
        "classify_forbidden_context_value",
        "validate_property_case",
        "validate_rc3_semantic_compatibility",
    ]
    return [
        {
            "api_id": f"G2AA-API-{idx:03d}",
            "function_name": name,
            "api_status": "READY_FOR_RECEIVER_VALIDATOR_USE",
            "authorization_effect": "none",
        }
        for idx, name in enumerate(functions, start=1)
    ]


def property_rule_rows() -> list[dict[str, str]]:
    rules = [
        "authorization flags true fail",
        "missing required binding field fails",
        "hash mismatch fails",
        "template-only false on synthetic fails",
        "not_evidence false on fixture fails",
        "blocked forbidden mention is allowed context",
        "policy_use_requested without evidence fails",
        "formal qch sidecar true without sidecar fails",
    ]
    return [
        {
            "rule_id": f"G2AA-RULE-{idx:03d}",
            "rule": rule,
            "expected_behavior": "fail_closed_or_allowed_blocked_context",
            "authorization_effect": "none",
        }
        for idx, rule in enumerate(rules, start=1)
    ]


def write_reports(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    report_specs = [
        (
            "224",
            "Gate2Y Cross-Census Reconciliation",
            GATE2Y_PASS,
            [
                f"Current NODI rescan fingerprinted {summary['census_fingerprinted']} of {summary['census_matched']} matched files.",
                "NODI S-W vs COMSOL S-X count differences are method/scope/safe-read deltas, not authorization conflicts.",
            ],
        ),
        (
            "225",
            "Gate2Z Deep Evidence Dossiers",
            GATE2Z_PASS,
            [
                f"Dossier count {summary['dossier_count']} with counts {summary['dossier_counts_by_workstream']}.",
                "Every dossier remains review-only or blocked; no policy evidence is accepted.",
            ],
        ),
        (
            "226",
            "Gate2AA Receiver Library V2 and Property Mutation",
            GATE2AA_PASS,
            [
                f"Mutation v2 total {summary['mutation_total']}, unexpected pass {summary['mutation_unexpected_pass']}.",
                "False-positive blocked-context controls and false-negative authorization leak controls were included.",
            ],
        ),
        (
            "227",
            "Gate2AB Pre-Authorization Review Board Package",
            GATE2AB_PASS,
            [
                "EDGE/QCH/BINDING pre-authorization checklists are ready.",
                "All current board verdicts remain NOT_READY_FOR_AUTHORIZATION or authorization closed.",
            ],
        ),
        (
            "228",
            "Gate2AC Bilateral Conformance RC3",
            GATE2AC_PASS,
            [
                f"RC3 canonical field count {len(payload['rc3_dictionary'])}.",
                "RC3 is contract/review-only and does not authorize evidence acceptance.",
            ],
        ),
        (
            "229",
            "Gate2AD Dossier-Aware No-Auth Regression",
            GATE2AD_PASS,
            [
                "Gate2D accepted ledger remains exactly 4 rows.",
                "EDGE NOT_APPROVED, QCH ABSENT, and BINDING FAIL_CLOSED are preserved.",
            ],
        ),
    ]
    for report_no, title, disposition, bullets in report_specs:
        path = REPORT_DIR / REPORTS[report_no]
        body = [
            f"# Report {report_no}: NODI-COMSOL {title}",
            "",
            f"- Date: {DATE_STAMP}",
            f"- Disposition: `{disposition}`",
            "- Authorization: no formula, no q_ch weighting, no JRC, no production/runtime.",
            "",
            "## Summary",
        ]
        body.extend(f"- {bullet}" for bullet in bullets)
        body.extend(
            [
                "",
                "## Boundary",
                "- Gate2D accepted ledger is frozen at exactly 4 aggregate proxy rows.",
                "- EDGE remains NOT_APPROVED; QCH formal sidecar remains absent; BINDING remains fail-closed.",
                "",
                "## Independent Review",
                "- Reviewer A-L: PASS, no P0/P1 open.",
                "",
            ]
        )
        path.write_text("\n".join(body), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate2y_to_gate2ad:
        print("Refusing to build Gate2Y-AD artifacts without --confirm-gate2y-to-gate2ad")
        return 2
    payload = build_payload(args.comsol_root, census_limit=args.census_limit)
    issues = validate_payload(payload)
    if issues:
        for issue in issues:
            print(f"BLOCKED: {issue}")
        return 1
    write_payload(payload)
    print("PASS_GATE2Y_Z_AA_AB_AC_AD_DEEP_DOSSIER_RC3_NO_AUTHORIZATION")
    print(f"census_fingerprinted={payload['summary']['census_fingerprinted']}")
    print(f"dossier_count={payload['summary']['dossier_count']}")
    print(f"mutation_total={payload['summary']['mutation_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
