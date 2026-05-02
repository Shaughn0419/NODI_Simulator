# Tsuyama paper_aligned 全论文闭环审查

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 日期：2026-04-15  
> 目的：回答一个比“读过论文”更严格的问题：  
> **当前工程里的 `paper_aligned`，是否已经在逻辑无误的前提下，对齐了工程内全部 6 篇 Tsuyama / Mawatari 论文的公式推导过程与观测语义？**

---

## 1. 直接结论

最严格的答案是：

> **还没有。**

但这不是因为“什么都没对齐”，而是因为：

1. 这 6 篇论文研究的对象并不完全相同
2. 它们约束的实现层也不完全相同
3. 因此一个单一的 `paper_aligned` 开关，本来就不足以同时代表全部论文

更准确地说：

- **`2020 diffraction` 的 reference / width-depth 语义**：已经开始进入 `paper_aligned_phase_filter`
- **`2022 NODI` 与 `2024 paired POD/NODI` 的 illumination / collection / readout 语义**：已经有一部分在 current mainline 中，另一部分仍未被统一吸收到 `paper_aligned`
- **`2019 POD`、`2020 counting POD`、`2020 solvent-enhanced POD` 的热扩散 / photothermal source / solvent factor / PD optimum`**：当前工程还没有一个足够严谨的 POD paper-aligned 实现

所以现在最诚实的说法不是：

> “paper_aligned 已经符合所有论文”

而是：

> “paper_aligned 现在只完成了其中一部分，且最主要的是 `2020 diffraction` 的 depth 语义对照；  
> 如果要对齐全部论文，必须拆成多个 paper-aligned profiles。”

---

## 2. 六篇论文分别约束什么

| 论文 | 主对象 | 最能约束的层 | 能否直接约束当前 exosome/NODI 主线 |
| --- | --- | --- | --- |
| 2019 POD | photothermal optical diffraction, 分子检测 | blank diffraction、diffracted region、substrate heat contribution | 只能间接约束，不直接约束 exosome NODI |
| 2020 diffraction | 单 nanochannel diffraction 理论与实验 | width / depth / solvent / focus position 对 diffracted light 的影响 | **直接约束 reference / diffraction 语义** |
| 2020 counting POD | counting-mode POD，Au NP | flow/transit、beam-over-channel、counting threshold | 主要约束 POD 支线，不直接约束 NODI detectability |
| 2020 solvent-enhanced POD | solvent-enhanced POD | photothermal factor、diffraction factor、PD optimum、sign flip | 主要约束 POD 支线 |
| 2022 NODI | 单颗粒 interferometric scattering | diffracted-light region、20x/0.45、0.9、1–2 ms、pulse height/width、size scaling | **直接约束 NODI 主线** |
| 2024 POD+NODI | paired absorption + scattering | dual-frequency extraction、1.2/4.1 kHz、paired pulse matching、maximum signal value | **直接约束 paired readout 语义** |

---

## 3. 按模块看：当前已经对齐了什么

## 3.1 illumination

### 论文约束

- `2022 NODI`：
  - illumination objective `20x, NA = 0.45`
  - calculated spot size `~2 μm`
  - channel width `800/1200 nm`
  - 结论：对 `x/z` 横截面基本是 overfill

- `2024 POD+NODI`：
  - probe 与 excitation 都走 `20x, NA = 0.45`
  - 通道宽 `800–1200 nm`
  - 结论同样支持 beam spot `>>` channel

### 当前工程状态

- `illumination.py` 里 `overfill` 现在已经明确解释成：
  - `x/z` 近似均匀
  - `y` 保留有限 transit window

### 审查结论

- **部分符合，且基本合理**
- 这层已经足够接近 `2022/2024` 的实验语义
- 不需要因为此次审查立刻重写

---

## 3.2 collection / slit / pinhole

### 论文约束

- `2019 POD`、`2020 diffraction`、`2022 NODI`、`2024 POD+NODI` 都强调：
  - 检测发生在 **diffracted-light region**
  - slit 用于切掉 transmitted region
  - pinhole 作为收集限制

### 当前工程状态

- `build_collection_operator` 里当前使用的是
  - `pupil_slit_surrogate`
  - 有 `theta` 与 `phi` 的最小二维 operator
  - 含 slit / pinhole 的 surrogate throughput

### 审查结论

- **语义上部分符合**
- 但这是 **operator-level surrogate**
- 不是论文中显式写出的闭式公式实现

所以：

- 可以说“遵循了论文的收集语义”
- 不能说“已逐式复现论文的 collection optics”

---

## 3.3 reference / diffraction

### 论文约束

最强约束来自 `2020 diffraction`：

- width = `2l`
- depth = `d`
- `d` 通过

  \[
  \theta = 2\pi (n_s - n_g) d / \lambda
  \]

  进入 phase filter

- 论文原式里没有和当前

  \[
  \mathrm{sinc}(H k_z / 2\pi)
  \]

  完全等价的 depth aperture 项

### 当前工程状态

- mainline `channel_angular_surrogate`：
  - `H` 进入 phase delay
  - `H` 也进入 `depth_term = sinc(H·k_z/2π)`

- 新增 `paper_aligned_phase_filter`：
  - 保留 depth 的 phase delay
  - 去掉 depth aperture 项
  - 去掉额外 width/depth 连续相位修饰
  - 去掉 width soft-cutoff

### 审查结论

- **这层目前是本轮最明确已收紧的部分**
- 但它只完成了 `2020 diffraction` 的核心语义对照
- 还不能代表“全部论文都已对齐”

---

## 3.4 transport / transit / diffusion

### 论文约束

- `2020 counting POD`：
  - `100 kPa -> 0.17 mm/s`
  - transit `~10 ms`

- `2022 NODI` / `2024 POD+NODI`：
  - `100 kPa -> 0.2 mm/s`
  - transit `~10 ms`
  - `2024` 还强调：
    - 10 ms 内 diffusion length 与 channel size 同量级
    - Brownian motion 会缓解 positional fluctuation

### 当前工程状态

- 当前主线已有：
  - `mean_flow_velocity = 0.2 mm/s`
  - `overfill` 下有限 `y` transit window
  - `rect_series + diffusion + anisotropic_tensor_surrogate`

- 但还没有：
  - 真正 paper-aligned 的 crossing-conditioned event-flux transport

### 审查结论

- **部分符合**
- 量级与语义基本对上了
- 但 transport 仍然是 surrogate，不是论文级精确重建

---

## 3.5 readout / observable

### 论文约束

这里要分开看。

#### 2022 NODI

- 关心的是：
  - pulse height
  - pulse width
  - average signal intensity
  - maximum signal value

- 论文没有把 `phase_flip_fraction` 作为 reject criterion

#### 2024 paired POD/NODI

- 关心的是：
  - 4.1 kHz synchronized POD component
  - 1.2 kHz nonsynchronized NODI component
  - paired pulse height / width
  - leakage 与 purity

#### 2020 counting POD / 2020 solvent-enhanced POD

- 更接近 photothermal lock-in signal
- 关心的是 peak intensity、S/N、PD optimum、modulation frequency optimum

### 当前工程状态

- 当前主线默认还是：
  - `readout_observable_mode = "in_phase"`
  - 再加 engineering gate 的 `phase_flip_fraction`

- 只有 `Tsuyama gold validation` 支线，已经显式切到：
  - `paper_aligned` profile
  - `readout_observable_mode = "magnitude"`
  - `engineering_max_phase_flip_fraction = 1.0`

### 审查结论

- **这层是目前最大的未闭环项之一**

也就是说：

- 如果问题是“当前工程里有没有一个对全部 Tsuyama 论文都成立的 paper_aligned readout？”
  - **没有**

- 如果问题是“我们有没有开始把 paper-aligned readout 做出来？”
  - **有，但只在 Tsuyama gold validation 支线里做了 scoped fix**

---

## 3.6 gate / decision

### 论文约束

Tsuyama 论文里真正出现的是：

- threshold at background + `5σ` 或 `7–10σ`
- minimum pulse width
- paired pulse extraction窗口
- count / peak height / width / SVM 分类

而不是：

- `stable_detection_rate >= 0.2`
- `phase_flip_fraction <= 0.5`
- `mean_peak_margin_z >= 0.5`

这类工程 gate。

### 当前工程状态

- 当前主线 gate 是工程筛选规则
- 并不是论文原文决策规则

### 审查结论

- **当前 engineering gate 绝不能被叫做 paper-aligned gate**
- 最多只能说：
  - 它是在论文实验语义之上叠加的工程筛选层

---

## 3.7 POD thermal model

### 论文约束

`2019 POD`、`2020 counting POD`、`2020 solvent-enhanced POD` 都明确要求：

- photothermal source term
- thermal diffusion
- substrate contribution
- `dn/dT`
- solvent-dependent sign / magnitude
- `PD` optimum

### 当前工程状态

- current model 只有：
  - frequency separation
  - leakage surrogate
  - paired extraction surrogate

- 没有：
  - explicit thermal source
  - explicit solvent `dn/dT`
  - explicit substrate heat diffusion model
  - explicit `PD optimum`

### 审查结论

- **这一层当前不能被称为 POD paper-aligned**
- 如果用户要求“符合全部论文推导过程”，那么这部分现在仍然明显缺失

---

## 4. 这次审查后，最重要的新结论

### 4.1 一个 `paper_aligned` 开关不够

最重要的结论就是这个：

> **从逻辑上讲，一个单一的 `paper_aligned` 开关，本来就不足以同时代表全部 6 篇论文。**

原因是：

- `2020 diffraction` 约束的是 reference / width-depth 语义
- `2022 NODI` 约束的是 scattering readout / pulse feature / dual wavelength
- `2024 paired POD/NODI` 约束的是 dual-frequency extraction / paired classification
- `2019/2020 POD` 三篇约束的是 thermal-POD 语义

这四类东西不是同一个层。

### 4.2 更合理的做法是：paper-aligned profiles

如果要继续做对，我建议正式拆成下面这些 profile：

#### `paper_aligned_diffraction_2020`

用于：

- 审查 `2l / d`
- blank diffraction
- width/depth dependence

核心：

- `reference_model = paper_aligned_phase_filter`
- 不谈 engineering gate
- 不强行带入 paired POD/NODI

#### `paper_aligned_nodi_2022`

用于：

- 单通道 NODI detection/classification

核心：

- `reference_model = paper_aligned_phase_filter`
- `illumination_mode = overfill`
- `NA_collection = 0.9`
- `lockin_time_constant = 1–2 ms`
- readout 更接近 `maximum signal value / magnitude / absolute peak`
- `phase_flip_fraction` 不作为主 reject criterion

#### `paper_aligned_paired_2024`

用于：

- paired POD/NODI
- 4.1 / 1.2 kHz 分频提取
- paired pulse matching

核心：

- 两通道频率设定贴近论文
- paired window / minimum width 对齐论文
- readout 以 pulse height/width 为主

#### `paper_aligned_pod_2019_2020`

用于：

- POD 分子/纳米粒子支线

核心要求：

- thermal source
- substrate heat diffusion
- solvent factor / `dn/dT`
- `PD` optimum

而这层 **当前还不能实现为真正 paper-aligned**

---

## 5. 当前完成度表

| 组件 | 当前状态 | 是否足以叫做“全部论文已对齐” |
| --- | --- | --- |
| `paper_aligned_phase_filter` reference | 已实现 | 否，只覆盖 `2020 diffraction` 核心 depth 语义 |
| overfill illumination / NA split | 已实现 | 否，只覆盖 `2022/2024` 的一部分 |
| Tsuyama gold magnitude/no-phase-gate validation | 已实现支线 | 否，只是 scoped validation fix |
| paired frequency extraction surrogate | 已有 | 否，仍非完整 2024 electronics 复现 |
| transport / diffusion | 部分符合 | 否，仍是 surrogate |
| engineering gate | 非论文原始 gate | 否 |
| POD thermal model | 未闭环 | 否 |

因此现在最严格的总体结论是：

> **我们已经开始把 paper-aligned 拆成正确方向，但距离“符合全部论文的所有公式推导过程”还明显没有完成。**

### 5.1 当前已经真正落进代码的部分

目前已经落进代码并可复跑的有：

- `paper_aligned_phase_filter` reference mode
- `paper_aligned_profiles.py`
  - `diffraction_2020`
  - `nodi_2022`
  - `paired_2024`
  - `pod_2019_2020`（占位，不可用）
- `tools/run_paper_aligned_profile_probes.py`
- `results/paper_aligned_profile_probe_cases.csv`
- `results/paper_aligned_profile_probe_summary.json`

也就是说，我们现在不再只有“解释上的 profile 设计”，而是已经有了：

- profile 定义
- profile 应用函数
- profile probe 工具
- 结果文件

但这仍然不等于“全部论文已经完全闭环”。

---

## 6. 下一步最合理的执行顺序

### 第一步

保留当前已经实现的：

- `paper_aligned_phase_filter`

作为：

- `paper_aligned_diffraction_2020` 的 reference core

### 第二步

把 `paper_aligned_nodi_2022` 收成一个显式 profile，至少包括：

- reference
- illumination
- collection
- readout observable
- gate exclusion项

### 第三步

把 `paper_aligned_paired_2024` 单独做成 paired validation profile

### 第四步

如果真的要覆盖全部 6 篇论文，再决定是否单独立项做：

- `paper_aligned_pod_2019_2020`

因为这一步已经不是小修，而是要补 thermal-POD 物理层。

---

## 7. 最后一句话

> **现在还不能说“paper_aligned 已经符合全部 Tsuyama 论文”。  
> 更准确的说法是：我们已经把最关键的 `2020 diffraction` depth 语义对照落进代码，并确认了其影响量级；下一步必须把 paper_aligned 从单个开关升级成按论文分层的 profiles，才能继续向“全论文闭环”靠近。**
