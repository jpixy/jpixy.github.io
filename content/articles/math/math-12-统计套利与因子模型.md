+++
title = "12.统计套利与因子模型(HFT)"
description = "深入讲解统计套利与因子模型：配对交易数学、PCA/ICA、协方差估计、Barra风险模型、因子分析与组合优化"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["统计套利", "因子模型", "PCA", "风险模型", "量化", "HFT"]
+++

# 统计套利与因子模型(HFT)

## 概述

统计套利利用统计方法识别价格偏离均衡的资产，通过买卖实现收益。因子模型则提供了理解和分解资产收益的框架。本文深入介绍这两个量化金融的核心领域。

## 一、配对交易数学

### 1.1 距离法配对选择

```python
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import StandardScaler

def find_pairs_distance(prices, n_pairs=10):
    """使用距离法寻找配对
    
    Args:
        prices: DataFrame, 股票价格矩阵
        n_pairs: 返回的配对数量
    
    Returns:
        配对列表及其距离
    """
    # 标准化价格
    scaler = StandardScaler()
    normalized = scaler.fit_transform(prices)
    
    # 计算欧氏距离
    distances = pdist(normalized.T, metric='euclidean')
    dist_matrix = squareform(distances)
    
    # 提取上三角矩阵（避免重复）
    n = len(prices.columns)
    pairs = []
    
    for i in range(n):
        for j in range(i+1, n):
            pairs.append({
                'stock1': prices.columns[i],
                'stock2': prices.columns[j],
                'distance': dist_matrix[i, j]
            })
    
    # 按距离排序
    pairs = sorted(pairs, key=lambda x: x['distance'])
    
    return pairs[:n_pairs]

# 示例
np.random.seed(42)
n_stocks, n_days = 20, 252

# 模拟股票价格
common_factor = np.cumsum(np.random.randn(n_days) * 0.01)
prices_data = {}

for i in range(n_stocks):
    beta = np.random.uniform(0.8, 1.2)
    idio = np.cumsum(np.random.randn(n_days) * 0.02)
    prices_data[f'Stock_{i}'] = 100 * np.exp(beta * common_factor + idio)

prices_df = pd.DataFrame(prices_data)
pairs = find_pairs_distance(prices_df, n_pairs=5)

print("距离法配对结果:")
for p in pairs:
    print(f"  {p['stock1']} - {p['stock2']}: 距离={p['distance']:.4f}")
```

### 1.2 协整法配对选择

```python
from statsmodels.tsa.stattools import coint

def find_pairs_cointegration(prices, significance=0.05):
    """使用协整法寻找配对
    
    Args:
        prices: DataFrame, 股票价格矩阵
        significance: 显著性水平
    
    Returns:
        协整配对列表
    """
    n = len(prices.columns)
    pairs = []
    
    for i in range(n):
        for j in range(i+1, n):
            # 协整检验
            stock1 = prices.iloc[:, i].values
            stock2 = prices.iloc[:, j].values
            
            try:
                score, pvalue, _ = coint(stock1, stock2)
                
                if pvalue < significance:
                    pairs.append({
                        'stock1': prices.columns[i],
                        'stock2': prices.columns[j],
                        'pvalue': pvalue,
                        'score': score
                    })
            except:
                continue
    
    # 按p值排序
    pairs = sorted(pairs, key=lambda x: x['pvalue'])
    
    return pairs

# 创建一些协整对
np.random.seed(42)
n_days = 500

# 真正的协整对
common = np.cumsum(np.random.randn(n_days) * 0.02)
stock_a = common + np.random.randn(n_days) * 0.1
stock_b = 0.5 + 1.5 * common + np.random.randn(n_days) * 0.1

# 非协整对
stock_c = np.cumsum(np.random.randn(n_days) * 0.02)
stock_d = np.cumsum(np.random.randn(n_days) * 0.02)

test_prices = pd.DataFrame({
    'A': stock_a, 'B': stock_b, 
    'C': stock_c, 'D': stock_d
})

coint_pairs = find_pairs_cointegration(test_prices, significance=0.05)
print("\n协整法配对结果:")
for p in coint_pairs:
    print(f"  {p['stock1']} - {p['stock2']}: p值={p['pvalue']:.4f}")
```

