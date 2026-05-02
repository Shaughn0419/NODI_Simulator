# dashboard/precompute.py — 预计算脚本

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。

> 2026-04-14 补充：当前 operational 口径已统一收口到 [24_高性能预计算与增量重算方案.md](../../24_高性能预计算与增量重算方案.md)。如果你只是想知道“现在该怎么跑”，优先看 `24`；本文负责解释 `dashboard/precompute.py` 这条实现链本身。



## 当前使用方式

- 文档定位：预计算实现说明
- 推荐阅读时机：当你要重算结果库、检查输出产物或理解 precompute 主入口时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/precompute.md](../../dashboard/precompute.md)
- [24_高性能预计算与增量重算方案.md](../../24_高性能预计算与增量重算方案.md)
- [25_dashboard_estimate_precompute_runtime.md](../../guides/dashboard/25_dashboard_estimate_precompute_runtime.md)

## 文件职责

离线执行参数扫描（sweep），将结果保存为主结果文件与相关审计文件供面板读取。这是"重计算"部分，运行时间 1–60 分钟，不在面板中交互执行。

从 `2026-04-06` 这轮 `fine + full_range` 全量计算的实际执行经验出发，本文新增一条明确原则：

- **凡是长耗时预计算，都必须能实时看到进度**

当前 `precompute.py` 仍是“整轮 sweep 结束后再一次性写出 `summary / compact / meta / result_health / freeze_probe`”，因此在执行中：

- 不能直接看到 `n_cases_completed`
- 不能稳定给出真实 ETA
- 不能只靠结果文件判断任务是否卡住

这意味着当前实现虽然能完成计算，但**可观测性还不达标**。后续继续沿用这条主链时，应把“实时进度上报”视为实现要求，而不是额外优化。

---

## 用法

```bash
python -m nodi_simulator.dashboard.precompute --grid coarse --tag default --output results/

# 生成完整粒径范围数据集（gold/exosome × 40–300nm，10nm步进）
python -m nodi_simulator.dashboard.precompute --grid coarse --particle-profile full_range --tag full_range --workers 12 --output results/

# full-range 重算前，先生成 freeze sanity report
PYTHONPATH=/Users/yanxuan/Documents/实验 python -m nodi_simulator.dashboard.precompute \
  --grid coarse \
  --particle-profile quick \
  --tag current_model_probe \
  --workers 8 \
  --freeze-probe-report \
  --output results/
```

当前标准 biomimetic exosome 全量重算的现行命令是：

```bash
PYTHONPATH=. python -m dashboard.precompute \
  --grid fine \
  --tag full_range_biomimetic_exosome_10000e \
  --particle-profile full_range_biomimetic_exosome \
  --workers 28 \
  --freeze-probe-report \
  --progress-interval 2 \
  --resume \
  --checkpoint \
  --checkpoint-batch-size 25 \
  --checkpoint-flush-interval 5 \
  --output results
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--grid` | `coarse` | 网格分辨率：`coarse`（4×4×4）或 `fine`（16×16×4） |
| `--tag` | profile 默认值 | 配置标签，用于文件命名 |
| `--particle-profile` | `quick` | 粒子预计算档位：`quick`、`full_range`（均匀 exosome 基线）或 `full_range_biomimetic_exosome`（当前标准 biomimetic 全量口径） |
| `--workers` | `1` | worker 进程数；`0` 表示使用全部逻辑 CPU |
| `--freeze-probe-report` | 关闭 | 额外导出 `*_freeze_probe.json`，把 case 级 freeze judgement 聚合成 coarse-probe 级 sanity report |
| `--progress-interval` | `2.0` | 进度刷新周期（秒）；控制 stdout 和 `*_progress.json` 的更新频率 |
| `--resume` / `--no-resume` | `--resume` | 是否从已有 checkpoint 恢复；恢复时只补跑缺失 case |
| `--checkpoint` / `--no-checkpoint` | `--checkpoint` | 是否持续写 raw case checkpoint |
| `--checkpoint-batch-size` | `25` | 每累计多少个新成功 case 刷一次 checkpoint chunk |
| `--checkpoint-flush-interval` | `5.0` | 即使 batch 未满，最长多少秒也要刷一次 checkpoint |
| `--output` | `results/` | 输出目录 |

