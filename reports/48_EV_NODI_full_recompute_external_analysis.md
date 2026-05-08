# EV/NODI 全量重算结果科学分析报告

> Codex 最终修订：2026-05-06。已用 full raw summary、runtime/meta/health JSON、`results/ev_size_weighted_route_analysis.csv`、Tsuyama Phase 2/2.11 收口结果、ET-2030 + LI5640 hardware feasibility 和 paper-statistics sensitivity 复核关键结论；本版按最新口径统一为：660/404 是 EV 工程主验证轴，532/488 是中波对照；Tsuyama selected-annulus paper-fit 计算侧已停止在 diagnostic / paper-reproduction 结论，不再回写 EV full-grid 或 global defaults。

## 0. 一页结论与读者入口

这次 full-grid 重算已经形成一个完整、可用于工程筛选的 EV/NODI 设计库。它的科学含义不是“已经标定出真实检测限”，而是：在统一的 NODI surrogate 模型和固定事件预算下，比较不同波长、通道宽深与粒径条件，判断哪些设计最值得进入第一轮真实实验。旧报告中的局部数值仍可作为历史参照，但本报告所有判断均以本轮 full recompute 的 raw summary 为准。

按本工程的实验目的，本报告应从 **660 nm 和 404 nm 两端波长验证** 出发阅读。这里的核心问题不是寻找一个平均分最高的单一路线，而是验证长波 660 nm 与短波 404 nm 在 NODI reference、cross term、blank/background、曝光风险和 EV 尺寸覆盖上的差异。**532 nm 和 488 nm 应作为中波对照组**：它们提供较稳的 reference-useful baseline，用来衡量 660/404 的数据差距和波长趋势，而不是本轮最优先想证明的对象。

660 nm 是本轮的**长波主验证轴**，但必须拆成两类路线。`660 / 800×1400` 和 `660 / 800×1500` 是 reference-useful 的长波候选，既保留了较强 EV proxy response，也没有落入最明显的 weak-reference 解释边界，应作为 660 的主验证几何。`660 / 700×1500` 的条件检出数很高，但它落在 weak-reference / NA boundary 上，不能解释为理想 NODI 增强；它仍然很有价值，但角色应是长波弱参考场边界对照。

404 nm 是本轮的**短波主验证轴**。它的本征散射、探测场和干涉项更强，适合验证短波机制、Au ladder、blank false positives、滤光片/物镜透过率、低功率阶梯和 EV 完整性风险。需要同时保留一个重要 caveat：在当前 EV 粒径与折射率设定下，404 的稳定检出覆盖没有随峰高同步提高，因此它不是“稳定检出最强路线”，而是必须实测确认的短波机制路线。

因此，第一轮实验应设计成一个围绕 660/404 的机制分层面板：660/800×1400 与 660/800×1500 做长波主验证，660/700×1500 做弱参考场边界对照，404/600×1300 做短波机制主验证，404/800×700 做 Tsuyama-like sanity，532/600×1500 与 488/600×1500 做中波对照基线，700/800/900 × 1200–1400 nm 做几何 robustness 扫描。

必须保留的边界是：本库支持 **relative / proxy / diagnostic engineering ranking**，不能支持真实 EV 浓度、真实回收率、absolute LOD、absolute SNR、真实跨波长最优或 EV biological specificity。报告中的检出数均表示“在 10000 个模拟粒子事件已经进入检测区的前提下，有多少事件被当前读出算法判为可检测”，不是实验浓度或绝对检测效率。

计算侧的总口径也已经更新：Tsuyama 2022 selected-annulus Phase 2 / 2.11 不再继续无实测参数搜索。当前最清晰的结论是：formula-consistent Table S1 Ag/Au signal 已基本对齐，detection 不是主 blocker；真正未解的是 raw Au size-response 偏陡，残差主要集中在 Au40-Au60 slope。单一全局 response-compression lens 已接近 descriptive partial，但仍不能签 paper-calibrated raw candidate。因此后续工作不应继续扩大 D2/noise/threshold/paper-fit 搜索，而应转向 ET-2030 + LI5640 detector-unit feasibility、paper-matched finite-count/IQR 统计和真实 blank/BFP/Au trace 标定。

### 0.1 本版相对旧版的口径变化

本版相对旧版的主要变化是实验目标的重排。旧版更强调 532/488 在当前 EV 模型和粒径加权下的稳健性；本版则把第一轮实验组织为 **660/404 主机制轴 + 532/488 中波对照**。这个变化不是推翻旧版数值，而是把目标从“寻找平均最稳候选”调整为“最大化第一轮实验的信息量”。

| 版本口径 | 主叙事 | 为什么变化 |
|---|---|---|
| 旧版 | 532/488 更像稳健主验证，404/660 偏机制或对照 | 偏重稳定检出和粒径加权表现 |
| 本版 | 660/404 是主验证轴，532/488 是中波对照 | 偏重机制分层：长波 reference-useful / weak-reference 边界、短波高散射/曝光风险、中波 baseline |

因此，660 nm 需要拆分为 reference-useful 长波候选和 weak-reference 边界对照；404 nm 需要作为短波高散射/高风险机制验证；532/488 保留为中波 baseline，用来判断 660/404 的机制差异是否真实。

### 0.2 第一轮实验 P0/P1/P2 面板

| 优先级 | 条件 | 角色 | 主要验证问题 | 成功/失败判读 |
|---|---|---|---|---|
| P0 | `660 / 800×1400` | 长波 reference-useful 主候选 | 660 避开 weak-reference 后是否仍有可用 NODI response | 若 blank 与 Au ladder 支持，优先推进 660 长波路线；若不支持，660 高分可能依赖 surrogate reference |
| P0 | `660 / 800×1500` | 长波深通道主候选 | 深度增加对 reference、blank、detection 是否有收益 | 与 800×1400 同向则说明 geometry robustness 更强；反向则提示深度/流体 trade-off |
| P0 | `660 / 700×1500` | weak-reference 边界对照 | 高条件检出是否来自非理想 NODI / 弱参考场边界 | 若强但 reference/BFP 不支持，应保留为边界现象而非主路线 |
| P0 | `404 / 600×1300` | 短波机制主候选 | 404 的散射/干涉增强是否能转化为真实 pulse | 若 blank、曝光和 EV integrity 通过，说明短波机制有实验价值；若 false-positive/损伤高，则短波只作机制边界 |
| P1 | `404 / 800×700` | Tsuyama-like / 文献近似 sanity | 平台是否处在合理量级 | 用于判断 404 机制结果是不是仪器/几何异常 |
| P1 | `532 / 600×1500` | 中波稳健 baseline | 与旧版稳健候选对齐，做趋势锚点 | 若 532 也不稳，应优先排查 blank / detector / channel |
| P1 | `488 / 600×1500` | 中波第二 baseline | 与 532 形成中波对照 | 用于区分波长趋势与单一 detector/filter 偏差 |
| P2 | `700/800/900 × 1200–1400` | geometry robustness | 制程、PEG、堵塞风险下的稳健性 | 用于收窄第二轮芯片几何，而不是第一轮主结论 |

### 0.3 速读边界：本报告能说什么，不能说什么

| 不要把本报告理解为 | 本报告能支持的是 |
|---|---|
| 已经证明 404 或 660 是真实最优波长 | full-grid 工程候选排序和第一轮实验设计优先级 |
| 已经给出 EV absolute LOD、absolute SNR、真实浓度或回收率 | 进入检测区后的 conditional detection proxy 与相对趋势 |
| 已经完成 detector-unit / Mie-to-power / blank calibration | 下一步 blank、BFP/slit、Au ladder、ET-2030 + LI5640 chain 的实验清单 |
| Tsuyama 2022 已被完全复现 | Tsuyama selected-annulus paper-fit 计算侧已停止在 diagnostic / paper-reproduction 结论 |
| selected-annulus 可替代 all-crossing 工程 ranking | selected-annulus 可作交叉验证，但系统性偏乐观且只覆盖约 40.2% 事件 |
| 660 / 700×1500 是理想 NODI 主路线 | 660 / 700×1500 是 weak-reference 边界对照 |

### 0.4 术语速查

| 术语 | 本报告中的含义 |
|---|---|
| all-crossing | 所有进入检测区事件的主工程口径 |
| selected-annulus | `edge_norm = 0.5–0.8` 的轨迹子区域，用于 paper-audit 与 cross-check |
| conditional detection | 已进入检测区的模拟事件中被判为可检出的比例，不是样品真实检出率 |
| stable detection | 过阈值且有足够 margin 的更保守检出 |
| reference-useful | 通道 reference 可解释为有效 NODI 干涉参考 |
| weak-reference | reference 太弱或处于 NA/boundary，不能按理想 NODI 增强解读 |
| governed surrogate | 统一受控的相对模型，不是绝对探测器模型 |
| paper-reproduction lens | 为复现论文 trend 的低自由度解释镜头，不等同 accepted calibration |

---

## 1. 数据质量与解释边界

