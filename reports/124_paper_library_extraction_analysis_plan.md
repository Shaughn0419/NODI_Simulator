# Paper Library Extraction and Engineering Analysis Plan

Date: 2026-05-17

## Goal

Build a reproducible, reviewable paper-library evidence base for the NODI simulator. The output must answer two questions for every local paper:

1. What text, figures, tables, captions, and numerical constraints were extractable from the file?
2. How does that evidence affect engineering judgement for the simulator, especially reference-field modelling, interferometric readout, Mie/material assumptions, EV calibration/reporting, flow/transport, POD/NODI boundaries, and experiment design?

This is not a speed pass. The lane is intentionally conservative: extract first, classify and analyze second, then run a coverage/gap review before treating the library as complete.

## Scope

- Source files: every `.pdf` and `.docx` under `papers/`, excluding generated analysis/provenance outputs.
- Unit of completion: unique content hash, with duplicate file paths mapped back to the same extracted artifact.
- Current expected input size from the initial audit: 69 file instances, about 53 unique content hashes.

## Output Layout

- `papers/analysis_full_v1/manifest.csv`: one row per file instance, including duplicate mapping.
- `papers/analysis_full_v1/manifest_unique.csv`: one row per unique paper/work.
- `papers/analysis_full_v1/<paper_id>/metadata.json`: extraction metadata, page counts, tables, images, captions, and duplicate paths.
- `papers/analysis_full_v1/<paper_id>/text/`: full text plus page-level text where available.
- `papers/analysis_full_v1/<paper_id>/figures/embedded/`: embedded images extracted from the source file.
- `papers/analysis_full_v1/<paper_id>/page_renders/`: rendered pages containing likely figure/table evidence.
- `papers/analysis_full_v1/<paper_id>/tables/`: machine-extracted table CSVs where available.
- `papers/analysis_full_v1/<paper_id>/analysis.md`: engineering-focused analysis card.
- `papers/analysis_full_v1/library_engineering_matrix.csv`: compact comparison matrix.
- `papers/analysis_full_v1/library_gap_review.md`: final coverage and residual-risk review.
- `reports/125_paper_library_extraction_and_engineering_analysis.md`: reader-facing synthesis.

## Analysis Rubric

Each paper gets a structured card:

- Bibliographic identity inferred from local filename and PDF/DOCX metadata.
- Extraction status: pages, text characters, image count, rendered evidence pages, table count, caption count.
- Engineering priority: critical, high, medium, or background.
- Engineering topic tags:
  - `nodi_tsuyama`
  - `diffraction_reference`
  - `iscat_interferometry`
  - `mie_materials`
  - `ev_ri_scatter_calibration`
  - `detector_threshold_reporting`
  - `flow_transport_nanofluidics`
  - `photothermal_pod`
  - `sample_prep_ev_biology`
  - `standards_reporting`
- Direct constraints and usable numbers.
- Engineering implications for the current simulator.
- Boundaries: what must not be over-claimed from the paper.
- Follow-up hooks: tests, parameters, dashboard/report wording, or experiment needs.

## Priority Policy

The analysis weights papers by engineering relevance:

- Critical: Tsuyama/Mawatari NODI/POD/diffraction papers and directly claim-bearing paper-audit sources.
- High: Mie/material optical constants, EV refractive-index/scatter calibration, detector calibration/reporting, and iSCAT/interferometric mechanism papers.
- Medium: nanofluidic transport, diffraction-grating/optofluidic sensor context, photothermal support papers, and EV sample-preparation papers.
- Background: broad reviews and supporting context that shape wording or risk boundaries but do not directly set simulator parameters.

## Completion Checks

Completion requires:

- Every local PDF/DOCX instance appears in `manifest.csv`.
- Every unique content hash has `metadata.json` and `analysis.md`.
- Every PDF has page-level text extraction attempted.
- Every PDF has table extraction attempted with success/failure recorded.
- Every file has figure evidence extraction attempted through embedded images and/or rendered figure/table pages.
- Duplicate paths are mapped, not silently skipped.
- The final gap review names residual limitations, including scanned/low-text pages, failed table extraction, missing OCR, and non-computed SVM/classification claims.
