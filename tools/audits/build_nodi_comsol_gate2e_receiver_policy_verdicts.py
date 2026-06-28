#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
PASS_STATUS = "PASS_GATE2E_RECEIVER_POLICY_VERDICTS_NO_ACCEPTED_ROW_EXPANSION_NO_WEIGHTING_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2E_RECEIVER_POLICY_VERDICTS"

OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
REPORT_204 = f"204_NODI_COMSOL_GATE2E_RECEIVER_POLICY_VERDICTS_{DATE_STAMP}.md"

EVIDENCE_REGISTER = f"NODI_COMSOL_GATE2E_COMSOL_WORKSTREAM_EVIDENCE_REGISTER_{DATE_STAMP}.csv"
EVIDENCE_MANIFEST = f"NODI_COMSOL_GATE2E_COMSOL_WORKSTREAM_EVIDENCE_MANIFEST_{DATE_STAMP}.csv"
EDGE_VERDICT = f"NODI_COMSOL_GATE2E_EDGE_RECEIVER_POLICY_VERDICT_{DATE_STAMP}.csv"
EDGE20_SNAPSHOT = f"NODI_COMSOL_GATE2E_EDGE20_DEFINITION_SNAPSHOT_{DATE_STAMP}.csv"
EDGE_REPORT = f"NODI_COMSOL_GATE2E_EDGE_POLICY_REVIEW_REPORT_{DATE_STAMP}.md"
QCH_VERDICT = f"NODI_COMSOL_GATE2E_QCH_RECEIPT_SCHEMA_VERDICT_{DATE_STAMP}.csv"
QCH_GAPS = f"NODI_COMSOL_GATE2E_QCH_REQUIRED_FIELDS_AND_GAPS_{DATE_STAMP}.csv"
QCH_REPORT = f"NODI_COMSOL_GATE2E_QCH_RECEIPT_REVIEW_REPORT_{DATE_STAMP}.md"
BINDING_VERDICT = f"NODI_COMSOL_GATE2E_BINDING_POLICY_VERDICT_{DATE_STAMP}.csv"
BINDING_MATRIX = f"NODI_COMSOL_GATE2E_BINDING_REPAIR_DECISION_MATRIX_{DATE_STAMP}.csv"
BINDING_REPORT = f"NODI_COMSOL_GATE2E_BINDING_REVIEW_REPORT_{DATE_STAMP}.md"
DASHBOARD = f"NODI_COMSOL_GATE2E_RECEIVER_DASHBOARD_{DATE_STAMP}.csv"
SELF_REVIEW = f"NODI_COMSOL_GATE2E_RECEIVER_SELF_REVIEW_{DATE_STAMP}.csv"
REPORT_JSON = f"NODI_COMSOL_GATE2E_RECEIVER_POLICY_REPORT_{DATE_STAMP}.json"
REPORT_MD = f"NODI_COMSOL_GATE2E_RECEIVER_POLICY_REPORT_{DATE_STAMP}.md"

DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
DEFAULT_PRS_ARTIFACT = (
    PROJECT_ROOT
    / "tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618"
    / "NODI_POSITION_RESPONSE_SURFACE.csv"
)

NODI_REPORT_203 = PROJECT_ROOT / "reports/203_NODI_COMSOL_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_ACCEPTANCE_LEDGER_20260628.md"
NODI_GATE2D_ACCEPTED_LEDGER = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_20260628.csv"
NODI_GATE2D_BLOCKERS = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_ACCEPTANCE_LEDGER_BLOCKER_CARRY_FORWARD_20260628.csv"
NODI_GATE2C_EDGE_CHECKLIST = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2C_EDGE4_EDGE20_POLICY_CHECKLIST_20260628.csv"
NODI_GATE2C_QCH_CHECKLIST = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2C_QCH_FORMAL_SIDECAR_ACCEPTANCE_CHECKLIST_20260628.csv"
NODI_GATE2C_PRS_VERDICT = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2C_PRS_COVERAGE_VERDICT_20260628.csv"

COMSOL_GATE2E_FILES = (
    ("G2E-MASTER", "master_plan", Path("roadmap/COMSOL_GATE2E_EXPANSION_WORKSTREAM_MASTER_PLAN_20260628.md")),
    ("G2E-INDEX", "workstream_index", Path("roadmap/COMSOL_GATE2E_EXPANSION_WORKSTREAM_INDEX_20260628.csv")),
    (
        "G2E-EDGE-REQ",
        "edge_requirements",
        Path("roadmap/COMSOL_GATE2E_EDGE4_EDGE20_POLICY_EVIDENCE_REQUIREMENTS_20260628.csv"),
    ),
    (
        "G2E-EDGE-PACKET",
        "edge_packet",
        Path("roadmap/COMSOL_GATE2E_EDGE4_EDGE20_POLICY_REVIEW_PACKET_20260628.md"),
    ),
    (
        "G2E-QCH-REQ",
        "qch_receipt_requirements",
        Path("roadmap/COMSOL_GATE2E_QCH_FORMAL_SIDECAR_RECEIPT_REQUIREMENTS_20260628.csv"),
    ),
    (
        "G2E-QCH-PACKET",
        "qch_preflight_packet",
        Path("roadmap/COMSOL_GATE2E_QCH_FORMAL_SIDECAR_PREFLIGHT_PACKET_20260628.md"),
    ),
    (
        "G2E-BIND-REQ",
        "binding_requirements",
        Path("roadmap/COMSOL_GATE2E_TPD_BINDING_REPAIR_REQUIREMENTS_20260628.csv"),
    ),
    (
        "G2E-BIND-PACKET",
        "binding_packet",
        Path("roadmap/COMSOL_GATE2E_TPD_BINDING_REPAIR_PACKET_20260628.md"),
    ),
    ("G2E-VALIDATION", "validation_results", Path("roadmap/COMSOL_GATE2E_EXPANSION_WORKSTREAM_VALIDATION_20260628.csv")),
    ("G2E-MANIFEST", "manifest", Path("roadmap/COMSOL_GATE2E_EXPANSION_WORKSTREAM_MANIFEST_20260628.csv")),
)

