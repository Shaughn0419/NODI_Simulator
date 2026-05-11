"""
dashboard/precompute.py — 预计算 sweep 并保存结果

Usage:
    python -m nodi_simulator.dashboard.precompute --grid coarse --tag default --output results/
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import time
from collections import Counter
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from datetime import datetime, timedelta
from typing import Any, cast

import numpy as np
import pandas as pd

import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for candidate in (PROJECT_ROOT,):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator._exports import (
    BASELINE_CHANNEL,
    classify_design_recommendation,
    classify_engineering_gate_explanation,
)
from nodi_simulator.data_objects import (
    ADAPTIVE_EVENT_BUDGET_MODE_OPTIONS,
    EVENT_BLOCK_RNG_ORDER_OPTIONS,
    EVENT_SAMPLING_POLICY_OPTIONS,
    RANDOM_SEQUENCE_POLICY_OPTIONS,
    VECTORIZED_EVENT_ENGINE_OPTIONS,
    make_ev_nodi_design_sweep_config,
)
from nodi_simulator.channel_geometry_model import CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS
from nodi_simulator.assay_control_matrix import ASSAY_CONTROL_DIAGNOSTIC_FIELDS
from nodi_simulator.bfp_detector_operator import BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS
from nodi_simulator.control_interpretation import CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS
from nodi_simulator.particle_channel_perturbation import (
    PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS,
)
from nodi_simulator.design_claim_governance import (
    CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
    DESIGN_CLAIM_GOVERNANCE_FIELDS,
    MINIMUM_OUTPUT_SCHEMA_FIELDS,
    PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
    require_claim_level,
    require_paper_alignment_target,
)
from nodi_simulator.design_metrics import DESIGN_METRIC_DIAGNOSTIC_FIELDS
from nodi_simulator.design_postprocess import (
    EV_DESIGN_POSTPROCESS_FIELDS,
    generate_claim_boundary_text,
)
from nodi_simulator.electrokinetic_transport import ELECTROKINETIC_DIAGNOSTIC_FIELDS
from nodi_simulator.event_quality_control import EVENT_QC_DIAGNOSTIC_FIELDS
from nodi_simulator.ev_integrity_risk import EV_INTEGRITY_DIAGNOSTIC_FIELDS
from nodi_simulator.ev_reporting_metadata import EV_REPORTING_DIAGNOSTIC_FIELDS
from nodi_simulator.fluidic_network_model import FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS
from nodi_simulator.fluidic_resistance import FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS
from nodi_simulator.materials import MATERIAL_DB
from nodi_simulator.parameter_sweep import (
    build_sweep_case_key,
    run_parameter_sweep,
    summarize_vectorized_fallback_telemetry,
)
from nodi_simulator.count_likelihood import COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS
from nodi_simulator.ood_detection import OOD_DIAGNOSTIC_FIELDS
from nodi_simulator.bayesian_calibration import (
    BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS,
)
from nodi_simulator.experimental_design_advisor import (
    EXPERIMENTAL_DESIGN_ADVISOR_FIELDS,
)
from nodi_simulator.population_inference import POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
from nodi_simulator.objective_panel import OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS
from nodi_simulator.particle_design_library import (
    EV_SAMPLE_PREPARATION_PROFILES,
    PARTICLE_CONTAMINANT_PRESETS,
    PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS,
    STANDARD_PARTICLE_PRESETS,
)
from nodi_simulator.ev_population_prior import EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS
from nodi_simulator.reference_field import TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS
from nodi_simulator.reference_operating_point import (
    REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS,
)
from nodi_simulator.readout_transfer_model import READOUT_TRANSFER_DIAGNOSTIC_FIELDS
from nodi_simulator.recompute_manifest import RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS
from nodi_simulator.run_state_model import RUN_STATE_DIAGNOSTIC_FIELDS
from nodi_simulator.nodi_thermal_contamination import (
    NODI_THERMAL_CONTAMINATION_FIELDS,
)
from nodi_simulator.polarization_jones_operator import (
    POLARIZATION_JONES_DIAGNOSTIC_FIELDS,
)
from nodi_simulator.selection_function import SELECTION_FUNCTION_DIAGNOSTIC_FIELDS
from nodi_simulator.wavelength_comparability import (
    WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS,
)

from nodi_simulator.dashboard.config import (
    BASELINE_PARTICLE, MEDIUM,
    OPTICAL_TEMPLATE, DEFAULT_SIM_CFG, THETA_GRID_RAD, GRID_CONFIGS,
    PRECOMPUTE_PROFILES, PRECOMPUTE_PROFILE_DEFAULT,
    get_precompute_particles, get_precompute_profile,
    infer_particle_material, infer_particle_diameter_nm,
    medium_for_particle,
)
from nodi_simulator.dashboard.safe_pickle import (
    dump_dashboard_pickle,
    load_dashboard_pickle,
)


_SAFE_CONFIG_TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


SavePayloadBuilder = Callable[[], Any]
SavePayloadWriter = Callable[[str, Any], None]
SaveAfterWriteHook = Callable[[Any], None]
SaveLogMessageBuilder = Callable[[Any, str], str | None]

ARTIFACT_PROFILE_FULL = "full"
ARTIFACT_PROFILE_STANDARD = "standard"
ARTIFACT_PROFILE_MINIMAL = "minimal"
ARTIFACT_PROFILES = (
    ARTIFACT_PROFILE_FULL,
    ARTIFACT_PROFILE_STANDARD,
    ARTIFACT_PROFILE_MINIMAL,
)
MIN_CHECKPOINT_FLUSH_INTERVAL_S = 1.0


@dataclass(frozen=True)
class PrecomputeSaveStep:
    """One save stage in the precompute export pipeline."""

    stage_name: str
    output_key: str | None
    path: str
    build_payload: SavePayloadBuilder
    writer: SavePayloadWriter
    after_write: SaveAfterWriteHook | None = None
    log_message: SaveLogMessageBuilder | None = None


@dataclass(frozen=True)
class PrecomputeArtifactPaths:
    """Canonical artifact paths for one precompute job prefix."""

    progress_json: str
    checkpoint_dir: str
    checkpoint_chunks_dir: str
    checkpoint_manifest_json: str
    summary_csv: str
    case_summary_csv: str
    case_summary_parquet: str
    design_postprocess_csv: str
    physics_fields_parquet: str
    diagnostics_long_parquet: str
    compact_pkl: str
    meta_json: str
    result_health_json: str
    runtime_performance_json: str
    freeze_probe_json: str


@dataclass(frozen=True)
class PrecomputeArtifactCopy:
    """Request to atomically copy an already-written artifact."""

    source_path: str
    row_count: int | None = None


@dataclass(frozen=True)
class PrecomputeMetadata:
    """Serializable metadata payload for one exported precompute dataset."""

    dashboard_schema_version: str
    model_semantics_version: str
    result_library_role: str
    result_library_status: str
    legacy_current_code_library_compatible: bool
    schema_migration_note: str
    config_tag: str
    grid: str
    particle_profile: str
    timestamp: str
    n_cases: int
    n_events_per_case: int
    sim_cfg: dict[str, Any]
    particle_types: list[str]
    wavelengths_nm: list[int]
    optical: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "dashboard_schema_version": self.dashboard_schema_version,
            "model_semantics_version": self.model_semantics_version,
            "result_library_role": self.result_library_role,
            "result_library_status": self.result_library_status,
            "legacy_current_code_library_compatible": bool(
                self.legacy_current_code_library_compatible
            ),
            "schema_migration_note": self.schema_migration_note,
            "config_tag": self.config_tag,
            "grid": self.grid,
            "particle_profile": self.particle_profile,
            "timestamp": self.timestamp,
            "n_cases": int(self.n_cases),
            "n_events_per_case": int(self.n_events_per_case),
            "sim_cfg": dict(self.sim_cfg),
            "particle_types": list(self.particle_types),
            "wavelengths_nm": list(self.wavelengths_nm),
            "optical": dict(self.optical),
        }


@dataclass(frozen=True)
class PrecomputeCheckpointManifest:
    """Serializable checkpoint manifest snapshot for one precompute job."""

    grid: str
    config_tag: str
    particle_profile: str
    total_cases: int
    checkpointed_cases: int
    checkpoint_chunk_count: int
    next_chunk_index: int
    current_stage: str
    status: str
    started_at_iso: str
    updated_at_iso: str
    progress_file: str
    error: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "job_type": "dashboard_precompute_checkpoint",
            "grid": self.grid,
            "config_tag": self.config_tag,
            "particle_profile": self.particle_profile,
            "total_cases": int(self.total_cases),
            "checkpointed_cases": int(self.checkpointed_cases),
            "checkpoint_chunk_count": int(self.checkpoint_chunk_count),
            "next_chunk_index": int(self.next_chunk_index),
            "current_stage": self.current_stage,
            "status": self.status,
            "started_at": self.started_at_iso,
            "updated_at": self.updated_at_iso,
            "progress_file": self.progress_file,
        }
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class PrecomputeProgressSnapshot:
    """Serializable live progress snapshot for one precompute job."""

    grid: str
    config_tag: str
    particle_profile: str
    n_events_per_case: int
    total_cases: int
    completed_cases: int
    successful_cases: int
    failed_cases: int
    progress_fraction: float
    elapsed_seconds: float
    cases_per_second: float | None
    estimated_total_seconds: float | None
    estimated_remaining_seconds: float | None
    eta_iso: str | None
    active_workers: int
    current_stage: str
    status: str
    started_at_iso: str
    updated_at_iso: str
    last_case: dict | None
    checkpoint_enabled: bool
    resume_enabled: bool
    checkpoint_dir: str | None
    checkpointed_cases: int
    checkpoint_chunk_count: int
    checkpoint_buffer_cases: int
    saved_outputs: dict[str, str]
    error: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "job_type": "dashboard_precompute",
            "grid": self.grid,
            "config_tag": self.config_tag,
            "particle_profile": self.particle_profile,
            "n_events_per_case": int(self.n_events_per_case),
            "total_cases": int(self.total_cases),
            "completed_cases": int(self.completed_cases),
            "successful_cases": int(self.successful_cases),
            "failed_cases": int(self.failed_cases),
            "progress_fraction": float(self.progress_fraction),
            "progress_percent": float(self.progress_fraction) * 100.0,
            "elapsed_seconds": float(self.elapsed_seconds),
            "elapsed_readable": _format_duration_readable(self.elapsed_seconds),
            "cases_per_second": self.cases_per_second,
            "estimated_total_seconds": self.estimated_total_seconds,
            "estimated_total_readable": _format_duration_readable(self.estimated_total_seconds),
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "estimated_remaining_readable": _format_duration_readable(self.estimated_remaining_seconds),
            "eta_iso": self.eta_iso,
            "active_workers": int(self.active_workers),
            "current_stage": self.current_stage,
            "status": self.status,
            "started_at": self.started_at_iso,
            "updated_at": self.updated_at_iso,
            "last_case": self.last_case,
            "checkpoint_enabled": bool(self.checkpoint_enabled),
            "resume_enabled": bool(self.resume_enabled),
            "checkpoint_dir": self.checkpoint_dir,
            "checkpointed_cases": int(self.checkpointed_cases),
            "checkpoint_chunk_count": int(self.checkpoint_chunk_count),
            "checkpoint_buffer_cases": int(self.checkpoint_buffer_cases),
            "saved_outputs": dict(self.saved_outputs),
        }
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass
class PrecomputeJobState:
    """Mutable in-memory state for one running precompute job."""

    started_at: datetime
    worker_count: int
    runtime_progress: "SweepRuntimeProgress"
    saved_outputs: dict[str, str] = field(default_factory=dict)
    checkpoint_results: list[dict] = field(default_factory=list)
    persisted_case_keys: set[str] = field(default_factory=set)
    checkpoint_buffer: list[dict] = field(default_factory=list)
    checkpoint_chunk_count: int = 0
    next_chunk_index: int = 0
    last_checkpoint_flush: float = 0.0
    checkpoint_flush_records: list[dict[str, Any]] = field(default_factory=list)
    save_stage_records: list[dict[str, Any]] = field(default_factory=list)
    sweep_elapsed_seconds: float = 0.0

    @classmethod
    def initial(cls, *, started_at: datetime, worker_count: int, total_cases: int) -> "PrecomputeJobState":
        return cls(
            started_at=started_at,
            worker_count=int(worker_count),
            runtime_progress=SweepRuntimeProgress.initial(
                total_cases=total_cases,
                active_workers=worker_count,
            ),
            last_checkpoint_flush=time.perf_counter(),
        )


@dataclass
class PrecomputeSaveContext:
    """Mutable shared state used during final artifact export."""

    summary_df: pd.DataFrame | None = None
    summary_csv_path: str | None = None
    design_postprocess_df: pd.DataFrame | None = None
    physics_fields_df: pd.DataFrame | None = None
    diagnostics_long_df: pd.DataFrame | None = None


@dataclass(frozen=True)
class PrecomputeRunContext:
    """Immutable configuration and artifact context for one precompute job."""

    grid_name: str
    config_tag: str
    particle_profile: str
    profile: dict[str, Any]
    particle_types: list
    grid: dict[str, Any]
    sim_cfg: dict[str, Any]
    total_cases: int
    worker_count: int
    artifact_paths: PrecomputeArtifactPaths
    checkpoint_enabled: bool
    resume_enabled: bool
    artifact_profile: str
    allow_partial_results: bool


@dataclass
class FreezeProbeReportPayload:
    """Serializable freeze-probe report payload."""

    n_cases: int
    status_distributions: dict[str, Any]
    width_groups: list[dict[str, Any]]
    top_cases: list[dict[str, Any]]
    sanity_checks: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "n_cases": int(self.n_cases),
            "status_distributions": dict(self.status_distributions),
            "width_groups": list(self.width_groups),
            "top_cases": list(self.top_cases),
            "sanity_checks": dict(self.sanity_checks),
        }


@dataclass
class ResultHealthReportPayload:
    """Serializable result-health report payload."""

    n_cases: int
    status_distributions: dict[str, Any]
    recommendation_distribution: dict[str, Any]
    engineering_gate_distribution: dict[str, Any]
    health_slices: dict[str, Any]
    monitoring_summary: dict[str, Any]
    monitoring_guidance: str
    top_caution_cases: list[dict[str, Any]]

    def to_payload(self) -> dict[str, Any]:
        return {
            "n_cases": int(self.n_cases),
            "status_distributions": dict(self.status_distributions),
            "recommendation_distribution": dict(self.recommendation_distribution),
            "engineering_gate_distribution": dict(self.engineering_gate_distribution),
            "health_slices": dict(self.health_slices),
            "monitoring_summary": dict(self.monitoring_summary),
            "monitoring_guidance": self.monitoring_guidance,
            "top_caution_cases": list(self.top_caution_cases),
        }


@dataclass
class SweepRuntimeProgress:
    """Structured runtime progress state for one precompute job."""

    stage: str
    status: str
    total_cases: int
    completed_cases: int
    successful_cases: int
    failed_cases: int
    progress_fraction: float
    elapsed_seconds: float
    cases_per_second: float | None
    estimated_total_seconds: float | None
    estimated_remaining_seconds: float | None
    active_workers: int
    last_case: dict | None

    @classmethod
    def initial(cls, *, total_cases: int, active_workers: int) -> "SweepRuntimeProgress":
        return cls(
            stage="initializing",
            status="running",
            total_cases=int(total_cases),
            completed_cases=0,
            successful_cases=0,
            failed_cases=0,
            progress_fraction=0.0,
            elapsed_seconds=0.0,
            cases_per_second=None,
            estimated_total_seconds=None,
            estimated_remaining_seconds=None,
            active_workers=int(active_workers),
            last_case=None,
        )

    @classmethod
    def from_payload(cls, payload: dict, *, fallback_total_cases: int, fallback_active_workers: int) -> "SweepRuntimeProgress":
        return cls(
            stage=str(payload.get("stage", "sweep")),
            status=str(payload.get("status", "running")),
            total_cases=int(payload.get("total_cases", fallback_total_cases) or fallback_total_cases),
            completed_cases=int(payload.get("completed_cases", 0) or 0),
            successful_cases=int(payload.get("successful_cases", 0) or 0),
            failed_cases=int(payload.get("failed_cases", 0) or 0),
            progress_fraction=float(payload.get("progress_fraction", 0.0) or 0.0),
            elapsed_seconds=float(payload.get("elapsed_seconds", 0.0) or 0.0),
            cases_per_second=(
                float(payload["cases_per_second"])
                if payload.get("cases_per_second") is not None
                else None
            ),
            estimated_total_seconds=(
                float(payload["estimated_total_seconds"])
                if payload.get("estimated_total_seconds") is not None
                else None
            ),
            estimated_remaining_seconds=(
                float(payload["estimated_remaining_seconds"])
                if payload.get("estimated_remaining_seconds") is not None
                else None
            ),
            active_workers=int(payload.get("active_workers", fallback_active_workers) or fallback_active_workers),
            last_case=payload.get("last_case"),
        )

    def mark_sweep_completed(self, *, total_cases: int, successful_cases: int, elapsed_seconds: float) -> None:
        self.stage = "sweep"
        self.status = "completed"
        self.total_cases = int(total_cases)
        self.completed_cases = int(total_cases)
        self.successful_cases = int(successful_cases)
        self.failed_cases = int(total_cases - successful_cases)
        self.progress_fraction = 1.0 if total_cases > 0 else 0.0
        self.elapsed_seconds = float(elapsed_seconds)
        self.estimated_total_seconds = float(elapsed_seconds)
        self.estimated_remaining_seconds = 0.0


def _remember_summary_dataframe(
    save_context: PrecomputeSaveContext,
    payload: pd.DataFrame,
    *,
    path: str | None = None,
) -> None:
    """Cache the flattened summary DataFrame for downstream save steps."""
    save_context.summary_df = payload
    save_context.summary_csv_path = path


def _build_saved_path_log_message(_payload: Any, path: str) -> str:
    """Standard log message for one saved artifact path."""
    return f"  Saved {path}"


def _build_saved_dataframe_log_message(payload: pd.DataFrame, path: str) -> str:
    """Log message for a saved DataFrame artifact."""
    return f"  Saved {path} ({len(payload)} rows)"


def _build_saved_tabular_artifact_log_message(
    payload: pd.DataFrame | PrecomputeArtifactCopy,
    path: str,
) -> str:
    """Log message for a saved tabular artifact, including copy-backed ones."""
    row_count = payload.row_count if isinstance(payload, PrecomputeArtifactCopy) else len(payload)
    return (
        f"  Saved {path} ({row_count} rows)"
        if row_count is not None
        else f"  Saved {path}"
    )


def _execute_precompute_save_step(step: PrecomputeSaveStep) -> tuple[str, str | None]:
    """Build, persist, and post-process one precompute save step."""
    payload = step.build_payload()
    step.writer(step.path, payload)
    after_write = step.after_write
    if after_write is not None:
        after_write(payload)
    log_message_builder = step.log_message
    log_message = (
        log_message_builder(payload, step.path)
        if log_message_builder is not None
        else None
    )
    return step.path, log_message


def _build_parameter_sweep_kwargs(
    *,
    run_context: PrecomputeRunContext,
    n_workers: int | None,
    progress_interval_s: float,
    progress_callback: Callable[[dict], None],
    case_result_callback: Callable[[dict], None],
    resume_results: list[dict],
    skip_case_keys: set[str],
) -> dict[str, Any]:
    """Build the parameter-sweep request for one precompute job."""
    return {
        "particle_types": run_context.particle_types,
        "medium": MEDIUM,
        "medium_resolver": medium_for_particle,
        "width_list_m": run_context.grid["width_list_m"],
        "depth_list_m": run_context.grid["depth_list_m"],
        "wavelength_list_m": run_context.grid["wavelength_list_m"],
        "optical_template": OPTICAL_TEMPLATE,
        "sim_cfg": run_context.sim_cfg,
        "theta_grid_rad": THETA_GRID_RAD,
        "baseline_particle": BASELINE_PARTICLE,
        "baseline_channel": BASELINE_CHANNEL,
        "verbose": True,
        "n_workers": n_workers,
        "progress_callback": progress_callback,
        "progress_interval_s": progress_interval_s,
        "case_result_callback": case_result_callback,
        "resume_results": resume_results,
        "skip_case_keys": skip_case_keys,
        "allow_partial": run_context.allow_partial_results,
    }


def _normalize_artifact_profile(artifact_profile: str | None) -> str:
    """Return a supported artifact profile name."""
    profile = str(artifact_profile or ARTIFACT_PROFILE_STANDARD).strip().lower()
    if profile not in ARTIFACT_PROFILES:
        raise ValueError(
            f"Unknown artifact_profile: {artifact_profile!r}. "
            f"Available: {list(ARTIFACT_PROFILES)}"
        )
    return profile


def _artifact_profile_enabled_exports(artifact_profile: str) -> set[str]:
    """Return export keys enabled by one artifact profile."""
    profile = _normalize_artifact_profile(artifact_profile)
    required_exports = {
        "summary_csv",
        "compact_pkl",
        "meta_json",
        "result_health_json",
        "runtime_performance_json",
    }
    if profile == ARTIFACT_PROFILE_MINIMAL:
        return required_exports
    if profile == ARTIFACT_PROFILE_STANDARD:
        return {
            *required_exports,
            "design_postprocess_csv",
        }
    return {
        *required_exports,
        "case_summary_csv",
        "case_summary_parquet",
        "design_postprocess_csv",
        "physics_fields_parquet",
        "diagnostics_long_parquet",
    }


def _build_precompute_save_steps(
    *,
    artifact_paths: PrecomputeArtifactPaths,
    save_context: PrecomputeSaveContext,
    results: list[dict],
    grid_name: str,
    config_tag: str,
    particle_profile: str,
    sim_cfg,
    grid: dict[str, Any],
    particle_types: list,
    save_freeze_probe_report: bool,
    artifact_profile: str = ARTIFACT_PROFILE_STANDARD,
    allow_partial_results: bool = False,
) -> list[PrecomputeSaveStep]:
    """Build the ordered save-stage pipeline for one completed precompute run."""
    enabled_exports = _artifact_profile_enabled_exports(artifact_profile)

    def get_summary_dataframe() -> pd.DataFrame:
        if save_context.summary_df is None:
            save_context.summary_df = results_to_dataframe(results)
        return save_context.summary_df

    def get_design_postprocess_dataframe() -> pd.DataFrame:
        if save_context.design_postprocess_df is None:
            save_context.design_postprocess_df = (
                results_to_design_postprocess_dataframe(results)
            )
        return save_context.design_postprocess_df

    def get_physics_fields_dataframe() -> pd.DataFrame:
        if save_context.physics_fields_df is None:
            save_context.physics_fields_df = results_to_physics_fields_dataframe(results)
        return save_context.physics_fields_df

    def get_diagnostics_long_dataframe() -> pd.DataFrame:
        if save_context.diagnostics_long_df is None:
            save_context.diagnostics_long_df = (
                results_to_diagnostics_long_dataframe(results)
            )
        return save_context.diagnostics_long_df

    def build_case_summary_csv_payload() -> pd.DataFrame | PrecomputeArtifactCopy:
        if (
            save_context.summary_df is not None
            and save_context.summary_csv_path == artifact_paths.summary_csv
            and os.path.exists(artifact_paths.summary_csv)
        ):
            return PrecomputeArtifactCopy(
                source_path=artifact_paths.summary_csv,
                row_count=len(save_context.summary_df),
            )
        return (
            save_context.summary_df
            if save_context.summary_df is not None
            else results_to_dataframe(results)
        )

    save_steps: list[PrecomputeSaveStep] = [
        PrecomputeSaveStep(
            stage_name="saving_summary",
            output_key="summary_csv",
            path=artifact_paths.summary_csv,
            build_payload=get_summary_dataframe,
            writer=_write_dataframe_atomic,
            after_write=lambda payload: _remember_summary_dataframe(
                save_context,
                payload,
                path=artifact_paths.summary_csv,
            ),
            log_message=_build_saved_dataframe_log_message,
        ),
    ]
    if "case_summary_csv" in enabled_exports:
        save_steps.append(
            PrecomputeSaveStep(
                stage_name="saving_case_summary",
                output_key="case_summary_csv",
                path=artifact_paths.case_summary_csv,
                build_payload=build_case_summary_csv_payload,
                writer=_write_dataframe_or_copy_atomic,
                log_message=_build_saved_tabular_artifact_log_message,
            )
        )
    if "design_postprocess_csv" in enabled_exports:
        save_steps.append(
            PrecomputeSaveStep(
                stage_name="saving_design_postprocess",
                output_key="design_postprocess_csv",
                path=artifact_paths.design_postprocess_csv,
                build_payload=get_design_postprocess_dataframe,
                writer=_write_dataframe_atomic,
                log_message=_build_saved_dataframe_log_message,
            )
        )
    save_steps.extend(
        [
        PrecomputeSaveStep(
            stage_name="saving_compact",
            output_key="compact_pkl",
            path=artifact_paths.compact_pkl,
            build_payload=lambda: results_to_compact(results),
            writer=_write_pickle_atomic,
            log_message=_build_saved_path_log_message,
        ),
        PrecomputeSaveStep(
            stage_name="saving_meta",
            output_key="meta_json",
            path=artifact_paths.meta_json,
            build_payload=lambda: build_metadata(
                grid_name,
                config_tag,
                particle_profile,
                sim_cfg,
                grid,
                particle_types,
                results,
                artifact_profile=artifact_profile,
                allow_partial_results=allow_partial_results,
            ),
            writer=_write_json_atomic,
            log_message=_build_saved_path_log_message,
        ),
        PrecomputeSaveStep(
            stage_name="saving_result_health",
            output_key="result_health_json",
            path=artifact_paths.result_health_json,
            build_payload=lambda: build_result_health_report(get_summary_dataframe()),
            writer=_write_json_atomic,
            log_message=_build_saved_path_log_message,
        ),
        ]
    )
    if _parquet_engine_available() and {
        "case_summary_parquet",
        "physics_fields_parquet",
        "diagnostics_long_parquet",
    }.issubset(enabled_exports):
        save_steps.extend(
            [
                PrecomputeSaveStep(
                    stage_name="saving_case_summary_parquet",
                    output_key="case_summary_parquet",
                    path=artifact_paths.case_summary_parquet,
                    build_payload=get_summary_dataframe,
                    writer=_write_dataframe_parquet_atomic,
                    log_message=_build_saved_dataframe_log_message,
                ),
                PrecomputeSaveStep(
                    stage_name="saving_physics_fields_parquet",
                    output_key="physics_fields_parquet",
                    path=artifact_paths.physics_fields_parquet,
                    build_payload=get_physics_fields_dataframe,
                    writer=_write_dataframe_parquet_atomic,
                    log_message=_build_saved_dataframe_log_message,
                ),
                PrecomputeSaveStep(
                    stage_name="saving_diagnostics_long_parquet",
                    output_key="diagnostics_long_parquet",
                    path=artifact_paths.diagnostics_long_parquet,
                    build_payload=get_diagnostics_long_dataframe,
                    writer=_write_dataframe_parquet_atomic,
                    log_message=_build_saved_dataframe_log_message,
                ),
            ]
        )
    if save_freeze_probe_report:
        save_steps.append(
            PrecomputeSaveStep(
                stage_name="saving_freeze_probe",
                output_key="freeze_probe_json",
                path=artifact_paths.freeze_probe_json,
                build_payload=lambda: build_freeze_probe_report(results),
                writer=_write_json_atomic,
                log_message=_build_saved_path_log_message,
            )
        )
    return save_steps


def build_precompute_sim_cfg(grid_name: str):
    """
    Build the SimulationConfig used by dashboard precompute jobs.

    Dashboard datasets are stored per particle / per case, so precompute must
    always use single-object scoring even if the package default config is set
    to joint mode for research demos.
    """
    if grid_name not in GRID_CONFIGS:
        raise ValueError(f"Unknown grid: {grid_name}. Available: {list(GRID_CONFIGS.keys())}")

    sim_cfg = make_ev_nodi_design_sweep_config(deepcopy(DEFAULT_SIM_CFG))
    sim_cfg.n_events = GRID_CONFIGS[grid_name]["n_events"]
    sim_cfg.score_mode = "single"
    sim_cfg.random_sequence_policy = "case_keyed_independent"
    sim_cfg.event_sampling_policy = "sobol_stratified"
    sim_cfg.adaptive_event_budget_mode = "fixed"
    sim_cfg.vectorized_event_engine = "off"
    sim_cfg.event_block_size = 32
    sim_cfg.event_block_rng_order = "event_loop_order"
    return sim_cfg


def _format_duration_readable(seconds: float | None) -> str | None:
    """Render a short human-readable duration string."""
    if seconds is None or not isinstance(seconds, (int, float)) or not math.isfinite(seconds):
        return None
    seconds = max(float(seconds), 0.0)
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{minutes:.1f} min"
    hours = minutes / 60.0
    return f"{hours:.2f} h"


def _write_json_atomic(path: str, payload: dict) -> None:
    """Atomically replace a JSON file so readers never see a partial write."""
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def _write_pickle_atomic(path: str, payload) -> None:
    """Atomically replace a pickle file."""
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "wb") as f:
        dump_dashboard_pickle(f, payload)
    os.replace(tmp_path, path)


def _write_dataframe_atomic(path: str, df: pd.DataFrame) -> None:
    """Atomically replace a CSV file generated from a DataFrame."""
    tmp_path = f"{path}.tmp"
    df.to_csv(tmp_path, index=False)
    os.replace(tmp_path, path)


def _copy_file_atomic(path: str, payload: PrecomputeArtifactCopy) -> None:
    """Atomically replace a file by copying an already-written artifact."""
    tmp_path = f"{path}.tmp"
    shutil.copyfile(payload.source_path, tmp_path)
    os.replace(tmp_path, path)


def _write_dataframe_or_copy_atomic(
    path: str,
    payload: pd.DataFrame | PrecomputeArtifactCopy,
) -> None:
    """Atomically write a DataFrame or copy an equivalent existing artifact."""
    if isinstance(payload, PrecomputeArtifactCopy):
        _copy_file_atomic(path, payload)
        return
    _write_dataframe_atomic(path, payload)


def _write_dataframe_parquet_atomic(path: str, df: pd.DataFrame) -> None:
    """Atomically replace a parquet file generated from a DataFrame."""
    tmp_path = f"{path}.tmp"
    _prepare_dataframe_for_parquet(df).to_parquet(tmp_path, index=False)
    os.replace(tmp_path, path)


def _parquet_engine_available() -> bool:
    """Return whether pandas can write parquet without adding a new dependency."""
    return bool(
        importlib.util.find_spec("pyarrow")
        or importlib.util.find_spec("fastparquet")
    )


def _stable_jsonable(value: Any) -> Any:
    """Convert dataclasses/numpy values into stable JSON-friendly structures."""
    if not isinstance(value, type) and is_dataclass(value):
        return _stable_jsonable(asdict(cast(Any, value)))
    if isinstance(value, Mapping):
        return {str(key): _stable_jsonable(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, np.ndarray):
        return _stable_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return _stable_jsonable(value.item())
    if isinstance(value, (set, frozenset)):
        items = [_stable_jsonable(item) for item in value]
        return sorted(
            items,
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"), default=str),
        )
    if isinstance(value, (list, tuple)):
        return [_stable_jsonable(item) for item in value]
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def _stable_hash(payload: Any, *, prefix: str) -> str:
    stable = json.dumps(
        _stable_jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:32]
    return f"{prefix}_{digest}"


def _export_cell_value(value: Any) -> Any:
    """Return a scalar/string value suitable for CSV/parquet export cells."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return json.dumps(_stable_jsonable(value), sort_keys=True)
    if isinstance(value, (Mapping, list, tuple, set, np.ndarray)):
        return json.dumps(_stable_jsonable(value), sort_keys=True, default=str)
    return value


