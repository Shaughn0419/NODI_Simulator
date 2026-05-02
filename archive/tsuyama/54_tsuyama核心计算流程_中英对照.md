# Tsuyama 核心计算流程（中英对照，工程对照校核版）

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 目的 / Purpose：在前一版论文总结基础上，进一步**对照当前工程中 Tsuyama 模型相关函数实现**，把“论文物理链”“工程默认主线”“paper-aligned 对齐口径”三层语义拆开，避免把代理模型误写成论文原公式。
>
> 结论先行 / Key conclusion first：
>
> 1. 工程中的 **NODI 主链** 已经有比较完整的事件级实现：`参考场 -> 本征散射 -> 轨迹/照明/相位 -> 干涉 -> 读出 -> 阈值/脉冲 -> 统计`。
> 2. 工程中的 **POD 主链并不是完整的 2019/2020 热扩散物理实现**；当前主要是读出链中的 POD-like 频段代理。`paper_aligned_profiles.py` 也明确把真正的 `pod_2019_2020` 标成 unavailable。
> 3. 因此本文档必须区分：
>    - `论文物理链 / paper physics`
>    - `工程默认主线 / engineering mainline`
>    - `论文对齐配置 / paper-aligned profiles`

---

## 0. 总览 / Overview

### 0.1 三层口径先分清 / Three Semantic Layers

- `论文物理链 / Paper physics`：论文中真正写出的物理公式和实验解释。
- `工程默认主线 / Engineering mainline`：当前默认配置下真正执行的函数链。默认值主要来自 `data_objects.py`：
  - `phase_model = "relative_surrogate"`
  - `reference_model = "channel_angular_surrogate"`
  - `path_opd_model = "single_pass"`
  - `pulse_detection_mode = "absolute"`
  - `detection_decision_mode = "single_channel"`
  - `readout_observable_mode = "in_phase"`
  - `lockin_time_constant_s = 1.0e-3`
  - `pod_lockin_frequency_Hz = 1200`
  - `nodi_lockin_frequency_Hz = 2400`
  - `illumination_mode = "overfill"`
- `论文对齐配置 / Paper-aligned profiles`：`paper_aligned_profiles.py` 中给出的对照通道。
  - `diffraction_2020`
  - `nodi_2022`
  - `paired_2024`
  - `pod_2019_2020`：**明确不可用**，原因是热源、热扩散、溶剂 `dn/dT`、玻璃贡献、最佳 `PD` 等关键 POD 物理尚未实现。

### 0.2 一条完整计算链 / One Full Calculation Chain

论文层的最简公式链可以写成：

$$
\theta
\;\to\;
E_D
\;\to\;
\begin{cases}
\Delta PD & \text{(POD)} \\
E_S & \text{(NODI)}
\end{cases}
\;\to\;
I_{\mathrm{det}} = |E_D + E_S|^2
\;\to\;
\text{readout}
\;\to\;
\text{pulse features}
\;\to\;
\text{count / classify}
$$

工程默认主线真正执行的是更细的版本：

$$
\theta
\;\to\;
E_{\mathrm{ref,base}}
\;\to\;
E_{\mathrm{ref}}(t)
\;\to\;
\frac{dC_{\mathrm{sca}}}{d\Omega}
\;\to\;
E_{\mathrm{sca,unit}}
\;\to\;
E_{\mathrm{sca}}(t)
\;\to\;
I_{\mathrm{det}}(t)
\;\to\;
s_{\mathrm{raw}}(t)
\;\to\;
s_{\mathrm{readout}}(t)
\;\to\;
\text{threshold / peaks}
\;\to\;
\text{pairing / summary}
$$

这里每一层对应的工程函数分别是：

- `compute_reference_field`
- `compute_reference_field_trace`
- `compute_intrinsic_scattering`
- `compute_illumination_envelope`
- `compute_scattering_field_trace`
- `generate_interferometric_trace`
- `apply_readout_chain`
- `estimate_threshold_stats_robust`
- `extract_pulse_features`
- `simulate_one_event`

### 0.3 为什么要先这样分层 / Why This Separation Matters

如果不先区分三层口径，就会犯两个常见错误：

1. 把工程里的 `channel_angular_surrogate`、`lockin_surrogate`、`relative_surrogate` 误当成论文原公式。
2. 把当前 POD 读出代理误当成已经实现了 2019/2020 论文中的热扩散 POD 物理。

下面每一节都会同时写：

- `论文公式 / Paper formula`
- `工程实现 / Implementation mapping`
- `承上启下 / Why this step is needed next`
- `论文支撑 / Paper support`

---

## 1. 空白通道衍射与参考场 / Blank-Channel Diffraction and Reference Field

### 1.1 论文中的基础起点 / Paper Starting Point

2020 diffraction 论文把 nanochannel 看成相位滤波器。通道内外的光程差写成相位差：

$$
\theta = \frac{2\pi (n_s - n_g)d}{\lambda}.
$$

其中：

- $n_s$：通道内介质折射率 / solvent refractive index
- $n_g$：玻璃折射率 / glass refractive index
- $d$：通道深度 / channel depth
- $\lambda$：探测光波长 / probe wavelength

若入射场是通道平面上的高斯场

$$
f(x',y') \propto
\exp\!\left(
-\frac{x'^2+y'^2}{\omega_z^2}
\right)
\exp\!\left(i\Phi_{\mathrm{GB}}(x',y',z_1)\right),
$$

