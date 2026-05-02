"""
dashboard/config.py — 共享配置

precompute.py 和 backend.py 都从这里读取参数。
修改此文件 = 修改整个面板的物理假设。
"""

import numpy as np
import sys
import os
import re

# Ensure the project remains importable even if the repo directory is renamed.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_PARENT = os.path.dirname(PROJECT_ROOT)
for candidate in (PROJECT_ROOT, PROJECT_PARENT):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator import (
    Particle, Medium, OpticalSystem, SimulationConfig, WATER,
    PBS_1X,
    make_gold_baseline_particle,
    list_exosome_model_presets,
    make_biomimetic_exosome_particle,
    make_biomimetic_exosome_ensemble_particles,
)

REFERENCE_CALIBRATION_PATH = os.environ.get("NODI_REFERENCE_CALIBRATION_PATH")
DEFAULT_REFERENCE_MODEL = (
    "calibrated_lookup" if REFERENCE_CALIBRATION_PATH else "channel_angular_surrogate"
)
DEFAULT_REFERENCE_ROUTE = (
    "calibrated_primary" if REFERENCE_CALIBRATION_PATH else "engineering_fallback"
)
REFERENCE_ROUTE_OPTIONS = [
    "calibrated_primary",
    "paper_aligned_comparison",
    "engineering_fallback",
    "legacy_debug",
]
REFERENCE_ROUTE_WARNING = (
    {
        "status": "calibrated_primary_blank_table",
        "message": "Blank-channel calibration path is active; reference uses calibrated_lookup.",
    }
    if REFERENCE_CALIBRATION_PATH
    else {
        "status": "engineering_fallback_no_blank_calibration",
        "message": (
            "No blank-channel calibration path is configured; reference uses "
            "engineering_fallback semantics rather than calibrated truth."
        ),
    }
)

# ============================================================
# 角度网格
# ============================================================
THETA_GRID_RAD = np.linspace(0.01, np.pi - 0.01, 500)

# ============================================================
# 粒子系统：类型 + 粒径分离
# ============================================================
DISPLAY_TO_MATERIAL_KEY = {
    "gold": "gold",
    "exosome": "exosome_uniform",
}
MATERIAL_KEY_TO_DISPLAY = {
    value: key for key, value in DISPLAY_TO_MATERIAL_KEY.items()
}
MATERIAL_OPTIONS = list(DISPLAY_TO_MATERIAL_KEY.keys())
DIAMETER_RANGE_NM = (40, 300)
FULL_DIAMETER_STEP_NM = 10
FULL_DIAMETER_VALUES_NM = list(
    range(DIAMETER_RANGE_NM[0], DIAMETER_RANGE_NM[1] + 1, FULL_DIAMETER_STEP_NM)
)
GOLD_ANCHOR_DIAMETER_VALUES_NM = [20, 30]
EXOSOME_FOCUS_DIAMETER_RANGE_NM = (50, 150)
EXOSOME_FOCUS_DIAMETER_VALUES_NM = list(
    range(
        EXOSOME_FOCUS_DIAMETER_RANGE_NM[0],
        EXOSOME_FOCUS_DIAMETER_RANGE_NM[1] + 1,
        FULL_DIAMETER_STEP_NM,
    )
)
DASHBOARD_DIAMETER_STEP_NM = FULL_DIAMETER_STEP_NM
DASHBOARD_DIAMETER_VALUES_NM = tuple(FULL_DIAMETER_VALUES_NM)
DEFAULT_DASHBOARD_DIAMETER_NM = 100
FULL_SWEEP_WAVELENGTHS_NM = (404, 488, 532, 660)
FULL_SWEEP_WAVELENGTHS_M = np.array(
    [wavelength_nm * 1e-9 for wavelength_nm in FULL_SWEEP_WAVELENGTHS_NM],
    dtype=float,
)
EV_DESIGN_WAVELENGTHS_NM = FULL_SWEEP_WAVELENGTHS_NM
EV_DESIGN_WAVELENGTHS_M = np.array(
    [wavelength_nm * 1e-9 for wavelength_nm in EV_DESIGN_WAVELENGTHS_NM],
    dtype=float,
)
DEFAULT_DATA_PREFIX = "coarse_default"
EXOSOME_BIOMIMETIC_PRESET_DEFAULT = "biomimetic_corona_nominal"
_BIOMIMETIC_EXOSOME_NAME_PATTERN = re.compile(
    r"^exosome_(?P<preset>.+)_(?P<diameter_nm>\d+)nm$"
)

MATERIAL_DEFAULTS = {
    "gold": {"n_real": 0.164, "n_imag": 2.47},
    "exosome_uniform": {"n_real": 1.38, "n_imag": 0.0},
}


def normalize_material_key(material_key: str) -> str:
    """Map UI-facing material names to internal material keys."""
    if material_key in DISPLAY_TO_MATERIAL_KEY:
        return DISPLAY_TO_MATERIAL_KEY[material_key]
    if material_key in MATERIAL_DEFAULTS:
        return material_key
    raise ValueError(f"Unknown material: {material_key}")


