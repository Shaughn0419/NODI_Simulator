# `interface_correction.py`

## 文件定位
- 类型：核心物理诊断模块
- 模块摘要：显式记录 homogeneous-medium Mie / core-shell 近似与界面修正状态。
- 当前职责：输出 interface correction mode、修正对象、未修正项、phase/polarity/angular-pattern 输出敏感性、`eta_interface` / `eta_lambda` 与 full-wave escalation provenance。

## 主要符号
- 顶层函数：`build_interface_correction_diagnostics`

## 调用与使用
- 由 `parameter_sweep.run_single_case_batch()` 在 case-level reference/intrinsic provenance 阶段调用。
- 默认 `interface_correction_mode="off"`，不改变数值主链，只声明当前是 homogeneous-medium approximation。
- 开启 `dipole_image_surrogate / planar_interface_tmatrix / fullwave` 时，第一版只输出 route/claim/provenance，不伪装成已完成 FDTD/RCWA。
- 即使 `interface_correction_mode="off"`，若当前输出依赖 phase、polarity 或 angular radiation pattern，`interface_fullwave_required` 会记录 `phase_polarity_or_angular_pattern_output`，并通过 `interface_quantitative_claim_blocker_summary` 防止 homogeneous-medium Mie 被误读成界面定量主线。

## 设计原则
1. interface correction 是所有粒子的通用诊断，不是 exosome-only 特性。
2. 未修正的 incident field、particle polarizability、radiation-pattern / collection 项必须显式可见。
3. 当 `eta_interface` 或 `eta_lambda` 触发 caution 时，结果应提示 planar-interface / full-wave 升级，而不是自动提升 quantitative claim。
4. 当 phase / polarity / angular-pattern 是主输出时，`dipole_image_surrogate` 只能标为 first-order surrogate，不能解锁 quantitative phase/polarity claim。
