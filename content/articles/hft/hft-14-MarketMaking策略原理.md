+++
title = "14.Market Making策略原理"
slug = "hft-14-MarketMaking策略原理"
date = 2026-01-21
description = "深入剖析做市商策略，包括做市商模型、库存管理、价差设置、风险控制和对冲策略"
[taxonomies]
tags = ["HFT", "做市商", "MarketMaking", "策略", "风控"]
+++

## 概述

做市商（Market Maker）通过同时挂买卖单提供流动性，赚取买卖价差。本文深入讲解做市策略的核心原理。

---

## 一、做市商基础

### 1.1 做市商角色

```
做市商的核心功能：
1. 提供流动性 - 随时准备买入或卖出
2. 缩小价差 - 降低市场交易成本
3. 价格发现 - 通过报价反映信息

收益来源：
- Bid-Ask Spread（买卖价差）
- Rebates（交易所返佣）

风险来源：
- 逆向选择（Adverse Selection）
- 库存风险（Inventory Risk）
- 市场风险（Market Risk）
```

### 1.2 基本做市模型

```cpp
struct Quote {
    double bid_price;
    double ask_price;
    int bid_size;
    int ask_size;
};

class BasicMarketMaker {
public:
    Quote generate_quote(double mid_price) {
        // 基础报价：中间价 ± 半个价差
        double half_spread = base_spread_ / 2.0;
        
        return Quote{
            .bid_price = mid_price - half_spread,
            .ask_price = mid_price + half_spread,
            .bid_size = default_size_,
            .ask_size = default_size_
        };
    }
    
private:
    double base_spread_ = 0.02;  // 2分价差
    int default_size_ = 100;
};
```

---

## 二、价差设置

### 2.1 最优价差理论

```cpp
// Avellaneda-Stoikov模型
// 最优价差考虑：库存风险、波动率、时间

class AvellanedaStoikovMM {
public:
    Quote generate_quote(double mid_price, double time_remaining) {
        // 保留价格（Reservation Price）
        // r = s - q * γ * σ² * T
        double reservation_price = mid_price - 
            inventory_ * gamma_ * volatility_ * volatility_ * time_remaining;
        
        // 最优价差
        // δ = γ * σ² * T + 2/γ * ln(1 + γ/k)
        double optimal_spread = gamma_ * volatility_ * volatility_ * time_remaining +
            2.0 / gamma_ * std::log(1.0 + gamma_ / kappa_);
        
        double half_spread = optimal_spread / 2.0;
        
        return Quote{
            .bid_price = reservation_price - half_spread,
            .ask_price = reservation_price + half_spread,
            .bid_size = calculate_size(Side::BUY),
            .ask_size = calculate_size(Side::SELL)
        };
    }
    
private:
    double inventory_ = 0;      // 当前持仓
    double gamma_ = 0.1;        // 风险厌恶系数
    double volatility_ = 0.01;  // 波动率
    double kappa_ = 1.5;        // 订单到达强度参数
    
    int calculate_size(Side side) {
        // 库存偏斜：持仓多则减少买单，增加卖单
        int base_size = 100;
        double skew = -inventory_ * size_skew_factor_;
        
        if (side == Side::BUY) {
            return std::max(1, static_cast<int>(base_size + skew));
        } else {
            return std::max(1, static_cast<int>(base_size - skew));
        }
    }
    
    double size_skew_factor_ = 0.1;
};
```

### 2.2 动态价差调整

```cpp
class DynamicSpreadMM {
public:
    double calculate_spread() {
        double spread = base_spread_;
        
        // 1. 波动率调整
        spread *= (1.0 + volatility_factor_ * current_volatility_);
        
        // 2. 库存调整
        spread *= (1.0 + inventory_factor_ * std::abs(inventory_));
        
        // 3. 订单流不平衡调整
        spread *= (1.0 + imbalance_factor_ * order_flow_imbalance_);
        
        // 4. 时段调整（开盘收盘价差放大）
        spread *= time_of_day_multiplier();
        
        return std::max(min_spread_, std::min(max_spread_, spread));
    }
    
private:
    double base_spread_ = 0.01;
    double min_spread_ = 0.005;
    double max_spread_ = 0.05;
    
    double volatility_factor_ = 2.0;
    double inventory_factor_ = 0.1;
    double imbalance_factor_ = 0.5;
    
    double current_volatility_ = 0;
    double inventory_ = 0;
    double order_flow_imbalance_ = 0;
    
    double time_of_day_multiplier() {
        auto now = get_current_time();
        // 开盘和收盘时段价差放大
        if (is_near_open(now) || is_near_close(now)) {
            return 1.5;
        }
        return 1.0;
    }
};
```

