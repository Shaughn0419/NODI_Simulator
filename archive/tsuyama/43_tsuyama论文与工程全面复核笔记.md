# Tsuyama 论文与工程全面复核笔记

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 建立时间：2026-04-14
> 用途：持续记录对仓库内 Tsuyama / Mawatari 相关论文、当前工程核心实现、现行文档口径与外部专业资料的逐项对照，避免长链路审查中的信息丢失。
> 当前状态：进行中

---

## 0. 本笔记的工作目标

本轮复核要回答四个问题：

1. 仓库里新增的 Tsuyama 论文各自真正证明了什么？
2. 当前工程的核心计算逻辑、参数估计值和整体趋势，是否和论文原始内容一致？
3. 如果不一致，差异属于“合理 surrogate / 已声明边界”，还是“需要修正的漏洞”？
4. 哪些地方还需要借助外部教材或专业文献进一步确认？

---

## 1. 当前已定位到的材料

### 1.1 论文原文 / PDF

这些 PDF 现统一存放在 `papers/` 目录下。

- `Tsuyama_Mawatari_2019_Nonfluorescent Molecule Detection in 10 sup2-sup nm Nanofluidic Channels by.pdf`
- `Tsuyama_Mawatari_2020_Detection and Characterization of Individual Nanoparticles in a Liquid by.pdf`
- `Tsuyama_Mawatari_2020_Concentration Determination at a Countable Molecular Level in Nanofluidics by.pdf`
- `Tsuyama和Mawatari - 2020 - Characterization of optical diffraction by single nanochannel for aL–fL sample detection in nanoflui.pdf`
- `Tsuyama_Mawatari_2022_Nanofluidic optical diffraction interferometry for detection and classification.pdf`
- `Tsuyama和Mawatari - 2024 - Nanofluidic detection platform for simultaneous light absorption and scattering measurement of indiv.pdf`

### 1.2 已存在的工程对齐文档

- `25_核心计算逻辑与公式总说明.md`
- `41_实验对齐原则与计算修正备忘.md`
- `42_全量重算前复核结论与现行边界.md`
- `reports/current/35_method_notes.md`

### 1.3 代码与结果入口

- `data_objects.py`
- `reference_field.py`
- `illumination.py`
- `trajectory.py`
- `scattering_trace.py`
- `interferometric_trace.py`
- `pulse_analysis.py`
- `parameter_sweep.py`
- `tools/audits/tsuyama_gold_validation_compare.py`
- `results/tsuyama_gold_validation_tau1ms_1000e_report.json`

---

## 2. 阶段性阅读与对照框架

### 2.1 论文抽取维度

每篇论文至少记录以下内容：

- 研究对象与检测目标
- 通道几何、波长、NA、slit/pinhole、流速、时间常数、调制频率
- 论文中直接给出的公式、比例关系、趋势与图表结论
- 论文实际验证的范围与不能外推的边界

### 2.2 工程对照维度

逐项核对：

- 参考场来源与收集条件
- illumination / collection 的几何拆分
- 通道衍射 surrogate 的参数口径
- 轨迹、pressure-driven flow、diffusion、hindrance 的实现
- transit / lock-in / pulse detection 的时间尺度
- 参数 sweep、评分和工程 gate 是否把论文验证范围误用到别的问题上

### 2.3 结果判定口径

把差异分成三类：

- A 类：论文与代码一致，且逻辑闭合
- B 类：代码是有意识的 surrogate，边界写清楚即可
- C 类：存在潜在漏洞、遗漏、参数误配或论证过度，需要修正

---

## 3. 已确认的初步事实

### 3.1 工程里已经存在大量 Tsuyama 对齐痕迹

从仓库检索结果看，当前工程并不是“尚未对接 Tsuyama 论文”的状态；相反，`41`、`42`、`25`、`35.1` 与 dashboard 的 `Tsuyama Comparison` 页面都已经把 Tsuyama 2020 / 2022 / 2024 当成主要外部验证链之一。

### 3.2 当前最值得重新审的不是“有没有对齐”，而是“是否对齐过度”

也就是说，本轮复核要特别警惕两类风险：

1. 把论文只验证了 blank diffraction / gold control 的结论，误推广到 exosome 默认路线
2. 把论文里的实验条件当成绝对标定值写进模型，但实际上只该作为范围或趋势约束

