from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from nodi_simulator.post_v2_bounded_solver_authorization_gate import (
    verify_gate_package,
)
from nodi_simulator.review_package import PROJECT_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify P5 bounded solver authorization-gate contracts."
    )
    parser.add_argument(
        "--package-root",
        default=str(PROJECT_ROOT),
        help="Repository/package root containing P5 authorization-gate artifacts.",
    )
    args = parser.parse_args()
    for line in verify_gate_package(Path(args.package_root)):
        print(line)


if __name__ == "__main__":
    main()
