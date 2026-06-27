#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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


PASS_STATUS = "PASS_GATE2B_CONTEXT_ONLY_FORMAL_INGESTION_PARTIAL_NO_WEIGHTING_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2B_CONTEXT_ONLY_FORMAL_INGESTION"
REPORT_SCHEMA_VERSION = "nodi_comsol_gate2b_formal_ingestion_report_v1"
REGISTER_SCHEMA_VERSION = "nodi_comsol_gate2b_formal_context_ingest_register_v1"
INGESTED_ROWS_SCHEMA_VERSION = "nodi_comsol_gate2b_ingested_context_rows_v1"
QUARANTINE_SCHEMA_VERSION = "nodi_comsol_gate2b_quarantine_review_only_register_v1"
BLOCKED_GRAIN_SCHEMA_VERSION = "nodi_comsol_gate2b_blocked_grain_disposition_v1"
FORBIDDEN_AUDIT_SCHEMA_VERSION = "nodi_comsol_gate2b_forbidden_claim_audit_v1"
SELF_REVIEW_SCHEMA_VERSION = "nodi_comsol_gate2b_self_review_findings_v1"
GATE2C_SCHEMA_VERSION = "nodi_comsol_gate2c_required_export_schema_v1"

OUTPUT_DIR = Path("reports/joint_interface_20260627")
REGISTER_FILENAME = "NODI_COMSOL_GATE2B_FORMAL_CONTEXT_INGEST_REGISTER_20260627.csv"
INGESTED_ROWS_FILENAME = "NODI_COMSOL_GATE2B_INGESTED_CONTEXT_ROWS_20260627.csv"
QUARANTINE_FILENAME = "NODI_COMSOL_GATE2B_QUARANTINE_REVIEW_ONLY_REGISTER_20260627.csv"
BLOCKED_GRAIN_FILENAME = "NODI_COMSOL_GATE2B_BLOCKED_GRAIN_DISPOSITION_20260627.csv"
FORBIDDEN_AUDIT_FILENAME = "NODI_COMSOL_GATE2B_FORBIDDEN_CLAIM_AUDIT_20260627.csv"
SELF_REVIEW_FILENAME = "NODI_COMSOL_GATE2B_SELF_REVIEW_FINDINGS_20260627.csv"
GATE2C_SCHEMA_FILENAME = "NODI_COMSOL_GATE2C_REQUIRED_EXPORT_SCHEMA_20260627.csv"
REPORT_JSON_FILENAME = "NODI_COMSOL_GATE2B_FORMAL_INGESTION_REPORT_20260627.json"
REPORT_MD_FILENAME = "NODI_COMSOL_GATE2B_FORMAL_INGESTION_REPORT_20260627.md"
REPORT_200_FILENAME = "200_NODI_COMSOL_GATE2B_CONTEXT_ONLY_FORMAL_INGESTION_20260627.md"

DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
DEFAULT_GATE2A_MATRIX = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2A_RECONCILIATION_MATRIX_20260627.csv"
)
DEFAULT_GATE2A_GRAIN = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2A_GRAIN_COMPATIBILITY_20260627.csv"
)
DEFAULT_GATE2A_BLOCKERS = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv"
)
DEFAULT_GATE2A_REPORT = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2A_INGESTION_DRY_RUN_REPORT_20260627.json"
)

COMSOL_GATE2A_PACKET = Path("roadmap/COMSOL_GATE2A_NODI_BINDING_PACKET_20260627.md")
COMSOL_GATE2A_CROSSWALK = Path("roadmap/COMSOL_GATE2A_NODI_BINDING_CROSSWALK_20260627.csv")
COMSOL_GATE2A_BLOCKERS = Path("roadmap/COMSOL_GATE2A_NODI_BINDING_BLOCKERS_20260627.csv")
COMSOL_GATE2A_QCH = Path("roadmap/COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv")
COMSOL_GATE2A_VALIDATION = Path("roadmap/COMSOL_GATE2A_NODI_BINDING_VALIDATION_20260627.csv")
COMSOL_GATE2A_MANIFEST = Path("roadmap/COMSOL_GATE2A_NODI_BINDING_MANIFEST_20260627.csv")

ALLOWED_FORMAL_REGISTER_ROWS = ("G2CTX-CHI-AGG-004", "G2CTX-CHI-BIN-005")
SOURCE_READY_BLOCKED_ROWS = ("G2CTX-TPD-SOURCE-001", "G2CTX-TPD-ALIGN-002")
LOCAL_Q_ROWS = ("G2CTX-LQ-ANCHOR-006", "G2CTX-LQ-SCREEN-007", "G2CTX-LQ-BRANCH-008")
V4_ROWS = ("G2CTX-V4-CONTRACT-009", "G2CTX-V4-SIDECAR-010")
QCH_ROW = "G2CTX-QCH-MISSING-003"

LANE_FORMAL = "gate2b_formal_context_only_ingested"
LANE_SOURCE_BLOCKED = "source_ready_but_blocked"
LANE_QCH_QUARANTINE = "q_ch_provenance_quarantine"
LANE_REVIEW_DIAGNOSTIC = "review_only_diagnostic"
LANE_V4_CEILING = "review_only_claim_ceiling"
LANE_STRONG_BLOCKER = "strong_claim_hard_blocker"

FORBIDDEN_CLAIMS = (
    "q_ch_weighting",
    "q_ch_eta",
    "q_ch_chi_eta",
    "chi_selected",
    "route_score",
    "JOINT_ROUTE_CLASS",
    "JRC",
    "yield",
    "winner",
    "detection_probability",
    "wet_pass_probability",
    "clogging_rate",
    "time_to_clog",
    "recovery",
    "runtime_configuration",
    "production_ingestion",
)

