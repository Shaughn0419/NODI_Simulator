# EV/NODI 综合分析报告 v5.2.1：reader comparison table pack + consistency hotfix

- 日期：2026-05-12（v5.1.1 hotfix + v5.2 reader comparison pack + v5.2.1 consistency hotfix）；v5.1 reader table 初版日期：2026-05-12；v5.0 主体重构日期：2026-05-11
- 版本：**v5.2.1（reader comparison table pack + consistency hotfix）**——在 v5.1 (4106d38) 基础上：
  - **v5.1.1 hotfix（codex 第三轮反馈 P0 + P1）**：新增真实 §6.4.F (4 波长信号链汇总)，让所有先前引用 `§6.4.F` 的位置不再悬空；§2.4 拆为"严格物理阶段量"块 A + "route-level evidence" 块 B，避免 strict / route-level 混读；§8.6 reference×2 修正逻辑（noise model 不变 → threshold 不同步上抬）；§10.6 把 mixed-lens cell 拆成 all-cross + NODI 两列；统一 detection 表头为 `synthetic detection score (%)` / `proxy (%)`；修正 §8.5 / §8.6 takeaway 表号；修复 `window-prior` → `width-prior` 拼写。
  - **v5.2 reader comparison pack**：新增附录 D（5 张固定 W × H vary λ 表）+ 附录 E（5 张固定 λ vary W × H 表）+ 附录 F（strict controlled vs route-level 14 行对照矩阵）。每张表都明确 source type / strict controlled? / baseline / lens / panel，detection cell 只在 source type 标为 strict 直接行时填数字，否则填 `—` 并在 note 列说明最近邻。
  - **v5.2.1 consistency hotfix（codex 第四轮反馈）**：修正 report 47 CSV 存在性表述；同步 header / ledger 版本标识；清理遗漏 detection 表头、mixed-lens cell、附录 F strict 规则、Markdown 表格转义、行数和空白字符。
- **所有数值结论、forbidden claim、release status 和冻结参数与 v5.0 / v4.2 完全一致**。**精确表述**：v5.1–v5.2.1 不引入新 simulation / solver case / candidate / lane / random seed / measured artifact ingest；新增内容仅为既有结果的**派生重组、单位换算、物理近似解释和读者向诊断表**（包括 §6.4.F 信号链汇总、§7.2.5a 信号链扩列、§8.6 假想 sensitivity 数值版、§13.2 阶段量来源映射、附录 D / E / F 等"derived reader table"）。这些派生表的 baseline / source / aggregation method 都在表头或下方明确标注。
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

### 0.3a 一页版读者地图（5 行回答 5 个问题）

| 你想知道 | 一句话答案 | 详细见 |
|---|---|---|
| 问题 A 是什么 | EV / NODI 工程主线推荐 | §1.1 |
| 问题 B 是什么 | Tsuyama 论文数值能否被估计参数复现 | §1.2 |
| 当前推荐是什么 | 口径 A：660 nm + 800 × 1400 / 1500 nm 双 main 集合；口径 B：D2.1 best 算子 + γ = 0.749 + 660 / 800 × 550 + 660 / 1200 × 550，**release_status 仍 negative_or_diagnostic_result_only** | §10 / §11 |
| 不能下哪些结论 | 校准 SNR / LOD / 真实浓度 / 生物特异性 / 替代主排序 / 移动 selected-annulus / 把 γ 当物理常数 / route promotion / classification accuracy 已复现 | §15.2 |
| 下一步要做什么 | P19 evidence-strategy gate 双口径同时声明 acceptance criteria + 优先获取 measured Au raw trace + measured blank / BFP / slit / ROI | §16 |

### 0.3b 读者问题导航表（10 个最常被问的问题 → 报告位置）

| # | 读者问题 | 在哪里回答 | 主要看哪张表 / 段 | 结论口径 | 注意事项 |
|--:|---|---|---|---|---|
| 1 | 这个通道尺寸对粒子的 detection proxy 是多少？ | §6.4 + §7.2 | 表 6.4.A（口径 A）+ 7.2.x | EV biomimetic + all-crossing | 数字是 synthetic detection score，**不是**实测事件概率 |
| 2 | 为什么检测不到？主要 blocker 是什么？ | §8.5 blocker 分类 | 表 8.5 | 双口径共用 | blocker 不是单一原因，要看 reference / noise / threshold / route gov 多条 |
| 3 | 固定尺寸时不同波长在 Mie / reference / peak / detection 上差多少？ | §6.4.F + §7.1 + §2.4 | 表 6.4.F（4 波长信号链分解）| 双口径分别给 EV + Au | 倍数列只用于阶段量；detection 列保留 % |
| 4 | 固定波长时不同 W / H 对 peak / transit / detection 影响多大？ | §7.2 + §10.4 | 表 7.2.1–7.2.5 + §10.4 width-prior | 口径 A all-crossing | 通道几何**不**改变 Csca（颗粒固有量）；改变的是 reference / 路径 / transit |
| 5 | 404 nm 为什么本征散射更强但不一定推荐？ | §2.4 + §6.4.F + §10.2 | 表 2.4 + 6.4.F | 口径 A | peak↑ 但 transit↓、phase flip↑、margin↓ → detection 反而 ↓；详 §8 |
| 6 | 660 nm 为什么是 main route？ | §10.2 因果链 5 步 + §10.6 裁决表 | 表 10.6 | 口径 A | 不是单指标最优，是 width-prior + R5.2 + P0 audit + 近壁细网格一致结果 |
| 7 | 噪声到底影响多大？ | §8.4 + §8.6 | 表 8.4 + 表 8.6 | 双口径共用 | 三个理由：参考场不放大噪声、阈值随噪声同步上抬、短波长 transit/sample 衰减 |
| 8 | reference field 增强这么多倍，为什么噪声还重要？ | §8.1–§8.3 + §3.0a | §3.0a 阶段量级联 | 双口径共用 | reference 放大相干一次项不放大非相干噪声；但阈值 / margin / transit 要分别看 |
| 9 | Csca、自散射、干涉项、peak 是不是简单相加 / 简单相乘？ | §3.0a + §2.3 + §2.4 | §3.0a 公式块 + 表 2.4 | 双口径共用 | signal proxy = self term + cross term；强参考场下 cross term 主导，peak ∝ \|E_ref\|·√Csca **不是** \|E_ref\|·Csca |
| 10 | 口径 B 到底怎么从 Tsuyama 数据走到 frozen diagnostic set？ | §11.1–§11.7 + §11.8 | 表 11.8 step 流程 | 口径 B | step 1 校准估计参数 → step 2 在校准 lens 内选 residual 最低；**不是**"为了贴近 Tsuyama 几何而选型" |

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

注意 √Csca 不是 Csca。所以波长把 EV biomimetic 颗粒 Csca 翻 7.1× 时（404 vs 660 nm，Rayleigh 1/λ⁴），peak 大致只放大 √7.1 ≈ 2.66×（再乘 |E_ref| 在相近几何下的弱波长因子约 0.95–1.00 与 cos Δφ 平均后约 0.7–0.9），实际只约 2×。这就是为什么 404 nm 的 peak 增益远比 Csca 增益小。

### 2.4 强参考场极限下的具体放大表（4 波长机制链：404 / 488 / 532 / 660 nm，EV biomimetic + 相近几何）

> **倍数计算口径**：本节所有"相对 660 nm"列都是 `量(λ) / 量(660 nm)` 的比值，baseline 是同一 W × H 同一 EV biomimetic panel 下的 660 nm。常数倍率（例如干涉项里的 `2`）在分子分母同时出现时已抵消，**不会再乘进相对倍数列**。`transit (ms)` 用绝对值；`synthetic detection score (%)` 用绝对百分比。
>
> **重要拆分（v5.1.1 hotfix）**：本节拆为两个数据块。**块 A**（严格物理阶段量）按"同一 W × H + 同一颗粒 panel + vary λ"做 strict controlled comparison；**块 B**（route-level available evidence）只展示 v5.x 报告内可用的 route-class detection 行，这些行**不是** strict λ-only fixed-geometry evidence。两块**不可混读**（详见 §7.0 第 1 条 controlled 比较约束）。

#### 块 A — 严格物理阶段量（strict controlled，同 W × H + 同 panel + vary λ）

| 量 | 660 nm 基线 | 532 nm | 488 nm | 404 nm | 物理 / 推导来源 |
|---|---:|---:|---:|---:|---|
| Mie 散射截面 Csca× | 1.00× | 2.37× | 3.34× | 7.10× | EV Rayleigh: (660 / λ)⁴ |
| 收集场幅值 \|E_sca\|× | 1.00× | 1.54× | 1.83× | 2.66× | √Csca |
| 参考场幅值 \|A_ref\|× | 1.00× | ≈ 1.00× | ≈ 1.00× | ≈ 0.95–1.00× | §6.3 衍射对照：在所考察 W × H 范围内 \|A_ref\| 波长方向因子约 ±2–9%；除 404 nm 在深通道偏低外，488 / 532 与 660 接近 |
| 干涉一次项 cross term× = \|A_ref\|·\|E_sca\| | 1.00× | ≈ 1.54× | ≈ 1.83× | ≈ 0.95 × 2.66 ≈ 2.5× | factor 2 在比值中抵消，**不再乘进** |
| 自散射 self term× = \|E_sca\|² = Csca× | 1.00× | 2.37× | 3.34× | 7.10× | self term 比 cross term 小（强参考场极限下被 cross term 主导）|
| 实际 peak×（含 cos Δφ 运行平均 0.7–0.9 因子）| 1.00× | ≈ 1.2–1.4× | ≈ 1.4–1.6× | ≈ 2.0× | cross term × cos Δφ 平均；用户示例表 404 = 2.01× 同 order |
| noise×（surrogate 内 noise 不随 λ）| 1.00× | 1.00× | 1.00× | 1.00× | pre-readout noise_std + post 不显式依赖 λ；noise model 是横向常数 |
| transit 时间窗（绝对 ms）| 8.94 ms | 7.21 ms | 6.61 ms | 5.48 ms | beam waist = 0.61 · λ / NA = 0.61 · λ / 0.45；transit = 2 w_0 / 0.2 mm·s⁻¹ |

> **块 A strict controlled？** ✅ 是。Csca / E_sca / A_ref / cross-term / self-term / peak / noise / transit 都是按"同一 W × H + 同一颗粒 panel + 仅变化 λ"的物理推导值或 surrogate 值；同一基线 660 nm 同 W × H 同 panel。

#### 块 B — Route-level available evidence（**非 strict λ-only**，仅做方向性参考）

| λ (nm) | 来自的 route class（§6.4 表 6.4.A） | EV synthetic detection score (%) | 几何 / panel 是否与块 A 同？ |
|---:|---|---:|---|
| 660 | main_660_W800_D1400 / D1500 类 (896 rows class avg) | 12.61 | ✅ 同 W × H = 800 × 1400 / 1500 同 panel |
| 532 | mid-wave baseline class (488 / 532 混合, 896 rows class avg) | ≈ 7.77 | ❌ 混合几何（class 内多 W × H）；仅作方向性参考 |
| 488 | mid-wave baseline class（同上）| ≈ 7.77 | ❌ 同上 |
| 404 | shortwave probe class (404 / 600 × 1300, 448 rows class avg) | 4.45 | ❌ 几何为 600 × 1300，不是块 A 的 800 × 1400；仅作方向性参考 |

> **块 B strict controlled？** ❌ 否。detection proxy 行是 route-level class evidence，不是 strict λ-only fixed-geometry evidence；v5.x 没有"固定 W × H = 800 × 1400 + 仅扫 λ + EV biomimetic 全 panel" 的直接行（§6.4.F + §7 数据覆盖矩阵已明示）。块 B 只能用来读"在 v5.x 已发布 route-level evidence 下 660 整体优于 404 / 488 / 532"的方向，**不能**反推"在 800 × 1400 nm 几何上 404 nm detection 是 X%"。

读法（4 条）：

```text
读法 1（机制链方向）：从 404 → 660，Csca 单调下降（7.10 → 1）；但 transit 单调上升（5.48 → 8.94 ms）；
                    两条链方向相反，最终 detection proxy 反而是 660 最高、404 最低。

读法 2（不是简单比）：peak× 不等于 √Csca×（因为 |A_ref| 也参与）；detection× 不等于 peak×
                    （因为 transit、phase flip、margin、threshold、route gate 都参与）；
                    所以"短波长 Csca 翻 7×"的直觉**远不能**外推到"detection 翻 7×"。

读法 3（中间波长）：488 / 532 处于 404 与 660 之间，Csca 优势比 660 大但比 404 小；
                  同时 transit 比 404 长一些。所以读者直觉"波长越短越好"在 488 / 532 处就已经开始失效，
                  不是只有 404 极端情况才失效。

读法 4（这是 EV biomimetic 视角）：本表全部对应 EV biomimetic Rayleigh 区颗粒，方向"短波 Csca↑"；
                                Au plasmonic 颗粒方向相反（660 Csca > 532 > 488，§6.2.2 / §6.4 表 6.4.C）。
                                所以"短波散射强"是 EV / dielectric Rayleigh 颗粒规律，不是金颗粒规律。
```

读法（结论）：peak 放大约 2×（404 vs 660）、detection 反而降到 ≈ 0.4× —— 这就是问题 Q4（"peak 放大 N 倍，detection 是否同步放大"）的答案：**不同步**，原因详见 §8 噪声归因。**4 波长一起看**比"只看 404 vs 660"更直观地说明这条非单调关系：488 / 532 不是简单的"中间值"，是同一物理传导链的中段证据。

---

## §3 可调变量与它们的物理含义

本节给变量做一次正名 + 解释。读完本节，读者应该能把后面 §7 / §10 / §11 出现的每个变量映射回它在 §2 物理链上的位置。

### 3.0 变量依赖图（哪个变量影响哪个 downstream 量）

> 这张图把 §3.1–§3.6 的所有变量在 §2 物理链上的连接位置画出来，让读者一眼建立"调谁 → 什么变 → 最终 detection 怎么变"的因果链。

```text
[材料 (§3.1)] ─┐
[粒径 a (§3.1)] ─┼─→ [Csca, S1, S2 (Mie, §2.2 阶段 1)]
                                       │
[波长 λ (§3.2)] ─┼─→ [k = 2π/λ → Csca, |E_sca|]
                 │
                 └─→ [beam waist w_0 ∝ λ/NA → transit time]
                                       │                │
[收集 NA (§3.2)] ─→ [收集算子 L_det → |E_sca,detected|] │
                                       │                │
[流速 (§3.2)] ───────────────────→ [transit time]      │
                                       │                │
[参考场模型 (§3.2)] ─→ [|E_ref| (§2.2 阶段 4)]         │
                                       │                │
[通道宽度 W (§3.3)] ─┬─→ [|E_ref|, 路径相位 φ_extra]   │
[通道深度 H (§3.3)] ─┘                  │                │
                                       ▼                ▼
                            [signal_trace = |E_sca|² + 2|E_ref||E_sca|cos(Δφ)]
                                       │
                                       │ (强参考场极限：peak ∝ |E_ref|·√Csca)
                                       ▼
                            [+ pre-readout 噪声 (§3.4 / §2.2 阶段 6)]
                                       │
[锁相 τ (§3.4)] ────────────→ [lock-in 读出]
[读出方式 (§3.4)] ─────────→  │
                                       ▼
                            [+ post-readout 噪声]
                                       │
[阈值 σ × MAD (§3.4)] ───────→ [阈值 → find_peaks]
[最小 peak 宽度 (§3.4)] ────→  │
                                       ▼
                            [batch detection_rate]
                                       │
[仪器情景 (§3.5)] ──────→ 8 情景重复扩展（不重新跑随机事件）
                                       │
                                       ▼
              ┌────────────────────────┴────────────────────────┐
              ▼                                                  ▼
   [口径 A: all-crossing detection (§4.1)]    [口径 B: selected-annulus detection (§4.2)]
              │                                                  │
              │                            ┌─[γ, s_SNR, e_SNR (§3.6 估计参数)]
              │                            ▼
              │                      [reproduction lens rescore (§4.4)]
              ▼                                                  ▼
   [§10 工程主线推荐]                                  [§11 论文审计两步推荐]
```