def _prepare_dataframe_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """Make object-heavy diagnostics dataframes parquet-engine friendly."""
    prepared = df.copy()
    for column in prepared.columns:
        if prepared[column].dtype == "object":
            prepared[column] = prepared[column].map(_export_object_cell_for_parquet)
    return prepared


def _export_object_cell_for_parquet(value: Any) -> str | None:
    """Coerce object-dtype cells to a stable string representation for parquet."""
    if value is None:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, str):
        return value
    return json.dumps(_stable_jsonable(value), sort_keys=True, default=str)


def _source_tree_fingerprint(project_root: str) -> str:
    """Hash source files when git metadata is unavailable."""
    excluded_dirs = {
        ".git",
        ".mypy_cache",
        ".omx",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        ".venv-tests",
        "__pycache__",
        "archive",
        "reports",
        "results",
        "tmp",
    }
    included_suffixes = {".py", ".toml", ".md"}
    hasher = hashlib.sha256()
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [name for name in dirs if name not in excluded_dirs]
        for file_name in sorted(files):
            if file_name.startswith("._"):
                continue
            if os.path.splitext(file_name)[1] not in included_suffixes:
                continue
            path = os.path.join(root, file_name)
            rel_path = os.path.relpath(path, project_root)
            hasher.update(rel_path.encode("utf-8"))
            try:
                with open(path, "rb") as f:
                    hasher.update(hashlib.sha256(f.read()).hexdigest().encode("ascii"))
            except OSError:
                continue
    return f"source_{hasher.hexdigest()[:16]}"


def _code_state_payload(project_root: str) -> dict[str, str | None]:
    """Return git commit hash when available, otherwise a source fingerprint."""
    commit = _read_git_commit_hash(project_root)
    if commit:
        return {
            "git_commit_hash": commit,
            "source_tree_fingerprint": None,
            "code_state_hash_or_git_commit_hash": commit,
            "code_state_source": "git_commit_hash",
        }
    fingerprint = _source_tree_fingerprint(project_root)
    return {
        "git_commit_hash": None,
        "source_tree_fingerprint": fingerprint,
        "code_state_hash_or_git_commit_hash": fingerprint,
        "code_state_source": "source_tree_fingerprint",
    }


def _read_git_commit_hash(project_root: str) -> str | None:
    """Read git HEAD directly without spawning a shell or process."""
    git_path = os.path.join(project_root, ".git")
    if os.path.isfile(git_path):
        try:
            with open(git_path, encoding="utf-8") as f:
                marker = f.read().strip()
        except OSError:
            return None
        prefix = "gitdir:"
        if not marker.startswith(prefix):
            return None
        git_path = marker[len(prefix):].strip()
        if not os.path.isabs(git_path):
            git_path = os.path.normpath(os.path.join(project_root, git_path))
    head_path = os.path.join(git_path, "HEAD")
    try:
        with open(head_path, encoding="utf-8") as f:
            head = f.read().strip()
    except OSError:
        return None
    if _looks_like_git_hash(head):
        return head
    ref_prefix = "ref:"
    if not head.startswith(ref_prefix):
        return None
    git_root = os.path.abspath(git_path)
    ref_path = os.path.abspath(
        os.path.normpath(os.path.join(git_path, head[len(ref_prefix):].strip()))
    )
    if os.path.commonpath([git_root, ref_path]) != git_root:
        return None
    try:
        with open(ref_path, encoding="utf-8") as f:
            ref_hash = f.read().strip()
    except OSError:
        return None
    return ref_hash if _looks_like_git_hash(ref_hash) else None


def _looks_like_git_hash(value: str) -> bool:
    return len(value) in {40, 64} and all(char in "0123456789abcdef" for char in value)


def _cleanup_runtime_artifacts(
    *,
    progress_path: str,
    checkpoint_dir: str | None,
) -> None:
    """
    Remove transient runtime artifacts after a successful precompute job.

    The final dataset artifacts are the only long-term deliverables. Progress
    snapshots and crash-recovery checkpoint chunks are retained during the run
    (and on failure), but are deleted once the job has completed and all final
    outputs have been written successfully.
    """
    if progress_path and os.path.exists(progress_path):
        os.remove(progress_path)
    if checkpoint_dir and os.path.isdir(checkpoint_dir):
        shutil.rmtree(checkpoint_dir)


def _eta_iso_from_remaining(updated_at: datetime, remaining_seconds: float | None) -> str | None:
    """Convert a remaining-duration estimate into an ISO timestamp."""
    if remaining_seconds is None or not isinstance(remaining_seconds, (int, float)):
        return None
    if not math.isfinite(remaining_seconds):
        return None
    return (updated_at + timedelta(seconds=max(float(remaining_seconds), 0.0))).isoformat()


def _format_case_key_from_raw_result(raw_result: dict) -> str:
    """Return the stable identity string for a raw case result."""
    if raw_result.get("case_key"):
        return str(raw_result["case_key"])
    return build_sweep_case_key(
        str(raw_result["particle_name"]),
        float(raw_result["wavelength_m"]),
        float(raw_result["width_m"]),
        float(raw_result["depth_m"]),
    )


def _normalize_raw_case_result(raw_result: dict) -> dict:
    """Ensure a raw checkpointed case result carries a stable case key."""
    normalized = dict(raw_result)
    normalized["case_key"] = _format_case_key_from_raw_result(normalized)
    return normalized


def _manifest_checkpoint_chunk_count(manifest: dict, default: int = 0) -> int:
    """Read checkpoint chunk count from either the legacy or canonical manifest key."""
    return int(
        manifest.get(
            "checkpoint_chunk_count",
            manifest.get("chunk_count", default),
        )
        or default
    )


def _should_flush_checkpoint(
    *,
    force: bool,
    buffer_size: int,
    batch_size: int,
    last_flush_at: float,
    now: float,
    flush_interval_s: float,
) -> bool:
    """Decide whether buffered checkpoint results should be flushed now."""
    if buffer_size <= 0:
        return False
    if force:
        return True
    effective_batch_size = max(1, int(batch_size))
    effective_flush_interval_s = max(
        float(flush_interval_s),
        MIN_CHECKPOINT_FLUSH_INTERVAL_S,
    )
    return (
        buffer_size >= effective_batch_size
        or (now - last_flush_at) >= effective_flush_interval_s
    )


def _restore_job_state_from_checkpoint(
    job_state: PrecomputeJobState,
    checkpoint_dir: str,
    run_context: PrecomputeRunContext,
) -> None:
    """Populate a precompute job state from checkpoint artifacts on disk."""
    checkpoint_results, checkpoint_manifest = _load_checkpoint_results(checkpoint_dir)
    _validate_checkpoint_manifest_matches_run_context(
        checkpoint_manifest,
        run_context=run_context,
        has_checkpoint_results=bool(checkpoint_results),
    )
    job_state.checkpoint_results = checkpoint_results
    job_state.persisted_case_keys = {
        str(result["case_key"]) for result in checkpoint_results
    }
    job_state.checkpoint_chunk_count = _manifest_checkpoint_chunk_count(
        checkpoint_manifest,
        default=0,
    )
    job_state.next_chunk_index = int(
        checkpoint_manifest.get(
            "next_chunk_index",
            job_state.checkpoint_chunk_count,
        )
        or 0
        )


def _validate_checkpoint_manifest_matches_run_context(
    manifest: Mapping[str, Any],
    *,
    run_context: PrecomputeRunContext,
    has_checkpoint_results: bool = False,
) -> None:
    """Refuse to resume checkpoint chunks from a different precompute job."""
    expected = {
        "grid": run_context.grid_name,
        "config_tag": run_context.config_tag,
        "particle_profile": run_context.particle_profile,
        "total_cases": int(run_context.total_cases),
    }
    mismatches: list[str] = []
    for key, expected_value in expected.items():
        if key not in manifest:
            if has_checkpoint_results:
                mismatches.append(f"{key}=<missing> != {expected_value!r}")
            continue
        actual_value = manifest.get(key)
        if key == "total_cases":
            try:
                actual_value = int(actual_value)
            except (TypeError, ValueError):
                mismatches.append(f"{key}={manifest.get(key)!r} != {expected_value!r}")
                continue
        if actual_value != expected_value:
            mismatches.append(f"{key}={actual_value!r} != {expected_value!r}")
    if mismatches:
        raise ValueError(
            "Checkpoint manifest does not match this precompute run; refusing "
            "to resume potentially incompatible raw case chunks: "
            + "; ".join(mismatches)
        )