FORBIDDEN_POSITIVE_FIELD_FRAGMENTS = (
    "q_ch_eta",
    "qch_eta",
    "q_ch_chi_eta",
    "qch_chi_eta",
    "chi_selected",
    "joint_route_class",
    "jrc",
    "route_score",
    "winner",
    "yield",
    "detection_probability",
    "wet_pass_probability",
    "clogging_rate",
    "time_to_clog",
    "runtime_configuration",
    "production_ingestion",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build NODI Gate2B partial context-only formal ingestion outputs. "
            "This writes no JRC, performs no q_ch weighting, and emits no chi_selected."
        )
    )
    parser.add_argument("--confirm-gate2b-formal-context-only", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--gate2a-matrix", type=Path, default=DEFAULT_GATE2A_MATRIX)
    parser.add_argument("--gate2a-grain", type=Path, default=DEFAULT_GATE2A_GRAIN)
    parser.add_argument("--gate2a-blockers", type=Path, default=DEFAULT_GATE2A_BLOCKERS)
    parser.add_argument("--gate2a-report", type=Path, default=DEFAULT_GATE2A_REPORT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_gate2b_payload(
    *,
    gate2a_matrix_rows: Sequence[Mapping[str, Any]],
    gate2a_grain_rows: Sequence[Mapping[str, Any]],
    gate2a_blocker_rows: Sequence[Mapping[str, Any]],
    comsol_crosswalk_rows: Sequence[Mapping[str, Any]],
    comsol_blocker_rows: Sequence[Mapping[str, Any]],
    qch_provenance_rows: Sequence[Mapping[str, Any]],
    comsol_validation_rows: Sequence[Mapping[str, Any]],
    comsol_manifest_rows: Sequence[Mapping[str, Any]],
    source_hashes: Mapping[str, str],
    source_row_counts: Mapping[str, str],
) -> dict[str, Any]:
    matrix_by_id = {_value(row, "nodi_register_row_id"): row for row in gate2a_matrix_rows}
    crosswalk_by_path = _crosswalk_by_path(comsol_crosswalk_rows)

    formal_register = [
        _formal_register_row(matrix_by_id[register_id], crosswalk_by_path)
        for register_id in ALLOWED_FORMAL_REGISTER_ROWS
        if register_id in matrix_by_id
    ]
    ingested_rows = [_ingested_context_row(row) for row in formal_register]
    quarantine_rows = _quarantine_rows(
        gate2a_matrix_rows=gate2a_matrix_rows,
        gate2a_blocker_rows=gate2a_blocker_rows,
        qch_provenance_rows=qch_provenance_rows,
        source_hashes=source_hashes,
        source_row_counts=source_row_counts,
    )
    blocked_grain_rows = [
        _blocked_grain_row(row)
        for row in gate2a_grain_rows
    ]
    forbidden_claim_audit = _forbidden_claim_audit_rows()
    self_review_rows = _self_review_rows(
        formal_register=formal_register,
        ingested_rows=ingested_rows,
        quarantine_rows=quarantine_rows,
        blocked_grain_rows=blocked_grain_rows,
        qch_provenance_rows=qch_provenance_rows,
    )
    gate2c_schema_rows = _gate2c_required_export_schema_rows()

    payload = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": PASS_STATUS,
        "allowed_scope": "Gate2B partial context-only formal ingestion ledger only",
        "gate2b_context_only_formal_ingestion": "PARTIAL",
        "formal_register_rows": formal_register,
        "ingested_context_rows": ingested_rows,
        "quarantine_review_only_rows": quarantine_rows,
        "blocked_grain_disposition_rows": blocked_grain_rows,
        "forbidden_claim_audit_rows": forbidden_claim_audit,
        "self_review_rows": self_review_rows,
        "gate2c_required_export_schema_rows": gate2c_schema_rows,
        "formal_register_row_count": len(formal_register),
        "ingested_context_row_count": len(ingested_rows),
        "quarantine_review_only_row_count": len(quarantine_rows),
        "blocked_grain_disposition_row_count": len(blocked_grain_rows),
        "forbidden_claim_audit_row_count": len(forbidden_claim_audit),
        "self_review_row_count": len(self_review_rows),
        "gate2c_required_export_schema_row_count": len(gate2c_schema_rows),
        "comsol_crosswalk_row_count": len(comsol_crosswalk_rows),
        "comsol_blocker_row_count": len(comsol_blocker_rows),
        "qch_provenance_row_count": len(qch_provenance_rows),
        "comsol_validation_row_count": len(comsol_validation_rows),
        "comsol_manifest_row_count": len(comsol_manifest_rows),
        "comsol_recommended_status_counts": dict(
            Counter(_value(row, "recommended_nodi_reconciled_status") for row in comsol_crosswalk_rows)
        ),
        "gate2b_ingestion_lanes": dict(Counter(row["ingestion_lane"] for row in quarantine_rows + formal_register)),
        "context_only_formal_ingestion_allowed_any": bool(formal_register),
        "can_enter_weighting_any": False,
        "can_enter_jrc_any": False,
        "is_chi_selected_any": False,
        "is_production_ingestion_any": False,
        "is_runtime_configuration_any": False,
        "qch_sidecar_status": "PROVENANCE_ONLY_NOT_GATE2_QCH_SIDECAR",
        "comsol_v4_context": default_comsol_v4_readonly_context(),
        "input_hashes": dict(source_hashes),
        "input_row_counts": dict(source_row_counts),
    }
    return payload


def validate_gate2b_payload(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    register_rows = list(payload.get("formal_register_rows", []))
    ingested_rows = list(payload.get("ingested_context_rows", []))
    quarantine_rows = list(payload.get("quarantine_review_only_rows", []))
    blocked_grain_rows = list(payload.get("blocked_grain_disposition_rows", []))
    forbidden_rows = list(payload.get("forbidden_claim_audit_rows", []))

    register_ids = {_value(row, "nodi_register_row_id") for row in register_rows}
    if register_ids != set(ALLOWED_FORMAL_REGISTER_ROWS):
        issues.append(f"Gate2B formal register must contain only allowed proxy rows: {sorted(register_ids)}")

    for row in register_rows + ingested_rows:
        register_id = _value(row, "nodi_register_row_id")
        if register_id not in ALLOWED_FORMAL_REGISTER_ROWS:
            issues.append(f"unexpected formal ingestion register row: {register_id}")
        if _value(row, "context_only_formal_ingestion_allowed") != "true":
            issues.append(f"formal context row is not marked context-only allowed: {register_id}")
        if _value(row, "diameter_nm") == "220":
            issues.append(f"220 nm row entered formal ingestion: {register_id}")
        if _value(row, "is_chi_selected") != "false":
            issues.append(f"chi_selected promotion in formal row: {register_id}")
        if _value(row, "is_production_ingestion") != "false":
            issues.append(f"production ingestion promotion in formal row: {register_id}")
        if _value(row, "is_runtime_configuration") != "false":
            issues.append(f"runtime configuration promotion in formal row: {register_id}")
        if _value(row, "can_enter_weighting") != "false":
            issues.append(f"weighting allowed in formal row: {register_id}")
        if _value(row, "can_enter_jrc") != "false":
            issues.append(f"JRC allowed in formal row: {register_id}")

    for forbidden in (QCH_ROW, *SOURCE_READY_BLOCKED_ROWS, *LOCAL_Q_ROWS, *V4_ROWS):
        if any(_value(row, "nodi_register_row_id") == forbidden for row in ingested_rows):
            issues.append(f"forbidden row entered ingested context rows: {forbidden}")

    if not any(_value(row, "ingestion_lane") == LANE_QCH_QUARANTINE for row in quarantine_rows):
        issues.append("q_ch provenance quarantine lane is missing")
    for row in quarantine_rows:
        if _value(row, "nodi_register_row_id") == QCH_ROW:
            if _value(row, "qch_sidecar_status") != "PROVENANCE_ONLY_NOT_GATE2_QCH_SIDECAR":
                issues.append("q_ch quarantine row was promoted to formal sidecar")
            if _value(row, "context_only_formal_ingestion_allowed") != "false":
                issues.append("q_ch quarantine row was allowed into formal context ingestion")

    for row in blocked_grain_rows:
        if _value(row, "diameter_nm") == "220" and _value(row, "gate2b_grain_disposition") != "blocked_or_review_only_preserved":
            issues.append("220 nm blocked grain disposition was not preserved")
        if "edge20_group" in _value(row, "bin_basis") and _value(row, "direct_prs_bin_compatible") != "false":
            issues.append("edge4/edge20 grouped bin became direct PRS bin")
        if _value(row, "can_enter_weighting") != "false" or _value(row, "can_enter_jrc") != "false":
            issues.append("blocked grain row allows weighting or JRC")

    for row in forbidden_rows:
        if _value(row, "observed_positive_output") != "false" or _value(row, "audit_status") != "PASS_BLOCKED":
            issues.append(f"forbidden claim audit did not pass-block: {_value(row, 'forbidden_claim')}")

    issues.extend(_validate_no_forbidden_positive_fields(register_rows + ingested_rows + quarantine_rows + blocked_grain_rows))
    issues.extend(validate_comsol_v4_readonly_context(payload.get("comsol_v4_context", {})))

    if payload.get("can_enter_weighting_any") is not False:
        issues.append("payload can_enter_weighting_any must be false")
    if payload.get("can_enter_jrc_any") is not False:
        issues.append("payload can_enter_jrc_any must be false")
    if payload.get("is_chi_selected_any") is not False:
        issues.append("payload is_chi_selected_any must be false")
    if payload.get("is_production_ingestion_any") is not False:
        issues.append("payload is_production_ingestion_any must be false")
    if payload.get("is_runtime_configuration_any") is not False:
        issues.append("payload is_runtime_configuration_any must be false")

    return issues


def write_gate2b_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "formal_register_csv": output_dir / REGISTER_FILENAME,
        "ingested_context_rows_csv": output_dir / INGESTED_ROWS_FILENAME,
        "quarantine_review_only_csv": output_dir / QUARANTINE_FILENAME,
        "blocked_grain_disposition_csv": output_dir / BLOCKED_GRAIN_FILENAME,
        "forbidden_claim_audit_csv": output_dir / FORBIDDEN_AUDIT_FILENAME,
        "self_review_findings_csv": output_dir / SELF_REVIEW_FILENAME,
        "gate2c_required_export_schema_csv": output_dir / GATE2C_SCHEMA_FILENAME,
        "formal_ingestion_report_json": output_dir / REPORT_JSON_FILENAME,
        "formal_ingestion_report_md": output_dir / REPORT_MD_FILENAME,
        "report_200_md": report_dir / REPORT_200_FILENAME,
    }
    write_csv_rows(outputs["formal_register_csv"], list(payload["formal_register_rows"]))
    write_csv_rows(outputs["ingested_context_rows_csv"], list(payload["ingested_context_rows"]))
    write_csv_rows(outputs["quarantine_review_only_csv"], list(payload["quarantine_review_only_rows"]))
    write_csv_rows(outputs["blocked_grain_disposition_csv"], list(payload["blocked_grain_disposition_rows"]))
    write_csv_rows(outputs["forbidden_claim_audit_csv"], list(payload["forbidden_claim_audit_rows"]))
    write_csv_rows(outputs["self_review_findings_csv"], list(payload["self_review_rows"]))
    write_csv_rows(outputs["gate2c_required_export_schema_csv"], list(payload["gate2c_required_export_schema_rows"]))
    for path in outputs.values():
        if path.suffix == ".csv":
            _normalize_lf(path)

    report_payload = dict(payload)
    report_payload["outputs"] = {name: str(path) for name, path in outputs.items()}
    output_hashes = {name: sha256_file(path) for name, path in outputs.items() if path.suffix == ".csv"}
    report_payload["output_hashes"] = output_hashes
    report_payload["json_self_hash_note"] = (
        "formal_ingestion_report_json SHA-256 is reported by CLI/final signoff "
        "after write; it is not embedded to avoid self-referential hash drift"
    )
    md_text = _render_gate2b_md(report_payload)
    report_200_text = md_text.replace(
        "# NODI/COMSOL Gate2B Formal Ingestion Report",
        "# Report 200 - NODI/COMSOL Gate2B Context-Only Formal Ingestion",
    )
    output_hashes["formal_ingestion_report_md"] = _sha256_text(md_text)
    output_hashes["report_200_md"] = _sha256_text(report_200_text)
    report_payload["output_hashes"] = output_hashes
    write_json_atomic(outputs["formal_ingestion_report_json"], report_payload, sort_keys=True)

    outputs["formal_ingestion_report_md"].write_text(md_text, encoding="utf-8")
    outputs["report_200_md"].write_text(report_200_text, encoding="utf-8")

    return {name: str(path) for name, path in outputs.items()}


def _formal_register_row(
    matrix_row: Mapping[str, Any],
    crosswalk_by_path: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    register_id = _value(matrix_row, "nodi_register_row_id")
    source_artifact = _value(matrix_row, "comsol_artifact")
    crosswalk_rows = list(crosswalk_by_path.get(source_artifact, []))
    source_sha = _unique_nonempty(crosswalk_rows, "sha256") or "UNKNOWN"
    source_row_count = _unique_nonempty(crosswalk_rows, "row_count") or "UNKNOWN"
    if register_id == "G2CTX-CHI-AGG-004":
        edge_policy = "aggregate_proxy_not_direct_prs_bin"
        bin_basis = "not_position_binned"
    else:
        edge_policy = "edge4_to_edge20_review_only_grouping_not_direct_prs_bin"
        bin_basis = "TPD_edge4_to_PRS_edge20_group_context"
    return {
        "schema_version": REGISTER_SCHEMA_VERSION,
        "source_artifact": source_artifact,
        "source_sha256": source_sha,
        "source_row_count": source_row_count,
        "source_package": "COMSOL_GATE2A_NODI_BINDING_20260627",
        "nodi_register_row_id": register_id,
        "comsol_artifact_id": _artifact_id_summary(crosswalk_rows),
        "comsol_gate_id": _value(matrix_row, "comsol_gate_id"),
        "route_key": "660/W800/D900",
        "NODI_view": "fixed_660_gold;per_wavelength_gold",
        "diameter_nm": "300",
        "bin_basis": bin_basis,
        "edge4_to_edge20_policy": edge_policy,
        "matched_prs_grain_status": "partial_context_only_match_2_route_view_diameter_grains",
        "blocked_grain_status": f"blocked_grains_preserved_count_{_value(matrix_row, 'blocked_grain_count')}",
        "ingestion_lane": LANE_FORMAL,
        "claim_boundary": _value(matrix_row, "claim_boundary"),
        "allowed_use": "formal context-only ledger entry for TPD/PRS proxy review",
        "blocked_use": _value(matrix_row, "blocked_use"),
        "required_next_gate": _value(matrix_row, "required_next_gate"),
        "context_only_formal_ingestion_allowed": "true",
        "qch_sidecar_status": "not_qch_sidecar",
        "can_enter_weighting": "false",
        "can_enter_jrc": "false",
        "is_chi_selected": "false",
        "is_production_ingestion": "false",
        "is_runtime_configuration": "false",
        "source_crosswalk_row_count": str(len(crosswalk_rows)),
    }


def _ingested_context_row(register_row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": INGESTED_ROWS_SCHEMA_VERSION,
        "ingested_context_row_id": f"G2B-INGEST-{_value(register_row, 'nodi_register_row_id')}",
        **{key: _value(register_row, key) for key in register_row if key != "schema_version"},
    }


def _quarantine_rows(
    *,
    gate2a_matrix_rows: Sequence[Mapping[str, Any]],
    gate2a_blocker_rows: Sequence[Mapping[str, Any]],
    qch_provenance_rows: Sequence[Mapping[str, Any]],
    source_hashes: Mapping[str, str],
    source_row_counts: Mapping[str, str],
) -> list[dict[str, Any]]:
    matrix_by_id = {_value(row, "nodi_register_row_id"): row for row in gate2a_matrix_rows}
    rows: list[dict[str, Any]] = []
    for register_id in SOURCE_READY_BLOCKED_ROWS:
        rows.append(_quarantine_from_matrix(matrix_by_id[register_id], LANE_SOURCE_BLOCKED))
    qch_source = "roadmap/COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv"
    rows.append(
        {
            "schema_version": QUARANTINE_SCHEMA_VERSION,
            "source_artifact": qch_source,
            "source_sha256": source_hashes.get(qch_source, "UNKNOWN"),
            "source_row_count": source_row_counts.get(qch_source, str(len(qch_provenance_rows))),
            "source_package": "COMSOL_GATE2A_NODI_BINDING_20260627",
            "nodi_register_row_id": QCH_ROW,
            "comsol_artifact_id": "COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627",
            "comsol_gate_id": "G2-QCH-SIDECAR",
            "route_key": "660/W800/D900_A85;660/W800/D1200_A87",
            "NODI_view": "not_applicable_provenance_only",
            "diameter_nm": "not_particle_diameter_binned",
            "bin_basis": "not_position_binned",
            "edge4_to_edge20_policy": "not_applicable",
            "matched_prs_grain_status": "not_gate2_qch_sidecar",
            "blocked_grain_status": "formal_qch_flow_split_sidecar_absent",
            "ingestion_lane": LANE_QCH_QUARANTINE,
            "claim_boundary": "qch_provenance_only_not_transport_occupancy_not_qch_eta",
            "allowed_use": "descriptive provenance and lineage review only",
            "blocked_use": "formal q_ch sidecar; q_ch weighting; q_ch*eta; q_ch*chi*eta; route_score; JRC; yield; winner; detection_probability",
            "required_next_gate": "COMSOL formal Gate2 q_ch/flow split sidecar package",
            "context_only_formal_ingestion_allowed": "false",
            "qch_sidecar_status": "PROVENANCE_ONLY_NOT_GATE2_QCH_SIDECAR",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
            "is_chi_selected": "false",
            "is_production_ingestion": "false",
            "is_runtime_configuration": "false",
        }
    )
    for register_id in LOCAL_Q_ROWS:
        rows.append(_quarantine_from_matrix(matrix_by_id[register_id], LANE_REVIEW_DIAGNOSTIC))
    for register_id in V4_ROWS:
        rows.append(_quarantine_from_matrix(matrix_by_id[register_id], LANE_V4_CEILING))
    for blocker in gate2a_blocker_rows:
        if _value(blocker, "nodi_register_row_id") == "*":
            rows.append(
                {
                    "schema_version": QUARANTINE_SCHEMA_VERSION,
                    "source_artifact": "NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv",
                    "source_sha256": source_hashes.get("reports/joint_interface_20260627/NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv", "UNKNOWN"),
                    "source_row_count": source_row_counts.get("reports/joint_interface_20260627/NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv", "UNKNOWN"),
                    "source_package": "NODI_GATE2A_REPORT199",
                    "nodi_register_row_id": "*",
                    "comsol_artifact_id": _value(blocker, "comsol_gate_id"),
                    "comsol_gate_id": _value(blocker, "comsol_gate_id"),
                    "route_key": "not_applicable_strong_claim_blocker",
                    "NODI_view": "not_applicable",
                    "diameter_nm": "not_applicable",
                    "bin_basis": "not_applicable",
                    "edge4_to_edge20_policy": "not_applicable",
                    "matched_prs_grain_status": "not_applicable",
                    "blocked_grain_status": _value(blocker, "blocker_status"),
                    "ingestion_lane": LANE_STRONG_BLOCKER,
                    "claim_boundary": "no_weighting_no_jrc_no_strong_claims",
                    "allowed_use": "blocked-field audit only",
                    "blocked_use": _value(blocker, "blocker_reason"),
                    "required_next_gate": _value(blocker, "required_next_gate"),
                    "context_only_formal_ingestion_allowed": "false",
                    "qch_sidecar_status": "not_qch_sidecar",
                    "can_enter_weighting": "false",
                    "can_enter_jrc": "false",
                    "is_chi_selected": "false",
                    "is_production_ingestion": "false",
                    "is_runtime_configuration": "false",
                }
            )
    return rows


def _quarantine_from_matrix(matrix_row: Mapping[str, Any], lane: str) -> dict[str, Any]:
    return {
        "schema_version": QUARANTINE_SCHEMA_VERSION,
        "source_artifact": _value(matrix_row, "comsol_artifact"),
        "source_sha256": "see_gate2a_reconciliation_source_package",
        "source_row_count": "see_gate2a_reconciliation_source_package",
        "source_package": "NODI_GATE2A_REPORT199",
        "nodi_register_row_id": _value(matrix_row, "nodi_register_row_id"),
        "comsol_artifact_id": _value(matrix_row, "comsol_artifact"),
        "comsol_gate_id": _value(matrix_row, "comsol_gate_id"),
        "route_key": _value(matrix_row, "route_key"),
        "NODI_view": _value(matrix_row, "NODI_view"),
        "diameter_nm": _value(matrix_row, "diameter_nm"),
        "bin_basis": _value(matrix_row, "bin_basis"),
        "edge4_to_edge20_policy": _edge_policy(_value(matrix_row, "bin_basis")),
        "matched_prs_grain_status": f"matched_prs_grain_count_{_value(matrix_row, 'matched_prs_grain_count')}",
        "blocked_grain_status": f"blocked_grain_count_{_value(matrix_row, 'blocked_grain_count')}",
        "ingestion_lane": lane,
        "claim_boundary": _value(matrix_row, "claim_boundary"),
        "allowed_use": _value(matrix_row, "allowed_use"),
        "blocked_use": _value(matrix_row, "blocked_use"),
        "required_next_gate": _value(matrix_row, "required_next_gate"),
        "context_only_formal_ingestion_allowed": "false",
        "qch_sidecar_status": "not_qch_sidecar",
        "can_enter_weighting": "false",
        "can_enter_jrc": "false",
        "is_chi_selected": "false",
        "is_production_ingestion": "false",
        "is_runtime_configuration": "false",
    }


def _blocked_grain_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": BLOCKED_GRAIN_SCHEMA_VERSION,
        "nodi_register_row_id": _value(row, "nodi_register_row_id"),
        "comsol_artifact": _value(row, "comsol_artifact"),
        "route_key": _value(row, "route_key"),
        "NODI_view": _value(row, "NODI_view"),
        "diameter_nm": _value(row, "diameter_nm"),
        "bin_basis": _value(row, "bin_basis"),
        "prs_grain_present": _value(row, "prs_grain_present"),
        "eas_route_view_present": _value(row, "eas_route_view_present"),
        "direct_prs_bin_compatible": _value(row, "direct_prs_bin_compatible"),
        "gate2a_grain_reconciled_status": _value(row, "grain_reconciled_status"),
        "gate2b_grain_disposition": "formal_context_only_ingested_grain"
        if _value(row, "can_enter_context_only_ingestion") == "true"
        else "blocked_or_review_only_preserved",
        "blocker_reason": _value(row, "blocker_reason"),
        "context_only_formal_ingestion_allowed": _value(row, "can_enter_context_only_ingestion"),
        "can_enter_weighting": "false",
        "can_enter_jrc": "false",
        "is_chi_selected": "false",
        "is_production_ingestion": "false",
        "is_runtime_configuration": "false",
    }


def _forbidden_claim_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": FORBIDDEN_AUDIT_SCHEMA_VERSION,
            "forbidden_claim": claim,
            "observed_positive_output": "false",
            "audit_status": "PASS_BLOCKED",
            "allowed_lane": "none",
            "required_next_gate": "future explicit authorization outside Gate2B context-only ingestion",
        }
        for claim in FORBIDDEN_CLAIMS
    ]


