#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    validate_effective_aperture_surrogate_csv,
    validate_position_response_surface_csv,
)
from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


REPORT_FILENAME = "NODI_COMSOL_PRE_JRC_DRY_MAPPING_REPORT_20260618.json"
REPORT_MD_FILENAME = "NODI_COMSOL_PRE_JRC_DRY_MAPPING_REPORT_20260618.md"
COVERAGE_FILENAME = "NODI_COMSOL_PRE_JRC_DRY_MAPPING_ROUTE_VIEW_COVERAGE_20260618.csv"
MAPPING_ROWS_FILENAME = "NODI_COMSOL_PRE_JRC_DRY_MAPPING_ROWS_20260618.csv"
MISSING_REGISTER_FILENAME = "NODI_COMSOL_PRE_JRC_MISSING_FIELD_REGISTER_20260618.csv"

PASS_STATUS = "PASS_PRE_JRC_DRY_MAPPING_WITH_BLOCKED_REGISTER_NO_OUTPUT_JRC"
BLOCKED_STATUS = "BLOCKED_PRE_JRC_DRY_MAPPING"

FORBIDDEN_FALSE_FIELDS = (
    "comsol_run_performed",
    "nodi_rerun_performed",
    "joint_route_class_generated",
    "q_ch_weighting_performed",
    "yield_computed",
    "winner_selected",
    "detection_probability_computed",
    "true_W_eff_claimed",
    "measured_geometry_claimed",
    "optical_solver_output_claimed",
    "fabrication_release_claimed",
    "P3_solver_conclusion_claimed",
)

FUTURE_BLOCKED_FIELDS = (
    (
        "joint_route_class_id",
        "requires explicit Gate 4 JOINT_ROUTE_CLASS regeneration authorization",
    ),
    ("q_ch_weight", "requires explicit Gate 2 COMSOL transport/q_ch sidecar authorization"),
    (
        "transported_position_distribution",
        "requires explicit Gate 2 COMSOL transport distribution authorization",
    ),
    ("q_ch_eta_weighted_response", "requires Gate 2 sidecar plus Gate 3 weighting authorization"),
    ("yield", "requires stronger evidence and explicit Gate 5 authorization"),
    ("winner", "requires stronger evidence and explicit Gate 5 authorization"),
    (
        "detection_probability",
        "requires explicit denominator, transport evidence, and Gate 5 authorization",
    ),
    ("true_W_eff", "EAS uses W_eff_surrogate_nm only; true W_eff is not authorized"),
    ("measured_geometry", "COMSOL descriptor is nominal surrogate input only"),
    ("optical_solver_output", "no optical solver output is present or authorized"),
    ("fabrication_release", "fabrication release is not authorized"),
    ("P3_solver_conclusion", "P3 solver conclusions are not authorized"),
)


def _default_output_dir() -> Path:
    return Path("tmp/nodi_comsol_pre_jrc_dry_mapping_20260618")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Gate 1 pre-JRC dry mapping report. This command writes no "
            "JOINT_ROUTE_CLASS, performs no q_ch weighting, and computes no yield, "
            "winner, or detection probability."
        )
    )
    parser.add_argument(
        "--confirm-dry-mapping-report",
        action="store_true",
        help="Confirm writing no-output pre-JRC dry mapping sidecars.",
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
        "--geometry-descriptor",
        type=Path,
        default=Path("tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def _route_view_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row["route_id_nodi"]),
        str(row["lambda_nm"]),
        str(row["W_nominal_nm"]),
        str(row["D_nm"]),
        str(row["NODI_view"]),
    )


def _geometry_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(int(float(row["W_nominal_nm"]))), str(int(float(row["D_nm"]))))


def _present_csv(value: bool) -> str:
    return "true" if value else "false"


