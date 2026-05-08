# dashboard/panels/interference_explorer.py — Interference Explorer

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。

> 2026-04-07 补充：Interference Explorer 当前默认围绕标准四波长结果库 `404 / 488 / 532 / 660 nm` 解释干涉链路，相关推荐与统计均对应 `55296 cases` 的 full-range 主库。

> 阶段 B 更新（2026-04-07）：当前页已开始收口到“标准结果库解释页”定位。页面会优先把当前选中 case 锚定到标准 `fine_full_range_*` 结果库，并在页首显示 recommendation / gate / freeze / detection 这组结果库结论；如果 session 中存在 live 参数，只作为工程调试提示，不再与主流程结论平级。

当前页默认已经不是旧版的“单角度 + 正实数散射代理”口径，而是：

- `channel_diffraction` 决定角谱中心
- `pupil_slit_surrogate` 对 `theta + phi` 角谱做最小二维收集
- `parallel` 投影保留更贴近干涉检测的复场分量
- `relative_surrogate` 把 `x-z` 平面内的最小二维路径差和沿流动方向的简化 Gouy 相位一起带进 clean signal
- `cross_section_surrogate` 把参考场从 case 级标量推进到 event 级 `E_ref(x,z)` surrogate

因此这里展示的 `E_sca normalized`、`peak cross-term` 和 `heterodyne gain`，现在更接近“有限角收集后的等效干涉响应”。

当前页面已经取消正文里的跨页跳转按钮，改成在主摘要和关键图后直接给出“本页结论”。这条结论会优先回答：

- 当前是不是 reference 放大的 heterodyne 主导区
- 纯散射项是否已经大到不能再把它只看成干涉增强
- 当前 overlap / projection / OPD 口径是否还处在可放心解释的范围

最近这一轮又进一步把顶部收成了“结论 + 趋势判断”：

- overlap / freeze 的长说明不再直接铺在主页面，而是后置到 `查看 overlap / freeze 口径说明`
- 主页面会额外给三条短诊断：
  - `当前放大机制`
  - `解释可信度`
  - `看趋势先盯`
- 也就是说，这页现在不只告诉你“当前最好”，还会告诉你“什么样的变化才算 reference 放大在变好”
- **扫描趋势翻译补充**：单变量扫描图下方现在还会直接给出“怎么看这条扫描趋势”，把 `A_ref / peak cross-term / |E_sca|^2 / heterodyne gain` 的相对变化翻译成一句结论
- **判断模板补充**：`本页结论` 下方现在还会额外给出 `什么算真变好 / 什么是假变好 / 先信什么证据` 三条短框，避免把“峰值变大”直接误读成参考场设计更优

同时，这一页现在把投影模式验证、reference consistency、OPD/Gouy freeze 统一后置到一个“高级诊断”展开区。默认主视图只保留：

- 顶部摘要卡
- 本页结论
- clean trace 分解
- 峰值构成
- 单变量扫描

这样页面先回答“为什么这个 clean pulse 会强”，再把审计工位留给需要核边界的人。
最近这一轮又继续做了减法：当前点关键量长表和扫描原始数据表都已从主页面移除，只保留结论、主图、峰值构成和高级诊断里的必要审计图。

## 当前使用方式

- 文档定位：Interference Explorer 专题
- 推荐阅读时机：当你要解释 reference 如何把本征散射转成 clean signal 时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/panels/interference_explorer.md](../../dashboard/panels/interference_explorer.md)
- [26_dashboard_mie_explorer.full.md](./26_dashboard_mie_explorer.full.md)
- [23_dashboard_noise_detection_explorer.full.md](./23_dashboard_noise_detection_explorer.full.md)

## 页面职责

这是一张专门的“桥接页”。

它不回答：

- 粒子本身散射强不强
- 最终 score 高不高
- 最后能不能检出

它只回答一个主问题：

**粒子的本征散射 `E_sca` 进入系统后，为什么会变成一个被 reference 放大的 clean interferometric pulse？**

