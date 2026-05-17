"""Compatibility test runner for the NODI simulator.

The full suite has two lanes:

* normal pytest tests, which are xdist-safe and can use multiple workers
* Streamlit AppTest interaction tests, which must stay serial inside their lane

The lanes run concurrently by default so the AppTest wall time overlaps with
the parallel pytest lane.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


MAX_DEFAULT_WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[1]
PYTEST_VENDOR = REPO_ROOT / ".pytest_vendor"
PROCESS_SHUTDOWN_TIMEOUT_S = 10.0
APPLEDOUBLE_SKIP_DIRS = {
    ".codex_pdf_venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv-tests",
    "__pycache__",
    "exports",
    "review_bundles",
}


def _clean_appledouble_metadata() -> None:
    """Remove macOS AppleDouble files before pytest sees result directories."""
    for path in REPO_ROOT.rglob("._*"):
        try:
            rel_parts = path.relative_to(REPO_ROOT).parts
        except ValueError:
            continue
        if any(part in APPLEDOUBLE_SKIP_DIRS for part in rel_parts[:-1]):
            continue
        if path.is_file():
            path.unlink()


def _build_env(*, require_xdist: bool) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_parts = [str(REPO_ROOT)]
    if PYTEST_VENDOR.is_dir():
        pythonpath_parts.insert(0, str(PYTEST_VENDOR))
    elif require_xdist:
        raise RuntimeError(
            f"Missing {PYTEST_VENDOR}. Install or vendor pytest-xdist before using workers."
        )
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


def _run(label: str, args: list[str]) -> int:
    print(f"\n== {label} ==", flush=True)
    print(" ".join(args), flush=True)
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=_build_env(require_xdist="-n" in args),
        check=False,
    ).returncode


def _terminate_process_tree(process: subprocess.Popen[bytes], *, force: bool = False) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        signal_to_send = signal.SIGKILL if force else signal.SIGTERM
        try:
            os.killpg(process.pid, signal_to_send)
            return
        except ProcessLookupError:
            return
    if force:
        process.kill()
    else:
        process.terminate()


def _stop_pending_processes(pending: set[subprocess.Popen[bytes]]) -> None:
    for process in pending:
        _terminate_process_tree(process)
    deadline = time.monotonic() + PROCESS_SHUTDOWN_TIMEOUT_S
    remaining = set(pending)
    while remaining and time.monotonic() < deadline:
        for process in list(remaining):
            if process.poll() is not None:
                remaining.remove(process)
        time.sleep(0.1)
    for process in remaining:
        _terminate_process_tree(process, force=True)
    for process in remaining:
        process.wait(timeout=PROCESS_SHUTDOWN_TIMEOUT_S)


def _run_concurrent(lanes: list[tuple[str, list[str]]]) -> int:
    processes: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        for label, args in lanes:
            print(f"\n== {label} ==", flush=True)
            print(" ".join(args), flush=True)
            env = _build_env(require_xdist="-n" in args)
            process = (
                subprocess.Popen(
                    args,
                    cwd=REPO_ROOT,
                    env=env,
                    start_new_session=True,
                )
                if os.name == "posix"
                else subprocess.Popen(args, cwd=REPO_ROOT, env=env)
            )
            processes.append((label, process))

        first_failure = 0
        pending = {process for _, process in processes}
        while pending:
            for label, process in processes:
                if process not in pending:
                    continue
                return_code = process.poll()
                if return_code is None:
                    continue
                pending.remove(process)
                if return_code:
                    first_failure = first_failure or return_code
                    _stop_pending_processes(pending)
                    print(
                        f"\n== {label} failed with exit code {return_code} ==",
                        flush=True,
                    )
                    return first_failure
            time.sleep(0.2)
        return first_failure
    except KeyboardInterrupt:
        pending = {process for _, process in processes if process.poll() is None}
        _stop_pending_processes(pending)
        raise


def _default_workers(*, skip_app_interactions: bool) -> int:
    cpu_count = os.cpu_count() or 2
    reserved_for_app_lane = 0 if skip_app_interactions else 1
    return max(1, min(MAX_DEFAULT_WORKERS, cpu_count - reserved_for_app_lane))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NODI pytest regression suite.")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=(
            "Parallel workers for non-AppTest tests. Defaults to one less than "
            f"the detected CPU count, capped at {MAX_DEFAULT_WORKERS}, when "
            "AppTest is also running."
        ),
    )
    parser.add_argument(
        "--skip-app-interactions",
        action="store_true",
        help="Skip Streamlit AppTest interaction tests.",
    )
    parser.add_argument(
        "--sequential-lanes",
        action="store_true",
        help="Run the parallel pytest lane before the serial AppTest lane.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    workers = (
        max(1, int(args.workers))
        if args.workers is not None
        else _default_workers(skip_app_interactions=args.skip_app_interactions)
    )
    _clean_appledouble_metadata()

    parallel_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "xdist.plugin",
        "tests",
        "-m",
        "not app_interactions",
        "-n",
        str(workers),
        "-q",
        "-o",
        "cache_dir=.pytest_cache/parallel",
    ]
    lanes = [("pytest parallel lane", parallel_cmd)]

    if not args.skip_app_interactions:
        serial_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-m",
            "app_interactions",
            "-q",
            "-o",
            "cache_dir=.pytest_cache/app",
        ]
        lanes.append(("pytest AppTest lane", serial_cmd))

    if args.sequential_lanes or len(lanes) == 1:
        result = 0
        for label, cmd in lanes:
            result = result or _run(label, cmd)
        return result
    return _run_concurrent(lanes)


if __name__ == "__main__":
    raise SystemExit(main())
