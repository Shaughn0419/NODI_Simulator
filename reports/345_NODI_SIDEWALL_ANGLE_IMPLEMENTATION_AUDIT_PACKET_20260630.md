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
| Package C Skorokhod implementation candidate | After explicit user authorization for implementation code and unit tests, trapezoid diffusive plug-flow trajectories use `trapezoid_skorokhod_normal_reflection_euler_active_set_v1`; geometry exposes wall constraints and inward normals; validators accept the post-registration guard `finite_step_reflection_surrogate_package_c_proof_registered_not_validated_brownian_solver_output_not_hindered_hydrodynamics` while still accepting legacy no-proof rows. | `test_single_wall_reflection_matches_folded_normal_limit`, `test_reflected_trajectory_has_no_boundary_atom_after_sidewall_crossing`, `test_corner_active_set_reflection_converges_inside_support`, `test_pure_brownian_step_preserves_accessible_area_equilibrium_moments`, `test_dt_halving_converges_wall_distance_distribution`, `test_rectangle_limit_matches_rectangular_reflection`, `test_position_response_sidewall_v2_accepts_skorokhod_boundary_with_registered_proof_guard` |
| Package C reflection telemetry | The geometry primitive can return active wall ids, reflection iteration count, total reflection displacement, and convergence status for one finite-step reflection update while preserving the tuple-return runtime API. Audit-only trajectory diagnostics now expose the Brownian target model, numerical scheme, no-specular/no-hindered guards, projection-surrogate flag, reflection update rule id, and telemetry reporting scope. | `test_reflection_diagnostics_noop_for_inside_trial_point`, `test_single_wall_reflection_matches_folded_normal_limit`, `test_corner_active_set_reflection_converges_inside_support`, `test_trapezoid_trajectory_diagnostics_mark_skorokhod_boundary` |
| Package C angle/depth mutation coverage | Reflected wall-distance distributions now change under sidewall-angle and depth mutations, and observation signatures include Brownian target/scheme/telemetry fields so cache keys cannot ignore the boundary implementation contract. | `test_angle_and_depth_mutation_change_reflected_wall_distance_distribution`, `test_sidewall_observation_signature_records_geometry_propagation_fields` |
| Package C equilibrium bin smoke | Pure-Brownian sidewall trajectories now check `x_local_norm` uniformity within u-slices using a KS-style empirical CDF bound plus left/right mean symmetry. | `test_pure_brownian_x_local_norm_uniformity_by_u_slice` |
| Package C proof scaffold | Package C proof/pass remains fail-closed, but any future `package_C_validation_status=pass` row must now carry a 52-field proof scaffold: the prior identity/evidence/authorization/no-claim fields plus telemetry/reproducibility fields for source/test/environment/dependency/seed/parameter hashes, dt/angle/depth/radius grids, thresholds, raw metrics, summary metrics, and independent-review artifact binding. | `test_sidewall_package_c_proof_scaffold_requires_evidence_fields`, `test_sidewall_package_c_proof_scaffold_requires_telemetry_fields`, `test_sidewall_package_c_proof_scaffold_rejects_bad_telemetry_hash`, `test_gate27_proof_artifact_contract_requires_real_future_evidence` |
| Gate28 Package C proof-review packet | The current Package C implementation candidate is packaged for external/independent review with source locks, 6 passing no-runtime evidence commands, a self-contained external-AI prompt, and a no-proof firewall; Gate28 CSV/JSON evidence files are explicitly GitHub-visible, the prompt lists the Gate27 proof contract and all 52 required fields, and proof registration, runtime, numeric PRS/EAS, COMSOL launch, and `.mph` load remain false. | `tests/test_nodi_comsol_gate28_sidewall_package_c_proof_review_packet.py`; `NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_20260630.json` |
| Gate29 external proof-review integration | External verdict `READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY` is captured as review-only input and converted into 19 future hard gates plus 24 telemetry/reproducibility fields; Package C proof/pass registration remains unauthorized and blocked. | `tests/test_nodi_comsol_gate29_sidewall_package_c_external_proof_review_integration.py`; `NODI_COMSOL_GATE29_SIDEWALL_STATUS_20260630.json` |

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
proof_contract_rows=52

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
gate27_proof_contract_field_rows=52
gate27_proof_contract_missing_required_fields=[]
gate27_proof_contract_extra_fields=[]
proof_registration_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false

