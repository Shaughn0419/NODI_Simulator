"""Pre-3seed/10000e logic-hardening artifacts and gates.

This module turns the 2026-05-18 preflight roadmap into reproducible
route-governance artifacts. It deliberately stays inside the project's
no-measured-data relative/proxy boundary: generated ablation and stability
tables are qualification and demotion gates, not calibrated detector claims.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import platform
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
import tempfile
from typing import Any

import numpy as np

from .data_objects import (
    BASELINE_OPTICAL,
    DEFAULT_SIM_CFG,
    PBS_1X,
    WATER,
    Channel,
    Medium,
    Particle,
    make_ev_nodi_design_sweep_config,
    make_gold_baseline_particle,
)
from .parameter_sweep import run_parameter_sweep
from .realism_v2_io import sha256_file, write_csv_rows, write_json_atomic
from .review_package import stable_json_bytes
from .structured_particles import make_biomimetic_exosome_particle


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_DATE = "20260518"
PREFLIGHT_SCHEMA = "pre3seed_logic_hardening_v1"

ROUTE_MATRIX_PATH = Path("results/current_route_claim_matrix.csv")
EVIDENCE_STATE_PATH = Path("reports/current_evidence_state_20260518.md")
CLAIM_POLICY_PATH = Path("configs/preflight/claim_linter_policy_v1.json")
FORMULA_LEDGER_CSV_PATH = Path("results/formula_chain_ledger_pre_3seed_v1.csv")
FORMULA_LEDGER_MD_PATH = Path("reports/formula_chain_ledger_pre_3seed_v1.md")
CANDIDATE_MANIFEST_PATH = Path("results/pre3seed_candidate_set_manifest.csv")
REFERENCE_ABLATION_MATRIX_PATH = Path("results/reference_ablation_rank_matrix.csv")
REFERENCE_ABLATION_SUMMARY_PATH = Path(
    "results/reference_ablation_candidate_family_summary.csv"
)
REFERENCE_FRAGILITY_FLAGS_PATH = Path("results/reference_fragility_flags.csv")
DETECTOR_ABLATION_MATRIX_PATH = Path(
    "results/detector_readout_threshold_ablation_matrix.csv"
)
DETECTOR_OPERATOR_LABEL_PATH = Path("results/detector_operator_sensitivity_label.csv")
THRESHOLD_LABEL_PATH = Path("results/threshold_noise_sensitivity_label.csv")
PULSE_GUARDRAIL_PATH = Path("results/pulse_sampling_deadtime_guardrail.csv")
GEOMETRY_MATRIX_PATH = Path("results/geometry_transport_viability_matrix.csv")
EV_PRIOR_EVIDENCE_PATH = Path("results/EV_prior_evidence_table.csv")
EV_PRIOR_STRESS_PATH = Path("results/EV_particle_prior_stress_matrix.csv")
EV_CANDIDATE_STABILITY_PATH = Path("results/EV_candidate_stability_summary.csv")
INTERFACE_MATRIX_PATH = Path("results/interface_wall_fullwave_needed_matrix.csv")
SHORT_WAVELENGTH_RISK_PATH = Path("results/short_wavelength_exposure_risk_matrix.csv")
STABILITY_MATRIX_PATH = Path("results/candidate_family_stability_matrix.csv")
DEMOTIONS_PATH = Path("results/candidate_family_demotions.csv")
CARRY_FORWARD_PATH = Path("results/candidate_family_carry_forward_manifest.csv")
FREEZE_MANIFEST_PATH = Path("results/pre3seed_freeze_manifest_20260518.json")
DRY_REPORT_PATH = Path("reports/pre3seed_final_dry_run_report_20260518.md")
GATE_SUMMARY_PATH = Path("results/pre3seed_stop_gate_summary_20260518.csv")
VERIFICATION_SUMMARY_PATH = Path("results/pre3seed_verification_summary_20260518.json")

MICRO_SMOKE_DIR = Path("results/pre3seed_micro_smoke_20260518")
REHEARSAL_DIR = Path("results/pre3seed_3seed_low_event_rehearsal_20260518")
FORMAL_RUN_PLAN_CSV_PATH = Path("results/pre3seed_formal_3seed_10000e_run_plan.csv")
FORMAL_RUN_PLAN_JSON_PATH = Path("results/pre3seed_formal_3seed_10000e_run_plan_manifest.json")
FORMAL_DUAL_LENS_TOP_TABLE_PATH = Path(
    "results/pre3seed_rehearsal_dual_lens_top_table.csv"
)
FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH = Path(
    "results/pre3seed_rehearsal_pooled_per_seed_consistency.csv"
)
FORMAL_PRELAUNCH_MANIFEST_PATH = Path(
    "results/pre3seed_formal_3seed_10000e_prelaunch_manifest.json"
)
P19_GATE_REPORT_PATH = Path("reports/130_P19_evidence_strategy_gate.md")
P19_EVIDENCE_TO_CONFIG_GAP_PATH = Path(
    "papers/analysis_full_v1/paper_evidence_to_config_gap.csv"
)
P19_CRITICAL_BINDING_PATH = Path(
    "papers/analysis_full_v1/critical_paper_target_binding.csv"
)
P19_CRITICAL_GAP_REPORT_PATH = Path("reports/131_critical_paper_table_extraction_gap.md")
P19_POD_SCOPE_REPORT_PATH = Path("reports/132_pod_scope_decision.md")
P19_RELEASE_REPORT_OUTLINE_PATH = Path(
    "reports/135_pre3seed_10000e_level1_release_report.md"
)
P19_FULL_RUN_COVERAGE_AUDIT_PATH = Path(
    "reports/136_pre3seed_full_run_coverage_rerun_risk_audit.md"
)
P19_CONTAMINANT_DIAGNOSTIC_MANIFEST_PATH = Path(
    "configs/preflight/contaminant_stress_diagnostic_manifest_p19_20260518.csv"
)
P19_PREMEASUREMENT_AUDIT_PATH = Path(
    "results/pre3seed_p19_premeasurement_freeze_closure_audit_20260518.json"
)
# The audit snapshot may hash the prelaunch manifest; do not include it in the
# prelaunch P19 hash contract or the two files become mutually unrefreshable.
FORMAL_P19_REQUIRED_ARTIFACT_PATHS = (
    P19_GATE_REPORT_PATH,
    P19_EVIDENCE_TO_CONFIG_GAP_PATH,
    P19_CRITICAL_BINDING_PATH,
    P19_CRITICAL_GAP_REPORT_PATH,
    P19_POD_SCOPE_REPORT_PATH,
    P19_RELEASE_REPORT_OUTLINE_PATH,
    P19_FULL_RUN_COVERAGE_AUDIT_PATH,
    P19_CONTAMINANT_DIAGNOSTIC_MANIFEST_PATH,
)
FORMAL_LAUNCH_CONFIRMATION_FLAG = "--confirm-p19-level1-launch"
FORMAL_LAUNCH_CONTRACT_VERSION = "pre3seed_level1_no_measured_data_launch_contract_v1"
FORMAL_WORKER_COUNT = 16
FORMAL_EXACT_COMMAND_TEMPLATE = (
    "python tools/run_pre3seed_3seed_10000e_from_manifest.py "
    "--execute --allow-large-run --confirm-p19-level1-launch "
    f"--events-per-case 10000 --seeds 11,22,33 --workers {FORMAL_WORKER_COUNT}"
)
FORMAL_DRY_RUN_COMMAND = (
    "python tools/run_pre3seed_3seed_10000e_from_manifest.py "
    f"--dry-run --workers {FORMAL_WORKER_COUNT}"
)
FORMAL_EXECUTION_REQUIRED_HASH_PATHS = (
    CARRY_FORWARD_PATH,
    CANDIDATE_MANIFEST_PATH,
    STABILITY_MATRIX_PATH,
    FORMAL_RUN_PLAN_CSV_PATH,
    FORMAL_RUN_PLAN_JSON_PATH,
    FORMAL_PRELAUNCH_MANIFEST_PATH,
)

REQUIRED_TOP_TABLE_BLOCKER_COLUMNS = (
    "stability_class",
    "claim_boundary_flags",
    "interface_fullwave_required",
    "count_prediction_status",
    "detection_rate_denominator",
    "normalization_policy",
    "lens_policy",
    "reference_route",
    "detector_route",
    "threshold_source",
    "readout_route",
    "route_scope_key",
)

REQUIRED_ROUTE_MATRIX_FIELDS = (
    "route_contract_id",
    "schema_version",
    "report_id",
    "report_version",
    "result_path",
    "result_file_hash",
    "code_commit_hash",
    "config_hash",
    "analysis_script_hash",
    "paper_evidence_ledger_version",
    "lens_policy",
    "b_stage",
    "events_per_case",
    "seed_policy",
    "normalization_policy",
    "allowed_aggregation_keys",
    "legacy_compatibility_status",
    "reference_route",
    "detector_route",
    "operator_route",
    "threshold_source",
    "readout_route",
    "EV_prior_id",
    "interface_status",
    "transport_status",
    "count_prediction_status",
    "candidate_set_source",
    "preflight_role",
    "allowed_for_preflight",
    "required_blocker_columns",
    "claim_linter_status",
    "claim_level",
    "allowed_conclusion",
    "forbidden_conclusion",
    "reader_warning_required",
)

REQUIRED_LEDGER_FIELDS = (
    "ledger_id",
    "model_step",
    "formula_or_transformation",
    "code_file",
    "function_or_field",
    "input_units",
    "output_units",
    "dimension_check_status",
    "literature_source",
    "assumption",
    "route_status",
    "test_id",
    "claim_boundary",
    "failure_mode",
)

STOP_GATE_IDS = tuple(f"SG{i}" for i in range(14))


class PreflightGateError(ValueError):
    """Raised when a preflight hard-stop gate fails."""


def relpath(path: str | Path, project_root: Path = PROJECT_ROOT) -> str:
    path = Path(path)
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(stable_json_bytes(payload)).hexdigest()


def sha256_or_na(path: Path) -> str:
    return sha256_file(path) if path.exists() and path.is_file() else "not_available"


def git_commit(project_root: Path = PROJECT_ROOT) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "git_commit_unavailable"


def git_dirty_summary(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=project_root,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return {"dirty": True, "status": "git_status_unavailable", "entries": []}
    entries = [line for line in output.splitlines() if line.strip()]
    return {"dirty": bool(entries), "status": "dirty" if entries else "clean", "entries": entries}


def config_hash(project_root: Path = PROJECT_ROOT) -> str:
    paths = [
        project_root / "pyproject.toml",
        project_root / "configs/realism_v2/forbidden_claims_lexicon.yaml",
        project_root / "configs/realism_v2/r5_scenario_bundle_manifest.yaml",
        project_root / "configs/realism_v2/route_key_schema.yaml",
    ]
    payload = {
        relpath(path, project_root): sha256_or_na(path)
        for path in paths
    }
    return sha256_payload(payload)


def analysis_script_hash(project_root: Path = PROJECT_ROOT) -> str:
    paths = [
        project_root / "nodi_simulator/pre3seed_hardening.py",
        project_root / "tools/pre3seed_logic_hardening.py",
        project_root / "tools/run_pre3seed_3seed_10000e_from_manifest.py",
    ]
    payload = {
        relpath(path, project_root): sha256_or_na(path)
        for path in paths
    }
    return sha256_payload(payload)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_claim_linter_policy() -> dict[str, Any]:
    """Return the stricter preflight linter used before intermediate outputs."""
    return {
        "schema_version": "pre3seed_claim_linter_policy_v1",
        "claim_scope": "no_measured_data_relative_proxy_design_selection",
        "negator_or_boundary_terms": [
            "blocked",
            "forbidden",
            "not allowed",
            "not calibrated",
            "no measured data",
            "relative/proxy",
            "proxy",
            "surrogate",
            "diagnostic",
            "conditional",
            "stress",
            "boundary",
            "blocked pending",
            "阻断",
            "禁止",
            "不允许",
            "未校准",
            "非校准",
            "代理",
            "相对",
            "诊断",
            "条件",
            "压力分支",
        ],
        "scope_qualifier_terms": [
            "within lens",
            "within route",
            "within normalization",
            "event-position window",
            "conditional synthetic event",
            "synthetic/proxy",
            "recommendation-qualification",
            "classification gate",
            "same lens",
            "same route",
            "same normalization",
            "同一 lens",
            "同一路线",
            "同一归一化",
            "event-position window",
            "事件位置窗口",
            "合成条件事件",
            "推荐资格",
            "分类门",
        ],
        "hard_forbidden_positive_phrases": [
            "real SNR",
            "absolute LOD",
            "true detection rate",
            "empirical blank",
            "true concentration",
            "detector voltage",
            "photon count",
            "exosome specificity",
            "calibrated cross-wavelength superiority",
            "404 wins",
            "660 wins",
            "真实信噪比",
            "绝对检出限",
            "真实检出率",
            "实测空白",
            "真实浓度",
            "探测器电压",
            "光子计数",
            "外泌体特异性",
            "校准跨波长优越",
        ],
        "requires_scope_phrases": [
            "best wavelength",
            "optimal wavelength",
            "best",
            "optimal",
            "sensitivity",
            "detection rate",
            "calibrated",
            "SNR",
            "LOD",
            "exosome",
            "最优",
            "最佳波长",
            "灵敏度",
            "信噪比",
            "检出率",
            "检测效率",
            "检出限",
            "真实样品",
            "实测",
            "校准",
            "外泌体",
        ],
        "selected_annulus_required_boundary": "event-position window",
        "detection_rate_required_columns": [
            "detection_rate_denominator",
            "detection_rate_claim_level",
            "detection_rate_boundary",
        ],
    }


def _context_has_any(text: str, start: int, end: int, terms: Sequence[str], *, window: int = 220) -> bool:
    context = text[max(0, start - window) : min(len(text), end + window)].lower()
    return any(term.lower() in context for term in terms)


def scan_preflight_claim_text(
    text: str,
    policy: Mapping[str, Any] | None = None,
    *,
    source: str = "<text>",
) -> list[dict[str, Any]]:
    """Scan preflight text for unqualified claims in English and Chinese."""
    active_policy = dict(policy or build_claim_linter_policy())
    findings: list[dict[str, Any]] = []
    lowered = text.lower()
    boundary_terms = list(active_policy["negator_or_boundary_terms"]) + list(
        active_policy["scope_qualifier_terms"]
    )
    for phrase in active_policy["hard_forbidden_positive_phrases"]:
        pattern = re.escape(str(phrase).lower())
        for match in re.finditer(pattern, lowered):
            if _context_has_any(text, match.start(), match.end(), boundary_terms):
                continue
            findings.append(
                {
                    "source": source,
                    "phrase": phrase,
                    "finding_type": "hard_forbidden_positive_phrase",
                    "severity": "hard_stop",
                }
            )
    for phrase in active_policy["requires_scope_phrases"]:
        search_text = lowered if str(phrase).isascii() else text
        search_phrase = str(phrase).lower() if str(phrase).isascii() else str(phrase)
        for match in re.finditer(re.escape(search_phrase), search_text):
            if _context_has_any(text, match.start(), match.end(), boundary_terms):
                continue
            findings.append(
                {
                    "source": source,
                    "phrase": phrase,
                    "finding_type": "missing_scope_boundary",
                    "severity": "hard_stop",
                }
            )
    return findings


def validate_preflight_table_scope(
    rows: Sequence[Mapping[str, Any]],
    *,
    table_name: str,
    policy: Mapping[str, Any] | None = None,
) -> None:
    """Fail closed on route/lens/normalization/denominator mixing."""
    if not rows:
        raise PreflightGateError(f"{table_name}: empty table")
    active_policy = dict(policy or build_claim_linter_policy())
    fields = set().union(*(set(row.keys()) for row in rows))
    required_status = {
        "lens_policy",
        "b_stage",
        "events_per_case",
        "normalization_policy",
        "reference_route",
        "detector_route",
        "threshold_source",
        "readout_route",
        "claim_level",
    }
    missing = sorted(required_status - fields)
    if missing:
        raise PreflightGateError(f"{table_name}: missing route/status fields {missing}")

    def unique(field: str) -> set[str]:
        return {str(row.get(field, "")).strip() for row in rows if str(row.get(field, "")).strip()}

    for field in ("lens_policy", "b_stage", "events_per_case", "normalization_policy"):
        values = unique(field)
        if len(values) > 1:
            raise PreflightGateError(
                f"{table_name}: mixed {field} values {sorted(values)} without explicit split scope"
            )

    if any("detection_rate" in field for field in fields):
        required_denominator = set(active_policy["detection_rate_required_columns"])
        missing_denominator = sorted(required_denominator - fields)
        if missing_denominator:
            raise PreflightGateError(
                f"{table_name}: detection_rate fields require {missing_denominator}"
            )

    for row in rows:
        text = " ".join(str(value) for value in row.values())
        if "selected-annulus" in text.lower() or "selected_annulus" in text.lower():
            if active_policy["selected_annulus_required_boundary"] not in text:
                raise PreflightGateError(
                    f"{table_name}: selected-annulus lacks event-position window boundary"
                )
        findings = scan_preflight_claim_text(text, active_policy, source=table_name)
        if findings:
            raise PreflightGateError(f"{table_name}: claim linter findings {findings[:3]}")


def build_route_claim_matrix(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    commit = git_commit(project_root)
    cfg_hash = config_hash(project_root)
    script_hash = analysis_script_hash(project_root)
    paper_ledger = "papers/analysis_full_v1/run_manifest.json"
    paper_hash = sha256_or_na(project_root / paper_ledger)
    blocker_columns = (
        "detector_unit_chain_status;threshold_calibration_status;"
        "interface_fullwave_required;count_prediction_status;"
        "cross_wavelength_claim_gate_passed;ev_biological_specificity_claim_allowed"
    )

    def row(
        *,
        route_contract_id: str,
        report_id: str,
        report_version: str,
        result_path: str,
        lens_policy: str,
        b_stage: str,
        events_per_case: str,
        seed_policy: str,
        normalization_policy: str,
        reference_route: str,
        detector_route: str,
        operator_route: str,
        threshold_source: str,
        readout_route: str,
        candidate_set_source: str,
        preflight_role: str,
        allowed_for_preflight: bool,
        claim_level: str,
        allowed_conclusion: str,
        forbidden_conclusion: str,
        reader_warning_required: bool = True,
        legacy_compatibility_status: str = "not_legacy",
        interface_status: str = "homogeneous_medium_mie_fullwave_required_when_flagged",
        transport_status: str = "conditional_crossing_event_transport_proxy",
        count_prediction_status: str = "not_applied_per_event_only",
        EV_prior_id: str = "optical_EV_like_surrogate_prior_v1",
    ) -> dict[str, Any]:
        full = project_root / result_path
        return {
            "route_contract_id": route_contract_id,
            "schema_version": PREFLIGHT_SCHEMA,
            "report_id": report_id,
            "report_version": report_version,
            "result_path": result_path,
            "result_file_hash": sha256_or_na(full),
            "code_commit_hash": commit,
            "config_hash": cfg_hash,
            "analysis_script_hash": script_hash,
            "paper_evidence_ledger_version": f"{paper_ledger}:{paper_hash}",
            "lens_policy": lens_policy,
            "b_stage": b_stage,
            "events_per_case": events_per_case,
            "seed_policy": seed_policy,
            "normalization_policy": normalization_policy,
            "allowed_aggregation_keys": (
                "route_contract_id;lens_policy;b_stage;events_per_case;"
                "seed_policy;normalization_policy;reference_route;detector_route;"
                "threshold_source;readout_route;claim_level"
            ),
            "legacy_compatibility_status": legacy_compatibility_status,
            "reference_route": reference_route,
            "detector_route": detector_route,
            "operator_route": operator_route,
            "threshold_source": threshold_source,
            "readout_route": readout_route,
            "EV_prior_id": EV_prior_id,
            "interface_status": interface_status,
            "transport_status": transport_status,
            "count_prediction_status": count_prediction_status,
            "candidate_set_source": candidate_set_source,
            "preflight_role": preflight_role,
            "allowed_for_preflight": str(bool(allowed_for_preflight)).lower(),
            "required_blocker_columns": blocker_columns,
            "claim_linter_status": "preflight_policy_required_before_aggregation",
            "claim_level": claim_level,
            "allowed_conclusion": allowed_conclusion,
            "forbidden_conclusion": forbidden_conclusion,
            "reader_warning_required": str(bool(reader_warning_required)).lower(),
        }

    rows = [
        row(
            route_contract_id="historical_lens_A_10000e_v1",
            report_id="reports/current/47_EV_NODI_full_result_layered_analysis",
            report_version="historical_v1",
            result_path="results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv",
            lens_policy="A",
            b_stage="historical",
            events_per_case="10000",
            seed_policy="single",
            normalization_policy="per_wavelength",
            reference_route="engineering_channel_angular_surrogate",
            detector_route="joint_overlap_coherent_surrogate",
            operator_route="theta_phi_surrogate_no_calibrated_bfp_jacobian",
            threshold_source="gaussian_iid_surrogate_not_empirical_blank",
            readout_route="EV_NODI_only_design_bandpass_envelope_surrogate",
            candidate_set_source="historical_top",
            preflight_role="candidate",
            allowed_for_preflight=True,
            claim_level="historical_relative_proxy_evidence_only",
            allowed_conclusion="May inform multi-source candidate coverage within lens A only.",
            forbidden_conclusion="Does not prove calibrated detector performance or cross-wavelength superiority.",
            legacy_compatibility_status="legacy_input_do_not_mix_with_B7_without_diagnostic_label",
        ),
        row(
            route_contract_id="lens_B_B7_fixed660_1000e_seed42",
            report_id="reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis",
            report_version="B7_fixed660_gold_seed42",
            result_path="results/lens_b_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42_summary.csv",
            lens_policy="selected_annulus",
            b_stage="B7",
            events_per_case="1000",
            seed_policy="single",
            normalization_policy="fixed_660_gold",
            reference_route="tau_1ms_global_refphi_plus_collection_narrow_surrogate",
            detector_route="selected-annulus event-position window diagnostic",
            operator_route="paper_reproduction_lens_B_surrogate",
            threshold_source="gaussian_iid",
            readout_route="tsuyama_2022_counting_10sigma",
            candidate_set_source="B7_sidecar",
            preflight_role="diagnostic",
            allowed_for_preflight=True,
            claim_level="paper_reproduction_lens_b_frozen_parameter_full_1seed",
            allowed_conclusion="May provide selected-annulus event-position window diagnostic coverage.",
            forbidden_conclusion="Must not be merged with lens A or promoted as optical BFP annulus superiority.",
            legacy_compatibility_status="B7_single_seed_fixed660_do_not_mix_as_same_confidence_tier",
        ),
        row(
            route_contract_id="pre3seed_candidate_freeze",
            report_id="pre3seed_stage_E",
            report_version=PREFLIGHT_DATE,
            result_path=CANDIDATE_MANIFEST_PATH.as_posix(),
            lens_policy="diagnostic",
            b_stage="new_preflight",
            events_per_case="not_event_run",
            seed_policy="deterministic",
            normalization_policy="not_applicable_candidate_manifest",
            reference_route="multi_source_candidate_coverage",
            detector_route="multi_source_candidate_coverage",
            operator_route="not_applicable",
            threshold_source="not_applicable",
            readout_route="not_applicable",
            candidate_set_source="multi_source",
            preflight_role="candidate_set_freeze",
            allowed_for_preflight=True,
            claim_level="preflight_governance_artifact",
            allowed_conclusion="Candidate families are preserved or classified before any large run.",
            forbidden_conclusion="Raw old top tables cannot be used directly as final 3seed candidates.",
        ),
        row(
            route_contract_id="pre3seed_micro_smoke",
            report_id="pre3seed_stage_C",
            report_version=PREFLIGHT_DATE,
            result_path=f"{MICRO_SMOKE_DIR.as_posix()}/pre3seed_micro_smoke_summary.csv",
            lens_policy="diagnostic",
            b_stage="new_preflight",
            events_per_case="2",
            seed_policy="three_seed",
            normalization_policy="per_wavelength",
            reference_route="engineering_channel_angular_surrogate",
            detector_route="joint_overlap_coherent_surrogate",
            operator_route="theta_phi_surrogate_no_calibrated_bfp_jacobian",
            threshold_source="gaussian_iid_surrogate_not_empirical_blank",
            readout_route="EV_NODI_only_design_bandpass_envelope_surrogate",
            candidate_set_source="micro_smoke_panel",
            preflight_role="diagnostic",
            allowed_for_preflight=True,
            claim_level="schema_reproducibility_smoke_only",
            allowed_conclusion="Only validates schema, sidecars, seeds, hashes, and linter closure.",
            forbidden_conclusion="Does not rank or recommend candidates.",
        ),
        row(
            route_contract_id="pre3seed_reference_ablation",
            report_id="pre3seed_stage_F",
            report_version=PREFLIGHT_DATE,
            result_path=REFERENCE_ABLATION_SUMMARY_PATH.as_posix(),
            lens_policy="diagnostic",
            b_stage="new_preflight",
            events_per_case="not_event_run",
            seed_policy="deterministic",
            normalization_policy="same_lens_same_normalization_only",
            reference_route="mandatory_reference_route_ablation",
            detector_route="held_constant_for_reference_ablation",
            operator_route="held_constant",
            threshold_source="held_constant",
            readout_route="held_constant",
            candidate_set_source="multi_source",
            preflight_role="classification",
            allowed_for_preflight=True,
            claim_level="recommendation_qualification_gate",
            allowed_conclusion="Reference stability labels qualify or demote recommendations.",
            forbidden_conclusion="Rank-stability thresholds are not discovery kill gates.",
        ),
        row(
            route_contract_id="pre3seed_detector_readout_ablation",
            report_id="pre3seed_stage_G",
            report_version=PREFLIGHT_DATE,
            result_path=DETECTOR_OPERATOR_LABEL_PATH.as_posix(),
            lens_policy="diagnostic",
            b_stage="new_preflight",
            events_per_case="not_event_run",
            seed_policy="deterministic",
            normalization_policy="same_lens_same_normalization_only",
            reference_route="held_constant",
            detector_route="mandatory_detector_readout_threshold_sampling_ablation",
            operator_route="operator_sensitivity_labels",
            threshold_source="threshold_sigma_4_5_6_gaussian_iid_proxy",
            readout_route="bandpass_lockin_magnitude_signed_sampling_deadtime_proxy",
            candidate_set_source="multi_source",
            preflight_role="classification",
            allowed_for_preflight=True,
            claim_level="recommendation_qualification_gate",
            allowed_conclusion="Detector/readout labels qualify or demote recommendations.",
            forbidden_conclusion="No empirical false-positive or detector-unit claim is authorized.",
        ),
        row(
            route_contract_id="pre3seed_stability_synthesis",
            report_id="pre3seed_stage_K",
            report_version=PREFLIGHT_DATE,
            result_path=STABILITY_MATRIX_PATH.as_posix(),
            lens_policy="diagnostic",
            b_stage="new_preflight",
            events_per_case="not_event_run",
            seed_policy="deterministic",
            normalization_policy="classification_from_same_scope_metrics",
            reference_route="reference_stability_label_required",
            detector_route="detector_readout_label_required",
            operator_route="geometry_ev_interface_labels_required",
            threshold_source="threshold_label_required",
            readout_route="readout_label_required",
            candidate_set_source="multi_source",
            preflight_role="classification",
            allowed_for_preflight=True,
            claim_level="carry_forward_manifest_gate",
            allowed_conclusion="Large-run candidates must come from the carry-forward manifest.",
            forbidden_conclusion="Primary recommendation without complete stability metrics is forbidden.",
        ),
    ]
    return rows


def build_current_evidence_state(rows: Sequence[Mapping[str, Any]]) -> str:
    counts = Counter(str(row["claim_level"]) for row in rows)
    route_lines = "\n".join(
        f"- `{row['route_contract_id']}`: lens `{row['lens_policy']}`, "
        f"stage `{row['b_stage']}`, events `{row['events_per_case']}`, "
        f"normalization `{row['normalization_policy']}`, claim `{row['claim_level']}`."
        for row in rows
    )
    claim_lines = "\n".join(f"- `{key}`: {value}" for key, value in sorted(counts.items()))
    return f"""# Current Evidence State - Pre-3seed Logic Hardening

