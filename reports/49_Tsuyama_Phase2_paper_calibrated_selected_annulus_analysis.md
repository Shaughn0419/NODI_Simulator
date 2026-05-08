# Tsuyama Phase 2 Paper-Calibrated Selected-Annulus 分析报告

> Codex 执行修订：2026-05-06。本文对应 `.omx/plans/roadmap-phase2-tsuyama-paper-calibrated-selected-annulus-2026-05-03.md` 的 G0-G5 推进结果，并合入 Phase 2.5 target-consistency、seed-median acceptance、epsilon/severity detection gate、raw-operator 修正、D2.1 局部 refphase/collection smoke、Phase 2.6 paper-reproduction rescore / size-only 3000-event confirmation、Phase 2.7 single global SNR response rescore、Phase 2.8 reviewed/descriptive score rescore、Phase 2.9 maximal upper-bound score rescore、Phase 2.10 raw Au size-response residual decomposition、Phase 2.11 single global pulse-height/readout compression rescore，以及 stop-decision 后的 ET-2030 / LI5640 instrument-aware feasibility 与 paper-statistics sensitivity boundary。Phase 2 仍是 computational paper-audit proxy lane，不修改 selected-annulus `0.5-0.8`，不回写 EV full-grid，不升级 absolute SNR / LOD / concentration claim。

## 1. 结论

Phase 2 已完成一遍完整的 computational paper-audit 闭环：target audit、read-only baseline acceptance、A-E family-ladder inverse search、8-worker / 3-seed full run、classification diagnostic 和报告同步都已跑通。full inverse 使用 `10000 events/case`、seeds `42 / 43 / 44`、`8 workers`，共评估 `52` 个 candidate、`156` 条 seed summary、`5616` 条 raw joint-case rows，运行时间约 `24968 s`（约 `6.94 h`）。Phase 2.5 之后又完成了一个更小的 D2.1 局部 smoke，只检查 `tau_2ms` 附近的 global reference phase 与窄 collection 组合，不再扩大 annulus 或 E-family correction。Phase 2.6 在现有 acceptance / inverse 工具内新增 `paper_reproduction_formula` 与 `paper_reproduction_strict_upper` rescore mode，并新增 size-only `F_paper_reproduction_fit` family，用来量化“若目标是尽量贴近 Tsuyama 数值，需要声明多大的 reproduction-only 估计项”。Phase 2.7 进一步只允许一个 single global SNR response exponent + scale，对同一批 3000-event size-only summary 做 read-only rescore。Phase 2.8 只调整评分叙事，不新增 simulation：strict Table S1 residual 改为 report-only，detection warning 与 complexity 降权，专门回答“当前低自由度估计项是否已能形成可读的数值复现口径”。Phase 2.9 再做 maximal upper-bound rescore：允许 hypothetical strict Table S1 per-wavelength Ag transfer，只用于估计“如果接受更高自由度，数值上限能到哪里”。Phase 2.10 不再追分数，而是把 raw Au size-response 拆成 wavelength、geometry、observable 和相邻粒径段，定位 raw exponent 偏陡的来源。Phase 2.11 把最后一个仍有物理可读性的低自由度方向落成显式 score：单一全局 pulse-height/readout compression `gamma` 同时作用于 size、SNR ratio 与 Ag/Au ratio。

最终签发状态是：**negative_or_diagnostic_result_only；没有 accepted paper-calibrated candidate**。这不是 EV full-grid 的失败，也不是 660/404 实验面板的阻塞项。它只说明：在当前 surrogate 和 selected-annulus `0.5-0.8` 固定口径下，Tsuyama paper-audit lane 仍只能作为 diagnostic / proxy，而不能升级为已签发的 paper-calibrated candidate。

目前最重要的正结果是：

- target audit 已把 `direct / inferred / operational / diagnostic_only` 分开，hard acceptance target 中没有 `diagnostic_only`。
- Table S1 Ag/Au target 已拆成 `interferometric_column_ratio`、`sqrt_scattering_column_ratio`、`recomputed_mie_sqrt_csca_ratio` 三种模式；当前 strict interferometric-column 口径保留作审计，但 Ag 行与论文“interferometric scattering 为 scattering 开方”的文字关系存在不一致，因此不再作为唯一 direct hard target。
- acceptance 现在以 candidate 的 seed-median 代表行签发，不再由单个 seed 的最低 score 决定 release status；JSON 同步记录 input path、hash、row count、candidate count、seed count 和 selected-annulus bounds。
- full inverse 的 best candidate 在 3 个 seeds 中解释方向稳定，且 seed-median 代表行没有触发 transfer gain、size-response、reference、rho 或 NA guardrail。
- detection alignment 不再作为本轮主 blocker：Au20 偏低降级为 weak-SNR warning，Au20 过高仍是 hard guard；Au30/Au40/Au60 使用 epsilon/severity gate，当前只有边界/轻微 warning，不触发 release blocker。
- E family 的 local signal + size transfer 可以把 Ag/Au calibrated ratio、Au size exponent 与 Au30/Au20 SNR proxy 拉到当前 tolerance 内。
- EV route shadow all-crossing dashboard 可用，selected/all uplift median 约 `1.384x`，没有出现高于 `1.6x` 的 route-level uplift warning。
- classification lane 仍是 diagnostic：feature export 完整，但本地 `sklearn` 不可用，因此保持 `no_accuracy_claim`。

目前最重要的保守结论是：

