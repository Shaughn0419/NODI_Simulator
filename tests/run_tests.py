"""
Compatibility test runner for the NODI simulator.

This wrapper keeps the older `python tests/run_tests.py --workers 8` command
working while still covering every pytest module under `tests/`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[1]
PYTEST_VENDOR = REPO_ROOT / ".pytest_vendor"


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_parts = [str(REPO_ROOT)]
    if PYTEST_VENDOR.is_dir():
        pythonpath_parts.insert(0, str(PYTEST_VENDOR))
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return env


def _run(label: str, args: list[str]) -> int:
    print(f"\n== {label} ==")
    print(" ".join(args))
    return subprocess.run(args, cwd=REPO_ROOT, env=_build_env(), check=False).returncode


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NODI pytest regression suite.")
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Parallel workers for non-AppTest tests (default: {DEFAULT_WORKERS}).",
    )
    parser.add_argument(
        "--skip-app-interactions",
        action="store_true",
        help="Skip Streamlit AppTest interaction tests.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    workers = max(1, int(args.workers))

    parallel_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "-m",
        "not app_interactions",
        "-n",
        str(workers),
        "-q",
    ]
    result = _run("pytest parallel lane", parallel_cmd)

    if not args.skip_app_interactions:
        serial_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-m",
            "app_interactions",
            "-q",
        ]
        result = result or _run("pytest AppTest lane", serial_cmd)

    return result


if __name__ == "__main__":
    raise SystemExit(main())