则相位滤波器可以写为

$$
t(x',y') =
\begin{cases}
e^{i\theta}, & a-l \le x' \le a+l,\\
1, & \text{otherwise}.
\end{cases}
$$

通道后场为

$$
E_{\mathrm{after}}(x',y') = f(x',y')\, t(x',y').
$$

再经透镜传播到后焦面：

$$
g(x,y) = \mathcal{F}\!\left\{E_{\mathrm{after}}(x',y')\right\},
\qquad
I(x,y) = |g(x,y)|^2.
$$

2020 diffraction 论文把强度进一步整理为：

$$
I(x,y)
=
I_0(x,y)
\Bigl[
1 + 2|u(x,l)|^2(1-\cos\theta)
- `2 Re{u(x,l)} * (1-cos(theta))`
- 2\operatorname{Im}[u(x,l)]\sin\theta
\Bigr].
$$

### 1.2 推导逻辑 / Derivation Logic

这一步的逻辑是：

1. 激光先到达空白通道 / the laser first illuminates a blank channel.
2. 通道与玻璃的折射率不同，所以在通道区域累积附加光程 / the groove region accumulates extra optical path.
3. 光程差转成相位差 $\theta$ / optical path difference becomes phase delay.
4. 因而通道等效为薄相位滤波器 / the channel acts as a thin phase filter.
5. 相位滤波后的场在后焦面产生衍射角谱 / the filtered field generates a diffraction angular spectrum.
6. 这个角谱经过收集口径后，才成为后面 NODI 要用的参考场 / after collection, this becomes the usable reference field.

### 1.3 工程默认主线怎么实现 / How the Engineering Mainline Implements It

当前工程的 `compute_reference_field` 并不直接求 Fresnel-Kirchhoff 全积分，而是走：

$$
\theta
\;\to\;
\text{channel diffraction angular surrogate}
\;\to\;
\text{collection operator collapse}
\;\to\;
g_{\mathrm{ref}}
\;\to\;
A_{\mathrm{ref}} = \rho\, g_{\mathrm{ref}}
\;\to\;
E_{\mathrm{ref}} = A_{\mathrm{ref}} e^{i\phi_{\mathrm{ref}}}.
$$

更具体地说：

1. 在 `_channel_diffraction_field_surrogate(...)` 里先计算

$$
\theta_{\mathrm{delay}}
=
\frac{2\pi |n_g-n_s| d}{\lambda}.
$$

2. 若使用 `paper_aligned_phase_filter`，工程强制采用更接近论文的语义：

$$
E_{\mathrm{ang}}(\theta,\phi)
\propto
\left|\operatorname{sinc}\!\left(\frac{W k_x}{2\pi}\right)\right|
\exp\!\left(
i\left(\phi_0+\frac{\theta_{\mathrm{delay}}}{2}+\phi_{\pi\text{-jump}}\right)
\right).
$$

并且**不再引入深度方向的 `sinc(Hk_z/2\pi)` 孔径项**。这正是工程里专门为 2020 diffraction 对齐而保留的模式。

3. 若使用默认主线 `channel_angular_surrogate`，则额外加入工程代理项：

$$
E_{\mathrm{ang}}^{\mathrm{eng}}
\propto
\left|\operatorname{sinc}\!\left(\frac{W k_x}{2\pi}\right)\right|
\left|\operatorname{sinc}\!\left(\frac{H k_z}{2\pi}\right)\right|
e^{i\phi_{\mathrm{eng}}(\theta,\phi)}.
$$

这里的深度 `sinc` 项和附加相位倾斜项是**工程代理，不是论文原式**。

4. 角谱随后被 `collapse_angular_field_with_operator(...)` 收集到探测口径中，得到检测到的参考复振幅 `detected`。再对一个基准通道归一化：

$$
g_{\mathrm{ref}}
=
\frac{|E_{\mathrm{detected}}|}{|E_{\mathrm{baseline}}|},
\qquad
A_{\mathrm{ref}} = \rho\, g_{\mathrm{ref}},
\qquad
\phi_{\mathrm{ref}} = \arg(E_{\mathrm{detected}}).
$$

5. 在 `compute_reference_field_trace(...)` 中，工程还把 case-level 的参考场推进成 event-level 的参考轨迹：

$$
A_{\mathrm{ref}}(t)
=
A_{\mathrm{ref,base}} \cdot a_{\mathrm{spatial}}(x(t),z(t)),
$$

$$
\phi_{\mathrm{ref}}(t)
=
\phi_{\mathrm{ref,base}} + \phi_{\mathrm{spatial}}(x(t),z(t)),
$$

$$
E_{\mathrm{ref}}(t)
=
A_{\mathrm{ref}}(t)e^{i\phi_{\mathrm{ref}}(t)}.
$$

### 1.4 承上启下 / Why This Step Feeds the Next One

这一步的输出不是一个“背景常数”，而是后面干涉层必须要用的复参考场：

$$
E_{\mathrm{ref}}(t).
$$

后面所有 NODI 干涉项都要依赖它：

$$
I_{\mathrm{int}}(t) \sim 2\operatorname{Re}\!\left(E_{\mathrm{ref}}(t) E_{\mathrm{sca}}^*(t)\right).
$$

没有参考场，NODI 的放大优势就不存在。

### 1.5 论文支撑 / Paper Support

- `2020 diffraction`：Eq. (3)-(4), Eq. (9)，phase filter 与后焦面强度。
- `2019 POD`：空白通道的折射率差先形成衍射，再作为后续 POD/NODI 的检测基础。

