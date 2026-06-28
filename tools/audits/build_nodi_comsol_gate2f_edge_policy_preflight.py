#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
import re
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
PASS_STATUS = "PASS_GATE2F_EDGE_REVIEW_ONLY_GROUPING_PREFLIGHT_NO_FORMULA_NO_JRC"
PARTIAL_STATUS = "PARTIAL_GATE2F_EDGE_BLOCKED_MISSING_EDGE20_GROUP_BOUNDARY_NO_FORMULA_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2F_EDGE_REVIEW_ONLY_POLICY_PREFLIGHT"

OUTPUT_DIR = Path(f"reports/joint_interface_{DATE_STAMP}")
REPORT_205 = f"205_NODI_COMSOL_GATE2F_EDGE_REVIEW_ONLY_POLICY_PREFLIGHT_{DATE_STAMP}.md"

EVIDENCE_REGISTER = f"NODI_COMSOL_GATE2F_EDGE_COMSOL_SKELETON_EVIDENCE_REGISTER_{DATE_STAMP}.csv"
EVIDENCE_MANIFEST = f"NODI_COMSOL_GATE2F_EDGE_COMSOL_SKELETON_EVIDENCE_MANIFEST_{DATE_STAMP}.csv"
GROUPING_PREFLIGHT = f"NODI_COMSOL_GATE2F_EDGE4_EDGE20_GROUPING_CANDIDATE_PREFLIGHT_{DATE_STAMP}.csv"
ROW_VERDICT = f"NODI_COMSOL_GATE2F_EDGE4_EDGE20_ROW_VERDICT_{DATE_STAMP}.csv"
LOSS_CHECKLIST = f"NODI_COMSOL_GATE2F_EDGE_LOSS_ERROR_SEMANTICS_CHECKLIST_{DATE_STAMP}.csv"
POLICY_REPORT_MD = f"NODI_COMSOL_GATE2F_EDGE_REVIEW_ONLY_POLICY_REPORT_{DATE_STAMP}.md"
NON_EDGE_CARRY_FORWARD = f"NODI_COMSOL_GATE2F_NON_EDGE_WORKSTREAM_CARRY_FORWARD_{DATE_STAMP}.csv"
DASHBOARD = f"NODI_COMSOL_GATE2F_EDGE_RECEIVER_DASHBOARD_{DATE_STAMP}.csv"
SELF_REVIEW = f"NODI_COMSOL_GATE2F_EDGE_SELF_REVIEW_{DATE_STAMP}.csv"
REPORT_JSON = f"NODI_COMSOL_GATE2F_EDGE_POLICY_PREFLIGHT_REPORT_{DATE_STAMP}.json"
REPORT_MD = f"NODI_COMSOL_GATE2F_EDGE_POLICY_PREFLIGHT_REPORT_{DATE_STAMP}.md"

DEFAULT_COMSOL_ROOT = PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
NODI_REPORT_204 = PROJECT_ROOT / "reports/204_NODI_COMSOL_GATE2E_RECEIVER_POLICY_VERDICTS_20260628.md"
NODI_GATE2E_EDGE_VERDICT = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2E_EDGE_RECEIVER_POLICY_VERDICT_20260628.csv"
NODI_GATE2E_EDGE20_SNAPSHOT = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2E_EDGE20_DEFINITION_SNAPSHOT_20260628.csv"
NODI_GATE2E_DASHBOARD = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2E_RECEIVER_DASHBOARD_20260628.csv"
NODI_GATE2D_ACCEPTED_LEDGER = PROJECT_ROOT / OUTPUT_DIR / "NODI_COMSOL_GATE2D_ACCEPTED_REDUCED_SCOPE_CONTEXT_LEDGER_20260628.csv"

COMSOL_EDGE_SKELETON = Path("roadmap/COMSOL_GATE2E_EDGE4_EDGE20_MINIMAL_DELIVERABLE_SKELETON_20260628.csv")
COMSOL_EDGE_PACKET = Path("roadmap/COMSOL_GATE2E_EDGE4_EDGE20_MINIMAL_DELIVERABLE_PACKET_20260628.md")
COMSOL_MINIMAL_DASHBOARD = Path("roadmap/COMSOL_GATE2E_MINIMAL_DELIVERABLE_DASHBOARD_20260628.csv")
COMSOL_MINIMAL_VALIDATION = Path("roadmap/COMSOL_GATE2E_MINIMAL_DELIVERABLE_VALIDATION_20260628.csv")
COMSOL_MINIMAL_MANIFEST = Path("roadmap/COMSOL_GATE2E_MINIMAL_DELIVERABLE_MANIFEST_20260628.csv")

