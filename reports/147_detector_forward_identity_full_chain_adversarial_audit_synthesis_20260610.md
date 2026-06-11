# Report 147 — Detector-Forward Identity 对抗性审查（no-data 相对审计定稿；收窄封板门）

- 日期: 2026-06-10（v2，吸收第三轮 reviewer B 挑错后修订）
- 口径: no-measured-data, Level-1 relative-simulator 审计
- 性质: 多轮外部对抗性交叉审查（reviewer A = Claude, reviewer B = GPT）的
  **no-data 相对仿真审计定稿**（收窄封板门下）；不是物理/生物真值封板。
- 收窄封板门: `R2/V1` 在 A/B/C/D 全 3-seed 主判决 + A/B 的 V2 抽样 gauge 检验；
  R1 读出轴与 C/D×V2 不纳入 no-data 封板范围，移交“模拟可补 / 实测优先”交接清单。
- 复核者立场: Mie/core-shell **数值引擎**已验证，但**完整光学前向模型未结案**；当前最高风险是
  **detector forward model identity 未决**。工程自带的 detector 自洽门(B vs C 比较)对 ~99.9%
  case 判 FAIL，但该门被排除在推荐资格之外。**注意: 现有不一致证据主要是 B/C diagnostic，
  不是 production A vs B；A/B 偏差(仅 self 项)尚未量化。**

本报告所有定量结论均由复核者**亲自重算/扫描**得到，数据源为**本地完整 repo** 的两条产线 artifact
(这些大文件在 repo 内 git-tracked，但被**刻意排除在裁剪后的外审包之外**，故外审包内不可复现):
v1 库 (`results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`,
channel_angular_surrogate, 32,032 行) 与 Lens-B 产线 diagnostic_rows (paper_aligned)。
**可复现脚本: `tools/audits/recompute_report147_detector_identity_tables.py`**（附录 A 给出完整命令，
并输出输入文件 sha256 前缀作 provenance）。引用他人结论处已标注。

---

## 0. 一页结论 (Executive Verdict)

1. **无 P0 级物理公式 bug。** Mie / core-shell / 截面 / 角振幅 / Rayleigh / 光学定理
   经独立重算通过（§1），可停止怀疑**散射数值引擎**（注: 结案的是引擎, 非完整光学前向模型）。
2. **当前最高 P1 = detector forward model 是 hybrid，且 identity 未由实验定义。**
   主 ranking trace 用「塌缩标量平方的自项 + 角谱积分的交叉项」，既不是自洽 ROI 强度探测器，
   也不是自洽 single-mode 相干探测器（§3）。
3. **工程自己的 detector 自洽诊断 lane 已经举手:**
   v1 库 (channel_angular_surrogate, 32,032 case) `band=large` 占 **99.9%**,
   `gate_passed=False` 占 **99.9%**, `roi_vs_scalar_signal_ratio` 中位 **≈ 4.97**;
   **已 spot-check 的 Lens-B lane (seed11/fixed_660 与 seed22/per_wavelength) 更强:
   band=large ≈99.99%, roi 中位 ≈ 6.90**（§4）。**注: 仅 spot-check 两条 lane, 完整
   3-seed × dual-view report 140 panel 的覆盖待补/重算; 不宣称已覆盖整个 headline panel。**
4. **detector identity 确实会动 404-vs-660 headline（minimal-panel 实证）:**
   在同一最小 panel（6 EV + Au20/40/60 anchors, representative geometry families, dual view,
   3 seed, 2000e, V1×R2）上, **A/B/D**(角谱 joint-cross 家族) 都保持
   `fixed_660_gold→404` / `per_wavelength_gold→660` 的 view-flip；**C**(collapsed-cross 家族)
   则在两 view 下都给出 `660 / lambda660_w800_middeep`, **3/3 seed 稳定地消除了 flip**。
   **C 与 A 的 self 项相同, 差异只在 cross-term 结构**(joint vs collapsed) → 这个 headline 翻转来自
   cross-term detector identity, **不是 C 被裁定为 calibrated truth**。这是 route disagreement 的
   明确信号, 不是「C 比 A 真」; 目前仍只是 minimal-panel 结果, 待更宽 panel / 全网格确认。
5. **但该门不在普通推荐资格层级:** detector gate 不属于 ordinary `relative_design_eligible` tier
   (推荐面, True 5320/32032), 只在更严的 `detector_resolved_relative_design_eligible` tier 里;
   后者仅 **True 7/32032**（§5）。故当前推荐是 **non-detector-resolved exploratory relative ranking**。
   即若按 detector 自洽门筛, 推荐面几乎清空; 当前推荐实际依赖不含该门的资格轨道(见 §5, 措辞已去动机化)。
6. **self/cross 机理（§4.2，已用 raw signed 列裁决，纠正两位审查者）:**
   - gold **压倒性 self-散射主导** (|cross|/self ≈ 0.01–0.05);
   - EV 在自洽 ROI lane: 交叉项**与自项同量级** (|cross|/self ≈ 1.0–1.5), 且**在当前未标定的
     reference-phase 约定下 raw signed cross 为负**(404nm 全 3861 行 cross<0, 0 行为正)——
     这是 current phase convention 下的 signed diagnostic, **不是 calibrated 的物理相消 claim**
     (ref_phi0/demod/BFP phase 未标定);
   - net `|signal|/self` **分布很宽**(中位 0.7–1.0): **p10≈0.18 = near-cancellation(|cross|≈self,
     净信号被压到远小于 self); p90≈16–22 = negative-cross-dominated polarity inversion(|cross|≫self,
     净信号大且极性翻转), 不是「更强相消」**;
   - 故 EV 既非「self 主导」(reviewer A 旧说, 中位 1.0 是 near-cancellation 假象),
     亦非「cross 相长增强」(reviewer B 隐含, 当前约定下 signed cross 为负)。
   - **新发现: 已打包派生表 `mechanism_chain_by_wavelength_EV_medians.csv` 把
     `median_cross_term_detector_integrated` 报成 +9.426(magnitude, 丢了符号), 而 raw 列是 −9.426 ——
     这个丢符号的派生表已实际误导 reviewer(把相消误读成相长), 是 **mechanism-critical reporting bug(§8 列 P2)**。**
