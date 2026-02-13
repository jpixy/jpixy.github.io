+++
title = "13. Order Book实现详解"
slug = "hft-13-OrderBook实现详解"
date = 2026-01-21
weight = 13000
description = "深入剖析Order Book的实现，包括数据结构选择、价格级别管理、快速查找、增量更新和内存优化"
[taxonomies]
tags = ["HFT", "OrderBook", "数据结构", "低延迟", "交易系统"]
+++

## 概述

Order Book是交易系统的核心数据结构，存储市场上所有挂单信息。高效的Order Book实现直接影响交易系统的延迟。

---

## 一、Order Book基础

### 1.1 数据结构概述

**Order Book结构**：

| 类型 | Price | Qty | Orders | 备注 |
|------|-------|-----|--------|------|
| ASKS (卖方) | 100.03 | 500 | [Order1, Order2] | |
| ASKS (卖方) | 100.02 | 300 | [Order3] | |
| ASKS (卖方) | 100.01 | 1000 | [Order4, Order5] | ← Best Ask |
| BIDS (买方) | 100.00 | 800 | [Order6, Order7] | ← Best Bid |
| BIDS (买方) | 99.99 | 1200 | [Order8] | |
| BIDS (买方) | 99.98 | 400 | [Order9, Order10] | |

### 1.2 核心操作

```cpp
class OrderBook {
public:
    // 核心操作 - 目标O(1)或O(log n)
    void add_order(const Order& order);      // 添加订单
    void cancel_order(uint64_t order_id);    // 撤销订单
    void modify_order(uint64_t order_id, 
                      uint64_t new_qty);     // 修改订单
    
    // 查询操作 - 必须O(1)
    Price get_best_bid() const;
    Price get_best_ask() const;
    Price get_mid_price() const;
    Quantity get_bid_qty_at(Price price) const;
    Quantity get_ask_qty_at(Price price) const;
    
    // 深度查询
    std::vector<PriceLevel> get_bid_levels(int depth) const;
    std::vector<PriceLevel> get_ask_levels(int depth) const;
};
```

---

## 二、数据结构选择

### 2.1 基于Map的实现

```cpp
#include <map>

class MapOrderBook {
public:
    void add_order(const Order& order) {
        if (order.side == Side::BUY) {
            bids_[order.price].add_order(order);
        } else {
            asks_[order.price].add_order(order);
        }
    }
    
    Price get_best_bid() const {
        return bids_.empty() ? 0 : bids_.rbegin()->first;
    }
    
    Price get_best_ask() const {
        return asks_.empty() ? 0 : asks_.begin()->first;
    }
    
private:
    std::map<Price, PriceLevel, std::greater<Price>> bids_;  // 降序
    std::map<Price, PriceLevel> asks_;  // 升序
};

// 优点：自动排序，实现简单
// 缺点：O(log n)查找，内存分散，缓存不友好
```

### 2.2 基于数组的实现（价格索引）

```cpp
// 适用于价格范围有限且密集的市场

class ArrayOrderBook {
public:
    ArrayOrderBook(Price min_price, Price max_price, Price tick_size)
        : min_price_(min_price), 
          tick_size_(tick_size),
          levels_((max_price - min_price) / tick_size + 1) {}
    
    void add_order(const Order& order) {
        size_t idx = price_to_index(order.price);
        levels_[idx].add_order(order);
        
        if (order.side == Side::BUY) {
            if (order.price > best_bid_) best_bid_ = order.price;
        } else {
            if (best_ask_ == 0 || order.price < best_ask_) 
                best_ask_ = order.price;
        }
    }
    
    Price get_best_bid() const { return best_bid_; }
    Price get_best_ask() const { return best_ask_; }
    
    const PriceLevel& get_level(Price price) const {
        return levels_[price_to_index(price)];
    }
    
private:
    size_t price_to_index(Price price) const {
        return (price - min_price_) / tick_size_;
    }
    
    Price min_price_;
    Price tick_size_;
    std::vector<PriceLevel> levels_;
    Price best_bid_ = 0;
    Price best_ask_ = 0;
};

// 优点：O(1)价格级别访问
// 缺点：内存使用大，需要维护best_bid/ask
```

