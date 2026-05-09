# EV/NODI 设计决策平台升级路线图与修改框架

> 当前状态：2026-05-08 复核版。旧版“Tsuyama 对齐主链升级路线图”中的 P0-P6 可落地项已经完成，完成态正文已归档到 [archive/tsuyama/59_Tsuyama对齐主链升级路线图与修改框架_2026-04-24完成态.md](./archive/tsuyama/59_Tsuyama对齐主链升级路线图与修改框架_2026-04-24完成态.md)。根目录文件43保留为历史/治理路线图；当前综合结论以 `reports/88_*` 为准，v2 无实测边界以 `reports/87_*` 和 `reports/84_*` 为准。

> 2026-05-08 补充：selected detector-mode / selected-annulus 已成为固定交叉验证口径，canonical annulus 保持 `0.5-0.8`；旧临时 plan 和旧 selected-detector-mode 探索结果已被 Phase 2 acceptance、D2/D2.1、Phase 2.6-2.11、v2 closure 和 `reports/88_*` 取代，不再作为当前证据入口。

> 2026-04-27 波长与几何网格口径修正：正式 `ev_design + full_range_biomimetic_exosome_with_anchors` 必须覆盖 `404 / 488 / 532 / 660 nm`，并使用 `11` 个宽度节点与 `13` 个深度节点，即 `32032 cases × 10000 events/case`。此前三波长 `7056 cases` 或旧几何 `9408 cases` 结果库只能视为 stale partial coverage，不能作为 current truth。

> 当前重算判断：formal EV full-grid recompute 已完成，只签 relative/proxy/diagnostic EV design decision library。没有实测 blank / standard particle / BFP ROI / lock-in transfer / detector-unit 数据时，P2/P3 继续保持 data-blocked / calibration-ready / future-high-fidelity lane，不得输出 calibrated SNR、absolute LOD、absolute EV concentration、真实跨波长 detector-unit 优劣或 biological EV specificity claim。若目标改为 experimental calibrated platform，必须等 P2/P3 的真实数据或高保真 solver 接入后再升级 claim。

## 总判断

这批新建议应该吸收进路线图。它把上一版的 EV ensemble、Au20-equivalent、reference design score、fluidic penalty、Pareto、dashboard advisor 往更底层推进了一步：不仅要回答“哪个 case 分数高”，还要回答这个分数是否稳健、是否可校准、是否能经受参考场不确定性、对准/制造误差、空白噪声、污染物重叠、EV reporting 规范、样品前处理、选择偏差、事件级伪差、跨波长/跨物镜归一化误读、NODI 非同步读出语义、BFP mode-overlap、particle-channel perturbation 双计数、单位/轴约定、全 trace population 效应、光学硬件选择和 laser exposure 安全风险。

下一版代码目标应改成：

```text
Which chip + assay-control panel can produce interpretable EV-like
single-particle measurements under optical, transport, calibration,
sample-preparation, reporting, and run-state uncertainty?
```

也就是：

```text
最大分数
  -> 稳健可检测
  -> 可校准
  -> 可解释
  -> 可实验验证
  -> 可报告 / 可审计
```

## 全量重算前的策略

如果目标是“全部修改后再全量重算”，这里的“全部”应定义为：

1. **所有不依赖实测数据的代码、schema、surrogate、后处理和测试先完成。**
2. **依赖实测数据的 lane 先完成接口、manifest、claim blocker、synthetic guard 和 dashboard 暴露，但不解锁 quantitative claim。**
3. **昂贵的 Monte Carlo/seed/alignment/fullwave 不默认乘到每个 full-grid case 上。** 主全量库生成基础宽表；候选精修库再对 top panel 做 seed replicate、alignment/fabrication MC、physics model consensus。

因此，正式全量重算前需要完成的是 **P0-hard、minimum required schema、P0-soft 的 skeleton/blocker 字段，以及能证明这些字段可用的 smoke path**；P1 只要求完成会直接参与 smoke/postprocess 的最小接口，不要求把所有 P1-active 功能做成正式主求解器。P2/P3 中需要真实 blank/standard/transfer/fullwave 数据的部分只做 calibration-ready 接口和 blocker。P0 的含义不是“所有新物理都进主求解器”，而是 full-grid 输出不能缺少会改变 claim 的基础字段、risk flag、selection/QC metadata 和 blocker。

## 冻结版结论

v5 作为 EV/NODI 设计决策平台总路线图冻结。后续不再新增大模块或新方向，除非发现会改变 W/H/lambda/objective 推荐的硬物理漏洞。

正式 full-grid recompute 前，只允许围绕以下事项收束实现：

```text
1. P0-hard gates
2. minimum required summary schema
3. smoke grid
4. dashboard blocker visibility
5. recompute manifest / hash / schema inventory
```

没有实测 blank / standard particle / BFP ROI / lock-in transfer function 前，所有输出均为 relative/proxy/diagnostic design decision；不得输出 calibrated SNR、absolute LOD、absolute EV concentration 或 biological EV specificity claim。

## 新线程接手说明

如果一个新线程只看到这个文件，应按下面规则接手，不要重新扩张路线图：

```text
目标：
  把当前 simulator 从 single-case engineering ranker 升级为
  claim-governed EV/NODI design decision platform。

当前阶段：
  v5 冻结版的非实测实现已收束。P0-hard gates、minimum required schema、
  P0-soft skeleton/blocker、smoke grid、dashboard blocker visibility、
  recompute manifest/hash/schema inventory 和 P1 diagnostic/scaffold
  已经可用于下一轮 relative/proxy/diagnostic full-grid recompute。
  P2/P3 保持 data-blocked，等待真实校准数据或高保真 solver。

不要做：
  不要新增大方向。
  不要把 P1/P2/P3 全部当作 formal recompute 前置条件。
  不要在没有实测 blank/standard/BFP/transfer function 时输出 calibrated SNR、
  absolute LOD、absolute EV concentration 或 biological EV specificity claim。
```

新线程开始实施前，先核对这些本地代码入口：

```text
nodi_simulator/data_objects.py:
  SimulationConfig、readout preset、detector_forward_model、normalization_mode、
  particle_induced_channel_perturbation_model、initial_position_distribution_mode。

nodi_simulator/structured_particles.py:
  EV/sEV core-shell surrogate、literature_bounds_2021 ensemble、diameter->radius factory。

nodi_simulator/tsuyama_phase_filter.py / nodi_simulator/reference_field.py:
  Tsuyama thin phase-filter BFP diagnostic 与 reference route 边界。

nodi_simulator/utils.py:
  detector forward diagnostics、readout convention diagnostics、calibration/claim blockers、
  particle-channel perturbation not-modeled diagnostics。

nodi_simulator/parameter_sweep.py:
  single-case engineering score/gate、robust score；后续 EV design aggregation 应从这里或
  nodi_simulator/design_postprocess.py 接出去，不要把所有设计语义塞回单 case score。

dashboard/precompute.py:
  当前 schema/version/manifest 基础；后续补 EV design schema 和 blocker visibility。

tests/test_physics_core.py:
  现有 Mie、Tsuyama、readout、perturbation diagnostics 测试；P0-hard 应从这里补测试。
```

第一批实现顺序按最小闭环推进：

```text
1. unit/axis convention hard tests + Mie amplitude/optical theorem hard tests。
2. minimum required output schema + final_green_eligible / primary_blocker_summary。
3. wavelength_comparability、readout_transfer_model、objective profile、optical exposure safety blocker。
4. EV_NODI_only_design preset + flux_weighted initial position，保留 legacy preset 兼容。
5. particle_channel_perturbation diagnostic-only + double-counting guard。
6. BFP ROI complex mode-overlap comparison lane + tsuyama_bfp_integrated route。
7. EV ensemble / Au20-equivalent / standard ladder / contaminant profile 的 smoke postprocess。
8. recompute manifest/hash/schema inventory + dashboard blocker visibility。
```

实施时坚持这些硬规则：

```text
Hard blocker 不能被 final_EV_design_score 抵消；
score 只在已允许的 recommendation band 内排序。

缺 minimum schema 列是 hard fail；
列存在且值为 unavailable/blocker 是允许的首版状态。

ROI complex mode-overlap lane 缺失时可以跑 exploratory full-grid，
但不能进入 formal EV design current truth，且 final_green_eligible=False。

particle-channel perturbation 首版只能 diagnostic/comparison；
没有 double-count guard/fullwave/实测验证前，不得相干加入主 score。

per-wavelength normalization 只能支持同一 lambda 内 W/H 排序；
跨 lambda / 跨 objective 真实优劣 claim 默认关闭。

analytic_lockin_surrogate 不是 measured_transfer_function；
EV/NODI 主路不得把 locked-carrier surrogate 当作真实 phase-locked event claim。

synthetic/template calibration 只能测试管线；
不得解锁 absolute/calibrated claim 或 green_absolute。
```

完成任一实现切片后，至少给出：

```text
changed files
新增/修改的 schema 字段
新增/修改的 blocker 或 claim rule
运行过的测试/未运行原因
是否仍允许 formal full-grid recompute
是否仍只能 exploratory full-grid
```

## P0 分层

为防止路线图继续膨胀，P0 从 v5 起拆成：

```text
P0-hard：不通过就不能做 formal EV design full recompute，或不能给 green recommendation / 对应 claim。
P0-soft：可以先 skeleton / diagnostic / blocker 字段，不阻塞 full-grid 生成，但阻塞对应 claim。
P1-active：进入 design_postprocess 或 top-candidate refinement，提高排序质量。
P2-measured：必须有实测 blank / standard / BFP / transfer function 后才解锁。
```

P0-hard 只包括：

```text
1. unit / axis convention hard tests
2. Mie amplitude normalization + optical theorem tests
3. wavelength comparability blocker
4. NODI nonsynchronized readout semantic blocker
5. BFP ROI complex mode-overlap comparison lane
6. particle-channel perturbation double-counting guard
7. objective profile schema + claim level
8. optical exposure safety diagnostic
9. synthetic calibration cannot unlock absolute claim
10. recompute manifest / hash / schema inventory
```

P0-hard 内部也分两类：`unit/mie/manifest` 这类失败时阻止 formal full-grid 进入 current truth；`BFP/readout/wavelength/objective/exposure` 这类失败时可以允许 exploratory full-grid 生成，但必须把 `final_green_eligible=False` 和对应 blocker 写入结果。P0-soft 包括 EV reporting、assay controls、selection function skeleton、event QC flags、standard ladder schema、geometry/electrokinetic/integrity diagnostics、fluidic practicality、reference operating point 等。它们需要进入 summary schema 和 dashboard blocker，但首版可用 skeleton/diagnostic 形态。P1-active 再做 population full-trace、objective panel sweep、EV correlated prior、expanded contaminant library、matched filter、OOD、Bayesian scaffold 和 value-of-information advisor。

## 当前代码对照

