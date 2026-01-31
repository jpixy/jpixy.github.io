+++
title = "44.C++面试题-并发与多线程"
date = 2026-01-31
description = "C++并发与多线程面试题：线程、互斥量、原子操作、内存模型深度解析"
[taxonomies]
tags = ["C++", "面试", "并发", "多线程", "原子操作"]
+++

# C++ 面试题 - 并发与多线程

本文深入探讨 C++ 并发与多线程的核心面试题，采用问答深挖形式，模拟真实面试场景。每个问题包含标准答案、面试官追问、完整代码示例、常见错误和最佳实践。

---

## 一、std::thread 的使用和注意事项

### Q1: 请介绍一下 std::thread 的基本用法，以及创建线程时需要注意什么？

**标准答案：**

`std::thread` 是 C++11 引入的线程类，用于创建和管理线程。基本用法包括：

1. **创建线程的三种方式**：
   - 函数指针
   - Lambda 表达式
   - 成员函数

2. **关键注意事项**：
   - 线程对象必须调用 `join()` 或 `detach()`，否则析构时会调用 `std::terminate()`
   - `std::thread` 不可拷贝，只能移动
   - 线程函数参数按值传递，需要引用时使用 `std::ref()`

**完整代码示例：**

```cpp
#include <thread>
#include <iostream>
#include <vector>
#include <functional>

// 1. 普通函数
void threadFunc(int id, const std::string& name) {
    std::cout << "Thread " << id << ": " << name << std::endl;
}

// 2. Lambda 表达式
void createLambdaThread() {
    std::thread t([](int x) {
        std::cout << "Lambda thread: " << x << std::endl;
    }, 42);
    t.join();
}

// 3. 成员函数
class Worker {
public:
    void doWork(int id) {
        std::cout << "Worker " << id << " is working" << std::endl;
    }
    
    static void staticWork(int id) {
        std::cout << "Static worker " << id << std::endl;
    }
};

void createMemberThread() {
    Worker w;
    std::thread t1(&Worker::doWork, &w, 1);  // 成员函数需要对象指针
    std::thread t2(&Worker::staticWork, 2);  // 静态函数不需要对象
    t1.join();
    t2.join();
}

// 4. 参数传递
void parameterPassing() {
    int value = 100;
    std::string str = "Hello";
    
    // 按值传递
    std::thread t1(threadFunc, 1, str);  // str 被拷贝
    
    // 按引用传递（需要使用 std::ref）
    std::thread t2([](int& v) {
        v = 200;
    }, std::ref(value));  // 传递引用
    
    t1.join();
    t2.join();
    
    std::cout << "Value after thread: " << value << std::endl;  // 200
}

// 5. 线程移动
void threadMove() {
    std::thread t1([]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    });
    
    // std::thread t2 = t1;  // 错误：不可拷贝
    std::thread t2 = std::move(t1);  // 正确：可以移动
    
    if (!t1.joinable()) {
        std::cout << "t1 is no longer associated with a thread" << std::endl;
    }
    
    t2.join();
}

// 6. 线程 ID
void threadId() {
    std::thread t([]() {
        std::cout << "Thread ID: " << std::this_thread::get_id() << std::endl;
    });
    
    std::cout << "Main thread ID: " << std::this_thread::get_id() << std::endl;
    std::cout << "Created thread ID: " << t.get_id() << std::endl;
    
    t.join();
}

// 7. 必须 join 或 detach
void mustJoinOrDetach() {
    std::thread t([]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        std::cout << "Thread finished" << std::endl;
    });
    
    // 方式1：等待线程完成
    t.join();
    
    // 方式2：分离线程（不等待）
    // t.detach();
    
    // 错误：既不 join 也不 detach
    // 线程对象析构时会调用 std::terminate()
}

// 8. 异常安全的线程管理
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

void exceptionSafe() {
    std::thread t([]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    });
    
    ThreadGuard guard(t);  // RAII：即使抛异常也会 join
    
    // 可能抛异常的操作
    // throw std::runtime_error("error");
}
```

**面试官追问 1：如果线程函数抛出异常，会发生什么？**

**答案：**

线程函数中的异常不会自动传播到创建线程的代码中。如果线程函数抛出未捕获的异常，会调用 `std::terminate()`。

```cpp
void exceptionInThread() {
    std::thread t([]() {
        throw std::runtime_error("Exception in thread");
        // 未捕获的异常会导致 std::terminate()
    });
    
    t.join();
    // 即使 join，也无法捕获线程中的异常
}

// 解决方案：在线程函数内部捕获异常
void safeThread() {
    std::exception_ptr eptr;
    
    std::thread t([&eptr]() {
        try {
            throw std::runtime_error("Exception in thread");
        } catch (...) {
            eptr = std::current_exception();
        }
    });
    
    t.join();
    
    if (eptr) {
        try {
            std::rethrow_exception(eptr);
        } catch (const std::exception& e) {
            std::cout << "Caught: " << e.what() << std::endl;
        }
    }
}
```

**面试官追问 2：std::thread 和 pthread 有什么区别？**

**答案：**

| 特性 | std::thread | pthread |
|------|-------------|---------|
| 标准 | C++11 标准库 | POSIX 标准 |
| 类型安全 | 是（模板） | 否（void*） |
| 跨平台 | 是（编译器支持） | 主要是 Unix/Linux |
| 资源管理 | RAII（自动管理） | 手动管理 |
| 异常安全 | 是 | 需要手动处理 |
| 性能 | 可能略慢（封装） | 直接系统调用 |

**常见错误和最佳实践：**

**常见错误：**
1. ❌ 忘记 join 或 detach
2. ❌ 试图拷贝 std::thread
3. ❌ 传递局部变量的引用（生命周期问题）
4. ❌ 在线程函数中抛出未捕获的异常

**最佳实践：**
1. ✅ 始终使用 RAII 管理线程（如 ThreadGuard）
2. ✅ 优先使用 `std::async` 进行简单的异步任务
3. ✅ 使用线程池管理大量线程
4. ✅ 在线程函数内部捕获所有异常

---

## 二、互斥量（mutex）和锁（lock_guard、unique_lock、scoped_lock）

### Q2: 请详细说明 C++ 中各种互斥量和锁的区别，以及它们的适用场景。

**标准答案：**

C++ 提供了多种互斥量和锁类型，每种都有其特定用途：

**互斥量类型：**
1. `std::mutex`：基本互斥锁，不可递归
2. `std::recursive_mutex`：可递归互斥锁
3. `std::timed_mutex`：带超时的互斥锁
4. `std::recursive_timed_mutex`：可递归且带超时
5. `std::shared_mutex`（C++17）：读写锁

**锁类型：**
1. `std::lock_guard`：简单的 RAII 锁，构造时加锁，析构时解锁
2. `std::unique_lock`：更灵活的锁，可以手动加锁/解锁，支持延迟加锁
3. `std::scoped_lock`（C++17）：可以同时锁定多个互斥量，避免死锁

**完整代码示例：**

