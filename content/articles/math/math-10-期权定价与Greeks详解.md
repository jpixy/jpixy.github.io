+++
title = "10.期权定价与Greeks详解(HFT)"
description = "深入讲解期权定价理论：Black-Scholes模型推导、Greeks敏感性分析、隐含波动率、波动率曲面与二叉树定价"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["期权定价", "Black-Scholes", "Greeks", "隐含波动率", "量化", "HFT"]
+++

# 期权定价与Greeks详解(HFT)

## 概述

期权定价是量化金融的核心领域。本文深入介绍Black-Scholes模型的推导、Greeks风险敏感性分析、隐含波动率计算以及数值定价方法。

## 一、Black-Scholes模型

### 1.1 模型假设

Black-Scholes模型基于以下假设：

1. 股票价格服从几何布朗运动：\(dS = \mu S dt + \sigma S dW\)
2. 无风险利率 \(r\) 恒定
3. 无交易成本和税收
4. 股票不支付股息
5. 可以无限制地卖空
6. 可以连续交易
7. 市场无套利

### 1.2 Black-Scholes PDE推导

考虑一个期权组合：持有1份期权 \(V(S,t)\)，做空 \(\Delta\) 份股票。

组合价值：\(\Pi = V - \Delta S\)

组合价值变化：

\[d\Pi = dV - \Delta dS\]

应用伊藤引理：

\[dV = \frac{\partial V}{\partial t}dt + \frac{\partial V}{\partial S}dS + \frac{1}{2}\frac{\partial^2 V}{\partial S^2}(dS)^2\]

由于 \((dS)^2 = \sigma^2 S^2 dt\)：

\[dV = \left(\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2}\right)dt + \frac{\partial V}{\partial S}dS\]

选择 \(\Delta = \frac{\partial V}{\partial S}\)（Delta对冲），消除随机项：

\[d\Pi = \left(\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2}\right)dt\]

无套利条件要求：\(d\Pi = r\Pi dt\)

得到 **Black-Scholes PDE**：

\[\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + rS\frac{\partial V}{\partial S} - rV = 0\]

### 1.3 Black-Scholes公式

**欧式看涨期权**：

\[C = S_0 N(d_1) - Ke^{-rT}N(d_2)\]

**欧式看跌期权**：

\[P = Ke^{-rT}N(-d_2) - S_0 N(-d_1)\]

其中：

\[d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}\]

\[d_2 = d_1 - \sigma\sqrt{T}\]

\(N(\cdot)\) 是标准正态分布的累积分布函数。

```python
import numpy as np
from scipy.stats import norm

def black_scholes(S, K, T, r, sigma, option_type='call'):
    """Black-Scholes期权定价
    
    Args:
        S: 标的价格
        K: 行权价
        T: 到期时间（年）
        r: 无风险利率
        sigma: 波动率
        option_type: 'call' 或 'put'
    
    Returns:
        期权价格
    """
    if T <= 0:
        if option_type == 'call':
            return max(S - K, 0)
        else:
            return max(K - S, 0)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    return price

# 示例
S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2
call_price = black_scholes(S, K, T, r, sigma, 'call')
put_price = black_scholes(S, K, T, r, sigma, 'put')

print(f"看涨期权价格: {call_price:.4f}")
print(f"看跌期权价格: {put_price:.4f}")

# 验证Put-Call Parity: C - P = S - K*exp(-rT)
parity_lhs = call_price - put_price
parity_rhs = S - K * np.exp(-r * T)
print(f"Put-Call Parity验证: {parity_lhs:.4f} = {parity_rhs:.4f}")
```

## 二、Greeks详解

### 2.1 Greeks定义与公式

| Greek | 定义 | 看涨期权公式 | 含义 |
|-------|------|-------------|------|
| Delta (Δ) | \(\frac{\partial V}{\partial S}\) | \(N(d_1)\) | 价格敏感度 |
| Gamma (Γ) | \(\frac{\partial^2 V}{\partial S^2}\) | \(\frac{n(d_1)}{S\sigma\sqrt{T}}\) | Delta变化率 |
| Theta (Θ) | \(\frac{\partial V}{\partial t}\) | (见下) | 时间衰减 |
| Vega (ν) | \(\frac{\partial V}{\partial \sigma}\) | \(S\sqrt{T}n(d_1)\) | 波动率敏感度 |
| Rho (ρ) | \(\frac{\partial V}{\partial r}\) | \(KTe^{-rT}N(d_2)\) | 利率敏感度 |

其中 \(n(\cdot)\) 是标准正态分布的概率密度函数。

**Theta公式**（看涨）：

\[\Theta = -\frac{S\sigma n(d_1)}{2\sqrt{T}} - rKe^{-rT}N(d_2)\]

```python
def calculate_greeks(S, K, T, r, sigma, option_type='call'):
    """计算期权的所有Greeks
    
    Returns:
        dict: 包含所有Greeks的字典
    """
    if T <= 0:
        return {
            'delta': 1 if (option_type == 'call' and S > K) else 
                     -1 if (option_type == 'put' and S < K) else 0,
            'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0
        }
    
    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    
    # 正态分布函数
    Nd1 = norm.cdf(d1)
    Nd2 = norm.cdf(d2)
    nd1 = norm.pdf(d1)
    
    # Delta
    if option_type == 'call':
        delta = Nd1
    else:
        delta = Nd1 - 1
    
    # Gamma (Call和Put相同)
    gamma = nd1 / (S * sigma * sqrt_T)
    
    # Theta
    theta_common = -S * sigma * nd1 / (2 * sqrt_T)
    if option_type == 'call':
        theta = theta_common - r * K * np.exp(-r * T) * Nd2
    else:
        theta = theta_common + r * K * np.exp(-r * T) * norm.cdf(-d2)
    theta = theta / 365  # 转换为每日
    
    # Vega (Call和Put相同)
    vega = S * sqrt_T * nd1 / 100  # 除以100，表示1%波动率变化
    
    # Rho
    if option_type == 'call':
        rho = K * T * np.exp(-r * T) * Nd2 / 100
    else:
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }

# 计算Greeks
greeks = calculate_greeks(100, 100, 1, 0.05, 0.2, 'call')
print("看涨期权Greeks:")
for name, value in greeks.items():
    print(f"  {name.capitalize()}: {value:.6f}")
```

### 2.2 Greeks的直观理解

```
Delta (Δ):
├── 范围: Call [0,1], Put [-1,0]
├── ATM期权 Delta ≈ ±0.5
├── 对冲比率: 需要Delta份股票对冲期权
└── 解释: 概率近似（风险中性下到期ITM的概率）

Gamma (Γ):
├── 总是正值
├── ATM期权Gamma最大
├── 临近到期时ATM Gamma激增
└── 解释: Delta的凸性，对冲需要频繁调整

Theta (Θ):
├── 通常为负（时间价值损耗）
├── ATM期权Theta绝对值最大
├── 临近到期时Theta加速
└── Theta与Gamma的关系: Θ ≈ -½ Γ S² σ²（近似）

Vega (ν):
├── 总是正值
├── ATM期权Vega最大
├── 长期期权Vega更大
└── 解释: 波动率交易的核心

Rho (ρ):
├── Call为正，Put为负
├── 长期期权更敏感
└── 在HFT中通常不重要（期限短）
```

### 2.3 Greeks可视化

```python
import matplotlib.pyplot as plt

def plot_greeks():
    """可视化Greeks随标的价格变化"""
    S_range = np.linspace(70, 130, 100)
    K, T, r, sigma = 100, 0.25, 0.05, 0.2
    
    greeks_data = {
        'delta': [], 'gamma': [], 'theta': [], 'vega': []
    }
    
    for S in S_range:
        g = calculate_greeks(S, K, T, r, sigma, 'call')
        for key in greeks_data:
            greeks_data[key].append(g[key])
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0, 0].plot(S_range, greeks_data['delta'])
    axes[0, 0].set_title('Delta')
    axes[0, 0].axhline(y=0.5, color='r', linestyle='--', alpha=0.5)
    axes[0, 0].axvline(x=K, color='gray', linestyle='--', alpha=0.5)
    
    axes[0, 1].plot(S_range, greeks_data['gamma'])
    axes[0, 1].set_title('Gamma')
    axes[0, 1].axvline(x=K, color='gray', linestyle='--', alpha=0.5)
    
    axes[1, 0].plot(S_range, greeks_data['theta'])
    axes[1, 0].set_title('Theta (per day)')
    axes[1, 0].axvline(x=K, color='gray', linestyle='--', alpha=0.5)
    
    axes[1, 1].plot(S_range, greeks_data['vega'])
    axes[1, 1].set_title('Vega (per 1% vol)')
    axes[1, 1].axvline(x=K, color='gray', linestyle='--', alpha=0.5)
    
    for ax in axes.flat:
        ax.set_xlabel('Stock Price')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('greeks.png', dpi=150)
    plt.close()

plot_greeks()
```

## 三、隐含波动率

### 3.1 隐含波动率定义

隐含波动率（IV）是使得BS模型价格等于市场价格的波动率：

\[C_{BS}(S, K, T, r, \sigma_{IV}) = C_{market}\]

### 3.2 Newton-Raphson求解

由于BS公式对 \(\sigma\) 单调递增，可用Newton-Raphson迭代：

\[\sigma_{n+1} = \sigma_n - \frac{C_{BS}(\sigma_n) - C_{market}}{\text{Vega}(\sigma_n)}\]

```python
def implied_volatility(price, S, K, T, r, option_type='call', 
                       max_iter=100, tol=1e-8):
    """使用Newton-Raphson计算隐含波动率
    
    Args:
        price: 期权市场价格
        S, K, T, r: BS模型参数
        option_type: 'call' 或 'put'
        max_iter: 最大迭代次数
        tol: 收敛容差
    
    Returns:
        隐含波动率
    """
    # 初始猜测
    sigma = 0.2
    
    for i in range(max_iter):
        # 计算BS价格和Vega
        bs_price = black_scholes(S, K, T, r, sigma, option_type)
        greeks = calculate_greeks(S, K, T, r, sigma, option_type)
        vega = greeks['vega'] * 100  # 转换回原始vega
        
        if abs(vega) < 1e-10:
            # Vega太小，使用二分法
            return implied_volatility_bisection(price, S, K, T, r, option_type)
        
        # Newton-Raphson更新
        diff = bs_price - price
        if abs(diff) < tol:
            return sigma
        
        sigma = sigma - diff / vega
        
        # 边界检查
        sigma = max(0.001, min(sigma, 5.0))
    
    return sigma

def implied_volatility_bisection(price, S, K, T, r, option_type='call',
                                  max_iter=100, tol=1e-8):
    """使用二分法计算隐含波动率（更稳健）"""
    low, high = 0.001, 5.0
    
    for i in range(max_iter):
        mid = (low + high) / 2
        bs_price = black_scholes(S, K, T, r, mid, option_type)
        
        if abs(bs_price - price) < tol:
            return mid
        
        if bs_price < price:
            low = mid
        else:
            high = mid
    
    return mid

# 示例：从期权价格反推隐含波动率
S, K, T, r = 100, 100, 0.25, 0.05
market_price = 5.5  # 市场价格

iv = implied_volatility(market_price, S, K, T, r, 'call')
print(f"隐含波动率: {iv:.4f} ({iv*100:.2f}%)")

# 验证
bs_price = black_scholes(S, K, T, r, iv, 'call')
print(f"BS价格验证: {bs_price:.4f} (市场价格: {market_price:.4f})")
```

### 3.3 波动率曲面

波动率曲面描述IV如何随行权价和到期时间变化。

```python
def create_volatility_surface():
    """创建波动率曲面示例"""
    S, r = 100, 0.05
    
    # 行权价范围（moneyness）
    moneyness = np.linspace(0.8, 1.2, 20)  # K/S
    strikes = moneyness * S
    
    # 到期时间范围
    maturities = np.array([0.083, 0.25, 0.5, 1.0])  # 1月, 3月, 6月, 1年
    
    # 模拟波动率曲面（实际中从市场数据获取）
    # 使用SABR/SVI等参数化模型或直接插值市场数据
    
    # 这里使用简化的微笑模型
    def vol_smile(K, T, S):
        # 简化的波动率微笑
        atm_vol = 0.2
        skew = -0.1  # 负偏斜
        curvature = 0.05
        
        log_moneyness = np.log(K / S)
        vol = atm_vol + skew * log_moneyness + curvature * log_moneyness**2
        
        # 期限结构
        vol *= np.sqrt(0.25 / T) ** 0.1
        
        return vol
    
    # 构建曲面数据
    vol_surface = np.zeros((len(maturities), len(strikes)))
    
    for i, T in enumerate(maturities):
        for j, K in enumerate(strikes):
            vol_surface[i, j] = vol_smile(K, T, S)
    
    # 3D可视化
    from mpl_toolkits.mplot3d import Axes3D
    
    K_mesh, T_mesh = np.meshgrid(strikes, maturities)
    
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    surf = ax.plot_surface(K_mesh, T_mesh, vol_surface * 100, 
                           cmap='viridis', alpha=0.8)
    
    ax.set_xlabel('Strike Price')
    ax.set_ylabel('Maturity (years)')
    ax.set_zlabel('Implied Volatility (%)')
    ax.set_title('Volatility Surface')
    
    plt.colorbar(surf, shrink=0.5, aspect=10)
    plt.savefig('vol_surface.png', dpi=150)
    plt.close()
    
    return vol_surface

create_volatility_surface()
```

## 四、二叉树定价

### 4.1 CRR模型

Cox-Ross-Rubinstein二叉树模型：

- 上涨因子：\(u = e^{\sigma\sqrt{\Delta t}}\)
- 下跌因子：\(d = 1/u = e^{-\sigma\sqrt{\Delta t}}\)
- 风险中性概率：\(p = \frac{e^{r\Delta t} - d}{u - d}\)

```python
def binomial_tree_european(S, K, T, r, sigma, N, option_type='call'):
    """欧式期权二叉树定价
    
    Args:
        S: 标的价格
        K: 行权价
        T: 到期时间
        r: 无风险利率
        sigma: 波动率
        N: 步数
        option_type: 'call' 或 'put'
    
    Returns:
        期权价格
    """
    dt = T / N
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp(r * dt) - d) / (u - d)
    
    # 到期时的股票价格
    ST = np.array([S * u**j * d**(N-j) for j in range(N+1)])
    
    # 到期时的期权价值
    if option_type == 'call':
        V = np.maximum(ST - K, 0)
    else:
        V = np.maximum(K - ST, 0)
    
    # 反向归纳
    discount = np.exp(-r * dt)
    for i in range(N-1, -1, -1):
        V = discount * (p * V[1:] + (1-p) * V[:-1])
    
    return V[0]

def binomial_tree_american(S, K, T, r, sigma, N, option_type='call'):
    """美式期权二叉树定价"""
    dt = T / N
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp(r * dt) - d) / (u - d)
    discount = np.exp(-r * dt)
    
    # 构建价格树
    price_tree = np.zeros((N+1, N+1))
    for i in range(N+1):
        for j in range(i+1):
            price_tree[j, i] = S * u**j * d**(i-j)
    
    # 计算到期收益
    option_tree = np.zeros((N+1, N+1))
    for j in range(N+1):
        if option_type == 'call':
            option_tree[j, N] = max(price_tree[j, N] - K, 0)
        else:
            option_tree[j, N] = max(K - price_tree[j, N], 0)
    
    # 反向归纳，考虑提前行权
    for i in range(N-1, -1, -1):
        for j in range(i+1):
            hold_value = discount * (p * option_tree[j+1, i+1] + 
                                     (1-p) * option_tree[j, i+1])
            
            if option_type == 'call':
                exercise_value = price_tree[j, i] - K
            else:
                exercise_value = K - price_tree[j, i]
            
            option_tree[j, i] = max(hold_value, exercise_value)
    
    return option_tree[0, 0]

# 比较定价结果
S, K, T, r, sigma = 100, 100, 1, 0.05, 0.2

bs_call = black_scholes(S, K, T, r, sigma, 'call')
bs_put = black_scholes(S, K, T, r, sigma, 'put')

print("定价比较:")
print(f"{'方法':<20} {'看涨':<12} {'看跌':<12}")
print("-" * 44)
print(f"{'Black-Scholes':<20} {bs_call:<12.4f} {bs_put:<12.4f}")

for N in [10, 50, 100, 500]:
    tree_call = binomial_tree_european(S, K, T, r, sigma, N, 'call')
    tree_put = binomial_tree_european(S, K, T, r, sigma, N, 'put')
    print(f"{'Binomial (N='+str(N)+')':<20} {tree_call:<12.4f} {tree_put:<12.4f}")

print("\n美式看跌期权（提前行权价值）:")
american_put = binomial_tree_american(S, K, T, r, sigma, 500, 'put')
european_put = binomial_tree_european(S, K, T, r, sigma, 500, 'put')
print(f"美式看跌: {american_put:.4f}")
print(f"欧式看跌: {european_put:.4f}")
print(f"提前行权溢价: {american_put - european_put:.4f}")
```

### 4.2 Greeks的数值计算

```python
def numerical_greeks(S, K, T, r, sigma, option_type='call', 
                     dS=0.01, dT=1/365, dsigma=0.01, dr=0.0001):
    """数值计算Greeks（有限差分法）"""
    
    price = black_scholes(S, K, T, r, sigma, option_type)
    
    # Delta: 中心差分
    price_up = black_scholes(S + dS, K, T, r, sigma, option_type)
    price_down = black_scholes(S - dS, K, T, r, sigma, option_type)
    delta = (price_up - price_down) / (2 * dS)
    
    # Gamma: 二阶中心差分
    gamma = (price_up - 2 * price + price_down) / (dS ** 2)
    
    # Theta: 向前差分（时间减少）
    price_later = black_scholes(S, K, T - dT, r, sigma, option_type)
    theta = (price_later - price) / dT
    
    # Vega: 中心差分
    price_vol_up = black_scholes(S, K, T, r, sigma + dsigma, option_type)
    price_vol_down = black_scholes(S, K, T, r, sigma - dsigma, option_type)
    vega = (price_vol_up - price_vol_down) / (2 * dsigma * 100)
    
    # Rho: 中心差分
    price_r_up = black_scholes(S, K, T, r + dr, sigma, option_type)
    price_r_down = black_scholes(S, K, T, r - dr, sigma, option_type)
    rho = (price_r_up - price_r_down) / (2 * dr * 100)
    
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
        'rho': rho
    }

# 比较解析和数值Greeks
S, K, T, r, sigma = 100, 100, 0.25, 0.05, 0.2

analytical = calculate_greeks(S, K, T, r, sigma, 'call')
numerical = numerical_greeks(S, K, T, r, sigma, 'call')

print("Greeks比较 (解析 vs 数值):")
print(f"{'Greek':<10} {'解析':<12} {'数值':<12} {'差异':<12}")
print("-" * 46)
for key in analytical:
    diff = abs(analytical[key] - numerical[key])
    print(f"{key:<10} {analytical[key]:<12.6f} {numerical[key]:<12.6f} {diff:<12.2e}")
```

## 五、Delta对冲

### 5.1 离散对冲模拟

```python
def simulate_delta_hedging(S0, K, T, r, sigma, N_hedge, num_sims=10000):
    """模拟Delta对冲策略
    
    Args:
        S0: 初始股价
        K: 行权价
        T: 到期时间
        r: 无风险利率
        sigma: 波动率
        N_hedge: 对冲次数
        num_sims: 模拟次数
    
    Returns:
        对冲误差分布
    """
    dt = T / N_hedge
    sqrt_dt = np.sqrt(dt)
    discount = np.exp(-r * dt)
    
    hedging_errors = np.zeros(num_sims)
    
    for sim in range(num_sims):
        # 初始化
        S = S0
        option_price = black_scholes(S, K, T, r, sigma, 'call')
        
        # 初始头寸：收到期权费，买入Delta份股票
        delta = calculate_greeks(S, K, T, r, sigma, 'call')['delta']
        cash = option_price - delta * S  # 借入现金
        stock_position = delta
        
        # 模拟股价路径和对冲
        for i in range(N_hedge):
            tau = T - i * dt  # 剩余时间
            
            # 股价演化
            dW = np.random.normal(0, sqrt_dt)
            S = S * np.exp((r - 0.5 * sigma**2) * dt + sigma * dW)
            
            if i < N_hedge - 1:
                tau_new = tau - dt
                new_delta = calculate_greeks(S, K, tau_new, r, sigma, 'call')['delta']
                
                # 调整对冲
                delta_change = new_delta - stock_position
                cash = cash * np.exp(r * dt) - delta_change * S
                stock_position = new_delta
            else:
                # 最后一步
                cash = cash * np.exp(r * dt)
        
        # 到期收益
        portfolio_value = cash + stock_position * S
        option_payoff = max(S - K, 0)
        
        hedging_errors[sim] = portfolio_value - option_payoff
    
    return hedging_errors

# 分析对冲效果
errors = simulate_delta_hedging(100, 100, 0.25, 0.05, 0.2, N_hedge=63, num_sims=10000)

print("Delta对冲结果:")
print(f"  平均误差: {errors.mean():.4f}")
print(f"  误差标准差: {errors.std():.4f}")
print(f"  误差范围: [{errors.min():.4f}, {errors.max():.4f}]")

# 不同对冲频率的比较
print("\n对冲频率影响:")
for N in [5, 10, 21, 63, 252]:
    errors = simulate_delta_hedging(100, 100, 0.25, 0.05, 0.2, N_hedge=N, num_sims=1000)
    print(f"  N={N:3d}: 平均={errors.mean():>7.4f}, 标准差={errors.std():.4f}")
```

## 六、面试常见问题

### Q1: 解释Put-Call Parity

**答案**：Put-Call Parity是欧式期权的基本关系：

\[C - P = S - Ke^{-rT}\]

直观解释：看涨期权加上行权价现金等于看跌期权加上股票。

### Q2: 为什么Gamma总是正的？

**答案**：Gamma表示Delta对股价的敏感度。期权的凸性保证了无论股价涨跌，期权持有者都能获益：
- 股价上涨时，Delta增大，获利加速
- 股价下跌时，Delta减小，损失减速

这种凸性（正Gamma）是期权的核心价值来源之一。

### Q3: 什么是Gamma Scalping？

**答案**：Gamma scalping是利用正Gamma进行Delta对冲获利的策略：
- 持有正Gamma头寸（如持有期权）
- 保持Delta中性
- 股价波动时，对冲调整产生利润
- 需要实际波动率高于隐含波动率才能盈利

## 总结

期权定价的核心要点：

1. **Black-Scholes**：欧式期权定价的基准模型
2. **Greeks**：理解期权价值的敏感性
3. **隐含波动率**：市场对未来波动的预期
4. **数值方法**：二叉树处理复杂期权
5. **对冲**：Delta对冲是风险管理的基础

掌握这些知识是期权交易和风险管理的基础。

---

## 相关文章

- [上一篇：金融数学基础(HFT)](/articles/math/math-09-金融数学基础/)
- [下一篇：时间序列分析详解(HFT)](/articles/math/math-11-时间序列分析详解/)
