+++
title = "金融数学基础"
description = "深入讲解量化金融的数学基础：随机过程、布朗运动、伊藤引理、几何布朗运动、鞅论与随机微分方程"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["金融数学", "随机过程", "布朗运动", "伊藤引理", "量化"]
+++

# 金融数学基础

## 概述

金融数学是量化金融的理论基石。从期权定价到风险管理，从交易策略到组合优化，都离不开随机过程和随机微分方程的支持。本文深入介绍金融数学的核心概念。

## 一、概率论回顾

### 1.1 概率空间

概率空间由三元组 \((\Omega, \mathcal{F}, \mathbb{P})\) 定义：

- \(\Omega\): 样本空间，所有可能结果的集合
- \(\mathcal{F}\): σ-代数，事件的集合
- \(\mathbb{P}\): 概率测度

**条件期望**:

给定σ-代数 \(\mathcal{G}\)，随机变量X的条件期望 \(\mathbb{E}[X|\mathcal{G}]\) 满足：

1. \(\mathbb{E}[X|\mathcal{G}]\) 是 \(\mathcal{G}\)-可测的
2. 对任意 \(A \in \mathcal{G}\)：\(\int_A X d\mathbb{P} = \int_A \mathbb{E}[X|\mathcal{G}] d\mathbb{P}\)

### 1.2 重要分布

```python
import numpy as np
from scipy import stats

# 正态分布 - 股票收益率的常用假设
mu, sigma = 0.05, 0.2  # 年化收益5%，波动率20%
daily_return = np.random.normal(mu/252, sigma/np.sqrt(252), 1000)

# 对数正态分布 - 股票价格模型
S0 = 100
T = 1  # 1年
prices = S0 * np.exp(np.random.normal((mu - 0.5*sigma**2)*T, 
                                       sigma*np.sqrt(T), 10000))

# 泊松分布 - 跳跃过程
lambda_jump = 3  # 年均跳跃3次
jumps = np.random.poisson(lambda_jump, 10000)

# 指数分布 - 到达时间间隔
arrival_times = np.random.exponential(1/lambda_jump, 10000)
```

## 二、随机过程

### 2.1 基本定义

随机过程是一族随机变量 \(\{X_t\}_{t \geq 0}\)，其中每个 \(X_t\) 是概率空间上的随机变量。

**重要性质**：

1. **平稳性**：统计特性不随时间改变
2. **马尔可夫性**：未来只依赖于现在，与过去无关
3. **鞅性**：条件期望等于当前值

### 2.2 布朗运动（维纳过程）

标准布朗运动 \(W_t\) 满足：

1. \(W_0 = 0\)
2. 独立增量：\(W_t - W_s\) 与 \(W_s\) 独立（\(t > s\)）
3. 正态增量：\(W_t - W_s \sim N(0, t-s)\)
4. 路径连续

**关键性质**：

- \(\mathbb{E}[W_t] = 0\)
- \(\text{Var}(W_t) = t\)
- \(\mathbb{E}[W_s W_t] = \min(s, t)\)
- 二次变差：\([W, W]_t = t\)

```python
import numpy as np
import matplotlib.pyplot as plt

def simulate_brownian_motion(T, N, num_paths=5):
    """模拟布朗运动
    
    Args:
        T: 终止时间
        N: 时间步数
        num_paths: 路径数量
    """
    dt = T / N
    t = np.linspace(0, T, N+1)
    
    # 生成增量
    dW = np.random.normal(0, np.sqrt(dt), (num_paths, N))
    
    # 累积求和得到路径
    W = np.zeros((num_paths, N+1))
    W[:, 1:] = np.cumsum(dW, axis=1)
    
    return t, W

# 模拟并绘图
t, W = simulate_brownian_motion(T=1, N=1000, num_paths=5)

plt.figure(figsize=(10, 6))
for i in range(5):
    plt.plot(t, W[i], alpha=0.7)
plt.xlabel('Time')
plt.ylabel('W(t)')
plt.title('Brownian Motion Paths')
plt.grid(True)
plt.show()
```

### 2.3 几何布朗运动（GBM）

股票价格常用几何布朗运动建模：