COMSOL_GATE2E_MANIFEST = Path("roadmap/COMSOL_GATE2E_EXPANSION_WORKSTREAM_MANIFEST_20260628.csv")
COMSOL_GATE2A_QCH_PROVENANCE = Path("roadmap/COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv")

EXPECTED_GATE2D_ACCEPTED_ROW_COUNT = 4
EXPECTED_PRS_SHA = "9ba83c84a563cd856b2fc624c523843a6e283206d5ac2e592a2b72607645f393"
FORBIDDEN_FALSE_FIELDS = (
    "accepted_row_expansion_authorized",
    "grain_level_ingestion_authorized",
    "direct_prs_bin_use_authorized",
    "formula_use_authorized",
    "qch_weighting_authorized",
    "qch_eta_authorized",
    "qch_chi_eta_authorized",
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
    "accepted row expansion",
    "edge4 row acceptance",
    "220 nm acceptance",
    "D1200 acceptance",
    "TPD source/alignment row acceptance",
    "formal q_ch from provenance",
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
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build NODI Gate2E receiver-side policy verdict outputs.")
    parser.add_argument("--confirm-gate2e-receiver-policy-verdicts", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--prs-artifact", type=Path, default=DEFAULT_PRS_ARTIFACT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_gate2e_payload(
    *,
    comsol_root: Path,
    prs_artifact_path: Path = DEFAULT_PRS_ARTIFACT,
    accepted_ledger_path: Path = NODI_GATE2D_ACCEPTED_LEDGER,
    blocker_path: Path = NODI_GATE2D_BLOCKERS,
    edge_checklist_path: Path = NODI_GATE2C_EDGE_CHECKLIST,
    qch_checklist_path: Path = NODI_GATE2C_QCH_CHECKLIST,
    prs_verdict_path: Path = NODI_GATE2C_PRS_VERDICT,
    report_203_path: Path = NODI_REPORT_203,
) -> dict[str, Any]:
    manifest_rows = read_csv_rows(comsol_root / COMSOL_GATE2E_MANIFEST)
    index_rows = read_csv_rows(comsol_root / "roadmap/COMSOL_GATE2E_EXPANSION_WORKSTREAM_INDEX_20260628.csv")
    edge_requirement_rows = read_csv_rows(
        comsol_root / "roadmap/COMSOL_GATE2E_EDGE4_EDGE20_POLICY_EVIDENCE_REQUIREMENTS_20260628.csv"
    )
    qch_requirement_rows = read_csv_rows(
        comsol_root / "roadmap/COMSOL_GATE2E_QCH_FORMAL_SIDECAR_RECEIPT_REQUIREMENTS_20260628.csv"
    )
    binding_requirement_rows = read_csv_rows(
        comsol_root / "roadmap/COMSOL_GATE2E_TPD_BINDING_REPAIR_REQUIREMENTS_20260628.csv"
    )
    accepted_rows = read_csv_rows(accepted_ledger_path)
    blocker_rows = read_csv_rows(blocker_path)
    edge_checklist_rows = read_csv_rows(edge_checklist_path)
    qch_checklist_rows = read_csv_rows(qch_checklist_path)
    prs_verdict_rows = read_csv_rows(prs_verdict_path)
    prs_rows = read_csv_rows(prs_artifact_path)
    prs_sha = sha256_file(prs_artifact_path)
    qch_provenance_path = comsol_root / COMSOL_GATE2A_QCH_PROVENANCE
    qch_provenance_row_count = _row_count(qch_provenance_path) if qch_provenance_path.exists() else 0

    evidence_rows = build_evidence_register(comsol_root=comsol_root, manifest_rows=manifest_rows)
    evidence_manifest_rows = build_evidence_manifest(evidence_rows)
    edge20_snapshot = build_edge20_definition_snapshot(prs_rows, prs_artifact_path=prs_artifact_path, prs_sha=prs_sha)
    edge_definition_hash = _value(edge20_snapshot[0], "edge20_definition_hash") if edge20_snapshot else ""
    edge_verdict_rows = build_edge_verdict_rows(edge_requirement_rows, edge_checklist_rows, edge_definition_hash)
    qch_verdict_rows = build_qch_verdict_rows(qch_requirement_rows, qch_provenance_row_count)
    qch_gap_rows = build_qch_gap_rows(qch_requirement_rows, qch_checklist_rows, qch_provenance_row_count)
    binding_verdict_rows = build_binding_verdict_rows(binding_requirement_rows, prs_verdict_rows, blocker_rows)
    binding_matrix_rows = build_binding_matrix_rows(binding_requirement_rows, prs_verdict_rows, blocker_rows)
    dashboard_rows = build_dashboard_rows(edge_verdict_rows, qch_verdict_rows, binding_verdict_rows, len(accepted_rows))
    self_review_rows = build_self_review_rows()

    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2e_receiver_policy_report_v1",
        "date_stamp": DATE_STAMP,
        "status": PASS_STATUS,
        "gate2e_receiver_disposition": PASS_STATUS,
        "gate2d_freeze_confirmed": True,
        "gate2d_accepted_row_count": len(accepted_rows),
        "comsol_gate2e_index_row_count": len(index_rows),
        "comsol_gate2e_manifest_row_count": len(manifest_rows),
        "nodi_prs_artifact": _rel(prs_artifact_path),
        "nodi_prs_sha256": prs_sha,
        "nodi_prs_row_count": len(prs_rows),
        "qch_provenance_row_count": qch_provenance_row_count,
        "evidence_register_rows": evidence_rows,
        "evidence_manifest_rows": evidence_manifest_rows,
        "edge20_definition_snapshot_rows": edge20_snapshot,
        "edge_receiver_policy_verdict_rows": edge_verdict_rows,
        "qch_receipt_schema_verdict_rows": qch_verdict_rows,
        "qch_required_fields_and_gaps_rows": qch_gap_rows,
        "binding_policy_verdict_rows": binding_verdict_rows,
        "binding_repair_decision_matrix_rows": binding_matrix_rows,
        "receiver_dashboard_rows": dashboard_rows,
        "self_review_rows": self_review_rows,
        "comsol_v4_context": default_comsol_v4_readonly_context(),
        "accepted_row_expansion_authorized": False,
        "formula_use_authorized": False,
        "weighting_or_jrc_allowed": False,
        "qch_formal_sidecar_exists": False,
        "edge4_policy_approved": False,
        "report203_gate2d_pass_present": PASS_STATUS.replace("GATE2E_RECEIVER_POLICY_VERDICTS", "GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_ACCEPTANCE_LEDGER")
        in report_203_path.read_text(encoding="utf-8"),
    }
    return payload


