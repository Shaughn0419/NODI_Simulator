from __future__ import annotations

import csv
import gzip
import hashlib
import json

from nodi_simulator.realism_v2_io import (
    open_text_artifact,
    read_csv_headers,
    read_csv_rows,
    resolve_artifact_path,
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


def test_write_csv_rows_uses_lf_line_endings(tmp_path):
    path = tmp_path / "rows.csv"

    write_csv_rows(path, [{"a": "1"}, {"a": "2"}])

    data = path.read_bytes()
    assert b"\r\n" not in data
    assert data == b"a\n1\n2\n"


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


def test_csv_artifact_helpers_resolve_gzip_fallback(tmp_path):
    logical_path = tmp_path / "rows.csv"
    gzip_path = tmp_path / "rows.csv.gz"
    content = "a,b\n1,2\n"
    with gzip.open(gzip_path, mode="wt", encoding="utf-8", newline="") as handle:
        handle.write(content)

    assert resolve_artifact_path(logical_path) == gzip_path
    with open_text_artifact(logical_path, newline="") as handle:
        assert handle.read() == content
    assert read_csv_headers(logical_path) == ["a", "b"]
    assert read_csv_rows(logical_path) == [{"a": "1", "b": "2"}]
    assert sha256_file(logical_path) == hashlib.sha256(content.encode("utf-8")).hexdigest()


def test_read_csv_rows_accepts_large_accumulated_source_fields(tmp_path):
    path = tmp_path / "large.csv"
    large_field = ";".join(f"event_{index:06d}" for index in range(20000))

    write_csv_rows(path, [{"source_event_rows": large_field, "count": 20000}])

    assert read_csv_rows(path) == [
        {"source_event_rows": large_field, "count": "20000"}
    ]


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
