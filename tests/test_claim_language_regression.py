from __future__ import annotations

import pytest

from nodi_simulator.review_package import claim_text_passes, load_forbidden_claims_lexicon

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


@pytest.mark.parametrize(
    "text",
    [
        "calibrated SNR blocked",
        "absolute LOD blocked",
        "not calibrated",
        "relative robustness only",
        "no-measured-data audit-only",
        "absolute claim blocked",
        "biological specificity blocked",
        "校准SNR被阻断",
        "不能声称绝对LOD",
        "真实EV浓度尚未可预测",
    ],
)
def test_forbidden_claim_lexicon_allows_blocker_language(text: str) -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    assert claim_text_passes(text, lexicon)


@pytest.mark.parametrize(
    "text",
    [
        "calibrated SNR is achieved",
        "absolute LOD is established",
        "true EV concentration can be predicted",
        "biological specificity is confirmed",
        "校准SNR已实现",
        "真实EV浓度已可预测",
    ],
)
def test_forbidden_claim_lexicon_blocks_positive_claims(text: str) -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    assert not claim_text_passes(text, lexicon)


def test_review_package_readme_preserves_relative_audit_boundary() -> None:
    text = root_path("REVIEW_PACKAGE_README.md").read_text(encoding="utf-8")

    assert "no-measured-data relative audit" in text
    assert "not calibrated physical predictions" in text