python tools/audits/build_nodi_comsol_gate29_sidewall_package_c_external_proof_review_integration.py --confirm-gate29-package-c-external-proof-review-integration
NODI_GATE29_SIDEWALL_PACKAGE_C_EXTERNAL_PROOF_REVIEW_INTEGRATION_READY_NO_PROOF_REGISTRATION
external_verdict=READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY
future_hard_gate_rows=19
telemetry_field_rows=24
gate27_proof_contract_field_rows=52
proof_registration_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false

python tools/audits/build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py --confirm-gate30-31-package-c-proof-metrics-candidate
NODI_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_READY_NO_PROOF_REGISTRATION
scenario_metric_rows=216
open_candidate_metric_rows=198
blocked_candidate_rows=18
dt_halving_rows=66
support_invariance_status=candidate_pass
boundary_atom_status=candidate_pass
equilibrium_uniformity_status=candidate_pass
dt_halving_status=candidate_pass
corner_active_set_status=candidate_pass
one_wall_limit_status=candidate_pass
rectangle_limit_status=candidate_pass
angle_depth_mutation_status=candidate_pass
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false

python tools/audits/build_nodi_comsol_gate32_sidewall_package_c_external_review_handoff.py --confirm-gate32-package-c-external-review-handoff
NODI_GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF_READY_NO_PROOF_REGISTRATION
gate30_31_metric_statuses_pass=true
github_path_map_rows=15
research_synthesis_question_rows=10
authorization_supersession_preflight_rows=21
source_missing_rows=0
external_review_received=false
authorization_supersedes_no_auth_ledger=false
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false

python -m pytest tests/test_nodi_comsol_gate33_36_sidewall_package_c_reflection_proof_authorization_design_packet.py -q
8 passed

python tools/audits/build_nodi_comsol_gate33_36_sidewall_package_c_reflection_proof_authorization_design_packet.py --confirm-gate33-36-package-c-proof-authorization-design
NODI_GATE33_36_SIDEWALL_PACKAGE_C_REFLECTION_PROOF_AUTHORIZATION_DESIGN_READY_NO_PROOF_REGISTRATION
external_verdict=READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY
packet_output_status=authorization_required_no_proof_registration
proof_hardening_backlog_rows=10
metric_expansion_spec_rows=8
threshold_matrix_rows=10
authorization_ledger_placeholder_rows=22
hard_fail_checklist_rows=14
evidence_chain_rows=9
review_request_rows=5
mutation_fail_count=0
self_review_fail_count=0
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false

python -m pytest tests/test_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate.py -q
8 passed

python tools/audits/build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate.py --confirm-gate37-package-c-metric-hardening-candidate
NODI_GATE37_SIDEWALL_PACKAGE_C_REFLECTION_METRIC_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION
boundary_atom_split_rows=198
histogram_rows=396
ess_proxy_rows=198
one_wall_suite_rows=18
worst_case_dt_refinement_rows=10
corner_heatmap_rows=40
max_exact_boundary_atom_fraction=0.0
max_near_boundary_band_fraction=0.002604167
max_wall_pileup_ratio=9.0
max_one_wall_positive_control_ks=0.019246436
projection_negative_control_status=expected_fail_observed
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false

python -m pytest tests/test_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate.py -q
6 passed

