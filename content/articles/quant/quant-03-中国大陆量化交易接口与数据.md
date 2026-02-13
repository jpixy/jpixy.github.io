+++
title = "03. 中国大陆量化交易接口与数据"
date = 2025-01-15
weight = 3000
description = "中国大陆个人量化交易可用的交易接口、可交易产品、数据来源及回测平台详解"
[taxonomies]
tags = ["quant", "trading", "china", "api", "data"]
+++

## 概述

中国大陆的量化交易环境相对特殊，个人投资者面临一定限制。本文详细介绍在中国大陆可用的交易接口、产品、数据来源和回测工具。

---

## 一、可交易产品

### 1.1 产品分类

```mermaid
graph TB
    subgraph 品种["中国大陆个人可交易品种"]
        subgraph 股票市场
            G1["A 股 - 上海、深圳"]
            G2["港股通 - 通过沪港通/深港通"]
            G3["北交所股票"]
        end
        subgraph 基金
            J1["ETF 场内交易"]
            J2["LOF 场内交易"]
            J3["场外基金 T+1或更长"]
        end
        subgraph 期货
            Q1["商品期货 需开户"]
            Q2["股指期货 50万门槛"]
            Q3["国债期货"]
        end
        subgraph 期权
            QQ1["50ETF/300ETF 期权"]
            QQ2["商品期权"]
            QQ3["个股期权 有限"]
        end
        subgraph 债券
            Z1["可转债 T+0 个人较常用"]
            Z2["国债"]
            Z3["企业债"]
        end
    end
```

### 1.2 各品种量化特点

**产品量化适合度对比**：

| 品种 | 量化友好度 | 备注 |
|------|-----------|------|
| A股 | ⭐⭐⭐ | T+1 限制，涨跌停限制 |
| ETF | ⭐⭐⭐⭐ | 流动性好，成本低 |
| 可转债 | ⭐⭐⭐⭐⭐ | T+0，无涨跌停，灵活 |
| 商品期货 | ⭐⭐⭐⭐ | T+0，杠杆，双向 |
| 股指期货 | ⭐⭐⭐⭐ | 门槛高，流动性好 |
| 期权 | ⭐⭐⭐ | 复杂度高 |

**个人量化推荐**：
1. 可转债（T+0 灵活）
2. ETF（成本低）
3. 商品期货（双向交易）

---

## 二、交易接口

### 2.1 股票/基金接口

```mermaid
graph TB
    subgraph A股接口["A股程序化交易接口"]
        subgraph 官方["券商官方接口 - 有限"]
            G1["大多数券商不对个人开放程序化接口"]
            G2["部分券商有条件开放: 如资金量要求"]
            G3["需咨询具体券商"]
        end
        subgraph 第三方接口
            subgraph QMT["QMT 迅投"]
                Q1["部分券商支持"]
                Q2["需申请，有一定门槛"]
                Q3["较专业的量化平台"]
            end
            subgraph PTrade["PTrade 恒生"]
                P1["机构级别"]
                P2["个人较难获取"]
            end
            subgraph easytrader["easytrader 开源"]
                E1["模拟客户端操作"]
                E2["非官方，有风险"]
                E3["稳定性不保证"]
            end
        end
        subgraph 模拟盘接口
            M1["聚宽模拟交易"]
            M2["米筐模拟交易"]
            M3["优矿模拟交易"]
        end
    end
```

⚠️ **注意**：
- A股程序化交易对个人限制较多
- 谨慎使用非官方接口
- 优先考虑券商官方渠道

### 2.2 期货接口

```mermaid
graph TB
    subgraph 期货接口["期货程序化接口 - 相对开放"]
        subgraph CTP["CTP 接口 - 推荐"]
            C1["期货公司官方接口"]
            C2["个人可申请"]
            C3["稳定可靠"]
            C4["需要编程能力"]
        end
        subgraph Python封装["Python 封装"]
            P1["vnpy: 国内最流行"]
            P2["ctpbee"]
            P3["openctp: 仿真/回测"]
        end
        subgraph 申请流程
            A1["1. 在期货公司开户"]
            A2["2. 申请 CTP 接口"]
            A3["3. 获取交易账号和授权码"]
            A4["4. 连接开发"]
        end
        subgraph 其他接口
            O1["飞创 Femas"]
            O2["易盛"]
            O3["恒生 UFT"]
        end
    end
    A1 --> A2 --> A3 --> A4
```

**期货量化开发示例（vnpy）**：
```python
from vnpy.gateway.ctp import CtpGateway
from vnpy.trader.engine import MainEngine

# 初始化
main_engine = MainEngine()
main_engine.add_gateway(CtpGateway)

# 连接
setting = {
    "用户名": "xxx",
    "密码": "xxx",
    "经纪商代码": "xxx",
    "交易服务器": "xxx",
    "行情服务器": "xxx",
}
main_engine.connect(setting, "CTP")
```

