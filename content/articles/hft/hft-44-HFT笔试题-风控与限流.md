+++
title = "44.HFT笔试题-风控与限流"
date = 2026-02-02
description = "HFT笔试：风控系统、限流算法、熔断器、订单检查"
[taxonomies]
tags = ["HFT", "笔试", "风控", "限流", "熔断"]
+++

# HFT 笔试题 - 风控与限流

本文汇总 HFT 笔试中关于风控系统和限流算法的编程题目。

---

## 题目 1：令牌桶限流

**题目**：实现高性能的令牌桶算法，支持微秒级精度。

**解答**：

```cpp
class TokenBucket {
public:
    TokenBucket(double rate_per_second, int burst_size)
        : rate_(rate_per_second),
          burst_(burst_size),
          tokens_(burst_size),
          last_update_(now_ns()) {}
    
    bool try_acquire(int tokens = 1) {
        refill();
        
        if (tokens_ >= tokens) {
            tokens_ -= tokens;
            return true;
        }
        return false;
    }
    
    // 非阻塞检查
    bool can_acquire(int tokens = 1) {
        refill();
        return tokens_ >= tokens;
    }
    
    // 获取需要等待的时间
    int64_t time_to_acquire_ns(int tokens = 1) {
        refill();
        
        if (tokens_ >= tokens) {
            return 0;
        }
        
        double needed = tokens - tokens_;
        return static_cast<int64_t>(needed / rate_ * 1e9);
    }
    
private:
    void refill() {
        uint64_t now = now_ns();
        uint64_t elapsed = now - last_update_;
        
        double new_tokens = elapsed * rate_ / 1e9;
        tokens_ = std::min(static_cast<double>(burst_), tokens_ + new_tokens);
        last_update_ = now;
    }
    
    uint64_t now_ns() {
        struct timespec ts;
        clock_gettime(CLOCK_MONOTONIC, &ts);
        return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
    }
    
    double rate_;       // 每秒补充速率
    int burst_;         // 桶大小
    double tokens_;     // 当前令牌数
    uint64_t last_update_;
};

// 无锁版本（单生产者单消费者）
class TokenBucketLockFree {
public:
    TokenBucketLockFree(double rate_per_second, int burst_size)
        : rate_(rate_per_second),
          burst_(burst_size),
          tokens_(burst_size * 1000),  // 使用整数，避免浮点
          last_update_(now_ns()) {}
    
    bool try_acquire(int tokens = 1) {
        uint64_t now = now_ns();
        
        // 原子更新
        int64_t current_tokens = tokens_.load(std::memory_order_relaxed);
        int64_t last = last_update_.load(std::memory_order_relaxed);
        
        // 计算新增令牌（毫令牌，1 token = 1000 milli-tokens）
        int64_t elapsed = now - last;
        int64_t new_tokens = elapsed * rate_ / 1000000;  // ns to milli-tokens
        
        int64_t updated = std::min(
            static_cast<int64_t>(burst_ * 1000),
            current_tokens + new_tokens
        );
        
        int needed = tokens * 1000;
        if (updated < needed) {
            return false;
        }
        
        // CAS 更新
        if (tokens_.compare_exchange_weak(current_tokens, updated - needed,
                                          std::memory_order_release)) {
            last_update_.store(now, std::memory_order_relaxed);
            return true;
        }
        
        return false;  // 竞争失败，下次重试
    }
    
private:
    double rate_;
    int burst_;
    std::atomic<int64_t> tokens_;
    std::atomic<uint64_t> last_update_;
};
```

---

## 题目 2：滑动窗口限流

**题目**：实现基于滑动窗口的订单频率限制。

**解答**：

```cpp
class SlidingWindowRateLimiter {
public:
    SlidingWindowRateLimiter(int max_requests, int64_t window_ns)
        : max_requests_(max_requests),
          window_ns_(window_ns) {}
    
    bool try_acquire() {
        uint64_t now = now_ns();
        
        // 移除过期的请求
        while (!timestamps_.empty() && 
               now - timestamps_.front() > window_ns_) {
            timestamps_.pop_front();
        }
        
        if (timestamps_.size() >= max_requests_) {
            return false;
        }
        
        timestamps_.push_back(now);
        return true;
    }
    
    int remaining() const {
        return max_requests_ - timestamps_.size();
    }
    
private:
    int max_requests_;
    int64_t window_ns_;
    std::deque<uint64_t> timestamps_;
};

// 高效版本：使用环形缓冲区
class SlidingWindowFast {
public:
    SlidingWindowFast(int max_requests, int64_t window_ns)
        : max_requests_(max_requests),
          window_ns_(window_ns),
          ring_(max_requests + 1),
          head_(0),
          tail_(0),
          count_(0) {}
    
    bool try_acquire() {
        uint64_t now = now_ns();
        
        // 移除过期
        while (count_ > 0 && now - ring_[head_] > window_ns_) {
            head_ = (head_ + 1) % ring_.size();
            count_--;
        }
        
        if (count_ >= max_requests_) {
            return false;
        }
        
        ring_[tail_] = now;
        tail_ = (tail_ + 1) % ring_.size();
        count_++;
        
        return true;
    }
    
private:
    int max_requests_;
    int64_t window_ns_;
    std::vector<uint64_t> ring_;
    size_t head_, tail_, count_;
};
```

