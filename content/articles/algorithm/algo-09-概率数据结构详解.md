+++
title = "概率数据结构详解"
description = "深入讲解概率数据结构：Bloom Filter、Count-Min Sketch、HyperLogLog、Cuckoo Filter、Skip List及其在HFT中的应用"
date = 2026-01-21
draft = false
[taxonomies]
categories = ["算法"]
tags = ["数据结构", "Bloom Filter", "HyperLogLog", "概率算法", "HFT"]
+++

# 概率数据结构详解

## 概述

概率数据结构通过牺牲少量精确性换取显著的空间和时间效率。在HFT系统中，这些结构用于快速检测重复订单、统计唯一客户、监控异常等场景。

## 一、Bloom Filter

### 1.1 原理

Bloom Filter用于判断元素是否可能在集合中：
- **空间效率**：使用位数组而非存储元素
- **假阳性**：可能误报元素存在
- **无假阴性**：不存在的元素一定报告不存在

```
插入元素:
element ──► hash1 ──► 位置1 ──► 置1
        ├─► hash2 ──► 位置2 ──► 置1
        └─► hash3 ──► 位置3 ──► 置1

查询元素:
element ──► hash1 ──► 位置1 ──► 检查
        ├─► hash2 ──► 位置2 ──► 检查
        └─► hash3 ──► 位置3 ──► 检查
        
所有位置都为1: 可能存在
任一位置为0: 一定不存在
```

### 1.2 实现

```cpp
#include <vector>
#include <functional>
#include <cmath>

class BloomFilter {
public:
    BloomFilter(size_t expected_elements, double false_positive_rate) {
        // 计算最优参数
        bits_ = optimalBits(expected_elements, false_positive_rate);
        hash_count_ = optimalHashCount(bits_, expected_elements);
        
        bit_array_.resize((bits_ + 63) / 64, 0);
    }
    
    void insert(const std::string& key) {
        for (size_t i = 0; i < hash_count_; ++i) {
            size_t pos = hash(key, i) % bits_;
            setBit(pos);
        }
    }
    
    bool mightContain(const std::string& key) const {
        for (size_t i = 0; i < hash_count_; ++i) {
            size_t pos = hash(key, i) % bits_;
            if (!getBit(pos)) {
                return false;
            }
        }
        return true;
    }
    
    double falsePositiveRate() const {
        // 实际假阳性率
        double fill_ratio = static_cast<double>(countBits()) / bits_;
        return std::pow(fill_ratio, hash_count_);
    }
    
private:
    size_t optimalBits(size_t n, double p) {
        return static_cast<size_t>(-n * std::log(p) / (std::log(2) * std::log(2)));
    }
    
    size_t optimalHashCount(size_t m, size_t n) {
        return static_cast<size_t>(std::round(static_cast<double>(m) / n * std::log(2)));
    }
    
    size_t hash(const std::string& key, size_t seed) const {
        // 使用MurmurHash3变体
        size_t h = seed;
        for (char c : key) {
            h ^= c;
            h *= 0x5bd1e995;
            h ^= h >> 15;
        }
        return h;
    }
    
    void setBit(size_t pos) {
        bit_array_[pos / 64] |= (1ULL << (pos % 64));
    }
    
    bool getBit(size_t pos) const {
        return bit_array_[pos / 64] & (1ULL << (pos % 64));
    }
    
    size_t countBits() const {
        size_t count = 0;
        for (uint64_t word : bit_array_) {
            count += __builtin_popcountll(word);
        }
        return count;
    }
    
    size_t bits_;
    size_t hash_count_;
    std::vector<uint64_t> bit_array_;
};

// HFT应用：检测重复订单ID
class DuplicateOrderDetector {
public:
    DuplicateOrderDetector() : bloom_(1000000, 0.01) {}
    
    bool isDuplicate(const std::string& order_id) {
        if (bloom_.mightContain(order_id)) {
            // 可能重复，查精确集合确认
            return exact_set_.count(order_id) > 0;
        }
        return false;
    }
    
    void recordOrder(const std::string& order_id) {
        bloom_.insert(order_id);
        exact_set_.insert(order_id);
        
        // 定期清理
        if (exact_set_.size() > 10000000) {
            // 重建bloom filter和清理旧订单
        }
    }
    
private:
    BloomFilter bloom_;
    std::unordered_set<std::string> exact_set_;
};
```

## 二、Count-Min Sketch

### 2.1 原理

Count-Min Sketch用于估计元素频率：
- 使用多个哈希函数和计数器数组
- 查询返回所有位置的最小计数
- 只会高估，不会低估

