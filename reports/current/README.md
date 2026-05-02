# Current Reports

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：旧正式全量结果文件 `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_*` 与旧根级 `results/ev_size_weighted_route_analysis.csv` 已清空，等待下一次从新代码完整重算。报告 47 只保留为上一轮 all-crossing 主口径历史基线，不再代表当前 `results/` 中存在可直接读取的正式全量库。下一次全量重跑应同时生成 all-crossing 主结果与 selected-annulus ranking / comparison 交叉验证结果；旧全量派生表缺 selected-annulus 源列时，新工具会标记 unavailable/null/NaN，不会回填成 selected 结论。Selected-annulus paper-fit EV targeted panel、3-seed pre-fullgrid robustness audit、lower-is-better joint-fit score、target metadata validation、claim compatibility check、all-crossing / paper-audit / 工程主库 lane 分层、non-paper-target joint-fit variant early rejection 与 8-worker annulus sensitivity smoke 已通过，当前 full-grid 阻塞点已从参数合理性转为运行成本/调度决策。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`。
<!-- DOCSYNC:END -->

This directory stores notes that are still useful for current work.

Current status:

- `35_method_notes.md` — scoring/report-writing method only; no live full-library numbers.
- `36_exosome_biomimetic_surface_model.md` — current EV/sEV biomimetic optical-model rationale.
- `46_全量计算性能优化复核.md` — current performance notes for the recompute path, including artifact profiles, summary-only streaming, trajectory context, worker-local invariant caches, the 16C/32T switch back to scalar/off defaults, and the rejected `block_lane_order` default switch.
- `47_EV_NODI全量结果分层分析报告.md` — historical 32032-case four-wavelength all-crossing reader-facing analysis from the previous full-library run; useful as a baseline, but its backing formal result files have been removed pending a fresh dual-lens recompute.
- `47_ev_design_full_grid_analysis/` — historical derived CSV tables backing report 47, including mechanism-chain, wavelength-ratio, geometry-effect, candidate-detection, 404-vs-660 decomposition, deep-channel usability, gold-gate sensitivity, PEG geometry scenarios, and EV size-weighted ranking tables.

2026-05-02 result cleanup update: the previous formal full-library result files and root-level size-weighted route analysis have been deleted from `results/`. Report 47 remains a historical all-crossing baseline, but new full-grid reruns must regenerate the source summary and size-weighted route analysis so all-crossing and selected-annulus rankings can be reviewed side by side; stale source tables are now treated as selected-annulus unavailable rather than producing synthetic selected ranks.

2026-05-01 Tsuyama Table S1 audit update: the code now has an explicit Tsuyama 2022 Supplementary Table S1 fixed-index Au/Ag audit profile for paper-claim checks only. It improves the 660 nm Ag/Au mean-peak ratio but still does not make selected-annulus detection/readout numerically equivalent to the paper's Fig. 5 / Table S1 signal-ratio or SVM classification metrics.

2026-05-01 selected-annulus joint-fit update: `tools/tsuyama_selected_annulus_joint_fit.py` is now the explicit paper-fit lane for Tsuyama selected-annulus alignment. Schema v2 scores both 800x550 and 1200x550 paper geometries for selected-annulus detection rates, Ag/Au peak ratios, Au size scaling, and Au30/Au20 SNR ratio. The current 10000-event v2 paper-fit best is `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit`: it applies bounded silver transfer plus an explicit Au power-law size-response correction from raw exponent `3.263` to paper target `2.300` with delta `-0.963` and no guardrail penalty. These transfer/size terms remain paper-fit lenses and do not change raw detection or global simulator defaults.

2026-05-01 classification-lane update: `tools/tsuyama_2022_classification_lane.py` exports linked 488/532 features for the 2022 Au40/Au60/Ag40/Ag60 SVM claim. The v2 lane uses the detected 488 pulse window and the 532 maximum within that window; the `400` events/class smoke writes `1600` linked rows and `849` paper-SVM-usable rows, but marks `svm_accuracy_claim_level = no_accuracy_claim` because optional `scikit-learn` is not available in the current project dependency set.

2026-05-01 pre-fullgrid EV robustness update: `results/tsuyama_selected_annulus_pre_fullgrid_ev_robustness_20260501/` verifies the selected-annulus paper-fit EV targeted profile across seeds `42 / 314 / 2718` at `3000` events/seed with `8` workers. All-crossing and selected-annulus top1 routes are seed-stable for all four EV size priors; selected-annulus top1 is `488 nm / 600x1500 nm`.

Deleted current-result reports:

- `35.4_最新全量数据库全面复核与选型报告.md`

That file was tied to deleted or stale full-library results. New current-result reporting should continue from report 47 unless a later complete full-library run supersedes it.