读法：

```text
- 变量框越靠左 / 上 = 越上游（影响越广）；
- 颗粒材料和粒径在最上游，所以 §9 排名 1 / 4 是它们；
- 波长 λ 同时影响 Csca、|E_sca|、transit time 三处，所以 §9 排名 3；
- 通道几何 W、H 在中游影响参考场和路径相位，所以 §9 排名 5–6；
- 估计参数 γ / s_SNR / e_SNR 只进入口径 B 的 reproduction rescore，所以只对 §11 选型有影响，对 §10 没有；
- 仪器情景 (§3.5) 是 v2 在 v1 之上的横向扩展，不改变上游变量，只观察路线角色稳定性。
```

### 3.0a 阶段量级联：每个量是谁、归谁管、怎样向下游传导

读者最常踩的两个坑是 (a) 把"通道宽度↑"想象成"Csca↑"；(b) 把"Csca↑ × reference↑ × peak↑"当成可乘的总放大。本节正面回答这两件事，让后面 §6 / §7 / §10 / §11 的阶段量列表都可以一眼读懂。

#### 阶段量是谁、归谁管

| 阶段量 | 符号 | 物理含义 | **由谁决定** | **不由谁决定** |
|---|---|---|---|---|
| Mie 散射截面 | Csca | 单粒子的固有角度积分散射截面 | 颗粒材料 (n, k)、粒径 a、探测波长 λ | **不由通道宽度 W / 深度 H 决定**；通道几何只影响下游的 \|E_sca\| 收集 / \|A_ref\| / 路径相位 |
| 收集场幅值 | \|E_sca\| | 散射场到 detector / annulus 的有效场强（≈ √Csca · 收集算子）| Csca、收集 NA、collection operator (`pupil_slit_surrogate` 等)、几何相位 | 不由 reference 决定 |
| 参考场幅值 | \|A_ref\| | 通道参考场到同一 detector 的有效场强代理 | 通道几何 W / H、波长 λ、参考场模型 (`channel_angular_surrogate` 等)、operating band | 不由颗粒决定（颗粒只贡献散射，不贡献参考场）|
| 干涉一次项 | cross term | 2 \|A_ref\|·\|E_sca\|·cos(Δφ) | 上述两项相乘 + 相对相位 | — |
| 自散射二次项 | self term | \|E_sca\|² | 只来自 \|E_sca\| | — |
| signal proxy | — | self term + cross term（**两项相加，不相乘**）| 上面两项之和 | 不是"放大倍数链相乘" |
| 噪声代理 | noise proxy | pre-readout (高斯 + shot + 漂移) + post-readout | noise model + readout 链路 | **不被参考场放大**（噪声没有相干相位）|
| peak 高度 | peak | 强参考场极限 ≈ cross term 主导 ≈ \|A_ref\|·√Csca | cross term + cos Δφ 平均 + 时间窗 | — |
| peak margin z | margin z | peak / noise proxy（粗略）| peak ↑ → ↑；noise ↑ → ↓；transit / 锁相样本数 ↑ → 估计更稳定 | 不是单纯"peak / 噪声常数" |
| transit 时间 | transit | 粒子穿过 beam waist 时间，beam waist ∝ λ / NA | λ、照明 NA、流速 | 不依赖通道几何（beam waist 由照明决定）|
| detection proxy | — | P(peak > threshold) 的合成相对先验估计 | margin z + threshold + transit / 锁相 sample 数 + phase flip + route gating | 不是 SNR 的单调函数 |

#### 三条简化关系（读者应记住的"骨架公式"）

```text
[阶段 1] signal proxy ≈ cross term + self term
                       ≈ 2 · |A_ref| · |E_sca| · cos(Δφ)  +  |E_sca|²
                                ↑                              ↑
                          强参考场下主导                    强参考场下被淹没

[阶段 2] strong-reference 极限：peak ≈ |A_ref| · √Csca （NOT |A_ref| · Csca）

[阶段 3] detection proxy ≈ f( peak margin z, transit / τ, phase flip, threshold, route gate )
       —— 不是 peak 的单调函数，更不是 Csca 的单调函数
```

#### 三条 "不保证" 警告

```text
警告 1: Csca↑  不保证  detection proxy↑
   反例: §6.4 表 6.4.D Au panel 20→60 nm Csca 跨 1200×，detection proxy 只 0% → 31.5%

警告 2: peak↑  不保证  detection proxy↑
   反例: §2.4 表 404 vs 660 nm peak ≈ 2×，detection proxy ≈ 0.4×
   原因: transit↓、phase flip↑、margin↓ 抵消 peak↑

警告 3: reference↑  不保证  SNR_amplitude↑ → detection↑
   reference 放大相干一次项确实让 signal 端上升、noise 端不变，amplitude SNR ↑；
   但 detection 还要看：阈值（随 noise 同步上抬）、有效锁相样本数、phase flip、route gating；
   且 reference 太弱时（如 660/700×1500 weak-ref control）虽然 selected-annulus uplift 看似高，
   但被 P0 audit / R5.2 sidecar 锁为 weak_reference_control_only，不是 route 物理优势。
```

#### 倍数表的正确读法

```text
- 只有以下阶段量可以写成"× 倍数"：Csca×、|E_sca|×、|A_ref|×、cross-term×、self-term×、peak×、noise×。
- 这些倍数都对应明确的 baseline（通常是 660 nm 同 W×H 同 panel）。
- transit 用 ms（绝对值），不用倍数。
- detection 用 % synthetic detection score / proxy（绝对百分比），不用倍数。
- 把上述阶段量倍数链相乘 ≠ detection 总倍数。例如 Csca× 7.10 × |A_ref|× ~1.0 ≠ detection× 7.10。
- 后面 §6.4.F、§7.x 的所有"× 列"都按这条约定读。
```

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
| 通道宽度 W | nm | 500 / 600 / 700 / **800 (main)** / 900 / 1000–1500 | 阶段 4 参考场、阶段 3 路径相位 | 窄通道 detection / route score 数字高（**Csca 不由通道宽度决定，是颗粒固有量**），但工程风险也高（§10.4 width-prior）|
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

> **阶段类型说明**（降低读者阶段名负担）：本表中 **audit** = 对已有数据再聚合 / 再分类，不跑新计算；**design / preflight / gate** = 设计文档 / 授权合同，不执行；**trace** = 实际跑了少量 case 产生新数字（但严格 bounded）；**synthesis** = 综合多 trace 的裁决。**全 P0–P18 内不存在"新跑全量随机事件"或"产生新 measured artifact"的阶段**。

| 阶段 | 类型 | 是否产生新 simulation | 关键数字 |
|---|---|---|---|
| P0 | mandatory **audit**（aggregate / classify）| ❌ 否（只对已有 v1 / v2 数据再聚合） | 572 个路线聚合审计行；563 surrogate-sensitive_not_promoted；2 main candidates；1 weak control；1 optional probe；1 shortwave probe |
| P1 | physical-ceiling diagnostic **contracts** | ❌ 否（只写诊断合同，不跑 solver） | 4 条合同（full-wave、vector/Jones、roughness、transport）；surrogate-risk reduction only |
| P2 | bounded physical-solver **readiness** | ❌ 否（route universe + verifier，solver execution blocked） | route universe + source binding + schema manifest + verifier |
| P3 | minimal pilot **design** | ❌ 否（只 design） | 选 P4 / P6 后续使用的 3 条路线子集 |
| P4 | dry-run **preflight** | ❌ 否（preflight，无 mesh） | mesh 标记 `not_generated_no_mesh_generation` |
| P5 | authorization **gate** | ❌ 否（gate，默认阻塞） | 默认 `not_authorized_pending_explicit_later_phase_execution_request` |
| P6 | bounded **trace** 1（minimal bounded Green kernel） | ✅ 是（少量 bounded case） | 顺序：800 × 1400 > 800 × 1500 > 404 probe |
| P8 | bounded **trace** 2（phase-gradient） | ✅ 是 | 同上顺序 |
| P10 | bounded **trace** 3（curvature-balance） | ✅ 是 | 800 × 1500 > 800 × 1400 > 404 probe（main-660 首位反转） |
| P12 | bounded **trace** 4（resonance-compactness） | ✅ 是 | 同 P10 |
| P14 | bounded **trace** 5（phase-curvature residual） | ✅ 是 | 800 × 1400 > 800 × 1500 > 404 probe（再反转） |
| P16 | bounded **trace** 6（phase-curvature residual） | ✅ 是 | 800 × 1500 > 800 × 1400 > 404 probe |
| P17 | 第七 lane 授权 **design** | ❌ 否 | 记录 P12→P14 与 P14→P16 都出现 rank delta [−1, +1, 0] |
| P18 | **synthesis** stop / continue | ❌ 否（综合裁决） | `bounded_lanes_sufficient_for_route_promotion = false`；停止机械式 lane 滚动；要求 P19 evidence-strategy gate |

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

#### 6.2.2 Au plasmonic（在当前 Au panel + Mie 输入下：660 nm Csca 最大）

> **重要免责声明**：教科书常说"Au 等离激元共振约在 520 nm"，所以读者会预期 532 nm 附近 Csca 最大。但本表给出的"660 nm Csca 最大"是 **当前 simulator Au panel（20 / 30 / 40 / 60 nm）+ 当前 Mie 输入折射率 + 4 几何 mean 聚合 (800 × 500 / 600, 1200 × 500 / 600)** 下的有效结果，**不是**泛化的"金纳米粒子在 660 nm 共振"口号。共振峰位置随颗粒尺寸 / 形状 / 介质有偏移，本数据只对应当前粒径段。

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

> **术语统一**（v5.0 二次精修）：本节所有标 `detection (%)` / `mean stable detection (%)` 的列**都不是事件概率**（不是 §13 第 6 档校准 / 实测值）。它们是合成相对先验代理量（synthetic detection proxy 或 relative-prior detection score），按各自 lens 的分母与聚合方式生成。读到 12.52% 不要默认理解为"100 个 EV 实物有 12.52 个被测到"，应理解为"在合成相对先验模型 + 该 lens 分母下的 detection-equivalent 比例"。详见 §4 / §13。

#### 表 6.4.A — 口径 A 主排序：EV biomimetic + all-crossing 8-scenario avg（synthetic detection score, %）

| 几何 (λ / W × H, nm) | events 来源 | synthetic detection score (%) | 路线最终角色（P0 audit） | 来源 |
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

> **一句话 takeaway（表 6.4.A）**：所有 660 nm 路线（main / weak-ref control / context / optional probe）的 detection score 都明显高于 404 nm 路线；其中**窄通道 660 / 500 × 1500 nm score 最高 (19.64%)**，但被治理裁决标为 surrogate_sensitive_not_promoted；main-660 选 800 × 1400 / 1500 是**治理意义上的稳定基准**（不是数字最高），见 §10.4 width-prior 解释。

#### 表 6.4.B — NODI engineering lens **synthetic stable detection score**（NODI engineering gate 通过的 17 strict-pass case 子集平均；与表 6.4.A 不同 lens、不可直接比较）

| 几何 | lens 1: NODI engineering proxy (%) | lens 2: 2020 paper-条件 proxy (%) | lens 3: 2022 NODI paper-条件 proxy (%) |
|---|---:|---:|---:|
| 404 / 500 × 800 | 33.65 | 34.50 | 35.40 |
| 660 / 800 × 550 | 47.15 | 43.50 | 46.70 |
| 660 / 800 × 1400 | 45.15 | 41.00 | 42.90 |
| 660 / 900 × 1200 | 42.60 | 44.20 | 47.05 |

> **一句话 takeaway（表 6.4.B）**：在 NODI engineering / 2020 paper / 2022 NODI paper 三个 lens 下，660 nm 几何普遍在 41–47% 量级，404 nm 几何在 33–35%；同 lens 内不同 660 nm 几何之间差异约 3–6 pp（§7.4 同 lens 差异）；不同 lens 之间差异约 4 pp（同行）。**没有单一几何在所有 lens 下都是最高**——例如 660 / 900 × 1200 在 2022 NODI paper lens 下 47.05% 略高于 660 / 800 × 550 的 46.70%（详见 §14.6 修正结论）。

#### 表 6.4.C — Au paper-audit selected-annulus lens（跨 4 几何 mean: 800×500/600 + 1200×500/600；synthetic detection proxy）

| λ (nm) | mean stable detection proxy (%) | mean pulse peak (相对) | pass 比例（strict NODI gate）|
|---:|---:|---:|---:|
| 488 | 5.95 | 0.0525 | 0.00 |
| 532 | 8.51 | 0.0773 | 0.00 |
| 660 | 17.74 | 0.1564 | 0.45 |

> **一句话 takeaway（表 6.4.C）**：Au panel 在 selected-annulus lens 下 660 > 532 > 488，与 §6.2.2 Csca 方向一致（**注意 Au plasmonic 方向与 EV biomimetic Rayleigh 相反**）；这是 §11.3 step 2 选 660 nm 为口径 B 主对照波长的直接数据根据。

#### 表 6.4.D — Au paper-audit selected-annulus lens, 粒径阶梯（660 / 800 × 500 nm，近 Tsuyama 2020 counting POD 条件 Au gold 对照；synthetic detection proxy）

| Au 粒径 (nm) | mean detection proxy (%) | mean stable detection proxy (%) | mean pulse peak (相对) |
|---:|---:|---:|---:|
| 20 | 0.00 | 0.00 | 0.000 |
| 30 | 14.6 | 14.0 | 0.044 |
| 40 | 26.6 | 26.5 | 0.110 |
| 50 | 30.5 | 30.0 | 0.232 |
| 60 | 31.5 | 30.8 | 0.447 |

> **一句话 takeaway（表 6.4.D）**：Au panel 20→60 nm 时 Csca 跨 1200×（§6.2.2），但 detection 只从 0% 升到 31.5%；说明**detection 不跟 Csca 同步放大**——Au20 在阈值之下、Au40+ 已在 detection 上限附近饱和。这是 §8 噪声归因 + §2.4 peak vs detection 解耦的最强直接证据。

#### 表 6.4.E — 660 nm 读出方式对照（60 cases，NODI 2024 readout mode calibration lane；synthetic detection proxy，**不是**已校准事件概率）

| 读出方式 | strict gate 通过比例 | mean detection proxy (%) | mean stable detection proxy (%) |
|---|---:|---:|---:|
| in-phase + phase-gated (基线) | 0.00 | 18.28 | 17.89 |
| in-phase no gate | 0.45 | 18.28 | 17.89 |
| magnitude（脉冲幅值）| 0.45 | 18.15 | 17.74 |

读法：strict gate 通过比例从 0 跳到 0.45 是边界判据切换，**不是** detection 本身改变。mean detection 几乎不变。

> **一句话 takeaway（表 6.4.E）**：读出方式（in-phase / magnitude / 是否加 phase-gate）对 mean detection proxy 几乎无影响（17.74–17.89%），但对 strict gate pass / fail 判据有决定性影响；这是 §9 排名 8 "读出方式：在 pass / fail 边界上影响巨大但 mean detection 几乎不变" 的直接证据。

#### 表 6.4.F — 4 波长信号链分解汇总（同一 W × H = 800 × 1400 nm，EV biomimetic + 同一颗粒 panel；synthesis of §2.4 + §7.2.5a.1）

> **derived reader table**：本表把 §2.4 4 波长机制链与 §7.2.5a.1 信号链扩列汇成一张紧凑的物理量级表，专门给 §0.3b / §3.0a / §10.6 / §13.2 / §18.4 引用 `§6.4.F` 时直接定位。**baseline = 660 nm 同 W × H 同颗粒 panel**；倍数列只用于阶段量；transit 用 ms 绝对值。

