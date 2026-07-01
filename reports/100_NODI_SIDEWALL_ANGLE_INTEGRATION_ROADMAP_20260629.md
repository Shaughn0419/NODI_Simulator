# 100 - NODI sidewall-angle integration roadmap

Date: 2026-06-29

Status: roadmap_only; no NODI recomputation; no COMSOL launch; no `.mph` load; no route winner; no route_score; no chi_selected; no JRC; no q_ch weighting; no yield; no detection_probability; no fabrication release.

## 0. Executive boundary

The right way to add dry-etch sidewall-angle sensitivity into NODI is not to add one scalar and rerun the current sweep. NODI already has a partial geometry descriptor layer (`trapezoid_tapered_sidewalls`, EAS, COMSOL descriptor metadata), but the main runtime still treats the nanochannel as a rectangle for initial-position sampling, trajectory reflection, near-wall gaps, many transport estimates, and much of the optical/reference-field surrogate. Therefore sidewall-angle work must be staged:

1. Freeze the angle convention and geometry descriptor first.
2. Propagate the trapezoid geometry into accessible area, steric gates, sampling, trajectory boundaries, near-wall distance, transport/residence diagnostics, and reference-field diagnostics.
3. Keep COMSOL rows and transported-position descriptors as `context-only` until exact grain matching and authorization are present.
4. Preserve all no-claim flags: no `JRC`, no `q_ch*eta`, no `q_ch*chi*eta`, no `chi_selected`, no `route_score`, no `winner`, no `yield`, no `detection_probability`, no `wet pass probability`, no `clogging rate`, no production/runtime ingestion.

The immediate deliverable should be a NODI-side sidewall-angle sensitivity program, not a new design conclusion.

In this roadmap, a `hard fail` means a validator, row, artifact, cache, or package cannot be labeled sidewall-aware and cannot advance to the next package. It is not a design, physics, or fabrication failure. A hard-failed row may remain visible only as an audit row labeled `blocked`, `descriptor_only`, or `context-only`, with no formula use, runtime config, production ingestion, scoring, or route conclusion.

The main refinement after independent review is therefore not a larger angle scan. It is to make validators reject hidden rectangular leakage, make cache keys reject old rectangular runs, and make schema/column names prevent claim promotion.

## 1. Evidence read and cross-agent synthesis

### 1.1 NODI current state

Relevant NODI files and artifacts:

- `nodi_simulator/data_objects.py`: core `Channel(width_m, depth_m)` model; x is width, z is depth, y is flow direction. Existing config fields include `channel_cross_section_model`, `sidewall_taper_angle_deg`, `corner_radius_nm`, `surface_roughness_rms_nm`, `width_along_channel_cv`, `depth_along_channel_cv`, and `measured_profile_path`.
- `nodi_simulator/cross_section_geometry.py` and `nodi_simulator/channel_geometry_model.py`: trapezoid geometry now has a shared primitive/oracle layer that preserves unclipped bottom width, closure status, center-accessible support, and descriptor/runtime clip separation.
- `nodi_simulator/utils.py`: trapezoid initial-position sampling is routed through the center-accessible support oracle; flux-weighted trapezoid sampling remains blocked unless a compatible trapezoid flow model exists.
- `nodi_simulator/trajectory.py`: trapezoid runs are guarded against rectangular reflection, rectangular near-wall diffusion, and rectangular flow-profile leakage. Pure-advection plug-flow audit paths can continue only with explicit geometry propagation diagnostics.
- `nodi_simulator/fluidic_resistance.py` and `nodi_simulator/electrokinetic_transport.py`: trapezoid hydraulic/electrokinetic paths are now explicitly marked proxy/blocked where geometry has not been propagated; no trapezoid Poiseuille, q_ch, clogging-rate, or wall-distance transport claim is emitted.
- `nodi_simulator/reference_field.py`: trapezoid reference-field paths are explicitly marked as rectangular width/depth proxies or geometry-independent audit paths, with `not_optical_solver_output=true` and `optical_solver_trigger_is_result=false`.
- `nodi_simulator/parameter_sweep.py`: observation signatures now include cross-section model, taper angle, particle radius, geometry propagation status, closure policy, sampler/trajectory/flow/reference guard fields, so old rectangular cache/signature states cannot silently satisfy trapezoid requests.
- `roadmap/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv`: already contains descriptor fields such as `sidewall_deg`, `depth_um`, `W_top_um`, `W_bottom_um`, `bottom_width_nm`, `D_inscribed_nm`, and `min_aperture_nm`, but only as descriptor metadata. It preserves negative bottom-width rows in descriptor space; current NODI runtime must not silently clip those rows into open runtime apertures.
- `nodi_simulator/nodi_comsol_next_artifacts.py`: existing EAS/PRS and Gate2 artifacts are bounded as surrogate sensitivity or `context-only`, not formula, not production, not route scoring. Sidewall v2 descriptor/PRS/EAS fields now have marker-triggered hard validators while preserving legacy V1 contracts.

NODI therefore has a useful starting point and several runtime leak guards are now implemented, but the simulator is not yet a fully sidewall-aware transport/optical engine. The remaining work is to replace guarded/proxy areas with validated trapezoid trajectory, flow, near-wall transport, and optical/reference solvers before any result can be promoted beyond audit or surrogate sensitivity.

### 1.2 COMSOL current state

Relevant COMSOL-side evidence:

- Nano dry-etch sidewall is a first-order process sensitivity. COMSOL has treated nano sidewall-angle/depth explicitly, unlike micro sidewall, where hydraulic impact was reviewed as comparatively small.
- COMSOL angle convention uses sidewall angle from the substrate/horizontal plane, with `90 deg` meaning vertical. NODI's `sidewall_taper_angle_deg` is a taper angle from vertical. These are complementary, not interchangeable.
- Stage119 sidewall-depth matrix spans sidewall/depth combinations and marks `pass`, `warning`, `geometry_closed`, and `solver_guard` cases. The main process focus window is `85 deg / 0.9-1.2 um`; `85 deg / 1.2 um` is a first-fabrication anchor but carries warning/boundary context.
- COMSOL normal-nanochannel V4/Stage119 outputs are smooth-wall hydraulic/descriptor surfaces, not wet vesicle, adhesion, clogging, recovery, event-rate, route-winner, or fabrication-release claims.
- Wall tau is currently a descriptor/proxy path unless a real verified local surface extraction is available.
- Gate2C/Gate2D alignment rows are `context-only`; Gate2D's four reduced-scope rows are accepted only as `context-only` artifact-level ledger entries, not accepted for grain-level ingestion, formula use, runtime config, production, or route conclusion. `velocity_weighted` and `residence_time_weighted` are TPD proxy aggregation descriptors, not NODI route weighting and not q_ch weighting.

### 1.3 Cross-agent agreement

Three independent read-only reviews converged on the same hazards:

| Source | Main finding | Action adopted here |
| --- | --- | --- |
| NODI-focused review | NODI has sidewall descriptor/EAS fields but main runtime geometry remains rectangular. | Roadmap separates descriptor, runtime geometry, transport, optical, and interface gates. |
| COMSOL-focused review | COMSOL sidewall/depth evidence can only enter NODI as bounded context unless grain/claim gates are satisfied. | Roadmap keeps Stage119/Gate2C/Gate2D as `context-only` and blocks promotion to scoring. |
| Cross-project risk review | A scalar sidewall field would create false confidence if sampling, trajectory, near-wall distance, and bins remain rectangular. | Roadmap requires mutation tests proving geometry propagation or explicit `not_propagated` flags. |

### 1.4 Implementation progress as of 2026-06-30

Completed NODI-side guardrails:

- Added `TrapezoidCrossSection` geometry primitive and tests for COMSOL/NODI angle conversion, bottom-width preservation, closure status, center-accessible area, wall-normal particle support, and uniform accessible-area sampling.
- Added a trapezoid particle-center support projection primitive and guarded trajectory path; this is a projection-boundary surrogate, not validated specular sloped-wall reflection or near-wall diffusion.
- Routed trapezoid initial-position sampling through the geometry oracle; rectangular sampler fallback is no longer accepted for trapezoid support rows.
- Added trajectory diagnostics that hard-block rectangular reflection, rectangular near-wall diffusion, and incompatible rectangular flow profiles under active trapezoid geometry.
- Added explicit electrokinetic, fluidic, and reference-field propagation statuses so non-propagated trapezoid paths remain audit/proxy rows, not sidewall-aware runtime results.
- Added sidewall geometry fields to observation signatures, including particle radius and reference-field geometry propagation status.
- Added artifact/schema hard-fails for claim-promotion column names, descriptor v2 sidewall fields, PRS sidewall v2 sampler/support/bin fields, and EAS sidewall v2 no-claim guards.
- Added PRS/EAS sidewall v2 row-level hard-fails for runtime propagation guard fields, Package D precheck binding, source route/depth/bin grain binding, and explicit `geometry_propagation_scope`.
- Added EAS geometry-marker triggering so `channel_cross_section_model=trapezoid_tapered_sidewalls` cannot bypass sidewall v2 validation.
- Added PRS trajectory guard columns for boundary model version, claim level, wall-distance claim level, flow-geometry claim level, not-propagated trajectory flags, and `sidewall_aware_runtime_status`.
- Added PRS/EAS sidewall v2 observation-signature hard-fails that bind `geometry_propagation_scope`, `channel_cross_section_model`, and `geometry_propagation_status`, so ideal-rectangle and trapezoid cache/signature states cannot satisfy each other.
- Expanded PRS/EAS sidewall v2 forbidden exact-column tests for `W_eff`, `score`, `route_score`, `sidewall_score`, `winner`, `chi_selected`, `JRC`, `q_ch`, `q_ch_eta`, `q_ch_chi_eta`, `yield`, `detection_probability`, `wet_pass_probability`, `clogging_rate`, `time_to_clog`, and `recovery`.
- Added PRS sidewall v2 rank-promotion hard-fail for nonblank `rank_under_surrogate`; legacy EAS rank columns remain blank-only in sidewall v2 rows.
- Refined sidewall v2 activation so ordinary PRS/EAS rows may explicitly carry `channel_cross_section_model=ideal_rectangle` without being forced into sidewall v2 schema; `trapezoid_tapered_sidewalls` and dedicated sidewall v2 fields still trigger hard validation.
- Expanded observation-signature binding to compare row values for geometry version, sampler/support, trajectory boundary, wall-distance, flow, reference, fluidic, electrokinetic, angle, and particle-radius guard fields rather than accepting stale key-name fragments.
- Added fluidic, fluidic-network, and electrokinetic model/claim guard fields to required observation signatures so proxy/blocked transport state changes cannot reuse stale sidewall cache identities.
- Added cache-status hard-fail so `blocked_old_rectangular_cache` cannot satisfy propagated sidewall PRS/EAS rows and is limited to blocked/non-propagated audit semantics.
- Added Package B particle-center support slice oracle for `open` / `narrow` / `blocked` status and steric block reasons, then routed trapezoid sampler diagnostics through that oracle.
- Added initial-position sampler support model, particle-center support status, and steric block reason to observation signatures so sampler-support diagnostics cannot reuse stale cache identities.
- Added PRS sidewall v2 validator checks requiring initial-position sampler-support signature fragments and binding `sampler_support_model` to `initial_position_sampler_support_model`; EAS sidewall v2 remains aperture-surrogate scoped and is not forced to carry PRS bin semantics.
- Added a trapezoid wall-distance / particle surface-gap primitive that emits nearest-wall geometry diagnostics only; it is not a hindered-diffusion, adhesion, wet-pass, clogging, recovery, or passability model.
- Added PRS sidewall v2 formula-level local-geometry checks for `W(u)`, sidewall-normal distances, top/bottom distances, nearest-wall identity, and particle surface gap while preserving the explicit ideal-rectangle context path.
- Added trapezoid initial-position wall-distance diagnostics and signature fragments for the geometry-only wall-distance model/claim level; PRS sidewall v2 now rejects signatures missing those sampler wall-distance identifiers.
- Tightened PRS sidewall v2 sampler wall-distance signature checks to require the exact `geometry_distance_primitive_not_hindered_diffusion` no-claim level, preventing hidden promotion to validated hindered-diffusion results.
- Bound PRS sidewall v2 wall-distance bins to Package C precheck status: any `wall_distance` bin basis must declare `includes_trajectory_near_wall_metrics=true` and `package_C_validation_status=pass`.
- After independent review, changed the current default PRS sidewall v2 propagated scope back to `particle_center_support_only_not_reference_fluidic_electrokinetic`; wall-distance-bin PRS rows remain blocked until an explicit future Package C authorization proof is registered.
- Made Package C proof binding fail-closed in the current no-auth gate: the proof registry is empty, hard-coded fixture hashes are not accepted, and `package_C_validation_status=pass` fails until a real physics authorization artifact is registered.
- Renamed sidewall trajectory runtime statuses from `no_wall_metrics` to `no_hindered_wall_metrics`, preserving the geometry-only wall-distance primitive while still blocking hindered-diffusion / wet-wall interpretations.
- Added prefixed channel-geometry descriptor wall-distance identity fields (`channel_geometry_wall_distance_model`, `channel_geometry_wall_distance_claim_level`) so ideal rectangles remain `rectangular_half_span_gap_v1` while trapezoid rows emit `trapezoid_signed_wall_distance_v1` with `geometry_distance_primitive_not_hindered_diffusion`, without colliding with trajectory `wall_distance_model`.
- Hardened PRS/EAS sidewall v2 validators so those prefixed channel-geometry wall-distance fields are required, signature-bound, and cannot be promoted to validated hindered-diffusion claims.
- Expanded Package C precheck enforcement so any PRS basis/source-basis field carrying `wall_distance` semantics requires `includes_trajectory_near_wall_metrics=true` and `package_C_validation_status=pass`, not only `bin_basis`.
- Bound actual batch sampler diagnostics into summary/reference/intrinsic observation signatures, with actual-path trapezoid batch tests proving `initial_position_wall_distance_model=trapezoid_signed_wall_distance_v1` is emitted by both event-loop and pure-advection block runtimes rather than only by hand-built fixtures.
- Expanded exact claim-promotion blacklists for sidewall PRS/EAS artifacts to reject `rank`, `route_rank`, `sidewall_rank`, `JOINT_ROUTE_CLASS`, `q_ch_weight`, and `q_ch_weighting` while preserving provenance fields such as `rank_source`.
- Hardened route/sidewall score alias rejection so names such as `route_score_norm` and `sidewall_score_value` cannot bypass the exact `route_score` / `sidewall_score` blacklist in sidewall artifacts or Package D precheck.
- Hardened positive JRC/chi-selected alias rejection with targeted fragments such as `JRC_value`, `joint_route_class_candidate`, `joint_route_class_id`, and `chi_selected_flag` while preserving explicit false/no-claim governance fields.
- Extended the sidewall PRS/EAS exact-column blacklist to reject bare `flow_rate` and `Q`, matching the roadmap rule that COMSOL Q/proxy fields cannot become formal `q_ch` without a future sidecar gate.
- Hardened the same flow/q guard against unitized and COMSOL-proxy aliases such as `flow_rate_m3_s`, `Q_m3_s`, `q_ch_m3_s`, and `comsol_Q_proxy` across PRS, EAS, and Package D precheck scanning.
- Added targeted rank-alias rejection for positive fields such as `rank_value`, `route_rank_value`, and `sidewall_rank_value`, and made Package D precheck reject nonblank `rank_under_surrogate` while keeping legacy non-sidewall rows outside this sidewall v2 gate.
- Tightened PRS sidewall v2 blocked-bin guards so `bin_accessible=false` and `bin_particle_center_support_status=blocked` must agree, every blocked bin needs `blocked_reason`, neighbor fill remains forbidden, and numeric response/proxy values are rejected across all blocked response fields.
- Bound COMSOL descriptor profile provenance so sidewall v2 rows with `geometry_profile_source=comsol_descriptor` must keep `geometry_profile_sha256` identical to `source_geometry_descriptor_sha`, preventing descriptor/profile hash drift.
- Bound profile identity into observation signatures with `geometry_profile_source`, `geometry_claim_level`, and `metrology_status`, so profile SHA reuse cannot silently change descriptor/measured-claim semantics.
- Added Gate14 no-auth implementation contract coverage for the NODI sidewall guard release and COMSOL Gate14 successor-head intake, keeping the COMSOL Gate13 package receipt valid while recognizing the known Gate14 producer successor.
- Added EAS sidewall v2 guards requiring generic `W_eff_surrogate_nm` to be an explicit numeric alias of a named sidewall-specific surrogate, while eta/rank-source fields remain blank or claim-labeled as disabled/no-rank legacy provenance.
- Added propagated trapezoid PRS allowlists so sampler, flow, and trajectory-boundary models cannot be blank or silently upgraded beyond the implemented `trapezoid_accessible_area_v1`, `plug`, and declared pure-advection/projection-boundary states.
- Added runtime top-aperture binding guards so `mask_width`, `top_cd`, and `post_bias_top_cd` descriptor semantics cannot be used as propagated/runtime aperture inputs unless `runtime_top_aperture_nm`, `top_cd_bias_nm`, and `top_cd_bias_source` are present and numerically consistent; PRS/EAS sidewall v2 descriptor-context rows inherit the same hard fail.
- Added a bare-angle-field convention guard so loose descriptor rows carrying `sidewall_deg`, `sidewall_angle`, or `taper_angle` without `sidewall_angle_convention` or legacy `angle_convention` hard-fail instead of silently inheriting the wrong COMSOL/NODI angle meaning.
- Added PRS/EAS sidewall v2 observation-signature binding for descriptor identity fields including angle convention, COMSOL angle, `W_top_semantics`, source descriptor hash, geometry runtime binding version, top/depth/bottom dimensions, closure status, closure policy, and runtime guard status.
- Hardened runtime channel-geometry diagnostics so `measured_profile_lookup` remains blocked metadata-only until an actual profile loader/hash/validator exists; `measured_profile_loaded`, `measured_profile_validated`, `measured_profile_sha256`, and runtime status are now emitted and included in observation signatures.
- Added a batch-level measured-profile lookup regression so `run_single_case_batch` keeps configured-but-unloaded measured profiles as metadata-only/blocked runtime state in both summary output and `observation_signature`.
- Tightened descriptor v2 measured-geometry claims so `geometry_claim_level=measured_geometry` requires explicit `measured_profile_loaded=true` and `measured_profile_validated=true`, in addition to measured source/path/hash metadata.
- Added propagated trapezoid PRS `flow_control_mode` allowlist so sidewall-aware PRS rows cannot silently mix fixed-pressure semantics into the current fixed-velocity-only plug-flow surrogate.
- Aligned EAS sidewall v2 propagation-status usage with PRS: `geometry_propagation_status=propagated` now hard-fails if `geometry_not_propagated_reasons` is nonblank.
- Closed the optional `runtime_top_aperture_nm` signature drift hole found by independent review: when the row has no runtime top-aperture value, PRS/EAS sidewall v2 signatures may only carry `runtime_top_aperture_nm=unknown`, not a numeric value.
- Added a positive `sidewall_aware=true` shortcut guard so artifacts must use explicit sidewall v2 schema/status fields rather than a broad boolean promotion flag; negative boundary flags such as `sidewall_aware=false` remain allowed.
- Added Gate23 static fixture execution packet: Gate22 source hashes are locked, 29 static fixture execution rows are executable as no-runtime pytest/validator surfaces, validator CLI success text is `PASS_CONTEXT_ONLY_NOT_PRODUCTION`, and Package C proof remains fail-closed.
- Added Gate24 Package C future-authorization ledger: Gate23 source hashes are locked without drift, the exact future Package C authorization phrase is recorded but still yields `authorized_now=false`, and Package C physics, proof-registry update, runtime configuration, NODI recomputation, COMSOL launch, `.mph` load, sidewall PRS/EAS numeric output, q_ch/JRC/route-score/winner/yield/detection/fabrication permissions all remain false.
- Added Gate25 Package C design-review packet: Gate24 sources are locked, Package C trajectory/near-wall/flow/electrokinetic/optical questions are separated into design-review rows, a self-contained external-AI prompt records local geometry formulas and current NODI boundaries, and implementation/runtime permissions remain false.
- Added Gate26 Package C external-review integration packet: the user-pasted external-AI verdict `READY_FOR_IMPLEMENTATION_DESIGN_ONLY` is captured as a SHA-locked source artifact and integrated only as design constraints; Skorokhod normal reflection is recorded as the future Brownian target model, the current projection boundary remains a non-validated surrogate, 20 required Package C tests and 46 schema fields are listed, hindered/flow/electrokinetic/optical blockers are preserved, and implementation/runtime/PRS-EAS numeric/COMSOL/.mph/q_ch/JRC/route/yield/detection/fabrication permissions all remain false.
- Added Gate27 Package C implementation-design preflight: Gate26 sources are locked, the future Skorokhod/corner/equilibrium/dt/schema/blocker work is mapped into a no-auth backlog, a real proof-artifact contract is defined, current `package_C_validation_status=pass` remains fail-closed without a registered proof, and proof registration/runtime/PRS-EAS numeric/COMSOL/.mph/q_ch/JRC/route/yield/detection/fabrication permissions all remain false.
- After explicit user authorization for Package C implementation code and unit tests, added the first Skorokhod/finite-step trapezoid reflection implementation candidate: geometry now exposes wall constraints and inward normals, trajectory uses `trapezoid_skorokhod_normal_reflection_euler_active_set_v1` for trapezoid diffusive plug-flow paths, PRS sidewall v2 validators now accept the post-registration claim guard `finite_step_reflection_surrogate_package_c_proof_registered_not_validated_brownian_solver_output_not_hindered_hydrodynamics`, and single-wall/corner/support/no-boundary-atom/rectangle-limit unit tests are in place. This remains finite-step surrogate evidence only and emits no PRS/EAS numeric output.
- Expanded the Package C proof scaffold: any future `package_C_validation_status=pass` row must carry reviewed evidence hashes, implementation commit binding, required-test matrix status, external review completion, explicit authorization id/hash superseding the no-auth ledger, and no-claim flags for hindered diffusion, trapezoid flow solver, electrokinetic solver, optical solver, wet claims, PRS/EAS numeric output, and route/yield/detection claims. The proof registry is still empty and fail-closed.
- Added Gate28 Package C proof-review packet: the current implementation candidate is packaged for external/independent review with source locks, a 6-command pytest/py_compile/git-diff evidence ledger, a self-contained external-AI prompt, and a no-proof firewall. Gate28 reports `evidence_pass_rows=6`, `source_missing_rows=0`, `proof_registration_authorized=false`, `runtime_allowed=false`, `numeric_prs_eas_allowed=false`, `comsol_launch_allowed=false`, and `mph_load_allowed=false`; it does not register Package C proof/pass.
- Added Gate29 external proof-review integration: external verdict `READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY` is captured as review-only input, the proof scaffold is expanded to 52 required fields with telemetry/reproducibility locks, and Gate29 emits 19 future hard gates plus 24 telemetry/reproducibility fields while keeping proof registration/runtime/numeric/COMSOL/`.mph` permissions false.

