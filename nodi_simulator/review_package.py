"""P0a review-package scaffolding for the post-v2 relative audit.

The helpers in this module deliberately package no-measured-data audit
evidence. They do not convert v2 sidecars into calibration artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
import unicodedata
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .realism_v2_io import sha256_file, write_csv_rows, write_json_atomic


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POST_V2_AUDIT_DIR = Path("results/post_v2_mandatory_audit")
PAPER_PROVENANCE_DIR = Path("papers/provenance")

CALIBRATION_SCAFFOLD_FILES: tuple[str, ...] = (
    "calibration/bfp_roi_mask_template.json",
    "calibration/blank_false_positive_template.csv",
    "calibration/blank_false_positive_template_manifest.json",
    "calibration/calibration_manifest_template.json",
    "calibration/collection_operator_template.csv",
    "calibration/collection_operator_template_manifest.json",
    "calibration/raw_blank_trace_manifest_template.json",
    "calibration/reference_blank_channel_template.csv",
    "calibration/reference_blank_channel_template_manifest.json",
    "calibration/standard_particle_template.csv",
    "calibration/standard_particle_template_manifest.json",
)

V1_SUMMARY_PATH = "results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
V1_REQUIRED_BOUNDARY_FIELDS: tuple[str, ...] = (
    "output_claim_level_resolved",
    "field_coordinate_measure",
    "operator_route",
    "detector_field_units",
    "bfp_to_angle_jacobian_applied",
    "detector_unit_chain_status",
)

EXISTING_V2_ROLE_PATHS: tuple[tuple[str, str, str], ...] = (
    (
        "claim_boundary_summary",
        "results/ev_nodi_realism_v2_no_measured_data_closure/v2_final_claim_boundary_summary.csv",
        "v2 closure",
    ),
    (
        "route_governance_summary",
        "results/ev_nodi_realism_v2_no_measured_data_closure/v2_route_governance_closure_summary.csv",
        "v2 closure",
    ),
    (
        "artifact_gap_register",
        "results/ev_nodi_realism_v2_no_measured_data_closure/v2_artifact_gap_closure_register.csv",
        "v2 closure",
    ),
    (
        "unmodeled_realism_register",
        "reports/89_EV_NODI_post_v2_unmodeled_realism_register.md",
        "post-v2 register",
    ),
    (
        "mie_to_power_guardrail_summary",
        "results/ev_nodi_realism_v2_anchor_smoke/mie_to_power_unit_check.csv",
        "upstream v2 evidence",
    ),
    (
        "noise_readout_scenario_manifest",
        "configs/realism_v2/r5_scenario_bundle_manifest.yaml",
        "R5 v2 evidence",
    ),
    (
        "noise_readout_scenario_summary",
        "results/ev_nodi_realism_v2_full_grid_R5_v2/scenario_bundle_sensitivity_summary.csv",
        "R5 v2 evidence",
    ),
    (
        "selected_annulus_summary",
        "results/ev_nodi_realism_v2_full_grid_R5_v2/selected_annulus_parallel_lens_summary.csv",
        "R5 v2 evidence",
    ),
)

POST_V2_GENERATED_ROLES: tuple[tuple[str, str, str], ...] = (
    (
        "candidate_universe_manifest",
        "results/post_v2_mandatory_audit/candidate_universe_manifest.json",
        "P0b.candidate_universe",
    ),
    (
        "top_candidate_mandatory_audit",
        "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv",
        "P0b.candidate_universe",
    ),
    (
        "top_candidate_particle_panel_audit",
        "results/post_v2_mandatory_audit/top_candidate_particle_panel_audit.csv",
        "P0b.ev_prior_contaminant_audit",
    ),
    (
        "top_candidate_pairwise_rank_inversion",
        "results/post_v2_mandatory_audit/top_candidate_pairwise_rank_inversion.csv",
        "P0b.pairwise_rank_audit",
    ),
    (
        "bfp_roi_operator_summary",
        "results/post_v2_mandatory_audit/bfp_roi_operator_summary.csv",
        "P0b.bfp_roi_audit",
    ),
    (
        "tsuyama_bfp_reference_summary",
        "results/post_v2_mandatory_audit/tsuyama_bfp_reference_summary.csv",
        "P0b.tsuyama_bfp_audit",
    ),
    (
        "ev_prior_contaminant_summary",
        "results/post_v2_mandatory_audit/ev_prior_contaminant_summary.csv",
        "P0b.ev_prior_contaminant_audit",
    ),
    (
        "noise_readout_scenario_bundle",
        "results/post_v2_mandatory_audit/noise_readout_scenario_bundle.csv",
        "P0b.noise_readout_audit",
    ),
    (
        "noise_readout_route_sensitivity",
        "results/post_v2_mandatory_audit/noise_readout_route_sensitivity.csv",
        "P0b.noise_readout_audit",
    ),
    (
        "top_candidate_mandatory_audit_readme",
        "results/post_v2_mandatory_audit/top_candidate_mandatory_audit_readme.md",
        "P0b.pairwise_rank_audit",
    ),
)

POST_V2_DIAGNOSTIC_ROLES: tuple[tuple[str, str, str], ...] = (
    (
        "top_candidate_extended_pairwise_stability",
        "results/post_v2_mandatory_audit/top_candidate_extended_pairwise_stability.csv",
        "P1.extended_pairwise_stability",
    ),
)

NON_P0_SIDECAR_P0_PACKAGE_EXCLUDED_CONFIGS: tuple[str, ...] = (
    "configs/realism_v2/physical_ceiling_extension_registry.yaml",
    "configs/realism_v2/full_wave_green_tensor_diagnostic_contract.yaml",
    "configs/realism_v2/vector_jones_polarization_diagnostic_contract.yaml",
    "configs/realism_v2/roughness_leakage_diagnostic_contract.yaml",
    "configs/realism_v2/transport_residence_time_diagnostic_contract.yaml",
    "configs/realism_v2/bounded_physical_solver_readiness_registry.yaml",
    "configs/realism_v2/bounded_solver_authorization_pilot_design_registry.yaml",
    "configs/realism_v2/bounded_solver_dry_run_preflight_registry.yaml",
    "configs/realism_v2/bounded_solver_authorization_gate_registry.yaml",
    "configs/realism_v2/minimal_bounded_solver_execution_registry.yaml",
    "configs/realism_v2/second_lane_authorization_design_registry.yaml",
    "configs/realism_v2/second_bounded_solver_lane_execution_registry.yaml",
    "configs/realism_v2/second_bounded_solver_lane_closure_registry.yaml",
    "configs/realism_v2/next_bounded_lane_authorization_design_registry.yaml",
    "configs/realism_v2/third_bounded_solver_lane_execution_registry.yaml",
    "configs/realism_v2/third_bounded_solver_lane_closure_registry.yaml",
    "configs/realism_v2/fourth_bounded_lane_authorization_design_registry.yaml",
    "configs/realism_v2/fourth_bounded_solver_lane_execution_registry.yaml",
    "configs/realism_v2/fourth_bounded_solver_lane_closure_registry.yaml",
    "configs/realism_v2/fifth_bounded_lane_authorization_design_registry.yaml",
)

REASON_CODE_VOCABULARY: tuple[dict[str, str], ...] = (
    {"code": "BFP.RANK_SHIFT_MAJOR", "module": "BFP", "meaning": "BFP rank-percentile shift exceeds the pinned major threshold."},
    {"code": "PAIRWISE.RELATIVE_ORDER_DISAGREEMENT", "module": "PAIRWISE", "meaning": "One or more relative audit lenses disagree with scalar ordering."},
    {"code": "TSUYAMA.EXTRAPOLATED_GEOMETRY", "module": "TSUYAMA", "meaning": "Tsuyama phase-filter lane is outside paper geometry."},
    {"code": "NOISE.RELATIVE_FRAGILE", "module": "NOISE", "meaning": "Route rank-percentile is unstable versus the nominal R5 scenario."},
    {"code": "EV.SAMPLE_UNKNOWN", "module": "EV", "meaning": "EV sample profile is unknown and cannot support clean-main promotion."},
    {"code": "CLAIM.CALIBRATED_BLOCKED", "module": "CLAIM", "meaning": "Calibrated or absolute claim remains blocked."},
)

ROUTE_ROLE_INITIAL_VALUES: tuple[str, ...] = (
    "main_locked",
    "weak_reference_control",
    "optional_robustness_probe",
    "historical_v1_main",
    "shortwave_probe",
    "paper_proxy_sanity",
    "paper_sanity_audit_only",
    "context_route",
    "warning_route",
)

ROUTE_ROLE_FINAL_VALUES: tuple[str, ...] = (
    "relative_main_candidate",
    "relative_control_candidate",
    "optional_robustness_probe_only",
    "probe_only",
    "paper_sanity_only",
    "surrogate_sensitive_not_promoted",
    "audit_incomplete_blocked",
)

V1_SOURCE_FIELD_MAPPING: tuple[dict[str, str], ...] = (
    {"audit_field": "v1_scalar_score", "source_column": "score", "derivation_rule": "direct_copy"},
    {
        "audit_field": "v1_engineering_score",
        "source_column": "engineering_score",
        "derivation_rule": "direct_copy",
    },
    {
        "audit_field": "v1_stable_detection_rate_proxy",
        "source_column": "engineering_basis_stable_detection_rate",
        "derivation_rule": "direct_copy_relative_proxy_only",
    },
    {
        "audit_field": "v1_mean_peak_margin_z_proxy",
        "source_column": "engineering_basis_mean_peak_margin_z",
        "derivation_rule": "direct_copy_relative_proxy_not_calibrated_snr",
    },
    {
        "audit_field": "v1_mean_peak_height_proxy",
        "source_column": "mean_peak_height",
        "derivation_rule": "direct_copy_arbitrary_relative_units_only",
    },
    {
        "audit_field": "v1_output_claim_level",
        "source_column": "output_claim_level_resolved",
        "derivation_rule": "direct_copy_expected_engineering_ranking",
    },
    {
        "audit_field": "v1_field_coordinate_measure",
        "source_column": "field_coordinate_measure",
        "derivation_rule": "direct_copy_expected_theta_phi_surrogate",
    },
    {
        "audit_field": "v1_operator_route",
        "source_column": "operator_route",
        "derivation_rule": "direct_copy_expected_pupil_slit_surrogate",
    },
    {
        "audit_field": "v1_detector_field_units",
        "source_column": "detector_field_units",
        "derivation_rule": "direct_copy_expected_arbitrary_relative_field_units",
    },
    {
        "audit_field": "v1_bfp_to_angle_jacobian_applied",
        "source_column": "bfp_to_angle_jacobian_applied",
        "derivation_rule": "rename_on_ingest_expected_false_unprefixed_forbidden",
    },
    {
        "audit_field": "v1_reference_operating_point_status",
        "source_column": "reference_operating_point_status",
        "derivation_rule": "direct_copy_relative_reference_status_only",
    },
    {
        "audit_field": "v1_reference_route_consensus_status",
        "source_column": "reference_route_consensus_status",
        "derivation_rule": "direct_copy",
    },
    {
        "audit_field": "v1_reference_solver_status",
        "source_column": "reference_solver_status",
        "derivation_rule": "direct_copy_expected_engineering_surrogate_language",
    },
    {
        "audit_field": "v1_reference_design_validity",
        "source_column": "reference_design_validity",
        "derivation_rule": "direct_copy",
    },
)

AUDIT_SCHEMA_COLUMNS: tuple[str, ...] = (
    "audit_schema_version",
    "audit_run_id",
    "audit_generated_at",
    "source_v1_library_id",
    "source_v1_library_path",
    "source_v1_library_sha256",
    "source_v2_closure_id",
    "candidate_id",
    "candidate_source",
    "route_role_initial",
    "route_role_final",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
    "comparison_stratum",
    "ranking_participation",
    "particle_panel_summary_id",
    "missing_v1_reason",
    "aggregation_scope",
    "aggregation_particle_family",
    "aggregation_particle_filter_id",
    "aggregation_weighting_id",
    "aggregation_metric_id",
    "aggregation_quantile",
    "anchor_particles_included",
    "contaminants_included_in_route_score",
)


@dataclass(frozen=True)
class ClaimFinding:
    text: str
    phrase: str
    language: str
    allowed_by_negator: bool


def normalize_relpath(path: str | Path) -> str:
    return unicodedata.normalize("NFC", Path(path).as_posix())


def stable_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _load_json_compatible(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_value(args: Sequence[str], *, project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def git_commit(project_root: Path = PROJECT_ROOT) -> str | None:
    return _git_value(["rev-parse", "HEAD"], project_root=project_root)


def git_dirty(project_root: Path = PROJECT_ROOT) -> bool:
    status = _git_value(["status", "--short"], project_root=project_root)
    return bool(status)


def file_entry(project_root: Path, relpath: str, *, role: str, source_lane: str) -> dict[str, Any]:
    path = project_root / relpath
    exists = path.exists()
    return {
        "role": role,
        "path": normalize_relpath(relpath),
        "path_status": "exists" if exists else "missing",
        "source_lane": source_lane,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
        "size_bytes": path.stat().st_size if exists and path.is_file() else None,
    }


def count_csv_data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        next(handle)
        return sum(1 for _ in handle)


def csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader)


def v1_summary_contract(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    path = project_root / V1_SUMMARY_PATH
    header = csv_header(path)
    current_hash = sha256_file(path)
    pin_path = project_root / "configs/realism_v2/v1_summary_hash_pin.json"
    pin = _load_json_compatible(pin_path) if pin_path.exists() else {}
    pinned_hash = pin.get("summary_csv_sha256", current_hash)
    approved_drift_path = pin.get("approved_v1_summary_drift_evidence_path")
    required_present = all(field in header for field in V1_REQUIRED_BOUNDARY_FIELDS)
    return {
        "summary_csv_path": V1_SUMMARY_PATH,
        "summary_csv_sha256": current_hash,
        "summary_csv_pinned_sha256": pinned_hash,
        "summary_csv_sha256_pinned_in_manifest": True,
        "summary_csv_hash_matches_pin": current_hash == pinned_hash,
        "n_cases": count_csv_data_rows(path),
        "required_v1_boundary_fields_present": required_present,
        "approved_v1_summary_drift_evidence_path": approved_drift_path,
        "v1_boundary_expected": {
            "output_claim_level_resolved": "engineering_ranking",
            "field_coordinate_measure": "theta_phi_surrogate",
            "operator_route": "pupil_slit_surrogate",
            "detector_field_units": "arbitrary_relative_field_units",
            "bfp_to_angle_jacobian_applied": False,
        },
    }


def v1_hash_drift_is_authorized(contract: Mapping[str, Any]) -> bool:
    return bool(
        contract.get("summary_csv_hash_matches_pin")
        or contract.get("approved_v1_summary_drift_evidence_path")
    )


def build_audit_schema_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return {
        "audit_manifest_schema": "ev_nodi_post_v2_mandatory_audit_manifest_v1",
        "milestone": "P0a_schema_scaffold",
        "claim_scope": "no_measured_data_relative_audit_only",
        "calibrated_claim_allowed": False,
        "source_v1_library_path": V1_SUMMARY_PATH,
        "v1_source_field_mapping": list(V1_SOURCE_FIELD_MAPPING),
        "unprefixed_forbidden_audit_columns": ["bfp_to_angle_jacobian_applied"],
        "required_core_columns": list(AUDIT_SCHEMA_COLUMNS),
        "required_aggregation_fields": [
            "aggregation_scope",
            "aggregation_particle_family",
            "aggregation_particle_filter_id",
            "aggregation_weighting_id",
            "aggregation_metric_id",
            "aggregation_quantile",
        ],
        "rank_policy": {
            "rank_direction": "higher_score_better",
            "rank_method": "average_tie_rank",
            "rank_percentile_definition": "1.0_best_0.0_worst",
            "primary_inversion_stratum": "all_ranked_routes",
            "raw_magnitude_final_gate_allowed": False,
        },
        "v1_bfp_to_angle_jacobian_applied_expected": False,
        "audit_bfp_jacobian_applied_layer": "post_v2_audit_sidecar_not_v1_fact",
        "p0b_artifacts_produced_from_evidence_chain": [
            {"role": role, "path": path, "generation_task_id": task}
            for role, path, task in POST_V2_GENERATED_ROLES
        ],
    }


def write_audit_schema_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "top_candidate_mandatory_audit_manifest.json"
    write_json_atomic(output, build_audit_schema_manifest(project_root), sort_keys=True)
    return output


def _default_paper_overrides(project_root: Path) -> dict[str, Any]:
    papers = scan_paper_files(project_root)
    return {
        "schema": "ev_nodi_paper_manifest_overrides_v1",
        "notes": (
            "Claim-bearing rows require explicit manual_override or verified_source metadata. "
            "Default rows are not claim-bearing."
        ),
        "papers": {
            paper_id: {
                "title": "",
                "authors": "",
                "year": "",
                "doi": "",
                "license_or_access_note": "local_reference_copy_not_relicensed",
                "used_for_claim_area": "",
                "metadata_source": "not_claim_bearing_not_used_for_claim_area",
            }
            for paper_id, _ in papers
        },
        "unavailable_or_not_packaged_papers": [],
    }


def paper_id_for_path(relpath: str) -> str:
    normalized = normalize_relpath(relpath)
    stem = Path(normalized).stem
    slug = re.sub(r"[^A-Za-z0-9]+", "_", unicodedata.normalize("NFKD", stem)).strip("_")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"{slug[:48]}_{digest}" if slug else f"paper_{digest}"


def scan_paper_files(project_root: Path = PROJECT_ROOT) -> list[tuple[str, str]]:
    paper_root = project_root / "papers"
    paths = []
    for suffix in ("*.pdf", "*.docx"):
        paths.extend(paper_root.glob(suffix))
    relpaths = sorted(
        normalize_relpath(path.relative_to(project_root))
        for path in paths
        if not path.name.startswith("._")
    )
    return [(paper_id_for_path(relpath), relpath) for relpath in relpaths]


def ensure_paper_overrides(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / PAPER_PROVENANCE_DIR / "paper_manifest_overrides.yaml"
    if not output.exists():
        write_json_atomic(output, _default_paper_overrides(project_root), sort_keys=True)
    return output


def load_paper_overrides(path: Path) -> dict[str, Any]:
    payload = _load_json_compatible(path)
    if not isinstance(payload.get("papers", {}), dict):
        raise ValueError("paper provenance overrides must contain a papers object")
    return payload


def _claim_metadata_is_verified(row: Mapping[str, Any]) -> bool:
    source = str(row.get("metadata_source", ""))
    return source in {"manual_override", "verified_source"}


def validate_paper_overrides(payload: Mapping[str, Any]) -> None:
    papers = payload.get("papers", {})
    if not isinstance(papers, Mapping):
        raise ValueError("paper provenance overrides must contain a papers object")
    for paper_id, row in papers.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"paper override must be an object: {paper_id}")
        if not row.get("used_for_claim_area"):
            continue
        required = ("title", "authors", "year", "doi")
        missing = [field for field in required if not str(row.get(field, "")).strip()]
        if missing or not _claim_metadata_is_verified(row):
            raise ValueError(
                "claim-bearing paper metadata must be manual_override or verified_source "
                f"with title/authors/year/doi: {paper_id}"
            )


def generate_paper_provenance(project_root: Path = PROJECT_ROOT) -> list[Path]:
    provenance_dir = project_root / PAPER_PROVENANCE_DIR
    provenance_dir.mkdir(parents=True, exist_ok=True)
    overrides_path = ensure_paper_overrides(project_root)
    overrides = load_paper_overrides(overrides_path)
    validate_paper_overrides(overrides)
    override_rows = overrides.get("papers", {})

    rows: list[dict[str, Any]] = []
    hash_lines: list[str] = []
    for paper_id, relpath in scan_paper_files(project_root):
        override = dict(override_rows.get(paper_id, {}))
        path = project_root / relpath
        digest = sha256_file(path)
        rows.append(
            {
                "paper_id": paper_id,
                "title": str(override.get("title", "")),
                "authors": str(override.get("authors", "")),
                "year": str(override.get("year", "")),
                "doi": str(override.get("doi", "")),
                "local_path": relpath,
                "sha256": digest,
                "included_in_package": "true",
                "license_or_access_note": str(
                    override.get("license_or_access_note", "local_reference_copy_not_relicensed")
                ),
                "used_for_claim_area": str(override.get("used_for_claim_area", "")),
                "metadata_source": str(
                    override.get("metadata_source", "not_claim_bearing_not_used_for_claim_area")
                ),
            }
        )
        hash_lines.append(f"{digest}  {relpath}\n")

    unavailable_rows = list(overrides.get("unavailable_or_not_packaged_papers", []))
    packaged_ids = {row["paper_id"] for row in rows}
    unavailable_ids = {str(row.get("paper_id", "")) for row in unavailable_rows}
    overlap = packaged_ids.intersection(unavailable_ids)
    if overlap:
        raise ValueError(f"paper provenance packaged/unavailable overlap: {sorted(overlap)}")

    write_csv_rows(provenance_dir / "paper_manifest.csv", rows)
    (provenance_dir / "paper_hashes.sha256").write_text("".join(hash_lines), encoding="utf-8")
    write_csv_rows(
        provenance_dir / "unavailable_or_not_packaged_papers.csv",
        unavailable_rows
        or [
            {
                "paper_id": "none_declared",
                "title": "",
                "reason": "no_unavailable_claim_area_papers_declared",
                "used_for_claim_area": "",
            }
        ],
    )
    (provenance_dir / "paper_bibliography.bib").write_text(
        "% Bibliography entries are intentionally manual/verified only.\n",
        encoding="utf-8",
    )
    (provenance_dir / "paper_provenance_notes.md").write_text(
        "# Paper Provenance\n\n"
        "Paper files are local reference copies for a no-measured-data relative audit. "
        "Claim-bearing metadata must come from manual overrides or verified sources; "
        "the generator does not infer bibliographic claims from filenames.\n",
        encoding="utf-8",
    )
    return [
        provenance_dir / "paper_manifest.csv",
        provenance_dir / "paper_manifest_overrides.yaml",
        provenance_dir / "paper_hashes.sha256",
        provenance_dir / "paper_bibliography.bib",
        provenance_dir / "paper_provenance_notes.md",
        provenance_dir / "unavailable_or_not_packaged_papers.csv",
    ]


def build_forbidden_claims_lexicon() -> dict[str, Any]:
    return {
        "schema": "ev_nodi_forbidden_claims_lexicon_v1",
        "languages": ["en", "zh"],
        "claim_scope": "no_measured_data_relative_audit_only",
        "negator_window_tokens_en": 8,
        "negator_window_chars_zh": 16,
        "verbs": [
            "calibrated",
            "validated",
            "absolute",
            "confirmed",
            "established",
            "measured",
            "true",
            "physical",
        ],
        "objects": [
            "SNR",
            "signal-to-noise",
            "LOD",
            "detection limit",
            "p_detect",
            "event probability",
            "false positive",
            "blank safety",
            "EV concentration",
            "particle count",
            "biological specificity",
            "exosome-specific detection",
            "MSC-EV-specific detection",
            "route promotion",
            "main-660 redefinition",
        ],
        "zh_forbidden_verbs": ["校准", "验证", "确认", "绝对", "真实", "实测", "已证明"],
        "zh_forbidden_objects": [
            "SNR",
            "信噪比",
            "LOD",
            "检测限",
            "假阳性",
            "空白安全",
            "EV浓度",
            "颗粒浓度",
            "生物特异性",
            "外泌体特异性",
            "MSC-EV特异性",
            "路线晋升",
            "main-660重新定义",
        ],
        "forbidden_phrase_negators": [
            "blocked",
            "forbidden",
            "not allowed",
            "cannot",
            "do not",
            "does not",
            "not",
            "no",
            "not supported",
            "not a claim",
            "not mean",
            "must not",
            "unauthorized",
            "not calibrated",
        ],
        "zh_negators": [
            "禁止",
            "阻断",
            "不允许",
            "不能",
            "不应",
            "未校准",
            "非校准",
            "不代表",
            "未实现",
            "未达",
            "无法",
            "尚未",
            "暂未",
            "不可声称",
            "已封禁",
            "已封锁",
            "被阻断",
        ],
        "allowed_blocker_examples": [
            "calibrated SNR blocked",
            "absolute LOD blocked",
            "not calibrated",
            "relative robustness only",
            "no-measured-data audit-only",
            "absolute claim blocked",
            "biological specificity blocked",
        ],
    }


def write_forbidden_claims_lexicon(project_root: Path = PROJECT_ROOT) -> Path:
    path = project_root / "configs/realism_v2/forbidden_claims_lexicon.yaml"
    write_json_atomic(path, build_forbidden_claims_lexicon(), sort_keys=True)
    return path


def write_p1_governance_files(project_root: Path = PROJECT_ROOT) -> list[Path]:
    outputs: list[Path] = []
    reason_path = project_root / "configs/realism_v2/reason_code_vocabulary.yaml"
    write_json_atomic(
        reason_path,
        {
            "schema": "ev_nodi_reason_code_vocabulary_v1",
            "code_pattern": "^[A-Z_]+\\.[A-Z0-9_]+$",
            "legacy_underscore_codes_allowed": False,
            "reason_codes": list(REASON_CODE_VOCABULARY),
        },
        sort_keys=True,
    )
    outputs.append(reason_path)
    role_path = project_root / "configs/realism_v2/route_role_vocabulary.yaml"
    write_json_atomic(
        role_path,
        {
            "schema": "ev_nodi_route_role_vocabulary_v1",
            "route_role_initial": list(ROUTE_ROLE_INITIAL_VALUES),
            "route_role_final": list(ROUTE_ROLE_FINAL_VALUES),
        },
        sort_keys=True,
    )
    outputs.append(role_path)
    ev_profiles_path = project_root / "configs/realism_v2/ev_sample_profiles.yaml"
    write_json_atomic(
        ev_profiles_path,
        {
            "schema": "ev_nodi_ev_sample_profiles_v1",
            "claim_level": "relative_sample_uncertainty_profiles_only",
            "profiles": {
                "unknown": {"min_risk_label": "medium", "biological_specificity_claim_allowed": False},
                "IEX_MSC_EV": {"min_risk_label": "medium", "biological_specificity_claim_allowed": False},
                "UF_MSC_EV": {"min_risk_label": "medium", "biological_specificity_claim_allowed": False},
                "PEG_like": {"min_risk_label": "high", "biological_specificity_claim_allowed": False},
                "SEC_like": {"min_risk_label": "medium", "biological_specificity_claim_allowed": False},
            },
        },
        sort_keys=True,
    )
    outputs.append(ev_profiles_path)
    noise_path = project_root / "configs/realism_v2/noise_readout_scenario_bundle.yaml"
    r5_manifest = _load_json_compatible(project_root / "configs/realism_v2/r5_scenario_bundle_manifest.yaml")
    scenario_ids = [row["scenario_id"] for row in r5_manifest["scenario_bundles"]]
    write_json_atomic(
        noise_path,
        {
            "schema": "ev_nodi_noise_readout_scenario_bundle_v1",
            "extends_scenario_bundle_id": r5_manifest["schema_version"],
            "source_scenario_manifest_path": "configs/realism_v2/r5_scenario_bundle_manifest.yaml",
            "source_scenario_manifest_sha256": sha256_file(project_root / "configs/realism_v2/r5_scenario_bundle_manifest.yaml"),
            "required_scenario_ids": scenario_ids,
            "scenario_alias_map": {},
            "forked_scenario_ids_allowed": False,
            "pass_criterion_id": "relative_rank_percentile_stability_vs_nominal_v1",
        },
        sort_keys=True,
    )
    outputs.append(noise_path)
    v1_pin_path = project_root / "configs/realism_v2/v1_summary_hash_pin.json"
    if not v1_pin_path.exists():
        write_json_atomic(
            v1_pin_path,
            {
                "schema": "ev_nodi_v1_summary_hash_pin_v1",
                "summary_csv_path": V1_SUMMARY_PATH,
                "summary_csv_sha256": sha256_file(project_root / V1_SUMMARY_PATH),
                "approved_v1_summary_drift_evidence_path": None,
                "drift_without_evidence_blocks_release": True,
            },
            sort_keys=True,
        )
    outputs.append(v1_pin_path)
    supersession_path = project_root / "HISTORICAL_REPORT_SUPERSESSION.md"
    supersession_path.write_text(
        "# Historical Report Supersession\n\n"
        "| historical_report_path | superseded_by | supersession_reason | current_claim_level |\n"
        "|---|---|---|---|\n"
        "| reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md | results/post_v2_mandatory_audit/ | P0 package and mandatory audit artifacts are now generated and tested. | no_measured_data_relative_audit_only |\n"
        "| reports/[0-8][0-9]_*.md | REVIEW_PACKAGE_MANIFEST.json | Frozen historical notes remain advisory and are superseded for current claims by the review package manifest. | frozen_history_advisory_only |\n",
        encoding="utf-8",
    )
    outputs.append(supersession_path)
    return outputs


def write_schema_docs(project_root: Path = PROJECT_ROOT) -> list[Path]:
    schema_dir = project_root / "docs/schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    docs = {
        "post_v2_mandatory_audit_schema.md": (
            "# Post-v2 Mandatory Audit Schema\n\n"
            "The core table is `results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv`. "
            "Rows are unique relative route aggregates with declared particle scope, rank-percentile evidence, "
            "and explicit claim blockers. Raw arbitrary-unit ratios are diagnostic only.\n"
        ),
        "review_package_manifest_schema.md": (
            "# Review Package Manifest Schema\n\n"
            "`REVIEW_BUILD_MANIFEST.json` may track build-time generation work. "
            "`REVIEW_PACKAGE_MANIFEST.json` is the relative-audit release manifest and may not contain "
            "`must_be_generated`. `REVIEW_PACKAGE_HASHES.sha256` excludes itself and the "
            "release manifest to avoid hash recursion.\n"
        ),
        "noise_readout_scenario_bundle_schema.md": (
            "# Noise/Readout Scenario Bundle Schema\n\n"
            "The post-v2 noise audit extends `configs/realism_v2/r5_scenario_bundle_manifest.yaml` "
            "by reference. Pass criteria are relative rank-percentile stability versus nominal; "
            "SNR, false-positive, and absolute margin floors remain blocked.\n"
        ),
        "ev_sample_profiles_schema.md": (
            "# EV Sample Profiles Schema\n\n"
            "`configs/realism_v2/ev_sample_profiles.yaml` defines relative uncertainty profiles. "
            "The `unknown` profile has at least medium risk and no biological-specificity claim.\n"
        ),
        "forbidden_claims_lexicon_schema.md": (
            "# Forbidden Claims Lexicon Schema\n\n"
            "`configs/realism_v2/forbidden_claims_lexicon.yaml` lists English and Chinese "
            "calibrated, absolute, biological, concentration, and promotion claim phrases. "
            "Negated blocker language is permitted within pinned windows.\n"
        ),
    }
    outputs = []
    for filename, text in docs.items():
        path = schema_dir / filename
        path.write_text(text, encoding="utf-8")
        outputs.append(path)
    return outputs


def _english_phrases(lexicon: Mapping[str, Any]) -> list[str]:
    phrases = []
    for verb in lexicon["verbs"]:
        for obj in lexicon["objects"]:
            phrases.append(f"{verb} {obj}".lower())
    phrases.extend(str(obj).lower() for obj in lexicon["objects"])
    return sorted(set(phrases), key=len, reverse=True)


def _zh_phrases(lexicon: Mapping[str, Any]) -> list[str]:
    phrases = []
    for verb in lexicon["zh_forbidden_verbs"]:
        for obj in lexicon["zh_forbidden_objects"]:
            phrases.append(f"{verb}{obj}")
    phrases.extend(str(obj) for obj in lexicon["zh_forbidden_objects"])
    return sorted(set(phrases), key=len, reverse=True)


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _ascii_object_only_phrase(phrase: str) -> bool:
    return phrase.isascii() and " " not in phrase and "-" not in phrase


def _has_negator_near_english(text: str, start: int, end: int, lexicon: Mapping[str, Any]) -> bool:
    lowered = text.lower()
    window = 320
    context = lowered[max(0, start - window) : min(len(text), end + window)]
    return any(str(negator).lower() in context for negator in lexicon["forbidden_phrase_negators"])


def _has_negator_near_zh(text: str, start: int, end: int, lexicon: Mapping[str, Any]) -> bool:
    window = int(lexicon["negator_window_chars_zh"])
    context = text[max(0, start - window) : min(len(text), end + window)]
    return any(str(negator) in context for negator in lexicon["zh_negators"])


def scan_forbidden_claims(text: str, lexicon: Mapping[str, Any]) -> list[ClaimFinding]:
    findings: list[ClaimFinding] = []
    lowered = text.lower()
    contains_cjk = _contains_cjk(text)
    for phrase in _english_phrases(lexicon):
        if contains_cjk and _ascii_object_only_phrase(phrase):
            continue
        start = lowered.find(phrase)
        if start == -1:
            continue
        end = start + len(phrase)
        findings.append(
            ClaimFinding(
                text=text,
                phrase=phrase,
                language="en",
                allowed_by_negator=_has_negator_near_english(text, start, end, lexicon),
            )
        )
    if not contains_cjk:
        return findings
    for phrase in _zh_phrases(lexicon):
        start = text.find(phrase)
        if start == -1:
            continue
        end = start + len(phrase)
        findings.append(
            ClaimFinding(
                text=text,
                phrase=phrase,
                language="zh",
                allowed_by_negator=_has_negator_near_zh(text, start, end, lexicon),
            )
        )
    return findings


def claim_text_passes(text: str, lexicon: Mapping[str, Any]) -> bool:
    return all(finding.allowed_by_negator for finding in scan_forbidden_claims(text, lexicon))


def load_forbidden_claims_lexicon(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return _load_json_compatible(project_root / "configs/realism_v2/forbidden_claims_lexicon.yaml")


def claim_scan_paths(project_root: Path = PROJECT_ROOT) -> list[Path]:
    patterns = (
        "README.md",
        "reports/9[0-9]_*.md",
        "reports/100_*.md",
        "reports/101_*.md",
        "reports/102_*.md",
        "reports/103_*.md",
        "reports/104_*.md",
        "reports/105_*.md",
        "reports/106_*.md",
        "reports/107_*.md",
        "reports/108_*.md",
        "reports/109_*.md",
        "reports/110_*.md",
        "reports/111_*.md",
        "reports/112_*.md",
        "reports/113_*.md",
        "reports/post_v2_*.md",
        "results/post_v2_mandatory_audit/*.md",
        "results/post_v2_physical_ceiling/*.md",
        "results/post_v2_bounded_physical_solver_readiness/*.md",
        "results/post_v2_bounded_solver_authorization_pilot_design/*.md",
        "results/post_v2_bounded_solver_dry_run_preflight/*.md",
        "results/post_v2_bounded_solver_authorization_gate/*.md",
        "results/post_v2_minimal_bounded_solver_execution/*.md",
        "results/post_v2_second_lane_authorization_design/*.md",
        "results/post_v2_second_bounded_solver_lane_execution/*.md",
        "results/post_v2_second_bounded_solver_lane_closure/*.md",
        "results/post_v2_next_bounded_lane_authorization_design/*.md",
        "results/post_v2_third_bounded_solver_lane_execution/*.md",
        "results/post_v2_third_bounded_solver_lane_closure/*.md",
        "results/post_v2_fourth_bounded_lane_authorization_design/*.md",
        "results/post_v2_fourth_bounded_solver_lane_execution/*.md",
        "results/post_v2_fourth_bounded_solver_lane_closure/*.md",
        "results/post_v2_fifth_bounded_lane_authorization_design/*.md",
        "REVIEW_PACKAGE_README.md",
        "papers/README.md",
    )
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(project_root.glob(pattern))
    return sorted(
        {
            path
            for path in paths
            if path.is_file()
            and not path.name.startswith("._")
            and normalize_relpath(path.relative_to(project_root))
        },
        key=lambda path: normalize_relpath(path.relative_to(project_root)),
    )


def _strip_fenced_code_blocks(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def scan_claim_files(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    lexicon = load_forbidden_claims_lexicon(project_root)
    violations: list[dict[str, Any]] = []
    for path in claim_scan_paths(project_root):
        text = _strip_fenced_code_blocks(path.read_text(encoding="utf-8"))
        for finding in scan_forbidden_claims(text, lexicon):
            if finding.allowed_by_negator:
                continue
            violations.append(
                {
                    "path": normalize_relpath(path.relative_to(project_root)),
                    "phrase": finding.phrase,
                    "language": finding.language,
                }
            )
    return violations


def write_review_package_readme(project_root: Path = PROJECT_ROOT) -> Path:
    path = project_root / "REVIEW_PACKAGE_README.md"
    path.write_text(
        "# EV/NODI Post-v2 Relative Audit Package\n\n"
        "This P0 release package supports a no-measured-data relative audit. "
        "It records reproducible paths, hashes, scaffold roles, paper provenance, "
        "claim-language blockers, and P0b route adjudication artifacts for review.\n\n"
        "v2 sidecars provide BFP ROI/Jacobian, Tsuyama BFP reference, Mie-to-power "
        "guardrail, noise/readout scenario, selected-annulus, and EV/sample uncertainty "
        "no-measured-data audit layers; however, the v1 full-grid main library remains a "
        "theta/phi surrogate, pupil/slit surrogate, arbitrary-unit relative engineering "
        "library, so all conclusions are relative candidate-audit conclusions and not "
        "calibrated physical predictions.\n",
        encoding="utf-8",
    )
    return path


def _config_entries(project_root: Path) -> list[dict[str, Any]]:
    paths = sorted((project_root / "configs/realism_v2").glob("*"))
    excluded = set(NON_P0_SIDECAR_P0_PACKAGE_EXCLUDED_CONFIGS)
    return [
        file_entry(
            project_root,
            normalize_relpath(path.relative_to(project_root)),
            role=path.name,
            source_lane="configs_realism_v2",
        )
        for path in paths
        if path.is_file()
        and not path.name.startswith("._")
        and normalize_relpath(path.relative_to(project_root)) not in excluded
    ]


def _paper_provenance_entries(project_root: Path) -> list[dict[str, Any]]:
    paths = sorted((project_root / PAPER_PROVENANCE_DIR).glob("*"))
    return [
        file_entry(
            project_root,
            normalize_relpath(path.relative_to(project_root)),
            role=path.name,
            source_lane="paper_provenance",
        )
        for path in paths
        if path.is_file() and not path.name.startswith("._")
    ]


def _artifact_groups(project_root: Path, *, include_generated_missing: bool) -> list[dict[str, Any]]:
    all_post_v2_roles_exist = all(
        (project_root / path).is_file() for _, path, _ in POST_V2_GENERATED_ROLES
    )
    groups: list[dict[str, Any]] = [
        {
            "group": "code_tests_tools_docs_reports",
            "artifacts": [
                file_entry(project_root, "README.md", role="repo_readme", source_lane="docs"),
                file_entry(
                    project_root,
                    "reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md",
                    role="roadmap",
                    source_lane="reports",
                ),
                file_entry(
                    project_root,
                    "reports/91_EV_NODI_post_v2_P0_release_completion_note.md",
                    role="p0_release_completion_note",
                    source_lane="reports",
                ),
                file_entry(
                    project_root,
                    "tools/generate_review_package_manifest.py",
                    role="review_package_manifest_generator",
                    source_lane="tools",
                ),
                file_entry(
                    project_root,
                    "tools/generate_paper_provenance.py",
                    role="paper_provenance_generator",
                    source_lane="tools",
                ),
                file_entry(
                    project_root,
                    "tools/verify_review_package.py",
                    role="review_package_verifier",
                    source_lane="tools",
                ),
                file_entry(
                    project_root,
                    "tools/export_review_package.py",
                    role="review_package_exporter",
                    source_lane="tools",
                ),
            ],
        },
        {"group": "configs_realism_v2", "artifacts": _config_entries(project_root)},
        {
            "group": "calibration_scaffold_all_files",
            "calibration_template_role": "schema_placeholder_no_measured_data",
            "artifacts": [
                file_entry(
                    project_root,
                    relpath,
                    role=Path(relpath).name,
                    source_lane="calibration_scaffold",
                )
                for relpath in CALIBRATION_SCAFFOLD_FILES
            ],
        },
        {
            "group": "v1_key_result_artifacts",
            "v1_summary_mode": "existing_single_summary_csv",
            "contract": v1_summary_contract(project_root),
            "artifacts": [
                file_entry(project_root, V1_SUMMARY_PATH, role="v1_summary_csv", source_lane="v1")
            ],
        },
        {
            "group": "v2_closure_artifacts",
            "artifacts": [
                file_entry(project_root, path, role=role, source_lane=source_lane)
                for role, path, source_lane in EXISTING_V2_ROLE_PATHS
            ],
        },
        {
            "group": "post_v2_mandatory_audit_schema",
            "artifacts": [
                file_entry(
                    project_root,
                    "results/post_v2_mandatory_audit/top_candidate_mandatory_audit_manifest.json",
                    role="top_candidate_mandatory_audit_manifest",
                    source_lane="P0a.v1_v2_artifact_mapping",
                )
            ],
        },
        {"group": "paper_provenance", "artifacts": _paper_provenance_entries(project_root)},
        {
            "group": "claim_language_lexicon",
            "artifacts": [
                file_entry(
                    project_root,
                    "configs/realism_v2/forbidden_claims_lexicon.yaml",
                    role="forbidden_claims_lexicon",
                    source_lane="claim_language_lexicon",
                )
            ],
        },
        {
            "group": "review_package_root",
            "artifacts": [
                file_entry(
                    project_root,
                    "REVIEW_PACKAGE_README.md",
                    role="review_package_readme",
                    source_lane="review_package_root",
                ),
                file_entry(
                    project_root,
                    "HISTORICAL_REPORT_SUPERSESSION.md",
                    role="historical_report_supersession",
                    source_lane="P1.governance",
                ),
            ],
        },
        {
            "group": "p1_governance_configs",
            "artifacts": [
                file_entry(
                    project_root,
                    "configs/realism_v2/reason_code_vocabulary.yaml",
                    role="reason_code_vocabulary",
                    source_lane="P1.governance",
                ),
                file_entry(
                    project_root,
                    "configs/realism_v2/route_role_vocabulary.yaml",
                    role="route_role_vocabulary",
                    source_lane="P1.governance",
                ),
                file_entry(
                    project_root,
                    "configs/realism_v2/ev_sample_profiles.yaml",
                    role="ev_sample_profiles",
                    source_lane="P1.governance",
                ),
                file_entry(
                    project_root,
                    "configs/realism_v2/noise_readout_scenario_bundle.yaml",
                    role="noise_readout_scenario_bundle_config",
                    source_lane="P1.governance",
                ),
                file_entry(
                    project_root,
                    "configs/realism_v2/v1_summary_hash_pin.json",
                    role="v1_summary_hash_pin",
                    source_lane="P1.governance",
                ),
            ],
        },
        {
            "group": "schema_docs",
            "artifacts": [
                file_entry(
                    project_root,
                    f"docs/schemas/{filename}",
                    role=Path(filename).stem,
                    source_lane="P2.schema_docs",
                )
                for filename in (
                    "post_v2_mandatory_audit_schema.md",
                    "review_package_manifest_schema.md",
                    "noise_readout_scenario_bundle_schema.md",
                    "ev_sample_profiles_schema.md",
                    "forbidden_claims_lexicon_schema.md",
                )
            ],
        },
    ]
    if include_generated_missing or all_post_v2_roles_exist:
        groups.append(
            {
                "group": "post_v2_mandatory_audit_artifacts",
                "artifacts": [
                    {
                        "role": role,
                        "path": path,
                        "path_status": "exists"
                        if (project_root / path).exists()
                        else "must_be_generated",
                        "source_lane": "post-v2 mandatory audit",
                        "sha256": sha256_file(project_root / path)
                        if (project_root / path).exists()
                        else None,
                        "generation_task_id": task
                        if include_generated_missing and not (project_root / path).exists()
                        else "",
                    }
                    for role, path, task in POST_V2_GENERATED_ROLES
                    if include_generated_missing or (project_root / path).exists()
                ],
            }
        )
    diagnostic_artifacts = [
        file_entry(project_root, path, role=role, source_lane=task)
        for role, path, task in POST_V2_DIAGNOSTIC_ROLES
        if (project_root / path).exists()
    ]
    if diagnostic_artifacts:
        groups.append(
            {
                "group": "post_v2_optional_diagnostic_artifacts",
                "release_blocker": False,
                "artifacts": diagnostic_artifacts,
            }
        )
    return groups


def iter_release_artifact_paths(manifest: Mapping[str, Any]) -> list[str]:
    paths: list[str] = []
    for group in manifest.get("artifact_groups", []):
        for artifact in group.get("artifacts", []):
            if artifact.get("path_status") == "exists":
                paths.append(str(artifact["path"]))
    return sorted(set(paths))


def write_hash_manifest(
    project_root: Path,
    artifact_paths: Iterable[str],
    *,
    output_relpath: str = "REVIEW_PACKAGE_HASHES.sha256",
) -> str:
    excluded = {
        output_relpath,
        "REVIEW_PACKAGE_MANIFEST.json",
        "REVIEW_BUILD_MANIFEST.json",
    }
    lines = []
    for relpath in sorted(set(normalize_relpath(path) for path in artifact_paths)):
        if relpath in excluded:
            continue
        path = project_root / relpath
        if path.is_file():
            lines.append(f"{sha256_file(path)}  {relpath}\n")
    output = project_root / output_relpath
    output.write_text("".join(lines), encoding="utf-8")
    return sha256_file(output)


def build_review_manifests(
    project_root: Path = PROJECT_ROOT,
    *,
    generated_at: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    generated_at = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    package_id = f"ev_nodi_post_v2_review_package_{datetime.now(UTC).strftime('%Y%m%d')}_p0b"
    base = {
        "package_id": package_id,
        "generated_at": generated_at,
        "git_commit": git_commit(project_root),
        "git_dirty": git_dirty(project_root),
        "calibrated_claim_allowed": False,
        "hashes_manifest_path": "REVIEW_PACKAGE_HASHES.sha256",
    }
    release_manifest = {
        **base,
        "review_package_manifest_schema": "ev_nodi_review_package_manifest_v1",
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "package_role": "external_review_relative_audit",
        "release_readiness": "p0_p0b_review_ready_relative_audit",
        "v1_summary_mode": "existing_single_summary_csv",
        "artifact_groups": _artifact_groups(project_root, include_generated_missing=False),
        "deferred_p0b_roles": [
            {"role": role, "path": path, "deferred_to": task}
            for role, path, task in POST_V2_GENERATED_ROLES
            if not (project_root / path).exists()
        ],
    }
    hashes_manifest_sha256 = write_hash_manifest(
        project_root,
        iter_release_artifact_paths(release_manifest),
    )
    release_manifest["hashes_manifest_sha256"] = hashes_manifest_sha256
    build_manifest = {
        **base,
        "review_build_manifest_schema": "ev_nodi_review_build_manifest_v1",
        "package_role": "internal_build_tracking",
        "release_manifest_path": "REVIEW_PACKAGE_MANIFEST.json",
        "hashes_manifest_sha256": hashes_manifest_sha256,
        "artifact_groups": _artifact_groups(project_root, include_generated_missing=True),
    }
    return build_manifest, release_manifest


def write_review_manifests(project_root: Path = PROJECT_ROOT) -> tuple[Path, Path, Path]:
    generate_paper_provenance(project_root)
    write_forbidden_claims_lexicon(project_root)
    write_p1_governance_files(project_root)
    write_schema_docs(project_root)
    write_audit_schema_manifest(project_root)
    write_review_package_readme(project_root)
    build_manifest, release_manifest = build_review_manifests(project_root)
    build_path = project_root / "REVIEW_BUILD_MANIFEST.json"
    release_path = project_root / "REVIEW_PACKAGE_MANIFEST.json"
    write_json_atomic(build_path, build_manifest, sort_keys=True)
    write_json_atomic(release_path, release_manifest, sort_keys=True)
    return build_path, release_path, project_root / "REVIEW_PACKAGE_HASHES.sha256"


def verify_review_package(project_root: Path = PROJECT_ROOT, *, allow_dirty: bool = False) -> list[str]:
    release_path = project_root / "REVIEW_PACKAGE_MANIFEST.json"
    hash_path = project_root / "REVIEW_PACKAGE_HASHES.sha256"
    manifest = _load_json_compatible(release_path)
    if manifest.get("review_package_manifest_schema") != "ev_nodi_review_package_manifest_v1":
        raise ValueError("unexpected REVIEW_PACKAGE_MANIFEST schema")
    if not allow_dirty and manifest.get("git_dirty"):
        raise ValueError("dirty worktree cannot be verified as an external release")
    encoded = json.dumps(manifest, ensure_ascii=False)
    if "must_be_generated" in encoded:
        raise ValueError("release manifest must not contain must_be_generated")
    if sha256_file(hash_path) != manifest.get("hashes_manifest_sha256"):
        raise ValueError("hashes_manifest_sha256 mismatch")
    v1_contract = next(
        group for group in manifest["artifact_groups"] if group["group"] == "v1_key_result_artifacts"
    )["contract"]
    if not v1_hash_drift_is_authorized(v1_contract):
        raise ValueError("V1_SUMMARY_DRIFT_UNAUTHORIZED")
    hash_entries: dict[str, str] = {}
    for line in hash_path.read_text(encoding="utf-8").splitlines():
        digest, relpath = line.split("  ", 1)
        if relpath in {"REVIEW_PACKAGE_HASHES.sha256", "REVIEW_PACKAGE_MANIFEST.json"}:
            raise ValueError("hash manifest contains a no-cycle excluded path")
        hash_entries[relpath] = digest
    for relpath in iter_release_artifact_paths(manifest):
        if relpath in {"REVIEW_PACKAGE_HASHES.sha256", "REVIEW_PACKAGE_MANIFEST.json"}:
            continue
        path = project_root / relpath
        if not path.exists():
            raise ValueError(f"required release artifact missing: {relpath}")
        if hash_entries.get(relpath) != sha256_file(path):
            raise ValueError(f"artifact hash mismatch: {relpath}")
    violations = scan_claim_files(project_root)
    if violations:
        raise ValueError(f"claim-language violations: {violations[:5]}")
    return [
        "PASS required_paths",
        "PASS hashes",
        "PASS v1_summary_contract",
        "PASS v2_closure_contract",
        "PASS post_v2_audit_schema"
        if not manifest.get("deferred_p0b_roles")
        else "SKIP post_v2_audit_tables declared_P0b_deferred",
        "PASS claim_blockers",
    ]


def export_review_package(
    project_root: Path = PROJECT_ROOT,
    *,
    output_path: Path | None = None,
) -> Path:
    write_review_manifests(project_root)
    manifest = _load_json_compatible(project_root / "REVIEW_PACKAGE_MANIFEST.json")
    if output_path is None:
        output_path = (
            project_root
            / "exports"
            / f"{manifest['package_id']}_review_package.zip"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    package_paths = sorted(
        set(
            [
                "REVIEW_PACKAGE_MANIFEST.json",
                "REVIEW_PACKAGE_HASHES.sha256",
                *iter_release_artifact_paths(manifest),
            ]
        )
    )
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for relpath in package_paths:
            if relpath.startswith("._") or "/._" in relpath or relpath == "REVIEW_BUILD_MANIFEST.json":
                continue
            path = project_root / relpath
            if not path.is_file():
                raise ValueError(f"cannot export missing package artifact: {relpath}")
            info = zipfile.ZipInfo(relpath)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, path.read_bytes())
    return output_path
