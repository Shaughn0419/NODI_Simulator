# paper_aligned_reference 对照结果

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 日期：2026-04-15  
> 目的：在不推翻当前主线的前提下，做一个更接近 Tsuyama 2020 `phase filter` 语义的参考场对照模式，判断当前 `depth_term` 额外作用到底会不会显著改变 width/depth 结论。

---

## 1. 这次具体改了什么

新增参考场模式：

- `paper_aligned_phase_filter`

它相对当前主线 `channel_angular_surrogate` 的差异是：

1. **保留** depth 通过

   \[
   \delta_{\mathrm{ref}} = 2\pi |\Delta n| H / \lambda
   \]

   进入 phase delay

2. **关闭**额外的

   \[
   \mathrm{sinc}(H k_z / 2\pi)
   \]

   depth aperture 项

3. **关闭** width soft-cutoff surrogate

4. **去掉**额外的连续 width/depth 几何相位修饰，只保留最小 `phase_delay/2`

因此它不是一个“全波新模型”，而是一个：

> **更接近 Tsuyama 2020 depth 只作为 phase thickness 的对照模式**

---

## 2. 生成了哪些结果

对照工具：

- `tools/compare_reference_depth_semantics.py`

输出文件：

- `results/reference_depth_semantics_reference_compare.csv`
- `results/reference_depth_semantics_batch_compare.csv`

这轮没有重跑全量库，只做了：

1. 一个 reference-level 小网格对照
2. 一组代表性粒径 / 波长 / 几何的 batch probe

所以这轮结果足够回答：

- “当前 depth 语义问题会不会立刻把参考场推翻”

但**还不足以**替代完整全量重算。

---

## 3. reference-level 的核心结果

在下面这些代表性 case 上：

- `404, 500×800`
- `404, 500×900`
- `660, 800×550`
- `660, 800×1400`
- `660, 900×1200`

当前主线与 `paper_aligned_phase_filter` 的 `A_ref / g_ref` 比例如下：

| case | current / paper `A_ref` |
| --- | --- |
| `404, 500×800` | `0.968x` |
| `404, 500×900` | `0.960x` |
| `660, 800×550` | `1.000x` |
| `660, 800×1400` | `0.963x` |
| `660, 900×1200` | `0.976x` |

### 3.1 全部小网格上的差异量级

在 `404/660`、`W=500/800/900/1200`、`H=500/550/800/900/1200/1400` 这个小网格上：

- `A_ref` 平均绝对差异约 **`2.13%`**
- 最大绝对差异约 **`9.20%`**

最大差异主要出现在：

- **`404 nm`**
- **更深、更窄的通道**

例如：

- `404, 500×1400`：current / paper = `0.908x`
- `404, 500×1200`：current / paper = `0.930x`
- `660, 800×1400`：current / paper = `0.963x`

### 3.2 这说明什么

这说明：

1. 当前 `depth_term` 的额外作用**不是零**
2. 但在这轮小网格里，它造成的是**百分之几到不到一成**的 reference 振幅差异
3. 它会系统性地把**深而窄、尤其短波**的参考场略微压低

所以这个问题目前更像：

> **解释口径必须修正**

而不是：

> **当前主线已经错到完全不能用**

---

## 4. batch probe 的结果怎么读

代表性 batch probe 也做了，但要非常谨慎地读。

本轮 batch probe 用的是：

- 少量代表性 case
- `n_events = 400`

所以它更适合看：

- `A_ref`
- `mean_peak_height`
- `phase_flip_fraction`

是否发生明显漂移，而不适合直接替代全量推荐排序。

### 4.1 目前看到的趋势

在代表性 case 上：

- `A_ref` 的差异与 reference-level 对照一致，基本仍是几百分点
- `mean_peak_height` 通常也只有小幅变化
- 本轮 probe 里没有看到“参考模式一换，检测率大面积翻转”的现象

这进一步说明：

- 这个问题**值得严肃对待**
- 但目前证据还不支持“当前主线推荐会立即整体翻盘”

---

## 5. 这对当前结论意味着什么

## 5.1 什么必须改

以后不能再把当前 `channel_angular_surrogate` 说成：

> “就是 Tsuyama 2020 原推导的直接实现”

更准确的说法必须改成：

> “当前主线是工程 surrogate；  
> `paper_aligned_phase_filter` 是专门用于审查 Tsuyama 2020 depth 语义的对照模式。”

## 5.2 什么暂时不用改

现阶段还**没有足够证据**要求我们：

- 立刻删掉当前主线
- 立刻推翻 35.2 的主推荐
- 立刻把所有历史结果作废

## 5.3 现在最合理的判断

当前最合理的判断是：

1. **主线先保留**
2. **paper-aligned 对照必须并行存在**
3. **凡是声称“这是 Tsuyama 论文直接支持的 width/depth 结论”的地方，都必须改口**

---

## 6. 下一步建议

如果要继续把这个问题做实，最值得做的是：

### 方案 A：定向重跑 width/depth 小网格

固定：

- `404 / 660`
- 代表性窄宽和深通道
- 代表性 exosome 粒径

对比：

- `channel_angular_surrogate`
- `paper_aligned_phase_filter`

输出：

- route 排序
- strict coverage
- weighted 应用排序

### 方案 B：只在 Tsuyama 对照链中使用 paper-aligned

也就是：

- 工程主线继续用当前 surrogate
- 所有 paper-aligned 结论只用 `paper_aligned_phase_filter`

这样可以先把“工程推荐”和“论文对齐”两条线干净分开。

---

## 7. 最后一句话

> **这轮对照说明：当前 `depth_term` 额外作用是真实存在的，但在已测小网格里主要表现为几百分点到不到一成的 reference 差异。  
> 所以现在最需要修的是“解释与对齐口径”，而不是立刻推翻整个主线。**