Still blocked in this roadmap:

- validated sloped-wall specular reflection, Package C proof/pass for Skorokhod/reflected-Brownian implementation, and near-wall diffusion under Brownian trajectories;
- trapezoid-compatible flow field or flux-weighted sampler;
- trapezoid-aware electrokinetic wall-distance grid;
- full optical/reference-field solver output;
- route winners, route_score, JRC, q_ch weighting, yield, detection_probability, wet pass probability, clogging rate, time-to-clog, recovery, fabrication release, or production/runtime ingestion.

## 2. Core physical principles

### 2.1 Angle convention and trapezoid geometry

Use two separate fields:

- `sidewall_deg_comsol`: angle from substrate/horizontal plane; `90 deg` is vertical.
- `sidewall_taper_angle_deg_nodi`: taper angle from vertical.

Conversion:

```text
alpha_taper_deg = 90.0 - sidewall_deg_comsol
sidewall_deg_comsol = 90.0 - alpha_taper_deg
```

For a symmetric dry-etched trapezoid that narrows from top to bottom, define:

```text
W_top = top/mask width
H = nanochannel depth
theta = sidewall_deg_comsol
alpha = 90 deg - theta
k = tan(alpha) = 1 / tan(theta)

W(u) = W_top - 2 * k * u, 0 <= u <= H
W_bottom_unclipped = W_top - 2 * H / tan(theta)
H_closure = 0.5 * W_top * tan(theta)
```

NODI must not pass COMSOL `85 deg` into `sidewall_taper_angle_deg=85`. The correct internal taper for a COMSOL `85 deg` sidewall is `5 deg`.

Example checks:

- `W_top=500 nm`, `H=900 nm`, `theta=85 deg`: `W_bottom_unclipped ~= 342.52 nm`.
- `W_top=500 nm`, `H=600 nm`, `theta=70 deg`: `W_bottom_unclipped ~= 63.24 nm`.

Descriptor artifacts should preserve `W_bottom_unclipped`, including negative values. Runtime branches may also carry a clipped value for numerical geometry, but clipping must be explicit:

```text
W_bottom_unclipped_nm
W_bottom_runtime_clipped_nm
closure_status = open | near_closed | geometry_closed
runtime_guard_status = none | solver_guard | validation_guard | resource_guard
closure_policy = preserve_unclipped_descriptor | closure_clamped_runtime | blocked_runtime
```

### 2.2 Particle-accessible region and steric exclusion

For particle radius `a`, the center-accessible region is smaller than the etched fluid region. A first-order trapezoid surrogate can use wall-normal exclusion:

```text
sidewall half width at depth u:
h(u) = W(u) / 2

distance to sidewall:
d_side(x, u) = (h(u) - abs(x)) / sqrt(1 + k^2)

center-accessible side constraint:
d_side(x, u) >= a
abs(x) <= h(u) - a * sqrt(1 + k^2)

top/bottom center constraints:
a <= u <= H - a
```

This matters most for 220 nm, 300 nm, and the large tail of EV size distributions. It is unsafe to judge passability from `W_top` or average width alone.

### 2.3 Near-wall distance and hindered diffusion

The current rectangular near-wall gap uses fixed half-width and half-depth. A trapezoid model needs wall-distance primitives:

```text
d_top = u
d_bottom = H - u
d_left_or_right = (h(u) - abs(x)) / sqrt(1 + k^2)
d_nearest_wall = min(d_top, d_bottom, d_left_or_right)
surface_gap_for_particle = d_nearest_wall - a
```

Any near-wall diffusion, wall-risk, wall-contact, selected-annulus, or edge-bin logic must use this geometry-aware distance. If not, it must emit an explicit `geometry_not_propagated_to_near_wall_metrics` flag.

### 2.4 Flow and residence time

Sidewall angle changes cross-section area, hydraulic diameter, perimeter, velocity profile, residence time, and local near-wall exposure. A basic geometric diagnostic can compute:

```text
A = 0.5 * (W_top + W_bottom_open) * H
s_side = sqrt(H^2 + ((W_top - W_bottom_open) / 2)^2)
P_wetted ~= W_top + W_bottom_open + 2 * s_side
D_h = 4 * A / P_wetted
```

However, this is not a full Stokes/Poiseuille solution. Rectangular duct series should not be silently reused for a trapezoid. Acceptable staging:

1. Descriptor-only: area, perimeter, bottom throat, closure status.
2. Diagnostic surrogate: area-scaled or hydraulic-diameter-scaled residence sensitivity with clear label.
3. Trapezoid cross-section solver: 2D cross-section Poisson/no-slip numerical solver or validated lookup.
4. COMSOL/experiment binding: pressure-flow and tracer-flow calibration, still with claim guards.

### 2.5 Optical and NODI reference-field effects

Sidewall angle can affect NODI optical response through:

- empty-channel diffraction/reference amplitude;
- phase thickness and effective aperture;
- local scattering/reference interference as particle positions shift;
- edge illumination and mode overlap;
- background/roughness leakage if roughness is also varied.

The current EAS modes (`nominal_width`, `W_bottom_conservative`, `min_aperture_conservative`, `top_bottom_average_heuristic`) are useful first-pass sensitivity modes, but they are not `true_W_eff`, not measured geometry, and not optical solver output.

If sidewall-angle sensitivity changes NODI response ordering, reference strength, or near-wall bin behavior materially, the correct next step is an optical solver/readiness gate, not a claim promotion.

### 2.6 Roughness, residue, lip, and corner physics

Do not collapse all fabrication effects into sidewall angle. Keep separate roles:

- `sidewall_deg`: trapezoid slope and bottom throat.
- `corner_radius_nm`: rounded-corner steric/accessibility and field smoothing.
- `surface_roughness_rms_nm`: may affect optical background, hydraulic friction, and wall interaction, but those uses need separate labels.
- `roughness_correlation_length_nm` and `scallop_amplitude_nm`: optional second-stage dry-etch texture descriptors.
- `edge_lip_nm_per_side` and `residue_thickness_nm`: reduce aperture differently from symmetric taper.
- `width_along_channel_cv`, `depth_along_channel_cv`: longitudinal variability, not cross-section taper.
- `measured_profile_path` and profile hash: only measured if the profile is actually loaded and validated.

## 3. Required parameter set

### 3.1 Geometry and process parameters

| Field | Meaning | Required stage |
| --- | --- | --- |
| `channel_cross_section_model` | `ideal_rectangle`, `trapezoid_tapered_sidewalls`, `rounded_rectangle`, `measured_profile_lookup` | G0 |
| `sidewall_angle_convention` | Explicit convention string | G0 |
| `sidewall_deg_comsol` | Angle from substrate/horizontal, 90 deg vertical | G0 |
| `sidewall_taper_angle_deg_nodi` | Internal angle from vertical | G0 |
| `angle_conversion_formula_id` | Stable id for conversion | G0 |
| `W_top_nm` | Top width value; runtime use requires `W_top_semantics=runtime_top_aperture` or `runtime_top_aperture_nm` binding | G0 |
| `W_top_semantics` | `runtime_top_aperture`, `mask_width`, `top_cd`, `post_bias_top_cd`, or `comsol_descriptor` | G0 |
| `mask_top_width_nm` | Lithographic or descriptor top width before optional CD corrections | G0 |
| `top_cd_bias_nm` | Bias applied to top CD when supported by source evidence | G1 |
| `top_cd_bias_source` | Source and claim level for any top-CD/process bias | G1 |
| `runtime_top_aperture_nm` | Top aperture actually bound into a runtime geometry profile | G1 |
| `D_nm` / `depth_nm` | Nanochannel depth | G0 |
| `W_bottom_unclipped_nm` | Formula bottom width, negative preserved | G0 |
| `W_bottom_runtime_clipped_nm` | Optional numerical/runtime bottom width | G1 |
| `closure_depth_nm` | Depth at which sidewalls meet | G0 |
| `closure_status` | Geometric state: `open`, `near_closed`, `geometry_closed` | G0 |
| `runtime_guard_status` | Execution/solver state such as `none`, `solver_guard`, `validation_guard`, `resource_guard` | G0 |
| `closure_policy` | How runtime handles closed geometry | G1 |
| `min_aperture_descriptor_nm` | Conservative descriptor convenience field; not EV passability evidence | G1 |
| `D_inscribed_nm` | Diameter-inscribed aperture descriptor if available | G1 |
| `corner_radius_nm` | Rounded-corner surrogate | G2 |
| `surface_roughness_rms_nm` | Roughness RMS, role-specific | G2 |
| `roughness_correlation_length_nm` | Optional roughness texture length | G3 |
| `scallop_amplitude_nm` | Optional etch scallop descriptor | G3 |
| `edge_lip_nm_per_side` | Optional lip/aperture loss | G3 |
| `residue_thickness_nm` | Optional residue aperture loss | G3 |
| `width_along_channel_cv` | Longitudinal width variability | G2 |
| `depth_along_channel_cv` | Longitudinal depth variability | G2 |
| `geometry_profile_source` | `parameterized`, `comsol_descriptor`, `sem`, `fibsem`, `profilometry`, etc. | G0 |
| `geometry_profile_sha256` | Hash of source profile/descriptor | G0 |
| `metrology_status` | `not_measured`, `pending`, `measured_unvalidated`, `validated` | G0 |
| `geometry_claim_level` | `descriptor_only`, `surrogate_sensitivity`, `measured_geometry`, etc. | G0 |

### 3.2 NODI optical and readout parameters

| Field | Why it matters |
| --- | --- |
| `lambda_nm` | Wavelength interacts with aperture/reference response. |
| `NODI_view` | Fixed-view and per-wavelength views must not be mixed silently. |
| `reference_field_model` | Determines whether width/depth are optical geometry, phase mask, or fallback parameters. |
| `reference_spatial_mode` | Must be tagged if using rectangle, effective aperture, or trapezoid surrogate. |
| `reference_route` | Needed for observation signature and old-cache separation. |
| `illumination_mode` | Edge illumination can interact with geometry-dependent particle distributions. |
| `detector_operator_id` | Needed to keep PRS response surfaces comparable. |
| `optical_geometry_claim_level` | `surrogate`, `solver_required`, `optical_solver_output`, etc. |

### 3.3 Transport, particle, and sampling parameters

