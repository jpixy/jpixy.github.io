+++
title = "26. CPU Affinity and NUMA (HFT)"
slug = "cpp-26-HFT-CPU亲和性与NUMA优化"
date = 2026-01-21
description = "深入剖析CPU亲和性设置、NUMA架构优化、线程绑定策略，HFT低延迟系统核心技术"
[taxonomies]
tags = ["C++", "CPU亲和性", "NUMA", "HFT", "低延迟", "性能优化"]
+++

## 概述

在HFT系统中，正确的CPU亲和性和NUMA配置可以减少上下文切换、避免跨NUMA访问延迟，是实现微秒级延迟的关键。

---

## 一、CPU亲和性基础

### 1.1 什么是CPU亲和性

```cpp
// CPU亲和性：将线程/进程绑定到特定CPU核心
// 好处：
// 1. 避免上下文切换开销
// 2. 保持L1/L2缓存热度
// 3. 减少缓存一致性开销
// 4. 避免跨NUMA访问

#include <sched.h>
#include <pthread.h>

void setAffinity(int cpu_id) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu_id, &cpuset);
    
    int result = pthread_setaffinity_np(pthread_self(), 
                                        sizeof(cpu_set_t), 
                                        &cpuset);
    if (result != 0) {
        throw std::runtime_error("Failed to set affinity");
    }
}
```

### 1.2 C++线程亲和性

```cpp
#include <thread>
#include <sched.h>

void setThreadAffinity(std::thread& t, int cpu_id) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu_id, &cpuset);
    
    int rc = pthread_setaffinity_np(t.native_handle(),
                                    sizeof(cpu_set_t), &cpuset);
    if (rc != 0) {
        throw std::runtime_error("Error setting thread affinity");
    }
}

// 使用
std::thread worker([]() {
    // 工作代码
});
setThreadAffinity(worker, 4);  // 绑定到CPU 4
```

### 1.3 查看CPU拓扑

```bash
# 查看CPU信息
lscpu

# 查看NUMA节点
numactl --hardware

# 输出示例：
# available: 2 nodes (0-1)
# node 0 cpus: 0 2 4 6 8 10 12 14 16 18 20 22
# node 1 cpus: 1 3 5 7 9 11 13 15 17 19 21 23
# node distances:
# node   0   1
#   0:  10  21
#   1:  21  10

# 查看超线程配对
cat /sys/devices/system/cpu/cpu0/topology/thread_siblings_list
```

---

## 二、NUMA架构

### 2.1 NUMA概述

```
┌────────────────────────┐    ┌────────────────────────┐
│       NUMA Node 0      │    │       NUMA Node 1      │
│  ┌──────┐  ┌──────┐   │    │  ┌──────┐  ┌──────┐   │
│  │CPU 0 │  │CPU 2 │   │    │  │CPU 1 │  │CPU 3 │   │
│  └──────┘  └──────┘   │    │  └──────┘  └──────┘   │
│         ↓             │    │         ↓             │
│  ┌────────────────┐   │    │  ┌────────────────┐   │
│  │   L3 Cache     │   │    │  │   L3 Cache     │   │
│  └────────────────┘   │    │  └────────────────┘   │
│         ↓             │    │         ↓             │
│  ┌────────────────┐   │    │  ┌────────────────┐   │
│  │  Local Memory  │←──┼────┼──│  Local Memory  │   │
│  │  (Fast: ~60ns) │   │    │  │  (Fast: ~60ns) │   │
│  └────────────────┘   │    │  └────────────────┘   │
└────────────────────────┘    └────────────────────────┘
          ↑                              ↑
          │   ←── QPI/UPI Link ──→       │
          │   (Slow: ~100-150ns)         │
          └──────────────────────────────┘
```

### 2.2 NUMA内存分配

```cpp
#include <numa.h>

// 在特定NUMA节点分配内存
void* numaAlloc(size_t size, int node) {
    void* ptr = numa_alloc_onnode(size, node);
    if (!ptr) {
        throw std::bad_alloc();
    }
    return ptr;
}

// 获取当前线程的NUMA节点
int getCurrentNode() {
    return numa_node_of_cpu(sched_getcpu());
}

// 在本地节点分配
void* allocLocal(size_t size) {
    return numa_alloc_local(size);
}

// 交错分配（跨所有节点）
void* allocInterleaved(size_t size) {
    return numa_alloc_interleaved(size);
}
```

### 2.3 NUMA策略

```bash
# 使用numactl运行程序

# 绑定到NUMA节点0
numactl --cpunodebind=0 --membind=0 ./hft_app

# 本地内存分配策略
numactl --localalloc ./hft_app

# 交错分配（适合大量随机访问）
numactl --interleave=all ./hft_app
```

---

## 三、HFT线程绑定策略

### 3.1 独占核心

```cpp
// HFT关键线程应该独占CPU核心
class HFTThread {
    std::thread thread_;
    int cpu_id_;
    
public:
    HFTThread(int cpu_id, std::function<void()> work)
        : cpu_id_(cpu_id) {
        thread_ = std::thread([this, work]() {
            // 绑定到指定CPU
            setAffinity(cpu_id_);
            
            // 设置实时调度
            setRealtimeScheduling();
            
            // 执行工作
            work();
        });
    }
    
private:
    void setAffinity(int cpu) {
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(cpu, &cpuset);
        pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);
    }
    
    void setRealtimeScheduling() {
        struct sched_param param;
        param.sched_priority = 99;  // 最高优先级
        pthread_setschedparam(pthread_self(), SCHED_FIFO, &param);
    }
};
```

### 3.2 隔离CPU核心

