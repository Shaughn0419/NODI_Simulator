# Report 148 — no-data 相对审计 closure ledger（原极致模拟路线图收口版）

- 日期: 2026-06-10；closure 更新: 2026-06-12
- 前置: 本路线图承接 [report 147](147_detector_forward_identity_full_chain_adversarial_audit_synthesis_20260610.md)
  的全部 P1/P2 发现。
- 当前定位: 本文件已从“待执行路线图”收口为 **no-data 相对审计 closure ledger**。它记录哪些任务已经
  用现有 artifact / 零重跑审查关闭，哪些任务被 owner 裁决为不再阻断 no-data 定稿、转入
  “模拟可补 / 实测优先”交接。
- 定稿边界: no-data 封板门已经收窄为 `R2/V1` A/B/C/D 全 3-seed 主判决 +
  A/B 的 V2 抽样 gauge 检验。R1 读出轴与 C/D×V2 不纳入 no-data 封板范围。
- 非授权: 本 closure 不授权 calibrated SNR/LOD/blank-FPR、detector-resolved winner、
  绝对跨波长 winner、生物真值或 NODI 外差增强倍数 claim。
- 保留说明: 下文原 T1–T9 的技术骨架保留为审计可追溯与后续交接材料；除明确标为
  `completed_under_no_data_scope` 的项目外，不再作为 report 147 no-data 定稿的阻断条件。
- 阅读规则: 下文技术骨架中的“必须 / 做法 / 判决 / 立即”等命令式语气，只在未来重新激活相应
  handoff 任务时生效；它们不是当前 no-data closure 的待办项。

---

## 0. 总原则与依赖关系

**closure 裁决:** report 147/148 的 no-data 定稿不再追求把所有 surrogate 自由度补成完整扫描轴。
当前已经完成的封板目标是: 在现有 artifact 下，把 Stage-1/T3/T4 三轮审查收口为
**candidate-families under detector surrogate**，并把无法由 no-data 模拟 clean-resolve 的轴显式移交。

