# paper_aligned_nodi_2022 最小决策网格结果

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 日期：2026-04-15  
> 用途：回答一个比单 case probe 更直接的问题：  
> **如果只看 Tsuyama 2022 更接近的 NODI 语义，`660` 和 `404` 的主路线排序会不会变化？**

---

## 1. 这轮计算怎么做的

这轮不是全量库重算，而是一个**最小决策网格**：

- profile：
  - `current_dashboard_replay`
  - `diffraction_2020`
  - `nodi_2022`
- 波长：
  - `404`
  - `660`
- 几何：
  - `500×800`
  - `800×550`
  - `800×1400`
- 粒径：
  - `60`
  - `100`
  - `150`
  - `300 nm`
- 每 case：
  - `60 events`
- worker：
  - `8`

输出文件：

- `results/paper_aligned_nodi2022_targeted_grid_cases.csv`
- `results/paper_aligned_nodi2022_targeted_grid_routes.csv`
- `results/paper_aligned_nodi2022_targeted_grid_summary.json`

---

## 2. 这轮结果最重要的结论

### 2.1 主波长没有翻转

在三个 profile 下，**`660` 仍然明显优于 `404`**。

这说明：

- `paper_aligned_nodi_2022` 不会把主波长从 `660` 翻到 `404`
- 所以 `660` 作为主平台波长的结论仍然稳

### 2.2 但主几何有明显收缩

这轮最关键的变化是：

- `current_dashboard_replay` 下：
  - 最优 route 是 **`660, 800×1400`**
- `diffraction_2020` 下：
  - `660, 800×550` 已经和 `660, 800×1400` 拉得更近
- `nodi_2022` 下：
  - 最优 route 变成 **`660, 800×550`**

也就是说：

> **在更接近 Tsuyama 2022 NODI 语义的最小网格里，`660` 仍是主波长，但最佳几何从深通道 `800×1400` 向论文器件附近的 `800×550` 收缩。**

---

## 3. route 排序结果

### 3.1 current mainline replay

| route | raw strict count | small-EV weighted strict | small-EV weighted stable |
| --- | --- | --- | --- |
| `660, 800×1400` | `3` | `0.7921` | `0.3809` |
| `660, 800×550` | `1` | `0.4573` | `0.3816` |
| `404, 500×800` | `1` | `0.3349` | `0.1870` |

current mainline 的读法仍然是：

- `660, 800×1400` 是更像默认主平台的几何

### 3.2 `diffraction_2020`

| route | raw strict count | small-EV weighted strict | small-EV weighted stable |
| --- | --- | --- | --- |
| `660, 800×550` | `3` | `0.7921` | `0.4065` |
| `404, 800×550` | `3` | `0.7921` | `0.2015` |
| `660, 800×1400` | `3` | `0.6651` | `0.3371` |

这说明只把 reference/diffraction 收到 paper-aligned 语义以后：

- 660 仍然占优
- 但浅通道已经明显更强

### 3.3 `nodi_2022`

| route | raw strict count | small-EV weighted strict | small-EV weighted stable |
| --- | --- | --- | --- |
| `660, 800×550` | `4` | `1.0000` | `0.4613` |
| `660, 800×1400` | `4` | `1.0000` | `0.3759` |
| `404, 500×800` | `3` | `0.7921` | `0.2217` |

这张表的意思非常直接：

1. `660` 仍然是第一波长
2. 在 `nodi_2022` profile 下，`800×550` 比 `800×1400` 更像论文语义下的首选
3. `404` 仍然落后于 `660`

---

## 4. 这对我们原来的结论意味着什么

## 4.1 什么没变

- `660` 作为主平台波长没有翻转
- `404` 仍然更像辅助路线

## 4.2 什么变了

如果我们讨论的是：

> **更接近 Tsuyama 2022 NODI 论文语义的 paper-aligned 选择**

那就不能再直接沿用：

- `660 + 800×1400`

作为默认最优。

在当前最小决策网格里，更合适的说法应该是：

- **current engineering mainline**：
  - `660 + 800×1400`
- **paper-aligned NODI 2022 lane**：
  - `660 + 800×550`

## 4.3 为什么会这样

因为 `nodi_2022` profile 收紧了三层东西：

1. reference depth 语义更接近 paper-aligned
2. readout 更接近 `magnitude / maximum signal value`
3. `phase_flip_fraction` 不再作为主 reject criterion

这三层一起作用后，**更深的通道不再自动占优**。

---

## 5. 当前最合理的解读

我认为现在最合理的解读是：

1. 如果目标是 **engineering mainline 默认平台**
   - 当前还可以保留 `660 + 800×1400`

2. 如果目标是 **paper-aligned NODI 2022 validation**
   - 更应该优先看 `660 + 800×550`

3. 因此：
   - 现在还不能把 mainline 和 paper-aligned 混成一个结论
   - 但已经可以明确说：**主波长不翻，主几何会变**

---

## 6. 下一步建议

下一步最值得做的，不是继续猜，而是：

### A. 把 `900×1200` 补回 paper-aligned NODI 2022 小网格

因为这条线在 current mainline 里是重要备选。

### B. 在 `nodi_2022` profile 下，把粒径点扩到 `60–300 nm` 全 25 点

这样才能真正比较：

- `800×550`
- `800×1400`
- `900×1200`

谁在 paper-aligned lane 里最稳。

### C. 不要在这一步就重跑全量库

因为现在已经拿到了最关键的方向性信息：

- 波长不翻
- 几何可能翻

这已经足够指导下一轮验证。

---

## 7. 最后一句话

> **这轮最小决策网格说明：  
> `paper_aligned_nodi_2022` 不会把主波长从 `660` 翻成 `404`，  
> 但会把最佳几何从 current mainline 的深通道路线，拉回到更接近论文器件的 `800×550`。**

