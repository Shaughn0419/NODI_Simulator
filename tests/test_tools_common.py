from __future__ import annotations

import json

import numpy as np

from tools._common import json_safe, write_json_file


def test_json_safe_normalizes_numpy_and_nonfinite_values(tmp_path) -> None:
    payload = {
        np.int64(7): {
            "finite": np.float64(1.25),
            "nan": np.float64("nan"),
            "inf": float("inf"),
            "flag": np.bool_(True),
            "items": (np.int32(3), np.float32(2.5)),
        }
    }

    safe = json_safe(payload)

    assert safe == {
        "7": {
            "finite": 1.25,
            "nan": None,
            "inf": None,
            "flag": True,
            "items": [3, 2.5],
        }
    }

    output_path = tmp_path / "payload.json"
    write_json_file(output_path, payload)

    assert json.loads(output_path.read_text(encoding="utf-8")) == safe
