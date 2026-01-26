+++
title = "55.Python量化面试题"
slug = "py-55-Python量化面试题"
date = 2026-01-21
description = "Python量化面试常见问题，包括策略实现、数据处理、性能优化、统计计算和Pandas/NumPy陷阱"
[taxonomies]
tags = ["Python", "面试", "量化", "Pandas", "NumPy"]
+++

## 一、策略实现

### Q1: 实现一个简单的动量策略回测

```python
import pandas as pd
import numpy as np

def momentum_strategy(prices, lookback=20, holding_period=5):
    """
    动量策略：
    - 过去lookback天收益率为正则做多
    - 持有holding_period天
    """
    # 计算收益率
    returns = prices.pct_change()
    
    # 计算动量信号
    momentum = prices.pct_change(lookback)
    
    # 生成信号：动量为正则为1，否则为0
    signals = (momentum > 0).astype(int)
    
    # 信号延迟一天（避免前瞻偏差）
    signals = signals.shift(1)
    
    # 策略收益
    strategy_returns = signals * returns
    
    # 累计收益
    cumulative_returns = (1 + strategy_returns).cumprod()
    
    return pd.DataFrame({
        'prices': prices,
        'momentum': momentum,
        'signal': signals,
        'strategy_returns': strategy_returns,
        'cumulative_returns': cumulative_returns
    })

# 计算回测指标
def calculate_metrics(returns):
    """计算策略绩效指标"""
    total_return = (1 + returns).prod() - 1
    annual_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = returns.std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility > 0 else 0
    
    # 最大回撤
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = cumulative / running_max - 1
    max_drawdown = drawdown.min()
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown
    }
```

### Q2: 实现VWAP（成交量加权平均价）

```python
def vwap(prices, volumes, window=None):
    """
    计算VWAP
    - window=None: 累计VWAP
    - window=N: 滚动VWAP
    """
    if window is None:
        # 累计VWAP
        cumulative_pv = (prices * volumes).cumsum()
        cumulative_v = volumes.cumsum()
        return cumulative_pv / cumulative_v
    else:
        # 滚动VWAP
        rolling_pv = (prices * volumes).rolling(window).sum()
        rolling_v = volumes.rolling(window).sum()
        return rolling_pv / rolling_v

# 日内VWAP（每天重置）
def daily_vwap(df):
    """df包含timestamp, price, volume列"""
    df['date'] = df['timestamp'].dt.date
    df['pv'] = df['price'] * df['volume']
    
    df['cum_pv'] = df.groupby('date')['pv'].cumsum()
    df['cum_v'] = df.groupby('date')['volume'].cumsum()
    df['vwap'] = df['cum_pv'] / df['cum_v']
    
    return df['vwap']
```

### Q3: 实现配对交易的z-score

```python
def pairs_trading_zscore(price_a, price_b, lookback=20):
    """
    配对交易z-score计算
    """
    # 计算价差（简化版：对数价差）
    spread = np.log(price_a) - np.log(price_b)
    
    # 滚动均值和标准差
    spread_mean = spread.rolling(lookback).mean()
    spread_std = spread.rolling(lookback).std()
    
    # z-score
    zscore = (spread - spread_mean) / spread_std
    
    return pd.DataFrame({
        'spread': spread,
        'zscore': zscore,
        'upper': 2.0,  # 做空价差
        'lower': -2.0  # 做多价差
    })
```

---

## 二、数据处理

### Q4: 处理缺失数据的正确方式

```python
# 问题：如何正确处理金融时序数据中的缺失值？

def handle_missing_data(df):
    """
    金融数据缺失值处理策略
    """
    # 1. 检查缺失情况
    print("缺失统计:")
    print(df.isnull().sum())
    
    # 2. 价格数据：前向填充（不能用均值）
    df['price'] = df['price'].ffill()
    
    # 3. 成交量：填充0或前向填充
    df['volume'] = df['volume'].fillna(0)
    
    # 4. 收益率：缺失则为0
    df['return'] = df['return'].fillna(0)
    
    # 5. 限制连续填充次数
    df['price'] = df['price'].ffill(limit=5)
    
    # 6. 删除仍然缺失的行
    df = df.dropna()
    
    return df

# 问题：为什么价格不能用均值填充？
# 答案：会引入前瞻偏差，均值包含未来信息
```

### Q5: DataFrame合并时的对齐问题

