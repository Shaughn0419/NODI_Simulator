# Exhaustive Full-Grid Scope Correction Audit

Date: 2026-05-18

Status: correction audit after scope error. The previous P19 `pre3seed_formal_3seed_10000e` launch path must not be treated as the user's requested exhaustive full calculation.

## Executive Correction

My previous interpretation was wrong.

I treated "full calculation" as the P19 frozen candidate-family run:

- 9 carry-forward route families
- 19-particle P19 panel
- 3 seeds: 11, 22, 33
- 10000 events/case
- 513 raw case rows
- 5,130,000 stochastic events

That is not the user's requested scope if "full calculation" means:

- all particle sizes in the canonical full-range EV+gold library
- 4 wavelengths
- all aperture/channel geometries used by the full-range grid
- 3 seeds
- 10000 events/case

The correct canonical exhaustive EV+gold full-grid scope, based on the existing local full-range result library, is:

- 56 particles: 29 gold sizes + 27 exosome/EV-like sizes
- 4 wavelengths: 404, 488, 532, 660 nm
- 11 widths: 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500 nm
- 13 depths: 500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500 nm
- 572 route triples = 4 x 11 x 13
- 32032 route-particle case rows per seed = 572 x 56
- 96096 physical route-particle-seed case rows for 3 seeds
- 960,960,000 physical stochastic event evaluations at 10000 events/case

Two normalization views are still needed for analysis:

- `fixed_660_gold`: fixed-660 gold reference view for cross-wavelength decision lineage
- `per_wavelength_gold`: per-wavelength gold reference view for Tsuyama/per-wavelength diagnostic lineage

These are analysis views, not new physical event axes. A correct no-rerun campaign should sample each physical event campaign once and emit both normalization views from the same event samples. If stored in long form, the analysis table may contain 192192 view rows, but the physical event budget should remain 960,960,000.

Implementation update: `tools/lens_b_ev_gold_fullgrid_runner.py` now exposes `--normalization-lane shared_dual_gold`, which samples each physical route-particle-seed event stream once and emits both required long-form normalization views. The old single-lane modes remain guarded fallbacks, not the canonical launch path.

## Evidence Checked

### Current P19 Formal Plan

File: `results/pre3seed_formal_3seed_10000e_run_plan.csv`

Observed by CSV parse:

- rows: 27
- candidate families: 9
- wavelengths present: 404, 488, 532, 660
- widths present: 500, 600, 700, 800, 900, 1100
- depths present: 1300, 1400, 1500
- seeds: 11, 22, 33
- expected particle panel size per route/seed: 19

File: `results/pre3seed_formal_3seed_10000e_prelaunch_manifest.json`

Observed:

- `candidate_family_count=9`
- `expected_rows=513`
- `expected_event_count=5130000`
- `planned_worker_count=16`
- exact command points to `tools/run_pre3seed_3seed_10000e_from_manifest.py`

Conclusion: this is a candidate-family formal run, not an exhaustive full grid.

### Canonical Existing Full-Range Library

File: `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`

Observed by streaming parse:

- rows: 32032
- particles: 56
- particle split: 29 gold, 27 exosome/EV-like
- wavelengths: 404, 488, 532, 660
- widths: 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500
- depths: 500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500
- route triples: 572
- route grid completeness: 572 = 4 x 11 x 13

File: `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_meta.json`

Observed:

- `particle_profile=full_range_biomimetic_exosome_with_anchors`
- `n_cases=32032`
- `n_events_per_case=10000`
- `wavelengths_nm=[404, 488, 532, 660]`
- `particle_types` length 56
- `sweep_completion_policy.expected_total_cases=32032`
- `sweep_completion_policy.saved_case_count=32032`
- `sweep_completion_policy.completion_status=complete`

Conclusion: this is the local canonical reference for "all particle sizes + 4 wavelengths + all full-range apertures" but it is one-seed evidence, not the requested 3-seed campaign.

### Existing Lens-B Full-Grid Runner

File: `tools/lens_b_ev_gold_fullgrid_runner.py`

Observed:

- `EXPECTED_ROUTES=572`
- `EXPECTED_PARTICLES=56`
- `EXPECTED_EV_PARTICLES=27`
- `EXPECTED_GOLD_PARTICLES=29`
- `EXPECTED_ROWS_PER_SEED=32032`
- supported normalization lanes: `per_wavelength_gold`, `fixed_660_gold`
- CLI requires `--workers`, `--n-events`, `--seed`, `--output-dir`, `--particle-scope ev_gold`, `--route-source`, `--normalization-lane`, and `--mode`
- `run_full` is explicitly one seed per invocation (`run_kind=lens_b_ev_gold_fullgrid_full_1seed`)

Conclusion: the runner can execute one seed of the canonical full grid per command while emitting both normalization views through the `shared_dual_gold` path. A correct 3-seed campaign should run the shared-dual path once per seed.

## Scope Comparison

