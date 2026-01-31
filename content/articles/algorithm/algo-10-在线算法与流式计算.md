+++
title = "10.在线算法与流式计算(HFT)"
slug = "algo-10-在线算法与流式计算"
description = "深入讲解在线算法与流式计算：滑动窗口统计、Welford在线均值/方差、Reservoir Sampling、流式Top-K、EMA与VWAP计算"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["在线算法", "流式计算", "滑动窗口", "VWAP", "HFT"]
+++

# 在线算法与流式计算(HFT)

## 概述

在线算法在数据流到达时逐个处理，无需存储全部历史数据。这在HFT系统中尤为重要，因为市场数据是连续流入的，需要实时计算统计指标。

## 一、滑动窗口统计

### 1.1 滑动窗口求和

```cpp
#include <deque>
#include <cstdint>

class SlidingWindowSum {
public:
    explicit SlidingWindowSum(size_t window_size) 
        : window_size_(window_size), sum_(0) {}
    
    void add(double value) {
        window_.push_back(value);
        sum_ += value;
        
        while (window_.size() > window_size_) {
            sum_ -= window_.front();
            window_.pop_front();
        }
    }
    
    double sum() const { return sum_; }
    
    double mean() const {
        return window_.empty() ? 0 : sum_ / window_.size();
    }
    
    size_t size() const { return window_.size(); }
    
private:
    size_t window_size_;
    std::deque<double> window_;
    double sum_;
};
```

### 1.2 滑动窗口最大/最小值

使用单调队列实现O(1)查询：

```cpp
#include <deque>

class SlidingWindowMax {
public:
    explicit SlidingWindowMax(size_t window_size)
        : window_size_(window_size), current_index_(0) {}
    
    void add(double value) {
        // 移除过期元素
        while (!dq_.empty() && 
               dq_.front().index <= current_index_ - window_size_) {
            dq_.pop_front();
        }
        
        // 移除比当前值小的元素（它们永远不会成为最大值）
        while (!dq_.empty() && dq_.back().value <= value) {
            dq_.pop_back();
        }
        
        dq_.push_back({value, current_index_});
        ++current_index_;
    }
    
    double max() const {
        return dq_.empty() ? 0 : dq_.front().value;
    }
    
private:
    struct Entry {
        double value;
        size_t index;
    };
    
    size_t window_size_;
    size_t current_index_;
    std::deque<Entry> dq_;
};

// 同时跟踪最大最小值
class SlidingWindowMinMax {
public:
    explicit SlidingWindowMinMax(size_t window_size)
        : max_tracker_(window_size), min_tracker_(window_size) {}
    
    void add(double value) {
        max_tracker_.add(value);
        min_tracker_.add(-value);  // 取反实现最小值
    }
    
    double max() const { return max_tracker_.max(); }
    double min() const { return -min_tracker_.max(); }
    double range() const { return max() - min(); }
    
private:
    SlidingWindowMax max_tracker_;
    SlidingWindowMax min_tracker_;
};
```

### 1.3 滑动窗口中位数

```cpp
#include <set>
#include <queue>

class SlidingWindowMedian {
public:
    explicit SlidingWindowMedian(size_t window_size)
        : window_size_(window_size) {}
    
    void add(double value) {
        // 添加新值
        if (lower_.empty() || value <= *lower_.rbegin()) {
            lower_.insert(value);
        } else {
            upper_.insert(value);
        }
        
        window_.push(value);
        
        // 移除过期值
        while (window_.size() > window_size_) {
            double old = window_.front();
            window_.pop();
            
            auto it = lower_.find(old);
            if (it != lower_.end()) {
                lower_.erase(it);
            } else {
                upper_.erase(upper_.find(old));
            }
        }
        
        // 平衡两个集合
        balance();
    }
    
    double median() const {
        if (lower_.size() > upper_.size()) {
            return *lower_.rbegin();
        } else if (upper_.size() > lower_.size()) {
            return *upper_.begin();
        } else {
            return (*lower_.rbegin() + *upper_.begin()) / 2.0;
        }
    }
    
private:
    void balance() {
        while (lower_.size() > upper_.size() + 1) {
            auto it = --lower_.end();
            upper_.insert(*it);
            lower_.erase(it);
        }
        while (upper_.size() > lower_.size() + 1) {
            auto it = upper_.begin();
            lower_.insert(*it);
            upper_.erase(it);
        }
    }
    
    size_t window_size_;
    std::queue<double> window_;
    std::multiset<double> lower_;  // 较小的一半
    std::multiset<double> upper_;  // 较大的一半
};
```