def material_display_name(material_key: str) -> str:
    """Return UI-facing material label."""
    return MATERIAL_KEY_TO_DISPLAY.get(normalize_material_key(material_key), material_key)


def infer_particle_material(particle_name: str) -> str:
    """Infer UI-facing material label from a particle name."""
    if particle_name.startswith("gold_"):
        return "gold"
    if particle_name.startswith("exosome_") or particle_name.startswith("exosome_uniform_"):
        return "exosome"
    return particle_name


def medium_for_material(material_key: str) -> Medium:
    """Resolve the liquid medium used for one particle family."""
    material = infer_particle_material(str(material_key))
    if material == "exosome":
        return PBS_1X
    return WATER


def medium_for_particle_name(particle_name: str) -> Medium:
    """Resolve medium by particle name."""
    return medium_for_material(infer_particle_material(particle_name))


def medium_for_particle(particle: Particle) -> Medium:
    """Resolve medium for a Particle instance."""
    return medium_for_particle_name(particle.name)


def infer_particle_diameter_nm(particle_name: str) -> int | None:
    """Infer diameter in nm from particle name like gold_40nm or exosome_100nm."""
    match = re.search(r"_(\d+)nm(?:_|$)", particle_name)
    if not match:
        return None
    return int(match.group(1))


def infer_biomimetic_exosome_preset_name(particle_name: str) -> str | None:
    """
    Infer the biomimetic exosome preset encoded in a particle name.

    Supported structured names look like:
        exosome_biomimetic_corona_nominal_100nm
        exosome_membrane_only_dim_2021_80nm

    Legacy homogeneous names such as `exosome_100nm` or
    `exosome_uniform_100nm` return None.
    """
    match = _BIOMIMETIC_EXOSOME_NAME_PATTERN.match(str(particle_name))
    if match is None:
        return None
    preset_name = str(match.group("preset"))
    if preset_name == "uniform":
        return None
    preset_catalog = set(list_exosome_model_presets())
    if preset_name in preset_catalog:
        return preset_name
    for catalog_name in sorted(preset_catalog, key=len, reverse=True):
        if preset_name.endswith(f"_{catalog_name}"):
            return catalog_name
    raise ValueError(
        f"Unknown exosome preset encoded in particle name '{particle_name}': "
        f"'{preset_name}'. Available presets: {sorted(preset_catalog)}"
    )


def format_particle_label(material: str, diameter_nm: int | float | None) -> str:
    """Build a compact user-facing particle label."""
    if diameter_nm is None:
        return material
    return f"{material} ({int(round(diameter_nm))} nm)"


def clip_diameter_nm(diameter_nm: int | float | None) -> int:
    """Clip a diameter into the supported dashboard range."""
    if diameter_nm is None:
        diameter_nm = DEFAULT_DASHBOARD_DIAMETER_NM
    return int(np.clip(float(diameter_nm), DIAMETER_RANGE_NM[0], DIAMETER_RANGE_NM[1]))


def snap_diameter_nm(
    diameter_nm: int | float | None,
    step_nm: int = DASHBOARD_DIAMETER_STEP_NM,
) -> int:
    """Snap a diameter to the nearest dashboard-supported step."""
    clipped = clip_diameter_nm(diameter_nm)
    origin = DIAMETER_RANGE_NM[0]
    step_nm = max(1, int(step_nm))
    snapped_index = int(np.floor(((clipped - origin) / step_nm) + 0.5))
    snapped = origin + snapped_index * step_nm
    return int(np.clip(snapped, DIAMETER_RANGE_NM[0], DIAMETER_RANGE_NM[1]))


def diameter_values_between(
    min_nm: int | float,
    max_nm: int | float,
    step_nm: int = DASHBOARD_DIAMETER_STEP_NM,
) -> list[int]:
    """Return dashboard-supported diameter values within an inclusive range."""
    lower_nm = snap_diameter_nm(min_nm, step_nm=step_nm)
    upper_nm = snap_diameter_nm(max_nm, step_nm=step_nm)
    if lower_nm > upper_nm:
        lower_nm, upper_nm = upper_nm, lower_nm
    return list(range(lower_nm, upper_nm + 1, max(1, int(step_nm))))


def particle_from_name(particle_name: str) -> Particle:
    """Rebuild a Particle instance from either legacy or current particle naming."""
    diameter_nm = infer_particle_diameter_nm(particle_name)
    if diameter_nm is None:
        raise ValueError(f"Cannot infer diameter from particle name: {particle_name}")
    preset_name = infer_biomimetic_exosome_preset_name(particle_name)
    if preset_name is not None:
        return make_biomimetic_exosome_particle(
            diameter_nm,
            name=particle_name,
            preset_name=preset_name,
        )
    material = infer_particle_material(particle_name)
    return make_particle(material, diameter_nm, name=particle_name)