---

## 这页在整条链里的位置

推荐顺序：

`Principle Guide -> Mie Explorer -> Interference Explorer -> Noise & Detection Explorer -> Design Explorer -> Case Inspector`

其中：

- `Mie Explorer` 负责“粒子本身”
- `Interference Explorer` 负责“系统怎样把粒子散射变成 clean signal”
- `Noise & Detection Explorer` 负责“为什么 clean signal 不一定能检测到”

---

## 页面输入

### 基础 case

- 材料
- 粒径（当前统一为 `40–300 nm`、`10 nm` 步进）
- 波长
- 通道宽度 `W`
- 通道深度 `H`
- 粒子相对位置 `x/(W/2)`、`z/(H/2)`

### 系统放大参数

- `rho`
- `reference_model`
- `ref_alpha / ref_beta / ref_gamma`
- `coupling_model`
- `beam_waist_y`

这些参数默认继承当前的 live 或默认系统参数，但本页修改只作用于本页，不会自动重跑整个全局 sweep。

当前页面中，控件与图表的高频标签也已统一为中文主标签，例如：

- `参考场模型`
- `位置耦合模型`
- `脉冲峰值处的组成分解`
- `通道宽度 W / 通道深度 H`

---

## 页面输出

### 1. 顶部摘要卡

直接给出最重要的量：

- `Csca`
- `E_sca normalized`
- `A_ref`
- `Peak clean signal`
- `Heterodyne gain`
- `Coupling factor`

这些卡片的作用是先回答：

- 当前是不是典型的弱散射 heterodyne 放大区
- clean signal 的增强主要来自 reference，还是来自粒子本身已经很强
- 当前 `path_opd_model` 是默认冻结主线，还是 roundtrip 对照口径
- 当前 `path_opd_model` 是否已经切到 `wall_referenced_gap_surrogate` 这条最近壁 gap 对照口径

顶部 summary 现在还会显式导出：

- `path_opd_model / path_opd_reference_plane / path_opd_z_geometry_factor / path_opd_z_reference_mode`
- `path_opd_default_model / path_opd_model_role / path_opd_default_frozen / path_opd_freeze_status`
- `interference_overlap_mode / interference_cross_term_mode`
- `interference_overlap_status / interference_overlap_factor_abs / interference_overlap_factor_phase_rad`
- `peak_phi_focus_crossing_rad / peak_phi_gouy_ref_rad / peak_phi_gouy_sca_rad / peak_delta_phi_gouy_rad`

现在顶部还会再给一句趋势判断：

- 如果某个变量变化时 `A_ref` 提升，并且 `peak cross-term` 继续压住 `|E_sca|^2`
  说明系统还在健康的 heterodyne 放大区
- 如果 clean peak 变强主要是因为 `|E_sca|^2` 抬头
  说明更像粒子本身够强，而不是 reference 放大在变好

### 2. Clean Trace 分解

主图把这条链完整展开：

- `A_env`
- `A_sca(t)`
- `|E_sca|^2`
- `2Re(E_ref·E_sca*)`
- `clean signal`

本轮之后，trace_df 里还会并排保留：

- `cross_term`
- `cross_term_collapsed`
- `cross_term_joint`

因此页面已经能直接审计：

- 当前 clean signal 用的是哪条交叉项口径
- joint overlap 相比默认 collapsed 口径偏了多少

在主图之后，页面还会把这些量压缩成“本页结论” callout，避免用户必须自己从多张图里再拼一次最终判断。

这一图是本页的核心。

### 3. 峰值构成

在 pulse 峰值时刻，把：

- 干涉交叉项
- 纯散射项
- 总 clean peak

放在一张图上，帮助用户快速判断当前系统是不是 reference 主导。

右侧的当前点解释仍然保留在主页面，但用于核对的 `g_ref / Peak A_env / Peak A_sca / 初始 x,z` 小表已经后置到按需展开，避免主页面一打开就像报告表。

