+++
title = "04. Concurrency and Multithreading"
date = 2026-01-19
description = "C++多线程编程：线程管理、同步原语、原子操作、内存模型、并发容器"
[taxonomies]
tags = ["C++", "并发", "多线程"]
+++

## 线程基础

### std::thread

```cpp
#include <thread>

// 函数作为线程入口
void task() {
    std::cout << "Hello from thread" << std::endl;
}

std::thread t(task);
t.join();  // 等待线程完成

// Lambda作为线程入口
std::thread t2([]() {
    std::cout << "Lambda thread" << std::endl;
});
t2.join();

// 传递参数
void print(int id, const std::string& msg) {
    std::cout << id << ": " << msg << std::endl;
}
std::thread t3(print, 1, "hello");
t3.join();
```

### join与detach

```cpp
std::thread t(task);

// 方式1：等待完成
t.join();

// 方式2：分离（不等待）
t.detach();

// 注意：必须选择其一，否则析构时terminate
if (t.joinable()) {
    t.join();  // 或 t.detach();
}
```

### RAII线程包装

```cpp
class ThreadGuard {
    std::thread& t;
public:
    explicit ThreadGuard(std::thread& t_) : t(t_) {}
    ~ThreadGuard() {
        if (t.joinable()) {
            t.join();
        }
    }
    ThreadGuard(const ThreadGuard&) = delete;
    ThreadGuard& operator=(const ThreadGuard&) = delete;
};

// C++20 std::jthread 自动join
std::jthread t(task);  // 析构时自动join
```

### 线程ID与硬件并发

```cpp
std::thread::id main_id = std::this_thread::get_id();

std::thread t([]() {
    std::cout << "Thread ID: " << std::this_thread::get_id() << std::endl;
});

// 硬件支持的线程数
unsigned int n = std::thread::hardware_concurrency();
```

---

## 互斥量

### std::mutex

```cpp
#include <mutex>

std::mutex mtx;
int counter = 0;

void increment() {
    mtx.lock();
    counter++;
    mtx.unlock();  // 必须释放
}
```

### lock_guard（RAII）

```cpp
void increment() {
    std::lock_guard<std::mutex> lock(mtx);
    counter++;
}  // 自动释放

// C++17 类模板参数推导
std::lock_guard lock(mtx);
```

### unique_lock

```cpp
void process() {
    std::unique_lock<std::mutex> lock(mtx);
    
    // 可以手动解锁
    lock.unlock();
    // 做不需要锁的事情
    lock.lock();  // 重新加锁
    
    // 可以转移所有权
    std::unique_lock<std::mutex> lock2 = std::move(lock);
}
```

### 死锁避免

```cpp
std::mutex mtx1, mtx2;

// 错误：可能死锁
void threadA() {
    std::lock_guard<std::mutex> lock1(mtx1);
    std::lock_guard<std::mutex> lock2(mtx2);
}
void threadB() {
    std::lock_guard<std::mutex> lock2(mtx2);
    std::lock_guard<std::mutex> lock1(mtx1);
}

// 正确：std::lock同时锁定
void safe() {
    std::lock(mtx1, mtx2);  // 原子地锁定两个
    std::lock_guard<std::mutex> lock1(mtx1, std::adopt_lock);
    std::lock_guard<std::mutex> lock2(mtx2, std::adopt_lock);
}

// C++17 scoped_lock
void safe_cpp17() {
    std::scoped_lock lock(mtx1, mtx2);
}
```

### 其他互斥量

```cpp
std::timed_mutex tmtx;
if (tmtx.try_lock_for(std::chrono::seconds(1))) {
    // 获得锁
    tmtx.unlock();
}

std::recursive_mutex rmtx;  // 可递归锁定

std::shared_mutex smtx;  // 读写锁
std::shared_lock<std::shared_mutex> read_lock(smtx);   // 读锁
std::unique_lock<std::shared_mutex> write_lock(smtx);  // 写锁
```

---

## 条件变量

### 基本用法

```cpp
#include <condition_variable>

std::mutex mtx;
std::condition_variable cv;
bool ready = false;

// 等待方
void consumer() {
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock, []{ return ready; });  // 等待条件
    // 处理数据
}

// 通知方
void producer() {
    {
        std::lock_guard<std::mutex> lock(mtx);
        ready = true;
    }
    cv.notify_one();  // 通知一个等待者
    // cv.notify_all();  // 通知所有等待者
}
```

### 虚假唤醒

```cpp
// wait可能虚假唤醒，需要循环检查
cv.wait(lock, []{ return ready; });  // 推荐，自动处理

// 等价于
while (!ready) {
    cv.wait(lock);
}
```

### 生产者-消费者

```cpp
template<typename T>
class ThreadSafeQueue {
    std::queue<T> queue;
    mutable std::mutex mtx;
    std::condition_variable cv;
    
public:
    void push(T value) {
        std::lock_guard<std::mutex> lock(mtx);
        queue.push(std::move(value));
        cv.notify_one();
    }
    
    T pop() {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [this]{ return !queue.empty(); });
        T value = std::move(queue.front());
        queue.pop();
        return value;
    }
};
```