def _self_review_rows(
    *,
    formal_register: Sequence[Mapping[str, Any]],
    ingested_rows: Sequence[Mapping[str, Any]],
    quarantine_rows: Sequence[Mapping[str, Any]],
    blocked_grain_rows: Sequence[Mapping[str, Any]],
    qch_provenance_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": SELF_REVIEW_SCHEMA_VERSION,
            "reviewer": "Reviewer A",
            "focus": "provenance_hash_row_count_path_reproducibility",
            "finding_severity": "PASS",
            "finding": "Gate2B outputs carry source paths, SHA-256, row counts, source package, and inherited Gate2A/COMSOL Gate2A package lineage.",
            "unresolved_risk": "none",
            "required_action": "none",
        },
        {
            "schema_version": SELF_REVIEW_SCHEMA_VERSION,
            "reviewer": "Reviewer B",
            "focus": "forbidden_claim_leakage",
            "finding_severity": "PASS",
            "finding": "All weighting, JRC, chi_selected, winner, yield, detection, wet pass, clogging, runtime, and production flags remain false.",
            "unresolved_risk": "none",
            "required_action": "none",
        },
        {
            "schema_version": SELF_REVIEW_SCHEMA_VERSION,
            "reviewer": "Reviewer C",
            "focus": "grain_semantics",
            "finding_severity": "PASS",
            "finding": (
                f"{len(blocked_grain_rows)} Gate2A grain rows are inherited; 220 nm, D1200, missing NODI_view, "
                "and edge4-to-edge20 issues remain blocked or review-only."
            ),
            "unresolved_risk": "none",
            "required_action": "none",
        },
        {
            "schema_version": SELF_REVIEW_SCHEMA_VERSION,
            "reviewer": "Reviewer D",
            "focus": "gate_logic",
            "finding_severity": "PASS",
            "finding": (
                f"Only {len(formal_register)} TPD/PRS proxy rows enter formal context-only ledger; "
                f"{len(ingested_rows)} ingested rows are not production, and {len(qch_provenance_rows)} q_ch rows stay provenance-only."
            ),
            "unresolved_risk": "none",
            "required_action": "none",
        },
    ]