本轮后，这个按需展开的小表还新增了：

- `Reference spatial mode`
- `Peak A_ref(local)`
- `Peak phi_material`
- `Peak phi_projection`
- `Peak phi_beam`
- `Peak phi_path_x`
- `Peak phi_path_z`
- `Peak phi_path`
- `Peak phi_ref`
- `Peak Δφ_ref`
- `Path OPD model`
- `Path OPD reference plane`
- `Path OPD z factor`

用来直接检查“材料散射相位”“投影后进入干涉的相位”“参考场局部变化”和“相对相位”是不是正在驱动当前 clean pulse。

### 4. 单变量扫描

支持扫描：

- `rho`
- `W`
- `H`
- `wavelength`

输出：

- `A_ref`
- `E_sca normalized`
- `Peak clean signal`
- `Heterodyne gain`

当扫描轴为 `wavelength` 时，页面现在还会额外生成一张 phase-scan 图，直接并排展示：

- `peak_phi_material_rad`
- `peak_phi_projection_rad`
- `peak_delta_phi_ref_rad`

这部分的目的不是做设计排名，而是看“哪个变量正在放大 clean signal”。
对波长扫描来说，它还承担另一层诊断职责：帮助确认信号极性变化到底更接近“材料散射相位变化”还是“参考相位/路径相位变化”。

最近这一轮之后，这块扫描图的推荐阅读方式也已经固定下来：

- 先看 clean 峰值整体是升还是降
- 再看 `A_ref` 和 `peak cross-term` 有没有一起变强
- 最后看 `|E_sca|^2` 是不是开始反客为主

也就是说，这页现在不仅会说“哪边更强”，还会明确告诉你“这种变强到底算不算 heterodyne 条件真的更好”。

页面显示当前也统一收口到“中文解释 + 符号”的风格，例如：

- `参考场幅值 (A_ref)`
- `归一化散射场幅值 (E_sca)`
- `干涉交叉项峰值 (peak cross-term)`
- `散射平方项峰值 (peak |E_sca|^2)`
- `干涉放大倍数 (heterodyne gain)`
- `等效检测角 (theta_det)`

这样用户在读页面时，不需要先记住内部变量名再去反推它的物理含义。

当前 case 峰值摘要里也已经把 beam phase 拆开展示：

- `Peak phi_gouy (rad)`
- `Peak phi_curv (rad)`

因此现在页面上不再只看到一个总的 `phi_beam`，而是能分辨“穿焦项”和“曲率项”分别有没有在主峰附近起作用。

### 5. 高级诊断：投影 / reference consistency / freeze 审计

这部分现在统一折叠到主页面底部，不再和主线图表并列抢注意力。

它固定：

- 粒子位置
- 通道几何
- reference / coupling / phase 模型

只同时比较三条散射投影路径：

- `parallel`
- `perpendicular`
- `intensity_proxy`

输出的不是普通 peak，而是 `dominant clean peak`，也就是按 `|clean_signal|` 取主极值后保留其符号。这样即使出现负脉冲，也不会被简单的正峰搜索掩盖。

当前表和图会显式给出：

- `projection_mode_role`
- `phase_aware`
- `dominant_peak_polarity`
- `dominant_peak_phi_material_rad`
- `dominant_peak_phi_projection_rad`
- `dominant_peak_delta_phi_ref_rad`

用途是把三条路径的边界冻结清楚：

- `parallel`：当前主物理解释路径
- `perpendicular`：偏振/投影对照路径
- `intensity_proxy`：legacy compatibility / regression 路径，不再作为主物理解释路径

### 6. overlap 审计

当前页面 summary 还会显式保留：

- `interference_overlap_mode`
- `interference_cross_term_mode`
- `interference_overlap_status`
- `interference_overlap_agreement_status`
- `interference_overlap_default_role / interference_overlap_default_freeze_status`
- `peak_cross_term_collapsed`
- `peak_cross_term_joint`

默认情况下：

