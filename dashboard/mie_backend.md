# `dashboard/mie_backend.py`

## 文件定位
- 类型：Dashboard 支撑模块
- 模块摘要：dashboard/mie_backend.py — Pure Mie scattering helpers for the dashboard
- 当前职责：为 Mie 相关页面提供纯散射侧的数据准备与可视化友好表格。

## 主要符号
- 顶层函数：`build_theta_grid_deg`、`_compute_mie_case_from_particle`、`compute_mie_case`、`build_mie_summary_dataframe`、`build_mie_angular_dataframe`、`build_mie_single_variable_scan_dataframe`、`build_mie_relative_index_scan_dataframe`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里适合放共享配置、结果加载和计算桥接逻辑；尽量避免把页面展示文案和大段 UI 拼装塞进来。

## 关联代码
- `dashboard/config.py`
- `data_objects.py`
- `intrinsic_scattering.py`

## 专题补充
- 当前没有专门的编号专题说明；本文件的同名说明文档就是第一份对应说明。

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