| 方向 | 当前代码事实 | 结论 |
|---|---|---|
| EV ensemble / sample uncertainty | `nodi_simulator/structured_particles.py` 已有 biomimetic EV preset 和 explicit ensemble builder；`nodi_simulator/utils.py` 已输出 EV claim、shape/corona/isolation uncertainty blocker。 | 需要从 metadata 升级为 design aggregation 与 sample-prep-weighted ensemble。 |
| EV reporting / preanalytical metadata | `nodi_simulator/ev_reporting_metadata.py` 已接入，能输出 EV reporting readiness / sample-prep provenance / biological-claim blocker。 | 当前可区分 EV-like optical particle 与 biological EV claim；无真实 metadata 时仍阻塞 biological specificity。 |
| Au20 anchor | gold family 由 `dashboard/config.py` 生成，但 full-range 当前从 40 nm 开始；Au20-equivalent 不存在。 | 增加 Au20/Au30/Au40 anchor profile 与 uncertainty-aware anchor distribution。 |
| Standard particle ladder | `nodi_simulator/utils.py` 已有 standard-particle calibration table、synthetic guard、uncertainty blockers 和 held-out validation blocker；但没有 PS/silica/liposome ladder 与 fit/validation/challenge split。 | P0 增加 ladder schema；P2 接实测 standard traces。 |
| Particle-induced channel perturbation | `particle_induced_channel_perturbation_model` 已支持 `excluded_volume_phase_surrogate` / `born_phase_object` / `full_phase_mask_recompute`，当前默认仍保持 diagnostic-only。 | 低散射 EV 风险诊断已可输出；没有 double-count guard / fullwave / 实测前不得 active coherent addition。 |
| Particle-channel double counting | `nodi_simulator/particle_channel_perturbation.py` 已输出 double-counting risk 与 guard 字段。 | 默认不把 perturbation 加回主 score；只有 guard 通过或高保真/实测闭环后才可升级。 |
| Detector forward model | `detector_forward_model` 已接受 `collapsed_scalar_surrogate`、`joint_overlap_coherent_surrogate`、`roi_intensity_integral`、`roi_complex_mode_overlap_integral`；`nodi_simulator/bfp_detector_operator.py` 已输出 scalar-vs-ROI disagreement。 | ROI lane 是 comparison/diagnostic contract；无 detector-unit chain 时仍不能给 photon/voltage calibrated claim。 |
| Tsuyama BFP reference | `nodi_simulator/tsuyama_phase_filter.py` 已输出 BFP 复场；`nodi_simulator/reference_field.py` 已提供 `tsuyama_bfp_integrated` detector-resolved comparison lane。 | 可做 BFP-level comparison，不替换 measured blank calibration 或 calibrated truth。 |
| Reference operating point | `nodi_simulator/reference_operating_point.py` 已输出 reference too weak / saturation / RIN/leakage risk 等工作带诊断。 | 防止“reference 越强越好”的错误推荐；无实测 detector/noise budget 时仍是诊断。 |
| NA cutoff | `nodi_simulator/reference_field.py` 当前有 engineering hard guardrail/width saturation。 | 增加 soft rolloff policy，保留 hard guardrail 作保守 lane。 |
| Transport / initial distribution | `uniform_accessible_area` 与 `flux_weighted` 已 runtime-active；`electrostatic_equilibrium` / measured distribution 仍为 schema-reserved。 | EV helper 可用 `flux_weighted`；正式 dashboard precompute 仍按 dashboard 默认配置，除非显式切换 helper。 |
| Fluidics / clogging | `nodi_simulator/fluidic_resistance.py`、`nodi_simulator/fluidic_network_model.py` 与 design metrics 已输出 hydraulic / practicality diagnostic。 | 当前是静态 practicality / resistance 诊断；fouling time evolution 仍属 P2。 |
| Channel real geometry | `nodi_simulator/channel_geometry_model.py` 已输出 geometry model schema、rounded/trapezoid/measured profile readiness 与 discrepancy flag。 | 真实 profile lookup / full geometry solver 仍需 P1/P2 数据或模型。 |
| Electrokinetic / surface charge | `nodi_simulator/electrokinetic_transport.py` 已输出 Debye/wall-potential diagnostic 与 claim blocker。 | transport 仍未用完整 Poisson-Boltzmann/wall-exclusion 主求解，保持 blocker。 |
| EV integrity / deformation | `nodi_simulator/ev_integrity_risk.py` 与 exposure/fluidic diagnostics 已输出 EV integrity risk / gate。 | 可阻止破坏性设计进绿色；非实测 integrity 仍是风险诊断。 |
| Interface correction | `nodi_simulator/interface_correction.py` 已有 boundary、dipole/fullwave blocker。 | P1 实现 dipole image surrogate；P3 再做 dyadic Green/fullwave lookup。 |
| Readout / threshold / event QC | `nodi_simulator/readout_transfer_model.py`、threshold/blank boundary、raw blank bootstrap boundary 与 `nodi_simulator/event_quality_control.py` 已接入；matched filter 仍非主线。 | 当前已能输出 event artifact risk / readout semantics blocker；P2 接实测 blank trace。 |
| Detector units / noise | `nodi_simulator/detector_units.py` 是 boundary；RIN/speckle/leakage/stray options 多为 not_applied。 | P1 做 relative noise components；P2 detector voltage/photon chain 解锁。 |
| POD / NODI thermal contamination | `nodi_simulator/photothermal_pod.py` 仍是 quantitative boundary；`nodi_simulator/nodi_thermal_contamination.py` 已输出 NODI thermal contamination proxy。 | P2/P3 做 thermal POD solver/lookup；当前不解锁热定量 amplitude。 |
| Materials / media / wavelength lanes | `nodi_simulator/materials.py` 已含 Au/Ag、water/PBS/HEPES/culture/sucrose/iodixanol、fused silica/Viosil/BK7 等 nominal properties；`nodi_simulator/wavelength_comparability.py` 已接入。 | 可输出 wavelength-lane claim blocker；无实测跨波长 detector-unit chain 时不能做真实跨波长优劣 claim。 |
| Contaminants / classification | `nodi_simulator/particle_design_library.py` 已包含 contaminant / standard-particle presets 与 design library diagnostics。 | EV_vs_contaminant AUC / unknown rejection 仍是 bounded diagnostic，不是实测分类器。 |
| Selection function / observed distribution | `nodi_simulator/selection_function.py` 已输出 skeleton 和 observed-distribution correction diagnostic。 | 可暴露 selection bias blocker；P3 population inference 仍需数据。 |
| OOD / unknown events | `nodi_simulator/ood_detection.py` 已接入 unknown/reject scaffold。 | 当前是 OOD diagnostic，不是训练好的实测分类器。 |
| Uncertainty / sensitivity | `nodi_simulator/uncertainty.py` 仍是 propagation boundary；`nodi_simulator/design_postprocess.py` 已输出 model consensus / route consensus 等设计层诊断。 | Sobol/Morris 与实测 posterior 仍属 P1/P2。 |
| Count-rate semantics | `nodi_simulator/count_generation.py` 已隔离 per-event detectability；`nodi_simulator/count_likelihood.py` 已提供 observed-count likelihood scaffold。 | count-rate confidence 仍需 concentration/flow/blank/dead-time 实测闭环。 |
| Population full-trace | `nodi_simulator/population_trace_simulator.py` 已提供 population full-trace skeleton/smoke。 | 防止 isolated detectability 被误读为真实 run；P3 才做正式 population inference。 |
| Run state / drift | `nodi_simulator/run_state_model.py` 已输出 stationarity/fouling/reblank interval scaffold。 | 实测 blank/run trace 校准仍属 P2。 |
| Unit / axis conventions | `nodi_simulator/unit_conventions.py` 已输出 unit/axis convention hard gate 与 Mie validation diagnostics。 | 当前用于 schema/gate；继续保持测试锁定。 |
| Objective / optical hardware | `nodi_simulator/optical_hardware_profiles.py` 与 `nodi_simulator/objective_panel.py` 已接入 objective profile / panel diagnostics。 | 可做 objective comparison scaffold；真实硬件 throughput 仍需校准。 |
| Optical exposure safety | `nodi_simulator/optical_exposure_safety.py` 已输出 exposure safety gate / safe-power claim level。 | 无热/photodamage 实测时仍是 conservative diagnostic。 |
| NODI readout semantics | 当前 readout 有 sampled carrier、analytic lockin surrogate、measured transfer function；`nodi_simulator/utils.py` 已标记 NODI source 是 transient scattering surrogate，不是 carrier-modulated source。 | P0 增加 `nodi_simulator/readout_transfer_model.py` 与 nonsynchronized NODI semantics blocker；EV design 默认不得使用 locked-carrier surrogate 解锁 claim。 |
| Polarization / Jones | `nodi_simulator/polarization_jones_operator.py` 已接入 scalar/Jones/measured-matrix scaffold。 | measured Jones matrix 才解锁 phase/polarization quantitative claim。 |
| Calibration planning | `nodi_simulator/bayesian_calibration.py`、`nodi_simulator/calibration_plan_advisor.py`、`nodi_simulator/experimental_design_advisor.py` 已接入 posterior / VOI scaffold。 | P2 接实测 posterior。 |
| Assay controls | `nodi_simulator/assay_control_matrix.py` 与 `nodi_simulator/control_interpretation.py` 已输出 buffer/medium/EV-depleted/lysis/spike-in/dilution control scaffold。 | 推荐输出可带 assay-control blockers；真实控制样本结果仍待接入。 |
| Recompute reproducibility | `nodi_simulator/recompute_manifest.py` 与 dashboard/precompute metadata/checkpoint 已输出 manifest/hash/schema inventory 与 performance context。 | 正式 full-grid 仍需实际重算生成 current library。 |
| Metadata / dashboard | `dashboard_schema_version=1.24`、`model_semantics_version`、schema inventory、blocker 字段、design postprocess / claim text 已有。 | UI blocker page / 宽表长表可继续增强，但当前 schema 已可重算。 |
| Golden tests | 已有 Mie Rayleigh/core-shell/threshold/readout/Tsuyama/BFP ROI/manifest guard/design governance/dashboard workflow 等测试。 | matched filter 和实测 P2/P3 闭环仍等待未来数据/模型。 |

## 第四轮复核新增硬闸门

第四次建议不改变主路线图的方向，但补上 8 个会直接影响 W/H/lambda/objective 推荐的防误判闸门。对照当前代码后，结论是这些都应进入 P0/P1：

```text
1. wavelength_comparability：当前 per_wavelength normalization 不能支撑真实跨 lambda 排名。
2. readout_transfer_model：当前 lock-in surrogate 需要显式区分 NODI transient pulse 与 locked carrier。
3. BFP ROI mode-overlap：当前 joint angular overlap 不是 slit/pinhole ROI 复场积分。
4. particle-channel double-count guard：excluded-volume phase surrogate 不能直接和 Mie scattering 相加。
5. unit/axis hard gate：Particle.radius_m 与文献 diameter naming 必须用测试锁死。
6. population full-trace：isolated event detectability 不能自动等于真实 run trace detectability。
7. objective/hardware profile：20x NA0.45 是当前配置，不应被当成唯一隐含设计。
8. optical exposure safety：detectability 高但 heating/photodamage/thermal artifact 高时不能给绿色推荐。
```

## P0-hard gate 验收表