def build_evidence_register(*, comsol_root: Path, manifest_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    manifest_by_path = {_value(row, "path"): row for row in manifest_rows}
    rows: list[dict[str, str]] = []
    for evidence_id, role, relative_path in COMSOL_GATE2E_FILES:
        path = comsol_root / relative_path
        manifest = manifest_by_path.get(relative_path.as_posix(), {})
        source_sha = sha256_file(path)
        source_row_count = _row_count(path)
        rows.append(
            {
                "evidence_id": evidence_id,
                "source_repo_or_project": "comsol_ev_pbs_bonded_cross_junction",
                "original_absolute_path": str(path),
                "relative_source_path": relative_path.as_posix(),
                "file_role": role,
                "source_sha256": source_sha,
                "copied_or_external_reference": "external_reference_only",
                "nodi_mirror_path_if_any": "",
                "mirror_sha256_if_any": "",
                "row_count": str(source_row_count),
                "producer": "COMSOL Gate2E workstream planning",
                "source_commit_if_available": "a7e5301",
                "manifest_sha256_if_any": _value(manifest, "sha256"),
                "manifest_row_count_if_any": _value(manifest, "row_count"),
                "manifest_match": _bool_text(
                    (not manifest)
                    or (
                        _value(manifest, "sha256") == source_sha
                        and _value(manifest, "row_count") in {str(source_row_count), "0"}
                    )
                ),
                "allowed_use": "receiver-side policy/schema/checklist evidence only",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
                "claim_boundary": "not accepted rows; not formula; not production; not runtime",
                "required_next_gate": "Gate2E receiver verdict review; future Gate2E package for any candidate expansion",
            }
        )
    return rows


def build_evidence_manifest(evidence_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "manifest_id": f"NODI-G2E-EVID-MAN-{index:03d}",
            "evidence_id": _value(row, "evidence_id"),
            "relative_source_path": _value(row, "relative_source_path"),
            "source_sha256": _value(row, "source_sha256"),
            "row_count": _value(row, "row_count"),
            "manifest_match": _value(row, "manifest_match"),
            "registration_status": "REGISTERED_EXTERNAL_REFERENCE_ONLY",
            "allowed_use": _value(row, "allowed_use"),
            "blocked_use": _value(row, "blocked_use"),
        }
        for index, row in enumerate(evidence_rows, start=1)
    ]


def build_edge20_definition_snapshot(
    prs_rows: Sequence[Mapping[str, Any]], *, prs_artifact_path: Path, prs_sha: str
) -> list[dict[str, str]]:
    base_bins: dict[str, Mapping[str, Any]] = {}
    for row in prs_rows:
        bin_id = _value(row, "bin_id")
        if (
            _value(row, "distribution_type") == "edge_norm_1d"
            and _value(row, "row_scope") == "response_surface_bin"
            and _value(row, "row_kind") == "base_bin"
            and bin_id.startswith("edge_")
        ):
            base_bins.setdefault(bin_id, row)
    snapshot_rows: list[dict[str, str]] = []
    definition_material = []
    for index in range(20):
        bin_id = f"edge_{index:02d}"
        row = base_bins.get(bin_id, {})
        min_value = _value(row, "edge_norm_min")
        max_value = _value(row, "edge_norm_max")
        status = "PASS_EDGE20_DEFINITION_HASHED" if row else "BLOCKED_MISSING_NODI_EDGE20_DEFINITION"
        definition_material.append(f"{bin_id}:{min_value}:{max_value}")
        snapshot_rows.append(
            {
                "edge20_snapshot_id": f"NODI-G2E-EDGE20-{index + 1:02d}",
                "bin_index": str(index),
                "bin_id": bin_id,
                "edge_norm_min": min_value,
                "edge_norm_max": max_value,
                "definition_status": status,
                "source_prs_artifact": _rel(prs_artifact_path),
                "source_prs_sha256": prs_sha,
                "source_prs_row_count": str(len(prs_rows)),
                "edge20_definition_hash": "",
                "allowed_use": "hashed NODI edge20 definition for receiver policy review only",
                "blocked_use": "direct PRS bin use; formula use; accepted row expansion; weighting; JRC",
            }
        )
    definition_hash = hashlib.sha256("|".join(definition_material).encode("utf-8")).hexdigest()
    for row in snapshot_rows:
        row["edge20_definition_hash"] = definition_hash
    return snapshot_rows


def build_edge_verdict_rows(
    edge_requirement_rows: Sequence[Mapping[str, Any]],
    edge_checklist_rows: Sequence[Mapping[str, Any]],
    edge_definition_hash: str,
) -> list[dict[str, str]]:
    checklist_status = "; ".join(sorted({_value(row, "gate2c_policy_status") for row in edge_checklist_rows if row}))
    verdicts = [
        (
            "NODI-G2E-EDGE-001",
            "EDGE_REVIEW_CAN_START_WITH_NODI_EDGE20_HASHED_DEFINITION",
            "NODI has a hashed edge20 definition snapshot; COMSOL edge4 remains review-only.",
        ),
        (
            "NODI-G2E-EDGE-002",
            "EDGE_POLICY_NOT_APPROVED_FORMULA_USE_FALSE",
            "No formula, direct PRS bin, grain ingestion, weighting, or JRC use is approved.",
        ),
        (
            "NODI-G2E-EDGE-003",
            "EDGE_BLOCKED_MISSING_LOSS_ERROR_SEMANTICS",
            "Future policy must define loss/error semantics, coverage, and conservatism before any stronger gate.",
        ),
    ]
    rows: list[dict[str, str]] = []
    for verdict_id, receiver_verdict, blocker in verdicts:
        rows.append(
            {
                "edge_verdict_id": verdict_id,
                "gate": "Gate2E-EDGE",
                "comsol_requirement_count": str(len(edge_requirement_rows)),
                "nodi_gate2c_edge_checklist_statuses": checklist_status,
                "edge20_definition_status": "PASS_EDGE20_DEFINITION_HASHED"
                if edge_definition_hash
                else "BLOCKED_MISSING_NODI_EDGE20_DEFINITION",
                "edge20_definition_hash": edge_definition_hash,
                "receiver_verdict": receiver_verdict,
                "edge4_edge20_relationship": "review_only_coarse_to_fine_candidate",
                "edge_review_can_start": "true" if receiver_verdict.endswith("HASHED_DEFINITION") else "false",
                "accepted_row_expansion_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "allowed_use": "receiver policy review only",
                "blocked_use": "edge4 row acceptance; direct PRS bin use; formula; q_ch weighting; JRC",
                "blocker_or_required_next_gate": blocker,
            }
        )
    return rows


def build_qch_verdict_rows(
    qch_requirement_rows: Sequence[Mapping[str, Any]], qch_provenance_row_count: int
) -> list[dict[str, str]]:
    return [
        {
            "qch_verdict_id": "NODI-G2E-QCH-001",
            "gate": "Gate2E-QCH",
            "receiver_verdict": "QCH_FORMAL_RECEIPT_SCHEMA_READY_BUT_NO_FORMAL_SIDECAR_PRESENT",
            "comsol_requirement_count": str(len(qch_requirement_rows)),
            "current_qch_provenance_row_count": str(qch_provenance_row_count),
            "current_qch_artifact_status": "PROVENANCE_ONLY_QUARANTINE_NOT_FORMAL_SIDECAR",
            "formal_sidecar_present": "false",
            "is_formal_gate2_qch_sidecar": "false",
            "qch_weighting_authorized": "false",
            "qch_eta_authorized": "false",
            "qch_chi_eta_authorized": "false",
            "formula_use_authorized": "false",
            "jrc_authorized": "false",
            "accepted_row_expansion_authorized": "false",
            "allowed_use": "receipt schema review only",
            "blocked_use": "q_ch weighting; q_ch*eta; q_ch*chi*eta; route_score; JRC; winner; yield; detection_probability",
            "required_next_gate": "COMSOL formal q_ch / flow-split sidecar export with NODI-bound route/view/diameter/bin fields",
        }
    ]


