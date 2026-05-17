"""Paper provenance generation for the review package."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .realism_v2_io import sha256_file, write_csv_rows, write_json_atomic
from .review_package_json import load_json_compatible as _load_json_compatible
from .review_package_paths import normalize_relpath as _normalize_relpath


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER_PROVENANCE_DIR = Path("papers/provenance")


def _default_paper_overrides(project_root: Path) -> dict[str, Any]:
    papers = scan_paper_files(project_root)
    return {
        "schema": "ev_nodi_paper_manifest_overrides_v1",
        "notes": (
            "Claim-bearing rows require explicit manual_override or verified_source metadata. "
            "Default rows are not claim-bearing."
        ),
        "papers": {
            paper_id: {
                "title": "",
                "authors": "",
                "year": "",
                "doi": "",
                "license_or_access_note": "local_reference_copy_not_relicensed",
                "used_for_claim_area": "",
                "metadata_source": "not_claim_bearing_not_used_for_claim_area",
            }
            for paper_id, _ in papers
        },
        "unavailable_or_not_packaged_papers": [],
    }


def paper_id_for_path(relpath: str) -> str:
    normalized = _normalize_relpath(relpath)
    stem = Path(normalized).stem
    slug = re.sub(r"[^A-Za-z0-9]+", "_", unicodedata.normalize("NFKD", stem)).strip("_")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"{slug[:48]}_{digest}" if slug else f"paper_{digest}"


def scan_paper_files(project_root: Path = PROJECT_ROOT) -> list[tuple[str, str]]:
    paper_root = project_root / "papers"
    paths: list[Path] = []
    for suffix in ("*.pdf", "*.docx"):
        paths.extend(paper_root.glob(suffix))
    relpaths = sorted(
        _normalize_relpath(path.relative_to(project_root))
        for path in paths
        if not path.name.startswith("._")
    )
    return [(paper_id_for_path(relpath), relpath) for relpath in relpaths]


def ensure_paper_overrides(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / PAPER_PROVENANCE_DIR / "paper_manifest_overrides.yaml"
    if not output.exists():
        write_json_atomic(output, _default_paper_overrides(project_root), sort_keys=True)
    return output


def load_paper_overrides(path: Path) -> dict[str, Any]:
    payload = _load_json_compatible(path)
    if not isinstance(payload.get("papers", {}), dict):
        raise ValueError("paper provenance overrides must contain a papers object")
    return payload


def _claim_metadata_is_verified(row: Mapping[str, Any]) -> bool:
    source = str(row.get("metadata_source", ""))
    return source in {"manual_override", "verified_source"}


def validate_paper_overrides(payload: Mapping[str, Any]) -> None:
    papers = payload.get("papers", {})
    if not isinstance(papers, Mapping):
        raise ValueError("paper provenance overrides must contain a papers object")
    for paper_id, row in papers.items():
        if not isinstance(row, Mapping):
            raise ValueError(f"paper override must be an object: {paper_id}")
        if not row.get("used_for_claim_area"):
            continue
        required = ("title", "authors", "year", "doi")
        missing = [field for field in required if not str(row.get(field, "")).strip()]
        if missing or not _claim_metadata_is_verified(row):
            raise ValueError(
                "claim-bearing paper metadata must be manual_override or verified_source "
                f"with title/authors/year/doi: {paper_id}"
            )


def generate_paper_provenance(project_root: Path = PROJECT_ROOT) -> list[Path]:
    provenance_dir = project_root / PAPER_PROVENANCE_DIR
    provenance_dir.mkdir(parents=True, exist_ok=True)
    overrides_path = ensure_paper_overrides(project_root)
    overrides = load_paper_overrides(overrides_path)
    validate_paper_overrides(overrides)
    override_rows = overrides.get("papers", {})

    rows: list[dict[str, Any]] = []
    hash_lines: list[str] = []
    for paper_id, relpath in scan_paper_files(project_root):
        override = dict(override_rows.get(paper_id, {}))
        path = project_root / relpath
        digest = sha256_file(path)
        rows.append(
            {
                "paper_id": paper_id,
                "title": str(override.get("title", "")),
                "authors": str(override.get("authors", "")),
                "year": str(override.get("year", "")),
                "doi": str(override.get("doi", "")),
                "local_path": relpath,
                "sha256": digest,
                "included_in_package": "true",
                "license_or_access_note": str(
                    override.get("license_or_access_note", "local_reference_copy_not_relicensed")
                ),
                "used_for_claim_area": str(override.get("used_for_claim_area", "")),
                "metadata_source": str(
                    override.get("metadata_source", "not_claim_bearing_not_used_for_claim_area")
                ),
            }
        )
        hash_lines.append(f"{digest}  {relpath}\n")

    unavailable_rows = list(overrides.get("unavailable_or_not_packaged_papers", []))
    packaged_ids = {row["paper_id"] for row in rows}
    unavailable_ids = {str(row.get("paper_id", "")) for row in unavailable_rows}
    overlap = packaged_ids.intersection(unavailable_ids)
    if overlap:
        raise ValueError(f"paper provenance packaged/unavailable overlap: {sorted(overlap)}")

    write_csv_rows(provenance_dir / "paper_manifest.csv", rows)
    (provenance_dir / "paper_hashes.sha256").write_text("".join(hash_lines), encoding="utf-8")
    write_csv_rows(
        provenance_dir / "unavailable_or_not_packaged_papers.csv",
        unavailable_rows
        or [
            {
                "paper_id": "none_declared",
                "title": "",
                "reason": "no_unavailable_claim_area_papers_declared",
                "used_for_claim_area": "",
            }
        ],
    )
    (provenance_dir / "paper_bibliography.bib").write_text(
        "% Bibliography entries are intentionally manual/verified only.\n",
        encoding="utf-8",
    )
    (provenance_dir / "paper_provenance_notes.md").write_text(
        "# Paper Provenance\n\n"
        "Paper files are local reference copies for a no-measured-data relative audit. "
        "Claim-bearing metadata must come from manual overrides or verified sources; "
        "the generator does not infer bibliographic claims from filenames.\n",
        encoding="utf-8",
    )
    return [
        provenance_dir / "paper_manifest.csv",
        provenance_dir / "paper_manifest_overrides.yaml",
        provenance_dir / "paper_hashes.sha256",
        provenance_dir / "paper_bibliography.bib",
        provenance_dir / "paper_provenance_notes.md",
        provenance_dir / "unavailable_or_not_packaged_papers.csv",
    ]