EXPECTED_EDGE20_DEFINITION_HASH = "b8b3358e7218e3ebc704c2c8dcaf2c9a0feb15283fa704610b39f8afc68d5ca3"
EXPECTED_PRS_SHA = "9ba83c84a563cd856b2fc624c523843a6e283206d5ac2e592a2b72607645f393"
EXPECTED_GATE2D_ACCEPTED_ROW_COUNT = 4
FORBIDDEN_FALSE_FIELDS = (
    "accepted_row_expansion_authorized",
    "edge4_row_accepted",
    "context_only_acceptance_allowed",
    "direct_prs_bin_use_authorized",
    "formula_use_authorized",
    "grain_level_ingestion_authorized",
    "qch_weighting_authorized",
    "qch_eta_authorized",
    "qch_chi_eta_authorized",
    "chi_selected_authorized",
    "route_score_authorized",
    "jrc_authorized",
    "yield_authorized",
    "winner_authorized",
    "detection_probability_authorized",
    "runtime_configuration_authorized",
    "production_ingestion_authorized",
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
    "direct PRS edge20 bin use",
    "grain-level ingestion",
    "formula use",
    "q_ch weighting",
    "q_ch*eta",
    "q_ch*chi*eta",
    "chi_selected",
    "route_score",
    "JOINT_ROUTE_CLASS/JRC",
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
    parser = argparse.ArgumentParser(description="Build NODI Gate2F-EDGE review-only policy preflight outputs.")
    parser.add_argument("--confirm-gate2f-edge-preflight", action="store_true")
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "reports")
    return parser


def build_gate2f_edge_payload(
    *,
    comsol_root: Path,
    report_204_path: Path | None = None,
    edge_verdict_path: Path | None = None,
    edge20_snapshot_path: Path | None = None,
    gate2e_dashboard_path: Path | None = None,
    gate2d_accepted_ledger_path: Path | None = None,
) -> dict[str, Any]:
    report_204_path = report_204_path or NODI_REPORT_204
    edge_verdict_path = edge_verdict_path or NODI_GATE2E_EDGE_VERDICT
    edge20_snapshot_path = edge20_snapshot_path or NODI_GATE2E_EDGE20_SNAPSHOT
    gate2e_dashboard_path = gate2e_dashboard_path or NODI_GATE2E_DASHBOARD
    gate2d_accepted_ledger_path = gate2d_accepted_ledger_path or NODI_GATE2D_ACCEPTED_LEDGER
    edge_skeleton_path = comsol_root / COMSOL_EDGE_SKELETON
    minimal_manifest_path = comsol_root / COMSOL_MINIMAL_MANIFEST
    skeleton_rows = read_csv_rows(edge_skeleton_path)
    manifest_rows = read_csv_rows(minimal_manifest_path)
    gate2d_rows = read_csv_rows(gate2d_accepted_ledger_path)
    edge_verdict_rows = read_csv_rows(edge_verdict_path)
    edge20_rows = read_csv_rows(edge20_snapshot_path)
    gate2e_dashboard_rows = read_csv_rows(gate2e_dashboard_path)
    report_204_text = report_204_path.read_text(encoding="utf-8")

    evidence_rows = build_evidence_register(comsol_root=comsol_root, manifest_rows=manifest_rows)
    evidence_manifest_rows = build_evidence_manifest(evidence_rows)
    grouping_rows = build_grouping_rows(skeleton_rows, edge20_rows)
    row_verdict_rows = build_row_verdict_rows(grouping_rows)
    loss_checklist_rows = build_loss_error_checklist_rows()
    non_edge_rows = build_non_edge_carry_forward_rows(gate2e_dashboard_rows)
    dashboard_rows = build_dashboard_rows(grouping_rows, gate2d_rows, non_edge_rows)
    self_review_rows = build_self_review_rows()
    status = PASS_STATUS if all(_value(row, "review_only_status") == "REVIEW_ONLY_GROUPING_CANDIDATE_DERIVED" for row in grouping_rows) else PARTIAL_STATUS

    payload: dict[str, Any] = {
        "schema_version": "nodi_comsol_gate2f_edge_policy_preflight_v1",
        "date_stamp": DATE_STAMP,
        "status": status,
        "gate2f_edge_disposition": status,
        "gate2d_freeze_confirmed": len(gate2d_rows) == EXPECTED_GATE2D_ACCEPTED_ROW_COUNT,
        "gate2d_accepted_row_count": len(gate2d_rows),
        "comsol_edge_skeleton_row_count": len(skeleton_rows),
        "nodi_edge20_snapshot_row_count": len(edge20_rows),
        "nodi_edge20_definition_hash": _edge20_hash(edge20_rows),
        "nodi_prs_sha256": _first_non_empty(edge20_rows, "source_prs_sha256"),
        "gate2e_edge_receiver_verdicts": [_value(row, "receiver_verdict") for row in edge_verdict_rows],
        "report204_gate2e_pass_present": "PASS_GATE2E_RECEIVER_POLICY_VERDICTS_NO_ACCEPTED_ROW_EXPANSION_NO_WEIGHTING_NO_JRC"
        in report_204_text,
        "evidence_register_rows": evidence_rows,
        "evidence_manifest_rows": evidence_manifest_rows,
        "grouping_candidate_preflight_rows": grouping_rows,
        "row_verdict_rows": row_verdict_rows,
        "loss_error_semantics_checklist_rows": loss_checklist_rows,
        "non_edge_carry_forward_rows": non_edge_rows,
        "receiver_dashboard_rows": dashboard_rows,
        "self_review_rows": self_review_rows,
        "comsol_v4_context": default_comsol_v4_readonly_context(),
        "accepted_row_expansion_authorized": False,
        "edge4_policy_approved": False,
        "formula_use_authorized": False,
        "direct_prs_bin_use_authorized": False,
        "grain_level_ingestion_authorized": False,
        "weighting_or_jrc_allowed": False,
        "qch_binding_status_changed": False,
    }
    return payload


