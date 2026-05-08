# Current Reports

This directory stores older notes that remain useful for methods, performance,
or historical comparison. It is not the current reader-facing entry point. Start
with `reports/88_*` for the current v1/v2 consolidated analysis and `reports/87_*`
for the v2 no-measured-data closure boundary.

Current status:

- `35_method_notes.md` — scoring/report-writing method only; no live full-library numbers.
- `36_exosome_biomimetic_surface_model.md` — current EV/sEV biomimetic optical-model rationale.
- `46_全量计算性能优化复核.md` — current performance notes for the recompute path, including artifact profiles, summary-only streaming, trajectory context, worker-local invariant caches, the 16C/32T switch back to scalar/off defaults, and the rejected `block_lane_order` default switch.
- `47_EV_NODI全量结果分层分析报告.md` — historical 32032-case four-wavelength all-crossing reader-facing analysis from an earlier reader-report lane. It remains useful for comparison, but current v1/v2 interpretation is report 88.
- `47_ev_design_full_grid_analysis/` — historical derived CSV tables backing report 47, including mechanism-chain, wavelength-ratio, geometry-effect, candidate-detection, 404-vs-660 decomposition, deep-channel usability, gold-gate sensitivity, PEG geometry scenarios, and EV size-weighted ranking tables.

2026-05-08 status update: report 47 is historical. Current formal v1/v2 reader interpretation has moved to `reports/88_*`; v2 has closed as a no-measured-data realism supplement, not an experimental acquisition lane.

2026-05-02 annulus sensitivity update: `results/tsuyama_annulus_ratio_sensitivity_medium_20260502/` scanned the 7 default annulus windows at `200` events/case with seeds `42 / 43 / 44` and `8` workers, then `results/tsuyama_annulus_ratio_sensitivity_topwindows_1000e_20260502/` repeated the top-window comparison at `1000` events/case. The higher-event focused run does not support changing the selected-annulus default; `0.5-0.8` remains the canonical paper-audit / EV cross-check lens.

2026-05-02 Phase 2 paper-fit note: Tsuyama paper-fit alignment is useful but does not block the nominal EV full-grid. Before any bounded inverse search, run a target audit that labels detection bands, signal-ratio, size-exponent, SNR-ratio, and classification targets as direct, inferred, operational, or diagnostic-only. Legacy broad detection-rate calibration bands and classification accuracy metadata must not be mixed into selected-annulus joint-fit hard acceptance without a source anchor.

2026-05-01 Tsuyama Table S1 audit update: the code now has an explicit Tsuyama 2022 Supplementary Table S1 fixed-index Au/Ag audit profile for paper-claim checks only. It improves the 660 nm Ag/Au mean-peak ratio but still does not make selected-annulus detection/readout numerically equivalent to the paper's Fig. 5 / Table S1 signal-ratio or SVM classification metrics.

2026-05-01 selected-annulus joint-fit update: `tools/tsuyama_selected_annulus_joint_fit.py` is now the explicit paper-fit lane for Tsuyama selected-annulus alignment. Schema v2 scores both 800x550 and 1200x550 paper geometries for selected-annulus detection rates, Ag/Au peak ratios, Au size scaling, and Au30/Au20 SNR ratio. The current 10000-event v2 paper-fit best is `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit`: it applies bounded silver transfer plus an explicit Au power-law size-response correction from raw exponent `3.263` to paper target `2.300` with delta `-0.963` and no guardrail penalty. These transfer/size terms remain paper-fit lenses and do not change raw detection or global simulator defaults.

2026-05-01 classification-lane update: `tools/tsuyama_2022_classification_lane.py` exports linked 488/532 features for the 2022 Au40/Au60/Ag40/Ag60 SVM claim. The v2 lane uses the detected 488 pulse window and the 532 maximum within that window; the `400` events/class smoke writes `1600` linked rows and `849` paper-SVM-usable rows, but marks `svm_accuracy_claim_level = no_accuracy_claim` because optional `scikit-learn` is not available in the current project dependency set.

2026-05-01 pre-fullgrid EV robustness update: `results/tsuyama_selected_annulus_pre_fullgrid_ev_robustness_20260501/` verifies the selected-annulus paper-fit EV targeted profile across seeds `42 / 314 / 2718` at `3000` events/seed with `8` workers. All-crossing and selected-annulus top1 routes are seed-stable for all four EV size priors; selected-annulus top1 is `488 nm / 600x1500 nm`.

Deleted current-result reports:

- `35.4_最新全量数据库全面复核与选型报告.md`

That file was tied to deleted or stale full-library results. New current-result reporting should now continue from report 88 unless a deliberately historical comparison is needed.
