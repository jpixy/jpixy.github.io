+++
title = "15. Custom Memory Allocators (HFT)"
slug = "cpp-20-HFT自定义内存分配器设计"
date = 2026-01-21
weight = 15000
description = "深入剖析C++自定义内存分配器设计，包括Arena分配器、池分配器、无锁分配器等，HFT低延迟系统必备技术"
[taxonomies]
tags = ["C++", "内存分配", "HFT", "低延迟", "性能优化", "Arena"]
+++

## 概述

在HFT系统中，动态内存分配是延迟的主要来源之一。标准的malloc/new可能触发系统调用、锁竞争、内存碎片等问题。自定义内存分配器可以显著降低延迟。

---

## 一、标准分配器的问题

### 1.1 malloc的延迟问题

```cpp
void* ptr = malloc(size);

// malloc可能导致：
// 1. 系统调用（sbrk/mmap）：10-100μs
// 2. 锁竞争（多线程）：1-10μs
// 3. 内存碎片查找：0.1-1μs
// 4. 缓存未命中：0.1μs

// HFT系统总延迟目标可能只有1-10μs！
```

### 1.2 延迟不确定性

```cpp
// 测量malloc延迟
#include <chrono>

void measureMallocLatency() {
    constexpr int iterations = 100000;
    std::vector<long long> latencies;
    latencies.reserve(iterations);
    
    for (int i = 0; i < iterations; ++i) {
        auto start = std::chrono::high_resolution_clock::now();
        void* p = malloc(1024);
        auto end = std::chrono::high_resolution_clock::now();
        
        latencies.push_back(
            std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count()
        );
        free(p);
    }
    
    // 分析结果
    std::sort(latencies.begin(), latencies.end());
    std::cout << "P50: " << latencies[iterations / 2] << " ns\n";
    std::cout << "P99: " << latencies[iterations * 99 / 100] << " ns\n";
    std::cout << "P99.9: " << latencies[iterations * 999 / 1000] << " ns\n";
    std::cout << "Max: " << latencies.back() << " ns\n";
}

// 典型输出：
// P50: 50 ns
// P99: 200 ns
// P99.9: 5000 ns  ← 尾部延迟很高！
// Max: 50000 ns
```

---

## 二、Arena分配器

### 2.1 基本实现

```cpp
class ArenaAllocator {
private:
    char* memory_;
    size_t capacity_;
    size_t offset_;
    
public:
    explicit ArenaAllocator(size_t capacity)
        : memory_(static_cast<char*>(std::aligned_alloc(64, capacity)))
        , capacity_(capacity)
        , offset_(0) {
        if (!memory_) {
            throw std::bad_alloc();
        }
    }
    
    ~ArenaAllocator() {
        std::free(memory_);
    }
    
    void* allocate(size_t size, size_t alignment = alignof(std::max_align_t)) {
        // 对齐调整
        size_t aligned_offset = (offset_ + alignment - 1) & ~(alignment - 1);
        
        if (aligned_offset + size > capacity_) {
            return nullptr;  // 或抛出异常
        }
        
        void* ptr = memory_ + aligned_offset;
        offset_ = aligned_offset + size;
        return ptr;
    }
    
    void reset() noexcept {
        offset_ = 0;  // 简单重置，O(1)
    }
    
    // 禁止拷贝
    ArenaAllocator(const ArenaAllocator&) = delete;
    ArenaAllocator& operator=(const ArenaAllocator&) = delete;
};

// 使用
ArenaAllocator arena(1024 * 1024);  // 1MB
void* p1 = arena.allocate(100);
void* p2 = arena.allocate(200);
arena.reset();  // 一次性释放所有
```

### 2.2 线程局部Arena

```cpp
class ThreadLocalArena {
    static constexpr size_t ARENA_SIZE = 64 * 1024;  // 64KB per thread
    
    alignas(64) char buffer_[ARENA_SIZE];
    size_t offset_ = 0;
    
public:
    static ThreadLocalArena& instance() {
        thread_local ThreadLocalArena arena;
        return arena;
    }
    
    void* allocate(size_t size) noexcept {
        size_t aligned = (offset_ + 7) & ~7;  // 8字节对齐
        if (aligned + size > ARENA_SIZE) {
            return nullptr;
        }
        void* ptr = buffer_ + aligned;
        offset_ = aligned + size;
        return ptr;
    }
    
    void reset() noexcept {
        offset_ = 0;
    }
};

// 用于请求处理
void handleRequest(const Request& req) {
    auto& arena = ThreadLocalArena::instance();
    
    // 使用arena分配临时对象
    auto* order = static_cast<Order*>(arena.allocate(sizeof(Order)));
    new (order) Order(req);
    
    processOrder(order);
    
    order->~Order();
    arena.reset();  // 请求结束时重置
}
```