def make_particle(
    material_key: str,
    diameter_nm: float,
    *,
    name: str | None = None,
) -> Particle:
    """粒子工厂：从材料类型 + 直径构建 Particle 实例。"""
    internal_key = normalize_material_key(material_key)
    diameter_nm_rounded = int(round(float(diameter_nm)))
    radius_m = float(diameter_nm) * 1e-9 / 2.0
    defaults = MATERIAL_DEFAULTS[internal_key]
    display_key = material_display_name(internal_key)
    return Particle(
        name=name or f"{display_key}_{diameter_nm_rounded}nm",
        radius_m=radius_m,
        n_real=defaults["n_real"],
        n_imag=defaults["n_imag"],
        material_key=internal_key,
        use_material_model=True,
    )


def build_particle_family(material_key: str, diameters_nm: list[int] | range) -> list[Particle]:
    """Build a family of particles with the same material and varying diameters."""
    return [make_particle(material_key, diameter_nm) for diameter_nm in diameters_nm]


def build_biomimetic_exosome_family(
    diameters_nm: list[int] | range,
    *,
    preset_name: str = EXOSOME_BIOMIMETIC_PRESET_DEFAULT,
) -> list[Particle]:
    """Build a family of biomimetic exosome particles over a diameter range."""
    return [
        make_biomimetic_exosome_particle(diameter_nm, preset_name=preset_name)
        for diameter_nm in diameters_nm
    ]


def build_biomimetic_exosome_ensemble_family(
    diameters_nm: list[int] | range,
    *,
    ensemble_name: str = "literature_bounds_2021",
) -> list[Particle]:
    """Build explicit deterministic EV optical ensemble cases over diameters."""
    particles: list[Particle] = []
    for diameter_nm in diameters_nm:
        particles.extend(
            make_biomimetic_exosome_ensemble_particles(
                diameter_nm,
                ensemble_name=ensemble_name,
            )
        )
    return particles


PRECOMPUTE_PROFILES = {
    "quick": {
        "label": "Quick — representative diameters",
        "description": "Fast startup dataset for quick browsing.",
        "particles": (
            build_particle_family("gold", [40])
            + build_particle_family("exosome", [100])
        ),
        "default_tag": "default",
    },
    "full_range": {
        "label": "Full Range — diameters 40-300 nm, step 10 nm",
        "description": (
            "Complete particle sweep for both gold and exosome at 10 nm spacing "
            "across 404/488/532/660 nm."
        ),
        "particles": (
            build_particle_family("gold", FULL_DIAMETER_VALUES_NM)
            + build_particle_family("exosome", FULL_DIAMETER_VALUES_NM)
        ),
        "default_tag": "full_range",
    },
    "full_range_biomimetic_exosome": {
        "label": "Full Range - gold + biomimetic exosome",
        "description": (
            "Complete particle sweep for gold plus the biomimetic core-shell "
            "exosome surrogate at 10 nm spacing across 404/488/532/660 nm."
        ),
        "particles": (
            build_particle_family("gold", FULL_DIAMETER_VALUES_NM)
            + build_biomimetic_exosome_family(FULL_DIAMETER_VALUES_NM)
        ),
        "default_tag": "full_range_biomimetic_exosome",
    },
    "full_range_biomimetic_exosome_with_anchors": {
        "label": "Full Range - gold anchors + biomimetic exosome",
        "description": (
            "Complete particle sweep for gold plus Au20/Au30 anchors and the "
            "biomimetic core-shell exosome surrogate at 10 nm spacing."
        ),
        "particles": (
            build_particle_family("gold", GOLD_ANCHOR_DIAMETER_VALUES_NM)
            + build_particle_family("gold", FULL_DIAMETER_VALUES_NM)
            + build_biomimetic_exosome_family(FULL_DIAMETER_VALUES_NM)
        ),
        "default_tag": "full_range_biomimetic_exosome_with_anchors",
    },
    "ev_design_biomimetic_ensemble_with_anchors": {
        "label": "EV Design - gold anchors + biomimetic ensemble",
        "description": (
            "EV design sweep with Au20/Au30 anchors, gold challenge standards, "
            "and four literature-bounded EV optical presets across 50-150 nm."
        ),
        "particles": (
            build_particle_family("gold", GOLD_ANCHOR_DIAMETER_VALUES_NM)
            + build_particle_family("gold", FULL_DIAMETER_VALUES_NM)
            + build_biomimetic_exosome_ensemble_family(
                EXOSOME_FOCUS_DIAMETER_VALUES_NM,
            )
        ),
        "default_tag": "ev_design_biomimetic_ensemble_with_anchors",
    },
    "exosome_50_150": {
        "label": "Exosome Focus — diameters 50-150 nm, step 10 nm",
        "description": (
            "Focused exosome-only sweep for the 50-150 nm band used to compare "
            "404/488/532/660 nm behavior with higher event counts."
        ),
        "particles": build_particle_family("exosome", EXOSOME_FOCUS_DIAMETER_VALUES_NM),
        "default_tag": "exosome_50_150_focus_404",
    },
}
PRECOMPUTE_PROFILE_DEFAULT = "quick"


def get_precompute_profile(profile_name: str = PRECOMPUTE_PROFILE_DEFAULT) -> dict:
    """Return precompute profile metadata."""
    if profile_name not in PRECOMPUTE_PROFILES:
        raise ValueError(
            f"Unknown precompute profile: {profile_name}. "
            f"Available: {sorted(PRECOMPUTE_PROFILES)}"
        )
    return PRECOMPUTE_PROFILES[profile_name]


