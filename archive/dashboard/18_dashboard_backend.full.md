# dashboard/backend.py — 后端接口

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。

> 2026-04-10 补充：`backend.py` 现在会优先识别并加载 `fine_full_range_biomimetic_exosome_10000e`，把它视为当前标准 biomimetic exosome 全量库；旧 `fine_fine_full_range_10000e` 只作为可选历史对照存在。


> 2026-04-07 补充：当前 backend 的标准结果库默认指向四波长 `fine_full_range_*` 主库；`data_prefix`、schema 以及 live/standard 切换都应按 `404 / 488 / 532 / 660 nm` 与 `55296 cases` 理解。



## 当前使用方式

- 文档定位：dashboard 数据桥接说明
- 推荐阅读时机：当你要理解结果库加载、prefix 切换、live/standard 边界和 bundle 构造时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/backend.md](../../dashboard/backend.md)
- [16_dashboard_precompute.full.md](./16_dashboard_precompute.full.md)
- [17_dashboard_app.full.md](./17_dashboard_app.full.md)

## 文件职责

面板的数据层和计算层。提供四类功能：
1. **数据加载**：读取 CSV / pkl / meta，含 schema 版本校验
2. **Explorer 构图**：热图矩阵、1D 切片、权重重算
3. **Inspector 构图**：case 查找、物理分解
4. **参数调节**：从 UI 构建配置、运行 live sweep、按需重算单 case

不包含任何 Streamlit UI 代码（`run_case_on_demand` 除外，需读取 session_state）。

---

## Schema 版本管理

```python
CURRENT_SCHEMA_VERSION = "1.4"
```

面板启动时 `check_data_files` 会验证 meta.json 中的 `dashboard_schema_version` 字段。三种异常分别对应：
- 文件缺失 → `FileNotFoundError`
- meta 缺少版本字段 → `ValueError`
- 版本不匹配 → `ValueError`

当前 `schema 1.4` 的主要变化是：

- `meta["sim_cfg"]` 记录完整 `SimulationConfig`
- `meta["optical"]` 按波长分别记录 effective illumination waist

因此 backend 现在不再依赖“手工挑出来的少数 provenance 字段”来判断结果库口径。

---

## 数据加载函数

| 函数 | 返回 | 说明 |
|------|------|------|
| `check_data_files(results_dir, prefix)` | `(csv, pkl, meta)` 路径 | 校验文件存在性 + schema 版本 |
| `list_available_datasets(results_dir)` | `list[str]` | 扫描目录列出可用数据集前缀 |
| `load_sweep_summary(csv_path)` | `pd.DataFrame` | 加载 CSV |
| `load_sweep_compact(pkl_path)` | `list[dict]` | 加载 pickle |
| `load_metadata(meta_path)` | `dict` | 加载 JSON，不存在时 raise |
| `load_result_health(results_dir, prefix, summary_df=None)` | `dict \| None` | 优先读取 `*_result_health.json`；若旧结果库没有该文件，则基于当前 `summary_df` 即时补一份 dataset-level 健康报告 |

### 主流程数据源优先级（2026-04-07）

当前 backend 已把 dashboard 主流程的预计算数据源优先级固定为：

1. `fine_full_range_biomimetic_exosome_10000e`
2. `fine_fine_full_range_10000e`
3. `fine_full_range`
4. `fine_current_model_full_range`
5. `coarse_full_range`
6. `coarse_default`

并新增两条收口规则：

- 若 session 中残留的是旧主流程前缀 `coarse_default / coarse_full_range / fine_full_range / fine_fine_full_range_10000e`，`sync_dashboard_data_prefix()` 会在 `fine_full_range_biomimetic_exosome_10000e` 存在时自动迁移到新标准结果库；这是兼容旧状态的修正逻辑，不表示旧前缀仍属于当前主流程
- `build_dashboard_data_source()` 现在会把 `fine_full_range_biomimetic_exosome_10000e` 明确标记为“标准 full-range 结果库”，而把 live 路径明确标记为“工程调试重算 sweep（非默认阅读路径）”

当前这两条加载路径又补了一层**旧结果兼容回填**：