---

## 三、池分配器

### 3.1 固定大小池

```cpp
template<typename T, size_t PoolSize = 1024>
class PoolAllocator {
private:
    union Slot {
        T object;
        Slot* next;
        
        Slot() : next(nullptr) {}
        ~Slot() {}
    };
    
    alignas(T) char memory_[sizeof(Slot) * PoolSize];
    Slot* free_list_;
    
public:
    PoolAllocator() : free_list_(nullptr) {
        // 初始化空闲链表
        Slot* slots = reinterpret_cast<Slot*>(memory_);
        for (size_t i = 0; i < PoolSize - 1; ++i) {
            slots[i].next = &slots[i + 1];
        }
        slots[PoolSize - 1].next = nullptr;
        free_list_ = slots;
    }
    
    T* allocate() noexcept {
        if (!free_list_) return nullptr;
        
        Slot* slot = free_list_;
        free_list_ = slot->next;
        return reinterpret_cast<T*>(slot);
    }
    
    void deallocate(T* ptr) noexcept {
        Slot* slot = reinterpret_cast<Slot*>(ptr);
        slot->next = free_list_;
        free_list_ = slot;
    }
};

// HFT订单池
PoolAllocator<Order, 10000> orderPool;

Order* createOrder() {
    Order* order = orderPool.allocate();
    if (order) {
        new (order) Order();
    }
    return order;
}

void destroyOrder(Order* order) {
    order->~Order();
    orderPool.deallocate(order);
}
```

### 3.2 无锁池分配器

```cpp
#include <atomic>

template<typename T, size_t PoolSize>
class LockFreePool {
private:
    struct Node {
        T data;
        std::atomic<Node*> next;
    };
    
    alignas(64) char memory_[sizeof(Node) * PoolSize];
    alignas(64) std::atomic<Node*> free_list_;
    
public:
    LockFreePool() {
        Node* nodes = reinterpret_cast<Node*>(memory_);
        
        // 初始化空闲链表
        for (size_t i = 0; i < PoolSize - 1; ++i) {
            nodes[i].next.store(&nodes[i + 1], std::memory_order_relaxed);
        }
        nodes[PoolSize - 1].next.store(nullptr, std::memory_order_relaxed);
        free_list_.store(nodes, std::memory_order_release);
    }
    
    T* allocate() noexcept {
        Node* head = free_list_.load(std::memory_order_acquire);
        while (head) {
            Node* next = head->next.load(std::memory_order_relaxed);
            if (free_list_.compare_exchange_weak(head, next,
                    std::memory_order_release, std::memory_order_acquire)) {
                return &head->data;
            }
            // CAS失败，head已更新，重试
        }
        return nullptr;
    }
    
    void deallocate(T* ptr) noexcept {
        Node* node = reinterpret_cast<Node*>(
            reinterpret_cast<char*>(ptr) - offsetof(Node, data)
        );
        
        Node* head = free_list_.load(std::memory_order_relaxed);
        do {
            node->next.store(head, std::memory_order_relaxed);
        } while (!free_list_.compare_exchange_weak(head, node,
                    std::memory_order_release, std::memory_order_relaxed));
    }
};
```

---

## 四、STL兼容分配器

### 4.1 std::allocator接口

```cpp
template<typename T>
class HFTAllocator {
public:
    using value_type = T;
    using size_type = std::size_t;
    using difference_type = std::ptrdiff_t;
    using propagate_on_container_move_assignment = std::true_type;
    using is_always_equal = std::true_type;
    
    HFTAllocator() noexcept = default;
    
    template<typename U>
    HFTAllocator(const HFTAllocator<U>&) noexcept {}
    
    T* allocate(size_type n) {
        if (n > std::numeric_limits<size_type>::max() / sizeof(T)) {
            throw std::bad_alloc();
        }
        
        // 使用自定义分配策略
        void* p = ThreadLocalArena::instance().allocate(n * sizeof(T));
        if (!p) {
            throw std::bad_alloc();
        }
        return static_cast<T*>(p);
    }
    
    void deallocate(T* p, size_type n) noexcept {
        // Arena不需要单独释放
    }
};

// 使用
using HFTString = std::basic_string<char, std::char_traits<char>, HFTAllocator<char>>;
using HFTVector = std::vector<int, HFTAllocator<int>>;
```

