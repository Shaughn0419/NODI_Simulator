# 深度依赖的 reference-model / 噪声口径证据 (report 146)

- 日期: 2026-06-03  口径: Level-1 no-measured-data 灵敏度检查
- 复现: `PYTHONPATH=. .venv/bin/python tmp/depth_evidence_artifact.py`  数据: `results/depth_reference_model_noise_regime_probe_20260603.csv`
- 配置: 全网格同款 frozen-B 算子 (`build_frozen_b_cfg`), 单粒子 `exosome_literature_bounds_2021_02_membrane_only_nominal_2020_100nm`, 4000 events, seed 11
- 仅切换 `reference_model`(+兼容 route) 与 `shot_noise_scale`; 其余与全网格一致
- 口径说明: 本探针的 `det_rate` 是 **all-crossing** engineering-basis 检出率(单粒子焦点探针),用于暴露机理;它**不替代**全网格被治理的 selected-annulus 推荐面(该面上深度更弱,见 §4 与 report 140)。本探针是机理灵敏度检查,不是 ensemble/先验加权结论。

## 1. 全网格实际用的是 paper_aligned, 不是 surrogate

`build_frozen_b_cfg` 实例化结果: `reference_model=paper_aligned_phase_filter`, `reference_route=paper_aligned_comparison`, `reference_na_edge_policy=hard_guardrail`, `NA_collection=0.9`。

## 2. 深度依赖在两种 reference model 下几乎一致 (非 surrogate 伪影)

### 660 nm / W800

| reference_model | D500 det | D1500 det | depth-span | A_ref D500→D1500 |
|---|---:|---:|---:|---|
| paper_aligned_phase_filter | 0.502 | 0.652 | 0.150 (23%) | 0.456→1.213 |
| channel_angular_surrogate | 0.471 | 0.646 | 0.175 (27%) | 0.456→1.196 |

### 404 nm / W500

| reference_model | D500 det | D1500 det | depth-span | A_ref D500→D1500 |
|---|---:|---:|---:|---|
| paper_aligned_phase_filter | 0.495 | 0.722 | 0.227 (31%) | 0.798→1.708 |
| channel_angular_surrogate | 0.494 | 0.707 | 0.212 (30%) | 0.795→1.649 |

机理: `A_ref` 随深度近线性增长 (`depth_scale=depth/550nm`, reference_field.py:673), 两模型一致; 外差增益项 2·Re(E_ref·E_sca*) 随 A_ref 抬升 margin_z, 把更多边缘事件推过**固定的 electronics 噪声门**。被代码标注为 spurious 的 surrogate 深度项 (kz 孔径/相位斜率) 只贡献两模型之间的小差异。

## 3. 深度收益依赖噪声口径 (electronics vs shot)

660 nm / W800, paper_aligned, 改变 `shot_noise_scale`:

| 噪声口径 | shot_scale | D500 | D900 | D1500 | depth-span | operating band |
|---|---:|---:|---:|---:|---:|---|
| electronics_limited_as_run | 0.001 | 0.502 | 0.556 | 0.652 | 0.150 (23%) | electronics_noise_limited_useful |
| shot_noise_heavy | 0.05 | 0.488 | 0.523 | 0.595 | 0.106 (18%) | shot_noise_limited_no_gain |
| shot_noise_dominant | 0.2 | 0.442 | 0.436 | 0.476 | 0.040 (8%) | shot_noise_limited_no_gain |

结论: 从 electronics-limited 走向 shot-limited, depth-span 收缩约一半, band 翻成 `shot_noise_limited_no_gain`。深度收益不是普适物理常数, 而是随**未标定的噪声口径**变化。

## 4. 对设计的含义

- 深度收益真实存在于模型中, 但其幅度取决于 (i) `A_ref∝depth` 线性外推 (无实测锚, 与 Tsuyama 2020 Eq.13 'S/B 与深度无关' 张力), 与 (ii) electronics-noise-limited 假设。
- 在被治理的 selected-annulus 推荐面上深度本就弱 (3–10%, 4 个先验里 2 个最优在中深 D900)。
- 工程建议: 深度按工艺取中深 (D900–D1200), 不为 D1400 买单; 用 measured blank + detector transfer 先把噪声口径钉死, 再决定是否加深。