python tools/audits/build_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate.py --confirm-gate38-wall-pileup-refinement-candidate
NODI_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION
gate37_max_wall_pileup_ratio=9.0
refined_top_pileup_rows=12
expanded_sample_count=8192
algorithmic_pileup_signal_rows=0
sparse_gate37_proxy_artifact_rows=12
max_expanded_first_vs_adjacent_gap_band_smoothed_ratio=1.298850575
max_expanded_wall_pileup_ratio_ci95_low=1.011337147
max_expanded_wall_pileup_ratio_ci95_high=1.928677789
wall_pileup_refinement_status=sparse_gate37_proxy_artifact_no_algorithmic_pileup_signal
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
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
| Package C | implementation candidate plus Gate33-38 metric hardening route present; proof registration/pass still blocked/fail-closed | The Skorokhod finite-step reflection candidate is implemented for trapezoid diffusive plug-flow trajectories with unit tests and validator guards. Gate33-36 captures the external research synthesis, threshold matrix, hardening backlog, authorization placeholder, and hard-fail checklist. Gate37 adds exact/near-boundary atom split, raw histograms, ESS proxy, one-wall folded-normal and negative-control rows, worst-case dt refinement, and corner heatmap. Gate38 resolves the Gate37 `max_wall_pileup_ratio=9.0` warning as sparse proxy artifact under expanded sampling. No Package C physics authorization proof is registered; validated reflection proof/pass, hindered diffusion, runtime metrics beyond this candidate, and numeric PRS/EAS remain blocked. |
| Package D | validator/preflight guard pass only | Sidewall PRS/EAS pilot generation remains no-claim and blocked for trajectory/near-wall/wall-distance metrics unless a future Package C gate passes. |

## Next Safe Actions

1. Fold Gate38 into the next metric-hardening candidate by replacing the brittle Gate37 wall-pileup ratio with expanded-sampling band counts, confidence intervals, and sparse-proxy classification.
2. Continue tightening remaining proof-level gaps: long-run ESS if timeseries equilibrium tests are introduced, additional `6.25e-6 s` dt refinement for worst cases if needed, and explicit substep/fail policy for large RMS step relative to local feature size.
3. Regenerate Gate33-38 evidence and source locks after refinement, then require clean reviewed commit binding before any future authorization packet can claim proof readiness.
4. Keep the manual authorization ledger and external-review artifact SHA as explicit placeholders until a separate authorization supersedes the no-auth ledger.
5. If a real measured-profile loader is added later, add implementation-level loader/hash/profile-schema tests before any `measured_geometry` runtime use.
6. Do not register proof or mark Package C as passed in the current gate.

## Consolidated Package C metric-hardening entrypoint

After Gate38, the Package C proof-metric hardening work is consolidated into one larger evidence block rather than continuing as many small gate turns:

```text
python tools/audits/build_nodi_comsol_package_c_metric_hardening_consolidation.py --confirm-package-c-metric-hardening-consolidation
NODI_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_CANDIDATE_READY_NO_PROOF_REGISTRATION
evidence_index_rows=10
readiness_criteria_rows=9
boundary_atom_split_rows=198
raw_histogram_rows=396
ess_proxy_rows=198
one_wall_suite_rows=18
worst_case_dt_refinement_rows=10
corner_heatmap_rows=40
wall_pileup_refinement_rows=12
algorithmic_pileup_signal_rows=0
proof_readiness_status=not_ready_missing_timeseries_ess_clean_commit_and_authorization
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

This consolidation is the current forward entrypoint for Package C metric hardening. It absorbs Gate37 exact/near-boundary atom split, raw histograms, ESS proxy, one-wall positive/negative controls, dt refinement, corner heatmap, and Gate38 expanded-sampling wall-pileup refinement into a single evidence index and readiness-criteria table. It does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C timeseries ESS candidate

The first post-consolidation proof-gap hardening block reduces the prior `timeseries_ess` gap from missing to candidate-evidenced:

```text
python tools/audits/build_nodi_comsol_package_c_timeseries_ess_candidate.py --confirm-package-c-timeseries-ess-candidate
NODI_PACKAGE_C_TIMESERIES_ESS_CANDIDATE_READY_NO_PROOF_REGISTRATION
scenario_rows=6
observable_ess_rows=18
autocorrelation_rows=144
substep_policy_rows=6
n_steps_per_scenario=65536
burn_in_steps=8192
sample_stride=8
retained_samples_per_scenario=7168
min_effective_sample_size=46.559312675
max_u_accessible_cdf_l1_to_uniform=0.284598214
max_x_local_norm_l1_to_uniform=0.108537946
support_violation_rows=0
nonconverged_reflection_rows=0
max_exact_boundary_atom_fraction_all_steps=0.0
substep_review_rows=6
timeseries_ess_candidate_status=candidate_artifact_complete_not_proof
stationarity_review_required=true
substep_policy_review_required=true
reviewed_commit_binding_status=pending_future_authorization_not_clean_head_bound
proof_readiness_impact=timeseries_ess_gap_reduced_but_not_proof_registered
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