---

## 4. 待补充的详细记录

### 4.1 论文逐篇摘要

#### 2019 POD：`Nonfluorescent Molecule Detection in 10^2 nm Nanofluidic Channels by Photothermal Optical Diffraction`

- 目标：在 `~10^2 nm` nanochannel 内实现非荧光分子的 POD 检测。
- 关键实验条件：
  - excitation `532 nm`
  - probe `633 nm`
  - illumination objective `20x, NA=0.45`
  - collection objective `NA=0.90`
  - `400 μm` pinhole
  - lock-in time constant `1 s`
  - 通道主例子：`400 nm × 400 nm`
- 关键结论：
  - 单通道衍射可把 transmitted beam 和 diffracted light 分开；
  - POD 信号与 diffracted light intensity 近似线性；
  - `400 nm` 通道下 LOD `5.0 μM`，对应检测体积 `230 aL`、约 `500 molecules`；
  - `200 nm` 通道也能工作而不显著恶化 LOD。
- 对本工程的意义：
  - 强支撑“blank-channel diffraction + slit-selected diffracted region + POD 读出”这条底层链；
  - 但它不是单颗粒 NODI 检测论文，不能直接拿来给当前 NODI detectability / gate 背书。

#### 2020 diffraction：`Characterization of optical diffraction by single nanochannel for aL–fL sample detection in nanofluidics`

- 目标：验证单 nanochannel diffraction 是否遵循常规 Fresnel–Kirchhoff 口径，并量化几何 / 位置 / 溶剂依赖。
- 关键实验条件：
  - probe `633 nm`
  - objective `20x, NA=0.45`
  - collection `NA=0.90`
  - chopper `1.1 kHz`
  - lock-in time constant `1 s`
- 关键图表与结论：
  - `Fig.3`：diffracted intensity 对 channel width 呈最优值，不是单调；在其条件下 optimum 约在 `500 nm` 附近。
  - `Fig.5`：diffracted intensity 随 depth 近似按平方趋势下降。
  - `Fig.6 / Fig.7`：对焦位置偏离会快速降低 diffracted intensity，尤其横向位置更敏感。
  - `Fig.8`：当溶剂折射率接近玻璃时，衍射强度最小。
  - `Fig.9`：POD 信号与 diffracted intensity 近似线性。
- 对本工程的意义：
  - 强支撑“参考场来自 channel diffraction、且 width/depth/solvent/focus position 会显著改写参考场”；
  - 也支持不能把 `A_ref` 设成与 `(W,H,λ,n)` 脱钩的常数。

#### 2020 counting POD：`Detection and Characterization of Individual Nanoparticles in a Liquid by Photothermal Optical Diffraction and Nanofluidics`

- 目标：在液体中对单颗 Au NP 做 counting-mode POD 检测与表征。
- 关键实验条件：
  - channel `800 ± 20 nm × 710 ± 20 nm`
  - `100 kPa` 时流速约 `0.17 mm/s`
  - lock-in time constant `2 ms`
  - modulation frequency `1.1 kHz`
- 关键结论：
  - `20 nm Au` 在该 POD 链中接近 `100% detection efficiency`；
  - `20/40 nm Au` 可用 photothermal signal 区分；
  - 计数模式下信号主要反映颗粒性质，而不是横向轨迹差异；
  - 这条链属于 absorption/POD，不是当前工程 NODI 单通道 detectability 的一对一验证。

#### 2020 solvent-enhanced POD：`Concentration Determination at a Countable Molecular Level in Nanofluidics by Solvent-Enhanced Photothermal Optical Diffraction`

- 目标：用溶剂热/光学性质提升 POD 灵敏度。
- 关键实验条件：
  - channel `400 ± 20 nm`
  - probe `633 nm`
  - excitation `532 nm`
- 关键结论：
  - POD 灵敏度同时受 diffraction factor 与 photothermal factor 控制；
  - 优化后 LOD 到 `75 nM`，约 `10 molecules / 0.23 fL`；
  - 说明 reference/diffraction side 与 thermal side 是耦合的，不能把 POD 简化成单一热模型。

#### 2022 NODI：`Nanofluidic optical diffraction interferometry for detection and classification of individual nanoparticles in a nanochannel`

