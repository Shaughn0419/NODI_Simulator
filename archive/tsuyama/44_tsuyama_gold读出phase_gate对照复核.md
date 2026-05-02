# Tsuyama Gold 读出与 Phase Gate 对照复核

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 建立时间：2026-04-14
> 目的：验证当前 Tsuyama gold validation 中，`readout_observable_mode="in_phase"` 与 `phase_flip_fraction` 工程 gate 的组合，是否在不必要地压制 gold case。

---

## 1. 本轮对照的三个场景

固定条件：

- `n_events = 1000`
- `lockin_tau = 1 ms`
- 几何：`800×500`、`800×600`、`1200×500`、`1200×600 nm`
- 波长：`488 / 532 / 660 nm`
- gold 粒径：`20 / 30 / 40 / 50 / 60 nm`

只改两类因素：

1. 基线场景 `baseline_in_phase_gate`
   - `readout_observable_mode="in_phase"`
   - `engineering_max_phase_flip_fraction = 0.5`

2. `magnitude_gate`
   - `readout_observable_mode="magnitude"`
   - `engineering_max_phase_flip_fraction = 0.5`

3. `in_phase_no_phase_gate`
   - `readout_observable_mode="in_phase"`
   - `engineering_max_phase_flip_fraction = 1.0`

这样设计的目的，是把两件事拆开：

- 到底是 `X` vs `R` 观测量定义本身在改结果；
- 还是 `phase_flip_fraction` 这个硬门槛在改结果。

---

## 2. 总体结果

