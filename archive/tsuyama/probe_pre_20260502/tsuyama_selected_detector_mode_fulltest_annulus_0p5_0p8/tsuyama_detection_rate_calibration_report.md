# Tsuyama Detection-Rate Calibration Sensitivity

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

## Boundary

- This is a sensitivity/calibration lane, not a replacement for global defaults.
- Only estimated/surrogate parameters are changed.
- It uses Tsuyama 2022 NODI single-channel gold conclusions as broad target bands.
- The paper does not provide a direct ground-truth crossing-to-detection efficiency table; these bands are operational targets, not empirical rates.

## Target Bands

- Au20: `0.08-0.25` (target `0.15`) - 20 nm Au pulses are observed, but the paper notes not all particles may be detected.
- Au30: `0.30-0.55` (target `0.42`) - 30 nm Au is clearly stronger than 20 nm while still close enough for overlap discussion.
- Au40: `0.45-0.75` (target `0.60`) - 40 nm Au is robust enough to support pulse-height statistics and classification lanes.
- Au60: `0.55-0.85` (target `0.70`) - 60 nm Au is a robust positive class in the dual-wavelength classification lane.

## Protected Criteria

- `threshold_sigma` unchanged from paper-aligned scenario
- `threshold_tail` unchanged from paper-aligned scenario
- `min_peak_width_s` unchanged from paper-aligned scenario
- `min_peak_interval_s` unchanged from paper-aligned scenario
- `pulse_width_measure_mode` unchanged from paper-aligned scenario

## Run Metadata

- screen_events: `2000`
- verify_events: `10000`
- workers: `8`
- scenario: `nodi_2022_10sigma_single`
- cases: `((488, 800, 550), (532, 800, 550), (660, 800, 550))`

## Best Verified Candidate

- candidate_id: `velocity_0p15mmps_low_noise_stack_fluxmix_0p10_noise_0p0065`
- calibration_score: `0.0014000962252979`
- target_fit_status: `within_all_bands`
- overrides: `{"initial_position_distribution_mode":"flux_uniform_mixture_surrogate","initial_position_flux_weighted_mixture_fraction":0.1,"mean_flow_velocity_m_s":0.00015,"noise_std":0.0065,"post_readout_noise_std":0.001,"shot_noise_scale":0.0005}`

## Top Verified Candidates