### 1.3 最优对冲比率

```python
from sklearn.linear_model import LinearRegression
from statsmodels.regression.linear_model import OLS

def calculate_hedge_ratio(y, x, method='ols'):
    """计算对冲比率
    
    Args:
        y: 目标资产价格
        x: 对冲资产价格
        method: 'ols', 'tls', 'kalman'
    
    Returns:
        对冲比率
    """
    if method == 'ols':
        # 普通最小二乘
        X = np.column_stack([np.ones(len(x)), x])
        model = OLS(y, X).fit()
        return model.params[1]
    
    elif method == 'tls':
        # 总体最小二乘 (TLS)
        # 考虑x和y都有误差
        combined = np.column_stack([x, y])
        mean = combined.mean(axis=0)
        centered = combined - mean
        
        # SVD分解
        U, S, Vt = np.linalg.svd(centered)
        
        # 最小特征值对应的特征向量
        v = Vt[-1]
        beta = -v[0] / v[1]
        
        return beta
    
    elif method == 'kalman':
        # 使用Kalman滤波估计时变beta
        # 简化版本，返回最终估计
        from filterpy.kalman import KalmanFilter
        
        kf = KalmanFilter(dim_x=2, dim_z=1)
        kf.F = np.eye(2)  # 状态转移
        kf.H = np.array([[1, 0]])  # 观测矩阵（动态更新）
        kf.Q = np.eye(2) * 0.001  # 过程噪声
        kf.R = np.array([[1]])  # 观测噪声
        kf.x = np.array([[0], [1]])  # 初始状态 [alpha, beta]
        kf.P = np.eye(2)  # 初始协方差
        
        betas = []
        for t in range(len(x)):
            kf.H = np.array([[1, x[t]]])
            kf.predict()
            kf.update(np.array([y[t]]))
            betas.append(kf.x[1, 0])
        
        return betas[-1], betas

# 比较不同方法
y, x = stock_b, stock_a

beta_ols = calculate_hedge_ratio(y, x, 'ols')
beta_tls = calculate_hedge_ratio(y, x, 'tls')

print(f"\n对冲比率估计:")
print(f"  OLS: {beta_ols:.4f}")
print(f"  TLS: {beta_tls:.4f}")
print(f"  真实: 1.5000")
```

## 二、主成分分析（PCA）

### 2.1 收益率PCA

```python
from sklearn.decomposition import PCA

def pca_returns(returns, n_components=5):
    """对收益率进行PCA分析
    
    Args:
        returns: DataFrame, 收益率矩阵 (T x N)
        n_components: 主成分数量
    
    Returns:
        PCA结果
    """
    # 标准化
    returns_std = (returns - returns.mean()) / returns.std()
    
    # PCA
    pca = PCA(n_components=n_components)
    factors = pca.fit_transform(returns_std)
    
    # 结果分析
    print("PCA分析结果:")
    print(f"  解释方差比:")
    for i, var in enumerate(pca.explained_variance_ratio_):
        print(f"    PC{i+1}: {var:.2%}")
    print(f"  累计解释方差: {pca.explained_variance_ratio_.sum():.2%}")
    
    # 因子载荷
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f'PC{i+1}' for i in range(n_components)],
        index=returns.columns
    )
    
    return pca, factors, loadings

# 模拟股票收益率
np.random.seed(42)
n_stocks, n_days = 50, 252

# 3个因子
market_factor = np.random.randn(n_days) * 0.01
size_factor = np.random.randn(n_days) * 0.008
value_factor = np.random.randn(n_days) * 0.006

returns_data = {}
for i in range(n_stocks):
    beta_m = np.random.uniform(0.8, 1.2)
    beta_s = np.random.uniform(-0.5, 0.5)
    beta_v = np.random.uniform(-0.3, 0.3)
    idio = np.random.randn(n_days) * 0.02
    
    returns_data[f'Stock_{i:02d}'] = (
        beta_m * market_factor + 
        beta_s * size_factor + 
        beta_v * value_factor + 
        idio
    )

returns_df = pd.DataFrame(returns_data)
pca, factors, loadings = pca_returns(returns_df, n_components=5)
```