```python
# 问题：两个不同时间戳的DataFrame如何正确合并？

# 股票价格
stock_prices = pd.DataFrame({
    'price': [100, 101, 102]
}, index=pd.to_datetime(['2024-01-01 09:30', '2024-01-01 09:31', '2024-01-01 09:32']))

# 市场指数（不同时间戳）
index_prices = pd.DataFrame({
    'index': [1000, 1001, 1002]
}, index=pd.to_datetime(['2024-01-01 09:30:05', '2024-01-01 09:31:02', '2024-01-01 09:32:01']))

# 方法1：merge_asof（最近时间匹配）
merged = pd.merge_asof(
    stock_prices.reset_index().rename(columns={'index': 'time'}),
    index_prices.reset_index().rename(columns={'index': 'time'}),
    on='time',
    direction='backward'  # 使用之前最近的值
)

# 方法2：重采样到相同频率后合并
stock_resampled = stock_prices.resample('S').ffill()
index_resampled = index_prices.resample('S').ffill()
merged = pd.concat([stock_resampled, index_resampled], axis=1)
```

### Q6: 高效计算滚动相关系数

```python
# 问题：如何高效计算两个序列的滚动相关系数？

def rolling_correlation(x, y, window):
    """
    方法1：使用rolling.corr（简单但可能慢）
    """
    return x.rolling(window).corr(y)

def rolling_correlation_fast(x, y, window):
    """
    方法2：使用在线算法（更快）
    """
    n = len(x)
    result = np.full(n, np.nan)
    
    # 初始化
    sum_x = x[:window].sum()
    sum_y = y[:window].sum()
    sum_xy = (x[:window] * y[:window]).sum()
    sum_x2 = (x[:window] ** 2).sum()
    sum_y2 = (y[:window] ** 2).sum()
    
    for i in range(window - 1, n):
        if i > window - 1:
            # 更新（滑动窗口）
            old_x, old_y = x[i - window], y[i - window]
            new_x, new_y = x[i], y[i]
            
            sum_x += new_x - old_x
            sum_y += new_y - old_y
            sum_xy += new_x * new_y - old_x * old_y
            sum_x2 += new_x ** 2 - old_x ** 2
            sum_y2 += new_y ** 2 - old_y ** 2
        
        # 计算相关系数
        mean_x = sum_x / window
        mean_y = sum_y / window
        
        cov = sum_xy / window - mean_x * mean_y
        var_x = sum_x2 / window - mean_x ** 2
        var_y = sum_y2 / window - mean_y ** 2
        
        if var_x > 0 and var_y > 0:
            result[i] = cov / np.sqrt(var_x * var_y)
    
    return pd.Series(result, index=x.index)
```

---

## 三、性能优化

### Q7: 为什么这段代码很慢？如何优化？

```python
# 慢代码
def slow_calculate_signals(df):
    df['signal'] = 0
    for i in range(len(df)):
        if df.iloc[i]['price'] > df.iloc[i]['ma_20']:
            df.iloc[i, df.columns.get_loc('signal')] = 1
        else:
            df.iloc[i, df.columns.get_loc('signal')] = -1
    return df

# 问题分析：
# 1. 使用了Python循环
# 2. iloc是慢速索引
# 3. 每次迭代都在查找列位置

# 优化后
def fast_calculate_signals(df):
    df['signal'] = np.where(df['price'] > df['ma_20'], 1, -1)
    return df

# 或使用布尔运算
def fast_calculate_signals_v2(df):
    df['signal'] = (df['price'] > df['ma_20']).astype(int) * 2 - 1
    return df
```

### Q8: 如何优化groupby操作？

```python
# 场景：计算每个股票的滚动统计

# 慢
def slow_group_stats(df):
    return df.groupby('symbol').apply(
        lambda x: pd.DataFrame({
            'ma_20': x['price'].rolling(20).mean(),
            'std_20': x['price'].rolling(20).std(),
            'returns': x['price'].pct_change()
        })
    )

# 快：使用transform
def fast_group_stats(df):
    df = df.sort_values(['symbol', 'date'])  # 确保排序
    
    df['ma_20'] = df.groupby('symbol')['price'].transform(
        lambda x: x.rolling(20).mean()
    )
    df['std_20'] = df.groupby('symbol')['price'].transform(
        lambda x: x.rolling(20).std()
    )
    df['returns'] = df.groupby('symbol')['price'].transform(
        lambda x: x.pct_change()
    )
    return df

# 更快：numba加速
from numba import jit

@jit(nopython=True)
def rolling_mean_numba(arr, window):
    n = len(arr)
    result = np.empty(n)
    result[:window-1] = np.nan
    
    cumsum = np.cumsum(arr)
    result[window-1:] = (cumsum[window-1:] - 
                          np.concatenate((np.array([0.0]), cumsum[:-window]))) / window
    return result
```

---

## 四、统计计算

### Q9: 解释并实现这些统计指标