### 4.2 pmr（C++17多态内存资源）

```cpp
#include <memory_resource>

// 使用栈内存
char buffer[10000];
std::pmr::monotonic_buffer_resource mbr(buffer, sizeof(buffer));
std::pmr::polymorphic_allocator<Order> alloc(&mbr);

std::pmr::vector<Order> orders(&mbr);
orders.reserve(100);

// 使用无同步池
std::pmr::unsynchronized_pool_resource pool;
std::pmr::vector<int> data(&pool);
```

---

## 五、高级技术

### 5.1 预热内存

```cpp
void warmupMemory(void* ptr, size_t size) {
    // 触发页面映射和TLB加载
    volatile char* p = static_cast<volatile char*>(ptr);
    for (size_t i = 0; i < size; i += 4096) {
        p[i] = 0;  // 每页写入一次
    }
}

// 在系统启动时预热
class TradingSystem {
public:
    TradingSystem() {
        // 预分配内存
        order_pool_ = std::aligned_alloc(64, ORDER_POOL_SIZE);
        
        // 预热
        warmupMemory(order_pool_, ORDER_POOL_SIZE);
        
        // 锁定内存（防止换出）
        mlock(order_pool_, ORDER_POOL_SIZE);
    }
};
```

### 5.2 Huge Pages

```cpp
#include <sys/mman.h>

void* allocateHugePages(size_t size) {
    // 使用2MB大页
    void* ptr = mmap(nullptr, size,
                     PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                     -1, 0);
    
    if (ptr == MAP_FAILED) {
        return nullptr;
    }
    
    // 预热
    warmupMemory(ptr, size);
    
    return ptr;
}

// 系统配置：
// echo 1024 > /proc/sys/vm/nr_hugepages
// 或在grub中添加：hugepages=1024
```

---

## 六、性能对比

```cpp
void benchmark() {
    constexpr int iterations = 1000000;
    
    // malloc
    {
        auto start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < iterations; ++i) {
            void* p = malloc(64);
            free(p);
        }
        auto end = std::chrono::high_resolution_clock::now();
        std::cout << "malloc: " << /* ... */ << " ns\n";
    }
    
    // Pool allocator
    {
        PoolAllocator<std::array<char, 64>> pool;
        auto start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < iterations; ++i) {
            auto* p = pool.allocate();
            pool.deallocate(p);
        }
        auto end = std::chrono::high_resolution_clock::now();
        std::cout << "Pool: " << /* ... */ << " ns\n";
    }
    
    // Arena (reset每1000次)
    {
        ArenaAllocator arena(1024 * 1024);
        auto start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < iterations; ++i) {
            arena.allocate(64);
            if (i % 1000 == 999) arena.reset();
        }
        auto end = std::chrono::high_resolution_clock::now();
        std::cout << "Arena: " << /* ... */ << " ns\n";
    }
}

// 典型结果：
// malloc: 50-100 ns
// Pool: 5-10 ns
// Arena: 2-5 ns
```

---

## 总结

| 分配器类型 | 延迟 | 适用场景 |
|------------|------|----------|
| malloc/new | 50-100ns | 通用 |
| Pool | 5-10ns | 固定大小对象 |
| Arena | 2-5ns | 批量分配/释放 |
| Huge Pages | 减少TLB miss | 大内存块 |

**HFT核心原则**：
1. 预分配所有需要的内存
2. 使用池分配器管理对象
3. 热路径避免任何动态分配
4. 使用Huge Pages减少TLB miss
5. 锁定内存防止换出

---

## 概念速查

- [算法与数据结构概念索引](@/articles/00-glossary/glossary-03-algorithm-concepts.md) - 对象池、内存分配等概念速查
- [HFT核心概念索引](@/articles/00-glossary/glossary-04-hft-concepts.md) - 内存管理、Huge Pages等概念速查
- [Linux核心概念索引](@/articles/00-glossary/glossary-01-linux-concepts.md) - 虚拟内存、mmap等概念速查

---

## 相关文章

- [上一篇：Exception Handling and Performance](@/articles/cpp/cpp-14-异常处理机制与性能开销.md)
- [下一篇：Smart Pointers Internals and Pitfalls](@/articles/cpp/cpp-16-智能指针底层与陷阱.md)
