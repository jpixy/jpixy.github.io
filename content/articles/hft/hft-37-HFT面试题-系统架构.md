+++
title = "37.HFT面试题-系统架构"
date = 2026-01-31
description = "HFT系统架构面试题：整体架构设计、延迟预算、组件设计、容错与监控深度解析"
[taxonomies]
tags = ["HFT", "面试", "系统架构", "延迟预算", "低延迟"]
+++

# HFT 面试题 - 系统架构

本文汇集 HFT（高频交易）系统架构相关的高频面试问题，采用问答深挖形式，模拟真实面试场景。

---

## 问题 1：描述典型的 HFT 系统架构

### 标准答案

```
典型 HFT 系统架构：

┌─────────────────────────────────────────────────────────────────┐
│                        交易所 / 市场                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ 交易所 A     │    │ 交易所 B     │    │ 暗池         │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
└─────────┼───────────────────┼───────────────────┼───────────────┘
          │ UDP Multicast     │ TCP               │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      网络层 (< 1μs)                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  NIC (Solarflare/Mellanox) + Kernel Bypass (DPDK/Onload) │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    市场数据处理 (< 5μs)                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ Feed       │  │ 协议解析   │  │ 规范化     │                │
│  │ Handler    │→ │ (ITCH/OUCH)│→ │ Normalizer │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    订单簿管理 (< 2μs)                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Order Book Engine (无锁数据结构，缓存优化)             │    │
│  │  - L1/L2/L3 价格层级                                   │    │
│  │  - 增量更新                                            │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    策略引擎 (< 5μs)                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │ 信号生成   │  │ 风险检查   │  │ 订单生成   │                │
│  │ Signal Gen │→ │ Risk Check │→ │ Order Gen  │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    订单管理 (< 2μs)                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Order Management System (OMS)                         │    │
│  │  - 订单状态跟踪                                        │    │
│  │  - 成交确认                                            │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    网关层 (< 1μs)                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Order Gateway (协议编码 → 发送)                        │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
        交易所
```

**关键组件职责**：

| 组件 | 职责 | 延迟目标 |
|------|------|----------|
| Feed Handler | 接收市场数据 | < 1μs |
| Protocol Parser | 解析交易所协议 | < 2μs |
| Order Book | 维护价格层级 | < 2μs |
| Strategy Engine | 决策与信号生成 | < 5μs |
| Risk Manager | 风控检查 | < 1μs |
| Order Gateway | 订单发送 | < 1μs |

### 面试官追问

**Q1: 为什么要使用内核旁路（Kernel Bypass）？**

```
传统网络栈延迟分解：
┌─────────────────────────────────────────┐
│ 应用层                                   │
│     ↓ ~100-200ns (系统调用)              │
│ Socket 层                               │
│     ↓ ~1-5μs (协议栈处理)                │
│ TCP/IP 栈                               │
│     ↓ ~100ns (内核调度)                  │
│ 设备驱动                                 │
│     ↓ ~2-10μs (中断处理)                 │
│ NIC                                     │
└─────────────────────────────────────────┘
总延迟：10-50μs

内核旁路（DPDK/Onload）：
┌─────────────────────────────────────────┐
│ 应用层                                   │
│     ↓ 直接访问（无系统调用）              │
│ 用户态驱动 (PMD)                         │
│     ↓ 轮询（无中断）                     │
│ NIC                                     │
└─────────────────────────────────────────┘
总延迟：< 1μs

优势：
- 消除系统调用开销
- 消除中断开销
- 消除数据拷贝
- 消除上下文切换
```

**Q2: Feed Handler 如何保证低延迟？**

```c++
// Feed Handler 设计要点

class FeedHandler {
    // 1. 使用内核旁路
    DPDKPort port;
    
    // 2. 预分配所有内存
    alignas(64) char recv_buffer[MAX_PACKET_SIZE];
    MessagePool<MarketData> msg_pool{100000};
    
    // 3. CPU 绑定
    void init() {
        bind_to_cpu(FEED_HANDLER_CPU);
        mlockall(MCL_CURRENT | MCL_FUTURE);
    }
    
    // 4. 轮询模式（无中断）
    void run() {
        while (running) {
            // 批量接收
            int n = port.recv_burst(packets, BURST_SIZE);
            
            for (int i = 0; i < n; i++) {
                // 预取下一个包
                if (i + 1 < n) {
                    __builtin_prefetch(packets[i + 1].data);
                }
                
                // 解析并分发
                process_packet(packets[i]);
            }
        }
    }
    
    // 5. 零拷贝处理
    void process_packet(Packet& pkt) {
        // 直接在 DMA 缓冲区解析，避免拷贝
        auto* msg = parser.parse_in_place(pkt.data, pkt.len);
        
        // 使用无锁队列发布
        output_queue.push(msg);
    }
};
```