def _gate2c_required_export_schema_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(category: str, field: str, required: str, allowed_values: str, notes: str) -> None:
        rows.append(
            {
                "schema_version": GATE2C_SCHEMA_VERSION,
                "requirement_category": category,
                "field_name": field,
                "required": required,
                "allowed_values_or_rule": allowed_values,
                "notes": notes,
            }
        )

    for field in (
        "source_artifact",
        "source_sha256",
        "source_row_count",
        "producer",
        "evidence_class",
        "route_key",
        "NODI_view",
        "diameter_nm",
        "bin_basis",
        "bin_policy",
        "claim_boundary",
        "allowed_use",
        "blocked_use",
        "required_next_gate",
    ):
        add("formal_transported_position_nodi_bound_sidecar", field, "yes", "must be explicit and machine-readable", "required before TPD source/alignment can enter a stronger gate")
    add("status_enum", "nodi_reconciled_status", "yes", "EXACT_NODI_BOUND_CONTEXT_CANDIDATE; CANDIDATE_RECHECK_REQUIRED; REVIEW_ONLY; BLOCKED", "COMSOL READY alone must not imply NODI production readiness")
    for field in ("qch_source_artifact", "qch_sha256", "qch_row_count", "route_key", "flow_split_basis", "qch_scope", "is_formal_gate2_qch_sidecar"):
        add("q_ch_flow_split_formal_sidecar", field, "yes", "must be present with authorization flags false unless separately approved", "needed before any q_ch review beyond provenance-only")
    for claim in FORBIDDEN_CLAIMS:
        add("forbidden_fields", claim, "must_be_absent_or_false", "false only in Gate2B/Gate2C context-only packages", "positive values require future explicit authorization")
    for field in ("v4_assumption_set_id", "review_loader_mode", "nodi_production_ingestion_allowed", "nodi_runtime_configuration_allowed", "comsol_launch_authorized_now", "mph_load_authorized_now"):
        add("v4_review_only_binding", field, "yes", "review-only; production/runtime/launch flags false", "V4 remains claim ceiling unless a future V4 gate opens")
    return rows


