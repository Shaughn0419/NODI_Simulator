# Report 158 - NODI next artifacts validator implementation

Date: 2026-06-17

Status:

```text
validator_implementation_completed
schema_constants_implemented
production_validator_cli_implemented
design_only_smoke_manifest_scaffolding_implemented
independent_review_request_changes_fixed
no runner implementation
no runner execution
no NODI run
no COMSOL run
no smoke execution
no production artifact
no JOINT_ROUTE_CLASS regeneration
```

This report records the first code-level implementation step after the
Report 156 COMSOL-side PASS and the user authorization to proceed.

## 1. Implemented files

```text
nodi_simulator/nodi_comsol_next_artifacts.py
tools/audits/validate_nodi_position_response_surface.py
tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py
tests/test_nodi_comsol_next_artifacts_contracts.py
```

The implementation is intentionally limited to executable contract constants,
CSV validators, COMSOL descriptor validation helpers, and design-only smoke
manifest row builders. It does not implement a NODI runner and does not execute
any NODI/COMSOL simulation.

## 2. Canonical source pins

The validator module pins the Report 156 canonical contract hashes for:

```text
reports/156_NODI_NEXT_ARTIFACTS_COMSOL_READONLY_REVIEW_INTEGRATION_20260617.md
reports/NODI_POSITION_RESPONSE_SURFACE_SCHEMA_CONTRACT_20260617.csv
reports/NODI_POSITION_RESPONSE_SURFACE_VALIDATOR_RULES_20260617.csv
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_SCHEMA_CONTRACT_20260617.csv
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_VALIDATOR_RULES_20260617.csv
```

Local hash validation was run and passed.

## 3. Position-response enforcement

Implemented hard checks include:

```text
row_scope=response_surface_bin for production NODI_POSITION_RESPONSE_SURFACE rows
qch_provenance_reference rejected from production rows
p1b_w800_qch_splitmid_20260617 rejected on response_surface_bin rows
neutral flow_condition_id required:
  nodi_position_response_surface_v1_not_comsol_transport
position_distribution_basis=comsol_transported_distribution rejected
not_comsol_transport_distribution=true required
not_qch_weighted=true required
not_yield=true required
not_detection_probability=true required
500 nm eta-response rows rejected
sample status kept separate from guardrail status
guardrail_blocked rejected as bin_sample_status
```

The PRS CLI validates production response-surface CSVs only. It does not expose
or authorize a q_ch provenance sidecar validator because that sidecar has not
yet been separately defined.

## 4. Effective-aperture enforcement

Implemented hard checks include:

```text
W_eff_surrogate_nm required
delta_W_eff_surrogate_nm required
old W_eff_nm and delta_W_eff_nm rejected
extra positive claim columns rejected
not_true_W_eff=true required
not_measured_geometry=true required
not_optical_solver_output=true required
not_fabrication_release=true required
not_yield=true required
not_winner=true required
claim_boundary=effective_aperture_surrogate_sensitivity_only required
source_geometry_descriptor_sha pinned to COMSOL_GEOMETRY_DESCRIPTOR_V1 SHA
rank_source limited to fullgrid recommendation-eligible route stability connector
Stage-1 detector identity rank source rejected
nonpositive min_aperture_conservative surrogate keeps eta/rank proxy blank
solver_contract_trigger_flag remains a contract trigger only
```

The descriptor helper validates:

```text
grain = route_geometry_id_comsol x process_state
W_top_um == width_group_um
W_bottom_um == bottom_width_nm / 1000
min_aperture_nm == min(bottom_width_nm, D_inscribed_nm)
negative min_aperture values are not clipped
unavailable fabrication/metrology fields remain blank or unavailable_v1, not zero
claim_boundary=nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
route_geometry_id_comsol_version=route_geometry_id_comsol_v1_contract_20260616
```

## 5. Verification performed

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
result: 24 passed

python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/validate_nodi_position_response_surface.py \
  tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
result: All checks passed

python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/validate_nodi_position_response_surface.py \
  tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py
result: pass

canonical Report 156 contract hash check
result: PASS

tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv validation
result: PASS

direct negative probes after independent review request changes:
  measured_geometry extra column -> EAS-V26
  optical_solver_output extra column -> EAS-V26
  fabrication_release extra column -> EAS-V26
  p3_conclusion extra column -> EAS-V26
  wrong route_geometry_id_comsol_version -> EAS-V06

python tests/run_tests.py --workers 7
result:
  AppTest lane: 5 passed, 1473 deselected
  parallel lane: 1473 passed
```

## 6. Independent review status

```text
read-only pattern exploration subagent: completed
read-only verifier subagent attempt 1: failed because usage limit was reached
read-only verifier subagent attempt 2: REQUEST_CHANGES
  HIGH: EAS extra positive claim columns were not rejected
  MEDIUM: descriptor route_geometry_id_comsol_version was not pinned
NODI fix: implemented
post-fix verifier re-review: PASS
post-fix verifier gaps: none from narrow re-review
```

## 7. Still not authorized

This implementation does not authorize:

```text
runner execution
smoke execution
full production run
production response-surface artifact
production aperture-surrogate artifact
COMSOL run
JOINT_ROUTE_CLASS regeneration
q_ch * eta
q_ch * chi_selected * eta
yield
winner
true W_eff
measured geometry
optical solver output
fabrication release
P3 solver execution or conclusion
```

## 8. Current stop point

```text
VALIDATOR_IMPLEMENTATION_PASS_READY_FOR_NEXT_AUTHORIZATION_GATE
```