| λ (nm) | Csca× | \|E_sca\|× | \|A_ref\|× | cross-term× | self-term× | peak× | noise× | transit (ms) | EV synthetic detection score (%) — strict controlled? |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 404 | 7.10 | 2.66 | ≈ 0.95 | ≈ 2.5 | 7.10 | ≈ 2.0 | 1.0 | 5.48 | — at this exact cell (route-level shortwave probe class avg ≈ 4.45%；非 strict λ-only) |
| 488 | 3.34 | 1.83 | ≈ 1.00 | ≈ 1.83 | 3.34 | ≈ 1.4–1.6 | 1.0 | 6.61 | — at this exact cell (mid-wave class avg ≈ 7.77%，混合几何) |
| 532 | 2.37 | 1.54 | ≈ 1.00 | ≈ 1.54 | 2.37 | ≈ 1.2–1.4 | 1.0 | 7.21 | — at this exact cell (同上 mid-wave class avg) |
| **660** (baseline) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 8.94 | **12.52** (§6.4 表 6.4.A 直接行 `main_660_W800_D1400`) |

> **表 6.4.F 严格性声明（重要）**：阶段量倍数列 (Csca× / |E_sca|× / |A_ref|× / cross-term× / self-term× / peak× / noise× / transit) 在固定 W × H + 颗粒 panel 下是 **strict controlled comparison**（§7.0 第 1 条）；但 detection 列**不是** strict λ-only，是 route-level available evidence —— v5.x 报告**没有**在 W × H = 800 × 1400 nm 这一具体几何下针对 404 / 488 / 532 各跑 EV biomimetic 全 panel detection；最近邻是 route-class 聚合（404 / 600 × 1300 shortwave probe 4.45%；488 / 532 mid-wave class avg 7.77%；这两个 class avg **本身**已混合几何）。所以 detection 列不能解读为"在 800 × 1400 nm 几何上 404 nm detection 是 X%"。
>
> 若要看真正"固定 W × H + 严格 vary λ + 同颗粒 panel"的 detection 行，v5.x 报告**仅在 660 nm 这一行有直接覆盖**；其他波长行需要 P19 evidence-strategy gate 之后实测补齐（§16.2 优先级 1）。

> **一句话 takeaway（表 6.4.F）**：阶段量层级（Csca / E_sca / A_ref / cross-term / self-term / peak）从 404 → 660 是单调递减；transit 从 404 → 660 是单调递增。两条链方向相反 + detection 列只在 660 nm cell 有 strict 直接行 —— 这就是为什么 §10.2 / §10.6 不能仅凭 "404 nm peak 大约 2× 660 nm" 推 "404 nm 应该是 main route"；route-level evidence + 治理裁决（§10.4 width-prior + §10.6 多候选裁决 5 条）共同决定 main 在 660 nm。

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

### 7.0 如何读 controlled comparison（变量固定法 5 条）

读者最容易问"你到底是不是固定变量后比较的？"。本节明确 §7 的 5 种比较方式 + 各自约束：

| 比较方式 | 固定的 | 变化的 | §7 对应位置 | 必须遵守的约束 |
|---|---|---|---|---|
| 1. 看波长影响 | particle panel + W + H + lens / route | λ | §7.1.x、§2.4 表、§7.2.5a.1 | 同一 panel + 同一 lens；不要混 EV biomimetic vs Au paper-audit |
| 2. 看尺寸影响 | particle panel + λ + lens / route | W 和 / 或 H | §7.2.x、§7.2.5a.2 | 同一 panel + 同一 lens；**Csca 不变**（颗粒固有量），变化的是 \|A_ref\| / 路径相位 / route gating |
| 3. 看材料影响 | λ + W + H | 颗粒 panel（EV biomimetic vs Au）| §6.4.B vs §6.4.C 对照、§9 排名 1 | **不能直接把不同 panel 的 detection 百分比当同一 ranking**（§4.5 / §9 排名 1 修正）；只能定性看方向（Csca 反转、route 选择不同） |
| 4. 看 lens 影响 | route candidate（同 λ + W + H + 颗粒）| lens（all-crossing / NODI engineering / 2020 paper / 2022 NODI paper / selected-annulus）| §7.4 三 lens 对照表 | 仅作口径诊断，不作交叉排名；同一几何在不同 lens 下差异 lens 切换 > 几何切换 > 波长切换（§9 排名 2）|
| 5. 看 Tsuyama calibration 影响 | candidate geometry + 颗粒 + lens | calibration parameter set（γ / s_SNR / e_SNR / 选定算子）| §11.2 step 1 校准 → §11.3 step 2 选型 | **先冻结 calibration，再在同一口径里选 residual 最低**——不是反过来"先挑几何再校准"；§11.4 关键澄清 |

**一句话原则**：**任何"X 影响 Y"的结论都要回到这 5 种比较方式之一；混种比较法（如 §9 排名 1 用 Au selected-annulus mean 与 EV NODI engineering lens 比的 v5.0 初稿错误）要明确标"定性影响判断"，不用具体百分比 ranking**。



公共约定（全 §7 适用）：

```text
- transit 列用 ms（按 §6.1 物理推导；只依赖 λ）
- detection 列用 % synthetic detection score / proxy（按 v4.2 / v5.0 已发布数字单位换算；§4 / §13 解释）
- 每张表显式标 lens 分母 + 颗粒口径
- "—" = v4.2 / v5.0 未直接覆盖该 cell；禁止读为 0%
```

### §7 数据覆盖矩阵（先看哪些 cell 是真比较，哪些是 gap map）

**这是 §7 全节最重要的一张图**。读者打开任何一张 §7.x 表前，应该先看这里：v5.0 报告**没有按"波长 × W × H × 颗粒"做完全交叉扫描**，而是以 660 nm 为主路线 + 404 nm 为短波探针 + 800 × 550 / 1200 × 550 / 800 × 1400 / 800 × 1500 / 500 × 800 / 500 × 1200–1500 / 600 × 1500 / 700 × 1500 / 900 × 1200 / 900 × 1400 / 800 × 500 / 800 × 600 / 1200 × 500 / 1200 × 600 几何为单点对照。所以下面表里大量 "—" 是**数据覆盖 gap，不是 0% detection**。

EV biomimetic 颗粒，按几何聚类的覆盖矩阵：

| (W × H) ↓ \\ λ → | 404 nm | 488 nm | 532 nm | 660 nm |
|---|:-:|:-:|:-:|:-:|
| 500 × 800 | ✅ NODI lens | — | — | — |
| 500 × 1200 | — | — | — | ✅ all-cross |
| 500 × 1300 | — | — | — | ✅ all-cross |
| 500 × 1400 | — | — | — | ✅ all-cross |
| 500 × 1500 | — | — | — | ✅ all-cross |
| 600 × 1300 | ✅ all-cross 类 | — | — | — |
| 600 × 1500 | — | — | — | ✅ all-cross |
| 700 × 1500 | — | — | — | ✅ all-cross |
| **800 × 550** | — | — | — | ✅ NODI / 2020 / 2022 lens |
| **800 × 1400** | — | — | — | ✅ all-cross + NODI / 2020 / 2022 lens |
| **800 × 1500** | — | — | — | ✅ all-cross |
| 900 × 1200 | — | — | — | ✅ NODI / 2020 / 2022 lens |
| 900 × 1400 | — | — | — | ✅ all-cross |

Au paper-audit 颗粒（Au panel 20–60 nm + Ag 40 / 60 nm），按几何聚类的覆盖矩阵：

| (W × H) ↓ \\ λ → | 488 nm | 532 nm | 660 nm |
|---|:-:|:-:|:-:|
| **800 × 500** | ⚠️ 在 §7.1.5 的 4 几何 mean 内 | ⚠️ 同上 | ✅ §6.4 表 6.4.D 直接行（Au 粒径阶梯）|
| **800 × 600** | ⚠️ 同上 | ⚠️ 同上 | ⚠️ 在 mean 内 |
| **1200 × 500** | ⚠️ 同上 | ⚠️ 同上 | ⚠️ 在 mean 内 |
| **1200 × 600** | ⚠️ 同上 | ⚠️ 同上 | ⚠️ 在 mean 内 |
| **800 × 550** | — | ✅ raw exponent 直接行（§7.3.1）| ✅ raw exponent 直接行（§7.3.1）|
| **1200 × 550** | — | — | ✅ raw exponent 直接行（§7.3.1，全 6 case 最低 residual）|

读法：

```text
✅ = v4.2 / v5.0 有直接数据
⚠️ = 该 cell 数据被聚合进 4 几何 mean (§6.4 表 6.4.C)，不能直接拆出单 cell 值
—  = v4.2 / v5.0 未覆盖；禁止读为 0%

§7.1 / §7.2 / §7.3 各表里出现 "—" 的 cell 都对应这两个矩阵里的 "—"。
要补这些 cell 必须新跑 case，不在 v5.0 范围内。
```

**这就是为什么 §7 的多张表里大量为 "—"**：v5.0 报告本身就是单点对照而非全扫描。读者不应该把空 cell 解读成"那里 detection 为 0"，而是"那里 v5.0 没数据，需要 P19 evidence-strategy gate 之后的实测才能补齐"。

### 7.1 固定几何，看波长（5 张表）

#### 7.1.1 W × H = 800 × 1400 nm 固定，vary λ（口径 A main 第一几何）；颗粒 EV biomimetic；lens = NODI engineering stable detection proxy

| λ (nm) | transit (ms) | EV Csca× (相对 660) | synthetic detection score (%) | 数据来源 |
|---:|---:|---:|---:|---|
| 404 | 5.48 | 7.10 | — | v4.2 未直接覆盖（最近邻 404 / 500 × 800 = 33.65%）|
| 488 | 6.61 | 3.34 | — | v4.2 未直接覆盖 |
| 532 | 7.21 | 2.37 | — | v4.2 未直接覆盖 |
| 660 | 8.94 | 1.00 | **45.15** | §6.4 表 B 直接行 |

#### 7.1.2 W × H = 800 × 550 nm 固定，vary λ（Tsuyama 论文 depth）；颗粒 EV biomimetic；lens = NODI engineering stable detection proxy

| λ (nm) | transit (ms) | EV Csca× | synthetic detection score (%) | 数据来源 |
|---:|---:|---:|---:|---|
| 404 | 5.48 | 7.10 | — | 未覆盖 |
| 488 | 6.61 | 3.34 | — | 未覆盖 |
| 532 | 7.21 | 2.37 | — | 未覆盖 |
| 660 | 8.94 | 1.00 | **47.15** | §6.4 表 B 直接行 |

#### 7.1.3 W × H = 500 × 800 nm 固定，vary λ（404 nm 短波 lens 几何）；颗粒 EV biomimetic；lens = NODI engineering stable detection proxy

| λ (nm) | transit (ms) | EV Csca× | synthetic detection score (%) | 数据来源 |
|---:|---:|---:|---:|---|
| **404** | 5.48 | 7.10 | **33.65** | §6.4 表 B 直接行 |
| 488 | 6.61 | 3.34 | — | 未覆盖 |
| 532 | 7.21 | 2.37 | — | 未覆盖 |
| 660 | 8.94 | 1.00 | — | 未覆盖（最近邻 800 × 550 = 47.15%）|

#### 7.1.4 W × H = 800 × 500 nm 固定，vary λ（Au paper-audit 主对照 + counting POD 论文几何）；颗粒 Au panel 20–60 nm；lens = selected-annulus proxy

| λ (nm) | transit (ms) | Au Csca× | Au20 detection proxy (%) | Au30 detection proxy (%) | Au40 detection proxy (%) | Au50 detection proxy (%) | Au60 detection proxy (%) | 数据来源 |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 488 | 6.61 | 0.43 | — | — | — | — | — | 未在此 cell 直接覆盖 |
| 532 | 7.21 | 0.59 | — | — | — | — | — | 未在此 cell 直接覆盖 |
| **660** | 8.94 | 1.00 | **0.0** | **14.6** | **26.6** | **30.5** | **31.5** | §6.4 表 D 直接行 |

#### 7.1.5 W × H = 跨 4 几何 mean（800 × 500/600 + 1200 × 500/600），vary λ；颗粒 Au panel mean；lens = selected-annulus proxy

| λ (nm) | transit (ms) | Au Csca (m²) | selected-annulus mean stable detection proxy (%) | mean pulse peak (相对) | 数据来源 |
|---:|---:|---:|---:|---:|---|
| 488 | 6.61 | 2.86 × 10⁻¹⁶ | 5.95 | 0.0525 | §6.4 表 C |
| 532 | 7.21 | 3.93 × 10⁻¹⁶ | 8.51 | 0.0773 | §6.4 表 C |
| 660 | 8.94 | 6.66 × 10⁻¹⁶ | 17.74 | 0.1564 | §6.4 表 C |

### 7.2 固定波长，看几何（5 张表）

#### 7.2.1 λ = 660 nm + H = 1500 nm；颗粒 EV biomimetic；lens = all-crossing 8-scenario avg

| W (nm) | transit (ms) | synthetic detection score (%) | 路线最终角色 |
|---:|---:|---:|---|
| 500 | 8.94 | 19.64 | context, surrogate_sensitive_not_promoted |
| 600 | 8.94 | 16.55 | context, surrogate_sensitive_not_promoted |
| 700 | 8.94 | 15.23 | weak_reference_control_only |
| **800 (main)** | 8.94 | **12.70** | **conditional_relative_main** |
| 900 | 8.94 | — | 未在 H=1500 直接覆盖（最近邻 900 × 1400 = 12.30%）|

#### 7.2.2 λ = 660 nm + H = 1400 nm；颗粒 EV biomimetic；lens = all-crossing 8-scenario avg

| W (nm) | transit (ms) | synthetic detection score (%) | 路线最终角色 |
|---:|---:|---:|---|
| 500 | 8.94 | 18.97 | context, surrogate_sensitive_not_promoted |
| 600 | 8.94 | — | 未覆盖 |
| 700 | 8.94 | — | 未覆盖 |
| **800 (main)** | 8.94 | **12.52** | **conditional_relative_main** |
| 900 | 8.94 | 12.30 | optional_robustness_probe_only |

#### 7.2.3 λ = 660 nm + W = 500 nm，看 H 阶梯；lens = all-crossing 8-scenario avg

| H (nm) | transit (ms) | synthetic detection score (%) | ratio vs main 660 | 路线最终角色 |
|---:|---:|---:|---:|---|
| 1200 | 8.94 | 17.39 | 1.379× | context, surrogate_sensitive_not_promoted |
| 1300 | 8.94 | 18.26 | 1.448× | context, surrogate_sensitive_not_promoted |
| 1400 | 8.94 | 18.97 | 1.504× | context, surrogate_sensitive_not_promoted |
| 1500 | 8.94 | 19.64 | 1.557× | context, surrogate_sensitive_not_promoted |

读法：W=500 在 H=1200→1500 内 detection 单调上升，但 4 行均被治理裁决降级为 `surrogate_sensitive_not_promoted`——这是 §10.4 width-prior + P0 audit 的典型例子。

#### 7.2.4 λ = 660 nm + W = 800 nm，看 H 阶梯；多 lens 同时排（仅 v4.2 已直接覆盖行）

| H (nm) | transit (ms) | NODI engineering stable detection proxy (%) | 2020 paper lens (%) | 2022 NODI paper lens (%) | all-crossing 8-scen avg (%) | 几何角色 |
|---:|---:|---:|---:|---:|---:|---|
| 550 | 8.94 | 47.15 | 43.50 | 46.70 | — | Tsuyama 论文 depth（cross-check）|
| 1400 (**main**) | 8.94 | **45.15** | 41.00 | 42.90 | **12.52** | **conditional_relative_main** |
| 1500 (**main**) | 8.94 | — | — | — | **12.70** | **conditional_relative_main** |

#### 7.2.5 λ = 660 nm + W = 900 nm，看 H；多 lens 同时排

| H (nm) | transit (ms) | NODI engineering stable detection proxy (%) | all-crossing 8-scen avg (%) | 几何角色 |
|---:|---:|---:|---:|---|
| 1200 | 8.94 | **42.60** | — | NODI lens 直接行 |
| 1400 | 8.94 | — | **12.30** | optional_robustness_probe_only |
| 1500 | 8.94 | — | — | 未覆盖 |

### 7.2.5a 信号链扩列对比（4 波长信号链分解，固定 W × H）

> codex 反馈：用户最想看的是 "Csca× / |E_sca|× / |A_ref|× / cross-term× / peak× / noise× / margin / transit / detection" 一行同时展示。本节给两张代表性扩列表（一张固定几何看波长 + 一张固定波长看几何），让读者把 §6 阶段量与 §7 隔离对比合在一张表里读。