\[dS_t = \mu S_t dt + \sigma S_t dW_t\]

其中：
- \(\mu\): 漂移率（期望收益率）
- \(\sigma\): 波动率

**解析解**（应用伊藤引理）：

\[S_t = S_0 \exp\left[\left(\mu - \frac{\sigma^2}{2}\right)t + \sigma W_t\right]\]

```python
def simulate_gbm(S0, mu, sigma, T, N, num_paths=1000):
    """模拟几何布朗运动
    
    Args:
        S0: 初始价格
        mu: 漂移率
        sigma: 波动率
        T: 终止时间
        N: 时间步数
        num_paths: 路径数量
    """
    dt = T / N
    t = np.linspace(0, T, N+1)
    
    # 生成布朗运动增量
    dW = np.random.normal(0, np.sqrt(dt), (num_paths, N))
    W = np.zeros((num_paths, N+1))
    W[:, 1:] = np.cumsum(dW, axis=1)
    
    # 计算价格路径
    S = S0 * np.exp((mu - 0.5*sigma**2) * t + sigma * W)
    
    return t, S

# 模拟股票价格
S0, mu, sigma, T = 100, 0.1, 0.2, 1
t, S = simulate_gbm(S0, mu, sigma, T, N=252, num_paths=1000)

# 统计验证
print(f"理论期望价格: {S0 * np.exp(mu * T):.2f}")
print(f"模拟平均价格: {S[:, -1].mean():.2f}")
print(f"理论标准差: {S0 * np.exp(mu * T) * np.sqrt(np.exp(sigma**2 * T) - 1):.2f}")
print(f"模拟标准差: {S[:, -1].std():.2f}")
```

## 三、伊藤引理

### 3.1 伊藤积分

对于适应过程 \(f_t\)，伊藤积分定义为：

\[\int_0^T f_t dW_t = \lim_{n \to \infty} \sum_{i=0}^{n-1} f_{t_i}(W_{t_{i+1}} - W_{t_i})\]

**关键性质**：

- \(\mathbb{E}\left[\int_0^T f_t dW_t\right] = 0\)（鞅性质）
- 伊藤等距：\(\mathbb{E}\left[\left(\int_0^T f_t dW_t\right)^2\right] = \mathbb{E}\left[\int_0^T f_t^2 dt\right]\)

### 3.2 伊藤引理（伊藤公式）

设 \(X_t\) 满足：
\[dX_t = \mu_t dt + \sigma_t dW_t\]

对于二阶连续可微函数 \(f(t, x)\)：

\[df(t, X_t) = \frac{\partial f}{\partial t}dt + \frac{\partial f}{\partial x}dX_t + \frac{1}{2}\frac{\partial^2 f}{\partial x^2}(dX_t)^2\]

由于 \((dW_t)^2 = dt\)，展开得：

\[df = \left(\frac{\partial f}{\partial t} + \mu_t\frac{\partial f}{\partial x} + \frac{1}{2}\sigma_t^2\frac{\partial^2 f}{\partial x^2}\right)dt + \sigma_t\frac{\partial f}{\partial x}dW_t\]

### 3.3 伊藤引理应用示例

**示例1：推导GBM解析解**

设 \(f(t, S) = \ln S\)，\(dS = \mu S dt + \sigma S dW\)

\[\frac{\partial f}{\partial t} = 0, \quad \frac{\partial f}{\partial S} = \frac{1}{S}, \quad \frac{\partial^2 f}{\partial S^2} = -\frac{1}{S^2}\]

应用伊藤引理：

\[d(\ln S) = \frac{1}{S}(\mu S dt + \sigma S dW) + \frac{1}{2}\left(-\frac{1}{S^2}\right)\sigma^2 S^2 dt\]

\[= \left(\mu - \frac{\sigma^2}{2}\right)dt + \sigma dW\]

积分得：

\[\ln S_t - \ln S_0 = \left(\mu - \frac{\sigma^2}{2}\right)t + \sigma W_t\]

因此：

\[S_t = S_0 \exp\left[\left(\mu - \frac{\sigma^2}{2}\right)t + \sigma W_t\right]\]