**Q3: 如何设计高性能订单簿？**

```c++
// 高性能订单簿设计

// 1. 价格层级使用数组（L1/L2 热点数据）
struct alignas(64) PriceLevel {
    int64_t price;
    int64_t total_qty;
    int32_t order_count;
    int32_t padding;
};

// 2. 订单使用侵入式链表（避免分配）
struct Order {
    int64_t order_id;
    int64_t price;
    int32_t qty;
    int32_t remaining;
    Order* prev;
    Order* next;
};

class OrderBook {
    // 固定大小的价格层级数组
    static constexpr int MAX_LEVELS = 100;
    PriceLevel bid_levels[MAX_LEVELS];
    PriceLevel ask_levels[MAX_LEVELS];
    
    // 订单池（预分配）
    ObjectPool<Order> order_pool{1000000};
    
    // 订单查找（O(1)）
    robin_hood::unordered_flat_map<int64_t, Order*> order_map;
    
public:
    // 添加订单：O(1) 平均
    void add_order(int64_t id, int64_t price, int32_t qty, Side side) {
        Order* order = order_pool.acquire();
        order->order_id = id;
        order->price = price;
        order->qty = qty;
        order->remaining = qty;
        
        // 更新价格层级
        auto& levels = (side == Side::BID) ? bid_levels : ask_levels;
        int idx = price_to_index(price, side);
        levels[idx].total_qty += qty;
        levels[idx].order_count++;
        
        // 加入链表
        insert_to_level(order, idx, side);
        
        // 加入查找表
        order_map[id] = order;
    }
    
    // 取消订单：O(1)
    void cancel_order(int64_t id) {
        auto it = order_map.find(id);
        if (it == order_map.end()) return;
        
        Order* order = it->second;
        // 更新价格层级
        // 从链表移除
        // 返还到池
        order_map.erase(it);
        order_pool.release(order);
    }
    
    // 获取 BBO：O(1)
    BBO get_bbo() const {
        return {
            bid_levels[0].price,
            bid_levels[0].total_qty,
            ask_levels[0].price,
            ask_levels[0].total_qty
        };
    }
};
```

---

## 问题 2：什么是延迟预算（Latency Budget）？如何分配？

### 标准答案

**延迟预算**：将端到端延迟目标分解到各个组件，确保整体延迟可控。

```
典型 HFT 延迟预算（Tick-to-Trade < 20μs）：

┌──────────────────────────────────────────────────────────────┐
│                     端到端延迟 < 20μs                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ 网络    │  │ 解析    │  │ 订单簿  │  │ 策略    │        │
│  │ 接收    │→ │ 处理    │→ │ 更新    │→ │ 决策    │        │
│  │ < 1μs   │  │ < 2μs   │  │ < 2μs   │  │ < 5μs   │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │
│  │ 风控    │  │ 订单    │  │ 网络    │                     │
│  │ 检查    │→ │ 编码    │→ │ 发送    │                     │
│  │ < 1μs   │  │ < 1μs   │  │ < 1μs   │                     │
│  └─────────┘  └─────────┘  └─────────┘                     │
│                                                              │
│  缓冲/队列开销：< 3μs                                        │
│  抖动余量：< 4μs                                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**延迟预算分配原则**：

| 原则 | 说明 |
|------|------|
| 关键路径优先 | 交易决策路径延迟最小化 |
| 留有余量 | 预留 20-30% 应对抖动 |
| 可测量 | 每个组件有独立的时间戳 |
| 可追溯 | 超时能定位到具体组件 |

### 面试官追问

**Q1: 如何测量各组件延迟？**

```c++
// 高精度时间戳