def get_precompute_particles(profile_name: str = PRECOMPUTE_PROFILE_DEFAULT) -> list[Particle]:
    """Return particle list for a named precompute profile."""
    return list(get_precompute_profile(profile_name)["particles"])


BASELINE_PARTICLE = make_gold_baseline_particle()

# ============================================================
# 介质
# ============================================================
MEDIUM = WATER

# ============================================================
# 光学系统模板
# ============================================================
OPTICAL_TEMPLATE = OpticalSystem(
    660e-9, 1.0, 300e-9, 700e-9, 300e-9,
    collection_theta_rad=np.pi / 4,
)

# ============================================================
# 模拟配置
# ============================================================
DEFAULT_SIM_CFG = SimulationConfig(
    total_time_s=0.2,
    sampling_rate_Hz=20000.0,
    mean_flow_velocity_m_s=2e-4,
    noise_std=0.01,
    shot_noise_scale=0.001,
    post_readout_noise_std=0.002,
    n_events=100,
    random_seed=42,
    rho=0.5,
    collection_angle_model="channel_diffraction",
    collection_integration_mode="pupil_slit_surrogate",
    collection_sigma_rad=np.deg2rad(10.0),
    collection_phi_sigma_rad=np.deg2rad(14.0),
    slit_phi_limit_rad=np.deg2rad(20.0),
    scattering_projection_mode="parallel",
    pulse_detection_mode="absolute",
    readout_model="lockin_surrogate",
    readout_observable_mode="in_phase",
    lockin_time_constant_s=1.0e-3,
    pod_lockin_frequency_Hz=1200.0,
    nodi_lockin_frequency_Hz=2400.0,
    pod_reference_phase_rad=0.0,
    nodi_reference_phase_rad=0.0,
    pod_to_nodi_crosstalk=0.05,
    nodi_to_pod_crosstalk=0.02,
    normalization_mode="per_wavelength",
    phase_model="relative_surrogate",
    reference_model=DEFAULT_REFERENCE_MODEL,
    reference_route=DEFAULT_REFERENCE_ROUTE,
    reference_calibration_path=REFERENCE_CALIBRATION_PATH,
    reference_spatial_mode="cross_section_surrogate",
    reference_spatial_amplitude_strength=0.35,
    reference_spatial_phase_strength_rad=np.deg2rad(36.0),
    ref_alpha=0.5,
    ref_beta=0.3,
    ref_gamma=1.0,
    coupling_model="gaussian_xy",
    flow_profile_model="rect_series",
    include_diffusion=True,
    diffusion_hindrance_model="anisotropic_tensor_surrogate",
    noise_model="gaussian_plus_drift",
    drift_slope=0.001,
    post_readout_drift_slope=0.0002,
    score_mode="joint",
    joint_alpha=0.6,
)

REFERENCE_MODEL_OPTIONS = [
    "constant",
    "geometry_scaled",
    "channel_angular_surrogate",
    "paper_aligned_phase_filter",
    "tsuyama_bfp_integrated",
]
if REFERENCE_CALIBRATION_PATH:
    REFERENCE_MODEL_OPTIONS.append("calibrated_lookup")
DEFAULT_REFERENCE_MODEL_INDEX = REFERENCE_MODEL_OPTIONS.index(DEFAULT_REFERENCE_MODEL)

# ============================================================
# 扫描网格
# ============================================================
GRID_CONFIGS = {
    "coarse": {
        "width_list_m": np.arange(500e-9, 2001e-9, 500e-9),    # 4 points
        "depth_list_m": np.arange(500e-9, 2001e-9, 500e-9),    # 4 points
        "wavelength_list_m": FULL_SWEEP_WAVELENGTHS_M.copy(),
        "n_events": 30,
    },
    "fine": {
        "width_list_m": np.arange(500e-9, 2001e-9, 100e-9),    # 16 points
        "depth_list_m": np.arange(500e-9, 2001e-9, 100e-9),    # 16 points
        "wavelength_list_m": FULL_SWEEP_WAVELENGTHS_M.copy(),
        "n_events": 10000,
    },
    "focus_50_150": {
        "width_list_m": np.arange(700e-9, 1501e-9, 100e-9),    # 9 points
        "depth_list_m": np.arange(500e-9, 1001e-9, 100e-9),    # 6 points
        "wavelength_list_m": FULL_SWEEP_WAVELENGTHS_M.copy(),
        "n_events": 10000,
    },
    "ev_design": {
        "width_list_m": (
            np.array(
                [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500],
                dtype=float,
            )
            * 1e-9
        ),
        "depth_list_m": (
            np.array(
                [500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500],
                dtype=float,
            )
            * 1e-9
        ),
        "wavelength_list_m": EV_DESIGN_WAVELENGTHS_M.copy(),
        "n_events": 10000,
    },
}

# ============================================================
# 参数说明 — 三层解释模型（定义 / 物理作用 / 对结果影响）
# ============================================================

