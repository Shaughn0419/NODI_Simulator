"""
dashboard/backend.py - backend helpers.

Provides:
    - Data loading (CSV, pkl, meta) with schema version check
    - Explorer utilities (heatmap matrix, slice, recompute scores)
    - Inspector utilities (case lookup, physics breakdown, on-demand recompute)
    - Parameter tuning support (build configs from UI, live sweep, live tag)
"""

import json
import os
import re
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from nodi_simulator.dashboard.config import (
    GRID_CONFIGS,
    get_precompute_particles,
    infer_particle_diameter_nm,
    infer_particle_material,
)
from nodi_simulator.dashboard.safe_pickle import load_dashboard_pickle
from nodi_simulator.utils import (
    classify_design_recommendation,
    classify_engineering_gate_explanation,
    build_case_decision_summary,
)


# ============================================================
# Schema version
# ============================================================

CURRENT_SCHEMA_VERSION = "1.24"
CURRENT_STANDARD_DATASET_PREFIX = "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"

_WORKFLOW_DATASET_PRIORITY = (
    CURRENT_STANDARD_DATASET_PREFIX,
    "coarse_default",
)
_STANDARD_WORKFLOW_PREFIXES = {
    CURRENT_STANDARD_DATASET_PREFIX,
}
_LEGACY_WORKFLOW_PREFIXES = {
    "coarse_default",
    "coarse_full_range",
    "fine_current_model_full_range",
    "fine_fine_full_range_10000e",
    "fine_full_range",
    "fine_full_range_biomimetic_exosome",
    "fine_full_range_biomimetic_exosome_10000e",
}
_SAFE_DATASET_PREFIX_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


@dataclass(frozen=True)
class DashboardDataSource:
    """Resolved dashboard data-source summary for one page render."""

    is_live: bool
    prefix: str | None
    tag: str | None
    summary_caption: str
    detail_caption: str


STANDARD_DATASET_FAMILY_LABEL = "标准 biomimetic full-range 结果库"
COMPATIBILITY_DATASET_FAMILY_LABEL = "兼容结果库"


@dataclass
class DashboardLoadedData:
    """Bundle of loaded dashboard artifacts for the active data source."""

    df: pd.DataFrame
    compact: list[dict] | None
    meta: dict | None
    health_report: dict | None
    source: DashboardDataSource


# ============================================================
# Data file management
# ============================================================

def check_data_files(results_dir: str, prefix: str) -> tuple[str, str, str]:
    """
    Check existence of sweep result files + schema version match.

    Three kinds of error:
      - File missing -> FileNotFoundError
      - meta missing dashboard_schema_version -> ValueError
      - Version mismatch -> ValueError

    Returns:
        (csv_path, pkl_path, meta_path)
    """
    safe_prefix = _validate_dataset_prefix(prefix)
    csv_path = os.path.join(results_dir, f"{safe_prefix}_summary.csv")
    pkl_path = os.path.join(results_dir, f"{safe_prefix}_compact.pkl")
    meta_path = os.path.join(results_dir, f"{safe_prefix}_meta.json")

    for path in [csv_path, pkl_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{path} not found. Run precompute.py first."
            )

    if os.path.exists(meta_path):
        meta = load_metadata(meta_path)
        version = meta.get("dashboard_schema_version")
        if version is None:
            raise ValueError(
                f"{meta_path} missing dashboard_schema_version field. "
                f"Re-run precompute.py to regenerate."
            )
        if version != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"Schema version mismatch: file has {version}, "
                f"code expects {CURRENT_SCHEMA_VERSION}. Re-run precompute.py."
            )
        _validate_standard_dataset_grid_coverage(meta, safe_prefix, meta_path)

    return csv_path, pkl_path, meta_path


def _validate_standard_dataset_grid_coverage(
    meta: Mapping[str, Any],
    prefix: str,
    meta_path: str,
) -> None:
    """Reject stale standard result libraries whose grid no longer matches code."""
    if prefix != CURRENT_STANDARD_DATASET_PREFIX:
        return
    expected_wavelengths = [
        int(round(float(value) * 1e9))
        for value in GRID_CONFIGS["ev_design"]["wavelength_list_m"]
    ]
    observed_wavelengths = [
        int(round(float(value))) for value in meta.get("wavelengths_nm", [])
    ]
    if observed_wavelengths != expected_wavelengths:
        raise ValueError(
            f"Standard dataset wavelength mismatch in {meta_path}: file has "
            f"{observed_wavelengths}, code expects {expected_wavelengths}. "
            "Re-run the formal ev_design precompute."
        )
    policy = meta.get("sweep_completion_policy", {})
    expected_cases = (
        len(get_precompute_particles("full_range_biomimetic_exosome_with_anchors"))
        * len(GRID_CONFIGS["ev_design"]["width_list_m"])
        * len(GRID_CONFIGS["ev_design"]["depth_list_m"])
        * len(GRID_CONFIGS["ev_design"]["wavelength_list_m"])
    )
    if int(policy.get("expected_total_cases") or meta.get("n_cases") or 0) != expected_cases:
        raise ValueError(
            f"Standard dataset case-count mismatch in {meta_path}: file has "
            f"{policy.get('expected_total_cases', meta.get('n_cases'))}, code expects "
            f"{expected_cases}. Re-run the formal ev_design precompute."
        )


def list_available_datasets(results_dir: str) -> list[str]:
    """List available dataset prefixes by scanning for *_summary.csv files."""
    if not os.path.isdir(results_dir):
        return []
    prefixes = []
    for f in sorted(os.listdir(results_dir)):
        if f.endswith("_summary.csv"):
            prefix = f.replace("_summary.csv", "")
            try:
                prefixes.append(_validate_dataset_prefix(prefix))
            except ValueError:
                continue
    return prefixes


def _validate_dataset_prefix(prefix: object) -> str:
    """Return a filesystem-safe dataset prefix before building artifact paths."""
    token = str(prefix).strip()
    if not token:
        raise ValueError("data_prefix must not be empty")
    if token in {".", ".."} or not _SAFE_DATASET_PREFIX_RE.fullmatch(token):
        raise ValueError(
            "data_prefix must be a safe filename token using only letters, "
            f"numbers, '.', '_' and '-'; got {prefix!r}"
        )
    return token


def _summary_parquet_path(results_dir: str, prefix: object) -> str:
    """Return the optional typed summary artifact path for a safe dataset prefix."""
    safe_prefix = _validate_dataset_prefix(prefix)
    return os.path.join(results_dir, f"{safe_prefix}_case_summary.parquet")


def is_standard_dashboard_dataset_prefix(prefix: str | None) -> bool:
    """Return whether the prefix is the current standard workflow dataset."""
    return prefix in _STANDARD_WORKFLOW_PREFIXES


def resolve_preferred_dataset_prefix(available_prefixes: list[str]) -> str | None:
    """Pick the preferred precomputed dataset prefix for dashboard browsing."""
    if not available_prefixes:
        return None
    for preferred in _WORKFLOW_DATASET_PRIORITY:
        if preferred in available_prefixes:
            return preferred
    return available_prefixes[0]


def sync_dashboard_data_prefix(
    session_state: Mapping[str, Any],
    available_prefixes: list[str],
) -> str | None:
    """Return a valid active precomputed prefix and sync it back to session state."""
    preferred_prefix = resolve_preferred_dataset_prefix(available_prefixes)
    if preferred_prefix is None:
        return None
    current_prefix = session_state.get("data_prefix")
    should_promote_legacy_prefix = (
        current_prefix in _LEGACY_WORKFLOW_PREFIXES
        and current_prefix != preferred_prefix
        and preferred_prefix in available_prefixes
    )
    if (
        (current_prefix not in available_prefixes or should_promote_legacy_prefix)
        and hasattr(session_state, "__setitem__")
    ):
        session_state["data_prefix"] = preferred_prefix
        return preferred_prefix
    return current_prefix if current_prefix in available_prefixes else preferred_prefix


# ============================================================
# Data loading
# ============================================================

_GATE_EXPLANATION_COLUMNS = [
    "engineering_gate_status_label",
    "engineering_gate_primary_blocker",
    "engineering_gate_primary_blocker_label",
    "engineering_gate_blocker_summary",
    "engineering_gate_guidance",
]

_DESIGN_RECOMMENDATION_COLUMNS = [
    "design_recommendation_status",
    "design_recommendation_label",
    "design_recommendation_rank",
    "design_recommendation_guidance",
]


def _maybe_backfill_gate_explanation(
    target: dict,
    *,
    gate_passed: object,
    gate_reason: object,
    gate_failed_count: object,
) -> None:
    if all(target.get(col) is not None for col in _GATE_EXPLANATION_COLUMNS):
        return
    explanation = classify_engineering_gate_explanation(
        engineering_gate_passed=bool(gate_passed),
        engineering_gate_reason=str(gate_reason or "N/A"),
        engineering_gate_failed_count=int(gate_failed_count or 0),
    )
    for key, value in explanation.items():
        target.setdefault(key, value)


