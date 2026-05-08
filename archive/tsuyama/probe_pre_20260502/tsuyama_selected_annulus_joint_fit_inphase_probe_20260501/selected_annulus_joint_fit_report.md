# Tsuyama Selected-Annulus Joint Fit

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

## Scope

- This is a paper-fitted selected-annulus calibration lane.
- It does not change global simulator defaults or EV route ranking by itself.
- The score uses selected-annulus detection rates, Ag/Au peak ratios, Au size scaling, and Au30/Au20 SNR ratio.
- `required_silver_transfer_gain_*` reports the residual wavelength/material gain needed to match Table S1 ratios after the simulated trace output.

## Run Metadata

- schema: `tsuyama_2022_selected_annulus_joint_fit_v1`
- scenario: `nodi_2022_10sigma_single`
- n_events: `300`
- workers: `8`
- random_seed: `42`
- candidates: `2`

## Top Candidates

| candidate_id                                                           | joint_fit_score | selected_rate_score | signal_ratio_score | size_exponent_score | snr_ratio_score | paper_fit_status                             | au20_660_selected_annulus_rate | au30_660_selected_annulus_rate | au40_660_selected_annulus_rate | au60_660_selected_annulus_rate | ag40_to_au40_peak_ratio_488 | ag40_to_au40_peak_ratio_532 | ag40_to_au40_peak_ratio_660 | required_silver_transfer_gain_488 | required_silver_transfer_gain_532 | required_silver_transfer_gain_660 | au_size_exponent_median | au30_to_au20_snr_ratio_median | annulus_fraction_min | joint_cfg_overrides_json                                                 |
| ---------------------------------------------------------------------- | --------------- | ------------------- | ------------------ | ------------------- | --------------- | -------------------------------------------- | ------------------------------ | ------------------------------ | ------------------------------ | ------------------------------ | --------------------------- | --------------------------- | --------------------------- | --------------------------------- | --------------------------------- | --------------------------------- | ----------------------- | ----------------------------- | -------------------- | ------------------------------------------------------------------------ |
| baseline_current_estimates__paper_inphase_absolute                     | 2.67837         | 0.0136441           | 0.9236             | 1.5769              | 0.0581485       | candidate_needs_signal_transfer_or_phase_fit | 0.381356                       | 0.711864                       | 0.822034                       | 0.889831                       | 1.47475                     | 0.704606                    | 0.856539                    | 2.863                             | 1.85753                           | 3.10114                           | 3.17902                 | 3.49992                       | 0.393333             | {"pulse_detection_mode":"absolute","readout_observable_mode":"in_phase"} |
| velocity_0p15mmps_low_noise_stack_fluxmix_0p10__paper_inphase_absolute | 3.30246         | 0.0988538           | 0.966198           | 2.47012             | 0.0722941       | candidate_needs_signal_transfer_or_phase_fit | 0.7                            | 0.891667                       | 0.9                            | 0.975                          | 1.41275                     | 0.687034                    | 0.855149                    | 2.98865                           | 1.90503                           | 3.10618                           | 3.40016                 | 3.59835                       | 0.4                  | {"pulse_detection_mode":"absolute","readout_observable_mode":"in_phase"} |

## Output Files

- `selected_annulus_joint_fit_raw_v1.csv`
- `selected_annulus_joint_fit_summary_v1.csv`
- `selected_annulus_joint_fit_meta_v1.json`