- full acceptance 现在只触发一个主 No-Go：`raw_size_response_alignment_not_met`。formula-consistent Table S1 Ag/Au raw signal 已通过；strict Table S1 signal 保留为 `strict_table_s1_signal_unresolved_formula_signal_pass` diagnostic warning。
- Au20 只有 `3/6` 个 joint cases 落入 operational band，但这些 miss 全部是 lower-bound miss；这与论文中 Au20 weak-SNR / not-all-detected 的描述相容，因此标为 `Au20_low_sensitivity_warning`，不再等同于 release blocker。
- A-D raw / non-transfer families没有出现 Ag/Au signal 与 Au size-response 同时对齐的候选：strict Table S1 target 下 raw signal 仍未通过；formula-consistent Table S1 target 下 raw signal 已有大量候选通过，但 raw Au size-response 仍未通过。full inverse 的 seed-median acceptance 下，best raw family score 约 `2.64`，best raw strict signal-ratio score 约 `0.895`，best raw formula-consistent signal-ratio score 约 `0.033`，best raw size-exponent score 约 `1.632`。D2.1 局部 smoke 把 raw size-exponent score 进一步压到约 `1.149`，但对应 raw Au exponent 仍约 `3.05`，离 `2.3` 的 paper-audit proxy target 仍明显偏陡。
- 因此，E family 的漂亮数值不能被解释成“估计参数自然收敛到论文结果”，而只能解释成 bounded local paper-fit lens 的诊断结果。
- Phase 2.6 reproduction rescore 给出了更直接的量化：D2.1 最优 reproduction base 是 `tau_2ms_global_refphi_plus`，`paper_reproduction_score_formula = 3.743`，需要全局 Au power-law size-response delta `-0.797` 和 single global SNR scale `0.728`，才能把 corrected Au exponent 映射到 `2.3`；full inverse 最优 reproduction base 是 `refspace_0p25__paper_5sigma_sensitivity`，score `4.681`，需要 delta `-0.958` 和 SNR scale `0.414`。两者都低于 raw-only 解释的残差，但都没有达到 bounded reproduction pass/partial threshold，因此仍是 `reproduction_fit_not_met`，不是 raw calibration。
- 3000-event size-only confirmation 验证了这条估计项路径的稳定性，但没有改变签发状态：最佳候选为 `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit`，`paper_reproduction_score_formula = 3.954`，required/applied global size delta `-0.878`，SNR scale `0.730`，detection alignment 为 pass/warning 级别；仍未达到 bounded reproduction pass/partial threshold，因此不进入 `10000 events/case` confirm。
- Phase 2.7 single global SNR response rescore 进一步确认：给同一个 best candidate 加入全局 SNR response exponent `0.812` 后，SNR ratio 加权残差从 `1.405` 降到 `0.423`，但 fit complexity 加权项从 `1.340` 升到 `1.931`，综合 score 只从 `3.954` 降到 `3.808`。这说明单一 SNR/readout 估计项有帮助，但在严格 scoring 下仍不足以进入 bounded partial，更不能触发 `10000 events/case` confirm。
- Phase 2.8 reviewed/descriptive rescore 进一步把“签发 acceptance”和“读者口径解释”分开：strict Table S1 residual 只报告、不计入 primary score；detection warning 与 fit complexity 作为描述性复现项降权。best candidate 仍是 `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit`，reviewed score 为 `1.9385`，状态为 `bounded_reproduction_partial_descriptive`。这意味着当前 estimated-parameter lens 已能形成一个可读的 partial paper-reproduction 叙事，但它不改变 No-Go：`raw_size_response_alignment_not_met`，也不签 raw calibration。
- Phase 2.9 maximal upper-bound rescore 则把“继续复现论文数值”推到当前合理边界：在不新增事件、不移动 annulus 的前提下，加入 hypothetical strict Table S1 Ag transfer。3000-event size-only best 的 maximal score 为 `1.2869`，仍只是 partial；full inverse 和 D2.1 的 best 上限分数分别为 `0.9814` 与 `0.9893`，可以达到 `maximal_paper_fit_upper_bound`。但它需要 per-wavelength Ag transfer gain 约 `1.76-3.12`，加上 global Au size-response / SNR response 估计项，因此只能作为高自由度 reproduction upper bound，不能签 raw calibration。
- Phase 2.10 raw Au size-response decomposition 说明 residual 的主要来源不是 Au20/Au30 低检出，而是 40→60 nm 这一段过陡。D2.1 best 的 peak-height median exponent 为 `3.0679`，local-SNR median exponent 为 `3.0882`；`peak_margin_z` 和 `peak_height_times_width` 更陡。所有 peak-height case 的 limiting pair 都是 `40-60`。660 nm 与 `1200x550` 相对最接近 target，532 nm / `800x550` 相对最差。这说明后续若继续复现，只应考虑全局 readout/pulse-height compression 这类单调压缩项；不应回头改 Au20 detection、移动 annulus 或做 per-diameter correction。
- Phase 2.11 response-compression rescore 验证了这个最后方向：D2.1 best `tau_2ms_global_refphi_plus_collection_narrow` 需要 `gamma=0.749` 才能把 Au exponent 映射到 `2.3`，score 为 `2.033`，已经非常接近但仍高于 bounded partial 阈值 `2.0`。full inverse best `low_noise_stack` score 为 `2.651`，3000-event size-only best score 为 `3.722`。因此 single global compression 只能作为 descriptive reproduction lens，不能升级为 accepted candidate；再往下若继续降分，就会需要 per-diameter、per-geometry、per-case 或 logistic remap 这类过拟合项。
- stop-decision 后的 instrument-aware feasibility 不是继续 paper-fit 搜索，而是检查实际 ET-2030 + LI5640 读出链的量级边界。`tools/instrument_hardware_feasibility.py` 用 ET-2030 silicon responsivity / NEP / 0.4 mm active area、LI5640 current/voltage sensitivity、time constant 与 filter-order prior 生成 `216` 个 feasibility rows；所有 current-input / low-noise TIA rows 都有 comfortable margin，而 50 Ω voltage path 有 `211/216` rows 低于最小 sensitivity、`5/216` rows 只是 near minimum。结论是硬件估计支持 current input / TIA 作为可行路线，但这只是 instrument feasibility estimate，不解锁 absolute SNR calibration。
- paper-statistics sensitivity boundary 使用 Phase 2.10 decomposition 只读估算 IQR trimming、finite-count sampling 或 vendor diameter distribution 需要贡献多大，才能把 limiting pair 的 slope 拉到 target `2.3`。输出 `288` rows，其中 `274` rows 为 `paper_statistics_unlikely_alone`，`14` rows 为 `paper_statistics_borderline`；最佳 D2.1 local-SNR case 仍需要对 high-diameter signal 做中位约 `30.6%` suppression，peak-height 需要约 `31.8%`。这说明 paper statistics / size distribution 可以作为解释贡献项，但没有 event-level pulses 或 measured size distribution 时，不能单独承担 raw Au size-response mismatch。

## 2. Gate 结果

| Gate | 产物 | 当前状态 | 复核结论 |
|---|---|---|---|
| G0 Target Audit | `results/tsuyama_phase2_paper_target_audit_v1/` | 完成 | `20` 个 target records，`10` 个 hard-acceptance targets；Table S1 Ag/Au ratio 拆成 strict / formula-consistent / recomputed-Mie 三种 target mode，hard target 不含 diagnostic_only |
| G1 Baseline Acceptance | `results/tsuyama_phase2_acceptance_baseline_v1/` | 完成 | best candidate 为 `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit`；detection 为 Au20 low warning，baseline release status 为 `baseline_requires_phase2_inverse_confirmation` |
| G2 Family-Ladder Inverse | `results/tsuyama_phase2_parameter_inverse_full_v1/` | 完成 | `10000 events/case`、`52` candidates、`3` seeds、`8 workers`；A-E family ladder 全量跑通 |
| G2.5 Raw-Operator Smoke | `results/tsuyama_phase2p5_operator_phase_bfp_smoke_v1/` | 完成 | `1500 events/case`、`20` candidates、`3` seeds、`8 workers`；没有 candidate 满足 promote rule，不进入 10000-event confirm |
| G2.6 D2.1 Local Smoke | `results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/` | 完成 | `2000 events/case`、`12` candidate variants、`3` seeds、`8 workers`；refphase/collection 小范围趋势稳定但仍不满足 promote rule |
| G2.7 Paper-Reproduction Rescore | `results/tsuyama_phase2p6_paper_reproduction_fit_d2p1_v1/`、`results/tsuyama_phase2p6_paper_reproduction_fit_full_inverse_v1/` | 完成 | read-only rescore；D2.1 best delta `-0.797`、full inverse best delta `-0.958`；均为 reproduction-only，status `reproduction_fit_not_met` |
| G2.8 Size-Only Reproduction Confirmation | `results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/`、`results/tsuyama_phase2p6_paper_reproduction_fit_3000e_acceptance_v1/` | 完成 | `3000 events/case`、`4` size-only candidates、`3` seeds、`8 workers`；best score `3.954`，delta `-0.878`，仍不满足 bounded reproduction pass/partial |
| G2.9 SNR Response Rescore | `results/tsuyama_phase2p7_snr_response_rescore_3000e_v1/` | 完成 | read-only rescore；best candidate 不变，SNR response exponent `0.812`，score 降至 `3.808`，仍不满足 bounded reproduction pass/partial |
| G2.10 Reviewed Score Rescore | `results/tsuyama_phase2p8_reviewed_score_rescore_3000e_v1/` | 完成 | read-only rescore；strict Table S1 report-only、detection/complexity 降权；reviewed score `1.938`，为 descriptive partial，不改变 negative/diagnostic release |
| G2.11 Maximal Upper-Bound Rescore | `results/tsuyama_phase2p9_maximal_upper_rescore_3000e_v1/`、`results/tsuyama_phase2p9_maximal_upper_rescore_full_inverse_v1/`、`results/tsuyama_phase2p9_maximal_upper_rescore_d2p1_v1/` | 完成 | read-only rescore；允许 hypothetical strict Ag transfer；D2.1/full-inverse 上限约 `0.98-0.99`，但属于 `maximal_paper_fit_upper_bound`，不改变 release |
| G2.12 Size-Response Residual Decomposition | `results/tsuyama_phase2p10_size_response_decomposition_3000e_v1/`、`results/tsuyama_phase2p10_size_response_decomposition_full_inverse_v1/`、`results/tsuyama_phase2p10_size_response_decomposition_d2p1_v1/` | 完成 | read-only decomposition；按 wavelength / geometry / observable / adjacent size pair 拆解 raw Au exponent，确认主残差来自 `40-60` pair |
| G2.13 Response-Compression Rescore | `results/tsuyama_phase2p11_response_compression_rescore_3000e_v1/`、`results/tsuyama_phase2p11_response_compression_rescore_full_inverse_v1/`、`results/tsuyama_phase2p11_response_compression_rescore_d2p1_v1/` | 完成 | single global gamma；D2.1 best score `2.033`，仍未达 bounded partial，release 不变 |
| G2.14 Instrument-Aware Feasibility | `results/instrument_hardware_feasibility_v1/` | 完成 | ET-2030 / LI5640 estimated hardware layer；current input / low-noise TIA 全部 comfortable，50 Ω voltage 多数低于 sensitivity；只作硬件可行性量级检查，不解锁 detector-unit calibration |
| G2.15 Paper-Statistics Sensitivity | `results/tsuyama_paper_statistics_sensitivity_v1/` | 完成 | 只读估算有限计数、IQR trimming、粒径分布能贡献的 flattening；`274/288` rows 为 unlikely-alone，最佳 D2.1 local-SNR 仍需约 `30.6%` high-size suppression |
| G3 Multi-Seed Signing | `results/tsuyama_phase2_acceptance_full_inverse_v1/` | 完成 | acceptance 使用 seed-median 代表行；best candidate 三 seed 稳定；detection 为 Au20 low warning + Au30-60 borderline/minor warning；formula-consistent raw signal 通过但 raw size-response 未通过，最终 release status 为 `negative_or_diagnostic_result_only` |
| G4 Classification Diagnostic | `results/tsuyama_2022_classification_lane_phase2_smoke_v1/` | 完成 | `200` feature rows、usable rows `107`、min class count `24`、`no_accuracy_claim` |
| G5 Report/Docs | 本报告、`reports/48_*`、`24_*`、`guides/operations/14_*` | 完成 | Phase 2 negative / diagnostic 边界已同步：不阻塞 660/404 实验，不改 EV 主库 |