```
结构:
     hash1  hash2  hash3  hash4
row1: [c] [ ] [c] [ ] [ ] [c] ...
row2: [ ] [c] [ ] [ ] [c] [ ] ...
row3: [c] [ ] [ ] [c] [ ] [ ] ...

估计频率 = min(row1[h1], row2[h2], row3[h3])
```

### 2.2 实现

```cpp
#include <vector>
#include <algorithm>
#include <limits>

class CountMinSketch {
public:
    CountMinSketch(size_t width, size_t depth) 
        : width_(width), depth_(depth), 
          table_(depth, std::vector<uint64_t>(width, 0)) {}
    
    void add(const std::string& key, uint64_t count = 1) {
        for (size_t i = 0; i < depth_; ++i) {
            size_t pos = hash(key, i) % width_;
            table_[i][pos] += count;
        }
    }
    
    uint64_t estimate(const std::string& key) const {
        uint64_t min_count = std::numeric_limits<uint64_t>::max();
        
        for (size_t i = 0; i < depth_; ++i) {
            size_t pos = hash(key, i) % width_;
            min_count = std::min(min_count, table_[i][pos]);
        }
        
        return min_count;
    }
    
    // 合并两个sketch
    void merge(const CountMinSketch& other) {
        for (size_t i = 0; i < depth_; ++i) {
            for (size_t j = 0; j < width_; ++j) {
                table_[i][j] += other.table_[i][j];
            }
        }
    }
    
private:
    size_t hash(const std::string& key, size_t seed) const {
        size_t h = seed * 0x9e3779b9;
        for (char c : key) {
            h ^= c + 0x9e3779b9 + (h << 6) + (h >> 2);
        }
        return h;
    }
    
    size_t width_;
    size_t depth_;
    std::vector<std::vector<uint64_t>> table_;
};

// HFT应用：监控每个客户的订单频率
class OrderRateMonitor {
public:
    OrderRateMonitor() : sketch_(10000, 5) {}
    
    bool checkRateLimit(const std::string& client_id, 
                        uint64_t max_orders_per_second) {
        sketch_.add(client_id);
        uint64_t count = sketch_.estimate(client_id);
        return count <= max_orders_per_second;
    }
    
    void resetWindow() {
        sketch_ = CountMinSketch(10000, 5);
    }
    
private:
    CountMinSketch sketch_;
};
```

## 三、HyperLogLog

### 3.1 原理

HyperLogLog用于估计集合基数（唯一元素数量）：
- 利用哈希值前导零的概率分布
- 使用多个桶取调和平均
- 标准误差约1.04/√m（m为桶数）

```
哈希值: 0001011010...
前导零数: 3

直觉：观察到k个前导零，约需2^k次尝试
取最大前导零数估计基数
```

### 3.2 实现

```cpp
#include <vector>
#include <cmath>
#include <algorithm>

class HyperLogLog {
public:
    HyperLogLog(int precision = 14) 
        : precision_(precision), 
          num_buckets_(1 << precision),
          buckets_(num_buckets_, 0) {
        // 偏差修正系数
        if (num_buckets_ == 16) alpha_ = 0.673;
        else if (num_buckets_ == 32) alpha_ = 0.697;
        else if (num_buckets_ == 64) alpha_ = 0.709;
        else alpha_ = 0.7213 / (1 + 1.079 / num_buckets_);
    }
    
    void add(const std::string& key) {
        uint64_t h = hash(key);
        
        // 前precision_位作为桶索引
        size_t bucket = h >> (64 - precision_);
        
        // 剩余位计算前导零
        uint64_t remaining = h << precision_;
        uint8_t leading_zeros = remaining == 0 ? 64 - precision_ 
                                                : __builtin_clzll(remaining) + 1;
        
        buckets_[bucket] = std::max(buckets_[bucket], leading_zeros);
    }
    
    uint64_t estimate() const {
        // 调和平均
        double sum = 0;
        for (uint8_t val : buckets_) {
            sum += std::pow(2.0, -val);
        }
        
        double raw_estimate = alpha_ * num_buckets_ * num_buckets_ / sum;
        
        // 小基数修正
        if (raw_estimate <= 2.5 * num_buckets_) {
            int zeros = std::count(buckets_.begin(), buckets_.end(), 0);
            if (zeros > 0) {
                return num_buckets_ * std::log(static_cast<double>(num_buckets_) / zeros);
            }
        }
        
        // 大基数修正
        if (raw_estimate > (1ULL << 32) / 30.0) {
            return -std::pow(2, 32) * std::log(1 - raw_estimate / std::pow(2, 32));
        }
        
        return static_cast<uint64_t>(raw_estimate);
    }
    
    // 合并两个HLL
    void merge(const HyperLogLog& other) {
        for (size_t i = 0; i < num_buckets_; ++i) {
            buckets_[i] = std::max(buckets_[i], other.buckets_[i]);
        }
    }
    
private:
    uint64_t hash(const std::string& key) const {
        uint64_t h = 0xcbf29ce484222325;
        for (char c : key) {
            h ^= c;
            h *= 0x100000001b3;
        }
        return h;
    }
    
    int precision_;
    size_t num_buckets_;
    double alpha_;
    std::vector<uint8_t> buckets_;
};

// HFT应用：统计唯一交易对手
class UniqueCounterpartCounter {
public:
    void recordTrade(const std::string& counterpart_id) {
        hll_.add(counterpart_id);
    }
    
    uint64_t uniqueCounterparts() const {
        return hll_.estimate();
    }
    
private:
    HyperLogLog hll_;
};
```

