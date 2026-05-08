# `dashboard/estimate_precompute_runtime.py`

## 文件定位
- 类型：Dashboard 支撑模块
- 模块摘要：dashboard/estimate_precompute_runtime.py
- 当前职责：对预计算任务做抽样耗时估计，帮助预估 sweep 成本。

## 主要符号
- 顶层函数：`_pick_evenly_spaced`、`_seconds_to_readable`、`_build_benchmark_subset`、`estimate_runtime`、`main`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常作为脚本从仓库根目录运行；建议先阅读文件内参数或 `main()` 入口。
- 直接维护建议：这里适合放共享配置、结果加载和计算桥接逻辑；尽量避免把页面展示文案和大段 UI 拼装塞进来。

## 关联代码
- `dashboard/config.py`
- `dashboard/precompute.py`

## 专题补充
- [`guides/dashboard/25_dashboard_estimate_precompute_runtime.md`](../guides/dashboard/25_dashboard_estimate_precompute_runtime.md)

## 备注
- `numba` 缺失时会通过共享 acceleration warning helper 提示当前 estimate 运行在无 JIT 加速路径；依赖仍通过 `.[acceleration]` 可选安装。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