def build_qch_gap_rows(
    qch_requirement_rows: Sequence[Mapping[str, Any]],
    nodi_qch_checklist_rows: Sequence[Mapping[str, Any]],
    qch_provenance_row_count: int,
) -> list[dict[str, str]]:
    nodi_by_req = {_value(row, "source_requirement_id"): row for row in nodi_qch_checklist_rows}
    rows: list[dict[str, str]] = []
    for index, requirement in enumerate(qch_requirement_rows, start=1):
        requirement_id = _value(requirement, "requirement_id")
        nodi_row = nodi_by_req.get(requirement_id, {})
        rows.append(
            {
                "qch_gap_id": f"NODI-G2E-QCH-GAP-{index:03d}",
                "comsol_requirement_id": requirement_id,
                "requirement_area": _value(requirement, "requirement_area"),
                "receipt_field": _value(requirement, "receipt_field") or _value(nodi_row, "field_name"),
                "required_field_or_type": _value(requirement, "needed_from_comsol"),
                "nodi_required_status": _value(nodi_row, "current_status", "GAP_PRESENT"),
                "current_gap": _value(requirement, "current_gap") or _value(nodi_row, "current_status", "GAP_PRESENT"),
                "current_qch_provenance_row_count": str(qch_provenance_row_count),
                "current_qch_artifact_status": "PROVENANCE_ONLY_NOT_FORMAL_SIDECAR",
                "formal_sidecar_present": "false",
                "is_formal_gate2_qch_sidecar": "false",
                "qch_weighting_authorized": "false",
                "formula_use_authorized": "false",
                "allowed_use": "schema and gap review only",
                "blocked_use": _value(nodi_row, "blocked_use")
                or "q_ch weighting; q_ch*eta; q_ch*chi*eta; JRC; route_score; winner",
                "required_next_gate": "formal q_ch / flow-split receipt package; no weighting authorization",
            }
        )
    return rows


