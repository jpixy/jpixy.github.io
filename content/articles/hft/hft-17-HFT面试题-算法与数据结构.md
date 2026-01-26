+++
title = "17.HFT面试题-算法与数据结构"
date = 2026-01-21
description = "HFT算法与数据结构面试题，包括时间序列、Order Book、滑动窗口和概率统计"
[taxonomies]
tags = ["HFT", "面试", "算法", "数据结构", "低延迟"]
+++

## 一、Order Book相关

### Q1: 实现一个Order Book

**问题**：实现一个支持添加、删除、修改订单的Order Book。

```cpp
class OrderBook {
public:
    void add_order(uint64_t order_id, Side side, int price, int quantity) {
        Order* order = pool_.allocate();
        order->order_id = order_id;
        order->price = price;
        order->remaining = quantity;
        order->side = side;
        
        orders_[order_id] = order;
        
        if (side == Side::BUY) {
            bids_[price].push_back(order);
            if (price > best_bid_) best_bid_ = price;
        } else {
            asks_[price].push_back(order);
            if (best_ask_ == 0 || price < best_ask_) best_ask_ = price;
        }
    }
    
    void cancel_order(uint64_t order_id) {
        auto it = orders_.find(order_id);
        if (it == orders_.end()) return;
        
        Order* order = it->second;
        auto& level = (order->side == Side::BUY) ? 
                      bids_[order->price] : asks_[order->price];
        
        // 从链表中移除
        level.remove(order);
        
        // 如果该价格级别为空，更新best price
        if (level.empty()) {
            update_best_price(order->side, order->price);
        }
        
        orders_.erase(it);
        pool_.release(order);
    }
    
    int best_bid() const { return best_bid_; }
    int best_ask() const { return best_ask_; }
    
private:
    void update_best_price(Side side, int removed_price) {
        if (side == Side::BUY && removed_price == best_bid_) {
            // 找下一个最优买价
            while (best_bid_ > 0 && bids_[best_bid_].empty()) {
                best_bid_--;
            }
        } else if (side == Side::SELL && removed_price == best_ask_) {
            // 找下一个最优卖价
            while (best_ask_ < MAX_PRICE && asks_[best_ask_].empty()) {
                best_ask_++;
            }
        }
    }
    
    std::unordered_map<uint64_t, Order*> orders_;
    std::array<std::list<Order*>, MAX_PRICE> bids_;
    std::array<std::list<Order*>, MAX_PRICE> asks_;
    int best_bid_ = 0;
    int best_ask_ = 0;
    ObjectPool<Order> pool_;
};
```

### Q2: Order Book撮合

**问题**：实现Price-Time优先级的撮合逻辑。

```cpp
struct Fill {
    uint64_t order_id;
    int price;
    int quantity;
};

std::vector<Fill> OrderBook::match(Order* incoming) {
    std::vector<Fill> fills;
    
    auto& contra_book = (incoming->side == Side::BUY) ? asks_ : bids_;
    int& best_contra = (incoming->side == Side::BUY) ? best_ask_ : best_bid_;
    
    while (incoming->remaining > 0 && can_match(incoming, best_contra)) {
        auto& level = contra_book[best_contra];
        
        while (!level.empty() && incoming->remaining > 0) {
            Order* resting = level.front();
            int fill_qty = std::min(incoming->remaining, resting->remaining);
            
            fills.push_back({resting->order_id, best_contra, fill_qty});
            
            incoming->remaining -= fill_qty;
            resting->remaining -= fill_qty;
            
            if (resting->remaining == 0) {
                level.pop_front();
                orders_.erase(resting->order_id);
                pool_.release(resting);
            }
        }
        
        if (level.empty()) {
            update_best_price(contra_side(incoming->side), best_contra);
        }
    }
    
    return fills;
}

bool OrderBook::can_match(Order* incoming, int best_contra) {
    if (incoming->side == Side::BUY) {
        return best_contra > 0 && incoming->price >= best_contra;
    } else {
        return best_contra > 0 && incoming->price <= best_contra;
    }
}
```

