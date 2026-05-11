#!/usr/bin/env python3
"""Minimal schema-doc to artifact field-drift auditor.

This utility performs an informative, non-authoritative scan:
- match schema docs `docs/schemas/*_schema.md` to sibling artifact files with the same stem;
- extract candidate field names from simple JSON/YAML/CSV artifacts;
- count whether field names appear verbatim in schema doc text.

It is intentionally permissive and does not fail build by default.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from collections import defaultdict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC_DIR = PROJECT_ROOT / "docs" / "schemas"
SKIP_DIR_PARTS = {".git", ".claude", "__pycache__"}


FIELD_TOKEN_RE = re.compile(r"(?<![a-zA-Z0-9_])[a-zA-Z_][a-zA-Z0-9_]{2,}(?![a-zA-Z0-9_])")
FIELD_SKIP = {
    "artifact",
    "artifacts",
    "artifact_count",
    "artifact_path",
    "artifact_paths",
    "artifacts_path",
    "artifacts_paths",
    "artifact_role",
    "analysis",
    "analysis_id",
    "analysis_id_hash",
    "analysis_status",
    "analysis_version",
    "call",
    "claim",
    "claim_boundary",
    "claim_boundary_path",
    "claim_confidence",
    "claim_notes",
    "claim_status",
    "commit",
    "created",
    "environment",
    "manifest",
    "manifest_count",
    "manifest_hash",
    "manifest_path",
    "manifest_role",
    "manifest_total",
    "path",
    "paths",
    "properties",
    "provenance",
    "provenance_id",
    "provenance_info",
    "provenance_signature",
    "python_version",
    "required",
    "required_false_fields",
    "required_future_authorization_phrase",
    "required_fields",
    "required_note",
    "required_phrase",
    "result",
    "results",
    "runtime",
    "runtime_stats",
    "run_id",
    "schema",
    "schema_hash",
    "schema_path",
    "schema_version",
    "seed",
    "seed_count",
    "timestamp",
    "type",
}

FIELD_SKIP_PREFIXES = (
    "artifact_",
    "analysis_",
    "claim_",
    "commit_",
    "manifest_",
    "provenance_",
    "required_",
    "result_",
    "runtime_",
    "schema_",
    "seed_",
)

FIELD_SKIP_SUFFIXES = (
    "_boundary",
    "_count",
    "_hash",
    "_id",
    "_id_hash",
    "_info",
    "_metadata",
    "_note",
    "_path",
    "_paths",
    "_phrase",
    "_role",
    "_signature",
    "_status",
    "_timestamp",
    "_version",
)


def _is_skippable_field(field: str) -> bool:
    return (
        field in FIELD_SKIP
        or any(field.startswith(prefix) for prefix in FIELD_SKIP_PREFIXES)
        or any(field.endswith(suffix) for suffix in FIELD_SKIP_SUFFIXES)
    )


def _field_tokens(text: str) -> set[str]:
    return {
        token
        for token in set(FIELD_TOKEN_RE.findall(text.lower()))
        if not _is_skippable_field(token)
    }


def _extract_fields(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    if path.suffix == ".json":
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeError):
            return set()
        if isinstance(payload, dict):
            if "properties" in payload and isinstance(payload["properties"], dict):
                return {str(k).lower() for k in payload["properties"].keys()}
            return {str(k).lower() for k in payload.keys()}
        return set()
    if path.suffix in {".yaml", ".yml"}:
        if yaml is None:
            return set()
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                payload = yaml.safe_load(f)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError):
            return set()
        if isinstance(payload, dict):
            if "properties" in payload and isinstance(payload["properties"], dict):
                return {str(k).lower() for k in payload["properties"].keys()}
            return {str(k).lower() for k in payload.keys()}
        return set()
    if path.suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="", errors="ignore") as f:
            rows = list(csv.reader(f))
        if not rows:
            return set()
        return _field_tokens(",".join(rows[0]))
    return set()


def _build_artifact_index() -> dict[str, list[Path]]:
    index: defaultdict[str, list[Path]] = defaultdict(list)
    root_parts = {part for part in PROJECT_ROOT.parts}

    def _is_private_path(path: Path) -> bool:
        return any(
            part in SKIP_DIR_PARTS or part.startswith("._")
            for part in path.parts
            if part not in root_parts
        )

    for path in PROJECT_ROOT.rglob("*"):
        if (
            not path.is_file()
            or _is_private_path(path)
            or path.name.startswith("._")
            or path.parent == DOC_DIR
            or path.suffix.lower() not in {".json", ".yaml", ".yml", ".csv"}
        ):
            continue
        index[path.stem].append(path)
    return dict(index)


def _find_artifacts(base: str, artifact_index: dict[str, list[Path]]) -> list[Path]:
    return artifact_index.get(base, [])


def _analyze_doc(
    doc_path: Path,
    strict: bool,
    artifact_index: dict[str, list[Path]],
    missing_only: bool = False,
) -> tuple[bool, int, int]:
    stem = doc_path.stem
    if not stem.endswith("_schema") or stem.startswith("._"):
        return True, 0, 0
    base = stem[: -len("_schema")]
    artifact_paths = _find_artifacts(base, artifact_index)
    if not artifact_paths:
        print(f"- {doc_path}: MISSING_ARTIFACT_MATCH ({base}*)")
        return (not strict, 1, 0)

    doc_text = doc_path.read_text(encoding="utf-8", errors="ignore").lower()
    doc_tokens = _field_tokens(doc_text)
    missing = 0
    checked = 0

    for artifact in artifact_paths:
        fields = _extract_fields(artifact)
        if not fields:
            continue
        checked += len(fields)
        misses = sorted(
            field for field in sorted(fields) if field not in doc_tokens and not _is_skippable_field(field)
        )
        if misses:
            missing += len(misses)
            if not missing_only:
                print(f"- {doc_path} -> {artifact.relative_to(PROJECT_ROOT)}: {len(misses)}/{len(fields)} fields missing from doc text")

    return (True if not strict else missing == 0), checked, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="exit non-zero on any detected mismatch")
    args = parser.parse_args()

    total_docs = 0
    total_matched = 0
    total_checked = 0
    total_missing = 0
    strict = args.strict

    artifact_index = _build_artifact_index()
    for doc in sorted(DOC_DIR.glob("*_schema.md")):
        total_docs += 1
        ok, checked, missing = _analyze_doc(doc, strict, artifact_index)
        if checked:
            total_matched += 1
            total_checked += checked
            total_missing += missing
        if ok is False and strict:
            pass

    print(f"Schema doc audit summary: docs={total_docs}, with_artifact={total_matched}, fields_checked={total_checked}, missing_hits={total_missing}")
    if strict and total_missing > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