def build_evidence_register(*, comsol_root: Path, manifest_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    manifest_by_path = {_value(row, "path"): row for row in manifest_rows}
    specs = [
        ("G2F-EDGE-SKEL", "edge_minimal_skeleton", COMSOL_EDGE_SKELETON),
        ("G2F-EDGE-PACKET", "edge_minimal_packet", COMSOL_EDGE_PACKET),
        ("G2F-MIN-DASH", "minimal_deliverable_dashboard", COMSOL_MINIMAL_DASHBOARD),
        ("G2F-MIN-VALIDATION", "minimal_deliverable_validation", COMSOL_MINIMAL_VALIDATION),
        ("G2F-MIN-MANIFEST", "minimal_deliverable_manifest", COMSOL_MINIMAL_MANIFEST),
    ]
    rows: list[dict[str, str]] = []
    for evidence_id, role, relative in specs:
        path = comsol_root / relative
        manifest = manifest_by_path.get(relative.as_posix(), {})
        source_sha = sha256_file(path)
        source_rows = _row_count(path)
        rows.append(
            {
                "evidence_id": evidence_id,
                "source_repo_or_project": "comsol_ev_pbs_bonded_cross_junction",
                "source_path": str(path),
                "relative_source_path": relative.as_posix(),
                "file_role": role,
                "source_artifact": relative.as_posix(),
                "source_sha256": source_sha,
                "row_count": str(source_rows),
                "manifest_sha256_if_any": _value(manifest, "sha256"),
                "manifest_row_count_if_any": _value(manifest, "row_count"),
                "manifest_match": _bool_text(
                    (not manifest)
                    or (
                        _value(manifest, "sha256") == source_sha
                        and _value(manifest, "row_count") in {str(source_rows), "0"}
                    )
                ),
                "copied_or_external_reference": "external_reference_only",
                "nodi_edge20_definition_hash": EXPECTED_EDGE20_DEFINITION_HASH,
                "allowed_use": "Gate2F-EDGE receiver review-only policy preflight evidence",
                "blocked_use": "; ".join(FORBIDDEN_CLAIMS),
                "claim_boundary": "skeleton/review-only; not accepted rows; not formula; not production",
                "required_next_gate": "loss/error semantics package before any stronger EDGE policy gate",
            }
        )
    return rows


def build_evidence_manifest(evidence_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "manifest_id": f"NODI-G2F-EDGE-EVID-MAN-{index:03d}",
            "evidence_id": _value(row, "evidence_id"),
            "relative_source_path": _value(row, "relative_source_path"),
            "source_sha256": _value(row, "source_sha256"),
            "row_count": _value(row, "row_count"),
            "manifest_match": _value(row, "manifest_match"),
            "registration_status": "REGISTERED_EXTERNAL_REFERENCE_ONLY",
            "nodi_edge20_definition_hash": _value(row, "nodi_edge20_definition_hash"),
            "allowed_use": _value(row, "allowed_use"),
            "blocked_use": _value(row, "blocked_use"),
        }
        for index, row in enumerate(evidence_rows, start=1)
    ]


