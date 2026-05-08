# Tsuyama 固定条件对标与结果表

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 日期：2026-04-17  
> 目的：回答“Tsuyama 论文里哪些图表 / 数据 / 结论可以和当前工程结果对标；在固定 Tsuyama 条件后，两边的结论或数据是否趋同”。  
> 口径：优先使用本地 `paper_aligned` / `Tsuyama-like validation` 结果文件，不把 engineering mainline 和 paper-aligned lane 混成一个结论。

## 1. 结论先行

可以对标，而且当前最有力的对标对象主要有三类：

1. **2020 diffraction**：可直接对标 `reference / diffraction` 机制与 width/depth 趋势。  
2. **2022 NODI**：可直接对标单通道 NODI 的 `波长主次、几何偏好、detectability / pulse` 趋势。  
3. **2022/2024 gold lane**：可直接对标 `gold 小粒径检测趋势` 与 `readout semantics` 对结论的影响。  

但也有明确不能硬说“已经对齐”的部分：

1. **2019 POD / 2020 POD thermal 支线**：当前没有完整 thermal-POD source / substrate diffusion / solvent `dn/dT`，不能做严格 paper-aligned 定量对标。  
2. **2022 / 2024 论文里的最终 SVM 准确率数值**：当前还没有完全同构的数据集、特征工程和分类协议，不能把工程结果直接说成复现了论文准确率。  

## 2. 可对标性地图

| 论文 / 图表或结论 | 论文固定条件 | 当前可用对标 lane | 可对标级别 | 当前判断 |
| --- | --- | --- | --- | --- |
| **2020 diffraction** `Fig.3 / Fig.5 / Fig.9` | `633 nm`, illumination `20x, NA=0.45`, collection `NA=0.9`, `1.1 kHz`, `tau = 1 s` | `diffraction_2020` profile + `reference_depth_semantics_*` | **直接机制对标** | **趋同**：width/depth 会显著改写 reference field，且参考场变化会传到 signal / peak |
| **2022 NODI** `Fig.4 / Fig.6 / Fig.7` | overfill-like spot, collection `NA=0.9`, slit `1 mm`, pinhole `400 μm`, `tau = 1–2 ms`, `100 kPa -> 0.2 mm/s`, channel 近 `800 × 550 nm` | `nodi_2022` profile + `paper_aligned_nodi2022_targeted_grid_*` | **直接趋势对标** | **趋同**：`660` 仍为主波长；最佳几何向论文器件附近收缩 |
| **2024 POD+NODI** `Fig.3 / Fig.4 / Fig.5` | probe `660 nm`, excitation `532 nm`, `tau = 1–2 ms`, `1.2 / 4.1 kHz`, width `800–1200 nm`, depth `~550 nm` | `paired_2024` profile probe + Tsuyama-like gold validation | **部分直接对标** | **部分趋同**：paired readout / frequency split 的语义同向，但还不是完整 electronics / thermal 复现 |
| **2022/2024 gold small-particle lane** | 小 Au NP、ms lock-in、窄浅通道 | `tsuyama_gold_validation_tau1ms_1000e_*` | **直接趋势对标** | **趋同**：`660 > 532 > 488` 的 detectability / peak 趋势成立 |
| **2019 POD / 2020 counting POD / 2020 solvent-enhanced POD** | photothermal source + substrate diffusion + solvent factor | 当前无完整 profile | **不可直接对标** | **暂不判定** |

## 3. 固定 Tsuyama 条件后的数据表

### 3.1 2020 diffraction：reference / width-depth 语义

论文侧最能直接对标的是：

- `Fig.3`：width 存在 optimum，不是单调；
- `Fig.5`：depth 会显著改写 diffracted intensity；
- `Fig.9`：POD signal 与 diffracted intensity 近线性。

当前最接近的固定条件 lane：

- `results/reference_depth_semantics_reference_compare.csv`
- `results/reference_depth_semantics_batch_compare.csv`
- `diffraction_2020` profile

代表性 case 的 `current / paper_aligned A_ref` 比值如下：

