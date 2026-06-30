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
| Angle-convention guard | Loose descriptor rows carrying `sidewall_deg`, `sidewall_angle`, or `taper_angle` cannot pass without an explicit angle convention. | `test_geometry_descriptor_v2_rejects_bare_ambiguous_angle_fields` |
| Descriptor identity signature binding | PRS/EAS sidewall v2 signatures bind angle convention, COMSOL angle, top/depth/bottom dimensions, source descriptor hash, runtime binding version, closure status/policy, runtime guard status, and reject numeric `runtime_top_aperture_nm` when the row has no runtime aperture value. | `test_position_response_sidewall_v2_rejects_signature_runtime_aperture_without_row_value`, `test_effective_aperture_sidewall_v2_rejects_signature_runtime_aperture_without_row_value` |
| Measured-profile lookup guard | Runtime channel-geometry diagnostics and batch outputs keep `measured_profile_lookup` blocked metadata-only until profile load/hash/validation exists, and bind measured-profile status fields into observation signatures. | `test_measured_profile_lookup_with_path_stays_blocked_until_loaded_and_validated`, `test_observation_signature_separates_secondary_geometry_descriptors`, `test_batch_signature_keeps_measured_profile_lookup_blocked_until_validated` |
| Measured-geometry claim guard | Descriptor v2 measured-geometry claims require loaded and validated measured-profile metadata; path/hash/source alone are insufficient. | `test_geometry_descriptor_v2_rejects_unloaded_measured_geometry_metadata` |
| Sampler propagation | Trapezoid sampler emits support status, steric block reason, nearest-wall distances, and surface gap diagnostics. | `nodi_simulator/utils.py` |
| Actual runtime signature | Event-loop and pure-advection block batches bind sampler diagnostics into `observation_signature`. | `test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics` |
| PRS sidewall v2 signature | PRS rows require exact sampler/support/wall-distance signature fragments and row/signature binding. | `tests/test_nodi_comsol_next_artifacts_contracts.py` |
| Package C gate | Any PRS basis/source-basis field carrying `wall_distance` requires `includes_trajectory_near_wall_metrics=true` and `package_C_validation_status=pass`. | commit `dc12148` |
| Grain/admission prechecks | Package D and PRS validators reject D900-to-D1200 borrowing, direct edge4-to-edge20 promotion, and 220/300 nm large-tail auto-admission without exact steric support. | `test_position_response_sidewall_v2_rejects_D900_to_D1200_source_borrowing`, `test_position_response_sidewall_v2_rejects_edge4_to_edge20_direct_mapping`, `test_position_response_sidewall_v2_rejects_auto_tail_admission` |
| PRS propagated allowlist | Propagated trapezoid PRS rows allow only implemented sampler, flow, flow-control, and boundary states. | `test_position_response_sidewall_v2_rejects_unsupported_propagated_flow_control` |
| Propagation-status usage | Propagated PRS/EAS sidewall v2 rows cannot carry `geometry_not_propagated_reasons`; non-propagated rows must remain blocked/audit-labeled. | `test_effective_aperture_sidewall_v2_rejects_propagated_not_propagated_reason` |
| EAS generic surrogate guard | Generic `W_eff_surrogate_nm` must be an explicit numeric alias of a named sidewall surrogate; eta/rank fields stay disabled/no-rank. | commit `c9ea9b7` |
| Claim blacklist | Sidewall PRS/EAS artifacts and Package D precheck reject claim-promotion aliases including `rank_value`, `route_rank_value`, `sidewall_rank_value`, Package D `rank_under_surrogate`, `route_score_norm`, `sidewall_score_value`, `JRC_value`, `joint_route_class_candidate`, `chi_selected_flag`, `q_ch_weight`, `q_ch_weighting`, bare/unitized `flow_rate` and `Q`, `q_ch_m3_s`, and `comsol_Q_proxy`, plus positive `sidewall_aware=true` shortcuts. | `test_position_response_sidewall_v2_rejects_forbidden_flow_alias_columns`, `test_effective_aperture_sidewall_v2_rejects_forbidden_flow_alias_columns`, `test_sidewall_package_d_precheck_scans_forbidden_columns_even_when_flag_passes` |

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
python -m pytest tests/test_cross_section_geometry.py tests/test_nodi_comsol_next_artifacts_contracts.py tests/test_nodi_comsol_gate11_sidewall_convergence.py tests/test_nodi_comsol_gate12_sidewall_addendum_release_candidate.py tests/test_nodi_comsol_gate13_sidewall_guard_convergence.py tests/test_physics_core.py::TestIntegration::test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics tests/test_physics_core.py::TestIntegration::test_batch_signature_keeps_measured_profile_lookup_blocked_until_validated -q
```

Latest result:

```text
478 passed in 84.04s (0:01:24)
```

Additional focused verification after adding the latest claim-alias guards:

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
406 passed in 59.78s
python -m pytest tests/test_cross_section_geometry.py -q
38 passed in 0.17s
python -m pytest tests/test_physics_core.py -k channel_geometry -q
3 passed, 383 deselected in 0.92s
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
2. If a real measured-profile loader is added later, add implementation-level loader/hash/profile-schema tests before any `measured_geometry` runtime use.
3. Design, but do not silently enable, a validated trapezoid trajectory/flow model path.
