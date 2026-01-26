+++
title = "43.C++协程与用户态调度"
slug = "cpp-43-C++协程与用户态调度"
date = 2026-01-21
description = "深入剖析C++20协程机制和用户态调度技术，包括协程原理、Fiber库、调度器设计以及在HFT中的应用"
[taxonomies]
tags = ["C++", "协程", "Fiber", "调度器", "并发", "HFT"]
+++

## 概述

协程提供了一种轻量级的并发机制，避免了线程的高开销。本文深入剖析C++20协程和用户态调度技术在高性能系统中的应用。

---

## 一、协程基础概念

### 1.1 协程 vs 线程

```
┌────────────────────────────────────────────────────────────┐
│                        对比                                 │
├──────────────┬──────────────────┬──────────────────────────┤
│              │      线程         │        协程              │
├──────────────┼──────────────────┼──────────────────────────┤
│ 调度         │ 操作系统（抢占式） │ 用户态（协作式）          │
│ 创建开销     │ ~1-10µs          │ ~100ns                   │
│ 栈大小       │ ~1MB-8MB         │ 几KB或无栈               │
│ 上下文切换   │ ~1-10µs          │ ~10-100ns                │
│ 数量限制     │ 数千             │ 数百万                    │
│ 同步         │ 需要锁           │ 单线程无需锁              │
└──────────────┴──────────────────┴──────────────────────────┘
```

### 1.2 协程类型

```
有栈协程（Stackful）：
- 每个协程有独立栈
- 可以在任意位置挂起
- 代表：Boost.Fiber, libco
- 栈大小通常4KB-64KB

无栈协程（Stackless）：
- 状态存储在堆对象中
- 只能在特定点挂起（co_await）
- 代表：C++20 coroutines, Python generators
- 状态对象通常更小
```

---

## 二、C++20协程详解

### 2.1 三个关键字

```cpp
#include <coroutine>

// co_await: 挂起协程，等待结果
Task<int> asyncRead() {
    auto data = co_await socket.read();  // 挂起，等待读取完成
    co_return data.size();
}

// co_yield: 产出值并挂起
Generator<int> range(int start, int end) {
    for (int i = start; i < end; ++i) {
        co_yield i;  // 产出i并挂起
    }
}

// co_return: 返回值并结束
Task<std::string> fetchData() {
    auto result = co_await download();
    co_return result;  // 返回并结束协程
}
```

### 2.2 协程组件

```cpp
// 协程的三个组成部分：

// 1. Promise Type: 定义协程行为
struct MyPromise {
    MyCoroutine get_return_object();
    std::suspend_never initial_suspend();   // 开始时是否挂起
    std::suspend_always final_suspend() noexcept;  // 结束时是否挂起
    void return_value(int value);           // co_return的处理
    void unhandled_exception();             // 异常处理
};

// 2. Coroutine Handle: 控制协程
std::coroutine_handle<MyPromise> handle;
handle.resume();   // 恢复执行
handle.done();     // 检查是否完成
handle.destroy();  // 销毁协程

// 3. Awaiter: 定义等待行为
struct MyAwaiter {
    bool await_ready();                      // 是否需要挂起
    void await_suspend(std::coroutine_handle<>);  // 挂起时的操作
    T await_resume();                        // 恢复后返回值
};
```

### 2.3 完整示例：Task

```cpp
#include <coroutine>
#include <optional>
#include <exception>

template<typename T>
class Task {
public:
    struct promise_type {
        std::optional<T> result;
        std::exception_ptr exception;
        
        Task get_return_object() {
            return Task{
                std::coroutine_handle<promise_type>::from_promise(*this)
            };
        }
        
        std::suspend_never initial_suspend() { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        
        void return_value(T value) {
            result = std::move(value);
        }
        
        void unhandled_exception() {
            exception = std::current_exception();
        }
    };
    
private:
    std::coroutine_handle<promise_type> handle_;
    
public:
    Task(std::coroutine_handle<promise_type> h) : handle_(h) {}
    
    ~Task() {
        if (handle_) handle_.destroy();
    }
    
    // Move only
    Task(Task&& other) noexcept : handle_(other.handle_) {
        other.handle_ = nullptr;
    }
    
    T get() {
        if (handle_.promise().exception) {
            std::rethrow_exception(handle_.promise().exception);
        }
        return *handle_.promise().result;
    }
};
```