当前 worker 口径请单独记住：

- 正式全量重算：`28 workers`
- 其他预计算试跑、freeze probe、runtime estimate、测试：`8 workers`

---

## 进度要求

从现在起，`dashboard/precompute.py` 及同类长耗时脚本应满足以下进度要求：

- 启动时就确定并显示 `total_cases`
- 运行中持续更新 `completed_cases`
- 终端、日志或单独的 `*_progress.json` 中可读到 `progress_fraction`
- 能显示 `elapsed_seconds` 和 `estimated_remaining_seconds`
- 能显示当前 `active_workers`
- 若任务按阶段执行，还应显示 `current_stage`

推荐做法：

1. 主进程启动时先写 job manifest
2. worker 每完成一个 case 就更新共享计数器
3. 主进程定时刷新进度文件并输出到 stdout
4. 任务完成后再写最终 `summary / compact / meta`

如果后续某次预计算仍然只能在结束后一次性落盘，而没有中间进度，就应视为“实现未满足运行要求”，不应再把它当成理想的长期执行方式。

当前实现已经补上最小可用的实时进度机制：

- 运行时会周期性打印 `completed / total / percent / ETA`
- 输出目录会同步写出 `*_progress.json`
- `current_stage` 会区分 `initializing / sweep / saving_* / completed`
- `status` 会区分 `running / completed / failed`

当前实现也补上了最小可用的断点续跑机制：

- 输出目录会生成一个 `*_checkpoint/` 目录
- `chunks/` 下持续写 raw case chunk
- `manifest.json` 记录 checkpoint 状态
- 下次以同一 `grid + tag + particle_profile` 启动且 `--resume` 开启时，会优先加载这些 raw case，只补跑未完成部分
- 如果 case 已全部算完但 `summary / compact / meta` 写盘阶段失败，下次也可以直接从 checkpoint 继续，不必重算 case 本体

---

## 输出文件

命名规则：`{grid}_{tag}_{type}.{ext}`

| 文件 | 格式 | 内容 |
|------|------|------|
| `*_summary.csv` | CSV | 每行一个 case，包含评分、检测指标、物理量 |
| `*_compact.pkl` | pickle | list[dict]，含 summary + physics + scores，不含 event trace |
| `*_meta.json` | JSON | 元数据：`schema 1.4`、完整 `sim_cfg`、分波长 optical provenance、网格、时间戳 |
| `*_progress.json` | JSON | 运行时进度快照，包含 `completed_cases / total_cases / progress_fraction / elapsed / ETA / active_workers / current_stage / saved_outputs` |
| `*_checkpoint/manifest.json` | JSON | checkpoint 目录状态，包含当前阶段、chunk 数、已落盘 case 数 |
| `*_checkpoint/chunks/chunk_*.pkl` | pickle | 中途落盘的 raw case 分块，可用于断点续跑 |
| `*_freeze_probe.json` | JSON | 仅在 `--freeze-probe-report` 开启时导出；聚合 `rho / overlap / projection / gouy / observation_freeze` 的分布、width-group 趋势和 top cases |
| `*_engineering_gate_calibration.json` | JSON | 当前保留为可选后处理报告；`build_engineering_gate_calibration_report(summary_df)` 能生成它，但 precompute CLI 不会自动把它当必然产物写出 |
| `*_result_health.json` | JSON | 默认结果库的持续监控报告；聚合 `observation / gouy / overlap / projection / rho / width_saturation` 分布、推荐标签分布、gate 通过情况、按 `width / wavelength / particle_material` 的健康切片，以及 top caution cases |

---

## 函数

### `precompute_sweep(grid_name, config_tag, particle_profile, output_dir, n_workers, save_freeze_probe_report=False)`

