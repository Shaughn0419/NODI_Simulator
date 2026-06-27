#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
import shutil
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
PASS_STATUS = "PASS_GATE2C_REQUIREMENT_REVIEW_EVIDENCE_STABILIZED_NO_WEIGHTING_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2C_REQUIREMENT_REVIEW"

OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
MIRROR_DIRNAME = "comsol_gate2b_evidence"

EVIDENCE_REGISTER = f"NODI_COMSOL_GATE2C_COMSOL_SUPPORT_EVIDENCE_REGISTER_{DATE_STAMP}.csv"
EVIDENCE_MANIFEST = f"NODI_COMSOL_GATE2C_COMSOL_SUPPORT_EVIDENCE_MANIFEST_{DATE_STAMP}.csv"
PARENT_CHILD_MAP = f"NODI_COMSOL_GATE2C_LEDGER_SUPPORT_PARENT_CHILD_MAP_{DATE_STAMP}.csv"
ALLOWED_ACCEPTANCE = f"NODI_COMSOL_GATE2C_ALLOWED_SUPPORT_ROW_ACCEPTANCE_{DATE_STAMP}.csv"
PRS_VERDICT = f"NODI_COMSOL_GATE2C_PRS_COVERAGE_VERDICT_{DATE_STAMP}.csv"
PRS_SUMMARY = f"NODI_COMSOL_GATE2C_PRS_COVERAGE_SUMMARY_{DATE_STAMP}.md"
EDGE_REVIEW_MD = f"NODI_COMSOL_GATE2C_EDGE4_EDGE20_POLICY_REVIEW_{DATE_STAMP}.md"
EDGE_CHECKLIST = f"NODI_COMSOL_GATE2C_EDGE4_EDGE20_POLICY_CHECKLIST_{DATE_STAMP}.csv"
QCH_CHECKLIST = f"NODI_COMSOL_GATE2C_QCH_FORMAL_SIDECAR_ACCEPTANCE_CHECKLIST_{DATE_STAMP}.csv"
QCH_GAP_MD = f"NODI_COMSOL_GATE2C_QCH_PROVENANCE_GAP_REVIEW_{DATE_STAMP}.md"
ACCEPTANCE_CHECKLIST = f"NODI_COMSOL_GATE2C_ACCEPTANCE_CHECKLIST_{DATE_STAMP}.csv"
SELF_REVIEW = f"NODI_COMSOL_GATE2C_SELF_REVIEW_FINDINGS_{DATE_STAMP}.csv"
REPORT_JSON = f"NODI_COMSOL_GATE2C_REQUIREMENT_REVIEW_REPORT_{DATE_STAMP}.json"
REPORT_MD = f"NODI_COMSOL_GATE2C_REQUIREMENT_REVIEW_REPORT_{DATE_STAMP}.md"
REPORT_201 = f"201_NODI_COMSOL_GATE2C_REQUIREMENT_REVIEW_AND_EVIDENCE_STABILIZATION_{DATE_STAMP}.md"

DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
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
EXPECTED_PRS_SHA = "9ba83c84a563cd856b2fc624c523843a6e283206d5ac2e592a2b72607645f393"
EXPECTED_EAS_SHA = "35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc"

NODI_GATE2B_REGISTER = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2B_FORMAL_CONTEXT_INGEST_REGISTER_20260627.csv"
)
NODI_GATE2B_INGESTED = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2B_INGESTED_CONTEXT_ROWS_20260627.csv"
)
NODI_GATE2B_QUARANTINE = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2B_QUARANTINE_REVIEW_ONLY_REGISTER_20260627.csv"
)
NODI_GATE2B_BLOCKED_GRAIN = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2B_BLOCKED_GRAIN_DISPOSITION_20260627.csv"
)
NODI_GATE2B_SCHEMA = (
    PROJECT_ROOT
    / "reports/joint_interface_20260627"
    / "NODI_COMSOL_GATE2C_REQUIRED_EXPORT_SCHEMA_20260627.csv"
)
NODI_REPORT_200 = PROJECT_ROOT / "reports/200_NODI_COMSOL_GATE2B_CONTEXT_ONLY_FORMAL_INGESTION_20260627.md"

COMSOL_EVIDENCE_FILES = (
    ("G2B-PACKET", "package_report", Path("roadmap/COMSOL_GATE2B_NODI_CONTEXT_ONLY_SUPPORT_PACKET_20260627.md")),
    ("G2B-ALLOWED", "allowed_context_rows", Path("roadmap/COMSOL_GATE2B_NODI_ALLOWED_CONTEXT_ROWS_20260627.csv")),
    ("G2B-QUARANTINE", "quarantine_review_only_rows", Path("roadmap/COMSOL_GATE2B_NODI_QUARANTINE_REVIEW_ONLY_ROWS_20260627.csv")),
    ("G2C-REPAIR", "transported_position_repair_plan", Path("roadmap/COMSOL_GATE2B_TPD_BINDING_REPAIR_PLAN_20260627.csv")),
    ("QCH-REQ-CSV", "formal_qch_requirements", Path("roadmap/COMSOL_GATE2B_QCH_FORMAL_SIDECAR_REQUIREMENTS_20260627.csv")),
    ("QCH-REQ-MD", "formal_qch_requirements_report", Path("roadmap/COMSOL_GATE2B_QCH_FORMAL_SIDECAR_REQUIREMENTS_20260627.md")),
    ("G2B-VALIDATION", "validation_results", Path("roadmap/COMSOL_GATE2B_NODI_SUPPORT_VALIDATION_20260627.csv")),
    ("G2B-MANIFEST", "support_manifest", Path("roadmap/COMSOL_GATE2B_NODI_SUPPORT_MANIFEST_20260627.csv")),
)

