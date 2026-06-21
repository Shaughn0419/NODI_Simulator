# NODI next artifacts boundary and forbidden claims

Date: 2026-06-17

Status:

```text
boundary_contract_only
no runner implementation
no runner execution
no NODI simulation
no COMSOL run
no production artifact
```

This boundary applies to the next-artifact planning bundle for:

```text
NODI_POSITION_RESPONSE_SURFACE
NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY
```

## 1. Allowed current work

Allowed:

```text
implementation planning
schema contract design
validator rule design
bounded dry/smoke path design
manifest/source-package planning
external review prompt design
```

Not allowed:

```text
runner implementation
runner execution
NODI simulation
full production run
production response-surface artifact
production aperture-surrogate artifact
COMSOL run
JOINT_ROUTE_CLASS regeneration
```

## 2. Forbidden positive claims

The planning bundle and future validators must reject positive claims of:

```text
q_ch * eta
q_ch * chi_selected * eta
yield
winner
true W_eff
measured geometry
optical solver output
fabrication release
calibrated detector claim
EV detection probability
throughput detection
scalar joint score
P3 solver conclusion
```

These terms may appear only in negative-boundary text, validator failure
messages, or forbidden-claim lexicons.

## 3. Position-response boundary

`NODI_POSITION_RESPONSE_SURFACE` is:

```text
conditional optical response by NODI synthetic initial-position bin
not COMSOL transported occupancy
not q_ch weighted
not yield
not calibrated detection probability
not a joint score
```

NODI-only rows must carry:

```text
row_scope = response_surface_bin
position_distribution_basis = nodi_synthetic_initial_position
flow_condition_id = nodi_position_response_surface_v1_not_comsol_transport
flow_condition_scope = nodi_response_surface_not_transport_distribution
flow_condition_claim_boundary = nodi_synthetic_position_response_not_transport_occupancy
view_physical_independence_flag = false
not_comsol_transport_distribution = true
not_qch_weighted = true
not_yield = true
not_detection_probability = true
```

`p1b_w800_qch_splitmid_20260617` is not a global flow condition. It is not
allowed in production response-surface rows. It may appear only as a scoped W800
q_ch reference in a manifest/provenance sidecar tied to:

```text
P1B-W800-001
P1B-W800-002
roadmap/P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv
SHA256 = BA92A77F92E0D972D7059DD8A60B5696AA3C649E5686AD3B474D6112F265ECEC
JPI-028
```

## 4. Aperture-surrogate boundary

`NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY` is:

```text
dry sensitivity only
surrogate aperture analysis only
not measured geometry
not true optical W_eff
not optical solver output
not fabrication release
not final route decision
```

COMSOL descriptor claim boundary:

```text
nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

Aperture artifact claim boundary:

```text
effective_aperture_surrogate_sensitivity_only
```

## 5. 500 nm boundary

500 nm remains:

```text
RC13 / out_of_particle_library_scope
eta blank
no interpolation
no zero proxy
no low optical proxy
not decision-use
```

## 6. P3 boundary

P3 flags are solver-contract triggers only:

```text
solver_contract_trigger_flag = true
```

does not mean:

```text
solver execution authorized
non-rectangular optical solver result exists
P3 conclusion reached
```

## 7. Current final status

```text
READY_FOR_USER_AUTHORIZATION_TO_IMPLEMENT_RUNNERS
```

This status means the implementation plan is ready for user review. It does not
authorize implementation or execution.