### 2.4 Generator实现

```cpp
template<typename T>
class Generator {
public:
    struct promise_type {
        T current_value;
        
        Generator get_return_object() {
            return Generator{
                std::coroutine_handle<promise_type>::from_promise(*this)
            };
        }
        
        std::suspend_always initial_suspend() { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        
        std::suspend_always yield_value(T value) {
            current_value = value;
            return {};
        }
        
        void return_void() {}
        void unhandled_exception() { std::terminate(); }
    };
    
private:
    std::coroutine_handle<promise_type> handle_;
    
public:
    Generator(std::coroutine_handle<promise_type> h) : handle_(h) {}
    ~Generator() { if (handle_) handle_.destroy(); }
    
    // 迭代器支持
    class iterator {
        std::coroutine_handle<promise_type> handle_;
    public:
        iterator(std::coroutine_handle<promise_type> h = nullptr) : handle_(h) {}
        
        iterator& operator++() {
            handle_.resume();
            if (handle_.done()) handle_ = nullptr;
            return *this;
        }
        
        T& operator*() { return handle_.promise().current_value; }
        bool operator!=(const iterator& other) const {
            return handle_ != other.handle_;
        }
    };
    
    iterator begin() {
        handle_.resume();
        return handle_.done() ? end() : iterator{handle_};
    }
    
    iterator end() { return iterator{nullptr}; }
};

// 使用
Generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        auto next = a + b;
        a = b;
        b = next;
    }
}

// 打印前10个Fibonacci数
int main() {
    int count = 0;
    for (int n : fibonacci()) {
        std::cout << n << " ";
        if (++count == 10) break;
    }
}
```

---

## 三、协程性能

### 3.1 开销分析

```cpp
#include <benchmark/benchmark.h>

// 普通函数调用
int regularFunction(int x) {
    return x + 1;
}

// 协程
Task<int> coroutineFunction(int x) {
    co_return x + 1;
}

static void BM_RegularFunction(benchmark::State& state) {
    for (auto _ : state) {
        benchmark::DoNotOptimize(regularFunction(42));
    }
}

static void BM_Coroutine(benchmark::State& state) {
    for (auto _ : state) {
        auto task = coroutineFunction(42);
        benchmark::DoNotOptimize(task.get());
    }
}

// 结果：
// BM_RegularFunction:  ~1 ns
// BM_Coroutine:        ~50-100 ns（包含堆分配）
```

### 3.2 优化协程分配

```cpp
// 使用自定义分配器避免堆分配
template<size_t N>
class StackAllocator {
    alignas(16) char buffer_[N];
    size_t offset_ = 0;
    
public:
    void* allocate(size_t size) {
        size = (size + 15) & ~15;  // 对齐
        if (offset_ + size > N) return nullptr;
        void* p = buffer_ + offset_;
        offset_ += size;
        return p;
    }
    
    void deallocate(void*, size_t) {
        // 栈分配器，不需要释放
    }
};

// 在promise_type中使用
struct promise_type {
    static thread_local StackAllocator<1024*1024> allocator;
    
    void* operator new(size_t size) {
        if (void* p = allocator.allocate(size)) {
            return p;
        }
        return ::operator new(size);
    }
    
    void operator delete(void* p, size_t size) {
        // 由分配器管理
    }
};
```

---

## 四、Boost.Fiber

### 4.1 基本使用

```cpp
#include <boost/fiber/all.hpp>

namespace fibers = boost::fibers;

void fiberFunction() {
    std::cout << "Fiber 1" << std::endl;
    fibers::this_fiber::yield();  // 让出执行权
    std::cout << "Fiber 1 resumed" << std::endl;
}

int main() {
    fibers::fiber f1(fiberFunction);
    fibers::fiber f2([]{
        std::cout << "Fiber 2" << std::endl;
    });
    
    f1.join();
    f2.join();
}
```