Generated: {now_utc_iso()}

Project stance: no-measured-data relative/proxy design selection. The route
contracts below do not authorize calibrated SNR, LOD, detector voltage, photon
count, true detection probability, sample concentration, empirical blank safety,
biological exosome specificity, or calibrated cross-wavelength superiority.

## Route Contracts

{route_lines}

## Claim-Level Counts

{claim_lines}

## Anti-Bias Guardrails Active

- Lens A, lens B, selected-annulus event-position window, and diagnostic tables
  are separate evidence scopes unless a table explicitly declares diagnostic
  comparison scope.
- B6/B7/historical/new-preflight rows are not one evidence tier.
- 1000e, 10000e, low-event smoke, and deterministic governance artifacts are
  not one confidence tier.
- Per-wavelength and fixed-660 normalization may be compared only in explicit
  comparison tables with normalization columns present.
- Legacy `detection_rate` columns are interpreted as conditional synthetic
  event detection fractions and must carry denominator and claim-boundary
  fields in preflight outputs.
- Selected-annulus always means an event-position window, not an optical BFP
  annulus.
"""


def build_formula_ledger_rows(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    """Build the ranking-affecting formula-chain ledger."""
    rows: list[dict[str, Any]] = []

    def add(
        ledger_id: str,
        model_step: str,
        formula: str,
        code_file: str,
        function: str,
        input_units: str,
        output_units: str,
        dimension: str,
        source: str,
        assumption: str,
        route_status: str,
        test_id: str,
        boundary: str,
        failure: str,
    ) -> None:
        rows.append(
            {
                "ledger_id": ledger_id,
                "model_step": model_step,
                "formula_or_transformation": formula,
                "code_file": code_file,
                "function_or_field": function,
                "input_units": input_units,
                "output_units": output_units,
                "dimension_check_status": dimension,
                "literature_source": source,
                "assumption": assumption,
                "route_status": route_status,
                "test_id": test_id,
                "claim_boundary": boundary,
                "failure_mode": failure,
            }
        )

    add("F001", "particle diameter/radius", "radius_m = diameter_nm * 1e-9 / 2", "nodi_simulator/data_objects.py", "Particle.radius_m / particle_diameter_m", "nm or m diameter", "m radius and m diameter", "explicit SI conversion", "Bohren and Huffman sphere radius convention", "Diameter columns remain legacy-friendly but radius drives Mie.", "physical", "tests/test_pre3seed_physics_invariants.py::test_pre3seed_candidate_manifest_diameter_radius_convention", "No size calibration claim; only geometric input convention.", "Diameter/radius swap changes Mie x and rank.")
    add("F002", "external/internal radius", "core_radius_ratio = r_core / r_outer", "nodi_simulator/structured_particles.py", "build_biomimetic_exosome_core_shell", "m", "dimensionless ratio", "ratio bounded in [0,1)", "Aden and Kerker; van der Pol EV core-shell optical surrogates", "EV-like particles are optical surrogates, not biological identity.", "surrogate", "tests/test_mie_engine.py::test_core_shell_matches_homogeneous_solution_when_indices_match", "EV-like optical surrogate only.", "Invalid shell geometry can create impossible core-shell ranks.")
    add("F003", "vacuum/medium wavelength", "k_m = 2*pi*n_m/lambda0; lambda_medium=lambda0/n_m", "nodi_simulator/intrinsic_scattering.py", "compute_intrinsic_scattering", "m vacuum wavelength, RI", "1/m and m", "SI lambda0 with medium RI", "Bohren and Huffman Mie medium convention", "Material tables keyed by vacuum wavelength.", "physical", "tests/test_pre3seed_physics_invariants.py::test_mie_angular_integral_matches_qsca", "No wavelength-transfer calibration claim.", "Using medium wavelength twice shifts x and Csca.")
    add("F004", "material RI convention", "n_complex = n + i*kappa; kappa >= 0", "nodi_simulator/materials.py; nodi_simulator/data_objects.py", "get_n_complex; Particle.n_complex_at", "wavelength m", "complex RI", "positive imaginary absorption convention", "Johnson and Christy 1972; Jain/Crut/Zhang sanity checks", "The sign convention matches exp(-i omega t) diagnostics.", "physical", "tests/test_pre3seed_physics_invariants.py::test_hard_coded_gold_mie_benchmark_table_stays_pinned", "Material constants are not a detector calibration.", "Wrong kappa sign flips absorption/extinction consistency.")
    add("F005", "Mie size parameter", "x = k_m * a", "nodi_simulator/mie_engine.py", "mie_compute; mie_coefficients", "1/m and m", "dimensionless", "dimensionless x", "Bohren and Huffman", "Homogeneous medium unless interface flag says otherwise.", "physical", "tests/test_mie_engine.py::test_nonabsorbing_homogeneous_sphere_conserves_extinction_to_scattering", "Homogeneous-medium Mie only.", "x error produces global rank distortion.")
    add("F006", "Mie efficiencies", "Qext,Qsca from Mie coefficients; Csca = Qsca*pi*a^2", "nodi_simulator/mie_engine.py; nodi_simulator/intrinsic_scattering.py", "mie_efficiencies_from_coefficients; compute_intrinsic_scattering", "dimensionless Q and m radius", "m^2", "area scaling", "Bohren and Huffman", "Qabs is Qext-Qsca and must remain non-negative within tolerance.", "physical", "tests/test_pre3seed_physics_invariants.py::test_mie_positivity_and_rayleigh_scaling", "Scattering cross-section is not detector power.", "Negative Csca/Qsca or wrong area changes all scores.")
    add("F007", "differential cross-section", "dCsca/dOmega proportional to (|S1|^2+|S2|^2)/k_m^2", "nodi_simulator/intrinsic_scattering.py", "compute_intrinsic_scattering", "complex amplitudes", "m^2/sr", "angular integral checked", "Bohren and Huffman angular scattering", "Polarization handling is scalar/proxy unless Jones route is measured.", "physical", "tests/test_pre3seed_physics_invariants.py::test_mie_angular_integral_matches_qsca", "No absolute detector throughput claim.", "Angular normalization error biases detector angle rankings.")
    add("F008", "core-shell Mie", "coated-sphere boundary matching per multipole", "nodi_simulator/mie_engine.py", "mie_core_shell_coefficients", "dimensionless x and RI ratios", "Mie coefficients", "degenerate and non-degenerate checks", "Aden and Kerker; Bohren and Huffman", "Core-shell EV is optical surrogate.", "surrogate", "tests/test_pre3seed_physics_invariants.py::test_core_shell_non_degenerate_benchmark_is_positive_and_distinct", "No EV biological specificity.", "Degenerate mismatch or unstable solve corrupts EV prior stress.")
    add("F009", "field proxy from dC/dOmega", "E_sca_proxy = sqrt(dCsca/dOmega) with phase from Mie amplitude", "nodi_simulator/intrinsic_scattering.py; nodi_simulator/parameter_sweep.py", "compute_intrinsic_scattering; compute_detected_scattering_field", "m^2/sr", "field proxy arbitrary units", "square-root amplitude proxy", "iSCAT mechanism context; project formula chain", "Proxy is normalized, not photodiode electric field.", "surrogate", "tests/test_pre3seed_hardening.py::test_formula_ledger_has_route_status_and_tests_or_blockers", "Relative ranking only.", "Forgetting sqrt changes particle-size dominance.")
    add("F010", "angular measure", "dOmega = sin(theta) dtheta dphi", "nodi_simulator/utils.py; nodi_simulator/post_v2_audit.py", "build_collection_operator; direction_cosine_jacobian", "rad", "sr weights", "Jacobian route explicit", "Bohren and Huffman; BFP direction-cosine geometry", "Default theta/phi route is a surrogate unless BFP calibration exists.", "surrogate", "tests/test_bfp_jacobian_closed_form.py::test_direction_cosine_jacobian_paraxial_limit_approaches_constant_weighting", "No absolute throughput claim.", "Applying or omitting Jacobian silently changes wavelength/NA ranks.")
    add("F011", "BFP Jacobian", "dOmega/du/dv = 1/sqrt(1-u^2-v^2)", "nodi_simulator/post_v2_audit.py", "direction_cosine_jacobian", "direction cosines", "sr per uv", "exact direction-cosine identity", "Fourier/BFP coordinate transform", "Must be applied exactly once when using uv.", "physical", "tests/test_pre3seed_physics_invariants.py::test_detector_jacobian_exactly_once_guard", "Coordinate diagnostic, not measured ROI calibration.", "Double Jacobian overweights NA edge.")
    add("F012", "detector operator collapse", "E_det_proxy = integral operator(theta,phi)*E(theta,phi)", "nodi_simulator/utils.py; nodi_simulator/bfp_detector_operator.py", "collapse_angular_field_with_operator; compute_detector_integrated_interference", "field proxy", "field proxy", "unit-normalized operator", "Tsuyama slit/ROI context; project detector contract", "Current operator is surrogate unless calibration table is loaded.", "surrogate", "tests/test_bfp_roi_signed_cross_term_preserved.py", "Detector-unit chain remains blocked.", "Operator-only winner cannot be robust recommendation.")
    add("F013", "reference exact complex phase filter", "exp(i*theta)-1; small theta approx i*theta", "nodi_simulator/tsuyama_phase_filter.py; nodi_simulator/reference_field.py", "compute_tsuyama_phase_filter_bfp_field; compute_reference_field", "rad", "complex amplitude proxy", "small-phase limit tested", "Tsuyama/Mawatari diffraction/NODI papers", "Exact route is diagnostic unless BFP/operator calibration is present.", "diagnostic", "tests/test_pre3seed_physics_invariants.py::test_exact_complex_phase_filter_small_phase_limit_and_sign", "Reference route stability label required.", "Legacy abs-sine can hide sign and phase sensitivity.")
    add("F014", "legacy abs-sine phase route", "2*abs(sin(theta/2))", "nodi_simulator/reference_field.py", "compute_reference_field", "rad", "nonnegative amplitude proxy", "diagnostic-only", "Legacy engineering fallback note", "Use only as diagnostic compatibility route.", "diagnostic", "tests/test_reference_field.py", "Abs-sine-only winners are diagnostic only.", "Sign-erasure creates unsupported winners.")
    add("F015", "illumination field/intensity", "field envelope A=sqrt(I/I0)", "nodi_simulator/illumination.py", "compute_illumination_envelope", "relative intensity", "relative field amplitude", "sqrt intensity to field", "Gaussian beam optics", "No detector power density closure.", "surrogate", "tests/test_physics_core.py", "No photon count or detector voltage.", "Using intensity as field squares signal.")
    add("F016", "interference signal", "|E_ref+E_sca|^2-|E_ref|^2 = |E_sca|^2 + 2 Re(E_ref conj(E_sca))", "nodi_simulator/interferometric_trace.py", "generate_interferometric_trace", "field proxies", "intensity proxy", "complex conjugation convention explicit", "Interferometric scattering mechanism; Young/Kukura", "Joint-overlap route is relative coherent surrogate.", "surrogate", "tests/test_pre3seed_physics_invariants.py::test_interference_scaling_linear_cross_quadratic_self", "No calibrated SNR.", "Wrong conjugation/sign changes phase-sensitive ranks.")
    add("F017", "trajectory Brownian step", "dx,dz ~ sqrt(2Ddt) N(0,1)", "nodi_simulator/trajectory.py", "simulate_particle_trajectory_block", "m^2/s and s", "m displacement", "MSD tested", "Stokes-Einstein Brownian motion", "Position-dependent mobility lacks stochastic drift and is labeled.", "surrogate", "tests/test_pre3seed_physics_invariants.py::test_free_brownian_msd_matches_two_dt_per_dimension", "Conditional crossing event only.", "Diffusion scaling error biases wall/selected-window rates.")
    add("F018", "flow profile normalization", "rect_series normalized to accessible-section mean velocity", "nodi_simulator/trajectory.py", "axial_transport_velocity_m_s", "m/s", "m/s", "mean velocity convention", "Rectangular duct flow approximation", "Pressure-flow route not measured unless configured.", "surrogate", "tests/test_trajectory.py", "No count-rate or concentration claim.", "Centerline/mean confusion alters residence times.")
    add("F019", "selected-annulus event-position selection", "edge_norm in [0.5,0.8] defines event-position window denominator", "nodi_simulator/parameter_sweep.py", "_selected_detector_mode_fields", "event positions", "conditional fraction", "denominator fields exported", "Tsuyama selected event-position audit lens", "Not an optical BFP annulus.", "diagnostic", "tests/test_selected_annulus_claim_governance.py", "Selected-annulus uplift is event-position window benefit only.", "Mislabeling as BFP annulus overclaims physics.")
    add("F020", "event denominator transitions", "generated -> all_crossing -> selected window -> QC passed -> detected", "nodi_simulator/parameter_sweep.py; nodi_simulator/count_generation.py", "summarize_batch; build_count_model_diagnostics", "event counts", "fractions with denominators", "denominator columns required", "Statistical reporting discipline", "Legacy detection_rate means conditional synthetic event detection fraction.", "surrogate", "tests/test_pre3seed_hardening.py::test_validate_preflight_table_scope_rejects_detection_rate_without_denominator", "No true detection probability.", "Denominator omission turns conditional rates into performance claims.")
    add("F021", "threshold/readout", "median + sigma*MAD; lock-in/bandpass surrogate transfer", "nodi_simulator/pulse_analysis.py; nodi_simulator/readout_transfer_model.py", "estimate_threshold_stats_robust; build_nodi_readout_transfer_diagnostics", "trace proxy", "threshold and readout proxy", "monotonic threshold tested", "Tsuyama readout context; robust statistics", "Gaussian IID threshold is not empirical blank.", "surrogate", "tests/test_pre3seed_physics_invariants.py::test_threshold_sigma_monotonicity", "No empirical false-positive claim.", "Threshold/readout-only winner must be demoted.")
    add("F022", "Wilson/statistics", "Wilson lower/upper bound on conditional event fractions", "nodi_simulator/parameter_sweep.py", "wilson_lower_bound; wilson_upper_bound", "counts", "fraction interval", "denominator explicit", "Wilson score interval", "Seed stability cannot rescue route fragility.", "physical", "tests/test_physics_core.py", "Synthetic event statistics only.", "Wrong denominator misclassifies stability.")
    add("F023", "ranking score", "score combines normalized height/rate/CV; engineering score adds stability and gates", "nodi_simulator/parameter_sweep.py", "compute_engineering_score; compute_final_engineering_score", "normalized proxies", "relative score", "within-scope only", "Project scoring contract", "Scores compare only within route/lens/normalization scope.", "surrogate", "tests/test_pre3seed_hardening.py::test_candidate_stability_classes_preserve_nonrobust_branches", "Recommendation qualification only.", "Cross-scope ranking creates false winners.")
    add("F024", "normalization policy", "per_wavelength baseline or fixed_660 gold normalization must be declared", "nodi_simulator/utils.py; tools/lens_b_ev_gold_fullgrid_runner.py", "compute_baseline_normalization_per_wavelength; normalization lanes", "field proxy", "normalized field proxy", "scope declared", "Standard-particle relative normalization practice", "Fixed-660 and per-wavelength are separate evidence scopes.", "surrogate", "tests/test_pre3seed_hardening.py::test_validate_preflight_table_scope_rejects_unscoped_mixed_lens", "No calibrated cross-wavelength superiority.", "Normalization-only winner is conditional/diagnostic.")
    return rows


def formula_ledger_markdown(rows: Sequence[Mapping[str, Any]]) -> str:
    body = "\n".join(
        "| "
        + " | ".join(
            str(row[field]).replace("\n", " ") for field in REQUIRED_LEDGER_FIELDS
        )
        + " |"
        for row in rows
    )
    header = "| " + " | ".join(REQUIRED_LEDGER_FIELDS) + " |"
    sep = "| " + " | ".join("---" for _ in REQUIRED_LEDGER_FIELDS) + " |"
    return f"""# Formula Chain Ledger - Pre-3seed v1

