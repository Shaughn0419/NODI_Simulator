# NODI Sidewall Package C Candidate Exchange RC2

Disposition: `PASS_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_READY_FOR_COMSOL_REINTAKE_NO_PROOF_REGISTRATION`.

This package converts Gate30/31 candidate metrics and Gate32 research handoff into a COMSOL-facing candidate exchange packet. It explicitly closes COMSOL PCCR's stale fail-closed observation as a time-delta, while preserving no-proof-registration boundaries.

## Core Counts

- Current NODI head: `a4757d6d4e3ea48316bf8806de4236770a20c28d`
- Gate32 clean successor verdict: `CLOSED_BY_GATE32_CLEAN_SUCCESSOR_A4757D6`
- COMSOL PCCR stale fail closed: `True`
- Scenario metrics: `216` total, `198` open candidate, `18` blocked.
- dt-halving rows: `66`.
- Mutation row-equivalent total: `300000`; unexpected pass `0`; authorization promotion `0`.

## Boundary

All metric pass language is normalized to `candidate_pass_not_proof`. The package does not authorize proof registration, Package C pass status, runtime, production, PRS/EAS numeric output, COMSOL launch, `.mph` load, q_ch, JRC, route score, rank, yield, winner, or detection probability.
