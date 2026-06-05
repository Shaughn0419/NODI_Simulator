# Exhaustive Full-Grid Rerun-Risk Audit

Date: 2026-05-18

Status: pre-launch audit after shared-event dual-normalization smoke and process-field review.

## Verdict

For the current no-measured-data Level-1 EV+gold design-selection goal, the corrected exhaustive calculation scope covers the necessary physical axes:

- 56 EV+gold particles
- 4 wavelengths
- 11 widths
- 13 depths
- 3 seeds
- 10000 events/case
- all-crossing and selected-annulus event-position-window lenses
- both required normalization analysis views: `fixed_660_gold` and `per_wavelength_gold`

The main previous rerun risk was the dual-normalization implementation. That risk has now been closed for the canonical production path: the full-grid runner supports `--normalization-lane shared_dual_gold`, which emits both required normalization views from one shared physical event stream.

The remaining launch risks are operational rather than scientific-axis gaps: run authorization, output destination hygiene, and post-run per-view analysis/aggregation discipline.

## Evidence Checked

Source scope:

- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`
- `tools/lens_b_ev_gold_fullgrid_runner.py`

Validated by `load_and_validate_source(...)`:

- routes: `572`
- particles: `56`
- EV/exosome particles: `27`
- gold particles: `29`
- route-particle rows per seed: `32032`

The route grid is complete:

- wavelengths: `404, 488, 532, 660`
- widths: `500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500`
- depths: `500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500`

Shared-normalization smoke:

- `reports/138_shared_dual_normalization_smoke_report_20260518.md`
- `tools/smoke_shared_dual_normalization.py`

The smoke passed on `660,800,1400` and `404,800,1400` with `gold_40nm` and `exosome_biomimetic_corona_nominal_100nm`.

Production shared-dual runner trial:

- command: `tools/lens_b_ev_gold_fullgrid_runner.py --mode trial --normalization-lane shared_dual_gold --n-events 5 --seed 11`
- output directory: `tmp/shared_dual_runner_trial_20260518_prodpath_b`
- completed route: `(404, 500, 500)`
- physical route-particle rows: `56`
- emitted view rows: `112` across two per-view raw CSVs
- raw and diagnostic outputs carry `shared_event_dual_normalization_used=True`

Process-field review:

- the existing full-range source has `1143` columns
- the full-grid runner now writes a lightweight analyzer raw CSV plus a scalar diagnostic sidecar
- trial sidecar check showed compact distribution fields are present:
  - `peak_height_p90`
  - `peak_margin_z_p95`
  - `peak_to_threshold_ratio_p99`
  - `peak_width_s_p50`
  - `transit_time_s_p90`
  - `local_snr_p90`

## Rerun-Risk Matrix

| Area | Current coverage | Rerun risk | Judgment |
|---|---|---:|---|
| EV+gold particle sizes | 56 particles, 29 gold + 27 EV-like | Low | Complete for canonical EV+gold scope |
| Wavelengths | 404/488/532/660 | Low | Complete for current NODI design grid; 488/532 remain control-only |
| Geometries | 11 widths x 13 depths | Low | Complete full-range route grid |
| Seeds/events | 11/22/33 x 10000 events/case | Medium | Correct formal design target; rank instability could still motivate future more-seed/more-event convergence, but that is not a forgotten axis |
| Normalization views | fixed-660 and per-wavelength required | Low | Production `shared_dual_gold` path emits both views from one physical stream |
| Detection lenses | all-crossing and selected-annulus event-position window | Low | Both preserved; selected-annulus must not be described as optical BFP annulus |
| EV ranking priors | uniform, small-EV, broad-EV, sharp-MSC-sEV | Low | Analyzer preserves multiple EV-size prior views |
| Wavelength role split | 404/660 recommendation-eligible, 488/532 control-only | Low | Explicitly preserved in analyzer and aggregator |
| Gold role | anchor / Tsuyama diagnostic only | Low | Gold rows are retained but must not drive EV recommendation claim |
| Process and blocker fields | raw + diagnostic scalar sidecar | Low | Reference/detector/readout/threshold/governance/event-QC/blocker fields preserved |
| Event-distribution summaries | compact p10/p50/p90/p95/p99 fields added | Low | Reduces rerun risk for distribution-tail questions without storing event arrays |
| Full event traces | intentionally not retained | Accepted risk | Rerun would be needed only if future analysis requires raw per-event traces, not scalar summaries |
| Contaminant/control roles outside EV+gold | separate diagnostic manifest, not formal grid | Accepted scope boundary | If user later wants full contaminant-size grid, that is a new scope and requires new computation |
| POD quantitative amplitude | out of current NODI scoring scope | No current rerun risk | Future POD work is separate; current run must not claim POD amplitude |
| Concentration/count-rate/LOD | excluded | No current rerun risk | Requires event-arrival + measured calibration later; not unlockable by this synthetic grid alone |
| Measured detector/BFP/full-wave calibration | excluded | No current rerun risk | Later Level-2+ plan; not a missing no-data Level-1 axis |

## Process Quantities To Preserve

The full run should preserve these families in raw or diagnostic sidecar outputs:

- identity/scope: route index, particle, material/family, wavelength, width, depth, seed, event count, normalization lane
- all-crossing detection: event counts, detected counts, detection rate, Wilson lower bound
- selected-annulus event-position window: candidate and annulus counts, fractions, detection rates, Wilson lower bounds, mean edge norm
- signal distribution: mean/std peak height, positive/negative peak summaries, peak width, peak-to-threshold ratio, peak margin
- compact tails: p10/p50/p90/p95/p99 for peak height, peak margin, peak-to-threshold ratio, peak width, transit time, local SNR
- readout/threshold: threshold sigma/tail, readout observable mode, lock-in/readout fields, robust threshold statistics
- reference/detector: reference route/status, detector forward model/status, calibration/blocker fields
- governance/blockers: claim level, calibration state, Bayesian/POD/count-rate blockers, event-QC fields
- route analysis: all-crossing and selected-annulus ranking outputs, EV prior-weighted route scores, wavelength summaries, gold diagnostic summary
- 3-seed analysis: per-lane seed coverage, route stability, top route aggregation, rank consistency

## Remaining Pre-Launch Discipline

The canonical launch path is now:

```bash
python tools/lens_b_ev_gold_fullgrid_runner.py --mode full --workers 16 --n-events 10000 --seed <11|22|33> --particle-scope ev_gold --normalization-lane shared_dual_gold --route-source results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv --output-dir <seed_output_dir>
```

Do not start the expensive campaign until the launch prompt/manifest records this shared-dual path, exact output directories, and post-run analysis commands for each emitted view. Do not use the old two-command separate-lane fallback unless the user explicitly chooses it.

## Final Judgment

I do not see another missing no-measured-data Level-1 axis that must be added before launch. The planned calculation is broad enough for the intended route-selection question, and the shared-event dual-normalization production path is now implemented.

Anything that could require future computation is either a deliberate later-plan item (measured calibration, POD, full-wave, count-rate/LOD) or a new scope expansion (full contaminant/control particle grid, raw per-event trace archaeology, more-seed convergence after instability is observed).
