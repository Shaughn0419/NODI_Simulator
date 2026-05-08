# EV/NODI Realism v2 Failure Mode Dashboard Template

> Current status: early-stage dashboard template retained for contract history. It is not the current v2 status table; current v2 closure is in `reports/87_*`.

| Gate | Status | Evidence | Required Action |
|---|---|---|---|
| v1 compatibility no-op | pending | route key separation test | Do not alter v1 full-grid outputs |
| claim/module enums | pending | contract test | Fix schema before running sidecars |
| Mie-to-power units | pending | `mie_to_power_unit_check.csv` | Block detector-unit interpretation if watts fail |
| BFP ROI operator | pending | unit tests | Review Jacobian, NA clip, and signed cross term |
| ET2030 state machine | pending | `detector_connection_state_machine_summary.csv` | Block invalid current-input direct path |
| detector SNR claim | pending | micro-anchor summary | Keep `absolute_blocked` until measured detector transfer plus blank |
| laser/DAQ provenance | pending | schema validation | Add source, unit, and claim metadata |
| blank rare tail | pending | `blank_rare_tail_check.csv` | Use analytic/semi-analytic tail, not finite zero-event safety |
| 404 thermal gate | pending | micro-anchor summary | Never promote optical score from thermal sidecar |
| run manifest | pending | `run_manifest.json` | Require checksums before any promote decision |
| scenario cap | pending | `smoke_run_cost_estimate.csv` | Do not run R2 if cap exceeded |