主函数。从 config.py 读取配置，调用 `run_parameter_sweep`，保存 summary / compact / meta 三个主输出；当 `save_freeze_probe_report=True` 时，还会额外保存 coarse-probe 级 freeze sanity report。当前版本还会无条件基于 `summary_df` 再生成一份 dataset-level 的 `*_result_health.json`，供默认结果库冻结后持续监控。

流程：
1. 从 `GRID_CONFIGS` 获取网格定义
2. 构建 dashboard 预计算专用 `SimulationConfig`，覆盖 `n_events`，并强制 `score_mode="single"`
3. 调用 `run_parameter_sweep(..., n_workers=n_workers)` 执行完整扫描
4. 用三个转换函数分别生成 CSV、pkl、JSON
5. 调用 `build_result_health_report(df)` 生成 `*_result_health.json`
6. 如果启用 `save_freeze_probe_report`，再调用 `build_freeze_probe_report(results)` 生成 `*_freeze_probe.json`

### `build_engineering_gate_calibration_report(summary_df, top_k=10) → dict`

把已经冻结好的 `summary.csv` 再归约成一份 gate 校准报告，回答的核心问题是：

- 当前默认 gate 下到底通过了多少 case
- 失败最常见的是哪类 blocker
- 如果只放宽 `phase_flip` 或 `stable_detection_rate`，会新增多少通过
- 这些新增通过里，有多少已经 `default_ready_for_result_freeze`
- 新增通过的 `final_engineering_score` 中位数是否仍为负

当前默认会比较四个方案：

- `current_default`
- `relax_phase_flip_to_0.55`
- `relax_stable_rate_to_0.15`
- `relax_phase_flip_and_stable_rate`

而且判断逻辑是保守的：

- 只要新增通过 case 的 `final_engineering_score` 中位数仍为负，就拒绝把它提升为默认门槛
- 即使分数中位数不差，只要新增通过里 `caution_probe_before_result_freeze` 占多数，也仍不建议直接放宽默认 gate

这份报告当前应理解为：

- 基于 `summary.csv` 的后处理分析
- 适合在正式主库重算完成后，按需单独生成
- 不应再被误读成 precompute CLI 的默认输出

### `build_result_health_report(summary_df, top_k=10) → dict`

把已经冻结好的 `summary.csv` 继续压缩成一份“默认结果库还能不能安心继续用”的监控报告。

当前会系统归约：

- `status_distributions`
  - `observation_freeze_status`
  - `delta_phi_gouy_validity`
  - `interference_overlap_default_freeze_status`
  - `projection_default_freeze_status`
  - `rho_physical_envelope_status`
  - `reference_width_saturation_status`
- `recommendation_distribution`
- `engineering_gate_distribution`
- `health_slices`
  - `by_wavelength_nm`
  - `by_particle_material`
- `width_saturation_by_width`
  - `mean / min / max reference_width_saturation_factor`
  - 各 `width_nm` 下的 `observation_freeze_status_distribution`
- `monitoring_summary`
  - `default_ready_fraction`
  - `observation_caution_fraction`
  - `shared_beam_caution_fraction`
  - `rho_out_of_envelope_count`
  - `narrower_width_has_stronger_saturation_factor`
- `monitoring_guidance`
- `top_caution_cases`

这一步和 `freeze_probe` 的分工不同：

- `build_freeze_probe_report()` 解决的是“现在能不能从 quick probe 放行到 full-range 重冻结”
- `build_result_health_report()` 解决的是“默认 full-range 结果库已经冻结后，当前还应该持续盯哪些系统性风险”

当前标准 full-range 结果库在重算完成后应生成：

- `fine_full_range_biomimetic_exosome_10000e_result_health.json`

当前这份 health report 在现行代码下至少应继续稳定导出：

- `default_ready_fraction`
- `shared_beam_caution_fraction`
- `rho_out_of_envelope_count`
- `narrower_width_has_stronger_saturation_factor`
- `monitoring_guidance`