def build_grouping_rows(
    skeleton_rows: Sequence[Mapping[str, Any]], edge20_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, str]]:
    edge20_bins = _edge20_bins(edge20_rows)
    edge20_hash = _edge20_hash(edge20_rows)
    rows: list[dict[str, str]] = []
    for index, skeleton in enumerate(skeleton_rows, start=1):
        label = _value(skeleton, "edge4_bin_label")
        bounds = _parse_edge4_bounds(label)
        covered = _covered_edge20_bins(edge20_bins, bounds) if bounds else []
        can_group = bool(bounds and covered and _covers_bounds(covered, bounds))
        rows.append(
            {
                "grouping_preflight_id": f"NODI-G2F-EDGE-GROUP-{index:03d}",
                "source_edge_deliverable_row_id": _value(skeleton, "edge_deliverable_row_id"),
                "source_edge4_artifact": _value(skeleton, "source_edge4_artifact"),
                "source_sha256": _value(skeleton, "source_sha256"),
                "source_row_identity": _value(skeleton, "source_row_identity"),
                "route_key": _value(skeleton, "route_key_candidate"),
                "NODI_view": _value(skeleton, "NODI_view"),
                "diameter_nm": _value(skeleton, "diameter_nm"),
                "tpd_proxy_aggregation_basis": _proxy_basis(_value(skeleton, "source_row_identity")),
                "edge4_bin_label": label,
                "edge4_min": _format_float(bounds[0]) if bounds else "",
                "edge4_max": _format_float(bounds[1]) if bounds else "",
                "candidate_edge20_group": "|".join(bin_row["bin_id"] for bin_row in covered),
                "edge20_bins_covered": str(len(covered)),
                "nodi_edge20_definition_hash": edge20_hash,
                "grouping_derivation": "derived_from_NODI_edge20_snapshot_boundaries"
                if can_group
                else "BLOCKED_MISSING_EDGE20_GROUP_BOUNDARY",
                "review_only_status": "REVIEW_ONLY_GROUPING_CANDIDATE_DERIVED"
                if can_group
                else "BLOCKED_MISSING_EDGE20_GROUP_BOUNDARY",
                "edge4_row_accepted": "false",
                "accepted_row_expansion_authorized": "false",
                "context_only_acceptance_allowed": "false",
                "direct_prs_bin_use_authorized": "false",
                "formula_use_authorized": "false",
                "grain_level_ingestion_authorized": "false",
                "can_enter_weighting": "false",
                "can_enter_jrc": "false",
                "allowed_use": "review-only grouping candidate preflight",
                "blocked_use": "direct PRS bin use; formula; grain-level ingestion; weighting; JRC; accepted ledger expansion",
                "required_next_gate": "loss/error semantics and conservative grouping review",
            }
        )
    return rows


def build_row_verdict_rows(grouping_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "row_verdict_id": f"NODI-G2F-EDGE-ROW-{index:03d}",
            "source_edge_deliverable_row_id": _value(row, "source_edge_deliverable_row_id"),
            "route_key": _value(row, "route_key"),
            "NODI_view": _value(row, "NODI_view"),
            "diameter_nm": _value(row, "diameter_nm"),
            "edge4_bin_label": _value(row, "edge4_bin_label"),
            "candidate_edge20_group": _value(row, "candidate_edge20_group"),
            "nodi_edge20_definition_hash": _value(row, "nodi_edge20_definition_hash"),
            "receiver_row_verdict": _value(row, "review_only_status"),
            "edge4_policy_approved": "false",
            "edge4_row_accepted": "false",
            "accepted_row_expansion_authorized": "false",
            "direct_prs_bin_use_authorized": "false",
            "formula_use_authorized": "false",
            "grain_level_ingestion_authorized": "false",
            "blocked_use": _value(row, "blocked_use"),
        }
        for index, row in enumerate(grouping_rows, start=1)
    ]