# 简短版：供 UI 控件 help= tooltip 使用
PARAM_HELP = {
    "rho": "ρ = E_ref / E_sca 强度比。控制干涉增强强度。",
    "ref_alpha": "reference 随 W 的缩放指数 α。",
    "ref_beta": "reference 随 H 的缩放指数 β。",
    "ref_gamma": "reference 随 λ 的缩放指数 γ。",
    "noise_std": "加性高斯噪声标准差。",
    "shot_noise_scale": "与基线强度相关的 pre-readout shot-noise surrogate 系数。",
    "drift_slope": "基线线性漂移斜率（信号单位/秒）。",
    "threshold_sigma": "阈值 = 背景中位数 + N×robust_std。",
    "velocity": "粒子平均流速（mm/s）。",
    "beam_waist_y": "流动方向光束 waist（nm）。",
    "include_diffusion": "是否考虑布朗扩散。",
    "reference_model": "参考场几何模型。",
    "reference_route": "参考场口径：标定主入口、论文对照、工程 fallback 或 legacy debug。",
    "coupling_model": "位置耦合模型。",
    "normalization_mode": "跨波长归一化方式。",
    "noise_model": "噪声模型类型。",
    "readout_model": "检测读出链模型。",
    "readout_observable_mode": "锁相输出取 in-phase 还是 magnitude。",
    "lockin_time_constant_ms": "lock-in 等效时间常数（ms）。",
    "pod_lockin_frequency_Hz": "POD surrogate 的锁相参考频率（Hz）。",
    "nodi_lockin_frequency_Hz": "NODI surrogate 的锁相参考频率（Hz）。",
    "pod_reference_phase_rad": "POD 锁相参考相位（rad）。",
    "nodi_reference_phase_rad": "NODI 锁相参考相位（rad）。",
    "particle_material": "粒子材料类型。",
    "particle_diameter": "粒径（nm，范围 40–300，10 nm 步进）。",
}