def build_pre_jrc_dry_mapping_payload(
    *,
    prs_rows: list[dict[str, str]],
    eas_rows: list[dict[str, str]],
    geometry_rows: list[dict[str, str]],
    prs_path: Path,
    eas_path: Path,
    geometry_descriptor_path: Path,
) -> dict[str, Any]:
    prs_by_route_view: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in prs_rows:
        prs_by_route_view[_route_view_key(row)].append(row)

    eas_by_route_view: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in eas_rows:
        eas_by_route_view[_route_view_key(row)].append(row)

    descriptor_keys = {
        _geometry_key(row)
        for row in geometry_rows
        if row.get("process_state") == "nominal_smooth_geometry"
        and row.get("sidewall_deg") == "85.0"
    }

    route_view_keys = sorted(set(prs_by_route_view) | set(eas_by_route_view))
    coverage_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []

    for key in route_view_keys:
        route_id, lambda_nm, w_nominal, d_nm, view = key
        prs_group = prs_by_route_view.get(key, [])
        eas_group = eas_by_route_view.get(key, [])
        prs_diameters = sorted({row["diameter_nm"] for row in prs_group}, key=int)
        eas_modes = sorted({row["aperture_surrogate_mode"] for row in eas_group})
        descriptor_present = (w_nominal, d_nm) in descriptor_keys
        edge_primary_count = sum(
            1 for row in prs_group if row.get("aggregate_source_type") == "edge_norm_primary"
        )
        xz_diagnostic_count = sum(
            1 for row in prs_group if row.get("aggregate_source_type") == "xz_norm_diagnostic"
        )
        coverage_rows.append(
            {
                "route_id_nodi": route_id,
                "lambda_nm": lambda_nm,
                "W_nominal_nm": w_nominal,
                "D_nm": d_nm,
                "NODI_view": view,
                "prs_present": _present_csv(bool(prs_group)),
                "prs_row_count": len(prs_group),
                "prs_diameters_nm": ";".join(prs_diameters),
                "prs_edge_norm_primary_rows": edge_primary_count,
                "prs_xz_norm_diagnostic_rows": xz_diagnostic_count,
                "eas_present": _present_csv(bool(eas_group)),
                "eas_mode_count": len(eas_modes),
                "eas_modes": ";".join(eas_modes),
                "nominal_smooth_85deg_descriptor_present": _present_csv(descriptor_present),
                "gate1_mapping_status": (
                    "dry_map_keys_available"
                    if prs_group and eas_group and descriptor_present
                    else "dry_map_keys_incomplete"
                ),
                "claim_boundary": "key coverage only; no JRC, no q_ch weighting, no yield/winner",
            }
        )
        if not prs_group:
            missing_rows.append(
                {
                    "scope": "route_view_prs_coverage",
                    "route_id_nodi": route_id,
                    "NODI_view": view,
                    "blocked_field": "NODI_POSITION_RESPONSE_SURFACE rows",
                    "status": "BLOCKED_MISSING_PRS_FOR_ROUTE_VIEW",
                    "required_authorization_or_input": (
                        "future PRS expansion or explicit reduced-scope decision"
                    ),
                    "current_evidence": "EAS route/view exists but PRS production rows are absent",
                }
            )
        if not eas_group:
            missing_rows.append(
                {
                    "scope": "route_view_eas_coverage",
                    "route_id_nodi": route_id,
                    "NODI_view": view,
                    "blocked_field": "NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY rows",
                    "status": "BLOCKED_MISSING_EAS_FOR_ROUTE_VIEW",
                    "required_authorization_or_input": "repair EAS production coverage",
                    "current_evidence": "PRS route/view exists but EAS rows are absent",
                }
            )
        if not descriptor_present:
            missing_rows.append(
                {
                    "scope": "route_geometry_descriptor_coverage",
                    "route_id_nodi": route_id,
                    "NODI_view": view,
                    "blocked_field": "nominal_smooth_85deg_geometry_descriptor",
                    "status": "BLOCKED_MISSING_DESCRIPTOR_KEY",
                    "required_authorization_or_input": "descriptor coverage for W_nominal_nm/D_nm",
                    "current_evidence": f"W_nominal_nm={w_nominal}, D_nm={d_nm}",
                }
            )

    mapping_rows = _build_dry_mapping_rows(prs_by_route_view, eas_by_route_view)
    missing_rows.extend(_future_blocked_field_rows())
    issues = validate_pre_jrc_dry_mapping_rows(
        coverage_rows=coverage_rows,
        mapping_rows=mapping_rows,
        missing_rows=missing_rows,
    )
    blocked_route_view_count = sum(
        1 for row in missing_rows if row["status"] == "BLOCKED_MISSING_PRS_FOR_ROUTE_VIEW"
    )
    blocked_future_field_count = sum(
        1 for row in missing_rows if row["status"] == "BLOCKED_NOT_AUTHORIZED"
    )

    return {
        "schema_version": "nodi_comsol_pre_jrc_dry_mapping_report_v1",
        "status": PASS_STATUS if not issues else BLOCKED_STATUS,
        "allowed_scope": "pre_jrc_key_mapping_and_missing_field_register_only",
        "prs_path": str(prs_path),
        "prs_sha256": sha256_file(prs_path),
        "eas_path": str(eas_path),
        "eas_sha256": sha256_file(eas_path),
        "geometry_descriptor_path": str(geometry_descriptor_path),
        "geometry_descriptor_sha256": sha256_file(geometry_descriptor_path),
        "coverage_row_count": len(coverage_rows),
        "dry_mapping_row_count": len(mapping_rows),
        "missing_register_row_count": len(missing_rows),
        "coverage_status_counts": dict(Counter(row["gate1_mapping_status"] for row in coverage_rows)),
        "missing_status_counts": dict(Counter(row["status"] for row in missing_rows)),
        "has_blocked_route_view_coverage": blocked_route_view_count > 0,
        "blocked_route_view_coverage_count": blocked_route_view_count,
        "has_blocked_future_fields": blocked_future_field_count > 0,
        "blocked_future_field_count": blocked_future_field_count,
        "comsol_run_performed": False,
        "nodi_rerun_performed": False,
        "joint_route_class_generated": False,
        "q_ch_weighting_performed": False,
        "yield_computed": False,
        "winner_selected": False,
        "detection_probability_computed": False,
        "true_W_eff_claimed": False,
        "measured_geometry_claimed": False,
        "optical_solver_output_claimed": False,
        "fabrication_release_claimed": False,
        "P3_solver_conclusion_claimed": False,
        "claim_boundary": (
            "pre-JRC dry mapping only; key coverage and missing-field register; "
            "no JRC output, no q_ch weighting, no yield, no winner"
        ),
        "issues": issues,
        "coverage_rows": coverage_rows,
        "dry_mapping_rows": mapping_rows,
        "missing_register_rows": missing_rows,
    }