7. **对外 headline 边界:** width 规则 `W≳λ/NA` 是 **stable engineering guardrail / family heuristic,
   不是 detector-resolved optimum law**(detector identity/gauge 未决前不能写成最优定律); 具体推荐宽度
   是**家族**且依产线: v1 panel **404 → W500–700**(top W600/D1300), **660 → ~W700 但
   band=reference_too_weak**(仅弱参考对照); Lens-B/README 框架是 404/W500、660/W800。
   depth 取中深 **D900–D1200**(注: **这不是 v1 探索 panel 的 raw top-score depth**(top 是 D1300/D1500);
   它是在 discount 掉 detector/gauge/noise 不确定度 + 流体/堵塞/PEG-accessibility 风险后的
   **conservative engineering recommendation**)。
   **404 vs 660 已实证是多轴脆弱、非稳定跨波长 winner。** 目前至少已有三条独立脆弱轴:
   1. **cross-term detector identity**: C 家族稳定翻转 headline(两 view 全 660, 3-seed 稳)；
   2. **EV 成分 / brightest EV preset**: 在 `surface_loaded_bright_2021` 的 7 个 RI 组合里,
      A 路的 `per_wavelength_gold` winner 退化为 `4` 个 **10000e 点估计 3-seed 一致的 404**
      与 `3` 个 **genuine near-tie**(10000e 仍 seed-不稳, 404/660 Wilson 区间重叠)；这 4 个
      404 组合仍有 404/660 Wilson 区间重叠, 因而不是区间分离的 deterministic 断言；
   3. **noise regime**: depth 收益已知随噪声口径变化(见 report 146)。
   因而在 BFP / 标准粒子 / blank 标定挑定 cross-term 模型并钉死噪声口径前, 只能称
   **candidate families**, 不能称稳定跨波长 winner; 不要写成单点宽度映射。

8. **封板前置标定清单(对应三条脆弱轴):**
   - **cross-term detector identity(A/C 之争)** ← BFP image + slit/pinhole transfer + reference phase map
     ：在拿到这些之前, `cross-term detector model` 相关 claim 维持 `blocked / candidate-only`。
   - **跨波长归一化 + heterodyne gauge(404-vs-660, ρ/Au20 baseline)** ← 多波长标准粒子 ladder
     (Au20/40/60 + EV mimic)：在拿到这些之前, `cross-wavelength winner` 维持 `candidate-only`。
   - **noise regime + 误报率(depth 收益, 5σ≈真实 FPR?)** ← measured blank trace(每波长/每芯片)
     + detector transfer / gain：在拿到这些之前, `depth gain / FPR-dependent conclusion` 维持
     `blocked or candidate-only`。
   - **EV composition prior(surface_loaded_bright 的近平局/seed 脆弱)** ← EV 正交表征
     (NTA/TRPS/DLS/TEM/flow cytometry) 约束 size/RI/corona 分布：在拿到这些之前,
     `bright-EV-specific winner claim` 维持 `candidate-only`。
   - **compute / artifact 口径说明**: shared dual-normalization 运行同时报告
     `case-row events` 与 `distinct physical events`。后者约为前者一半, 因为两条
     normalization view 共享同一条物理事件流；任何算量/预算比较都必须标清口径。

---

## 1. 散射数值引擎 — 已验证（独立重算）；完整光学前向模型未结案

复核者绕过测试名直接重算 (`mie_engine.py`, `intrinsic_scattering.py`):

| 检验 | 结果 | 判定 |
|---|---|---|
| core-shell→homogeneous 退化 (m_core=m_shell, x=3, m=1.5+0.01j) | max\|Δa_n\|=1.1e-15, \|Δb_n\|=8.0e-16 | `a_n=-solve(...)` 负号正确 |
| 光学定理 Qext≥Qsca, 非吸收 Qabs→0 | x=2,m=1.33: Qabs=1.1e-16; 金 x=5,m=0.2+3.7j: Qabs=0.126 | 守恒 |
| Rayleigh x⁴ (x=0.05) | Qsca(x)/Qsca(x/2)=16.002 | 精确 |
| physics 测试套件 | `test_physics_core.py + test_mie_engine.py` → 382 passed | 通过 |

**结论: Mie/core-shell 数值引擎 (系数、截面、角振幅、单位 `k=2πn_m/λ₀`, `x=k a`, `m=ñ_p/n_m`,
`dCsca/dΩ=(|S1|²+|S2|²)/2k²`) 在测试 regime 内已验证, 可停止怀疑。**
**但「散射物理底座」若含 high-NA 矢量投影、近界面散射、GLMT/聚焦束梯度、EV 非球形、
EV RI/corona 不确定度、particle-channel 微扰, 则尚未结案** —— 见 §3(detector identity)、
§6(EV RI/theta_phase)。**结案的是数值引擎, 不是完整光学前向模型。**

`materials.py` RI 来源清楚(金/银 Johnson&Christy 1972; 水/PBS Cauchy surrogate;
熔融石英 Malitson Sellmeier; EV uniform 固定 1.38)。EV RI 不确定度未传播 → 见 §6 (P1)。

---

## 2. 全链路前向模型(复核确认的真实代码路径)

```
Input Θ
 → Material ñ_p,n_m,n_g                         materials.py
 → Mie/core-shell a_n,b_n,S1,S2,Csca            mie_engine.py, intrinsic_scattering.py   [physical]
 → Detector angular collapse → E_sca_det(复)     utils.py:3107/3349/3648                   [surrogate]
 → 归一化 E_sca/E_sca_ref(Au20 baseline)         utils.py:4118                              [gauge]
 → Reference A_ref=ρ·g, 角谱场                    reference_field.py:1458/652               [surrogate]
 → Trajectory 受阻布朗+矩形流型                   trajectory.py                             [physical surrogate]
 → Illumination 场包络 A_env=√(I/I₀)              illumination.py                           [physical]
 → 干涉 ΔI=|E_sca|²+2Re[F·E_ref·E_sca*]           interferometric_trace.py                  [surrogate, hybrid]
 → Readout lockin surrogate + Noise              parameter_sweep.py:1099/2055              [surrogate]
 → Threshold median+5·1.4826·MAD(前20%)          pulse_analysis.py:45                      [engineering, 非FP]
 → Event QC artifact-risk                        event_quality_control.py                  [batch surrogate]
 → Batch stats Wilson LB/UB(z=1.96), robust CV   parameter_sweep.py:6166                   [correct]
 → Engineering gate (gate-before-rank, LB based) parameter_sweep.py evaluate_engineering_gate
 → EV ensemble aggregation (prior 权重)
 → Claim governance / eligibility flags          design_claim_governance.py
 → Candidate panel
```

关键默认 (data_objects.py): `phase_model=relative_surrogate`,
`reference_model=channel_angular_surrogate`(v1) / `paper_aligned_phase_filter`(Lens-B report 140),
`scattering_projection_mode=parallel`(S2/k, 保相位), `collection_integration_mode=pupil_slit_surrogate`,
`interference_overlap_mode=joint_overlap_integrated`, `field_coordinate_measure=theta_phi_surrogate`,
`bfp_to_angle_jacobian_applied=False`, `pulse_detection_mode=absolute`, `threshold_sigma=5`,
生产 `NA_collection=0.9`。

---

## 3. 最高风险 P1 — Detector Forward Identity 未决

### 3.1 三条 detector route 的代数（复核确认）

令 `w` 为角度收集权重(θ,φ), `r=E_ref(Ω)`, `s=E_sca(Ω)`。

