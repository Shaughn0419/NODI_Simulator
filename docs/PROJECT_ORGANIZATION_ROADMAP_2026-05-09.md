# Project Organization Roadmap - 2026-05-09

This roadmap defines a gradual cleanup path for making the repository easier to
navigate without breaking the current scientific results, dashboard, tests, or
legacy command entrypoints.

## Migration Principles

- Keep behavior locked before every migration batch.
- Move one bounded module family at a time.
- Use canonical package paths (`nodi_simulator/<module>.py`) for package
  modules. Root package-module compatibility wrappers are retired.
- Prefer deletion of generated/process artifacts over reshuffling live sources.
- Keep reports, configs, tests, tools, and source modules in clearly separate
  lanes.
- Do not introduce new dependencies for organization work.

## Target Layout

```text
nodi_simulator/          # canonical Python package modules
dashboard/               # Streamlit app and dashboard panels
tools/
  audits/                # repeatable analysis/audit entrypoints
  benchmarks/            # performance and benchmark entrypoints
  one_shot/              # historical generation/adjudication scripts
configs/                 # declarative run and governance configs
docs/                    # project governance, specs, and organization docs
guides/                  # reader-facing module and operation guides
reports/                 # current and staged analysis reports
archive/                 # historical provenance snapshots
tests/                   # pytest suite and test runner
results/, tmp/, exports/ # ignored generated artifacts
```

## Phase 0 - Hygiene Baseline

Status: complete for this pass.

- Removed AppleDouble metadata and Python/tool caches outside `.git` and local
  environment/vendor directories.
- Kept registered worktrees, virtual environments, vendored test dependencies,
  and generated result artifacts intact.
- Verified the repository with lint, typed-seed typecheck, and the full test
  runner; full-repository type debt remains outside the release gate for now.

## Phase 1 - Package Migration Scaffold

Status: complete for package modules in this pass.

- Make `nodi_simulator/` the canonical location for package Python modules.
- Keep public package exports in `nodi_simulator/_exports.py`.
- For migrated package modules:
  1. implementation lives in `nodi_simulator/<module>.py`;
  2. root package-module compatibility wrappers have been deleted;
  3. companion docs name the canonical path;
  4. targeted tests plus the standard gates were run for migration batches.

Current package-module status:

- `nodi_simulator/type_coerce.py` is the canonical implementation.
- `nodi_simulator/optional_acceleration.py` is the canonical implementation.
- `nodi_simulator/realism_v2_io.py` is the canonical implementation.
- `nodi_simulator/unit_conventions.py` is the canonical implementation.
- `nodi_simulator/detector_units.py` is the canonical implementation.
- `nodi_simulator/uncertainty.py` is the canonical implementation.
- root compatibility wrappers have been retired for package modules.

## Phase 2 - Low-Risk Shared Helpers

Move small dependency-light helpers first.

Status: complete for this pass.

Completed helper batches:

The batch log below keeps module basenames for compact provenance. Unless a
row explicitly says `root`, the current implementation path is
`nodi_simulator/<name>.py`.

- Batch 1:
  `realism_v2_io.py`, `unit_conventions.py`, `detector_units.py`,
  `uncertainty.py`
- Batch 2:
  `calibration_models.py`, `calibration_plan_advisor.py`,
  `run_state_model.py`, `recompute_manifest.py`
- Batch 3:
  `control_interpretation.py`, `count_likelihood.py`, `ood_detection.py`,
  `bayesian_calibration.py`
- Batch 4:
  `experimental_design_advisor.py`, `population_inference.py`,
  `ev_population_prior.py`, `seed_robustness.py`
- Batch 5:
  `assay_control_matrix.py`, `event_quality_control.py`,
  `ev_integrity_risk.py`, `ev_reporting_metadata.py`
- Batch 6:
  `channel_geometry_model.py`, `fluidic_resistance.py`,
  `fluidic_network_model.py`, `electrokinetic_transport.py`
- Batch 7:
  `design_metrics.py`, `particle_channel_perturbation.py`,
  `nodi_thermal_contamination.py`, `photothermal_pod.py`
- Batch 8:
  `design_postprocess.py`, `design_claim_governance.py`,
  `selection_function.py`, `reference_operating_point.py`
- Batch 9:
  `optical_exposure_safety.py`, `optical_hardware_profiles.py`,
  `objective_panel.py`, `wavelength_comparability.py`
- Batch 10:
  `readout_transfer_model.py`, `bfp_detector_operator.py`,
  `paper_aligned_profiles.py`, `tsuyama_phase_filter.py`
- Batch 11:
  `count_generation.py`, `interface_correction.py`,
  `structured_particles.py`, `particle_design_library.py`
- Batch 12:
  `materials.py`, `mie_engine.py`, `intrinsic_scattering.py`,
  `illumination.py`
- Batch 13:
  `scattering_trace.py`, `interferometric_trace.py`, `pulse_analysis.py`
- Batch 14:
  `reference_field.py`, `trajectory.py`
- Batch 15:
  `data_objects.py`
- Batch 16:
  `population_trace_simulator.py`, `polarization_jones_operator.py`
