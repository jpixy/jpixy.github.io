+++
title = "Lock-Free Data Structures (HFT)"
slug = "cpp-22-HFT-Lock-Free数据结构详解"
date = 2026-01-21
weight = 17000
description = "深入剖析无锁数据结构的原理与实现，包括CAS、ABA问题、SPSC/MPMC队列、Hazard Pointer等，HFT低延迟系统核心技术"
[taxonomies]
tags = ["C++", "Lock-Free", "并发", "HFT", "低延迟", "无锁队列"]
+++

## 概述

Lock-Free数据结构是HFT系统的核心技术，避免了互斥锁的阻塞和上下文切换开销。本文深入剖析无锁编程的原理和实践。

---

## 一、Lock-Free基础

### 1.1 定义

```cpp
// Lock-Free定义：
// 如果一个线程被暂停，其他线程仍能继续执行
// 对比：
// - 阻塞（Blocking）：一个线程持有锁时，其他线程必须等待
// - 无锁（Lock-Free）：始终有线程能取得进展
// - 无等待（Wait-Free）：每个线程都能在有限步内完成
```

### 1.2 CAS（Compare-And-Swap）

```cpp
#include <atomic>

// CAS是无锁编程的基础
std::atomic<int> value{0};

bool casExample() {
    int expected = 0;
    int desired = 1;
    
    // 如果value==expected，则设置value=desired，返回true
    // 否则，expected=value（当前值），返回false
    return value.compare_exchange_strong(expected, desired);
}

// CAS循环模式
void atomicAdd(std::atomic<int>& counter, int delta) {
    int old = counter.load(std::memory_order_relaxed);
    while (!counter.compare_exchange_weak(old, old + delta,
                std::memory_order_release, std::memory_order_relaxed)) {
        // CAS失败，old已更新为当前值，继续尝试
    }
}
```

### 1.3 strong vs weak

```cpp
// compare_exchange_strong：保证不会虚假失败
// compare_exchange_weak：可能虚假失败（在某些架构上更高效）

// 使用weak的场景：在循环中
while (!counter.compare_exchange_weak(old, new_val)) {
    // 即使虚假失败也会重试
}

// 使用strong的场景：单次尝试
if (counter.compare_exchange_strong(old, new_val)) {
    // 成功
} else {
    // 确实失败了，不是虚假失败
}
```

---

## 二、ABA问题

### 2.1 问题描述

```cpp
// ABA问题示例
std::atomic<Node*> head{nodeA};

// 线程1：准备将A替换为B
Node* expected = head.load();  // A
Node* desired = nodeB;

// 线程1被中断...

// 线程2：将A替换为C，然后又替换回A
head.store(nodeC);
head.store(nodeA);  // A被释放后又重新分配了相同地址！

// 线程1继续：
head.compare_exchange_strong(expected, desired);
// CAS成功！因为head仍然是A（但已经不是原来的A了）
```

### 2.2 解决方案：带版本号的指针

```cpp
template<typename T>
struct TaggedPointer {
    T* ptr;
    uintptr_t tag;
};

// 使用128位CAS（需要硬件支持）
#include <cstdint>

struct alignas(16) AtomicTaggedPointer {
    uintptr_t ptr;
    uintptr_t tag;
};

static_assert(sizeof(AtomicTaggedPointer) == 16);

// x86-64使用cmpxchg16b指令
bool casTaggedPointer(std::atomic<AtomicTaggedPointer>& target,
                      AtomicTaggedPointer& expected,
                      AtomicTaggedPointer desired) {
    return target.compare_exchange_strong(expected, desired);
}
```

### 2.3 Hazard Pointer

```cpp
// Hazard Pointer：延迟回收机制
class HazardPointerDomain {
    static constexpr size_t MAX_HAZARDS = 100;
    std::array<std::atomic<void*>, MAX_HAZARDS> hazards_;
    
public:
    // 线程声明正在使用某个指针
    void protect(size_t index, void* ptr) {
        hazards_[index].store(ptr, std::memory_order_release);
    }
    
    // 清除保护
    void clear(size_t index) {
        hazards_[index].store(nullptr, std::memory_order_release);
    }
    
    // 检查指针是否被任何线程保护
    bool isProtected(void* ptr) {
        for (auto& hp : hazards_) {
            if (hp.load(std::memory_order_acquire) == ptr) {
                return true;
            }
        }
        return false;
    }
    
    // 安全回收
    void retire(void* ptr) {
        // 如果没有线程保护这个指针，可以安全删除
        if (!isProtected(ptr)) {
            delete static_cast<Node*>(ptr);
        } else {
            // 稍后重试
            retiredList_.push_back(ptr);
        }
    }
};
```

