+++
title = "08 - 回测系统设计与实现"
date = 2025-01-15
description = "量化交易回测系统架构设计：事件驱动 vs 向量化、核心模块、常见陷阱、自建框架实战"
[taxonomies]
tags = ["quant", "backtesting", "system-design", "event-driven", "vectorized"]
+++

## 概述

回测系统是量化交易的核心基础设施。理解回测系统的原理，才能识别回测陷阱，做出可靠的策略验证。本文介绍回测系统的设计与实现。

---

## 一、回测系统的重要性

### 1.1 为什么要理解回测原理

```
理解回测原理的意义：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   识别陷阱                                              │
│   ────────                                              │
│   • 理解前视偏差如何产生                                │
│   • 识别幸存者偏差                                      │
│   • 理解成本模拟的问题                                  │
│                                                          │
│   定制能力                                              │
│   ────────                                              │
│   • 现有框架不一定满足需求                              │
│   • 自定义成本模型                                      │
│   • 特殊规则实现                                        │
│                                                          │
│   调试能力                                              │
│   ────────                                              │
│   • 回测结果异常时能定位原因                            │
│   • 理解结果的可信度                                    │
│                                                          │
│   底层思维                                              │
│   ────────                                              │
│   • 知其然更知其所以然                                  │
│   • 不被框架限制思维                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 自建 vs 使用框架

```
选择对比：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   使用现有框架                                          │
│   ──────────────                                        │
│   优点：                                                │
│   • 快速上手                                            │
│   • 功能完善                                            │
│   • 社区支持                                            │
│                                                          │
│   缺点：                                                │
│   • 黑箱，不了解细节                                    │
│   • 定制受限                                            │
│   • 可能有隐藏 bug                                      │
│                                                          │
│   推荐框架：backtrader, vnpy, zipline                   │
│                                                          │
│   ──────────────────────────────────────────────────   │
│                                                          │
│   自建回测系统                                          │
│   ──────────────                                        │
│   优点：                                                │
│   • 完全理解原理                                        │
│   • 高度定制                                            │
│   • 学习价值高                                          │
│                                                          │
│   缺点：                                                │
│   • 开发成本高                                          │
│   • 可能有 bug                                          │
│   • 需要持续维护                                        │
│                                                          │
│   建议：先用框架入门，再自建深入理解                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 二、回测架构模式

### 2.1 两种主要架构

```
回测系统架构对比：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   向量化回测（Vectorized）                              │
│   ────────────────────────                              │
│   • 用 pandas/numpy 一次性计算                          │
│   • 适合简单策略                                        │
│   • 速度极快                                            │
│   • 难以处理复杂逻辑                                    │
│                                                          │
│   事件驱动回测（Event-Driven）                          │
│   ────────────────────────                              │
│   • 模拟真实交易流程                                    │
│   • 逐 bar 处理                                         │
│   • 可处理复杂逻辑                                      │
│   • 速度较慢                                            │
│   • 容易迁移到实盘                                      │
│                                                          │
│   选择建议：                                            │
│   • 研究阶段：向量化（快速迭代）                        │
│   • 验证阶段：事件驱动（更真实）                        │
│   • 准备实盘：事件驱动（易迁移）                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 向量化回测示例

```python
import pandas as pd
import numpy as np

def vectorized_backtest(prices, signals, initial_capital=1000000):
    """
    向量化回测示例
    
    prices: 价格序列
    signals: 信号序列（1=买入持有, 0=空仓, -1=做空）
    """
    # 计算收益率
    returns = prices.pct_change()
    
    # 策略收益 = 信号 * 收益率（信号要滞后一天，避免前视偏差）
    strategy_returns = signals.shift(1) * returns
    
    # 扣除交易成本
    trades = signals.diff().abs()  # 换手
    costs = trades * 0.001  # 假设千分之一成本
    strategy_returns = strategy_returns - costs
    
    # 累计收益
    cumulative_returns = (1 + strategy_returns).cumprod()
    portfolio_value = initial_capital * cumulative_returns
    
    # 计算指标
    total_return = portfolio_value.iloc[-1] / initial_capital - 1
    annual_return = (1 + total_return) ** (252 / len(returns)) - 1
    volatility = strategy_returns.std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility > 0 else 0
    max_drawdown = (portfolio_value / portfolio_value.cummax() - 1).min()
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'portfolio_value': portfolio_value
    }