```python
def calculate_all_metrics(returns):
    """
    计算完整的策略绩效指标
    """
    # 年化收益
    n_years = len(returns) / 252
    total_return = (1 + returns).prod() - 1
    annual_return = (1 + total_return) ** (1 / n_years) - 1
    
    # 波动率（年化）
    volatility = returns.std() * np.sqrt(252)
    
    # 夏普比率（假设无风险利率为0）
    sharpe = annual_return / volatility if volatility > 0 else 0
    
    # Sortino比率（只考虑下行波动）
    downside_returns = returns[returns < 0]
    downside_vol = downside_returns.std() * np.sqrt(252)
    sortino = annual_return / downside_vol if downside_vol > 0 else 0
    
    # 最大回撤
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = cumulative / running_max - 1
    max_drawdown = drawdown.min()
    
    # Calmar比率
    calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # 胜率
    win_rate = (returns > 0).mean()
    
    # 盈亏比
    avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
    avg_loss = abs(returns[returns < 0].mean()) if (returns < 0).any() else 0
    profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    return {
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'max_drawdown': max_drawdown,
        'calmar_ratio': calmar,
        'win_rate': win_rate,
        'profit_factor': profit_factor
    }
```

### Q10: 信息系数(IC)计算

```python
def calculate_ic(factor_values, forward_returns):
    """
    计算因子的信息系数
    
    IC = corr(factor, forward_returns)
    """
    # 每期IC
    ic_series = factor_values.groupby(level='date').apply(
        lambda x: x.corrwith(forward_returns.loc[x.index])
    )
    
    # IC均值
    ic_mean = ic_series.mean()
    
    # IC标准差
    ic_std = ic_series.std()
    
    # IR (Information Ratio) = IC_mean / IC_std
    ir = ic_mean / ic_std if ic_std > 0 else 0
    
    # IC > 0 的比例
    ic_positive_rate = (ic_series > 0).mean()
    
    return {
        'ic_mean': ic_mean,
        'ic_std': ic_std,
        'ir': ir,
        'ic_positive_rate': ic_positive_rate
    }
```

---

## 五、常见陷阱

### Q11: 解释这个前瞻偏差问题

```python
# 问题代码
def buggy_strategy(df):
    # 使用未来数据计算信号！
    df['signal'] = np.where(df['price'] > df['price'].mean(), 1, -1)
    return df

# 正确做法
def correct_strategy(df):
    # 使用滚动均值（只用历史数据）
    df['ma'] = df['price'].expanding().mean()
    df['signal'] = np.where(df['price'] > df['ma'].shift(1), 1, -1)
    return df

# 另一个常见错误
def buggy_zscore(df, window=20):
    # 错误：使用整个序列的均值和标准差
    mean = df['price'].mean()
    std = df['price'].std()
    df['zscore'] = (df['price'] - mean) / std
    return df

# 正确
def correct_zscore(df, window=20):
    df['zscore'] = (df['price'] - df['price'].rolling(window).mean()) / \
                   df['price'].rolling(window).std()
    return df
```

### Q12: DataFrame复制问题

```python
# 问题：这段代码有什么问题？
def process_subset(df):
    subset = df[df['price'] > 100]  # 这是视图还是拷贝？
    subset['new_col'] = 1  # SettingWithCopyWarning
    return subset

# 解决方案
def process_subset_correct(df):
    subset = df[df['price'] > 100].copy()  # 显式拷贝
    subset['new_col'] = 1
    return subset

# 或使用.loc
def process_subset_loc(df):
    df.loc[df['price'] > 100, 'new_col'] = 1
    return df
```

### Q13: 浮点数比较问题

```python
# 问题
price1 = 100.0 + 0.1 + 0.1 + 0.1
price2 = 100.3
print(price1 == price2)  # False！

# 原因
print(repr(price1))  # 100.30000000000001
print(repr(price2))  # 100.3

# 解决方案
import math

# 方法1：使用math.isclose
print(math.isclose(price1, price2, rel_tol=1e-9))  # True

# 方法2：使用numpy
print(np.isclose(price1, price2))  # True

# 方法3：使用Decimal（金融计算推荐）
from decimal import Decimal, ROUND_HALF_UP

price1 = Decimal('100.0') + Decimal('0.1') + Decimal('0.1') + Decimal('0.1')
price2 = Decimal('100.3')
print(price1 == price2)  # True
```

---

## 总结

**关键知识点**：

1. **策略实现**
   - 避免前瞻偏差
   - 正确计算滚动指标
   - 完整的回测指标计算

2. **数据处理**
   - 缺失值处理策略
   - 时间序列对齐
   - 高效的滚动计算

3. **性能优化**
   - 向量化替代循环
   - groupby优化技巧
   - Numba加速

4. **常见陷阱**
   - 前瞻偏差
   - DataFrame复制
   - 浮点数精度
