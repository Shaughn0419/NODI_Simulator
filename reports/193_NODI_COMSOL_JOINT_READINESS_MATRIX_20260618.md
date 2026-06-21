# Report 193 - NODI/COMSOL Joint Readiness Matrix

Date: 2026-06-18

## Disposition

`JOINT_READINESS_MATRIX_DEFINED_NO_JOINT_EXECUTION_AUTHORIZED`

This report turns Report 192's interface contract into a readiness matrix. The
matrix separates what is ready for read-only linkage from what remains blocked
until a separate future authorization gate.

Machine-readable matrix:

`reports/joint_interface_20260618/NODI_COMSOL_JOINT_READINESS_MATRIX_20260618.csv`

## Summary

Ready now:

- PRS read-only import as conditional NODI optical response
- EAS read-only import as dry surrogate sensitivity
- COMSOL geometry descriptor import as nominal dry-surrogate descriptor input
- COMSOL read-only PASS disposition as review evidence
- no-output mapping design for future consumer checks

Not ready now:

- COMSOL transport weighting
- q_ch or q_ch*eta weighting
- yield
- winner
- detection probability
- `JOINT_ROUTE_CLASS` regeneration
- measured geometry, true W_eff, optical solver output, fabrication release, or
  P3 solver conclusions

## Readiness Matrix

| interface item | producer | consumer | current status | allowed now | blocked until |
|---|---|---|---|---|---|
| PRS production CSV | NODI | COMSOL/joint consumer | ready_read_only | import, schema check, row arithmetic, key mapping | COMSOL transport weighting authorization |
| EAS production CSV | NODI | COMSOL/joint consumer | ready_read_only | import, surrogate-mode comparison, key mapping | true W_eff or solver-claim authorization |
| EAS selector policy JSON | NODI | joint consumer | ready_read_only | verify nominal smooth 85 degree policy | measured-geometry or fabrication-release authorization |
| COMSOL geometry descriptor V1 | COMSOL descriptor side | NODI/joint consumer | ready_as_nominal_surrogate_input | descriptor join-key check | measured-geometry authorization |
| COMSOL read-only PASS disposition | COMSOL reviewer | NODI/joint governance | ready_as_review_evidence | cite no-correction review result | any execution or claim-upgrade authorization |
| PRS candidate SHA match | NODI | joint governance | ready_read_only | prove production PRS equals validated candidate | none for read-only use |
| xz_norm_2d rows | NODI | joint consumer | diagnostic_only | read as diagnostic/context | explicit promotion policy plus adequate support |
| edge_norm_1d rows | NODI | joint consumer | primary_conditional_response | read as primary conditional response | transport weighting authorization |
| q_ch / flow split sidecar | COMSOL future lane | joint consumer | missing_blocked | none | explicit q_ch sidecar authorization |
| transported position distribution | COMSOL future lane | joint consumer | missing_blocked | none | explicit COMSOL transport authorization |
| JRC output | joint future lane | downstream consumer | not_generated_blocked | no-output dry mapping only | explicit JRC regeneration authorization |
| yield / winner output | joint future lane | downstream consumer | not_authorized_blocked | none | explicit yield/winner authorization after required inputs exist |

## Consumer Checklist

Any downstream consumer of the current artifacts must pass these checks before
claiming readiness:

```text
1. Confirm PRS SHA256 equals e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e.
2. Confirm EAS SHA256 equals 35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc.
3. Confirm selector policy SHA256 equals 399e34aa40279c0fc47a335685ddedd6b159f98a1786bb03b3cb13b20466ad32.
4. Confirm review package SHA256 equals b7924da8896bee47ac85052b329eeae65efe8adc11cc130eaed3104a934a4b6a.
5. Confirm PRS row_scope=response_surface_bin and neutral flow_condition_id only.
6. Confirm PRS not_comsol_transport_distribution, not_qch_weighted, not_yield,
   and not_detection_probability remain true.
7. Confirm EAS not_true_W_eff, not_measured_geometry, not_optical_solver_output, not_fabrication_release, not_yield, and not_winner remain true.
8. Confirm xz_norm_2d rows are diagnostic only.
9. Confirm no JRC output path is written.
10. Confirm no weighted scores, yield, winner, or detection probability are computed.
```

## Efficient Execution Path

The next implementation should be one narrow tool, not a pile of unrelated
checks:

```text
tools/audits/verify_nodi_comsol_joint_readiness.py
```

Expected behavior:

- read the matrix
- verify the current PRS/EAS/selector/report hashes
- run the existing PRS/EAS validators
- scan for authorization flags that accidentally became true
- write one readiness report
- never run COMSOL
- never write `JOINT_ROUTE_CLASS`
- never compute weights, yield, winner, or detection probability

This keeps automation subordinate to the interface contract rather than making
the automation itself the main project.
