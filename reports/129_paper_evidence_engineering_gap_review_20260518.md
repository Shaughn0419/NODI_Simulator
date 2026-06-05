# Paper Evidence to Engineering Gap Review

Date: 2026-05-18

## Verdict

The engineering is strong as a no-measured-data, relative/proxy NODI design-selection simulator. It is not yet complete as a calibrated physical predictor.

The paper library now supports the engineering review at a useful depth: 53 unique papers have extraction status `ok`, 2035 engineering evidence rows are indexed, and the old missing-table caveat has been split into 13 papers with layout/OCR table candidates and 28 non-table figure/text evidence cases. The evidence base is therefore good enough to judge model coverage and engineering gaps.

The main remaining work is not more broad paper extraction. It is upgrading several currently diagnostic/scaffold lanes into measured, calibrated, or physically coupled lanes. The most important boundary is unchanged: current outputs cannot claim calibrated SNR, absolute LOD, true event probability, true EV concentration, empirical blank safety, or biological specificity.

## Evidence Base Used

- `papers/analysis_full_v1/library_engineering_evidence_ledger.csv`
- `papers/analysis_full_v1/library_engineering_matrix.csv`
- `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`
- `reports/89_EV_NODI_post_v2_unmodeled_realism_register.md`
- `reports/120_EV_NODI_P18_bounded_lane_synthesis_stop_continue_design.md`
- `reports/current_evidence_state_20260518.md`
- `reports/formula_chain_ledger_pre_3seed_v1.md`
- Key code modules under `nodi_simulator/`

Ledger distribution:

- EV scatter / refractive-index calibration: 717 evidence rows
- POD / absorption / photothermal: 585 evidence rows
- NODI geometry / readout / reference: 461 evidence rows
- Detector threshold / reporting: 158 evidence rows
- Flow / nanofluidic transport: 109 evidence rows

Critical/high evidence rows are concentrated in EV calibration, POD/photothermal, and NODI geometry/readout. That matches the project risk profile.

## Cross-cutting Conclusion

The code already contains many of the right engineering surfaces:

- Mie and core-shell particle optics
- EV correlated prior scaffold
- Brownian/advection/near-wall transport surrogates
- rectangular-channel flow profile and fluidic-network diagnostics
- BFP detector operator and ROI comparison diagnostics
- scalar/Jones polarization interface diagnostics
- Tsuyama paper-aligned phase-filter and NODI profiles
- readout transfer semantics and threshold governance
- POD and thermal contamination diagnostics
- calibration-table contracts and Bayesian calibration scaffold
- claim-governance gates that block calibrated overclaims

But several of these are intentionally marked diagnostic-only, unavailable, not calibrated, or scaffold-only. The next engineering maturity step is to convert selected diagnostic lanes into evidence-bearing lanes, starting with measured artifacts.

## 1. Particle and Material Modeling

### Current Strength

The engine uses physically grounded Mie / coated-sphere optics and EV core-shell presets. It has explicit diameter/radius convention tests, material RI convention tests, core-shell degeneracy tests, and EV population-prior diagnostics.

### Remaining Gaps

1. EVs remain optical surrogates, not biological populations. The current EV model has membrane/corona/EDL presets and a three-bin prior scaffold, but it does not infer a measured size-RI-cargo-corona distribution.
2. Nonsphericity, deformation, patchy corona, aggregates, and co-isolates are not represented in the forward scattering engine.
3. EV sample preparation effects are tracked as claim boundaries but are not coupled to event generation or contaminant priors deeply enough to support biological specificity.
4. Gold/silver and standard-particle material constants are implemented, but detector transfer from standard particles to EVs is not calibrated.

### Recommended Improvements

- Add an empirical EV population ingestion format: diameter distribution, RI distribution, shell/corona state, sample-prep method, contaminant/co-isolate labels, and uncertainty.
- Add a contaminant panel alongside EVs: lipoproteins, protein aggregates, cell debris, buffer background, hollow organosilica/reference beads, Au/Ag standards.
- Extend particle design from single representative particles to weighted populations and report selection bias by stratum.
- Keep nonspherical and aggregate particles as stress lanes first; do not let them alter final route claims until validated.

Priority: high for EV claim language and sample realism; medium for current relative route sorting.

## 2. Flow, Transport, and Event Generation

### Current Strength

The trajectory module includes advection, Brownian diffusion, reflecting boundaries, near-wall mobility, accessible center constraints, and rectangular duct flow. There are diagnostics for fluidic-network resistance, electrokinetic wall exclusion, Debye length, and zeta-potential metadata.

### Remaining Gaps

1. Current event simulation is still a conditional single-particle crossing model, not a concentration-to-count-rate model.
2. Pressure-flow relation is only partially computed; external tubing, inlet/outlet losses, reservoir conditions, and measured pressure-flow traces are missing.
3. Electrokinetics and wall exclusion exist as sensitivity diagnostics, not calibrated transport.
4. Adsorption, fouling, time drift, wall-loss, particle sticking, and sample aging are not modeled dynamically.
5. Coincidence/blended pulses are not modeled as a concentration-dependent event-overlap process.

