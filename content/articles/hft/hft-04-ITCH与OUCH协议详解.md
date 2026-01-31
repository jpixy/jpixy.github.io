+++
title = "04.ITCH与OUCH协议详解"
date = 2026-01-13
description = "NASDAQ原生协议ITCH/OUCH深度解析：二进制格式、消息类型与超低延迟设计"
[taxonomies]
tags = ["hft", "itch", "ouch", "protocol", "nasdaq"]
+++

# HFT协议系列-ITCH与OUCH协议详解

ITCH 和 OUCH 是 NASDAQ 开发的原生二进制协议，代表了交易所协议的极致低延迟设计，本文深入解析其机制与实现。

---

## 一、协议概述

### 1.1 ITCH 与 OUCH 的关系

| 协议 | 用途 | 方向 |
|-----|------|------|
| ITCH | 行情数据分发 | 交易所 → 客户端 |
| OUCH | 订单输入 | 客户端 ↔ 交易所 |

```
客户端                         交易所
   │                            │
   │◀────── ITCH 行情 ──────────│
   │                            │
   │─────── OUCH 订单 ─────────▶│
   │◀───── OUCH 确认 ───────────│
```

### 1.2 设计哲学

| 原则 | 说明 |
|-----|------|
| 极简 | 只包含必要信息 |
| 定长 | 固定消息大小，快速解析 |
| 二进制 | 无文本转换开销 |
| 无状态 | ITCH 完整信息，无增量依赖 |
| 无会话层 | 最小协议开销 |

### 1.3 使用场景

| 交易所/系统 | 使用协议 |
|------------|---------|
| NASDAQ US | ITCH 5.0, OUCH 5.0 |
| NASDAQ Nordic | ITCH, OUCH |
| LSE (Turquoise) | ITCH 变体 |
| BATS/CBOE | PITCH (类似) |
| 新加坡交易所 | ITCH 变体 |

---

## 二、ITCH 协议详解

### 2.1 ITCH 消息格式

**通用结构**：
```
┌──────────────────────────────────────────┐
│  消息类型 (1 byte)                        │
├──────────────────────────────────────────┤
│  时间戳 (6 bytes)                         │
├──────────────────────────────────────────┤
│  消息特定字段 (变化)                      │
└──────────────────────────────────────────┘
```

### 2.2 时间戳格式

- 6 字节无符号整数
- 纳秒精度
- 从午夜开始计算
- 范围覆盖一个交易日

### 2.3 消息类型

**系统消息**：

| 类型 | 代码 | 说明 |
|-----|------|------|
| System Event | S | 系统状态变更 |
| Stock Directory | R | 股票基础信息 |
| Stock Trading Action | H | 交易状态（暂停/恢复） |
| Reg SHO Restriction | Y | 卖空限制 |
| Market Participant Position | L | 做市商信息 |

**订单簿消息**：

| 类型 | 代码 | 说明 | 大小 |
|-----|------|------|------|
| Add Order | A | 新订单加入订单簿 | 36 bytes |
| Add Order with MPID | F | 带做市商标识 | 40 bytes |
| Order Executed | E | 订单成交 | 31 bytes |
| Order Executed with Price | C | 带成交价格 | 36 bytes |
| Order Cancel | X | 部分撤销 | 23 bytes |
| Order Delete | D | 完全删除 | 19 bytes |
| Order Replace | U | 订单替换 | 35 bytes |

**交易消息**：

| 类型 | 代码 | 说明 |
|-----|------|------|
| Trade (Non-Cross) | P | 非集合竞价成交 |
| Cross Trade | Q | 集合竞价成交 |
| Broken Trade | B | 取消成交 |

### 2.4 Add Order 消息结构

| 字段 | 偏移 | 大小 | 类型 | 说明 |
|-----|------|------|------|------|
| Message Type | 0 | 1 | char | 'A' |
| Timestamp | 1 | 6 | uint48 | 纳秒 |
| Order Reference | 7 | 8 | uint64 | 订单唯一标识 |
| Buy/Sell | 15 | 1 | char | 'B' 或 'S' |
| Shares | 16 | 4 | uint32 | 数量 |
| Stock | 20 | 8 | char[8] | 股票代码（右填空格） |
| Price | 28 | 4 | uint32 | 价格（4位小数） |

**总大小**：36 字节

### 2.5 Order Executed 消息结构