最近这一轮又补了一层更实用的 dashboard 消费语义：

- `by_wavelength_nm` 会直接给出每个波长子组的
  `default_ready_fraction / observation_caution_fraction / shared_beam_caution_fraction / engineering_gate_pass_fraction / recommended_default_fraction`
- `by_particle_material` 会给出每类粒子的同一组健康切片
- 因此 `Design Explorer` 和 `Case Inspector` 不再只能看整库平均，而是能直接看到 caution 集中在哪个波长或哪类粒子

### `build_precompute_sim_cfg(grid_name) → SimulationConfig`

返回 dashboard 预计算专用配置。

这里有一个很重要的当前口径：

- 包级默认 `DEFAULT_SIM_CFG` 仍然可以是 `joint`
- 但 dashboard 预计算必须强制用 `single`

原因是 dashboard 的预计算结果本质上是“每个粒子 / 每个 case 一行”。像 `full_range` 这种包含 54 个粒子的库，如果继续沿用 `joint`，在当前模型定义下根本不可计算。

### `results_to_dataframe(results) → pd.DataFrame`

将 sweep 结果展平为 CSV 行。从 `r["intrinsic"]` 和 `r["reference"]` 中提取物理量。

关键列：`particle_name`, `particle_material`, `particle_diameter_nm`, `wavelength_nm`, `width_nm`, `depth_nm`, `score`, `engineering_score`, `final_engineering_score`, `robust_score`, `joint_score`, `detection_rate`, `detection_decision_mode`, `engineering_decision_basis`, `engineering_basis_detection_rate_wilson_lb`, `engineering_basis_stable_detection_rate_wilson_lb`, `engineering_basis_mean_peak_margin_z`, `single_channel_detection_rate`, `single_channel_detection_rate_wilson_lb`, `paired_channel_detection_rate`, `paired_channel_detection_rate_wilson_lb`, `strict_paired_detection_rate`, `strict_paired_detection_rate_wilson_lb`, `engineering_gate_basis`, `engineering_gate_strict_paired_rate_lb`, `engineering_gate_required_strict_paired_detection_rate`, `mean_peak_height`, `mean_positive_peak_height`, `mean_negative_peak_height`, `positive_peak_fraction`, `negative_peak_fraction`, `mean_local_snr`, `mean_transit_time_ms`, `mean_nodi_transit_bandwidth_Hz`, `mean_nodi_transit_bandwidth_gain`, `mean_nodi_bandwidth_limited_fraction`, `paired_detection_rate`, `CV`, `Csca_m2`, `E_sca_at_det`, `E_sca_ref`, `E_sca_normalized`, `A_ref`, `g_ref`, `phi_projection_rad`, `phi_sca_material_rad`, `phi_sca_material_parallel_rad`, `phi_sca_material_perpendicular_rad`, `rho_requested`, `rho_physical_envelope_nominal`, `rho_physical_envelope_lower`, `rho_physical_envelope_upper`, `rho_physical_ratio_to_nominal`, `rho_physical_envelope_in_range`, `rho_physical_envelope_status`, `reference_diffraction_efficiency_zeroth_order`, `reference_diffraction_efficiency_first_order`, `reference_width_saturation_mode`, `reference_width_saturation_status`, `reference_width_saturation_factor`, `reference_width_effective_nm`, `path_opd_model`, `path_opd_reference_plane`, `path_opd_z_geometry_factor`, `path_opd_z_reference_mode`, `path_opd_default_model`, `path_opd_model_role`, `path_opd_default_frozen`, `path_opd_freeze_status`, `H_norm`, `R_norm`, `CV_norm`, `local_snr_norm`

### `build_freeze_probe_report(results, top_k=10) → dict`

把 case 级结果归约成一个“能不能进入结果冻结”的 dataset-level sanity report。

当前会聚合：

- `path_opd_freeze_status`
- `interference_overlap_default_freeze_status`
- `projection_default_freeze_status`
- `delta_phi_gouy_validity`
- `observation_freeze_status`
- `rho_physical_envelope_status`
- `design_recommendation_status`

