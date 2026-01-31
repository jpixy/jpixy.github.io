+++
title = "16. Smart Pointers Internals and Pitfalls"
slug = "cpp-21-智能指针底层与陷阱"
date = 2026-01-21
description = "深入剖析unique_ptr、shared_ptr、weak_ptr的底层实现、性能开销和常见陷阱"
[taxonomies]
tags = ["C++", "智能指针", "内存管理", "性能优化", "RAII"]
+++

## 概述

智能指针是C++11引入的核心特性，自动化内存管理的同时也带来了开销。理解其底层实现对于在性能敏感场景中正确使用至关重要。

---

## 一、unique_ptr

### 1.1 底层实现

```cpp
// unique_ptr的简化实现
template<typename T, typename Deleter = std::default_delete<T>>
class unique_ptr {
private:
    T* ptr_;
    [[no_unique_address]] Deleter deleter_;  // C++20: 空基类优化
    
public:
    explicit unique_ptr(T* p = nullptr) noexcept : ptr_(p) {}
    
    ~unique_ptr() {
        if (ptr_) {
            deleter_(ptr_);
        }
    }
    
    // 移动操作
    unique_ptr(unique_ptr&& other) noexcept 
        : ptr_(other.ptr_), deleter_(std::move(other.deleter_)) {
        other.ptr_ = nullptr;
    }
    
    unique_ptr& operator=(unique_ptr&& other) noexcept {
        if (this != &other) {
            reset(other.release());
            deleter_ = std::move(other.deleter_);
        }
        return *this;
    }
    
    // 禁止拷贝
    unique_ptr(const unique_ptr&) = delete;
    unique_ptr& operator=(const unique_ptr&) = delete;
    
    T* release() noexcept {
        T* tmp = ptr_;
        ptr_ = nullptr;
        return tmp;
    }
    
    void reset(T* p = nullptr) noexcept {
        T* old = ptr_;
        ptr_ = p;
        if (old) deleter_(old);
    }
    
    T* get() const noexcept { return ptr_; }
    T& operator*() const { return *ptr_; }
    T* operator->() const noexcept { return ptr_; }
    explicit operator bool() const noexcept { return ptr_ != nullptr; }
};
```

### 1.2 零开销抽象

```cpp
// unique_ptr大小等于原始指针（使用默认删除器时）
static_assert(sizeof(std::unique_ptr<int>) == sizeof(int*));

// 自定义删除器可能增加大小
auto custom_deleter = [](int* p) { delete p; };
std::unique_ptr<int, decltype(custom_deleter)> ptr(new int(42), custom_deleter);
// 大小可能增加（取决于lambda是否捕获）
```

### 1.3 数组特化

```cpp
// 数组版本
std::unique_ptr<int[]> arr(new int[100]);
arr[0] = 42;  // 支持operator[]

// 不支持operator*和operator->
// *arr;  // 编译错误
```

---

## 二、shared_ptr

### 2.1 底层实现

```cpp
// shared_ptr的控制块
struct ControlBlock {
    std::atomic<size_t> strong_count;
    std::atomic<size_t> weak_count;
    // 可能还包含：
    // - 删除器
    // - 分配器
    // - 指向对象的指针（如果使用make_shared则对象内嵌）
};

// shared_ptr包含两个指针
template<typename T>
class shared_ptr {
private:
    T* ptr_;                  // 指向管理的对象
    ControlBlock* control_;   // 指向控制块
    
public:
    // 大小 = 2个指针
    // 拷贝时需要原子操作增加引用计数
};

static_assert(sizeof(std::shared_ptr<int>) == 2 * sizeof(void*));
```

### 2.2 make_shared优化

```cpp
// 不推荐：两次分配
std::shared_ptr<Widget> p1(new Widget());
// 分配1：Widget对象
// 分配2：控制块

// 推荐：一次分配
auto p2 = std::make_shared<Widget>();
// 对象和控制块一起分配

// 内存布局：
// +------------------+
// | ControlBlock     |
// | - strong_count   |
// | - weak_count     |
// +------------------+
// | Widget object    |
// +------------------+
```

### 2.3 原子操作开销

```cpp
// shared_ptr拷贝需要原子操作
void copySharedPtr(std::shared_ptr<int> src) {
    // 1. 读取src的控制块指针
    // 2. 原子增加strong_count
    // 3. 复制指针
}

void benchmark() {
    auto ptr = std::make_shared<int>(42);
    
    // 测量拷贝开销
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < 1000000; ++i) {
        auto copy = ptr;  // 原子递增
        (void)copy;       // 原子递减
    }
    auto end = std::chrono::high_resolution_clock::now();
    
    // 典型结果：20-50ns/次（取决于争用程度）
}
```