---

## 题目 3：熔断器实现

**题目**：实现交易系统的熔断器（Circuit Breaker）。

**解答**：

```cpp
class CircuitBreaker {
public:
    enum class State { Closed, Open, HalfOpen };
    
    struct Config {
        int failure_threshold = 5;        // 触发熔断的失败次数
        int success_threshold = 3;        // 恢复需要的成功次数
        int64_t open_duration_ms = 30000; // 熔断持续时间
        int64_t half_open_max_calls = 3;  // 半开状态最大调用数
    };
    
    CircuitBreaker(const Config& config = {}) : config_(config) {}
    
    // 检查是否允许调用
    bool allow_request() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        switch (state_) {
            case State::Closed:
                return true;
                
            case State::Open:
                if (now_ms() - last_failure_time_ >= config_.open_duration_ms) {
                    transition_to(State::HalfOpen);
                    return true;
                }
                return false;
                
            case State::HalfOpen:
                return half_open_calls_ < config_.half_open_max_calls;
        }
        return false;
    }
    
    // 记录成功
    void record_success() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        switch (state_) {
            case State::Closed:
                failure_count_ = 0;
                break;
                
            case State::HalfOpen:
                success_count_++;
                if (success_count_ >= config_.success_threshold) {
                    transition_to(State::Closed);
                }
                break;
                
            default:
                break;
        }
    }
    
    // 记录失败
    void record_failure() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        last_failure_time_ = now_ms();
        
        switch (state_) {
            case State::Closed:
                failure_count_++;
                if (failure_count_ >= config_.failure_threshold) {
                    transition_to(State::Open);
                }
                break;
                
            case State::HalfOpen:
                transition_to(State::Open);
                break;
                
            default:
                break;
        }
    }
    
    State state() const { return state_; }
    
private:
    void transition_to(State new_state) {
        state_ = new_state;
        failure_count_ = 0;
        success_count_ = 0;
        half_open_calls_ = 0;
    }
    
    Config config_;
    State state_ = State::Closed;
    int failure_count_ = 0;
    int success_count_ = 0;
    int half_open_calls_ = 0;
    int64_t last_failure_time_ = 0;
    std::mutex mutex_;
};

// RAII 包装器
class CircuitBreakerGuard {
public:
    CircuitBreakerGuard(CircuitBreaker& cb) : cb_(cb), allowed_(cb.allow_request()) {}
    
    ~CircuitBreakerGuard() {
        if (allowed_) {
            if (success_) {
                cb_.record_success();
            } else {
                cb_.record_failure();
            }
        }
    }
    
    bool allowed() const { return allowed_; }
    void mark_success() { success_ = true; }
    void mark_failure() { success_ = false; }
    
private:
    CircuitBreaker& cb_;
    bool allowed_;
    bool success_ = false;
};
```

---

## 题目 4：订单预检系统

**题目**：实现交易订单的预检系统，包括多种风控规则。

**解答**：