- `interference_overlap_mode = joint_overlap_integrated`
- `interference_cross_term_mode = joint_overlap_integrated`

如果后续手动切回 `collapsed_then_multiplied`，页面会恢复 legacy collapsed 交叉项，但仍保留 joint 对照项，便于做主线 / alternative 审计。

本轮页面又进一步把 freeze rule 接成了显式结论层：

- `aligned`：joint 与 collapsed 足够接近，collapsed 可继续作为低风险对照
- `caution`：joint 已冻结为默认主线，但 collapsed 近似已开始出现可见偏差
- `mismatch`：joint 与 collapsed 明显脱钩，collapsed 应降级为 legacy review-only 路径

这一轮页面还把最小统一偏振框架接进了 case 摘要表。现在会额外显示：

- `illumination_polarization_effective_mode`
- `illumination_polarization_alignment_status`
- `illumination_polarization_amplitude_factor`
- `illumination_projection_basis`
- `illumination_projection_basis_match`
- `illumination_projection_coupling_status`
- `reference_projection_effective_mode`
- `reference_projection_alignment_status`
- `reference_projection_amplitude_factor`
- `reference_projection_basis`
- `reference_projection_basis_match`
- `reference_projection_coupling_status`
- `interference_projection_basis_match`
- `interference_projection_coupling_status`

因此这里不再只是“看散射投影通道”，还可以直接看到照明端和 reference 端是否与当前散射主通道同偏振。

### 6. Reference Model Consistency Check

这是参考场主线这轮新增的第二个“验证工位”。

它不再比较散射投影路径，而是直接在同一组 `W/H/λ` 点上比较：

- `channel_angular_surrogate`
- `calibrated_lookup`

当前页面会围绕当前选中的 `W/H`，自动取一个局部小邻域，再结合固定的波长轴做对照。输出包括：

- `A_ref_surrogate / A_ref_calibrated`
- `A_ref_rel_error`
- `phi_ref_delta_wrapped_rad`
- `A_ref rank corr`
- 标定点是否外推 `calibration_extrapolated`

这一步现在已经不只是“看图”，还会直接给出冻结建议。当前默认规则是：

- 只要存在标定表，主路径始终优先 `calibrated_lookup`
- 只有当重叠区同时满足
  - `A_ref rank corr >= 0.85`
  - `mean |A_ref rel err| <= 0.25`
  - `mean |Δphi_ref| <= 0.75 rad`
  时，才接受 `channel_angular_surrogate` 继续作为默认 no-table fallback

页面现在还会额外给出按波长拆开的子表。注意这里的解释边界：

- reference field 不依赖粒子材料，所以 **material split 在这一层不适用**
- wavelength split 是有意义的，因为 reference surrogate 本身显式依赖 `λ`
- 如果某个波长子组的非外推点太少，页面会保留 `caution / mismatch`，而不会因为局部刚好误差小就误判成稳定 `aligned`

这一步的目标不是要求 surrogate 和 calibration 完全相等，而是回答：

- 在标定表覆盖区域里，surrogate 是否至少保留了相同的趋势排序
- 幅值偏差和相位偏差大概处在什么量级
- 哪些点已经落到了标定表外推区，不应拿来当严格对照

推荐解读：

- 如果 `A_ref rank corr` 很高，但 `A_ref_rel_error` 有系统偏差，说明 surrogate 更适合作为趋势 fallback，而不是绝对量值替代
- 如果排序本身也明显脱钩，就说明这段参数区间应优先信任 `calibrated_lookup`
- 如果很多点都被标成 `calibration_extrapolated=True`，说明当前对照区已经超出标定表有效覆盖范围

### 7. Path OPD / Gouy Freeze Check

这是当前页面新增的第三个“冻结判断工位”。

它会在同一组 case 参数下并排比较三条 `path_opd_model`：

- `single_pass`
- `reference_plane_roundtrip_surrogate`
- `wall_referenced_gap_surrogate`

并同时审计：

