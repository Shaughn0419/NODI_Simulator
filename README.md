# NODI Interferometric Simulator

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

> 文档角色：仓库入口与快速总览。当前事实以 2026-05-02 selected-annulus governance、lower-is-better joint-fit score、claim compatibility 与 sensitivity smoke 同步为准。

This repository simulates nanoparticle transit events in a NODI-type nanochannel detection zone. It compares channel width, depth, wavelength, particle model, reference route, readout settings, and detection statistics through a reproducible sweep / dashboard workflow.

## Repository Scope

This GitHub repository is intended to track source code, tests, lightweight configuration, calibration templates, and human-readable documentation. Large generated artifacts stay local by default:

- virtual environments and dependency caches: `.venv/`, `.venv-tests/`, `.pytest_vendor/`
- local agent/runtime state: `.omx/`, `.claude/`
- scratch and computed outputs: `tmp/`, `results/`, `exports/`, `.pdf_output/`
- paper binaries: `papers/*.pdf`, `papers/*.docx`
- historical computed artifacts under `archive/`, except markdown audit notes

If a generated result is needed for long-term provenance, prefer documenting the command, inputs, metadata, and summary in markdown instead of committing large binary or CSV outputs.

## Quick Start

Requires Python `>=3.13`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the dashboard:

```bash
streamlit run dashboard/app.py
```

Run the standard local checks:

```bash
ruff check .
python -m pyright
pytest -q
```

## Current Status

