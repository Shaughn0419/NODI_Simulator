# Gate26 External AI Feedback Capture

Source visibility: user-pasted external AI feedback in the Codex thread, captured
as a Gate26 source artifact because the original external AI did not have local
file access.

Verdict:
- READY_FOR_IMPLEMENTATION_DESIGN_ONLY.
- This verdict is not implementation authorization.
- Package C remains design-review-only / no-auth.

Boundary:
- No NODI runtime recomputation.
- No COMSOL launch.
- No `.mph` load.
- No sidewall PRS/EAS numeric output.
- No proof-registry pass/update.
- No q_ch, JRC, route_score, route winner, yield, detection_probability,
  wet-pass probability, clogging rate, time-to-clog, recovery, fabrication
  release, or production ingestion.

Brownian trajectory requirements:
- Target model: `skorokhod_normal_reflection_convex_offset_trapezoid_v1`.
- Current model remains `trapezoid_center_support_projection_boundary_v1`.
- Current claim remains
  `sidewall_projection_boundary_surrogate_not_specular_reflection`.
- Projection/clamp must not be renamed as validated Brownian reflection,
  specular reflection, or Skorokhod-validated reflection.
- Particle-center support domain is represented by wall constraints
  `g_i(x,u) >= 0`; active wall local time/correction grows only at active walls.
- Single-wall crossing should use a folded-normal / wall-normal mirror update
  in design, not a projection-to-boundary spike.
- Corners require an active-set / normal-cone correction with iteration limits
  and hard fail or substepping if convergence fails.

Required Package C tests:
- `test_trapezoid_skorokhod_normals_match_wall_distance_gradients`
- `test_single_wall_reflection_matches_folded_normal_limit`
- `test_projection_boundary_has_no_validated_reflection_claim`
- `test_reflected_trajectory_all_points_inside_center_support`
- `test_reflected_trajectory_has_no_boundary_atom_spike`
- `test_pure_brownian_equilibrium_uniform_over_accessible_area`
- `test_x_local_norm_uniformity_by_u_slice`
- `test_left_right_symmetry_for_symmetric_trapezoid`
- `test_corner_active_set_no_corner_pileup`
- `test_dt_halving_converges_wall_distance_distribution`
- `test_theta_mutation_changes_boundary_event_counts_and_signature`
- `test_depth_mutation_changes_support_and_signature`
- `test_geometry_closed_blocks_trajectory_runtime`
- `test_near_closed_requires_resource_or_step_guard`
- `test_hindered_diffusion_blocked_under_trapezoid_unless_solver_or_surrogate_label`
- `test_parabolic_rect_and_rect_series_blocked_under_trapezoid`
- `test_fixed_pressure_trapezoid_requires_poisson_solver_or_context_only`
- `test_boltzmann_wall_exclusion_blocked_until_trapezoid_grid_exists`
- `test_reference_field_under_trapezoid_remains_proxy_not_solver`
- `test_no_forbidden_claim_columns_in_package_c_artifacts`

Required schema/design fields:
- `brownian_boundary_target_model`
- `brownian_boundary_numerical_scheme`
- `brownian_boundary_claim_level`
- `not_ballistic_specular_collision_claim`
- `projection_boundary_surrogate_used`
- `reflection_update_rule_id`
- `wall_constraint_formula_id`
- `active_wall_set`
- `active_wall_count`
- `corner_handling_model`
- `corner_guard_status`
- `normal_vector_x`
- `normal_vector_u`
- `reflection_displacement_nm`
- `brownian_rms_step_nm`
- `dt_s`
- `dt_stability_status`
- `dt_halving_convergence_status`
- `dt_halving_max_distribution_delta`
- `max_reflection_iterations`
- `reflection_iteration_count_p50`
- `reflection_iteration_count_p99`
- `corner_active_set_count`
- `boundary_atom_fraction`
- `wall_bias_check_status`
- `equilibrium_uniformity_check_status`
- `rectangle_limit_check_status`
- `one_wall_neumann_kernel_check_status`
- `diffusion_tensor_model`
- `diffusion_hindrance_model`
- `diffusion_hindrance_claim_level`
- `hindered_diffusion_solver_required_reason`
- `flow_control_interpretation`
- `trapezoid_flow_solver_status`
- `trapezoid_velocity_field_status`
- `fixed_pressure_hydraulic_resistance_status`
- `not_qch_weighted`
- `electrokinetic_grid_geometry_model`
- `electrokinetic_solver_status`
- `electrokinetic_claim_level`
- `optical_solver_status`
- `optical_solver_required_reason`
- `not_true_W_eff`
- `not_reference_strength_claim`
- `not_detector_response_claim`
- `not_sidewall_scattering_claim`

Model blockers:
- Trapezoid hindered diffusion remains blocked in v1 except a possible future
  nearest-wall single-plane surrogate with strict one-wall dominance and
  `surrogate_sensitivity_only` claim level.
- Package C v1 safest flow is fixed-velocity plug-flow audit only:
  `flow_profile_model=plug`, `flow_control_mode=fixed_velocity`,
  `not_qch_weighted=true`.
- Trapezoid fixed-pressure/Poiseuille flow requires a future cross-section
  Poisson/no-slip solver or validated lookup.
- Electrokinetic trapezoid claims require a profile-aware grid/solver.
- Optical/reference-field sidewall claims require an actual solver or validated
  lookup before true W_eff, reference strength, detector response, or sidewall
  scattering can be claimed.