本次重算的数据完整性足够支撑后续工程分析。18 个 summary 分片合并后得到 **32032 个唯一 case**，没有重复 case；每个 case 均完成 10000 个模拟事件，总事件数为 **3.2032 亿**。运行记录显示 full-grid 不是 partial run：`allow_partial_results = false`，保存 case 数与预期 case 数完全一致，全部 case 均通过 recompute manifest gate。因此，本报告可以把这批结果视为一个完整设计库，而不是抽样残片或中断结果。

运行性能也没有提示异常。整轮 sweep 约 10 小时完成，case runtime 的中位数与 p95 很接近，说明没有明显长尾或少数 case 拖垮计算；event engine 被明确配置为非向量化路径，没有出现意外 fallback。checkpoint 和最终保存的耗时占比很低，因此 I/O 不是结果解释中的主要不确定性来源。

需要保留一个量级解释 caveat：本轮 **3640 / 32032 个 case（11.4%）** 的 `rho_physical_envelope_status = unavailable`。这不影响完整性和主工程排序，但说明 reference 量级、cross term 绝对量级等 rho-sensitive 解释仍需在实验 blank/reference 标定后再扩大外推。

更重要的是解释边界。health 文件显示当前 forward model 仍是 governed surrogate：collection operator、detector unit chain、Mie-to-power chain 和实测 blank calibration 都还没有真实实验校准。这意味着结果适合比较“哪条设计路线更值得做”，不适合给出绝对光功率、绝对 SNR、LOD 或真实 EV 浓度。换句话说，数据质量是完整的，但物理标定仍是相对/工程口径。

selected-annulus 字段在全部 32032 个 case 中均可用，且 rate 与 fraction 是同行有效的。这个口径平均覆盖约 **40.2%** 的事件，代表一个更有利、可重复的轨迹子区域。它适合做交叉验证：如果某个 route 在 all-crossing 和 selected-annulus 下都表现好，可信度更高；如果只在 selected-annulus 下变亮，则应谨慎看待，因为它可能依赖被筛出的有利轨迹，而不代表所有 crossing。

---

## 2. 本报告回答的问题

本报告的核心问题是：在尚未完成 detector-unit calibration、blank trace calibration 和真实样品验证之前，如何用这批 full-grid 结果设计一轮最有信息量的实验。换句话说，它关心的不是“哪个设计已经被证明最好”，而是“哪些设计最值得被拿去验证，并且每个设计应该验证什么科学问题”。

因此，报告能够回答的是：在当前 governed surrogate 模型、当前 event readout 和当前 geometry grid 下，660/404 应分别用哪些通道几何来做长波和短波验证，532/488 应如何作为中波对照基线，以及哪些组合更适合做弱参考场边界、Tsuyama-like sanity check 或几何 robustness 扫描。

报告不能回答的是：真实样品中有多少 EV，真实样品进入通道的概率是多少，真实 blank false-positive 是多少，真实光功率/探测器响应下的 SNR/LOD 是多少，或者不同 EV 分离方法/生物来源是否具有 specificity。EV 的 RI、形貌、膜/冠层等会显著影响散射解释；EV RI 也不是一个可以随便固定的常数，小颗粒散射解释同时依赖 size、morphology 和 refractive index。

本报告里的 `detected_per_10000` 统一定义为：**假设 10000 个粒子事件已经进入检测区并经过当前读出算法，其中被判为可检测事件的个数**。这不是浓度、不是回收率、不是绝对 LOD、不是绝对 SNR。

---

## 3. 工程目标口径：660/404 主验证，532/488 对照

### 3.1 候选路线复核表

下表不是单纯的排名表，而是把每条候选路线放回其科学角色中理解。`all-crossing` 表示所有进入检测区事件的主口径；`selected-annulus` 表示较有利轨迹子区域中的交叉验证结果；`strict` 则进一步要求该结果没有落入 weak-reference 或 NA boundary。只有同时看这三类信息，才能区分“数值高但不可解释”和“数值适中但更适合实验验证”的路线。selected-annulus 全局 top route（如 660 / 500×1500 一类窄/浅几何）已在第 4.1 节单独讨论并排除主推；本表只列入按工程目标需要进入实验面板的候选。

| 角色 | route | all-crossing 检出/10000 | pass/27 | strict/27 | selected-annulus 检出/10000 | selected rate≥0.2 | reference band | 判断 |
|---|---|---:|---:|---:|---:|---:|---|---|
| 660 长波主验证 A | 660 / 800×1400 | 1866 | 13 | 13 | 2278 | 17 | useful | 重点验证 660 下 reference-useful 长波读出 |
| 660 长波主验证 B | 660 / 800×1500 | 1873 | 12 | 12 | 2232 | 15 | useful | 与 800×1400 并列验证深通道长波路线 |
| 660 弱参考边界对照 | 660 / 700×1500 | 2292 | 15 | 0 | 2630 | 16 | too weak | 专门验证 weak-reference / NA boundary |
| 404 短波主验证 | 404 / 600×1300 | 587 | 0 | 0 | 665 | 0 | useful | 验证短波散射、cross term、blank 与曝光风险 |
| 404 Tsuyama-like sanity | 404 / 800×700 | 539 | 0 | 0 | 761 | 0 | useful | 系统 sanity，不追求最高检出 |
| 中波对照 A | 532 / 600×1500 | 1345 | 7 | 7 | 1490 | 9 | useful | 稳定 reference-useful 对照，用来衡量 660/404 差距 |
| 中波对照 B | 488 / 600×1500 | 1073 | 3 | 3 | 1181 | 6 | useful | 相邻中波对照，用来观察波长趋势 |

注：表中“主验证”指本工程的科学验证目标，不等于“稳定检出已就绪”。660 的主验证目标是 reference-useful 长波读出；404 的主验证目标是短波散射、cross term、blank/background、曝光和 EV integrity。404 两条 route 在当前 surrogate 下均为 0/27 `engineering_gate_passed`，因此它是短波机制主验证路线，而不是稳定检出已经成熟的主检测路线；532/488 虽然 pass 数更稳，但在本工程里承担中波对照角色。

### 3.2 每个波长内部 top 几何

从单波长内部看，四个波段承担的实验角色并不相同。

660 nm 是本轮最需要实测确认的长波轴。窄宽度或 700 nm 宽度深通道能给出很高的条件检出数，但这些结果多数处于 weak-reference / NA boundary，不能被解释为理想的 NODI 干涉增强。因此，`660 / 700×1500` 应作为边界对照来验证 weak-reference 现象；真正承担 660 主验证的是 `800×1400` 与 `800×1500` 这类 reference-useful 几何，它们既保留了长波下较强的 EV proxy response，也没有落入最明显的不可解释边界。

| 660 类型 | 例子 | 是否主推 | 原因 |
|---|---|---|---|
| reference-useful 660 | `800×1400`、`800×1500` | 是，作为长波主验证 | reference band 可解释，能回答长波 NODI 是否可用 |
| weak-reference 660 | `700×1500` | 对照，不是主路线 | 条件检出高但不能按理想 NODI 增强解释 |
| wide/robust 660 | `900×1400`、`900×1500` | 可选 robustness | 流体/制程更稳，但灵敏度与 reference trade-off 需实测 |

404 nm 是对应的短波轴。它的优势来自短波散射和干涉项增强，但在当前 EV 模型下没有形成足够稳定的尺寸覆盖。因此，404 的实验目的应写清楚：`600×1300` 用来验证短波峰高、cross term、blank/background 和曝光/EV integrity 风险；`800×700` 更适合做 Tsuyama-like sanity geometry，用于验证平台对 nanochannel diffraction 和 Au ladder 的响应是否合理。500 nm 宽度虽然局部检出数可更高，但 PEG、近壁面偏置和堵塞风险更大，不宜作为第一轮主芯片。

| 404 优势 | 404 风险 |
|---|---|
| 本征散射和探测场更强 | 曝光、热效应和 EV integrity 风险更高 |
| 干涉 cross term 和 peak proxy 更强 | 物镜、滤光片、探测器响应必须重测 |
| Au ladder 机制验证价值高 | 稳定检出覆盖没有随峰高同步提升 |
| 可验证短波极限 | blank false positive 可能更敏感 |

488 nm 和 532 nm 在本轮应作为中波对照，而不是被叙述成工程目标的主角。它们的价值正是稳定：`532 / 600×1500` 在 EV 覆盖、reference band、selected-annulus 支持和工程分数之间形成了较可靠的 baseline；`488 / 600×1500` 作为相邻中波可以检查 532 的优势是否来自真实波长响应，而不是单一模型假设。`600×1300`、`600×1400`、`700×1500` 可作为 532 nm 周边 geometry robustness 扫描。

详细候选数字保留在表 3.1 和 Appendix C；主文采用上述角色划分，是为了避免把“数值最高”误读为“物理上最可靠”。

### 3.3 为什么不能跨波长给“绝对最好”

这批结果采用 per-wavelength normalization，且全表 cross-wavelength claim gate 均未通过。科学上，这意味着不同波长之间的绝对响应还缺少探测器响应、滤光片透过率、入射功率、collection operator 和 reference calibration 的共同标尺。