// 1. 使用 RDTSC（最低开销）
inline uint64_t rdtsc() {
    uint32_t lo, hi;
    asm volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

// 校准 TSC 频率
uint64_t calibrate_tsc() {
    auto start = std::chrono::high_resolution_clock::now();
    uint64_t tsc_start = rdtsc();
    
    usleep(100000);  // 100ms
    
    auto end = std::chrono::high_resolution_clock::now();
    uint64_t tsc_end = rdtsc();
    
    auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
        end - start).count();
    return (tsc_end - tsc_start) * 1000000000ULL / ns;
}

// 2. 延迟测量框架
class LatencyTracker {
    static constexpr int STAGES = 8;
    
    struct Timestamps {
        uint64_t ts[STAGES];
    };
    
    // 每条消息携带时间戳
    thread_local static Timestamps current;
    
public:
    static void mark(int stage) {
        current.ts[stage] = rdtsc();
    }
    
    static void report() {
        uint64_t freq = tsc_freq;
        for (int i = 1; i < STAGES; i++) {
            uint64_t delta = current.ts[i] - current.ts[i-1];
            uint64_t ns = delta * 1000000000ULL / freq;
            printf("Stage %d->%d: %lu ns\n", i-1, i, ns);
        }
    }
};

// 使用
void process_message(Message& msg) {
    LatencyTracker::mark(0);  // 接收
    
    parse(msg);
    LatencyTracker::mark(1);  // 解析完成
    
    update_orderbook(msg);
    LatencyTracker::mark(2);  // 订单簿更新
    
    auto signal = strategy.evaluate();
    LatencyTracker::mark(3);  // 策略决策
    
    if (signal) {
        risk_check(signal);
        LatencyTracker::mark(4);  // 风控
        
        send_order(signal);
        LatencyTracker::mark(5);  // 发送
    }
    
    LatencyTracker::report();
}
```

**Q2: 如何处理延迟抖动（Jitter）？**

```
延迟抖动来源及解决方案：

1. CPU 相关
   来源：上下文切换、中断、功耗调节
   解决：
   - isolcpus 隔离 CPU
   - nohz_full 禁用定时器
   - 禁用 C-States 和 P-States
   - 禁用超线程

2. 内存相关
   来源：TLB miss、缺页、NUMA 远程访问
   解决：
   - 使用大页
   - mlock 锁定内存
   - NUMA 本地绑定
   - 内存预热

3. 内核相关
   来源：内核任务、软中断、RCU
   解决：
   - rcu_nocbs 卸载 RCU
   - 禁用 irqbalance
   - 中断亲和性设置

4. 应用相关
   来源：内存分配、锁竞争、GC
   解决：
   - 预分配所有内存
   - 无锁编程
   - 避免使用带 GC 的语言

5. 网络相关
   来源：中断合并、缓冲区溢出
   解决：
   - 禁用中断合并
   - 调整 ring buffer
   - 使用内核旁路
```

**Q3: 什么是尾延迟（Tail Latency）？如何优化？**

```
尾延迟 = P99/P99.9/P99.99 延迟

问题：
- 平均延迟 10μs
- P99 延迟 100μs（10 倍！）
- P99.99 延迟 1ms（100 倍！）

在 HFT 中，尾延迟可能意味着：
- 错失交易机会
- 被其他交易者抢先

分析方法：
1. 延迟直方图
2. 抖动分布图
3. 时间序列相关性

代码示例：
```

```c++
class LatencyHistogram {
    static constexpr int BUCKETS = 1000;  // 1ns 精度
    uint64_t counts[BUCKETS] = {0};
    uint64_t overflow = 0;
    uint64_t total = 0;
    
public:
    void record(uint64_t latency_ns) {
        if (latency_ns < BUCKETS) {
            counts[latency_ns]++;
        } else {
            overflow++;
        }
        total++;
    }
    
    uint64_t percentile(double p) const {
        uint64_t target = (uint64_t)(total * p);
        uint64_t cumulative = 0;
        
        for (int i = 0; i < BUCKETS; i++) {
            cumulative += counts[i];
            if (cumulative >= target) {
                return i;
            }
        }
        return BUCKETS;  // overflow
    }
    
    void report() const {
        printf("P50: %lu ns\n", percentile(0.50));
        printf("P90: %lu ns\n", percentile(0.90));
        printf("P99: %lu ns\n", percentile(0.99));
        printf("P99.9: %lu ns\n", percentile(0.999));
        printf("P99.99: %lu ns\n", percentile(0.9999));
    }
};
```

```
优化尾延迟的方法：