### 2.3 混合实现

```cpp
// 结合数组（热区）和Map（冷区）

class HybridOrderBook {
public:
    HybridOrderBook(Price center_price, Price tick_size, size_t hot_levels = 100)
        : center_(center_price), 
          tick_size_(tick_size),
          hot_half_(hot_levels / 2),
          hot_levels_(hot_levels) {
        bid_hot_.resize(hot_half_);
        ask_hot_.resize(hot_half_);
    }
    
    void add_order(const Order& order) {
        int offset = (order.price - center_) / tick_size_;
        
        if (order.side == Side::BUY) {
            if (offset >= -static_cast<int>(hot_half_) && offset < 0) {
                // 热区
                bid_hot_[-offset - 1].add_order(order);
            } else {
                // 冷区
                bid_cold_[order.price].add_order(order);
            }
        } else {
            if (offset >= 0 && offset < static_cast<int>(hot_half_)) {
                ask_hot_[offset].add_order(order);
            } else {
                ask_cold_[order.price].add_order(order);
            }
        }
    }
    
private:
    Price center_;
    Price tick_size_;
    size_t hot_half_;
    size_t hot_levels_;
    
    std::vector<PriceLevel> bid_hot_;  // 热区bid
    std::vector<PriceLevel> ask_hot_;  // 热区ask
    std::map<Price, PriceLevel, std::greater<Price>> bid_cold_;
    std::map<Price, PriceLevel> ask_cold_;
};
```

---

## 三、价格级别管理

### 3.1 价格级别结构

```cpp
struct Order {
    uint64_t order_id;
    Price price;
    Quantity quantity;
    Quantity remaining;
    Side side;
    uint64_t timestamp;
    Order* prev = nullptr;
    Order* next = nullptr;
};

class PriceLevel {
public:
    void add_order(Order* order) {
        // 添加到队列尾部（Price-Time优先级）
        if (tail_) {
            tail_->next = order;
            order->prev = tail_;
            tail_ = order;
        } else {
            head_ = tail_ = order;
        }
        total_qty_ += order->remaining;
        order_count_++;
    }
    
    void remove_order(Order* order) {
        if (order->prev) order->prev->next = order->next;
        else head_ = order->next;
        
        if (order->next) order->next->prev = order->prev;
        else tail_ = order->prev;
        
        total_qty_ -= order->remaining;
        order_count_--;
    }
    
    void reduce_qty(Order* order, Quantity delta) {
        order->remaining -= delta;
        total_qty_ -= delta;
        
        if (order->remaining == 0) {
            remove_order(order);
        }
    }
    
    // O(1) 查询
    Quantity total_qty() const { return total_qty_; }
    size_t order_count() const { return order_count_; }
    bool empty() const { return order_count_ == 0; }
    Order* front() const { return head_; }
    
private:
    Order* head_ = nullptr;
    Order* tail_ = nullptr;
    Quantity total_qty_ = 0;
    size_t order_count_ = 0;
};
```

### 3.2 订单查找优化

```cpp
class OrderBook {
public:
    void add_order(Order* order) {
        // O(1) 插入到哈希表
        orders_[order->order_id] = order;
        
        // 添加到价格级别
        get_or_create_level(order->price, order->side).add_order(order);
    }
    
    void cancel_order(uint64_t order_id) {
        auto it = orders_.find(order_id);
        if (it == orders_.end()) return;
        
        Order* order = it->second;
        get_level(order->price, order->side).remove_order(order);
        orders_.erase(it);
        
        // 归还到内存池
        order_pool_.release(order);
    }
    
    Order* find_order(uint64_t order_id) {
        auto it = orders_.find(order_id);
        return it != orders_.end() ? it->second : nullptr;
    }
    
private:
    std::unordered_map<uint64_t, Order*> orders_;  // O(1) 订单查找
    ObjectPool<Order> order_pool_;
};
```

---

## 四、增量更新处理

### 4.1 L2增量更新