- The old Tsuyama alignment fixes formerly tracked in [43_Tsuyama对齐主链升级路线图与修改框架.md](./43_Tsuyama对齐主链升级路线图与修改框架.md) have been implemented and archived. File 43 is now the EV/NODI design-decision roadmap.
- Current governed metadata target is `schema 1.24`.
- The previous full database prefix `fine_full_range_biomimetic_exosome_10000e_*` has been superseded by the EV design anchor library prefix `ev_design_full_range_biomimetic_exosome_with_anchors_10000e_*`.
- File 43 is frozen as the v5 EV/NODI design-decision roadmap. Its non-measured P0-hard gates, minimum required schema, P0-soft blockers, smoke-critical dashboard/export paths, and P1 diagnostic/scaffold lanes are now in place for the next relative/proxy/diagnostic full recompute.
- The recompute path is now fixed on the current safe full-run engine: `standard` artifact profile, per-case `TrajectoryContext`, worker-local intrinsic/reference/operator caches, summary-only streaming, and dashboard/precompute `vectorized_event_engine="off"` with `event_block_size=32` and `event_block_rng_order="event_loop_order"`.
- Event-block engines and the faster `block_lane_order` RNG experiment remain opt-in only. The 16C/32T 10000-event probe found scalar/off faster than `event_block_v3_b32`, while `block_lane_order` changed detection, stable detection, peak height, peak width, and engineering gate agreement, so neither is the formal full-run default.
- EV relative design governance is split from absolute/global green claims: detector-operator disagreement now creates detector caution fields instead of hard-blocking relative ranking, while `final_green_eligible` remains reserved for stricter absolute/global claims.
- A measured/calibrated `bfp_roi_mask_path` now affects the Tsuyama BFP reference integral through a 1D projected ROI lane (`calibrated_bfp_roi_mask_projected_1d`); synthetic mask templates remain contract-only and do not alter physics outputs.
- Tsuyama selected detector-mode is now a parallel analysis lens: `detection_rate` remains the all-crossing engineering-gate/main-score rate, while selected-candidate and edge-norm annulus conditional rates are exported and can drive separate EV targeted/full-grid ranking comparisons for cross-checking. The annulus bounds are recorded in `SimulationConfig.selected_annulus_edge_norm_min/max` and default to `0.5-0.8`; empty annulus denominators export and remain `NaN` through gold-lane flattening and route analysis rather than fabricated zero-rate selected results. `dashboard.precompute` now carries these fields through summary / compact / diagnostics-long exports, so the next full-grid recompute will materialize selected-annulus source columns directly in the full summary; stale pre-2026-05-01 inputs are explicitly marked unavailable/null instead of being backfilled into fake selected-annulus rankings.
- Tsuyama geometry labels have been corrected: the 2022 NODI paper geometry is `800 / 1200 nm` wide and `550 nm` deep with 488 / 532 / 660 nm measurement/comparison coverage, while the 2024 paired POD+NODI paper uses `800-1200 nm` wide and `550 nm` deep channels with a 660 nm probe. `800x710 nm` belongs to the 2020 POD counting paper and is treated only as a POD bridge / sensitivity case, not as NODI exact geometry.
- Tsuyama 2022 Supplementary Table S1 fixed-index Au/Ag profile is available for paper-claim audit only. It improves the 660 nm Ag/Au mean-peak ratio; numeric alignment to Fig. 5 / Table S1 signal ratios should now go through the explicit selected-annulus joint-fit lane and its residual transfer/interference calibration terms.
- `tools/tsuyama_selected_annulus_joint_fit.py` now provides the explicit selected-annulus Tsuyama paper-fit lane. Schema v2 scores both 800x550 and 1200x550 paper geometries for selected-annulus detection rates, Ag/Au peak ratios, Au size scaling, and Au30/Au20 SNR ratio across Au `20/30/40/60 nm` and Ag `40/60 nm` current joint-fit diagnostics. Variants ending in `signal_transfer_fit` apply bounded paper-fit silver transfer gains; variants ending in `signal_size_transfer_fit` additionally apply a bounded Au power-law size-response correction. `joint_fit_score` is a lower-is-better loss-style penalty, not a reward score. Size-response correction is clipped to the declared exponent-delta guardrail before scoring, and guardrail violations cannot be labeled as paper-fit pass. Selected-annulus metadata now uses centralized claim/target governance: `paper_aligned_2022_nodi_proxy_lens` against `tsuyama_2022_nodi_table_s1`, with readout-layer target metadata validated per raw row.
- all-crossing remains an engineering gate and primary ranking lens, not a paper detection-rate target. The selected-annulus 2022 NODI paper-audit lane currently uses Au20 `0.30`, Au30 `0.60`, Au40 `0.78`, and Au60 `0.92` surrogate detection-rate targets from the joint-fit code; the 2020 POD near-100% Au20 thermal-counting conclusion is a different mechanism and is not a NODI calibration anchor. Joint-fit variants that switch to `in_phase + absolute` readout are now rejected early because they violate the current `magnitude + positive` paper-target metadata guard.
- `tools/tsuyama_2022_classification_lane.py` exports a separate linked 488/532 feature/protocol table for the 2022 Au40/Au60/Ag40/Ag60 classification claim. It now uses the detected 488 pulse window as the event window and records the 532 maximum within that window. The `400` events/class v2 smoke produced `1600` linked rows and `849` paper-SVM-usable rows; SVM accuracy remains unavailable only because `scikit-learn` is not a project dependency.
- `results/tsuyama_selected_annulus_pre_fullgrid_ev_robustness_20260501/` records the pre-fullgrid EV robustness audit: `nodi_2022_5sigma_single_sensitivity`, `3000` events per seed, seeds `42 / 314 / 2718`, `8` workers. All-crossing and selected-annulus top1 routes were seed-stable across all four EV size priors, with selected-annulus top1 = `488 nm / 600x1500 nm`.
- `results/selected_annulus_fullchain_dryrun_20260501_v2/` records the small full-chain dry run before full recompute: `coarse + quick`, `128` cases, `30` events/case, `8` workers. It verifies precompute save -> EV route analysis -> selected-annulus ranking comparison end to end; selected-annulus lens is available for all `64` EV route rows and all `4` size priors.
- `results/tsuyama_annulus_ratio_sensitivity_smoke_20260502/` records a low-event true smoke of the annulus ratio sensitivity path with `8` workers and two seeds. It validates real compute -> raw -> per-seed summary -> seed aggregate -> meta/decision output, including lower-is-better score direction, scenario ID, target metadata guard, and current Au/Ag particle-size diagnostics. It is intentionally not a canonical annulus-ratio decision.
- Historical probe/smoke selected-annulus outputs have been moved from `results/` to `archive/tsuyama/probe_pre_20260502/` for audit-only retention.
- Dashboard long-form diagnostics and schema inventory now export the full `DESIGN_CLAIM_GOVERNANCE_FIELDS`, including detector-caution fields.
- P2/P3 remain data-blocked unless real blank / standard-particle / BFP ROI / lock-in transfer / detector-unit data or high-fidelity solvers are supplied. Synthetic templates and surrogate lanes must not be read as calibrated SNR, absolute LOD, absolute EV concentration, cross-wavelength detector-unit ranking, or biological EV specificity.

