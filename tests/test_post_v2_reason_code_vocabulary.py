from __future__ import annotations

import csv
import json
import re

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _vocabulary() -> set[str]:
    payload = json.loads(
        root_path("configs/realism_v2/reason_code_vocabulary.yaml").read_text(encoding="utf-8")
    )
    return {row["code"] for row in payload["reason_codes"]}


def test_reason_code_vocabulary_is_modular_and_closed() -> None:
    payload = json.loads(
        root_path("configs/realism_v2/reason_code_vocabulary.yaml").read_text(encoding="utf-8")
    )
    pattern = re.compile(payload["code_pattern"])

    assert payload["schema"] == "ev_nodi_reason_code_vocabulary_v1"
    assert payload["legacy_underscore_codes_allowed"] is False
    assert all(pattern.fullmatch(row["code"]) for row in payload["reason_codes"])


def test_audit_reason_codes_resolve_to_vocabulary() -> None:
    vocabulary = _vocabulary()
    reason_fields = {
        "top_candidate_mandatory_audit.csv": ["rank_inversion_reason_codes"],
        "tsuyama_bfp_reference_summary.csv": ["tsuyama_extrapolation_reason_code"],
        "top_candidate_pairwise_rank_inversion.csv": ["pairwise_inversion_reason"],
    }

    for filename, fields in reason_fields.items():
        with root_path(f"results/post_v2_mandatory_audit/{filename}").open(
            encoding="utf-8",
            newline="",
        ) as handle:
            for row in csv.DictReader(handle):
                for field in fields:
                    for code in filter(None, row[field].split(";")):
                        assert code in vocabulary