```cpp
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <chrono>
#include <iostream>

// 1. std::mutex 基本用法
std::mutex mtx;
int shared_data = 0;

void incrementWithMutex() {
    for (int i = 0; i < 100000; ++i) {
        std::lock_guard<std::mutex> lock(mtx);  // RAII
        ++shared_data;
    }
}

// 2. lock_guard vs unique_lock
void lockComparison() {
    std::mutex mtx;
    
    // lock_guard：简单场景
    {
        std::lock_guard<std::mutex> lock(mtx);
        // 临界区
        // 自动解锁
    }
    
    // unique_lock：需要灵活控制
    {
        std::unique_lock<std::mutex> lock(mtx);
        // 可以手动解锁
        lock.unlock();
        // 做一些不需要锁的操作
        lock.lock();
        // 再次加锁
    }
    
    // unique_lock：延迟加锁
    std::unique_lock<std::mutex> lock(mtx, std::defer_lock);
    // 此时未加锁
    lock.lock();  // 手动加锁
}

// 3. recursive_mutex：递归锁
std::recursive_mutex rmtx;

void recursiveFunction(int depth) {
    std::lock_guard<std::recursive_mutex> lock(rmtx);
    
    if (depth > 0) {
        recursiveFunction(depth - 1);  // 可以递归调用
    }
}

// 4. timed_mutex：带超时
std::timed_mutex tmtx;

void tryLockWithTimeout() {
    std::unique_lock<std::timed_mutex> lock(tmtx, std::defer_lock);
    
    // 尝试加锁，最多等待 100ms
    if (lock.try_lock_for(std::chrono::milliseconds(100))) {
        // 成功获取锁
        std::cout << "Lock acquired" << std::endl;
    } else {
        // 超时
        std::cout << "Failed to acquire lock" << std::endl;
    }
    
    // 或使用绝对时间
    auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(100);
    if (lock.try_lock_until(deadline)) {
        // ...
    }
}

// 5. shared_mutex：读写锁
std::shared_mutex smtx;
int read_count = 0;

void reader(int id) {
    std::shared_lock<std::shared_mutex> lock(smtx);  // 共享锁（读锁）
    std::cout << "Reader " << id << " reading: " << read_count << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
}

void writer(int id) {
    std::unique_lock<std::shared_mutex> lock(smtx);  // 独占锁（写锁）
    ++read_count;
    std::cout << "Writer " << id << " writing: " << read_count << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
}

// 6. scoped_lock：多锁同时加锁（C++17）
std::mutex mtx1, mtx2;

void multiLock() {
    // 传统方式：可能死锁
    // mtx1.lock();
    // mtx2.lock();  // 如果另一个线程先锁 mtx2 再锁 mtx1，可能死锁
    
    // scoped_lock：自动避免死锁
    std::scoped_lock lock(mtx1, mtx2);  // 同时加锁，自动排序避免死锁
    // 临界区
}

// 7. std::lock：手动多锁加锁
void manualMultiLock() {
    std::unique_lock<std::mutex> lock1(mtx1, std::defer_lock);
    std::unique_lock<std::mutex> lock2(mtx2, std::defer_lock);
    
    std::lock(lock1, lock2);  // 同时加锁，避免死锁
    // 或使用 std::lock(mtx1, mtx2);
    // 然后 std::lock_guard<std::mutex> guard1(mtx1, std::adopt_lock);
    //      std::lock_guard<std::mutex> guard2(mtx2, std::adopt_lock);
}
```

**面试官追问 1：lock_guard 和 unique_lock 的性能差异如何？**

**答案：**

`lock_guard` 更轻量，性能略好；`unique_lock` 功能更丰富但开销稍大。

```cpp
// lock_guard：无额外开销，只存储互斥量引用
std::lock_guard<std::mutex> lock(mtx);  // 大小：通常 8 字节（64位）

// unique_lock：需要存储锁状态，开销更大
std::unique_lock<std::mutex> lock(mtx);  // 大小：通常 16-24 字节

// 性能测试
void performanceTest() {
    std::mutex mtx;
    const int iterations = 1000000;
    
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        std::lock_guard<std::mutex> lock(mtx);
        // 空操作
    }
    auto end = std::chrono::high_resolution_clock::now();
    
    // lock_guard 通常比 unique_lock 快 5-10%
    // 但在实际应用中差异可忽略
}
```

**面试官追问 2：什么时候应该使用 shared_mutex？**

**答案：**

`shared_mutex` 适用于读多写少的场景，可以显著提升并发性能。

```cpp
// 场景：配置类（读多写少）
class Config {
    std::shared_mutex mtx_;
    std::map<std::string, std::string> config_;
    
public:
    // 读操作：使用共享锁，多个线程可以同时读
    std::string get(const std::string& key) const {
        std::shared_lock<std::shared_mutex> lock(mtx_);
        auto it = config_.find(key);
        return it != config_.end() ? it->second : "";
    }
    
    // 写操作：使用独占锁，互斥
    void set(const std::string& key, const std::string& value) {
        std::unique_lock<std::shared_mutex> lock(mtx_);
        config_[key] = value;
    }
};

// 性能对比
// 纯 mutex：所有操作互斥，读操作也会阻塞
// shared_mutex：读操作可以并发，只有写操作互斥
// 在读多写少场景下，shared_mutex 性能可提升数倍
```

**常见错误和最佳实践：**

**常见错误：**
1. ❌ 手动 lock/unlock 忘记 unlock（应使用 RAII）
2. ❌ 多个互斥量加锁顺序不一致导致死锁
3. ❌ 在持有锁时调用可能阻塞的函数
4. ❌ 使用 recursive_mutex 掩盖设计问题

**最佳实践：**
1. ✅ 优先使用 `lock_guard`，需要灵活性时用 `unique_lock`
2. ✅ 多锁场景使用 `scoped_lock`（C++17）
3. ✅ 读多写少使用 `shared_mutex`
4. ✅ 保持锁的粒度尽可能小
5. ✅ 避免在持有锁时进行耗时操作

---

## 三、条件变量的正确使用方式

### Q3: 请解释条件变量的工作原理，并说明如何正确使用条件变量实现生产者-消费者模式。

**标准答案：**

条件变量（`std::condition_variable`）用于线程间的同步，允许线程等待某个条件成立。它必须与互斥量配合使用。

**工作原理：**
1. 线程在互斥量保护下检查条件
2. 如果条件不满足，调用 `wait()` 释放锁并阻塞
3. 其他线程修改条件后调用 `notify_one()` 或 `notify_all()` 唤醒等待线程
4. 被唤醒的线程重新获取锁并检查条件

**完整代码示例：**

