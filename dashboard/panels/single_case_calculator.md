# `dashboard/panels/single_case_calculator.py`

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
- `nodi_simulator/data_objects.py`

## 页面定位
**这页回答：** 给定一个具体 case，当前完整计算链为什么会得到这样的 detect / miss 与最终判断。

- 独立工具页，不属于科研展示主线；适合教学、验证和参数试探
- 页面现在只保留输入、结论和关键阶段主链；旧的使用说明、图表阅读提示、附加阶段展开区已移除
- 报告阶段现在只保留主显示阶段：输入 → Mie 本征散射 → 参考场 → 干涉 clean signal → 噪声与读出 → 批量统计 → 工程解释

## 专题补充
- [`archive/dashboard/29_dashboard_single_case_calculator.md`](../../archive/dashboard/29_dashboard_single_case_calculator.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