| 字段 | 偏移 | 大小 | 类型 | 说明 |
|-----|------|------|------|------|
| Message Type | 0 | 1 | char | 'E' |
| Timestamp | 1 | 6 | uint48 | 纳秒 |
| Order Reference | 7 | 8 | uint64 | 订单标识 |
| Executed Shares | 15 | 4 | uint32 | 成交数量 |
| Match Number | 19 | 8 | uint64 | 成交编号 |

**总大小**：31 字节

### 2.6 价格表示

ITCH 使用定点数表示价格：

| 格式 | 说明 |
|-----|------|
| 4 位小数 | 价格 × 10000 存储 |
| 例：$123.45 | 存储为 1234500 |
| 无符号整数 | 4 字节 uint32 |

---

## 三、OUCH 协议详解

### 3.1 OUCH 消息格式

**客户端发送（Inbound）**：

| 类型 | 代码 | 说明 | 大小 |
|-----|------|------|------|
| Enter Order | O | 新订单 | 49 bytes |
| Replace Order | U | 改单 | 47 bytes |
| Cancel Order | X | 撤单 | 19 bytes |
| Modify Order | M | 修改（仅数量） | 19 bytes |

**交易所发送（Outbound）**：

| 类型 | 代码 | 说明 |
|-----|------|------|
| System Event | S | 系统事件 |
| Accepted | A | 订单接受 |
| Replaced | U | 改单确认 |
| Canceled | C | 撤单确认 |
| Executed | E | 成交 |
| Broken Trade | B | 成交取消 |
| Rejected | J | 订单拒绝 |

### 3.2 Enter Order 消息

| 字段 | 偏移 | 大小 | 说明 |
|-----|------|------|------|
| Message Type | 0 | 1 | 'O' |
| Order Token | 1 | 14 | 客户端订单标识 |
| Buy/Sell | 15 | 1 | 'B' 或 'S' |
| Shares | 16 | 4 | 数量 |
| Stock | 20 | 8 | 股票代码 |
| Price | 28 | 4 | 价格 |
| Time in Force | 32 | 4 | 有效期 |
| Firm | 36 | 4 | 公司代码 |
| Display | 40 | 1 | 显示类型 |
| Capacity | 41 | 1 | 身份 |
| Intermarket Sweep | 42 | 1 | ISO 标识 |
| Minimum Quantity | 43 | 4 | 最小成交量 |
| Cross Type | 47 | 1 | 集合竞价类型 |
| Customer Type | 48 | 1 | 客户类型 |

### 3.3 Accepted 消息

确认订单已进入订单簿，包含：
- 订单 Token（客户端标识）
- Order Reference Number（交易所标识）
- 接受时间戳
- 订单详情

### 3.4 Executed 消息

| 字段 | 说明 |
|-----|------|
| Timestamp | 成交时间 |
| Order Token | 客户端标识 |
| Executed Shares | 成交数量 |
| Execution Price | 成交价格 |
| Liquidity Flag | 流动性标识（添加/移除） |
| Match Number | 成交编号 |

### 3.5 有效期类型（Time in Force）

| 值 | 类型 | 说明 |
|---|------|------|
| 0 | Immediate | 立即成交或取消 |
| 99998 | Market Hours | 交易时段有效 |
| 99999 | System Hours | 系统时段有效 |
| 其他 | 秒数 | 指定秒数后过期 |

---

## 四、订单簿重建

### 4.1 ITCH 订单簿维护

使用 ITCH 消息重建完整订单簿：

```
收到 Add Order (A):
    → 添加订单到对应价格档位

收到 Order Executed (E):
    → 减少订单数量
    → 数量为 0 则删除

收到 Order Cancel (X):
    → 减少订单数量
    → 数量为 0 则删除

收到 Order Delete (D):
    → 删除订单

收到 Order Replace (U):
    → 删除旧订单
    → 添加新订单
```

### 4.2 数据结构设计

| 需求 | 数据结构 | 说明 |
|-----|---------|------|
| 订单查找 | HashMap | O(1) 按 Order Reference |
| 价格档位 | 红黑树/跳表 | O(log n) 有序 |
| 同价订单 | 双向链表 | 维护时间优先 |
| 内存池 | 预分配 | 避免运行时分配 |

### 4.3 订单簿快照

ITCH 不提供显式快照，需要：
1. 从交易日开始接收所有消息
2. 或使用交易所的快照服务
3. 增量更新维护实时状态

---

## 五、网络传输

