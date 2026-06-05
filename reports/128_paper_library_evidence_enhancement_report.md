# Paper Library Evidence Enhancement Report

Date: 2026-05-18

## Verdict

The remaining table caveat has been narrowed. The former flat missing-table count is now split into candidate-resolved table gaps, true visual-review gaps, and papers that are mainly figure/text evidence rather than table evidence.

## Run Outputs

- Table gap review: `papers/analysis_full_v1/library_table_gap_review.csv`
- Engineering evidence ledger: `papers/analysis_full_v1/library_engineering_evidence_ledger.csv`
- Per-paper candidate files: `papers/analysis_full_v1/<paper_id>/evidence/`
- Plan: `reports/127_paper_library_evidence_enhancement_plan.md`

## Coverage

- Unique papers reviewed: 53
- Papers without machine table CSV: 41
- Missing-machine-table papers improved with layout/OCR candidates: 13
- Missing-machine-table papers reclassified as not table gaps: 28
- Missing-machine-table papers still requiring visual table review: 0
- Critical/high papers still requiring visual table review: 0
- Candidate rows saved: 100
- Evidence ledger rows: 2035
- AppleDouble sidecar files removed: 250

## Table Gap Status Counts

- improved_candidate: 13
- not_a_table_gap: 28
- resolved: 12

## Table Gap Resolution Counts

- layout_candidate_available: 13
- machine_table_available: 12
- not_a_table_gap_figure_evidence_only: 28

## Table Gap Priority Counts

- background: 3
- critical: 9
- high: 23
- medium: 18

## Table Candidate Method Counts

- pdftotext_layout: 89
- tesseract_ocr: 11

## Evidence Ledger Source Counts

- caption: 481
- layout_table_candidate: 89
- machine_table_csv: 29
- numeric_hook: 800
- ocr_table_candidate: 11
- source_sentence: 625

## Evidence Ledger Axis Counts

- detector_threshold_reporting: 158
- ev_scatter_ri_calibration: 717
- flow_transport_nanofluidics: 109
- mie_material_optics: 3
- nodi_geometry_readout: 461
- pod_absorption_photothermal: 585
- sample_prep_biology: 1
- standards_reporting: 1

## Critical/High Remaining Visual Table Reviews

- None

## Improved Missing-table Papers

- background - Influence of the isolation method on characteristics and functional activity of mesenchymal stromal -> layout_candidate_available (3 layout, 0 OCR)
- background - Diffraction of hermite–gaussian beams from a sinusoidal conducting grating -> layout_candidate_available (7 layout, 0 OCR)
- high - Calculated absorption and scattering properties of gold nanoparticles of different size, shape, and -> layout_candidate_available (13 layout, 1 OCR)
- high - Optical constants of the noble metals -> layout_candidate_available (7 layout, 2 OCR)
- high - Deriving extracellular vesicle size from scatter intensities measured by flow cytometry -> layout_candidate_available (11 layout, 2 OCR)
- high - Precision size and refractive index analysis of weakly scattering nanoparticles in polydispersions -> layout_candidate_available (2 layout, 1 OCR)
- high - Hollow organosilica beads as reference particles for optical detection of extracellular vesicles -> layout_candidate_available (1 layout, 1 OCR)
- high - Fluorescence and light scatter calibration allow comparisons of small particle data in standard unit -> layout_candidate_available (7 layout, 2 OCR)
- high - MIFlowCyt-EV A framework for standardized reporting of extracellular vesicle flow cytometry experim -> layout_candidate_available (1 layout, 1 OCR)
- high - Refractive index determination of nanoparticles in suspension using nanoparticle tracking analysis -> layout_candidate_available (2 layout, 0 OCR)
- high - Single vs. Swarm detection of microparticles and exosomes by flow cytometry -> layout_candidate_available (6 layout, 0 OCR)
- critical - Extended-nanofluidics fundamental technologies, unique liquid properties, and application in chemic -> layout_candidate_available (4 layout, 0 OCR)
- medium - Advanced top-down fabrication for a fused silica nanofluidic device -> layout_candidate_available (5 layout, 0 OCR)

## Interpretation

- Layout candidates are the strongest automatic improvement because they preserve columns better than plain extracted text.
- OCR candidates are useful for locating image-encoded tables, but they remain lower confidence.
- Papers reclassified as `not_a_table_gap` still may contain important figures; they are now represented through captions, numeric hooks, rendered pages, and ledger rows rather than table CSVs.
- The practical next step for simulator changes is to start from `library_engineering_evidence_ledger.csv`, filter `priority` in `critical/high`, and follow each row's `manual_action`.