- `peak_clean_signal`
- `peak_delta_phi_ref_rad`
- `peak_phi_sca_path_z_rad`
- `peak_phi_gouy_ref_rad`
- `peak_phi_gouy_sca_rad`
- `peak_delta_phi_gouy_rad`

页面会直接给出两组结论：

- `path_opd_freeze_agreement_status`
- `path_opd_freeze_default_freeze_status`
- `delta_phi_gouy_freeze_agreement_status`
- `delta_phi_gouy_default_freeze_status`
- `delta_phi_gouy_validity`
- `delta_phi_gouy_geometry_width_to_waist_ratio / depth_to_waist_ratio`
- `observation_freeze_status`

当前代码下，它们的职责边界已经明确：

- `single_pass` 仍是工程主线的默认比较基准
- `reference_plane_roundtrip_surrogate` 和 `wall_referenced_gap_surrogate` 保留为诊断对照
- shared-beam `delta_phi_gouy` 现在除了数值对比，还会用 `W / w_x`、`H / w_z` 这类几何比值进一步区分 `shared_beam_acceptable` 与 `shared_beam_caution`
- 页面会把 `path_opd / overlap / projection / gouy geometry` 再聚合成一条 `observation_freeze_status`，直接说明当前 case 能否进入结果冻结判断

也就是说，这一块的目的不是马上替换主链，而是把“哪些解释已经够稳定、哪些还要继续复核”明确写成页面级结论。

---

## 如何阅读这页

页面顶部的 `这页怎么用` 现在默认折叠，主页面优先保留摘要卡、clean trace 和峰值构成。

### 情况 1：`A_ref` 变化很大，`E_sca normalized` 基本不变

说明你看到的 clean signal 提升主要来自 reference 放大，而不是粒子本征散射变强。

### 情况 2：`|E_sca|^2` 很小，但 `2Re(E_ref·E_sca*)` 很大

这是典型的 NODI 弱散射工作区，系统主要依赖 heterodyne gain。

### 情况 3：`|E_sca|^2` 已经不小

说明当前 case 不再只是“参考场把弱散射放大”，而是粒子自身散射已经进入明显可见区。

---

## 为什么不单独做“peak 加倍页”

因为 peak 变大在这里已经能解释清楚：

- 可能来自 `A_ref` 增大
- 可能来自 `E_sca normalized` 增大
- 可能来自两者共同变化

也就是说，peak 不是独立物理层，而是 interference 链条的结果。

---

## 关联后端

- `dashboard/signal_backend.py`
  - `compute_interference_case()`
  - `build_interference_scan_dataframe()`
  - `build_projection_mode_validation_dataframe()`
  - `build_reference_model_consistency_report()`

这些函数保证本页解释的量和主模拟器使用的是同一套公式，而不是单独写一套展示逻辑。

---

## 2026-04-03 文案补充

- 扫描图中的 `E_sca normalized / Peak clean signal / Heterodyne gain / Coupling factor` 已统一成中文优先表达：
  - `E_sca 归一化幅值`
  - `clean 峰值`
  - `异频增益`
  - `耦合因子`
- 本页仍保留 `A_ref`、`A_env`、`A_sca(t)` 等物理量符号写法，原因是它们更像公式符号而不是普通界面词。
## 2026-04-07 D / E 收口

- 本页顶部锚点卡片已改为复用 `render_workflow_anchor_summary()`。
- 本页的数据来源提示已改为复用 `render_workflow_source_notice()`。
- 页面自己的职责只剩两类：
  - 把当前标准 case 的 `Mie -> reference -> clean signal` 机制讲清楚
  - 展示本页专属的干涉链 summary / trace / scan

## 2026-04-07 来源提示统一

- `Interference Explorer` 页头现在改为共享的 workflow case/source 面板。
- 本页不再重复维护一套独立的“标准结果库 / live / 当前 case”提示，而是复用公共术语与来源说明。
- 术语折叠块明确了本页的职责：解释 clean signal 的放大来源，而不是单独做参数搜索。
