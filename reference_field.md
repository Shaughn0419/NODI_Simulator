# `reference_field.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Reference Field Module
- 当前职责：生成参考场 surrogate 模型，描述通道几何与波长如何放大干涉检测中的 reference。

## 主要符号
- 顶层函数：`compute_reference_field`、`compute_reference_field_trace`、`compute_reference_field_from_tsuyama_bfp`、`_resolve_phase_grating_amplitude_scale`、`_build_reference_field_envelope_diagnostics`、`_resolve_reference_width_saturation`、`_reference_model_metadata`、`_classify_geometry_depth_scaling`、`_coerce_rows`、`_load_reference_calibration`、`_interpolate_scalar`、`_interpolate_phase`、`_lookup_calibrated_reference`、`_channel_diffraction_field_surrogate`、`_angular_surrogate_reference` 等
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- `data_objects.py`（`Channel`、`OpticalSystem`、`SimulationConfig`）
- `utils.py`（`build_collection_operator`、`collapse_angular_field_with_operator` 等）
- `tsuyama_phase_filter.py`（BFP reference comparison lane）

## 当前 Tsuyama/BFP ROI 口径

- `compute_reference_field_from_tsuyama_bfp(...)` 仍是 detector-resolved comparison lane，不是 calibrated detector-unit model。
- 未配置 measured mask 时，默认仍使用 `tsuyama_bfp_roi_mode`：`symmetric_na_aperture` 或 `slit_off_axis_lobe_surrogate`。
- 配置 `SimulationConfig.bfp_roi_mask_path` 且 `build_bfp_roi_mask_contract(...)` 判定为 measured/calibrated 后，mask rows 会按 `theta_rad / phi_rad / mask_weight / solid_angle_weight` 投影到 Tsuyama 1D BFP q 轴，并用 weighted ROI 积分计算 `E_ref_complex_roi`、`I_ref_intensity_roi`、`E_no_channel_complex_roi` 与 `I_no_channel_intensity_roi`。
- 该路径会导出 `tsuyama_bfp_roi_mode="calibrated_bfp_roi_mask_projected_1d"`、`bfp_roi_mask_projection_status`、`bfp_roi_mask_projected_row_count`、`bfp_roi_mask_projected_sample_count`，并把 `reference_detector_bridge_status` 标为 `calibrated_roi_mask_projected_1d_no_detector_unit_chain`。
- Synthetic/template mask 仍只导出 contract/status，不参与 ROI 积分，不解锁 absolute/global green claim。

## 专题补充
- [`guides/core/05_reference_field.md`](guides/core/05_reference_field.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