同时还会按 `width_nm` 分组导出：

- `mean_A_ref`
- `mean_reference_to_scattering_amplitude_ratio`
- `mean_interference_overlap_factor_abs`
- `mean_final_engineering_score`
- `dominant_observation_freeze_status`

并在 `sanity_checks` 里给出：

- `observation_ready_fraction`
- `review_required_fraction`
- `shared_beam_caution_fraction`
- `rho_out_of_envelope_count`
- `narrow / wide channel` 的 reference、ratio、overlap 对比
- `narrow_channel_reference_more_conservative`

这一步的作用不是替代 full-range 结果库，而是把 “case-level freeze diagnostics” 提前收成 “coarse-probe 能否放行下一步重冻结” 的桥接报告。

当前 `results_to_dataframe()` / `results_to_compact()` 还会继续把结果浏览层的统一推荐标签一并导出：

- `design_recommendation_status`
- `design_recommendation_label`
- `design_recommendation_rank`
- `design_recommendation_guidance`

因此 precompute 产物现在不只保存 physics / score / gate，也会直接保存“默认推荐、需复核推荐、可研究但 gate 未过”这层解释语义。

这一轮又把 gate 解释层一起接进了导出：

- `engineering_gate_status_label`
- `engineering_gate_primary_blocker`
- `engineering_gate_primary_blocker_label`
- `engineering_gate_blocker_summary`
- `engineering_gate_guidance`

所以当前 compact / csv 不再只保留 `engineering_gate_reason` 原文，也会保留更稳定的 blocker 分类与用户提示。

### `results_to_compact(results) → list[dict]`

提取紧凑数据（summary + physics + scores），去掉 event trace 以控制文件大小。

每个 dict 结构：
```python
{
    "particle_name": str,
    "particle_material": str,
    "particle_diameter_nm": int,
    "wavelength_m": float,
    "width_m": float,
    "depth_m": float,
    "summary": {n_events, n_detected, detection_rate, mean_peak_height,
                mean_positive_peak_height, mean_negative_peak_height,
                positive_peak_fraction, negative_peak_fraction,
                std_peak_height, mean_peak_width_s, mean_local_snr,
                mean_transit_time_s, mean_nodi_transit_bandwidth_Hz,
                mean_nodi_transit_bandwidth_gain, mean_nodi_bandwidth_limited_fraction,
                detection_decision_mode,
                single_channel_detection_rate, single_channel_detection_rate_wilson_lb,
                single_channel_stable_detection_rate,
                paired_channel_detection_rate, paired_channel_detection_rate_wilson_lb,
                paired_channel_stable_detection_rate,
                strict_paired_detection_rate, strict_paired_detection_rate_wilson_lb,
                paired_detection_rate,
                rho_requested,
                rho_physical_envelope_nominal, rho_physical_envelope_lower,
                rho_physical_envelope_upper, rho_physical_ratio_to_nominal,
                rho_physical_envelope_in_range, rho_physical_envelope_status,
                reference_diffraction_efficiency_model,
                reference_diffraction_efficiency_zeroth_order,
                reference_diffraction_efficiency_first_order,
                reference_field_amplitude_envelope_nominal,
                reference_width_saturation_mode,
                reference_width_saturation_status,
                reference_width_saturation_factor,
                reference_width_effective_m,
                all_heights, all_widths},
    "physics": {
        Csca_m2, E_sca_at_det, E_sca_ref, E_sca_normalized, A_ref, g_ref,
        phi_projection_rad, phi_sca_material_rad,
        rho_requested, rho_physical_envelope_source,
        rho_physical_envelope_nominal, rho_physical_envelope_lower,
        rho_physical_envelope_upper, rho_physical_ratio_to_nominal,
        rho_physical_envelope_in_range, rho_physical_envelope_status,
        reference_diffraction_efficiency_model,
        reference_diffraction_efficiency_zeroth_order,
        reference_diffraction_efficiency_first_order,
        reference_field_amplitude_envelope_nominal,
        reference_width_saturation_mode,
        reference_width_saturation_status,
        reference_width_saturation_cutoff_ratio,
        reference_width_lambda_ratio_nominal,
        reference_width_lambda_ratio_effective,
        reference_width_effective_m,
        reference_width_saturation_factor,
        path_opd_model, path_opd_reference_plane, path_opd_z_geometry_factor,
        path_opd_z_reference_mode,
        path_opd_default_model, path_opd_model_role,
        path_opd_default_frozen, path_opd_freeze_status,
        phi_sca_material_parallel_rad, phi_sca_material_perpendicular_rad
    },
    "score": float,
    "robust_score": float,
    "joint_score": float | None,
    "engineering_decision_basis": str | None,
    "engineering_basis_detection_rate_wilson_lb": float | None,
    "engineering_basis_stable_detection_rate_wilson_lb": float | None,
    "engineering_basis_mean_peak_margin_z": float | None,
    "engineering_gate_basis": str | None,
    "engineering_gate_strict_paired_rate_lb": float | None,
    "engineering_gate_required_strict_paired_detection_rate": float | None,
}
```

