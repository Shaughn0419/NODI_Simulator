from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from nodi_simulator.realism_v2_io import write_csv_rows, write_json_atomic


def write_csv_records(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    """Write non-empty mapping records to a CSV file."""
    if not records:
        raise ValueError("records must be non-empty")
    write_csv_rows(path, [dict(record) for record in records])


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
        payload,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        allow_nan=allow_nan,
    )


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
