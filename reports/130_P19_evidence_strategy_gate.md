# P19 Evidence Strategy Gate

Date: 2026-05-18

Status: pre-measurement Level-1 gate for the no-measured-data 3 seeds x 10000e run. This report authorizes the scientific scope of the planned Level-1 relative/proxy route-ranking run, but it does not launch the run.

Correction note (2026-05-18): this P19 gate covers the 9-family carry-forward candidate run only. It is not an authorization for the exhaustive EV+gold full grid over all canonical particle sizes, 4 wavelengths, and all width/depth apertures. For that corrected exhaustive scope, see `reports/137_exhaustive_full_grid_scope_correction_audit_20260518.md`.

## Gate Decision

P19 decision: conditionally authorized for the declared Level-1 no-measured-data scope, blocked for launch until the final freeze/prelaunch closure is regenerated or explicitly accepted with the documented dirty-state exception below.

The planned full run must not be started by this report or by copying a command from a report. It may only be launched later if the user explicitly asks for it, the final prelaunch state is clean or auditable, and the runner command includes the P19 confirmation flag `--confirm-p19-level1-launch`.

Measured artifacts are later-plan items. Missing measured detector transfer, standard-particle ladder, raw blank trace, pressure-flow trace, measured BFP/reference, and EV/control-matrix biology artifacts do not block this no-measured-data Level-1 run. They do block Level-2+ claims.

## Evidence Inventory Sanity

Schema sanity is complete.

- `library_engineering_evidence_ledger.csv` uses `engineering_axis`; there is no `axis` column.
- `library_engineering_matrix.csv` has no `engineering_relevance` column; P19 audits the existing `primary_engineering_use` and `main_boundary` fields instead of inventing a new schema field.
- Ledger counts were rechecked: 2035 rows total; source types are 800 numeric hooks, 625 source sentences, 481 captions, 89 layout candidates, 29 machine-table CSV rows, and 11 OCR candidates.
- Axis counts were rechecked: EV scatter/RI 717, POD/photothermal 585, NODI geometry/readout 461, detector threshold 158, flow/nanofluidics 109, Mie/material optics 3, sample-prep biology 1, standards reporting 1.
- Downstream P19 artifacts must not refer to nonexistent `axis` or `engineering_relevance` columns.

## Level-1 State

| State | P19 status | Meaning |
|---|---|---|
| Capability | reached | Formula-chain, governance, run-plan, and evidence-boundary machinery support no-measured-data relative/proxy route ranking. |
| Release-ready | conditional | Evidence map, critical binding, POD/contaminant/event decisions, and binding test now exist; launch still needs final freeze/prelaunch closure. |
| External claim | not yet public-release | Until the run and post-run report exist, only capability and prelaunch readiness can be described. |

After final launch closure, the only allowed Level-1 claim is:

> Within the declared lens, normalization, reference route, detector route, threshold, and readout semantics, this no-measured-data simulator supports relative/proxy route ranking.

## Allowed Wording

- "No-measured-data Level-1 relative/proxy route-ranking run."
- "Within the same lens, same normalization, same reference route, same detector route, same threshold source, and same readout route, candidate families are compared as engineering proxies."
- "All-crossing and selected-annulus outputs are parallel audit lenses."
- "Selected-annulus is an event-position window, not an optical BFP annulus."
- "Formal route geometries and particle classes are engineering defaults unless individually confirmed in `critical_paper_target_binding.csv`."
- "POD, contaminants, and event-arrival are scoped decisions for interpretation, not calibrated scoring upgrades."

## Forbidden Wording

- calibrated SNR, absolute LOD, detector voltage, photon count, true event probability, true concentration, empirical blank false-positive rate, biological EV specificity, calibrated cross-wavelength superiority, or route promotion.
- "Selected-annulus improves optical BFP collection."
- "The route is calibrated."
- "660 nm is physically best across wavelengths."
- "POD amplitude is quantitatively predicted."
- "Contaminant stress promotes or demotes robust route families."
- "Synthetic fixtures or route results replace measured calibration."

## Explicit Run Inventory

Run plan checked: `results/pre3seed_formal_3seed_10000e_run_plan.csv`.

Current parsed inventory:

- Rows: 27.
- Candidate families: 9.
- Seeds: 11, 22, 33.
- Events per case: 10000.
- Planned sustained-run worker count: 16.
- Expected particle panel size: 19.
- Expected event count per seed-route: 190000.
- Expected diagnostic snapshot: `pre3seed_formal_3seed_10000e_diagnostic_snapshot.jsonl`, one case-level row per raw summary row, with large per-event arrays summarized.
- Lens policy: `parallel_all_crossing_and_selected_annulus_outputs`.
- Normalization: `per_wavelength_raw_scope; fixed_660_requires_separate_scope`.
- Reference route: `channel_angular_surrogate_formal_freeze`.
- Detector route: `joint_overlap_coherent_surrogate_formal_freeze`.
- Threshold source: `gaussian_iid_surrogate_not_empirical_blank`.
- Readout route: `EV_NODI_only_design_lockin_surrogate`.
- Count prediction: `not_applied_per_event_only`.
- Claim level in plan: `formal_run_plan_no_results`.
- Selected-annulus boundary: `selected-annulus event-position window, not optical BFP annulus`.

P19 consistency rule: launch is blocked if the run plan is missing, has a row count other than 27, has candidate/seed duplicates, changes events per case away from 10000, changes expected particle panel size away from 19, omits either all-crossing or selected-annulus output, omits the diagnostic snapshot sidecar, or changes any route/normalization/threshold/readout field without a new P19 review. After launch, the diagnostic snapshot row count must match raw summary rows; it is for rerun avoidance and process audit, not for calibrated claims.

## Candidate Family Rationale

| Family | Role | Level-1 rationale |
|---|---|---|
| `main_660_W800_D1400` | primary relative candidate | Robust relative candidate under current surrogate reference/detector route. |
| `main_660_W800_D1500` | primary relative candidate | Depth-neighbor check for main 660 nm behavior without claiming absolute calibration. |
| `historical_488_W600_D1500` | conditional candidate | Historical comparator retained for sensitivity to reference/top-k conditioning. |
| `historical_532_W600_D1500` | conditional candidate | Historical comparator retained for paper-adjacent wavelength context and reference sensitivity. |
| `wide_660_W1100_D1400` | conditional candidate | Width stress/neighbor route retained to check robustness around the main 660 family. |
| `optional_900_660_W900_D1400` | stress branch | Optional 660 nm wider route retained as stress branch, not as main-route replacement. |
| `shortwave_404_W600_D1300` | conditional candidate | Short-wavelength stress branch with exposure/transfer blockers kept visible. |
| `less_narrow_404_W700_D1400` | conditional candidate | Less-narrow 404 nm branch retained for shortwave sensitivity, not promotion. |
| `narrow_404_W500_D1500` | stress branch | Narrow/wall-risk branch retained to expose wall/transport and full-wave blockers. |

## Particle Panel Rationale

The formal panel remains the existing 19-particle panel in `nodi_simulator/pre3seed_hardening.py`; P19 does not modify it.

| Particle class | Count | Level-1 rationale |
|---|---:|---|
| Au anchors | 4 | Standard-particle optical anchors for relative material/size sensitivity; no detector-transfer calibration. |
| EV-like nominal and large-tail surrogates | 5 | Optical EV-like design priors, not biological EV identity. |
| EV-like low-RI surrogates | 3 | Low-RI stress for weak scatter/RI uncertainty. |
| EV-like high-RI corona | 1 | High-RI/corona sensitivity branch. |
| Existing contaminant comparators | 3 | Existing comparator particles stay in the frozen formal panel; no new stress scoring lens is added. |
| PS/silica controls | 2 | Non-EV bead controls for optical contrast context only. |
| Doublet proxy | 1 | Aggregate/doublet optical stress proxy; no population inference. |

Additional contaminant stress particles are recorded separately in `configs/preflight/contaminant_stress_diagnostic_manifest_p19_20260518.csv` and excluded from formal full-run scoring.

## Evidence-to-Config Binding

P19 creates:

- `papers/analysis_full_v1/paper_evidence_to_config_gap.csv`
- `papers/analysis_full_v1/critical_paper_target_binding.csv`
- `reports/131_critical_paper_table_extraction_gap.md`
- `tests/test_critical_paper_binding_integrity.py`
- `reports/136_pre3seed_full_run_coverage_rerun_risk_audit.md`

Binding policy:

- Machine-table rows are seeded but remain blocked until original-page review confirms table semantics and units.
- Layout/OCR candidates are context-only until original-page verified.
- Critical-paper rows are either `bound`, `not_parameterizable`, `deferred_to_measured_plan`, or `engineering_default_unconfirmed_against_paper`.
- Current formal route geometries and Gaussian IID threshold semantics are explicitly engineering defaults unless individually confirmed.
- No simulator self-fit, reverse-engineering, or route-result back-solving is allowed.

## POD Scope Decision

Decision: POD is out-of-scope for the current no-data NODI full-run scoring lens.

The 585 POD/photothermal evidence rows are preserved as future POD evidence. They do not change the current full-run scoring lens and do not authorize quantitative POD amplitude, sign, LOD, absorption, or thermal claims.

Detailed decision: `reports/132_pod_scope_decision.md`.

## Contaminant Stress Decision

Decision: `separate_diagnostic_manifest`.

P19 does not add any new contaminants to `PARTICLE_PANEL`, does not refreeze the formal particle panel, and does not add a contaminant stress scoring lens to the 3 seeds x 10000e run. Existing comparator/control particles in the formal 19-particle panel remain as already frozen, but additional stress proxies are diagnostic-only and excluded from robust route promotion.

Manifest: `configs/preflight/contaminant_stress_diagnostic_manifest_p19_20260518.csv`.

## Event-Arrival Decision

Decision: excluded from current full-run scoring.

The formal run keeps `count_prediction_status=not_applied_per_event_only` and uses existing relative route scoring. No `nodi_simulator/event_arrival.py` implementation is required before this full run. P19 forbids concentration, LOD, true event probability, count-rate, and empirical blank-rate claims.

## Freeze Closure

Existing freeze manifest checked: `results/pre3seed_freeze_manifest_20260518.json`.

Current known issue: the manifest records `git_dirty_state.status=dirty` and predates this P19 pre-measurement package. The current worktree also contains unrelated/historical dirty files plus the new P19 artifacts. P19 therefore documents a dirty-state exception but does not pretend the launch state is clean.

P19 freeze-closure audit snapshot: `results/pre3seed_p19_premeasurement_freeze_closure_audit_20260518.json`.

Freeze closure requirement before launch:

1. Create a clean commit or an explicitly accepted audited snapshot that includes the P19 artifacts.
2. Regenerate or update the prelaunch manifest so it records the exact run plan, P19 files, binding CSVs, tests, and dirty-state exception.
3. Confirm the manifest hash and exact command/template in the post-run outline.
4. Confirm that `results/pre3seed_formal_3seed_10000e_prelaunch_manifest.json` contains `launch_authorization_contract.contract_version=pre3seed_level1_no_measured_data_launch_contract_v1`, P19 artifact hashes, `planned_worker_count=16`, and the required execute flags `--execute`, `--allow-large-run`, and `--confirm-p19-level1-launch`.

Until this closure exists, launch remains blocked even though the scientific run inventory is accepted.

## Readiness Checklist

| Item | Status |
|---|---|
| WP0 evidence schema sanity | complete |
| WP0.5 freeze closure | blocked pending regenerated/accepted freeze snapshot |
| WP1 P19 gate | complete |
| WP2 paper evidence to config gap map | complete |
| WP3 critical target binding | complete |
| WP3.5 binding integrity test | complete, targeted test passing |
| POD scope decision | complete, out-of-scope |
| Contaminant decision | complete, separate diagnostic manifest |
| Event-arrival decision | complete, excluded from scoring |
| Level-1 wording lock | complete |
| Run command/template recorded | exact command template recorded in `results/pre3seed_formal_3seed_10000e_prelaunch_manifest.json`; it must include `--confirm-p19-level1-launch` and `--workers 16`, and is reproduced in release report outline §4 for human readability |
| No-measured-data label | complete |
| Release report outline | complete |

Verification completed in this turn:

- `python -m pytest tests/test_critical_paper_binding_integrity.py tests/test_pre3seed_hardening.py tests/test_pre3seed_physics_invariants.py -q`: 32 passed.
- `python tests/run_tests.py --workers 7`: AppTest lane 5 passed; parallel lane 1390 passed.

## Authorization Line

P19 accepts the no-measured-data Level-1 scientific run inventory in `results/pre3seed_formal_3seed_10000e_run_plan.csv` as the intended 3 seeds x 10000e scope, but launch is not authorized from the current dirty/unrefreshed freeze state. Before execution, regenerate or explicitly accept the freeze/prelaunch manifest, confirm the P19 launch contract and artifact hashes, then launch only if the user explicitly requests the full calculation.
