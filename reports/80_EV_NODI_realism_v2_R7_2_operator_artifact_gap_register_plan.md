# EV NODI realism v2 R7.2 operator artifact gap register plan

## Decision requested

This is a self-reviewed plan-only artifact after:

```text
PASS_R7_1_RESULTS_PREPARE_OPERATOR_ARTIFACT_GAP_REGISTER_ONLY
```

The maximum future action inside v2 is a no-measured-data closure bundle. This plan does not authorize operator-artifact acquisition, bench measurement, experiments, solver cases, new scenarios, stochastic seeds, R8 planning, R8 execution, route promotion, main-660 redefinition, selected-annulus changes, score-derived physical priors, calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, or biological specificity.

## Why this plan exists

R7.1 converted R7's missing physical/operator evidence into protocol requirements:

```text
evidence_module_count = 6
required_artifact_field_count = 30
```

R7.2 records those requirements as a post-v2 artifact gap register. It is not an acquisition plan and it does not collect artifacts.

## Artifact gap registry

Six artifact gaps are registered:

```text
reference_operating_band_artifact
BFP_slit_ROI_alignment_operator_artifact
fabrication_metrology_margin_artifact
wall_PEG_transport_proxy_artifact
particle_stratum_residual_artifact
optional_900_governance_diagnostic_artifact
```

The first three are physical/operator dependency gaps for any future post-v2 validation program. The latter three are diagnostic/proxy or governance gaps. All six remain:

```text
gap_status = registered_no_acquisition
gap_resolution_authorized = false
bench_measurement_authorized = false
experiment_authorized = false
solver_case_authorized = false
route_promotion_authorized = false
main_660_redefinition_authorized = false
uses_source_v1_relative_score_as_physical_input = false
allows_route_specific_multiplier = false
allows_particle_specific_fit = false
```

## Stop gates

The plan fails closed on acquisition, bench measurement, R8, new scenarios, new seeds, solver cases, experiments, route promotion, main-660 redefinition, selected-annulus changes, forbidden fits, score-derived physical priors, calibrated claims, absolute claims, and biological-specificity claims.

## Current conclusion

R7.2 is valid as a plan-only gap register. It intentionally stops before acquisition. The next step should be v2 no-measured-data closure, with any real artifact collection left outside v2 as a separately scoped future program.