---

## 二、滑动窗口

### Q3: 滑动窗口最大值

**问题**：实现一个O(1)获取滑动窗口最大值的数据结构。

```cpp
class SlidingWindowMax {
public:
    SlidingWindowMax(int window_size) : window_size_(window_size) {}
    
    void push(int value) {
        // 移除过期元素
        while (!deque_.empty() && 
               deque_.front().index <= current_index_ - window_size_) {
            deque_.pop_front();
        }
        
        // 移除所有比当前值小的元素
        while (!deque_.empty() && deque_.back().value < value) {
            deque_.pop_back();
        }
        
        deque_.push_back({value, current_index_});
        current_index_++;
    }
    
    int max() const {
        return deque_.empty() ? 0 : deque_.front().value;
    }
    
private:
    struct Entry {
        int value;
        int index;
    };
    
    std::deque<Entry> deque_;
    int window_size_;
    int current_index_ = 0;
};
```

### Q4: 滑动窗口均值和标准差

**问题**：实现O(1)更新的滑动窗口统计。

```cpp
class SlidingWindowStats {
public:
    SlidingWindowStats(int window_size) : window_(window_size) {}
    
    void push(double value) {
        if (window_.full()) {
            double old_value = window_.front();
            // 更新统计量
            sum_ -= old_value;
            sum_sq_ -= old_value * old_value;
            count_--;
        }
        
        window_.push(value);
        sum_ += value;
        sum_sq_ += value * value;
        count_++;
    }
    
    double mean() const {
        return count_ > 0 ? sum_ / count_ : 0;
    }
    
    double variance() const {
        if (count_ < 2) return 0;
        double m = mean();
        return sum_sq_ / count_ - m * m;
    }
    
    double stddev() const {
        return std::sqrt(variance());
    }
    
private:
    RingBuffer<double> window_;
    double sum_ = 0;
    double sum_sq_ = 0;
    int count_ = 0;
};
```

### Q5: 滚动中位数

**问题**：实现O(log n)更新的滚动中位数。

```cpp
class SlidingMedian {
public:
    SlidingMedian(int window_size) : window_(window_size) {}
    
    void push(double value) {
        // 移除过期元素
        if (window_.full()) {
            double old_value = window_.front();
            remove(old_value);
        }
        
        window_.push(value);
        insert(value);
    }
    
    double median() const {
        int total = lower_half_.size() + upper_half_.size();
        if (total == 0) return 0;
        
        if (lower_half_.size() == upper_half_.size()) {
            return (lower_half_.top() + upper_half_.top()) / 2.0;
        } else {
            return lower_half_.top();
        }
    }
    
private:
    void insert(double value) {
        if (lower_half_.empty() || value <= lower_half_.top()) {
            lower_half_.push(value);
        } else {
            upper_half_.push(value);
        }
        
        rebalance();
    }
    
    void remove(double value) {
        if (value <= lower_half_.top()) {
            // 延迟删除
            to_remove_lower_[value]++;
        } else {
            to_remove_upper_[value]++;
        }
        
        prune();
        rebalance();
    }
    
    void rebalance() {
        // 保持lower_half比upper_half多0或1个元素
        while (lower_half_.size() > upper_half_.size() + 1) {
            upper_half_.push(lower_half_.top());
            lower_half_.pop();
        }
        while (upper_half_.size() > lower_half_.size()) {
            lower_half_.push(upper_half_.top());
            upper_half_.pop();
        }
    }
    
    void prune() {
        while (!lower_half_.empty() && 
               to_remove_lower_[lower_half_.top()] > 0) {
            to_remove_lower_[lower_half_.top()]--;
            lower_half_.pop();
        }
        while (!upper_half_.empty() && 
               to_remove_upper_[upper_half_.top()] > 0) {
            to_remove_upper_[upper_half_.top()]--;
            upper_half_.pop();
        }
    }
    
    RingBuffer<double> window_;
    std::priority_queue<double> lower_half_;  // max heap
    std::priority_queue<double, std::vector<double>, 
                        std::greater<double>> upper_half_;  // min heap
    std::unordered_map<double, int> to_remove_lower_;
    std::unordered_map<double, int> to_remove_upper_;
};
```

