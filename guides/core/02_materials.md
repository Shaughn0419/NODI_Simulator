# materials.py — 材料数据库模块


<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件职责

管理整个系统中所有材料在不同波长下的复折射率。服务对象不仅是粒子，还包括介质（当前按粒子类型在 water / 1x PBS 间切换）和通道壁（当前默认熔融石英）——任何需要折射率的地方都通过本模块的统一接口获取数据。

**核心设计原则**：单一数据来源。系统中不存在第二个"材料常数查询入口"，所有材料光学常数最终都汇聚到 `get_n_complex(material_key, wavelength_m)` 这一个函数。这避免了后续在 reference field、near-wall correction 等模块中出现"两套材料来源"的问题。

---

## 数据结构

### MATERIAL_DB

全局字典，存储所有材料条目。每个条目按当前代码有四类：

**tabulated（查表插值型）**：

```python
"gold": {
    "source": "Johnson & Christy 1972",
    "type": "tabulated",
    "wavelength_m": np.array([...]),   # 400–700nm，31个点
    "n_real": np.array([...]),
    "n_imag": np.array([...]),
}
```

适用于光学常数随波长显著变化的材料（如金属）。查询时做线性插值。

**cauchy / sellmeier（名义色散公式型）**：

```python
"pbs_1x": {
    "source": "water Cauchy surrogate plus nominal PBS offset",
    "type": "cauchy",
    "wavelength_range_m": (400e-9, 700e-9),
    "n_imag_const": 0.0,
}
```

`water` 使用 visible Cauchy nominal surrogate；`fused_silica` 使用 Malitson Sellmeier nominal dispersion。这些公式只解锁 nominal dispersion diagnostics，不包含温度、buffer composition 或 uncertainty propagation。

**constant（常数型）**：

```python
"polystyrene": {
    "source": "Literature constant for visible range",
    "type": "constant",
    "n_real_const": 1.59,
    "n_imag_const": 0.0,
}
```

适用于保留的历史/兼容材料。所有波长返回同一值。

### 第一批材料

| material_key | 来源 | 类型 | 波长范围 | 备注 |
|-------------|------|------|---------|------|
| gold | Johnson & Christy 1972 | tabulated | 400–700nm | 31 个数据点，线性插值 |
| silver | Johnson & Christy 1972 | tabulated | 约 397–705nm | visible Ag 数据点，线性插值 |
| pbs_1x | water Cauchy + nominal PBS offset | cauchy | 400–700nm | 当前 exosome 默认介质 |
| hepes_buffer | water Cauchy + nominal HEPES offset | cauchy | 400–700nm | EV buffer scaffold |
| culture_medium_surrogate | water Cauchy + nominal culture-medium offset | cauchy | 400–700nm | culture medium scaffold |
| sucrose_solution_xpct | nominal sucrose-gradient surrogate | cauchy | 400–700nm | 密度梯度介质 scaffold |
| iodixanol_solution_xpct | nominal iodixanol-gradient surrogate | cauchy | 400–700nm | 密度梯度介质 scaffold |
| fused_silica | Malitson Sellmeier | sellmeier | 210–3710nm | 当前默认壁材 |
| fused_silica_viosil | Viosil nominal + Malitson surrogate | sellmeier | 210–3710nm | 供应商/材料 profile scaffold |
| water | room-temperature visible Cauchy surrogate | cauchy | 400–700nm | 当前 gold 介质 |
| glass_bk7 | Sellmeier / 常数近似 | constant | 任意 | n=1.52，保留为历史/兼容条目 |
| polystyrene | 文献常数 | constant | 任意 | n=1.59 |
| exosome_uniform | 文献范围 1.37–1.40 | constant | 任意 | n=1.38，均匀球近似 |

> 2026-04-10 更新：`exosome_uniform` 现在属于历史紧凑基线，仍保留在 `MATERIAL_DB` 中供旧结果与对照使用。当前默认 exosome 生产模型已经迁移到结构化粒子链路中的 biomimetic core-shell family，不再只靠这里的单一常数折射率条目表达。

