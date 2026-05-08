# dashboard/panels/noise_detection_explorer.py — Noise & Detection Explorer

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。

> 2026-04-07 补充：Noise & Detection Explorer 当前默认围绕标准四波长结果库 `404 / 488 / 532 / 660 nm` 解释噪声、检出与 gate 结论，相关统计均对应 `55296 cases` 的 full-range 主库。

> 阶段 B 更新（2026-04-07）：当前页已开始收口到“标准结果库解释页”定位。页面会优先把当前选中 case 锚定到标准 `fine_full_range_*` 结果库，并在页首显示 recommendation / gate / stable-detection / freeze 这组结果库结论；如果 session 中存在工程调试参数，只作为提示，不再作为默认阅读来源。

## 当前使用方式

- 文档定位：Noise & Detection Explorer 专题
- 推荐阅读时机：当你要解释噪声、阈值、detect/miss 与 gate 边界时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/panels/noise_detection_explorer.md](../../dashboard/panels/noise_detection_explorer.md)
- [22_dashboard_interference_explorer.full.md](./22_dashboard_interference_explorer.full.md)
- [20_dashboard_inspector.full.md](./20_dashboard_inspector.full.md)

## 页面职责

这是一张专门的“detect / miss 机制页”。

它不负责解释：

- 粒子本身的本征散射
- reference 为什么会放大 clean signal
- 全局设计区哪里最好

它只回答一个主问题：

**为什么理论上存在的 clean pulse，最后会变成 detect / miss 两种完全不同的实验结果？**

---

## 这页在整条链里的位置

推荐顺序：

`Principle Guide -> Mie Explorer -> Interference Explorer -> Noise & Detection Explorer -> Design Explorer -> Case Inspector`

其中这页正好处在：

`clean signal -> noisy trace -> threshold -> detect/miss`

这一步。

---

## 页面输入

### 检测主线参数

- 材料
- 粒径（当前统一为 `40–300 nm`、`10 nm` 步进）
- 波长
- `W`
- `H`
- `noise_std`
- `noise_model`
- `drift_slope`
- `threshold_sigma`
- `velocity`
- `include_diffusion`
- 批量事件数

### 信号上下文参数

这部分默认后置，不是本页主线：

- `rho`
- `reference_model`
- `phase_model`
- `collection_angle_model`
- `pulse_detection_mode`
- `detection_decision_mode`
- `readout_model`
- `lockin_time_constant`
- `ref_alpha / ref_beta / ref_gamma`
- `coupling_model`
- `beam_waist_y`

它们的作用是给当前 noise/detection 判断一个 clean-signal 背景。

当前这页解释 `lockin_time_constant` 时，默认口径按下面理解：

- Tsuyama 2022 / 2024：实验时间常数范围为 `1–2 ms`
- 当前页面默认值：`1 ms`
- 这样做是为了和真实机器可直接设置的 `1 ms / 2 ms` 档位一致

当前页面中，控件、摘要卡和图表标题也已统一为中文主标签，例如：

- `噪声标准差`
- `阈值倍数`
- `检出率 / 漏检率 / 平均峰高`
- `单事件轨迹：clean / raw / readout / threshold 对照`

当前页面同样已经取消正文里的跨页跳转按钮，改成在摘要和主图后直接给出“本页结论”，优先说明当前点主要是：

- 峰高余量不够
- 阈值或噪声过高
- transit-bandwidth 受限
- 还是已经进入稳健 detect 区

这页最近又做了一轮减法：顶部不再同时铺开过多指标，而是优先显示最直接决定 detect/miss 的 6 个量：

- 检出率
- 峰高/阈值比
- 平均阈值
- 平均峰高
- 双通道检出率
- 带宽受限占比

正负峰均值/占比、`A_ref / g_ref / E_sca normalized` 和噪声上下文现在都后置到按需展开的上下文表里。
最近这一轮又进一步删掉了这些表：当前检测上下文表和扫描原始数据表都已移除，只保留压缩后的上下文摘要和趋势解释。

最近这一轮又往前推进了一步：