| Field | Why it matters |
| --- | --- |
| `particle_diameter_nm` / `particle_radius_m` | Steric accessibility depends on bottom throat and wall-normal exclusion. |
| `particle_kind` / EV size distribution | Tail sizes may become blocked before mean diameter does. |
| `particle_support_model` | Must identify the steric support oracle, e.g. `wall_normal_half_plane_offset_v1`. |
| `particle_center_support_status` | `open`, `narrow`, or `blocked`; required before any PRS/EAS sidewall pilot row. |
| `center_accessible_area_fraction` | Required support descriptor; not yield or pass probability. |
| `initial_position_distribution_mode` | Uniform/flux-weighted/center-biased samplers need trapezoid-aware support. |
| `position_distribution_basis` | Must distinguish NODI synthetic positions from COMSOL transport distributions. |
| `flow_profile_model` | Rectangular series is invalid for trapezoid unless guarded. |
| `flow_control_mode` | Fixed velocity, fixed Q, fixed pressure, or COMSOL descriptor context imply different sensitivities. |
| `viscosity_pa_s` / `temperature_K` | Transport/resistance scaling and calibration. |
| `diffusion_hindrance_model` | Must use trapezoid wall distance if enabled. |
| `trajectory_boundary_model` | Rectangle vs trapezoid reflection must be explicit. |
| `wall_distance_model` | Source of near-wall metrics and selected-annulus bins. |
| `n_seeds`, `n_events`, `bin_policy` | Needed for reproducible PRS diagnostics. |

### 3.4 Interface and claim-guard parameters

| Field | Required rule |
| --- | --- |
| `source_geometry_descriptor_id` | Required for COMSOL-derived descriptor rows. |
| `source_geometry_descriptor_sha` | Required; mismatch is hard fail. |
| `source_gate_context_id` | Gate2C/Gate2D/Gate7 context row id if used. |
| `not_true_W_eff` | Must be true for EAS surrogate rows. |
| `not_measured_geometry` | Must be true unless actual profile measurement is loaded and validated. |
| `not_optical_solver_output` | Must be true unless a solver artifact exists. |
| `not_comsol_transport_distribution` | Must stay true for synthetic NODI PRS bins. |
| `not_qch_weighted` | Must stay true until explicit q_ch sidecar authorization. |
| `not_yield` | Must stay true. |
| `not_winner` | Must stay true. |
| `not_detection_probability` | Must stay true. |
| `not_production_or_runtime_config` | Must stay true for review artifacts. |
| `claim_boundary` | Must use exact boundary labels, e.g. `context-only`, `surrogate_sensitivity_only`, `descriptor_only`. |

### 3.5 PRS/EAS sidewall v2 minimum schema

Shared PRS/EAS fields:

```text
artifact_id
artifact_version
roadmap_status
claim_boundary
not_accepted_for_formula_use
not_accepted_for_runtime_config
not_accepted_for_production
route_id_nodi
source_geometry_descriptor_id
source_geometry_descriptor_sha
source_gate_context_id
geometry_profile_source
geometry_profile_sha256
geometry_claim_level
metrology_status
channel_cross_section_model
cross_section_geometry_version
geometry_runtime_binding_version
geometry_propagation_status
geometry_not_propagated_reasons
sidewall_angle_convention
sidewall_deg_comsol
sidewall_taper_angle_deg_nodi
angle_conversion_formula_id
W_top_nm
W_top_semantics
runtime_top_aperture_nm
depth_nm
W_bottom_unclipped_nm
W_bottom_runtime_clipped_nm
closure_depth_nm
closure_status
closure_policy
runtime_guard_status
particle_diameter_nm
particle_radius_nm
particle_support_model
particle_center_support_status
center_accessible_area_fraction
observation_signature
cache_geometry_match_status
```

PRS-only minimum fields:

```text
position_distribution_basis
sampler_geometry_model
sampler_support_model
coordinate_basis
coordinate_conversion_formula_id
x_nm
u_nm
z_nm
x_left_nm
x_right_nm
x_center_nm
local_width_nm
x_local_norm
u_norm
d_top_nm
d_bottom_nm
d_side_left_nm
d_side_right_nm
d_nearest_wall_nm
nearest_wall_id
surface_gap_for_particle_nm
bin_id
bin_basis
bin_accessible
bin_accessible_area_fraction
bin_particle_center_support_status
blocked_reason
sparse_reason
neighbor_fill_used
```

EAS-only minimum fields:

```text
eas_mode
aperture_surrogate_basis
aperture_surrogate_claim_level
W_eff_optical_surrogate_nm
W_eff_transport_surrogate_nm
W_eff_accessible_surrogate_nm
W_bottom_conservative_nm
top_bottom_average_heuristic_nm
center_accessible_aperture_surrogate_nm
min_aperture_conservative_nm
not_true_W_eff
not_measured_geometry
not_optical_solver_output
optical_solver_triggered
optical_solver_trigger_reason
optical_solver_trigger_is_result
```

Coordinate convention:

```text
roadmap equations: u in [0, H], measured downward from the top wall
existing NODI runtime often uses centered z
required conversion when centered z is used: u = z + H/2
coordinate_conversion_formula_id = centered_z_to_u_from_top_v1
```

## 4. NODI implementation roadmap

### G0 - Boundary, vocabulary, and invariants

Goal: prevent semantic drift before code changes.

Actions:

1. Add a sidewall-angle vocabulary contract:
   - COMSOL angle: `sidewall_deg_comsol`, from horizontal/substrate, `90 deg` vertical.
   - NODI angle: `sidewall_taper_angle_deg_nodi`, from vertical.
   - Conversion formula id: `sidewall_from_horizontal_to_taper_from_vertical_v1`.
2. Add explicit width terms:
   - `W_top_nm`
   - `W_top_semantics`
   - `runtime_top_aperture_nm`
   - `W_bottom_unclipped_nm`
   - `W_bottom_runtime_clipped_nm`
   - `W_mid_nm`
   - `W_eff_accessible_nm`
   - `W_eff_transport_surrogate_nm`
   - `W_eff_optical_surrogate_nm`
3. Add claim labels:
   - `descriptor_only`
   - `surrogate_sensitivity_only`
   - `context-only`
   - `accepted_context_only_artifact_level_ledger`
   - `not accepted for grain-level ingestion`
   - `not accepted for formula use`
   - `not accepted for runtime config`
   - `not accepted for production`
   - `not grain-level ingestion`
   - `solver_required`
   - `blocked`
4. Add hard no-promotion rules:
   - no `JRC`
   - no `q_ch*eta`
   - no `q_ch*chi*eta`
   - no `chi_selected`
   - no `route_score`
   - no `winner`
   - no `yield`
   - no `detection_probability`
   - no `wet pass probability`
   - no `clogging rate`
   - no fabrication release
   - no production/runtime ingestion
5. Add a sidewall artifact column blacklist:
   - no bare `W_eff`
   - no `score`
   - no `route_score`
   - no `rank_under_surrogate`
   - no `winner`
   - no `chi_selected`
   - no `JRC`
   - no `q_ch`
   - no `q_ch_eta`
   - no `q_ch_chi_eta`
   - no `yield`
   - no `detection_probability`
   - no `wet_pass_probability`
   - no `clogging_rate`
   - no `time_to_clog`
   - no `recovery`

Allowed replacements must carry claim qualifiers, for example `W_eff_optical_surrogate_nm`, `W_eff_transport_surrogate_nm`, `static_throat_margin_band`, `near_wall_exposure_proxy_band`, `diagnostic_sensitivity_metric`, and the relevant `not_*` flags.

Acceptance checks:

- `sidewall_deg_comsol=85` converts to `sidewall_taper_angle_deg_nodi=5`.
- A row with `sidewall_taper_angle_deg_nodi=85` is rejected unless its convention explicitly says taper-from-vertical and geometry remains valid.
- Negative bottom widths are preserved in descriptor fields and never silently clipped without a runtime clip field and closure policy.
- A row with `W_top_semantics=mask_width` or `top_cd` cannot be runtime-bound unless `runtime_top_aperture_nm` and source/bias metadata are present.
- `min_aperture_nm` or `min_aperture_descriptor_nm` cannot be used as EV passability evidence.

### G1 - Geometry descriptor v2

Goal: upgrade the descriptor layer without changing physical conclusions.

Target files:

- `nodi_simulator/data_objects.py`
- `nodi_simulator/channel_geometry_model.py`
- `nodi_simulator/nodi_comsol_next_artifacts.py`
- new or existing validator modules under `tools/audits/`

Actions:

1. Define a geometry profile object or schema:
   - rectangle
   - trapezoid parameterized by top width, depth, and sidewall angle
   - rounded rectangle
   - measured profile lookup
2. Store both formula and source:
   - `formula_id`
   - `angle_convention`
   - `source_descriptor_id`
   - `source_sha256`
3. Preserve unclipped values:
   - bottom width can be negative in descriptor space.
   - runtime may block or closure-clamp, but cannot pretend the geometry is open.
4. Split top-width semantics:
   - `mask_top_width_nm` is lithography or design context only.
   - `top_down_cd_nm`, if later added, supports only a top-CD prior.
   - `runtime_top_aperture_nm` is required before runtime binding.
   - `W_top_semantics` must declare `runtime_top_aperture`, `mask_width`, `top_cd`, `post_bias_top_cd`, or `comsol_descriptor`.
5. Add field evidence rows:
   - one row per field, with source path/hash and claim level.
6. Emit `geometry_profile_descriptor_v2` artifacts:
   - `NODI_GEOMETRY_PROFILE_DESCRIPTOR_V2.csv`
   - `NODI_GEOMETRY_FIELD_EVIDENCE_V2.csv`
   - `NODI_GEOMETRY_TO_RUNTIME_BINDING_MANIFEST.json`

Acceptance checks:

- Formula reproduction against COMSOL descriptor examples.
- Hash mismatch fails.
- Missing angle convention fails.
- COMSOL/NODI angle fields whose sum is not `90 deg` within tolerance fail.
- Descriptor emission fails if bottom width is clipped before `W_bottom_unclipped_nm` is emitted.
- Missing closure policy for nonpositive bottom width fails.
- `closure_status=open` fails when `W_bottom_unclipped_nm <= 0`.
- Runtime binding fails if `W_top_nm` has only mask/top-CD semantics.
- Descriptor rows cannot claim measured geometry without a validated measurement profile.

### G2 - Geometry-aware accessible region and sampling

Goal: propagate geometry into particle center accessibility and initial position.

Target files:

- `nodi_simulator/utils.py`
- `nodi_simulator/trajectory.py`
- `nodi_simulator/parameter_sweep.py`
- possible new module: `nodi_simulator/cross_section_geometry.py`

Actions:

1. Introduce cross-section primitives:
   - `width_at_depth(u)`
   - `x_left(u)`
   - `x_right(u)`
   - `x_center(u)`
   - `bottom_width_unclipped()`
   - `closure_depth()`
   - `fluid_area()`
   - `center_accessible_width_at_depth(u, particle_radius)`
   - `distance_to_walls(x, u)`
   - `contains_particle_center(x, u, radius)`
2. Replace rectangle-only initial-position sampler with geometry-aware sampler when `channel_cross_section_model=trapezoid_tapered_sidewalls`.
3. Support at least:
   - uniform over center-accessible area;
   - bin-conditioned sampling for PRS;
   - explicit blocked-bin reporting for inaccessible bins.
4. Make `contains_particle_center(x, u, radius)` the single steric support oracle for sampler, PRS binning, blocked-bin logic, and particle-support diagnostics.
5. Keep flux-weighted sampling blocked or diagnostic-only until a trapezoid flow field exists.

Acceptance checks:

- All sampled points satisfy wall-normal steric exclusion.
- 220 nm and 300 nm particles are blocked or flagged when bottom throat is insufficient.
- Sparse/inaccessible bins are emitted as sparse/blocked, not filled by neighbor bins.
- Rectangle model reproduces current sampler behavior within expected stochastic tolerance.
- `channel_cross_section_model=trapezoid_tapered_sidewalls` without `cross_section_geometry_version` fails.
- A nominal `uniform_accessible_area` row fails if actual support is a rectangular box.
- A blocked bin fails if it contains a normal numeric response value or uses neighbor filling.
- Flux-weighted sampling under trapezoid fails unless a compatible trapezoid flow model is present.

### G3 - Trajectory boundaries and near-wall metrics

Goal: stop using rectangular gaps when the geometry is trapezoidal.

Target files:

- `nodi_simulator/trajectory.py`
- `nodi_simulator/electrokinetic_transport.py`
- `nodi_simulator/parameter_sweep.py`
- post-v2 physical ceiling diagnostics

Actions:

1. Implement trapezoid reflection:
   - sidewall reflection uses the sloped wall normal.
   - top/bottom reflection remains planar.
2. Implement geometry-aware `nearest_wall_distance`.
3. Rebase hindered diffusion and wall-risk diagnostics on `nearest_wall_distance`.
4. Rename or version selected-annulus metrics:
   - `selected_annulus_rectangular_v1`
   - `selected_annulus_trapezoid_wall_distance_v1`
5. Emit a propagation audit:
   - `NODI_TRANSPORT_TRAPEZOID_DIAGNOSTIC.csv`
   - `NODI_GEOMETRY_PROPAGATION_AUDIT.csv`

Acceptance checks:

- Changing `sidewall_deg_comsol` changes near-wall distributions, or the artifact explicitly says `geometry_not_propagated_to_near_wall_metrics`.
- Rectangle and trapezoid selected-annulus metrics are never mixed under the same field name.
- Mutation tests prove angle/depth changes alter trajectory boundary behavior.
- Rectangular reflection or rectangular clamp under active trapezoid geometry is a hard fail for sidewall-aware runtime rows.
- `d_nearest_wall` is a geometry primitive, not a validated hindered-diffusion, adhesion, wet-pass, clogging, or recovery model.
- Hindered diffusion under trapezoid is allowed only as `surrogate_sensitivity_only`.
- `geometry_not_propagated_*` flags are allowed for audit rows, not for accepted sidewall-aware PRS/EAS pilot rows.
- Corner, multi-wall, roughness, charge, residue, lip, and adhesion regimes remain `solver_required` or experiment-gated.

### G4 - Transport and residence-time sensitivity

Goal: make hydrodynamic effects explicit, even if only diagnostic at first.

Target files:

- `nodi_simulator/fluidic_resistance.py`
- `nodi_simulator/electrokinetic_transport.py`
- transport/residence diagnostics under `results/post_v2_physical_ceiling`

Actions:

1. Add `flow_profile_model` guard:
   - `plug`: allowed as rough diagnostic.
   - `parabolic_rect` / `rect_series`: invalid for trapezoid unless explicitly rectangular.
   - `trapezoid_area_scaled_surrogate`: diagnostic only.
   - `trapezoid_cross_section_solver`: future validated solver.
   - `comsol_context_descriptor`: context-only, not q_ch.
2. Add hydraulic diagnostic fields:
   - `area_ratio_vs_rectangle`
   - `hydraulic_diameter_ratio_vs_rectangle`
   - `bottom_throat_ratio`
   - `closure_status`
   - `runtime_guard_status`
   - `flow_model_claim_level`
   - `not_qch_weighted=true`
3. Keep fixed-velocity and fixed-pressure interpretations separate.
   - At fixed mean velocity, geometry mainly changes spatial exposure and optical sampling.
   - At fixed pressure, geometry changes Q/residence strongly.
   - At COMSOL context, do not call the field q_ch unless authorized.

Acceptance checks:

- Rectangular duct series cannot run under trapezoid geometry without an explicit compatibility flag.
- Fixed-pressure and fixed-velocity diagnostics cannot share one unlabeled output column.
- COMSOL Q/proxy fields cannot be imported as formal q_ch.
- Any `rect_series` or `parabolic_rect` use under trapezoid is hard-invalid unless the row is explicitly rectangular or a non-propagated audit row.
- A field named `q_ch`, `flow_rate`, or `Q` cannot appear in sidewall PRS/EAS artifacts unless a future formal q_ch sidecar gate explicitly authorizes it.

### G5 - Position response surface v2

Goal: measure NODI optical response under geometry-aware initial-position support.

Starting route set:

- `404/W500/D900`
- `404/W500/D1200`
- `660/W800/D900`
- `660/W800/D1200`
- diagnostic: `404/W600/D900`
- trap/negative-control style: `660/W500/D1500`

Recommended sidewall scan:

- Focus: `sidewall_deg_comsol = 89, 87, 85, 83, 80`
- Stress: `70`
- Vertical control: `90`, only if descriptor formula and runtime branch support it
- Depth focus: `D900`, `D1200`
- Optional process-window context: exact Stage119 sidewall/depth rows as descriptor context, not automatic NODI accepted rows

Position bases:

- `edge_norm_1d_rectangular_v1` remains historical.
- `edge_norm_1d_trapezoid_wall_distance_v1` bins by nearest-wall distance.
- `xz_norm_2d_trapezoid_local_width_v1` uses local half-width normalization at depth.
- `wall_distance_1d_v1` is preferred for comparing near-wall effects across angles.