- 如果旧版 `summary.csv` 缺少 `design_recommendation_*` 或 `engineering_gate_*` 解释字段，`load_sweep_summary()` 会在读入后按现有 `engineering_gate_passed / engineering_gate_reason / engineering_gate_failed_count / observation_freeze_status` 自动补齐。
- 如果旧版 `compact.pkl` 缺少这些字段，`load_sweep_compact()` 会在 `root / summary / physics` 三层同步补齐。
- 这意味着当前默认冻结结果库即使早于“推荐标签 / gate 解释”这轮实现，也能在 dashboard 中直接展示最新解释，而不必为了字段可见性立刻重跑 full-range。
- 同样地，如果旧版结果目录还没有 `*_result_health.json`，`load_result_health()` 也会优先用当前 `summary_df` 即时回填一份健康报告，因此页面层不需要关心结果库是否早于 health-report 这轮实现。

---

## Explorer 构图函数

### `build_heatmap_matrix(df, particle, wavelength_nm, value_col) → (W_arr, H_arr, matrix)`

从 DataFrame 构建 2D 热图矩阵。matrix.shape = (nH, nW)。

### `build_slice_data(df, particle, wavelength_nm, fixed_dim, fixed_val, value_col) → (x_arr, y_arr)`

提取 1D 切片。`fixed_dim` 为 `"width"`（固定 W，变 H）或 `"depth"`（固定 H，变 W）。

### `recompute_scores(df, w_height, w_rate, w_cv) → pd.Series`

用新权重重算 single score。返回 Series 赋给 `df["score_display"]`，**不覆盖原始 `df["score"]`**。

**重要**：只影响 single score。`robust_score` 和 `joint_score` 依赖邻域结构和配对，不可在面板内重算。

---

## Inspector 构图函数

### `get_case_summary(compact, particle, wavelength_nm, W_nm, H_nm) → dict | None`

从 compact 数据中按参数查找 case。使用 `np.isclose(atol=1e-12)` 做浮点匹配，避免 nm↔m 转换精度丢失。

### `build_physics_breakdown(case_data) → dict`

将 case 数据拆分为两组：
- `case_physics`：本征散射量（Csca, E_sca, g_ref, A_ref，以及 `phi_projection / phi_sca_material / phi_sca_material_parallel / phi_sca_material_perpendicular` 这组 case 级相位诊断）
- `batch_outcome`：统计结果（detection_rate, mean_height, CV，以及 `mean_local_snr / mean_transit_time_ms / mean_nodi_transit_bandwidth_Hz / mean_nodi_transit_bandwidth_gain / mean_nodi_bandwidth_limited_fraction / single_channel_detection_rate / paired_channel_detection_rate / paired_channel_stable_detection_rate / strict_paired_detection_rate / strict_paired_detection_rate_wilson_lb / paired_detection_rate / ROC-AUC / d′` 这类工程判别量；当前也会带出 `engineering_decision_basis / engineering_basis_detection_rate_wilson_lb / engineering_gate_basis / engineering_gate_strict_paired_rate_lb / engineering_gate_required_strict_paired_detection_rate` 供 Inspector 展示）

现在这个返回值前面还多了一层统一结果解释块：

- `decision_summary`

它由 `build_case_decision_summary(...)` 统一生成，并把：

- `design_recommendation_*`
- `engineering_gate_*`
- `observation_freeze_status`

归约成一组稳定字段：

- `decision_summary_tone`
- `decision_summary_headline`
- `decision_summary_badge`
- `decision_summary_primary_message`
- `decision_summary_blocker_text`
- `decision_summary_next_step`

因此 `build_physics_breakdown()` 现在不只是在“拆数字”，也在负责把单 case
最终解释语义统一提供给 Inspector 和其他结果页。

当前 backend 侧又多了一层 dataset-level 兼容加载：

- `Design Explorer` 会通过 `load_result_health()` 读取或即时回填结果库健康摘要
- `Case Inspector` 也会复用同一份健康摘要，提示当前 case 所属结果库的整体 ready / caution 状态

因此现在 backend 不仅能回答“单个 case 为什么这样”，也能回答“这整个结果库目前是否仍值得继续当默认基线使用”。

