+++
title = "32. Memory Hierarchy and Bandwidth (HFT)"
date = 2026-01-21
description = "深入剖析内存层次结构对HFT性能的影响，包括DRAM时序、内存带宽、Memory-bound分析、NUMA优化等"
[taxonomies]
tags = ["C++", "内存", "DRAM", "NUMA", "性能优化", "HFT"]
+++

## 概述

内存子系统是现代计算机的主要性能瓶颈。在HFT系统中，理解内存层次结构并优化内存访问模式是获得低延迟的关键。

---

## 一、内存层次结构

### 1.1 典型延迟

```
存储层次          大小           延迟
─────────────────────────────────────────
寄存器           ~100 B         0 cycles
L1 Cache         32-64 KB       4-5 cycles     (~1 ns)
L2 Cache         256-512 KB     12-14 cycles   (~3-4 ns)
L3 Cache         8-64 MB        40-60 cycles   (~15-25 ns)
主内存           GB-TB          200-400 cycles (~50-100 ns)
NVMe SSD         TB             ~10,000 cycles (~10 µs)
网络             -              ~10,000+ cycles (~10+ µs)
```

### 1.2 带宽对比

```
存储层次          带宽
─────────────────────────────────────
L1 Cache         2x 64B/周期 ≈ 800 GB/s (3GHz CPU)
L2 Cache         64B/周期 ≈ 200 GB/s
L3 Cache         ~100-200 GB/s
主内存           DDR4: 25-50 GB/s
                 DDR5: 50-100 GB/s
```

---

## 二、DRAM架构

### 2.1 DRAM组织

```
Channel → DIMM → Rank → Chip → Bank → Row → Column

典型DDR4配置：
- 2 Channels (双通道)
- 2 DIMMs per channel
- 2 Ranks per DIMM
- 8 Banks per Rank
- 数千Rows per Bank
- 1024 Columns per Row
```

### 2.2 DRAM时序参数

```
关键时序（以DDR4-3200 CL16为例）：

CAS Latency (CL):   16 cycles  (~10 ns)
  - 从列地址到数据可用

tRCD:               16 cycles
  - Row to Column Delay
  - 从行激活到列访问

tRP:                16 cycles
  - Row Precharge
  - 关闭一行准备打开另一行

tRAS:               39 cycles
  - Row Active Time
  - 行必须保持激活的最短时间

随机访问延迟 ≈ tRCD + CL ≈ 20ns
行切换延迟 ≈ tRP + tRCD + CL ≈ 30ns
```

### 2.3 Row Buffer

```
每个Bank有一个Row Buffer（8KB典型值）

Row Buffer Hit:  快速，~10ns
Row Buffer Miss: 需要precharge + activate, ~30ns
Row Buffer Conflict: 最慢，需要关闭当前行

优化策略：
- 顺序访问利用Row Buffer局部性
- 避免跨Bank的随机访问
```

---

## 三、内存带宽计算

### 3.1 理论带宽

```cpp
// DDR4-3200 双通道
// 传输速率 = 3200 MT/s (Million Transfers per second)
// 总线宽度 = 64 bits = 8 bytes
// 通道数 = 2

// 理论带宽 = 3200 * 8 * 2 = 51.2 GB/s

// DDR5-5200 双通道
// 理论带宽 = 5200 * 8 * 2 = 83.2 GB/s
```

### 3.2 测量实际带宽

```cpp
#include <chrono>
#include <cstring>

void measureBandwidth() {
    const size_t SIZE = 1ULL << 30;  // 1GB
    char* src = new char[SIZE];
    char* dst = new char[SIZE];
    
    // 预热
    std::memset(src, 1, SIZE);
    std::memset(dst, 0, SIZE);
    
    auto start = std::chrono::high_resolution_clock::now();
    
    std::memcpy(dst, src, SIZE);
    
    auto end = std::chrono::high_resolution_clock::now();
    
    double seconds = std::chrono::duration<double>(end - start).count();
    double bandwidth = (SIZE * 2.0) / seconds / 1e9;  // 读+写
    
    std::cout << "Bandwidth: " << bandwidth << " GB/s" << std::endl;
    
    delete[] src;
    delete[] dst;
}
```

### 3.3 STREAM Benchmark

