# NODI Sidewall-Angle Implementation Audit Packet

Date: 2026-06-30

Status: no-compute audit packet. No NODI production recomputation, no COMSOL launch, no `.mph` load, no route winner, no `route_score`, no `JRC`, no `q_ch` weighting, no yield, no detection probability, no fabrication release.

## Scope

This packet records the current implementation state for introducing sidewall angle into NODI while preserving the existing `ideal_rectangle` path. It is an implementation and validator audit, not a design conclusion.

The current supported split is:

- `ideal_rectangle`: retained as a native rectangular geometry path with rectangular sampler and wall-gap identities.
- `trapezoid_tapered_sidewalls`: supported for descriptor geometry, particle center-accessible support, sampler diagnostics, geometry-only wall-distance primitives, observation-signature binding, PRS/EAS v2 schema guards, and no-claim artifact validation.

## Completed Guards

| Area | Current status | Evidence |
| --- | --- | --- |
| Geometry primitive | `TrapezoidCrossSection` preserves unclipped bottom width, closure status, center support, and wall-normal particle support. | `nodi_simulator/cross_section_geometry.py`, `tests/test_cross_section_geometry.py` |
| Rectangle preservation | `ideal_rectangle` keeps rectangle-specific sampler/support/wall-gap identity. | `test_channel_diagnostics_keep_ideal_rectangle_wall_distance_identity` |
| Descriptor wall-distance identity | Channel geometry emits prefixed `channel_geometry_wall_distance_model` and claim level, avoiding collision with trajectory `wall_distance_model`. | commit `1f0c2bf` |
| Runtime top-aperture binding | `mask_width`, `top_cd`, and `post_bias_top_cd` cannot become propagated/runtime top apertures without `runtime_top_aperture_nm`, `top_cd_bias_nm`, `top_cd_bias_source`, and numeric consistency. | `test_geometry_descriptor_v2_accepts_mask_width_runtime_binding_with_bias_metadata` |
| Descriptor identity signature binding | PRS/EAS sidewall v2 signatures bind angle convention, COMSOL angle, top/depth/bottom dimensions, source descriptor hash, runtime binding version, closure status/policy, and runtime guard status. | `test_position_response_sidewall_v2_rejects_signature_bottom_width_mismatch`, `test_effective_aperture_sidewall_v2_rejects_signature_bottom_width_mismatch` |
| Sampler propagation | Trapezoid sampler emits support status, steric block reason, nearest-wall distances, and surface gap diagnostics. | `nodi_simulator/utils.py` |
| Actual runtime signature | Event-loop and pure-advection block batches bind sampler diagnostics into `observation_signature`. | `test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics` |
| PRS sidewall v2 signature | PRS rows require exact sampler/support/wall-distance signature fragments and row/signature binding. | `tests/test_nodi_comsol_next_artifacts_contracts.py` |
| Package C gate | Any PRS basis/source-basis field carrying `wall_distance` requires `includes_trajectory_near_wall_metrics=true` and `package_C_validation_status=pass`. | commit `dc12148` |
| PRS propagated allowlist | Propagated trapezoid PRS rows allow only implemented sampler, flow, and boundary states. | commit `c0ae571` |
| EAS generic surrogate guard | Generic `W_eff_surrogate_nm` must be an explicit numeric alias of a named sidewall surrogate; eta/rank fields stay disabled/no-rank. | commit `c9ea9b7` |
| Claim blacklist | Sidewall PRS/EAS artifacts reject exact claim-promotion aliases including `rank`, `route_rank`, `sidewall_rank`, `JOINT_ROUTE_CLASS`, `q_ch_weight`, and `q_ch_weighting`. | commit `fb17362` |

## Still Blocked

The following remain blocked and must not be inferred from current sidewall-aware rows:

- validated sloped-wall specular reflection;
- validated hindered diffusion under trapezoid Brownian trajectories;
- trapezoid Poiseuille or flux-weighted trapezoid flow model;
- trapezoid electrokinetic wall-distance grid;
- optical/reference-field solver output;
- wet pass probability, adhesion probability, clogging rate, time-to-clog, recovery, yield, detection probability;
- route winner, route rank, `route_score`, `JRC`, `chi_selected`, or `q_ch` weighting;
- production/runtime ingestion or fabrication release.

## Verification

Latest clean-tree sidewall mainline regression command:

```text
python -m pytest tests/test_cross_section_geometry.py tests/test_nodi_comsol_next_artifacts_contracts.py tests/test_nodi_comsol_gate11_sidewall_convergence.py tests/test_nodi_comsol_gate12_sidewall_addendum_release_candidate.py tests/test_nodi_comsol_gate13_sidewall_guard_convergence.py tests/test_physics_core.py::TestIntegration::test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics -q
```

Latest result:

```text
416 passed in 80.78s (0:01:20)
```

Additional focused verification after adding runtime top-aperture binding guards:

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
351 passed in 59.62s
```

## Current Go/No-Go

| Package | Status | Note |
| --- | --- | --- |
| Package A | pass for schema/descriptor/validator guard scope | No PRS/EAS data generation authorized by this packet. |
| Package B | pass for geometry primitive, sampler support, and actual signature binding | Flux-weighted trapezoid sampling remains blocked. |
| Package C | partial audit/guard pass | Geometry wall-distance primitive exists; validated hindered diffusion and specular reflection remain blocked. |
| Package D | validator/preflight guard pass only | Sidewall PRS/EAS pilot generation remains no-claim and blocked unless A/B and relevant C prechecks pass. |

## Next Safe Actions

1. Keep strengthening no-compute validators and mutation tests for profile/source-hash drift and geometry-source promotion.
2. Add explicit measured-profile load/hash/validation guards before any `measured_geometry` claim.
3. Design, but do not silently enable, a validated trapezoid trajectory/flow model path.
