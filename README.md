# NODI Interferometric Simulator

This repository simulates NODI-style nanochannel interferometric detection for
nanoparticles and EV-like particles. It contains the forward model, parameter
sweeps, dashboard tooling, test suite, and reader-facing analysis reports.

The current project state is:

- **v1 is the baseline relative simulation library.** It covers `32,032`
  source design cases with `10,000` synthetic events per case.
- **v2 is a no-measured-data realism supplement.** It adds instrument-aware
  constraints, route governance, blank/thermal guardrails, near-wall mesh
  adjudication, width-risk sensitivity, and artifact-gap registration.
- **post-v2 P0-P18 is a relative-audit and bounded-trace evidence layer.** It
  adds the P0 review-ready audit package plus six bounded trace-only lanes; it
  does not promote a route because the two legacy 660-family candidates swap
  rank across P6/P8/P10/P12/P14/P16.
- **The current reader-facing analysis is a no-data closure, not a route winner
  declaration.** Report 140 is now aligned to reports 147/148: the 3-seed,
  10,000 events/case exhaustive EV+gold full-grid is retained as evidence, but
  its fixed/per-wavelength rankings are interpreted as detector-surrogate
  candidate-family evidence. The no-data sealing gate is narrowed to `R2/V1`
  A/B/C/D all-3-seed primary decision plus A/B V2 gauge-sampling; R1 and
  C/D×V2 are explicitly deferred out of the no-data gate.
- **The older τ=1 ms B6/B7 Lens-B reads remain historical single-seed
  overlays.** B6 per-wavelength gold normalization is still useful for
  Tsuyama-lineage geometry diagnostics; B7 fixed-660-gold normalization was the
  previous low-event cross-wavelength decision overlay. Both are now superseded
  for robust Lens-B interpretation by the 3-seed 10000e post-run analysis.
  EV recommendations use EV/exosome rows only; gold rows are diagnostic anchors
  only. The old 2026-05-13 `10,000` events/case Lens-B full-grid remains a
  2 ms legacy sensitivity/reference run, not the current 1 ms decision lane.
- **The repository still has no measured acquisition data.** It does not
  authorize calibrated signal-to-noise ratio, calibrated event probability,
  absolute detection limit, true EV concentration, biological specificity,
  measured blank safety, route promotion, or legacy route-family redefinition.

For readers, start with the latest full-grid post-run analysis, then use the
older consolidated reports for background and provenance:

- [reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md](./reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md)
- [reports/147_detector_forward_identity_full_chain_adversarial_audit_synthesis_20260610.md](./reports/147_detector_forward_identity_full_chain_adversarial_audit_synthesis_20260610.md)
- [reports/148_extreme_simulation_roadmap_post_audit_20260610.md](./reports/148_extreme_simulation_roadmap_post_audit_20260610.md)
- [reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md](./reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md)
- [reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md](./reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md)

Report 140 is the current final reader-facing analysis. It confirms hard output
integrity with a raw/diagnostic schema caveat, then applies the 147/148
detector-identity closure: `fixed_660_gold` retains a 404 nm / W500
candidate family, `per_wavelength_gold` retains a 660 nm / W800 candidate
family, and Stage-1 prevents either from becoming a detector-resolved or
absolute winner because A/B/D preserve the view-flip while C gives 660 in both
views. Report 88 remains consolidated background; report 100 is historical.

For historical v2 boundary provenance, read:

- [reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md](./reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md)
- [reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md](./reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md)
- [reports/89_EV_NODI_post_v2_unmodeled_realism_register.md](./reports/89_EV_NODI_post_v2_unmodeled_realism_register.md)

## What This Repository Can Claim

Supported:

- relative simulation evidence;
- scenario-prior sensitivity under named synthetic instrument scenarios;
- route-role stability inside the bounded v2 prior model;
- post-v2 relative-audit records and trace-only rank-instability evidence;
- mesh/sign consistency checks for the legacy 660 nm route-family diagnostics;
- a low-dimensional explanation for why narrow/deep context routes scored high;
- Level-1 3-seed EV+gold route-family comparison under explicitly named
  normalization views;
- a concrete list of missing artifacts needed before physical calibration.

