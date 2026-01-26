+++
title = "25.HFT-缓存友好数据结构设计"
slug = "cpp-25-HFT缓存友好数据结构设计"
date = 2026-01-21
description = "深入剖析缓存友好的数据结构设计，包括SoA vs AoS、数据布局优化、Cache-Oblivious算法，HFT低延迟系统核心技术"
[taxonomies]
tags = ["C++", "缓存优化", "数据结构", "HFT", "低延迟", "Data-Oriented Design"]
+++

## 概述

缓存友好的数据结构设计可以显著提升性能。在HFT系统中，正确的数据布局可以将内存访问延迟从100ns降低到1ns。

---

## 一、AoS vs SoA

### 1.1 Array of Structures（AoS）

```cpp
// 传统面向对象设计
struct Particle {
    float x, y, z;       // 位置
    float vx, vy, vz;    // 速度
    float mass;
    int type;
};

std::vector<Particle> particles;  // AoS

// 更新所有粒子的位置
void updatePositions(float dt) {
    for (auto& p : particles) {
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.z += p.vz * dt;
    }
}

// 内存访问模式：
// [x0,y0,z0,vx0,vy0,vz0,mass0,type0, x1,y1,z1,vx1,vy1,vz1,mass1,type1, ...]
// 每次迭代加载整个结构体（32字节），但只使用部分字段
```

### 1.2 Structure of Arrays（SoA）

```cpp
// 数据导向设计
struct ParticlesSoA {
    std::vector<float> x, y, z;       // 位置
    std::vector<float> vx, vy, vz;    // 速度
    std::vector<float> mass;
    std::vector<int> type;
    size_t count;
};

ParticlesSoA particles;

// 更新所有粒子的位置
void updatePositions(float dt) {
    for (size_t i = 0; i < particles.count; ++i) {
        particles.x[i] += particles.vx[i] * dt;
        particles.y[i] += particles.vy[i] * dt;
        particles.z[i] += particles.vz[i] * dt;
    }
}

// 内存访问模式：
// x:  [x0,x1,x2,x3,...]  连续访问
// vx: [vx0,vx1,vx2,...]  连续访问
// 完美的空间局部性！
```

### 1.3 性能对比

```cpp
void benchmark() {
    constexpr size_t N = 1'000'000;
    
    // AoS
    std::vector<Particle> aos(N);
    auto start = std::chrono::high_resolution_clock::now();
    for (auto& p : aos) {
        p.x += p.vx * 0.016f;
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::cout << "AoS: " << /* ... */ << " ms\n";
    
    // SoA
    std::vector<float> x(N), vx(N);
    start = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < N; ++i) {
        x[i] += vx[i] * 0.016f;
    }
    end = std::chrono::high_resolution_clock::now();
    std::cout << "SoA: " << /* ... */ << " ms\n";
}

// 典型结果：
// AoS: 15 ms
// SoA: 3 ms (5x faster!)
```

### 1.4 SIMD友好性

```cpp
// SoA天然适合SIMD
void updatePositionsSIMD(float dt) {
    __m256 dt_vec = _mm256_set1_ps(dt);
    
    for (size_t i = 0; i + 8 <= particles.count; i += 8) {
        __m256 x = _mm256_loadu_ps(&particles.x[i]);
        __m256 vx = _mm256_loadu_ps(&particles.vx[i]);
        x = _mm256_fmadd_ps(vx, dt_vec, x);
        _mm256_storeu_ps(&particles.x[i], x);
    }
}
```

---

## 二、HFT数据结构设计

### 2.1 订单簿设计

```cpp
// 传统设计（AoS）
struct Order {
    int64_t order_id;
    int64_t timestamp;
    int32_t price;
    int32_t quantity;
    int8_t side;
    // padding...
};

std::map<int32_t, std::vector<Order>> order_book;

// 优化设计（SoA + 连续内存）
struct alignas(64) PriceLevel {
    int32_t price;
    int32_t total_quantity;
    int32_t order_count;
    int32_t padding;
};

class FastOrderBook {
    // 使用数组而非map
    std::array<PriceLevel, MAX_LEVELS> bid_levels_;
    std::array<PriceLevel, MAX_LEVELS> ask_levels_;
    size_t bid_count_ = 0;
    size_t ask_count_ = 0;
    
public:
    // 最优买价：O(1)，cache friendly
    const PriceLevel& bestBid() const {
        return bid_levels_[0];
    }
    
    // 遍历所有买方级别：顺序内存访问
    void forEachBid(auto&& fn) const {
        for (size_t i = 0; i < bid_count_; ++i) {
            fn(bid_levels_[i]);
        }
    }
};
```

### 2.2 行情数据结构

```cpp
// 热数据与冷数据分离
struct MarketDataHot {
    int32_t bid_price;
    int32_t ask_price;
    int32_t bid_size;
    int32_t ask_size;
    int64_t timestamp;
    // 32 bytes - fits in half cache line
};

struct MarketDataCold {
    char symbol[16];
    char exchange[8];
    int32_t tick_size;
    int32_t lot_size;
    // 不常访问的字段
};

class MarketData {
    MarketDataHot hot_;
    MarketDataCold* cold_;  // 指针指向冷数据
    
public:
    // 热路径只访问hot_
    int32_t getBidPrice() const { return hot_.bid_price; }
    int32_t getAskPrice() const { return hot_.ask_price; }
    int64_t getMidPrice() const {
        return (hot_.bid_price + hot_.ask_price) / 2;
    }
};
```

