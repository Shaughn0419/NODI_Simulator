# Lens-B τ=1 ms recalibration roadmap

- Date: 2026-05-14
- Scope: Criterion B / 口径 B only
- Current rule: Criterion B runtime lock-in time constant is fixed at `τ = 1 ms`
- Current status: the completed `results/lens_b_ev_gold_fullgrid_1seed_20260513/` run is a real completed full-grid, but it used `lockin_time_constant_s = 0.002`; it is now legacy 2 ms sensitivity/reference evidence. A current `τ=1 ms` Stage B6 EV+gold full-grid has since completed at `1000 events/case` in `results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514/`; it is low-event full-grid design evidence, not the planned `10000 events/case` final-validation run.

## New-thread quick start

If a new thread starts from this file, it should do the following in order:

1. Read `AGENTS.md` and this roadmap.
2. Treat Stages B0-B5 as completed targeted/diagnostic work and Stage B6 as completed at low event count (`1000 events/case`).
3. Verify the current state with the commands below before changing any recommendation wording.
4. Do not treat Stage B5 targeted evidence as final B=1 ms full-grid recommendation evidence.
5. Do not relabel the Stage B6 `1000 events/case` result as the planned `10000 events/case` final-validation run. Use it for current design optimization; run 10k only if final-validation strength is required.

Current source-of-truth files:

| File | Role |
|---|---|
| `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md` | Current reader-facing report; v5.2.8 overlay should read the Stage B6 1000e full-grid as low-event 1 ms design evidence |
| `reports/125_lens_b_tau1ms_recalibration_roadmap_2026-05-14.md` | This execution roadmap |
| `tools/lens_b_ev_gold_fullgrid_runner.py` | Future B runner; should emit `lockin_time_constant_s = 0.001` |
| `tools/analyze_lens_b_ev_gold_fullgrid.py` | Derived-analysis script; labels 1000e as low-event design evidence and non-1ms rows as legacy/reference |
| `results/lens_b_ev_gold_fullgrid_1seed_20260513/seed_42_raw_rows.csv` | Completed legacy 2 ms full-grid raw rows |
| `results/lens_b_tau1ms_recalibration_20260514/stage_b5_tau1ms_targeted_ev_probe_3000e_1seed/` | Completed targeted B5 τ=1 ms EV probe; not final full-grid evidence |
| `reports/126_lens_b_tau1ms_stage_b5_targeted_probe_note_2026-05-14.md` | Short fixed note for the completed Stage B5 conclusion and next action |
| `results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514/` | Completed current τ=1 ms Stage B6 EV+gold full-grid at 1000 events/case |
| `reports/127_lens_b_tau1ms_stage_b6_1000e_fullgrid_note_2026-05-15.md` | Short fixed note for the completed Stage B6 1000e result and design read |

Minimal verification before starting new work:

```bash
python -m py_compile tools/lens_b_ev_gold_fullgrid_runner.py tools/analyze_lens_b_ev_gold_fullgrid.py
python tools/analyze_lens_b_ev_gold_fullgrid.py --check-only
python - <<'PY'
import pandas as pd
from tools import lens_b_ev_gold_fullgrid_runner as runner

cfg, _ = runner.build_frozen_b_cfg(10, 42)
assert cfg.lockin_time_constant_s == 0.001

raw = pd.read_csv(
    "results/lens_b_ev_gold_fullgrid_1seed_20260513/seed_42_raw_rows.csv",
    usecols=["lockin_time_constant_s"],
)
assert sorted(raw["lockin_time_constant_s"].unique().tolist()) == [0.002]
print("criterion_b_tau_state_ok")
PY
```

Completed first derived deliverables:

| Deliverable | Description |
|---|---|
| `results/lens_b_tau1ms_recalibration_20260514/tau_1ms_vs_2ms_transit_gain_inference.csv` | No-simulation inference from old 2 ms rows to estimated 1 ms transit gain |
| `results/lens_b_tau1ms_recalibration_20260514/tau_1ms_impact_summary.md` | Short summary of expected changes by particle scope, wavelength, and route family |

These deliverables did not change any recommendation. They only set the breadth of the Stage B2/B5 candidate and probe panels.

Current next action:

| Action | Reason |
|---|---|
| Stage B7 report/metadata synchronization | Stage B6 has completed at 1000 events/case; update report text, metadata, and handoff files so the design read uses this evidence without calling it 10k final validation |

2026-05-14 Ag/Au correction overlay:

| Item | Current handling |
|---|---|
| Corrected Table S1 Ag/Au target | The Table S1 silver interferometric column is used directly as the Ag/Au ratio-like target: `488/532/660 nm = 1.90/0.89/0.85` |
| Legacy over-ratio | The old Ag-column/Au-column quotient `4.222/1.309/2.656` is legacy audit-only and must not be used as the hard acceptance target |
| B3/B4 impact | Stage B3 and B4 acceptance/rescore outputs were rerun with the corrected target; strict signal alignment now passes, diagnostic warnings are empty, but release remains `negative_or_diagnostic_result_only` because raw size-response alignment still fails |
| B5 impact | No change to targeted EV probe ordering: B5 contains EV rows plus gold anchors for continuity, but no Ag rows; 404 still does not overtake 660 |

## 0. Non-negotiable boundaries

| Boundary | Rule |
|---|---|
| τ | Current Criterion B runtime must use `lockin_time_constant_s = 0.001` |
| Scope separation | EV/exosome rows are the only source for EV recommendation; gold rows are anchor/Tsuyama diagnostics only |
| Wavelength recommendation | Raw/control tables keep 404/488/532/660; final recommendation can only choose from 404/660 |
| Selected annulus | Keep selected-annulus 0.5-0.8 fixed unless a separate sensitivity appendix is explicitly requested |
| Claim boundary | All results remain synthetic relative until measured blank, detector transfer, Au raw trace, and EV biological evidence exist |
| Legacy 2 ms results | May be used for impact comparison; must not be relabeled as 1 ms |

## 1. What must be recalibrated

| Parameter / output | Current value / source | Why affected by τ=1 ms | Required action |
|---|---|---|---|
| `lockin_time_constant_s` | Old B full-grid rows: `0.002`; current runner: `0.001` | Direct runtime change; changes lock-in bandwidth and transit attenuation | Fixed to 1 ms in all new B runs |
| D2.1 operator provenance | `tau_2ms_global_refphi_plus_collection_narrow` | Its score was found in a 2 ms search family | Rebuild a 1 ms operator family using the same refphase/collection knobs, not the old score |
| `ref_phi0_rad` | old D2.1: `0.4` | Phase/lock-in readout can move peak/margin and size response after τ change | Refit or confirm under 1 ms |
| `collection_sigma_rad` | old D2.1: `0.08` | Narrow collection interacts with readout amplitude and detection loss | Refit or confirm under 1 ms |
| `collection_phi_sigma_rad` | old D2.1: `0.16` | Same as above | Refit or confirm under 1 ms |
| `slit_phi_limit_rad` | old D2.1: `0.25` | Same as above | Refit or confirm under 1 ms |
| `gamma` | old Phase 2.11: `0.749` | Derived from raw Au exponent under 2 ms | Recompute from 1 ms anchor outputs |
| `snr_scale` | old reproduction lens: `0.728` | SNR anchor changes when peak/noise/readout changes | Recompute from 1 ms anchor outputs |
| `snr_response_exp` | old Phase 2.7: `0.812` | SNR ratio response may change after τ | Recompute or mark obsolete |
| Au size exponent | old raw D2.1 about 3.05-3.19 before compression | Peak heights change under 1 ms | Refit/rescore against target 2.3 |
| Ag/Au signal ratio score | old formula-consistent pass | Peak/readout may shift; formula proxy may remain stable but must be rechecked | Recompute for 1 ms candidates |
| Au30/Au20 SNR ratio | old target 33/12 ≈ 2.75 | SNR ratio depends on peak/margin/noise | Recompute |
| Detection loss / selected-annulus detection | old 2 ms rows | Detection can be ceiling-limited but still changes | Recompute under 1 ms |
| EV B2 ranking | old 2 ms full-grid pointed to 660/800 nm width | 404 benefits more from shorter τ, so relative ranking can move | Re-run B2 after B1 freeze |

## 2. What should stay fixed unless explicitly reopened

| Item | Reason |
|---|---|
| `selected_annulus_edge_norm_min/max = 0.5/0.8` | It defines Criterion B's Tsuyama-selected-annulus lens |
| `threshold_sigma` variants as controlled modes, not free knobs | 5σ and 10σ are readout/detection scenarios; do not tune threshold just to rescue score |
| Particle scope | Gold anchors cannot be mixed into EV recommendation |
| Recommendation wavelength filter | 488/532 remain control/trend-only |
| Per-diameter / per-geometry / per-case correction ban | Prevents overfitting the Tsuyama reproduction lens |
| Criterion A recommendation | A remains the engineering main ranking; B does not overwrite it |

