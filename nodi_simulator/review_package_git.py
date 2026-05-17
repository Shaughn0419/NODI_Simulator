"""Git metadata helpers for review-package manifests."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _git_value(args: Sequence[str], *, project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def git_commit(project_root: Path = PROJECT_ROOT) -> str | None:
    return _git_value(["rev-parse", "HEAD"], project_root=project_root)


def git_commit_is_ancestor(
    ancestor_commit: str,
    descendant_commit: str,
    project_root: Path = PROJECT_ROOT,
) -> bool:
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor_commit, descendant_commit],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def git_dirty(project_root: Path = PROJECT_ROOT) -> bool:
    status = _git_value(["status", "--short"], project_root=project_root)
    return bool(status)


def git_tracked_paths(project_root: Path = PROJECT_ROOT) -> frozenset[str] | None:
    output = _git_value(["ls-files"], project_root=project_root)
    if output is None:
        return None
    return frozenset(line for line in output.splitlines() if line)
