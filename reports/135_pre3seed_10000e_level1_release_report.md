# Pre-3seed 10000e Level-1 Release Report Outline

Date: 2026-05-18

Status: outline only. The formal 3 seeds x 10000e full calculation has not been run.

Correction note (2026-05-18): this outline is for the P19 9-family candidate run, not the exhaustive EV+gold full grid. Do not use its command as the launch command for "all particle sizes x 4 wavelengths x all apertures x 3 seeds x 10000e". Use `reports/137_exhaustive_full_grid_scope_correction_audit_20260518.md` and `tmp/exhaustive_full_grid_3seed_10000e_launch_prompt_20260518.md` for the corrected exhaustive scope.

This file is the post-run report scaffold required before a completed full run can be treated as human-readable Level-1 release evidence.

## 1. P19 Authorization Line

To fill after launch:

- P19 source: `reports/130_P19_evidence_strategy_gate.md`
- Authorization status at launch:
- Any freeze/prelaunch exception accepted:
- Statement that the run is no-measured-data, relative/proxy, and non-calibrated:

## 2. Run Inventory

To fill from the launch manifest and run plan:

- Run plan path:
- Run plan hash:
- Candidate families:
- Seeds:
- Events per case:
- Particle panel size:
- Lens policy:
- Normalization:
- Reference route:
- Detector route:
- Threshold source:
- Readout route:
- Count prediction status:
- Claim level:
- Diagnostic snapshot schema:

## 3. Freeze / Prelaunch Manifest

To fill after final prelaunch closure:

- Manifest path:
- Manifest hash:
- Git commit hash or documented dirty-state exception:
- Input hashes included:
- P19 artifact hashes included:
- Launch contract version:
- Required execute flags confirmed:
- Verification command and result:

## 4. Exact Command / Template

Pre-filled from `results/pre3seed_formal_3seed_10000e_prelaunch_manifest.json`
field `exact_command_template`. This remains a template only; do not execute it
from this outline without explicit user launch authorization and final
freeze/prelaunch closure. The P19 confirmation flag is intentionally part of
the command so that `--execute --allow-large-run` alone cannot start the
formal run.

```bash
python tools/run_pre3seed_3seed_10000e_from_manifest.py --execute --allow-large-run --confirm-p19-level1-launch --events-per-case 10000 --seeds 11,22,33 --workers 16
```

## 5. Dual-Lens Top-Table Summary

To fill from full-run outputs:

- raw summary path and hash:
- diagnostic snapshot JSONL path and hash:
- diagnostic snapshot row count equals raw summary rows:
- run manifest records `n_workers=16`:
- diagnostic snapshot caveat: process audit only, not calibrated evidence:
- all-crossing top table:
- selected-annulus top table:
- lens agreement/disagreement:
- normalized scope boundaries:

## 6. Pooled Per-Seed Consistency

To fill from full-run outputs:

- per-seed rank stability:
- pooled consistency:
- fragile candidates:
- stress/conditional branches:

## 7. All-Crossing vs Selected-Annulus Boundary

Required wording:

Selected-annulus is an event-position window, not an optical BFP annulus. It does not replace all-crossing, and all-crossing does not replace selected-annulus.

To fill after run:

- all-crossing conclusion:
- selected-annulus conclusion:
- cross-lens caveat:

## 8. WP2 Evidence-to-Config Completeness

Current prelaunch source:

- `papers/analysis_full_v1/paper_evidence_to_config_gap.csv`

To fill:

- row counts by review status:
- machine-table rows:
- layout/OCR candidate rows:
- critical binding rows:
- remaining original-page checks:

## 9. WP3 Critical Binding Completeness

Current prelaunch source:

- `papers/analysis_full_v1/critical_paper_target_binding.csv`
- `reports/131_critical_paper_table_extraction_gap.md`

To fill:

- critical papers covered:
- rows by binding status:
- `engineering_default_unconfirmed_against_paper` summary:
- self-fit/back-solving confirmation:

## 10. Scope Decisions

Prelaunch decisions:

- POD: out-of-scope for current no-data NODI scoring; future POD evidence retained.
- Contaminant stress: separate diagnostic manifest; no new `PARTICLE_PANEL` change; no stress-lens promotion/demotion.
- Event-arrival: excluded from current scoring; no concentration, count-rate, LOD, or true event probability claim.

To fill after run:

- confirm no POD/contaminant/event-arrival scoring lens was introduced:
- confirm no formal particle-panel refreeze occurred unless explicitly authorized:

## 11. Allowed / Forbidden Level-1 Wording

Allowed:

- no-measured-data Level-1 relative/proxy route ranking
- same-lens, same-normalization, same-reference, same-detector, same-threshold, same-readout comparison
- all-crossing and selected-annulus as parallel audit lenses

Forbidden:

- calibrated SNR
- absolute LOD
- detector voltage
- photon count
- true event probability
- concentration
- empirical blank false-positive rate
- biological EV specificity
- calibrated cross-wavelength superiority
- POD quantitative amplitude
- contaminant stress route promotion

## 12. Remaining Caveats and Later Measured-Plan Handoff

To fill:

- measured detector transfer:
- standard-particle ladder:
- raw blank trace:
- pressure-flow trace:
- measured BFP/reference:
- EV/control-matrix biology artifacts:
- POD thermal model:
- event-arrival/count-rate calibration:

## 13. Final Release Verdict

To fill after full run and verification:

- Level-1 release evidence status:
- residual blockers:
- next recommended action:
