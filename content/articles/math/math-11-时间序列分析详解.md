+++
title = "时间序列分析详解"
description = "深入讲解金融时间序列分析：AR/MA/ARIMA/SARIMA、GARCH/EGARCH、协整检验、均值回归、Kalman滤波与状态空间模型"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["时间序列", "ARIMA", "GARCH", "协整", "量化"]
+++

# 时间序列分析详解

## 概述

时间序列分析是量化金融的核心工具。从价格预测到波动率建模，从配对交易到风险管理，都离不开对时间序列的深入理解。本文系统介绍金融时间序列的主要模型和方法。

## 一、平稳性与基础概念

### 1.1 平稳性定义

**严格平稳**：联合分布不随时间改变
**弱平稳（协方差平稳）**：
- 均值恒定：\(\mathbb{E}[X_t] = \mu\)
- 方差恒定：\(\text{Var}(X_t) = \sigma^2\)
- 自协方差只依赖于时间差：\(\text{Cov}(X_t, X_{t+h}) = \gamma(h)\)

### 1.2 平稳性检验

```python
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
import matplotlib.pyplot as plt

def test_stationarity(series, name="Series"):
    """平稳性检验
    
    Args:
        series: 时间序列
        name: 序列名称
    """
    print(f"=== {name} 平稳性检验 ===\n")
    
    # ADF检验 (H0: 存在单位根，非平稳)
    adf_result = adfuller(series.dropna(), autolag='AIC')
    print("ADF检验:")
    print(f"  统计量: {adf_result[0]:.4f}")
    print(f"  p值: {adf_result[1]:.4f}")
    print(f"  临界值: 1%={adf_result[4]['1%']:.4f}, "
          f"5%={adf_result[4]['5%']:.4f}, "
          f"10%={adf_result[4]['10%']:.4f}")
    adf_stationary = adf_result[1] < 0.05
    print(f"  结论: {'平稳' if adf_stationary else '非平稳'}")
    
    print()
    
    # KPSS检验 (H0: 平稳)
    kpss_result = kpss(series.dropna(), regression='c', nlags='auto')
    print("KPSS检验:")
    print(f"  统计量: {kpss_result[0]:.4f}")
    print(f"  p值: {kpss_result[1]:.4f}")
    kpss_stationary = kpss_result[1] > 0.05
    print(f"  结论: {'平稳' if kpss_stationary else '非平稳'}")
    
    return adf_stationary and kpss_stationary

# 示例
np.random.seed(42)
n = 500

# 平稳序列
stationary = np.cumsum(np.random.randn(n) * 0.1) * 0 + np.random.randn(n)

# 非平稳序列（随机游走）
random_walk = np.cumsum(np.random.randn(n))

test_stationarity(pd.Series(stationary), "平稳序列")
print("\n" + "="*50 + "\n")
test_stationarity(pd.Series(random_walk), "随机游走")
```

### 1.3 自相关函数（ACF）和偏自相关函数（PACF）

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import acf, pacf