## 四、Cuckoo Filter

### 4.1 原理

Cuckoo Filter是Bloom Filter的改进版：
- 支持删除操作
- 更好的空间效率
- 使用指纹和两个可选位置

```
插入:
fingerprint = hash(element)
pos1 = hash1(element)
pos2 = pos1 XOR hash(fingerprint)

如果pos1或pos2有空位，插入
否则，踢出一个元素到其备选位置
```

### 4.2 实现

```cpp
#include <vector>
#include <random>

class CuckooFilter {
public:
    CuckooFilter(size_t capacity, int fingerprint_bits = 8)
        : capacity_(capacity),
          fingerprint_bits_(fingerprint_bits),
          max_kicks_(500),
          buckets_(capacity, Bucket()) {}
    
    bool insert(const std::string& key) {
        uint8_t fp = fingerprint(key);
        size_t i1 = hash1(key) % capacity_;
        size_t i2 = altIndex(i1, fp);
        
        // 尝试插入到两个位置之一
        if (buckets_[i1].insert(fp) || buckets_[i2].insert(fp)) {
            return true;
        }
        
        // 需要踢出
        size_t i = (rand() % 2 == 0) ? i1 : i2;
        
        for (int n = 0; n < max_kicks_; ++n) {
            uint8_t kicked_fp = buckets_[i].swap(fp);
            i = altIndex(i, kicked_fp);
            
            if (buckets_[i].insert(kicked_fp)) {
                return true;
            }
            
            fp = kicked_fp;
        }
        
        return false;  // 过滤器已满
    }
    
    bool contains(const std::string& key) const {
        uint8_t fp = fingerprint(key);
        size_t i1 = hash1(key) % capacity_;
        size_t i2 = altIndex(i1, fp);
        
        return buckets_[i1].contains(fp) || buckets_[i2].contains(fp);
    }
    
    bool remove(const std::string& key) {
        uint8_t fp = fingerprint(key);
        size_t i1 = hash1(key) % capacity_;
        size_t i2 = altIndex(i1, fp);
        
        if (buckets_[i1].remove(fp) || buckets_[i2].remove(fp)) {
            return true;
        }
        return false;
    }
    
private:
    static constexpr int BUCKET_SIZE = 4;
    
    struct Bucket {
        uint8_t slots[BUCKET_SIZE] = {0};
        
        bool insert(uint8_t fp) {
            for (int i = 0; i < BUCKET_SIZE; ++i) {
                if (slots[i] == 0) {
                    slots[i] = fp;
                    return true;
                }
            }
            return false;
        }
        
        bool contains(uint8_t fp) const {
            for (int i = 0; i < BUCKET_SIZE; ++i) {
                if (slots[i] == fp) return true;
            }
            return false;
        }
        
        bool remove(uint8_t fp) {
            for (int i = 0; i < BUCKET_SIZE; ++i) {
                if (slots[i] == fp) {
                    slots[i] = 0;
                    return true;
                }
            }
            return false;
        }
        
        uint8_t swap(uint8_t fp) {
            int idx = rand() % BUCKET_SIZE;
            uint8_t old = slots[idx];
            slots[idx] = fp;
            return old;
        }
    };
    
    uint8_t fingerprint(const std::string& key) const {
        uint64_t h = 0;
        for (char c : key) h = h * 31 + c;
        return (h % 255) + 1;  // 非零
    }
    
    size_t hash1(const std::string& key) const {
        size_t h = 0;
        for (char c : key) h = h * 131 + c;
        return h;
    }
    
    size_t altIndex(size_t index, uint8_t fp) const {
        return (index ^ (fp * 0x5bd1e995)) % capacity_;
    }
    
    size_t capacity_;
    int fingerprint_bits_;
    int max_kicks_;
    std::vector<Bucket> buckets_;
};
```