## 3. Target Audit

G0 输出的 target manifest 把 Tsuyama paper side 的信息拆成四类：

- **Direct / audit**：Table S1 Ag40/Au40 `interferometric_column_ratio`，覆盖 488、532、660 nm；保留 strict 审计，但不再无条件作为唯一 hard target。
- **Formula-consistent**：Table S1 scattering cross-section column 的 `sqrt_scattering_column_ratio`；这是当前推荐 hard signal-ratio mode，因为它与论文文字说明一致。
- **Recomputed-Mie**：用 Table S1 fixed n,k 在本 simulator 内重算 `sqrt(Csca_Ag/Csca_Au)`，作为 inferred / diagnostic cross-check。
- **Inferred**：Au size exponent `2.3`、Au30/Au20 SNR ratio `33/12 = 2.75`。
- **Operational**：Au30/40/60 selected-annulus detection proxy bands、Au20 upper-detection guard、Au20 low-sensitivity warning，以及 selected-annulus geometry guardrail。
- **Diagnostic only**：classification accuracy `71.9 +/- 4.0%`、2020 POD Au20 near-100% counting、2024 paired POD+NODI classification。

这个拆分很关键：Phase 2 可以使用 operational / inferred target 做 proxy acceptance，但不能把它写成论文直接 ground truth。classification accuracy 暂时不能成为 hard acceptance，因为当前只完成 feature protocol 对齐，且本地没有计算 SVM accuracy。

## 4. Baseline Acceptance

read-only acceptance report 读取现有 `10000 events/case` selected-annulus joint-fit summary，没有重新跑模拟。当前 best row：

- candidate: `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit`
- joint_fit_score: `0.498779`
- paper_fit_status: `candidate_joint_fit_with_paper_transfer`
- annulus_fraction_min: `0.3813`
- transfer_gain_guardrail_penalty: `0`
- size_response_guardrail_penalty: `0`
- reference / rho / NA hard boundary: pass

分项结果：

| 指标 | 状态 | 解释 |
|---|---|---|
| target audit | pass | hard target 不含 diagnostic_only |
| detection alignment | partial_pass_with_Au20_low_warning | Au30/40/60 median pass；Au20 only-low miss 作为 weak-SNR warning |
| signal ratio | pass | calibrated Ag/Au residual 很小 |
| size exponent | pass | calibrated Au exponent = `2.3`，delta 在 guardrail 内 |
| SNR ratio | pass | Au30/Au20 ratio = `3.36086`，在当前 log tolerance 内，但仍偏高 |
| classification | diagnostic_complete | feature export protocol 对齐，但 `no_accuracy_claim` |
| no-go status | pass | baseline 不签 accepted candidate，只是因为还没有 family-ladder inverse confirmation |

这里的正确读法是：baseline 可以作为 Phase 2 的起点，但不能直接签为最终 accepted candidate。原因不是 Au20 偏低，而是 baseline 还没有证明 raw / non-transfer 参数族能够自然解释 signal ratio 与 size-response；当前最漂亮的 size/signal 结果依赖 local paper-fit transfer/size lens，需要后续 family-ladder search 和 multi-seed confirmation 确认不是“调参贴论文”。

## 5. Shadow All-Crossing Dashboard

G1 同步生成了 EV route shadow dashboard。它只用于工程 sanity，不进入 Tsuyama paper score。

| 指标 | 数值 | 解释 |
|---|---:|---|
| route_count | 572 | EV route-level full-grid route 数 |
| selected_all_uplift_median | 1.383647 | selected-annulus 系统性偏乐观，但仍在当前 uplift warning 上限内 |
| selected_all_uplift_max | 1.556754 | 未超过 `1.6x` warning threshold |
| selected_fraction_mean | 0.401984 | selected 子集约覆盖 40% 事件 |
| selected_contribution_mean | 0.060904 | annulus 子区对全事件分母的平均贡献 |
| all_crossing_detection_mean | 0.114024 | EV route all-crossing mean detection |
| selected_detection_mean | 0.151295 | selected-annulus mean detection |
| reference_useful_routes | 507 | 可作 selected cross-check |
| weak_reference_boundary_routes | 65 | 只能作边界对照 |

这组 shadow 指标支持继续使用 selected-annulus 作为 paper-audit lens，但也再次提醒：selected-annulus 不应替代 all-crossing 主工程口径。

## 6. Family-Ladder Inverse Search

G2 新增的 `tools/tsuyama_phase2_parameter_inverse.py` 把 inverse search 拆成 A-E 五个参数族；Phase 2.5 进一步新增 raw-only `D2_operator_phase_bfp_raw`，专门承接 Table S1 target ambiguity 之后最有价值的 reference phase / BFP ROI / collection operator 方向。

| Family | 角色 | 当前执行状态 |
|---|---|---|
| A | blank / threshold / colored noise / post-readout noise | 已 dry-run；已 smoke |
| B | logger / lock-in / pulse width policy | 已 dry-run |
| C | transport / event shape / fluxmix | 已 dry-run |
| D | reference / collection / rho / BFP ROI | 已 dry-run |
| D2 | paper-aligned reference phase / BFP ROI / collection operator raw search | 已 dry-run；已完成 1500-event / 3-seed smoke；没有 promotable candidate |
| E | bounded Ag transfer / Au size-response | 已 dry-run；明确最后使用 |

dry run 复核显示，A-D2 family 的 `variant_signal_transfer_mode = none`，E family 才打开 `fit_required_silver_by_wavelength` 和 `fit_required_au_power_law`。这符合“不要一开始就让 transfer/size correction 救场”的 No-Go 逻辑。D2 当前已写出完整 dry-run plan：`10` 个 raw-operator base candidates × `2` 个 threshold variants = `20` rows，覆盖 `tau_2ms_control`、`paper_aligned_phase_filter`、`refphase_flat/wide`、`global_refphi +/-`、`collection_narrow/wide`、`bfp_lobe_045/065`。

随后完成 D2 Stage 1 smoke：

```bash
python tools/tsuyama_phase2_parameter_inverse.py \
  --n-events 1500 \
  --workers 8 \
  --seeds 42 43 44 \
  --families D2_operator_phase_bfp_raw \
  --output-dir results/tsuyama_phase2p5_operator_phase_bfp_smoke_v1
```

运行结果：`20` candidates、`60` summary rows、`2160` raw rows、`12` guardrail failure rows，运行 `1827.9 s`（约 `30.5 min`）。Acceptance 输出位于 `results/tsuyama_phase2p5_operator_phase_bfp_acceptance_smoke_v1/`，最终仍是 `negative_or_diagnostic_result_only`。按 seed-median + epsilon detection 口径，这轮 D2 smoke 的 detection 只是 `partial_pass_with_Au20_low_warning` 与 Au30-60 borderline/minor warning；formula-consistent Ag/Au raw signal 已通过，真正 release blocker 是 `raw_size_response_alignment_not_met`，没有候选进入 10000-event confirm。

D2 smoke 的关键排序如下：

| 口径 | best candidate | 结果 | 解释 |
|---|---|---:|---|
| lowest joint score | `tau_2ms_global_refphi_plus` | median score `2.444` | 比 `tau_2ms_control` 略好，但仍需要 signal transfer / phase fit |
| formula-consistent Ag/Au signal | `tau_2ms_bfp_lobe_045` | formula signal score `0.0098` | Ag/Au signal 最好，但触发 hard guardrail 且 size exponent 更差 |
| raw Au size exponent | `tau_2ms_global_refphi_plus` | exponent median `3.090` | 是 D2 中最接近 `2.3` 的 raw size-response，但仍高出约 `0.79` |
| promote rule | none | `0` candidates | 没有候选同时满足 formula signal、size exponent、guardrail 和 detection sanity |