- **诊断摘要前置**：`本页结论` 之后，页面现在会直接给出 `当前检测区间 / 主要瓶颈 / 优先比较` 三个诊断标签
- **下一步建议只在本页内收口**：不再让用户跳页，而是直接说明更该先查 `noise/threshold`、`single vs paired`，还是 `lockin tau / 流速 / beam waist`
- **三段主线编号化**：现在主页面按 `1. 单事件 trace -> 2. 批量结果 -> 3. 参数扫描` 顺序展开，更像一条连续诊断链
- **参数扫描趋势补充**：扫描图下方现在还会直接说明“什么趋势代表真的变好”，例如噪声降低时应同时看到检出率上升和阈值下降，流速升高时若检出率掉得很快则更像 transit/bandwidth 受限
- **判断模板补充**：`本页结论` 下方现在还会额外给出 `什么算真变好 / 什么是假变好 / 先信什么证据` 三条短框，把 detect/miss 页真正收口成诊断页

---

## 页面输出

### 1. 顶部摘要卡

主卡片包括：

- `Detection rate`
- `Miss rate`
- `Mean threshold`
- `Mean peak height`
- `CV`
- `Single-channel detection rate`
- `Paired-channel detection rate`
- `A_ref / E_sca_norm`
- `theta_det_deg`

这些量优先回答：

- 当前到底是“稳健可检出”
- 还是“边缘可检测”
- 还是“多数事件都测不到”
- 当前是“信号本身太弱”，还是“相位/角度/阈值口径把它推到了检测边缘”

### 2. 诊断摘要

在顶部结论之后，页面现在会再给三条更可执行的诊断：

- `当前检测区间`：稳健可检测区 / 边缘可检测区 / 阈值下方
- `主要瓶颈`：读出带宽限制 / 峰值余量不足 / 事件间波动过大 / 当前没有单一硬瓶颈
- `优先比较`：`single vs paired` 或 `noise/threshold scan`

这一步的目标不是再报更多数字，而是先把当前点归类。

### 3. 单事件 trace

主图把：

- `clean signal`
- `raw noisy signal`
- `NODI readout`
- `threshold`

叠在一起，回答单事件层面到底发生了什么。

### 4. 批量 detect / miss 结果

包括：

- detected vs missed 数量
- detected 事件的最佳峰高分布

这部分帮助区分：

- 是整体都不行
- 还是只是有一部分事件掉到阈值以下

用于核对 `A_ref / g_ref / E_sca normalized / Mean threshold / Noise std` 的小表，以及正负峰分组统计，都已经后置到按需展开；主页面现在优先保留结论提示和 detect/miss 图。

当前页顶部也会显式标出：

- 相位模型
- 检测角模型
- 角谱收集模式
- 散射投影模式
- 脉冲检测模式
- 最终判决模式

这样在比较不同 detect/miss 结果时，不会把“物理观测模型变化”误当成单纯的噪声变化。

### 5. 参数扫描：什么最容易把当前点拖出可检测区

支持扫描：

- `noise_std`
- `threshold_sigma`
- `velocity`

输出：

- `detection_rate`
- `single_channel_detection_rate`
- `paired_channel_detection_rate`
- `mean_threshold`
- `mean_peak_height`
- `mean_positive_peak_height`
- `mean_negative_peak_height`
- `positive_peak_fraction`
- `negative_peak_fraction`
- `CV`
- `hit_rate_at_fixed_false_alarm`
- `roc_auc_event_vs_background`
- `d_prime_event_vs_background`

目的不是做最终设计评分，而是定位“谁在拖低检出”。

最近这一轮之后，参数扫描的默认阅读顺序已经进一步收口成：

- 先看 `detection_rate` 是不是明显上升或下降
- 再看 `mean_peak_height - mean_threshold` 的余量是在变宽还是变窄
- 最后再看 `CV`，判断问题是整体强弱，还是事件间波动

页面显示层当前也统一改成“中文解释 + 符号”的口径，例如：

- `检测阈值 (threshold)`
- `读出噪声标准差 (noise_std)`
- `阈值倍数 (threshold_sigma)`
- `参考场幅值 (A_ref)`
- `归一化散射场幅值 (E_sca)`

这样单事件 trace、批量摘要和参数扫描三块读起来会更一致，不需要在中文解释和内部变量名之间来回切换。

---

## 如何阅读这页

页面顶部的 `这页怎么用` 现在默认折叠，主页面优先保留摘要卡、单事件 trace 和批量 detect/miss 结果。

