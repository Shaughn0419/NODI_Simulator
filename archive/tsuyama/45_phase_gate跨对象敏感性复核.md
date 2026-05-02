# Phase Gate 跨对象敏感性复核

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 建立时间：2026-04-14
> 目的：判断 `phase_flip_fraction` 问题是否只存在于 Tsuyama gold validation 支线，还是已经影响到 exosome 分支；同时评估当前是否需要全量重算。

> 2026-04-14 补充更正：
> 本文第 4 节里关于“`exosome_mainline_representative` 当前代码 rerun 不再复现主库”的判断，
> 当时使用的是 `1000 events + 1.0 ms` 的快速敏感性设置，因此它只能作为“值得继续审计”的信号，
> 不能直接当成最终 provenance 结论。
> 后续已经补做严格的 `meta.json` 精确重放，请以 `46_主路线一致性审计.md` 为准。

---

## 1. 本轮复核的 case 组成

使用三类代表 case，共 `17` 个 case：

1. `gold_tsuyama_phase_sensitive`
   - 来自前一轮 `Tsuyama gold` 复核里，所有会被 `paper-aligned` 口径救回的 `660 nm` gold case
   - 共 `9` 个 case

2. `exosome_mainline_representative`
   - 从当前全量主库里，选取 `404 / 488` 主路线中具有代表性的 `recommended_default` exosome case
   - 共 `4` 个 case

3. `exosome_660_phase_sensitive`
   - 从当前全量主库里，选取 `660 nm` 下高分但被 `phase_flip_fraction` 卡住的 exosome case
   - 共 `4` 个 case

三组都跑三种场景：

- `baseline_in_phase_gate`
- `magnitude_gate`
- `in_phase_no_phase_gate`

---

## 2. 最核心的结果

### 2.1 Tsuyama gold：结论再次被确认

| cohort | 场景 | gate pass |
| --- | --- | ---: |
| `gold_tsuyama_phase_sensitive` | `baseline_in_phase_gate` | `0 / 9` |
| `gold_tsuyama_phase_sensitive` | `in_phase_no_phase_gate` | `9 / 9` |
| `gold_tsuyama_phase_sensitive` | `magnitude_gate` | `9 / 9` |

并且：

- 只放宽 `phase_flip` gate 时：
  - `mean_abs_detection_delta = 0`
  - `mean_abs_stable_delta = 0`
  - `mean_abs_peak_delta = 0`

这再次说明：

- **Tsuyama gold 支线里的问题，确实主要是 gate 语义，而不是物理 detectability 本身。**

### 2.2 660 exosome：也存在 phase-gate 敏感性

| cohort | 场景 | gate pass |
| --- | --- | ---: |
| `exosome_660_phase_sensitive` | `baseline_in_phase_gate` | `2 / 4` |
| `exosome_660_phase_sensitive` | `in_phase_no_phase_gate` | `4 / 4` |
| `exosome_660_phase_sensitive` | `magnitude_gate` | `4 / 4` |

并且：

- `in_phase_no_phase_gate` 相对 baseline：
  - `changed_to_pass_count = 2`
  - `mean_abs_detection_delta = 0`
  - `mean_abs_stable_delta = 0`
  - `mean_abs_peak_delta = 0`
- `magnitude_gate` 相对 baseline：
  - `changed_to_pass_count = 2`
  - `mean_abs_detection_delta ≈ 0.0085`
  - `mean_abs_stable_delta ≈ 0.0110`
  - `mean_abs_peak_delta ≈ 0.000645`

这说明：

- **phase-gate 敏感性并不只存在于 Tsuyama gold。**
- 在当前代码下，`660 nm` exosome 的一部分 case 也会被同样类型的 gate 解释压住。

### 2.3 404/488 exosome 主路线：这次没有看到“phase-gate 误伤翻盘”

| cohort | 场景 | gate pass |
| --- | --- | ---: |
| `exosome_mainline_representative` | `baseline_in_phase_gate` | `0 / 4` |
| `exosome_mainline_representative` | `in_phase_no_phase_gate` | `0 / 4` |
| `exosome_mainline_representative` | `magnitude_gate` | `0 / 4` |

