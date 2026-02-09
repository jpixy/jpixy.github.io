+++
title = "18.交易所撮合引擎原理"
date = 2026-01-21
description = "深入剖析交易所撮合引擎，包括撮合算法、订单类型、Queue Position、Exchange Fees和Maker/Taker"
[taxonomies]
tags = ["HFT", "交易所", "撮合引擎", "订单类型", "做市"]
+++

## 概述

理解交易所撮合引擎的工作原理对于HFT策略至关重要。本文深入讲解撮合机制。

---

## 一、撮合算法

### 1.1 Price-Time Priority (价格-时间优先)

```
原则：
1. 最优价格优先成交
2. 同价格先到先成交

示例：
Order Book:
  Bids                    Asks
  Price   Qty   Time      Price   Qty   Time
  100.00  100   09:30:01  100.01  200   09:30:00
  100.00  50    09:30:02  100.01  100   09:30:01
  99.99   200   09:30:00  100.02  150   09:30:00

新订单: Buy 250 @ Market

撮合过程：
1. 匹配100.01 × 200 (09:30:00的订单先成交)
2. 匹配100.01 × 50  (剩余需求)
3. 剩余0，完成

成交报告：
- 200 @ 100.01
- 50 @ 100.01
```

### 1.2 Pro-Rata (按比例分配)

```
原则：
1. 最优价格优先
2. 同价格按订单大小比例分配

示例：
Ask level @ 100.01:
  Order A: 1000
  Order B: 500  
  Order C: 500
  Total: 2000

新订单: Buy 1000 @ 100.01

分配（按比例）:
  Order A: 1000/2000 × 1000 = 500
  Order B: 500/2000 × 1000 = 250
  Order C: 500/2000 × 1000 = 250

适用于：期货市场（如CME的某些合约）
```

### 1.3 FIFO with Pro-Rata Allocation

```
混合模式：
1. 一定数量按FIFO
2. 剩余按Pro-Rata

示例：CME Eurodollar
- 前X手按时间优先
- 剩余按比例分配
```

---

## 二、订单类型

### 2.1 基本订单类型

```cpp
enum class OrderType {
    // 市价单：立即以最优价格成交
    MARKET,
    
    // 限价单：指定价格或更优成交
    LIMIT,
    
    // 止损单：价格触及后转为市价单
    STOP,
    
    // 止损限价：价格触及后转为限价单
    STOP_LIMIT,
    
    // 盘中有效
    DAY,
    
    // 撤销前有效
    GTC,  // Good Till Cancel
    
    // 立即成交否则取消
    IOC,  // Immediate Or Cancel
    
    // 全部成交否则取消
    FOK,  // Fill Or Kill
    
    // 收盘价成交
    MOC,  // Market On Close
    
    // 开盘价成交
    MOO,  // Market On Open
};
```

### 2.2 高级订单类型

```cpp
// 冰山单：只显示部分数量
struct IcebergOrder {
    uint64_t total_qty;
    uint64_t display_qty;  // 可见数量
    uint64_t filled_qty;
    
    uint64_t visible_qty() const {
        uint64_t remaining = total_qty - filled_qty;
        return std::min(display_qty, remaining);
    }
    
    void on_fill(uint64_t qty) {
        filled_qty += qty;
        // 显示数量可能会"刷新"
    }
};

// Peg订单：跟踪市场价格
struct PegOrder {
    enum class PegType {
        PRIMARY,    // 跟踪同侧最优价
        MARKET,     // 跟踪对手侧最优价
        MIDPOINT,   // 跟踪中间价
    };
    
    PegType peg_type;
    int64_t offset;  // 相对偏移（可正可负）
    
    Price calculate_price(Price bid, Price ask) const {
        switch (peg_type) {
            case PegType::PRIMARY:
                return bid + offset;  // 假设买单
            case PegType::MARKET:
                return ask + offset;
            case PegType::MIDPOINT:
                return (bid + ask) / 2 + offset;
        }
    }
};
```

### 2.3 TIF (Time in Force)