| Gate | Required inputs | Required outputs | Pass condition | Fail condition | Effect on recommendation / claim |
|---|---|---|---|---|---|
| unit_axis_convention | particle preset、Channel、OpticalSystem axis map | `particle_size_convention`、`unit_axis_convention_status` | Au20/EV100 按 diameter；W=x、H=z、flow=y 可审计 | radius/diameter 或 W/H/z 语义不明 | 不允许 EV design full recompute；不允许 green |
| mie_amplitude_validation | Mie coefficients、S1/S2、dCsca/dOmega tests | `mie_validation_status` | 角积分、optical theorem、Rayleigh phase、core-shell 小粒子极限通过 | S1/S2 归一化或相位约定未验证 | 不允许 BFP/Jones/mode-overlap 相关推荐 claim |
| cross_wavelength_comparability | normalization mode、detector chain、lambda-specific power/responsivity/throughput | `wavelength_ranking_claim_level`、`absolute_or_calibrated_lambda_comparison_allowed` | per-wavelength active 且 detector chain 未解锁时禁用 absolute lambda ranking | 输出 404/488/532/660 总排名但未声明 within-lambda only | 不允许推荐“某 lambda 绝对最优” |
| nodi_readout_semantics | readout route、arrival phase policy、observable mode | `nodi_readout_semantics`、`readout_phase_locked_claim_allowed` | EV 默认 bandpass/envelope 或 random-arrival-phase；magnitude governance 生效 | locked-carrier surrogate 被当主 EV claim | 不允许 phase-locked NODI event claim；不能 green |
| bfp_mode_overlap | BFP fields、ROI mask、metric/Jacobian | `roi_vs_scalar_signal_ratio`、`mode_overlap_efficiency`、`detector_operator_disagreement_band` | ROI complex mode-overlap lane 可运行且 disagreement 可见 | 只用 collapsed scalar 排名 | disagreement large 时最多 yellow；无 lane 时不能 green |
| particle_channel_double_count | perturbation mode、Mie forward/phase proxy | `double_counting_risk_band`、`no_double_count_guard_passed` | perturbation 默认 diagnostic-only；未通过 guard 不相干加入 score | excluded-volume phase 与 Mie scattering 直接相加 | 不能进入 `final_EV_design_score` 主项；不能 green |
| objective_profile | objective profile、NA、waist、working distance | `objective_candidate_id`、`objective_design_claim_level` | profile/schema 存在；working distance/transit risk 可见 | 20x NA0.45 被隐含为唯一硬件 | 不允许跨物镜推荐 claim；不能 green hardware claim |
| optical_exposure_safety | probe/excitation power metadata、waist、absorption/heating proxy | `safe_power_claim_level`、`ev_photodamage_risk_band` | 高 exposure 风险显式降级；缺功率则 blocker | 高功率/短波长/小 waist 仅靠 detectability 排高 | exposure red 时不能 green |
| synthetic_calibration_guard | calibration manifest、data role、synthetic flag | `calibration_synthetic_fixture_active`、`output_claim_level_resolved` | synthetic/template 不能解锁 absolute/calibrated claim | synthetic 行被当实测 | 禁止 absolute claim；不能 green_absolute |
| recompute_manifest | config/material/particle/detector hashes、RNG stream、schema version | `manifest_id`、hashes、schema inventory | 每行可追溯 manifest/hash/RNG；full-grid 与 refinement 分开 | 无 manifest 或 hash 不匹配 | 不允许正式 full-grid 进入 current truth |

分数只负责在允许的 recommendation band 内排序。Hard gate 负责决定最高允许 band。

## 设计原则

1. **主链从“单 case score”升级为“实验设计平台”。**
2. **active solver 与 calibration-ready interface 分开。** 没有实测数据时，只能输出 relative/proxy/diagnostic claim。
3. **先做低成本可审计 surrogate，再做高保真 solver。** 例如先做 particle phase perturbation、BFP ROI surrogate、dipole image；fullwave 留到 P3。
4. **全量库和候选精修库分开。** full-grid 不能盲目乘 seed × alignment × model ensemble，否则算力爆炸；推荐先 full-grid 再 top-candidate refinement。
5. **EV 主推荐不依赖未标定 polarity 或 POD thermal amplitude。**
6. **所有推荐必须能生成“可说/不可说”文本。**
7. **模型分歧会降级推荐。** 任何只在一个 surrogate 下高分的设计不能进绿色。
8. **EV biological claim 默认关闭。** 缺少 preanalytical metadata、orthogonal sizing、marker/negative marker 和控制样品时，只能说 EV-like optical particle。
9. **observed events 不是 true population。** 所有分布、浓度、分类输出必须显式记录 selection function 与 QC 过滤。
10. **推荐对象是 chip + assay + calibration + reporting panel。** 不是单一 W/H/lambda top-1。
11. **跨波长/跨物镜比较默认降级。** per-wavelength normalization 只能支持同一 lambda 内 W/H 排序；缺 detector chain、laser power、objective throughput、reference/noise 统一口径时，不允许输出真实 lambda/objective 优劣 claim。
12. **NODI pulse 不是相位锁定载波。** EV 主读出必须按 transient/bandpass/envelope 或 random-arrival-phase 语义处理；locked-carrier surrogate 只能用于 debug 或降级 claim。
13. **BFP detector 要比较复场 mode-overlap。** ROI 强度积分、ROI complex overlap 和 collapsed scalar 三者不一致时，必须输出 disagreement 并降级推荐。
14. **particle-channel perturbation 先做诊断，不默认相干相加。** 在没有 double-counting guard/fullwave/实测验证前，不把 excluded-volume phase perturbation 直接加入主 score。
15. **单位和坐标约定必须硬测试。** Au20/EV100 等名字默认 diameter，不是 radius；W=x、H=z、flow=y、optical axis 的约定必须在 summary 中可审计。
16. **光学安全独立于 detectability。** laser power density、heating、photodamage、bubble/thermal lens artifact 高风险时，即使 detectability 高也不得给绿色推荐。

## 总体架构

```text
Simulation rows
  -> EV reporting metadata / sample-prep profile / assay-control matrix
  -> intrinsic scattering / particle-channel perturbation
  -> reference route / Tsuyama BFP / BFP ROI detector operator
  -> wavelength/objective comparability blocker / readout transfer semantics
  -> channel geometry / electrokinetic / EV integrity / fluidic model
  -> trajectory / flux-weighted event distribution / selection function inputs
  -> interference / readout / threshold / blank false-positive model / event QC / optical exposure safety
  -> per-event detectability, QC pass rate, and batch stability
  -> population full-trace smoke / isolated-vs-full-trace bias
  -> row metrics: Au20-equivalent / reference operating point / fluidic risk
  -> design_postprocess: EV ensemble / standard ladder / contaminants / selection / consensus / Pareto
  -> candidate refinement: seed, alignment/fabrication, sensitivity, model ensemble
  -> chip + assay-control panel selector
  -> dashboard advisor + claim blocker + reporting readiness + calibration/VOI advisor
```

## P0：全量重算前必须具备的 hard gates 与 smoke-critical 改动

这些项目不依赖真实实验数据，并且会影响 full-grid 数据是否能直接服务 EV 设计决策。这里的“必须具备”优先指 **schema、blocker、claim gate、测试和 smoke path**；只有已经足够低风险、低成本且明确影响主结果语义的部分才进入 active solver。探索性 full-grid 可以在部分 comparison lane 未完成时生成，但不能被标记为 formal EV design truth，也不能产生 green recommendation。

### P0.1 配置、目标与 preset

在 `nodi_simulator/data_objects.py` 增加：

```python
@dataclass(frozen=True)
class DesignObjectiveConfig:
    target_family: str = "EV_sEV"
    anchor_particle_name: str = "gold_20nm"
    ev_size_quantiles_nm: tuple[float, ...] = (50.0, 70.0, 100.0, 150.0)
    ev_ensemble_group: str = "literature_bounds_2021"
    w_ev_worst_case: float = 0.35
    w_ev_d50: float = 0.15
    w_au20_anchor: float = 0.15
    w_reference: float = 0.10
    w_specificity_or_overlap: float = 0.10
    w_practicality_penalty: float = 0.10
    w_route_or_model_disagreement_penalty: float = 0.10
    au20_equivalent_green: float = 1.0
    au20_equivalent_yellow: float = 0.5
```

这些默认值与后面的 `final_EV_design_score` 首版公式保持一致；实现时可以集中放在 `DesignObjectiveConfig`，避免公式常量散落在后处理代码里。

新增 `EV_NODI_only_design` readout preset：

```python
READOUT_PRESET_CONFIG_OVERRIDES["EV_NODI_only_design"] = {
    "readout_observable_mode": "magnitude",
    "readout_internal_demod_route": "analytic_lockin_surrogate",
    "readout_anti_alias_policy": "analytic_demod_no_carrier_sampling",
    "nodi_readout_semantics": "bandpass_envelope_surrogate",
    "electronics_demod_phase_policy": "magnitude_only",
    "lockin_time_constant_s": 1.0e-3,
    "nodi_lockin_frequency_Hz": 2000.0,
    "threshold_sigma": 5.0,
    "threshold_tail": "one_sided",
    "min_peak_width_s": 2.5e-3,
    "min_peak_interval_s": 0.1,
    "detection_decision_mode": "single_channel",
    "pulse_detection_mode": "positive",
    "engineering_decision_basis": "single_channel",
    "engineering_max_phase_flip_fraction": 1.0,
}
```

同时必须更新 `READOUT_PRESET_OPTIONS`、`READOUT_PRESET_PROVENANCE` 和 `SimulationConfig` validation 覆盖路径；否则新 preset 会在配置校验阶段被拒绝。

实现顺序注意：`READOUT_PRESET_CONFIG_OVERRIDES` 会被 `_readout_preset_mismatch_fields()` 逐项 `getattr(sim_cfg, field_name)` 检查。因此 `nodi_readout_semantics` 必须先作为 `SimulationConfig` 字段、options 和 validation 加入，再放进 preset override；否则新 preset 会在 readout diagnostics 阶段触发缺字段错误。

新增 EV design sweep preset：

```python
include_diffusion=True
flow_profile_model="rect_series"
diffusion_hindrance_model="near_wall_surrogate"
initial_position_distribution_mode="flux_weighted"
reference_model="channel_angular_surrogate"
readout_preset="EV_NODI_only_design"
EV_ensemble_mode="explicit_preset_cases"
```

### P0.2 粒子对通道 reference 的局部扰动

新增 `nodi_simulator/particle_channel_perturbation.py`。

扩展配置：

```python
PARTICLE_INDUCED_CHANNEL_PERTURBATION_MODEL_OPTIONS = (
    "not_applied",
    "excluded_volume_phase_surrogate",
    "born_phase_object",
    "full_phase_mask_recompute",
)

PARTICLE_CHANNEL_PERTURBATION_APPLICATION_MODE_OPTIONS = (
    "diagnostic_only",
    "alternative_forward_phase_lane",
    "coherent_addition_with_no_double_count_guard",
)
```

首版实现 `excluded_volume_phase_surrogate`：

```text
delta_phi_particle = (2*pi/lambda) * (n_particle_eff - n_medium) * path_length_eff
delta_E_ref_particle = shared_detector_operator(local_phase_object * incident_field)
```

输出：

```text
particle_induced_channel_perturbation_model
particle_channel_perturbation_application_mode
delta_E_ref_particle_peak_abs
delta_E_ref_particle_to_E_sca_ratio
delta_E_ref_particle_to_E_ref_ratio
particle_phase_perturbation_to_mie_forward_ratio
double_counting_risk_band
no_double_count_guard_passed
particle_channel_perturbation_claim_level
nodi_particle_induced_channel_coupling_status
```

