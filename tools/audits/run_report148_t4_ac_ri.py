#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportCallIssue=false, reportArgumentType=false, reportGeneralTypeIssues=false
from __future__ import annotations

import argparse
import hashlib
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import THETA_GRID_RAD, medium_for_particle, particle_from_name  # noqa: E402
from nodi_simulator.parameter_sweep import run_single_case_batch_shared_event_normalization_views  # noqa: E402
from nodi_simulator.structured_particles import make_biomimetic_exosome_particle, resolve_structured_particle_spec  # noqa: E402
from tools._common import write_json_file  # noqa: E402
from tools.audits import tsuyama_gold_aligned_detection_lane as lane  # noqa: E402
from tools.audits.run_report148_stage1_ab_minimal import (  # noqa: E402
    NORMALIZATION_VIEWS,
    PRIOR_NAME,
    READOUT_POLICY,
    ROUTE_MODEL_CATALOG,
    _build_route_cfg,
    _rank_routes_for_group,
    default_route_panel,
)
from tools.lens_b_ev_gold_fullgrid_runner import _fixed_660_e_sca_ref, _per_wavelength_e_sca_ref  # noqa: E402


OUTPUT_DIR_DEFAULT = Path("results/audits") / f"report148_t4_ac_ri_{datetime.now().strftime('%Y%m%d')}"
DETECTOR_ROUTE_IDS = ("A_hybrid", "C_collapsed_coherent")
GAUGE_MODE = "V1_gauge_locked"
NOISE_POLICY = "common_noise_control"
EV_DIAMETERS_NM = (80, 120, 160)
GOLD_ANCHOR_NAMES = ("gold_20nm", "gold_40nm", "gold_60nm")
PRESETS = (
    "membrane_only_dim_2021",
    "membrane_only_nominal_2020",
    "biomimetic_corona_nominal",
    "surface_loaded_bright_2021",
)
CORE_N_REAL_VALUES = (1.36, 1.38, 1.40)
CORONA_LABELS = ("absent", "nominal", "protein_rich")
CORONA_THICKNESS_M = {
    "absent": 0.0,
    "nominal": 4e-9,
    "protein_rich": 8e-9,
}
BASELINE_COMBO = (
    "biomimetic_corona_nominal",
    1.38,
    "nominal",
)
SEED11 = 11
PROMOTED_SEEDS = (22, 33)


@dataclass(frozen=True)
class CaseTask:
    route: tuple[int, int, int]
    particle: Any
    seed: int
    detector_route_id: str
    n_events: int


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _particle_metadata(particle: Any) -> dict[str, Any]:
    params = dict(particle.structure_params or {})
    preset_name = str(params.get("preset_name", "not_applicable"))
    core_n_real = params.get("core_n_real")
    corona_thickness_nominal = params.get("corona_thickness_m")
    corona_label = str(params.get("t4_corona_label", "not_applicable"))
    return {
        "particle_name": particle.name,
        "particle_family": "gold" if "gold" in particle.name else "EV_sEV",
        "particle_diameter_nm": float(particle.radius_m * 2e9),
        "preset_name": preset_name,
        "core_n_real": (float(core_n_real) if core_n_real is not None else None),
        "corona_label": corona_label,
        "corona_thickness_nominal_m": (
            float(corona_thickness_nominal)
            if corona_thickness_nominal is not None
            else None
        ),
    }


def build_ev_particles() -> list[Any]:
    particles: list[Any] = []
    for preset_name in PRESETS:
        for core_n_real in CORE_N_REAL_VALUES:
            for corona_label in CORONA_LABELS:
                overrides = {
                    "core_n_real": float(core_n_real),
                    "corona_thickness_m": float(CORONA_THICKNESS_M[corona_label]),
                    "t4_corona_label": str(corona_label),
                }
                if corona_label == "protein_rich":
                    overrides["corona_n_real"] = 1.40
                    overrides["edl_refractive_increment"] = 0.005
                for diameter_nm in EV_DIAMETERS_NM:
                    particles.append(
                        make_biomimetic_exosome_particle(
                            diameter_nm,
                            name=(
                                f"exosome_t4_{preset_name}_core{core_n_real:.2f}_"
                                f"{corona_label}_{int(diameter_nm)}nm"
                            ),
                            preset_name=preset_name,
                            overrides=overrides,
                        )
                    )
    return particles


def build_gold_particles() -> list[Any]:
    return [particle_from_name(name) for name in GOLD_ANCHOR_NAMES]