```

### 2.3 事件驱动架构

```
事件驱动回测架构：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   ┌──────────────────────────────────────────────────┐  │
│   │                     主循环                        │  │
│   │              (遍历每个时间点)                     │  │
│   └───────────────────────┬──────────────────────────┘  │
│                           │                              │
│                           ▼                              │
│   ┌──────────────────────────────────────────────────┐  │
│   │                   数据模块                        │  │
│   │         (提供当前 bar 的市场数据)                │  │
│   └───────────────────────┬──────────────────────────┘  │
│                           │ Market Event                 │
│                           ▼                              │
│   ┌──────────────────────────────────────────────────┐  │
│   │                   策略模块                        │  │
│   │         (根据数据生成交易信号)                   │  │
│   └───────────────────────┬──────────────────────────┘  │
│                           │ Signal Event                 │
│                           ▼                              │
│   ┌──────────────────────────────────────────────────┐  │
│   │                   风控模块                        │  │
│   │         (检查风控规则，决定仓位)                 │  │
│   └───────────────────────┬──────────────────────────┘  │
│                           │ Order Event                  │
│                           ▼                              │
│   ┌──────────────────────────────────────────────────┐  │
│   │                   执行模块                        │  │
│   │         (模拟订单执行，考虑滑点)                 │  │
│   └───────────────────────┬──────────────────────────┘  │
│                           │ Fill Event                   │
│                           ▼                              │
│   ┌──────────────────────────────────────────────────┐  │
│   │                   账户模块                        │  │
│   │         (更新持仓、资金、净值)                   │  │
│   └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 三、核心模块设计

### 3.1 数据模块

```python
class DataHandler:
    """
    数据处理模块
    负责管理和提供市场数据
    """
    def __init__(self, data_source):
        self.data_source = data_source
        self.current_index = 0
        self.data = None
        
    def load_data(self, symbols, start_date, end_date):
        """加载历史数据"""
        self.data = {}
        for symbol in symbols:
            df = self.data_source.get_history(
                symbol, start_date, end_date
            )
            # 确保数据按时间排序
            df = df.sort_index()
            self.data[symbol] = df
        
        # 获取所有交易日
        self.trading_dates = self._get_trading_dates()
        
    def get_current_bar(self, symbol):
        """获取当前 bar 数据"""
        date = self.trading_dates[self.current_index]
        if date in self.data[symbol].index:
            return self.data[symbol].loc[date]
        return None
    
    def get_history(self, symbol, lookback):
        """获取历史数据（不包含未来数据）"""
        end_idx = self.current_index + 1
        start_idx = max(0, end_idx - lookback)
        dates = self.trading_dates[start_idx:end_idx]
        return self.data[symbol].loc[dates]
    
    def next(self):
        """移动到下一个时间点"""
        self.current_index += 1
        return self.current_index < len(self.trading_dates)
```

### 3.2 策略模块