The substep rows are design guards only, not runtime policy. This packet does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C substep/fail policy hardening

The next post-consolidation hardening block converts the timeseries substep review rows into explicit future proof/pass validator requirements:

```text
python tools/audits/build_nodi_comsol_package_c_substep_fail_policy_hardening.py --confirm-package-c-substep-fail-policy-hardening
NODI_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION
policy_rows=6
triggered_policy_rows=6
substep_trigger_metric=brownian_rms_step_over_surface_gap_p05
substep_trigger_threshold=1.0
substep_max_observed_trigger_value=22.925543703
substep_triggered_scenario_count=6
substep_policy_bound_trigger_count=6
substep_policy_scope=proof_guard_only_not_runtime_config
proof_field_requirement_rows=10
validator_hardening_status=package_c_proof_pass_requires_substep_policy_fields
proof_readiness_impact=future_package_c_proof_pass_hard_fails_without_substep_policy_evidence
github_visibility_status=local_worktree_pre_commit_urls_valid_after_publish
substep_review_required_for_current_candidate=true
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

The contract validator now rejects future `package_C_validation_status=pass` rows unless substep policy evidence, status, scope, trigger metric, threshold, max observed trigger value, triggered scenario count, bound trigger count, closed review status, and false runtime authorization are all present and consistent. This packet does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C substep dt-refinement requirements

The follow-on sizing block converts the six substep-triggered scenarios into explicit substep/dt reduction requirements:

```text
python tools/audits/build_nodi_comsol_package_c_substep_dt_refinement_requirements.py --confirm-package-c-substep-dt-refinement-requirements
NODI_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_CANDIDATE_READY_NO_PROOF_REGISTRATION
refinement_rows=6
substep_trigger_metric=brownian_rms_step_over_surface_gap_p05
substep_trigger_threshold=1.0
current_dt_s=2.5e-05
min_required_substeps_to_meet_threshold=4
max_required_substeps_to_meet_threshold=526
min_required_dt_s_to_meet_threshold=4.75285171103e-08
max_projected_trigger_value_after_required_substeps=0.999601207629
dt_refinement_candidate_status=requirements_complete_not_runtime_policy_not_proof
proof_readiness_impact=substep_review_rows_now_have_explicit_dt_refinement_requirements
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

This packet is a policy-sizing artifact, not a runtime policy. It does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C proof-threshold table

The next consolidation block makes candidate/proof thresholds and remaining proof gaps machine-readable:

```text
python tools/audits/build_nodi_comsol_package_c_proof_threshold_table.py --confirm-package-c-proof-threshold-table
NODI_PACKAGE_C_PROOF_THRESHOLD_TABLE_CANDIDATE_READY_NO_PROOF_REGISTRATION
threshold_rows=13
candidate_pass_rows=8
proof_gap_rows=5
runtime_policy_gap_rows=2
threshold_table_status=candidate_threshold_table_ready_not_proof_registered
proof_readiness_impact=proof_gaps_are_explicit_and_machine_readable
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

This packet is threshold planning evidence only. It does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C proof-readiness index

The current preferred entrypoint consolidates Package C metric-hardening state, blockers, and external-research questions:

```text
python tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py --confirm-package-c-proof-readiness-index
NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION
readiness_index_rows=5
open_blocker_rows=5
external_research_question_rows=4
proof_readiness_index_status=single_entrypoint_ready_not_proof_registered
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

This packet is readiness/context evidence only. It does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C external-research prompt

The next handoff block converts the readiness index into a copyable external-AI prompt for broad method/literature synthesis:

```text
python tools/audits/build_nodi_comsol_package_c_external_research_prompt.py --confirm-package-c-external-research-prompt
NODI_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_READY_NO_PROOF_REGISTRATION
context_rows=5
research_question_rows=4
blocker_rows=5
prompt_status=copyable_external_research_prompt_ready
github_visibility_status=local_worktree_pre_commit_urls_valid_after_publish
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

This packet is a research handoff only. It tells external AI to inspect GitHub-visible files, not local Codex files, and to answer the four research questions with sources, thresholds, and next evidence priorities. It does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C stationarity ensemble refinement

The next proof-gap reduction block adds independent-ensemble transition-invariance evidence:

```text
python tools/audits/build_nodi_comsol_package_c_stationarity_ensemble_refinement.py --confirm-package-c-stationarity-ensemble-refinement
NODI_PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION
scenario_seed_rows=18
total_independent_samples=589824
min_independent_ensemble_ess=32768.0
max_final_u_accessible_cdf_l1_to_uniform=0.0217651367188
max_final_x_local_norm_l1_to_uniform=0.0203979492187
max_ci95_upper_l1=0.0219939450399
support_violation_count=0
exact_boundary_atom_count=0
nonconverged_reflection_count=0
stationarity_ensemble_status=candidate_numeric_stationarity_lines_met_not_proof_registered
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

The refreshed threshold/readiness chain absorbs this evidence:

```text
python tools/audits/build_nodi_comsol_package_c_proof_threshold_table.py --confirm-package-c-proof-threshold-table
NODI_PACKAGE_C_PROOF_THRESHOLD_TABLE_CANDIDATE_READY_NO_PROOF_REGISTRATION
threshold_rows=13
proof_gap_rows=2
proof_threshold_met_not_registered_rows=7
runtime_policy_gap_rows=2

python tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py --confirm-package-c-proof-readiness-index
NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION
readiness_index_rows=6
open_blocker_rows=5
external_research_question_rows=4
```

This packet reduces the stationarity/ESS and u/x-local uniformity gap, but it does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C one-wall and wall-pileup refinement

The next proof-threshold reduction block expands the one-wall folded-normal and wall-pileup diagnostics:

```text
python tools/audits/build_nodi_comsol_package_c_one_wall_wall_pileup_refinement.py --confirm-package-c-one-wall-wall-pileup-refinement
NODI_PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION
one_wall_rows=6
wall_pileup_rows=12
one_wall_sample_count=65536
wall_pileup_sample_count=65536
max_one_wall_positive_control_ks=0.005281493
max_wall_pileup_ratio=1.072659525
max_wall_pileup_ratio_ci95_high=1.214998175
one_wall_wall_pileup_status=candidate_numeric_thresholds_met_not_proof_registered
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

The refreshed threshold/readiness chain now treats one-wall and wall-pileup numeric proof-threshold gaps as reduced, while leaving proof registration blocked:

```text
python tools/audits/build_nodi_comsol_package_c_proof_threshold_table.py --confirm-package-c-proof-threshold-table
NODI_PACKAGE_C_PROOF_THRESHOLD_TABLE_CANDIDATE_READY_NO_PROOF_REGISTRATION
threshold_rows=13
proof_gap_rows=0
proof_method_gap_rows=1
proof_threshold_met_not_registered_rows=9
runtime_policy_gap_rows=2
proof_readiness_impact=numeric_proof_threshold_gaps_reduced_to_method_authorization_and_runtime_policy_gaps

python tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py --confirm-package-c-proof-readiness-index
NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION
readiness_index_rows=7
open_blocker_rows=5
external_research_question_rows=4
```

This packet closes the remaining one-wall/wall-pileup numeric threshold gaps in candidate evidence only. It does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims. The remaining blockers are near-boundary expected-band method binding, clean reviewed commit/manual authorization, runtime/substep policy review, and separate solver/wet evidence branches.

## Package C near-boundary expected-band method

The next method-binding block converts the sparse near-boundary band fraction into an analytic area-expectation check:

```text
python tools/audits/build_nodi_comsol_package_c_near_boundary_expected_band_method.py --confirm-package-c-near-boundary-expected-band-method
NODI_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_CANDIDATE_READY_NO_PROOF_REGISTRATION
expected_band_rows=24
legacy_sparse_context_rows=1
max_abs_z_to_expected=2.049081656
max_observed_first_band_fraction=0.017562866211
max_expected_first_band_fraction=0.016840432432
near_boundary_expected_band_method_status=candidate_method_bound_not_proof_registered
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

