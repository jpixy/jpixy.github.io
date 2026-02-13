+++
title = "42. HFT笔试题-延迟测量与优化"
date = 2026-02-02
weight = 42000
description = "HFT笔试：延迟测量、时间戳精度、热路径优化、分支预测"
[taxonomies]
tags = ["HFT", "笔试", "延迟", "性能", "优化"]
+++

# HFT 笔试题 - 延迟测量与优化

本文汇总 HFT 笔试中关于延迟测量和性能优化的编程题目。

---

## 题目 1：高精度时间戳

**题目**：实现纳秒级精度的时间戳获取函数，分析不同方法的优缺点。

**解答**：

```cpp
#include <chrono>
#include <x86intrin.h>

// 方法 1：std::chrono（通用，但有开销）
inline uint64_t get_time_chrono() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch()
    ).count();
}

// 方法 2：clock_gettime（Linux，较快）
inline uint64_t get_time_clock() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000ULL + ts.tv_nsec;
}

// 方法 3：RDTSC（最快，但需要转换）
inline uint64_t rdtsc() {
    return __rdtsc();
}

// 方法 4：RDTSCP（带序列化，更准确）
inline uint64_t rdtscp() {
    unsigned int aux;
    return __rdtscp(&aux);
}

// TSC 转纳秒
class TscTimer {
public:
    TscTimer() {
        calibrate();
    }
    
    void calibrate() {
        uint64_t start_tsc = rdtsc();
        uint64_t start_ns = get_time_clock();
        
        // 等待一段时间
        usleep(100000);  // 100ms
        
        uint64_t end_tsc = rdtsc();
        uint64_t end_ns = get_time_clock();
        
        tsc_per_ns_ = (double)(end_tsc - start_tsc) / (end_ns - start_ns);
    }
    
    uint64_t tsc_to_ns(uint64_t tsc) const {
        return (uint64_t)(tsc / tsc_per_ns_);
    }
    
    uint64_t now_ns() const {
        return tsc_to_ns(rdtsc());
    }
    
private:
    double tsc_per_ns_;
};
```

**性能对比**：

| 方法 | 延迟 | 精度 | 可移植性 |
|------|------|------|----------|
| chrono | ~20ns | 纳秒 | 高 |
| clock_gettime | ~15ns | 纳秒 | Linux |
| RDTSC | ~5ns | cycles | x86 |
| RDTSCP | ~10ns | cycles | x86 |

---

## 题目 2：延迟直方图

**题目**：实现一个高效的延迟直方图统计类，支持 p50/p90/p99 计算。

**解答**：

```cpp
class LatencyHistogram {
public:
    LatencyHistogram(uint64_t max_latency_ns = 1000000000ULL,  // 1s
                     uint64_t bucket_size_ns = 100)            // 100ns
        : max_latency_(max_latency_ns),
          bucket_size_(bucket_size_ns),
          num_buckets_(max_latency_ns / bucket_size_ns + 1),
          buckets_(num_buckets_, 0),
          count_(0),
          sum_(0) {}
    
    void record(uint64_t latency_ns) {
        count_++;
        sum_ += latency_ns;
        
        size_t bucket = std::min(latency_ns / bucket_size_, num_buckets_ - 1);
        buckets_[bucket]++;
    }
    
    double mean() const {
        return count_ > 0 ? (double)sum_ / count_ : 0;
    }
    
    uint64_t percentile(double p) const {
        if (count_ == 0) return 0;
        
        uint64_t target = (uint64_t)(count_ * p / 100.0);
        uint64_t cumulative = 0;
        
        for (size_t i = 0; i < num_buckets_; i++) {
            cumulative += buckets_[i];
            if (cumulative >= target) {
                return i * bucket_size_;
            }
        }
        
        return max_latency_;
    }
    
    uint64_t p50() const { return percentile(50); }
    uint64_t p90() const { return percentile(90); }
    uint64_t p99() const { return percentile(99); }
    uint64_t p999() const { return percentile(99.9); }
    
    void print() const {
        printf("Count: %lu, Mean: %.2f ns\n", count_, mean());
        printf("P50: %lu ns, P90: %lu ns, P99: %lu ns, P99.9: %lu ns\n",
               p50(), p90(), p99(), p999());
    }
    
    void reset() {
        std::fill(buckets_.begin(), buckets_.end(), 0);
        count_ = 0;
        sum_ = 0;
    }
    
private:
    uint64_t max_latency_;
    uint64_t bucket_size_;
    size_t num_buckets_;
    std::vector<uint64_t> buckets_;
    uint64_t count_;
    uint64_t sum_;
};
```

---

## 题目 3：热路径优化

**题目**：优化以下订单处理代码的热路径。

**原始代码**：

```cpp
void process_order(const Order& order) {
    // 日志记录
    log("Processing order: " + std::to_string(order.id));
    
    // 风控检查
    if (!risk_check(order)) {
        log("Risk check failed");
        return;
    }
    
    // 查找账户
    Account* account = accounts_.find(order.account_id);
    if (!account) {
        log("Account not found");
        return;
    }
    
    // 执行订单
    execute(order, account);
}
```