```python
from abc import ABC, abstractmethod

class Strategy(ABC):
    """
    策略基类
    """
    def __init__(self, data_handler, portfolio):
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.signals = []
        
    @abstractmethod
    def calculate_signals(self):
        """
        计算交易信号
        子类必须实现
        """
        pass
    
    def generate_signal(self, symbol, signal_type, strength=1.0):
        """
        生成交易信号
        signal_type: 'BUY', 'SELL', 'EXIT'
        """
        signal = {
            'datetime': self.data_handler.current_datetime,
            'symbol': symbol,
            'type': signal_type,
            'strength': strength
        }
        self.signals.append(signal)
        return signal


class DualMAStrategy(Strategy):
    """
    双均线策略示例
    """
    def __init__(self, data_handler, portfolio, short_window=10, long_window=50):
        super().__init__(data_handler, portfolio)
        self.short_window = short_window
        self.long_window = long_window
        self.position_state = {}  # 记录持仓状态
        
    def calculate_signals(self):
        for symbol in self.data_handler.symbols:
            # 获取历史数据
            history = self.data_handler.get_history(symbol, self.long_window)
            
            if len(history) < self.long_window:
                continue
            
            # 计算均线
            short_ma = history['close'].iloc[-self.short_window:].mean()
            long_ma = history['close'].mean()
            
            # 获取当前持仓状态
            current_state = self.position_state.get(symbol, 'OUT')
            
            # 生成信号
            if short_ma > long_ma and current_state != 'LONG':
                self.generate_signal(symbol, 'BUY')
                self.position_state[symbol] = 'LONG'
            elif short_ma < long_ma and current_state == 'LONG':
                self.generate_signal(symbol, 'SELL')
                self.position_state[symbol] = 'OUT'
```

### 3.3 执行模块

```python
class ExecutionHandler:
    """
    执行模块
    模拟订单执行，包括滑点和成本
    """
    def __init__(self, data_handler, slippage_model=None, commission_model=None):
        self.data_handler = data_handler
        self.slippage_model = slippage_model or FixedSlippage(0.0001)
        self.commission_model = commission_model or PercentageCommission(0.0003)
        
    def execute_order(self, order):
        """
        执行订单
        返回成交记录
        """
        bar = self.data_handler.get_current_bar(order['symbol'])
        
        # 基础价格（使用开盘价或收盘价）
        base_price = bar['close']
        
        # 计算滑点
        slippage = self.slippage_model.calculate(order, bar)
        
        # 成交价格
        if order['direction'] == 'BUY':
            fill_price = base_price * (1 + slippage)
        else:
            fill_price = base_price * (1 - slippage)
        
        # 计算佣金
        commission = self.commission_model.calculate(
            order['quantity'], fill_price
        )
        
        # 生成成交记录
        fill = {
            'datetime': self.data_handler.current_datetime,
            'symbol': order['symbol'],
            'direction': order['direction'],
            'quantity': order['quantity'],
            'fill_price': fill_price,
            'commission': commission
        }
        
        return fill


class FixedSlippage:
    """固定比例滑点"""
    def __init__(self, slippage_pct):
        self.slippage_pct = slippage_pct
        
    def calculate(self, order, bar):
        return self.slippage_pct


class PercentageCommission:
    """百分比佣金"""
    def __init__(self, rate):
        self.rate = rate
        
    def calculate(self, quantity, price):
        return quantity * price * self.rate
```

### 3.4 账户模块

```python
class Portfolio:
    """
    账户/组合管理模块
    """
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {symbol: quantity}
        self.holdings = {}   # {symbol: market_value}
        
        # 记录历史
        self.history = []
        self.trades = []
        
    def update_fill(self, fill):
        """
        更新成交
        """
        symbol = fill['symbol']
        quantity = fill['quantity']
        price = fill['fill_price']
        commission = fill['commission']
        
        # 更新持仓
        if fill['direction'] == 'BUY':
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity
            self.cash -= quantity * price + commission
        else:
            self.positions[symbol] = self.positions.get(symbol, 0) - quantity
            self.cash += quantity * price - commission
        
        # 清理空持仓
        if self.positions.get(symbol, 0) == 0:
            del self.positions[symbol]
        
        # 记录交易
        self.trades.append(fill)
    
    def update_market_value(self, data_handler):
        """
        按当前市场价格更新市值
        """
        total_value = self.cash
        
        for symbol, quantity in self.positions.items():
            bar = data_handler.get_current_bar(symbol)
            if bar is not None:
                market_value = quantity * bar['close']
                self.holdings[symbol] = market_value
                total_value += market_value
        
        # 记录净值历史
        self.history.append({
            'datetime': data_handler.current_datetime,
            'total_value': total_value,
            'cash': self.cash,
            'positions': self.positions.copy()
        })
        
        return total_value
    
    def get_statistics(self):
        """
        计算绩效统计
        """
        history_df = pd.DataFrame(self.history)
        history_df.set_index('datetime', inplace=True)
        
        # 计算收益率
        returns = history_df['total_value'].pct_change().dropna()
        
        # 统计指标
        total_return = (history_df['total_value'].iloc[-1] / 
                       self.initial_capital - 1)
        
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe = annual_return / volatility if volatility > 0 else 0
        
        # 最大回撤
        cummax = history_df['total_value'].cummax()
        drawdown = (history_df['total_value'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.trades)
        }
```

