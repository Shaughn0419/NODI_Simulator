# External AI Research Prompt: NODI Package C Sidewall Reflection Proof Gaps

You can only inspect GitHub-visible files. Do not assume access to local Codex files, local COMSOL projects, local `.mph` files, local CSVs outside GitHub, or uncommitted artifacts. If a GitHub URL is not visible yet, treat it as a publish-timing limitation, not as evidence absence.

Primary GitHub-visible entrypoint after publish:
- Readiness status: https://github.com/Shaughn0419/NODI_Simulator/blob/main/reports/joint_interface_20260701/NODI_COMSOL_PACKAGE_C_PROOF_READINESS_STATUS_20260701.json
- Readiness index CSV: https://github.com/Shaughn0419/NODI_Simulator/blob/main/reports/joint_interface_20260701/NODI_COMSOL_PACKAGE_C_PROOF_READINESS_INDEX_20260701.csv
- Open blockers CSV: https://github.com/Shaughn0419/NODI_Simulator/blob/main/reports/joint_interface_20260701/NODI_COMSOL_PACKAGE_C_PROOF_READINESS_BLOCKERS_20260701.csv
- External research questions CSV: https://github.com/Shaughn0419/NODI_Simulator/blob/main/reports/joint_interface_20260701/NODI_COMSOL_PACKAGE_C_PROOF_READINESS_EXTERNAL_RESEARCH_QUESTIONS_20260701.csv
- Proof threshold table CSV: https://github.com/Shaughn0419/NODI_Simulator/blob/main/reports/joint_interface_20260701/NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv
- Roadmap: https://github.com/Shaughn0419/NODI_Simulator/blob/main/reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md
- Audit packet: https://github.com/Shaughn0419/NODI_Simulator/blob/main/reports/345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md

Current disposition:
- NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION
- artifact_id=PACKAGE_C_PROOF_READINESS_INDEX_20260701
- readiness_index_rows=7
- open_blocker_rows=5
- external_research_question_rows=4

Hard boundary:
- Do not register Package C proof/pass.
- Do not mark `package_C_validation_status=pass`.
- Do not authorize runtime configuration, NODI recomputation, COMSOL launch, `.mph` load, numeric PRS/EAS output, route_score, winner, JRC, q_ch weighting, yield, detection_probability, wet pass, clogging, time-to-clog, recovery, fabrication release, or production ingestion.
- Treat all current metrics as candidate/readiness evidence, not validated Brownian solver output, hindered hydrodynamics, trapezoid Poiseuille, electrokinetic solver, optical solver, wet behavior, or production evidence.

Open blockers:
- manual_authorization_ledger_missing: proof_registration_authorized remains false -> explicit manual authorization ledger that supersedes no-auth ledger
- clean_reviewed_commit_binding_pending: reviewed_commit_binding_status remains pending in candidate packets -> future proof/pass artifact must bind a reviewed clean commit and source lock
- proof_method_gaps_present: max_near_boundary_band_fraction -> bind proof-level statistical method, expected-band mass model, and uncertainty review
- runtime_policy_gaps_present: max_required_substeps_to_meet_threshold;max_projected_trigger_value_after_required_substeps -> manual runtime cost and substep policy review required before runtime use
- no_solver_or_wet_claim_authorized: hindered diffusion, flow, electrokinetic, optical, wet claims all remain blocked -> separate solver/experiment authorization required

Current threshold rows:
- support_violation_rows: observed=0; candidate=must_equal_0; proof=must_equal_0; status=candidate_and_proof_threshold_met_not_registered
- nonconverged_reflection_rows: observed=0; candidate=must_equal_0; proof=must_equal_0; status=candidate_and_proof_threshold_met_not_registered
- max_exact_boundary_atom_fraction: observed=0.0; candidate=<=0.005; proof=must_equal_0; status=candidate_and_proof_threshold_met_not_registered
- max_near_boundary_band_fraction: observed=0.002604167; candidate=<=0.005; proof=requires_area_expectation_plus_confidence_interval; status=candidate_pass_proof_method_gap
- max_one_wall_positive_control_ks: observed=0.005281493; candidate=<=0.02; proof=<=0.01; status=candidate_and_proof_threshold_met_not_registered
- projection_negative_control_status: observed=expected_fail_observed; candidate=expected_fail_observed; proof=expected_fail_observed; status=candidate_and_proof_threshold_met_not_registered
- max_expanded_wall_pileup_ratio: observed=1.072659525; candidate=<=1.5; proof=<=1.25; status=candidate_and_proof_threshold_met_not_registered
- min_effective_sample_size: observed=32768.0; candidate=>=20; proof=effective_sample_size>=5000_or_confidence_interval_justified; status=candidate_and_proof_threshold_met_not_registered
- max_u_accessible_cdf_l1_to_uniform: observed=0.0217651367188; candidate=<=0.30; proof=<=0.04_hard_target_<=0.03; status=candidate_and_proof_threshold_met_not_registered
- max_x_local_norm_l1_to_uniform: observed=0.0203979492187; candidate=<=0.30; proof=<=0.04_hard_target_<=0.03; status=candidate_and_proof_threshold_met_not_registered
- substep_policy_bound_trigger_count: observed=6; candidate=equals_triggered_scenario_count; proof=equals_triggered_scenario_count_and_policy_evidence_sha_bound; status=candidate_pass_proof_authorization_gap
- max_required_substeps_to_meet_threshold: observed=526; candidate=sized_and_reported; proof=manual_runtime_cost_review_or_smaller_dt_policy_required; status=candidate_sized_runtime_policy_gap
- max_projected_trigger_value_after_required_substeps: observed=0.999601207629; candidate=<=1.0; proof=<=1.0_with_validated_substep_tests; status=candidate_pass_proof_runtime_gap

Research questions to answer in one pass:
1. What proof-level stationarity and ESS method is appropriate for finite-step reflected Brownian motion in a convex offset trapezoid?
   Scope guard: Use stationarity ensemble and threshold rows for min ESS and u/x-local L1 gaps; do not infer proof/pass or runtime authorization.
2. How should near-boundary band mass be compared to accessible-area expectation with confidence intervals?
   Scope guard: Use exact atom split and raw histogram context; keep no wet/hindered hydrodynamic claim.
3. Are the expanded one-wall KS <=0.01 and wall-pileup ratio/CI <=1.25 candidate lines sufficient for future proof registration, and what raw evidence should be bound?
   Scope guard: Use the one-wall/wall-pileup refinement as candidate evidence only; no proof/pass or runtime claim, and avoid turning candidate metrics into validated solver output.
4. Given max_required_substeps=526, what substep or smaller-dt strategy is numerically defensible before runtime activation?
   Scope guard: Treat this as proof-policy design only; no NODI runtime, COMSOL, PRS/EAS numeric output, or production claim.

Requested output:
1. Give a concise verdict for each research question: recommended proof-level method/threshold, supporting references or reasoning, and whether current candidate evidence is sufficient, insufficient, or needs a different metric.
2. Identify the highest-leverage next local evidence block. Prefer one block that can move multiple proof gaps at once.
3. Keep claim boundaries explicit. If you suggest future runtime/substep policy, state exactly what remains required before runtime can be authorized.
4. Do not provide route, yield, detection, wet, fabrication, or production conclusions.