def _route_family_lookup(route_key: tuple[int, int, int]) -> tuple[str, str]:
    for route in default_route_panel():
        if (route.wavelength_nm, route.width_nm, route.depth_nm) == route_key:
            return route.route_family_id, route.route_family_note
    raise ValueError(f"route family not found for route {route_key}")


def _run_case_task(task: CaseTask) -> list[dict[str, Any]]:
    particle = task.particle
    medium = medium_for_particle(particle)
    wavelength_nm, width_nm, depth_nm = task.route
    route_family_id, route_family_note = _route_family_lookup(task.route)
    channel = lane.case_baseline_channel(width_nm, depth_nm)
    structured_spec = None
    if getattr(particle, "model_type", "") == "mie_core_shell":
        optical_medium_n = float(medium.refractive_index_at(float(wavelength_nm) * 1e-9))
        structured_spec = resolve_structured_particle_spec(
            particle,
            optical_medium_n,
            float(wavelength_nm) * 1e-9,
        )
    view_configs: dict[str, Any] = {}
    e_sca_refs: dict[str, float] = {}
    for normalization_view in NORMALIZATION_VIEWS:
        cfg, optical_template = _build_route_cfg(
            n_events=int(task.n_events),
            seed=task.seed,
            detector_route_id=task.detector_route_id,
            detector_forward_model=ROUTE_MODEL_CATALOG[task.detector_route_id],
            normalization_lane=normalization_view,
        )
        view_configs[normalization_view] = cfg
        if normalization_view == "fixed_660_gold":
            e_sca_refs[normalization_view] = _fixed_660_e_sca_ref(
                width_nm=width_nm,
                depth_nm=depth_nm,
                cfg=cfg,
                optical_template=optical_template,
            )
        else:
            e_sca_refs[normalization_view] = _per_wavelength_e_sca_ref(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                medium=medium,
                cfg=cfg,
                optical_template=optical_template,
            )
    optical = optical_template
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    outputs = run_single_case_batch_shared_event_normalization_views(
        particle,
        medium,
        channel,
        optical,
        view_configs,
        e_sca_refs,
        THETA_GRID_RAD,
    )
    meta = _particle_metadata(particle)
    rows: list[dict[str, Any]] = []
    for normalization_view, payload in outputs.items():
        summary = payload["summary"]
        spec = structured_spec or {}
        rows.append(
            {
                "detector_route_id": task.detector_route_id,
                "detector_forward_model": ROUTE_MODEL_CATALOG[task.detector_route_id],
                "gauge_mode": GAUGE_MODE,
                "readout_policy": READOUT_POLICY,
                "normalization_view": normalization_view,
                "seed": int(task.seed),
                "wavelength_nm": int(wavelength_nm),
                "width_nm": int(width_nm),
                "depth_nm": int(depth_nm),
                "route_family_id": route_family_id,
                "route_family_note": route_family_note,
                "noise_policy": NOISE_POLICY,
                **meta,
                "corona_thickness_resolved_m": spec.get("corona_thickness_resolved_m"),
                "membrane_thickness_resolved_m": spec.get("membrane_thickness_resolved_m"),
                "edl_thickness_resolved_m": spec.get("edl_thickness_resolved_m"),
                "surface_layer_scale_factor": spec.get("surface_layer_scale_factor"),
                "surface_layer_clipped_flag": spec.get("surface_layer_clipped_flag"),
                "core_radius_fraction_resolved": spec.get("core_radius_fraction_resolved"),
                "structured_particle_preset_name": spec.get("preset_name"),
                "detection_rate": float(summary["detection_rate"]),
                "stable_detection_rate": float(summary["stable_detection_rate"]),
                "detection_rate_wilson_lb": float(summary["detection_rate_wilson_lb"]),
                "stable_detection_rate_wilson_lb": float(summary["stable_detection_rate_wilson_lb"]),
                "mean_peak_margin_z": float(summary["mean_peak_margin_z"]),
                "selected_detector_mode_annulus_detection_rate": float(summary["selected_detector_mode_annulus_detection_rate"]),
                "selected_detector_mode_annulus_detection_rate_wilson_lb": float(summary["selected_detector_mode_annulus_detection_rate_wilson_lb"]),
                "selected_detector_mode_annulus_fraction": float(summary["selected_detector_mode_annulus_fraction"]),
                "selected_detector_mode_annulus_mean_edge_norm": float(summary["selected_detector_mode_annulus_mean_edge_norm"]),
                "selected_detector_mode_annulus_n_events": int(summary["selected_detector_mode_annulus_n_events"]),
                "selected_detector_mode_annulus_n_detected": int(summary["selected_detector_mode_annulus_n_detected"]),
                "reference_operating_band": str(summary.get("reference_operating_band")),
                "engineering_gate_passed": bool(summary.get("engineering_gate_passed")),
                "strict_ok": bool(
                    bool(summary.get("engineering_gate_passed"))
                    and not bool(summary.get("na_cutoff_active"))
                    and str(summary.get("rho_physical_envelope_status")) == "within_envelope"
                ),
                "all_crossing_detection_rate": float(summary["all_crossing_detection_rate"]),
                "final_engineering_score": float(summary["mean_peak_margin_z"]),
                "route_screening_claim_level": "candidate_families_under_current_detector_surrogate_A_vs_C_EV_RI_screening",
                "route_screening_status": "t4_seed_screening",
            }
        )
    return rows


