#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    POSITION_RESPONSE_ARTIFACT,
    PRS_CLAIM_BOUNDARY,
    PRS_EDGE_PRIMARY_CANDIDATE_FILENAME,
    ROWS_PER_ROUTE_DIAMETER_VIEW,
    validate_position_response_surface_rows,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


PASS_STATUS = "PASS_PRS_EDGE_PRIMARY_CANDIDATE_MERGED_VALIDATED_NOT_PROMOTED"
BLOCKED_STATUS = "BLOCKED_PRS_EDGE_PRIMARY_CANDIDATE_MERGE"
REPORT_FILENAME = "NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE_MERGE_REPORT_20260618.json"
ISSUES_FILENAME = "NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE_MERGE_ISSUES_20260618.csv"
MANIFEST_FILENAME = "NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE_MERGE_MANIFEST_20260618.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Merge already validated edge-primary NODI_POSITION_RESPONSE_SURFACE "
            "candidate CSVs into one production-shaped candidate. This command only "
            "copies rows, detects duplicate route/diameter/view bins, validates the "
            "merged PRS contract, and writes sidecars. It does not run NODI, run "
            "COMSOL, regenerate JOINT_ROUTE_CLASS, or promote q_ch/yield/winner claims."
        )
    )
    parser.add_argument(
        "--confirm-merge-candidates",
        action="store_true",
        help="Confirm merging candidate CSV rows without generating new measurements.",
    )
    parser.add_argument(
        "--candidate",
        dest="candidates",
        action="append",
        type=Path,
        required=True,
        help="Validated edge-primary NODI_POSITION_RESPONSE_SURFACE candidate CSV.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def _grain_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    return (
        str(row.get("route_id_nodi", "")),
        str(row.get("diameter_nm", "")),
        str(row.get("NODI_view", "")),
        str(row.get("distribution_type", "")),
        str(row.get("row_kind", "")),
        str(row.get("bin_id", "")),
        str(row.get("aggregate_id", "")),
    )


def _route_diameter_view_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("route_id_nodi", "")),
        str(row.get("diameter_nm", "")),
        str(row.get("NODI_view", "")),
    )


def _load_candidate_rows(path: Path, issues: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        issues.append(f"MERGE-PRS-C01: missing candidate {path}")
        return []
    rows = read_csv_rows(path)
    row_issues = validate_position_response_surface_rows(
        rows,
        production_table=True,
        require_complete_row_arithmetic=True,
    )
    issues.extend(f"MERGE-PRS-C02: {path}: {issue}" for issue in row_issues)
    return rows


def merge_candidate_rows(
    candidate_paths: list[Path],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    issues: list[str] = []
    merged_rows: list[dict[str, str]] = []
    manifest_rows: list[dict[str, str]] = []
    seen: dict[tuple[str, str, str, str, str, str, str], str] = {}
    for index, path in enumerate(candidate_paths, start=1):
        rows = _load_candidate_rows(path, issues)
        before = len(merged_rows)
        for row_index, row in enumerate(rows, start=1):
            key = _grain_key(dict(row))
            previous = seen.get(key)
            if previous is not None:
                issues.append(
                    "MERGE-PRS-C03: duplicate PRS row key "
                    f"{key} in {path}:{row_index}; previously seen in {previous}"
                )
                continue
            seen[key] = f"{path}:{row_index}"
            merged_rows.append(dict(row))
        grains = {_route_diameter_view_key(dict(row)) for row in rows}
        manifest_rows.append(
            {
                "candidate_index": str(index),
                "candidate_path": str(path),
                "candidate_sha256": sha256_file(path) if path.exists() else "",
                "candidate_row_count": str(len(rows)),
                "merged_row_count_added": str(len(merged_rows) - before),
                "route_diameter_view_count": str(len(grains)),
                "claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )
    if merged_rows:
        merged_issues = validate_position_response_surface_rows(
            merged_rows,
            production_table=True,
            require_complete_row_arithmetic=True,
        )
        issues.extend(f"MERGE-PRS-V01: {issue}" for issue in merged_issues)
    else:
        issues.append("MERGE-PRS-V02: no rows to merge")
    return merged_rows, manifest_rows, issues


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_merge_candidates:
        raise SystemExit(
            "refusing candidate merge without --confirm-merge-candidates"
        )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_paths = [Path(path) for path in args.candidates]
    rows, manifest_rows, issues = merge_candidate_rows(candidate_paths)

    manifest_path = output_dir / MANIFEST_FILENAME
    write_csv_rows(
        manifest_path,
        manifest_rows or [{"candidate_index": "", "candidate_path": ""}],
    )
    issue_rows = [
        {"issue_index": str(index), "issue": issue}
        for index, issue in enumerate(issues, start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)

    candidate_path = output_dir / PRS_EDGE_PRIMARY_CANDIDATE_FILENAME
    if rows and not issues:
        write_csv_rows(candidate_path, rows)
    route_diameter_view_count = len({_route_diameter_view_key(dict(row)) for row in rows})
    report: dict[str, Any] = {
        "schema_version": "nodi_position_response_edge_primary_candidate_merge_v1",
        "status": PASS_STATUS if rows and not issues else BLOCKED_STATUS,
        "artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "merge_validated_edge_primary_candidates_not_promoted",
        "allowed_current_action": "copy_merge_candidate_rows_and_validate_contract_only",
        "candidate_inputs": [str(path) for path in candidate_paths],
        "candidate_input_count": len(candidate_paths),
        "candidate_csv": str(candidate_path) if rows and not issues else "",
        "candidate_csv_sha256": sha256_file(candidate_path)
        if rows and not issues
        else "",
        "candidate_row_count": len(rows) if rows and not issues else 0,
        "expected_rows_per_route_diameter_view": ROWS_PER_ROUTE_DIAMETER_VIEW,
        "route_diameter_view_count": route_diameter_view_count,
        "manifest_csv": str(manifest_path),
        "manifest_csv_sha256": sha256_file(manifest_path),
        "issue_csv": str(issue_path),
        "issue_csv_sha256": sha256_file(issue_path),
        "issues": issues,
        "candidate_promoted_to_production_gate": False,
        "production_generation_performed": False,
        "nodi_run_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
    }
    report_path = output_dir / REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    write_json_atomic(report_path, report, sort_keys=True)

    print(f"NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE_MERGE: {report['status']}")
    print(f"candidate_csv: {report['candidate_csv']}")
    print(f"candidate_csv_sha256: {report['candidate_csv_sha256']}")
    print(f"candidate_row_count: {report['candidate_row_count']}")
    print(f"route_diameter_view_count: {report['route_diameter_view_count']}")
    print(f"report_path: {report_path}")
    print(f"report_sha256: {sha256_file(report_path)}")
    for issue in issues:
        print(f"- issue: {issue}")
    return 0 if report["status"] == PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