def _load_checkpoint_results(checkpoint_dir: str) -> tuple[list[dict], dict]:
    """Load deduplicated raw case results and checkpoint metadata, if any."""
    chunks_dir = os.path.join(checkpoint_dir, "chunks")
    manifest_path = os.path.join(checkpoint_dir, "manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    if not os.path.isdir(chunks_dir):
        manifest.setdefault("next_chunk_index", 0)
        manifest.setdefault("checkpoint_chunk_count", _manifest_checkpoint_chunk_count(manifest, default=0))
        manifest.setdefault("chunk_count", manifest["checkpoint_chunk_count"])
        manifest.setdefault("checkpointed_cases", 0)
        return [], manifest

    chunk_files = sorted(
        file_name
        for file_name in os.listdir(chunks_dir)
        if file_name.startswith("chunk_") and file_name.endswith(".pkl")
    )
    results_by_key: dict[str, dict] = {}
    max_chunk_index = -1
    for file_name in chunk_files:
        stem = os.path.splitext(file_name)[0]
        try:
            chunk_index = int(stem.split("_")[-1])
            max_chunk_index = max(max_chunk_index, chunk_index)
        except ValueError:
            pass

        chunk_path = os.path.join(chunks_dir, file_name)
        with open(chunk_path, "rb") as f:
            chunk_payload = load_dashboard_pickle(f)
        for raw_result in chunk_payload:
            normalized = _normalize_raw_case_result(raw_result)
            results_by_key[normalized["case_key"]] = normalized

    manifest.setdefault(
        "checkpoint_chunk_count",
        _manifest_checkpoint_chunk_count(manifest, default=len(chunk_files)),
    )
    manifest.setdefault("chunk_count", manifest["checkpoint_chunk_count"])
    manifest.setdefault("checkpointed_cases", len(results_by_key))
    manifest.setdefault("next_chunk_index", max_chunk_index + 1 if max_chunk_index >= 0 else 0)
    return list(results_by_key.values()), manifest


def _build_precompute_artifact_paths(output_dir: str, prefix: str) -> PrecomputeArtifactPaths:
    """Return the canonical artifact paths for one precompute job prefix."""
    checkpoint_dir = os.path.join(output_dir, f"{prefix}_checkpoint")
    return PrecomputeArtifactPaths(
        progress_json=os.path.join(output_dir, f"{prefix}_progress.json"),
        checkpoint_dir=checkpoint_dir,
        checkpoint_chunks_dir=os.path.join(checkpoint_dir, "chunks"),
        checkpoint_manifest_json=os.path.join(checkpoint_dir, "manifest.json"),
        summary_csv=os.path.join(output_dir, f"{prefix}_summary.csv"),
        case_summary_csv=os.path.join(output_dir, f"{prefix}_case_summary.csv"),
        case_summary_parquet=os.path.join(output_dir, f"{prefix}_case_summary.parquet"),
        design_postprocess_csv=os.path.join(
            output_dir,
            f"{prefix}_design_postprocess.csv",
        ),
        physics_fields_parquet=os.path.join(
            output_dir,
            f"{prefix}_physics_fields.parquet",
        ),
        diagnostics_long_parquet=os.path.join(
            output_dir,
            f"{prefix}_diagnostics_long.parquet",
        ),
        compact_pkl=os.path.join(output_dir, f"{prefix}_compact.pkl"),
        meta_json=os.path.join(output_dir, f"{prefix}_meta.json"),
        result_health_json=os.path.join(output_dir, f"{prefix}_result_health.json"),
        runtime_performance_json=os.path.join(
            output_dir,
            f"{prefix}_runtime_performance.json",
        ),
        freeze_probe_json=os.path.join(output_dir, f"{prefix}_freeze_probe.json"),
    )


def _validate_config_tag(config_tag: object, *, field_name: str = "config_tag") -> str:
    """Return a filesystem-safe config tag or raise before paths are built."""
    tag = str(config_tag).strip()
    if not tag:
        raise ValueError(f"{field_name} must not be empty")
    if not _SAFE_CONFIG_TAG_RE.fullmatch(tag) or tag in {".", ".."}:
        raise ValueError(
            f"{field_name} must be a safe filename token using only letters, "
            f"numbers, '.', '_' and '-'; got {config_tag!r}"
        )
    return tag


def _count_expected_sweep_cases(
    particle_types: list,
    grid: Mapping[str, Any],
) -> int:
    """Return the case count implied by one precompute particle/grid selection."""
    return int(
        len(particle_types)
        * len(grid["wavelength_list_m"])
        * len(grid["width_list_m"])
        * len(grid["depth_list_m"])
    )


def _build_sweep_completion_policy(
    *,
    expected_total_cases: int,
    saved_case_count: int,
    allow_partial_results: bool,
) -> dict[str, Any]:
    """Describe whether a saved sweep is complete or explicitly partial."""
    if saved_case_count == expected_total_cases:
        completion_status = "complete"
    elif allow_partial_results:
        completion_status = "partial_results_explicitly_allowed"
    else:
        completion_status = "incomplete_unexpected"

    return {
        "allow_partial_results": bool(allow_partial_results),
        "expected_total_cases": int(expected_total_cases),
        "saved_case_count": int(saved_case_count),
        "completion_status": completion_status,
    }


def _build_precompute_run_context(
    *,
    grid_name: str,
    config_tag: str | None,
    particle_profile: str,
    output_dir: str,
    n_workers: int | None,
    checkpoint_enabled: bool,
    resume_enabled: bool,
    artifact_profile: str = ARTIFACT_PROFILE_STANDARD,
    allow_partial_results: bool = False,
    random_sequence_policy: str | None = None,
    event_sampling_policy: str | None = None,
    adaptive_event_budget_mode: str | None = None,
    adaptive_min_events: int | None = None,
    adaptive_check_interval: int | None = None,
    adaptive_wilson_half_width_target: float | None = None,
    vectorized_event_engine: str | None = None,
    event_block_size: int | None = None,
    event_block_rng_order: str | None = None,
    include_diffusion: bool | None = None,
) -> PrecomputeRunContext:
    """Resolve the immutable runtime context for a precompute job."""
    if grid_name not in GRID_CONFIGS:
        raise ValueError(f"Unknown grid: {grid_name}. Available: {list(GRID_CONFIGS.keys())}")

    profile = get_precompute_profile(particle_profile)
    particle_types = get_precompute_particles(particle_profile)
    raw_config_tag = profile["default_tag"] if config_tag is None else config_tag
    resolved_config_tag = _validate_config_tag(raw_config_tag)
    grid = GRID_CONFIGS[grid_name]
    sim_cfg = build_precompute_sim_cfg(grid_name)
    sim_cfg_overrides: dict[str, Any] = {}
    if random_sequence_policy is not None:
        sim_cfg_overrides["random_sequence_policy"] = random_sequence_policy
    if event_sampling_policy is not None:
        sim_cfg_overrides["event_sampling_policy"] = event_sampling_policy
    if adaptive_event_budget_mode is not None:
        sim_cfg_overrides["adaptive_event_budget_mode"] = adaptive_event_budget_mode
    if adaptive_min_events is not None:
        sim_cfg_overrides["adaptive_min_events"] = int(adaptive_min_events)
    if adaptive_check_interval is not None:
        sim_cfg_overrides["adaptive_check_interval"] = int(adaptive_check_interval)
    if adaptive_wilson_half_width_target is not None:
        sim_cfg_overrides["adaptive_wilson_half_width_target"] = float(
            adaptive_wilson_half_width_target
        )
    if vectorized_event_engine is not None:
        sim_cfg_overrides["vectorized_event_engine"] = vectorized_event_engine
    if event_block_size is not None:
        sim_cfg_overrides["event_block_size"] = int(event_block_size)
    if event_block_rng_order is not None:
        sim_cfg_overrides["event_block_rng_order"] = event_block_rng_order
    if include_diffusion is not None:
        sim_cfg_overrides["include_diffusion"] = bool(include_diffusion)
    if sim_cfg_overrides:
        sim_cfg = replace(sim_cfg, **sim_cfg_overrides)
    total_cases = _count_expected_sweep_cases(particle_types, grid)
    worker_count = max(1, os.cpu_count() or 1) if n_workers == 0 else max(1, int(n_workers or 1))
    prefix = f"{grid_name}_{resolved_config_tag}"
    artifact_paths = _build_precompute_artifact_paths(output_dir, prefix)
    resolved_artifact_profile = _normalize_artifact_profile(artifact_profile)
    return PrecomputeRunContext(
        grid_name=grid_name,
        config_tag=resolved_config_tag,
        particle_profile=particle_profile,
        profile=profile,
        particle_types=particle_types,
        grid=grid,
        sim_cfg=sim_cfg,
        total_cases=total_cases,
        worker_count=worker_count,
        artifact_paths=artifact_paths,
        checkpoint_enabled=bool(checkpoint_enabled),
        resume_enabled=bool(resume_enabled),
        artifact_profile=resolved_artifact_profile,
        allow_partial_results=bool(allow_partial_results),
    )


def _build_result_coordinate_payload(result: dict) -> dict[str, Any]:
    """Return the shared geometric identity for one exported result row."""
    return {
        "particle_name": result["particle_name"],
        "particle_material": infer_particle_material(result["particle_name"]),
        "particle_diameter_nm": infer_particle_diameter_nm(result["particle_name"]),
        "wavelength_m": result["wavelength_m"],
        "width_m": result["width_m"],
        "depth_m": result["depth_m"],
        "wavelength_nm": round(result["wavelength_m"] * 1e9),
        "width_nm": round(result["width_m"] * 1e9),
        "depth_nm": round(result["depth_m"] * 1e9),
    }


def _build_result_score_payload(result: dict) -> dict[str, Any]:
    """Return the shared score/ranking fields for one exported result row."""
    return {
        "score": result.get("score", 0.0),
        "final_engineering_score": result.get(
            "final_engineering_score",
            result.get("engineering_score", 0.0),
        ),
        "engineering_score": result.get("engineering_score", 0.0),
        "engineering_decision_basis": result.get("engineering_decision_basis"),
        "engineering_basis_detection_rate": result.get("engineering_basis_detection_rate"),
        "engineering_basis_stable_detection_rate": result.get(
            "engineering_basis_stable_detection_rate"
        ),
        "engineering_basis_stable_detection_rate_wilson_lb": result.get(
            "engineering_basis_stable_detection_rate_wilson_lb"
        ),
        "engineering_basis_phase_flip_fraction_wilson_ub": result.get(
            "engineering_basis_phase_flip_fraction_wilson_ub"
        ),
        "engineering_basis_mean_peak_margin_z": result.get(
            "engineering_basis_mean_peak_margin_z"
        ),
        "engineering_gate_passed": result.get("engineering_gate_passed"),
        "engineering_gate_failed_count": result.get("engineering_gate_failed_count"),
        "engineering_gate_reason": result.get("engineering_gate_reason"),
        "engineering_gate_status_label": result.get("engineering_gate_status_label"),
        "engineering_gate_primary_blocker": result.get("engineering_gate_primary_blocker"),
        "engineering_gate_primary_blocker_label": result.get(
            "engineering_gate_primary_blocker_label"
        ),
        "engineering_gate_blocker_summary": result.get("engineering_gate_blocker_summary"),
        "engineering_gate_guidance": result.get("engineering_gate_guidance"),
        "engineering_gate_required_detected_events": result.get(
            "engineering_gate_required_detected_events"
        ),
        "engineering_gate_detected_fraction_lb": result.get(
            "engineering_gate_detected_fraction_lb"
        ),
        "engineering_gate_stable_detection_rate_lb": result.get(
            "engineering_gate_stable_detection_rate_lb"
        ),
        "engineering_gate_phase_flip_fraction_ub": result.get(
            "engineering_gate_phase_flip_fraction_ub"
        ),
        "engineering_gate_mean_peak_margin_z": result.get(
            "engineering_gate_mean_peak_margin_z"
        ),
        "engineering_gate_strict_paired_rate_lb": result.get(
            "engineering_gate_strict_paired_rate_lb"
        ),
        "engineering_gate_required_strict_paired_detection_rate": result.get(
            "engineering_gate_required_strict_paired_detection_rate"
        ),
        "design_recommendation_status": result.get("design_recommendation_status"),
        "design_recommendation_label": result.get("design_recommendation_label"),
        "design_recommendation_guidance": result.get("design_recommendation_guidance"),
        "final_engineering_failure_rank": result.get("final_engineering_failure_rank"),
        "final_engineering_score_rank": result.get("final_engineering_score_rank"),
        "robust_score": result.get("robust_score", 0.0),
        "joint_score": result.get("joint_score"),
        "H_norm": result.get("H_norm", 0.0),
        "R_norm": result.get("R_norm", 0.0),
        "CV_norm": result.get("CV_norm", 1.0),
        "stable_rate_norm": result.get("stable_rate_norm", 0.0),
        "threshold_margin_norm": result.get("threshold_margin_norm", 0.0),
        "local_snr_norm": result.get("local_snr_norm", 0.0),
        "auc_norm": result.get("auc_norm", 0.0),
        "hit_rate_norm": result.get("hit_rate_norm", 0.0),
        "d_prime_norm": result.get("d_prime_norm", 0.0),
    }


SELECTED_DETECTOR_MODE_DIAGNOSTIC_FIELDS = (
    "all_crossing_n_events",
    "all_crossing_n_detected",
    "all_crossing_detection_rate",
    "all_crossing_detection_rate_wilson_lb",
    "selected_detector_mode_candidate_source",
    "selected_detector_mode_candidate_margin_z_min",
    "selected_detector_mode_candidate_n_events",
    "selected_detector_mode_candidate_n_detected",
    "selected_detector_mode_candidate_fraction",
    "selected_detector_mode_candidate_detection_rate",
    "selected_detector_mode_candidate_detection_rate_wilson_lb",
    "selected_detector_mode_annulus_source",
    "selected_detector_mode_annulus_edge_norm_min",
    "selected_detector_mode_annulus_edge_norm_max",
    "selected_detector_mode_annulus_n_events",
    "selected_detector_mode_annulus_n_detected",
    "selected_detector_mode_annulus_fraction",
    "selected_detector_mode_annulus_detection_rate",
    "selected_detector_mode_annulus_detection_rate_wilson_lb",
    "selected_detector_mode_annulus_mean_edge_norm",
)


def _build_compact_summary_payload(result: dict) -> dict[str, Any]:
    """Return the compact summary payload stored in `compact.pkl`."""
    summary = result["summary"]
    return {
        **{field: summary.get(field) for field in MINIMUM_OUTPUT_SCHEMA_FIELDS},
        **{field: summary.get(field) for field in EVENT_QC_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in SELECTION_FUNCTION_DIAGNOSTIC_FIELDS},
        **{
            field: summary.get(field)
            for field in EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS
        },
        **{field: summary.get(field) for field in COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS},
        **{
            field: summary.get(field)
            for field in POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
        },
        **{field: summary.get(field) for field in OOD_DIAGNOSTIC_FIELDS},
        **{
            field: summary.get(field)
            for field in BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS
        },
        **{
            field: summary.get(field)
            for field in EXPERIMENTAL_DESIGN_ADVISOR_FIELDS
        },
        **{field: summary.get(field) for field in OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS},
        **{
            field: summary.get(field)
            for field in POLARIZATION_JONES_DIAGNOSTIC_FIELDS
        },
        **{field: summary.get(field) for field in CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in ELECTROKINETIC_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in EV_INTEGRITY_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in EV_REPORTING_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in ASSAY_CONTROL_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS},
        **{
            field: summary.get(field)
            for field in PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS
        },
        **{field: summary.get(field) for field in TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in DESIGN_METRIC_DIAGNOSTIC_FIELDS},
        **{field: summary.get(field) for field in EV_DESIGN_POSTPROCESS_FIELDS},
        **{
            field: summary.get(field)
            for field in WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS
        },
        **{field: summary.get(field) for field in SELECTED_DETECTOR_MODE_DIAGNOSTIC_FIELDS},
        "n_events": summary["n_events"],
        "random_sequence_policy": summary.get("random_sequence_policy"),
        "event_sampling_policy": summary.get("event_sampling_policy"),
        "event_position_low_variance_sampling": summary.get(
            "event_position_low_variance_sampling"
        ),
        "adaptive_event_budget_mode": summary.get("adaptive_event_budget_mode"),
        "adaptive_event_budget_requested_events": summary.get(
            "adaptive_event_budget_requested_events"
        ),
        "adaptive_event_budget_actual_events": summary.get(
            "adaptive_event_budget_actual_events"
        ),
        "adaptive_event_budget_stopped_early": summary.get(
            "adaptive_event_budget_stopped_early"
        ),
        "adaptive_event_budget_stop_reason": summary.get(
            "adaptive_event_budget_stop_reason"
        ),
        "adaptive_event_budget_max_half_width": summary.get(
            "adaptive_event_budget_max_half_width"
        ),
        "case_runtime_seconds": result.get("case_runtime_seconds"),
        "case_events_per_second": (
            float(summary.get("n_events", 0) or 0) / float(result["case_runtime_seconds"])
            if result.get("case_runtime_seconds") is not None
            and float(result["case_runtime_seconds"]) > 0
            else None
        ),
        "vectorized_event_engine": summary.get("vectorized_event_engine"),
        "event_block_size": summary.get("event_block_size"),
        "event_block_rng_order": summary.get("event_block_rng_order"),
        "vectorized_event_engine_used": summary.get("vectorized_event_engine_used"),
        "vectorized_event_engine_fallback_reason": summary.get(
            "vectorized_event_engine_fallback_reason"
        ),
        "vectorized_event_rng_order": summary.get("vectorized_event_rng_order"),
        "n_detected": summary["n_detected"],
        "detection_rate": summary["detection_rate"],
        "detection_rate_wilson_lb": summary.get("detection_rate_wilson_lb"),
        "stable_detection_rate": summary.get("stable_detection_rate"),
        "stable_detection_rate_wilson_lb": summary.get("stable_detection_rate_wilson_lb"),
        "mean_peak_height": summary["mean_peak_height"],
        "std_peak_height": summary["std_peak_height"],
        "mean_positive_peak_height": summary.get("mean_positive_peak_height"),
        "mean_negative_peak_height": summary.get("mean_negative_peak_height"),
        "positive_peak_fraction": summary.get("positive_peak_fraction"),
        "negative_peak_fraction": summary.get("negative_peak_fraction"),
        "mean_peak_width_s": summary["mean_peak_width_s"],
        "phase_flip_fraction": summary.get("phase_flip_fraction"),
        "phase_flip_fraction_wilson_ub": summary.get("phase_flip_fraction_wilson_ub"),
        "hit_rate_at_fixed_false_alarm": summary.get("hit_rate_at_fixed_false_alarm"),
        "roc_auc_event_vs_background": summary.get("roc_auc_event_vs_background"),
        "d_prime_event_vs_background": summary.get("d_prime_event_vs_background"),
        "fixed_false_alarm_rate_used": summary.get("fixed_false_alarm_rate_used"),
        "robust_cv_peak_height": summary.get("robust_cv_peak_height"),
        "mean_peak_to_threshold_ratio": summary.get("mean_peak_to_threshold_ratio"),
        "mean_peak_margin_z": summary.get("mean_peak_margin_z"),
        "mean_transit_time_s": summary.get("mean_transit_time_s"),
        "mean_local_snr": summary.get("mean_local_snr"),
        "mean_nodi_transit_bandwidth_Hz": summary.get("mean_nodi_transit_bandwidth_Hz"),
        "mean_nodi_transit_bandwidth_gain": summary.get("mean_nodi_transit_bandwidth_gain"),
        "mean_nodi_bandwidth_limited_fraction": summary.get(
            "mean_nodi_bandwidth_limited_fraction"
        ),
        "detection_decision_mode": summary.get("detection_decision_mode"),
        "single_channel_detection_rate": summary.get("single_channel_detection_rate"),
        "paired_channel_detection_rate": summary.get("paired_channel_detection_rate"),
        "paired_channel_mean_peak_margin_z": summary.get(
            "paired_channel_mean_peak_margin_z"
        ),
        "strict_paired_detection_rate_wilson_lb": summary.get(
            "strict_paired_detection_rate_wilson_lb"
        ),
        "paired_detection_rate": summary.get("paired_detection_rate"),
        "mean_I_baseline": summary.get("mean_I_baseline"),
        "mean_shot_noise_std": summary.get("mean_shot_noise_std"),
        "rho_physical_envelope_nominal": summary.get("rho_physical_envelope_nominal"),
        "rho_physical_envelope_status": summary.get("rho_physical_envelope_status"),
        "interference_overlap_default_freeze_status": summary.get(
            "interference_overlap_default_freeze_status"
        ),
        "projection_default_freeze_status": summary.get(
            "projection_default_freeze_status"
        ),
        "delta_phi_gouy_validity": summary.get("delta_phi_gouy_validity"),
        "observation_freeze_status": summary.get("observation_freeze_status"),
        "all_heights": summary["all_heights"],
        "all_signed_heights": summary.get("all_signed_heights", []),
        "all_widths": summary["all_widths"],
        "all_peak_margin_z": summary.get("all_peak_margin_z", []),
    }


_READOUT_CONVENTION_FIELDS = (
    "readout_preset",
    "readout_preset_status",
    "readout_preset_claim_level",
    "readout_preset_threshold_scope",
    "readout_shared_threshold_profile",
    "readout_lane_specific_thresholds_available",
    "readout_preset_frequency_leakage_note",
    "readout_paper_time_constant_range_s",
    *READOUT_TRANSFER_DIAGNOSTIC_FIELDS,
    "electronics_demod_phase_policy",
    "effective_electronics_demod_phase_policy",
    "readout_reference_phase_source",
    "readout_polarity",
    "polarity_source",
    "arrival_phase_distribution",
    "readout_internal_sampling_rate_Hz",
    "readout_output_sampling_rate_Hz",
    "readout_max_lockin_frequency_Hz",
    "readout_sampling_oversampling_ratio",
    "readout_carrier_nyquist_resolved",
    "readout_carrier_resolved",
    "readout_carrier_resolved_with_margin",
    "readout_analytic_demod_used",
    "readout_internal_demod_route",
    "readout_anti_alias_policy",
    "readout_anti_alias_filter_before_downsample",
    "lockin_output_grid_matches_data_logger",
    "readout_sampling_validity",
    "lockin_output_unit_convention",
    "lockin_gain_chain",
    "lockin_reported_channel",
    "lockin_reported_channel_source",
    "lockin_measured_voltage_comparable",
    "readout_model_claim_level",
    "pod_source_model_status",
    "nodi_source_model_status",
)


_PHOTOTHERMAL_POD_FIELDS = (
    "thermal_pod_model",
    "thermal_pod_input_contract_schema",
    "thermal_pod_required_inputs",
    "thermal_pod_missing_inputs",
    "thermal_pod_api_boundary_status",
    "thermal_pod_model_status",
    "pod_quantitative_amplitude_available",
    "pod_quantitative_sign_available",
    "pod_quantitative_claim_level",
    "probe_wavelength_m",
    "excitation_wavelength_m",
    "probe_power_W",
    "excitation_power_W",
    "pod_quantitative_route_status",
    "pod_amplitude_model_boundary",
    "probe_wavelength_source",
    "pod_probe_reference_field_status",
    "probe_coherent_field_group_id",
    "excitation_incoherent_power_group_id",
    "pod_probe_excitation_wavelength_status",
    "pod_wavelength_grouping_status",
    "multi_wavelength_coherent_addition_policy",
    "multi_wavelength_power_addition_policy",
    "probe_excitation_wavelengths_separated",
    "probe_wavelength_fields_add_coherently",
    "excitation_wavelength_fields_never_add_to_probe_E_ref_E_sca",
    "pod_roi_sensitivity_derivative_status",
    "pod_signal_sign_source",
    "pod_thermal_spatial_distribution_status",
    "pod_roi_derivative_validity",
    "pod_absorption_cross_section_status",
    "pod_excitation_absorption_cross_section_status",
    "pod_heat_source_status",
    "pod_heat_diffusion_status",
    "pod_solvent_dn_dT_status",
    "pod_solvent_dn_dT_source",
    "pod_substrate_heat_contribution_status",
    "pod_detector_responsivity_status",
    "pod_detector_responsivity_source",
    "pod_spectral_filter_status",
    "pod_spectral_filter_source",
    "pod_modulation_response_status",
    "pod_thermal_validation_status",
    "pod_amplitude_quantitative_blocker_summary",
)


_MIE_INCIDENT_FIELD_FIELDS = (
    "incident_field_model_for_mie",
    "local_plane_wave_validity",
    "mie_particle_radius_m",
    "mie_size_parameter",
    "mie_incident_beam_waist_min_m",
    "mie_radius_to_beam_waist_ratio",
    "mie_field_gradient_across_particle_status",
    "mie_incident_field_GLMT_required",
    "mie_incident_field_fullwave_required",
    "mie_incident_field_claim_level",
    "mie_illumination_geometry_source",
    "mie_illumination_NA",
    "mie_incident_field_blocker_summary",
)


_THRESHOLD_FALSE_ALARM_FIELDS = (
    "threshold_sigma",
    "threshold_sigma_nodi",
    "threshold_sigma_pod",
    "threshold_lane_specific_model",
    "threshold_tail",
    "threshold_tail_configured",
    "threshold_tail_status",
    "threshold_false_alarm_tail_count",
    "threshold_sign",
    "threshold_polarity_mode",
    "target_false_alarm_rate",
    "threshold_from_blank_trace",
    "threshold_from_event_background_segment",
    "threshold_background_source",
    "threshold_background_segment_fraction",
    "threshold_background_segment_samples",
    "threshold_calibration_source",
    "threshold_calibration_status",
    "blank_false_positive_calibration_status",
    "blank_false_positive_calibration_source",
    "blank_false_positive_calibration_id",
    "absolute_threshold_sigma_equivalent",
    "positive_threshold_sigma_equivalent",
    "gaussian_iid_single_sample_false_alarm_probability",
    "gaussian_iid_background_segment_false_alarm_probability",
    "mean_threshold_robust_std",
    "mean_pod_threshold_robust_std",
    "blank_trace_autocorrelation_time_s",
    "effective_independent_samples_per_trace",
    "lockin_filter_order",
    "empirical_peak_false_alarm_rate_per_minute",
    "empirical_pair_false_alarm_rate_per_minute",
    "lane_noise_correlation_coefficient",
    "colored_noise_false_alarm_model",
    "colored_noise_false_alarm_status",
    "colored_noise_surrogate_components",
    "colored_noise_threshold_bias",
    "colored_noise_threshold_bias_status",
    "paired_false_alarm_status",
    "blank_false_positive_calibration_row_id",
    "blank_false_positive_calibration_row_index",
    "blank_false_positive_calibration_row_count",
    "blank_false_positive_calibration_data_role",
    "blank_false_positive_synthetic_fixture_active",
    "blank_false_positive_table_validation_status",
    "blank_false_positive_manifest_status",
    "blank_false_positive_manifest_validation_status",
    "blank_false_positive_manifest_path",
    "raw_blank_trace_bootstrap_schema",
    "raw_blank_trace_path_configured",
    "raw_blank_trace_bootstrap_supported",
    "raw_blank_trace_bootstrap_status",
    "raw_blank_trace_required_columns",
    "raw_blank_trace_bootstrap_outputs",
)


_PARTICLE_MODEL_FIELDS = (
    "particle_family",
    "particle_family_status",
    "particle_optical_model",
    "structured_particle_model_status",
    "structured_particle_key",
    "structured_particle_preset_name",
    "EV_label",
    "EV_claim_level",
    "exosome_biogenesis_claim",
    "biogenesis_claim",
    "material_dataset",
    "particle_material_model_mode",
    "particle_material_dataset_key",
    "particle_material_dataset_source",
    "particle_material_dataset_type",
    "particle_material_wavelength_status",
    "particle_material_temperature_correction_status",
    "particle_material_uncertainty_status",
    "metal_size_damping",
    "metal_size_damping_status",
    "ligand_shell",
    "ligand_shell_status",
    "medium_dispersion",
    "medium_dispersion_status",
    "wall_dispersion",
    "wall_dispersion_status",
    "shape_model",
    "anisotropic_shell_model",
    "orientation_average_status",
    "shape_uncertainty_status",
    "EV_sample_preparation_status",
    "EV_isolation_method",
    "EV_aggregation_or_coisolate_status",
    "EV_ensemble_mode",
    "EV_ensemble_name",
    "EV_ensemble_member_index",
    "EV_ensemble_member_count",
    "EV_ensemble_member_preset",
    "EV_ensemble_status",
    "ev_population_prior_status",
    "ev_low_RI_tail_detection_risk",
    "EV_core_RI_nominal",
    "EV_shell_RI_nominal",
    "EV_shell_thickness_m",
    "EV_uncertainty_inputs",
    "size_distribution_uncertainty",
    "core_RI_uncertainty",
    "shell_RI_uncertainty",
    "shell_thickness_uncertainty",
    "anisotropy_uncertainty",
    "shape_uncertainty",
    "corona_coisolate_uncertainty",
    "isolation_batch_uncertainty",
    "particle_uncertainty_budget_model",
    "particle_uncertainty_budget_status",
    "uncertainty_propagation_mode",
    "uncertainty_inputs",
    "uncertainty_outputs",
    "uncertainty_output_confidence_status",
    "uncertainty_propagation_schema",
    "uncertainty_propagation_route_configured",
    "uncertainty_propagation_status",
    "uncertainty_required_input_schema",
    "uncertainty_propagated_outputs",
    "uncertainty_route_active",
    "uncertainty_propagation_blocker_summary",
    "peak_height_CI_available",
    "detection_rate_CI_available",
    "count_rate_CI_available",
    "classification_probability_CI_available",
)


_COUNT_MODEL_FIELDS = (
    "conditional_detection_rate",
    "conditional_detection_rate_definition",
    "conditional_detection_rate_source",
    "count_generation_model",
    "per_event_detectability_boundary",
    "count_prediction_model",
    "count_prediction_status",
    "count_prediction_claim_level",
    "number_concentration_m3",
    "count_observation_window_s",
    "accessible_area_m2",
    "accessible_area_status",
    "volumetric_flow_rate_m3_s",
    "volumetric_flow_rate_source",
    "poisson_arrival_process_status",
    "flux_conditioned_initial_distribution_status",
    "crossing_conditioned_transport_status",
    "event_rate_Hz",
    "expected_events_in_window",
    "detected_event_rate_before_deadtime_Hz",
    "predicted_count_rate_Hz",
    "predicted_counts_in_window",
    "missed_event_rate_Hz",
    "count_dead_time_s",
    "dead_time_model",
    "dead_time_limited_count_rate_Hz",
    "dead_time_loss_fraction",
    "blank_false_positive_rate_Hz",
    "blank_false_positive_correction_status",
    "missed_event_correction_status",
    "multi_occupancy_window_s",
    "focus_occupancy_mean",
    "multi_occupancy_probability",
    "occupancy_correction_status",
    "dead_time_correction_status",
    "single_particle_condition_status",
    "wall_interaction_model",
    "wall_interaction_status",
    "zeta_potential_particle_mV",
    "zeta_potential_wall_mV",
    "ionic_strength_M",
    "adsorption_probability_per_length_m",
    "adsorption_or_clogging_exclusion_status",
    "count_rate_source",
    "count_rate_confidence_status",
    "count_prediction_uncertainty_status",
)


_INTERFACE_CORRECTION_FIELDS = (
    "interface_correction_mode",
    "interface_correction_input_contract_schema",
    "interface_required_inputs",
    "interface_missing_inputs",
    "interface_api_boundary_status",
    "interface_correction_status",
    "interface_correction_priority",
    "interface_correction_applied_to",
    "interface_correction_particle_family",
    "interface_correction_active",
    "interface_incident_field_correction",
    "interface_particle_polarizability_correction",
    "interface_radiation_pattern_collection_correction",
    "interface_correction_claim_level",
    "interface_output_sensitivity_status",
    "interface_phase_or_polarity_sensitive_output",
    "interface_angular_pattern_sensitive_output",
    "interface_dipole_surrogate_validity",
    "interface_quantitative_claim_blocker_summary",
    "homogeneous_medium_mie_assumption",
    "nearest_wall_gap_nominal_m",
    "lambda_medium_m",
    "eta_interface",
    "eta_lambda",
    "interface_fullwave_required",
    "interface_fullwave_reason",
    "interface_escalation_route",
)


_CALIBRATION_STATE_EXTRA_FIELDS = (
    "calibration_state_machine_schema",
    "calibration_state_resolver_status",
    "calibration_lane_summary",
    "calibration_state_blocker_summary",
    "calibration_synthetic_fixture_active",
    "output_claim_level_resolved",
    "standard_particle_calibration_row_id",
    "standard_particle_calibration_row_index",
    "standard_particle_calibration_row_count",
    "standard_particle_calibration_data_role",
    "standard_particle_synthetic_fixture_active",
    "standard_particle_table_validation_status",
    "standard_particle_manifest_status",
    "standard_particle_manifest_validation_status",
    "standard_particle_manifest_path",
    "detector_unit_chain_schema",
    "detector_unit_chain_unlocked",
    "detector_unit_chain_status",
    "incident_power_density_status",
    "mie_differential_cross_section_status",
    "detector_etendue_status",
    "absolute_optical_throughput_status",
    "photodiode_responsivity_status",
    "transimpedance_gain_status",
    "adc_conversion_status",
    "lockin_voltage_unit_status",
    "detector_unit_chain_blocker_summary",
)


_COLLECTION_OPERATOR_EXTRA_FIELDS = (
    "collection_operator_calibration_row_id",
    "collection_operator_calibration_row_index",
    "collection_operator_calibration_row_count",
    "collection_operator_geometry_distance_report",
    "collection_operator_calibration_data_role",
    "collection_operator_synthetic_fixture_active",
    "collection_operator_table_validation_status",
    "collection_operator_manifest_status",
    "collection_operator_manifest_validation_status",
    "collection_operator_manifest_path",
    "bfp_roi_mask_schema",
    "bfp_roi_mask_path_configured",
    "bfp_roi_mask_calibrated",
    "bfp_roi_mask_source",
    "bfp_roi_mask_status",
    "bfp_roi_mask_claim_level",
    "bfp_roi_mask_data_role",
    "bfp_roi_mask_synthetic_fixture_active",
    "bfp_roi_mask_table_validation_status",
    "bfp_roi_mask_manifest_status",
    "bfp_roi_mask_manifest_validation_status",
    "bfp_roi_mask_manifest_path",
    "bfp_roi_mask_row_count",
    "bfp_roi_mask_required_field_groups_missing",
    "bfp_roi_mask_gate_passed",
    "bfp_pixel_to_angle_status",
    "slit_position_mapping_status",
    "pinhole_projection_status",
    "bfp_roi_required_inputs",
)


_REFERENCE_CALIBRATION_EXTRA_FIELDS = (
    "reference_calibration_row_id",
    "reference_calibration_row_index",
    "reference_calibration_row_count",
    "reference_calibration_data_role",
    "reference_calibration_synthetic_fixture_active",
    "reference_calibration_table_validation_status",
    "reference_calibration_manifest_status",
    "reference_calibration_manifest_validation_status",
    "reference_calibration_manifest_path",
)


_REPORT_GOVERNED_STATUS_FIELDS = (
    "detector_forward_model",
    "detector_forward_status",
    "detector_forward_claim_level",
    "field_coordinate_measure",
    "bfp_to_angle_jacobian_applied",
    "coordinate_frame_mapping",
    "operator_route",
    "operator_normalization",
    "collection_operator_calibration_status",
    "collection_operator_coverage_status",
    "collection_operator_calibration_data_role",
    "bfp_roi_mask_status",
    "output_claim_level",
    "output_claim_level_resolved",
    "scattering_normalization_route",
    "mie_to_power_chain_status",
    "detector_unit_chain_status",
    "detector_field_units",
    "standard_particle_calibration_coverage_status",
    "standard_particle_calibration_data_role",
    "bayesian_calibration_status",
    "bayesian_posterior_available",
    "experimental_design_advisor_status",
    "next_experiment_priority_bucket",
    "objective_panel_status",
    "objective_panel_recommendation",
    "population_inference_status",
    "population_inference_gate_passed",
    "control_interpretation_status",
    "control_interpretation_claim_level",
    "control_failure_interpretation_gate_passed",
    "fluidic_network_model_status",
    "fluidic_network_claim_level",
    "fluidic_network_external_geometry_status",
    "fluidic_network_pressure_flow_relation_status",
    "fluidic_network_fixed_pressure_prediction_allowed",
    "fluidic_network_gate_passed",
    "global_phase_offset_calibration_status",
    "calibration_design_rank",
    "calibration_held_out_validation_status",
    "vector_validity_status",
    "polarization_jones_operator_status",
    "phase_polarization_quantitative_claim_allowed",
    "high_NA_collection_warning",
    "superposition_validity_status",
    "joint_fullwave_required_for_quantitative_phase",
    "background_field_status",
    "residual_transmitted_leakage_status",
    "readout_preset_status",
    "readout_sampling_validity",
    "lockin_output_unit_convention",
    "threshold_tail",
    "threshold_calibration_status",
    "blank_false_positive_calibration_data_role",
    "raw_blank_trace_bootstrap_status",
    "colored_noise_false_alarm_status",
    "particle_material_uncertainty_status",
    "particle_uncertainty_budget_status",
    "peak_height_CI_available",
    "interface_correction_status",
    "interface_api_boundary_status",
    "interface_output_sensitivity_status",
    "interface_fullwave_required",
    "thermal_pod_model_status",
    "thermal_pod_api_boundary_status",
    "pod_quantitative_route_status",
    "pod_probe_reference_field_status",
    "pod_heat_source_status",
    "count_generation_model",
    "per_event_detectability_boundary",
    "count_prediction_model",
    "count_prediction_status",
    "count_likelihood_status",
    "count_likelihood_gate_passed",
    "ood_detection_status",
    "unknown_particle_flag",
    "poisson_arrival_process_status",
    "crossing_conditioned_transport_status",
    "count_rate_confidence_status",
)


_RESULT_HEALTH_STATUS_FIELDS = (
    "observation_freeze_status",
    "delta_phi_gouy_validity",
    "interference_overlap_default_freeze_status",
    "projection_default_freeze_status",
    "rho_physical_envelope_status",
    "reference_width_saturation_status",
    *_REPORT_GOVERNED_STATUS_FIELDS,
)


_FREEZE_PROBE_STATUS_FIELDS = (
    "path_opd_freeze_status",
    "interference_overlap_default_freeze_status",
    "projection_default_freeze_status",
    "delta_phi_gouy_validity",
    "observation_freeze_status",
    "rho_physical_envelope_status",
    *_REPORT_GOVERNED_STATUS_FIELDS,
)


def _build_compact_physics_payload(result: dict) -> dict[str, Any]:
    """Return the compact physics payload stored in `compact.pkl`."""
    intrinsic = result.get("intrinsic", {})
    reference = result.get("reference", {})
    summary = result["summary"]
    return {
        "Csca_m2": intrinsic.get("Csca_m2"),
        "theta_det_rad": intrinsic.get("theta_det_rad"),
        "theta_center_rad": intrinsic.get("theta_center_rad"),
        "sigma_effective_rad": intrinsic.get("sigma_effective_rad"),
        "E_sca_at_det": intrinsic.get("E_sca_at_det"),
        "E_sca_ref": intrinsic.get("E_sca_ref"),
        "E_sca_normalized": intrinsic.get("E_sca_unit_normalized"),
        "phi_projection_rad": intrinsic.get("phi_projection_rad"),
        "phi_sca_material_rad": intrinsic.get("phi_sca_material_rad"),
        "detection_operator_signature": intrinsic.get("operator_signature"),
        "operator_route": intrinsic.get("operator_route"),
        "operator_normalization": intrinsic.get("operator_normalization"),
        "collection_operator_calibration_status": intrinsic.get(
            "collection_operator_calibration_status"
        ),
        "collection_operator_coverage_status": intrinsic.get(
            "collection_operator_coverage_status"
        ),
        "collection_operator_id": intrinsic.get("collection_operator_id"),
        "collection_operator_calibrated_geometry": intrinsic.get(
            "collection_operator_calibrated_geometry"
        ),
        **{field: intrinsic.get(field) for field in _COLLECTION_OPERATOR_EXTRA_FIELDS},
        "absolute_throughput_calibrated": intrinsic.get(
            "absolute_throughput_calibrated"
        ),
        "observation_signature": intrinsic.get("observation_signature"),
        "detector_forward_model": intrinsic.get("detector_forward_model"),
        "detector_forward_status": intrinsic.get("detector_forward_status"),
        "detector_forward_claim_level": intrinsic.get("detector_forward_claim_level"),
        "field_coordinate_measure": intrinsic.get("field_coordinate_measure"),
        "field_measure_status": intrinsic.get("field_measure_status"),
        "bfp_to_angle_jacobian_applied": intrinsic.get("bfp_to_angle_jacobian_applied"),
        "detector_mask_units": intrinsic.get("detector_mask_units"),
        "coordinate_frame_mapping": intrinsic.get("coordinate_frame_mapping"),
        "joint_overlap_used": intrinsic.get("joint_overlap_used"),
        "scattering_projection_basis": intrinsic.get("scattering_projection_basis"),
        "complex_time_harmonic_convention": intrinsic.get(
            "complex_time_harmonic_convention"
        ),
        "fourier_transform_sign_convention": intrinsic.get(
            "fourier_transform_sign_convention"
        ),
        "mie_amplitude_phase_convention": intrinsic.get(
            "mie_amplitude_phase_convention"
        ),
        "interference_conjugation_convention": intrinsic.get(
            "interference_conjugation_convention"
        ),
        "interference_cross_term_convention": intrinsic.get(
            "interference_cross_term_convention"
        ),
        "global_phase_offset_source": intrinsic.get("global_phase_offset_source"),
        "absolute_polarity_claim": intrinsic.get("absolute_polarity_claim"),
        "complex_convention_status": intrinsic.get("complex_convention_status"),
        "complex_field_claim_level": intrinsic.get("complex_field_claim_level"),
        "polarization_basis_model": intrinsic.get("polarization_basis_model"),
        "jones_basis_status": intrinsic.get("jones_basis_status"),
        "vector_optics_mode": intrinsic.get("vector_optics_mode"),
        **{
            field: intrinsic.get(field)
            for field in POLARIZATION_JONES_DIAGNOSTIC_FIELDS
        },
        "mie_s1_s2_lab_basis_mapping": intrinsic.get("mie_s1_s2_lab_basis_mapping"),
        "active_mie_basis_component": intrinsic.get("active_mie_basis_component"),
        "S1S2_to_lab_basis_rotation_applied": intrinsic.get(
            "S1S2_to_lab_basis_rotation_applied"
        ),
        "reference_jones_field_defined": intrinsic.get("reference_jones_field_defined"),
        "detector_analyzer_jones_matrix_defined": intrinsic.get(
            "detector_analyzer_jones_matrix_defined"
        ),
        "mie_jones_bridge_status": intrinsic.get("mie_jones_bridge_status"),
        "high_NA_collection_warning": intrinsic.get("high_NA_collection_warning"),
        "vector_validity_status": intrinsic.get("vector_validity_status"),
        "calibration_state_machine_version": intrinsic.get(
            "calibration_state_machine_version"
        ),
        "calibration_state_machine_status": intrinsic.get(
            "calibration_state_machine_status"
        ),
        "output_claim_level": intrinsic.get("output_claim_level"),
        "calibrated_quantitative_unlocked": intrinsic.get(
            "calibrated_quantitative_unlocked"
        ),
        "output_claim_blocker_summary": intrinsic.get(
            "output_claim_blocker_summary"
        ),
        "scattering_normalization_route": intrinsic.get(
            "scattering_normalization_route"
        ),
        "scattering_normalization_status": intrinsic.get(
            "scattering_normalization_status"
        ),
        "scattering_calibration_level": intrinsic.get("scattering_calibration_level"),
        "baseline_normalization_role": intrinsic.get("baseline_normalization_role"),
        "baseline_particle_absolute_scale_restored": intrinsic.get(
            "baseline_particle_absolute_scale_restored"
        ),
        "baseline_normalized_E_sca_allowed_in_photon_unit_route": intrinsic.get(
            "baseline_normalized_E_sca_allowed_in_photon_unit_route"
        ),
        "K_sca_calibration_status": intrinsic.get("K_sca_calibration_status"),
        "K_sca_value": intrinsic.get("K_sca_value"),
        "K_sca_role": intrinsic.get("K_sca_role"),
        "mie_to_power_chain_status": intrinsic.get("mie_to_power_chain_status"),
        "scattered_power_conversion_status": intrinsic.get(
            "scattered_power_conversion_status"
        ),
        "detector_field_units": intrinsic.get("detector_field_units"),
        "power_chain_absolute_units_available": intrinsic.get(
            "power_chain_absolute_units_available"
        ),
        "K_sca_power_chain_role": intrinsic.get("K_sca_power_chain_role"),
        "mie_to_power_chain_blocker_summary": intrinsic.get(
            "mie_to_power_chain_blocker_summary"
        ),
        "standard_particle_calibration_path_configured": intrinsic.get(
            "standard_particle_calibration_path_configured"
        ),
        "standard_particle_calibration_coverage_status": intrinsic.get(
            "standard_particle_calibration_coverage_status"
        ),
        "global_phase_offset_calibration_status": intrinsic.get(
            "global_phase_offset_calibration_status"
        ),
        "K_sca_uncertainty_status": intrinsic.get("K_sca_uncertainty_status"),
        "K_sca_uncertainty_propagated_to_outputs": intrinsic.get(
            "K_sca_uncertainty_propagated_to_outputs"
        ),
        "standard_particle_uncertainty_budget_status": intrinsic.get(
            "standard_particle_uncertainty_budget_status"
        ),
        "standard_particle_size_distribution_status": intrinsic.get(
            "standard_particle_size_distribution_status"
        ),
        "standard_particle_shape_uncertainty_status": intrinsic.get(
            "standard_particle_shape_uncertainty_status"
        ),
        "standard_particle_ligand_shell_status": intrinsic.get(
            "standard_particle_ligand_shell_status"
        ),
        "standard_particle_batch_status": intrinsic.get(
            "standard_particle_batch_status"
        ),
        "standard_particle_concentration_uncertainty_status": intrinsic.get(
            "standard_particle_concentration_uncertainty_status"
        ),
        "standard_particle_material_dataset_uncertainty_status": intrinsic.get(
            "standard_particle_material_dataset_uncertainty_status"
        ),
        "calibration_design_rank": intrinsic.get("calibration_design_rank"),
        "calibration_standard_count": intrinsic.get("calibration_standard_count"),
        "calibration_wavelength_count": intrinsic.get("calibration_wavelength_count"),
        "calibration_geometry_count": intrinsic.get("calibration_geometry_count"),
        "calibration_held_out_validation_status": intrinsic.get(
            "calibration_held_out_validation_status"
        ),
        "calibration_held_out_error": intrinsic.get("calibration_held_out_error"),
        "calibration_identifiability_blocker_summary": intrinsic.get(
            "calibration_identifiability_blocker_summary"
        ),
        "calibration_fit_parameter_coupling_status": intrinsic.get(
            "calibration_fit_parameter_coupling_status"
        ),
        "calibration_design_minimum_requirement_status": intrinsic.get(
            "calibration_design_minimum_requirement_status"
        ),
        "fit_parameters_identifiable": intrinsic.get("fit_parameters_identifiable"),
        "detector_calibration_level": intrinsic.get("detector_calibration_level"),
        "readout_calibration_level": intrinsic.get("readout_calibration_level"),
        "count_calibration_level": intrinsic.get("count_calibration_level"),
        **{field: intrinsic.get(field) for field in _CALIBRATION_STATE_EXTRA_FIELDS},
        "noise_model_route": intrinsic.get("noise_model_route"),
        "detector_noise_claim_level": intrinsic.get("detector_noise_claim_level"),
        "absolute_throughput_route": intrinsic.get("absolute_throughput_route"),
        "photon_unit_noise_model_status": intrinsic.get(
            "photon_unit_noise_model_status"
        ),
        "lockin_ENBW_Hz": intrinsic.get("lockin_ENBW_Hz"),
        "lockin_ENBW_status": intrinsic.get("lockin_ENBW_status"),
        "lockin_ENBW_claim_level": intrinsic.get("lockin_ENBW_claim_level"),
        "shot_noise_model_status": intrinsic.get("shot_noise_model_status"),
        "photon_shot_noise_term_status": intrinsic.get(
            "photon_shot_noise_term_status"
        ),
        "electronics_noise_model_status": intrinsic.get(
            "electronics_noise_model_status"
        ),
        "electronics_noise_term_status": intrinsic.get("electronics_noise_term_status"),
        "rin_noise_model_status": intrinsic.get("rin_noise_model_status"),
        "rin_noise_term_status": intrinsic.get("rin_noise_term_status"),
        "speckle_background_noise_model_status": intrinsic.get(
            "speckle_background_noise_model_status"
        ),
        "speckle_like_noise_term_status": intrinsic.get(
            "speckle_like_noise_term_status"
        ),
        "drift_noise_term_status": intrinsic.get("drift_noise_term_status"),
        "lockin_output_noise_term_status": intrinsic.get(
            "lockin_output_noise_term_status"
        ),
        "noise_terms_schema_version": intrinsic.get("noise_terms_schema_version"),
        "noise_term_quantitative_contribution_status": intrinsic.get(
            "noise_term_quantitative_contribution_status"
        ),
        "detector_dynamic_range_model": intrinsic.get(
            "detector_dynamic_range_model"
        ),
        "detector_saturation_status": intrinsic.get("detector_saturation_status"),
        "dynamic_range_margin": intrinsic.get("dynamic_range_margin"),
        "ADC_dynamic_range_status": intrinsic.get("ADC_dynamic_range_status"),
        "reference_enhancement_gain": intrinsic.get("reference_enhancement_gain"),
        "reference_enhancement_snr_claim": intrinsic.get(
            "reference_enhancement_snr_claim"
        ),
        "background_field_model": intrinsic.get("background_field_model"),
        "background_field_status": intrinsic.get("background_field_status"),
        "background_claim_level": intrinsic.get("background_claim_level"),
        "residual_transmitted_leakage_status": intrinsic.get(
            "residual_transmitted_leakage_status"
        ),
        "stray_light_status": intrinsic.get("stray_light_status"),
        "blank_trace_empirical_available": intrinsic.get(
            "blank_trace_empirical_available"
        ),
        "particle_induced_channel_phase_perturbation_status": intrinsic.get(
            "particle_induced_channel_phase_perturbation_status"
        ),
        "independent_superposition_status": intrinsic.get(
            "independent_superposition_status"
        ),
        "superposition_validity_status": intrinsic.get(
            "superposition_validity_status"
        ),
        "E_sca_to_E_ref_amplitude_ratio_estimate": intrinsic.get(
            "E_sca_to_E_ref_amplitude_ratio_estimate"
        ),
        "extinction_to_beam_area_estimate": intrinsic.get(
            "extinction_to_beam_area_estimate"
        ),
        "reference_depletion_fraction_estimate": intrinsic.get(
            "reference_depletion_fraction_estimate"
        ),
        "reference_depletion_estimate_status": intrinsic.get(
            "reference_depletion_estimate_status"
        ),
        "channel_particle_coupling_model": intrinsic.get(
            "channel_particle_coupling_model"
        ),
        "joint_fullwave_required_for_quantitative_phase": intrinsic.get(
            "joint_fullwave_required_for_quantitative_phase"
        ),
        "superposition_validity_claim_level": intrinsic.get(
            "superposition_validity_claim_level"
        ),
        "superposition_validity_blocker_summary": intrinsic.get(
            "superposition_validity_blocker_summary"
        ),
        "nodi_signal_component_model": intrinsic.get("nodi_signal_component_model"),
        "nodi_signal_component_status": intrinsic.get("nodi_signal_component_status"),
        "nodi_forward_extinction_leakage_status": intrinsic.get(
            "nodi_forward_extinction_leakage_status"
        ),
        "nodi_transmitted_leakage_component_status": intrinsic.get(
            "nodi_transmitted_leakage_component_status"
        ),
        "nodi_particle_induced_channel_coupling_status": intrinsic.get(
            "nodi_particle_induced_channel_coupling_status"
        ),
        "nodi_signal_component_claim_level": intrinsic.get(
            "nodi_signal_component_claim_level"
        ),
        "nodi_component_escalation_route": intrinsic.get(
            "nodi_component_escalation_route"
        ),
        "path_opd_freeze_status": intrinsic.get("path_opd_freeze_status"),
        "A_ref": reference.get("A_ref"),
        "g_ref": reference.get("g_ref"),
        "reference_route": reference.get("reference_route"),
        "reference_claim_level": reference.get("reference_claim_level"),
        "reference_solver_route": reference.get("reference_solver_route"),
        "reference_solver_status": reference.get("reference_solver_status"),
        "reference_solver_detector_bridge_status": reference.get(
            "reference_solver_detector_bridge_status"
        ),
        "phase_filter_validity": reference.get("phase_filter_validity"),
        "phase_filter_H_over_lambda0": reference.get("phase_filter_H_over_lambda0"),
        "phase_filter_delta_ref_rad": reference.get("phase_filter_delta_ref_rad"),
        "phase_filter_theta_signed_rad": reference.get(
            "phase_filter_theta_signed_rad"
        ),
        "phase_filter_H_over_zR": reference.get("phase_filter_H_over_zR"),
        "phase_filter_multiple_reflection_warning": reference.get(
            "phase_filter_multiple_reflection_warning"
        ),
        "subwavelength_groove_validity_status": reference.get(
            "subwavelength_groove_validity_status"
        ),
        "finite_length_assumption_status": reference.get(
            "finite_length_assumption_status"
        ),
        "sidewall_scattering_roughness_status": reference.get(
            "sidewall_scattering_roughness_status"
        ),
        "evanescent_component_unmodeled": reference.get(
            "evanescent_component_unmodeled"
        ),
        "groove_waveguide_mode_unmodeled": reference.get(
            "groove_waveguide_mode_unmodeled"
        ),
        "roughness_scatter_unmodeled": reference.get("roughness_scatter_unmodeled"),
        "depth_validity_reason": reference.get("depth_validity_reason"),
        "requires_calibration_or_fullwave": reference.get(
            "requires_calibration_or_fullwave"
        ),
        "reference_calibration_amplitude_status": reference.get(
            "reference_calibration_amplitude_status"
        ),
        "reference_calibration_coverage_status": reference.get(
            "reference_calibration_coverage_status"
        ),
        **{field: reference.get(field) for field in _REFERENCE_CALIBRATION_EXTRA_FIELDS},
        "reference_phase_calibration_status": reference.get(
            "reference_phase_calibration_status"
        ),
        "reference_projection_basis": reference.get("reference_projection_basis"),
        "reference_effective_basis": reference.get("reference_effective_basis"),
        "reference_projection_basis_match": reference.get(
            "reference_projection_basis_match"
        ),
        "reference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "rho_physical_envelope_nominal": reference.get("rho_physical_envelope_nominal"),
        "rho_physical_envelope_status": reference.get("rho_physical_envelope_status"),
        "reference_width_saturation_status": reference.get(
            "reference_width_saturation_status"
        ),
        "reference_width_saturation_factor": reference.get(
            "reference_width_saturation_factor"
        ),
        "na_cutoff_active": reference.get("na_cutoff_active"),
        "na_cutoff_condition_met": reference.get("na_cutoff_condition_met"),
        "na_cutoff_hard_zero_applied": reference.get("na_cutoff_hard_zero_applied"),
        "na_cutoff_policy": reference.get("na_cutoff_policy"),
        "na_cutoff_diff_ratio": reference.get("na_cutoff_diff_ratio"),
        "na_cutoff_na_ratio": reference.get("na_cutoff_na_ratio"),
        "na_cutoff_NA_collection": reference.get("na_cutoff_NA_collection"),
        "na_cutoff_W_min_m": reference.get("na_cutoff_W_min_m"),
        "interference_overlap_default_freeze_status": summary.get(
            "interference_overlap_default_freeze_status"
        ),
        "projection_default_freeze_status": summary.get(
            "projection_default_freeze_status"
        ),
        "delta_phi_gouy_validity": summary.get("delta_phi_gouy_validity"),
        "observation_freeze_status": summary.get("observation_freeze_status"),
        **{field: intrinsic.get(field) for field in _PARTICLE_MODEL_FIELDS},
        **{
            field: intrinsic.get(field)
            for field in EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS
        },
        **{field: intrinsic.get(field) for field in _INTERFACE_CORRECTION_FIELDS},
        **{field: intrinsic.get(field) for field in _COUNT_MODEL_FIELDS},
        **{field: intrinsic.get(field) for field in COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS},
        **{
            field: intrinsic.get(field)
            for field in POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
        },
        **{field: intrinsic.get(field) for field in OOD_DIAGNOSTIC_FIELDS},
        **{
            field: intrinsic.get(field)
            for field in BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS
        },
        **{
            field: intrinsic.get(field)
            for field in EXPERIMENTAL_DESIGN_ADVISOR_FIELDS
        },
        **{field: intrinsic.get(field) for field in OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS},
        **{
            field: intrinsic.get(field, reference.get(field, summary.get(field)))
            for field in _READOUT_CONVENTION_FIELDS
        },
        **{field: intrinsic.get(field) for field in _PHOTOTHERMAL_POD_FIELDS},
        **{field: intrinsic.get(field) for field in _MIE_INCIDENT_FIELD_FIELDS},
        **{field: intrinsic.get(field) for field in _THRESHOLD_FALSE_ALARM_FIELDS},
        **{
            field: intrinsic.get(field, reference.get(field, summary.get(field)))
            for field in WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS
        },
        **{
            field: intrinsic.get(field, reference.get(field, summary.get(field)))
            for field in FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS
        },
        **{
            field: intrinsic.get(field, reference.get(field, summary.get(field)))
            for field in CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS
        },
    }


def results_to_dataframe(results: list[dict]) -> pd.DataFrame:
    """Flatten sweep results into a DataFrame (one row per case)."""
    rows = []
    for r in results:
        summary = r["summary"]
        intrinsic = r.get("intrinsic", {})
        reference = r.get("reference", {})
        mh = summary["mean_peak_height"]
        sh = summary["std_peak_height"]
        cv = sh / mh if mh > 0 else float("inf")
        case_runtime_seconds = r.get("case_runtime_seconds")
        n_events = int(summary.get("n_events", 0) or 0)
        case_events_per_second = (
            n_events / float(case_runtime_seconds)
            if case_runtime_seconds is not None and float(case_runtime_seconds) > 0
            else None
        )

        rows.append({
            **{
                key: value
                for key, value in _build_result_coordinate_payload(r).items()
                if key.endswith("_nm") or key == "particle_name" or key == "particle_material" or key == "particle_diameter_nm"
            },
            **_build_result_score_payload(r),
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in DESIGN_CLAIM_GOVERNANCE_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in EVENT_QC_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in SELECTION_FUNCTION_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in OOD_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in EXPERIMENTAL_DESIGN_ADVISOR_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in POLARIZATION_JONES_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in ELECTROKINETIC_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in EV_INTEGRITY_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in EV_REPORTING_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in ASSAY_CONTROL_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in DESIGN_METRIC_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in EV_DESIGN_POSTPROCESS_FIELDS
            },
            **{
                field: summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, r.get(field))),
                )
                for field in WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS
            },
            **{
                field: summary.get(field)
                for field in SELECTED_DETECTOR_MODE_DIAGNOSTIC_FIELDS
            },
            "detection_rate": summary["detection_rate"],
            "random_sequence_policy": summary.get("random_sequence_policy"),
            "event_sampling_policy": summary.get("event_sampling_policy"),
            "event_position_low_variance_sampling": summary.get(
                "event_position_low_variance_sampling"
            ),
            "adaptive_event_budget_mode": summary.get("adaptive_event_budget_mode"),
            "adaptive_event_budget_requested_events": summary.get(
                "adaptive_event_budget_requested_events"
            ),
            "adaptive_event_budget_actual_events": summary.get(
                "adaptive_event_budget_actual_events"
            ),
            "adaptive_event_budget_stopped_early": summary.get(
                "adaptive_event_budget_stopped_early"
            ),
            "adaptive_event_budget_stop_reason": summary.get(
                "adaptive_event_budget_stop_reason"
            ),
            "adaptive_event_budget_max_half_width": summary.get(
                "adaptive_event_budget_max_half_width"
            ),
            "case_runtime_seconds": (
                float(case_runtime_seconds)
                if case_runtime_seconds is not None
                else None
            ),
            "case_events_per_second": case_events_per_second,
            "vectorized_event_engine": summary.get("vectorized_event_engine"),
            "event_block_size": summary.get("event_block_size"),
            "event_block_rng_order": summary.get("event_block_rng_order"),
            "vectorized_event_engine_used": summary.get(
                "vectorized_event_engine_used"
            ),
            "vectorized_event_engine_fallback_reason": summary.get(
                "vectorized_event_engine_fallback_reason"
            ),
            "vectorized_event_rng_order": summary.get("vectorized_event_rng_order"),
            "detection_rate_wilson_lb": summary.get("detection_rate_wilson_lb"),
            "stable_detection_rate": summary.get("stable_detection_rate"),
            "stable_detection_rate_wilson_lb": summary.get("stable_detection_rate_wilson_lb"),
            "mean_peak_height": mh,
            "std_peak_height": sh,
            "mean_positive_peak_height": summary.get("mean_positive_peak_height"),
            "mean_negative_peak_height": summary.get("mean_negative_peak_height"),
            "positive_peak_fraction": summary.get("positive_peak_fraction"),
            "negative_peak_fraction": summary.get("negative_peak_fraction"),
            "mean_peak_width_ms": summary["mean_peak_width_s"] * 1e3,
            "phase_flip_fraction": summary.get("phase_flip_fraction"),
            "hit_rate_at_fixed_false_alarm": summary.get("hit_rate_at_fixed_false_alarm"),
            "roc_auc_event_vs_background": summary.get("roc_auc_event_vs_background"),
            "d_prime_event_vs_background": summary.get("d_prime_event_vs_background"),
            "robust_cv_peak_height": summary.get("robust_cv_peak_height"),
            "mean_peak_to_threshold_ratio": summary.get("mean_peak_to_threshold_ratio"),
            "mean_peak_margin_z": summary.get("mean_peak_margin_z"),
            "mean_transit_time_ms": (
                float(summary.get("mean_transit_time_s", 0.0)) * 1e3
                if summary.get("mean_transit_time_s") is not None
                else None
            ),
            "mean_local_snr": summary.get("mean_local_snr"),
            "mean_nodi_transit_bandwidth_Hz": summary.get("mean_nodi_transit_bandwidth_Hz"),
            "mean_nodi_transit_bandwidth_gain": summary.get("mean_nodi_transit_bandwidth_gain"),
            "mean_nodi_bandwidth_limited_fraction": summary.get("mean_nodi_bandwidth_limited_fraction"),
            "path_opd_model": intrinsic.get("path_opd_model"),
            "path_opd_freeze_status": summary.get("path_opd_freeze_status"),
            "interference_overlap_default_freeze_status": summary.get(
                "interference_overlap_default_freeze_status"
            ),
            "projection_default_freeze_status": summary.get(
                "projection_default_freeze_status"
            ),
            "delta_phi_gouy_validity": summary.get("delta_phi_gouy_validity"),
            "delta_phi_gouy_geometry_width_to_waist_ratio": summary.get(
                "delta_phi_gouy_geometry_width_to_waist_ratio"
            ),
            "delta_phi_gouy_geometry_depth_to_waist_ratio": summary.get(
                "delta_phi_gouy_geometry_depth_to_waist_ratio"
            ),
            "observation_freeze_status": summary.get("observation_freeze_status"),
            "engineering_gate_status_label": summary.get("engineering_gate_status_label"),
            "engineering_gate_primary_blocker": summary.get("engineering_gate_primary_blocker"),
            "engineering_gate_primary_blocker_label": summary.get("engineering_gate_primary_blocker_label"),
            "engineering_gate_blocker_summary": summary.get("engineering_gate_blocker_summary"),
            "engineering_gate_guidance": summary.get("engineering_gate_guidance"),
            "design_recommendation_status": summary.get("design_recommendation_status"),
            "design_recommendation_label": summary.get("design_recommendation_label"),
            "design_recommendation_guidance": summary.get("design_recommendation_guidance"),
            "detection_decision_mode": summary.get("detection_decision_mode"),
            "strict_paired_detection_rate_wilson_lb": summary.get(
                "strict_paired_detection_rate_wilson_lb"
            ),
            "paired_detection_rate": summary.get("paired_detection_rate"),
            "CV": cv if cv != float("inf") else None,
            "H_norm": r.get("H_norm", 0.0),
            "R_norm": r.get("R_norm", 0.0),
            "CV_norm": r.get("CV_norm", 1.0),
            "stable_rate_norm": r.get("stable_rate_norm", 0.0),
            "threshold_margin_norm": r.get("threshold_margin_norm", 0.0),
            "local_snr_norm": r.get("local_snr_norm", 0.0),
            "auc_norm": r.get("auc_norm", 0.0),
            "hit_rate_norm": r.get("hit_rate_norm", 0.0),
            "d_prime_norm": r.get("d_prime_norm", 0.0),
            "Csca_m2": intrinsic.get("Csca_m2"),
            "theta_det_deg": (
                float(np.degrees(intrinsic.get("theta_det_rad")))
                if intrinsic.get("theta_det_rad") is not None
                else None
            ),
            "theta_center_deg": (
                float(np.degrees(intrinsic.get("theta_center_rad")))
                if intrinsic.get("theta_center_rad") is not None
                else None
            ),
            "sigma_effective_deg": (
                float(np.degrees(intrinsic.get("sigma_effective_rad")))
                if intrinsic.get("sigma_effective_rad") is not None
                else None
            ),
            "E_sca_at_det": intrinsic.get("E_sca_at_det"),
            "E_sca_ref": intrinsic.get("E_sca_ref"),
            "E_sca_normalized": intrinsic.get("E_sca_unit_normalized"),
            "phi_projection_rad": intrinsic.get("phi_projection_rad"),
            "phi_sca_material_rad": intrinsic.get("phi_sca_material_rad"),
            "detection_operator_signature": intrinsic.get("operator_signature"),
            "operator_route": intrinsic.get("operator_route"),
            "operator_normalization": intrinsic.get("operator_normalization"),
            "collection_operator_calibration_status": intrinsic.get(
                "collection_operator_calibration_status"
            ),
            "collection_operator_coverage_status": intrinsic.get(
                "collection_operator_coverage_status"
            ),
            "collection_operator_id": intrinsic.get("collection_operator_id"),
            "collection_operator_calibrated_geometry": intrinsic.get(
                "collection_operator_calibrated_geometry"
            ),
            **{
                field: intrinsic.get(field)
                for field in _COLLECTION_OPERATOR_EXTRA_FIELDS
            },
            "absolute_throughput_calibrated": intrinsic.get(
                "absolute_throughput_calibrated"
            ),
            "observation_signature": intrinsic.get("observation_signature"),
            "detector_forward_model": intrinsic.get("detector_forward_model"),
            "detector_forward_status": intrinsic.get("detector_forward_status"),
            "detector_forward_claim_level": intrinsic.get("detector_forward_claim_level"),
            "field_coordinate_measure": intrinsic.get("field_coordinate_measure"),
            "field_measure_status": intrinsic.get("field_measure_status"),
            "bfp_to_angle_jacobian_applied": intrinsic.get(
                "bfp_to_angle_jacobian_applied"
            ),
            "detector_mask_units": intrinsic.get("detector_mask_units"),
            "coordinate_frame_mapping": intrinsic.get("coordinate_frame_mapping"),
            "joint_overlap_used": intrinsic.get("joint_overlap_used"),
            "complex_time_harmonic_convention": intrinsic.get(
                "complex_time_harmonic_convention"
            ),
            "fourier_transform_sign_convention": intrinsic.get(
                "fourier_transform_sign_convention"
            ),
            "mie_amplitude_phase_convention": intrinsic.get(
                "mie_amplitude_phase_convention"
            ),
            "interference_conjugation_convention": intrinsic.get(
                "interference_conjugation_convention"
            ),
            "interference_cross_term_convention": intrinsic.get(
                "interference_cross_term_convention"
            ),
            "global_phase_offset_source": intrinsic.get("global_phase_offset_source"),
            "absolute_polarity_claim": intrinsic.get("absolute_polarity_claim"),
            "complex_convention_status": intrinsic.get("complex_convention_status"),
            "complex_field_claim_level": intrinsic.get("complex_field_claim_level"),
            "polarization_basis_model": intrinsic.get("polarization_basis_model"),
            "jones_basis_status": intrinsic.get("jones_basis_status"),
            "vector_optics_mode": intrinsic.get("vector_optics_mode"),
            "mie_s1_s2_lab_basis_mapping": intrinsic.get(
                "mie_s1_s2_lab_basis_mapping"
            ),
            "active_mie_basis_component": intrinsic.get(
                "active_mie_basis_component"
            ),
            "S1S2_to_lab_basis_rotation_applied": intrinsic.get(
                "S1S2_to_lab_basis_rotation_applied"
            ),
            "reference_jones_field_defined": intrinsic.get(
                "reference_jones_field_defined"
            ),
            "detector_analyzer_jones_matrix_defined": intrinsic.get(
                "detector_analyzer_jones_matrix_defined"
            ),
            "mie_jones_bridge_status": intrinsic.get("mie_jones_bridge_status"),
            "high_NA_collection_warning": intrinsic.get("high_NA_collection_warning"),
            "vector_validity_status": intrinsic.get("vector_validity_status"),
            "calibration_state_machine_version": intrinsic.get(
                "calibration_state_machine_version"
            ),
            "calibration_state_machine_status": intrinsic.get(
                "calibration_state_machine_status"
            ),
            "output_claim_level": intrinsic.get("output_claim_level"),
            "calibrated_quantitative_unlocked": intrinsic.get(
                "calibrated_quantitative_unlocked"
            ),
            "output_claim_blocker_summary": intrinsic.get(
                "output_claim_blocker_summary"
            ),
            "scattering_normalization_route": intrinsic.get(
                "scattering_normalization_route"
            ),
            "scattering_normalization_status": intrinsic.get(
                "scattering_normalization_status"
            ),
            "scattering_calibration_level": intrinsic.get(
                "scattering_calibration_level"
            ),
            "baseline_normalization_role": intrinsic.get(
                "baseline_normalization_role"
            ),
            "baseline_particle_absolute_scale_restored": intrinsic.get(
                "baseline_particle_absolute_scale_restored"
            ),
            "baseline_normalized_E_sca_allowed_in_photon_unit_route": intrinsic.get(
                "baseline_normalized_E_sca_allowed_in_photon_unit_route"
            ),
            "K_sca_calibration_status": intrinsic.get("K_sca_calibration_status"),
            "K_sca_value": intrinsic.get("K_sca_value"),
            "K_sca_role": intrinsic.get("K_sca_role"),
            "mie_to_power_chain_status": intrinsic.get("mie_to_power_chain_status"),
            "scattered_power_conversion_status": intrinsic.get(
                "scattered_power_conversion_status"
            ),
            "detector_field_units": intrinsic.get("detector_field_units"),
            "power_chain_absolute_units_available": intrinsic.get(
                "power_chain_absolute_units_available"
            ),
            "K_sca_power_chain_role": intrinsic.get("K_sca_power_chain_role"),
            "mie_to_power_chain_blocker_summary": intrinsic.get(
                "mie_to_power_chain_blocker_summary"
            ),
            "standard_particle_calibration_path_configured": intrinsic.get(
                "standard_particle_calibration_path_configured"
            ),
            "standard_particle_calibration_coverage_status": intrinsic.get(
                "standard_particle_calibration_coverage_status"
            ),
            "global_phase_offset_calibration_status": intrinsic.get(
                "global_phase_offset_calibration_status"
            ),
            "K_sca_uncertainty_status": intrinsic.get("K_sca_uncertainty_status"),
            "K_sca_uncertainty_propagated_to_outputs": intrinsic.get(
                "K_sca_uncertainty_propagated_to_outputs"
            ),
            "standard_particle_uncertainty_budget_status": intrinsic.get(
                "standard_particle_uncertainty_budget_status"
            ),
            "standard_particle_size_distribution_status": intrinsic.get(
                "standard_particle_size_distribution_status"
            ),
            "standard_particle_shape_uncertainty_status": intrinsic.get(
                "standard_particle_shape_uncertainty_status"
            ),
            "standard_particle_ligand_shell_status": intrinsic.get(
                "standard_particle_ligand_shell_status"
            ),
            "standard_particle_batch_status": intrinsic.get(
                "standard_particle_batch_status"
            ),
            "standard_particle_concentration_uncertainty_status": intrinsic.get(
                "standard_particle_concentration_uncertainty_status"
            ),
            "standard_particle_material_dataset_uncertainty_status": intrinsic.get(
                "standard_particle_material_dataset_uncertainty_status"
            ),
            "calibration_design_rank": intrinsic.get("calibration_design_rank"),
            "calibration_standard_count": intrinsic.get("calibration_standard_count"),
            "calibration_wavelength_count": intrinsic.get(
                "calibration_wavelength_count"
            ),
            "calibration_geometry_count": intrinsic.get("calibration_geometry_count"),
            "calibration_held_out_validation_status": intrinsic.get(
                "calibration_held_out_validation_status"
            ),
            "calibration_held_out_error": intrinsic.get("calibration_held_out_error"),
            "calibration_identifiability_blocker_summary": intrinsic.get(
                "calibration_identifiability_blocker_summary"
            ),
            "calibration_fit_parameter_coupling_status": intrinsic.get(
                "calibration_fit_parameter_coupling_status"
            ),
            "calibration_design_minimum_requirement_status": intrinsic.get(
                "calibration_design_minimum_requirement_status"
            ),
            "fit_parameters_identifiable": intrinsic.get(
                "fit_parameters_identifiable"
            ),
            "detector_calibration_level": intrinsic.get("detector_calibration_level"),
            "readout_calibration_level": intrinsic.get("readout_calibration_level"),
            "count_calibration_level": intrinsic.get("count_calibration_level"),
            **{
                field: intrinsic.get(field)
                for field in _CALIBRATION_STATE_EXTRA_FIELDS
            },
            "noise_model_route": intrinsic.get("noise_model_route"),
            "detector_noise_claim_level": intrinsic.get("detector_noise_claim_level"),
            "absolute_throughput_route": intrinsic.get("absolute_throughput_route"),
            "photon_unit_noise_model_status": intrinsic.get(
                "photon_unit_noise_model_status"
            ),
            "lockin_ENBW_Hz": intrinsic.get("lockin_ENBW_Hz"),
            "lockin_ENBW_status": intrinsic.get("lockin_ENBW_status"),
            "lockin_ENBW_claim_level": intrinsic.get("lockin_ENBW_claim_level"),
            "shot_noise_model_status": intrinsic.get("shot_noise_model_status"),
            "photon_shot_noise_term_status": intrinsic.get(
                "photon_shot_noise_term_status"
            ),
            "electronics_noise_model_status": intrinsic.get(
                "electronics_noise_model_status"
            ),
            "electronics_noise_term_status": intrinsic.get(
                "electronics_noise_term_status"
            ),
            "rin_noise_model_status": intrinsic.get("rin_noise_model_status"),
            "rin_noise_term_status": intrinsic.get("rin_noise_term_status"),
            "speckle_background_noise_model_status": intrinsic.get(
                "speckle_background_noise_model_status"
            ),
            "speckle_like_noise_term_status": intrinsic.get(
                "speckle_like_noise_term_status"
            ),
            "drift_noise_term_status": intrinsic.get("drift_noise_term_status"),
            "lockin_output_noise_term_status": intrinsic.get(
                "lockin_output_noise_term_status"
            ),
            "noise_terms_schema_version": intrinsic.get("noise_terms_schema_version"),
            "noise_term_quantitative_contribution_status": intrinsic.get(
                "noise_term_quantitative_contribution_status"
            ),
            "detector_dynamic_range_model": intrinsic.get(
                "detector_dynamic_range_model"
            ),
            "detector_saturation_status": intrinsic.get(
                "detector_saturation_status"
            ),
            "dynamic_range_margin": intrinsic.get("dynamic_range_margin"),
            "ADC_dynamic_range_status": intrinsic.get("ADC_dynamic_range_status"),
            "reference_enhancement_gain": intrinsic.get("reference_enhancement_gain"),
            "reference_enhancement_snr_claim": intrinsic.get(
                "reference_enhancement_snr_claim"
            ),
            "background_field_model": intrinsic.get("background_field_model"),
            "background_field_status": intrinsic.get("background_field_status"),
            "background_claim_level": intrinsic.get("background_claim_level"),
            "residual_transmitted_leakage_status": intrinsic.get(
                "residual_transmitted_leakage_status"
            ),
            "stray_light_status": intrinsic.get("stray_light_status"),
            "blank_trace_empirical_available": intrinsic.get(
                "blank_trace_empirical_available"
            ),
            "particle_induced_channel_phase_perturbation_status": intrinsic.get(
                "particle_induced_channel_phase_perturbation_status"
            ),
            "independent_superposition_status": intrinsic.get(
                "independent_superposition_status"
            ),
            "superposition_validity_status": intrinsic.get(
                "superposition_validity_status"
            ),
            "E_sca_to_E_ref_amplitude_ratio_estimate": intrinsic.get(
                "E_sca_to_E_ref_amplitude_ratio_estimate"
            ),
            "extinction_to_beam_area_estimate": intrinsic.get(
                "extinction_to_beam_area_estimate"
            ),
            "reference_depletion_fraction_estimate": intrinsic.get(
                "reference_depletion_fraction_estimate"
            ),
            "reference_depletion_estimate_status": intrinsic.get(
                "reference_depletion_estimate_status"
            ),
            "channel_particle_coupling_model": intrinsic.get(
                "channel_particle_coupling_model"
            ),
            "joint_fullwave_required_for_quantitative_phase": intrinsic.get(
                "joint_fullwave_required_for_quantitative_phase"
            ),
            "superposition_validity_claim_level": intrinsic.get(
                "superposition_validity_claim_level"
            ),
            "superposition_validity_blocker_summary": intrinsic.get(
                "superposition_validity_blocker_summary"
            ),
            "nodi_signal_component_model": intrinsic.get("nodi_signal_component_model"),
            "nodi_signal_component_status": intrinsic.get("nodi_signal_component_status"),
            "nodi_forward_extinction_leakage_status": intrinsic.get(
                "nodi_forward_extinction_leakage_status"
            ),
            "nodi_transmitted_leakage_component_status": intrinsic.get(
                "nodi_transmitted_leakage_component_status"
            ),
            "nodi_particle_induced_channel_coupling_status": intrinsic.get(
                "nodi_particle_induced_channel_coupling_status"
            ),
            "nodi_signal_component_claim_level": intrinsic.get(
                "nodi_signal_component_claim_level"
            ),
            "nodi_component_escalation_route": intrinsic.get(
                "nodi_component_escalation_route"
            ),
            **{field: intrinsic.get(field) for field in _PARTICLE_MODEL_FIELDS},
            **{
                field: intrinsic.get(field)
                for field in EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS
            },
            **{field: intrinsic.get(field) for field in _INTERFACE_CORRECTION_FIELDS},
            **{field: intrinsic.get(field) for field in _COUNT_MODEL_FIELDS},
            **{
                field: intrinsic.get(field)
                for field in COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS
            },
            **{
                field: intrinsic.get(field)
                for field in POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
            },
            **{field: intrinsic.get(field) for field in OOD_DIAGNOSTIC_FIELDS},
            **{
                field: intrinsic.get(field)
                for field in BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS
            },
            **{
                field: intrinsic.get(field)
                for field in EXPERIMENTAL_DESIGN_ADVISOR_FIELDS
            },
            **{
                field: intrinsic.get(field)
                for field in OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS
            },
            **{
                field: intrinsic.get(field, reference.get(field, summary.get(field)))
                for field in _READOUT_CONVENTION_FIELDS
            },
            **{field: intrinsic.get(field) for field in _PHOTOTHERMAL_POD_FIELDS},
            **{field: intrinsic.get(field) for field in _MIE_INCIDENT_FIELD_FIELDS},
            **{field: intrinsic.get(field) for field in _THRESHOLD_FALSE_ALARM_FIELDS},
            **{
                field: intrinsic.get(field, reference.get(field, summary.get(field)))
                for field in WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS
            },
            "A_ref": reference.get("A_ref"),
            "g_ref": reference.get("g_ref"),
            "reference_route": reference.get("reference_route"),
            "reference_claim_level": reference.get("reference_claim_level"),
            "reference_solver_route": reference.get("reference_solver_route"),
            "reference_solver_status": reference.get("reference_solver_status"),
            "reference_solver_detector_bridge_status": reference.get(
                "reference_solver_detector_bridge_status"
            ),
            "phase_filter_validity": reference.get("phase_filter_validity"),
            "phase_filter_H_over_lambda0": reference.get(
                "phase_filter_H_over_lambda0"
            ),
            "phase_filter_delta_ref_rad": reference.get("phase_filter_delta_ref_rad"),
            "phase_filter_theta_signed_rad": reference.get(
                "phase_filter_theta_signed_rad"
            ),
            "phase_filter_H_over_zR": reference.get("phase_filter_H_over_zR"),
            "phase_filter_multiple_reflection_warning": reference.get(
                "phase_filter_multiple_reflection_warning"
            ),
            "subwavelength_groove_validity_status": reference.get(
                "subwavelength_groove_validity_status"
            ),
            "finite_length_assumption_status": reference.get(
                "finite_length_assumption_status"
            ),
            "sidewall_scattering_roughness_status": reference.get(
                "sidewall_scattering_roughness_status"
            ),
            "evanescent_component_unmodeled": reference.get(
                "evanescent_component_unmodeled"
            ),
            "groove_waveguide_mode_unmodeled": reference.get(
                "groove_waveguide_mode_unmodeled"
            ),
            "roughness_scatter_unmodeled": reference.get(
                "roughness_scatter_unmodeled"
            ),
            "depth_validity_reason": reference.get("depth_validity_reason"),
            "requires_calibration_or_fullwave": reference.get(
                "requires_calibration_or_fullwave"
            ),
            "reference_calibration_amplitude_status": reference.get(
                "reference_calibration_amplitude_status"
            ),
            "reference_calibration_coverage_status": reference.get(
                "reference_calibration_coverage_status"
            ),
            **{
                field: reference.get(field)
                for field in _REFERENCE_CALIBRATION_EXTRA_FIELDS
            },
            "reference_phase_calibration_status": reference.get(
                "reference_phase_calibration_status"
            ),
            "mean_I_baseline": summary.get("mean_I_baseline"),
            "mean_shot_noise_std": summary.get("mean_shot_noise_std"),
            "rho_requested": summary.get("rho_requested"),
            "rho_physical_envelope_nominal": summary.get("rho_physical_envelope_nominal"),
            "rho_physical_envelope_status": summary.get("rho_physical_envelope_status"),
            "reference_width_saturation_status": reference.get("reference_width_saturation_status"),
            "reference_width_saturation_factor": reference.get("reference_width_saturation_factor"),
            "na_cutoff_active": reference.get("na_cutoff_active"),
            "na_cutoff_policy": reference.get("na_cutoff_policy"),
            "na_cutoff_hard_zero_applied": reference.get(
                "na_cutoff_hard_zero_applied"
            ),
            "na_cutoff_NA_collection": reference.get("na_cutoff_NA_collection"),
        })

    return pd.DataFrame(rows)


