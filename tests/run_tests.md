# `tests/run_tests.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位

- 类型：测试入口兼容脚本
- 当前职责：保留 `python tests/run_tests.py --workers 8` 旧命令，同时转调 pytest 主测试套件。

## 使用方式

```bash
python tests/run_tests.py --workers 8
```

等价于先对整个 `tests/` 运行非 AppTest pytest lane，再对整个 `tests/` 运行 AppTest lane。不要把该 wrapper 收窄到少数测试文件，否则会漏掉 Tsuyama / selected-annulus / event-block 等专项回归。

当前完整 pytest 基线是 `563 passed`，无 warnings。旧 wrapper 仍可用于兼容，但最终收口验证优先看 `pytest -q`、`ruff check .`、`pyright` 和源码 `compileall`。在 USB/macOS 目录中运行 `compileall` 时要排除 AppleDouble `._*` 元数据文件。

## 主要符号
- 顶层函数：`main` 以及 `_build_env` / `_run` / `_parse_args` 内部 helper。

## 关联说明

- [`guides/operations/14_测试说明.md`](../guides/operations/14_测试说明.md)
- [`tests/test_physics_core.py`](test_physics_core.py)
- [`tests/test_dashboard_workflow.py`](test_dashboard_workflow.py)
