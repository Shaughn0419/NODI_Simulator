from __future__ import annotations

import argparse
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from nodi_simulator.realism_v2_io import write_csv_rows, write_json_atomic


def write_csv_records(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    """Write non-empty mapping records to a CSV file."""
    if not records:
        raise ValueError("records must be non-empty")
    write_csv_rows(path, [dict(record) for record in records])


def json_safe(value: Any) -> Any:
    """Convert common numpy/non-finite values into strict JSON-compatible values."""
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json_file(
    path: Path,
    payload: Any,
    *,
    sort_keys: bool = True,
    ensure_ascii: bool = False,
    allow_nan: bool = False,
) -> None:
    """Write JSON atomically with the project-wide realism-v2 I/O helper."""
    write_json_atomic(
        path,
        json_safe(payload),
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        allow_nan=allow_nan,
    )


def dataframe_to_markdown_table(
    df: Any,
    *,
    float_format: str = ".6g",
    empty_message: str | None = None,
) -> str:
    """Render a small pandas DataFrame as a compact GitHub-style Markdown table."""
    import pandas as pd

    if df.empty and empty_message is not None:
        return empty_message
    display = df.copy()
    for column in display.columns:
        if pd.api.types.is_float_dtype(display[column]):
            display[column] = display[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):{float_format}}"
            )
        else:
            display[column] = display[column].map(lambda value: "" if pd.isna(value) else str(value))
    columns = list(display.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in display.itertuples(index=False)
    )
    return "\n".join(lines)


def format_record_lines(
    records: Sequence[Mapping[str, Any]],
    template: str,
    *,
    empty_message: str | None = None,
) -> str:
    """Format mapping records with one template per non-empty record."""
    lines = [template.format(**record) for record in records if record]
    if lines:
        return "\n".join(lines)
    if empty_message is not None:
        return empty_message
    return ""


def parse_realism_v2_writer_args(
    argv: Sequence[str] | None,
    *,
    description: str | None,
    default_output_dir: str | Path,
    output_help: str,
) -> argparse.Namespace:
    """Parse the common guarded writer flags for realism-v2 one-shot tools."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Confirm intentional execution of this historical one-shot writer.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(default_output_dir),
        help=output_help,
    )
    parser.add_argument(
        "--write-root-manifest",
        action="store_true",
        help="Also update the repository-root run_manifest.json.",
    )
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("refusing to execute one-shot writer without --execute")
    return args