---

## 2. 照明包络与过焦时间 / Illumination Envelope and Transit Window

### 2.1 这一步为什么必须单独写 / Why This Step Must Be Explicit

论文在叙述中经常直接从“颗粒散射”跳到“干涉读出”，但工程实现里中间还有一个必要层：**颗粒到底在焦区里看到怎样的场幅、持续多久、相位怎样变化**。这层由 `compute_illumination_envelope` 给出。

### 2.2 工程中的基础公式 / Engineering Formulas

工程里先定义高斯照明强度包络：

$$
I_{\mathrm{inc}}(x,y,z)
=
I_0
\exp\!\left(
-2\frac{(x-x_f)^2}{w_x^2}
-2\frac{(y-y_f)^2}{w_y^2}
-2\frac{(z-z_f)^2}{w_z^2}
\right).
$$

但真正进入散射场幅的是**场包络**而不是强度：

$$
A_{\mathrm{env}}
=
\sqrt{\frac{I_{\mathrm{inc}}}{I_0}}
=
\exp\!\left(
-\frac{(x-x_f)^2}{w_x^2}
-\frac{(y-y_f)^2}{w_y^2}
-\frac{(z-z_f)^2}{w_z^2}
\right).
$$

这点很关键，因为散射场幅应与入射场幅线性相乘，而不是与强度直接相乘。

### 2.3 `overfill` 模式的含义 / Meaning of the `overfill` Mode

当前默认 `illumination_mode = "overfill"`，它对应 Tsuyama 2022 中“光斑大于通道宽度”的实验语义。工程上的处理是：

- `x/z` 横截面上的照明不再强烈惩罚边缘路径
- 但 `y` 方向穿过焦区的时间窗仍然保留

因此默认主线近似为：

$$
A_{\mathrm{env}}^{\mathrm{overfill}}(t)
\approx
\exp\!\left(
-\frac{(y(t)-y_f)^2}{w_y^2}
\right),
$$

而不是全三维都严格衰减。

### 2.4 焦区相位代理 / Beam-Phase Surrogate

工程还给了一个最小波前相位代理：

$$
\phi_{\mathrm{gouy}}(t)
=
\arctan\!\left(\frac{y(t)-y_f}{z_R}\right),
$$

$$
\phi_{\mathrm{curv}}(t)
=
\frac{1}{2}k_m r_\perp^2 \frac{1}{R(y)},
$$

$$
\phi_{\mathrm{beam}}(t)
=
\phi_{\mathrm{gouy}}(t)+\phi_{\mathrm{curv}}(t).
$$

### 2.5 承上启下 / Why This Step Feeds the Next One

这一层把“本征散射能力”转换成“某条真实轨迹上实际能被激发出的散射场包络”：

$$
E_{\mathrm{sca,unit}}
\;\to\;
A_{\mathrm{env}}(t)\,E_{\mathrm{sca,unit}}.
$$

同时，它还给出了后面读出链要用的过焦时间尺度 `transit_time_s`。这会影响 NODI 通道的带宽代理增益。

### 2.6 论文支撑 / Paper Support

- `2022 NODI`：光斑大于通道、不同颗粒接收到近似一致照明。
- `2024 POD+NODI`：毫秒级过焦事件与锁相时间常数/频率窗口相关。

---

## 3. 本征散射：Mie 量先算出来 / Intrinsic Scattering: First Compute the Mie Quantities

### 3.1 基础公式 / Basic Mie Formulas

对球形颗粒，先定义：

$$
x = \frac{2\pi n_m a}{\lambda},
\qquad
m = \frac{\tilde n_p}{n_m},
\qquad
k_m = \frac{2\pi n_m}{\lambda}.
$$

其中：

- $x$：尺寸参数 / size parameter
- $m$：相对复折射率 / relative complex refractive index
- $\tilde n_p$：颗粒复折射率 / particle complex refractive index

Mie 系数为：

$$
a_n,\; b_n.
$$

工程里的 `mie_efficiencies_from_coefficients(...)` 采用标准公式：

$$
Q_{\mathrm{ext}}
=
\frac{2}{x^2}
\sum_{n=1}^{\infty}
(2n+1)\operatorname{Re}(a_n+b_n),
$$

$$
Q_{\mathrm{sca}}
=
\frac{2}{x^2}
\sum_{n=1}^{\infty}
(2n+1)\left(|a_n|^2+|b_n|^2\right).
$$

从而得到

$$
C_{\mathrm{sca}} = Q_{\mathrm{sca}} \pi a^2,
\qquad
C_{\mathrm{ext}} = Q_{\mathrm{ext}} \pi a^2.
$$

角向散射振幅函数满足：

$$
S_1(\theta)
=
\sum_n \frac{2n+1}{n(n+1)}
\left[a_n\pi_n(\cos\theta)+b_n\tau_n(\cos\theta)\right],
$$

$$
S_2(\theta)
=
\sum_n \frac{2n+1}{n(n+1)}
\left[a_n\tau_n(\cos\theta)+b_n\pi_n(\cos\theta)\right].
$$

对应的微分散射截面为：

$$
\frac{dC_{\mathrm{sca}}}{d\Omega}
=
\frac{|S_1|^2+|S_2|^2}{2k_m^2}.
$$

### 3.2 为什么要从截面转到场幅 / Why We Must Convert Cross Section to Field Amplitude

