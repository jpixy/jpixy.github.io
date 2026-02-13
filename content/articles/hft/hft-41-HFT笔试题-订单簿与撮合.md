+++
title = "HFT笔试题-订单簿与撮合"
date = 2026-02-02
weight = 41000
description = "HFT笔试：订单簿实现、撮合引擎、价格优先时间优先、订单类型"
[taxonomies]
tags = ["HFT", "笔试", "订单簿", "撮合", "数据结构"]
+++

# HFT 笔试题 - 订单簿与撮合

本文汇总 HFT 笔试中关于订单簿实现和撮合引擎的编程题目。

---

## 题目 1：基础订单簿实现

**题目**：实现一个支持限价单的订单簿，要求：
- 支持添加订单（买/卖）
- 支持取消订单
- 获取最优买卖价格
- 时间复杂度要求：添加 O(log n)，取消 O(1)，查询 O(1)

**解答**：

```cpp
#include <map>
#include <unordered_map>
#include <list>

enum class Side { Buy, Sell };

struct Order {
    uint64_t order_id;
    Side side;
    double price;
    int quantity;
    
    // 用于链表定位
    std::list<Order*>::iterator list_it;
};

class OrderBook {
public:
    void add_order(Order* order) {
        orders_[order->order_id] = order;
        
        if (order->side == Side::Buy) {
            auto& level = bids_[order->price];
            level.push_back(order);
            order->list_it = std::prev(level.end());
        } else {
            auto& level = asks_[order->price];
            level.push_back(order);
            order->list_it = std::prev(level.end());
        }
    }
    
    bool cancel_order(uint64_t order_id) {
        auto it = orders_.find(order_id);
        if (it == orders_.end()) return false;
        
        Order* order = it->second;
        
        if (order->side == Side::Buy) {
            auto& level = bids_[order->price];
            level.erase(order->list_it);
            if (level.empty()) bids_.erase(order->price);
        } else {
            auto& level = asks_[order->price];
            level.erase(order->list_it);
            if (level.empty()) asks_.erase(order->price);
        }
        
        orders_.erase(it);
        delete order;
        return true;
    }
    
    double best_bid() const {
        return bids_.empty() ? 0 : bids_.rbegin()->first;
    }
    
    double best_ask() const {
        return asks_.empty() ? 0 : asks_.begin()->first;
    }
    
    int bid_size_at(double price) const {
        auto it = bids_.find(price);
        if (it == bids_.end()) return 0;
        int total = 0;
        for (const auto* order : it->second) {
            total += order->quantity;
        }
        return total;
    }
    
private:
    // 买盘：价格降序（greater），高价优先
    std::map<double, std::list<Order*>, std::greater<double>> bids_;
    // 卖盘：价格升序，低价优先
    std::map<double, std::list<Order*>> asks_;
    // 订单索引
    std::unordered_map<uint64_t, Order*> orders_;
};
```

---

## 题目 2：价格优先时间优先撮合

**题目**：实现撮合引擎，支持：
- 限价单撮合
- 价格优先、时间优先规则
- 返回成交结果

**解答**：

```cpp
struct Fill {
    uint64_t maker_order_id;
    uint64_t taker_order_id;
    double price;
    int quantity;
};

class MatchingEngine {
public:
    std::vector<Fill> process_order(Order* order) {
        std::vector<Fill> fills;
        
        if (order->side == Side::Buy) {
            match_buy(order, fills);
        } else {
            match_sell(order, fills);
        }
        
        // 剩余数量加入订单簿
        if (order->quantity > 0) {
            book_.add_order(order);
        } else {
            delete order;
        }
        
        return fills;
    }
    
private:
    void match_buy(Order* buy_order, std::vector<Fill>& fills) {
        // 买单与卖盘撮合
        while (buy_order->quantity > 0 && !asks_.empty()) {
            auto ask_it = asks_.begin();
            double ask_price = ask_it->first;
            
            // 价格不匹配
            if (buy_order->price < ask_price) break;
            
            auto& level = ask_it->second;
            while (!level.empty() && buy_order->quantity > 0) {
                Order* sell_order = level.front();
                
                int match_qty = std::min(buy_order->quantity, sell_order->quantity);
                
                fills.push_back({
                    sell_order->order_id,
                    buy_order->order_id,
                    ask_price,  // 以挂单价成交
                    match_qty
                });
                
                buy_order->quantity -= match_qty;
                sell_order->quantity -= match_qty;
                
                if (sell_order->quantity == 0) {
                    level.pop_front();
                    orders_.erase(sell_order->order_id);
                    delete sell_order;
                }
            }
            
            if (level.empty()) {
                asks_.erase(ask_it);
            }
        }
    }
    
    void match_sell(Order* sell_order, std::vector<Fill>& fills) {
        // 卖单与买盘撮合
        while (sell_order->quantity > 0 && !bids_.empty()) {
            auto bid_it = bids_.begin();
            double bid_price = bid_it->first;
            
            if (sell_order->price > bid_price) break;
            
            auto& level = bid_it->second;
            while (!level.empty() && sell_order->quantity > 0) {
                Order* buy_order = level.front();
                
                int match_qty = std::min(sell_order->quantity, buy_order->quantity);
                
                fills.push_back({
                    buy_order->order_id,
                    sell_order->order_id,
                    bid_price,
                    match_qty
                });
                
                sell_order->quantity -= match_qty;
                buy_order->quantity -= match_qty;
                
                if (buy_order->quantity == 0) {
                    level.pop_front();
                    orders_.erase(buy_order->order_id);
                    delete buy_order;
                }
            }
            
            if (level.empty()) {
                bids_.erase(bid_it);
            }
        }
    }
    
    std::map<double, std::list<Order*>, std::greater<double>> bids_;
    std::map<double, std::list<Order*>> asks_;
    std::unordered_map<uint64_t, Order*> orders_;
};
```