---

## 四、完整回测引擎

### 4.1 回测引擎实现

```python
class BacktestEngine:
    """
    回测引擎
    整合所有模块
    """
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.data_handler = None
        self.strategy = None
        self.portfolio = None
        self.execution_handler = None
        
    def set_data(self, data_handler):
        self.data_handler = data_handler
        
    def set_strategy(self, strategy_class, **strategy_params):
        self.strategy_class = strategy_class
        self.strategy_params = strategy_params
        
    def run(self):
        """
        运行回测
        """
        # 初始化组件
        self.portfolio = Portfolio(self.initial_capital)
        self.execution_handler = ExecutionHandler(self.data_handler)
        self.strategy = self.strategy_class(
            self.data_handler, 
            self.portfolio,
            **self.strategy_params
        )
        
        # 主循环
        while self.data_handler.next():
            # 1. 更新市值
            self.portfolio.update_market_value(self.data_handler)
            
            # 2. 策略计算信号
            self.strategy.calculate_signals()
            
            # 3. 处理信号
            for signal in self.strategy.signals:
                # 生成订单
                order = self._signal_to_order(signal)
                if order:
                    # 执行订单
                    fill = self.execution_handler.execute_order(order)
                    # 更新账户
                    self.portfolio.update_fill(fill)
            
            # 清空已处理的信号
            self.strategy.signals = []
        
        # 返回结果
        return self.portfolio.get_statistics()
    
    def _signal_to_order(self, signal):
        """
        信号转订单
        """
        if signal['type'] == 'BUY':
            # 计算可买数量
            bar = self.data_handler.get_current_bar(signal['symbol'])
            affordable = self.portfolio.cash / bar['close'] * 0.95
            quantity = int(affordable * signal['strength'])
            
            if quantity > 0:
                return {
                    'symbol': signal['symbol'],
                    'direction': 'BUY',
                    'quantity': quantity
                }
        
        elif signal['type'] == 'SELL':
            quantity = self.portfolio.positions.get(signal['symbol'], 0)
            if quantity > 0:
                return {
                    'symbol': signal['symbol'],
                    'direction': 'SELL',
                    'quantity': quantity
                }
        
        return None
```

### 4.2 使用示例

```python
# 使用示例
if __name__ == '__main__':
    # 1. 准备数据
    data_handler = DataHandler(YourDataSource())
    data_handler.load_data(
        symbols=['AAPL', 'GOOGL', 'MSFT'],
        start_date='2020-01-01',
        end_date='2023-12-31'
    )
    
    # 2. 创建回测引擎
    engine = BacktestEngine(initial_capital=1000000)
    engine.set_data(data_handler)
    engine.set_strategy(DualMAStrategy, short_window=10, long_window=50)
    
    # 3. 运行回测
    results = engine.run()
    
    # 4. 输出结果
    print("=== 回测结果 ===")
    print(f"总收益: {results['total_return']:.2%}")
    print(f"年化收益: {results['annual_return']:.2%}")
    print(f"夏普比率: {results['sharpe']:.2f}")
    print(f"最大回撤: {results['max_drawdown']:.2%}")
    print(f"总交易次数: {results['total_trades']}")
```

---

## 五、回测陷阱详解

### 5.1 前视偏差