### Recommended Improvements

- Add a concentration/flux/event-arrival layer that converts sample concentration and flow to stochastic event arrivals with coincidence probability.
- Add measured pressure-flow calibration ingestion and compare target residence time against actual pressure/flow traces.
- Add wall interaction states: pass, transient adhesion, permanent adsorption, fouling-background contribution.
- Add event overlap and swarm/coincidence diagnostics based on flow rate, concentration, optical volume, and lock-in response time.
- Promote electrokinetic transport only after ionic strength, wall zeta, particle zeta, and buffer chemistry are specified.

Priority: high if the project wants count-rate, concentration, or LOD claims; medium for pure relative geometry screening.

## 3. Optical Scattering and Full-wave Physics

### Current Strength

The chain from Mie cross-section to field proxy to detector collapse is well guarded. The formula ledger explicitly tests medium wavelength, angular measures, BFP Jacobian, complex conjugation, and sqrt-field conversion. There are interfaces for BFP operator diagnostics, near-interface correction, and Tsuyama phase-filter routes.

### Remaining Gaps

1. The main forward model is still a scalar/surrogate chain, not a full channel-particle-wall Maxwell solve.
2. Interface effects, finite groove length, evanescent/guided modes, sidewall roughness, and wall-scatter background are diagnostic or unmodeled.
3. The Tsuyama phase-filter route is 1D and useful, but it is not a full 2D/3D BFP blank-reference model.
4. Full-wave/RCWA/FDTD/Green tensor checks exist as planning or diagnostic concepts, not a systematic production validation lane.

### Recommended Improvements

- Add a small validation-grade full-wave spot-check matrix, not a huge grid: representative main-660 routes, 404 stress routes, Tsuyama-like 660 x 800/1200 x 550 routes, and selected EV/Au/Ag particles.
- Use RCWA/FDTD/Green-tensor outputs to calibrate or bound the reference/scattering operator, not to replace the fast grid.
- Add roughness/defect blank-background modeling only when fabrication metrology or blank BFP images exist.
- Add explicit validity bands to every route: scalar ok, scalar extrapolated, full-wave required.

Priority: very high for optical credibility; should be bounded and representative, not full-grid brute force.

## 4. Reference Field, BFP, and Interference Enhancement

### Current Strength

The project now correctly separates channel reference, scattering field, self term, cross term, selected-annulus event-position lens, and BFP detector-operator diagnostics. It also blocks the dangerous misreading that selected-annulus means optical BFP annulus.

### Remaining Gaps

1. Reference-field amplitude/phase is still not measured from a blank channel.
2. BFP/slit/ROI mask exists as a contract and surrogate, not as a calibrated detector operator.
3. Particle-induced channel phase perturbation is diagnostic-only and not coherently added because of double-counting risk.
4. Global phase offset and sign/polarity remain unmeasured.

### Recommended Improvements

- Acquire or ingest measured blank BFP / slit / ROI artifacts for the exact channel geometry and wavelength.
- Add a calibrated detector-operator table with mask weights, solid-angle weights, throughput, and provenance.
- Convert particle-channel perturbation from diagnostic-only to an alternative validated lane only after double-counting is resolved against full-wave or measured reference data.
- Make global phase offset an explicit calibration artifact; never infer it from route ranking.

Priority: highest. This is the shortest path from relative proxy to credible paper-aligned NODI prediction.

## 5. Detector, Readout, Threshold, and Noise

### Current Strength

Readout semantics are carefully governed. The engine distinguishes locked-carrier, random-arrival lock-in, bandpass-envelope surrogate, and measured-transfer-function semantics. Thresholding has robust statistics and denominator discipline.

### Remaining Gaps

1. No measured detector transfer function is loaded.
2. No empirical blank false-positive model is available.
3. Photon units, detector voltage, responsivity, absolute throughput, RIN, speckle, ADC dynamic range, and electronics noise remain blocked or not calibrated.
4. Current threshold/readout outputs support relative gating, not LOD or false-positive-rate claims.

### Recommended Improvements

- Add measured blank trace ingestion with false-positive bootstrap, autocorrelation time, drift, and threshold stability.
- Add detector transfer table: responsivity, gain, bandwidth, lock-in time constant, sampling, ADC range, spectral throughput.
- Add standard-particle calibration lanes to connect Mie predictions to detector output units.
- Make every dashboard metric distinguish: proxy event fraction, empirical false-positive adjusted rate, and calibrated detection probability.

Priority: highest if any SNR/LOD/readout claim is desired.

## 6. POD, Absorption, Thermal Coupling, and Paired Detection

### Current Strength

The project correctly refuses to treat the current POD lane as quantitative photothermal physics. The `pod_2019_2020` paper-aligned profile is explicitly unavailable, and `photothermal_pod.py` lists missing thermal-source, heat-diffusion, solvent, substrate, and modulation pieces.

### Remaining Gaps

