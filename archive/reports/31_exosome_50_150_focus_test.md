# 50–150 nm Exosome Focus Test

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 文档状态：历史参考。本文记录的是 focused 404 结果库的生成任务；如果你要看当前结论，请优先查看 [archive/reports/32_exosome_50_150_focus_404_analysis.md](./32_exosome_50_150_focus_404_analysis.md)。

## 目标

运行一个面向 `exosome 50–150 nm` 粒径带的定向 precompute，用更高的 `1000 events/case` 复核以下问题：

- 对 `50–150 nm`，`404 / 488 / 532 / 660 nm` 四种波长谁更占优
- 哪一类通道几何更适合作为这一粒径带的优先设计区
- 之前基于 `100 events/case` 得到的趋势在高事件数下是否保持一致

## 固定扫描范围

- 粒径：`50–150 nm`，`10 nm` 步进
- 粒子类型：仅 `exosome`
- 通道宽度 `W`：`700–1500 nm`，`100 nm` 步进
- 通道深度 `H`：`500–1000 nm`，`100 nm` 步进
- 波长：`404 / 488 / 532 / 660 nm`
- 每个 case：`1000 events`
- worker：`24`

总 case 数：

- `11 diameters × 9 widths × 6 depths × 4 wavelengths = 2376 cases`

## 运行命令

在仓库根目录执行：

```bash
python dashboard/precompute.py \
  --grid focus_50_150 \
  --particle-profile exosome_50_150 \
  --tag exosome_50_150_focus_404 \
  --workers 24 \
  --freeze-probe-report \
  --output results/
```

## 结果文件前缀

本次任务的输出前缀固定为：

```text
focus_50_150_exosome_50_150_focus_404
```

说明：为避免误续跑旧的三波长 checkpoint，本次四波长任务统一使用新的 `--tag exosome_50_150_focus_404`。

重点文件：

- `results/focus_50_150_exosome_50_150_focus_404_summary.csv`
- `results/focus_50_150_exosome_50_150_focus_404_compact.pkl`
- `results/focus_50_150_exosome_50_150_focus_404_meta.json`
- `results/focus_50_150_exosome_50_150_focus_404_result_health.json`
- `results/focus_50_150_exosome_50_150_focus_404_freeze_probe.json`
- `results/focus_50_150_exosome_50_150_focus_404_progress.json`
- `results/focus_50_150_exosome_50_150_focus_404_checkpoint/`

## 运行要求

- 保持默认 `resume` 与 `checkpoint` 开启，不要手动关闭
- 如果线程中断，优先直接重跑同一条命令，让任务从 checkpoint 继续
- 中断恢复时必须保持同一个 `--tag exosome_50_150_focus_404`
- 中断恢复时不要删除已有的 `progress.json`、`checkpoint/` 或 `chunks/`
- 不要改扫描范围、不要改事件数、不要改 worker 数
- 不要把这次结果覆盖成标准 `fine_full_range_*` 主结果库

## 进度与续跑说明

本次任务的主进度文件固定为：

```text
results/focus_50_150_exosome_50_150_focus_404_progress.json
```

续跑所依赖的 checkpoint 目录固定为：

```text
results/focus_50_150_exosome_50_150_focus_404_checkpoint/
```

如果计算被打断：

1. 不要改命令参数
2. 不要改 `--tag`
3. 不要删 checkpoint 目录
4. 直接重新执行同一条命令

默认情况下，precompute 会自动尝试从已有 checkpoint 继续。

## 完成判据

满足以下条件才算完成：

- `progress.json` 的 `status` 为 `completed`
- `summary.csv`、`compact.pkl`、`meta.json` 已生成
- `meta.json` 中 `n_events_per_case = 1000`
- `meta.json` 或日志中显示总 case 数为 `2376`

## 完成后需要回答的问题

跑完后请基于 `summary.csv` 回答：

1. 在 `50–150 nm` 整体上，`404 / 488 / 532 / 660 nm` 四种波长谁最适合作为主波长，谁应作为第二优先波长
2. 对 `50–100 nm`、`100–150 nm` 两个子区间，波长优先级是否发生变化
3. 哪个 `W/H` 区域更像“平台”，而不是单点尖峰
4. 与之前 `100 events/case` 的判断相比，哪些结论被强化了，哪些结论被推翻了

## 跑完后要输出的结论

结果分析不要只停留在“哪个单点最高”，而要给出面向选型的结论。至少要形成下面这 6 类结论：

### 1. 总体波长结论

必须明确回答：

- `50–150 nm` 整体范围内，主推荐波长是哪一个
- 第二推荐波长是哪一个
- 其余较低优先级波长是否还有保留价值，还是可以明显降级

输出时要避免只说“某个单点最高”，而要说明：