设计 gate：

```text
delta_E_ref_particle_to_E_sca_ratio > 0.3
  -> independent E_ref + E_sca superposition 降级，进入 yellow/red blocker

application_mode = coherent_addition_with_no_double_count_guard
  and no_double_count_guard_passed = False
  -> 不允许进入 final_engineering_score / final_EV_design_score
```

P0 默认：`diagnostic_only`。这条 lane 只影响 risk flag、model disagreement 和 candidate refinement priority；P1/P2 再用 fullwave、dyadic Green 或 EV-like standard 判断是否纳入 active signal。这样避免把 Mie forward scattering 与 excluded-volume phase-object perturbation 双计数。

### P0.3 BFP ROI detector operator

新增 `nodi_simulator/bfp_detector_operator.py`。

新增配置：

```python
detector_forward_model = (
    "collapsed_scalar_surrogate"
    | "joint_overlap_coherent_surrogate"
    | "roi_intensity_integral"
    | "roi_complex_mode_overlap_integral"
)
bfp_grid_mode = "direction_cosine_uv"
bfp_roi_mask_source = "surrogate_slit_pinhole"
bfp_to_angle_jacobian_applied = True
```

当前 `DETECTOR_FORWARD_MODEL_OPTIONS` 与 `SimulationConfig` validation 已接受这四个值；ROI 两条 lane 仍是 comparison / diagnostic contract，不是 detector-unit calibrated truth。

核心函数：

```python
def compute_detector_integrated_interference(
    E_ref_bfp: np.ndarray,
    E_sca_bfp: np.ndarray,
    roi_mask: np.ndarray,
    bfp_metric: dict,
) -> dict:
    ...
```

输出：

```text
signal_detector_integrated
cross_term_detector_integrated
self_sca_detector_integrated
I_ref_detector_integrated
interference_overlap_efficiency
roi_vs_scalar_signal_ratio
roi_vs_scalar_phase_disagreement_rad
mode_overlap_efficiency
detector_operator_disagreement_band
bfp_roi_mask_status = surrogate_not_calibrated
detector_forward_claim_level = relative_ranking_only
```

注意：这条 lane 是 detector-resolved comparison，不直接解锁 detector voltage 或 photon-unit claim。核心硬要求是：

```text
S_ROI = integral_ROI(|E_ref + E_sca|^2 - |E_ref|^2) dA
      = integral_ROI(|E_sca|^2)dA + 2 Re integral_ROI(E_ref * conj(E_sca))dA
```

不能把 `integral(|E_ref|^2)` 和 `integral(|E_sca|^2)` 当成 detector signal 的全部，也不能默认 `2 Re(collapse(E_ref) collapse(E_sca)*)` 等价于 ROI mode overlap。`detector_operator_disagreement_band="large"` 时，设计推荐最多为 yellow，不能进绿色。

P0-hard 语义：

```text
有 ROI complex mode-overlap lane -> 可以给 relative green/yellow/red recommendation claim。
没有 ROI complex mode-overlap lane -> 只能做 exploratory ranking，不能给 green recommendation。
有 ROI complex mode-overlap lane 也不等于 detector voltage / photon-unit calibrated claim。
```

### P0.4 Tsuyama BFP integrated reference lane

新增：

```python
reference_model = "tsuyama_bfp_integrated"
```

不要复用 `paper_aligned_phase_filter` 的旧语义。新增函数：

```python
def compute_reference_field_from_tsuyama_bfp(
    channel,
    optical,
    sim_cfg,
    medium_refractive_index,
    wall_refractive_index,
    roi_mask=None,
) -> dict:
    ...
```

输出同时保留：

```text
E_ref_complex_roi = integral(E_diff ROI)
I_ref_intensity_roi = integral(|E_diff|^2 ROI)
reference_detector_bridge_status = surrogate_roi
reference_claim_level = paper_aligned_detector_resolved_comparison
```

这条 route 用于 route consensus 和 reference design score，不是 calibrated blank truth。

同时需要扩展 `reference_model` validation、`REFERENCE_ROUTE_MODEL_COMPATIBILITY`、`REFERENCE_SOLVER_ROUTE_OPTIONS` 和 `resolve_reference_solver_route_name()`，否则新 route 会被配置层拒绝。

### P0.5 Reference design + operating point

在 `nodi_simulator/reference_field.py` 或 `detector_noise_budget.py` 中增加：

```python
compute_reference_design_metrics(...)
compute_reference_operating_point_metrics(...)
```

输出：

```text
reference_design_intensity_proxy
reference_design_amplitude_proxy
reference_design_roi_fraction
reference_design_width_rank_metric
reference_design_validity
I_ref_proxy
reference_shot_noise_proxy
reference_total_noise_proxy
reference_saturation_margin_proxy
reference_operating_band
```

风险带：

```text
reference_too_weak
electronics_noise_limited_useful
balanced
shot_noise_limited_no_gain
rin_or_leakage_risk
reference_saturation_risk
```

代码注释和测试应锁定首版物理语义：

```text
weak scattering: signal ~= 2 |E_ref| |E_sca| cos(phi)
electronics-noise dominated: SNR improves with |E_ref|
shot-noise dominated: noise_shot ~= sqrt(I_ref) ~= |E_ref|, so SNR no longer improves indefinitely
```

因此 `reference_design_score` 不能无限奖励强 reference；进入 `shot_noise_limited_no_gain`、`rin_or_leakage_risk` 或 `reference_saturation_risk` 时应降级。

新增 NA soft rolloff：

```python
reference_na_edge_policy = "soft_rolloff"  # or "hard_guardrail"
reference_na_rolloff_width_deg = 2.0
```

输出：

```text
reference_na_edge_rolloff_factor
reference_na_edge_status = inside / near_edge / outside
```

### P0.6 Flux-weighted initial distribution

扩展：

```python
initial_position_distribution_mode = (
    "uniform",
    "center_biased_surrogate",
    "uniform_accessible_area",
    "flux_weighted",
    "electrostatic_equilibrium",
    "measured_cross_section_distribution",
)
```

首版新增实现 `uniform_accessible_area` 和 `flux_weighted`；`uniform` 与 `center_biased_surrogate` 必须保持向后兼容。采样规则：

```text
p(x,z | crossing event) proportional to v_y(x,z)
```

输出：

```text
initial_position_distribution_mode
flux_weighted_sampling_acceptance_rate
cross_section_event_bias_status
```

`make_ev_nodi_design_sweep_config(...)` 这条 EV/NODI design helper 默认使用 `flux_weighted`。当前 dashboard formal precompute 命令仍按 `dashboard/config.py::DEFAULT_SIM_CFG` 构造，并只在 `build_precompute_sim_cfg(...)` 中把 `score_mode` 改为 `single`；因此正式全量重算若未显式切换 helper，初始位置分布仍以 dashboard 默认配置为准。

### P0.7 Fluidic practicality + hydraulic resistance v1

新增 `nodi_simulator/fluidic_resistance.py`。

实现：

```python
compute_rectangular_channel_hydraulic_resistance(...)
compute_fluidic_practicality_penalty(...)
```

输出：

```text
hydraulic_resistance_Pa_s_m3
pressure_required_for_target_velocity_Pa
predicted_flow_rate_m3_s
sample_consumption_pL_min
residence_time_s
fluidic_practicality_penalty
fluidic_clogging_risk_band
wall_interaction_risk_band
accessible_cross_section_fraction
nearest_wall_gap_D50_nm
nearest_wall_gap_D90_nm
```

首版 flow mode：

```python
flow_control_mode = "fixed_velocity" | "fixed_pressure"
```

这需要新增 `SimulationConfig.flow_control_mode` 及 validation；首版可以只让 `fixed_pressure` 输出 diagnostic，不改变默认 trajectory。

full-grid 主库可保留 fixed_velocity，同时输出 fixed_pressure diagnostic，用于公平比较不同 W/H。

### P0.8 EV / anchor / contaminant particle library

新增或扩展：

```text
EV_SHAPE_MODEL_OPTIONS
StandardParticleSpec
STANDARD_PARTICLE_PRESETS
PARTICLE_CONTAMINANT_PRESETS
EV_SAMPLE_PREPARATION_PROFILES
```

P0 active 范围：

- EV ensemble：已有 preset group 要进入 precompute profile。
- EV shape：先做 `spheroid_orientation_average` 的 Rayleigh depolarization factor surrogate。
- Au anchor：增加 `gold_20nm / gold_30nm / gold_40nm`，输出 size CV、ligand shell、material correction status。
- Standard ladder：增加 `polystyrene_50nm / polystyrene_100nm / silica_50nm / silica_100nm / liposome_100nm_low_RI / hollow_organosilica_EV_mimic`。
- Contaminants：至少加入 LDL-like、protein aggregate、silica dust、polystyrene contaminant 的 surrogate library。
- Sample prep：SEC/IEX/UF/UC/PEG/unknown 先作为 ensemble weight metadata，不强行改写单粒子物理。
- Calibration split：标准颗粒必须标记 `fit / validation / challenge`，fit 标准不能同时用于 held-out performance claim。

输出：

```text
shape_model
aspect_ratio
orientation_average_status
shape_scattering_factor
anchor_particle_uncertainty_status
au20_anchor_signal_p10/p50/p90
standard_particle_family
standard_particle_RI_class
standard_particle_traceability_status
standard_particle_calibration_role
calibration_train_or_validation_split
calibration_transfer_to_EV_risk
contaminant_family
EV_to_contaminant_signal_overlap
EV_specificity_risk
EV_sample_preparation_profile
EV_model_weight
```

### P0.9 Row-level design metrics

新增 `nodi_simulator/design_metrics.py` 或放入 `nodi_simulator/design_postprocess.py` 的 row metric 层：

```python
attach_anchor_equivalent_metrics(...)
attach_reference_operating_metrics(...)
attach_fluidic_practicality_metrics(...)
```

Anchor matching keys 必须包含：

```text
width_m / depth_m / wavelength_m / reference_model / reference_solver_route / readout_preset / detector_forward_model
```

输出：

```text
Au20_anchor_available
Au20_anchor_geometry_matched
Au20_equivalent_peak_ratio
Au20_equivalent_margin_ratio
Au20_equivalent_stable_rate_ratio
Au20_equivalent_detectability_band
```

### P0.10 Geometry-level EV aggregation

新增 `nodi_simulator/design_postprocess.py`：

```python
compute_ev_ensemble_design_score(...)
compute_reference_route_consensus(...)
compute_physics_model_consensus(...)
compute_pareto_front(...)
generate_claim_text(...)
```

分组键：

```text
width_m / depth_m / wavelength_m / reference_model / reference_solver_route
readout_preset / detector_forward_model
```

每个几何点输出：

```text
ev_member_count
ev_score_min / ev_score_p10 / ev_score_median
ev_gate_pass_fraction
ev_min_margin_z
ev_max_phase_flip_fraction
au20_equivalent_peak_ratio
reference_design_score
reference_operating_band
fluidic_practicality_penalty
EV_contaminant_overlap_fraction
route_disagreement_flag
physics_model_disagreement_flag
final_EV_design_score
EV_design_recommendation_band
EV_design_claim_text
```

