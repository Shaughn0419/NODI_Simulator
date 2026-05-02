# `interface_correction.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

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