NODI 真正进入探测器的是干涉项，而不是纯强度项。干涉项需要场幅：

$$
I_{\mathrm{int}} \sim E_D E_S.
$$

而纯散射给出的是强度量：

$$
I_{\mathrm{sca}} \propto |E_S|^2.
$$

所以必须经过：

$$
\frac{dC_{\mathrm{sca}}}{d\Omega}
\;\to\;
E_{\mathrm{sca,unit}}
\propto
\sqrt{\frac{dC_{\mathrm{sca}}}{d\Omega}}.
$$

工程中的 `compute_intrinsic_scattering(...)` 正是这样定义：

$$
E_{\mathrm{sca,unit}} = \sqrt{\frac{dC_{\mathrm{sca}}}{d\Omega}}.
$$

返回键名就是 `Esca_unit_amp`。

### 3.3 这里“只到哪一步”为止 / Where This Layer Stops

这里要特别小心：`compute_intrinsic_scattering(...)` 只给出**颗粒本征光学散射能力**，还没有把以下因素乘进去：

- 照明包络 / illumination envelope
- 轨迹位置 / particle trajectory
- 收集耦合 / spatial coupling
- 相位路径差 / phase/path surrogate
- 参考场干涉 / interference with channel reference

也就是说，这一层的输出还只是：

$$
E_{\mathrm{sca,unit}}
$$

而不是最终的

$$
E_{\mathrm{sca}}(t).
$$

### 3.4 承上启下 / Why This Step Feeds the Next One

这一步把“粒子材料和尺寸信息”编码进一个 detector-angle 的散射振幅代理里。后面真正的时域散射场会把它升级为：

$$
E_{\mathrm{sca,unit}}
\;\to\;
A_{\mathrm{env}}(t)\, f_{\mathrm{coupling}}(t)\, E_{\mathrm{sca,unit}}\, e^{i\phi(t)}
\;\to\;
E_{\mathrm{sca}}(t).
$$

### 3.5 论文支撑 / Paper Support

- `2022 NODI`：Mie theory、多波长散射比、`sqrt(pure scattering)` 进入干涉分析。
- `2022 NODI` 引言：纯散射近似 $d^6$，干涉信号近似 $d^3$。

---

## 4. 时域散射场：把本征散射推进到事件轨迹上 / Time-Domain Scattering Field Along a Particle Trajectory

### 4.1 工程的核心组合公式 / Core Engineering Formula

`compute_scattering_field_trace(...)` 的设计目标非常明确：

$$
E_{\mathrm{sca}}(t)
=
A_{\mathrm{env}}(t)\,
f_{\mathrm{coupling}}(t)\,
E_{\mathrm{sca,unit}}\,
e^{i\phi_{\mathrm{sca}}(t)}.
$$

把振幅单独拆开写就是：

$$
A_{\mathrm{sca}}(t)
=
A_{\mathrm{env}}(t)\,
f_{\mathrm{coupling}}(t)\,
\left|E_{\mathrm{sca,unit}}\right|.
$$

### 4.2 振幅为什么这样乘 / Why the Amplitude Is Built This Way

这三个因子分别代表：

- $A_{\mathrm{env}}(t)$：粒子此刻位于焦区什么位置，看到多强的入射场 / how strongly the particle is illuminated at that moment
- $f_{\mathrm{coupling}}(t)$：即使产生了散射，探测器/口径是否高效收进来 / how efficiently the scattered field is coupled into detection
- $\left|E_{\mathrm{sca,unit}}\right|$：颗粒本身在该角度、本波长、该材料下的本征散射能力 / intrinsic optical scattering strength

因此它不是一个随意的经验乘法，而是把三个物理来源分层相乘。

### 4.3 相位代理 / Phase Surrogate

默认主线 `phase_model = "relative_surrogate"`。工程把散射相位写成：

$$
\phi_{\mathrm{sca}}(t)
=
\phi_{\mathrm{unit}}
+ \phi_{\mathrm{beam,eff}}(t)
+ \phi_{\mathrm{path},x}(t)
+ \phi_{\mathrm{path},z}(t)
+ \phi_{\mathrm{focus}}(t).
$$

其中：

$$
\phi_{\mathrm{path},x}(t)
=
k_m \bigl(x(t)-x_f\bigr)\sin\theta_{\mathrm{det}},
$$

$$
\phi_{\mathrm{path},z}(t)
=
\gamma_z\, k_m \bigl(z(t)-z_f\bigr)\cos\theta_{\mathrm{det}},
$$

$$
\phi_{\mathrm{focus}}(t)
=
\arctan\!\left(\frac{y(t)-y_f}{z_R}\right).
$$

这里：

- $\phi_{\mathrm{unit}}$：来自本征 Mie 振幅的复相位 / intrinsic material/angle phase
- $\gamma_z$：由 `path_opd_model` 决定的几何因子；默认 `single_pass`
- $\theta_{\mathrm{det}}$：探测方向的等效收集角 / effective detection angle

### 4.4 为什么工程里要做 Gouy 去重 / Why Gouy De-duplication Is Needed

照明层已经有

$$
\phi_{\mathrm{beam}} = \phi_{\mathrm{gouy}} + \phi_{\mathrm{curv}},
$$

而 `relative_surrogate` 里又单独加入了

$$
\phi_{\mathrm{focus}}(t)
=
\arctan\!\left(\frac{y(t)-y_f}{z_R}\right).
$$