def results_to_design_postprocess_dataframe(results: list[dict]) -> pd.DataFrame:
    """Flatten design-postprocess diagnostics into a focused export table."""
    rows = []
    fields = tuple(
        dict.fromkeys(DESIGN_METRIC_DIAGNOSTIC_FIELDS + EV_DESIGN_POSTPROCESS_FIELDS)
    )
    for result in results:
        summary = result.get("summary", {})
        intrinsic = result.get("intrinsic", {})
        reference = result.get("reference", {})
        rows.append(
            {
                **_build_result_coordinate_payload(result),
                **{
                    field: summary.get(
                        field,
                        intrinsic.get(field, reference.get(field, result.get(field))),
                    )
                    for field in fields
                },
            }
        )
        if rows[-1].get("EV_design_claim_forbidden_text") is None:
            rows[-1].update(generate_claim_boundary_text(rows[-1]))
    return pd.DataFrame(rows)


def results_to_physics_fields_dataframe(results: list[dict]) -> pd.DataFrame:
    """Flatten compact physics fields into one row per case."""
    rows = []
    for result in results:
        rows.append(
            {
                **_build_result_coordinate_payload(result),
                **{
                    key: _export_cell_value(value)
                    for key, value in _build_compact_physics_payload(result).items()
                },
            }
        )
    return pd.DataFrame(rows)


