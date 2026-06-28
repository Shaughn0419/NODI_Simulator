# Report 204 - NODI/COMSOL Gate2E Receiver Policy Verdicts

Date: 2026-06-28

## Disposition

`PASS_GATE2E_RECEIVER_POLICY_VERDICTS_NO_ACCEPTED_ROW_EXPANSION_NO_WEIGHTING_NO_JRC`

Gate2D accepted ledger is frozen at exactly four W800/D900/300 aggregate proxy context-only rows. Gate2E only records receiver-side policy verdicts for EDGE, QCH, and BINDING; it does not add accepted rows.

## EDGE Verdict

`EDGE_REVIEW_CAN_START_WITH_NODI_EDGE20_HASHED_DEFINITION`, but `EDGE_POLICY_NOT_APPROVED_FORMULA_USE_FALSE` and `EDGE_BLOCKED_MISSING_LOSS_ERROR_SEMANTICS` remain active. edge4 rows are not accepted and direct PRS edge20 bin use is not authorized.

## QCH Verdict

`QCH_FORMAL_RECEIPT_SCHEMA_READY_BUT_NO_FORMAL_SIDECAR_PRESENT`. Current q_ch provenance stays quarantine/review-only and is not formal q_ch / flow-split receipt.

## BINDING Verdict

220 nm remains blocked with no auto-map. D1200/300 remains blocked/uncertain and cannot borrow D900. TPD source/alignment rows missing NODI_view fail closed.

## Output Hashes

- evidence register: `11a5c28135b6b6e27d9b564690052f9eda003ac2a06cd71dd1f7c876981e7b80`
- EDGE verdict: `85ffb9c49dabe72d3529b44b6954093b0b207066125c5cd65fdd1fb1ef5161ed`
- QCH verdict: `2355633ff549b903fd5cbd05cbba8e07c68bb30f356f7f9cfcd58f154606e616`
- BINDING verdict: `ef9a76a699dfcfd6bc8044ffb209a6c4c26972713d7c52da646c05499d05a04f`
- dashboard: `1981bc5cdcd516465534f20c4cfa5c375d7a13982020f58b5d9a0368685758ca`
- JSON report: `f692c42c257eb5a2726af235841523bda4ba3cbbfe1ab58807dd27db64f303ae`

## Non-Authorization

This report does not authorize q_ch weighting, q_ch*eta, q_ch*chi*eta, chi_selected, route_score, JOINT_ROUTE_CLASS/JRC, yield, winner, detection_probability, wet pass probability, clogging rate, runtime configuration, or production ingestion.
