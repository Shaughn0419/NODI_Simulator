# EV/NODI 综合分析报告 v5.0：从物理链到工程推荐的读者向重构

- 日期：2026-05-11
- 版本：**v5.0（reader-centric full restructure）**——本版以问题 → 物理 → 变量 → 数据 → 分析 → 推荐 → 边界 → 出处的顺序重新组织 v3.0 / v4.0 / v4.1 / v4.2 的内容，把层层叠加的修订序列改写为一条可跟进的叙事线；同时把代码层的 ID（如 `tau_2ms_global_refphi_plus_collection_narrow`、`conditional_relative_main`、`gamma`）替换为可读的科学命名（保留代码 ID 作为括号补注），并在附录 A 给出对照表。
- **所有数值结论、forbidden claim、release status 和冻结参数与 v4.2 完全一致**；本版只重排叙事并改名，不引入新计算、新候选、新 lane、新随机种子、新 solver case、新 experiment、新 measured artifact ingest。
- 报告性质：读者向综合分析报告
- 适用口径：无实测数据 + 合成相对先验模型 + post-v2 审计 / 有界 trace
- 预计阅读时间：完整 60–90 分钟；按 §0.3 路径建议跳读 25–40 分钟

---

## §0 阅读须知

### 0.1 这份报告是什么、不是什么

**是**：在没有任何实测采集数据的前提下，把物理推导、surrogate 模型、估计参数与多轮审计证据按读者直觉串起来，给出 EV / NODI 工程主线推荐 + Tsuyama 论文审计推荐 + 边界声明的读者向综合分析。

**不是**：

- 不是实验报告（没有实测）
- 不是仪器校准报告（没有 calibrated SNR / LOD / 浓度）
- 不是论文完整复现（Tsuyama 数值的复现只到 reproduction-lens partial，没有 accepted paper-calibrated candidate）
- 不是生物学论证（没有 biological specificity claim）

### 0.2 双口径并立

本报告同时回答两个并立问题，**互不替代**：

```text
口径 A — 工程主排序
        问题：在 32,032 设计组合 × 8 仪器情景的合成相对先验模型内，
              EV / NODI 工程路线如何排序、主路线选哪一组几何？
        主分母：全 back-focal-plane 全 crossing
        颗粒：EV biomimetic + Au20/Au30 anchors
        当前推荐：660 nm + 通道宽 800 nm × 通道深 1400 / 1500 nm 的双 main 集合

口径 B — 论文审计
        问题：在 selected-annulus 0.5–0.8 固定窗口下，
              当前 simulator 的低自由度估计参数能否自然复现 Tsuyama 论文数值？
        主分母：selected-annulus 0.5–0.8
        颗粒：Au 20 / 30 / 40 / 60 nm + Ag 40 / 60 nm
        当前推荐：两步框架——
                step 1 用 Tsuyama 数据校准估计参数（γ ≈ 0.749 等），
                step 2 在校准 lens 内选几何 = 660 / 800 × 550 + 660 / 1200 × 550
```

把口径 A 的工程几何当作口径 B 的论文审计结论、或把口径 B 的估计参数当作物理常数推广到口径 A 工程库，都属于 §15 forbidden claim。

### 0.3 阅读路径建议

| 你的角色 | 建议路径 | 大致用时 |
|---|---|---:|
| 第一次阅读 | §0 → §1 → §2 → §6 → §10 或 §11（按你的口径）→ §15 | 25–40 分钟 |
| 工程评审 / 审计 | §1 → §3 → §4 → §5 → §7 → §9 → §10 → §15 → §17 | 50–70 分钟 |
| 论文对照 | §6 → §11 → §14 → §15 | 30–40 分钟 |
| 边界与治理 | §12 → §13 → §15 → §16 → §18 | 25–35 分钟 |
| 出处溯源 | §17 → 附录 A → §18 | 15–25 分钟 |
| 完整通读 | §0 → §18 → 附录 A/B/C | 60–90 分钟 |

### 0.4 v5.0 与之前版本的关系

- v3.0：仅口径 A，selected-annulus 仅一处指针提及
- v4.0：双口径并立、§14 selected-annulus 等规模并入、§15 双口径综合
- v4.1：新增 §16 读者向解读层
- v4.2：§16 改两步框架 + §16.3 / §16.4 改 ms / % 多表
- **v5.0**：**全文 reader-centric 重构**。把 v3 → v4.2 的叠加痕迹清掉，按问题 → 物理 → 变量 → 数据 → 分析 → 推荐 → 边界 → 出处的顺序重排；把代码层参数 ID 改名为可读科学命名（附录 A 给出对照表）。**数值与 forbidden 完全继承 v4.2，没有放宽任何边界**。

### 0.5 v5.0 重构的不变量（invariants，不会被改名 / 改顺序改变的事实）

```text
1. 全部数值结论与 v4.2 一致
2. 全部 forbidden claim 与 v4.2 一致（§15）
3. 口径 B 冻结参数集与 v4.2 一致（§11.7）
4. 双口径并立、互不替代的治理原则与 v4.0 起一致
5. selected-annulus 0.5–0.8 固定不可移动
6. raw provenance 来源不变：reports/49（口径 B Phase 2 / 2.5–2.11）+ reports/71（R5.2 sidecar）
```

---

## §1 项目要解决的两个并立问题

### 1.1 问题 A — EV / NODI 工程主线推荐

在以下候选范围内挑出最适合作为 EV / NODI 工程主线的几何 + 波长组合：

```text
波长候选：404 / 488 / 532 / 660 nm
通道宽度候选：11 个值（500 / 600 / 700 / 800 / 900 / 1000 / 1100 / 1200 / 1300 / 1400 / 1500 nm）
通道深度候选：13 个值（覆盖 500–1500 nm）
颗粒类型候选：56 种（EV biomimetic 系列 + Au 20–300 nm anchors）
合计：32,032 个基础设计组合
```

**"最适合"在本报告内的精确意思**：在合成相对先验模型 + 8 个仪器情景下，detection 数字稳定、近壁条件下网格证据充分、对低自由度风险先验解释鲁棒、并且没有被路线治理审计降级到对替代量级敏感 (`surrogate_sensitive_not_promoted`) 状态。

**它不是**：不是"detection 数字绝对最高"。§10.4 会显示，detection 数字最高的反而是 500 nm 宽窄通道路线（19.6% 在 660 / 500 × 1500 nm），但它们在路线治理裁决后被标为 `surrogate_sensitive_not_promoted`——原因是窄通道工程风险在原模型中被低估（§10.4 详解 width-prior 风险先验）。

### 1.2 问题 B — Tsuyama 论文数值能否被估计参数复现

Tsuyama 等 2019 / 2020 / 2022 / 2024 共 6 篇论文给出了 NODI / POD 检测的若干**论文数值**：

```text
Table S1 Ag40 / Au40 signal ratio（按散射截面开方列）
Au 粒径响应斜率 ≈ 2.3
Au30 / Au20 SNR 比 ≈ 33 / 12 ≈ 2.75
Au20 / Au30 / Au40 / Au60 selected-annulus detection 带
selected-annulus 几何 guardrail
classification accuracy 71.9 ± 4.0%（diagnostic only）
```

**问题 B 的边界条件**：

```text
不修改 selected-annulus 0.5–0.8 窗口
不回写 EV 工程主线
不开 per-diameter / per-geometry / per-case correction
只允许低自由度全局估计参数
```

在这组边界内回答：能否自然复现？

**当前结论（详见 §11）**：partial。formula-consistent Ag / Au signal 已通过；raw Au peak-height exponent 最低 3.0335（target 2.3，limiting size pair 40–60 nm）；total reproduction score 2.033（bounded partial 阈值 2.0）。所以 v4.0 起把当前参数集冻结为口径 B 选型，**不再追更低分**，要继续推进必须靠实测 artifact。

### 1.3 为什么是两个并立问题、不是一个？

| 维度 | 口径 A：工程主排序 | 口径 B：论文审计 |
|---|---|---|
| 目标 | EV / NODI 工程整体路线排序 | Tsuyama 论文数值复现可行性 |
| 主分母窗口 | 全 BFP 全 crossing | selected-annulus 0.5–0.8 |
| 候选规模 | 32,032 设计 × 8 情景 = 256,256 行 | 约 52 paper-audit candidates × 3 seeds |
| 颗粒 panel | EV biomimetic + Au20 / Au30 anchors | Au 20 / 30 / 40 / 60 + Ag 40 / 60 nm |
| 主推几何 | 660 nm + 800 × 1400 + 800 × 1500 nm | 660 nm + 800 × 550 + 1200 × 550 nm |
| 当前 release | `conditional_relative_main` 集合 | `negative_or_diagnostic_result_only` |
| 主 No-Go | 无（已收口）| `raw_size_response_alignment_not_met` |

两套候选不一样、分母不一样、回答不一样的问题，所以**不能把一边的结论搬到另一边**。后面 §10 / §11 各自展开。

---

## §2 物理链：粒子如何变成一个 detection event

本节回答"信号是从哪里来的、经过哪些环节"。读完本节，读者应该能跟着一条公式链算下来，并理解 §11.2 关键问题"**本征散射 |E_sca|² 与干涉项 2|E_ref||E_sca|cos(Δφ) 是相加还是相乘？**"的答案为什么是相加。

### 2.1 链条总览（7 阶段）

```text
[阶段 1] 粒子本征散射（Mie 散射）
            产物：散射截面 Csca、角度散射振幅 S1(θ), S2(θ)、收集前场幅值 |E_sca,unit|
            源代码：nodi_simulator/mie_engine.py + intrinsic_scattering.py
                ↓
[阶段 2] 角度收集（探测算子 L_det）
            产物：被收集的检测端散射场 E_sca,detected
            源代码：nodi_simulator/utils.py 中 build_collection_operator + collapse_angular_field_with_operator
                ↓
[阶段 3] 照明 + 路径相位 + 耦合 → 事件级散射场
            产物：事件随时间的散射场 E_sca(t)
            源代码：nodi_simulator/scattering_trace.py + illumination.py
                ↓
[阶段 4] 通道参考场（Tsuyama BFP / channel-angular surrogate）
            产物：事件随时间的参考场 E_ref(t)
            源代码：nodi_simulator/reference_field.py
                ↓
[阶段 5] 干涉叠加 → signal_trace
            产物：signal_trace(t) = |E_ref + E_sca|² - |E_ref|²
            源代码：nodi_simulator/interferometric_trace.py
                ↓
[阶段 6] 噪声 + 锁相读出
            产物：post-readout 信号
            源代码：nodi_simulator/pulse_analysis.py (与 reference 的 lock-in surrogate 部分)
                ↓
[阶段 7] 阈值 + 脉冲提取 + batch 统计
            产物：detection_rate, mean_peak_margin_z, phase_flip_fraction, ...
            源代码：nodi_simulator/pulse_analysis.py + count_generation.py
                ↓
[最终] 按 lens 分组：
       口径 A 看 all_crossing_detection_rate
       口径 B 看 selected_annulus_detection_rate
```

### 2.2 每个阶段的公式与物理量含义

**阶段 1 — Mie 本征散射**

```text
散射截面：Csca = Qsca · π a²    （a = 粒径半径）
角度散射场幅值（非偏振平均）：dCsca / dΩ = (|S1|² + |S2|²) / (2 k²)
场幅值代理：|E_sca,unit(θ)| = √(dCsca / dΩ)
```

读法：粒子越大、折射率反差越大、波长越短（在 Rayleigh 区），Csca 越大。对 EV biomimetic 这种低反差颗粒，Csca ≈ 1 / λ⁴（Rayleigh 极限）；对 Au plasmonic 颗粒，Csca 在等离激元共振附近（约 520 nm）局部增强，所以 Au 在 660 nm 的 Csca 反而比 488 nm 大。

证据档位（§13 6 档来源谱）：**Mie 推导值（第 2 档）**，由物理常数 n、k、λ、π 直接算出。

**阶段 2 — 角度收集**

```text
E_sca,detected = L_det[ field_sca(θ, φ) ]    （L_det = 当前 surrogate 收集算子）
```

`L_det` 在 v4.0 / v4.2 / v5.0 内仍是 surrogate（默认 `channel_diffraction + pupil_slit_surrogate + parallel projection`），它把完整角度散射图压成一个由 BFP / slit / pinhole 决定的收集场。它**不是**完整 pupil integral，所以收集量级是 surrogate 估计，不是 calibrated detector unit chain。

证据档位：**Surrogate 估值（第 3 档）**。

**阶段 3 — 照明 + 路径相位 + 耦合 → 事件级散射场**

```text
E_sca(t) = E_env(t) · E_sca,unit · f_coupling(t) · exp(i · φ_extra(t))
```

其中 `E_env(t)` 是照明场（默认 `overfill` 模式），`f_coupling(t)` 是 Gaussian xy 耦合，`φ_extra(t)` 包括路径 OPD 与焦点穿过相位。这一步把"静态散射场"转成"事件随时间的散射场"。

证据档位：第 3 档（surrogate 估值）。

**阶段 4 — 通道参考场**

```text
E_ref(t) ~ L_det[ E_diff,ch ]
```

当前默认参考场模型是 `channel_angular_surrogate`（通道角谱 surrogate）。NODI 主链看的是参考场和散射场的**干涉**，不是单独的 `|E_sca|²`。

证据档位：第 3 档（surrogate）。在 reports/49 / 71 / Phase 2 lane 内有 `paper_aligned_phase_filter` 与 `tsuyama_bfp_roi_mode` 等更接近论文条件的 reference 变体；当前主报告 reference 模型对论文条件做相位滤波对照，相对误差 ≈ 2–9%（§6.3 表）。

**阶段 5 — 干涉叠加**（**关键公式，§2.3 / §11.4 都引用它**）

```text
E_det(t)       = E_ref(t) + E_sca(t)
I_det(t)       = |E_det(t)|²
signal_trace(t)= I_det(t) - |E_ref(t)|²
              = |E_sca|² + 2 · Re( E_ref · E_sca* )
                  ↑        ↑
              本征二次项   参考场放大的一次干涉项
```

**这一行就是问题"本征 vs 干涉是相加还是相乘"的答案**：**严格意义上是相加**——两项简单叠加，不是相乘。但量级关系按 |E_ref| / |E_sca| 的比值分三个极限：

| 极限 | \|E_ref\| / \|E_sca\| | 主导项 | peak 量级 |
|---|---|---|---|
| 弱参考场 | ≪ 1 | 本征二次项 \|E_sca\|² | peak ∝ Csca |
| 平衡 | ≈ 1 | 两项可比 | peak ≈ \|E_sca\|² + 2\|E_ref\|\|E_sca\|cos(Δφ) |
| **强参考场**（当前模型 + Tsuyama 论文条件） | ≫ 1 | **干涉一次项** | **peak ≈ 2 · \|E_ref\| · \|E_sca\| · cos(Δφ) ≈ \|E_ref\| · √Csca** |