def results_to_diagnostics_long_dataframe(results: list[dict]) -> pd.DataFrame:
    """Export governed diagnostics as long-form field/value rows."""
    diagnostic_groups = {
        "minimum_design_claim_schema": DESIGN_CLAIM_GOVERNANCE_FIELDS,
        "event_quality_control": EVENT_QC_DIAGNOSTIC_FIELDS,
        "selection_function": SELECTION_FUNCTION_DIAGNOSTIC_FIELDS,
        "readout_convention": _READOUT_CONVENTION_FIELDS,
        "ev_population_prior": EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS,
        "count_likelihood": COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS,
        "population_inference": POPULATION_INFERENCE_DIAGNOSTIC_FIELDS,
        "ood_detection": OOD_DIAGNOSTIC_FIELDS,
        "bayesian_calibration": BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS,
        "experimental_design_advisor": EXPERIMENTAL_DESIGN_ADVISOR_FIELDS,
        "objective_panel": OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS,
        "polarization_jones_operator": POLARIZATION_JONES_DIAGNOSTIC_FIELDS,
        "nodi_thermal_contamination": NODI_THERMAL_CONTAMINATION_FIELDS,
        "run_state_model": RUN_STATE_DIAGNOSTIC_FIELDS,
        "channel_geometry": CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS,
        "electrokinetic_transport": ELECTROKINETIC_DIAGNOSTIC_FIELDS,
        "ev_integrity_risk": EV_INTEGRITY_DIAGNOSTIC_FIELDS,
        "ev_reporting_metadata": EV_REPORTING_DIAGNOSTIC_FIELDS,
        "assay_control_matrix": ASSAY_CONTROL_DIAGNOSTIC_FIELDS,
        "control_interpretation": CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS,
        "recompute_manifest": RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS,
        "bfp_detector_operator": BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS,
        "particle_channel_perturbation": PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS,
        "tsuyama_bfp_reference": TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS,
        "reference_operating_point": REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS,
        "fluidic_resistance": FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS,
        "fluidic_network_model": FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS,
        "particle_design_library": PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS,
        "design_metrics": DESIGN_METRIC_DIAGNOSTIC_FIELDS,
        "ev_design_postprocess": EV_DESIGN_POSTPROCESS_FIELDS,
        "wavelength_material_governance": WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS,
        "selected_detector_mode": SELECTED_DETECTOR_MODE_DIAGNOSTIC_FIELDS,
    }
    rows = []
    for result in results:
        identity = _build_result_coordinate_payload(result)
        summary = result.get("summary", {})
        intrinsic = result.get("intrinsic", {})
        reference = result.get("reference", {})
        for group_name, fields in diagnostic_groups.items():
            for field in fields:
                value = summary.get(
                    field,
                    intrinsic.get(field, reference.get(field, result.get(field))),
                )
                if value is None:
                    continue
                rows.append(
                    {
                        **identity,
                        "diagnostic_group": group_name,
                        "field": field,
                        "value": _export_cell_value(value),
                    }
                )
    return pd.DataFrame(rows)


def results_to_compact(results: list[dict]) -> list[dict]:
    """
    Extract compact data (summary + physics + scores) for pkl storage.
    Drops event traces to keep file size manageable.
    """
    compact = []
    for r in results:
        identity = _build_result_coordinate_payload(r)
        score_payload = _build_result_score_payload(r)
        compact.append({
            "particle_name": identity["particle_name"],
            "particle_material": identity["particle_material"],
            "particle_diameter_nm": identity["particle_diameter_nm"],
            "wavelength_m": identity["wavelength_m"],
            "width_m": identity["width_m"],
            "depth_m": identity["depth_m"],
            "summary": _build_compact_summary_payload(r),
            "physics": _build_compact_physics_payload(r),
            **score_payload,
            "engineering_basis_n_detected": r.get("engineering_basis_n_detected"),
            "engineering_basis_phase_flip_fraction": r.get(
                "engineering_basis_phase_flip_fraction"
            ),
        })
    return compact


def build_particle_model_catalog(
    particle_types: list,
    sim_cfg: Any | None = None,
) -> list[dict[str, Any]]:
    """
    Build a compact per-particle model catalog for metadata export.

    This keeps dataset-level provenance explicit when multiple particle
    optical models share the same display material label, such as the legacy
    uniform exosome and the new biomimetic core-shell exosome.
    """
    catalog: list[dict[str, Any]] = []
    for particle in particle_types:
        particle_name = str(particle.name)
        material = infer_particle_material(particle_name)
        structure_key = getattr(particle, "structure_key", None)
        is_ev_like = material == "exosome" or particle_name.startswith("exosome_")
        if structure_key == "exosome_biomimetic":
            particle_optical_model = "core_shell_EV_sEV_surrogate"
        elif is_ev_like:
            particle_optical_model = "homogeneous_EV_sEV_surrogate"
        else:
            particle_optical_model = "homogeneous_mie_sphere"
        catalog.append(
            {
                "particle_name": particle_name,
                "particle_material": material,
                "particle_diameter_nm": infer_particle_diameter_nm(particle_name),
                "particle_family": "EV_sEV" if is_ev_like else material,
                "particle_optical_model": particle_optical_model,
                "EV_label": "exosome_like" if is_ev_like else None,
                "EV_claim_level": (
                    "optical_EV_like_particle" if is_ev_like else "not_applicable"
                ),
                "EV_ensemble_mode": (
                    getattr(sim_cfg, "EV_ensemble_mode", None)
                    if sim_cfg is not None
                    else None
                ),
                "EV_ensemble_name": (
                    (getattr(particle, "structure_params", None) or {}).get(
                        "EV_ensemble_name"
                    )
                    if isinstance(getattr(particle, "structure_params", None), dict)
                    else None
                ),
                "EV_ensemble_member_preset": (
                    (getattr(particle, "structure_params", None) or {}).get(
                        "EV_ensemble_member_preset"
                    )
                    if isinstance(getattr(particle, "structure_params", None), dict)
                    else None
                ),
                "particle_uncertainty_budget_model": (
                    getattr(sim_cfg, "particle_uncertainty_budget_model", None)
                    if sim_cfg is not None
                    else None
                ),
                "uncertainty_propagation_mode": (
                    getattr(sim_cfg, "particle_uncertainty_propagation_mode", None)
                    if sim_cfg is not None
                    else None
                ),
                "thermal_pod_model": (
                    getattr(sim_cfg, "thermal_pod_model", None)
                    if sim_cfg is not None
                    else None
                ),
                "pod_roi_sensitivity_derivative_status": (
                    getattr(sim_cfg, "pod_roi_sensitivity_derivative_status", None)
                    if sim_cfg is not None
                    else None
                ),
                "pod_signal_sign_source": (
                    getattr(sim_cfg, "pod_signal_sign_source", None)
                    if sim_cfg is not None
                    else None
                ),
                "model_type": str(getattr(particle, "model_type", "mie")),
                "material_key": getattr(particle, "material_key", None),
                "use_material_model": bool(getattr(particle, "use_material_model", False)),
                "structure_key": structure_key,
                "structure_params": deepcopy(getattr(particle, "structure_params", None)),
            }
        )
    return catalog


def _metadata_status_distribution(values: list[object]) -> dict[str, dict[str, float | int]]:
    cleaned: list[str] = []
    for value in values:
        if value is None:
            cleaned.append("missing")
            continue
        text = str(value)
        cleaned.append(text if text and text.lower() != "nan" else "missing")
    total = max(len(cleaned), 1)
    return {
        key: {"count": int(count), "fraction": float(count / total)}
        for key, count in Counter(cleaned).most_common()
    }


def build_reference_calibration_health(
    results: list[dict],
    sim_cfg: Any,
) -> dict[str, Any]:
    """Summarize blank-reference calibration coverage for metadata."""
    reference_model = str(getattr(sim_cfg, "reference_model", "unknown"))
    reference_route = str(getattr(sim_cfg, "reference_route", "unknown"))
    calibration_path = getattr(sim_cfg, "reference_calibration_path", None)
    path_configured = bool(calibration_path)
    active = bool(reference_model == "calibrated_lookup" and path_configured)

    references = [
        result.get("reference", result.get("physics", {}))
        for result in results
        if isinstance(result, Mapping)
    ]
    amplitude_statuses = [
        reference.get("reference_calibration_amplitude_status")
        for reference in references
        if isinstance(reference, Mapping)
    ]
    coverage_statuses = [
        reference.get("reference_calibration_coverage_status")
        for reference in references
        if isinstance(reference, Mapping)
    ]
    phase_statuses = [
        reference.get("reference_phase_calibration_status")
        for reference in references
        if isinstance(reference, Mapping)
    ]
    data_roles = [
        reference.get("reference_calibration_data_role")
        for reference in references
        if isinstance(reference, Mapping)
    ]
    row_ids = [
        reference.get("reference_calibration_row_id")
        for reference in references
        if isinstance(reference, Mapping)
    ]
    synthetic_count = int(
        sum(
            bool(reference.get("reference_calibration_synthetic_fixture_active"))
            for reference in references
            if isinstance(reference, Mapping)
        )
    )
    rho_used_flags = [
        bool(reference.get("rho_used_for_reference_amplitude"))
        for reference in references
        if isinstance(reference, Mapping)
    ]

    n_cases = int(len(results))
    absolute_calibrated_count = int(
        sum(status == "absolute_calibrated" for status in amplitude_statuses)
    )
    scale_only_count = int(
        sum(status == "calibrated_scale_only" for status in amplitude_statuses)
    )
    extrapolated_count = int(
        sum(status == "extrapolated_nearest_fallback" for status in coverage_statuses)
    )
    rho_dependent_count = int(sum(rho_used_flags))
    measured_phase_count = int(
        sum(status == "measured_or_fitted_phase_with_source" for status in phase_statuses)
    )

    if not active:
        health_status = "inactive_no_blank_calibration_path"
        guidance = (
            "reference_model is not using calibrated_lookup with a configured "
            "blank table; reference amplitude remains an engineering fallback."
        )
    elif n_cases == 0:
        health_status = "active_no_cases_evaluated"
        guidance = (
            "blank calibration path is configured, but no computed cases were "
            "available to assess grid coverage."
        )
    elif extrapolated_count > 0:
        health_status = "active_with_extrapolated_cases"
        guidance = (
            "some cases use nearest-fallback calibration outside table coverage; "
            "treat them as calibration extrapolations."
        )
    elif absolute_calibrated_count == 0:
        health_status = "active_scale_only_no_A_ref_cases"
        guidance = (
            "calibration rows only provide g_ref for evaluated cases, so A_ref "
            "still depends on rho and cannot unlock absolute reference claims."
        )
    else:
        health_status = "active_covered"
        guidance = (
            "evaluated cases with calibrated_lookup are covered by the blank "
            "reference table; remaining claim level is governed by phase, "
            "scattering, detector, readout, and count calibration states."
        )

    denominator = max(n_cases, 1)
    return {
        "reference_calibration_health_schema": "reference_calibration_health_v1",
        "reference_model": reference_model,
        "reference_route": reference_route,
        "reference_calibration_path_configured": path_configured,
        "reference_calibration_active": active,
        "n_cases": n_cases,
        "health_status": health_status,
        "amplitude_status_distribution": _metadata_status_distribution(
            amplitude_statuses
        ),
        "coverage_status_distribution": _metadata_status_distribution(
            coverage_statuses
        ),
        "phase_status_distribution": _metadata_status_distribution(phase_statuses),
        "data_role_distribution": _metadata_status_distribution(data_roles),
        "matched_row_id_distribution": _metadata_status_distribution(row_ids),
        "synthetic_fixture_case_count": synthetic_count,
        "absolute_A_ref_case_count": absolute_calibrated_count,
        "scale_only_case_count": scale_only_count,
        "extrapolated_case_count": extrapolated_count,
        "rho_dependent_reference_case_count": rho_dependent_count,
        "measured_or_fitted_phase_case_count": measured_phase_count,
        "absolute_A_ref_case_fraction": float(absolute_calibrated_count / denominator),
        "scale_only_case_fraction": float(scale_only_count / denominator),
        "extrapolated_case_fraction": float(extrapolated_count / denominator),
        "rho_dependent_reference_case_fraction": float(
            rho_dependent_count / denominator
        ),
        "measured_or_fitted_phase_case_fraction": float(
            measured_phase_count / denominator
        ),
        "synthetic_fixture_case_fraction": float(synthetic_count / denominator),
        "guidance": guidance,
    }


def build_collection_operator_calibration_health(
    results: list[dict],
    sim_cfg: Any,
) -> dict[str, Any]:
    """Summarize calibrated collection-operator coverage for metadata."""
    path_configured = bool(
        getattr(sim_cfg, "collection_operator_calibration_path", None)
    )
    operator_id = getattr(sim_cfg, "collection_operator_id", None)
    physics_rows = [
        result.get("intrinsic", result.get("physics", {}))
        for result in results
        if isinstance(result, Mapping)
    ]
    n_cases = len(physics_rows)
    statuses = [
        row.get("collection_operator_calibration_status")
        for row in physics_rows
        if isinstance(row, Mapping)
    ]
    coverage_statuses = [
        row.get("collection_operator_coverage_status")
        for row in physics_rows
        if isinstance(row, Mapping)
    ]
    routes = [
        row.get("operator_route")
        for row in physics_rows
        if isinstance(row, Mapping)
    ]
    normalizations = [
        row.get("operator_normalization")
        for row in physics_rows
        if isinstance(row, Mapping)
    ]
    data_roles = [
        row.get("collection_operator_calibration_data_role")
        for row in physics_rows
        if isinstance(row, Mapping)
    ]
    row_ids = [
        row.get("collection_operator_calibration_row_id")
        for row in physics_rows
        if isinstance(row, Mapping)
    ]
    synthetic_count = int(
        sum(
            bool(row.get("collection_operator_synthetic_fixture_active"))
            for row in physics_rows
            if isinstance(row, Mapping)
        )
    )
    calibrated_geometry_count = int(
        sum(
            bool(row.get("collection_operator_calibrated_geometry"))
            for row in physics_rows
            if isinstance(row, Mapping)
        )
    )
    absolute_throughput_count = int(
        sum(
            bool(row.get("absolute_throughput_calibrated"))
            for row in physics_rows
            if isinstance(row, Mapping)
        )
    )
    extrapolated_count = int(
        sum(
            str(row.get("collection_operator_coverage_status"))
            == "extrapolated_nearest_row"
            for row in physics_rows
            if isinstance(row, Mapping)
        )
    )

    if not path_configured:
        health_status = "inactive_no_operator_calibration_path"
        guidance = (
            "Collection uses the configured surrogate operator; quantitative "
            "throughput remains unavailable."
        )
    elif n_cases == 0:
        health_status = "active_no_cases_evaluated"
        guidance = "Operator calibration path is configured but no cases were evaluated."
    elif synthetic_count > 0:
        health_status = "active_synthetic_fixture_not_applied"
        guidance = (
            "At least one row came from a synthetic/template fixture and was not "
            "applied as experimental calibration."
        )
    elif extrapolated_count > 0:
        health_status = "active_with_extrapolated_operator_cases"
        guidance = (
            "At least one case used nearest-row extrapolation; inspect geometry "
            "coverage before quantitative comparison."
        )
    elif absolute_throughput_count == 0:
        health_status = "active_geometry_only_no_absolute_throughput"
        guidance = (
            "Operator geometry is calibrated, but no absolute throughput row "
            "was available for detector-unit SNR."
        )
    else:
        health_status = "active_operator_covered"
        guidance = "Collection operator geometry and absolute throughput are covered."

    denominator = max(n_cases, 1)
    return {
        "collection_operator_calibration_health_schema": (
            "collection_operator_calibration_health_v1"
        ),
        "collection_operator_calibration_path_configured": path_configured,
        "collection_operator_id": operator_id,
        "absolute_throughput_route": getattr(
            sim_cfg,
            "absolute_throughput_route",
            None,
        ),
        "n_cases": n_cases,
        "health_status": health_status,
        "operator_route_distribution": _metadata_status_distribution(routes),
        "operator_normalization_distribution": _metadata_status_distribution(
            normalizations
        ),
        "calibration_status_distribution": _metadata_status_distribution(statuses),
        "coverage_status_distribution": _metadata_status_distribution(
            coverage_statuses
        ),
        "data_role_distribution": _metadata_status_distribution(data_roles),
        "matched_row_id_distribution": _metadata_status_distribution(row_ids),
        "synthetic_fixture_case_count": synthetic_count,
        "calibrated_geometry_case_count": calibrated_geometry_count,
        "absolute_throughput_case_count": absolute_throughput_count,
        "extrapolated_operator_case_count": extrapolated_count,
        "calibrated_geometry_case_fraction": float(
            calibrated_geometry_count / denominator
        ),
        "absolute_throughput_case_fraction": float(
            absolute_throughput_count / denominator
        ),
        "extrapolated_operator_case_fraction": float(
            extrapolated_count / denominator
        ),
        "synthetic_fixture_case_fraction": float(synthetic_count / denominator),
        "guidance": guidance,
    }