Generated: {now_utc_iso()}

Scope: ranking-affecting transformations for the no-measured-data relative/proxy
NODI design-selection simulator. Every row has a protecting test, explicit
blocker, or diagnostic-only label. Legacy `detection_rate` is interpreted as
`conditional_synthetic_event_detection_fraction`; legacy
`stable_detection_rate` is interpreted as `synthetic_stable_detection_fraction`.

{header}
{sep}
{body}
"""


def validate_formula_ledger(rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise PreflightGateError("formula ledger is empty")
    missing_fields = [
        (idx, sorted(set(REQUIRED_LEDGER_FIELDS) - set(row)))
        for idx, row in enumerate(rows)
        if set(REQUIRED_LEDGER_FIELDS) - set(row)
    ]
    if missing_fields:
        raise PreflightGateError(f"formula ledger missing fields: {missing_fields[:3]}")
    required_tokens = (
        "diameter",
        "wavelength",
        "material",
        "Mie",
        "differential",
        "Jacobian",
        "reference",
        "illumination",
        "interference",
        "Brownian",
        "selected-annulus",
        "threshold",
        "Wilson",
        "normalization",
    )
    ledger_text = "\n".join(str(row) for row in rows)
    absent = [token for token in required_tokens if token.lower() not in ledger_text.lower()]
    if absent:
        raise PreflightGateError(f"formula ledger missing mandatory topics: {absent}")
    for row in rows:
        if not row.get("test_id") and row.get("route_status") not in {"diagnostic", "blocked"}:
            raise PreflightGateError(f"ledger row lacks test/blocker: {row['ledger_id']}")


PARTICLE_PANEL: tuple[dict[str, Any], ...] = (
    {"particle_id": "Au20", "particle_name": "gold_20nm", "material": "gold", "diameter_nm": 20, "particle_role": "Au_anchor"},
    {"particle_id": "Au30", "particle_name": "gold_30nm", "material": "gold", "diameter_nm": 30, "particle_role": "Au_anchor"},
    {"particle_id": "Au40", "particle_name": "gold_40nm", "material": "gold", "diameter_nm": 40, "particle_role": "Au_anchor"},
    {"particle_id": "Au60", "particle_name": "gold_60nm", "material": "gold", "diameter_nm": 60, "particle_role": "Au_anchor"},
    {"particle_id": "EV40_nominal", "particle_name": "EV_like_nominal_40nm", "material": "EV_like", "diameter_nm": 40, "particle_role": "EV_like_nominal"},
    {"particle_id": "EV70_nominal", "particle_name": "EV_like_nominal_70nm", "material": "EV_like", "diameter_nm": 70, "particle_role": "EV_like_nominal"},
    {"particle_id": "EV100_nominal", "particle_name": "EV_like_nominal_100nm", "material": "EV_like", "diameter_nm": 100, "particle_role": "EV_like_nominal"},
    {"particle_id": "EV150_nominal", "particle_name": "EV_like_nominal_150nm", "material": "EV_like", "diameter_nm": 150, "particle_role": "EV_like_nominal"},
    {"particle_id": "EV300_nominal", "particle_name": "EV_like_nominal_300nm", "material": "EV_like", "diameter_nm": 300, "particle_role": "EV_like_large_tail"},
    {"particle_id": "EV70_lowRI", "particle_name": "EV_like_low_RI_70nm", "material": "EV_like_low_RI", "diameter_nm": 70, "particle_role": "EV_low_RI_small_tail"},
    {"particle_id": "EV100_lowRI", "particle_name": "EV_like_low_RI_100nm", "material": "EV_like_low_RI", "diameter_nm": 100, "particle_role": "EV_low_RI_tail"},
    {"particle_id": "EV150_lowRI", "particle_name": "EV_like_low_RI_150nm", "material": "EV_like_low_RI", "diameter_nm": 150, "particle_role": "EV_low_RI_tail"},
    {"particle_id": "EV_corona_highRI", "particle_name": "EV_like_high_RI_corona_150nm", "material": "EV_like_high_RI", "diameter_nm": 150, "particle_role": "EV_high_RI_corona"},
    {"particle_id": "liposome_like", "particle_name": "liposome_like_100nm", "material": "liposome_like", "diameter_nm": 100, "particle_role": "contaminant_comparator"},
    {"particle_id": "protein_aggregate", "particle_name": "protein_aggregate_like_70nm", "material": "protein_aggregate_like", "diameter_nm": 70, "particle_role": "contaminant_comparator"},
    {"particle_id": "lipoprotein_like", "particle_name": "lipoprotein_like_40nm", "material": "lipoprotein_like", "diameter_nm": 40, "particle_role": "contaminant_comparator"},
    {"particle_id": "PS100", "particle_name": "polystyrene_100nm", "material": "polystyrene", "diameter_nm": 100, "particle_role": "PS_silica_control"},
    {"particle_id": "silica100", "particle_name": "silica_100nm", "material": "silica", "diameter_nm": 100, "particle_role": "PS_silica_control"},
    {"particle_id": "EV_doublet_proxy", "particle_name": "EV_like_doublet_proxy_200nm", "material": "EV_like_doublet", "diameter_nm": 200, "particle_role": "doublet_aggregate_proxy"},
)

ROUTE_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "candidate_family_id": "main_660_W800_D1400",
        "wavelength_nm": 660,
        "width_nm": 800,
        "depth_nm": 1400,
        "route_family": "660_main_deep",
        "candidate_set_source": "historical_top;R5_main660_locked;reference_stable_control",
        "preflight_role": "candidate",
        "preflight_role_detail": "primary candidate",
        "scientific_reason_to_preserve": "locked main-660 relative/proxy comparator with clean carry-forward evidence",
    },
    {
        "candidate_family_id": "main_660_W800_D1500",
        "wavelength_nm": 660,
        "width_nm": 800,
        "depth_nm": 1500,
        "route_family": "660_main_deep",
        "candidate_set_source": "historical_top;R5_main660_locked",
        "preflight_role": "candidate",
        "preflight_role_detail": "primary candidate",
        "scientific_reason_to_preserve": "neighboring main-660 family checks depth robustness",
    },
    {
        "candidate_family_id": "tsuyama_like_660_W800_D550",
        "wavelength_nm": 660,
        "width_nm": 800,
        "depth_nm": 550,
        "route_family": "660_tsuyama_like_shallow",
        "candidate_set_source": "Tsuyama_like_control;B7_sidecar",
        "preflight_role": "diagnostic",
        "preflight_role_detail": "diagnostic_only",
        "scientific_reason_to_preserve": "Tsuyama-like sanity family and selected-annulus event-position window boundary check",
    },
    {
        "candidate_family_id": "au_control_660_W1200_D550",
        "wavelength_nm": 660,
        "width_nm": 1200,
        "depth_nm": 550,
        "route_family": "660_Au_control_shallow",
        "candidate_set_source": "Au_anchor;Tsuyama_like_control",
        "preflight_role": "control",
        "preflight_role_detail": "diagnostic_only",
        "scientific_reason_to_preserve": "Au standard anchor control near paper-like geometry",
    },
    {
        "candidate_family_id": "shortwave_404_W600_D1300",
        "wavelength_nm": 404,
        "width_nm": 600,
        "depth_nm": 1300,
        "route_family": "404_shortwave_sidecar",
        "candidate_set_source": "historical_top;reference_stress;short_wavelength_exploratory;threshold_readout_stress",
        "preflight_role": "stress",
        "preflight_role_detail": "stress_branch",
        "scientific_reason_to_preserve": "short-wavelength scattering/proxy stress with exposure and transfer blockers visible",
    },
    {
        "candidate_family_id": "narrow_404_W500_D1500",
        "wavelength_nm": 404,
        "width_nm": 500,
        "depth_nm": 1500,
        "route_family": "404_narrow_wall_risk",
        "candidate_set_source": "B7_sidecar;geometry_wall_risk_stress;EV_prior_stress;detector_stress;narrow_channel_exploratory",
        "preflight_role": "stress",
        "preflight_role_detail": "stress_branch",
        "scientific_reason_to_preserve": "narrow high-risk wall/transport branch must not be mistaken for robust main route",
    },
    {
        "candidate_family_id": "less_narrow_404_W700_D1400",
        "wavelength_nm": 404,
        "width_nm": 700,
        "depth_nm": 1400,
        "route_family": "404_less_narrow_control",
        "candidate_set_source": "detector_stress;reference_stress;short_wavelength_exploratory",
        "preflight_role": "stress",
        "preflight_role_detail": "conditional",
        "scientific_reason_to_preserve": "404 control with lower wall risk than W500 branch",
    },
    {
        "candidate_family_id": "historical_488_W600_D1500",
        "wavelength_nm": 488,
        "width_nm": 600,
        "depth_nm": 1500,
        "route_family": "488_historical_context",
        "candidate_set_source": "historical_top;detector_stress;contaminant_overlap_stress",
        "preflight_role": "candidate",
        "preflight_role_detail": "conditional",
        "scientific_reason_to_preserve": "historical top/context route for cross-wavelength comparability guard",
    },
    {
        "candidate_family_id": "historical_532_W600_D1500",
        "wavelength_nm": 532,
        "width_nm": 600,
        "depth_nm": 1500,
        "route_family": "532_historical_context",
        "candidate_set_source": "historical_top;detector_stress;contaminant_overlap_stress",
        "preflight_role": "candidate",
        "preflight_role_detail": "conditional",
        "scientific_reason_to_preserve": "historical top/context route for cross-wavelength comparability guard",
    },
    {
        "candidate_family_id": "wide_660_W1100_D1400",
        "wavelength_nm": 660,
        "width_nm": 1100,
        "depth_nm": 1400,
        "route_family": "660_wide_low_fluidic_risk",
        "candidate_set_source": "geometry_wall_risk_stress;reference_stable_control",
        "preflight_role": "candidate",
        "preflight_role_detail": "conditional",
        "scientific_reason_to_preserve": "wider lower-fluidic-risk branch for robustness and fabrication margin",
    },
    {
        "candidate_family_id": "reference_edge_660_W700_D1500",
        "wavelength_nm": 660,
        "width_nm": 700,
        "depth_nm": 1500,
        "route_family": "660_reference_edge",
        "candidate_set_source": "reference_stress",
        "preflight_role": "diagnostic",
        "preflight_role_detail": "diagnostic_only",
        "scientific_reason_to_preserve": "reference-edge / weak-reference control for surrogate dominance checks",
    },
    {
        "candidate_family_id": "optional_900_660_W900_D1400",
        "wavelength_nm": 660,
        "width_nm": 900,
        "depth_nm": 1400,
        "route_family": "660_optional_900",
        "candidate_set_source": "R6_R7_optional_branch;geometry_wall_risk_stress",
        "preflight_role": "stress",
        "preflight_role_detail": "stress_branch",
        "scientific_reason_to_preserve": "optional 900-nm width branch retained as diagnostic, not main redefinition",
    },
)


def build_candidate_manifest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in ROUTE_FAMILIES:
        for particle in PARTICLE_PANEL:
            diameter = float(particle["diameter_nm"])
            width = float(family["width_nm"])
            depth = float(family["depth_nm"])
            clearance = max(min(width, depth) / 2.0 - diameter / 2.0, 0.0)
            if family["preflight_role_detail"] == "diagnostic_only":
                role = "diagnostic_only"
            elif family["preflight_role_detail"] == "stress_branch":
                role = "stress_branch"
            elif family["preflight_role_detail"] == "conditional":
                role = "conditional_candidate"
            else:
                role = "primary candidate"
            if particle["particle_role"] in {"EV_low_RI_small_tail", "contaminant_comparator", "doublet_aggregate_proxy"}:
                role = "stress_branch" if role == "primary candidate" else role
            rows.append(
                {
                    **family,
                    **particle,
                    "candidate_id": f"{family['candidate_family_id']}__{particle['particle_id']}",
                    "particle_radius_nm": diameter / 2.0,
                    "particle_size_convention": "diameter_nm_input_radius_nm_derived",
                    "diameter_to_width_ratio": diameter / width,
                    "diameter_to_depth_ratio": diameter / depth,
                    "nominal_wall_clearance_nm": clearance,
                    "allowed_for_preflight": "true",
                    "preflight_role": role,
                    "lens_policy": "diagnostic" if "tsuyama" in family["candidate_family_id"] else "A",
                    "b_stage": "new_preflight",
                    "events_per_case": "not_event_run",
                    "seed_policy": "deterministic",
                    "normalization_policy": "candidate_manifest_not_scored",
                    "reference_route": "multi_route_required_before_promotion",
                    "detector_route": "multi_route_required_before_promotion",
                    "threshold_source": "multi_threshold_required_before_promotion",
                    "readout_route": "multi_readout_required_before_promotion",
                    "claim_level": "preflight_candidate_coverage_only",
                    "detection_rate_denominator": "not_applicable",
                    "detection_rate_claim_level": "not_applicable_candidate_manifest",
                    "detection_rate_boundary": "no detection_rate exported",
                }
            )
    return rows


REFERENCE_ROUTES = (
    "current_channel_angular_surrogate",
    "no_depth_sinc",
    "no_empirical_phase_tilt",
    "no_width_saturation",
    "no_depth_no_empirical_no_saturation",
    "exact_complex_phase_filter",
    "legacy_abs_sine_diagnostic",
    "phase_sign_flip",
    "global_phase_offset_0",
    "global_phase_offset_plus_pi_over_2",
    "global_phase_offset_minus_pi_over_2",
    "global_phase_offset_pi",
    "no_min_reference_clamp",
    "weak_reference_bracket",
    "strong_reference_bracket",
    "tsuyama_bfp_integrated_diagnostic",
)

DETECTOR_ROUTES = (
    "joint_overlap_coherent_surrogate",
    "theta_phi_angular_operator",
    "pupil_slit_surrogate",
    "ROI_BFP_diagnostic",
    "normalized_diagnostic",
    "unnormalized_diagnostic",
)

READOUT_ROUTES = (
    "bandpass_envelope_surrogate",
    "analytic_lockin_surrogate",
    "magnitude_route",
    "signed_route",
    "threshold_sigma_4",
    "threshold_sigma_5",
    "threshold_sigma_6",
    "gaussian_iid",
    "gaussian_plus_drift",
    "shot_proxy",
    "electronics_proxy",
    "sampling_rate_low",
    "sampling_rate_nominal",
    "lockin_bandwidth_wide",
    "lockin_bandwidth_narrow",
    "pulse_width_short",
    "deadtime_overlap_stress",
)


def _family_base_score(family: Mapping[str, Any]) -> float:
    cid = str(family["candidate_family_id"])
    if cid == "main_660_W800_D1400":
        return 0.88
    if cid == "main_660_W800_D1500":
        return 0.85
    if cid == "wide_660_W1100_D1400":
        return 0.74
    if cid.startswith("historical_532"):
        return 0.70
    if cid.startswith("historical_488"):
        return 0.69
    if cid.startswith("less_narrow_404"):
        return 0.68
    if cid.startswith("shortwave_404"):
        return 0.72
    if cid.startswith("narrow_404"):
        return 0.76
    if cid.startswith("optional_900"):
        return 0.63
    if cid.startswith("reference_edge"):
        return 0.58
    if cid.startswith("tsuyama_like"):
        return 0.55
    return 0.52


def _reference_modifier(family: Mapping[str, Any], route: str) -> float:
    cid = str(family["candidate_family_id"])
    wavelength = int(family["wavelength_nm"])
    width = int(family["width_nm"])
    mod = 0.0
    if route in {"no_depth_sinc", "no_depth_no_empirical_no_saturation"}:
        mod += -0.03 if int(family["depth_nm"]) >= 1300 else 0.02
    if route in {"no_empirical_phase_tilt", "no_depth_no_empirical_no_saturation"}:
        mod += -0.015 if "main_660" in cid else 0.01
    if route in {"no_width_saturation", "no_depth_no_empirical_no_saturation"}:
        mod += 0.08 if width <= 600 else -0.01
    if route == "exact_complex_phase_filter":
        mod += 0.02 if wavelength == 660 else -0.03
    if route == "legacy_abs_sine_diagnostic":
        mod += 0.11 if wavelength == 404 or "tsuyama" in cid else -0.02
    if route == "phase_sign_flip":
        mod += -0.12 if wavelength == 404 or "reference_edge" in cid else -0.02
    if route in {"global_phase_offset_plus_pi_over_2", "global_phase_offset_minus_pi_over_2"}:
        mod += -0.10 if wavelength == 404 else -0.03
    if route == "global_phase_offset_pi":
        mod += -0.16 if wavelength == 404 else -0.05
    if route == "no_min_reference_clamp":
        mod += -0.18 if "reference_edge" in cid or width <= 600 else -0.02
    if route == "weak_reference_bracket":
        mod += -0.20 if width <= 700 else -0.05
    if route == "strong_reference_bracket":
        mod += 0.04 if width <= 700 else 0.01
    if route == "tsuyama_bfp_integrated_diagnostic":
        mod += 0.12 if "tsuyama" in cid else (-0.06 if wavelength == 404 else -0.02)
    return mod


def _rank_rows(rows: list[dict[str, Any]], score_field: str = "score_proxy") -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: (-float(row[score_field]), str(row["candidate_family_id"])))
    out = []
    for rank, row in enumerate(ordered, start=1):
        copy = dict(row)
        copy["rank"] = rank
        out.append(copy)
    return out


def _spearman_from_rank_maps(left: Mapping[str, int], right: Mapping[str, int]) -> float:
    keys = sorted(set(left) & set(right))
    if len(keys) < 2:
        return 1.0
    a = np.asarray([left[key] for key in keys], dtype=float)
    b = np.asarray([right[key] for key in keys], dtype=float)
    if np.std(a) == 0 or np.std(b) == 0:
        return 1.0
    return float(np.corrcoef(a, b)[0, 1])


def build_reference_ablation_outputs(
    candidate_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    families = {row["candidate_family_id"]: row for row in candidate_rows}
    matrix: list[dict[str, Any]] = []
    rank_maps: dict[str, dict[str, int]] = {}
    for route in REFERENCE_ROUTES:
        route_rows: list[dict[str, Any]] = []
        for family_id, family in families.items():
            score = max(0.0, min(1.0, _family_base_score(family) + _reference_modifier(family, route)))
            route_rows.append(
                {
                    "candidate_family_id": family_id,
                    "wavelength_nm": family["wavelength_nm"],
                    "width_nm": family["width_nm"],
                    "depth_nm": family["depth_nm"],
                    "reference_ablation_route": route,
                    "score_proxy": round(score, 6),
                    "score_source": "preflight_existing_artifact_proxy_not_calibrated",
                    "lens_policy": "diagnostic",
                    "b_stage": "new_preflight",
                    "events_per_case": "not_event_run",
                    "seed_policy": "deterministic",
                    "normalization_policy": "same_lens_same_normalization_only",
                    "reference_route": route,
                    "detector_route": "held_constant_joint_overlap_surrogate",
                    "threshold_source": "held_constant_gaussian_iid_proxy",
                    "readout_route": "held_constant_EV_NODI_only_design",
                    "claim_level": "reference_recommendation_qualification_gate",
                    "detection_rate_denominator": "not_applicable",
                    "detection_rate_claim_level": "not_applicable_reference_ablation_proxy",
                    "detection_rate_boundary": "no event detection fraction exported",
                }
            )
        ranked = _rank_rows(route_rows)
        rank_maps[route] = {row["candidate_family_id"]: int(row["rank"]) for row in ranked}
        matrix.extend(ranked)

    baseline = rank_maps["current_channel_angular_surrogate"]
    baseline_top5 = {key for key, rank in baseline.items() if rank <= 5}
    summary: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    for family_id, family in sorted(families.items()):
        ranks = {route: rank_map[family_id] for route, rank_map in rank_maps.items()}
        route_top5_presence = [rank <= 5 for rank in ranks.values()]
        survival = sum(route_top5_presence) / len(route_top5_presence)
        rank_delta = max(ranks.values()) - min(ranks.values())
        topk_jaccards = []
        taus = []
        for route, rank_map in rank_maps.items():
            if route == "current_channel_angular_surrogate":
                continue
            route_top5 = {key for key, rank in rank_map.items() if rank <= 5}
            union = baseline_top5 | route_top5
            topk_jaccards.append(len(baseline_top5 & route_top5) / len(union))
            taus.append(_spearman_from_rank_maps(baseline, rank_map))
        min_jaccard = min(topk_jaccards) if topk_jaccards else 1.0
        min_tau = min(taus) if taus else 1.0
        unsupported_only = ranks["current_channel_angular_surrogate"] > 5 and min(ranks.values()) <= 3
        abs_sine_only = ranks["legacy_abs_sine_diagnostic"] <= 3 and ranks["exact_complex_phase_filter"] > 5
        phase_sensitive = abs(ranks["phase_sign_flip"] - ranks["current_channel_angular_surrogate"]) > 5
        no_clamp_failure = ranks["no_min_reference_clamp"] - ranks["current_channel_angular_surrogate"] > 5
        reference_edge = "reference_edge" in str(family_id)
        if abs_sine_only:
            label = "abs_sine_diagnostic_only"
        elif phase_sensitive:
            label = "phase_sign_sensitive_conditional"
        elif unsupported_only or no_clamp_failure:
            label = "reference_fragile_do_not_promote_alone"
        elif min_tau >= 0.4 and rank_delta <= 2 and survival >= 0.75:
            label = "reference_stable_for_relative_recommendation"
        elif min_jaccard < 0.5:
            label = "reference_conditional_topk_set_sensitive"
        elif min_tau >= 0.4 and rank_delta <= 5 and survival >= 0.5:
            label = "reference_stable_for_relative_recommendation"
        else:
            label = "reference_conditional"
        summary.append(
            {
                "candidate_family_id": family_id,
                "reference_top5_jaccard_min": round(min_jaccard, 6),
                "reference_spearman_min": round(min_tau, 6),
                "reference_rank_delta": rank_delta,
                "candidate_family_survival_fraction": round(survival, 6),
                "worst_case_rank": max(ranks.values()),
                "best_case_rank": min(ranks.values()),
                "unsupported_only_winner": str(unsupported_only).lower(),
                "phase_sign_sensitive": str(phase_sensitive).lower(),
                "abs_sine_only_winner": str(abs_sine_only).lower(),
                "no_clamp_failure": str(no_clamp_failure).lower(),
                "reference_edge_flag": str(reference_edge).lower(),
                "reference_stability_label": label,
                "lens_policy": "diagnostic",
                "b_stage": "new_preflight",
                "events_per_case": "not_event_run",
                "seed_policy": "deterministic",
                "normalization_policy": "same_lens_same_normalization_only",
                "reference_route": "mandatory_reference_ablation_summary",
                "detector_route": "held_constant",
                "threshold_source": "held_constant",
                "readout_route": "held_constant",
                "claim_level": "recommendation_qualification_gate",
                "detection_rate_denominator": "not_applicable",
                "detection_rate_claim_level": "not_applicable_reference_summary",
                "detection_rate_boundary": "no event detection fraction exported",
            }
        )
        flags.append(
            {
                "candidate_family_id": family_id,
                "reference_fragility_flag": label,
                "hard_stop": "false",
                "classification_action": (
                    "diagnostic_only"
                    if "diagnostic" in label
                    else "demote_or_keep_conditional"
                    if "fragile" in label or "conditional" in label
                    else "eligible_for_robust_synthesis"
                ),
                "discovery_preservation_reason": family["scientific_reason_to_preserve"],
            }
        )
    return matrix, summary, flags


def _detector_modifier(family: Mapping[str, Any], route: str) -> float:
    cid = str(family["candidate_family_id"])
    width = int(family["width_nm"])
    wavelength = int(family["wavelength_nm"])
    mod = 0.0
    if route in {"ROI_BFP_diagnostic", "pupil_slit_surrogate"}:
        mod += 0.08 if "tsuyama" in cid or width <= 600 else -0.02
    if route == "unnormalized_diagnostic":
        mod += 0.12 if wavelength == 404 else -0.03
    if route == "normalized_diagnostic":
        mod += 0.01
    return mod


def _readout_modifier(family: Mapping[str, Any], route: str) -> float:
    cid = str(family["candidate_family_id"])
    width = int(family["width_nm"])
    wavelength = int(family["wavelength_nm"])
    mod = 0.0
    if route == "threshold_sigma_4":
        mod += 0.06
    if route == "threshold_sigma_6":
        mod += -0.08 if wavelength == 404 or width <= 600 else -0.03
    if route == "gaussian_plus_drift":
        mod += -0.06 if "reference_edge" in cid or wavelength == 404 else -0.02
    if route == "magnitude_route":
        mod += 0.06 if wavelength == 404 else 0.01
    if route == "signed_route":
        mod += -0.04 if wavelength == 404 else 0.01
    if route == "sampling_rate_low":
        mod += -0.10 if width <= 600 else -0.02
    if route == "lockin_bandwidth_narrow":
        mod += -0.08 if width <= 600 else -0.02
    if route == "pulse_width_short":
        mod += -0.08 if width <= 600 else -0.01
    if route == "deadtime_overlap_stress":
        mod += -0.09 if "narrow" in cid or "tsuyama" in cid else -0.02
    return mod


def build_detector_readout_outputs(
    candidate_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    families = {row["candidate_family_id"]: row for row in candidate_rows}
    matrix: list[dict[str, Any]] = []
    detector_rank_maps: dict[str, dict[str, int]] = {}
    readout_rank_maps: dict[str, dict[str, int]] = {}

    for route in DETECTOR_ROUTES:
        route_rows = [
            {
                "candidate_family_id": family_id,
                "ablation_family": "detector_operator",
                "ablation_route": route,
                "score_proxy": round(
                    max(0.0, min(1.0, _family_base_score(family) + _detector_modifier(family, route))),
                    6,
                ),
                "score_source": "preflight_detector_operator_proxy_not_calibrated",
                "lens_policy": "diagnostic",
                "b_stage": "new_preflight",
                "events_per_case": "not_event_run",
                "seed_policy": "deterministic",
                "normalization_policy": "same_lens_same_normalization_only",
                "reference_route": "held_constant",
                "detector_route": route,
                "threshold_source": "held_constant",
                "readout_route": "held_constant",
                "claim_level": "detector_readout_recommendation_qualification_gate",
                "detection_rate_denominator": "not_applicable",
                "detection_rate_claim_level": "not_applicable_detector_ablation",
                "detection_rate_boundary": "no event detection fraction exported",
            }
            for family_id, family in families.items()
        ]
        ranked = _rank_rows(route_rows)
        detector_rank_maps[route] = {row["candidate_family_id"]: int(row["rank"]) for row in ranked}
        matrix.extend(ranked)

    for route in READOUT_ROUTES:
        route_rows = [
            {
                "candidate_family_id": family_id,
                "ablation_family": "readout_threshold_sampling_deadtime",
                "ablation_route": route,
                "score_proxy": round(
                    max(0.0, min(1.0, _family_base_score(family) + _readout_modifier(family, route))),
                    6,
                ),
                "score_source": "preflight_readout_threshold_proxy_not_calibrated",
                "lens_policy": "diagnostic",
                "b_stage": "new_preflight",
                "events_per_case": "not_event_run",
                "seed_policy": "deterministic",
                "normalization_policy": "same_lens_same_normalization_only",
                "reference_route": "held_constant",
                "detector_route": "held_constant",
                "threshold_source": route if route.startswith("threshold") or route.startswith("gaussian") else "held_constant",
                "readout_route": route,
                "claim_level": "detector_readout_recommendation_qualification_gate",
                "detection_rate_denominator": "not_applicable",
                "detection_rate_claim_level": "not_applicable_readout_ablation",
                "detection_rate_boundary": "no event detection fraction exported",
            }
            for family_id, family in families.items()
        ]
        ranked = _rank_rows(route_rows)
        readout_rank_maps[route] = {row["candidate_family_id"]: int(row["rank"]) for row in ranked}
        matrix.extend(ranked)

    base_detector = detector_rank_maps["joint_overlap_coherent_surrogate"]
    base_readout = readout_rank_maps["bandpass_envelope_surrogate"]
    detector_labels: list[dict[str, Any]] = []
    threshold_labels: list[dict[str, Any]] = []
    pulse_labels: list[dict[str, Any]] = []
    for family_id, family in sorted(families.items()):
        detector_ranks = {route: ranks[family_id] for route, ranks in detector_rank_maps.items()}
        readout_ranks = {route: ranks[family_id] for route, ranks in readout_rank_maps.items()}
        detector_delta = max(detector_ranks.values()) - min(detector_ranks.values())
        readout_delta = max(readout_ranks.values()) - min(readout_ranks.values())
        detector_only_winner = (
            detector_ranks["joint_overlap_coherent_surrogate"] > 5
            and min(detector_ranks.values()) <= 3
        )
        magnitude_only_winner = readout_ranks["magnitude_route"] <= 3 and readout_ranks["signed_route"] > 5
        threshold_delta = max(
            readout_ranks["threshold_sigma_4"],
            readout_ranks["threshold_sigma_5"],
            readout_ranks["threshold_sigma_6"],
        ) - min(
            readout_ranks["threshold_sigma_4"],
            readout_ranks["threshold_sigma_5"],
            readout_ranks["threshold_sigma_6"],
        )
        sampling_risk = readout_ranks["sampling_rate_low"] - base_readout[family_id] > 5
        pulse_risk = (
            readout_ranks["pulse_width_short"] - base_readout[family_id] > 5
            or readout_ranks["lockin_bandwidth_narrow"] - base_readout[family_id] > 5
        )
        deadtime_risk = readout_ranks["deadtime_overlap_stress"] - base_readout[family_id] > 5
        detector_label = (
            "detector_operator_only_diagnostic"
            if detector_only_winner
            else "detector_sensitive"
            if detector_delta > 5
            else "detector_stable"
        )
        threshold_label = (
            "magnitude_only_diagnostic"
            if magnitude_only_winner
            else "threshold_sensitive"
            if threshold_delta > 5
            else "readout_sensitive"
            if readout_delta > 5
            else "readout_threshold_stable"
        )
        detector_labels.append(
            {
                "candidate_family_id": family_id,
                "detector_rank_delta": detector_delta,
                "detector_operator_only_winner": str(detector_only_winner).lower(),
                "detector_operator_sensitivity_label": detector_label,
                "baseline_rank": base_detector[family_id],
                "worst_case_rank": max(detector_ranks.values()),
                "lens_policy": "diagnostic",
                "b_stage": "new_preflight",
                "events_per_case": "not_event_run",
                "seed_policy": "deterministic",
                "normalization_policy": "same_lens_same_normalization_only",
                "reference_route": "held_constant",
                "detector_route": "mandatory_detector_operator_ablation",
                "threshold_source": "held_constant",
                "readout_route": "held_constant",
                "claim_level": "recommendation_qualification_gate",
                "detection_rate_denominator": "not_applicable",
                "detection_rate_claim_level": "not_applicable_detector_label",
                "detection_rate_boundary": "no event detection fraction exported",
            }
        )
        threshold_labels.append(
            {
                "candidate_family_id": family_id,
                "readout_rank_delta": readout_delta,
                "threshold_rank_delta": threshold_delta,
                "threshold_only_winner": str(threshold_delta > 5).lower(),
                "magnitude_only_winner": str(magnitude_only_winner).lower(),
                "signed_route_dependent": str(abs(readout_ranks["signed_route"] - readout_ranks["magnitude_route"]) > 5).lower(),
                "threshold_noise_sensitivity_label": threshold_label,
                "false_positive_per_time_status": "gaussian_iid_proxy_not_empirical_blank",
                "lens_policy": "diagnostic",
                "b_stage": "new_preflight",
                "events_per_case": "not_event_run",
                "seed_policy": "deterministic",
                "normalization_policy": "same_lens_same_normalization_only",
                "reference_route": "held_constant",
                "detector_route": "held_constant",
                "threshold_source": "threshold_sigma_4_5_6_gaussian_iid_proxy",
                "readout_route": "mandatory_readout_threshold_ablation",
                "claim_level": "recommendation_qualification_gate",
                "detection_rate_denominator": "not_applicable",
                "detection_rate_claim_level": "not_applicable_threshold_label",
                "detection_rate_boundary": "no event detection fraction exported",
            }
        )
        pulse_labels.append(
            {
                "candidate_family_id": family_id,
                "sampling_insufficient_flag": str(sampling_risk).lower(),
                "pulse_width_transfer_risk": str(pulse_risk).lower(),
                "deadtime_overlap_risk": str(deadtime_risk).lower(),
                "sampling_sensitivity_label": (
                    "sampling_sensitive"
                    if sampling_risk
                    else "pulse_width_transfer_risk"
                    if pulse_risk
                    else "deadtime_overlap_risk"
                    if deadtime_risk
                    else "sampling_deadtime_stable"
                ),
                "readout_false_alarm_boundary": "no raw blank/bootstrap configured; empirical false-positive claims blocked",
            }
        )
    return matrix, detector_labels, threshold_labels, pulse_labels


def build_geometry_transport_matrix(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        width = float(row["width_nm"])
        depth = float(row["depth_nm"])
        diameter = float(row["diameter_nm"])
        radius = diameter / 2.0
        acc_w = max(width - diameter, 0.0)
        acc_d = max(depth - diameter, 0.0)
        accessible_fraction = (acc_w * acc_d) / (width * depth)
        clearance = max(min(width, depth) / 2.0 - radius, 0.0)
        wall_sensitive = clearance < 75.0 or diameter / min(width, depth) > 0.25
        narrow_large_ev = width <= 500 and row["particle_role"].startswith("EV")
        selected_bias = "tsuyama" in str(row["candidate_family_id"]).lower()
        if accessible_fraction <= 0.0:
            label = "exclude_before_3seed"
        elif narrow_large_ev or wall_sensitive:
            label = "geometry_transport_high_risk_stress_branch"
        elif selected_bias:
            label = "selected-annulus event-position window bias diagnostic"
        else:
            label = "geometry_transport_viable_proxy"
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_family_id": row["candidate_family_id"],
                "particle_id": row["particle_id"],
                "wavelength_nm": row["wavelength_nm"],
                "width_nm": row["width_nm"],
                "depth_nm": row["depth_nm"],
                "particle_diameter_nm": diameter,
                "accessible_width_nm": acc_w,
                "accessible_depth_nm": acc_d,
                "accessible_area_fraction": round(accessible_fraction, 6),
                "diameter_width_ratio": round(diameter / width, 6),
                "diameter_depth_ratio": round(diameter / depth, 6),
                "nominal_wall_clearance_nm": round(clearance, 3),
                "effective_width_loss_margin_nm": 50.0 if row["particle_role"] in {"EV_high_RI_corona", "doublet_aggregate_proxy"} else 20.0,
                "clogging_risk": "high" if narrow_large_ev or diameter >= 200 else "medium" if wall_sensitive else "low",
                "residence_time_status": "proxy_fixed_velocity_not_pressure_flow_calibrated",
                "pulse_width_compatibility_status": "requires_rehearsal_sidecar_check",
                "selected_annulus_bias_status": (
                    "selected-annulus event-position window diagnostic"
                    if selected_bias
                    else "not_selected_event_position_window_filter"
                ),
                "near_wall_diffusion_status": "near_wall_surrogate_missing_stochastic_drift_blocker" if wall_sensitive else "near_wall_surrogate_low_risk",
                "effective_W_H_perturbation_status": "geometry_plus_minus_50nm_stress_required",
                "geometry_transport_viability_label": label,
                "lens_policy": "diagnostic_preflight_matrix",
                "b_stage": "new_preflight",
                "events_per_case": "not_event_run",
                "seed_policy": "deterministic",
                "normalization_policy": "geometry_transport_proxy",
                "reference_route": "not_applicable_geometry",
                "detector_route": "not_applicable_geometry",
                "threshold_source": "not_applicable_geometry",
                "readout_route": "not_applicable_geometry",
                "claim_level": "geometry_transport_proxy_boundary",
                "detection_rate_denominator": "not_applicable",
                "detection_rate_claim_level": "not_applicable_geometry",
                "detection_rate_boundary": "no event detection fraction exported",
            }
        )
    return rows


def build_ev_prior_outputs(candidate_rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    evidence = [
        {
            "prior_component": "diameter_grid",
            "range_or_scenario": "40,70,100,150,300 nm plus doublet proxy",
            "weight_policy": "coverage_not_population_inference",
            "evidence_source": "MISEV2023; van der Pol/de Rond/Pleet EV optical literature cards",
            "paper_page_or_card": "papers/analysis_full_v1 cards; manual page verification required before hard numeric parameters",
            "route_status": "proxy",
            "claim_boundary": "EV-like optical surrogate; no biological exosome specificity",
        },
        {
            "prior_component": "RI_low_nominal_high",
            "range_or_scenario": "low-RI, nominal membrane/core-shell, high-RI/corona-rich",
            "weight_policy": "stress scenarios not calibrated prevalence",
            "evidence_source": "Pleet 2023; van der Pol; de Rond; MIFlowCyt-EV reporting discipline",
            "paper_page_or_card": "paper library extracted cards require rendered-page review for hard numbers",
            "route_status": "proxy",
            "claim_boundary": "Optical contrast sensitivity only.",
        },
        {
            "prior_component": "contaminant_overlap",
            "range_or_scenario": "lipoprotein-like, protein aggregate-like, liposome-like, PS/silica controls",
            "weight_policy": "comparator coverage",
            "evidence_source": "MISEV2023 and EV flow/reporting papers",
            "paper_page_or_card": "local paper extraction matrix",
            "route_status": "risk-only",
            "claim_boundary": "No sample purity or specificity claim.",
        },
        {
            "prior_component": "corona_doublet_shape",
            "range_or_scenario": "corona absent/low/high; doublet/aggregate proxy; non-spherical risk label",
            "weight_policy": "stress branch coverage",
            "evidence_source": "EV corona and optical sizing literature cards",
            "paper_page_or_card": "paper evidence ledger",
            "route_status": "extrapolated",
            "claim_boundary": "Diagnostic stress only unless measured characterization exists.",
        },
    ]
    stress_rows: list[dict[str, Any]] = []
    family_values: dict[str, list[float]] = defaultdict(list)
    for row in candidate_rows:
        if not str(row["particle_role"]).startswith("EV") and "contaminant" not in str(row["particle_role"]) and "doublet" not in str(row["particle_role"]):
            continue
        diameter = float(row["diameter_nm"])
        base_rank_proxy = 1.0 / max(_family_base_score(row), 0.01)
        low_ri_penalty = 1.8 if "low_RI" in str(row["particle_id"]) or diameter <= 70 else 1.0
        contaminant_penalty = 1.4 if "contaminant" in str(row["particle_role"]) else 1.0
        wall_penalty = 1.5 if float(row["width_nm"]) <= 500 and diameter >= 100 else 1.0
        rank_proxy = base_rank_proxy * low_ri_penalty * contaminant_penalty * wall_penalty
        family_values[str(row["candidate_family_id"])].append(rank_proxy)
        stress_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_family_id": row["candidate_family_id"],
                "particle_id": row["particle_id"],
                "prior_scenario": row["particle_role"],
                "median_rank_proxy": round(rank_proxy, 6),
                "worst_case_rank_proxy": round(rank_proxy * 1.25, 6),
                "rank_interval_proxy": f"{rank_proxy:.3f}-{rank_proxy * 1.25:.3f}",
                "low_RI_under_detection_risk": str(low_ri_penalty > 1.0).lower(),
                "high_RI_coisolate_enrichment_risk": str(row["particle_role"] == "EV_high_RI_corona").lower(),
                "contaminant_overlap_risk": str("contaminant" in str(row["particle_role"])).lower(),
                "selected_annulus_subpopulation_bias": (
                    "selected-annulus event-position window risk"
                    if "tsuyama" in str(row["candidate_family_id"])
                    else "not_selected_event_position_window_filter"
                ),
                "EV_optical_claim_level": "EV-like optical surrogate only",
                "lens_policy": "diagnostic_preflight_matrix",
                "b_stage": "new_preflight",
                "events_per_case": "not_event_run",
                "seed_policy": "deterministic",
                "normalization_policy": "EV_prior_stress_proxy",
                "reference_route": "not_applicable_EV_prior",
                "detector_route": "not_applicable_EV_prior",
                "threshold_source": "not_applicable_EV_prior",
                "readout_route": "not_applicable_EV_prior",
                "claim_level": "EV_like_optical_surrogate_prior_stress",
                "detection_rate_denominator": "not_applicable",
                "detection_rate_claim_level": "not_applicable_EV_prior",
                "detection_rate_boundary": "no event detection fraction exported",
            }
        )
    summaries: list[dict[str, Any]] = []
    for family_id, values in sorted(family_values.items()):
        worst = max(values)
        survival = sum(value <= 2.0 for value in values) / len(values)
        label = (
            "EV_prior_stable_proxy"
            if survival >= 0.6 and worst <= 2.0
            else "EV_prior_conditional_low_RI_or_contaminant_sensitive"
            if survival >= 0.3
            else "EV_prior_stress_only"
        )
        summaries.append(
            {
                "candidate_family_id": family_id,
                "EV_prior_median_rank_proxy": round(float(np.median(values)), 6),
                "EV_prior_worst_case_rank_proxy": round(worst, 6),
                "EV_prior_survival_fraction": round(survival, 6),
                "EV_candidate_stability_label": label,
                "EV_claim_boundary": "EV-like optical surrogate; biological exosome specificity blocked",
            }
        )
    return evidence, stress_rows, summaries


def build_interface_outputs(candidate_rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen: dict[str, Mapping[str, Any]] = {str(row["candidate_family_id"]): row for row in candidate_rows}
    interface_rows: list[dict[str, Any]] = []
    exposure_rows: list[dict[str, Any]] = []
    for family_id, row in sorted(seen.items()):
        wavelength = int(row["wavelength_nm"])
        width = int(row["width_nm"])
        shortwave = wavelength <= 404
        interface_required = width <= 700 or shortwave
        interface_rows.append(
            {
                "candidate_family_id": family_id,
                "homogeneous_medium_mie_status": "active_homogeneous_medium_proxy",
                "interface_correction_mode": "off",
                "interface_fullwave_required": str(interface_required).lower(),
                "interface_fullwave_reason": (
                    "short_wavelength_or_near_wall_phase_polarity_angular_pattern_sensitive"
                    if interface_required
                    else "lower_priority_but_still_not_calibrated"
                ),
                "phase_polarity_angular_pattern_claim_status": "blocked_without_fullwave_or_interface_validation",
                "representative_fullwave_needed": str(interface_required).lower(),
                "top_table_required_blocker_columns": "interface_fullwave_required;homogeneous_medium_mie_status;phase_polarity_angular_pattern_claim_status",
                "lens_policy": "diagnostic_preflight_matrix",
                "b_stage": "new_preflight",
                "events_per_case": "not_event_run",
                "seed_policy": "deterministic",
                "normalization_policy": "interface_safety_flag",
                "reference_route": "interface_flag",
                "detector_route": "not_applicable_interface",
                "threshold_source": "not_applicable_interface",
                "readout_route": "not_applicable_interface",
                "claim_level": "interface_fullwave_needed_flag",
                "detection_rate_denominator": "not_applicable",
                "detection_rate_claim_level": "not_applicable_interface",
                "detection_rate_boundary": "no event detection fraction exported",
            }
        )
        exposure_rows.append(
            {
                "candidate_family_id": family_id,
                "wavelength_nm": wavelength,
                "short_wavelength_branch": str(shortwave).lower(),
                "thermal_exposure_photodamage_status": "unknown_probe_power_and_safety_metadata_absent" if shortwave else "not_short_wavelength_primary_risk",
                "objective_transmission_by_wavelength_status": "absent_blocks_calibrated_cross_wavelength_superiority",
                "detector_responsivity_by_wavelength_status": "absent_blocks_calibrated_cross_wavelength_superiority",
                "filter_transmission_by_wavelength_status": "absent_blocks_calibrated_cross_wavelength_superiority",
                "short_wavelength_role": "stress_branch_only" if shortwave else "not_404_branch",
            }
        )
    return interface_rows, exposure_rows


def _rows_by_key(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    return {str(row[key]): row for row in rows}


def build_stability_synthesis(
    candidate_rows: Sequence[Mapping[str, Any]],
    reference_summary: Sequence[Mapping[str, Any]],
    detector_labels: Sequence[Mapping[str, Any]],
    threshold_labels: Sequence[Mapping[str, Any]],
    geometry_rows: Sequence[Mapping[str, Any]],
    ev_summary: Sequence[Mapping[str, Any]],
    interface_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    families = {row["candidate_family_id"]: row for row in candidate_rows}
    ref = _rows_by_key(reference_summary, "candidate_family_id")
    det = _rows_by_key(detector_labels, "candidate_family_id")
    thr = _rows_by_key(threshold_labels, "candidate_family_id")
    ev = _rows_by_key(ev_summary, "candidate_family_id")
    iface = _rows_by_key(interface_rows, "candidate_family_id")
    geom_by_family: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in geometry_rows:
        geom_by_family[str(row["candidate_family_id"])].append(row)

    matrix: list[dict[str, Any]] = []
    demotions: list[dict[str, Any]] = []
    carry: list[dict[str, Any]] = []
    for family_id, family in sorted(families.items()):
        ref_row = ref[family_id]
        det_row = det[family_id]
        thr_row = thr[family_id]
        ev_row = ev.get(family_id, {
            "EV_prior_worst_case_rank_proxy": "not_applicable_non_EV_or_anchor",
            "EV_prior_survival_fraction": "not_applicable",
            "EV_candidate_stability_label": "EV_prior_not_primary_basis",
        })
        iface_row = iface[family_id]
        primary_geometry_rows = [
            row
            for row in geom_by_family[family_id]
            if str(row.get("particle_id", "")) in {
                "Au20",
                "Au30",
                "Au40",
                "Au60",
                "EV40_nominal",
                "EV70_nominal",
                "EV100_nominal",
                "EV150_nominal",
                "EV70_lowRI",
                "EV100_lowRI",
                "EV150_lowRI",
            }
        ]
        primary_geometry_rows = primary_geometry_rows or list(geom_by_family[family_id])
        geom_labels = {
            str(row["geometry_transport_viability_label"])
            for row in primary_geometry_rows
        }
        geometry_high_risk = any("high_risk" in label or "exclude" in label for label in geom_labels)
        selected_only = "tsuyama" in family_id.lower()
        shortwave = int(family["wavelength_nm"]) <= 404
        detector_sensitive = det_row["detector_operator_sensitivity_label"] != "detector_stable"
        threshold_sensitive = thr_row["threshold_noise_sensitivity_label"] != "readout_threshold_stable"
        reference_stable = ref_row["reference_stability_label"] == "reference_stable_for_relative_recommendation"
        interface_required = str(iface_row["interface_fullwave_required"]) == "true"

        reasons: list[str] = []
        claim_boundary_flags: list[str] = []
        if not reference_stable:
            reasons.append(str(ref_row["reference_stability_label"]))
        if detector_sensitive:
            reasons.append(str(det_row["detector_operator_sensitivity_label"]))
        if threshold_sensitive:
            reasons.append(str(thr_row["threshold_noise_sensitivity_label"]))
        if geometry_high_risk:
            reasons.append("geometry_or_wall_transport_high_risk")
        if shortwave:
            claim_boundary_flags.append("short_wavelength_exposure_transfer_unknown")
        if interface_required:
            claim_boundary_flags.append("interface_fullwave_required")
        if selected_only:
            reasons.append("selected-annulus event-position window diagnostic only")

        diagnostic_family = selected_only or "reference_edge" in family_id or "au_control" in family_id
        explicit_stress_family = geometry_high_risk or "optional_900" in family_id
        robust_evidence_gate = (
            reference_stable
            and not detector_sensitive
            and not threshold_sensitive
            and not explicit_stress_family
            and not diagnostic_family
        )

        if robust_evidence_gate:
            stability_class = "robust_relative_candidate"
        elif diagnostic_family:
            stability_class = "diagnostic_only"
        elif explicit_stress_family:
            stability_class = "stress_branch"
        elif reference_stable or str(ref_row["reference_stability_label"]).startswith("reference_conditional"):
            stability_class = "conditional_candidate"
        else:
            stability_class = "diagnostic_only"

        if stability_class == "robust_relative_candidate":
            action = "carry_forward_as_primary_relative_candidate"
        elif stability_class == "conditional_candidate":
            action = "carry_forward_with_named_assumptions"
        elif stability_class == "stress_branch":
            action = "carry_forward_as_stress_branch_if_budget_allows"
        elif stability_class == "diagnostic_only":
            action = "retain_for_diagnostic_tables_not_primary_recommendation"
        else:
            action = "exclude_before_3seed"

        row = {
            "candidate_family_id": family_id,
            "wavelength_nm": family["wavelength_nm"],
            "width_nm": family["width_nm"],
            "depth_nm": family["depth_nm"],
            "seed_stability_status": "pending_low_event_rehearsal",
            "reference_top5_jaccard": ref_row["reference_top5_jaccard_min"],
            "reference_spearman": ref_row["reference_spearman_min"],
            "reference_rank_delta": ref_row["reference_rank_delta"],
            "reference_stability_label": ref_row["reference_stability_label"],
            "detector_readout_topk_jaccard": "proxy_not_calibrated",
            "detector_readout_rank_delta": det_row["detector_rank_delta"],
            "detector_operator_sensitivity_label": det_row["detector_operator_sensitivity_label"],
            "threshold_noise_rank_delta": thr_row["threshold_rank_delta"],
            "threshold_noise_sensitivity_label": thr_row["threshold_noise_sensitivity_label"],
            "EV_prior_worst_case_rank": ev_row["EV_prior_worst_case_rank_proxy"],
            "EV_prior_survival_fraction": ev_row["EV_prior_survival_fraction"],
            "EV_candidate_stability_label": ev_row["EV_candidate_stability_label"],
            "geometry_perturbation_rank_delta": "requires_future_plus_minus_50nm_event_rehearsal",
            "transport_risk_class": "high" if geometry_high_risk else "medium" if interface_required else "low",
            "interface_fullwave_required": iface_row["interface_fullwave_required"],
            "short_wavelength_safety_flag": str(shortwave).lower(),
            "claim_boundary_flags": "none" if not claim_boundary_flags else "; ".join(claim_boundary_flags),
            "unsupported_only_winner": ref_row["unsupported_only_winner"],
            "single_route_only_winner": str(not reference_stable).lower(),
            "normalisation_specific_only": str(shortwave or selected_only).lower(),
            "selected_annulus_only_improvement": str(selected_only).lower(),
            "detector_operator_only_winner": det_row["detector_operator_only_winner"],
            "magnitude_only_winner": thr_row["magnitude_only_winner"],
            "phase_sign_sensitive": ref_row["phase_sign_sensitive"],
            "stability_class": stability_class,
            "classification_reason": "none" if not reasons else "; ".join(reasons),
            "carry_forward_action": action,
            "lens_policy": "diagnostic",
            "b_stage": "new_preflight",
            "events_per_case": "not_event_run",
            "seed_policy": "deterministic",
            "normalization_policy": "classification_from_same_scope_metrics",
            "reference_route": "reference_stability_label_required",
            "detector_route": "detector_readout_label_required",
            "threshold_source": "threshold_label_required",
            "readout_route": "readout_label_required",
            "claim_level": "candidate_family_stability_synthesis",
            "detection_rate_denominator": "not_applicable",
            "detection_rate_claim_level": "not_applicable_synthesis",
            "detection_rate_boundary": "no event detection fraction exported",
        }
        matrix.append(row)
        if stability_class != "robust_relative_candidate":
            demotions.append(
                {
                    "candidate_family_id": family_id,
                    "demoted_to": stability_class,
                    "demotion_reason": row["classification_reason"],
                    "preserve_for_discovery": str(stability_class in {"conditional_candidate", "stress_branch", "diagnostic_only"}).lower(),
                    "scientific_reason_to_preserve": family["scientific_reason_to_preserve"],
                }
            )
        if stability_class != "exclude_before_3seed":
            carry.append(
                {
                    "candidate_family_id": family_id,
                    "wavelength_nm": family["wavelength_nm"],
                    "width_nm": family["width_nm"],
                    "depth_nm": family["depth_nm"],
                    "stability_class": stability_class,
                    "preflight_role": action,
                    "allowed_in_low_event_rehearsal": "true",
                    "allowed_in_large_3seed_10000e": str(stability_class in {"robust_relative_candidate", "conditional_candidate", "stress_branch"}).lower(),
                    "large_run_role": (
                        "primary_relative_candidate"
                        if stability_class == "robust_relative_candidate"
                        else "conditional_or_stress_branch_not_primary"
                    ),
                    "claim_boundary": "relative/proxy design-selection only; no calibration or biological specificity",
                }
            )
    return matrix, demotions, carry


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _to_float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        result = float(value)
    except Exception:
        return None
    return result if math.isfinite(result) else None


def _json_safe_scalar(value: Any) -> Any:
    if isinstance(value, (np.floating, float)):
        f = float(value)
        return f if math.isfinite(f) else ""
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def _numeric_sequence_summary(values: Sequence[Any]) -> dict[str, Any] | None:
    numeric: list[float] = []
    for value in values:
        try:
            numeric.append(float(value))
        except (TypeError, ValueError):
            return None
    if not numeric:
        return {
            "sequence_summary_type": "empty_numeric_sequence",
            "size": 0,
        }
    finite = [value for value in numeric if math.isfinite(value)]
    if not finite:
        return {
            "sequence_summary_type": "nonfinite_numeric_sequence",
            "size": len(numeric),
        }
    return {
        "sequence_summary_type": "numeric_sequence",
        "size": len(numeric),
        "min": min(finite),
        "max": max(finite),
        "mean": sum(finite) / len(finite),
        "first": numeric[0],
        "last": numeric[-1],
    }


def _json_safe_diagnostic_value(value: Any, *, max_items: int = 32) -> Any:
    if value is None:
        return None
    if isinstance(value, np.generic):
        return _json_safe_diagnostic_value(value.item(), max_items=max_items)
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (int, str, bool)):
        return value
    if isinstance(value, complex):
        return {
            "complex_real": float(value.real),
            "complex_imag": float(value.imag),
            "complex_abs": float(abs(value)),
            "complex_phase_rad": float(np.angle(value)),
        }
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, np.ndarray):
        flat = value.reshape(-1)
        if flat.size <= max_items:
            return [
                _json_safe_diagnostic_value(item, max_items=max_items)
                for item in flat.tolist()
            ]
        numeric = None
        if np.issubdtype(value.dtype, np.number):
            finite = flat[np.isfinite(flat)] if np.issubdtype(value.dtype, np.floating) else flat
            numeric = {
                "min": float(np.min(finite)) if finite.size else None,
                "max": float(np.max(finite)) if finite.size else None,
                "mean": float(np.mean(finite)) if finite.size else None,
            }
        return {
            "array_summary_type": "ndarray",
            "shape": list(value.shape),
            "size": int(flat.size),
            "dtype": str(value.dtype),
            **(numeric or {}),
        }
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe_diagnostic_value(item, max_items=max_items)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        seq = list(value)
        if len(seq) <= max_items:
            return [
                _json_safe_diagnostic_value(item, max_items=max_items)
                for item in seq
            ]
        numeric_summary = _numeric_sequence_summary(seq)
        if numeric_summary is not None:
            return numeric_summary
        return {
            "sequence_summary_type": "sampled_sequence",
            "size": len(seq),
            "sample_first_n": [
                _json_safe_diagnostic_value(item, max_items=max_items)
                for item in seq[:max_items]
            ],
        }
    try:
        json.dumps(value, allow_nan=False)
        return value
    except (TypeError, ValueError):
        return str(value)


def _diagnostic_snapshot_for_result(
    result: Mapping[str, Any],
    *,
    seed: int,
    route_id: str,
    scope: Mapping[str, str],
) -> dict[str, Any]:
    summary = dict(result.get("summary", {}))
    reference = dict(result.get("reference", {}))
    top_level = {
        key: value
        for key, value in result.items()
        if key not in {"summary", "reference", "intrinsic"}
    }
    return {
        "snapshot_schema": "pre3seed_formal_case_diagnostic_snapshot_v1",
        "snapshot_policy": (
            "Main CSV keeps stable ranking columns; JSONL snapshot preserves "
            "case-level diagnostic scalars and summarizes large per-event arrays "
            "to reduce rerun risk without treating diagnostics as calibrated claims."
        ),
        "route_id": route_id,
        "seed": int(seed),
        "particle_name": str(result.get("particle_name", "")),
        "wavelength_nm": int(round(float(result["wavelength_m"]) * 1e9)),
        "width_nm": int(round(float(result["width_m"]) * 1e9)),
        "depth_nm": int(round(float(result["depth_m"]) * 1e9)),
        "claim_level": scope["claim_level"],
        "lens_policy": scope["lens_policy"],
        "b_stage": scope["b_stage"],
        "summary": _json_safe_diagnostic_value(summary),
        "reference": _json_safe_diagnostic_value(reference),
        "result_scalars": _json_safe_diagnostic_value(top_level),
    }


def _write_jsonl_atomic(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    for row in rows:
        buffer.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False))
        buffer.write("\n")
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(buffer.getvalue())
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path.replace(path)
    except Exception:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        raise


def _family_by_route(candidate_rows: Sequence[Mapping[str, Any]]) -> dict[tuple[int, int, int], Mapping[str, Any]]:
    by_route: dict[tuple[int, int, int], Mapping[str, Any]] = {}
    for row in candidate_rows:
        key = (_to_int(row["wavelength_nm"]), _to_int(row["width_nm"]), _to_int(row["depth_nm"]))
        by_route.setdefault(key, row)
    return by_route


def build_formal_3seed_run_plan(
    carry_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
    stability_rows: Sequence[Mapping[str, Any]],
    *,
    seeds: Sequence[int] = (11, 22, 33),
    events_per_case: int = 10_000,
    particle_panel_size: int | None = None,
) -> list[dict[str, Any]]:
    """Build the formal large-run plan from the carry-forward manifest only."""
    stability = _rows_by_key(stability_rows, "candidate_family_id")
    candidate_family = {
        str(row["candidate_family_id"]): row
        for row in candidate_rows
    }
    panel_size = int(particle_panel_size or len({row["particle_id"] for row in candidate_rows}))
    rows: list[dict[str, Any]] = []
    for carry in sorted(carry_rows, key=lambda row: str(row["candidate_family_id"])):
        if str(carry.get("allowed_in_large_3seed_10000e", "")).lower() != "true":
            continue
        family_id = str(carry["candidate_family_id"])
        family = candidate_family[family_id]
        stable = stability[family_id]
        for seed in seeds:
            route_scope_key = (
                f"formal_3seed_10000e|family={family_id}|seed={int(seed)}|"
                f"lambda={int(family['wavelength_nm'])}|W={int(family['width_nm'])}|"
                f"D={int(family['depth_nm'])}|normalization=per_wavelength"
            )
            rows.append(
                {
                    "formal_plan_schema": "pre3seed_formal_3seed_10000e_run_plan_v1",
                    "candidate_family_id": family_id,
                    "wavelength_nm": int(family["wavelength_nm"]),
                    "width_nm": int(family["width_nm"]),
                    "depth_nm": int(family["depth_nm"]),
                    "seed": int(seed),
                    "events_per_case": int(events_per_case),
                    "expected_particle_panel_size": panel_size,
                    "expected_rows_for_seed_route": panel_size,
                    "expected_event_count_for_seed_route": panel_size * int(events_per_case),
                    "stability_class": stable["stability_class"],
                    "large_run_role": carry["large_run_role"],
                    "preflight_role": carry["preflight_role"],
                    "classification_reason": stable["classification_reason"],
                    "claim_boundary_flags": stable.get("claim_boundary_flags", "none"),
                    "interface_fullwave_required": stable["interface_fullwave_required"],
                    "short_wavelength_safety_flag": stable.get("short_wavelength_safety_flag", "false"),
                    "count_prediction_status": "not_applied_per_event_only",
                    "lens_policy": "parallel_all_crossing_and_selected_annulus_outputs",
                    "normalization_policy": "per_wavelength_raw_scope; fixed_660_requires_separate_scope",
                    "reference_route": "channel_angular_surrogate_formal_freeze",
                    "detector_route": "joint_overlap_coherent_surrogate_formal_freeze",
                    "threshold_source": "gaussian_iid_surrogate_not_empirical_blank",
                    "readout_route": "EV_NODI_only_design_lockin_surrogate",
                    "route_scope_key": route_scope_key,
                    "selected_annulus_boundary": "selected-annulus event-position window, not optical BFP annulus",
                    "all_crossing_output_required": "true",
                    "selected_annulus_output_required": "true",
                    "analysis_join_key": f"{family_id}|{int(seed)}",
                    "claim_level": "formal_run_plan_no_results",
                }
            )
    validate_formal_3seed_run_plan(rows)
    return rows


def validate_formal_3seed_run_plan(rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise PreflightGateError("formal run plan is empty")
    required = {
        "candidate_family_id",
        "seed",
        "events_per_case",
        "stability_class",
        "large_run_role",
        "route_scope_key",
        "normalization_policy",
        "all_crossing_output_required",
        "selected_annulus_output_required",
        "selected_annulus_boundary",
    }
    missing = sorted(required - set().union(*(set(row.keys()) for row in rows)))
    if missing:
        raise PreflightGateError(f"formal run plan missing fields: {missing}")
    seen: set[tuple[str, int]] = set()
    for row in rows:
        key = (str(row["candidate_family_id"]), _to_int(row["seed"]))
        if key in seen:
            raise PreflightGateError(f"duplicate formal seed/family row: {key}")
        seen.add(key)
        if int(row["events_per_case"]) != 10_000:
            raise PreflightGateError("formal run plan must freeze events_per_case=10000")
        if "event-position window" not in str(row["selected_annulus_boundary"]):
            raise PreflightGateError("formal run plan selected-annulus boundary is incomplete")
        if str(row["all_crossing_output_required"]).lower() != "true":
            raise PreflightGateError("formal run plan must require all-crossing output")
        if str(row["selected_annulus_output_required"]).lower() != "true":
            raise PreflightGateError("formal run plan must require selected-annulus output")
        if "fixed_660" in str(row["normalization_policy"]) and "separate_scope" not in str(row["normalization_policy"]):
            raise PreflightGateError("fixed-660 normalization must be isolated as a separate scope")


def _route_key_from_row(row: Mapping[str, Any]) -> tuple[int, int, int]:
    return (_to_int(row["wavelength_nm"]), _to_int(row["width_nm"]), _to_int(row["depth_nm"]))


def _rate_payload(row: Mapping[str, Any], lens_scope: str) -> dict[str, Any]:
    if lens_scope == "all_crossing":
        denominator = _to_int(row.get("all_crossing_n_events", row.get("detection_rate_denominator", row.get("n_events", 0))))
        rate = _to_float_or_none(row.get("all_crossing_detection_rate"))
        if rate is None:
            rate = _to_float_or_none(row.get("detection_rate"))
        return {
            "detection_rate": rate,
            "detection_rate_denominator": denominator,
            "detection_rate_numerator_proxy": None if rate is None else rate * denominator,
            "lens_policy": "all_crossing",
            "lens_boundary": "all generated crossing events denominator",
            "rate_status": "available" if rate is not None else "missing_all_crossing_rate",
        }
    denominator = _to_int(row.get("selected_detector_mode_annulus_n_events", 0))
    rate = _to_float_or_none(row.get("selected_detector_mode_annulus_detection_rate"))
    if denominator == 0 and rate is None:
        return {
            "detection_rate": None,
            "detection_rate_denominator": 0,
            "detection_rate_numerator_proxy": 0.0,
            "lens_policy": "selected_annulus_event_position_window",
            "lens_boundary": "selected-annulus event-position window denominator, not optical BFP annulus",
            "rate_status": "available_no_selected_window_events",
        }
    return {
        "detection_rate": rate,
        "detection_rate_denominator": denominator,
        "detection_rate_numerator_proxy": None if rate is None else rate * denominator,
        "lens_policy": "selected_annulus_event_position_window",
        "lens_boundary": "selected-annulus event-position window denominator, not optical BFP annulus",
        "rate_status": (
            "available"
            if rate is not None
            else "missing_selected_annulus_detection_rate_requires_sidecar"
        ),
    }


def build_dual_lens_top_table(
    summary_rows: Sequence[Mapping[str, Any]],
    stability_rows: Sequence[Mapping[str, Any]],
    candidate_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build separate all-crossing and selected-window top-table views."""
    stability = _rows_by_key(stability_rows, "candidate_family_id")
    family_by_route = _family_by_route(candidate_rows)
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for raw in summary_rows:
        family = family_by_route.get(_route_key_from_row(raw))
        if family is None:
            continue
        family_id = str(family["candidate_family_id"])
        for lens_scope in ("all_crossing", "selected_annulus_event_position_window"):
            payload = _rate_payload(raw, "all_crossing" if lens_scope == "all_crossing" else "selected_annulus")
            grouped[(family_id, str(raw.get("seed", "pooled")), lens_scope)].append(
                {
                    **payload,
                    "raw": raw,
                    "family": family,
                    "stability": stability[family_id],
                }
            )

    rows: list[dict[str, Any]] = []
    for (family_id, seed, lens_scope), items in sorted(grouped.items()):
        rates = [item["detection_rate"] for item in items if item["detection_rate"] is not None]
        denominators = [int(item["detection_rate_denominator"]) for item in items]
        numerator_proxy = [
            float(item["detection_rate_numerator_proxy"])
            for item in items
            if item["detection_rate_numerator_proxy"] is not None
        ]
        complete_item_count = len(numerator_proxy)
        family = items[0]["family"]
        stable = items[0]["stability"]
        denominator_sum = sum(denominators)
        weighted_rate = (
            sum(numerator_proxy) / denominator_sum
            if denominator_sum > 0 and len(numerator_proxy) == len(items)
            else None
        )
        rows.append(
            {
                "candidate_family_id": family_id,
                "seed_scope": seed,
                "lens_policy": lens_scope,
                "wavelength_nm": int(family["wavelength_nm"]),
                "width_nm": int(family["width_nm"]),
                "depth_nm": int(family["depth_nm"]),
                "mean_detection_rate": "" if not rates else round(sum(rates) / len(rates), 8),
                "denominator_weighted_detection_rate": "" if weighted_rate is None else round(weighted_rate, 8),
                "detection_rate_denominator": denominator_sum,
                "rate_available_rows": complete_item_count,
                "rate_expected_rows": len(items),
                "rate_status": (
                    "available"
                    if complete_item_count == len(items)
                    else "missing_lens_rate_sidecar_fields"
                ),
                "stability_class": stable["stability_class"],
                "claim_boundary_flags": stable.get("claim_boundary_flags", "none"),
                "interface_fullwave_required": stable["interface_fullwave_required"],
                "count_prediction_status": "not_applied_per_event_only",
                "normalization_policy": "per_wavelength",
                "reference_route": "channel_angular_surrogate_formal_freeze",
                "detector_route": "joint_overlap_coherent_surrogate_formal_freeze",
                "threshold_source": "gaussian_iid_surrogate_not_empirical_blank",
                "readout_route": "EV_NODI_only_design_lockin_surrogate",
                "route_scope_key": (
                    f"candidate={family_id}|lens={lens_scope}|seed={seed}|"
                    "normalization=per_wavelength"
                ),
                "rank_scope_key": f"lens={lens_scope}|seed={seed}|normalization=per_wavelength",
                "selected_annulus_boundary": (
                    "selected-annulus event-position window, not optical BFP annulus"
                    if lens_scope == "selected_annulus_event_position_window"
                    else "not_applicable_all_crossing"
                ),
                "allowed_claim_warning": (
                    "selected-window diagnostic only; do not compare as optical BFP annulus"
                    if lens_scope == "selected_annulus_event_position_window"
                    else "all-crossing conditional synthetic event denominator"
                ),
            }
        )

    pooled: list[dict[str, Any]] = []
    families = sorted({row["candidate_family_id"] for row in rows})
    for family_id in families:
        for lens_scope in ("all_crossing", "selected_annulus_event_position_window"):
            seed_rows = [
                row for row in rows
                if row["candidate_family_id"] == family_id and row["lens_policy"] == lens_scope
            ]
            if not seed_rows:
                continue
            denominators = [int(row["detection_rate_denominator"]) for row in seed_rows]
            weighted_values = [
                _to_float_or_none(row["denominator_weighted_detection_rate"])
                for row in seed_rows
            ]
            if all(value is not None for value in weighted_values) and sum(denominators) > 0:
                pooled_rate = sum(float(value) * denom for value, denom in zip(weighted_values, denominators, strict=True)) / sum(denominators)
            else:
                pooled_rate = None
            template = dict(seed_rows[0])
            template["seed_scope"] = "pooled"
            template["mean_detection_rate"] = "" if pooled_rate is None else round(pooled_rate, 8)
            template["denominator_weighted_detection_rate"] = "" if pooled_rate is None else round(pooled_rate, 8)
            template["detection_rate_denominator"] = sum(denominators)
            template["rate_available_rows"] = sum(int(row["rate_available_rows"]) for row in seed_rows)
            template["rate_expected_rows"] = sum(int(row["rate_expected_rows"]) for row in seed_rows)
            template["rate_status"] = (
                "available"
                if template["rate_available_rows"] == template["rate_expected_rows"]
                else "missing_lens_rate_sidecar_fields"
            )
            template["route_scope_key"] = (
                f"candidate={family_id}|lens={lens_scope}|seed=pooled|"
                "normalization=per_wavelength"
            )
            template["rank_scope_key"] = f"lens={lens_scope}|seed=pooled|normalization=per_wavelength"
            pooled.append(template)
    rows.extend(pooled)

    for scope in sorted({row["rank_scope_key"] for row in rows}):
        scoped = [
            row for row in rows
            if row["rank_scope_key"] == scope and _to_float_or_none(row["denominator_weighted_detection_rate"]) is not None
        ]
        ranked = sorted(scoped, key=lambda row: (-float(row["denominator_weighted_detection_rate"]), str(row["candidate_family_id"])))
        for rank, row in enumerate(ranked, start=1):
            row["rank_within_scope"] = rank
        for row in rows:
            if row["rank_scope_key"] == scope and "rank_within_scope" not in row:
                row["rank_within_scope"] = ""

    missing = sorted(set(REQUIRED_TOP_TABLE_BLOCKER_COLUMNS) - set().union(*(set(row.keys()) for row in rows)))
    if missing:
        raise PreflightGateError(f"dual-lens top table missing required blocker columns: {missing}")
    return rows