P0 若没有完整 classification objective，可先输出 `EV_contaminant_overlap_fraction` / `specificity_risk`；`EV_vs_contaminant_AUC` 在 P1 `classification_objectives.py` 中作为正式分类指标。

首版公式：

```text
final_EV_design_score =
    0.35 * ev_score_min
  + 0.15 * ev_score_median
  + 0.15 * au20_anchor_score
  + 0.10 * reference_design_score
  + 0.10 * specificity_or_overlap_proxy
  - 0.10 * fluidic_practicality_penalty
  - 0.10 * route_or_model_disagreement_penalty
```

其中 `specificity_or_overlap_proxy` 在 P0 只来自 contaminant overlap / risk band；正式的 `EV_vs_contaminant_AUC` 等分类指标放到 P1。

Hard blocker 不能被连续 score 抵消。实现时必须先算最高允许 recommendation band，再在该 band 内用 `final_EV_design_score` 排序：

```python
final_eligible_for_green = (
    unit_gate_passed
    and mie_gate_passed
    and wavelength_claim_gate_passed
    and readout_semantic_gate_passed
    and detector_operator_gate_passed
    and double_counting_gate_passed
    and objective_profile_gate_passed
    and exposure_safety_not_red
    and synthetic_calibration_not_unlocking_absolute
    and recompute_manifest_gate_passed
)

if not final_eligible_for_green:
    final_recommendation_band = max_allowed_band(primary_blockers)
else:
    final_recommendation_band = score_to_band(final_EV_design_score)
```

也就是说，分数决定 yellow 内谁更优；hard gate 决定能不能 green。

### P0.11 Seed robustness and candidate refinement interface

新增：

```python
run_seed_replicates(case, seeds=(1, 2, 3, 4, 5))
```

输出：

```text
seed_score_mean
seed_score_std
seed_score_p10
seed_rank_stability
seed_gate_pass_fraction
```

不要在 full-grid 默认跑所有 seed；在 design_postprocess 选出的 candidate panel 上跑。

### P0.12 Metadata hash、导出格式和 claim text

增强 metadata：

```text
model_semantic_version
simulation_config_hash
particle_library_hash
material_database_hash
reference_model_hash
detector_operator_hash
code_state_hash_or_git_commit_hash
```

当前目录可能不是 Git worktree；实现时应支持：

```text
git_commit_hash if available
source_tree_fingerprint otherwise
```

导出层拆分：

```text
summary.csv
compact.pkl
meta.json
result_health.json
runtime_performance.json
freeze_probe.json
design_postprocess.csv
```

正式全量重算当前使用 `--artifact-profile standard`，因此上面是标准结果库合同。若需要历史兼容拆分产物，可显式使用 `--artifact-profile full` 额外导出：

```text
case_summary.csv
case_summary.parquet
physics_fields.parquet
diagnostics_long.parquet
```

新增 claim text generator：

```text
可说：该几何在当前 relative EV design model 下优先级较高。
不可说：该几何真实 detector voltage / absolute SNR 最高。
```

### P0.13 Materials、medium 属性与 wavelength lane governance

新增 `nodi_simulator/wavelength_comparability.py`，把“跨波长/跨物镜能不能比较”从 dashboard 文案升级为硬 blocker。现有 `normalization_mode="per_wavelength"` 适合在同一 lambda 下比较 W/H，但不能证明 404/488/532/660 nm 的真实 detector voltage、真实 SNR 或真实 LOD 谁更优。

扩展 `nodi_simulator/materials.py` 与 `Medium` / `SimulationConfig`：

```text
MATERIAL_DB["hepes_buffer"]
MATERIAL_DB["culture_medium_surrogate"]
MATERIAL_DB["sucrose_solution_xpct"]
MATERIAL_DB["iodixanol_solution_xpct"]
MATERIAL_DB["fused_silica_viosil"]
medium_optical_material_key
medium_transport_material_key
medium_thermal_material_key
wavelength_lane_id
probe_power_by_wavelength_W
detector_responsivity_by_wavelength
filter_transmission_by_wavelength
reference_calibration_by_wavelength
```

每个 medium 至少暴露：

```text
n_real(lambda)
n_imag(lambda)
dn_dT
viscosity_Pa_s
density
thermal_conductivity
thermal_diffusivity
osmolarity_or_solute_fraction
source
claim_level
```

输出：

```text
cross_wavelength_comparison_status
wavelength_lane_calibration_complete
wavelength_ratio_claim_level
medium_property_claim_level
per_wavelength_normalization_active
absolute_or_calibrated_lambda_comparison_allowed
laser_choice_claim_blocker
lambda_score_comparability_band
detector_responsivity_lambda_status
objective_transmission_lambda_status
laser_power_density_lambda_status
reference_lambda_scaling_status
```

没有 wavelength-specific power/responsivity/filter/reference calibration 时，跨波长只能称为 normalized simulator trend，不能称真实电压或真实 SNR 更高。

硬规则：

```text
if per_wavelength_normalization_active and not detector_unit_chain_unlocked:
    absolute_or_calibrated_lambda_comparison_allowed = False
    wavelength_ranking_claim_level = "within_lambda_geometry_ranking_only"
```

dashboard 可以说“在 660 nm 下 W/H=A 比 W/H=B 更优”，但不能说“660 nm 真实优于 532 nm”，除非 detector responsivity、laser power、objective throughput、reference scaling 和 noise model 的跨波长口径统一。

### P0.14 EV reporting metadata and assay-control skeleton

新增 `nodi_simulator/ev_reporting_metadata.py`。

核心 dataclass：

```python
@dataclass(frozen=True)
class EVPreanalyticalMetadata:
    sample_source: str | None = None
    donor_or_cell_line: str | None = None
    culture_medium: str | None = None
    serum_depletion_method: str | None = None
    collection_time_h: float | None = None
    storage_temperature_C: float | None = None
    freeze_thaw_cycles: int | None = None
    isolation_method: str | None = None
    concentration_method: str | None = None
    buffer_exchange_method: str | None = None
    final_buffer: str | None = None
    filtration_um: float | None = None
    protein_assay_available: bool = False
    lipid_assay_available: bool = False
    RNA_assay_available: bool = False
    marker_panel_available: bool = False
    negative_marker_available: bool = False
    orthogonal_size_method: str | None = None
```

输出：

```text
ev_reporting_readiness_score
misev_metadata_completeness
evtrack_reporting_completeness
ev_characterization_completeness
ev_sample_identity_claim_level
ev_biological_specificity_claim_allowed
ev_biological_specificity_blocker_summary
```

规则：

```text
缺 sample source / isolation method / final buffer / orthogonal size method
  -> 不允许 biological EV specificity claim
缺 marker panel 或 negative marker
  -> 只能说 EV-like optical particle 或 EV-enriched sample under metadata limits
```

新增 `nodi_simulator/assay_control_matrix.py` skeleton。首版只输出控制样品清单和 claim blocker，不需要实测 trace：

```text
buffer_blank
medium_blank
EV_depleted_sample
detergent_lysed_EV_sample
proteinase_treated_sample
spike_in_Au20
spike_in_PS_or_silica
spike_in_liposome
dilution_linearity_control
high_concentration_coincidence_control
```

输出：

```text
required_control_samples
control_expected_signal_pattern
control_failure_interpretation
control_priority
assay_control_readiness_score
```

### P0.15 Selection function skeleton

新增 `nodi_simulator/selection_function.py`。P0 只建立 schema 和基础计算，不做完整 population inversion。

```python
def compute_detection_selection_function(
    design_table,
    particle_population_table,
    qc_model=None,
    count_model=None,
) -> dict:
    ...
```

基础定义：

```text
p_observed_i proportional to p_true_i * P_detect_i * P_pass_QC_i * P_not_adsorbed_i * P_not_coincident_i
```

P1 完整 selection function 应扩展为：

```text
p_observed_i proportional to
    p_true_i
  * P_pass_sample_prep_i
  * P_channel_entry_i
  * P_transport_i
  * P_detect_i
  * P_pass_event_QC_i
  * P_classifier_accept_i
```

输出：

```text
P_detect_by_population_bin
P_pass_QC_by_population_bin
sample_prep_selection_bias
channel_entry_selection_bias
optical_detection_selection_bias
event_qc_selection_bias
classifier_rejection_selection_bias
observed_distribution_predicted
true_to_observed_bias_factor
true_to_observed_total_bias
small_EV_under_detection_bias
low_RI_EV_under_detection_bias
contaminant_enrichment_in_observed_events
selection_bias_claim_level
```

P0 dashboard 至少要能显示：

```text
true distribution assumed
observed distribution predicted by current surrogate
selection bias blockers
```

### P0.16 Event-level QC and signed/magnitude governance

新增 `nodi_simulator/event_quality_control.py`。

事件级 flags：

```text
event_qc_pass
event_qc_failure_reason
event_baseline_nonstationary
event_pulse_width_out_of_range
event_saturation_risk
event_doublet_or_overlap_risk
event_edge_clipped
event_negative_positive_mismatch
event_pod_nodi_pairing_mismatch
event_shape_template_mismatch
event_local_noise_burst
```

函数：

```python
def compute_event_quality_flags(
    signal_detect: np.ndarray,
    time_s: np.ndarray,
    pulse_features: dict,
    readout: dict,
    sim_cfg: SimulationConfig,
) -> dict:
    ...
```

批量输出：

```text
event_qc_pass_fraction
event_qc_primary_failure_reason
event_artifact_risk_score
detected_rate_after_event_qc
```

同时新增 readout sign governance：

```text
signed_signal_available
polarity_claim_allowed
magnitude_readout_information_loss
phase_sensitive_classification_allowed
```

规则：

```text
readout_observable_mode="magnitude"
  -> polarity_claim_allowed=False
  -> phase_sensitive_classification_allowed=False
```

### P0.17 Geometry, electrokinetic, and EV integrity diagnostics

新增 `nodi_simulator/channel_geometry_model.py` skeleton：

```text
CHANNEL_CROSS_SECTION_MODEL_OPTIONS =
  ideal_rectangle / rounded_rectangle / trapezoid_tapered_sidewalls / measured_profile_lookup
sidewall_taper_angle_deg
corner_radius_nm
surface_roughness_rms_nm
width_along_channel_cv
depth_along_channel_cv
measured_profile_path
```

P0 输出：

```text
effective_accessible_area_m2
effective_phase_mask_area_m2
geometry_model_discrepancy_flag
roughness_scattering_background_proxy
geometry_claim_level
```

新增 `nodi_simulator/electrokinetic_transport.py` skeleton：

```text
ELECTROKINETIC_MODEL_OPTIONS =
  not_applied / debye_layer_diagnostic / boltzmann_wall_exclusion / pressure_plus_eof_surrogate
```

P0 只做 Debye diagnostic：

```text
debye_length_nm
debye_to_channel_depth_ratio
zeta_particle_mV
zeta_wall_mV
electrostatic_wall_exclusion_length_nm
electroosmotic_flow_fraction
surface_charge_transport_claim_level
```

gate：

```text
debye_length_nm / min(W, H) > 0.1
  -> electrostatic_confinement_flag="non_negligible"
```

新增 `nodi_simulator/ev_integrity_risk.py` skeleton：