---

## 三、库存管理

### 3.1 库存风险

```cpp
// 库存风险：持有仓位暴露于市场波动

class InventoryManager {
public:
    void update_inventory(int filled_qty, Side side) {
        if (side == Side::BUY) {
            inventory_ += filled_qty;
        } else {
            inventory_ -= filled_qty;
        }
        
        update_pnl();
        check_limits();
    }
    
    // 库存倾斜报价
    Quote skew_quote(Quote base_quote) {
        double skew = inventory_ * skew_per_unit_;
        
        // 持仓多时，降低买价，提高卖价（鼓励卖出）
        return Quote{
            .bid_price = base_quote.bid_price - skew,
            .ask_price = base_quote.ask_price - skew,
            .bid_size = base_quote.bid_size,
            .ask_size = base_quote.ask_size
        };
    }
    
    bool should_pause_quoting() const {
        return std::abs(inventory_) >= max_inventory_;
    }
    
private:
    int inventory_ = 0;
    int max_inventory_ = 1000;
    double skew_per_unit_ = 0.0001;
    double realized_pnl_ = 0;
    double unrealized_pnl_ = 0;
    
    void update_pnl() {
        // 使用当前中间价计算未实现盈亏
        unrealized_pnl_ = inventory_ * (current_mid_ - avg_entry_price_);
    }
    
    void check_limits() {
        if (std::abs(inventory_) >= max_inventory_) {
            log_warning("Inventory limit reached: {}", inventory_);
        }
    }
    
    double current_mid_ = 0;
    double avg_entry_price_ = 0;
};
```

### 3.2 库存清算策略

```cpp
class InventoryClearingStrategy {
public:
    Quote adjust_for_clearing(Quote base_quote, int inventory, 
                              double urgency) {
        if (std::abs(inventory) < clearing_threshold_) {
            return base_quote;
        }
        
        // 紧急程度：0-1，越高越激进
        double clearing_spread_reduction = urgency * max_spread_reduction_;
        
        if (inventory > 0) {
            // 需要卖出，降低卖价
            return Quote{
                .bid_price = base_quote.bid_price,
                .ask_price = base_quote.ask_price - clearing_spread_reduction,
                .bid_size = 0,  // 停止买入
                .ask_size = std::min(inventory, max_clear_size_)
            };
        } else {
            // 需要买入，提高买价
            return Quote{
                .bid_price = base_quote.bid_price + clearing_spread_reduction,
                .ask_price = base_quote.ask_price,
                .bid_size = std::min(-inventory, max_clear_size_),
                .ask_size = 0
            };
        }
    }
    
    double calculate_urgency(int inventory, double time_to_close) {
        // 收盘前紧急程度增加
        double inventory_urgency = std::abs(inventory) / 
                                   static_cast<double>(max_inventory_);
        double time_urgency = 1.0 - time_to_close / total_trading_time_;
        
        return std::max(inventory_urgency, time_urgency);
    }
    
private:
    int clearing_threshold_ = 500;
    int max_inventory_ = 1000;
    double max_spread_reduction_ = 0.02;
    int max_clear_size_ = 200;
    double total_trading_time_ = 6.5 * 3600;  // 6.5小时
};
```

---

## 四、逆向选择

### 4.1 信息不对称风险