### 2.2 统计因子构建

```python
def construct_statistical_factors(returns, n_factors=3):
    """构建统计因子
    
    Args:
        returns: 收益率矩阵
        n_factors: 因子数量
    
    Returns:
        因子收益率序列
    """
    pca = PCA(n_components=n_factors)
    
    # 标准化
    returns_std = (returns - returns.mean()) / returns.std()
    
    # 提取因子
    factor_returns = pca.fit_transform(returns_std)
    
    # 因子载荷
    loadings = pca.components_.T
    
    # 因子暴露标准化
    factor_df = pd.DataFrame(
        factor_returns,
        index=returns.index,
        columns=[f'Factor_{i+1}' for i in range(n_factors)]
    )
    
    # 计算因子统计特征
    print("因子统计特征:")
    for col in factor_df.columns:
        sharpe = factor_df[col].mean() / factor_df[col].std() * np.sqrt(252)
        print(f"  {col}: 年化夏普比率 = {sharpe:.2f}")
    
    return factor_df, loadings
```

## 三、独立成分分析（ICA）

### 3.1 ICA因子提取

```python
from sklearn.decomposition import FastICA

def ica_returns(returns, n_components=3):
    """使用ICA提取独立因子
    
    Args:
        returns: 收益率矩阵
        n_components: 独立成分数量
    
    Returns:
        独立成分
    """
    # 标准化
    returns_std = (returns - returns.mean()) / returns.std()
    
    # ICA
    ica = FastICA(n_components=n_components, random_state=42)
    independent_components = ica.fit_transform(returns_std)
    
    # 混合矩阵
    mixing = ica.mixing_
    
    print("ICA分析结果:")
    print(f"  独立成分数量: {n_components}")
    
    # 检验独立性（通过相关性）
    ic_df = pd.DataFrame(independent_components)
    corr = ic_df.corr()
    print(f"  成分相关性矩阵对角线外最大值: {np.abs(corr.values - np.eye(n_components)).max():.4f}")
    
    return independent_components, mixing

# ICA与PCA对比
ic, mixing = ica_returns(returns_df, n_components=3)
```

## 四、协方差估计

### 4.1 样本协方差

```python
def sample_covariance(returns):
    """计算样本协方差矩阵"""
    return returns.cov()

def ewm_covariance(returns, halflife=60):
    """指数加权协方差矩阵"""
    return returns.ewm(halflife=halflife).cov().iloc[-len(returns.columns):]
```

### 4.2 收缩估计

```python
from sklearn.covariance import LedoitWolf, OAS

def shrinkage_covariance(returns, method='ledoit_wolf'):
    """收缩协方差估计
    
    Args:
        returns: 收益率矩阵
        method: 'ledoit_wolf' 或 'oas'
    
    Returns:
        收缩协方差矩阵
    """
    if method == 'ledoit_wolf':
        estimator = LedoitWolf()
    else:
        estimator = OAS()
    
    estimator.fit(returns)
    
    print(f"收缩强度: {estimator.shrinkage_:.4f}")
    
    return estimator.covariance_

# 比较不同估计方法
sample_cov = sample_covariance(returns_df)
shrunk_cov = shrinkage_covariance(returns_df)

print("\n协方差矩阵条件数:")
print(f"  样本协方差: {np.linalg.cond(sample_cov):.2f}")
print(f"  收缩协方差: {np.linalg.cond(shrunk_cov):.2f}")
```

### 4.3 因子模型协方差