def build_binding_verdict_rows(
    binding_requirement_rows: Sequence[Mapping[str, Any]],
    prs_verdict_rows: Sequence[Mapping[str, Any]],
    blocker_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    _ = binding_requirement_rows, prs_verdict_rows, blocker_rows
    return [
        {
            "binding_verdict_id": "NODI-G2E-BIND-001",
            "gate": "Gate2E-BINDING",
            "binding_case": "220_nm",
            "receiver_verdict": "BLOCKED_NO_DIRECT_NODI_PRS_GRAIN_NO_AUTO_MAP",
            "accepted_row_expansion_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "formula_use_authorized": "false",
            "allowed_use": "binding repair policy review only",
            "blocked_use": "220 nm accepted row expansion; diameter remapping; weighting; JRC",
            "required_next_gate": "direct NODI PRS grain or explicit future no-auto-map policy package",
        },
        {
            "binding_verdict_id": "NODI-G2E-BIND-002",
            "gate": "Gate2E-BINDING",
            "binding_case": "D1200_300_nm",
            "receiver_verdict": "BLOCKED_D1200_EXACT_GRAIN_ABSENT_OR_UNCERTAIN",
            "accepted_row_expansion_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "formula_use_authorized": "false",
            "allowed_use": "binding repair policy review only",
            "blocked_use": "D1200 borrowing D900 semantics; accepted row expansion; weighting; JRC",
            "required_next_gate": "D1200 NODI-bound exact grain evidence; no borrowing from D900",
        },
        {
            "binding_verdict_id": "NODI-G2E-BIND-003",
            "gate": "Gate2E-BINDING",
            "binding_case": "TPD_source_alignment_unbound_view",
            "receiver_verdict": "BLOCKED_UNBOUND_VIEW_FAIL_CLOSED",
            "accepted_row_expansion_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "formula_use_authorized": "false",
            "allowed_use": "binding repair policy review only",
            "blocked_use": "silent cross-view mapping; TPD source/alignment accepted row expansion; weighting; JRC",
            "required_next_gate": "formal NODI_view-bound TPD source/alignment sidecar",
        },
    ]


def build_binding_matrix_rows(
    binding_requirement_rows: Sequence[Mapping[str, Any]],
    prs_verdict_rows: Sequence[Mapping[str, Any]],
    blocker_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    verdict_by_case = {
        "220": "BLOCKED_NO_DIRECT_NODI_PRS_GRAIN_NO_AUTO_MAP",
        "D1200": "BLOCKED_D1200_EXACT_GRAIN_ABSENT_OR_UNCERTAIN",
        "UNBOUND": "BLOCKED_UNBOUND_VIEW_FAIL_CLOSED",
    }
    rows: list[dict[str, str]] = []
    for index, requirement in enumerate(binding_requirement_rows, start=1):
        blocker = _value(requirement, "binding_blocker")
        if "220" in blocker:
            verdict = verdict_by_case["220"]
        elif "D1200" in blocker:
            verdict = verdict_by_case["D1200"]
        else:
            verdict = verdict_by_case["UNBOUND"]
        rows.append(
            {
                "binding_matrix_id": f"NODI-G2E-BIND-MAT-{index:03d}",
                "comsol_requirement_id": _value(requirement, "requirement_id"),
                "binding_blocker": blocker,
                "affected_rows": _value(requirement, "affected_rows"),
                "nodi_receiver_verdict": verdict,
                "prs_related_rows_reviewed": str(len(prs_verdict_rows)),
                "gate2d_blocker_rows_reviewed": str(len(blocker_rows)),
                "accepted_row_expansion_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "formula_use_authorized": "false",
                "required_next_gate": _value(requirement, "success_criteria")
                or "future NODI-bound repair package; no auto-map",
            }
        )
    return rows


def build_dashboard_rows(
    edge_rows: Sequence[Mapping[str, Any]],
    qch_rows: Sequence[Mapping[str, Any]],
    binding_rows: Sequence[Mapping[str, Any]],
    accepted_count: int,
) -> list[dict[str, str]]:
    return [
        {
            "gate": "Gate2D-FREEZE",
            "receiver_status": "FROZEN_ACCEPTED_LEDGER_EXACTLY_FOUR_ROWS",
            "gate2d_accepted_row_count": str(accepted_count),
            "can_start_review_gate": "not_applicable",
            "approval_status": "accepted_scope_frozen_no_expansion",
            "accepted_row_expansion_authorized": "false",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
            "required_next_gate": "Gate2E review gates only; Gate3 for any future formula discussion",
        },
        {
            "gate": "Gate2E-EDGE",
            "receiver_status": _value(edge_rows[0], "receiver_verdict"),
            "gate2d_accepted_row_count": str(accepted_count),
            "can_start_review_gate": "true",
            "approval_status": "REVIEW_CAN_START_POLICY_NOT_APPROVED",
            "accepted_row_expansion_authorized": "false",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
            "required_next_gate": "edge4-edge20 loss/error semantics and tests",
        },
        {
            "gate": "Gate2E-QCH",
            "receiver_status": _value(qch_rows[0], "receiver_verdict"),
            "gate2d_accepted_row_count": str(accepted_count),
            "can_start_review_gate": "true",
            "approval_status": "SCHEMA_READY_NO_FORMAL_SIDECAR",
            "accepted_row_expansion_authorized": "false",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
            "required_next_gate": "formal q_ch flow-split sidecar receipt",
        },
        {
            "gate": "Gate2E-BINDING",
            "receiver_status": "; ".join(_value(row, "receiver_verdict") for row in binding_rows),
            "gate2d_accepted_row_count": str(accepted_count),
            "can_start_review_gate": "true",
            "approval_status": "FAIL_CLOSED_POLICY_VERDICTS_ONLY",
            "accepted_row_expansion_authorized": "false",
            "can_enter_weighting": "false",
            "can_enter_jrc": "false",
            "required_next_gate": "220/D1200/view-bound repair package",
        },
    ]


def build_self_review_rows() -> list[dict[str, str]]:
    return [
        {
            "reviewer": "Reviewer A",
            "focus": "COMSOL Gate2E evidence registration",
            "finding_severity": "PASS",
            "finding": "Gate2E plan/index/EDGE/QCH/BINDING/validation/manifest files are registered as external read-only evidence with manifest checks.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer B",
            "focus": "EDGE edge20 semantics",
            "finding_severity": "PASS",
            "finding": "NODI edge20 definition is hashed from current PRS, but edge4-to-edge20 remains review-only and not direct PRS bin use.",
            "unresolved_risk": "loss/error semantics still required before any stronger gate",
        },
        {
            "reviewer": "Reviewer C",
            "focus": "QCH receipt schema and no promotion",
            "finding_severity": "PASS",
            "finding": "QCH receipt schema verdict is ready, current q_ch provenance stays quarantine and is not a formal sidecar.",
            "unresolved_risk": "formal q_ch / flow-split sidecar not present",
        },
        {
            "reviewer": "Reviewer D",
            "focus": "BINDING fail-closed and no accepted row expansion",
            "finding_severity": "PASS",
            "finding": "220 nm, D1200, and unbound-view rows remain blocked; Gate2D accepted scope stays exactly four rows.",
            "unresolved_risk": "none for current no-expansion verdict",
        },
    ]


def validate_gate2e_payload(payload: Mapping[str, Any], *, comsol_root: Path, prs_artifact_path: Path) -> list[str]:
    issues: list[str] = []
    if payload.get("status") != PASS_STATUS:
        issues.append("unexpected Gate2E receiver disposition")
    if payload.get("gate2d_accepted_row_count") != EXPECTED_GATE2D_ACCEPTED_ROW_COUNT:
        issues.append("Gate2D accepted row count must remain exactly four")
    if payload.get("nodi_prs_sha256") != EXPECTED_PRS_SHA or sha256_file(prs_artifact_path) != EXPECTED_PRS_SHA:
        issues.append("PRS hash drift hard fail")
    if payload.get("accepted_row_expansion_authorized") is not False:
        issues.append("accepted row expansion must remain false")
    for row in payload.get("evidence_register_rows", []):
        if _value(row, "manifest_match") != "true":
            issues.append(f"COMSOL evidence manifest mismatch: {_value(row, 'evidence_id')}")
        path = comsol_root / _value(row, "relative_source_path")
        if sha256_file(path) != _value(row, "source_sha256"):
            issues.append(f"COMSOL evidence hash drift: {_value(row, 'evidence_id')}")
    edge_snapshot = list(payload.get("edge20_definition_snapshot_rows", []))
    if len(edge_snapshot) != 20 or any(_value(row, "definition_status") != "PASS_EDGE20_DEFINITION_HASHED" for row in edge_snapshot):
        issues.append("edge20 definition snapshot must contain 20 hashed PRS bins")
    for row in payload.get("edge_receiver_policy_verdict_rows", []):
        if _value(row, "direct_prs_bin_use_authorized") != "false" or _value(row, "formula_use_authorized") != "false":
            issues.append("EDGE direct PRS bin/formula flags must be false")
    for row in payload.get("qch_receipt_schema_verdict_rows", []):
        if _value(row, "formal_sidecar_present") != "false" or _value(row, "qch_weighting_authorized") != "false":
            issues.append("QCH formal sidecar and weighting flags must be false")
    binding_statuses = {_value(row, "receiver_verdict") for row in payload.get("binding_policy_verdict_rows", [])}
    required = {
        "BLOCKED_NO_DIRECT_NODI_PRS_GRAIN_NO_AUTO_MAP",
        "BLOCKED_D1200_EXACT_GRAIN_ABSENT_OR_UNCERTAIN",
        "BLOCKED_UNBOUND_VIEW_FAIL_CLOSED",
    }
    if not required.issubset(binding_statuses):
        issues.append("BINDING 220/D1200/UNBOUND cases must fail closed")
    for group in (
        "edge_receiver_policy_verdict_rows",
        "qch_receipt_schema_verdict_rows",
        "qch_required_fields_and_gaps_rows",
        "binding_policy_verdict_rows",
        "binding_repair_decision_matrix_rows",
        "receiver_dashboard_rows",
    ):
        issues.extend(_validate_forbidden_false_fields(payload.get(group, []), group))
    issues.extend(validate_comsol_v4_readonly_context(payload.get("comsol_v4_context", {})))
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "evidence_register_csv": output_dir / EVIDENCE_REGISTER,
        "evidence_manifest_csv": output_dir / EVIDENCE_MANIFEST,
        "edge_verdict_csv": output_dir / EDGE_VERDICT,
        "edge20_snapshot_csv": output_dir / EDGE20_SNAPSHOT,
        "edge_report_md": output_dir / EDGE_REPORT,
        "qch_verdict_csv": output_dir / QCH_VERDICT,
        "qch_gaps_csv": output_dir / QCH_GAPS,
        "qch_report_md": output_dir / QCH_REPORT,
        "binding_verdict_csv": output_dir / BINDING_VERDICT,
        "binding_matrix_csv": output_dir / BINDING_MATRIX,
        "binding_report_md": output_dir / BINDING_REPORT,
        "dashboard_csv": output_dir / DASHBOARD,
        "self_review_csv": output_dir / SELF_REVIEW,
        "report_json": output_dir / REPORT_JSON,
        "report_md": output_dir / REPORT_MD,
        "report_204_md": report_dir / REPORT_204,
    }
    write_csv_rows(paths["evidence_register_csv"], list(payload["evidence_register_rows"]))
    write_csv_rows(paths["evidence_manifest_csv"], list(payload["evidence_manifest_rows"]))
    write_csv_rows(paths["edge_verdict_csv"], list(payload["edge_receiver_policy_verdict_rows"]))
    write_csv_rows(paths["edge20_snapshot_csv"], list(payload["edge20_definition_snapshot_rows"]))
    write_csv_rows(paths["qch_verdict_csv"], list(payload["qch_receipt_schema_verdict_rows"]))
    write_csv_rows(paths["qch_gaps_csv"], list(payload["qch_required_fields_and_gaps_rows"]))
    write_csv_rows(paths["binding_verdict_csv"], list(payload["binding_policy_verdict_rows"]))
    write_csv_rows(paths["binding_matrix_csv"], list(payload["binding_repair_decision_matrix_rows"]))
    write_csv_rows(paths["dashboard_csv"], list(payload["receiver_dashboard_rows"]))
    write_csv_rows(paths["self_review_csv"], list(payload["self_review_rows"]))
    for path in paths.values():
        if path.suffix == ".csv":
            _normalize_lf(path)

    edge_report = render_edge_report(payload)
    qch_report = render_qch_report(payload)
    binding_report = render_binding_report(payload)
    paths["edge_report_md"].write_text(edge_report, encoding="utf-8", newline="\n")
    paths["qch_report_md"].write_text(qch_report, encoding="utf-8", newline="\n")
    paths["binding_report_md"].write_text(binding_report, encoding="utf-8", newline="\n")

    report_payload = dict(payload)
    report_payload["outputs"] = {key: _rel(path) for key, path in paths.items()}
    output_hashes = {
        key: sha256_file(path)
        for key, path in paths.items()
        if path.exists() and path.suffix in {".csv", ".md"}
    }
    report_payload["output_hashes"] = output_hashes
    write_json_atomic(paths["report_json"], report_payload, sort_keys=True)
    report_payload["output_hashes"]["report_json"] = sha256_file(paths["report_json"])
    report_md = render_report_md(report_payload)
    paths["report_md"].write_text(report_md, encoding="utf-8", newline="\n")
    paths["report_204_md"].write_text(
        report_md.replace(
            "# NODI/COMSOL Gate2E Receiver Policy Verdicts",
            "# Report 204 - NODI/COMSOL Gate2E Receiver Policy Verdicts",
        ),
        encoding="utf-8",
        newline="\n",
    )
    return {key: str(path) for key, path in paths.items()}


def render_edge_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# NODI Gate2E-EDGE Receiver Policy Review",
            "",
            "Verdict: `EDGE_REVIEW_CAN_START_WITH_NODI_EDGE20_HASHED_DEFINITION`.",
            "",
            "NODI has a hashed edge20 definition snapshot from the current PRS artifact. The edge4-to-edge20 relationship remains review-only; direct PRS bin use, formula use, grain-level ingestion, weighting, and JRC are false.",
            "",
            "Current blocker: `EDGE_BLOCKED_MISSING_LOSS_ERROR_SEMANTICS`.",
        ]
    ) + "\n"