# 完整版：三层解释，供"参数解释模式"展开使用
PARAM_HELP_FULL = {
    "rho": """**定义**：ρ = E_ref / E_sca，参考场与散射场的强度比。

**物理作用**：控制干涉增强强度（heterodyne gain）。NODI 的核心检测原理是弱散射场被强参考场放大：S(t) ≈ 2·Re(E_ref · E_sca*)，ρ 直接决定放大倍数。

**对结果影响**：
- ↑ρ → 信号增强（peak height ↑），检出率提高
- 但：对 reference model 假设更敏感，容易产生"假最优"
- **建议**：用于 sensitivity sweep 验证结论稳定性，而非最终定量预测""",

    "ref_alpha": """**定义**：α，reference 场随通道宽度 W 的缩放指数。

**物理作用**：E_ref ∝ (W/W₀)^α。物理上，通道宽度影响衍射光场的空间分布，α 是对这一效应的经验参数化。

**对结果影响**：
- ↑α → W 对最终信号的影响更显著，热图中 W 方向梯度加大
- α=0 时 W 不影响参考场（退化为 constant model 行为）
- **建议**：推荐范围 0.3–0.8，需实验校准""",

    "ref_beta": """**定义**：β，reference 场随通道深度 H 的缩放指数。

**物理作用**：E_ref ∝ (H/H₀)^β。通道深度影响光与粒子的纵向交互长度。

**对结果影响**：
- ↑β → H 对参考场影响更大，热图中 H 方向梯度加大
- β=0 时 H 不影响参考场
- **建议**：推荐范围 0.2–0.5，需实验校准""",

    "ref_gamma": """**定义**：γ，reference 场随波长 λ 的缩放指数。

**物理作用**：E_ref ∝ (λ₀/λ)^γ。短波长衍射更强，γ 控制这一波长依赖性的强度。

**对结果影响**：
- ↑γ → 短波长（488nm）的参考场更强，可能翻转波长排名
- γ=0 时波长不影响参考场
- **建议**：推荐范围 0.5–1.5""",

    "noise_std": """**定义**：σ_noise，加性高斯白噪声的标准差。

**物理作用**：模拟检测器暗噪声和散粒噪声的综合效应。直接叠加在干涉信号上。

**对结果影响**：
- ↑noise_std → 信噪比下降 → 阈值检测中峰更容易被淹没 → detection_rate ↓
- 小粒子（弱散射）对噪声更敏感
- **建议**：典型范围 0.005–0.05，与实际检测系统匹配""",

    "shot_noise_scale": """**定义**：与基线强度相关的 pre-readout shot-noise surrogate 系数。

**物理作用**：raw 检测层的波动不再完全固定，而是随 `I_baseline` / `I_det` 的平方根放大。参考场越强，原始光子统计波动也越大。

**对结果影响**：
- ↑shot_noise_scale → 在强参考场下 raw 层噪声更显著
- 低折射率、低 `E_sca` 的 case 更容易被这类基线相关波动淹没
- **建议**：把它理解成“与基线绑定的 shot-noise surrogate”，与固定 `noise_std` 配合使用""",

    "drift_slope": """**定义**：基线线性漂移斜率（信号单位/秒）。

**物理作用**：模拟低频背景漂移（如温度波动、光源不稳定）。使阈值估计偏移，增加检测难度。

**对结果影响**：
- ↑drift_slope → robust threshold 估计偏高 → 漏检增加
- 主要影响长时间采集的事件
- **建议**：0 表示无漂移，典型 0.0005–0.005""",

    "threshold_sigma": """**定义**：阈值倍数 N，threshold = median(background) + N × robust_std。

**物理作用**：控制检测灵敏度与误检率的权衡。基于 MAD（中位绝对偏差）的稳健统计。

**对结果影响**：
- ↑N → 更保守：误检（false positive）↓ 但漏检（false negative）↑
- ↓N → 更灵敏：检出率↑ 但噪声峰也可能被误判
- **建议**：3–5σ 为灵敏区，5–8σ 为保守区""",

    "velocity": """**定义**：粒子平均流速 v（mm/s）。

**物理作用**：决定粒子穿过光束的时间 t_transit ≈ beam_waist_y / v。直接影响脉冲宽度。

**对结果影响**：
- ↑v → 峰越窄 → 停留时间越短 → 采样点越少 → 可能遗漏窄峰
- ↓v → 峰越宽 → 信号积分更多 → 但扩散影响增大
- **建议**：0.1–0.5 mm/s 为典型微流控范围""",

    "beam_waist_y": """**定义**：流动方向（y）的光束腰斑半径 w_y（nm）。

**物理作用**：决定粒子被照亮的空间范围。与流速共同决定脉冲宽度：t_peak ≈ w_y / v。

**对结果影响**：
- ↑w_y → 粒子被照亮时间越长 → 峰越宽 → 信噪比可能↑（更多积分）
- ↓w_y → 峰更尖锐但更难检测
- **建议**：300–1000nm 为典型范围""",

    "include_diffusion": """**定义**：是否启用布朗扩散运动模型。

**物理作用**：小粒子受热运动影响，轨迹随机偏移。扩散系数 D = kT/(6πηa)，粒径越小扩散越强。

**对结果影响**：
- 开启 → 峰高/峰宽分布更宽（更接近真实），CV↑
- 关闭 → 纯对流模型，事件间一致性更高但不真实
- **建议**：除基准测试外应始终开启""",

    "reference_model": """**定义**：参考场的几何模型选择。

**物理作用**：
- `constant`：E_ref = ρ（常数），通道几何仅通过位置采样影响结果
- `geometry_scaled`：E_ref = ρ × (W/W₀)^α × (H/H₀)^β × (λ₀/λ)^γ，经验 surrogate model
- `channel_angular_surrogate`：先生成最小通道衍射角谱场，再用与 E_sca 相同的 pupil/slit 探测算子积分
- `paper_aligned_phase_filter`：Tsuyama 2020 对照模式，depth 只通过相位延迟进入，不再额外乘 depth aperture 项
- `calibrated_lookup`：从 blank-channel 标定表读取或插值 `A_ref / phi_ref / g_ref`

**对结果影响**：
- `constant` → 热图中 W/H 的影响仅来自散射 + 耦合，不含参考场贡献
- `geometry_scaled` → W/H/λ 同时影响散射和参考场，更接近真实但依赖经验参数
- `channel_angular_surrogate` → 在没有标定表时，把参考场从“自由幂律”推进成“通道角谱场 + 探测算子”的最小物理 surrogate
- `paper_aligned_phase_filter` → 更适合审查 Tsuyama 论文中 depth 主要作为 phase thickness 的语义是否会改变宽深趋势
- `calibrated_lookup` → 若标定表可靠，默认优先使用，能显著减少经验幂律带来的假最优风险
- **建议**：有真实标定表时默认使用 calibrated_lookup；否则优先使用 channel_angular_surrogate。若要审查 Tsuyama 2020 的 width/depth 语义，再加跑 paper_aligned_phase_filter 对照""",

    "coupling_model": """**定义**：粒子位置到检测效率的耦合函数。

**物理作用**：
- `constant`：无论粒子在通道哪个位置，耦合效率相同
- `gaussian_xy`：偏离通道中心时效率下降，f = exp(-(x/w_cx)² - (z/w_cz)²)

**对结果影响**：
- `gaussian_xy` → 边缘粒子信号减弱 → 峰高分布更宽 → CV↑
- `constant` → 所有位置等权，CV↓ 但不真实
- **建议**：默认 gaussian_xy""",

    "readout_model": """**定义**：原始含噪干涉信号如何映射成最终用于阈值检测的读出轨迹。

**物理作用**：
- `raw`：不经过读出链，直接在原始含噪 trace 上检测
- `lockin_surrogate`：先做 POD/NODI 两路 surrogate 分解，再加入简化串扰，最后在 NODI 读出通道上检测

**对结果影响**：
- `raw` → 最接近旧版模型，响应最快，但更乐观
- `lockin_surrogate` → 会平滑脉冲、压制漂移、也可能让串扰重新把部分背景带回检测通道
- **建议**：dashboard 默认使用 lockin_surrogate；只有做旧结果对照时才切 raw""",

    "lockin_time_constant_ms": """**定义**：lock-in surrogate 的一阶低通时间常数（ms）。

**物理作用**：控制读出链对快速脉冲和慢背景的分离强度。时间常数越大，POD/NODI 两路都更平滑。

**对结果影响**：
- ↑时间常数 → 脉冲更圆滑，峰值更低，阈值更稳定
- ↓时间常数 → 更接近原始时域，脉冲更尖锐但更容易带入高频噪声
- **建议**：Tsuyama 论文给的是 `1–2 ms` 范围；当前默认取机器可直接设置的 `1 ms`，再看结论对 `1 ms / 2 ms` 是否敏感""",

    "pod_lockin_frequency_Hz": """**定义**：POD surrogate 通道的锁相参考频率（Hz）。

**物理作用**：POD 通道会先把 `pod_source` 放到这个 carrier 上，再用同频参考解调和低通；与 NODI 频率拉开时，跨通道泄漏会自然受到频率失配抑制。

**对结果影响**：
- 与 NODI 频率越接近，频率选择性越弱，泄漏更容易进入另一通道
- 与 NODI 频率拉开，POD / NODI 两路分离更干净
- **建议**：把它看成最小 lock-in 频率选择 surrogate，而不是完整电子学标定""",

    "nodi_lockin_frequency_Hz": """**定义**：NODI surrogate 通道的锁相参考频率（Hz）。

**物理作用**：决定检测通道在最小 lock-in surrogate 里的频率参考，并与 `pod_lockin_frequency_Hz` 一起决定 cross-demod leakage 的衰减程度。

**对结果影响**：
- 越接近 POD 频率，cross-demod leakage 越大
- 频率分离越明显，NODI 读出越像“频率选择后的检测通道”
- **建议**：默认保持明显频率分离，先看趋势，再在重算后做参数校准""",

    "normalization_mode": """**定义**：散射场归一化方式，影响同一波长内几何排序；不能单独解锁真实跨波长激光选择。

**物理作用**：
- `per_wavelength`：每个 λ 用该波长下 baseline 粒子的 E_sca 独立归一化
- `global_single_lambda`：所有 λ 共用 660nm 的 E_sca_ref

**对结果影响**：
- `per_wavelength` → 同一 λ 内 W/H 排序更稳，推荐默认；跨 λ 只能解释为 normalized simulator trend
- `global_single_lambda` → 短波长散射更强但基准不变 → 存在"锚定偏置"
- **建议**：默认使用 per_wavelength；若要判断 488/532/660 nm 真实谁更优，需要 detector responsivity、laser power、objective throughput、reference scaling 和 noise calibration 的统一口径""",

    "noise_model": """**定义**：噪声生成模型。

**物理作用**：
- `gaussian`：纯高斯白噪声，模拟检测器随机噪声
- `gaussian_plus_drift`：白噪声 + 线性基线漂移，更接近真实系统

**对结果影响**：
- `gaussian` → 阈值估计稳定，检出率更高
- `gaussian_plus_drift` → 阈值可能偏移 → 对长采集时间更敏感
- **建议**：建模时用 gaussian_plus_drift，对照实验用 gaussian""",

    "particle_material": """**定义**：粒子材料类型。

**物理作用**：
- `gold`：等离子体共振金属纳米颗粒。n ≈ 0.16+2.47i（660nm），强散射 + 强吸收，plasmon enhanced
- `exosome`：弱散射生物颗粒。n ≈ 1.38+0i，近似介电体，散射极弱

**对结果影响**：
- gold → 散射信号强，容易检测，用于系统验证和优化
- exosome → 接近检测极限，真正考验系统灵敏度
- **注意**：材料与粒径是强耦合物理问题——改变粒径不仅改大小，不同材料的散射机制完全不同""",

    "particle_diameter": """**定义**：粒径 d（nm），当前 dashboard 使用 `40–300 nm`、`10 nm` 步进。

**物理作用**：散射截面 Csca ∝ a⁶（小粒子 Rayleigh 极限）。size parameter x = πd·n_m/λ 决定散射 regime：
- x ≪ 1：Rayleigh regime，散射 ∝ d⁶/λ⁴
- x ~ 1：Mie 过渡区，出现共振结构
- x ≫ 1：几何光学区

**对结果影响**：
- 粒径翻倍 → 散射增强约 64 倍（Rayleigh 极限下）
- 小粒子（<80nm）对噪声极敏感，detection_rate 急剧下降
- **建议**：40–100nm 用于测试灵敏度极限，100–300nm 用于验证系统""",
}