---

## 题目 3：市价单处理

**题目**：扩展撮合引擎，支持市价单（Market Order）。

**解答**：

```cpp
enum class OrderType { Limit, Market };

struct Order {
    uint64_t order_id;
    Side side;
    OrderType type;
    double price;      // 市价单忽略
    int quantity;
};

std::vector<Fill> process_market_order(Order* order) {
    std::vector<Fill> fills;
    
    if (order->side == Side::Buy) {
        // 市价买单：吃掉卖盘直到数量满足
        while (order->quantity > 0 && !asks_.empty()) {
            auto ask_it = asks_.begin();
            auto& level = ask_it->second;
            
            while (!level.empty() && order->quantity > 0) {
                Order* sell_order = level.front();
                int match_qty = std::min(order->quantity, sell_order->quantity);
                
                fills.push_back({
                    sell_order->order_id,
                    order->order_id,
                    sell_order->price,
                    match_qty
                });
                
                order->quantity -= match_qty;
                sell_order->quantity -= match_qty;
                
                if (sell_order->quantity == 0) {
                    level.pop_front();
                    delete sell_order;
                }
            }
            
            if (level.empty()) asks_.erase(ask_it);
        }
    } else {
        // 市价卖单类似
        // ...
    }
    
    // 市价单不进入订单簿
    delete order;
    return fills;
}
```

---

## 题目 4：IOC 和 FOK 订单

**题目**：实现 IOC（Immediate or Cancel）和 FOK（Fill or Kill）订单类型。

**解答**：

```cpp
enum class TimeInForce { GTC, IOC, FOK };

struct Order {
    // ... 其他字段
    TimeInForce tif;
};

std::vector<Fill> process_order(Order* order) {
    std::vector<Fill> fills;
    int original_qty = order->quantity;
    
    // 先尝试撮合
    if (order->side == Side::Buy) {
        match_buy(order, fills);
    } else {
        match_sell(order, fills);
    }
    
    switch (order->tif) {
        case TimeInForce::GTC:
            // 剩余数量加入订单簿
            if (order->quantity > 0) {
                book_.add_order(order);
            }
            break;
            
        case TimeInForce::IOC:
            // 立即撤销剩余部分
            if (order->quantity > 0) {
                delete order;
            }
            break;
            
        case TimeInForce::FOK:
            // 如果没有完全成交，撤销所有成交
            if (order->quantity > 0) {
                // 回滚成交（实际系统中需要更复杂的处理）
                fills.clear();
                delete order;
            }
            break;
    }
    
    return fills;
}

// FOK 预检查版本（更高效）
bool can_fill_completely(const Order* order) {
    int available = 0;
    
    if (order->side == Side::Buy) {
        for (const auto& [price, level] : asks_) {
            if (price > order->price) break;
            for (const auto* o : level) {
                available += o->quantity;
                if (available >= order->quantity) return true;
            }
        }
    } else {
        for (const auto& [price, level] : bids_) {
            if (price < order->price) break;
            for (const auto* o : level) {
                available += o->quantity;
                if (available >= order->quantity) return true;
            }
        }
    }
    
    return false;
}
```

---

## 题目 5：订单簿快照与增量更新

**题目**：实现订单簿的快照生成和增量更新处理。

**解答**：

