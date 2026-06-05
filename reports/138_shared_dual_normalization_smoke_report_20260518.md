# Shared-Event Dual-Normalization Smoke Report

Date: 2026-05-18

Status: smoke test completed and production shared-event dual-normalization path implemented for the exhaustive full-grid runner.

## What Was Tested

Tool: `tools/smoke_shared_dual_normalization.py`

Scope:

- routes: `660,800,1400` and `404,800,1400`
- particles: `gold_40nm`, `exosome_biomimetic_corona_nominal_100nm`
- seed: `11`
- events tested: `20`, `200`, and `1000`
- lanes: `fixed_660_gold`, `per_wavelength_gold`

Outputs:

- `tmp/shared_dual_normalization_smoke_20260518/`
- `tmp/shared_dual_normalization_smoke_200e_20260518/`
- `tmp/shared_dual_normalization_smoke_404_200e_20260518/`
- `tmp/shared_dual_normalization_smoke_404_1000e_20260518/`

## Correctness Findings

The smoke test passed.

For matching route / particle / seed / event count, both normalization views use the same:

- `case_random_seed`
- `case_random_identity`

The 404 nm smoke verifies that this is not a relabeling artifact. The two views share event identity but differ in normalization references and downstream metrics:

- `fixed_660_gold` and `per_wavelength_gold` have different `E_sca_ref`
- `E_sca_normalized` differs
- detection metrics can differ
- the direct paired-batch feasibility path matches current one-lane outputs for checked fields

Example from `tmp/shared_dual_normalization_smoke_404_200e_20260518/shared_dual_normalization_comparison.csv`:

- `gold_40nm`: shared seed/identity true; `fixed_E_sca_normalized=2.013364`, `per_wavelength_E_sca_normalized=1.000000`
- `exosome_biomimetic_corona_nominal_100nm`: shared seed/identity true; `fixed_E_sca_normalized=0.617033`, `per_wavelength_E_sca_normalized=0.306046`

## Timing Findings

The smoke compared:

1. Current separate one-lane route runs.
2. A direct paired-batch feasibility path that runs both views in one process with shared intrinsic cache.

Observed timings:

| Scope | separate one-lane total | paired direct | ratio |
|---|---:|---:|---:|
| 660 / 800 x 1400, 2 particles, 20 events | 0.353 s | 0.231 s | 0.656 |
| 660 / 800 x 1400, 2 particles, 200 events | 1.747 s | 1.601 s | 0.916 |
| 404 / 800 x 1400, 2 particles, 200 events | 1.718 s | 1.601 s | 0.932 |
| 404 / 800 x 1400, 2 particles, 1000 events | 7.876 s | 7.772 s | 0.987 |

Interpretation:

- At very small event counts, sharing case-level setup/caches helps.
- As event count rises, event simulation dominates and the current paired feasibility path gives almost no speedup.
- Therefore, the production fix had to be below runner-level relabeling: the event stream itself must be shared and two normalization accumulators must be filled from that stream.

## Production Implementation Update

Implemented production path:

- `nodi_simulator/parameter_sweep.py` now provides `run_single_case_batch_shared_event_normalization_views(...)`.
- `tools/lens_b_ev_gold_fullgrid_runner.py` now accepts `--normalization-lane shared_dual_gold`.
- The shared path samples each physical route-particle-seed event stream once, then emits both long-form normalization views:
  - `fixed_660_gold`
  - `per_wavelength_gold`
- The runner writes separate per-view raw and diagnostic CSVs while recording `shared_event_dual_normalization_used=True`.
- Full mode does not require `--accept-one-lane-primitive` for `shared_dual_gold`; that flag remains only for explicitly accepted single-lane fallback runs.

Production smoke run:

```bash
python tools/lens_b_ev_gold_fullgrid_runner.py --mode trial --workers 1 --n-events 5 --seed 11 --benchmark-seconds 2 --output-dir tmp/shared_dual_runner_trial_20260518_prodpath_b --particle-scope ev_gold --normalization-lane shared_dual_gold --route-source results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv
```

Observed output:

- completed route: `1/572`, route `(404, 500, 500)`
- physical rows: `56`
- emitted views: `2`
- output files:
  - `seed_11_trial_fixed_660_gold_rows.csv`, 56 rows
  - `seed_11_trial_per_wavelength_gold_rows.csv`, 56 rows
  - `seed_11_trial_fixed_660_gold_diagnostic_rows.csv`, 56 rows
  - `seed_11_trial_per_wavelength_gold_diagnostic_rows.csv`, 56 rows
- all four CSVs carry the expected normalization lane; raw and diagnostic files carry `shared_event_dual_normalization_used=True`.

Regression lock:

- `tests/test_exhaustive_fullgrid_chain_guards.py::test_shared_event_dual_normalization_matches_independent_views` verifies the shared-event path matches independent single-lane batches for checked deterministic and event-derived summary fields across 404 nm gold, 660 nm gold, and 404 nm EV-like cases.
- `tests/test_exhaustive_fullgrid_chain_guards.py::test_shared_event_summary_preserves_independent_summary_keys` guards against 1-event skeleton summary-key leakage in recompute manifest fields.
- `tests/test_exhaustive_fullgrid_chain_guards.py::test_shared_event_dual_normalization_rejects_rng_affecting_view_mismatch` rejects view configs whose noise/RNG-affecting fields differ.
- `tests/test_exhaustive_fullgrid_chain_guards.py::test_shared_dual_full_runner_does_not_require_one_lane_acknowledgement` verifies the production shared lane is the canonical full-mode path and does not require the single-lane fallback acknowledgment.

## Optimization Implication

The implemented production path factors below the old one-lane runner wrapper:

1. Generate event positions / Brownian trajectories / illumination envelopes once per physical event stream.
2. Reuse the same random standard draws for detector, shot, and post-readout noise.
3. Branch only the normalization-dependent scattering/interference/readout calculations for `fixed_660_gold` and `per_wavelength_gold`.
4. Accumulate two summaries from the same event block.

The current frozen Lens-B config still uses `vectorized_event_engine=off`, so this implementation is an event-loop shared production path, not a vectorized block accelerator. It removes scientific recomputation of physical stochastic events across normalization views; later vectorization may still improve throughput.

## Launch Consequence

The smoke plus production trial support the canonical launch path:

- Use `tools/lens_b_ev_gold_fullgrid_runner.py --normalization-lane shared_dual_gold`.
- Do not run separate `fixed_660_gold` and `per_wavelength_gold` full campaigns unless the user explicitly chooses the guarded fallback.
- The formal physical event budget remains `960,960,000` stochastic samples for the 3-seed EV+gold exhaustive grid.

Do not use `tools/smoke_shared_dual_normalization.py` as a launcher; it remains a diagnostic smoke tool.