```python
def factor_model_covariance(returns, n_factors=3):
    """基于因子模型的协方差估计
    
    Cov = B * Cov(F) * B' + D
    
    Args:
        returns: 收益率矩阵
        n_factors: 因子数量
    
    Returns:
        因子模型协方差矩阵
    """
    # PCA提取因子
    pca = PCA(n_components=n_factors)
    returns_std = (returns - returns.mean()) / returns.std()
    factors = pca.fit_transform(returns_std)
    
    # 因子载荷 (N x K)
    B = pca.components_.T * returns.std().values.reshape(-1, 1)
    
    # 因子协方差 (K x K)
    factor_cov = np.cov(factors.T)
    
    # 残差
    fitted = factors @ pca.components_
    residuals = returns_std.values - fitted
    
    # 特异性方差 (对角矩阵)
    D = np.diag(np.var(residuals, axis=0)) * (returns.std().values ** 2)
    
    # 因子模型协方差
    cov_factor = B @ factor_cov @ B.T + D
    
    return cov_factor, B, factor_cov, D

factor_cov, B, F_cov, D = factor_model_covariance(returns_df, n_factors=3)
print(f"\n因子模型协方差条件数: {np.linalg.cond(factor_cov):.2f}")
```

## 五、Barra风险模型

### 5.1 Barra模型结构

```python
class BarraRiskModel:
    """简化的Barra风险模型"""
    
    def __init__(self, n_style_factors=5):
        self.n_style_factors = n_style_factors
        self.factor_returns = None
        self.factor_cov = None
        self.specific_risk = None
        self.exposures = None
    
    def calculate_exposures(self, market_cap, book_to_price, momentum, 
                           volatility, beta):
        """计算因子暴露
        
        Args:
            各因子的原始值
        
        Returns:
            标准化因子暴露
        """
        # 标准化
        def standardize(x):
            return (x - x.mean()) / x.std()
        
        exposures = pd.DataFrame({
            'Size': standardize(np.log(market_cap)),
            'Value': standardize(book_to_price),
            'Momentum': standardize(momentum),
            'Volatility': standardize(volatility),
            'Beta': standardize(beta)
        })
        
        self.exposures = exposures
        return exposures
    
    def estimate_factor_returns(self, returns, exposures):
        """横截面回归估计因子收益率
        
        r_i = Σ X_ik * f_k + ε_i
        
        Args:
            returns: 股票收益率 (T x N)
            exposures: 因子暴露 (N x K)
        
        Returns:
            因子收益率 (T x K)
        """
        T = len(returns)
        K = exposures.shape[1]
        
        factor_returns = np.zeros((T, K))
        specific_returns = np.zeros((T, len(exposures)))
        
        for t in range(T):
            # 横截面回归
            X = exposures.values
            y = returns.iloc[t].values
            
            # 加权最小二乘 (可以用市值加权)
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            factor_returns[t] = beta
            specific_returns[t] = y - X @ beta
        
        self.factor_returns = pd.DataFrame(
            factor_returns,
            index=returns.index,
            columns=exposures.columns
        )
        
        return self.factor_returns, specific_returns
    
    def estimate_covariance(self, half_life=60):
        """估计因子协方差和特异性风险"""
        # 因子协方差 (指数加权)
        self.factor_cov = self.factor_returns.ewm(halflife=half_life).cov()
        
        # 最新的因子协方差矩阵
        latest_factor_cov = self.factor_cov.iloc[-self.n_style_factors:]
        
        return latest_factor_cov
    
    def calculate_portfolio_risk(self, weights):
        """计算组合风险
        
        σ_p² = w' * B * Σ_f * B' * w + w' * D * w
        
        Args:
            weights: 组合权重
        
        Returns:
            组合风险分解
        """
        B = self.exposures.values
        w = weights.values if hasattr(weights, 'values') else weights
        
        # 组合因子暴露
        portfolio_exposure = B.T @ w
        
        # 因子风险
        factor_cov = self.factor_cov.iloc[-self.n_style_factors:].values
        factor_var = portfolio_exposure @ factor_cov @ portfolio_exposure
        
        # 特异性风险
        if self.specific_risk is not None:
            specific_var = np.sum((w ** 2) * self.specific_risk)
        else:
            specific_var = 0
        
        total_var = factor_var + specific_var
        
        return {
            'total_risk': np.sqrt(total_var),
            'factor_risk': np.sqrt(factor_var),
            'specific_risk': np.sqrt(specific_var),
            'factor_contribution': factor_var / total_var,
            'portfolio_exposure': portfolio_exposure
        }

# 示例使用
np.random.seed(42)
n_stocks = 100
n_days = 252

# 模拟因子数据
market_cap = np.exp(np.random.randn(n_stocks) * 2 + 10)
book_to_price = np.random.uniform(0.5, 2, n_stocks)
momentum = np.random.randn(n_stocks)
volatility = np.random.uniform(0.1, 0.5, n_stocks)
beta = np.random.uniform(0.5, 1.5, n_stocks)

model = BarraRiskModel()
exposures = model.calculate_exposures(market_cap, book_to_price, momentum, 
                                       volatility, beta)
print("因子暴露统计:")
print(exposures.describe())
```