Not supported:

- calibrated signal-to-noise ratio;
- calibrated event probability;
- absolute detection limit;
- true EV concentration;
- biological specificity;
- measured blank safety;
- empirical route promotion;
- replacing all-crossing ranking with selected-annulus ranking, or the reverse;
- treating P6-P16 trace ordering as route promotion.
- treating Lens-B gold anchor geometry as an EV recommendation;
- double-counting `fixed_660_gold` and `per_wavelength_gold` as independent
  physical stochastic event campaigns;
- treating 488/532 raw or control wins as final recommendation wavelengths.

## Current Scientific Bottom Line

Within the no-measured-data closure, the current bottom line is:

- 404/W500 is a fixed-view detector-surrogate candidate family.
- 660/W800 is a per-wavelength detector-surrogate candidate family.
- Stage-1 detector-route audit prevents either family from being promoted to a
  detector-resolved or absolute 404/660 winner.
- Depth is a weak, calibration/noise-dependent engineering band; D900-D1200 is
  the conservative fabrication range, not a D1400/D1500 mandate.
- 488/532 remain control/reference wavelengths.

This is a no-data relative-audit final, not a physical or biological truth
closure. The remaining open axes are measurement-facing: detector identity
(BFP/slit/reference phase), cross-wavelength gauge, blank/noise/FPR, and EV
composition. R1 and C/D×V2 remain simulation-completable but are not blockers
for the no-data final.

## Quick Start

Requires Python `>=3.13`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Optional JIT acceleration is available when `numba` supports your Python and
platform:

```bash
python -m pip install -e ".[dev,acceleration]"
```

If `numba` is absent, the simulator still runs on the pure-Python / NumPy path
and now emits an explicit runtime warning for acceleration-backed kernels.

Run the dashboard:

```bash
streamlit run dashboard/app.py
```

Run standard checks:

```bash
ruff check .
python -m pyright
python -m mypy
python tests/run_tests.py --workers 7
```

The latest local cleanup/review baseline was:

- `ruff check .` -> pass
- `python -m pyright` -> `0 errors, 0 warnings` on the transitional typed seed allowlist in `pyrightconfig.json`
- `python -m mypy` -> pass on the same typed seed allowlist; full-repository type debt is not yet a release gate
- AppTest lane after pruning full-page-only checks -> `5 passed` in `3.67s`
- `python tests/run_tests.py --workers 7` is now bounded mostly by the non-AppTest xdist lane
- AppleDouble `._*` metadata files are ignored by source review, but can still
  reappear on mounted storage and break naive recursive tooling; prefer tracked
  file lists for compile/static checks.

## Documentation Map

