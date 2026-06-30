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
| COMSOL descriptor profile hash binding | When `geometry_profile_source=comsol_descriptor`, sidewall PRS/EAS rows require `geometry_profile_sha256` to match `source_geometry_descriptor_sha`. | `test_position_response_sidewall_v2_rejects_comsol_descriptor_profile_sha_mismatch`, `test_effective_aperture_sidewall_v2_rejects_comsol_descriptor_profile_sha_mismatch` |
| Profile identity signature binding | Observation signatures bind `geometry_profile_source`, `geometry_claim_level`, and `metrology_status` in both actual batch signatures and PRS/EAS sidewall v2 rows. | `test_sidewall_observation_signature_records_geometry_propagation_fields`, `test_position_response_sidewall_v2_rejects_signature_profile_identity_mismatch`, `test_effective_aperture_sidewall_v2_rejects_signature_profile_identity_mismatch` |
| Gate14 no-auth implementation contract | Gate14 release contract keeps NODI sidewall guards review-only and accepts the known COMSOL Gate14 successor head while preserving the Gate13 package receipt boundary. | `test_nodi_comsol_gate14_sidewall_implementation_contract.py`, `test_nodi_comsol_gate13_sidewall_guard_convergence.py` |
| Measured-profile lookup guard | Runtime channel-geometry diagnostics and batch outputs keep `measured_profile_lookup` blocked metadata-only until profile load/hash/validation exists, and bind measured-profile status fields into observation signatures. | `test_measured_profile_lookup_with_path_stays_blocked_until_loaded_and_validated`, `test_observation_signature_separates_secondary_geometry_descriptors`, `test_batch_signature_keeps_measured_profile_lookup_blocked_until_validated` |
| Measured-geometry claim guard | Descriptor v2 measured-geometry claims require loaded and validated measured-profile metadata; path/hash/source alone are insufficient. | `test_geometry_descriptor_v2_rejects_unloaded_measured_geometry_metadata` |
| Sampler propagation | Trapezoid sampler emits support status, steric block reason, nearest-wall distances, and surface gap diagnostics. | `nodi_simulator/utils.py` |
| Actual runtime signature | Event-loop and pure-advection block batches bind sampler diagnostics into `observation_signature`. | `test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics` |
| PRS sidewall v2 signature | PRS rows require exact sampler/support/wall-distance signature fragments and row/signature binding. | `tests/test_nodi_comsol_next_artifacts_contracts.py` |
| Package C gate | Any PRS basis/source-basis field carrying `wall_distance` requires `includes_trajectory_near_wall_metrics=true` plus a future authorized Package C proof; current no-auth registry is empty and `package_C_validation_status=pass` fails closed. | `test_sidewall_package_d_precheck_blocks_near_wall_metrics_until_package_c_authorized` |
| Grain/admission prechecks | Package D and PRS validators reject D900-to-D1200 borrowing, direct edge4-to-edge20 promotion, and 220/300 nm large-tail auto-admission without exact steric support. | `test_position_response_sidewall_v2_rejects_D900_to_D1200_source_borrowing`, `test_position_response_sidewall_v2_rejects_edge4_to_edge20_direct_mapping`, `test_position_response_sidewall_v2_rejects_auto_tail_admission` |
| Blocked-bin consistency | PRS sidewall v2 rows require `bin_accessible` and `bin_particle_center_support_status` to agree; blocked bins require `blocked_reason`, `decision_use_allowed=false`, no neighbor fill, and no numeric response/proxy values. | `test_position_response_sidewall_v2_rejects_blocked_bin_neighbor_fill`, `test_position_response_sidewall_v2_rejects_blocked_bin_numeric_response`, `test_position_response_sidewall_v2_rejects_inaccessible_open_support_status`, `test_position_response_sidewall_v2_rejects_blocked_support_marked_accessible` |
| PRS propagated allowlist | Propagated trapezoid PRS rows allow only implemented sampler, flow, flow-control, and boundary states. | `test_position_response_sidewall_v2_rejects_unsupported_propagated_flow_control` |
| Propagation-status usage | Propagated PRS/EAS sidewall v2 rows cannot carry `geometry_not_propagated_reasons`; non-propagated rows must remain blocked/audit-labeled. | `test_effective_aperture_sidewall_v2_rejects_propagated_not_propagated_reason` |
| EAS generic surrogate guard | Generic `W_eff_surrogate_nm` must be an explicit numeric alias of a named sidewall surrogate; eta/rank fields stay disabled/no-rank. | commit `c9ea9b7` |
| Claim blacklist | Sidewall PRS/EAS artifacts and Package D precheck reject claim-promotion aliases including `rank_value`, `route_rank_value`, `sidewall_rank_value`, Package D `rank_under_surrogate`, `route_score_norm`, `sidewall_score_value`, `JRC_value`, `joint_route_class_candidate`, `chi_selected_flag`, `q_ch_weight`, `q_ch_weighting`, bare/unitized `flow_rate` and `Q`, `q_ch_m3_s`, and `comsol_Q_proxy`, plus positive `sidewall_aware=true` shortcuts. | `test_position_response_sidewall_v2_rejects_forbidden_flow_alias_columns`, `test_effective_aperture_sidewall_v2_rejects_forbidden_flow_alias_columns`, `test_sidewall_package_d_precheck_scans_forbidden_columns_even_when_flag_passes` |
| Validator CLI boundary | PRS, EAS, and Package D sidewall validators print `PASS_CONTEXT_ONLY_NOT_PRODUCTION`, not bare production-style `PASS`. | `test_sidewall_prs_validator_cli_accepts_valid_sidewall_csv`, `test_sidewall_eas_validator_cli_accepts_valid_sidewall_csv`, `test_sidewall_package_d_precheck_cli_accepts_valid_csv` |
| Production candidate policy | PRS production candidate rows and CSV validation reject sidewall v2 artifacts, `not_accepted_for_production=true`, and roadmap-only statuses. | `test_position_response_production_candidate_csv_blocks_sidewall_v2` |
| Gate23 static fixture packet | Gate22 source hashes are locked; 29 static fixture execution rows are executable without runtime; Package C proof registry is fail-closed. | `tests/test_nodi_comsol_gate23_sidewall_static_fixture_execution.py` |
| Gate24 Package C authorization ledger | Gate23 source hashes are locked; exact future Package C phrase matching is recorded but does not authorize Package C physics, proof-registry update, runtime, NODI recomputation, COMSOL launch, `.mph` load, or sidewall PRS/EAS numeric output. | `tests/test_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py` |
| Gate25 Package C design-review packet | Gate24 sources are locked; trajectory, near-wall diffusion, flow, electrokinetic, and optical/reference questions are packaged for external review with local formulas and no-auth boundaries. | `tests/test_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py` |
| Gate26 Package C external-review integration | User-pasted external-AI feedback is captured as a SHA-locked source artifact; `READY_FOR_IMPLEMENTATION_DESIGN_ONLY` is integrated as design constraints only, with Skorokhod Brownian target, required tests/schema fields, blocked model ledgers, and no-auth firewall preserved. | `tests/test_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py` |
| Gate27 Package C implementation-design preflight | Gate26 constraints are converted into future implementation backlog, proof-artifact contract, fail-closed matrix, validation plan, and no-auth firewall; no Package C proof is registered and `package_C_validation_status=pass` remains blocked. | `tests/test_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py` |
| Package C Skorokhod implementation candidate | After explicit user authorization for implementation code and unit tests, trapezoid diffusive plug-flow trajectories use `trapezoid_skorokhod_normal_reflection_euler_active_set_v1`; geometry exposes wall constraints and inward normals; validators require `finite_step_reflection_surrogate_not_hindered_hydrodynamics_not_package_c_proof_registered`. | `test_single_wall_reflection_matches_folded_normal_limit`, `test_reflected_trajectory_has_no_boundary_atom_after_sidewall_crossing`, `test_corner_active_set_reflection_converges_inside_support`, `test_pure_brownian_step_preserves_accessible_area_equilibrium_moments`, `test_dt_halving_converges_wall_distance_distribution`, `test_rectangle_limit_matches_rectangular_reflection`, `test_position_response_sidewall_v2_accepts_skorokhod_boundary_with_no_proof_claim` |
| Package C reflection telemetry | The geometry primitive can return active wall ids, reflection iteration count, total reflection displacement, and convergence status for one finite-step reflection update while preserving the tuple-return runtime API. Audit-only trajectory diagnostics now expose the Brownian target model, numerical scheme, no-specular/no-hindered guards, projection-surrogate flag, reflection update rule id, and telemetry reporting scope. | `test_reflection_diagnostics_noop_for_inside_trial_point`, `test_single_wall_reflection_matches_folded_normal_limit`, `test_corner_active_set_reflection_converges_inside_support`, `test_trapezoid_trajectory_diagnostics_mark_skorokhod_boundary` |
| Package C angle/depth mutation coverage | Reflected wall-distance distributions now change under sidewall-angle and depth mutations, and observation signatures include Brownian target/scheme/telemetry fields so cache keys cannot ignore the boundary implementation contract. | `test_angle_and_depth_mutation_change_reflected_wall_distance_distribution`, `test_sidewall_observation_signature_records_geometry_propagation_fields` |
| Package C equilibrium bin smoke | Pure-Brownian sidewall trajectories now check `x_local_norm` uniformity within u-slices using a KS-style empirical CDF bound plus left/right mean symmetry. | `test_pure_brownian_x_local_norm_uniformity_by_u_slice` |
| Package C proof scaffold | Package C proof/pass remains fail-closed, but any future `package_C_validation_status=pass` row must now carry a 28-field proof manifest scaffold: reviewed evidence hashes, implementation commit, external review status, required-test matrix status, explicit authorization id/hash superseding the no-auth ledger, and no-claim flags for hindered diffusion, flow, electrokinetic, optical, wet, PRS/EAS numeric, route/yield/detection claims. | `test_sidewall_package_c_proof_scaffold_requires_evidence_fields`, `test_sidewall_package_c_proof_scaffold_rejects_bad_evidence_hash`, `test_sidewall_package_c_proof_scaffold_rejects_bad_authorization_hash`, `test_sidewall_package_c_proof_scaffold_requires_no_claim_flags`, `test_gate27_proof_artifact_contract_requires_real_future_evidence` |
| Gate28 Package C proof-review packet | The current Package C implementation candidate is packaged for external/independent review with source locks, 6 passing no-runtime evidence commands, a self-contained external-AI prompt, and a no-proof firewall; Gate28 CSV/JSON evidence files are explicitly GitHub-visible, the prompt lists the Gate27 proof contract and all 28 required fields, and proof registration, runtime, numeric PRS/EAS, COMSOL launch, and `.mph` load remain false. | `tests/test_nodi_comsol_gate28_sidewall_package_c_proof_review_packet.py`; `NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_20260630.json` |

