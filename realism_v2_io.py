"""I/O helpers for realism-v2 result and provenance artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_run_manifest(
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    project_root: Path,
    write_root_manifest: bool,
) -> None:
    """Write the stage-local manifest and optionally update the tracked root copy."""
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    if write_root_manifest:
        (project_root / "run_manifest.json").write_text(manifest_text, encoding="utf-8")
