# Tsuyama 修正闭环清单

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 建立时间：2026-04-14  
> 用途：在讨论全量重算前，明确区分  
> 1. Tsuyama 论文已经要求进入当前工程口径、并且本轮必须闭环的修正项  
> 2. 仍然值得继续升级、但不属于“本轮不做就不能重算”的后续增强项

---

## 1. 先给结论

如果问题是：

> “参考了 Tsuyama 2020 / 2022 / 2024 之后，所有必须先修正的东西是不是都已经修完？”

我的当前判断是：

### 1.1 已经完成的部分

与 Tsuyama 论文主线直接相关、并且我认为属于 **本轮必须进入 current code** 的关键修正，已经基本完成：

1. `NA cutoff` 已写入参考场链路  
2. illumination / collection 几何已拆开  
3. `overfill` 的 `x/z` 与 `y` 语义已修正  
4. Gouy 相位双重叠加 bug 已修掉  
5. Tsuyama gold validation 的判据层已改成 `paper_aligned` 支线  
6. 文档里 Tsuyama 的支撑范围与期刊引用口径已同步修正

### 1.2 还没有“全部完成”的部分

但如果把“需要完善”理解成 **所有被论文复核后指出的后续升级点都必须一起做完**，那答案是否定的。

至少还有两类事情没有完成：

1. **crossing-conditioned / event-flux transport 升级**  
   这件事仍然没有做。

2. **主路线全量库与当前代码重新对齐**  
   当前 `fine_full_range_biomimetic_exosome_10000e_*` 还不是按现行 current code 重新生成的标准主库。

所以更准确的说法不是“全部都做完了”，而是：

> **必须先修的 Tsuyama 主线硬修正，已经基本做完；但后续增强项和主库重建还没完成。**

---

## 2. 我怎么划分“必须先闭环”与“后续增强”

这里的关键不是把所有想到的改进都塞进“must-fix”。

我现在按两层划分：

### A. 本轮必须先闭环，才能说“当前代码主链已对齐 Tsuyama”

这类项的特点是：

- 如果不修，会直接导致当前代码和论文实验主约束冲突
- 或者会让论文对照的主结论被错误 gate / 语义误读

### B. 后续仍然值得继续升级，但不属于“本轮不做就不能进入 current code”

这类项的特点是：

- 它们会提升严谨性
- 但当前还属于“已明示 surrogate 边界”
- 不等于当前主链已经硬错

---

## 3. 闭环状态总表

| 项目 | 来自 Tsuyama 的含义 | 当前状态 | 是否属于本轮 must-fix |
|------|--------------------|----------|-------------------------|
| `NA cutoff` | 一阶衍射收集不到时 reference 不能继续非零 | **已完成** | **是** |
| illumination / collection 解耦 | `NA=0.45` 照明与 `NA=0.9` 收集不能混用 | **已完成** | **是** |
| overfill 语义修正 | `x/z` 近似均匀、`y` 保留有限 transit window | **已完成** | **是** |
| Gouy 去重 | 避免 beam-side Gouy 与 focus-crossing 重复叠加 | **已完成** | **是** |
| lock-in 默认口径统一到 `1 ms` | 2022/2024 给 `1–2 ms`，current 默认明确切到 `1 ms` | **代码/文档已完成；主库未重算** | **是** |
| Tsuyama gold 判据改成 `paper_aligned` | 论文主观测量更接近 `magnitude / maximum signal value` | **已完成（支线）** | **是** |
| Tsuyama 支撑范围缩窄 | gold validation 不能直接替 exosome 路线背书 | **已完成（文档/展示）** | **是** |
| crossing-conditioned transport | 压力驱动通量统计要和观测平面事件采样一致 | **未完成** | **否，属于后续增强** |
| blank-channel 实测 reference 标定 | `channel_angular_surrogate` 仍是 fallback，不是实测 | **未完成** | **否，属于后续增强** |
| 主路线全量库按 current code 重建 | 让 dataset 与 current code 完全一致 | **未完成** | **是，但它本身就是“重算”动作** |

---

## 4. 已完成的 must-fix 项

### 4.1 `NA cutoff`：已完成

这条是 Tsuyama 2020/2022 最明确的硬约束之一。

当前代码已经把：

`W_min = λ / NA_collection`

写进 reference 链路，不再只是文档提醒。

因此：

- `660 nm + 700 nm width` 不再被错误保留 reference
- `488 nm + 500 nm width` 这类 case 也应被 current code 视作 cutoff 外

结论：**这项已经闭环。**

### 4.2 illumination / collection 解耦：已完成

Tsuyama 2022 给出：

- illumination objective `NA = 0.45`
- collection objective `NA = 0.9`

现在 current code 已经明确：

- illumination 侧走 decoupled illumination geometry
- collection 侧继续按自身 `NA_collection`

结论：**这项已经闭环。**

### 4.3 overfill 语义修正：已完成

现在 `overfill` 的 current 语义已经是：

- `x/z` 近似均匀
- `y` 保留有限 transit envelope

这修掉了早期“整条 trace 都像在焦内”的错误。

结论：**这项已经闭环。**

### 4.4 Gouy 双重叠加：已完成