```
前视偏差（Look-Ahead Bias）：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   定义：使用了当时不可能知道的未来信息                  │
│                                                          │
│   常见场景：                                            │
│   ──────────                                            │
│   1. 用当日收盘价决策，当日执行                         │
│      修正：信号应该在 T 日产生，T+1 日执行              │
│                                                          │
│   2. 财务数据不考虑发布延迟                             │
│      修正：使用发布日期，而非报告期                     │
│                                                          │
│   3. 用全样本计算统计量                                 │
│      修正：只用到当时为止的数据                         │
│                                                          │
│   4. 数据中包含未来修正值                               │
│      修正：使用点时间（Point-in-Time）数据              │
│                                                          │
│   检测方法：                                            │
│   ──────────                                            │
│   • 检查信号生成和执行的时间关系                        │
│   • 验证数据的时间戳                                    │
│   • Walk-forward 测试                                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.2 幸存者偏差

```
幸存者偏差（Survivorship Bias）：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   定义：只使用"存活"的数据，忽略已消失的                │
│                                                          │
│   影响：                                                │
│   ──────────                                            │
│   • 低估风险（退市的通常表现差）                        │
│   • 高估收益                                            │
│   • 价值策略受影响最大                                  │
│                                                          │
│   示例：                                                │
│   ──────────                                            │
│   2010 年买入"便宜"股票                                 │
│   其中一些后来退市归零                                  │
│   只用当前存在的股票回测会忽略这些亏损                  │
│                                                          │
│   解决方案：                                            │
│   ──────────                                            │
│   • 使用包含退市股票的完整数据                          │
│   • 使用专业数据源（如 CRSP）                           │
│   • 至少意识到这个偏差的存在                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.3 成本低估

```
交易成本模拟：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   需要考虑的成本：                                      │
│   ──────────────                                        │
│   • 佣金（明确的）                                      │
│   • 印花税（A 股卖出千一）                              │
│   • 买卖价差（Bid-Ask Spread）                          │
│   • 滑点（Slippage）                                    │
│   • 市场冲击（大单影响价格）                            │
│                                                          │
│   常见错误：                                            │
│   ──────────────                                        │
│   • 不考虑成本                                          │
│   • 只考虑佣金                                          │
│   • 滑点估计过低                                        │
│   • 忽视流动性限制                                      │
│                                                          │
│   成本估算参考：                                        │
│   ──────────────                                        │
│   • A股：单边 0.1-0.2%（含滑点）                        │
│   • 美股：单边 0.05-0.1%                                │
│   • 期货：单边 0.01-0.02%                               │
│   • 小盘股/低流动性：更高                               │
│                                                          │
│   建议：成本估算保守一些                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 六、性能优化

### 6.1 向量化优化

```python
# 慢：逐行循环
def slow_calculate_ma(prices, window):
    result = []
    for i in range(len(prices)):
        if i < window - 1:
            result.append(np.nan)
        else:
            result.append(np.mean(prices[i-window+1:i+1]))
    return result

# 快：向量化
def fast_calculate_ma(prices, window):
    return prices.rolling(window).mean()
```

### 6.2 并行化

```python
from concurrent.futures import ProcessPoolExecutor

def backtest_single_param(params):
    """单个参数组合的回测"""
    engine = BacktestEngine()
    # ... 设置参数
    return engine.run()

def parallel_backtest(param_combinations):
    """并行回测多个参数组合"""
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(backtest_single_param, param_combinations))
    return results
```

---

## 七、总结

```
回测系统设计要点：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   架构选择                                              │
│   ────────                                              │
│   • 研究阶段：向量化（快速）                            │
│   • 验证阶段：事件驱动（真实）                          │
│                                                          │
│   核心模块                                              │
│   ────────                                              │
│   • 数据模块：提供历史数据，防止前视偏差                │
│   • 策略模块：生成交易信号                              │
│   • 执行模块：模拟真实交易成本                          │
│   • 账户模块：跟踪持仓和净值                            │
│                                                          │
│   陷阱防范                                              │
│   ────────                                              │
│   • 严格防止前视偏差                                    │
│   • 使用完整数据（含退市）                              │
│   • 保守估计交易成本                                    │
│   • Walk-forward 验证                                   │
│                                                          │
│   ──────────────────────────────────────────────────   │
│                                                          │
│   "理解回测原理，才能信任回测结果。"                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```