## 六、组合优化

### 6.1 均值-方差优化

```python
from scipy.optimize import minimize

def mean_variance_optimization(returns, risk_aversion=1):
    """均值-方差优化
    
    max w'μ - (λ/2) w'Σw
    s.t. Σw = 1, w >= 0
    
    Args:
        returns: 收益率矩阵
        risk_aversion: 风险厌恶系数
    
    Returns:
        最优权重
    """
    n = len(returns.columns)
    mu = returns.mean().values
    sigma = returns.cov().values
    
    # 目标函数（最小化负效用）
    def objective(w):
        portfolio_return = w @ mu
        portfolio_var = w @ sigma @ w
        return -portfolio_return + (risk_aversion / 2) * portfolio_var
    
    # 约束条件
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # 权重和为1
    ]
    
    # 边界条件（无卖空）
    bounds = [(0, 1) for _ in range(n)]
    
    # 初始权重
    w0 = np.ones(n) / n
    
    # 优化
    result = minimize(objective, w0, method='SLSQP', 
                     bounds=bounds, constraints=constraints)
    
    weights = result.x
    
    # 计算组合统计
    port_return = weights @ mu * 252  # 年化
    port_vol = np.sqrt(weights @ sigma @ weights * 252)
    sharpe = port_return / port_vol
    
    print(f"均值-方差优化结果 (λ={risk_aversion}):")
    print(f"  年化收益: {port_return:.2%}")
    print(f"  年化波动: {port_vol:.2%}")
    print(f"  夏普比率: {sharpe:.2f}")
    
    return weights

# 最小方差组合
def minimum_variance_portfolio(returns):
    """最小方差组合"""
    return mean_variance_optimization(returns, risk_aversion=1e6)

# 最大夏普比率组合
def maximum_sharpe_portfolio(returns, rf=0.02):
    """最大夏普比率组合"""
    n = len(returns.columns)
    mu = returns.mean().values * 252  # 年化
    sigma = returns.cov().values * 252
    
    def neg_sharpe(w):
        port_ret = w @ mu
        port_vol = np.sqrt(w @ sigma @ w)
        return -(port_ret - rf) / port_vol
    
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(0, 1) for _ in range(n)]
    w0 = np.ones(n) / n
    
    result = minimize(neg_sharpe, w0, method='SLSQP',
                     bounds=bounds, constraints=constraints)
    
    return result.x

weights = mean_variance_optimization(returns_df.iloc[:, :10], risk_aversion=2)
```

### 6.2 风险平价

```python
def risk_parity_portfolio(returns):
    """风险平价组合
    
    使每个资产对组合风险的贡献相等
    """
    n = len(returns.columns)
    sigma = returns.cov().values * 252
    
    def risk_contribution(w):
        port_vol = np.sqrt(w @ sigma @ w)
        marginal_risk = sigma @ w / port_vol
        risk_contrib = w * marginal_risk
        return risk_contrib
    
    def objective(w):
        rc = risk_contribution(w)
        target = np.sum(rc) / n  # 目标风险贡献
        return np.sum((rc - target) ** 2)
    
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(0.01, 1) for _ in range(n)]
    w0 = np.ones(n) / n
    
    result = minimize(objective, w0, method='SLSQP',
                     bounds=bounds, constraints=constraints)
    
    weights = result.x
    rc = risk_contribution(weights)
    
    print("风险平价组合:")
    print(f"  权重范围: [{weights.min():.2%}, {weights.max():.2%}]")
    print(f"  风险贡献范围: [{rc.min():.4f}, {rc.max():.4f}]")
    print(f"  风险贡献标准差: {rc.std():.6f}")
    
    return weights

rp_weights = risk_parity_portfolio(returns_df.iloc[:, :10])
```

