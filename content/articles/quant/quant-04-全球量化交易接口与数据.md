+++
title = "04 - 全球量化交易接口与数据"
date = 2025-01-15
description = "放眼全球：海外市场量化交易接口、可交易产品、数据来源及回测平台详解"
[taxonomies]
tags = ["quant", "trading", "global", "api", "data", "us-market"]
+++

## 概述

相比中国大陆，海外市场对个人量化交易更加开放。本文详细介绍全球主要市场的交易接口、产品、数据来源和工具。

---

## 一、可交易产品

### 1.1 美国市场

```mermaid
graph TB
    subgraph 美股品种["美国市场可交易品种"]
        subgraph 股票
            G1["NYSE / NASDAQ 股票"]
            G2["OTC 股票"]
            G3["ADR（中概股等）"]
            G4["无 T+1 限制（但有 PDT 规则）"]
        end
        subgraph ETF["ETF（极其丰富）"]
            E1["指数 ETF (SPY, QQQ)"]
            E2["行业 ETF"]
            E3["杠杆/反向 ETF"]
            E4["商品 ETF"]
            E5["债券 ETF"]
        end
        subgraph 期权
            Q1["股票期权（非常活跃）"]
            Q2["指数期权"]
            Q3["ETF 期权"]
            Q4["个人可参与"]
        end
        subgraph 期货
            F1["股指期货（ES, NQ）"]
            F2["商品期货"]
            F3["微型期货（Micro）降低门槛"]
        end
        subgraph 加密货币
            C1["Bitcoin, Ethereum 等"]
            C2["24/7 交易"]
            C3["多交易所可选"]
        end
    end
```

### 1.2 其他市场

**其他主要市场**：

| 市场 | 特点 |
|------|------|
| 欧洲 (德/英/法等) | 多国市场，需注意时区；流动性较好 |
| 日本 | 亚洲时区，与 A 股有相关性；日经期货活跃 |
| 香港 | 与 A 股联动；可做空 |
| 加密货币 | 全球市场，24/7；波动大，机会多 |
| 外汇 | 24/5 交易；杠杆高，风险大 |

---

## 二、交易接口

### 2.1 Interactive Brokers（盈透证券）

```mermaid
graph TB
    subgraph IB["Interactive Brokers（IB）⭐ 强烈推荐"]
        subgraph 优点
            Y1["全球市场覆盖（150+ 市场）"]
            Y2["专业的 API 接口"]
            Y3["低佣金"]
            Y4["支持多种资产类别"]
            Y5["个人可开户"]
        end
        subgraph API接口["API 接口"]
            A1["TWS API（Java/C++/C#/Python）"]
            A2["Client Portal API（REST）"]
            A3["ib_insync（Python 推荐）"]
        end
        subgraph 门槛
            M1["最低入金要求（不同地区不同）"]
            M2["需要一定编程能力"]
        end
        subgraph 费用
            F1["市场数据费（可选）"]
            F2["交易佣金（较低）"]
        end
    end
```

**Python 示例（ib_insync）**：
```python
from ib_insync import *

# 连接
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# 获取行情
contract = Stock('AAPL', 'SMART', 'USD')
ib.qualifyContracts(contract)
ticker = ib.reqMktData(contract)

# 下单
order = MarketOrder('BUY', 100)
trade = ib.placeOrder(contract, order)

ib.disconnect()
```

### 2.2 Alpaca

```mermaid
graph TB
    subgraph Alpaca["Alpaca（零佣金）"]
        subgraph 优点
            Y1["零佣金"]
            Y2["简洁的 REST API"]
            Y3["支持加密货币"]
            Y4["提供免费市场数据"]
            Y5["专为量化设计"]
        end
        subgraph 限制
            X1["仅美股和加密货币"]
            X2["需要美国税务身份（或特定地区）"]
        end
        D["地址：alpaca.markets"]
    end
```

**Python 示例**：
```python
import alpaca_trade_api as tradeapi

api = tradeapi.REST(
    key_id='YOUR_API_KEY',
    secret_key='YOUR_SECRET_KEY',
    base_url='https://paper-api.alpaca.markets'  # 模拟盘
)

# 获取账户
account = api.get_account()

# 下单
api.submit_order(
    symbol='AAPL',
    qty=10,
    side='buy',
    type='market',
    time_in_force='gtc'
)
```

### 2.3 加密货币交易所

