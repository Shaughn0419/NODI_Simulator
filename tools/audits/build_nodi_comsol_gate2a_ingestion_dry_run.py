#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT,
    default_comsol_v4_readonly_context,
    validate_comsol_v4_readonly_context,
)
from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


REPORT_SCHEMA_VERSION = "nodi_comsol_gate2a_ingestion_dry_run_report_v1"
MATRIX_SCHEMA_VERSION = "nodi_comsol_gate2a_reconciliation_matrix_v1"
GRAIN_SCHEMA_VERSION = "nodi_comsol_gate2a_grain_compatibility_v1"
BLOCKER_SCHEMA_VERSION = "nodi_comsol_gate2a_blockers_v1"
PASS_STATUS = "PASS_GATE2A_RECONCILIATION_NO_WEIGHTING_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2A_RECONCILIATION"

OUTPUT_DIR = Path("reports/joint_interface_20260627")
MATRIX_FILENAME = "NODI_COMSOL_GATE2A_RECONCILIATION_MATRIX_20260627.csv"
GRAIN_FILENAME = "NODI_COMSOL_GATE2A_GRAIN_COMPATIBILITY_20260627.csv"
BLOCKERS_FILENAME = "NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv"
REPORT_FILENAME = "NODI_COMSOL_GATE2A_INGESTION_DRY_RUN_REPORT_20260627.json"
REPORT_MD_FILENAME = "NODI_COMSOL_GATE2A_INGESTION_DRY_RUN_REPORT_20260627.md"

DEFAULT_COMSOL_ROOT = (
    PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
)
DEFAULT_NODI_REGISTER = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_20260627.csv"
)
DEFAULT_NODI_BLOCKED = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2_CONTEXT_BLOCKED_GRAIN_REGISTER_20260627.csv"
)
DEFAULT_NODI_SCHEMA = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_SCHEMA_20260627.csv"
)
DEFAULT_PRS = (
    PROJECT_ROOT
    / "tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618"
    / "NODI_POSITION_RESPONSE_SURFACE.csv"
)
DEFAULT_EAS = (
    PROJECT_ROOT
    / "tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618"
    / "NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv"
)

COMSOL_INDEX = Path("roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_INDEX_20260627.csv")
COMSOL_GATES = Path("roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_GATES_20260627.csv")
COMSOL_VALIDATION = Path("roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_VALIDATION_20260627.csv")
COMSOL_MANIFEST = Path("roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_MANIFEST_20260627.csv")
COMSOL_PACKET = Path("roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_PACKET_20260627.md")

STATUS_CONTEXT_CANDIDATE = "NODI_RECONCILED_CONTEXT_ONLY_CANDIDATE"
STATUS_REVIEW_ONLY = "NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT"
STATUS_BLOCKED_GRAIN = "NODI_RECONCILED_BLOCKED_ROUTE_DIAMETER_BIN_VIEW_MISMATCH"
STATUS_BLOCKED_QCH = "NODI_RECONCILED_BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT"
STATUS_BLOCKED_STRONG = "NODI_RECONCILED_BLOCKED_STRONG_CLAIMS"
STATUS_V4_REVIEW = "NODI_RECONCILED_V4_REVIEW_ONLY"
COMSOL_READY_SOURCE_REVIEW_ONLY = "COMSOL_READY_SOURCE_REVIEW_ONLY"

FORBIDDEN_FIELD_FRAGMENTS = (
    "q_ch_eta",
    "qch_eta",
    "chi_selected",
    "joint_route_class",
    "jrc",
    "winner",
    "yield",
    "detection_probability",
    "wet_pass_probability",
    "clogging_rate",
    "time_to_clog",
    "route_score",
)

FORBIDDEN_ALLOWED_USE_TERMS = (
    "q_ch*eta",
    "chi_selected",
    "joint_route_class",
    " jrc",
    "winner",
    "yield",
    "detection probability",
    "wet pass probability",
    "clogging rate",
    "production-ready",
    "production ready",
    "runtime configuration",
)

GATE_BY_REGISTER_ROW = {
    "G2CTX-TPD-SOURCE-001": "G2-TPD-SOURCE-CONTEXT",
    "G2CTX-TPD-ALIGN-002": "G2-TPD-PRS-ALIGNMENT",
    "G2CTX-QCH-MISSING-003": "G2-QCH-SIDECAR",
    "G2CTX-CHI-AGG-004": "G2-CHI-PROXY",
    "G2CTX-CHI-BIN-005": "G2-CHI-PROXY",
    "G2CTX-LQ-ANCHOR-006": "G2-LOCAL-Q-HYDRAULIC",
    "G2CTX-LQ-SCREEN-007": "G2-LOCAL-Q-HYDRAULIC",
    "G2CTX-LQ-BRANCH-008": "G2-LOCAL-Q-HYDRAULIC",
    "G2CTX-V4-CONTRACT-009": "G2-V4-NODI-REVIEW",
    "G2CTX-V4-SIDECAR-010": "G2-V4-NODI-REVIEW",
}