## 3. Recalibration stages

### Stage B0 - Freeze current state and impact inventory

Goal: make sure the project cannot confuse 2 ms legacy evidence with current 1 ms Criterion B.

Actions:
- Assert runner config emits `lockin_time_constant_s = 0.001`.
- Assert old raw rows remain marked as `0.002`.
- Keep old 2 ms results as `legacy_non_1ms_runtime_reference_not_current_final`.
- Produce an affected-fields inventory covering reports, runner metadata, derived analysis, tests, and result manifests.

Exit criteria:
- `tools/lens_b_ev_gold_fullgrid_runner.py` future runtime is 1 ms.
- Derived analysis flags non-1ms rows as legacy reference.
- Report 88 distinguishes the completed B=1 ms 1000e low-event full-grid design evidence from any future 10000e final-validation run.

### Stage B1 - No-simulation analytical impact estimate

Goal: estimate direction and rough magnitude before spending compute.

Actions:
- Use existing 2 ms full-grid rows to infer 1 ms transit-gain change from `mean_nodi_transit_bandwidth_gain`.
- Summarize by particle scope, wavelength, and route family.
- Report expected movement in `mean_peak_height`, `mean_peak_margin_z`, and selected-annulus detection ceiling effects.

Key outputs:
- `tau_1ms_vs_2ms_transit_gain_inference.csv`
- `tau_1ms_impact_summary.md`

Decision:
- If 404 gain becomes plausibly competitive with 660, include more 404 routes in Stage B5 targeted probe.
- This stage never signs final recommendation.

### Stage B2 - Build the 1 ms anchor candidate family

Goal: replace the old `tau_2ms_*` family with an explicitly 1 ms family.

Candidate family should include:
- `tau_1ms_control`
- `tau_1ms_global_refphi_plus_0p2`
- `tau_1ms_global_refphi_plus_0p4`
- `tau_1ms_global_refphi_plus_0p6`
- `tau_1ms_global_refphi_minus_0p4`
- `tau_1ms_collection_narrow`
- `tau_1ms_global_refphi_plus_collection_narrow`
- optionally one `collection_wide` and one `bfp_lobe` diagnostic if guardrails stay clean

Compute level:
- Start with dry run / plan table.
- Then a smoke run, e.g. `2000 events/case`, seeds `42/43/44`, anchor particles only.
- Do not run EV full-grid here.

Metrics:
- `joint_fit_score`
- `joint_fit_score_formula`
- `signal_ratio_score_*`
- `size_exponent_score`
- `snr_ratio_score`
- guardrails: reference/rho/NA, detection loss, hard penalties

Exit criteria:
- A 1 ms candidate family exists with no guardrail confusion.
- Either one best candidate is stable across seeds, or the stage explicitly reports that B=1 ms remains diagnostic-only with no stable operator.

### Stage B3 - Re-estimate reproduction parameters under 1 ms

Goal: recompute all low-DOF estimated parameters from the 1 ms anchor outputs.

Actions:
- Run the Phase 2 acceptance/rescore path on the 1 ms candidate summaries.
- Recompute:
  - `gamma`
  - `snr_scale`
  - `snr_response_exp`
  - required Au size-response delta as diagnostic only
  - reproduction score decomposition
- Keep the same no-overfit rule: one global gamma, one global SNR scale/exponent, no per-size correction as final.

Exit criteria:
- A new B=1 ms parameter set exists, or the report states no acceptable/partial 1 ms parameter set exists.
- Old `gamma=0.749`, `snr_scale=0.728`, `snr_response_exp=0.812` are either replaced, or explicitly retained only as legacy 2 ms provenance.

### Stage B4 - Anchor confirmation at higher event count

Goal: confirm the selected 1 ms anchor candidate before EV full-grid.

Actions:
- Run top 1-3 Stage B2/B3 candidates at higher count, ideally `10000 events/case` and seeds `42/43/44`.
- Keep this anchor-only; do not include full EV library.
- Generate acceptance summary and score decomposition.

Exit criteria:
- Candidate ranking is seed-stable enough to freeze.
- `release_status` is updated honestly:
  - accepted only if score/guardrails pass,
  - bounded partial if close but not passing,
  - diagnostic-only if no stable fit.

### Stage B5 - Targeted EV 1 ms probe before full-grid

Goal: check whether EV ranking behavior changes enough to justify full-grid immediately.