#### 7.2.5a.1 固定 W × H = 800 × 1400 nm（口径 A main 第一几何），4 波长信号链分解（EV biomimetic + 同 panel；baseline 660 nm）

| λ (nm) | Csca× | \|E_sca\|× | \|A_ref\|× | cross-term× | peak× | noise× | transit (ms) | EV synthetic detection score (%) | 主要 blocker（§8.5）|
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 404 | 7.10 | 2.66 | ≈ 0.95 | ≈ 2.5 | ≈ 2.0 | 1.0 | 5.48 | — (此 cell 无直接行；最近邻 404 / 600 × 1300 = 4.45%) | transit / gating mismatch + phase flip |
| 488 | 3.34 | 1.83 | ≈ 1.00 | ≈ 1.83 | ≈ 1.4–1.6 | 1.0 | 6.61 | — (此 cell 无直接行；mid-wave class avg 7.77%) | transit↓ 较弱、margin 中等 |
| 532 | 2.37 | 1.54 | ≈ 1.00 | ≈ 1.54 | ≈ 1.2–1.4 | 1.0 | 7.21 | — (同上) | margin 接近 main |
| **660** (baseline) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 8.94 | **12.52** (§6.4 表 6.4.A 直接行) | — (main route, no blocker) |

> **takeaway（表 7.2.5a.1）**：在 W × H = 800 × 1400 nm 同一几何下，404 nm 的阶段量在 Csca / |E_sca| / cross-term / peak 全部超过 660 nm（peak 约 2×），但 EV biomimetic 的 detection proxy 在 660 nm 这一行**才有直接数据**——其他波长的数据 gap 限制了直接比较，需要 P19 evidence-strategy gate 后实测补齐（§16.2 优先级 1）。从趋势看（§6.4.A mid-wave class avg 7.77% vs shortwave probe class 4.45% vs main-660 12.61%），这条几何上短波长 detection 仍**低于** 660 nm。

#### 7.2.5a.2 固定 λ = 660 nm（main 波长）、固定 H = 1500 nm，看 W 阶梯：信号链分解

注意：**固定 λ + 固定颗粒 panel 时，Csca 不变**（颗粒固有量；§3.0a 阶段量是谁、归谁管）。下表 Csca 列因此是绝对值、不再是倍数；变化的是 |A_ref| / cross-term / route gating。

| W × H (nm) | Csca (绝对，EV biomimetic 60 nm 等代表 panel) | \|E_sca\|× | \|A_ref\|× | cross-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | route role | 主要 blocker（§8.5） |
|---|:-:|:-:|:-:|:-:|:-:|:-:|---:|---:|---|---|
| 500 × 1500 | 同（颗粒固有）| 1.0 | 偏离 baseline（窄通道 \|A_ref\| 谱形改变）| ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 19.64 | context, surrogate_sensitive_not_promoted | geometry outside preferred + route governance downgrade |
| 600 × 1500 | 同 | 1.0 | 接近 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 16.55 | context, surrogate_sensitive_not_promoted | 同上 |
| 700 × 1500 | 同 | 1.0 | 偏低（reference too weak）| < 1.0 | < 1.0 | 1.0 | 8.94 | 15.23 | weak_reference_control_only | reference too weak |
| **800 × 1500 (main)** | 同 | 1.0 | **1.0 baseline** | **1.0 baseline** | **1.0 baseline** | 1.0 | 8.94 | **12.70** | **conditional_relative_main** | — (main, no blocker) |
| 900 × 1400（同 H 行无直接覆盖；用 1400 行）| 同 | 1.0 | 接近 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 12.30 | optional_robustness_probe_only | — (probe, no main blocker) |

> **takeaway（表 7.2.5a.2）**：**固定 λ + 固定颗粒 panel 时，Csca 是常数**——所以"窄通道 detection 高"的现象与 Csca 无关，是 |A_ref| / 路径相位 / route gating / width-prior 风险先验的综合结果。这条直接对应 codex 反馈的"通道几何不改变 Csca"原则，也对应 §10.4 width-prior 解释的物理直觉。**windowed detection score 数字最高（19.64%）但 route 治理裁决降级到 surrogate_sensitive_not_promoted**——说明数字不是单一裁决条件，必须看 §10.6 多条件裁决表。

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

| 几何 | NODI engineering lens stable detection proxy (%) | 2020 paper lens proxy (%) | 2022 NODI paper lens proxy (%) | EV all-crossing 8-scen avg synthetic score (%) | lens 间最大差 |
|---|---:|---:|---:|---:|---:|
| 660 / 800 × 1400 | 45.15 | 41.00 | 42.90 | 12.52 | 32.6 pp |
| 660 / 800 × 550 | 47.15 | 43.50 | 46.70 | — | 3.6 pp |
| 660 / 900 × 1200 | 42.60 | 44.20 | 47.05 | — | 4.5 pp |
| 404 / 500 × 800 | 33.65 | 34.50 | 35.40 | — | 1.7 pp |

读法：**仅在 660 nm 几个相近几何之间（800×1400 vs 800×550 vs 900×1200），同 lens 内差异约 3–6 pp**；但只要拉到 404 vs 660 这一对波长（同 lens、不同几何），差异就能到 ≈ 13 pp（NODI engineering lens 33.65% vs 47.15%，§6.4 表 6.4.B）；EV all-crossing 8-scen avg 在不同路线之间的差异更可超过 15 pp（§6.4 表 6.4.A 中 main-660 12.52% vs 500×1500 context 19.64%）。所以同 lens 内"波长 / 几何切换差异"的实际范围是 3–15 pp，不是单一小数字。

但**真正大的 lens 间差异**仍达 32.6 pp（如 660 / 800 × 1400 NODI engineering 45.15% vs all-crossing 8-scen 12.52%）——这才是 §4.5 禁止跨 lens 直接比较的实证根据：lens 切换的影响**始终**大于同 lens 内的几何 / 波长切换。

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
| 660 / 700 × 1500 weak-ref | 偏低（\|E_ref\| 弱）| 0.012 | 中 | 15.23（同 lens 下高于 main 12.52）| 数字来自 **all-crossing 8-scenario avg 路线类**（同 main 同分母），不是 selected-annulus；但口径 A R5.2 sidecar 把这条路线锁为 `weak_reference_control_only` —— "weak ref 跨 8 / 8 情景持续高于 main" 不被读为路线物理优势，而是参考场偏低导致路线治理裁决（见 §10.5 / §12.2）|

### 8.5 blocker 分类表（"为什么检测不到"——不是黑箱失败）

读者最常问："detection 为什么这么低？是噪声大、还是阈值高、还是路线被压？"。下表把 v5.0 在已有 audit / sidecar / route classification 中出现过的所有 blocker 类型分类，让读者看到 detection 低不是单一黑箱失败，而是多条不同物理 / 治理通道：

| blocker 类型 | 物理含义 | 通常出现在哪些 λ / geometry | 对 detection 的影响方向 | 读者应该如何理解 |
|---|---|---|---|---|
| reference too weak | \|A_ref\| 偏低，强参考场极限失效，cross term 减弱、self term 占比上升 | 660 / 700 × 1500（weak-reference control）；窄通道 W ≤ 600 部分情况 | selected-annulus uplift 看似高，但 absolute peak 偏低；治理裁决 weak_reference_control_only | "selected-annulus uplift 高"≠"路线物理优势"；分子分母同步缩小是另一种解释 |
| noise too high / margin too low | pre-readout / post-readout noise → MAD ↑ → threshold ↑；peak 高度不一定不够，但 margin z 不稳定 | 短波长 + 短 transit；少有效锁相样本数情况 | margin z 偏小 → detection ↓ | 不是"peak 不够大"，是"margin 不稳定"；§8.6 数值版 |
| peak below threshold | peak 高度本身低于 threshold = median + threshold_sigma · 1.4826 · MAD | Au20 (660 / 800 × 500)；EV biomimetic 在某些短波 + 窄通道 | detection = 0% 或近 0% | 不是 noise 问题，是颗粒散射太弱；增大颗粒 / 改材料才能解 |
| unstable route（rank instability across bounded lanes）| P6–P16 trace 6 条 lane 之间排名反复切换 | main_660_W800_D1400 vs main_660_W800_D1500 在 trace 间互换首位 | 不能从 trace-only lane 挑单一冠军 | 治理上保留为 conditional_relative_main 集合；不是路线本身有问题 |
| transit / gating mismatch | transit 太短（短波长 + 高 NA）→ 有效锁相样本数不够 | 404 nm 系列；窄 beam waist 路径 | margin z ↓ + Wilson LB 收紧 | peak 翻倍但 transit 0.61× → detection 反而 ↓ |
| geometry outside preferred operating region | 通道 W / H 越过 width-prior `(W/800)^1.5` / `^2` 的可接受范围 | 窄通道 W = 500–600 + 深通道 H ≥ 1300 | route score 看似高，但被 width-prior + R5.2 sidecar 降级 | "数字最高"≠"治理推荐"；§10.4 详解 |
| route governance downgrade | P0 audit 把 route 分为 conditional_main / weak control / optional probe / shortwave probe / surrogate_sensitive_not_promoted | 563 / 572 路线（绝大多数 v1 高分上下文）| 不允许 route promotion | 不是单 case 失败，是审计层面拒绝晋升 |
| weak_reference_control_only | 同"reference too weak" 的治理裁决标签 | 660 / 700 × 1500 | 仅作为对照，不替代 main-660 | §10.5 / §12.2 |
| paper-likeness / lens mismatch | 在某 lens 下 detection 看似高，但其他 lens 不一致或不在 paper anchor 集合 | 例如 660 / 900 × 1200 在 2022 NODI paper lens 47.05% 但 NODI engineering lens 42.60% | 单 lens 高分不能替代 cross-lens 一致性 | §7.4 / §14.6 |
| classification accuracy 不可复现 | 本地 sklearn 不可用 | Tsuyama 2022 NODI classification 71.9 ± 4.0% | `no_accuracy_claim` | 不是 detection blocker，但是 release-positive 的额外 forbidden 边界 |

**一句话 takeaway（表 8.5）**：detection 低**从来不是单一黑箱失败**——v5.0 内每条低 detection / 未晋升路线都能映射到上面 10 类 blocker 之一（或多条叠加）。所以"为什么检测不到"必须先指明 blocker 类别，再讨论用什么 measured artifact（§16.2）能解锁哪一类。

### 8.6 噪声 sensitivity 数值版（"reference 增强了那么多倍，noise 还重要"）

§8.1–§8.3 已经从概念回答；本节给具体 sensitivity 数字，让读者看到 peak 和 noise 不是简单线性关系：

| 场景 | peak× (相对 660 / 800 × 1400 main) | reference× | noise×（相对 main 基线，pre + post）| peak margin z 估计 | synthetic detection score (%) | 一句话结论 |
|---|---:|---:|---:|---|---:|---|
| 660 / 800 × 1400 main（baseline）| 1.00× | 1.00× | 1.00× | 数 σ 量级 | 12.52 | baseline |
| 404 / 600 × 1300 短波探针 | ≈ 2.0× peak | ≈ 0.93× | ≈ 1.0×（surrogate 内 noise 不随 λ）| margin z ≈ 1.2–1.6×（被 transit↓ 0.61× 与 phase flip↑ 拖累）| 4.45 | peak 翻倍 ≠ detection 翻倍；transit↓ + phase flip↑ 把 margin 拉回 |
| 660 / 700 × 1500 weak-ref | ≈ 0.7–0.9× peak（\|A_ref\| 弱）| ≈ 0.7–0.9× | ≈ 1.0× | margin z 中 | 15.23 | reference↓ → cross term↓ → peak↓；selected-annulus 分子分母同步缩小让 uplift 看似高，但治理上仍 weak_reference_control_only |
| 假想 noise×2（双噪声） | 1.00× | 1.00× | 2.00× | margin z ≈ 0.5×；threshold ≈ 2× | 估计大幅下降，难以稳定通过 strict gate | noise 直接抬阈值与 z 同步，detection 不能靠 reference 救回 |
| 假想 reference×2（参考场翻倍，noise model 不变） | ≈ 2× peak（cross term 翻倍）| 2.00× | 1.00× | margin z ≈ 2× | 估计 detection 中等改善（margin 改善确实让 detection 上升），但仍受 route gate / phase stability / saturation / operating band 约束 | reference↑ → cross term↑ → peak↑；此情景下 noise proxy 不变 → threshold 不随 reference 同步上抬；detection 改善是真实的，但不解锁 release-positive（route governance / paper-likeness / forbidden 边界仍约束）|

读法：

```text
比较行 (404 / 600 × 1300) 与假想 noise×2：
  两者都让 detection ↓，但途径不同——404 是 transit↓ 间接拖累 margin；noise×2 是直接抬阈值。
  所以单看"peak 是否大"或"reference 是否大"都不够，必须看 (peak, noise, transit, gate) 四元组。

比较 weak-ref 行 与假想 reference×2（noise model 不变）：
  reference 的方向性影响：太弱 (cross term↓ → peak↓ → margin z↓)；reference×2 在 noise model 不变下
  确实让 cross term + peak + margin z 同步↑，detection 改善是真实的；但本报告 surrogate baseline 内
  reference 的实际可调范围由 operating band / route governance / width-prior 等共同约束，
  不是单纯"越大越好"。
  这条边界论是 §10.4 width-prior 模型 (W/800)^1.5/^2 之所以"补缺"而不是"打压"的物理直觉支持
  （window-of-acceptance 而非 maximize）。
  注：本节 reference×2 假想**没有**采用 shot-noise-like reference-coupled noise 假设
  （那是另一个独立情景，会让 noise× 同步>1，并改变结论方向；详见 §3.0a 噪声三条不保证警告 第 3 条）。
```

**一句话 takeaway（表 8.6）**：reference 增强 → amplitude SNR ↑，但 detection 还要过 threshold / margin / transit / gate 四关。所以"reference 放大了 N 倍噪声却还重要"的根本答案是：**noise 不是被参考场放大或抑制，它进入的是另一个完全独立的环节（threshold + margin），这条独立路径既不被参考场放大也不被参考场抑制**。

### 8.7 一句话总结噪声归因

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
| 1 | **颗粒材料**（EV biomimetic vs Au plasmonic）| **定性最高**——488 / 532 / 660 上 Csca 方向完全相反（EV Rayleigh 短波↑ vs Au plasmonic 长波↑，§6.2.1 vs §6.2.2）；同时不同材料 panel 在 v4.2 / v5.0 内**没有同 lens 同几何**的可直接比较行（cross-lens 比较违反 §4.5）。所以本排名按"方向反转 + 影响 §10 / §11 选择不同主波长"判最高，而**不**用具体百分比作 cross-panel 加减法 | §6.2.1 / §6.2.2；§7.1（材料 panel 切换）| 最大影响。不分材料的"波长 / 几何 → detection"结论会误导。 |
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

> **口径声明**：本步骤的 660 vs 404 比较**不是**严格 λ-only 隔离对照（v5.0 没有"固定几何 + 仅扫 λ"的全 EV biomimetic 直接行，§7 数据覆盖矩阵已说明这是 gap）。下面引用的是**route-level available evidence**：每条 route 都是某个 (λ, W, H) 组合的整体 detection，不是单变量切片。

- §6.4 表 6.4.B：660 / 800 × 1400 在 NODI engineering lens stable det 45.15%；同 lens 下 404 / 500 × 800 只有 33.65%（**注意几何不同**，所以 13.5 pp 的差既包含 λ 因素也包含几何因素）
- §6.4 表 6.4.A 短波探针类（404 / 600 × 1300）mean 4.45% << main-660 12.61%（**同样跨几何**：4.45 与 12.61 的差既来自 λ 也来自 W/H）
- §5.3 P6–P16 trace：404 probe（404 / 600 × 1300）始终排第 3，从未挑战 main-660（800 × 1400 / 1500）——这是 route 级别一致性证据
- 404 nm 热效应旁路 §15 forbidden 中明令不得加分