所以"参考场放大 N 倍 × 本征 Csca 翻 M 倍 = 总放大 N · M"是**错的直觉**。在当前强参考场口径下，peak 大致跟 |E_ref| · √Csca，**不是** |E_ref| · Csca。

**阶段 6 — 噪声 + 锁相读出**

噪声进入位置：

```text
干涉 signal_trace
    ↓
[pre-readout 噪声] 高斯 + 散粒 (shot-noise surrogate) + 漂移 surrogate
                 默认: noise_std = 0.01, shot_noise_scale = 0.001
    ↓
锁相读出 lock-in surrogate（时间常数 1–2 ms；in-phase / magnitude / phase-gated）
    ↓
[post-readout 噪声] 默认: post_readout_noise_std = 0.002
    ↓
输入到阈值
```

**关键观察**：参考场放大的是相干一次项（signal 端），**不放大噪声**（噪声没有相干相位）。但 noise floor 不是常数：

- 阈值用背景的 MAD 估计；noise↑ → 阈值↑ → detection↓
- 短波长 transit 时间窗变小 → 锁相有效样本数变少 → margin z 变小
- phase flip fraction 在短波长更高（OPD 抖动相对 λ 占比更大）

这就是 §8 / §11.4 / 用户曾问"为什么参考场放大那么多倍噪声还重要"的答案：noise 不被放大，但 noise 决定阈值，阈值决定 detection；transit 与 phase flip 还会进一步压低短波长的 detection。

**阶段 7 — 阈值 + 脉冲提取 + batch 统计**

```text
threshold = median(background[:n_bg]) + threshold_sigma · 1.4826 · MAD(background[:n_bg])
默认: threshold_sigma ∈ {5, 10}, n_bg = first 20% samples

find_peaks(signal_post_readout):
    height   ≥ threshold
    width    ≥ min_peak_width   （Phase 2 paper-audit lane: 2.0–3.0 ms）
    distance ≥ min_peak_interval

batch 输出:
    detection_rate / stable_detection_rate / mean_peak_height / mean_peak_margin_z
    phase_flip_fraction / roc_auc_event_vs_background / d_prime_event_vs_background
```

最后按 lens 分母选择是 all-crossing 还是 selected-annulus（§4 详解）。

### 2.3 关键问题答覆：本征散射 + 干涉项 是相加还是相乘？

直接答：**相加**（§2.2 阶段 5 公式）。

但在强参考场极限（**当前模型 + Tsuyama 论文条件就在这里**）下，干涉一次项 `2|E_ref||E_sca|cos(Δφ)` 主导，本征二次项 `|E_sca|²` 被淹没。所以读者直觉中的"参考场放大 × 本征 Csca 翻倍 → 总倍数相乘"是错的；正确量级关系是：

```text
peak ≈ 2 · |E_ref| · |E_sca| · cos(Δφ)
     ≈ |E_ref| · √Csca · (cos Δφ 的运行平均)
```

注意 √Csca 不是 Csca。所以波长把 EV biomimetic 颗粒 Csca 翻 7.1x 时（404 vs 660 nm，Rayleigh 1/λ⁴），peak 大致只放大 √7.1 ≈ 2.66x（再乘 |E_ref| 的几何因子约 1.04x 与 cos Δφ 平均），实际只约 2x。这就是为什么 404 nm 的 peak 增益远比 Csca 增益小。

### 2.4 强参考场极限下的具体放大表（404 vs 660 nm，EV biomimetic + 相同几何）

| 量 | 660 nm 基线 | 404 nm 相对值 | 物理 / 推导来源 |
|---|---:|---:|---|
| Mie 散射截面 Csca | 1.00× | 7.10× | EV Rayleigh: (660/404)⁴ = 7.10 |
| 收集场幅值 \|E_sca\| | 1.00× | 2.66× | √Csca |
| 参考场幅值 \|E_ref\| | 1.00× | ≈ 1.04× | §6.3 衍射对照（404/500×800 = 0.968×，660/800×550 = 1.000×；倒着读 404 比 660 略大）|
| 干涉一次项 2\|E_ref\|\|E_sca\| | 1.00× | ≈ 5.5× | 1.04 × 2.66 × 2 |
| 实际 peak（含 cos Δφ 平均，约 0.4 量级）| 1.00× | ≈ 2.0× | 用户曾给出的示例表 2.01× 同 order |
| transit 时间窗（与几何无关，只看 λ） | 8.94 ms | 5.48 ms (≈ 0.61×) | beam waist ∝ λ/NA → 短波 transit 短 |
| 综合 detection | 1.00× | ≈ 0.4× | §6.4 表 B / §7.1：peak 翻倍但 transit↓、phase flip↑、margin↓ → detection 反而下降 |

读法：peak 放大 2×、detection 反而降到 0.4× —— 这就是问题 Q4（"peak 放大 N 倍，detection 是否同步放大"）的答案：**不同步**，原因详见 §8 噪声归因。

---

## §3 可调变量与它们的物理含义

本节给变量做一次正名 + 解释。读完本节，读者应该能把后面 §7 / §10 / §11 出现的每个变量映射回它在 §2 物理链上的位置。

### 3.1 颗粒变量

| 变量 | 单位 | 默认 / 主推范围 | 在 §2 物理链上的位置 | 影响 |
|---|---|---|---|---|
| 颗粒材料 | 折射率 n, k 谱 | EV biomimetic（生物拟态低反差）/ Au（金 plasmonic）/ Ag | 阶段 1 Mie | **影响最大的变量**（§9 排名 1）；EV 与 Au 在 488–660 nm 的 Csca 走向**相反** |
| 颗粒粒径 | nm | EV biomimetic 50–150 nm；Au 20 / 30 / 40 / 60 nm（口径 B 主 panel） | 阶段 1 Mie | Csca ∝ a⁶ 在 Rayleigh 区；Au20 vs Au60 Csca 差 ≈ 1200× |

### 3.2 光学变量

| 变量 | 单位 | 默认 / 主推范围 | 在 §2 物理链上的位置 | 影响 |
|---|---|---|---|---|
| 探测波长 λ | nm | 候选 404 / 488 / 532 / 660 | 阶段 1、2、3、4 | EV Rayleigh 颗粒：短波 Csca↑；Au plasmonic：长波 Csca↑（共振红移到约 520 nm）|
| 收集 NA | — | 0.9（Tsuyama 2020 / 2022 论文条件，本报告对照口径） | 阶段 2 探测算子 | 影响 \|E_sca\|；当前 surrogate 不是绝对 NA 校准 |
| 照明 NA | — | 0.45（Tsuyama 2020 物镜，沿用至 2022） | 阶段 3 照明 | 决定 beam waist → transit time |
| 流速 | mm/s | 0.2（Tsuyama 2022 NODI 论文条件） | 阶段 3 / transit | 与照明 NA 一起决定 transit 时间 |
| 参考场模型 | — | `channel_angular_surrogate`（主线）/ `paper_aligned_phase_filter`（论文条件对照）| 阶段 4 | 与论文条件相对差异 ≈ 2–9%（§6.3）|

### 3.3 几何变量

| 变量 | 单位 | 候选范围 | 在 §2 物理链上的位置 | 影响 |
|---|---|---|---|---|
| 通道宽度 W | nm | 500 / 600 / 700 / **800 (main)** / 900 / 1000–1500 | 阶段 4 参考场、阶段 3 路径相位 | 窄通道 Csca 数字高但工程风险也高（§10.4 width-prior）|
| 通道深度 H | nm | 550 (Tsuyama 论文 depth) / 800 / 1200 / 1300 / **1400 (main)** / **1500 (main)** | 阶段 4 参考场、阶段 3 路径 | H 在 1200–1500 nm 区间内 detection 已基本饱和 |

### 3.4 电子学变量

| 变量 | 单位 | 默认 | 在 §2 物理链上的位置 | 影响 |
|---|---|---|---|---|
| 锁相时间常数 τ | ms | 1–2（Tsuyama 2022 NODI / 2020 counting POD 论文）| 阶段 6 锁相 | 决定有效锁相样本数；transit / τ ≈ 锁相 bin 数 |
| 读出方式 | — | in-phase（默认）/ magnitude / in-phase + phase-gated | 阶段 6 | 在 pass / fail 边界上影响巨大，但 mean detection 几乎不变（§6.4）|
| 阈值倍数 threshold_sigma | — | {5, 10}（Phase 2 paper-audit 限定） | 阶段 7 | 阈值 = median + threshold_sigma · 1.4826 · MAD |
| 最小 peak 宽度 min_peak_width | ms | 2.0–3.0（Phase 2 paper-audit 限定） | 阶段 7 | metadata guardrail，不一致就 fail fast |
| 相位翻转硬剔除 phase_flip_hard_reject | — | false | 阶段 7 / batch | 当前不硬剔除负 peak，但极性保存为字段 |

### 3.5 仪器情景变量（v2 受限仪器情景先验，无实测）

v2 在原 v1 基础设计组合之上，把每个 case 放入 8 个**受限仪器情景**里做确定性扩展。它**不是**真实采集，**不引入任何 measured artifact**——是 noise / blank / readout 路径的先验分布扫描，用于看路线角色稳定性。

```text
情景 1：标称仪器 + 干净空白样本
情景 2：50 Ω 探测器路径的悲观情况
情景 3：外置 TIA（current input + low-noise transimpedance amplifier）的乐观情况
情景 4：空白样本中存在突发强度噪声
情景 5：后焦面 / 狭缝偏移带来的泄漏风险
情景 6：PEG 或近壁损失更悲观的情况
情景 7：404 nm 热效应风险较高、功率较低的情况
情景 8：数据采集分辨率较低的情况
```

8 个情景 × 32,032 设计 = 256,256 合成评估行。

### 3.6 估计参数（口径 B 复现 lens 估计项）

这些不是物理常数，不是 surrogate，是用 Tsuyama 论文 target 反推出的低自由度全局参数；§11.2 给出它们的具体校准过程。

| 估计参数 | 描述名 | 代码 ID | 数值 | 含义 |
|---|---|---|---|---|
| γ | 全局响应压缩因子 | `paper_reproduction_response_compression_gamma` | 0.749 | 把 raw 模型 peak 高度按 (peak)^γ 重映射，让 Au 粒径响应斜率从 raw 3.05–3.19 落到 Tsuyama 论文的 2.3 |
| s_SNR | 全局 SNR 缩放因子 | `paper_reproduction_global_snr_scale` | 0.728 | 把 Au20 / Au30 局部 SNR 平移到 Tsuyama 论文 anchor |
| e_SNR | 全局 SNR 响应指数 | `paper_reproduction_snr_response_exponent` | 0.812 | Phase 2.7 引入；调节 SNR ratio 的相对 scaling |
| 选定算子 | 2 ms 锁相 + 全局参考相位正向位移 + 窄收集窗 | `tau_2ms_global_refphi_plus_collection_narrow`（D2.1 局部 smoke 内最优）| — | 选定的探测算子配置；不是物理仪器接法，是 surrogate operator |

**重要边界**（§13 / §15 重申）：这 4 项都是**复现 lens 估计项（第 4 档证据）**，禁止解读为仪器物理常数。

---

## §4 检测率有 4 种含义

读者最容易踩的坑：同一个"detection %"在本报告里其实可能是 4 种不同的量。本节把它们一次性厘清。

### 4.1 all-crossing detection rate（口径 A 主排序）

```text
all_crossing_events     = { event i | event 横穿模拟检测区 }
all_crossing_detection_rate = n_detected(all_crossing_events) / n(all_crossing_events)
```

- 分母：横穿检测区的所有 event（不挑分母 condition）
- 用途：口径 A 主排序、工程 gate、main-660 治理
- 典型数字：12.5–20% 范围（EV biomimetic + 8-scenario avg）
- 出现位置：§6.4 表 6.4.A、§7.2 各表等

### 4.2 selected-annulus detection rate（口径 B 主审计）

```text
edge_norm_i = max( |x_norm_i|, |z_norm_i| )       # 粒子横截面位置归一化
selected_annulus_events = { event i | 0.5 ≤ edge_norm_i ≤ 0.8 }
selected_annulus_detection_rate = n_detected(selected_annulus_events) / n(selected_annulus_events)
```

- 分母：横穿检测区且初始位置在通道边缘 0.5–0.8 比例环带的 event
- 用途：Tsuyama 2022 NODI 论文有效采样区语义、口径 B paper-audit lane
- 典型数字：分子分母同步缩小，平均 uplift ≈ 1.384× 相对 all-crossing
- 关键 forbidden：不替代 all-crossing 主排序（§15）

### 4.3 NODI engineering lens stable detection rate

来自 §6.4 表 6.4.B 的 NODI engineering lens（17 strict-pass cases）mean stable detection；它是"通过 strict NODI engineering gate 的 case 子集上的平均稳定 detection"。和 all-crossing 主排序的 8-scenario avg 不可直接比较（分母不同）。

- 典型数字：33–47%
- 出现位置：§6.4 表 6.4.B、§7.1.1 / §7.1.2 / §7.1.3 等

### 4.4 paper-audit reproduction score（口径 B Phase 2.6+ 复现 lens）

这**不是 detection 量**，是 paper-audit lane 的 lower-is-better penalty score（多个 loss 项加权）：

```text
reproduction_score = SNR_ratio_loss + SNR_anchor_loss + formula_signal_loss
                   + size_response_loss + detection_loss + complexity_penalty + strict_residual
```

- 用途：口径 B Phase 2.6–2.11 选 candidate
- 阈值：bounded partial 阈值 ≤ 2.0；当前 best 2.033（partial reproduction descriptive 级别）
- 关键 forbidden：不能按"分数越高越好"解读；不能当作物理量

### 4.5 4 种数字何时可比 / 何时不可比

| 比较 | 是否可比 | 注 |
|---|---|---|
| 同一 lens 不同几何 | ✅ 可比 | 例：660 / 800 × 1400 vs 660 / 800 × 1500 都在 all-crossing |
| 同一 lens 不同波长 | ✅ 可比（前提是同一颗粒 panel）| 例：488 / 532 / 660 都在同一 selected-annulus Au panel |
| 同一 lens 不同颗粒 | ⚠️ 谨慎 | EV biomimetic vs Au 是不同 panel |
| all-crossing vs selected-annulus | ❌ 不直接可比 | 分母不同；只能看 uplift ratio |
| all-crossing vs NODI engineering lens | ❌ 不直接可比 | 不同 lens 不同分母 |
| reproduction score vs detection % | ❌ 不直接可比 | 一个是 loss、一个是 rate |

所以表里每个 detection 数字必须显式标 lens；同一表里**只能**放同 lens 的数字；不同 lens 数字并排出现时必须分列。

---

## §5 计算与审计 study design

本节回答"我们到底做了什么计算和审计"。读完本节，读者应该能回答"这些数字是怎么生成的、用了多少 events、跑了多少种子"。

### 5.1 v1 全量库（基础计算）