因此，本报告可以做两类判断：第一，在同一波长内部比较不同通道几何；第二，设计一个覆盖不同波长角色的实验面板。它不能做的判断是把 404、488、532、660 nm 直接排成真实绝对灵敏度榜单。比如 660 nm 某些几何的检出数很高，但如果该结果来自 weak-reference boundary，它就不能被写成“660 真实最佳”；同理，404 nm 的短波散射优势也不能自动转化为稳定 EV 检出优势。

主工程分数应理解为综合证据，而不是单一物理量。它把稳定检出、峰值裕量、reference band、流体风险和 claim blockers 一起考虑；这也是为什么本报告把 660/404 作为需要实测回答的两端波长主问题，同时保留 532/488 作为中波对照，而不是简单选择全表最大检出数或把中波稳定性误写成工程目标优先级。

---

## 4. selected-annulus：交叉验证而非主结论

### 4.1 selected-annulus top routes

在 EV route 层面，selected-annulus 按 selected mean detection 排名时，top routes 几乎全被 660 nm 与窄/浅几何占据：`660 / 500×1500`、`500×1400`、`500×1300`、`500×1200`、`500×1100` 等，selected 检出约 **2854–3156/10000**（对应 `660 / 500 × 1100 → 1500 nm` 五个 route）；但是这些 route 全部 `reference_too_weak`，strict count = 0。因此 selected-annulus 的全局 top 不应直接覆盖 all-crossing 主工程口径。

下游 route analysis 现在默认把 selected-annulus ranking 拆成两张表：`reference_useful_only` 主表和 weak/unknown-reference boundary 表。若只看 EV reference-useful route，selected-annulus top 变为 `660 / 800×500`、`800×550`、`800×600`、`900×500`、`800×650` 等浅通道；对应 weak-reference boundary 表则保留 `660 / 500×1500`、`500×1400`、`500×1300` 等高 selected 数值路线，明确标成边界对照。这说明 selected lens 更容易偏向某些有利轨迹/annulus 子集，也更容易把浅通道抬高。它是很有价值的交叉验证，但不是最终推荐本身。

### 4.2 selected-annulus 与 all-crossing 是否一致

不完全一致。候选面板内的方向是一致的：532/488 中波对照在 selected-annulus 下都变强，404 仍未达到稳定覆盖，660 的 weak-reference 问题不消失。但全局 top route 不一致：selected-annulus 会把 660 窄/浅 route 推到最前，而 all-crossing 主口径更重视全事件稳定性、reference band 和工程门槛。

| route | all-crossing/10000 | selected/10000 | selected/all | all pass | selected rate≥0.2 | 解释 |
|---|---:|---:|---:|---:|---:|---|
| 532 / 600×1500 | 1345 | 1490 | 1.11× | 7/27 | 9/27 | 稳定中波对照，但没有覆盖小 EV |
| 488 / 600×1500 | 1073 | 1181 | 1.10× | 3/27 | 6/27 | 中波相邻对照，弱于 532 |
| 404 / 600×1300 | 587 | 665 | 1.13× | 0/27 | 0/27 | 短波机制主验证，但不是稳定检出路线 |
| 404 / 800×700 | 539 | 761 | 1.41× | 0/27 | 0/27 | sanity 几何在 selected 下变亮，但仍不过线 |
| 660 / 700×1500 | 2292 | 2630 | 1.15× | 15/27 | 16/27 | 仍是 weak-reference 对照 |
| 660 / 800×1400 | 1866 | 2278 | 1.22× | 13/27 | 17/27 | 支持作为 660 reference-useful 主验证 |
| 660 / 800×1500 | 1873 | 2232 | 1.19× | 12/27 | 15/27 | 支持作为 660 reference-useful 主验证 |

在 EV route 层面，selected/all 比值的中位数约 **1.35×**，均值约 **1.33×**；572 个 EV route 中 selected mean detection 全部高于 all-crossing mean detection。这不是坏事，但意味着 selected-annulus 具有系统性乐观倾向。为避免把这个偏乐观条件率误读成全体 crossing 收益，route analysis 现在同时输出 `selected_annulus_contribution = selected_annulus_fraction × selected_annulus_detection_rate` 和 `selected_annulus_uplift`；前者表示 annulus 子区对全事件分母的贡献，后者用于标记过强 uplift。

### 4.3 selected-annulus 偏乐观在哪里

selected-annulus 只看 edge norm 0.5–0.8 的事件子集，平均只覆盖约 **40.2%** 事件。它可以回答“在一个较有利、可重复的轨迹子区域中，读出是否也支持该 route”，但不能代表所有 crossing。偏乐观主要体现在：

1. 它排除了部分不利 crossing，因此 detection rate 通常高于 all-crossing。
2. 它会把 660 nm 窄/浅几何推高，即使这些几何的 reference band 不可解释。
3. 它会让 selected rate ≥ 0.2 的尺寸阈值提前。例如 `532 / 600×1500` 从 all-crossing 的 240–300 nm pass 扩展到 selected 的 220–300 nm；`488 / 600×1500` 从 280–300 nm 扩展到 250–300 nm。但 40–200 nm 的小 EV 仍然大多没过保守门槛。

实际分析时应同时检查三个新状态字段：`selected_annulus_reference_interpretation` 把 reference-useful cross-check 与 weak-reference boundary 分开；`selected_annulus_fraction_guardrail_status` 在 fraction < 0.35 时给工程警告、< 0.25 时判为失败；`selected_annulus_uplift_warning_status` 在 uplift > 1.6× 时提示 annulus-dominated 解释风险。

### 4.4 all-crossing 与 selected-annulus 的快速判读

| all-crossing | selected-annulus | 推荐判读 |
|---|---|---|
| 强 | 强 | 高可信主候选，可优先实验；仍需看 reference band 与 blank |
| 强 | 弱 | 全域稳健但有利 annulus 不突出；需检查空间轨迹、BFP/ROI 与流体分布 |
| 弱 | 强 | 不宜直接主推；可能只在有利轨迹变亮，需看 selected fraction、uplift 与 reference 解释 |
| 弱 | 弱 | 不推荐作为主路线；只保留 sanity 或机制边界用途 |

这个表是本报告判读 selected-annulus 的核心规则：selected-annulus 是审计镜头，不是替代主口径的排名器。尤其当 selected-only 变强且 route 同时处于 weak-reference 时，应优先解释为边界对照，而不是主工程候选。

---

## 5. 波长机制：为什么 660/404 都要验证

NODI 的核心机制是纳米通道衍射参考场与粒子散射场发生干涉。用简化场强表达式看，总强度可写成 `|E_D + E_S|²`，其中包含通道衍射项、粒子散射项，以及与 `2|E_D||E_S|cosφ` 成比例的交叉干涉项；正是这个 reference/scattering overlap 帮助读出弱散射事件。因此不能只看 Mie scattering，也不能只看 detection_rate；需要看 `Csca → detected field → reference amplitude → cross term → peak → noise/readout → stable detection`。

下表为固定 EV 粒子和几何、以 660 nm 为分母的 EV-pairwise 中位数倍数；仅作为机制解释。本表基于 per-wavelength normalization 的 surrogate 输出，且全部 32032 个 case 的 `cross_wavelength_claim_gate_passed = False`，因此不构成任何跨波长 absolute SNR、LOD 或检出最优 claim。

| 指标，配对中位数相对 660 | 404 nm | 488 nm | 532 nm | 说明 |
|---|---:|---:|---:|---|
| `Csca_m2` | 1.83× | 1.69× | 1.52× | 短波本征散射更强 |
| `E_sca_at_det` | 2.01× | 1.63× | 1.43× | 到探测方向的散射场也增强 |
| `reference_design_amplitude_proxy` | 1.31× | 1.17× | 1.11× | 参考场增强幅度小于散射增强 |
| `abs(cross_term_detector_integrated)` | 3.36× | 2.33× | 1.58× | 干涉项最能体现 404 的短波散射 / 干涉机制信号 |
| `mean_peak_height` | 2.84× | 2.14× | 1.49× | 404 峰更高，但不是稳定覆盖的充分条件 |
| `reference_total_noise_proxy` | 1.001× | 1.001× | 1.000× | 当前 proxy 下噪声几乎不随波长变 |
| `stable_detection_rate` | 0.24× | 0.45× | 0.59× | 读出稳定覆盖并未随短波峰高同步提升 |

**为什么 404 是重点验证但不能只看检出数？** 404 的本征散射、探测场、干涉项和 peak height 都强，但 EV 小粒径/低 RI 事件仍经常不过 detected events 或 stable detection 门槛；同时 404 还需要验证曝光、热效应、滤光片/物镜透过率、EV 完整性和 blank 背景。换句话说，404 是短波机制主验证路线，但它要回答的是“短波增强能否在真实 blank 和样品完整性约束下转化为可用读出”，不是单凭模拟检出数直接冻结为稳定检出最优路线。

