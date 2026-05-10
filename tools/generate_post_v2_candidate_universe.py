from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_PATH))

from nodi_simulator.post_v2_audit import write_candidate_universe_manifest
from nodi_simulator.review_package import PROJECT_ROOT, write_review_manifests


def main() -> None:
    path = write_candidate_universe_manifest(PROJECT_ROOT)
    write_review_manifests(PROJECT_ROOT)
    print(path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