```python
# 验证伊藤引理的数值计算
def verify_ito_lemma():
    """数值验证伊藤引理"""
    S0, mu, sigma, T, N = 100, 0.1, 0.2, 1, 10000
    dt = T / N
    
    # 模拟一条路径
    dW = np.random.normal(0, np.sqrt(dt), N)
    
    # 方法1：直接模拟GBM
    S = np.zeros(N + 1)
    S[0] = S0
    for i in range(N):
        S[i+1] = S[i] * (1 + mu * dt + sigma * dW[i])
    
    # 方法2：使用解析解
    W = np.zeros(N + 1)
    W[1:] = np.cumsum(dW)
    t = np.linspace(0, T, N + 1)
    S_exact = S0 * np.exp((mu - 0.5*sigma**2) * t + sigma * W)
    
    print(f"直接模拟最终价格: {S[-1]:.4f}")
    print(f"解析解最终价格: {S_exact[-1]:.4f}")
    print(f"相对误差: {abs(S[-1] - S_exact[-1]) / S_exact[-1] * 100:.4f}%")

verify_ito_lemma()
```

**示例2：计算 \(W_t^2\) 的微分**

设 \(f(W) = W^2\)

\[\frac{\partial f}{\partial W} = 2W, \quad \frac{\partial^2 f}{\partial W^2} = 2\]

应用伊藤引理：

\[d(W_t^2) = 2W_t dW_t + \frac{1}{2} \cdot 2 \cdot dt = 2W_t dW_t + dt\]

积分得：

\[W_t^2 = 2\int_0^t W_s dW_s + t\]

因此：

\[\int_0^t W_s dW_s = \frac{1}{2}(W_t^2 - t)\]

## 四、鞅论

### 4.1 鞅的定义

随机过程 \(\{M_t\}_{t \geq 0}\) 是鞅，如果对所有 \(s < t\)：

\[\mathbb{E}[M_t | \mathcal{F}_s] = M_s\]

**直观理解**：当前观测值是对未来值的最佳预测。

### 4.2 重要的鞅

1. **布朗运动** \(W_t\) 是鞅
2. **补偿泊松过程** \(N_t - \lambda t\) 是鞅
3. **几何布朗运动**（贴现后）在风险中性测度下是鞅

```python
def verify_martingale_property():
    """验证鞅性质"""
    # 模拟布朗运动
    N, T = 10000, 1
    dt = T / N
    paths = 10000
    
    dW = np.random.normal(0, np.sqrt(dt), (paths, N))
    W = np.zeros((paths, N + 1))
    W[:, 1:] = np.cumsum(dW, axis=1)
    
    # 在时间s，计算E[W_t | F_s]
    s_idx = N // 2
    t_idx = N
    
    W_s = W[:, s_idx]
    W_t = W[:, t_idx]
    
    # 条件期望应该等于W_s
    # 由于增量独立，E[W_t | F_s] = W_s + E[W_t - W_s] = W_s
    print(f"E[W_t - W_s] = {(W_t - W_s).mean():.4f} (应接近0)")
    print(f"Var(W_t - W_s) = {(W_t - W_s).var():.4f} (应接近{(t_idx - s_idx) * dt:.4f})")

verify_martingale_property()
```

### 4.3 Girsanov定理

Girsanov定理允许我们改变概率测度，将带漂移的过程转化为鞅。

设 \(W_t\) 是 \(\mathbb{P}\) 下的标准布朗运动，\(\theta_t\) 是适应过程。定义：

\[\tilde{W}_t = W_t + \int_0^t \theta_s ds\]

在新测度 \(\mathbb{Q}\) 下（通过 Radon-Nikodym 导数定义），\(\tilde{W}_t\) 是标准布朗运动。

**金融应用**：将实际测度 \(\mathbb{P}\) 转换为风险中性测度 \(\mathbb{Q}\)。

## 五、随机微分方程

### 5.1 SDE的一般形式

\[dX_t = \mu(t, X_t)dt + \sigma(t, X_t)dW_t\]

其中：
- \(\mu(t, x)\)：漂移系数
- \(\sigma(t, x)\)：扩散系数

### 5.2 常见SDE模型

