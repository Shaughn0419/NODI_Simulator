# `dashboard/panels/mie_explorer.py`

## 文件定位
- 类型：Dashboard 页面模块
- 模块摘要：dashboard/panels/mie_explorer.py — Pure Mie scattering explorer
- 当前职责：Mie Explorer 页面，负责给出主流程真正需要的本征散射证据。

## 主要符号
- 顶层函数：`_summary_df_cached`、`_metric_label`、`_build_line_figure`、`_build_single_variable_scan_figure`、`_build_overview_trend_note`、`_build_overview_reading_frame`、`_closest_wavelength_option`、`_resolve_linked_mie_defaults`、`render_mie_explorer`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：优先在这里维护页面叙事、显示顺序和文案；涉及数据读取、重算或统计口径时，应尽量下沉到 backend 层。

## 关联代码
- `dashboard/backend.py`
- `dashboard/config.py`
- `dashboard/mie_backend.py`
- `dashboard/panels/common.py`

## 页面定位
**这页回答：** 粒子本征散射本身有多强，以及这种强弱如何随粒径 / 波长变化。

- 是证据页，不是最终选型页；用来解释 `Csca / dCsca/dOmega / E_sca` 的趋势
- 当前会继承主流程里的选中 case 作为默认值
- 页面现在只保留三段主链：总览趋势、固定角度单变量扫描、单点明细
- 角分布 / 折射率 / 偏振高级分析已移除
- 关键指标：总览 `Csca / Cext / Cabs / Qsca`、固定角度下单变量扫描、单点 `dCsca/dOmega / Esca`

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