1. 消除周期性抖动
   - 定位周期（10ms=内核 tick，1s=日志刷新）
   - 移除或异步化周期性任务

2. 预热关键路径
   - 启动时执行虚拟交易
   - 触发所有分支
   - 加载所有数据到缓存

3. 冗余处理
   - 关键计算并行执行
   - 使用最快完成的结果

4. 提前终止
   - 设置超时
   - 超时后使用备用策略
```

---

## 问题 3：如何设计策略引擎？

### 标准答案

```c++
// 策略引擎设计

// 1. 策略接口
class Strategy {
public:
    virtual ~Strategy() = default;
    
    // 接收市场数据更新
    virtual void on_market_data(const MarketData& md) = 0;
    
    // 接收订单更新
    virtual void on_order_update(const OrderUpdate& update) = 0;
    
    // 获取待发送订单
    virtual std::span<Order> get_pending_orders() = 0;
};

// 2. 做市策略示例
class MarketMakingStrategy : public Strategy {
    // 预分配订单缓冲
    Order pending_orders[MAX_PENDING];
    int pending_count = 0;
    
    // 策略参数
    double spread_bps = 1.0;
    double skew_factor = 0.5;
    int max_position = 1000;
    
    // 状态
    int position = 0;
    double theo_price = 0;
    
    // 订单簿引用
    const OrderBook& book;
    
public:
    void on_market_data(const MarketData& md) override {
        // 1. 更新理论价格
        update_theo_price(md);
        
        // 2. 计算报价
        auto [bid_price, ask_price] = calculate_quotes();
        
        // 3. 检查是否需要更新订单
        if (should_update_quotes(bid_price, ask_price)) {
            // 4. 生成取消/新订单
            generate_quote_updates(bid_price, ask_price);
        }
    }
    
private:
    void update_theo_price(const MarketData& md) {
        // 微价格模型
        double bid = book.best_bid();
        double ask = book.best_ask();
        double bid_size = book.bid_size(0);
        double ask_size = book.ask_size(0);
        
        double imbalance = bid_size / (bid_size + ask_size);
        theo_price = bid + (ask - bid) * imbalance;
    }
    
    std::pair<double, double> calculate_quotes() {
        // 基础价差
        double half_spread = theo_price * spread_bps / 10000 / 2;
        
        // 仓位偏移（持仓多时卖价更激进）
        double skew = position * skew_factor / max_position * half_spread;
        
        double bid_price = theo_price - half_spread + skew;
        double ask_price = theo_price + half_spread + skew;
        
        return {bid_price, ask_price};
    }
};
```

### 面试官追问

**Q1: 如何实现热路径优化？**

```c++
// 热路径优化技术

// 1. 避免虚函数调用（使用 CRTP）
template<typename Derived>
class StrategyBase {
public:
    void on_market_data(const MarketData& md) {
        static_cast<Derived*>(this)->on_market_data_impl(md);
    }
};

class FastStrategy : public StrategyBase<FastStrategy> {
public:
    // 编译时确定，无虚函数开销
    void on_market_data_impl(const MarketData& md) {
        // ...
    }
};

// 2. 分支预测优化
inline void process_update(const MarketData& md) {
    // 大多数更新不触发交易
    if (unlikely(should_trade(md))) {
        execute_trade(md);
    }
}

// 3. 内联关键计算
__attribute__((always_inline))
inline double calculate_theo(double bid, double ask, 
                            double bid_size, double ask_size) {
    double imbalance = bid_size / (bid_size + ask_size);
    return bid + (ask - bid) * imbalance;
}

// 4. SIMD 批量计算
void calculate_signals_simd(const double* prices, 
                           const double* factors,
                           double* signals, int n) {
    for (int i = 0; i < n; i += 4) {
        __m256d p = _mm256_load_pd(&prices[i]);
        __m256d f = _mm256_load_pd(&factors[i]);
        __m256d s = _mm256_mul_pd(p, f);
        _mm256_store_pd(&signals[i], s);
    }
}

// 5. 预计算查表
class PriceTable {
    // 预计算价格层级
    double tick_prices[10000];
    
public:
    PriceTable() {
        for (int i = 0; i < 10000; i++) {
            tick_prices[i] = base_price + i * tick_size;
        }
    }
    