QCH_DESCRIPTIVE_ARTIFACT = "roadmap/P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv"
ROUTE_FAMILY_RE = re.compile(r"(?P<route>\d+/W\d+/D\d+)")
CASE_ROUTE_RE = re.compile(r"W(?P<width>\d+)_D(?P<depth>\d+)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the NODI Gate2A COMSOL export reconciliation and ingestion "
            "dry-run. This writes no JRC, performs no q_ch weighting, and computes "
            "no chi_selected, yield, winner, or detection probability."
        )
    )
    parser.add_argument("--confirm-gate2a-dry-run", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--nodi-register", type=Path, default=DEFAULT_NODI_REGISTER)
    parser.add_argument("--nodi-blocked-register", type=Path, default=DEFAULT_NODI_BLOCKED)
    parser.add_argument("--nodi-register-schema", type=Path, default=DEFAULT_NODI_SCHEMA)
    parser.add_argument("--prs", type=Path, default=DEFAULT_PRS)
    parser.add_argument("--eas", type=Path, default=DEFAULT_EAS)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser


def build_gate2a_payload(
    *,
    nodi_register_rows: Sequence[Mapping[str, Any]],
    nodi_blocked_rows: Sequence[Mapping[str, Any]],
    nodi_schema_rows: Sequence[Mapping[str, Any]],
    comsol_index_rows: Sequence[Mapping[str, Any]],
    comsol_gate_rows: Sequence[Mapping[str, Any]],
    comsol_validation_rows: Sequence[Mapping[str, Any]],
    comsol_manifest_rows: Sequence[Mapping[str, Any]],
    prs_rows: Sequence[Mapping[str, Any]],
    eas_rows: Sequence[Mapping[str, Any]],
    comsol_root: Path,
    source_paths: Mapping[str, Path],
) -> dict[str, Any]:
    index_by_path = {_value(row, "path"): row for row in comsol_index_rows}
    gates_by_id = {_value(row, "gate_id"): row for row in comsol_gate_rows}
    prs_grains = {
        (_value(row, "route_id_nodi"), _value(row, "diameter_nm"), _value(row, "NODI_view"))
        for row in prs_rows
        if _value(row, "route_id_nodi") and _value(row, "diameter_nm") and _value(row, "NODI_view")
    }
    eas_route_views = {
        (_value(row, "route_id_nodi"), _value(row, "NODI_view"))
        for row in eas_rows
        if _value(row, "route_id_nodi") and _value(row, "NODI_view")
    }

    matrix_rows: list[dict[str, Any]] = []
    grain_rows: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    blocked_by_register = _blocked_rows_by_register(nodi_blocked_rows)

    for nodi_row in nodi_register_rows:
        register_id = _value(nodi_row, "register_row_id")
        gate_id = GATE_BY_REGISTER_ROW.get(register_id, "UNMAPPED_COMSOL_GATE")
        gate = gates_by_id.get(gate_id, {})
        source_artifact = _value(nodi_row, "source_artifact")
        index_row = _index_row_for_nodi_row(nodi_row, index_by_path)
        comsol_status = _value(index_row, "readiness_status") or _value(gate, "gate_status")
        reconciled_status = reconcile_status(nodi_row, comsol_status)
        can_enter_context = reconciled_status == STATUS_CONTEXT_CANDIDATE
        blocker_reason = _blocker_reason(nodi_row, index_row, gate, reconciled_status)
        matrix_rows.append(
            {
                "nodi_register_row_id": register_id,
                "comsol_gate_id": gate_id,
                "comsol_artifact": _value(index_row, "path") or source_artifact,
                "comsol_status": comsol_status,
                "comsol_source_review_status": _comsol_source_review_status(comsol_status),
                "nodi_preflight_status": _value(nodi_row, "candidate_status"),
                "reconciled_status": reconciled_status,
                "route_key": _value(nodi_row, "route_key"),
                "NODI_view": _nodi_view_basis(register_id, blocked_by_register),
                "diameter_nm": _value(nodi_row, "diameter_basis"),
                "bin_basis": _value(nodi_row, "bin_basis"),
                "matched_prs_grain_count": _value(nodi_row, "matched_grain_count"),
                "blocked_grain_count": _value(nodi_row, "blocked_grain_count"),
                "allowed_use": _value(index_row, "allowed_use") or _value(nodi_row, "allowed_use"),
                "blocked_use": _value(index_row, "blocked_use") or _value(nodi_row, "blocked_use"),
                "claim_boundary": _value(index_row, "claim_boundary") or _value(nodi_row, "claim_boundary"),
                "required_next_gate": _value(nodi_row, "required_next_gate"),
                "blocker_reason": blocker_reason,
                "can_enter_context_only_ingestion": _bool_text(can_enter_context),
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
            }
        )
        blockers.extend(_matrix_blocker_rows(register_id, gate_id, reconciled_status, blocker_reason))
        grain_rows.extend(
            _grain_compatibility_rows(
                nodi_row=nodi_row,
                index_row=index_row,
                blocked_rows=blocked_by_register.get(register_id, []),
                prs_grains=prs_grains,
                eas_route_views=eas_route_views,
                source_path=source_paths.get(source_artifact),
                comsol_root=comsol_root,
            )
        )

    blockers.extend(_package_gate_blockers(comsol_gate_rows))
    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": PASS_STATUS,
        "allowed_scope": "Gate2A COMSOL export reconciliation and ingestion dry-run only",
        "comsol_packet_path": str(comsol_root / COMSOL_PACKET),
        "comsol_packet_sha256": sha256_file(comsol_root / COMSOL_PACKET),
        "comsol_index_path": str(comsol_root / COMSOL_INDEX),
        "comsol_index_sha256": sha256_file(comsol_root / COMSOL_INDEX),
        "comsol_index_row_count": len(comsol_index_rows),
        "comsol_gates_path": str(comsol_root / COMSOL_GATES),
        "comsol_gates_sha256": sha256_file(comsol_root / COMSOL_GATES),
        "comsol_gate_row_count": len(comsol_gate_rows),
        "comsol_validation_path": str(comsol_root / COMSOL_VALIDATION),
        "comsol_validation_sha256": sha256_file(comsol_root / COMSOL_VALIDATION),
        "comsol_validation_row_count": len(comsol_validation_rows),
        "comsol_manifest_path": str(comsol_root / COMSOL_MANIFEST),
        "comsol_manifest_sha256": sha256_file(comsol_root / COMSOL_MANIFEST),
        "comsol_manifest_row_count": len(comsol_manifest_rows),
        "nodi_register_schema_row_count": len(nodi_schema_rows),
        "reconciliation_row_count": len(matrix_rows),
        "grain_compatibility_row_count": len(grain_rows),
        "blocker_row_count": len(blockers),
        "reconciled_status_counts": dict(Counter(row["reconciled_status"] for row in matrix_rows)),
        "comsol_status_counts": dict(Counter(row["comsol_status"] for row in matrix_rows)),
        "grain_status_counts": dict(Counter(row["grain_reconciled_status"] for row in grain_rows)),
        "gate2b_context_only_formal_ingestion": _gate2b_recommendation(matrix_rows),
        "can_enter_weighting_any": False,
        "can_enter_jrc_any": False,
        "q_ch_weighting_performed": False,
        "q_ch_eta_computed": False,
        "chi_selected_emitted": False,
        "joint_route_class_generated": False,
        "yield_computed": False,
        "winner_selected": False,
        "detection_probability_computed": False,
        "wet_pass_probability_computed": False,
        "clogging_rate_computed": False,
        "v4_runtime_or_production_promoted": False,
        "comsol_v4_context": default_comsol_v4_readonly_context(
            v4_scope=COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT,
            source_artifact=(
                "comsol test/comsol_ev_pbs_bonded_cross_junction/roadmap/"
                "EV_PBS_SAMPLE_SURFACE_CANONICAL_CONTRACT_V4_20260627.json"
            ),
        ),
        "issues": [],
        "reconciliation_rows": matrix_rows,
        "grain_compatibility_rows": grain_rows,
        "blocker_rows": blockers,
    }
    payload["issues"] = validate_gate2a_payload(payload)
    if payload["issues"]:
        payload["status"] = BLOCKED_STATUS
    return payload