```cpp
class OrderPreChecker {
public:
    enum class RejectReason {
        None,
        MaxOrderSize,
        MaxOrderValue,
        MaxPosition,
        MaxDailyVolume,
        MaxDailyLoss,
        PriceOutOfRange,
        SymbolNotAllowed,
        AccountSuspended,
        RateLimitExceeded
    };
    
    struct CheckResult {
        bool passed;
        RejectReason reason;
        std::string message;
    };
    
    struct RiskLimits {
        int max_order_quantity = 10000;
        double max_order_value = 1000000;
        int max_position = 100000;
        double max_daily_volume = 10000000;
        double max_daily_loss = 100000;
        double max_price_deviation = 0.1;  // 10% from reference
    };
    
    CheckResult check(const Order& order) {
        // 1. 订单大小检查
        if (order.quantity > limits_.max_order_quantity) {
            return {false, RejectReason::MaxOrderSize, 
                    "Order quantity exceeds limit"};
        }
        
        // 2. 订单价值检查
        double value = order.price * order.quantity;
        if (value > limits_.max_order_value) {
            return {false, RejectReason::MaxOrderValue,
                    "Order value exceeds limit"};
        }
        
        // 3. 持仓限制检查
        int projected_position = get_position(order.symbol) +
            (order.side == Side::Buy ? 1 : -1) * order.quantity;
        if (std::abs(projected_position) > limits_.max_position) {
            return {false, RejectReason::MaxPosition,
                    "Would exceed position limit"};
        }
        
        // 4. 日交易量检查
        double daily_volume = get_daily_volume(order.symbol);
        if (daily_volume + value > limits_.max_daily_volume) {
            return {false, RejectReason::MaxDailyVolume,
                    "Would exceed daily volume limit"};
        }
        
        // 5. 日亏损检查
        if (get_daily_pnl() < -limits_.max_daily_loss) {
            return {false, RejectReason::MaxDailyLoss,
                    "Daily loss limit reached"};
        }
        
        // 6. 价格偏离检查
        double ref_price = get_reference_price(order.symbol);
        double deviation = std::abs(order.price - ref_price) / ref_price;
        if (deviation > limits_.max_price_deviation) {
            return {false, RejectReason::PriceOutOfRange,
                    "Price deviates too much from reference"};
        }
        
        // 7. 频率限制
        if (!rate_limiter_.try_acquire()) {
            return {false, RejectReason::RateLimitExceeded,
                    "Order rate limit exceeded"};
        }
        
        return {true, RejectReason::None, ""};
    }
    
private:
    RiskLimits limits_;
    TokenBucket rate_limiter_{100, 10};  // 100/s, burst 10
    
    int get_position(const std::string& symbol);
    double get_daily_volume(const std::string& symbol);
    double get_daily_pnl();
    double get_reference_price(const std::string& symbol);
};
```

---

## 题目 5：Kill Switch

**题目**：实现交易系统的紧急终止开关。

**解答**：

```cpp
class KillSwitch {
public:
    enum class TriggerReason {
        Manual,
        MaxLoss,
        MaxPosition,
        SystemError,
        ExchangeError,
        NetworkIssue
    };
    
    struct TriggerEvent {
        TriggerReason reason;
        std::string details;
        uint64_t timestamp;
    };
    
    // 检查是否已触发
    bool is_triggered() const {
        return triggered_.load(std::memory_order_acquire);
    }
    
    // 触发 kill switch
    void trigger(TriggerReason reason, const std::string& details = "") {
        bool expected = false;
        if (triggered_.compare_exchange_strong(expected, true,
                                               std::memory_order_release)) {
            trigger_event_ = {reason, details, now_ns()};
            
            // 执行紧急操作
            execute_emergency_actions();
            
            // 通知监控系统
            notify_monitoring(trigger_event_);
        }
    }
    
    // 重置（需要人工确认）
    bool reset(const std::string& operator_id, const std::string& reason) {
        if (!triggered_.load()) return true;
        
        // 记录重置操作
        log_reset(operator_id, reason);
        
        // 重置状态
        triggered_.store(false, std::memory_order_release);
        trigger_event_ = {};
        
        return true;
    }
    
    // 获取触发信息
    const TriggerEvent& trigger_event() const {
        return trigger_event_;
    }
    
private:
    void execute_emergency_actions() {
        // 1. 取消所有挂单
        cancel_all_orders();
        
        // 2. 停止新订单
        block_new_orders();
        
        // 3. 断开交易所连接（可选）
        // disconnect_exchanges();
        
        // 4. 发送警报
        send_alert("KILL SWITCH TRIGGERED", trigger_event_.details);
    }
    
    void cancel_all_orders() {
        for (auto& [symbol, orders] : open_orders_) {
            for (const auto& order : orders) {
                send_cancel(order.order_id);
            }
        }
    }
    
    void block_new_orders() {
        order_gate_open_.store(false, std::memory_order_release);
    }
    
    std::atomic<bool> triggered_{false};
    std::atomic<bool> order_gate_open_{true};
    TriggerEvent trigger_event_;
    std::map<std::string, std::vector<Order>> open_orders_;
};

// 带自动监控的 Kill Switch
class AutoKillSwitch : public KillSwitch {
public:
    struct Thresholds {
        double max_daily_loss = 100000;
        double max_drawdown = 50000;
        int max_consecutive_losses = 10;
        int max_error_count = 5;
        int64_t error_window_ms = 60000;
    };
    
    void update_pnl(double current_pnl) {
        // 检查日亏损
        if (current_pnl < -thresholds_.max_daily_loss) {
            trigger(TriggerReason::MaxLoss, 
                   "Daily loss exceeded: " + std::to_string(current_pnl));
            return;
        }
        
        // 检查回撤
        if (current_pnl > peak_pnl_) {
            peak_pnl_ = current_pnl;
        }
        double drawdown = peak_pnl_ - current_pnl;
        if (drawdown > thresholds_.max_drawdown) {
            trigger(TriggerReason::MaxLoss,
                   "Drawdown exceeded: " + std::to_string(drawdown));
            return;
        }
    }
    
    void record_trade_result(bool profitable) {
        if (profitable) {
            consecutive_losses_ = 0;
        } else {
            consecutive_losses_++;
            if (consecutive_losses_ >= thresholds_.max_consecutive_losses) {
                trigger(TriggerReason::MaxLoss,
                       "Consecutive losses: " + std::to_string(consecutive_losses_));
            }
        }
    }
    
    void record_error() {
        uint64_t now = now_ms();
        error_timestamps_.push_back(now);
        
        // 清理过期错误
        while (!error_timestamps_.empty() &&
               now - error_timestamps_.front() > thresholds_.error_window_ms) {
            error_timestamps_.pop_front();
        }
        
        if (error_timestamps_.size() >= thresholds_.max_error_count) {
            trigger(TriggerReason::SystemError,
                   "Error rate too high: " + std::to_string(error_timestamps_.size()));
        }
    }
    
private:
    Thresholds thresholds_;
    double peak_pnl_ = 0;
    int consecutive_losses_ = 0;
    std::deque<uint64_t> error_timestamps_;
};
```

