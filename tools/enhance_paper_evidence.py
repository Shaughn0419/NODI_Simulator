from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = PROJECT_ROOT / "papers" / "analysis_full_v1"
TABLE_GAP_CSV = LIBRARY_ROOT / "library_table_gap_review.csv"
EVIDENCE_LEDGER_CSV = LIBRARY_ROOT / "library_engineering_evidence_ledger.csv"
PLAN_REPORT = PROJECT_ROOT / "reports" / "127_paper_library_evidence_enhancement_plan.md"
RESULT_REPORT = PROJECT_ROOT / "reports" / "128_paper_library_evidence_enhancement_report.md"


TABLE_PATTERN = re.compile(
    r"(?<![A-Za-z])(?:Table|TABLE|Tab\.|Supplementary\s+Table|SUPPLEMENTARY\s+TABLE)"
    r"\s*\.?\s*(?:S?\d+[A-Za-z]?|[IVX]+[A-Za-z]?)(?![A-Za-z])"
)
TABLE_LINE_PATTERN = re.compile(
    r"(?m)^\s*(?:Table|TABLE|Tab\.|Supplementary\s+Table|SUPPLEMENTARY\s+TABLE)"
    r"\s*\.?\s*(?:S?\d+[A-Za-z]?|[IVX]+[A-Za-z]?)(?![A-Za-z])"
)
FIGURE_PATTERN = re.compile(r"(?i)\b(?:fig(?:ure)?|scheme|supplementary\s+fig(?:ure)?)\s*[s\dIVXivx]*[A-Za-z]?\b")
NUMERIC_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?(?:\s*(?:-|to|~|±)\s*\d+(?:\.\d+)?)?\s*"
    r"(?:nm|um|µm|mm|cm|mL|nL|pL|fL|aL|zmol|mol|M|mM|µM|uM|nM|pM|%"
    r"|Hz|kHz|MHz|mW|W|NA|eV|Pa|kPa|m/s|m/sec|s|ms)\b",
    flags=re.I,
)

AXIS_RULES: list[tuple[str, list[str]]] = [
    ("nodi_geometry_readout", ["nodi", "nanochannel", "diffraction", "phase", "objective", "NA", "wavelength", "probe"]),
    ("pod_absorption_photothermal", ["photothermal", "thermal", "absorption", "POD", "Sunset Yellow", "LOD"]),
    ("ev_scatter_ri_calibration", ["extracellular vesicle", "EV", "refractive index", "scatter", "FCMPASS", "calibration bead"]),
    ("detector_threshold_reporting", ["threshold", "limit of detection", "LOD", "sensitivity", "MESF", "reporting"]),
    ("mie_material_optics", ["Mie", "optical constants", "gold", "silver", "cross section", "Johnson", "Christy"]),
    ("flow_transport_nanofluidics", ["flow", "diffusion", "Brownian", "pressure", "transport", "viscosity"]),
    ("sample_prep_biology", ["isolation", "mesenchymal", "sample preparation", "biological", "staining"]),
    ("standards_reporting", ["MISEV", "MIFlowCyt", "minimal information", "standardized", "guideline"]),
]


