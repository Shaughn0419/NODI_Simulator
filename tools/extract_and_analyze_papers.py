from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPERS_ROOT = PROJECT_ROOT / "papers"
OUTPUT_ROOT = PAPERS_ROOT / "analysis_full_v1"


TOPIC_PATTERNS: dict[str, list[str]] = {
    "nodi_tsuyama": [
        r"tsuyama",
        r"mawatari",
        r"\bNODI\b",
        r"nanofluidic optical diffraction interferometry",
    ],
    "diffraction_reference": [
        r"diffraction",
        r"diffracted",
        r"phase filter",
        r"grating",
        r"reference field",
    ],
    "iscat_interferometry": [
        r"iSCAT",
        r"interferometric",
        r"heterodyne",
        r"dark-field",
        r"scattering microscopy",
    ],
    "mie_materials": [
        r"\bMie\b",
        r"optical constants",
        r"Johnson",
        r"Christy",
        r"gold nanoparticle",
        r"silver nanoparticle",
        r"cross section",
    ],
    "ev_ri_scatter_calibration": [
        r"extracellular vesicle",
        r"\bEV\b",
        r"refractive index",
        r"scatter calibration",
        r"core-shell",
        r"FCMPASS",
        r"MIFlowCyt",
    ],
    "detector_threshold_reporting": [
        r"threshold",
        r"limit of detection",
        r"\bLOD\b",
        r"sensitivity",
        r"calibration",
        r"reporting",
        r"fluorescence sensitivity",
    ],
    "flow_transport_nanofluidics": [
        r"flow",
        r"diffusion",
        r"brownian",
        r"nanofluidic",
        r"nanochannel",
        r"pressure-driven",
        r"transport",
    ],
    "photothermal_pod": [
        r"photothermal",
        r"thermal lens",
        r"\bPOD\b",
        r"absorption",
        r"solvent-enhanced",
    ],
    "sample_prep_ev_biology": [
        r"isolation method",
        r"mesenchymal",
        r"biological",
        r"functional activity",
        r"sample preparation",
    ],
    "standards_reporting": [
        r"MISEV",
        r"minimal information",
        r"standardi[sz]ed reporting",
        r"guideline",
    ],
}


UNIT_PATTERN = re.compile(
    r"\b(?:\d+(?:\.\d+)?(?:\s*(?:-|–|to|~|±)\s*\d+(?:\.\d+)?)?\s*"
    r"(?:nm|µm|um|mm|cm|ms|s|Hz|kHz|MHz|mW|W|NA|sigma|%|m\^?2|m2|Pa|kPa|"
    r"pL/min|m/sec|eV|mL|nL|fL|aL)"
    r"|NA\s*[=:]?\s*\d+(?:\.\d+)?|SNR\s*(?:of|=|about|~)?\s*\d+(?:\.\d+)?)"
)


CAPTION_PATTERN = re.compile(
    r"(?is)\b((?:fig(?:ure)?|table|scheme|supplementary\s+(?:fig(?:ure)?|table))"
    r"\s*\.?\s*[sS]?\d+[A-Za-z]?(?:\s*[-.:]\s*|\s+).{20,900}?)(?=\n\s*\n|"
    r"\b(?:fig(?:ure)?|table|scheme|supplementary\s+(?:fig(?:ure)?|table))\s*\.?\s*[sS]?\d+|\Z)"
)


@dataclass(frozen=True)
class PaperInstance:
    relpath: str
    path: Path
    sha256: str
    suffix: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_relpath(path: Path) -> str:
    return path.as_posix()


def slugify(text: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_text).strip("_").lower()
    slug = re.sub(r"_+", "_", slug)
    return (slug[:90] or fallback).strip("_")


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def scan_instances() -> list[PaperInstance]:
    instances: list[PaperInstance] = []
    for suffix in ("*.pdf", "*.docx"):
        for path in sorted(PAPERS_ROOT.rglob(suffix)):
            if path.name.startswith("._"):
                continue
            if "analysis_full_v1" in path.parts or "provenance" in path.parts:
                continue
            relpath = normalize_relpath(path.relative_to(PROJECT_ROOT))
            instances.append(PaperInstance(relpath, path, sha256_file(path), path.suffix.lower()))
    return instances


def primary_sort_key(instance: PaperInstance) -> tuple[int, int, str]:
    rel = instance.relpath
    under_classified = "/paper- scattering/" in rel
    return (1 if under_classified else 0, rel.count("/"), rel)


def infer_category(paths: list[str]) -> str:
    categories: list[str] = []
    for relpath in paths:
        parts = Path(relpath).parts
        if len(parts) >= 3 and parts[0] == "papers" and parts[1] == "paper- scattering":
            categories.append(parts[2])
        elif len(parts) >= 2 and parts[0] == "papers":
            categories.append("packaged_reference")
    if not categories:
        return "uncategorized"
    counts = Counter(categories)
    return counts.most_common(1)[0][0]


