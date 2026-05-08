# NODI 干涉散射检测模拟器

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

## 核心计算逻辑详解（扩充版）

*每一步的物理原理、公式推导、设计理由与文献依据*

## 1. 总体架构与设计思路

### 1.1 我们要解决什么问题

在纳米流控芯片中，当一颗纳米粒子（如 $20\text{--}100\,\mathrm{nm}$ 的金粒子或外泌体）随流体通过一条宽度和深度均在亚微米量级的通道时，探测激光照射产生的散射光极其微弱。以 $40\,\mathrm{nm}$ 金粒子为例，其散射截面约为 $10^{-15}\,\mathrm{m}^2$ 量级，远低于传统光学系统的直接检测极限。

NODI（Nanofluidic Optical Diffraction Interferometry）系统的核心思路是：不直接测量这个微弱的散射光强度，而是利用纳米通道本身产生的衍射光作为参考场，让它与粒子散射场发生干涉，从而将微弱信号线性放大到可检测水平。这与 iSCAT 显微镜利用盖玻片反射光作为参考场的原理一脉相承。

本模拟器的目标不是精确预测某个具体实验点的绝对信号值，而是系统地比较不同设计参数组合（粒子种类、激光波长、通道宽度、通道深度）下的相对可检测性，为实验设计提供参数空间筛选。

### 1.2 为什么要分层设计

如果把所有物理过程写在一个函数里，会出现两个问题：第一，很难定位错误在哪一层；第二，修改一个物理模型会牵动整个系统。分层设计使得每一层都有独立的物理含义和可审计的中间量。

例如，修改噪声模型不需要重新计算 Mie 散射；修改粒子材料不需要重新配置峰提取算法；修改评分权重不需要重跑干涉计算。这种模块化的可维护性对大规模参数扫描至关重要。

这种分层思路在干涉散射显微镜（iSCAT）领域被广泛使用。标准信号模型将检测过程分解为：粒子散射特性、参考场产生、干涉叠加、探测器读出等独立步骤。

- [1] Taylor, R.W. & Sandoghdar, V. Nano Lett. 19, 4827-4835 (2019). — iSCAT 干涉散射检测的基本信号模型
- [2] Tsuyama, Y. & Mawatari, K. Anal. Chem. 96, 11430-11438 (2024). — NODI 系统的直接实验基础
- [3] Tsuyama, Y. & Mawatari, K. Microfluid. Nanofluid. 26, 63 (2022). — NODI 检测原理与分类
### 1.3 七层计算链总览

整个计算链由以下七层组成，每一层的输出作为下一层的输入：

- **第一层：粒子本征散射（Mie 理论）**
  回答：这颗粒子在给定介质和波长下，本身散射得多强？散射光的角分布和复振幅相位是什么？

- **第二层：检测角与角谱收集**
  回答：实验系统等效地在哪个角度范围内收集散射光？有限孔径、狭缝和针孔如何影响收集效率？

- **第三层：参考场模型**
  回答：纳米通道产生的衍射参考场有多强？其与通道几何和波长的关系如何？

- **第四层：粒子轨迹与照明**
  回答：粒子在通道内怎么运动？在每个位置上被多强的光照射？光束自身携带的相位如何变化？

- **第五层：干涉检测信号**
  回答：参考场与散射场叠加后，探测器看到的时域信号是什么？干涉是建设性还是破坏性？

- **第六层：读出与噪声**
  回答：经过锁相放大器读出和各种噪声后，最终的可观测信号是什么？POD 和 NODI 两路信号如何分离？

- **第七层：峰提取与工程评分**
  回答：这个信号能不能被检测到？在大量随机事件中，检出率和稳定性如何？不同设计参数组合该怎么排序？

## 2. 第一层：粒子本征散射（Mie 理论）

### 2.1 这一层要解决什么

给定一颗球形粒子，我们需要知道它在给定波长和介质中的散射能力。这包括三个方面：散射了多少光（总截面积）；散射光在不同方向上的强度分布（角分布）；以及散射光在每个方向上的复振幅相位（材料散射相位）。

这一层故意只回答粒子本身的问题，不涉及通道几何、参考场、噪声等系统因素。这样做的原因是物理清晰性：粒子的本征光学性质是由其材料、尺寸和周围介质的折射率决定的，不应依赖于它被放在什么样的检测系统中。

对于球形粒子，这个问题有精确的解析解——Mie 理论（1908 年由 Gustav Mie 提出）。它是 Maxwell 方程在球对称边界条件下的严格解。

### 2.2 输入参数与物理含义

- **粒子半径** $a$

直接影响尺寸参数 $x = \frac{2\pi n_m a}{\$\lambda$}$，是 Mie 散射强弱的主要控制量。当 $x \ll 1$ 时，处于 Rayleigh 极限，散射截面与 $a^6$ 成正比——这意味着粒径缩小一半，散射强度下降 64 倍。这是小粒子检测困难的根本原因，也是干涉增强方法存在的必要性所在。

- **粒子复折射率** $n_p(\lambda) = n_{\mathrm{real}} + i\,n_{\mathrm{imag}}$

实部决定散射强度，虚部决定吸收。对于金纳米粒子，复折射率随波长剧烈变化，在等离子体共振（约 $520\,\mathrm{nm}$）附近散射和吸收都显著增强。这不是简单的 $1/\$\lambda$^4$ 趋势，而是由材料的电子结构决定的色散关系。工程中使用 Johnson & Christy (1972) 的实验测量数据进行表格插值，而不是用常数近似。