### 4.2 Fiber通道

```cpp
#include <boost/fiber/all.hpp>

namespace fibers = boost::fibers;

void producer(fibers::buffered_channel<int>& chan) {
    for (int i = 0; i < 10; ++i) {
        chan.push(i);
        fibers::this_fiber::yield();
    }
    chan.close();
}

void consumer(fibers::buffered_channel<int>& chan) {
    int value;
    while (chan.pop(value) == fibers::channel_op_status::success) {
        std::cout << "Received: " << value << std::endl;
    }
}

int main() {
    fibers::buffered_channel<int> chan{16};
    
    fibers::fiber prod(producer, std::ref(chan));
    fibers::fiber cons(consumer, std::ref(chan));
    
    prod.join();
    cons.join();
}
```

### 4.3 自定义调度器

```cpp
#include <boost/fiber/all.hpp>
#include <boost/fiber/algo/round_robin.hpp>

namespace fibers = boost::fibers;

class PriorityScheduler : public fibers::algo::algorithm {
    std::deque<fibers::context*> high_priority_;
    std::deque<fibers::context*> low_priority_;
    
public:
    void awakened(fibers::context* ctx) noexcept override {
        // 根据属性分配到不同队列
        if (ctx->get_properties().is_high_priority()) {
            high_priority_.push_back(ctx);
        } else {
            low_priority_.push_back(ctx);
        }
    }
    
    fibers::context* pick_next() noexcept override {
        // 优先选择高优先级
        if (!high_priority_.empty()) {
            auto* ctx = high_priority_.front();
            high_priority_.pop_front();
            return ctx;
        }
        if (!low_priority_.empty()) {
            auto* ctx = low_priority_.front();
            low_priority_.pop_front();
            return ctx;
        }
        return nullptr;
    }
    
    bool has_ready_fibers() const noexcept override {
        return !high_priority_.empty() || !low_priority_.empty();
    }
    
    void suspend_until(std::chrono::steady_clock::time_point const& tp) noexcept override {
        std::this_thread::sleep_until(tp);
    }
    
    void notify() noexcept override {
        // 唤醒调度器
    }
};

// 安装调度器
fibers::use_scheduling_algorithm<PriorityScheduler>();
```

---

## 五、HFT协程应用

### 5.1 协程 vs 回调

```cpp
// 回调风格（复杂）
void processOrder(Order order, 
                  std::function<void(Result)> callback) {
    validateAsync(order, [=](bool valid) {
        if (!valid) {
            callback({Error::InvalidOrder});
            return;
        }
        checkRiskAsync(order, [=](bool passed) {
            if (!passed) {
                callback({Error::RiskFailed});
                return;
            }
            submitAsync(order, [=](Result result) {
                callback(result);
            });
        });
    });
}

// 协程风格（清晰）
Task<Result> processOrder(Order order) {
    if (!co_await validateAsync(order)) {
        co_return {Error::InvalidOrder};
    }
    if (!co_await checkRiskAsync(order)) {
        co_return {Error::RiskFailed};
    }
    co_return co_await submitAsync(order);
}
```

### 5.2 低延迟注意事项

```cpp
// HFT热路径：避免协程开销
void hotPath(const Message& msg) {
    // 同步处理，无协程
    auto result = process(msg);
    send(result);
}

// 非关键路径：可以使用协程
Task<void> coldPath() {
    auto config = co_await loadConfig();
    auto stats = co_await calculateStats();
    co_await saveReport(stats);
}

// 混合策略
class OrderHandler {
public:
    // 热路径：同步
    void onMarketData(const MarketData& data) {
        updateBook(data);
        checkSignals();
    }
    
    // 冷路径：异步
    Task<void> onDailySettle() {
        co_await reconcile();
        co_await generateReports();
    }
};
```

### 5.3 IO多路复用