并且：

- `magnitude_gate` 相对 baseline：
  - `mean_abs_detection_delta ≈ 0.0010`
  - `mean_abs_stable_delta ≈ 0.0005`
  - `mean_abs_peak_delta ≈ 0.000126`
- `changed_to_pass_count = 0`

如果只看这三场景内部对比，它说明：

- **在这 4 个 rerun case 上，`phase_flip` 不是主导 blocker。**

---

## 3. 但这里出现了一个更重要的问题

### 3.1 当前代码对 404/488 主路线 exosome 的 rerun，和存量全量主库不一致

本轮选出来的 `exosome_mainline_representative`，本来是从当前全量主库中挑出的 `recommended_default` case。

例如：

- `exosome_biomimetic_corona_nominal_80nm`, `404 nm`, `500×1800 nm`
  - 全量主库：`engineering_gate_passed = True`, `detection_rate = 0.2717`
  - 当前代码独立 rerun：`engineering_gate_passed = False`, `detection_rate = 0.000`

- `exosome_biomimetic_corona_nominal_140nm`, `404 nm`, `500×1700 nm`
  - 全量主库：`engineering_gate_passed = True`, `detection_rate = 0.4907`
  - 当前代码独立 rerun：`engineering_gate_passed = False`, `detection_rate = 0.145`

- `exosome_biomimetic_corona_nominal_80nm`, `488 nm`, `600×1600 nm`
  - 全量主库：`engineering_gate_passed = True`, `detection_rate = 0.3864`
  - 当前代码独立 rerun：`engineering_gate_passed = False`, `detection_rate = 0.007`

这已经不是“统计噪声”能解释的量级差异。

### 3.2 这意味着什么

这意味着当前我们面对的是两个层次不同的问题：

1. **phase gate 语义问题**
   - 已被 Tsuyama gold 和 `660 exosome` 共同验证为真实存在

2. **当前代码 vs 存量全量主库的一致性问题**
   - 至少在部分 `404/488 exosome` 主路线 case 上，已经出现明显漂移
   - 因此不能简单假设“只要不碰主线默认，就完全不需要重新核对全量库”

---

## 4. 当前最稳妥的结论

### 4.1 关于 Tsuyama gold scoped fix

- **已经足够成立**
- 不需要再为这一步单独回退

### 4.2 关于是否把修正推广到主线

- 不能直接因为 Tsuyama gold 的结论，就立刻全局把 `phase_flip_fraction` 从主 gate 中拿掉
- 但也不能再说“这只是 gold 局部问题”
- 因为 `660 exosome` 的代表 case 也表现出同类 phase-gate 敏感性

### 4.3 关于是否需要全量重算

我现在的判断是：

1. **如果问题只限定在 Tsuyama gold validation 支线，不需要全量重算。**
2. **如果要把读出/gate 修正推广到 exosome 主线，或者要把当前代码状态当成新的主真值，那么就需要全量重算。**
3. **即使暂时不推广 phase-gate 修正，这次复核也已经暴露出“当前代码 vs 存量全量主库”在部分主路线 exosome case 上存在显著漂移，因此全量重算已经变成一项有现实必要性的工作，而不再只是可选优化。**

---

## 5. 我建议的下一步顺序

1. 先做一次**主路线一致性审计**
   - 专门核对为什么 `404/488` 的 `recommended_default` exosome case 在当前代码下 rerun 不再复现主库结果
   - 这一步优先级已经高于继续讨论 `phase_flip` 在主线是否降级

2. 如果确认当前代码就是我们要保留的状态
   - **启动全量重算**
   - 至少需要重算 biomimetic exosome 主库

3. 重算完成后，再决定主线 engineering gate 是否也要跟进 `phase_flip` 分层
   - 因为那时我们面对的是同一版代码、同一版结果库，讨论才不会混乱

---

## 6. 本轮结果文件

- `results/phase_gate_cross_scope_sensitivity_selected_cases.csv`
- `results/phase_gate_cross_scope_sensitivity_cases.csv`
- `results/phase_gate_cross_scope_sensitivity_report.json`