---

## 三、SPSC队列（单生产者单消费者）

### 3.1 基本实现

```cpp
template<typename T, size_t Capacity>
class SPSCQueue {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be power of 2");
    
    alignas(64) T buffer_[Capacity];
    alignas(64) std::atomic<size_t> write_pos_{0};
    alignas(64) std::atomic<size_t> read_pos_{0};
    
public:
    bool push(const T& item) {
        const size_t write = write_pos_.load(std::memory_order_relaxed);
        const size_t next = (write + 1) & (Capacity - 1);
        
        if (next == read_pos_.load(std::memory_order_acquire)) {
            return false;  // 满
        }
        
        buffer_[write] = item;
        write_pos_.store(next, std::memory_order_release);
        return true;
    }
    
    bool pop(T& item) {
        const size_t read = read_pos_.load(std::memory_order_relaxed);
        
        if (read == write_pos_.load(std::memory_order_acquire)) {
            return false;  // 空
        }
        
        item = buffer_[read];
        read_pos_.store((read + 1) & (Capacity - 1), std::memory_order_release);
        return true;
    }
};
```

### 3.2 优化：缓存位置

```cpp
template<typename T, size_t Capacity>
class OptimizedSPSCQueue {
    alignas(64) T buffer_[Capacity];
    
    // 生产者本地缓存
    alignas(64) std::atomic<size_t> write_pos_{0};
    size_t cached_read_pos_{0};
    
    // 消费者本地缓存
    alignas(64) std::atomic<size_t> read_pos_{0};
    size_t cached_write_pos_{0};
    
public:
    bool push(const T& item) {
        const size_t write = write_pos_.load(std::memory_order_relaxed);
        const size_t next = (write + 1) & (Capacity - 1);
        
        // 使用缓存的读位置，减少原子读
        if (next == cached_read_pos_) {
            cached_read_pos_ = read_pos_.load(std::memory_order_acquire);
            if (next == cached_read_pos_) {
                return false;
            }
        }
        
        buffer_[write] = item;
        write_pos_.store(next, std::memory_order_release);
        return true;
    }
    
    bool pop(T& item) {
        const size_t read = read_pos_.load(std::memory_order_relaxed);
        
        if (read == cached_write_pos_) {
            cached_write_pos_ = write_pos_.load(std::memory_order_acquire);
            if (read == cached_write_pos_) {
                return false;
            }
        }
        
        item = buffer_[read];
        read_pos_.store((read + 1) & (Capacity - 1), std::memory_order_release);
        return true;
    }
};
```

---

## 四、MPMC队列（多生产者多消费者）

### 4.1 基于序列号的实现

```cpp
template<typename T, size_t Capacity>
class MPMCQueue {
    struct Cell {
        std::atomic<size_t> sequence;
        T data;
    };
    
    alignas(64) Cell buffer_[Capacity];
    alignas(64) std::atomic<size_t> enqueue_pos_{0};
    alignas(64) std::atomic<size_t> dequeue_pos_{0};
    
public:
    MPMCQueue() {
        for (size_t i = 0; i < Capacity; ++i) {
            buffer_[i].sequence.store(i, std::memory_order_relaxed);
        }
    }
    
    bool push(const T& item) {
        Cell* cell;
        size_t pos = enqueue_pos_.load(std::memory_order_relaxed);
        
        for (;;) {
            cell = &buffer_[pos & (Capacity - 1)];
            size_t seq = cell->sequence.load(std::memory_order_acquire);
            intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos);
            
            if (diff == 0) {
                if (enqueue_pos_.compare_exchange_weak(pos, pos + 1,
                        std::memory_order_relaxed)) {
                    break;
                }
            } else if (diff < 0) {
                return false;  // 队列满
            } else {
                pos = enqueue_pos_.load(std::memory_order_relaxed);
            }
        }
        
        cell->data = item;
        cell->sequence.store(pos + 1, std::memory_order_release);
        return true;
    }
    
    bool pop(T& item) {
        Cell* cell;
        size_t pos = dequeue_pos_.load(std::memory_order_relaxed);
        
        for (;;) {
            cell = &buffer_[pos & (Capacity - 1)];
            size_t seq = cell->sequence.load(std::memory_order_acquire);
            intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos + 1);
            
            if (diff == 0) {
                if (dequeue_pos_.compare_exchange_weak(pos, pos + 1,
                        std::memory_order_relaxed)) {
                    break;
                }
            } else if (diff < 0) {
                return false;  // 队列空
            } else {
                pos = dequeue_pos_.load(std::memory_order_relaxed);
            }
        }
        
        item = cell->data;
        cell->sequence.store(pos + Capacity, std::memory_order_release);
        return true;
    }
};
```