def analyze_acf_pacf(series, lags=40):
    """ACF和PACF分析"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    plot_acf(series.dropna(), lags=lags, ax=axes[0])
    axes[0].set_title('自相关函数 (ACF)')
    
    plot_pacf(series.dropna(), lags=lags, ax=axes[1])
    axes[1].set_title('偏自相关函数 (PACF)')
    
    plt.tight_layout()
    plt.savefig('acf_pacf.png', dpi=150)
    plt.close()

# ACF/PACF模式识别：
# AR(p): ACF缓慢衰减，PACF在p阶后截尾
# MA(q): ACF在q阶后截尾，PACF缓慢衰减
# ARMA(p,q): ACF和PACF都缓慢衰减
```

## 二、ARIMA模型

### 2.1 AR模型

自回归模型 AR(p)：

\[X_t = c + \phi_1 X_{t-1} + \phi_2 X_{t-2} + ... + \phi_p X_{t-p} + \epsilon_t\]

```python
from statsmodels.tsa.arima.model import ARIMA

def simulate_ar(phi, c=0, sigma=1, n=1000):
    """模拟AR(p)过程"""
    p = len(phi)
    X = np.zeros(n)
    X[:p] = np.random.randn(p) * sigma
    
    for t in range(p, n):
        X[t] = c + sum(phi[i] * X[t-1-i] for i in range(p)) + np.random.randn() * sigma
    
    return X

# 模拟AR(2)
phi = [0.5, 0.3]
ar_series = simulate_ar(phi, n=500)

# 拟合AR模型
model = ARIMA(ar_series, order=(2, 0, 0))
result = model.fit()
print(result.summary())

print(f"\n真实参数: φ₁={phi[0]}, φ₂={phi[1]}")
print(f"估计参数: φ₁={result.arparams[0]:.4f}, φ₂={result.arparams[1]:.4f}")
```

### 2.2 MA模型

移动平均模型 MA(q)：

\[X_t = \mu + \epsilon_t + \theta_1 \epsilon_{t-1} + ... + \theta_q \epsilon_{t-q}\]

```python
def simulate_ma(theta, mu=0, sigma=1, n=1000):
    """模拟MA(q)过程"""
    q = len(theta)
    epsilon = np.random.randn(n + q) * sigma
    X = np.zeros(n)
    
    for t in range(n):
        X[t] = mu + epsilon[t + q] + sum(theta[i] * epsilon[t + q - 1 - i] for i in range(q))
    
    return X

# 模拟MA(2)
theta = [0.6, -0.3]
ma_series = simulate_ma(theta, n=500)

# 拟合MA模型
model = ARIMA(ma_series, order=(0, 0, 2))
result = model.fit()
print(f"真实参数: θ₁={theta[0]}, θ₂={theta[1]}")
print(f"估计参数: θ₁={result.maparams[0]:.4f}, θ₂={result.maparams[1]:.4f}")
```

### 2.3 ARIMA模型

ARIMA(p, d, q)：对d阶差分后的序列拟合ARMA(p, q)

```python
def fit_arima(series, max_p=5, max_d=2, max_q=5):
    """自动选择ARIMA阶数（基于AIC）"""
    best_aic = np.inf
    best_order = None
    best_model = None
    
    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                try:
                    model = ARIMA(series, order=(p, d, q))
                    result = model.fit()
                    if result.aic < best_aic:
                        best_aic = result.aic
                        best_order = (p, d, q)
                        best_model = result
                except:
                    continue
    
    print(f"最优ARIMA阶数: {best_order}")
    print(f"AIC: {best_aic:.2f}")
    
    return best_model, best_order

# 股票收益率建模示例
np.random.seed(42)
# 模拟带均值回归的收益率
returns = np.zeros(500)
for t in range(1, 500):
    returns[t] = 0.1 * (-returns[t-1]) + np.random.randn() * 0.02

model, order = fit_arima(returns, max_p=3, max_d=1, max_q=3)
```

### 2.4 SARIMA（季节性ARIMA）

SARIMA(p, d, q)(P, D, Q)s 处理季节性模式：

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

def fit_sarima(series, seasonal_period=12):
    """拟合SARIMA模型"""
    # 示例：SARIMA(1,1,1)(1,1,1,12)
    model = SARIMAX(series,
                    order=(1, 1, 1),
                    seasonal_order=(1, 1, 1, seasonal_period))
    result = model.fit(disp=False)
    return result

# 季节性数据示例
t = np.arange(500)
seasonal_data = (np.sin(2 * np.pi * t / 12) * 10 + 
                 0.1 * t + 
                 np.cumsum(np.random.randn(500) * 0.5))
```

## 三、GARCH波动率模型

### 3.1 GARCH(p,q)模型

GARCH模型捕捉波动率聚集现象：

\[r_t = \mu + \epsilon_t, \quad \epsilon_t = \sigma_t z_t, \quad z_t \sim N(0,1)\]

\[\sigma_t^2 = \omega + \sum_{i=1}^{q} \alpha_i \epsilon_{t-i}^2 + \sum_{j=1}^{p} \beta_j \sigma_{t-j}^2\]

```python
from arch import arch_model

def fit_garch(returns, p=1, q=1):
    """拟合GARCH模型
    
    Args:
        returns: 收益率序列
        p: GARCH阶数
        q: ARCH阶数
    """
    # 创建GARCH模型
    model = arch_model(returns, vol='Garch', p=p, q=q, mean='Constant')
    result = model.fit(disp='off')
    
    print(result.summary())
    
    # 提取条件波动率
    conditional_vol = result.conditional_volatility
    
    return result, conditional_vol

# 模拟GARCH(1,1)
def simulate_garch(omega, alpha, beta, n=1000):
    """模拟GARCH(1,1)过程"""
    returns = np.zeros(n)
    sigma2 = np.zeros(n)
    sigma2[0] = omega / (1 - alpha - beta)  # 无条件方差
    
    for t in range(1, n):
        sigma2[t] = omega + alpha * returns[t-1]**2 + beta * sigma2[t-1]
        returns[t] = np.sqrt(sigma2[t]) * np.random.randn()
    
    return returns, np.sqrt(sigma2)

# 模拟并拟合
omega, alpha, beta = 0.00001, 0.1, 0.85
returns, true_vol = simulate_garch(omega, alpha, beta, n=2000)

print("GARCH(1,1)参数估计:")
print(f"真实参数: ω={omega:.6f}, α={alpha:.2f}, β={beta:.2f}")
result, est_vol = fit_garch(returns * 100, p=1, q=1)  # 放大100倍便于估计
```

### 3.2 EGARCH模型

EGARCH捕捉杠杆效应（负收益导致更高波动率）：

\[\ln(\sigma_t^2) = \omega + \sum_{i=1}^{q} \alpha_i g(z_{t-i}) + \sum_{j=1}^{p} \beta_j \ln(\sigma_{t-j}^2)\]

其中 \(g(z) = \theta z + \gamma(|z| - \mathbb{E}[|z|])\)

```python
def fit_egarch(returns, p=1, q=1):
    """拟合EGARCH模型"""
    model = arch_model(returns, vol='EGARCH', p=p, q=q, mean='Constant')
    result = model.fit(disp='off')
    
    print("EGARCH模型结果:")
    print(f"  ω = {result.params['omega']:.4f}")
    print(f"  α = {result.params['alpha[1]']:.4f}")
    print(f"  γ = {result.params['gamma[1]']:.4f}")  # 杠杆效应
    print(f"  β = {result.params['beta[1]']:.4f}")
    
    return result

# 杠杆效应解读：
# γ < 0 表示负收益增加波动率（典型股市行为）
```

### 3.3 波动率预测

```python
def forecast_volatility(model_result, horizon=10):
    """预测未来波动率"""
    forecast = model_result.forecast(horizon=horizon)
    
    # 预测的方差
    variance_forecast = forecast.variance.iloc[-1]
    volatility_forecast = np.sqrt(variance_forecast)
    
    print(f"未来{horizon}期波动率预测:")
    for i, vol in enumerate(volatility_forecast):
        print(f"  t+{i+1}: {vol:.4f}")
    
    return volatility_forecast

# forecast_volatility(result, horizon=5)
```

## 四、协整与配对交易

### 4.1 协整概念

两个非平稳序列 \(X_t\) 和 \(Y_t\) 是协整的，如果存在 \(\beta\) 使得：

\[Y_t - \beta X_t \sim I(0) \quad \text{(平稳)}\]

### 4.2 协整检验

```python
from statsmodels.tsa.stattools import coint
from statsmodels.regression.linear_model import OLS

def test_cointegration(y, x):
    """Engle-Granger两步法协整检验"""
    
    # 第一步：回归
    model = OLS(y, np.column_stack([np.ones(len(x)), x]))
    result = model.fit()
    residuals = result.resid
    beta = result.params[1]
    
    print(f"协整回归: Y = {result.params[0]:.4f} + {beta:.4f} * X")
    
    # 第二步：检验残差平稳性
    adf_result = adfuller(residuals)
    
    print(f"\n残差ADF检验:")
    print(f"  统计量: {adf_result[0]:.4f}")
    print(f"  p值: {adf_result[1]:.4f}")
    
    # 使用statsmodels的协整检验
    coint_stat, pvalue, crit_values = coint(y, x)
    print(f"\n协整检验:")
    print(f"  统计量: {coint_stat:.4f}")
    print(f"  p值: {pvalue:.4f}")
    
    is_cointegrated = pvalue < 0.05
    print(f"  结论: {'存在协整关系' if is_cointegrated else '不存在协整关系'}")
    
    return is_cointegrated, beta, residuals

# 模拟协整对
np.random.seed(42)
n = 500

# 共同趋势
common_trend = np.cumsum(np.random.randn(n) * 0.5)

# 两个协整序列
x = common_trend + np.random.randn(n) * 0.3
y = 0.5 + 1.5 * common_trend + np.random.randn(n) * 0.3

is_coint, beta, spread = test_cointegration(y, x)
```

### 4.3 配对交易策略

```python
class PairsTrading:
    """配对交易策略"""
    
    def __init__(self, lookback=60, entry_threshold=2.0, exit_threshold=0.5):
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
    
    def calculate_spread(self, y, x, beta):
        """计算价差"""
        return y - beta * x
    
    def calculate_zscore(self, spread):
        """计算z-score"""
        mean = pd.Series(spread).rolling(self.lookback).mean()
        std = pd.Series(spread).rolling(self.lookback).std()
        zscore = (spread - mean) / std
        return zscore
    
    def generate_signals(self, y, x, beta):
        """生成交易信号"""
        spread = self.calculate_spread(y, x, beta)
        zscore = self.calculate_zscore(spread)
        
        signals = np.zeros(len(spread))
        position = 0
        
        for t in range(self.lookback, len(spread)):
            if position == 0:
                # 入场信号
                if zscore.iloc[t] > self.entry_threshold:
                    signals[t] = -1  # 做空spread (卖Y买X)
                    position = -1
                elif zscore.iloc[t] < -self.entry_threshold:
                    signals[t] = 1   # 做多spread (买Y卖X)
                    position = 1
            else:
                # 出场信号
                if abs(zscore.iloc[t]) < self.exit_threshold:
                    signals[t] = 0
                    position = 0
                else:
                    signals[t] = position
        
        return signals, spread, zscore
    
    def backtest(self, y, x, beta):
        """回测配对交易策略"""
        signals, spread, zscore = self.generate_signals(y, x, beta)
        
        # 计算收益
        spread_returns = pd.Series(spread).diff()
        strategy_returns = signals[:-1] * spread_returns.iloc[1:].values
        
        # 性能指标
        cumulative_returns = np.cumsum(strategy_returns[~np.isnan(strategy_returns)])
        sharpe = np.mean(strategy_returns) / np.std(strategy_returns) * np.sqrt(252)
        
        print(f"配对交易回测结果:")
        print(f"  总收益: {cumulative_returns[-1]:.4f}")
        print(f"  夏普比率: {sharpe:.4f}")
        print(f"  交易次数: {np.sum(np.abs(np.diff(signals)) > 0)}")
        
        return strategy_returns, cumulative_returns

# 回测
strategy = PairsTrading(lookback=30, entry_threshold=2.0, exit_threshold=0.5)
returns, cum_returns = strategy.backtest(y, x, beta)
```

## 五、Kalman滤波

### 5.1 状态空间模型

状态方程：\(x_t = F x_{t-1} + w_t, \quad w_t \sim N(0, Q)\)

观测方程：\(y_t = H x_t + v_t, \quad v_t \sim N(0, R)\)

### 5.2 Kalman滤波实现

```python
class KalmanFilter:
    """Kalman滤波器"""
    
    def __init__(self, F, H, Q, R, x0, P0):
        """
        Args:
            F: 状态转移矩阵
            H: 观测矩阵
            Q: 过程噪声协方差
            R: 观测噪声协方差
            x0: 初始状态
            P0: 初始协方差
        """
        self.F = np.array(F)
        self.H = np.array(H)
        self.Q = np.array(Q)
        self.R = np.array(R)
        self.x = np.array(x0)
        self.P = np.array(P0)
    
    def predict(self):
        """预测步骤"""
        # 状态预测
        self.x = self.F @ self.x
        # 协方差预测
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return self.x.copy(), self.P.copy()
    
    def update(self, y):
        """更新步骤"""
        # 创新（观测残差）
        innovation = y - self.H @ self.x
        # 创新协方差
        S = self.H @ self.P @ self.H.T + self.R
        # Kalman增益
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # 状态更新
        self.x = self.x + K @ innovation
        # 协方差更新
        I = np.eye(len(self.x))
        self.P = (I - K @ self.H) @ self.P
        
        return self.x.copy(), self.P.copy(), K
    
    def filter(self, observations):
        """对整个序列进行滤波"""
        n = len(observations)
        state_dim = len(self.x)
        
        filtered_states = np.zeros((n, state_dim))
        filtered_covs = np.zeros((n, state_dim, state_dim))
        
        for t, y in enumerate(observations):
            self.predict()
            self.update(np.array([y]))
            filtered_states[t] = self.x
            filtered_covs[t] = self.P
        
        return filtered_states, filtered_covs

# 示例：使用Kalman滤波估计动态beta
def kalman_dynamic_beta():
    """使用Kalman滤波估计动态对冲比率"""
    np.random.seed(42)
    n = 500
    
    # 真实的时变beta
    true_beta = 1.0 + 0.5 * np.sin(2 * np.pi * np.arange(n) / 100)
    
    # 模拟数据
    x = np.cumsum(np.random.randn(n))
    noise = np.random.randn(n) * 0.5
    y = true_beta * x + noise
    
    # Kalman滤波设置
    # 状态: [alpha, beta]
    F = np.eye(2)  # 随机游走假设
    H = np.array([[1, 0]])  # 初始化，会动态更新
    Q = np.diag([0.001, 0.001])  # 过程噪声
    R = np.array([[0.25]])  # 观测噪声
    x0 = np.array([0, 1])  # 初始状态
    P0 = np.eye(2)  # 初始协方差
    
    kf = KalmanFilter(F, H, Q, R, x0, P0)
    
    estimated_beta = np.zeros(n)
    
    for t in range(n):
        # 更新观测矩阵
        kf.H = np.array([[1, x[t]]])
        
        kf.predict()
        kf.update(np.array([y[t]]))
        
        estimated_beta[t] = kf.x[1]
    
    # 比较结果
    print("Kalman滤波动态Beta估计:")
    print(f"  真实Beta范围: [{true_beta.min():.2f}, {true_beta.max():.2f}]")
    print(f"  估计Beta范围: [{estimated_beta.min():.2f}, {estimated_beta.max():.2f}]")
    print(f"  RMSE: {np.sqrt(np.mean((true_beta - estimated_beta)**2)):.4f}")
    
    return true_beta, estimated_beta

true_beta, est_beta = kalman_dynamic_beta()
```

## 六、均值回归

### 6.1 Ornstein-Uhlenbeck过程

均值回归过程的连续时间模型：

\[dX_t = \kappa(\mu - X_t)dt + \sigma dW_t\]

参数估计：

```python
def estimate_ou_parameters(series, dt=1/252):
    """估计OU过程参数
    
    Args:
        series: 时间序列
        dt: 时间步长（默认日频）
    
    Returns:
        kappa: 均值回归速度
        mu: 长期均值
        sigma: 波动率
    """
    n = len(series)
    
    # AR(1)回归: X_t = a + b * X_{t-1} + epsilon
    X = series[:-1]
    Y = series[1:]
    
    # OLS估计
    X_with_const = np.column_stack([np.ones(len(X)), X])
    params = np.linalg.lstsq(X_with_const, Y, rcond=None)[0]
    a, b = params
    
    # 残差标准差
    residuals = Y - (a + b * X)
    sigma_residual = np.std(residuals)
    
    # 转换为OU参数
    kappa = -np.log(b) / dt
    mu = a / (1 - b)
    sigma = sigma_residual * np.sqrt(-2 * np.log(b) / (dt * (1 - b**2)))
    
    # 半衰期
    half_life = np.log(2) / kappa
    
    print(f"OU过程参数估计:")
    print(f"  均值回归速度 (κ): {kappa:.4f}")
    print(f"  长期均值 (μ): {mu:.4f}")
    print(f"  波动率 (σ): {sigma:.4f}")
    print(f"  半衰期: {half_life:.2f} 期")
    
    return kappa, mu, sigma, half_life

# 示例
np.random.seed(42)
# 模拟OU过程
kappa_true, mu_true, sigma_true = 5, 0, 0.3
dt = 1/252
n = 1000

ou_series = np.zeros(n)
for t in range(1, n):
    ou_series[t] = ou_series[t-1] + kappa_true * (mu_true - ou_series[t-1]) * dt + \
                   sigma_true * np.sqrt(dt) * np.random.randn()

kappa_est, mu_est, sigma_est, hl = estimate_ou_parameters(ou_series, dt)
print(f"\n真实参数: κ={kappa_true}, μ={mu_true}, σ={sigma_true}")
```

### 6.2 均值回归策略

```python
class MeanReversionStrategy:
    """均值回归策略"""
    
    def __init__(self, lookback=20, entry_zscore=2.0, exit_zscore=0.5):
        self.lookback = lookback
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
    
    def generate_signals(self, prices):
        """生成交易信号"""
        # 计算z-score
        rolling_mean = pd.Series(prices).rolling(self.lookback).mean()
        rolling_std = pd.Series(prices).rolling(self.lookback).std()
        zscore = (prices - rolling_mean) / rolling_std
        
        signals = np.zeros(len(prices))
        position = 0
        
        for t in range(self.lookback, len(prices)):
            z = zscore.iloc[t]
            
            if position == 0:
                if z > self.entry_zscore:
                    signals[t] = -1  # 做空
                    position = -1
                elif z < -self.entry_zscore:
                    signals[t] = 1   # 做多
                    position = 1
            elif position == 1:
                if z > -self.exit_zscore:
                    signals[t] = 0
                    position = 0
                else:
                    signals[t] = 1
            elif position == -1:
                if z < self.exit_zscore:
                    signals[t] = 0
                    position = 0
                else:
                    signals[t] = -1
        
        return signals, zscore

# 策略回测
strategy = MeanReversionStrategy(lookback=20, entry_zscore=2.0, exit_zscore=0.5)
signals, zscore = strategy.generate_signals(ou_series)
```

## 七、面试常见问题

### Q1: 如何判断一个序列是否适合均值回归策略？

**答案**：
1. 进行平稳性检验（ADF/KPSS）
2. 估计OU参数，检查半衰期是否合理（太长无法交易，太短交易成本过高）
3. 检验均值回归速度κ是否显著为正
4. 分析历史数据中均值回归的稳定性

### Q2: GARCH模型的持久性是什么？

**答案**：GARCH(1,1)的持久性定义为 \(\alpha + \beta\)。
- 接近1表示波动率冲击持续时间长（高持久性）
- 等于1时为IGARCH（积分GARCH），冲击永久影响
- 典型股票指数的持久性约为0.95-0.99

### Q3: 解释协整和相关性的区别

**答案**：
- **相关性**：衡量两个变量同时变动的程度，可以是平稳或非平稳序列
- **协整**：特指非平稳序列的长期均衡关系，线性组合是平稳的
- **关键区别**：两个序列可以高度相关但不协整（如两个独立的随机游走）；也可以协整但短期相关性较低

## 总结

时间序列分析的核心要点：

1. **平稳性**：大多数模型要求平稳性，必须先检验
2. **ARIMA**：预测和建模的基础工具
3. **GARCH**：捕捉波动率聚集，风险管理必备
4. **协整**：配对交易的理论基础
5. **Kalman滤波**：处理时变参数的强大工具
6. **均值回归**：量化策略的重要来源

掌握这些工具是进行量化研究和策略开发的基础。