### 2.3 可转债接口

```mermaid
graph TB
    subgraph 可转债接口["可转债交易接口"]
        subgraph 通道["走股票通道"]
            T1["可转债通过股票账户交易"]
            T2["接口与股票相同"]
        end
        subgraph 常用方式
            F1["QMT: 如券商支持"]
            F2["easytrader: 非官方"]
            F3["券商 API: 如有"]
        end
        subgraph 量化优势["可转债量化优势"]
            Y1["T+0 交易"]
            Y2["无涨跌停限制, 有临停"]
            Y3["品种数量适中, 约 500 只"]
            Y4["适合日内和短线策略"]
        end
    end
```

---

## 三、数据来源

### 3.1 免费数据源

```mermaid
graph TB
    subgraph 免费数据["免费数据获取"]
        subgraph Tushare["Tushare: 推荐"]
            T1["国内最流行的免费数据源"]
            T2["A股、基金、期货、可转债数据"]
            T3["需注册，有积分限制"]
            T4["高级功能需付费"]
            T5["地址：tushare.pro"]
        end
        subgraph AKShare["AKShare: 推荐"]
            A1["完全免费开源"]
            A2["数据覆盖广"]
            A3["更新活跃"]
            A4["地址：github.com/akfamily/akshare"]
        end
        subgraph BaoStock
            B1["免费股票数据"]
            B2["历史数据较全"]
            B3["更新可能有延迟"]
        end
        subgraph 网页["新浪/东方财富"]
            W1["网页抓取"]
            W2["不稳定，可能被封"]
            W3["适合临时使用"]
        end
    end
```

**数据获取示例：**

```python
# Tushare 示例
import tushare as ts
pro = ts.pro_api('你的token')
df = pro.daily(ts_code='000001.SZ', start_date='20200101')

# AKShare 示例
import akshare as ak
df = ak.stock_zh_a_hist(symbol="000001", period="daily")

# BaoStock 示例
import baostock as bs
bs.login()
rs = bs.query_history_k_data_plus("sh.600000")
```

### 3.2 付费数据源

**付费数据源**：

| 数据源 | 特点 |
|--------|------|
| Tushare Pro | 积分制，高级数据需付费 |
| Wind（万得） | 机构级，非常贵，个人较难获取 |
| 聚源数据 | 专业级，价格较高 |
| 通联数据 | 专业级，有个人版 |
| 米筐 | 量化平台，数据较全 |

**个人建议**：
- 入门用免费数据源足够
- Tushare Pro 性价比较高
- 机构级数据个人用不太值得

### 3.3 另类数据

```mermaid
graph TB
    subgraph 另类数据["另类数据来源"]
        subgraph 公告数据
            G1["巨潮资讯网"]
            G2["上交所/深交所公告"]
            G3["可做事件驱动策略"]
        end
        subgraph 舆情数据
            Y1["雪球、东方财富股吧"]
            Y2["新闻舆情"]
            Y3["需要 NLP 处理"]
        end
        subgraph 宏观数据
            H1["国家统计局"]
            H2["央行数据"]
            H3["海关数据"]
        end
        subgraph 资金流向
            Z1["龙虎榜数据"]
            Z2["北向资金"]
            Z3["融资融券"]
        end
    end
```

---

## 四、回测平台

### 4.1 在线回测平台

```mermaid
graph TB
    subgraph 在线平台["国内在线量化平台"]
        subgraph JQ["聚宽 JoinQuant ⭐ 推荐"]
            J1["最流行的国内量化平台"]
            J2["免费额度较多"]
            J3["数据覆盖全"]
            J4["社区活跃"]
            J5["支持股票、期货、ETF"]
            J6["地址：joinquant.com"]
        end
        subgraph RQ["米筐 RiceQuant"]
            R1["专业级平台"]
            R2["数据质量高"]
            R3["部分功能收费"]
            R4["地址：ricequant.com"]
        end
        subgraph UQ["优矿 Uqer"]
            U1["通联数据旗下"]
            U2["因子研究强"]
            U3["地址：uqer.datayes.com"]
        end
        subgraph MQ["掘金量化"]
            M1["支持实盘接口"]
            M2["期货支持好"]
            M3["地址：myquant.cn"]
        end
    end
```

### 4.2 本地回测框架

```mermaid
graph TB
    subgraph 本地框架["本地回测框架"]
        subgraph vnpy["vnpy: 推荐"]
            V1["国内最流行的开源框架"]
            V2["支持回测和实盘"]
            V3["期货支持最好"]
            V4["有图形界面"]
            V5["地址：github.com/vnpy/vnpy"]
        end
        subgraph backtrader
            B1["国际流行的回测框架"]
            B2["功能完善"]
            B3["学习资源多"]
            B4["地址：backtrader.com"]
        end
        subgraph Zipline
            Z1["Quantopian 开源"]
            Z2["设计优雅"]
            Z3["国内数据需要适配"]
        end
        subgraph 自建框架
            S1["完全自定义"]
            S2["学习价值高"]
            S3["适合深入理解"]
        end
    end
```

