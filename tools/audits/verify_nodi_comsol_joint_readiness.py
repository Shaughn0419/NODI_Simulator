#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    PRS_NEUTRAL_FLOW_CONDITION_ID,
    validate_effective_aperture_surrogate_csv,
    validate_position_response_surface_csv,
    validate_production_generation_report,
)
from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_json_atomic


EXPECTED = {
    "prs_sha256": "e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e",
    "eas_sha256": "35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc",
    "selector_sha256": "399e34aa40279c0fc47a335685ddedd6b159f98a1786bb03b3cb13b20466ad32",
    "production_report_sha256": "12e3ba991b3ce1b3cf192f07c3291bc1ce338b202dcaa2d2ec3c493d0f7970f4",
    "review_zip_sha256": "b7924da8896bee47ac85052b329eeae65efe8adc11cc130eaed3104a934a4b6a",
    "review_zip_file_count": 26,
}

EXPECTED_MATRIX_ROWS = {
    "PRS production CSV": {
        "producer": "NODI",
        "consumer": "COMSOL/joint consumer",
        "current_artifact": (
            "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/"
            "NODI_POSITION_RESPONSE_SURFACE.csv"
        ),
        "status": "ready_read_only",
        "allowed_now": "import; schema check; row arithmetic; key mapping",
        "blocked_until": "COMSOL transport weighting authorization",
        "claim_boundary": "conditional NODI optical response only",
        "validation_or_evidence": (
            "validate_nodi_position_response_surface.py plus Report 191 PASS"
        ),
    },
    "EAS production CSV": {
        "producer": "NODI",
        "consumer": "COMSOL/joint consumer",
        "current_artifact": (
            "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/"
            "NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv"
        ),
        "status": "ready_read_only",
        "allowed_now": "import; surrogate-mode comparison; key mapping",
        "blocked_until": "true W_eff or solver-claim authorization",
        "claim_boundary": "dry surrogate sensitivity only",
        "validation_or_evidence": (
            "validate_nodi_effective_aperture_surrogate_sensitivity.py plus Report 191 PASS"
        ),
    },
    "EAS selector policy JSON": {
        "producer": "NODI",
        "consumer": "joint consumer",
        "current_artifact": (
            "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/"
            "NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json"
        ),
        "status": "ready_read_only",
        "allowed_now": "verify nominal smooth 85 degree selector policy",
        "blocked_until": "measured-geometry or fabrication-release authorization",
        "claim_boundary": "selector metadata only",
        "validation_or_evidence": (
            "SHA256 399e34aa40279c0fc47a335685ddedd6b159f98a1786bb03b3cb13b20466ad32"
        ),
    },
    "COMSOL geometry descriptor V1": {
        "producer": "COMSOL descriptor side",
        "consumer": "NODI/joint consumer",
        "current_artifact": "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        "status": "ready_as_nominal_surrogate_input",
        "allowed_now": "descriptor join-key check",
        "blocked_until": "measured-geometry authorization",
        "claim_boundary": "nominal dry-surrogate descriptor not measured geometry",
        "validation_or_evidence": (
            "SHA256 1198055754c41710a4821894ecb749660e5ef4a14b2e0fc647789ba31a0b38a2"
        ),
    },
    "COMSOL read-only PASS disposition": {
        "producer": "COMSOL reviewer",
        "consumer": "NODI/joint governance",
        "current_artifact": (
            "reports/191_NODI_COMSOL_READONLY_REVIEW_PASS_DISPOSITION_20260618.md"
        ),
        "status": "ready_as_review_evidence",
        "allowed_now": "cite no-correction review result",
        "blocked_until": "any execution or claim-upgrade authorization",
        "claim_boundary": "read-only review evidence only",
        "validation_or_evidence": (
            "review package SHA256 "
            "b7924da8896bee47ac85052b329eeae65efe8adc11cc130eaed3104a934a4b6a"
        ),
    },
    "PRS candidate SHA match": {
        "producer": "NODI",
        "consumer": "joint governance",
        "current_artifact": (
            "tmp/nodi_position_response_edge_primary_candidate_20260618/"
            "NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_20260618.csv"
        ),
        "status": "ready_read_only",
        "allowed_now": "prove production PRS equals validated candidate",
        "blocked_until": "none for read-only use",
        "claim_boundary": "provenance consistency only",
        "validation_or_evidence": (
            "SHA256 e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e"
        ),
    },
    "xz_norm_2d rows": {
        "producer": "NODI",
        "consumer": "joint consumer",
        "current_artifact": "inside PRS production CSV",
        "status": "diagnostic_only",
        "allowed_now": "read as diagnostic/context",
        "blocked_until": "explicit promotion policy plus adequate support",
        "claim_boundary": "not primary current decision input",
        "validation_or_evidence": (
            "1776 diagnostic rows and zero xz_norm_primary_if_adequate rows"
        ),
    },
    "edge_norm_1d rows": {
        "producer": "NODI",
        "consumer": "joint consumer",
        "current_artifact": "inside PRS production CSV",
        "status": "primary_conditional_response",
        "allowed_now": "read as primary conditional response",
        "blocked_until": "transport weighting authorization",
        "claim_boundary": "conditional optical response not occupancy",
        "validation_or_evidence": "92 edge_norm_primary rows",
    },
    "q_ch / flow split sidecar": {
        "producer": "COMSOL future lane",
        "consumer": "joint consumer",
        "current_artifact": "not present",
        "status": "missing_blocked",
        "allowed_now": "none",
        "blocked_until": "explicit q_ch sidecar authorization",
        "claim_boundary": "not currently available",
        "validation_or_evidence": "no current artifact",
    },
    "transported position distribution": {
        "producer": "COMSOL future lane",
        "consumer": "joint consumer",
        "current_artifact": "not present",
        "status": "missing_blocked",
        "allowed_now": "none",
        "blocked_until": "explicit COMSOL transport authorization",
        "claim_boundary": "not currently available",
        "validation_or_evidence": "no current artifact",
    },
    "JRC output": {
        "producer": "joint future lane",
        "consumer": "downstream consumer",
        "current_artifact": "not generated",
        "status": "not_generated_blocked",
        "allowed_now": "no-output dry mapping only",
        "blocked_until": "explicit JRC regeneration authorization",
        "claim_boundary": "no JRC claim",
        "validation_or_evidence": "no current artifact",
    },
    "yield / winner output": {
        "producer": "joint future lane",
        "consumer": "downstream consumer",
        "current_artifact": "not generated",
        "status": "not_authorized_blocked",
        "allowed_now": "none",
        "blocked_until": "explicit yield/winner authorization after required inputs exist",
        "claim_boundary": "no yield/winner claim",
        "validation_or_evidence": "no current artifact",
    },
}