这和 Gouy 形式相同。如果两个都全量叠加，就会把过焦相位摆动算两次。因此工程默认在 `relative_surrogate` 下采用：

$$
\phi_{\mathrm{beam,eff}}(t) = \phi_{\mathrm{curv}}(t),
$$

只保留曲率项，把 Gouy-like 的过焦摆动交给 $\phi_{\mathrm{focus}}(t)$。

### 4.5 最终输出 / Final Output

因此工程最终得到：

$$
E_{\mathrm{sca}}(t)
=
A_{\mathrm{sca}}(t)e^{i\phi_{\mathrm{sca}}(t)}.
$$

### 4.6 承上启下 / Why This Step Feeds the Next One

经过这一步，第三节中的“本征散射能力”

$$
E_{\mathrm{sca,unit}}
$$

终于变成了可以直接和参考场相加的**时域复散射场**

$$
E_{\mathrm{sca}}(t).
$$

下一步的干涉层才真正有意义：

$$
E_{\mathrm{det}}(t)=E_{\mathrm{ref}}(t)+E_{\mathrm{sca}}(t).
$$

### 4.7 论文支撑 / Paper Support

- `2022 NODI`：颗粒穿过焦区时产生干涉脉冲，信号高度依赖相位和过焦时间平均。
- `2024 POD+NODI`：双通道事件同样是以毫秒级单颗粒 transit 为基本单位。

---

## 5. 干涉层：参考场和散射场在探测器上相加 / Interference Layer: Reference and Scattering Add at the Detector

### 5.1 论文中的核心公式 / Core Paper Formula

2022 NODI 的核心就是：

$$
I_t
=
|E_D+E_S|^2
=
|E_D|^2 + |E_S|^2 + 2|E_D||E_S|\cos\phi.
$$

若写成复数形式：

$$
I_t
=
|E_D|^2 + |E_S|^2 + 2\operatorname{Re}(E_D E_S^*).
$$

在弱散射极限下

$$
|E_D|^2 \gg |E_S|^2,
$$

于是常用近似是

$$
I_t - |E_D|^2
\approx
2\operatorname{Re}(E_D E_S^*).
$$

### 5.2 工程实现的精确对应 / Exact Engineering Mapping

`generate_interferometric_trace(...)` 做的事情是：

$$
E_{\mathrm{det}}(t)
=
E_{\mathrm{ref}}(t)+E_{\mathrm{sca}}(t),
$$

$$
I_{\mathrm{det}}(t)
=
\left|E_{\mathrm{det}}(t)\right|^2.
$$

随后拆出三项：

$$
I_{\mathrm{baseline}}(t)=|E_{\mathrm{ref}}(t)|^2,
$$

$$
I_{\mathrm{sca}}(t)=|E_{\mathrm{sca}}(t)|^2,
$$

$$
I_{\mathrm{cross}}(t)
=
2\operatorname{Re}\!\left(E_{\mathrm{ref}}(t)E_{\mathrm{sca}}^*(t)\right).
$$

如果 `background_subtraction_on = True`，则真正往后传的工作信号不是原始总强度，而是基线扣除后的：

$$
s_{\mathrm{raw}}(t)
=
I_{\mathrm{sca}}(t)+I_{\mathrm{cross}}(t).
$$

因此工程主线更准确的说法是：

$$
s_{\mathrm{raw}}(t)
=
|E_{\mathrm{sca}}(t)|^2
+ 2\operatorname{Re}\!\left(E_{\mathrm{ref}}(t)E_{\mathrm{sca}}^*(t)\right),
$$

而不是直接把整条原始 $|E_D+E_S|^2$ 原封不动地送到后级。

### 5.3 为什么这是合理的 / Why This Is Reasonable

因为论文要识别的不是恒定的空白通道背景，而是颗粒引起的增量事件。把大背景先从工作信号里扣掉，工程上更接近真实探测链会关注的“事件增量”。

### 5.4 `joint_overlap_integrated` 的含义 / Meaning of `joint_overlap_integrated`

工程还有一个重叠因子：

$$
I_{\mathrm{cross}}(t)
=
2\operatorname{Re}\!\left(
\Gamma_{\mathrm{overlap}}
E_{\mathrm{ref}}(t)E_{\mathrm{sca}}^*(t)
\right).
$$

其中 $\Gamma_{\mathrm{overlap}}$ 表示角向/投影重叠的复因子。这说明工程把“是否真正相干耦合得上”也显式放进来了。

### 5.5 承上启下 / Why This Step Feeds the Next One

前四节算出来的是“光场”；从这一节开始，输出变成了“探测器看到的时域信号”：

$$
s_{\mathrm{raw}}(t).
$$

后面的读出链、锁相、阈值、脉冲提取，全部都是对这个检测信号做电子学和算法处理。

### 5.6 论文支撑 / Paper Support

- `2022 NODI`：Eq. (1)，核心干涉公式。
- `2024 POD+NODI`：双通道系统依然共享同一物理入口，即探测器端的时域信号。
- `2019 POD`、`2020 diffraction`：都强调检测位置应位于 diffracted-light region 而不是 transmitted region。

---

## 6. 读出链：锁相、分频、串扰代理 / Readout Chain: Lock-In, Frequency Split, and Crosstalk Surrogates

### 6.1 标准锁相基础式 / Standard Lock-In Basics

任意频率 $f$ 上的锁相提取都可以写成：

$$
X_f(t)=\mathrm{LPF}\!\left[s(t)\cos(2\pi ft)\right],
$$