- **介质折射率** $n_m$

水在可见光波段约为 1.33。它与粒子折射率的比值 $m_{\mathrm{rel}} = n_p / n_m$ 是 Mie 计算的核心输入。当粒子折射率与介质很接近时（如生物粒子在水中），散射极弱，称为光学软粒子。

- [4] Bohren, C.F. & Huffman, D.R. Absorption and Scattering of Light by Small Particles. Wiley (1983), Ch. 4. — Mie 理论的标准教科书处理
- [5] Johnson, P.B. & Christy, R.W. Phys. Rev. B 6, 4370-4379 (1972). — 金银光学常数的标准数据源
- [6] Mie, G. Ann. Phys. 25, 377-445 (1908). — Mie 散射理论原始论文
### 2.3 Mie 系数的计算方法

Mie 散射系数 $a_n$ 和 $b_n$ 是级数展开中每一阶的权重，分别对应电多极子和磁多极子贡献。它们的计算需要 Riccati-Bessel 函数（$\psi_n$ 和 $\xi_n$）及其导数。

数值实现采用 Bohren & Huffman (1983) 的标准路径：首先用 Wiscombe (1980) 准则确定级数截断阶数 $n_{\max} = x + 4x^{1/3} + 2$；然后用下行递推计算对数导数 $D_n(mx)$（这比上行递推数值稳定得多）；再用上行递推计算 $\psi_n$(x) 和 $\xi_n$(x)；最后代入边界条件公式得到 $a_n$ 和 $b_n$。

这套算法在过去 40 年中被广泛验证，对于 x 从 0.01 到数千的范围都能给出可靠结果。

- [7] Wiscombe, W.J. Appl. Opt. 19, 1505-1509 (1980). — Mie 级数截断准则与数值稳定性
### 2.4 散射截面与效率因子

**总散射效率因子和消光效率因子：**

$$
Q_{\mathrm{sca}} = \frac{2}{x^2}\sum_n (2n+1)\left(|a_n|^2 + |b_n|^2\right)
$$

$$
Q_{\mathrm{ext}} = \frac{2}{x^2}\sum_n (2n+1)\,\mathrm{Re}(a_n + b_n)
$$

**对应的截面积：**

$$
C_{\mathrm{sca}} = Q_{\mathrm{sca}}\,\pi a^2
$$

$$
C_{\mathrm{ext}} = Q_{\mathrm{ext}}\,\pi a^2
$$

$$
C_{\mathrm{abs}} = C_{\mathrm{ext}} - C_{\mathrm{sca}}
$$

Q 值大于 1 表示粒子的散射截面超过了其几何截面——这在共振条件下是常见的，反映了粒子对入射场的有效收集范围超过了自身的物理尺寸。

### 2.5 角散射振幅函数

Mie 理论给出散射光在任意方向上的复振幅，通过角振幅函数 $S_1(\$\theta$)$ 和 $S_2(\$\theta$)$ 表达：

$$
S_1(\theta) = \sum_n \frac{2n+1}{n(n+1)} \left[a_n \pi_n(\cos\theta) + b_n \tau_n(\cos\theta)\right]
$$

$$
S_2(\theta) = \sum_n \frac{2n+1}{n(n+1)} \left[a_n \tau_n(\cos\theta) + b_n \pi_n(\cos\theta)\right]
$$

其中 $\pi_n$ 和 $\tau_n$ 是角函数，按 cos $\theta$ 递推计算。S1 对应垂直偏振散射分量，S2 对应平行偏振散射分量。这两个函数都是复数值——辐角包含散射相位信息，模值决定各方向的散射强度。

需要注意的是，$\sqrt{\frac{dC_{\mathrm{sca}}}{d\Omega}}$ 具有长度量纲（单位为 m），物理上对应散射振幅的尺度。它不是绝对电场值，而是一个与检测角处散射场幅度成正比的本征量。之所以取截面的平方根，是因为微分散射截面与散射振幅的平方成正比（Bohren & Huffman, 1983, Eq. 4.61），因此 $\sqrt{dC/d\Omega}$ 自然地具有"场振幅代理"的物理含义，适合在后续干涉模型中与参考场放在同一相对幅度框架下比较。

非偏振平均的微分散射截面为：

$$
\frac{dC_{\mathrm{sca}}}{d\Omega} = \frac{|S_1|^2 + |S_2|^2}{2k_m^2}
$$

需要特别说明的是，$\sqrt{\frac{dC_{\mathrm{sca}}}{d\Omega}}$ 具有长度量纲（单位 m），物理上对应散射振幅的尺度。这不是绝对电场值，而是一个与检测角处散射场幅度成正比的本征量。之所以取截面的平方根，是因为微分散射截面与散射振幅的平方成正比（Bohren & Huffman, 1983, Eq. 4.61），因此 $\sqrt{dC/d\Omega}$ 自然地具有场振幅代理的物理含义，适合在后续干涉模型中与参考场放在同一相对幅度框架下比较。

### 2.6 为什么输出复场振幅而不仅仅是截面

这一步是整个计算链中一个关键的设计选择。传统的散射检测（如暗场显微镜）只需要散射截面或强度；但干涉散射检测需要的是复电场——既需要振幅（决定信号强度）也需要相位（决定干涉条件）。