**为什么仍需要 488/532 对照？** 它们在 reference-useful 深通道里给出更稳的 EV 覆盖，尤其 532 / 600×1500 有 7/27 all-crossing pass 和 9/27 selected rate≥0.2；488 作为相邻波长可以验证波长趋势与 detector response。正因为 532/488 更稳定，它们适合做中波基准：用来判断 660 的长波读出和 404 的短波机制到底偏离 baseline 多少，而不是取代 660/404 的主验证目标。

**为什么 660 要拆成主验证和边界对照？** 660 的 500/600/700 nm 宽度在当前 reference model 下触发 `reference_too_weak` / NA boundary；这些 route 的 detection count 可能高，但 cross term 和 reference amplitude 并不支持“理想 NODI 增强”解释。因此 660 不是不能做，相反它是本轮长波主问题：`800×1400/1500` 做 reference-useful 长波主验证，`700×1500` 做 weak-reference 对照，二者合起来才能判断 660 的高响应来自可解释干涉读出还是边界效应。

---

## 6. 通道几何：灵敏度、参考场与流体风险的折中

在同一波长内改变几何，reference amplitude 的 route-level 中位数动态范围约 **4×**，cross/interference term 约 **4.2–5.7×**，peak height 从 404 的约 **3.25×** 到 660 的约 **35×**，而 `reference_total_noise_proxy` 只变化约 **1.0–1.01×**。这说明几何不是小修小补，它直接改变参考场和干涉读出。

相对于 `800×700 nm` sanity 几何，几个关键候选的中位数倍数如下：

| 候选相对同波长 800×700 | peak | margin z | abs cross term | reference amp | noise | stable rate |
|---|---:|---:|---:|---:|---:|---:|
| 404 / 600×1300 | 1.50× | 1.53× | 1.78× | 1.74× | 1.006× | 1.09× |
| 488 / 600×1500 | 1.87× | 1.92× | 2.18× | 2.05× | 1.008× | 1.09× |
| 532 / 600×1500 | 2.07× | 2.17× | 2.39× | 2.17× | 1.008× | 1.13× |
| 660 / 700×1500 | 0.074× | 0.055× | 0× | 0× | 0.998× | 1.55× |
| 660 / 800×1400 | 1.80× | 1.91× | 2.18× | 1.78× | 1.004× | 1.07× |
| 660 / 800×1500 | 1.89× | 2.00× | 2.30× | 1.86× | 1.005× | 1.07× |

这解释了为什么 `600×1500` 与 `600×1300` 深通道会成为高敏候选：它们在保持窄宽度参考场优势的同时，用深度提高可用参考/干涉读出；但 600 nm 宽度仍然是激进设计，对 PEG 和堵塞更敏感。`800×700` 更适合作为 Tsuyama-like sanity，因为它接近本项目一直使用的文献近似/系统对照几何，适合验证平台和模拟是否跑在相近机制区间；它不是本轮 full-grid 的最高分 route，也不应直接当 EV 最优。

**PEG-silane 5k 与壁面水合层的推断：** 本轮 summary 没有实测 PEG 后几何，也没有真实 wall adsorption/pressure-flow 数据；因此以下只是工程推断。若 PEG 和水合层让有效宽度/深度每侧缩小 10–40 nm，则 500 nm 宽度最容易被推向堵塞、近壁面偏置和有效 NA/reference 改变；600×1300/1500 仍可作为高敏候选，但要配 blank、Au ladder 和 pressure-flow；800×1400/1500 的 clearance 更大，更适合长波、低风险和 PEG robustness 对照。

---

## 7. EV 粒径分布：小 EV 偏置会如何改变判断

本节使用仓库正式输出 `results/ev_size_weighted_route_analysis.csv`，其默认分析范围为 **60–300 nm** EV 尺寸点。注意它与第 3–4 节的 raw EV route mean 不完全同一口径：第 3–4 节按 **40–300 nm 的 27 个 EV 尺寸模型等权** 聚合；本节按 `tools/ev_size_weighted_route_analysis.py` 的 60–300 nm priors 聚合。因此 `uniform` 列不会等于第 3.1 节的 raw mean，例如 `532 / 600×1500` 在 27-size raw mean 下是 1345/10000，在 60–300 nm uniform 下是 1441/10000。这不是矛盾，而是分母不同。

四个权重场景为：`uniform`、`small_ev_literature`、`broad_ev_literature`、`sharp_msc_sev_empirical`。它们是 sensitivity scenario，不是实际样品分布。真实样品仍需要 NTA/TRPS/EM/orthogonal characterization；不同 EV isolation method 也会改变 EV 的 cargo、蛋白和功能，不应只用粒径权重替代样品表征。

候选面板 all-crossing 加权检出数如下，单位仍是“每 10000 个进入检测区的模拟事件”。

| route | uniform | small_ev_literature | broad_ev_literature | sharp_msc_sev_empirical | reference 解释 |
|---|---:|---:|---:|---:|---|
| 532 / 600×1500 | 1441 | 831 | 1280 | 617 | useful 中波对照 |
| 488 / 600×1500 | 1152 | 616 | 1007 | 447 | useful 中波对照 |
| 404 / 600×1300 | 633 | 290 | 537 | 191 | useful 短波主验证 |
| 404 / 800×700 | 579 | 249 | 481 | 172 | sanity |
| 660 / 700×1500 | 2476 | 894 | 2092 | 213 | weak-reference 对照 |
| 660 / 800×1400 | 1993 | 1315 | 1827 | 1029 | useful 长波主验证 |
| 660 / 800×1500 | 2002 | 1285 | 1822 | 996 | useful 长波主验证 |

**如果真实 exosome/sEV 小粒径更多，660/404 的判断会怎么变？** 数据会让解释更保守：小粒径权重会压低所有 route 的检出数，尤其 404；这说明 404 的短波增强需要真实 blank 和 EV integrity 来证明能否转化为可用读出。660 / 800×1400 在 `small_ev_literature` 和 `sharp_msc_sev_empirical` 下仍显著高于 532/488 中波对照，但跨波长 claim gate 仍未过，且 660 的 detector response、filter、reference/BFP、blank false positives 尚未实测，所以不能说“660 已是真实最优”。实际推荐是：把 660 / 800×1400 或 800×1500 作为长波主验证，并用 532/488 对照量化其相对增益和边界风险。

**404 的短波机制信号会如何表现？** 对 small/sEV-biased priors，404 的 conditional detection proxy 仍低于 488/532 与 reference-useful 660 候选；它的散射/峰高信号仍存在，但不足以越过稳定检出覆盖门槛。因此 404 仍应作为短波主验证路线，但成功标准不能只写成 pass count，而应包括 Au ladder、blank/background、低功率阶梯、曝光后 EV integrity 和与 488/532 对照的波长趋势。

**660 的高检出是否仍受 reference boundary 限制？** 是。`660 / 700×1500` 在各种权重下仍是 weak-reference control；只有 `800×1400/1500` 这种 reference-useful 几何才可被解释为长波 NODI 主验证候选。

---

## 8. Tsuyama 论文数据与本轮结果对照

Tsuyama & Mawatari 2022 的 NODI 机制使用单 nanochannel 衍射作为 reference light，让粒子散射与通道衍射发生干涉，从而实现流动纳米粒子的检测和分类；这适合做本轮 NODI 机制 sanity check。但是本轮不是 Tsuyama absolute reproduction：没有用实测 Tsuyama blank、BFP/slit/pinhole ROI、detector gain、lock-in transfer、真实 gold 标样浓度或原始 trace 校准。因此不能声称复现 Tsuyama detection rate、SNR 或 classification accuracy。

本节把 Tsuyama 论文侧数据与本轮结果分层对照。最重要的边界是：**Tsuyama 对 660 nm NODI 主线有直接约束，对 404 nm 没有等价的直接实验目标**。因此，660 是可用 Tsuyama paper-audit 直接 sanity check 的长波主验证轴；404 是本工程扩展出的短波机制验证轴，只能通过 blank、Au ladder、曝光/EV integrity 和 488/532 中波对照来验证，不能写成“Tsuyama 已经支持 404”。

### 8.1 对照层级地图

