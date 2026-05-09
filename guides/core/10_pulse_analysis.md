# nodi_simulator/pulse_analysis.py — 脉冲分析模块

## 文件职责

从检测轨迹中提取脉冲特征。这是将"时间信号"转化为"事件级指标"的关键步骤，直接对应论文中的数据处理方法：基于背景波动设阈值，使用最小峰宽和最小峰间隔提取事件。

需要注意当前主链已经变成：

- `signal_raw_noisy`：原始干涉信号经过 pre-readout 噪声后的轨迹
- `signal_detect_pre_post`：经过 `readout_model` 之后、post-readout 噪声之前的检测轨迹
- `signal_noisy`：经过 `readout_model` 处理后、真正进入阈值和峰提取的检测轨迹

其中 `signal_raw_noisy` 当前已经不再只是“固定高斯噪声”，还可能包含与 `I_baseline / I_det` 相关的 shot-noise surrogate；因此本模块面对的是“最终检测通道的时间序列”，而不再默认等同于旧版 `raw + noise_std`。

---

## 函数

### `estimate_threshold_robust(signal_segment, sigma_multiplier) → float`

#### 作用

用稳健统计方法从背景信号段估计检测阈值。

#### 为什么用 median + MAD 而不是 mean + std？

Mean 和 std 容易受异常值（如脉冲残留）影响。Median 和 MAD（Median Absolute Deviation）对异常值更稳健。即使有少量脉冲泄漏到背景段，估计结果也不会偏很多。

#### 公式

```
median = np.median(signal_segment)
MAD = np.median(|signal_segment - median|)
robust_std = 1.4826 × MAD
threshold = median + sigma_multiplier × robust_std
```

**1.4826 的来源**：对于高斯分布，MAD = 0.6745·σ，因此 σ = MAD / 0.6745 ≈ 1.4826 × MAD。

#### 重要调用约定

**必须传入背景段（前 20%），不是整条信号。** 在 `simulate_one_event` 中：
```python
n_bg = int(0.2 × len(signal))
threshold = estimate_threshold_robust(signal[:n_bg], sigma_multiplier)
```

前 20% 是纯背景的保证来自轨迹设计（粒子在 50% 处才到达焦点）和 `validate_simulation_config` 的检查。

### `estimate_threshold_stats_robust(signal_segment, sigma_multiplier) → dict`

当前代码在保留旧接口的同时，还新增了一个更完整的阈值统计入口，返回：

- `median`
- `mad`
- `robust_std`
- `threshold`

这样 batch 汇总层不仅能拿到阈值本身，还能拿到 `robust_std` 去定义更稳的 `peak margin z-score`。

---

### `extract_pulse_features(time_s, signal_noisy, threshold, min_peak_width_s, min_peak_interval_s, detection_mode="positive") → dict`

#### 作用

从信号中提取所有满足条件的脉冲，并计算每个脉冲的特征。

当前模块支持两种检测口径：

- `positive`：只检测高于阈值的正峰
- `absolute`：在 `|signal|` 上检测峰，但仍保留原始信号的符号和值

第二种模式是为了配合新的位置相关相位模型。引入 `relative_surrogate` 后，真实信号不再保证所有事件都是建设性干涉，负脉冲也可能是有效响应；如果仍然只找正峰，会把相位导致的负脉冲误判成“未检出”。

#### 内部逻辑

**步骤 1：参数转换**

将秒为单位的约束转换为采样点数：
```python
dt = time_s[1] - time_s[0]
min_width_samples = max(1, int(min_peak_width_s / dt))
min_distance_samples = max(1, int(min_peak_interval_s / dt))
```

**步骤 2：调用 scipy.signal.find_peaks**

`detection_mode="positive"` 时：

```python
peak_indices, properties = find_peaks(
    signal_noisy,
    height=threshold,
    width=min_width_samples,
    distance=min_distance_samples,
    prominence=0,
)
```

`detection_mode="absolute"` 时，`find_peaks` 会改在 `abs(signal_noisy)` 上运行，但后续记录的峰值仍会回到原始带符号信号上读取。

`find_peaks` 返回：
- `peak_indices`：峰的位置索引
- `properties`：包含 peak_heights、widths、prominences、left_ips、right_ips 等

**步骤 3：逐峰提取特征**

对每个检测到的峰：

- **height**：峰值高度（signal 在峰位置的值）
- **signed_height**：原始信号在峰位置的带符号幅值
- **polarity**：该峰在原始信号中是正峰还是负峰
- **peak_time_s**：峰出现的时间
- **width_s**：峰的半高全宽（FWHM），由 `find_peaks` 的 width 属性换算
- **prominence**：峰相对于两侧基线的凸出程度
- **area**：峰下面积

面积计算使用梯形积分，边界索引用 `floor/ceil` 处理浮点值：
```python
left = max(0, int(np.floor(properties["left_ips"][i])))
right = min(len(signal) - 1, int(np.ceil(properties["right_ips"][i])))
area = np.trapezoid(signal[left:right+1], time[left:right+1])
```

用 floor 取左界、ceil 取右界、再 clip 到合法范围，避免浮点索引截断导致漏掉边界面积。

#### 输出

```python
{
    "n_peaks": int,            # 检测到的峰数
    "peaks": [                 # 每个峰的特征字典列表
        {
            "peak_time_s": float,
            "peak_height": float,          # 检测用幅值；absolute 模式下始终为正
            "peak_signed_height": float,   # 原始带符号幅值
            "peak_polarity": str,          # "positive" / "negative"
            "peak_width_s": float,
            "peak_area": float,
            "prominence": float,
        },
        ...
    ],
    "threshold_used": float,   # 使用的阈值值
    "detection_mode": str,     # 当前峰提取口径
}
```

---

## 与论文的对应

论文中的数据处理流程：
1. 记录时间信号
2. 基于背景波动设阈值（N_σ × σ_background）
3. 用最小峰宽和最小峰间隔过滤
4. 提取峰高和峰宽做后续分析

本模块直接对应这个流程。`threshold_sigma` 对应论文中的 N_σ。

需要注意：当前主链虽然已经在脉冲提取前加入了一个最小可用的 `lockin_surrogate` 读出链，但它仍然不是论文里完整的锁相电子学复现。`absolute` 检测模式的目标仍然是避免在引入位置相关相位后，把负脉冲直接丢掉。

---

## 在流水线中的位置

```
signal_noisy(t) [读出后的检测通道] → estimate_threshold_robust(前20%背景段)
       │                        │
       ▼                        ▼ threshold
extract_pulse_features(signal_noisy, threshold, ...)
       │
       ▼ {n_peaks, peaks}
summarize_batch → detection_rate, mean_height, mean_width, ...
```

## 当前默认口径

- 基础包 `DEFAULT_SIM_CFG` 现在也已默认切到 `pulse_detection_mode="absolute"` 和 `readout_model="lockin_surrogate"`，并与 `channel_diffraction + relative_surrogate` 主观测链保持一致
- `positive + raw` 仍保留，但现在是显式 legacy compatibility 路径，不再是默认工作流