```text
扫描参数空间：32,032 个基础设计组合
每个组合的随机事件数：10,000 events
合计事件级 case 量：3.2 × 10⁸ events
单 case 跑随机种子：1 (precompute 用 case_keyed_independent 随机流)
```

v1 给出：每个 case 的 detection_rate / mean_peak_height / phase_flip_fraction / ROC AUC 等。这是后续所有 lens 的原料。

### 5.2 v2 仪器情景扩展（不重新跑随机事件）

```text
v1 基础设计组合 × 8 仪器情景 = 256,256 合成评估行
新增随机种子：0（确定性扩展，不重 sample）
```

8 情景见 §3.5。v2 的作用是**看路线角色稳定性**，不是生成新事件概率。

### 5.3 post-v2 P0–P18 审计 + 6 条有界 trace（口径 A）

| 阶段 | 类型 | 关键数字 |
|---|---|---|
| P0 | mandatory audit | 572 个路线聚合审计行；563 surrogate-sensitive_not_promoted；2 main candidates；1 weak control；1 optional probe；1 shortwave probe |
| P1 | physical-ceiling diagnostic contracts | 4 条合同（full-wave、vector/Jones、roughness、transport）；surrogate-risk reduction only，不跑 solver |
| P2 | bounded physical-solver readiness | route universe + source binding + schema manifest + verifier；solver execution blocked |
| P3 | minimal pilot design | 选 P4 / P6 后续使用的 3 条路线子集 |
| P4 | dry-run preflight | mesh 标记 `not_generated_no_mesh_generation` |
| P5 | authorization gate | 默认 `not_authorized_pending_explicit_later_phase_execution_request` |
| P6 | bounded trace 1（minimal bounded Green kernel）| 顺序：800 × 1400 > 800 × 1500 > 404 probe |
| P8 | bounded trace 2（phase-gradient）| 同上顺序 |
| P10 | bounded trace 3（curvature-balance）| 800 × 1500 > 800 × 1400 > 404 probe（main-660 首位反转）|
| P12 | bounded trace 4（resonance-compactness）| 同 P10 |
| P14 | bounded trace 5（phase-curvature residual）| 800 × 1400 > 800 × 1500 > 404 probe（再反转）|
| P16 | bounded trace 6（phase-curvature residual）| 800 × 1500 > 800 × 1400 > 404 probe |
| P17 | 第七 lane 授权设计 | 记录 P12→P14 与 P14→P16 都出现 rank delta [−1, +1, 0] |
| P18 | synthesis stop / continue | `bounded_lanes_sufficient_for_route_promotion = false`；停止机械式 lane 滚动；要求 P19 evidence-strategy gate |

### 5.4 Phase 2 Tsuyama 论文审计 lane（口径 B）

```text
Phase 2 family-ladder full inverse:
    52 candidates × 3 seeds × 10,000 events / case
    156 summary rows、5616 raw rows、runtime ≈ 6.94 h
Phase 2.5 D2 raw-operator (operator family D2):
    20 candidates × 3 seeds × 1,500 events / case = 60 summary rows
Phase 2.5 D2.1 local smoke (D2.1 局部 12 variants):
    12 candidates × 3 seeds × 2,000 events / case = 36 summary rows
Phase 2.6–2.11 reproduction lens 链:
    单 size-only F-family 3,000 events / case (12 summary rows)
    其余为 read-only rescore（不重跑 simulation）
```

Phase 2 / 2.5 / 2.6 / 2.7 / 2.8 / 2.9 / 2.10 / 2.11 的具体作用见 §11.2。

### 5.5 仪器可行性估算 + 论文统计敏感性

```text
ET-2030 + LI5640 instrument-aware feasibility:
    216 配置（responsivity × NEP × 0.4 mm 有效面 × time constant × filter-order 先验）
    输出：current input/TIA 与 50 Ω voltage path 双列 verdict

Paper-statistics sensitivity (Phase 2.10 limiting-pair 只读估算):
    288 行
    输出：paper_statistics_unlikely_alone / paper_statistics_borderline
```

**重要边界**：这两组数据是**量级估计 + 只读估算**，不是 calibrated SNR / LOD。

---

## §6 物理量级与核心数据

本节集中放整份报告的核心数据，按"transit → Csca → \|E_ref\| → detection"顺序排。这些数字会在 §7 / §10 / §11 反复引用。

### 6.1 transit 时间随波长（物理推导）

```text
公式: transit ≈ 2 · w_0 / v_flow
推导假设: w_0 = 0.61 · λ / NA  (Airy radius)
          NA = 0.45 (Tsuyama 2020 / 2022 illumination objective)
          v_flow = 0.2 mm/s = 200 nm/ms (Tsuyama 2022 NODI 流速)
```

| 探测波长 λ (nm) | beam waist w_0 (nm) | transit 时间 (ms) | 相对 660 nm |
|---:|---:|---:|---:|
| 404 | 547.7 | 5.48 | 0.61× |
| 488 | 661.4 | 6.61 | 0.74× |
| 532 | 721.2 | 7.21 | 0.81× |
| 660 | 894.4 | 8.94 | 1.00× |

证据档位：**Mie / 物理推导（第 2 档）**。

读法：短波长 transit 短，意味着锁相在同一 τ = 1–2 ms 下的有效采样数变少（404 nm 的 transit / τ ≈ 2.7–5.5，660 nm ≈ 4.5–8.9）；这是 detection 不能跟 peak 同步放大的根本原因之一。

### 6.2 Csca 随波长（EV biomimetic vs Au，两种颗粒走向相反）

#### 6.2.1 EV biomimetic（Rayleigh 区，低反差）

```text
近似: Csca ∝ 1 / λ⁴
基线: 660 nm = 1.00×
```

| λ (nm) | EV Csca 相对 660 | 推导 |
|---:|---:|---|
| 404 | 7.10× | (660 / 404)⁴ |
| 488 | 3.34× | (660 / 488)⁴ |
| 532 | 2.37× | (660 / 532)⁴ |
| 660 | 1.00× | 基准 |

#### 6.2.2 Au plasmonic（共振红移到 ≈ 520 nm，方向相反）

| λ (nm) | Au Csca (m²) | Au Csca 相对 660 | 来源 |
|---:|---:|---:|---|
| 488 | 2.86 × 10⁻¹⁶ | 0.43× | §7 直接行（4 几何 mean）|
| 532 | 3.93 × 10⁻¹⁶ | 0.59× | 同上 |
| 660 | 6.66 × 10⁻¹⁶ | 1.00× | 同上 |

**Au 颗粒粒径阶梯**（660 / 800 × 500 nm）：

| 粒径 a (nm) | Au Csca (m²) | 相对 a = 20 nm |
|---:|---:|---:|
| 20 | 2.019 × 10⁻¹⁸ | 1× |
| 30 | 2.499 × 10⁻¹⁷ | ≈ 12× |
| 40 | 1.577 × 10⁻¹⁶ | ≈ 78× |
| 50 | 6.956 × 10⁻¹⁶ | ≈ 345× |
| 60 | 2.449 × 10⁻¹⁵ | ≈ 1213× |

**关键观察**：Au 颗粒 Csca 在 20→60 nm 跨 1200×，但后面 §6.4 / §7.3 表会显示 detection 只从 0% 升到 31.5%（**没有同步翻 1200×**）。原因是 Au20 远低于阈值、Au40+ 已接近 detection 上限饱和；详见 §8。

### 6.3 \|E_ref\| 随几何（§6.2 衍射对照已有数据）

来自原 §6.2 Tsuyama 2020 diffraction 论文条件对照，按 660 / 800 × 550 nm 为基线归一：

| 探测波长 λ | 通道几何 W × H (nm) | \|E_ref\| 相对 660 / 800 × 550 | 解读 |
|---|---|---:|---|
| 404 | 500 × 800 | 0.968× | 差异小 |
| 404 | 500 × 900 | 0.960× | 差异小 |
| 404 | 500 × 1200 | 0.930× | 深通道偏差开始明显 |
| 404 | 500 × 1400 | 0.908× | 深窄短波偏差最大 |
| 660 | 800 × 550 | 1.000× | 基准（Tsuyama 论文几何）|
| 660 | 800 × 1400 | 0.963× | 差异小 |
| 660 | 900 × 1200 | 0.976× | 差异小 |

平均绝对差异 ≈ 2.13%，最大绝对差异 ≈ 9.20%。

读法：**\|E_ref\| 在所考察范围内几乎不随波长 / 几何剧烈变化**（差异 < 10%）。所以波长引起的 peak 放大主要来自 \|E_sca\| 项（即 √Csca），不是 \|E_ref\| 项。

### 6.4 detection 数字大表（按 lens 分组的 v4.2 已直接发布行）

下面把 v4.2 / v5.0 报告涉及的所有直接发布 detection 行汇总在一张大表，按 lens 分组。**禁止跨 lens 直接比较**（详见 §4.5）。每行的 detection 数值都是 v4.2 已公开的（仅做 0.xxx → x.xx% 单位换算）。

#### 表 6.4.A — 口径 A 主排序：EV biomimetic + all-crossing 8-scenario avg (mean relative-prior detection score)

| 几何 (λ / W × H, nm) | events 来源 | detection (%) | 路线最终角色（P0 audit） | 来源 |
|---|---|---:|---|---|
| 660 / 500 × 1200 | R5.2 audit (660_500x1200) | 17.39 | context, surrogate_sensitive_not_promoted | §12.2 |
| 660 / 500 × 1300 | R5.2 audit | 18.26 | context, surrogate_sensitive_not_promoted | §12.2 |
| 660 / 500 × 1400 | R5.2 audit | 18.97 | context, surrogate_sensitive_not_promoted | §12.2 |
| 660 / 500 × 1500 | R5.2 audit | 19.64 | context, surrogate_sensitive_not_promoted（ratio_vs_main 1.557）| §12.2 |
| 660 / 600 × 1500 | R5.2 audit | 16.55 | context, surrogate_sensitive_not_promoted | §12.2 |
| 660 / 700 × 1500 | R5.2 audit | 15.23 | **weak_reference_control_only** | v2 路线类 / §12.2 |
| **660 / 800 × 1400** | main route (448 rows) | **12.52** | **conditional_relative_main** | v1 main-660 直接行 |
| **660 / 800 × 1500** | main route (448 rows) | **12.70** | **conditional_relative_main** | v1 main-660 直接行 |
| 660 / 900 × 1400 | optional probe (448 rows) | 12.30 | **optional_robustness_probe_only** | v2 路线类 |
| 404 / 600 × 1300 | shortwave probe class | 4.45 | **shortwave_probe_only** | v2 路线类 + §5.3 P0/P6 trace |
| 路线类 mean: 弱参考场控制 | 448 rows | 15.23 | — | v2 路线类 |
| 路线类 mean: main-660 | 896 rows | 12.61 | — | v2 路线类 |
| 路线类 mean: optional probe | 448 rows | 12.30 | — | v2 路线类 |
| 路线类 mean: long-wave selected-annulus probe | 1344 rows | 10.09 | — | v2 路线类 |
| 路线类 mean: mid-wave baseline (488/532) | 896 rows | 7.77 | — | v2 路线类 |
| 路线类 mean: large context | 250,432 rows | 7.09 | — | v2 路线类 |
| 路线类 mean: shortwave probe | 448 rows | 4.45 | — | v2 路线类 |
| 路线类 mean: shortwave selected-annulus probe | 1344 rows | 4.04 | — | v2 路线类 |

#### 表 6.4.B — NODI engineering lens stable detection（NODI engineering gate 通过的 17 strict-pass case 子集平均；与表 6.4.A 不同 lens）

| 几何 | lens 1: NODI engineering (%) | lens 2: 2020 paper-条件 (%) | lens 3: 2022 NODI paper-条件 (%) |
|---|---:|---:|---:|
| 404 / 500 × 800 | 33.65 | 34.50 | 35.40 |
| 660 / 800 × 550 | 47.15 | 43.50 | 46.70 |
| 660 / 800 × 1400 | 45.15 | 41.00 | 42.90 |
| 660 / 900 × 1200 | 42.60 | 44.20 | 47.05 |

#### 表 6.4.C — Au paper-audit selected-annulus lens（跨 4 几何 mean: 800×500/600 + 1200×500/600）

| λ (nm) | mean stable detection (%) | mean pulse peak (相对) | pass 比例（strict NODI gate）|
|---:|---:|---:|---:|
| 488 | 5.95 | 0.0525 | 0.00 |
| 532 | 8.51 | 0.0773 | 0.00 |
| 660 | 17.74 | 0.1564 | 0.45 |

#### 表 6.4.D — Au paper-audit selected-annulus lens, 粒径阶梯（660 / 800 × 500 nm，近 Tsuyama 2020 counting POD 条件 Au gold 对照）

| Au 粒径 (nm) | mean detection (%) | mean stable detection (%) | mean pulse peak (相对) |
|---:|---:|---:|---:|
| 20 | 0.00 | 0.00 | 0.000 |
| 30 | 14.6 | 14.0 | 0.044 |
| 40 | 26.6 | 26.5 | 0.110 |
| 50 | 30.5 | 30.0 | 0.232 |
| 60 | 31.5 | 30.8 | 0.447 |

#### 表 6.4.E — 660 nm 读出方式对照（60 cases，NODI 2024 readout mode calibration lane）

| 读出方式 | strict gate 通过比例 | mean detection (%) | mean stable detection (%) |
|---|---:|---:|---:|
| in-phase + phase-gated (基线) | 0.00 | 18.28 | 17.89 |
| in-phase no gate | 0.45 | 18.28 | 17.89 |
| magnitude（脉冲幅值）| 0.45 | 18.15 | 17.74 |

读法：strict gate 通过比例从 0 跳到 0.45 是边界判据切换，**不是** detection 本身改变。mean detection 几乎不变。

### 6.5 雷区警告：禁止跨 lens 直接比较

```text
表 6.4.A 行 660 / 800 × 1400 = 12.52% (口径 A all-crossing 8-scenario avg)
表 6.4.B 行 660 / 800 × 1400 = 45.15% (NODI engineering lens stable detection)

12.52 与 45.15 同是 "660 / 800 × 1400 detection"，但分母不同、aggregation 不同；
直接读 "detection 从 12.52% 跳到 45.15% 因为换了 lens" 是错的；
正确读法是 "这两个数字回答两个不同问题，不可比"。
```

---

## §7 变量隔离分析（固定其他，看一个变量）

本节用 §6 的数据回答"固定 X，看 Y 改变了什么"。它是 §1 → §10 / §11 推荐之间的桥梁——读者能在这里直接看到每个变量的影响幅度。

公共约定（全 §7 适用）：

```text
- transit 列用 ms（按 §6.1 物理推导；只依赖 λ）
- detection 列用 %（按 v4.2 / v5.0 已发布数字单位换算）
- 每张表显式标 lens 分母 + 颗粒口径
- "—" = v4.2 / v5.0 未直接覆盖该 cell；禁止读为 0%
```

### 7.1 固定几何，看波长（5 张表）