- 目标：建立 NODI，对流动中的单颗粒做 interferometric scattering 检测和双波长分类。
- 关键实验条件：
  - illumination objective `20x, NA=0.45`
  - calculated spot size `~2 μm`
  - collection objective `NA=0.9`
  - slit `1 mm`
  - pinhole `400 μm`
  - time constant `1–2 ms`
  - 典型 `100 kPa -> 0.2 mm/s`
  - 颗粒 `~10 ms` 通过检测区
- 关键图表与结论：
  - `Fig.4`：检测主要发生在 diffracted-light region，不在 transmitted region。
  - `Fig.5`：Ag/Au signal ratio 更接近 interferometric scattering，而不是纯 scattering 或 absorption。
  - `Fig.6`：最佳 detection frequency 在 `~1–6 kHz`。
  - `Fig.7`：gold signal 约按 `d^2.3` 标度，而不是 `d^6`。
  - 20 nm Au 可见但更接近边界，30 nm 更稳；
  - 双波长 `488/532` 可对 `40/60 nm` Au/Ag 做分类，SVM 准确率约 `71.9 ± 4.0%`。
- 特别重要的措辞：
  - 论文多次说的是 pulse `height / width / maximum signal value`；
  - 论文强调 phase fluctuation 会存在，但 millisecond lock-in 抽取后，**maximum signal value** 仍携带粒径与组成信息；
  - 正文没有把“正负号翻转占比”作为 reject criterion。

#### 2024 POD+NODI：`Nanofluidic detection platform for simultaneous light absorption and scattering measurement of individual nanoparticles in flow`

- 目标：同步测量 POD absorption 与 NODI scattering，并做混样分类。
- 关键实验条件：
  - excitation `532 nm`
  - probe `660 nm`
  - illumination objective `20x, NA=0.45`
  - collection `NA=0.9`
  - slit `1 mm`
  - pinhole `400 μm`
  - lock-in `1–2 ms`
  - 典型 `100 kPa -> 0.2 mm/s`
  - 通道宽度 `800–1200 nm`，深度约 `550 nm`
- 关键图表与结论：
  - `Fig.3`：`4.1 kHz` 通道对 excitation 强度敏感，`1.2 kHz` 通道近似不随 excitation 变化，证明两路信号可分离；
  - `Fig.4`：随着 modulation frequency 从 `0.5` 提高到 `4.1 kHz`，POD purity 提高到 `>80%`；
  - `Fig.5`：四类颗粒联合散点可分，SVM 平均准确率 `82.6 ± 2.1%`；
  - 20 nm gold 的 scattering lane 很弱，接近背景；
  - 讨论部分明确写到：`~10 ms` 内 diffusion length 与 channel size 同量级，maximum signal value 仍携带颗粒信息。
- 对本工程的意义：
  - 强支撑 paired POD/NODI 的价值；
  - 强支撑高 modulation frequency 对 separation 的必要性；
  - 但它测的是 plasmonic particles，不是 exosome 默认路线的直接验证。

### 4.2 图表与参数摘录

#### 2020 diffraction

- width 不是越小越强，也不是越大越强，而是存在 optimum；
- depth 趋势更接近 intensity `~H^2`；
- focus misalignment 会显著压低 diffraction；
- POD signal 与 diffracted intensity 近线性。

#### 2022 NODI

- slit 扫描图清楚显示：信号峰主要在 diffracted-light region，而不是 transmitted-light region；
- `silver/gold` ratio 的实验值与 interferometric scattering 理论更接近；
- size scaling 约 `d^2.3`；
- `20 nm Au` SNR 明显弱于 `30 nm Au`；
- dual-wavelength 散点图可以分群，但不是完全分离。

#### 2024 paired POD/NODI

- `0.5–1.2 kHz` 有明显 signal leakage；
- `4.1 kHz` 时 POD ratio 已到 `~0.8`；
- 联合散点图里 `20 nm gold` 更靠近低 scattering / 中等 absorption 一侧；
- 40/60 nm silver 与 gold 的 separation 来自双通道联用，而不是单通道独立足够。

### 4.3 代码链逐模块核对

#### 已确认和论文对齐的实现