| 模型 | SDE | 用途 |
|------|-----|------|
| 几何布朗运动 | \(dS = \mu S dt + \sigma S dW\) | 股票价格 |
| Ornstein-Uhlenbeck | \(dX = \kappa(\theta - X)dt + \sigma dW\) | 利率、均值回归 |
| Cox-Ingersoll-Ross | \(dr = \kappa(\theta - r)dt + \sigma\sqrt{r}dW\) | 利率 |
| Heston | \(dv = \kappa(\theta - v)dt + \xi\sqrt{v}dW\) | 随机波动率 |

### 5.3 OU过程

Ornstein-Uhlenbeck过程具有均值回归特性：

\[dX_t = \kappa(\theta - X_t)dt + \sigma dW_t\]

**解析解**：

\[X_t = X_0 e^{-\kappa t} + \theta(1 - e^{-\kappa t}) + \sigma \int_0^t e^{-\kappa(t-s)} dW_s\]

```python
def simulate_ou_process(X0, kappa, theta, sigma, T, N, num_paths=1000):
    """模拟OU过程
    
    Args:
        X0: 初始值
        kappa: 均值回归速度
        theta: 长期均值
        sigma: 波动率
        T: 终止时间
        N: 时间步数
        num_paths: 路径数量
    """
    dt = T / N
    t = np.linspace(0, T, N+1)
    
    X = np.zeros((num_paths, N+1))
    X[:, 0] = X0
    
    dW = np.random.normal(0, np.sqrt(dt), (num_paths, N))
    
    for i in range(N):
        X[:, i+1] = X[:, i] + kappa * (theta - X[:, i]) * dt + sigma * dW[:, i]
    
    return t, X

# 模拟
X0, kappa, theta, sigma = 0.5, 2, 1, 0.3
t, X = simulate_ou_process(X0, kappa, theta, sigma, T=5, N=1000, num_paths=100)

# 验证长期分布
# 稳态均值 = theta, 稳态方差 = sigma^2 / (2*kappa)
print(f"理论稳态均值: {theta:.4f}")
print(f"模拟终值均值: {X[:, -1].mean():.4f}")
print(f"理论稳态标准差: {sigma / np.sqrt(2 * kappa):.4f}")
print(f"模拟终值标准差: {X[:, -1].std():.4f}")
```

### 5.4 CIR过程

Cox-Ingersoll-Ross过程用于建模利率：

\[dr_t = \kappa(\theta - r_t)dt + \sigma\sqrt{r_t}dW_t\]

**Feller条件**：\(2\kappa\theta > \sigma^2\) 保证 \(r_t > 0\)

```python
def simulate_cir_process(r0, kappa, theta, sigma, T, N, num_paths=1000):
    """模拟CIR过程（使用Euler-Maruyama方法，带截断）"""
    dt = T / N
    t = np.linspace(0, T, N+1)
    
    r = np.zeros((num_paths, N+1))
    r[:, 0] = r0
    
    dW = np.random.normal(0, np.sqrt(dt), (num_paths, N))
    
    for i in range(N):
        r_pos = np.maximum(r[:, i], 0)  # 截断负值
        r[:, i+1] = r[:, i] + kappa * (theta - r_pos) * dt + sigma * np.sqrt(r_pos) * dW[:, i]
        r[:, i+1] = np.maximum(r[:, i+1], 0)  # 截断负值
    
    return t, r

# 检验Feller条件
r0, kappa, theta, sigma = 0.05, 0.5, 0.05, 0.1
feller_satisfied = 2 * kappa * theta > sigma**2
print(f"Feller条件: {2*kappa*theta:.4f} > {sigma**2:.4f} = {feller_satisfied}")

t, r = simulate_cir_process(r0, kappa, theta, sigma, T=10, N=2520, num_paths=1000)
print(f"路径非负: {(r >= 0).all()}")
```

## 六、数值方法

### 6.1 Euler-Maruyama方法

对于SDE \(dX = \mu(X)dt + \sigma(X)dW\)：

\[X_{n+1} = X_n + \mu(X_n)\Delta t + \sigma(X_n)\Delta W_n\]

其中 \(\Delta W_n \sim N(0, \Delta t)\)