def build_loss_error_checklist_rows() -> list[dict[str, str]]:
    specs = [
        ("LOSS-001", "information_loss", "Define what is lost when five edge20 bins are summarized as one edge4 quarter bin."),
        ("LOSS-002", "coverage", "Prove complete and non-overlapping edge4 coverage of the hashed edge20 definition."),
        ("LOSS-003", "monotonicity", "Check whether coarse grouping preserves expected ordering or explicitly flags violations."),
        ("LOSS-004", "conservativeness", "Define conservative bounds or a no-decision-use fallback."),
        ("LOSS-005", "error_bounds", "Provide numerical or categorical upper/lower error bounds before stronger use."),
        ("LOSS-006", "reproducibility", "Pin source SHA, row_count, edge20 hash, grouping method, and validation checks."),
        ("LOSS-007", "review_context_only", "Keep review-only flags true and all formula/direct-bin/grain flags false."),
        ("LOSS-008", "formula_exclusion", "List conditions that still forbid formula use even if grouping is reproducible."),
    ]
    return [
        {
            "check_id": f"NODI-G2F-EDGE-{check_id}",
            "semantics_area": area,
            "required_evidence": required,
            "current_status": "PENDING_REQUIRED_FOR_POLICY_APPROVAL"
            if area not in {"coverage", "reproducibility", "review_context_only"}
            else "PREFLIGHT_REVIEWABLE_NOT_APPROVED",
            "policy_approved": "false",
            "allowed_use": "review-only policy preflight",
            "blocked_use": "formula use; direct PRS bin use; grain-level ingestion; weighting; JRC",
            "required_next_gate": "Gate2F/2G EDGE loss-error semantics evidence package",
        }
        for check_id, area, required in specs
    ]