这属于论文对齐后额外暴露出的 current code bug。

它已经在 `relative_surrogate` 路径里去重，避免 `2× arctan`。

结论：**这项已经闭环。**

### 4.5 `1 ms` current lock-in 默认：代码与文档已完成

Tsuyama 2022 / 2024 给的是 `1–2 ms` 范围。

我们本轮已经明确把 current code / current docs 的默认理解切到：

- `1 ms` 主工作点
- `2 ms` 作为敏感性复核

因此：

- current code 默认值已闭环
- 但旧主库仍然是 `1.5 ms` 口径

所以这项要拆成两层：

1. **代码/文档口径：已闭环**  
2. **结果库同步：未闭环**

### 4.6 Tsuyama gold `paper_aligned` 判据：已完成

这条是本轮最重要的新修正之一。

现在 Tsuyama gold validation 支线已经明确区分：

- `legacy_mainline`
- `paper_aligned`

其中 canonical targeted validation 已经切到：

- `readout_observable_mode = "magnitude"`
- `engineering_max_phase_flip_fraction = 1.0`

并把 `phase_flip_fraction` 降级为诊断项。

结论：**这条支线上的判据修正已经闭环。**

### 4.7 Tsuyama 支撑范围与引用口径：已完成

现在文档已经明确：

- Tsuyama 最强支持的是 blank diffraction、plasmonic gold/silver、paired POD/NODI
- 不能直接把这条验证链外推成 exosome 默认路线已被论文逐值证实

Tsuyama 2022 的期刊引用也已统一回到 *Microfluidics and Nanofluidics*。

结论：**文档口径层面的修正已经闭环。**

---

## 5. 还没完成、但不属于“先做完才能进入全量重算”的项

### 5.1 crossing-conditioned transport：还没完成

这是我当前最明确保留的物理升级项之一。

它还没有做，当前实现仍然是：

- uniform accessible cross-section sampling
- `rect_series + diffusion + anisotropic hindrance`
- 进入焦区前预跑一段轨迹

为什么我没有把它列成“先做完才能重算”的 blocker：

1. Tsuyama 2024 的确支持 pressure-driven + diffusion，但并没有直接提供我们可一键照抄的 crossing-conditioned 构造  
2. 现在如果仓促把 flux weighting 硬塞成初始位置偏置，反而容易做出语义不干净的补丁  
3. 它更像“下一阶段应该认真升级”的边界，而不是 current code 当前已经明显违反论文主线

所以我的结论是：

- **这项没有完成**
- **但它不应该和本轮 must-fix 混为一类**

### 5.2 blank-channel 实测标定：还没完成

当前 reference 若无标定表，仍然主要依赖 `channel_angular_surrogate`。

这是合理 fallback，但不是实测 blank reference。

所以：

- **这项没有完成**
- **但它属于 future calibration / validation upgrade，不属于本轮 Tsuyama 主链硬修正**

---

## 6. 为什么我现在仍然不直接说“可以立刻全量重算”

不是因为 Tsuyama-derived must-fix 还漏了哪条 code bug 没修。

而是因为现在还有一个新的、更现实的问题：

> **现存 biomimetic exosome 全量主库，已经不能再被当成 current code 的标准真值。**

也就是说，阻止我们继续“直接沿用主库再往下分析”的，
现在主要不是“Tsuyama 修正没做完”，而是：

1. current code 已经变了  
2. current docs 已经变了  
3. current Tsuyama gold validation 口径也已经变了  
4. 但 exosome 主路线全量库还没有按这些 current 口径重建

所以如果你问：

> “在参考 Tsuyama 之后，需要修正或完善的部分，是不是已经都完成了，再说全量重算？”

我会给出更精确的回答：

### 6.1 如果你说的是“必须先修的 Tsuyama 主线问题”

**基本已经完成。**

### 6.2 如果你说的是“所有后续增强项也要一起做完”

**没有完成，而且不应该把它们全部绑成全量重算前置条件。**

### 6.3 现在真正阻止我们继续沿用旧主库的原因

不是 Tsuyama must-fix 还没做，而是：

**当前主库已经和 current code 不完全一致。**

---

## 7. 我建议的判断标准

我建议把“能不能开始全量重算”改成下面这个判断题：

### 条件 1

Tsuyama 论文主线要求进入 current code 的硬修正是否都已闭环？

我的答案：**是，基本已闭环。**

### 条件 2

当前是否还存在一个明确已知的 current-code blocker，会让整套全量重算失去意义？

我的答案：**目前没有发现这种 blocker。**

### 条件 3

当前是否还在拿一个已知与 current code 不完全一致的旧主库继续当标准真值？

我的答案：**是。**

所以最终逻辑变成：

> **不是因为 Tsuyama 修正没做完，不能重算；恰恰相反，是因为 Tsuyama 主线修正已经基本做完，而旧主库又已经过时，所以应该在确认 current 默认口径后重算。**

---

## 8. 这份清单对应的当前结论

一句话总结：

**Tsuyama 导出的 must-fix 基本已经闭环；还没做的是后续增强项，而不是继续拖住全量重算的前置 bug。现在真正需要解决的，是按 current code 重建主路线全量库。**
