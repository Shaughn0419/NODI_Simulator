# EV/NODI realism v2 no-measured-data closure analysis

## Decision

`V2_CLOSED_NO_MEASURED_DATA_SYNTHETIC_PRIOR_MODEL_ONLY`

The closure bundle is intended to stop v2 at the correct boundary: an
instrument-aware realism simulation supplement with no measured data and no
calibrated physical claims. Its job is to make the original engineering logic
and baseline simulation result lanes more credible by adding explicit
reality-biased instrument, route, blank, sidecar, and governance constraints. It
carries forward R7.2 artifact gaps as post-v2 dependencies and does not start
artifact acquisition, bench measurement, experiments, solver cases, R8 planning,
route promotion, or main-660 redefinition.

## Scope

The closure output is generated from existing R7.2 artifacts and two v2
governance reports only. It adds no route rows, scenarios, stochastic seeds,
solver cases, experiments, or measured artifacts.

The final closure preserves:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
primary_metric = detectability_relative_prior_score
detected_events_source = relative_prior_score_proxy_count_not_observed_events
```

## Route Governance

Main-660 remains locked to:

```text
660_800x1400
660_800x1500
```

Context routes remain warnings only. Optional `660_900x1400` remains an optional
robustness probe. Selected-annulus remains a parallel diagnostic lens and does
not replace all-crossing ranking.

## Scientific Boundary

R6 supports a stable low-dimensional width-family explanatory hypothesis for the
R5.2 warning. R7 decomposes that hypothesis and identifies missing
operator/physical artifacts. R7.2 registers those artifacts as post-v2
dependencies. None of those steps calibrates the model against real instrument
data.

## Final Status

v2 is closed as a no-measured-data realism-simulation supplement. Any
acquisition, operator artifact resolution, experimental validation, or calibrated
detector claim belongs to a separately scoped post-v2 program.