def build_schema_feature_inventory(sim_cfg: Any) -> dict[str, Any]:
    """
    Build the schema-level provenance contract exported in `meta.json`.

    This is a route/field inventory rather than a case-level result summary.
    Case-specific values still live in summary/compact rows; metadata records
    which governed provenance groups this schema promises to export.
    """
    return {
        "inventory_schema_version": "schema_feature_inventory_v1",
        "required_metadata_sections": [
            "sim_cfg",
            "optical",
            "particle_models",
            "reference_calibration_health",
            "collection_operator_calibration_health",
            "schema_feature_inventory",
        ],
        "route_contract": {
            "reference_route_config": getattr(sim_cfg, "reference_route", None),
            "reference_solver_route_config": getattr(
                sim_cfg,
                "reference_solver_route",
                None,
            ),
            "reference_model": getattr(sim_cfg, "reference_model", None),
            "detector_forward_model": getattr(
                sim_cfg,
                "detector_forward_model",
                None,
            ),
            "field_coordinate_measure": getattr(
                sim_cfg,
                "field_coordinate_measure",
                None,
            ),
            "polarization_jones_operator_mode": getattr(
                sim_cfg,
                "polarization_jones_operator_mode",
                None,
            ),
            "bfp_to_angle_jacobian_applied": getattr(
                sim_cfg,
                "bfp_to_angle_jacobian_applied",
                None,
            ),
            "coordinate_frame_mapping": getattr(
                sim_cfg,
                "coordinate_frame_mapping",
                None,
            ),
            "collection_operator_calibration_path_configured": bool(
                getattr(sim_cfg, "collection_operator_calibration_path", None)
            ),
            "collection_operator_id": getattr(
                sim_cfg,
                "collection_operator_id",
                None,
            ),
            "absolute_throughput_route": getattr(
                sim_cfg,
                "absolute_throughput_route",
                None,
            ),
            "standard_particle_calibration_path_configured": bool(
                getattr(sim_cfg, "standard_particle_calibration_path", None)
            ),
            "standard_particle_calibration_id": getattr(
                sim_cfg,
                "standard_particle_calibration_id",
                None,
            ),
            "readout_preset": getattr(sim_cfg, "readout_preset", None),
            "threshold_tail": getattr(sim_cfg, "threshold_tail", None),
            "blank_false_positive_calibration_path_configured": bool(
                getattr(sim_cfg, "blank_false_positive_calibration_path", None)
            ),
            "blank_false_positive_calibration_id": getattr(
                sim_cfg,
                "blank_false_positive_calibration_id",
                None,
            ),
            "wavelength_lane_id": getattr(sim_cfg, "wavelength_lane_id", None),
            "medium_optical_material_key": getattr(
                sim_cfg,
                "medium_optical_material_key",
                None,
            ),
            "medium_transport_material_key": getattr(
                sim_cfg,
                "medium_transport_material_key",
                None,
            ),
            "medium_thermal_material_key": getattr(
                sim_cfg,
                "medium_thermal_material_key",
                None,
            ),
            "probe_power_by_wavelength_configured": bool(
                getattr(sim_cfg, "probe_power_by_wavelength_W", None)
            ),
            "detector_responsivity_by_wavelength_configured": bool(
                getattr(sim_cfg, "detector_responsivity_by_wavelength", None)
            ),
            "filter_transmission_by_wavelength_configured": bool(
                getattr(sim_cfg, "filter_transmission_by_wavelength", None)
            ),
            "reference_calibration_by_wavelength_configured": bool(
                getattr(sim_cfg, "reference_calibration_by_wavelength", None)
            ),
            "raw_blank_trace_path_configured": bool(
                getattr(sim_cfg, "raw_blank_trace_path", None)
            ),
            "bfp_roi_mask_path_configured": bool(
                getattr(sim_cfg, "bfp_roi_mask_path", None)
            ),
            "interface_correction_mode": getattr(
                sim_cfg,
                "interface_correction_mode",
                None,
            ),
            "thermal_pod_model": getattr(sim_cfg, "thermal_pod_model", None),
            "count_prediction_model": getattr(sim_cfg, "count_prediction_model", None),
            "na_cutoff_policy": getattr(sim_cfg, "na_cutoff_policy", None),
            "analysis_lanes": [
                "all_crossing",
                "selected_annulus",
            ],
            "selected_annulus_source": "initial_position_edge_norm_annulus",
            "selected_annulus_edge_norm_min": getattr(
                sim_cfg,
                "selected_annulus_edge_norm_min",
                None,
            ),
            "selected_annulus_edge_norm_max": getattr(
                sim_cfg,
                "selected_annulus_edge_norm_max",
                None,
            ),
            "selected_annulus_claim_level": require_claim_level(
                CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS
            ),
            "selected_annulus_paper_alignment_target": require_paper_alignment_target(
                PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
            ),
        },
        "governed_case_field_groups": {
            "selected_detector_mode": list(SELECTED_DETECTOR_MODE_DIAGNOSTIC_FIELDS),
            "reference_detector_and_calibration": [
                "reference_route",
                "reference_solver_route",
                "reference_model",
                "reference_field_decomposition",
                "detector_forward_model",
                "detector_forward_status",
                "detector_forward_claim_level",
                "field_coordinate_measure",
                "bfp_to_angle_jacobian_applied",
                "operator_route",
                "operator_normalization",
                "collection_operator_calibration_status",
                "collection_operator_coverage_status",
                "collection_operator_calibration_data_role",
                "bfp_roi_mask_source",
                "bfp_roi_mask_status",
                "bfp_roi_mask_data_role",
                "bfp_roi_mask_gate_passed",
                "absolute_throughput_route",
                "absolute_throughput_calibrated",
                "scattering_normalization_route",
                "mie_to_power_chain_status",
                "detector_field_units",
                "detector_unit_chain_status",
                "standard_particle_calibration_coverage_status",
                "standard_particle_calibration_data_role",
                "global_phase_offset_calibration_status",
                "calibration_design_rank",
                "calibration_held_out_validation_status",
                "calibration_state_machine_status",
                "output_claim_level",
            ],
            "coordinate_vector_superposition": [
                "coordinate_frame_mapping",
                "vector_optics_mode",
                "vector_validity_status",
                "polarization_jones_operator_mode",
                "polarization_overlap_efficiency",
                "phase_polarization_quantitative_claim_allowed",
                "phase_polarization_claim_blocker_summary",
                "high_NA_collection_warning",
                "superposition_validity_status",
                "channel_particle_coupling_model",
                "joint_fullwave_required_for_quantitative_phase",
                "background_field_model",
                "residual_transmitted_leakage_status",
            ],
            "detector_noise_and_units": [
                "noise_model_route",
                "detector_noise_claim_level",
                "detector_unit_chain_status",
                "incident_power_density_status",
                "photodiode_responsivity_status",
                "transimpedance_gain_status",
                "detector_dynamic_range_model",
                "detector_saturation_status",
                "lockin_ENBW_claim_level",
                "noise_terms_schema_version",
                "photon_shot_noise_term_status",
                "electronics_noise_term_status",
                "rin_noise_term_status",
                "speckle_like_noise_term_status",
                "drift_noise_term_status",
                "lockin_output_noise_term_status",
            ],
            "readout_convention": list(_READOUT_CONVENTION_FIELDS),
            "minimum_design_claim_schema": list(DESIGN_CLAIM_GOVERNANCE_FIELDS),
            "event_quality_control": list(EVENT_QC_DIAGNOSTIC_FIELDS),
            "selection_function": list(SELECTION_FUNCTION_DIAGNOSTIC_FIELDS),
            "ev_population_prior": list(EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS),
            "count_likelihood": list(COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS),
            "population_inference": list(POPULATION_INFERENCE_DIAGNOSTIC_FIELDS),
            "ood_detection": list(OOD_DIAGNOSTIC_FIELDS),
            "bayesian_calibration": list(
                BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS
            ),
            "experimental_design_advisor": list(
                EXPERIMENTAL_DESIGN_ADVISOR_FIELDS
            ),
            "objective_panel": list(OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS),
            "polarization_jones_operator": list(
                POLARIZATION_JONES_DIAGNOSTIC_FIELDS
            ),
            "nodi_thermal_contamination": list(NODI_THERMAL_CONTAMINATION_FIELDS),
            "run_state_model": list(RUN_STATE_DIAGNOSTIC_FIELDS),
            "channel_geometry": list(CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS),
            "electrokinetic_transport": list(ELECTROKINETIC_DIAGNOSTIC_FIELDS),
            "ev_integrity_risk": list(EV_INTEGRITY_DIAGNOSTIC_FIELDS),
            "ev_reporting_metadata": list(EV_REPORTING_DIAGNOSTIC_FIELDS),
            "assay_control_matrix": list(ASSAY_CONTROL_DIAGNOSTIC_FIELDS),
            "control_interpretation": list(CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS),
            "recompute_manifest": list(RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS),
            "bfp_detector_operator": list(BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS),
            "particle_channel_perturbation": list(
                PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS
            ),
            "tsuyama_bfp_reference": list(TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS),
            "reference_operating_point": list(
                REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS
            ),
            "fluidic_resistance": list(FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS),
            "fluidic_network_model": list(FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS),
            "particle_design_library": list(
                PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS
            ),
            "design_metrics": list(DESIGN_METRIC_DIAGNOSTIC_FIELDS),
            "ev_design_postprocess": list(EV_DESIGN_POSTPROCESS_FIELDS),
            "wavelength_material_governance": list(
                WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS
            ),
            "threshold_false_alarm": list(_THRESHOLD_FALSE_ALARM_FIELDS),
            "particle_material_and_uncertainty": list(_PARTICLE_MODEL_FIELDS),
            "interface_correction": list(_INTERFACE_CORRECTION_FIELDS),
            "thermal_pod": list(_PHOTOTHERMAL_POD_FIELDS),
            "count_generation": list(_COUNT_MODEL_FIELDS),
            "mie_incident_field": list(_MIE_INCIDENT_FIELD_FIELDS),
        },
        "quantitative_boundaries": {
            "output_claim_level": "case_level_calibration_state_controls_quantitative_claim",
            "pod_amplitude": "blocked_until_heat_diffusion_and_probe_calibration_exist",
            "count_rate_confidence": (
                "blocked_until_blank_false_positive_and_uncertainty_propagation_exist"
            ),
            "interface_phase_polarity": (
                "blocked_until_planar_interface_or_fullwave_route_exists"
            ),
            "standard_particle_uncertainty": (
                "must_propagate_before_quantitative_confidence"
            ),
        },
    }


def build_export_format_manifest(
    prefix: str,
    *,
    parquet_enabled: bool,
    artifact_profile: str = ARTIFACT_PROFILE_STANDARD,
) -> dict[str, Any]:
    """Describe compatibility and split export artifacts for one dataset prefix."""
    profile = _normalize_artifact_profile(artifact_profile)
    enabled_exports = _artifact_profile_enabled_exports(profile)
    parquet_status = (
        "parquet_exports_enabled"
        if parquet_enabled and "case_summary_parquet" in enabled_exports
        else "parquet_exports_skipped_missing_engine"
        if not parquet_enabled
        else "parquet_exports_skipped_by_artifact_profile"
    )
    optional_exports = {
        "case_summary_csv",
        "case_summary_parquet",
        "design_postprocess_csv",
        "physics_fields_parquet",
        "diagnostics_long_parquet",
    }
    return {
        "export_manifest_schema": "precompute_export_formats_v1",
        "artifact_profile": profile,
        "legacy_summary_csv": f"{prefix}_summary.csv",
        "legacy_compact_pkl": f"{prefix}_compact.pkl",
        "runtime_performance_json": f"{prefix}_runtime_performance.json",
        "case_summary_csv": f"{prefix}_case_summary.csv",
        "case_summary_parquet": f"{prefix}_case_summary.parquet",
        "design_postprocess_csv": f"{prefix}_design_postprocess.csv",
        "physics_fields_parquet": f"{prefix}_physics_fields.parquet",
        "diagnostics_long_parquet": f"{prefix}_diagnostics_long.parquet",
        "enabled_exports": sorted(enabled_exports),
        "skipped_optional_exports": sorted(optional_exports - enabled_exports),
        "parquet_export_status": parquet_status,
        "claim_text_fields": [
            "EV_design_claim_text",
            "EV_design_claim_allowed_text",
            "EV_design_claim_forbidden_text",
        ],
    }


def build_metadata_hashes(
    *,
    sim_cfg: Any,
    particle_types: list,
    particle_models: list[dict[str, Any]],
    project_root: str,
) -> dict[str, Any]:
    """Build P0.12 dataset provenance hashes."""
    reference_contract = {
        "reference_model": getattr(sim_cfg, "reference_model", None),
        "reference_route": getattr(sim_cfg, "reference_route", None),
        "reference_solver_route": getattr(sim_cfg, "reference_solver_route", None),
        "reference_spatial_mode": getattr(sim_cfg, "reference_spatial_mode", None),
        "reference_phase_grating_mode": getattr(
            sim_cfg,
            "reference_phase_grating_mode",
            None,
        ),
        "reference_width_saturation_mode": getattr(
            sim_cfg,
            "reference_width_saturation_mode",
            None,
        ),
        "reference_na_edge_policy": getattr(sim_cfg, "reference_na_edge_policy", None),
    }
    detector_contract = {
        "detector_forward_model": getattr(sim_cfg, "detector_forward_model", None),
        "field_coordinate_measure": getattr(sim_cfg, "field_coordinate_measure", None),
        "collection_integration_mode": getattr(
            sim_cfg,
            "collection_integration_mode",
            None,
        ),
        "bfp_to_angle_jacobian_applied": getattr(
            sim_cfg,
            "bfp_to_angle_jacobian_applied",
            None,
        ),
        "coordinate_frame_mapping": getattr(sim_cfg, "coordinate_frame_mapping", None),
    }
    particle_library_payload = {
        "particle_models": particle_models,
        "particle_types": particle_types,
        "standard_particle_presets": STANDARD_PARTICLE_PRESETS,
        "particle_contaminant_presets": PARTICLE_CONTAMINANT_PRESETS,
        "EV_sample_preparation_profiles": EV_SAMPLE_PREPARATION_PROFILES,
    }
    return {
        "model_semantic_version": "tsuyama_alignment_governed_surrogate_v1",
        "simulation_config_hash": _stable_hash(sim_cfg, prefix="simcfg"),
        "particle_library_hash": _stable_hash(
            particle_library_payload,
            prefix="particlelib",
        ),
        "material_database_hash": _stable_hash(MATERIAL_DB, prefix="materials"),
        "reference_model_hash": _stable_hash(reference_contract, prefix="refmodel"),
        "detector_operator_hash": _stable_hash(detector_contract, prefix="detectorop"),
        **_code_state_payload(project_root),
    }


def build_metadata(
    grid_name: str,
    config_tag: str,
    particle_profile: str,
    sim_cfg,
    grid: dict,
    particle_types: list,
    results: list[dict],
    *,
    artifact_profile: str = ARTIFACT_PROFILE_STANDARD,
    allow_partial_results: bool = False,
) -> dict:
    """Build metadata dict for JSON storage."""
    expected_total_cases = _count_expected_sweep_cases(particle_types, grid)
    wavelength_geometry = {}
    for wavelength_m in grid["wavelength_list_m"]:
        optical_case = deepcopy(OPTICAL_TEMPLATE)
        optical_case.wavelength_m = float(wavelength_m)
        geometry = optical_case.resolve_illumination_geometry()
        wavelength_geometry[str(int(round(float(wavelength_m) * 1e9)))] = {
            "illumination_effective_beam_waist_x_nm": round(
                float(geometry["illumination_beam_waist_x_m"]) * 1e9
            ),
            "illumination_effective_beam_waist_y_nm": round(
                float(geometry["illumination_beam_waist_y_m"]) * 1e9
            ),
            "illumination_effective_beam_waist_z_nm": round(
                float(geometry["illumination_beam_waist_z_m"]) * 1e9
            ),
            "illumination_beam_geometry_source": geometry["illumination_geometry_source"],
        }
    metadata = PrecomputeMetadata(
        dashboard_schema_version="1.24",
        model_semantics_version="tsuyama_alignment_governed_surrogate_v1",
        result_library_role="paper_aligned_governed_engineering_surrogate",
        result_library_status="schema_1_24_requires_regenerated_results",
        legacy_current_code_library_compatible=False,
        schema_migration_note=(
            "Old current-code result libraries must not be interpreted as "
            "schema 1.24 Tsuyama-aligned wavelength/material governed outputs."
        ),
        config_tag=config_tag,
        grid=grid_name,
        particle_profile=particle_profile,
        timestamp=datetime.now().isoformat(timespec="seconds"),
        n_cases=len(results),
        n_events_per_case=grid["n_events"],
        sim_cfg=asdict(sim_cfg),
        particle_types=[p.name for p in particle_types],
        wavelengths_nm=[round(w * 1e9) for w in grid["wavelength_list_m"]],
        optical={
            "beam_waist_x_nm": round(OPTICAL_TEMPLATE.beam_waist_x_m * 1e9),
            "beam_waist_y_nm": round(OPTICAL_TEMPLATE.beam_waist_y_m * 1e9),
            "beam_waist_z_nm": round(OPTICAL_TEMPLATE.beam_waist_z_m * 1e9),
            "illumination_NA": OPTICAL_TEMPLATE.illumination_NA,
            "collection_theta_rad": OPTICAL_TEMPLATE.collection_theta_rad,
            "NA_collection": OPTICAL_TEMPLATE.NA_collection,
            "illumination_effective_beam_waists_by_wavelength_nm": wavelength_geometry,
        },
    ).to_payload()
    metadata["sweep_completion_policy"] = _build_sweep_completion_policy(
        expected_total_cases=expected_total_cases,
        saved_case_count=len(results),
        allow_partial_results=allow_partial_results,
    )
    particle_models = build_particle_model_catalog(particle_types, sim_cfg=sim_cfg)
    metadata["particle_models"] = particle_models
    metadata["reference_calibration_health"] = build_reference_calibration_health(
        results,
        sim_cfg,
    )
    metadata["collection_operator_calibration_health"] = (
        build_collection_operator_calibration_health(
            results,
            sim_cfg,
        )
    )
    metadata["schema_feature_inventory"] = build_schema_feature_inventory(sim_cfg)
    metadata["analysis_lanes"] = {
        "all_crossing": {
            "role": "engineering_gate_and_primary_score",
            "rate_field": "detection_rate",
            "cross_check_alias": "all_crossing_detection_rate",
        },
        "selected_annulus": {
            "role": "paper_alignment_cross_check_lens",
            "source": "initial_position_edge_norm_annulus",
            "edge_norm_min": float(sim_cfg.selected_annulus_edge_norm_min),
            "edge_norm_max": float(sim_cfg.selected_annulus_edge_norm_max),
            "rate_field": "selected_detector_mode_annulus_detection_rate",
            "fraction_field": "selected_detector_mode_annulus_fraction",
            "claim_level": require_claim_level(
                CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS
            ),
            "paper_alignment_target": require_paper_alignment_target(
                PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
            ),
            "does_not_replace_engineering_gate": True,
        },
    }
    metadata.update(
        build_metadata_hashes(
            sim_cfg=sim_cfg,
            particle_types=particle_types,
            particle_models=particle_models,
            project_root=PROJECT_ROOT,
        )
    )
    metadata["export_format_manifest"] = build_export_format_manifest(
        f"{grid_name}_{config_tag}",
        parquet_enabled=_parquet_engine_available(),
        artifact_profile=artifact_profile,
    )
    return metadata


def _build_status_distribution(values: list[object]) -> dict[str, dict[str, float | int]]:
    cleaned = []
    for value in values:
        if value is None:
            cleaned.append("missing")
            continue
        text = str(value)
        cleaned.append(text if text and text.lower() != "nan" else "missing")
    total = max(len(cleaned), 1)
    return {
        key: {
            "count": int(count),
            "fraction": float(count / total),
        }
        for key, count in Counter(cleaned).most_common()
    }


def _build_status_distributions_for_fields(
    frame: pd.DataFrame,
    fields: tuple[str, ...],
) -> dict[str, dict[str, dict[str, float | int]]]:
    return {
        field: _build_status_distribution(
            frame.get(field, pd.Series(dtype=object)).tolist()
        )
        for field in fields
    }


def _case_report_value(result: Mapping[str, Any], field: str) -> Any:
    for section_name in ("summary", "intrinsic", "reference", "physics"):
        section = result.get(section_name, {})
        if isinstance(section, Mapping) and field in section:
            return section[field]
    return result.get(field)


def _status_text_series(
    frame: pd.DataFrame,
    field: str,
    *,
    default: str = "",
) -> pd.Series:
    series = frame.get(
        field,
        pd.Series([default] * len(frame), index=frame.index, dtype=object),
    )
    return series.fillna(default).astype(str)


def _is_truthy_status_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _truthy_status_series(frame: pd.DataFrame, field: str) -> pd.Series:
    series = frame.get(
        field,
        pd.Series([False] * len(frame), index=frame.index, dtype=object),
    ).fillna(False)
    return series.map(_is_truthy_status_value)


def _split_engineering_gate_reason_tokens(reason: object) -> list[str]:
    if reason is None:
        return []
    text = str(reason).strip()
    if not text or text == "PASS":
        return []
    return [token.strip() for token in text.split("/") if token.strip()]


def _engineering_gate_token_category(token: str) -> str:
    text = str(token)
    if text.startswith("n_detected<"):
        return "n_detected"
    if "detection_rate<" in text and "stable_detection_rate" not in text:
        return "detection_rate"
    if "stable_detection_rate<" in text:
        return "stable_detection_rate"
    if "phase_flip_fraction>" in text:
        return "phase_flip_fraction"
    if "mean_peak_margin_z<" in text:
        return "mean_peak_margin_z"
    if "strict_paired_detection_rate<" in text:
        return "strict_paired_detection_rate"
    return "other"


def _ensure_recommendation_columns(summary_df: pd.DataFrame) -> pd.DataFrame:
    """Backfill recommendation columns when a legacy summary lacks them."""
    df = summary_df.copy()
    required = {
        "design_recommendation_status",
        "design_recommendation_label",
        "design_recommendation_rank",
        "design_recommendation_guidance",
    }
    if required.issubset(df.columns) or "observation_freeze_status" not in df.columns:
        return df

    recommendations = df.apply(
        lambda row: classify_design_recommendation(
            engineering_gate_passed=bool(row.get("engineering_gate_passed", False)),
            observation_freeze_status=str(
                row.get(
                    "observation_freeze_status",
                    "review_required_before_result_freeze",
                )
            ),
        ),
        axis=1,
        result_type="expand",
    )
    for col in recommendations.columns:
        df[col] = recommendations[col]
    return df