---

## 三、时间序列

### Q6: TWAP计算

**问题**：实现时间加权平均价格(TWAP)计算。

```cpp
class TWAP {
public:
    void on_price_update(double price, uint64_t timestamp_ns) {
        if (last_timestamp_ > 0) {
            uint64_t duration = timestamp_ns - last_timestamp_;
            weighted_sum_ += last_price_ * duration;
            total_time_ += duration;
        }
        
        last_price_ = price;
        last_timestamp_ = timestamp_ns;
    }
    
    double get_twap(uint64_t current_timestamp_ns) const {
        if (total_time_ == 0) return last_price_;
        
        // 包含当前时间到最后更新的时间
        uint64_t additional_time = current_timestamp_ns - last_timestamp_;
        double total_weighted = weighted_sum_ + last_price_ * additional_time;
        uint64_t total = total_time_ + additional_time;
        
        return total_weighted / total;
    }
    
private:
    double last_price_ = 0;
    uint64_t last_timestamp_ = 0;
    double weighted_sum_ = 0;
    uint64_t total_time_ = 0;
};
```

### Q7: VWAP计算

**问题**：实现成交量加权平均价格(VWAP)计算。

```cpp
class VWAP {
public:
    void on_trade(double price, int64_t volume) {
        price_volume_sum_ += price * volume;
        volume_sum_ += volume;
    }
    
    double get_vwap() const {
        return volume_sum_ > 0 ? price_volume_sum_ / volume_sum_ : 0;
    }
    
    // 滚动VWAP
    void on_trade_rolling(double price, int64_t volume, 
                          uint64_t timestamp) {
        trades_.push_back({price, volume, timestamp});
        price_volume_sum_ += price * volume;
        volume_sum_ += volume;
        
        // 移除窗口外的交易
        while (!trades_.empty() && 
               timestamp - trades_.front().timestamp > window_ns_) {
            auto& old = trades_.front();
            price_volume_sum_ -= old.price * old.volume;
            volume_sum_ -= old.volume;
            trades_.pop_front();
        }
    }
    
private:
    struct Trade {
        double price;
        int64_t volume;
        uint64_t timestamp;
    };
    
    std::deque<Trade> trades_;
    double price_volume_sum_ = 0;
    int64_t volume_sum_ = 0;
    uint64_t window_ns_ = 300'000'000'000ULL;  // 5分钟
};
```

---

## 四、概率与统计

### Q8: 在线算法计算均值和方差

**问题**：实现Welford算法计算在线均值和方差。

```cpp
class OnlineStats {
public:
    void update(double value) {
        count_++;
        double delta = value - mean_;
        mean_ += delta / count_;
        double delta2 = value - mean_;
        m2_ += delta * delta2;
    }
    
    double mean() const { return mean_; }
    
    double variance() const {
        return count_ > 1 ? m2_ / (count_ - 1) : 0;
    }
    
    double stddev() const {
        return std::sqrt(variance());
    }
    
private:
    int64_t count_ = 0;
    double mean_ = 0;
    double m2_ = 0;  // 与均值差的平方和
};
```

### Q9: 指数移动平均

**问题**：实现EMA及其变体。

```cpp
class EMA {
public:
    EMA(double alpha) : alpha_(alpha) {}
    
    // 从span计算alpha：alpha = 2/(span+1)
    static EMA from_span(int span) {
        return EMA(2.0 / (span + 1));
    }
    
    void update(double value) {
        if (!initialized_) {
            ema_ = value;
            initialized_ = true;
        } else {
            ema_ = alpha_ * value + (1 - alpha_) * ema_;
        }
    }
    
    double value() const { return ema_; }
    
private:
    double alpha_;
    double ema_ = 0;
    bool initialized_ = false;
};

// 双指数移动平均（DEMA）
class DEMA {
public:
    DEMA(double alpha) : ema1_(alpha), ema2_(alpha) {}
    
    void update(double value) {
        ema1_.update(value);
        ema2_.update(ema1_.value());
    }
    
    double value() const {
        return 2 * ema1_.value() - ema2_.value();
    }
    
private:
    EMA ema1_, ema2_;
};
```

