+++
title = "53. Interview - Concurrency and Multithreading"
date = 2026-01-21
description = "C++并发与多线程面试题汇总，包括线程、互斥锁、条件变量、原子操作、内存序等核心概念"
[taxonomies]
tags = ["C++", "面试题", "并发", "多线程"]
+++

## 一、线程基础

### Q1: 如何创建和管理线程？

```cpp
#include <thread>

// 创建线程
void threadFunc(int x) {
    std::cout << "Value: " << x << std::endl;
}

std::thread t1(threadFunc, 42);       // 普通函数
std::thread t2([]{ /* lambda */ });    // Lambda
std::thread t3(&MyClass::method, &obj);// 成员函数

// 必须join或detach
t1.join();   // 等待线程结束
t2.detach(); // 分离线程
// t3未join/detach会在析构时terminate

// 检查是否可join
if (t.joinable()) {
    t.join();
}

// 获取线程ID
std::thread::id id = std::this_thread::get_id();
```

### Q2: std::thread可以拷贝吗？

```cpp
std::thread t1(func);
// std::thread t2 = t1;  // 错误：thread不可拷贝

std::thread t2 = std::move(t1);  // OK：可以移动
// 现在t1不再关联任何线程
```

---

## 二、互斥锁

### Q3: mutex的种类和用法？

```cpp
#include <mutex>

std::mutex mtx;                    // 基本互斥锁
std::recursive_mutex rmtx;         // 可递归锁
std::timed_mutex tmtx;             // 带超时
std::shared_mutex smtx;            // 读写锁（C++17）

// 基本用法
mtx.lock();
// 临界区
mtx.unlock();

// 推荐：RAII包装
{
    std::lock_guard<std::mutex> lock(mtx);  // 自动加锁解锁
    // 临界区
}

// C++17简化
{
    std::lock_guard lock(mtx);  // CTAD
}

// 更灵活的unique_lock
{
    std::unique_lock<std::mutex> lock(mtx);
    // 可以手动unlock
    lock.unlock();
    // 可以再次lock
    lock.lock();
}

// 读写锁
{
    std::shared_lock lock(smtx);  // 共享锁（读）
}
{
    std::unique_lock lock(smtx);  // 独占锁（写）
}
```

### Q4: 如何避免死锁？

```cpp
// 死锁条件：
// 1. 互斥
// 2. 持有并等待
// 3. 不可抢占
// 4. 循环等待

// 避免方法1：固定加锁顺序
void func1() {
    std::lock_guard lock1(mtxA);
    std::lock_guard lock2(mtxB);  // 总是先A后B
}

// 避免方法2：std::lock同时加锁
void func2() {
    std::lock(mtxA, mtxB);  // 原子地获取两个锁
    std::lock_guard lockA(mtxA, std::adopt_lock);
    std::lock_guard lockB(mtxB, std::adopt_lock);
}

// C++17：std::scoped_lock
void func3() {
    std::scoped_lock lock(mtxA, mtxB);  // 同时获取，无死锁
}

// 避免方法3：try_lock超时
if (mtx.try_lock()) {
    // 获取成功
    mtx.unlock();
}
```

---

## 三、条件变量

### Q5: 条件变量的使用？

```cpp
#include <condition_variable>

std::mutex mtx;
std::condition_variable cv;
bool ready = false;
std::queue<int> data_queue;

// 生产者
void producer() {
    {
        std::lock_guard lock(mtx);
        data_queue.push(42);
        ready = true;
    }
    cv.notify_one();  // 通知一个等待线程
    // cv.notify_all();  // 通知所有等待线程
}

// 消费者
void consumer() {
    std::unique_lock lock(mtx);
    cv.wait(lock, []{ return ready; });  // 等待条件
    // 或者不带谓词
    // while (!ready) cv.wait(lock);
    
    int data = data_queue.front();
    data_queue.pop();
}
```

### Q6: 虚假唤醒是什么？

```cpp
// 条件变量可能在没有notify的情况下返回
// 这称为虚假唤醒（spurious wakeup）

// 错误做法
cv.wait(lock);
// 可能没有被notify就返回

// 正确做法：使用带谓词的wait
cv.wait(lock, []{ return condition; });

// 或者循环检查
while (!condition) {
    cv.wait(lock);
}
```

---

## 四、原子操作

### Q7: std::atomic的使用？

```cpp
#include <atomic>

std::atomic<int> counter{0};

// 原子操作
counter++;              // 原子递增
counter.load();         // 原子读取
counter.store(42);      // 原子写入
counter.fetch_add(1);   // 原子加法，返回旧值
counter.exchange(100);  // 原子交换，返回旧值

// compare_exchange
int expected = 0;
counter.compare_exchange_strong(expected, 1);
// 如果counter==expected，则counter=1，返回true
// 否则expected=counter，返回false
```

### Q8: 什么是内存序（Memory Order）？