---

## 原子操作

### std::atomic

```cpp
#include <atomic>

std::atomic<int> counter{0};

void increment() {
    counter++;                  // 原子操作
    counter.fetch_add(1);       // 等价
    counter.store(10);          // 原子写
    int val = counter.load();   // 原子读
}
```

### 原子操作类型

```cpp
// 基本类型都有对应原子类型
std::atomic<int> ai;
std::atomic<bool> ab;
std::atomic<long> al;
std::atomic<void*> ap;

// 也有typedef
std::atomic_int ai;
std::atomic_bool ab;
```

### compare_exchange

```cpp
std::atomic<int> val{0};

int expected = 0;
int desired = 1;

// 如果val == expected，则val = desired，返回true
// 否则expected = val，返回false
if (val.compare_exchange_strong(expected, desired)) {
    // 交换成功
}

// weak版本可能虚假失败，需要循环
while (!val.compare_exchange_weak(expected, desired)) {
    // 重试
}
```

### 无锁数据结构

```cpp
template<typename T>
class LockFreeStack {
    struct Node {
        T data;
        Node* next;
    };
    std::atomic<Node*> head{nullptr};
    
public:
    void push(T data) {
        Node* new_node = new Node{std::move(data)};
        new_node->next = head.load();
        while (!head.compare_exchange_weak(new_node->next, new_node));
    }
    
    // pop需要处理ABA问题
};
```

---

## 内存模型

### 内存顺序

```cpp
// 顺序一致（默认，最强）
counter.store(1, std::memory_order_seq_cst);
counter.load(std::memory_order_seq_cst);

// 释放-获取
std::atomic<bool> flag{false};
int data = 0;

// 线程A
data = 42;
flag.store(true, std::memory_order_release);  // 释放

// 线程B
while (!flag.load(std::memory_order_acquire));  // 获取
assert(data == 42);  // 保证看到data=42

// 宽松（最弱）
counter.fetch_add(1, std::memory_order_relaxed);
```

### 选择指南

| 顺序 | 保证 | 性能 | 使用场景 |
|------|------|------|----------|
| seq_cst | 全序 | 最慢 | 默认，最安全 |
| acquire/release | 同步对 | 中等 | 生产者-消费者 |
| relaxed | 无 | 最快 | 独立计数器 |

---

## 异步与Future

### std::async

```cpp
#include <future>

int compute() {
    return 42;
}

// 异步执行
std::future<int> fut = std::async(std::launch::async, compute);

// 获取结果（阻塞）
int result = fut.get();

// 启动策略
std::async(std::launch::async, func);    // 新线程
std::async(std::launch::deferred, func); // 延迟到get()调用
std::async(std::launch::async | std::launch::deferred, func);  // 默认
```

### std::promise

```cpp
std::promise<int> prom;
std::future<int> fut = prom.get_future();

std::thread t([&prom]() {
    prom.set_value(42);  // 设置结果
});

int result = fut.get();  // 获取结果
t.join();
```

### std::packaged_task

```cpp
std::packaged_task<int(int, int)> task([](int a, int b) {
    return a + b;
});

std::future<int> fut = task.get_future();

std::thread t(std::move(task), 3, 4);
int result = fut.get();  // 7
t.join();
```

### 超时与等待

```cpp
std::future<int> fut = std::async(compute);

// 等待一段时间
auto status = fut.wait_for(std::chrono::seconds(1));

if (status == std::future_status::ready) {
    int result = fut.get();
} else if (status == std::future_status::timeout) {
    // 超时
} else if (status == std::future_status::deferred) {
    // 延迟执行
}
```

---

## 并行算法（C++17）

```cpp
#include <execution>
#include <algorithm>

std::vector<int> v = {5, 3, 1, 4, 2};

// 顺序执行
std::sort(std::execution::seq, v.begin(), v.end());

// 并行执行
std::sort(std::execution::par, v.begin(), v.end());

// 并行+向量化
std::sort(std::execution::par_unseq, v.begin(), v.end());

// 其他算法同样支持
std::for_each(std::execution::par, v.begin(), v.end(), [](int& x) {
    x *= 2;
});
```

---

## 总结

| 组件 | 用途 | 线程安全 |
|------|------|----------|
| std::thread | 线程管理 | - |
| std::mutex | 互斥锁 | ✓ |
| std::condition_variable | 条件等待 | 需配合mutex |
| std::atomic | 原子操作 | ✓ |
| std::future/promise | 异步结果 | ✓ |
| std::async | 异步任务 | ✓ |

**最佳实践**：
1. 优先使用高层抽象（async、parallel algorithms）
2. 使用RAII管理锁（lock_guard、scoped_lock）
3. 避免死锁（统一加锁顺序、使用scoped_lock）
4. 减少锁粒度，考虑无锁数据结构

---

## 相关文章

- [上一篇：Templates and Generic Programming](/articles/cpp/cpp-03-模板与泛型编程/)
- [下一篇：Performance Optimization](/articles/cpp/cpp-05-性能优化技术/)