def infer_bibliographic_identity(stem: str) -> dict[str, str]:
    normalized = stem.replace("_", " ")
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", normalized)
    year = year_match.group(1) if year_match else ""
    authors = ""
    title = normalized
    dash_parts = re.split(r"\s+-\s+", normalized, maxsplit=2)
    if len(dash_parts) >= 3 and re.fullmatch(r"19\d{2}|20\d{2}", dash_parts[1].strip()):
        authors = dash_parts[0].strip()
        year = dash_parts[1].strip()
        title = dash_parts[2].strip()
    elif year_match:
        before = normalized[: year_match.start()].strip(" -_")
        after = normalized[year_match.end() :].strip(" -_")
        authors = before.strip()
        title = after.strip() or normalized.strip()
    title = re.sub(r"\s+", " ", title).strip()
    authors = re.sub(r"\s+", " ", authors).strip()
    return {"title_guess": title, "authors_guess": authors, "year_guess": year}


def get_fitz() -> Any:
    try:
        import fitz  # type: ignore

        return fitz
    except Exception as exc:  # pragma: no cover - environment check
        raise SystemExit("PyMuPDF/fitz is required. Run with the project .venv Python.") from exc


def extract_pdf(path: Path, out_dir: Path) -> dict[str, Any]:
    fitz = get_fitz()
    doc = fitz.open(path)
    pdf_metadata = dict(doc.metadata or {})
    text_dir = out_dir / "text"
    image_dir = out_dir / "figures" / "embedded"
    render_dir = out_dir / "page_renders"
    tables_dir = out_dir / "tables"
    text_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    page_rows: list[dict[str, Any]] = []
    image_rows: list[dict[str, Any]] = []
    render_rows: list[dict[str, Any]] = []
    all_text_parts: list[str] = []
    xrefs_seen: set[int] = set()
    pages_with_visual_evidence: set[int] = set()

    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        page_no = page_index + 1
        page_text = clean_text(page.get_text("text", sort=True))
        all_text_parts.append(f"\n\n--- Page {page_no} ---\n\n{page_text}")
        write_text(text_dir / f"page-{page_no:03d}.txt", page_text + "\n")

        image_count = 0
        for image_number, image_info in enumerate(page.get_images(full=True), start=1):
            xref = int(image_info[0])
            if xref in xrefs_seen:
                continue
            xrefs_seen.add(xref)
            try:
                extracted = doc.extract_image(xref)
            except Exception:
                continue
            width = int(extracted.get("width") or 0)
            height = int(extracted.get("height") or 0)
            if width * height < 8000:
                continue
            ext = str(extracted.get("ext") or "bin").lower()
            target = image_dir / f"page-{page_no:03d}-img-{image_number:02d}.{ext}"
            target.write_bytes(extracted["image"])
            image_count += 1
            image_rows.append(
                {
                    "page": page_no,
                    "image_index": image_number,
                    "path": normalize_relpath(target.relative_to(PROJECT_ROOT)),
                    "width": width,
                    "height": height,
                    "extension": ext,
                }
            )
        if image_count:
            pages_with_visual_evidence.add(page_no)
        if re.search(r"(?i)\b(fig(?:ure)?|table|scheme)\s*\.?\s*[sS]?\d+", page_text):
            pages_with_visual_evidence.add(page_no)
        page_rows.append(
            {
                "page": page_no,
                "text_chars": len(page_text),
                "embedded_images_kept": image_count,
            }
        )

    full_text = clean_text("".join(all_text_parts))
    write_text(text_dir / "full_text.txt", full_text + "\n")

    for page_no in sorted(pages_with_visual_evidence):
        try:
            page = doc.load_page(page_no - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
            target = render_dir / f"page-{page_no:03d}.png"
            pix.save(target)
            render_rows.append({"page": page_no, "path": normalize_relpath(target.relative_to(PROJECT_ROOT))})
        except Exception as exc:
            render_rows.append({"page": page_no, "path": "", "error": str(exc)})

    table_rows = extract_pdf_tables(path, tables_dir)
    caption_rows = extract_captions(full_text)
    write_csv(out_dir / "page_index.csv", page_rows, ["page", "text_chars", "embedded_images_kept"])
    write_csv(out_dir / "figures" / "embedded_image_index.csv", image_rows)
    write_csv(out_dir / "page_renders" / "render_index.csv", render_rows)
    write_csv(out_dir / "tables" / "table_index.csv", table_rows)
    write_csv(out_dir / "caption_index.csv", caption_rows)
    doc.close()
    return {
        "format": "pdf",
        "page_count": len(page_rows),
        "text_chars": len(full_text),
        "page_text_files": len(page_rows),
        "embedded_images_extracted": len(image_rows),
        "rendered_visual_pages": len([row for row in render_rows if row.get("path")]),
        "tables_extracted": len(table_rows),
        "captions_extracted": len(caption_rows),
        "pdf_metadata": pdf_metadata,
    }


def extract_pdf_tables(path: Path, tables_dir: Path) -> list[dict[str, Any]]:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return [{"page": "", "table_index": "", "path": "", "status": "pdfplumber_missing"}]

    rows: list[dict[str, Any]] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                try:
                    tables = page.extract_tables() or []
                except Exception as exc:
                    rows.append({"page": page_index, "table_index": "", "path": "", "status": f"failed:{exc}"})
                    continue
                for table_index, table in enumerate(tables, start=1):
                    cleaned = [["" if cell is None else str(cell).strip() for cell in row] for row in table if row]
                    if not cleaned or sum(bool(cell) for row in cleaned for cell in row) < 3:
                        continue
                    target = tables_dir / f"page-{page_index:03d}-table-{table_index:02d}.csv"
                    with target.open("w", encoding="utf-8", newline="") as handle:
                        writer = csv.writer(handle)
                        writer.writerows(cleaned)
                    rows.append(
                        {
                            "page": page_index,
                            "table_index": table_index,
                            "path": normalize_relpath(target.relative_to(PROJECT_ROOT)),
                            "rows": len(cleaned),
                            "cols": max(len(row) for row in cleaned),
                            "status": "ok",
                        }
                    )
    except Exception as exc:
        rows.append({"page": "", "table_index": "", "path": "", "status": f"open_failed:{exc}"})
    return rows


def extract_docx(path: Path, out_dir: Path) -> dict[str, Any]:
    text_dir = out_dir / "text"
    image_dir = out_dir / "figures" / "embedded"
    tables_dir = out_dir / "tables"
    render_dir = out_dir / "page_renders"
    text_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)

    paragraph_texts: list[str] = []
    table_rows: list[dict[str, Any]] = []
    image_rows: list[dict[str, Any]] = []
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        if "word/document.xml" in archive.namelist():
            root = ET.fromstring(archive.read("word/document.xml"))
            body = root.find("w:body", ns)
            if body is not None:
                table_index = 0
                for element in list(body):
                    if element.tag.endswith("}p"):
                        texts = [node.text or "" for node in element.findall(".//w:t", ns)]
                        paragraph = clean_text("".join(texts))
                        if paragraph:
                            paragraph_texts.append(paragraph)
                    elif element.tag.endswith("}tbl"):
                        table_index += 1
                        table_data: list[list[str]] = []
                        for tr in element.findall(".//w:tr", ns):
                            row: list[str] = []
                            for tc in tr.findall("./w:tc", ns):
                                texts = [node.text or "" for node in tc.findall(".//w:t", ns)]
                                row.append(clean_text("".join(texts)))
                            if row:
                                table_data.append(row)
                        if table_data:
                            target = tables_dir / f"docx-table-{table_index:02d}.csv"
                            with target.open("w", encoding="utf-8", newline="") as handle:
                                writer = csv.writer(handle)
                                writer.writerows(table_data)
                            table_rows.append(
                                {
                                    "page": "",
                                    "table_index": table_index,
                                    "path": normalize_relpath(target.relative_to(PROJECT_ROOT)),
                                    "rows": len(table_data),
                                    "cols": max(len(row) for row in table_data),
                                    "status": "ok",
                                }
                            )
        for member in archive.namelist():
            if member.startswith("word/media/") and not member.endswith("/"):
                target = image_dir / Path(member).name
                target.write_bytes(archive.read(member))
                image_rows.append(
                    {
                        "page": "",
                        "image_index": len(image_rows) + 1,
                        "path": normalize_relpath(target.relative_to(PROJECT_ROOT)),
                        "width": "",
                        "height": "",
                        "extension": target.suffix.lstrip("."),
                    }
                )

    full_text = clean_text("\n\n".join(paragraph_texts))
    write_text(text_dir / "full_text.txt", full_text + "\n")
    write_csv(out_dir / "tables" / "table_index.csv", table_rows)
    write_csv(out_dir / "figures" / "embedded_image_index.csv", image_rows)
    render_rows = render_docx_pages(path, render_dir)
    write_csv(out_dir / "page_renders" / "render_index.csv", render_rows)
    caption_rows = extract_captions(full_text)
    write_csv(out_dir / "caption_index.csv", caption_rows)
    return {
        "format": "docx",
        "page_count": "",
        "text_chars": len(full_text),
        "page_text_files": 0,
        "embedded_images_extracted": len(image_rows),
        "rendered_visual_pages": len([row for row in render_rows if row.get("path")]),
        "docx_render_status": render_rows[0].get("status", "not_attempted") if render_rows else "not_attempted",
        "tables_extracted": len(table_rows),
        "captions_extracted": len(caption_rows),
        "pdf_metadata": {},
    }