| Route | 自项 (self) | 交叉项 (cross) | 物理身份 | 谁在用 |
|---|---|---|---|---|
| **A (production hybrid)** | `\|∫w·s\|²` | `2Re∫w·r·s*` | 半截升级, 无对应真实探测器 | **检出/排序/推荐** (interferometric_trace.py:98–113, 160–172) |
| **B (ROI intensity)** | `∫w·\|s\|²` | `2Re∫w·r·s*` | ROI 强度积分 surrogate(**gauge-locked, 非独立 photodiode truth, 见 §3.2**) | diagnostic (bfp_detector_operator.py:116–167, 252–259) |
| **C (collapsed coherent)** | `\|∫w·s\|²` | `2Re[(∫w·r)(∫w·s)*]` | collapsed coherent surrogate(形似相干模投影, 但 `w` 是 aperture/collection kernel, **非标定 complex mode function**, 不是真实 matched-mode detector) | ratio 分母 (scalar_signal) |

- production = **A = C 的自项 + B 的交叉项**(「半截升级」, reviewer A 命名, 复核确认)。
- **关键: A 与 B 共享同一个角谱交叉项** (overlap_factor = joint_overlap/collapsed_product,
  utils.py:3574–3634)。因此 `A − B = self_C − self_B` **只差 self 项**, 与 cross 项无关。
- 仅就 self 项, 在当前归一化正核 + throughput 约定下有 `self_C = t²|∫w·s|² ≤ t·∫w|s|² = self_B`
  (注: collapse 带 t², ROI self 带 t¹, t≤1, reviewer B 指出的 throughput 幂次差; 故不等式在
  当前约定下更强成立)。**但这是 signed 信号关系, 不直接给出 readout 后 (`pulse_detection_mode=absolute`)
  的可检性大小排序** —— 见 §4.3。
- **A、B、C 不是三种数值近似, 而是三种 detector identity 假设。**

### 3.2 B 是 gauge-locked surrogate, 不是独立 photodiode truth（reviewer B 的关键收紧，本轮升为核心）

B route **不是从独立物理场直接积分得到的 detector signal**。源码
`compute_detector_integrated_interference()` 先 collapse raw angular field, 再把 ref/sca 角谱场
**rescale 到 production collapsed target** (bfp_detector_operator.py:225–228):
`reference_target_collapsed = E_ref_complex`, `scattering_target_collapsed = E_sca_unit_normalized`。
此外:
- `theta_phase=exp(i(θ-θc)sinφ)` 是无量纲启发式相位 (bfp_detector_operator.py:108–112, utils.py 同形),
  无 `k·x` / `kΔz(1-cosθ)` 推导; **但注意它(以及 projection 的 `exp(i·0.5 sinθ sinφ)`)在 B 的 integrand
  里抵消** —— `|s·tp|²=|s|²`, 且 `(r·tp)·conj(s·tp)=r·conj(s)·|tp|²=r·conj(s)`。
  **故 theta_phase 不是 B route signed-negative cross 的来源**(B 的 cross 符号来自 `arg(∫w r s*)`,
  即未标定的 `ref_phi0`+材料/路径相位); theta_phase 主要通过 **collapsed amplitude(A/C 路) 与
  gauge-locking rescale factor** 间接影响结果;
- φ 依赖由投影模型与 surrogate phase 人工展开。

**后果(本轮重点): B/C disagreement 不能解读为「真实 ROI photodiode vs scalar detector」。**
它实为: **在 production scalar gauge 已被固定后, surrogate 角谱形状与 collapsed scalar 表示的
内部不一致。** 因此:
- B 的「物理身份」应写成 **ROI-intensity-like angular surrogate, rescaled to collapsed scalar
  targets; not an independent calibrated photodiode forward model**;
- **下一轮 A/B/C 必须分两版(见 §7): V1 gauge-locked(保留 rescale, 测工程内部 detector surrogate
  的 ranking stability) 与 V2 raw-angular(不 rescale, 测 detector route 本身的物理敏感性)。
  否则无法区分 A/B/C 差异是 detector identity 造成的, 还是 collapsed-gauge back-fitting 造成的。**
- **随后最小 panel 实证已补出 detector-identity headline 结果:** A/B/D(角谱 joint-cross 家族)
  保持 `fixed_660→404` / `per_wavelength→660` 的 view-flip, 但 C(collapsed-cross 家族)
  使两 view 全变成 `660`, **3/3 seed 稳定**。因为 A 与 C 的 self 项相同、只差 cross-term 结构,
  这个翻转必须归到 **cross-term detector identity disagreement**, **不是** C 被裁定为 calibrated truth。
  因而 report 140 的 `404 vs 660` 只能继续写成
  `candidate families under the current detector surrogate`, 直到实测标定挑定 cross-term 模型。

**后续实现补记(Report 148 stage1 跟进):** 在当前 frozen-B / `median+5·MAD` 自校准阈值口径下,
**gauge / scale 差异本身不会自动成为 detector-identity headline。** 当前实现里 V1↔V2 raw-angular
若只改整体 amplitude scale, 会同时受到两层抑制:
1. `n_ref_raw` / `n_sca_raw` 会把 raw angular 场重新钉回接近现有 scalar 工作点；
2. 阈值是 trace 内部自校准, 对纯整体 scale 的敏感性通常弱于对时域 shape 的敏感性;
   **但在 frozen-B 这类带绝对电子噪声的 as-run 配置下, 这种吸收只是部分的, 不是严格不变。**
因此 report 147 标出的 detector-route `~5–7×` 幅度不一致(B/C、V1/V2 gauge) 在**事件检出层**
本身几乎不可见, **不能单独拿来证明 detector identity 会改 ranking**。真正会推动
detectability / ranking 改变的, 是 cross/self 的时域 shape 差异(A/B/C/D), **不是**
gauge/scale 本身。这个结论只适用于 `current threshold convention 下的 relative detectability`,
**不得升级成** `detector identity 无关紧要`、detector-resolved、heterodyne-gain 或跨波长最优 claim。

**T4 / EV-RI 补记(Report 148 收尾):** 在最小 panel 的 A-vs-C EV-RI 扫描里, 大多数 EV-RI 组合
(`29/36`) 保持 Stage-1 headline；**只有** `surface_loaded_bright_2021` 的 `7/9` 组合会让
A 路的 `per_wavelength_gold` winner 在 `404↔660` 之间退化成 seed 脆弱。对这 `7` 个组合做
focused `10000e × 3-seed` 后:
- A 路有 `4` 个组合收敛为 **10000e 点估计 3-seed 一致的 404 winner**, 但 404/660 Wilson
  区间仍重叠, 不升级为区间分离的 deterministic winner；
- A 路另 `3` 个组合仍是 **genuine near-tie**(10000e 仍 seed-不稳, 404/660 Wilson 区间重叠)；
- C 路在这 `7` 个组合上全部保持 **deterministic 660**。
因此 EV-RI 的机制应写成 **bright-EV near-tie / RI dependence**, 不是“RI 确定性地把所有 winner 推走”。
同时 `A↔C` 的 route disagreement 对 RI **不稳健**: `22/36` 组合始终分歧, `13/36` 组合只在部分 seed
分歧, `1/36` 组合(`surface_loaded_bright_2021 / 1.38 / protein_rich`)始终一致。**这依然是 route
disagreement, 不是某一 route 被证成 calibrated truth。**

