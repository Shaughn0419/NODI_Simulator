from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from nodi_simulator.review_package import PROJECT_ROOT, generate_paper_provenance


def main() -> None:
    paths = generate_paper_provenance(PROJECT_ROOT)
    for path in paths:
        print(path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
