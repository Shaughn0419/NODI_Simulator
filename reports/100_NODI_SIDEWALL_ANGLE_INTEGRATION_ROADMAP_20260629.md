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
- Updated the PRS sidewall v2 propagated scope to `particle_center_support_and_wall_distance_only_not_reference_fluidic_electrokinetic`; legacy particle-center-only scope no longer satisfies wall-distance-bin PRS rows.
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

Still blocked in this roadmap:

- validated sloped-wall specular reflection and near-wall diffusion under Brownian trajectories;
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

- Package C can emit trajectory-boundary propagation audits, wall-distance diagnostics, and near-wall surrogate diagnostics.
- Package C cannot emit clogging rate, adhesion probability, wet pass probability, recovery, or calibrated event probabilities.
- Package C must pass before Package D can use trajectory, near-wall, hindered-diffusion, or selected-annulus metrics.

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

## 9. Recommended next action

Start with Package A and Package B:

1. Implement the geometry descriptor v2 and convention validator.
2. Add a standalone geometry primitive module.
3. Add unit tests for formula, closure, steric support, and sampling support.
4. Generate a no-compute descriptor/audit packet.
5. Run a review-only cross-check before any PRS/EAS rerun.

Only after those pass should NODI run a sidewall-aware PRS/EAS pilot. Even then, the result should remain `surrogate_sensitivity_only` / `context-only` until measurement or solver evidence is explicitly added and authorized.