The refreshed threshold/readiness chain now treats the near-boundary method gap as bound candidate evidence, while leaving proof registration blocked:

```text
python tools/audits/build_nodi_comsol_package_c_proof_threshold_table.py --confirm-package-c-proof-threshold-table
NODI_PACKAGE_C_PROOF_THRESHOLD_TABLE_CANDIDATE_READY_NO_PROOF_REGISTRATION
threshold_rows=14
proof_gap_rows=0
proof_method_gap_rows=0
proof_method_bound_not_registered_rows=1
proof_threshold_met_not_registered_rows=9
runtime_policy_gap_rows=2
proof_readiness_impact=numeric_and_method_candidate_lines_bound_to_authorization_and_runtime_policy_gaps

python tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py --confirm-package-c-proof-readiness-index
NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION
readiness_index_rows=8
open_blocker_rows=4
external_research_question_rows=4
```

This packet binds the near-boundary expected-band method in candidate evidence only. It does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims. The remaining blockers are clean reviewed commit/manual authorization, runtime/substep policy review, and separate solver/wet evidence branches.

## Package C runtime/substep policy design

The next policy-design block converts the dt-refinement sizing rows into fail-closed runtime/substep authorization classes:

```text
python tools/audits/build_nodi_comsol_package_c_runtime_substep_policy_design.py --confirm-package-c-runtime-substep-policy-design
NODI_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_CANDIDATE_READY_NO_RUNTIME_AUTHORIZATION
policy_rows=6
field_requirement_rows=8
low_substep_cost_rows=4
moderate_substep_cost_rows=1
high_substep_cost_rows=0
prohibitive_substep_cost_rows=1
max_required_substeps_to_meet_threshold=526
runtime_substep_policy_design_status=policy_design_bound_not_runtime_authorized
runtime_policy_authorization_status=missing_not_authorized
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

The refreshed threshold/readiness/external prompt chain now includes the runtime/substep policy design:

```text
python tools/audits/build_nodi_comsol_package_c_proof_threshold_table.py --confirm-package-c-proof-threshold-table
NODI_PACKAGE_C_PROOF_THRESHOLD_TABLE_CANDIDATE_READY_NO_PROOF_REGISTRATION
threshold_rows=16
runtime_policy_gap_rows=4
proof_readiness_impact=numeric_method_and_runtime_policy_candidate_lines_bound_to_authorization_gaps

python tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py --confirm-package-c-proof-readiness-index
NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION
readiness_index_rows=9
open_blocker_rows=4
external_research_question_rows=4

python tools/audits/build_nodi_comsol_package_c_external_research_prompt.py --confirm-package-c-external-research-prompt
NODI_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_READY_NO_PROOF_REGISTRATION
context_rows=7
```

This packet makes the `526` substep worst case a machine-readable prohibitive-cost authorization issue, not a runtime setting. It does not register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C authorization preflight

The next authorization-design block binds the current GitHub-visible candidate commit and keeps the manual ledger empty/fail-closed:

```text
python tools/audits/build_nodi_comsol_package_c_authorization_preflight.py --confirm-package-c-authorization-preflight
NODI_PACKAGE_C_AUTHORIZATION_PREFLIGHT_CANDIDATE_READY_NO_AUTHORIZATION
target_reviewed_commit_sha=9586f8fc27d80d54b5887dc4ca59560476a86b97
origin_main_sha=9586f8fc27d80d54b5887dc4ca59560476a86b97
head_matches_origin_main=true
manual_authorization_ledger_status=missing_fail_closed
hard_fail_checklist_rows=9
proof_registration_authorized=false
package_c_validation_status_pass_authorized=false
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
```

The refreshed readiness/external prompt chain now includes the authorization preflight:

```text
python tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py --confirm-package-c-proof-readiness-index
NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION
readiness_index_rows=10
open_blocker_rows=4
external_research_question_rows=4

