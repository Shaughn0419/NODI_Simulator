# `__init__.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：包入口模块
- 模块摘要：NODI Interferometric Simulator
- 当前职责：包级入口，负责暴露顶层版本或导出符号。

## 主要符号
- 顶层函数：当前没有顶层函数，或主要通过类/常量组织逻辑。
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由包导入自动触发，不单独运行。
- 直接维护建议：保持导出关系清晰即可，避免在 `__init__` 中堆积复杂副作用。

## 关联代码
- 全部核心模块的统一再导出入口，详见 `guides/core/12_init.md`
- 当前包根还再导出文件43 v5 的 governance / scaffold / diagnostic helper，例如 design claim governance、EV reporting、assay control、BFP detector operator、count/population/OOD、unit/wavelength/readout 与 calibration advisor；这些导出用于统一 provenance 与 blocker，不代表对应 lane 已解锁 calibrated quantitative 求解。

## 专题补充
- [`guides/core/12_init.md`](guides/core/12_init.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
