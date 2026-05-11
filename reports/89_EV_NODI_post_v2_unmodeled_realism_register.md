# EV NODI post-v2 unmodeled realism register

> Status: post-v2 boundary register. This file does not reopen v2, add scenarios, add stochastic seeds, run solver cases, authorize experiments, or change route governance. As of 2026-05-11, report 88 v4.0 is the current full-data reader report; it carries two parallel reader lenses of equal priority — all-crossing (§1–§13) and selected-annulus paper-audit (§14) — with §15 as the integrated cross-lens analysis. This register applies to **both** lenses unless explicitly noted.

## Purpose

v2 is closed as a no-measured-data realism supplement: it makes the original relative simulation more realistic by adding instrument-aware priors, route governance, blank/thermal guardrails, near-wall mesh adjudication, route-role stability checks, width-prior sensitivity, and artifact-gap registration.

This register records realism dimensions that remain outside v2 because they require measured artifacts, new physical operators, or post-v2 validation programs. They are not missing blockers for v2 closure, and they must not be converted into calibrated claims inside v2.

## Current boundary

Allowed current claim:

- synthetic relative-prior evidence for design comparison;
- trend and fixed-condition alignment against Tsuyama/Mawatari literature;
- route-governance stability inside the no-measured-data model;
- explicit identification of post-v2 artifact gaps.

Forbidden current claim (applies to both lenses):

- calibrated signal-to-noise ratio;
- calibrated event probability;
- absolute detection limit;
- true EV concentration;
- biological specificity;
- measured blank safety;
- route promotion (all-crossing lens) / accepted paper-calibrated candidate (selected-annulus lens);
- main-660 redefinition;
- **selected-annulus replacing all-crossing ranking, and all-crossing replacing selected-annulus paper-audit conclusions** (the two lenses sit in parallel and do not replace each other);
- selected-annulus bound changes (`0.5-0.8` is fixed);
- treating P6-P16 trace-only rank order as route promotion or as a single main-660 champion;
- treating estimated-parameter reproduction lens as raw physical calibration (selected-annulus lens);
- treating gamma response compression as a real physical law (selected-annulus lens);
- claiming local classification accuracy reproduction (local sklearn unavailable, `no_accuracy_claim` still in force).

## P0-P18 status note

P0-P18 refine this register rather than closing it. P0 provides a
review-ready relative audit package and keeps `main_660_W800_D1400` plus
`main_660_W800_D1500` as conditional relative-main candidates. P6/P8/P10/P12/P14/P16
then run six bounded trace-only lanes over the same three-route set; the two
main-660 candidates swap rank across lanes, while the 404 probe remains a
shortwave probe. P18 therefore stops mechanical lane roll-forward pending a P19
evidence-strategy gate with explicit acceptance criteria.

P0-P18 are conducted under the all-crossing lens; the selected-annulus lens did
not run independent P1-P18 stages. Selected-annulus evidence at the same time
horizon is captured by the Tsuyama Phase 2 / Phase 2.5-2.11 reproduction-lens
chain (release status `negative_or_diagnostic_result_only`, best low-DOF
reproduction lens single global response compression `gamma ≈ 0.749` with score
`2.033`) and by the R5.2 bounded scenario-prior audit sidecar guardrails
(`selected_annulus_replaces_all_crossing_ranking = false`,
`selected_annulus_bound_change_authorized = false`). The P19 evidence-strategy
gate must therefore declare acceptance criteria for **both** lenses, not just
the all-crossing lane.

## Post-v2 realism gaps

| Gap | Why it matters | v2 status | Post-v2 dependency |
|---|---|---|---|
| Solvent thermo-optic coupling | Solvent refractive-index changes can alter optical background and phase response, especially in photothermal/POD-adjacent settings. | 404 nm thermal behavior is kept as a safety/diagnostic sidecar and never increases NODI optical score; residual thermo-optic coupling is not calibrated. | Measured or independently specified thermo-optic operator before quantitative use. |
| Polarization fidelity | High-NA collection, channel-wall birefringence, PEG layers, and alignment can perturb the assumed polarization response. | Orthogonal sensitivity and sign/parity diagnostics exist, but there is no measured polarization transfer function. | Polarization transfer artifact or bounded operator model. |
| Slow pointing and alignment drift | Static slit/BFP offsets do not capture minutes-to-hours drift, warm-up, or long blank acquisition stability. | R5 includes a BFP/slit-offset scenario, but not a time-series drift model. | Time-resolved alignment/blank artifact or explicit drift prior. |
| EV polydispersity and non-spherical morphology | Real EV samples are broad mixtures with shape, membrane, cargo, and refractive-index heterogeneity. | v1/v2 use representative EV-like particles and anchors; particle-stratum residuals are warnings, not empirical fits. | Sample distribution model or measured size/refractive-index panel. |
| Coincidence and blended pulses | At higher flux or concentration, multiple particles can occupy the optical volume and produce blended events. | Current event logic is single-particle relative simulation; proxy counts are not observed detections. | Concentration/flow model and event-overlap simulator or measurement. |
| Channel roughness and fabrication-scatter background | Wall roughness, defects, and metrology tolerances can add fixed scattering background and route-specific fragility. | R7/R7.2 register fabrication/metrology artifacts, but v2 does not calibrate roughness background. | Fabrication metrology and blank-scatter artifact. |
| PEG adsorption and long-time fouling | Surface adsorption and fouling evolve with time and can change blank, transport, and wall-loss behavior. | Wall/PEG/transport priors are low-dimensional explanatory hypotheses, not time-resolved fouling models. | Time-resolved blank/flow/fouling artifact. |

## Interpretation rule

These gaps explain why v2 remains a no-measured-data, synthetic relative-prior model. They do not invalidate the v2 closure, but they define the line beyond which the project needs a separate post-v2 validation or artifact-acquisition program.

The register is deliberately not a to-do list for more v2 computation. Any future work that uses these gaps to unlock calibrated detector claims, biological specificity, absolute detection limits, true EV concentration, route promotion, or main-660 redefinition requires a separate reviewed plan outside v2.