| Scope | Routes | Particles | Seeds | Events/case | Raw case rows | Stochastic events | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| Current P19 candidate-family run | 9 | 19 | 3 | 10000 | 513 | 5,130,000 | Not exhaustive |
| 12 named preseed route triples | 12 | 19 | 3 | 10000 | 684 | 6,840,000 | Still not full particle-size grid |
| Canonical EV+gold physical event grid | 572 | 56 | 3 | 10000 | 96096 physical case rows | 960,960,000 | Corrected exhaustive physical scope |
| Canonical EV+gold dual-normalization analysis views | 572 | 56 | 3 | 10000 | 192192 long-form view rows, or 96096 wide rows | 960,960,000 if shared-event implementation is used | Required analysis coverage without physical-event doubling |
| Legacy separate-lane workaround | 572 x 2 invocations | 56 | 3 | 10000 | 192192 recomputed case rows | 1,921,920,000 | Guarded fallback only; not preferred as canonical scope |
| Current shared-dual production runner | 572 | 56 | 3 | 10000 | 192192 long-form view rows | 960,960,000 | Canonical no-rerun launch path |

## Process And Analysis Outputs That Must Be Preserved

The existing full-range summary has 1143 columns. It already includes many process and analysis quantities that reduce rerun risk:

- all-crossing outputs: `all_crossing_n_events`, `all_crossing_n_detected`, `all_crossing_detection_rate`, Wilson lower bound
- selected-annulus event-position window outputs: selected candidate and selected annulus event counts, fractions, detection rates, Wilson lower bounds, mean edge norm
- engineering gates and blockers
- score fields and final engineering scores
- reference fields and reference calibration status
- detector operator fields and detector calibration status
- threshold/readout/noise fields
- phase/polarity/governance fields
- event QC fields
- compact distribution summaries for peak height, peak margin, peak-to-threshold ratio, peak width, transit time, and local SNR (`p10/p50/p90/p95/p99`)
- count prediction blocker fields
- POD unavailable/blocker fields
- BFP/ROI surrogate and calibration status fields

The corrected 3-seed full-grid campaign must either keep this rich raw-row schema or emit a separate diagnostic/process sidecar of equal or better coverage. A minimal P19-style 513-row summary is not enough for the user's requested "no omissions" full calculation.

Implementation update: the full-grid runner now writes a lightweight analyzer raw CSV plus a scalar diagnostic sidecar. The sidecar preserves scalar blocker / calibration / event-QC / reference / detector / governance fields from the full per-case result while intentionally excluding per-event arrays and nested tables that would make the 10000e campaign impractically large. To reduce post-run rerun risk without storing event arrays, batch summaries now include compact `p10/p50/p90/p95/p99` distribution fields for the main event-level scalar families listed above.

## Normalization Lane Decision

The existing Lens-B full-grid runner distinguishes:

- `per_wavelength_gold`: useful for per-wavelength relative normalization and Stage B6 diagnostic lineage
- `fixed_660_gold`: useful for fixed-660 cross-wavelength decision lineage and Stage B7 outputs

Future comparison questions may require either normalization view, so both views should be preserved. However, preserving both views should not be interpreted as running a second physical event campaign.

Correct target behavior:

- generate the 572 x 56 x 3 x 10000 physical event campaign once
- retain or recompute enough raw per-case quantities to evaluate both normalization references
- emit both `fixed_660_gold` and `per_wavelength_gold` analysis columns, or emit long-form rows keyed by `normalization_lane`
- keep seed, all-crossing lens, selected-annulus event-position-window lens, and normalization view separate during aggregation

Current implementation:

- `tools/lens_b_ev_gold_fullgrid_runner.py` accepts `--normalization-lane shared_dual_gold`
- full mode rejects non-10000e runs, rejects seeds outside 11/22/33, refuses silent overwrite, and exits non-zero if a seed run is incomplete
- single-lane full-mode fallbacks still require `--accept-one-lane-primitive`
- the shared path calls `run_single_case_batch_shared_event_normalization_views(...)`
- the shared path computes the physical trajectory/illumination/event stream once per case and accumulates `fixed_660_gold` and `per_wavelength_gold` summaries from that shared event stream
- outputs are long-form per-view CSVs keyed by `normalization_lane`, with `shared_event_dual_normalization_used=True`

Because normalization is coupled into event simulation through `E_sca_unit_normalized`, simply running one lane and relabeling its summary as the other lane remains invalid. The canonical pre-launch fix is now implemented; use `shared_dual_gold` rather than the guarded separate-lane fallback.

## Shared-Event Dual-Normalization Smoke Status

Follow-up smoke report: `reports/138_shared_dual_normalization_smoke_report_20260518.md`.

The smoke passed on a small grid:

- routes: `660,800,1400` and `404,800,1400`
- particles: `gold_40nm` and `exosome_biomimetic_corona_nominal_100nm`
- seed: `11`
- event counts: `20`, `200`, and `1000`
- lanes: `fixed_660_gold` and `per_wavelength_gold`

Correctness result:

- matching route / particle / seed / event-count cases have the same `case_random_seed` and `case_random_identity` across normalization views
- the 404 nm check proves this is not a relabeling artifact because `E_sca_ref`, `E_sca_normalized`, and detection summaries differ between views as expected
- the direct paired feasibility path matches the current one-lane outputs for checked fields

Timing result:

- 660 nm, 20 events/case: paired/separate ratio `0.656`
- 660 nm, 200 events/case: paired/separate ratio `0.916`
- 404 nm, 200 events/case: paired/separate ratio `0.932`
- 404 nm, 1000 events/case: paired/separate ratio `0.987`

Interpretation: event stream sharing is feasible and the later production implementation moved the dual-view split below the one-lane runner wrapper. The implemented path is an event-loop shared stream with dual accumulators, not a vectorized accelerator; it removes normalization-view physical-event recomputation, while later vectorization may still improve throughput.

## Particles Not Covered By Canonical EV+gold Full Grid

The canonical 56-particle full-range grid covers gold and exosome/EV-like size series. It does not include every contaminant/control proxy from the P19 diagnostic manifest, such as PS/silica/liposome/lipoprotein/protein aggregate rows, except where those are represented in separate P19 diagnostic/control artifacts.

If the intended phrase "all particle sizes" also means "all contaminant/control particle roles across full size ladders", that is a larger scope than any current local runner supports. It must be defined separately before launch.

## Immediate Safety Rule

Do not launch this command as the user's exhaustive full calculation:

```bash
python tools/run_pre3seed_3seed_10000e_from_manifest.py --execute --allow-large-run --confirm-p19-level1-launch --events-per-case 10000 --seeds 11,22,33 --workers 16
```

That command only launches the 9-family P19 candidate run after freeze closure.

## Corrected Launch Direction

For the canonical exhaustive EV+gold full grid, use `tools/lens_b_ev_gold_fullgrid_runner.py` or a wrapper around it, not the P19 candidate-family runner.

Corrected physical event campaign:

- source: `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`
- particle scope: `ev_gold`
- seeds: 11, 22, 33
- events/case: 10000
- workers: 16
- expected rows per seed: 32032
- expected physical case rows for 3 seeds: 96096
- expected physical stochastic events: 960,960,000
- required analysis views: `fixed_660_gold` and `per_wavelength_gold`
- acceptable storage shape: 96096 wide rows with paired normalization-view columns, or 192192 long-form rows keyed by `normalization_lane`

Current canonical runner path:

- run `tools/lens_b_ev_gold_fullgrid_runner.py --normalization-lane shared_dual_gold` once per seed
- expected long-form view rows: 192192 across three seeds
- expected physical stochastic events: 960,960,000
- status: preferred no-rerun production path

## Required Work Before Any Exhaustive Launch

1. Generate a new exhaustive full-grid run manifest that explicitly records:
   - 56 particle names and particle split
   - 572 route triples
   - 4 wavelengths
   - 11 widths
   - 13 depths
   - seeds 11, 22, 33
   - events/case 10000
   - worker count 16
   - required normalization analysis views
   - that views are produced by shared-event dual-normalization through `shared_dual_gold`
   - exact commands
2. Add a hard preflight check that fails unless:
   - route count is 572
   - particle count is 56
   - rows per seed is 32032
   - three seed outputs are expected
3. Use the hard shared-event/normalization check:
   - canonical launch uses `--normalization-lane shared_dual_gold`
   - runner output must emit both normalization views from the same physical event samples
   - smoke/regression tests must prove equivalence against separate one-lane runs on a tiny grid
4. Decide whether contaminant/control roles outside EV+gold are separate diagnostics or part of the exhaustive run.
5. Ensure post-run analysis aggregates across seeds without mixing:
   - seed
   - normalization analysis view
   - all-crossing lens
   - selected-annulus event-position-window lens
   - recommendation-eligible 404/660 vs control-only 488/532
6. Keep Level-1 no-measured-data claim boundaries:
   - no calibrated SNR
   - no LOD
   - no true concentration
   - no empirical blank false-positive claim
   - no detector voltage claim
   - no EV biological specificity claim

## Final Audit Verdict

The previous P19 launch prompt is not safe as the launch prompt for the user's requested exhaustive full calculation. It has now been marked with a top-of-file warning, but the correct next step is a new exhaustive full-grid launch manifest and prompt.

The corrected physical-event scope is 960.96M events, not 5.13M events.

Both normalization views should be preserved, but they should not double the physical-event budget. If the guarded single-lane fallback is used twice, the 1.92192B-event total must be labeled as an accepted implementation workaround, not as the scientifically required full-grid scope.

The save/analysis chain now has three explicit layers: the runner writes both lightweight raw rows and scalar diagnostic sidecars; `tools/analyze_lens_b_ev_gold_fullgrid.py` validates and derives one seed / one normalization view at a time; and `tools/aggregate_lens_b_ev_gold_fullgrid_3seed.py` aggregates derived outputs across the expected seeds without rereading or duplicating the giant raw CSVs.