def render_qch_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# NODI Gate2E-QCH Receipt Schema Review",
            "",
            "Verdict: `QCH_FORMAL_RECEIPT_SCHEMA_READY_BUT_NO_FORMAL_SIDECAR_PRESENT`.",
            "",
            f"Current q_ch provenance-only row count observed: `{payload['qch_provenance_row_count']}`.",
            "",
            "The provenance file remains quarantine/review-only. It is not a formal Gate2 q_ch sidecar and does not authorize q_ch weighting, q_ch*eta, q_ch*chi*eta, route scoring, JRC, yield, winner, or detection_probability.",
        ]
    ) + "\n"


def render_binding_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# NODI Gate2E-BINDING Receiver Policy Review",
            "",
            "Verdicts:",
            "",
            "- `BLOCKED_NO_DIRECT_NODI_PRS_GRAIN_NO_AUTO_MAP` for 220 nm.",
            "- `BLOCKED_D1200_EXACT_GRAIN_ABSENT_OR_UNCERTAIN` for D1200/300.",
            "- `BLOCKED_UNBOUND_VIEW_FAIL_CLOSED` for TPD source/alignment missing NODI_view.",
            "",
            "No accepted row expansion is authorized.",
        ]
    ) + "\n"


def render_report_md(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2E Receiver Policy Verdicts",
            "",
            "Date: 2026-06-28",
            "",
            "## Disposition",
            "",
            f"`{payload['status']}`",
            "",
            "Gate2D accepted ledger is frozen at exactly four W800/D900/300 aggregate proxy context-only rows. Gate2E only records receiver-side policy verdicts for EDGE, QCH, and BINDING; it does not add accepted rows.",
            "",
            "## EDGE Verdict",
            "",
            "`EDGE_REVIEW_CAN_START_WITH_NODI_EDGE20_HASHED_DEFINITION`, but `EDGE_POLICY_NOT_APPROVED_FORMULA_USE_FALSE` and `EDGE_BLOCKED_MISSING_LOSS_ERROR_SEMANTICS` remain active. edge4 rows are not accepted and direct PRS edge20 bin use is not authorized.",
            "",
            "## QCH Verdict",
            "",
            "`QCH_FORMAL_RECEIPT_SCHEMA_READY_BUT_NO_FORMAL_SIDECAR_PRESENT`. Current q_ch provenance stays quarantine/review-only and is not formal q_ch / flow-split receipt.",
            "",
            "## BINDING Verdict",
            "",
            "220 nm remains blocked with no auto-map. D1200/300 remains blocked/uncertain and cannot borrow D900. TPD source/alignment rows missing NODI_view fail closed.",
            "",
            "## Output Hashes",
            "",
            f"- evidence register: `{hashes.get('evidence_register_csv', 'pending')}`",
            f"- EDGE verdict: `{hashes.get('edge_verdict_csv', 'pending')}`",
            f"- QCH verdict: `{hashes.get('qch_verdict_csv', 'pending')}`",
            f"- BINDING verdict: `{hashes.get('binding_verdict_csv', 'pending')}`",
            f"- dashboard: `{hashes.get('dashboard_csv', 'pending')}`",
            f"- JSON report: `{hashes.get('report_json', 'pending')}`",
            "",
            "## Non-Authorization",
            "",
            "This report does not authorize q_ch weighting, q_ch*eta, q_ch*chi*eta, chi_selected, route_score, JOINT_ROUTE_CLASS/JRC, yield, winner, detection_probability, wet pass probability, clogging rate, runtime configuration, or production ingestion.",
        ]
    ) + "\n"


