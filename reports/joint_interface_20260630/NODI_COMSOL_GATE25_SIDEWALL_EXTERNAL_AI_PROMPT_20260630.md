# External AI Prompt - NODI Sidewall Package C Physics Design Review

You are reviewing a NODI sidewall-angle Package C design packet. Review only.
Do not request or assume NODI recomputation, COMSOL launch, `.mph` loading,
sidewall PRS/EAS numeric generation, q_ch weighting, JRC, route_score, route
winner, yield, detection_probability, wet-pass probability, clogging rate,
time-to-clog, recovery, fabrication release, or production ingestion.

Visibility note: you may only see files on GitHub. Treat the local facts below
as the verified local packet; do not assume unavailable COMSOL or local CSV
contents are absent.

Primary GitHub-visible files to inspect:
- `nodi_simulator/cross_section_geometry.py`
- `nodi_simulator/trajectory.py`
- `nodi_simulator/utils.py`
- `nodi_simulator/fluidic_resistance.py`
- `nodi_simulator/electrokinetic_transport.py`
- `nodi_simulator/reference_field.py`
- `nodi_simulator/nodi_comsol_next_artifacts.py`
- `reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md`
- `reports/345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md`
- `reports/450_NODI_COMSOL_GATE24_SIDEWALL_PACKAGE_C_AUTHORIZATION_LEDGER_MASTER_REPORT_20260630.md`
- `reports/456_NODI_COMSOL_GATE25_SIDEWALL_PACKAGE_C_DESIGN_REVIEW_MASTER_REPORT_20260630.md`

Current verified NODI state:
- `ideal_rectangle` remains a native rectangular path.
- `trapezoid_tapered_sidewalls` exists for descriptor geometry, particle-center
  support, initial-position sampling, geometry-only wall-distance diagnostics,
  observation signatures, and PRS/EAS v2 no-claim validators.
- Current trapezoid trajectory diffusion uses
  `trapezoid_center_support_projection_boundary_v1` and is explicitly
  `sidewall_projection_boundary_surrogate_not_specular_reflection`.
- Trapezoid hindered diffusion is blocked when `diffusion_hindrance_model` is
  not `none`.
- Trapezoid flow currently allows only plug-flow geometry-independent surrogate
  semantics; `parabolic_rect` and `rect_series` are blocked under trapezoid.
- Electrokinetic rectangular wall-distance grids are blocked under trapezoid.
- Reference/optical fields under trapezoid are proxy or audit paths, not optical
  solver output and not true W_eff.
- Gate24 records the future phrase `authorize NODI sidewall Package C physics
  preauthorization`, but exact phrase matching still returns `authorized_now=false`.

Geometry conventions and formulas to review:
- Coordinates: x is channel width, y is flow direction, z is centered depth.
  Package C formulas use `u = z + H/2`, measured downward from the top.
- COMSOL sidewall angle `theta` is from the horizontal substrate; `90 deg` is
  vertical. NODI taper angle `alpha = 90 deg - theta` is from vertical.
- `k = tan(alpha)`.
- Symmetric trapezoid local width: `W(u) = W_top - 2*k*u`.
- Unclipped bottom width: `W_bottom_unclipped = W_top - 2*k*H`.
- Closure is `geometry_closed` when `W_bottom_unclipped <= 0` or
  `H >= W_top/(2*k)`. Negative bottom width must be preserved in descriptor
  space, not silently clipped into an open runtime aperture.
- Side-wall signed distances for centerline x and top-depth u use
  `h(u)=W(u)/2`, `d_left=(x+h(u))/sqrt(1+k^2)`, and
  `d_right=(h(u)-x)/sqrt(1+k^2)`.
- Particle radius `a` center support excludes top/bottom by `a` and sidewalls by
  `a*sqrt(1+k^2)`, so local center x bounds are
  `abs(x) <= h(u) - a*sqrt(1+k^2)` with blocked slices when the right side is
  nonpositive.

Please review:
1. For Brownian trajectories in the particle-center offset trapezoid, should
   Package C use specular reflection, projected Brownian reflection, or
   Skorokhod normal reflection? Give the correct wall-normal update rule,
   corner handling, and time-step stability tests.
2. What tests prove the reflected process stays inside support and does not
   create an artificial wall/corner bias? Include angle/depth mutation tests and
   equilibrium distribution checks.
3. Is any single-wall hindered-diffusion formula acceptable for sloped walls and
   finite particles, or must multi-wall/corner/roughness/profile cases remain
   `solver_required` or `surrogate_sensitivity_only`?
4. What is the safest Package C flow-model plan? Distinguish fixed-velocity
   plug-flow audit, trapezoid velocity-field surrogate, fixed-pressure hydraulic
   resistance, and forbidden q_ch weighting.
5. What electrokinetic grid/profile-aware requirements are needed before
   trapezoid wall-distance electrokinetic metrics can be claimed?
6. What optical/reference-field effects require an actual solver before any
   W_eff, reference strength, detector response, or sidewall scattering claim?
7. Are any schema fields or validators missing before implementation begins?

Return:
- `READY_FOR_IMPLEMENTATION_DESIGN_ONLY` if the design can be implemented later
  after explicit authorization, with required tests listed.
- `NEEDS_REVISION_BEFORE_IMPLEMENTATION` if formulas, claims, or tests are
  incomplete.
- `BLOCKED_PHYSICS_UNSAFE` if the proposed Package C path would create false
  physical claims or route/fabrication conclusions.