def _rank_combo_group(group: pd.DataFrame) -> pd.DataFrame:
    ev_only = group[group["particle_family"].astype(str).eq("EV_sEV")].copy()
    ranked = _rank_routes_for_group(ev_only)
    return ranked


def _winner_rows(case_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in case_df.groupby(
        [
            "detector_route_id",
            "normalization_view",
            "seed",
            "preset_name",
            "core_n_real",
            "corona_label",
            "wavelength_nm",
        ],
        sort=True,
    ):
        route_id, view, seed, preset_name, core_n_real, corona_label, wavelength_nm = keys
        ranked = _rank_combo_group(group)
        if ranked.empty:
            continue
        top = ranked.iloc[0]
        rows.append(
            {
                "detector_route_id": route_id,
                "normalization_view": view,
                "seed": int(seed),
                "preset_name": preset_name,
                "core_n_real": float(core_n_real),
                "corona_label": corona_label,
                "wavelength_nm": int(wavelength_nm),
                "winner_family_id": str(top["route_family_id"]),
                "winner_route": f"{int(top['wavelength_nm'])}/{int(top['width_nm'])}x{int(top['depth_nm'])}",
                "selected_annulus_rank": int(top["selected_annulus_rank"]),
                "weighted_selected_annulus_detection": float(top[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]),
                "weighted_stable": float(top[f"{PRIOR_NAME}_weighted_stable"]),
                "weighted_final": float(top[f"{PRIOR_NAME}_weighted_final"]),
            }
        )
    return pd.DataFrame(rows)


def _view_flip_rows(winner_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in winner_df.groupby(
        ["detector_route_id", "seed", "preset_name", "core_n_real", "corona_label"],
        sort=True,
    ):
        route_id, seed, preset_name, core_n_real, corona_label = keys
        winners = {
            (row["normalization_view"], int(row["wavelength_nm"])): row
            for row in group.to_dict("records")
        }
        required = {
            ("fixed_660_gold", 404),
            ("fixed_660_gold", 660),
            ("per_wavelength_gold", 404),
            ("per_wavelength_gold", 660),
        }
        if set(winners) != required:
            continue
        fixed_404 = winners[("fixed_660_gold", 404)]
        fixed_660 = winners[("fixed_660_gold", 660)]
        per_404 = winners[("per_wavelength_gold", 404)]
        per_660 = winners[("per_wavelength_gold", 660)]
        fixed_winner = fixed_404 if fixed_404["weighted_selected_annulus_detection"] >= fixed_660["weighted_selected_annulus_detection"] else fixed_660
        per_winner = per_404 if per_404["weighted_selected_annulus_detection"] >= per_660["weighted_selected_annulus_detection"] else per_660
        rows.append(
            {
                "detector_route_id": route_id,
                "seed": int(seed),
                "preset_name": preset_name,
                "core_n_real": float(core_n_real),
                "corona_label": corona_label,
                "fixed_660_gold_winner_wavelength": int(fixed_winner["wavelength_nm"]),
                "fixed_660_gold_winner_family_id": fixed_winner["winner_family_id"],
                "per_wavelength_gold_winner_wavelength": int(per_winner["wavelength_nm"]),
                "per_wavelength_gold_winner_family_id": per_winner["winner_family_id"],
                "view_flip_flag": int(fixed_winner["wavelength_nm"]) != int(per_winner["wavelength_nm"]),
            }
        )
    return pd.DataFrame(rows)


def _baseline_changed_combos(view_flip_df: pd.DataFrame) -> set[tuple[str, float, str]]:
    baseline = view_flip_df[
        view_flip_df["preset_name"].eq(BASELINE_COMBO[0])
        & view_flip_df["core_n_real"].eq(BASELINE_COMBO[1])
        & view_flip_df["corona_label"].eq(BASELINE_COMBO[2])
    ].copy()
    baseline_map = {
        row["detector_route_id"]: row
        for row in baseline.to_dict("records")
    }
    promoted: set[tuple[str, float, str]] = set()
    for row in view_flip_df.to_dict("records"):
        baseline_row = baseline_map.get(row["detector_route_id"])
        if baseline_row is None:
            continue
        changed = (
            row["fixed_660_gold_winner_wavelength"] != baseline_row["fixed_660_gold_winner_wavelength"]
            or row["per_wavelength_gold_winner_wavelength"] != baseline_row["per_wavelength_gold_winner_wavelength"]
            or row["fixed_660_gold_winner_family_id"] != baseline_row["fixed_660_gold_winner_family_id"]
            or row["per_wavelength_gold_winner_family_id"] != baseline_row["per_wavelength_gold_winner_family_id"]
            or bool(row["view_flip_flag"]) != bool(baseline_row["view_flip_flag"])
        )
        if changed:
            promoted.add((row["preset_name"], float(row["core_n_real"]), row["corona_label"]))
    return promoted


def _build_tasks(
    *,
    particles: list[Any],
    seeds: tuple[int, ...],
    n_events: int,
) -> list[CaseTask]:
    routes = [(route.wavelength_nm, route.width_nm, route.depth_nm) for route in default_route_panel()]
    return [
        CaseTask(
            route=route,
            particle=particle,
            seed=seed,
            detector_route_id=route_id,
            n_events=int(n_events),
        )
        for route_id in DETECTOR_ROUTE_IDS
        for seed in seeds
        for route in routes
        for particle in particles
    ]


def _run_tasks(tasks: list[CaseTask], workers: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for batch_rows in executor.map(_run_case_task, tasks):
                rows.extend(batch_rows)
    else:
        for task in tasks:
            rows.extend(_run_case_task(task))
    return pd.DataFrame(rows)


def _combo_particles(ev_particles: list[Any], combo: tuple[str, float, str]) -> list[Any]:
    preset_name, core_n_real, corona_label = combo
    selected: list[Any] = []
    for particle in ev_particles:
        meta = _particle_metadata(particle)
        if (
            meta["preset_name"] == preset_name
            and float(meta["core_n_real"]) == float(core_n_real)
            and meta["corona_label"] == corona_label
        ):
            selected.append(particle)
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run report 148 T4 EV-RI sensitivity for routes A and C.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR_DEFAULT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--n-events", type=int, default=2000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    ev_particles = build_ev_particles()
    gold_particles = build_gold_particles()
    seed11_df = _run_tasks(
        _build_tasks(
            particles=ev_particles + gold_particles,
            seeds=(SEED11,),
            n_events=int(args.n_events),
        ),
        workers=int(args.workers),
    )
    winner_seed11 = _winner_rows(seed11_df)
    view_flip_seed11 = _view_flip_rows(winner_seed11)
    promoted_combos = _baseline_changed_combos(view_flip_seed11)

    promoted_df = pd.DataFrame()
    if promoted_combos:
        promoted_particles: list[Any] = []
        for combo in sorted(promoted_combos):
            promoted_particles.extend(_combo_particles(ev_particles, combo))
        promoted_particles.extend(gold_particles)
        promoted_df = _run_tasks(
            _build_tasks(
                particles=promoted_particles,
                seeds=PROMOTED_SEEDS,
                n_events=int(args.n_events),
            ),
            workers=int(args.workers),
        )

    case_df = pd.concat([seed11_df, promoted_df], ignore_index=True)
    winner_df = _winner_rows(case_df)
    view_flip_df = _view_flip_rows(winner_df)

    case_df.to_csv(output_dir / "report148_t4_ac_case_rows.csv", index=False)
    winner_df.to_csv(output_dir / "report148_t4_ac_winner_rows.csv", index=False)
    view_flip_df.to_csv(output_dir / "report148_t4_ac_view_flip_rows.csv", index=False)

    route_disagreement_rows: list[dict[str, Any]] = []
    for keys, group in view_flip_df.groupby(["preset_name", "core_n_real", "corona_label", "seed"], sort=True):
        preset_name, core_n_real, corona_label, seed = keys
        winners = {row["detector_route_id"]: row for row in group.to_dict("records")}
        if set(winners) != set(DETECTOR_ROUTE_IDS):
            continue
        a_row = winners["A_hybrid"]
        c_row = winners["C_collapsed_coherent"]
        route_disagreement_rows.append(
            {
                "preset_name": str(preset_name),
                "core_n_real": float(core_n_real),
                "corona_label": str(corona_label),
                "seed": int(seed),
                "A_fixed_winner": a_row["fixed_660_gold_winner_family_id"],
                "A_per_winner": a_row["per_wavelength_gold_winner_family_id"],
                "A_view_flip_flag": bool(a_row["view_flip_flag"]),
                "C_fixed_winner": c_row["fixed_660_gold_winner_family_id"],
                "C_per_winner": c_row["per_wavelength_gold_winner_family_id"],
                "C_view_flip_flag": bool(c_row["view_flip_flag"]),
                "route_disagreement_present": (
                    a_row["fixed_660_gold_winner_family_id"] != c_row["fixed_660_gold_winner_family_id"]
                    or a_row["per_wavelength_gold_winner_family_id"] != c_row["per_wavelength_gold_winner_family_id"]
                    or bool(a_row["view_flip_flag"]) != bool(c_row["view_flip_flag"])
                ),
            }
        )
    route_disagreement_df = pd.DataFrame(route_disagreement_rows)
    route_disagreement_df.to_csv(output_dir / "report148_t4_ac_route_disagreement.csv", index=False)

    summary_rows: list[dict[str, Any]] = []
    for route_id, group in view_flip_df.groupby("detector_route_id", sort=True):
        fixed_mode = group["fixed_660_gold_winner_family_id"].mode().iat[0]
        per_mode = group["per_wavelength_gold_winner_family_id"].mode().iat[0]
        any_change = bool(
            (group["fixed_660_gold_winner_family_id"] != fixed_mode).any()
            or (group["per_wavelength_gold_winner_family_id"] != per_mode).any()
            or (group["view_flip_flag"] != group["view_flip_flag"].mode().iat[0]).any()
        )
        summary_rows.append(
            {
                "summary_kind": "ev_ri_route_summary",
                "detector_route_id": route_id,
                "ev_ri_winner_stability_class": (
                    "ri_sensitive_winner_or_flip_change"
                    if any_change
                    else "ri_stable_winner_and_flip"
                ),
                "ev_ri_flip_change_flag": bool(
                    group["view_flip_flag"].nunique() > 1 or not bool(group["view_flip_flag"].mode().iat[0])
                ),
                "fixed_660_gold_winner_family_mode": fixed_mode,
                "per_wavelength_gold_winner_family_mode": per_mode,
                "rows": int(len(group)),
            }
        )
    if not route_disagreement_df.empty:
        summary_rows.append(
            {
                "summary_kind": "route_disagreement_summary",
                "detector_route_id": "A_vs_C",
                "ev_ri_winner_stability_class": None,
                "ev_ri_flip_change_flag": None,
                "fixed_660_gold_winner_family_mode": None,
                "per_wavelength_gold_winner_family_mode": None,
                "rows": int(len(route_disagreement_df)),
                "route_disagreement_stable_across_ri": bool(route_disagreement_df["route_disagreement_present"].nunique() == 1),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_dir / "report148_t4_ac_summary.csv", index=False)

    manifest = {
        "generated_at": _utc_now_iso(),
        "output_dir": str(output_dir),
        "detector_route_ids": list(DETECTOR_ROUTE_IDS),
        "gauge_mode": GAUGE_MODE,
        "normalization_views": list(NORMALIZATION_VIEWS),
        "baseline_combo": {
            "preset_name": BASELINE_COMBO[0],
            "core_n_real": BASELINE_COMBO[1],
            "corona_label": BASELINE_COMBO[2],
            "baseline_selection_status": "inferred_nominal_reference_combo",
        },
        "ev_diameters_nm": list(EV_DIAMETERS_NM),
        "gold_anchor_names": list(GOLD_ANCHOR_NAMES),
        "promoted_combos": [
            {
                "preset_name": combo[0],
                "core_n_real": combo[1],
                "corona_label": combo[2],
            }
            for combo in sorted(promoted_combos)
        ],
        "seed11_only_rows": int(len(seed11_df)),
        "promoted_rows": int(len(promoted_df)),
        "workers": int(args.workers),
        "n_events": int(args.n_events),
    }
    write_json_file(output_dir / "report148_t4_ac_manifest.json", manifest)


if __name__ == "__main__":
    main()