也就是说，预计算 compact 数据现在已经能把 case 级“散射材料相位”和“探测投影相位”一起冻结下来，Inspector / Interference Explorer 读取 compact 数据时不必再靠页面端重推这些量。

这一轮 compact 里又补进了偏振基底一致性字段：

- `scattering_projection_basis`
- `reference_projection_basis`
- `reference_projection_basis_match`
- `reference_projection_coupling_status`

因此 Inspector 现在不仅能回看“材料相位 / 投影相位”，也能回看
reference 与 scattering 是否真在同一 detector basis 上干涉。

**注意**：
- `quick` 档位只覆盖代表粒径，适合快速启动和默认浏览
- `full_range` 档位覆盖 `gold/exosome × [40, 50, ..., 300] nm`，离线预计算时间会明显高于 `quick`
- 当前这台 10 核机器上，`workers=8` 的最新结果可参考：
  - `coarse + full_range`: `2,592 cases`, 正式实测 `3277.2 s`，约 `54.6 min`
  - `fine + full_range`: 暂未在当前主链下重新正式实测；仍建议先以 coarse 结果冻结和 gate 校准为主

### `build_metadata(grid_name, config_tag, particle_profile, sim_cfg, grid, particle_types, results) → dict`

生成 meta.json 内容。包含：
- `dashboard_schema_version: "1.4"` — 面板启动时检查此字段
- 完整 `SimulationConfig`
- 粒子列表、波长列表
- 光学系统参数（beam waist, collection_theta_rad）
- `optical.illumination_effective_beam_waists_by_wavelength_nm`

---

## 当前 freeze probe 结论

`2026-04-05` 已按当前主链重跑：

- `../../results/coarse_current_model_probe_summary.csv`（历史结果文件，当前工作区可能不存在）
- `../../results/coarse_current_model_probe_compact.pkl`（历史结果文件，当前工作区可能不存在）
- `../../results/coarse_current_model_probe_meta.json`（历史结果文件，当前工作区可能不存在）
- `../../results/coarse_current_model_probe_freeze_probe.json`（历史结果文件，当前工作区可能不存在）

当前 sanity report 的结论是：

- `path_opd_freeze_status` 全部为 `default_frozen_active`
- `projection_default_freeze_status` 全部为 `default_frozen_active`
- `interference_overlap_default_freeze_status` 全部为 `default_frozen_active`
- `rho_physical_envelope_status` 全部为 `within_envelope`
- `observation_freeze_status` 分成：
  - `default_ready_for_result_freeze = 54 / 96`
  - `caution_probe_before_result_freeze = 42 / 96`
- `review_required_fraction = 0.0`
- `rho_out_of_envelope_count = 0`