```bash
# 编译
gcc -O3 -march=native -fopenmp stream.c -o stream

# 运行
./stream

# 输出示例
# Function    Best Rate MB/s  Avg time
# Copy:           45000.0     0.0180
# Scale:          44000.0     0.0185
# Add:            48000.0     0.0250
# Triad:          47000.0     0.0260
```

---

## 四、Memory-Bound vs Compute-Bound

### 4.1 操作强度

```cpp
// 操作强度（Operational Intensity）= FLOP / Byte

// 低操作强度（Memory-Bound）
void vectorAdd(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];  // 1 FLOP, 12 bytes
    }
    // OI = 1/12 ≈ 0.08 FLOP/Byte
}

// 高操作强度（Compute-Bound）
void matrixMultiply(float* A, float* B, float* C, int n) {
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            float sum = 0;
            for (int k = 0; k < n; ++k) {
                sum += A[i*n+k] * B[k*n+j];  // 2n FLOP
            }
            C[i*n+j] = sum;  // 3n bytes amortized
        }
    }
    // OI ≈ 2n/3 FLOP/Byte (大n时)
}
```

### 4.2 Roofline模型

```
性能上限 = min(峰值计算能力, 带宽 × 操作强度)

对于OI=0.1的算法，DDR4带宽50GB/s：
- 最大性能 = 50 × 0.1 = 5 GFLOP/s
- 远低于CPU的数百GFLOP/s峰值

优化策略：
- 低OI：优化内存访问（预取、缓存优化）
- 高OI：优化计算（向量化、并行）
```

### 4.3 识别瓶颈

```bash
# 使用perf
perf stat -e cycles,instructions,cache-misses,\
mem_load_retired.l3_miss ./app

# 计算
# IPC (Instructions Per Cycle)
# 低IPC + 高L3 miss → Memory-Bound
# 高IPC + 低L3 miss → Compute-Bound
```

---

## 五、内存预取

### 5.1 硬件预取

```
现代CPU有多个硬件预取器：
- L1 Adjacent Line Prefetcher: 预取相邻缓存行
- L1 IP Prefetcher: 基于指令地址预测
- L2 Stream Prefetcher: 检测顺序访问模式
- L2 Spatial Prefetcher: 预取同一4KB页内的数据

硬件预取器能处理：
- 顺序访问
- 简单的跨步模式

无法处理：
- 随机访问
- 复杂的不规则模式
```

### 5.2 软件预取

```cpp
#include <xmmintrin.h>  // _mm_prefetch

void processWithPrefetch(const Data* array, size_t n) {
    const int PREFETCH_DISTANCE = 8;  // 经验值，需要调优
    
    for (size_t i = 0; i < n; ++i) {
        // 预取未来的数据
        if (i + PREFETCH_DISTANCE < n) {
            _mm_prefetch(
                reinterpret_cast<const char*>(&array[i + PREFETCH_DISTANCE]),
                _MM_HINT_T0  // 预取到L1
            );
        }
        
        process(array[i]);
    }
}

// 预取提示
// _MM_HINT_T0: 预取到所有缓存级别
// _MM_HINT_T1: 预取到L2及以上
// _MM_HINT_T2: 预取到L3
// _MM_HINT_NTA: 非时间局部性，尽量不污染缓存
```

### 5.3 预取链表

```cpp
struct Node {
    int data;
    Node* next;
};

int traverseWithPrefetch(Node* head) {
    int sum = 0;
    Node* curr = head;
    
    while (curr) {
        // 预取下两个节点
        if (curr->next) {
            _mm_prefetch(
                reinterpret_cast<const char*>(curr->next),
                _MM_HINT_T0
            );
            if (curr->next->next) {
                _mm_prefetch(
                    reinterpret_cast<const char*>(curr->next->next),
                    _MM_HINT_T0
                );
            }
        }
        
        sum += curr->data;
        curr = curr->next;
    }
    
    return sum;
}
```

---

## 六、NUMA优化

### 6.1 NUMA架构

```
NUMA (Non-Uniform Memory Access)

┌─────────────────┐     ┌─────────────────┐
│    Node 0       │     │    Node 1       │
│  ┌───┐ ┌───┐   │     │   ┌───┐ ┌───┐  │
│  │CPU│ │CPU│   │     │   │CPU│ │CPU│  │
│  └───┘ └───┘   │     │   └───┘ └───┘  │
│       │         │     │        │        │
│  ┌─────────┐   │     │   ┌─────────┐   │
│  │ Memory  │←──┼──┬──┼──→│ Memory  │   │
│  └─────────┘   │  │  │   └─────────┘   │
└─────────────────┘  │  └─────────────────┘
                     │
              QPI/UPI Interconnect

本地内存访问: ~70ns
远程内存访问: ~100-150ns (1.5x-2x)
```