### 5.1 传输层

| 服务 | 协议 | 特点 |
|-----|------|------|
| ITCH 行情 | UDP 组播 | 高效，一对多 |
| ITCH 恢复 | TCP | 可靠，丢包恢复 |
| OUCH 订单 | TCP | 可靠，顺序保证 |

### 5.2 MoldUDP64 封装

NASDAQ 使用 MoldUDP64 协议封装 ITCH：

| 字段 | 大小 | 说明 |
|-----|------|------|
| Session | 10 bytes | 会话标识 |
| Sequence Number | 8 bytes | 序号 |
| Message Count | 2 bytes | 消息数量 |
| Messages | 变长 | 多条 ITCH 消息 |

每条消息格式：
```
[2 bytes: 消息长度][N bytes: 消息内容]
```

### 5.3 SoupBinTCP

OUCH 使用 SoupBinTCP 作为会话层：

**消息类型**：

| 代码 | 类型 | 方向 |
|-----|------|------|
| + | Debug | 双向 |
| A | Login Accepted | S→C |
| J | Login Rejected | S→C |
| S | Sequenced Data | S→C |
| H | Server Heartbeat | S→C |
| O | Logout Request | C→S |
| L | Login Request | C→S |
| U | Unsequenced Data | C→S |
| R | Client Heartbeat | C→S |

---

## 六、低延迟实现

### 6.1 解析优化

| 策略 | 说明 |
|-----|------|
| 定长消息 | 无需解析长度 |
| 固定偏移 | 直接内存访问 |
| 无字符串解析 | 二进制直接使用 |
| 类型分发 | 按首字节跳转 |
| 内联解析 | 避免函数调用 |

### 6.2 消息处理模式

```
接收缓冲区
    │
    ▼
┌─────────────────┐
│ 读取消息类型     │  ← 单字节读取
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
  Add(A)   Exec(E)  Delete(D)  ...
    │         │        │
    ▼         ▼        ▼
 专用处理   专用处理  专用处理   ← 无虚函数
```

### 6.3 内存布局

| 优化 | 说明 |
|-----|------|
| 结构体对齐 | 匹配消息格式 |
| 打包属性 | 无填充字节 |
| 缓存行对齐 | 关键数据 64 字节对齐 |
| 预分配 | 避免运行时分配 |

### 6.4 性能基准

| 操作 | 延迟 |
|-----|------|
| 消息解析 | <100ns |
| 订单簿更新 | 100-500ns |
| 端到端处理 | 1-5μs |

---

## 七、与其他协议对比

| 对比项 | ITCH/OUCH | FIX | FAST |
|-------|----------|-----|------|
| 格式 | 二进制定长 | 文本 | 二进制变长 |
| 设计目标 | 极致低延迟 | 通用互操作 | 压缩传输 |
| 消息大小 | 最小 | 最大 | 中等 |
| 解析速度 | 最快 | 最慢 | 快 |
| 复杂度 | 低 | 高 | 高 |
| 状态依赖 | 无 | 有（会话） | 有（增量） |
| 通用性 | NASDAQ 系 | 全球通用 | 行情专用 |

---

## 八、实现建议

### 8.1 关键实现点

| 方面 | 建议 |
|-----|------|
| 解析器 | 代码生成，零开销 |
| 订单簿 | 预分配，无锁更新 |
| 网络 | 内核旁路，轮询 |
| 时间 | 硬件时间戳 |
| 日志 | 异步，零拷贝 |

### 8.2 常见陷阱

| 问题 | 解决 |
|-----|------|
| 字节序 | ITCH 使用大端序 |
| 股票代码空格 | 右侧填充空格 |
| 价格精度 | 注意小数点位置 |
| 序号连续性 | 检测丢包 |
| 时间戳回绕 | 跨日处理 |

---

## 参考资料

- [NASDAQ ITCH 5.0 Specification](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/NQTVITCHSpecification.pdf)
- [NASDAQ OUCH 5.0 Specification](https://www.nasdaqtrader.com/content/technicalsupport/specifications/TradingProducts/OUCH5.0.pdf)
- [MoldUDP64 Specification](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/moldudp64.pdf)
- [SoupBinTCP Specification](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/soupbintcp.pdf)

---

## 相关文章

- [上一篇：FAST协议详解](/articles/hft/hft-03-FAST协议详解/)
- [下一篇：数据采集层设计](/articles/hft/hft-05-数据采集层设计/)
