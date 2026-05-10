from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from nodi_simulator.post_v2_p8_closure_p9_authorization_design import (
    write_closure_and_design_packages,
)
from nodi_simulator.review_package import PROJECT_ROOT


def main() -> None:
    for path in write_closure_and_design_packages(PROJECT_ROOT):
        print(path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
