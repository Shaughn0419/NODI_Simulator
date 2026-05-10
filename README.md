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
  does not promote a route because the two locked main-660 candidates swap
  rank across P6/P8/P10/P12/P14/P16.
- **The repository still has no measured acquisition data.** It does not
  authorize calibrated signal-to-noise ratio, calibrated event probability,
  absolute detection limit, true EV concentration, biological specificity,
  measured blank safety, route promotion, or main-660 redefinition.

For readers, start with the consolidated analysis:

- [reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md](./reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md)

That report is now the v3.0 current full-data reader report dated 2026-05-11:
it merges the v1 full-grid library, realism v2 closure, P0 review-ready
relative audit, and P1-P18 bounded physical-ceiling / trace-governance record.

For the final v2 boundary, read:

- [reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md](./reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md)
- [reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md](./reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md)
- [reports/89_EV_NODI_post_v2_unmodeled_realism_register.md](./reports/89_EV_NODI_post_v2_unmodeled_realism_register.md)

## What This Repository Can Claim

Supported:

- relative simulation evidence;
- scenario-prior sensitivity under named synthetic instrument scenarios;
- route-role stability inside the bounded v2 prior model;
- post-v2 relative-audit records and trace-only rank-instability evidence;
- mesh/sign consistency checks for the locked 660 nm main route;
- a low-dimensional explanation for why narrow/deep context routes scored high;
- a concrete list of missing artifacts needed before physical calibration.

Not supported:

- calibrated signal-to-noise ratio;
- calibrated event probability;
- absolute detection limit;
- true EV concentration;
- biological specificity;
- measured blank safety;
- empirical route promotion;
- replacing all-crossing ranking with selected-annulus ranking.
- treating P6-P16 trace ordering as route promotion.

## Current Scientific Bottom Line

Within the no-measured-data v2 model, the locked 660 nm main route remains:

- 660 nm wavelength, 800 nm width, 1400 nm depth;
- 660 nm wavelength, 800 nm width, 1500 nm depth.

The post-v2 P0 audit keeps those two routes as conditional relative-main
candidates. P6/P8 rank 800x1400 above 800x1500, P10/P12 reverse that order,
P14 returns to 800x1400, and P16 returns to 800x1500; the current bottom line
is therefore rank instability, not a single champion. The earlier
weak-reference and narrow/deep context-route warnings are best read as evidence
that the original model underweighted narrow-channel engineering risk. R6/R7
show that this warning is explainable by low-dimensional width-family and
mechanistic-prior hypotheses, but those hypotheses are not calibrated physical
laws.

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
- [reports/121_EV_NODI_full_update_review_ledger_2026-05-11.md](./reports/121_EV_NODI_full_update_review_ledger_2026-05-11.md): 2026-05-11 full report merge, code-review ledger, documentation ledger, and verification record.
- [type_coerce.md](./type_coerce.md), [realism_v2_io.md](./realism_v2_io.md), and [optional_acceleration.md](./optional_acceleration.md): small shared helper modules introduced during the May 8 hardening pass. These helpers, plus realism-v2, data-object, utility, parameter-sweep, material, Mie, intrinsic-scattering, illumination, reference-field, trajectory, scattering-trace, interferometric-trace, pulse-analysis, population-trace, polarization-Jones, calibration, manifest, run-state, control, count, OOD, Bayesian, population, experimental-design, seed, geometry, fluidic, electrokinetic, optical-exposure, optical-hardware, objective-panel, wavelength-comparability, readout-transfer, BFP-detector, paper-aligned, Tsuyama phase-filter, count-generation, interface-correction, structured-particle, particle-design, design-metric, design-postprocess, design-claim, selection, reference-operating, particle-channel, NODI thermal, photothermal-POD, assay-control, event-QC, EV integrity, EV reporting, unit, detector-unit, and uncertainty helpers, are canonical under `nodi_simulator/`.
- Public package exports are maintained in `nodi_simulator/_exports.py`; root package-module compatibility wrappers have been retired.

The `docs/realism_v2/` files are contract/specification documents used by the
test suite. They are retained for governance and regression checks even when
the reader-facing storyline is now summarized by reports 84, 87, 88, the
post-v2 gap register in report 89, and the P0-P18 reports 90-120.

## Result Libraries

The baseline v1 library is stored under:

- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_*`

The v2 result lineage is stored under staged `results/ev_nodi_realism_v2_*`
directories. These are evidence artifacts, not reader entry points. Use the
reports above for interpretation.

The post-v2 result lineage is stored under `results/post_v2_*`. These artifacts
are review/audit/trace records. They are not measured data and must not be used
as calibrated detector output.

## Repository Hygiene

Generated caches, local agents, virtual environments, review bundles, and large
computed artifacts should stay out of normal source review unless explicitly
needed for provenance:

- `.venv/`, `.venv-tests/`, `.pytest_cache/`
- `.omx/`, `.claude/`
- `tmp/`, `.pdf_output/`
- large generated files under `results/`, `exports/`, and `review_bundles/`

Historical material under `archive/` is kept for provenance. Do not use archive
documents as current scientific truth unless the current reports explicitly
refer to them.