```cpp
// 结合io_uring和协程
class AsyncSocket {
    int fd_;
    io_uring* ring_;
    
public:
    struct ReadAwaiter {
        AsyncSocket* socket;
        void* buffer;
        size_t size;
        ssize_t result;
        std::coroutine_handle<> continuation;
        
        bool await_ready() { return false; }
        
        void await_suspend(std::coroutine_handle<> h) {
            continuation = h;
            
            // 提交io_uring请求
            auto* sqe = io_uring_get_sqe(socket->ring_);
            io_uring_prep_read(sqe, socket->fd_, buffer, size, 0);
            io_uring_sqe_set_data(sqe, this);
            io_uring_submit(socket->ring_);
        }
        
        ssize_t await_resume() { return result; }
    };
    
    ReadAwaiter read(void* buffer, size_t size) {
        return {this, buffer, size};
    }
    
    // 完成处理
    void handleCompletion(io_uring_cqe* cqe) {
        auto* awaiter = static_cast<ReadAwaiter*>(
            io_uring_cqe_get_data(cqe)
        );
        awaiter->result = cqe->res;
        awaiter->continuation.resume();
    }
};
```

---

## 六、调度器设计

### 6.1 简单调度器

```cpp
class SimpleScheduler {
    std::queue<std::coroutine_handle<>> ready_queue_;
    
public:
    void schedule(std::coroutine_handle<> h) {
        ready_queue_.push(h);
    }
    
    void run() {
        while (!ready_queue_.empty()) {
            auto h = ready_queue_.front();
            ready_queue_.pop();
            
            if (!h.done()) {
                h.resume();
            }
        }
    }
};

// 全局调度器
inline SimpleScheduler scheduler;

// Awaiter使用调度器
struct ScheduleAwaiter {
    bool await_ready() { return false; }
    void await_suspend(std::coroutine_handle<> h) {
        scheduler.schedule(h);
    }
    void await_resume() {}
};
```

### 6.2 工作窃取调度器

```cpp
class WorkStealingScheduler {
    struct Worker {
        std::deque<std::coroutine_handle<>> local_queue;
        std::mutex mutex;
    };
    
    std::vector<Worker> workers_;
    std::atomic<size_t> active_workers_{0};
    
public:
    WorkStealingScheduler(size_t num_workers) 
        : workers_(num_workers) {}
    
    void schedule(size_t worker_id, std::coroutine_handle<> h) {
        auto& worker = workers_[worker_id];
        std::lock_guard lock(worker.mutex);
        worker.local_queue.push_back(h);
    }
    
    std::coroutine_handle<> steal(size_t thief_id) {
        for (size_t i = 0; i < workers_.size(); ++i) {
            if (i == thief_id) continue;
            
            auto& victim = workers_[i];
            std::lock_guard lock(victim.mutex);
            
            if (!victim.local_queue.empty()) {
                auto h = victim.local_queue.front();
                victim.local_queue.pop_front();
                return h;
            }
        }
        return nullptr;
    }
    
    void run_worker(size_t id) {
        while (active_workers_ > 0) {
            std::coroutine_handle<> h = nullptr;
            
            {
                auto& worker = workers_[id];
                std::lock_guard lock(worker.mutex);
                if (!worker.local_queue.empty()) {
                    h = worker.local_queue.back();
                    worker.local_queue.pop_back();
                }
            }
            
            if (!h) {
                h = steal(id);
            }
            
            if (h && !h.done()) {
                h.resume();
            }
        }
    }
};
```

---

## 总结

| 技术 | 开销 | 适用场景 |
|------|------|----------|
| C++20协程 | ~50-100ns | IO密集型 |
| Boost.Fiber | ~100-500ns | 有栈协程需求 |
| 线程 | ~1-10µs | CPU密集型 |

**HFT协程使用原则**：
1. 热路径避免协程（使用同步代码）
2. 冷路径可以使用协程简化逻辑
3. 自定义分配器减少堆分配
4. 配合io_uring实现零拷贝IO
5. 单线程协程避免锁开销