| 对照项目 | Tsuyama 论文侧数据 / 协议 | 本轮可比数据 | 对齐判断 |
|---|---|---|---|
| 波长 | 2022 NODI / Table S1 / classification lane 主要覆盖 488、532、660 nm；660 是 NODI gold sanity 的核心波长 | full-grid 覆盖 404、488、532、660 nm；paper-audit lane 覆盖 488、532、660 nm | 660 可直接做 Tsuyama sanity；404 是工程扩展，需单独验证 |
| 通道几何 | paper-audit lane 固定 `800×550` 与 `1200×550 nm`；`800×700 nm` 用作 Tsuyama-like sanity | EV full-grid 推荐 `660 / 800×1400/1500`、`404 / 600×1300`、`532/488 / 600×1500` | paper 几何与 EV 工程几何不同；只能做机制和趋势对照 |
| 颗粒集合 | Au20/Au30/Au40/Au60，Ag40/Ag60；classification 使用 Au/Ag 40/60 | full-grid 有 EV + gold anchors；joint-fit 精确覆盖 Au20/30/40/60 与 Ag40/60 | gold/silver 对照可直接用于 sanity，EV 不是 Tsuyama 论文对象 |
| 读出口径 | 论文最终看 pulse height、pulse width、counts / classification；paper-audit metadata 限定 magnitude / positive readout、ms 级 peak width、5σ/10σ sensitivity | 本轮 full-grid 与 paper-audit 均输出 event-level pulse 和 detection proxy；EV full-grid 使用 5σ EV_NODI preset | 读出结构同构，但 detector gain / blank / lock-in transfer 仍未绝对校准 |
| detection rate | 论文没有提供 crossing-denominator 的 gold detection-efficiency 表 | joint-fit 使用 Au20/30/40/60 selected-annulus target bands 作为 operational / inferred proxy | 可做 paper-aligned proxy，不可写成论文直接复现 |
| 分类准确率 | classification metadata 中保留 `71.9 ± 4.0%` 目标；协议使用 Au/Ag 40/60、488/532 pulse features、SVM | 当前只导出 linked 488/532 features；本地缺 sklearn，未计算 accuracy | protocol 可对照，accuracy 暂无复现 claim |

### 8.2 Table S1 Ag/Au ratio：strict target 与 formula-consistent target

Tsuyama 2022 Supporting Table S1 给出 40 nm Au/Ag 在 488、532、660 nm 的 scattering cross section 与 interferometric scattering 计算值。旧口径直接使用 Table S1 的 interferometric-scattering column 做 Ag40/Au40 ratio；Phase 2.5 复核后发现，Ag 行的 interferometric column 与论文文字“interferometric scattering 近似为 scattering cross section 的平方根”不完全一致。因此本报告同时保留两个读法：strict `interferometric_column_ratio` 用于历史审计，`sqrt_scattering_column_ratio` 作为 formula-consistent target mode。

| wavelength | paper Au40 | paper Ag40 | paper Ag/Au target | 本轮 raw Ag/Au peak ratio | paper-transfer 后 ratio | applied Ag transfer gain | 读法 |
|---|---:|---:|---:|---:|---:|---:|---|
| 488 nm | 0.45 | 1.90 | 4.222 | 1.460 | 4.222 | 2.892 | raw 偏低；bounded transfer 后对齐 |
| 532 nm | 0.68 | 0.89 | 1.309 | 0.686 | 1.309 | 1.908 | raw 偏低；bounded transfer 后对齐 |
| 660 nm | 0.32 | 0.85 | 2.656 | 0.853 | 2.656 | 3.116 | raw 偏低；bounded transfer 后对齐 |

在 strict interferometric-column target 下，当前 raw trace 的 Ag/Au 材料响应明显偏低，需要 wavelength-specific bounded silver transfer；三个 gain 均在当前 guardrail `0.25–4.0` 内，因此可作为 paper-audit diagnostic lens 使用。但在 formula-consistent `sqrt_scattering_column_ratio` 下，full inverse 的 seed-median acceptance 已有 `27` 个 raw candidate 通过 signal-ratio gate，best raw formula score 约 `0.033`。这说明 Ag/Au mismatch 的一部分来自 Table S1 target-mode 解释，而不是必然来自材料或全局 EV 默认错误。

### 8.3 Au selected-annulus detection-rate proxy

下面的 detection-rate target band 是本项目为了 paper-audit 建立的 operational / inferred proxy；论文没有直接给出 crossing-to-detection efficiency 表。当前数值来自 `n_events = 10000`、8 workers、selected annulus `0.5–0.8` 的 joint-fit lane。

| Au diameter | paper-audit proxy band | target | `660 / 800×550` selected rate | `660 / 1200×550` selected rate | 判断 |
|---|---:|---:|---:|---:|---|
| Au20 | 0.15–0.45 | 0.30 | 0.391 | 0.304 | 两个 paper geometry 都在 band 内 |
| Au30 | 0.45–0.75 | 0.60 | 0.715 | 0.616 | 两个 paper geometry 都在 band 内 |
| Au40 | 0.65–0.90 | 0.78 | 0.863 | 0.799 | 两个 paper geometry 都在 band 内 |
| Au60 | 0.85–0.98 | 0.92 | 0.908 | 0.854 | 两个 paper geometry 都在 band 内 |

这一组结果是目前最接近“Tsuyama-like detection 数值对齐”的证据：Au20 到 Au60 单调增强，且 660 nm 两个 paper geometry 均落入 operational band。更完整的 6-case acceptance 中，Au20 只有 `3/6` 个 cases 落入 band，但 miss 全部偏低；这与论文中 Au20 weak-SNR、not-all-detected 的描述相容，当前已降级为 warning。Au20 过高、Au20/Au30 倒挂、Au30-60 severe miss 仍会作为 hard gate。它仍然只是 selected-annulus / proxy 口径，不是绝对 detection efficiency 复现。

### 8.4 SNR、size response 与 joint-fit 诊断

| 指标 | Tsuyama 论文 / paper-audit target | 本轮 joint-fit 结果 | 判断 |
|---|---|---|---|
| Au30/Au20 SNR ratio | 论文报告 Au20 平均 SNR 约 12、Au30 平均 SNR 约 33；target ratio = 2.75 | median ratio = 3.36 | 方向一致但偏高约 22%；说明 readout/noise 仍不是绝对校准 |
| Au size exponent | paper-audit target = 2.3 | raw peak-height exponent 约 3.2；bounded paper-lane correction 后 = 2.300，delta 约 -0.96 | raw size response 偏陡；bounded correction 可对齐，但只限 paper-audit lane |
| annulus fraction | guardrail ≥ 0.25 | min annulus fraction = 0.381 | selected-annulus 分母足够，不是空分母拟合 |
| joint-fit status | lower-is-better score，要求 transfer / size guardrail 不违规 | best score = 0.499，`candidate_joint_fit_with_paper_transfer` | 可作为 diagnostic local paper-fit lens，不改变 EV 主库 |

因此，Tsuyama 数值对齐目前最稳的是“660 nm Au selected-rate proxy 大体合理”和“Table S1 Ag/Au ratio 在 formula-consistent target 下 raw signal 已接近、在 strict target 下可由 bounded transfer 对齐”。真正仍未解决的是 raw Au size-response：seed-median acceptance 下 best raw size score 仍约 `1.632`，没有 raw family 同时通过 signal 与 size。这个问题更可能需要 reference phase / BFP ROI / collection operator / pulse-readout 进一步诊断，而不应通过改 EV 全局默认来硬贴。

### 8.5 488/532 classification protocol 对照

Tsuyama 2022 的 Au/Ag classification 使用 Au40、Au60、Ag40、Ag60，以及 488/532 nm 的 pulse height / width 类特征。当前 classification lane 只做了协议级 feature export，不做 accuracy claim。

| 项目 | Tsuyama 侧目标 / 协议 | 本轮 classification lane | 判断 |
|---|---|---|---|
| class set | Au40、Au60、Ag40、Ag60 | 完全一致，4 classes | protocol 对齐 |
| wavelength | 488 / 532 nm dual-wavelength | linked 488 pulse window + 532 window maximum | protocol 对齐 |
| feature rows | 论文按 class 构造分类数据集 | 400 events/class，1600 rows | 数据量足够做 smoke，但不是论文原始数据 |
| usable rows | 需同时有可用 linked features | usable_for_paper_svm = 849，min class count = 196 | 四类均有可用样本 |
| accuracy | metadata target `71.9 ± 4.0%`，但当前报告不把它列为 hard acceptance | sklearn unavailable，`no_accuracy_claim` | 暂不能声称复现 classification accuracy |

分类 lane 的价值是确认 488/532 中波对照不只是 detection-rate baseline，也可以继续承担 Tsuyama-like dual-wavelength feature sanity；但在 sklearn / exact protocol / source audit 完成前，classification 只能是 diagnostic。

### 8.6 Full-grid Gold anchor 在候选路线中的趋势

| route | Au20 | Au30 | Au40 | Au60 | 读法 |
|---|---:|---:|---:|---:|---|
| 404 / 600×1300 | 2 | 3 | 10 | 40 | 小金颗粒递增，但 404 候选仍不过硬门槛 |
| 404 / 800×700 | 7 | 22 | 29 | 75 | Tsuyama-like sanity 几何可看 size trend |
| 488 / 600×1500 | 6 | 27 | 58 | 110 | 中波对照下金 ladder 有清楚递增 |
| 532 / 600×1500 | 9 | 31 | 76 | 179 | 中波对照基线，Au60 更明显 |
| 660 / 700×1500 | 0 | 391 | 646 | 918 | 数值强但 reference too weak，不当主解释 |
| 660 / 800×1400 | 55 | 103 | 232 | 402 | 长波 reference-useful sanity 可用 |
| 660 / 800×1500 | 45 | 120 | 180 | 413 | 长波 reference-useful sanity 可用 |

