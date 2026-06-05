# Pre-3seed Full-Run Coverage and Rerun-Risk Audit

Date: 2026-05-18

Status: pre-launch audit only. The formal 3 seeds x 10000e full calculation has not been run.

Correction note (2026-05-18): this report audits the P19 candidate-family formal run only. It must not be interpreted as the exhaustive full-grid campaign over all canonical EV+gold particle sizes, 4 wavelengths, and all width/depth apertures. For that corrected scope, see `reports/137_exhaustive_full_grid_scope_correction_audit_20260518.md`.

## Verdict

For the current P19 Level-1 no-measured-data relative/proxy route-ranking scope, the planned full run is computationally complete after adding the diagnostic snapshot sidecar.

The current plan covers:

- 9 formal candidate/stress families.
- 3 seeds: 11, 22, 33.
- 19-particle formal panel.
- 10000 synthetic crossing events per route/seed/particle case.
- 513 route/seed/particle cases and 5130000 synthetic events.
- parallel all-crossing and selected-annulus event-position-window analysis.
- per-wavelength normalization only, with fixed-660 treated as a separate future scope.
- frozen reference, detector, threshold, and readout routes.
- raw summary, route-claim matrix, claim scan, diagnostic JSONL snapshot, dual-lens top table, pooled per-seed consistency, and postrun manifest.

The current plan does not try to cover Level-2+ measured claims, count-rate/LOD claims, quantitative POD, full-wave replacement, measured detector units, or biological EV specificity. Those omissions are intentional and do not block this Level-1 run.

## Evidence Checked

- Run plan: `results/pre3seed_formal_3seed_10000e_run_plan.csv`
- Prelaunch manifest: `results/pre3seed_formal_3seed_10000e_prelaunch_manifest.json`
- P19 gate: `reports/130_P19_evidence_strategy_gate.md`
- Release outline: `reports/135_pre3seed_10000e_level1_release_report.md`
- Carry-forward manifest: `results/candidate_family_carry_forward_manifest.csv`
- Candidate manifest: `results/pre3seed_candidate_set_manifest.csv`
- Formal runner: `tools/run_pre3seed_3seed_10000e_from_manifest.py`
- Formal helpers: `nodi_simulator/pre3seed_hardening.py`

## Included Route Families

The formal run includes all P19-authorized large-run families:

- `main_660_W800_D1400`
- `main_660_W800_D1500`
- `historical_488_W600_D1500`
- `historical_532_W600_D1500`
- `wide_660_W1100_D1400`
- `optional_900_660_W900_D1400`
- `shortwave_404_W600_D1300`
- `less_narrow_404_W700_D1400`
- `narrow_404_W500_D1500`

These cover the current robust, conditional, shortwave, historical, wide, optional, and narrow/wall-risk route questions.

## Deliberately Excluded Route Families

Three carry-forward rows remain `diagnostic_only` and are not in the formal 10000e run:

- `au_control_660_W1200_D550`
- `reference_edge_660_W700_D1500`
- `tsuyama_like_660_W800_D550`

This is acceptable for the current P19 scoring scope because they are not allowed to promote or demote robust route families. They remain covered by preflight diagnostic matrices, not by full 10000e event budgets.

Rerun-risk note: if the desired deliverable later asks for formal 10000e event-level evidence on Tsuyama-like shallow geometry, Au shallow control geometry, or reference-edge weak-reference behavior, these three families would need either a separate diagnostic full run or a revised 12-family formal run before launch. Adding them now would increase the formal case count from 513 to 684 and the event count from 5130000 to 6840000, about a 33 percent increase.

My judgment: do not add them by default for Level-1 route ranking. Consider adding them only if the project wants maximum diagnostic insurance and accepts the 33 percent extra compute cost.

## Included Particle Panel

The full run uses the frozen 19-particle panel:

- 4 Au anchors: 20, 30, 40, 60 nm.
- 5 EV-like nominal/large-tail particles: 40, 70, 100, 150, 300 nm.
- 3 EV-like low-RI particles: 70, 100, 150 nm.
- 1 EV high-RI corona particle.
- 3 existing contaminant comparators: liposome-like, protein-aggregate-like, lipoprotein-like.
- 2 PS/silica controls.
- 1 EV doublet proxy.

Additional contaminants remain in `configs/preflight/contaminant_stress_diagnostic_manifest_p19_20260518.csv` and do not enter robust route promotion.

Rerun-risk note: if the project decides to promote additional contaminant proxies into the formal scoring panel, the run plan and P19 inventory must change before launch.

## Included Lenses and Analysis Outputs

The formal raw summary exports both:

- all-crossing denominator and detection fraction.
- selected-annulus event-position-window denominator and detection fraction.

The postprocess creates:

- `pre3seed_formal_3seed_10000e_dual_lens_top_table.csv`
- `pre3seed_formal_3seed_10000e_pooled_per_seed_consistency.csv`
- `pre3seed_formal_3seed_10000e_postrun_manifest.json`

The selected-annulus output remains an event-position window, not an optical BFP annulus.

## Process-Quantity Coverage

Before this audit, the formal raw summary was a stable 48-column CSV focused on ranking, denominators, seeds, route identity, and claim boundaries. That is enough for Level-1 ranking, but too thin for later process-level review.

The runner now also writes:

- `pre3seed_formal_3seed_10000e_diagnostic_snapshot.jsonl`

This JSONL sidecar stores one case-level diagnostic snapshot per route/seed/particle row. It preserves summary/reference/result diagnostics as JSON-safe values and summarizes large per-event arrays rather than writing unbounded traces. Its purpose is rerun avoidance and process audit, not calibrated evidence.

Residual rerun-risk note: if future analysis needs individual event traces or full per-event trajectories rather than summarized arrays, the formal run would still need a different trace-retention mode. That is intentionally not enabled for the current full run because it would greatly increase output volume and is not needed for Level-1 ranking.

## Parameters Frozen for This Run

- `events_per_case=10000`
- `seeds=11,22,33`
- `normalization_mode=per_wavelength`
- `random_sequence_policy=case_keyed_independent`
- `event_sampling_policy=stratified_grid`
- `adaptive_event_budget_mode=fixed`
- `vectorized_event_engine=off`
- `n_workers=16` for the sustained formal calculation
- reference route: `channel_angular_surrogate_formal_freeze`
- detector route: `joint_overlap_coherent_surrogate_formal_freeze`
- threshold source: `gaussian_iid_surrogate_not_empirical_blank`
- readout route: `EV_NODI_only_design_lockin_surrogate`
- count prediction: `not_applied_per_event_only`

Changing any of these after launch should be treated as a new scope, not as the same run. In particular, changing the worker count away from 16 after prelaunch closure would require P19/freeze refresh before accepting outputs as the same Level-1 run.

## What Would Require a New Run

A new run would be required if any of these decisions change:

- include the 3 diagnostic-only route families in the formal event budget.
- add extra contaminant particles into the formal `PARTICLE_PANEL`.
- change seeds, event budget, event sampling policy, vectorization, worker/chunk order, or random sequence policy.
- make fixed-660 normalization part of the same rank scope.
- replace the frozen reference/detector/readout/threshold route with another scoring route.
- add event-arrival, count-rate, concentration, coincidence, or LOD claims.
- add quantitative POD scoring.
- require full event traces instead of case-level diagnostic snapshots.
- use measured artifacts for Level-2+ calibration.

## Launch Readiness Judgment

Computational content readiness for current Level-1 scope: yes, with the diagnostic snapshot sidecar now included.

Launch authorization: still no. The full run remains blocked until final clean or explicitly accepted freeze/prelaunch closure and explicit user launch authorization.

Best pre-launch decision still open:

- Keep current 9-family run for focused Level-1 ranking.
- Or revise to a 12-family coverage-expanded run if the project values diagnostic insurance more than the 33 percent extra cost.