在 NODI 的相位感知主链中，我们保留 $S_2/k_m$ 的完整复数值（称为 parallel 投影模式）。其模值 $|S_2/k_m|$ 给出该方向的散射场强度；其辐角 $\arg(S_2/k_m)$ 就是材料散射相位 $\$\phi$_{\mathrm{material}}$。

对于金纳米粒子，材料散射相位在等离子体共振（约 $520\,\mathrm{nm}$）附近会发生近 $\pi$ 的跳变。这意味着在某些波长下干涉是建设性的（正脉冲），而在另一些波长下变成破坏性的（负脉冲）。如果只保留实数的散射截面值，这个关键信息就会完全丢失，模型将无法解释为什么某些波长-粒子组合的检出率突然下降。

- [8] Young, G. & Kukura, P. Annu. Rev. Phys. Chem. 70, 301-322 (2019). — 散射相位在干涉检测中的作用
- [9] Priest, L., Peters, J.S. & Kukura, P. Chem. Rev. 121, 11937-11970 (2021). — 散射显微镜中复振幅的重要性
## 3. 第二层：检测角与角谱收集

### 3.1 为什么需要这一层

Mie 理论给出的是完整的角分布 $\frac{dC_{\mathrm{sca}}}{d\Omega}(\$\theta$,\$\phi$)$，覆盖全部 $4\pi$ 立体角。但实验系统不会把所有角度的散射光都等权收集。在 Tsuyama 的实验中，收集端使用 $\mathrm{NA}=0.9$ 的物镜，加上 $1\,\mathrm{mm}$ 机械狭缝和 $400\,\mu\mathrm{m}$ 针孔。这些光学元件共同定义了一个特定的角谱收集窗口。

只有落在这个窗口内的散射光才能到达光电探测器。如果粒子的散射主要集中在窗口之外（例如大粒子的前向散射锥很窄），即使总散射截面很大，系统也未必能有效检测到。

因此，必须从完整角分布中提取出"系统实际能收集到的部分"。

### 3.2 通道衍射角模型

在 NODI 系统中，检测角不是任意选择的，而是由通道本身的衍射几何决定。纳米通道相当于一个亚波长衍射结构，其特征衍射角与通道宽度和波长的比值有关：

$$
\theta_{\mathrm{base}} = \arcsin\!\left(\frac{m\lambda_{\mathrm{eff}}}{W}\right), \qquad \lambda_{\mathrm{eff}} = \frac{\lambda_0}{n_m}
$$

$m$ 是衍射级次（通常取 1），$W$ 是通道宽度。这个关系直接来自经典衍射理论。当 $W$ 远大于 $\$\lambda$_{\mathrm{eff}}$ 时，衍射角很小；当 $W$ 接近 $\$\lambda$_{\mathrm{eff}}$ 时，衍射角增大。

失效边界：当 m * $\$\lambda$_{\mathrm{eff}}$ >= W 时，arcsin 的参数大于等于 1，公式不再有物理意义。这对应通道宽度已经接近或小于介质中的有效波长，此时通道不再像经典衍射孔径那样工作，而更接近亚波长波导。在这种情况下，系统自动回退到固定角模式或标定表查询，并在诊断中记录这一回退。

这个模型不是精确的通道衍射全波求解，而是一个经过物理约束的代理，捕获通道宽度、波长与检测角之间的基本几何关系。

- [10] Goodman, J.W. Introduction to Fourier Optics, 4th ed. W.H. Freeman (2017), Ch. 4. — 衍射角与孔径的关系
### 3.3 有限角收集算子

**实际的收集过程用一个二维角谱算子来表达：**

$$
E_{\mathrm{sca,det}} = \iint L_{\mathrm{det}}(\theta,\phi)\,E_{\mathrm{sca}}(\theta,\phi)\,d\Omega
$$

这个算子 $L_{\mathrm{det}}$ 包含以下分量：

$\theta$ 方向的高斯角核：以衍射中心角为中心，反映物镜的有限角收集带宽。核宽度 $\sigma_\$\theta$$ 由有效 NA 和通道几何共同决定。

光瞳函数 $pupil(\$\theta$)$：表达物镜对大角度分量的渐进衰减。实际物镜在其数值孔径边缘处的传递效率会下降。

狭缝函数 $slit(\$\phi$)$：表达 $1\,\mathrm{mm}$ 机械狭缝在方位角（$\phi$）方向的空间滤波。这限制了收集的方位角范围。

针孔函数 $pinhole(\$\theta$,\$\phi$)$：表达 $400\,\mu\mathrm{m}$ 针孔的进一步角度限制。

偏振投影 $\Pi_{\mathrm{pol}}(\$\theta$,\$\phi$)$：只有与参考场同偏振的散射分量才能产生有效干涉。对于平行偏振入射，主要收集的是 $S_2$ 分量。

- [2] Tsuyama & Mawatari (2024), Fig. 2 — 实验光路中的狭缝、针孔和滤光片
- [11] Hecht, E. Optics, 5th ed. Pearson (2017), Ch. 10. — 衍射光学与空间滤波
### 3.4 归一化：消除绝对比例常数

不同波长和不同通道几何下，收集算子的传递效率会变化。为了让不同 `case` 之间可以直接比较，所有散射场都用同一个基准粒子在同一探测算子下的值做归一化：

$$
E_{\mathrm{sca,norm}} = \frac{E_{\mathrm{sca,det}}}{E_{\mathrm{sca,ref}}}
$$

