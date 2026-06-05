# Paper Library Evidence Enhancement Plan

Date: 2026-05-18

## Goal

Compress the remaining extraction caveat from a broad "no machine table CSV" warning into per-paper evidence states that are useful for simulator review.

## Available Local Toolchain

- `soffice` / LibreOffice: DOCX layout rendering.
- `pdftotext -layout`: PDF page-layout text recovery for table-like blocks.
- `pdfplumber`: first-pass machine table CSV extraction, already used by the base extractor.
- `pdftoppm` / PyMuPDF page renders: visual evidence for figures and table pages.
- `tesseract`: OCR fallback for rendered table pages when layout text is insufficient.
- Existing analysis cards: topic, priority, numeric hooks, claim boundaries, and source-evidence sentences.

## Improvement Route

1. Classify every paper with missing machine table CSV into true table signal, figure-only evidence, or low-risk no-table-signal state.
2. For table-signal papers, run `pdftotext -layout` on the relevant pages and save table-like candidate blocks.
3. For table-signal pages not resolved by layout text, run `tesseract` OCR against rendered page images and save OCR candidates.
4. Build a global engineering evidence ledger across the whole library, with stronger density for `critical` and `high` papers.
5. Update the quality report so the remaining caveat is no longer a flat count; it becomes a status matrix with review actions.

## Quality Boundary

Layout and OCR candidates reduce search effort but do not become hard simulator parameters by themselves. Any hard numeric claim must still be checked against the original page or rendered visual evidence.
