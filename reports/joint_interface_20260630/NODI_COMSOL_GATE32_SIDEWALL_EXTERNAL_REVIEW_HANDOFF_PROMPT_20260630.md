# Gate32 External AI Research Synthesis Handoff: NODI Package C Sidewall Reflection Candidate

You can only rely on GitHub-visible files. Do not assume access to local
Codex files, COMSOL models, `.mph` files, or untracked workspace artifacts.

This is not a narrow audit request. Please use your ability to search and
compare broader technical/literature sources. The goal is to answer enough
methodology, evidence, and next-step questions in one pass that Codex can move
several implementation gates forward without repeated back-and-forth review.

## Current candidate

- Disposition: `NODI_GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF_READY_NO_PROOF_REGISTRATION`
- Gate30/31 source disposition: `NODI_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_READY_NO_PROOF_REGISTRATION`
- Candidate artifact id: `GATE30_31_PACKAGE_C_REFLECTION_PROOF_METRICS_CANDIDATE_20260630`
- Claim boundary: `candidate_only_finite_step_reflection_surrogate_not_package_c_proof_registered`
- Scenario/open/blocked metric rows: `216` /
  `198` / `18`
- dt-halving rows: `66`
- Max boundary atom fraction: `0.001302083`
- Max equilibrium uniformity distance: `0.052822321`
- dt-halving max distribution delta: `0.096354167`

Candidate metric statuses:
- support invariance: `candidate_pass`
- no boundary atom: `candidate_pass`
- equilibrium uniformity proxy: `candidate_pass`
- dt halving: `candidate_pass`
- corner active set: `candidate_pass`
- one-wall limit: `candidate_pass`
- rectangle limit: `candidate_pass`
- angle/depth mutation: `candidate_pass`

## Hard boundary

This is not Package C proof/pass registration. It is not runtime authorization,
PRS/EAS numeric output, NODI recomputation, COMSOL launch, `.mph` load,
route/yield/detection/wet/fabrication/production authorization, validated
hindered diffusion, trapezoid Poiseuille, electrokinetic solver, optical solver,
or true W_eff evidence.

Current authorization fields are all false:
- `proof_registration_authorized=false`
- `package_c_validation_status_pass_authorized=false`
- `runtime_allowed=false`
- `numeric_prs_eas_allowed=false`
- `comsol_launch_allowed=false`
- `mph_load_allowed=false`

## GitHub-visible files to review

- `start_here_prompt`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_EXTERNAL_REVIEW_PROMPT_20260630.md
- `gate30_31_status`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_STATUS_20260630.json
- `gate30_31_summary_metrics`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_SUMMARY_METRICS_20260630.json
- `gate30_31_raw_metrics`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_RAW_METRICS_20260630.json
- `gate30_31_candidate_manifest`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_CANDIDATE_MANIFEST_20260630.csv
- `gate30_31_evidence_map`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_CANDIDATE_EVIDENCE_MAP_20260630.csv
- `gate30_31_no_proof_firewall`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv
- `gate30_31_parameter_matrix`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_TEST_PARAMETER_MATRIX_20260630.csv
- `gate30_31_seed_matrix`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/joint_interface_20260630/NODI_COMSOL_GATE30_31_SIDEWALL_RNG_SEED_MATRIX_20260630.csv
- `geometry_implementation`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/nodi_simulator/cross_section_geometry.py
- `trajectory_integration`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/nodi_simulator/trajectory.py
- `gate30_31_builder`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/tools/audits/build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py
- `gate30_31_tests`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/tests/test_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py
- `roadmap`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md
- `audit_packet`: https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main/reports/345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md

## Research synthesis questions

Please answer all of these with source-backed analysis and concrete engineering
recommendations:

G32-RESEARCH-001. Find and synthesize authoritative sources on reflected Brownian motion / Skorokhod reflection in convex polygonal domains; state what is and is not justified for a finite-step engineering surrogate.
G32-RESEARCH-002. Compare active-set normal reflection, sequential half-plane reflection, projection/clamp, rejection/resampling, substepping, and exact/approximate reflected-kernel methods for polygonal domains.
G32-RESEARCH-003. Identify the strongest one-wall Neumann/folded-normal sanity tests and what tolerances or diagnostics are appropriate for finite dt Brownian dynamics near a planar wall.
G32-RESEARCH-004. Recommend equilibrium uniformity tests for reflecting Brownian motion in a trapezoid center-accessible domain, including u-marginal, x-local normalized slices, symmetry, and sample-size requirements.
G32-RESEARCH-005. Recommend diagnostics for boundary atoms, projection spikes, wall pile-up, and how to distinguish acceptable finite-step reflection contacts from artificial boundary clamping.
G32-RESEARCH-006. Analyze corner active-set behavior in convex polygonal reflection, including normal-cone ambiguity, corner pile-up risks, dt/substep triggers, and convergence telemetry.
G32-RESEARCH-007. Propose a proof-level dt-halving matrix and quantitative pass/fail thresholds for wall-distance distributions, local x/u distributions, nearest-wall counts, and reflection/corner event rates.
G32-RESEARCH-008. Recommend additional proof artifact fields beyond the current 52-field candidate manifest, especially raw metric reproducibility, environment locks, seed policy, and reviewer/authorization records.
G32-RESEARCH-009. Check whether hindered diffusion, hydrodynamic wall effects, trapezoid pressure-flow, electrokinetic grid/Poisson-Boltzmann, optical/reference-field effects, wet pass/clogging/recovery/yield/detection must remain blocked.
G32-RESEARCH-010. Give an engineering go-forward plan that would let Codex proceed for several gates without repeated review loops, including which evidence to add next and which decisions require manual authorization.

## Requested external verdict

Return exactly one of:
- `READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY`
- `NEEDS_MORE_CANDIDATE_EVIDENCE`
- `BLOCKED_CLAIM_PROMOTION`

Please close with:
1. A ranked list of evidence to add next, grouped into work that Codex can do
   immediately versus work that requires manual authorization, COMSOL, measured
   profiles, optical/electrokinetic solvers, or wet experiments.
2. A threshold/test-matrix recommendation for no-boundary-atom, equilibrium
   uniformity, dt convergence, one-wall limit, rectangle limit, and corner bias.
3. A claim-boundary risk list: any term, field, metric, or report language that
   could be misread as proof/pass registration, runtime authorization, wet
   performance, route selection, yield, or detection probability.
4. A go-forward route that should minimize future review loops.