### 6.3 带约束的优化

```python
def constrained_optimization(returns, factor_exposures, constraints_dict):
    """带因子约束的组合优化
    
    Args:
        returns: 收益率
        factor_exposures: 因子暴露矩阵
        constraints_dict: 约束条件
            - 'factor_limits': {factor_name: (min, max)}
            - 'sector_limits': {sector: (min, max)}
            - 'position_limits': (min, max)
    
    Returns:
        最优权重
    """
    n = len(returns.columns)
    mu = returns.mean().values
    sigma = returns.cov().values
    
    # 目标函数
    def objective(w):
        return -w @ mu + 0.5 * w @ sigma @ w
    
    # 约束列表
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
    ]
    
    # 因子暴露约束
    if 'factor_limits' in constraints_dict:
        for factor, (min_exp, max_exp) in constraints_dict['factor_limits'].items():
            if factor in factor_exposures.columns:
                exp = factor_exposures[factor].values
                constraints.append({
                    'type': 'ineq', 
                    'fun': lambda w, e=exp, m=min_exp: w @ e - m
                })
                constraints.append({
                    'type': 'ineq', 
                    'fun': lambda w, e=exp, m=max_exp: m - w @ e
                })
    
    # 个股权重约束
    pos_min, pos_max = constraints_dict.get('position_limits', (0, 0.1))
    bounds = [(pos_min, pos_max) for _ in range(n)]
    
    w0 = np.ones(n) / n
    result = minimize(objective, w0, method='SLSQP',
                     bounds=bounds, constraints=constraints)
    
    return result.x

# 示例约束
constraints = {
    'factor_limits': {
        'Beta': (-0.1, 0.1),  # Beta中性
        'Size': (-0.2, 0.2)   # 限制规模暴露
    },
    'position_limits': (0, 0.05)  # 单个股票最多5%
}
```

## 七、面试常见问题

### Q1: PCA和因子模型的区别？

**答案**：
- **PCA**：纯统计方法，提取解释方差最大的正交成分，因子没有经济含义
- **因子模型**：基于经济理论，因子有明确含义（如市场、规模、价值），可能不正交
- **联系**：PCA可用于发现潜在因子结构，验证因子模型的因子数量

### Q2: 为什么需要协方差收缩？

**答案**：
- 样本协方差在 T < N 时不可逆
- 即使可逆，极端特征值导致优化不稳定
- 收缩向结构化目标（如对角矩阵）拉近，减少估计误差
- 提高样本外表现

### Q3: 解释风险平价的优势和劣势

**答案**：
**优势**：
- 不需要预测收益率（均值估计难度大）
- 分散化更均衡
- 对输入误差更稳健

**劣势**：
- 可能配置过多低风险低收益资产
- 忽略资产间相关性变化
- 实际中需要杠杆实现目标收益

## 总结

统计套利与因子模型的核心要点：

1. **配对交易**：协整是数学基础，对冲比率决定风险控制
2. **PCA/ICA**：降维和因子发现的有力工具
3. **协方差估计**：收缩和因子模型改善稳定性
4. **Barra模型**：行业标准风险模型框架
5. **组合优化**：目标和约束的合理设置是关键

这些方法是量化投资的核心技术栈。

---

## 相关文章

- [上一篇：时间序列分析详解(HFT)](/articles/math/math-11-时间序列分析详解/)
- [下一篇：数值计算与浮点精度(HFT)](/articles/math/math-13-数值计算与浮点精度/)