**优化后**：

```cpp
// 优化 1：移除热路径上的字符串操作
// 优化 2：使用 likely/unlikely 提示
// 优化 3：内联关键函数
// 优化 4：避免虚函数调用

#define likely(x)   __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)

// 异步日志
class AsyncLogger {
public:
    void log_async(const char* msg, uint64_t value) {
        // 写入无锁队列，后台线程处理
        log_queue_.push({msg, value});
    }
private:
    SPSCQueue<LogEntry> log_queue_;
};

// 优化后的处理函数
__attribute__((hot))
void process_order_optimized(const Order& order) {
    // 快速路径：大多数订单应该通过风控
    if (likely(risk_check_fast(order))) {
        // 使用预先构建的索引，O(1) 查找
        Account* account = account_index_[order.account_id];
        
        if (likely(account != nullptr)) {
            execute_inline(order, account);
            return;
        }
    }
    
    // 慢速路径
    process_order_slow(order);
}

// 慢速路径单独函数，避免影响快速路径的 icache
__attribute__((cold, noinline))
void process_order_slow(const Order& order) {
    async_logger_.log_async("Slow path for order", order.id);
    
    if (!risk_check(order)) {
        async_logger_.log_async("Risk check failed", order.id);
        return;
    }
    
    Account* account = accounts_.find(order.account_id);
    if (!account) {
        async_logger_.log_async("Account not found", order.account_id);
        return;
    }
    
    execute(order, account);
}
```

---

## 题目 4：分支预测优化

**题目**：优化以下代码的分支预测性能。

**原始代码**：

```cpp
int process_messages(const Message* messages, int count) {
    int result = 0;
    for (int i = 0; i < count; i++) {
        switch (messages[i].type) {
            case MsgType::Quote:
                result += handle_quote(messages[i]);
                break;
            case MsgType::Trade:
                result += handle_trade(messages[i]);
                break;
            case MsgType::Order:
                result += handle_order(messages[i]);
                break;
            case MsgType::Cancel:
                result += handle_cancel(messages[i]);
                break;
            default:
                result += handle_other(messages[i]);
                break;
        }
    }
    return result;
}
```

**优化后**：

```cpp
// 方法 1：函数指针表（消除分支）
using Handler = int(*)(const Message&);

const Handler handlers[] = {
    handle_quote,   // MsgType::Quote = 0
    handle_trade,   // MsgType::Trade = 1
    handle_order,   // MsgType::Order = 2
    handle_cancel,  // MsgType::Cancel = 3
    handle_other    // MsgType::Other = 4
};

int process_messages_table(const Message* messages, int count) {
    int result = 0;
    for (int i = 0; i < count; i++) {
        result += handlers[messages[i].type](messages[i]);
    }
    return result;
}

// 方法 2：按类型批量处理（提高分支预测）
int process_messages_sorted(Message* messages, int count) {
    // 先按类型排序（如果可以重排）
    std::sort(messages, messages + count,
              [](const Message& a, const Message& b) {
                  return a.type < b.type;
              });
    
    // 相同类型连续处理，分支预测准确率高
    int result = 0;
    for (int i = 0; i < count; i++) {
        switch (messages[i].type) {
            case MsgType::Quote:
                result += handle_quote(messages[i]);
                break;
            // ...
        }
    }
    return result;
}

// 方法 3：模板 + 编译期分发
template<MsgType T>
int process_single(const Message& msg);

template<>
int process_single<MsgType::Quote>(const Message& msg) {
    return handle_quote(msg);
}
// ... 其他特化
```

---

## 题目 5：缓存友好遍历

**题目**：优化以下数据结构的遍历性能。

**原始代码**：

```cpp
struct Order {
    uint64_t id;
    double price;
    int quantity;
    Side side;
    TimeInForce tif;
    char symbol[16];
    uint64_t timestamp;
    void* user_data;
    // ... 更多字段，共 256 字节
};

double calculate_total_value(const std::vector<Order>& orders) {
    double total = 0;
    for (const auto& order : orders) {
        total += order.price * order.quantity;
    }
    return total;
}
```

**优化后**：