| candidate_id                                                      | calibration_score | target_fit_status         | au20_median_detection_rate | au30_median_detection_rate | au40_median_detection_rate | au60_median_detection_rate | au20_median_selected_detector_mode_candidate_detection_rate | au30_median_selected_detector_mode_candidate_detection_rate | au40_median_selected_detector_mode_candidate_detection_rate | au60_median_selected_detector_mode_candidate_detection_rate | au20_median_selected_detector_mode_candidate_fraction | au30_median_selected_detector_mode_candidate_fraction | au40_median_selected_detector_mode_candidate_fraction | au60_median_selected_detector_mode_candidate_fraction | au20_median_selected_detector_mode_annulus_detection_rate | au30_median_selected_detector_mode_annulus_detection_rate | au40_median_selected_detector_mode_annulus_detection_rate | au60_median_selected_detector_mode_annulus_detection_rate | au20_median_selected_detector_mode_annulus_fraction | au30_median_selected_detector_mode_annulus_fraction | au40_median_selected_detector_mode_annulus_fraction | au60_median_selected_detector_mode_annulus_fraction | rho  | noise_std | shot_noise_scale | post_readout_noise_std | mean_flow_velocity_m_s | flow_profile_model | lockin_time_constant_s | reference_spatial_amplitude_strength | initial_position_distribution_mode | initial_position_center_bias_strength | initial_position_center_bias_min_confinement_ratio | initial_position_flux_weighted_mixture_fraction | nodi_transit_response_model | colored_noise_false_alarm_model | threshold_calibration_source | pulse_duration_estimation_policy | pulse_extraction_sampling_interval_s | post_readout_colored_noise_std | post_readout_colored_noise_tau_s | optical_illumination_beam_waist_y_m |
| ----------------------------------------------------------------- | ----------------- | ------------------------- | -------------------------- | -------------------------- | -------------------------- | -------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------- | ---- | --------- | ---------------- | ---------------------- | ---------------------- | ------------------ | ---------------------- | ------------------------------------ | ---------------------------------- | ------------------------------------- | -------------------------------------------------- | ----------------------------------------------- | --------------------------- | ------------------------------- | ---------------------------- | -------------------------------- | ------------------------------------ | ------------------------------ | -------------------------------- | ----------------------------------- |
| velocity_0p15mmps_low_noise_stack_fluxmix_0p10_noise_0p0065       | 0.0014001         | within_all_bands          | 0.1342                     | 0.4377                     | 0.5944                     | 0.6645                     | 0.16247                                                     | 0.535544                                                    | 0.737469                                                    | 0.838224                                                    | 0.8244                                                | 0.817                                                 | 0.8054                                                | 0.7957                                                | 0.198841                                                  | 0.661542                                                  | 0.859375                                                  | 0.937054                                                  | 0.3968                                              | 0.3968                                              | 0.3968                                              | 0.3924                                              | 0.5  | 0.0065    | 0.0005           | 0.001                  | 0.00015                | rect_series        | 0.001                  | 0.35                                 | flux_uniform_mixture_surrogate     | 1                                     | 0.08                                               | 0.1                                             | time_constant_surrogate     | not_applied                     | gaussian_iid                 | interpolated_threshold_crossing  | nan                                  | 0                              | 0.001                            | nan                                 |
| velocity_0p15mmps_fluxmix_0p10_flowparabolic_rho_0p45_noise_0p008 | 0.00281416        | within_all_bands          | 0.1313                     | 0.458                      | 0.6368                     | 0.7233                     | 0.148563                                                    | 0.525832                                                    | 0.740293                                                    | 0.853294                                                    | 0.8823                                                | 0.8696                                                | 0.8588                                                | 0.8467                                                | 0.182209                                                  | 0.652515                                                  | 0.890321                                                  | 0.980288                                                  | 0.3957                                              | 0.3957                                              | 0.3957                                              | 0.3957                                              | 0.45 | 0.008     | 0.0005           | 0.001                  | 0.00015                | parabolic_rect     | 0.001                  | 0.35                                 | flux_uniform_mixture_surrogate     | 1                                     | 0.08                                               | 0.1                                             | time_constant_surrogate     | not_applied                     | gaussian_iid                 | interpolated_threshold_crossing  | nan                                  | 0                              | 0.001                            | nan                                 |
| baseline_current_estimates                                        | 0.217725          | outside_one_or_more_bands | 0.0508                     | 0.231                      | 0.4048                     | 0.5269                     | 0.0791401                                                   | 0.367191                                                    | 0.659498                                                    | 0.88258                                                     | 0.6419                                                | 0.6291                                                | 0.6138                                                | 0.597                                                 | 0.0838323                                                 | 0.376996                                                  | 0.66381                                                   | 0.859422                                                  | 0.4008                                              | 0.4008                                              | 0.3968                                              | 0.3948                                              | 0.5  | 0.01      | 0.001            | 0.002                  | 0.0002                 | rect_series        | 0.001                  | 0.35                                 | flux_weighted                      | 1                                     | 0.08                                               | 0.5                                             | time_constant_surrogate     | not_applied                     | gaussian_iid                 | interpolated_threshold_crossing  | nan                                  | 0                              | 0.001                            | nan                                 |

## Output Files

- `screen_gold_rows_v1.csv`
- `screen_candidate_summary_v1.csv`
- `verify_gold_rows_v1.csv`
- `verify_candidate_summary_v1.csv`
