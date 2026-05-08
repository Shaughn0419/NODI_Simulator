# mie_engine.py — Mie 散射理论引擎

## 文件职责

实现 Mie 散射理论的完整数值计算，遵循 Bohren & Huffman (1983) 的算法。由于运行环境中没有 miepython 等第三方库，本文件从零实现了 Mie 级数展开。

本模块是整个工程的最底层物理引擎——所有散射截面、角分布的计算都从这里开始。

---

## 物理背景

Mie 理论求解的是一个均匀球体在平面电磁波照射下的精确散射解。关键输入量是：

- **尺寸参数** x = k·a = 2π·n_m·a / λ₀（无量纲）
- **相对折射率** m = ñ_p / n_m（复数）

其中 a 是粒子半径，n_m 是介质折射率，ñ_p 是粒子复折射率，λ₀ 是真空波长。

---

## 函数列表

### 内部函数（以 `_` 开头，不对外暴露）

#### `_compute_nmax(x)`

确定 Mie 级数需要多少项才能收敛。使用 Wiscombe (1980) 准则：

```
nmax = int(x + 4·x^(1/3) + 2)
```

至少取 3 项。对于本工程中的纳米粒子（x 通常 < 1），nmax 一般为 3–5。

#### `_log_derivative_downward(m_rel, x, nmax)`

计算对数导数函数 D_n(mx)，采用**向下递推**（downward recurrence），这是数值上最稳定的方法。

递推公式：
```
D_{n-1}(z) = n/z - 1/(D_n(z) + n/z)
```

从足够高的阶 N_mx 开始（D_{N_mx} ≈ 0），递推到 n=1。N_mx 取 max(nmax, |mx|) + 16。

返回 D_1 到 D_nmax 的数组。

#### `_riccati_bessel(x, nmax)`

计算 Riccati-Bessel 函数 ψ_n(x) 和 ξ_n(x)，采用**向上递推**（upward recurrence）。

定义：
```
ψ_n(x) = x·j_n(x)        （实数，j_n 是球 Bessel 函数）
ξ_n(x) = ψ_n(x) - i·χ_n(x)  （复数，Bohren & Huffman 符号约定）
```

其中 χ_n(x) = -x·y_n(x)（y_n 是球 Neumann 函数）。

初始值：
```
ψ_0 = sin(x),  ψ_1 = sin(x)/x - cos(x)
χ_0 = cos(x),  χ_1 = cos(x)/x + sin(x)
```

递推：
```
ψ_{n+1} = (2n+1)/x · ψ_n - ψ_{n-1}
χ_{n+1} = (2n+1)/x · χ_n - χ_{n-1}
```

**重要**：ξ = ψ **- i**·χ，这里减号是 Bohren & Huffman 的约定。原始代码中曾用加号，导致吸收粒子出现 Qext < 0 的错误，已修复。

#### `_pi_tau(nmax, mu)`

计算角度依赖函数 π_n(cosθ) 和 τ_n(cosθ)，用于角分布计算。

递推关系：
```
π_1 = 1,  π_2 = 3μ
π_n = ((2n-1)·μ·π_{n-1} - n·π_{n-2}) / (n-1)
τ_n = n·μ·π_n - (n+1)·π_{n-1}
```

返回形状为 (nmax, N_angles) 的二维数组。

### 对外函数

#### `mie_coefficients(size_parameter, m_rel)`

计算 Mie 散射系数 a_n 和 b_n。

公式（B&H 第 100 页）：
```
a_n = (D_n/m + n/x)·ψ_n - ψ_{n-1}
      ─────────────────────────────
      (D_n/m + n/x)·ξ_n - ξ_{n-1}

b_n = (m·D_n + n/x)·ψ_n - ψ_{n-1}
      ─────────────────────────────
      (m·D_n + n/x)·ξ_n - ξ_{n-1}
```

返回两个复数数组 (a_n, b_n)，n = 1 到 nmax。

#### `mie_compute(size_parameter, m_rel) → (Qext, Qsca)`

计算消光效率因子 Qext 和散射效率因子 Qsca。

公式：
```
Qext = (2/x²) · Σ_n (2n+1) · Re(a_n + b_n)
Qsca = (2/x²) · Σ_n (2n+1) · (|a_n|² + |b_n|²)
```

截面可由效率因子乘以几何截面得到：Csca = Qsca · π·a²。

吸收效率 Qabs = Qext - Qsca，对非吸收粒子应近似为零。

#### `mie_angular(size_parameter, m_rel, theta_grid_rad) → (S1, S2)`

计算散射振幅函数 S1(θ) 和 S2(θ)。

公式：
```
S1(θ) = Σ_n (2n+1)/(n(n+1)) · [a_n·π_n(cosθ) + b_n·τ_n(cosθ)]
S2(θ) = Σ_n (2n+1)/(n(n+1)) · [a_n·τ_n(cosθ) + b_n·π_n(cosθ)]
```

S1 对应垂直偏振分量，S2 对应平行偏振分量。返回两个复数数组。

---

## 数值注意事项

1. **符号约定**：ξ = ψ - iχ（Bohren & Huffman）。这是整个引擎中最容易出错的地方。如果用错符号（ξ = ψ + iχ），吸收粒子的 Qext 会变成负数。
2. **向下递推 vs 向上递推**：对数导数 D_n 必须用向下递推（数值稳定），Riccati-Bessel 函数用向上递推。
3. **零尺寸保护**：当 x < 1e-10 时直接返回零，避免除零。
