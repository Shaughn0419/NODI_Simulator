# `dashboard/panels/explorer.py`

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
