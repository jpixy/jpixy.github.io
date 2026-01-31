+++
title = "16.HFT面试题-系统设计"
slug = "hft-16-HFT面试题-系统设计"
date = 2026-01-21
description = "HFT系统设计面试题，包括交易系统架构、延迟优化、容错设计和市场数据处理"
[taxonomies]
tags = ["HFT", "面试", "系统设计", "架构", "低延迟"]
+++

## 一、交易系统架构

### Q1: 设计一个低延迟交易系统

**问题**：请设计一个端到端延迟在10微秒以内的交易系统架构。

**答案框架**：

```
1. 高层架构
┌─────────────────────────────────────────────────────────────┐
│  Market Data Feed                                            │
│         ↓ (Kernel Bypass / FPGA)                            │
│  ┌─────────────────┐                                         │
│  │ Market Data     │ → Shared Memory → Strategy Engine      │
│  │ Handler         │              ↘                          │
│  └─────────────────┘               Order Book                │
│                                          ↓                   │
│  ┌─────────────────┐    ← Shared Memory ←                   │
│  │ Order Gateway   │                                         │
│  └─────────────────┘                                         │
│         ↓ (Kernel Bypass)                                    │
│  Exchange                                                    │
└─────────────────────────────────────────────────────────────┘

2. 关键设计决策：
- 网络：使用DPDK/Solarflare绕过内核
- 进程间通信：共享内存，避免序列化
- 数据结构：预分配、缓存对齐
- 线程模型：CPU亲和性，busy polling
- 内存：大页、NUMA感知

3. 延迟分解（目标10μs）：
- Wire to NIC: 0.5μs
- NIC to App: 1μs (Kernel Bypass)
- Parsing: 0.5μs
- Strategy: 2μs
- Order Gen: 0.5μs
- App to NIC: 1μs
- NIC to Wire: 0.5μs
- Buffer: 4μs
```

### Q2: 如何处理市场数据的高吞吐量？

**问题**：设计一个每秒处理1000万条市场数据消息的系统。

**答案**：

```cpp
// 1. 多队列处理
class MarketDataProcessor {
public:
    void start(int num_workers) {
        // 按品种分片
        for (int i = 0; i < num_workers; ++i) {
            workers_.emplace_back([this, i]() {
                process_shard(i);
            });
            // 绑定CPU核心
            set_cpu_affinity(workers_.back(), i);
        }
    }
    
    void dispatch(const RawMessage& msg) {
        // 按symbol哈希分配到不同队列
        int shard = hash(msg.symbol) % num_shards_;
        queues_[shard].push(msg);
    }
    
private:
    void process_shard(int shard_id) {
        while (running_) {
            RawMessage msg;
            if (queues_[shard_id].pop(msg)) {
                auto parsed = parser_.parse(msg);
                book_builder_.update(parsed);
                notify_strategies(parsed);
            }
        }
    }
    
    std::vector<SPSCQueue<RawMessage>> queues_;
    int num_shards_;
};

// 2. 零拷贝解析
// 3. Lock-free队列
// 4. 批量处理
// 5. SIMD加速解析
```

### Q3: 交易系统的容错设计

**问题**：如何设计一个高可用的交易系统？

**答案**：

```
1. 主从架构
┌─────────────┐     ┌─────────────┐
│   Primary   │ ←→ │   Standby   │
│   (Active)  │     │  (Passive)  │
└─────────────┘     └─────────────┘
       ↑                   ↑
       └───────┬───────────┘
               ↓
        State Replication

2. 状态同步策略：
- 同步复制：每个订单都等待从机确认（增加延迟）
- 异步复制：从机延迟复制（可能丢失）
- 混合模式：关键状态同步，非关键异步

3. 故障检测与切换：
- 心跳检测（毫秒级）
- 多数派投票（避免脑裂）
- 自动切换 vs 手动切换

4. 状态恢复：
- 订单状态机重建
- 仓位核对
- 序列号Gap Fill
```

---

## 二、延迟优化

### Q4: 如何测量和优化系统延迟？

**问题**：描述你会如何分析和优化一个交易系统的延迟。

**答案**：