Route panel:
- 660: `800x800`, `800x900`, `800x1300`, `800x1400`, `800x1500`
- 404: `500x550`, `600x1300`, plus any prior 404 sidecar route used in report 88
- 488/532: top control-only references such as `488/600x650`, `532/700x750`
- Weak-reference controls: representative 500 nm width rows to keep the reference-useful filter honest

Particle panel:
- EV/exosome full particle list if cheap enough.
- Gold anchors can be included only for diagnostic continuity, never for EV recommendation.

Metrics:
- selected-annulus detection
- all-crossing detection
- stable detection
- `mean_peak_height`
- `mean_peak_margin_z`
- `mean_nodi_transit_bandwidth_gain`
- reference operating band
- per-prior weighted ranking

Exit criteria:
- If 660/800 remains stable and 404 does not overtake under reference-useful filtering, full-grid can be lower priority.
- If 404/660 order changes or route family shifts, proceed to full-grid before report recommendation.
- 488/532 stay control-only regardless of raw rank.

2026-05-14 completion note:
- Completed targeted probe output directory: `results/lens_b_tau1ms_recalibration_20260514/stage_b5_tau1ms_targeted_ev_probe_3000e_1seed/`.
- Probe size: 14 routes x 31 particles = 434 rows, seed 42, `3000 events/case`.
- Runtime check: every B5 raw row has `lockin_time_constant_s = 0.001`.
- Particle rule: EV/exosome rows drive EV recommendation diagnostics; 4 gold anchor rows per route were included only for continuity diagnostics.
- Route note: the roadmap example `532/700x750` is not present in the route source, so B5 used `532/700x700` as the nearest control-grid substitute and recorded that substitution in the manifest.
- Main result: under reference-useful selected-annulus filtering, 404 did not overtake 660 for any of the four EV priors.
- Recommendation-eligible top in this targeted panel: `660 nm / 800 x 1500 nm` for uniform, small-EV, broad-EV, and sharp MSC-sEV priors.
- Control result: 488/532 can still show high raw/control selected-annulus values, especially `488 nm / 600 x 650 nm`, but remain control/trend-only and cannot enter the final recommendation.
- Exit read: B5 alone is not full-grid evidence; its 660-over-404 wavelength read is now cross-checked by the Stage B6 1000e full-grid result.
- Claim boundary: Stage B5 is targeted evidence only, not B=1 ms final full-grid evidence.
- Ag/Au correction impact: none on the B5 EV ordering; the corrected Ag/Au target only changes B3/B4 anchor acceptance wording/status from formula-only signal pass to strict corrected-interferometric signal pass.

### Stage B6 - B-application EV+gold full-grid at τ=1 ms

Goal: generate the current Criterion B final data product.

Prerequisite:
- Stage B3/B4 must freeze the 1 ms B lens, or explicitly choose a diagnostic-only lens.

Run:
- Same route source as old full-grid.
- EV/exosome + gold.
- Wavelengths 404/488/532/660.
- Seed 42 first. The planned final-validation budget is `10000 events/case`; the completed time-limited run used `1000 events/case`.
- Add 3-seed expansion only after a seed-42 result is internally consistent and only if final-validation strength requires it.

Precheck:
- 32,032 rows for 1 seed.
- `random_seed == 42` for first run.
- `n_events == 1000` for the completed low-event design run, or `n_events == 10000` for a later final-validation run.
- `particle_material in {exosome, gold}`.
- `wavelength_nm in {404,488,532,660}`.
- `lockin_time_constant_s == 0.001` for every row.

Derived outputs:
- EV full-grid route ranking.
- EV recommendation-eligible 404/660 table.
- EV control-only 488/532 table.
- Gold anchor/Tsuyama diagnostic summary.
- A vs B difference table.
- τ=1 ms vs legacy 2 ms comparison table.
- Short markdown analysis report.

2026-05-15 completion note for the time-limited Stage B6 run:
- Completed output directory: `results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514/`.
- Run size: 32,032 rows, seed 42, `1000 events/case`, 32,032,000 particle events, no failures.
- Runtime check: every raw row has `lockin_time_constant_s = 0.001`.
- Analyzer precheck: passed after the analyzer was updated to distinguish 1000e low-event design evidence from 10000e final-validation evidence.
- EV recommendation rule: EV/exosome rows only; gold rows diagnostic-only; final recommendation wavelengths remain 404/660 only.
- Main result: all four EV priors are led by the `660 nm / 800 nm` width family under the reference-useful selected-annulus filter.
- Top routes: `660 / 800 x 1100` for uniform and small-EV priors, `660 / 800 x 1000` for broad-EV, and `660 / 800 x 1400` for sharp MSC-sEV.
- Control result: 488 can still rank high in the control-only table (`488 / 600 x 900`, `488 / 600 x 1100`, `488 / 600 x 1300` depending on prior), but 488/532 remain control/trend-only.
- B5 relationship: B5's wavelength conclusion is confirmed (`404` does not overtake `660`), while the full-grid depth read shifts from the targeted-panel `800 x 1500` toward a broader `800 x 1000-1400` design band.
- Claim boundary: this is low-event current 1 ms full-grid design evidence, not a 10k final-validation run, not a 3-seed consensus, and not measured calibration.

