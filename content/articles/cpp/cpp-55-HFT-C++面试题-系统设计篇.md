+++
title = "55. Interview - System Design (HFT)"
date = 2026-01-21
description = "HFT系统设计C++面试题汇总，包括低延迟设计、内存管理、网络优化、架构设计等核心话题"
[taxonomies]
tags = ["C++", "面试题", "HFT", "系统设计", "低延迟"]
+++

## 一、低延迟设计

### Q1: 如何设计一个低延迟的订单处理系统？

```cpp
// 核心设计原则：

// 1. 预分配内存，避免运行时分配
class OrderProcessor {
    ObjectPool<Order> order_pool_;  // 预分配订单对象
    char* send_buffer_;             // 预分配发送缓冲区
    
public:
    OrderProcessor() {
        order_pool_.reserve(10000);
        send_buffer_ = static_cast<char*>(
            std::aligned_alloc(64, BUFFER_SIZE));
        mlock(send_buffer_, BUFFER_SIZE);  // 锁定内存
    }
};

// 2. 避免虚函数调用
template<typename Strategy>
class TradingEngine {
    Strategy strategy_;  // CRTP，编译期多态
    
    void onMarketData(const MarketData& data) {
        if (strategy_.shouldTrade(data)) {  // 可内联
            auto order = strategy_.generateOrder(data);
            sendOrder(order);
        }
    }
};

// 3. 使用无锁数据结构
SPSCQueue<MarketData> market_data_queue_;

// 4. CPU亲和性和隔离
void init() {
    setAffinity(4);  // 绑定到隔离的CPU核心
    setRealtimePriority();
}
```

### Q2: 如何测量和优化tick-to-trade延迟？

```cpp
class LatencyTracker {
    struct Timestamps {
        uint64_t market_data_recv;    // 接收行情
        uint64_t strategy_start;      // 策略开始
        uint64_t strategy_end;        // 策略结束
        uint64_t order_sent;          // 订单发送
    };
    
    RingBuffer<Timestamps, 10000> samples_;
    
public:
    void record(const Timestamps& ts) {
        samples_.push(ts);
    }
    
    void analyze() {
        // 计算各阶段延迟
        // P50, P99, P99.9, Max
        // 识别热点
    }
};

// 优化方法：
// 1. 使用RDTSC高精度计时
// 2. 分析各阶段占比
// 3. 优化最大延迟贡献者
// 4. 使用perf分析CPU开销
```

---

## 二、内存管理

### Q3: 设计一个低延迟的内存分配器

```cpp
template<typename T, size_t PoolSize>
class LowLatencyPool {
    struct alignas(64) Slot {
        T object;
        Slot* next;
    };
    
    alignas(64) char memory_[sizeof(Slot) * PoolSize];
    alignas(64) Slot* free_list_;
    
public:
    LowLatencyPool() {
        // 初始化空闲链表
        Slot* slots = reinterpret_cast<Slot*>(memory_);
        for (size_t i = 0; i < PoolSize - 1; ++i) {
            slots[i].next = &slots[i + 1];
        }
        slots[PoolSize - 1].next = nullptr;
        free_list_ = slots;
        
        // 预热和锁定内存
        warmup();
        mlock(memory_, sizeof(memory_));
    }
    
    T* allocate() noexcept {
        if (!free_list_) return nullptr;
        Slot* slot = free_list_;
        free_list_ = slot->next;
        return &slot->object;
    }
    
    void deallocate(T* ptr) noexcept {
        Slot* slot = reinterpret_cast<Slot*>(ptr);
        slot->next = free_list_;
        free_list_ = slot;
    }
    
private:
    void warmup() {
        // 触发所有页面的加载
        volatile char* p = memory_;
        for (size_t i = 0; i < sizeof(memory_); i += 4096) {
            p[i] = 0;
        }
    }
};
```

### Q4: 如何避免内存分配带来的延迟？