#### 7.1.1 几何 = 660 / 800 × 1400（口径 A main 第一）；颗粒 EV biomimetic；lens = NODI engineering stable detection

| λ (nm) | transit (ms) | EV Csca× (相对 660) | detection (%) | 数据来源 |
|---:|---:|---:|---:|---|
| 404 | 5.48 | 7.10 | — | v4.2 未直接覆盖（最近邻 404 / 500 × 800 = 33.65%）|
| 488 | 6.61 | 3.34 | — | v4.2 未直接覆盖 |
| 532 | 7.21 | 2.37 | — | v4.2 未直接覆盖 |
| 660 | 8.94 | 1.00 | **45.15** | §6.4 表 B 直接行 |

#### 7.1.2 几何 = 800 × 550 nm（Tsuyama 论文 depth）；颗粒 EV biomimetic；lens = NODI engineering stable detection

| λ (nm) | transit (ms) | EV Csca× | detection (%) | 数据来源 |
|---:|---:|---:|---:|---|
| 404 | 5.48 | 7.10 | — | 未覆盖 |
| 488 | 6.61 | 3.34 | — | 未覆盖 |
| 532 | 7.21 | 2.37 | — | 未覆盖 |
| 660 | 8.94 | 1.00 | **47.15** | §6.4 表 B 直接行 |

#### 7.1.3 几何 = 500 × 800 nm（404 nm 短波 lens 几何）；颗粒 EV biomimetic；lens = NODI engineering stable detection

| λ (nm) | transit (ms) | EV Csca× | detection (%) | 数据来源 |
|---:|---:|---:|---:|---|
| **404** | 5.48 | 7.10 | **33.65** | §6.4 表 B 直接行 |
| 488 | 6.61 | 3.34 | — | 未覆盖 |
| 532 | 7.21 | 2.37 | — | 未覆盖 |
| 660 | 8.94 | 1.00 | — | 未覆盖（最近邻 800 × 550 = 47.15%）|

#### 7.1.4 几何 = 800 × 500 nm（Au paper-audit 主对照 + counting POD 论文几何）；颗粒 Au panel 20–60 nm；lens = selected-annulus

| λ (nm) | transit (ms) | Au Csca× | Au20 det (%) | Au30 det (%) | Au40 det (%) | Au50 det (%) | Au60 det (%) | 数据来源 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 488 | 6.61 | 0.43 | — | — | — | — | — | 未在此 cell 直接覆盖 |
| 532 | 7.21 | 0.59 | — | — | — | — | — | 未在此 cell 直接覆盖 |
| **660** | 8.94 | 1.00 | **0.0** | **14.6** | **26.6** | **30.5** | **31.5** | §6.4 表 D 直接行 |

#### 7.1.5 几何 = 跨 4 几何 mean（800 × 500/600 + 1200 × 500/600）；颗粒 Au panel mean；lens = selected-annulus

| λ (nm) | transit (ms) | Au Csca (m²) | mean stable detection (%) | mean pulse peak (相对) | 数据来源 |
|---:|---:|---:|---:|---:|---|
| 488 | 6.61 | 2.86 × 10⁻¹⁶ | 5.95 | 0.0525 | §6.4 表 C |
| 532 | 7.21 | 3.93 × 10⁻¹⁶ | 8.51 | 0.0773 | §6.4 表 C |
| 660 | 8.94 | 6.66 × 10⁻¹⁶ | 17.74 | 0.1564 | §6.4 表 C |

### 7.2 固定波长，看几何（5 张表）

#### 7.2.1 λ = 660 nm + H = 1500 nm；颗粒 EV biomimetic；lens = all-crossing 8-scenario avg

| W (nm) | transit (ms) | detection (%) | 路线最终角色 |
|---:|---:|---:|---|
| 500 | 8.94 | 19.64 | context, surrogate_sensitive_not_promoted |
| 600 | 8.94 | 16.55 | context, surrogate_sensitive_not_promoted |
| 700 | 8.94 | 15.23 | weak_reference_control_only |
| **800 (main)** | 8.94 | **12.70** | **conditional_relative_main** |
| 900 | 8.94 | — | 未在 H=1500 直接覆盖（最近邻 900 × 1400 = 12.30%）|

#### 7.2.2 λ = 660 nm + H = 1400 nm；颗粒 EV biomimetic；lens = all-crossing 8-scenario avg

| W (nm) | transit (ms) | detection (%) | 路线最终角色 |
|---:|---:|---:|---|
| 500 | 8.94 | 18.97 | context, surrogate_sensitive_not_promoted |
| 600 | 8.94 | — | 未覆盖 |
| 700 | 8.94 | — | 未覆盖 |
| **800 (main)** | 8.94 | **12.52** | **conditional_relative_main** |
| 900 | 8.94 | 12.30 | optional_robustness_probe_only |

#### 7.2.3 λ = 660 nm + W = 500 nm，看 H 阶梯；lens = all-crossing 8-scenario avg

| H (nm) | transit (ms) | detection (%) | ratio vs main 660 | 路线最终角色 |
|---:|---:|---:|---:|---|
| 1200 | 8.94 | 17.39 | 1.379× | context, surrogate_sensitive_not_promoted |
| 1300 | 8.94 | 18.26 | 1.448× | context, surrogate_sensitive_not_promoted |
| 1400 | 8.94 | 18.97 | 1.504× | context, surrogate_sensitive_not_promoted |
| 1500 | 8.94 | 19.64 | 1.557× | context, surrogate_sensitive_not_promoted |

读法：W=500 在 H=1200→1500 内 detection 单调上升，但 4 行均被治理裁决降级为 `surrogate_sensitive_not_promoted`——这是 §10.4 width-prior + P0 audit 的典型例子。

#### 7.2.4 λ = 660 nm + W = 800 nm，看 H 阶梯；多 lens 同时排（仅 v4.2 已直接覆盖行）

| H (nm) | transit (ms) | NODI engineering stable det (%) | 2020 paper lens (%) | 2022 NODI paper lens (%) | all-crossing 8-scen avg (%) | 几何角色 |
|---:|---:|---:|---:|---:|---:|---|
| 550 | 8.94 | 47.15 | 43.50 | 46.70 | — | Tsuyama 论文 depth（cross-check）|
| 1400 (**main**) | 8.94 | **45.15** | 41.00 | 42.90 | **12.52** | **conditional_relative_main** |
| 1500 (**main**) | 8.94 | — | — | — | **12.70** | **conditional_relative_main** |

#### 7.2.5 λ = 660 nm + W = 900 nm，看 H；多 lens 同时排

| H (nm) | transit (ms) | NODI engineering stable det (%) | all-crossing 8-scen avg (%) | 几何角色 |
|---:|---:|---:|---:|---|
| 1200 | 8.94 | **42.60** | — | NODI lens 直接行 |
| 1400 | 8.94 | — | **12.30** | optional_robustness_probe_only |
| 1500 | 8.94 | — | — | 未覆盖 |

### 7.3 固定颗粒粒径，看几何（口径 B paper-audit）

#### 7.3.1 Au 颗粒 + selected-annulus + D2.1 算子；按 case-level raw Au peak-height exponent 排序（数据来自 §11.2.1 第 Phase 2.10 行：raw Au size-response 残差分解）

| λ (nm) | 几何 W × H (nm) | transit (ms) | raw Au peak-height exponent | residual vs Tsuyama 2.3 | 几何角色（§11.3 step 2）|
|---:|---|---:|---:|---:|---|
| 660 | 1200 × 550 | 8.94 | **3.0335** | **+0.73** | **口径 B 主对照（residual 全 6 case 最低）**|
| 660 | 800 × 550 | 8.94 | 3.0456 | +0.75 | **口径 B 主对照**|
| 532 | 800 × 550 | 7.21 | 3.1563 | +0.86 | wavelength 对照 |
| 488 | 800 × 550 / 1200 × 550 | 6.61 | — | — | v4.2 D2.1 case-level 未直接覆盖 |
| 532 | 1200 × 550 | 7.21 | — | — | 未直接覆盖 |

读法：在 step 1（§11.2）校准过的 reproduction lens 内，660 / 1200 × 550 与 660 / 800 × 550 的 raw Au peak-height exponent residual 最低——这是 step 2 选这两个几何为口径 B 主对照的**直接数据根据**（§11.3 / §11.4）。

### 7.4 三 lens 同时排列对照（同一波长 / 几何在不同 lens 下的 detection 差异有多大）

| 几何 | NODI engineering lens stable det (%) | 2020 paper lens (%) | 2022 NODI paper lens (%) | EV all-crossing 8-scen avg (%) | lens 间最大差 |
|---|---:|---:|---:|---:|---:|
| 660 / 800 × 1400 | 45.15 | 41.00 | 42.90 | 12.52 | 32.6 pp |
| 660 / 800 × 550 | 47.15 | 43.50 | 46.70 | — | 3.6 pp |
| 660 / 900 × 1200 | 42.60 | 44.20 | 47.05 | — | 4.5 pp |
| 404 / 500 × 800 | 33.65 | 34.50 | 35.40 | — | 1.7 pp |

读法：**lens 切换造成的差异（最大 32.6 pp）远大于同 lens 内波长 / 几何切换造成的差异（同 lens 内最大约 6 pp）**。这就是 §4.5 的实证根据——禁止跨 lens 比较不是过度谨慎，是数字本身就告诉你不能。

### 7.5 §7 的 6 条读法（总结）

```text
读法 1: 表 7.1.x 显示 v4.2 / v5.0 在 EV biomimetic + 跨波长几何对照上数据稀疏；
        660 nm 行通常有直接数据，404 / 488 / 532 行多数为 "—"。
        要补这些 cell，必须新跑 case，不是 v5.0 范围内能完成。

读法 2: 表 7.2.x 在 660 nm 下数据密；其它波长在 W、H 阶梯上稀疏。
        v4.2 / v5.0 没有按 "波长 × W × H" 三维全扫，而是以 660 nm 为主路线 +
        404 nm 为短波探针的单点对照。

读法 3: transit (ms) 只依赖 λ，几何不变它就不变。同一 λ 在所有 §7.2 表里 transit 一致。
        这是物理推导，§13 第 2 档证据。

读法 4: §7.3.1 是 §11.3 / §11.4 几何选型的直接数据根据。660 / 1200 × 550 与
        660 / 800 × 550 之所以是口径 B 主对照，不是因为它们最像 Tsuyama 器件，
        而是因为在 step 1 校准过的 lens 内 raw exponent residual 最低。

读法 5: §7.4 显示 lens 切换 > 波长切换 > 几何切换。颗粒切换（EV vs Au）的
        影响在 §9 排第 1，比 lens 切换还大（§9 详解）。

读法 6: 表 7.2.1 / 7.2.2 显示窄通道 (W=500) detection 数字最高，但都被治理裁决降级
        为 surrogate_sensitive_not_promoted。详细解释见 §10.4。
```

---

## §8 噪声归因（为什么参考场放大不消除噪声）

读完 §2 / §6 / §7，读者会问：

```text
既然参考场放大 |E_sca| 把 peak 放大了，
而噪声 (noise_std = 0.01 + post_readout = 0.002) 这么小，
detection 不应该接近 100% 吗？
```

答案：不是。本节用 3 个理由解释。

### 8.1 理由 1 — 参考场放大相干一次项，不放大噪声

回看 §2.2 阶段 5：

```text
signal_trace = |E_sca|² + 2 · Re(E_ref · E_sca*)
```

参考场放大的是 `2 · Re(E_ref · E_sca*)`——一个**相干项**（含相对相位）。噪声没有相干相位，所以参考场不放大它。

```text
信号 amplification: × |E_ref| (与 λ 几乎无关)
噪声 amplification: × 1
```

SNR 确实增加。但 detection 不只是 SNR 的单调函数——它还要过**阈值**和**采样数**两关。

### 8.2 理由 2 — 阈值随噪声同步抬高

阈值公式：

```text
threshold = median(背景前 20%) + threshold_sigma · 1.4826 · MAD(背景前 20%)
threshold_sigma = 5 或 10
```

所以 noise↑ → MAD↑ → threshold↑ → detection↓。换句话说：阈值是 noise-aware 的，参考场放大 signal 后阈值也变。但 signal / noise ratio 改善确实让 detection 上升——这就是 main-660 lens 下 detection 能到 12.5–47% 的原因。

### 8.3 理由 3 — 短波长 transit↓ + phase flip↑ → 有效采样数↓ + margin↓

参考 §2.4 表与 §6.1 transit 表，404 nm 比 660 nm：

```text
transit:  5.48 ms  vs  8.94 ms (≈ 0.61×)
锁相 τ:   1–2 ms (二者同)
有效采样: transit / τ ≈ 0.61× (404 比 660 少约 40% 有效样本)
phase flip fraction: 短波长更高（OPD 抖动相对 λ 占比更大，正负翻转更频繁）
```

短波长虽然 peak 放大，但：

- 有效采样数变少 → margin z 不能跟 peak 同步放大（mean_peak_margin_z 在 404 nm ≈ 1.2–1.6× 660 nm 的水平，不是 2×）
- phase flip 把一些事件分到负 peak（在 `pulse_detection_mode="absolute"` 下负 peak 可被检出，但极性记录会拖累 stable detection rate）
- Wilson 下界 (`detection_rate_wilson_lb`) 在有限事件数 + 高方差下进一步压低

### 8.4 数值版（noise 影响的具体量级）

| 场景 | peak（相对 660 / 800 × 1400 main）| pre + post noise std (相对) | mean_peak_margin_z 估计 | 综合 detection % (8-scen avg) | 解释 |
|---|---:|---:|---|---:|---|
| 660 / 800 × 1400 main | 1.00× | 0.012 | 数 σ 量级 | 12.52 | 主路线基线 |
| 404 / 600 × 1300 短波探针 | 2× peak 但 transit ≈ 0.61× | 0.012（相同噪声） | 偏小（margin z ≈ 1.2–1.6× 但被 phase flip 拖累）| 4.45 | shortwave_probe_only |
| 660 / 700 × 1500 weak-ref | 偏低（\|E_ref\| 弱）| 0.012 | 中 | 15.23（在 selected-annulus 反而看似高）| 弱参考场，分子分母同步缩小，看似比 main 还高，但参考场太弱不是物理优势 |

### 8.5 一句话总结噪声归因

```text
参考场放大相干一次项 → signal 端确实放大；
噪声不被放大 → SNR_amplitude 上升；
但 detection = P(peak > 阈值) 这一概率还要看：
  (a) 阈值（随噪声同步上抬）
  (b) 有效采样数（随 transit 与 τ 决定）
  (c) phase flip（短波长更频繁）
所以 detection ≠ SNR_amplitude 的单调函数；
peak 翻倍不等于 detection 翻倍（§2.4 数值证据）。
```

---

## §9 变量影响排序（哪个变量对 detection 影响最大）

按 |Δ detection| / |Δ variable| 量级估算，把所有可调变量排序：