## Still Blocked

The following remain blocked and must not be inferred from current sidewall-aware rows:

- validated sloped-wall specular reflection or Package C proof/pass for Skorokhod reflected Brownian implementation;
- validated hindered diffusion under trapezoid Brownian trajectories;
- trapezoid Poiseuille or flux-weighted trapezoid flow model;
- trapezoid electrokinetic wall-distance grid;
- optical/reference-field solver output;
- wet pass probability, adhesion probability, clogging rate, time-to-clog, recovery, yield, detection probability;
- route winner, route rank, `route_score`, `JRC`, `chi_selected`, or `q_ch` weighting;
- production/runtime ingestion or fabrication release.

## Verification

Latest clean-tree sidewall mainline regression commands:

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
481 passed in 200.25s (0:03:20)

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "sidewall or production_candidate_validator"
312 passed, 169 deselected in 33.40s

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "sidewall or production_candidate_validator"
314 passed, 169 deselected in 27.57s

python -m pytest tests/test_cross_section_geometry.py tests/test_physics_core.py -q -k "ideal_rectangle or sidewall or trapezoid"
35 passed, 389 deselected in 0.25s

python -m pytest tests/test_nodi_comsol_gate23_sidewall_static_fixture_execution.py -q
7 passed in 6.19s

python -m pytest tests/test_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py -q
7 passed in 6.55s