关键约束：归一化基准必须与运行时 `case` 使用完全相同的探测算子配置。这样可以吸收掉所有未知的绝对比例常数（如激光功率、探测器响应度等），只保留不同设计之间的相对差异。

这使得模型特别适合回答设计比较类问题：不同粒径谁更容易检测？不同通道几何谁更有利？不同波长谁更适合某种粒子？

## 4. 第三层：参考场模型

### 4.1 参考场的物理角色

NODI 检测的核心增强机制来自干涉。在弱散射极限下，检测信号近似为 $2|E_{\mathrm{ref}}||E_{\mathrm{sca}}|\cos(\Delta\phi)$。这意味着散射场 $E_{\mathrm{sca}}$ 被参考场 $E_{\mathrm{ref}}$ 线性放大。

举一个具体例子：如果 $|E_{\mathrm{ref}}| = 100|E_{\mathrm{sca}}|$，那么自散射项 $|E_{\mathrm{sca}}|^2 = 1$（相对单位），而干涉项 $2|E_{\mathrm{ref}}||E_{\mathrm{sca}}| = 200$。干涉信号比自散射强了 200 倍。这就是为什么 NODI 能检测到 $20\,\mathrm{nm}$ 的单个金纳米粒子——如果只靠 $|E_{\mathrm{sca}}|^2$，这在当前噪声水平下是不可能的。

在经典 iSCAT 显微镜中，参考场来自盖玻片的 Fresnel 反射（反射率约 0.4%）。在 NODI 中，参考场来自纳米通道本身对探测激光的衍射。Tsuyama (2022) 明确指出：通道衍射光同时充当光热检测（POD）的读出信号和干涉散射检测（NODI）的参考光。

- [1] Taylor & Sandoghdar (2019). — iSCAT 中参考场的角色
- [3] Tsuyama & Mawatari (2022). — NODI 中通道衍射光作为参考场
### 4.2 深度相位光栅模型

纳米通道可以看作一个嵌入玻璃基底中的水填充矩形沟槽。当探测光穿过这个结构时，水填充区域（$n_{\mathrm{water}} = 1.33$）和周围玻璃（$n_{\mathrm{glass}} = 1.46$）之间的折射率差异导致一个相位延迟：

$$
\delta_{\mathrm{ref}} = \frac{2\pi |\Delta n| H}{\lambda}
$$

其中 $\Delta n = n_{\mathrm{glass}} - n_{\mathrm{water}} = 0.13$，H 是通道深度。这个相位延迟决定了通道作为相位光栅的衍射效率。

根据薄相位光栅理论（Goodman, 2017, Ch. 4），一阶衍射场振幅正比于：

$$
E_{\mathrm{ref}} \propto 2\left|\sin\!\left(\frac{\delta_{\mathrm{ref}}}{2}\right)\right|
$$

这个公式有几个重要的物理含义：

（1）当 $\delta$ 很小时（浅通道或长波长），sin 近似为线性，衍射效率随 H 和 $\Delta n$ 线性增长

（2）当 $\delta = \pi$ 时（即 $|\Delta n|H = \$\lambda$/2$），衍射效率达到最大值

（3）当 $\delta$ 超过 $\pi$ 时，效率开始下降并出现振荡——这是 Raman-Nath 衍射区的特征行为

对于 Tsuyama 实验的典型参数：H = $550\,\mathrm{nm}$, $\Delta n$ = 0.13, $\lambda$ = $660\,\mathrm{nm}$ 时，$\delta = 0.68\,\mathrm{rad}$，远未到振荡区。对应的衍射振幅约为 $2|\sin(0.34)| = 0.67$（相对单位）。

- [10] Goodman (2017), Ch. 4 — 相位光栅的衍射效率
- [11] Hecht (2017), Ch. 10 — 衍射光栅理论
### 4.3 角谱结构

除了总的衍射效率，通道的矩形截面还决定了参考场在角谱空间中的分布。宽度方向（W）产生一个 sinc 型包络，深度方向（H）主要由上述相位光栅效率控制。整个参考场通过与散射场完全相同的探测算子进行角谱积分：

$$
E_{\mathrm{ref}} \propto \iint L_{\mathrm{det}}\,\mathrm{sinc}\!\left(\frac{Wk\sin\theta\cos\phi}{2\pi}\right)\,2\left|\sin\!\left(\frac{\delta}{2}\right)\right|e^{i\phi_{\mathrm{ref}}}\,d\Omega
$$

一个关键的设计选择是：$E_{\mathrm{ref}}$ 和 $E_{\mathrm{sca}}$ 必须通过同一个探测算子 $L_{\mathrm{det}}$。这保证了干涉项的物理一致性。如果两者使用不同的角谱权重，干涉效率（$overlap\ factor$）会下降——系统会显式计算这个 $overlap\ factor$ 作为结果可靠性的诊断指标。

### 4.4 参考场强度的物理约束

参考场强度参数 $\rho$ 不是完全自由的经验参数，而是受到物理包络约束的。基于相位光栅理论，一阶衍射效率 $\eta_1 = \sin^2(\delta/2)$，对应的振幅比为 $|\sin(\delta/2)|$。系统导出 $\rho$ 的物理建议范围（lower/upper 包络），并在诊断中检查实际使用的 $\rho$ 是否落在合理范围内。如果 $\rho$ 大幅偏离物理包络，对应 `case` 的解释可信度会被自动降低。

## 5. 第四层：粒子轨迹与照明