$$
Y_f(t)=\mathrm{LPF}\!\left[s(t)\sin(2\pi ft)\right],
$$

$$
R_f(t)=\sqrt{X_f^2(t)+Y_f^2(t)}.
$$

### 6.2 工程默认主线并不是“单个理想锁相器” / The Engineering Mainline Is Not a Single Ideal Lock-In

`apply_readout_chain(...)` 的默认模式是 `lockin_surrogate`，其结构是：

$$
s_{\mathrm{raw}}(t)
\;\to\;
\text{POD-like source} + \text{NODI-like source}
\;\to\;
\text{two demodulation lanes}
\;\to\;
\text{crosstalk mixing}
\;\to\;
s_{\mathrm{detect}}(t).
$$

具体写成公式就是：

$$
s_{\mathrm{pod,src}}(t)=\mathrm{LPF}\!\left(s_{\mathrm{raw}}(t)\right),
$$

$$
s_{\mathrm{nodi,src}}(t)=\mathrm{LPF}\!\left(s_{\mathrm{raw}}(t)-s_{\mathrm{pod,src}}(t)\right).
$$

然后分别做解调：

$$
D_{\mathrm{pod}}[\cdot] = \text{demod at } f_{\mathrm{pod}},
\qquad
D_{\mathrm{nodi}}[\cdot] = \text{demod at } f_{\mathrm{nodi}}.
$$

得到两条观测通道：

$$
s_{\mathrm{pod}}(t)
=
D_{\mathrm{pod}}\!\left[s_{\mathrm{pod,src}}\right]
+
\varepsilon_{n\to p}
D_{\mathrm{pod}}\!\left[s_{\mathrm{nodi,src}}\right],
$$

$$
s_{\mathrm{nodi}}(t)
=
D_{\mathrm{nodi}}\!\left[s_{\mathrm{nodi,src}}\right]
+
\varepsilon_{p\to n}
D_{\mathrm{nodi}}\!\left[s_{\mathrm{pod,src}}\right].
$$

最终 downstream 检测默认使用：

$$
s_{\mathrm{detect}}(t)=s_{\mathrm{nodi}}(t).
$$

### 6.3 可观测量选择 / Observable Selection

工程默认 `readout_observable_mode = "in_phase"`，因此默认输出是：

$$
s_{\mathrm{detect}}(t)=X(t).
$$

但 paper-aligned 的 `nodi_2022` 和 `paired_2024` 会切到：

$$
s_{\mathrm{detect}}(t)=R(t)=\sqrt{X^2(t)+Y^2(t)}.
$$

所以文档里不能笼统写成“工程默认就是 magnitude”；那只对 paper-aligned lane 成立，不对默认主线成立。

### 6.4 POD 与 NODI 的额外增益代理 / Extra POD and NODI Gain Surrogates

工程还有两个非常关键的代理增益：

1. POD 频率响应代理

$$
G_{\mathrm{pod}}(f)
\approx
\left(\frac{f_{\mathrm{ref}}}{f_{\mathrm{pod}}}\right)^p,
$$

再裁剪到预设范围。它只表达“低频更强”的趋势，**不是完整热扩散求解**。

2. NODI 过焦带宽代理

若过焦时间为 $t_{\mathrm{tr}}$，则

$$
f_{\mathrm{tr}} \approx \frac{1}{t_{\mathrm{tr}}},
\qquad
f_{\mathrm{LI}} \approx \frac{1}{2\pi\tau}.
$$

工程代理写为：

$$
G_{\mathrm{nodi}}
=
\frac{1}{\sqrt{1+\left(\frac{f_{\mathrm{tr}}}{f_{\mathrm{LI}}}\right)^2}},
$$

同样会裁剪到一个有限范围。

### 6.5 这一步和论文的关系 / Relation to the Papers

这一步要分开说：

- `2022 NODI` 和 `2024 POD+NODI` 的论文确实支撑“频率选择、时间常数、双通道分频、串扰减小”这些实验结论。
- 但工程里的 `apply_readout_chain(...)` 仍然是**电子学代理模型**，不是对真实硬件电路逐元件复现。
- 尤其是 POD 支路，当前工程没有把热源 $Q(r,z,t)$、热扩散方程、溶剂/玻璃 `dn/dT` 显式推进到时域读出；它只是保留了一个 POD-like 频段与增益代理。

### 6.6 承上启下 / Why This Step Feeds the Next One

这一层把“原始光学检测信号”

$$
s_{\mathrm{raw}}(t)
$$

变成“算法真正拿来判峰的检测信号”

$$
s_{\mathrm{detect}}(t).
$$

因此后面的阈值、峰值、配对，判的都不是光场，也不是原始强度，而是**读出后的检测通道波形**。

### 6.7 论文支撑 / Paper Support

- `2022 NODI`：Fig. 6，频率窗口、时间常数。
- `2024 POD+NODI`：Fig. 3-4，双通道 4.1/1.2 kHz 分频与串扰讨论。

---

## 7. 阈值、脉冲提取与双通道配对 / Thresholding, Pulse Extraction, and Two-Channel Pairing

### 7.1 论文口径 / Paper-Level Detection Rule

论文里的规则可以抽象成：

$$
\text{peak valid if } s(t_{\mathrm{peak}})
>
\mu_{\mathrm{bg}} + N\sigma_{\mathrm{bg}},
$$

并要求：