python -m pytest tests/test_nodi_comsol_gate23_sidewall_static_fixture_execution.py tests/test_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py -q
14 passed in 10.69s

python -m pytest tests/test_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py -q
7 passed in 6.53s

python -m pytest tests/test_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py tests/test_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py -q
14 passed in 14.82s

python -m pytest tests/test_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py -q
11 passed in 31.29s

python -m pytest tests/test_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py tests/test_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py -q
18 passed in 14.11s

python -m pytest tests/test_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py -q
8 passed in 8.14s

python -m pytest tests/test_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py tests/test_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py -q
19 passed in 15.39s

python -m pytest tests/test_cross_section_geometry.py -q -k "trapezoid or sidewall or skorokhod or reflection or rectangle_limit or corner_active"
33 passed, 11 deselected in 0.85s

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "sidewall_v2 and (boundary or trajectory_guard or propagated_boundary or proof)"
5 passed, 478 deselected in 0.95s

python -m pytest tests/test_trajectory.py -q
4 passed in 2.28s

python -m pytest tests/test_cross_section_geometry.py tests/test_physics_core.py -q -k "ideal_rectangle or sidewall or trapezoid or trajectory_boundary"
37 passed, 392 deselected in 0.35s

python -m pytest tests/test_cross_section_geometry.py tests/test_trajectory.py -q
48 passed in 0.83s