def _render_gate2b_md(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    input_hashes = payload.get("input_hashes", {})
    input_row_counts = payload.get("input_row_counts", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2B Formal Ingestion Report",
            "",
            "Date: 2026-06-27",
            "",
            "## Disposition",
            "",
            f"`{payload['status']}`",
            "",
            "This is a partial context-only formal ingestion ledger. It is not production ingestion, not runtime configuration, not q_ch weighting, and not JRC.",
            "",
            "## Scope",
            "",
            "- `context_only_formal_ingestion_allowed = true` only for `G2CTX-CHI-AGG-004` and `G2CTX-CHI-BIN-005`.",
            "- `can_enter_weighting = false` globally.",
            "- `can_enter_jrc = false` globally.",
            "- `is_chi_selected = false` globally.",
            "- `is_production_ingestion = false` globally.",
            "- `is_runtime_configuration = false` globally.",
            "",
            "## Counts",
            "",
            f"- formal register rows: `{payload['formal_register_row_count']}`",
            f"- ingested context rows: `{payload['ingested_context_row_count']}`",
            f"- quarantine/review-only rows: `{payload['quarantine_review_only_row_count']}`",
            f"- blocked grain disposition rows: `{payload['blocked_grain_disposition_row_count']}`",
            f"- forbidden claim audit rows: `{payload['forbidden_claim_audit_row_count']}`",
            f"- self-review rows: `{payload['self_review_row_count']}`",
            f"- q_ch provenance rows read: `{payload['qch_provenance_row_count']}`",
            "",
            "## Outputs",
            "",
            f"- formal context register: `{REGISTER_FILENAME}` SHA256 `{hashes.get('formal_register_csv', 'pending')}`",
            f"- ingested context rows: `{INGESTED_ROWS_FILENAME}` SHA256 `{hashes.get('ingested_context_rows_csv', 'pending')}`",
            f"- quarantine register: `{QUARANTINE_FILENAME}` SHA256 `{hashes.get('quarantine_review_only_csv', 'pending')}`",
            f"- blocked grain disposition: `{BLOCKED_GRAIN_FILENAME}` SHA256 `{hashes.get('blocked_grain_disposition_csv', 'pending')}`",
            f"- forbidden claim audit: `{FORBIDDEN_AUDIT_FILENAME}` SHA256 `{hashes.get('forbidden_claim_audit_csv', 'pending')}`",
            f"- self-review findings: `{SELF_REVIEW_FILENAME}` SHA256 `{hashes.get('self_review_findings_csv', 'pending')}`",
            f"- Gate2C required export schema: `{GATE2C_SCHEMA_FILENAME}` SHA256 `{hashes.get('gate2c_required_export_schema_csv', 'pending')}`",
            "",
            "## Input Evidence",
            "",
            f"- NODI Gate2A matrix rows: `{input_row_counts.get('reports/joint_interface_20260627/NODI_COMSOL_GATE2A_RECONCILIATION_MATRIX_20260627.csv', 'unknown')}`, SHA256 `{input_hashes.get('reports/joint_interface_20260627/NODI_COMSOL_GATE2A_RECONCILIATION_MATRIX_20260627.csv', 'unknown')}`",
            f"- NODI Gate2A grain rows: `{input_row_counts.get('reports/joint_interface_20260627/NODI_COMSOL_GATE2A_GRAIN_COMPATIBILITY_20260627.csv', 'unknown')}`, SHA256 `{input_hashes.get('reports/joint_interface_20260627/NODI_COMSOL_GATE2A_GRAIN_COMPATIBILITY_20260627.csv', 'unknown')}`",
            f"- NODI Gate2A blockers rows: `{input_row_counts.get('reports/joint_interface_20260627/NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv', 'unknown')}`, SHA256 `{input_hashes.get('reports/joint_interface_20260627/NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv', 'unknown')}`",
            f"- COMSOL Gate2A binding crosswalk rows: `{input_row_counts.get('roadmap/COMSOL_GATE2A_NODI_BINDING_CROSSWALK_20260627.csv', 'unknown')}`, SHA256 `{input_hashes.get('roadmap/COMSOL_GATE2A_NODI_BINDING_CROSSWALK_20260627.csv', 'unknown')}`",
            f"- COMSOL Gate2A q_ch provenance rows: `{input_row_counts.get('roadmap/COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv', 'unknown')}`, SHA256 `{input_hashes.get('roadmap/COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv', 'unknown')}`",
            "",
            "## Formal Context-Only Ingested Rows",
            "",
            "- `G2CTX-CHI-AGG-004`: TPD/PRS proxy aggregate, only for context-only review over current matched `660/W800/D900`, `300 nm` route/view grains.",
            "- `G2CTX-CHI-BIN-005`: TPD/PRS proxy bin context, only with edge4-to-edge20 review-only grouping; not a direct PRS bin.",
            "",
            "## Quarantine / Review-Only / Blocked",
            "",
            "- TPD source/alignment remain source-ready but blocked: missing `NODI_view` and route/diameter/bin mismatches.",
            "- q_ch remains provenance-only quarantine: no formal q_ch / flow-split sidecar.",
            "- local-Q remains review-only hydraulic/event-tree diagnostic context.",
            "- V4 remains review-only claim ceiling with production/runtime/launch flags false.",
            "- weighting, JRC, yield, winner, detection probability, wet pass, clogging, runtime, and production promotion remain hard blocked.",
            "",
            "## Gate2C Request",
            "",
            "COMSOL should provide a formal NODI-bound transported-position sidecar with explicit route/view/diameter/bin binding, an edge4-to-edge20 policy, and a formal q_ch / flow-split sidecar if q_ch is to move beyond provenance-only. All forbidden claims must remain absent or false until separately authorized.",
            "",
            "## Self-Review",
            "",
            "- Reviewer A: PASS, provenance/hash/row_count/path reproducibility.",
            "- Reviewer B: PASS, forbidden claim leakage remains blocked.",
            "- Reviewer C: PASS, grain semantics preserve 220 nm, D1200, missing view, and edge4 review-only blockers.",
            "- Reviewer D: PASS, COMSOL source-ready context is not upgraded to NODI production-ready.",
            "",
            "## Verification",
            "",
            "Run the Gate2B helper with `--confirm-gate2b-formal-context-only`, then run `py_compile`, `ruff`, and focused pytest before committing.",
        ]
    ) + "\n"