---

## 五、回测的有效性

### 5.1 中国市场回测的挑战

```mermaid
graph TB
    subgraph A股特殊性["A股市场特殊性"]
        subgraph 制度特点
            Z1["T+1 交易制度"]
            Z2["涨跌停限制"]
            Z3["做空限制"]
            Z4["政策影响大"]
        end
        subgraph 市场特点
            S1["散户占比高"]
            S2["投机氛围重"]
            S3["政策市特征"]
            S4["风格轮动剧烈"]
        end
        subgraph 回测挑战
            H1["涨跌停时可能无法成交"]
            H2["新股/次新股数据特殊"]
            H3["停牌数据处理"]
            H4["制度变化, 如注册制"]
        end
    end
```

### 5.2 提高回测有效性

```mermaid
graph TB
    subgraph 提高可靠性["提高回测可靠性"]
        subgraph T1["1. 考虑交易限制"]
            T1A["涨跌停不能买入/卖出"]
            T1B["停牌处理"]
            T1C["T+1 限制"]
        end
        subgraph T2["2. 真实成本估算"]
            T2A["佣金: 约万2-万3"]
            T2B["印花税: 卖出千1"]
            T2C["滑点: 估算0.1-0.3%"]
        end
        subgraph T3["3. 使用全市场数据"]
            T3A["包含退市股票"]
            T3B["包含 ST 股票"]
            T3C["避免幸存者偏差"]
        end
        subgraph T4["4. 样本外测试"]
            T4A["留出近期数据验证"]
            T4B["Walk-forward 分析"]
        end
        subgraph T5["5. 保守预期"]
            T5A["实盘通常比回测差 30-50%"]
            T5B["预留安全边际"]
        end
    end
```

---

## 六、实践建议

### 6.1 个人量化路径

```mermaid
graph TB
    subgraph 路径["中国个人量化推荐路径"]
        subgraph 入门阶段
            R1["在聚宽学习和回测"]
            R2["用免费数据: AKShare/Tushare"]
            R3["先做 ETF/可转债策略"]
            R4["模拟交易 3-6 个月"]
        end
        subgraph 进阶阶段
            J1["搭建本地回测环境"]
            J2["学习 vnpy: 如做期货"]
            J3["申请 CTP 接口: 期货"]
            J4["小资金实盘验证"]
        end
        subgraph 稳定阶段
            W1["多策略组合"]
            W2["自动化运维"]
            W3["持续优化迭代"]
        end
    end
    入门阶段 --> 进阶阶段 --> 稳定阶段
```

### 6.2 品种选择建议

```mermaid
graph TB
    subgraph 品种推荐["个人量化品种推荐"]
        subgraph 首选["首选：可转债"]
            S1["T+0 灵活"]
            S2["门槛低"]
            S3["策略容易验证"]
            S4["适合日内和短线"]
        end
        subgraph 次选["次选：ETF"]
            C1["成本低"]
            C2["流动性好"]
            C3["适合择时和轮动"]
        end
        subgraph 进阶["进阶：商品期货"]
            J1["接口开放: CTP"]
            J2["T+0 双向"]
            J3["杠杆需注意风险"]
        end
        subgraph A股["A 股"]
            A1["T+1 限制较大"]
            A2["更适合中长期策略"]
            A3["因子策略/价值投资"]
        end
    end
```

---

## 七、总结

```mermaid
graph TB
    subgraph 要点["中国大陆个人量化要点"]
        subgraph 接口
            J1["A股接口限制多，期货 CTP 相对开放"]
            J2["可转债通过股票通道"]
            J3["优先使用官方渠道"]
        end
        subgraph 数据
            D1["Tushare/AKShare 足够入门"]
            D2["聚宽平台数据较全"]
            D3["注意数据质量验证"]
        end
        subgraph 产品
            C1["可转债/ETF 对个人最友好"]
            C2["期货接口开放但有杠杆风险"]
            C3["A股 T+1 限制中低频策略"]
        end
        subgraph 回测
            H1["考虑 A 股特殊规则"]
            H2["真实成本估算"]
            H3["保守预期，实盘会更差"]
        end
    end
    要点 --> 结论["在中国做个人量化，可转债和期货是相对友好的选择"]
```

---

## 相关文章

- [上一篇：02 - 中低频量化交易最佳实践](@/articles/quant/quant-02-中低频量化交易最佳实践.md)
- [下一篇：04 - 全球量化交易接口与数据](@/articles/quant/quant-04-全球量化交易接口与数据.md)