    double get_price(int tick_index) const {
        return tick_prices[tick_index];  // O(1)
    }
};
```

**Q2: 如何设计风控系统？**

```c++
// 低延迟风控设计

class RiskManager {
    // 预设限制（编译时常量）
    static constexpr int MAX_ORDER_SIZE = 10000;
    static constexpr int MAX_POSITION = 100000;
    static constexpr int MAX_ORDERS_PER_SEC = 1000;
    static constexpr double MAX_NOTIONAL = 10000000.0;
    
    // 运行时状态（缓存行对齐）
    alignas(64) struct State {
        std::atomic<int> position{0};
        std::atomic<int> orders_this_second{0};
        std::atomic<double> notional{0};
        std::atomic<int64_t> current_second{0};
    } state;
    
public:
    // 快速风控检查（< 100ns）
    __attribute__((always_inline))
    bool check(const Order& order) {
        // 1. 订单大小检查
        if (unlikely(order.qty > MAX_ORDER_SIZE)) {
            return false;
        }
        
        // 2. 仓位检查
        int new_pos = state.position.load(std::memory_order_relaxed);
        if (order.side == Side::BUY) {
            new_pos += order.qty;
        } else {
            new_pos -= order.qty;
        }
        if (unlikely(std::abs(new_pos) > MAX_POSITION)) {
            return false;
        }
        
        // 3. 频率检查（每秒重置）
        update_second();
        int orders = state.orders_this_second.fetch_add(
            1, std::memory_order_relaxed);
        if (unlikely(orders >= MAX_ORDERS_PER_SEC)) {
            return false;
        }
        
        // 4. 名义金额检查
        double notional = order.price * order.qty;
        double total = state.notional.fetch_add(
            notional, std::memory_order_relaxed);
        if (unlikely(total + notional > MAX_NOTIONAL)) {
            state.notional.fetch_sub(notional, std::memory_order_relaxed);
            return false;
        }
        
        return true;
    }
    
private:
    void update_second() {
        int64_t now = current_time_seconds();
        int64_t prev = state.current_second.load(std::memory_order_relaxed);
        if (now != prev) {
            if (state.current_second.compare_exchange_strong(
                    prev, now, std::memory_order_relaxed)) {
                state.orders_this_second.store(0, std::memory_order_relaxed);
                state.notional.store(0, std::memory_order_relaxed);
            }
        }
    }
};
```

---

## 问题 4：如何实现高可用和容错？

### 标准答案

```
HFT 高可用架构：

┌─────────────────────────────────────────────────────────────┐
│                     主数据中心                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ 主交易节点  │←──→│ 备交易节点  │←──→│ 仲裁节点    │    │
│  │ (Active)    │    │ (Standby)   │    │ (Arbiter)   │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         ↓                  ↓                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              状态同步层 (< 10μs)                      │  │
│  │         共享内存 / RDMA / Replicated Log             │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │
         │ 异地复制
         ↓
┌─────────────────────────────────────────────────────────────┐
│                     灾备数据中心                             │
│  ┌─────────────┐                                           │
│  │ 灾备节点    │                                           │
│  │ (DR)        │                                           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

**故障切换策略**：

| 场景 | 切换时间 | 策略 |
|------|----------|------|
| 进程崩溃 | < 1ms | Watchdog 自动重启 |
| 网络断开 | < 10ms | 备节点接管 |
| 服务器宕机 | < 100ms | 硬件仲裁 + 切换 |
| 数据中心故障 | < 1s | 灾备接管 |

### 面试官追问

**Q1: 如何实现低延迟的状态同步？**

