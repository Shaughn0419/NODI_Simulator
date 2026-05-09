# EV NODI realism v2 R7.1 operator artifact validation protocol analysis

## Decision

`PASS_R7_1_RESULTS_PREPARE_OPERATOR_ARTIFACT_GAP_REGISTER_ONLY`

The R7.1 protocol generation result is internally consistent and guardrailed. It supports only a future plan-only step for operator artifact gap registration. It does not authorize acquisition, experiments, solver cases, new scenarios, stochastic seeds, R8 planning or execution, route promotion, main-660 redefinition, selected-annulus changes, score-derived physical priors, calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, or biological specificity.

## Blocking findings

None.

The protocol generation stayed inside the plan-only evidence-definition lane.

## Scope checks

R7.1 generated protocol artifacts only:

```text
R7_1_operator_artifact_validation_protocol_generation_run = true
generation_type = protocol_artifact_requirements_only_no_measurement
evidence_module_count = 6
required_artifact_field_count = 30
new_case_rows_added = 0
new_scenario_bundles_added = 0
new_stochastic_seeds_added = 0
new_solver_cases_added = 0
new_experiments_started = 0
operator_artifact_acquisition_started = false
experimental_validation_started = false
R8_plan_preparation_authorized = false
R8_execution_authorized = false
```

The selected future recommendation is:

```text
prepare_operator_artifact_gap_register_plan_only
```

This is a planning target, not permission to acquire artifacts.

## Output set

The R7.1 result directory contains exactly the planned 12 files:

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

No R8, experiment, solver, new scenario, route-governance, selected-annulus, or calibrated-claim artifact was generated.

## Protocol content

R7.1 defines six evidence modules:

```text
reference_operating_band_artifact_protocol
BFP_slit_ROI_alignment_operator_artifact_protocol
fabrication_metrology_margin_artifact_protocol
wall_PEG_transport_proxy_validation_protocol
particle_stratum_residual_validation_protocol
optional_900_governance_diagnostic_protocol
```

Across those modules, 30 required artifact fields are registered. Every protocol row keeps:

```text
field_required_before_physical_prior_use = true
field_required_before_post_v2_validation_program = true
authorizes_measurement = false
authorizes_experiment = false
authorizes_solver_case = false
authorizes_route_promotion = false
authorizes_main_660_redefinition = false
uses_source_v1_relative_score_as_physical_input = false
allows_route_specific_multiplier = false
allows_particle_specific_fit = false
protocol_status = requirement_defined_not_executed
```

This is the correct boundary: R7.1 turns R7's artifact gaps into a checklist, not data.

## Claim and governance guardrails

Claim boundaries remain:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
calibrated_SNR_or_event_probability_claim_emitted = false
absolute_LOD_or_true_concentration_claim_emitted = false
biological_specificity_claim_emitted = false
```

Exact legacy CSV headers remain absent:

```text
detector_SNR
calibrated_detector_SNR
```

Route governance remains closed:

```text
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
selected_annulus_bound_change_authorized = false
route_specific_manual_prior_multiplier_attempted = false
scenario_specific_per_route_fit_attempted = false
particle_specific_empirical_fit_attempted = false
score_derived_physical_prior_attempted = false
```

## Critical interpretation

R7.1 is useful because it prevents the next stage from quietly treating missing physical/operator evidence as already available. The plan now says exactly what evidence is required before reference-band, BFP/slit/ROI, fabrication/metrology, wall/transport, particle residual, or optional-900 diagnostics can influence any future route-prior model.

The result does not reduce scientific uncertainty by itself. It only makes the uncertainty auditable.

## Next action

The only next action supported is:

```text
prepare_operator_artifact_gap_register_plan_only
```

That future plan must remain plan-only and must define:

```text
which artifacts would be acquired
which fields each artifact must contain
acceptance criteria
failure criteria
chain of custody / provenance
which post-v2 dependency class would be needed outside v2
explicit stop gates ensuring no acquisition starts inside v2
```

It must still prohibit R8 execution, route promotion, main-660 redefinition, selected-annulus changes, score-derived physical priors, and calibrated/absolute claims.

## Verification

Focused R7.1 protocol and plan tests:

```text
15 passed in 1.11s
```

R7.1/R7/R6/R5.3/contract context suite:

```text
90 passed in 4.22s
```

Static check:

```text
ruff check realism_v2.py \
  tools/one_shot/ev_nodi_realism_v2_R7_1_operator_artifact_validation_protocol.py \
  tests/test_realism_v2_R7_1_operator_artifact_validation_protocol.py \
  tests/test_realism_v2_R7_1_operator_artifact_validation_plan.py

All checks passed
```

Full test suite:

```text
929 passed in 207.32s
```