def _maybe_backfill_design_recommendation(
    target: dict,
    *,
    gate_passed: object,
    observation_freeze_status: object,
) -> None:
    if all(target.get(col) is not None for col in _DESIGN_RECOMMENDATION_COLUMNS):
        return
    if observation_freeze_status is None:
        return
    recommendation = classify_design_recommendation(
        engineering_gate_passed=bool(gate_passed),
        observation_freeze_status=str(observation_freeze_status),
    )
    for key, value in recommendation.items():
        target.setdefault(key, value)


def _backfill_case_views(
    targets: list[dict],
    *,
    gate_passed: object,
    gate_reason: object,
    gate_failed_count: object,
    observation_freeze_status: object,
) -> None:
    for target in targets:
        _maybe_backfill_gate_explanation(
            target,
            gate_passed=gate_passed,
            gate_reason=gate_reason,
            gate_failed_count=gate_failed_count,
        )
        _maybe_backfill_design_recommendation(
            target,
            gate_passed=gate_passed,
            observation_freeze_status=observation_freeze_status,
        )


def _enrich_loaded_compact_case(case: dict) -> dict:
    summary = case.setdefault("summary", {})
    physics = case.setdefault("physics", {})

    gate_passed = case.get(
        "engineering_gate_passed",
        summary.get("engineering_gate_passed", False),
    )
    gate_reason = case.get(
        "engineering_gate_reason",
        summary.get("engineering_gate_reason", "N/A"),
    )
    gate_failed_count = case.get(
        "engineering_gate_failed_count",
        summary.get("engineering_gate_failed_count", 0),
    )
    observation_freeze_status = summary.get("observation_freeze_status")

    _backfill_case_views(
        [case, summary, physics],
        gate_passed=gate_passed,
        gate_reason=gate_reason,
        gate_failed_count=gate_failed_count,
        observation_freeze_status=observation_freeze_status,
    )
    return case