| 排名 | 变量 | 量化影响（v4.2 / v5.0 现有数据估算）| 出处 | 解读 |
|---:|---|---|---|---|
| 1 | **颗粒材料**（EV biomimetic vs Au plasmonic）| 同 660 / 800 × 550 几何：Au mean stable det 17.74% vs EV NODI lens 47.15%；488/532/660 上 Csca 方向完全相反 | §6.4 表 C vs 表 B；§7 | 最大影响。不分材料的"波长 / 几何 → detection"结论会误导。 |
| 2 | **lens 切换**（all-crossing vs NODI engineering vs selected-annulus vs 2022 NODI paper） | 同 660 / 800 × 1400：NODI eng = 45.15%、all-crossing 8-scen = 12.52%（差 32.6 pp）| §7.4 | 第 2 大。这是为什么 §4.5 明令禁止跨 lens 比较的实证。 |
| 3 | **探测波长 λ**（在固定材料 + 几何）| EV biomimetic：detection 大致 0.4 / 0.7 / 0.7 / 1.0× (404 / 488 / 532 / 660)；Au plasmonic：0.34 / 0.49 / 1.0× (488 / 532 / 660) | §6.4 表 C；§7.1 | 大。方向与材料绑定。 |
| 4 | **颗粒粒径**（在固定 Au）| 660 / 800 × 500：0 / 14.6 / 26.6 / 30.5 / 31.5% (20 / 30 / 40 / 50 / 60 nm) | §6.4 表 D | 大。Au20 是 weak-SNR / not-all-detected 的物理边界。 |
| 5 | **通道宽度 W**（在 660 nm，H = 1400–1500）| 500 → 18.97%；800 (main) → 12.52%；900 → 12.30% | §7.2.1 / 7.2.2 | 中。窄通道分数高但被 §10.4 width-prior + 治理压住。 |
| 6 | **通道深度 H**（在 660 nm，W = 800）| 1400 → 12.52%；1500 → 12.70%（差 < 2%）| §7.2.4 | 中-小。1400 / 1500 已饱和。 |
| 7 | **收集算子配置**（D2.1 best 内 `collection_narrow` vs control）| raw Au exponent 3.071 vs 3.190；joint score 2.377 vs 2.635 | §11.3 step 2 | 中-小（口径 B paper-audit lane 内可量化的中等改进）。 |
| 8 | **读出方式**（in-phase / magnitude / in-phase + phase-gated）| 660 nm：mean stable det 几乎一致（17.74–17.89%），但 strict gate 通过比例从 0.00 跳到 0.45 | §6.4 表 E | 在 pass / fail 边界上影响巨大；mean detection 几乎不变。 |
| 9 | **参考场模型**（`channel_angular_surrogate` vs `paper_aligned_phase_filter` vs `calibrated_lookup`）| 平均绝对差异 ≈ 2.13%，最大 ≈ 9.20% | §6.3 | 小（在波长 / 几何固定后，参考场模型差异约 1–9%）。 |
| 10 | **selected-annulus 窗口 (0.5–0.8)** | shadow uplift median 1.384×、max 1.557× | §12.2 R5.2 sidecar | 中（分母层面），但**禁止移动**（§15）。 |
| 11 | **threshold_sigma + min_peak_width** metadata guardrail | 不一致就 fail fast | §5.4 / §3.4 | 小（量化上），但 fail-fast 判据 |

读者结论：**排前 4 都是"颗粒侧 / lens 侧"变量**；几何（W、H）位列 5-6，量级中等且在 main-660 锁定后已基本饱和；7-10 都是计算 / 算子 / 读出层级，量化影响小但在路线治理和 metadata guardrail 层是 fail-fast 判据。

---

## §10 口径 A 工程主线推荐（EV / NODI engineering main route）

### 10.1 推荐参数（总览）

```text
探测波长 λ          = 660 nm
通道宽度 W          = 800 nm
通道深度 H          ∈ {1400 nm, 1500 nm}     # 双 main 集合，不挑单一冠军
颗粒目标            = EV biomimetic (含 Au20 / Au30 anchors)
排序窗口            = all-crossing (全 BFP 全 crossing)
路线最终角色        = conditional_relative_main
release status      = (口径 A 已收口；后续依赖 P19 evidence-strategy gate)
```

为什么是双 main 而不是单一推荐？P6–P16 六条 trace 在 (800 × 1400, 800 × 1500) 之间首位反复切换（§5.3 表 P6–P16 行），所以保留两条为集合，不挑单一冠军；详细出处见 §10.5 与 §5.3。

### 10.2 因果链：物理 → 工程 → 治理（5 步推导）

**第 1 步 — 颗粒材料锁定为 EV biomimetic**

项目目标即 EV / NODI 检测；§9 排名 1 决定波长方向：EV biomimetic 在 Rayleigh 区段，Csca ≈ 1 / λ⁴；同时强参考场下 peak ≈ |E_ref| · √Csca。

**第 2 步 — 波长 → 660 nm**

- §6.4 表 6.4.B：660 / 800 × 1400 在 NODI engineering lens stable det 45.15%
- §6.4 表 6.4.B：404 / 500 × 800 在同 lens 只有 33.65%
- §6.4 表 6.4.A 短波探针类（404 / 600 × 1300）mean 4.45% << main-660 12.61%
- §5.3 P6–P16 trace：404 probe 始终排第 3
- 404 nm 热效应旁路 §15 forbidden 中明令不得加分

**第 3 步 — 通道宽度 → 800 nm**

- §6.4 表 6.4.A：500 / 1500 detection 19.64%、500 / 1400 detection 18.97%（context routes 分数最高）
- §10.4 width-prior 给出"窄通道工程风险被低估"的低自由度解释
- §12.2 R5.2 sidecar：`context_route_promotion_authorized = false`
- §5.3 P0 audit 把 563 条 surrogate-sensitive 路线降级

所以 W = 800 是**治理意义上的稳定基准**，不是数字最高。详细见 §10.4。

**第 4 步 — 通道深度 → 1400 或 1500 nm（双 main 集合）**

- §6.4 表 6.4.A：800 × 1400 vs 800 × 1500 在 all-crossing 8-scen avg 上差 < 2%（12.52% vs 12.70%）
- §5.3 post-v2 近壁细网格证据：两条 main-660 在细网格上通过比例 = 1.0
- §5.3 P6–P16 trace 首位反复切换 → P18 stop_mechanical_lane_roll_forward
- 两条 main-660 同时保留为 conditional_relative_main 集合

**第 5 步 — 路线治理边界（不可越过）**

```text
main_660_redefinition_authorized = false        # 不得重新定义 main-660
route_promotion_authorized       = false        # 不得直接路线晋升
calibrated_claim_allowed         = false        # 仍 surrogate-relative
P19 evidence-strategy gate 之前不再机械式滚 lane
```

### 10.3 detection 增益数字（口径 A 视角）

| 对比 | detection 差 | 倍数 |
|---|---:|---:|
| main-660 (12.52%) vs short-wave probe (4.45%) | +8.07 pp | ≈ 2.81× |
| main-660 (12.52%) vs large context class (7.09%) | +5.43 pp | ≈ 1.77× |
| main-660 (12.52%) vs mid-wave baseline (7.77%) | +4.75 pp | ≈ 1.61× |

读法：**这些倍数不是绝对 detection 改善**，是合成相对先验分数下的相对改进。在 v5.0 内不解锁 calibration（§13 / §15）。

### 10.4 为什么不挑数字最高的几何（深度解释）

**现象**：表 6.4.A / 7.2.1 / 7.2.2 / 7.2.3 显示 660 / 500 × 1500 detection 19.64% > 600 / 1500 16.55% > 700 / 1500 15.23% > 800 / 1500 12.70% (main) > 900 / 1400 12.30%（optional probe）——**窄通道反而数字最高**。

**关键提问**：那 main-660 为什么不是 500 × 1500？

**答案 1（width-prior 解释 + R5.2 sidecar）**

引入"窄通道工程风险被低估"的低自由度先验后，2 种 width-prior 模型能同时满足"main 路线保留 + context 路线越线消失 + weak-ref 越线消失"：

| width-prior 模型 | main 保留比例 | context 越线数 | weak-ref 越线数 | 解释等级 |
|---|---:|---:|---:|---|
| (W / 800)^1.5 | 1.000 | 0 | 0 | 可接受 |
| (W / 800)^2.0 | 1.000 | 0 | 0 | 可接受 |
| (W / 850)^2.0 | 0.886 | 0 | 0 | 可接受但需谨慎 |
| (W / 900)^2.0 | 0.79 | 0 | 0 | **过强**（main 压损太多）|

所以"窄通道高分"很可能不是物理真的更好，而是**原模型低估了窄通道工程风险**（颗粒-壁面间隙、PEG、近壁运输、堵塞、通量风险等）。

但本报告同时声明：

```text
width-prior (W / 800)^1.5 / ^2 是可接受解释模型，
不是真实物理定律（§13 第 5 档：可接受解释先验）；
推到 (W / 900)^2 会过度打压主路线。
```

**答案 2（多轮审计裁决）**

| 审计 | 对 660 / 500 × 1500 等窄通道高分路线的裁决 |
|---|---|
| P0 audit | surrogate_sensitive_not_promoted（563 条之一）|
| R5.2 bounded scenario-prior audit | context_route_promotion_authorized = false |
| P18 synthesis | bounded_lanes_sufficient_for_route_promotion = false |
| width-prior 解释 | 窄通道工程风险被低估，分数高不等于物理优势 |

所以 main-660 锁在 800 × 1400 / 1500 是 **width-prior + 多轮独立审计 + 治理边界**的一致结果，不是单一指标决定。

### 10.5 路线治理裁决总表（每条路线最终角色 + 主要理由）

| 几何 (660 nm) | all-crossing detection (%) | P0 audit 最终角色 | 主要理由 |
|---|---:|---|---|
| 800 × 1400 | 12.52 | **conditional_relative_main** | §5.3 post-v2 近壁细网格通过 1.0 + §5.3 P6 / P8 / P14 trace 首位 |
| 800 × 1500 | 12.70 | **conditional_relative_main** | §5.3 post-v2 近壁细网格通过 1.0 + §5.3 P10 / P12 / P16 trace 首位 |
| 700 × 1500 | 15.23 | weak_reference_control_only | §12.2 R5.2：weak ref 8 / 8 scenarios above main，但 \|E_ref\| 偏低不是物理优势 |
| 900 × 1400 | 12.30 | optional_robustness_probe_only | §6.4 表 6.4.A + §5.3 P0 audit；不得 redefine main-660 |
| 500 × 1200–1500 | 17.39–19.64 | context, surrogate_sensitive_not_promoted | §10.4 width-prior + §12.2 sidecar |
| 600 × 1500 | 16.55 | context, surrogate_sensitive_not_promoted | 同上 |
| 800 × 550 | (NODI lens 47.15%) | paper-sanity / cross-check（仅作为 §14 Tsuyama 对照）| 不替代 main-660；详 §14.6（口径 B Tsuyama 2022 NODI 对照）|

---

## §11 口径 B 论文审计推荐（两步框架）

### 11.1 两步框架总览

口径 B 的核心逻辑是**先校准估计参数，再选几何**，不是"挑哪个几何最像 Tsuyama"。

```text
Step 1 — Tsuyama 数据校准估计参数
   target: Tsuyama Table S1 Ag/Au signal、Au size exponent 2.3、Au30/Au20 SNR 33/12
        ↓
   反推: 全局响应压缩 γ + 全局 SNR 缩放 + 全局 SNR 响应指数 + 选定算子 (D2.1 best)
        ↓
   产物: 一组低自由度复现 lens 估计参数（§3.6 / §11.2）

Step 2 — 在校准 lens 内选几何 / 波长 / 颗粒 / 读出
   在 step 1 估计参数固定的条件下扫几何 × 波长 × 颗粒 × 读出
        ↓
   选 residual 最低的组合
        ↓
   产物: 几何 = 660 / 1200 × 550 + 660 / 800 × 550；
         颗粒 panel = Au 20 / 30 / 40 / 60 nm；
         硬件接法 = ET-2030 + LI5640 + current input / TIA
```

**关键澄清**（§11.4 详解）：几何 800 × 550 / 1200 × 550 之所以被选中，**不是因为它们最像 Tsuyama 论文器件**（虽然 Tsuyama 2022 NODI 器件确实在 800 × 550 附近），**而是因为在 step 1 校准过的 lens 内 raw Au peak-height exponent residual 最低**。

### 11.2 Step 1 — 用 Tsuyama 数据校准估计参数

#### 11.2.1 Phase 2 / 2.5 / 2.6 / 2.7 / 2.8 / 2.9 / 2.10 / 2.11 链做了什么

| Phase | 角色 | 关键产物 |
|---|---|---|
| 2 | family-ladder full inverse | 52 candidates × 3 seeds × 10,000 events；main No-Go = `raw_size_response_alignment_not_met` |
| 2.5 D2 | raw-operator family search | 20 candidates × 3 seeds × 1,500 events；最优 raw Au exponent 3.090（仍偏陡）|
| 2.5 D2.1 | D2 局部 smoke 加密 | 12 variants × 3 seeds × 2,000 events；选出 **D2.1 best = `tau_2ms_global_refphi_plus_collection_narrow`** |
| 2.6 | size-only F-family 单确认 + paper-reproduction formula | 12 rows × 3 seeds × 3,000 events；只允许全局 size delta + 全局 SNR scale |
| 2.7 | 加 SNR 响应指数 | 同一 best candidate；SNR ratio loss 从 1.4053 降到 0.4235 |
| 2.8 | reviewed / descriptive rescore | bounded_reproduction_partial_descriptive；release status 仍 negative |
| 2.9 | maximal upper-bound rescore | 给可映射上限，不签 accepted |
| 2.10 | raw Au size-response 残差分解 | 按 wavelength × geometry × observable × adjacent size pair 拆，**limiting pair 全为 40-60 nm** |
| 2.11 | single global response compression rescore | 最终 best: **γ = 0.749，total reproduction score 2.033** |

#### 11.2.2 校准产物（3 个全局估计参数 + 1 个选定算子）

| 描述名 | 符号 / 代码 ID | 数值 | 物理意义 |
|---|---|---:|---|
| 全局响应压缩因子 | γ (`paper_reproduction_response_compression_gamma`) | 0.749 | 把 raw peak 高度按 peak^γ 重映射，让 Au 粒径响应斜率落到论文 2.3 |
| 全局 SNR 缩放因子 | s_SNR (`paper_reproduction_global_snr_scale`) | 0.728 | 把 Au20 / Au30 局部 SNR 平移到 Tsuyama 论文 anchor |
| 全局 SNR 响应指数 | e_SNR (`paper_reproduction_snr_response_exponent`) | 0.812 | Phase 2.7 引入，调节 SNR ratio 的相对 scaling |
| 选定探测算子 (D2.1 best) | `tau_2ms_global_refphi_plus_collection_narrow` | — | lock-in τ = 2 ms + 全局参考相位正向位移 + 窄收集窗 |

