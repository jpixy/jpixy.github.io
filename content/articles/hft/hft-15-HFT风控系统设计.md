+++
title = "15.HFT风控系统设计"
slug = "hft-15-HFT风控系统设计"
date = 2026-01-21
description = "深入剖析HFT风控系统设计，包括实时风控、限额管理、熔断机制、异常检测和合规要求"
[taxonomies]
tags = ["HFT", "风控", "交易系统", "合规", "风险管理"]
+++

## 概述

风控是HFT系统的生命线。本文深入讲解HFT风控系统的设计原则和实现方法。

---

## 一、风控架构

### 1.1 多层风控体系

| 层级 | 名称 | 说明 |
|------|------|------|
| L1 | 交易所层 | 交易所强制的限额和熔断 |
| L2 | 网关层 | 订单发送前的最后检查（硬限制） |
| L3 | 策略层 | 策略内部的软限制 |
| L4 | 监控层 | 实时监控和告警 |

### 1.2 风控检查流程

```cpp
class RiskGateway {
public:
    enum class CheckResult {
        PASS,
        REJECT,
        THROTTLE,
        KILL
    };
    
    CheckResult check_order(const Order& order) {
        // 按优先级检查
        
        // 1. 硬限制检查（必须通过）
        if (!check_hard_limits(order)) {
            return CheckResult::REJECT;
        }
        
        // 2. Kill Switch检查
        if (kill_switch_active_) {
            return CheckResult::KILL;
        }
        
        // 3. 节流检查
        if (!check_throttle(order)) {
            return CheckResult::THROTTLE;
        }
        
        // 4. 软限制检查（可能警告）
        check_soft_limits(order);
        
        return CheckResult::PASS;
    }
    
private:
    bool check_hard_limits(const Order& order);
    bool check_throttle(const Order& order);
    void check_soft_limits(const Order& order);
    
    std::atomic<bool> kill_switch_active_{false};
};
```

---

## 二、实时限额管理

### 2.1 仓位限额

```cpp
class PositionLimits {
public:
    struct Limits {
        int64_t max_long;           // 最大多头仓位
        int64_t max_short;          // 最大空头仓位
        int64_t max_gross;          // 最大总仓位
        double max_notional;        // 最大名义价值
    };
    
    bool check_position(const Order& order) {
        int64_t projected_position = calculate_projected_position(order);
        double projected_notional = calculate_projected_notional(order);
        
        // 检查多头限额
        if (projected_position > 0 && 
            projected_position > limits_.max_long) {
            reject_reason_ = "Long position limit exceeded";
            return false;
        }
        
        // 检查空头限额
        if (projected_position < 0 && 
            -projected_position > limits_.max_short) {
            reject_reason_ = "Short position limit exceeded";
            return false;
        }
        
        // 检查总仓位限额
        int64_t gross = calculate_gross_position() + 
                        std::abs(order.quantity);
        if (gross > limits_.max_gross) {
            reject_reason_ = "Gross position limit exceeded";
            return false;
        }
        
        // 检查名义价值限额
        if (projected_notional > limits_.max_notional) {
            reject_reason_ = "Notional limit exceeded";
            return false;
        }
        
        return true;
    }
    
private:
    Limits limits_;
    std::unordered_map<std::string, int64_t> positions_;
    std::string reject_reason_;
    
    int64_t calculate_projected_position(const Order& order) {
        int64_t current = positions_[order.symbol];
        if (order.side == Side::BUY) {
            return current + order.quantity;
        } else {
            return current - order.quantity;
        }
    }
};
```

### 2.2 订单限额

```cpp
class OrderLimits {
public:
    bool check_order(const Order& order) {
        // 单笔订单大小限制
        if (order.quantity > max_order_size_) {
            reject("Order size exceeds limit");
            return false;
        }
        
        // 单笔订单金额限制
        double notional = order.price * order.quantity;
        if (notional > max_order_notional_) {
            reject("Order notional exceeds limit");
            return false;
        }
        
        // 价格合理性检查
        if (!check_price_reasonability(order)) {
            return false;
        }
        
        // FAT FINGER检查
        if (!check_fat_finger(order)) {
            return false;
        }
        
        return true;
    }
    
private:
    bool check_price_reasonability(const Order& order) {
        double mid_price = get_mid_price(order.symbol);
        if (mid_price <= 0) return true;  // 无参考价格时跳过
        
        double deviation = std::abs(order.price - mid_price) / mid_price;
        
        if (deviation > max_price_deviation_) {
            reject("Price deviation too large: " + 
                   std::to_string(deviation * 100) + "%");
            return false;
        }
        
        return true;
    }
    
    bool check_fat_finger(const Order& order) {
        // 检查订单是否会导致自成交
        if (would_self_trade(order)) {
            reject("Self-trade prevention");
            return false;
        }
        
        // 检查订单是否会穿透多个价格级别
        int levels_crossed = calculate_levels_crossed(order);
        if (levels_crossed > max_levels_crossed_) {
            reject("Order would cross too many price levels");
            return false;
        }
        
        return true;
    }
    
    int64_t max_order_size_ = 1000;
    double max_order_notional_ = 100000;
    double max_price_deviation_ = 0.05;  // 5%
    int max_levels_crossed_ = 5;
};
```

