# NODI Sidewall Package C Candidate Exchange RC2 COMSOL Review Request

Disposition target: `PASS_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_READY_FOR_COMSOL_REINTAKE_NO_PROOF_REGISTRATION`.

COMSOL should perform no-run receipt and feasibility review only. Do not launch COMSOL, load `.mph`, generate solver evidence, or register Package C proof.

| request_id | expected_output_enum | question |
| --- | --- | --- |
| RC2-COMSOL-001 | RECEIPT_VALIDATE_NOW_NO_RUN | Verify NODI exchange RC2 manifest row_count and sha values. |
| RC2-COMSOL-002 | RECEIPT_VALIDATE_NOW_NO_RUN | Replace old nodi_dirty_count=29 / exchange_rc1_files=0 observation with RC2 clean release receipt. |
| RC2-COMSOL-003 | CONTEXT_REVIEW_NOW_NO_RUN | Review boundary atom, support invariance, equilibrium uniformity, and dt-halving metrics as candidate-only thresholds. |
| RC2-COMSOL-004 | NODI_ONLY_ALGORITHM_METRIC | Mark finite-step reflection telemetry as NODI algorithm candidate metrics, not COMSOL solver evidence. |
| RC2-COMSOL-005 | FUTURE_COMSOL_RUN_REQUIRED_NOT_AUTHORIZED | Identify which Package C questions require future COMSOL solver or .mph review. |
| RC2-COMSOL-006 | FUTURE_MPH_LOAD_REQUIRED_NOT_AUTHORIZED | Identify any descriptor/source items that would require future .mph load. |
| RC2-COMSOL-007 | FUTURE_USER_AUTHORIZATION_REQUIRED | Confirm authorization-supersession fields remain drafts and do not authorize proof registration. |
| RC2-COMSOL-008 | BLOCKED_AS_EXPECTED | Confirm the 18 blocked candidate rows remain blocked and are not overwritten by aggregate candidate_pass summaries. |