```text
ev_clearance_margin_nm
ev_confinement_ratio
ev_shear_rate_proxy
ev_osmotic_stress_flag
ev_wall_contact_probability
ev_deformation_or_rupture_risk
ev_integrity_claim_level
```

首版规则：

```text
clearance_nm < 2 * roughness_rms_nm + 20
  -> high_contact_or_deformation_risk
diameter_nm / min(W_nm, H_nm) > 0.5
  -> moderate_confinement_risk
```

### P0.18 Recompute manifest and performance budget

新增 `nodi_simulator/recompute_manifest.py` 或扩展 dashboard/precompute manifest。

输出：

```text
sweep_manifest_id
case_count
estimated_memory_GB
estimated_runtime_proxy
worker_count
chunk_size
checkpoint_interval
failed_case_count
resume_from_checkpoint_supported
random_seed_policy
rng_stream_id
```

要求：

```text
full-grid result row 必须能追溯到 manifest_id / config hash / particle hash / RNG stream。
candidate refinement 的 seed/alignment/model-consensus 不能混入主 full-grid manifest。
```

### P0.19 NODI nonsynchronized readout semantics

新增 `nodi_simulator/readout_transfer_model.py`，把 NODI transient pulse 与 POD locked modulation 分清楚。Tsuyama-style simultaneous POD/NODI 读出可以用 lock-in 电子学描述，但 EV/NODI pulse 本身不是稳定相位锁定载波；它更接近 transient pulse 经过 bandpass/lock-in transfer function 后的 envelope/IQ 响应。

新增配置：

```python
NODI_READOUT_SEMANTICS = (
    "locked_carrier_surrogate",
    "bandpass_envelope_surrogate",
    "random_arrival_phase_lockin",
    "measured_transfer_function",
)
```

EV design 默认：

```text
nodi_readout_semantics = "bandpass_envelope_surrogate"
electronics_demod_phase_policy = "magnitude_only"
```

输出：

```text
nodi_readout_semantics
nodi_event_arrival_phase_policy
nodi_bandpass_center_Hz
nodi_bandpass_gain
nodi_bandpass_phase
nodi_random_arrival_phase_average_gain
nodi_lockin_phase_bias_risk
readout_phase_locked_claim_allowed
readout_sampling_output_claim_blocker_active
```

硬规则：

```text
nodi_readout_semantics = "locked_carrier_surrogate"
  -> EV/NODI 主推荐 claim 降级
  -> 不允许输出 phase-locked NODI event claim
```

现有 `sampled_carrier_demod_on_event_grid` 可保留为 debug/legacy lane；EV full-grid 主路必须用 envelope/random-phase/measured-transfer 语义之一。

硬规则：

```text
analytic_lockin_surrogate != measured_transfer_function
```

`analytic_lockin_surrogate` 只能说明 readout 语义和 anti-alias 口径合理，不能说明实际电子学 transfer function 已被校准。P0 默认允许 `bandpass_envelope_surrogate`、`random_arrival_phase` smoke 和 `magnitude_only` governance；P2 接入 measured gain/phase/noise transfer table 后，才允许 `measured_transfer_function` 解锁电子学可比 claim。

### P0.20 Unit conventions and axis hard gate

新增 `nodi_simulator/unit_conventions.py` 和 `tests/test_unit_conventions.py`，把 radius/diameter、W/H、坐标轴和 flow/optical axis 约定做成 hard gate。

新增输出字段：

```text
particle_size_input_convention
particle_radius_m
particle_diameter_m
size_convention_validated
channel_width_axis = "x"
channel_depth_axis = "z"
flow_axis_convention = "y"
optical_axis_convention
axis_convention_status
```

必须测试：

```python
def test_gold_20nm_preset_means_diameter_not_radius():
    assert particle.radius_m == pytest.approx(10e-9)

def test_ev_100nm_preset_means_diameter_not_radius():
    assert particle.radius_m == pytest.approx(50e-9)

def test_channel_width_depth_convention():
    assert axis_map["width_m"] == "x"
    assert axis_map["depth_m"] == "z"
    assert axis_map["flow_axis"] == "y"

def test_height_depth_not_swapped_in_hydraulic_resistance():
    ...
```

这属于 P0 hard gate，因为 diameter/radius 错一次会把 EV/Au detectability 推高或压低数个数量级。

### P0.21 Optical hardware profiles and objective schema

新增 `nodi_simulator/optical_hardware_profiles.py` 和 `nodi_simulator/objective_panel.py`。现有 `OpticalSystem` 参数继续保留，但全量设计输出必须知道这些参数来自哪个 objective/hardware profile，而不是隐含固定为 20x NA0.45。

核心 dataclass：

```python
@dataclass(frozen=True)
class ObjectiveProfile:
    objective_id: str
    magnification: float
    illumination_NA: float
    collection_NA: float | None
    immersion: str
    working_distance_mm: float | None
    coverglass_correction: str | None
    wavelength_transmission_band: tuple[float, float] | None
    nominal_waist_model: str
    bfp_mapping_status: str
```

P0 只建 schema 和 claim blocker；P1 再做 active objective panel sweep。推荐 panel：

```text
current_control: 20x / NA0.45 illumination + NA0.9 collection
moderate_upgrade: 40x / NA0.6-0.75 illumination
high_NA_test: 60x / NA1.0-1.2, only if chip geometry allows
large_spot_control: lower NA, larger waist, lower position sensitivity
```

输出：

```text
objective_candidate_id
illumination_waist_m
depth_of_focus_m
transit_time_s
lockin_bandwidth_margin
position_sensitivity_score
working_distance_compatibility
objective_design_claim_level
```

规则：

```text
transit_time_s < 3 * lockin_time_constant_s
  -> lockin_bandwidth_margin = "risk"
working_distance incompatible with chip
  -> objective_candidate_status = "not_practical"
```

### P0.22 Optical exposure and EV photodamage safety

新增 `nodi_simulator/optical_exposure_safety.py`。这条 gate 独立于 POD thermal solver 和 NODI thermal contamination：即使 EV 主路是 NODI-only，短波长、高功率、小 waist 也可能带来 heating、EV membrane damage、thermal lens、bubble 或 Au standard thermal artifact。

输出：

```text
laser_power_density_W_m2
particle_absorbed_power_proxy
medium_absorption_heating_proxy
wall_heating_proxy
estimated_temperature_rise_K_surrogate
ev_photodamage_risk_band
bubble_or_thermal_lens_artifact_risk
au_standard_thermal_artifact_risk
safe_power_claim_level
```

硬规则：

```text
ev_photodamage_risk_band = "high"
  -> final recommendation 降级
safe_power_claim_level != "calibrated_or_bounded"
  -> 不允许真实安全功率 claim
```

### P0.23 Mie amplitude normalization hard tests

现有 Mie tests 已覆盖 basic positivity、nonabsorbing consistency、core-shell reduction、角积分 Csca 等。第四轮建议把更硬的 Mie amplitude/phase tests 提到 P0，因为 BFP mode-overlap、polarization/Jones、core-shell EV 都依赖 S1/S2 的复振幅归一化。

P0 必测：

```text
test_mie_qsca_matches_integrated_dCsca_dOmega
test_mie_extinction_optical_theorem_consistency
test_rayleigh_limit_complex_polarizability_phase
test_core_shell_small_particle_limit_against_effective_polarizability
test_S1_S2_units_and_phase_convention
```

这些测试失败时，不允许跑正式 EV design full-grid。

## P1：全量主库前建议完成的候选精修与高价值 surrogate

这些不一定进入每个 full-grid case，但代码应在全量前完成，用于重算后的候选 panel 精修。

1. `alignment_fabrication_robustness.py`
   - `AlignmentToleranceConfig`
   - focus x/z、channel position、beam waist、W/H fabrication MC
   - 输出 `alignment_robust_score_p10`、`alignment_failure_fraction`

2. `sensitivity_analysis.py`
   - Morris/Sobol-lite sensitivity
   - 输出 dominant uncertainty source
   - 若 dominant source 是 unmeasured `phi_ref` 或 BFP ROI，则绿色推荐降级

3. `inverse_problem_diagnostics.py`
   - size/RI/shell thickness Jacobian
   - 输出 `inverse_problem_condition_number`、`RI_size_degeneracy_score`
   - 推荐辅助测量：TRPS/MRPS/NTA/TEM

4. `classification_objectives.py`
   - `analysis_objective = detectability / size_estimation / EV_vs_contaminant_classification / multi_class_particle_classification`
   - 输出 `objective_specific_score`、`classification_AUC`、`feature_space_separation`

5. `matched_filter` pulse detection
   - `pulse_detection_algorithm = find_peaks / matched_filter / glrt_template_bank`
   - 输出 `matched_filter_snr`、`template_mismatch_score`

6. `interface_correction_mode="dipole_image_surrogate"`
   - 输出 `interface_corrected_E_sca_ratio`、`interface_corrected_phase_shift_rad`
   - 只做 sensitivity，不解锁 absolute phase

7. `rin/speckle/leakage/stray` relative blank-noise components
   - 输出 contribution fractions
   - 无 blank trace 时只做 surrogate

8. Counting objective / coincidence refinement
   - 在现有 `nodi_simulator/count_generation.py` 基础上新增 `single_event_detectability_score` 与 `experiment_counting_score`
   - 输出 `multi_occupancy_probability`、`coincidence_distortion_risk`、`recommended_dilution_factor`

9. `chip_panel_candidate_selector`
   - 输出 aggressive / balanced / fluidically robust / Tsuyama-like control / weak-reference control

10. Dashboard `EV Design Advisor` 和 `Claim Blocker` 页面
   - 显示 design band、claim text、blockers、recommended calibration experiments

11. `nodi_simulator/calibration_plan_advisor.py` static blocker-to-experiment map
   - 无实测数据时也能把 blocker 翻译成最小实验清单
   - 输出 `required_calibration_experiments`
   - 只给 next-step guidance，不解锁 calibrated claim

12. Selection-function-based observed distribution correction
   - 用 P0 `nodi_simulator/selection_function.py` 输出 true-vs-observed bias
   - 显示 small/low-RI EV under-detection bias
   - 不做 population inversion claim

13. Event QC scoring weights
   - 将 P0 flags 聚合为 `event_artifact_risk_score`
   - 输出 `detected_rate_after_event_qc`
   - 分类和 count score 必须使用 QC 后事件率

14. Channel geometry active surrogate
   - `rounded_rectangle` / `trapezoid_tapered_sidewalls`
   - 输出 accessible area、phase mask area 与 ideal rectangle discrepancy

15. Electrokinetic Boltzmann wall-exclusion surrogate
   - `p(x,z) proportional to v_y(x,z) * exp[-U_wall/kT]`
   - 只作为 transport sensitivity lane，不解锁真实表面化学 claim

16. `nodi_simulator/run_state_model.py`
   - 输出 `run_state_stationarity_score`、`reference_drift_rate_per_min`
   - 推荐 `recommended_reblank_interval_min`
   - 无真实 run trace 时只做 drift/fouling diagnostic

17. `nodi_simulator/nodi_thermal_contamination.py`
   - 输出 `nodi_thermal_contamination_proxy`
   - 对 Au/Ag 标准颗粒标记 absorption-to-scattering cross-talk risk
   - EV 主 gate 暂不依赖 thermal quantitative solver

18. `nodi_simulator/polarization_jones_operator.py` interface
   - `scalar_projection / jones_pupil_surrogate / measured_jones_matrix`
   - 输出 `polarization_overlap_efficiency`
   - 未测 Jones matrix 时不允许 phase/polarization quantitative claim

19. `nodi_simulator/count_likelihood.py`
   - 在 expected count-rate 之外增加 `log_likelihood_counts(...)`
   - 输出 `false_positive_corrected_count`、`false_negative_corrected_count`
   - 无浓度/blank/dead-time标定时 claim 保持 exploratory

20. `nodi_simulator/ood_detection.py`
   - Mahalanobis / one-class / density threshold / conformal rejection
   - 输出 `unknown_particle_flag`、`classifier_rejection_rate`
   - EV/contaminant classifier 不能硬分 unknown events

21. `nodi_simulator/bayesian_calibration.py` scaffold
   - 先定义 priors/posterior schema，不做重型采样
   - 输出 posterior predictive score p10 的接口

22. `nodi_simulator/experimental_design_advisor.py`
   - 将 blocker / sensitivity / model disagreement 转成 next-experiment priority
   - 输出 `value_of_information_score`

23. `nodi_simulator/population_inference.py` skeleton
   - P1 只定义 likelihood shape 和 claim blocker
   - 正式从 observed events 反推 true distribution 放到 P3

24. `nodi_simulator/population_trace_simulator.py`
   - 从 isolated single-event library 采样完整 trace：
     `blank(t) + drift(t) + sum_i event_i(t - t_i) + noise(t)`
   - 输出 `full_trace_detectability_vs_isolated_detectability_ratio`
   - P1 做 synthetic smoke；P2 接 raw blank trace

25. Random-arrival-phase NODI readout simulation
   - 在 `nodi_simulator/readout_transfer_model.py` 上增加 `random_arrival_phase_lockin`
   - 输出 `arrival_phase_average_gain`、`I/Q variance`、`magnitude bias`
   - 与 `locked_carrier_surrogate` 分歧大时降级 readout claim

26. Objective panel sweep
   - 基于 P0 `ObjectiveProfile` 扫 current/moderate/high-NA/large-spot controls
   - 输出 `objective_panel_recommendation`、`position_sensitivity_score`
   - 不把高 NA 自动当成更优；必须同时看 transit time、lock-in bandwidth、working distance 与 exposure safety

27. `nodi_simulator/ev_population_prior.py`
   - 将 EV ensemble 从独立范围升级为 correlated prior
   - 输出 `ev_prior_physical_validity`、`ev_low_RI_tail_detection_risk`
   - 与 selection function 联动，避免把不合理自由组合当成 worst case

28. Expanded contaminant library
   - 增加 HDL/VLDL/chylomicron-like、liposome/LNP、PEG/polymer aggregate、salt/crystal dust、nanobubble、cell debris、OMV/virus-like、column/resin particle
   - 输出 `contaminant_detectability_score`、`EV_specificity_risk`

29. Colored blank-noise surrogate
   - Gaussian + AR/1-f + slow multiplicative speckle
   - 输出 `colored_noise_false_alarm_status` 和 `threshold_bias`
   - 无 raw blank 时仍保持 surrogate claim

30. `nodi_simulator/fluidic_network_model.py`
   - 从单 nanochannel resistance 扩展到 microchannel/capillary/inlet/reservoir/parallel channels
   - P1 只做 diagnostic，真实 pressure-flow relation 留到 P2 measured flow

31. `nodi_simulator/control_interpretation.py`
   - 对 detergent lysis、EV-depleted、filtration、proteinase、spike-in、dilution controls 增加解释风险
   - 输出 `control_failure_interpretation`，避免把控制样品异常误读为 EV 光学结论

## P2：有第一批 blank / standard particle / transfer 数据后解锁

这些需要实测数据。全量前可以先完成接口和 manifest，但不能输出 calibrated quantitative claim。

1. Calibrated BFP ROI mask
   - blank-channel BFP image
   - slit/pinhole ROI mapping
   - `bfp_roi_mask_source="calibrated_mask"`

2. Measured lock-in transfer function
   - frequency/gain/phase/noise density/time constant/filter slope
   - `readout_internal_demod_route="measured_transfer_function"`
   - 解锁 `nodi_readout_semantics="measured_transfer_function"`，替代 random-phase surrogate

3. Standard-particle calibration
   - Au20/Au30/Au40 trace
   - `K_sca`、global phase offset、held-out validation

4. Blank false-positive bootstrap
   - raw blank trace
   - block bootstrap
   - target false-positive rate in Hz

5. Detector unit chain
   - photodiode responsivity
   - TIA gain
   - ADC scale
   - optical power / throughput
   - wavelength-specific detector responsivity / filter transmission / objective transmission
   - 只有这条链完整时，跨波长真实 detector voltage/SNR claim 才能从 blocker 升级

6. Real count-rate calibration
   - concentration, dead time, occupancy, flow velocity, dilution

7. Calibration closure update after measured data
   - 用已完成的校准实验更新 blocker 和 claim level：

```text
blank channel BFP image at each W/H/lambda
slit scan / pinhole ROI mapping
Au20/Au30/Au40 standard trace
blank buffer trace for false-positive bootstrap
flow velocity calibration
```

静态“缺什么该测什么”的清单生成属于 P1 `nodi_simulator/calibration_plan_advisor.py`；P2 只负责将真实实验结果接回 calibration state。

8. Standard particle ladder measured validation
   - Au20/Au30/Au40 可作为 sensitivity anchor
   - PS/silica/liposome/EV-mimic 用作 held-out validation 或 challenge
   - fit 标准不得同时作为 validation performance claim

9. Measured run-state and reblank calibration
   - blank/run trace 估计 reference drift、noise drift、flow drift、fouling index
   - 输出 `recommended_reblank_interval_min`

10. Bayesian calibration from real standards
   - posterior over `K_sca / rho / global_phase_offset / A_ref scale / throughput / noise`
   - 输出 posterior predictive detection-rate and design-score intervals

11. Measured Jones / polarization calibration
   - measured analyzer/Jones matrix 才允许 phase/polarization-sensitive classification claim

12. Assay-control result ingestion
   - buffer/medium/EV-depleted/lysis/spike-in/dilution controls 进入 claim blocker
   - 控制样品失败时 biological EV claim 自动降级

13. Measured optical hardware and exposure validation
   - objective throughput / BFP mapping / working distance compatibility
   - probe power at sample、spot size、temperature proxy 或 safe-power bound
   - 用于升级 `objective_design_claim_level` 与 `safe_power_claim_level`

14. Full population trace validation
   - raw blank + mixed standard/EV-mimic trace
   - 校准 overlap rejection、min-interval suppression、threshold adaptation bias
   - isolated-vs-full-trace bias 进入 candidate refinement

## P3：高保真物理与长期扩展

这些不应阻塞下一版 EV design full recompute，但要作为架构接口保留。

1. Planar-interface dyadic Green solver / fullwave lookup。
2. Debye-Wolf vector focus / measured PSF lookup。
3. Quantitative thermal POD solver and POD/NODI thermal cross-talk solver。
4. EV RI inference from orthogonal characterization。
5. Population inference from observed events after selection correction。
6. High-fidelity EV deformation / rupture model。
7. Multi-channel array optimization。
8. Channel fouling / adsorption time evolution。
9. Full Bayesian hierarchical calibration。
10. Full data lake long-table metric claim system。

## 模块清单

建议新增文件：

```text
nodi_simulator/particle_channel_perturbation.py
nodi_simulator/bfp_detector_operator.py
detector_noise_budget.py
nodi_simulator/fluidic_resistance.py
nodi_simulator/design_metrics.py
nodi_simulator/design_postprocess.py
alignment_fabrication_robustness.py
sensitivity_analysis.py
classification_objectives.py
inverse_problem_diagnostics.py
ev_ri_inference.py
nodi_simulator/calibration_plan_advisor.py
thermal_pod_solver.py
nodi_simulator/wavelength_comparability.py
nodi_simulator/readout_transfer_model.py
nodi_simulator/unit_conventions.py
nodi_simulator/optical_hardware_profiles.py
nodi_simulator/objective_panel.py
nodi_simulator/optical_exposure_safety.py
nodi_simulator/population_trace_simulator.py
nodi_simulator/ev_population_prior.py
nodi_simulator/fluidic_network_model.py
nodi_simulator/control_interpretation.py
nodi_simulator/ev_reporting_metadata.py
nodi_simulator/selection_function.py
standard_particle_ladder.py
nodi_simulator/event_quality_control.py
nodi_simulator/count_likelihood.py
nodi_simulator/channel_geometry_model.py
nodi_simulator/electrokinetic_transport.py
nodi_simulator/ev_integrity_risk.py
nodi_simulator/run_state_model.py
nodi_simulator/nodi_thermal_contamination.py
nodi_simulator/polarization_jones_operator.py
nodi_simulator/bayesian_calibration.py
nodi_simulator/experimental_design_advisor.py
nodi_simulator/ood_detection.py
nodi_simulator/population_inference.py
nodi_simulator/assay_control_matrix.py
nodi_simulator/recompute_manifest.py
```

建议扩展现有文件：

```text
nodi_simulator/data_objects.py
nodi_simulator/structured_particles.py
nodi_simulator/materials.py
nodi_simulator/reference_field.py
nodi_simulator/interferometric_trace.py
nodi_simulator/trajectory.py
nodi_simulator/pulse_analysis.py
nodi_simulator/utils.py
nodi_simulator/detector_units.py
nodi_simulator/count_generation.py
dashboard/precompute.py
dashboard/backend.py
dashboard/panels/*
tests/test_physics_core.py
tests/test_dashboard_workflow.py
```

## 测试路线

### P0 必测

1. EV design preset：
   - diffusion on
   - rect_series
   - flux_weighted
   - magnitude readout

2. Particle-channel perturbation：
   - `not_applied` 保持旧结果
   - `excluded_volume_phase_surrogate` 输出 ratio
   - ratio 高时 blocker 触发

3. BFP ROI detector：
   - `integral(|E_ref+E_sca|^2)` 不等于 collapsed scalar 时输出 disagreement
   - ROI mask status 为 surrogate 时 claim 不升格

4. Tsuyama BFP：
   - W 扫描有中间峰
   - depth scaling 不无限线性外推

5. Au20 anchor：
   - matching 不跨 W/H/lambda/reference/readout/detector route
   - 缺 anchor 时 unavailable

6. Flux-weighted：
   - rect_series 下中心流线采样概率更高
   - acceptance rate 有记录

7. Fluidic penalty：
   - `min(W,H) < 2.5 * D90` red
   - `2.5-4.0 * D90` yellow
   - 更宽 green

8. Contaminant overlap：
   - EV 与 contaminant feature overlap 高时 specificity risk 升高

9. Synthetic calibration guard：
   - synthetic fixture 不能产生 absolute 或 green_absolute recommendation

10. Metadata hash：
   - config/material/particle/detector hash 改变时 dashboard warning 触发

11. EV reporting：
   - 缺 sample source / isolation / orthogonal size method 时，biological specificity claim 关闭
   - marker/negative marker 缺失时输出 EV-like optical particle claim

12. Standard ladder split：
   - `fit` 标准不能同时作为 `validation` performance claim
   - synthetic/template standard 不解锁 calibration claim