@dataclass
class PaperContext:
    manifest: dict[str, str]
    review: dict[str, str]
    paper_dir: Path
    analysis: dict[str, Any]
    metadata: dict[str, Any]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def relpath(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def clean_sidecars(root: Path) -> int:
    count = 0
    for path in root.rglob("._*"):
        if path.is_file():
            path.unlink(missing_ok=True)
            count += 1
    return count


def safe_int(value: Any) -> int:
    try:
        return int(float(str(value or "0")))
    except ValueError:
        return 0


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def paper_contexts() -> list[PaperContext]:
    manifest_rows = load_csv(LIBRARY_ROOT / "manifest_unique.csv")
    review_by_id = {row["paper_id"]: row for row in load_csv(LIBRARY_ROOT / "library_quality_review.csv")}
    contexts: list[PaperContext] = []
    for row in manifest_rows:
        paper_dir = LIBRARY_ROOT / row["paper_id"]
        contexts.append(
            PaperContext(
                manifest=row,
                review=review_by_id.get(row["paper_id"], {}),
                paper_dir=paper_dir,
                analysis=read_json(paper_dir / "analysis.json"),
                metadata=read_json(paper_dir / "metadata.json"),
            )
        )
    return contexts


def page_texts(paper_dir: Path) -> dict[int, str]:
    pages: dict[int, str] = {}
    for page_path in sorted((paper_dir / "text").glob("page-*.txt")):
        if page_path.name.startswith("._"):
            continue
        match = re.search(r"page-(\d+)\.txt$", page_path.name)
        if match:
            pages[int(match.group(1))] = read_text(page_path)
    return pages


def load_captions(paper_dir: Path) -> list[dict[str, str]]:
    return load_csv(paper_dir / "caption_index.csv")


def caption_page_hints(captions: list[dict[str, str]], pattern: re.Pattern[str]) -> set[int]:
    pages: set[int] = set()
    for row in captions:
        caption = row.get("caption", "").strip()
        if pattern is TABLE_PATTERN:
            matched = TABLE_LINE_PATTERN.search(caption) is not None
        else:
            matched = pattern.search(caption) is not None
        if not matched:
            continue
        page_hint = row.get("page_hint", "")
        if page_hint.isdigit():
            pages.add(int(page_hint))
    return pages


def detect_signal_pages(pages: dict[int, str], captions: list[dict[str, str]]) -> tuple[set[int], set[int]]:
    table_pages: set[int] = set()
    figure_pages = caption_page_hints(captions, FIGURE_PATTERN)
    for page_no, text in pages.items():
        if TABLE_LINE_PATTERN.search(text):
            table_pages.add(page_no)
        if FIGURE_PATTERN.search(text):
            figure_pages.add(page_no)
    return table_pages, figure_pages


def run_pdftotext_layout(pdf_path: Path, page_no: int) -> str:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        return ""
    result = subprocess.run(
        [pdftotext, "-layout", "-f", str(page_no), "-l", str(page_no), str(pdf_path), "-"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=45,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def line_numeric_count(line: str) -> int:
    return len(re.findall(r"\d+(?:\.\d+)?", line))


def line_column_count(line: str) -> int:
    return len([part for part in re.split(r"\s{2,}", line.strip()) if part])


def is_table_like_line(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 8:
        return False
    if TABLE_LINE_PATTERN.search(stripped):
        return True
    columns = line_column_count(line)
    numbers = line_numeric_count(line)
    has_units = bool(NUMERIC_PATTERN.search(line))
    return columns >= 3 and (numbers >= 2 or has_units or len(stripped) > 60)


def extract_table_blocks(text: str, min_chars: int = 70) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current: list[str] = []
    blank_budget = 0

    def flush() -> None:
        nonlocal current, blank_budget
        block = "\n".join(current).strip()
        if not block:
            current = []
            blank_budget = 0
            return
        table_caption = TABLE_LINE_PATTERN.search(block) is not None
        numeric_count = line_numeric_count(block)
        multi_column_lines = sum(1 for line in block.splitlines() if line_column_count(line) >= 3)
        if len(block) >= min_chars and (table_caption or numeric_count >= 4 or multi_column_lines >= 2):
            rows.append(
                {
                    "block_text": re.sub(r"[ \t]+$", "", block, flags=re.M),
                    "line_count": len(block.splitlines()),
                    "numeric_tokens": numeric_count,
                    "multi_column_lines": multi_column_lines,
                    "has_table_label": "yes" if table_caption else "no",
                }
            )
        current = []
        blank_budget = 0

    for line in text.splitlines():
        if is_table_like_line(line):
            current.append(line.rstrip())
            blank_budget = 0
            continue
        if current and not line.strip() and blank_budget == 0:
            current.append(line.rstrip())
            blank_budget += 1
            continue
        if current and line.strip() and line_column_count(line) >= 2 and line_numeric_count(line) >= 1:
            current.append(line.rstrip())
            blank_budget = 0
            continue
        flush()
    flush()
    return rows


def rendered_image_for_page(paper_dir: Path, page_no: int) -> Path | None:
    candidates = [
        paper_dir / "page_renders" / f"page-{page_no:03d}.png",
        paper_dir / "page_renders" / f"docx-page-{page_no}.png",
    ]
    for path in candidates:
        if path.exists():
            return path
    for row in load_csv(paper_dir / "page_renders" / "render_index.csv"):
        if safe_int(row.get("page")) == page_no and row.get("path"):
            path = PROJECT_ROOT / row["path"]
            if path.exists():
                return path
    return None


def run_tesseract(image_path: Path) -> str:
    tesseract = shutil.which("tesseract")
    if not tesseract:
        return ""
    result = subprocess.run(
        [tesseract, str(image_path), "stdout", "--psm", "6"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=90,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def table_candidate_rows(ctx: PaperContext) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    paper_id = ctx.manifest["paper_id"]
    paper_dir = ctx.paper_dir
    evidence_dir = paper_dir / "evidence"
    candidates_dir = evidence_dir / "table_candidates"
    if candidates_dir.exists():
        shutil.rmtree(candidates_dir)
    pages = page_texts(paper_dir)
    captions = load_captions(paper_dir)
    table_pages, figure_pages = detect_signal_pages(pages, captions)
    source_path = PROJECT_ROOT / ctx.manifest["primary_relpath"]
    suffix = ctx.manifest.get("suffix", "")
    machine_tables = safe_int(ctx.manifest.get("tables_extracted"))
    priority = ctx.manifest.get("engineering_priority", "")

    candidate_rows: list[dict[str, Any]] = []
    layout_candidate_pages: set[int] = set()
    pages_to_process = sorted(table_pages)

    for page_no in pages_to_process:
        layout_text = ""
        if suffix == ".pdf" and source_path.exists():
            layout_text = run_pdftotext_layout(source_path, page_no)
        if not layout_text:
            layout_text = pages.get(page_no, "")
        for block_index, block in enumerate(extract_table_blocks(layout_text), start=1):
            target = candidates_dir / f"layout_page_{page_no:03d}_candidate_{block_index:02d}.txt"
            write_text(target, block["block_text"] + "\n")
            layout_candidate_pages.add(page_no)
            candidate_rows.append(
                {
                    "paper_id": paper_id,
                    "method": "pdftotext_layout",
                    "page": page_no,
                    "candidate_index": block_index,
                    "path": relpath(target),
                    "status": "candidate",
                    "line_count": block["line_count"],
                    "numeric_tokens": block["numeric_tokens"],
                    "multi_column_lines": block["multi_column_lines"],
                    "has_table_label": block["has_table_label"],
                    "confidence": "medium",
                    "text_preview": " ".join(block["block_text"].split())[:500],
                }
            )

    ocr_pages = sorted(table_pages - layout_candidate_pages)
    if priority in {"critical", "high"}:
        ocr_pages = sorted(set(ocr_pages) | set(list(table_pages)[:2]))
    for page_no in ocr_pages[:6]:
        image_path = rendered_image_for_page(paper_dir, page_no)
        if image_path is None:
            candidate_rows.append(
                {
                    "paper_id": paper_id,
                    "method": "tesseract_ocr",
                    "page": page_no,
                    "candidate_index": "",
                    "path": "",
                    "status": "skipped_no_rendered_page",
                    "confidence": "none",
                    "text_preview": "",
                }
            )
            continue
        ocr_text = run_tesseract(image_path)
        ocr_target = candidates_dir / f"ocr_page_{page_no:03d}.txt"
        if ocr_text.strip():
            write_text(ocr_target, ocr_text.strip() + "\n")
        blocks = extract_table_blocks(ocr_text, min_chars=50)
        if not blocks:
            candidate_rows.append(
                {
                    "paper_id": paper_id,
                    "method": "tesseract_ocr",
                    "page": page_no,
                    "candidate_index": "",
                    "path": relpath(ocr_target) if ocr_target.exists() else "",
                    "status": "ocr_text_no_table_block",
                    "confidence": "low",
                    "text_preview": " ".join(ocr_text.split())[:500],
                }
            )
            continue
        for block_index, block in enumerate(blocks, start=1):
            target = candidates_dir / f"ocr_page_{page_no:03d}_candidate_{block_index:02d}.txt"
            write_text(target, block["block_text"] + "\n")
            candidate_rows.append(
                {
                    "paper_id": paper_id,
                    "method": "tesseract_ocr",
                    "page": page_no,
                    "candidate_index": block_index,
                    "path": relpath(target),
                    "status": "candidate",
                    "line_count": block["line_count"],
                    "numeric_tokens": block["numeric_tokens"],
                    "multi_column_lines": block["multi_column_lines"],
                    "has_table_label": block["has_table_label"],
                    "confidence": "low_medium",
                    "text_preview": " ".join(block["block_text"].split())[:500],
                }
            )

    write_csv(paper_dir / "evidence" / "table_candidates.csv", candidate_rows)
    layout_candidates = [row for row in candidate_rows if row.get("method") == "pdftotext_layout" and row.get("status") == "candidate"]
    ocr_candidates = [row for row in candidate_rows if row.get("method") == "tesseract_ocr" and row.get("status") == "candidate"]
    table_signal = bool(table_pages)
    figure_signal = bool(figure_pages)
    if machine_tables > 0:
        resolution = "machine_table_available"
        status = "resolved"
        review_action = "use_machine_csv_then_check_original_page_for_hard_claims"
        confidence = "high"
    elif layout_candidates:
        resolution = "layout_candidate_available"
        status = "improved_candidate"
        review_action = "inspect_layout_candidate_and_original_page_before_citing_values"
        confidence = "medium"
    elif ocr_candidates:
        resolution = "ocr_candidate_available"
        status = "improved_candidate"
        review_action = "inspect_ocr_candidate_and_original_page_before_citing_values"
        confidence = "low_medium"
    elif table_signal:
        resolution = "table_signal_visual_review_required"
        status = "visual_review_required"
        review_action = "open_rendered_or_original_table_page_before_citing_values"
        confidence = "visual_only"
    elif figure_signal:
        resolution = "not_a_table_gap_figure_evidence_only"
        status = "not_a_table_gap"
        review_action = "use figure/caption evidence; no table-specific repair needed"
        confidence = "medium"
    else:
        resolution = "not_a_table_gap_no_table_signal"
        status = "not_a_table_gap"
        review_action = "no table-specific repair needed"
        confidence = "medium"

    gap_row = {
        "paper_id": paper_id,
        "title_guess": ctx.manifest.get("title_guess", ""),
        "primary_relpath": ctx.manifest.get("primary_relpath", ""),
        "priority": priority,
        "topic_tags": ctx.manifest.get("topic_tags", ""),
        "machine_tables": machine_tables,
        "layout_candidates": len(layout_candidates),
        "ocr_candidates": len(ocr_candidates),
        "table_signal_pages": ",".join(str(page) for page in sorted(table_pages)),
        "figure_signal_pages": ",".join(str(page) for page in sorted(figure_pages)),
        "status": status,
        "resolution": resolution,
        "confidence": confidence,
        "review_action": review_action,
        "candidate_csv": relpath(paper_dir / "evidence" / "table_candidates.csv"),
    }
    write_json(paper_dir / "evidence" / "table_gap_review.json", gap_row)
    return gap_row, candidate_rows


def classify_axis(text: str, fallback_topics: str = "") -> str:
    haystack = f"{text} {fallback_topics}".lower()
    scores: Counter[str] = Counter()
    for axis, keywords in AXIS_RULES:
        for keyword in keywords:
            if keyword.lower() in haystack:
                scores[axis] += 1
    if not scores:
        return "general_background"
    return scores.most_common(1)[0][0]


def manual_action_for(source_type: str, axis: str, priority: str) -> str:
    if source_type in {"machine_table_csv", "layout_table_candidate", "ocr_table_candidate"}:
        return "verify against original page before parameterizing simulator"
    if source_type == "caption":
        return "use as visual locator; inspect rendered page for trend or diagram semantics"
    if source_type == "numeric_hook":
        return "treat as candidate value; bind to page/table before hard claim"
    if priority in {"critical", "high"}:
        return "compare with simulator assumptions and cite source page if used"
    return "background context; cite only if it changes scope or wording"


def add_ledger_row(rows: list[dict[str, Any]], ctx: PaperContext, source_type: str, locator: str, path: str, text: str, confidence: str) -> None:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return
    priority = ctx.manifest.get("engineering_priority", "")
    axis = classify_axis(text, ctx.manifest.get("topic_tags", ""))
    rows.append(
        {
            "paper_id": ctx.manifest["paper_id"],
            "title_guess": ctx.manifest.get("title_guess", ""),
            "priority": priority,
            "topic_tags": ctx.manifest.get("topic_tags", ""),
            "source_type": source_type,
            "locator": locator,
            "path": path,
            "engineering_axis": axis,
            "confidence": confidence,
            "manual_action": manual_action_for(source_type, axis, priority),
            "hard_claim_ready": "no" if source_type != "machine_table_csv" else "after_original_page_check",
            "evidence_text": text[:1200],
        }
    )


def machine_table_rows(ctx: PaperContext) -> list[dict[str, str]]:
    table_index = ctx.paper_dir / "tables" / "table_index.csv"
    return [row for row in load_csv(table_index) if row.get("status") == "ok" and row.get("path")]


def build_evidence_ledger(contexts: list[PaperContext], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_by_paper: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        if row.get("status") == "candidate":
            candidate_by_paper[str(row["paper_id"])].append(row)

    rows: list[dict[str, Any]] = []
    for ctx in contexts:
        priority = ctx.manifest.get("engineering_priority", "")
        high_value = priority in {"critical", "high"}
        numeric_limit = 30 if high_value else 12
        sentence_limit = 16 if high_value else 6
        caption_limit = 20 if high_value else 8
        for hook in (ctx.analysis.get("numeric_hits") or [])[:numeric_limit]:
            add_ledger_row(rows, ctx, "numeric_hook", "analysis.numeric_hits", relpath(ctx.paper_dir / "analysis.json"), str(hook), "medium")
        for index, sentence in enumerate((ctx.analysis.get("evidence_sentences") or [])[:sentence_limit], start=1):
            add_ledger_row(rows, ctx, "source_sentence", f"analysis.evidence_sentences[{index}]", relpath(ctx.paper_dir / "analysis.json"), str(sentence), "medium")
        for row in load_captions(ctx.paper_dir)[:caption_limit]:
            locator = f"caption_index={row.get('caption_index','')};page_hint={row.get('page_hint','')}"
            add_ledger_row(rows, ctx, "caption", locator, relpath(ctx.paper_dir / "caption_index.csv"), row.get("caption", ""), "medium_high")
        for row in machine_table_rows(ctx):
            locator = f"page={row.get('page','')};table={row.get('table_index','')}"
            text = f"machine table rows={row.get('rows','')} cols={row.get('cols','')} status={row.get('status','')}"
            add_ledger_row(rows, ctx, "machine_table_csv", locator, row.get("path", ""), text, "high")
        for row in candidate_by_paper.get(ctx.manifest["paper_id"], []):
            source_type = "layout_table_candidate" if row.get("method") == "pdftotext_layout" else "ocr_table_candidate"
            locator = f"page={row.get('page','')};candidate={row.get('candidate_index','')}"
            add_ledger_row(rows, ctx, source_type, locator, row.get("path", ""), row.get("text_preview", ""), row.get("confidence", "medium"))
    return rows


def write_plan_report() -> None:
    report = """# Paper Library Evidence Enhancement Plan

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
"""
    write_text(PLAN_REPORT, report)


def write_result_report(
    contexts: list[PaperContext],
    table_gap_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    ledger_rows: list[dict[str, Any]],
    sidecars_removed: int,
) -> None:
    status_counts = Counter(row["status"] for row in table_gap_rows)
    resolution_counts = Counter(row["resolution"] for row in table_gap_rows)
    priority_counts = Counter(row["priority"] for row in table_gap_rows)
    source_counts = Counter(row["source_type"] for row in ledger_rows)
    axis_counts = Counter(row["engineering_axis"] for row in ledger_rows)
    candidate_counts = Counter(row["method"] for row in candidate_rows if row.get("status") == "candidate")
    missing_machine = [row for row in table_gap_rows if safe_int(row["machine_tables"]) == 0]
    unresolved_table_signal = [row for row in missing_machine if row["status"] == "visual_review_required"]
    high_unresolved = [row for row in unresolved_table_signal if row["priority"] in {"critical", "high"}]
    improved = [row for row in missing_machine if row["status"] == "improved_candidate"]
    not_gap = [row for row in missing_machine if row["status"] == "not_a_table_gap"]

    def bullet(items: list[str]) -> str:
        return "".join(f"- {item}\n" for item in items) if items else "- None\n"

    report = f"""# Paper Library Evidence Enhancement Report

Date: 2026-05-18

## Verdict

The remaining table caveat has been narrowed. The former flat missing-table count is now split into candidate-resolved table gaps, true visual-review gaps, and papers that are mainly figure/text evidence rather than table evidence.

## Run Outputs

- Table gap review: `{TABLE_GAP_CSV.relative_to(PROJECT_ROOT)}`
- Engineering evidence ledger: `{EVIDENCE_LEDGER_CSV.relative_to(PROJECT_ROOT)}`
- Per-paper candidate files: `papers/analysis_full_v1/<paper_id>/evidence/`
- Plan: `{PLAN_REPORT.relative_to(PROJECT_ROOT)}`

## Coverage

- Unique papers reviewed: {len(contexts)}
- Papers without machine table CSV: {len(missing_machine)}
- Missing-machine-table papers improved with layout/OCR candidates: {len(improved)}
- Missing-machine-table papers reclassified as not table gaps: {len(not_gap)}
- Missing-machine-table papers still requiring visual table review: {len(unresolved_table_signal)}
- Critical/high papers still requiring visual table review: {len(high_unresolved)}
- Candidate rows saved: {len([row for row in candidate_rows if row.get('status') == 'candidate'])}
- Evidence ledger rows: {len(ledger_rows)}
- AppleDouble sidecar files removed: {sidecars_removed}

## Table Gap Status Counts

{bullet([f"{key}: {value}" for key, value in sorted(status_counts.items())])}
## Table Gap Resolution Counts

{bullet([f"{key}: {value}" for key, value in sorted(resolution_counts.items())])}
## Table Gap Priority Counts

{bullet([f"{key}: {value}" for key, value in sorted(priority_counts.items())])}
## Table Candidate Method Counts

{bullet([f"{key}: {value}" for key, value in sorted(candidate_counts.items())])}
## Evidence Ledger Source Counts

{bullet([f"{key}: {value}" for key, value in sorted(source_counts.items())])}
## Evidence Ledger Axis Counts

{bullet([f"{key}: {value}" for key, value in sorted(axis_counts.items())])}
## Critical/High Remaining Visual Table Reviews

{bullet([f"{row['priority']} - {row['title_guess']} -> {row['review_action']}" for row in high_unresolved])}
## Improved Missing-table Papers

{bullet([f"{row['priority']} - {row['title_guess']} -> {row['resolution']} ({row['layout_candidates']} layout, {row['ocr_candidates']} OCR)" for row in improved[:40]])}
## Interpretation

- Layout candidates are the strongest automatic improvement because they preserve columns better than plain extracted text.
- OCR candidates are useful for locating image-encoded tables, but they remain lower confidence.
- Papers reclassified as `not_a_table_gap` still may contain important figures; they are now represented through captions, numeric hooks, rendered pages, and ledger rows rather than table CSVs.
- The practical next step for simulator changes is to start from `library_engineering_evidence_ledger.csv`, filter `priority` in `critical/high`, and follow each row's `manual_action`.
"""
    write_text(RESULT_REPORT, report)


def main() -> None:
    write_plan_report()
    contexts = paper_contexts()
    initial_sidecars = clean_sidecars(LIBRARY_ROOT)
    table_gap_rows: list[dict[str, Any]] = []
    all_candidate_rows: list[dict[str, Any]] = []
    for ctx in contexts:
        gap_row, candidate_rows = table_candidate_rows(ctx)
        table_gap_rows.append(gap_row)
        all_candidate_rows.extend(candidate_rows)
    write_csv(TABLE_GAP_CSV, table_gap_rows)
    write_csv(LIBRARY_ROOT / "library_table_candidates.csv", all_candidate_rows)
    ledger_rows = build_evidence_ledger(contexts, all_candidate_rows)
    write_csv(EVIDENCE_LEDGER_CSV, ledger_rows)
    final_sidecars = clean_sidecars(LIBRARY_ROOT)
    sidecars_removed = initial_sidecars + final_sidecars
    write_result_report(contexts, table_gap_rows, all_candidate_rows, ledger_rows, sidecars_removed)
    print(f"unique_papers={len(contexts)}")
    print(f"table_gap_rows={len(table_gap_rows)}")
    print(f"table_candidates={len([row for row in all_candidate_rows if row.get('status') == 'candidate'])}")
    print(f"evidence_ledger_rows={len(ledger_rows)}")
    print(f"sidecars_removed={sidecars_removed}")
    print(f"table_gap_csv={TABLE_GAP_CSV.relative_to(PROJECT_ROOT)}")
    print(f"evidence_ledger_csv={EVIDENCE_LEDGER_CSV.relative_to(PROJECT_ROOT)}")
    print(f"report={RESULT_REPORT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