```cpp
struct PriceLevel {
    double price;
    int quantity;
    int order_count;
};

struct BookSnapshot {
    std::vector<PriceLevel> bids;  // 前 N 档买盘
    std::vector<PriceLevel> asks;  // 前 N 档卖盘
    uint64_t sequence;
};

struct BookDelta {
    enum Action { Add, Modify, Delete };
    Action action;
    Side side;
    double price;
    int quantity;
    uint64_t sequence;
};

class OrderBookWithSnapshot {
public:
    BookSnapshot get_snapshot(int depth = 10) const {
        BookSnapshot snap;
        snap.sequence = sequence_;
        
        int count = 0;
        for (const auto& [price, level] : bids_) {
            if (count++ >= depth) break;
            int qty = 0;
            for (const auto* o : level) qty += o->quantity;
            snap.bids.push_back({price, qty, (int)level.size()});
        }
        
        count = 0;
        for (const auto& [price, level] : asks_) {
            if (count++ >= depth) break;
            int qty = 0;
            for (const auto* o : level) qty += o->quantity;
            snap.asks.push_back({price, qty, (int)level.size()});
        }
        
        return snap;
    }
    
    void apply_delta(const BookDelta& delta) {
        if (delta.sequence != sequence_ + 1) {
            // 序列号不连续，需要重新同步
            request_snapshot();
            return;
        }
        
        sequence_ = delta.sequence;
        
        auto& book = (delta.side == Side::Buy) ? bid_levels_ : ask_levels_;
        
        switch (delta.action) {
            case BookDelta::Add:
            case BookDelta::Modify:
                book[delta.price] = delta.quantity;
                break;
            case BookDelta::Delete:
                book.erase(delta.price);
                break;
        }
    }
    
private:
    uint64_t sequence_ = 0;
    std::map<double, int, std::greater<double>> bid_levels_;
    std::map<double, int> ask_levels_;
};
```

---

## 题目 6：高性能订单簿（内存池）

**题目**：使用内存池优化订单分配。

**解答**：

```cpp
template<typename T, size_t BlockSize = 4096>
class MemoryPool {
public:
    T* allocate() {
        if (free_list_) {
            T* ptr = free_list_;
            free_list_ = *reinterpret_cast<T**>(ptr);
            return ptr;
        }
        
        if (current_block_ == nullptr || block_pos_ >= BlockSize) {
            allocate_block();
        }
        
        return &current_block_[block_pos_++];
    }
    
    void deallocate(T* ptr) {
        *reinterpret_cast<T**>(ptr) = free_list_;
        free_list_ = ptr;
    }
    
private:
    void allocate_block() {
        current_block_ = new T[BlockSize];
        blocks_.push_back(current_block_);
        block_pos_ = 0;
    }
    
    T* free_list_ = nullptr;
    T* current_block_ = nullptr;
    size_t block_pos_ = 0;
    std::vector<T*> blocks_;
};

// 使用
MemoryPool<Order> order_pool;

Order* create_order() {
    Order* order = order_pool.allocate();
    new (order) Order();  // placement new
    return order;
}

void destroy_order(Order* order) {
    order->~Order();
    order_pool.deallocate(order);
}
```

---

## 题目 7：订单簿不平衡指标

**题目**：计算订单簿不平衡指标。

**解答**：

```cpp
struct ImbalanceMetrics {
    double bid_ask_imbalance;     // 买卖不平衡
    double depth_imbalance;        // 深度不平衡
    double weighted_mid_price;     // 加权中间价
};

ImbalanceMetrics calculate_imbalance(const OrderBook& book, int levels = 5) {
    ImbalanceMetrics metrics;
    
    double bid_qty = 0, ask_qty = 0;
    double bid_value = 0, ask_value = 0;
    
    int count = 0;
    for (const auto& [price, level] : book.bids()) {
        if (count++ >= levels) break;
        for (const auto* order : level) {
            bid_qty += order->quantity;
            bid_value += order->quantity * price;
        }
    }
    
    count = 0;
    for (const auto& [price, level] : book.asks()) {
        if (count++ >= levels) break;
        for (const auto* order : level) {
            ask_qty += order->quantity;
            ask_value += order->quantity * price;
        }
    }
    
    // 一档不平衡
    double bid1 = book.bid_size_at(book.best_bid());
    double ask1 = book.bid_size_at(book.best_ask());
    metrics.bid_ask_imbalance = (bid1 - ask1) / (bid1 + ask1 + 1e-10);
    
    // 深度不平衡
    metrics.depth_imbalance = (bid_qty - ask_qty) / (bid_qty + ask_qty + 1e-10);
    
    // 加权中间价
    double best_bid = book.best_bid();
    double best_ask = book.best_ask();
    metrics.weighted_mid_price = 
        (best_bid * ask1 + best_ask * bid1) / (bid1 + ask1 + 1e-10);
    
    return metrics;
}
```

---

## 相关文章

- [OrderBook实现详解](@/articles/hft/hft-13-OrderBook实现详解.md)
- [交易所撮合引擎原理](@/articles/hft/hft-18-交易所撮合引擎原理.md)
- [HFT面试题-算法与数据结构](@/articles/hft/hft-23-HFT面试题-算法与数据结构.md)