```c++
// 状态同步方案

// 方案 1：共享内存（同机房）
class SharedStateManager {
    // 映射共享内存
    void* shm = mmap_shared("/hft_state", STATE_SIZE);
    
    // 状态结构
    struct SharedState {
        std::atomic<uint64_t> version;
        std::atomic<int> position;
        std::atomic<double> pnl;
        // ...
    };
    
    SharedState* state = static_cast<SharedState*>(shm);
    
public:
    // 原子更新（主节点）
    void update_position(int delta) {
        state->position.fetch_add(delta, std::memory_order_release);
        state->version.fetch_add(1, std::memory_order_release);
    }
    
    // 读取（备节点）
    int get_position() {
        return state->position.load(std::memory_order_acquire);
    }
};

// 方案 2：复制日志（Replicated Log）
class ReplicatedLog {
    struct LogEntry {
        uint64_t sequence;
        uint64_t timestamp;
        uint8_t type;
        uint8_t data[55];  // 填充到 64 字节
    };
    
    // 环形缓冲区
    alignas(64) LogEntry log[LOG_SIZE];
    std::atomic<uint64_t> head{0};
    
    // RDMA 发布
    RDMAConnection backup_conn;
    
public:
    void append(const LogEntry& entry) {
        uint64_t pos = head.fetch_add(1, std::memory_order_relaxed);
        log[pos % LOG_SIZE] = entry;
        
        // RDMA 写到备节点（异步，不阻塞）
        backup_conn.write_async(&log[pos % LOG_SIZE], 
                               backup_log_addr + (pos % LOG_SIZE) * 64,
                               sizeof(LogEntry));
    }
};

// 方案 3：事件溯源（Event Sourcing）
// 不同步状态，只同步事件
// 备节点通过回放事件重建状态
class EventStore {
    std::vector<Event> events;
    
    void publish(const Event& e) {
        events.push_back(e);
        broadcast_to_replicas(e);
    }
    
    State rebuild() {
        State s;
        for (const auto& e : events) {
            s.apply(e);
        }
        return s;
    }
};
```

**Q2: 如何检测和处理网络分区？**

```c++
// 网络分区检测（脑裂防护）

class SplitBrainProtector {
    // 心跳检测
    std::atomic<int64_t> last_heartbeat{0};
    
    // 仲裁服务
    QuorumService quorum;
    
    // 交易所连接状态
    std::atomic<bool> exchange_connected{true};
    
public:
    enum class Role { PRIMARY, STANDBY, ISOLATED };
    
    Role determine_role() {
        // 1. 检查交易所连接
        if (!exchange_connected.load()) {
            return Role::ISOLATED;  // 无法交易
        }
        
        // 2. 检查心跳
        int64_t now = current_time_ms();
        int64_t last = last_heartbeat.load();
        if (now - last > HEARTBEAT_TIMEOUT_MS) {
            // 对方可能挂了，询问仲裁
            return query_quorum();
        }
        
        return current_role;
    }
    
    Role query_quorum() {
        // 向仲裁服务请求
        // 仲裁确保只有一个 PRIMARY
        QuorumDecision decision = quorum.request_leadership(node_id);
        
        if (decision == QuorumDecision::GRANTED) {
            return Role::PRIMARY;
        } else if (decision == QuorumDecision::DENIED) {
            return Role::STANDBY;
        } else {
            // 仲裁不可达
            return Role::ISOLATED;
        }
    }
    
    void on_role_change(Role new_role) {
        if (new_role == Role::PRIMARY) {
            start_trading();
        } else {
            stop_trading();
            // 主动取消所有挂单
            cancel_all_orders();
        }
    }
};
```

---

## 问题 5：如何设计监控和告警系统？

### 标准答案

```
HFT 监控架构：

┌─────────────────────────────────────────────────────────────┐
│                    交易系统                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  内置指标采集器 (无锁、无分配)                        │   │
│  │  - 延迟直方图                                        │   │
│  │  - 吞吐量计数器                                      │   │
│  │  - 错误计数器                                        │   │
│  └──────────────────────┬──────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │ 共享内存 / UDP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    监控代理（独立进程）                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 指标聚合    │  │ 告警评估    │  │ 日志收集    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    告警与可视化                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Prometheus  │  │ Grafana     │  │ PagerDuty   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

**关键监控指标**：

| 类别 | 指标 | 告警阈值 |
|------|------|----------|
| 延迟 | P99 tick-to-trade | > 50μs |
| 延迟 | 延迟抖动 | > 20μs |
| 吞吐 | 消息处理速率 | < 100k/s |
| 可靠性 | 丢包率 | > 0.01% |
| 仓位 | 净仓位 | > 限额 80% |
| 资金 | PnL | 亏损 > 阈值 |
| 系统 | CPU 使用率 | < 50%（留余量）|
| 系统 | 内存使用 | > 80% |

### 面试官追问

**Q1: 如何实现零开销的指标采集？**

```c++
// 零开销指标采集

