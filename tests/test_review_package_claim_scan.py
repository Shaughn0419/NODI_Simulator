from __future__ import annotations

import pytest

from nodi_simulator.review_package import claim_scan_paths, scan_claim_files

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_hard_claim_scan_scope_includes_post_v2_and_package_docs() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert "README.md" in paths
    assert "reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md" in paths
    assert "REVIEW_PACKAGE_README.md" in paths
    assert "papers/README.md" in paths


def test_hard_claim_scan_has_no_unblocked_forbidden_claims() -> None:
    assert scan_claim_files(root_path(".")) == []
