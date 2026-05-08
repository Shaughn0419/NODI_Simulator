# Tsuyama 2020 宽深记号与当前 reference surrogate 复核

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 日期：2026-04-15  
> 目的：核对 Tsuyama 2020 `Characterization of optical diffraction by single nanochannel for aL-fL sample detection in nanofluidics` 论文中 `2l / d` 的物理含义，确认当前工程对 `width / depth` 的理解是否有误。

---

## 1. 先给结论

结论分两层：

1. **宽度记号本身没有错**
   Tsuyama 论文里的通道宽度写成 `2l`，所以如果我们代码里的 `W` 表示**全宽**，那么 `W = 2l` 这层映射是对的。

2. **深度的物理角色不能直接等同成第二个横向孔径宽度**
   在 Tsuyama 2020 的 Eq. (3)-(9) 里，`d` 首先是**相位厚度 / 光程差厚度**，
   主要通过

   \[
   \theta = 2\pi (n_s - n_g) d / \lambda
   \]

   进入相位滤波函数。论文原式并没有一个和当前

   \[
   \mathrm{sinc}(H k_z / 2\pi)
   \]

   完全等价的“depth 作为第二横向狭缝宽度”的项。

所以更准确的判断是：

> **当前工程对 `width=W` 作为全宽的理解是正确的；  
> 但如果把当前 `depth=H` 的处理说成 Tsuyama 原推导本身，那是不严谨的。**

---

## 2. 论文里 `2l` 和 `d` 到底是什么

Tsuyama 2020 在 Theory 部分给出的核心对象是一个“phase filter”。

论文原文对应的关键结构是：

- 通道宽度：`2l`
- 通道深度：`d`
- phase filter：

  \[
  t(x', y') =
  \begin{cases}
  e^{i\theta}, & a-l \le x' \le a+l \\
  1, & x' < a-l \text{ or } x' > a+l
  \end{cases}
  \]

- 相位延迟：

  \[
  \theta = 2\pi (n_s - n_g) d / \lambda
  \]

这里最关键的是：

### 2.1 `2l` 是全宽，不是半宽

因为论文已经明确写了：

- channel width = `2l`
- 相位窗口区间是 `a-l` 到 `a+l`

所以：

- `l` 是半宽
- `2l` 才是实际通道全宽

这也和论文后面 `Fig. 3` 的说法一致：

- optimum channel width around `500 nm`
- corresponding to `0.5 ω0`

如果把 `l` 误当成 width，这个结论会变成 `250 nm` 量级，显然和论文图文不一致。

### 2.2 `d` 是光学厚度，不是第二个横向 slit width

Tsuyama 论文里的 `t(x', y')` 只在 `x'` 上发生阶跃切换。  
这意味着在该推导里：

- `width` 是横向 aperture / phase window 的尺寸
- `depth` 主要通过 `θ` 进入相位延迟

也就是说，论文的深度作用是：

> **深度改变 phase contrast**

而不是：

> **深度再作为一个独立的第二横向孔径，把 angular spectrum 再乘一个 `sinc`**

---

## 3. 当前工程主链是怎么写的

在 `reference_field.py` 里，当前 `channel_angular_surrogate` 的核心部分是：

- `phase_delay_rad = 2π * contrast * depth / λ`
- `width_term = sinc(W * kx / 2π)`
- `depth_term = sinc(H * kz / 2π)`

也就是说，当前主链里：

1. `H` 通过 `phase_delay_rad` 进入相位光栅响应
2. `H` 又通过 `depth_term` 再进入一个二维矩形角谱项

因此当前实现本质上是：

> **“薄相位光栅深度响应” + “二维矩形沟槽 angular surrogate”**

而不只是：

> **Tsuyama 2020 单通道 phase-filter 原式**

---

## 4. 这意味着哪些地方是对齐的，哪些地方不是

## 4.1 对齐的地方

### 宽度的全宽记号

如果代码里的 `channel.width_m = W` 被理解成实际通道全宽，那么：

- `W = 2l`

这和论文记号是兼容的。

### 深度进入 phase delay

当前主链里：

\[
\delta_{\mathrm{ref}} = 2\pi |\Delta n| H / \lambda
\]

这至少保留了和论文一致的核心结构：

- 深度影响 phase delay
- phase delay 决定 reference / diffraction 响应

## 4.2 不对齐的地方

### `depth_term = sinc(H k_z / 2π)` 不是论文原式

这条项意味着：

- 我们把通道深度同时看成了一个第二横向尺寸

而 Tsuyama 2020 原文的单通道 phase-filter 推导并没有这样写。

### 因此当前 width/depth 不是论文的一维 width + 光学深度，而是二维沟槽 surrogate

这不是一定“错”，但它的身份必须说清楚：

- 它可以是工程 surrogate
- 但不能再说成“这就是 Tsuyama Eq. (3)-(9)”

---

## 5. 对当前“宽和深怎么想”的直接判断

如果问题是：

> “我们把 Tsuyama 图里的 `2l` 当成代码里的 `W`，会不会错？”

答案是：

- **不会**
- 前提是 `W` 表示全宽，不是半宽

如果问题是：

> “我们把 Tsuyama 图里的 `d` 直接当成代码里的第二个 aperture dimension，会不会错？”

答案是：

- **按论文原推导来说，不严谨**
- 因为论文里的 `d` 首先是 phase thickness，不是第二横向 slit width

所以最准确的话应该是：

> **宽度这层主要是“记号是否把 `W` 当成全宽”的问题；  
> 深度这层主要是“我们当前是否把论文的一维 phase-filter 模型扩展成了二维沟槽 surrogate”的问题。**

---

## 6. 对后续分析的影响

这件事会影响两个判断。

### 6.1 对宽度最优点的判断

只要 `W = 2l` 这层保持一致，那么：

- 论文里 `optimum width ≈ 500 nm ≈ 0.5ω0`

这个判断就不需要整体平移。

### 6.2 对深度趋势的判断

如果我们想做 **paper-aligned diffraction validation**，那么更严谨的做法应该是：

- 保留 `d` 只进入 phase delay
- 不把 `d` 再额外当成第二横向 sinc 项

否则当前模型里的 depth trend 会混进：

1. 薄相位光栅深度响应
2. 二维 aperture / groove angular spectrum

这和 Tsuyama 2020 的单通道 phase-filter 理论不再是同一件事。

---

## 7. 建议的表述方式

以后在文档里最好固定这样写：

1. **Tsuyama 2020 原式中：**
   - width = `2l` = 全宽
   - depth = `d` = 相位厚度

2. **当前工程主线中：**
   - `W` 与论文全宽兼容
   - `H` 除了进入 phase delay 外，还进入了额外的二维 angular surrogate

3. **因此：**
   - 宽度记号没错
   - 深度建模不是“照抄论文”，而是“在论文相位厚度语义上再加了一层工程 surrogate”

---

## 8. 最后一条直接结论

> **你提醒的这个点是对的：  
> 真正需要警惕的不是 `2l` 和 `W` 的对应，而是不要把论文里的 `d` 错当成和当前 `H·k_z` 同语义的第二横向孔径尺寸。**