```mermaid
graph TB
    subgraph 加密API["加密货币 API（ccxt 统一接口）"]
        subgraph 主流交易所
            E1["Binance（币安）"]
            E2["Coinbase Pro"]
            E3["Kraken"]
            E4["FTX（已倒闭，注意风险）"]
            E5["OKX"]
        end
        subgraph ccxt["ccxt 库（推荐）"]
            C1["统一接口支持 100+ 交易所"]
            C2["Python/JavaScript/PHP"]
            C3["开源免费"]
            C4["地址：github.com/ccxt/ccxt"]
        end
        subgraph 优势
            Y1["24/7 交易"]
            Y2["高波动性"]
            Y3["接口开放"]
            Y4["无 PDT 规则"]
        end
        subgraph 风险
            R1["交易所风险（如 FTX 事件）"]
            R2["监管不确定性"]
            R3["极端波动"]
        end
    end
```

**ccxt 示例**：
```python
import ccxt

exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
})

# 获取行情
ticker = exchange.fetch_ticker('BTC/USDT')

# 下单
order = exchange.create_market_buy_order('BTC/USDT', 0.01)
```

### 2.4 其他接口

**其他常用接口**：

| 接口 | 特点 |
|------|------|
| TD Ameritrade | 美股，API 友好（已被嘉信收购） |
| QuantConnect | 云端量化平台，可对接多个券商 |
| Tradier | 美股/期权，API 友好 |
| OANDA | 外汇交易 |
| IG | CFD，多市场覆盖 |

---

## 三、数据来源

### 3.1 免费数据源

```mermaid
graph TB
    subgraph 免费数据["免费美股数据"]
        subgraph yf["Yahoo Finance（yfinance）"]
            Y1["最常用的免费数据源"]
            Y2["股票、ETF、指数、期权"]
            Y3["历史数据较全"]
            Y4["可能有延迟和缺失"]
        end
        subgraph av["Alpha Vantage"]
            A1["免费 API（有调用限制）"]
            A2["股票、外汇、加密货币"]
            A3["技术指标内置"]
        end
        subgraph fred["FRED（联储经济数据）"]
            F1["宏观经济数据"]
            F2["完全免费"]
        end
        subgraph quandl["Quandl（部分免费）"]
            Q1["多种数据类型"]
            Q2["部分免费，高级收费"]
        end
        subgraph iex["IEX Cloud"]
            I1["有免费额度"]
            I2["数据质量较高"]
        end
    end
```

**yfinance 示例**：
```python
import yfinance as yf

# 获取股票数据
ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1y")

# 多只股票
data = yf.download(['AAPL', 'GOOGL', 'MSFT'], start="2020-01-01")
```

### 3.2 付费数据源

**付费数据源**：

| 数据源 | 特点 |
|--------|------|
| Polygon.io | 实时数据，质量高，价格适中 |
| Tiingo | 历史数据全，有免费层 |
| Intrinio | 基本面数据强 |
| Bloomberg | 机构级，非常贵 |
| Refinitiv | 机构级 |
| IB 数据 | 通过 IB 订阅，质量可靠 |

**个人建议**：
- 入门用 yfinance 足够
- 需要实时数据考虑 Polygon 或 IB
- 机构级数据性价比不高

### 3.3 另类数据

```mermaid
graph TB
    subgraph 另类数据["另类数据来源"]
        subgraph SEC["SEC 文件"]
            S1["SEC EDGAR"]
            S2["13F 持仓披露"]
            S3["内部人交易"]
        end
        subgraph 卫星数据
            W1["停车场车辆计数"]
            W2["价格昂贵"]
        end
        subgraph 社交媒体
            M1["Twitter/Reddit 情绪"]
            M2["需要 NLP 处理"]
        end
        subgraph 宏观数据
            H1["FRED（免费）"]
            H2["世界银行数据"]
        end
    end
```

---

## 四、回测平台

### 4.1 云端平台

```mermaid
graph TB
    subgraph 云端平台["云端量化平台"]
        subgraph QC["QuantConnect ⭐ 推荐"]
            Q1["免费使用"]
            Q2["多市场数据"]
            Q3["可对接实盘（IB/Alpaca 等）"]
            Q4["Python/C# 支持"]
            Q5["活跃社区"]
            Q6["地址：quantconnect.com"]
        end
        subgraph QP["Quantopian（已关闭）"]
            P1["曾经最流行，2020 年关闭"]
            P2["代码开源（Zipline）"]
        end
        subgraph BS["Blueshift"]
            B1["QuantInsti 旗下"]
            B2["类似 Quantopian"]
        end
    end
```

### 4.2 本地框架

```mermaid
graph TB
    subgraph 本地框架["本地回测框架"]
        subgraph Zipline
            Z1["Quantopian 开源"]
            Z2["设计优雅"]
            Z3["但维护减少"]
        end
        subgraph bt1["backtrader ⭐ 推荐"]
            B1["功能全面"]
            B2["文档详细"]
            B3["活跃维护"]
        end
        subgraph Lean["Lean（QuantConnect 开源）"]
            L1["与 QuantConnect 兼容"]
            L2["生产级别"]
            L3["C#/Python"]
        end
        subgraph vectorbt
            V1["向量化回测"]
            V2["速度极快"]
            V3["适合快速研究"]
        end
        subgraph bt2["bt"]
            T1["简洁易用"]
            T2["适合资产配置策略"]
        end
    end
```