## Start Here

1. [文档导航.md](./文档导航.md)  
   Task-based map of current, historical, and archived docs.
2. [24_高性能预计算与增量重算方案.md](./24_高性能预计算与增量重算方案.md)  
   The current full-recompute execution guide.
3. [42_全量重算前复核结论与现行边界.md](./42_全量重算前复核结论与现行边界.md)  
   Final pre-recompute judgment and remaining boundaries.
4. [43_Tsuyama对齐主链升级路线图与修改框架.md](./43_Tsuyama对齐主链升级路线图与修改框架.md)  
   EV/NODI design-decision roadmap: EV ensemble aggregation, standard-particle ladder, selection bias, event QC, reporting readiness, assay controls, wavelength/objective claim blockers, readout semantics, BFP mode-overlap, exposure safety, consensus, and advisor outputs.

## Result Library Target

The next formal full recompute should recreate:

- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_design_postprocess.csv`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_compact.pkl`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_meta.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_result_health.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_runtime_performance.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_freeze_probe.json`

`dashboard.precompute` now defaults to the `standard` artifact profile for full recompute exports, so duplicate `case_summary` and heavy parquet split exports are intentionally skipped unless `--artifact-profile full` is explicitly requested.

Expected scope:

- grid: `ev_design`
- particle profile: `full_range_biomimetic_exosome_with_anchors`
- wavelengths: `404 / 488 / 532 / 660 nm`
- particles: Au20/Au30 anchors plus gold and biomimetic EV/sEV exosome-like particles, `40-300 nm`
- channels: `W = 500 / 600 / 700 / 800 / 900 / 1000 / 1100 / 1200 / 1300 / 1400 / 1500 nm`; `H = 500 / 550 / 600 / 650 / 700 / 800 / 900 / 1000 / 1100 / 1200 / 1300 / 1400 / 1500 nm`
- events per case: `10000`
- cases: `32032`
- recommended 16C/32T full-run launch: `NUMBA_NUM_THREADS=4`, `--workers 28`, `--vectorized-event-engine off`

EV optical-uncertainty variant:

- particle profile: `ev_design_biomimetic_ensemble_with_anchors`
- particles: Au20/Au30 anchors, gold `40-300 nm`, and four literature-bounded biomimetic EV optical presets at `50-150 nm`
- cases on the same `ev_design` grid: `41756`
- use this profile when `ev_score_min / ev_score_p10` must reflect EV optical-model uncertainty rather than only size uncertainty.

## Documentation Layers

- Same-basename module docs, for example [parameter_sweep.md](./parameter_sweep.md), explain the adjacent Python module.
- [guides/core/](./guides/core/README.md) contains longer core-physics guides.
- [guides/operations/](./guides/operations/README.md) contains testing, calibration-data, and workflow guidance.
- [reports/current/](./reports/current/README.md) contains still-useful current notes; reports tied to the deleted old full library are marked as historical snapshots.
- [archive/](./archive/README.md) contains historical notes and should not be treated as current truth.

## Verification Baseline

Current verification pass used:

- `ruff check .`
- `pyright` → `0 errors, 0 warnings, 0 informations`
- `pytest -q` → `563 passed`, with no warnings
- `PYTHONPATH=. python -m dashboard.precompute --grid coarse --particle-profile quick --tag codex_ev_design_smoke_20260426 --workers 8 --artifact-profile minimal --output tmp/codex_ev_design_smoke --progress-interval 1` → `128 cases` saved with `EV_NODI_only_design`, `magnitude`, `flux_weighted`, `off`, and `event_loop_order` recorded in metadata
- production-code `bandit` → passed after excluding virtualenv, vendor, archive, tmp, results, and tests
- Previous dependency audit reported only `pip 26.0.1 / CVE-2026-3219` with no Fix Versions.
- Latest 16C/32T recompute performance pass: at `10000` events/case, scalar/off completed the 64-case probe in `74.062 s`, while `event_block_v3_b32` took `131.048 s` and `event_block_v3_b16` took `107.604 s`; formal full recompute therefore defaults to scalar/off.

Do not treat template calibration rows as measured data. They are deliberately marked as synthetic fixtures and do not unlock calibrated quantitative claims.