因此当前 coarse probe 的历史阻塞项已经解除。现阶段真正的标准结果库已经是 `fine + full_range`，而 `coarse + full_range` 更适合作为 benchmark、回归验证和局部排查基线；当前仍保留的 `shared_beam_caution` 与 `narrow_channel_reference_more_conservative = false` 更适合作为监控项，而不是继续阻塞结果库冻结。

---

## 依赖关系

- **读取**：`config.py`（所有配置）
- **调用**：`nodi_simulator.run_parameter_sweep`
- **被调用**：命令行 / 手工全量重算流程 / `backend.run_live_sweep` 中导入转换函数
---

## 2026-04-06 实现收口

这一轮对 `dashboard/precompute.py` 和 `parameter_sweep.py` 做了系统性收口，重点是减少状态分叉、提升 checkpoint/resume 稳定性，并让运行期产物与保存期产物都来自同一套规则。

- 命名规则统一：
  所有产物统一从 `{prefix} = "{grid}_{tag}"` 派生，包括
  `{prefix}_progress.json`、
  `{prefix}_checkpoint/manifest.json`、
  `{prefix}_checkpoint/chunks/chunk_*.pkl`、
  `{prefix}_summary.csv`、
  `{prefix}_compact.pkl`、
  `{prefix}_meta.json`、
  `{prefix}_result_health.json`、
  `{prefix}_freeze_probe.json`。

- 状态对象结构化：
  `precompute` 主链现在明确拆成
  `SweepRuntimeProgress`、
  `PrecomputeJobState`、
  `PrecomputeRunContext`、
  `PrecomputeSaveContext`，
  不再在 `precompute_sweep()` 里散落维护多份局部 dict。

- 协议统一：
  `*_progress.json` 和 `*_checkpoint/manifest.json` 的 payload 都来自统一 builder；
  `parameter_sweep.py` 的 progress callback payload、`last_case` 快照和 stdout 进度输出也都已统一。

- checkpoint / resume 稳定化：
  现在支持从中途落盘的 raw case 恢复，并兼容旧 manifest 里的 `chunk_count` 字段，再统一标准化为 `checkpoint_chunk_count`。

- 保存阶段去样板：
  save-step pipeline 已统一为结构化步骤，固定顺序是
  `summary -> compact -> meta -> result_health -> freeze_probe`，
  不再逐段复制 `_save_*` 模板。

- 验证结果：
  相关改动已通过 `py_compile`、`pytest` 和 `tests/run_tests.py` 的定向验证。
  当前剩余 warning 主要是 pytest cache 权限 warning 与 Streamlit runtime warning，不影响逻辑正确性。
- 补充
  `parameter_sweep.py` 的逐 case verbose 输出现在也统一走命名 helper，`progress callback`、stdout 进度行、逐 case 成功/失败日志不再在主循环里各自拼接。
- 补充
  预计算导出的 `meta / result_health / freeze_probe` 已收敛到结构化 payload builder；`results_to_dataframe()` 与 `results_to_compact()` 也开始复用共享结果字段 builder，降低导出字段漂移风险。
2026-04-12 result-status update:

- The old `fine + full_range` result artifacts have been cleared to make room for the next recompute.
- The standard target library now remains `fine_full_range_biomimetic_exosome_10000e_*`.
- The next default fine full-range outputs should be:
  `fine_full_range_biomimetic_exosome_10000e_summary.csv`
  `fine_full_range_biomimetic_exosome_10000e_compact.pkl`
  `fine_full_range_biomimetic_exosome_10000e_meta.json`
  `fine_full_range_biomimetic_exosome_10000e_result_health.json`
  `fine_full_range_biomimetic_exosome_10000e_freeze_probe.json`
- Optional postprocess artifact:
  `fine_full_range_biomimetic_exosome_10000e_engineering_gate_calibration.json`
- Code-readiness and recompute-readiness should now be checked against:
  [41_实验对齐原则与计算修正备忘.md](../../41_实验对齐原则与计算修正备忘.md)
  [42_全量重算前复核结论与现行边界.md](../../42_全量重算前复核结论与现行边界.md)