这说明 D2 raw-operator 方向有信息价值：formula-consistent Ag/Au signal 已经不是主要障碍，且 `global_refphi_plus` 对 size exponent 有轻微改善；但改善幅度不足，BFP lobe 候选虽然 signal 更好却撞 reference/guardrail 且 size-response 变差。当前不应升到 confirm，也不应扩大 E-family correction。代码层已加入 D2 operator variant diagnostic，后续输出会标记候选相对 `tau_2ms_control` 是否数值 inert，避免把“覆盖参数但输出几乎不变”的候选误读成有效搜索。

在 GPT-Pro 建议的最小 D2.1 follow-up 中，又只保留 `tau_2ms_control`、`global_refphi_plus` 的 `+0.2 / +0.4 / +0.6` 小步长、`collection_narrow` 和 `global_refphi_plus + collection_narrow` 组合，并用 `2000 events/case`、seeds `42 / 43 / 44`、`8 workers` 跑完局部 smoke：

```bash
python tools/tsuyama_phase2_parameter_inverse.py \
  --n-events 2000 \
  --workers 8 \
  --seeds 42 43 44 \
  --families D2_operator_phase_bfp_raw \
  --candidate-ids tau_2ms_control tau_2ms_global_refphi_plus_0p2 tau_2ms_global_refphi_plus tau_2ms_global_refphi_plus_0p6 tau_2ms_collection_narrow tau_2ms_global_refphi_plus_collection_narrow \
  --output-dir results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1
```

D2.1 的 acceptance 输出位于 `results/tsuyama_phase2p5_d2p1_refphi_collection_acceptance_v1/`。它把 detection alignment 提升到 `pass`，Au20 只是单点 high-outlier warning；但 release status 仍是 `negative_or_diagnostic_result_only`，唯一主 No-Go 仍是 `raw_size_response_alignment_not_met`。strict Table S1 signal 只作为 diagnostic warning 保留，局部候选排序如下：

| candidate | joint score | formula joint score | formula signal score | raw Au exponent | size score | 判断 |
|---|---:|---:|---:|---:|---:|---|
| `tau_2ms_global_refphi_plus_collection_narrow` | 2.377 | 0.687 | 0.0286 | 3.071 | 1.212 | 全局 score 最低，guardrail pass，但 size 仍失败 |
| `tau_2ms_global_refphi_plus_0p6` | 2.383 | 0.677 | 0.0322 | 3.050 | 1.149 | raw size 最好，但仍明显高于 2.3 |
| `tau_2ms_global_refphi_plus` | 2.471 | 0.761 | 0.0334 | 3.097 | 1.297 | 比 control 改善，但不够 |
| `tau_2ms_control` | 2.635 | 0.906 | 0.0328 | 3.190 | 1.616 | D2.1 baseline |

这次小验证的价值是确认趋势，而不是签发：global reference phase 往正方向移动确实能稳定压低 raw Au exponent，窄 collection 与 `+0.4` 组合能进一步改善 joint score；但是最好的 raw exponent 仍约 `3.05`，没有达到 `<= 2.85` 的 promote floor，更没有接近 `2.3`。因此 D2.1 后不应进入 raw-family `10000 events/case` confirm。如果目标是 physical calibration，后续需要实测 blank、BFP/slit/ROI、lock-in/logger 和 Au raw trace；如果目标只是用估计项尽量复现论文数值，则应转入显式 paper-reproduction rescore，而不是继续把 raw 参数自由度扩大。

Phase 2.6 按第二种目标执行：不新增工具，先在 `tools/tsuyama_phase2_acceptance_report.py` 中扩展 `primary_score_mode`，把现有 full inverse 与 D2.1 summary 重新评分为 `paper_reproduction_formula` / `paper_reproduction_strict_upper`；随后只新增 size-only `F_paper_reproduction_fit` family 做 `3000 events/case` 小确认。这个 rescore / confirmation 只允许两个全局、可声明的 reproduction-only fit terms：一个作用于所有 Au 粒径、全部 wavelength/geometry 的 power-law size-response delta；一个把 Au20/Au30 local SNR 映射到论文 SNR anchor 的 single global SNR scale。它不允许 per-diameter correction、per-case SNR scale、selected-annulus 窗口移动，也不把 E-family transfer 写成 raw calibration。

| rescore source | best candidate | formula score | class/status | required Au size delta | SNR scale | 解释 |
|---|---|---:|---|---:|---:|---|
| D2.1 local smoke | `tau_2ms_global_refphi_plus` | `3.7428` | `bounded_reproduction_fit` / `reproduction_fit_not_met` | `-0.7973` | `0.7279` | 用较小的全局 size flattening 可把 corrected exponent 映射到 `2.3`，但 SNR/detection/complexity 合成分仍未达到 bounded pass |
| full inverse | `refspace_0p25__paper_5sigma_sensitivity` | `4.6815` | `bounded_reproduction_fit` / `reproduction_fit_not_met` | `-0.9583` | `0.4138` | 比 D2.1 需要更大的 size flattening 与 SNR scale，作为历史 full inverse reproduction 对照 |
| full inverse E-family reference | `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit` | `5.6926` | `maximal_paper_fit` / `reproduction_fit_not_met` | `-0.9632` | `0.4200` | 因使用 Ag transfer + size correction，只能作为 strict upper-bound / maximal lens |

这组结果把“继续用估计值贴论文”说清楚了：formula-consistent Ag/Au signal 已经不是主要问题；最小可解释 correction 是全局 Au size-response flattening，D2.1 底座所需 delta 约 `-0.80`，比 full inverse/E-family 的约 `-0.96` 更温和。但按当前 reproduction score，最佳候选仍超过 bounded pass/partial 阈值，因此 Phase 2.6 只发布 `paper_reproduction_fit_only_not_physical_calibration`。

随后新增 size-only `F_paper_reproduction_fit` family，只对 4 个候选开启 `paper_5sigma_size_response_fit`，不开 Ag transfer、不移动 selected-annulus、不做 per-case / per-diameter correction：

```bash
python tools/tsuyama_phase2_parameter_inverse.py \
  --n-events 3000 \
  --workers 8 \
  --seeds 42 43 44 \
  --families F_paper_reproduction_fit \
  --candidate-ids tau_2ms tau_2ms_global_refphi_plus tau_2ms_global_refphi_plus_0p6 tau_2ms_global_refphi_plus_collection_narrow \
  --output-dir results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1
```

3000-event 小确认结果如下：

| candidate | formula joint score | paper reproduction score | required Au size delta | SNR scale | detection status | 判断 |
|---|---:|---:|---:|---:|---|---|
| `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `0.2788` | `3.9541` | `-0.8782` | `0.7304` | pass + Au20 high-outlier warning + Au30 minor warning | 当前 size-only reproduction best，但未过 bounded pass/partial |
| `tau_2ms_global_refphi_plus_collection_narrow__paper_5sigma_size_response_fit` | `0.3000` | `16.4235` | `-0.8414` | `0.5062` | detection loss 高 | joint score 接近，但 reproduction score 被 detection/SNR 拉低 |
| `tau_2ms_global_refphi_plus__paper_5sigma_size_response_fit` | `0.2983` | `15.6535` | `-0.8943` | `0.7266` | detection loss 高 | 不优于 `+0.6` |
| `tau_2ms__paper_5sigma_size_response_fit` | `0.3337` | `16.0397` | `-0.9563` | `0.7193` | detection loss 高 | baseline reproduction 对照 |

这一步的结论是：size-only reproduction family 确实把 size exponent score 归零，且 formula-consistent signal 保持 pass；但综合 score 仍高于 `<= 2.0` 的 bounded partial threshold。也就是说，显式全局 size flattening 是有价值的论文复现估计项，但当前还不足以让我们进入 10000-event confirmation 或签任何 accepted calibration。

Phase 2.7 随后只做 read-only rescore，不再跑新事件。它在同一 acceptance 工具内新增 `paper_reproduction_snr_response` primary score mode，允许一个全局 SNR/readout power-law exponent 加一个全局 scale，用来测试“当前 3000-event size-only result 是否只是 SNR ratio 映射没对齐”。这个估计项仍然是全局的：同一个 exponent 作用于 Au20/Au30、所有 wavelength 和 geometry；它不改变 detection rate、size-response delta、selected-annulus，也不引入 per-case 或 per-diameter SNR scale。

```bash
python tools/tsuyama_phase2_acceptance_report.py \
  --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv \
  --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv \
  --primary-score-mode paper_reproduction_snr_response \
  --output-dir results/tsuyama_phase2p7_snr_response_rescore_3000e_v1
