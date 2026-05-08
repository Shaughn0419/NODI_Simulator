# `dashboard/panels/common.py`

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