python -m pytest tests/test_cross_section_geometry.py -q -k "pure_brownian_step or dt_halving"
2 passed, 44 deselected in 0.64s

python -m pytest tests/test_cross_section_geometry.py tests/test_trajectory.py -q
50 passed in 0.96s

python -m pytest tests/test_cross_section_geometry.py -q -k "reflection_diagnostics or single_wall_reflection or corner_active"
3 passed, 44 deselected in 0.58s

python -m py_compile nodi_simulator/cross_section_geometry.py
pass

python -m pytest tests/test_cross_section_geometry.py tests/test_trajectory.py -q
51 passed in 0.79s

python -m pytest tests/test_cross_section_geometry.py -q -k "trajectory_diagnostics"
3 passed, 44 deselected in 0.49s

python -m py_compile nodi_simulator/trajectory.py
pass

python -m pytest tests/test_cross_section_geometry.py tests/test_trajectory.py -q
51 passed in 4.60s

python -m pytest tests/test_physics_core.py::TestIntegration::test_claim_state_machine_smoke_matrix_exports_route_and_boundaries -q
1 passed in 0.20s

python -m py_compile nodi_simulator/parameter_sweep.py nodi_simulator/trajectory.py
pass

python -m pytest tests/test_cross_section_geometry.py -q -k "angle_and_depth_mutation or observation_signature_records"
2 passed, 46 deselected in 0.68s

python -m pytest tests/test_cross_section_geometry.py tests/test_trajectory.py -q
52 passed in 1.48s

python -m pytest tests/test_cross_section_geometry.py -q -k "x_local_norm_uniformity"
1 passed, 48 deselected in 0.60s

python -m pytest tests/test_cross_section_geometry.py tests/test_trajectory.py -q
53 passed in 1.32s

python -m pytest tests/test_cross_section_geometry.py -q -k "pure_brownian or x_local_norm_uniformity or dt_halving"
3 passed, 46 deselected in 0.54s

python -m pytest tests/test_physics_core.py::TestIntegration::test_claim_state_machine_smoke_matrix_exports_route_and_boundaries -q
1 passed in 0.37s

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "sidewall or production_candidate_validator"
314 passed, 169 deselected in 29.14s

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "sidewall or production_candidate_validator"
314 passed, 169 deselected in 24.11s

python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py
pass

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "package_c_proof_scaffold or package_d_precheck_blocks_near_wall or bad_package_c_proof"
12 passed, 479 deselected in 9.25s

