# `dashboard/panels/interference_explorer.py`

## 文件定位
- 类型：Dashboard 页面模块
- 模块摘要：dashboard/panels/interference_explorer.py — Interference Explorer page
- 当前职责：Interference Explorer 页面，负责说明 reference 如何把散射转成 clean signal。

## 主要符号
- 顶层函数：`_resolve_defaults`、`_apply_defaults`、`_build_trace_figure`、`_build_peak_figure`、`_build_scan_figure`、`_build_interference_scan_notes`、`_build_interference_verdict_frame`、`render_interference_explorer`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：优先在这里维护页面叙事、显示顺序和文案；涉及数据读取、重算或统计口径时，应尽量下沉到 backend 层。

## 关联代码
- `dashboard/backend.py`
- `dashboard/config.py`
- `dashboard/panels/common.py`
- `dashboard/signal_backend.py`

## 页面定位
**这页回答：** reference field 如何把本征散射变成 clean signal。

- 默认围绕标准结果库解释当前选中 case；live 参数只作为调试提示
- 页面现在只保留主链：当前点摘要、clean trace 分解、峰值构成、单变量扫描
- 高级 projection / reference consistency / freeze 审计入口已移除
- 默认粒子、波长、通道和光学/仿真配置来自 `dashboard.panels.common.resolve_shared_case_parameter_defaults()`，不再在本页复制 selected-case fallback 逻辑
- 关键指标：`A_ref`、`peak cross-term`、`peak |E_sca|^2`、`heterodyne gain`、overlap 是否仍在可解释区

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
