#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
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


SCHEMA_VERSION = "nodi_comsol_gate2_context_candidate_register_v1"
REPORT_SCHEMA_VERSION = "nodi_comsol_gate2_context_candidate_preflight_report_v1"
PASS_STATUS = "PASS_GATE2_CONTEXT_CANDIDATE_PREFLIGHT_NO_WEIGHTING_NO_JRC"
BLOCKED_STATUS = "BLOCKED_GATE2_CONTEXT_CANDIDATE_PREFLIGHT"

OUTPUT_DIR = Path("reports/joint_interface_20260627")
REPORT_FILENAME = "NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_PREFLIGHT_REPORT_20260627.json"
REPORT_MD_FILENAME = "NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_PREFLIGHT_REPORT_20260627.md"
REGISTER_FILENAME = "NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_20260627.csv"
BLOCKED_GRAINS_FILENAME = "NODI_COMSOL_GATE2_CONTEXT_BLOCKED_GRAIN_REGISTER_20260627.csv"
SCHEMA_FILENAME = "NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_SCHEMA_20260627.csv"

MISSING_SHA = "MISSING_UNTIL_FORMAL_GATE2_EXPORT"

DEFAULT_COMSOL_ROOT = (
    PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
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

FORBIDDEN_OUTPUT_FIELDS = (
    "q_ch_eta",
    "qch_eta",
    "q_ch_times_eta",
    "qch_times_eta",
    "winner",
    "detection_probability",
    "joint_route_class",
    "jrc",
    "yield",
    "wet_pass_probability",
    "clogging_rate",
    "true_w_eff",
    "measured_geometry",
)

FORBIDDEN_ALLOWED_USE_TERMS = (
    "q_ch*eta",
    "q_ch eta",
    "chi_selected",
    "route score",
    "yield",
    "winner",
    "detection probability",
    "joint_route_class",
    "jrc",
    "wet pass probability",
    "clogging rate",
    "production ingestion",
)

COMMON_BLOCKED_USE = (
    "PRS occupancy; q_ch*eta; chi_selected; route score; yield; winner; "
    "detection_probability; JOINT_ROUTE_CLASS; true W_eff; measured geometry; "
    "optical solver claim; wet pass probability; clogging rate"
)

REGISTER_FIELDS = (
    "register_row_id",
    "schema_version",
    "candidate_type",
    "source_artifact",
    "sha256",
    "row_count",
    "producer",
    "evidence_class",
    "route_key",
    "diameter_basis",
    "bin_basis",
    "claim_boundary",
    "allowed_use",
    "blocked_use",
    "required_next_gate",
    "v4_context_binding",
    "candidate_status",
    "grain_alignment_status",
    "matched_grain_count",
    "blocked_grain_count",
    "review_note",
)

ALLOWED_CANDIDATE_STATUSES = frozenset(
    {
        "GATE2_CANDIDATE_CONTEXT_ONLY_REVIEWABLE",
        "GATE2_CANDIDATE_CONTEXT_ONLY_PARTIAL_GRAIN_MATCH",
        "REVIEW_ONLY_NOT_GATE2_INPUT",
        "BLOCKED_MISSING_FORMAL_GATE2_EXPORT",
        "BLOCKED_ROUTE_DIAMETER_BIN_MISMATCH",
    }
)

REVIEW_ONLY_TYPES = frozenset(
    {
        "local-Q hydraulic anchor / event-tree diagnostic candidate",
        "V4 sample/surface review-only context",
    }
)

ROUTE_FAMILY_RE = re.compile(r"(?P<route>\d+/W\d+/D\d+)")
CASE_ROUTE_RE = re.compile(r"W(?P<width>\d+)_D(?P<depth>\d+)")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class CandidateSpec:
    register_row_id: str
    candidate_type: str
    source_artifact: str
    producer: str
    evidence_class: str
    claim_boundary: str
    allowed_use: str
    blocked_use: str
    required_next_gate: str
    v4_context_binding: str
    review_note: str
    missing_artifact: bool = False


DEFAULT_CANDIDATE_SPECS: tuple[CandidateSpec, ...] = (
    CandidateSpec(
        register_row_id="G2CTX-TPD-SOURCE-001",
        candidate_type="COMSOL transported-position context candidate",
        source_artifact=(
            "roadmap/TRANSPORTED_POSITION_SOURCE_SMOKE_COMBINED_RETRY3_20260621.csv"
        ),
        producer="COMSOL",
        evidence_class="transported_position_source_smoke_context_only",
        claim_boundary="transport_distribution_context_only_not_detection",
        allowed_use="Gate2 context candidate review and route/bin alignment preflight only",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate=(
            "formal Gate2 export with NODI route/view/diameter/bin binding; no weighting"
        ),
        v4_context_binding="not_v4_bound_transport_context",
        review_note="TPD source exists, but it is coarse edge4 context and has no NODI view binding.",
    ),
    CandidateSpec(
        register_row_id="G2CTX-TPD-ALIGN-002",
        candidate_type="COMSOL transported-position context candidate",
        source_artifact="roadmap/TPD_TO_NODI_BRIDGE_ALIGNMENT_TABLE_20260621.csv",
        producer="COMSOL",
        evidence_class="tpd_to_nodi_schema_alignment_context_only",
        claim_boundary="transport_distribution_context_only_not_detection",
        allowed_use="Gate2 context candidate review of coarse-to-fine bin alignment only",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate=(
            "NODI PRS artifact ingestion recheck plus explicit context-only Gate2 acceptance"
        ),
        v4_context_binding="not_v4_bound_transport_context",
        review_note="Schema-compatible alignment, but no scalar chi or q_ch use is authorized.",
    ),
    CandidateSpec(
        register_row_id="G2CTX-QCH-MISSING-003",
        candidate_type="q_ch / flow split candidate",
        source_artifact="UNAVAILABLE_FORMAL_QCH_FLOW_SPLIT_SIDECAR",
        producer="COMSOL",
        evidence_class="missing_formal_gate2_qch_flow_split_export",
        claim_boundary="no_qch_or_flow_split_artifact_available_for_nodi_gate2",
        allowed_use="none beyond blocked-register documentation",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate="COMSOL formal Gate2 q_ch/flow split export package",
        v4_context_binding="not_v4_bound_qch_missing",
        review_note="Reviewed COMSOL packets say qch_reference_status=not_used.",
        missing_artifact=True,
    ),
    CandidateSpec(
        register_row_id="G2CTX-CHI-AGG-004",
        candidate_type="TPD/PRS context proxy candidate",
        source_artifact="roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv",
        producer="COMSOL",
        evidence_class="threshold_crossing_fraction_proxy_context_only",
        claim_boundary="chi_context_proxy_not_calibrated_not_detection",
        allowed_use="Gate2 context proxy review only; no scalar promotion",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate=(
            "NODI-side Gate2 context-only review with blocked-grain disposition"
        ),
        v4_context_binding="not_v4_bound_chi_context_proxy",
        review_note="Context proxy rows keep NODI views and weighting bases separate.",
    ),
    CandidateSpec(
        register_row_id="G2CTX-CHI-BIN-005",
        candidate_type="TPD/PRS context proxy candidate",
        source_artifact="roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv",
        producer="COMSOL",
        evidence_class="threshold_crossing_fraction_proxy_bin_context_only",
        claim_boundary="chi_context_proxy_not_calibrated_not_detection",
        allowed_use="Gate2 bin-level context proxy review only; no selected-chi promotion",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate=(
            "explicit coarse edge4 to PRS edge20 review before any future formula use"
        ),
        v4_context_binding="not_v4_bound_chi_context_proxy",
        review_note="Bin rows map 4 TPD bins to PRS edge20 groups; this is not direct PRS occupancy.",
    ),
    CandidateSpec(
        register_row_id="G2CTX-LQ-ANCHOR-006",
        candidate_type="local-Q hydraulic anchor / event-tree diagnostic candidate",
        source_artifact=(
            "roadmap/"
            "EV_PBS_ENTRANCE_LOCAL_Q_EFFECTIVE_APERTURE_LOCAL_Q_EVENT_TREE_BRIDGE_INPUT_20260623.csv"
        ),
        producer="COMSOL",
        evidence_class="local_q_hydraulic_anchor_context",
        claim_boundary="simulation_only_local_hydraulic_anchor",
        allowed_use="review-only hydraulic context; no NODI scalar promotion",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate="separate local-Q/NODI binding review if hydraulic context is needed",
        v4_context_binding="not_v4_bound_local_q_anchor",
        review_note="Hydraulic anchor lacks NODI lambda/view/bin binding.",
    ),
    CandidateSpec(
        register_row_id="G2CTX-LQ-SCREEN-007",
        candidate_type="local-Q hydraulic anchor / event-tree diagnostic candidate",
        source_artifact="roadmap/EV_PBS_LOCAL_Q_EVENT_TREE_BRIDGE_SCREENING_RESULTS_20260623.csv",
        producer="COMSOL/Python diagnostic",
        evidence_class="event_tree_route_shift_diagnostic_not_result",
        claim_boundary="screening_only_not_calibrated_event_tree",
        allowed_use="review-only event-tree diagnostic context",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate="calibrated event-data gate before any event-tree result claim",
        v4_context_binding="not_v4_bound_event_tree_screening",
        review_note="Rows are marked not_a_result and cannot become NODI production input.",
    ),
    CandidateSpec(
        register_row_id="G2CTX-LQ-BRANCH-008",
        candidate_type="local-Q hydraulic anchor / event-tree diagnostic candidate",
        source_artifact="roadmap/EV_PBS_LOCAL_Q_BRANCH_ENVELOPE_REVIEW_GATE_BRANCH_DECISIONS_20260624.csv",
        producer="COMSOL/Python diagnostic",
        evidence_class="branch_envelope_review_gate_context",
        claim_boundary="screening_main_trunk_not_calibrated_result",
        allowed_use="review-only branch-envelope context",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate="separate physics-contract gate before default event-tree use",
        v4_context_binding="not_v4_bound_branch_envelope",
        review_note="Packet explicitly blocks calibrated route winner and detection probability.",
    ),
    CandidateSpec(
        register_row_id="G2CTX-V4-CONTRACT-009",
        candidate_type="V4 sample/surface review-only context",
        source_artifact="roadmap/EV_PBS_SAMPLE_SURFACE_CANONICAL_CONTRACT_V4_20260627.json",
        producer="COMSOL context governance",
        evidence_class="v4_descriptor_closure_contract_review_only",
        claim_boundary=(
            "literature_derived_descriptor_closure_scenario_only_not_project_measurement_or_calibration"
        ),
        allowed_use="review-only V4 claim-boundary context",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate="V4-bound Gate2 review package with all production flags false",
        v4_context_binding="v4_assumption_set_hash_pinned_review_only_no_production",
        review_note="Canonical V4 contract is descriptor-only and not NODI production input.",
    ),
    CandidateSpec(
        register_row_id="G2CTX-V4-SIDECAR-010",
        candidate_type="V4 sample/surface review-only context",
        source_artifact="roadmap/EV_PBS_V4_NON_NANO_NODI_REVIEW_CONTEXT_SIDECAR_ROWS_20260627.csv",
        producer="COMSOL context governance",
        evidence_class="v4_nodi_review_context_sidecar_review_only",
        claim_boundary="review_context_only_not_production_ingestion",
        allowed_use="review-only NODI-facing V4 context loading",
        blocked_use=COMMON_BLOCKED_USE,
        required_next_gate="separate V4 production-ingestion authorization, currently blocked",
        v4_context_binding="v4_assumption_set_hash_pinned_review_only_no_production",
        review_note="Sidecar rows carry production/count/optical/runtime/COMSOL flags false.",
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a NODI-side Gate2 COMSOL context candidate ingestion preflight "
            "register. This writes no JRC, performs no q_ch weighting, and computes "
            "no yield, winner, or detection probability."
        )
    )
    parser.add_argument(
        "--confirm-gate2-context-preflight",
        action="store_true",
        help="Confirm writing context-only Gate2 preflight sidecars.",
    )
    parser.add_argument("--comsol-root", type=Path, default=DEFAULT_COMSOL_ROOT)
    parser.add_argument("--prs", type=Path, default=DEFAULT_PRS)
    parser.add_argument("--eas", type=Path, default=DEFAULT_EAS)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser


def build_gate2_context_candidate_payload(
    *,
    prs_rows: Sequence[Mapping[str, Any]],
    eas_rows: Sequence[Mapping[str, Any]],
    comsol_root: Path,
    prs_path: Path,
    eas_path: Path,
    candidate_specs: Sequence[CandidateSpec] = DEFAULT_CANDIDATE_SPECS,
) -> dict[str, Any]:
    prs_grains = _prs_grains(prs_rows)
    eas_route_views = {
        (_value(row, "route_id_nodi"), _value(row, "NODI_view")) for row in eas_rows
    }
    register_rows: list[dict[str, Any]] = []
    blocked_grain_rows: list[dict[str, Any]] = []

    for spec in candidate_specs:
        rows, row_count, digest = _load_candidate_rows(comsol_root, spec)
        alignment_rows = _build_blocked_grain_rows(
            spec=spec,
            rows=rows,
            prs_grains=prs_grains,
            eas_route_views=eas_route_views,
        )
        matched_count = _count_matched_grains(rows, prs_grains)
        blocked_grain_rows.extend(alignment_rows)
        register_rows.append(
            _build_register_row(
                spec=spec,
                rows=rows,
                row_count=row_count,
                digest=digest,
                matched_grain_count=matched_count,
                blocked_grain_count=len(alignment_rows),
            )
        )

    schema_rows = gate2_context_candidate_schema_rows()
    issues = validate_gate2_context_candidate_register_rows(register_rows)
    issues.extend(validate_gate2_blocked_grain_rows(blocked_grain_rows))
    v4_context = default_comsol_v4_readonly_context(
        v4_scope=COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT,
        source_artifact=(
            "comsol test/comsol_ev_pbs_bonded_cross_junction/roadmap/"
            "EV_PBS_SAMPLE_SURFACE_CANONICAL_CONTRACT_V4_20260627.json"
        ),
    )
    issues.extend(
        f"GATE2-V4: {issue}" for issue in validate_comsol_v4_readonly_context(v4_context)
    )
    status = PASS_STATUS if not issues else BLOCKED_STATUS
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": status,
        "allowed_scope": "Gate2 context candidate ingestion preflight only",
        "prs_path": str(prs_path),
        "prs_sha256": sha256_file(prs_path) if prs_path.exists() else "",
        "prs_row_count": len(prs_rows),
        "eas_path": str(eas_path),
        "eas_sha256": sha256_file(eas_path) if eas_path.exists() else "",
        "eas_row_count": len(eas_rows),
        "register_row_count": len(register_rows),
        "blocked_grain_row_count": len(blocked_grain_rows),
        "candidate_status_counts": dict(
            Counter(row["candidate_status"] for row in register_rows)
        ),
        "candidate_type_counts": dict(Counter(row["candidate_type"] for row in register_rows)),
        "blocked_alignment_status_counts": dict(
            Counter(row["alignment_status"] for row in blocked_grain_rows)
        ),
        "comsol_run_performed": False,
        "nodi_rerun_performed": False,
        "joint_route_class_generated": False,
        "q_ch_weighting_performed": False,
        "q_ch_eta_computed": False,
        "yield_computed": False,
        "winner_selected": False,
        "detection_probability_computed": False,
        "true_W_eff_claimed": False,
        "measured_geometry_claimed": False,
        "wet_pass_probability_computed": False,
        "clogging_rate_computed": False,
        "comsol_v4_context": v4_context,
        "issues": issues,
        "register_rows": register_rows,
        "blocked_grain_rows": blocked_grain_rows,
        "schema_rows": schema_rows,
    }