| wavelength | geometry | current / paper `A_ref` | 趋势判断 |
| --- | --- | ---: | --- |
| 404 | `500×800` | `0.968x` | 差异很小 |
| 404 | `500×900` | `0.960x` | 差异很小 |
| 404 | `500×1200` | `0.930x` | 深通道开始出现系统偏差 |
| 404 | `500×1400` | `0.908x` | 深而窄时偏差最大 |
| 660 | `800×550` | `1.000x` | 与 paper-aligned 基本重合 |
| 660 | `800×1400` | `0.963x` | 差异很小 |
| 660 | `900×1200` | `0.976x` | 差异很小 |

补充统计：

- 全小网格 `A_ref` 平均绝对差异约 **`2.13%`**
- 最大绝对差异约 **`9.20%`**

这张表支持的结论是：

1. **2020 diffraction 约束的核心机制是成立的**：reference field 不是常数，width/depth 会改写它。  
2. **当前 mainline 与更接近论文的 reference lane 在机制方向上趋同**，但深而窄、尤其短波 case 的振幅会有系统偏差。  
3. 所以这部分能支持“机制趋同”，**不能**支持“逐点振幅已逐式复现”。  

### 3.2 2022 NODI：固定 paper-aligned 语义后的 route 对照

当前最接近论文条件的 lane：

- `profile = nodi_2022`
- `reference_model = paper_aligned_phase_filter`
- `illumination_mode = overfill`
- `readout_observable_mode = magnitude`
- `pulse_detection_mode = positive`
- `lockin_time_constant = 1 ms`
- `nodi_lockin_frequency = 3 kHz`
- `decision_mode = single_channel`

结果文件：

- `results/paper_aligned_nodi2022_targeted_grid_cases.csv`
- `results/paper_aligned_nodi2022_targeted_grid_routes.csv`

四条代表 route 在三个 profile 下的结果如下：

| profile | route | raw strict count | mean detection | mean stable | small-EV weighted strict | small-EV weighted stable |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| current | `404, 500×800` | 16 | 0.3425 | 0.3365 | 0.3679 | 0.2162 |
| current | `660, 800×550` | 16 | 0.4830 | 0.4715 | 0.7461 | 0.4090 |
| current | `660, 800×1400` | 19 | 0.4580 | 0.4515 | 0.5976 | 0.3727 |
| current | `660, 900×1200` | 14 | 0.4350 | 0.4260 | 0.7265 | 0.3672 |
| diffraction_2020 | `404, 500×800` | 16 | 0.3535 | 0.3450 | 0.3878 | 0.2188 |
| diffraction_2020 | `660, 800×550` | 23 | 0.4505 | 0.4350 | 0.9015 | 0.4128 |
| diffraction_2020 | `660, 800×1400` | 17 | 0.4160 | 0.4100 | 0.7293 | 0.3421 |
| diffraction_2020 | `660, 900×1200` | 13 | 0.4485 | 0.4420 | 0.6015 | 0.3616 |
| nodi_2022 | `404, 500×800` | 21 | 0.3600 | 0.3540 | 0.7451 | 0.2334 |
| nodi_2022 | `660, 800×550` | 25 | 0.4875 | 0.4670 | 1.0000 | 0.4593 |
| nodi_2022 | `660, 800×1400` | 25 | 0.4395 | 0.4290 | 1.0000 | 0.3748 |
| nodi_2022 | `660, 900×1200` | 25 | 0.4775 | 0.4705 | 1.0000 | 0.3972 |

这张表支持的结论是：

1. **主波长没有翻转**：无论 current / diffraction_2020 / nodi_2022，`660` 都明显优于 `404`。  
2. **最佳几何向论文器件收缩**：在 `nodi_2022` profile 下，`660 + 800×550` 的 `small-EV weighted stable = 0.4593`，高于 `660 + 800×1400` 的 `0.3748`。  
3. 因此最严谨的说法是：  
   - engineering mainline 默认几何仍可保留深通道路线；  
   - **paper-aligned NODI 2022 lane 更接近 `660 + 800×550`。**

