# Tsuyama gold-aligned NODI detection lane report

## One-page conclusion

- full_grid_decision: `go_full_grid`
- full_grid_allowed: `True`
- blockers: `none`

## Method boundary

- Lane A only: NODI 2022/2024 gold-aligned relative detection lane.
- Lane B POD 2020 is a claim boundary only; it is not used as NODI calibration.
- Synthetic blank, when used, is a guardrail and not empirical blank calibration.

## Existing gate-only baseline

- simulation_status: `no_simulation_read_existing_csvs_only`
- current_pass_count_total: `74`
- relaxed10_pass_count_total: `138`
- relaxed05_pass_count_total: `188`

## Gold targeted sweep

- smoke rows: `260`, scenarios: `['nodi_2022_10sigma_single', 'nodi_2022_5sigma_single_sensitivity', 'ev_nodi_5sigma_single_current_design', 'paired_2024_5sigma_diag', 'paired_2024_10sigma_diag']`
- final rows: `260`, scenarios: `['nodi_2022_10sigma_single', 'nodi_2022_5sigma_single_sensitivity', 'ev_nodi_5sigma_single_current_design', 'paired_2024_5sigma_diag', 'paired_2024_10sigma_diag']`

## Blank FPR guardrail

- blank rows/meta rows: `10`
- source blank_summary: `None`

## Feasible scenarios

- ev_nodi_5sigma_single_current_design: scenario_config_feasible=True, feasible_case_count=12, paired_diag_pass=False
- nodi_2022_10sigma_single: scenario_config_feasible=True, feasible_case_count=12, paired_diag_pass=False
- nodi_2022_5sigma_single_sensitivity: scenario_config_feasible=True, feasible_case_count=12, paired_diag_pass=False
- paired_2024_10sigma_diag: scenario_config_feasible=False, feasible_case_count=0, paired_diag_pass=True
- paired_2024_5sigma_diag: scenario_config_feasible=False, feasible_case_count=0, paired_diag_pass=True

## EV targeted transfer and ranking

- ranking_change_profile_count: `12`
- primary ranking lens: `all_crossing_weighted_stable_then_detection`
- selected-annulus ranking lens: `weighted_selected_detector_mode_annulus_detection_rate_then_stable`
- selected_annulus_top3_diff_profile_count: `12`
- comparison_support_status: `targeted_support_not_bitwise`

## Full-grid decision

Full-grid is not run by this v1 tool. It is allowed only when the targeted lane satisfies the explicit go/no-go gate. Selected-annulus ranking is a parallel analysis lens and does not replace the primary go/no-go gate.

## Claim boundaries

- no calibrated SNR
- no absolute LOD
- no absolute EV concentration
- no biological EV specificity
- synthetic blank is not empirical blank calibration