```cpp
// 逆向选择：知情交易者利用做市商的报价

class AdverseSelectionDetector {
public:
    double estimate_adverse_selection() {
        // 使用成交方向和价格变动的相关性估计
        // 如果买入成交后价格上涨概率高，说明逆向选择严重
        
        double informed_prob = 0;
        
        for (const auto& trade : recent_trades_) {
            double subsequent_return = get_subsequent_return(trade);
            
            if (trade.side == Side::BUY && subsequent_return > 0) {
                informed_prob += 1.0;
            } else if (trade.side == Side::SELL && subsequent_return < 0) {
                informed_prob += 1.0;
            }
        }
        
        return informed_prob / recent_trades_.size();
    }
    
    void adjust_spread_for_adverse_selection(Quote& quote) {
        double as_prob = estimate_adverse_selection();
        
        // 逆向选择概率高时，扩大价差
        double as_adjustment = as_prob * adverse_selection_factor_;
        double half_adjustment = as_adjustment / 2.0;
        
        quote.bid_price -= half_adjustment;
        quote.ask_price += half_adjustment;
    }
    
private:
    std::deque<Trade> recent_trades_;
    double adverse_selection_factor_ = 0.01;
    
    double get_subsequent_return(const Trade& trade) {
        // 成交后一段时间的价格变动
        return (price_after_trade_ - trade.price) / trade.price;
    }
};
```

### 4.2 订单流毒性检测

```cpp
class OrderFlowToxicity {
public:
    // VPIN (Volume-synchronized Probability of Informed Trading)
    double calculate_vpin() {
        double total_volume = 0;
        double buy_volume = 0;
        
        for (const auto& bucket : volume_buckets_) {
            total_volume += bucket.total;
            buy_volume += bucket.buy;
        }
        
        double sell_volume = total_volume - buy_volume;
        double imbalance = std::abs(buy_volume - sell_volume);
        
        return imbalance / total_volume;
    }
    
    void on_trade(const Trade& trade) {
        // 使用Bulk Volume Classification分类买卖
        double buy_prob = classify_trade(trade);
        
        current_bucket_.total += trade.quantity;
        current_bucket_.buy += trade.quantity * buy_prob;
        
        if (current_bucket_.total >= bucket_size_) {
            volume_buckets_.push_back(current_bucket_);
            if (volume_buckets_.size() > num_buckets_) {
                volume_buckets_.pop_front();
            }
            current_bucket_ = VolumeBucket{};
        }
    }
    
private:
    struct VolumeBucket {
        double total = 0;
        double buy = 0;
    };
    
    std::deque<VolumeBucket> volume_buckets_;
    VolumeBucket current_bucket_;
    double bucket_size_ = 10000;
    size_t num_buckets_ = 50;
    
    double classify_trade(const Trade& trade) {
        // 基于成交价与中间价的位置判断
        double mid = (best_bid_ + best_ask_) / 2.0;
        double range = best_ask_ - best_bid_;
        
        if (range <= 0) return 0.5;
        
        return std::max(0.0, std::min(1.0, 
            (trade.price - best_bid_) / range));
    }
    
    double best_bid_ = 0;
    double best_ask_ = 0;
};
```

---

## 五、风险控制

### 5.1 风控限额

```cpp
class MarketMakerRiskLimits {
public:
    bool check_order(const Order& order) {
        // 检查各种限额
        if (!check_position_limit(order)) return false;
        if (!check_order_size_limit(order)) return false;
        if (!check_notional_limit(order)) return false;
        if (!check_loss_limit()) return false;
        if (!check_message_rate()) return false;
        
        return true;
    }
    
private:
    bool check_position_limit(const Order& order) {
        int projected_position = current_position_;
        if (order.side == Side::BUY) {
            projected_position += order.quantity;
        } else {
            projected_position -= order.quantity;
        }
        return std::abs(projected_position) <= max_position_;
    }
    
    bool check_order_size_limit(const Order& order) {
        return order.quantity <= max_order_size_;
    }
    
    bool check_notional_limit(const Order& order) {
        double notional = order.price * order.quantity;
        double projected_notional = total_notional_ + notional;
        return projected_notional <= max_notional_;
    }
    
    bool check_loss_limit() {
        return daily_pnl_ >= -max_daily_loss_;
    }
    
    bool check_message_rate() {
        auto now = std::chrono::steady_clock::now();
        // 清理旧的时间戳
        while (!message_times_.empty() && 
               now - message_times_.front() > std::chrono::seconds(1)) {
            message_times_.pop_front();
        }
        return message_times_.size() < max_messages_per_second_;
    }
    
    int current_position_ = 0;
    int max_position_ = 1000;
    int max_order_size_ = 100;
    double total_notional_ = 0;
    double max_notional_ = 1000000;
    double daily_pnl_ = 0;
    double max_daily_loss_ = 10000;
    std::deque<std::chrono::steady_clock::time_point> message_times_;
    size_t max_messages_per_second_ = 100;
};
```