```cpp
#include <condition_variable>
#include <mutex>
#include <queue>
#include <thread>
#include <iostream>

// 1. 基本用法：等待条件
std::mutex mtx;
std::condition_variable cv;
bool ready = false;

void waiter() {
    std::unique_lock<std::mutex> lock(mtx);
    
    // 方式1：使用谓词（推荐）
    cv.wait(lock, []{ return ready; });
    // 等价于：
    // while (!ready) {
    //     cv.wait(lock);
    // }
    
    std::cout << "Condition is ready!" << std::endl;
}

void notifier() {
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    {
        std::lock_guard<std::mutex> lock(mtx);
        ready = true;
    }
    cv.notify_one();  // 或 cv.notify_all()
}

// 2. 生产者-消费者队列（正确实现）
template<typename T>
class ThreadSafeQueue {
private:
    std::queue<T> queue_;
    mutable std::mutex mtx_;
    std::condition_variable cv_not_empty_;
    std::condition_variable cv_not_full_;
    size_t max_size_;
    
public:
    explicit ThreadSafeQueue(size_t max_size = std::numeric_limits<size_t>::max())
        : max_size_(max_size) {}
    
    void push(const T& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        
        // 等待队列不满
        cv_not_full_.wait(lock, [this] {
            return queue_.size() < max_size_;
        });
        
        queue_.push(item);
        cv_not_empty_.notify_one();  // 通知消费者
    }
    
    bool try_pop(T& item) {
        std::lock_guard<std::mutex> lock(mtx_);
        if (queue_.empty()) {
            return false;
        }
        item = queue_.front();
        queue_.pop();
        cv_not_full_.notify_one();  // 通知生产者
        return true;
    }
    
    void pop(T& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        
        // 等待队列不空
        cv_not_empty_.wait(lock, [this] {
            return !queue_.empty();
        });
        
        item = queue_.front();
        queue_.pop();
        cv_not_full_.notify_one();  // 通知生产者
    }
    
    bool empty() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return queue_.empty();
    }
    
    size_t size() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return queue_.size();
    }
};

// 3. 使用示例
void producerConsumerExample() {
    ThreadSafeQueue<int> queue(10);
    
    // 生产者
    std::thread producer([&queue]() {
        for (int i = 0; i < 100; ++i) {
            queue.push(i);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    });
    
    // 消费者
    std::thread consumer([&queue]() {
        int item;
        for (int i = 0; i < 100; ++i) {
            queue.pop(item);
            std::cout << "Consumed: " << item << std::endl;
        }
    });
    
    producer.join();
    consumer.join();
}

// 4. 带超时的等待
void waitWithTimeout() {
    std::mutex mtx;
    std::condition_variable cv;
    bool ready = false;
    
    std::unique_lock<std::mutex> lock(mtx);
    
    // 等待最多 1 秒
    if (cv.wait_for(lock, std::chrono::seconds(1), []{ return ready; })) {
        std::cout << "Condition met" << std::endl;
    } else {
        std::cout << "Timeout" << std::endl;
    }
    
    // 或使用绝对时间
    auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(1);
    cv.wait_until(lock, deadline, []{ return ready; });
}
```

**面试官追问 1：什么是虚假唤醒（spurious wakeup）？如何避免？**

**答案：**

虚假唤醒是指条件变量在没有调用 `notify` 的情况下被唤醒。这是 POSIX 标准允许的行为，可能由系统调度引起。

```cpp
// 错误做法：可能虚假唤醒
void wrongWait() {
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock);  // 可能在没有 notify 的情况下返回
    // 此时 ready 可能仍然是 false！
    if (ready) {  // 需要再次检查
        // ...
    }
}

// 正确做法1：使用谓词（推荐）
void correctWait1() {
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock, []{ return ready; });  // 自动循环检查
    // 保证 ready == true
}

// 正确做法2：手动循环检查
void correctWait2() {
    std::unique_lock<std::mutex> lock(mtx);
    while (!ready) {  // 循环检查
        cv.wait(lock);
    }
    // 保证 ready == true
}

// wait 的等价实现
template<typename Predicate>
void wait_impl(std::unique_lock<std::mutex>& lock, Predicate pred) {
    while (!pred()) {
        cv.wait(lock);
    }
}
```

**面试官追问 2：notify_one() 和 notify_all() 的区别是什么？**

**答案：**

- `notify_one()`：唤醒一个等待线程（如果有多个线程等待，选择哪个由系统决定）
- `notify_all()`：唤醒所有等待线程

```cpp
std::mutex mtx;
std::condition_variable cv;
int data = 0;

// 场景1：只有一个消费者，使用 notify_one
void singleConsumer() {
    std::thread consumer([&]() {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, []{ return data > 0; });
        std::cout << "Data: " << data << std::endl;
    });
    
    {
        std::lock_guard<std::mutex> lock(mtx);
        data = 42;
    }
    cv.notify_one();  // 只唤醒一个消费者
    
    consumer.join();
}

// 场景2：多个消费者，使用 notify_all
void multipleConsumers() {
    std::vector<std::thread> consumers;
    
    for (int i = 0; i < 5; ++i) {
        consumers.emplace_back([&, i]() {
            std::unique_lock<std::mutex> lock(mtx);
            cv.wait(lock, []{ return data > 0; });
            std::cout << "Consumer " << i << " got: " << data << std::endl;
        });
    }
    
    {
        std::lock_guard<std::mutex> lock(mtx);
        data = 100;
    }
    cv.notify_all();  // 唤醒所有消费者
    
    for (auto& t : consumers) {
        t.join();
    }
}

// 性能考虑
// notify_one()：只唤醒一个线程，开销小
// notify_all()：唤醒所有线程，可能引起"惊群效应"，但所有线程都会检查条件
```

**常见错误和最佳实践：**

**常见错误：**
1. ❌ 不使用谓词，直接 `wait(lock)`（可能虚假唤醒）
2. ❌ 在持有锁时调用 `notify`（虽然正确，但可能影响性能）
3. ❌ 忘记通知等待的线程
4. ❌ 条件检查不在互斥量保护下

**最佳实践：**
1. ✅ 始终使用带谓词的 `wait()` 避免虚假唤醒
2. ✅ 可以在锁外调用 `notify` 提升性能（但需确保修改在锁内完成）
3. ✅ 使用 `notify_one()` 除非确实需要唤醒所有线程
4. ✅ 条件变量的条件检查必须在互斥量保护下

---

## 四、原子操作和 std::atomic

### Q4: 请详细解释 std::atomic 的作用，以及 C++ 内存模型中的各种内存序（memory order）。

**标准答案：**

`std::atomic` 提供原子操作，保证操作的原子性和内存可见性。C++11 定义了六种内存序，控制原子操作的内存可见性和顺序。

**内存序类型：**
1. `memory_order_relaxed`：只保证原子性，不保证顺序
2. `memory_order_acquire`：获取语义，之后的读写不能重排序到之前
3. `memory_order_release`：释放语义，之前的读写不能重排序到之后
4. `memory_order_acq_rel`：acquire + release
5. `memory_order_seq_cst`：顺序一致（默认），最强保证
6. `memory_order_consume`：消费语义（已弃用）

**完整代码示例：**

