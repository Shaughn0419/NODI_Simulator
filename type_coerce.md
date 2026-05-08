# `type_coerce.py`

## 文件定位
- 类型：共享工具模块
- 模块摘要：集中管理诊断、报告和工具脚本中常见的数值类型转换。
- 当前职责：替代多个模块中重复的 `_as_float` / `_safe_float` helper，避免缺失值、NaN、inf 和默认值语义在不同调用点悄悄分叉。

## 主要符号
- `as_float(value, default=0.0)`
- `float_or_nan(value, default=math.nan)`
- `finite_float(value, default=0.0)`
- `finite_float_or_nan(value, default=math.nan)`
- `optional_finite_float(value, default=None)`

## 调用与使用
- 需要“无法解析就用数值默认值”的地方使用 `as_float` 或 `finite_float`。
- 需要保持缺失/不可解析为 `NaN` 的报告或 paper-audit 工具使用 `float_or_nan` 或 `finite_float_or_nan`。
- 需要保留 `None` 语义、让下游明确知道数据不可用时使用 `optional_finite_float`。

## 关联代码
- `count_likelihood.py`
- `population_inference.py`
- `ev_population_prior.py`
- `selection_function.py`
- `tools/tsuyama_*`

## 备注
- 这个模块只做类型转换，不做单位换算、物理解释或 claim-level 判断。
- 新增数值转换 helper 时优先扩展此模块，不要在业务模块里重新复制 `_as_float`。