**这 4 项（3 个全局估计参数 + 1 个选定算子）的证据档位都是第 4 档（reproduction-lens 估计项）**——不是物理常数、不是仪器物理量。详见 §13。

#### 11.2.3 校准 score 的具体分解（D2.1 best + γ = 0.749）

```text
formula-consistent Ag/Au loss  ≈ 0.041   (pass，已通过 raw signal-ratio target)
SNR-ratio loss                 ≈ 0.387
SNR-anchor loss                ≈ 0.0146
detection loss                 ≈ 0.65
complexity penalty             ≈ 0.818
strict Table S1 residual       ≈ 0.12    (Ag-anchor + Ag 行歧义，保留为 diagnostic warning)
total reproduction score       ≈ 2.033   (bounded partial 阈值 2.0)
```

raw Au peak-height exponent 在 D2.1 best 上 case-level decomposition：

```text
660 / 1200 × 550  →  3.0335    (residual 全 6 case 最低)
660 / 800 × 550   →  3.0456
532 / 800 × 550   →  3.1563
limiting size pair: 40–60 nm (全 6 case 一致)
```

#### 11.2.4 Phase 2.6+ 不再降分的边界（**重要**）

Phase 2.11 后再追更低 reproduction score 必须引入 per-diameter / per-geometry / per-case correction 或 detection logistic remap，**越过 estimated-parameter 复现边界**。所以 v4.0 起把当前参数集冻结，不再扩大算法自由度。

```text
这 0.033 不应通过调权重抹掉。
剩余项来自真实的 SNR ratio residual、γ complexity 与 detection warning。
要继续推进必须靠实测 artifact，不是更多 reproduction-lens 自由度。
```

### 11.3 Step 2 — 在校准 lens 内选几何 / 波长 / 颗粒 / 读出

固定 step 1 的 γ / s_SNR / e_SNR / D2.1 best 算子，在 step 1 lens 内扫候选范围，选 residual 最低的组合：

| 选型维度 | 候选范围 | step 1 lens 内最优 | step 2 residual 理由（出处） |
|---|---|---|---|
| 几何 | {488 / 532 / 660 nm} × {800 × 550, 1200 × 550, ...} | **660 / 1200 × 550** + **660 / 800 × 550** | §7.3.1 / §11.2.3：raw Au peak-height exponent 3.0335 / 3.0456 全 6 case 最低 |
| 探测波长 | 488 / 532 / 660 nm | **660 nm（主对照）**，488 / 532 保留作 wavelength 对照 | §6.4 表 C：660 mean stable det 17.74% > 532 8.51% > 488 5.95% |
| 颗粒 panel | Ag / Au 组合 | **Au 20 / 30 / 40 / 60 + Ag 40 / 60 nm** | §1.3 / §3.1：与 Tsuyama Table S1 + paper anchor 集合一致 |
| 收集算子 | D2 raw operator 全 family + D2.1 局部 12 variants | **`tau_2ms_global_refphi_plus_collection_narrow`** | §11.2.1：D2.1 内 collection_narrow 把 raw exponent 从 3.190（control）压到 3.071，joint score 从 2.635 压到 2.377 |
| 硬件接法 | ET-2030 + LI5640 × {current input/TIA, 50 Ω voltage path} × 216 配置 | **current input + low-noise TIA** | §11.6：current input / TIA 216 / 216 comfortable；50 Ω voltage path 211 / 216 below sensitivity → 黑名单 |

### 11.4 关键澄清（用户反馈点）

```text
几何选 660/800x550 与 660/1200x550，不是因为 "它们最像 Tsuyama 2022 NODI 论文器件"。
它们之所以被选中，是因为在 step 1 校准过的 reproduction-lens 口径下，
   raw Au peak-height exponent 3.05 / 3.03 在所有候选几何中 residual vs 2.3 最低。

这两件事方向重叠（Tsuyama 2022 NODI 器件确实在 800x550 附近），
是物理一致性的体现，不是选型逻辑的根据。

如果未来 measured artifact 把 step 1 校准从 reproduction-lens 推进到 calibrated lens，
那么 step 2 的 "最适合几何" 可能会改变 —— 因为 estimated parameters 变了。

但 v5.0 仍没有 measured artifact，所以 step 1 + step 2 在当前 estimated-parameter 边界内
已是最优低自由度解；这就是 v4.0 把当前参数集冻结为口径 B 选型的逻辑根据。
```

### 11.5 reproduction 增益（口径 B 视角）

| 对比 | reproduction score | 含义 |
|---|---:|---|
| Phase 2 family-ladder baseline median | ≈ 2.6–2.9 | raw inverse search 起点 |
| D2.1 best + γ = 0.749 (Phase 2.11) | **2.033** | bounded partial 阈值 2.0；当前选型 |
| 改善幅度 | 22–30% | step 1 校准成果 |

formula-consistent Ag / Au loss ≈ 0.041 已 pass；strict Table S1 residual 保留为 diagnostic（target-mode 歧义）；total score 仍高于 partial 阈值 2.0，差距约 0.033（score 是 lower-is-better penalty，无量纲），不应通过调权重抹掉。

### 11.6 硬件接法推荐（ET-2030 + LI5640 + current input / TIA）

来自 §5.5 instrument-aware feasibility：

| 接法 | 配置数 | comfortable margin | near minimum | below minimum sensitivity |
|---|---:|---:|---:|---:|
| current input + low-noise TIA | 216 | **216 / 216 (100%)** | 0 | 0 |
| 50 Ω voltage path | 216 | 0 | 5 / 216 | **211 / 216 (97.7%)** |

**推荐**：current input + low-noise TIA。**黑名单**：50 Ω voltage path（量级估计就已 below sensitivity）。

注意这是 instrument-aware feasibility 量级估计，不解锁 calibrated SNR / LOD。

### 11.7 口径 B 冻结参数集（v4.0 起冻结，v5.0 继承）

```text
chosen_lens_id      = single_global_response_compression_with_d2p1_base_v1
chosen_candidate_id = tau_2ms_global_refphi_plus_collection_narrow   # D2.1 best
chosen_response_compression_gamma γ  = 0.749
chosen_global_snr_scale s_SNR        = 0.728
chosen_global_snr_response_exp e_SNR = 0.812
selected_annulus_window              = 0.5–0.8     # 固定，不可移动
lock_in_time_constant τ              = 1–2 ms
readout_observable                   = pulse peak height (脉冲幅值)
phase_flip_hard_reject               = false
hardware_silicon_detector            = ET-2030 (responsivity / NEP / 0.4 mm active area)
hardware_lock_in                     = LI5640
hardware_connection                  = current_input_with_low_noise_TIA  # 推荐
hardware_connection_blacklist        = 50_ohm_voltage_path
au_diameter_panel                    = 20 / 30 / 40 / 60 nm
geometry_paper_audit_primary         = 660 / 1200 × 550, 660 / 800 × 550
geometry_paper_audit_secondary       = 488 / 800 × 550, 532 / 800 × 550, 488 / 1200 × 550, 532 / 1200 × 550
```

冻结后的 release：

```text
release_status                          = negative_or_diagnostic_result_only
no_accepted_paper_calibrated_candidate  = true
chosen_lens_total_reproduction_score    = 2.033
detection_status                        = partial_pass_with_Au20_low_warning
formula_consistent_signal               = pass
strict_table_s1_signal                  = unresolved (target-mode 歧义, diagnostic-only)
raw_au_size_response                    = unresolved (limiting pair 40-60 nm)
classification_accuracy                 = no_accuracy_claim (本地 sklearn 不可用)
```

---

## §12 双口径同时存在的意义

### 12.1 两套推荐为什么不冲突

| 维度 | 口径 A 推荐 | 口径 B 推荐 |
|---|---|---|
| 颗粒 | EV biomimetic (含 Au20 / Au30 anchors) | Au 20 / 30 / 40 / 60 nm + Ag 40 / 60 nm |
| 主波长 | 660 nm | 660 nm (含 488/532 wavelength 对照) |
| 主几何 | 800 × 1400 + 800 × 1500 nm | 800 × 550 + 1200 × 550 nm |
| 主目标 | EV route role + main-660 治理集合 | Tsuyama 2022 paper-audit proxy 复现 |
| 排序 lens | all-crossing 全 BFP 全 crossing | selected-annulus 0.5–0.8 |
| release | conditional_relative_main 集合 | negative_or_diagnostic_result_only |
| 下一步硬依赖 | P19 evidence-strategy gate | measured Au raw trace + blank + BFP/slit/ROI + lock-in/logger |

**两套推荐回答不同问题，分母不同、颗粒不同、几何不同，所以不冲突**。

### 12.2 同一证据在两个 lens 下的对照

| 证据 | 口径 A 下的结论 | 口径 B 下的结论 |
|---|---|---|
| main-660 (800 × 1400 / 1500) | conditional_relative_main 集合；P6–P16 trace 首位反复切换 | reference-useful long-wave candidate；**不是** paper-audit geometry 复现 |
| weak-reference control (660 / 700 × 1500) | weak_reference_control_only；§6.4 表 6.4.A mean 15.23% | weak-reference / NA boundary control |
| 660 nm 高分 context (660 / 500 × 1200–1500) | R5.2 ratio_vs_main 1.31–1.56×；context, surrogate_sensitive_not_promoted | selected-annulus uplift median 1.384×；同样 surrogate_sensitive |
| 404 nm probe (404 / 600 × 1300) | shortwave_probe_only；P6–P16 trace 排第 3 | short-wave engineering sanity；**不是** Tsuyama direct target |
| optional (660 / 900 × 1400) | optional_robustness_probe_only | 未独立扩展 |
| width-prior (W / 800)^1.5 / ^2 | 可接受解释；main 保留 1.000 + 越线 0 | sidecar 解释，不影响 paper-audit candidate score |
| 404 nm 热效应旁路 | 旁路提示，不加分 | 仍 forbidden（双口径共同）|
| Au panel 20–60 nm | 用作 anchor + Au-equivalent risk 解释 | paper-audit 主对照 |
| Tsuyama 2022 NODI paper 几何 (800 × 550) | 工程口径 cross-check，不替代 main-660 | step 2 paper-audit 几何子集（在 step 1 校准 lens 内 raw exponent residual 最低）|
| classification accuracy 71.9 ± 4.0% | 仅引用，不复现 | diagnostic_only target；本地 sklearn 不可用 |

### 12.3 双口径并立治理原则（going forward）

| 原则 | 描述 |
|---|---|
| 1 | 任何后续 realism v2 / post-v2 P19+ 阶段证据并入本报告时，必须**同时**评估两个口径，不允许只写一边 |
| 2 | 某口径下若没有等价证据，必须**显式标注 gap**："selected-annulus 口径下未扩展" 或 "all-crossing 口径下未扩展" |
| 3 | 新证据若改变了 §15 共同 forbidden claim 中的任意一条，必须先在 §15 显式更新，不允许通过新阶段表述间接推翻 |
| 4 | P19 evidence-strategy gate 必须为两个口径分别给出 acceptance criteria（详 §16.3）|
| 5 | 每次 P19+ 并入时，§12.2 对照表与共同收口段必须同步更新 |
| 6 | raw provenance 保留：reports/49 + 71 仍是口径 B 主源；不允许仅更新它们就声称报告 88 已同步 |

---

## §13 估计值的 6 档来源谱

读者最常被误读的：v5.0 报告里的每个数字属于哪一档证据？6 档总表如下：

| 档位 | 含义 | v5.0 报告中代表 | 可外推到 calibrated claim？ |
|---:|---|---|---|
| 1 | **物理常数 / 教科书参数** | λ, π, NA, n_water, c | ✅ 是 |
| 2 | **Mie 推导值**（由 1 直接计算）| Csca, Cext, Cabs, S1, S2, transit time (§6.1)、Au Csca (§6.2) | ✅ 是（受输入折射率精度限制）|
| 3 | **Surrogate 模型估值**（明确标 surrogate）| `channel_angular_surrogate` 参考场、`pupil_slit_surrogate` 收集、`lockin_surrogate` 读出、`relative_surrogate` 相位、Wilson LB | ❌ 否（方向有效，绝对量级不解锁）|
| 4 | **Reproduction-lens 估计项**（口径 B Phase 2.6–2.11）| γ = 0.749, s_SNR = 0.728, e_SNR = 0.812, D2.1 best 算子, Au size delta ≈ −0.80, Phase 2.11 reproduction score 2.033 | ❌ 否（明确禁止视为物理常数 / 仪器物理量）|
| 5 | **可接受解释先验**（口径 A 路线治理）| width-prior `(W/800)^1.5 / ^2`、`0.5–0.8` selected-annulus 边界、threshold_sigma `5 / 10`、noise_std `0.01`、shot_noise_scale `0.001`、post_readout_noise_std `0.002`、路线角色分类 | ❌ 否（解释模型，不是物理定律）|
| 6 | **校准 / 实测值** | **当前 0 个**；v5.0 全文 `calibrated_claim_allowed = false`、`measured_data_ingest_authorized = false` | — |

读者结论：**v5.0 报告所有可视化数字至多到第 5 档**。任何把 3–5 档当作第 6 档的解读都违反 §15 共同 forbidden claim。

高频被误读数字的正确档位：

| 数字 | 出处 | 档位 | 容易被误读为 | 正确读法 |
|---|---|---:|---:|---|
| EV Csca× 7.10x | §6.2 | 2 | 6 | Mie 推导，不解锁 calibration |
| peak× 2× (404 vs 660 nm) | §2.4 | 2 (Mie) × 3 (surrogate) | 6 | surrogate 相对放大，不解锁 absolute peak unit |
| detection 12.52% / 47.15% | §6.4 / §7 | 3 (synthetic relative-prior) | 6 (event probability) | 合成相对先验代理计数比例，**不是事件概率** |
| γ = 0.749, s_SNR = 0.728 | §11.7 | 4 | 5 或 6 | reproduction-lens 估计项，不是物理常数 |
| (W / 800)^2 width-prior | §10.4 | 5 | 6 | 解释模型，不是物理定律 |
| 0.5–0.8 selected-annulus 窗口 | §4 / §11 | 5 (canonical) | 5 但**不可移动**（§15）| canonical default，移动需另起 sensitivity 流程 |
| Wilson LB | §2.2 阶段 7 | 3 | 3（被误读为"安全下界"）| finite-event statistical lower bound，**不是** safety bound |

---

## §14 Tsuyama 6 篇论文逐篇对照

按论文角色总览 → 6 篇分论文条件对照 → 整体结论顺序展开。这里数值已经在 §6 / §7 / §11.3 引用过，本节只把它们组织成论文条件 → 当前模型对照 → 判定的形式。

### 14.1 6 篇论文角色总览