def _build_dry_mapping_rows(
    prs_by_route_view: dict[tuple[str, str, str, str, str], list[dict[str, str]]],
    eas_by_route_view: dict[tuple[str, str, str, str, str], list[dict[str, str]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(set(prs_by_route_view) & set(eas_by_route_view)):
        prs_group = prs_by_route_view[key]
        eas_group = eas_by_route_view[key]
        prs_diameters = sorted({row["diameter_nm"] for row in prs_group}, key=int)
        eas_modes = sorted({row["aperture_surrogate_mode"] for row in eas_group})
        route_id, lambda_nm, w_nominal, d_nm, view = key
        for diameter in prs_diameters:
            for mode in eas_modes:
                rows.append(
                    {
                        "dry_mapping_scope": "pre_jrc_no_output",
                        "route_id_nodi": route_id,
                        "lambda_nm": lambda_nm,
                        "W_nominal_nm": w_nominal,
                        "D_nm": d_nm,
                        "NODI_view": view,
                        "diameter_nm": diameter,
                        "aperture_surrogate_mode": mode,
                        "prs_rows_available": sum(
                            1 for row in prs_group if row["diameter_nm"] == diameter
                        ),
                        "eas_rows_available": sum(
                            1 for row in eas_group if row["aperture_surrogate_mode"] == mode
                        ),
                        "future_joint_route_class_id": "",
                        "future_joint_route_class_status": "BLOCKED_NOT_GENERATED_GATE1",
                        "q_ch_weight": "",
                        "q_ch_weight_status": "BLOCKED_MISSING_GATE2_COMSOL_SIDE_QCH",
                        "transported_position_distribution": "",
                        "transported_position_distribution_status": (
                            "BLOCKED_MISSING_GATE2_COMSOL_TRANSPORT"
                        ),
                        "weighted_response": "",
                        "yield": "",
                        "winner": "",
                        "detection_probability": "",
                        "claim_boundary": "dry key mapping only; no weighted output",
                    }
                )
    return rows


def _future_blocked_field_rows() -> list[dict[str, str]]:
    return [
        {
            "scope": "future_jrc_field",
            "route_id_nodi": "*",
            "NODI_view": "*",
            "blocked_field": field,
            "status": "BLOCKED_NOT_AUTHORIZED",
            "required_authorization_or_input": reason,
            "current_evidence": "Gate 1 writes dry mapping only",
        }
        for field, reason in FUTURE_BLOCKED_FIELDS
    ]


def validate_pre_jrc_dry_mapping_rows(
    *,
    coverage_rows: list[dict[str, Any]],
    mapping_rows: list[dict[str, Any]],
    missing_rows: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not coverage_rows:
        issues.append("PRE-JRC: coverage rows are empty")
    if not missing_rows:
        issues.append("PRE-JRC: missing-field register is empty")
    for index, row in enumerate(mapping_rows, start=1):
        if row.get("future_joint_route_class_id"):
            issues.append(f"PRE-JRC row {index}: JRC id must be blank")
        if row.get("future_joint_route_class_status") != "BLOCKED_NOT_GENERATED_GATE1":
            issues.append(f"PRE-JRC row {index}: JRC status drifted")
        for field in (
            "q_ch_weight",
            "transported_position_distribution",
            "weighted_response",
            "yield",
            "winner",
            "detection_probability",
        ):
            if row.get(field):
                issues.append(f"PRE-JRC row {index}: {field} must remain blank")
    future_fields = {row["blocked_field"] for row in missing_rows if row["scope"] == "future_jrc_field"}
    expected_future_fields = {field for field, _reason in FUTURE_BLOCKED_FIELDS}
    if future_fields != expected_future_fields:
        issues.append("PRE-JRC: future blocked-field register drifted")
    return issues


def validate_pre_jrc_dry_mapping_payload(payload: dict[str, Any]) -> list[str]:
    issues = list(payload.get("issues", []))
    if payload.get("schema_version") != "nodi_comsol_pre_jrc_dry_mapping_report_v1":
        issues.append("PRE-JRC: schema_version drifted")
    if payload.get("status") not in {PASS_STATUS, BLOCKED_STATUS}:
        issues.append("PRE-JRC: status drifted")
    for field in FORBIDDEN_FALSE_FIELDS:
        if payload.get(field) is not False:
            issues.append(f"PRE-JRC: {field} must remain false")
    issues.extend(
        validate_pre_jrc_dry_mapping_rows(
            coverage_rows=list(payload.get("coverage_rows", [])),
            mapping_rows=list(payload.get("dry_mapping_rows", [])),
            missing_rows=list(payload.get("missing_register_rows", [])),
        )
    )
    if payload.get("status") == PASS_STATUS and issues:
        issues.append("PRE-JRC: PASS status cannot carry validation issues")
    return issues


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# NODI/COMSOL Pre-JRC Dry Mapping Report",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This is Gate 1 dry mapping only. It writes no `JOINT_ROUTE_CLASS`, runs no",
        "COMSOL or NODI rerun, performs no q_ch weighting, and computes no yield,",
        "winner, or detection probability.",
        "",
        "## Counts",
        "",
        f"- coverage rows: {payload['coverage_row_count']}",
        f"- dry mapping rows: {payload['dry_mapping_row_count']}",
        f"- missing-register rows: {payload['missing_register_row_count']}",
        f"- coverage status counts: `{payload['coverage_status_counts']}`",
        f"- missing status counts: `{payload['missing_status_counts']}`",
        "",
        "## Issues",
        "",
    ]
    if payload["issues"]:
        lines.extend(f"- {issue}" for issue in payload["issues"])
    else:
        lines.append("- none")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_pre_jrc_dry_mapping_bundle(
    *,
    prs_path: Path,
    eas_path: Path,
    geometry_descriptor_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validator_issues = [
        *validate_position_response_surface_csv(
            prs_path,
            production_table=True,
            require_complete_row_arithmetic=True,
        ),
        *validate_effective_aperture_surrogate_csv(eas_path),
    ]
    payload = build_pre_jrc_dry_mapping_payload(
        prs_rows=read_csv_rows(prs_path),
        eas_rows=read_csv_rows(eas_path),
        geometry_rows=read_csv_rows(geometry_descriptor_path),
        prs_path=prs_path,
        eas_path=eas_path,
        geometry_descriptor_path=geometry_descriptor_path,
    )
    payload["issues"] = [*validator_issues, *payload["issues"]]
    if payload["issues"]:
        payload["status"] = BLOCKED_STATUS

    coverage_path = output_dir / COVERAGE_FILENAME
    mapping_path = output_dir / MAPPING_ROWS_FILENAME
    missing_path = output_dir / MISSING_REGISTER_FILENAME
    report_path = output_dir / REPORT_FILENAME
    report_md_path = output_dir / REPORT_MD_FILENAME

    write_csv_rows(coverage_path, payload["coverage_rows"])
    write_csv_rows(mapping_path, payload["dry_mapping_rows"])
    write_csv_rows(missing_path, payload["missing_register_rows"])
    payload["coverage_csv"] = str(coverage_path)
    payload["coverage_csv_sha256"] = sha256_file(coverage_path)
    payload["dry_mapping_csv"] = str(mapping_path)
    payload["dry_mapping_csv_sha256"] = sha256_file(mapping_path)
    payload["missing_register_csv"] = str(missing_path)
    payload["missing_register_csv_sha256"] = sha256_file(missing_path)
    payload["report_path"] = str(report_path)
    payload["report_md_path"] = str(report_md_path)
    write_json_atomic(report_path, payload, sort_keys=True)
    _write_markdown(report_md_path, payload)
    payload["report_sha256"] = sha256_file(report_path)
    payload["report_md_sha256"] = sha256_file(report_md_path)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_dry_mapping_report:
        parser.error(
            "refusing to write pre-JRC dry mapping sidecars without "
            "--confirm-dry-mapping-report"
        )

    payload = write_pre_jrc_dry_mapping_bundle(
        prs_path=args.prs,
        eas_path=args.eas,
        geometry_descriptor_path=args.geometry_descriptor,
        output_dir=args.output_dir,
    )
    print(f"NODI_COMSOL_PRE_JRC_DRY_MAPPING: {payload['status']}")
    print(f"report_path: {payload['report_path']}")
    print(f"report_sha256: {payload['report_sha256']}")
    print(f"coverage_csv: {payload['coverage_csv']}")
    print(f"dry_mapping_csv: {payload['dry_mapping_csv']}")
    print(f"missing_register_csv: {payload['missing_register_csv']}")
    for issue in payload["issues"]:
        print(f"- issue: {issue}")
    return 0 if payload["status"] == PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