### 6.2 NUMA感知编程

```cpp
#include <numa.h>
#include <numaif.h>

// 检查NUMA可用性
void checkNuma() {
    if (numa_available() < 0) {
        std::cerr << "NUMA not available" << std::endl;
        return;
    }
    
    std::cout << "NUMA nodes: " << numa_num_configured_nodes() << std::endl;
    std::cout << "CPUs: " << numa_num_configured_cpus() << std::endl;
}

// 在指定节点分配内存
void* allocateOnNode(size_t size, int node) {
    void* ptr = numa_alloc_onnode(size, node);
    if (!ptr) {
        throw std::bad_alloc();
    }
    return ptr;
}

// 本地分配（当前线程所在节点）
void* allocateLocal(size_t size) {
    return numa_alloc_local(size);
}

// 交织分配（跨节点分布）
void* allocateInterleaved(size_t size) {
    return numa_alloc_interleaved(size);
}

// 释放
void deallocate(void* ptr, size_t size) {
    numa_free(ptr, size);
}
```

### 6.3 线程绑定

```cpp
#include <pthread.h>

void bindThreadToNode(int node) {
    // 获取节点的CPU掩码
    struct bitmask* cpumask = numa_allocate_cpumask();
    numa_node_to_cpus(node, cpumask);
    
    // 绑定线程
    pthread_t thread = pthread_self();
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    
    for (int i = 0; i < numa_num_configured_cpus(); ++i) {
        if (numa_bitmask_isbitset(cpumask, i)) {
            CPU_SET(i, &cpuset);
        }
    }
    
    pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
    
    numa_free_cpumask(cpumask);
}

// HFT最佳实践
void hftThreadSetup(int coreId, int numaNode) {
    // 1. 绑定到特定核心
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(coreId, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);
    
    // 2. 设置内存策略为本地
    numa_set_localalloc();
    
    // 3. 锁定内存
    mlockall(MCL_CURRENT | MCL_FUTURE);
}
```

### 6.4 numactl使用

```bash
# 查看NUMA拓扑
numactl --hardware

# 在节点0运行程序
numactl --cpunodebind=0 --membind=0 ./app

# 交织内存分配
numactl --interleave=all ./app

# 查看进程的NUMA统计
numastat -p <pid>
```

---

## 七、内存分配优化

### 7.1 大页（Huge Pages）

```cpp
#include <sys/mman.h>

// 使用2MB大页
void* allocateHugePages(size_t size) {
    void* ptr = mmap(
        nullptr,
        size,
        PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
        -1,
        0
    );
    
    if (ptr == MAP_FAILED) {
        throw std::runtime_error("mmap failed");
    }
    
    return ptr;
}

// 配置系统大页
// echo 1024 > /proc/sys/vm/nr_hugepages
// 或
// sysctl -w vm.nr_hugepages=1024
```

### 7.2 THP（Transparent Huge Pages）

```bash
# 查看THP状态
cat /sys/kernel/mm/transparent_hugepage/enabled

# HFT通常禁用THP（因为压缩延迟不可预测）
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

---

## 总结

| 技术 | 效果 | HFT适用性 |
|------|------|-----------|
| 顺序访问 | 利用预取和Row Buffer | ⭐⭐⭐ |
| 软件预取 | 隐藏内存延迟 | ⭐⭐⭐ |
| NUMA本地分配 | 减少跨节点访问 | ⭐⭐⭐ |
| 大页 | 减少TLB miss | ⭐⭐⭐ |
| 内存交织 | 提高带宽 | ⭐（特定场景） |

**HFT内存优化原则**：
1. 数据尽量顺序访问
2. 线程和数据保持NUMA本地
3. 使用大页减少TLB miss
4. 禁用THP避免不确定延迟
5. 使用软件预取隐藏延迟

---

## 相关文章

- [上一篇：CPU Microarchitecture Optimization (HFT)](/articles/cpp/cpp-31-HFT-CPU微架构与性能优化/)
- [下一篇：Coroutines and User-Space Scheduling](/articles/cpp/cpp-33-C++协程与用户态调度/)