1. No thermal diffusion model exists for POD.
2. No solvent dn/dT lane or solvent-enhanced sign flip is implemented.
3. No excitation/probe power-to-heat-source conversion is implemented.
4. NODI thermal contamination is only an absorption/scattering proxy.
5. Paired POD+NODI classification cannot be quantitative until the POD branch is real.

### Recommended Improvements

- Implement POD as a separate thermal forward model: absorption cross-section at excitation wavelength, heat diffusion, glass/water dn/dT, substrate contribution, modulation response, and ROI dI/dtheta.
- Keep POD and NODI scoring separated until paired-channel cross-talk and phase/frequency separation are calibrated.
- Use the 2019/2020/2024 Tsuyama/Mawatari POD papers to define acceptance tests: LOD scale, solvent-enhancement direction, sign flip, and paired readout behavior.

Priority: high for paired POD+NODI or photothermal claims; lower if the project stays NODI-only.

## 7. Calibration, Statistics, and Route Governance

### Current Strength

The project has unusually strong claim governance: formula ledger, route contracts, denominator fields, forbidden-claim tests, P0-P18 reports, and a P19 gate requirement. This prevents overclaiming.

### Remaining Gaps

1. Bayesian calibration is scaffold-only; no posterior is sampled.
2. Bounded trace lanes show rank instability between main-660 variants, so P18 correctly stops mechanical roll-forward.
3. Some lens-B results are one-seed/low-event design evidence and should not become final validation.
4. There is not yet a unified acceptance-criteria document that maps measured artifacts to claim upgrades.

### Recommended Improvements

- Define P19 as an evidence strategy gate before more compute: what artifact unlocks which claim, and what acceptance threshold is required.
- Add posterior calibration only after real standard/blank/operator artifacts exist.
- Promote from relative proxy to calibrated claim in staged levels: reference-calibrated, detector-calibrated, blank-adjusted, standard-particle transferred, EV-sample validated.
- Keep all-crossing and selected-annulus as separate lenses unless a planned bridge experiment explicitly links them.

Priority: highest for project governance; no more broad brute-force lanes should precede P19.

## 8. EV Reporting, Controls, and Biological Specificity

### Current Strength

The paper library now includes MISEV/MIFlowCyt/FCMPASS and EV RI/scatter calibration references. The code has assay/control/reporting modules and claim blockers.

### Remaining Gaps

1. Biological specificity is still blocked.
2. EV sample-prep differences are known but not coupled to a measured sample pipeline.
3. Control matrix is not yet tied to actual acquisition artifacts.
4. Classification/OOD rejection is blocked until trained and calibrated.

### Recommended Improvements

- Turn MISEV/MIFlowCyt-style fields into mandatory experiment metadata.
- Require buffer blank, medium blank, standard-particle ladder, EV-depleted control, spike-in controls, and sample-prep provenance.
- Add OOD/contaminant detection only after real labeled traces exist.
- Report EV results as optical-particle evidence unless biological validation exists.

Priority: highest for any exosome/biology-facing claim; moderate for optical instrument development.

## Proposed Priority Order

1. P19 evidence strategy gate: define claim upgrade ladder and required artifacts.
2. Measured blank/reference BFP/ROI artifact ingestion.
3. Standard-particle detector calibration with Au/Ag and/or validated scatter standards.
4. Detector/readout transfer and empirical blank false-positive calibration.
5. Representative full-wave spot checks for channel/reference/scatter operator.
6. Flow/pressure/concentration/event-arrival calibration.
7. EV population/sample-prep/control matrix ingestion.
8. POD thermal model, if paired POD+NODI remains in scope.
9. Bayesian posterior calibration after the above artifacts exist.

## Practical Engineering Backlog

### Near-term Software Work

- Add a `paper_evidence_to_config_gap.csv` that maps evidence-ledger rows to simulator config fields and claim blockers.
- Add dashboard filters for evidence axis, priority, source type, and manual action.
- Add validators for measured blank BFP, detector operator, standard-particle, and raw trace manifests.
- Add a P19 gate report generator that lists which claims remain locked and what artifact would unlock each.

### Medium-term Model Work

- Convert BFP detector operator from surrogate to calibrated lookup.
- Add full-wave spot-check ingestion and scalar-model correction factors with uncertainty.
- Add concentration/event-arrival and coincidence modeling.
- Add empirical EV population priors and contaminant stress panels.

### Longer-term Validation Work

- Build a measured data package: blank, Au/Ag standards, EV-like calibration beads, EV controls, raw traces, BFP images, detector settings, pressure/flow.
- Run posterior calibration and posterior predictive route comparison.
- Only then consider calibrated SNR, LOD, event probability, concentration, or biological specificity language.

## Final Engineering Judgment

The project does not need another broad literature extraction pass. It needs a calibration and physical-operator upgrade pass.

For a relative design-selection simulator, the engineering is already broad and careful. For a paper-claim or experiment-facing simulator, the biggest missing pieces are measured reference/BFP/operator artifacts, detector/readout calibration, empirical blank false-positive behavior, concentration/flow event generation, and full-wave spot checks. POD thermal physics is the largest mechanism-specific gap if paired POD+NODI remains part of the engineering target.