**T3 / noise-regime 补记(Report 148 收尾):** 在 baseline EV composition 下, `shot_noise_scale`
从 `0.001 → 0.05 → 0.2` 显式改变了跨波长 headline 与 depth 口径:
- `0.001` baseline 已补齐为 **3-seed**；`0.001` / `0.05` 下, A 路仍保持 Stage-1 headline
  (`fixed_660→404`, `per_wavelength→660`)；
- `0.2` 下, `fixed_660_gold` 是 **2/3 seed 翻到 660、1 seed 仍 404**，而 `per_wavelength_gold`
  仍是 **3/3 seed 全 660** ——  
  **noise regime 确实是第三条会动跨波长 headline 的轴**, 但它表现为 strong-shot 下的
  seed-fragile headline shift, 不是干净单调翻转。
- depth 口径必须明确分两面, 且旧的 selected-annulus 因果要收紧:
  - **all-crossing** depth-span 随 shot↑显著收缩(中位从约 `0.14–0.16` 降到 `0.05–0.08`),  
    并且 depth-top seed 稳定率分档为
    `0.001→10/10`, `0.05→8/10`, `0.2→8/10`（合计 **26/30**），说明这里有真实、可复现的深度结构；
  - **selected-annulus** 推荐面一开始就没有可复现的 depth 排序: width-family 内
    depth-top 的 seed 稳定率分档为
    `0.001→1/10`, `0.05→1/10`, `0.2→3/10`（合计 **5/30**），对应的 depth-span 中位数仅约
    `0.017–0.050`，与 `N=2000`、`p≈0.5–0.7` 下的采样噪声底同量级。所谓高 shot 下的 "4–8%"
    抬升, 更准确地说是 **p→0.5 时噪声底变大**, 不是噪声把一个真实深度效应“再分叉”出来。
    `0.001` baseline 本身就已给出同样方向的证据(`selected 1/10` vs `all-crossing 10/10`),
    说明 selected-annulus 深度不稳是**内禀口径特征**, 不是 high-shot 才被诱发。
因此 report 146 的“深度收益随 shot↑收缩”只对 **all-crossing probe 面**成立；到了 governed
selected-annulus 面, 更准确的表述应是: **depth 本就弱, 且其 span 多数是 sampling-noise floor,
不应被解释为可复现深度排序。**
与此同时, `reference_operating_band` 在 `404` 侧从 `electronics_noise_limited_useful` 翻成
`shot_noise_limited_no_gain`, 而 `660` 侧始终混有 `reference_too_weak`。这再次说明 headline 不是
单一物理 winner, 而是 detector identity × EV composition × noise regime 的联合脆弱结果。

A/B/C 之间无任何实测可裁决 → 这是 identity 未定义, 不是「B 比 A 真」。

---

## 4. 工程自带 detector 自洽门的全网格实测

### 4.1 disagreement 分布 —— 两条产线（复核者亲自扫描）

**v1 库** (channel_angular_surrogate, `..._10000e_summary.csv`, 32,032 行):

| 字段 | 实测 |
|---|---|
| `detector_operator_disagreement_band` | large 32,000 / moderate 24 / small 8 → **99.9% large** |
| `detector_operator_gate_passed` | **False 32,000 / True 32 → 99.9% False** |
| `roi_vs_scalar_signal_ratio` (=\|B\|/\|C\|) | min 0.12, p10 4.89, **median 4.97**, p90 5.16, max 941 |

**Lens-B 产线** (paper_aligned, report 140 headline 来源,
`..._seed11_..._fixed_660_gold_diagnostic_rows.csv`, 32,032 行):

| 字段 | 实测 |
|---|---|
| `detector_operator_disagreement_band` | large 32,030 / moderate 2 → **99.99% large** |
| `detector_operator_gate_passed` | **False 32,030 → 99.99% False** |
| `roi_vs_scalar_signal_ratio` | p10 6.76, **median 6.90**, p90 7.04 |

spot-check 不止 seed11/fixed_660: seed22/per_wavelength_gold lane 同样 band large 32028/32032、
roi 中位 6.90。**但仍只覆盖 (seed11 fixed_660) + (seed22 per_wavelength) 两条 lane, 不等于完整
3-seed × dual-view report 140 panel** —— 故只能说「已 spot-check 的 Lens-B lane 一致地更强」,
完整覆盖待补(见 §7 输出字段)。

⇒ **detector-route 不一致在已 spot-check 的 headline lane 上更强, 不是 v1 surrogate 独有。**
(注: 该 diagnostic_rows 的 `reference_model` 列为空, 故**该文件不能自证 paper_aligned** ——
paper_aligned provenance 须由 runner 代码 `build_frozen_b_cfg`/report 146 确认, 不能由 diagnostic_rows
自身证明; 空列本身也印证 §6 provenance 缺口。)

注: `roi_vs_scalar_signal_ratio` 比的是 **B vs C**, 不是 production A vs B。
「~5–7×」是 collapsed-only 与 ROI-integrated 之差; production A 介于两者之间。
**下一轮必须新增 `A_vs_B_signal_ratio`** 才能量化主 trace 偏离自洽 B 多少 (reviewer B 提出, 复核采纳)。

### 4.2 self vs cross 逐波长/族分解 —— 裁决两位审查者的分歧

复核者从 **v1 库**按 (family, wavelength) 聚合 `self_sca_detector_integrated`,
`cross_term_detector_integrated` (已验证 `signal = self + cross` 逐行精确, 重构误差 0)。
Lens-B 产线 diagnostic_rows 缺干净的 particle_family 列, 无法同样干净拆分, 但其聚合层
中位 cross = −2.45 且 60.3% 行 cross<0, 与下表「cross 在当前相位约定下以 signed-negative 为主」方向一致:

| family | nm | n | med self | med cross | med \|cross\|/self | cross<0 占比 |
|---|---|---|---|---|---|---|
| ev | 404 | 3861 | 7.507 | **−9.426** | 1.335 | **100.0%** |
| ev | 488 | 3861 | 5.031 | **−5.272** | 1.155 | 90.9% |
| ev | 532 | 3861 | 2.674 | **−3.600** | 1.495 | 90.9% |
| ev | 660 | 3861 | 1.456 | **−1.054** | 0.964 | 72.7% |
| gold | 404 | 4147 | 3765.263 | 8.005 | 0.017 | 45.3% |
| gold | 488 | 4147 | 3043.964 | 85.806 | 0.031 | 0.4% |
| gold | 532 | 4147 | 2361.984 | 104.568 | 0.045 | 0.0% |
| gold | 660 | 4147 | 2981.653 | 24.793 | 0.011 | 19.6% |