### 5.1 粒子在通道中的运动

粒子在纳米通道中的运动由两个机制控制：

**确定性流动**

粒子沿 y 方向随流体运动。矩形通道中的层流速度分布为抛物线型：中心处最快，壁面处为零。当前模型使用矩形截面抛物流剖面的精确形式。Tsuyama (2024) 报道典型流速约 $0.2\,\mathrm{mm}/\mathrm{s}$（$100\,\mathrm{kPa}$ 压力下），粒子通过检测区域约需 $10\,\mathrm{ms}$。

**随机扩散**

粒子在 x（宽度）和 z（深度）方向上发生布朗运动。扩散系数由 Stokes-Einstein 关系给出：

$$
D = \frac{k_B T}{6\pi \eta a}
$$

其中 k_B 是玻尔兹曼常数，T 是温度，eta 是介质粘度，a 是粒子半径。对于 $40\,\mathrm{nm}$ 金粒子在 $25^\circ\mathrm{C}$ 的水中，$D$ 大约为 $1.1\times10^{-11}\,\mathrm{m}^2/\mathrm{s}$。在 $10\,\mathrm{ms}$ 的 $transit\ time$ 内，平均扩散长度 $\sqrt{2D \cdot 10\,\mathrm{ms}}$ 约 $470\,\mathrm{nm}$，与通道尺寸（$500\text{--}2000\,\mathrm{nm}$）同量级，说明扩散对粒子在检测区内的位置变化有显著影响。

- [12] Einstein, A. Ann. Phys. 17, 549-560 (1905). — 布朗运动与 Stokes-Einstein 关系
- [2] Tsuyama & Mawatari (2024) — 典型流速和 transit time
### 5.2 近壁受限扩散

当粒子靠近通道壁面时，流体动力学相互作用会显著抑制扩散系数。物理原因是：壁面附近的流体必须从粒子和壁之间的狭窄间隙中被挤出，这增加了流体阻力。

模型采用 Faxen 风格的修正因子：

$$
D_{\mathrm{local}} = D\,f(a/h)
$$

其中 h 是粒子中心到最近壁面的距离，$\chi = a/h$ 是粒子半径与壁面距离的比值。平行于壁面方向的一阶修正为 $f \approx 1 - \frac{9\chi}{16} + \frac{\chi^3}{8} - \cdots$ ；垂直于壁面方向的抑制更强。

这个修正带来一个重要的物理效果：同一通道中，大粒子（chi 更大）受到更强的近壁限制——其扩散被更显著地抑制，位置波动更小。这是实验中确实观察到的现象，对理解不同粒径下的信号稳定性很有帮助。

- [13] Happel, J. & Brenner, H. Low Reynolds Number Hydrodynamics. Springer (1983). — Faxen 修正的理论基础
- [14] Deen, W.M. AIChE J. 33, 1409-1425 (1987). — 纳米通道中的受限输运理论
### 5.3 高斯光束照明包络

探测激光聚焦在通道上形成一个三维高斯光斑。由于我们需要的是场振幅（不是强度），所以照明包络取强度分布的平方根：

$$
A_{\mathrm{env}}(t) = \exp\!\left[-\frac{(x-x_f)^2}{w_x^2} - \frac{(y-y_f)^2}{w_y^2} - \frac{(z-z_f)^2}{w_z^2}\right]
$$

其中 w_x, w_y, w_z 是三个方向的光束腰半径，(x_f, y_f, z_f) 是焦点位置。这个包络决定了信号脉冲的时间宽度（$transit\ time$）——粒子只有在经过这个光斑时才会产生有意义的散射信号。

### 5.4 光束相位：Gouy 相位与波前曲率

聚焦高斯光束不只有振幅包络，还携带两个重要的相位项。这些相位直接参与干涉，影响信号的极性和波形。

**Gouy 相位**

粒子沿流动方向（y）穿过焦点时，经历一个总量为 $\pi$ 的相位跳变。这是聚焦光束的基本物理性质（任何聚焦波通过焦点时都会经历 Gouy 相移），在光学教科书中有标准推导：

$$
\phi_{\mathrm{Gouy}}(y) = \arctan\!\left(\frac{y-y_f}{z_R}\right)
$$

其中 $z_R = \pi n_m w_{\mathrm{eff}}^2 / \$\lambda$$ 是 Rayleigh 长度。

**波前曲率相位**

离焦后，光束波前从平面变为弯曲。离轴的粒子会经历额外的二次相位项：

其中波前曲率半径 R_eff(y) 的标准闭式表达为：

R_eff(y) = (y - y_f) + z_R^2 / (y - y_f) = (y - y_f) [1 + (z_R / (y - y_f))^2]

这是高斯光束理论中的标准结果（Kogelnik & Li, 1966; Saleh & Teich, 2019, Ch. 3）。离焦距离 |y - y_f| 很小时，R_eff 趋向无穷大（平面波前），$\phi$_curv 趋向零；离焦距离远大于 z_R 时，R_eff 近似为 (y - y_f)（球面波前）。因此：

$$
\phi_{\mathrm{curv}}(x,z,y) = \frac{0.5\,k_m\left((x-x_f)^2 + (z-z_f)^2\right)(y-y_f)}{(y-y_f)^2 + z_R^2}
$$

在焦点处（y = y_f），分子为零，$\phi$_curv 严格等于零。只有离焦且离轴时，这个项才逐步显现。这个边界行为已由测试冻结。

