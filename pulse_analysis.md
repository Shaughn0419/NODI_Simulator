# `pulse_analysis.py`

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Pulse Analysis Module
- 当前职责：完成脉冲检测、阈值判断、峰值提取与单事件特征统计。

## 主要符号
- 顶层函数：`build_pulse_extraction_context`、`estimate_threshold_stats_robust`、`estimate_threshold_robust`、`extract_pulse_features`
- 顶层类：`PulseExtractionContext`

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- 当前文件主要依赖标准库或第三方库；没有显式导入其他仓库内模块。

## 专题补充
- [`guides/core/10_pulse_analysis.md`](guides/core/10_pulse_analysis.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