## 二、Welford在线算法

### 2.1 在线均值和方差

Welford算法数值稳定地计算运行均值和方差：

```cpp
class WelfordStatistics {
public:
    WelfordStatistics() : n_(0), mean_(0), M2_(0) {}
    
    void update(double value) {
        ++n_;
        double delta = value - mean_;
        mean_ += delta / n_;
        double delta2 = value - mean_;
        M2_ += delta * delta2;
    }
    
    double mean() const { return mean_; }
    
    double variance() const {
        return n_ < 2 ? 0 : M2_ / n_;
    }
    
    double sample_variance() const {
        return n_ < 2 ? 0 : M2_ / (n_ - 1);
    }
    
    double stddev() const {
        return std::sqrt(variance());
    }
    
    size_t count() const { return n_; }
    
    // 合并两个统计
    void merge(const WelfordStatistics& other) {
        if (other.n_ == 0) return;
        if (n_ == 0) {
            *this = other;
            return;
        }
        
        size_t combined_n = n_ + other.n_;
        double delta = other.mean_ - mean_;
        double combined_mean = mean_ + delta * other.n_ / combined_n;
        double combined_M2 = M2_ + other.M2_ + 
                            delta * delta * n_ * other.n_ / combined_n;
        
        n_ = combined_n;
        mean_ = combined_mean;
        M2_ = combined_M2;
    }
    
private:
    size_t n_;
    double mean_;
    double M2_;
};

// 滑动窗口版本
class SlidingWelford {
public:
    explicit SlidingWelford(size_t window_size)
        : window_size_(window_size) {}
    
    void update(double value) {
        window_.push_back(value);
        stats_.update(value);
        
        if (window_.size() > window_size_) {
            // 从统计中移除最老的值（近似方法）
            // 精确方法需要重新计算
            double old = window_.front();
            window_.pop_front();
            
            if (window_.size() > 0) {
                // 简化：重新计算整个窗口
                stats_ = WelfordStatistics();
                for (double v : window_) {
                    stats_.update(v);
                }
            }
        }
    }
    
    double mean() const { return stats_.mean(); }
    double stddev() const { return stats_.stddev(); }
    
private:
    size_t window_size_;
    std::deque<double> window_;
    WelfordStatistics stats_;
};
```

### 2.2 在线协方差和相关性

```cpp
class OnlineCovariance {
public:
    OnlineCovariance() : n_(0), mean_x_(0), mean_y_(0), C_(0) {}
    
    void update(double x, double y) {
        ++n_;
        double dx = x - mean_x_;
        mean_x_ += dx / n_;
        double dy = y - mean_y_;
        mean_y_ += dy / n_;
        C_ += dx * (y - mean_y_);  // 注意：使用更新后的mean_y_
    }
    
    double covariance() const {
        return n_ < 2 ? 0 : C_ / n_;
    }
    
    double sample_covariance() const {
        return n_ < 2 ? 0 : C_ / (n_ - 1);
    }
    
private:
    size_t n_;
    double mean_x_;
    double mean_y_;
    double C_;
};

class OnlineCorrelation {
public:
    void update(double x, double y) {
        stats_x_.update(x);
        stats_y_.update(y);
        cov_.update(x, y);
    }
    
    double correlation() const {
        double sx = stats_x_.stddev();
        double sy = stats_y_.stddev();
        if (sx == 0 || sy == 0) return 0;
        return cov_.covariance() / (sx * sy);
    }
    
private:
    WelfordStatistics stats_x_;
    WelfordStatistics stats_y_;
    OnlineCovariance cov_;
};
```

## 三、指数移动平均(EMA)

### 3.1 EMA实现