| 论文 | 年份 | 对当前主线的约束强度 | 当前对照方式 | 主要作用 |
|---|---|---|---|---|
| Tsuyama 2019 POD | 2019 | 中 | POD 热效应边界 + 衍射光读出区域 | 支持衍射光读出与小通道 POD 可行性；不直接校准 EV NODI |
| Tsuyama 2020 单纳米通道衍射 | 2020 | 高 | 固定 633 nm 衍射与参考场对照 | 参考场、宽度与深度趋势强对齐 |
| Tsuyama 2020 POD 纳米颗粒计数 | 2020 | 中 | POD 计数边界 + 流动 / 读出时间尺度 | 支持毫秒级瞬态与金颗粒 POD 可检测性 |
| Tsuyama 2020 溶剂增强 POD | 2020 | 中 | 热效应与溶剂边界 | 边界控制；不做 NODI 热效应定量 |
| **Tsuyama 2022 NODI** | 2022 | **高** | 接近论文条件的 NODI 对照 + 金颗粒对照 | **口径 B 中心对照论文** |
| Tsuyama 2024 POD + NODI | 2024 | 高 | 双频读出与 POD / NODI 配对语义 | 配对读出方向对齐；未复现完整电子链路 |

### 14.2 Tsuyama 2019 POD (Nonfluorescent Molecule Detection)

**论文重点**：非荧光分子 POD 检测；信号在衍射光区域；约 400 × 400 nm 通道下 LOD ≈ 5.0 µM；200 × 200 nm 下按 detection volume 不显著恶化。

**当前模型对照**：

| 项 | 论文 | 当前模型 | 判定 |
|---|---|---|---|
| 检测机制 | 光热衍射 POD（分子级）| NODI 散射干涉（颗粒级）| out-of-scope |
| 通道尺度 | 200×200 至 400×400 nm² 截面 | EV / NODI 主路线 500–900 nm 宽，论文对照 800 × 550 nm | out-of-scope |
| 衍射光读出区域 | 核心机制 | v2 用 BFP / slit / pinhole 显式约束 | match（方向）|
| 小通道 LOD | 论文给绝对值 | 当前禁止 absolute LOD claim | out-of-scope |
| 热扩散到玻璃基底 | 核心物理项 | v2 不做完整热源；旁路只作 boundary | boundary |

**结论**：支持衍射光区域作为读出区域 + 小通道不天然不可用的趋势；**不能**把 POD 分子 LOD 外推为 EV NODI 事件概率。

### 14.3 Tsuyama 2020 diffraction (Characterization of Optical Diffraction by Single Nanochannel)

**论文条件**：633 nm He-Ne 探测 + 照明物镜 NA 0.45（20×）+ 收集 NA 0.9 + lock-in 1.1 kHz + time constant 1 s + 通道宽 / 深变化。

**当前模型与论文条件参考场振幅对比**（§6.3 已给）：平均绝对差异 ≈ 2.13%、最大 ≈ 9.20%。

**结论**：当前模型最强的参考场约束来源；支持"空白通道是相位滤波结构 + 参考场幅值方向"；**不**支持"所有绝对衍射强度已逐图复现"。

### 14.4 Tsuyama 2020 counting POD (Detection of Individual Nanoparticles)

**论文条件**：通道 ≈ 800 × 710 nm；压力 100 kPa；流速 0.17 mm/s；lock-in 1.1 kHz + τ = 2 ms；颗粒 20 nm Au；POD counting 下接近 100% 检测。

**当前模型对照**（§6.4 表 D）：

| Au 粒径 | 当前 NODI 散射检出 (660 / 800 × 500) | 论文 POD 热计数 | 判定 |
|---:|---:|---|---|
| 20 | 0.0% | ≈ 100% | out-of-scope（POD → NODI 不可外推）|
| 30 | 14.6% | — | partial（同向）|
| 40 | 26.6% | — | match（同向）|
| 50 | 30.5% | — | match（同向）|
| 60 | 31.5% | — | match（同向）|

**结论**：POD 100% Au20 检出**不能**外推为 NODI 散射 100%；当前 Au20 在 NODI 上 0% 与 §14.4 Au20 weak-SNR / not-all-detected 描述相容。

### 14.5 Tsuyama 2020 solvent-enhanced POD (Concentration Determination)

**论文条件**：532 nm 激发 + 633 nm 探测 + 通道 ≈ 400 × 400 nm；solvent dn/dT 主导；solvent enhancement > 30×；LOD = 75 nM；sign flip 可发生。

**当前模型对照**：

| 项 | 论文 | 当前 v5.0 | 判定 |
|---|---|---|---|
| solvent dn / dT | 核心变量 | 不在 NODI 主模型 | out-of-scope |
| solvent enhancement | > 30× | 不评估 | out-of-scope |
| LOD | 绝对值 75 nM | 禁止 absolute LOD claim | out-of-scope |
| sign flip | POD 特征 | NODI 不当作 sign-preservation 替代指标 | boundary |

**结论**：边界控制——POD 热效应与溶剂增强可以很强，但**不是** EV NODI 散射可检测性的直接校准来源。

### 14.6 Tsuyama 2022 NODI (Nanofluidic Optical Diffraction Interferometry — 口径 B 中心对照)

**论文条件**：探测 660 nm；收集 NA 0.9；slit 1 mm；pinhole 400 µm；time constant 1–2 ms；压力 100 kPa；流速 0.2 mm/s；通道 ≈ 800 × 550 nm。

**当前模型对照（多种 lens 下的同 lens 比较）**（§6.4 表 B）：

| Lens | 404 / 500 × 800 | 660 / 800 × 550 | 660 / 800 × 1400 | 660 / 900 × 1200 |
|---|---:|---:|---:|---:|
| NODI engineering stable det (%) | 33.65 | **47.15** | 45.15 | 42.60 |
| 2020 paper lens (%) | 34.50 | 43.50 | 41.00 | 44.20 |
| 2022 NODI paper lens (%) | 35.40 | **46.70** | 42.90 | 47.05 |

**结论**：

1. 固定到 2022 NODI 语义后，660 nm 仍强于 404 nm
2. 最优几何向论文器件附近 800 × 550 收缩（在 NODI engineering lens 与 2022 paper lens 下都是 47% 左右）
3. 工程主线 660 / 800 × 1400 / 1500 与 paper 几何 800 × 550 在多 lens 下方向一致；但 main-660 锁的是工程几何，**不**因 paper geometry cross-check 发生 route promotion 或 main-660 redefinition

口径 B reproduction lens 链（Phase 2 / 2.5 / 2.6–2.11）已经在 §11.2 详细展开。

### 14.7 Tsuyama 2024 POD + NODI (Simultaneous Light Absorption and Scattering)

**论文条件**：探测 660 nm + 激发 532 nm；time constant 1–2 ms；frequency split 1.2 / 4.1 kHz；通道宽 800–1200 nm + 深 ~550 nm；POD + NODI 配对脉冲读出。

**当前模型对照**（§6.4 表 E）：

| 读出方式 | strict gate 通过比例 | mean detection (%) |
|---|---:|---:|
| in-phase + phase-gated | 0.00 | 18.28 |
| in-phase no gate | 0.45 | 18.28 |
| magnitude | 0.45 | 18.15 |

**结论**：读出方式切换显著改变 pass / fail 判定，但 mean detection 几乎不变。配对 POD + NODI 电子链路与分类协议**不**复现。

### 14.8 整体结论：趋势对齐，未完成数值校准

```text
当前模型和 Tsuyama 的关系是 "趋势一致、固定论文条件下已检查"，
不是 "已按论文数值完成校准"。

强约束: 2020 diffraction、2022 NODI、2024 POD + NODI（参考场 + 660 nm 主波长 +
        毫秒级读出 + 脉冲观测量 + 读出口径 方向对齐）
边界控制: 2019 POD、2020 counting POD、2020 solvent-enhanced POD（POD 热效应 / 溶剂 /
        分子检测论文不能直接校准 EV NODI 散射）
```

**不可签发**：accepted paper-calibrated candidate；classification accuracy 已复现；论文全部数值已逐图复现。

---

## §15 当前可发布与禁止的结论清单（unified forbidden claim）

### 15.1 可以发布的（双口径分别 + 共同）

**双口径共同可发布**：

```text
- 合成相对先验证据；
- 受限仪器情景下的相对先验判断；
- 锁定路线在合成模型内的稳定性；
- 近壁网格、路线角色和窄通道风险先验的审计结论；
- P0 相对审计与 P6 / P8 / P10 / P12 / P14 / P16 trace-only 排名不稳定结论；
- ET-2030 + LI5640 instrument-aware feasibility 量级估计；
- 未来进入实测或校准前必须补齐的 artifact 清单。
```

**口径 A 可发布**：

```text
- 在合成相对先验模型内，660 nm + 800 × 1400 + 800 × 1500 nm 为 conditional_relative_main 集合；
- 窄通道 context 路线高分由 width-prior 与多轮审计降级为 surrogate_sensitive_not_promoted；
- main-660 不能从 trace-only lane 中挑单一冠军。
```

**口径 B 可发布**：

```text
- 当前选型已冻结（§11.7）；按 D2.1 best + γ = 0.749 + 选定几何 + 推荐硬件接法出最终结果；
- formula-consistent Ag / Au signal proxy 已通过 raw signal-ratio target；
- ET-2030 + LI5640 + current input / TIA 是推荐接法（216 / 216 comfortable）；
- 50 Ω voltage path 不被推荐（211 / 216 below sensitivity）。
```

### 15.2 不能发布的（unified forbidden claim）

```text
- 校准信噪比；
- 校准事件概率；
- 绝对检出限 (LOD)；
- 真实 EV 浓度；
- 生物特异性；
- 实测空白样本安全性；
- 探测器电压 / 样品计数预测；
- 路线直接升级（口径 A）或 accepted paper-calibrated candidate（口径 B）；
- main-660 重新定义；
- selected-annulus 替代 all-crossing 主排序，反之亦然（**双向并立 forbidden**）；
- selected-annulus 边界变更（0.5–0.8 固定）；
- P6–P16 trace 排名当作路线升级或单一冠军结论；
- estimated-parameter reproduction lens 当作 raw physical calibration；
- classification accuracy 已本地复现（本地 sklearn 不可用，仍 no_accuracy_claim）；
- γ response compression 当作真实物理定律；
- 当前 γ / SNR scale / SNR response exponent 当作仪器物理常数（reproduction-lens 估计项）；
- 404 nm 热效应旁路加分；
- Tsuyama 论文 Table S1 / classification 数值已被 raw 参数自然复现；
- 把 §13 第 3 / 4 / 5 档证据数字当作第 6 档校准 / 实测值。
```

---

## §16 Open dependencies 与下一步需要的实测

### 16.1 P19 evidence-strategy gate 必须做什么

P19 是双口径共同下一步硬依赖。任何 P19 计划必须：

1. **同时**为两个口径声明 acceptance criteria，不允许只覆盖一边
2. 口径 A 至少包含：`measured_blank_bfp` / standard particle transfer / slit-ROI scan / full-wave spot-check
3. 口径 B 至少包含：measured Au raw trace + blank + BFP / slit / ROI 扫描 + lock-in / logger
4. 把口径 B 冻结参数集（§11.7）当作 P19 baseline，**不允许**视为"过渡候选"再做新一轮 reproduction-score 搜索
5. 引用 §12.3 going-forward 治理原则与本节 §16 全部条目

P19 设计若只覆盖一个口径，**不是**合法 P19 计划（双口径并立的强一致约束）。

### 16.2 实测 artifact 优先级清单

```text
优先级 1: measured Au raw trace（推进口径 B step 1 校准从 reproduction-lens 到 calibrated）
优先级 1: measured blank / BFP / slit / ROI scan（推进口径 A main-660 与口径 B reference 模型）
优先级 2: lock-in / logger 配置实测（验证硬件接法量级估计）
优先级 2: PEG / fluidic 流体可行性数据（验证 width-prior 解释）
优先级 3: EV polydispersity / non-sphericity / coincidence / blended pulses（v2 未建模现实因素）
优先级 3: roughness / fabrication background / PEG fouling / drift（post-v2 validation）
```

### 16.3 P19 之前能做与不能做

| 类别 | 能做 | 不能做 |
|---|---|---|
| 算法 / 参数 | 不再扩大 reproduction-lens 自由度；按 v5.0 / §11.7 冻结参数输出最终结果 | 在没有 measured artifact 之前重启 broad raw-parameter sweep |
| 报告 | 修订表述 / 改善读者向解释（v5.0 即此类）| 把冻结参数当 calibration |
| 路线 | 保留 main-660 conditional_relative_main 集合 | route promotion / main-660 redefinition |
| 测量 | 设计 P19 实测计划（双口径同时覆盖）| 把任何单口径计划等同于 P19 |

---

## §17 Evidence trail / provenance

### 17.1 口径 A 主线证据（v1 + v2 全量库 + post-v2 P0–P18）

```text
v1 全量库:
    results/ev_nodi_realism_v2_full_grid_R5_v2/
    （32,032 设计 × 8 情景 = 256,256 行）

v2 收口报告:
    reports/51_EV_NODI_realism_v2_instrument_aware_roadmap.md
    reports/75_EV_NODI_realism_v2_R6_route_prior_sensitivity_audit_analysis.md
    reports/77_EV_NODI_realism_v2_R7_route_prior_mechanistic_decomposition_audit_analysis.md
    reports/81_EV_NODI_realism_v2_R7_2_operator_artifact_gap_register_generation_analysis.md
    reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md
    reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md
    results/ev_nodi_realism_v2_R6_route_prior_sensitivity_audit/
    results/ev_nodi_realism_v2_R7_route_prior_mechanistic_decomposition_audit/
    results/ev_nodi_realism_v2_R7_2_operator_artifact_gap_register/
    results/ev_nodi_realism_v2_no_measured_data_closure/

post-v2 P0 audit + P1–P18 (审计 + 6 trace + synthesis):
    reports/90 … 120
    results/post_v2_mandatory_audit/
    results/post_v2_minimal_bounded_solver_execution/
    results/post_v2_second_bounded_solver_lane_execution/
    results/post_v2_third_bounded_solver_lane_execution/
    results/post_v2_fourth_bounded_solver_lane_execution/
    results/post_v2_fifth_bounded_solver_lane_execution/
    results/post_v2_sixth_bounded_solver_lane_execution/
    results/post_v2_bounded_lane_synthesis_stop_continue/
```

### 17.2 口径 B 主线证据（Phase 2 / 2.5 / 2.6–2.11 + 仪器可行性 + 论文统计）

