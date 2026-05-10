from __future__ import annotations

import subprocess
import sys

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_verify_review_package_cli_supports_package_root_and_local_mode() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_review_package.py")),
            "--package-root",
            str(root_path(".")),
            "--mode",
            "local-dev",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS required_paths" in result.stdout
    assert "PASS post_v2_audit_schema" in result.stdout