### 情况 1：clean signal 很高，但 detection rate 仍然低

优先怀疑：

- 事件间位置波动
- diffusion
- 阈值设置过高
- 噪声或漂移把边缘事件吃掉

### 情况 2：threshold 随噪声一起明显上升

说明当前检测性能主要被背景噪声主导。

### 情况 3：提高 velocity 后 detection rate 降低

通常意味着 pulse 变窄，峰更容易被采样和阈值条件共同压低。

### 情况 4：出现负脉冲或 polarity 翻转

这通常不是“检测器坏了”，而是相位条件改变后，clean signal 的符号发生了翻转。当前页面默认使用 `absolute` 脉冲检测，所以这类事件仍可作为有效响应被统计，但你仍应结合带符号单事件轨迹判断它属于哪种干涉条件。

本轮页面摘要里又补了极性分组统计：

- `mean_positive_peak_height`
- `mean_negative_peak_height`
- `positive_peak_fraction`
- `negative_peak_fraction`

这样当 `mean_signed_peak_height` 接近 0 时，你现在可以区分：

- 是所有峰本来就很弱
- 还是正峰和负峰都不小，但在平均时互相抵消了

当前 dashboard 默认的相位层已经从单纯 `axial_path` 进一步升级为
`relative_surrogate`，也就是在深度路径差之外，再加入沿流动方向穿焦
造成的简化 Gouy-like 相位趋势。因此这里看到的 polarity 翻转，通常不再只是
“z 位置变化”，也可能是粒子经过焦点附近时相对相位在变化。

当前页面默认还会在噪声之后经过 `lockin_surrogate` 读出层：

- `signal_raw_noisy`：原始干涉信号加噪后的轨迹
- `signal_detect_pre_post`：readout 之后、post-readout 噪声之前的检测轨迹
- `signal_pod`：低频 / POD surrogate 通道
- `signal_nodi`：post-readout 之后、真正进入阈值和峰提取的 NODI surrogate 通道

因此本页里的 detect / miss，已经不是直接在 raw noisy trace 上做的。

当前这层 `lockin_surrogate` 也已经显式包含两路参考频率：

- `pod_lockin_frequency_Hz`
- `nodi_lockin_frequency_Hz`

并且现在还显式包含：

- `pod_reference_phase_rad / nodi_reference_phase_rad`
- `readout_observable_mode = in_phase | magnitude`
- `signal_nodi_i / signal_nodi_q / signal_nodi_mag`

所以这页现在不只是“时间常数 + 串扰”页面，也能表达“频率分离越明显，cross-demod leakage 越弱”的最小趋势。
同时也能表达“参考相位怎么把读出从 I 分量转到 Q 分量”，以及“为什么 magnitude 模式会更像幅值锁相，而不是保留原始符号”。

本轮又补了一层 POD 频率响应 surrogate：

- `pod_frequency_response_model`
- `pod_frequency_response_reference_Hz`
- `pod_frequency_response_exponent`

当前默认是 `inverse_power_surrogate`。它会让 POD lane 额外乘一个近似
`(f_ref / f_pod)^exponent` 的 gain，并裁剪到固定上下限。这样这页现在还能表达：

- POD 调制频率越低，`signal_pod_true` 越强
- POD 调制频率越低，POD lane 中的 `signal_pod_leak` 也会更强
- 因而“低频更容易把 POD/NODI 分离变差”已经不再只是文档假设，而是当前读出链里可调、可看的显式参数

这一轮又把 NODI lane 的 transit-time 约束显式接进来了：

- `nodi_transit_response_model`
- `nodi_transit_bandwidth_Hz`
- `nodi_transit_bandwidth_gain`
- `nodi_bandwidth_limited_fraction`
- `nodi_lockin_bandwidth_Hz`

它的当前最小语义是：事件越快，`f_transit ~ 1 / transit_time` 越高；如果
`lockin_time_constant_s` 太慢，等效 `f_lockin ~ 1 / (2π\tau)` 太低，那么
NODI lane 会被额外压低。这样本页现在不只会显示“噪声大/阈值高”，也能显示
“这个事件本来就太快，NODI 读出带宽跟不上”。

因此当前默认讨论这个效应时，应优先把 `1 ms` 当作主工作点，再比较 `2 ms` 是否会把结论明显推偏。