```cpp
// 内存序控制原子操作的可见性和顺序

std::atomic<bool> flag{false};
int data = 0;

// memory_order_relaxed：最弱，只保证原子性
counter.fetch_add(1, std::memory_order_relaxed);

// memory_order_acquire：获取语义
// 之后的读写不能重排序到之前
flag.load(std::memory_order_acquire);

// memory_order_release：释放语义
// 之前的读写不能重排序到之后
flag.store(true, std::memory_order_release);

// memory_order_seq_cst：最强，顺序一致（默认）
flag.store(true);  // 等价于memory_order_seq_cst

// 典型使用：发布-订阅模式
void producer() {
    data = 42;
    flag.store(true, std::memory_order_release);
}

void consumer() {
    while (!flag.load(std::memory_order_acquire)) {}
    assert(data == 42);  // 保证看到data=42
}
```

---

## 五、并发设施

### Q9: std::async和std::future？

```cpp
#include <future>

// async：异步执行任务
std::future<int> result = std::async(std::launch::async, []() {
    return 42;
});

// 获取结果（阻塞）
int value = result.get();

// launch策略
std::launch::async;    // 立即在新线程执行
std::launch::deferred; // 延迟执行（调用get时）
std::launch::async | std::launch::deferred;  // 默认：由实现决定

// promise-future通信
std::promise<int> promise;
std::future<int> future = promise.get_future();

std::thread t([&promise]() {
    promise.set_value(42);  // 设置结果
});

int result = future.get();  // 获取结果
t.join();
```

### Q10: std::packaged_task？

```cpp
#include <future>

// 封装可调用对象
std::packaged_task<int(int, int)> task([](int a, int b) {
    return a + b;
});

std::future<int> result = task.get_future();

std::thread t(std::move(task), 1, 2);
t.join();

int sum = result.get();  // 3
```

---

## 六、线程安全

### Q11: 什么是数据竞争？

```cpp
int counter = 0;  // 非原子

void increment() {
    for (int i = 0; i < 100000; ++i) {
        counter++;  // 数据竞争！
    }
}

std::thread t1(increment);
std::thread t2(increment);
t1.join();
t2.join();

// counter可能不是200000

// 解决方案：
// 1. 使用mutex
// 2. 使用std::atomic<int>
```

### Q12: 线程安全的单例模式？

```cpp
// 方法1：C++11静态局部变量（推荐）
class Singleton {
public:
    static Singleton& getInstance() {
        static Singleton instance;  // C++11保证线程安全
        return instance;
    }
    
private:
    Singleton() = default;
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
};

// 方法2：双重检查锁定（DCLP）
class Singleton2 {
    static std::atomic<Singleton2*> instance;
    static std::mutex mtx;
    
public:
    static Singleton2* getInstance() {
        Singleton2* tmp = instance.load(std::memory_order_acquire);
        if (!tmp) {
            std::lock_guard lock(mtx);
            tmp = instance.load(std::memory_order_relaxed);
            if (!tmp) {
                tmp = new Singleton2();
                instance.store(tmp, std::memory_order_release);
            }
        }
        return tmp;
    }
};

// 方法3：std::call_once
class Singleton3 {
    static std::unique_ptr<Singleton3> instance;
    static std::once_flag flag;
    
public:
    static Singleton3& getInstance() {
        std::call_once(flag, []() {
            instance.reset(new Singleton3());
        });
        return *instance;
    }
};
```

---

## 七、高级话题

### Q13: 什么是Lock-Free？

```cpp
// Lock-Free：不使用锁的并发算法
// 保证：至少有一个线程能取得进展

// Lock-Free栈的push操作
template<typename T>
class LockFreeStack {
    struct Node {
        T data;
        Node* next;
    };
    std::atomic<Node*> head{nullptr};
    
public:
    void push(const T& data) {
        Node* new_node = new Node{data, nullptr};
        new_node->next = head.load(std::memory_order_relaxed);
        while (!head.compare_exchange_weak(new_node->next, new_node,
                std::memory_order_release, std::memory_order_relaxed)) {
            // CAS失败，new_node->next已更新，重试
        }
    }
};
```

### Q14: 线程池的基本实现？

```cpp
class ThreadPool {
    std::vector<std::thread> workers;
    std::queue<std::function<void()>> tasks;
    std::mutex mtx;
    std::condition_variable cv;
    std::atomic<bool> stop{false};
    
public:
    ThreadPool(size_t num_threads) {
        for (size_t i = 0; i < num_threads; ++i) {
            workers.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock lock(mtx);
                        cv.wait(lock, [this] {
                            return stop || !tasks.empty();
                        });
                        if (stop && tasks.empty()) return;
                        task = std::move(tasks.front());
                        tasks.pop();
                    }
                    task();
                }
            });
        }
    }
    
    template<typename F>
    void enqueue(F&& f) {
        {
            std::lock_guard lock(mtx);
            tasks.emplace(std::forward<F>(f));
        }
        cv.notify_one();
    }
    
    ~ThreadPool() {
        stop = true;
        cv.notify_all();
        for (auto& w : workers) w.join();
    }
};
```

---

## 面试技巧

1. **线程创建**：记住join/detach的重要性
2. **互斥锁**：推荐scoped_lock避免死锁
3. **条件变量**：强调虚假唤醒和谓词使用
4. **原子操作**：理解memory_order，默认用seq_cst
5. **线程安全单例**：推荐静态局部变量方法