**(#10 边界)** 这里的"无实测数据可达的上限"指的是
**surrogate-axis explicitness / uncertainty propagation / claim governance 的工程上限**，
**不是 optical truth 或 biological truth 的上限**——无实测数据**不可能**逼近物理/生物真实上限，
那需要 BFP/标准粒子/blank 标定(见 report 147 §7)。

固定不动(本轮不重写)分两档, **不要混为一谈(#1)**:
- **由 report 147 §1 独立重算验证(engine closure)**: Mie/core-shell 数值引擎、截面、角振幅、Rayleigh、光学定理;
- **本轮暂不重写、但验证状态≠Mie engine closure**: Wilson、受阻布朗输运、illumination 场包络
  (它们只是"本轮不动", 不代表已被 §1 同级验证)。

原依赖图(保留为历史设计，不再表示 no-data 定稿阻断链):

```
[T8 v1 summary 零重跑(E_sca_normalized); Lens-B emit deferred] ─┐
[T6 派生表符号修复(零重跑; deferred polish)]                   ─┼─► 原立即可做项; 现为交接材料
[T5 provenance 字段(零重跑)]                            ─┘

[T1 route-aware event trace] ─► [T1g model A/B/C/D × R1/R2 × V1/V2 小网格]
[T2 gauge ρ 轴]  ─┐
[T3 noise 轴]    ─┼─► 与 T1g 合并成一个"统一不确定度扫描"
[T4 EV-RI 轴]    ─┘

[T7 theta_phase 推导 / k_m_inv / bundle] ─► 清理项, 可并行
[T9 测试集] ─► 贯穿全程
```

**no-data closure 摘要(2026-06-12):**

| 项 | closure 状态 | 说明 |
|---|---|---|
| Stage-1 主判决 | `completed_under_narrowed_no_data_gate` | `R2/V1` A/B/C/D 全 3-seed；A/B 的 `R2/V2` 抽样 gauge 检验完成 |
| T3 noise 轴 | `completed_for_no_data_claim` | selected-annulus 深度噪声底主导；all-crossing 与 selected-annulus 双口径并立 |
| T4 EV-RI / bright-EV | `completed_for_no_data_claim` | 7 bright-EV combo 全 Wilson 重叠；4 个点估计 seed 一致 404 但非区间分离，3 个 genuine near-tie |
| T7 清理 | `completed_under_no_data_scope` | `theta_phase` 登记为唯象假设；`k_m` canonical / `k_m_inv` deprecated alias；external-bundle mode 已补 |
| R1 全轴 | `deferred_out_of_no_data_gate` | R1-不变性是假设、未测；模拟可补但优先级低于实测桶 A |
| C/D×V2 | `deferred_out_of_no_data_gate` | 仅由 A/B×V2 抽样 gauge 检验代表；模拟可补但不阻断 no-data 定稿 |
| T1/T2/T5/T6/T8 全量工程化 | `handoff_not_blocking_no_data_final` | 保留为后续模拟可补 / 交接材料，不再要求本轮执行 |

**核心可行性发现(历史设计, 保留作交接)**: A/B/C/D 四路在 **event 级只差 case-level 标量**，
且三条时域分量 `scattering_only_intensity`、`interference_cross_term_joint`、
`interference_cross_term_collapsed` 在 **full-diagnostics(slow) path 已算好**(见 T1.1)。
**因此 V1 slow-path 原型可作为有界 route 组装层落地; 但完整 route-aware event tracing 仍需另行处理:
fast/vectorized path(C2)、route-specific readout/noise(M2/M3/#3)、以及 V2 raw-angular tuple 生成(#4-#6)。
"不是重写 pipeline"只对 slow-path V1 成立, 不要外推到 fast/V2。**

---

## 1. T1 — Detector-forward identity 解析(最高优先级 P1)

**closure 状态:** `handoff_not_blocking_no_data_final`。Stage-1 已用收窄门完成主判决:
`R2/V1` A/B/C/D 全 3-seed + A/B `R2/V2` 抽样 gauge。下文 route-aware event trace 设计保留为
未来模拟可补/实测交接材料；R1 与 C/D×V2 不再阻断 report 147 no-data 定稿。

### 1.1 先把 event 级路由代数推清楚(决定实现量)

case 级一次性算好(均来自现有 `compute_detected_scattering_field` + `bfp_detector_operator`):

| 量 | 来源 | 含义 |
|---|---|---|
| `E_sca_unit_normalized` (复) | parameter_sweep.py:6730 | 塌缩散射场(归一化) |
| `self_collapsed ≡ \|E_sca_unit_normalized\|²` | 上者取模平方 | C/A 的自项核 |
| `self_roi ≡ self_sca_detector_integrated` | bfp_detector_operator.py:280 | B 的自项核(=∫w\|s\|²) |
| `R_self ≡ self_roi / self_collapsed` | 二者相除 | **A→B 的自项放大因子(含 1/throughput)**; **expected ≥1 under current positive-kernel/current-throughput surrogate convention, 非普适定理(#3)** |
| `cross_joint(t)` | `interference_cross_term_joint` | A/B 共用的角谱重叠交叉项 |
| `cross_collapsed(t)` | `interference_cross_term_collapsed` | C 的塌缩积交叉项 |
| `self_t ≡ scattering_only_intensity(t)` | interferometric_trace | `=A_env(t)²f² self_collapsed` |

**关键: 因为 A 与 B 的自项都 ∝ `A_env(t)²f²`，二者之比 `R_self` 是时间无关常数。** 于是四路时域信号：

```
signal_A(t) = self_t            + cross_joint(t)        # 当前 production(hybrid)
signal_B(t) = R_self · self_t   + cross_joint(t)        # ROI 强度积分
signal_C(t) = self_t            + cross_collapsed(t)    # collapsed coherent
signal_D(t) =                     cross_joint(t)        # cross-only
```

三条分量 (`self_t`, `cross_joint(t)`, `cross_collapsed(t)`) 在 **full-diagnostics(slow) path** 已返回；
**对 V1 slow path, route assembly 主要只需新增标量 `R_self` 与一个 route 组装函数**。
**但这不是全部 plumbing(#2)**: fast/vectorized path(C2)、route-specific noise/readout(M2/M3)、
V2 raw-angular tuple(#4–#6) 都仍需额外实现。

### 1.2 代码骨架 — route-aware 组装

新增 `nodi_simulator/detector_route_assembly.py`:

```python
import numpy as np
DETECTOR_ROUTES = ("A_hybrid", "B_roi_intensity", "C_collapsed_coherent", "D_cross_only")

def compute_r_self(reference: dict, E_sca_unit_normalized: complex) -> float:
    """R_self = self_roi / self_collapsed (case-level; includes 1/throughput).
    Expected >=1 under the current positive-kernel/current-throughput surrogate convention,
    NOT a universal invariant (changes if V2 normalization or calibrated throughput/gauge changes)."""
    self_collapsed = float(abs(complex(E_sca_unit_normalized)) ** 2)
    self_roi = reference.get("self_sca_detector_integrated")
    if self_roi is None or self_collapsed <= 0.0:
        return float("nan")   # route lane unavailable -> gate False
    return float(self_roi) / self_collapsed

def assemble_route_signal(trace: dict, route: str, r_self: float) -> np.ndarray:
    """Build the per-route signed signal_trace(t) from existing components."""
    self_t = np.asarray(trace["scattering_only_intensity"], dtype=float)
    cross_joint = np.asarray(trace["interference_cross_term_joint"], dtype=float)
    cross_collapsed = np.asarray(trace["interference_cross_term_collapsed"], dtype=float)
    if route == "A_hybrid":
        return self_t + cross_joint
    if route == "B_roi_intensity":
        return r_self * self_t + cross_joint
    if route == "C_collapsed_coherent":
        return self_t + cross_collapsed
    if route == "D_cross_only":
        return cross_joint
    raise ValueError(f"unknown detector route: {route}")
```

落地点: 组装层须插在 trace 调用(parameter_sweep.py:4089–4091)与噪声(4094–4101)之间，
对每条 route 用 `assemble_route_signal(...)` 得到 signed trace，再分别走 T1.4 的读出。

**【C2 重大修正 — "组件已算好"只对慢路径成立】** 三条分量
(`scattering_only_intensity`/`interference_cross_term_{joint,collapsed}`)只在
`generate_interferometric_trace` 的 **full-diagnostics 分支(interferometric_trace.py:258–283)** 返回；
fast 分支(`export_full_diagnostics=False`, :162–197)只返回单条 `interference_cross_term`。
而生产有三个调用点: `simulate_one_event:4089`(默认 True)、
`_simulate_one_event_from_shared_physical_state:4536`(True)、**`_simulate_stream_event_block:5670`
(传 `export_full_diagnostics=False`)**。**向量化/流式引擎走 `_simulate_stream_event_block`(:7030)，
此时 `assemble_route_signal` 会 KeyError。** 因此 route lane 必须二选一:
(a) **强制 `sim_cfg.vectorized_event_engine="off"`**(as-run 默认即 off, data_objects.py:1352，
所以现有数据用的是慢路径) **并** 在三个调用点都强制 `export_full_diagnostics=True`; 或
(b) 把三条分量穿过 `_simulate_stream_event_block` + summary accumulator(这正是 report 147 §7
说的"event-trace plumbing 仍需开发"——本路线图原"有界组装层"措辞低估了这一点)。
**结论: T1 比"纯组装"多一层；务必先锁 `vectorized_event_engine=off` 跑通慢路径，再谈向量化。**

### 1.3 V1 gauge-locked vs V2 raw-angular(reviewer B 新 P1)

`R_self` 与 `cross_joint` 当前都来自 **gauge-locked** 诊断(`compute_detector_integrated_interference`
把角谱场 rescale 到 collapsed target, bfp_detector_operator.py:225–228)。两版定义:

| 版本 | self_roi / 角谱场 | 归一化锚 |
|---|---|---|
| **V1 gauge-locked** | 用现有 rescaled `self_sca_detector_integrated`(=保留 back-fit) | collapsed scalar target |
| **V2 raw-angular** | 用 raw `∫w\|s(θ)\|²`(s=`collection["angular_field_theta"]`, 已按投影; 不 rescale) | **ref/sca 各自显式 norm mode** |

V2 必须把"raw 角谱场如何归一化"写死，否则 ranking flip 可能只是 normalization flip:

**【#2 修正 — V2 必须给完整 raw detector tuple, 不能只 raw self】** 若只把 self 换成 raw、cross 仍沿用
V1 gauge-locked, V2 就退化成"raw-self + locked-cross"的新 hybrid, 不是真 raw-angular route。V2 必须从
raw 角谱场重算 **self / reference / joint / collapsed** 全套(不 rescale 到 collapsed target):

```python
def raw_angular_detector_tuple(intrinsic, collection, reference, operator, sim_cfg, *,
                               ref_norm_mode, sca_norm_mode):
    # 【#5】不要硬编码 S2/k(只对 parallel 成立)。用 collection 已按 scattering_projection_mode
    #   生成的 angular_field_theta(compute_detected_scattering_field 输出), 与 production 同投影。
    s_raw = np.asarray(collection["angular_field_theta"], complex)        # 已投影, 未 rescale
    r_raw = np.asarray(reference["reference_angular_field"], complex)     # 参考角谱(可能 2D θ/φ)
    # 【#6】ref 是 2D θ/φ、sca 通常 1D θ → 必须复用 bfp_detector_operator 的 resample/project/integrate
    #   路径(_resample_complex_theta_field + _prepare_projected_fields + _integrate_detector_terms),
    #   只把 target-collapsed rescale 关掉; 不能直接相乘(shape mismatch / 不可比)。
    s_e, r_e, phi = _resample_and_project(s_raw, r_raw, reference, operator, sim_cfg)  # 复用现有 helper
    # 【#4】ref 与 sca 来自不同 surrogate, 不能共用一个 n。各自归一, joint 用 n_ref*n_sca。
    n_ref = reference_norm(ref_norm_mode, r_e, operator)
    n_sca = scattering_norm(sca_norm_mode, s_e, operator)
    self_roi_raw      = roi_intensity_integral(s_e, operator, phi) / n_sca**2     # ∫w|s|²
    I_ref_raw         = roi_intensity_integral(r_e, operator, phi) / n_ref**2     # ∫w|r|²
    joint_raw         = roi_overlap_integral(r_e, s_e, operator, phi) / (n_ref*n_sca)  # ∫w r s*
    cross_raw         = 2.0 * np.real(joint_raw)                                  # = B/D 的 cross
    collapsed_ref_raw = roi_field_collapse(r_e, operator, phi) / n_ref            # ∫w r
    collapsed_sca_raw = roi_field_collapse(s_e, operator, phi) / n_sca            # ∫w s
    return dict(self_roi_raw=self_roi_raw, I_ref_raw=I_ref_raw, joint_raw=joint_raw,
                cross_raw=cross_raw, collapsed_ref_raw=collapsed_ref_raw,
                collapsed_sca_raw=collapsed_sca_raw,
                n_ref_raw=n_ref, n_sca_raw=n_sca,
                raw_reference_normalization_mode=ref_norm_mode,
                raw_scattering_normalization_mode=sca_norm_mode,
                joint_normalization_mode="n_ref_times_n_sca")
```
注: `_resample_and_project` / `roi_*` 为对 bfp_detector_operator 现有 `_resample_complex_theta_field` /
`_prepare_projected_fields` / `_integrate_detector_terms` 的薄封装(关掉 rescale), 不是新写积分器。
**(#8)** 更好的做法是**重构 bfp_detector_operator 暴露一个共享 primitive**
`compute_projected_detector_terms(..., rescale_to_collapsed_target: bool)`: V1 用 `rescale=True`,
V2 用 `rescale=False`。**避免 V1/V2 维护两套积分逻辑而未来漂移。**

V2 下四路用这套 raw 量重组(B 用 self_roi_raw + cross_raw; C 用 |collapsed_sca_raw|² + 2Re[collapsed_ref_raw·conj(collapsed_sca_raw)]; D 用 cross_raw)，
**raw 振幅归一化由 `raw_reference_normalization_mode` 与 `raw_scattering_normalization_mode` 分别显式决定，必须落字段。**

**判决规则(写进 lane): 只在同一 (ref_norm, sca_norm) 组合内比 ranking；跨 norm 的差是
diagnostic，不是 final ranking 证据。** 推荐主锚: sca 用 `per_case_au20_sca_baseline`(与现有 gauge 一致),
ref 用 `rho_g_reference_amplitude`(= 现有 A_ref=ρ·g 口径); 另跑 sca `global_fixed_660_au20_sca_baseline`
作跨波长可比对照。**(#4: 不要用 Au20 *scattering* baseline 去归一化 *reference* 场。)**

### 1.4 R1/R2 读出策略(不是 detector identity)

每条 route 的 signed trace 走现有读出链，在峰提取的极性策略上分叉:

```python
from nodi_simulator.parameter_sweep import add_detector_noise, apply_readout_chain
from nodi_simulator.pulse_analysis import extract_pulse_features

def run_route_readout(signal_route_signed, time_s, sim_cfg, rng, *, readout_policy,
                      I_det=None, I_baseline=None):
    # 【M3 修正】shot-noise surrogate 需要 detected_intensity/baseline_intensity;
    #   生产在 simulate_one_event:4099-4100 传入。route lane 必须同样传, 否则 shot 项
    #   退化为 max(signal,0)(parameter_sweep.py:1145), D 路(EV cross 负)会被错误清零。
    noisy = add_detector_noise(signal_route_signed, time_s, sim_cfg, rng,
                               detected_intensity=I_det, baseline_intensity=I_baseline)
    readout = apply_readout_chain(noisy["signal_noisy"], time_s, sim_cfg, ...)
    sig = readout["signal_detect"]
    detection_mode = "positive" if readout_policy == "R1" else "absolute"
    # 【#10】不要自写 background_segment(): 复用生产同一阈值/背景路径
    #   (_threshold_background_segments / _estimate_runtime_threshold_stats_1d, parameter_sweep.py),
    #   或把它抽成 shared public threshold helper; 否则 route lane 与 production lane 阈值口径会漂移。
    thr = production_threshold(sig, sim_cfg)   # = simulate_one_event 用的同一 helper
    return extract_pulse_features(time_s, sig, thr, sim_cfg.min_peak_width_s,
                                  sim_cfg.min_peak_interval_s, detection_mode=detection_mode)
```

**【M2 重大修正 — R1/R2 的极性语义依赖 readout_model】** "signed-positive 漏检负脉冲"只在
**`readout_model="raw"` + `readout_observable_mode="in_phase"`** 下成立。生产用的
`lockin_surrogate` 把 `signal_detect=signal_nodi` 做了 lowpass+demod 变换
(parameter_sweep.py:2144–2194)，并非保号恒等；`magnitude` 观测模式更是已取 `|raw|`(:2087)。
故纯负输入经读出后可能已变号/整流，R1 不再"干净地漏检"。**因此 R1/R2 的极性对照必须在
`raw + in_phase` 读出下做**(才是真正 signed-vs-absolute 的对照)；若要测生产 lockin 链下的极性后果，
另设一条 lane 并显式标注"R1/R2 语义随 readout_model 改变"。不要把两者混为一谈。

- **R1 signed-positive**(仅 raw+in_phase): `detection_mode="positive"`。
- **R2 absolute-peak**: `detection_mode="absolute"`(当前 `pulse_detection_mode` 默认)。

D 路必须 R1+R2 都跑(raw+in_phase 下 EV 负 cross → signed 漏检、abs 可检)，输出
`signed_cross_route_score` 与 `absolute_cross_route_detection_score`。

### 1.5 网格规格与参数选择

| 轴 | 取值 | 说明 |
|---|---|---|
| detector model | A_hybrid / B_roi_intensity / C_collapsed_coherent / D_cross_only | T1.2 |
| readout policy | R1_signed_positive / R2_absolute | T1.4 |
| gauge mode | V1_gauge_locked / V2_raw_angular | T1.3 |
| angular norm (V2, **ref/sca 分开命名 #4**) | sca: `per_case_au20_sca_baseline`(主)/`global_fixed_660_au20_sca_baseline`/`unit_sca`; ref: `rho_g_reference_amplitude`/`sqrt_I_ref_roi`/`unit_reference`/`calibrated_reference_lookup` | T1.3 |
| wavelength | 404, 660 (+488/532 control) | 聚焦 headline 争议 |
| width | 404: {500,600,700}; 660: {700,800} | report 147 §9 family |
| depth | {900, 1100, 1300, 1500} | 中深 vs raw-top 对照 |
| EV prior | sharp_msc_sev(主) + uniform/broad(对照) | 与 report 140 一致 |
| EV 粒子 | **Stage 1: representative subset**(如 2 preset × 3 尺寸 ≈ 6); **Stage 2/T4: full RI grid 144** | 主网格用 subset, 不是 144(#8) |
| gold anchor | Au20/40/60 = **+3 anchor 行(不是粒子轴, 不与 EV 做笛卡尔积; 归一化/anchor 用)** | #7 |
| normalization view | fixed_660_gold / per_wavelength_gold | 复现 report 140 的 view-flip |
| seed | 11/22/33 | 3-seed |
| events/case | **2000**(screening; 非 10000 全量) | 见计算量 / #10 |
| reference_model | **必须 ∈ {channel_angular_surrogate, paper_aligned_phase_filter}** | 否则无角谱场→`self_sca`=None→B/D 路 gate False(m2) |

历史 T1 设计中的事件预算选 2000 而非 10000(**#10 修正, 措辞收紧**): 2000e 是**经济的 screening
预算**, 用于初筛。若未来重新激活该 route-grid handoff, rank margin 小或出现 route-dependent flip 的 case
应提升到 10000e 再下该未来任务的局部结论；这不是当前 no-data closure 的封板门。
不写"2000e 已足以分辨 family 翻转"。

### 1.6 输出字段(每 case × route × readout × gauge 一行)

```
detector_route_id, readout_policy, gauge_mode,
normalization_view,                       # V1 的分组键(fixed_660_gold / per_wavelength_gold)
# 【#5】不再用 singular angular_field_normalization_mode; V2 用下面 ref/sca 分开的两个 mode。
# angular_field_normalization_mode_deprecated,  # 标 deprecated, 禁止后处理按单一 norm 分组
r_self, self_collapsed_detector, self_roi_detector,
total_signed_signal_selected, total_abs_signal_selected,
detection_rate, stable_detection_rate, *_wilson_lb, mean_peak_margin_z,
A_vs_B_abs_signal_ratio_static, A_vs_C_abs_signal_ratio_static, B_vs_C_signal_ratio,
selected_annulus_rank, detector_route_rank_stability_class,
detector_route_flip_flag_404_660,
signed_cross_route_score, absolute_cross_route_detection_score,   # D 路
# 【#10】noise policy / route baseline(与 T3 一致, 否则结果表无法审是 common 还是 route-consistent):
noise_policy,                # route_consistent_shot_noise / common_noise_control
I_baseline_route, I_det_route, shot_noise_intensity_route,
route_baseline_model, route_noise_consistency_status,
# V2 raw norm provenance(与 T1.3 一致):
raw_reference_normalization_mode, raw_scattering_normalization_mode, n_ref_raw, n_sca_raw
```

### 1.7 判决规则(决定 report 140 headline 命运)

```
# 【#5】分组键: V1 只按 normalization_view 比; V2 按 (raw_reference_normalization_mode,
#   raw_scattering_normalization_mode, normalization_view) 比。不要跨分组键比 ranking。
若 (A,B[,D]) 在 R2 + V1(按 view) 与 V2(按 ref/sca norm × view) 下:
    404↔660 view-flip 保持 ∧ selected family 不变
  → P1-detector 降为 documented surrogate gap; 404/660 caveat 维持现状。
否则(view-flip 改变 或 self/cross 主导翻转):
  → report 140 的 404-vs-660 撤回为 "candidate families under current
     collapse-gauge-locked hybrid-detector surrogate"; detector identity 列为头号待标定项。
```

**实现后补记(Report 148 stage1 follow-up):** 当前 frozen-B / `median+5·MAD` 自校准阈值口径下,
若 V1↔V2 主要只是整体 amplitude scale / raw norm 重钉, 则其 detectability effect 往往会被阈值与
工作点归一共同吸收; **但在带绝对电子噪声的 as-run 配置下, 这种吸收只是部分的, 不是严格 scale-invariant。**
即便如此, gauge(V1/V2) 仍不应再当成 headline 主判据。后续 T1 的主判决顺序应改为:
1. 先看 `A/B/C/D` 的 cross/self 时域 shape 是否改变 winner family / view-flip；
2. 再看 `V1/V2` 是否在同一 shape-route 下提供额外敏感性。
换言之, detector-identity 对 report 140/147 headline 的风险, **优先来自 shape route(A/B/C/D), 不是 gauge 本身。**

### 1.8 计算量估计

粒子轴(**#7 修正**): 每个几何/λ 下 particle 行 = **N_EV_subset + N_gold_anchors**(加法, **不是** EV×gold
笛卡尔积; gold 是 anchor 不是粒子轴)。Stage 1: 约 6 EV subset + 3 gold = 9 行; Stage 2/T4: 144 EV + 3 gold。
总规模 = model(A/B/C/D) × readout(R1/R2) × gauge(V1/V2) × λ(4) × width(≈2.5) × depth(4) × EV-prior(3)
× (N_EV+N_gold) × view(2) × seed(3) × 2000e。

**减负策略**: D 路只需 R1+R2; **C 路在 V2 下 optional/diagnostic**(#13: T1.3 已定义 V2 的
`collapsed_ref_raw`/`collapsed_sca_raw`, 故 raw-angular C **可定义**, 只是 cost 上可省略 ——
要省就明说"为省成本略去", **不要写"raw-angular 无意义"**)。
先跑 **Stage 1 主网格 (A,B) × R2 × V1_gauge_locked(angular_norm=N/A) × view∈{fixed_660,per_wavelength}**
(#12: per_case_au20 是 V2 的 angular norm, V1 不用它; 此处的归一化区分用 normalization view)定调,
再按需展开 V2(带 ref/sca norm)/R1/D。**主网格 ≈ 2 model × 1 readout × 1 gauge × 2 view,
事件总量约为一次 3-seed 2000e 全网格的 ~4 倍。**

---

## 2. T2 — Heterodyne gauge 轴(P1)

**closure 状态:** `handoff_not_blocking_no_data_final`。Gauge 轴已在 no-data claim 中降级为
candidate-family 边界；A/B `V2_raw_angular` 仅作为抽样 gauge 检验。任何 calibrated heterodyne /
跨波长绝对强弱 claim 均转入标准粒子 ladder 实测交接。

**问题**: 干涉工作点由 `(Au20 baseline E_sca_ref, ρ)` 两未标定常数 gauge-fix(report 147 §6)。
`|E_sca|/|E_ref| = (E_sca_at_det/E_sca_ref)/(ρ·g)` 决定 cross vs self 相对强度。

**做法**: 把 `ρ`(`sim_cfg.rho`) 升为显式轴，扫**目标工作点**(**#5: median-of-ratios 口径, 别写回 median(a)/median(g)**):
`target_ratio ≡ median_i(|E_sca_i| / (ρ·g_ref_i))`，故 `ρ = median_i(|E_sca_i| / g_ref_i) / target_ratio`:

| gauge_ratio 档 | 含义 |
|---|---|
| 0.01 | 强参考/heterodyne-dominant |
| 0.1 | 中间 |
| 1.0 | self/cross 同量级(对照) |

**【关键修正 #1 — ρ 只能 per-scenario 解一次, 绝不能 per-case 反解】** 若对每个 particle/geometry
单独反解 ρ 使其 ratio=target, 等于把所有 case 强行钉到同一 |E_sca|/A_ref 工作点，**人为抹掉散射强弱
差异、毁掉 ranking**。正确做法: 对一个 scenario(固定 λ/几何家族/view), 用一个**锚 population**
(EV median 或 Au anchor median)解出**一个** ρ, 然后该 ρ 应用于该 scenario 下**所有** cases。

```python
from dataclasses import replace
import numpy as np

def get_E_sca_normalized(row):   # 列名因来源而异(#3); 【#4】带 finite guard, 非有限返回 None
    for k in ("E_sca_unit_normalized", "E_sca_normalized", "E_sca_unit_normalized_complex"):
        if k in row and row[k] not in (None, ""):
            try:
                out = abs(complex(row[k]))
            except (TypeError, ValueError):
                continue
            return out if np.isfinite(out) else None
    return None   # 缺列/非有限: 由调用方过滤, 不直接 raise(对脏行更鲁棒)

_RHO_CONTROLS = {"constant","geometry_scaled","channel_angular_surrogate",
                 "paper_aligned_phase_filter","tsuyama_bfp_integrated"}      # rho 控 A_ref
_RHO_NOT_CONTROLS = {"calibrated_lookup","calibrated_A_ref_lookup"}          # rho 不控

def infer_rho_controls_A_ref(row):   # 【#3】真正实现"字段缺则按 reference_model 推断"
    v = row.get("rho_used_for_reference_amplitude")
    if v is True:  return True, "from_field"
    if v is False: return False, "from_field"
    rm = row.get("reference_model") or row.get("reference_amplitude_source")
    if rm in _RHO_CONTROLS:     return True,  "inferred_from_reference_model"
    if rm in _RHO_NOT_CONTROLS: return False, "inferred_from_reference_model"
    return None, "unknown"   # 无法推断 → 计入 unknown_rho_control_fraction

def solve_rho_for_scenario(anchor_rows, target_ratio, *, anchor_filter="ev_median"):
    """Solve ONE rho per scenario from an anchor population (NOT per-case)."""
    # 【#9/#3】rho 是否控 A_ref: 字段优先, 缺则按 reference_model 推断; 显式 False=真 calibrated route。
    flags = [infer_rho_controls_A_ref(r) for r in anchor_rows]
    controls = [f for f, _ in flags]
    stats = {
        "missing_rho_control_field_fraction": float(np.mean(["rho_used_for_reference_amplitude" not in r for r in anchor_rows])),
        "unknown_rho_control_fraction": float(np.mean([c is None for c in controls])),
        "rho_control_inference_source": ("from_field" if all(s == "from_field" for _, s in flags) else "backfilled_or_inferred"),
    }
    if any(c is False for c in controls):   # 任一确定为 calibrated_A_ref_route → gauge 不适用
        return None, {"gauge_axis_applicable": False, "reason": "calibrated_A_ref_route", **stats}
    # 【M5】na_cutoff hard-zero / 弱参考 g≈0 的行剔除(A_ref=rho*g=0 与 rho 无关 → gauge no-op;
    #   cutoff 示例 660nm/700nm = 660 headline 家族, reference_field.py:1609-1612/1632-1634)
    # 【#4】同时剔除 g 非有限 / E_sca 非有限的脏行
    def _ok(r):
        g = r.get("g_ref"); a = get_E_sca_normalized(r)
        return (g is not None and np.isfinite(float(g)) and float(g) > 1e-9 and a is not None)
    kept = [r for r in anchor_rows if _ok(r)]
    stats["skipped_anchor_fraction"] = float(1.0 - len(kept) / max(len(anchor_rows), 1))
    if not kept:
        return None, {"gauge_axis_applicable": False, "reason": "all_anchor_g_ref~0_or_nonfinite", **stats}
    ratios = [get_E_sca_normalized(r) / float(r["g_ref"]) for r in kept]
    # 【#2】解 median(|E_sca|/(rho*g)) = target_ratio  ⇒  rho = median(|E_sca|/g)/target_ratio
    #   (不是 median(a)/median(g): 当 E_sca 与 g 随 λ/几何 共变时, 后者会偏)
    rho_new = float(np.median(ratios)) / target_ratio
    return rho_new, {"gauge_axis_applicable": True, **stats}

def apply_rho_to_scenario(base_cfg, rho_new):       # 同一 rho 应用于 scenario 内全部 case
    return replace(base_cfg, rho=rho_new)
```

**【#2 — rho_scope 边界, 防止污染 W/D ranking】** 若本轮要比较 width/depth ranking, **rho_scope 绝不能细到
exact candidate W/D**(否则每个几何各自重解 rho、重新钉住 reference 工作点, 削弱甚至破坏几何 ranking):
- **允许 scope(用于 geometry ranking)**: `wavelength × reference_model × normalization_view × anchor_population`;
- **diagnostic-only scope**: 固定一个 representative geometry;
- **禁止用于 geometry ranking**: per-exact-candidate-geometry rho solving。

**输出**: `gauge_ratio`, `rho_used`, **`rho_scope`(=wavelength×reference_model×view×anchor, **不含 exact W/D**),
`rho_anchor_population`(ev_median/au_median), `rho_anchor_filter`, `rho_solved_once_per_scenario=True`,
`reference_amplitude_source`, `rho_controls_A_ref`, `gauge_axis_applicable`, `gauge_solvable`,
`missing_rho_control_field_fraction`, `skipped_anchor_fraction`, `rho_control_inference_source`**, 以及每档下的 selected family。
`rho_controls_A_ref=False`(如 calibrated_lookup) → 标 `gauge_axis_not_applicable_for_calibrated_A_ref_route`。
**判决**: 若 family 随 gauge_ratio 翻转 → 报告所有"NODI 外差增强倍数"措辞必须带 gauge 注脚(已在 147 §9)。
**计算量**: 3 档 × 主网格子集(404/660 × 代表几何 × sharp prior × seed11) ≈ 小。

---

## 3. T3 — Noise-regime 轴(P1)

**closure 状态:** `completed_for_no_data_claim`。T3 已完成独立审查收口:
selected-annulus 深度排序主要落在 sampling-noise floor；all-crossing 与 selected-annulus 双口径并立。
blank-FPR / calibrated noise 仍属实测桶 A。

**问题**: `shot_noise_scale` 是自由旋钮，as-run 0.001(electronics-limited)。report 146 已证 depth 收益随它收缩。

**做法**: 升为正式 scenario 轴(已有 `tmp/depth_evidence_artifact.py` 雏形，固化进 lane):

| shot_noise_scale | regime | 期望 |
|---|---|---|
| 0.001 | electronics_limited(as-run) | depth-span 大 |
| 0.05 | intermediate | depth-span 收缩 |
| 0.2 | shot-dominant | band→shot_noise_limited_no_gain |

```python
for s in (0.001, 0.05, 0.2):
    cfg_s = replace(base_cfg, shot_noise_scale=s)
    run_case(..., cfg_s)   # 输出 depth-span, operating_band, selected depth rank
```

**输出**: `shot_noise_scale`, `depth_span_404`, `depth_span_660`, `operating_band`,
`selected_depth_rank_by_regime`。

**【#3 修正 — T1×T3 合并必须显式声明 noise policy, 不能静默沿用 A 的 baseline】** shot-noise surrogate 需要
`detected_intensity`/`baseline_intensity`(见 M3)。若把 T3 与 T1 多 route 合并并号称"detector-route-consistent
noise scan", 则每条 route 应有**自己的** `I_baseline_route`/`I_det_route`/`shot_noise_intensity_route`
(如 B 路用 ROI reference intensity baseline, 而非 production A 的 collapsed baseline)。否则只能设
`common_noise_control=True`(所有 route 故意共用同一 noise baseline, 只比 signal route)。**两者必须二选一并落字段**
`noise_policy ∈ {route_consistent_shot_noise, common_noise_control}` —— **不许默认沿用 A baseline 却解释成
route-consistent**。
**判决**: depth 结论必须以**区间**报告(D900–D1200 推荐 + "depth 收益 X–Y%, 随噪声口径变化")。
**计算量**: 3 档 × 主网格子集 ≈ 小。**可与 T1g 合并成一个统一扫描**(T1×T2×T3 共用 case 循环, 但须固定 noise_policy)。

---

## 4. T4 — EV RI / core-shell / corona 不确定度传播(P1)

**closure 状态:** `completed_for_no_data_claim`。T4 已用现有 artifact 与 focused Wilson 支撑收口:
7 个 bright-EV combo 全部 Wilson 区间重叠；4 个为点估计 3-seed 一致 404 但非区间分离，
3 个为 genuine near-tie。EV 物理 composition prior 仍属实测桶 A。

**问题**: uniform EV 固定 1.38; structured presets 存在但未把不确定度传到 ranking。

**结构参数**(来自 `structured_particles.EXOSOME_MODEL_PRESETS`):
`core_n_real`, `membrane_n_real`, `corona_n_real`, `membrane_thickness_m`, `corona_thickness_m`,
`edl_refractive_increment`。

**敏感性网格**(**#5 修正: 这是 fractional screening grid, 不是完整正交网格**; 下表与 skeleton 已对齐):

| 参数 | 档位 | 说明 |
|---|---|---|
| preset | membrane_only_dim_2021 / membrane_only_nominal_2020 / biomimetic_corona_nominal / surface_loaded_bright_2021 | 4 个 preset, skeleton 已全含 |
| core_n_real | 1.36 / 1.38 / 1.40 | 显式 override 轴 |
| corona | absent(0nm) / nominal(4nm) / protein_rich(8nm + corona_n_real↑ + EDL↑) | 显式厚度(M4) |
| 代表尺寸 | 40 / 70 / 100 / 150 nm | 覆盖 sEV 主峰 |

注: **`membrane_n_real` 不作独立正交轴** —— 它已由 preset 编码(各 preset 的膜 RI 不同: 1.45/1.46/1.52,
structured_particles.py:69/84/118)。若要单独扫膜 RI, 再加一条 override 轴并重算粒子数; 当前 screening
不展开它。粒子数 = 4 preset × 3 core × 3 corona × 4 size = **144**(非"≈12")。

```python
from nodi_simulator.structured_particles import make_biomimetic_exosome_particle  # 见 :355
# 签名: make_biomimetic_exosome_particle(diameter_nm, *, name=None,
#                                        preset_name="biomimetic_corona_nominal", overrides=None)
# overrides 的键覆盖 preset: core_n_real / membrane_n_real / corona_n_real /
#                            membrane_thickness_m / corona_thickness_m / edl_refractive_increment
#
# 【C1 修正】build_biomimetic_exosome_core_shell 对 overrides 做 params.update() 后立即
#   float(params["corona_thickness_m"])（structured_particles.py:251,258）——传 None 会抛 TypeError。
#   "保留 preset" 的唯一正确写法是 *省略该键*，不能传 None。
# 【M4 修正】membrane_only_nominal_2020 / surface_loaded_bright_2021 的 preset corona=0nm，
#   只有 biomimetic_corona_nominal=4nm。若只靠 preset，"absent" 与 "nominal" 对前两个 preset 相同 →
#   corona 轴半失效。故 corona 轴必须 *显式置厚度*，不依赖 preset。
CORONA_THICKNESS_M = {"absent": 0.0, "nominal": 4e-9, "protein_rich": 8e-9}
PRESETS = ("membrane_only_dim_2021","membrane_only_nominal_2020",
           "biomimetic_corona_nominal","surface_loaded_bright_2021")   # 4 个, 与表对齐
def ev_ri_grid():
    for preset in PRESETS:
        for core_n in (1.36, 1.38, 1.40):
            for corona in ("absent","nominal","protein_rich"):
                for d_nm in (40, 70, 100, 150):
                    ov = {"core_n_real": core_n,
                          "corona_thickness_m": CORONA_THICKNESS_M[corona]}   # 显式, 永不 None
                    if corona == "protein_rich":
                        # 【#7】protein_rich 是 combined stress preset(同时改 corona 厚度+RI+EDL),
                        #   不是正交物理轴: 若 ranking 翻转, 无法归因到厚度/RI/EDL 哪个。
                        #   要 attribution 另加消融: thick_corona_only / high_corona_RI_only /
                        #   EDL_plus_only / combined。
                        ov["corona_n_real"] = 1.40
                        ov["edl_refractive_increment"] = 0.005
                    yield make_biomimetic_exosome_particle(d_nm, preset_name=preset, overrides=ov)
```

**【#6 — nominal ≠ resolved 厚度, 必须落两套】** `build_biomimetic_exosome_core_shell` 在
`surface_total > radius·(1−min_core_radius_fraction)` 时**等比缩放 membrane/corona/EDL**
(structured_particles.py:262-270): 对小 EV(如 40nm)+厚膜 preset+8nm corona, **nominal 8nm ≠ resolved**。
故每粒子从 spec(=`resolve_structured_particle_spec`)落:
`corona_thickness_nominal_m`(=override 输入) **与** `corona_thickness_resolved_m`(=spec["corona_thickness_m"]),
以及 `membrane_thickness_resolved_m`/`edl_thickness_resolved_m`/`core_radius_fraction_resolved`(=spec 内)、
`surface_layer_scale_factor`(=resolved/ nominal surface_total)、`surface_layer_clipped_flag`(=scale<1)。
**否则解释"protein_rich 8nm corona"会把 nominal input 当成 actual resolved shell。**

**输出**: 每个 RI 组合下的 selected width/λ/depth family + `ev_ranking_stability_class` + 上述 resolved 厚度字段。
**判决**: 若 top family 在 RI 网格内稳定 → 可写"EV-prior-robust"; 否则只写"under specified EV preset/prior"。
**计算量**: 4 preset ×3 core ×3 corona ×4 size = **144 粒子** × 代表几何(404/660 × 2 width × 2 depth) × seed11
× 2000e ≈ 小-中。先只跑 V1/R2/A 主 route。

**实现后补记(Report 148 收尾):**
- 最小 panel 的 A-vs-C EV-RI 初筛显示: `29/36` 组合保持 Stage-1 headline, `7/36` 组合会动 winner/flip；
- 这 `7/36` 组合全部落在 `surface_loaded_bright_2021`, 其余 preset 未见 headline 漂移；
- 对这 `7` 个 brightest-EV 组合做 focused `10000e × 3-seed` 后, A 路分成两类:
  `4` 个 **点估计 3-seed 一致的 404 winner**(但 404/660 Wilson 区间仍重叠, 不升级为区间分离
  deterministic), `3` 个 **genuine near-tie**(10000e 仍 seed-不稳, 404/660 Wilson 区间重叠)；
- 同一 `7` 组合上, C 路全部保持 **deterministic 660**。
因此 T4 的最终机制应写成: **EV-RI 对 headline 的影响主要来自 brightest EV preset 的近平局 / seed 脆弱性；
不是所有 RI 组合都会系统性换 winner。** 同时 `A↔C` 的分歧对 RI **不稳健**:
`22/36` 组合始终分歧, `13/36` 组合只在部分 seed 分歧, `1/36` 组合始终一致。
这意味着后续 headline 判读必须把 `detector identity × EV composition` 联合看待, 不能单看任一轴。

**T3 / noise-regime 补记(第三轴):**
- baseline EV composition 下, `0.001` baseline 已补齐为 **3-seed**；
  `shot_noise_scale=0.001 / 0.05` 仍保持 Stage-1 headline
  (`fixed_660→404`, `per_wavelength→660`)；
- `shot_noise_scale=0.2` 时, `fixed_660_gold` 只出现 **2/3 seed 翻到 660、1 seed 仍 404**，
  `per_wavelength_gold` 则是 **3/3 seed 全 660** ——  
  说明 **noise regime 也会动跨波长 headline**, 但表现为 strong-shot 下的 seed-fragile shift,
  不是干净单调翻转。
- depth 口径必须显式分两面, 且 selected-annulus 的旧归因要纠正:
  - **all-crossing** depth-span 随 shot↑显著收缩(与 report 146 一致), 且 depth-top
    的 seed 稳定率分档为 `0.001→10/10`, `0.05→8/10`, `0.2→8/10`（合计 **26/30**）；
  - **selected-annulus** 推荐面一开始就没有可复现的 depth 排序, width-family 内 depth-top
    的 seed 稳定率分档为 `0.001→1/10`, `0.05→1/10`, `0.2→3/10`（合计 **5/30**）；
    其 depth-span 中位数约 `0.017–0.050`, 与 `N=2000`、`p≈0.5–0.7` 的 sampling-noise floor
    同量级。高 shot 下看见的 `4–8%` 不是“被噪声再分叉出来的深度效应”, 更准确地说是
    **p→0.5 时噪声底变大**。`0.001` baseline 自身就已给出同样信号(`selected 1/10` vs
    `all-crossing 10/10`), 说明 selected-annulus 深度不稳是内禀口径特征, 不是 noise-induced 排序翻转。
因此 T3 的最终表述应是: **noise regime 是第三条独立脆弱轴；它不仅动 depth, 在强 shot 下也会让
404-vs-660 headline 向 660 侧漂。** 但这个 effect 依然停留在 detector-surrogate /
candidate-family 层级, 不是任何 detector-resolved winner。所有算量同时保留
`case-row events` 与 `distinct physical events` 两种口径, 后者约为前者一半(双 view 共用物理事件流)。

---

## 5. T5 — Provenance / runtime-config trace(P1, 零重跑可补 schema)

**closure 状态:** `handoff_not_blocking_no_data_final`。Stage-1 preseal evidence package 已给出本轮所需
manifest / coverage / event-accounting provenance；更宽 provenance schema 仍可零重跑补强，但不阻断
no-data 定稿。

**问题**: seed `run_manifest.json` 的 `runtime_config_subset` 与 `design_postprocess.csv`(48列)缺
关键 config; diagnostic_rows 的 `reference_model` 列为空。

**做法**: 在 runner 写 manifest 处(tools/lens_b_ev_gold_fullgrid_runner.py:379 `runtime_config_subset`)
强制补全。**【#6 修正 — NameError】** 当前 `_write_manifest(*, output_dir, args, scope, cfg, run_kind)`
**没有 `optical_template` 形参**(:309-316), 且 `NA_collection` 在 OpticalSystem 上、不在 `cfg` 上。
故必须**给 `_write_manifest` 加 `optical_template=None` 形参**(并在调用处传入), 且用安全读取兜底:

```python
# _write_manifest 签名补: def _write_manifest(*, ..., cfg, run_kind, optical_template=None)
NA_collection = getattr(optical_template, "NA_collection", getattr(cfg, "NA_collection", None))
runtime_config_subset = {
    **existing,
    "reference_model": cfg.reference_model,
    "reference_route": cfg.reference_route,
    "reference_na_edge_policy": cfg.reference_na_edge_policy,
    "NA_collection": NA_collection,
    "noise_std": cfg.noise_std,
    "shot_noise_scale": cfg.shot_noise_scale,
    "post_readout_noise_std": cfg.post_readout_noise_std,
    "field_coordinate_measure": cfg.field_coordinate_measure,
    "bfp_to_angle_jacobian_applied": cfg.bfp_to_angle_jacobian_applied,
    "interference_overlap_mode": cfg.interference_overlap_mode,
    "interference_overlap_status": "<from reference>",
    "scattering_projection_mode": cfg.scattering_projection_mode,
    "rho": cfg.rho, "threshold_sigma": cfg.threshold_sigma,
    "normalization_view": args.normalization_lane,
    # 【#14】给既有 run 回填字段时, 必须标注来源, 不能伪装成原始 runtime 记录:
    "config_trace_status": "backfilled",                         # vs original_runtime_record
    "backfilled_at": "<iso8601>",
    # 【#7】单个全局 origin 不够: 一份 manifest 里字段来源不同(runtime/cfg/code default/runner args)。
    #   用 per-field origin map(或 companion CSV: field,value,origin,source,confidence):
    "manifest_field_origins": {        # field -> origin
        "reference_model": "cfg",      "NA_collection": "optical_template",
        "rho": "cfg",                  "normalization_view": "runner_args",
        # ...逐字段: original_runtime_record / cfg / code_default / runner_args / reconstructed_from_code
    },
}
```

**【#14 关键】** 对**新 run** 这些字段是 `original_runtime_record`; 对**回填既有 manifest** 必须标
`config_trace_status=backfilled` + **per-field** `manifest_field_origins`(逐字段来源)/`backfilled_at`,
**绝不能让回填出的 manifest 被误读成原始 runtime 直接记录**。
同时给每个 result CSV 增写 `*_audit_minimal_config_trace.csv`(route/view/seed 各一行 + hash + origin)。
**判决/测试**(T9): `assert reference_model in run_manifest` 且回填行 `config_trace_status=="backfilled"`。**零重跑**(只补 manifest/导出)。

---

## 6. T6 — 派生表符号修复(P2, 零重跑)

**closure 状态:** `handoff_not_blocking_no_data_final`。report 147 已按 raw signed 口径修正机制叙述；
旧派生表符号修复仍是可追溯性清理项，但不阻断 no-data 定稿。

**问题**: `mechanism_chain_by_wavelength_EV_medians.csv` 把 signed cross 报成 magnitude(丢符号)，
已实际误导 reviewer(把相消误读成相长)。**生成器当前未在 `tools/` 中找到**(grep `mechanism_chain`
仅命中本路线图的 recompute 脚本; 该表可能由一次性/未跟踪脚本产出)。**第一步必须先定位或重建生成器**
(候选: 产出 report-47 分析目录的 lane, 如 `tools/audits/tsuyama_gold_aligned_detection_lane.py`，
需实跑核对其是否写该表); 若无法定位, 直接用
`tools/audits/recompute_report147_detector_identity_tables.py` 的 signed/abs 输出替代该派生表。

**做法**: 在(重建的)生成处，把单列 `median_cross_term_detector_integrated` 拆成显式三组:

```python
out["median_signed_cross_term_detector_integrated"] = float(np.median(cross_signed))
out["median_abs_cross_term_detector_integrated"]    = float(np.median(np.abs(cross_signed)))
# 【#6】tolerance-based near-zero(== 0 精确比较对长期生成器不稳); 同一 eps 给 T9 sign audit 复用
# 【#8】先剔除 NaN/Inf, 空数组直接 raise(避免 median 出 NaN/warning)
cross_signed = np.asarray(cross_signed, dtype=float)
cross_signed = cross_signed[np.isfinite(cross_signed)]
if cross_signed.size == 0:
    raise ValueError("no finite cross_term values for sign audit")
eps = max(1e-15, 1e-12 * float(np.median(np.abs(cross_signed))))
out["cross_term_zero_tolerance"]      = eps
out["cross_term_negative_fraction"]   = float(np.mean(cross_signed < -eps))
out["cross_term_near_zero_fraction"]  = float(np.mean(np.abs(cross_signed) <= eps))
out["cross_term_positive_fraction"]   = float(np.mean(cross_signed >  eps))
# 弃用原歧义列, 或保留并改名 *_magnitude 并标 deprecated
```

**测试**(T9, **#11 加过滤条件**): 仅在
`family=="ev" ∧ wavelength_nm==404 ∧ lineage=="v1_channel_angular_surrogate" ∧ phase_convention=="current_uncalibrated"`
下 `assert cross_term_negative_fraction == 1.0`(对 gold / Lens-B aggregate / 未来 phase convention 不适用)。**零重跑**。

---

## 7. T7 — 清理/补推导项(P2/P3)

**closure 状态:** `completed_under_no_data_scope`。

- **theta_phase 推导(P3, 并入 T1 sensitivity)**: 当前 `exp(i(θ-θc)sinφ)` 无量纲启发式。
  在 B integrand 内抵消(report 147 §3.2)，只经 A/C collapsed amplitude 与 gauge rescale 影响。
  2026-06-12 已在源码注释与 report 147 残余假设台账登记为
  `heuristic_unitless_aperture_phase`：唯象 aperture phase surrogate，未经第一性推导验证。
  做法: (a) 给推导(若意在某 BFP 离焦相位，应为 `k·Δz·(1-cosθ)` 形式) 或 (b) 标
  `theta_phase_model="heuristic_unitless_aperture_phase"` 并作为 T1 的一个 on/off sensitivity 开关。
- **`k_m_inv` 清理(P3)**: 2026-06-12 已收敛为 `k_m` canonical；`k_m_inv` 仅保留为
  deprecated legacy exact alias（非 1/k），下游新增路径统一读 `k_m`，回归测试断言两者数值完全一致。
- **external-bundle 验证模式(P2 交付)**: 2026-06-12 已给 `review_package.verify_*` / CLI 增加
  `--external-bundle-mode`，用于跳过本地 git commit 可达性绑定；严格 hash/package 结构检查仍保留。

---

## 8. T8 — A_vs_B 静态量化(P1 量化缺口; v1 summary 真·零重跑, Lens-B emit deferred)

**closure 状态:** `handoff_not_blocking_no_data_final`。A_vs_B 静态量化仍是有价值的后续解释补强；
Stage-1 no-data 主判决已经由 A/B/C/D route family consensus 与 C 的独异性完成，不再要求先执行 T8。

**问题**: 现有强证据是 B/C(`roi_vs_scalar_signal_ratio`)，缺 production A vs 自洽 B。

**【修正 — v1 summary 其实零重跑可算; 上一版的"必须 emit"是因为搜错列名】** 实测确认 **v1 summary
带 `E_sca_normalized` 列(col 615)**，它就是 `|E_sca_unit_normalized|` 的别名 → `self_collapsed=E_sca_normalized²`。
4 行核对: `self_sca_detector_integrated / E_sca_normalized² = 4.9556` 对 `roi_vs_scalar_signal_ratio=4.9577`
(逐行 4 位有效吻合)，证明 `E_sca_normalized²=self_collapsed`。**所以 v1 summary 的 A/B、A/C static
全部零重跑可算。** 我和 subagent 上一版都搜了 `E_sca_unit_normalized` 而漏了真实列名 `E_sca_normalized`——
这是检索口径错误，已纠正。**唯一仍需 emit 的是 Lens-B `diagnostic_rows`(实测无 `E_sca_normalized` 列)**:
那一侧的 A/B 需一次 case-level emit(无事件循环, 成本极低)。

**做法(v1 summary, 零重跑)**: 后处理已有列:

```python
self_collapsed = row["E_sca_normalized"] ** 2           # = |E_sca_unit_normalized|² (v1 summary 已存)
cross_joint    = row["cross_term_detector_integrated"]  # 已有
A_static = self_collapsed + cross_joint                 # = C 的 self + A/B 共用 cross
B_static = row["signal_detector_integrated"]            # B 已直接存(= self_roi + cross_joint)
abs_C = abs(B_static) / max(row["roi_vs_scalar_signal_ratio"], 1e-30)  # |C|=|B|/ (B/C)
# 【#9】只能恢复 absolute magnitude ratio(|C|=|B|/roi 丢了符号); 名字必须标 abs/static,
#   不能判 A/C polarity。要 signed relation 必须另 emit signed C, 不能从 |B|/|C| 反推。
row["A_vs_B_abs_signal_ratio_static"] = abs(A_static) / max(abs(B_static), 1e-30)
row["A_vs_C_abs_signal_ratio_static"] = abs(A_static) / max(abs_C, 1e-30)
```

Lens-B 侧前置: emit `self_collapsed_detector = |E_sca_unit_normalized|²`(或直接补 `E_sca_normalized` 列)。
**这是把"production 偏离自洽 B 多大"从未知变成可量化的最快一步**，v1 侧应在 T1 之前立即做。
**判决**(m4 修正: 注意基线不是 1): 对 self-dominated 的 gold，因 `A` 用 collapsed self、`B` 用 ROI self，
而 `roi_vs_scalar(=B/C)≈5`，故 `A_vs_B` 的 self-主导基线本就 ≈1/5 而非 1。判据应按 family 分别定阈
(gold 看是否偏离其自身 self-主导基线 ≈1/5; EV cross-竞争看是否偏离~1)。
**(#9 修正)** 若各 family 内 `A_vs_B` 稳定贴近其预期基线 **且 route ranking 不变** →
A/B 差异是 **systematic scaling gap, 不是 rank-changing gap**；T1 优先级可降为"仅做 route-rank 确认"。
**但当 baseline gap ≈1/5 时, 不能把 production hybrid 描述成"与 B 接近"** —— 它是稳定的系统性尺度差, 不是数值接近。
若 `A_vs_B` 偏离基线或 route ranking 改变 → T1 必须做。

---

## 9. T9 — 测试集(贯穿)

**closure 状态:** `completed_for_touched_no_data_paths`。本轮已通过 Stage-1 minimal tests、
`k_m` alias regression、pyright 与 ruff；下表剩余测试仍作为未来 route-aware / full-grid 工程化时的交接清单。

| 测试 | 期望(无需实测) |
|---|---|
| route 退化 | `r_self=1` 时 `signal_B == signal_A`; overlap=1 时 `cross_joint==cross_collapsed`→`A==C` |
| route 守恒 | 四路 self/cross 分量与 `interferometric_trace` 三分量逐点一致 |
| gauge 归一化 | V1 按 `normalization_view` 比; V2 按 `(raw_reference_normalization_mode, raw_scattering_normalization_mode, normalization_view)` 比; 跨分组键标 diagnostic(断言不进 final) |
| R1/R2 (**仅 raw+in_phase** fixture, #7) | 纯负 raw trace: R1 `n_peaks=0`, R2 `n_peaks>0`。**lockin_surrogate/magnitude 下只测 route/readout label 与 pipeline 一致性, 不断言负 trace 必漏检**(读出已整流/变号) |
| noise regime | shot 0.001→0.2: depth-span 单调收缩, band 翻转(固化 report 146 数字) |
| EV-RI 稳定性 | RI 网格内 top family 翻转 → 触发 "not EV-robust" 标记 |
| 符号审计(T6) (**带过滤**, #11) | `family=ev ∧ λ=404 ∧ lineage=v1_channel_angular_surrogate ∧ phase=current_uncalibrated` 下 `cross_term_negative_fraction==1.0`(不适用 gold/Lens-B/未来 phase) |
| provenance(T5) | manifest 含 reference_model/noise/Jacobian/overlap/NA |
| A_vs_B(T8) (**signed static scalar only**, #8) | 同 cross、同符号约定下 `self_B=r_self·self_A, r_self≥1 ⇒ A_static ≤ B_static`(signed)。**不可用于 `abs(·)`/readout peak/detection_rate/noisy trace** |
| 派生表回归 | mechanism_chain 新列 signed 与 abs 同模反号(EV) |

---

## 10. Closure 决议、证据包与交接矩阵

**2026-06-12 closure 决议:** 本文件原本列出的“极致模拟”路线已经被 owner 裁决收窄为
no-data 相对审计封板门。当前不再补算 R1 全轴、C/D×V2 或全量 10000e；这些工作只作为
“模拟可补 / 实测优先”交接项保留。

**已满足的 no-data 封板门:** `R2/V1` 在 A/B/C/D 全 3-seed 主判决 + A/B 的 V2 抽样 gauge 检验，
且 T3/T4/Stage-1 三轮审查收口。

**主证据包:** `results/audits/report148_stage1_preseal_review_20260612/`

- `report148_stage1_flip_evidence.csv`: A/B/D 在 V1/R2 下
  `fixed_660_gold→404`、`per_wavelength_gold→660` 且 3/3 seed flip=True；C 两 view 均为 660
  且 3/3 seed flip=False。A/B 的 V2 抽样 gauge 检验同为 3/3 seed 完整。
- `report148_stage1_coverage_matrix.csv`: 原始 `coverage_status` 保留 missing/complete；新增
  `gate_classification` 将 R1 与 C/D×V2 标为收窄门外，而非静默抹去。
- `report148_stage1_preseal_manifest.json`: `sealing_gate_status =
  met_under_narrowed_no_data_scope`，`out_of_scope_cells = 10`。
- `report148_stage1_event_accounting.csv`: 同时报告 case-row events 与 distinct physical events；
  双 normalization view 共享物理事件流，distinct 口径约为 case-row 口径一半。
- `report148_stage1_t4_wilson_support.csv`: 7 个 bright-EV combo 全部 Wilson 区间重叠；
  4 个点估计 seed 一致 404 但非区间分离，3 个 genuine near-tie。

**交接矩阵:**

| 项 | closure 分类 | no-data 定稿是否阻断 | 后续出口 |
|---|---|---:|---|
| Stage-1 `R2/V1` A/B/C/D | completed_under_narrowed_no_data_gate | 否 | 已封存为主判决证据 |
| A/B `R2/V2` | completed_as_ab_gauge_sample | 否 | 作为 gauge 抽样，不代表 C/D 全覆盖 |
| T3 noise | completed_for_no_data_claim | 否 | blank trace / detector transfer 实测 |
| T4 EV-RI bright-EV Wilson | completed_for_no_data_claim | 否 | EV 正交表征实测 |
| T7 theta_phase/k_m/bundle | completed_under_no_data_scope | 否 | theta_phase 随 detector identity 推导/实测关闭 |
| R1 全轴 | deferred_out_of_no_data_gate | 否 | 模拟可补；优先级低于实测桶 A |
| C/D×V2 | deferred_out_of_no_data_gate | 否 | 模拟可补；当前仅由 A/B×V2 抽样代表 |
| T1 route-aware full engineering | handoff_not_blocking_no_data_final | 否 | 若未来要扩模拟，再按 §1 骨架执行 |
| T2 calibrated gauge | measurement_priority_handoff | 否 | Au20/40/60 + EV mimic ladder |
| T5/T6/T8 polish | handoff_not_blocking_no_data_final | 否 | 可追溯性/解释补强，不改变 no-data 定稿状态 |

**最终边界:** 148 到此关闭的是 no-measured-data 相对审计路线，不是 calibrated simulator、
optical truth 或 biological truth。三条实测脆弱轴仍开放: cross-term detector identity、
跨波长 gauge、noise/FPR；R1 与 C/D×V2 作为模拟可补项仍开放，但不再阻断 no-data closure。

---

## 附录 — 原任务状态速查

| 任务 | closure 状态 | 本轮重跑? | no-data 后续 |
|---|---|---:|---|
| T1 route 网格 | narrowed/completed for `R2/V1`; full R1/C-D V2 deferred | 否 | 技术骨架保留作模拟可补 |
| T2 gauge 轴 | A/B V2 sample complete; calibrated gauge deferred | 否 | 标准粒子 ladder 实测 |
| T3 noise 轴 | completed_for_no_data_claim | 否 | blank/FPR 实测 |
| T4 EV-RI | completed_for_no_data_claim | 否 | EV composition 实测 |
| T5 provenance | sufficient_for_stage1_preseal; broader schema deferred | 否 | 可选补强 |
| T6 符号修复 | prose corrected; generator cleanup deferred | 否 | 可选补强 |
| T7 清理 | completed_under_no_data_scope | 否 | theta_phase 推导/实测后关闭 |
| T8 A_vs_B 量化 | not blocking; deferred explanation aid | 否 | 可选补强 |
| T9 测试 | touched no-data paths verified | 否 | full route tests 留给未来工程化 |

*本 closure ledger 不引入任何 calibrated 物理 claim；所有标定/实测项明确留在路线图之外，
作为未来 calibrated-simulator 阶段的前置。*