合起来：在所有可用 route-level 证据下，660 nm 系列**整体优于** 404 nm 系列；定向上与 §2.4 物理推导（短波 transit↓ + phase flip↑ → detection↓）一致；这条结论不依赖纯 λ 隔离对照。

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

> **白话解释**：width-prior 不是"故意惩罚窄通道让数字下降"，而是"在原模型给窄通道打的分里，加上一个被原模型遗漏的工程风险代价"。如果原模型已经把这些风险算进去了，那加 width-prior 就不会让数字变化；事实是加了之后窄通道分数被合理压下，说明原模型确实漏算了这一块。这是**补缺，不是打压**。

但本报告同时声明：

```text
width-prior (W / 800)^1.5 / ^2 是可接受解释模型，
不是真实物理定律（§13 第 5 档：可接受解释先验）；
推到 (W / 900)^2 会过度打压主路线，越过"补缺"边界进入"打压"。
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

| 几何 (660 nm) | all-crossing synthetic detection score (%) | P0 audit 最终角色 | 主要理由 |
|---|---:|---|---|
| 800 × 1400 | 12.52 | **conditional_relative_main** | §5.3 post-v2 近壁细网格通过 1.0 + §5.3 P6 / P8 / P14 trace 首位 |
| 800 × 1500 | 12.70 | **conditional_relative_main** | §5.3 post-v2 近壁细网格通过 1.0 + §5.3 P10 / P12 / P16 trace 首位 |
| 700 × 1500 | 15.23 | weak_reference_control_only | §12.2 R5.2：weak ref 8 / 8 scenarios above main，但 \|E_ref\| 偏低不是物理优势 |
| 900 × 1400 | 12.30 | optional_robustness_probe_only | §6.4 表 6.4.A + §5.3 P0 audit；不得 redefine main-660 |
| 500 × 1200–1500 | 17.39–19.64 | context, surrogate_sensitive_not_promoted | §10.4 width-prior + §12.2 sidecar |
| 600 × 1500 | 16.55 | context, surrogate_sensitive_not_promoted | 同上 |
| 800 × 550 | (NODI lens 47.15%) | paper-sanity / cross-check（仅作为 §14 Tsuyama 对照）| 不替代 main-660；详 §14.6（口径 B Tsuyama 2022 NODI 对照）|

### 10.6 多候选裁决表（"为什么不挑数字最高的，也不挑最像 Tsuyama 的"）

读者最希望看清楚的不是"哪个候选数字高"，而是"为什么最终选 main-660 而不是其它看起来更亮眼的候选"。下表把所有相关候选放到一起，**按多条件裁决而不是单指标排名**对照：

> **lens 列拆分（v5.1.1 hotfix）**：原表把 all-cross 和 NODI lens 放在同一 cell（如 `12.52 (all-cross) / 45.15 (NODI lens)`）容易诱发跨 lens 比较。本版拆为 2 列分别展示 `all-crossing synthetic score (%)` 与 `NODI engineering proxy (%)`；空 cell 用 `—` 表示该 lens 在此候选下无直接行（**不是 0%**）。

| candidate | peak signal（相对 main） | all-crossing synthetic score (%) | NODI engineering proxy (%) | transit (ms) | noise / margin 风险 | paper-likeness | route governance | why yes / why not |
|---|---|---:|---:|---:|---|---|---|---|
| **660 / 800 × 1400 (main 1)** | 1.00× baseline | **12.52** | **45.15** | 8.94 | 中等（baseline）| 与 2022 NODI 几何同方向 | **conditional_relative_main**；近壁细网格通过 1.0；P6 / P8 / P14 trace 首位 | **WHY YES**：通过所有 5 条主裁决：物理稳定 + width-prior 可接受 + 近壁细网格 + R5.2 sidecar + P0 audit + paper trend 对齐 |
| **660 / 800 × 1500 (main 2)** | ≈ 1.00× | **12.70** | — (NODI lens 未直接覆盖此 H) | 8.94 | 中等 | 同 main 1 | **conditional_relative_main**；近壁细网格通过 1.0；P10 / P12 / P16 trace 首位 | **WHY YES**：与 main 1 在 trace 间互换首位，作为集合保留；不挑单一冠军 |
| 660 / 500 × 1500 | 略低（参考场偏离 baseline）| **19.64**（all-cross 内数字最高）| — | 8.94 | 高（窄通道工程风险被原模型低估）| 偏离论文器件 | **context, surrogate_sensitive_not_promoted**（ratio_vs_main 1.557）| **WHY NOT**：§10.4 width-prior `(W/800)^1.5/^2` 加补缺后越线消失；R5.2 sidecar `context_route_promotion_authorized = false`；P0 audit 把 563 条类似路线降级 |
| 660 / 700 × 1500 | 偏低（\|A_ref\| 弱）| 15.23 | — | 8.94 | 中等-高（reference too weak）| 偏离论文器件 | **weak_reference_control_only**；R5.2 显示 weak-ref 8 / 8 scenarios above main | **WHY NOT**：all-cross detection 看似高但 \|A_ref\| 偏低 → cross term 弱 → 不是物理优势；治理上仅作 control |
| 660 / 900 × 1400 | ≈ 1.00× | 12.30 | — | 8.94 | 中等 | 偏离论文器件 | **optional_robustness_probe_only** | **WHY NOT (as main)**：all-cross detection 与 main 持平但治理边界禁止 main-660 redefinition；保留为 probe |
| 404 / 600 × 1300 | ≈ 2× peak（短波散射强）| 4.45 | — | 5.48 | 高（transit↓ + phase flip↑ + margin↓）| out-of-scope | **shortwave_probe_only**；P6–P16 trace 始终排第 3 | **WHY NOT**：peak↑ 但 transit↓ + margin↓ → detection 反而最低；§2.4 / §6.4.F 详解；404 nm 热效应旁路 §15 forbidden 不得加分 |
| 660 / 800 × 550（Tsuyama 论文 depth）| ≈ 1.00× | — | **47.15** (NODI lens 内最高之一) | 8.94 | 中等 | **最接近论文器件几何** | **paper-sanity / cross-check**；不替代 main-660 | **WHY NOT (as main-660)**：paper-likeness 高但 v5.0 main-660 治理选择**不依赖**单纯"接近 Tsuyama 几何"；保留为 cross-check 几何 |
| 口径 B frozen diagnostic set: 660 / 1200 × 550 + 660 / 800 × 550（Au panel + selected-annulus）| — | — | — | 8.94 | — | step 1 校准 lens 内 raw Au peak-height exponent residual 最低 (3.0335 / 3.0456) | **conditional diagnostic set, release_status = negative_or_diagnostic_result_only** | **WHY YES (as 口径 B)**：在 step 1 校准过的 reproduction lens 内 residual 最低（**不是因为最像 Tsuyama 几何**；§11.4 关键澄清）。注：口径 B 用 reproduction score 而非 detection 排名 |

> **裁决原则总结（必须看完）**：本表的关键不是某个候选在某列上得分多少，而是 **5 条裁决条件必须同时成立**才能成为 main 推荐：
>
> 1. **物理稳定性**：peak / margin / transit 在合理 operating band；不被 §8.5 任一 blocker 主导
> 2. **风险先验补缺**：width-prior `(W/800)^1.5/^2` 加补缺后不被压损（main 保留比 ≥ 0.9）
> 3. **多 lens 一致性**：在 NODI engineering / 2020 paper / 2022 paper / all-crossing 等多 lens 下方向一致
> 4. **route governance**：通过 P0 audit + R5.2 sidecar + P6–P16 bounded trace 一致裁决
> 5. **不越过 §15 forbidden**：不得 main-660 redefinition / route promotion / paper-calibrated claim
>
> 任何"单指标最高"的候选（如 detection 数字 19.64% 的 500×1500、peak 数字 ≈ 2× 的 404 / 600×1300、paper-likeness 最高的 800×550）**都至少缺其中 1 条裁决条件**——这就是为什么 main-660 锁在 800 × 1400 / 1500 双集合而不是单 winner，也是为什么口径 A 推荐与口径 B 推荐**不同几何**的根本原因。

**一句话 takeaway（表 10.6）**：main 推荐**不是单指标最优**，是 5 条裁决一致结果；任何看起来"数字更高 / 更像论文"的候选，都至少有 1 条裁决不通过——读者无须再问"为什么不选 X"，对照上表 why not 一栏即可。

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

| 选型维度 | 候选范围 | step 1 lens 内 residual 最低的冻结 diagnostic set | step 2 residual 理由（出处） |
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
已是 reproduction-lens 框架内 residual 最低的低自由度 diagnostic 解（**仍 release_status = negative_or_diagnostic_result_only，不是 accepted candidate**）；这就是 v4.0 把当前参数集冻结为口径 B 选型的逻辑根据。
```

### 11.5 reproduction 增益（口径 B 视角）

| 对比 | reproduction score | 含义 |
|---|---:|---|
| Phase 2 family-ladder baseline median | ≈ 2.6–2.9 | raw inverse search 起点 |
| D2.1 best + γ = 0.749 (Phase 2.11) | **2.033** | bounded partial 阈值 2.0；当前冻结 diagnostic set（**非 accepted candidate**）|
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

### 11.8 口径 B step 流程表（"input → output → what it is not"）

读者最容易把口径 B 的两步框架误读为"为了贴近 Tsuyama 而调几何"。下表把 §11.1–§11.7 整个流程拆成 6 步 + 每步明确"它是什么"和"它不是什么"，避免误读：

| step | action | input | output | what it is NOT |
|---|---|---|---|---|
| 1 | 读取 Tsuyama 论文 target | Tsuyama Table S1 Ag/Au signal、Au size exponent ≈ 2.3、Au30/Au20 SNR ≈ 33/12、selected-annulus 0.5–0.8 几何 guardrail、classification accuracy 71.9% (diagnostic only) | 一组论文目标值 + target-mode 标注（direct / inferred / operational / diagnostic only） | **不是**把 Tsuyama 论文当作 EV NODI 的正验证；**不是**直接用 Tsuyama 数值作为 calibrated reference |
| 2 | 用 Tsuyama 数据反推估计参数 | 上面 step 1 的论文目标 + Phase 2 family-ladder + Phase 2.5 D2 + D2.1 局部 smoke + Phase 2.6–2.11 reproduction lens 链 | γ / s_SNR / e_SNR / D2.1 best 算子的反推数值；reproduction score | **不是**校准（§13 第 4 档不是第 6 档）；**不是**把这些参数当成仪器物理常数 |
| 3 | 冻结 calibration parameter set | step 2 反推出的 4 项估计参数 + selected-annulus 0.5–0.8 + lock-in τ = 1–2 ms + readout = pulse peak height + Au panel 20/30/40/60 + Ag 40/60 + ET-2030 + LI5640 + current input/TIA | §11.7 冻结参数集 | **不是**最终验证通过的 calibrated set；**不是**可以推广到 EV biomimetic 工程库的物理参数 |
| 4 | 在冻结参数下重新评价候选几何 | step 3 冻结参数 + Phase 2.10 raw Au peak-height exponent case-level decomposition（660/1200×550 = 3.0335、660/800×550 = 3.0456、532/800×550 = 3.1563 等 6 case） | 每个候选几何的 raw Au size exponent residual vs Tsuyama 2.3 | **不是**为了"挑最像 Tsuyama 论文器件几何"——只看校准 lens 内 residual 数字；几何与论文器件方向重叠是物理一致性，不是选型逻辑 |
| 5 | 选择 residual 最低的 diagnostic geometry | step 4 的 residual 排名 | 660 / 1200 × 550（residual 全 6 case 最低，3.0335）+ 660 / 800 × 550（次低，3.0456）作为口径 B 主对照几何；488 / 800 × 550 / 1200 × 550 + 532 / 800 × 550 / 1200 × 550 作为 wavelength 对照 | **不是** main route candidate；**不是**口径 A 工程主线的 cross-validation；**不是** release-positive optimization |
| 6 | 保持 release 状态 | step 5 选定 set + Phase 2.11 total reproduction score 2.033（仍高于 partial 阈值 2.0）+ formula-consistent Ag/Au pass + raw Au size unresolved + classification no_accuracy_claim | release_status = negative_or_diagnostic_result_only；冻结参数集（§11.7）作为口径 B 输出 | **不是** accepted paper-calibrated candidate；**不是**推翻口径 A；**不是**允许放宽 §15 forbidden 中的任意一条 |

**一句话 takeaway（表 11.8）**：口径 B 走的是 "**校准在前、选型在后**" 的两步流程；每一步都有明确的"input → output → what it is not"。读者只要走完这 6 步，就不会再问"为什么不挑最像 Tsuyama 几何的"——答案是 step 4 / 5 不走那条捷径，只看校准 lens 内 residual。这条逻辑也是 v4.2 / v5.0 / v5.1 反复强调"口径 B release 仍 negative_or_diagnostic_result_only"的根本原因（step 6）。

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

### 13.1 6 档（含 1a）来源谱总表

读者最常被误读的：v5.0 报告里的每个数字属于哪一档证据？7 档（在 v5.0 内把 v4.2 第 1 档"物理常数 + 仪器设定"拆成 1 物理常数 + 1a 仪器设定 / 论文条件，避免读者把 NA 当物理定律）总表如下：

| 档位 | 含义 | v5.0 报告中代表 | 可作为物理推导输入？ | 可作为仪器 / 实验校准声明？ |
|---:|---|---|---|---|
| 1 | **物理常数 / 教科书参数** | λ, π, n_water, c | ✅ 是 | — |
| 1a | **仪器设定 / 论文条件**（外部规范，本报告作为输入引用，不是物理定律）| 收集 NA = 0.9 (Tsuyama 2020 / 2022)、照明 NA = 0.45、流速 0.2 mm/s、lock-in τ = 1–2 ms、threshold_sigma = 5 / 10 | ✅ 是（作为已知输入条件）| ❌ 否（这些是论文 / 工程规范，不是 v5.0 报告内做出的校准声明）|
| 2 | **Mie 推导值**（由档 1 + 1a 直接计算）| Csca, Cext, Cabs, S1, S2, transit time (§6.1)、Au Csca (§6.2) | ✅ 是（受输入折射率精度限制）| ❌ 否 |
| 3 | **Surrogate 模型估值**（明确标 surrogate）| `channel_angular_surrogate` 参考场、`pupil_slit_surrogate` 收集、`lockin_surrogate` 读出、`relative_surrogate` 相位、Wilson LB | ⚠️ 部分（方向有效，绝对量级不解锁）| ❌ 否 |
| 4 | **Reproduction-lens 估计项**（口径 B Phase 2.6–2.11）| γ = 0.749, s_SNR = 0.728, e_SNR = 0.812, D2.1 best 算子, Au size delta ≈ −0.80, Phase 2.11 reproduction score 2.033 | ❌ 否（不是物理常数）| ❌ 否（明确禁止视为仪器物理量；§15 / §11.7）|
| 5 | **可接受解释先验**（口径 A 路线治理）| width-prior `(W/800)^1.5 / ^2`、`0.5–0.8` selected-annulus 边界、noise_std `0.01`、shot_noise_scale `0.001`、post_readout_noise_std `0.002`、路线角色分类 | ❌ 否（解释模型，不是物理定律）| ❌ 否 |
| 6 | **校准 / 实测值** | **当前 0 个**；v5.0 全文 `calibrated_claim_allowed = false`、`measured_data_ingest_authorized = false` | — | — |

读者结论：**v5.0 报告所有可视化数字至多到第 5 档**（实际多在 1a–4 档）。**第 1a 档不能解锁第 6 档**——例如收集 NA = 0.9 是论文条件，可作为推导 transit / E_sca 的输入，但不能由此声称本报告做了"NA = 0.9 的校准"。任何把 3–5 档当作第 6 档的解读都违反 §15 共同 forbidden claim。

高频被误读数字的正确档位：