```

| rescore mode | best candidate | score | SNR response exponent | SNR ratio weighted loss | detection weighted loss | complexity weighted loss | 判断 |
|---|---|---:|---:|---:|---:|---:|---|
| Phase 2.6 size-only | `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `3.9541` | none | `1.4053` | `1.0500` | `1.3400` | size-only best，但未过 partial |
| Phase 2.7 SNR response | `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `3.8076` | `0.8120` | `0.4235` | `1.0500` | `1.9308` | SNR ratio 明显改善，但复杂度抵消一部分收益，仍未过 partial |

Phase 2.7 的结论是负面的、但有信息量：一个全局 SNR response exponent 可以解释一部分 Au30/Au20 SNR ratio 偏差，但剩余 detection warning、strict Table S1 diagnostic residual 和 declared fit complexity 仍让 score 停在 `3.8` 左右。若不放宽评分、不加入更多自由度，这一路线不应升到 `10000 events/case`。

Phase 2.8 按用户选择的 B 路线继续：不再运行事件模拟，只复核 reproduction score 的叙事权重是否过硬。新的 `paper_reproduction_reviewed` primary score mode 保持所有物理/fit 项不变，但做三件事：

- strict Table S1 interferometric-column residual 仍完整输出，但不再进入 primary descriptive score，因为 Table S1 Ag 行与“interferometric scattering = scattering 开方”的文字解释存在 target-mode ambiguity。
- detection warning 从 hard-ish reproduction penalty 降权，保留 Au20 over-detection / Au30-60 severe miss guardrail；当前 best 只有 Au20 high-outlier warning 和 Au30 minor warning。
- fit complexity penalty 降权，用来回答“当前显式估计项是否足以写成读者可理解的 paper reproduction lens”，而不是签发 raw calibration。

```bash
python tools/tsuyama_phase2_acceptance_report.py \
  --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv \
  --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv \
  --primary-score-mode paper_reproduction_reviewed \
  --output-dir results/tsuyama_phase2p8_reviewed_score_rescore_3000e_v1
```

| rescore mode | best candidate | score | SNR response exponent | detection weighted loss | strict weighted loss | complexity weighted loss | status |
|---|---|---:|---:|---:|---:|---:|---|
| Phase 2.7 SNR response | `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `3.8076` | `0.8120` | `1.0500` | `0.1788` | `1.9308` | `reproduction_fit_not_met` |
| Phase 2.8 reviewed/descriptive | `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `1.9385` | `0.8120` | `0.3500` | `0.0000` | `0.9654` | `bounded_reproduction_partial_descriptive` |

这个结果的解释要非常严格：Phase 2.8 不是新的 acceptance pass，而是说明在“只求论文数值复现叙事”的 reader-facing score 下，当前低自由度估计项已经达到 partial reproduction；但 `candidate_release_status` 仍为 `negative_or_diagnostic_result_only`，No-Go 仍是 `raw_size_response_alignment_not_met`。换句话说，它适合写进报告作为“estimated-parameter reproduction lens”，不适合用来启动 `10000 events/case` confirm 或回写 EV full-grid。

Phase 2.9 继续沿用户指定的路线 2 推进，但把自由度边界明确标成 **maximal upper-bound**：它不再假装是 raw physical family，也不新增事件模拟；只在现有 acceptance report 中加入 `paper_reproduction_maximal_upper` score mode。这个模式允许一个 hypothetical strict Table S1 per-wavelength Ag transfer，把 strict `interferometric_column_ratio` residual 作为“如果用显式 Ag transfer 硬贴 strict 表列，最多能贴到哪里”的上限项。该 transfer 仍受 `0.25-4.0` bounded gain guardrail 约束，并单独记入 complexity / DOF；它不改 material defaults、不回写 EV full-grid，也不改变 formula-consistent Table S1 仍是更干净 signal proxy 的判断。

```bash
python tools/tsuyama_phase2_acceptance_report.py \
  --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv \
  --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv \
  --primary-score-mode paper_reproduction_maximal_upper \
  --output-dir results/tsuyama_phase2p9_maximal_upper_rescore_3000e_v1
```

同一口径也复核了 full inverse 和 D2.1 局部 smoke：

```bash
python tools/tsuyama_phase2_acceptance_report.py \
  --joint-summary results/tsuyama_phase2_parameter_inverse_full_v1/phase2_parameter_inverse_summary_v1.csv \
  --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv \
  --primary-score-mode paper_reproduction_maximal_upper \
  --output-dir results/tsuyama_phase2p9_maximal_upper_rescore_full_inverse_v1

python tools/tsuyama_phase2_acceptance_report.py \
  --joint-summary results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/phase2_parameter_inverse_summary_v1.csv \
  --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv \
  --primary-score-mode paper_reproduction_maximal_upper \
  --output-dir results/tsuyama_phase2p9_maximal_upper_rescore_d2p1_v1
```

| source | best candidate | maximal score | maximal status | size delta | strict Ag transfer gain range | 解释 |
|---|---|---:|---|---:|---:|---|
| 3000-event size-only | `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `1.2869` | `maximal_paper_fit_partial_upper_bound` | `-0.8782` | `1.810-3.070` | 仍只是 partial；低自由度候选不靠 strict Ag transfer 也已可读 |
| full inverse | `refspace_0p25__paper_5sigma_sensitivity` | `0.9814` | `maximal_paper_fit_upper_bound` | `-0.9583` | `1.902-3.116` | 上限分数可过 `<=1`，但需要更强 size delta 与 strict Ag transfer |
| D2.1 local smoke | `tau_2ms_global_refphi_plus_collection_narrow` | `0.9893` | `maximal_paper_fit_upper_bound` | `-0.7706` | `1.758-3.085` | 需要的 size delta 最温和，但仍是 high-DOF upper-bound lens |

Phase 2.9 的科学含义是：如果目标仅是“把现有 selected-annulus 输出映射到 Tsuyama paper proxy 数值附近”，那么在引入 global Au size-response correction、single global SNR response，以及 strict Table S1 per-wavelength Ag transfer 后，full inverse 与 D2.1 都能给出接近 score `1` 的上限解。但这个解的自由度已经高于 bounded descriptive reproduction；它证明的是 **可映射性上限**，不是 raw-family 自然复现。因此它正好给出当前计算路线的停点：若继续追更低分，只能引入 per-diameter / per-geometry / per-case correction 或 detection logistic remap，这会越过本项目允许的 estimated-parameter 复现边界。

Phase 2.10 不继续追更低 score，而是把 raw Au size-response residual 拆开。新增输出 `paper_reproduction_size_response_case_decomposition_v1.csv` 和 `paper_reproduction_size_response_candidate_summary_v1.csv`，对每个 seed-median candidate、每个 observable、每个 wavelength×geometry 都重新拟合 Au20/Au30/Au40/Au60 的 log-log exponent，并额外记录 `20-30`、`30-40`、`40-60` 三个相邻粒径段的局部斜率。

```bash
python tools/tsuyama_phase2_acceptance_report.py \
  --joint-summary results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/phase2_parameter_inverse_summary_v1.csv \
  --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv \
  --primary-score-mode paper_reproduction_maximal_upper \
  --output-dir results/tsuyama_phase2p10_size_response_decomposition_d2p1_v1
```

关键拆解结果如下：

| source / best | observable | median exponent | residual vs 2.3 | 最主要相邻粒径段 | 解释 |
|---|---|---:|---:|---|---|
| D2.1 `tau_2ms_global_refphi_plus_collection_narrow` | peak height | `3.0679` | `+0.7679` | `40-60` | 当前 raw 最优底座；仍明显偏陡 |
| D2.1 best | local SNR | `3.0882` | `+0.7882` | `40-60` | local SNR 没有解决 size-response |
| D2.1 best | peak margin z | `3.3165` | `+1.0165` | `40-60` | margin 口径更陡 |
| D2.1 best | peak height × width | `3.9420` | `+1.6420` | `40-60` | width/area-like 口径更不适合作为 size target |
| 3000-event size-only best | peak height | `3.1738` | `+0.8738` | `40-60` | size-only correction 前的 raw 底座比 D2.1 更陡 |
| full inverse maximal best | peak height | `3.2541` | `+0.9541` | `40-60` | full inverse 上限分低，但 raw size 底座更陡 |

D2.1 best 的 peak-height case-level decomposition 显示，最接近的组合是 `660 / 1200x550`（exponent `3.0335`）和 `660 / 800x550`（`3.0456`）；相对最差的是 `532 / 800x550`（`3.1563`）。所有 6 个 peak-height case 的 limiting pair 都是 `40-60`，不是 `20-30`。这点很关键：继续调 Au20 检出率、Au20 lower band 或 Au20 SNR，并不能解决 raw exponent 偏陡；真正需要解释的是大粒径段的 readout / phase / trajectory / collection 是否存在全局压缩或饱和。