```cpp
class ExponentialMovingAverage {
public:
    explicit ExponentialMovingAverage(double alpha) 
        : alpha_(alpha), initialized_(false), value_(0) {}
    
    // 从半衰期或窗口大小创建
    static ExponentialMovingAverage fromHalfLife(double half_life) {
        return ExponentialMovingAverage(1 - std::exp(-std::log(2) / half_life));
    }
    
    static ExponentialMovingAverage fromSpan(int span) {
        return ExponentialMovingAverage(2.0 / (span + 1));
    }
    
    void update(double value) {
        if (!initialized_) {
            value_ = value;
            initialized_ = true;
        } else {
            value_ = alpha_ * value + (1 - alpha_) * value_;
        }
    }
    
    double value() const { return value_; }
    
    bool initialized() const { return initialized_; }
    
private:
    double alpha_;
    bool initialized_;
    double value_;
};

// EMA方差（用于波动率估计）
class EMAVariance {
public:
    explicit EMAVariance(double alpha)
        : alpha_(alpha), mean_(alpha), var_(0), initialized_(false) {}
    
    void update(double value) {
        mean_.update(value);
        
        if (initialized_) {
            double diff = value - mean_.value();
            var_ = (1 - alpha_) * var_ + alpha_ * diff * diff;
        }
        initialized_ = true;
    }
    
    double variance() const { return var_; }
    double stddev() const { return std::sqrt(var_); }
    
private:
    double alpha_;
    ExponentialMovingAverage mean_;
    double var_;
    bool initialized_;
};
```

### 3.2 双重EMA（DEMA）和三重EMA（TEMA）

```cpp
class DEMA {
public:
    explicit DEMA(double alpha) : ema1_(alpha), ema2_(alpha) {}
    
    void update(double value) {
        ema1_.update(value);
        ema2_.update(ema1_.value());
    }
    
    double value() const {
        return 2 * ema1_.value() - ema2_.value();
    }
    
private:
    ExponentialMovingAverage ema1_;
    ExponentialMovingAverage ema2_;
};

class TEMA {
public:
    explicit TEMA(double alpha) : ema1_(alpha), ema2_(alpha), ema3_(alpha) {}
    
    void update(double value) {
        ema1_.update(value);
        ema2_.update(ema1_.value());
        ema3_.update(ema2_.value());
    }
    
    double value() const {
        return 3 * ema1_.value() - 3 * ema2_.value() + ema3_.value();
    }
    
private:
    ExponentialMovingAverage ema1_;
    ExponentialMovingAverage ema2_;
    ExponentialMovingAverage ema3_;
};
```

## 四、VWAP计算

### 4.1 实时VWAP

VWAP（成交量加权平均价格）是HFT中的重要指标：

```cpp
class VWAP {
public:
    VWAP() : total_value_(0), total_volume_(0) {}
    
    void addTrade(double price, double volume) {
        total_value_ += price * volume;
        total_volume_ += volume;
    }
    
    double vwap() const {
        return total_volume_ == 0 ? 0 : total_value_ / total_volume_;
    }
    
    double totalVolume() const { return total_volume_; }
    
    void reset() {
        total_value_ = 0;
        total_volume_ = 0;
    }
    
private:
    double total_value_;
    double total_volume_;
};

// 滑动窗口VWAP
class SlidingVWAP {
public:
    explicit SlidingVWAP(size_t window_size)
        : window_size_(window_size), total_value_(0), total_volume_(0) {}
    
    void addTrade(double price, double volume) {
        trades_.push_back({price, volume});
        total_value_ += price * volume;
        total_volume_ += volume;
        
        while (trades_.size() > window_size_) {
            auto& old = trades_.front();
            total_value_ -= old.price * old.volume;
            total_volume_ -= old.volume;
            trades_.pop_front();
        }
    }
    
    double vwap() const {
        return total_volume_ == 0 ? 0 : total_value_ / total_volume_;
    }
    
private:
    struct Trade {
        double price;
        double volume;
    };
    
    size_t window_size_;
    std::deque<Trade> trades_;
    double total_value_;
    double total_volume_;
};

// 时间窗口VWAP
class TimeWindowVWAP {
public:
    explicit TimeWindowVWAP(int64_t window_ns)
        : window_ns_(window_ns), total_value_(0), total_volume_(0) {}
    
    void addTrade(int64_t timestamp_ns, double price, double volume) {
        trades_.push_back({timestamp_ns, price, volume});
        total_value_ += price * volume;
        total_volume_ += volume;
        
        // 移除过期交易
        int64_t cutoff = timestamp_ns - window_ns_;
        while (!trades_.empty() && trades_.front().timestamp < cutoff) {
            auto& old = trades_.front();
            total_value_ -= old.price * old.volume;
            total_volume_ -= old.volume;
            trades_.pop_front();
        }
    }
    
    double vwap() const {
        return total_volume_ == 0 ? 0 : total_value_ / total_volume_;
    }
    
private:
    struct TimedTrade {
        int64_t timestamp;
        double price;
        double volume;
    };
    
    int64_t window_ns_;
    std::deque<TimedTrade> trades_;
    double total_value_;
    double total_volume_;
};
```