def validate_gate2_context_candidate_payload(payload: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if payload.get("schema_version") != REPORT_SCHEMA_VERSION:
        issues.append("GATE2: report schema_version drifted")
    if payload.get("status") not in {PASS_STATUS, BLOCKED_STATUS}:
        issues.append("GATE2: invalid status")
    for field in (
        "comsol_run_performed",
        "nodi_rerun_performed",
        "joint_route_class_generated",
        "q_ch_weighting_performed",
        "q_ch_eta_computed",
        "yield_computed",
        "winner_selected",
        "detection_probability_computed",
        "true_W_eff_claimed",
        "measured_geometry_claimed",
        "wet_pass_probability_computed",
        "clogging_rate_computed",
    ):
        if payload.get(field) is not False:
            issues.append(f"GATE2: {field} must remain false")
    v4_context = payload.get("comsol_v4_context")
    if not isinstance(v4_context, Mapping):
        issues.append("GATE2: missing COMSOL V4 read-only context")
    else:
        issues.extend(
            f"GATE2-V4: {issue}" for issue in validate_comsol_v4_readonly_context(v4_context)
        )
    issues.extend(
        validate_gate2_context_candidate_register_rows(
            list(payload.get("register_rows", []))
        )
    )
    issues.extend(
        validate_gate2_blocked_grain_rows(list(payload.get("blocked_grain_rows", [])))
    )
    if payload.get("status") == PASS_STATUS and issues:
        issues.append("GATE2: PASS status cannot carry validation issues")
    return issues


def validate_gate2_context_candidate_register_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["GATE2-REG: no register rows supplied"]
    for row_index, row in enumerate(rows, start=1):
        for field in REGISTER_FIELDS:
            if field not in row:
                issues.append(f"row {row_index} GATE2-REG-S01: missing {field}")
        for field in row:
            normalized = field.lower()
            for forbidden in FORBIDDEN_OUTPUT_FIELDS:
                if forbidden in normalized:
                    issues.append(
                        f"row {row_index} GATE2-REG-S02: forbidden output field {field}"
                    )
                    break
        if row.get("schema_version") != SCHEMA_VERSION:
            issues.append(f"row {row_index} GATE2-REG-S03: schema_version drifted")
        if row.get("candidate_status") not in ALLOWED_CANDIDATE_STATUSES:
            issues.append(f"row {row_index} GATE2-REG-S04: invalid candidate_status")
        digest = str(row.get("sha256", ""))
        if digest != MISSING_SHA and not SHA256_RE.match(digest):
            issues.append(f"row {row_index} GATE2-REG-S05: sha256 is not valid")
        try:
            row_count = int(str(row.get("row_count", "")))
        except ValueError:
            issues.append(f"row {row_index} GATE2-REG-S06: row_count is not integer")
        else:
            if row_count < 0:
                issues.append(f"row {row_index} GATE2-REG-S06: row_count is negative")
        allowed_use = str(row.get("allowed_use", "")).lower().replace("_", " ")
        for term in FORBIDDEN_ALLOWED_USE_TERMS:
            if term in allowed_use:
                issues.append(
                    f"row {row_index} GATE2-REG-S07: allowed_use promotes {term}"
                )
        if "production" in str(row.get("v4_context_binding", "")).lower():
            if "no_production" not in str(row.get("v4_context_binding", "")).lower():
                issues.append(
                    f"row {row_index} GATE2-REG-S08: V4 production promotion is forbidden"
                )
        if str(row.get("nodi_production_ingestion_allowed", "")).lower() == "true":
            issues.append(
                f"row {row_index} GATE2-REG-S09: nodi_production_ingestion_allowed true"
            )
    return issues


def validate_gate2_blocked_grain_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        status = str(row.get("alignment_status", ""))
        if not (status.startswith("BLOCKED_") or status.startswith("REVIEW_ONLY_")):
            issues.append(
                f"row {row_index} GATE2-GRAIN-S01: mismatch row must be blocked/review-only"
            )
        if not row.get("required_next_gate"):
            issues.append(f"row {row_index} GATE2-GRAIN-S02: missing required_next_gate")
    return issues


def gate2_context_candidate_schema_rows() -> list[dict[str, str]]:
    descriptions = {
        "source_artifact": "COMSOL or blocked source artifact path, relative to COMSOL root when present",
        "sha256": "SHA256 of source_artifact or MISSING_UNTIL_FORMAL_GATE2_EXPORT",
        "row_count": "Source row count; JSON contracts count as 1; missing blocked rows count as 0",
        "producer": "Producer or governance owner",
        "evidence_class": "Context evidence class; never production physics promotion",
        "route_key": "NODI route key if bound; otherwise explicit no-route/review marker",
        "diameter_basis": "Diameter grain or explicit non-diameter/review basis",
        "bin_basis": "Bin or context basis; coarse bins must be explicit",
        "claim_boundary": "Claim ceiling carried from COMSOL packet or NODI register",
        "allowed_use": "Context-only or review-only use allowed before later gates",
        "blocked_use": "Forbidden interpretations and outputs",
        "required_next_gate": "Gate needed before any stronger use",
        "v4_context_binding": "V4 context binding status, if applicable",
    }
    return [
        {
            "field": field,
            "required": "true",
            "description": descriptions.get(field, "Gate2 candidate register control field"),
        }
        for field in REGISTER_FIELDS
    ]


def write_gate2_context_candidate_bundle(
    *,
    comsol_root: Path,
    prs_path: Path,
    eas_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_gate2_context_candidate_payload(
        prs_rows=read_csv_rows(prs_path),
        eas_rows=read_csv_rows(eas_path),
        comsol_root=comsol_root,
        prs_path=prs_path,
        eas_path=eas_path,
    )
    validation_issues = validate_gate2_context_candidate_payload(payload)
    if validation_issues:
        payload["issues"] = validation_issues
        payload["status"] = BLOCKED_STATUS

    register_path = output_dir / REGISTER_FILENAME
    blocked_path = output_dir / BLOCKED_GRAINS_FILENAME
    schema_path = output_dir / SCHEMA_FILENAME
    report_path = output_dir / REPORT_FILENAME
    report_md_path = output_dir / REPORT_MD_FILENAME

    write_csv_rows(register_path, payload["register_rows"])
    write_csv_rows(blocked_path, payload["blocked_grain_rows"])
    write_csv_rows(schema_path, payload["schema_rows"])
    _normalize_lf(register_path)
    _normalize_lf(blocked_path)
    _normalize_lf(schema_path)
    payload["register_csv"] = str(register_path)
    payload["register_csv_sha256"] = sha256_file(register_path)
    payload["blocked_grain_csv"] = str(blocked_path)
    payload["blocked_grain_csv_sha256"] = sha256_file(blocked_path)
    payload["schema_csv"] = str(schema_path)
    payload["schema_csv_sha256"] = sha256_file(schema_path)
    payload["report_path"] = str(report_path)
    payload["report_md_path"] = str(report_md_path)
    write_json_atomic(report_path, payload, sort_keys=True)
    _write_markdown_report(report_md_path, payload)
    payload["report_sha256"] = sha256_file(report_path)
    payload["report_md_sha256"] = sha256_file(report_md_path)
    return payload


def _load_candidate_rows(
    comsol_root: Path,
    spec: CandidateSpec,
) -> tuple[list[dict[str, str]], int, str]:
    if spec.missing_artifact:
        return [], 0, MISSING_SHA
    path = comsol_root / spec.source_artifact
    if path.suffix.lower() == ".csv":
        rows = read_csv_rows(path)
        return rows, len(rows), sha256_file(path)
    return [], 1, sha256_file(path)


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


def _build_register_row(
    *,
    spec: CandidateSpec,
    rows: Sequence[Mapping[str, Any]],
    row_count: int,
    digest: str,
    matched_grain_count: int,
    blocked_grain_count: int,
) -> dict[str, Any]:
    candidate_status = _candidate_status(spec, matched_grain_count, blocked_grain_count)
    return {
        "register_row_id": spec.register_row_id,
        "schema_version": SCHEMA_VERSION,
        "candidate_type": spec.candidate_type,
        "source_artifact": spec.source_artifact,
        "sha256": digest,
        "row_count": row_count,
        "producer": spec.producer,
        "evidence_class": spec.evidence_class,
        "route_key": _route_key_basis(rows, spec),
        "diameter_basis": _diameter_basis(rows, spec),
        "bin_basis": _bin_basis(rows, spec),
        "claim_boundary": spec.claim_boundary,
        "allowed_use": spec.allowed_use,
        "blocked_use": spec.blocked_use,
        "required_next_gate": spec.required_next_gate,
        "v4_context_binding": spec.v4_context_binding,
        "candidate_status": candidate_status,
        "grain_alignment_status": _grain_alignment_status(
            spec, matched_grain_count, blocked_grain_count
        ),
        "matched_grain_count": matched_grain_count,
        "blocked_grain_count": blocked_grain_count,
        "review_note": spec.review_note,
    }


def _candidate_status(
    spec: CandidateSpec,
    matched_grain_count: int,
    blocked_grain_count: int,
) -> str:
    if spec.missing_artifact:
        return "BLOCKED_MISSING_FORMAL_GATE2_EXPORT"
    if spec.candidate_type in REVIEW_ONLY_TYPES:
        return "REVIEW_ONLY_NOT_GATE2_INPUT"
    if matched_grain_count > 0 and blocked_grain_count > 0:
        return "GATE2_CANDIDATE_CONTEXT_ONLY_PARTIAL_GRAIN_MATCH"
    if matched_grain_count > 0 and blocked_grain_count == 0:
        return "GATE2_CANDIDATE_CONTEXT_ONLY_REVIEWABLE"
    if blocked_grain_count > 0:
        return "BLOCKED_ROUTE_DIAMETER_BIN_MISMATCH"
    return "GATE2_CANDIDATE_CONTEXT_ONLY_REVIEWABLE"


def _grain_alignment_status(
    spec: CandidateSpec,
    matched_grain_count: int,
    blocked_grain_count: int,
) -> str:
    if spec.missing_artifact:
        return "BLOCKED_NO_FORMAL_QCH_FLOW_SPLIT_ARTIFACT"
    if spec.candidate_type in REVIEW_ONLY_TYPES:
        return "REVIEW_ONLY_NO_NODI_ROUTE_DIAMETER_BIN_BINDING"
    if matched_grain_count > 0 and blocked_grain_count > 0:
        return "PARTIAL_MATCH_BLOCKED_GRAINS_REGISTERED"
    if matched_grain_count > 0:
        return "MATCHED_CONTEXT_ONLY_NO_WEIGHTING"
    if blocked_grain_count > 0:
        return "BLOCKED_ROUTE_DIAMETER_BIN_MISMATCH"
    return "REVIEW_ONLY_NO_EXPLICIT_GRAIN_BINDING"


def _build_blocked_grain_rows(
    *,
    spec: CandidateSpec,
    rows: Sequence[Mapping[str, Any]],
    prs_grains: set[tuple[str, str, str]],
    eas_route_views: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    if spec.missing_artifact:
        return [
            _blocked_row(
                spec,
                route_key="*",
                diameter_nm="*",
                nodi_view="*",
                bin_basis="*",
                status="BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT_EXPORT",
                reason="No formal q_ch / flow split sidecar is present in reviewed packets.",
            )
        ]
    if spec.candidate_type in REVIEW_ONLY_TYPES:
        return [
            _blocked_row(
                spec,
                route_key=_route_key_basis(rows, spec),
                diameter_nm=_diameter_basis(rows, spec),
                nodi_view="UNBOUND_REVIEW_ONLY",
                bin_basis=_bin_basis(rows, spec),
                status="REVIEW_ONLY_NO_NODI_ROUTE_DIAMETER_BIN_BINDING",
                reason="Context lacks exact NODI route/diameter/view/bin production binding.",
            )
        ]

    blocked: list[dict[str, Any]] = []
    for route_key, diameter_nm, nodi_view, bin_basis in sorted(_explicit_grains(rows)):
        if (route_key, diameter_nm, nodi_view) not in prs_grains:
            blocked.append(
                _blocked_row(
                    spec,
                    route_key=route_key,
                    diameter_nm=diameter_nm,
                    nodi_view=nodi_view,
                    bin_basis=bin_basis,
                    status="BLOCKED_MISSING_PRS_ROUTE_DIAMETER_VIEW_GRAIN",
                    reason="COMSOL context grain is absent from current NODI production PRS.",
                )
            )
        if (route_key, nodi_view) not in eas_route_views:
            blocked.append(
                _blocked_row(
                    spec,
                    route_key=route_key,
                    diameter_nm=diameter_nm,
                    nodi_view=nodi_view,
                    bin_basis=bin_basis,
                    status="BLOCKED_MISSING_EAS_ROUTE_VIEW_GRAIN",
                    reason="COMSOL context grain lacks current NODI production EAS route/view.",
                )
            )
        if "edge4" in bin_basis or "prs_edge20_group" in bin_basis:
            blocked.append(
                _blocked_row(
                    spec,
                    route_key=route_key,
                    diameter_nm=diameter_nm,
                    nodi_view=nodi_view,
                    bin_basis=bin_basis,
                    status="REVIEW_ONLY_COARSE_TO_FINE_BIN_GROUP_NOT_DIRECT_PRS_BIN",
                    reason="Coarse TPD bins require explicit review before formula use.",
                )
            )

    if not blocked and not _explicit_grains(rows):
        for route_key, diameter_nm, bin_basis in sorted(_route_diameter_without_view(rows)):
            blocked.append(
                _blocked_row(
                    spec,
                    route_key=route_key,
                    diameter_nm=diameter_nm,
                    nodi_view="UNBOUND",
                    bin_basis=bin_basis,
                    status="REVIEW_ONLY_MISSING_NODI_VIEW_BINDING",
                    reason="COMSOL context has route/diameter context but no NODI_view grain.",
                )
            )
            if not any(
                route_key == prs_route and diameter_nm == prs_diameter
                for prs_route, prs_diameter, _view in prs_grains
            ):
                blocked.append(
                    _blocked_row(
                        spec,
                        route_key=route_key,
                        diameter_nm=diameter_nm,
                        nodi_view="UNBOUND",
                        bin_basis=bin_basis,
                        status="BLOCKED_MISSING_PRS_ROUTE_DIAMETER_GRAIN",
                        reason="COMSOL route/diameter context is absent from current PRS.",
                    )
                )
    return blocked


def _blocked_row(
    spec: CandidateSpec,
    *,
    route_key: str,
    diameter_nm: str,
    nodi_view: str,
    bin_basis: str,
    status: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "register_row_id": spec.register_row_id,
        "candidate_type": spec.candidate_type,
        "source_artifact": spec.source_artifact,
        "route_key": route_key,
        "diameter_nm": diameter_nm,
        "NODI_view": nodi_view,
        "bin_basis": bin_basis,
        "alignment_status": status,
        "required_next_gate": spec.required_next_gate,
        "reason": reason,
    }


def _count_matched_grains(
    rows: Sequence[Mapping[str, Any]],
    prs_grains: set[tuple[str, str, str]],
) -> int:
    return sum(1 for grain in _explicit_grains(rows) if grain[:3] in prs_grains)


def _prs_grains(rows: Sequence[Mapping[str, Any]]) -> set[tuple[str, str, str]]:
    return {
        (_value(row, "route_id_nodi"), _value(row, "diameter_nm"), _value(row, "NODI_view"))
        for row in rows
        if _value(row, "route_id_nodi")
        and _value(row, "diameter_nm")
        and _value(row, "NODI_view")
    }


def _explicit_grains(rows: Sequence[Mapping[str, Any]]) -> set[tuple[str, str, str, str]]:
    grains: set[tuple[str, str, str, str]] = set()
    for row in rows:
        route_key = _value(row, "route_id_nodi")
        diameter = _value(row, "diameter_nm")
        view = _value(row, "NODI_view")
        if route_key and diameter and view:
            grains.add((route_key, diameter, view, _row_bin_basis(row)))
    return grains


def _route_diameter_without_view(
    rows: Sequence[Mapping[str, Any]],
) -> set[tuple[str, str, str]]:
    grains: set[tuple[str, str, str]] = set()
    for row in rows:
        route_key = _route_key_from_row(row)
        diameter = _value(row, "diameter_nm")
        if route_key and diameter:
            grains.add((route_key, diameter, _row_bin_basis(row)))
    return grains


def _route_key_basis(rows: Sequence[Mapping[str, Any]], spec: CandidateSpec) -> str:
    if spec.missing_artifact:
        return "MISSING_QCH_FLOW_SPLIT_ROUTE_KEY"
    values = sorted({_route_key_from_row(row) for row in rows if _route_key_from_row(row)})
    if values:
        return ";".join(values)
    if spec.candidate_type == "V4 sample/surface review-only context":
        return "V4_REVIEW_CONTEXT_UNBOUND_TO_NODI_ROUTE"
    return "UNBOUND_REVIEW_ONLY"


def _diameter_basis(rows: Sequence[Mapping[str, Any]], spec: CandidateSpec) -> str:
    if spec.missing_artifact:
        return "MISSING_QCH_FLOW_SPLIT_DIAMETER_BASIS"
    values = sorted({_value(row, "diameter_nm") for row in rows if _value(row, "diameter_nm")})
    if values:
        return ";".join(values)
    if any(_value(row, "effective_aperture_category") for row in rows):
        return "effective_aperture_category_not_particle_diameter"
    return "not_diameter_binned"


def _bin_basis(rows: Sequence[Mapping[str, Any]], spec: CandidateSpec) -> str:
    if spec.missing_artifact:
        return "MISSING_QCH_FLOW_SPLIT_BIN_BASIS"
    if any(_value(row, "prs_bin_count") for row in rows):
        return "TPD_edge4_to_PRS_edge20_group_context"
    for field in ("tpd_bin_schema", "bin_schema", "context_family", "effective_aperture_category"):
        values = sorted({_value(row, field) for row in rows if _value(row, field)})
        if values:
            return ";".join(values)
    return "not_position_binned"


def _row_bin_basis(row: Mapping[str, Any]) -> str:
    if _value(row, "prs_bin_count"):
        return f"prs_edge20_group_count_{_value(row, 'prs_bin_count')}"
    if _value(row, "tpd_bin_schema"):
        return f"{_value(row, 'tpd_bin_schema')}_edge4_context"
    if _value(row, "bin_schema"):
        return f"{_value(row, 'bin_schema')}_edge4_context"
    return "not_position_binned"


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
        if match:
            return f"W{match.group('width')}/D{match.group('depth')}_NO_NODI_LAMBDA"
    width = _value(row, "W_nominal_nm")
    depth = _value(row, "D_nm")
    if width and depth:
        return f"W{width}/D{depth}_NO_NODI_LAMBDA"
    return ""


def _value(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field, "")
    if value is None:
        return ""
    return str(value).strip()


def _write_markdown_report(path: Path, payload: Mapping[str, Any]) -> None:
    lines = [
        "# NODI/COMSOL Gate2 Context Candidate Preflight Report",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This is a context-candidate register only. It writes no `JOINT_ROUTE_CLASS`,",
        "performs no q_ch weighting or q_ch*eta, and computes no yield, winner,",
        "detection probability, wet pass probability, or clogging rate.",
        "",
        "## Counts",
        "",
        f"- register rows: {payload['register_row_count']}",
        f"- blocked/review grain rows: {payload['blocked_grain_row_count']}",
        f"- candidate status counts: `{payload['candidate_status_counts']}`",
        f"- blocked alignment counts: `{payload['blocked_alignment_status_counts']}`",
        "",
        "## Outputs",
        "",
        f"- register: `{payload.get('register_csv', '')}`",
        f"- blocked grains: `{payload.get('blocked_grain_csv', '')}`",
        f"- schema: `{payload.get('schema_csv', '')}`",
        "",
        "## Issues",
        "",
    ]
    issues = list(payload.get("issues", []))
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- none")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_gate2_context_preflight:
        parser.error(
            "refusing to write Gate2 context candidate sidecars without "
            "--confirm-gate2-context-preflight"
        )

    payload = write_gate2_context_candidate_bundle(
        comsol_root=args.comsol_root,
        prs_path=args.prs,
        eas_path=args.eas,
        output_dir=args.output_dir,
    )
    print(f"NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_PREFLIGHT: {payload['status']}")
    print(f"report_path: {payload['report_path']}")
    print(f"report_sha256: {payload['report_sha256']}")
    print(f"register_csv: {payload['register_csv']}")
    print(f"register_csv_sha256: {payload['register_csv_sha256']}")
    print(f"blocked_grain_csv: {payload['blocked_grain_csv']}")
    print(f"schema_csv: {payload['schema_csv']}")
    for issue in payload["issues"]:
        print(f"- issue: {issue}")
    return 0 if payload["status"] == PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
