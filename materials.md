# `materials.py`

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Materials Database
- 当前职责：提供材料光学常数查询、Au/Ag visible tabulated 数据，water/PBS/HEPES/culture/sucrose/iodixanol 等介质 nominal dispersion，fused-silica/BK7 壁材或历史兼容材料，以及材料库覆盖度诊断。

## 主要符号
- 顶层函数：`get_n_complex`、`list_materials`、`material_property_summary`、`material_db_coverage_diagnostics`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- 当前文件主要依赖标准库或第三方库；没有显式导入其他仓库内模块。

## 专题补充
- [`guides/core/02_materials.md`](guides/core/02_materials.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