本轮又把路线图里 reference-amplitude / shot-noise sanity check 需要的量直接接进了 `case_physics`：

- `reference model tier / role`
- `geometry_scaled depth exponent / depth scaling class`
- `mean I_baseline`
- `mean shot-noise std`
- `shot-noise baseline-dominated fraction`
- `mean A_ref(local) / mean A_sca(local)`
- `mean |E_ref|/|E_sca|`
- `reference-dominated fraction`
- `rho requested / rho envelope nominal / rho envelope lower / rho envelope upper`
- `rho / nominal envelope`
- `rho envelope status`
- `reference first-order diffraction efficiency`
- `reference width saturation mode / status / effective width / saturation factor`

当前 `dashboard/signal_backend.py` 里还补了一条单 case 专用的
`build_rho_sensitivity_report(...)`：

- 它不会改写 `sim_cfg.rho`
- 但会把当前 `requested / lower / nominal / upper` 四个 `rho` anchor
  逐个重算成一个小表
- 表里会同时导出 `A_ref / peak clean / heterodyne gain / detection rate /
  stable detection rate / gate / recommendation`
- summary 还会归约成
  `rho_sensitivity_status / label / guidance`

这样 backend 现在不只会说“当前 rho 是否出界”，还会直接回答：

- 如果把 `rho` 拉回 nominal，这个 case 的检测率会不会明显变化
- 这个 case 是“包络内且稳”，还是“包络外且敏感”
- 绝对检测率的不确定性到底只是提示级，还是已经足以翻转工程结论

因此 Inspector 现在不只是在看“峰高和检测率”，也能直接看到：

- 当前 reference model 到底属于哪一档精度
- `geometry_scaled` 的 `H` 指数更像 amplitude-like 还是纯经验值
- 当前 case 的噪声层是否真的是 reference baseline 主导
- 当前 `rho` 是否明显跑到了 reference-side 物理建议区间之外
- 当前 reference 的 width 向角谱是否已经进入 `W ≲ λ_eff` 的软 cutoff 区间

Interference Explorer 侧当前还会在 case summary 中直接暴露 OPD 语义：

- `path_opd_model`
- `path_opd_reference_plane`
- `path_opd_z_geometry_factor`
- `path_opd_z_reference_mode`
- `path_opd_default_model`
- `path_opd_model_role`
- `path_opd_default_frozen`
- `path_opd_freeze_status`

这样 backend / signal backend 现在不仅能回答“峰值是多少”，也能回答当前
`phi_sca_path_z` 是按哪一种 reference-plane surrogate 解释的，以及当前是不是默认冻结主线。

这一轮又把 freeze judgement 的聚合结果直接接到了 backend / Inspector 可读层。
当前 summary / physics 层还会继续暴露：

- `interference_overlap_default_frozen / interference_overlap_default_freeze_status`
- `projection_default_frozen / projection_default_freeze_status`
- `delta_phi_gouy_validity`
- `delta_phi_gouy_geometry_width_to_waist_ratio / depth_to_waist_ratio`
- `observation_freeze_status`
- `design_recommendation_status / design_recommendation_label / design_recommendation_guidance`
- `engineering_gate_status_label / engineering_gate_primary_blocker_label / engineering_gate_blocker_summary / engineering_gate_guidance`

因此单 case 复盘现在不仅能看 OPD 语义本身，还能直接看：

- collapsed overlap 是否仍被接受为默认冻结主线
- 当前 shared phase-aware projection basis 是否仍处于 frozen 状态
- shared-beam `delta_phi_gouy` 只是 `caution` 还是已经几何上可接受
- 整条 observation chain 是否已进入 `default_ready_for_result_freeze`
- 当前结果在浏览层到底属于“推荐（默认）”“推荐（需复核）”还是“可研究（门槛未过）”
- 当前 case 真正主要卡在“稳定检出率不足”“相位翻转过高”还是“双通道确认不足”
- 当前页面 callout 到底应该显示 success / warning / error / info 中的哪一类
- 当前 case 的一句话 headline、主要判断和建议关注项是什么