def reconcile_status(nodi_row: Mapping[str, Any], comsol_status: str) -> str:
    register_id = _value(nodi_row, "register_row_id")
    candidate_type = _value(nodi_row, "candidate_type")
    nodi_status = _value(nodi_row, "candidate_status")
    if register_id == "G2CTX-QCH-MISSING-003" or "q_ch / flow split" in candidate_type:
        return STATUS_BLOCKED_QCH
    if "V4 sample/surface" in candidate_type:
        return STATUS_V4_REVIEW
    if "local-Q hydraulic anchor" in candidate_type:
        return STATUS_REVIEW_ONLY
    if "BLOCKED_ROUTE_DIAMETER_BIN" in nodi_status:
        return STATUS_BLOCKED_GRAIN
    if "BLOCKED_STRONG" in comsol_status:
        return STATUS_BLOCKED_STRONG
    if "PARTIAL_GRAIN_MATCH" in nodi_status:
        return STATUS_CONTEXT_CANDIDATE
    if "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY" in comsol_status:
        return STATUS_CONTEXT_CANDIDATE
    if nodi_status.startswith("REVIEW_ONLY"):
        return STATUS_REVIEW_ONLY
    return STATUS_BLOCKED_GRAIN


def validate_gate2a_payload(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if payload.get("schema_version") != REPORT_SCHEMA_VERSION:
        issues.append("GATE2A: report schema_version drifted")
    for field in (
        "can_enter_weighting_any",
        "can_enter_jrc_any",
        "q_ch_weighting_performed",
        "q_ch_eta_computed",
        "chi_selected_emitted",
        "joint_route_class_generated",
        "yield_computed",
        "winner_selected",
        "detection_probability_computed",
        "wet_pass_probability_computed",
        "clogging_rate_computed",
        "v4_runtime_or_production_promoted",
    ):
        if payload.get(field) is not False:
            issues.append(f"GATE2A: {field} must remain false")
    v4_context = payload.get("comsol_v4_context")
    if not isinstance(v4_context, Mapping):
        issues.append("GATE2A: missing V4 read-only context")
    else:
        issues.extend(f"GATE2A-V4: {issue}" for issue in validate_comsol_v4_readonly_context(v4_context))
    issues.extend(validate_reconciliation_rows(list(payload.get("reconciliation_rows", []))))
    issues.extend(validate_grain_rows(list(payload.get("grain_compatibility_rows", []))))
    return issues


def validate_reconciliation_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["GATE2A-MATRIX: no reconciliation rows"]
    for row_index, row in enumerate(rows, start=1):
        _reject_forbidden_positive_fields(row, row_index, "GATE2A-MATRIX", issues)
        if _value(row, "can_enter_weighting") != "false":
            issues.append(f"row {row_index} GATE2A-MATRIX: can_enter_weighting must be false")
        if _value(row, "can_enter_jrc") != "false":
            issues.append(f"row {row_index} GATE2A-MATRIX: can_enter_jrc must be false")
        if _value(row, "comsol_status") == "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY":
            if "PRODUCTION" in _value(row, "reconciled_status"):
                issues.append(f"row {row_index} GATE2A-MATRIX: COMSOL ready cannot become production-ready")
        allowed = _value(row, "allowed_use").lower().replace("_", " ")
        for term in FORBIDDEN_ALLOWED_USE_TERMS:
            if term in allowed:
                issues.append(f"row {row_index} GATE2A-MATRIX: allowed_use promotes {term}")
        if _value(row, "can_enter_context_only_ingestion") == "true":
            if _value(row, "reconciled_status") != STATUS_CONTEXT_CANDIDATE:
                issues.append(f"row {row_index} GATE2A-MATRIX: only context candidates may enter ingestion")
    return issues


def validate_grain_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["GATE2A-GRAIN: no grain compatibility rows"]
    for row_index, row in enumerate(rows, start=1):
        _reject_forbidden_positive_fields(row, row_index, "GATE2A-GRAIN", issues)
        if _value(row, "can_enter_weighting") != "false":
            issues.append(f"row {row_index} GATE2A-GRAIN: can_enter_weighting must be false")
        if _value(row, "can_enter_jrc") != "false":
            issues.append(f"row {row_index} GATE2A-GRAIN: can_enter_jrc must be false")
        if _value(row, "diameter_nm") == "220" and _value(row, "prs_grain_present") == "true":
            issues.append(f"row {row_index} GATE2A-GRAIN: 220 nm must not auto-map to PRS")
        if "edge4" in _value(row, "bin_basis") or "edge20_group" in _value(row, "bin_basis"):
            if _value(row, "direct_prs_bin_compatible") == "true":
                issues.append(f"row {row_index} GATE2A-GRAIN: edge4 cannot be direct PRS bin")
    return issues


def write_gate2a_bundle(
    *,
    comsol_root: Path,
    nodi_register_path: Path,
    nodi_blocked_path: Path,
    nodi_schema_path: Path,
    prs_path: Path,
    eas_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_gate2a_payload(
        nodi_register_rows=read_csv_rows(nodi_register_path),
        nodi_blocked_rows=read_csv_rows(nodi_blocked_path),
        nodi_schema_rows=read_csv_rows(nodi_schema_path),
        comsol_index_rows=read_csv_rows(comsol_root / COMSOL_INDEX),
        comsol_gate_rows=read_csv_rows(comsol_root / COMSOL_GATES),
        comsol_validation_rows=read_csv_rows(comsol_root / COMSOL_VALIDATION),
        comsol_manifest_rows=read_csv_rows(comsol_root / COMSOL_MANIFEST),
        prs_rows=read_csv_rows(prs_path),
        eas_rows=read_csv_rows(eas_path),
        comsol_root=comsol_root,
        source_paths={
            _value(row, "source_artifact"): comsol_root / _value(row, "source_artifact")
            for row in read_csv_rows(nodi_register_path)
            if _value(row, "source_artifact").startswith("roadmap/")
        },
    )

    matrix_path = output_dir / MATRIX_FILENAME
    grain_path = output_dir / GRAIN_FILENAME
    blockers_path = output_dir / BLOCKERS_FILENAME
    report_path = output_dir / REPORT_FILENAME
    report_md_path = output_dir / REPORT_MD_FILENAME

    write_csv_rows(matrix_path, payload["reconciliation_rows"])
    write_csv_rows(grain_path, payload["grain_compatibility_rows"])
    write_csv_rows(blockers_path, payload["blocker_rows"])
    _normalize_lf(matrix_path)
    _normalize_lf(grain_path)
    _normalize_lf(blockers_path)
    payload["reconciliation_matrix_csv"] = str(matrix_path)
    payload["reconciliation_matrix_sha256"] = sha256_file(matrix_path)
    payload["grain_compatibility_csv"] = str(grain_path)
    payload["grain_compatibility_sha256"] = sha256_file(grain_path)
    payload["blockers_csv"] = str(blockers_path)
    payload["blockers_sha256"] = sha256_file(blockers_path)
    payload["report_path"] = str(report_path)
    payload["report_md_path"] = str(report_md_path)
    write_json_atomic(report_path, payload, sort_keys=True)
    _write_markdown_report(report_md_path, payload)
    payload["report_sha256"] = sha256_file(report_path)
    payload["report_md_sha256"] = sha256_file(report_md_path)
    return payload


def _grain_compatibility_rows(
    *,
    nodi_row: Mapping[str, Any],
    index_row: Mapping[str, Any],
    blocked_rows: Sequence[Mapping[str, Any]],
    prs_grains: set[tuple[str, str, str]],
    eas_route_views: set[tuple[str, str]],
    source_path: Path | None,
    comsol_root: Path,
) -> list[dict[str, Any]]:
    register_id = _value(nodi_row, "register_row_id")
    source_artifact = _value(nodi_row, "source_artifact")
    rows: list[dict[str, Any]] = []
    explicit_grains = _source_grains(source_path) if source_path and source_path.exists() else set()
    blocked_keys = {
        (_value(row, "route_key"), _value(row, "diameter_nm"), _value(row, "NODI_view"), _value(row, "bin_basis"))
        for row in blocked_rows
    }
    for route, diameter, view, bin_basis in sorted(explicit_grains):
        prs_present = (route, diameter, view) in prs_grains
        eas_present = (route, view) in eas_route_views
        direct_bin = not ("edge4" in bin_basis or "edge20_group" in bin_basis)
        if diameter == "220":
            grain_status = STATUS_BLOCKED_GRAIN
            reason = "220 nm COMSOL context has no current NODI PRS production diameter grain."
        elif not prs_present:
            grain_status = STATUS_BLOCKED_GRAIN
            reason = "COMSOL route/diameter/view grain is absent from current NODI PRS."
        elif not eas_present:
            grain_status = STATUS_BLOCKED_GRAIN
            reason = "COMSOL route/view grain is absent from current NODI EAS."
        elif not direct_bin:
            grain_status = STATUS_REVIEW_ONLY
            reason = "edge4/edge20 grouped bin is review-only, not direct PRS bin."
        else:
            grain_status = STATUS_CONTEXT_CANDIDATE
            reason = "Exact context proxy grain matches current PRS/EAS, still no weighting."
        rows.append(
            _grain_row(
                register_id=register_id,
                source_artifact=source_artifact,
                index_row=index_row,
                route=route,
                diameter=diameter,
                view=view,
                bin_basis=bin_basis,
                prs_present=prs_present,
                eas_present=eas_present,
                direct_bin=direct_bin,
                grain_status=grain_status,
                reason=reason,
            )
        )
    for blocked in blocked_rows:
        key = (
            _value(blocked, "route_key"),
            _value(blocked, "diameter_nm"),
            _value(blocked, "NODI_view"),
            _value(blocked, "bin_basis"),
        )
        if key in blocked_keys and any(
            row["route_key"] == key[0]
            and row["diameter_nm"] == key[1]
            and row["NODI_view"] == key[2]
            and row["bin_basis"] == key[3]
            for row in rows
        ):
            continue
        rows.append(
            _grain_row(
                register_id=register_id,
                source_artifact=source_artifact,
                index_row=index_row,
                route=key[0],
                diameter=key[1],
                view=key[2],
                bin_basis=key[3],
                prs_present=(key[0], key[1], key[2]) in prs_grains,
                eas_present=(key[0], key[2]) in eas_route_views,
                direct_bin=not ("edge4" in key[3] or "edge20_group" in key[3]),
                grain_status=_status_from_blocked_alignment(_value(blocked, "alignment_status")),
                reason=_value(blocked, "reason"),
            )
        )
    if not rows:
        rows.append(
            _grain_row(
                register_id=register_id,
                source_artifact=source_artifact,
                index_row=index_row,
                route=_value(nodi_row, "route_key"),
                diameter=_value(nodi_row, "diameter_basis"),
                view="UNBOUND_REVIEW_ONLY",
                bin_basis=_value(nodi_row, "bin_basis"),
                prs_present=False,
                eas_present=False,
                direct_bin=False,
                grain_status=reconcile_status(nodi_row, _value(index_row, "readiness_status")),
                reason="No exact route/diameter/view/bin grain is available for dry-run binding.",
            )
        )
    return rows


def _source_grains(source_path: Path) -> set[tuple[str, str, str, str]]:
    if source_path.suffix.lower() != ".csv":
        return set()
    rows = read_csv_rows(source_path)
    grains: set[tuple[str, str, str, str]] = set()
    for row in rows:
        route = _route_key_from_row(row)
        diameter = _value(row, "diameter_nm")
        view = _value(row, "NODI_view")
        if route and diameter and view:
            grains.add((route, diameter, view, _bin_basis(row)))
    return grains


def _grain_row(
    *,
    register_id: str,
    source_artifact: str,
    index_row: Mapping[str, Any],
    route: str,
    diameter: str,
    view: str,
    bin_basis: str,
    prs_present: bool,
    eas_present: bool,
    direct_bin: bool,
    grain_status: str,
    reason: str,
) -> dict[str, Any]:
    context_ok = grain_status == STATUS_CONTEXT_CANDIDATE
    return {
        "schema_version": GRAIN_SCHEMA_VERSION,
        "nodi_register_row_id": register_id,
        "comsol_artifact": _value(index_row, "path") or source_artifact,
        "route_key": route,
        "NODI_view": view,
        "diameter_nm": diameter,
        "bin_basis": bin_basis,
        "prs_grain_present": _bool_text(prs_present),
        "eas_route_view_present": _bool_text(eas_present),
        "direct_prs_bin_compatible": _bool_text(direct_bin),
        "grain_reconciled_status": grain_status,
        "blocker_reason": reason,
        "can_enter_context_only_ingestion": _bool_text(context_ok),
        "can_enter_weighting": "false",
        "can_enter_jrc": "false",
    }


def _matrix_blocker_rows(
    register_id: str,
    gate_id: str,
    reconciled_status: str,
    reason: str,
) -> list[dict[str, Any]]:
    if reconciled_status == STATUS_CONTEXT_CANDIDATE:
        return []
    return [
        {
            "schema_version": BLOCKER_SCHEMA_VERSION,
            "nodi_register_row_id": register_id,
            "comsol_gate_id": gate_id,
            "blocker_status": reconciled_status,
            "blocker_reason": reason,
            "required_next_gate": _required_next_for_status(reconciled_status),
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
        }
    ]


def _package_gate_blockers(comsol_gate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for gate in comsol_gate_rows:
        gate_id = _value(gate, "gate_id")
        status = _value(gate, "gate_status")
        if gate_id in {"G2-WEIGHTING-AUTHORIZATION", "G2-JRC-STRONG-CLAIMS"}:
            blockers.append(
                {
                    "schema_version": BLOCKER_SCHEMA_VERSION,
                    "nodi_register_row_id": "*",
                    "comsol_gate_id": gate_id,
                    "blocker_status": STATUS_BLOCKED_STRONG,
                    "blocker_reason": _value(gate, "blocked") or _value(gate, "evidence"),
                    "required_next_gate": "future explicit weighting/JRC/strong-claims authorization",
                    "can_enter_weighting": "false",
                    "can_enter_jrc": "false",
                }
            )
        elif status in {"BLOCKED_NOT_WEIGHTING_AUTHORIZED", "BLOCKED_STRONG_CLAIMS_FORBIDDEN"}:
            blockers.append(
                {
                    "schema_version": BLOCKER_SCHEMA_VERSION,
                    "nodi_register_row_id": "*",
                    "comsol_gate_id": gate_id,
                    "blocker_status": STATUS_BLOCKED_STRONG,
                    "blocker_reason": _value(gate, "blocked"),
                    "required_next_gate": "future explicit strong-claims authorization",
                    "can_enter_weighting": "false",
                    "can_enter_jrc": "false",
                }
            )
    return blockers


def _index_row_for_nodi_row(
    nodi_row: Mapping[str, Any],
    index_by_path: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    source = _value(nodi_row, "source_artifact")
    if source in index_by_path:
        return index_by_path[source]
    if _value(nodi_row, "register_row_id") == "G2CTX-QCH-MISSING-003":
        return index_by_path.get(QCH_DESCRIPTIVE_ARTIFACT, {})
    return {}


def _status_from_blocked_alignment(status: str) -> str:
    if status.startswith("REVIEW_ONLY"):
        return STATUS_REVIEW_ONLY
    if "QCH" in status:
        return STATUS_BLOCKED_QCH
    return STATUS_BLOCKED_GRAIN


def _required_next_for_status(status: str) -> str:
    if status == STATUS_BLOCKED_QCH:
        return "COMSOL formal Gate2 q_ch/flow split export package"
    if status == STATUS_V4_REVIEW:
        return "separate V4-bound ingestion gate before runtime or production use"
    if status == STATUS_REVIEW_ONLY:
        return "remain review-only unless a future scoped binding gate is opened"
    if status == STATUS_BLOCKED_STRONG:
        return "future explicit strong-claims authorization"
    return "NODI/COMSOL route-diameter-view-bin binding repair or reduced-scope decision"


def _blocker_reason(
    nodi_row: Mapping[str, Any],
    index_row: Mapping[str, Any],
    gate: Mapping[str, Any],
    reconciled_status: str,
) -> str:
    if reconciled_status == STATUS_CONTEXT_CANDIDATE:
        return "context-only dry-run candidate; weighting/JRC remain blocked"
    return (
        _value(index_row, "blocker_if_any")
        or _value(gate, "blocked")
        or _value(nodi_row, "review_note")
        or _required_next_for_status(reconciled_status)
    )


def _comsol_source_review_status(comsol_status: str) -> str:
    if comsol_status == "READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY":
        return COMSOL_READY_SOURCE_REVIEW_ONLY
    return comsol_status


def _nodi_view_basis(
    register_id: str,
    blocked_by_register: Mapping[str, Sequence[Mapping[str, Any]]],
) -> str:
    views = sorted({_value(row, "NODI_view") for row in blocked_by_register.get(register_id, []) if _value(row, "NODI_view")})
    return ";".join(views) if views else "UNBOUND_OR_REGISTER_LEVEL"


def _blocked_rows_by_register(
    blocked_rows: Sequence[Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    by_id: dict[str, list[Mapping[str, Any]]] = {}
    for row in blocked_rows:
        by_id.setdefault(_value(row, "register_row_id"), []).append(row)
    return by_id


def _gate2b_recommendation(matrix_rows: Sequence[Mapping[str, Any]]) -> str:
    candidates = [row for row in matrix_rows if _value(row, "reconciled_status") == STATUS_CONTEXT_CANDIDATE]
    blocked = [row for row in matrix_rows if _value(row, "reconciled_status").startswith("NODI_RECONCILED_BLOCKED")]
    if candidates and blocked:
        return "PARTIAL"
    if candidates:
        return "YES"
    return "NO"


def _route_key_from_row(row: Mapping[str, Any]) -> str:
    if _value(row, "route_id_nodi"):
        return _value(row, "route_id_nodi")
    route_family = _value(row, "route_family")
    if route_family:
        match = ROUTE_FAMILY_RE.search(route_family)
        if match:
            return match.group("route")
    case_id = _value(row, "case_id")
    if case_id:
        match = CASE_ROUTE_RE.search(case_id)
        if match and match.group("width") == "800":
            return f"660/W{match.group('width')}/D{match.group('depth')}"
    return ""


def _bin_basis(row: Mapping[str, Any]) -> str:
    if _value(row, "prs_bin_count"):
        return f"prs_edge20_group_count_{_value(row, 'prs_bin_count')}"
    if _value(row, "tpd_bin_schema"):
        return f"{_value(row, 'tpd_bin_schema')}_edge4_context"
    if _value(row, "bin_schema"):
        return f"{_value(row, 'bin_schema')}_edge4_context"
    return _value(row, "bin_basis") or "not_position_binned"


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _value(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field, "")
    if value is None:
        return ""
    return str(value).strip()


def _reject_forbidden_positive_fields(
    row: Mapping[str, Any],
    row_index: int,
    prefix: str,
    issues: list[str],
) -> None:
    allowed_control_fields = {
        "can_enter_jrc",
        "can_enter_weighting",
        "nodi_register_row_id",
        "comsol_gate_id",
    }
    for field, value in row.items():
        normalized = field.lower()
        if normalized in allowed_control_fields:
            continue
        for fragment in FORBIDDEN_FIELD_FRAGMENTS:
            if fragment in normalized:
                issues.append(f"row {row_index} {prefix}: forbidden positive output field {field}")
                break
        if normalized in {
            "nodi_production_ingestion_allowed",
            "nodi_runtime_configuration_allowed",
            "production_ingestion_allowed",
        } and str(value).lower() == "true":
            issues.append(f"row {row_index} {prefix}: V4/runtime production promotion is forbidden")


def _normalize_lf(path: Path) -> None:
    raw = path.read_bytes()
    text = (
        raw.replace(b"\r\r\n", b"\n")
        .replace(b"\r\n", b"\n")
        .replace(b"\r", b"\n")
        .decode("utf-8")
    )
    lines = [line for line in text.split("\n") if line]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _write_markdown_report(path: Path, payload: Mapping[str, Any]) -> None:
    lines = [
        "# NODI/COMSOL Gate2A Ingestion Dry-Run Report",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This is a reconciliation and dry-run report only. It writes no JRC,",
        "performs no q_ch weighting or q_ch*eta, emits no chi_selected, and",
        "computes no yield, winner, detection probability, wet pass probability,",
        "or clogging rate.",
        "",
        "## Counts",
        "",
        f"- reconciliation rows: {payload['reconciliation_row_count']}",
        f"- grain compatibility rows: {payload['grain_compatibility_row_count']}",
        f"- blocker rows: {payload['blocker_row_count']}",
        f"- Gate2B context-only formal ingestion: `{payload['gate2b_context_only_formal_ingestion']}`",
        f"- reconciled status counts: `{payload['reconciled_status_counts']}`",
        "",
        "## Outputs",
        "",
        f"- reconciliation matrix: `{payload.get('reconciliation_matrix_csv', '')}`",
        f"- grain compatibility: `{payload.get('grain_compatibility_csv', '')}`",
        f"- blockers: `{payload.get('blockers_csv', '')}`",
        "",
        "## Issues",
        "",
    ]
    issues = list(payload.get("issues", []))
    lines.extend(f"- {issue}" for issue in issues) if issues else lines.append("- none")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_gate2a_dry_run:
        parser.error(
            "refusing to write Gate2A dry-run sidecars without --confirm-gate2a-dry-run"
        )
    payload = write_gate2a_bundle(
        comsol_root=args.comsol_root,
        nodi_register_path=args.nodi_register,
        nodi_blocked_path=args.nodi_blocked_register,
        nodi_schema_path=args.nodi_register_schema,
        prs_path=args.prs,
        eas_path=args.eas,
        output_dir=args.output_dir,
    )
    print(f"NODI_COMSOL_GATE2A_INGESTION_DRY_RUN: {payload['status']}")
    print(f"report_path: {payload['report_path']}")
    print(f"report_sha256: {payload['report_sha256']}")
    print(f"reconciliation_matrix_csv: {payload['reconciliation_matrix_csv']}")
    print(f"grain_compatibility_csv: {payload['grain_compatibility_csv']}")
    print(f"blockers_csv: {payload['blockers_csv']}")
    for issue in payload["issues"]:
        print(f"- issue: {issue}")
    return 0 if payload["status"] == PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