```cpp
// 1. 预分配策略
class PreallocatedSystem {
    std::vector<Order> orders_;  // 预分配
    std::vector<MarketData> market_data_;
    
public:
    PreallocatedSystem() {
        orders_.reserve(100000);
        market_data_.reserve(1000000);
    }
};

// 2. Arena分配器用于临时数据
class MessageProcessor {
    ArenaAllocator arena_{1024 * 1024};  // 1MB
    
public:
    void processMessage(const char* data) {
        // 使用arena分配临时对象
        auto* parsed = arena_.allocate<ParsedMessage>();
        parse(data, parsed);
        process(parsed);
        arena_.reset();  // 快速释放
    }
};

// 3. 复用对象
class ConnectionPool {
    std::vector<std::unique_ptr<Connection>> pool_;
    std::queue<Connection*> available_;
    
public:
    Connection* acquire() {
        if (available_.empty()) return nullptr;
        Connection* conn = available_.front();
        available_.pop();
        return conn;
    }
    
    void release(Connection* conn) {
        conn->reset();
        available_.push(conn);
    }
};
```

---

## 三、网络优化

### Q5: 如何设计低延迟的网络层？

```cpp
// 1. 使用kernel bypass（如DPDK）
class DPDKNetworkLayer {
public:
    void init() {
        rte_eal_init(argc, argv);
        // 配置PMD驱动
        // 分配mempool
    }
    
    void pollLoop() {
        while (running_) {
            // 轮询接收
            uint16_t nb_rx = rte_eth_rx_burst(port_id, queue_id,
                                              rx_pkts, MAX_PKT_BURST);
            for (uint16_t i = 0; i < nb_rx; ++i) {
                processPacket(rx_pkts[i]);
            }
        }
    }
};

// 2. 或使用优化的socket配置
void configureSocket(int sock) {
    // 禁用Nagle算法
    int flag = 1;
    setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));
    
    // 启用忙等待
    setsockopt(sock, SOL_SOCKET, SO_BUSY_POLL, &flag, sizeof(flag));
    
    // 使用非阻塞IO
    fcntl(sock, F_SETFL, O_NONBLOCK);
    
    // 设置缓冲区大小
    int bufsize = 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
}

// 3. 使用io_uring（Linux 5.1+）
class IOUringNetwork {
    struct io_uring ring_;
    
public:
    void init() {
        io_uring_queue_init(QUEUE_DEPTH, &ring_, 0);
    }
    
    void submitRead(int fd, void* buf, size_t len) {
        struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
        io_uring_prep_read(sqe, fd, buf, len, 0);
        io_uring_submit(&ring_);
    }
};
```

### Q6: 如何处理多个交易所的行情？

```cpp
class MultiExchangeHandler {
    // 每个交易所独立的处理线程
    struct ExchangeContext {
        int cpu_id;
        SPSCQueue<MarketData> queue;
        std::thread worker;
    };
    
    std::vector<ExchangeContext> exchanges_;
    
public:
    void start() {
        for (size_t i = 0; i < exchanges_.size(); ++i) {
            auto& ctx = exchanges_[i];
            ctx.worker = std::thread([this, &ctx]() {
                setAffinity(ctx.cpu_id);
                while (running_) {
                    MarketData data;
                    if (ctx.queue.pop(data)) {
                        processMarketData(data);
                    }
                }
            });
        }
    }
    
    void onMarketData(size_t exchange_id, const MarketData& data) {
        exchanges_[exchange_id].queue.push(data);
    }
};
```

---

## 四、数据结构设计

### Q7: 设计一个高效的订单簿

```cpp
class OrderBook {
    // 价格级别：使用数组而非map
    struct PriceLevel {
        int64_t price;
        int64_t total_quantity;
        int32_t order_count;
    };
    
    // 固定大小数组，按价格排序
    std::array<PriceLevel, MAX_LEVELS> bid_levels_;
    std::array<PriceLevel, MAX_LEVELS> ask_levels_;
    size_t bid_count_ = 0;
    size_t ask_count_ = 0;
    
public:
    // O(1) 获取最优价格
    int64_t getBestBid() const {
        return bid_count_ > 0 ? bid_levels_[0].price : 0;
    }
    
    int64_t getBestAsk() const {
        return ask_count_ > 0 ? ask_levels_[0].price : 0;
    }
    
    // 更新价格级别
    void updateLevel(Side side, int64_t price, int64_t quantity) {
        auto& levels = (side == Side::BUY) ? bid_levels_ : ask_levels_;
        auto& count = (side == Side::BUY) ? bid_count_ : ask_count_;
        
        // 二分查找位置
        auto it = std::lower_bound(
            levels.begin(), levels.begin() + count,
            price,
            [side](const PriceLevel& l, int64_t p) {
                return side == Side::BUY ? l.price > p : l.price < p;
            }
        );
        
        // 更新或插入
        // ...
    }
};
```