---

## 题目 6：持仓限制管理

**题目**：实现多维度的持仓限制管理。

**解答**：

```cpp
class PositionLimitManager {
public:
    struct Limits {
        int64_t max_shares;           // 最大股数
        double max_notional;          // 最大名义金额
        double max_loss;              // 最大亏损
        double var_limit;             // VaR 限制
    };
    
    struct PositionInfo {
        int64_t shares;
        double avg_price;
        double market_price;
        double notional;
        double unrealized_pnl;
        double realized_pnl;
    };
    
    bool check_order(const Order& order, Limits& limits) {
        std::string key = order.symbol;
        auto& pos = positions_[key];
        
        int64_t delta = (order.side == Side::Buy ? 1 : -1) * order.quantity;
        int64_t new_shares = pos.shares + delta;
        double new_notional = std::abs(new_shares * order.price);
        
        // 检查股数限制
        if (std::abs(new_shares) > limits.max_shares) {
            return false;
        }
        
        // 检查名义金额限制
        if (new_notional > limits.max_notional) {
            return false;
        }
        
        // 检查亏损限制
        double potential_loss = calculate_worst_case_loss(pos, order);
        if (potential_loss > limits.max_loss) {
            return false;
        }
        
        return true;
    }
    
    void update_position(const Execution& exec) {
        auto& pos = positions_[exec.symbol];
        
        int64_t delta = (exec.side == Side::Buy ? 1 : -1) * exec.quantity;
        
        if (pos.shares == 0) {
            pos.shares = delta;
            pos.avg_price = exec.price;
        } else if ((pos.shares > 0) == (delta > 0)) {
            // 同向：更新平均价
            double total_cost = pos.shares * pos.avg_price + delta * exec.price;
            pos.shares += delta;
            pos.avg_price = total_cost / pos.shares;
        } else {
            // 反向：实现盈亏
            int64_t close_qty = std::min(std::abs(pos.shares), std::abs(delta));
            double pnl = close_qty * (exec.price - pos.avg_price) * 
                        (pos.shares > 0 ? 1 : -1);
            pos.realized_pnl += pnl;
            
            pos.shares += delta;
            if (pos.shares == 0) {
                pos.avg_price = 0;
            }
        }
        
        update_notional(exec.symbol, exec.price);
    }
    
    void update_market_price(const std::string& symbol, double price) {
        auto& pos = positions_[symbol];
        pos.market_price = price;
        pos.notional = std::abs(pos.shares * price);
        pos.unrealized_pnl = pos.shares * (price - pos.avg_price);
    }
    
    double total_pnl() const {
        double total = 0;
        for (const auto& [symbol, pos] : positions_) {
            total += pos.realized_pnl + pos.unrealized_pnl;
        }
        return total;
    }
    
private:
    double calculate_worst_case_loss(const PositionInfo& pos, const Order& order);
    void update_notional(const std::string& symbol, double price);
    
    std::unordered_map<std::string, PositionInfo> positions_;
};
```

---

## 相关文章

- [HFT风控系统设计](/articles/hft/hft-15-HFT风控系统设计/)
- [交易系统容错与恢复](/articles/hft/hft-21-交易系统容错与恢复/)
- [HFT合规与监管要求](/articles/hft/hft-40-HFT合规与监管要求/)