### 3.3 2022 NODI：固定条件下的粒径覆盖对照

在 `profile = nodi_2022` 下：

| route | strict count | 未通过粒径 |
| --- | ---: | --- |
| `660, 800×550` | `25/25` | 无 |
| `404, 500×800` | `21/25` | `60, 70, 80, 130 nm` |

这张表说明：

- 如果固定到更接近 Tsuyama 2022 的单通道语义，**`660` 仍然是更稳的主路线**；
- `404` 在 paper-aligned lane 下比 current mainline 更强，但仍没有把 `660` 翻掉。

### 3.4 Tsuyama-like gold lane：固定 `tau = 1 ms`、magnitude readout

当前最接近论文语义的 gold 验证条件来自：

- `results/tsuyama_gold_validation_tau1ms_1000e_report.json`

固定条件为：

- wavelength = `488 / 532 / 660 nm`
- geometry = `800×500`, `800×600`, `1200×500`, `1200×600 nm`
- diameter = `20 / 30 / 40 / 50 / 60 nm`
- `n_events_per_case = 1000`
- `lockin_tau = 1 ms`
- `validation_profile = paper_aligned`
- `readout_observable_mode = magnitude`
- `engineering_max_phase_flip_fraction = 1.0`

按波长聚合结果：

| wavelength | gate pass rate | mean detection | mean stable | mean peak height | mean `Csca` |
| --- | ---: | ---: | ---: | ---: | ---: |
| 488 | 0.00 | 0.0608 | 0.0595 | 0.05245 | `2.856e-16` |
| 532 | 0.00 | 0.0868 | 0.0851 | 0.07730 | `3.932e-16` |
| 660 | 0.45 | 0.1815 | 0.1774 | 0.15641 | `6.658e-16` |

固定 `660, 800×500` 时的粒径表：

| Au diameter | gate | detection | stable | mean peak | `Csca` |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20 nm | fail | 0.000 | 0.000 | 0.00000 | `2.019e-18` |
| 30 nm | fail | 0.146 | 0.140 | 0.04414 | `2.499e-17` |
| 40 nm | pass | 0.266 | 0.265 | 0.10954 | `1.577e-16` |
| 50 nm | pass | 0.305 | 0.300 | 0.23239 | `6.956e-16` |
| 60 nm | pass | 0.315 | 0.308 | 0.44681 | `2.449e-15` |

这张表支持的结论是：

1. **在 Tsuyama-like gold lane 下，`660 > 532 > 488` 的 detectability / peak 趋势很强。**
2. **20 nm Au 仍接近边界，30 nm 开始可见但不稳，40 nm 往上明显进入可检出区。**
3. 这和论文里“小 gold 由长波 NODI lane 主导、20 nm 接近边界”的方向是同向的。  

### 3.5 readout semantics：固定光学条件，只改读出口径

对应结果文件：

- `results/tsuyama_gold_validation_scenario_compare_summary.csv`
- `results/tsuyama_gold_validation_scenario_compare_by_wavelength.csv`

三种场景：

- `baseline_in_phase_gate`
- `in_phase_no_phase_gate`
- `magnitude_gate`

总体对照：

| scenario | gate pass count | gate pass rate | mean detection | mean stable | mean phase flip | mean peak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_in_phase_gate | `0/60` | 0.00 | 0.11075 | 0.10850 | 0.44738 | 0.095283 |
| in_phase_no_phase_gate | `9/60` | 0.15 | 0.11075 | 0.10850 | 0.44738 | 0.095283 |
| magnitude_gate | `9/60` | 0.15 | 0.10967 | 0.10732 | 0.00000 | 0.095390 |

按波长看，`660 nm` 是变化最大的受益者：

| scenario | wavelength | gate pass rate | mean detection | mean stable | mean peak |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_in_phase_gate | 660 | 0.00 | 0.18275 | 0.17890 | 0.15637 |
| in_phase_no_phase_gate | 660 | 0.45 | 0.18275 | 0.17890 | 0.15637 |
| magnitude_gate | 660 | 0.45 | 0.18145 | 0.17735 | 0.15641 |