数值单位均为 detected/10000。Au20/Au30/Au40/Au60 趋势总体符合“小粒子难、大粒子更容易”的 NODI sanity；部分全尺寸 gold ladder 在 20–300 nm 不严格单调，这是 Mie resonance、phase、geometry/readout 和工程 gate 共同作用的结果，不应被简单视为错误。`532 / 600×1500` 对 gold 20–300 nm 的 detection_rate 是单调递增的，这对中波对照基线是有利 sanity。

### 8.7 EV 推荐是否物理合理

是，作为 relative/proxy ranking 是合理的：EV 小尺寸 40–150 nm 大多不过门槛，240–300 nm 在 532 / 600×1500 中波对照通过；488 只有 280–300 nm 通过；660 / 800×1400 从 180 nm 开始通过。这与 Mie scattering 随尺寸增强、NODI 干涉项放大弱散射的基本趋势一致。Gold anchor 的作用是检查链路有没有明显反常，不是把 gold 的 absolute 检出率迁移到 EV。

### 8.8 与本工程 660/404 口径的关系

Tsuyama paper-audit 给本报告提供的是 **660 nm 长波 sanity anchor**：在 paper geometry、Au/Ag 材料 ratio、Au size/SNR proxy 上，660 可以被详细对照。它不能直接替代本轮 EV full-grid 的 660 / 800×1400/1500 工程选择，因为后者是更深通道的 EV design route；但它支持“660 是值得作为长波主验证轴”的总体方向。

404 nm 的情况不同：Tsuyama 2022 NODI 不是 404 nm 实验，因此 404 的主验证必须依靠本工程自己的 blank/background、exposure、Au ladder、EV integrity 和 488/532 中波对照来建立。报告中把 404 写成“短波机制主验证”，不是因为 Tsuyama 已经验证了 404，而是因为 full-grid 显示短波 scattering / cross term / peak proxy 具有机制信号，但稳定检出覆盖仍需实验确认。

### 8.9 Phase 2 paper-audit 当前状态

2026-05-04 已按 Phase 2 roadmap 建立并跑完整个 Tsuyama paper-calibrated selected-annulus proxy lane：target audit、read-only acceptance baseline、A-E family-ladder inverse、8-worker / 3-seed `10000 events/case` full run、classification diagnostic smoke 和 `reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md` 均已生成。full run 覆盖 `52` 个 candidate、`156` 条 seed summary、`5616` 条 raw joint-case rows，运行约 `6.94 h`。

这一步不改变本报告的 EV full-grid 主结论：selected-annulus 仍固定 `0.5–0.8`，all-crossing 仍是主工程口径，660/404 第一轮实验面板不被 Phase 2 阻塞。Phase 2 的最终签发状态为 `negative_or_diagnostic_result_only`；当前唯一主 No-Go 是 `raw_size_response_alignment_not_met`。检测率现在被分层解释为 `partial_pass_with_Au20_low_warning`：Au20 偏低是 warning，Au30/Au40/Au60 只有 borderline/minor warning，不是 release blocker。A-D raw / non-transfer families 在 formula-consistent Table S1 target 下已有 raw signal 候选通过；strict Table S1 signal 保留为 `strict_table_s1_signal_unresolved_formula_signal_pass` diagnostic warning；但没有 raw family 形成 size-response alignment。E-family local Ag transfer + Au size-response correction 只能作为 bounded diagnostic lens。因此它支持“Tsuyama paper-audit proxy 仍有诊断价值”，但不支持“已完成 paper-calibrated candidate 签发”。

Phase 2.5 已继续跑 D2 raw-operator smoke：`1500 events/case`、`20` candidates、seeds `42/43/44`、`8 workers`。结果没有任何候选满足 promote rule。`tau_2ms_global_refphi_plus` 的 joint score 最低，raw Au size exponent 约 `3.09`，比 control 略好但仍离 `2.3` 很远；`bfp_lobe_045` 的 formula-consistent Ag/Au signal score最好，但触发 guardrail 且 size exponent 更差。

随后又按最小 D2.1 方案跑了局部 refphase/collection smoke：`2000 events/case`、`12` candidate variants、seeds `42/43/44`、`8 workers`。这一步只检查 `tau_2ms_control`、`global_refphi_plus` 的 `+0.2/+0.4/+0.6` 小步长、`collection_narrow` 与 `global_refphi_plus + collection_narrow` 组合。D2.1 的 best joint candidate 是 `tau_2ms_global_refphi_plus_collection_narrow`，formula-consistent Ag/Au signal score 约 `0.0286`，raw Au exponent 约 `3.071`；best raw size candidate 是 `tau_2ms_global_refphi_plus_0p6`，raw Au exponent 约 `3.050`，size score 约 `1.149`。二者均 guardrail pass，且 detection alignment 已是 pass/warning 级别，但仍没有达到 `raw Au exponent <= 2.85` 的 promote floor，更没有接近 `2.3`。

因此当前仍不进入 raw-family `10000 events/case` confirm。代码侧已补入 seed-median signing、epsilon/severity detection gate、target-mode score、input manifest/hash 与 D2 inert diagnostic；D2.1 进一步说明计算侧小范围 refphase/collection 调整只能带来有限改善。随后 Phase 2.6 在同一 acceptance 工具内做 read-only paper-reproduction rescore，没有改变 selected-annulus：D2.1 rescore best 为 `tau_2ms_global_refphi_plus`，`paper_reproduction_score_formula = 3.7428`，需要全局 Au size-response delta `-0.7973` 和 single global SNR scale `0.7279` 才能把 corrected Au exponent 映射到 `2.3`；full inverse rescore best 为 `refspace_0p25__paper_5sigma_sensitivity`，score `4.6815`，delta `-0.9583`，SNR scale `0.4138`。这说明如果只追“用估计项复现论文数值”，最小有意义的 correction 是全局 Au size flattening，而不是继续扫 annulus 或 per-case 参数。

按这个判断，又在现有 inverse 工具内新增 size-only `F_paper_reproduction_fit` family，并跑了 `3000 events/case` × seeds `42/43/44` × `8 workers` 小确认。最佳候选为 `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit`，`paper_reproduction_score_formula = 3.9541`，required/applied global size delta `-0.8782`，SNR scale `0.7304`，formula signal loss `0.0346`，SNR-ratio loss `0.4684`，detection alignment 为 pass/warning 级别；但 status 仍是 `reproduction_fit_not_met`。因此该路径确认了“size-only 估计项能稳定改善数值贴合”，但还不足以进入 `10000 events/case` confirm，也不签 raw calibration、不回写 EV full-grid。

继续按“只增加一个全局估计项”的边界做 Phase 2.7 read-only rescore：在同一个 3000-event summary 上加入 single global SNR response exponent + scale。最佳候选仍是 `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit`，SNR response exponent 为 `0.812`，SNR-ratio weighted loss 从 `1.405` 降到 `0.423`，但 complexity weighted loss 从 `1.340` 升到 `1.931`，综合 score 只降到 `3.8076`。因此单一 SNR/readout 估计项有帮助但不足以过 bounded partial，仍不进入 `10000 events/case` confirm。

进一步按“只复核评分叙事、不新增仿真自由度”的边界做 Phase 2.8 reviewed/descriptive rescore：strict Table S1 interferometric-column residual 改为 report-only，不再进入 primary reproduction score；detection warning 与 fit complexity 也按描述性复现目标降权。最佳候选仍不变，reviewed score 降至 `1.9385`，状态为 `bounded_reproduction_partial_descriptive`。这个结果说明：如果目标只是描述“现有估计项能把 Tsuyama 数值贴近到什么程度”，当前低自由度 fit 已达到一个可读的 partial reproduction；但它不是 acceptance，不改变 `negative_or_diagnostic_result_only`，No-Go 仍是 `raw_size_response_alignment_not_met`，也不触发 `10000 events/case` confirm。

继续沿“路线 2”做 Phase 2.9 maximal upper-bound rescore：不新增事件模拟、不改变 selected-annulus，而是在 acceptance 工具中只读加入 hypothetical strict Table S1 per-wavelength Ag transfer，用它回答“如果接受更高自由度的 strict Ag transfer，上限能贴到多近”。3000-event size-only best 仍是 `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit`，maximal score `1.2869`，仅为 `maximal_paper_fit_partial_upper_bound`；full inverse best `refspace_0p25__paper_5sigma_sensitivity` score `0.9814`，D2.1 best `tau_2ms_global_refphi_plus_collection_narrow` score `0.9893`，二者可达 `maximal_paper_fit_upper_bound`。但这一路径需要 hypothetical Ag transfer gains 约 `1.76-3.12`，并叠加 global Au size-response / SNR response 估计项；因此它只证明“当前结果在更高自由度 paper-reproduction lens 下有数值上限”，不证明 raw physical family 自然对齐。release 仍是 `negative_or_diagnostic_result_only`，No-Go 仍是 `raw_size_response_alignment_not_met`，所以这一步是当前计算路线的合理停点。