```cpp
#include <atomic>
#include <thread>
#include <vector>
#include <iostream>

// 1. 基本原子操作
void basicAtomic() {
    std::atomic<int> counter{0};
    
    // 原子操作
    counter++;                    // 原子递增
    counter.fetch_add(1);        // 原子加法，返回旧值
    counter.store(100);          // 原子存储
    int value = counter.load();  // 原子加载
    
    // 原子交换
    int old = counter.exchange(200);
    
    // compare_exchange：CAS 操作
    int expected = 100;
    bool success = counter.compare_exchange_strong(expected, 300);
    // 如果 counter == expected，则 counter = 300，返回 true
    // 否则 expected = counter，返回 false
}

// 2. memory_order_relaxed：只保证原子性
std::atomic<int> relaxed_counter{0};

void relaxedExample() {
    std::vector<std::thread> threads;
    
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back([]() {
            for (int j = 0; j < 1000; ++j) {
                relaxed_counter.fetch_add(1, std::memory_order_relaxed);
            }
        });
    }
    
    for (auto& t : threads) {
        t.join();
    }
    
    std::cout << "Relaxed counter: " << relaxed_counter << std::endl;
}

// 3. acquire-release 语义：发布-订阅模式
std::atomic<bool> flag{false};
int data = 0;  // 非原子

void acquireReleaseExample() {
    // 生产者：release
    std::thread producer([]() {
        data = 42;  // 1. 先写入数据
        flag.store(true, std::memory_order_release);  // 2. 发布标志
        // release 保证：1 不会重排序到 2 之后
    });
    
    // 消费者：acquire
    std::thread consumer([]() {
        while (!flag.load(std::memory_order_acquire)) {
            // 等待
        }
        // acquire 保证：看到 flag == true 时，一定能看到 data == 42
        std::cout << "Data: " << data << std::endl;  // 保证输出 42
    });
    
    producer.join();
    consumer.join();
}

// 4. 顺序一致（seq_cst）：默认，最强保证
std::atomic<bool> x{false}, y{false};
std::atomic<int> z{0};

void sequentialConsistency() {
    // 线程1
    std::thread t1([]() {
        x.store(true, std::memory_order_seq_cst);  // 默认
        // 等价于 x.store(true);
    });
    
    // 线程2
    std::thread t2([]() {
        y.store(true, std::memory_order_seq_cst);
    });
    
    // 线程3：观察全局顺序
    std::thread t3([]() {
        while (!x.load(std::memory_order_seq_cst)) {}
        if (y.load(std::memory_order_seq_cst)) {
            z++;
        }
    });
    
    // 线程4：观察全局顺序
    std::thread t4([]() {
        while (!y.load(std::memory_order_seq_cst)) {}
        if (x.load(std::memory_order_seq_cst)) {
            z++;
        }
    });
    
    t1.join();
    t2.join();
    t3.join();
    t4.join();
    
    // seq_cst 保证：所有线程看到相同的全局顺序
    // z 的值可能是 0, 1, 2，但不会是其他值
}

// 5. Lock-Free 栈实现
template<typename T>
class LockFreeStack {
private:
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
        
        // CAS 循环
        while (!head_.compare_exchange_weak(
            new_node->next, new_node,
            std::memory_order_release,
            std::memory_order_relaxed)) {
            // CAS 失败，new_node->next 已更新，重试
        }
    }
    
    bool pop(T& result) {
        Node* old_head = head_.load(std::memory_order_acquire);
        
        while (old_head != nullptr &&
               !head_.compare_exchange_weak(
                   old_head, old_head->next,
                   std::memory_order_release,
                   std::memory_order_acquire)) {
            // CAS 失败，重试
        }
        
        if (old_head == nullptr) {
            return false;
        }
        
        result = old_head->data;
        delete old_head;
        return true;
    }
};

// 6. 原子操作的性能
void atomicPerformance() {
    std::atomic<int> atomic_counter{0};
    int normal_counter = 0;
    const int iterations = 10000000;
    
    // 原子操作
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        atomic_counter++;
    }
    auto end = std::chrono::high_resolution_clock::now();
    
    // 原子操作通常比普通操作慢 2-10 倍
    // 但比 mutex 快得多（mutex 可能慢 100 倍以上）
}
```

**面试官追问 1：compare_exchange_weak 和 compare_exchange_strong 的区别？**

**答案：**

- `compare_exchange_weak`：可能虚假失败（即使值相等也可能返回 false），但性能更好，适合循环中使用
- `compare_exchange_strong`：不会虚假失败，但可能性能稍差

```cpp
std::atomic<int> value{0};

// weak：可能虚假失败，适合循环
void weakExample() {
    int expected = 0;
    while (!value.compare_exchange_weak(expected, 1,
                                        std::memory_order_release,
                                        std::memory_order_relaxed)) {
        // 失败可能是因为值不相等，也可能是虚假失败
        // 但 expected 已更新为当前值，继续循环即可
    }
}

// strong：不会虚假失败
void strongExample() {
    int expected = 0;
    if (value.compare_exchange_strong(expected, 1)) {
        // 成功
    } else {
        // 失败：expected 已更新为当前值
    }
}

// 选择建议：
// - 循环中使用 weak（性能更好）
// - 单次尝试使用 strong（语义更清晰）
```

**面试官追问 2：什么时候应该使用原子操作而不是互斥量？**

**答案：**

**使用原子操作的场景：**
1. 简单的计数器、标志位
2. Lock-Free 数据结构
3. 性能关键路径，锁竞争激烈
4. 只需要保护单个变量

**使用互斥量的场景：**
1. 需要保护多个相关变量
2. 需要复杂的临界区逻辑
3. 需要条件变量配合
4. 代码可读性优先

```cpp
// 场景1：简单计数器 → 原子操作
std::atomic<int> counter{0};
counter++;  // 比 mutex 快得多

// 场景2：多个相关变量 → 互斥量
struct Account {
    int balance;
    int transaction_count;
};
std::mutex mtx;
Account account;

void transfer(int amount) {
    std::lock_guard<std::mutex> lock(mtx);
    account.balance += amount;  // 需要同时保护两个变量
    account.transaction_count++;
}

// 场景3：Lock-Free vs Lock-Based
// Lock-Free：适合高并发、低延迟
// Lock-Based：代码更简单、更容易理解
```

**常见错误和最佳实践：**

**常见错误：**
1. ❌ 混合使用不同内存序导致未定义行为
2. ❌ 对非原子变量使用原子操作的内存序
3. ❌ 过度使用 `memory_order_seq_cst`（性能损失）
4. ❌ 误以为原子操作就是线程安全的（需要配合正确的内存序）

**最佳实践：**
1. ✅ 默认使用 `memory_order_seq_cst`，需要优化时再考虑其他
2. ✅ acquire-release 配对使用
3. ✅ 简单场景用原子操作，复杂场景用互斥量
4. ✅ 理解 happens-before 关系

---

## 五、C++ 内存模型（happens-before、synchronizes-with）

### Q5: 请解释 C++ 内存模型中的 happens-before 和 synchronizes-with 关系。

**标准答案：**

C++ 内存模型定义了多线程程序中操作的可见性和顺序关系。

**核心概念：**
1. **happens-before**：如果操作 A happens-before 操作 B，则 A 的结果对 B 可见
2. **synchronizes-with**：同步关系，建立 happens-before 关系
3. **memory_order**：控制内存操作的可见性和顺序

**完整代码示例：**