Phase 2.10 还做了一个只读估算：如果用单一 global pulse-height response compression `signal' = signal^gamma`，D2.1 best 需要 `gamma ≈ 0.749` 才能把 peak-height exponent 映射到 `2.3`。这个估计项会把 Au30/Au20 SNR ratio 从 `3.28` 压到约 `2.43`，formula-consistent Ag/Au loss 仍约 `0.041`，但 strict Table S1 loss 仍高。这说明 response compression 是比 per-diameter correction 更值得考虑的下一种估计项；不过它仍是 reproduction lens，不是 raw calibration。

Phase 2.11 已把这个只读估算落实为正式 `paper_reproduction_response_compression` score mode。它不新增事件模拟，也不改 selected-annulus；同一个全局 `gamma` 同时作用于 Au size-response、Au20/Au30 SNR ratio 与 Ag/Au signal ratio，并且只允许一个 global SNR scale 来对应 paper-normalized Au20/Au30 anchors。它不允许 per-wavelength、per-geometry、per-diameter 或 per-case gamma，也不做 detection logistic remap。

```bash
python tools/tsuyama_phase2_acceptance_report.py \
  --joint-summary results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/phase2_parameter_inverse_summary_v1.csv \
  --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv \
  --primary-score-mode paper_reproduction_response_compression \
  --output-dir results/tsuyama_phase2p11_response_compression_rescore_d2p1_v1
```

三组输入的结果如下：

| 输入 | best candidate | gamma | response-compression score | status |
|---|---|---:|---:|---|
| D2.1 local smoke | `tau_2ms_global_refphi_plus_collection_narrow` | `0.749` | `2.033` | `response_compression_fit_not_met` |
| full inverse | `low_noise_stack` | `0.703` | `2.651` | `response_compression_fit_not_met` |
| 3000-event size-only confirmation | `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `0.724` | `3.722` | `response_compression_fit_not_met` |

D2.1 best 的 score breakdown 是：SNR-ratio loss `0.387`，SNR-anchor loss `0.0146`，formula-consistent Ag/Au loss `0.0410`，complexity penalty `0.818`，detection loss `0.65`。这里需要明确：`gamma` 是按 target/raw Au exponent 反推出的全局 readout/pulse-height compression，因此 size loss 贴近 0 是该 reproduction lens 的定义结果；真正的残差检验是 SNR ratio、paper-normalized SNR anchor、formula-consistent Ag/Au signal、detection warning 与 complexity。也就是说，global compression 确实是当前最干净的低自由度 reproduction lens，但总分 `2.033` 仍略高于 bounded partial 阈值 `2.0`。这 `0.033` 不应通过调权重抹掉，因为剩余项来自真实的 SNR ratio residual、gamma complexity 与 detection warning。至此，计算路线已经基本收口；再追更低分就需要 per-diameter / per-geometry / per-case / logistic remap 等过拟合项。

随后完成了正式 full family-ladder run：

```bash
python tools/tsuyama_phase2_parameter_inverse.py \
  --n-events 10000 \
  --workers 8 \
  --seeds 42 43 44 \
  --output-dir results/tsuyama_phase2_parameter_inverse_full_v1