---

## 三、weak_ptr

### 3.1 作用

```cpp
// 打破循环引用
class Node {
public:
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // 使用weak_ptr避免循环引用
};

// 检查对象是否还存在
std::weak_ptr<Widget> weak = shared;
if (auto locked = weak.lock()) {
    // 对象还存在，locked是shared_ptr
    locked->doSomething();
}
```

### 3.2 开销

```cpp
// weak_ptr.lock()需要：
// 1. 检查strong_count是否>0
// 2. 原子增加strong_count
// 3. 构造shared_ptr

// 如果频繁调用lock()，开销不小
```

---

## 四、常见陷阱

### 4.1 循环引用

```cpp
class A {
public:
    std::shared_ptr<B> b;
};

class B {
public:
    std::shared_ptr<A> a;  // 循环引用！内存泄漏
};

// 解决：使用weak_ptr
class B {
public:
    std::weak_ptr<A> a;
};
```

### 4.2 从this创建shared_ptr

```cpp
class Widget {
public:
    std::shared_ptr<Widget> getShared() {
        // 错误：创建独立的控制块
        return std::shared_ptr<Widget>(this);
    }
};

// 正确：继承enable_shared_from_this
class Widget : public std::enable_shared_from_this<Widget> {
public:
    std::shared_ptr<Widget> getShared() {
        return shared_from_this();
    }
};

// 使用
auto widget = std::make_shared<Widget>();
auto ptr = widget->getShared();  // 共享同一控制块
```

### 4.3 多线程问题

```cpp
std::shared_ptr<int> global_ptr;

void thread1() {
    global_ptr = std::make_shared<int>(42);  // 非线程安全！
}

void thread2() {
    auto local = global_ptr;  // 可能读到半更新状态
}

// 解决：使用atomic_shared_ptr（C++20）或mutex
std::atomic<std::shared_ptr<int>> atomic_ptr;

// 或者
std::mutex mtx;
std::shared_ptr<int> protected_ptr;

void safeWrite() {
    std::lock_guard lock(mtx);
    protected_ptr = std::make_shared<int>(42);
}
```

### 4.4 自定义删除器

```cpp
// 管理非new分配的资源
std::shared_ptr<FILE> file(fopen("test.txt", "r"), fclose);

// 管理数组（C++17前）
std::shared_ptr<int> arr(new int[100], std::default_delete<int[]>());

// C++17：shared_ptr支持数组
std::shared_ptr<int[]> arr2(new int[100]);
```

---

## 五、HFT中的使用建议

### 5.1 避免热路径使用shared_ptr

```cpp
// 不好：热路径中拷贝shared_ptr
void processOrder(std::shared_ptr<Order> order) {
    // 每次调用都有原子操作
}

// 好：使用引用或原始指针
void processOrder(const Order& order) {
    // 无原子操作
}

void processOrder(Order* order) {
    // 无原子操作，但要注意生命周期
}
```

### 5.2 使用unique_ptr

```cpp
// HFT中优先使用unique_ptr
class OrderBook {
private:
    std::vector<std::unique_ptr<Order>> orders_;
    
public:
    void addOrder(std::unique_ptr<Order> order) {
        orders_.push_back(std::move(order));
    }
};

// 或者直接存储对象（如果大小合适）
class OrderBook {
private:
    std::vector<Order> orders_;  // 最佳：连续内存
};
```

### 5.3 对象池替代

```cpp
// 使用对象池而非智能指针
template<typename T>
class ObjectPool {
    std::vector<T> storage_;
    std::vector<T*> free_list_;
    
public:
    T* acquire() { /* ... */ }
    void release(T* obj) { /* ... */ }
};

// 使用原始指针，生命周期由池管理
```

---

## 总结

| 智能指针 | 大小 | 拷贝开销 | HFT适用性 |
|----------|------|----------|-----------|
| unique_ptr | 1指针 | 禁止拷贝 | **推荐** |
| shared_ptr | 2指针 | 原子操作 | 避免热路径 |
| weak_ptr | 2指针 | 原子操作 | 避免热路径 |
| 原始指针 | 1指针 | 无 | 需手动管理 |

**最佳实践**：
1. 优先unique_ptr
2. 热路径传引用/指针
3. 避免频繁拷贝shared_ptr
4. 考虑对象池替代

---

## 相关文章

- [上一篇：Custom Memory Allocators (HFT)](/articles/cpp/cpp-15-HFT自定义内存分配器设计/)
- [下一篇：Lock-Free Data Structures (HFT)](/articles/cpp/cpp-17-HFT-Lock-Free数据结构详解/)