```cpp
// Level 2数据只有价格/数量，无订单详情

struct L2Update {
    Price price;
    Quantity quantity;  // 新的总数量，0表示删除
    Side side;
};

class L2OrderBook {
public:
    void apply_update(const L2Update& update) {
        auto& levels = update.side == Side::BUY ? bids_ : asks_;
        
        if (update.quantity == 0) {
            // 删除价格级别
            levels.erase(update.price);
        } else {
            // 更新或创建价格级别
            levels[update.price] = update.quantity;
        }
        
        update_best_prices();
    }
    
    void apply_snapshot(const std::vector<L2Update>& snapshot) {
        bids_.clear();
        asks_.clear();
        
        for (const auto& update : snapshot) {
            if (update.quantity > 0) {
                auto& levels = update.side == Side::BUY ? bids_ : asks_;
                levels[update.price] = update.quantity;
            }
        }
        
        update_best_prices();
    }
    
private:
    std::map<Price, Quantity, std::greater<Price>> bids_;
    std::map<Price, Quantity> asks_;
    Price best_bid_ = 0;
    Price best_ask_ = 0;
    
    void update_best_prices() {
        best_bid_ = bids_.empty() ? 0 : bids_.begin()->first;
        best_ask_ = asks_.empty() ? 0 : asks_.begin()->first;
    }
};
```

### 4.2 L3增量更新

```cpp
// Level 3数据包含完整订单信息

enum class L3Action {
    ADD,
    MODIFY,
    DELETE,
    EXECUTE
};

struct L3Update {
    L3Action action;
    uint64_t order_id;
    Price price;
    Quantity quantity;
    Side side;
    uint64_t sequence;
};

class L3OrderBook {
public:
    void apply_update(const L3Update& update) {
        switch (update.action) {
            case L3Action::ADD:
                add_order(update);
                break;
            case L3Action::MODIFY:
                modify_order(update);
                break;
            case L3Action::DELETE:
                cancel_order(update.order_id);
                break;
            case L3Action::EXECUTE:
                execute_order(update);
                break;
        }
        last_sequence_ = update.sequence;
    }
    
    bool has_gap(uint64_t sequence) const {
        return sequence != last_sequence_ + 1;
    }
    
private:
    void add_order(const L3Update& update) {
        Order* order = order_pool_.allocate();
        order->order_id = update.order_id;
        order->price = update.price;
        order->remaining = update.quantity;
        order->side = update.side;
        
        orders_[update.order_id] = order;
        get_level(update.price, update.side).add_order(order);
    }
    
    void execute_order(const L3Update& update) {
        Order* order = find_order(update.order_id);
        if (!order) return;
        
        get_level(order->price, order->side)
            .reduce_qty(order, update.quantity);
        
        if (order->remaining == 0) {
            orders_.erase(update.order_id);
            order_pool_.release(order);
        }
    }
    
    uint64_t last_sequence_ = 0;
};
```

---

## 五、内存优化

### 5.1 对象池

```cpp
template<typename T, size_t BlockSize = 4096>
class ObjectPool {
public:
    T* allocate() {
        if (free_list_) {
            T* obj = free_list_;
            free_list_ = *reinterpret_cast<T**>(free_list_);
            return new (obj) T();
        }
        
        if (current_block_pos_ >= BlockSize) {
            allocate_block();
        }
        
        T* obj = &blocks_.back()[current_block_pos_++];
        return new (obj) T();
    }
    
    void release(T* obj) {
        obj->~T();
        *reinterpret_cast<T**>(obj) = free_list_;
        free_list_ = obj;
    }
    
private:
    void allocate_block() {
        blocks_.push_back(
            std::make_unique<std::array<T, BlockSize>>()
        );
        current_block_pos_ = 0;
    }
    
    std::vector<std::unique_ptr<std::array<T, BlockSize>>> blocks_;
    size_t current_block_pos_ = BlockSize;
    T* free_list_ = nullptr;
};
```

### 5.2 内存布局优化