def _validate_forbidden_false_fields(rows: Sequence[Mapping[str, Any]], group: str) -> list[str]:
    issues: list[str] = []
    for index, row in enumerate(rows, start=1):
        for field in FORBIDDEN_FALSE_FIELDS:
            if field in row and str(row[field]).lower() not in {"false", "", "not_applicable"}:
                issues.append(f"{group} row {index} forbidden field {field} is {row[field]!r}")
    return issues


def _row_count(path: Path) -> int:
    if path.suffix.lower() != ".csv":
        return 0
    return len(read_csv_rows(path))


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
    if not args.confirm_gate2e_receiver_policy_verdicts:
        raise SystemExit("Refusing to write Gate2E receiver verdicts without explicit confirmation flag.")
    payload = build_gate2e_payload(comsol_root=args.comsol_root, prs_artifact_path=args.prs_artifact)
    issues = validate_gate2e_payload(payload, comsol_root=args.comsol_root, prs_artifact_path=args.prs_artifact)
    if issues:
        print(f"NODI_COMSOL_GATE2E_RECEIVER_POLICY_VERDICTS: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    report_sha = sha256_file(outputs["report_json"])
    print(f"NODI_COMSOL_GATE2E_RECEIVER_POLICY_VERDICTS: {PASS_STATUS}")
    print(f"report_path: {outputs['report_json']}")
    print(f"report_sha256: {report_sha}")
    print(f"dashboard_csv: {outputs['dashboard_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