**符号审计(决定性, 解决 reviewer B 提出的 sign 冲突):** raw `cross_term_detector_integrated`
列(=`2·Re(joint)·throughput`, 有符号) 对 EV **在当前未标定 reference-phase 约定下确为负**:
404nm **3861 行全 cross<0, 0 行为正**; 488/532nm 各 3510 neg + 351 zero; 660nm 2808 neg + 1053 zero。
**0 行为正。** 这是 current phase convention 下的 signed diagnostic(`ref_phi0`/demod/BFP phase 未标定),
**不是 calibrated 的物理 destructive-interference claim**。已打包派生表
`mechanism_chain_by_wavelength_EV_medians.csv` 的 `median_cross_term_detector_integrated=+9.426`
是 **magnitude(丢符号)**, 与 raw signed −9.426 同模反号 —— **reviewer B 是被这张丢符号的派生表误导;
Report 147 的 signed-negative 结论对**。该派生表丢符号是一个 mechanism-critical reporting bug(§8 列 P2)。

**net 信号(纠正旧「net 小」表述, reviewer B 的 P1-9/P1-10 成立):** EV `net |signal|/self` **分布很宽**(中位 0.7–1.0):
- **p10≈0.18 = near-cancellation**: |cross|≈self 反号, `signal=self+cross` 穿过近零, 净信号被压到远小于 self;
- **p90≈16–22 = negative-cross-dominated polarity inversion**(不是「更强相消」): |cross|≫self,
  净信号大且极性翻转(例 self=1,cross=−20 → signal=−19,|signal|/self=19)。

宽是 near-zero 穿越 + 负 cross 主导两端共同造成, **不是「双峰」**(无 histogram/dip test, 不下双峰结论)。

**裁决(纠正双方):**
- **gold = 压倒性 self-散射主导** (|cross| 仅自项的 ~1–5%)。reviewer A 的 gold 判断成立。
- **EV: 交叉项与自项同量级 (|cross|/self ≈ 1.0–1.5), 且当前相位约定下 raw signed cross 为负**;
  net |signal| 宽(从 near-cancellation 到 negative-cross-dominated polarity-inversion 两端,
  中位约 self 的 0.7、且在当前约定下为负)。
- 因此 **reviewer A 的「EV self-dominated, 部分推翻 NODI 前提」过强**(中位 self/|signal|=1.0 是
  near-cancellation 假象); **reviewer B 的「cross 相长增强」也过强**(raw cross 实为负相消)。
- **本轮结论表述: 在自洽 ROI 积分(NA=0.9)、当前未标定相位约定下, EV 外差交叉项与自项同量级但
  signed 为负, net ROI 信号宽(兼有 near-cancellation 与 negative-cross-dominated polarity-inversion 两端);
  gold 则 self 主导。真实物理相消/相长归属待 reference-phase 标定。**
- **【重要纠错, reviewer B 的 P1-2 成立】不能说「production collapse-first 规避了角度相消」——
  这是代数错误。** production A 的交叉项 = B 的角谱重叠(同一个 `2Re∫w r s*`), **A 完全继承同样的
  (负)角谱交叉项, 没有规避相消**; A 与 B 只差 **self 项的表示**(A 用 `|∫ws|²`, B 用 `∫w|s|²`)。
  若 B 的 cross 为负, A 的 cross 同样为负 —— 改变的只是 self 项尺度, 不是 cross 的相消。

### 4.3 必须自我设限的诚实声明

detector-integrated lane 是**静态 case-level 快照**(单一场配置), 而 production 检出在**时域**对
`cos(Δφ(t))` 随轨迹相位扫掠后、在 `|signal|` 峰上判定 (`pulse_detection_mode=absolute`)。
**因此「静态 cross 为负」不能直接等同「production EV 检出被相消压死」。** 它**能**证明的是:
detector-route 选择改变了静态信号的符号与量级结构(全网格)。本轮 no-data 封板只裁定
`R2/V1` 主判决与 A/B 的 V2 抽样 gauge 检验；真实时域/读出后果仍需实测定义 detector identity
(见 §7)。**这是 identity 未决, 不是已证 NODI 不成立。**

---

## 5. 门控接线 —— detector gate 只在更严的 tier，不在普通推荐资格（有牙齿的实证）

`design_claim_governance.py:594–607` (复核确认):

```
relative_design_eligible = engineering_gate ∧ readout_semantics ∧ double_counting
                         ∧ manifest ∧ event_qc ∧ selection ∧ ev_integrity     (不含 detector_gate)
detector_resolved_relative_design_eligible = relative_design_eligible ∧ detector_gate
```

全网格实测 (复核者亲自扫描):

| 资格旗标 | True | 占比 |
|---|---|---|
| `relative_design_eligible` | 5320 / 32032 | 16.6% |
| `detector_resolved_relative_design_eligible` | **7 / 32032** | **0.02%** |
| `absolute_global_green_eligible` | 0 | 0% |
| `final_green_eligible` | 0 | 0% |

注: 上述资格分数来自 **full-summary 扫描**(裁剪外审包内的 `claim_field_distributions.csv` 不含
`detector_resolved_relative_design_eligible` 列, 故该 7/32032 不可由轻量表复核, 但被打包的
`within_lambda_top_geometries.csv` 中 `EV_design_detector_resolved_pass_fraction=0.0` 佐证)。
两条产线 detector_resolved 都≈0: v1 True 7/32032, Lens-B(seed11) True 2/32032
(注意 Lens-B 的 `relative_design_eligible` 因门限不同而 True 占 ~83%, 但 detector_resolved 同样≈0)。

**含义(措辞已收紧, 去动机化): 当前推荐/报告路径实际依赖非 detector-resolved 的
`relative_design_eligible` 层级。** 这作为 exploratory relative lane 是被允许的, 也不是隐瞒
(blocker 已写进 candidate panel 的 `detector_operator_gate_not_passed`); 但该 blocker
**没有阻止 route ranking/headline 的形成**。对外只能称
`relative/proxy ranking with detector-operator caution`, 不能称 `detector-resolved relative ranking`。

另(纠正旧表述, reviewer B 的 P2-1 成立): 区分 **score 软惩罚 vs hard gate**。
`compute_engineering_score`(parameter_sweep.py:10048) **已把 `event_artifact_risk_norm` 作为软惩罚
计入排序数字**(`w_event_artifact=0.6`, line 10091); 但 hard gate `evaluate_engineering_gate`
(events/stable/margin/phase-flip) **不含** event_qc/selection/detector, `compute_final_engineering_score`
也只按该 hard gate 决定 pass/fail。即 event artifact 进了排序软惩罚、未进 hard gate;
detector/selection 既不进 hard gate 也不进排序数字。报告层必须强制
`recommended ⇒ relative_design_eligible`，且不得升级为 detector-resolved claim，否则护栏形同虚设。

---

## 6. 已收敛的相对仿真边界 (P1, 多轮一致)