// 1. 无锁计数器
class AtomicCounter {
    alignas(64) std::atomic<uint64_t> value{0};
    
public:
    void increment() {
        value.fetch_add(1, std::memory_order_relaxed);
    }
    
    uint64_t get() const {
        return value.load(std::memory_order_relaxed);
    }
};

// 2. 无锁延迟直方图（预分配桶）
class LockFreeHistogram {
    static constexpr int BUCKETS = 1000;  // 0-999μs
    alignas(64) std::atomic<uint64_t> buckets[BUCKETS];
    alignas(64) std::atomic<uint64_t> overflow{0};
    
public:
    void record(uint64_t latency_us) {
        if (latency_us < BUCKETS) {
            buckets[latency_us].fetch_add(1, std::memory_order_relaxed);
        } else {
            overflow.fetch_add(1, std::memory_order_relaxed);
        }
    }
    
    // 采集器读取（不影响热路径）
    void snapshot(uint64_t* out) const {
        for (int i = 0; i < BUCKETS; i++) {
            out[i] = buckets[i].load(std::memory_order_relaxed);
        }
    }
};

// 3. 采样而非全量
class SampledMetrics {
    std::atomic<uint64_t> counter{0};
    static constexpr uint64_t SAMPLE_RATE = 100;  // 1%
    
    LockFreeHistogram histogram;
    
public:
    void record_if_sampled(uint64_t latency) {
        uint64_t c = counter.fetch_add(1, std::memory_order_relaxed);
        if (c % SAMPLE_RATE == 0) {
            histogram.record(latency);
        }
    }
};

// 4. 共享内存导出（监控进程读取）
class MetricsExporter {
    struct SharedMetrics {
        AtomicCounter message_count;
        AtomicCounter error_count;
        LockFreeHistogram latency;
        // ...
    };
    
    SharedMetrics* metrics;
    
public:
    MetricsExporter() {
        int fd = shm_open("/hft_metrics", O_CREAT | O_RDWR, 0666);
        ftruncate(fd, sizeof(SharedMetrics));
        metrics = static_cast<SharedMetrics*>(
            mmap(nullptr, sizeof(SharedMetrics), 
                 PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0));
    }
    
    SharedMetrics& get() { return *metrics; }
};
```

**Q2: 如何实现实时告警而不影响交易？**

```c++
// 异步告警系统

class AlertSystem {
    // 无锁告警队列
    SPSCQueue<Alert, 10000> alert_queue;
    
    // 告警线程（独立 CPU）
    std::thread alert_thread;
    
public:
    // 热路径调用（非阻塞）
    void raise_alert(AlertType type, const char* msg) {
        Alert alert{type, msg, current_time_ns()};
        
        // 尝试入队，如果满了就丢弃（不阻塞交易）
        bool ok = alert_queue.try_push(alert);
        if (!ok) {
            // 可选：增加丢弃计数
            dropped_alerts.fetch_add(1, std::memory_order_relaxed);
        }
    }
    
private:
    void alert_worker() {
        // 绑定到非关键 CPU
        bind_to_cpu(ALERT_CPU);
        
        while (running) {
            Alert alert;
            if (alert_queue.try_pop(alert)) {
                // 发送告警（可能阻塞，没关系）
                send_to_pagerduty(alert);
                write_to_log(alert);
            } else {
                // 空闲时睡眠
                usleep(1000);
            }
        }
    }
};

// 条件告警（避免告警风暴）
class ThrottledAlert {
    std::atomic<int64_t> last_alert_time{0};
    static constexpr int64_t MIN_INTERVAL_NS = 1000000000;  // 1秒
    
public:
    bool should_alert() {
        int64_t now = current_time_ns();
        int64_t last = last_alert_time.load(std::memory_order_relaxed);
        
        if (now - last < MIN_INTERVAL_NS) {
            return false;
        }
        
        return last_alert_time.compare_exchange_strong(
            last, now, std::memory_order_relaxed);
    }
};
```

---

## 问题 6：如何进行系统调优？

### 标准答案

```bash
# HFT 系统调优清单

# === 1. 内核参数 ===

# 禁用透明大页
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# 预留大页
echo 4096 > /proc/sys/vm/nr_hugepages

# 禁用 swap
swapoff -a