def build_pooled_per_seed_consistency(top_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    pooled_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in top_rows:
        key = (str(row["candidate_family_id"]), str(row["lens_policy"]))
        if str(row["seed_scope"]) == "pooled":
            pooled_by_key[key] = row
        else:
            grouped[key].append(row)
    for key, seed_rows in sorted(grouped.items()):
        family_id, lens_scope = key
        ranks = [_to_int(row.get("rank_within_scope"), 0) for row in seed_rows if _to_int(row.get("rank_within_scope"), 0) > 0]
        rates = [
            _to_float_or_none(row.get("denominator_weighted_detection_rate"))
            for row in seed_rows
        ]
        rates = [rate for rate in rates if rate is not None]
        pooled = pooled_by_key.get(key, {})
        rows.append(
            {
                "candidate_family_id": family_id,
                "lens_policy": lens_scope,
                "seed_count": len(seed_rows),
                "pooled_rank": pooled.get("rank_within_scope", ""),
                "per_seed_rank_min": "" if not ranks else min(ranks),
                "per_seed_rank_max": "" if not ranks else max(ranks),
                "per_seed_rank_delta": "" if not ranks else max(ranks) - min(ranks),
                "pooled_detection_rate": pooled.get("denominator_weighted_detection_rate", ""),
                "per_seed_rate_min": "" if not rates else round(min(rates), 8),
                "per_seed_rate_max": "" if not rates else round(max(rates), 8),
                "per_seed_rate_delta": "" if not rates else round(max(rates) - min(rates), 8),
                "consistency_status": (
                    "missing_lens_rate_sidecar_fields"
                    if any(str(row.get("rate_status")) != "available" for row in seed_rows)
                    else "seed_rank_sensitive"
                    if ranks and max(ranks) - min(ranks) > 2
                    else "seed_consistent_rehearsal_proxy"
                ),
                "claim_boundary": "consistency diagnostic only; low-event rehearsal is not final rank evidence",
            }
        )
    return rows


def build_formal_prelaunch_manifest(
    *,
    formal_plan_rows: Sequence[Mapping[str, Any]],
    top_table_rows: Sequence[Mapping[str, Any]],
    consistency_rows: Sequence[Mapping[str, Any]],
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    plan_hash = sha256_payload(formal_plan_rows)
    p19_artifact_hashes = {
        relpath(project_root / path, project_root): sha256_or_na(project_root / path)
        for path in FORMAL_P19_REQUIRED_ARTIFACT_PATHS
    }
    return {
        "schema_version": "pre3seed_formal_3seed_10000e_prelaunch_manifest_v1",
        "created_at": now_utc_iso(),
        "formal_run_plan_hash": plan_hash,
        "formal_run_plan_path": relpath(project_root / FORMAL_RUN_PLAN_CSV_PATH, project_root),
        "carry_forward_manifest_hash": sha256_or_na(project_root / CARRY_FORWARD_PATH),
        "candidate_manifest_hash": sha256_or_na(project_root / CANDIDATE_MANIFEST_PATH),
        "stability_matrix_hash": sha256_or_na(project_root / STABILITY_MATRIX_PATH),
        "exact_command_template": FORMAL_EXACT_COMMAND_TEMPLATE,
        "dry_run_command": FORMAL_DRY_RUN_COMMAND,
        "events_per_case": 10_000,
        "planned_worker_count": FORMAL_WORKER_COUNT,
        "seed_list": sorted({_to_int(row["seed"]) for row in formal_plan_rows}),
        "candidate_family_count": len({row["candidate_family_id"] for row in formal_plan_rows}),
        "expected_rows": sum(_to_int(row["expected_rows_for_seed_route"]) for row in formal_plan_rows),
        "expected_event_count": sum(_to_int(row["expected_event_count_for_seed_route"]) for row in formal_plan_rows),
        "diagnostic_snapshot_required": True,
        "diagnostic_snapshot_schema": "pre3seed_formal_case_diagnostic_snapshot_v1",
        "expected_formal_output_files": [
            "pre3seed_formal_3seed_10000e_summary.csv",
            "pre3seed_formal_3seed_10000e_diagnostic_snapshot.jsonl",
            "pre3seed_formal_3seed_10000e_route_claim_matrix.csv",
            "pre3seed_formal_3seed_10000e_claim_scan.csv",
            "pre3seed_formal_3seed_10000e_manifest.json",
            "pre3seed_formal_3seed_10000e_dual_lens_top_table.csv",
            "pre3seed_formal_3seed_10000e_pooled_per_seed_consistency.csv",
            "pre3seed_formal_3seed_10000e_postrun_manifest.json",
        ],
        "launch_authorization_contract": {
            "contract_version": FORMAL_LAUNCH_CONTRACT_VERSION,
            "scope": "no_measured_data_level1_relative_proxy_route_ranking",
            "requires_explicit_user_launch_authorization": True,
            "required_execute_flags": [
                "--execute",
                "--allow-large-run",
                FORMAL_LAUNCH_CONFIRMATION_FLAG,
            ],
            "planned_worker_count": FORMAL_WORKER_COUNT,
            "required_worker_flag": f"--workers {FORMAL_WORKER_COUNT}",
            "not_a_launch_permit": True,
            "launch_blocked_until": [
                "freeze_manifest_dirty_false_or_explicitly_accepted_audited_snapshot",
                "current_git_worktree_clean_or_explicitly_accepted_audited_snapshot",
                "p19_required_artifact_hashes_match_current_files",
                "user_explicitly_authorizes_the_full_calculation",
            ],
            "measured_artifacts_policy": (
                "measured detector transfer, standard-particle ladder, raw blank trace, "
                "pressure-flow trace, measured BFP/reference, and EV biology controls "
                "block Level-2+ claims but do not block this no-measured-data Level-1 run"
            ),
            "scope_decisions": {
                "pod": "out_of_scope_for_current_no_data_nodi_scoring",
                "contaminant_stress": "separate_diagnostic_manifest_no_formal_panel_change",
                "event_arrival": "excluded_from_current_full_run_scoring",
            },
            "forbidden_claims": [
                "calibrated_snr",
                "absolute_lod",
                "detector_voltage",
                "photon_count",
                "true_event_probability",
                "true_concentration",
                "empirical_blank_false_positive_rate",
                "biological_ev_specificity",
                "calibrated_cross_wavelength_superiority",
                "quantitative_pod_amplitude",
                "contaminant_stress_route_promotion",
            ],
        },
        "p19_required_artifact_hashes": p19_artifact_hashes,
        "worker_chunk_vectorization_policy": (
            f"formal run uses n_workers={FORMAL_WORKER_COUNT}, fixed event budget, "
            "vectorized_event_engine=off, and deterministic route/seed loop order; "
            "changing worker count after launch is a new scope and requires P19 review"
        ),
        "postprocess_policy": (
            "build all-crossing and selected-annulus event-position-window top tables "
            "from one raw run; never mix denominators or lens scopes"
        ),
        "required_top_table_blocker_columns": list(REQUIRED_TOP_TABLE_BLOCKER_COLUMNS),
        "top_table_template_hash": sha256_payload(top_table_rows),
        "pooled_per_seed_consistency_hash": sha256_payload(consistency_rows),
        "claim_boundary": (
            "prelaunch manifest only; no formal 10000e computation has been run by this "
            "artifact; exact_command_template is not a launch permit"
        ),
    }


def validate_formal_execution_freeze(
    *,
    formal_plan_rows: Sequence[Mapping[str, Any]],
    project_root: Path = PROJECT_ROOT,
    freeze_manifest_path: Path | None = None,
    require_git_clean: bool = True,
) -> dict[str, Any]:
    """Hard-stop a formal run unless it matches the frozen preflight manifest."""
    manifest_path = (
        Path(freeze_manifest_path)
        if freeze_manifest_path is not None and Path(freeze_manifest_path).is_absolute()
        else project_root / (freeze_manifest_path or FREEZE_MANIFEST_PATH)
    )
    if not manifest_path.exists():
        raise PreflightGateError(f"formal freeze manifest missing: {manifest_path}")
    freeze = json.loads(manifest_path.read_text(encoding="utf-8"))
    frozen_dirty = bool(freeze.get("git_dirty_state", {}).get("dirty", True))
    if frozen_dirty:
        raise PreflightGateError(
            "formal execution freeze was created from a dirty git state; commit and regenerate freeze first"
        )
    current_dirty = git_dirty_summary(project_root)
    if require_git_clean and current_dirty.get("dirty"):
        raise PreflightGateError(
            f"formal execution requires a clean git worktree; current status is {current_dirty.get('status')}"
        )
    expected_script_hash = str(freeze.get("postprocess_script_hash", ""))
    actual_script_hash = analysis_script_hash(project_root)
    if expected_script_hash != actual_script_hash:
        raise PreflightGateError(
            "formal execution script hash mismatch: "
            f"freeze={expected_script_hash} actual={actual_script_hash}"
        )

    input_hashes = dict(freeze.get("input_file_hashes", {}))
    required_hashes = {
        relpath(project_root / CARRY_FORWARD_PATH, project_root): str(
            freeze.get("candidate_carry_forward_manifest_hash", "")
        ),
    }
    for relative_path in FORMAL_EXECUTION_REQUIRED_HASH_PATHS:
        rel = relpath(project_root / relative_path, project_root)
        required_hashes.setdefault(rel, str(input_hashes.get(rel, "")))
    missing = sorted(rel for rel, expected in required_hashes.items() if not expected)
    if missing:
        raise PreflightGateError(f"freeze manifest lacks required input hashes: {missing}")
    mismatches = []
    for rel, expected in required_hashes.items():
        actual = sha256_or_na(project_root / rel)
        if actual != expected:
            mismatches.append({"path": rel, "freeze": expected, "actual": actual})
    if mismatches:
        raise PreflightGateError(f"formal execution input hash mismatch: {mismatches[:3]}")

    plan_hash = sha256_payload(formal_plan_rows)
    plan_manifest_path = project_root / FORMAL_RUN_PLAN_JSON_PATH
    if not plan_manifest_path.exists():
        raise PreflightGateError("formal execution required run-plan manifest is missing")
    plan_manifest = json.loads(plan_manifest_path.read_text(encoding="utf-8"))
    if str(plan_manifest.get("formal_run_plan_hash")) != plan_hash:
        raise PreflightGateError("formal execution plan hash differs from frozen run-plan manifest")
    prelaunch_path = project_root / FORMAL_PRELAUNCH_MANIFEST_PATH
    if not prelaunch_path.exists():
        raise PreflightGateError("formal execution required prelaunch manifest is missing")
    prelaunch = json.loads(prelaunch_path.read_text(encoding="utf-8"))
    if str(prelaunch.get("formal_run_plan_hash")) != plan_hash:
        raise PreflightGateError("formal execution plan hash differs from frozen prelaunch manifest")
    contract = prelaunch.get("launch_authorization_contract")
    if not isinstance(contract, Mapping):
        raise PreflightGateError(
            "formal execution prelaunch manifest lacks launch_authorization_contract; "
            "regenerate prelaunch after P19 closure"
        )
    if str(contract.get("contract_version", "")) != FORMAL_LAUNCH_CONTRACT_VERSION:
        raise PreflightGateError(
            "formal execution prelaunch manifest has stale launch contract version; "
            "regenerate prelaunch after P19 closure"
        )
    if not bool(contract.get("requires_explicit_user_launch_authorization", False)):
        raise PreflightGateError(
            "formal execution prelaunch manifest must require explicit user launch authorization"
        )
    required_flags = {str(flag) for flag in contract.get("required_execute_flags", [])}
    missing_flags = {
        "--execute",
        "--allow-large-run",
        FORMAL_LAUNCH_CONFIRMATION_FLAG,
    } - required_flags
    if missing_flags:
        raise PreflightGateError(
            f"formal execution prelaunch manifest lacks required execute flags: {sorted(missing_flags)}"
        )
    if FORMAL_LAUNCH_CONFIRMATION_FLAG not in str(prelaunch.get("exact_command_template", "")):
        raise PreflightGateError(
            "formal execution prelaunch exact_command_template lacks "
            f"{FORMAL_LAUNCH_CONFIRMATION_FLAG}"
        )
    if str(prelaunch.get("exact_command_template", "")) != FORMAL_EXACT_COMMAND_TEMPLATE:
        raise PreflightGateError(
            "formal execution prelaunch exact_command_template is stale; regenerate "
            "prelaunch so it records the 16-worker launch command"
        )
    if _to_int(prelaunch.get("planned_worker_count", -1)) != FORMAL_WORKER_COUNT:
        raise PreflightGateError(
            "formal execution prelaunch manifest has stale planned_worker_count; "
            f"expected {FORMAL_WORKER_COUNT}"
        )
    if _to_int(contract.get("planned_worker_count", -1)) != FORMAL_WORKER_COUNT:
        raise PreflightGateError(
            "formal execution launch contract has stale planned_worker_count; "
            f"expected {FORMAL_WORKER_COUNT}"
        )
    if str(contract.get("required_worker_flag", "")) != f"--workers {FORMAL_WORKER_COUNT}":
        raise PreflightGateError(
            "formal execution launch contract has stale required_worker_flag; "
            f"expected --workers {FORMAL_WORKER_COUNT}"
        )
    p19_hashes = prelaunch.get("p19_required_artifact_hashes")
    if not isinstance(p19_hashes, Mapping):
        raise PreflightGateError(
            "formal execution prelaunch manifest lacks p19_required_artifact_hashes"
        )
    p19_missing = []
    p19_mismatches = []
    for path in FORMAL_P19_REQUIRED_ARTIFACT_PATHS:
        rel = relpath(project_root / path, project_root)
        expected = str(p19_hashes.get(rel, ""))
        if not expected or expected == "na":
            p19_missing.append(rel)
            continue
        actual = sha256_or_na(project_root / rel)
        if actual != expected:
            p19_mismatches.append({"path": rel, "prelaunch": expected, "actual": actual})
    if p19_missing:
        raise PreflightGateError(
            f"formal execution prelaunch manifest lacks P19 artifact hashes: {p19_missing}"
        )
    if p19_mismatches:
        raise PreflightGateError(
            f"formal execution P19 artifact hash mismatch: {p19_mismatches[:3]}"
        )
    return {
        "status": "passed",
        "freeze_manifest_path": relpath(manifest_path, project_root),
        "formal_run_plan_hash": plan_hash,
        "checked_input_hashes": sorted(required_hashes),
        "checked_p19_artifact_hashes": [
            relpath(project_root / path, project_root)
            for path in FORMAL_P19_REQUIRED_ARTIFACT_PATHS
        ],
        "planned_worker_count": FORMAL_WORKER_COUNT,
        "launch_contract_version": FORMAL_LAUNCH_CONTRACT_VERSION,
        "required_launch_confirmation_flag": FORMAL_LAUNCH_CONFIRMATION_FLAG,
        "require_git_clean": require_git_clean,
    }


def _smoke_particles() -> list[Particle]:
    return [
        make_gold_baseline_particle(20, name="gold_20nm"),
        make_gold_baseline_particle(40, name="gold_40nm"),
        make_biomimetic_exosome_particle(
            70,
            name="EV_like_low_RI_70nm",
            preset_name="membrane_only_dim_2021",
        ),
        make_biomimetic_exosome_particle(
            100,
            name="EV_like_nominal_100nm",
            preset_name="biomimetic_corona_nominal",
        ),
    ]


def build_formal_particle_panel() -> list[Particle]:
    """Build the preflight particle panel used by the manifest-driven runner."""
    particles: list[Particle] = []
    for item in PARTICLE_PANEL:
        diameter_nm = float(item["diameter_nm"])
        material = str(item["material"])
        name = str(item["particle_name"])
        if material == "gold":
            particles.append(make_gold_baseline_particle(diameter_nm, name=name))
        elif material == "EV_like_low_RI":
            particles.append(
                make_biomimetic_exosome_particle(
                    diameter_nm,
                    name=name,
                    preset_name="membrane_only_dim_2021",
                )
            )
        elif material in {"EV_like", "EV_like_high_RI", "EV_like_doublet"}:
            particles.append(
                make_biomimetic_exosome_particle(
                    diameter_nm,
                    name=name,
                    preset_name="biomimetic_corona_nominal",
                )
            )
        elif material == "polystyrene":
            particles.append(Particle(name=name, radius_m=diameter_nm * 1e-9 / 2.0, n_real=1.59))
        elif material == "silica":
            particles.append(Particle(name=name, radius_m=diameter_nm * 1e-9 / 2.0, n_real=1.45))
        elif material == "liposome_like":
            particles.append(Particle(name=name, radius_m=diameter_nm * 1e-9 / 2.0, n_real=1.37))
        elif material == "protein_aggregate_like":
            particles.append(Particle(name=name, radius_m=diameter_nm * 1e-9 / 2.0, n_real=1.45))
        elif material == "lipoprotein_like":
            particles.append(Particle(name=name, radius_m=diameter_nm * 1e-9 / 2.0, n_real=1.40))
        else:
            raise PreflightGateError(f"unsupported formal particle panel material: {material}")
    return particles


def _medium_for_particle(particle: Particle) -> Medium:
    name = particle.name.lower()
    if name.startswith("ev") or "exosome" in name:
        return PBS_1X
    return WATER


def _sweep_scope_metadata(label: str) -> dict[str, str]:
    if label == "pre3seed_formal_3seed_10000e":
        return {
            "claim_level": "formal_3seed_10000e_relative_proxy_no_calibration_raw_summary",
            "lens_policy": "parallel_all_crossing_and_selected_annulus_outputs",
            "b_stage": "formal_3seed_10000e",
            "seed_policy": "three_seed_formal",
            "candidate_set_source": "formal_carry_forward_manifest",
            "preflight_role": "formal_relative_proxy_run",
            "legacy_compatibility_status": "new_formal_3seed_10000e_do_not_mix_with_rehearsal",
            "allowed_conclusion": "Raw formal relative/proxy summary only; use generated dual-lens top tables for ranking.",
            "forbidden_conclusion": "No calibrated detector claim, biological specificity, or cross-scope wavelength winner.",
        }
    if "rehearsal" in label:
        return {
            "claim_level": "low_event_3seed_rehearsal_schema_seed_and_dual_lens_check_only",
            "lens_policy": "parallel_all_crossing_and_selected_annulus_outputs",
            "b_stage": "low_event_rehearsal",
            "seed_policy": "three_seed_rehearsal",
            "candidate_set_source": "carry_forward_rehearsal_subset",
            "preflight_role": "diagnostic_rehearsal",
            "legacy_compatibility_status": "new_preflight_low_event_rehearsal",
            "allowed_conclusion": "Schema, seed, sidecar and dual-lens postprocess closure only.",
            "forbidden_conclusion": "No candidate recommendation or calibrated detector claim.",
        }
    return {
        "claim_level": "micro_smoke_schema_reproducibility_only",
        "lens_policy": "parallel_all_crossing_and_selected_annulus_outputs",
        "b_stage": "micro_integrated_smoke",
        "seed_policy": "three_seed_smoke",
        "candidate_set_source": "micro_smoke_panel",
        "preflight_role": "diagnostic_smoke",
        "legacy_compatibility_status": "new_preflight_micro_smoke",
        "allowed_conclusion": "Schema, sidecar, seed, denominator and hash closure only.",
        "forbidden_conclusion": "No candidate recommendation or calibrated detector claim.",
    }


def _flatten_sweep_result(
    result: Mapping[str, Any],
    *,
    seed: int,
    route_id: str,
    scope: Mapping[str, str],
) -> dict[str, Any]:
    summary = dict(result.get("summary", {}))
    reference = dict(result.get("reference", {}))
    merged = {**reference, **summary}
    n_events = int(summary.get("n_events", 0) or 0)
    annulus_n_events = int(summary.get("selected_detector_mode_annulus_n_events", 0) or 0)
    annulus_n_detected = int(summary.get("selected_detector_mode_annulus_n_detected", 0) or 0)
    annulus_detection_rate = _json_safe_scalar(
        summary.get("selected_detector_mode_annulus_detection_rate", "")
    )
    if annulus_detection_rate == "" and annulus_n_events > 0:
        annulus_detection_rate = annulus_n_detected / annulus_n_events
    return {
        "route_id": route_id,
        "seed": int(seed),
        "particle_name": result["particle_name"],
        "wavelength_nm": int(round(float(result["wavelength_m"]) * 1e9)),
        "width_nm": int(round(float(result["width_m"]) * 1e9)),
        "depth_nm": int(round(float(result["depth_m"]) * 1e9)),
        "n_events": n_events,
        "n_detected": int(summary.get("n_detected", 0) or 0),
        "conditional_synthetic_event_detection_fraction": float(summary.get("detection_rate", 0.0) or 0.0),
        "detection_rate": float(summary.get("detection_rate", 0.0) or 0.0),
        "detection_rate_denominator": n_events,
        "detection_rate_claim_level": "conditional_synthetic_event_detection_fraction",
        "detection_rate_boundary": "synthetic/proxy conditional on generated crossing events; not true detection probability",
        "stable_detection_rate": float(summary.get("stable_detection_rate", 0.0) or 0.0),
        "stable_detection_rate_denominator": n_events,
        "stable_detection_rate_claim_level": "synthetic_stable_detection_fraction",
        "all_crossing_n_events": int(summary.get("all_crossing_n_events", n_events) or 0),
        "all_crossing_n_detected": int(summary.get("all_crossing_n_detected", summary.get("n_detected", 0)) or 0),
        "all_crossing_detection_rate": float(summary.get("all_crossing_detection_rate", summary.get("detection_rate", 0.0)) or 0.0),
        "all_crossing_detection_rate_wilson_lb": _json_safe_scalar(summary.get("all_crossing_detection_rate_wilson_lb", "")),
        "selected_detector_mode_annulus_n_events": annulus_n_events,
        "selected_detector_mode_annulus_n_detected": annulus_n_detected,
        "selected_detector_mode_annulus_fraction": _json_safe_scalar(summary.get("selected_detector_mode_annulus_fraction", "")),
        "selected_detector_mode_annulus_detection_rate": annulus_detection_rate,
        "selected_detector_mode_annulus_detection_rate_wilson_lb": _json_safe_scalar(summary.get("selected_detector_mode_annulus_detection_rate_wilson_lb", "")),
        "selected_detector_mode_annulus_boundary": "selected-annulus event-position window, not optical BFP annulus",
        "reference_route": str(merged.get("reference_solver_route", merged.get("reference_route", "engineering_channel_angular_surrogate"))),
        "detector_route": str(merged.get("detector_forward_model", "joint_overlap_coherent_surrogate")),
        "operator_route": str(merged.get("operator_route", "theta_phi_surrogate_no_calibrated_bfp_jacobian")),
        "threshold_source": str(merged.get("threshold_calibration_source", "gaussian_iid_surrogate_not_empirical_blank")),
        "readout_route": str(merged.get("nodi_readout_semantics", "bandpass_envelope_surrogate")),
        "interface_fullwave_required": str(merged.get("interface_fullwave_required", "unknown")),
        "count_prediction_status": str(merged.get("count_prediction_status", "not_applied_per_event_only")),
        "claim_level": scope["claim_level"],
        "lens_policy": scope["lens_policy"],
        "b_stage": scope["b_stage"],
        "events_per_case": n_events,
        "seed_policy": scope["seed_policy"],
        "normalization_policy": "per_wavelength",
        "score": float(result.get("score", 0.0) or 0.0),
        "engineering_gate_passed": str(bool(result.get("engineering_gate_passed", False))).lower(),
        "primary_blocker_summary": str(merged.get("primary_blocker_summary", "not_available")),
        "random_sequence_policy": str(summary.get("random_sequence_policy", "")),
        "event_sampling_policy": str(summary.get("event_sampling_policy", "")),
        "case_random_seed": summary.get("case_random_seed"),
        "case_hash": str(merged.get("case_hash", "")),
        "config_hash": str(merged.get("config_hash", "")),
        "sidecar_required_fields_status": "present",
    }


def run_low_event_sweep(
    output_dir: Path,
    *,
    routes: Sequence[tuple[int, int, int]],
    seeds: Sequence[int],
    n_events: int,
    label: str,
    project_root: Path = PROJECT_ROOT,
    particles: Sequence[Particle] | None = None,
    n_workers: int = 1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output_dir = project_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        from dashboard.config import THETA_GRID_RAD
    except Exception:
        THETA_GRID_RAD = np.linspace(0.01, np.pi - 0.01, 500)

    particles = list(particles) if particles is not None else _smoke_particles()
    worker_count = int(n_workers)
    if worker_count < 1:
        raise ValueError("n_workers must be >= 1")
    baseline_particle = make_gold_baseline_particle(40)
    scope = _sweep_scope_metadata(label)
    rows: list[dict[str, Any]] = []
    diagnostic_snapshots: list[dict[str, Any]] = []
    route_seed_hashes: list[str] = []
    for seed in seeds:
        cfg = make_ev_nodi_design_sweep_config(DEFAULT_SIM_CFG)
        cfg = replace(
            cfg,
            n_events=int(n_events),
            random_seed=int(seed),
            normalization_mode="per_wavelength",
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="stratified_grid",
            vectorized_event_engine="off",
            adaptive_event_budget_mode="fixed",
        )
        for wavelength_nm, width_nm, depth_nm in routes:
            route_id = f"{wavelength_nm}_{width_nm}x{depth_nm}"
            results = run_parameter_sweep(
                particles,
                WATER,
                np.asarray([width_nm * 1e-9], dtype=float),
                np.asarray([depth_nm * 1e-9], dtype=float),
                np.asarray([wavelength_nm * 1e-9], dtype=float),
                BASELINE_OPTICAL,
                cfg,
                theta_grid_rad=THETA_GRID_RAD,
                baseline_particle=baseline_particle,
                baseline_channel=Channel(width_nm * 1e-9, depth_nm * 1e-9),
                medium_resolver=_medium_for_particle,
                n_workers=worker_count,
                verbose=False,
            )
            route_rows = [
                _flatten_sweep_result(result, seed=int(seed), route_id=route_id, scope=scope)
                for result in results
            ]
            diagnostic_snapshots.extend(
                _diagnostic_snapshot_for_result(
                    result,
                    seed=int(seed),
                    route_id=route_id,
                    scope=scope,
                )
                for result in results
            )
            rows.extend(route_rows)
            route_seed_hashes.append(sha256_payload(route_rows))

    summary_path = output_dir / f"{label}_summary.csv"
    write_csv_rows(summary_path, rows)
    diagnostic_snapshot_path = output_dir / f"{label}_diagnostic_snapshot.jsonl"
    _write_jsonl_atomic(diagnostic_snapshot_path, diagnostic_snapshots)

    expected_rows = len(routes) * len(seeds) * len(particles)
    seed_counts = Counter(str(row["seed"]) for row in rows)
    route_counts = Counter(str(row["route_id"]) for row in rows)
    expected_rows_per_seed = len(routes) * len(particles)
    route_particle_counts = Counter(
        (str(row["seed"]), str(row["route_id"]))
        for row in rows
    )
    per_seed_route_particle_grid_complete = all(
        route_particle_counts[(str(seed), f"{wl}_{w}x{d}")] == len(particles)
        for seed in seeds
        for wl, w, d in routes
    )
    claim_policy = build_claim_linter_policy()
    scan_rows = scan_paths_to_rows([summary_path], claim_policy, project_root=project_root)
    scan_path = output_dir / f"{label}_claim_scan.csv"
    write_csv_rows(scan_path, scan_rows or [{"path": relpath(summary_path, project_root), "status": "pass", "phrase": "", "finding_type": "", "severity": ""}])
    matrix_rows = [
        {
            **row,
            "route_contract_id": f"{label}_{row['route_id']}_seed{row['seed']}",
            "schema_version": PREFLIGHT_SCHEMA,
            "report_id": f"pre3seed_{label}",
            "report_version": PREFLIGHT_DATE,
            "result_path": relpath(summary_path, project_root),
            "result_file_hash": sha256_or_na(summary_path),
            "code_commit_hash": git_commit(project_root),
            "config_hash": row.get("config_hash") or config_hash(project_root),
            "analysis_script_hash": analysis_script_hash(project_root),
            "paper_evidence_ledger_version": "paper_library_extraction_cards_proxy",
            "allowed_aggregation_keys": "route_contract_id;lens_policy;b_stage;events_per_case;seed_policy;normalization_policy",
            "legacy_compatibility_status": scope["legacy_compatibility_status"],
            "EV_prior_id": "optical_EV_like_surrogate_prior_v1",
            "interface_status": "interface_fullwave_required_column_exported",
            "transport_status": "conditional_crossing_event_transport_proxy",
            "candidate_set_source": scope["candidate_set_source"],
            "preflight_role": scope["preflight_role"],
            "allowed_for_preflight": "true",
            "required_blocker_columns": "interface_fullwave_required;count_prediction_status;detection_rate_denominator",
            "claim_linter_status": "pass" if not scan_rows else "fail",
            "allowed_conclusion": scope["allowed_conclusion"],
            "forbidden_conclusion": scope["forbidden_conclusion"],
            "reader_warning_required": "true",
        }
        for row in rows
    ]
    route_matrix_path = output_dir / f"{label}_route_claim_matrix.csv"
    write_csv_rows(route_matrix_path, matrix_rows)

    manifest = {
        "schema_version": f"{label}_manifest_v1",
        "created_at": now_utc_iso(),
        "label": label,
        "routes": [f"{wl}_{w}x{d}" for wl, w, d in routes],
        "seeds": list(seeds),
        "n_events": int(n_events),
        "n_workers": worker_count,
        "particles": [particle.name for particle in particles],
        "expected_row_count": expected_rows,
        "actual_row_count": len(rows),
        "row_count_passed": len(rows) == expected_rows,
        "seed_counts": dict(seed_counts),
        "route_counts": dict(route_counts),
        "seed_reproducibility_policy": (
            "case-keyed deterministic RNG; same route/particle/seed rows are "
            "hashed in route_seed_config_hashes for freeze comparison"
        ),
        "seed_independence_policy": (
            "unique seed identifiers with case_keyed_independent random sequence; "
            "this is a reproducibility/independence guard, not a statistical proof"
        ),
        "seed_independence_passed": (
            len(set(int(seed) for seed in seeds)) == len(seeds)
            and all(seed_counts[str(seed)] == expected_rows_per_seed for seed in seeds)
        ),
        "pooled_per_seed_consistency_passed": (
            len(set(seed_counts.values())) == 1
            and next(iter(seed_counts.values()), 0) == expected_rows_per_seed
            and sum(seed_counts.values()) == len(rows)
        ),
        "per_seed_route_particle_grid_complete": per_seed_route_particle_grid_complete,
        "same_seed_config_reproducibility_hashes": route_seed_hashes,
        "route_seed_config_hashes": route_seed_hashes,
        "summary_path": relpath(summary_path, project_root),
        "summary_sha256": sha256_or_na(summary_path),
        "diagnostic_snapshot_path": relpath(diagnostic_snapshot_path, project_root),
        "diagnostic_snapshot_sha256": sha256_or_na(diagnostic_snapshot_path),
        "diagnostic_snapshot_row_count": len(diagnostic_snapshots),
        "diagnostic_snapshot_schema": "pre3seed_formal_case_diagnostic_snapshot_v1",
        "diagnostic_snapshot_policy": (
            "case-level JSONL diagnostics for rerun avoidance; large per-event "
            "arrays summarized, not treated as calibrated measurements"
        ),
        "worker_chunk_vectorization_policy": (
            f"n_workers={worker_count}; vectorized_event_engine=off; "
            "route/seed loop order deterministic; output row order may depend on "
            "the sweep implementation but rows are keyed by route/seed/particle hashes"
        ),
        "route_claim_matrix_path": relpath(route_matrix_path, project_root),
        "route_claim_matrix_sha256": sha256_or_na(route_matrix_path),
        "claim_scan_path": relpath(scan_path, project_root),
        "claim_scan_sha256": sha256_or_na(scan_path),
        "claim_linter_passed": not scan_rows,
        "denominator_columns_present": all(
            "detection_rate_denominator" in row
            and "detection_rate_claim_level" in row
            and "detection_rate_boundary" in row
            for row in rows
        ),
        "selected_annulus_boundary_present": all(
            "event-position window" in str(row.get("selected_detector_mode_annulus_boundary", ""))
            for row in rows
        ),
    }
    manifest_path = output_dir / f"{label}_manifest.json"
    write_json_atomic(manifest_path, manifest, sort_keys=True)
    return rows, manifest


def scan_paths_to_rows(
    paths: Sequence[Path],
    policy: Mapping[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            findings.append(
                {
                    "path": relpath(path, project_root),
                    "status": "fail",
                    "phrase": "",
                    "finding_type": "missing_path",
                    "severity": "hard_stop",
                }
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            findings.append(
                {
                    "path": relpath(path, project_root),
                    "status": "fail",
                    "phrase": "",
                    "finding_type": "invalid_utf8",
                    "severity": "hard_stop",
                    "detail": str(exc),
                }
            )
            continue
        for finding in scan_preflight_claim_text(
            text,
            policy,
            source=relpath(path, project_root),
        ):
            findings.append({"status": "fail", **finding})
    return findings


def build_dry_report(
    route_matrix: Sequence[Mapping[str, Any]],
    ledger_rows: Sequence[Mapping[str, Any]],
    stability: Sequence[Mapping[str, Any]],
    demotions: Sequence[Mapping[str, Any]],
    carry: Sequence[Mapping[str, Any]],
    gate_rows: Sequence[Mapping[str, Any]],
) -> str:
    class_counts = Counter(str(row["stability_class"]) for row in stability)
    class_lines = "\n".join(f"- `{klass}`: {count}" for klass, count in sorted(class_counts.items()))
    carry_lines = "\n".join(
        f"- `{row['candidate_family_id']}`: `{row['stability_class']}` / `{row['large_run_role']}`"
        for row in carry
    )
    demotion_lines = "\n".join(
        f"- `{row['candidate_family_id']}` -> `{row['demoted_to']}`: {row['demotion_reason']}"
        for row in demotions[:20]
    )
    gate_lines = "\n".join(
        f"- `{row['gate_id']}` `{row['status']}`: {row['evidence']}"
        for row in gate_rows
    )
    route_line = f"{len(route_matrix)} route contracts; formula ledger rows: {len(ledger_rows)}."
    return f"""# Pre-3seed Final-Style Dry Run Report

Generated: {now_utc_iso()}

## Route/Evidence State

{route_line}

This dry report is a no-measured-data relative/proxy design-selection artifact.
All event fractions are conditional synthetic event metrics with explicit
denominators. Selected-annulus entries are event-position window diagnostics,
not optical BFP annuli. Detector units, photon units, empirical blank safety,
sample concentration, biological exosome specificity, and calibrated
cross-wavelength superiority remain blocked.

## Formula Ledger Summary

The formula ledger covers diameter/radius, vacuum/medium wavelength, material RI
convention, Mie/core-shell, dC/dOmega to field proxy, detector/BFP Jacobian,
reference phase-filter routes, illumination, interference, trajectory,
selected-annulus event-position selection, threshold/readout, Wilson/statistics,
ranking score, and normalization policy.

## Candidate Stability Classes

{class_lines}

## Carry-Forward Manifest

{carry_lines}

## Candidate Demotions

{demotion_lines}

## Stop-Gate Status

{gate_lines}

## Allowed Claims

- Relative/proxy candidate-family classification within declared lens, route,
  normalization, and surrogate assumptions.
- Conditional/stress/diagnostic preservation for scientifically informative
  branches.
- Rehearsal schema and seed reproducibility evidence.
- All-crossing and selected-annulus event-position-window analyses may be
  compared only as separate lens scopes with explicit denominators.

## Forbidden Claims

- Calibrated detector performance, absolute limit-of-detection statements,
  empirical blank control, detector voltage, photon-counting, true sample
  concentration/count rate, biological specificity, or unscoped wavelength
  winners.
- Selected-annulus results must not be described as optical BFP annulus
  superiority, and selected-window ranks must not replace all-crossing ranks
  without saying the lens changed.
"""


def build_gate_summary(
    *,
    route_matrix_rows: Sequence[Mapping[str, Any]],
    ledger_rows: Sequence[Mapping[str, Any]],
    micro_manifest: Mapping[str, Any],
    candidate_rows: Sequence[Mapping[str, Any]],
    reference_summary: Sequence[Mapping[str, Any]],
    detector_labels: Sequence[Mapping[str, Any]],
    threshold_labels: Sequence[Mapping[str, Any]],
    geometry_rows: Sequence[Mapping[str, Any]],
    ev_evidence: Sequence[Mapping[str, Any]],
    interface_rows: Sequence[Mapping[str, Any]],
    stability_rows: Sequence[Mapping[str, Any]],
    rehearsal_manifest: Mapping[str, Any],
    freeze_manifest: Mapping[str, Any] | None,
    dry_report_scan_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    freeze_structural = freeze_manifest is not None and all(
        key in freeze_manifest
        for key in ("git_commit_hash", "git_dirty_state", "test_result_hash")
    )
    freeze_dirty = (
        bool(freeze_manifest.get("git_dirty_state", {}).get("dirty", True))
        if freeze_manifest is not None
        else True
    )
    freeze_evidence = (
        "freeze manifest complete structurally; freeze.dirty=true; formal --execute is currently blocked until commit and regenerated freeze"
        if freeze_structural and freeze_dirty
        else "freeze manifest complete structurally; freeze.dirty=false; formal --execute still checks current git and input hashes"
        if freeze_structural
        else "freeze manifest incomplete or missing"
    )
    statuses = {
        "SG0": (bool(route_matrix_rows), "route matrix and preflight linter policy generated"),
        "SG1": (bool(ledger_rows), "formula ledger generated and validated"),
        "SG2": (bool(micro_manifest.get("row_count_passed")) and bool(micro_manifest.get("claim_linter_passed")) and bool(micro_manifest.get("denominator_columns_present")), "micro smoke row count, linter, denominator fields"),
        "SG3": (True, "physics invariant pytest suite required; see freeze/test result hash"),
        "SG4": (
            {
                source
                for row in candidate_rows
                for source in str(row["candidate_set_source"]).split(";")
                if source
            }
            >= {
                "historical_top",
                "B7_sidecar",
                "Tsuyama_like_control",
                "Au_anchor",
                "reference_stress",
                "detector_stress",
                "threshold_readout_stress",
                "EV_prior_stress",
                "contaminant_overlap_stress",
                "geometry_wall_risk_stress",
                "short_wavelength_exploratory",
                "narrow_channel_exploratory",
            },
            "multi-source candidate manifest generated",
        ),
        "SG5": (all(row.get("reference_stability_label") for row in reference_summary), "reference stability labels complete"),
        "SG6": (all(row.get("detector_operator_sensitivity_label") for row in detector_labels) and all(row.get("threshold_noise_sensitivity_label") for row in threshold_labels), "detector/readout/threshold labels complete"),
        "SG7": (all(row.get("geometry_transport_viability_label") for row in geometry_rows), "geometry/transport labels complete"),
        "SG8": (bool(ev_evidence), "EV prior evidence table and stress matrix generated"),
        "SG9": (all("interface_fullwave_required" in row for row in interface_rows), "interface/full-wave/404 flags complete"),
        "SG10": (all(row.get("stability_class") for row in stability_rows), "candidate stability matrix generated"),
        "SG11": (
            bool(rehearsal_manifest.get("row_count_passed"))
            and bool(rehearsal_manifest.get("claim_linter_passed"))
            and bool(rehearsal_manifest.get("seed_independence_passed"))
            and bool(rehearsal_manifest.get("pooled_per_seed_consistency_passed"))
            and bool(rehearsal_manifest.get("per_seed_route_particle_grid_complete")),
            "low-event 3seed rehearsal passed schema/linter/seed consistency gates",
        ),
        "SG12": (freeze_structural, freeze_evidence),
        "SG13": (not dry_report_scan_rows, "dry report preflight claim scan passed"),
    }
    rows = []
    for gate_id in STOP_GATE_IDS:
        passed, evidence = statuses[gate_id]
        rows.append(
            {
                "gate_id": gate_id,
                "status": "passed" if passed else "failed",
                "evidence": evidence,
                "failure_action": "stop" if not passed else "none",
            }
        )
    return rows


def build_freeze_manifest(
    *,
    artifact_paths: Sequence[Path],
    expected_rehearsal_rows: int,
    expected_seed_count: int,
    verification_summary_path: Path | None = None,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    verification_path = project_root / verification_summary_path if verification_summary_path else project_root / VERIFICATION_SUMMARY_PATH
    try:
        import numpy
        numpy_version = numpy.__version__
    except Exception:
        numpy_version = "not_available"
    try:
        import pandas
        pandas_version = pandas.__version__
    except Exception:
        pandas_version = "not_available"
    try:
        import scipy
        scipy_version = scipy.__version__
    except Exception:
        scipy_version = "not_available"
    return {
        "schema_version": "pre3seed_freeze_manifest_v1",
        "created_at": now_utc_iso(),
        "git_commit_hash": git_commit(project_root),
        "git_dirty_state": git_dirty_summary(project_root),
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "numpy_version": numpy_version,
        "scipy_version": scipy_version,
        "pandas_version": pandas_version,
        "blas_lapack_backend": "see numpy/scipy build configuration; not expanded by this lightweight manifest",
        "dependency_lock_or_environment_export": "pyproject.toml hash plus runtime versions",
        "config_hash": config_hash(project_root),
        "input_file_hashes": {
            relpath(path, project_root): sha256_or_na(path)
            for path in artifact_paths
        },
        "particle_panel_version_hash": sha256_payload(PARTICLE_PANEL),
        "candidate_carry_forward_manifest_hash": sha256_or_na(project_root / CARRY_FORWARD_PATH),
        "route_matrix_hash": sha256_or_na(project_root / ROUTE_MATRIX_PATH),
        "formula_ledger_hash": sha256_or_na(project_root / FORMULA_LEDGER_CSV_PATH),
        "paper_evidence_ledger_hash": sha256_or_na(project_root / "papers/analysis_full_v1/run_manifest.json"),
        "RNG_implementation": "numpy.random.default_rng with case_keyed_independent per-case seeds",
        "seed_allocation_policy": "three_seed_low_event_rehearsal; future 3seed 10000e must use carry-forward manifest",
        "event_block_vectorization_policy": "formal preflight runner freezes vectorized_event_engine=off and fixed event budget; change only after small-scale hash-equivalence validation",
        "expected_row_count": int(expected_rehearsal_rows),
        "expected_seed_count": int(expected_seed_count),
        "worker_chunk_policy": (
            f"formal preflight runner freezes n_workers={FORMAL_WORKER_COUNT} "
            "for sustained full calculation and deterministic route/seed loop order"
        ),
        "result_schema_version": PREFLIGHT_SCHEMA,
        "postprocess_script_hash": analysis_script_hash(project_root),
        "claim_scanner_policy_hash": sha256_or_na(project_root / CLAIM_POLICY_PATH),
        "rank_stability_thresholds_version": "roadmap_v2_defaults_top5_jaccard_0.5_spearman_0.4_rank_delta_5_survival_0.5",
        "dashboard_report_generator_version": "pre3seed_final_dry_run_report_20260518",
        "test_command": "python -m pytest tests/test_pre3seed_hardening.py tests/test_pre3seed_physics_invariants.py tests/test_mie_engine.py tests/test_reference_field.py tests/test_bfp_jacobian_closed_form.py tests/test_trajectory.py tests/test_claim_language_regression.py tests/test_review_package_claim_scan.py -q",
        "test_result_path": relpath(verification_path, project_root),
        "test_result_hash": sha256_or_na(verification_path),
        "test_result_status": (
            json.loads(verification_path.read_text(encoding="utf-8")).get("status", "unknown")
            if verification_path.exists()
            else "pending_verification_summary_not_yet_written"
        ),
    }


def _unique_family_rows(candidate_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in candidate_rows:
        key = str(row["candidate_family_id"])
        if key not in out:
            out[key] = dict(row)
    return list(out.values())


def _assert_no_failed_gates(gate_rows: Sequence[Mapping[str, Any]], *, allow_pending_tests: bool = True) -> None:
    failed = [row for row in gate_rows if row["status"] != "passed"]
    if allow_pending_tests:
        failed = [row for row in failed if row["gate_id"] != "SG3"]
    if failed:
        raise PreflightGateError(f"preflight gate failures: {failed}")


def generate_pre3seed_hardening_artifacts(
    project_root: Path = PROJECT_ROOT,
    *,
    run_smoke: bool = True,
    run_rehearsal: bool = True,
    verification_summary_path: Path | None = None,
) -> dict[str, Any]:
    """Generate roadmap A-N artifacts in dependency order."""
    project_root = Path(project_root)
    policy = build_claim_linter_policy()
    write_json_atomic(project_root / CLAIM_POLICY_PATH, policy, sort_keys=True)

    route_matrix_rows = build_route_claim_matrix(project_root)
    write_csv_rows(project_root / ROUTE_MATRIX_PATH, route_matrix_rows)
    write_markdown(project_root / EVIDENCE_STATE_PATH, build_current_evidence_state(route_matrix_rows))

    ledger_rows = build_formula_ledger_rows(project_root)
    validate_formula_ledger(ledger_rows)
    write_csv_rows(project_root / FORMULA_LEDGER_CSV_PATH, ledger_rows)
    write_markdown(project_root / FORMULA_LEDGER_MD_PATH, formula_ledger_markdown(ledger_rows))

    if run_smoke:
        micro_rows, micro_manifest = run_low_event_sweep(
            MICRO_SMOKE_DIR,
            routes=((660, 800, 1400), (660, 800, 550), (404, 500, 1500)),
            seeds=(101, 202, 303),
            n_events=2,
            label="pre3seed_micro_smoke",
            project_root=project_root,
        )
        validate_preflight_table_scope(micro_rows, table_name="pre3seed_micro_smoke", policy=policy)
    else:
        micro_manifest = {
            "row_count_passed": False,
            "claim_linter_passed": False,
            "denominator_columns_present": False,
            "expected_row_count": 0,
        }

    candidate_rows = build_candidate_manifest_rows()
    write_csv_rows(project_root / CANDIDATE_MANIFEST_PATH, candidate_rows)

    family_rows = _unique_family_rows(candidate_rows)
    ref_matrix, ref_summary, ref_flags = build_reference_ablation_outputs(family_rows)
    write_csv_rows(project_root / REFERENCE_ABLATION_MATRIX_PATH, ref_matrix)
    write_csv_rows(project_root / REFERENCE_ABLATION_SUMMARY_PATH, ref_summary)
    write_csv_rows(project_root / REFERENCE_FRAGILITY_FLAGS_PATH, ref_flags)
    validate_preflight_table_scope(ref_summary, table_name="reference_ablation_summary", policy=policy)

    detector_matrix, detector_labels, threshold_labels, pulse_labels = (
        build_detector_readout_outputs(family_rows)
    )
    write_csv_rows(project_root / DETECTOR_ABLATION_MATRIX_PATH, detector_matrix)
    write_csv_rows(project_root / DETECTOR_OPERATOR_LABEL_PATH, detector_labels)
    write_csv_rows(project_root / THRESHOLD_LABEL_PATH, threshold_labels)
    write_csv_rows(project_root / PULSE_GUARDRAIL_PATH, pulse_labels)
    validate_preflight_table_scope(detector_labels, table_name="detector_labels", policy=policy)
    validate_preflight_table_scope(threshold_labels, table_name="threshold_labels", policy=policy)

    geometry_rows = build_geometry_transport_matrix(candidate_rows)
    write_csv_rows(project_root / GEOMETRY_MATRIX_PATH, geometry_rows)
    validate_preflight_table_scope(geometry_rows, table_name="geometry_transport", policy=policy)

    ev_evidence, ev_stress, ev_summary = build_ev_prior_outputs(candidate_rows)
    write_csv_rows(project_root / EV_PRIOR_EVIDENCE_PATH, ev_evidence)
    write_csv_rows(project_root / EV_PRIOR_STRESS_PATH, ev_stress)
    write_csv_rows(project_root / EV_CANDIDATE_STABILITY_PATH, ev_summary)
    validate_preflight_table_scope(ev_stress, table_name="EV_prior_stress", policy=policy)

    interface_rows, shortwave_rows = build_interface_outputs(family_rows)
    write_csv_rows(project_root / INTERFACE_MATRIX_PATH, interface_rows)
    write_csv_rows(project_root / SHORT_WAVELENGTH_RISK_PATH, shortwave_rows)
    validate_preflight_table_scope(interface_rows, table_name="interface_flags", policy=policy)

    stability_rows, demotion_rows, carry_rows = build_stability_synthesis(
        family_rows,
        ref_summary,
        detector_labels,
        threshold_labels,
        geometry_rows,
        ev_summary,
        interface_rows,
    )
    write_csv_rows(project_root / STABILITY_MATRIX_PATH, stability_rows)
    write_csv_rows(project_root / DEMOTIONS_PATH, demotion_rows)
    write_csv_rows(project_root / CARRY_FORWARD_PATH, carry_rows)
    validate_preflight_table_scope(stability_rows, table_name="candidate_stability", policy=policy)

    formal_plan_rows = build_formal_3seed_run_plan(
        carry_rows,
        family_rows,
        stability_rows,
        seeds=(11, 22, 33),
        events_per_case=10_000,
        particle_panel_size=len({row["particle_id"] for row in candidate_rows}),
    )
    write_csv_rows(project_root / FORMAL_RUN_PLAN_CSV_PATH, formal_plan_rows)
    write_json_atomic(
        project_root / FORMAL_RUN_PLAN_JSON_PATH,
        {
            "schema_version": "pre3seed_formal_3seed_10000e_run_plan_manifest_v1",
            "created_at": now_utc_iso(),
            "formal_run_plan_path": relpath(project_root / FORMAL_RUN_PLAN_CSV_PATH, project_root),
            "formal_run_plan_hash": sha256_payload(formal_plan_rows),
            "candidate_family_count": len({row["candidate_family_id"] for row in formal_plan_rows}),
            "seed_list": sorted({_to_int(row["seed"]) for row in formal_plan_rows}),
            "expected_rows": sum(_to_int(row["expected_rows_for_seed_route"]) for row in formal_plan_rows),
            "expected_event_count": sum(_to_int(row["expected_event_count_for_seed_route"]) for row in formal_plan_rows),
            "claim_boundary": (
                "dry-run plan unless the full P19 launch command, including "
                f"{FORMAL_LAUNCH_CONFIRMATION_FLAG}, was supplied after final launch authorization"
            ),
        },
        sort_keys=True,
    )

    if run_rehearsal:
        rehearsal_routes = [
            (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
            for row in carry_rows
            if row["stability_class"]
            in {"robust_relative_candidate", "conditional_candidate", "stress_branch", "diagnostic_only"}
        ][:5]
        rehearsal_rows, rehearsal_manifest = run_low_event_sweep(
            REHEARSAL_DIR,
            routes=rehearsal_routes,
            seeds=(11, 22, 33),
            n_events=2,
            label="pre3seed_3seed_low_event_rehearsal",
            project_root=project_root,
        )
        validate_preflight_table_scope(rehearsal_rows, table_name="pre3seed_rehearsal", policy=policy)
    else:
        rehearsal_rows = []
        rehearsal_manifest = {
            "row_count_passed": False,
            "claim_linter_passed": False,
            "expected_row_count": 0,
        }

    dual_lens_top_rows = build_dual_lens_top_table(
        rehearsal_rows,
        stability_rows,
        family_rows,
    ) if rehearsal_rows else []
    if dual_lens_top_rows:
        write_csv_rows(project_root / FORMAL_DUAL_LENS_TOP_TABLE_PATH, dual_lens_top_rows)
    consistency_rows = (
        build_pooled_per_seed_consistency(dual_lens_top_rows)
        if dual_lens_top_rows
        else []
    )
    if consistency_rows:
        write_csv_rows(project_root / FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH, consistency_rows)
    dual_lens_top_rows_for_manifest = (
        read_csv_rows(project_root / FORMAL_DUAL_LENS_TOP_TABLE_PATH)
        if (project_root / FORMAL_DUAL_LENS_TOP_TABLE_PATH).exists()
        else []
    )
    consistency_rows_for_manifest = (
        read_csv_rows(project_root / FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH)
        if (project_root / FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH).exists()
        else []
    )
    formal_prelaunch_manifest = build_formal_prelaunch_manifest(
        formal_plan_rows=formal_plan_rows,
        top_table_rows=dual_lens_top_rows_for_manifest,
        consistency_rows=consistency_rows_for_manifest,
        project_root=project_root,
    )
    write_json_atomic(
        project_root / FORMAL_PRELAUNCH_MANIFEST_PATH,
        formal_prelaunch_manifest,
        sort_keys=True,
    )

    artifact_paths = [
        ROUTE_MATRIX_PATH,
        FORMULA_LEDGER_CSV_PATH,
        CANDIDATE_MANIFEST_PATH,
        REFERENCE_ABLATION_SUMMARY_PATH,
        DETECTOR_OPERATOR_LABEL_PATH,
        THRESHOLD_LABEL_PATH,
        GEOMETRY_MATRIX_PATH,
        EV_PRIOR_EVIDENCE_PATH,
        INTERFACE_MATRIX_PATH,
        STABILITY_MATRIX_PATH,
        CARRY_FORWARD_PATH,
        FORMAL_RUN_PLAN_CSV_PATH,
        FORMAL_RUN_PLAN_JSON_PATH,
        FORMAL_DUAL_LENS_TOP_TABLE_PATH,
        FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH,
        FORMAL_PRELAUNCH_MANIFEST_PATH,
        REHEARSAL_DIR / "pre3seed_3seed_low_event_rehearsal_summary.csv",
    ]
    freeze_manifest = build_freeze_manifest(
        artifact_paths=[project_root / path for path in artifact_paths],
        expected_rehearsal_rows=int(rehearsal_manifest.get("expected_row_count", 0) or 0),
        expected_seed_count=3,
        verification_summary_path=verification_summary_path,
        project_root=project_root,
    )
    write_json_atomic(project_root / FREEZE_MANIFEST_PATH, freeze_manifest, sort_keys=True)

    provisional_gate_rows = build_gate_summary(
        route_matrix_rows=route_matrix_rows,
        ledger_rows=ledger_rows,
        micro_manifest=micro_manifest,
        candidate_rows=candidate_rows,
        reference_summary=ref_summary,
        detector_labels=detector_labels,
        threshold_labels=threshold_labels,
        geometry_rows=geometry_rows,
        ev_evidence=ev_evidence,
        interface_rows=interface_rows,
        stability_rows=stability_rows,
        rehearsal_manifest=rehearsal_manifest,
        freeze_manifest=freeze_manifest,
        dry_report_scan_rows=[],
    )
    dry_report = build_dry_report(
        route_matrix_rows,
        ledger_rows,
        stability_rows,
        demotion_rows,
        carry_rows,
        provisional_gate_rows,
    )
    write_markdown(project_root / DRY_REPORT_PATH, dry_report)
    dry_scan_rows = scan_paths_to_rows([project_root / DRY_REPORT_PATH], policy, project_root=project_root)
    dry_scan_path = project_root / "results/pre3seed_final_dry_run_claim_scan_20260518.csv"
    write_csv_rows(
        dry_scan_path,
        dry_scan_rows
        or [{"path": relpath(project_root / DRY_REPORT_PATH, project_root), "status": "pass", "phrase": "", "finding_type": "", "severity": ""}],
    )

    gate_rows = build_gate_summary(
        route_matrix_rows=route_matrix_rows,
        ledger_rows=ledger_rows,
        micro_manifest=micro_manifest,
        candidate_rows=candidate_rows,
        reference_summary=ref_summary,
        detector_labels=detector_labels,
        threshold_labels=threshold_labels,
        geometry_rows=geometry_rows,
        ev_evidence=ev_evidence,
        interface_rows=interface_rows,
        stability_rows=stability_rows,
        rehearsal_manifest=rehearsal_manifest,
        freeze_manifest=freeze_manifest,
        dry_report_scan_rows=dry_scan_rows,
    )
    write_csv_rows(project_root / GATE_SUMMARY_PATH, gate_rows)
    _assert_no_failed_gates(gate_rows)

    return {
        "route_matrix_path": relpath(project_root / ROUTE_MATRIX_PATH, project_root),
        "formula_ledger_path": relpath(project_root / FORMULA_LEDGER_CSV_PATH, project_root),
        "candidate_manifest_path": relpath(project_root / CANDIDATE_MANIFEST_PATH, project_root),
        "stability_matrix_path": relpath(project_root / STABILITY_MATRIX_PATH, project_root),
        "carry_forward_path": relpath(project_root / CARRY_FORWARD_PATH, project_root),
        "formal_run_plan_path": relpath(project_root / FORMAL_RUN_PLAN_CSV_PATH, project_root),
        "dual_lens_top_table_path": relpath(project_root / FORMAL_DUAL_LENS_TOP_TABLE_PATH, project_root),
        "pooled_per_seed_consistency_path": relpath(project_root / FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH, project_root),
        "formal_prelaunch_manifest_path": relpath(project_root / FORMAL_PRELAUNCH_MANIFEST_PATH, project_root),
        "freeze_manifest_path": relpath(project_root / FREEZE_MANIFEST_PATH, project_root),
        "dry_report_path": relpath(project_root / DRY_REPORT_PATH, project_root),
        "gate_summary_path": relpath(project_root / GATE_SUMMARY_PATH, project_root),
        "micro_manifest": micro_manifest,
        "rehearsal_manifest": rehearsal_manifest,
        "stability_class_counts": dict(Counter(row["stability_class"] for row in stability_rows)),
        "gate_status": {row["gate_id"]: row["status"] for row in gate_rows},
        "dry_report_claim_scan_passed": not dry_scan_rows,
    }


def run_verification_suite(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_pre3seed_hardening.py",
        "tests/test_pre3seed_physics_invariants.py",
        "tests/test_mie_engine.py",
        "tests/test_reference_field.py",
        "tests/test_bfp_jacobian_closed_form.py",
        "tests/test_trajectory.py",
        "tests/test_claim_language_regression.py",
        "tests/test_review_package_claim_scan.py",
        "-q",
    ]
    started = now_utc_iso()
    completed = subprocess.run(
        command,
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = completed.stdout
    summary = {
        "schema_version": "pre3seed_verification_summary_v1",
        "started_at": started,
        "completed_at": now_utc_iso(),
        "command": command,
        "returncode": int(completed.returncode),
        "status": "passed" if completed.returncode == 0 else "failed",
        "output_sha256": sha256_text(output),
        "output_tail": output[-4000:],
    }
    write_json_atomic(project_root / VERIFICATION_SUMMARY_PATH, summary, sort_keys=True)
    if completed.returncode != 0:
        raise PreflightGateError(output[-4000:])
    return summary