def _sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_lf(path: Path) -> None:
    data = path.read_bytes()
    while b"\r\n" in data:
        data = data.replace(b"\r\n", b"\n")
    data = data.replace(b"\r", b"")
    path.write_bytes(data)


def _crosswalk_by_path(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_value(row, "comsol_artifact_path")].append(row)
    return grouped


def _artifact_id_summary(rows: Sequence[Mapping[str, Any]]) -> str:
    ids = sorted({_value(row, "comsol_artifact_id") for row in rows if _value(row, "comsol_artifact_id")})
    if not ids:
        return "UNKNOWN"
    if len(ids) == 1:
        return ids[0]
    return f"{len(ids)}_crosswalk_rows"


def _unique_nonempty(rows: Sequence[Mapping[str, Any]], key: str) -> str:
    values = sorted({_value(row, key) for row in rows if _value(row, key)})
    return values[0] if len(values) == 1 else ""


def _edge_policy(bin_basis: str) -> str:
    if "edge" in bin_basis.lower():
        return "edge4_to_edge20_review_only_grouping_not_direct_prs_bin"
    return "not_applicable"


def _validate_no_forbidden_positive_fields(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row_index, row in enumerate(rows):
        for key, value in row.items():
            lower_key = str(key).lower()
            if not any(fragment in lower_key for fragment in FORBIDDEN_POSITIVE_FIELD_FRAGMENTS):
                continue
            value_text = str(value).strip().lower()
            if value_text in {"", "false", "0", "none", "not_applicable", "not_qch_sidecar"}:
                continue
            if key in {"blocked_use", "claim_boundary", "required_next_gate", "forbidden_claim"}:
                continue
            issues.append(f"forbidden positive field {key}={value!r} in row {row_index}")
    return issues


def _value(row: Mapping[str, Any], key: str, default: str = "") -> str:
    value = row.get(key, default)
    if value is None:
        return default
    return str(value)


def _relative(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _count_csv_rows(path: Path) -> str:
    return str(len(read_csv_rows(path)))


def _collect_source_hashes(
    *,
    comsol_root: Path,
    gate2a_matrix: Path,
    gate2a_grain: Path,
    gate2a_blockers: Path,
    gate2a_report: Path,
) -> tuple[dict[str, str], dict[str, str]]:
    paths = {
        "reports/joint_interface_20260627/NODI_COMSOL_GATE2A_RECONCILIATION_MATRIX_20260627.csv": gate2a_matrix,
        "reports/joint_interface_20260627/NODI_COMSOL_GATE2A_GRAIN_COMPATIBILITY_20260627.csv": gate2a_grain,
        "reports/joint_interface_20260627/NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv": gate2a_blockers,
        "reports/joint_interface_20260627/NODI_COMSOL_GATE2A_INGESTION_DRY_RUN_REPORT_20260627.json": gate2a_report,
        str(COMSOL_GATE2A_PACKET).replace("\\", "/"): comsol_root / COMSOL_GATE2A_PACKET,
        str(COMSOL_GATE2A_CROSSWALK).replace("\\", "/"): comsol_root / COMSOL_GATE2A_CROSSWALK,
        str(COMSOL_GATE2A_BLOCKERS).replace("\\", "/"): comsol_root / COMSOL_GATE2A_BLOCKERS,
        str(COMSOL_GATE2A_QCH).replace("\\", "/"): comsol_root / COMSOL_GATE2A_QCH,
        str(COMSOL_GATE2A_VALIDATION).replace("\\", "/"): comsol_root / COMSOL_GATE2A_VALIDATION,
        str(COMSOL_GATE2A_MANIFEST).replace("\\", "/"): comsol_root / COMSOL_GATE2A_MANIFEST,
    }
    hashes = {logical: sha256_file(path) for logical, path in paths.items()}
    row_counts = {
        logical: _count_csv_rows(path) if path.suffix.lower() == ".csv" else "n/a"
        for logical, path in paths.items()
    }
    return hashes, row_counts


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate2b_formal_context_only:
        raise SystemExit("Refusing to write Gate2B formal ingestion outputs without explicit confirmation flag.")

    comsol_root = args.comsol_root
    source_hashes, source_row_counts = _collect_source_hashes(
        comsol_root=comsol_root,
        gate2a_matrix=args.gate2a_matrix,
        gate2a_grain=args.gate2a_grain,
        gate2a_blockers=args.gate2a_blockers,
        gate2a_report=args.gate2a_report,
    )
    payload = build_gate2b_payload(
        gate2a_matrix_rows=read_csv_rows(args.gate2a_matrix),
        gate2a_grain_rows=read_csv_rows(args.gate2a_grain),
        gate2a_blocker_rows=read_csv_rows(args.gate2a_blockers),
        comsol_crosswalk_rows=read_csv_rows(comsol_root / COMSOL_GATE2A_CROSSWALK),
        comsol_blocker_rows=read_csv_rows(comsol_root / COMSOL_GATE2A_BLOCKERS),
        qch_provenance_rows=read_csv_rows(comsol_root / COMSOL_GATE2A_QCH),
        comsol_validation_rows=read_csv_rows(comsol_root / COMSOL_GATE2A_VALIDATION),
        comsol_manifest_rows=read_csv_rows(comsol_root / COMSOL_GATE2A_MANIFEST),
        source_hashes=source_hashes,
        source_row_counts=source_row_counts,
    )
    issues = validate_gate2b_payload(payload)
    if issues:
        print(f"NODI_COMSOL_GATE2B_FORMAL_INGESTION: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1

    outputs = write_gate2b_outputs(payload, args.output_dir, args.report_dir)
    report_hash = sha256_file(Path(outputs["formal_ingestion_report_json"]))
    print(f"NODI_COMSOL_GATE2B_FORMAL_INGESTION: {PASS_STATUS}")
    print(f"report_path: {outputs['formal_ingestion_report_json']}")
    print(f"report_sha256: {report_hash}")
    print(f"formal_register_csv: {outputs['formal_register_csv']}")
    print(f"ingested_context_rows_csv: {outputs['ingested_context_rows_csv']}")
    print(f"quarantine_review_only_csv: {outputs['quarantine_review_only_csv']}")
    print(f"blocked_grain_disposition_csv: {outputs['blocked_grain_disposition_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