```cpp
#include <atomic>
#include <thread>
#include <iostream>

// 1. happens-before 关系
void happensBeforeExample() {
    int x = 0;  // 非原子
    std::atomic<bool> flag{false};
    
    // 线程1
    std::thread t1([&]() {
        x = 42;                    // 1
        flag.store(true);          // 2
        // 1 happens-before 2（程序顺序）
    });
    
    // 线程2
    std::thread t2([&]() {
        if (flag.load()) {         // 3
            std::cout << x << std::endl;  // 4
            // 如果 3 看到 flag == true，则 2 synchronizes-with 3
            // 因此 1 happens-before 4
            // 保证输出 42
        }
    });
    
    t1.join();
    t2.join();
}

// 2. synchronizes-with：通过原子操作建立
void synchronizesWithExample() {
    std::atomic<int> data{0};
    int non_atomic = 0;
    
    // 线程1：release
    std::thread t1([&]() {
        non_atomic = 100;                    // A
        data.store(42, std::memory_order_release);  // B
        // A happens-before B（程序顺序）
    });
    
    // 线程2：acquire
    std::thread t2([&]() {
        int val = data.load(std::memory_order_acquire);  // C
        if (val == 42) {
            std::cout << non_atomic << std::endl;  // D
            // B synchronizes-with C（如果 C 看到 B 写入的值）
            // 因此 A happens-before D
            // 保证输出 100
        }
    });
    
    t1.join();
    t2.join();
}

// 3. 传递性：happens-before 具有传递性
void transitivityExample() {
    std::atomic<int> a{0}, b{0};
    int x = 0, y = 0;
    
    // 线程1
    std::thread t1([&]() {
        x = 1;                              // 1
        a.store(1, std::memory_order_release);  // 2
    });
    
    // 线程2
    std::thread t2([&]() {
        if (a.load(std::memory_order_acquire) == 1) {  // 3
            b.store(1, std::memory_order_release);     // 4
        }
    });
    
    // 线程3
    std::thread t3([&]() {
        if (b.load(std::memory_order_acquire) == 1) {  // 5
            y = x;                                      // 6
            // 1 happens-before 2 (程序顺序)
            // 2 synchronizes-with 3 (acquire-release)
            // 3 happens-before 4 (程序顺序)
            // 4 synchronizes-with 5 (acquire-release)
            // 5 happens-before 6 (程序顺序)
            // 由传递性：1 happens-before 6
            // 因此 y == 1
        }
    });
    
    t1.join();
    t2.join();
    t3.join();
}

// 4. 顺序一致（seq_cst）：全局顺序
void sequentialConsistencyExample() {
    std::atomic<bool> x{false}, y{false};
    std::atomic<int> z{0};
    
    // 线程1
    std::thread t1([&]() {
        x.store(true, std::memory_order_seq_cst);  // A
    });
    
    // 线程2
    std::thread t2([&]() {
        y.store(true, std::memory_order_seq_cst);  // B
    });
    
    // 线程3
    std::thread t3([&]() {
        while (!x.load(std::memory_order_seq_cst)) {}  // C
        if (y.load(std::memory_order_seq_cst)) {       // D
            z++;
        }
    });
    
    // 线程4
    std::thread t4([&]() {
        while (!y.load(std::memory_order_seq_cst)) {}  // E
        if (x.load(std::memory_order_seq_cst)) {       // F
            z++;
        }
    });
    
    t1.join();
    t2.join();
    t3.join();
    t4.join();
    
    // seq_cst 保证：所有线程看到相同的全局顺序
    // 不可能出现：C 看到 A，E 看到 B，但 D 和 F 都返回 false
    // 这违反了顺序一致性
}

// 5. relaxed：只保证原子性
void relaxedExample() {
    std::atomic<int> x{0}, y{0};
    int r1 = 0, r2 = 0;
    
    // 线程1
    std::thread t1([&]() {
        x.store(1, std::memory_order_relaxed);  // A
        y.store(1, std::memory_order_relaxed);  // B
    });
    
    // 线程2
    std::thread t2([&]() {
        r1 = y.load(std::memory_order_relaxed);  // C
        r2 = x.load(std::memory_order_relaxed);  // D
    });
    
    t1.join();
    t2.join();
    
    // relaxed 允许重排序
    // 可能出现：r1 == 1, r2 == 0（C 看到 B，但 D 没看到 A）
    // 这在 seq_cst 下不可能
}

// 6. 实际应用：双重检查锁定（DCLP）
class Singleton {
private:
    static std::atomic<Singleton*> instance_;
    static std::mutex mtx_;
    
public:
    static Singleton* getInstance() {
        Singleton* tmp = instance_.load(std::memory_order_acquire);
        if (tmp == nullptr) {
            std::lock_guard<std::mutex> lock(mtx_);
            tmp = instance_.load(std::memory_order_relaxed);
            if (tmp == nullptr) {
                tmp = new Singleton();
                instance_.store(tmp, std::memory_order_release);
            }
        }
        return tmp;
    }
};

std::atomic<Singleton*> Singleton::instance_{nullptr};
std::mutex Singleton::mtx_;
```

**面试官追问 1：happens-before 和 synchronizes-with 的区别？**

**答案：**

- **happens-before**：更广泛的概念，包括程序顺序、同步关系等
- **synchronizes-with**：特定的同步关系，通过原子操作建立

```cpp
// happens-before 的来源：
// 1. 程序顺序：同一线程内的操作顺序
// 2. synchronizes-with：通过原子操作建立
// 3. 传递性：A happens-before B, B happens-before C → A happens-before C

// synchronizes-with 的建立：
// - release store synchronizes-with acquire load（如果 load 看到 store 写入的值）
// - 顺序一致的原子操作之间

void relationshipExample() {
    std::atomic<int> flag{0};
    int data = 0;
    
    // 线程1
    std::thread t1([&]() {
        data = 42;                                    // A
        flag.store(1, std::memory_order_release);    // B
        // A happens-before B（程序顺序）
    });
    
    // 线程2
    std::thread t2([&]() {
        if (flag.load(std::memory_order_acquire) == 1) {  // C
            std::cout << data << std::endl;                // D
            // B synchronizes-with C（如果 C 看到 B 写入的值）
            // 因此 A happens-before D（通过 synchronizes-with 和传递性）
        }
    });
    
    t1.join();
    t2.join();
}
```

**面试官追问 2：为什么需要内存模型？没有内存模型会怎样？**

**答案：**

内存模型定义了多线程程序的行为，没有它会导致未定义行为。

```cpp
// 没有内存模型的问题：
// 1. 编译器重排序：为了优化，编译器可能重排序操作
// 2. CPU 重排序：CPU 可能乱序执行
// 3. 缓存一致性：不同 CPU 核心的缓存可能不同步

// 例子：没有内存序保证
int x = 0, y = 0;
std::atomic<bool> flag{false};

// 线程1（可能的重排序）
std::thread t1([&]() {
    flag.store(true);  // 可能被重排序到前面
    x = 1;             // 可能被重排序到后面
    y = 2;
});

// 线程2
std::thread t2([&]() {
    if (flag.load()) {
        // 可能看到 flag == true，但 x, y 还没更新！
        std::cout << x << ", " << y << std::endl;
    }
});

// 内存模型通过 memory_order 控制重排序：
// - acquire：防止后续操作重排序到前面
// - release：防止前面操作重排序到后面
// - seq_cst：最强的顺序保证
```

**常见错误和最佳实践：**

**常见错误：**
1. ❌ 误以为所有操作都是顺序一致的
2. ❌ 混合使用不同内存序导致未定义行为
3. ❌ 对非原子变量使用原子操作的内存序语义
4. ❌ 不理解 happens-before 的传递性

**最佳实践：**
1. ✅ 理解 happens-before 和 synchronizes-with 关系
2. ✅ acquire-release 配对使用
3. ✅ 默认使用 seq_cst，需要性能时再优化
4. ✅ 使用内存模型验证工具（如 ThreadSanitizer）

---

## 六、死锁的预防和检测

