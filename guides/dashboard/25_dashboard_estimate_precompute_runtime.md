# dashboard/estimate_precompute_runtime.py — 预计算时长试算脚本

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。


> 2026-04-27 修正：当前 runtime estimator 默认目标已切到 `ev_design + full_range_biomimetic_exosome_with_anchors`；`sample_wavelengths` 默认值为 `4`，当前正式目标总规模为 `32032 cases`。



## 当前使用方式

- 文档定位：预计算耗时估计专题
- 推荐阅读时机：当你要预估 full-range 或 focused sweep 的运行成本时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/estimate_precompute_runtime.md](../../dashboard/estimate_precompute_runtime.md)
- [dashboard/precompute.md](../../dashboard/precompute.md)
- [24_高性能预计算与增量重算方案.md](../../24_高性能预计算与增量重算方案.md)

## 文件职责

在目标机器上先跑一小批代表性 case，测出真实吞吐，再外推 `ev_design` 或其他配置的整库预计算时长。

这个脚本不写入正式数据集，只输出一份 JSON 报告，适合：
- 迁移到新机器前先摸底
- 比较不同 `workers` 设置的甜点值
- 估算 `ev_design/full_range_biomimetic_exosome_with_anchors` 的大致成本

---

## 用法

```bash
python -m nodi_simulator.dashboard.estimate_precompute_runtime \
  --target-grid ev_design \
  --target-particle-profile full_range_biomimetic_exosome_with_anchors \
  --workers 12 \
  --output-json runtime_ev_design_anchors.json
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--target-grid` | `ev_design` | 目标网格：`coarse`、`fine`、`focus_50_150` 或 `ev_design` |
| `--target-particle-profile` | `full_range_biomimetic_exosome_with_anchors` | 目标粒子档位：`quick`、`full_range`、`full_range_biomimetic_exosome`、`full_range_biomimetic_exosome_with_anchors` 或 focused profile |
| `--benchmark-grid` | `None` | 试算使用的网格；不填时跟 target 相同 |
| `--benchmark-particle-profile` | `None` | 试算使用的粒子档位；不填时跟 target 相同 |
| `--benchmark-events` | `None` | 只覆盖试算时的事件数；最终总时长仍按目标 grid 官方 `n_events` 推算 |
| `--sample-particles` | `4` | 试算抽样的粒子数量 |
| `--sample-widths` | `2` | 试算抽样的宽度数量 |
| `--sample-depths` | `2` | 试算抽样的深度数量 |
| `--sample-wavelengths` | `4` | 试算抽样的波长数量 |
| `--workers` | `1` | worker 进程数；`0` 表示使用全部逻辑 CPU |
| `--output-json` | `None` | 可选 JSON 输出路径 |

---

## 核心函数

### `estimate_runtime(...) → dict`

主入口。流程如下：

1. 通过 `_build_benchmark_subset()` 从目标 profile / grid 中抽样代表性粒子和网格点
2. 调用 `build_precompute_sim_cfg()` 构建与 dashboard 预计算一致的 `SimulationConfig`
3. 调用 `run_parameter_sweep(..., n_workers=...)` 实际试算
4. 用试算得到的 `events_per_second` 外推目标整库总时长
5. 返回机器信息、benchmark 吞吐和 target 估算结果

返回结构包含三块：
- `machine`
- `benchmark`
- `target`

其中 `target["estimated_readable"]` 会给出可读的时间字符串，如 `12.9 min` 或 `4.7 h`。

### `_pick_evenly_spaced(values, n) → list`

从有序列表中均匀抽样，避免 benchmark 只落在粒径或几何范围的一端。

### `_build_benchmark_subset(...) → dict`

为试算构造一个小而有代表性的粒子/宽度/深度/波长子集。

---

## 与其他文件的关系

- 读取 [15_dashboard_config.md](./15_dashboard_config.md) 对应的 `GRID_CONFIGS`、particle profile、baseline 配置
- 复用 [dashboard/precompute.md](../../dashboard/precompute.md) 对应的 `build_precompute_sim_cfg`
- 调用 [guides/core/11_parameter_sweep.md](../core/11_parameter_sweep.md) 对应的 `run_parameter_sweep`

---

## 当前口径提醒

- 当前正式 profile `full_range_biomimetic_exosome_with_anchors` 包含 Au20/Au30 anchors，加上 gold 与 biomimetic exosome 的 `40–300 nm`、`10 nm` 主范围
- `coarse` 的 W/H 步进是 `500 nm`
- `fine` 的 W/H 步进是 `100 nm`
- `ev_design` / `fine` / `focus_50_150` 当前官方 `n_events` 是 `10000`
- `--workers` 的甜点值依赖机器；建议先用这个脚本扫一轮再正式开跑

当前这台 10 核机器上，`workers=8` 附近表现最好，当前主链下最新可参考结果是：

- `coarse + full_range`: 正式实测 `3277.2 s`，约 `54.6 min`
- `ev_design + full_range_biomimetic_exosome_with_anchors`: 当前主链下尚未正式全量实测