Phase 2.10 又对 raw Au size-response 做了只读拆解：D2.1 best 的 peak-height median exponent 为 `3.0679`，local-SNR median exponent 为 `3.0882`，而 `peak_margin_z` 与 `peak_height×width` 更陡。所有 peak-height case 的主要残差都来自 `40-60 nm` pair，660 nm 与 `1200x550` 最接近，532 nm / `800x550` 最偏。这个结果说明，当前不应把努力放回 Au20 检出率或 annulus 窗口；如果还要继续计算，只剩一个相对有意义的方向：单一全局 pulse-height/readout compression 项。但它仍应被视为 reproduction-only lens，不改变 EV full-grid 的 660/404 工程结论。

Phase 2.11 已把这个最后的计算方向显式化为 `paper_reproduction_response_compression` score mode：同一个 `gamma` 同时作用于 Au size-response、Au20/Au30 SNR ratio 和 Ag/Au signal ratio，不允许 per-wavelength / per-geometry / per-diameter 压缩。D2.1 best 为 `tau_2ms_global_refphi_plus_collection_narrow`，`gamma=0.749`，压缩后 Au exponent 正好映射到 `2.3`，formula-consistent Ag/Au loss 仍低，但总分为 `2.033`，略高于 bounded partial 阈值 `2.0`；full inverse best score 为 `2.651`，3000-event size-only best score 为 `3.722`。这说明即使给一个全局单自由度 readout compression，数值也只能接近“descriptive partial”，不能升级为 paper-calibrated raw candidate。计算路线到这里已经基本收口：再往下若要降分，只能引入 per-size/per-case/logistic remap 等更高自由度项，那会变成过拟合而不是可解释 reproduction lens。

2026-05-06 的 stop-decision 复核后，本报告采用这个收口结论：**Tsuyama paper-fit 的无实测计算搜索停止；实际仪器工程模拟仍可继续，但它属于 hardware / statistics validation，不属于继续寻找 accepted Tsuyama raw-fit candidate。** 两个后续只读敏感性检查已经补入工程判断：ET-2030 + LI5640 方向提示 current-input / TIA 接法才是合理路径，50 Ω voltage path 对 pA 级信号风险很高；paper-matched finite-count / IQR / vendor diameter prior 可以作为统计敏感性，但不能单独把 Au40-Au60 slope 自然压到 `2.3`。因此本报告不再把“继续调参复现 Tsuyama 数值”列为下一步，而把后续重点放到硬件链路、真实 blank/BFP/Au pulse trace 和实验面板执行。

---

## 9. 第一轮实验推荐面板

### 9.1 芯片/波长路线

| 面板角色 | 推荐 route | 目的 |
|---|---|---|
| 长波主验证 A | 660 / 800×1400 | 验证 660 下 reference-useful 长波读出，尤其小 EV weighting 下的 proxy 表现 |
| 长波主验证 B | 660 / 800×1500 | 与 800×1400 并列验证深通道长波路线，观察 geometry robustness |
| 长波边界对照 | 660 / 700×1500 | 专门验证 reference_too_weak / NA boundary，不作为理想 NODI 解释 |
| 短波主验证 | 404 / 600×1300 | 验证短波散射、cross term、peak/margin 与曝光、blank、EV integrity 风险 |
| 短波 sanity | 404 / 800×700（首选）；可选 532 / 800×700 | 验证平台对 nanochannel diffraction / Au ladder 是否在合理趋势内；首选 404 与短波主验证轴对齐，532 仅作为中波 Tsuyama-like 行为备选 |
| 中波对照 A | 532 / 600×1500 | 提供稳定 reference-useful baseline，衡量 660/404 与中波的差距 |
| 中波对照 B | 488 / 600×1500 | 验证相邻中波 detector/filter response 与波长趋势 |
| 几何 robustness | 700/800/900 × 1200–1400 | 验证 PEG/fluidic/clearance 与 reference 的 trade-off |

### 9.2 必做 control

- **Blank/background**：每个波长、每个几何都要 blank channel trace；必须估计 empirical false-positive，不再只用 Gaussian iid surrogate。
- **Au ladder**：Au20/Au30/Au40/Au60 至少覆盖；建议加 Au100/Au200 作为动态范围和饱和/非线性检查。
- **EV mimic / bead / contaminant controls**：liposome/EV mimic、silica/PS bead、protein aggregate 或 lipoprotein-like control，用来检查 EV/contaminant overlap。
- **BFP/slit/reference scan**：记录空通道 BFP、slit/pinhole ROI、selected-annulus 对应区域，直接校准 reference operating band。
- **ET-2030 + LI5640 接法**：优先验证 current-input / 低噪声 TIA 链路，记录 full-scale、input range、time constant、filter order、demod phase 与 sampling；不要默认 50 Ω voltage input 足够。
- **all-crossing vs selected-annulus 对照**：实验上尽量记录位置/ROI 或 surrogate annulus 子集，验证 selected lens 是否确实偏乐观。
- **paper statistics sensitivity**：Au size-response 需要保存 raw pulse height/width/area/local-SNR，按 Tsuyama-like finite-count 与 IQR trimming 复算，而不是只保存 summary mean。
- **particle size prior**：Au20/Au30/Au40/Au60 最好记录供应商批次、DLS/TEM 或至少 nominal CV，用来判断 size-response 残差是否受真实粒径分布影响。
- **Optical exposure / EV integrity**：404 nm 必须记录功率、曝光、温升 proxy、EV 前后 NTA/TRPS/EM 或至少 size distribution 变化。
- **Fluidic/PEG**：PEG 前后通道流阻、pressure-flow curve、堵塞率、吸附/滞留 trace；重点比较 600 nm 与 800 nm 宽度。

---

## 10. 不能过度解读的地方

1. **不要把 detection_rate 当浓度。** 它是进入检测区事件的条件检出概率，不包含真实进样、吸附、堵塞、死时间、浓度和 false positives。
2. **不要声称 absolute SNR / LOD。** detector-unit chain、Mie-to-power chain、blank trace、detector gain、photon unit noise 都未校准。
3. **不要声称真实跨波长最优。** 本库是 per-wavelength normalization，cross-wavelength claim gate 全部 false。
4. **不要把 selected-annulus 当主口径。** 它可用但系统性偏乐观，且只覆盖约 40% 事件子集。
5. **不要把 660 / 700×1500 当理想 NODI 主推荐。** 它是 weak-reference control。
6. **不要把 532/488 的稳定对照误写成工程目标优先级。** 本工程主要想验证 660 和 404；532/488 的价值是提供中波 baseline 和趋势参照。
7. **不要用 2020 POD 或 2024 paired POD+NODI 来校准本轮 EV NODI detection rate。** 本报告只把 Tsuyama 2022 NODI 机制作为 sanity check；2020 POD 是 photothermal thermal counting，2024 是 paired absorption/scattering classification，不应混用作本轮 EV full-grid 标定。
8. **不要把 EV biological specificity 作为已证明结论。** 需要 orthogonal EV characterization、contaminant controls 和 classification/label-free specificity validation。
9. **不要把 Phase 2.11 response compression 写成 raw calibration。** `gamma=0.749` 是 reproduction-only lens，接近 descriptive partial 但没有通过 bounded partial，也不能回写材料、annulus 或 EV full-grid。

---

## 11. 下一步分析和实验清单

1. 冻结计算侧 paper-fit 结论：Phase 2/2.11 保持 `negative_or_diagnostic_result_only`，不再扩大无实测 D2/noise/threshold/annulus 搜索；正式记录见 `reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md` 与 `reports/50_计算侧收口总结与工程瘦身记录.md`。
2. 生成实验版 `candidate_panel.csv`：按 660/404 优先、532/488 对照的顺序列出推荐 route、blank、Au ladder、EV mimic、BFP scan、ET-2030/LI5640 接法和 raw pulse export 要求。
3. 对每个候选 route 采集 blank trace，估计 empirical false-positive rate、colored noise、drift、threshold stability。
4. 采集空通道 diffraction / BFP / slit / pinhole ROI，替换 `not_configured_surrogate` collection operator。
5. 明确 ET-2030 + LI5640 detector-unit chain：current input / TIA、full-scale、time constant、filter order、demod phase、sampling interval、noise floor、saturation margin；若使用 50 Ω voltage path，必须单独证明信号量级足够。
6. 用 Au20/Au30/Au40/Au60/Au100/Au200 做 detector gain、dynamic range、response compression 和 NODI reference sanity；同时保存 raw pulse trace，用 finite-count / IQR / diameter-CV sensitivity 复算 size-response。
7. 在 660 / 800×1400 与 660 / 800×1500 上优先做 EV mimic 与真实 EV 读出，验证 reference-useful 长波路线。
8. 在 660 / 700×1500 上专门验证 weak-reference boundary，判断高检出数是否来自不可解释边界效应。
9. 在 404 / 600×1300 上做低功率阶梯、曝光前后 EV integrity、blank false positives 和 Au ladder。
10. 在 532 / 600×1500 与 488 / 600×1500 上做中波对照，量化 660/404 相对 baseline 的差距和波长趋势。
11. 对 PEG-silane 5k 前后做 pressure-flow、堵塞率和有效通道尺寸 proxy。
12. 将实测 blank / standard / BFP / detector response 反馈到 simulator，解锁 detector-resolved ranking；在此之前不要升级到 absolute claim。