### Stage B7 - Report and metadata synchronization

Goal: prevent stale or mixed claims.

Must update:
- `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`
- `results/.../run_manifest.json`
- derived analysis reports
- `tools/lens_b_ev_gold_fullgrid_runner.py`
- `tools/analyze_lens_b_ev_gold_fullgrid.py`
- any report/metadata that says B full-grid is pending, targeted-only, final 2 ms, or current final without τ=1 ms evidence

Required wording:
- Criterion A remains the engineering main ranking.
- Criterion B is Tsuyama-anchored EV application, not Tsuyama anchor geometry recommendation.
- B1 freezes estimated parameters; B2 applies them to EV.
- Gold rows diagnostic only.
- 488/532 control/trend only.
- Current B result is synthetic relative, not measured SNR/LOD or biological specificity.

### Stage B8 - Measured artifact gate

Goal: separate synthetic recalibration from physical calibration.

Minimum artifacts:
- measured Au raw traces for 20/30/40/60 nm under B geometry/readout
- measured blank and false-alarm characterization
- measured BFP/slit/ROI or detector transfer artifact
- lock-in/logger transfer under 1 ms
- standard-particle concentration/counting sanity checks
- EV biological specificity evidence

Only after this stage may any report move from reproduction-lens estimates toward calibrated SNR/LOD or physical detection claims.

## 4. Affected project locations

| Location | Impact |
|---|---|
| `tools/lens_b_ev_gold_fullgrid_runner.py` | Must keep future B runtime at 1 ms and preserve 2 ms only as provenance |
| `tools/audits/tsuyama_detection_rate_calibration.py` | Needs explicit `tau_1ms_*` candidate catalog entries |
| `tools/one_shot/tsuyama_phase2_parameter_inverse.py` | Needs 1 ms family specs or a separate 1 ms phase plan |
| `tools/one_shot/tsuyama_phase2_acceptance_report.py` | Reuse for 1 ms rescore; output must distinguish legacy 2 ms vs current 1 ms |
| `tools/analyze_lens_b_ev_gold_fullgrid.py` | Must assert/report `lockin_time_constant_s`; non-1ms rows stay legacy |
| `reports/88_...md` | Must keep v5.2.7 overlay until 1 ms full-grid replaces it |
| `reports/49_...md` | Remains historical 2 ms provenance; add an addendum only after 1 ms B1 results exist |
| `results/lens_b_ev_gold_fullgrid_1seed_20260513/` | Legacy 2 ms reference; not current final |
| tests | Add/adjust tests for 1 ms runner config, candidate family, and non-1ms precheck labeling |

## 5. Decision tree

```text
Start: B runtime fixed at 1 ms
  |
  v
B2 1 ms anchor smoke stable?
  |-- no  -> B remains diagnostic-only; do not run full EV full-grid as final
  |
  |-- yes
       v
   B3 1 ms rescore gives acceptable / bounded partial parameter set?
       |-- no  -> report B=1 ms diagnostic-only; optional targeted EV probe only
       |
       |-- yes
            v
        targeted EV 1 ms probe changes 404/660 ordering?
            |-- yes -> run full-grid before recommendation
            |-- no  -> still run full-grid before final claim, but lower urgency
```

## 6. Summary judgment

The 2 ms to 1 ms change is large enough to invalidate the old B1 parameter freeze as a current final freeze. It is probably not guaranteed to overturn the broad old B2 trend that 660/800 nm width is strong, because many EV selected-annulus routes are already close to detection-rate ceiling. But 404 receives a larger transit-gain benefit than 660, so the only defensible path is:

1. rebuild B1 at 1 ms,
2. re-estimate `gamma`, `snr_scale`, and `snr_response_exp`,
3. run a targeted EV 1 ms probe,
4. then run B2 1 ms full-grid before signing any current Criterion B recommendation.