---

## 函数

### `get_n_complex(material_key, wavelength_m) → complex`

**作用**：返回指定材料在指定波长下的复折射率 n + ik。

**内部逻辑**：
1. 从 MATERIAL_DB 查找 material_key
2. 如果 type="constant"，直接返回 `n_real_const + i·n_imag_const`
3. 如果 type="tabulated"，检查波长范围并线性插值
4. 如果 type="cauchy" / "sellmeier"，检查名义适用范围并计算可见色散

**异常**：
- `KeyError`：材料不在数据库中
- `ValueError`：波长超出 tabulated 材料的数据范围（如 gold 的 400–700nm）

**示例输出**：

| 调用 | 返回值 |
|------|--------|
| get_n_complex("gold", 488e-9) | 0.668 + 1.586i |
| get_n_complex("gold", 532e-9) | 0.320 + 1.564i |
| get_n_complex("gold", 660e-9) | 0.164 + 2.470i |
| get_n_complex("pbs_1x", 532e-9) | 1.334 + 0.0i |
| get_n_complex("water", 532e-9) | 1.33 + 0.0i |

---

### `list_materials() → list[str]`

返回数据库中所有可用 material_key 的排序列表。

---

### `material_db_coverage_diagnostics() → dict`

返回当前材料库覆盖度状态，用于 summary / metadata / health 输出。重点字段包括：

- `material_db_coverage_status`
- `tsuyama_AuAg_multispectral_supported`
- `medium_wall_dispersion_status`
- `material_db_gold_status`
- `material_db_silver_status`

这些字段只说明材料库是否足以支持当前 governed comparison；它们不会替代真实材料 uncertainty propagation。

### `material_property_summary(material_key, wavelength_m) → dict`

返回某个材料在指定波长下的折射率、热/输运 nominal 属性、来源与 claim level。该函数用于把材料介质、壁材、热/POD 和 uncertainty 边界写成扁平 provenance 字段；没有实测材料批次或 uncertainty budget 时，仍只能作为 nominal material property summary。

---

## 与其他模块的交互

```
materials.py
    │
    ├──→ Particle.n_complex_at(wavelength_m)      [data_objects.py]
    │       用于 intrinsic_scattering 中的粒子折射率查询
    │
    ├──→ Medium.refractive_index_at(wavelength_m)  [data_objects.py]
    │       用于 intrinsic_scattering 中的介质折射率查询
    │
    └──→ Channel.wall_refractive_index_at(wavelength_m) [data_objects.py]
            为后续 Phase（near-wall correction）预留
```

**关键约束**：materials.py 本身不依赖工程中的任何其他模块（只依赖 numpy），处于依赖链最底层。数据类通过延迟导入（`from .materials import get_n_complex`）调用它，避免循环依赖。

---

## 当前模型中介质/壁材料的说明

Medium 和 Channel 的波长查询接口现在已经接入 nominal dispersion：

- `water` 使用 room-temperature visible Cauchy nominal surrogate。
- `pbs_1x` 使用 water Cauchy + nominal PBS offset。
- `hepes_buffer`、`culture_medium_surrogate`、`sucrose_solution_xpct`、`iodixanol_solution_xpct` 是 EV sample / gradient / buffer scaffold，用于暴露未来介质 profile 与 claim 边界。
- `fused_silica` 使用 Malitson Sellmeier nominal dispersion。
- `fused_silica_viosil` 复用 Malitson Sellmeier 作为 Viosil nominal scaffold。
- 固定值材料仍保留为历史/兼容条目，例如 `glass_bk7`、`polystyrene`、`exosome_uniform`。

这仍然只是 nominal dispersion，不包含温度、buffer composition、材料批次或 uncertainty propagation；因此它能支撑 multispectral engineering / paper-aligned comparison provenance，不能单独解锁 absolute calibrated material claim。