### 2.3 时间序列数据

```cpp
// 环形缓冲区：避免内存分配
template<typename T, size_t Capacity>
class RingBuffer {
    alignas(64) T buffer_[Capacity];
    size_t head_ = 0;
    size_t size_ = 0;
    
public:
    void push(const T& item) {
        buffer_[(head_ + size_) % Capacity] = item;
        if (size_ < Capacity) {
            ++size_;
        } else {
            head_ = (head_ + 1) % Capacity;
        }
    }
    
    // 获取最近N个元素
    void getRecent(T* out, size_t n) const {
        n = std::min(n, size_);
        for (size_t i = 0; i < n; ++i) {
            out[i] = buffer_[(head_ + size_ - n + i) % Capacity];
        }
    }
};

// 使用
RingBuffer<int64_t, 1024> price_history;
```

---

## 三、Cache-Oblivious算法

### 3.1 概念

```cpp
// Cache-Oblivious：不需要知道缓存大小的算法
// 自动适应各级缓存

// 传统矩阵乘法：cache unfriendly
void matmul_naive(const float* A, const float* B, float* C, int n) {
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            for (int k = 0; k < n; ++k) {
                C[i*n + j] += A[i*n + k] * B[k*n + j];
            }
        }
    }
}

// Cache-Oblivious递归分块
void matmul_recursive(const float* A, const float* B, float* C,
                      int n, int i0, int j0, int k0, int size) {
    if (size <= 32) {  // 基本情况
        for (int i = i0; i < i0 + size; ++i) {
            for (int j = j0; j < j0 + size; ++j) {
                for (int k = k0; k < k0 + size; ++k) {
                    C[i*n + j] += A[i*n + k] * B[k*n + j];
                }
            }
        }
        return;
    }
    
    int half = size / 2;
    // 递归分解为8个子问题
    // ...
}
```

### 3.2 B+树的缓存优化

```cpp
// 传统B+树节点
template<typename K, typename V, int Order>
struct BPlusNode {
    K keys[Order - 1];
    union {
        BPlusNode* children[Order];  // 内部节点
        V values[Order - 1];          // 叶子节点
    };
    int count;
    bool is_leaf;
};

// 缓存优化B+树：节点大小=Cache Line
template<typename K, typename V>
struct alignas(64) CacheFriendlyNode {
    // 假设K和V各4字节，Order选择使节点恰好64字节
    static constexpr int Order = (64 - 8) / (sizeof(K) + sizeof(V));
    
    K keys[Order];
    V values[Order];
    int count;
    int padding;
};

static_assert(sizeof(CacheFriendlyNode<int, int>) == 64);
```

---

## 四、避免缓存陷阱

### 4.1 Cache Line Boundary

```cpp
// 避免数据跨越Cache Line边界
struct BadStruct {
    int64_t a;
    int64_t b;  // 可能跨越Cache Line边界
};

// 好：确保对齐
struct alignas(64) GoodStruct {
    int64_t a;
    int64_t b;
    char padding[48];
};
```

### 4.2 链表的缓存问题

```cpp
// 链表：缓存不友好
struct ListNode {
    int data;
    ListNode* next;  // 指向随机位置
};

// 遍历：每次访问可能cache miss
int sumList(ListNode* head) {
    int sum = 0;
    while (head) {
        sum += head->data;  // 可能cache miss
        head = head->next;  // 指针追逐
    }
    return sum;
}

// 解决方案1：使用数组
std::vector<int> data;

// 解决方案2：展开链表
struct UnrolledNode {
    int data[16];  // 每个节点存多个元素
    int count;
    UnrolledNode* next;
};
```

### 4.3 二维数组访问顺序

```cpp
// 行优先存储的矩阵
float matrix[N][M];

// 好：按行访问
for (int i = 0; i < N; ++i) {
    for (int j = 0; j < M; ++j) {
        matrix[i][j] = 0;  // 连续内存访问
    }
}

// 坏：按列访问
for (int j = 0; j < M; ++j) {
    for (int i = 0; i < N; ++i) {
        matrix[i][j] = 0;  // 每次跳M个元素，可能cache miss
    }
}
```

---

## 五、测量工具

```bash
# Linux perf测量缓存效率
perf stat -e cache-references,cache-misses,L1-dcache-load-misses ./app

# Valgrind cachegrind
valgrind --tool=cachegrind ./app
cg_annotate cachegrind.out.*

# Intel VTune
vtune -collect memory-access ./app
```

---

## 总结

| 技术 | 效果 | 适用场景 |
|------|------|----------|
| SoA | 5-10x | 批量处理同类数据 |
| Hot/Cold分离 | 2-5x | 访问模式不均匀 |
| Cache Line对齐 | 1.5-2x | 多线程共享数据 |
| 数组替代链表 | 2-10x | 遍历操作 |
| 循环优化 | 2-5x | 矩阵/数组操作 |

**HFT核心原则**：
1. 优先使用SoA布局
2. 热数据与冷数据分离
3. 保持Cache Line对齐
4. 避免链表和指针追逐
5. 预分配连续内存