- `data_objects.py`
  - `OpticalSystem.illumination_NA = 0.45`
  - `NA_collection = 0.9`
  - `lockin_time_constant_s = 1e-3`
  - `illumination_mode = "overfill"`
- `illumination.py`
  - `overfill` 只抹平 `x/z`，保留 `y` transit 包络；
  - 明确按 `~2 μm` overfill 语义对齐 Tsuyama 2022。
- `reference_field.py`
  - 已加入 `W_min = λ / NA_collection` 的 NA cutoff；
  - `reference_model="channel_angular_surrogate"` 时，reference amplitude 的确会随 `(W,H,λ)` 变化，而不是常数。
- `trajectory.py`
  - dashboard 主线不是 `plug`，而是 `rect_series + diffusion + anisotropic_tensor_surrogate`；
  - 颗粒中心的可达区域已扣掉粒子半径；
  - 近壁 hindrance 用 parallel/perpendicular wall-mobility surrogate 组合。
- `pulse_analysis.py`
  - 阈值来自前 `20%` 背景段；
  - 最小 peak width `2.5 ms`、最小 interval `100 ms`，和 2022/2024 文本口径一致。
- `parameter_sweep.py`
  - lock-in surrogate 显式建了 POD/NODI true lane、leak lane、频率响应和串扰；
  - paired pulse 诊断已存在。

#### 已识别出的潜在不一致 / 需要重点审查

##### 1. `readout_observable_mode="in_phase"` 与 `phase_flip_fraction` gate 组合，可能把“锁相相位选择”误当成“物理不稳定”

- 论文口径：
  - 2022 / 2024 都把分类特征写成 pulse `height / width`，并强调 `maximum signal value` 携带颗粒信息；
  - 没有把“正负号翻转比例”作为 reject criterion。
- 代码口径：
  - dashboard 默认 `readout_observable_mode="in_phase"`；
  - 同时 `pulse_detection_mode="absolute"`，即负峰也会被当作检测事件；
  - 但工程 gate 又用 `phase_flip_fraction = n_negative / n_detected` 处罚。
- 小范围诊断复算（现行主线，仅改 `readout_observable_mode`）：
  - `800×600 nm, 660 nm, gold 50 nm`
    - `in_phase`: `det=0.325`, `stable=0.3125`, `phase_flip=0.50`, `mean_peak=1.229`
    - `magnitude`: `det=0.3125`, `stable=0.3000`, `phase_flip=0.00`, `mean_peak=1.212`
  - `800×600 nm, 660 nm, gold 60 nm`
    - `in_phase`: `det=0.3167`, `stable=0.3000`, `phase_flip=0.4737`, `mean_peak=2.351`
    - `magnitude`: `det=0.3000`, `stable=0.3000`, `phase_flip=0.00`, `mean_peak=2.351`
  - `800×500 nm, 532 nm, gold 50 nm`
    - `in_phase`: `det=0.1167`, `phase_flip=0.7143`
    - `magnitude`: `det=0.1167`, `phase_flip=0.00`
- 初步判断：
  - **phase-flip gate 对当前 Tsuyama gold 对照的影响，很可能主要来自 X-channel / in-phase 读出的相位选择，而不是 detectability 本身。**
  - 这更像“工程 gate 语义过严或和论文观测量不完全同构”，不是原理层错误。

##### 2. 当前输运入口仍是“初始横截面均匀采样”，而不是“通过检测面的事件通量采样”

- `utils.sample_initial_position()` 默认仍是 uniform accessible cross-section。
- `trajectory.py` 虽已加入 `rect_series + diffusion + hindrance`，但事件采样不是 crossing-conditioned。
- Tsuyama 2024 明确给出：
  - `U ~ 0.2 mm/s`
  - transit `~10 ms`
  - diffusion length 与 channel size 可比
- 额外估算（室温水中 Stokes-Einstein）：
  - `20 nm` 粒子 `10 ms` diffusion length 约 `661 nm`
  - `40–60 nm` 粒子约 `382–467 nm`
  - 对 `H ~ 500–600 nm` 是可比量级，但对 `W ~ 800–1200 nm` 不是“完全重混”的强结论。
