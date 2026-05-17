# Lens-B τ=1 ms Stage B5 targeted probe note

- Date: 2026-05-14
- Scope: Criterion B / 口径 B only
- Status: Stage B5 targeted EV probe completed; Stage B6 low-event full-grid now completed at `1000 events/case`

## Source artifacts

| Artifact | Role |
|---|---|
| `results/lens_b_tau1ms_recalibration_20260514/stage_b5_tau1ms_targeted_ev_probe_3000e_1seed/stage_b5_tau1ms_targeted_ev_probe_raw_rows.csv` | Raw targeted probe rows |
| `results/lens_b_tau1ms_recalibration_20260514/stage_b5_tau1ms_targeted_ev_probe_3000e_1seed/stage_b5_tau1ms_targeted_ev_probe_route_ranking.csv` | EV route ranking by prior |
| `results/lens_b_tau1ms_recalibration_20260514/stage_b5_tau1ms_targeted_ev_probe_3000e_1seed/stage_b5_tau1ms_targeted_ev_probe_wavelength_summary.csv` | Wavelength-level EV summary |
| `results/lens_b_tau1ms_recalibration_20260514/stage_b5_tau1ms_targeted_ev_probe_3000e_1seed/stage_b5_tau1ms_targeted_ev_probe_summary.md` | Generated B5 summary |
| `results/lens_b_tau1ms_recalibration_20260514/stage_b5_tau1ms_targeted_ev_probe_3000e_1seed/stage_b5_tau1ms_targeted_ev_probe_manifest.json` | Probe panel, substitutions, and governance metadata |

## Probe configuration

| Field | Value |
|---|---|
| Candidate | `tau_1ms_global_refphi_plus_collection_narrow` |
| Scenario | `nodi_2022_5sigma_single_sensitivity` |
| Runtime τ | `lockin_time_constant_s = 0.001` for every raw row |
| Seed | `42` |
| Events | `3000 events/case` |
| Rows | `434` |
| Particle panel | 27 EV/exosome particles + 4 gold anchors |
| Route panel | 14 targeted routes |

Gold anchor rows were included only for diagnostic continuity. They are not eligible for EV recommendation.

## Route panel note

The roadmap example `532 nm / 700 x 750 nm` is not present in the route source grid. Stage B5 used `532 nm / 700 x 700 nm` as the nearest top-control grid substitute and recorded this substitution in the manifest.

## Main finding

Under the reference-useful selected-annulus filter, 404 did not overtake 660 in any EV prior:

| Prior | Best 404 selected-annulus detection | Best 660 selected-annulus detection | 404 overtakes 660 |
|---|---:|---:|---|
| uniform | 0.818403 | 0.833043 | no |
| small_ev_literature | 0.798491 | 0.825178 | no |
| broad_ev_literature | 0.839691 | 0.849154 | no |
| sharp_msc_sev_empirical | 0.688461 | 0.749051 | no |

The recommendation-eligible top route in this targeted panel is `660 nm / 800 x 1500 nm` for all four EV priors. This is a targeted-panel result, not a full-grid final recommendation. The later Stage B6 low-event full-grid keeps the 660-over-404 conclusion but shifts most EV priors shallower (`660 / 800 x 1000-1100`, with `800 x 1400` for the sharp MSC-sEV prior).

## Control-only read

The best 488/532 control-only rows can remain high in raw selected-annulus metrics. In this probe, `488 nm / 600 x 650 nm` is the top control-only route across the four priors. This does not affect the final recommendation boundary: 488/532 remain control/trend-only, while final recommendation conclusions can only choose 404/660.

## Decision

Stage B5 correctly lowered the urgency of a full-grid solely to check a 404-over-660 flip. Stage B6 has now completed at `1000 events/case`, so this note should be read as targeted prior evidence and as a useful explanation of why the 404 probe did not need to be widened further.

Next recommended step: use `reports/127_lens_b_tau1ms_stage_b6_1000e_fullgrid_note_2026-05-15.md` plus the Stage B6 derived outputs for report synchronization. Run a `10000 events/case` final-validation pass only if the project needs stronger final-validation evidence than the current low-event design read.

## Ag/Au correction impact

Another 2026-05-14 thread corrected the Tsuyama Table S1 Ag/Au interpretation: the silver interferometric column is now treated as the direct Ag/Au ratio-like target (`488/532/660 nm = 1.90/0.89/0.85`), while the old Ag-column/Au-column quotient is legacy audit-only.

This does not change the Stage B5 EV ordering because the targeted EV probe contains EV rows plus gold anchors for continuity, but no Ag rows. The corrected Ag/Au target does affect the Stage B3/B4 anchor acceptance wording/status: those acceptance outputs were rerun, strict corrected-interferometric signal alignment now passes, diagnostic warnings are empty, and the remaining no-go reason is still `raw_size_response_alignment_not_met`.

## Claim boundary

This note must not be cited as B=1 ms full-grid evidence. The completed 2026-05-13 full-grid is legacy `τ=2 ms` evidence, and the completed Stage B5 run is bounded targeted `τ=1 ms` evidence. Current low-event full-grid design evidence is the Stage B6 1000e run documented in report 127; it still must not be relabeled as a `10000 events/case` final-validation result.