- [23] Kogelnik, H. & Li, T. Appl. Opt. 5, 1550-1567 (1966). — 高斯光束参数的标准推导
- [15] Saleh, B.E.A. & Teich, M.C. Fundamentals of Photonics, 3rd ed. Wiley (2019), Ch. 3. — 高斯光束、Gouy 相位与波前曲率
## 6. 第五层：干涉检测信号

### 6.1 干涉信号的基本公式

探测器看到的是参考场和散射场的相干叠加。在背景扣除后，信号为：

$$
E_{\mathrm{det}}(t) = E_{\mathrm{ref}}(t) + E_{\mathrm{sca}}(t)
$$

$$
\mathrm{signal}(t) = |E_{\mathrm{det}}(t)|^2 - |E_{\mathrm{ref}}(t)|^2
$$

$$
= |E_{\mathrm{sca}}|^2 + 2\,\mathrm{Re}\!\left(E_{\mathrm{ref}}E_{\mathrm{sca}}^\ast\right)
$$

第一项 $|E_{\mathrm{sca}}|^2$ 是自散射项，对于纳米粒子极其微弱（与散射截面成正比，即与粒径的六次方成正比）。第二项是交叉干涉项，它被参考场线性放大（只与散射振幅成正比，即与粒径的三次方成正比）。

这个放大效应正是干涉散射检测的核心优势。在 $shot\ noise$ 限制下，干涉检测的信噪比正比于 $|E_{\mathrm{sca}}|$（而不是 $|E_{\mathrm{sca}}|^2$），因此散射振幅每下降 2 倍，SNR 只下降 2 倍而不是 4 倍。

- [1] Taylor & Sandoghdar (2019). — 干涉增强的基本原理与 SNR 分析
### 6.2 弱散射极限与干涉增强的量级估计

当 $|E_{\mathrm{sca}}| \ll |E_{\mathrm{ref}}|$ 时（这是 NODI 检测纳米粒子时的典型情况），信号简化为：

$$
\mathrm{signal} \approx 2|E_{\mathrm{ref}}||E_{\mathrm{sca}}|\cos(\Delta\phi)
$$

对于 Tsuyama 实验中的 $40\,\mathrm{nm}$ 金粒子，散射场与参考场的典型比值为 $|E_{\mathrm{sca}}|/|E_{\mathrm{ref}}|$ = 10^-2 到 10^-3 量级。干涉交叉项因此是自散射项的 100-1000 倍——这就是纳米粒子在 NODI 系统中可以被检测到的根本原因。

### 6.3 相位差的多个来源

干涉信号 $2|E_{\mathrm{ref}}||E_{\mathrm{sca}}|\cos(\Delta\phi)$ 中的相位差 \Delta\phi 决定了干涉是建设性（$\cos(\Delta\phi) > 0$，正脉冲）还是破坏性（$\cos(\Delta\phi) < 0$，负脉冲）。这个相位差来自四个独立的物理来源：

（1）材料散射相位 $\$\phi$_{\mathrm{material}}$

来自 Mie 系数的复数相位 $\arg(S_2/k_m)$。对于金粒子，在等离子体共振附近会发生近 $\pi$ 的跳变。这意味着同一个粒子在不同波长下可能产生正脉冲或负脉冲。系统显式导出这个量以供诊断。

（2）路径相位 $\$\phi$_{\mathrm{path}}$

粒子在通道内不同位置（主要是深度方向 z）与参考场之间存在光程差：

$$
\phi_{\mathrm{path}} \approx k_m z \cos(\theta_{\mathrm{det}})
$$

这是信号随粒子位置波动（$phase\ flip$）的主要原因。在 $500\,\mathrm{nm}$ 深的通道中，不同深度位置可以导致 $\$\phi$_{\mathrm{path}}$ 从 0 变化到约 $\pi/3\,\mathrm{rad}$，足以显著改变干涉条件。

（3）光束相位 $\$\phi$_{\mathrm{beam}}$

包括穿焦 Gouy 相位（arctan 函数，总跳变 $\pi$）和离焦波前曲率相位。

（4）参考场相位 $\$\phi$_{\mathrm{ref}}$

来自通道衍射结构的固有相位。包括深度相位光栅的相位贡献和矩形角谱中 $\mathrm{sinc}$ 函数过零时的 pi 跳变。

- [16] Mahmoodabadi, R.G. et al. Opt. Express 28, 25969-25988 (2020). — iPSF 中相位差与轴向位置的关系
### 6.4 Overlap factor：角谱不匹配的量化

严格来说，干涉项不是简单地把分别积分后的 $E_{\mathrm{ref}}$ 和 $E_{\mathrm{sca}}$ 相乘，而应该在角谱空间做联合积分。当 $E_{\mathrm{ref}}$（通道衍射场角谱）和 $E_{\mathrm{sca}}$（Mie 散射角谱）的角分布不完全匹配时，联合积分的结果会偏离简单乘积。

系统显式计算 $overlap\ factor$ 来量化这个偏差，其数学定义为：

eta_ov = |INTEGRAL INTEGRAL $L_{\mathrm{det}}$ $E_{\mathrm{ref}}$ $E_{\mathrm{sca}}$* d_Omega| / (|INTEGRAL INTEGRAL $L_{\mathrm{det}}$ $E_{\mathrm{ref}}$ d_Omega| * |INTEGRAL INTEGRAL $L_{\mathrm{det}}$ $E_{\mathrm{sca}}$ d_Omega|)