# 网络参数
sysctl -w net.core.busy_read=50
sysctl -w net.core.busy_poll=50
sysctl -w net.core.netdev_budget=600
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728

# === 2. GRUB 参数 ===
# /etc/default/grub
GRUB_CMDLINE_LINUX="isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7 \
intel_pstate=disable processor.max_cstate=0 idle=poll \
transparent_hugepage=never audit=0 nosoftlockup"

# === 3. CPU 调优 ===

# 禁用超线程（BIOS 或运行时）
for cpu in /sys/devices/system/cpu/cpu*/online; do
    core_id=$(cat ${cpu%/online}/topology/core_id)
    # 禁用逻辑核
done

# 禁用 C-States
for cpu in /sys/devices/system/cpu/cpu*/cpuidle/state*/disable; do
    echo 1 > $cpu
done

# 设置性能模式
for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > $gov
done

# === 4. 中断调优 ===

# 禁用 irqbalance
systemctl stop irqbalance
systemctl disable irqbalance

# 设置网卡中断亲和性
echo 2 > /proc/irq/<eth0_irq>/smp_affinity

# 禁用网卡中断合并
ethtool -C eth0 rx-usecs 0 tx-usecs 0 rx-frames 1 tx-frames 1

# === 5. 网卡调优 ===

# 增加 ring buffer
ethtool -G eth0 rx 4096 tx 4096

# 禁用卸载功能（减少延迟）
ethtool -K eth0 gro off gso off tso off lro off

# 设置队列数
ethtool -L eth0 combined 8
```

### 面试官追问

**Q1: 如何验证调优效果？**

```bash
# 1. 测量基线延迟
# 使用 sockperf 或自定义工具
sockperf ping-pong -i <server_ip> -p 12345 --tcp

# 2. 检查 CPU 隔离
cat /sys/devices/system/cpu/isolated
# 应该显示隔离的 CPU 列表

# 3. 检查中断分布
watch -n 1 "cat /proc/interrupts | grep eth0"
# 中断应该只在指定 CPU

# 4. 检查 C-State 使用
turbostat --show Core,CPU,Busy%,Bzy_MHz,PkgWatt,C1,C6 \
    --interval 1

# 5. 检查调度延迟
# 使用 cyclictest
cyclictest -p 99 -t 1 -a 2 -i 100 -n -m -d 0

# 6. 检查网络延迟
# 使用硬件时间戳
ethtool -T eth0
# 使用 PTP 测量单向延迟

# 7. 检查 TLB miss
perf stat -e dTLB-load-misses,dTLB-loads ./trading_app

# 8. 检查缓存效率
perf stat -e cache-misses,cache-references ./trading_app
```

**Q2: 常见的调优陷阱有哪些？**

```
1. 过度隔离 CPU
   问题：系统 CPU 不足，内核任务饥饿
   症状：软中断延迟增加
   解决：保留足够 CPU 给系统

2. 禁用所有电源管理
   问题：CPU 温度过高，降频
   症状：突发性能下降
   解决：监控温度，确保散热

3. 错误的 NUMA 配置
   问题：跨节点内存访问
   症状：延迟抖动大
   解决：使用 numactl 验证

4. 网卡队列配置不当
   问题：流量集中在单队列
   症状：单核 CPU 100%
   解决：正确配置 RSS/RFS

5. 忽略应用层优化
   问题：只调内核，不优化代码
   症状：调优效果有限
   解决：应用层和系统层同时优化

6. 测试环境与生产不一致
   问题：测试结果不可复现
   症状：生产延迟比测试高
   解决：使用相同硬件和配置
```

---

## 高频考点总结

| 考点 | 频率 | 深度要求 |
|------|------|----------|
| 系统架构 | ★★★ | 组件职责、数据流 |
| 延迟预算 | ★★★ | 分配原则、测量方法 |
| 订单簿设计 | ★★★ | 数据结构、性能优化 |
| 策略引擎 | ★★☆ | 热路径优化 |
| 风控系统 | ★★★ | 低延迟检查 |
| 高可用设计 | ★★☆ | 故障切换、状态同步 |
| 监控告警 | ★★☆ | 零开销采集 |
| 系统调优 | ★★★ | 内核参数、验证方法 |

---

## 相关文章

- [上一篇：HFT笔试题-SIMD与向量化](/articles/hft/hft-36-HFT笔试题-SIMD与向量化/)
