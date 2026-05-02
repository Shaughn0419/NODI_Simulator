# `dashboard/panels/common.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：Dashboard 页面模块
- 模块摘要：dashboard/panels/common.py — Shared dashboard guidance helpers
- 当前职责：Dashboard 共享展示辅助层，集中管理页面注册、共享提示语、header 与视觉语言。

## 主要符号
- 顶层函数：`inject_dashboard_theme`、`render_display_banner`、`render_section_intro`、`initialize_dashboard_session_state`、`get_selected_case_context`、`set_selected_case_context`、`get_active_data_source_tag`、`build_case_context`、`resolve_active_system_defaults`、`resolve_shared_case_parameter_defaults`、`render_page_header_hub`、`render_auxiliary_page_header`、`render_current_context_bar`、`format_case_verdict_caption`、`render_workflow_case_source_panel` 等
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：优先在这里维护页面叙事、显示顺序和文案；涉及数据读取、重算或统计口径时，应尽量下沉到 backend 层。

## 关联代码
- `dashboard/config.py`

## 设计原则
1. 共享 header / verdict / context 语义必须优先收在这里。
2. 页面层尽量消费 common 提供的展示语义，而不是各自复制一份。
3. 如果主阅读路径调整，优先改这里，不要每页单独改文案。
4. Interference 与 Noise/Detection 这类共享 selected-case 默认值的页面，应通过 `resolve_shared_case_parameter_defaults()` 取默认粒子、波长、几何和光学/仿真配置，避免每页复制一套 fallback 逻辑。

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