### 5.2 紧急停止

```cpp
class KillSwitch {
public:
    void check_and_trigger() {
        // 检查各种紧急条件
        if (should_kill()) {
            trigger_kill_switch();
        }
    }
    
private:
    bool should_kill() {
        // 1. 损失超限
        if (daily_pnl_ < -kill_loss_threshold_) {
            kill_reason_ = "Loss limit exceeded";
            return true;
        }
        
        // 2. 仓位异常
        if (std::abs(position_) > kill_position_threshold_) {
            kill_reason_ = "Position limit exceeded";
            return true;
        }
        
        // 3. 市场数据异常
        if (is_market_data_stale()) {
            kill_reason_ = "Stale market data";
            return true;
        }
        
        // 4. 系统延迟异常
        if (latency_p99_ > max_latency_threshold_) {
            kill_reason_ = "High latency detected";
            return true;
        }
        
        return false;
    }
    
    void trigger_kill_switch() {
        // 1. 停止所有新订单
        stop_new_orders_ = true;
        
        // 2. 取消所有挂单
        cancel_all_orders();
        
        // 3. 发送告警
        send_alert("Kill switch triggered: " + kill_reason_);
        
        // 4. 记录日志
        log_critical("KILL SWITCH: {}", kill_reason_);
    }
    
    double daily_pnl_ = 0;
    double kill_loss_threshold_ = -50000;
    int position_ = 0;
    int kill_position_threshold_ = 5000;
    uint64_t latency_p99_ = 0;
    uint64_t max_latency_threshold_ = 1000000;  // 1ms
    bool stop_new_orders_ = false;
    std::string kill_reason_;
};
```

---

## 六、对冲策略

### 6.1 Delta对冲

```cpp
class DeltaHedger {
public:
    void hedge_if_needed() {
        double current_delta = calculate_portfolio_delta();
        
        if (std::abs(current_delta) > delta_threshold_) {
            // 计算对冲数量
            int hedge_qty = -static_cast<int>(current_delta / hedge_ratio_);
            
            // 发送对冲订单
            send_hedge_order(hedge_instrument_, hedge_qty);
        }
    }
    
private:
    double calculate_portfolio_delta() {
        // 对于股票做市商，delta就是仓位
        // 对于期权做市商，需要考虑期权的delta
        return position_ * delta_per_unit_;
    }
    
    double delta_threshold_ = 100;
    double hedge_ratio_ = 1.0;
    double delta_per_unit_ = 1.0;
    int position_ = 0;
    std::string hedge_instrument_;
};
```

---

## 总结

| 策略组件 | 作用 | 关键参数 |
|----------|------|----------|
| 价差设置 | 确定买卖价格 | 基础价差、波动率因子 |
| 库存管理 | 控制仓位风险 | 最大仓位、倾斜系数 |
| 逆向选择 | 识别知情交易 | VPIN阈值 |
| 风险控制 | 限制损失 | 止损线、仓位限额 |

**最佳实践**：
1. 根据市场状态动态调整价差
2. 严格控制库存，避免单边敞口
3. 监控订单流毒性，及时调整策略
4. 设置多层风控，包括kill switch
5. 收盘前清理库存

---

## 相关文章

- [上一篇：Order Book实现详解](/articles/hft/hft-13-OrderBook实现详解/)
- [下一篇：HFT风控系统设计](/articles/hft/hft-15-HFT风控系统设计/)