$$
w_{\mathrm{peak}} \ge w_{\min},
\qquad
\Delta t_{\mathrm{adjacent}} \ge \Delta t_{\min}.
$$

### 7.2 工程默认阈值并不是简单均值方差 / The Engineering Threshold Is Not a Plain Mean-Std Threshold

当前工程在 `simulate_one_event(...)` 中只取**前 20% 背景段**，再用 `estimate_threshold_stats_robust(...)` 计算：

$$
\mathrm{med} = \operatorname{median}(s_{\mathrm{bg}}),
$$

$$
\mathrm{MAD} = \operatorname{median}\!\left(|s_{\mathrm{bg}}-\mathrm{med}|\right),
$$

$$
\sigma_{\mathrm{robust}} = 1.4826 \cdot \mathrm{MAD},
$$

$$
\text{threshold} = \mathrm{med} + N\sigma_{\mathrm{robust}}.
$$

这比“全局均值 + 全局标准差”更接近单颗粒事件分析，因为它减少了事件本身污染背景估计的风险。

### 7.3 峰提取 / Peak Extraction

`extract_pulse_features(...)` 基于 `scipy.signal.find_peaks`，并使用：

- `height = threshold`
- `width \ge w_{\min}`
- `distance \ge \Delta t_{\min}`

返回的特征至少包括：

- `peak_height`
- `peak_signed_height`
- `peak_polarity`
- `peak_width_s`
- `peak_area`
- `prominence`

### 7.4 `absolute` 与 `positive` 的区别 / Difference Between `absolute` and `positive`

这也是工程校核时必须明确的一点：

- 默认主线：`pulse_detection_mode = "absolute"`

  $$
  s_{\mathrm{det,peak}}(t)=|s_{\mathrm{detect}}(t)|
  $$

  即正峰负峰都可以被记为事件。

- paper-aligned `nodi_2022` / `paired_2024`：`pulse_detection_mode = "positive"`

  $$
  s_{\mathrm{det,peak}}(t)=s_{\mathrm{detect}}(t),\quad s>0
  $$

  这更接近论文中“正向超过阈值”的检测口径。

### 7.5 双通道配对 / Two-Channel Pairing

2024 双通道逻辑在工程中实现为：先独立提取 NODI 与 POD 峰，再按时间配对：

$$
t_{2,\mathrm{match}}
=
\arg\max_{|t-t_{1,\mathrm{peak}}|\le \Delta t_{\mathrm{pair}}}
s_2(t).
$$

默认主线下

$$
\Delta t_{\mathrm{pair}} = 5\ \mathrm{ms},
$$

而 `paired_2024` 会放宽为

$$
\Delta t_{\mathrm{pair}} = 50\ \mathrm{ms}.
$$

最后：

- `single_channel`：只看 NODI 峰是否存在
- `paired_channel`：只保留有 POD 伙伴的 NODI 峰

### 7.6 承上启下 / Why This Step Feeds the Next One

从这一层开始，连续时间波形真正被离散成“事件”：

$$
s_{\mathrm{detect}}(t)
\;\to\;
\{\text{peaks}\}
\;\to\;
\{\text{event features}\}.
$$

论文里后续的粒径分布、计数率、分类散点图，本质上都是基于这些事件特征，而不是基于整条原始波形。

### 7.7 论文支撑 / Paper Support

- `2020 counting POD`：阈值、脉宽、计数。
- `2022 NODI`：阈值脉冲检测、maximum signal value。
- `2024 POD+NODI`：双通道时间配对。

---

## 8. 事件级到批统计：浓度、标度与分类 / From Event-Level Traces to Batch Statistics: Concentration, Scaling, and Classification

### 8.1 单事件模拟主链 / Single-Event Simulation Chain

`simulate_one_event(...)` 按如下顺序执行：

1. 采样初始位置 $(x_0,z_0)$
2. 若启用扩散，则根据 Stokes-Einstein 计算

$$
D = \frac{k_B T}{6\pi \eta a}
$$

3. 生成轨迹 $(x(t),y(t),z(t))$
4. 计算照明包络 `compute_illumination_envelope`
5. 估计过焦时间 `transit_time_s`
6. 生成参考场轨迹 `compute_reference_field_trace`
7. 生成散射场轨迹 `compute_scattering_field_trace`
8. 生成干涉信号 `generate_interferometric_trace`
9. 加探测噪声
10. 过 `apply_readout_chain`
11. 用背景段估阈值
12. 提取 NODI/POD 峰
13. 做双通道配对
14. 形成事件级特征和 detected / missed 判定

### 8.2 计数率与浓度 / Count Rate and Concentration

在低浓度稀疏事件下，论文和工程都默认：

$$
r = \frac{N_{\mathrm{peaks}}}{T_{\mathrm{obs}}}
\propto c.
$$

更细地写：

$$
r \approx c\,Q_v\,\eta_{\mathrm{det}}.
$$

### 8.3 为什么 counting POD 会接近 Poisson / Why Counting POD Approaches Poisson Statistics

若进入检测区的事件相互独立，则单位时间内计数服从泊松分布：

$$
P(k;\lambda_p)
=
\frac{\lambda_p^k e^{-\lambda_p}}{k!}.
$$

这对应的是“稀疏单颗粒、事件彼此独立”的统计语义。

### 8.4 为什么 NODI 实测不一定严格是理想 $d^3$ / Why Measured NODI Scaling Need Not Be Exactly $d^3$

理想瞬时干涉幅度更接近：