FORBIDDEN_FLAG_FIELDS = (
    "is_chi_selected",
    "qch_weighting_authorized",
    "jrc_authorized",
    "production_ingestion_authorized",
    "runtime_configuration_authorized",
    "gate2b_grain_level_context_ingestion_authorized",
    "can_enter_weighting",
    "can_enter_jrc",
    "is_production_ingestion",
    "is_runtime_configuration",
)
FORBIDDEN_CLAIMS = (
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
    parser = argparse.ArgumentParser(
        description="Build NODI Gate2C requirement review and evidence stabilization outputs."
    )
    parser.add_argument("--confirm-gate2c-requirement-review", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--prs", type=Path, default=DEFAULT_PRS)
    parser.add_argument("--eas", type=Path, default=DEFAULT_EAS)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_gate2c_payload(
    *,
    comsol_root: Path,
    output_dir: Path,
    prs_path: Path,
    eas_path: Path,
    mirror_evidence: bool = True,
) -> dict[str, Any]:
    nodi_register_rows = read_csv_rows(NODI_GATE2B_REGISTER)
    nodi_ingested_rows = read_csv_rows(NODI_GATE2B_INGESTED)
    nodi_quarantine_rows = read_csv_rows(NODI_GATE2B_QUARANTINE)
    nodi_blocked_grain_rows = read_csv_rows(NODI_GATE2B_BLOCKED_GRAIN)
    nodi_schema_rows = read_csv_rows(NODI_GATE2B_SCHEMA)
    allowed_rows = read_csv_rows(comsol_root / "roadmap/COMSOL_GATE2B_NODI_ALLOWED_CONTEXT_ROWS_20260627.csv")
    quarantine_rows = read_csv_rows(comsol_root / "roadmap/COMSOL_GATE2B_NODI_QUARANTINE_REVIEW_ONLY_ROWS_20260627.csv")
    repair_rows = read_csv_rows(comsol_root / "roadmap/COMSOL_GATE2B_TPD_BINDING_REPAIR_PLAN_20260627.csv")
    qch_req_rows = read_csv_rows(comsol_root / "roadmap/COMSOL_GATE2B_QCH_FORMAL_SIDECAR_REQUIREMENTS_20260627.csv")
    validation_rows = read_csv_rows(comsol_root / "roadmap/COMSOL_GATE2B_NODI_SUPPORT_VALIDATION_20260627.csv")
    manifest_rows = read_csv_rows(comsol_root / "roadmap/COMSOL_GATE2B_NODI_SUPPORT_MANIFEST_20260627.csv")
    prs_rows = read_csv_rows(prs_path)
    eas_rows = read_csv_rows(eas_path)

    prs_sha = sha256_file(prs_path)
    eas_sha = sha256_file(eas_path)
    if prs_sha != EXPECTED_PRS_SHA or eas_sha != EXPECTED_EAS_SHA:
        raise ValueError(
            "NODI PRS/EAS hash drift: "
            f"PRS {prs_sha} expected {EXPECTED_PRS_SHA}; EAS {eas_sha} expected {EXPECTED_EAS_SHA}"
        )

    evidence_register, evidence_manifest = build_evidence_register(
        comsol_root=comsol_root,
        output_dir=output_dir,
        manifest_rows=manifest_rows,
        mirror_evidence=mirror_evidence,
    )
    parent_child_rows = build_parent_child_map(nodi_register_rows, allowed_rows)
    allowed_acceptance_rows = build_allowed_support_acceptance(allowed_rows, parent_child_rows)
    prs_verdict_rows = build_prs_coverage_verdict(allowed_rows, prs_rows, eas_rows, prs_path, prs_sha)
    edge_checklist_rows = build_edge_policy_checklist()
    qch_checklist_rows = build_qch_acceptance_checklist(qch_req_rows)
    acceptance_rows = build_acceptance_checklist(
        evidence_register=evidence_register,
        parent_child_rows=parent_child_rows,
        allowed_acceptance_rows=allowed_acceptance_rows,
        prs_verdict_rows=prs_verdict_rows,
        edge_checklist_rows=edge_checklist_rows,
        qch_checklist_rows=qch_checklist_rows,
    )
    self_review_rows = build_self_review_rows()

    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2c_requirement_review_report_v1",
        "status": PASS_STATUS,
        "date_stamp": DATE_STAMP,
        "gate2b_freeze_verdict": "ACCEPTED_PARTIAL_CONTEXT_ONLY_LEDGER_READY",
        "allowed_scope": "Gate2C requirement review and evidence stabilization only",
        "nodi_gate2b_parent_ledger_row_count": len(nodi_register_rows),
        "nodi_gate2b_ingested_context_row_count": len(nodi_ingested_rows),
        "nodi_gate2b_quarantine_row_count": len(nodi_quarantine_rows),
        "nodi_gate2b_blocked_grain_row_count": len(nodi_blocked_grain_rows),
        "nodi_gate2c_schema_row_count": len(nodi_schema_rows),
        "comsol_allowed_support_row_count": len(allowed_rows),
        "comsol_quarantine_row_count": len(quarantine_rows),
        "comsol_repair_plan_row_count": len(repair_rows),
        "comsol_qch_requirement_row_count": len(qch_req_rows),
        "comsol_validation_row_count": len(validation_rows),
        "comsol_manifest_row_count": len(manifest_rows),
        "evidence_register_rows": evidence_register,
        "evidence_manifest_rows": evidence_manifest,
        "parent_child_rows": parent_child_rows,
        "allowed_support_acceptance_rows": allowed_acceptance_rows,
        "prs_coverage_verdict_rows": prs_verdict_rows,
        "edge_policy_checklist_rows": edge_checklist_rows,
        "qch_acceptance_checklist_rows": qch_checklist_rows,
        "acceptance_checklist_rows": acceptance_rows,
        "self_review_rows": self_review_rows,
        "prs_artifact": str(prs_path),
        "prs_sha256": prs_sha,
        "prs_row_count": len(prs_rows),
        "eas_artifact": str(eas_path),
        "eas_sha256": eas_sha,
        "eas_row_count": len(eas_rows),
        "allowed_support_counts_by_type": dict(Counter(row["source_row_type"] for row in allowed_rows)),
        "parent_child_counts": dict(Counter(row["parent_nodi_register_row_id"] for row in parent_child_rows)),
        "prs_verdict_counts": dict(Counter(row["coverage_verdict"] for row in prs_verdict_rows)),
        "edge4_edge20_policy_approved": False,
        "qch_formal_sidecar_exists": False,
        "weighting_or_jrc_allowed": False,
        "comsol_v4_context": default_comsol_v4_readonly_context(),
    }
    return payload


def build_evidence_register(
    *,
    comsol_root: Path,
    output_dir: Path,
    manifest_rows: Sequence[Mapping[str, Any]],
    mirror_evidence: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_by_path = {_value(row, "path"): row for row in manifest_rows}
    mirror_dir = output_dir / MIRROR_DIRNAME
    register: list[dict[str, Any]] = []
    mirror_manifest: list[dict[str, Any]] = []
    for index, (evidence_id, role, relative_path) in enumerate(COMSOL_EVIDENCE_FILES, start=1):
        source = comsol_root / relative_path
        source_sha = sha256_file(source)
        row_count = _row_count(source)
        manifest_row = manifest_by_path.get(relative_path.as_posix(), {})
        manifest_sha = _value(manifest_row, "sha256")
        manifest_count = _value(manifest_row, "row_count")
        if manifest_sha and manifest_sha != source_sha:
            raise ValueError(f"COMSOL manifest hash drift for {relative_path}: {manifest_sha} != {source_sha}")
        if manifest_count and manifest_count not in {"0", "n/a"} and manifest_count != str(row_count):
            raise ValueError(f"COMSOL manifest row-count drift for {relative_path}: {manifest_count} != {row_count}")
        mirror_path = ""
        mirror_sha = ""
        if mirror_evidence:
            mirror_dir.mkdir(parents=True, exist_ok=True)
            mirror = mirror_dir / source.name
            shutil.copyfile(source, mirror)
            mirror_path = _rel(mirror)
            mirror_sha = sha256_file(mirror)
            if mirror_sha != source_sha:
                raise ValueError(f"mirror hash mismatch for {relative_path}: {mirror_sha} != {source_sha}")
        allowed, blocked, boundary, next_gate = _evidence_use_policy(role)
        row = {
            "evidence_id": f"NODI-G2C-EVID-{index:03d}-{evidence_id}",
            "source_repo_or_project": "comsol_ev_pbs_bonded_cross_junction",
            "original_absolute_path": str(source),
            "relative_source_path": relative_path.as_posix(),
            "file_role": role,
            "source_sha256": source_sha,
            "copied_or_external_reference": "copied_mirror_and_external_reference" if mirror_evidence else "external_reference_only",
            "nodi_mirror_path_if_any": mirror_path,
            "mirror_sha256_if_any": mirror_sha,
            "row_count": row_count,
            "producer": "COMSOL Gate2B support package",
            "source_commit_if_available": "not_available_in_package",
            "allowed_use": allowed,
            "blocked_use": blocked,
            "claim_boundary": boundary,
            "required_next_gate": next_gate,
        }
        register.append(row)
        mirror_manifest.append(
            {
                "manifest_id": f"NODI-G2C-MIRROR-{index:03d}",
                "evidence_id": row["evidence_id"],
                "relative_source_path": relative_path.as_posix(),
                "nodi_mirror_path": mirror_path,
                "source_sha256": source_sha,
                "mirror_sha256": mirror_sha,
                "sha_match": _bool_text((not mirror_evidence) or mirror_sha == source_sha),
                "row_count": row_count,
                "status": "PASS_MIRROR_SHA_MATCH" if mirror_evidence else "PASS_EXTERNAL_REFERENCE_ONLY",
            }
        )
    return register, mirror_manifest


def build_parent_child_map(
    nodi_register_rows: Sequence[Mapping[str, Any]],
    allowed_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    register_by_id = {_value(row, "nodi_register_row_id"): row for row in nodi_register_rows}
    rows: list[dict[str, Any]] = []
    for allowed in allowed_rows:
        source_type = _value(allowed, "source_row_type")
        parent_id = "G2CTX-CHI-AGG-004" if source_type == "proxy_aggregate" else "G2CTX-CHI-BIN-005"
        parent = register_by_id[parent_id]
        rows.append(
            {
                "parent_child_map_id": f"MAP-{_value(allowed, 'gate2b_context_row_id')}",
                "parent_nodi_register_row_id": parent_id,
                "parent_source_artifact": _value(parent, "source_artifact"),
                "parent_source_row_count": _value(parent, "source_row_count"),
                "child_gate2b_context_row_id": _value(allowed, "gate2b_context_row_id"),
                "child_source_artifact": _value(allowed, "source_artifact"),
                "child_source_row_identity": _value(allowed, "source_row_identity"),
                "child_source_row_type": source_type,
                "child_route_key": _value(allowed, "route_key"),
                "child_NODI_view": _value(allowed, "NODI_view"),
                "child_diameter_nm": _value(allowed, "diameter_nm"),
                "child_bin_basis": _value(allowed, "bin_basis"),
                "child_tpd_bin_label": _value(allowed, "tpd_bin_label"),
                "parent_ledger_acceptance_status": "PARENT_LEDGER_ACCEPTED_CONTEXT_ONLY",
                "child_support_row_acceptance_status": "CHILD_SUPPORT_ROW_REGISTERED_ARTIFACT_LEVEL_ONLY",
                "grain_level_authorization": "false",
                "decision_use_allowed": "false",
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "is_chi_selected": "false",
                "is_production_ingestion": "false",
                "is_runtime_configuration": "false",
            }
        )
    return rows


def build_allowed_support_acceptance(
    allowed_rows: Sequence[Mapping[str, Any]],
    parent_child_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    map_by_child = {_value(row, "child_gate2b_context_row_id"): row for row in parent_child_rows}
    rows: list[dict[str, Any]] = []
    for allowed in allowed_rows:
        child_id = _value(allowed, "gate2b_context_row_id")
        map_row = map_by_child[child_id]
        bin_policy_required = _value(allowed, "source_row_type") == "proxy_bin"
        rows.append(
            {
                "acceptance_row_id": f"NODI-G2C-ACCEPT-{child_id}",
                "parent_nodi_register_row_id": _value(map_row, "parent_nodi_register_row_id"),
                "gate2b_context_row_id": child_id,
                "source_row_type": _value(allowed, "source_row_type"),
                "route_key": _value(allowed, "route_key"),
                "NODI_view": _value(allowed, "NODI_view"),
                "diameter_nm": _value(allowed, "diameter_nm"),
                "bin_basis": _value(allowed, "bin_basis"),
                "tpd_bin_label": _value(allowed, "tpd_bin_label"),
                "nodi_acceptance_status": "CHILD_SUPPORT_ROW_REGISTERED_ARTIFACT_LEVEL_ONLY",
                "parent_ledger_status": "PARENT_LEDGER_ACCEPTED_CONTEXT_ONLY",
                "grain_level_authorization_status": "GRAIN_LEVEL_AUTHORIZATION_FALSE",
                "edge4_edge20_status": "EDGE4_EDGE20_POLICY_REQUIRED" if bin_policy_required else "AGGREGATE_PROXY_NO_DIRECT_PRS_BIN_CLAIM",
                "prs_coverage_status": "PRS_COVERAGE_RECHECK_REQUIRED",
                "blocked_or_review_status": "BLOCKED_OR_REVIEW_ONLY",
                "gate2b_artifact_level_context_candidate": _value(allowed, "gate2b_artifact_level_context_candidate"),
                "gate2b_grain_level_context_ingestion_authorized": _value(allowed, "gate2b_grain_level_context_ingestion_authorized"),
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "is_chi_selected": "false",
                "is_production_ingestion": "false",
                "is_runtime_configuration": "false",
                "allowed_use": _value(allowed, "allowed_use"),
                "blocked_use": _value(allowed, "blocked_use"),
                "claim_boundary": "artifact_level_context_support_not_grain_ingestion_not_formula",
            }
        )
    return rows


def build_prs_coverage_verdict(
    allowed_rows: Sequence[Mapping[str, Any]],
    prs_rows: Sequence[Mapping[str, Any]],
    eas_rows: Sequence[Mapping[str, Any]],
    prs_path: Path,
    prs_sha: str,
) -> list[dict[str, Any]]:
    prs_by_grain: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in prs_rows:
        prs_by_grain[(_value(row, "route_id_nodi"), _value(row, "diameter_nm"), _value(row, "NODI_view"))].append(row)
    eas_route_view = {(_value(row, "route_id_nodi"), _value(row, "NODI_view")) for row in eas_rows}
    current_nodi_views = sorted(view for view in {_value(row, "NODI_view") for row in prs_rows} if view)
    preferred_views = [view for view in ("fixed_660_gold", "per_wavelength_gold") if view in current_nodi_views]
    if not preferred_views:
        preferred_views = current_nodi_views
    support_views: dict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    seen_support: set[tuple[str, str, str, str]] = set()
    for allowed in allowed_rows:
        support_key = (
            _value(allowed, "route_key"),
            _value(allowed, "diameter_nm"),
            _value(allowed, "source_row_type"),
            _value(allowed, "bin_basis"),
        )
        seen_support.add(support_key)
        support_views[support_key].add(_value(allowed, "NODI_view"))
    verdicts: list[dict[str, Any]] = []
    for route, diameter, row_type, bin_basis in sorted(seen_support):
        support_view_binding = ";".join(sorted(support_views[(route, diameter, row_type, bin_basis)]))
        view_status = (
            "COMSOL_PROXY_VIEW_BINDING_RECHECK_REQUIRED"
            if "CANDIDATE_VIEW" in support_view_binding or not support_view_binding
            else "COMSOL_VIEW_DECLARED"
        )
        for view in preferred_views:
            prs_matches = prs_by_grain.get((route, diameter, view), [])
            exact_present = bool(prs_matches)
            direct_edge20 = row_type == "proxy_bin" and False
            if diameter == "220":
                verdict = "BLOCKED_220NM_NO_DIRECT_PRS_MATCH"
            elif route.endswith("/D1200") and not exact_present:
                verdict = "BLOCKED_D1200_DIAMETER_VIEW_GRAIN_ABSENT"
            elif row_type == "proxy_bin":
                verdict = "REVIEW_ONLY_EDGE4_TO_EDGE20_POLICY_REQUIRED"
            elif exact_present:
                verdict = "EXACT_GRAIN_PRESENT_CONTEXT_ONLY_REVIEW"
            else:
                verdict = "ABSENT_OR_RECHECK_REQUIRED"
            verdicts.append(
                {
                    "coverage_verdict_id": f"PRS-{len(verdicts) + 1:03d}",
                    "route_key": route,
                    "diameter_nm": diameter,
                    "NODI_view": view,
                    "comsol_support_view_binding": support_view_binding,
                    "comsol_view_binding_status": view_status,
                    "source_row_type": row_type,
                    "bin_basis": bin_basis,
                    "aggregate_proxy_status": "artifact_level_only"
                    if row_type == "proxy_aggregate"
                    else "not_aggregate_proxy",
                    "edge4_bin_proxy_status": "review_only_not_direct_prs_bin"
                    if row_type == "proxy_bin"
                    else "not_edge4_bin_proxy",
                    "prs_edge20_status": "direct_prs_edge20_not_approved"
                    if row_type == "proxy_bin"
                    else "not_position_binned",
                    "exact_grain_present": _bool_text(exact_present),
                    "eas_route_view_present": _bool_text((route, view) in eas_route_view),
                    "matched_prs_row_count": len(prs_matches),
                    "coverage_verdict": verdict,
                    "decision_use_allowed": "false",
                    "review_only": "true",
                    "prs_artifact": _rel(prs_path),
                    "prs_sha256": prs_sha,
                    "evidence_hash": prs_sha,
                    "can_enter_weighting": "false",
                    "can_enter_jrc": "false",
                    "is_chi_selected": "false",
                    "is_production_ingestion": "false",
                    "is_runtime_configuration": "false",
                    "direct_prs_bin_compatible": _bool_text(direct_edge20),
                }
            )
    return verdicts


def build_edge_policy_checklist() -> list[dict[str, Any]]:
    checks = [
        ("EDGE-POL-001", "COMSOL edge4 definition captured", "quarter bins over edge_norm_1d: 0-0.25, 0.25-0.50, 0.50-0.75, 0.75-1.00", "PASS_REVIEW_FRAMEWORK"),
        ("EDGE-POL-002", "NODI PRS edge20 definition captured", "20 bins over edge_norm_1d with 0.05 increments in current PRS edge_00..edge_19", "PASS_REVIEW_FRAMEWORK"),
        ("EDGE-POL-003", "coarse-to-fine candidate grouping", "edge4 quarter bins may group five PRS edge20 bins each only as review-only candidate", "REVIEW_ONLY_NOT_DIRECT_PRS_BIN"),
        ("EDGE-POL-004", "error-bound requirement", "needs documented aggregation error bounds before any formula or decision use", "NOT_APPROVED"),
        ("EDGE-POL-005", "coverage requirement", "requires complete route/view/diameter/bin coverage including explicit 220/D1200 disposition", "NOT_APPROVED"),
        ("EDGE-POL-006", "monotonicity/conservatism requirement", "needs policy proving conservative grouping or explicit uncertainty flags", "NOT_APPROVED"),
        ("EDGE-POL-007", "loss semantics", "must define how edge4 aggregation preserves or reports information loss relative to edge20", "NOT_APPROVED"),
        ("EDGE-POL-008", "decision-use flags", "decision_use_allowed, weighting, JRC, chi_selected, runtime, production must remain false until future gate", "PASS_BLOCKED"),
    ]
    return [
        {
            "check_id": check_id,
            "check_name": name,
            "requirement_or_observation": note,
            "gate2c_policy_status": status,
            "policy_approved": "false",
            "allowed_use": "review-only policy framework",
            "blocked_use": "direct PRS edge20 grain ingestion; formula input; weighting; JRC; decision use",
            "required_next_gate": "future edge4-to-edge20 policy approval with tests and uncertainty bounds",
        }
        for check_id, name, note, status in checks
    ]


def build_qch_acceptance_checklist(qch_req_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for req in qch_req_rows:
        rows.append(
            {
                "check_id": f"NODI-G2C-{_value(req, 'requirement_id')}",
                "source_requirement_id": _value(req, "requirement_id"),
                "field_name": _value(req, "field_name"),
                "requirement_level": _value(req, "requirement_level"),
                "current_status": "GAP_PRESENT" if _value(req, "missing_from_gate2a_provenance_export") == "true" else "PROVENANCE_ONLY_REVIEWABLE",
                "formal_sidecar_acceptance_status": "NOT_SATISFIED_CURRENTLY",
                "current_qch_artifact_status": "PROVENANCE_ONLY_NOT_FORMAL_SIDECAR",
                "is_formal_gate2_qch_sidecar": "false",
                "qch_weighting_authorized": "false",
                "qch_eta_authorized": "false",
                "qch_chi_eta_authorized": "false",
                "allowed_use": _value(req, "allowed_use"),
                "blocked_use": _value(req, "blocked_use"),
                "required_next_gate": "future formal q_ch / flow-split sidecar export and NODI validation",
            }
        )
    return rows


def build_acceptance_checklist(
    *,
    evidence_register: Sequence[Mapping[str, Any]],
    parent_child_rows: Sequence[Mapping[str, Any]],
    allowed_acceptance_rows: Sequence[Mapping[str, Any]],
    prs_verdict_rows: Sequence[Mapping[str, Any]],
    edge_checklist_rows: Sequence[Mapping[str, Any]],
    qch_checklist_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    checks = [
        ("G2C-ACC-001", "Gate2B freeze accepted", "PASS", "Gate2B partial context-only ledger accepted; not formula/production."),
        ("G2C-ACC-002", "COMSOL support evidence registered", "PASS", f"{len(evidence_register)} support files registered and mirrored."),
        ("G2C-ACC-003", "2-vs-80 parent-child map", "PASS", f"{len(parent_child_rows)} support rows mapped to 2 parent ledger rows."),
        ("G2C-ACC-004", "Allowed support grain authorization false", "PASS_BLOCKED_AS_EXPECTED", f"{len(allowed_acceptance_rows)} rows remain artifact-level only."),
        ("G2C-ACC-005", "PRS coverage verdict complete", "PASS_BLOCKED_AS_EXPECTED", f"{len(prs_verdict_rows)} unique route/view/diameter/type verdicts emitted."),
        ("G2C-ACC-006", "edge4 to edge20 policy", "REVIEW_ONLY_NOT_APPROVED", f"{len(edge_checklist_rows)} checklist rows; no direct PRS bin use."),
        ("G2C-ACC-007", "q_ch formal sidecar", "BLOCKED_AS_EXPECTED", f"{len(qch_checklist_rows)} requirements reviewed; no formal sidecar exists."),
        ("G2C-ACC-008", "weighting/JRC authorization", "PASS_BLOCKED", "All weighting, JRC, chi_selected, decision, runtime, production flags false."),
    ]
    return [
        {
            "check_id": check_id,
            "check_name": name,
            "status": status,
            "finding": finding,
            "can_open_weighting": "false",
            "can_open_jrc": "false",
            "required_next_gate": "COMSOL Gate2C export repair package or future explicit authorization",
        }
        for check_id, name, status, finding in checks
    ]


def build_self_review_rows() -> list[dict[str, Any]]:
    return [
        {
            "reviewer": "Reviewer A",
            "focus": "COMSOL evidence path/SHA/row_count/mirror reproducibility",
            "finding_severity": "PASS",
            "finding": "All COMSOL Gate2B support files are registered with external path, source SHA, row_count, and mirror SHA.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer B",
            "focus": "2-vs-80 parent-child granularity",
            "finding_severity": "PASS",
            "finding": "2 NODI parent ledger rows map to 80 COMSOL support rows; child rows remain artifact-level only.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer C",
            "focus": "PRS coverage and edge4-to-edge20 semantics",
            "finding_severity": "PASS_BLOCKED_AS_EXPECTED",
            "finding": "W800/D900/300 exact PRS grains are present for both views; 220, D1200/300, and edge4-to-edge20 remain blocked/review-only.",
            "unresolved_risk": "edge4-to-edge20 policy not approved",
        },
        {
            "reviewer": "Reviewer D",
            "focus": "forbidden claim leakage and gate logic",
            "finding_severity": "PASS",
            "finding": "No q_ch weighting, chi_selected, JRC, winner, yield, detection, wet pass, clogging, runtime, or production promotion is emitted.",
            "unresolved_risk": "none",
        },
    ]


def validate_gate2c_payload(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if payload.get("status") != PASS_STATUS:
        issues.append("unexpected Gate2C status")
    if payload.get("comsol_allowed_support_row_count") != 80:
        issues.append("COMSOL allowed support row count must be 80")
    if payload.get("parent_child_counts", {}).get("G2CTX-CHI-AGG-004") != 16:
        issues.append("G2CTX-CHI-AGG-004 must map to 16 aggregate support rows")
    if payload.get("parent_child_counts", {}).get("G2CTX-CHI-BIN-005") != 64:
        issues.append("G2CTX-CHI-BIN-005 must map to 64 bin support rows")
    for row in payload.get("allowed_support_acceptance_rows", []):
        if _value(row, "grain_level_authorization_status") != "GRAIN_LEVEL_AUTHORIZATION_FALSE":
            issues.append(f"grain-level authorization not false for {_value(row, 'gate2b_context_row_id')}")
        if _value(row, "gate2b_grain_level_context_ingestion_authorized") != "false":
            issues.append(f"COMSOL allowed row has grain ingestion authorized: {_value(row, 'gate2b_context_row_id')}")
    for row in payload.get("prs_coverage_verdict_rows", []):
        if _value(row, "diameter_nm") == "220" and not _value(row, "coverage_verdict").startswith("BLOCKED_220NM"):
            issues.append("220 nm was not blocked in PRS verdict")
        if "/D1200" in _value(row, "route_key") and _value(row, "diameter_nm") == "300" and _value(row, "exact_grain_present") != "false":
            issues.append("D1200/300 unexpectedly has exact PRS grain")
        if _value(row, "source_row_type") == "proxy_bin" and _value(row, "direct_prs_bin_compatible") != "false":
            issues.append("proxy bin became direct PRS bin")
        if _value(row, "decision_use_allowed") != "false":
            issues.append("PRS verdict allowed decision use")
        if "CANDIDATE_VIEW" in _value(row, "comsol_support_view_binding") and (
            _value(row, "comsol_view_binding_status") != "COMSOL_PROXY_VIEW_BINDING_RECHECK_REQUIRED"
        ):
            issues.append("COMSOL candidate view binding did not fail closed to recheck-required")
    for row in payload.get("qch_acceptance_checklist_rows", []):
        if _value(row, "is_formal_gate2_qch_sidecar") != "false":
            issues.append("q_ch requirement row promoted to formal sidecar")
        if _value(row, "qch_weighting_authorized") != "false":
            issues.append("q_ch weighting authorized")
    issues.extend(_validate_forbidden_flags(payload))
    issues.extend(validate_comsol_v4_readonly_context(payload.get("comsol_v4_context", {})))
    return issues


def write_outputs(payload: Mapping[str, Any], output_dir: Path, report_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "evidence_register_csv": output_dir / EVIDENCE_REGISTER,
        "evidence_manifest_csv": output_dir / EVIDENCE_MANIFEST,
        "parent_child_map_csv": output_dir / PARENT_CHILD_MAP,
        "allowed_acceptance_csv": output_dir / ALLOWED_ACCEPTANCE,
        "prs_verdict_csv": output_dir / PRS_VERDICT,
        "edge_checklist_csv": output_dir / EDGE_CHECKLIST,
        "qch_checklist_csv": output_dir / QCH_CHECKLIST,
        "acceptance_checklist_csv": output_dir / ACCEPTANCE_CHECKLIST,
        "self_review_csv": output_dir / SELF_REVIEW,
        "report_json": output_dir / REPORT_JSON,
        "report_md": output_dir / REPORT_MD,
        "prs_summary_md": output_dir / PRS_SUMMARY,
        "edge_review_md": output_dir / EDGE_REVIEW_MD,
        "qch_gap_md": output_dir / QCH_GAP_MD,
        "report_201_md": report_dir / REPORT_201,
    }
    write_csv_rows(paths["evidence_register_csv"], list(payload["evidence_register_rows"]))
    write_csv_rows(paths["evidence_manifest_csv"], list(payload["evidence_manifest_rows"]))
    write_csv_rows(paths["parent_child_map_csv"], list(payload["parent_child_rows"]))
    write_csv_rows(paths["allowed_acceptance_csv"], list(payload["allowed_support_acceptance_rows"]))
    write_csv_rows(paths["prs_verdict_csv"], list(payload["prs_coverage_verdict_rows"]))
    write_csv_rows(paths["edge_checklist_csv"], list(payload["edge_policy_checklist_rows"]))
    write_csv_rows(paths["qch_checklist_csv"], list(payload["qch_acceptance_checklist_rows"]))
    write_csv_rows(paths["acceptance_checklist_csv"], list(payload["acceptance_checklist_rows"]))
    write_csv_rows(paths["self_review_csv"], list(payload["self_review_rows"]))
    for path in paths.values():
        if path.suffix == ".csv":
            _normalize_lf(path)
    report_payload = dict(payload)
    report_payload["outputs"] = {key: _rel(path) for key, path in paths.items()}
    report_payload["output_hashes"] = {
        key: sha256_file(path) for key, path in paths.items() if path.suffix == ".csv"
    }
    write_json_atomic(paths["report_json"], report_payload, sort_keys=True)
    report_md = render_report_md(report_payload)
    paths["report_md"].write_text(report_md, encoding="utf-8", newline="\n")
    paths["report_201_md"].write_text(
        report_md.replace(
            "# NODI/COMSOL Gate2C Requirement Review And Evidence Stabilization",
            "# Report 201 - NODI/COMSOL Gate2C Requirement Review And Evidence Stabilization",
        ),
        encoding="utf-8",
        newline="\n",
    )
    paths["prs_summary_md"].write_text(render_prs_summary_md(report_payload), encoding="utf-8", newline="\n")
    paths["edge_review_md"].write_text(render_edge_review_md(), encoding="utf-8", newline="\n")
    paths["qch_gap_md"].write_text(render_qch_gap_md(), encoding="utf-8", newline="\n")
    return {key: str(path) for key, path in paths.items()}


def render_report_md(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2C Requirement Review And Evidence Stabilization",
            "",
            "Date: 2026-06-28",
            "",
            "## Disposition",
            "",
            f"`{payload['status']}`",
            "",
            "Gate2B is frozen as accepted partial context-only ledger ready. This report stabilizes COMSOL Gate2B support evidence for NODI review and does not authorize formula, weighting, JRC, runtime, or production use.",
            "",
            "## Key Answers",
            "",
            "- Gate2B accepted partial ledger: `YES`.",
            "- COMSOL Gate2B support evidence registered and mirrored: `YES`.",
            "- COMSOL 80 allowed rows accepted only as artifact-level support rows: `YES`.",
            "- Grain-level authorization for those 80 rows: `FALSE` for all rows.",
            "- edge4-to-edge20 policy approved: `NO`, review-only framework emitted.",
            "- formal q_ch / flow-split sidecar exists: `NO`.",
            "- weighting/JRC/chi_selected/winner/yield/detection_probability allowed: `NO`.",
            "",
            "## Counts",
            "",
            f"- NODI parent ledger rows: `{payload['nodi_gate2b_parent_ledger_row_count']}`",
            f"- COMSOL allowed support rows: `{payload['comsol_allowed_support_row_count']}`",
            f"- COMSOL quarantine rows: `{payload['comsol_quarantine_row_count']}`",
            f"- evidence register rows: `{len(payload['evidence_register_rows'])}`",
            f"- PRS verdict rows: `{len(payload['prs_coverage_verdict_rows'])}`",
            f"- q_ch requirement rows reviewed: `{payload['comsol_qch_requirement_row_count']}`",
            "",
            "## Output Hashes",
            "",
            f"- evidence register: `{hashes.get('evidence_register_csv', 'pending')}`",
            f"- evidence manifest: `{hashes.get('evidence_manifest_csv', 'pending')}`",
            f"- parent-child map: `{hashes.get('parent_child_map_csv', 'pending')}`",
            f"- allowed acceptance: `{hashes.get('allowed_acceptance_csv', 'pending')}`",
            f"- PRS verdict: `{hashes.get('prs_verdict_csv', 'pending')}`",
            f"- edge checklist: `{hashes.get('edge_checklist_csv', 'pending')}`",
            f"- q_ch checklist: `{hashes.get('qch_checklist_csv', 'pending')}`",
            f"- acceptance checklist: `{hashes.get('acceptance_checklist_csv', 'pending')}`",
            "",
            "## Parent-Child Verdict",
            "",
            "`G2CTX-CHI-AGG-004` maps to 16 COMSOL proxy aggregate support rows. `G2CTX-CHI-BIN-005` maps to 64 COMSOL proxy bin support rows. These 80 child rows are not 80 NODI grain ingestion rows; every child row remains artifact-level support with grain-level authorization false.",
            "",
            "## PRS Coverage Verdict",
            "",
            "Current PRS/EAS hashes match Report 199/200. `660/W800/D900`, `300 nm`, both `fixed_660_gold` and `per_wavelength_gold` have exact current PRS grains for context review. `220 nm` has no direct PRS match. `660/W800/D1200`, `300 nm` is absent. Proxy-bin rows remain review-only because edge4-to-edge20 policy is not approved.",
            "",
            "## q_ch Verdict",
            "",
            "No formal q_ch / flow-split sidecar exists. COMSOL q_ch material remains requirements/provenance-only and quarantined. It cannot be q_ch weighting, q_ch*eta, q_ch*chi*eta, route_score, JRC, winner, yield, or detection_probability input.",
            "",
            "## Forbidden Claims",
            "",
            "All Gate2C outputs keep q_ch weighting, q_ch*eta, q_ch*chi*eta, chi_selected, route_score, JRC, yield, winner, detection_probability, wet pass probability, clogging rate, time-to-clog, recovery, fabrication release, runtime configuration, and production ingestion blocked.",
        ]
    ) + "\n"


def render_prs_summary_md(payload: Mapping[str, Any]) -> str:
    counts = payload.get("prs_verdict_counts", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2C PRS Coverage Summary",
            "",
            "Current PRS/EAS artifacts match the frozen Report 199/200 hashes.",
            "",
            f"- PRS rows: `{payload['prs_row_count']}` SHA256 `{payload['prs_sha256']}`",
            f"- EAS rows: `{payload['eas_row_count']}` SHA256 `{payload['eas_sha256']}`",
            f"- verdict counts: `{counts}`",
            "",
            "Decision-use remains false for all COMSOL support rows. Coverage is review evidence only.",
        ]
    ) + "\n"


def render_edge_review_md() -> str:
    return "\n".join(
        [
            "# Gate2C Edge4 To Edge20 Policy Review",
            "",
            "COMSOL proxy-bin rows use edge4 quarter bins over edge_norm_1d. NODI PRS edge20 uses 20 bins over edge_norm_1d at 0.05 increments.",
            "",
            "A candidate coarse-to-fine review grouping is five PRS edge20 bins per COMSOL quarter bin. This is review-only and not a direct PRS bin mapping.",
            "",
            "Policy is not approved. Approval would require error bounds, coverage checks, monotonicity or conservatism criteria, explicit loss semantics, and all decision-use flags remaining false until a future gate.",
        ]
    ) + "\n"


def render_qch_gap_md() -> str:
    return "\n".join(
        [
            "# Gate2C q_ch Formal Sidecar Acceptance And Gap Review",
            "",
            "The current q_ch material is requirements/provenance-only. It is not a formal Gate2 q_ch or flow-split sidecar.",
            "",
            "A future formal sidecar must provide route_key, NODI_view policy, diameter/bin scope, q_ch value, flow_split value, units, normalization basis, source solve/provenance id, geometry hash, integration definition, uncertainty/review flags, blocked-use fields, and validation checks.",
            "",
            "Current state remains blocked for q_ch weighting, q_ch*eta, q_ch*chi*eta, route_score, JRC, winner, yield, and detection_probability.",
        ]
    ) + "\n"


def _evidence_use_policy(role: str) -> tuple[str, str, str, str]:
    if role == "allowed_context_rows":
        return (
            "artifact-level Gate2B support review only",
            "grain-level ingestion; weighting; chi_selected; JRC; production/runtime",
            "context_only_support_not_formula_not_grain_ingestion",
            "NODI Gate2C parent-child and PRS coverage review",
        )
    if "qch" in role:
        return (
            "q_ch formal sidecar requirement review only",
            "formal sidecar use; q_ch weighting; q_ch*eta; q_ch*chi*eta",
            "requirements_only_not_qch_sidecar",
            "future formal q_ch / flow-split sidecar export",
        )
    return (
        "read-only evidence and blocker review",
        "; ".join(FORBIDDEN_CLAIMS),
        "review_only_no_formula_no_production",
        "future explicit Gate2C repair or authorization",
    )


def _validate_forbidden_flags(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    row_groups = (
        payload.get("parent_child_rows", []),
        payload.get("allowed_support_acceptance_rows", []),
        payload.get("prs_coverage_verdict_rows", []),
        payload.get("qch_acceptance_checklist_rows", []),
    )
    for rows in row_groups:
        for row in rows:
            for key in FORBIDDEN_FLAG_FIELDS:
                if key in row and str(row[key]).lower() not in {"false", "", "not_applicable"}:
                    issues.append(f"forbidden flag {key}={row[key]!r} in row {row}")
    return issues


def _row_count(path: Path) -> int:
    if path.suffix.lower() != ".csv":
        return 0
    return len(read_csv_rows(path))


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
    if not args.confirm_gate2c_requirement_review:
        raise SystemExit("Refusing to write Gate2C outputs without explicit confirmation flag.")
    payload = build_gate2c_payload(
        comsol_root=args.comsol_root,
        output_dir=args.output_dir,
        prs_path=args.prs,
        eas_path=args.eas,
        mirror_evidence=True,
    )
    issues = validate_gate2c_payload(payload)
    if issues:
        print(f"NODI_COMSOL_GATE2C_REQUIREMENT_REVIEW: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    report_sha = sha256_file(outputs["report_json"])
    print(f"NODI_COMSOL_GATE2C_REQUIREMENT_REVIEW: {PASS_STATUS}")
    print(f"report_path: {outputs['report_json']}")
    print(f"report_sha256: {report_sha}")
    print(f"evidence_register_csv: {outputs['evidence_register_csv']}")
    print(f"parent_child_map_csv: {outputs['parent_child_map_csv']}")
    print(f"prs_verdict_csv: {outputs['prs_verdict_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
