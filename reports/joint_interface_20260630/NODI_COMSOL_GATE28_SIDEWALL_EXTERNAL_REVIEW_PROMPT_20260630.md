# Gate28 External AI Review Prompt: NODI Package C Sidewall Reflection Proof Evidence

You are reviewing a GitHub-visible NODI sidewall-angle implementation candidate.
You cannot see local files unless they are committed to GitHub, so this prompt is
self-contained and names the exact committed files/artifacts to inspect.

## Verdict requested

Return one of:
- `READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY`
- `NEEDS_MORE_TEST_EVIDENCE_BEFORE_PROOF_REGISTRATION`
- `BLOCKED_PHYSICS_OR_CLAIM_BOUNDARY_UNSAFE`

Do not recommend NODI runtime recomputation, COMSOL launch, `.mph` load, PRS/EAS
numeric output, route_score/winner/JRC/q_ch weighting, yield, detection probability,
wet-pass probability, clogging rate, time-to-clog, recovery, fabrication release,
or production ingestion.

## Current Gate28 status

- Disposition: `NODI_GATE28_SIDEWALL_PACKAGE_C_PROOF_REVIEW_PACKET_READY_NO_PROOF_REGISTRATION`.
- Build commit recorded by packet: `48de7c4063a68d47316e8463d0dac84c2e7a21f7`.
- Gate27 disposition: `NODI_GATE27_SIDEWALL_PACKAGE_C_IMPLEMENTATION_DESIGN_PREFLIGHT_READY_NO_AUTH`.
- Gate27 proof contract rows: `52`.
- Gate27 proof registry/update rows: `0` / `0`.
- Evidence commands passed: `6` of `6`.
- Test evidence JSON sha256: `d118d10838553735ee37391196c14bb83f99bb7ce53972b9bb6a279216652641`.
- Source lock CSV sha256: `0c884ffa772bc6d5099bdaa4580dbe1cc37d496fe355367e087e52563ceb8d77`.
- Proof registration authorized: `False`.
- Runtime / numeric PRS-EAS / COMSOL / `.mph`: `False` / `False` / `False` / `False`.

## Implementation target and claim boundary

Package C targets Brownian reflected diffusion in a symmetric convex trapezoid
particle-center support domain, not hydrodynamic hindered diffusion or wet
clogging/adhesion physics.

Target model:

```text
brownian_boundary_target_model =
  skorokhod_normal_reflection_convex_offset_trapezoid_v1
```

Particle center domain:

```text
D_a = { g_i(x,u) >= 0 for all walls }
g_i = d_i(x,u) - a
```

Inward unit normals used by the design:

```text
top:    g_top = u - a
        n_top = (0, +1)

bottom: g_bottom = H - a - u
        n_bottom = (0, -1)

left:   g_left = (x + h(u))/sqrt(1+k^2) - a
        n_left = (1, -k)/sqrt(1+k^2)

right:  g_right = (h(u) - x)/sqrt(1+k^2) - a
        n_right = (-1, -k)/sqrt(1+k^2)
```

Current implementation candidate name:

```text
trapezoid_skorokhod_normal_reflection_euler_active_set_v1
```

Current claim level:

```text
finite_step_reflection_surrogate_not_hindered_hydrodynamics_not_package_c_proof_registered
```

This packet still does not register Package C proof/pass. It only packages
review evidence for an external or independent reviewer.

## Files to inspect on GitHub

- `nodi_simulator/cross_section_geometry.py`
- `nodi_simulator/trajectory.py`
- `nodi_simulator/nodi_comsol_next_artifacts.py`
- `tests/test_cross_section_geometry.py`
- `tests/test_trajectory.py`
- `tests/test_nodi_comsol_next_artifacts_contracts.py`
- `reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_20260630.json`
- `reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_SOURCE_LOCK_20260630.csv`
- `reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv`
- `reports/joint_interface_20260630/NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv`

## Gate27 required-field proof scaffold to review

The Gate27 proof contract currently contains exactly
52 required fields. Every field below
must be present before any separate future gate can even consider
`package_C_validation_status=pass`:

- `angle_depth_mutation_evidence_sha256`
- `authorization_supersedes_no_auth_ledger_id`
- `authorization_supersedes_no_auth_ledger_sha256`
- `boundary_atom_threshold`
- `corner_active_set_evidence_sha256`
- `corner_bias_test_threshold`
- `dependency_lock_sha256`
- `depth_grid_nm`
- `diffusion_coefficient_grid_m2_s`
- `dt_convergence_evidence_sha256`
- `dt_grid_s`
- `equilibrium_test_method`
- `equilibrium_test_threshold`
- `equilibrium_uniformity_evidence_sha256`
- `external_review_artifact_sha256`
- `implementation_commit_sha`
- `independent_reviewer_id_or_artifact_sha256`
- `max_reflection_iterations`
- `no_boundary_atom_evidence_sha256`
- `one_wall_limit_tolerance`
- `package_C_proof_artifact_id`
- `package_C_proof_artifact_scope`
- `package_C_proof_artifact_sha256`
- `package_C_proof_artifact_status`
- `package_C_proof_authorization_status`
- `package_C_proof_claim_boundary`
- `package_C_proof_evidence_claim_level`
- `package_C_proof_external_review_status`
- `package_C_proof_manifest_schema_version`
- `package_C_proof_no_electrokinetic_solver_claim`
- `package_C_proof_no_hindered_diffusion_claim`
- `package_C_proof_no_optical_solver_claim`
- `package_C_proof_no_prs_eas_numeric_output`
- `package_C_proof_no_route_yield_detection_claim`
- `package_C_proof_no_trapezoid_flow_solver_claim`
- `package_C_proof_no_wet_claim`
- `package_C_proof_required_test_matrix_status`
- `particle_radius_grid_nm`
- `raw_metric_artifact_sha256`
- `rectangle_limit_evidence_sha256`
- `rectangle_limit_tolerance`
- `reflection_algorithm_source_sha256`
- `reflection_metric_schema_version`
- `reflection_test_script_sha256`
- `required_test_result_artifact_sha256`
- `rng_seed_matrix_sha256`
- `sidewall_angle_grid_deg_comsol`
- `substep_policy`
- `summary_metric_artifact_sha256`
- `test_environment_lock_sha256`
- `test_parameter_matrix_sha256`
- `tolerance_m`

## Review questions

1. Does the finite-step active-set normal reflection candidate remain correctly
   labeled as a Brownian reflecting-boundary surrogate, not ballistic specular
   reflection and not hydrodynamic hindered diffusion?
2. Are the current tests sufficient as proof-registration evidence for the
   implemented claim level, especially support invariance, no boundary atom,
   corner active-set convergence, accessible-area equilibrium moments,
   u-slice local-width uniformity/symmetry, dt-halving one-wall convergence,
   angle/depth mutation, and rectangle limit?
3. Are the 28 proof scaffold fields sufficient before any future
   `package_C_validation_status=pass` row is allowed?
4. Are any claims still over-promoted, especially hindered diffusion,
   trapezoid flow solver, electrokinetic solver, optical/reference solver,
   PRS/EAS numeric output, route/yield/detection, wet pass, clogging, or
   production/fabrication release?
5. What exact additional tests or schema fields would you require before a
   separate future authorization could register a Package C proof artifact?
