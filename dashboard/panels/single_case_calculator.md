# `dashboard/panels/single_case_calculator.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：Dashboard 页面模块
- 模块摘要：dashboard/panels/single_case_calculator.py — Standalone single-case calculator
- 当前职责：独立单案例计算页，负责现场重算某个具体 case 的完整链路。

## 主要符号
- 顶层函数：`_render_page_style`、`_default_diameter_for_material`、`_seed_single_case_state`、`_build_single_case_report_from_state`、`_build_trace_figure`、`_looks_numeric_text`、`_format_scientific_value`、`_render_metric_grid`、`_render_stage_reading`、`_format_dataframe_for_display`、`_render_stage`、`render_single_case_calculator`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：优先在这里维护页面叙事、显示顺序和文案；涉及数据读取、重算或统计口径时，应尽量下沉到 backend 层。

补充：
- 页面默认值当前直接来自 `dashboard/config.py::DEFAULT_SIM_CFG`
- 因此 single-case 页和 precompute / live backend 的默认输运、噪声与读出口径已对齐
- Stage 3 的 reference 区现在不只显示 `rho` 包络状态，还会把
  `requested / lower / nominal / upper` 这组 `rho` anchor 做一次 probe
- 页面层不会静默改写用户输入的 `rho`；probe 只作为审计报告存在，用来回答
  “这个 case 的绝对 detection 结论到底有多依赖 rho”
- 相关汇总逻辑已经下沉到 `dashboard/signal_backend.py::build_rho_sensitivity_report(...)`
  与 `build_single_case_stage_report(...)`

## 关联代码
- `dashboard/config.py`
- `dashboard/panels/common.py`
- `dashboard/signal_backend.py`
- `data_objects.py`

## 页面定位
**这页回答：** 给定一个具体 case，当前完整计算链为什么会得到这样的 detect / miss 与最终判断。

- 独立工具页，不属于科研展示主线；适合教学、验证和参数试探
- 页面现在只保留输入、结论和关键阶段主链；旧的使用说明、图表阅读提示、附加阶段展开区已移除
- 报告阶段现在只保留主显示阶段：输入 → Mie 本征散射 → 参考场 → 干涉 clean signal → 噪声与读出 → 批量统计 → 工程解释

## 专题补充
- [`archive/dashboard/29_dashboard_single_case_calculator.md`](../../archive/dashboard/29_dashboard_single_case_calculator.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
