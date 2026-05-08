# Tsuyama Selected-Annulus Joint Fit

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

## Scope

- This is a paper-fitted selected-annulus calibration lane.
- It does not change global simulator defaults or EV route ranking by itself.
- The score uses 800x550 and 1200x550 selected-annulus detection rates, Ag/Au peak ratios, Au size scaling, and Au30/Au20 SNR ratio.
- Ag/Au transfer-fit variants use one residual transfer gain per wavelength, then score both paper geometries under that same gain.
- Au size-scaling is still scored on peak height, while alternate observables are exported as diagnostics only.
- `required_silver_transfer_gain_*` reports the residual wavelength/material gain needed to match Table S1 ratios after the simulated trace output.
- Variants ending in `signal_transfer_fit` explicitly apply that residual gain inside the paper-fit score, with a gain regularization and guardrail.
- The transfer-fit variants do not alter simulated detection rates or global material defaults; they only calibrate the paper-fit signal-ratio lens.

## Run Metadata

- schema: `tsuyama_2022_selected_annulus_joint_fit_v2`
- scenario: `nodi_2022_10sigma_single`
- n_events: `1000`
- workers: `8`
- random_seed: `42`
- candidates: `1`

## Top Candidates

| candidate_id                                                 | joint_fit_score | selected_rate_score | signal_ratio_score | size_exponent_score | snr_ratio_score | transfer_gain_regularization_score | transfer_gain_guardrail_penalty | paper_fit_status                        | joint_signal_transfer_mode        | au20_660_800x550_selected_annulus_rate | au30_660_800x550_selected_annulus_rate | au40_660_800x550_selected_annulus_rate | au60_660_800x550_selected_annulus_rate | au20_660_1200x550_selected_annulus_rate | au30_660_1200x550_selected_annulus_rate | au40_660_1200x550_selected_annulus_rate | au60_660_1200x550_selected_annulus_rate | ag40_to_au40_peak_ratio_488 | ag40_to_au40_peak_ratio_532 | ag40_to_au40_peak_ratio_660 | ag40_to_au40_calibrated_peak_ratio_488 | ag40_to_au40_calibrated_peak_ratio_532 | ag40_to_au40_calibrated_peak_ratio_660 | required_silver_transfer_gain_488 | required_silver_transfer_gain_532 | required_silver_transfer_gain_660 | applied_silver_transfer_gain_488 | applied_silver_transfer_gain_532 | applied_silver_transfer_gain_660 | au_size_exponent_median | au_size_exponent_peak_height_median | au_size_exponent_local_snr_median | au_size_exponent_peak_margin_z_median | au_size_exponent_peak_height_times_width_median | au_size_exponent_800x550_median | au_size_exponent_1200x550_median | au_size_exponent_best_observable | au_size_exponent_diagnostic_status          | au30_to_au20_snr_ratio_median | annulus_fraction_min | joint_cfg_overrides_json |
| ------------------------------------------------------------ | --------------- | ------------------- | ------------------ | ------------------- | --------------- | ---------------------------------- | ------------------------------- | --------------------------------------- | --------------------------------- | -------------------------------------- | -------------------------------------- | -------------------------------------- | -------------------------------------- | --------------------------------------- | --------------------------------------- | --------------------------------------- | --------------------------------------- | --------------------------- | --------------------------- | --------------------------- | -------------------------------------- | -------------------------------------- | -------------------------------------- | --------------------------------- | --------------------------------- | --------------------------------- | -------------------------------- | -------------------------------- | -------------------------------- | ----------------------- | ----------------------------------- | --------------------------------- | ------------------------------------- | ----------------------------------------------- | ------------------------------- | -------------------------------- | -------------------------------- | ------------------------------------------- | ----------------------------- | -------------------- | ------------------------ |
| baseline_current_estimates__paper_5sigma_signal_transfer_fit | 1.21287         | 0.00764837          | 0.000158735        | 1.9083              | 0.0352686       | 0.23312                            | 0                               | candidate_joint_fit_with_paper_transfer | fit_required_silver_by_wavelength | 0.370844                               | 0.723785                               | 0.856777                               | 0.920918                               | 0.300518                                | 0.629534                                | 0.826425                                | 0.858612                                | 1.48263                     | 0.693691                    | 0.849691                    | 4.22222                                | 1.30882                                | 2.65625                                | 2.84779                           | 1.88675                           | 3.12614                           | 2.84779                          | 1.88675                          | 3.12614                          | 3.26699                 | 3.26699                             | 3.14529                           | 3.36454                               | 4.40698                                         | 3.25109                         | 3.2675                           | local_snr                        | alternate_observable_closer_to_paper_target | 3.31813                       | 0.386                | {"threshold_sigma":5.0}  |

## Output Files

- `selected_annulus_joint_fit_raw_v2.csv`
- `selected_annulus_joint_fit_summary_v2.csv`
- `selected_annulus_joint_fit_meta_v2.json`