```cpp
// 缓存行对齐
struct alignas(64) CacheLinePriceLevel {
    Quantity total_qty;
    uint32_t order_count;
    Order* head;
    Order* tail;
    char padding[64 - sizeof(Quantity) - sizeof(uint32_t) - 
                 sizeof(Order*) * 2];
};

// 紧凑订单结构
struct CompactOrder {
    uint64_t order_id;      // 8 bytes
    uint32_t price_ticks;   // 4 bytes (相对价格)
    uint32_t remaining;     // 4 bytes
    uint16_t next_offset;   // 2 bytes (相对偏移)
    uint16_t prev_offset;   // 2 bytes
    uint8_t side;           // 1 byte
    uint8_t flags;          // 1 byte
    // Total: 22 bytes, 可以进一步压缩
};
```

### 5.3 预分配与热点数据

```cpp
class OptimizedOrderBook {
public:
    OptimizedOrderBook() {
        // 预分配价格级别
        bid_levels_.reserve(1000);
        ask_levels_.reserve(1000);
        
        // 预分配订单空间
        orders_.reserve(100000);
        
        // 预热内存（避免页错误）
        for (auto& level : bid_levels_) {
            volatile char* p = reinterpret_cast<char*>(&level);
            *p = 0;
        }
    }
    
    // 热点数据内联
    Price best_bid() const { return best_bid_; }
    Price best_ask() const { return best_ask_; }
    Quantity bid_qty_top() const { return bid_qty_top_; }
    Quantity ask_qty_top() const { return ask_qty_top_; }
    
private:
    // 热点数据放在一起
    Price best_bid_ = 0;
    Price best_ask_ = 0;
    Quantity bid_qty_top_ = 0;
    Quantity ask_qty_top_ = 0;
    
    std::vector<PriceLevel> bid_levels_;
    std::vector<PriceLevel> ask_levels_;
    std::unordered_map<uint64_t, Order*> orders_;
};
```

---

## 六、性能基准

### 6.1 操作延迟目标

| 操作 | 目标延迟 | 实现要求 |
|------|----------|----------|
| get_best_bid/ask | <10ns | O(1)，内联缓存 |
| add_order | <100ns | O(1)预期，对象池 |
| cancel_order | <50ns | O(1)哈希查找 |
| get_level_qty | <20ns | O(1)数组索引 |
| apply_update | <100ns | 批量优化 |

### 6.2 基准测试

```cpp
void benchmark_orderbook() {
    OrderBook book;
    
    // 预热
    for (int i = 0; i < 10000; ++i) {
        Order order{/* ... */};
        book.add_order(order);
    }
    
    // 测试add_order
    auto start = rdtsc();
    for (int i = 0; i < 100000; ++i) {
        Order order{/* ... */};
        book.add_order(order);
    }
    auto end = rdtsc();
    
    double ns_per_op = cycles_to_ns(end - start) / 100000.0;
    printf("add_order: %.1f ns/op\n", ns_per_op);
}
```

---

## 总结

| 实现方式 | 添加 | 删除 | 查找 | 内存 | 适用场景 |
|----------|------|------|------|------|----------|
| std::map | O(log n) | O(log n) | O(log n) | 中 | 通用 |
| 数组索引 | O(1) | O(1) | O(1) | 大 | 密集价格 |
| 混合 | O(1)热 | O(1)热 | O(1)热 | 中 | 生产环境 |

**最佳实践**：
1. 使用对象池避免动态分配
2. 热点数据缓存行对齐
3. 分离热区和冷区
4. 预分配并预热内存
5. 使用哈希表O(1)订单查找

---

## 概念速查

- [算法与数据结构概念索引](@/articles/00-glossary/glossary-03-algorithm-concepts.md) - 红黑树、哈希表、对象池等概念速查
- [HFT核心概念索引](@/articles/00-glossary/glossary-04-hft-concepts.md) - OrderBook、低延迟等概念速查
- [C++核心概念索引](@/articles/00-glossary/glossary-05-cpp-concepts.md) - 内存管理、智能指针等概念速查

---

## 相关文章

- [上一篇：HFT系统延迟分析方法](@/articles/hft/hft-12-HFT系统延迟分析方法.md)
- [下一篇：Market Making策略原理](@/articles/hft/hft-14-MarketMaking策略原理.md)