| 项 | 状态 | 修复 |
|---|---|---|
| **heterodyne gauge** 由 (Au20 baseline `E_sca_ref` × `ρ`) 两未标定常数固定工作点 (utils.py:4118, reference_field.py:1532) | 决定交叉项 vs 自项相对强度, 跨波长不完全抵消 throughput → 喂入 404↔660 view-flip | 标准粒子 ladder; 报告加 gauge 注脚, 禁「增强倍数」 |
| **provenance**: seed `run_manifest.json` runtime_config_subset 与 `design_postprocess.csv`(48列) 缺 reference_model/noise/Jacobian/overlap/NA | 外审无法只靠 artifact 核验 runtime | **零重跑** 补 config trace |
| **noise regime**: `shot_noise_scale` 自由旋钮(as-run 0.001) | electronics→shot, depth-span 23%→8% 并翻 band (report 146) | 升为 scenario 轴 0.001/0.05/0.2 |
| **EV RI 不确定度**: uniform 固定 1.38, core-shell 存在但未传播 | EV 最优 λ/几何 鲁棒性不可见 | 小网格 n=1.37/1.38/1.40 × shell × corona |
| **external bundle**: 裁剪包 verifier 需要外部包模式 | 2026-06-12 已补 `--external-bundle-mode`; 严格 hash/package 结构检查仍保留 | 已清理(P2) |
| **theta_phase** 无量纲启发式 | 在 B integrand 内抵消; 经 A/C collapsed amplitude 与 gauge rescale 间接影响; 已登记为未经第一性推导验证的唯象 surrogate | 并入 §7 sensitivity 或给推导 |
| `k_m_inv` legacy alias(=k 非 1/k) | `k_m` 为 canonical；`k_m_inv` 仅保留 deprecated exact alias，回归测试守住数值完全一致 | 已清理(P3) |

depth 校正(reviewer A 提出, 复核采纳): 大 depth 效应在 **all-crossing** probe 面, 不在
selected-annulus 推荐面(后者 depth 仅 3–10%)。最终仍取 D900–D1200, 但理由是
「推荐面 depth 本就弱 + 工艺/堵塞/PEG accessibility + gauge/noise 未标定」, 而非「强行压住大偏好」。

---

## 7. 决定性下一步 — detector model (A/B/C/D) × 读出策略 (R1/R2) × gauge (V1/V2) 小网格

**维度分清(reviewer B 的 P2-3 成立): A/B/C/D 是 detector signal model; signed-vs-absolute 是
读出/峰检测策略, 不是 detector identity。** 故正交三轴展开, 不要把读出策略混进 detector route。

**工作量纠正(reviewer B 的 P2-2 成立): 不是「几乎零新代码」。** `signal_detector_integrated`(B)、
`scalar_signal`(C) 目前是 **case-level 静态 diagnostic scalar**, 不是 event-level time trace。
要把 B/C/D 经同一 `trajectory → illumination A_env(t) → phase(t) → lock-in/threshold → find_peaks`
pipeline 跑(再叠加 R1/R2 读出与 V1/V2 gauge), 仍需新 plumbing: 定义 `self_B(t)`、`cross_B(t)`、
随轨迹的角谱相位、ROI 项是按 `A_env(t)` 还是 `A_env(t)²` 缩放等。**结论: B/C 的静态项已实现, route-resolved event-trace 生成仍需开发。**

对 sharp MSC/sEV 先验 + gold 20/40/60 anchor + 404 与 660 的**宽度家族**(不是单点宽度),
**通过同一 lock-in/threshold/event 检出 pipeline** 跑 **detector model × 读出策略 × gauge** 三轴:

**轴一 — detector signal model A/B/C/D:**

| Model | 信号(detector identity) | 目的 |
|---|---|---|
| A | `\|∫w·s\|² + 2Re∫w·r·s*` | 当前 production hybrid(legacy baseline) |
| B | `∫w\|s\|² + 2Re∫w·r·s*` (静态项=`signal_detector_integrated`) | ROI 强度积分 surrogate(gauge-locked, 非独立 photodiode truth) |
| C | `\|∫w·s\|² + 2Re[(∫wr)(∫ws)*]` (静态项=`scalar_signal`) | collapsed coherent surrogate(`w` 非标定 mode function, 非真实 matched-mode) |
| D | `2Re∫w·r·s*` (cross-only) | **cross-only weak-scattering surrogate route**(非「真·heterodyne」; 仍用 surrogate ref 场/投影/未标定相位/未标定算子): 测在给定 phase/gauge 约定下, 仅交叉项能否撑起 ranking |

**轴二 — 读出策略 R1/R2(非 detector identity):**

| Policy | 定义 | 对齐 |
|---|---|---|
| R1 | signed trace → 同一 readout/filter → `find_peaks(readout(signal))` (signed-positive 检出) | signed 检出 |
| R2 | signed trace → 同一 readout/filter → `find_peaks(\|readout(signal)\|)` (abs 放**峰提取**处, 非直接 `\|self+cross\|` 当 detector signal) | 当前 `pulse_detection_mode=absolute` |

D 路因 EV cross 在当前约定下为负, signed 全负但 abs 仍可检出, **必须 R1 与 R2 都跑**,
输出 `signed_cross_route_score` 与 `absolute_cross_route_detection_score`。

**轴三 — gauge 模式 V1/V2(reviewer B 的新 P1):**
- **V1 gauge-locked**: 保留 rescale-to-collapsed-target → 测当前工程内部 detector surrogate 的 ranking stability;
- **V2 raw-angular**: 不 rescale, 直接用 raw angular ref/sca 场 → 测 detector route 本身的物理敏感性。
  **V2 必须显式定义 raw angular 振幅如何归一化**(否则 V2 的 ranking flip 可能只是 normalization flip,
  不是 detector identity flip); 新增 `angular_field_normalization_mode`, `raw_angular_reference_norm`,
  `raw_angular_scattering_norm`, `route_normalization_anchor`, `route_level_normalization_view`。
- 否则无法区分 A/B/C 差异是 detector identity 还是 collapsed-gauge back-fitting / normalization 造成的。

新增必输出字段: `detector_route_id(A/B/C/D)`, `readout_policy(R1/R2)`, `gauge_mode(locked/raw)`,
`self_term_selected`, `cross_term_selected`, `total_signed_signal_selected`, `total_abs_signal_selected`,
`A_vs_B_signal_ratio`, `A_vs_C_signal_ratio`, `B_vs_C_signal_ratio`(**当前只有 B/C, 缺 A/B**),
`detector_route_rank_stability_class`, `detector_route_flip_flag_404_660`。

**判决规则:**
- **只在同一 `angular_field_normalization_mode` 内比 ranking; 跨 normalization 的差异是 diagnostic, 不是 final ranking 证据。**
- 若 A/B(/D) 在 R2 + 两 gauge 版下都给出同一 family、404↔660 view-flip 保持 → P1-detector 降为 documented surrogate gap。
- 若改变 view-flip 或翻转 self/cross 主导 → **report 140 的 404-vs-660 headline 撤回到
  「candidate families under the current collapse-gauge-locked hybrid-detector surrogate」, detector identity 列为第一标定需求。**