def build_non_edge_carry_forward_rows(gate2e_dashboard_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    by_gate = {_value(row, "gate"): row for row in gate2e_dashboard_rows}
    return [
        {
            "carry_forward_id": "NODI-G2F-NONEDGE-QCH",
            "workstream": "Gate2E-QCH",
            "prior_receiver_status": _value(by_gate.get("Gate2E-QCH", {}), "receiver_status"),
            "gate2f_status": "UNCHANGED_SCHEMA_READY_NO_FORMAL_SIDECAR",
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "required_next_gate": "formal q_ch / flow-split sidecar receipt package",
        },
        {
            "carry_forward_id": "NODI-G2F-NONEDGE-BINDING",
            "workstream": "Gate2E-BINDING",
            "prior_receiver_status": _value(by_gate.get("Gate2E-BINDING", {}), "receiver_status"),
            "gate2f_status": "UNCHANGED_220_D1200_UNBOUND_FAIL_CLOSED",
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "required_next_gate": "220/D1200/view-bound repair package",
        },
    ]


def build_dashboard_rows(
    grouping_rows: Sequence[Mapping[str, Any]],
    gate2d_rows: Sequence[Mapping[str, Any]],
    non_edge_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    derived = sum(1 for row in grouping_rows if _value(row, "review_only_status") == "REVIEW_ONLY_GROUPING_CANDIDATE_DERIVED")
    blocked = len(grouping_rows) - derived
    return [
        {
            "dashboard_id": "NODI-G2F-DASH-001",
            "workstream": "Gate2D-FREEZE",
            "status": "FROZEN_ACCEPTED_LEDGER_EXACTLY_FOUR_ROWS",
            "row_count": str(len(gate2d_rows)),
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "can_enter_jrc": "false",
            "required_next_gate": "none for Gate2F EDGE preflight",
        },
        {
            "dashboard_id": "NODI-G2F-DASH-002",
            "workstream": "Gate2F-EDGE",
            "status": "REVIEW_ONLY_GROUPING_PREFLIGHT_DERIVED" if blocked == 0 else "PARTIAL_BLOCKED_MISSING_BOUNDARY",
            "row_count": str(len(grouping_rows)),
            "derived_grouping_row_count": str(derived),
            "blocked_grouping_row_count": str(blocked),
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "can_enter_jrc": "false",
            "required_next_gate": "loss/error semantics review",
        },
        {
            "dashboard_id": "NODI-G2F-DASH-003",
            "workstream": "Gate2F-NONEDGE",
            "status": "; ".join(_value(row, "gate2f_status") for row in non_edge_rows),
            "row_count": str(len(non_edge_rows)),
            "accepted_row_expansion_authorized": "false",
            "formula_use_authorized": "false",
            "can_enter_jrc": "false",
            "required_next_gate": "QCH/BINDING future packages; no state change in Gate2F EDGE",
        },
    ]


def build_self_review_rows() -> list[dict[str, str]]:
    return [
        {
            "reviewer": "Reviewer A",
            "focus": "source evidence/SHA/row_count",
            "finding_severity": "PASS",
            "finding": "COMSOL EDGE skeleton, packet, dashboard, validation, and manifest are registered as read-only evidence.",
            "unresolved_risk": "none",
        },
        {
            "reviewer": "Reviewer B",
            "focus": "edge20 definition/hash/grouping derivation",
            "finding_severity": "PASS",
            "finding": "edge4 quarter-bin candidates are derived from NODI edge20 snapshot boundaries and hash, not from direct PRS bin authorization.",
            "unresolved_risk": "none for preflight; policy approval still pending",
        },
        {
            "reviewer": "Reviewer C",
            "focus": "loss/error semantics and review-only boundary",
            "finding_severity": "PASS_BLOCKED_AS_EXPECTED",
            "finding": "Grouping can be reviewed, but loss/error semantics remain pending and policy is not approved.",
            "unresolved_risk": "loss/error bounds and conservativeness evidence required",
        },
        {
            "reviewer": "Reviewer D",
            "focus": "forbidden claim leakage and no accepted row expansion",
            "finding_severity": "PASS",
            "finding": "All formula, direct-bin, grain-ingestion, weighting, JRC, runtime, and production flags remain false.",
            "unresolved_risk": "none",
        },
    ]


def validate_gate2f_payload(payload: Mapping[str, Any], *, comsol_root: Path) -> list[str]:
    issues: list[str] = []
    status = _value(payload, "status")
    if status not in {PASS_STATUS, PARTIAL_STATUS}:
        issues.append("unexpected Gate2F disposition")
    if int(payload.get("gate2d_accepted_row_count", -1)) != EXPECTED_GATE2D_ACCEPTED_ROW_COUNT:
        issues.append("Gate2D accepted ledger row count must remain exactly 4")
    if _value(payload, "nodi_edge20_definition_hash") != EXPECTED_EDGE20_DEFINITION_HASH:
        issues.append("edge20 definition hash mismatch hard fail")
    if _value(payload, "nodi_prs_sha256") != EXPECTED_PRS_SHA:
        issues.append("PRS hash drift hard fail")
    if int(payload.get("comsol_edge_skeleton_row_count", -1)) != 16:
        issues.append("COMSOL EDGE skeleton must have 16 rows")
    for row in payload.get("evidence_register_rows", []):
        if _value(row, "manifest_match") != "true":
            issues.append(f"COMSOL evidence manifest mismatch: {_value(row, 'evidence_id')}")
        path = comsol_root / _value(row, "relative_source_path")
        if sha256_file(path) != _value(row, "source_sha256"):
            issues.append(f"COMSOL evidence hash drift: {_value(row, 'evidence_id')}")
    for row in payload.get("grouping_candidate_preflight_rows", []):
        if _value(row, "route_key") != "660/W800/D900":
            issues.append("EDGE row route is outside reduced review scope")
        if _value(row, "diameter_nm") != "300":
            issues.append("EDGE row diameter is outside reduced review scope")
        if _value(row, "NODI_view") not in {"fixed_660_gold", "per_wavelength_gold"}:
            issues.append("EDGE row view is outside reduced review scope")
        if _value(row, "edge20_bins_covered") != "5" and _value(row, "review_only_status") == "REVIEW_ONLY_GROUPING_CANDIDATE_DERIVED":
            issues.append("derived EDGE grouping must cover exactly five edge20 bins")
    if status == PASS_STATUS and any(
        _value(row, "review_only_status") != "REVIEW_ONLY_GROUPING_CANDIDATE_DERIVED"
        for row in payload.get("grouping_candidate_preflight_rows", [])
    ):
        issues.append("PASS disposition cannot contain blocked grouping rows")
    for group in (
        "grouping_candidate_preflight_rows",
        "row_verdict_rows",
        "loss_error_semantics_checklist_rows",
        "non_edge_carry_forward_rows",
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
        "grouping_preflight_csv": output_dir / GROUPING_PREFLIGHT,
        "row_verdict_csv": output_dir / ROW_VERDICT,
        "loss_checklist_csv": output_dir / LOSS_CHECKLIST,
        "policy_report_md": output_dir / POLICY_REPORT_MD,
        "non_edge_carry_forward_csv": output_dir / NON_EDGE_CARRY_FORWARD,
        "dashboard_csv": output_dir / DASHBOARD,
        "self_review_csv": output_dir / SELF_REVIEW,
        "report_json": output_dir / REPORT_JSON,
        "report_md": output_dir / REPORT_MD,
        "report_205_md": report_dir / REPORT_205,
    }
    write_csv_rows(paths["evidence_register_csv"], list(payload["evidence_register_rows"]))
    write_csv_rows(paths["evidence_manifest_csv"], list(payload["evidence_manifest_rows"]))
    write_csv_rows(paths["grouping_preflight_csv"], list(payload["grouping_candidate_preflight_rows"]))
    write_csv_rows(paths["row_verdict_csv"], list(payload["row_verdict_rows"]))
    write_csv_rows(paths["loss_checklist_csv"], list(payload["loss_error_semantics_checklist_rows"]))
    write_csv_rows(paths["non_edge_carry_forward_csv"], list(payload["non_edge_carry_forward_rows"]))
    write_csv_rows(paths["dashboard_csv"], list(payload["receiver_dashboard_rows"]))
    write_csv_rows(paths["self_review_csv"], list(payload["self_review_rows"]))
    for path in paths.values():
        if path.suffix == ".csv":
            _normalize_lf(path)

    paths["policy_report_md"].write_text(render_policy_report(payload), encoding="utf-8", newline="\n")
    report_payload = dict(payload)
    report_payload["outputs"] = {key: _rel(path) for key, path in paths.items()}
    report_payload["output_hashes"] = {
        key: sha256_file(path)
        for key, path in paths.items()
        if path.exists() and path.suffix in {".csv", ".md"}
    }
    write_json_atomic(paths["report_json"], report_payload, sort_keys=True)
    report_payload["output_hashes"]["report_json"] = sha256_file(paths["report_json"])
    report_md = render_report_md(report_payload)
    paths["report_md"].write_text(report_md, encoding="utf-8", newline="\n")
    paths["report_205_md"].write_text(
        report_md.replace(
            "# NODI/COMSOL Gate2F-EDGE Review-Only Policy Preflight",
            "# Report 205 - NODI/COMSOL Gate2F-EDGE Review-Only Policy Preflight",
        ),
        encoding="utf-8",
        newline="\n",
    )
    return {key: str(path) for key, path in paths.items()}


def render_policy_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# NODI Gate2F-EDGE Review-Only Policy Report",
            "",
            f"Disposition: `{payload['status']}`.",
            "",
            "The COMSOL 16-row edge4 minimal skeleton can be aligned to NODI edge20 snapshot boundaries as review-only grouping candidates. This is not acceptance, formula use, direct PRS bin use, or grain-level ingestion.",
            "",
            "Loss/error semantics remain pending: information loss, coverage proof, monotonicity, conservativeness, error bounds, reproducibility, review-only flags, and formula exclusions must be supplied before any stronger EDGE gate.",
        ]
    ) + "\n"