# ============================================================
# 粒子材料物理描述（供 UI 显示）
# ============================================================
MATERIAL_PHYSICS_LABELS = {
    "gold": "Gold — 等离子体颗粒（plasmon resonance，强散射+吸收）",
    "exosome": "Exosome — 弱散射生物颗粒（dielectric，接近检测极限）",
}


def compute_particle_physics_status(material_key: str, diameter_nm: float,
                                     wavelength_nm: float = 660.0) -> dict:
    """
    计算当前粒子的实时物理状态，用于 UI 显示。

    Returns:
        dict with keys:
            size_parameter: x = 2πa·n_m/λ
            scattering_regime: str ("Rayleigh" / "Rayleigh–Mie 过渡" / "Mie")
            scattering_scaling: str (近似缩放关系描述)
            material_type: str (物理类型描述)
    """
    n_m = 1.33  # water refractive index (approximately constant in visible)
    a_m = diameter_nm * 1e-9 / 2.0
    wavelength_m = wavelength_nm * 1e-9
    x = 2.0 * np.pi * a_m * n_m / wavelength_m

    if x < 0.3:
        regime = "Rayleigh"
        scaling = "Csca ~ a⁶/λ⁴（Rayleigh 极限，散射随粒径急剧变化）"
    elif x < 1.5:
        regime = "Rayleigh–Mie 过渡区"
        scaling = "Csca ~ a⁶（近似成立，但开始偏离 Rayleigh 极限）"
    else:
        regime = "Mie"
        scaling = "完整 Mie 级数求解（出现共振结构，不可简单近似）"

    material_display = material_display_name(material_key)

    if material_display == "gold":
        mat_type = "Plasmon enhanced — 金属纳米颗粒的等离子体共振显著增强散射和吸收"
    elif material_display == "exosome":
        mat_type = "Dielectric — 低折射率对比度生物颗粒，散射极弱，依赖 reference 增强"
    else:
        mat_type = "未知材料类型"

    return {
        "size_parameter": x,
        "scattering_regime": regime,
        "scattering_scaling": scaling,
        "material_type": mat_type,
    }