python -m pytest tests/test_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py -q
8 passed in 6.66s

python tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py --confirm-gate27-package-c-implementation-design-preflight
NODI_GATE27_SIDEWALL_PACKAGE_C_IMPLEMENTATION_DESIGN_PREFLIGHT_READY_NO_AUTH
proof_contract_rows=28

python -m py_compile nodi_simulator/cross_section_geometry.py nodi_simulator/trajectory.py nodi_simulator/nodi_comsol_next_artifacts.py
pass

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "sidewall or production_candidate_validator"
322 passed, 169 deselected in 24.54s

python -m pytest tests/test_cross_section_geometry.py tests/test_trajectory.py -q
53 passed in 0.94s

python tools/audits/build_nodi_comsol_gate28_sidewall_package_c_proof_review_packet.py --confirm-gate28-package-c-proof-review-packet
NODI_GATE28_SIDEWALL_PACKAGE_C_PROOF_REVIEW_PACKET_READY_NO_PROOF_REGISTRATION
evidence_pass_rows=6
source_missing_rows=0
gate27_proof_contract_field_rows=28
gate27_proof_contract_missing_required_fields=[]
gate27_proof_contract_extra_fields=[]
proof_registration_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

Additional CLI/compile verification:

```text
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/validate_nodi_position_response_surface.py tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py tools/audits/validate_nodi_sidewall_package_d_precheck.py tools/audits/build_nodi_comsol_gate23_sidewall_static_fixture_execution.py tools/audits/write_nodi_sidewall_package_c_authorization_gate.py tools/audits/build_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py tools/audits/build_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py tools/audits/build_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py
python tools/audits/build_nodi_comsol_gate23_sidewall_static_fixture_execution.py --confirm-gate23-static-fixture-execution
NODI_GATE23_SIDEWALL_STATIC_FIXTURE_EXECUTION_READY_NO_AUTH
python tools/audits/build_nodi_comsol_gate24_sidewall_package_c_authorization_ledger.py --confirm-gate24-package-c-authorization-ledger
NODI_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_READY_NO_AUTH
python tools/audits/build_nodi_comsol_gate25_sidewall_package_c_design_review_packet.py --confirm-gate25-package-c-design-review
NODI_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_PACKET_READY_NO_AUTH
python tools/audits/build_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py --confirm-gate26-package-c-external-review-integration
NODI_GATE26_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_INTEGRATION_DESIGN_CONSTRAINTS_READY_NO_AUTH
python tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py --confirm-gate27-package-c-implementation-design-preflight
NODI_GATE27_SIDEWALL_PACKAGE_C_IMPLEMENTATION_DESIGN_PREFLIGHT_READY_NO_AUTH
```

## Current Go/No-Go

| Package | Status | Note |
| --- | --- | --- |
| Package A | pass for schema/descriptor/validator guard scope | No PRS/EAS data generation authorized by this packet. |
| Package B | pass for geometry primitive, sampler support, and actual signature binding | Flux-weighted trapezoid sampling remains blocked. |
| Package C | implementation candidate present; proof registration/pass still blocked/fail-closed | The Skorokhod finite-step reflection candidate is implemented for trapezoid diffusive plug-flow trajectories with unit tests and validator guards. No Package C physics authorization proof is registered; validated reflection proof/pass, hindered diffusion, runtime metrics beyond this candidate, and numeric PRS/EAS remain blocked. |
| Package D | validator/preflight guard pass only | Sidewall PRS/EAS pilot generation remains no-claim and blocked for trajectory/near-wall/wall-distance metrics unless a future Package C gate passes. |

## Next Safe Actions

1. Keep strengthening no-compute validators and mutation tests for profile/source-hash drift and geometry-source promotion.
2. If a real measured-profile loader is added later, add implementation-level loader/hash/profile-schema tests before any `measured_geometry` runtime use.
3. Submit the Gate28 proof-review packet to external/independent review and use the feedback to decide whether more Package C tests/schema guards are needed. Do not register proof or mark Package C as passed until that review is complete and an explicit future authorization path supersedes the current no-auth ledger.
