"""I/O helpers for realism-v2 result and provenance artifacts."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any


csv.field_size_limit(16 * 1024 * 1024)


def resolve_artifact_path(path: str | Path) -> Path:
    """Resolve a logical artifact path, allowing a gzip-compressed twin."""
    artifact_path = Path(path)
    if artifact_path.exists():
        return artifact_path
    gzip_path = artifact_path.with_name(f"{artifact_path.name}.gz")
    if gzip_path.exists():
        return gzip_path
    return artifact_path


def open_text_artifact(path: str | Path, *, newline: str | None = None):
    artifact_path = resolve_artifact_path(path)
    if artifact_path.suffix == ".gz":
        return gzip.open(artifact_path, mode="rt", newline=newline, encoding="utf-8")
    return artifact_path.open(newline=newline, encoding="utf-8")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    requested_path = Path(path)
    artifact_path = resolve_artifact_path(requested_path)
    if artifact_path.suffix == ".gz" and artifact_path != requested_path:
        with gzip.open(artifact_path, mode="rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    else:
        with artifact_path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with open_text_artifact(path, newline="") as handle:
        return list(csv.DictReader(handle))


def read_csv_headers(path: str | Path) -> list[str]:
    with open_text_artifact(path, newline="") as handle:
        try:
            return list(next(csv.reader(handle)))
        except StopIteration:
            raise ValueError(f"CSV file has no header row: {path}") from None


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    _atomic_write_text(path, buffer.getvalue())


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            dir=path.parent,
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path.replace(path)
    except Exception:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        raise


def write_json_atomic(
    path: Path,
    payload: Any,
    *,
    indent: int | None = 2,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
    allow_nan: bool = False,
) -> None:
    """Write JSON through the same temporary-file replacement path as manifests."""
    text = json.dumps(
        payload,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        allow_nan=allow_nan,
    )
    _atomic_write_text(path, text)


def write_run_manifest(
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    project_root: Path,
    write_root_manifest: bool,
) -> None:
    """Write the stage-local manifest and optionally update the tracked root copy."""
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True)
    _atomic_write_text(manifest_path, manifest_text)
    if write_root_manifest:
        _atomic_write_text(project_root / "run_manifest.json", manifest_text)