def render_report_md(payload: Mapping[str, Any]) -> str:
    hashes = payload.get("output_hashes", {})
    return "\n".join(
        [
            "# NODI/COMSOL Gate2F-EDGE Review-Only Policy Preflight",
            "",
            "Date: 2026-06-28",
            "",
            "## Disposition",
            "",
            f"`{payload['status']}`",
            "",
            "Gate2D accepted ledger remains frozen at exactly four aggregate proxy rows. Gate2F-EDGE adds no accepted rows and authorizes no formula, direct PRS bin use, grain-level ingestion, weighting, or JRC.",
            "",
            "## Grouping Verdict",
            "",
            f"COMSOL EDGE skeleton rows reviewed: `{payload['comsol_edge_skeleton_row_count']}`.",
            f"NODI edge20 definition hash: `{payload['nodi_edge20_definition_hash']}`.",
            "",
            "Each edge4 quarter bin is mapped from the NODI edge20 snapshot boundaries into five candidate edge20 bins as a review-only grouping candidate. The mapping is derived from the snapshot, not from a direct PRS bin-use authorization.",
            "",
            "## Loss/Error Semantics",
            "",
            "Policy is not approved. Future evidence must define information loss, complete coverage, monotonicity/conservativeness checks, error bounds, reproducibility, and conditions that still forbid formula use.",
            "",
            "## QCH/BINDING Carry-Forward",
            "",
            "QCH remains schema-ready but no formal sidecar is present. BINDING remains fail-closed for 220 nm, D1200/300, and UNBOUND NODI_view. No status change is made in this EDGE preflight.",
            "",
            "## Output Hashes",
            "",
            f"- evidence register: `{hashes.get('evidence_register_csv', 'pending')}`",
            f"- grouping preflight: `{hashes.get('grouping_preflight_csv', 'pending')}`",
            f"- row verdict: `{hashes.get('row_verdict_csv', 'pending')}`",
            f"- loss/error checklist: `{hashes.get('loss_checklist_csv', 'pending')}`",
            f"- dashboard: `{hashes.get('dashboard_csv', 'pending')}`",
            f"- JSON report: `{hashes.get('report_json', 'pending')}`",
            "",
            "## Non-Authorization",
            "",
            "No q_ch weighting, q_ch*eta, q_ch*chi*eta, chi_selected, route_score, JOINT_ROUTE_CLASS/JRC, yield, winner, detection_probability, wet pass probability, clogging rate, runtime configuration, or production ingestion is authorized.",
        ]
    ) + "\n"