**实现后优先级修正:** 若 V1↔V2 只改整体 amplitude scale, 其 effect 多半被 norm 重钉与自校准阈值吸收。
此时 detector-identity 对 headline 的主判据应从 `gauge(V1/V2)` 转到 `shape(A/B/C/D)`:
- `A/B/C/D` 改的是 self / cross 的时域 shape, 检出会直接看到；
- `V1/V2` 若主要是 norm / scale 重钉, 只保留 secondary diagnostic 价值。
因此后续是否撤回 / 保留 `404 vs 660` headline, 要以 **A/B/C/D 的 winner-family / view-flip**
是否改变为主判据, gauge 只作辅助说明。

最终裁决仍需实测: BFP image / slit-pinhole transfer / reference phase map / 标准粒子 ladder,
以判断真实光路更像 A、B 还是 C。

**2026-06-12 Stage-1 收窄封板门状态:** 证据包
`results/audits/report148_stage1_preseal_review_20260612/` 显示 `R2/V1` 已覆盖
A/B/C/D 全 3-seed；A/B 的 `R2/V2` 也为 3/3 seed 完整，作为抽样 gauge 检验。consensus 复现为
A/B/D 在 V1/R2 下 `fixed_660_gold→404`、`per_wavelength_gold→660` 且 3/3 seed flip=True；
C 在 V1/R2 下两 view 均为 660 且 3/3 seed flip=False。`R1` 全轴未运行，`C/D × V2`
未运行；二者登记为收窄门范围外的残余假设，不作为本轮 no-data 相对审计封板阻断项。

### 7a. 封板门收窄记录（2026-06-12）

- 裁决人: owner。
- 新封板门定义: no-data 相对审计封板门 = `R2/V1` 在 A/B/C/D 全 3-seed 主判决 +
  A/B 的 V2 抽样 gauge 检验，且 T3/T4/Stage-1 三轮审查收口。
- 范围外: R1 读出轴与 C/D×V2 不纳入 no-data 封板范围，移交“模拟可补 / 实测优先”
  交接清单。
- 收窄理由: headline 已降为 **candidate-families under detector surrogate**；R1 是读出策略，
  V2 是 gauge 不确定度轴。继续补齐这些模拟 cell 只会强化“不可裁决”的不确定性陈述，
  不能立 clean winner；clean winner 需要实测 BFP/slit/reference phase、标准粒子 ladder 与 blank trace。

### 7b. 残余假设台账（双桶）

**桶 A — 物理真值，需实测才能 resolve（保持封板前置标定清单不动）**

- cross-term detector identity: A/C 之争仍需 BFP image、slit/pinhole transfer 与 reference phase map。
- 跨波长 gauge: 404↔660 的 gauge 需要 Au20/40/60 + EV mimic 多波长标准粒子 ladder。
- noise·FPR: depth / selected-annulus 结论仍需 measured blank trace 与 detector transfer / gain。

**桶 B — 模拟可补，本轮判为非 headline-决策相关而未跑**

- R1 读出轴: headline 的 R1-不变性为假设、未测；可模拟补齐，但当前判为非 headline-决策相关，
  优先级低于桶 A 实测。
- C/D×V2: 仅由 A/B×V2 抽样 gauge 检验代表，未做 C/D 全覆盖；可模拟补齐，但当前判为非
  headline-决策相关，优先级低于桶 A 实测。
- theta_phase: `exp(i(θ-θc)sinφ)` 是无量纲唯象启发式 aperture phase surrogate，未经第一性推导验证；
  已在源码注释登记为 surrogate assumption，应随 detector identity 实测/推导一起关闭。

---

## 8. 综合严重度表(no-data 收窄门定稿)

| # | 问题 | 是否动 ranking | 是否动 headline | 严重度 |
|---|---|---|---|---|
| 1 | detector forward identity 未决 (A=hybrid; A/B/C 是三种探测器假设) | 可能(self/cross 主导可翻) | 可能(404 vs 660) | **P1 (最高)** |
| 1b | 现有不一致证据是 B/C diagnostic, 非 production A/B; 且 B 是 gauge-locked(rescale 到 collapsed target) | 待 A/B 量化 | — | **P1(量化缺口)** |
| 2 | detector gate ~99.9% FAIL 且被排除在推荐资格外 (detector_resolved≈0, 两产线) | 间接 | 否 | **P1** |
| 3 | heterodyne gauge (Au20,ρ) 未标定 | 否(相对内成立) | 限「增强倍数」措辞 | P1 |
| 4 | provenance: manifest/postprocess 缺 config | 否 | 否(可复核性) | P1(零重跑) |
| 5 | noise regime 自由旋钮 | 是(depth) | depth 降级 | P1 |
| 6 | EV RI 不确定度未传播 | 是(可能翻 family) | 是 | P1 |
| 7 | score 与 eligibility 解耦 | 取决于报告层 AND | 否 | P2 |
| 8 | external bundle verifier 已补 `--external-bundle-mode` | 否 | 否(交付 usability) | 已清理(P2) |
| 9 | depth 大效应在 all-crossing 非推荐面 | 否 | 否 | 校正(降级) |
| 10 | theta_phase 无量纲启发式 | 二阶 | 否 | P3→并入#1 sensitivity |
| 11 | 派生表 `mechanism_chain_..._EV_medians.csv` 把 signed cross 报成 magnitude(丢符号), 已实际误导 reviewer、把相消误读成相长 | 否 | 否(但 mechanism 归因) | **P2**(mechanism-critical reporting bug; 改输出 `median_signed_cross_*`/`median_abs_cross_*`/`cross_term_{negative,zero,positive}_fraction`) |
| 12 | 物理内核(Mie/core-shell 数值引擎) | — | — | 结案(仅引擎) |

---

## 9. 对外 claim-safe 语言(本轮)

```
✅ Mie/core-shell 数值引擎已独立验证(测试 regime 内); 完整光学前向模型未结案。
✅ width 规则 W≳λ/NA 是 **stable engineering guardrail / family heuristic, 不是 detector-resolved
   optimum law**。具体宽度是家族且依产线, 不写单点映射:
   404 → 窄宽家族 ~W500–700 (v1 panel top W600/D1300; W500 激进、W600 更实用);
   660 → ~W700–800 家族 (v1 panel 的 660 top 多被标 reference_too_weak, 仅弱参考对照;
        Lens-B/README 框架为 W800), 待 reference-strength 验证。
✅ depth 取中深 D900–D1200。**注: 这不是 v1 探索 panel 的 raw top-score depth(top 是 D1300/D1500);
   而是 discount 掉 detector/gauge/noise 不确定度 + 流体/堵塞/PEG-accessibility 风险后的
   conservative engineering recommendation。**
⛔ 404 vs 660: no-data 收窄封板门已满足(`R2/V1` A/B/C/D 全 3-seed + A/B 的 V2 抽样 gauge 检验)，
   但在 (1) BFP/slit/reference phase 实测、(2) 标准粒子 ladder、(3) blank trace 前, 只能称
   "candidate families under the current collapse-gauge-locked hybrid-detector surrogate",
   优先级同时依赖 normalization view 与 detector-forward route。
⛔ 不可声明: detector-resolved relative ranking; NODI 外差增强倍数; 真实 SNR/LOD/blank FPR;
   EV 浓度/count rate; 生物 exosome 特异性; 跨波长绝对最优。
⛔ 不可声明: selected-annulus = BFP 光学环 (它是 event-position/分析窗口 lens)。
```