---

## 五、无锁栈

```cpp
template<typename T>
class LockFreeStack {
    struct Node {
        T data;
        Node* next;
        
        Node(const T& d) : data(d), next(nullptr) {}
    };
    
    std::atomic<Node*> head_{nullptr};
    
public:
    void push(const T& data) {
        Node* new_node = new Node(data);
        new_node->next = head_.load(std::memory_order_relaxed);
        
        while (!head_.compare_exchange_weak(new_node->next, new_node,
                std::memory_order_release, std::memory_order_relaxed)) {
            // CAS失败，new_node->next已更新
        }
    }
    
    bool pop(T& result) {
        Node* old_head = head_.load(std::memory_order_relaxed);
        
        while (old_head) {
            if (head_.compare_exchange_weak(old_head, old_head->next,
                    std::memory_order_acquire, std::memory_order_relaxed)) {
                result = old_head->data;
                // 注意：这里有内存泄漏风险，需要使用Hazard Pointer或引用计数
                delete old_head;
                return true;
            }
        }
        return false;
    }
};
```

---

## 六、性能测试

```cpp
void benchmarkQueues() {
    constexpr int iterations = 10'000'000;
    
    // SPSC队列
    {
        SPSCQueue<int, 65536> queue;
        
        std::thread producer([&]() {
            for (int i = 0; i < iterations; ++i) {
                while (!queue.push(i)) {}
            }
        });
        
        std::thread consumer([&]() {
            int value;
            for (int i = 0; i < iterations; ++i) {
                while (!queue.pop(value)) {}
            }
        });
        
        auto start = std::chrono::high_resolution_clock::now();
        producer.join();
        consumer.join();
        auto end = std::chrono::high_resolution_clock::now();
        
        auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
        std::cout << "SPSC: " << ns / iterations << " ns/op\n";
    }
}

// 典型结果：
// SPSC: 10-30 ns/op
// MPMC: 50-100 ns/op
// std::mutex + std::queue: 100-500 ns/op
```

---

## 总结

| 数据结构 | 延迟 | 复杂度 | 适用场景 |
|----------|------|--------|----------|
| SPSC Queue | 10-30ns | 低 | 单生产者单消费者 |
| MPSC Queue | 30-50ns | 中 | 多生产者单消费者 |
| MPMC Queue | 50-100ns | 高 | 通用 |
| Lock-Free Stack | 30-50ns | 中 | LIFO场景 |

**HFT核心原则**：
1. 优先使用SPSC队列
2. 避免ABA问题
3. 使用适当的memory order
4. Cache Line对齐避免False Sharing
5. 考虑使用Hazard Pointer管理内存

---

## 概念速查

- [算法与数据结构概念索引](@/articles/00-glossary/glossary-03-algorithm-concepts.md) - 无锁队列、CAS、ABA问题等概念速查
- [C++核心概念索引](@/articles/00-glossary/glossary-05-cpp-concepts.md) - 内存序、原子操作等C++概念速查
- [HFT核心概念索引](@/articles/00-glossary/glossary-04-hft-concepts.md) - 低延迟系统设计概念速查

---

## 相关文章

- [上一篇：Smart Pointers Internals and Pitfalls](@/articles/cpp/cpp-16-智能指针底层与陷阱.md)
- [下一篇：SIMD Programming (HFT)](@/articles/cpp/cpp-18-HFT-SIMD编程详解.md)
