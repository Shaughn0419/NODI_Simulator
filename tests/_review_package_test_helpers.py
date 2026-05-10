from __future__ import annotations

import json
from pathlib import Path

from nodi_simulator.review_package import PROJECT_ROOT, write_review_manifests


def ensure_review_package_artifacts() -> None:
    required = (
        PROJECT_ROOT / "REVIEW_BUILD_MANIFEST.json",
        PROJECT_ROOT / "REVIEW_PACKAGE_MANIFEST.json",
        PROJECT_ROOT / "REVIEW_PACKAGE_HASHES.sha256",
        PROJECT_ROOT / "papers/provenance/paper_manifest.csv",
        PROJECT_ROOT / "configs/realism_v2/forbidden_claims_lexicon.yaml",
        PROJECT_ROOT
        / "results/post_v2_mandatory_audit/top_candidate_mandatory_audit_manifest.json",
    )
    if not all(path.exists() for path in required):
        write_review_manifests(PROJECT_ROOT)


def load_json(relpath: str) -> dict:
    ensure_review_package_artifacts()
    return json.loads((PROJECT_ROOT / relpath).read_text(encoding="utf-8"))


def root_path(relpath: str) -> Path:
    ensure_review_package_artifacts()
    return PROJECT_ROOT / relpath
