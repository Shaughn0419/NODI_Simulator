# `dashboard/panels/explorer.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：Dashboard 页面模块
- 模块摘要：dashboard/panels/explorer.py — Design Explorer 页面
- 当前职责：Design Explorer 页面，负责在结果空间中寻找平台、代表点与候选设计。

## 主要符号
- 顶层函数：`_metric_label`、`_format_metric_value`、`_style_candidate_table`、`_resolve_default_design_material`、`_sort_cases_by_metric`、`render_explorer`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：优先在这里维护页面叙事、显示顺序和文案；涉及数据读取、重算或统计口径时，应尽量下沉到 backend 层。

## 关联代码
- `dashboard/backend.py`
- `dashboard/config.py`
- `dashboard/panels/common.py`
- `utils.py`

## 页面定位
**这页回答：** 在标准结果库里，哪些 λ / W / H 组合更像稳定平台，而不是偶然尖峰。

- 优先围绕标准 biomimetic full-range 主结果库工作；live sweep 只保留为工程调试入口
- 阅读顺序：热图 → 候选 → 切片 → Inspector
- 关注热图里的**连续高分区**（而非单点最高值）、Top 候选是否集中同一区域、切片区域是平台还是尖峰

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