## 五、Skip List

### 5.1 原理

Skip List是一种支持快速查找的有序数据结构：
- 多层链表，上层是下层的"快速通道"
- 平均O(log n)查找、插入、删除
- 实现简单，易于并发

```
Level 3: head ─────────────────────────► 50 ─────────────────► NIL
Level 2: head ──────► 20 ──────────────► 50 ──────► 70 ──────► NIL
Level 1: head ──► 10 ─► 20 ──► 30 ──► 40 ─► 50 ──► 70 ──► 80 ─► NIL
Level 0: head ──► 10 ─► 20 ──► 30 ──► 40 ─► 50 ─► 60 ─► 70 ─► 80 ─► NIL
```

### 5.2 实现

```cpp
#include <vector>
#include <random>
#include <limits>

template<typename K, typename V>
class SkipList {
public:
    SkipList(int max_level = 16) 
        : max_level_(max_level), level_(0), 
          head_(new Node(K(), V(), max_level)),
          gen_(std::random_device{}()) {}
    
    ~SkipList() {
        Node* current = head_;
        while (current) {
            Node* next = current->forward[0];
            delete current;
            current = next;
        }
    }
    
    void insert(const K& key, const V& value) {
        std::vector<Node*> update(max_level_);
        Node* current = head_;
        
        // 找到插入位置
        for (int i = level_; i >= 0; --i) {
            while (current->forward[i] && current->forward[i]->key < key) {
                current = current->forward[i];
            }
            update[i] = current;
        }
        
        current = current->forward[0];
        
        if (current && current->key == key) {
            current->value = value;  // 更新
            return;
        }
        
        // 随机决定新节点层数
        int new_level = randomLevel();
        if (new_level > level_) {
            for (int i = level_ + 1; i <= new_level; ++i) {
                update[i] = head_;
            }
            level_ = new_level;
        }
        
        // 创建并插入新节点
        Node* new_node = new Node(key, value, new_level);
        for (int i = 0; i <= new_level; ++i) {
            new_node->forward[i] = update[i]->forward[i];
            update[i]->forward[i] = new_node;
        }
    }
    
    bool find(const K& key, V& value) const {
        Node* current = head_;
        
        for (int i = level_; i >= 0; --i) {
            while (current->forward[i] && current->forward[i]->key < key) {
                current = current->forward[i];
            }
        }
        
        current = current->forward[0];
        
        if (current && current->key == key) {
            value = current->value;
            return true;
        }
        return false;
    }
    
    bool remove(const K& key) {
        std::vector<Node*> update(max_level_);
        Node* current = head_;
        
        for (int i = level_; i >= 0; --i) {
            while (current->forward[i] && current->forward[i]->key < key) {
                current = current->forward[i];
            }
            update[i] = current;
        }
        
        current = current->forward[0];
        
        if (!current || current->key != key) {
            return false;
        }
        
        for (int i = 0; i <= level_; ++i) {
            if (update[i]->forward[i] != current) break;
            update[i]->forward[i] = current->forward[i];
        }
        
        delete current;
        
        while (level_ > 0 && !head_->forward[level_]) {
            --level_;
        }
        
        return true;
    }
    
private:
    struct Node {
        K key;
        V value;
        std::vector<Node*> forward;
        
        Node(const K& k, const V& v, int level)
            : key(k), value(v), forward(level + 1, nullptr) {}
    };
    
    int randomLevel() {
        int level = 0;
        while (level < max_level_ - 1 && 
               std::uniform_real_distribution<>(0, 1)(gen_) < 0.5) {
            ++level;
        }
        return level;
    }
    
    int max_level_;
    int level_;
    Node* head_;
    std::mt19937 gen_;
};

// HFT应用：价格级别管理
using PriceLevel = SkipList<int64_t, int64_t>;  // 价格 -> 数量
```

## 六、HFT应用总结

| 数据结构 | 典型应用 | 空间复杂度 | 时间复杂度 |
|----------|----------|------------|------------|
| Bloom Filter | 重复订单检测 | O(n) | O(k) |
| Count-Min Sketch | 频率限制 | O(w×d) | O(d) |
| HyperLogLog | 唯一客户统计 | O(m) | O(1) |
| Cuckoo Filter | 黑名单检测 | O(n) | O(1) |
| Skip List | 价格级别管理 | O(n) | O(log n) |

## 总结

概率数据结构的核心优势：

1. **空间效率**：显著减少内存使用
2. **时间效率**：常数或对数时间操作
3. **可合并**：支持分布式计算
4. **可配置精度**：根据需求调整误差率

在HFT系统中合理使用这些结构，可以在保证业务需求的同时大幅提升性能。