```bash
# 在grub配置中隔离CPU核心
# /etc/default/grub
GRUB_CMDLINE_LINUX="isolcpus=4,5,6,7 nohz_full=4,5,6,7 rcu_nocbs=4,5,6,7"

# isolcpus: 从调度器中排除这些CPU
# nohz_full: 禁用时钟中断
# rcu_nocbs: 将RCU回调移到其他CPU

# 更新grub
sudo update-grub
sudo reboot
```

### 3.3 典型HFT线程布局

```cpp
// HFT系统线程分配策略
class TradingSystem {
    // 网络接收线程 - CPU 4 (隔离核心)
    HFTThread network_rx_{4, [this]() { networkReceiveLoop(); }};
    
    // 策略线程 - CPU 5 (隔离核心)
    HFTThread strategy_{5, [this]() { strategyLoop(); }};
    
    // 订单发送线程 - CPU 6 (隔离核心)
    HFTThread order_sender_{6, [this]() { orderSendLoop(); }};
    
    // 日志线程 - CPU 0 (普通核心)
    std::thread logger_{[this]() { logLoop(); }};
    
    // 监控线程 - CPU 1 (普通核心)
    std::thread monitor_{[this]() { monitorLoop(); }};
};
```

---

## 四、超线程考虑

### 4.1 超线程的影响

```cpp
// 超线程（SMT）在同一物理核心上运行两个逻辑核心
// 共享：L1/L2缓存、执行单元
// 不共享：寄存器状态

// HFT最佳实践：
// 1. 禁用超线程，或
// 2. 只使用每对超线程中的一个

// 获取超线程配对
int getSiblingCore(int cpu) {
    std::string path = "/sys/devices/system/cpu/cpu" + 
                       std::to_string(cpu) + 
                       "/topology/thread_siblings_list";
    std::ifstream file(path);
    std::string siblings;
    std::getline(file, siblings);
    // 解析返回配对核心
    // ...
    return -1;
}

// 只使用物理核心
std::vector<int> getPhysicalCores() {
    std::vector<int> physical;
    std::set<int> seen;
    
    for (int cpu = 0; cpu < getNumCPUs(); ++cpu) {
        int sibling = getSiblingCore(cpu);
        if (seen.find(sibling) == seen.end()) {
            physical.push_back(cpu);
            seen.insert(cpu);
        }
    }
    return physical;
}
```

### 4.2 禁用超线程

```bash
# BIOS中禁用

# 或运行时禁用
echo 0 > /sys/devices/system/cpu/cpu1/online  # 禁用CPU 1
# 假设CPU 0和CPU 1是超线程配对

# 或在grub中
GRUB_CMDLINE_LINUX="nosmt"
```

---

## 五、性能测量

### 5.1 测量NUMA效应

```cpp
void benchmarkNUMA() {
    const size_t size = 100 * 1024 * 1024;  // 100MB
    
    // 本地节点分配
    int current_node = numa_node_of_cpu(sched_getcpu());
    char* local_mem = (char*)numa_alloc_onnode(size, current_node);
    
    // 远程节点分配
    int remote_node = (current_node + 1) % numa_num_configured_nodes();
    char* remote_mem = (char*)numa_alloc_onnode(size, remote_node);
    
    // 预热
    memset(local_mem, 0, size);
    memset(remote_mem, 0, size);
    
    // 测量本地访问
    auto start = std::chrono::high_resolution_clock::now();
    volatile long sum = 0;
    for (size_t i = 0; i < size; i += 64) {
        sum += local_mem[i];
    }
    auto local_time = std::chrono::high_resolution_clock::now() - start;
    
    // 测量远程访问
    start = std::chrono::high_resolution_clock::now();
    sum = 0;
    for (size_t i = 0; i < size; i += 64) {
        sum += remote_mem[i];
    }
    auto remote_time = std::chrono::high_resolution_clock::now() - start;
    
    std::cout << "Local: " << local_time.count() << " ns\n";
    std::cout << "Remote: " << remote_time.count() << " ns\n";
    std::cout << "Ratio: " << (double)remote_time.count() / local_time.count() << "x\n";
    
    // 典型结果：Remote比Local慢1.5-2x
}
```

### 5.2 使用perf

```bash
# 测量NUMA效应
perf stat -e \
    node-loads,node-load-misses,\
    node-stores,node-store-misses \
    ./hft_app

# 测量上下文切换
perf stat -e context-switches,cpu-migrations ./hft_app
```

---

## 六、最佳实践清单

```cpp
// HFT系统CPU/NUMA配置清单

// 1. 隔离关键CPU核心
// isolcpus=4,5,6,7 nohz_full=4,5,6,7

// 2. 禁用或正确使用超线程
// nosmt 或 只使用一半逻辑核心

// 3. 绑定关键线程到隔离核心
setAffinity(network_thread, 4);
setAffinity(strategy_thread, 5);
setAffinity(order_thread, 6);

// 4. 使用NUMA本地内存
void* buffer = numa_alloc_local(size);

// 5. 设置实时调度
struct sched_param param;
param.sched_priority = 99;
sched_setscheduler(0, SCHED_FIFO, &param);

// 6. 锁定内存
mlockall(MCL_CURRENT | MCL_FUTURE);

// 7. 关闭频率缩放
// echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

---

## 总结

| 优化 | 延迟减少 | 复杂度 |
|------|----------|--------|
| CPU亲和性 | 5-20 µs | 低 |
| NUMA本地内存 | 30-50 ns/访问 | 中 |
| 核心隔离 | 消除抖动 | 中 |
| 禁用超线程 | 减少干扰 | 低 |
| 实时调度 | 消除延迟尖峰 | 中 |

**HFT核心原则**：
1. 关键路径线程绑定隔离核心
2. 所有数据在同一NUMA节点
3. 禁用超线程或只用一半
4. 使用实时调度策略
5. 锁定内存，禁用swap