def render_docx_pages(path: Path, render_dir: Path) -> list[dict[str, Any]]:
    soffice = shutil.which("soffice")
    pdftoppm = shutil.which("pdftoppm")
    if not soffice:
        return [{"page": "", "path": "", "status": "soffice_missing"}]
    if not pdftoppm:
        return [{"page": "", "path": "", "status": "pdftoppm_missing"}]
    for stale_path in list(render_dir.glob("docx-page-*.png")) + list(render_dir.glob("._docx-page-*.png")):
        stale_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="paper_docx_render_") as tmp:
        tmp_path = Path(tmp)
        profile_dir = tmp_path / "lo_profile"
        pdf_dir = tmp_path / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [
                soffice,
                f"-env:UserInstallation=file://{profile_dir}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(pdf_dir),
                str(path),
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        pdf_candidates = sorted(pdf_dir.glob("*.pdf"))
        if result.returncode != 0 or not pdf_candidates:
            return [
                {
                    "page": "",
                    "path": "",
                    "status": f"convert_failed:{result.returncode}",
                    "stderr": result.stderr.strip()[:500],
                }
            ]
        pdf_path = pdf_candidates[0]
        prefix = render_dir / "docx-page"
        render = subprocess.run(
            [pdftoppm, "-png", str(pdf_path), str(prefix)],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if render.returncode != 0:
            return [
                {
                    "page": "",
                    "path": "",
                    "status": f"render_failed:{render.returncode}",
                    "stderr": render.stderr.strip()[:500],
                }
            ]
        for sidecar_path in render_dir.glob("._docx-page-*.png"):
            sidecar_path.unlink(missing_ok=True)
        rows: list[dict[str, Any]] = []
        image_paths = [image_path for image_path in sorted(render_dir.glob("docx-page-*.png")) if not image_path.name.startswith("._")]
        for page_index, image_path in enumerate(image_paths, start=1):
            rows.append(
                {
                    "page": page_index,
                    "path": normalize_relpath(image_path.relative_to(PROJECT_ROOT)),
                    "status": "ok",
                }
            )
        return rows or [{"page": "", "path": "", "status": "rendered_no_pages"}]


def extract_captions(full_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in CAPTION_PATTERN.finditer(full_text):
        caption = re.sub(r"\s+", " ", match.group(1)).strip()
        page_match = re.search(r"--- Page (\d+) ---", full_text[: match.start()][-2000:])
        rows.append(
            {
                "caption_index": len(rows) + 1,
                "page_hint": page_match.group(1) if page_match else "",
                "caption": caption[:1200],
            }
        )
    return rows


def sentence_split(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?。；;])\s+(?=[A-Z0-9(])", text)
    return [part.strip() for part in parts if len(part.strip()) > 30]


def extract_abstract(text: str) -> str:
    head = text[:25000]
    match = re.search(r"(?is)\babstract\b\s*[:.\-]?\s*(.{200,2500}?)(?=\bkeywords?\b|\bintroduction\b|\n\s*1\s+\.?\s*introduction\b)", head)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()[:1800]
    sentences = sentence_split(head)
    return " ".join(sentences[:5])[:1800]


def text_before_references(text: str) -> str:
    parts = re.split(r"(?im)^\s*(references|bibliography)\s*$", text, maxsplit=1)
    return parts[0] if parts else text


def detect_topics(text: str, title: str, authors: str, category: str, relpath: str) -> dict[str, int]:
    scoped_text = text_before_references(text)
    combined = f"{title}\n{authors}\n{category}\n{relpath}\n{scoped_text[:50000]}"
    scores: dict[str, int] = {}
    for topic, patterns in TOPIC_PATTERNS.items():
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, combined, flags=re.IGNORECASE))
        scores[topic] = count
    return scores


def active_topics_for(topic_scores: dict[str, int], title: str, authors: str, category: str, relpath: str) -> list[str]:
    lower = f"{title} {authors} {category} {relpath}".lower()
    active = {topic for topic, score in topic_scores.items() if score >= 3 and topic != "nodi_tsuyama"}
    if "tsuyama" in lower or "mawatari" in lower:
        active.add("nodi_tsuyama")
        if any(token in lower for token in ["nodi", "interferometric", "scattering"]):
            active.add("iscat_interferometry")
        if any(token in lower for token in ["diffraction", "nanochannel"]):
            active.add("diffraction_reference")
        if any(token in lower for token in ["pod", "photothermal", "absorption"]):
            active.add("photothermal_pod")
        if "nanofluidic" in lower or "flow" in lower:
            active.add("flow_transport_nanofluidics")
    category_forces = {
        "B. 光学衍射": "diffraction_reference",
        "C. NODI": "iscat_interferometry",
        "D. Mie": "mie_materials",
        "E. EV": "ev_ri_scatter_calibration",
        "F. Detector": "detector_threshold_reporting",
        "G. Flow": "flow_transport_nanofluidics",
        "H. POD": "photothermal_pod",
    }
    for prefix, topic in category_forces.items():
        if prefix in category:
            active.add(topic)
    if "misev" in lower or "minimal information" in lower or "miflowcyt" in lower:
        active.add("standards_reporting")
    return [topic for topic in TOPIC_PATTERNS if topic in active]


def priority_for(title: str, authors: str, category: str, relpath: str, active_topics: list[str]) -> str:
    lower = f"{title} {authors} {category} {relpath}".lower()
    if "tsuyama" in lower or "mawatari" in lower:
        return "critical"
    if any(token in lower for token in ["bohren", "johnson", "christy", "jain", "mie theory", "optical constants"]):
        return "high"
    if any(token in lower for token in ["fcm", "mis", "extracellular vesicle", "refractive index", "scatter calibration"]):
        return "high"
    if any(token in category for token in ["A. 核心论文", "D. Mie", "E. EV", "F. Detector"]):
        return "high"
    if any(token in category for token in ["C. NODI", "G. Flow", "H. POD"]):
        return "medium"
    if "iscat_interferometry" in active_topics or "flow_transport_nanofluidics" in active_topics:
        return "medium"
    return "background"


def engineering_family_notes(
    title: str, authors: str, category: str, relpath: str, active_topics: list[str]
) -> tuple[list[str], list[str]]:
    lower = f"{title} {authors} {category} {relpath}".lower()
    implications: list[str] = []
    boundaries: list[str] = []
    if "tsuyama" in lower or "mawatari" in lower:
        implications.append(
            "Treat as a primary paper-alignment source: extract geometry, wavelength, objective/NA, lock-in or readout frequency, particle ladder, pulse statistics, and explicit POD-vs-NODI scope."
        )
        boundaries.append(
            "Do not collapse POD thermal absorption, 2020 diffraction reference semantics, 2022 single-channel NODI, and 2024 paired POD+NODI into one calibration claim."
        )
    if "mie_materials" in active_topics or any(token in lower for token in ["bohren", "jain", "johnson", "christy", "optical constants"]):
        implications.append(
            "Use for intrinsic scattering/material checks: Mie cross sections, Au/Ag optical constants, size scaling, and wavelength-dependent material uncertainty."
        )
        boundaries.append(
            "Material or Mie agreement alone cannot validate detector transfer, blank reference, event threshold, or EV biological specificity."
        )
    if "ev_ri_scatter_calibration" in active_topics or "extracellular vesicle" in lower:
        implications.append(
            "Use for EV refractive-index, hollow/core-shell, calibration bead, and small-particle reporting constraints that shape EV-like material priors and claim language."
        )
        boundaries.append(
            "EV scatter-calibration papers do not by themselves prove NODI detection of biological exosomes without matched sample prep, blank, and calibration measurements."
        )
    if "detector_threshold_reporting" in active_topics:
        implications.append(
            "Use to audit threshold, LOD, detector sensitivity, calibration ladder, and reporting fields in dashboard/results claims."
        )
        boundaries.append(
            "Flow-cytometer sensitivity and fluorescence calibration units should not be transferred to NODI as absolute SNR without an explicit readout bridge."
        )
    if "iscat_interferometry" in active_topics:
        implications.append(
            "Use to check interferometric contrast logic: reference field, heterodyne scaling, background suppression, and event-level observables."
        )
        boundaries.append(
            "iSCAT contrast principles support mechanism choices but do not set nanofluidic channel geometry or POD/NODI lock-in electronics by themselves."
        )
    if "flow_transport_nanofluidics" in active_topics:
        implications.append(
            "Use for flow, Brownian transport, wall exclusion, pressure-driven injection, and transit-time plausibility checks."
        )
        boundaries.append(
            "Generic nanofluidic transport constraints need geometry and buffer-condition matching before becoming hard simulator parameters."
        )
    if "photothermal_pod" in active_topics:
        implications.append(
            "Use for POD absorption branch boundaries: thermal lens/source, solvent enhancement, differential frequency extraction, and paired POD/NODI separation."
        )
        boundaries.append(
            "Photothermal detectability must remain separate from NODI scattering detectability unless a paired-readout model is explicitly configured."
        )
    if not implications:
        implications.append(
            "Use as contextual support only unless later manual review finds a direct numeric constraint for the simulator."
        )
        boundaries.append(
            "No hard simulator parameter should be changed from this paper without a direct extracted value and a matching mechanism."
        )
    return implications, boundaries


def rank_evidence_sentences(sentences: list[str], topic_scores: dict[str, int]) -> list[str]:
    topic_terms = [pattern for patterns in TOPIC_PATTERNS.values() for pattern in patterns]
    ranked: list[tuple[float, str]] = []
    for sentence in sentences:
        if len(sentence) > 700:
            continue
        score = 0.0
        if UNIT_PATTERN.search(sentence):
            score += 4.0
        for pattern in topic_terms:
            if re.search(pattern, sentence, flags=re.IGNORECASE):
                score += 0.7
        if re.search(r"(?i)\b(objective|NA|wavelength|diameter|channel|threshold|frequency|SNR|refractive index|classification|detection|scattering|calibration|flow|diffusion)\b", sentence):
            score += 2.0
        if score >= 2.5:
            ranked.append((score, sentence))
    ranked.sort(key=lambda item: (-item[0], len(item[1])))
    deduped: list[str] = []
    seen: set[str] = set()
    for _, sentence in ranked:
        key = re.sub(r"\W+", "", sentence.lower())[:120]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sentence)
        if len(deduped) >= 24:
            break
    return deduped


