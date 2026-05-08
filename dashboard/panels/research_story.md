# `dashboard/panels/research_story.py`

## 文件定位
- 类型：Dashboard 页面模块
- 模块摘要：dashboard/panels/research_story.py
- 当前职责：科研展示主线页面，负责把全量结论与工程平台区分析组织成三页统一叙事。

## 主要符号
- 顶层函数：`_frame`、`_safe_bool_mean`、`_safe_sum_matches`、`_load_named_dataset`、`_aggregate_wavelength_table`、`_format_order`、`_metric_card`、`_bar_figure`、`_load_primary_story_inputs`、`_resolve_story_dataset_prefix`、`_filter_default_ready_within_envelope`、`_aggregate_band_wavelength_table`、`_band_heatmap_figure`、`_segment_window_table`、`_pick_top_window` 等
- 顶层 render 函数：`render_research_overview`（Decision Summary）、`render_geometry_platform`（Engineering Windows）
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：优先在这里维护页面叙事、显示顺序和文案；涉及数据读取、重算或统计口径时，应尽量下沉到 backend 层。

## 关联代码
- `dashboard/backend.py`
- `dashboard/panels/common.py`

## 专题补充
- [`archive/reports/32_exosome_50_150_focus_404_analysis.md`](../../archive/reports/32_exosome_50_150_focus_404_analysis.md)
- [`archive/reports/33_full_range_4w_analysis.md`](../../archive/reports/33_full_range_4w_analysis.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