这一轮 backend 又把偏振基底一致性诊断接通了。当前 summary / physics
层会直接暴露：

- `scattering_projection_basis`
- `illumination_projection_basis`
- `reference_projection_basis`
- `interference_projection_basis_match`
- `reference_projection_coupling_status`

因此页面不再只知道“当前是 parallel 还是 perpendicular”，还知道
reference / illumination 是否与 scattering 真共用同一 detector basis。

返回原始数值，格式化由 Inspector 负责。

---

## 参数调节函数

### `build_sim_cfg_from_ui(...) → SimulationConfig`

从 UI 控件值构建 SimulationConfig。基于 `DEFAULT_SIM_CFG` 深拷贝后覆盖改动字段。

### `build_optical_from_ui(beam_waist_y_nm) → OpticalSystem`

从 UI beam_waist_y 值构建 OpticalSystem。基于 `OPTICAL_TEMPLATE` 深拷贝后覆盖。

### `build_live_tag(sim_cfg) → str`

自动生成可读标识。格式示例：`rho20_a0.8b0.3g1.0_n0.030_diff_geom_gaus_143025`

包含：ρ 值、α/β/γ（geometry_scaled 模式下）、噪声、扩散开关、模型缩写、时间戳。

### `run_live_sweep(sim_cfg, optical_template, particle, grid_name="coarse") → (DataFrame, list[dict])`

用自定义参数和**单个用户选择粒子**跑命名 preset sweep。当前可直接用于 `coarse` 或 `fine` 这类在 `GRID_CONFIGS` 中注册的网格。

流程：
1. 深拷贝 sim_cfg，覆盖 n_events
2. 强制 `score_mode="single"`，因为 live sweep 当前只比较一个粒子
3. `validate_simulation_config` 检查参数合理性
4. 调用 `run_parameter_sweep`
5. 通过 `results_to_dataframe` / `results_to_compact` 转换

### `build_local_fine_grid(center_W_nm, center_H_nm, ...) → dict`

围绕当前候选点建立局部 `100 nm` 细扫网格。主要用于第二轮分析流程：

1. 先用 `coarse` 找大致候选区
2. 再围绕当前 `W/H` 用 `local_fine` 看局部平台和峰位

这个 helper 会：

- 围绕中心点生成 `width_list_m` / `depth_list_m`
- 按允许范围 `[500, 2000] nm` 做边界裁剪
- 继承 `fine` 模式的波长轴
- 记录 `half_window_nm / step_nm / n_events`

### `run_live_sweep_custom(sim_cfg, optical_template, particle, grid) → (DataFrame, list[dict])`

和 `run_live_sweep` 相同，但网格由调用者显式提供。`Design Explorer` 里的 `local_fine` 和 `Top 3 -> local_fine` 按钮都通过这个入口运行。

典型用途：

- 围绕当前候选点做局部 `100 nm` 细扫
- 在测试里构造最小自定义 grid 验证 live sweep 行为

### `run_case_on_demand(particle_name, wavelength_nm, W_nm, H_nm) → dict`

按需重算单个 case。**自动检测 live vs 默认参数**：读取 `st.session_state.using_live_data` 判断。

返回完整 batch 结果，含 `events` 列表（用于 trace 显示）。

---

## 依赖关系

- **读取**：`config.py`（延迟导入，避免循环）
- **调用**：`precompute.py`（转换函数）、`nodi_simulator`（sweep、batch、validation）
- **被调用**：`explorer.py`、`inspector.py`
- 2026-04-06 补充：dashboard 数据加载已新增统一 bundle 入口，当前活动数据源的 `df / compact / meta / health_report / source captions` 不再由 `Explorer` 和 `Inspector` 各自手写 live-vs-precomputed 分支。
## 2026-04-07 D / E 收口

- backend 新增 `load_workflow_case_anchor(results_dir, session_state)`。
- 这个 helper 会强制按预计算工作流口径读取当前选中 case，不受 `using_live_data=True` 影响。
- 目标是让 `Mie / Interference / Noise` 三页都从同一个标准结果库锚点出发解释，不再各自重复拼装 `load_dashboard_data_bundle() + lookup_summary_case_row()`。