### 2.3 消息频率限制

```cpp
class MessageRateLimiter {
public:
    bool check_rate(const std::string& symbol) {
        auto now = std::chrono::steady_clock::now();
        
        // 全局消息频率
        if (!check_global_rate(now)) {
            return false;
        }
        
        // 每品种消息频率
        if (!check_symbol_rate(symbol, now)) {
            return false;
        }
        
        return true;
    }
    
private:
    bool check_global_rate(TimePoint now) {
        // 滑动窗口计数
        while (!global_timestamps_.empty() && 
               now - global_timestamps_.front() > window_) {
            global_timestamps_.pop_front();
        }
        
        if (global_timestamps_.size() >= max_global_rate_) {
            throttle_count_++;
            return false;
        }
        
        global_timestamps_.push_back(now);
        return true;
    }
    
    bool check_symbol_rate(const std::string& symbol, TimePoint now) {
        auto& timestamps = symbol_timestamps_[symbol];
        
        while (!timestamps.empty() && 
               now - timestamps.front() > window_) {
            timestamps.pop_front();
        }
        
        if (timestamps.size() >= max_symbol_rate_) {
            return false;
        }
        
        timestamps.push_back(now);
        return true;
    }
    
    using TimePoint = std::chrono::steady_clock::time_point;
    std::chrono::milliseconds window_{1000};  // 1秒窗口
    size_t max_global_rate_ = 1000;           // 全局每秒1000条
    size_t max_symbol_rate_ = 100;            // 每品种每秒100条
    
    std::deque<TimePoint> global_timestamps_;
    std::unordered_map<std::string, std::deque<TimePoint>> symbol_timestamps_;
    std::atomic<uint64_t> throttle_count_{0};
};
```

---

## 三、熔断机制

### 3.1 多级熔断

```cpp
class CircuitBreaker {
public:
    enum class Level {
        NORMAL,    // 正常
        WARNING,   // 警告
        THROTTLE,  // 限速
        HALT       // 停止
    };
    
    Level check_and_update() {
        Level new_level = calculate_level();
        
        if (new_level != current_level_) {
            on_level_change(current_level_, new_level);
            current_level_ = new_level;
        }
        
        return current_level_;
    }
    
private:
    Level calculate_level() {
        // 基于多个指标计算熔断级别
        
        // 1. 损失检查
        if (daily_pnl_ < -halt_loss_) {
            return Level::HALT;
        }
        if (daily_pnl_ < -throttle_loss_) {
            return Level::THROTTLE;
        }
        if (daily_pnl_ < -warning_loss_) {
            return Level::WARNING;
        }
        
        // 2. 仓位检查
        if (std::abs(net_position_) > halt_position_) {
            return Level::HALT;
        }
        
        // 3. 错误率检查
        if (error_rate_ > halt_error_rate_) {
            return Level::HALT;
        }
        
        return Level::NORMAL;
    }
    
    void on_level_change(Level from, Level to) {
        log_warning("Circuit breaker level changed: {} -> {}", 
                    level_to_string(from), level_to_string(to));
        
        if (to == Level::HALT) {
            trigger_halt();
        } else if (to == Level::THROTTLE) {
            enable_throttle();
        }
        
        send_alert(to);
    }
    
    void trigger_halt() {
        // 取消所有挂单
        cancel_all_pending_orders();
        // 停止新订单
        halt_new_orders_ = true;
    }
    
    Level current_level_ = Level::NORMAL;
    double daily_pnl_ = 0;
    double warning_loss_ = -10000;
    double throttle_loss_ = -30000;
    double halt_loss_ = -50000;
    int64_t net_position_ = 0;
    int64_t halt_position_ = 10000;
    double error_rate_ = 0;
    double halt_error_rate_ = 0.1;
    bool halt_new_orders_ = false;
};
```