EXPECTED_REVIEW_ZIP_NAMES = [
    "reports/185_NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_EDGE_PRIMARY_PREFLIGHT_20260618.md",
    "reports/186_NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE_VALIDATION_20260618.md",
    "reports/187_NODI_NEXT_ARTIFACTS_FULL_PRODUCTION_GENERATION_PRS_EAS_20260618.md",
    "reports/188_NODI_NEXT_ARTIFACTS_PRODUCTION_GATE_REVIEW_FIX_20260618.md",
    "reports/COMSOL_READONLY_REVIEW_PROMPT_NODI_NEXT_ARTIFACTS_FULL_PRODUCTION_20260618.md",
    "nodi_simulator/nodi_comsol_next_artifacts.py",
    "nodi_simulator/realism_v2_io.py",
    "tools/audits/run_nodi_next_artifacts_production_generation.py",
    "tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py",
    "tools/audits/build_nodi_position_response_edge_primary_candidate.py",
    "tests/test_nodi_comsol_next_artifacts_contracts.py",
    "tests/test_realism_v2_io.py",
    "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json",
    "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_POSITION_RESPONSE_SURFACE.csv",
    "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv",
    "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json",
    "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_20260618.csv",
    "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_20260618.csv",
    "tmp/nodi_position_response_source_production_eligibility_20260618/NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_REPORT_20260618.json",
    "tmp/nodi_position_response_source_production_eligibility_20260618/NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_CANDIDATES_20260618.csv",
    "tmp/nodi_position_response_source_production_eligibility_20260618/NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_GROUPS_20260618.csv",
    "tmp/nodi_position_response_source_production_eligibility_20260618/NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKERS_20260618.csv",
    "tmp/nodi_position_response_source_production_eligibility_20260618/NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_ISSUES_20260618.csv",
    "tmp/nodi_position_response_edge_primary_candidate_20260618/NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_REPORT_20260618.json",
    "tmp/nodi_position_response_edge_primary_candidate_20260618/NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_20260618.csv",
    "tmp/nodi_position_response_edge_primary_candidate_20260618/NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_ISSUES_20260618.csv",
]

PRS_TRUE_FIELDS = (
    "not_comsol_transport_distribution",
    "not_qch_weighted",
    "not_yield",
    "not_detection_probability",
)