def build_engineering_gate_calibration_report(
    summary_df: pd.DataFrame,
    *,
    top_k: int = 10,
) -> dict:
    """
    Build a structured calibration report for the current engineering gate.

    The report is intentionally conservative:
      - it treats the current gate decisions as the frozen baseline
      - candidate variants only relax the stable-rate and/or phase-flip rules
      - a variant is only considered healthy if it adds cases with mostly
        `default_ready_for_result_freeze` status and non-negative median
        `final_engineering_score`
    """
    if summary_df.empty:
        return {
            "n_cases": 0,
            "current_gate": {},
            "candidate_variants": [],
            "recommended_default_variant": "current_default",
            "recommended_default_guidance": (
                "没有可用 case；保持 current_default。"
            ),
        }

    df = summary_df.copy()
    current_pass = df["engineering_gate_passed"].fillna(False).astype(bool)
    reasons = df["engineering_gate_reason"].fillna("")
    tokens_per_case = [_split_engineering_gate_reason_tokens(reason) for reason in reasons]

    blocker_labels: list[str] = []
    for idx, reason in enumerate(reasons):
        label = df.get("engineering_gate_primary_blocker_label")
        if label is not None and pd.notna(label.iloc[idx]):
            blocker_labels.append(str(label.iloc[idx]))
            continue
        gate_explanation = classify_engineering_gate_explanation(
            engineering_gate_passed=bool(current_pass.iloc[idx]),
            engineering_gate_reason=str(reason),
            engineering_gate_failed_count=int(
                df.get("engineering_gate_failed_count", pd.Series([0] * len(df))).iloc[idx]
            ),
        )
        blocker_labels.append(str(gate_explanation["engineering_gate_primary_blocker_label"]))
    df["_engineering_gate_tokens"] = tokens_per_case
    df["_engineering_gate_primary_blocker_label"] = blocker_labels

    failure_label_counter: Counter[str] = Counter()
    failed_df = df.loc[~current_pass].copy()
    failure_label_counter.update(
        str(label) for label in failed_df["_engineering_gate_primary_blocker_label"].tolist()
    )

    candidate_variants = [
        {
            "name": "current_default",
            "engineering_min_stable_detection_rate": 0.20,
            "engineering_max_phase_flip_fraction": 0.50,
        },
        {
            "name": "relax_phase_flip_to_0.55",
            "engineering_min_stable_detection_rate": 0.20,
            "engineering_max_phase_flip_fraction": 0.55,
        },
        {
            "name": "relax_stable_rate_to_0.15",
            "engineering_min_stable_detection_rate": 0.15,
            "engineering_max_phase_flip_fraction": 0.50,
        },
        {
            "name": "relax_phase_flip_and_stable_rate",
            "engineering_min_stable_detection_rate": 0.15,
            "engineering_max_phase_flip_fraction": 0.55,
        },
    ]

    variant_reports: list[dict[str, object]] = []
    recommended_variant = "current_default"
    recommended_guidance = (
        "当前默认门槛先冻结不动；新增放行需要同时提高 ready 占比，并避免把"
        " 负 `final_engineering_score` 集合整体抬入通过集。"
    )

    for variant in candidate_variants:
        variant_name = str(variant["name"])
        stable_floor = float(variant["engineering_min_stable_detection_rate"])
        phase_cap = float(variant["engineering_max_phase_flip_fraction"])
        variant_pass = current_pass.copy()

        for idx, row in df.loc[~current_pass].to_dict("index").items():
            unresolved: list[str] = []
            for token in row["_engineering_gate_tokens"]:
                token_category = _engineering_gate_token_category(token)
                if token_category == "stable_detection_rate":  # nosec B105
                    stable_lb = float(row.get("engineering_gate_stable_detection_rate_lb", np.nan))
                    if np.isfinite(stable_lb) and stable_lb >= stable_floor:
                        continue
                elif token_category == "phase_flip_fraction":  # nosec B105
                    phase_ub = float(row.get("engineering_gate_phase_flip_fraction_ub", np.nan))
                    if np.isfinite(phase_ub) and phase_ub <= phase_cap:
                        continue
                unresolved.append(token)
            if not unresolved:
                variant_pass.at[idx] = True

        promoted = variant_pass & ~current_pass
        promoted_df = df.loc[promoted].copy()
        promoted_ready = int(
            (promoted_df["observation_freeze_status"] == "default_ready_for_result_freeze").sum()
        )
        promoted_caution = int(
            (promoted_df["observation_freeze_status"] != "default_ready_for_result_freeze").sum()
        )
        promoted_total = int(promoted.sum())
        promoted_caution_fraction = (
            float(promoted_caution / promoted_total) if promoted_total > 0 else 0.0
        )
        promoted_median_final_score = (
            float(promoted_df["final_engineering_score"].median())
            if promoted_total > 0
            else 0.0
        )

        promoted_blockers = Counter(promoted_df["_engineering_gate_primary_blocker_label"].tolist())
        if variant_name == "current_default":
            promotion_status = "frozen_default"
            promotion_guidance = "当前默认门槛。"
        elif promoted_total == 0:
            promotion_status = "no_effect"
            promotion_guidance = "放宽后没有新增通过 case，不值得调整默认门槛。"
        elif promoted_median_final_score < 0.0:
            promotion_status = "reject_negative_score"
            promotion_guidance = (
                "新增放行 case 的 `final_engineering_score` 中位数仍为负，"
                " 不建议提升为默认门槛。"
            )
        elif promoted_caution_fraction > 0.5:
            promotion_status = "reject_caution_heavy"
            promotion_guidance = (
                "新增放行 case 里 `caution_probe_before_result_freeze` 占多数，"
                " 不建议提升为默认门槛。"
            )
        else:
            promotion_status = "candidate_for_review"
            promotion_guidance = (
                "新增放行 case 质量尚可，可作为后续人工复核候选。"
            )
            if recommended_variant == "current_default":
                recommended_variant = variant_name
                recommended_guidance = promotion_guidance

        variant_reports.append(
            {
                "name": variant_name,
                "engineering_min_stable_detection_rate": stable_floor,
                "engineering_max_phase_flip_fraction": phase_cap,
                "passed_cases": int(variant_pass.sum()),
                "promoted_cases": promoted_total,
                "promoted_ready_cases": promoted_ready,
                "promoted_caution_cases": promoted_caution,
                "promoted_primary_blockers": [
                    {"label": str(label), "count": int(count)}
                    for label, count in promoted_blockers.most_common(5)
                ],
                "promotion_status": promotion_status,
                "promotion_guidance": promotion_guidance,
            }
        )

    return {
        "n_cases": int(len(df)),
        "current_gate": {
            "passed_cases": int(current_pass.sum()),
            "failed_cases": int((~current_pass).sum()),
            "passed_ready_cases": int(
                (current_pass & (df["observation_freeze_status"] == "default_ready_for_result_freeze")).sum()
            ),
            "passed_caution_cases": int(
                (current_pass & (df["observation_freeze_status"] != "default_ready_for_result_freeze")).sum()
            ),
        },
        "failure_primary_blockers": [
            {"label": str(label), "count": int(count)}
            for label, count in failure_label_counter.most_common()
        ],
        "candidate_variants": variant_reports,
        "recommended_default_variant": recommended_variant,
        "recommended_default_guidance": recommended_guidance,
    }


def build_result_health_report(
    summary_df: pd.DataFrame,
    *,
    top_k: int = 10,
) -> dict:
    """
    Build a dataset-level monitoring report for the frozen default result set.

    This report is intentionally diagnostic rather than prescriptive: it turns
    the remaining non-blocking watch items into explicit JSON so they can be
    reviewed without reopening the full calibration / freeze notebooks.
    """
    if summary_df.empty:
        return ResultHealthReportPayload(
            n_cases=0,
            status_distributions={},
            recommendation_distribution={},
            engineering_gate_distribution={},
            health_slices={
                "by_wavelength_nm": [],
                "by_particle_material": [],
            },
            monitoring_summary={
                "default_ready_fraction": 0.0,
                "shared_beam_caution_fraction": 0.0,
                "rho_out_of_envelope_count": 0,
                "count_prediction_active_count": 0,
                "count_confidence_unavailable_count": 0,
                "crossing_conditioned_transport_unimplemented_count": 0,
                "detector_forward_surrogate_count": 0,
                "unimplemented_mie_to_power_chain_count": 0,
                "held_out_calibration_unavailable_count": 0,
                "interface_fullwave_required_count": 0,
                "thermal_pod_blocked_count": 0,
                "narrower_width_has_stronger_saturation_factor": False,
            },
            monitoring_guidance="没有可用 case；暂无健康度监控结论。",
            top_caution_cases=[],
        ).to_payload()

    df = _ensure_recommendation_columns(summary_df)
    if "particle_material" not in df.columns and "particle_name" in df.columns:
        df["particle_material"] = df["particle_name"].map(infer_particle_material)

    def _build_health_slice(
        frame: pd.DataFrame,
        group_col: str,
    ) -> list[dict[str, object]]:
        if group_col not in frame.columns:
            return []
        rows: list[dict[str, object]] = []
        for group_value, group in frame.groupby(group_col, sort=True):
            observation_group = group.get(
                "observation_freeze_status",
                pd.Series(dtype=object),
            ).fillna("")
            gouy_group = group.get(
                "delta_phi_gouy_validity",
                pd.Series(dtype=object),
            ).fillna("")
            gate_group = group.get(
                "engineering_gate_passed",
                pd.Series(dtype=bool),
            ).fillna(False).astype(bool)
            count_prediction_group = group.get(
                "count_prediction_status",
                pd.Series([""] * len(group), index=group.index, dtype=object),
            ).fillna("")
            count_confidence_group = group.get(
                "count_rate_confidence_status",
                pd.Series([""] * len(group), index=group.index, dtype=object),
            ).fillna("")
            interface_fullwave_group = _truthy_status_series(
                group,
                "interface_fullwave_required",
            )
            pod_route_group = _status_text_series(group, "pod_quantitative_route_status")
            pod_model_group = _status_text_series(group, "thermal_pod_model_status")
            mie_to_power_group = _status_text_series(group, "mie_to_power_chain_status")
            rows.append(
                {
                    group_col: (
                        float(group_value)
                        if isinstance(group_value, (int, float, np.integer, np.floating))
                        else str(group_value)
                    ),
                    "n_cases": int(len(group)),
                    "default_ready_fraction": float(
                        (observation_group == "default_ready_for_result_freeze").mean()
                    ),
                    "shared_beam_caution_fraction": float(
                        (gouy_group == "shared_beam_caution").mean()
                    ),
                    "engineering_gate_pass_fraction": float(gate_group.mean()),
                    "count_prediction_active_fraction": float(
                        (
                            count_prediction_group
                            == "poisson_flux_deadtime_surrogate_active"
                        ).mean()
                    ),
                    "count_confidence_unavailable_fraction": float(
                        (
                            count_confidence_group
                            == "not_available_no_blank_false_positive_or_uncertainty_propagation"
                        ).mean()
                    ),
                    "interface_fullwave_required_fraction": float(
                        interface_fullwave_group.mean()
                    ),
                    "thermal_pod_blocked_fraction": float(
                        (
                            pod_route_group.str.startswith("blocked")
                            | pod_model_group.str.startswith("unavailable")
                        ).mean()
                    ),
                    "unimplemented_mie_to_power_chain_fraction": float(
                        mie_to_power_group.str.startswith("not_implemented").mean()
                    ),
                }
            )
        return rows

    status_distributions = _build_status_distributions_for_fields(
        df,
        _RESULT_HEALTH_STATUS_FIELDS,
    )

    recommendation_distribution = _build_status_distribution(
        df.get("design_recommendation_label", pd.Series(dtype=object)).tolist()
    )
    engineering_gate_distribution = {
        "passed": int(df.get("engineering_gate_passed", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()),
        "failed": int((~df.get("engineering_gate_passed", pd.Series(dtype=bool)).fillna(False).astype(bool)).sum()),
    }
    health_slices = {
        "by_wavelength_nm": _build_health_slice(df, "wavelength_nm"),
        "by_particle_material": _build_health_slice(df, "particle_material"),
    }

    width_saturation_by_width: list[dict[str, object]] = []
    if {"width_nm", "reference_width_saturation_factor"}.issubset(df.columns):
        for width_nm, group in df.groupby("width_nm", sort=True):
            width_saturation_by_width.append(
                {
                    "width_nm": float(width_nm),
                    "n_cases": int(len(group)),
                    "mean_reference_width_saturation_factor": float(
                        group["reference_width_saturation_factor"].fillna(1.0).mean()
                    ),
                }
            )

    narrowest_factor = None
    widest_factor = None
    stronger_for_narrower = False
    if width_saturation_by_width:
        narrowest = width_saturation_by_width[0]
        widest = width_saturation_by_width[-1]
        narrowest_factor = narrowest["mean_reference_width_saturation_factor"]
        widest_factor = widest["mean_reference_width_saturation_factor"]
        stronger_for_narrower = bool(narrowest_factor >= widest_factor - 1e-12)

    observation_series = df.get("observation_freeze_status", pd.Series(dtype=object)).fillna("")
    gouy_series = df.get("delta_phi_gouy_validity", pd.Series(dtype=object)).fillna("")
    rho_series = df.get("rho_physical_envelope_status", pd.Series(dtype=object)).fillna("")
    count_prediction_series = df.get(
        "count_prediction_status",
        pd.Series(dtype=object),
    ).fillna("")
    count_confidence_series = df.get(
        "count_rate_confidence_status",
        pd.Series(dtype=object),
    ).fillna("")
    crossing_transport_series = df.get(
        "crossing_conditioned_transport_status",
        pd.Series(dtype=object),
    ).fillna("")
    detector_forward_model_series = _status_text_series(df, "detector_forward_model")
    detector_forward_status_series = _status_text_series(df, "detector_forward_status")
    mie_to_power_series = _status_text_series(df, "mie_to_power_chain_status")
    held_out_calibration_series = _status_text_series(
        df,
        "calibration_held_out_validation_status",
    )
    interface_fullwave_series = _truthy_status_series(
        df,
        "interface_fullwave_required",
    )
    pod_route_series = _status_text_series(df, "pod_quantitative_route_status")
    pod_model_series = _status_text_series(df, "thermal_pod_model_status")

    default_ready_fraction = float(
        (observation_series == "default_ready_for_result_freeze").mean()
    )
    shared_beam_caution_fraction = float(
        (gouy_series == "shared_beam_caution").mean()
    )
    rho_out_of_envelope_count = int((rho_series != "within_envelope").sum())
    count_prediction_active_count = int(
        (count_prediction_series == "poisson_flux_deadtime_surrogate_active").sum()
    )
    count_confidence_unavailable_count = int(
        (
            count_confidence_series
            == "not_available_no_blank_false_positive_or_uncertainty_propagation"
        ).sum()
    )
    crossing_conditioned_transport_unimplemented_count = int(
        crossing_transport_series.str.startswith("not_implemented").sum()
    )
    detector_forward_surrogate_count = int(
        (
            detector_forward_model_series.str.contains("surrogate", regex=False)
            | detector_forward_status_series.str.contains("surrogate", regex=False)
        ).sum()
    )
    unimplemented_mie_to_power_chain_count = int(
        mie_to_power_series.str.startswith("not_implemented").sum()
    )
    held_out_calibration_unavailable_count = int(
        held_out_calibration_series.str.startswith("not_available").sum()
    )
    interface_fullwave_required_count = int(interface_fullwave_series.sum())
    thermal_pod_blocked_count = int(
        (
            pod_route_series.str.startswith("blocked")
            | pod_model_series.str.startswith("unavailable")
        ).sum()
    )

    if rho_out_of_envelope_count > 0:
        monitoring_guidance = (
            "当前仍有 case 落在 rho 物理包络外，建议先复核 reference 量级，再考虑扩大结果解释范围。"
        )
    elif not stronger_for_narrower and width_saturation_by_width:
        monitoring_guidance = (
            "窄通道 width-saturation 因子没有表现出更保守趋势，建议把它继续视为监控项而不是硬门槛。"
        )
    elif shared_beam_caution_fraction > 0.0:
        monitoring_guidance = (
            "当前默认结果库可继续使用，但仍应持续监控 shared-beam Gouy caution 区域。"
        )
    else:
        monitoring_guidance = (
            "当前默认结果库的主要监控项都处于稳定区间，可继续沿用 current_default。"
        )

    caution_df = df.loc[
        observation_series == "caution_probe_before_result_freeze"
    ].copy()
    sort_cols = [
        col
        for col in ["final_engineering_score", "score"]
        if col in caution_df.columns
    ]
    if sort_cols:
        caution_df = caution_df.sort_values(sort_cols, ascending=[False] * len(sort_cols))
    top_caution_cases = [
        {
            "particle_name": str(row.get("particle_name", "")),
            "observation_freeze_status": str(row.get("observation_freeze_status", "")),
            "final_engineering_score": float(row.get("final_engineering_score", 0.0) or 0.0),
        }
        for row in caution_df.head(max(int(top_k), 1)).to_dict("records")
    ]

    return ResultHealthReportPayload(
        n_cases=int(len(df)),
        status_distributions=status_distributions,
        recommendation_distribution=recommendation_distribution,
        engineering_gate_distribution=engineering_gate_distribution,
        health_slices=health_slices,
        monitoring_summary={
            "default_ready_fraction": default_ready_fraction,
            "shared_beam_caution_fraction": shared_beam_caution_fraction,
            "rho_out_of_envelope_count": rho_out_of_envelope_count,
            "count_prediction_active_count": count_prediction_active_count,
            "count_confidence_unavailable_count": count_confidence_unavailable_count,
            "crossing_conditioned_transport_unimplemented_count": (
                crossing_conditioned_transport_unimplemented_count
            ),
            "detector_forward_surrogate_count": detector_forward_surrogate_count,
            "unimplemented_mie_to_power_chain_count": (
                unimplemented_mie_to_power_chain_count
            ),
            "held_out_calibration_unavailable_count": (
                held_out_calibration_unavailable_count
            ),
            "interface_fullwave_required_count": interface_fullwave_required_count,
            "thermal_pod_blocked_count": thermal_pod_blocked_count,
            "narrower_width_has_stronger_saturation_factor": stronger_for_narrower,
        },
        monitoring_guidance=monitoring_guidance,
        top_caution_cases=top_caution_cases,
    ).to_payload()


def _finite_runtime_values(values: list[object]) -> list[float]:
    """Return positive finite floats for runtime summaries."""
    out: list[float] = []
    for value in values:
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number) and number >= 0.0:
            out.append(number)
    return out