### Q6: 请说明什么是死锁，如何预防和检测死锁？

**标准答案：**

死锁是指两个或多个线程互相等待对方持有的资源，导致所有线程都无法继续执行。

**死锁的四个必要条件（Coffman 条件）：**
1. 互斥：资源不能被多个线程同时使用
2. 持有并等待：线程持有资源的同时等待其他资源
3. 不可抢占：资源不能被强制释放
4. 循环等待：存在循环等待链

**完整代码示例：**

```cpp
#include <mutex>
#include <thread>
#include <chrono>
#include <iostream>

// 1. 死锁示例
std::mutex mtx1, mtx2;

void deadlockExample() {
    // 线程1：先锁 mtx1，再锁 mtx2
    std::thread t1([]() {
        std::lock_guard<std::mutex> lock1(mtx1);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        std::lock_guard<std::mutex> lock2(mtx2);  // 等待 mtx2
    });
    
    // 线程2：先锁 mtx2，再锁 mtx1
    std::thread t2([]() {
        std::lock_guard<std::mutex> lock2(mtx2);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        std::lock_guard<std::mutex> lock1(mtx1);  // 等待 mtx1
        // 死锁！
    });
    
    t1.join();
    t2.join();
}

// 2. 预防方法1：固定加锁顺序
void preventByOrder() {
    // 所有线程都按相同顺序加锁：先 mtx1，后 mtx2
    std::thread t1([]() {
        std::lock_guard<std::mutex> lock1(mtx1);
        std::lock_guard<std::mutex> lock2(mtx2);
    });
    
    std::thread t2([]() {
        std::lock_guard<std::mutex> lock1(mtx1);  // 相同顺序
        std::lock_guard<std::mutex> lock2(mtx2);
    });
    
    t1.join();
    t2.join();
}

// 3. 预防方法2：std::lock 同时加锁
void preventByStdLock() {
    std::thread t1([]() {
        std::lock(mtx1, mtx2);  // 原子地获取两个锁
        std::lock_guard<std::mutex> lock1(mtx1, std::adopt_lock);
        std::lock_guard<std::mutex> lock2(mtx2, std::adopt_lock);
        // 临界区
    });
    
    std::thread t2([]() {
        std::lock(mtx2, mtx1);  // 顺序可以不同，std::lock 会处理
        std::lock_guard<std::mutex> lock2(mtx2, std::adopt_lock);
        std::lock_guard<std::mutex> lock1(mtx1, std::adopt_lock);
    });
    
    t1.join();
    t2.join();
}

// 4. 预防方法3：scoped_lock（C++17，推荐）
void preventByScopedLock() {
    std::thread t1([]() {
        std::scoped_lock lock(mtx1, mtx2);  // 自动处理多锁
        // 临界区
    });
    
    std::thread t2([]() {
        std::scoped_lock lock(mtx2, mtx1);  // 顺序无关
        // 临界区
    });
    
    t1.join();
    t2.join();
}

// 5. 预防方法4：try_lock 超时
void preventByTimeout() {
    std::thread t1([]() {
        std::unique_lock<std::mutex> lock1(mtx1);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        
        std::unique_lock<std::mutex> lock2(mtx2, std::defer_lock);
        if (lock2.try_lock_for(std::chrono::milliseconds(100))) {
            // 成功获取锁
        } else {
            // 超时，释放 lock1，避免死锁
            lock1.unlock();
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            lock1.lock();
            lock2.lock();
        }
    });
    
    t1.join();
}

// 6. 死锁检测：使用层次锁
class HierarchicalMutex {
    std::mutex mtx_;
    unsigned long const hierarchy_value_;
    unsigned long previous_hierarchy_value_;
    static thread_local unsigned long this_thread_hierarchy_value_;
    
public:
    explicit HierarchicalMutex(unsigned long value)
        : hierarchy_value_(value), previous_hierarchy_value_(0) {}
    
    void lock() {
        check_for_hierarchy_violation();
        mtx_.lock();
        update_hierarchy_value();
    }
    
    void unlock() {
        this_thread_hierarchy_value_ = previous_hierarchy_value_;
        mtx_.unlock();
    }
    
    bool try_lock() {
        check_for_hierarchy_violation();
        if (!mtx_.try_lock()) {
            return false;
        }
        update_hierarchy_value();
        return true;
    }
    
private:
    void check_for_hierarchy_violation() {
        if (this_thread_hierarchy_value_ >= hierarchy_value_) {
            throw std::logic_error("mutex hierarchy violated");
        }
    }
    
    void update_hierarchy_value() {
        previous_hierarchy_value_ = this_thread_hierarchy_value_;
        this_thread_hierarchy_value_ = hierarchy_value_;
    }
};

thread_local unsigned long HierarchicalMutex::this_thread_hierarchy_value_ = ULONG_MAX;

// 使用层次锁防止死锁
void hierarchicalLockExample() {
    HierarchicalMutex high(10000);
    HierarchicalMutex mid(5000);
    HierarchicalMutex low(1000);
    
    std::thread t1([&]() {
        std::lock_guard<HierarchicalMutex> lock_high(high);
        std::lock_guard<HierarchicalMutex> lock_mid(mid);
        std::lock_guard<HierarchicalMutex> lock_low(low);
        // 正确顺序：高 → 中 → 低
    });
    
    std::thread t2([&]() {
        std::lock_guard<HierarchicalMutex> lock_low(low);
        // 如果试图锁 high，会抛出异常（层次违反）
        // std::lock_guard<HierarchicalMutex> lock_high(high);  // 错误！
    });
    
    t1.join();
    t2.join();
}

// 7. 死锁检测工具
// - ThreadSanitizer: -fsanitize=thread
// - Helgrind (Valgrind)
// - 静态分析工具
```

**面试官追问 1：如何检测运行时的死锁？**

**答案：**

可以使用工具和代码检测死锁。

```cpp
// 方法1：使用 ThreadSanitizer
// 编译：g++ -fsanitize=thread -g program.cpp
// 运行时会检测数据竞争和死锁

// 方法2：使用超时检测
class TimeoutLock {
    std::mutex& mtx_;
    std::chrono::steady_clock::time_point deadline_;
    
public:
    TimeoutLock(std::mutex& mtx, std::chrono::milliseconds timeout)
        : mtx_(mtx), deadline_(std::chrono::steady_clock::now() + timeout) {
        if (!mtx_.try_lock_until(deadline_)) {
            throw std::runtime_error("Lock timeout - possible deadlock");
        }
    }
    
    ~TimeoutLock() {
        mtx_.unlock();
    }
};

// 方法3：记录锁的获取顺序
class LockTracker {
    struct LockInfo {
        std::thread::id thread_id;
        std::chrono::steady_clock::time_point timestamp;
        void* lock_address;
    };
    
    static thread_local std::vector<LockInfo> held_locks_;
    static std::mutex tracker_mtx_;
    static std::map<std::thread::id, std::vector<LockInfo>> all_locks_;
    
public:
    static void acquire(void* lock_addr) {
        LockInfo info{
            std::this_thread::get_id(),
            std::chrono::steady_clock::now(),
            lock_addr
        };
        
        std::lock_guard<std::mutex> lock(tracker_mtx_);
        held_locks_.push_back(info);
        all_locks_[std::this_thread::get_id()] = held_locks_;
        
        // 检测死锁：检查是否有循环等待
        detect_deadlock();
    }
    
    static void release(void* lock_addr) {
        held_locks_.erase(
            std::remove_if(held_locks_.begin(), held_locks_.end(),
                [lock_addr](const LockInfo& info) {
                    return info.lock_address == lock_addr;
                }),
            held_locks_.end()
        );
    }
    
private:
    static void detect_deadlock() {
        // 简化版：检查是否有循环等待
        // 实际实现需要构建等待图并检测环
    }
};

thread_local std::vector<LockTracker::LockInfo> LockTracker::held_locks_;
std::mutex LockTracker::tracker_mtx_;
std::map<std::thread::id, std::vector<LockTracker::LockInfo>> LockTracker::all_locks_;
```

