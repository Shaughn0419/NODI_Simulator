# `realism_v2_io.py`

## 文件定位
- 类型：realism v2 I/O 辅助模块
- 模块摘要：集中管理 v2 结果 CSV、checksum 和 run manifest 写入。
- 当前职责：从 `realism_v2.py` 中抽出通用文件写入逻辑，减少巨型模块中的重复 I/O helper，并收紧 root manifest 覆盖行为。

## 主要符号
- `sha256_file(path)`
- `write_csv_rows(path, rows)`
- `write_run_manifest(manifest_path, manifest, project_root, write_root_manifest)`

## 调用与使用
- `realism_v2.py` 仍是 v2 计算与审计主入口；本模块只承接低层 I/O。
- `write_run_manifest` 总是写 stage-local manifest；只有显式传 `write_root_manifest=True` 时才更新仓库根目录的 `run_manifest.json`。
- CLI 工具需要更新 root manifest 时必须显式使用 `--write-root-manifest`。

## 关联代码
- `realism_v2.py`
- `tools/ev_nodi_realism_v2_*.py`
- `tests/test_realism_v2_io.py`
- `tests/test_realism_v2_micro_anchor.py`

## 备注
- root `run_manifest.json` 是受控 provenance 文件，不应被默认运行静默覆盖。
- 本模块不改变任何 v2 科学结论，只改变文件写入边界和复用位置。