### Q10: 相关系数在线计算

**问题**：实现在线计算两个序列的相关系数。

```cpp
class OnlineCorrelation {
public:
    void update(double x, double y) {
        count_++;
        
        double dx = x - mean_x_;
        double dy = y - mean_y_;
        
        mean_x_ += dx / count_;
        mean_y_ += dy / count_;
        
        double dx2 = x - mean_x_;
        double dy2 = y - mean_y_;
        
        var_x_ += dx * dx2;
        var_y_ += dy * dy2;
        cov_xy_ += dx * dy2;
    }
    
    double correlation() const {
        if (count_ < 2) return 0;
        
        double std_x = std::sqrt(var_x_ / (count_ - 1));
        double std_y = std::sqrt(var_y_ / (count_ - 1));
        
        if (std_x == 0 || std_y == 0) return 0;
        
        return (cov_xy_ / (count_ - 1)) / (std_x * std_y);
    }
    
private:
    int64_t count_ = 0;
    double mean_x_ = 0, mean_y_ = 0;
    double var_x_ = 0, var_y_ = 0;
    double cov_xy_ = 0;
};
```

---

## 五、其他常见题

### Q11: LRU Cache实现

```cpp
class LRUCache {
public:
    LRUCache(int capacity) : capacity_(capacity) {}
    
    int get(int key) {
        auto it = cache_.find(key);
        if (it == cache_.end()) return -1;
        
        // 移到最前面
        order_.splice(order_.begin(), order_, it->second);
        return it->second->second;
    }
    
    void put(int key, int value) {
        auto it = cache_.find(key);
        
        if (it != cache_.end()) {
            // 更新并移到最前面
            it->second->second = value;
            order_.splice(order_.begin(), order_, it->second);
            return;
        }
        
        // 检查容量
        if (cache_.size() >= capacity_) {
            cache_.erase(order_.back().first);
            order_.pop_back();
        }
        
        // 插入新元素
        order_.push_front({key, value});
        cache_[key] = order_.begin();
    }
    
private:
    int capacity_;
    std::list<std::pair<int, int>> order_;
    std::unordered_map<int, std::list<std::pair<int, int>>::iterator> cache_;
};
```

### Q12: 限流器实现

```cpp
class RateLimiter {
public:
    RateLimiter(int rate, int per_seconds) 
        : rate_(rate), 
          window_ns_(per_seconds * 1'000'000'000ULL),
          tokens_(rate) {}
    
    bool try_acquire() {
        refill();
        
        if (tokens_ > 0) {
            tokens_--;
            return true;
        }
        return false;
    }
    
private:
    void refill() {
        auto now = std::chrono::steady_clock::now();
        auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            now.time_since_epoch()).count();
        
        if (last_refill_ns_ == 0) {
            last_refill_ns_ = now_ns;
            return;
        }
        
        uint64_t elapsed = now_ns - last_refill_ns_;
        double new_tokens = (double)elapsed / window_ns_ * rate_;
        
        tokens_ = std::min(static_cast<double>(rate_), tokens_ + new_tokens);
        last_refill_ns_ = now_ns;
    }
    
    int rate_;
    uint64_t window_ns_;
    double tokens_;
    uint64_t last_refill_ns_ = 0;
};
```

---

## 总结

**HFT算法题特点**：
1. 强调O(1)时间复杂度
2. 关注内存效率和缓存友好性
3. 避免动态内存分配
4. 使用定点数而非浮点数（精度）
5. 考虑数值稳定性