### Q8: 设计时间序列数据存储

```cpp
template<typename T, size_t WindowSize>
class TimeSeriesWindow {
    struct Entry {
        uint64_t timestamp;
        T value;
    };
    
    std::array<Entry, WindowSize> buffer_;
    size_t head_ = 0;
    size_t size_ = 0;
    
public:
    void add(uint64_t timestamp, const T& value) {
        buffer_[(head_ + size_) % WindowSize] = {timestamp, value};
        if (size_ < WindowSize) {
            ++size_;
        } else {
            head_ = (head_ + 1) % WindowSize;
        }
    }
    
    // 获取时间窗口内的统计
    T getAverage(uint64_t window_ns) const {
        uint64_t now = getCurrentTimestamp();
        T sum = T{};
        size_t count = 0;
        
        for (size_t i = 0; i < size_; ++i) {
            const auto& entry = buffer_[(head_ + i) % WindowSize];
            if (now - entry.timestamp <= window_ns) {
                sum += entry.value;
                ++count;
            }
        }
        
        return count > 0 ? sum / count : T{};
    }
};
```

---

## 五、系统架构

### Q9: HFT系统的典型架构？

```
┌─────────────────────────────────────────────────────────────┐
│                      Market Data Feed                        │
│  (Exchange A)     (Exchange B)     (Exchange C)              │
└──────┬───────────────┬───────────────┬──────────────────────┘
       │               │               │
       ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│              Network Layer (DPDK / io_uring)                 │
│              Hardware Timestamping                           │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Message Parser (Zero-copy)                      │
│              Protocol Handlers (FIX/FAST/ITCH)              │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Order Book Manager                              │
│              Market Data Aggregator                          │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Strategy Engine                                 │
│              Signal Generation                               │
│              Risk Checks                                     │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Order Management System                         │
│              Position Tracking                               │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Network Layer (Order Sending)                   │
└─────────────────────────────────────────────────────────────┘
```

### Q10: 如何保证系统的可靠性？

```cpp
// 1. 热备份
class FailoverSystem {
    std::atomic<bool> is_primary_{true};
    HeartbeatMonitor heartbeat_;
    
public:
    void run() {
        if (is_primary_) {
            heartbeat_.sendHeartbeat();
            processOrders();
        } else {
            if (!heartbeat_.receivedRecently()) {
                becomePrimary();
            }
        }
    }
};

// 2. 订单恢复
class OrderRecovery {
    PersistentLog<Order> order_log_;
    
public:
    void onOrderSent(const Order& order) {
        order_log_.append(order);
    }
    
    void recover() {
        // 读取日志，重建状态
        for (const auto& order : order_log_) {
            if (!order.isComplete()) {
                queryExchangeStatus(order);
            }
        }
    }
};

// 3. 限制和熔断
class RiskManager {
    std::atomic<int> orders_per_second_{0};
    std::atomic<int64_t> position_{0};
    
public:
    bool checkPreTrade(const Order& order) {
        if (orders_per_second_ > MAX_ORDERS_PER_SECOND) return false;
        if (position_ + order.quantity > MAX_POSITION) return false;
        return true;
    }
};
```

---

## 面试技巧

1. **延迟来源**：列举内存分配、系统调用、锁竞争等
2. **优化手段**：预分配、无锁、CPU绑定、kernel bypass
3. **权衡取舍**：延迟vs吞吐量、复杂度vs性能
4. **故障处理**：热备份、订单恢复、风险控制
5. **测量方法**：RDTSC、延迟分布、perf分析