- 初步判断：
  - 当前“uniform initial position + pre-run diffusion”不是明显硬错，但也**不能当成严格 event-flux 修正的替代品**；
  - 对 `40–60 nm` gold / exosome 这类 `Pe_xz` 仍为几到十的情况，这是一条值得继续升级的边界，而不是可以彻底忽略的次要问题。

##### 3. 文档中偶有引用口径漂移

- 多处文档把 Tsuyama 2022 误写成 `Lab Chip`，实际文件是 *Microfluidics and Nanofluidics* 2022。
- 这是引用卫生问题，不直接影响计算，但会降低后续审查可追溯性。

### 4.4 可能的漏洞 / 需要修正项

#### 当前最像“需要修正或至少重分层”的点

1. **把 `phase_flip_fraction` 从当前“detectability 主 gate”里降级**
   - 更合适的角色可能是：
     - `in_phase` 模式下的诊断风险项
     - 或 paired / phase-aware 扩展分析项
   - 但不宜继续直接压住 Tsuyama gold detectability 对照的主结论。

2. **把 Tsuyama 对照结论限定在它真正覆盖的范围**
   - blank diffraction
   - plasmonic gold/silver single-particle detection
   - POD/NODI paired readout
   - 不能直接改写 exosome 默认路线。

3. **把 crossing-conditioned transport 升级列为真正下一阶段重点**
   - 现行输运并非 must-fix blocker；
   - 但它是当前最重要的物理边界之一，不应在文档里被弱化成“几乎已经等价解决”。

### 4.5 外部文献与教材核验

#### 已补充

- Stanford Research Systems 锁相放大器资料：
  - 双相锁相输出本质是 `X = R cosθ`, `Y = R sinθ`，相位需要调零；
  - 这进一步支持“`in_phase` 的正负号受参考相位选择影响，而 `R` / magnitude 更接近相位不变读出”。

#### 待继续补

- 受限通道中颗粒的 crossing-conditioned event statistics / entrance-conditioned transport 文献；
- 矩形纳米通道内颗粒在中等 Peclet 数下的横截面占据分布文献。

---

## 5. 当前阶段的综合判断

### 5.1 可以较高置信度成立的判断

1. 当前工程的**底层物理主链并没有偏离 Tsuyama 论文主线**。
   - 单通道衍射参考场；
   - illumination / collection 几何拆分；
   - 干涉散射而非纯 `d^6` 散射；
   - millisecond lock-in + finite transit 的时间尺度；
   - paired POD/NODI 与调制频率分离的重要性。

2. 当前工程最值得优先修正的，不是 reference-field 主公式，也不是 width/depth 趋势，而是**读出层和 gate 层之间的语义错配**。
   - `absolute` 检测接受负峰；
   - 但 `phase_flip_fraction` 又把负峰占比当成主惩罚；
   - 这使得 `in_phase` 参考相位选择，可能被误解释成物理可检测性下降。

3. 当前输运实现更像“合理 surrogate + 仍需升级”，而不是“已经被 Tsuyama 文献彻底证实正确”。
   - 对 `20 nm` 粒子，论文文本能支持 diffusion 与通道尺度可比；
   - 对更大粒子或更宽通道，现行 uniform-start 近似仍可能残留系统偏差。

### 5.2 我认为需要尽快落实的修正方向

1. **把 Tsuyama gold validation 的主判据切回与论文观测量更同构的量**
   - 优先考虑 `magnitude` / `envelope` / `absolute peak` 路径；
   - `phase_flip_fraction` 保留为诊断项，而不是主淘汰项。

2. **把文档中的“Tsuyama 支撑范围”写得更窄、更准确**
   - 明确区分：
     - diffraction blank validation
     - plasmonic single-particle validation
     - exosome/default-route extrapolation

3. **后续若继续提升物理严谨性，transport 应优先升级为 crossing-conditioned 统计**
   - 即检测事件按局部轴向通量加权，而不是只从初始横截面均匀抽样。

### 5.3 当前不建议仓促改动的地方

1. 不建议因为这轮复核，就回退当前已经建立好的 diffraction surrogate、NA cutoff 或 overfill 实现。
2. 不建议把 2022 / 2024 文中关于 diffusion 的描述，直接解释成“横截面占据必然完全均匀”。
3. 不建议把 plasmonic gold/silver 的成功对照，直接写成对 exosome detectability 的完成验证。