- [文档导航.md](./文档导航.md): task-based navigation for active docs.
- [docs/PROJECT_ORGANIZATION_ROADMAP_2026-05-09.md](./docs/PROJECT_ORGANIZATION_ROADMAP_2026-05-09.md): staged file-organization and package-migration roadmap.
- [00_工程总指南.md](./00_工程总指南.md): engineering overview.
- [25_核心计算逻辑与公式总说明.md](./25_核心计算逻辑与公式总说明.md): core calculation and formulas.
- [34_完整全波理论推导与当前模型边界.md](./34_完整全波理论推导与当前模型边界.md): theory boundary.
- [guides/operations/14_测试说明.md](./guides/operations/14_测试说明.md): test operation notes.
- [guides/operations/15_无实测数据时如何接入未来校准数据.md](./guides/operations/15_无实测数据时如何接入未来校准数据.md): future calibration-data handoff boundary.
- [reports/89_EV_NODI_post_v2_unmodeled_realism_register.md](./reports/89_EV_NODI_post_v2_unmodeled_realism_register.md): post-v2 realism gaps acknowledged but not solved inside v2.
- [reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md](./reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md): current 3-seed 10000e EV+gold exhaustive full-grid audit and interpretation.
- [reports/141_full_project_code_doc_cleanup_audit_20260523.md](./reports/141_full_project_code_doc_cleanup_audit_20260523.md): 2026-05-23 code/documentation cleanup review ledger.
- [reports/142_current_documentation_status_audit_20260523.md](./reports/142_current_documentation_status_audit_20260523.md): 2026-05-23 per-Markdown-file currentness audit.
- [reports/143_project_productization_cleanup_20260523.md](./reports/143_project_productization_cleanup_20260523.md): 2026-05-23 productization cleanup ledger, artifact tiers, and next refactor queue.
- [reports/144_results_papers_internal_slimming_audit_20260523.md](./reports/144_results_papers_internal_slimming_audit_20260523.md): 2026-05-23 internal `results/` / `papers/` slimming candidates and risk tiers.
- [reports/121_EV_NODI_full_update_review_ledger_2026-05-11.md](./reports/121_EV_NODI_full_update_review_ledger_2026-05-11.md): 2026-05-11 full report merge, code-review ledger, documentation ledger, and verification record.
- [type_coerce.md](./type_coerce.md), [realism_v2_io.md](./realism_v2_io.md), and [optional_acceleration.md](./optional_acceleration.md): small shared helper modules introduced during the May 8 hardening pass. These helpers, plus realism-v2, data-object, utility, parameter-sweep, material, Mie, intrinsic-scattering, illumination, reference-field, trajectory, scattering-trace, interferometric-trace, pulse-analysis, population-trace, polarization-Jones, calibration, manifest, run-state, control, count, OOD, Bayesian, population, experimental-design, seed, geometry, fluidic, electrokinetic, optical-exposure, optical-hardware, objective-panel, wavelength-comparability, readout-transfer, BFP-detector, paper-aligned, Tsuyama phase-filter, count-generation, interface-correction, structured-particle, particle-design, design-metric, design-postprocess, design-claim, selection, reference-operating, particle-channel, NODI thermal, photothermal-POD, assay-control, event-QC, EV integrity, EV reporting, unit, detector-unit, and uncertainty helpers, are canonical under `nodi_simulator/`.
- Public package exports are maintained in `nodi_simulator/_exports.py`; root package-module compatibility wrappers have been retired.
- [docs/GENERATED_ARTIFACT_BOUNDARY.md](./docs/GENERATED_ARTIFACT_BOUNDARY.md): source-reviewed vs generated artifact boundary.
- [docs/POST_V2_ENTRYPOINTS.md](./docs/POST_V2_ENTRYPOINTS.md): post-v2 module/tool lifecycle and deletion policy.

The `docs/realism_v2/` files are contract/specification documents used by the
test suite. They are retained for governance and regression checks even when
the reader-facing storyline is now summarized by reports 140, 147, and 148.
Reports 84, 87, 88, the post-v2 gap register in report 89, and the P0-P18
reports 90-120 remain useful provenance, but they are no longer the current
conclusion entry point.

## Result Libraries

The baseline v1 library is stored under:

- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_*`

The v2 result lineage is stored under staged `results/ev_nodi_realism_v2_*`
directories. These are evidence artifacts, not reader entry points. Use the
reports above for interpretation.

The post-v2 result lineage is stored under `results/post_v2_*`. These artifacts
are review/audit/trace records. They are not measured data and must not be used
as calibrated detector output.

The current exhaustive Lens-B EV+gold 3-seed 10000e lineage is stored under
`results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed*_16worker_20260518`
and the paired aggregation directories
`results/exhaustive_ev_gold_fullgrid_shared_dual_3seed_10000e_*_aggregation_20260518`.
Use report 140 for interpretation rather than reading the raw CSVs directly.

## Repository Hygiene

Generated caches, local agents, virtual environments, review bundles, and large
computed artifacts should stay out of normal source review unless explicitly
needed for provenance:

- `.venv/`, `.venv-tests/`, `.pytest_cache/`
- `.omx/`, `.claude/`
- `tmp/`, `.pdf_output/`
- large generated files under `results/`, `exports/`, and `review_bundles/`

The 2026-05-23 productization cleanup pass removed safe local cache/export
noise and left `results/` / `papers/` intact pending hash-manifest
externalization. See report 143 before deleting large local runtime or evidence
directories.

Historical material under `archive/` is kept for provenance. Do not use archive
documents as current scientific truth unless the current reports explicitly
refer to them.