```
DAY:     当日有效，收盘自动取消
GTC:     长期有效，直到成交或手动取消
IOC:     立即成交，未成交部分取消
FOK:     全部成交或全部取消
GTD:     指定日期前有效
GAT:     指定时间后生效

HFT使用：
- IOC：试探市场，避免被动挂单
- FOK：全仓操作，避免部分成交
- DAY：做市商常用
```

---

## 三、Queue Position

### 3.1 队列位置重要性

```
在Price-Time优先的市场：
- 早到的订单有更高成交概率
- 队列位置 = 潜在利润

示例：
Best Bid @ 100.00 总量1000手
你的订单在位置200（前面有200手）

如果成交500手：
- 你的订单成交（如果你排在前500）
- 否则只能等待

Queue Position策略：
1. 预测价格稳定时提前挂单
2. 价格可能变动时取消
3. 使用Order Modify保持位置
```

### 3.2 队列位置计算

```cpp
class QueuePositionTracker {
public:
    void on_order_add(uint64_t order_id, Price price, Quantity qty) {
        auto& level = levels_[price];
        level.total_qty += qty;
        level.orders.push_back({order_id, qty});
    }
    
    void on_order_cancel(uint64_t order_id, Price price, Quantity qty) {
        auto& level = levels_[price];
        level.total_qty -= qty;
        
        // 更新队列位置
        auto it = std::find_if(level.orders.begin(), level.orders.end(),
            [order_id](const auto& o) { return o.id == order_id; });
        
        if (it != level.orders.end()) {
            level.orders.erase(it);
        }
    }
    
    // 估算我的订单的队列位置
    Quantity estimate_position(uint64_t my_order_id, Price price) {
        auto& level = levels_[price];
        Quantity position = 0;
        
        for (const auto& order : level.orders) {
            if (order.id == my_order_id) {
                return position;
            }
            position += order.qty;
        }
        
        return position;
    }
    
    // 估算成交概率
    double estimate_fill_probability(uint64_t my_order_id, Price price,
                                     Quantity expected_volume) {
        Quantity position = estimate_position(my_order_id, price);
        Quantity my_qty = get_order_qty(my_order_id);
        
        if (position + my_qty <= expected_volume) {
            return 1.0;  // 肯定成交
        } else if (position >= expected_volume) {
            return 0.0;  // 肯定不成交
        } else {
            return double(expected_volume - position) / my_qty;
        }
    }
    
private:
    struct Order { uint64_t id; Quantity qty; };
    struct Level {
        Quantity total_qty = 0;
        std::vector<Order> orders;
    };
    
    std::unordered_map<Price, Level> levels_;
};
```

---

## 四、Maker/Taker与手续费

### 4.1 手续费结构

**Maker** (提供流动性) vs **Taker** (消耗流动性)

| 角色 | 说明 |
|------|------|
| Maker | 挂限价单，等待被成交；通常获得返佣（rebate） |
| Taker | 主动成交对手盘的订单；支付手续费 |

**示例费率（每手）**：

| 交易所 | Maker | Taker |
|--------|-------|-------|
| NYSE | -$0.0010 | +$0.0030 |
| NASDAQ | -$0.0020 | +$0.0030 |
| CME | +$0.0010 | +$0.0020 |

> 负数 = 返佣，正数 = 费用

### 4.2 费用感知策略

```cpp
class FeeAwareStrategy {
public:
    // 计算实际盈亏（包含费用）
    double calculate_net_pnl(const Trade& trade) {
        double gross_pnl = trade.price * trade.qty * 
                          (trade.is_buy ? -1 : 1);
        
        double fee;
        if (trade.is_maker) {
            fee = trade.qty * maker_fee_;  // 可能是负数（返佣）
        } else {
            fee = trade.qty * taker_fee_;
        }
        
        return gross_pnl - fee;
    }
    
    // 决定是主动成交还是挂单
    bool should_take_liquidity(double expected_price_move,
                               double current_spread) {
        // 如果预期价格变动大于Taker费用，主动成交
        double taker_cost = taker_fee_;
        double maker_rebate = -maker_fee_;
        
        // 考虑：
        // 1. 主动成交立即执行但付费
        // 2. 挂单可能获得返佣但可能不成交
        
        return expected_price_move > taker_cost + current_spread / 2;
    }
    
private:
    double maker_fee_ = -0.001;  // 返佣
    double taker_fee_ = 0.003;   // 费用
};
```

