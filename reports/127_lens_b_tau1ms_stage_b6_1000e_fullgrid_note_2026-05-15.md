# Lens-B tau=1 ms Stage B6 low-event full-grid note

- Date: 2026-05-15
- Scope: Criterion B / 口径 B only
- Status: Stage B6 seed-42 EV+gold full-grid completed at `1000 events/case`
- Claim boundary: low-event full-grid design evidence, not the planned `10000 events/case` final-validation run
- Superseding overlay: Stage B7 fixed-660-gold normalization is now documented in `reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md`; B6 remains the per-wavelength gold-normalized Tsuyama-lineage comparison read, not the latest cross-wavelength Criterion-B decision read.
- 2026-05-23 overlay: this note is historical single-seed 1000e context. The latest robust Lens-B full-grid interpretation is `reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`; report 140 supersedes this note and report 100 for route-family interpretation.

## Source artifacts

| Artifact | Role |
|---|---|
| `results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514/seed_42_raw_rows.csv` | Completed raw EV+gold full-grid rows |
| `results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514/derived_1000e/` | Derived analysis directory regenerated with the current analyzer |
| `results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514/run_manifest.json` | Run manifest; corrected to show actual `n_events=1000` in frozen-B metadata |
| `results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514/seed_42_run_summary.json` | Completion/runtime summary |

## Run integrity

| Check | Result |
|---|---|
| rows | `32,032` |
| route-particle rows per seed | `32,032` |
| seed | `42` only |
| n_events | `1000` only |
| completed particle events | `32,032,000` |
| materials | `exosome`, `gold` |
| EV rows | `15,444` |
| gold rows | `16,588` |
| wavelengths | `404`, `488`, `532`, `660` |
| runtime tau | `lockin_time_constant_s = 0.001` for every raw row |
| failures | none |
| analyzer precheck | passed |

## EV recommendation-eligible tops

Final recommendation conclusions may only use `404` or `660`, and only EV/exosome rows. Under the reference-useful selected-annulus filter, every EV prior is still led by `660 nm / 800 nm` width:

| EV prior | top recommendation-eligible route | selected-annulus detection | all-crossing detection | final engineering score |
|---|---|---:|---:|---:|
| uniform | `660 / 800 x 1100` | `0.841044` | `0.646963` | `1.078969` |
| small_ev_literature | `660 / 800 x 1100` | `0.833029` | `0.608569` | `0.845224` |
| broad_ev_literature | `660 / 800 x 1000` | `0.858362` | `0.635354` | `1.016162` |
| sharp_msc_sev_empirical | `660 / 800 x 1400` | `0.757808` | `0.571951` | `0.705121` |

404 remains recommendation-eligible, but it does not overtake 660 in this low-event full-grid.

## Control-only tops

488/532 remain control/trend-only even when their selected-annulus metric is high:

| EV prior | top control-only route | selected-annulus detection | all-crossing detection | final engineering score |
|---|---|---:|---:|---:|
| uniform | `488 / 600 x 900` | `0.833377` | `0.644741` | `1.269859` |
| small_ev_literature | `488 / 600 x 1100` | `0.818085` | `0.628371` | `0.819894` |
| broad_ev_literature | `488 / 600 x 900` | `0.855403` | `0.652188` | `1.251411` |
| sharp_msc_sev_empirical | `488 / 600 x 1300` | `0.717183` | `0.569991` | `0.892152` |

These rows are useful trend/control evidence only and cannot enter the final wavelength recommendation.

## Design read

This 1000-event full-grid confirms the important B5 wavelength conclusion: `404` does not overtake `660`, and `488/532` stay outside the recommendation set. It changes the geometry read relative to the targeted B5 panel: B5 had `660 / 800 x 1500` as the targeted-panel top across priors, while the full-grid low-event run shifts most priors shallower.

Current Criterion B design wording should therefore be:

```text
Criterion B low-event design evidence points to a 660 nm / 800 nm-width family.
Use 800 x 1100 nm as the broad default center, 800 x 1000 nm as the broad-EV
neighbor, and 800 x 1400 nm as the sharp small-sEV stress-check. Keep 404 as an
eligible shortwave sidecar and 488/532 as control-only.
```

Do not write this as a measured SNR/LOD claim, a biological EV specificity claim, a 3-seed consensus, or a `10000 events/case` final-validation result.

## Next step

No immediate full recomputation is needed for the design note unless the project needs final-validation strength. If final-validation strength is required, rerun the same B6 scope at `10000 events/case` for seed 42, then consider 3 seeds only if the 10k seed-42 result materially changes the 404/660 ordering or the 660/800 depth family.