- Batch 17:
  `utils.py`
- Batch 18:
  `parameter_sweep.py`
- Batch 19:
  `realism_v2.py`
- Batch 20:
  root `__init__.py` export table moved to `nodi_simulator/_exports.py`
- Batch 21:
  retired root compatibility wrappers for low-risk shared helpers:
  `type_coerce.py`, `optional_acceleration.py`, `realism_v2_io.py`,
  `unit_conventions.py`, `detector_units.py`, `uncertainty.py`,
  `calibration_models.py`, `calibration_plan_advisor.py`,
  `run_state_model.py`, `recompute_manifest.py`,
  `control_interpretation.py`, `count_likelihood.py`, `ood_detection.py`,
  `bayesian_calibration.py`, `experimental_design_advisor.py`,
  `population_inference.py`
- Batch 22:
  retired root compatibility wrappers for diagnostic, design, fluidic, and
  optical governance helpers:
  `assay_control_matrix.py`, `event_quality_control.py`,
  `ev_integrity_risk.py`, `ev_reporting_metadata.py`,
  `channel_geometry_model.py`, `fluidic_resistance.py`,
  `fluidic_network_model.py`, `electrokinetic_transport.py`,
  `design_metrics.py`, `particle_channel_perturbation.py`,
  `nodi_thermal_contamination.py`, `photothermal_pod.py`,
  `design_postprocess.py`, `design_claim_governance.py`,
  `selection_function.py`, `reference_operating_point.py`,
  `optical_exposure_safety.py`, `optical_hardware_profiles.py`,
  `objective_panel.py`, `wavelength_comparability.py`
- Batch 23:
  retired root compatibility wrappers for optical/physics core, trace, pulse,
  and particle-library modules:
  `materials.py`, `mie_engine.py`, `intrinsic_scattering.py`,
  `illumination.py`, `reference_field.py`, `trajectory.py`,
  `scattering_trace.py`, `interferometric_trace.py`, `pulse_analysis.py`,
  `bfp_detector_operator.py`, `paper_aligned_profiles.py`,
  `tsuyama_phase_filter.py`, `count_generation.py`, `interface_correction.py`,
  `structured_particles.py`, `particle_design_library.py`,
  `readout_transfer_model.py`
- Batch 24:
  retired final low-risk diagnostic/population wrappers:
  `seed_robustness.py`, `ev_population_prior.py`,
  `population_trace_simulator.py`, `polarization_jones_operator.py`
- Batch 25:
  retired final root package-module compatibility entrypoints:
  root `__init__.py`, `data_objects.py`, `parameter_sweep.py`, `utils.py`,
  `realism_v2.py`

Next suggested organization candidates:

1. documentation pointer consolidation
2. archive-only utility review
3. archive-only script modernization

## Phase 3 - Core Simulation Modules

Move the main physics and sweep modules in dependency order:

1. data/material primitives: complete for this pass.
2. optical kernels: complete for this pass.
3. trajectory and trace stack: complete for this pass.
4. sweep and scoring stack: complete for this pass.

Root package-module wrappers are retired for this pass. Dashboard, tools, and
tests should use `nodi_simulator/` paths or package imports rather than
root-module fallback behavior.

## Phase 4 - Diagnostic and Realism Modules

Status: complete for package modules in this pass.

Diagnostic, governance, and v2 realism modules are package-local. Remaining
organization work is documentation consolidation and archive/tool-entrypoint
cleanup, not root package-module migration.

Suggested groups:

- geometry, controls, and detector diagnostics: package-local;
- EV population and reporting diagnostics: package-local;
- calibration and count-likelihood modules: package-local;
- `nodi_simulator/realism_v2.py` is package-local; root compatibility wrapper
  has been retired.

## Phase 5 - Documentation Consolidation

- Keep `README.md` and `文档导航.md` as entry points.
- Root-level module companion documents currently remain discoverable, but they
  must name the canonical `nodi_simulator/` implementation paths.
- Move long module companion documents under `guides/core/` or
  `guides/operations/` in a separate doc-only batch.
- Replace duplicate root module docs with short pointers only after links in
  README, navigation, guides, and current reports have been updated.
- Keep current reports in `reports/`; keep provenance-only material in
  `archive/`.

## Phase 6 - Wrapper Retirement

Status: complete for package modules; still open for legacy tool wrappers.

- Root package-module compatibility wrappers have been retired. External usage
  should import `nodi_simulator.<module>` or `from nodi_simulator import ...`.
- Keep tool wrappers until the documented `tools/README.md` removal window or
  until external usage has had migration notice.
- Do not reintroduce root package modules as compatibility shims without a new
  migration decision and fresh verification.

## Standard Verification Gate

Run for every migration batch:

```bash
python -m pytest tests/test_type_coerce.py
ruff check .
python -m pyright
python -m mypy
python tests/run_tests.py --workers 7
```

Use a narrower first test when a batch does not touch `type_coerce.py`, but keep
the final four commands as the default release-quality gate. `pyright` and
`mypy` currently run against the transitional typed seed allowlist declared in
their config files; expanding that allowlist is the migration path for full-repo
type coverage.