```cpp
// 1. 测量方法
class LatencyProfiler {
public:
    // 使用硬件时间戳
    void record_checkpoint(const char* name) {
        checkpoints_[name] = rdtscp();
    }
    
    void print_breakdown() {
        uint64_t prev = 0;
        for (const auto& [name, ts] : checkpoints_) {
            if (prev > 0) {
                uint64_t delta_ns = cycles_to_ns(ts - prev);
                printf("%s: %lu ns\n", name, delta_ns);
            }
            prev = ts;
        }
    }
};

// 2. 优化步骤
/*
Step 1: 建立基准
- 测量端到端延迟分布
- 识别P50、P99、P99.9

Step 2: 识别瓶颈
- 使用perf分析CPU热点
- 检查缓存命中率
- 分析系统调用

Step 3: 优化热路径
- 减少内存分配
- 优化数据结构布局
- 使用SIMD

Step 4: 减少抖动
- 禁用中断聚合
- 使用isolcpus
- 锁定内存
*/
```

### Q5: 网络延迟优化

**问题**：如何优化网络延迟？

**答案**：

```
1. 硬件层
- 使用低延迟网卡（Solarflare、Mellanox）
- 直连交易所（Co-location）
- 光纤优化（空心光纤）

2. 协议栈优化
- Kernel Bypass（DPDK、ef_vi）
- TCP优化（禁用Nagle、调整buffer）
- 使用UDP（适用时）

3. 应用层优化
- 连接预热
- 批量发送
- 零拷贝

4. Socket调优
```cpp
int enable_low_latency(int fd) {
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
    setsockopt(fd, IPPROTO_TCP, TCP_QUICKACK, &one, sizeof(one));
    
    // 减小缓冲区（减少排队延迟）
    int bufsize = 4096;
    setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
    setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));
    
    // Busy polling
    int busy_poll = 50;  // 50us
    setsockopt(fd, SOL_SOCKET, SO_BUSY_POLL, &busy_poll, sizeof(busy_poll));
    
    return 0;
}
```

---

## 三、数据处理

### Q6: 设计Order Book数据结构

**问题**：设计一个支持快速更新和查询的Order Book。

**答案**：

```cpp
class OrderBook {
public:
    // O(1) 获取最优价格
    Price best_bid() const { return best_bid_; }
    Price best_ask() const { return best_ask_; }
    
    // O(1) 添加订单（使用对象池）
    void add_order(Order* order) {
        orders_[order->id] = order;
        get_level(order->price, order->side).add(order);
        update_best_prices(order->side);
    }
    
    // O(1) 取消订单
    void cancel_order(uint64_t order_id) {
        auto it = orders_.find(order_id);
        if (it == orders_.end()) return;
        
        Order* order = it->second;
        get_level(order->price, order->side).remove(order);
        orders_.erase(it);
        update_best_prices(order->side);
        
        order_pool_.release(order);
    }
    
private:
    // 使用数组索引价格级别（热区）
    std::array<PriceLevel, 1000> bid_levels_;
    std::array<PriceLevel, 1000> ask_levels_;
    
    // 哈希表快速查找订单
    std::unordered_map<uint64_t, Order*> orders_;
    
    // 缓存最优价格
    Price best_bid_ = 0;
    Price best_ask_ = 0;
    
    // 对象池避免动态分配
    ObjectPool<Order> order_pool_;
};

// 关键优化：
// 1. 价格使用整数（tick为单位）
// 2. 预分配所有数据结构
// 3. 缓存行对齐
// 4. 使用侵入式链表
```

### Q7: 处理行情断线重连

**问题**：如何处理市场数据连接断开和重连？

**答案**：

```cpp
class MarketDataConnection {
public:
    void handle_disconnect() {
        // 1. 标记数据为stale
        mark_all_books_stale();
        
        // 2. 通知策略停止交易
        notify_strategies(MarketDataStatus::STALE);
        
        // 3. 开始重连
        start_reconnect();
    }
    
    void handle_reconnect() {
        // 1. 请求snapshot
        request_snapshot();
        
        // 2. 处理snapshot
        apply_snapshot(snapshot);
        
        // 3. 处理缓存的增量更新
        apply_buffered_updates();
        
        // 4. 恢复正常状态
        notify_strategies(MarketDataStatus::LIVE);
    }
    
private:
    void request_snapshot() {
        // 发送快照请求
        send_snapshot_request();
        
        // 等待快照（带超时）
        if (!wait_for_snapshot(timeout_)) {
            throw std::runtime_error("Snapshot timeout");
        }
    }
    