### 3.2 Kill Switch

```cpp
class KillSwitch {
public:
    void arm() {
        armed_ = true;
        log_info("Kill switch armed");
    }
    
    void trigger(const std::string& reason) {
        if (!armed_) return;
        
        triggered_ = true;
        trigger_time_ = std::chrono::system_clock::now();
        trigger_reason_ = reason;
        
        // 执行紧急停止
        execute_kill();
        
        // 发送告警
        send_critical_alert("KILL SWITCH TRIGGERED: " + reason);
    }
    
    bool is_triggered() const { return triggered_; }
    
    void reset(const std::string& auth_code) {
        if (!verify_auth_code(auth_code)) {
            log_error("Invalid auth code for kill switch reset");
            return;
        }
        
        triggered_ = false;
        log_info("Kill switch reset by authorized user");
    }
    
private:
    void execute_kill() {
        // 1. 停止所有策略
        for (auto& strategy : strategies_) {
            strategy->stop();
        }
        
        // 2. 取消所有挂单
        for (const auto& order_id : pending_orders_) {
            send_cancel(order_id);
        }
        
        // 3. 断开行情连接（可选）
        // disconnect_market_data();
        
        // 4. 记录状态快照
        save_state_snapshot();
        
        log_critical("Kill switch executed - all trading stopped");
    }
    
    std::atomic<bool> armed_{false};
    std::atomic<bool> triggered_{false};
    std::chrono::system_clock::time_point trigger_time_;
    std::string trigger_reason_;
    std::vector<Strategy*> strategies_;
    std::set<uint64_t> pending_orders_;
};
```

---

## 四、异常检测

### 4.1 价格异常检测

```cpp
class PriceAnomalyDetector {
public:
    struct AnomalyResult {
        bool is_anomaly;
        std::string type;
        double severity;
    };
    
    AnomalyResult check(const MarketData& md) {
        AnomalyResult result{false, "", 0};
        
        // 1. 价格跳变检测
        if (auto jump = detect_price_jump(md); jump.has_value()) {
            if (jump->severity > jump_threshold_) {
                result = {true, "price_jump", jump->severity};
                return result;
            }
        }
        
        // 2. 价差异常检测
        double spread = md.ask - md.bid;
        double spread_ratio = spread / md.mid();
        if (spread_ratio > spread_threshold_) {
            result = {true, "wide_spread", spread_ratio};
            return result;
        }
        
        // 3. 交叉价格检测
        if (md.bid >= md.ask) {
            result = {true, "crossed_market", 1.0};
            return result;
        }
        
        return result;
    }
    
private:
    std::optional<Jump> detect_price_jump(const MarketData& md) {
        if (last_prices_.find(md.symbol) == last_prices_.end()) {
            last_prices_[md.symbol] = md.mid();
            return std::nullopt;
        }
        
        double last = last_prices_[md.symbol];
        double current = md.mid();
        double change = std::abs(current - last) / last;
        
        last_prices_[md.symbol] = current;
        
        if (change > 0.001) {  // 0.1%以上变动
            return Jump{change};
        }
        
        return std::nullopt;
    }
    
    struct Jump { double severity; };
    
    std::unordered_map<std::string, double> last_prices_;
    double jump_threshold_ = 0.05;   // 5%跳变阈值
    double spread_threshold_ = 0.1;  // 10%价差阈值
};
```

### 4.2 系统异常检测

