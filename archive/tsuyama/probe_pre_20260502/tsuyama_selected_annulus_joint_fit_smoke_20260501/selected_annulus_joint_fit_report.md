# Tsuyama Selected-Annulus Joint Fit

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
- candidates: `6`

## Top Candidates

| candidate_id                                                             | joint_fit_score | selected_rate_score | signal_ratio_score | size_exponent_score | snr_ratio_score | paper_fit_status                             | au20_660_selected_annulus_rate | au30_660_selected_annulus_rate | au40_660_selected_annulus_rate | au60_660_selected_annulus_rate | ag40_to_au40_peak_ratio_488 | ag40_to_au40_peak_ratio_532 | ag40_to_au40_peak_ratio_660 | required_silver_transfer_gain_488 | required_silver_transfer_gain_532 | required_silver_transfer_gain_660 | au_size_exponent_median | au30_to_au20_snr_ratio_median | annulus_fraction_min | joint_cfg_overrides_json                     |
| ------------------------------------------------------------------------ | --------------- | ------------------- | ------------------ | ------------------- | --------------- | -------------------------------------------- | ------------------------------ | ------------------------------ | ------------------------------ | ------------------------------ | --------------------------- | --------------------------- | --------------------------- | --------------------------------- | --------------------------------- | --------------------------------- | ----------------------- | ----------------------------- | -------------------- | -------------------------------------------- |
| baseline_current_estimates__paper_5sigma_sensitivity                     | 2.82955         | 0.0051031           | 0.931547           | 1.87003             | 0.052683        | candidate_needs_signal_transfer_or_phase_fit | 0.364407                       | 0.70339                        | 0.830508                       | 0.90678                        | 1.46963                     | 0.692946                    | 0.85822                     | 2.87298                           | 1.88878                           | 3.09507                           | 3.25724                 | 3.45952                       | 0.393333             | {"threshold_sigma":5.0}                      |
| baseline_current_estimates                                               | 2.85928         | 0.0762549           | 0.938465           | 1.7595              | 0.052683        | candidate_needs_signal_transfer_or_phase_fit | 0.245763                       | 0.5                            | 0.711864                       | 0.881356                       | 1.46287                     | 0.698429                    | 0.850329                    | 2.88626                           | 1.87395                           | 3.12379                           | 3.22852                 | 3.45952                       | 0.393333             | {}                                           |
| baseline_current_estimates__paper_refphase_flat                          | 2.91932         | 0.139675            | 0.916961           | 1.82971             | 0.0617398       | candidate_needs_signal_transfer_or_phase_fit | 0.194915                       | 0.423729                       | 0.711864                       | 0.872881                       | 1.49293                     | 0.703297                    | 0.855256                    | 2.82815                           | 1.86098                           | 3.10579                           | 3.24687                 | 3.52569                       | 0.393333             | {"reference_spatial_phase_strength_rad":0.0} |
| velocity_0p15mmps_low_noise_stack_fluxmix_0p10__paper_refphase_flat      | 3.07382         | 0.0153569           | 0.961516           | 2.20511             | 0.0657531       | candidate_needs_signal_transfer_or_phase_fit | 0.225                          | 0.783333                       | 0.925                          | 0.983333                       | 1.44505                     | 0.676871                    | 0.849339                    | 2.92185                           | 1.93364                           | 3.12743                           | 3.33947                 | 3.55383                       | 0.4                  | {"reference_spatial_phase_strength_rad":0.0} |
| velocity_0p15mmps_low_noise_stack_fluxmix_0p10__paper_5sigma_sensitivity | 3.20833         | 0.0815294           | 0.970089           | 2.31477             | 0.0584794       | candidate_needs_signal_transfer_or_phase_fit | 0.516667                       | 0.9                            | 0.958333                       | 0.983333                       | 1.40118                     | 0.687997                    | 0.856889                    | 3.01333                           | 1.90237                           | 3.09988                           | 3.36501                 | 3.50232                       | 0.4                  | {"threshold_sigma":5.0}                      |
| velocity_0p15mmps_low_noise_stack_fluxmix_0p10                           | 3.21982         | 0.0200654           | 0.960242           | 2.50006             | 0.0584794       | candidate_needs_signal_transfer_or_phase_fit | 0.35                           | 0.825                          | 0.925                          | 0.975                          | 1.41889                     | 0.688122                    | 0.857554                    | 2.97572                           | 1.90202                           | 3.09747                           | 3.40681                 | 3.50232                       | 0.4                  | {}                                           |

## Output Files

- `selected_annulus_joint_fit_raw_v1.csv`
- `selected_annulus_joint_fit_summary_v1.csv`
- `selected_annulus_joint_fit_meta_v1.json`