---

## Appendix A. 使用的数据文件

本报告使用的数据与约束来自 full recompute 输出、summary 分片和 JSON health/runtime/meta/freeze 文件；任务说明明确要求合并 18 个 summary 分片、检查 selected-annulus 字段，并限制 claim 边界。

实际读取/复核：

- `summary_part_001.csv` … `summary_part_018.csv`，合并后 32032 rows。
- 完整 summary 以单文件 `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv` 形式保留；旧上传分片副本已经清理，不作为正式数据源。
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`，用于 Codex 审阅复算关键 raw summary 数字。
- `ev_design_full_range_biomimetic_exosome_with_anchors_10000e_meta.json`。
- `ev_design_full_range_biomimetic_exosome_with_anchors_10000e_result_health.json`。
- `ev_design_full_range_biomimetic_exosome_with_anchors_10000e_runtime_performance.json`。
- `ev_design_full_range_biomimetic_exosome_with_anchors_10000e_freeze_probe.json`。
- `results/ev_size_weighted_route_analysis.csv`。
- `results/ev_size_weighted_route_analysis_selected_annulus_ranking.csv`。
- `results/tsuyama_selected_annulus_joint_fit_v2_size_response_10000e_20260501/selected_annulus_joint_fit_summary_v2.csv`。
- `results/tsuyama_selected_annulus_joint_fit_v2_size_response_10000e_20260501/selected_annulus_joint_fit_report.md`。
- `results/tsuyama_2022_classification_lane_v2_400e_20260501/tsuyama_2022_classification_summary_v2.csv`。
- `results/tsuyama_2022_classification_lane_v2_400e_20260501/tsuyama_2022_classification_report_v2.md`。
- `results/tsuyama_phase2_acceptance_full_inverse_v1/` 与 `results/tsuyama_phase2_parameter_inverse_full_v1/`，用于 Phase 2 full inverse acceptance。
- `results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/` 与 `results/tsuyama_phase2p5_d2p1_refphi_collection_acceptance_v1/`，用于 D2.1 raw refphase/collection smoke。
- `results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/`、`results/tsuyama_phase2p7_snr_response_rescore_3000e_v1/`、`results/tsuyama_phase2p8_reviewed_score_rescore_3000e_v1/`、`results/tsuyama_phase2p9_maximal_upper_rescore_3000e_v1/`、`results/tsuyama_phase2p10_size_response_decomposition_d2p1_v1/` 与 `results/tsuyama_phase2p11_response_compression_rescore_d2p1_v1/`，用于 paper-reproduction 收口判断。
- `results/instrument_hardware_feasibility_v1/` 与 `results/tsuyama_paper_statistics_sensitivity_v1/`，用于 ET-2030 + LI5640 feasibility 与 paper-statistics sensitivity。
- `reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md` 与 `reports/50_计算侧收口总结与工程瘦身记录.md`，用于最终 Phase 2/2.11 收口叙事。
- `47_EV_NODI全量结果分层分析报告.md`，仅作旧结论对照，不作为本轮数值来源。

---

## Appendix B. 关键字段解释

| 字段 | 本报告用法 |
|---|---|
| `detection_rate` / `all_crossing_detection_rate` | 主口径检出率，按所有 crossing 事件计算 |
| `detected_per_10000` | 本报告中由 `detection_rate × 10000` 得到，仅为条件模拟事件检出数 |
| `stable_detection_rate` | 读出稳定检出率，参与工程 gate 与 ranking |
| `mean_peak_margin_z` | 峰值相对阈值的 z-margin proxy，不是 absolute SNR |
| `final_engineering_score` | 单 case 工程综合分；EV route 以 EV 聚合字段与 pass count 一起看 |
| `final_EV_design_score` | EV ensemble route 层综合分；不能单独覆盖 reference/gate/blocker |
| `engineering_gate_passed` | 当前 surrogate 工程门槛是否通过 |
| `reference_operating_band` | `electronics_noise_limited_useful` 可按 reference/interference 解释；`reference_too_weak` 只能作边界/对照 |
| `selected_detector_mode_annulus_detection_rate` | selected-annulus 子集检出率；交叉验证口径，可能偏乐观 |
| `selected_detector_mode_annulus_fraction` | selected 子集占全事件比例；本轮均值约 0.402 |
| `selected_detector_mode_annulus_contribution` | `fraction × selected detection rate`；表示 selected 子区对全体 crossing 分母的贡献，用来约束 selected rate 的乐观解释 |
| `selected_detector_mode_annulus_uplift` | selected rate 相对 all-crossing rate 的倍率；>1.6× 时在 route analysis 中标记为 high-uplift warning |
| `selected_annulus_reference_interpretation` | route-level selected 解释状态；reference-useful 可作交叉验证，weak-reference 只能作边界对照 |
| `selected_annulus_fraction_guardrail_status` | route-level fraction guardrail；<0.35 为工程警告，<0.25 为失败 |
| `selected_annulus_rank_scope` | selected ranking CSV 的排序范围；本版默认 `reference_useful_only`，weak/unknown-reference route 另写入 boundary top routes |
| `*_weighted_detection` | `ev_size_weighted_route_analysis.csv` 中的 size-weighted all-crossing sensitivity；默认 EV 直径范围 60–300 nm；对应 `uniform`、`small_ev_literature`、`broad_ev_literature`、`sharp_msc_sev_empirical` 四个 prior；不等同于 section 3–4 的 40–300 nm raw EV mean |
| `fluidic_practicality_score` | 静态 hydraulic proxy；未实测 pressure-flow，不能当真实流体结论 |
| `ev_clearance_margin_nm` | 几何 clearance proxy；PEG/水合层会改变有效值，当前未实测 |
| `cross_wavelength_claim_gate_passed` | 全部 False；阻止真实跨波长最优 claim |
| `detector_operator_caution_flag` | detector/operator 未充分校准的 caution；阻止 absolute claim |

---

## Appendix C. 可复核的关键表格

### C1. `700/800/900 × 1200–1400 nm` 面板摘要

| wavelength | panel 内推荐读法 | 关键数字 |
|---|---|---|
| 404 | 700×1400 / 800×1300–1400 可做短波 geometry robustness，但 0/27 pass | top final-score `700×1400`: 507/10000，selected 595/10000 |
| 488 | 700×1400、800×1400、900×1400 是中等风险 geometry scan，不如 600×1500 中波对照基线 | `700×1400`: 913/10000，selected 1069/10000，0/27 pass |
| 532 | 700×1300/1400 可作为中波对照周边 robustness | `700×1400`: 1162/10000，4/27 pass，selected 1358/10000 |
| 660 | 700×1200–1400 是 weak-reference；800/900×1200–1400 是 reference-useful 长波主验证候选 | `800×1400`: 1866/10000，13/27 pass，selected 2278/10000 |

### C2. candidate EV 尺寸通过范围

| route | all-crossing pass EV diameter | selected rate≥0.2 EV diameter |
|---|---|---|
| 532 / 600×1500 | 240–300 nm | 220–300 nm |
| 488 / 600×1500 | 280–300 nm | 250–300 nm |
| 404 / 600×1300 | none | none |
| 404 / 800×700 | none | none |
| 660 / 700×1500 | 160–300 nm，但 reference_too_weak | 150–300 nm，但 reference_too_weak |
| 660 / 800×1400 | 180–300 nm | 140–300 nm |
| 660 / 800×1500 | 190–300 nm | 160–300 nm |

注：`none` 表示 27 个 EV 尺寸点（40–300 nm，10 nm 间隔）均未通过 `engineering_gate_passed`；`reference_too_weak` 表示该 route 的 EV 尺寸点落在 weak-reference band，对应 pass 数只能作为 stable/margin 工程信号看待，不能解释为 NODI reference-useful 干涉读出。

### C3. old report 与新 summary 的主要数字修正

| route | 旧报告典型检出/10000 | 本轮 raw summary all-crossing/10000 | 修正说明 |
|---|---:|---:|---|
| 404 / 600×1300 | 520 | 587 | 方向一致，数值以新 summary 为准 |
| 404 / 800×700 | 431 | 539 | 方向一致，数值以新 summary 为准 |
| 488 / 600×1500 | 970 | 1073 | 方向一致，数值以新 summary 为准 |
| 532 / 600×1500 | 1305 | 1345 | 方向一致，数值以新 summary 为准 |
| 660 / 700×1500 | 2856 | 2292 | 仍为 weak-reference 对照，不能主推 |
| 660 / 800×1400 | 约 1966 | 1866 | 仍为可解释长波候选 |
| 660 / 800×1500 | 约 1957 | 1873 | 仍为可解释长波候选 |