首批芯片建议: 不押单一路线; 至少保留 404 窄宽家族 与 660 较宽家族两组; depth D900–D1200;
同步做 Au20/40/60 ladder + blank BFP/slit scan + EV mimic, 用实测 BFP/photodiode trace
判定真实 detector 更接近 A、B 还是 C。

---

## 10. 多轮审查谁对谁错 — 诚实记录

| 命题 | reviewer A (Claude) | reviewer B (GPT) | 数据裁决 |
|---|---|---|---|
| 物理内核有无 P0 | 无(重算确认) | 无 | ✅ 无 |
| bundle verify 4 failed | 限定为裁剪包内, repo 根 8 passed | 接受修正 | ✅ 裁剪包问题 |
| joint-overlap 半截升级 | 提出(P1-B) | 确认+throughput 细化 | ✅ 成立 |
| detector-integrated lane 存在 | 复核确认全网格分布 | **首先指出 lane 存在** | ✅ GPT 首功 |
| roi_vs_scalar≈5 含义 | 后修正为 B vs C | 钉死 B vs C ≠ A 误差 | ✅ B vs C |
| EV self/cross 主导 | 旧说 self-dominated(过强) | cross-competitive/相长(过强) | ⚖️ 都过头: raw signed cross **为负(相消)**, \|cross\|≈self, net 宽 |
| EV cross 符号 | scan 得负 | 据派生表称为正、质疑 Claude | ✅ raw signed 列**确为负**; 派生表丢了符号(magnitude), reviewer B 被其误导 |
| "production 规避角度相消" | 旧文写了(**错**) | 指出代数错误 | ✅ reviewer B 对: A 与 B 同一 cross 项, 不规避相消 |
| B 是独立 detector truth? | 旧文称 photodiode 强度积分 | 指出 B 被 rescale 到 collapsed target | ✅ reviewer B 对: B 是 gauge-locked surrogate |
| roi_vs_scalar≈5–7 用得过重 | 后修正为 B/C | 钉死缺 A/B | ✅ A/B 未量化 |
| 五路小网格"零代码" | 旧文称几乎零代码 | 指出需 event-trace plumbing | ✅ reviewer B 对 |
| gold self-dominated | 提出 | 接受 | ✅ 成立(|cross|/self≈0.01–0.05) |
| detector identity 未定义 | 隐含 | **明确升为最底层** | ✅ GPT 锐化 |
| heterodyne gauge | **提出(升 P1)** | 接受升 P1 | ✅ Claude 首功 |
| depth 反向校正 | 提出 | 接受 | ✅ 推荐面 depth 弱 |

---

## 附录 A — 复现命令

```bash
# 物理内核独立重算
.venv/bin/python -m pytest tests/test_physics_core.py tests/test_mie_engine.py -q   # 382 passed
.venv/bin/python - <<'PY'   # core-shell collapse / 光学定理 / Rayleigh
from nodi_simulator.mie_engine import mie_coefficients, mie_core_shell_coefficients, mie_compute
import numpy as np
x=3.0;m=1.5+0.01j
a1,b1=mie_coefficients(x,m);a2,b2=mie_core_shell_coefficients(x,0.5,m,m)
print(np.max(np.abs(a1-a2)))            # ~1e-15
print(mie_compute(2.0,1.33+0j))         # Qext==Qsca, Qabs~0
Qs1=mie_compute(0.05,1.5+0j)[1];Qs2=mie_compute(0.025,1.5+0j)[1];print(Qs1/Qs2)  # ~16
PY

# 全网格 detector-route disagreement / self-cross(signed!) / net|signal| / eligibility
#   一条命令复现本报告 §4–§5 的全部数字 (输出输入文件 sha256 前缀作 provenance):
.venv/bin/python tools/audits/recompute_report147_detector_identity_tables.py \
  --v1-summary results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv \
  --lensb-diagnostic \
    results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed11_16worker_20260518/seed_11_fixed_660_gold_diagnostic_rows.csv \
    results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed22_16worker_20260518/seed_22_per_wavelength_gold_diagnostic_rows.csv
#   注: 该脚本同时打印 EV cross 的 signed 中位(负) 与 pos/neg/zero 计数, 以及 net|signal|/self 分位,
#   直接核验「raw signed cross 为负、派生表 mechanism_chain 报的是 magnitude」这一裁决。
#   完整 v1 summary(1.6GB)与 diagnostic_rows 在本地 repo git-tracked, 但不在裁剪外审包内。

# Stage-1 no-data 收窄封板门证据包:
#   results/audits/report148_stage1_preseal_review_20260612/
#   R2/V1 覆盖 A/B/C/D 全 3-seed；A/B 的 R2/V2 作为抽样 gauge 检验。
#   R1 与 C/D×V2 登记为范围外残余假设，而非本轮 no-data 封板阻断项。

# external bundle verify (病因定位)
.venv/bin/python -m pytest tests/test_review_package_manifest.py tests/test_verify_review_package_cli.py -q  # repo 根 8 passed
```

## 附录 B — 关键源码锚点

- 干涉主 trace (hybrid): `nodi_simulator/interferometric_trace.py:98–113, 160–172, 232–256`
- detector-integrated 自洽 lane: `nodi_simulator/bfp_detector_operator.py:116–167, 186–291`, 接入 `parameter_sweep.py:6845`
- overlap_factor: `nodi_simulator/utils.py:3574–3634`
- 角度塌缩 + theta_phase: `nodi_simulator/utils.py:3349–3431`
- reference 角谱 surrogate(含自标 spurious 深度项): `nodi_simulator/reference_field.py:652–785`, A_ref∝depth `:673`
- 归一化 baseline (Au20 gauge): `nodi_simulator/utils.py:4118–4144`
- 阈值: `nodi_simulator/pulse_analysis.py:45–64`
- 噪声(electronics+shot surrogate): `nodi_simulator/parameter_sweep.py:1099–1153`
- Wilson LB/UB: `nodi_simulator/parameter_sweep.py:6166–6184`
- engineering gate: `nodi_simulator/parameter_sweep.py evaluate_engineering_gate`
- eligibility 组合: `nodi_simulator/design_claim_governance.py:594–613`

---

*本报告为 no-measured-data 相对仿真审计在**收窄封板门**下的定稿：
`R2/V1` A/B/C/D 全 3-seed 主判决 + A/B 的 V2 抽样 gauge 检验。
它不授权任何 calibrated SNR/LOD/浓度/blank safety/生物特异性/绝对跨波长最优 claim；
R1 与 C/D×V2 仍列入“模拟可补 / 实测优先”交接清单。
所有定量数字均可由附录 A 的 `recompute_report147_detector_identity_tables.py` 在**本地完整 repo**
(非裁剪外审包)上复现。*