```cpp
// 方法 1：数据布局优化（SoA）
struct OrdersSoA {
    std::vector<double> prices;
    std::vector<int> quantities;
    // 其他字段...
    
    void add(double price, int quantity) {
        prices.push_back(price);
        quantities.push_back(quantity);
    }
};

double calculate_total_value_soa(const OrdersSoA& orders) {
    double total = 0;
    size_t n = orders.prices.size();
    
    // 连续内存访问，缓存友好
    for (size_t i = 0; i < n; i++) {
        total += orders.prices[i] * orders.quantities[i];
    }
    return total;
}

// 方法 2：SIMD 优化
#include <immintrin.h>

double calculate_total_value_simd(const OrdersSoA& orders) {
    size_t n = orders.prices.size();
    size_t i = 0;
    
    __m256d sum = _mm256_setzero_pd();
    
    // 每次处理 4 个 double
    for (; i + 4 <= n; i += 4) {
        __m256d prices = _mm256_loadu_pd(&orders.prices[i]);
        __m256d quantities = _mm256_cvtepi32_pd(
            _mm_loadu_si128((__m128i*)&orders.quantities[i]));
        
        sum = _mm256_fmadd_pd(prices, quantities, sum);
    }
    
    // 水平求和
    double result[4];
    _mm256_storeu_pd(result, sum);
    double total = result[0] + result[1] + result[2] + result[3];
    
    // 处理剩余
    for (; i < n; i++) {
        total += orders.prices[i] * orders.quantities[i];
    }
    
    return total;
}

// 方法 3：预取
double calculate_total_value_prefetch(const std::vector<Order>& orders) {
    double total = 0;
    size_t n = orders.size();
    
    for (size_t i = 0; i < n; i++) {
        // 预取后续数据
        if (i + 4 < n) {
            __builtin_prefetch(&orders[i + 4], 0, 3);
        }
        total += orders[i].price * orders[i].quantity;
    }
    return total;
}
```

---

## 题目 6：延迟测量框架

**题目**：实现一个零开销的延迟测量框架。

**解答**：

```cpp
// 编译期开关
#ifdef ENABLE_LATENCY_MEASUREMENT
    #define LATENCY_START(name) \
        uint64_t __latency_start_##name = rdtsc()
    
    #define LATENCY_END(name, histogram) \
        do { \
            uint64_t __latency_end = rdtsc(); \
            histogram.record(__latency_end - __latency_start_##name); \
        } while(0)
#else
    #define LATENCY_START(name)
    #define LATENCY_END(name, histogram)
#endif

// 使用 RAII 自动测量
class ScopedLatency {
public:
    ScopedLatency(LatencyHistogram& hist) : hist_(hist), start_(rdtsc()) {}
    
    ~ScopedLatency() {
        hist_.record(rdtsc() - start_);
    }
    
private:
    LatencyHistogram& hist_;
    uint64_t start_;
};

#ifdef ENABLE_LATENCY_MEASUREMENT
    #define MEASURE_LATENCY(hist) ScopedLatency __scoped_latency(hist)
#else
    #define MEASURE_LATENCY(hist)
#endif

// 使用示例
void process_message(const Message& msg) {
    MEASURE_LATENCY(message_latency_);
    
    LATENCY_START(decode);
    decode(msg);
    LATENCY_END(decode, decode_latency_);
    
    LATENCY_START(process);
    process_internal(msg);
    LATENCY_END(process, process_latency_);
}
```

---

## 题目 7：CPU 绑定与隔离

**题目**：实现线程 CPU 绑定和 NUMA 亲和性设置。

**解答**：

```cpp
#include <pthread.h>
#include <sched.h>
#include <numa.h>

class ThreadAffinity {
public:
    // 绑定到特定 CPU
    static bool pin_to_cpu(int cpu) {
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(cpu, &cpuset);
        
        return pthread_setaffinity_np(
            pthread_self(), sizeof(cpuset), &cpuset) == 0;
    }
    
    // 绑定到 CPU 集合
    static bool pin_to_cpus(const std::vector<int>& cpus) {
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        for (int cpu : cpus) {
            CPU_SET(cpu, &cpuset);
        }
        
        return pthread_setaffinity_np(
            pthread_self(), sizeof(cpuset), &cpuset) == 0;
    }
    
    // 绑定到 NUMA 节点
    static bool pin_to_numa_node(int node) {
        if (numa_available() < 0) return false;
        
        struct bitmask* mask = numa_allocate_cpumask();
        numa_node_to_cpus(node, mask);
        
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        
        for (int i = 0; i < numa_num_possible_cpus(); i++) {
            if (numa_bitmask_isbitset(mask, i)) {
                CPU_SET(i, &cpuset);
            }
        }
        
        numa_free_cpumask(mask);
        
        return pthread_setaffinity_np(
            pthread_self(), sizeof(cpuset), &cpuset) == 0;
    }
    
    // 在 NUMA 节点分配内存
    static void* alloc_on_node(size_t size, int node) {
        return numa_alloc_onnode(size, node);
    }
    
    // 设置实时优先级
    static bool set_realtime_priority(int priority) {
        struct sched_param param;
        param.sched_priority = priority;
        return pthread_setschedparam(
            pthread_self(), SCHED_FIFO, &param) == 0;
    }
};

// 使用示例
void trading_thread() {
    // 绑定到隔离的 CPU
    ThreadAffinity::pin_to_cpu(2);
    
    // 设置实时优先级
    ThreadAffinity::set_realtime_priority(80);
    
    // 交易主循环
    while (running_) {
        process_messages();
    }
}
```

---

## 相关文章

- [HFT系统延迟分析方法](@/articles/hft/hft-12-HFT系统延迟分析方法.md)
- [HFT笔试题-性能分析](@/articles/hft/hft-29-HFT笔试题-性能分析.md)
- [HFT面试题-CPU与缓存优化](@/articles/hft/hft-31-HFT面试题-CPU与缓存优化.md)