当前噪声链也已经拆成两层：

- `pre-readout`：由 `noise_std / shot_noise_scale / noise_model / drift_slope` 控制，作用在原始干涉信号层
- `post-readout`：由 `post_readout_noise_std / post_readout_drift_slope` 控制，作用在 `lockin_surrogate` 之后、阈值之前

其中 `shot_noise_scale` 不是固定底噪，而是会随 `I_baseline / I_det` 一起变化的 shot-noise surrogate，所以这页现在既能看固定电子噪声，也能看“参考场越强，raw 层波动也越大”的情况。

本轮又把这条链补成了可审计 diagnostics：

- `mean_I_baseline`
- `mean_shot_noise_std`
- `mean_shot_noise_reference_dominated_fraction`
- `mean_reference_to_scattering_amplitude_ratio`

所以这页现在不只会说“噪声变大了”，还可以直接判断：

- 这次 shot noise 是不是主要由 reference baseline 在主导
- 当前 case 是否仍处在 `|E_ref| > |E_sca|` 的弱散射干涉区间

当前 detect/miss 页面还会显式给出“固定误报率命中率 / ROC-AUC / d′”这组三个判别量。它们不是替代 `detection_rate`，而是补一层更贴近工程筛选的问题：

- 如果把背景误报率固定在一个小值，真正事件还能被命中多少？
- 事件分布和背景分布到底分得开吗？
- 这个 case 是“平均能看到”，还是“和背景几乎混在一起”？

本页现在还会额外给出三类帮助解释 detect / miss 的量：

- `mean_transit_time`
  看粒子是不是根本没有在主 waist 区域待够久
- `mean_local_snr`
  看即使事件到了焦区，读出链本地 SNR 是否仍然偏低
- `mean_nodi_transit_bandwidth_Hz / mean_nodi_transit_bandwidth_gain / mean_nodi_bandwidth_limited_fraction`
  看 detect/miss 是不是已经被 NODI lane 的 transit-bandwidth 约束推到了边缘
- `single_channel_detection_rate / paired_channel_detection_rate`
  看差异主要出在“单通道过阈”还是“配对判决更严格”
- `paired_detection_rate`
  看 NODI 峰能否在 POD 通道找到对应脉冲，帮助判断双通道 lock-in surrogate 是否一致

---

## 为什么不单独做“纯噪声页”

因为实验上真正关心的不是噪声本身，而是：

**噪声怎样改变 detect / miss 的结果。**

如果只做纯噪声页，就会丢失：

- clean pulse 的起点
- threshold 的作用
- detect/miss 的最终表现

所以这里把它明确做成 `Noise & Detection Explorer`。

---

## 关联后端

- `dashboard/signal_backend.py`
  - `compute_noise_detection_case()`
  - `build_event_trace_dataframe()`
  - `build_detection_scan_dataframe()`

这些后端函数保证本页里的 trace、threshold 和 detect/miss 逻辑与主模拟器一致。

虽然本页主显示仍聚焦在 `clean / raw / readout / threshold`，但 `build_event_trace_dataframe()` 现在也会把 `phi_material / phi_projection / phi_ref / delta_phi_ref` 这组相位诊断一起带出来，便于跨页复核 detect / miss 是否和相位条件变化有关。

---

## 2026-04-03 文案补充

- 单事件轨迹图的图例已统一为 `clean signal / 含噪信号 / 阈值`。
- 轨迹图标题已改成“单事件轨迹：clean / 含噪 / 阈值 对照”。
- 扫描图测试口径已同步到中文轴标题，如“噪声标准差”“流速 (mm/s)”和“平均阈值”。
## 2026-04-07 D / E 收口

- 本页顶部锚点卡片已改为复用 `render_workflow_anchor_summary()`。
- 本页的数据来源提示已改为复用 `render_workflow_source_notice()`。
- 页面职责进一步收窄为：
  - 解释当前标准 case 为什么会走到当前的 detection / gate / freeze 结论
  - 展示本页专属的 noise / threshold / detect-miss 分析

## 2026-04-07 来源提示统一

- `Noise & Detection Explorer` 页头现在改为共享的 workflow case/source 面板。
- 统一术语说明后，本页的重点更明确：解释 clean signal 为什么会落到 detect / miss / freeze / gate 这些实验结论上。