**面试官追问 2：除了互斥量，还有哪些情况会导致死锁？**

**答案：**

死锁不仅限于互斥量，还包括其他资源。

```cpp
// 1. 文件锁死锁
void fileLockDeadlock() {
    // 线程1：先锁 file1，再锁 file2
    // 线程2：先锁 file2，再锁 file1
    // → 死锁
}

// 2. 数据库锁死锁
void databaseLockDeadlock() {
    // 事务1：UPDATE table1; UPDATE table2;
    // 事务2：UPDATE table2; UPDATE table1;
    // → 死锁
}

// 3. 网络资源死锁
void networkDeadlock() {
    // 进程A 等待进程B 的数据
    // 进程B 等待进程A 的数据
    // → 死锁（通信死锁）
}

// 4. 线程 join 死锁
void joinDeadlock() {
    std::thread t1, t2;
    
    t1 = std::thread([&t2]() {
        t2.join();  // t1 等待 t2
    });
    
    t2 = std::thread([&t1]() {
        t1.join();  // t2 等待 t1
    });
    
    // 死锁！
}

// 5. 条件变量死锁
void conditionVariableDeadlock() {
    std::mutex mtx;
    std::condition_variable cv;
    bool ready = false;
    
    std::thread t1([&]() {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, []{ return ready; });  // 等待条件
        // 如果条件永远不满足 → 死锁
    });
    
    // 忘记 notify
    // t1 永远等待
}
```

**常见错误和最佳实践：**

**常见错误：**
1. ❌ 不同线程以不同顺序加锁
2. ❌ 在持有锁时调用可能阻塞的函数
3. ❌ 忘记释放锁
4. ❌ 嵌套锁导致死锁

**最佳实践：**
1. ✅ 使用 `scoped_lock` 同时获取多个锁
2. ✅ 固定加锁顺序
3. ✅ 使用超时机制
4. ✅ 避免在持有锁时进行耗时操作
5. ✅ 使用工具检测死锁（ThreadSanitizer）

---

## 七、生产者-消费者队列的 C++ 实现

### Q7: 请实现一个线程安全的生产者-消费者队列，并说明设计要点。

**标准答案：**

生产者-消费者队列是多线程编程的经典问题。需要保证：
1. 线程安全：多生产者/消费者并发访问
2. 阻塞：队列空时消费者阻塞，队列满时生产者阻塞
3. 正确性：使用条件变量避免忙等待

**完整代码示例：**

```cpp
#include <queue>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <iostream>
#include <chrono>

// 1. 基础版本：无界队列
template<typename T>
class ThreadSafeQueue {
private:
    std::queue<T> queue_;
    mutable std::mutex mtx_;
    std::condition_variable cv_not_empty_;
    
public:
    void push(const T& item) {
        {
            std::lock_guard<std::mutex> lock(mtx_);
            queue_.push(item);
        }
        cv_not_empty_.notify_one();
    }
    
    void push(T&& item) {
        {
            std::lock_guard<std::mutex> lock(mtx_);
            queue_.push(std::move(item));
        }
        cv_not_empty_.notify_one();
    }
    
    bool try_pop(T& item) {
        std::lock_guard<std::mutex> lock(mtx_);
        if (queue_.empty()) {
            return false;
        }
        item = queue_.front();
        queue_.pop();
        return true;
    }
    
    void pop(T& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_not_empty_.wait(lock, [this] {
            return !queue_.empty();
        });
        item = queue_.front();
        queue_.pop();
    }
    
    std::shared_ptr<T> pop() {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_not_empty_.wait(lock, [this] {
            return !queue_.empty();
        });
        auto result = std::make_shared<T>(queue_.front());
        queue_.pop();
        return result;
    }
    
    bool empty() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return queue_.empty();
    }
    
    size_t size() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return queue_.size();
    }
};

// 2. 有界队列版本
template<typename T>
class BoundedQueue {
private:
    std::queue<T> queue_;
    mutable std::mutex mtx_;
    std::condition_variable cv_not_empty_;
    std::condition_variable cv_not_full_;
    size_t max_size_;
    
public:
    explicit BoundedQueue(size_t max_size)
        : max_size_(max_size > 0 ? max_size : 1) {}
    
    void push(const T& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_not_full_.wait(lock, [this] {
            return queue_.size() < max_size_;
        });
        queue_.push(item);
        cv_not_empty_.notify_one();
    }
    
    void push(T&& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_not_full_.wait(lock, [this] {
            return queue_.size() < max_size_;
        });
        queue_.push(std::move(item));
        cv_not_empty_.notify_one();
    }
    
    bool try_push(const T& item) {
        std::lock_guard<std::mutex> lock(mtx_);
        if (queue_.size() >= max_size_) {
            return false;
        }
        queue_.push(item);
        cv_not_empty_.notify_one();
        return true;
    }
    
    void pop(T& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_not_empty_.wait(lock, [this] {
            return !queue_.empty();
        });
        item = queue_.front();
        queue_.pop();
        cv_not_full_.notify_one();
    }
    
    bool try_pop(T& item) {
        std::lock_guard<std::mutex> lock(mtx_);
        if (queue_.empty()) {
            return false;
        }
        item = queue_.front();
        queue_.pop();
        cv_not_full_.notify_one();
        return true;
    }
    
    bool empty() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return queue_.empty();
    }
    
    size_t size() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return queue_.size();
    }
};

// 3. 支持关闭的队列
template<typename T>
class StoppableQueue {
private:
    std::queue<T> queue_;
    mutable std::mutex mtx_;
    std::condition_variable cv_not_empty_;
    bool stopped_;
    
public:
    StoppableQueue() : stopped_(false) {}
    
    void push(const T& item) {
        std::lock_guard<std::mutex> lock(mtx_);
        if (stopped_) {
            throw std::runtime_error("Queue is stopped");
        }
        queue_.push(item);
        cv_not_empty_.notify_one();
    }
    
    bool pop(T& item) {
        std::unique_lock<std::mutex> lock(mtx_);
        cv_not_empty_.wait(lock, [this] {
            return !queue_.empty() || stopped_;
        });
        
        if (queue_.empty() && stopped_) {
            return false;  // 队列已关闭且为空
        }
        
        item = queue_.front();
        queue_.pop();
        return true;
    }
    
    void stop() {
        {
            std::lock_guard<std::mutex> lock(mtx_);
            stopped_ = true;
        }
        cv_not_empty_.notify_all();  // 唤醒所有等待的消费者
    }
    
    bool is_stopped() const {
        std::lock_guard<std::mutex> lock(mtx_);
        return stopped_;
    }
};

// 4. 使用示例
void producerConsumerExample() {
    BoundedQueue<int> queue(10);
    
    // 多个生产者
    std::vector<std::thread> producers;
    for (int i = 0; i < 3; ++i) {
        producers.emplace_back([&queue, i]() {
            for (int j = 0; j < 100; ++j) {
                queue.push(i * 100 + j);
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        });
    }
    
    // 多个消费者
    std::vector<std::thread> consumers;
    std::mutex cout_mtx;
    for (int i = 0; i < 2; ++i) {
        consumers.emplace_back([&queue, &cout_mtx, i]() {
            int item;
            int count = 0;
            while (count < 150) {  // 每个消费者处理 150 个
                queue.pop(item);
                {
                    std::lock_guard<std::mutex> lock(cout_mtx);
                    std::cout << "Consumer " << i << " got: " << item << std::endl;
                }
                ++count;
            }
        });
    }
    
    for (auto& t : producers) {
        t.join();
    }
    for (auto& t : consumers) {
        t.join();
    }
}

// 5. 性能优化版本：减少锁竞争
template<typename T>
class OptimizedQueue {
private:
    struct Node {
        std::shared_ptr<T> data;
        std::unique_ptr<Node> next;
    };
    
    std::mutex head_mtx_;
    std::unique_ptr<Node> head_;
    std::mutex tail_mtx_;
    Node* tail_;
    std::condition_variable cv_not_empty_;
    
    Node* get_tail() {
        std::lock_guard<std::mutex> lock(tail_mtx_);
        return tail_;
    }
    
public:
    OptimizedQueue() : head_(std::make_unique<Node>()), tail_(head_.get()) {}
    
    void push(T item) {
        auto new_data = std::make_shared<T>(std::move(item));
        auto new_node = std::make_unique<Node>();
        Node* const new_tail = new_node.get();
        
        {
            std::lock_guard<std::mutex> lock(tail_mtx_);
            tail_->data = new_data;
            tail_->next = std::move(new_node);
            tail_ = new_tail;
        }
        cv_not_empty_.notify_one();
    }
    
    std::shared_ptr<T> pop() {
        std::unique_lock<std::mutex> lock(head_mtx_);
        cv_not_empty_.wait(lock, [this] {
            return head_.get() != get_tail();
        });
        
        auto old_head = std::move(head_);
        head_ = std::move(old_head->next);
        return old_head->data;
    }
};
```