## 五、Reservoir Sampling

### 5.1 基本实现

从流中均匀随机采样k个元素：

```cpp
#include <random>
#include <vector>

template<typename T>
class ReservoirSampling {
public:
    explicit ReservoirSampling(size_t k)
        : k_(k), count_(0), gen_(std::random_device{}()) {}
    
    void add(const T& item) {
        ++count_;
        
        if (reservoir_.size() < k_) {
            reservoir_.push_back(item);
        } else {
            // 以k/count的概率替换
            std::uniform_int_distribution<size_t> dist(0, count_ - 1);
            size_t j = dist(gen_);
            if (j < k_) {
                reservoir_[j] = item;
            }
        }
    }
    
    const std::vector<T>& sample() const {
        return reservoir_;
    }
    
    size_t count() const { return count_; }
    
private:
    size_t k_;
    size_t count_;
    std::vector<T> reservoir_;
    std::mt19937 gen_;
};

// 带权重的水库抽样
template<typename T>
class WeightedReservoirSampling {
public:
    explicit WeightedReservoirSampling(size_t k)
        : k_(k), gen_(std::random_device{}()) {}
    
    void add(const T& item, double weight) {
        double key = std::pow(std::uniform_real_distribution<>(0, 1)(gen_), 
                              1.0 / weight);
        
        if (heap_.size() < k_) {
            heap_.push({key, item});
        } else if (key > heap_.top().key) {
            heap_.pop();
            heap_.push({key, item});
        }
    }
    
    std::vector<T> sample() const {
        std::vector<T> result;
        auto temp = heap_;
        while (!temp.empty()) {
            result.push_back(temp.top().item);
            temp.pop();
        }
        return result;
    }
    
private:
    struct Entry {
        double key;
        T item;
        bool operator<(const Entry& other) const {
            return key > other.key;  // 最小堆
        }
    };
    
    size_t k_;
    std::priority_queue<Entry> heap_;
    std::mt19937 gen_;
};
```

## 六、流式Top-K

### 6.1 Space-Saving算法

```cpp
#include <unordered_map>
#include <set>

class SpaceSaving {
public:
    explicit SpaceSaving(size_t k) : k_(k) {}
    
    void add(const std::string& item) {
        auto it = counters_.find(item);
        
        if (it != counters_.end()) {
            // 已存在，增加计数
            size_t old_count = it->second;
            ordered_.erase({old_count, item});
            ++it->second;
            ordered_.insert({it->second, item});
        } else if (counters_.size() < k_) {
            // 还有空间
            counters_[item] = 1;
            ordered_.insert({1, item});
        } else {
            // 替换最小元素
            auto min_it = ordered_.begin();
            size_t min_count = min_it->first;
            std::string min_item = min_it->second;
            
            ordered_.erase(min_it);
            counters_.erase(min_item);
            
            counters_[item] = min_count + 1;
            ordered_.insert({min_count + 1, item});
        }
    }
    
    std::vector<std::pair<std::string, size_t>> topK() const {
        std::vector<std::pair<std::string, size_t>> result;
        for (auto it = ordered_.rbegin(); it != ordered_.rend(); ++it) {
            result.emplace_back(it->second, it->first);
        }
        return result;
    }
    
    size_t estimate(const std::string& item) const {
        auto it = counters_.find(item);
        return it != counters_.end() ? it->second : 0;
    }
    
private:
    size_t k_;
    std::unordered_map<std::string, size_t> counters_;
    std::set<std::pair<size_t, std::string>> ordered_;
};

// HFT应用：跟踪最活跃的交易品种
class ActiveSymbolTracker {
public:
    explicit ActiveSymbolTracker(size_t top_n = 100) : tracker_(top_n) {}
    
    void recordTrade(const std::string& symbol) {
        tracker_.add(symbol);
    }
    
    std::vector<std::pair<std::string, size_t>> mostActive() const {
        return tracker_.topK();
    }
    
private:
    SpaceSaving tracker_;
};
```

