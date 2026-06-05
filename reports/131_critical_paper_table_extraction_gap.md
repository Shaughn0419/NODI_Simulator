# Critical Paper Table Extraction and Target Binding Gap

Date: 2026-05-18

Scope: manual pre-measurement audit for the nine critical papers listed in `library_table_gap_review.csv`, resolved into `papers/analysis_full_v1/critical_paper_target_binding.csv`.

## Verdict

Critical binding is complete for the pre-measurement Level-1 gate. All nine critical papers have rows for the six required target sections:

- channel geometry
- wavelength/objective/detector optics
- flow/pressure/transit/concentration
- detector/readout/threshold/SN/blank handling
- POD thermal parameters
- NODI reference/slit/BFP/ROI/diffraction fields

The binding CSV has 72 rows:

- 38 `bound`
- 18 `engineering_default_unconfirmed_against_paper`
- 12 `not_parameterizable`
- 4 `deferred_to_measured_plan`

The key outcome is intentionally conservative: extracted paper values can support Level-1 context and boundary wording, but they do not calibrate the current simulator. Formal route-family geometry and Gaussian IID threshold/readout semantics remain engineering defaults unless explicitly bound in the CSV and accepted by a later P19/freeze review.

## Table Gap Status

| Paper | Machine tables | Layout/OCR candidates | P19 treatment |
|---|---:|---:|---|
| Nonfluorescent Molecule Detection in 10^2 nm Nanofluidic Channels | 0 | 0 | figure/text POD context; no NODI operator binding |
| Concentration Determination at a Countable Molecular Level in Nanofluidics | 1 | 5 layout | POD solvent/table context; original-page check still needed for hard config |
| Detection and Characterization of Individual Nanoparticles in a Liquid | 0 | 0 | figure/text POD counting context; no NODI score transfer |
| Nanofluidic optical diffraction interferometry for detection and classification | 0 | 0 | primary NODI mechanism/optics context from text/figures |
| Supplementary file1 | 2 | 0 | machine-table material/interferometric context; original DOCX page check needed |
| Characterization of optical diffraction by single nanochannel | 0 | 0 | diffraction/geometry/BFP-theory context from text/figures |
| Nanofluidic detection platform for simultaneous light absorption and scattering | 0 | 0 | paired POD+NODI context; scoring remains NODI-only |
| Extended-nanofluidics fundamental technologies | 0 | 4 layout | generic fluidic boundary context; not current NODI config |
| Solvent-enhanced POD duplicate/category copy | 1 | 5 layout | same POD solvent evidence class as packaged reference |

## Binding Rules Applied

- Bound rows must provide source locator, paper value, unit, and target field.
- Unbound rows use only `not_parameterizable`, `deferred_to_measured_plan`, or `engineering_default_unconfirmed_against_paper`.
- No row unlocks Level-2+ claims.
- POD values cannot become NODI scattering/detector claims.
- Count-rate, concentration, empirical blank, detector voltage, and LOD are later measured-plan domains.
- Missing paper fields are not inferred from simulator output.

## Important Bound Context

NODI-relevant context:

- 2022 NODI paper: single nanochannel acts as reference light for interferometric detection; 532 nm laser, 20x NA 0.45 objective, NA 0.9 collection, slit/photodiode/lock-in readout, 100 kPa giving about 0.2 mm/s and 5.4 pL/min in the cited setup.
- 2022 supplementary DOCX: 488/532/660 nm material/interferometric scattering tables for 40 nm Au/Ag and classification procedure context.
- 2020 optical diffraction characterization: Fresnel-Kirchhoff / back-focal-plane formulation, 633 nm He-Ne, 20x NA 0.45, NA 0.90 collection, 1.1 kHz lock-in, width/depth sweep context.
- 2024 paired platform: 800-1200 nm wide, 550 nm deep channels; 532/660 nm lasers; slit 1 mm; photodiode 400 um aperture; two-channel lock-in at 4.1/1.2 kHz; threshold rules.

POD/photothermal context:

- 2019 POD molecule detection and 2020 solvent-enhanced/counting POD papers provide POD mechanism, thermal/solvent, LOD, and detection-volume context.
- These rows remain future POD evidence and do not alter the current NODI full-run scoring lens.

Transport context:

- Several critical papers include pressure/flow or generic extended-nanofluidic pressure scales.
- Current formal run keeps `count_prediction_status=not_applied_per_event_only`; no event-arrival/count-rate lens is bound.

## Engineering Defaults Explicitly Marked

Two classes of current simulator values are marked `engineering_default_unconfirmed_against_paper` for every critical paper:

1. Formal route-family geometry in `results/pre3seed_formal_3seed_10000e_run_plan.csv`.
2. Gaussian IID threshold / lock-in surrogate semantics in the formal run plan and `readout_transfer_model.py`.

These defaults are allowed for Level-1 no-data ranking only. They do not become paper-confirmed or calibrated by proximity to extracted literature values.

## Full-Run Implication

The critical binding package supports a Level-1 launch only after freeze closure. It does not create a measured calibration path and does not authorize route promotion, calibrated SNR, LOD, concentration, empirical blank safety, detector voltage, or biological specificity.

Primary artifacts:

- `papers/analysis_full_v1/critical_paper_target_binding.csv`
- `papers/analysis_full_v1/paper_evidence_to_config_gap.csv`
- `tests/test_critical_paper_binding_integrity.py`
