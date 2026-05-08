# `mie_engine.py`

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Mie Engine
- 当前职责：实现 Mie 散射核心数值求解，包括系数、总截面与角分布计算。

## 主要符号
- 顶层函数：`_compute_nmax`、`_log_derivative_downward`、`_riccati_bessel`、`_riccati_bessel_full`、`_solve_core_shell_mode`、`mie_coefficients`、`mie_core_shell_coefficients`、`mie_efficiencies_from_coefficients`、`mie_compute`、`_pi_tau`、`mie_angular_from_coefficients`、`mie_angular`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- 当前文件主要依赖标准库或第三方库；没有显式导入其他仓库内模块。

## 专题补充
- [`guides/core/02_mie_engine.md`](guides/core/02_mie_engine.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