| 数字 | 出处 | 档位 | 容易被误读为 | 正确读法 |
|---|---|---:|---:|---|
| 收集 NA = 0.9 / 照明 NA = 0.45 | §3.2 / §6.1 | 1a | 1（物理常数）或 6（已校准）| 论文条件 / 仪器规范，作为推导输入；**不是** v5.0 内的 calibration |
| EV Csca× 7.10× | §6.2 | 2 | 6 | Mie 推导，不解锁 calibration |
| peak× 2× (404 vs 660 nm) | §2.4 | 2 (Mie) × 3 (surrogate) | 6 | surrogate 相对放大，不解锁 absolute peak unit |
| detection 12.52% / 47.15% | §6.4 / §7 | 3 (synthetic relative-prior) | 6 (event probability) | 合成相对先验代理计数比例，**不是事件概率** |
| γ = 0.749, s_SNR = 0.728 | §11.7 | 4 | 5 或 6 | reproduction-lens 估计项，不是物理常数 |
| (W / 800)^2 width-prior | §10.4 | 5 | 6 | 解释模型，不是物理定律 |
| 0.5–0.8 selected-annulus 窗口 | §4 / §11 | 5 (canonical) | 5 但**不可移动**（§15）| canonical default，移动需另起 sensitivity 流程 |
| Wilson LB | §2.2 阶段 7 | 3 | 3（被误读为"安全下界"）| finite-event statistical lower bound，**不是** safety bound |

### 13.2 阶段量来源与置信等级映射表

读者最希望知道的不是"哪个证据档是几档"，而是"我看到的某个具体数字（Csca / E_sca / |A_ref| / cross term / peak / noise / margin / transit / detection / route score / paper-likeness / Tsuyama residual）属于哪一档、是怎么算出来的、可以用来做什么"。下表把 v5.0 / v5.1 报告里读者会反复看到的 13 个阶段量整理成"符号 / 来源 / 推导方式 / 置信档位 / 可用于什么"5 列对照：

| 阶段量 | 符号 | 来源 (报告位置 + 主要 results 目录) | 推导方式 | 置信档（§13.1）| 可用于什么 / 不可用于什么 |
|---|---|---|---|---|---|
| Mie 散射截面 | Csca | §6.2.1 / §6.2.2；`results/ev_nodi_realism_v2_full_grid_R5_v2/` 内 case 字段 | 输入 n, k, λ, a 的 Mie 直接计算 | 2（Mie 推导）| ✅ 物理推导；❌ 校准 / 实测声明 |
| 收集场幅值 | \|E_sca\| | §3.0a / §6.4 / §7.x 间接出现；surrogate 算子 collapse | √Csca · L_det collapse 因子 | 2 + 3 | ✅ 推导；❌ absolute detector unit chain |
| 参考场幅值 | \|A_ref\| | §6.3 / §3.0a；`results/ev_nodi_realism_v2_full_grid_R5_v2/` reference 字段；reports/49 paper-aligned 变体 | `channel_angular_surrogate` 算子 + 同 L_det collapse | 3（surrogate）| ✅ 方向性比较；❌ absolute \|E_ref\| 校准 |
| 干涉一次项 | cross term | §3.0a 公式块；§2.4 / §7.2.5a 表 | 2 \|A_ref\|·\|E_sca\|·cos(Δφ) | 2 + 3 | ✅ 推导 / 方向性；❌ release-positive |
| 自散射二次项 | self term | §3.0a 公式块 | \|E_sca\|² = Csca | 2 | ✅ 推导；❌ release-positive |
| 平均脉冲峰值 | mean peak height | §6.4 表 6.4.D / 6.4.C；`results/ev_nodi_realism_v2_full_grid_R5_v2/` summary | batch 字段 mean_peak_height | 3（surrogate）| ✅ 同 lens 同 panel 比较；❌ cross-lens / cross-panel ranking |
| 噪声代理 | noise proxy | §3.0a / §8.4 / §8.5；`SimulationConfig` noise_std + shot_noise_scale + post_readout_noise_std | pre-readout (高斯 + shot + drift) + post-readout 模型加和 | 5（可接受先验：noise_std=0.01 等）| ✅ 同模型内 sensitivity；❌ 实测 noise 替代 |
| 峰值 margin z | mean_peak_margin_z | §5（batch 字段）/ §8.6 sensitivity 表；同 results 目录 summary 字段 | (peak − threshold) / robust_std 量级 | 3（surrogate）| ✅ 同 lens 内稳定性；❌ absolute SNR 校准 |
| transit 时间 | transit | §6.1 / §7.x；推导 | 2 · w_0 / v_flow，w_0 = 0.61 · λ / NA | 2 + 1a（论文条件 NA / v_flow）| ✅ 物理推导（依赖论文条件输入）；❌ NA / v_flow 实测校准声明 |
| 合成 detection | synthetic detection score / proxy | §6.4 / §7.x / §10 / §11 各 detection 表；`results/ev_nodi_realism_v2_full_grid_R5_v2/` summary detection_rate / stable_detection_rate | batch find_peaks 后 n_detected / n_events，按 lens 分母（all-crossing / selected-annulus / NODI engineering 等） | 3（synthetic relative-prior）| ✅ 同 lens 同 panel 内排序；❌ 事件概率（不是 P(event detected)）；❌ cross-lens / cross-panel 直接比 |
| route score | route_score | `results/post_v2_mandatory_audit/`；§5.3 P0 audit 行 | engineering_score / final_engineering_score 加权 | 3 + 5（surrogate 评分 + 可接受先验）| ✅ 同 lens route 排序；❌ 直接转 detection 概率 |
| paper-likeness | （多种 lens）| §6.4 表 6.4.B（NODI engineering / 2020 paper / 2022 paper lens）；§14 论文对照 | 同 detection batch + 论文条件 lens metadata 切片 | 3（surrogate lens）| ✅ 同 lens 内方向性；❌ paper accuracy 已复现声明 |
| Tsuyama residual | reproduction score | §11.2.3 / §11.5；`results/tsuyama_phase2p11_response_compression_rescore_d2p1_v1/` | reproduction lens 多目标 lower-is-better penalty 加和 | 4（reproduction-lens 估计项）| ✅ 口径 B candidate 排序；❌ 当作物理常数 / 校准声明 / 推到口径 A |

读法：

```text
- 任何"× 倍数"列（§2.4 / §6.4.F / §7.2.5a）只能用于"同 baseline 同 lens 同 panel 比较"；
  不能跨档位或跨 lens 直接乘进总倍数（§3.0a 三条骨架公式）。
- 任何 detection % 列都是 synthetic detection score 或 proxy；
  读到一个百分比时先回到本表确认它来自哪个 lens / 哪个分母（§4 详解）。
- 任何 reproduction score / Tsuyama residual 都是第 4 档 reproduction-lens 估计项；
  不能跨到口径 A，更不能转成校准声明（§11.4 / §11.8 step 6）。
```

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
| NODI engineering stable detection proxy (%) | 33.65 | **47.15** | 45.15 | 42.60 |
| 2020 paper lens (%) | 34.50 | 43.50 | 41.00 | 44.20 |
| 2022 NODI paper lens (%) | 35.40 | **46.70** | 42.90 | 47.05 |

**结论**：

1. 固定到 2022 NODI 语义后，660 nm 仍强于 404 nm
2. **800 × 550 几何在多个 lens 下都是高值且接近 Tsuyama 论文器件几何**，但**并不是该表唯一最高**——例如 660 / 900 × 1200 在 2022 NODI paper lens 下 = 47.05%，略高于 660 / 800 × 550 = 46.70%。所以这里不是"最优几何收缩到 800 × 550"的强结论，而是"800 × 550 处于高值簇且物理上接近论文器件，可作 cross-check 几何"
3. 工程主线 660 / 800 × 1400 / 1500 与 paper 几何 800 × 550 在多 lens 下方向一致；但 main-660 锁的是工程几何，**不**因 paper geometry cross-check 发生 route promotion 或 main-660 redefinition

口径 B reproduction lens 链（Phase 2 / 2.5 / 2.6–2.11）已经在 §11.2 详细展开；几何选型最终落到 800 × 550 + 1200 × 550 是 step 1 校准过的 lens 内 raw Au peak-height exponent residual 最低，而不是这张 §14.6 表里 detection 的最高（§11.4 关键澄清）。

### 14.7 Tsuyama 2024 POD + NODI (Simultaneous Light Absorption and Scattering)

**论文条件**：探测 660 nm + 激发 532 nm；time constant 1–2 ms；frequency split 1.2 / 4.1 kHz；通道宽 800–1200 nm + 深 ~550 nm；POD + NODI 配对脉冲读出。

**当前模型对照**（§6.4 表 E）：

| 读出方式 | strict gate 通过比例 | mean detection proxy (%) |
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
- 当前冻结 diagnostic set 已确定（§11.7，**release_status = negative_or_diagnostic_result_only**）；按 D2.1 best + γ = 0.749 + 选定几何 + 推荐硬件接法出最终结果；
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

### 16.2 实测 artifact 优先级清单（artifact → 解决哪个不确定性 → 会改变哪个结论）

| 优先级 | Measured artifact | 解决的不确定性 | 一旦获得，会改变 v5.0 哪个结论 |
|:-:|---|---|---|
| 1 | measured **Au raw trace**（按 Phase 2 paper-audit 几何采集 Au panel 20–60 nm 实测信号）| 口径 B step 1 校准目前是 reproduction-lens 估计（§13 第 4 档），不知 raw exponent 偏陡是否来自模型 surrogate 还是真实 Au 散射 | 把 §11.2 step 1 校准从第 4 档推到第 6 档；§11.3 step 2 几何选型可能改变；§11.7 冻结参数集可能更新；§13 表新增第 6 档行 |
| 1 | measured **blank / BFP / slit / ROI scan**（参考场 + 收集算子的实测对照）| 口径 A 主路线 \|E_ref\| 模型仍是 surrogate（§13 第 3 档），且 §6.3 给的 2–9% 差异是相对 surrogate 不是相对 absolute | §10 main-660 conditional → 可能升级 / 降级；§6.3 表数字可能进入第 6 档；§11.3 step 2 收集算子选择可能改变 |
| 2 | **lock-in / logger 配置实测**（ET-2030 + LI5640 实际响应度 / NEP / current-input vs voltage path 实测对照）| §11.6 硬件接法 216 / 216 vs 211 / 216 仍是量级估计（§5.5）| 把 §11.6 推到第 6 档；可能允许 absolute SNR claim（仍受 §15 forbidden 约束）|
| 2 | **PEG / fluidic 流体可行性**（窄通道颗粒输运实测）| §10.4 width-prior 是可接受解释模型（§13 第 5 档），但没有直接实测窄通道运输风险 | 验证或推翻 width-prior；可能改变 §10.5 路线治理裁决 |
| 3 | **EV polydispersity / non-sphericity / coincidence / blended pulses** | v2 / v5.0 未建模的 EV 真实形态分布 | 可能在 §10 main-660 detection 上加入 polydispersity 修正；不会改变路线选型方向 |
| 3 | **roughness / fabrication background / PEG fouling / drift** | post-v2 validation program 的项 | 长期影响 main-660 路线 long-term reliability；不改变当前选型 |

读法：

```text
优先级 1 = 直接解锁 §13 第 4 档→第 6 档跨越，影响最大
优先级 2 = 把 §13 第 3 / 5 档的某项升档；改变 §11.6 硬件 / §10.4 width-prior 解释
优先级 3 = 改善细节 / 长期可靠性，不动 v5.0 选型方向
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
| v4.0 amendment | 2026-05-11 | 口径 B 当前参数集冻结为选型（在 v4.2 旧版 §14.12 / 14.13 / 14.14；在 v5.0 重新组织为 §11.7 冻结参数 + §14.6 Tsuyama 2022 NODI 对照 + §11.6 硬件接法）|
| v4.1 | 2026-05-11 | 新增**旧版 §16** 读者向解读层（物理链 + 估计值来源 + 变量影响排序 + 推荐因果链）。**与 v5.0 现行 §16（Open dependencies 与下一步实测）不是同一节**——v5.0 把旧版 §16 拆散到现 §2 / §13 / §9 / §10 / §11 |
| v4.2 | 2026-05-11 | 旧版 §16.9.2 改两步框架（用户反馈 1）→ v5.0 移到 §11.2 / §11.3 / §11.4；旧版 §16.3 / §16.4 改 ms / % 多表（用户反馈 2）→ v5.0 整合进 §6.4 + §7.1 / §7.2 |
| **v5.0** | **2026-05-11** | **reader-centric 全文重构**：把层层叠加结构改为问题 → 物理 → 变量 → 数据 → 分析 → 推荐 → 边界 → 出处的一次性叙事；代码层 ID 改名为可读科学命名；附录给出对照 |
| v5.0 二次精修 | 2026-05-11（commit `c67c768`）| 按 codex 审阅清单做 P0（§2.4 数学 / 方向修正、§3.3 Csca 错归因、§8.4 weak-ref 解释、§7.4 同 lens 差异限定、§9 跨 lens 排名、§14.6 800×550 收缩修正）+ P1（§13 拆 1a 档、§6.4 detection 命名、§7.1 标题、§7 数据覆盖矩阵、§10.2 口径声明、§11 "最优"改"residual 最低 diagnostic set"、§6.2.2 Au plasmon 免责声明）+ P2（§0 一页版地图、§3.0 变量依赖图、§5.3 阶段类型标注、§6.4 takeaway、§10.4 width-prior 白话、§16.2 artifact 三列表、§18 旧版 §16 标注）|
| **v5.1** | **2026-05-12** | **reader table supplement**（codex 第二轮反馈吸收）：新增 §0.3b 读者问题导航表 + §3.0a 阶段量级联解释 + 7.0 变量固定法 + §7.2.5a 信号链扩列对比（2 张代表性表）+ §8.5 blocker 分类表 + §8.6 噪声 sensitivity 数值表 + §10.6 多候选裁决表 + §11.8 口径 B step 流程表 + §13.2 阶段量来源映射表；扩展 §2.4 到 4 波长机制链。**不引入新 simulation / solver case / candidate / lane / random seed / measured artifact ingest**；新增读者表为派生重组 / 单位换算 / 物理近似解释，数值与 forbidden 与 v5.0 完全一致。|
| **v5.1.1 hotfix** | **2026-05-12** | codex 第三轮反馈 P0 + P1 修正：新增真实 §6.4.F 让先前引用不悬空；§2.4 拆 strict block A + route-level block B；§8.6 reference×2 逻辑修正（option A：noise model 不变→threshold 不同步上抬）；§10.6 mixed-lens cell 拆 2 列；统一 detection 表头为 `synthetic detection score (%)` / `proxy (%)`；§8.5 / §8.6 takeaway 表号修正；`window-prior` → `width-prior` 拼写修正；header 把"不引入新计算"改成精确表述（不引入新 simulation / solver case / candidate / lane / random seed / measured artifact ingest）|
| **v5.2** | **2026-05-12** | **reader comparison table pack**：附录 D（5 张固定 W × H vary λ derived reader tables）+ 附录 E（5 张固定 λ vary W × H derived reader tables）+ 附录 F（strict controlled vs route-level 14 行对照矩阵——v5.2 防误读核心）。每张表明确 source type / strict controlled / baseline；detection cell 只在 strict 直接行时填，否则 `—` + note 最近邻。**不引入新 simulation / solver case / candidate / lane / random seed / measured artifact ingest**；仅做派生重组、单位换算、物理近似解释和读者向诊断表。|
| **v5.2.1 hotfix** | **2026-05-12** | codex 第四轮反馈（consistency hotfix）：(1) §18.7 修正 report 47 CSV 存在性表述（codex 第三轮其实正确——文件在 `reports/current/47_ev_design_full_grid_analysis/`，v5.1.1 漏查目录；迁移仍延后做 audit）；(2) §18.2 v5.2 行 "不引入新计算" → 精确表述；(3) ledger 122 同；(4) §18.6 / 附录 F 表号修正；(5) 统一遗漏的 detection 表头（`Au20 det (%)` / `all-crossing detection (%)` 等）；(6) 附录 D.1 / D.3 / E.3 / E.5 mixed-lens cell 拆为多列或挪到 note；(7) 附录 F 14 行对照"detection 仅 660 cell" → "detection 仅 source type 标 strict 直接行的 cell"；(8) §6.4.F trailing whitespace；(9) report 88 行数 typo 2455 → 2453。**不引入新内容**，仅 consistency 修正。|

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

### 18.4 v5.1 / v5.1.1 reader table supplement 的 8 项验收（codex 第一与第二轮反馈映射）

v5.1 / v5.1.1 仅做读者表格 / 解释增强 + 风险点 hotfix，不改变 v5.0 / v4.2 任何数值或 forbidden。

**口径声明（重要，v5.1.1 修正）**：v5.1 已完成 reader table supplement 的**第一层代表性补表**（§6.4.F + §7.2.5a 各 1–2 张代表性扩列表 + §10.6 + §11.8 等导航 / 解释表）；**完整多表格 reader comparison pack**（每个固定几何 / 固定波长 5–7 张完整表）放在 v5.2（详 §18.6）。下列 8 项验收**只回答"是否提供了读者直觉入口"，不回答"是否完成了完整多表格 pack"**。

验收按 codex 8 项读者问题：

| # | codex 验收问题 | v5.1 解决位置 | 状态 |
|--:|---|---|---|
| 1 | 我能不能看到某个固定尺寸下 404/488/532/660 的完整对比？ | §2.4 4 波长机制链 + §7.2.5a.1 信号链扩列（800×1400 nm）| ✅ |
| 2 | 我能不能看到固定 660 nm 时不同 W/H 为什么有差异？ | §7.2.5a.2 信号链扩列（660 nm + H=1500，vary W）+ §7.2.x + §10.4 width-prior + §10.6 多候选裁决 | ✅ |
| 3 | 我能不能看懂 Csca / E_sca / reference / cross-term / peak / noise / detection 之间不是简单线性关系？ | §3.0a 阶段量级联（"是谁、归谁管、三条骨架公式、三条不保证"）+ §13.2 阶段量来源映射 | ✅ |
| 4 | 我能不能知道 detection 低到底败在什么 blocker？ | §8.5 blocker 分类表（10 类 blocker）| ✅ |
| 5 | 我能不能理解为什么 404 peak 强但不一定推荐？ | §2.4 4 波长扩展 + §6.4.F + §10.6 候选裁决"why not 404"行 + §8 噪声归因 | ✅ |
| 6 | 我能不能理解为什么 660 main route 被保留？ | §10.2 5 步因果链 + §10.4 width-prior 白话 + §10.5 治理裁决 + §10.6 多候选裁决"why yes main-660"行 | ✅ |
| 7 | 我能不能理解口径 B 是"校准后选型"，不是"为了贴近 Tsuyama 而选型"？ | §11.4 关键澄清 + §11.8 step 流程表 (input → output → what it is NOT) + §10.6 候选裁决表（口径 B frozen diagnostic set 行）| ✅ |
| 8 | 我能不能清楚知道哪些表是既有 artifact 派生 / simulation 原始输出 / 解释性诊断？ | §13.2 阶段量来源映射表（13 个阶段量的"来源 + 推导方式 + 置信档"3 列）+ §5（study design）| ✅ |

### 18.5 v5.1 / v5.1.1 / v5.2 不变量

```text
1. 全部 §18.3 v5.0 不变量继续成立；
2. v5.1 / v5.1.1 / v5.2 不引入任何新 simulation / 新 solver case / 新 candidate /
   新 lane / 新 random seed / 新 measured artifact ingest；