python tools/audits/build_nodi_comsol_package_c_external_research_prompt.py --confirm-package-c-external-research-prompt
NODI_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_READY_NO_PROOF_REGISTRATION
context_rows=8
```

This packet identifies a candidate reviewed commit and an empty manual-ledger placeholder only. It does not supersede the no-auth ledger, register proof, mark Package C as passed, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C user authorization ledger

The user then explicitly authorized the manual ledger, runtime/substep policy path, and solver/wet branch paths. The ledger records scope authorization without promoting results:

```text
python tools/audits/build_nodi_comsol_package_c_user_authorization_ledger.py --confirm-package-c-user-authorization-ledger
NODI_PACKAGE_C_USER_AUTHORIZATION_LEDGER_ACCEPTED_NO_RESULT_PROMOTION
authorized_scope_rows=4
package_c_proof_registration_path_authorized=true
runtime_substep_policy_authorized=true
solver_branch_authorized=true
wet_branch_authorized=true
package_c_proof_artifact_registered=false
package_c_validation_status_pass_current=false
runtime_execution_started=false
sidewall_prs_eas_numeric_output_current=false
comsol_launch_started=false
mph_load_started=false
```

The refreshed readiness/external prompt chain now includes the user authorization ledger:

```text
python tools/audits/build_nodi_comsol_package_c_proof_readiness_index.py --confirm-package-c-proof-readiness-index
NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION
readiness_index_rows=11
open_blocker_rows=4
external_research_question_rows=4

python tools/audits/build_nodi_comsol_package_c_external_research_prompt.py --confirm-package-c-external-research-prompt
NODI_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_READY_NO_PROOF_REGISTRATION
context_rows=9
```

This packet resolves the manual authorization blocker as an authorized path. It does not register proof, mark Package C as passed, start runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## Package C proof registration artifact

The proof-registration artifact now registers Package C finite-step reflection-surrogate evidence, while keeping runtime and downstream claims blocked:

```text
python tools/audits/build_nodi_comsol_package_c_proof_registration_artifact.py --confirm-package-c-proof-registration-artifact
NODI_PACKAGE_C_PROOF_REGISTRATION_ARTIFACT_REGISTERED_NO_RUNTIME
package_c_proof_artifact_registered=true
package_c_validation_status_pass_current=true
package_c_validation_status_pass_scope=finite_step_reflection_surrogate_evidence_only
proof_gap_rows=0
proof_method_gap_rows=0
runtime_policy_gap_rows=4
runtime_allowed=false
numeric_prs_eas_allowed=false
comsol_launch_allowed=false
mph_load_allowed=false
post_registration_guard_rows=14
source_lock_rows=26
```

This packet registers only finite-step reflection-surrogate proof evidence. It does not start runtime, emit sidewall PRS/EAS numeric output, launch COMSOL, load `.mph`, validate hindered diffusion, validate trapezoid flow/electrokinetic/optical solver output, claim true `W_eff`, or create route/yield/detection/wet/fabrication/production claims.

## Package C runtime/substep guard implementation

The runtime/substep path now has a code-level preflight guard in `nodi_simulator/runtime_substep_policy.py`:

```text
policy_version=trapezoid_runtime_substep_guard_v1
trigger_metric=brownian_rms_step_over_surface_gap_quantile
low_cost_max_substeps=16
review_max_substeps=128
sidewall_prs_eas_numeric_allowed=false
```

The guard reproduces the current stress-case sizing (`required_substeps=526`) as `blocked_prohibitive_substep_cost` without a separate execution packet/waiver. It is a runtime preflight guard only: it does not run NODI, emit sidewall PRS/EAS numeric output, launch COMSOL, load `.mph`, or create solver/wet/route/yield/detection claims.