当 eta_ov 接近 1 时，参考场与散射场的角谱高度重叠，分别积分后再相乘是好的近似；当 eta_ov 显著小于 1 时，说明两者的角谱分布不匹配较严重，干涉效率下降，需要切换到联合角谱积分模式或人工复核。对于典型的 NODI 参数，当通道几何不太极端时，eta_ov 通常保持在 0.85 以上。

## 7. 第六层：读出与噪声

### 7.1 双通道锁相放大器模型

在 Tsuyama (2024) 的实验中，POD（光热吸收）信号和 NODI（干涉散射）信号共用同一个光电探测器和光路，通过双通道锁相放大器（LI5660, NF Corporation）分离：

POD 通道（1-ch）：提取与激发光调制频率（如 $4.1\,\mathrm{kHz}$）同步的分量。当粒子吸收激发光并产生热效应时，局部折射率变化导致通道衍射光强度发生与调制频率同步的变化。

NODI 通道（2-ch）：提取与调制频率不同步的高频分量（如 $1.2\,\mathrm{kHz}$）。粒子的弹性散射与激发光调制无关，但其与通道衍射光的干涉产生独立的高频信号。

Tsuyama (2024) 的实验结果表明：当调制频率较低时（0.5-$1.2\,\mathrm{kHz}$），NODI 信号会泄漏到 POD 通道，导致两路信号难以分离。只有将调制频率提高到 $4.1\,\mathrm{kHz}$，POD 信号的纯度才超过 $80\%$。

- [2] Tsuyama & Mawatari (2024), Fig. 4 — 调制频率对 POD/NODI 分离质量的影响
### 7.2 读出链代理

模拟器构建了一个最小的锁相读出代理，包含以下要素：

时间常数（$1\text{--}2\,\mathrm{ms}$）：决定低通滤波的等效带宽。Tsuyama 实验中使用 $1\text{--}2\,\mathrm{ms}$ 的时间常数。

POD 频率响应：光热信号强度与调制频率成反比（这是热扩散导致的基本物理特性），因此 POD 通道在高频下灵敏度降低。

NODI transit-bandwidth 约束：当粒子通过检测区的时间（约 $10\,\mathrm{ms}$）对应的信号频率接近或超过 lock-in 的等效带宽时，信号会被部分截断。模型用一阶低通响应近似这个效应。

通道串扰矩阵：模拟低频下 NODI 信号向 POD 通道的泄漏。

### 7.3 噪声模型

噪声分为两个层次，对应物理上不同来源的噪声：

前读出层（pre-readout）

高斯噪声：代表探测器热噪声和放大器噪声。

Shot noise：光子噪声，与参考场强度成正比：

$$
\mathrm{shot\_noise}(t) \sim \mathcal{N}\!\left(0,\ \mathrm{shot\_noise\_scale}^2\,I_{\mathrm{proxy}}(t)\right)
$$

这反映了干涉检测的一个基本物理限制：参考场越强，干涉增强越大，但 $shot\ noise$ 也同时增大。在 $shot\ noise$ 限制下，最佳参考场强度是信号增强和噪声增加之间的折中。

线性漂移：代表激光功率漂移、温度变化等慢变化因素。

后读出层（post-readout）

经过锁相放大器后再叠加的额外噪声和基线偏置，代表电子学链路中的残余噪声。

- [17] Kukura, P. et al. Nat. Methods 6, 923-927 (2009). — iSCAT 中的 shot noise 限制
## 8. 第七层：峰提取与工程评分

### 8.1 阈值估计

要判断一个脉冲是否是真实的粒子信号，首先需要估计背景噪声水平。模型使用信号前段（粒子尚未进入检测区时）的数据作为纯背景段，用 $\mathrm{MAD}$（Median Absolute Deviation）进行稳健估计：

$$
\mathrm{robust\_std} = 1.4826 \cdot \mathrm{MAD}(\mathrm{signal}_{\mathrm{bg}})
$$

$$
\mathrm{threshold} = \mathrm{median}(\mathrm{signal}_{\mathrm{bg}}) + N_\sigma \cdot \mathrm{robust\_std}
$$

选择 MAD 而不是标准差的原因是：即使背景段中有少量异常值（如偶发的通道缺陷信号或电子学毛刺），$\mathrm{MAD}$ 也能给出稳定的噪声估计。系数 1.4826 使得对正态分布而言，MAD 估计值与标准差一致。$N_\sigma$ 是阈值倍数，默认取 $5\sigma$。

- [18] Huber, P.J. Robust Statistics. Wiley (1981). — MAD 稳健估计的统计理论基础
### 8.2 峰检测模式

系统支持两种峰检测模式：

**positive 模式**

只在原始信号上检测正脉冲。适用于相位模型关闭（假设始终建设性干涉）的简化情况。

**absolute 模式（默认）**

在 $|\mathrm{signal}|$ 上检测峰，但同时记录原始信号的符号、带符号高度和极性。这是默认模式，因为一旦引入位置相关的相位模型，某些事件可能产生负脉冲——如果只检测正峰，这些有效的物理信号就会被误判为未检出，导致检出率被系统性低估。

### 8.3 单事件到批量统计

每个 `case`（固定的粒子、波长、通道几何组合）模拟 n_events 个随机事件，每个事件有不同的初始位置和扩散轨迹。对于每个事件，如果检测到多个峰，只取最高峰。然后汇总以下统计量：

