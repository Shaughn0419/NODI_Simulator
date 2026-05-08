# EV NODI realism v2 R7.1 operator artifact / validation plan

## Decision requested

This is a self-reviewed plan-only artifact after:

```text
PASS_R7_RESULTS_PREPARE_OPERATOR_ARTIFACT_GAP_REGISTER_PLAN_ONLY
```

The plan does not authorize operator artifact generation, physical measurement, experiments, solver cases, new scenarios, stochastic seeds, R8 planning, R8 execution, route promotion, main-660 redefinition, selected-annulus changes, calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, biological specificity, or any score-derived physical prior.

## Why this plan exists

R7 supported the width-family explanation as a mechanism hypothesis, but it also found that the strongest unresolved pieces are not more route-prior fitting. They are missing physical/operator artifacts:

```text
physical_operator_artifact_gap_count = 3
executable_existing_artifact_mechanistic_candidate_count = 2
particle_stratum_residual_warning_count = 50
```

The next useful step is therefore to define the artifact-gap requirements, not to execute R8 or collect new measurements.

## Evidence modules

The plan registers six modules:

```text
reference_operating_band_artifact_protocol
BFP_slit_ROI_alignment_operator_artifact_protocol
fabrication_metrology_margin_artifact_protocol
wall_PEG_transport_proxy_validation_protocol
particle_stratum_residual_validation_protocol
optional_900_governance_diagnostic_protocol
```

All modules are requirements/protocol definitions only. Each module keeps:

```text
authorizes_measurement = false
authorizes_experiment = false
authorizes_solver_case = false
authorizes_route_promotion = false
authorizes_main_660_redefinition = false
uses_source_v1_relative_score_as_physical_input = false
allows_route_specific_multiplier = false
allows_particle_specific_fit = false
```

## Main safeguards

R7.1 explicitly forbids:

```text
R8_plan_preparation
R8_execution
new_experiment_started
new_solver_case_started
new_scenario_bundle_added
new_stochastic_seed_added
route_promotion
main_660_redefinition
selected_annulus_boundary_change
route_specific_manual_multiplier
scenario_specific_per_route_fit
particle_specific_empirical_fit
score_derived_physical_prior
calibrated_SNR_or_event_probability_claim
absolute_LOD_or_true_concentration_claim
biological_specificity_claim
```

The point is to turn R7's operator gaps into a clean evidence checklist before any future collection or computation is considered.

## Required future outputs

If a later self-review authorizes only protocol generation, the output set is limited to:

```text
R7_1_operator_artifact_validation_manifest.csv
R7_1_reference_operating_band_artifact_protocol.csv
R7_1_BFP_slit_ROI_alignment_operator_artifact_protocol.csv
R7_1_fabrication_metrology_margin_artifact_protocol.csv
R7_1_wall_PEG_transport_proxy_validation_protocol.csv
R7_1_particle_stratum_residual_validation_protocol.csv
R7_1_optional_900_governance_protocol.csv
R7_1_claim_boundary_guardrail_summary.csv
R7_1_stop_gate_summary.csv
R7_1_next_stage_recommendation_matrix.csv
run_manifest.json
R7_1_operator_artifact_validation_report.md
```

## Current conclusion

R7.1 is intentionally conservative. It preserves the R7 conclusion that width-family regularization is plausible, while refusing to treat missing reference/BFP/metrology operators as if they had already been measured or computed.