```cpp
class SystemHealthMonitor {
public:
    struct HealthStatus {
        bool healthy;
        std::vector<std::string> issues;
    };
    
    HealthStatus check_health() {
        HealthStatus status{true, {}};
        
        // 1. 延迟检查
        if (latency_p99_ > max_latency_ns_) {
            status.healthy = false;
            status.issues.push_back("High latency: " + 
                std::to_string(latency_p99_ / 1000) + "us");
        }
        
        // 2. 市场数据延迟
        if (market_data_staleness_ > max_staleness_ms_) {
            status.healthy = false;
            status.issues.push_back("Stale market data");
        }
        
        // 3. 订单确认延迟
        if (avg_ack_time_ > max_ack_time_ms_) {
            status.healthy = false;
            status.issues.push_back("Slow order acknowledgment");
        }
        
        // 4. 错误率
        if (error_rate_ > max_error_rate_) {
            status.healthy = false;
            status.issues.push_back("High error rate: " + 
                std::to_string(error_rate_ * 100) + "%");
        }
        
        // 5. 队列积压
        if (queue_depth_ > max_queue_depth_) {
            status.healthy = false;
            status.issues.push_back("Queue backlog");
        }
        
        return status;
    }
    
    void update_metrics(const SystemMetrics& metrics) {
        latency_p99_ = metrics.latency_p99;
        market_data_staleness_ = metrics.md_staleness;
        avg_ack_time_ = metrics.avg_ack_time;
        error_rate_ = metrics.error_rate;
        queue_depth_ = metrics.queue_depth;
    }
    
private:
    uint64_t latency_p99_ = 0;
    uint64_t max_latency_ns_ = 100000;  // 100us
    
    uint64_t market_data_staleness_ = 0;
    uint64_t max_staleness_ms_ = 100;
    
    uint64_t avg_ack_time_ = 0;
    uint64_t max_ack_time_ms_ = 50;
    
    double error_rate_ = 0;
    double max_error_rate_ = 0.01;  // 1%
    
    size_t queue_depth_ = 0;
    size_t max_queue_depth_ = 1000;
};
```

---

## 五、合规要求

### 5.1 审计日志

```cpp
class AuditLogger {
public:
    void log_order(const Order& order, const std::string& action) {
        AuditRecord record;
        record.timestamp = get_precise_timestamp();
        record.action = action;
        record.order_id = order.order_id;
        record.symbol = order.symbol;
        record.side = order.side;
        record.price = order.price;
        record.quantity = order.quantity;
        record.user_id = current_user_id_;
        record.source_ip = source_ip_;
        
        write_record(record);
    }
    
    void log_risk_event(const std::string& event_type,
                        const std::string& details) {
        AuditRecord record;
        record.timestamp = get_precise_timestamp();
        record.action = "RISK_EVENT";
        record.event_type = event_type;
        record.details = details;
        
        write_record(record);
    }
    
private:
    struct AuditRecord {
        uint64_t timestamp;
        std::string action;
        uint64_t order_id;
        std::string symbol;
        Side side;
        double price;
        int64_t quantity;
        std::string user_id;
        std::string source_ip;
        std::string event_type;
        std::string details;
    };
    
    void write_record(const AuditRecord& record) {
        // 写入持久化存储（不可修改）
        audit_writer_.write(serialize(record));
        
        // 同步到合规系统
        if (compliance_enabled_) {
            send_to_compliance(record);
        }
    }
    
    std::string current_user_id_;
    std::string source_ip_;
    AuditWriter audit_writer_;
    bool compliance_enabled_ = true;
};
```

### 5.2 监管报告

```cpp
class RegulatoryReporting {
public:
    void generate_daily_report() {
        DailyReport report;
        
        // 交易统计
        report.total_orders = daily_stats_.total_orders;
        report.total_fills = daily_stats_.total_fills;
        report.total_volume = daily_stats_.total_volume;
        report.total_notional = daily_stats_.total_notional;
        
        // 风控事件
        report.risk_events = risk_events_;
        report.circuit_breaker_triggers = circuit_breaker_count_;
        
        // 延迟统计
        report.latency_p50 = latency_stats_.p50;
        report.latency_p99 = latency_stats_.p99;
        report.latency_max = latency_stats_.max;
        
        // 生成报告
        std::string report_path = generate_report_file(report);
        
        // 提交到监管系统
        submit_to_regulator(report_path);
    }
    
private:
    DailyStats daily_stats_;
    std::vector<RiskEvent> risk_events_;
    int circuit_breaker_count_ = 0;
    LatencyStats latency_stats_;
};
```

---

## 总结

| 风控层 | 检查内容 | 延迟要求 |
|--------|----------|----------|
| 网关层 | 硬限制、Kill Switch | <100ns |
| 策略层 | 软限制、警告 | <1μs |
| 监控层 | 异常检测、告警 | 实时 |
| 合规层 | 审计日志、报告 | 异步 |

**最佳实践**：
1. 网关层风控必须是同步的、低延迟的
2. 设置多级熔断，避免单点失效
3. Kill Switch必须有独立的触发路径
4. 所有订单和风控事件必须有审计日志
5. 定期进行风控系统压力测试

---

## 相关文章

- [上一篇：Market Making策略原理](/articles/hft/hft-14-MarketMaking策略原理/)
- [下一篇：DPDK深度实践](/articles/hft/hft-16-DPDK深度实践/)
