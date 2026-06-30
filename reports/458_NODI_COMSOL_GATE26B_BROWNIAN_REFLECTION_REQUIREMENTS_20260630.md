# GATE26B BROWNIAN REFLECTION REQUIREMENTS

- Gate26 disposition: `NODI_GATE26_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_INTEGRATION_DESIGN_CONSTRAINTS_READY_NO_AUTH`
- External review verdict: `READY_FOR_IMPLEMENTATION_DESIGN_ONLY` integrated as design-only/no-auth.
- Gate25 source drift/missing: 0/0.
- Boundary: no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.
- Machine-readable support: `reports/joint_interface_20260630`.
- Brownian target model: `skorokhod_normal_reflection_convex_offset_trapezoid_v1`.
- Current projection model remains `sidewall_projection_boundary_surrogate_not_specular_reflection` only.
- Hard requirements include active-set corner handling, no boundary atom, uniform equilibrium, dt-halving convergence, rectangle limit, angle/depth mutation, and closure guards.