---

## 五、交易所特性

### 5.1 Order Matching特点

```cpp
struct ExchangeCharacteristics {
    // 撮合算法
    enum class MatchAlgo { FIFO, PRORATA, HYBRID } match_algo;
    
    // 最小价格变动
    double tick_size;
    
    // 最小数量
    int lot_size;
    
    // 费率
    double maker_fee;
    double taker_fee;
    
    // 典型延迟
    uint64_t typical_latency_us;
    
    // 消息速率限制
    int max_messages_per_second;
    
    // 支持的订单类型
    std::set<OrderType> supported_order_types;
};

// 示例
ExchangeCharacteristics nasdaq = {
    .match_algo = MatchAlgo::FIFO,
    .tick_size = 0.01,
    .lot_size = 1,
    .maker_fee = -0.002,
    .taker_fee = 0.003,
    .typical_latency_us = 50,
    .max_messages_per_second = 10000,
    .supported_order_types = {LIMIT, MARKET, IOC, FOK, DAY, GTC}
};
```

### 5.2 Self-Trade Prevention

```cpp
// 防止自成交
enum class STPAction {
    CANCEL_NEWEST,    // 取消新订单
    CANCEL_OLDEST,    // 取消旧订单
    CANCEL_BOTH,      // 取消双方
    DECREMENT         // 减少数量
};

class SelfTradePrevention {
public:
    bool would_self_trade(const Order& new_order) {
        // 检查新订单是否会与自己的挂单成交
        for (const auto& existing : my_orders_) {
            if (existing.symbol != new_order.symbol) continue;
            if (existing.side == new_order.side) continue;
            
            if (new_order.side == Side::BUY) {
                if (new_order.price >= existing.price) {
                    return true;  // 买单价格 >= 卖单价格，会成交
                }
            } else {
                if (new_order.price <= existing.price) {
                    return true;
                }
            }
        }
        return false;
    }
    
private:
    std::vector<Order> my_orders_;
};
```

---

## 六、延迟与Co-location

### 6.1 延迟组成

**典型延迟分解**：

| 组件 | 延迟 |
|------|------|
| Co-lo内网络 | 10-50μs |
| 交易所Gateway | 10-50μs |
| 撮合引擎 | 10-100μs |
| 返回确认 | 10-50μs |
| **总计（Co-lo）** | **50-200μs** |
| **总计（非Co-lo）** | **1-10ms** |

### 6.2 Co-location优势

```
Co-location的好处：
1. 最短物理距离
2. 专用网络连接
3. 低延迟交换机
4. 与交易所相同的网络设备

成本：
- 机柜租金：$5,000-50,000/月
- 网络连接：$1,000-10,000/月
- 硬件成本：一次性

ROI计算：
如果每微秒价值$X，Co-lo节省1ms = 节省1000 × $X
```

---

## 总结

| 概念 | 重要性 | 策略影响 |
|------|--------|----------|
| 撮合算法 | 高 | 决定队列策略 |
| 订单类型 | 高 | 执行效率 |
| Queue Position | 很高 | 成交概率 |
| Maker/Taker | 高 | 费用优化 |

**最佳实践**：
1. 了解目标交易所的撮合规则
2. 追踪队列位置
3. 优化Maker/Taker比例
4. 使用适当的订单类型减少滑点
5. 考虑Co-location

---

## 相关文章

- [上一篇：Solarflare/Onload与FPGA网卡](/articles/hft/hft-17-Solarflare与FPGA网卡/)
- [下一篇：全球主要交易所技术对比](/articles/hft/hft-19-全球主要交易所技术对比/)