```text
口径 B paper-audit 主源（reports / 49 / 71 / 70）:
    reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md  (Phase 2 / 2.5–2.11)
    reports/70_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_plan_for_external_review.md
    reports/71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md  (sidecar)

口径 B results 目录:
    results/tsuyama_phase2_paper_target_audit_v1/
    results/tsuyama_phase2_acceptance_baseline_v1/
    results/tsuyama_phase2_parameter_inverse_full_v1/
    results/tsuyama_phase2_acceptance_full_inverse_v1/
    results/tsuyama_phase2p5_operator_phase_bfp_smoke_v1/
    results/tsuyama_phase2p5_operator_phase_bfp_acceptance_smoke_v1/
    results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/    # D2.1 best
    results/tsuyama_phase2p5_d2p1_refphi_collection_acceptance_v1/
    results/tsuyama_phase2p6_paper_reproduction_fit_d2p1_v1/
    results/tsuyama_phase2p6_paper_reproduction_fit_full_inverse_v1/
    results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/
    results/tsuyama_phase2p6_paper_reproduction_fit_3000e_acceptance_v1/
    results/tsuyama_phase2p7_snr_response_rescore_3000e_v1/
    results/tsuyama_phase2p8_reviewed_score_rescore_3000e_v1/
    results/tsuyama_phase2p9_maximal_upper_rescore_3000e_v1/     # 与 d2p1 / full inverse 三套
    results/tsuyama_phase2p10_size_response_decomposition_3000e_v1/
    results/tsuyama_phase2p11_response_compression_rescore_d2p1_v1/  # γ = 0.749 最终
    results/instrument_hardware_feasibility_v1/                  # ET-2030 + LI5640 216 配置
    results/tsuyama_paper_statistics_sensitivity_v1/             # 288 行
    results/ev_nodi_realism_v2_R5_2_bounded_scenario_prior_audit/
```

### 17.3 Tsuyama 文献证据（双口径共用）

```text
archive/tsuyama/48_tsuyama六篇严格补读结论.md
archive/tsuyama/51_tsuyama_paper_aligned全论文闭环审查.md
archive/tsuyama/56_tsuyama已解决与尚未解决问题_中英对照表.md
archive/tsuyama/57_工程主线与Tsuyama论文结果趋势对照_中英对照.md
archive/tsuyama/58_tsuyama固定条件对标与结果表.md

papers/:
    Tsuyama_Mawatari_2019_Nonfluorescent Molecule Detection.pdf
    Tsuyama和Mawatari - 2020 - Characterization of optical diffraction by single nanochannel.pdf
    Tsuyama_Mawatari_2020_Detection and Characterization of Individual Nanoparticles.pdf
    Tsuyama_Mawatari_2020_Concentration Determination at a Countable Molecular Level.pdf
    Tsuyama_Mawatari_2022_Nanofluidic optical diffraction interferometry for detection and classification.pdf
    Tsuyama和Mawatari - 2024 - Nanofluidic detection platform.pdf
```

### 17.4 v3.0 → v4.0 → v4.1 → v4.2 → v5.0 ledger

```text
reports/121_EV_NODI_full_update_review_ledger_2026-05-11.md  (v3.0 → v4.0 全量合并审计)
reports/122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md
    包含: v4.0 dual-lens consolidation + v4.0 lens-B parameter freeze
         v4.1 §16 reader-explainer layer
         v4.2 two-step lens-B framing + ms / % many-table reformat
         v5.0 reader-centric full restructure（本版本）
```

---

## §18 历史与版本演化

### 18.1 supersession（这份报告替代了什么）

本报告 88（v5.0 reader-centric restructure）是**当前全量读者向报告**。如下旧报告的读者面结论已并入本报告：

| 历史报告 | 替代位置 | supersession_reason |
|---|---|---|
| reports/47_EV_NODI全量结果分层分析报告.md | 本报告（v5.0）| 全量库 v1 历史分析；现在的读者面结论在本报告 §6 / §10 |
| reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md | 本报告 §11 / §11.2 | Phase 2 / 2.5–2.11 reader-facing 结论；49 仍为口径 B raw provenance |
| reports/70 + 71 | 本报告 §12.2 | R5.2 sidecar reader-facing 结论；70 / 71 仍为 sidecar raw provenance |
| reports/9[1-9] + 1[0-1][0-9] + 120 | 本报告 §5.3 / §10.5 | P1–P18 阶段报告 reader-facing 结论；阶段报告仍为 trace_only_provenance |

### 18.2 v3.0 → v5.0 演化记录

| 版本 | 日期 | 主要内容 |
|---|---|---|
| v3.0 | （v4 之前）| 仅口径 A；selected-annulus 仅 §11 / §13 一处指针提及 |
| v4.0 | 2026-05-11 | 双口径并立；§14 selected-annulus 等规模并入；§15 双口径综合；reports/49 + 71 等规模并入；reports/122 ledger 建立 |
| v4.0 amendment | 2026-05-11 | 口径 B 当前参数集冻结为选型（在 v4.2 §14.12 / 14.13 / 14.14；在 v5.0 重新组织为 §11.7 冻结参数 + §14.6 Tsuyama 2022 NODI 对照 + §11.6 硬件接法）|
| v4.1 | 2026-05-11 | 新增 §16 读者向解读层：物理链 + 估计值来源 + 变量影响排序 + 推荐因果链 |
| v4.2 | 2026-05-11 | §16.9.2 改两步框架（用户反馈 1）；§16.3 / §16.4 改 ms / % 多表（用户反馈 2）|
| **v5.0** | **2026-05-11** | **reader-centric 全文重构**：把层层叠加结构改为问题 → 物理 → 变量 → 数据 → 分析 → 推荐 → 边界 → 出处的一次性叙事；代码层 ID 改名为可读科学命名；附录给出对照 |

### 18.3 v5.0 重构的不变量（不会被改名 / 改顺序改变的事实）

```text
1. 全部数值结论与 v4.2 一致；
2. 全部 forbidden claim 与 v4.2 一致；
3. 口径 B 冻结参数集 (γ = 0.749, s_SNR = 0.728, e_SNR = 0.812, D2.1 best 算子,
   selected-annulus 0.5–0.8, lock-in τ = 1–2 ms, ET-2030 + LI5640,
   current input / TIA, Au panel 20 / 30 / 40 / 60 nm,
   geometry 660 / 1200 × 550 + 660 / 800 × 550) 与 v4.2 一致；
4. 双口径并立、互不替代的治理原则与 v4.0 起一致；
5. selected-annulus 0.5–0.8 固定不可移动；
6. raw provenance 来源不变：reports / 49 (口径 B Phase 2 / 2.5–2.11) + reports / 71 (R5.2 sidecar)。
```

---

## 附录 A：术语表（描述名 ↔ 代码 ID 对照）

| 描述名（本报告主要用语）| 代码 ID / 短码 | 含义 |
|---|---|---|
| 全局响应压缩因子 γ | `paper_reproduction_response_compression_gamma`, `gamma` | 把 raw 模型 peak 高度按 peak^γ 重映射，让 Au size exponent 从 ≈ 3.05–3.19 落到 Tsuyama 论文的 2.3；reproduction-lens 估计项，**不是**物理常数 |
| 全局 SNR 缩放因子 s_SNR | `paper_reproduction_global_snr_scale`, `snr_scale` | 把 Au20 / Au30 局部 SNR 平移到 Tsuyama 论文 anchor |
| 全局 SNR 响应指数 e_SNR | `paper_reproduction_snr_response_exponent`, `snr_response_exp` | Phase 2.7 引入，调节 SNR ratio 的相对 scaling |
| 选定探测算子 | `tau_2ms_global_refphi_plus_collection_narrow`（D2.1 best）| 2 ms 锁相 + 全局参考相位正向位移 + 窄收集窗 |
| 探测算子 family D2 | `D2_operator_phase_bfp_raw` | Phase 2.5 D2 raw-operator family |
| 探测算子 family D2.1 | D2.1 局部 12 variants | D2 加密的局部 smoke，最优解 = D2.1 best |
| 主路线 1 | `main_660_W800_D1400` | 660 nm + 800 nm 宽 + 1400 nm 深 |
| 主路线 2 | `main_660_W800_D1500` | 660 nm + 800 nm 宽 + 1500 nm 深 |
| 短波探针路线 | `probe_404_W600_D1300` | 404 nm + 600 nm 宽 + 1300 nm 深 |
| 弱参考场对照路线 | `control_660_W700_D1500` | 660 nm + 700 nm 宽 + 1500 nm 深 |
| 可选稳健性探针路线 | `optional_660_W900_D1400` | 660 nm + 900 nm 宽 + 1400 nm 深 |
| 条件性相对主路线 | `conditional_relative_main` | 在合成相对先验框架内的主路线（不是绝对校准主路线）|
| 对替代量级敏感、未晋升 | `surrogate_sensitive_not_promoted` | 被 P0 audit 降级；不允许按 v1 高分直接晋升 |
| 仅作为弱参考场对照 | `weak_reference_control_only` | 不替代 main-660；不允许 route promotion |
| 仅作为可选稳健性探针 | `optional_robustness_probe_only` | 同上 |
| 仅作为短波探针 | `shortwave_probe_only` | 同上 |
| 仅作为论文条件 sanity | `paper_sanity_only` | 仅论文条件 cross-check，不替代 main-660 |
| 选定环带 | `selected_annulus` | 初始粒子位置在通道边缘 0.5–0.8 比例环带 |
| 全 crossing 排序 | `all_crossing` / `all-crossing` | 不挑分母 condition，全 BFP 全 crossing |
| 选定环带不替代全 crossing 主排序 | `selected_annulus_replaces_all_crossing_ranking = false` | 双向并立 forbidden 一条 |
| 选定环带边界不可移动 | `selected_annulus_bound_change_authorized = false` | 0.5–0.8 固定 |
| 路线晋升不许可 | `route_promotion_authorized = false` | 不得 route promotion |
| main-660 重新定义不许可 | `main_660_redefinition_authorized = false` | 不得 redefine main-660 |
| 校准声明不许可 | `calibrated_claim_allowed = false` | 全文 forbidden |
| 实测数据未授权摄入 | `measured_data_ingest_authorized = false` | 全文 forbidden |
| 公式自洽信号比 | `formula-consistent` | 论文 Csca 列开方比 vs interferometric 列比；当前 best loss ≈ 0.041 pass |
| 总复现 score | `total_reproduction_score` / Phase 2.11 best | 多目标 lower-is-better penalty；当前 2.033 |
| 候选 release 状态 | `release_status` | accepted / negative / diagnostic / **negative_or_diagnostic_result_only** |
| raw 粒径响应未对齐 | `raw_size_response_alignment_not_met` | 口径 B 主 No-Go |
| BFP | back focal plane | 后焦面 |
| ROI | region of interest | 感兴趣区域 |
| Wilson LB | Wilson lower bound | 有限事件数下 detection_rate 的统计下界 |
| transit time | — | 粒子穿过 beam waist 的时间，按 beam_diameter / v_flow 估算（§6.1）|

---

## 附录 B：公式简表

| 阶段 | 公式 | 关键变量 | 证据档位 |
|---|---|---|---|
| 1 | Csca = Qsca · π a²；dCsca/dΩ = (\|S1\|² + \|S2\|²) / (2 k²)；\|E_sca,unit\| = √(dCsca/dΩ) | a, n, k, λ | 2（Mie 推导）|
| 2 | E_sca,detected = L_det[ field_sca(θ, φ) ] | 收集算子 L_det | 3（surrogate）|
| 3 | E_sca(t) = E_env(t) · E_sca,unit · f_coupling(t) · exp(i · φ_extra(t)) | 照明 / 耦合 / 路径相位 | 3（surrogate）|
| 4 | E_ref(t) ~ L_det[E_diff,ch] | channel-angular surrogate | 3（surrogate）|
| 5 | signal_trace = \|E_sca\|² + 2 · Re(E_ref · E_sca*)  ← **相加，不相乘** | E_ref, E_sca, Δφ | 2 + 3（公式 + surrogate）|
| 5 强参考场极限 | peak ≈ 2 \|E_ref\| \|E_sca\| cos(Δφ) ≈ \|E_ref\| · √Csca | — | 2 + 3 |
| 6 | post-readout = lock-in(signal_trace + pre-noise) + post-noise | τ, in-phase / magnitude, noise_std | 3 |
| 7 阈值 | threshold = median(bg) + threshold_sigma · 1.4826 · MAD(bg) | threshold_sigma, MAD | 5（可接受先验）|
| 7 脉冲 | find_peaks(height ≥ threshold, width ≥ min_peak_width, distance ≥ min_peak_interval) | — | 3 |
| 7 batch | detection_rate = n_detected / n_events；selected_annulus_detection_rate (§4) | edge_norm, annulus 0.5–0.8 | 3 + 5 |
| Reproduction lens (口径 B) | (peak')^γ；SNR_obs = s_SNR · (SNR_raw)^e_SNR | γ = 0.749, s_SNR = 0.728, e_SNR = 0.812 | 4（reproduction-lens 估计项）|

---

## 附录 C：表格索引

按变量类型分组找表：

| 你想找的内容 | 去 § | 表 ID |
|---|---|---|
| transit 时间随波长 | §6.1 | 表 6.1 |
| EV biomimetic Csca 随波长 | §6.2.1 | 表 6.2.1 |
| Au plasmonic Csca 随波长 | §6.2.2 | 表 6.2.2 |
| Au 粒径阶梯 Csca | §6.2.2 | 表 6.2.2 第二张 |
| \|E_ref\| 随几何 | §6.3 | 表 6.3 |
| EV biomimetic all-crossing detection 总表 | §6.4 | 表 6.4.A |
| NODI engineering lens stable detection | §6.4 | 表 6.4.B |
| Au paper-audit selected-annulus 跨波长 | §6.4 | 表 6.4.C |
| Au 粒径阶梯 detection | §6.4 | 表 6.4.D |
| 660 nm 读出方式对照 | §6.4 | 表 6.4.E |
| 固定几何看波长（5 张）| §7.1 | 表 7.1.1–7.1.5 |
| 固定波长看几何（5 张）| §7.2 | 表 7.2.1–7.2.5 |
| 口径 B 几何选型数据根据 | §7.3 | 表 7.3.1 |
| 三 lens 同时排列 | §7.4 | 表 7.4 |
| 噪声归因 | §8.4 | 表 8.4 |
| 变量影响 10 项排序 | §9 | 表 9 |
| 口径 A 推荐 detection 增益 | §10.3 | 表 10.3 |
| 口径 A 路线治理裁决总表 | §10.5 | 表 10.5 |
| 口径 A width-prior 模型对照 | §10.4 | 表 10.4 |
| 口径 B Step 1 校准产物 | §11.2.2 | 表 11.2.2 |
| 口径 B Step 1 score 分解 | §11.2.3 | 表 11.2.3 |
| 口径 B Step 2 选型 5 维度 | §11.3 | 表 11.3 |
| 口径 B 硬件接法 | §11.6 | 表 11.6 |
| 口径 B 冻结参数集 | §11.7 | 表 11.7 |
| 双口径同一证据对照 | §12.2 | 表 12.2 |
| 估计值 6 档来源谱 | §13 | 表 13 |
| 高频被误读数字读法 | §13 | 表 13（第二张）|
| Tsuyama 6 篇角色总览 | §14.1 | 表 14.1 |
| Tsuyama 2022 NODI 多 lens 对照 | §14.6 | 表 14.6 |
| Forbidden claim 完整列表 | §15.2 | 表 15.2 |

---

（v5.0 报告主体结束。完整内容版次、不变量、保留 forbidden 与冻结参数列表见 §18.3。下一步硬依赖见 §16。）