    void apply_buffered_updates() {
        // 按序列号排序并应用
        std::sort(buffered_updates_.begin(), buffered_updates_.end(),
                  [](auto& a, auto& b) { return a.seq < b.seq; });
        
        for (const auto& update : buffered_updates_) {
            if (update.seq > last_applied_seq_) {
                apply_update(update);
                last_applied_seq_ = update.seq;
            }
        }
        
        buffered_updates_.clear();
    }
    
    uint64_t last_applied_seq_ = 0;
    std::vector<MarketDataUpdate> buffered_updates_;
};
```

---

## 四、系统设计问答

### Q8: 如何处理交易所的消息序列号Gap？

**答案**：

```
1. 检测Gap
- 每条消息都有序列号
- 如果收到的序列号 > 期望序列号 + 1，说明有Gap

2. 处理策略
方案A：请求重传
- 向交易所请求缺失的消息
- 缓存后续消息直到Gap填补

方案B：请求Snapshot
- 如果Gap太大，请求完整快照
- 重建整个Order Book

方案C：继续处理 + 告警
- 某些场景可以容忍Gap
- 记录并告警

3. 实现考虑
- Gap检测必须是O(1)
- 缓冲区大小限制
- 超时处理
```

### Q9: 如何设计一个支持多交易所的系统？

**答案**：

```
1. 抽象层设计
┌─────────────────────────────────────────────────────────────┐
│  Unified Interface                                           │
│  - order_book_interface                                     │
│  - order_gateway_interface                                  │
│  - market_data_interface                                    │
└─────────────────────────────────────────────────────────────┘
        ↓              ↓              ↓
┌───────────┐  ┌───────────┐  ┌───────────┐
│ CME       │  │ NASDAQ    │  │ NYSE      │
│ Adapter   │  │ Adapter   │  │ Adapter   │
└───────────┘  └───────────┘  └───────────┘

2. 关键设计点
- 统一的订单类型映射
- 价格精度处理（不同交易所tick不同）
- 时间同步（PTP）
- 品种代码映射

3. 性能考虑
- 每个交易所独立连接
- 避免跨交易所的锁竞争
- 按交易所分片处理
```

### Q10: 监控和告警系统设计

**答案**：

```
1. 监控指标层次
- 业务层：PnL、仓位、订单成功率
- 应用层：延迟、吞吐量、队列深度
- 系统层：CPU、内存、网络
- 硬件层：温度、ECC错误

2. 低延迟监控
// 不影响主路径的监控
class AsyncMetrics {
    void record(const char* name, uint64_t value) {
        // 写入无锁队列
        metrics_queue_.push({name, value, rdtsc()});
    }
    
    // 后台线程聚合和上报
    void background_reporter() {
        while (running_) {
            Metric m;
            while (metrics_queue_.pop(m)) {
                aggregate(m);
            }
            report_to_monitoring_system();
            std::this_thread::sleep_for(1s);
        }
    }
};

3. 告警分级
- P1: 立即处理（Kill Switch触发）
- P2: 5分钟内处理（延迟异常）
- P3: 1小时内处理（资源预警）
- P4: 次日处理（统计异常）
```

---

## 总结

**系统设计面试要点**：

1. **先澄清需求**
   - 延迟要求
   - 吞吐量要求
   - 可用性要求

2. **从高到低设计**
   - 高层架构
   - 组件设计
   - 关键数据结构

3. **权衡讨论**
   - 延迟 vs 吞吐量
   - 一致性 vs 可用性
   - 复杂度 vs 可维护性

4. **展示深度**
   - 具体的技术选型
   - 实际的数字（延迟、吞吐量）
   - 生产环境经验

---

## 相关文章

- [上一篇：交易系统容错与恢复](/articles/hft/hft-21-交易系统容错与恢复/)
- [下一篇：HFT面试题-算法与数据结构](/articles/hft/hft-23-HFT面试题-算法与数据结构/)
