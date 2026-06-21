# External AI prompts for NODI next artifacts

Date: 2026-06-17

Status:

```text
optional_review_prompt
planning_artifact_only
no runner implementation
no runner execution
```

## Prompt 1 - Contract and boundary review

```text
You are reviewing a NODI/COMSOL planning bundle. Review only. Do not request or
assume any NODI run, COMSOL run, runner implementation, runner execution, full
production artifact, or JOINT_ROUTE_CLASS regeneration.

Primary files:
- NODI_NEXT_ARTIFACTS_RUNNER_IMPLEMENTATION_PLAN_20260617.md
- NODI_NEXT_ARTIFACTS_BOUNDARY_AND_FORBIDDEN_CLAIMS_20260617.md
- NODI_POSITION_RESPONSE_SURFACE_SCHEMA_CONTRACT_20260617.csv
- NODI_POSITION_RESPONSE_SURFACE_VALIDATOR_RULES_20260617.csv
- NODI_POSITION_RESPONSE_SURFACE_SMOKE_MANIFEST_20260617.csv
- NODI_EFFECTIVE_APERTURE_SURROGATE_SCHEMA_CONTRACT_20260617.csv
- NODI_EFFECTIVE_APERTURE_SURROGATE_VALIDATOR_RULES_20260617.csv
- NODI_EFFECTIVE_APERTURE_SURROGATE_SMOKE_MANIFEST_20260617.csv

Please answer:
1. Does the position-response contract preserve Report 155 flow_condition
   semantics, especially that production rows have row_scope=response_surface_bin
   and p1b_w800_qch_splitmid_20260617 stays out of production rows?
2. Are NODI-only response rows clearly marked as not COMSOL transport, not
   q_ch-weighted, not yield, and not detection probability?
3. Does the aperture-surrogate contract avoid measured geometry, true W_eff,
   optical solver output, fabrication release, winner, and P3 conclusions,
   including by using W_eff_surrogate_nm instead of W_eff_nm?
4. Do the validator rules catch the key claim-boundary failures?
5. Is the smoke path clearly smoke-only and not production?

Return PASS, PASS_WITH_NONBLOCKING_RISKS, or BLOCKED with file/line evidence.
```

## Prompt 2 - Implementation readiness review

```text
You are reviewing whether a future implementation can safely begin after user
authorization. Review only; do not implement.

Check:
1. Are proposed future scripts sufficiently scoped?
2. Are schema contracts complete enough to implement validators before runners?
3. Are smoke manifests bounded and cheap enough to validate row arithmetic?
4. Are source paths and SHA requirements explicit enough?
5. Are there any ambiguities that would cause a future agent to accidentally run
   production or make prohibited claims?

Return:
- READY_FOR_USER_AUTHORIZATION_TO_IMPLEMENT_RUNNERS, or
- BLOCKED_BEFORE_IMPLEMENTATION: <specific reason>.
```