---

## 五、回测的有效性

### 5.1 美股回测优势

```mermaid
graph TB
    subgraph 美股优势["美股回测相对更可靠"]
        subgraph 市场成熟
            C1["历史数据长（可回测几十年）"]
            C2["数据质量高"]
            C3["市场规则稳定"]
        end
        subgraph 交易限制少
            X1["无 T+1 限制"]
            X2["可做空"]
            X3["无涨跌停（有熔断）"]
        end
        subgraph 流动性好
            L1["大盘股滑点小"]
            L2["成交容易"]
        end
        subgraph 学术研究多
            Y1["大量因子研究"]
            Y2["策略验证充分"]
        end
    end
```

### 5.2 回测注意事项

```mermaid
graph TB
    subgraph 注意事项["全球市场回测注意事项"]
        subgraph 数据质量
            D1["免费数据可能有错误"]
            D2["验证数据准确性"]
            D3["注意分红/拆股调整"]
        end
        subgraph 幸存者偏差
            S1["使用包含退市股票的数据"]
            S2["或意识到这个偏差"]
        end
        subgraph PDT规则["PDT 规则"]
            P1["美股账户 < $25,000 有日内交易限制"]
            P2["回测时考虑这个限制"]
        end
        subgraph 时区
            T1["注意不同市场的交易时间"]
            T2["数据时间戳处理"]
        end
        subgraph 汇率
            H1["多市场策略考虑汇率风险"]
            H2["收益需换算"]
        end
    end
```

---

## 六、中国投资者参与全球市场

### 6.1 开户途径

```mermaid
graph TB
    subgraph 海外开户["中国居民海外开户"]
        subgraph IB["Interactive Brokers（盈透）"]
            I1["接受中国大陆居民开户"]
            I2["全球市场覆盖"]
            I3["入金：银行电汇"]
            I4["每年有外汇额度限制（5万美元）"]
        end
        subgraph 港美股["老虎证券/富途证券"]
            T1["中国团队，中文界面"]
            T2["美股/港股"]
            T3["开户相对简单"]
            T4["API 支持有限"]
        end
        subgraph 加密货币交易所
            C1["部分仍可使用"]
            C2["注意合规风险"]
            C3["P2P 入金"]
        end
        subgraph 注意事项
            N1["遵守外汇管理规定"]
            N2["了解税务申报义务"]
            N3["入金出金可能有限制"]
        end
    end
```

### 6.2 实践建议

```mermaid
graph TB
    subgraph 建议["中国投资者全球量化建议"]
        subgraph 入门阶段
            R1["先在 QuantConnect 学习和回测"]
            R2["用免费数据（yfinance）研究"]
            R3["模拟交易验证策略"]
        end
        subgraph 开户
            K1["IB 开户（接受大陆居民）"]
            K2["准备好资金入金渠道"]
            K3["了解 API 使用方法"]
        end
        subgraph 策略选择
            C1["ETF 轮动策略"]
            C2["美股因子策略"]
            C3["全球资产配置"]
        end
        subgraph 风险考虑
            F1["汇率风险"]
            F2["时区问题（交易时间）"]
            F3["资金出入境限制"]
        end
    end
```

---

## 七、总结

```mermaid
graph TB
    subgraph 要点["全球量化交易要点"]
        subgraph 接口
            J1["IB 是个人量化的首选"]
            J2["Alpaca 零佣金适合美股"]
            J3["ccxt 统一加密货币接口"]
        end
        subgraph 数据
            D1["yfinance 免费够用"]
            D2["需要实时数据考虑付费"]
            D3["QuantConnect 提供免费数据"]
        end
        subgraph 回测
            H1["QuantConnect 云端免费"]
            H2["backtrader 本地开发"]
            H3["美股数据质量较高"]
        end
        subgraph 中国投资者
            Z1["IB 可开户"]
            Z2["注意外汇限制"]
            Z3["考虑时区和汇率"]
        end
    end
    要点 --> 结论["全球市场给个人量化提供了更广阔的空间，<br/>IB + QuantConnect 是很好的起点"]
```

---

## 相关文章

- [上一篇：03 - 中国大陆量化交易接口与数据](/articles/quant/quant-03-中国大陆量化交易接口与数据/)
- [下一篇：05 - 个人量化常用策略详解](/articles/quant/quant-05-个人量化常用策略详解/)
