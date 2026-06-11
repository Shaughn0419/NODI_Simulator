from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from nodi_simulator.review_package import PROJECT_ROOT, verify_review_package


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the post-v2 review package.")
    parser.add_argument(
        "--package-root",
        default=str(PROJECT_ROOT),
        help="Root of an unzipped review package or the repository/package directory.",
    )
    parser.add_argument(
        "--mode",
        choices=("local-dev", "external-review"),
        default="local-dev",
        help="external-review disallows dirty build manifests; local-dev permits --allow-dirty.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow a dirty worktree for local P0a development verification.",
    )
    parser.add_argument(
        "--external-bundle-mode",
        action="store_true",
        help=(
            "Verify an exported/unzipped bundle without requiring its manifest "
            "commit to be reachable from the local git checkout."
        ),
    )
    args = parser.parse_args()
    allow_dirty = args.allow_dirty or (args.mode == "local-dev" and not args.external_bundle_mode)
    for line in verify_review_package(
        Path(args.package_root),
        allow_dirty=allow_dirty,
        external_bundle_mode=bool(args.external_bundle_mode),
    ):
        print(line)


if __name__ == "__main__":
    main()