```

结果：

- planned candidates: `52`
- summary rows: `156`（`52` candidates × `3` seeds）
- raw rows: `5616`
- best-candidate rows: `52`
- guardrail failure rows: `12`
- runtime: `24968.06 s`，约 `6.94 h`

整体排序显示，最低 score 都来自 E family，也就是需要同时打开 bounded Ag transfer 与 Au size-response correction 的 local paper-fit lens：

| 排名口径 | family | candidate | median score | 解释 |
|---|---|---|---:|---|
| 全局 best | E | `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit` | `0.496282` | signal ratio、size exponent、SNR proxy 都能被 local lens 拉齐 |
| E 次优 | E | `low_noise_stack_uniform_accessible__paper_5sigma_signal_size_transfer_fit` | `0.519414` | 仍依赖 signal + size transfer |
| raw best | B | `tau_2ms` | `2.641891` | 不触发 guardrail，但仍是 `candidate_needs_signal_transfer_or_phase_fit` |
| D best | D | `refspace_0p25__paper_5sigma_sensitivity` | `2.855049` | reference-space 调整没有解决 signal/size residual |
| A best | A | `baseline_current_estimates__paper_5sigma_sensitivity` | `2.875281` | readout/noise family 不能独立对齐 |
| C best | C | `low_noise_stack_fluxmix_0p10` | `2.915548` | transport/fluxmix family 不能独立对齐 |

full acceptance report 因此触发当前唯一主 No-Go：

- `raw_size_response_alignment_not_met`：acceptance 先把 `156` 条 seed summary 聚合为 `52` 个 candidate seed-median 代表行；raw/non-transfer family 共 `38` 个可用 candidate，strict Table S1 target 下 `raw_strict_signal_aligned_count = 0`，因此记录 `strict_table_s1_signal_unresolved_formula_signal_pass` diagnostic warning；formula-consistent Table S1 target 下 `raw_formula_signal_aligned_count = 27`，说明 Ag/Au raw signal mismatch 很大一部分来自 target-mode 歧义；但 `raw_size_aligned_count = 0`，`raw_joint_signal_size_aligned_count = 0`，所以仍不能签 accepted candidate。

detection side 的状态则改为 `partial_pass_with_Au20_low_warning`：Au20 在 `6` 个 joint cases 中只有 `3` 个进入 operational band，但 miss 全部偏低；Au30 为 `5/6` 且属于 minor/borderline warning，Au40/Au60 为 `6/6`。这个结果与论文中 Au20 weak-SNR、not-all-detected 的叙述相容，不再作为与 raw signal/size alignment 同等级的 release blocker。Au20 过高、Au20/Au30 倒挂、Au30-60 severe miss 或 median 明显越界仍会 hard fail。

这说明 Phase 2 找到了“如果允许 bounded local lens，怎样能数值上靠近 Tsuyama proxy target”，但没有找到“只靠 blank/noise、logger/lock-in、transport/fluxmix、reference/collection 这些估计参数就自然对齐”的候选。严格结论应是 **negative / diagnostic result**，不是 accepted paper-calibrated candidate。

## 7. Classification Diagnostic

G4 smoke run 使用 `n_events = 50`，输出 `200` feature rows；四类 Au40、Au60、Ag40、Ag60 都有 usable rows，min class count 为 `24`。本地仍显示 `sklearn_available = False`，所以 `svm_accuracy_claim_level = no_accuracy_claim`。

这与 Phase 2 红线一致：classification 只检查 feature export、class balance、raw / paper-transfer feature separability 的方向，不参与 inverse search，不作为 accepted candidate 的硬门槛。

## 8. Paper Geometry 与 EV Engineering Geometry

Phase 2 报告必须继续用双栏 claim，避免把 Tsuyama paper geometry 与 EV engineering route 混用：

| Lane | Geometry | Allowed claim |
|---|---|---|
| Tsuyama paper-audit | `660 / 800x550`、`660 / 1200x550`，并含 488/532 对照 | selected-annulus paper-audit proxy；本轮为 negative / diagnostic，不签 accepted candidate |
| EV engineering | `660 / 800x1400`、`660 / 800x1500` | reference-useful long-wave candidate，不是 paper geometry 复现 |
| Boundary control | `660 / 700x1500` | weak-reference / NA boundary control |
| Short-wave engineering | `404 / 600x1300`、`404 / 800x700` sanity | short-wave mechanism / blank / exposure validation，不是 Tsuyama direct target |

这也是为什么 Phase 2 不阻塞 660/404 第一轮实验准备。660/404 实验真正需要的是 blank、BFP、Au ladder、EV mimic、404 exposure/integrity 与 PEG/fluidic 数据；Phase 2 只让 Tsuyama paper-audit 叙事更可审计。

## 9. No-Go / Negative Result 模板

本轮 full inverse search 已触发严格 No-Go；因此本报告采用 negative result 模板，而不是 accepted candidate 模板。仍需长期保留的 stop rules 是：

- hard acceptance target 中出现 `diagnostic_only`。
- target audit 显示 Table S1 target mode 尚未 source-audited，却把 strict mode 当唯一 hard target。
- candidate 主要依赖 Ag transfer 或 Au size correction 才好看，但 raw signal + raw size-response 没有同时改善。本轮已触发。
- selected/all uplift 过强且 all-crossing shadow 完全不支持。
- SNR ratio 和 size exponent 只能二选一改善。
- top candidate 在 3 seeds 中解释方向变化。
- candidate 触发 reference-too-weak、rho 或 NA boundary。
- Au20 过高、Au20/Au30 倒挂，或 Au30/Au40/Au60 practical detection gate 崩坏。本轮未触发；本轮只是 Au20 lower-bound warning。

本轮结论应写成：

```text
Phase 2 did not sign an accepted paper-calibrated candidate.
This does not invalidate the EV full-grid engineering ranking.
It only says the current Tsuyama paper-audit selected-annulus proxy lane cannot be upgraded beyond diagnostic/proxy status without blank/BFP/detector/lock-in calibration.
```

## 10. Phase 2.11 后的边界复核

计算侧已经完成 D2.1 局部 smoke、Phase 2.6 read-only paper-reproduction rescore、`3000 events/case` size-only confirmation、Phase 2.7 single global SNR response rescore、Phase 2.8 reviewed/descriptive score rescore、Phase 2.9 maximal upper-bound rescore、Phase 2.10 raw Au size-response residual decomposition，以及 Phase 2.11 single global response-compression rescore。当前最可审计的结论是：formula-consistent Table S1 Ag/Au signal 基本可讲通，detection proxy 也不是主阻塞；剩下的核心问题是 raw Au size-response 仍偏陡。如果目标是“raw physical family 自然对齐”，D2.1 已经给出足够证据说明，继续在 global phase / scalar collection surrogate 上细扫，收益会快速递减，并容易滑向隐形 E-family correction。

如果目标是“继续用估计项尽量复现论文数值”，Phase 2.6-2.11 已经给出了分层答案。严格 reproduction score 下，最佳 size-only 候选 `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` 三 seed 稳定、无 guardrail failure，size delta `-0.878` 仍在 bounded 区间内，SNR response exponent `0.812` 也在 bounded 区间内，但 score 只降至 `3.808`，仍高于严格 `<= 2.0` threshold。reviewed/descriptive score 下，同一候选降至 `1.938`，可写成 `bounded_reproduction_partial_descriptive`。maximal upper-bound score 下，full inverse 与 D2.1 可降至约 `0.98-0.99`，但依赖 hypothetical strict Table S1 per-wavelength Ag transfer，fit DOF 增至 `6`，只能写成 `maximal_paper_fit_upper_bound`。Phase 2.11 用单一全局 response-compression 替代 per-size correction 后，D2.1 best 达到 score `2.033`，非常接近但仍未过 `<= 2.0` threshold。因此当前应停止继续加计算自由度：路线 2 已经证明“能部分或上限式贴近论文数值”，但下一步再降分就需要 per-diameter correction、per-geometry correction、per-case SNR scale 或 detection logistic remap，这会把 reproduction lens 推向过拟合。

外部 stop-decision 复核同意这一收口判断：现在可以停止 Tsuyama selected-annulus Phase 2 / Phase 2.11 的计算侧 estimated-parameter / reproduction-lens search。Phase 2.11 已经完成此前唯一仍有科学价值的后续计算方向。它说明 global response compression 是比 per-diameter correction 更干净的 reproduction lens，但仍不足以签 accepted candidate。若没有新的实测约束或明确物理新项，不再建议继续 broad raw sweep、继续调 annulus、继续调 Au20 detection，或把 score threshold/权重调到“刚好通过”。

为了避免“是不是停得太早”的误判，stop-decision 后又补了两个只读边界检查。第一个是 ET-2030 + LI5640 的 instrument-aware feasibility：在 estimated silicon responsivity、NEP、LI5640 current sensitivity、time constant / filter-order prior 下，current-input / low-noise TIA 连接具备 comfortable sensitivity margin；同样的弱 photocurrent 若走 50 Ω voltage path，多数配置低于最小 voltage sensitivity。这支持第一轮实验优先核对 current-input / TIA 接法和量程，而不是继续在 optical surrogate 里调相位。第二个是 paper-statistics sensitivity：把 Phase 2.10 的 limiting-pair decomposition 转换成“需要把 high-diameter member 压低多少才能匹配 `2.3` exponent”。结果显示大部分 case 需要 `30%+` 的 high-size signal suppression；这意味着 IQR trimming、500-count finite sampling 或 vendor size dispersion 可能解释一部分 flattening，但没有 event-level pulses / TEM-DLS batch distribution 时，不能单独把 40-60 nm 斜率问题讲通。

长期 stop rule 仍需保留：除非拿到新的实测 blank / BFP / detector / lock-in / Au trace 数据，或者新增的是明确由这些实测数据约束的 operator model，否则不再把 broad raw-parameter sweep 作为主路线。若未来确实重启 raw-family 计算，promote 条件仍保持严格：formula-consistent signal score 通过或 strict signal score 显著下降，同时 raw Au size exponent 至少降到 `2.85` 以下或相对当前 D2.1 best 再改善 `>= 0.25`，且 Au30-60 detection 不能 severe fail，Au20 不能过检，三 seeds 方向一致。

如果要把 Phase 2 从 proxy 继续往 absolute calibration 推进，还需要以下最小实测数据：

| 数据包 | 作用 |
|---|---|
| blank trace by wavelength/geometry | false positive、drift、colored noise |
| empty-channel BFP / slit / ROI image | collection operator / reference band |
| Au20/30/40/60 raw traces | SNR、size exponent、threshold 与 pulse extraction |
| lock-in settings and logger sampling metadata | pulse width / demod response |
| detector gain / responsivity / filter transmission | detector-unit calibration |
| pressure-flow and clogging log | paper geometry 与 EV engineering geometry 的流体可行性 |

没有这组数据时，Phase 2 即使 full inverse search 数值漂亮，也只能发布 paper-calibrated proxy / diagnostic，不能升级为 absolute detection efficiency reproduction。

## Appendix A. 输出文件

- `tools/tsuyama_paper_target_audit.py`
- `tools/tsuyama_phase2_acceptance_report.py`
- `tools/tsuyama_phase2_parameter_inverse.py`
- `results/tsuyama_phase2_paper_target_audit_v1/`
- `results/tsuyama_phase2_acceptance_baseline_v1/`
- `results/tsuyama_phase2_parameter_inverse_dryrun_v1/`
- `results/tsuyama_phase2_parameter_inverse_smoke_v1/`
- `results/tsuyama_phase2_parameter_inverse_full_v1/`
- `results/tsuyama_phase2_acceptance_full_inverse_v1/`
- `results/tsuyama_phase2p5_operator_phase_bfp_dryrun_v1/`
- `results/tsuyama_phase2p5_operator_phase_bfp_smoke_v1/`
- `results/tsuyama_phase2p5_operator_phase_bfp_acceptance_smoke_v1/`
- `results/tsuyama_phase2p5_d2p1_refphi_collection_dryrun_v1/`
- `results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/`
- `results/tsuyama_phase2p5_d2p1_refphi_collection_acceptance_v1/`
- `results/tsuyama_phase2p6_paper_reproduction_fit_d2p1_v1/`
- `results/tsuyama_phase2p6_paper_reproduction_fit_full_inverse_v1/`
- `results/tsuyama_phase2p6_paper_reproduction_fit_dryrun_v1/`
- `results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/`
- `results/tsuyama_phase2p6_paper_reproduction_fit_3000e_acceptance_v1/`
- `results/tsuyama_phase2p7_snr_response_rescore_3000e_v1/`
- `results/tsuyama_phase2p8_reviewed_score_rescore_3000e_v1/`
- `results/tsuyama_phase2p9_maximal_upper_rescore_3000e_v1/`
- `results/tsuyama_phase2p9_maximal_upper_rescore_full_inverse_v1/`
- `results/tsuyama_phase2p9_maximal_upper_rescore_d2p1_v1/`
- `results/tsuyama_phase2p10_size_response_decomposition_3000e_v1/`
- `results/tsuyama_phase2p10_size_response_decomposition_full_inverse_v1/`
- `results/tsuyama_phase2p10_size_response_decomposition_d2p1_v1/`
- `results/tsuyama_phase2p11_response_compression_rescore_3000e_v1/`
- `results/tsuyama_phase2p11_response_compression_rescore_full_inverse_v1/`
- `results/tsuyama_phase2p11_response_compression_rescore_d2p1_v1/`
- `results/tsuyama_2022_classification_lane_phase2_smoke_v1/`
- `tools/instrument_hardware_feasibility.py`
- `tools/tsuyama_paper_statistics_sensitivity.py`
- `results/instrument_hardware_feasibility_v1/`
- `results/tsuyama_paper_statistics_sensitivity_v1/`

## Appendix B. 测试

新增 focused regression tests：

- `tests/test_tsuyama_paper_target_audit.py`
- `tests/test_tsuyama_phase2_acceptance.py`
- `tests/test_tsuyama_phase2_parameter_inverse.py`
- `tests/test_instrument_hardware_feasibility.py`
- `tests/test_tsuyama_paper_statistics_sensitivity.py`

已执行并通过：

- `python -m pytest tests/test_tsuyama_paper_target_audit.py -q`
- `python -m pytest tests/test_tsuyama_phase2_acceptance.py -q`
- `python -m pytest tests/test_tsuyama_phase2_parameter_inverse.py -q`
- `python -m pytest tests/test_tsuyama_phase2_acceptance.py tests/test_tsuyama_paper_target_audit.py -q`
- `python -m pytest tests/test_tsuyama_phase2_parameter_inverse.py tests/test_tsuyama_selected_annulus_joint_fit.py -q`
- `python -m pytest tests/test_tsuyama_phase2_acceptance.py -q` → `33 passed`
- `python -m pytest tests/test_tsuyama_paper_target_audit.py tests/test_tsuyama_phase2_acceptance.py tests/test_tsuyama_phase2_parameter_inverse.py tests/test_tsuyama_selected_annulus_joint_fit.py tests/test_tsuyama_2022_classification_lane.py tests/test_tsuyama_gold_aligned_detection_lane.py tests/test_tsuyama_annulus_ratio_sensitivity.py -q` → `74 passed`
- `python -m pytest tests/test_instrument_hardware_feasibility.py tests/test_tsuyama_paper_statistics_sensitivity.py -q` → `9 passed`
- `python -m ruff check tools/tsuyama_paper_target_audit.py tools/tsuyama_phase2_acceptance_report.py tools/tsuyama_phase2_parameter_inverse.py tools/tsuyama_selected_annulus_joint_fit.py tools/tsuyama_detection_rate_calibration.py tests/test_tsuyama_paper_target_audit.py tests/test_tsuyama_phase2_acceptance.py tests/test_tsuyama_phase2_parameter_inverse.py tests/test_tsuyama_selected_annulus_joint_fit.py`
- `python -m ruff check tools/instrument_hardware_feasibility.py tools/tsuyama_paper_statistics_sensitivity.py tests/test_instrument_hardware_feasibility.py tests/test_tsuyama_paper_statistics_sensitivity.py`
- 当时完整 `python -m pytest -q` 基线通过；当前全仓库验证基线请以 `README.md` 和 `tests/run_tests.md` 为准。
- `python -m ruff check .`
- `python -m pyright` → `0 errors, 0 warnings, 0 informations`
- `python -m compileall -q -x '(^|.*/)[.]_' .`
- `python -m py_compile tools/tsuyama_paper_target_audit.py tools/tsuyama_phase2_acceptance_report.py tools/tsuyama_phase2_parameter_inverse.py tools/tsuyama_selected_annulus_joint_fit.py tools/tsuyama_detection_rate_calibration.py`
- `python -m py_compile tools/instrument_hardware_feasibility.py tools/tsuyama_paper_statistics_sensitivity.py tests/test_instrument_hardware_feasibility.py tests/test_tsuyama_paper_statistics_sensitivity.py`
- `python tools/tsuyama_paper_target_audit.py`
- `python tools/tsuyama_phase2_acceptance_report.py --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv`
- `python tools/tsuyama_phase2_parameter_inverse.py --dry-run --max-candidates-per-family 2 --output-dir results/tsuyama_phase2_parameter_inverse_dryrun_v1`
- `python tools/tsuyama_phase2_parameter_inverse.py --dry-run --families D2_operator_phase_bfp_raw --output-dir results/tsuyama_phase2p5_operator_phase_bfp_dryrun_v1`
- `python tools/tsuyama_phase2_parameter_inverse.py --n-events 1500 --workers 8 --seeds 42 43 44 --families D2_operator_phase_bfp_raw --output-dir results/tsuyama_phase2p5_operator_phase_bfp_smoke_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p5_operator_phase_bfp_smoke_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --output-dir results/tsuyama_phase2p5_operator_phase_bfp_acceptance_smoke_v1`
- `python tools/tsuyama_phase2_parameter_inverse.py --dry-run --families D2_operator_phase_bfp_raw --candidate-ids tau_2ms_control tau_2ms_global_refphi_plus_0p2 tau_2ms_global_refphi_plus tau_2ms_global_refphi_plus_0p6 tau_2ms_collection_narrow tau_2ms_global_refphi_plus_collection_narrow --output-dir results/tsuyama_phase2p5_d2p1_refphi_collection_dryrun_v1`
- `python tools/tsuyama_phase2_parameter_inverse.py --n-events 2000 --workers 8 --seeds 42 43 44 --families D2_operator_phase_bfp_raw --candidate-ids tau_2ms_control tau_2ms_global_refphi_plus_0p2 tau_2ms_global_refphi_plus tau_2ms_global_refphi_plus_0p6 tau_2ms_collection_narrow tau_2ms_global_refphi_plus_collection_narrow --output-dir results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --output-dir results/tsuyama_phase2p5_d2p1_refphi_collection_acceptance_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_formula --output-dir results/tsuyama_phase2p6_paper_reproduction_fit_d2p1_v1`
- `python tools/instrument_hardware_feasibility.py --output-dir results/instrument_hardware_feasibility_v1`
- `python tools/tsuyama_paper_statistics_sensitivity.py --input results/tsuyama_phase2p10_size_response_decomposition_d2p1_v1/paper_reproduction_size_response_case_decomposition_v1.csv --output-dir results/tsuyama_paper_statistics_sensitivity_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2_parameter_inverse_full_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_formula --output-dir results/tsuyama_phase2p6_paper_reproduction_fit_full_inverse_v1`
- `python tools/tsuyama_phase2_parameter_inverse.py --dry-run --families F_paper_reproduction_fit --candidate-ids tau_2ms tau_2ms_global_refphi_plus tau_2ms_global_refphi_plus_0p6 tau_2ms_global_refphi_plus_collection_narrow --output-dir results/tsuyama_phase2p6_paper_reproduction_fit_dryrun_v1`
- `python tools/tsuyama_phase2_parameter_inverse.py --n-events 3000 --workers 8 --seeds 42 43 44 --families F_paper_reproduction_fit --candidate-ids tau_2ms tau_2ms_global_refphi_plus tau_2ms_global_refphi_plus_0p6 tau_2ms_global_refphi_plus_collection_narrow --output-dir results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_formula --output-dir results/tsuyama_phase2p6_paper_reproduction_fit_3000e_acceptance_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_snr_response --output-dir results/tsuyama_phase2p7_snr_response_rescore_3000e_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_reviewed --output-dir results/tsuyama_phase2p8_reviewed_score_rescore_3000e_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_maximal_upper --output-dir results/tsuyama_phase2p9_maximal_upper_rescore_3000e_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2_parameter_inverse_full_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_maximal_upper --output-dir results/tsuyama_phase2p9_maximal_upper_rescore_full_inverse_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_maximal_upper --output-dir results/tsuyama_phase2p9_maximal_upper_rescore_d2p1_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_maximal_upper --output-dir results/tsuyama_phase2p10_size_response_decomposition_3000e_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2_parameter_inverse_full_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_maximal_upper --output-dir results/tsuyama_phase2p10_size_response_decomposition_full_inverse_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_maximal_upper --output-dir results/tsuyama_phase2p10_size_response_decomposition_d2p1_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_response_compression --output-dir results/tsuyama_phase2p11_response_compression_rescore_3000e_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2_parameter_inverse_full_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_response_compression --output-dir results/tsuyama_phase2p11_response_compression_rescore_full_inverse_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --primary-score-mode paper_reproduction_response_compression --output-dir results/tsuyama_phase2p11_response_compression_rescore_d2p1_v1`
- `python tools/tsuyama_phase2_parameter_inverse.py --n-events 50 --workers 8 --seeds 42 43 44 --families A_blank_threshold_noise --max-candidates-per-family 1 --output-dir results/tsuyama_phase2_parameter_inverse_smoke_v1`
- `python tools/tsuyama_phase2_parameter_inverse.py --n-events 10000 --workers 8 --seeds 42 43 44 --output-dir results/tsuyama_phase2_parameter_inverse_full_v1`
- `python tools/tsuyama_phase2_acceptance_report.py --joint-summary results/tsuyama_phase2_parameter_inverse_full_v1/phase2_parameter_inverse_summary_v1.csv --target-manifest results/tsuyama_phase2_paper_target_audit_v1/tsuyama_paper_targets_v1.csv --output-dir results/tsuyama_phase2_acceptance_full_inverse_v1`
- `python tools/tsuyama_2022_classification_lane.py --n-events 50 --random-seed 42 --compute-svm --output-dir results/tsuyama_2022_classification_lane_phase2_smoke_v1`