## 七、TWAP计算

```cpp
class TWAP {
public:
    TWAP() : last_timestamp_(0), last_price_(0),
             time_weighted_sum_(0), total_time_(0) {}
    
    void updatePrice(int64_t timestamp_ns, double price) {
        if (last_timestamp_ > 0) {
            int64_t duration = timestamp_ns - last_timestamp_;
            time_weighted_sum_ += last_price_ * duration;
            total_time_ += duration;
        }
        
        last_timestamp_ = timestamp_ns;
        last_price_ = price;
    }
    
    double twap(int64_t current_timestamp_ns) const {
        if (total_time_ == 0 && last_timestamp_ == 0) {
            return 0;
        }
        
        int64_t duration = current_timestamp_ns - last_timestamp_;
        double adjusted_sum = time_weighted_sum_ + last_price_ * duration;
        int64_t adjusted_time = total_time_ + duration;
        
        return adjusted_time == 0 ? last_price_ : adjusted_sum / adjusted_time;
    }
    
    void reset() {
        last_timestamp_ = 0;
        last_price_ = 0;
        time_weighted_sum_ = 0;
        total_time_ = 0;
    }
    
private:
    int64_t last_timestamp_;
    double last_price_;
    double time_weighted_sum_;
    int64_t total_time_;
};
```

## 八、HFT实时指标计算器

```cpp
class RealTimeMarketMetrics {
public:
    RealTimeMarketMetrics()
        : vwap_(), 
          twap_(),
          ema_price_(0.1),
          ema_volume_(0.1),
          volatility_(0.05),
          trade_count_(0) {}
    
    void onTrade(int64_t timestamp_ns, double price, double volume) {
        // 更新VWAP
        vwap_.addTrade(price, volume);
        
        // 更新TWAP
        twap_.updatePrice(timestamp_ns, price);
        
        // 更新EMA
        ema_price_.update(price);
        ema_volume_.update(volume);
        
        // 更新波动率
        volatility_.update(price);
        
        ++trade_count_;
    }
    
    double getVWAP() const { return vwap_.vwap(); }
    double getTWAP(int64_t now_ns) const { return twap_.twap(now_ns); }
    double getEMAPrice() const { return ema_price_.value(); }
    double getVolatility() const { return volatility_.stddev(); }
    size_t getTradeCount() const { return trade_count_; }
    
private:
    VWAP vwap_;
    TWAP twap_;
    ExponentialMovingAverage ema_price_;
    ExponentialMovingAverage ema_volume_;
    EMAVariance volatility_;
    size_t trade_count_;
};
```

## 总结

在线算法的核心特点：

1. **单遍处理**：数据只需遍历一次
2. **有限内存**：不需要存储全部历史数据
3. **增量更新**：每次更新时间复杂度低
4. **数值稳定**：使用Welford等稳定算法

这些算法是HFT实时计算系统的基础组件。

---

## 概念速查

- [算法与数据结构概念索引](/articles/00-glossary/glossary-03-algorithm-concepts/) - 滑动窗口、时间复杂度等概念速查
- [HFT核心概念索引](/articles/00-glossary/glossary-04-hft-concepts/) - 实时计算、VWAP等概念速查

---

## 相关文章

- [上一篇：概率数据结构详解(HFT)](/articles/algorithm/algo-09-概率数据结构详解/)
- [下一篇：平衡树详解](/articles/algorithm/algo-11-平衡树详解/)