13. Selection function：
   - 低 `P_detect` 的 50 nm low-RI EV 在 predicted observed distribution 中被下采样
   - selection bias claim level 不得升格为 true population inference

14. Event QC：
   - baseline step / local noise burst / edge-clipped pulse 不应计入 QC-pass EV pulse
   - `detected_rate_after_event_qc <= raw_detected_rate`

15. Magnitude readout governance：
   - `readout_observable_mode="magnitude"` 时 `polarity_claim_allowed=False`
   - phase-sensitive classification claim 关闭

16. Channel geometry：
   - rounded/tapered cross-section 的 accessible area 与 ideal rectangle 不同
   - roughness status 不得静默为 calibrated

17. Electrokinetic / integrity：
   - low ionic strength 下 Debye ratio 触发 transport claim 降级
   - EV diameter 接近 channel depth 时 deformation/contact risk 变高

18. Recompute manifest：
   - result row 能追溯 manifest/hash/RNG stream
   - candidate refinement manifest 与 full-grid manifest 分开

19. Cross-wavelength comparability：
   - `per_wavelength_normalization_active=True` 且 detector chain 未解锁时，`absolute_or_calibrated_lambda_comparison_allowed=False`
   - full-grid 每行必须说明 lambda ranking 是 `within_lambda_geometry_ranking_only` 还是 calibrated global comparison

20. NODI readout semantics：
   - EV design 默认不能是 `locked_carrier_surrogate`
   - locked carrier lane 只能用于 debug 或自动降级 claim
   - magnitude/random-arrival-phase 路径不得输出 phase-locked event claim

21. BFP mode-overlap：
   - `roi_complex_mode_overlap_integral` 存在并可输出 `mode_overlap_efficiency`
   - scalar-vs-ROI disagreement 大时推荐降级

22. Particle-channel double-counting guard：
   - perturbation 默认 `diagnostic_only`
   - 未通过 no-double-count guard 时不能把 perturbation 相干加入主 score

23. Unit / axis conventions：
   - Au20 / EV100 preset 名字按 diameter 解释
   - W=x、H=z、flow=y、optical axis convention 写入 summary 并有测试

24. Objective and exposure safety：
   - objective profile schema 存在
   - `transit_time_s < 3 * lockin_time_constant_s` 触发 bandwidth risk
   - 高 photodamage/heating risk 不能给绿色推荐

25. Mie amplitude normalization：
   - S1/S2 角积分、optical theorem、Rayleigh polarizability phase、core-shell 小粒子极限测试通过

### P1 必测

1. Alignment/fabrication MC 输出 p10 与 failure fraction。
2. Seed replicate 用 p10 而不是单 seed 做候选精修。
3. Matched filter 在低 SNR 合成 pulse 下不劣于 find_peaks。
4. Model consensus 分歧高时 recommendation 降级。
5. Inverse conditioning 病态时推荐辅助尺寸测量。
6. Claim text 不允许把 relative ranking 写成 absolute SNR。
7. Tsuyama focus offset / alignment surrogate 曲线对称且能进入 alignment robustness。
8. Mie series convergence 补齐，P0 amplitude/optical-theorem hard tests 已通过。
9. Selection-function observed distribution correction 保持归一化且暴露 bias factor。
10. Event QC scoring 权重不会让伪峰提高 design score。
11. OOD detection 对远离已知类的 synthetic unknown 输出 reject。
12. Count likelihood 在 false positive 增大时降低 concentration claim。
13. Bayesian calibration scaffold 不输出 posterior claim when no real standard data。
14. Value-of-information advisor 能把 dominant uncertainty 映射到下一步实验。
15. Population full-trace simulator 输出 isolated-vs-full-trace bias、overlap rejection、deadtime/min-interval suppression。
16. Objective panel sweep 不把高 NA 自动升格；必须同时看 transit、position sensitivity、working distance 和 exposure safety。
17. EV correlated prior 保持物理有效，selection function 输出 low-RI tail under-detection risk。
18. Expanded contaminant library 对 unknown/contaminant-rich case 不给 EV specificity claim。
19. Random-arrival-phase readout 与 locked-carrier lane 分歧大时降级 readout claim。
20. Control interpretation 不把 failed lysis/depleted/dilution control 静默当作 EV 光学成功。

## 全量重算前验收闸门

正式 EV design full recompute 之前必须满足：

```text
ruff / typed-seed pyright / typed-seed mypy / pytest 通过；`pyright` / `mypy` 当前只覆盖配置中的 typed-seed allowlist（公共 helper 与 legacy entrypoint），全仓类型债尚未作为 release gate；如重新运行 security audit 或 dependency audit，应在报告中单独记录当次结果和剩余风险
P0 小网格 smoke 通过
EV ensemble + Au20 + contaminants profile 可生成
standard particle ladder + fit/validation/challenge split 可生成
EV reporting readiness + assay-control skeleton 可生成
reference routes 至少有 engineering + tsuyama_bfp_integrated comparison
detector_forward_model 至少有 scalar current + ROI intensity + ROI complex mode-overlap comparison
若 ROI complex mode-overlap lane 暂缺，只能生成 exploratory full-grid，不能进入 formal EV design current truth，且所有行必须 `final_green_eligible=False`
cross-wavelength ranking blocker present；full-grid 行说明 lambda ranking 是 within-lambda only 还是 calibrated
NODI readout semantic route is not locked-carrier by default
particle-channel perturbation double-counting blocker present
radius/diameter + W/H/axis convention tests pass
objective profile schema present；objective claim level 已入 summary
safe-power / EV photodamage / thermal artifact diagnostic 已入 summary
Mie angular amplitude normalization + optical theorem hard tests pass
flux_weighted sampling 已启用或明确 blocker
selection function / event QC / magnitude-governance 字段已入 summary
geometry / electrokinetic / integrity diagnostics 已入 summary
design_postprocess 能从 smoke summary 生成 EV design table
dashboard 能显示 EV Design Advisor、Claim Blocker、Reporting Readiness、Selection Bias、Assay Controls、Wavelength/Objective Claim、Exposure Safety
synthetic calibration 不能解锁 absolute claim
metadata hash / schema inventory / recompute manifest 完整
```

## Minimum required output schema

没有以下最低字段，不允许进入正式 EV design full-grid。字段可以先以 blocker / unavailable / diagnostic 形式出现，但不能缺列；**缺列是 schema hard fail，字段值为 `unavailable` 但带 blocker 是允许的首版状态**：

```text
case_id
manifest_id
particle_preset_id
particle_size_convention
particle_radius_m
particle_diameter_m
W_nm
H_nm
lambda_nm
objective_candidate_id
normalization_scope
wavelength_ranking_claim_level
detector_forward_model
detector_operator_disagreement_band
readout_semantics
readout_observable_mode
polarity_claim_allowed
E_ref_route
reference_operating_band
particle_channel_perturbation_mode
double_counting_risk_band
unit_axis_convention_status
mie_validation_status
event_qc_pass_fraction
selection_bias_warning
safe_power_claim_level
ev_integrity_claim_level
calibration_state
output_claim_level_resolved
final_recommendation_band
final_green_eligible
primary_blocker_summary
```

这些字段是 dashboard、design_postprocess、candidate selector 和 claim generator 的共同契约；后续新增指标不能替代这组最低字段。

## 正式重算建议流程

```text
1. P0-hard complete；P0-soft required schema/skeleton complete；P1 仅完成 smoke-critical interfaces
2. unit + integration tests
3. tiny smoke grid
4. focused EV design smoke:
   W = 600/800/1000 nm
   H = 400/550/700 nm
   lambda = 404/488/532/660 nm
   EV sizes = 50/70/100/150 nm
   EV ensemble = literature_bounds_2021
   anchors = Au20/Au30/Au40
   standards = Au ladder + PS/silica/liposome challenge rows
   contaminants = LDL/HDL/protein aggregate/silica dust/PS/liposome/LNP/nanobubble
   objective profiles = current_control + moderate_upgrade schema
   readout semantics = bandpass_envelope_surrogate + random_arrival_phase smoke
   exposure safety = probe-power metadata or blocker
   controls = buffer blank / medium blank / EV-depleted / lysis / spike-in / dilution skeleton
5. design_postprocess smoke
6. selection function + event QC smoke
7. wavelength/objective/exposure claim-blocker smoke
8. population full-trace synthetic smoke
9. dashboard advisor smoke
10. formal full-grid recompute
11. top-candidate seed/alignment/model-consensus/objective-panel/refinement
12. chip + assay-control panel candidate output
```

## 推荐输出形态

最终报告不要只给 top-10。应输出：

```text
EV design table
Pareto front
route/model consensus heatmaps
EV vs contaminant specificity map
reference operating point map
fluidic risk map
chip panel candidate matrix
assay-control matrix
EV reporting readiness table
selection bias map
event QC artifact summary
population full-trace bias summary
wavelength comparability and objective profile claim summary
optical exposure / EV photodamage safety map
claim blocker summary
calibration plan advisor
value-of-information advisor
recompute manifest summary
```

推荐芯片矩阵至少包含：

```text
aggressive_high_sensitivity
balanced_primary
fluidically_robust
tsuyama_like_control
weak_reference_control
```

每个候选都要给：

```text
candidate_role
W_nm / H_nm / lambda_nm
reason_for_inclusion
main_risk
expected_validation_value
claim_level
required_calibration_experiments
required_control_samples
selection_bias_warning
event_qc_primary_failure
ev_reporting_claim_level
wavelength_ranking_claim_level
objective_candidate_id
objective_design_claim_level
safe_power_claim_level
population_full_trace_bias
```

## 立即执行路线

最小有序开发顺序：

```text
DesignObjectiveConfig + EV_NODI_only_design
  -> EV reporting metadata + assay-control skeleton
  -> unit_conventions hard gate + Mie amplitude hard tests
  -> wavelength_comparability + optical_hardware_profiles + optical_exposure_safety blockers
  -> readout_transfer_model nonsynchronized NODI semantics
  -> flux_weighted initial position
  -> particle_channel_perturbation excluded-volume diagnostic + double-counting guard
  -> bfp_detector_operator ROI mode-overlap + tsuyama_bfp_integrated route
  -> reference_design + reference_operating metrics
  -> fluidic_resistance + practicality penalty
  -> channel geometry / electrokinetic / EV integrity diagnostics
  -> EV ensemble / standard ladder / Au20 / contaminant profiles
  -> selection_function + event_quality_control + readout sign governance
  -> population_trace_simulator synthetic smoke
  -> design_metrics + design_postprocess
  -> metadata hash + recompute manifest + claim text
  -> EV Design Advisor + Claim Blocker + Reporting/Selection/Controls/Wavelength/Objective/Exposure dashboard
  -> P0 tests + smoke grid
  -> formal recompute
```

这条路线吸收了四轮建议的核心：不是继续让模拟器变得更“花”，而是让它能在没有实测闭环时诚实地输出 relative design decision；在有实测数据后，又能沿着已经铺好的接口逐步升级到 calibrated experimental platform。最终推荐对象不是单个最优通道，而是一组带 claim level、selection bias、event QC、reporting readiness、assay controls、wavelength/objective comparability、optical exposure safety 和 calibration next steps 的 EV/NODI 验证矩阵。