def _edge20_bins(edge20_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    bins: list[dict[str, Any]] = []
    for row in edge20_rows:
        if _value(row, "definition_status") != "PASS_EDGE20_DEFINITION_HASHED":
            continue
        bins.append(
            {
                "bin_id": _value(row, "bin_id"),
                "min": float(_value(row, "edge_norm_min")),
                "max": float(_value(row, "edge_norm_max")),
            }
        )
    return sorted(bins, key=lambda row: row["min"])


def _covered_edge20_bins(edge20_bins: Sequence[Mapping[str, Any]], bounds: tuple[float, float]) -> list[Mapping[str, Any]]:
    lo, hi = bounds
    eps = 1e-9
    return [
        row
        for row in edge20_bins
        if float(row["min"]) + eps >= lo and float(row["max"]) <= hi + eps
    ]


def _covers_bounds(covered: Sequence[Mapping[str, Any]], bounds: tuple[float, float]) -> bool:
    if not covered:
        return False
    lo, hi = bounds
    eps = 1e-9
    return abs(float(covered[0]["min"]) - lo) < eps and abs(float(covered[-1]["max"]) - hi) < eps


def _parse_edge4_bounds(label: str) -> tuple[float, float] | None:
    match = re.fullmatch(r"edge_norm_(\d+)p(\d+)_(\d+)p(\d+)", label)
    if not match:
        return None
    left = float(f"{int(match.group(1))}.{match.group(2)}")
    right = float(f"{int(match.group(3))}.{match.group(4)}")
    return left, right


def _proxy_basis(identity: str) -> str:
    if "velocity_weighted" in identity:
        return "velocity_weighted"
    if "residence_time_weighted" in identity:
        return "residence_time_weighted"
    return "unknown"


def _edge20_hash(edge20_rows: Sequence[Mapping[str, Any]]) -> str:
    hashes = {_value(row, "edge20_definition_hash") for row in edge20_rows if _value(row, "edge20_definition_hash")}
    return sorted(hashes)[0] if hashes else ""


def _first_non_empty(rows: Sequence[Mapping[str, Any]], field: str) -> str:
    for row in rows:
        value = _value(row, field)
        if value:
            return value
    return ""


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


def _format_float(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _normalize_lf(path: Path) -> None:
    data = path.read_bytes()
    while b"\r\n" in data:
        data = data.replace(b"\r\n", b"\n")
    data = data.replace(b"\r", b"")
    path.write_bytes(data)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate2f_edge_preflight:
        raise SystemExit("Refusing to write Gate2F-EDGE outputs without explicit confirmation flag.")
    payload = build_gate2f_edge_payload(comsol_root=args.comsol_root)
    issues = validate_gate2f_payload(payload, comsol_root=args.comsol_root)
    if issues:
        print(f"NODI_COMSOL_GATE2F_EDGE_POLICY_PREFLIGHT: {BLOCKED_STATUS}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload, args.output_dir, args.report_dir)
    report_sha = sha256_file(outputs["report_json"])
    print(f"NODI_COMSOL_GATE2F_EDGE_POLICY_PREFLIGHT: {payload['status']}")
    print(f"report_path: {outputs['report_json']}")
    print(f"report_sha256: {report_sha}")
    print(f"grouping_preflight_csv: {outputs['grouping_preflight_csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