def analyze_paper(unique: dict[str, Any], extraction: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    text_path = out_dir / "text" / "full_text.txt"
    full_text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
    scoped_text = text_before_references(full_text)
    identity = infer_bibliographic_identity(Path(unique["primary_relpath"]).stem)
    title = identity["title_guess"] or Path(unique["primary_relpath"]).stem
    authors = identity["authors_guess"]
    category = str(unique["category"])
    relpath = str(unique["primary_relpath"])
    abstract = extract_abstract(scoped_text)
    topic_scores = detect_topics(scoped_text, title, authors, category, relpath)
    active_topics = active_topics_for(topic_scores, title, authors, category, relpath)
    priority = priority_for(title, authors, category, relpath, active_topics)
    implications, boundaries = engineering_family_notes(title, authors, category, relpath, active_topics)
    sentences = sentence_split(scoped_text)
    evidence = rank_evidence_sentences(sentences, topic_scores)
    numeric_hits = []
    for sentence in evidence:
        matches = UNIT_PATTERN.findall(sentence)
        if matches:
            numeric_hits.extend(matches[:5])
    numeric_hits = list(dict.fromkeys(hit.strip() for hit in numeric_hits if hit.strip()))[:40]

    card = {
        **identity,
        "paper_id": unique["paper_id"],
        "sha256": unique["sha256"],
        "primary_relpath": unique["primary_relpath"],
        "duplicate_count": unique["duplicate_count"],
        "category": category,
        "engineering_priority": priority,
        "active_topics": active_topics,
        "topic_scores": topic_scores,
        "abstract_or_opening": abstract,
        "numeric_hits": numeric_hits,
        "evidence_sentences": evidence,
        "engineering_implications": implications,
        "claim_boundaries": boundaries,
        "extraction": extraction,
    }
    write_analysis_markdown(out_dir / "analysis.md", card)
    write_json(out_dir / "analysis.json", card)
    return card


def markdown_list(items: list[str]) -> str:
    if not items:
        return "- None captured.\n"
    return "".join(f"- {item}\n" for item in items)


def write_analysis_markdown(path: Path, card: dict[str, Any]) -> None:
    extraction = card["extraction"]
    evidence = card["evidence_sentences"][:12]
    numeric_hits = card["numeric_hits"][:30]
    text = f"""# {card['title_guess'] or card['paper_id']}

## Identity

- Paper ID: `{card['paper_id']}`
- Primary path: `{card['primary_relpath']}`
- Duplicate paths: {card['duplicate_count']}
- Category: {card['category']}
- Inferred authors: {card['authors_guess'] or 'not inferred'}
- Inferred year: {card['year_guess'] or 'not inferred'}
- Engineering priority: **{card['engineering_priority']}**
- Topic tags: {', '.join(card['active_topics']) if card['active_topics'] else 'none detected'}

## Extraction Status

- Format: {extraction.get('format')}
- Page count: {extraction.get('page_count')}
- Text characters: {extraction.get('text_chars')}
- Page text files: {extraction.get('page_text_files')}
- Embedded images extracted: {extraction.get('embedded_images_extracted')}
- Rendered figure/table pages: {extraction.get('rendered_visual_pages')}
- Tables extracted: {extraction.get('tables_extracted')}
- Captions extracted: {extraction.get('captions_extracted')}

## Abstract or Opening Summary

{card['abstract_or_opening'] or 'No abstract/opening text was extractable.'}

## Engineering Implications

{markdown_list(card['engineering_implications'])}
## Claim Boundaries

{markdown_list(card['claim_boundaries'])}
## Numerical and Parameter Hooks

{markdown_list([f'`{hit}`' for hit in numeric_hits])}
## Source-Evidence Sentences for Manual Follow-Up

{markdown_list(evidence)}
## How To Use This Paper In The Simulator Review

- Use this card as a pointer, not as a standalone claim source.
- For hard parameter changes, open `text/full_text.txt`, `caption_index.csv`, and any table CSVs in this paper directory.
- If a figure/table page is rendered, inspect `page_renders/` before citing a visual trend.
- If this paper is marked `critical` or `high`, compare its constraints against `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md` before changing claim wording.
"""
    write_text(path, text)


def process_unique_papers(instances: list[PaperInstance]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[PaperInstance]] = defaultdict(list)
    for instance in instances:
        grouped[instance.sha256].append(instance)

    unique_rows: list[dict[str, Any]] = []
    instance_rows: list[dict[str, Any]] = []
    analysis_cards: list[dict[str, Any]] = []

    for sha256, group in sorted(grouped.items(), key=lambda item: primary_sort_key(sorted(item[1], key=primary_sort_key)[0])):
        group_sorted = sorted(group, key=primary_sort_key)
        primary = group_sorted[0]
        identity = infer_bibliographic_identity(primary.path.stem)
        slug = slugify(identity["title_guess"] or primary.path.stem, f"paper_{sha256[:12]}")
        paper_id = f"{slug}_{sha256[:12]}"
        out_dir = OUTPUT_ROOT / paper_id
        if out_dir.exists():
            shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        duplicate_paths = [item.relpath for item in group_sorted]
        unique = {
            "paper_id": paper_id,
            "sha256": sha256,
            "primary_relpath": primary.relpath,
            "duplicate_paths": duplicate_paths,
            "duplicate_count": len(group_sorted),
            "category": infer_category(duplicate_paths),
            "suffix": primary.suffix,
        }
        try:
            if primary.suffix == ".pdf":
                extraction = extract_pdf(primary.path, out_dir)
            elif primary.suffix == ".docx":
                extraction = extract_docx(primary.path, out_dir)
            else:
                extraction = {"format": primary.suffix, "status": "unsupported"}
            extraction["status"] = "ok"
        except Exception as exc:
            extraction = {
                "format": primary.suffix,
                "status": f"failed:{type(exc).__name__}:{exc}",
                "page_count": "",
                "text_chars": 0,
                "page_text_files": 0,
                "embedded_images_extracted": 0,
                "rendered_visual_pages": 0,
                "tables_extracted": 0,
                "captions_extracted": 0,
                "pdf_metadata": {},
            }
        metadata = {**unique, "extraction": extraction, "generated_at": datetime.now(timezone.utc).isoformat()}
        write_json(out_dir / "metadata.json", metadata)
        card = analyze_paper(unique, extraction, out_dir)
        analysis_cards.append(card)

        unique_rows.append(
            {
                **{key: unique[key] for key in ["paper_id", "sha256", "primary_relpath", "category", "suffix", "duplicate_count"]},
                "title_guess": card["title_guess"],
                "authors_guess": card["authors_guess"],
                "year_guess": card["year_guess"],
                "engineering_priority": card["engineering_priority"],
                "topic_tags": ";".join(card["active_topics"]),
                "text_chars": extraction.get("text_chars", 0),
                "page_count": extraction.get("page_count", ""),
                "embedded_images_extracted": extraction.get("embedded_images_extracted", 0),
                "rendered_visual_pages": extraction.get("rendered_visual_pages", 0),
                "tables_extracted": extraction.get("tables_extracted", 0),
                "captions_extracted": extraction.get("captions_extracted", 0),
                "extraction_status": extraction.get("status", ""),
                "analysis_path": normalize_relpath((out_dir / "analysis.md").relative_to(PROJECT_ROOT)),
            }
        )
        for item in group_sorted:
            instance_rows.append(
                {
                    "relpath": item.relpath,
                    "sha256": sha256,
                    "paper_id": paper_id,
                    "is_primary": str(item.relpath == primary.relpath).lower(),
                    "primary_relpath": primary.relpath,
                }
            )
    return instance_rows, unique_rows, analysis_cards


def write_synthesis(unique_rows: list[dict[str, Any]], cards: list[dict[str, Any]]) -> None:
    priority_counts = Counter(row["engineering_priority"] for row in unique_rows)
    topic_counts: Counter[str] = Counter()
    for row in unique_rows:
        for topic in str(row.get("topic_tags", "")).split(";"):
            if topic:
                topic_counts[topic] += 1
    matrix_rows: list[dict[str, Any]] = []
    for row, card in zip(unique_rows, cards, strict=True):
        matrix_rows.append(
            {
                "paper_id": row["paper_id"],
                "title_guess": row["title_guess"],
                "year_guess": row["year_guess"],
                "category": row["category"],
                "priority": row["engineering_priority"],
                "topic_tags": row["topic_tags"],
                "primary_engineering_use": " | ".join(card["engineering_implications"][:2]),
                "main_boundary": " | ".join(card["claim_boundaries"][:2]),
                "analysis_path": row["analysis_path"],
            }
        )
    write_csv(OUTPUT_ROOT / "library_engineering_matrix.csv", matrix_rows)

    failed = [row for row in unique_rows if str(row.get("extraction_status")) != "ok"]
    low_text = [row for row in unique_rows if int(row.get("text_chars") or 0) < 1000]
    no_visual = [
        row
        for row in unique_rows
        if int(row.get("embedded_images_extracted") or 0) == 0 and int(row.get("rendered_visual_pages") or 0) == 0
    ]
    no_tables = [row for row in unique_rows if int(row.get("tables_extracted") or 0) == 0]

    gap_md = f"""# Paper Library Extraction Gap Review

Generated: {datetime.now(timezone.utc).isoformat()}

## Coverage

- File instances in manifest: {sum(int(row['duplicate_count']) for row in unique_rows)}
- Unique content hashes: {len(unique_rows)}
- Extraction failures: {len(failed)}
- Low-text unique files (<1000 chars): {len(low_text)}
- Unique files with no extracted embedded images or rendered figure/table pages: {len(no_visual)}
- Unique files with no machine-extracted tables: {len(no_tables)}

## Priority Distribution

{markdown_list([f'{key}: {value}' for key, value in sorted(priority_counts.items())])}
## Topic Distribution

{markdown_list([f'{key}: {value}' for key, value in sorted(topic_counts.items())])}
## Extraction Failures

{markdown_list([f"{row['paper_id']} - {row['extraction_status']}" for row in failed])}
## Low-Text Items

{markdown_list([f"{row['paper_id']} - {row['text_chars']} chars" for row in low_text])}
## Items Without Visual Evidence Files

{markdown_list([row['paper_id'] for row in no_visual[:80]])}
## Items Without Machine-Extracted Tables

{markdown_list([row['paper_id'] for row in no_tables[:80]])}
## Residual Risks

- PDF table extraction is heuristic; rendered page inspection is still required before citing exact table values.
- Embedded image extraction can capture panels/logos separately; rendered figure/table pages are the safer visual review surface.
- DOCX layout is rendered through LibreOffice/`soffice` when available; check each DOCX `page_renders/render_index.csv` for conversion status.
- The analysis cards are engineering triage artifacts. Critical and high-priority papers should still be manually reopened before any hard simulator parameter or claim text is changed.
"""
    write_text(OUTPUT_ROOT / "library_gap_review.md", gap_md)

    critical_high = [row for row in unique_rows if row["engineering_priority"] in {"critical", "high"}]
    synthesis = f"""# Full Paper Library Extraction and Engineering Analysis

Date: 2026-05-17

## Executive Status

The full local paper library has been deduplicated, extracted, and analyzed into `papers/analysis_full_v1/`.

- Local file instances covered: {sum(int(row['duplicate_count']) for row in unique_rows)}
- Unique content hashes analyzed: {len(unique_rows)}
- Critical/high-priority papers: {len(critical_high)}
- Extraction failures: {len(failed)}
- Low-text files needing caution: {len(low_text)}

## How To Read The Library

Start with:

1. `papers/analysis_full_v1/library_engineering_matrix.csv`
2. `papers/analysis_full_v1/library_gap_review.md`
3. Individual `analysis.md` cards for critical and high-priority papers

The per-paper cards are designed to support engineering decisions, not just bibliographic indexing. Each card separates usable constraints from claim boundaries so that NODI, POD, EV calibration, detector reporting, and material/Mie evidence do not get mixed into one over-broad validation statement.

## Priority Counts

{markdown_list([f'{key}: {value}' for key, value in sorted(priority_counts.items())])}
## Topic Counts

{markdown_list([f'{key}: {value}' for key, value in sorted(topic_counts.items())])}
## Critical And High-Priority Reading Queue

{markdown_list([f"{row['engineering_priority']} - {row['title_guess']} ({row['analysis_path']})" for row in critical_high])}
## Engineering Interpretation

The library now supports a layered reading of the project:

- Tsuyama/Mawatari papers remain the direct alignment spine for diffraction reference semantics, NODI selected-annulus/pulse interpretation, and POD-vs-NODI boundaries.
- Mie/material papers support intrinsic scattering and Au/Ag optical-constant uncertainty, but they do not validate event readout or detector thresholds.
- iSCAT/interferometric papers support the reference-field and heterodyne logic, but they do not directly determine nanofluidic geometry.
- EV refractive-index/scatter-calibration/reporting papers constrain EV material priors and claim language, especially around biological specificity and calibration status.
- Flow/nanofluidic transport papers should inform transit, diffusion, wall exclusion, and injection assumptions before any future measured-data closure.

## Completion Review

The extraction pass created a traceable artifact for every unique local paper. Remaining caution is mostly about extraction fidelity rather than missing coverage: table extraction is not guaranteed perfect, some figures require rendered-page review, and DOCX layout rendering should be checked through each DOCX render index.
"""
    write_text(OUTPUT_ROOT / "library_auto_synthesis.md", synthesis)


def main() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    instances = scan_instances()
    instance_rows, unique_rows, cards = process_unique_papers(instances)
    write_csv(OUTPUT_ROOT / "manifest.csv", instance_rows)
    write_csv(OUTPUT_ROOT / "manifest_unique.csv", unique_rows)
    write_json(
        OUTPUT_ROOT / "run_manifest.json",
        {
            "schema": "paper_library_extraction_analysis_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_root": "papers",
            "output_root": normalize_relpath(OUTPUT_ROOT.relative_to(PROJECT_ROOT)),
            "file_instances": len(instance_rows),
            "unique_papers": len(unique_rows),
        },
    )
    write_synthesis(unique_rows, cards)
    print(f"file_instances={len(instance_rows)}")
    print(f"unique_papers={len(unique_rows)}")
    print(f"output={OUTPUT_ROOT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