这张表支持的结论是：

1. **论文语义里更接近 `maximum signal value / magnitude` 的读法，会直接改变 pass/fail。**
2. detection / stable / peak 本身几乎不变，变化最大的其实是 **interpretation / gate semantics**。
3. 因此，这部分和 Tsuyama 2022 / 2024 的论文口径是**强趋同**的：  
   论文关注的是 pulse observables，不是 `phase_flip_fraction` 这样的硬 reject criterion。

## 4. 综合判断：哪些地方已经趋同，哪些还不能说过头

### 4.1 已经可以说“趋同”的部分

| 对标点 | 判断 | 依据 |
| --- | --- | --- |
| blank-channel diffraction / reference-field 机制 | **趋同** | `2020 diffraction` 对照 lane 与当前 mainline 的 `A_ref` 差异大多在几百分点 |
| `660` 在 Tsuyama-like gold lane 的主导地位 | **趋同** | `660` 在 `Csca / detection / peak / pass rate` 上均高于 `532 / 488` |
| `2022 NODI` 下 `660` 仍是主波长 | **趋同** | `nodi_2022` targeted grid 中 `660` 三条路线均优于 `404` |
| readout semantics 会显著改写结论 | **强趋同** | 固定光学条件只改 readout / gate，pass count 从 `0/60` 升到 `9/60` |

### 4.2 只能说“部分趋同”的部分

| 对标点 | 判断 | 备注 |
| --- | --- | --- |
| 最优几何是否与论文器件完全相同 | **部分趋同** | 主趋势一致，但 current mainline 与 paper-aligned lane 的最优深度不同 |
| 论文图上的绝对振幅 / 绝对强度数值 | **部分趋同** | 当前 collection / transport 仍含 surrogate，不能宣称逐图逐点复现 |
| 2024 paired POD/NODI 的完整 paired classification 准确率 | **部分趋同** | paired 语义已可跑，但还不是完整 electronics / thermal lane |

### 4.3 当前不能说已经对齐的部分

| 对标点 | 当前状态 |
| --- | --- |
| 2019 POD / 2020 counting POD / 2020 solvent-enhanced POD 的 thermal 定量链 | 未实现完整 thermal-POD source，因此不能严格对标 |
| 2022 / 2024 论文里的 SVM accuracy 数值 | 当前没有同构 feature / dataset / classifier protocol，不能直接声称复现 |

## 5. 最后一句话

最严格的结论是：

> **Tsuyama 论文里已经有一批可以和当前工程结果做固定条件对标的对象；在 `2020 diffraction`、`2022 NODI` 和 Tsuyama-like gold/readout lane 上，当前结果与论文的主趋势是明显趋同的。**  
> **但这仍然主要是“机制与趋势对齐”，不是“所有图表的绝对数值已逐式复现”。**

## 6. 本文用到的本地文件

- `43_tsuyama论文与工程全面复核笔记.md`
- `50_paper_aligned_reference对照结果.md`
- `51_tsuyama_paper_aligned全论文闭环审查.md`
- `52_paper_aligned_profiles说明.md`
- `53_paper_aligned_nodi2022最小决策网格结果.md`
- `57_工程主线与Tsuyama论文结果趋势对照_中英对照.md`
- `results/reference_depth_semantics_reference_compare.csv`
- `results/reference_depth_semantics_batch_compare.csv`
- `results/paper_aligned_nodi2022_targeted_grid_cases.csv`
- `results/paper_aligned_nodi2022_targeted_grid_routes.csv`
- `results/tsuyama_gold_validation_tau1ms_1000e_cases.csv`
- `results/tsuyama_gold_validation_tau1ms_1000e_report.json`
- `results/tsuyama_gold_validation_scenario_compare_summary.csv`
- `results/tsuyama_gold_validation_scenario_compare_by_wavelength.csv`