$$
\text{检出率 } detection\_rate = \frac{n_{\mathrm{detected}}}{n_{\mathrm{events}}}
$$

稳定检出率 stable_$detection\_rate$：只计算峰高明显超过阈值（而不是刚好过阈）的事件

平均峰高及其变异系数 CV

相位翻转比例 $phase\_flip\_fraction$：负脉冲在已检出事件中的占比

阈值安全裕量 $mean\_peak\_margin\_z$：峰高超出阈值的程度（以背景标准差为单位）

$local\ \mathrm{SNR}$：信号峰值与局部背景噪声的比值

$\mathrm{ROC\!-\!AUC}$ 和 $d^\prime$：事件信号分布与背景分布的可分离度

### 8.4 三层评分体系

**$\mathrm{score}$（探索分数）**

$$
\mathrm{score} = w_h H_{\mathrm{norm}} + w_r R_{\mathrm{norm}} - w_{cv} CV_{\mathrm{norm}}
$$

主要关注平均峰高、检出率和变异系数。适合快速探索、历史对照和趋势发现。

**$\mathrm{engineering\_score}$（工程分数）**

在探索分数基础上增加了稳定检出率、阈值安全裕量、$local\ \mathrm{SNR}$、$\mathrm{ROC\!-\!AUC}$、$d^\prime$ 以及相位翻转惩罚。它的设计意图是偏向中等强度但更稳定、更可区分背景的设计点。

**$\mathrm{final\_engineering\_score}$（最终工程决策分数）**

先检查一组硬性工程门槛，不通过的 `case` 直接被压到通过集合之后：

最小检出事件数（避免因为事件太少就给出过高的检出率估计）

Wilson 下界的检出率（Wilson 小样本修正提供保守的置信下界）

稳定检出率下界

相位翻转比例上界（如果大量事件的信号极性不稳定，该设计不可靠）

峰高裕量下界（如果信号只是刚好过阈值，稍有波动就会丢失）

通过门槛后，再按工程分数排序。这个两阶段机制确保了工程上不可接受的 `case`（如检出太少或翻相太多）不会因为某个单项指标偶然很高而被错误地排到前面。

- [19] Wilson, E.B. J. Am. Stat. Assoc. 22, 209-212 (1927). — Wilson 小样本修正
- [20] Green, D.M. & Swets, J.A. Signal Detection Theory and Psychophysics. Wiley (1966). — ROC 分析与 d-prime
## 9. 参考文献汇总

- [1] Taylor, R.W. & Sandoghdar, V. Interferometric Scattering Microscopy: Seeing Single Nanoparticles and Molecules via Rayleigh Scattering. Nano Lett. 19, 4827-4835 (2019).
- [2] Tsuyama, Y. & Mawatari, K. Nanofluidic Detection Platform for Simultaneous Light Absorption and Scattering Measurement of Individual Nanoparticles in Flow. Anal. Chem. 96, 11430-11438 (2024).
- [3] Tsuyama, Y. & Mawatari, K. Nanofluidic optical diffraction interferometry for detection and classification of individual nanoparticles in a nanochannel. Microfluid. Nanofluid. 26, 63 (2022).
- [4] Bohren, C.F. & Huffman, D.R. Absorption and Scattering of Light by Small Particles. Wiley-Interscience (1983).
- [5] Johnson, P.B. & Christy, R.W. Optical Constants of the Noble Metals. Phys. Rev. B 6, 4370-4379 (1972).
- [6] Mie, G. Beitraege zur Optik trüber Medien. Ann. Phys. 25, 377-445 (1908).
- [7] Wiscombe, W.J. Improved Mie scattering algorithms. Appl. Opt. 19, 1505-1509 (1980).
- [8] Young, G. & Kukura, P. Interferometric Scattering Microscopy. Annu. Rev. Phys. Chem. 70, 301-322 (2019).
- [9] Priest, L., Peters, J.S. & Kukura, P. Scattering-Based Light Microscopy. Chem. Rev. 121, 11937-11970 (2021).
- [10] Goodman, J.W. Introduction to Fourier Optics, 4th ed. W.H. Freeman (2017).
- [11] Hecht, E. Optics, 5th ed. Pearson (2017).
- [12] Einstein, A. Ann. Phys. 17, 549-560 (1905).
- [13] Happel, J. & Brenner, H. Low Reynolds Number Hydrodynamics. Springer (1983).
- [14] Deen, W.M. AIChE J. 33, 1409-1425 (1987).
- [15] Saleh, B.E.A. & Teich, M.C. Fundamentals of Photonics, 3rd ed. Wiley (2019).
- [16] Mahmoodabadi, R.G. et al. Opt. Express 28, 25969-25988 (2020).
- [17] Kukura, P. et al. Nat. Methods 6, 923-927 (2009).
- [18] Huber, P.J. Robust Statistics. Wiley (1981).
- [19] Wilson, E.B. J. Am. Stat. Assoc. 22, 209-212 (1927).
- [20] Green, D.M. & Swets, J.A. Signal Detection Theory and Psychophysics. Wiley (1966).
- [21] Tsuyama, Y. & Mawatari, K. Anal. Chem. 92, 3434-3439 (2020).
- [22] Spacková, B. et al. Nat. Methods 19, 751-758 (2022).
- [23] Kogelnik, H. & Li, T. Laser Beams and Resonators. Appl. Opt. 5, 1550-1567 (1966).
