from __future__ import annotations

import csv
import json

from nodi_simulator.realism_v2_io import (
    sha256_file,
    write_csv_rows,
    write_json_atomic,
    write_run_manifest,
)


def test_write_csv_rows_preserves_first_seen_column_order(tmp_path):
    path = tmp_path / "rows.csv"

    write_csv_rows(path, [{"b": 1, "a": 2}, {"c": 3, "a": 4}])

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["b", "a", "c"]
        assert list(reader) == [
            {"b": "1", "a": "2", "c": ""},
            {"b": "", "a": "4", "c": "3"},
        ]


def test_write_csv_rows_replaces_atomically(tmp_path, monkeypatch):
    path = tmp_path / "rows.csv"
    replace_calls: list[tuple[str, str, bool]] = []
    original_replace = type(path).replace

    def recording_replace(self, target):
        replace_calls.append((self.name, target.name, self.exists()))
        return original_replace(self, target)

    monkeypatch.setattr(type(path), "replace", recording_replace)

    write_csv_rows(path, [{"b": 1, "a": 2}])

    assert [target for _, target, _ in replace_calls] == ["rows.csv"]
    assert all(existed for _, _, existed in replace_calls)
    assert not list(tmp_path.rglob("*.tmp"))


def test_write_json_atomic_disallows_nan(tmp_path):
    path = tmp_path / "payload.json"

    write_json_atomic(path, {"status": "ok"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "ok"}

    try:
        write_json_atomic(path, {"bad": float("nan")})
    except ValueError:
        pass
    else:  # pragma: no cover - explicit failure branch
        raise AssertionError("write_json_atomic must reject NaN by default")


def test_sha256_file_hashes_file_contents(tmp_path):
    path = tmp_path / "payload.txt"
    path.write_text("abc", encoding="utf-8")

    assert sha256_file(path) == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


def test_write_run_manifest_writes_root_copy_only_when_requested(tmp_path):
    manifest = {"run_id": "example"}
    stage_manifest = tmp_path / "stage" / "run_manifest.json"
    stage_manifest.parent.mkdir()

    write_run_manifest(
        stage_manifest,
        manifest,
        project_root=tmp_path,
        write_root_manifest=False,
    )

    assert json.loads(stage_manifest.read_text(encoding="utf-8")) == manifest
    assert not (tmp_path / "run_manifest.json").exists()

    write_run_manifest(
        stage_manifest,
        manifest,
        project_root=tmp_path,
        write_root_manifest=True,
    )

    assert json.loads((tmp_path / "run_manifest.json").read_text(encoding="utf-8")) == manifest


def test_write_run_manifest_replaces_stage_and_root_atomically(tmp_path, monkeypatch):
    manifest = {"run_id": "atomic"}
    stage_manifest = tmp_path / "stage" / "run_manifest.json"
    stage_manifest.parent.mkdir()
    replace_calls: list[tuple[str, str, bool]] = []
    original_replace = type(stage_manifest).replace

    def recording_replace(self, target):
        replace_calls.append((self.name, target.name, self.exists()))
        return original_replace(self, target)

    monkeypatch.setattr(type(stage_manifest), "replace", recording_replace)

    write_run_manifest(
        stage_manifest,
        manifest,
        project_root=tmp_path,
        write_root_manifest=True,
    )

    assert [target for _, target, _ in replace_calls] == [
        "run_manifest.json",
        "run_manifest.json",
    ]
    assert all(existed for _, _, existed in replace_calls)
    assert not list(tmp_path.rglob("*.tmp"))
