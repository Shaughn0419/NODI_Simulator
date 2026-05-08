# `dashboard/panels/noise_detection_explorer.py`

## 文件定位
- 类型：Dashboard 页面模块
- 模块摘要：dashboard/panels/noise_detection_explorer.py — Noise & Detection Explorer page
- 当前职责：Noise & Detection Explorer 页面，负责解释噪声、阈值与检出边界。

## 主要符号
- 顶层函数：`_resolve_defaults`、`_apply_defaults`、`_build_detection_scan_notes`、`_build_detection_verdict_frame`、`_detection_case_cached`、`_detection_scan_cached`、`_build_trace_figure`、`_build_detection_outcome_figure`、`_build_scan_figure`、`render_noise_detection_explorer`
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
**这页回答：** 理论上存在的 clean pulse，为什么最后会变成 detect / miss。

- 默认围绕标准结果库解释当前选中 case；live 参数仅作为调试辅助
- 页面现在只保留主链：当前点摘要、单事件 trace、批量结果、参数扫描
- 阈值公式长说明和稳定性分型卡已移除，避免把页面重新拉回教学稿
- 默认粒子、波长、通道和光学/仿真配置来自 `dashboard.panels.common.resolve_shared_case_parameter_defaults()`，与 Interference 页共享同一 selected-case fallback
- 主要解释 threshold、local SNR、带宽限制和 detect/miss 分流
- 关键指标：`threshold`、`local SNR`、`bandwidth limited fraction`、`detection_rate`、`stable_detection_rate`

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
