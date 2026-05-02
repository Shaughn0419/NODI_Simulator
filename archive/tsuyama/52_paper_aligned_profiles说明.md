# paper_aligned profiles 说明

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 日期：2026-04-15  
> 目的：把 `paper_aligned` 从一个单一开关，升级成按论文分层的 profile 配置层。

---

## 1. 为什么要拆成 profiles

Tsuyama / Mawatari 这组论文不是“一篇新论文把前一篇全部替代”的关系，而是分层迭代：

- `2020 diffraction`：基础 diffraction / width-depth / phase-filter 语义
- `2022 NODI`：单颗粒 interferometric scattering 检测与 pulse 特征
- `2024 POD+NODI`：双频率、双通道、paired classification
- `2019 / 2020 POD`：thermal-POD / solvent-enhanced POD 支线

因此：

> **一个总的 `paper_aligned` 开关，本来就不足以同时代表全部论文。**

更合理的做法是：

- 为不同论文层建立不同的 profile
- 每个 profile 只对齐它真正能约束的实现层

---

## 2. 当前已实现的 profile

代码入口：

- `paper_aligned_profiles.py`

当前 profile 列表：

- `diffraction_2020`
- `nodi_2022`
- `paired_2024`
- `pod_2019_2020`（占位，当前不可用）

---

## 3. 各 profile 的作用

## 3.1 `diffraction_2020`

作用：

- 审查 Tsuyama 2020 里 `2l / d` 的 width-depth 语义
- 对照当前 reference 模型是否把 depth 误当成第二孔径维度

主要设置：

- `reference_model = paper_aligned_phase_filter`
- `illumination_mode = overfill`
- 保持 operator-level collection surrogate

注意：

- 这是一个 **reference / diffraction 审查 profile**
- 不是完整事件级 NODI/POD validation profile

## 3.2 `nodi_2022`

作用：

- 审查 Tsuyama 2022 NODI 单通道检测语义

主要设置：

- `reference_model = paper_aligned_phase_filter`
- `illumination_mode = overfill`
- `readout_observable_mode = magnitude`
- `pulse_detection_mode = positive`
- `lockin_time_constant_s = 1 ms`
- `nodi_lockin_frequency_Hz = 3 kHz`
- `detection_decision_mode = single_channel`
- `engineering_decision_basis = single_channel`
- `engineering_max_phase_flip_fraction = 1.0`

这代表的逻辑是：

- 更接近论文里的 pulse height / width / maximum signal value
- 不再把 `phase_flip_fraction` 当成 paper-aligned 的主 reject criterion

## 3.3 `paired_2024`

作用：

- 审查 Tsuyama 2024 paired POD/NODI 语义

主要设置：

- `reference_model = paper_aligned_phase_filter`
- `illumination_mode = overfill`
- `readout_observable_mode = magnitude`
- `pulse_detection_mode = positive`
- `lockin_time_constant_s = 1 ms`
- `pod_lockin_frequency_Hz = 4.1 kHz`
- `nodi_lockin_frequency_Hz = 1.2 kHz`
- `detection_decision_mode = paired_channel`
- `engineering_decision_basis = paired_channel`
- `pulse_pairing_tolerance_s = 50 ms`
- `engineering_max_phase_flip_fraction = 1.0`

这代表的逻辑是：

- paired extraction
- 更贴近论文里的 frequency split 与 second-pulse pairing
- 仍然不是完整 electronics / thermal-POD 复现

## 3.4 `pod_2019_2020`

状态：

- 当前仅作为占位 profile

原因：

- 这部分真正要求的是 thermal source、substrate diffusion、solvent `dn/dT`、PD optimum
- 当前工程尚未实现足够 paper-aligned 的 POD thermal 物理层

所以不能假装它已经可用。

---

## 4. 当前最重要的边界

### 可以说的

- 当前已经有 `2020 diffraction` 的 reference core 对照模式
- 当前已经有 `2022 NODI` / `2024 paired` 的 paper-aligned 配置入口
- 可以用这些 profile 做定向 probe 和 profile-level 比较

### 不能说的

- 不能说“paper_aligned 已经符合全部 6 篇论文”
- 不能说 `paired_2024` 已经等价于 2024 论文的完整系统
- 不能说 `pod_2019_2020` 已经实现

---

## 5. 输出文件

profile probe 工具：

- `tools/run_paper_aligned_profile_probes.py`

结果文件：

- `results/paper_aligned_profile_probe_cases.csv`
- `results/paper_aligned_profile_probe_summary.json`

这些文件的作用是：

- 对比 `current_dashboard_replay`
- 对比 `diffraction_2020`
- 对比 `nodi_2022`
- 对比 `paired_2024`

从而把“paper-aligned 配置是否改变结论”变成可追踪的结果，而不是口头判断。

### 当前 probe 的一句话结论

当前 `10` 个代表性 case 的 probe 结果表明：

- `diffraction_2020` 主要改变的是 reference 语义，平均 `A_ref` 略高于 current mainline
- `nodi_2022` 主要改变的是 readout / observable / gate 语义，`phase_flip_fraction` 会被压成诊断项
- `paired_2024` 进一步把 paired-channel 决策和 `4.1/1.2 kHz` 分频语义收紧，因此对部分 case 的 detection/stable 会更保守

在当前 probe summary 中：

- `current_dashboard_replay` 平均 detection 约 `0.9706`
- `diffraction_2020` 平均 detection 约 `0.9654`
- `nodi_2022` 平均 detection 约 `0.9672`
- `paired_2024` 平均 detection 约 `0.9578`

这说明：

> **profile 化以后，结论会发生语义上的收紧，但当前 probe 还没有显示出“推荐整体翻盘”的证据。**

---

## 6. 建议的使用方式

### 6.1 审 reference / width-depth

优先用：

- `diffraction_2020`

### 6.2 审单颗粒 NODI detectability

优先用：

- `nodi_2022`

### 6.3 审 paired POD/NODI 分类与双通道判决

优先用：

- `paired_2024`

### 6.4 审 thermal-POD 本身

当前：

- 不应声称已有 paper-aligned profile

---

## 7. 最后一句话

> **现在的正确方向，不是继续增强一个总的 `paper_aligned` 开关，而是维持一组按论文分层的 paper-aligned profiles。**
