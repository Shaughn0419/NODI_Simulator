from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from nodi_simulator.post_v2_bounded_physical_solver_readiness import (
    verify_readiness_package,
)
from nodi_simulator.review_package import PROJECT_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify P2 bounded physical-solver readiness contracts."
    )
    parser.add_argument(
        "--package-root",
        default=str(PROJECT_ROOT),
        help="Repository/package root containing P2 readiness artifacts.",
    )
    args = parser.parse_args()
    for line in verify_readiness_package(Path(args.package_root)):
        print(line)


if __name__ == "__main__":
    main()