Actions:

1. Emit PRS v2 schema with geometry fields.
2. Add bin support fields:
   - `cross_section_geometry_version`
   - `position_distribution_basis`
   - `sampler_geometry_model`
   - `particle_radius_nm`
   - `coordinate_basis`
   - `coordinate_conversion_formula_id`
   - `x_nm`
   - `u_nm`
   - `z_nm`
   - `x_left_nm`
   - `x_right_nm`
   - `x_center_nm`
   - `local_width_nm`
   - `x_local_norm`
   - `u_norm`
   - `d_top_nm`
   - `d_bottom_nm`
   - `d_side_left_nm`
   - `d_side_right_nm`
   - `d_nearest_wall_nm`
   - `nearest_wall_id`
   - `surface_gap_for_particle_nm`
   - `bin_accessible`
   - `bin_accessible_area_fraction`
   - `bin_particle_center_support_status`
   - `blocked_reason`
   - `sparse_reason`
   - `neighbor_fill_used=false`
3. Keep PRS semantics conditional:
   - NODI synthetic initial position only.
   - not COMSOL transport distribution.
   - not q_ch weighted.
   - not yield.
   - not detection probability.

Acceptance checks:

- No neighbor filling of inaccessible bins.
- No direct mapping from edge4 to edge20 unless an explicit aggregation contract exists.
- No D900-to-D1200 borrowing.
- No 220 nm automatic admission where steric support fails.
- A sidewall-aware PRS row fails if particle support is tested only against `W_top`, average width, clipped bottom width, or rectangular half-spans.
- A COMSOL TPD/proxy/context row cannot be accepted as an exact PRS grain.

### G6 - Effective aperture and optical diagnostic v2

Goal: distinguish geometry aperture sensitivity from true optical solving.

Target artifacts:

- `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY_V2.csv`
- `NODI_REFERENCE_TRAPEZOID_OPTICAL_DIAGNOSTIC.csv`
- `NODI_OPTICAL_SOLVER_TRIGGER_REGISTER.csv`

Actions:

1. Keep EAS modes explicit:
   - `nominal_width`
   - `W_bottom_conservative`
   - `min_aperture_conservative`
   - `top_bottom_average_heuristic`
   - `center_accessible_aperture_surrogate`
2. Add EAS v2 fields:
   - `eas_mode`
   - `aperture_surrogate_basis`
   - `aperture_surrogate_claim_level=surrogate_sensitivity_only`
   - `W_eff_optical_surrogate_nm`
   - `W_eff_transport_surrogate_nm`
   - `W_eff_accessible_surrogate_nm`
   - `W_bottom_conservative_nm`
   - `top_bottom_average_heuristic_nm`
   - `center_accessible_aperture_surrogate_nm`
   - `min_aperture_conservative_nm`
   - `optical_solver_triggered`
   - `optical_solver_trigger_reason`
   - `optical_solver_trigger_is_result=false`
3. Add trigger reasons:
   - nonpositive or near-closed aperture;
   - response changes beyond a predeclared sensitivity threshold;
   - reference-too-weak ambiguity;
   - candidate-family ordering changes;
   - edge/near-wall bins dominate response change;
   - measured profile exists but no optical solver exists.
4. Keep no-claim flags:
   - `not_true_W_eff=true`
   - `not_measured_geometry=true` unless validated measured profile
   - `not_optical_solver_output=true`
   - `not_fabrication_release=true`
   - `not_yield=true`
   - `not_winner=true`

Acceptance checks:

- A solver trigger is not a solver result.
- `W_eff_optical_surrogate_nm` and `W_eff_transport_surrogate_nm` cannot be collapsed into one field.
- EAS cannot write route winners.
- A bare `W_eff` column fails schema validation.
- `rank_under_surrogate`, `score`, or `route_score` fails schema validation in sidewall EAS/PRS artifacts.

### G7 - COMSOL context binding without claim promotion

Goal: allow COMSOL sidewall/depth evidence to inform NODI sensitivity planning while preserving grain and claim boundaries.

Allowed inputs:

- Stage119 sidewall/depth matrix as process-window context.
- Stage18 nano sidewall sensitivity as historical/planning context.
- Gate2C schema alignment as compatibility evidence.
- Gate2D reduced-scope `W800/D900/300 nm` aggregate-proxy rows as accepted only for a `context-only` artifact-level ledger, not accepted for grain-level ingestion, formula use, runtime config, production, or route conclusion.
- Wall-tau analytic proxy only as descriptor/watch context, not wet performance.

Blocked promotions:

- `velocity_weighted` or `residence_time_weighted` cannot become NODI route weighting.
- COMSOL Q/proxy cannot become q_ch without a formal sidecar and authorization.
- TPD proxy bins cannot become exact PRS grain rows without exact route/view/diameter/bin binding.
- Context rows cannot become formula/JRC/chi_selected/route_score/winner/yield/detection_probability.

Acceptance checks:

- Every COMSOL-derived NODI row carries source id, source sha, context gate id, and claim boundary.
- Grain mismatches remain visible.
- Accepted-row counts do not silently expand.
- `velocity_weighted` and `residence_time_weighted` remain TPD proxy aggregation descriptors only.
- Gate2D `W800/D900/300 nm` aggregate proxy rows cannot expand beyond the exactly bounded context-only ledger without a new NODI gate.
- Edge4-to-edge20 grouping remains review-only until a dedicated NODI policy approves direct PRS-bin use.

### G8 - Observation signature, cache, and manifest hardening

Goal: prevent stale rectangular runs from being reused as sidewall-aware runs.

Actions:

1. Add geometry profile identity to observation signature:
   - cross-section model
   - angle convention
   - sidewall angle
   - top/bottom width
   - `mask_top_width_nm`, `top_cd_bias_nm`, and `runtime_top_aperture_nm` when present
   - depth
   - closure status/policy
   - runtime guard status
   - sampler version
   - wall-distance model
   - flow profile model
   - reference geometry mode
   - source descriptor hash
   - `geometry_profile_sha256`
   - `cross_section_geometry_version`
   - `W_top_semantics`
   - `runtime_top_aperture_nm`
   - `W_bottom_unclipped_nm`
   - `particle_radius_nm`
   - `center_accessible_support_model`
   - `sampler_geometry_model`
   - `trajectory_boundary_model`
2. Add manifest fields:
   - `geometry_profile_descriptor_version`
   - `geometry_runtime_binding_version`
   - `geometry_propagation_status`
   - `geometry_not_propagated_reasons`
3. Add stale-cache checks:
   - angle changed but signature unchanged: hard fail.
   - descriptor hash changed but manifest unchanged: hard fail.
   - runtime says trapezoid but sampler says rectangular: hard fail unless explicitly diagnostic with `not_propagated`.
   - particle radius changed but center-accessible support signature unchanged: hard fail.
   - closure policy changed but cache key unchanged: hard fail.
   - reference spatial mode changed between rectangle, effective-aperture surrogate, and trapezoid but cache key unchanged: hard fail.
   - old rectangular cache satisfies a trapezoid request: hard fail.

Acceptance checks:

- Mutation tests catch sidewall/depth changes.
- Old rectangular cache cannot satisfy trapezoid request.
- Manifests and CSV row counts are consistent.

### G9 - Experimental validation path

Goal: define what is needed to move beyond parameterized surrogate.

Minimum measurements:

- cross-section SEM or FIB-SEM sidewall angle;
- SEM/profilometry nano depth;
- top CD and, ideally, bottom throat or profile reconstruction;
- pressure-flow curve;
- tracer or particle flow map;
- blank-channel optical reference calibration;
- roughness/etch texture characterization if roughness is varied;
- EV size distribution via NTA/TRPS/AF4 or equivalent;
- adsorption/QC assay if wall-risk claims are later considered.

Rules:

- Top-down CD alone supports a top-CD-informed prior, not bottom width, sidewall angle, local throat, or EV passability.
- `measured_profile_lookup` is not measured geometry unless the profile is loaded, hashed, validated, and propagated.
- If measured geometry falls outside the COMSOL/NODI grid, mark `geometry_outside_model_domain`; do not silently extrapolate.

## 5. Suggested first implementation package

### Package A - Review-safe schema and descriptor work

Scope:

- No compute.
- No COMSOL launch.
- No NODI production sweep.
- Only schema, descriptor, validator, and manifest work.

Deliverables:

- `NODI_GEOMETRY_PROFILE_DESCRIPTOR_V2.csv`
- `NODI_GEOMETRY_FIELD_EVIDENCE_V2.csv`
- `NODI_GEOMETRY_TO_RUNTIME_BINDING_MANIFEST.json`
- `NODI_GEOMETRY_DESCRIPTOR_V2_VALIDATION_REPORT.md`

Tests:

- angle conversion examples;
- formula examples;
- negative bottom-width preservation;
- `D_inscribed_nm`, `W_bottom_unclipped_nm`, `W_bottom_runtime_clipped_nm`, and `min_aperture_descriptor_nm` role separation;
- `W_top_semantics` runtime-binding failure when only mask/top-CD context is present;
- missing source hash failure;
- bare forbidden-column scanner.

Go/no-go:

- Package A can emit only `descriptor_only`, `roadmap_only`, and validation-report artifacts.
- Package A cannot emit PRS/EAS sensitivity rows, trajectory claims, flow claims, optical claims, or any runtime/production artifact.
- Package A must pass before Package B can claim a sidewall-aware runtime binding.

### Package B - Runtime geometry primitives

Scope:

- Add geometry primitives and sampler support.
- No optical solver.
- No COMSOL launch.
- No route conclusion.

Deliverables:

- `cross_section_geometry.py` or equivalent module.
- geometry-aware initial-position sampler.
- geometry-aware accessible-area diagnostics.
- sampler mutation tests.

Tests:

- sampled points remain inside trapezoid support.
- rectangle compatibility.
- 220/300 nm steric block cases.
- inaccessible bin handling.
- `contains_particle_center(x, u, radius)` is the single support oracle.
- `uniform_accessible_area` is rejected if implemented by rectangular half-spans.
- blocked bins are never neighbor-filled.

Go/no-go:

- Package B can emit geometry primitives, sampler support audits, and center-accessible descriptors.
- Package B cannot enable flux-weighted sampling unless a compatible trapezoid flow field exists.
- Package B must pass before Package D can emit sidewall-aware PRS/EAS pilot rows.

### Package C - Trajectory and near-wall propagation

Scope:

- Propagate trapezoid geometry into trajectory boundary and near-wall diagnostics.
- Keep transport model diagnostic-only unless validated.

Deliverables:

- trapezoid reflection.
- geometry-aware wall distance.
- `NODI_GEOMETRY_PROPAGATION_AUDIT.csv`
- `NODI_TRANSPORT_TRAPEZOID_DIAGNOSTIC.csv`

Tests:

- angle mutation changes wall-distance distribution.
- selected-annulus v1/v2 cannot be mixed.
- rectangular series is blocked for trapezoid flow unless explicitly labeled.
- rectangular reflection/clamp is rejected for sidewall-aware runtime rows.
- `d_nearest_wall` and hindered diffusion stay `surrogate_sensitivity_only`.
- old selected-annulus field names cannot carry trapezoid wall-distance semantics.

Go/no-go:

- Under the current Gate23 no-auth state, Package C is blocked/fail-closed. It cannot be treated as passed by a row-local id/hash fixture.
- Under the current Gate24 no-auth ledger, the future authorization phrase is recorded for auditability but does not authorize Package C physics, proof-registry update, runtime configuration, NODI recomputation, COMSOL launch, `.mph` load, or sidewall PRS/EAS numeric output.
- Gate25 prepares the Package C physics design review and external prompt only. It does not implement sloped-wall reflection, hindered diffusion, trapezoid flow, electrokinetic grids, optical/reference solvers, or any PRS/EAS numeric output.
- Gate26 integrates external review feedback as a design-constraints ledger only. It records `skorokhod_normal_reflection_convex_offset_trapezoid_v1` as the future Brownian target, requires active-set corner handling, no-boundary-atom checks, pure-Brownian uniform-equilibrium checks, dt-halving convergence, rectangle-limit and angle/depth mutation tests, and requires any projection boundary to stay labeled `sidewall_projection_boundary_surrogate_not_specular_reflection`.
- Gate27 converts Gate26 into an implementation-design preflight only: future write scopes, 52 proof-artifact contract fields, and fail-closed triggers are enumerated, but no Package C proof artifact is registered and no pass/runtime/numeric-output permission is granted.
- After explicit user authorization for Package C implementation code and unit tests, a finite-step Skorokhod/normal-reflection implementation candidate is present for trapezoid diffusive plug-flow trajectories. The geometry primitive can emit active wall ids, reflection iteration count, total reflection displacement, and convergence status for one finite-step reflection update; audit-only trajectory diagnostics also expose the Brownian target model, numerical scheme, no-specular/no-hindered guards, projection-surrogate flag, reflection update rule id, and telemetry reporting scope. The observation signature includes these Brownian boundary/telemetry fields. Current tests cover single-wall folded-normal behavior, no projection boundary atom, corner active-set convergence, pure-Brownian accessible-area moment preservation, u-slice `x_local_norm` uniformity/symmetry, dt-halving one-wall wall-distance convergence, angle/depth reflected wall-distance mutation, and rectangle-limit equivalence. This is still not a Package C proof/pass registration and still does not authorize hindered diffusion, trapezoid Poiseuille, electrokinetic grids, optical/reference solver output, sidewall PRS/EAS numeric output, route/yield/detection claims, NODI recomputation, COMSOL launch, or `.mph` load.
- Gate28 packages the current Package C implementation candidate for external proof-review only. It locks sources, stores a JSON evidence ledger for 6 passing no-runtime evidence commands, writes a self-contained external review prompt, and keeps proof registration/runtime/numeric/COMSOL/`.mph` permissions false.
- Gate29 integrates the external proof-review verdict as `READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY`: this allows the proof-registration review track to continue, but still does not authorize Package C proof/pass registration. Future proof registration must satisfy Gate29 hard gates for dt convergence, equilibrium uniformity, no-boundary-atom behavior, corner active-set behavior, mutation/limit tests, evidence hashes, source/environment/reviewer locks, and all no-claim flags.
- A future explicit Package C gate may emit trajectory-boundary propagation audits, wall-distance diagnostics, and near-wall surrogate diagnostics only after a real registered proof artifact, an external/independent physics review, and an explicit execution authorization path exist.
- Package C cannot emit clogging rate, adhesion probability, wet pass probability, recovery, or calibrated event probabilities.
- Package C must pass before Package D can use trajectory, near-wall, hindered-diffusion, wall-distance-bin, or selected-annulus metrics.

### Package D - PRS/EAS sidewall sensitivity pilot

Scope:

- Generate sidewall-aware PRS/EAS sensitivity artifacts under no-claim flags.
- Use exact route/view/depth/diameter/bin labels.
- Keep COMSOL rows as context only.
- This package is blocked until Package A and Package B pass.
- If it includes trajectory, near-wall, hindered-diffusion, or selected-annulus metrics, it is also blocked until Package C passes.

Deliverables:

- `NODI_POSITION_RESPONSE_SURFACE_V2_SIDEWALL_SENSITIVITY.csv`
- `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY_V2.csv`
- `NODI_OPTICAL_SOLVER_TRIGGER_REGISTER.csv`
- sidewall sensitivity report.

Tests:

- no forbidden fields;
- no q_ch weighting;
- no JRC;
- no chi_selected;
- no route_score;
- no winner;
- no yield;
- no detection_probability;
- no D900-to-D1200 borrowing;
- no edge4-to-edge20 direct mapping.
- no old rectangular cache reuse;
- no COMSOL context row promoted to exact PRS grain;
- no automatic 220/300 nm admission without exact steric support.

Preflight manifest:

```text
package_A_validation_status = pass
package_B_validation_status = pass
package_C_validation_status = pass | not_applicable_for_this_artifact
no_forbidden_claim_columns = pass
no_rectangular_cache_reuse = pass
no_comsol_context_grain_promotion = pass
no_edge4_to_edge20_direct_mapping = pass
no_D900_to_D1200_borrowing = pass
no_auto_220_300nm_admission = pass
```

## 6. Pilot matrix

### 6.1 Minimal NODI-side pilot