def get_score_explanation(case_data: dict) -> dict:
    """
    自动分析一个 case 的高分/低分原因。

    Returns:
        dict with keys:
            dominant_factor: str ("scattering" / "reference" / "coupling" / "balanced")
            explanation: str (人类可读的解释)
            E_sca_E_ref_ratio: float (散射场/参考场比值)
            trust_level: str ("high" / "medium" / "low")
            trust_reason: str
    """
    physics = case_data.get("physics", {})
    summary = case_data.get("summary", {})

    E_sca = physics.get("E_sca_at_det", 0) or 0
    E_sca_ref = physics.get("E_sca_ref", 1) or 1
    E_sca_norm = physics.get("E_sca_normalized") or (E_sca / E_sca_ref if E_sca_ref else 0)
    g_ref = physics.get("g_ref", 1) or 1
    A_ref = physics.get("A_ref", 0) or 0
    det_rate = summary.get("detection_rate", 0)
    mean_h = summary.get("mean_peak_height", 0)
    cv = summary.get("std_peak_height", 0) / mean_h if mean_h > 0 else float("inf")

    # E_sca / E_ref ratio (unnormalized, for physical insight)
    ratio = abs(E_sca_norm / A_ref) if A_ref > 0 else float("inf")

    # Determine dominant factor
    if A_ref > 5 and E_sca_norm < 0.5:
        dominant = "reference"
        expl = (f"此设计高分主要由 reference 增强主导（A_ref={A_ref:.2f}），"
                f"而非散射本身强（E_sca_norm={E_sca_norm:.4f}）。"
                f"通道几何放大了干涉增益。")
    elif E_sca_norm > 2 and A_ref < 3:
        dominant = "scattering"
        expl = (f"此设计高分主要由粒子散射强度主导（E_sca_norm={E_sca_norm:.4f}），"
                f"reference 贡献相对较小（A_ref={A_ref:.2f}）。")
    elif g_ref > 2:
        dominant = "coupling"
        expl = (f"几何因子 g_ref={g_ref:.2f} 较大，说明通道几何对参考场有显著增强。"
                f"散射和参考场共同贡献了最终信号。")
    else:
        dominant = "balanced"
        expl = (f"散射（E_sca_norm={E_sca_norm:.4f}）和参考场（A_ref={A_ref:.2f}）"
                f"贡献相对均衡。")

    # Trust level assessment
    if det_rate > 0.8 and cv < 0.3 and A_ref < 20:
        trust = "high"
        trust_reason = "检出率高、CV低、参考场在合理范围 → 物理主导，结果可信"
    elif det_rate > 0.5 and cv < 0.5:
        trust = "medium"
        trust_reason = "检出率和稳定性尚可，但可能受模型参数（ρ, α/β/γ）影响"
    else:
        trust = "low"
        if det_rate < 0.3:
            trust_reason = "检出率极低 → 信号可能在噪声以下，结果不可靠"
        elif cv > 0.5:
            trust_reason = "CV 过高 → 信号不稳定，受噪声/扩散/normalization 影响大"
        elif A_ref > 20:
            trust_reason = "A_ref 极大 → reference model 主导结果，对经验参数极敏感"
        else:
            trust_reason = "综合指标不佳，建议检查参数合理性"

    return {
        "dominant_factor": dominant,
        "explanation": expl,
        "E_sca_E_ref_ratio": ratio,
        "trust_level": trust,
        "trust_reason": trust_reason,
    }
