# `optional_acceleration.py`

## 文件定位
- 类型：共享运行时提示模块
- 模块摘要：管理可选 JIT 加速依赖缺失时的用户提示。
- 当前职责：当 `numba` 不可用时，为 trajectory、illumination、parameter sweep 和 precompute runtime estimate 等加速路径发出一致的 runtime warning。

## 主要符号
- `warn_numba_unavailable(feature)`

## 调用与使用
- `numba` 仍然是 optional dependency，安装方式为 `python -m pip install -e ".[acceleration]"`。
- 缺少 `numba` 时，模拟仍可运行，只是退回无 JIT 加速路径；该模块负责让降速显性化。
- 不要把 `numba` 移入主依赖，除非项目明确决定放弃纯 Python / NumPy fallback。

## 关联代码
- `illumination.py`
- `trajectory.py`
- `parameter_sweep.py`
- `dashboard/estimate_precompute_runtime.py`
- `tests/test_optional_acceleration_dependency.py`

## 备注
- 本模块只负责提示，不参与数值计算，不改变随机数、物理模型或结果语义。