- 是因为平台更宽
- 还是因为过 gate 的 case 更多
- 还是因为稳定检出率更高

### 2. 分粒径区间结论

必须分别给出以下 3 段的判断：

- `50–80 nm`
- `90–110 nm`
- `120–150 nm`

每一段都要回答：

- 四种波长的优先级排序
- 当前最推荐的几何区间
- 这一段是否已经形成“可用平台”，还是仍然只是“相对更优但整体仍难”

### 3. 通道几何结论

必须把几何结论写成区间，而不是只写一个点：

- 优先宽度区间 `W`
- 优先深度区间 `H`
- 是否存在一个跨多个粒径都还成立的公共平台
- 是否存在明显的“浅通道更优”或“中等深度更优”趋势

如果没有宽平台，也要明确写：

- 哪些高分点是尖峰点
- 哪些区域对 `W/H` 扰动更敏感

### 4. 工程可行性结论

不能只看 `engineering_score` 或 `final_engineering_score`，还要把下面这些量一起解释：

- `engineering_gate_passed`
- `engineering_basis_detection_rate`
- `engineering_basis_stable_detection_rate`
- `engineering_basis_phase_flip_fraction_wilson_ub`
- `engineering_basis_mean_peak_margin_z`

需要明确说明：

- 哪些推荐区域是真的“更容易通过 gate”
- 哪些区域只是分数看起来高，但 gate 或稳定性并不稳

### 5. 与旧结论对比

必须和之前基于 `100 events/case` 的判断做对照，至少回答：

- `488 nm` 作为 `50–150 nm` 主波长的判断，是被强化了还是被削弱了
- 新加入的 `404 nm`，整体与分区间中的竞争位置如何，是否值得进入后续主设计集合
- `532 nm` 在 `130 nm` 左右的竞争力，是被强化了还是被削弱了
- `660 nm` 在 `80–100 nm` 一带偶尔出现的高点，是否仍然成立，还是更像采样波动
- 之前怀疑是尖峰的区域，在 `1000 events/case` 下有没有变成平台

### 6. 最终设计建议

最后必须压缩成可以直接指导下一步实验的建议，格式建议固定为：

- 默认主设计：
- 第二备选设计：
- 若样本偏小粒径时的设计：
- 若样本偏大粒径时的设计：
- 当前不建议优先投入的波长/几何：

这里的“设计”必须同时包含：

- 波长
- 通道宽度范围
- 通道深度范围

## 跑完后建议的分析步骤

为了保证结论一致，建议按下面顺序分析 `summary.csv`：

1. 先看整体 `50–150 nm` 全集
2. 再按粒径分成 `50–80 / 90–110 / 120–150`
3. 每一段先按波长聚合比较，再看 `W/H` 热图或 pivot
4. 优先找“连续较优区域”，不要先盯单个最高点
5. 最后再回头检查 top case 周围 `±100 nm` 的邻域是否也维持较好表现

## 建议重点看的聚合方式

建议至少做下面这些聚合表：

- 按 `wavelength_nm` 聚合：
  看每个波长的平均 `final_engineering_score`、平均 `engineering_score`、gate 通过比例、平均稳定检出率
- 按 `particle_diameter_nm + wavelength_nm` 聚合：
  看不同粒径下波长优先级如何变化
- 按 `wavelength_nm + width_nm + depth_nm` 聚合：
  找整体最佳平台区
- 按 `particle_diameter_nm + width_nm + depth_nm` 聚合：
  看某一粒径下的最佳几何是否稳定

如果只能做少量表，优先顺序是：

1. `particle_diameter_nm × wavelength_nm`
2. `wavelength_nm × width_nm × depth_nm`
3. top case 邻域比较

## 最终交付建议格式

建议最终把结论整理成下面这个结构，方便直接审阅：

### A. 一句话结论

例如：

```text
在 1000 events/case 的 focused sweep 下，50–150 nm exosome 的总体选型若仍由 488 nm 领先，
则需要同时交代新加入的 404 nm 是成为补充波长、竞争波长，还是可以明确降级。
```

### B. 分区间结论

- `50–80 nm`：
- `90–110 nm`：
- `120–150 nm`：

### C. 设计建议

- 默认主设计：
- 第二备选：
- 小粒径优先设计：
- 大粒径优先设计：

### D. 风险与不确定性

- 哪些区域仍然没有形成稳定平台
- 哪些结论虽然更清楚了，但仍需后续更高保真验证
- 是否还需要进一步做粒径分布加权分析

## 配置来源

这次任务使用仓库里已经写好的专用配置：

- profile：`exosome_50_150`
- grid：`focus_50_150`

它们已经固定为本任务需要的粒径、几何、波长和 `1000 events/case` 设置。