3. v5.1 / v5.1.1 / v5.2 所有新表的数据都是既有结果的派生重组、单位换算、物理近似解释
   或读者向诊断表（包括 §6.4.F 信号链汇总、§7.2.5a 信号链扩列、§8.6 假想 sensitivity、
   §13.2 阶段量来源映射、附录 D / E 完整 reader pack、附录 F strict vs route-level 对照）；
4. v5.1+ 所有新表都按 v5.0 二次精修后的术语口径写：
   - detection 列写 synthetic detection score (%) 或 proxy (%)，不是事件概率；
   - transit 用 ms 绝对值，不用倍数；
   - 倍数列只用于阶段量（Csca× / |E_sca|× / |A_ref|× / cross-term× / peak× / noise×），
     且每张表都明确 baseline；
   - 固定 λ + 固定 panel 时 Csca 列写 "constant for same particle panel"，不写倍数；
5. 跨 lens / panel 的对比一律按 §7.0 变量固定法 5 条 + 附录 F 14 行对照矩阵进行，
   严禁 cross-lens 直接百分比 ranking；
6. 口径 B 流程严格按 §11.8 step 1 → 6 顺序展开，
   不允许把"为了贴近 Tsuyama 几何"读成选型逻辑（§11.4 关键澄清在 §11.8 step 4 / 5 重申）；
7. v5.2 附录 D / E 中 detection cell **只在 source type 标为 strict 直接行时填数字**；
   其他 cell 一律 `—` + note 列说明最近邻——这是防止 reader 把最近邻当 strict 数据的硬约束。