def _enrich_loaded_summary_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    enriched = df.copy()
    if any(col not in enriched.columns for col in _GATE_EXPLANATION_COLUMNS):
        explanations = enriched.apply(
            lambda row: classify_engineering_gate_explanation(
                engineering_gate_passed=bool(row.get("engineering_gate_passed", False)),
                engineering_gate_reason=str(row.get("engineering_gate_reason", "N/A")),
                engineering_gate_failed_count=int(row.get("engineering_gate_failed_count", 0) or 0),
            ),
            axis=1,
            result_type="expand",
        )
        for col in explanations.columns:
            if col not in enriched.columns:
                enriched[col] = explanations[col]
    if (
        any(col not in enriched.columns for col in _DESIGN_RECOMMENDATION_COLUMNS)
        and "observation_freeze_status" in enriched.columns
    ):
        recommendations = enriched.apply(
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
            if col not in enriched.columns:
                enriched[col] = recommendations[col]
    return enriched


def ensure_summary_geometry_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Backfill commonly used particle geometry columns for dashboard views."""
    enriched = df.copy()
    if "particle_material" not in enriched.columns and "particle_name" in enriched.columns:
        enriched["particle_material"] = enriched["particle_name"].map(infer_particle_material)
    if "particle_diameter_nm" not in enriched.columns and "particle_name" in enriched.columns:
        enriched["particle_diameter_nm"] = enriched["particle_name"].map(
            infer_particle_diameter_nm
        )
    return enriched


def lookup_summary_case_row(
    df: pd.DataFrame,
    *,
    particle_name: str | None,
    wavelength_nm: int | float | None,
    width_nm: int | float | None,
    depth_nm: int | float | None,
) -> dict[str, Any] | None:
    """Return one summary-row dict for the selected case if it exists."""
    if (
        particle_name is None
        or wavelength_nm is None
        or width_nm is None
        or depth_nm is None
        or df.empty
    ):
        return None

    sub = df[df["particle_name"] == particle_name]
    if sub.empty:
        return None

    sub = sub[
        np.isclose(sub["wavelength_nm"].astype(float), float(wavelength_nm))
        & np.isclose(sub["width_nm"].astype(float), float(width_nm))
        & np.isclose(sub["depth_nm"].astype(float), float(depth_nm))
    ]
    if sub.empty:
        return None
    return dict(sub.iloc[0])


def build_dashboard_data_source(
    session_state: Mapping[str, Any],
    *,
    meta: dict | None = None,
) -> DashboardDataSource:
    """Build shared live/precomputed source captions for dashboard pages."""
    if session_state.get("using_live_data"):
        live_tag = session_state.get("live_tag")
        tag = str(live_tag) if live_tag is not None else None
        return DashboardDataSource(
            is_live=True,
            prefix=None,
            tag=tag,
            summary_caption=(
                f"Live sweep source [{tag}] is active for this page."
                if tag
                else "Live sweep source is active for this page."
            ),
            detail_caption=(
                f"Live detail recomputation [{tag}]"
                if tag
                else "Live detail recomputation"
            ),
        )
    prefix = session_state.get("data_prefix")
    prefix_text = str(prefix) if prefix is not None else "unknown"
    if is_standard_dashboard_dataset_prefix(prefix_text):
        summary_caption = f"{STANDARD_DATASET_FAMILY_LABEL} [{prefix_text}]"
        detail_caption = f"来自 {STANDARD_DATASET_FAMILY_LABEL} 的明细视图 [{prefix_text}]"
    else:
        summary_caption = f"{COMPATIBILITY_DATASET_FAMILY_LABEL} [{prefix_text}]"
        detail_caption = f"来自 {COMPATIBILITY_DATASET_FAMILY_LABEL} 的明细视图 [{prefix_text}]"
    return DashboardDataSource(
        is_live=False,
        prefix=prefix_text,
        tag=prefix_text,
        summary_caption=summary_caption,
        detail_caption=detail_caption,
    )

def load_sweep_summary(
    csv_path: str,
    *,
    parquet_path: str | None = None,
) -> pd.DataFrame:
    """Load sweep summary, preferring the typed parquet artifact when present."""
    if parquet_path is not None and os.path.exists(parquet_path):
        return _enrich_loaded_summary_df(pd.read_parquet(parquet_path))
    return _enrich_loaded_summary_df(pd.read_csv(csv_path, low_memory=False))


def load_sweep_compact(pkl_path: str) -> list[dict]:
    """Load compact sweep results from a restricted dashboard pickle artifact."""
    with open(pkl_path, "rb") as f:
        data = load_dashboard_pickle(f)
    return [_enrich_loaded_compact_case(case) for case in data]


def load_metadata(meta_path: str) -> dict:
    """
    Load metadata JSON. Always returns dict.
    Raises FileNotFoundError if file doesn't exist.
    """
    if not os.path.exists(meta_path):
        raise FileNotFoundError(
            f"{meta_path} not found. Re-run precompute.py."
        )
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_result_health(
    results_dir: str,
    prefix: str | None,
    *,
    summary_df: pd.DataFrame | None = None,
) -> dict | None:
    """
    Load a dataset-level health report.

    Prefer a precomputed `{prefix}_result_health.json`. If it does not exist
    but a summary dataframe is available, backfill the report on demand from
    the current summary so older datasets remain display-compatible.
    """
    if prefix:
        safe_prefix = _validate_dataset_prefix(prefix)
        health_path = os.path.join(results_dir, f"{safe_prefix}_result_health.json")
        if os.path.exists(health_path):
            with open(health_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            report["_report_source"] = "precomputed_json"
            report["_report_path"] = health_path
            return report

    if summary_df is not None:
        from nodi_simulator.dashboard.precompute import build_result_health_report

        report = build_result_health_report(summary_df)
        report["_report_source"] = "computed_from_summary"
        report["_report_path"] = None
        return report

    return None


def load_dashboard_data_bundle(
    results_dir: str,
    session_state: Mapping[str, Any],
    *,
    include_compact: bool = False,
) -> DashboardLoadedData:
    """Load the active dashboard dataset bundle from live state or precomputed files."""
    source = build_dashboard_data_source(session_state)
    if source.is_live and session_state.get("sweep_df_live") is not None:
        df = ensure_summary_geometry_columns(session_state["sweep_df_live"])
        compact = session_state.get("sweep_compact_live") if include_compact else None
        health_report = load_result_health(
            results_dir,
            None,
            summary_df=df,
        )
        return DashboardLoadedData(
            df=df,
            compact=compact,
            meta=None,
            health_report=health_report,
            source=source,
        )

    prefix = source.prefix
    if prefix is None:
        raise FileNotFoundError("No active dashboard dataset prefix is selected.")
    csv_path, pkl_path, meta_path = check_data_files(results_dir, prefix)
    safe_prefix = _validate_dataset_prefix(prefix)
    parquet_path = _summary_parquet_path(results_dir, safe_prefix)
    df = ensure_summary_geometry_columns(
        load_sweep_summary(csv_path, parquet_path=parquet_path)
    )
    meta = load_metadata(meta_path)
    compact = load_sweep_compact(pkl_path) if include_compact else None
    health_report = load_result_health(
        results_dir,
        safe_prefix,
        summary_df=df,
    )
    return DashboardLoadedData(
        df=df,
        compact=compact,
        meta=meta,
        health_report=health_report,
        source=source,
    )


def load_workflow_case_anchor(
    results_dir: str,
    session_state: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    """Load the selected case row from the active precomputed workflow dataset."""
    workflow_state = {
        "using_live_data": False,
        "data_prefix": session_state.get("data_prefix"),
    }
    try:
        bundle = load_dashboard_data_bundle(results_dir, workflow_state)
    except (FileNotFoundError, ValueError):
        return None, None

    row = lookup_summary_case_row(
        bundle.df,
        particle_name=session_state.get("selected_particle"),
        wavelength_nm=session_state.get("selected_wavelength_nm"),
        width_nm=session_state.get("selected_W_nm"),
        depth_nm=session_state.get("selected_H_nm"),
    )
    return row, bundle.source.prefix


# ============================================================
# Explorer utilities
# ============================================================

def build_heatmap_matrix(
    df: pd.DataFrame,
    particle: str,
    wavelength_nm: float,
    value_col: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a 2D matrix for heatmap display.

    Returns:
        (W_arr, H_arr, matrix) where matrix.shape = (nH, nW).
    """
    sub = df[(df["particle_name"] == particle) &
             (df["wavelength_nm"] == wavelength_nm)].copy()

    if sub.empty:
        return np.array([]), np.array([]), np.array([[]])

    W_arr = np.sort(sub["width_nm"].unique())
    H_arr = np.sort(sub["depth_nm"].unique())

    matrix = np.full((len(H_arr), len(W_arr)), np.nan)
    for row in sub.to_dict("records"):
        wi = np.searchsorted(W_arr, row["width_nm"])
        hi = np.searchsorted(H_arr, row["depth_nm"])
        if wi < len(W_arr) and hi < len(H_arr):
            matrix[hi, wi] = row[value_col]

    return W_arr, H_arr, matrix


def build_slice_data(
    df: pd.DataFrame,
    particle: str,
    wavelength_nm: float,
    fixed_dim: str,
    fixed_val: float,
    value_col: str,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract a 1D slice from sweep data.

    Args:
        fixed_dim: "width" (fix W, vary H) or "depth" (fix H, vary W).
        fixed_val: Value of the fixed dimension in nm.
        value_col: Column to plot.

    Returns:
        (x_arr, y_arr) - varying dimension values and corresponding metric.
    """
    sub = df[(df["particle_name"] == particle) &
             (df["wavelength_nm"] == wavelength_nm)]

    if fixed_dim == "width":
        sub = sub[sub["width_nm"] == fixed_val].sort_values("depth_nm")
        return sub["depth_nm"].values, sub[value_col].values
    elif fixed_dim == "depth":
        sub = sub[sub["depth_nm"] == fixed_val].sort_values("width_nm")
        return sub["width_nm"].values, sub[value_col].values
    else:
        raise ValueError(f"fixed_dim must be 'width' or 'depth', got {fixed_dim}")


def recompute_scores(
    df: pd.DataFrame,
    w_height: float = 1.0,
    w_rate: float = 1.0,
    w_cv: float = 1.0,
) -> pd.Series:
    """
    Recompute single scores with new weights 竊・score_display.

    NOTE: Only affects single score. robust_score and joint_score are NOT
    recomputed (they depend on neighbor structure / dual-object pairing).
    """
    return (
        w_height * df["H_norm"]
        + w_rate * df["R_norm"]
        - w_cv * df["CV_norm"]
    )


# ============================================================
# Inspector utilities
# ============================================================

def get_case_summary(
    compact: list[dict],
    particle: str,
    wavelength_nm: float,
    W_nm: float,
    H_nm: float,
) -> dict | None:
    """
    Find a specific case from compact data.
    Uses np.isclose for float matching to avoid nm竊芭 precision issues.
    """
    wl_m = wavelength_nm * 1e-9
    w_m = W_nm * 1e-9
    h_m = H_nm * 1e-9
    for c in compact:
        if (c["particle_name"] == particle and
            np.isclose(c["wavelength_m"], wl_m, atol=1e-12) and
            np.isclose(c["width_m"], w_m, atol=1e-12) and
            np.isclose(c["depth_m"], h_m, atol=1e-12)):
            return c
    return None


def build_physics_breakdown(case_data: dict) -> dict:
    """
    Split case data into two groups for Inspector display.

    Returns:
        {
            "case_physics": dict of {name: float_or_None},
            "batch_outcome": dict of {name: float_or_str},
        }
    """
    physics = case_data.get("physics", {})
    summary = case_data.get("summary", {})
    decision_summary = build_case_decision_summary(
        design_recommendation_label=case_data.get(
            "design_recommendation_label",
            summary.get("design_recommendation_label"),
        ),
        design_recommendation_status=case_data.get(
            "design_recommendation_status",
            summary.get("design_recommendation_status"),
        ),
        design_recommendation_guidance=case_data.get(
            "design_recommendation_guidance",
            summary.get("design_recommendation_guidance"),
        ),
        engineering_gate_passed=bool(case_data.get("engineering_gate_passed")),
        engineering_gate_status_label=case_data.get(
            "engineering_gate_status_label",
            summary.get("engineering_gate_status_label"),
        ),
        engineering_gate_primary_blocker_label=case_data.get(
            "engineering_gate_primary_blocker_label",
            summary.get("engineering_gate_primary_blocker_label"),
        ),
        engineering_gate_blocker_summary=case_data.get(
            "engineering_gate_blocker_summary",
            summary.get("engineering_gate_blocker_summary"),
        ),
        engineering_gate_guidance=case_data.get(
            "engineering_gate_guidance",
            summary.get("engineering_gate_guidance"),
        ),
        observation_freeze_status=summary.get("observation_freeze_status"),
        observation_freeze_guidance=summary.get("observation_freeze_guidance"),
    )

    return {
        "decision_summary": decision_summary,
        "case_physics": {
            "Csca (mﾂｲ)": physics.get("Csca_m2"),
            "E_sca at det": physics.get("E_sca_at_det"),
            "E_sca_ref": physics.get("E_sca_ref"),
            "E_sca normalized": physics.get("E_sca_normalized"),
            "phi_projection (rad)": physics.get("phi_projection_rad"),
            "phi_sca_material (rad)": physics.get("phi_sca_material_rad"),
            "scattering projection basis": physics.get("scattering_projection_basis"),
            "particle family": physics.get("particle_family"),
            "particle optical model": physics.get("particle_optical_model"),
            "structured particle status": physics.get("structured_particle_model_status"),
            "structured particle preset": physics.get("structured_particle_preset_name"),
            "EV label": physics.get("EV_label"),
            "EV claim level": physics.get("EV_claim_level"),
            "exosome biogenesis claim": physics.get("exosome_biogenesis_claim"),
            "material dataset": physics.get("material_dataset"),
            "particle material model": physics.get("particle_material_model_mode"),
            "particle material source": physics.get("particle_material_dataset_source"),
            "particle material type": physics.get("particle_material_dataset_type"),
            "particle material wavelength status": physics.get(
                "particle_material_wavelength_status"
            ),
            "particle material temperature correction": physics.get(
                "particle_material_temperature_correction_status"
            ),
            "particle material uncertainty": physics.get(
                "particle_material_uncertainty_status"
            ),
            "metal size damping status": physics.get("metal_size_damping_status"),
            "ligand shell status": physics.get("ligand_shell_status"),
            "medium dispersion status": physics.get("medium_dispersion_status"),
            "wall dispersion status": physics.get("wall_dispersion_status"),
            "shape model": physics.get("shape_model"),
            "anisotropic shell model": physics.get("anisotropic_shell_model"),
            "orientation average status": physics.get("orientation_average_status"),
            "EV sample preparation": physics.get("EV_sample_preparation_status"),
            "EV isolation method": physics.get("EV_isolation_method"),
            "EV aggregation/co-isolate status": physics.get(
                "EV_aggregation_or_coisolate_status"
            ),
            "EV ensemble mode": physics.get("EV_ensemble_mode"),
            "EV ensemble name": physics.get("EV_ensemble_name"),
            "EV ensemble member": physics.get("EV_ensemble_member_preset"),
            "EV ensemble status": physics.get("EV_ensemble_status"),
            "EV prior status": physics.get("ev_population_prior_status"),
            "EV prior physical validity": physics.get("ev_prior_physical_validity"),
            "EV low-RI tail detection risk": physics.get(
                "ev_low_RI_tail_detection_risk"
            ),
            "contaminant family": physics.get("contaminant_family"),
            "contaminant detectability score": physics.get(
                "contaminant_detectability_score"
            ),
            "EV core RI nominal": physics.get("EV_core_RI_nominal"),
            "EV shell RI nominal": physics.get("EV_shell_RI_nominal"),
            "EV shell thickness m": physics.get("EV_shell_thickness_m"),
            "particle uncertainty budget": physics.get(
                "particle_uncertainty_budget_status"
            ),
            "uncertainty propagation mode": physics.get("uncertainty_propagation_mode"),
            "uncertainty output confidence": physics.get(
                "uncertainty_output_confidence_status"
            ),
            "uncertainty propagation status": physics.get(
                "uncertainty_propagation_status"
            ),
            "uncertainty propagation blockers": physics.get(
                "uncertainty_propagation_blocker_summary"
            ),
            "peak-height CI available": physics.get("peak_height_CI_available"),
            "detection-rate CI available": physics.get("detection_rate_CI_available"),
            "interface correction mode": physics.get("interface_correction_mode"),
            "interface API boundary": physics.get("interface_api_boundary_status"),
            "interface missing inputs": physics.get("interface_missing_inputs"),
            "interface correction status": physics.get("interface_correction_status"),
            "interface correction active": physics.get("interface_correction_active"),
            "interface incident-field correction": physics.get(
                "interface_incident_field_correction"
            ),
            "interface polarizability correction": physics.get(
                "interface_particle_polarizability_correction"
            ),
            "interface radiation-pattern correction": physics.get(
                "interface_radiation_pattern_collection_correction"
            ),
            "interface correction claim": physics.get("interface_correction_claim_level"),
            "interface output sensitivity": physics.get(
                "interface_output_sensitivity_status"
            ),
            "interface phase/polarity sensitive": physics.get(
                "interface_phase_or_polarity_sensitive_output"
            ),
            "interface angular-pattern sensitive": physics.get(
                "interface_angular_pattern_sensitive_output"
            ),
            "interface dipole surrogate validity": physics.get(
                "interface_dipole_surrogate_validity"
            ),
            "interface quantitative blockers": physics.get(
                "interface_quantitative_claim_blocker_summary"
            ),
            "homogeneous-medium Mie assumption": physics.get(
                "homogeneous_medium_mie_assumption"
            ),
            "eta interface": physics.get("eta_interface"),
            "eta lambda": physics.get("eta_lambda"),
            "interface full-wave required": physics.get("interface_fullwave_required"),
            "interface full-wave reason": physics.get("interface_fullwave_reason"),
            "conditional detection rate": physics.get("conditional_detection_rate"),
            "count generation model": physics.get("count_generation_model"),
            "per-event detectability boundary": physics.get(
                "per_event_detectability_boundary"
            ),
            "count prediction model": physics.get("count_prediction_model"),
            "count prediction status": physics.get("count_prediction_status"),
            "count prediction claim": physics.get("count_prediction_claim_level"),
            "number concentration m^-3": physics.get("number_concentration_m3"),
            "accessible area m2": physics.get("accessible_area_m2"),
            "volumetric flow rate m3/s": physics.get("volumetric_flow_rate_m3_s"),
            "volumetric flow rate source": physics.get("volumetric_flow_rate_source"),
            "Poisson arrival process": physics.get("poisson_arrival_process_status"),
            "flux-conditioned initial distribution": physics.get(
                "flux_conditioned_initial_distribution_status"
            ),
            "crossing-conditioned transport": physics.get(
                "crossing_conditioned_transport_status"
            ),
            "event rate Hz": physics.get("event_rate_Hz"),
            "predicted count rate Hz": physics.get("predicted_count_rate_Hz"),
            "dead-time loss fraction": physics.get("dead_time_loss_fraction"),
            "dead-time correction": physics.get("dead_time_correction_status"),
            "multi-occupancy probability": physics.get("multi_occupancy_probability"),
            "occupancy correction": physics.get("occupancy_correction_status"),
            "single-particle condition": physics.get("single_particle_condition_status"),
            "blank false-positive correction": physics.get(
                "blank_false_positive_correction_status"
            ),
            "missed-event correction": physics.get("missed_event_correction_status"),
            "count likelihood status": physics.get("count_likelihood_status"),
            "count log likelihood": physics.get("count_log_likelihood"),
            "false-positive corrected count": physics.get(
                "false_positive_corrected_count"
            ),
            "false-negative corrected count": physics.get(
                "false_negative_corrected_count"
            ),
            "count likelihood blockers": physics.get(
                "count_likelihood_blocker_summary"
            ),
            "OOD detection status": physics.get("ood_detection_status"),
            "unknown particle flag": physics.get("unknown_particle_flag"),
            "classifier rejection rate": physics.get("classifier_rejection_rate"),
            "unknown particle reason": physics.get("unknown_particle_reason"),
            "EV/contaminant hard classification allowed": physics.get(
                "EV_contaminant_hard_classification_allowed"
            ),
            "count-rate confidence": physics.get("count_rate_confidence_status"),
            "count uncertainty": physics.get("count_prediction_uncertainty_status"),
            "wall interaction model": physics.get("wall_interaction_model"),
            "wall interaction status": physics.get("wall_interaction_status"),
            "Detection operator": physics.get("detection_operator_signature"),
            "operator route": physics.get("operator_route"),
            "operator normalization": physics.get("operator_normalization"),
            "collection operator calibration": physics.get(
                "collection_operator_calibration_status"
            ),
            "collection operator coverage": physics.get(
                "collection_operator_coverage_status"
            ),
            "collection operator calibration role": physics.get(
                "collection_operator_calibration_data_role"
            ),
            "BFP ROI mask status": physics.get("bfp_roi_mask_status"),
            "BFP ROI mask source": physics.get("bfp_roi_mask_source"),
            "BFP ROI mask role": physics.get("bfp_roi_mask_data_role"),
            "BFP ROI mask gate": physics.get("bfp_roi_mask_gate_passed"),
            "collection operator id": physics.get("collection_operator_id"),
            "collection operator calibrated geometry": physics.get(
                "collection_operator_calibrated_geometry"
            ),
            "Observation signature": physics.get("observation_signature"),
            "detector forward model": physics.get("detector_forward_model"),
            "detector forward status": physics.get("detector_forward_status"),
            "detector forward claim": physics.get("detector_forward_claim_level"),
            "field coordinate measure": physics.get("field_coordinate_measure"),
            "field measure status": physics.get("field_measure_status"),
            "BFP-angle Jacobian applied": physics.get("bfp_to_angle_jacobian_applied"),
            "detector mask units": physics.get("detector_mask_units"),
            "coordinate frame mapping": physics.get("coordinate_frame_mapping"),
            "joint overlap used": physics.get("joint_overlap_used"),
            "complex time convention": physics.get(
                "complex_time_harmonic_convention"
            ),
            "Fourier sign convention": physics.get(
                "fourier_transform_sign_convention"
            ),
            "Mie amplitude convention": physics.get(
                "mie_amplitude_phase_convention"
            ),
            "interference conjugation": physics.get(
                "interference_conjugation_convention"
            ),
            "interference cross-term convention": physics.get(
                "interference_cross_term_convention"
            ),
            "global phase source": physics.get("global_phase_offset_source"),
            "absolute polarity claim": physics.get("absolute_polarity_claim"),
            "complex convention status": physics.get("complex_convention_status"),
            "complex field claim": physics.get("complex_field_claim_level"),
            "polarization basis model": physics.get("polarization_basis_model"),
            "Jones basis status": physics.get("jones_basis_status"),
            "vector optics mode": physics.get("vector_optics_mode"),
            "polarization Jones operator": physics.get(
                "polarization_jones_operator_mode"
            ),
            "polarization overlap efficiency": physics.get(
                "polarization_overlap_efficiency"
            ),
            "phase/polarization quantitative claim allowed": physics.get(
                "phase_polarization_quantitative_claim_allowed"
            ),
            "phase/polarization claim blockers": physics.get(
                "phase_polarization_claim_blocker_summary"
            ),
            "Mie S1/S2 basis mapping": physics.get("mie_s1_s2_lab_basis_mapping"),
            "active Mie basis component": physics.get("active_mie_basis_component"),
            "S1/S2 lab rotation applied": physics.get(
                "S1S2_to_lab_basis_rotation_applied"
            ),
            "reference Jones field defined": physics.get("reference_jones_field_defined"),
            "detector analyzer Jones matrix defined": physics.get(
                "detector_analyzer_jones_matrix_defined"
            ),
            "Mie/Jones bridge status": physics.get("mie_jones_bridge_status"),
            "high NA scalar warning": physics.get("high_NA_collection_warning"),
            "vector validity status": physics.get("vector_validity_status"),
            "Mie incident field model": physics.get("incident_field_model_for_mie"),
            "local plane wave validity": physics.get("local_plane_wave_validity"),
            "Mie radius / beam waist": physics.get(
                "mie_radius_to_beam_waist_ratio"
            ),
            "Mie field gradient status": physics.get(
                "mie_field_gradient_across_particle_status"
            ),
            "Mie incident GLMT required": physics.get(
                "mie_incident_field_GLMT_required"
            ),
            "Mie incident full-wave required": physics.get(
                "mie_incident_field_fullwave_required"
            ),
            "Mie incident field claim": physics.get("mie_incident_field_claim_level"),
            "Mie incident blockers": physics.get(
                "mie_incident_field_blocker_summary"
            ),
            "calibration state machine": physics.get(
                "calibration_state_machine_status"
            ),
            "output claim level": physics.get("output_claim_level"),
            "calibrated quantitative unlocked": physics.get(
                "calibrated_quantitative_unlocked"
            ),
            "output claim blockers": physics.get("output_claim_blocker_summary"),
            "scattering normalization route": physics.get(
                "scattering_normalization_route"
            ),
            "scattering normalization status": physics.get(
                "scattering_normalization_status"
            ),
            "scattering calibration level": physics.get("scattering_calibration_level"),
            "baseline normalization role": physics.get("baseline_normalization_role"),
            "baseline absolute scale restored": physics.get(
                "baseline_particle_absolute_scale_restored"
            ),
            "baseline E_sca allowed in photon route": physics.get(
                "baseline_normalized_E_sca_allowed_in_photon_unit_route"
            ),
            "K_sca calibration status": physics.get("K_sca_calibration_status"),
            "standard particle calibration row": physics.get(
                "standard_particle_calibration_row_id"
            ),
            "standard particle calibration role": physics.get(
                "standard_particle_calibration_data_role"
            ),
            "Bayesian calibration status": physics.get(
                "bayesian_calibration_status"
            ),
            "Bayesian posterior available": physics.get(
                "bayesian_posterior_available"
            ),
            "posterior predictive score p10": physics.get(
                "posterior_predictive_design_score_p10"
            ),
            "Bayesian calibration blockers": physics.get(
                "bayesian_calibration_blocker_summary"
            ),
            "experimental design advisor": physics.get(
                "experimental_design_advisor_status"
            ),
            "next experiment priority": physics.get("next_experiment_priority"),
            "value of information score": physics.get("value_of_information_score"),
            "VOI priority reason": physics.get("next_experiment_priority_reason"),
            "objective panel status": physics.get("objective_panel_status"),
            "objective panel recommendation": physics.get(
                "objective_panel_recommendation"
            ),
            "objective panel score": physics.get("objective_panel_recommended_score"),
            "population inference status": physics.get("population_inference_status"),
            "population inference gate": physics.get(
                "population_inference_gate_passed"
            ),
            "control interpretation status": physics.get(
                "control_interpretation_status"
            ),
            "control interpretation claim": physics.get(
                "control_interpretation_claim_level"
            ),
            "control high-risk families": physics.get(
                "control_failure_interpretation_high_risk_controls"
            ),
            "control interpretation gate": physics.get(
                "control_failure_interpretation_gate_passed"
            ),
            "control interpretation blockers": physics.get(
                "control_interpretation_blocker_summary"
            ),
            "fluidic network status": physics.get("fluidic_network_model_status"),
            "fluidic network claim": physics.get("fluidic_network_claim_level"),
            "fluidic network external geometry": physics.get(
                "fluidic_network_external_geometry_status"
            ),
            "fluidic network pressure-flow relation": physics.get(
                "fluidic_network_pressure_flow_relation_status"
            ),
            "fluidic network pressure-flow gate": physics.get(
                "fluidic_network_gate_passed"
            ),
            "fluidic network blockers": physics.get(
                "fluidic_network_blocker_summary"
            ),
            "K_sca value": physics.get("K_sca_value"),
            "K_sca role": physics.get("K_sca_role"),
            "Mie-to-power chain": physics.get("mie_to_power_chain_status"),
            "detector-unit chain": physics.get("detector_unit_chain_status"),
            "detector-unit blockers": physics.get(
                "detector_unit_chain_blocker_summary"
            ),
            "scattered power conversion": physics.get(
                "scattered_power_conversion_status"
            ),
            "detector field units": physics.get("detector_field_units"),
            "power-chain absolute units": physics.get(
                "power_chain_absolute_units_available"
            ),
            "K_sca power-chain role": physics.get("K_sca_power_chain_role"),
            "Mie-to-power blockers": physics.get(
                "mie_to_power_chain_blocker_summary"
            ),
            "standard particle calibration coverage": physics.get(
                "standard_particle_calibration_coverage_status"
            ),
            "global phase offset calibration": physics.get(
                "global_phase_offset_calibration_status"
            ),
            "K_sca uncertainty status": physics.get("K_sca_uncertainty_status"),
            "K_sca uncertainty propagated": physics.get(
                "K_sca_uncertainty_propagated_to_outputs"
            ),
            "standard particle uncertainty budget": physics.get(
                "standard_particle_uncertainty_budget_status"
            ),
            "standard particle size distribution": physics.get(
                "standard_particle_size_distribution_status"
            ),
            "standard particle shape uncertainty": physics.get(
                "standard_particle_shape_uncertainty_status"
            ),
            "standard particle ligand shell": physics.get(
                "standard_particle_ligand_shell_status"
            ),
            "standard particle batch": physics.get("standard_particle_batch_status"),
            "standard particle concentration uncertainty": physics.get(
                "standard_particle_concentration_uncertainty_status"
            ),
            "standard particle material uncertainty": physics.get(
                "standard_particle_material_dataset_uncertainty_status"
            ),
            "calibration design rank": physics.get("calibration_design_rank"),
            "calibration standards": physics.get("calibration_standard_count"),
            "calibration wavelengths": physics.get("calibration_wavelength_count"),
            "calibration geometries": physics.get("calibration_geometry_count"),
            "calibration held-out status": physics.get(
                "calibration_held_out_validation_status"
            ),
            "calibration held-out error": physics.get("calibration_held_out_error"),
            "calibration identifiability blockers": physics.get(
                "calibration_identifiability_blocker_summary"
            ),
            "calibration fit parameter coupling": physics.get(
                "calibration_fit_parameter_coupling_status"
            ),
            "calibration minimum requirement": physics.get(
                "calibration_design_minimum_requirement_status"
            ),
            "fit parameters identifiable": physics.get("fit_parameters_identifiable"),
            "detector calibration level": physics.get("detector_calibration_level"),
            "readout calibration level": physics.get("readout_calibration_level"),
            "count calibration level": physics.get("count_calibration_level"),
            "noise model route": physics.get("noise_model_route"),
            "detector noise claim": physics.get("detector_noise_claim_level"),
            "absolute throughput route": physics.get("absolute_throughput_route"),
            "absolute throughput calibrated": physics.get(
                "absolute_throughput_calibrated"
            ),
            "photon-unit noise model": physics.get("photon_unit_noise_model_status"),
            "noise terms schema": physics.get("noise_terms_schema_version"),
            "noise term quantitative contribution": physics.get(
                "noise_term_quantitative_contribution_status"
            ),
            "lock-in ENBW Hz": physics.get("lockin_ENBW_Hz"),
            "lock-in ENBW status": physics.get("lockin_ENBW_status"),
            "lock-in ENBW claim": physics.get("lockin_ENBW_claim_level"),
            "shot noise model": physics.get("shot_noise_model_status"),
            "photon shot noise term": physics.get("photon_shot_noise_term_status"),
            "electronics noise model": physics.get("electronics_noise_model_status"),
            "electronics noise term": physics.get("electronics_noise_term_status"),
            "RIN noise model": physics.get("rin_noise_model_status"),
            "RIN noise term": physics.get("rin_noise_term_status"),
            "speckle background noise model": physics.get(
                "speckle_background_noise_model_status"
            ),
            "speckle-like noise term": physics.get("speckle_like_noise_term_status"),
            "drift noise term": physics.get("drift_noise_term_status"),
            "lock-in output noise term": physics.get(
                "lockin_output_noise_term_status"
            ),
            "detector dynamic range model": physics.get(
                "detector_dynamic_range_model"
            ),
            "detector saturation status": physics.get("detector_saturation_status"),
            "dynamic range margin": physics.get("dynamic_range_margin"),
            "ADC dynamic range status": physics.get("ADC_dynamic_range_status"),
            "reference enhancement gain": physics.get("reference_enhancement_gain"),
            "reference enhancement SNR claim": physics.get(
                "reference_enhancement_snr_claim"
            ),
            "background field model": physics.get("background_field_model"),
            "background field status": physics.get("background_field_status"),
            "background claim level": physics.get("background_claim_level"),
            "residual transmitted leakage": physics.get(
                "residual_transmitted_leakage_status"
            ),
            "stray light status": physics.get("stray_light_status"),
            "blank trace empirical available": physics.get(
                "blank_trace_empirical_available"
            ),
            "particle-induced channel perturbation": physics.get(
                "particle_induced_channel_phase_perturbation_status"
            ),
            "NODI signal component model": physics.get("nodi_signal_component_model"),
            "NODI signal component status": physics.get("nodi_signal_component_status"),
            "NODI forward extinction leakage": physics.get(
                "nodi_forward_extinction_leakage_status"
            ),
            "NODI transmitted leakage component": physics.get(
                "nodi_transmitted_leakage_component_status"
            ),
            "NODI particle-channel coupling": physics.get(
                "nodi_particle_induced_channel_coupling_status"
            ),
            "NODI signal component claim": physics.get(
                "nodi_signal_component_claim_level"
            ),
            "independent superposition status": physics.get(
                "independent_superposition_status"
            ),
            "superposition validity status": physics.get(
                "superposition_validity_status"
            ),
            "E_sca/E_ref amplitude estimate": physics.get(
                "E_sca_to_E_ref_amplitude_ratio_estimate"
            ),
            "extinction-to-beam-area estimate": physics.get(
                "extinction_to_beam_area_estimate"
            ),
            "reference depletion estimate": physics.get(
                "reference_depletion_fraction_estimate"
            ),
            "reference depletion estimate status": physics.get(
                "reference_depletion_estimate_status"
            ),
            "channel-particle coupling model": physics.get(
                "channel_particle_coupling_model"
            ),
            "joint fullwave required for quantitative phase": physics.get(
                "joint_fullwave_required_for_quantitative_phase"
            ),
            "superposition validity claim": physics.get(
                "superposition_validity_claim_level"
            ),
            "superposition validity blockers": physics.get(
                "superposition_validity_blocker_summary"
            ),
            "readout preset": physics.get("readout_preset"),
            "readout preset status": physics.get("readout_preset_status"),
            "readout preset claim": physics.get("readout_preset_claim_level"),
            "readout threshold scope": physics.get("readout_preset_threshold_scope"),
            "readout shared threshold profile": physics.get(
                "readout_shared_threshold_profile"
            ),
            "readout lane-specific thresholds available": physics.get(
                "readout_lane_specific_thresholds_available"
            ),
            "readout frequency leakage note": physics.get(
                "readout_preset_frequency_leakage_note"
            ),
            "electronics demod phase policy": physics.get(
                "electronics_demod_phase_policy"
            ),
            "effective demod phase policy": physics.get(
                "effective_electronics_demod_phase_policy"
            ),
            "readout polarity": physics.get("readout_polarity"),
            "polarity source": physics.get("polarity_source"),
            "arrival phase distribution": physics.get("arrival_phase_distribution"),
            "NODI random phase average gain": physics.get(
                "nodi_random_arrival_phase_average_gain"
            ),
            "NODI random phase magnitude bias": physics.get(
                "nodi_random_arrival_phase_magnitude_bias"
            ),
            "NODI random-vs-locked disagreement": physics.get(
                "nodi_random_vs_locked_disagreement"
            ),
            "NODI random-vs-locked claim degraded": physics.get(
                "nodi_random_vs_locked_claim_degraded"
            ),
            "readout internal sampling Hz": physics.get(
                "readout_internal_sampling_rate_Hz"
            ),
            "readout output sampling Hz": physics.get(
                "readout_output_sampling_rate_Hz"
            ),
            "readout max lock-in frequency Hz": physics.get(
                "readout_max_lockin_frequency_Hz"
            ),
            "readout oversampling ratio": physics.get(
                "readout_sampling_oversampling_ratio"
            ),
            "readout carrier Nyquist resolved": physics.get(
                "readout_carrier_nyquist_resolved"
            ),
            "readout carrier resolved": physics.get("readout_carrier_resolved"),
            "readout analytic demod used": physics.get(
                "readout_analytic_demod_used"
            ),
            "readout demod route": physics.get("readout_internal_demod_route"),
            "readout anti-alias policy": physics.get("readout_anti_alias_policy"),
            "readout sampling validity": physics.get("readout_sampling_validity"),
            "lock-in output unit convention": physics.get(
                "lockin_output_unit_convention"
            ),
            "lock-in gain chain": physics.get("lockin_gain_chain"),
            "lock-in reported channel": physics.get("lockin_reported_channel"),
            "lock-in measured voltage comparable": physics.get(
                "lockin_measured_voltage_comparable"
            ),
            "readout model claim": physics.get("readout_model_claim_level"),
            "POD source model status": physics.get("pod_source_model_status"),
            "NODI source model status": physics.get("nodi_source_model_status"),
            "thermal POD model": physics.get("thermal_pod_model"),
            "thermal POD status": physics.get("thermal_pod_model_status"),
            "POD quantitative amplitude available": physics.get(
                "pod_quantitative_amplitude_available"
            ),
            "POD quantitative sign available": physics.get(
                "pod_quantitative_sign_available"
            ),
            "POD quantitative claim": physics.get("pod_quantitative_claim_level"),
            "POD quantitative route status": physics.get(
                "pod_quantitative_route_status"
            ),
            "thermal POD API boundary": physics.get("thermal_pod_api_boundary_status"),
            "thermal POD missing inputs": physics.get("thermal_pod_missing_inputs"),
            "POD amplitude model boundary": physics.get(
                "pod_amplitude_model_boundary"
            ),
            "probe wavelength m": physics.get("probe_wavelength_m"),
            "excitation wavelength m": physics.get("excitation_wavelength_m"),
            "POD probe reference field status": physics.get(
                "pod_probe_reference_field_status"
            ),
            "probe/excitation wavelength status": physics.get(
                "pod_probe_excitation_wavelength_status"
            ),
            "POD wavelength grouping status": physics.get(
                "pod_wavelength_grouping_status"
            ),
            "probe coherent field group": physics.get("probe_coherent_field_group_id"),
            "excitation incoherent power group": physics.get(
                "excitation_incoherent_power_group_id"
            ),
            "multi-wavelength coherent policy": physics.get(
                "multi_wavelength_coherent_addition_policy"
            ),
            "POD ROI derivative status": physics.get(
                "pod_roi_sensitivity_derivative_status"
            ),
            "POD sign source": physics.get("pod_signal_sign_source"),
            "raw blank trace bootstrap": physics.get(
                "raw_blank_trace_bootstrap_status"
            ),
            "blank FP calibration role": physics.get(
                "blank_false_positive_calibration_data_role"
            ),
            "POD thermal spatial status": physics.get(
                "pod_thermal_spatial_distribution_status"
            ),
            "POD ROI derivative validity": physics.get("pod_roi_derivative_validity"),
            "POD absorption cross-section status": physics.get(
                "pod_excitation_absorption_cross_section_status",
                physics.get("pod_absorption_cross_section_status"),
            ),
            "POD heat source status": physics.get("pod_heat_source_status"),
            "POD heat diffusion status": physics.get("pod_heat_diffusion_status"),
            "POD solvent dn/dT status": physics.get("pod_solvent_dn_dT_status"),
            "POD detector responsivity status": physics.get(
                "pod_detector_responsivity_status"
            ),
            "POD spectral filter status": physics.get("pod_spectral_filter_status"),
            "POD modulation response status": physics.get(
                "pod_modulation_response_status"
            ),
            "POD thermal validation status": physics.get("pod_thermal_validation_status"),
            "POD amplitude blockers": physics.get(
                "pod_amplitude_quantitative_blocker_summary"
            ),
            "threshold sigma": physics.get("threshold_sigma"),
            "threshold tail": physics.get("threshold_tail"),
            "threshold tail status": physics.get("threshold_tail_status"),
            "threshold sign": physics.get("threshold_sign"),
            "threshold polarity mode": physics.get("threshold_polarity_mode"),
            "threshold lane-specific model": physics.get(
                "threshold_lane_specific_model"
            ),
            "threshold from blank trace": physics.get("threshold_from_blank_trace"),
            "threshold background source": physics.get("threshold_background_source"),
            "threshold background samples": physics.get(
                "threshold_background_segment_samples"
            ),
            "threshold calibration source": physics.get(
                "threshold_calibration_source"
            ),
            "threshold calibration status": physics.get(
                "threshold_calibration_status"
            ),
            "blank false-positive calibration": physics.get(
                "blank_false_positive_calibration_status"
            ),
            "blank false-positive calibration id": physics.get(
                "blank_false_positive_calibration_id"
            ),
            "Gaussian iid sample false alarm": physics.get(
                "gaussian_iid_single_sample_false_alarm_probability"
            ),
            "Gaussian iid segment false alarm": physics.get(
                "gaussian_iid_background_segment_false_alarm_probability"
            ),
            "blank trace autocorrelation time s": physics.get(
                "blank_trace_autocorrelation_time_s"
            ),
            "effective independent samples per trace": physics.get(
                "effective_independent_samples_per_trace"
            ),
            "lock-in filter order": physics.get("lockin_filter_order"),
            "empirical peak false alarm per minute": physics.get(
                "empirical_peak_false_alarm_rate_per_minute"
            ),
            "empirical pair false alarm per minute": physics.get(
                "empirical_pair_false_alarm_rate_per_minute"
            ),
            "lane noise correlation coefficient": physics.get(
                "lane_noise_correlation_coefficient"
            ),
            "colored-noise false alarm model": physics.get(
                "colored_noise_false_alarm_model"
            ),
            "colored-noise false alarm status": physics.get(
                "colored_noise_false_alarm_status"
            ),
            "colored-noise threshold bias": physics.get(
                "colored_noise_threshold_bias"
            ),
            "colored-noise threshold bias status": physics.get(
                "colored_noise_threshold_bias_status"
            ),
            "paired false alarm status": physics.get("paired_false_alarm_status"),
            "g_ref": physics.get("g_ref"),
            "A_ref": physics.get("A_ref"),
            "reference route": physics.get("reference_route"),
            "reference claim level": physics.get("reference_claim_level"),
            "reference solver route": physics.get("reference_solver_route"),
            "reference solver status": physics.get("reference_solver_status"),
            "reference solver bridge": physics.get(
                "reference_solver_detector_bridge_status"
            ),
            "phase-filter validity": physics.get("phase_filter_validity"),
            "phase-filter H/lambda0": physics.get("phase_filter_H_over_lambda0"),
            "phase-filter delta ref rad": physics.get("phase_filter_delta_ref_rad"),
            "phase-filter signed theta rad": physics.get(
                "phase_filter_theta_signed_rad"
            ),
            "phase-filter H/zR": physics.get("phase_filter_H_over_zR"),
            "phase-filter multiple reflection": physics.get(
                "phase_filter_multiple_reflection_warning"
            ),
            "subwavelength groove validity": physics.get(
                "subwavelength_groove_validity_status"
            ),
            "finite length assumption": physics.get("finite_length_assumption_status"),
            "sidewall roughness status": physics.get(
                "sidewall_scattering_roughness_status"
            ),
            "evanescent component unmodeled": physics.get(
                "evanescent_component_unmodeled"
            ),
            "groove waveguide mode unmodeled": physics.get(
                "groove_waveguide_mode_unmodeled"
            ),
            "roughness scatter unmodeled": physics.get("roughness_scatter_unmodeled"),
            "depth validity reason": physics.get("depth_validity_reason"),
            "requires calibration/full-wave": physics.get(
                "requires_calibration_or_fullwave"
            ),
            "reference calibration amplitude": physics.get(
                "reference_calibration_amplitude_status"
            ),
            "reference calibration coverage": physics.get(
                "reference_calibration_coverage_status"
            ),
            "reference phase calibration": physics.get(
                "reference_phase_calibration_status"
            ),
            "reference projection basis": physics.get("reference_projection_basis"),
            "reference effective basis": physics.get("reference_effective_basis"),
            "reference/scattering basis match": physics.get("reference_projection_basis_match"),
            "reference projection coupling status": physics.get(
                "reference_projection_coupling_status"
            ),
            "path OPD freeze status": physics.get(
                "path_opd_freeze_status",
                summary.get("path_opd_freeze_status"),
            ),
            "interference overlap freeze status": physics.get(
                "interference_overlap_default_freeze_status",
                summary.get("interference_overlap_default_freeze_status"),
            ),
            "projection freeze status": physics.get(
                "projection_default_freeze_status",
                summary.get("projection_default_freeze_status"),
            ),
            "delta_phi_gouy validity": physics.get(
                "delta_phi_gouy_validity",
                summary.get("delta_phi_gouy_validity"),
            ),
            "delta_phi_gouy width/waist": physics.get(
                "delta_phi_gouy_geometry_width_to_waist_ratio",
                summary.get("delta_phi_gouy_geometry_width_to_waist_ratio"),
            ),
            "delta_phi_gouy depth/waist": physics.get(
                "delta_phi_gouy_geometry_depth_to_waist_ratio",
                summary.get("delta_phi_gouy_geometry_depth_to_waist_ratio"),
            ),
            "observation freeze status": physics.get(
                "observation_freeze_status",
                summary.get("observation_freeze_status"),
            ),
            "design recommendation": physics.get(
                "design_recommendation_label",
                summary.get("design_recommendation_label"),
            ),
            "design recommendation status": physics.get(
                "design_recommendation_status",
                summary.get("design_recommendation_status"),
            ),
            "engineering gate blocker": physics.get(
                "engineering_gate_primary_blocker_label",
                summary.get("engineering_gate_primary_blocker_label"),
            ),
            "engineering gate guidance": physics.get(
                "engineering_gate_guidance",
                summary.get("engineering_gate_guidance"),
            ),
            "reference model tier": physics.get("reference_model_precision_tier"),
            "reference model role": physics.get("reference_model_role"),
            "mean I_baseline": summary.get("mean_I_baseline"),
            "mean shot-noise std": summary.get("mean_shot_noise_std"),
            "mean A_ref(local)": summary.get("mean_A_ref_local"),
            "mean A_sca(local)": summary.get("mean_A_sca_local"),
            "mean |E_ref|/|E_sca|": summary.get(
                "mean_reference_to_scattering_amplitude_ratio"
            ),
            "rho requested": physics.get("rho_requested", summary.get("rho_requested")),
            "rho envelope nominal": physics.get(
                "rho_physical_envelope_nominal",
                summary.get("rho_physical_envelope_nominal"),
            ),
            "rho envelope status": physics.get(
                "rho_physical_envelope_status",
                summary.get("rho_physical_envelope_status"),
            ),
            "reference width saturation status": physics.get(
                "reference_width_saturation_status"
            ),
            "reference width saturation factor": physics.get(
                "reference_width_saturation_factor"
            ),
            "NA cutoff policy": physics.get("na_cutoff_policy"),
            "NA cutoff active": physics.get("na_cutoff_active"),
            "NA hard zero applied": physics.get("na_cutoff_hard_zero_applied"),
            "NA cutoff collection NA": physics.get("na_cutoff_NA_collection"),
            "sigma_effective (deg)": (
                float(np.degrees(physics.get("sigma_effective_rad")))
                if physics.get("sigma_effective_rad") is not None
                else None
            ),
        },
        "batch_outcome": {
            "score": case_data.get("score"),
            "final_engineering_score": case_data.get("final_engineering_score"),
            "engineering_score": case_data.get("engineering_score"),
            "engineering_decision_basis": case_data.get("engineering_decision_basis"),
            "engineering_gate_passed": case_data.get("engineering_gate_passed"),
            "engineering_gate_basis": case_data.get("engineering_gate_basis"),
            "engineering_gate_reason": case_data.get("engineering_gate_reason"),
            "engineering_gate_primary_blocker_label": case_data.get("engineering_gate_primary_blocker_label"),
            "engineering_gate_blocker_summary": case_data.get("engineering_gate_blocker_summary"),
            "engineering_gate_required_detected_events": case_data.get("engineering_gate_required_detected_events"),
            "engineering_gate_detected_fraction_lb": case_data.get("engineering_gate_detected_fraction_lb"),
            "engineering_gate_stable_detection_rate_lb": case_data.get(
                "engineering_gate_stable_detection_rate_lb"
            ),
            "engineering_gate_phase_flip_fraction_ub": case_data.get(
                "engineering_gate_phase_flip_fraction_ub"
            ),
            "engineering_gate_mean_peak_margin_z": case_data.get(
                "engineering_gate_mean_peak_margin_z"
            ),
            "engineering_gate_strict_paired_rate_lb": case_data.get("engineering_gate_strict_paired_rate_lb"),
            "engineering_gate_required_strict_paired_detection_rate": case_data.get(
                "engineering_gate_required_strict_paired_detection_rate"
            ),
            "stable_detection_rate": summary.get("stable_detection_rate"),
            "hit_rate_at_fixed_false_alarm": summary.get("hit_rate_at_fixed_false_alarm"),
            "roc_auc_event_vs_background": summary.get("roc_auc_event_vs_background"),
            "mean_positive_peak_height": summary.get("mean_positive_peak_height"),
            "mean_negative_peak_height": summary.get("mean_negative_peak_height"),
            "positive_peak_fraction": summary.get("positive_peak_fraction"),
            "negative_peak_fraction": summary.get("negative_peak_fraction"),
            "n_detected": summary.get("n_detected"),
            "phase_flip_fraction": summary.get("phase_flip_fraction"),
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
            "paired_detection_rate": summary.get("paired_detection_rate"),
        },
    }


# ============================================================
# Parameter tuning support (V7)
# ============================================================

def build_sim_cfg_from_ui(
    rho, ref_alpha, ref_beta, ref_gamma,
    noise_std, drift_slope, threshold_sigma,
    velocity_mm_s, include_diffusion,
    reference_model, coupling_model,
    normalization_mode, noise_model,
):
    """Build SimulationConfig from UI control values."""
    from nodi_simulator.dashboard.config import DEFAULT_SIM_CFG
    cfg = deepcopy(DEFAULT_SIM_CFG)
    # Live sweep currently explores one user-selected particle at a time.
    cfg.score_mode = "single"
    cfg.rho = rho
    cfg.ref_alpha = ref_alpha
    cfg.ref_beta = ref_beta
    cfg.ref_gamma = ref_gamma
    cfg.noise_std = noise_std
    cfg.drift_slope = drift_slope
    cfg.threshold_sigma = threshold_sigma
    cfg.mean_flow_velocity_m_s = velocity_mm_s * 1e-3
    cfg.reference_model = reference_model
    cfg.coupling_model = coupling_model
    cfg.normalization_mode = normalization_mode
    cfg.noise_model = noise_model
    cfg.include_diffusion = include_diffusion
    return cfg


def build_optical_from_ui(beam_waist_y_nm):
    """Build OpticalSystem from UI beam_waist_y value."""
    from nodi_simulator.dashboard.config import OPTICAL_TEMPLATE
    opt = deepcopy(OPTICAL_TEMPLATE)
    opt.beam_waist_y_m = beam_waist_y_nm * 1e-9
    opt.illumination_beam_waist_y_m = beam_waist_y_nm * 1e-9
    return opt


def build_live_tag(sim_cfg):
    """Generate a readable tag string for live sweep identification."""
    parts = [f"rho{sim_cfg.rho:.0f}"]
    if sim_cfg.reference_model == "geometry_scaled":
        parts.append(f"a{sim_cfg.ref_alpha:.1f}b{sim_cfg.ref_beta:.1f}g{sim_cfg.ref_gamma:.1f}")
    parts.append(f"n{sim_cfg.noise_std:.3f}")
    if sim_cfg.include_diffusion:
        parts.append("diff")
    parts.append(sim_cfg.reference_model[:4])
    parts.append(sim_cfg.coupling_model[:4])
    parts.append(datetime.now().strftime("%H%M%S"))
    return "_".join(parts)


def run_live_sweep(sim_cfg, optical_template, particle, grid_name="coarse"):
    """
    Run a named preset sweep with custom parameters.

    Returns:
        (DataFrame, list[dict]) summary df and compact list.
    """
    from nodi_simulator.dashboard.config import GRID_CONFIGS

    return run_live_sweep_custom(
        sim_cfg,
        optical_template,
        particle,
        {
            **GRID_CONFIGS[grid_name],
            "grid_name": grid_name,
        },
    )


def build_local_fine_grid(center_W_nm, center_H_nm, half_window_nm=200, step_nm=100, n_events=20):
    """Build a local fine grid by clipping the standard fine grid around one center point."""
    from nodi_simulator.dashboard.config import GRID_CONFIGS

    step_nm = max(1, int(step_nm))
    center_W_nm = float(center_W_nm)
    center_H_nm = float(center_H_nm)
    half_window_nm = max(0.0, float(half_window_nm))

    fine_grid = GRID_CONFIGS["fine"]
    width_nm = np.round(np.asarray(fine_grid["width_list_m"], dtype=float) * 1e9).astype(int)
    depth_nm = np.round(np.asarray(fine_grid["depth_list_m"], dtype=float) * 1e9).astype(int)

    width_mask = np.abs(width_nm - center_W_nm) <= half_window_nm + 1e-9
    depth_mask = np.abs(depth_nm - center_H_nm) <= half_window_nm + 1e-9

    width_selected = width_nm[width_mask]
    depth_selected = depth_nm[depth_mask]

    if width_selected.size == 0:
        width_selected = np.array([int(width_nm[np.argmin(np.abs(width_nm - center_W_nm))])], dtype=int)
    if depth_selected.size == 0:
        depth_selected = np.array([int(depth_nm[np.argmin(np.abs(depth_nm - center_H_nm))])], dtype=int)

    return {
        "width_list_m": np.asarray(width_selected, dtype=float) * 1e-9,
        "depth_list_m": np.asarray(depth_selected, dtype=float) * 1e-9,
        "wavelength_list_m": np.asarray(fine_grid["wavelength_list_m"], dtype=float),
        "n_events": int(n_events),
        "grid_name": "local_fine",
        "center_W_nm": center_W_nm,
        "center_H_nm": center_H_nm,
        "half_window_nm": half_window_nm,
        "step_nm": float(step_nm),
    }


def _run_sweep_grid(sim_cfg, optical_template, particle, grid: dict):
    from nodi_simulator.dashboard.config import (
        BASELINE_PARTICLE,
        MEDIUM,
        THETA_GRID_RAD,
        medium_for_particle,
    )
    from nodi_simulator.dashboard.precompute import results_to_compact, results_to_dataframe
    from nodi_simulator import BASELINE_CHANNEL, run_parameter_sweep, validate_simulation_config

    sim_cfg_run = deepcopy(sim_cfg)
    sim_cfg_run.n_events = int(grid["n_events"])
    sim_cfg_run.score_mode = "single"

    try:
        validate_simulation_config(sim_cfg_run, optical_template)
    except ValueError as exc:
        raise ValueError(
            "Current parameter combination violates physical validation. "
            f"Original validation error: {exc}. "
            "Check beam_waist_y, velocity, or total_time."
        ) from exc

    results = run_parameter_sweep(
        particle_types=[particle],
        medium=MEDIUM,
        medium_resolver=medium_for_particle,
        width_list_m=np.asarray(grid["width_list_m"], dtype=float),
        depth_list_m=np.asarray(grid["depth_list_m"], dtype=float),
        wavelength_list_m=np.asarray(grid["wavelength_list_m"], dtype=float),
        optical_template=optical_template,
        sim_cfg=sim_cfg_run,
        theta_grid_rad=THETA_GRID_RAD,
        baseline_particle=BASELINE_PARTICLE,
        baseline_channel=BASELINE_CHANNEL,
        verbose=False,
    )
    return results_to_dataframe(results), results_to_compact(results)


def run_live_sweep_custom(sim_cfg, optical_template, particle, grid: dict):
    """Run a custom sweep grid with the same output format as run_live_sweep."""
    return _run_sweep_grid(sim_cfg, optical_template, particle, grid)


def run_case_on_demand(particle_name, wavelength_nm, W_nm, H_nm):
    """Recompute one detail case using the active live config when available."""
    import streamlit as st

    from nodi_simulator.data_objects import Channel
    from nodi_simulator.dashboard.config import (
        BASELINE_PARTICLE,
        OPTICAL_TEMPLATE,
        THETA_GRID_RAD,
        medium_for_particle,
        particle_from_name,
    )
    from nodi_simulator.parameter_sweep import run_single_case_batch
    from nodi_simulator.utils import (
        compute_baseline_normalization,
        compute_baseline_normalization_per_wavelength,
        validate_simulation_config,
    )
    from nodi_simulator import BASELINE_CHANNEL, DEFAULT_SIM_CFG

    if st.session_state.get("using_live_data"):
        sim_cfg = deepcopy(st.session_state.live_sim_cfg)
        optical = deepcopy(st.session_state.live_optical)
    else:
        sim_cfg = deepcopy(DEFAULT_SIM_CFG)
        optical = deepcopy(OPTICAL_TEMPLATE)

    optical.wavelength_m = float(wavelength_nm) * 1e-9
    channel = Channel(width_m=float(W_nm) * 1e-9, depth_m=float(H_nm) * 1e-9)
    particle = particle_from_name(particle_name)
    case_medium = medium_for_particle(particle)

    validate_simulation_config(sim_cfg, optical)

    if sim_cfg.normalization_mode == "per_wavelength":
        ref_map = compute_baseline_normalization_per_wavelength(
            BASELINE_PARTICLE,
            case_medium,
            OPTICAL_TEMPLATE,
            np.array([optical.wavelength_m]),
            THETA_GRID_RAD,
            channel=BASELINE_CHANNEL,
            sim_cfg=sim_cfg,
        )
        E_sca_ref = float(ref_map[float(optical.wavelength_m)])
    else:
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            case_medium,
            optical,
            THETA_GRID_RAD,
            channel=BASELINE_CHANNEL,
            sim_cfg=sim_cfg,
        )
        E_sca_ref = float(baseline["E_sca_ref"])

    return run_single_case_batch(
        particle,
        case_medium,
        channel,
        optical,
        sim_cfg,
        E_sca_ref,
        THETA_GRID_RAD,
    )