| 场景 | 通过 case 数 | 通过率 | 平均 detection_rate | 平均 stable_detection_rate | 平均 phase_flip_fraction | 平均 mean_peak_height |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline_in_phase_gate` | 0 / 60 | 0.00 | 0.11075 | 0.10850 | 0.44738 | 0.095283 |
| `in_phase_no_phase_gate` | 9 / 60 | 0.15 | 0.11075 | 0.10850 | 0.44738 | 0.095283 |
| `magnitude_gate` | 9 / 60 | 0.15 | 0.10967 | 0.10732 | 0.00000 | 0.095390 |

最关键的观察有三条：

1. **只放宽 `phase_flip` gate，就有 `9` 个 case 从不通过变成通过。**
2. **这 `9` 个 case 在放宽 gate 时，`detection_rate / stable_detection_rate / mean_peak_height` 全都不变。**
3. **把读出改成 `magnitude` 后，也正好是同样 `9` 个 case 变成通过，而且 detection/peak 的变化非常小。**

这说明：

- 当前差异的主因，不是参考场公式被改了；
- 也不是 detectability 本身突然大幅变化；
- 而是 **`phase_flip_fraction` 作为硬 gate 的定义，在当前 Tsuyama gold 对照里过于主导。**

---

## 3. 和基线相比，差异到底有多大

### 3.1 `magnitude_gate` 相对基线

- 平均绝对 `detection_rate` 变化：`0.00272`
- 平均绝对 `stable_detection_rate` 变化：`0.00268`
- 平均绝对 `mean_peak_height` 变化：`0.000552`
- 平均 `phase_flip_fraction` 变化：`-0.44738`

解释：

- detectability 和 peak 基本没怎么变；
- 但 `phase_flip_fraction` 几乎整体塌到 `0`。

这与锁相读出常识一致：

- `in_phase` 更接近相位相关的 `X` 通道；
- `magnitude` 更接近相位不变的包络 `R`。

### 3.2 `in_phase_no_phase_gate` 相对基线

- 平均绝对 `detection_rate` 变化：`0.0`
- 平均绝对 `stable_detection_rate` 变化：`0.0`
- 平均绝对 `mean_peak_height` 变化：`0.0`
- 平均 `phase_flip_fraction` 变化：`0.0`

解释：

- 这个场景根本没有改动物理量或读出量；
- 它只是告诉我们：**原基线里那 9 个 case 之所以不过，纯粹就是因为 `phase_flip_fraction` 这个 gate。**

---

## 4. 哪些 case 真正被 `phase_flip` 单独卡住

从基线变成通过的 `9` 个 case，全都满足：

- 基线主 blocker = `phase_flip_fraction`
- 改成 `magnitude` 后直接 `pass`
- 或者保持 `in_phase` 不变、仅放宽 `phase_flip` gate 后也直接 `pass`

这 `9` 个 case 全部都在 `660 nm`：

1. `660 nm, 800×500 nm, 40 nm Au`
2. `660 nm, 800×500 nm, 50 nm Au`
3. `660 nm, 800×500 nm, 60 nm Au`
4. `660 nm, 800×600 nm, 50 nm Au`
5. `660 nm, 800×600 nm, 60 nm Au`
6. `660 nm, 1200×500 nm, 50 nm Au`
7. `660 nm, 1200×500 nm, 60 nm Au`
8. `660 nm, 1200×600 nm, 50 nm Au`
9. `660 nm, 1200×600 nm, 60 nm Au`

也就是说，本轮对照的最直接结论不是“所有问题都解决了”，而是：

- **660 nm gold 这条线里，确实存在一批本来 detectability 就够、但被 `phase_flip` 单独压掉的 case。**

---

## 5. 没有被这次修正解决的部分

这一步并没有让 `488 / 532 nm` 自动通过，也没有让所有 `660 nm` case 都通过。

当前 blocker 分布：

- 基线：
  - `detected_events`: `27`
  - `stable_detection_rate`: `18`
  - `phase_flip_fraction`: `9`
  - `detection_rate`: `6`
- `magnitude` 或放宽 `phase_flip` 后：
  - `pass`: `9`
  - 其余仍主要卡在 `detected_events / stable_detection_rate / detection_rate`

这说明：

1. `phase_flip` 不是唯一问题；
2. 但它确实在当前 gold 对照里制造了**额外且可分离**的误伤；
3. 所以它应该先从“主 gate”降级成“诊断项”，而不是继续和 detectability 主结论绑死。

---

## 6. 当前最合理的修正建议

### 建议 A：先修 Tsuyama gold validation 的判据层

优先做法：

- 把 Tsuyama 对照主口径切到更接近论文的 `magnitude / absolute peak / maximum signal value`
- 把 `phase_flip_fraction` 保留为诊断项

原因：

- 这和论文的观测量更同构；
- 也和本轮三场景结果最一致。

### 建议 B：不要把这一步误解成“模型已全部修好”

即使移除了 `phase_flip` 误伤：

- 仍有大量 case 卡在 `detected_events`
- 仍有大量 case 卡在 `stable_detection_rate`

所以这一步是**先修评价口径**，不是宣布 transport / noise / threshold 问题都已经解决。

### 建议 C：transport 升级仍然重要，但优先级在这一步之后

因为本轮对照已经证明：

- 有一部分结论变化，根本不需要改 transport 就会发生；
- 所以在 transport 升级之前，先把读出/gate 语义理顺，更能避免把两个问题混在一起。

---

## 7. 本轮复核后的判断

我现在的判断是：

1. **需要修正**，但优先修的是 `Tsuyama gold validation` 的观测量/门槛解释方式。
2. 这不是“推翻现有核心物理链”，而是“把一个过强的工程 gate 从主结论里拿出来”。
3. 真正的底层物理升级，例如 crossing-conditioned transport，应该放在这一层修完之后再做。

---

## 8. 相关结果文件

- `results/tsuyama_gold_validation_tau1ms_1000e_in_phase_gate_cases.csv`
- `results/tsuyama_gold_validation_tau1ms_1000e_in_phase_gate_report.json`
- `results/tsuyama_gold_validation_tau1ms_1000e_magnitude_gate_cases.csv`
- `results/tsuyama_gold_validation_tau1ms_1000e_magnitude_gate_report.json`
- `results/tsuyama_gold_validation_tau1ms_1000e_in_phase_no_phase_gate_cases.csv`
- `results/tsuyama_gold_validation_tau1ms_1000e_in_phase_no_phase_gate_report.json`
- `results/tsuyama_gold_validation_scenario_compare_summary.csv`
- `results/tsuyama_gold_validation_scenario_compare_by_wavelength.csv`
- `results/tsuyama_gold_validation_scenario_compare_report.json`

---

## 9. 已实施的 scoped fix

本轮没有改全局 `DEFAULT_SIM_CFG`，只做了两类局部修正：

1. `tools/tsuyama_gold_validation_compare.py`
   - 新增 `validation_profile`
   - 当前默认 profile 改为 `paper_aligned`
   - 对应口径：
     - `readout_observable_mode="magnitude"`
     - `engineering_max_phase_flip_fraction=1.0`
   - 同时保留 `legacy_mainline` 作为历史对照入口

2. `dashboard/panels/research_story.py`
   - 在 `Tsuyama Comparison` 页面新增 targeted gold 判据复核区
   - 明确把“全库趋势图”和“Tsuyama gold 支线判据复核”分层展示
   - 避免继续把旧主库里 `in_phase + phase gate` 的读法误当成论文对齐后的最终判断

另外，canonical targeted validation 结果文件：

- `results/tsuyama_gold_validation_tau1ms_1000e_cases.csv`
- `results/tsuyama_gold_validation_tau1ms_1000e_report.json`

现已重算为 `paper_aligned` 口径。