```

### 18.6 v5.2 reader comparison pack 验收

v5.2 完成 codex 第三轮验收清单（10 项）的覆盖：

| # | codex v5.2 验收问题 | v5.2 解决位置 | 状态 |
|--:|---|---|---|
| 1 | 我能不能看到多个固定尺寸下 404 / 488 / 532 / 660 的阶段量对比？ | 附录 D 5 张表（800×1400 / 800×1500 / 800×550 / 600×1300 / 500×1500）| ✅ |
| 2 | 我能不能看到 660 nm 下多个 W / H 的阶段量对比？ | 附录 E 5 张表（H=1400/H=1500 vary W；W=800/W=500 vary H；404 sweep）| ✅ |
| 3 | 我能不能区分 strict controlled comparison 和 route-level evidence？ | 附录 F 14 行对照矩阵；每张 D/E 表的 source type 列；§7.0 变量固定法 5 条 | ✅ |
| 4 | 我能不能知道哪些 `—` 是数据 gap，而不是 0？ | 附录 D / E note 列明确 "—" = "此 cell 无 strict 直接行；最近邻是 X% (不同 lens / 不同几何)"；§7 数据覆盖矩阵已声明 | ✅ |
| 5 | 我能不能看懂为什么 Csca 高不等于 peak 高、peak 高不等于 detection 高？ | §3.0a 三条骨架公式 + 三条不保证警告 + §6.4.D Au 粒径阶梯实证 | ✅ |
| 6 | 我能不能看懂为什么 404 peak 强但不推荐？ | §2.4 块 A + 块 B + 附录 D.4 (404 / 600 × 1300 strict 直接行 = 4.45%) + §10.6 候选裁决 why not 行 | ✅ |
| 7 | 我能不能看懂为什么 660 / 800×1400 和 800×1500 是 main 集合？ | §10.2 5 步因果链 + §10.6 候选裁决 + 附录 E.3 / E.1 / E.2 strict 直接行 | ✅ |
| 8 | 我能不能看懂为什么 500×1500 score 高但不 promotion？ | §10.4 width-prior + §10.6 候选裁决 + 附录 E.4 (W=500 vary H 4 行全降级) + 附录 D.5 | ✅ |
| 9 | 我能不能看懂口径 B 是先反推参数，再在 frozen lens 里选 residual-lowest geometry？ | §11.4 关键澄清 + §11.8 step 流程表 + 附录 F 第 §11.2.3 行 strict ✅ + §10.6 候选裁决 口径 B frozen diagnostic set 行 | ✅ |
| 10 | 我能不能知道每张表的数据来自哪里、是什么证据档位、能不能用于 release-positive claim？ | §13.2 阶段量来源 + 附录 F source type 列 + §13.1 7 档证据谱 + §15 forbidden | ✅ |

### 18.7 关于旧 report 47 派生表的迁移决定

**v5.2.1 修正（codex 第四轮反馈）**：v5.2 / v5.1.1 写"file 不存在"是错的——v5.1.1 的 `find` 只查了 `results/` 和 `archive/`，**漏查了 `reports/current/`**。codex 第三轮反馈是正确的，以下 6 个 historical report 47 派生 CSV 实际存在于本地：

```text
reports/current/47_ev_design_full_grid_analysis/mechanism_chain_by_wavelength_EV_medians.csv
reports/current/47_ev_design_full_grid_analysis/paired_wavelength_effect_ratios_EV.csv
reports/current/47_ev_design_full_grid_analysis/geometry_effect_ranges_EV.csv
reports/current/47_ev_design_full_grid_analysis/within_lambda_top_geometries.csv
reports/current/47_ev_design_full_grid_analysis/wavelength_404_to_660_signal_decomposition.csv
reports/current/47_ev_design_full_grid_analysis/reference_operating_point_by_lambda.csv
```

**v5.2 决定（修正后表述）**：这些 historical report 47 CSV 存在于 `reports/current/47_ev_design_full_grid_analysis/`，但 v5.2 不迁移它们——迁移需要单独做 provenance / 术语 / lens / panel / forbidden-claim 审计（旧 report 47 用的术语和 lens 口径与 v5.0 二次精修后的命名规范不同步，直接搬入会引入 release-positive 误读）。当前 v5.2 已用附录 D / E / F 满足 reader comparison pack 的核心需求（§18.6 验收 10 项全 ✅）；report 47 迁移**延后到专门的审计补充或 P19 之后**。

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
| **v5.1 新增**：读者问题导航表（10 行）| §0.3b | 表 0.3b |
| **v5.1 新增**：阶段量是谁/归谁管 + 三条骨架公式 + 三条不保证 | §3.0a | 表 3.0a |
| **v5.1 新增**：4 波长机制链（404 / 488 / 532 / 660 信号链分解）| §2.4 | 表 2.4（扩展）|
| **v5.1 新增**：变量固定法 5 条（如何读 controlled comparison）| §7.0 | 表 7.0 |
| **v5.1 新增**：信号链扩列对比（800×1400 + 660 nm/H=1500 vary W）| §7.2.5a | 表 7.2.5a.1 / 7.2.5a.2 |
| **v5.1 新增**：blocker 分类表（10 类 detection blocker）| §8.5 | 表 8.5 |
| **v5.1 新增**：噪声 sensitivity 数值版（包含 reference×2 / noise×2 假想）| §8.6 | 表 8.6 |
| **v5.1 新增**：多候选裁决表（why yes / why not main-660 等 8 候选）| §10.6 | 表 10.6 |
| **v5.1 新增**：口径 B step 流程表（input → output → what it is NOT）| §11.8 | 表 11.8 |
| **v5.1 新增**：阶段量来源与置信等级映射（13 个阶段量）| §13.2 | 表 13.2 |
| **v5.1.1 新增**：4 波长信号链汇总（800×1400 同 W×H，4 波长 strict + route-level 评估）| §6.4.F | 表 6.4.F |
| **v5.2 新增**：strict vs route-level 对照矩阵 | 附录 F | 表 F |
| **v5.2 新增**：固定 W×H vary λ 5 张表 | 附录 D | 表 D.1–D.5 |
| **v5.2 新增**：固定 λ vary W/H 5 张表 | 附录 E | 表 E.1–E.5 |

---

## 附录 D：固定 W × H 看波长（5 组 derived reader tables，全 strict / 部分 strict）

> **说明**：本附录是 v5.2 reader comparison pack 的核心。每组对应一个固定几何，列出 4 个候选波长（404 / 488 / 532 / 660）的全阶段量倍数 + transit 绝对 ms + synthetic detection score。**所有 detection cell 严格遵守**："如果 v5.x 没有 strict (固定几何 + 固定颗粒 panel + 仅扫 λ + 同 lens) 直接行，则填 `—` 且只在 note 列说明最近邻；不把最近邻 route-class 数字塞进 detection cell"。这一约束防止跨 lens / 跨几何混读（codex P0.4 修正原则）。
>
> **共用约定**：颗粒 panel 默认 EV biomimetic + 同 panel 跨波长保持一致；倍数列 baseline 都是 660 nm 同 W × H 同 panel；transit 用 ms 绝对值；阶段量来源 = §6.1 物理推导 + §6.2 Mie + §6.3 |A_ref| 衍射对照 + §3.0a 强参考场极限近似。

### 表 D.1 — 固定 W × H = 800 × 1400 nm（口径 A main 第一几何）

| λ (nm) | source type | Csca× | \|E_sca\|× | \|A_ref\|× | cross-term× | self-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | blocker / role | note |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 404 | strict 物理 + route-level note | 7.10 | 2.66 | ≈ 0.95 | ≈ 2.5 | 7.10 | ≈ 2.0 | 1.0 | 5.48 | — | transit / gating mismatch | 此 cell 无 strict 直接行；route-level 最近邻：shortwave probe class avg ≈ 4.45% (404 / 600 × 1300，几何不同) |
| 488 | strict 物理 + route-level note | 3.34 | 1.83 | ≈ 1.00 | ≈ 1.83 | 3.34 | ≈ 1.4–1.6 | 1.0 | 6.61 | — | 中等 transit 衰减 | 同上；route-level 最近邻：mid-wave class avg ≈ 7.77% (488 / 532 混合几何) |
| 532 | strict 物理 + route-level note | 2.37 | 1.54 | ≈ 1.00 | ≈ 1.54 | 2.37 | ≈ 1.2–1.4 | 1.0 | 7.21 | — | 接近 main，无 blocker | 同上 mid-wave class avg |
| 660 | **strict 直接行** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 8.94 | **12.52** (all-cross) | main, no blocker | §6.4 表 6.4.A `main_660_W800_D1400` 直接行；NODI engineering lens proxy = 45.15%（不同 lens；详 §6.4 表 6.4.B），不在此 cell 内做跨 lens 比较 |

> **takeaway D.1**：660 nm 是此几何下唯一有 strict 直接行的波长；其他 3 个波长只能从阶段量推导方向（短波 peak↑ + transit↓），detection cell 不可填。本表 detection 列固定为 all-crossing synthetic score (%) **单 lens**；NODI lens proxy 不与 all-cross 在同 cell 并列，避免重新引发跨 lens 误读。

### 表 D.2 — 固定 W × H = 800 × 1500 nm（口径 A main 第二几何）

| λ (nm) | source type | Csca× | \|E_sca\|× | \|A_ref\|× | cross-term× | self-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | blocker / role | note |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 404 | strict 物理 | 7.10 | 2.66 | ≈ 0.91 (深通道偏低) | ≈ 2.4 | 7.10 | ≈ 1.9 | 1.0 | 5.48 | — | transit / gating mismatch；reference 深通道偏低 | route-level 最近邻：shortwave probe class 4.45%（不同几何）|
| 488 | strict 物理 | 3.34 | 1.83 | ≈ 1.00 | ≈ 1.83 | 3.34 | ≈ 1.4–1.6 | 1.0 | 6.61 | — | 中等 transit | 同 D.1 mid-wave class avg |
| 532 | strict 物理 | 2.37 | 1.54 | ≈ 1.00 | ≈ 1.54 | 2.37 | ≈ 1.2–1.4 | 1.0 | 7.21 | — | 接近 main | 同上 |
| 660 | **strict 直接行** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 8.94 | **12.70** (all-cross) | main, no blocker | §6.4 表 6.4.A `main_660_W800_D1500` 直接行；NODI lens 在此 H 未直接覆盖 |

> **takeaway D.2**：与 D.1 同方向；800 × 1500 比 800 × 1400 detection 略高 (12.70 vs 12.52, all-cross)，差异 <2%——这是 P6–P16 trace 反复切换两条 main 首位的根因。

### 表 D.3 — 固定 W × H = 800 × 550 nm（Tsuyama 论文 depth）

| λ (nm) | source type | Csca× | \|E_sca\|× | \|A_ref\|× | cross-term× | self-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | blocker / role | note |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 404 | strict 物理 | 7.10 | 2.66 | ≈ 0.97 (浅通道接近 baseline) | ≈ 2.6 | 7.10 | ≈ 2.1 | 1.0 | 5.48 | — | transit / gating mismatch | 此 cell 无 strict 直接行；同 W × H 下 404 nm 未在 v5.x 跑 |
| 488 | strict 物理 | 3.34 | 1.83 | ≈ 1.00 | ≈ 1.83 | 3.34 | ≈ 1.4–1.6 | 1.0 | 6.61 | — | 接近 main 方向 | 同上；口径 B 在此波长 / 几何对 Au panel 未直接覆盖 |
| 532 | strict 物理 + 口径 B note | 2.37 | 1.54 | ≈ 1.00 | ≈ 1.54 | 2.37 | ≈ 1.2–1.4 | 1.0 | 7.21 | — | EV 口径无 strict；口径 B 仅给 raw Au exponent | 口径 B raw Au exponent = 3.1563 (532 / 800 × 550 D2.1 best)；§11.2.3 case-level decomposition |
| 660 | **strict 直接行** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 8.94 | **47.15** (NODI engineering lens) | paper-sanity / cross-check | §6.4 表 6.4.B 直接行；2020 paper lens proxy = 43.50%、2022 NODI paper lens proxy = 46.70%（不同 lens，详见 §6.4 表 6.4.B；不在此 cell 内做跨 lens 比较）|

> **takeaway D.3**：800 × 550 nm 是 Tsuyama 论文 depth；660 nm 在 3 个 lens 下都给出高 detection proxy (43.5–47.2%)，但**这是 NODI lens / paper lens**，不是 all-crossing；不能与 D.1 / D.2 中 12.52% / 12.70% 直接比较（§4.5）。

### 表 D.4 — 固定 W × H = 600 × 1300 nm（404 nm shortwave probe 几何）

| λ (nm) | source type | Csca× | \|E_sca\|× | \|A_ref\|× | cross-term× | self-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | blocker / role | note |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| **404** | **strict 直接行** | 7.10 | 2.66 | ≈ 0.95 | ≈ 2.5 | 7.10 | ≈ 2.0 | 1.0 | 5.48 | **4.45** (shortwave probe class avg) | shortwave_probe_only；transit↓ + phase flip↑ | §6.4 表 6.4.A `probe_404_W600_D1300` |
| 488 | strict 物理 | 3.34 | 1.83 | ≈ 1.00 | ≈ 1.83 | 3.34 | ≈ 1.4–1.6 | 1.0 | 6.61 | — | 中等 transit | 此 cell 无直接行 |
| 532 | strict 物理 | 2.37 | 1.54 | ≈ 1.00 | ≈ 1.54 | 2.37 | ≈ 1.2–1.4 | 1.0 | 7.21 | — | 接近 main | 此 cell 无直接行 |
| 660 | strict 物理 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 8.94 | — | route-level evidence 中 600 × 1300 仅在 404 nm 下作为 shortwave probe 评估 | 此 cell 无直接行 |

> **takeaway D.4**：这是 shortwave probe 的"原产几何"——v5.x 报告里 600 × 1300 仅在 404 nm 下被作为 probe 评估；其他波长在此几何下无 strict 直接行。这条 route 一致排第 3（§5.3 P6–P16 trace），是 §10.6 候选裁决"why not 404"的直接证据。

### 表 D.5 — 固定 W × H = 500 × 1500 nm（口径 A 数字最高的 context route）

| λ (nm) | source type | Csca× | \|E_sca\|× | \|A_ref\|× | cross-term× | self-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | blocker / role | note |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 404 | strict 物理 | 7.10 | 2.66 | ≈ 0.91–0.95 | ≈ 2.4–2.5 | 7.10 | ≈ 1.9–2.0 | 1.0 | 5.48 | — | 此 cell 无直接行 | route-level 最近邻 4.45% (不同 W) |
| 488 | strict 物理 | 3.34 | 1.83 | ≈ 1.00 | ≈ 1.83 | 3.34 | ≈ 1.4–1.6 | 1.0 | 6.61 | — | 同上 | — |
| 532 | strict 物理 | 2.37 | 1.54 | ≈ 1.00 | ≈ 1.54 | 2.37 | ≈ 1.2–1.4 | 1.0 | 7.21 | — | 同上 | — |
| **660** | **strict 直接行** | 1.00 | 1.00 | 1.00 (相对 660/800×550 baseline 偏离 reference 谱形) | 1.00 | 1.00 | 1.00 | 1.00 | 8.94 | **19.64** (all-cross 8-scen avg, ratio_vs_main 1.557) | **context, surrogate_sensitive_not_promoted** | §12.2 R5.2 audit；窄通道工程风险被低估 (§10.4 width-prior) |

> **takeaway D.5**：660 nm 在此几何下 detection 19.64% 是口径 A all-crossing 表里数字最高，但**被治理裁决降级**（§10.4 width-prior + §10.6 多候选裁决）；不是 main route。404 / 488 / 532 在此几何下无直接行。

---

## 附录 E：固定 λ 看 W × H（5 组 derived reader tables）

> **说明**：本附录与附录 D 镜像。固定 λ + 固定颗粒 panel 时，**Csca 是常数**（颗粒固有；§3.0a 已强调），所以倍数列**不再有 Csca×**——变化的是 |A_ref| / cross-term / route gating。

### 表 E.1 — 固定 λ = 660 nm + H = 1400 nm，vary W（口径 A all-crossing + EV biomimetic）

| W × H (nm) | source type | Csca status | \|A_ref\|× | cross-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | route role | blocker |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 500 × 1400 | strict 直接行 | constant for same particle panel | 偏离 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 18.97 | context, surrogate_sensitive_not_promoted | geometry outside preferred + width-prior |
| 600 × 1400 | qualitative only (无直接行) | 同 | 接近 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | — (此 W 在 H=1400 v5.x 未直接覆盖) | 推断属于 context | — |
| 700 × 1400 | qualitative only | 同 | 接近 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | — | 推断接近 weak-ref | — |
| **800 × 1400 (main)** | strict 直接行 | 同 | 1.0 baseline | 1.0 | 1.0 | 1.0 | 8.94 | **12.52** | **conditional_relative_main** | — |
| 900 × 1400 | strict 直接行 | 同 | 接近 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 12.30 | optional_robustness_probe_only | — (probe, no main blocker) |

### 表 E.2 — 固定 λ = 660 nm + H = 1500 nm，vary W

| W × H (nm) | source type | Csca status | \|A_ref\|× | cross-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | route role | blocker |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 500 × 1500 | strict 直接行 | constant for same particle panel | 偏离 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 19.64 | context, surrogate_sensitive_not_promoted | width-prior + route gov |
| 600 × 1500 | strict 直接行 | 同 | 接近 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 16.55 | context, surrogate_sensitive_not_promoted | 同上 |
| 700 × 1500 | strict 直接行 | 同 | 偏低 (reference too weak) | < 1.0 | < 1.0 | 1.0 | 8.94 | 15.23 | weak_reference_control_only | reference too weak |
| **800 × 1500 (main)** | strict 直接行 | 同 | 1.0 baseline | 1.0 | 1.0 | 1.0 | 8.94 | **12.70** | **conditional_relative_main** | — |
| 900 × 1500 | qualitative only | 同 | 接近 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | — | 此 W 在 H=1500 v5.x 未直接覆盖 | — |

### 表 E.3 — 固定 λ = 660 nm + W = 800 nm，vary H

| W × H (nm) | source type | Csca status | \|A_ref\|× | cross-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | route role | blocker |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 800 × 550 | strict 直接行（NODI engineering lens；其他 lens 见 note）| constant for same particle panel | ≈ 1.0 (≈ baseline 几何)| 1.0 | 1.0 | 1.0 | 8.94 | 47.15 (NODI engineering lens) | paper-sanity / cross-check | 2020 paper lens proxy = 43.50%、2022 NODI paper lens proxy = 46.70%（不在此 cell 内并列；详 §6.4 表 6.4.B）；all-cross 此 H 未直接覆盖 |
| 800 × 1200 | qualitative only | 同 | 接近 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | — | 此 H 在 W=800 v5.x 未直接覆盖 | — |
| **800 × 1400 (main)** | strict 直接行 | 同 | 1.0 baseline | 1.0 | 1.0 | 1.0 | 8.94 | **12.52** (all-cross) | **conditional_relative_main** | NODI engineering lens proxy = 45.15%（不在此 cell 内并列；详 §6.4 表 6.4.B；不同 lens 不可与 12.52 直接比较）|
| **800 × 1500 (main)** | strict 直接行 | 同 | ≈ 1.0 | 1.0 | 1.0 | 1.0 | 8.94 | **12.70** (all-cross) | **conditional_relative_main** | NODI engineering lens 此 H 未直接覆盖 |

### 表 E.4 — 固定 λ = 660 nm + W = 500 nm，vary H

| W × H (nm) | source type | Csca status | \|A_ref\|× | cross-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | route role | blocker |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 500 × 1200 | strict 直接行 | constant | 偏离 baseline | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 17.39 | context, surrogate_sensitive_not_promoted | width-prior |
| 500 × 1300 | strict 直接行 | 同 | 同上 | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 18.26 | context, surrogate_sensitive_not_promoted | 同 |
| 500 × 1400 | strict 直接行 | 同 | 同上 | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 18.97 | context, surrogate_sensitive_not_promoted | 同 |
| 500 × 1500 | strict 直接行 | 同 | 同上 | ≈ 1.0 | ≈ 1.0 | 1.0 | 8.94 | 19.64 | context, surrogate_sensitive_not_promoted | 同 |

> **takeaway E.4**：W=500 nm 跨 H 4 个直接行的 detection 单调上升（17.39 → 19.64），方向与 H 增大相同；但**4 行全部被治理裁决降级**为 surrogate_sensitive_not_promoted。这条是 §10.4 width-prior + §10.6 多候选裁决"窄通道高 score 但不晋升"的最强直接证据。

### 表 E.5 — 固定 λ = 404 nm representative geometry sweep

| W × H (nm) | source type | Csca status | \|A_ref\|× | cross-term× | peak× | noise× | transit (ms) | synthetic detection score (%) | route role | blocker |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 500 × 800 | strict 直接行 (NODI engineering lens；其他 lens 见 note) | constant for same particle panel | ≈ 0.97 (浅通道) | ≈ 2.6 (相对 660 同 W × H baseline) | ≈ 2.0 | 1.0 | 5.48 | 33.65 (NODI engineering lens) | 短波 lens cross-check | 2020 paper lens proxy = 34.50%、2022 NODI paper lens proxy = 35.40%（不在此 cell 内并列；详 §6.4 表 6.4.B）；transit / gating mismatch |
| 600 × 1300 | strict 直接行 (口径 A all-cross) | 同 | ≈ 0.95 | ≈ 2.5 | ≈ 2.0 | 1.0 | 5.48 | 4.45 (shortwave probe class avg) | **shortwave_probe_only** | transit + phase flip |
| 800 × 1400 | qualitative only | 同 | ≈ 0.95 | ≈ 2.5 | ≈ 2.0 | 1.0 | 5.48 | — | 此 cell 无直接行 | — |

> **takeaway E.5**：404 nm 仅 2 个几何有 strict 直接行（500 × 800 在多 lens 下 33–35%；600 × 1300 在 all-cross 4.45%）；**lens 切换让同 panel 同 λ 下数字差到 30 pp 以上**——这是 §4.5 / §7.4 禁止跨 lens 比较的直接证据。404 nm 在 800 × 1400 / 1500 main 几何上**没有 strict 直接行**。

---

## 附录 F：Strict controlled vs route-level 对照矩阵（防误读总表）

> **本附录是 v5.2 最重要的防误读表**。读者打开任意一张 §6 / §7 / §10 / §11 / 附录 D / E 的表时，回到本表确认"这张比较是 strict controlled 还是 route-level evidence"，就能避免把 route-level evidence 当 strict 比较读。

| comparison | strict controlled? | what is fixed | what varies | detection 列可比？ | conclusion 允许的范围 |
|---|---|---|---|---|---|
| §2.4 块 A 4 波长机制链（Csca / E_sca / A_ref / peak / noise / transit）| ✅ 是 | particle panel + W × H + lens | λ | ✅ 同 baseline 同 panel 可比 | 物理推导 / 方向性结论；**不可**反推 detection 倍数 |
| §2.4 块 B route-level evidence | ❌ 否 | 不同 route class，几何与 panel 也不一致 | λ + 几何同时变 | ❌ 仅作方向参考 | "660 整体优于其他波长"方向性结论；**不可** "404 nm 在 X% detection" |
| §6.4 表 6.4.A 内不同 (λ, W, H) 路线 | ⚠️ 同 lens（all-crossing 8-scen avg）但跨几何 | lens 一致 | (λ, W, H) 同时变 | ✅ 同 lens 内相对排序可读 | 路线排序可比；**不可**单独归因 λ 或几何 |
| §6.4 表 6.4.B 4 几何 × 3 lens | ⚠️ 同 panel + 同 8-scen，但跨 lens | panel 一致 | 几何 + lens 同时变 | ❌ 跨 lens 不直接可比 | 同 lens 内方向；**不可**跨 lens 数字比 |
| §6.4 表 6.4.C 跨 4 几何 mean (Au panel)| ⚠️ 同 panel + 同 lens，几何已聚合 | panel + lens | λ + (4 几何 mean) | ✅ 仅相对方向 | "Au 660 > 532 > 488"方向；**不可** geometry breakdown |
| §6.4 表 6.4.D Au 粒径阶梯 (660/800×500)| ✅ 严格 | λ + W × H + lens 全部固定 | Au 粒径 | ✅ 直接可比 | Au 粒径响应方向 + 阈值 / 饱和效应；属于强证据 |
| §6.4 表 6.4.E 660 nm 读出方式 (60 cases)| ✅ 严格 | λ + 60 case mix 固定 | readout mode | ✅ pass/fail 与 mean 分别可读 | 读出方式对 pass/fail 边界与 mean 的不同影响 |
| §6.4 表 6.4.F 4 波长信号链汇总 (800×1400 同 W×H)| ⚠️ 阶段量 strict / detection route-level | W × H + panel | λ | 阶段量 ✅ ；detection 仅 source type 标为 strict 直接行的 cell 可读 | 阶段量方向；detection 不可由 route-level note 外推 |
| §7.2.5a.1 信号链扩列 (800×1400 vary λ)| 同上 | 同上 | 同上 | 同上 | 同上 |
| §7.2.5a.2 信号链扩列 (660 nm + H=1500 vary W)| ✅ 严格（同 λ + 同 panel + 同 lens）| λ + panel + lens (all-cross) | W | ✅ 直接可比 | W 影响方向 + 治理裁决；属于 strict |
| §10.6 多候选裁决表 | ⚠️ 拆 2 lens 列后同 lens 可比；跨候选 (λ, W, H) 不同 | lens (拆列后)；其余共享 v5.x 已发布数据口径 | candidate (含 λ, W, H) | 同 lens 列内可读相对排序；跨 lens 列不可直接乘 | 多条件裁决；**不可**单一指标 ranking |
| §11.2.3 口径 B raw Au peak-height exponent | ✅ 严格 | calibration parameter set + selected-annulus + Au panel + lens | (λ, W × H) 几何对比 | ✅ residual 排序可读 | step 1 校准 lens 内 residual 排名 |
| 附录 D.1–D.5 各表 | 阶段量 ✅；detection 列只在 source type 标为 strict 直接行的 cell 填数 | W × H + panel | λ | 阶段量 ✅；detection 仅 strict 直接行 cell 可读 | 同 §6.4.F；例如 D.4 的 404/600×1300 也是 strict 直接行 |
| 附录 E.1–E.5 各表 | 同 λ + 同 panel 时阶段量 ✅；具体 (W, H) detection 严格性见每行 source type 列 | λ + panel | (W, H) | 同 lens 列内可比 | 同 §10.6 |
| 跨 panel 比较 (EV biomimetic vs Au paper-audit) | ❌ 否 | — | panel + (通常)lens 同时变 | ❌ 直接百分比 ranking 禁止（§4.5） | 仅 "Csca 方向反转"等定性影响（§9 排名 1 修正后立场） |

> **总规则（§7.0 + 附录 F 共同）**：任何不在本表 strict controlled = ✅ 行内的比较，**只能**做方向性 / 定性结论，**不能**做百分比 ranking 或量化外推。

> **takeaway 附录 F**：v5.x 报告里读者会看到的所有 detection / 阶段量比较表都可以归到本表 14 行之一。读到具体数字时先回本表确认 "strict controlled? ✅ / ⚠️ / ❌"——这是 v5.2 reader comparison pack 的最关键防误读机制。

---

（v5.2 报告主体结束。v5.1.1 hotfix + v5.2 reader comparison pack 完整验收映射见 §18.4 + §18.6；不变量见 §18.3 + §18.5；下一步硬依赖见 §16。）