EAS_TRUE_FIELDS = (
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_fabrication_release",
    "not_yield",
    "not_winner",
)

AUTHORIZATION_FALSE_FIELDS = (
    "comsol_run_authorized",
    "nodi_run_authorized",
    "joint_route_class_regeneration_authorized",
    "q_ch_weighting_or_q_ch_eta_authorized",
    "yield_computation_authorized",
    "winner_selection_authorized",
    "detection_probability_authorized",
    "true_W_eff_authorized",
    "measured_geometry_authorized",
    "optical_solver_output_authorized",
    "fabrication_release_authorized",
    "P3_solver_conclusion_authorized",
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_comsol_joint_readiness_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify Gate 0 read-only readiness for NODI/COMSOL joint linkage. "
            "This command never runs COMSOL, never regenerates JOINT_ROUTE_CLASS, "
            "and never computes q_ch weighting, yield, winner, or detection probability."
        )
    )
    parser.add_argument(
        "--confirm-readiness-report",
        action="store_true",
        help="Confirm writing a read-only readiness report sidecar.",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=Path("reports/joint_interface_20260618/NODI_COMSOL_JOINT_READINESS_MATRIX_20260618.csv"),
    )
    parser.add_argument(
        "--prs",
        type=Path,
        default=Path(
            "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/"
            "NODI_POSITION_RESPONSE_SURFACE.csv"
        ),
    )
    parser.add_argument(
        "--eas",
        type=Path,
        default=Path(
            "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/"
            "NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv"
        ),
    )
    parser.add_argument(
        "--selector-policy",
        type=Path,
        default=Path(
            "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/"
            "NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json"
        ),
    )
    parser.add_argument(
        "--production-report",
        type=Path,
        default=Path(
            "tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/"
            "NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json"
        ),
    )
    parser.add_argument(
        "--review-zip",
        type=Path,
        default=Path("tmp/nodi_comsol_readonly_review_full_production_20260618.zip"),
    )
    parser.add_argument(
        "--disposition-sidecar",
        type=Path,
        default=Path(
            "tmp/nodi_comsol_readonly_review_disposition_20260618/"
            "NODI_COMSOL_READONLY_REVIEW_DISPOSITION_20260618.json"
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def _bool_is_true(value: object) -> bool:
    return str(value).strip().lower() == "true"


def _add_hash_check(
    checks: list[dict[str, object]],
    issues: list[str],
    *,
    label: str,
    path: Path,
    expected_sha256: str,
) -> None:
    if not path.exists():
        issues.append(f"{label}: missing file {path}")
        checks.append({"label": label, "status": "FAIL", "path": str(path), "reason": "missing"})
        return
    actual = sha256_file(path)
    ok = actual.lower() == expected_sha256.lower()
    checks.append(
        {
            "label": label,
            "status": "PASS" if ok else "FAIL",
            "path": str(path),
            "expected_sha256": expected_sha256,
            "actual_sha256": actual,
        }
    )
    if not ok:
        issues.append(f"{label}: SHA256 drifted")


def _validate_matrix(matrix_path: Path, checks: list[dict[str, object]], issues: list[str]) -> None:
    rows = read_csv_rows(matrix_path)
    required = {
        "interface_item",
        "producer",
        "consumer",
        "current_artifact",
        "status",
        "allowed_now",
        "blocked_until",
        "claim_boundary",
        "validation_or_evidence",
    }
    if not rows:
        issues.append("matrix: no rows")
        checks.append({"label": "readiness_matrix", "status": "FAIL", "reason": "no rows"})
        return
    missing = required.difference(rows[0])
    if missing:
        issues.append(f"matrix: missing columns {sorted(missing)}")
    rows_by_item = {str(row.get("interface_item")): row for row in rows}
    missing_items = sorted(set(EXPECTED_MATRIX_ROWS).difference(rows_by_item))
    extra_items = sorted(set(rows_by_item).difference(EXPECTED_MATRIX_ROWS))
    drifted_items: list[dict[str, object]] = []
    for item, expected in EXPECTED_MATRIX_ROWS.items():
        row = rows_by_item.get(item)
        if row is None:
            continue
        for field, expected_value in expected.items():
            if row.get(field) != expected_value:
                drifted_items.append(
                    {
                        "interface_item": item,
                        "field": field,
                        "expected": expected_value,
                        "actual": row.get(field),
                    }
                )
    if missing_items:
        issues.append(f"matrix: missing expected interface items {missing_items}")
    if extra_items:
        issues.append(f"matrix: unexpected interface items {extra_items}")
    if drifted_items:
        issues.append("matrix: expected row status or blocker drifted")
    checks.append(
        {
            "label": "readiness_matrix",
            "status": "PASS"
            if not missing and not missing_items and not extra_items and not drifted_items
            else "FAIL",
            "path": str(matrix_path),
            "rows": len(rows),
            "missing_items": missing_items,
            "extra_items": extra_items,
            "drifted_items": drifted_items,
        }
    )


def _validate_prs(prs_path: Path, checks: list[dict[str, object]], issues: list[str]) -> None:
    validator_issues = validate_position_response_surface_csv(
        prs_path,
        production_table=True,
        require_complete_row_arithmetic=True,
    )
    checks.append(
        {
            "label": "prs_contract_validator",
            "status": "PASS" if not validator_issues else "FAIL",
            "issues": validator_issues,
        }
    )
    issues.extend(f"prs_contract_validator: {issue}" for issue in validator_issues)
    rows = read_csv_rows(prs_path)
    bad_rows = [
        index
        for index, row in enumerate(rows, start=1)
        if row.get("row_scope") != "response_surface_bin"
        or row.get("flow_condition_id") != PRS_NEUTRAL_FLOW_CONDITION_ID
        or any(not _bool_is_true(row.get(field)) for field in PRS_TRUE_FIELDS)
    ]
    checks.append(
        {
            "label": "prs_boundary_flags",
            "status": "PASS" if not bad_rows else "FAIL",
            "row_count": len(rows),
            "bad_row_count": len(bad_rows),
            "first_bad_rows": bad_rows[:10],
        }
    )
    if bad_rows:
        issues.append("prs_boundary_flags: PRS contains non-neutral flow or forbidden flag drift")


def _validate_eas(eas_path: Path, checks: list[dict[str, object]], issues: list[str]) -> None:
    validator_issues = validate_effective_aperture_surrogate_csv(eas_path)
    checks.append(
        {
            "label": "eas_contract_validator",
            "status": "PASS" if not validator_issues else "FAIL",
            "issues": validator_issues,
        }
    )
    issues.extend(f"eas_contract_validator: {issue}" for issue in validator_issues)
    rows = read_csv_rows(eas_path)
    bad_rows = [
        index
        for index, row in enumerate(rows, start=1)
        if any(not _bool_is_true(row.get(field)) for field in EAS_TRUE_FIELDS)
    ]
    checks.append(
        {
            "label": "eas_boundary_flags",
            "status": "PASS" if not bad_rows else "FAIL",
            "row_count": len(rows),
            "bad_row_count": len(bad_rows),
            "first_bad_rows": bad_rows[:10],
        }
    )
    if bad_rows:
        issues.append("eas_boundary_flags: EAS forbidden flag drift")


def _validate_production_report(
    report_path: Path, checks: list[dict[str, object]], issues: list[str]
) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validator_issues = validate_production_generation_report(report)
    checks.append(
        {
            "label": "production_generation_report_validator",
            "status": "PASS" if not validator_issues else "FAIL",
            "issues": validator_issues,
        }
    )
    issues.extend(
        f"production_generation_report_validator: {issue}" for issue in validator_issues
    )


def _validate_review_zip(zip_path: Path, checks: list[dict[str, object]], issues: list[str]) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
    bad_names = [name for name in names if "/._" in name or name.startswith("._") or "__MACOSX" in name]
    missing_names = sorted(set(EXPECTED_REVIEW_ZIP_NAMES).difference(names))
    extra_names = sorted(set(names).difference(EXPECTED_REVIEW_ZIP_NAMES))
    ok = (
        len(names) == EXPECTED["review_zip_file_count"]
        and not bad_names
        and not missing_names
        and not extra_names
    )
    checks.append(
        {
            "label": "review_zip_structure",
            "status": "PASS" if ok else "FAIL",
            "file_count": len(names),
            "expected_file_count": EXPECTED["review_zip_file_count"],
            "appledouble_or_macosx_entries": bad_names,
            "missing_entries": missing_names,
            "extra_entries": extra_names,
        }
    )
    if len(names) != EXPECTED["review_zip_file_count"]:
        issues.append("review_zip_structure: unexpected file count")
    if bad_names:
        issues.append("review_zip_structure: AppleDouble or __MACOSX entries present")
    if missing_names:
        issues.append("review_zip_structure: expected entries missing")
    if extra_names:
        issues.append("review_zip_structure: unexpected entries present")


def _validate_disposition_sidecar(
    sidecar_path: Path, checks: list[dict[str, object]], issues: list[str]
) -> None:
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    authorization = payload.get("authorization_status_after_this_pass", {})
    bad_fields = [
        field
        for field in AUTHORIZATION_FALSE_FIELDS
        if authorization.get(field) is not False
    ]
    ok = (
        payload.get("status") == "PASS_COMSOL_READONLY_REVIEW_NO_CORRECTIONS_REQUIRED"
        and not bad_fields
    )
    checks.append(
        {
            "label": "review_disposition_authorization_boundary",
            "status": "PASS" if ok else "FAIL",
            "bad_authorization_fields": bad_fields,
        }
    )
    if payload.get("status") != "PASS_COMSOL_READONLY_REVIEW_NO_CORRECTIONS_REQUIRED":
        issues.append("review_disposition_authorization_boundary: disposition status drifted")
    if bad_fields:
        issues.append(
            "review_disposition_authorization_boundary: forbidden authorization field drifted"
        )


def _markdown_report(report: dict[str, object]) -> str:
    status = report["status"]
    lines = [
        "# NODI/COMSOL Joint Readiness Report",
        "",
        f"Status: `{status}`",
        "",
        "This is a Gate 0 read-only readiness report. It does not authorize COMSOL",
        "execution, NODI rerun, JOINT_ROUTE_CLASS regeneration, q_ch weighting,",
        "yield, winner, detection probability, true W_eff, measured geometry,",
        "optical solver output, fabrication release, or P3 solver conclusions.",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        lines.append(f"- `{check['label']}`: `{check['status']}`")
    lines.extend(["", "## Issues", ""])
    if report["issues"]:
        lines.extend(f"- {issue}" for issue in report["issues"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def build_readiness_report(args: argparse.Namespace) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    issues: list[str] = []

    _validate_matrix(args.matrix, checks, issues)
    _add_hash_check(
        checks,
        issues,
        label="prs_sha256",
        path=args.prs,
        expected_sha256=EXPECTED["prs_sha256"],
    )
    _add_hash_check(
        checks,
        issues,
        label="eas_sha256",
        path=args.eas,
        expected_sha256=EXPECTED["eas_sha256"],
    )
    _add_hash_check(
        checks,
        issues,
        label="selector_policy_sha256",
        path=args.selector_policy,
        expected_sha256=EXPECTED["selector_sha256"],
    )
    _add_hash_check(
        checks,
        issues,
        label="production_report_sha256",
        path=args.production_report,
        expected_sha256=EXPECTED["production_report_sha256"],
    )
    _add_hash_check(
        checks,
        issues,
        label="review_zip_sha256",
        path=args.review_zip,
        expected_sha256=EXPECTED["review_zip_sha256"],
    )
    _validate_prs(args.prs, checks, issues)
    _validate_eas(args.eas, checks, issues)
    _validate_production_report(args.production_report, checks, issues)
    _validate_review_zip(args.review_zip, checks, issues)
    _validate_disposition_sidecar(args.disposition_sidecar, checks, issues)

    return {
        "schema_version": "nodi_comsol_joint_readiness_report_v1",
        "status": "PASS_GATE0_JOINT_READINESS_READ_ONLY" if not issues else "BLOCKED_GATE0_JOINT_READINESS",
        "generated_at_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "allowed_scope": "read_only_joint_interface_readiness",
        "forbidden_scope": [
            "COMSOL_run",
            "NODI_rerun",
            "JOINT_ROUTE_CLASS_regeneration",
            "q_ch_weighting_or_q_ch_eta",
            "yield",
            "winner",
            "detection_probability",
            "true_W_eff",
            "measured_geometry",
            "optical_solver_output",
            "fabrication_release",
            "P3_solver_conclusion",
        ],
        "checks": checks,
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_readiness_report:
        parser.error("refusing to write readiness sidecar without --confirm-readiness-report")

    report = build_readiness_report(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "NODI_COMSOL_JOINT_READINESS_REPORT_20260618.json"
    md_path = args.output_dir / "NODI_COMSOL_JOINT_READINESS_REPORT_20260618.md"
    write_json_atomic(json_path, report, sort_keys=True)
    md_path.write_text(_markdown_report(report), encoding="utf-8")

    print(f"NODI_COMSOL_JOINT_READINESS: {report['status']}")
    print(f"report_json: {json_path}")
    print(f"report_md: {md_path}")
    print(f"report_json_sha256: {sha256_file(json_path)}")
    print(f"report_md_sha256: {sha256_file(md_path)}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return 0 if not report["issues"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