| Dimension | Values |
| --- | --- |
| Routes | `404/W500/D900`, `404/W500/D1200`, `660/W800/D900`, `660/W800/D1200` |
| Diagnostic route | `404/W600/D900` |
| Trap/stress route | `660/W500/D1500` |
| Sidewall angles | `90`, `89`, `87`, `85`, `83`, `80`, `70` deg COMSOL convention |
| Internal tapers | `0`, `1`, `3`, `5`, `7`, `10`, `20` deg NODI convention |
| Depths | `900`, `1200` nm for route focus; additional Stage119 depths only as context |
| Diameters | `40`, `60`, `100`, `150`, `220`, `230`, `240`, `250`, `260`, `270`, `280`, `290`, `300` nm |
| EAS modes | `nominal_width`, `W_bottom_conservative`, `min_aperture_conservative`, `top_bottom_average_heuristic`, `center_accessible_aperture_surrogate` |
| Position bases | rectangular historical, trapezoid local-width, wall-distance |

### 6.2 COMSOL context overlay

Use COMSOL sidewall/depth matrices as context overlays, not automatic NODI accepted rows:

- `85 deg / 0.9-1.2 um`: focus/process window.
- `85 deg / 1.2 um`: first-fabrication anchor with warning context.
- `83/85/87 deg`: local sidewall sensitivity context.
- `70/80/89 deg`: stress/open-window context.
- `geometry_closed` rows: blocked/closure-policy evidence, not failed runs.
- Gate2D `W800/D900/300 nm` rows: reduced-scope aggregate-proxy context only.

## 7. Validation gates

### Gate S0 - Schema and convention

Hard fails:

- missing angle convention;
- ambiguous `sidewall_deg`;
- COMSOL angle passed as NODI taper angle;
- COMSOL and NODI angle fields whose sum is not `90 deg` within tolerance;
- missing `W_top_semantics`;
- runtime binding from `mask_top_width_nm` or top-down CD without `runtime_top_aperture_nm` and source/bias metadata;
- missing source hash for COMSOL-derived descriptor;
- bottom width clipped without unclipped descriptor and closure policy.

### Gate S1 - Geometry formula and closure

Hard fails:

- formula mismatch for known examples;
- `W_bottom_unclipped_nm` missing;
- descriptor formula clips negative bottom width before descriptor emission;
- nonpositive bottom width treated as open;
- `W_bottom_runtime_clipped_nm` used without explicit `closure_policy`;
- closure-clamped row mixed into open-channel transport branch;
- `min_aperture_nm` or `min_aperture_descriptor_nm` negative values silently clipped in descriptor space;
- `min_aperture_nm` or `min_aperture_descriptor_nm` used as EV passability evidence.

### Gate S2 - Runtime propagation

Hard fails:

- trapezoid descriptor active but sampler remains rectangle without `not_propagated`;
- trapezoid runtime active without `cross_section_geometry_version`;
- sidewall-aware PRS row generated without `contains_particle_center(x, u, radius)` support validation;
- `uniform_accessible_area` implemented by rectangular half-spans;
- rectangular reflection/clamp used in sidewall-aware trajectory rows;
- trapezoid wall distance computed from rectangular `half_w` / `half_h` gaps;
- sidewall angle mutation does not alter accessible area, wall distance, or propagation audit;
- selected-annulus metrics are reused under old rectangular field names;
- flux-weighted sampling enabled without a compatible flow model;
- `geometry_not_propagated_*` audit flags are treated as permission for accepted sidewall-aware PRS/EAS rows.

### Gate S3 - Interface and claim boundary

Hard fails:

- `W_eff`, `score`, `rank_under_surrogate`, `JRC`, `chi_selected`, `route_score`, `winner`, `q_ch`, `q_ch_eta`, `q_ch_chi_eta`, `yield`, `detection_probability`, `wet pass probability`, `wet_pass_probability`, `clogging rate`, `clogging_rate`, `time_to_clog`, `recovery`, or fabrication-release claims appear.
- `not_true_W_eff`, `not_measured_geometry`, `not_optical_solver_output`, `not_qch_weighted`, `not_yield`, or `not_detection_probability` flags are missing from sidewall EAS/PRS artifacts.
- `velocity_weighted` or `residence_time_weighted` is interpreted as NODI/q_ch weighting.
- COMSOL TPD/proxy rows are ingested as exact PRS production grains.
- D900 rows are reused for D1200.
- 220 nm rows are auto-admitted without exact support.
- edge4 rows are treated as direct edge20 PRS bins.
- accepted-row counts silently expand beyond the bounded context-only ledger.

### Gate S4 - Signature and cache

Hard fails:

- `sidewall_deg_comsol` changes but observation signature does not.
- `sidewall_taper_angle_deg_nodi` changes but observation signature does not.
- `W_top_semantics` or `runtime_top_aperture_nm` changes but observation signature does not.
- `W_bottom_unclipped_nm` changes but observation signature does not.
- `closure_status` or `closure_policy` changes but observation signature does not.
- `particle_radius_nm` changes but center-accessible support signature does not.
- `sampler_geometry_model`, `wall_distance_model`, `trajectory_boundary_model`, `flow_profile_model`, or `reference_spatial_mode` changes but cache key does not.
- sidewall/depth/profile hash changes but observation signature does not.
- old rectangular cache is reused for trapezoid geometry.
- manifest row counts or SHA values do not match generated artifacts.

### Gate S5 - Solver/metrology readiness

Hard fails:

- measured geometry claim without loaded and validated profile;
- optical solver claim without optical solver artifact;
- optical solver trigger treated as optical solver result;
- calibrated claim without measurement package;
- geometry outside model domain silently extrapolated.

## 8. Review checklist before any compute rerun

- Angle convention table is present and tested.
- COMSOL `85 deg` maps to NODI taper `5 deg`.
- `W_top`, `W_bottom_unclipped`, `W_bottom_runtime_clipped`, and `min_aperture` are distinct fields.
- `W_top_semantics` and `runtime_top_aperture_nm` are present before runtime binding.
- `min_aperture_descriptor_nm` is not used as EV passability evidence.
- Negative bottom widths are preserved in descriptor rows.
- `geometry_closed` and `solver_guard` are not treated as ordinary pass/fail.
- Particle center-accessible region is radius-aware.
- `contains_particle_center(x, u, radius)` is the steric support oracle for sampler and PRS bins.
- Near-wall distance uses trapezoid wall normals.
- `d_nearest_wall` is not promoted to wet pass, adhesion, clogging, or recovery evidence.
- Flow profile is compatible with geometry or explicitly diagnostic-only.
- PRS bins state their geometry basis.
- No neighbor filling of blocked bins.
- Observation signature contains geometry model and source hash.
- Observation signature contains sidewall angle, `W_top_semantics`, unclipped bottom width, closure policy, particle radius, sampler model, wall-distance model, trajectory boundary model, flow model, reference spatial mode, and geometry profile hash.
- All COMSOL context rows carry source id, source sha, and claim boundary.
- No forbidden claim terms are emitted.
- No `chi_selected` or `route_score` terms are emitted as selected/scored design outputs.
- Gate2 accepted-row counts do not silently expand.
- Package D preflight manifest passes before any PRS/EAS sidewall sensitivity pilot.
- Tests include mutation cases for sidewall angle and depth.

## 9. Current Gate30/31 status

Gate30/31 now adds a GitHub-visible Package C proof-metrics candidate:

- Artifact id: `GATE30_31_PACKAGE_C_REFLECTION_PROOF_METRICS_CANDIDATE_20260630`.
- Disposition: `NODI_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: finite-step active-set normal-reflection metrics candidate for the trapezoid particle-center support domain.
- Parameter grid: sidewall angles `90, 89, 87, 85, 83, 80, 70 deg`; depths `900, 1200 nm`; particle radii `20, 30, 50, 75, 110, 150 nm`; dt grid `5e-5, 2.5e-5, 1.25e-5 s`.
- Generated evidence: raw metrics, summary metrics, parameter matrix, RNG seed matrix, candidate evidence map, 52-field proof-candidate manifest, no-proof firewall, source lock, and external review prompt.
- Current candidate checks: support invariance, no-boundary-atom, equilibrium uniformity proxy, dt-halving, corner active-set, one-wall limit, rectangle limit, and angle/depth mutation are all `candidate_pass`.
- Current boundary: `candidate_only`; `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This Gate30/31 candidate is deliberately stronger than a design-only checklist, but it is still not a proof/pass registration. It is the evidence package that an external reviewer can inspect before any future, separate authorization supersedes the no-auth ledger.

## 10. Current Gate32 status

Gate32 packages the Gate30/31 candidate into a GitHub-visible external AI research/synthesis handoff:

- Disposition: `NODI_GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF_READY_NO_PROOF_REGISTRATION`.
- Scope: external research/synthesis prompt, review intake, GitHub path map, research agenda, authorization-supersession preflight, and no-proof firewall.
- GitHub path map rows: `15`, covering the prompt, Gate30/31 status, raw/summary metrics, candidate manifest, evidence map, firewall, parameter/seed matrices, geometry and trajectory source, builder/tests, roadmap, and audit packet.
- Research synthesis questions: `10`, covering reflected Brownian / Skorokhod foundations, finite-step algorithms, one-wall tests, equilibrium uniformity, boundary atom diagnostics, corner active-set behavior, dt-convergence thresholds, proof schema, blocked physics boundaries, and go-forward engineering route.
- Authorization-supersession preflight rows: `21`, including required external review verdict/hash, reviewed candidate hashes, reviewed commit sha, manual authorization record, proof-registry update plan, and all no-claim guards.
- Current boundary remains: `external_review_received=false`; `authorization_supersedes_no_auth_ledger=false`; `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

Gate32 is the correct packet to send to an external AI because it does not assume local file visibility, and it does not merely ask for another audit. It explicitly asks the external AI to search broader technical/literature sources, compare methods, propose thresholds and test matrices, identify claim-boundary risks, and return a route that should support several future gates. It still asks for one of three verdicts: `READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY`, `NEEDS_MORE_CANDIDATE_EVIDENCE`, or `BLOCKED_CLAIM_PROMOTION`.

## 11. Current Gate33-36 status

Gate33-36 absorbs the external AI research synthesis into a single combined authorization-design packet:

- Artifact id: `GATE33_36_PACKAGE_C_REFLECTION_PROOF_AUTHORIZATION_DESIGN_PACKET_20260630`.
- Disposition: `NODI_GATE33_36_SIDEWALL_PACKAGE_C_REFLECTION_PROOF_AUTHORIZATION_DESIGN_READY_NO_PROOF_REGISTRATION`.
- External verdict captured: `READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY`.
- Output status: `authorization_required_no_proof_registration`.
- Scope: source lock, evidence chain, external research capture, proof-metric hardening backlog, metric expansion spec, threshold matrix, authorization ledger placeholder, hard-fail checklist, review request, mutation results, self-review, no-proof firewall, status/report/manifest.
- Proof-hardening backlog rows: `10`, covering clean reviewed commit binding, exact/near-boundary atom split, raw histograms, ESS/autocorrelation, one-wall folded-normal tests, projection/rejection negative controls, worst-case dt refinement, corner heatmap, and line-broken review artifacts.
- Threshold matrix rows: `10`, including candidate `dt_halving_distribution_delta <= 0.10`, future proof hard line `<= 0.075`, candidate `equilibrium_uniformity_distance <= 0.06`, future proof hard line `<= 0.04`, exact atom separation, one-wall kernel distance, rectangle limit, corner active-set, corner pile-up, and mutation requirements.
- Authorization placeholder rows: `22`; hard-fail checklist rows: `14`; evidence chain rows: `9`; review request rows: `5`; mutation result rows: `9`; self-review rows: `5`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

Gate33-36 is intentionally a merged evidence railway rather than a sequence of small review pauses. It allows implementation to proceed toward proof-metric hardening while keeping proof registration, Package C pass, runtime ingestion, numeric PRS/EAS, COMSOL launch, `.mph` load, and all route/yield/detection/wet/fabrication/production claims fail-closed.

## 12. Current Gate37 status

Gate37 implements the first proof-metric hardening candidate block from the Gate33-36 backlog:

- Artifact id: `GATE37_PACKAGE_C_REFLECTION_METRIC_HARDENING_CANDIDATE_20260630`.
- Disposition: `NODI_GATE37_SIDEWALL_PACKAGE_C_REFLECTION_METRIC_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: exact/near-boundary atom split, reviewer-friendly raw histograms, ESS proxy rows, one-wall folded-normal positive control, projection/rejection negative controls, worst-case dt refinement rows, corner heatmap rows, source lock, no-proof firewall, status/report/manifest.
- Inherited Gate30/31 scenario rows: `216`.
- Boundary atom split rows: `198`; raw histogram rows: `396`; ESS proxy rows: `198`.
- One-wall suite rows: `18`; worst-case dt refinement rows: `10`; corner heatmap rows: `40`.
- `max_exact_boundary_atom_fraction=0.0`.
- `max_near_boundary_band_fraction=0.002604167`.
- `max_one_wall_positive_control_ks=0.019246436`.
- `projection_negative_control_status=expected_fail_observed`, with `max_projection_negative_control_exact_atom_fraction=0.495849609`.
- `max_wall_pileup_ratio=9.0`, which is a candidate-level warning for future near-wall/corner refinement and not proof evidence.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

Gate37 improves the evidence surface substantially: it shows that the current finite-step reflection candidate does not create exact boundary atoms under the tested split, and that the negative-control suite is strong enough to reject projection clamp. It also exposes a wall-pileup proxy risk that must be investigated before any proof-level claim. Therefore Gate37 is useful forward progress, but it still does not register proof/pass.

## 13. Current Gate38 status

Gate38 refines the Gate37 wall-pileup proxy warning with focused expanded sampling:

- Artifact id: `GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_CANDIDATE_20260701`.
- Disposition: `NODI_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Source warning: Gate37 `max_wall_pileup_ratio=9.0`.
- Scope: top `12` Gate37 wall-pileup rows, expanded to `8192` samples per row, with band counts, first/adjacent band fractions, Haldane-Anscombe ratio confidence intervals, sparse-proxy classification, source lock, no-proof firewall, status/report/manifest.
- Result: `algorithmic_pileup_signal_rows=0`.
- `sparse_gate37_proxy_artifact_rows=12`.
- `max_expanded_first_vs_adjacent_gap_band_smoothed_ratio=1.298850575`.
- `max_expanded_wall_pileup_ratio_ci95_low=1.011337147`.
- `max_expanded_wall_pileup_ratio_ci95_high=1.928677789`.
- Refinement status: `sparse_gate37_proxy_artifact_no_algorithmic_pileup_signal`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

Gate38 resolves the specific Gate37 `9.0` first-vs-adjacent gap-band smoothed proxy as a small-sample / empty-adjacent-bin artifact rather than an observed algorithmic reflection failure. This does not prove Package C; it only clears that localized candidate warning and improves the statistical diagnostic.

## 14. Current Package C metric-hardening consolidation status

Gate37 and Gate38 are now folded into a single Package C metric-hardening consolidation entrypoint:

- Artifact id: `PACKAGE_C_METRIC_HARDENING_CONSOLIDATION_20260701`.
- Disposition: `NODI_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: one evidence index, one proof-readiness criteria table, one no-proof firewall, one source lock, one manifest, and one human-readable report that consolidate Gate37 exact/near-boundary atom split, raw histograms, ESS proxy, one-wall positive/negative controls, dt refinement, corner heatmap, and Gate38 expanded-sampling wall-pileup refinement.
- Evidence index rows: `10`; readiness criteria rows: `9`.
- Proof-readiness status: `not_ready_missing_timeseries_ess_clean_commit_and_authorization`.
- Gate37 `max_wall_pileup_ratio=9.0` is treated as superseded by Gate38 expanded-sampling diagnostics; `algorithmic_pileup_signal_rows=0`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This consolidation is the intended forward work style after the Gate37/38 review: use larger implementation/evidence blocks with a single review entrypoint, not a new small gate for every diagnostic. It keeps `ideal_rectangle` as a first-class path while preserving the sidewall/trapezoid analysis branch as schema-bound and cache-distinct.

## 15. Current Package C timeseries ESS candidate status

The first post-consolidation proof-gap hardening block adds long-run time-series evidence for the finite-step reflection candidate:

- Artifact id: `PACKAGE_C_TIMESERIES_ESS_CANDIDATE_20260701`.
- Disposition: `NODI_PACKAGE_C_TIMESERIES_ESS_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: six representative/stress scenarios, long-chain autocorrelation, ESS, retained-sample stationarity proxies, substep/fail policy candidate rows, source lock, no-proof firewall, status/report/manifest.
- Chain settings: `65536` steps per scenario, `8192` burn-in steps, stride `8`, retained samples per scenario `7168`.
- Output rows: scenario summary `6`, observable ESS `18`, autocorrelation `144`, substep policy `6`.
- Current results: `min_effective_sample_size=46.559312675`, `max_u_accessible_cdf_l1_to_uniform=0.284598214`, `max_x_local_norm_l1_to_uniform=0.108537946`, `support_violation_rows=0`, `nonconverged_reflection_rows=0`, `max_exact_boundary_atom_fraction_all_steps=0.0`.
- Substep guard rows: `substep_review_rows=6`; these are design guards only, not runtime policy.
- Candidate status: `candidate_artifact_complete_not_proof`; `stationarity_review_required=true`; `substep_policy_review_required=true`.
- Reviewed commit binding status: `pending_future_authorization_not_clean_head_bound`.
- Proof-readiness impact: `timeseries_ess_gap_reduced_but_not_proof_registered`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This block reduces the prior `timeseries_ess` gap from missing to candidate-evidenced, but it still does not register Package C proof/pass. Future proof registration would still need a reviewed clean commit binding, manual authorization ledger, proof-level thresholds, and independent review of the statistical method.

## 16. Current Package C substep/fail policy hardening status

The next post-consolidation block converts the timeseries substep review finding into proof/pass validator hard-fail requirements:

- Artifact id: `PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_20260701`.
- Disposition: `NODI_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: substep fail-policy rows, Package C proof/pass field requirements, source lock, no-proof firewall, status/report/manifest.
- Trigger metric: `brownian_rms_step_over_surface_gap_p05`.
- Trigger threshold: `1.0`.
- Policy rows: `6`; triggered rows: `6`.
- Max observed trigger value: `22.925543703`.
- Triggered scenario count: `6`; bound trigger count: `6`.
- Substep policy scope: `proof_guard_only_not_runtime_config`.
- Proof field requirement rows: `10`.
- Validator hardening status: `package_c_proof_pass_requires_substep_policy_fields`.
- Proof-readiness impact: `future_package_c_proof_pass_hard_fails_without_substep_policy_evidence`.
- GitHub visibility status: `local_worktree_pre_commit_urls_valid_after_publish`.
- Current candidate still has `substep_review_required_for_current_candidate=true`; this is a hardening signal, not runtime authorization.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

The contract validator now requires future `package_C_validation_status=pass` rows to include substep policy evidence, status, scope, trigger metric, trigger threshold, max observed trigger value, triggered scenario count, bound trigger count, closed review status, and a false runtime-policy authorization flag. Missing or inconsistent fields raise `SIDEWALL-D-PRECHECK-V03`.

## 17. Current Package C substep dt-refinement requirements status

The next block converts the substep-triggered scenarios into explicit dt/substep reduction requirements:

- Artifact id: `PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_20260701`.
- Disposition: `NODI_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: dt-refinement requirement rows, source lock, no-proof firewall, status/report/manifest.
- Trigger metric: `brownian_rms_step_over_surface_gap_p05`.
- Current dt: `2.5e-05 s`.
- Refinement rows: `6`.
- Min required substeps to meet threshold: `4`.
- Max required substeps to meet threshold: `526`.
- Min required dt to meet threshold: `4.75285171103e-08 s`.
- Max projected trigger value after required substeps: `0.999601207629`.
- Candidate status: `requirements_complete_not_runtime_policy_not_proof`.
- Proof-readiness impact: `substep_review_rows_now_have_explicit_dt_refinement_requirements`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This block is a policy-sizing artifact, not a runtime policy. It shows that the worst current candidate (`narrow_tail_theta70_D900_r150`) would require `526` substeps at the current `dt` to bring the rms-step/surface-gap p05 trigger below `1.0`; future proof/pass review should therefore treat sidewall runtime activation as expensive unless a smaller-dt/substep strategy is explicitly authorized and tested.

## 18. Current Package C proof-threshold table status

The next block makes candidate/proof thresholds and remaining proof gaps machine-readable:

- Artifact id: `PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701`.
- Disposition: `NODI_PACKAGE_C_PROOF_THRESHOLD_TABLE_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: threshold table rows, source lock, no-proof firewall, status/report/manifest.
- Threshold rows: `14`.
- Candidate-pass rows: `2`.
- Proof-gap rows: `0`.
- Proof-method gap rows: `0`.
- Proof-method-bound rows: `1`.
- Runtime-policy gap rows: `2`.
- Proof-threshold-met-not-registered rows: `9`.
- Threshold table status: `candidate_threshold_table_ready_not_proof_registered`.
- Proof-readiness impact: `numeric_and_method_candidate_lines_bound_to_authorization_and_runtime_policy_gaps`.
- Stationarity/ESS rows now use `PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT_20260701`: `min_effective_sample_size=32768.0`, `max_u_accessible_cdf_l1_to_uniform=0.0217651367188`, and `max_x_local_norm_l1_to_uniform=0.0203979492187`, all marked `candidate_and_proof_threshold_met_not_registered`.
- One-wall/wall-pileup rows now use `PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT_20260701`: `max_one_wall_positive_control_ks=0.005281493`, `max_expanded_wall_pileup_ratio=1.072659525`, and wall-pileup CI95 high `1.214998175`, all marked `candidate_and_proof_threshold_met_not_registered`.
- Near-boundary rows now use `PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_20260701`: the legacy sparse near-boundary row is retained as context, while `max_near_boundary_expected_band_z_abs=2.049081656` is marked `candidate_and_proof_method_bound_not_registered` against candidate line `<=3.0`.
- Runtime-policy gaps remain: `max_required_substeps_to_meet_threshold=526` and `max_projected_trigger_value_after_required_substeps=0.999601207629` require manual runtime-cost/substep-policy review before any runtime/substep policy.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This block is threshold planning evidence only. It does not register Package C proof/pass and does not make any runtime, PRS/EAS numeric, COMSOL, `.mph`, route, yield, detection, wet, fabrication, or production claim.

## 19. Current Package C proof-readiness index status

The next block consolidates the Package C metric-hardening state into a single machine-readable entrypoint:

- Artifact id: `PACKAGE_C_PROOF_READINESS_INDEX_20260701`.
- Disposition: `NODI_PACKAGE_C_PROOF_READINESS_INDEX_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: readiness index rows, open blocker rows, external-research question rows, source lock, no-proof firewall, status/report/manifest.
- Readiness index rows: `8`, covering metric-hardening consolidation, timeseries ESS, stationarity ensemble refinement, one-wall/wall-pileup refinement, near-boundary expected-band method, substep fail-policy hardening, substep dt-refinement requirements, and proof-threshold table.
- Open blocker rows: `4`: manual authorization ledger missing, clean reviewed commit binding pending, runtime-policy gaps present, and solver/wet claims still unauthorized.
- External research question rows: `4`: stationarity/ESS method review, near-boundary expected-band external review, one-wall/wall-pileup method binding, and substep runtime-cost strategy.
- Proof-readiness index status: `single_entrypoint_ready_not_proof_registered`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This block is the preferred entrypoint for future Package C review or external-AI research. External AI should use the listed research questions for broad method/literature work, not as a repetitive micro-review loop. The index still does not register Package C proof/pass and does not make any runtime, PRS/EAS numeric, COMSOL, `.mph`, route, yield, detection, wet, fabrication, or production claim.

## 20. Current Package C external-research prompt status

The next block turns the readiness index into a copyable external-AI prompt that is designed for one larger research pass rather than repeated micro-review:

- Artifact id: `PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_20260701`.
- Disposition: `NODI_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_READY_NO_PROOF_REGISTRATION`.
- Scope: copyable prompt, context rows, research-question rows, blocker rows, source lock, no-proof firewall, status/report/manifest.
- Context rows: `6`, covering the GitHub-visible entrypoint, artifact roles, stationarity method context, one-wall/wall-pileup refinement context, near-boundary expected-band method, and substep runtime cost.
- Research question rows: `4`: stationarity/ESS method review, near-boundary expected-band external review, one-wall/wall-pileup method binding, and substep runtime-cost strategy.
- Blocker rows: `4`: manual authorization ledger missing, clean reviewed commit binding pending, runtime-policy gaps present, and solver/wet claims still unauthorized.
- Prompt status: `copyable_external_research_prompt_ready`.
- GitHub visibility status: `local_worktree_pre_commit_urls_valid_after_publish`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This block is an external research handoff, not a proof/pass registration. Its prompt explicitly tells external AI that it can only inspect GitHub-visible files, must not assume local Codex/COMSOL/`.mph`/uncommitted artifacts, and should answer the four method/literature questions with sources, thresholds, and next evidence priorities. It does not authorize Package C pass, runtime, sidewall PRS/EAS numeric output, NODI recomputation, COMSOL launch, `.mph` load, route/yield/detection/wet/fabrication/production claims, or true `W_eff`.

## 21. Current Package C stationarity ensemble refinement status

The next local proof-gap reduction block adds independent-ensemble transition-invariance evidence for the finite-step reflection candidate:

- Artifact id: `PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT_20260701`.
- Disposition: `NODI_PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: independent uniform-support ensemble samples, initial/final histograms, confidence intervals, source lock, no-proof firewall, status/report/manifest.
- Scenario-seed rows: `18`, covering six representative/stress scenarios and three seeds per scenario.
- Total independent samples: `589824`; min independent ensemble ESS: `32768.0`.
- Max final `u_accessible_cdf` L1 to uniform: `0.0217651367188`.
- Max final `x_local_norm` L1 to uniform: `0.0203979492187`.
- Max CI95 upper L1: `0.0219939450399`.
- Support violation count: `0`; exact boundary atom count: `0`; nonconverged reflection count: `0`.
- Stationarity ensemble status: `candidate_numeric_stationarity_lines_met_not_proof_registered`.
- Proof-readiness impact: `stationarity_ess_and_u_x_uniformity_gaps_reduced_by_independent_ensemble_candidate`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This block reduces the stationarity/ESS and u/x-local uniformity gap without registering Package C proof/pass. It is an independent-ensemble candidate check of one-step transition invariance from analytically uniform center support; it is not a validated Brownian solver output, not runtime authorization, and not sidewall PRS/EAS numeric output.

## 22. Current Package C one-wall and wall-pileup refinement status

The next local proof-threshold reduction block expands the two remaining numeric stress diagnostics:

- Artifact id: `PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT_20260701`.
- Disposition: `NODI_PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: expanded one-wall folded-normal positive control and expanded first-vs-adjacent near-wall band pileup diagnostics, source lock, no-proof firewall, status/report/manifest.
- One-wall rows: `6`, using `65536` samples per d/sigma case.
- Wall-pileup rows: `12`, using `65536` samples per scenario.
- Max one-wall KS: `0.005281493` against proof line `<=0.01`.
- Max wall-pileup ratio: `1.072659525` against proof line `<=1.25`.
- Max wall-pileup CI95 high: `1.214998175` against proof line `<=1.25`.
- Candidate status: `candidate_numeric_thresholds_met_not_proof_registered`.
- Proof-readiness impact: `one_wall_and_wall_pileup_proof_threshold_gaps_reduced_by_expanded_sampling_candidate`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This block closes the remaining one-wall/wall-pileup numeric threshold gaps in candidate evidence, but it still does not register Package C proof/pass. After the following near-boundary method-binding block, the remaining Package C blockers are manual authorization/clean commit binding, runtime/substep policy review, and separate solver/wet branches.

## 23. Current Package C near-boundary expected-band method status

The next local method-binding block converts the near-boundary band check from a sparse raw fraction into an area-expectation method:

- Artifact id: `PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_20260701`.
- Disposition: `NODI_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_CANDIDATE_READY_NO_PROOF_REGISTRATION`.
- Scope: expected-band area formula rows, legacy sparse context row, source lock, no-proof firewall, status/report/manifest.
- Formula: `expected_fraction=(Area(radius+a)-Area(radius+b))/Area(radius)` over the center-accessible geometry.
- Expected-band rows: `24`, covering the first two 1 nm wall-gap bands for the 12 expanded wall-pileup scenarios.
- Legacy sparse context rows: `1`; the old Gate37 `0.001 nm` / `n=384` near-band row is retained as underpowered sparse context, not as proof failure.
- Max abs z to expected: `2.049081656` against candidate line `<=3.0`.
- Max observed first-band fraction: `0.017562866211`; max expected first-band fraction: `0.016840432432`.
- Method status: `candidate_method_bound_not_proof_registered`.
- Proof-readiness impact: `near_boundary_expected_band_method_bound_as_candidate_no_proof_registration`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

This block binds the near-boundary expected-band method without registering proof/pass. It is a geometry/statistical method artifact only, not a validated Brownian solver output, not runtime authorization, and not sidewall PRS/EAS numeric output.

## 24. Current Package C runtime/substep policy design status

The next block converts the substep dt-refinement requirements into a fail-closed runtime/substep policy design:

- Artifact id: `PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_20260701`.
- Disposition: `NODI_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_CANDIDATE_READY_NO_RUNTIME_AUTHORIZATION`.
- Scope: per-scenario runtime/substep policy classes, future runtime-policy field requirements, source lock, no-proof firewall, status/report/manifest.
- Policy rows: `6`.
- Field requirement rows: `8`.
- Low/moderate/high/prohibitive substep-cost rows: `4` / `1` / `0` / `1`.
- Max required substeps to meet threshold: `526`.
- Runtime policy design status: `policy_design_bound_not_runtime_authorized`.
- Runtime policy authorization status: `missing_not_authorized`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

The refreshed threshold/readiness/external-research chain now carries this runtime/substep policy design as candidate evidence:

- Proof-threshold rows: `16`; runtime-policy gap rows: `4`; proof-readiness impact: `numeric_method_and_runtime_policy_candidate_lines_bound_to_authorization_gaps`.
- Proof-readiness rows: `9`, adding `runtime_substep_policy_design`; open blocker rows remain `4`.
- External-research context rows: `7`, adding `runtime_substep_policy_design`.

This block makes the `526` substep worst case machine-readable as a prohibitive-cost authorization issue, not a runtime setting. It does not register Package C proof/pass, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## 25. Current Package C authorization preflight status

The next block binds the current GitHub-visible candidate commit into an authorization preflight packet while keeping the manual ledger empty and fail-closed:

- Artifact id: `PACKAGE_C_AUTHORIZATION_PREFLIGHT_20260701`.
- Disposition: `NODI_PACKAGE_C_AUTHORIZATION_PREFLIGHT_CANDIDATE_READY_NO_AUTHORIZATION`.
- Scope: clean commit binding row, manual authorization ledger placeholder, hard-fail checklist, source lock, no-proof firewall, status/report/manifest.
- Target reviewed commit: `9586f8fc27d80d54b5887dc4ca59560476a86b97`.
- Head matches `origin/main`: `true`.
- Manual authorization ledger status: `missing_fail_closed`.
- Hard-fail checklist rows: `9`.
- Current boundary remains: `proof_registration_authorized=false`; `package_c_validation_status_pass_authorized=false`; `runtime_allowed=false`; `numeric_prs_eas_allowed=false`; `comsol_launch_allowed=false`; `.mph_load_allowed=false`.

The refreshed readiness/external-research chain now carries this preflight as candidate evidence:

- Proof-readiness rows: `10`, adding `authorization_preflight`; open blocker rows remain `4`.
- External-research context rows: `8`, adding `authorization_preflight`.

This block identifies a GitHub-visible candidate commit and a fail-closed manual-ledger placeholder. It does not supersede the no-auth ledger, register Package C proof/pass, authorize runtime, emit numeric PRS/EAS, launch COMSOL, load `.mph`, or create route/yield/detection/wet/fabrication/production claims.

## 26. Current Package C user authorization ledger status

The user has now explicitly authorized the manual authorization ledger, runtime/substep policy path, and solver/wet branch paths. This is recorded as a scope authorization ledger rather than a result-promotion artifact:

- Artifact id: `PACKAGE_C_USER_AUTHORIZATION_LEDGER_20260701`.
- Disposition: `NODI_PACKAGE_C_USER_AUTHORIZATION_LEDGER_ACCEPTED_NO_RESULT_PROMOTION`.
- Authorized scopes: `package_c_proof_registration_path`, `runtime_substep_policy_path`, `solver_branch_path`, `wet_branch_path`.
- Authorized scope rows: `4`.
- Result-promotion guard rows: `14`.
- Authorization source: `user_explicit_message_current_thread_20260701`.
- Current result state remains: `package_c_proof_artifact_registered=false`; `package_c_validation_status_pass_current=false`; `runtime_execution_started=false`; `sidewall_prs_eas_numeric_output_current=false`; `comsol_launch_started=false`; `.mph_load_started=false`.

The refreshed readiness/external-research chain now carries this authorization ledger:

- Proof-readiness rows: `11`, adding `user_authorization_ledger`.
- Open blocker rows remain `4`, but the manual-ledger blocker is replaced by proof-artifact registration, runtime execution evidence, solver/wet evidence, and final clean-commit binding blockers.
- External-research context rows: `9`, adding `user_authorization_ledger`.

This block resolves the manual authorization blocker as a path authorization. It does not itself register Package C proof/pass, start runtime, launch COMSOL, load `.mph`, emit sidewall PRS/EAS numeric output, or create route/yield/detection/wet/fabrication/production claims.

## 27. Current Package C proof registration artifact status

Package C finite-step reflection-surrogate proof evidence is now registered, with a narrow scope and no runtime promotion:

- Artifact id: `PACKAGE_C_PROOF_REGISTRATION_ARTIFACT_20260701`.
- Disposition: `NODI_PACKAGE_C_PROOF_REGISTRATION_ARTIFACT_REGISTERED_NO_RUNTIME`.
- Registered scope: `finite_step_reflection_surrogate_evidence_only`.
- Reviewed evidence commit: `55e093489b48c48e1ed61b598e8167bf1dc61348`.
- Proof registration authorized: `true`, via `PACKAGE_C_USER_AUTHORIZATION_LEDGER_20260701`.
- Package C proof artifact registered: `true`.
- Package C validation status pass current: `true`, scoped only to finite-step reflection-surrogate evidence.
- Proof-threshold rows: `16`; proof gap rows: `0`; proof method gap rows: `0`.
- Runtime-policy gap rows remain: `4`.
- Post-registration guard rows: `14`.
- Source-lock rows: `26`.

This registration does not authorize runtime configuration, NODI recomputation, sidewall PRS/EAS numeric output, COMSOL launch, `.mph` load, validated Brownian solver output beyond the finite-step surrogate, hindered diffusion, trapezoid flow, electrokinetic solver output, optical solver output, true `W_eff`, route/yield/detection, wet claims, fabrication release, or production ingestion.

## 28. Current runtime/substep guard implementation status

The runtime/substep path now has a code-level preflight guard:

- Module: `nodi_simulator/runtime_substep_policy.py`.
- Policy version: `trapezoid_runtime_substep_guard_v1`.
- Trigger metric: `brownian_rms_step_over_surface_gap_quantile`.
- Default threshold: `1.0`.
- Default surface-gap quantile: `0.05`.
- Low-cost runtime guard threshold: `required_substeps <= 16`.
- Review/prohibitive boundary: `required_substeps > 128` is blocked unless a later execution packet records a manual waiver.
- PRS/EAS numeric permission remains: `sidewall_prs_eas_numeric_allowed=false`.

This guard can classify rectangle/no-diffusion paths as not applicable, low-cost substep paths as execution-packet required, and the current narrow-tail stress case (`required_substeps=526`) as `blocked_prohibitive_substep_cost` unless a separate execution packet records a manual waiver. It does not itself run NODI, emit sidewall PRS/EAS numeric output, launch COMSOL, load `.mph`, or create solver/wet/route/yield/detection claims.

## 29. Recommended next action

Current safe route after Package C proof registration:

1. Treat Package C reflection boundary evidence as registered only for `finite_step_reflection_surrogate_evidence_only`.
2. Next local implementation block should bind this runtime/substep guard into an execution packet and then into the narrowest NODI trajectory smoke test; do not jump directly to PRS/EAS numeric output.
3. Treat runtime/substep and solver/wet branches as authorized paths, but require execution/evidence packets before any runtime output, COMSOL launch record, `.mph` load record, wet claim, solver output, or sidewall PRS/EAS numeric result is reported.
4. Do not broaden `package_C_validation_status_pass_current=true` beyond finite-step reflection-surrogate evidence without a separate solver/wet/runtime packet.
5. Keep `ideal_rectangle` as a first-class runtime path and keep trapezoid sidewall analysis schema-bound; no rectangular cache may satisfy trapezoid requests.
6. Use external AI only for broad literature/method synthesis or a major proof-threshold review, not for repetitive micro-audits that local tests/subagents can cover.

Only after Package A/B remain green and the runtime/substep execution packet clears its retained blockers should NODI run any sidewall-aware PRS/EAS pilot involving trajectory, near-wall, hindered-diffusion, or wall-distance-bin metrics. Even then, the result should remain `surrogate_sensitivity_only` / `context-only` until measurement or solver evidence is explicitly added and authorized.

## 30. Authorized downstream mainline advancement status

The user has explicitly authorized the downstream runtime/substep, solver, wet, and route/yield/detection branches. This changes the planning state from "do not touch these branches" to "implement and generate evidence, but do not promote incomplete evidence into final claims."

The next integrated packet is:

- Artifact id: `PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_20260701`.
- Disposition: `NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_READY_FOR_EXECUTION_PACKETS`.
- Covered branches:
  - `runtime_substep_execution`
  - `trapezoid_flow_solver`
  - `electrokinetic_solver`
  - `optical_reference_solver`
  - `wet_ev_evidence`
  - `route_yield_detection_decision`
- Branch state: `authorized_to_implement=true` and `evidence_generation_allowed=true`.
- Current final-claim state: `final_claim_promoted_current=false`.

This wording is intentional. Runtime, solver, wet, route, yield, and detection work are now in-scope for implementation. Their outputs should first be marked as candidate evidence or branch evidence with source hashes, parameter grids, and promotion contracts. A final `route_score`, `winner`, `JRC`, `q_ch`, `yield`, `detection_probability`, wet-pass, fabrication, or production claim becomes true only after the corresponding branch evidence packet satisfies its promotion contract.

The efficient mainline route is:

1. Build the runtime/substep execution packet and run the narrowest guarded NODI trajectory smoke/stress cases.
2. In parallel, prepare solver preflights for trapezoid flow, electrokinetic grid/field evidence, and optical/reference evidence.
3. In parallel, prepare the wet/EV evidence contract for passability, clogging, recovery, yield, and detection controls.
4. Bind route/yield/detection promotion only after the runtime, solver, wet, and Package D precheck evidence hashes exist.

This keeps ideal rectangle as a first-class runtime path while allowing trapezoid sidewall evidence to advance as a coordinated downstream program rather than as isolated micro-gates.

## 31. Current runtime/substep execution packet status

The first authorized downstream execution packet converts the runtime/substep guard from design evidence into narrow guarded runtime smoke evidence:

- Artifact id: `PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_20260701`.
- Disposition: `NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_READY_WITH_GUARDED_SMOKE`.
- Runtime policy version: `trapezoid_runtime_substep_guard_v1`.
- Executed smoke case: `low_cost_theta90_D900_r20_seed31031`.
- Smoke role: `guarded_runtime_smoke_executed`.
- Stress blocker case: `narrow_tail_theta70_D900_r150`.
- Stress blocker role: `prohibitive_substep_stress_blocked`.
- Stress required substeps: `526`.

This packet runs the narrowest local NODI trajectory smoke evidence under the trapezoid runtime guard and records the prohibitive 526-substep stress case as blocked-as-expected. It does not emit sidewall PRS/EAS numeric output, launch COMSOL, load `.mph`, produce solver/wet output, promote route/yield/detection claims, or create fabrication/production evidence.

The next efficient blocks can proceed in parallel:

1. Add a substep-aware runtime kernel or wrapper if the project needs to execute moderate/prohibitive cases rather than only classify them.
2. Prepare trapezoid flow solver / COMSOL flow comparison preflight before any `q_ch` weighting.
3. Prepare electrokinetic grid and optical/reference preflights before any true `W_eff` or detection-response claim.
4. Prepare wet/EV evidence contract before passability, clogging, recovery, yield, or detection probability claims.

## 32. Current trapezoid flow solver candidate status

The flow/q_ch branch now has a first local candidate solver evidence packet:

- Module: `nodi_simulator/trapezoid_flow_solver.py`.
- Solver version: `trapezoid_poisson_no_slip_fd_candidate_v1`.
- Artifact id: `PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_20260701`.
- Disposition: `NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_READY_NOT_QCH`.
- Solver rows:
  - `rectangle_limit_theta90_D900_W500`
  - `taper_theta85_D900_W500`
  - `closed_theta70_D900_W500`
- The solver solves a small finite-difference cross-section Poisson/no-slip surrogate, with `Q = (dp/dy)/viscosity * integral(phi dA)`, where `laplacian(phi)=-1`.
- `taper_theta85_D900_W500` is candidate solver output and increases hydraulic resistance relative to the rectangular proxy.
- `closed_theta70_D900_W500` is blocked as `blocked_geometry_closed`.

This is real solver-candidate evidence for the flow branch, not a formal `q_ch` sidecar and not route weighting. The packet keeps:

- `not_qch_weighted=true`
- `q_ch_weighting_current=false`
- `route_score_current=false`
- `winner_current=false`
- `yield_detection_probability_current=false`

Before any formal `q_ch`, `route_score`, `winner`, `JRC`, yield, or detection-probability claim can become true, this candidate solver must either be validated against COMSOL/pressure-flow evidence or bound to an explicitly accepted flow sidecar with source hashes and the Package D route precheck.

## 33. Current q_ch sidecar candidate status

The flow branch has now advanced from solver-candidate rows into a candidate
`q_ch` sidecar:

- Module: `nodi_simulator/qch_sidecar.py`.
- Sidecar version: `qch_sidecar_candidate_from_trapezoid_flow_solver_v1`.
- Artifact id: `PACKAGE_C_QCH_SIDECAR_CANDIDATE_20260701`.
- Disposition: `NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_READY_NOT_ROUTE`.
- Source artifact: `NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_SOLVER_ROWS_20260701.csv`.
- Candidate definition: `q_ch_candidate_m3_s = pressure_drop_Pa / hydraulic_resistance_Pa_s_m3`.
- Normalization: `candidate_flow_split_fraction` over open solver rows at fixed pressure.

This is no longer merely a blocker or placeholder. It is a concrete candidate
sidecar that carries source hashes, geometry hashes, units, pressure drop,
normalization basis, and blocked-source rows. It remains not-yet-formal because
pressure-flow calibration or COMSOL comparison evidence is still needed before
the sidecar can be accepted as a formal Gate2 q_ch source.

The promotion path is now explicit:

1. `formal_gate2_qch_sidecar`: requires pressure-flow calibration or COMSOL
   comparison evidence hash plus source/geometry hash review.
2. `route_score`: requires accepted q_ch sidecar plus sidewall PRS/EAS Package D
   precheck and no-borrowing audit.
3. `winner_or_JRC`: requires route-score evidence plus independent route audit.
4. `yield_detection_probability`: requires wet/EV evidence contract plus
   optical/detection calibration.

Thus q_ch, route, yield, and detection are all being advanced as authorized
branches, but each branch still has a distinct evidence requirement before its
final claim can become true.

## 34. Current pressure-flow validation context status

The q_ch branch now has a first COMSOL pressure-flow validation context packet:

- Module: `nodi_simulator/pressure_flow_validation.py`.
- Validation version: `pressure_flow_validation_candidate_v1`.
- Artifact id: `PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_20260701`.
- Disposition: `NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_READY_NOT_FORMAL_QCH`.
- NODI source: `NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_QCH_ROWS_20260701.csv`.
- COMSOL context source:
  `stage11_explicit_nano_pressure_only_p1b_w800_qch_01_sw85_d0p9_hmax0p5_summary.csv`.

This packet ingests existing local COMSOL pressure-flow evidence at sw85/d0.9
and 5 kPa, locks the source hash, and compares the 522 candidate q_ch rows at
the COMSOL pressure drop. The comparison is deliberately marked
`geometry_family_context_only` because the COMSOL source is a W800/route-family
context row, while the current q_ch sidecar rows come from W500 candidate
solver cases.

Result:

- COMSOL context is now available and source-locked.
- The q_ch branch has moved beyond a purely local finite-difference candidate.
- Formal q_ch acceptance remains false until an exact geometry/route match or
  an explicitly accepted mapping/calibration evidence hash is provided.
- Route score, winner/JRC, yield, detection probability, wet pass, fabrication,
  and production remain downstream promotion targets, not current conclusions.

The next most efficient route is to either run or ingest an exact W500/D900
pressure-flow comparison for the theta85 candidate, or to add an explicit
W800-to-W500 mapping/calibration contract if the W800 COMSOL family is intended
to calibrate the W500 NODI sidecar.

## 35. Current route/yield/detection candidate status

The route/yield/detection branch now has a concrete candidate packet:

- Module: `nodi_simulator/route_yield_detection_candidate.py`.
- Candidate version: `route_yield_detection_candidate_from_qch_context_v1`.
- Artifact id: `PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_20260701`.
- Disposition: `NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_READY_NOT_FINAL`.
- Inputs:
  - `NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_QCH_ROWS_20260701.csv`
  - `NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_COMPARISON_ROWS_20260701.csv`

This packet computes a `route_decision_candidate_metric` from candidate q_ch
flow split and pressure-flow context weight. It also emits
`candidate_sort_index_under_context` so downstream analysis can inspect the
candidate ordering without calling it a route winner.

The current candidate metric is intentionally not a formal route score:

- `route_score_current=false`
- `winner_current=false`
- `JRC_current=false`
- `yield_current=false`
- `detection_probability_current=false`

The wet and optical/detection branches are now explicitly bound as evidence
gaps rather than treated as out of scope. The next evidence needed before final
claims can become true is:

1. accepted formal q_ch sidecar plus exact pressure-flow validation;
2. route-score decision ledger and independent route audit;
3. wet EV pass/recovery controls and sample-handling evidence;
4. optical/reference calibration plus detector-response evidence.

## 36. Current wet/optical/detection evidence-context status

The wet/optical/detection branch now has a first evidence-context packet that
binds existing NODI/Tsuyama detection materials to the current Package C route
candidates:

- Module: `nodi_simulator/wet_optical_detection_evidence.py`.
- Evidence context version:
  `wet_optical_detection_evidence_context_from_tsuyama_lane_v1`.
- Artifact id:
  `PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_20260701`.
- Disposition:
  `NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_READY_NOT_FINAL`.
- Inputs:
  - `NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_ROUTE_CANDIDATE_ROWS_20260701.csv`
  - `results/tsuyama_gold_aligned_detection_lane/gold_targeted_sweep_final_v1.csv`
  - `results/tsuyama_gold_aligned_detection_lane/blank_fpr_sweep_v1.csv`
  - `results/tsuyama_gold_aligned_detection_lane/feasible_scenarios_v1.csv`
  - `results/tsuyama_gold_aligned_detection_lane/ev_targeted_panel_v1.csv`
  - `results/tsuyama_gold_aligned_detection_lane/ev_ranking_comparison_v1.csv`

This packet changes the state of the wet/optical/detection branch from
`missing` to source-locked context evidence. It records nearest-geometry
detection context for the current W500/D900 route candidates, binds blank-FPR
guardrail evidence, and connects the EV weighted detection panel/ranking context
to each candidate route row.

It does not claim sidewall-specific optical calibration or wet validation:

- `sidewall_specific_optical_solver_current=false`
- `sidewall_specific_wet_evidence_current=false`
- `detection_probability_current=false`
- `yield_current=false`
- `route_score_current=false`
- `winner_current=false`
- `JRC_current=false`

The next efficient wet/optical/detection blocks are:

1. run or ingest W500/D900 sidewall-specific optical/reference calibration for
   theta85 and rectangle-limit cases;
2. rerun the EV detection panel with selected-annulus columns if selected-annulus
   detection is intended to enter Package D;
3. add wet EV pass/recovery and wall-interaction evidence contracts before yield
   or recovery can be promoted;
4. combine accepted q_ch, exact pressure-flow validation, sidewall optical
   calibration, and wet evidence into a future route-score decision ledger.

## 37. Current sidewall optical/reference smoke status

The optical/reference branch now has a first executable NODI smoke packet for
the W500/D900 route candidates:

- Module: `nodi_simulator/sidewall_optical_reference_smoke.py`.
- Smoke version: `sidewall_optical_reference_smoke_w500_d900_v1`.
- Artifact id: `PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_READY_NOT_OPTICAL_SOLVER`.
- Cases:
  - `rectangle_limit_theta90_D900_W500`
  - `taper_theta85_D900_W500`

This packet runs small NODI batches for the rectangle-limit and theta85
trapezoid cases, records synthetic detection context, and exports the reference
geometry propagation diagnostics. The trapezoid row explicitly records:

- `geometry_not_propagated_to_reference_field=true`
- `reference_geometry_propagation_status=blocked_trapezoid_geometry_not_propagated_to_reference_field`
- `reference_geometry_claim_level=proxy_not_sidewall_aware_not_optical_solver_output`

This advances the optical/reference branch from pure gap planning to executable
smoke evidence. It also proves the current limitation that trapezoid geometry is
still not consumed by a true optical/reference solver.

Current claim state remains:

- `optical_solver_current=false`
- `detection_probability_current=false`
- `yield_current=false`
- `route_score_current=false`
- `winner_current=false`
- `JRC_current=false`

The next optical branch step is to replace this smoke/proxy evidence with a
sidewall-aware optical/reference solver or calibrated lookup that consumes the
trapezoid geometry, after which detection-response calibration and blank-trace
validation can be evaluated.

## 38. Current sidewall reference surrogate candidate status

The optical/reference branch now has a geometry-propagated reference surrogate
candidate:

- Reference model: `trapezoid_effective_aperture_surrogate`.
- Module: `nodi_simulator/sidewall_reference_surrogate_candidate.py`.
- Artifact id:
  `PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_READY_NOT_OPTICAL_SOLVER`.
- Rows: rectangle-limit and theta85 W500/D900 at 404 nm and 660 nm.

This candidate consumes trapezoid geometry through an area-equivalent aperture
factor:

`effective_aperture_width = (W_top + W_bottom_runtime_clipped) / 2`

For W500/D900/theta85, the 404 nm row records a sidewall aperture factor below
the rectangle-limit row. The 660 nm rows also record the W500 NA cutoff context,
where the reference amplitude is hard-zeroed by the existing NA guardrail.

This is a real propagation step beyond the previous reference smoke packet:

- `geometry_not_propagated_to_reference_field=false`
- `reference_uses_rectangular_width_depth_surrogate=false`
- `reference_geometry_propagation_status=trapezoid_geometry_propagated_to_effective_aperture_reference_surrogate`

It is still not a full optical solver or calibrated detector model:

- `full_wave_or_calibrated_optical_solver_current=false`
- `true_W_eff_current=false`
- `detection_probability_current=false`
- `route_score_current=false`

The next optical branch step is a calibrated lookup or electromagnetic/optical
field solver that defines true `W_eff`, detector response, and blank-channel
reference behavior for the sidewall geometry.

## 39. Current NODI smoke status for the sidewall reference surrogate

The sidewall reference surrogate is now exercised inside an executable NODI
smoke matrix, rather than only as a standalone `compute_reference_field` row:

- Module: `nodi_simulator/sidewall_reference_surrogate_smoke.py`.
- Smoke version: `sidewall_reference_surrogate_smoke_w500_d900_v1`.
- Artifact id: `PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_READY_NOT_OPTICAL_SOLVER`.
- Matrix:
  - `rectangle_limit_theta90_D900_W500`
  - `taper_theta85_D900_W500`
  - `channel_angular_surrogate`
  - `trapezoid_effective_aperture_surrogate`
  - 404 nm and 660 nm

This packet compares the legacy rectangular reference proxy against the
trapezoid effective-aperture surrogate in small `run_single_case_batch` smoke
runs. It keeps the rectangle-limit channel as a first-class baseline while
showing that the theta85 sidewall row changes from:

- `geometry_not_propagated_to_reference_field=true` under
  `channel_angular_surrogate`

to:

- `geometry_not_propagated_to_reference_field=false`
- `reference_geometry_propagation_status=trapezoid_geometry_propagated_to_effective_aperture_reference_surrogate`
- `reference_solver_status=trapezoid_effective_aperture_surrogate_active`

under `trapezoid_effective_aperture_surrogate`.

The 404 nm theta85 row records the effective-aperture factor without the W500
NA hard-zero masking the sidewall effect. The 660 nm rows preserve the existing
NA cutoff context.

Detection-rate deltas in this smoke packet are explicitly small-n synthetic
context. They are not:

- detection probability;
- yield;
- route score;
- winner/JRC;
- true `W_eff`;
- wet pass evidence;
- full-wave or calibrated optical solver output.

The next large block should therefore use this propagated reference surrogate
to bridge into a calibrated/validated detector context: either a sidewall-aware
blank-channel calibration table or an optical solver branch that can define
true `W_eff`, detector response, and route-level scoring prerequisites.

## 40. Current sidewall optical calibration bridge status

The optical branch now has a calibration bridge packet that converts the 528
NODI smoke rows into a replaceable reference-calibration seed table and a
readiness matrix:

- Module: `nodi_simulator/sidewall_optical_calibration_bridge.py`.
- Bridge version:
  `sidewall_optical_calibration_bridge_from_reference_surrogate_smoke_v1`.
- Artifact id: `PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_READY_SEED_ONLY`.
- Seed table:
  `NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_SEED_TABLE_20260701.csv`.
- Seed manifest:
  `NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_SEED_TABLE_20260701.csv.manifest.json`.

The seed table is intentionally marked:

- `calibration_data_role=synthetic_fixture_not_experimental`
- `not_experimental_blank_channel_calibration=true`
- `not_full_wave_optical_solver=true`
- `not_true_W_eff=true`
- `not_detector_response_validation=true`
- `not_detection_probability=true`

This is deliberate. The table is schema-compatible with the existing
`calibrated_lookup` path so future measured blank-channel or solver rows can
replace it, but the current synthetic role must keep runtime lookup from
unlocking calibrated reference claims.

The readiness matrix currently tracks these promotion lanes:

- blank-channel reference amplitude and phase;
- sidewall geometry coverage;
- detector response / BFP / ROI bridge;
- blank false-positive trace validation;
- wet wall-interaction evidence;
- integrated route ledger.

Current claim state remains:

- `full_wave_or_calibrated_optical_solver_current=false`
- `true_W_eff_current=false`
- `detector_response_validation_current=false`
- `detection_probability_current=false`
- `yield_current=false`
- `route_score_current=false`
- `winner_current=false`
- `JRC_current=false`

The next large block should use this bridge to either ingest measured/solver
sidewall calibration rows or build the integrated promotion ledger that states
exactly which calibrated optical, flow, wet, and route-selection inputs are
still missing before detection probability, yield, route score, or winner can
be claimed.

## 41. Current integrated promotion ledger status

The sidewall Package C evidence chain now has an integrated promotion preflight
ledger:

- Module: `nodi_simulator/sidewall_integrated_promotion_ledger.py`.
- Ledger version: `sidewall_integrated_promotion_preflight_ledger_v1`.
- Artifact id: `PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_READY_PREFLIGHT_ONLY`.

This is not a route ranking table. It deliberately emits:

- route summary ledger rows;
- blocker catalog rows;
- `route_candidate_id x evidence_lane x target_claim` promotion-lane rows.

The ledger joins the current q_ch sidecar, pressure-flow validation context,
route/yield/detection candidate, wet/optical detection context, sidewall
reference surrogate smoke, and optical calibration bridge. Its output is a
preflight statement of what still blocks promotion:

- formal q_ch / accepted flow split is still not current;
- pressure-flow validation is still context-only;
- selected-annulus context is still missing;
- sidewall optical calibration is still synthetic seed only;
- detector response and blank false-positive validation are still missing;
- wet wall-interaction evidence is still missing;
- route-selection policy / independent decision audit is still missing.

The ledger keeps these flags false:

- `route_score_current=false`
- `winner_current=false`
- `JRC_current=false`
- `yield_current=false`
- `detection_probability_current=false`
- `formal_qch_weighting_current=false`

Allowed use is promotion planning and evidence prioritization. Blocked use is
route scoring, route selection, q_ch weighting, detection probability, yield,
wet pass, clogging/time-to-clog/recovery, fabrication release, or production
ingestion.

## 42. Current selected-annulus sidewall context status

The selected-annulus blocker now has a small executable sidewall context packet:

- Module: `nodi_simulator/sidewall_selected_annulus_context.py`.
- Context version: `sidewall_selected_annulus_context_w500_d900_v1`.
- Artifact id: `PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_READY_NOT_PROBABILITY`.
- Cases:
  - `rectangle_limit_theta90_D900_W500`
  - `taper_theta85_D900_W500`
- Reference model:
  `trapezoid_effective_aperture_surrogate`.
- Wavelength: 404 nm.

This packet runs a small NODI sidewall selected-annulus smoke and records:

- `selected_annulus_source=initial_position_edge_norm_annulus_diagnostic_v1`
- `selected_annulus_edge_norm_min=0.5`
- `selected_annulus_edge_norm_max=0.8`
- selected-annulus event counts, detected counts, fraction, context rate, and
  Wilson lower-bound context.

The output can reduce the integrated ledger lane from
`selected_annulus_context_missing_rerun_required` to
`selected_annulus_context_available_small_n_not_probability`.

It is still not:

- detection probability;
- route score;
- winner/JRC;
- yield;
- wet pass;
- calibrated detector response.

The next ledger refresh should consume this packet and update only the
selected-annulus blocker status, while keeping detection probability and route
promotion blocked until calibrated optical, blank false-positive, wet, q_ch,
and route-selection evidence are all available.

## 43. Current integrated promotion ledger refresh status

The selected-annulus context has now been consumed into the integrated promotion
ledger as a narrow refresh:

- Module:
  `tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_refresh.py`.
- Artifact id:
  `PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_READY_PREFLIGHT_ONLY`.
- Claim boundary:
  `promotion_ledger_refresh_not_route_score_not_detection_probability`.

This refresh copies the Gate 530 promotion-lane ledger and updates only the
`selected_annulus_detection_context` rows. The lane status changes from missing
rerun evidence to:

- `selected_annulus_context_available_small_n_not_probability`

The source artifact for that lane is now the Gate 531 selected-annulus context
CSV, SHA-bound through the refresh source lock. The refresh emits one delta row
per route candidate and keeps the target claim state false:

- `detection_probability_current=false`
- `route_score_current=false`
- `winner_current=false`
- `yield_current=false`

The selected-annulus blocker is therefore no longer "no sidewall run exists";
it is now "small-N context exists but cannot be used as probability or route
selection evidence." The next large block should attack the remaining evidence
lanes directly:

1. calibrated detector response and blank false-positive traces;
2. accepted sidewall optical/reference calibration or solver output;
3. wet wall-interaction evidence;
4. formal q_ch / pressure-flow validation that can be promoted beyond context;
5. route-selection policy and independent decision audit after the evidence
   hashes above exist.

This keeps ideal rectangle and trapezoid sidewall branches distinct while
allowing the route/yield/detection program to move forward as a coordinated
evidence chain rather than as isolated unmerged diagnostics.

## 44. Current sidewall qch grid-validation refresh status

The flow/qch lane now has an exact W500/D900 grid-refinement candidate packet:

- Module: `nodi_simulator/sidewall_qch_grid_validation.py`.
- Builder:
  `tools/audits/build_nodi_package_c_sidewall_qch_grid_validation_refresh.py`.
- Artifact id:
  `PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_READY_CANDIDATE_ONLY`.
- Claim boundary:
  `qch_grid_refinement_candidate_not_formal_qch_not_route_score`.

The packet runs the current trapezoid pressure-flow candidate solver on the
exact W500/D900 geometry for:

- `rectangle_limit_theta90_D900_W500`
- `taper_theta85_D900_W500`
- `closed_theta70_D900_W500`

It evaluates grids `21`, `31`, and `41`, records the closed geometry as blocked,
and compares candidate flow-split fractions against the 41-grid reference.
The key interpretation is:

- W500/D900 split-candidate convergence is stable enough for promotion
  planning;
- absolute q_ch remains grid-sensitive and still requires exact COMSOL,
  measurement, or a reviewed solver-calibration artifact before it can become
  formal q_ch weighting;
- route score, winner/JRC, yield, and detection probability remain false.

The packet emits a narrow `flow_split_qch` promotion update:

- new status:
  `w500_d900_grid_refined_split_candidate_absolute_q_requires_validation`;
- blocked promotion:
  `formal_qch_weighting`, `route_score`, `winner`, `yield`, and
  `detection_probability`;
- next required evidence:
  exact COMSOL or measurement pressure-flow validation plus route policy audit.

This moves the qch branch forward from generic candidate flow context to an
exact-geometry W500/D900 split-stability candidate, while preserving the
remaining validation requirements for calibrated absolute flow and route-level
claims.

## 45. Current integrated promotion ledger qch-refresh status

The integrated promotion ledger has now consumed the W500/D900 qch
grid-validation packet:

- Builder:
  `tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_qch_refresh.py`.
- Artifact id:
  `PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_QCH_REFRESH_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_QCH_REFRESH_READY_PREFLIGHT_ONLY`.
- Claim boundary:
  `promotion_ledger_qch_refresh_not_formal_qch_not_route_score`.

This refresh starts from the selected-annulus ledger refresh and updates only
the `flow_split_qch` promotion-lane rows. The qch lane status is now:

- `w500_d900_grid_refined_split_candidate_absolute_q_requires_validation`

The selected-annulus lane remains:

- `selected_annulus_context_available_small_n_not_probability`

The integrated ledger therefore now reflects two concrete blocker reductions:

1. selected-annulus sidewall context exists, but is still small-N and not a
   detection probability;
2. W500/D900 flow-split evidence is grid-refined enough for promotion planning,
   but absolute calibrated q_ch and formal q_ch weighting still require exact
   COMSOL, measurement, or a reviewed solver-calibration artifact.

The following values remain false in the integrated ledger:

- `formal_qch_weighting_current=false`
- `route_score_current=false`
- `winner_current=false`
- `yield_current=false`
- `detection_probability_current=false`

The next large block should now move to the detector/blank/optical calibration
lane or to exact COMSOL/measurement pressure-flow validation, because those are
the remaining evidence gates before route/yield/detection can be computed as
accepted claims rather than candidate planning rows.

## 46. Current detector/blank context refresh status

The detector/blank lane now has a sidewall context refresh that joins the latest
selected-annulus and qch-ledger updates with the existing Tsuyama-aligned
wet/optical detection context:

- Module: `nodi_simulator/sidewall_detector_blank_context.py`.
- Builder:
  `tools/audits/build_nodi_package_c_sidewall_detector_blank_context_refresh.py`.
- Artifact id:
  `PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_READY_CONTEXT_ONLY`.
- Claim boundary:
  `detector_blank_context_not_detector_validation_not_detection_probability`.

The refresh consumes:

- wet/optical detection context rows;
- selected-annulus sidewall context rows;
- qch-refreshed integrated promotion ledger rows;
- optical calibration bridge readiness rows.

For both W500/D900 route candidates, it records:

- selected-annulus context is available but small-N and not probability;
- qch flow-split context is W500/D900 grid-refined but not formal q_ch;
- blank false-positive context is nearest-geometry Tsuyama context, not
  sidewall-specific blank validation;
- detector response context is detector-identity/readiness context, not a
  sidewall detector-response calibration;
- optical calibration remains a synthetic reference seed, not measured blank
  calibration or full-wave solver output.

The packet emits promotion-update rows for:

1. `blank_false_positive_trace`
2. `detector_response_bridge`

Both update rows keep `target_claim_current=false`. They reduce the blocker from
"no context assembled" to "context available but not validation." They still
require sidewall-specific blank traces or a validated transferable blank model,
plus detector operator/ROI/slit/standard-particle calibration consuming the
sidewall reference field.

The following remain false:

- `detector_response_validation_current=false`
- `sidewall_specific_blank_trace_current=false`
- `sidewall_specific_optical_calibration_current=false`
- `detection_probability_current=false`
- `route_score_current=false`
- `winner_current=false`
- `yield_current=false`

This is the correct bridge into route/yield/detection computation: the lane has
usable context for planning, but not yet the calibrated detector/blank evidence
needed for accepted detection probability.

## 47. Current integrated promotion ledger detector/blank-refresh status

The integrated promotion ledger has now consumed the detector/blank context
refresh:

- Builder:
  `tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_detector_blank_refresh.py`.
- Artifact id:
  `PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_REFRESH_20260701`.
- Disposition:
  `NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_REFRESH_READY_PREFLIGHT_ONLY`.
- Claim boundary:
  `promotion_ledger_detector_blank_refresh_not_detector_validation_not_detection_probability`.

This refresh starts from the qch-refreshed integrated ledger and updates only
the detector/blank promotion lanes:

1. `blank_false_positive_trace`
2. `detector_response_bridge`

For both W500/D900 route candidates, the blank lane now records:

- `nearest_blank_context_available_not_sidewall_specific_validation`

and the detector lane now records:

- `detector_identity_context_available_not_sidewall_response_validation`

The qch lane remains:

- `w500_d900_grid_refined_split_candidate_absolute_q_requires_validation`

and the selected-annulus lane remains:

- `selected_annulus_context_available_small_n_not_probability`

This is a useful mainline reduction: flow split, selected annulus,
nearest-blank context, and detector identity/readiness are now all represented
in the same promotion ledger. The remaining large blockers are no longer
"context not assembled"; they are concrete validation or calibration tasks:

- exact COMSOL/measurement pressure-flow validation or reviewed solver
  calibration for formal q_ch;
- sidewall-specific blank traces or a validated transferable blank model;
- detector operator, ROI/slit throughput, and standard-particle calibration
  consuming the sidewall reference field;
- wet/surface evidence for pass/recovery/clogging/yield claims.

The following remain false in this ledger refresh:

- `detector_response_validation_current=false`
- `sidewall_specific_blank_trace_current=false`
- `sidewall_specific_optical_calibration_current=false`
- `detection_probability_current=false`
- `route_score_current=false`
- `winner_current=false`
- `yield_current=false`
