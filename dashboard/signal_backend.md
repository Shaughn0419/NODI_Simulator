# `dashboard/signal_backend.py`

## 文件定位
- 类型：Dashboard 支撑模块
- 模块摘要：dashboard/signal_backend.py — Signal-chain helpers for explanatory dashboard pages
- 当前职责：为干涉、噪声和单案例页面提供信号链计算、扫描结果与解释性统计。

## 主要符号
- 顶层函数：`_resolve_projection_basis`、`_wrapped_phase_delta_rad`、`_rank_correlation`、`_classify_reference_consistency`、`_classify_interference_overlap`、`_classify_path_opd_and_gouy_freeze`、`_summarize_reference_consistency_subset`、`_projection_mode_semantics`、`_dominant_clean_peak_summary`、`_resolve_esca_reference`、`build_case_inputs`、`compute_interference_case`、`build_interference_scan_dataframe`、`build_projection_mode_validation_dataframe`、`build_reference_model_consistency_report`、`build_path_opd_freeze_report`、`compute_noise_detection_case`、`build_event_trace_dataframe`、`build_rho_sensitivity_report`、`build_single_case_stage_report`、`build_detection_scan_dataframe` 等
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里适合放共享配置、结果加载和计算桥接逻辑；尽量避免把页面展示文案和大段 UI 拼装塞进来。

## 关联代码
- `dashboard/config.py`

## 专题补充
- 当前没有专门的编号专题说明；本文件的同名说明文档就是第一份对应说明。

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