收敛阶：强收敛 \(O(\sqrt{\Delta t})\)，弱收敛 \(O(\Delta t)\)

### 6.2 Milstein方法

\[X_{n+1} = X_n + \mu(X_n)\Delta t + \sigma(X_n)\Delta W_n + \frac{1}{2}\sigma(X_n)\sigma'(X_n)((\Delta W_n)^2 - \Delta t)\]

收敛阶：强收敛 \(O(\Delta t)\)

```python
def euler_maruyama(X0, mu, sigma, T, N, num_paths=1):
    """Euler-Maruyama方法"""
    dt = T / N
    X = np.zeros((num_paths, N+1))
    X[:, 0] = X0
    
    dW = np.random.normal(0, np.sqrt(dt), (num_paths, N))
    
    for i in range(N):
        X[:, i+1] = X[:, i] + mu(X[:, i]) * dt + sigma(X[:, i]) * dW[:, i]
    
    return X

def milstein(X0, mu, sigma, sigma_prime, T, N, num_paths=1):
    """Milstein方法"""
    dt = T / N
    X = np.zeros((num_paths, N+1))
    X[:, 0] = X0
    
    dW = np.random.normal(0, np.sqrt(dt), (num_paths, N))
    
    for i in range(N):
        X[:, i+1] = (X[:, i] + mu(X[:, i]) * dt + sigma(X[:, i]) * dW[:, i] + 
                    0.5 * sigma(X[:, i]) * sigma_prime(X[:, i]) * (dW[:, i]**2 - dt))
    
    return X

# 比较精度（GBM）
S0, mu_val, sigma_val, T = 100, 0.1, 0.2, 1

mu = lambda x: mu_val * x
sigma_func = lambda x: sigma_val * x
sigma_prime = lambda x: sigma_val

# 解析解期望
analytical_mean = S0 * np.exp(mu_val * T)

for N in [10, 100, 1000]:
    np.random.seed(42)
    S_euler = euler_maruyama(S0, mu, sigma_func, T, N, num_paths=10000)
    np.random.seed(42)  # 相同随机数
    S_milstein = milstein(S0, mu, sigma_func, sigma_prime, T, N, num_paths=10000)
    
    euler_err = abs(S_euler[:, -1].mean() - analytical_mean)
    milstein_err = abs(S_milstein[:, -1].mean() - analytical_mean)
    
    print(f"N={N:4d}: Euler误差={euler_err:.4f}, Milstein误差={milstein_err:.4f}")
```

## 七、面试常见问题

### Q1: 解释伊藤引理与普通链式法则的区别

**答案**：普通微积分中，\(d(f(x)) = f'(x)dx\)。但在随机微积分中，由于 \((dW)^2 = dt \neq 0\)（而普通微积分中 \((dx)^2 = 0\)），我们需要额外的二阶项：

\[df = f'dX + \frac{1}{2}f''(dX)^2\]

这就是伊藤引理的核心差异。

### Q2: 为什么GBM的期望收益率和漂移率不同？

**答案**：由于Jensen不等式。对于对数正态分布：

\[\mathbb{E}[S_T] = S_0 e^{\mu T}\]

但：

\[\mathbb{E}[\ln(S_T/S_0)] = (\mu - \sigma^2/2)T\]

因此对数收益率的期望是 \(\mu - \sigma^2/2\)，而非 \(\mu\)。

### Q3: 什么是风险中性定价？

**答案**：风险中性定价是指在一个虚构的概率测度（风险中性测度）下，所有资产的期望收益率都等于无风险利率。在此测度下：

\[\text{衍生品价格} = e^{-rT}\mathbb{E}^{\mathbb{Q}}[\text{到期收益}]\]

Girsanov定理提供了从真实测度到风险中性测度转换的数学基础。

## 总结

金融数学的核心要点：

1. **布朗运动**：金融模型的基础随机驱动
2. **伊藤引理**：随机微积分的链式法则
3. **几何布朗运动**：股票价格的标准模型
4. **鞅论**：公平博弈和风险中性定价的基础
5. **数值方法**：实际应用中的模拟技术

掌握这些概念是理解期权定价、风险管理和量化策略的基础。