def _numeric_runtime_summary(values: list[object]) -> dict[str, Any]:
    """Build compact percentile stats for a runtime vector."""
    cleaned = _finite_runtime_values(values)
    if not cleaned:
        return {
            "count": 0,
            "min": None,
            "median": None,
            "mean": None,
            "p90": None,
            "p95": None,
            "max": None,
        }
    arr = np.asarray(cleaned, dtype=float)
    return {
        "count": int(arr.size),
        "min": float(np.min(arr)),
        "median": float(np.median(arr)),
        "mean": float(np.mean(arr)),
        "p90": float(np.percentile(arr, 90)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(np.max(arr)),
    }


def _runtime_status_distribution(values: list[object]) -> dict[str, int]:
    """Return a plain count distribution for runtime routing labels."""
    labels = ["missing" if value is None else str(value) for value in values]
    return dict(sorted(Counter(labels).items()))


def _runtime_group_summary(
    df: pd.DataFrame,
    group_cols: list[str],
    *,
    top_k: int = 12,
) -> list[dict[str, Any]]:
    """Summarize case runtime by one or more grouping columns."""
    if df.empty or "case_runtime_seconds" not in df.columns:
        return []
    if not set(group_cols).issubset(df.columns):
        return []
    rows: list[dict[str, Any]] = []
    for group_value, group in df.groupby(group_cols, dropna=False, sort=True):
        runtime = _numeric_runtime_summary(group["case_runtime_seconds"].tolist())
        events = float(group.get("n_events", pd.Series(dtype=float)).fillna(0).sum())
        seconds = float(group["case_runtime_seconds"].fillna(0.0).sum())
        row: dict[str, Any] = {
            "n_cases": int(len(group)),
            "total_case_runtime_seconds": seconds,
            "total_events": int(events),
            "events_per_case_runtime_second": (
                float(events / seconds) if seconds > 0.0 else None
            ),
            "case_runtime_seconds": runtime,
        }
        values = group_value if isinstance(group_value, tuple) else (group_value,)
        for col, value in zip(group_cols, values):
            row[col] = (
                float(value)
                if isinstance(value, (int, float, np.integer, np.floating))
                and math.isfinite(float(value))
                else str(value)
            )
        rows.append(row)
    rows.sort(
        key=lambda item: float(item["case_runtime_seconds"].get("mean") or 0.0),
        reverse=True,
    )
    return rows[: max(1, int(top_k))]


def build_runtime_performance_report(
    results: list[dict],
    *,
    run_context: PrecomputeRunContext,
    job_state: PrecomputeJobState,
    wall_elapsed_seconds: float,
) -> dict[str, Any]:
    """
    Build a low-overhead runtime report for post-full-recompute optimization.

    The report intentionally stores aggregate timings and the slowest case
    identities, not event traces, so it is cheap enough to keep enabled during
    formal full-grid recomputes.
    """
    rows: list[dict[str, Any]] = []
    for result in results:
        summary = result.get("summary", {})
        runtime_seconds = result.get("case_runtime_seconds")
        n_events = int(summary.get("n_events", 0) or 0)
        runtime = (
            float(runtime_seconds)
            if runtime_seconds is not None and math.isfinite(float(runtime_seconds))
            else None
        )
        rows.append(
            {
                **_build_result_coordinate_payload(result),
                "n_events": n_events,
                "case_runtime_seconds": runtime,
                "case_events_per_second": (
                    float(n_events / runtime)
                    if runtime is not None and runtime > 0.0
                    else None
                ),
                "vectorized_event_engine": summary.get("vectorized_event_engine"),
                "vectorized_event_engine_used": summary.get(
                    "vectorized_event_engine_used"
                ),
                "vectorized_event_engine_fallback_reason": summary.get(
                    "vectorized_event_engine_fallback_reason"
                ),
                "event_block_rng_order": summary.get("event_block_rng_order"),
                "event_sampling_policy": summary.get("event_sampling_policy"),
                "adaptive_event_budget_stopped_early": summary.get(
                    "adaptive_event_budget_stopped_early"
                ),
                "adaptive_event_budget_actual_events": summary.get(
                    "adaptive_event_budget_actual_events"
                ),
            }
        )
    df = pd.DataFrame(rows)
    case_runtime_values = (
        df["case_runtime_seconds"].tolist() if "case_runtime_seconds" in df else []
    )
    case_runtime_total = float(sum(_finite_runtime_values(case_runtime_values)))
    total_events = int(df["n_events"].fillna(0).sum()) if "n_events" in df else 0
    sweep_elapsed = float(job_state.sweep_elapsed_seconds or 0.0)
    save_elapsed = float(
        sum(float(item.get("duration_seconds", 0.0) or 0.0) for item in job_state.save_stage_records)
    )
    checkpoint_elapsed = float(
        sum(
            float(item.get("duration_seconds", 0.0) or 0.0)
            for item in job_state.checkpoint_flush_records
        )
    )
    slowest_cases = []
    if not df.empty and "case_runtime_seconds" in df.columns:
        slowest_df = df.sort_values("case_runtime_seconds", ascending=False).head(20)
        for row in slowest_df.to_dict("records"):
            slowest_cases.append(
                {
                    "particle_name": str(row.get("particle_name", "")),
                    "particle_material": str(row.get("particle_material", "")),
                    "particle_diameter_nm": row.get("particle_diameter_nm"),
                    "wavelength_nm": row.get("wavelength_nm"),
                    "width_nm": row.get("width_nm"),
                    "depth_nm": row.get("depth_nm"),
                    "n_events": int(row.get("n_events", 0) or 0),
                    "case_runtime_seconds": (
                        float(row["case_runtime_seconds"])
                        if pd.notna(row.get("case_runtime_seconds"))
                        else None
                    ),
                    "case_events_per_second": (
                        float(row["case_events_per_second"])
                        if pd.notna(row.get("case_events_per_second"))
                        else None
                    ),
                    "vectorized_event_engine_used": row.get(
                        "vectorized_event_engine_used"
                    ),
                    "vectorized_event_engine_fallback_reason": row.get(
                        "vectorized_event_engine_fallback_reason"
                    ),
                }
            )

    fallback_telemetry = summarize_vectorized_fallback_telemetry(results)
    fallback_count = int(fallback_telemetry["vectorized_fallback_case_count"])
    report = {
        "runtime_performance_schema": "precompute_runtime_performance_v1",
        "monitoring_intent": (
            "Use this file after full recompute to decide whether the next "
            "optimization target is event loop, worker scheduling, checkpoint I/O, "
            "artifact export, or case-family physics/reference cost."
        ),
        "run": {
            "grid": run_context.grid_name,
            "particle_profile": run_context.particle_profile,
            "config_tag": run_context.config_tag,
            "worker_count": int(run_context.worker_count),
            "artifact_profile": run_context.artifact_profile,
            "checkpoint_enabled": bool(run_context.checkpoint_enabled),
            "resume_enabled": bool(run_context.resume_enabled),
            "total_cases": int(run_context.total_cases),
            "saved_cases": int(len(results)),
            "events_per_case_config": int(run_context.grid["n_events"]),
            "total_events_observed": total_events,
        },
        "throughput": {
            "wall_elapsed_seconds": float(wall_elapsed_seconds),
            "sweep_elapsed_seconds": sweep_elapsed,
            "save_elapsed_seconds": save_elapsed,
            "checkpoint_flush_elapsed_seconds": checkpoint_elapsed,
            "case_runtime_sum_seconds": case_runtime_total,
            "wall_cases_per_second": (
                float(len(results) / wall_elapsed_seconds)
                if wall_elapsed_seconds > 0.0
                else None
            ),
            "sweep_cases_per_second": (
                float(len(results) / sweep_elapsed) if sweep_elapsed > 0.0 else None
            ),
            "wall_events_per_second": (
                float(total_events / wall_elapsed_seconds)
                if wall_elapsed_seconds > 0.0
                else None
            ),
            "sweep_events_per_second": (
                float(total_events / sweep_elapsed) if sweep_elapsed > 0.0 else None
            ),
            "case_runtime_parallel_efficiency_proxy": (
                float(case_runtime_total / (sweep_elapsed * run_context.worker_count))
                if sweep_elapsed > 0.0 and run_context.worker_count > 0
                else None
            ),
        },
        "case_runtime_seconds": _numeric_runtime_summary(case_runtime_values),
        "case_events_per_second": _numeric_runtime_summary(
            df["case_events_per_second"].tolist()
            if "case_events_per_second" in df
            else []
        ),
        "routing_distributions": {
            "vectorized_event_engine": _runtime_status_distribution(
                df.get("vectorized_event_engine", pd.Series(dtype=object)).tolist()
            ),
            "vectorized_event_engine_used": _runtime_status_distribution(
                df.get("vectorized_event_engine_used", pd.Series(dtype=object)).tolist()
            ),
            "vectorized_event_engine_fallback_reason": _runtime_status_distribution(
                df.get(
                    "vectorized_event_engine_fallback_reason",
                    pd.Series(dtype=object),
                ).tolist()
            ),
            "event_sampling_policy": _runtime_status_distribution(
                df.get("event_sampling_policy", pd.Series(dtype=object)).tolist()
            ),
        },
        "vectorized_fallback_telemetry": fallback_telemetry,
        "slowest_cases": slowest_cases,
        "slowest_groups": {
            "by_particle_material": _runtime_group_summary(df, ["particle_material"]),
            "by_wavelength_nm": _runtime_group_summary(df, ["wavelength_nm"]),
            "by_particle_material_and_wavelength_nm": _runtime_group_summary(
                df,
                ["particle_material", "wavelength_nm"],
            ),
            "by_geometry_nm": _runtime_group_summary(df, ["width_nm", "depth_nm"]),
        },
        "checkpoint_flushes": {
            "count": int(len(job_state.checkpoint_flush_records)),
            "records": list(job_state.checkpoint_flush_records[-20:]),
            "duration_seconds": _numeric_runtime_summary(
                [
                    item.get("duration_seconds")
                    for item in job_state.checkpoint_flush_records
                ]
            ),
        },
        "save_stages": {
            "count": int(len(job_state.save_stage_records)),
            "records": list(job_state.save_stage_records),
            "duration_seconds": _numeric_runtime_summary(
                [item.get("duration_seconds") for item in job_state.save_stage_records]
            ),
        },
        "optimization_watch_items": {
            "event_loop_fallback_count": fallback_count,
            "event_loop_fallback_fraction_of_vectorized_requested_cases": (
                fallback_telemetry[
                    "vectorized_fallback_fraction_of_requested_cases"
                ]
            ),
            "checkpoint_share_of_sweep_time": (
                float(checkpoint_elapsed / sweep_elapsed) if sweep_elapsed > 0.0 else None
            ),
            "save_share_of_wall_time": (
                float(save_elapsed / wall_elapsed_seconds)
                if wall_elapsed_seconds > 0.0
                else None
            ),
            "slow_case_p95_to_median_ratio": (
                float(
                    (_numeric_runtime_summary(case_runtime_values)["p95"] or 0.0)
                    / (_numeric_runtime_summary(case_runtime_values)["median"] or 1.0)
                )
                if _numeric_runtime_summary(case_runtime_values)["median"]
                else None
            ),
        },
    }
    return report


def build_freeze_probe_report(
    results: list[dict],
    *,
    top_k: int = 10,
) -> dict:
    """
    Build a compact sanity report for the current freeze-judgement mainline.

    Intended use:
      - run on `coarse + quick` before any expensive full-range recompute
      - confirm freeze diagnostics do not collapse into large-scale caution /
        review-required regions
    """
    rows: list[dict[str, object]] = []
    for result in results:
        summary = result.get("summary", {})
        row: dict[str, object] = {
            "particle_name": result.get("particle_name"),
            "wavelength_nm": round(float(result.get("wavelength_m", 0.0)) * 1e9),
            "width_nm": round(float(result.get("width_m", 0.0)) * 1e9),
            "depth_nm": round(float(result.get("depth_m", 0.0)) * 1e9),
            "score": float(result.get("score", 0.0) or 0.0),
            "final_engineering_score": float(
                result.get(
                    "final_engineering_score",
                    result.get("engineering_score", 0.0),
                )
                or 0.0
            ),
            "path_opd_freeze_status": summary.get("path_opd_freeze_status"),
            "interference_overlap_default_freeze_status": summary.get(
                "interference_overlap_default_freeze_status"
            ),
            "projection_default_freeze_status": summary.get(
                "projection_default_freeze_status"
            ),
            "delta_phi_gouy_validity": summary.get("delta_phi_gouy_validity"),
            "observation_freeze_status": summary.get("observation_freeze_status"),
            "rho_physical_envelope_status": summary.get(
                "rho_physical_envelope_status"
            ),
            "A_ref": result.get("reference", {}).get("A_ref"),
            "mean_reference_to_scattering_amplitude_ratio": summary.get(
                "mean_reference_to_scattering_amplitude_ratio"
            ),
            "mean_interference_overlap_factor_abs": summary.get(
                "mean_interference_overlap_factor_abs"
            ),
        }
        for field in _FREEZE_PROBE_STATUS_FIELDS:
            row[field] = _case_report_value(result, field)
        rows.append(row)

    if not rows:
        return FreezeProbeReportPayload(
            n_cases=0,
            status_distributions={},
            width_groups=[],
            top_cases=[],
            sanity_checks={
                "observation_ready_fraction": 0.0,
                "review_required_fraction": 0.0,
                "shared_beam_caution_fraction": 0.0,
                "rho_out_of_envelope_count": 0,
                "count_prediction_active_fraction": 0.0,
                "count_confidence_unavailable_fraction": 0.0,
                "crossing_conditioned_transport_unimplemented_fraction": 0.0,
                "interface_fullwave_required_fraction": 0.0,
                "thermal_pod_blocked_fraction": 0.0,
                "unimplemented_mie_to_power_chain_fraction": 0.0,
                "held_out_calibration_unavailable_fraction": 0.0,
            },
        ).to_payload()

    df = pd.DataFrame(rows)
    width_values = sorted(df["width_nm"].dropna().unique().tolist())
    narrow_width = float(width_values[0]) if width_values else None
    wide_width = float(width_values[-1]) if width_values else None

    status_distributions = _build_status_distributions_for_fields(
        df,
        _FREEZE_PROBE_STATUS_FIELDS,
    )

    width_groups = []
    for width_nm, group in df.groupby("width_nm", sort=True):
        width_groups.append(
            {
                "width_nm": float(width_nm),
                "n_cases": int(len(group)),
            }
        )

    narrow_group = df[df["width_nm"] == narrow_width] if narrow_width is not None else pd.DataFrame()
    wide_group = df[df["width_nm"] == wide_width] if wide_width is not None else pd.DataFrame()

    def _safe_mean(frame: pd.DataFrame, col: str, default: float) -> float:
        if frame.empty:
            return float(default)
        return float(frame[col].fillna(default).mean())

    narrow_mean_aref = _safe_mean(narrow_group, "A_ref", 0.0)
    wide_mean_aref = _safe_mean(wide_group, "A_ref", 0.0)
    narrow_mean_ratio = _safe_mean(
        narrow_group, "mean_reference_to_scattering_amplitude_ratio", 0.0
    )
    wide_mean_ratio = _safe_mean(
        wide_group, "mean_reference_to_scattering_amplitude_ratio", 0.0
    )
    narrow_mean_overlap = _safe_mean(
        narrow_group, "mean_interference_overlap_factor_abs", 1.0
    )
    wide_mean_overlap = _safe_mean(
        wide_group, "mean_interference_overlap_factor_abs", 1.0
    )

    observation_ready_fraction = float(
        (df["observation_freeze_status"] == "default_ready_for_result_freeze").mean()
    )
    review_required_fraction = float(
        (df["observation_freeze_status"] == "review_required_before_result_freeze").mean()
    )
    shared_beam_caution_fraction = float(
        (df["delta_phi_gouy_validity"] == "shared_beam_caution").mean()
    )
    rho_out_of_envelope_count = int(
        (df["rho_physical_envelope_status"] != "within_envelope").sum()
    )
    count_prediction_active_fraction = float(
        (df["count_prediction_status"] == "poisson_flux_deadtime_surrogate_active").mean()
    )
    count_confidence_unavailable_fraction = float(
        (
            df["count_rate_confidence_status"]
            == "not_available_no_blank_false_positive_or_uncertainty_propagation"
        ).mean()
    )
    crossing_conditioned_transport_unimplemented_fraction = float(
        df["crossing_conditioned_transport_status"].fillna("").str.startswith(
            "not_implemented"
        ).mean()
    )
    interface_fullwave_required_fraction = float(
        _truthy_status_series(df, "interface_fullwave_required").mean()
    )
    pod_route_series = _status_text_series(df, "pod_quantitative_route_status")
    pod_model_series = _status_text_series(df, "thermal_pod_model_status")
    thermal_pod_blocked_fraction = float(
        (
            pod_route_series.str.startswith("blocked")
            | pod_model_series.str.startswith("unavailable")
        ).mean()
    )
    unimplemented_mie_to_power_chain_fraction = float(
        _status_text_series(df, "mie_to_power_chain_status")
        .str.startswith("not_implemented")
        .mean()
    )
    held_out_calibration_unavailable_fraction = float(
        _status_text_series(df, "calibration_held_out_validation_status")
        .str.startswith("not_available")
        .mean()
    )

    top_cases = []
    top_df = df.sort_values(
        ["final_engineering_score", "score"],
        ascending=[False, False],
    ).head(max(int(top_k), 1))
    for row in top_df.to_dict("records"):
        top_cases.append(
            {
                "particle_name": str(row["particle_name"]),
                "final_engineering_score": float(row["final_engineering_score"]),
                "path_opd_freeze_status": row["path_opd_freeze_status"],
                "observation_freeze_status": row["observation_freeze_status"],
                "count_prediction_status": row["count_prediction_status"],
                "count_rate_confidence_status": row["count_rate_confidence_status"],
                "interface_fullwave_required": _is_truthy_status_value(
                    row["interface_fullwave_required"]
                ),
                "thermal_pod_model_status": row["thermal_pod_model_status"],
                "pod_quantitative_route_status": row["pod_quantitative_route_status"],
            }
        )

    return FreezeProbeReportPayload(
        n_cases=int(len(df)),
        status_distributions=status_distributions,
        width_groups=width_groups,
        top_cases=top_cases,
        sanity_checks={
            "observation_ready_fraction": observation_ready_fraction,
            "review_required_fraction": review_required_fraction,
            "shared_beam_caution_fraction": shared_beam_caution_fraction,
            "rho_out_of_envelope_count": rho_out_of_envelope_count,
            "count_prediction_active_fraction": count_prediction_active_fraction,
            "count_confidence_unavailable_fraction": (
                count_confidence_unavailable_fraction
            ),
            "crossing_conditioned_transport_unimplemented_fraction": (
                crossing_conditioned_transport_unimplemented_fraction
            ),
            "interface_fullwave_required_fraction": (
                interface_fullwave_required_fraction
            ),
            "thermal_pod_blocked_fraction": thermal_pod_blocked_fraction,
            "unimplemented_mie_to_power_chain_fraction": (
                unimplemented_mie_to_power_chain_fraction
            ),
            "held_out_calibration_unavailable_fraction": (
                held_out_calibration_unavailable_fraction
            ),
            "narrow_width_nm": narrow_width,
            "wide_width_nm": wide_width,
            "narrow_channel_reference_more_conservative": bool(
                narrow_mean_aref <= wide_mean_aref + 1e-12
                and narrow_mean_ratio <= wide_mean_ratio + 1e-12
                and narrow_mean_overlap <= wide_mean_overlap + 1e-12
            ),
        },
    ).to_payload()


def precompute_sweep(
    grid_name: str = "coarse",
    config_tag: str | None = None,
    particle_profile: str = PRECOMPUTE_PROFILE_DEFAULT,
    output_dir: str = "results/",
    n_workers: int | None = 1,
    save_freeze_probe_report: bool = False,
    progress_interval_s: float = 2.0,
    resume: bool = True,
    checkpoint_enabled: bool = True,
    checkpoint_batch_size: int = 100,
    checkpoint_flush_interval_s: float = 5.0,
    artifact_profile: str = ARTIFACT_PROFILE_STANDARD,
    allow_partial_results: bool = False,
    random_sequence_policy: str | None = None,
    event_sampling_policy: str | None = None,
    adaptive_event_budget_mode: str | None = None,
    adaptive_min_events: int | None = None,
    adaptive_check_interval: int | None = None,
    adaptive_wilson_half_width_target: float | None = None,
    vectorized_event_engine: str | None = None,
    event_block_size: int | None = None,
    event_block_rng_order: str | None = None,
    include_diffusion: bool | None = None,
):
    """Run full parameter sweep and save results to files."""
    os.makedirs(output_dir, exist_ok=True)
    run_context = _build_precompute_run_context(
        grid_name=grid_name,
        config_tag=config_tag,
        particle_profile=particle_profile,
        output_dir=output_dir,
        n_workers=n_workers,
        checkpoint_enabled=checkpoint_enabled,
        resume_enabled=resume,
        artifact_profile=artifact_profile,
        allow_partial_results=allow_partial_results,
        random_sequence_policy=random_sequence_policy,
        event_sampling_policy=event_sampling_policy,
        adaptive_event_budget_mode=adaptive_event_budget_mode,
        adaptive_min_events=adaptive_min_events,
        adaptive_check_interval=adaptive_check_interval,
        adaptive_wilson_half_width_target=adaptive_wilson_half_width_target,
        vectorized_event_engine=vectorized_event_engine,
        event_block_size=event_block_size,
        event_block_rng_order=event_block_rng_order,
        include_diffusion=include_diffusion,
    )
    grid_name = run_context.grid_name
    config_tag = run_context.config_tag
    particle_profile = run_context.particle_profile
    profile = run_context.profile
    particle_types = run_context.particle_types
    grid = run_context.grid
    sim_cfg = run_context.sim_cfg
    n_particles = len(particle_types)
    n_wavelengths = len(grid["wavelength_list_m"])
    n_widths = len(grid["width_list_m"])
    n_depths = len(grid["depth_list_m"])
    total = run_context.total_cases
    worker_count = run_context.worker_count
    artifact_paths = run_context.artifact_paths
    artifact_profile = run_context.artifact_profile
    progress_path = artifact_paths.progress_json
    checkpoint_dir = artifact_paths.checkpoint_dir
    checkpoint_chunks_dir = artifact_paths.checkpoint_chunks_dir
    checkpoint_manifest_path = artifact_paths.checkpoint_manifest_json
    job_state = PrecomputeJobState.initial(
        started_at=datetime.now().astimezone(),
        worker_count=worker_count,
        total_cases=total,
    )

    if run_context.checkpoint_enabled:
        if run_context.resume_enabled:
            _restore_job_state_from_checkpoint(job_state, checkpoint_dir, run_context)
        else:
            if os.path.isdir(checkpoint_dir):
                shutil.rmtree(checkpoint_dir)
        os.makedirs(checkpoint_chunks_dir, exist_ok=True)

    def _build_checkpoint_manifest_payload(
        *,
        status: str,
        current_stage: str,
        updated_at: datetime,
        error: str | None = None,
    ) -> dict:
        return PrecomputeCheckpointManifest(
            grid=run_context.grid_name,
            config_tag=run_context.config_tag,
            particle_profile=run_context.particle_profile,
            total_cases=total,
            checkpointed_cases=len(job_state.persisted_case_keys),
            checkpoint_chunk_count=job_state.checkpoint_chunk_count,
            next_chunk_index=job_state.next_chunk_index,
            current_stage=current_stage,
            status=status,
            started_at_iso=job_state.started_at.isoformat(),
            updated_at_iso=updated_at.isoformat(),
            progress_file=progress_path,
            error=error,
        ).to_payload()

    def _apply_runtime_progress_update(
        runtime_progress: dict | SweepRuntimeProgress | None,
    ) -> None:
        if runtime_progress is None:
            return
        if isinstance(runtime_progress, SweepRuntimeProgress):
            job_state.runtime_progress = runtime_progress
            return
        job_state.runtime_progress = SweepRuntimeProgress.from_payload(
            runtime_progress,
            fallback_total_cases=total,
            fallback_active_workers=job_state.worker_count,
        )

    def _write_status_artifacts(
        *,
        current_stage: str,
        status: str,
        runtime_progress: dict | SweepRuntimeProgress | None = None,
        updated_at: datetime | None = None,
        manifest_stage: str | None = None,
        error: str | None = None,
        write_manifest: bool = True,
        write_progress: bool = True,
    ) -> None:
        _apply_runtime_progress_update(runtime_progress)
        if updated_at is None:
            updated_at = datetime.now().astimezone()
        if write_manifest and run_context.checkpoint_enabled:
            checkpoint_payload = _build_checkpoint_manifest_payload(
                status=status,
                current_stage=manifest_stage or current_stage,
                updated_at=updated_at,
                error=error,
            )
            _write_json_atomic(checkpoint_manifest_path, checkpoint_payload)
        if write_progress:
            progress_payload = _build_progress_payload(
                current_stage=current_stage,
                status=status,
                runtime_progress=job_state.runtime_progress,
                updated_at=updated_at,
                error=error,
            )
            _write_json_atomic(progress_path, progress_payload)

    def write_checkpoint_manifest(
        *,
        status: str,
        current_stage: str,
        updated_at: datetime | None = None,
        error: str | None = None,
    ) -> None:
        _write_status_artifacts(
            current_stage=current_stage,
            status=status,
            updated_at=updated_at,
            error=error,
            write_progress=False,
        )

    def flush_checkpoint(*, force: bool = False) -> None:
        if not run_context.checkpoint_enabled or not job_state.checkpoint_buffer:
            return
        now = time.perf_counter()
        if not _should_flush_checkpoint(
            force=force,
            buffer_size=len(job_state.checkpoint_buffer),
            batch_size=checkpoint_batch_size,
            last_flush_at=job_state.last_checkpoint_flush,
            now=now,
            flush_interval_s=checkpoint_flush_interval_s,
        ):
            return

        flush_t0 = time.perf_counter()
        chunk_payload = [_normalize_raw_case_result(item) for item in job_state.checkpoint_buffer]
        job_state.checkpoint_buffer.clear()
        chunk_index = job_state.next_chunk_index
        chunk_path = os.path.join(
            checkpoint_chunks_dir,
            f"chunk_{chunk_index:06d}.pkl",
        )
        _write_pickle_atomic(chunk_path, chunk_payload)
        flush_duration = time.perf_counter() - flush_t0
        for item in chunk_payload:
            job_state.persisted_case_keys.add(str(item["case_key"]))
        job_state.next_chunk_index += 1
        job_state.checkpoint_chunk_count += 1
        job_state.last_checkpoint_flush = now
        job_state.checkpoint_flush_records.append(
            {
                "chunk_index": int(chunk_index),
                "cases": int(len(chunk_payload)),
                "duration_seconds": float(flush_duration),
                "bytes": int(os.path.getsize(chunk_path)) if os.path.exists(chunk_path) else None,
            }
        )
        write_checkpoint_manifest(status="running", current_stage="checkpointing")

    def _build_progress_payload(
        *,
        current_stage: str,
        status: str,
        runtime_progress: SweepRuntimeProgress,
        updated_at: datetime,
        error: str | None = None,
    ) -> dict:
        progress_fraction = float(runtime_progress.progress_fraction or 0.0)
        elapsed_seconds = float(runtime_progress.elapsed_seconds or 0.0)
        estimated_remaining_seconds = runtime_progress.estimated_remaining_seconds
        estimated_total_seconds = runtime_progress.estimated_total_seconds
        if current_stage != "sweep" and status != "failed":
            progress_fraction = 1.0 if total > 0 else 0.0
            estimated_remaining_seconds = 0.0
            estimated_total_seconds = max(elapsed_seconds, estimated_total_seconds or 0.0)

        eta_iso = _eta_iso_from_remaining(updated_at, estimated_remaining_seconds)

        return PrecomputeProgressSnapshot(
            grid=run_context.grid_name,
            config_tag=run_context.config_tag,
            particle_profile=run_context.particle_profile,
            n_events_per_case=int(run_context.grid["n_events"]),
            total_cases=total,
            completed_cases=runtime_progress.completed_cases,
            successful_cases=runtime_progress.successful_cases,
            failed_cases=runtime_progress.failed_cases,
            progress_fraction=progress_fraction,
            elapsed_seconds=elapsed_seconds,
            cases_per_second=runtime_progress.cases_per_second,
            estimated_total_seconds=estimated_total_seconds,
            estimated_remaining_seconds=estimated_remaining_seconds,
            eta_iso=eta_iso,
            active_workers=int(runtime_progress.active_workers or job_state.worker_count),
            current_stage=current_stage,
            status=status,
            started_at_iso=job_state.started_at.isoformat(),
            updated_at_iso=updated_at.isoformat(),
            last_case=runtime_progress.last_case,
            checkpoint_enabled=run_context.checkpoint_enabled,
            resume_enabled=run_context.resume_enabled,
            checkpoint_dir=checkpoint_dir if run_context.checkpoint_enabled else None,
            checkpointed_cases=len(job_state.persisted_case_keys),
            checkpoint_chunk_count=job_state.checkpoint_chunk_count,
            checkpoint_buffer_cases=len(job_state.checkpoint_buffer),
            saved_outputs=dict(job_state.saved_outputs),
            error=error,
        ).to_payload()

    def publish_status(
        *,
        current_stage: str,
        status: str,
        runtime_progress: dict | SweepRuntimeProgress | None = None,
        manifest_stage: str | None = None,
        error: str | None = None,
        write_manifest: bool = True,
    ) -> None:
        _write_status_artifacts(
            current_stage=current_stage,
            status=status,
            runtime_progress=runtime_progress,
            manifest_stage=manifest_stage,
            error=error,
            write_manifest=write_manifest,
        )

    def on_runtime_progress(progress: dict) -> None:
        flush_checkpoint(force=False)
        publish_status(
            current_stage="sweep",
            status="running",
            runtime_progress=progress,
            write_manifest=False,
        )

    def on_case_result(raw_result: dict) -> None:
        if not run_context.checkpoint_enabled:
            return
        job_state.checkpoint_buffer.append(_normalize_raw_case_result(raw_result))
        flush_checkpoint(force=False)

    def run_save_stage(step: PrecomputeSaveStep):
        publish_status(current_stage=step.stage_name, status="running")
        save_t0 = time.perf_counter()
        output_path, log_message = _execute_precompute_save_step(step)
        save_duration = time.perf_counter() - save_t0
        if step.output_key and output_path:
            job_state.saved_outputs[step.output_key] = output_path
        job_state.save_stage_records.append(
            {
                "stage_name": step.stage_name,
                "output_key": step.output_key,
                "path": output_path,
                "duration_seconds": float(save_duration),
                "bytes": int(os.path.getsize(output_path)) if os.path.exists(output_path) else None,
            }
        )
        publish_status(current_stage=step.stage_name, status="running", write_manifest=False)
        if log_message:
            print(log_message, flush=True)
        return output_path

    print(
        f"Starting sweep: grid={grid_name}, tag={config_tag}, "
        f"profile={particle_profile}"
    , flush=True)
    print(f"  {profile['label']}", flush=True)
    print(f"  {n_particles} particles × {n_wavelengths} wavelengths × "
          f"{n_widths} widths × {n_depths} depths = {total} cases", flush=True)
    print(f"  {grid['n_events']} events per case", flush=True)
    print(
        "  sampling: "
        f"events={sim_cfg.event_sampling_policy}, "
        f"rng={sim_cfg.random_sequence_policy}, "
        f"adaptive={sim_cfg.adaptive_event_budget_mode}, "
        f"vectorized={sim_cfg.vectorized_event_engine}, "
        f"block={sim_cfg.event_block_size}, "
        f"rng_order={sim_cfg.event_block_rng_order}, "
        f"diffusion={sim_cfg.include_diffusion}",
        flush=True,
    )
    print(f"  artifact profile: {artifact_profile}", flush=True)
    print(f"  progress file: {progress_path}", flush=True)
    if run_context.checkpoint_enabled:
        print(f"  checkpoint dir: {checkpoint_dir}", flush=True)
        if job_state.checkpoint_results:
            print(
                f"  resume enabled: loaded {len(job_state.checkpoint_results)} checkpointed cases",
                flush=True,
            )
    print(flush=True)
    publish_status(current_stage="initializing", status="running")

    t0 = time.time()
    try:
        results = run_parameter_sweep(
            **_build_parameter_sweep_kwargs(
                run_context=run_context,
                n_workers=n_workers,
                progress_interval_s=progress_interval_s,
                progress_callback=on_runtime_progress,
                case_result_callback=on_case_result,
                resume_results=job_state.checkpoint_results,
                skip_case_keys=job_state.persisted_case_keys,
            )
        )
    except Exception as exc:
        flush_checkpoint(force=True)
        publish_status(current_stage="sweep", status="failed", error=str(exc))
        raise
    flush_checkpoint(force=True)
    elapsed = time.time() - t0
    job_state.sweep_elapsed_seconds = float(elapsed)
    job_state.runtime_progress.mark_sweep_completed(
        total_cases=total,
        successful_cases=len(results),
        elapsed_seconds=elapsed,
    )
    publish_status(
        current_stage="sweep",
        manifest_stage="sweep_completed",
        status="completed",
    )

    print(f"\nSweep completed: {len(results)} cases in {elapsed:.1f}s", flush=True)

    # Save files
    try:
        save_context = PrecomputeSaveContext()
        save_steps = _build_precompute_save_steps(
            artifact_paths=artifact_paths,
            save_context=save_context,
            results=results,
            grid_name=grid_name,
            config_tag=config_tag,
            particle_profile=particle_profile,
            sim_cfg=sim_cfg,
            grid=grid,
            particle_types=particle_types,
            save_freeze_probe_report=save_freeze_probe_report,
            artifact_profile=artifact_profile,
            allow_partial_results=run_context.allow_partial_results,
        )

        for step in save_steps:
            run_save_stage(step)
        publish_status(current_stage="saving_runtime_performance", status="running")
        runtime_t0 = time.perf_counter()
        runtime_performance = build_runtime_performance_report(
            results,
            run_context=run_context,
            job_state=job_state,
            wall_elapsed_seconds=time.time() - t0,
        )
        _write_json_atomic(artifact_paths.runtime_performance_json, runtime_performance)
        runtime_duration = time.perf_counter() - runtime_t0
        job_state.saved_outputs["runtime_performance_json"] = (
            artifact_paths.runtime_performance_json
        )
        job_state.save_stage_records.append(
            {
                "stage_name": "saving_runtime_performance",
                "output_key": "runtime_performance_json",
                "path": artifact_paths.runtime_performance_json,
                "duration_seconds": float(runtime_duration),
                "bytes": int(os.path.getsize(artifact_paths.runtime_performance_json))
                if os.path.exists(artifact_paths.runtime_performance_json)
                else None,
            }
        )
        publish_status(
            current_stage="saving_runtime_performance",
            status="running",
            write_manifest=False,
        )
        print(f"  Saved {artifact_paths.runtime_performance_json}", flush=True)
    except Exception as exc:
        publish_status(current_stage="saving_outputs", status="failed", error=str(exc))
        raise

    publish_status(current_stage="completed", status="completed")
    try:
        _cleanup_runtime_artifacts(
            progress_path=progress_path,
            checkpoint_dir=checkpoint_dir if run_context.checkpoint_enabled else None,
        )
    except Exception as exc:
        print(
            "Warning: final results were saved, but temporary runtime artifact cleanup "
            f"failed: {exc}",
            flush=True,
        )

    return results


def main():
    parser = argparse.ArgumentParser(description="NODI Simulator — Precompute sweep results")
    parser.add_argument("--grid", default="coarse", choices=sorted(GRID_CONFIGS),
                        help="Grid resolution (default: coarse)")
    parser.add_argument("--tag", default=None,
                        help="Config tag for file naming (default: profile tag)")
    parser.add_argument(
        "--particle-profile",
        default=PRECOMPUTE_PROFILE_DEFAULT,
        choices=sorted(PRECOMPUTE_PROFILES),
        help="Particle precompute profile",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help=(
            "Worker process count for the sweep "
            "(default: 8 for routine runs; use 0 for all logical CPUs)."
        ),
    )
    parser.add_argument(
        "--freeze-probe-report",
        action="store_true",
        help="Save an additional *_freeze_probe.json sanity report for current results.",
    )
    parser.add_argument(
        "--progress-interval",
        type=float,
        default=2.0,
        help="Progress refresh interval in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Resume from checkpointed raw cases when available (default: enabled).",
    )
    parser.add_argument(
        "--checkpoint",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Persist raw case chunks for crash-safe resume (default: enabled).",
    )
    parser.add_argument(
        "--checkpoint-batch-size",
        type=int,
        default=100,
        help="Flush checkpoint chunks after this many successful new cases (default: 100).",
    )
    parser.add_argument(
        "--checkpoint-flush-interval",
        type=float,
        default=5.0,
        help="Maximum seconds between checkpoint flushes (default: 5.0).",
    )
    parser.add_argument("--output", default="results/",
                        help="Output directory (default: results/)")
    parser.add_argument(
        "--artifact-profile",
        default=ARTIFACT_PROFILE_STANDARD,
        choices=ARTIFACT_PROFILES,
        help=(
            "Export artifact set: standard keeps dashboard plus design-postprocess outputs, "
            "full keeps compatibility split exports, "
            "minimal keeps only dashboard-required outputs."
        ),
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help=(
            "Allow final artifacts to contain only successful cases if some sweep "
            "cases fail. Default is to fail the run instead."
        ),
    )
    parser.add_argument(
        "--random-sequence-policy",
        default=None,
        choices=RANDOM_SEQUENCE_POLICY_OPTIONS,
        help=(
            "Case-level RNG policy. Omit to keep the SimulationConfig default."
        ),
    )
    parser.add_argument(
        "--event-sampling-policy",
        default=None,
        choices=EVENT_SAMPLING_POLICY_OPTIONS,
        help=(
            "Event initial-position sampling policy. Low-variance modes "
            "intentionally change numerical estimates."
        ),
    )
    parser.add_argument(
        "--adaptive-event-budget-mode",
        default=None,
        choices=ADAPTIVE_EVENT_BUDGET_MODE_OPTIONS,
        help="Adaptive event budget policy. Omit to keep fixed n_events.",
    )
    parser.add_argument(
        "--adaptive-min-events",
        type=int,
        default=None,
        help="Minimum events before adaptive stopping can trigger.",
    )
    parser.add_argument(
        "--adaptive-check-interval",
        type=int,
        default=None,
        help="Event interval for adaptive Wilson-precision checks.",
    )
    parser.add_argument(
        "--adaptive-wilson-half-width",
        type=float,
        default=None,
        help="Target Wilson half-width for adaptive precision stopping.",
    )
    parser.add_argument(
        "--vectorized-event-engine",
        default=None,
        choices=VECTORIZED_EVENT_ENGINE_OPTIONS,
        help=(
            "Optional event-loop engine. pure_advection_block batches "
            "non-diffusive stream-summary sweeps; event_block_v2 also batches "
            "diffusion-enabled stream-summary sweeps; event_block_v3 adds "
            "block-level peak summary extraction and records any fallback."
        ),
    )
    parser.add_argument(
        "--event-block-size",
        type=int,
        default=None,
        help="Maximum events per vectorized block.",
    )
    parser.add_argument(
        "--event-block-rng-order",
        default=None,
        choices=EVENT_BLOCK_RNG_ORDER_OPTIONS,
        help=(
            "Random draw order for event_block_v2/v3. event_loop_order preserves "
            "scalar-order regression behavior; block_lane_order uses faster "
            "per-lane streams and changes individual event trajectories."
        ),
    )
    parser.add_argument(
        "--diffusion",
        dest="include_diffusion",
        action="store_true",
        default=None,
        help="Enable Brownian diffusion for this precompute run.",
    )
    parser.add_argument(
        "--no-diffusion",
        dest="include_diffusion",
        action="store_false",
        help=(
            "Disable Brownian diffusion. This allows pure_advection_block "
            "to run when the other stream-summary constraints are met."
        ),
    )
    args = parser.parse_args()

    try:
        precompute_sweep(
            grid_name=args.grid,
            config_tag=args.tag,
            particle_profile=args.particle_profile,
            output_dir=args.output,
            n_workers=args.workers,
            save_freeze_probe_report=args.freeze_probe_report,
            progress_interval_s=args.progress_interval,
            resume=args.resume,
            checkpoint_enabled=args.checkpoint,
            checkpoint_batch_size=args.checkpoint_batch_size,
            checkpoint_flush_interval_s=args.checkpoint_flush_interval,
            artifact_profile=args.artifact_profile,
            allow_partial_results=args.allow_partial,
            random_sequence_policy=args.random_sequence_policy,
            event_sampling_policy=args.event_sampling_policy,
            adaptive_event_budget_mode=args.adaptive_event_budget_mode,
            adaptive_min_events=args.adaptive_min_events,
            adaptive_check_interval=args.adaptive_check_interval,
            adaptive_wilson_half_width_target=args.adaptive_wilson_half_width,
            vectorized_event_engine=args.vectorized_event_engine,
            event_block_size=args.event_block_size,
            event_block_rng_order=args.event_block_rng_order,
            include_diffusion=args.include_diffusion,
        )
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