**面试官追问 1：如何实现 Lock-Free 的生产者-消费者队列？**

**答案：**

Lock-Free 实现使用原子操作和 CAS，性能更好但实现更复杂。

```cpp
#include <atomic>
#include <memory>

template<typename T>
class LockFreeQueue {
private:
    struct Node {
        std::atomic<T*> data{nullptr};
        std::atomic<Node*> next{nullptr};
    };
    
    std::atomic<Node*> head_{nullptr};
    std::atomic<Node*> tail_{nullptr};
    
public:
    LockFreeQueue() {
        Node* dummy = new Node;
        head_.store(dummy);
        tail_.store(dummy);
    }
    
    ~LockFreeQueue() {
        while (Node* old_head = head_.load()) {
            head_.store(old_head->next.load());
            delete old_head;
        }
    }
    
    void push(T item) {
        Node* new_node = new Node;
        T* new_data = new T(std::move(item));
        
        Node* prev_tail = tail_.exchange(new_node, std::memory_order_acq_rel);
        prev_tail->data.store(new_data, std::memory_order_release);
        prev_tail->next.store(new_node, std::memory_order_release);
    }
    
    std::unique_ptr<T> pop() {
        Node* head = head_.load(std::memory_order_acquire);
        Node* next = head->next.load(std::memory_order_acquire);
        
        if (next == nullptr) {
            return nullptr;  // 队列为空
        }
        
        T* data = next->data.load(std::memory_order_acquire);
        if (data == nullptr) {
            return nullptr;  // 数据还未写入
        }
        
        head_.store(next, std::memory_order_release);
        delete head;
        
        return std::unique_ptr<T>(data);
    }
};
```

**面试官追问 2：生产者-消费者队列的性能瓶颈在哪里？如何优化？**

**答案：**

主要瓶颈是锁竞争，可以通过以下方式优化：

```cpp
// 1. 减少锁的粒度
// - 使用细粒度锁（如 OptimizedQueue）
// - 分离 head 和 tail 的锁

// 2. 使用 Lock-Free 实现
// - 避免锁开销
// - 但实现复杂，需要处理 ABA 问题

// 3. 批量操作
template<typename T>
class BatchedQueue {
    // 批量 push/pop，减少锁获取次数
    void push_batch(const std::vector<T>& items) {
        std::lock_guard<std::mutex> lock(mtx_);
        for (const auto& item : items) {
            queue_.push(item);
        }
        cv_not_empty_.notify_all();
    }
};

// 4. 使用无锁数据结构
// - 如 boost::lockfree::queue
// - 或自己实现 Lock-Free 版本

// 5. 线程本地缓存
// - 每个线程维护本地队列
// - 定期同步到全局队列
```

**常见错误和最佳实践：**

**常见错误：**
1. ❌ 忘记通知等待的线程
2. ❌ 条件检查不在锁保护下
3. ❌ 虚假唤醒处理不当
4. ❌ 队列关闭时未唤醒所有等待线程

**最佳实践：**
1. ✅ 使用条件变量避免忙等待
2. ✅ 有界队列防止内存无限增长
3. ✅ 支持移动语义减少拷贝
4. ✅ 提供 try_pop/try_push 非阻塞接口
5. ✅ 支持优雅关闭

---

## 高频考点总结

| 考点 | 关键点 | 难度 |
|------|--------|------|
| std::thread | join/detach、移动语义、异常处理 | ★★☆ |
| mutex 类型 | mutex、recursive_mutex、timed_mutex、shared_mutex | ★★☆ |
| 锁类型 | lock_guard、unique_lock、scoped_lock | ★★☆ |
| 条件变量 | wait 谓词、虚假唤醒、notify_one/all | ★★★ |
| 原子操作 | atomic、CAS、内存序 | ★★★ |
| 内存模型 | happens-before、synchronizes-with | ★★★ |
| 死锁 | 四个条件、预防方法、检测工具 | ★★☆ |
| 生产者-消费者 | 线程安全队列、Lock-Free 实现 | ★★★ |

---

## 相关文章

- [上一篇：C++面试题-内存与对象模型](/articles/cpp/cpp-43-C++面试题-内存与对象模型/)
- [下一篇：（系列最后一篇）]

---

## 面试技巧

1. **线程创建**：强调 join/detach 的重要性，推荐 RAII 管理
2. **锁的选择**：简单场景用 lock_guard，需要灵活性用 unique_lock，多锁用 scoped_lock
3. **条件变量**：必须使用谓词避免虚假唤醒
4. **原子操作**：理解各种内存序，默认使用 seq_cst
5. **死锁**：掌握四种预防方法，优先使用 scoped_lock
6. **性能**：理解锁竞争的影响，知道何时使用 Lock-Free 实现

---

*本文涵盖了 C++ 并发与多线程的核心面试题，建议结合实际项目经验深入理解每个概念。*