$$
I_{\mathrm{int}} \propto a^3.
$$

但真实读出看到的是经历了以下处理后的量：

$$
E_{\mathrm{sca}}(t)
\to
I_{\mathrm{cross}}(t)
\to
s_{\mathrm{raw}}(t)
\to
s_{\mathrm{detect}}(t)
\to
\text{peak height / max signal}.
$$

因此它会受到：

- 相位波动 / phase fluctuations
- 过焦时间平均 / transit-time averaging
- 锁相低通 / lock-in low-pass averaging
- 阈值和峰值定义 / threshold and peak definition

的共同影响。这正是 2022 NODI 实测更接近经验幂次而非理想瞬时 $d^3$ 的原因。

### 8.5 分类特征 / Classification Features

单通道 NODI 常用：

$$
\mathbf{x}
=
\left[
h,\,
w,\,
\text{maximum signal value}
\right].
$$

双通道 POD+NODI 常用：

$$
\mathbf{x}
=
\left[
h_{\mathrm{POD}},\,
w_{\mathrm{POD}},\,
h_{\mathrm{NODI}},\,
w_{\mathrm{NODI}}
\right].
$$

### 8.6 承上启下 / Why This Is the Final Physics-to-Statistics Bridge

前面所有光学与读出推导，最终都服务于这里：把连续的场和波形，转成论文真正汇报的对象：

- 计数率 / count rate
- 脉冲高度 / peak height
- 最大值 / maximum signal value
- 宽度 / width
- 双通道联合特征 / paired features

也就是说，Tsuyama 体系真正反复验证的对象，是**事件级可检测统计量**。

### 8.7 论文支撑 / Paper Support

- `2020 counting POD`：Poisson、计数、检测效率。
- `2022 NODI`：粒径标度、双波长分类、maximum signal value。
- `2024 POD+NODI`：吸收 + 散射双通道联合分类。

---

## 9. 六篇论文分别支撑哪一层 / What Each of the Six Papers Actually Constrains

- `2019 POD`

  支撑 POD 的物理起点：空白通道衍射、光热引起折射率变化、在 diffracted-light region 中检测。

- `2020 diffraction`

  支撑空白通道相位滤波器模型、后焦面衍射强度分布，以及从 $\theta$ 到衍射信号变化的理论骨架。

- `2020 counting POD`

  支撑单颗粒吸收检测的 transit、阈值、计数与 Poisson 统计语义。

- `2020 solvent-enhanced POD`

  支撑完整 POD 物理应包含：热源、热扩散、溶剂与玻璃的 `dn/dT`、`diffraction factor × photothermal factor`、符号翻转、最佳 `PD`、最佳调制频率。

- `2022 NODI`

  支撑 NODI 的核心干涉式

  $$
  I_t = |E_D+E_S|^2
  $$

  以及 overfill 照明、频率窗口、Mie-散射到干涉幅的关系、粒径标度与分类语义。

- `2024 POD+NODI`

  支撑双通道 simultaneous POD/NODI、分频、串扰、配对峰和 absorption + scattering 联合分类。

### 9.1 与当前工程的对应结论 / Alignment Verdict Against the Current Code

- `NODI 主链`：已经有较完整的工程实现，但其中参考场、相位、读出链都包含明确的 surrogate。
- `2020 diffraction 对齐`：可以通过 `paper_aligned_phase_filter` 更接近论文。
- `2022 NODI 对齐`：可以通过 `nodi_2022` profile 把照明、参考模型、读出 observable、检测极性调到更接近论文。
- `2024 paired POD+NODI 对齐`：可以通过 `paired_2024` profile 把双通道频率和配对规则调到更接近论文。
- `2019/2020 POD 热物理`：**当前并未真正实现**，只能写论文物理链，不能把工程默认 POD-like 读出代理说成论文定量实现。

---

## 10. 最后一条压缩版总流程 / Final Compressed Flow

若只保留最核心的一条链，可以写成：

$$
\underbrace{
\theta = \frac{2\pi(n_s-n_g)d}{\lambda}
}_{\text{blank-channel phase delay}}
\;\to\;
\underbrace{
E_{\mathrm{ref}}(t)
}_{\text{channel-derived reference}}
\;\to\;
\underbrace{
\frac{dC_{\mathrm{sca}}}{d\Omega}
\to
E_{\mathrm{sca,unit}}
\to
E_{\mathrm{sca}}(t)
}_{\text{particle scattering on trajectory}}
\;\to\;
\underbrace{
s_{\mathrm{raw}}(t)
=
|E_{\mathrm{sca}}|^2 + 2\operatorname{Re}(E_{\mathrm{ref}}E_{\mathrm{sca}}^*)
}_{\text{baseline-subtracted detector signal}}
\;\to\;
\underbrace{
s_{\mathrm{detect}}(t)
}_{\text{lock-in/readout output}}
\;\to\;
\underbrace{
\text{threshold} \to \text{peaks} \to \text{pairing} \to \text{count/classify}
}_{\text{event statistics}}
$$

而 POD 支路的正确写法应当分两句：

1. `论文上 / In the papers`

$$
Q(r,z,t)
\to
\Delta T
\to
\Delta n_s,\Delta n_g
\to
\Delta \theta
\to
\Delta PD.
$$

2. `当前工程上 / In the current code`

POD 主要体现在 `apply_readout_chain(...)` 的 POD-like 频段与串扰代理中，**不是完整的 2019/2020 thermal POD forward model**。
