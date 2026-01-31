+++
title = "43.C++面试题-内存与对象模型"
date = 2026-01-31
description = "C++内存与对象模型面试题：虚函数表、内存布局、智能指针、RAII深度解析"
[taxonomies]
tags = ["C++", "面试", "内存", "对象模型", "智能指针"]
+++

# C++ 面试题 - 内存与对象模型

本文深入探讨 C++ 内存与对象模型相关的面试题，采用问答深挖形式，模拟真实面试场景。涵盖虚函数表、内存布局、智能指针、RAII 等核心概念。

**难度标注**：★☆☆ 基础 | ★★☆ 中级 | ★★★ 困难

---

## 问题 1：C++ 对象的内存布局是什么？

**面试官**：请解释一下 C++ 对象在内存中是如何布局的？包括虚函数表、成员变量的顺序、内存对齐等。

### 标准答案

C++ 对象的内存布局遵循以下规则：

1. **成员变量顺序**：按照声明顺序存储
2. **内存对齐**：根据平台和类型大小对齐（通常是 4/8 字节）
3. **虚函数表指针（vptr）**：如果类有虚函数，对象首部存储 vptr
4. **继承布局**：基类成员在前，派生类成员在后
5. **多重继承**：每个基类子对象独立存储

### 代码示例

```cpp
#include <iostream>
#include <cstddef>

// 简单类
class Simple {
    int a;      // 偏移 0
    char b;     // 偏移 4
    int c;      // 偏移 8（对齐）
    // 总大小：12 字节（对齐到 4 的倍数）
};

// 有虚函数的类
class Base {
public:
    int x;              // 偏移 8（vptr 占 8 字节）
    virtual void foo() {}  // vptr 指向虚函数表
    // 总大小：16 字节（x 对齐到 8 字节边界）
};

// 继承
class Derived : public Base {
public:
    int y;              // 偏移 16
    virtual void bar() {}
    // 总大小：24 字节
};

// 验证内存布局
void print_layout() {
    std::cout << "Simple size: " << sizeof(Simple) << std::endl;
    std::cout << "Base size: " << sizeof(Base) << std::endl;
    std::cout << "Derived size: " << sizeof(Derived) << std::endl;
    
    // 查看成员偏移
    std::cout << "Base::x offset: " << offsetof(Base, x) << std::endl;
    std::cout << "Derived::y offset: " << offsetof(Derived, y) << std::endl;
}
```

### 内存布局图示

```
Simple 对象布局（假设 4 字节对齐）：
┌─────────┬─────────┬─────────┐
│   int a │  char b │ padding │
│  (4字节) │  (1字节) │  (3字节) │
└─────────┴─────────┴─────────┘
┌─────────┐
│   int c │
│  (4字节) │
└─────────┘
总大小：12 字节

Base 对象布局（64位系统）：
┌─────────────┐
│    vptr     │ ← 指向虚函数表（8字节）
├─────────────┤
│   padding   │
├─────────────┤
│     int x   │ ← 成员变量（4字节）
│   padding   │
└─────────────┘
总大小：16 字节（对齐到 8 字节）

Derived 对象布局：
┌─────────────┐
│    vptr     │ ← 指向 Derived 的虚函数表
├─────────────┤
│   padding   │
├─────────────┤
│  Base::x    │ ← 继承自 Base
├─────────────┤
│   padding   │
├─────────────┤
│ Derived::y  │ ← 派生类成员
│   padding   │
└─────────────┘
总大小：24 字节
```

### 面试官追问 1

**面试官**：如果类中有多个虚函数，内存布局会变化吗？

**答案**：不会。无论有多少个虚函数，对象中只存储一个 vptr（8 字节，64位系统）。所有虚函数的地址都存储在虚函数表中，vptr 指向这个表。

```cpp
class MultiVirtual {
public:
    virtual void func1() {}
    virtual void func2() {}
    virtual void func3() {}
    int x;
    // 大小仍然是 16 字节（vptr + int + padding）
    // vptr 指向包含 func1、func2、func3 的虚函数表
};
```

### 面试官追问 2

**面试官**：空类的大小是多少？为什么？

**答案**：空类大小至少为 1 字节。这是为了确保不同对象的地址不同。

```cpp
class Empty {};
std::cout << sizeof(Empty) << std::endl;  // 输出：1

// 但如果空类有虚函数
class EmptyVirtual {
    virtual void foo() {}
};
std::cout << sizeof(EmptyVirtual) << std::endl;  // 输出：8（vptr）
```

### 面试官追问 3

**面试官**：内存对齐的目的是什么？如何控制对齐？

**答案**：内存对齐是为了提高访问效率。CPU 访问对齐的数据更快。

```cpp
// 默认对齐
struct DefaultAlign {
    char a;   // 偏移 0
    int b;    // 偏移 4（对齐到 4 字节边界）
    char c;   // 偏移 8
    // 总大小：12 字节
};

// 紧凑布局（可能降低性能）
#pragma pack(1)
struct Packed {
    char a;   // 偏移 0
    int b;    // 偏移 1（不对齐）
    char c;   // 偏移 5
    // 总大小：6 字节
};
#pragma pack()

// C++11 alignas
struct Aligned {
    alignas(16) int x;  // 对齐到 16 字节边界
    int y;
    // 总大小：16 字节（x 对齐到 16）
};
```

---

## 问题 2：虚函数是如何实现的？

**面试官**：请详细解释 C++ 虚函数的实现机制，包括虚函数表（vtable）、虚函数指针（vptr）、以及多重继承下的情况。

### 标准答案

虚函数通过**虚函数表（vtable）**和**虚函数指针（vptr）**实现：

1. **vtable**：每个有虚函数的类都有一个虚函数表，存储虚函数地址
2. **vptr**：每个对象包含一个指向 vtable 的指针
3. **动态绑定**：通过 vptr 间接调用虚函数，实现多态
4. **多重继承**：每个基类都有自己的 vptr 和 vtable

### 代码示例

```cpp
#include <iostream>

class Base {
public:
    int base_data = 10;
    
    virtual void func1() {
        std::cout << "Base::func1()" << std::endl;
    }
    
    virtual void func2() {
        std::cout << "Base::func2()" << std::endl;
    }
    
    void non_virtual() {
        std::cout << "Base::non_virtual()" << std::endl;
    }
};

class Derived : public Base {
public:
    int derived_data = 20;
    
    void func1() override {
        std::cout << "Derived::func1()" << std::endl;
    }
    // func2 继承自 Base
};

// 查看虚函数表内容（平台相关）
void examine_vtable(Base* obj) {
    // 获取 vptr（对象首地址）
    void** vptr = *(void***)obj;
    
    std::cout << "vptr address: " << vptr << std::endl;
    std::cout << "vtable[0] (func1): " << vptr[0] << std::endl;
    std::cout << "vtable[1] (func2): " << vptr[1] << std::endl;
}

int main() {
    Base base;
    Derived derived;
    
    Base* ptr1 = &base;
    Base* ptr2 = &derived;
    
    ptr1->func1();  // Base::func1() - 通过 vptr 调用
    ptr2->func1();  // Derived::func1() - 多态
    
    examine_vtable(&base);
    examine_vtable(&derived);
    
    return 0;
}
```

### 虚函数表结构图示

```
Base 类的虚函数表：
┌─────────────────┐
│ vtable for Base │
├─────────────────┤
│ &Base::func1    │ ← 索引 0
├─────────────────┤
│ &Base::func2    │ ← 索引 1
└─────────────────┘

Base 对象：
┌─────────────┐
│    vptr     │ ──┐
├─────────────┤   │
│  base_data  │   │
└─────────────┘   │
                  │
                  └─→ 指向 Base 的 vtable

Derived 类的虚函数表：
┌──────────────────┐
│ vtable for Derived│
├──────────────────┤
│ &Derived::func1  │ ← 覆盖了 Base::func1
├──────────────────┤
│ &Base::func2     │ ← 继承自 Base
└──────────────────┘

Derived 对象：
┌─────────────┐
│    vptr     │ ──┐
├─────────────┤   │
│  base_data  │   │
├─────────────┤   │
│derived_data │   │
└─────────────┘   │
                  │
                  └─→ 指向 Derived 的 vtable
```

### 面试官追问 1

**面试官**：多重继承下，虚函数表是如何组织的？

**答案**：多重继承时，派生类有多个 vptr，每个基类对应一个。

```cpp
class Base1 {
public:
    virtual void func1() { std::cout << "Base1::func1" << std::endl; }
    int base1_data = 1;
};

class Base2 {
public:
    virtual void func2() { std::cout << "Base2::func2" << std::endl; }
    int base2_data = 2;
};

class Derived : public Base1, public Base2 {
public:
    void func1() override { std::cout << "Derived::func1" << std::endl; }
    void func2() override { std::cout << "Derived::func2" << std::endl; }
    int derived_data = 3;
};

// Derived 对象布局（64位系统）：
// ┌─────────────┐
// │  vptr1      │ → Base1 的 vtable
// ├─────────────┤
// │ base1_data  │
// ├─────────────┤
// │  vptr2      │ → Base2 的 vtable
// ├─────────────┤
// │ base2_data  │
// ├─────────────┤
// │derived_data │
// └─────────────┘

void test_multiple_inheritance() {
    Derived d;
    Base1* b1 = &d;
    Base2* b2 = &d;
    
    // 指针值不同！需要调整（thunk）
    std::cout << "Derived*: " << &d << std::endl;
    std::cout << "Base1*:   " << b1 << std::endl;
    std::cout << "Base2*:   " << b2 << std::endl;  // 偏移了 16 字节
}
```

### 面试官追问 2

**面试官**：虚继承（virtual inheritance）的内存布局有什么不同？

**答案**：虚继承使用共享的基类子对象，通过虚基类表（vbtable）定位。

```cpp
class Base {
public:
    int base_data = 100;
    virtual void func() {}
};

class Derived1 : virtual public Base {
public:
    int derived1_data = 200;
};

class Derived2 : virtual public Base {
public:
    int derived2_data = 300;
};

class Final : public Derived1, public Derived2 {
public:
    int final_data = 400;
};

// Final 对象布局（简化）：
// ┌─────────────┐
// │  vptr1      │ → Derived1 的 vtable（包含虚基类偏移）
// ├─────────────┤
// │derived1_data│
// ├─────────────┤
// │  vptr2      │ → Derived2 的 vtable
// ├─────────────┤
// │derived2_data│
// ├─────────────┤
// │ final_data  │
// ├─────────────┤
// │  vptr_base  │ → Base 的 vtable
// ├─────────────┤
// │ base_data   │ ← 共享的 Base 子对象（只有一份）
// └─────────────┘

void test_virtual_inheritance() {
    Final f;
    Base* b1 = static_cast<Derived1*>(&f);
    Base* b2 = static_cast<Derived2*>(&f);
    
    // 两个指针指向同一个 Base 子对象
    std::cout << "b1 == b2: " << (b1 == b2) << std::endl;  // true
}
```

### 面试官追问 3

**面试官**：构造函数和析构函数中调用虚函数会发生什么？

**答案**：在构造/析构过程中，虚函数机制不完整，会调用当前类的版本。

```cpp
class Base {
public:
    Base() {
        func();  // 调用 Base::func()，不是派生类版本！
    }
    
    virtual ~Base() {
        func();  // 调用 Base::func()
    }
    
    virtual void func() {
        std::cout << "Base::func()" << std::endl;
    }
};

class Derived : public Base {
public:
    Derived() {
        func();  // 调用 Derived::func()
    }
    
    ~Derived() {
        func();  // 调用 Derived::func()
    }
    
    void func() override {
        std::cout << "Derived::func()" << std::endl;
    }
};

// 执行顺序：
// 1. Base 构造函数 → Base::func()
// 2. Derived 构造函数 → Derived::func()
// 3. Derived 析构函数 → Derived::func()
// 4. Base 析构函数 → Base::func()
```

---

## 问题 3：智能指针的区别和实现

**面试官**：请详细说明 `unique_ptr`、`shared_ptr`、`weak_ptr` 的区别，以及它们的实现原理。

### 标准答案

三种智能指针的核心区别：

1. **unique_ptr**：独占所有权，不可拷贝，可移动
2. **shared_ptr**：共享所有权，使用引用计数
3. **weak_ptr**：不拥有所有权，解决 shared_ptr 循环引用

### 代码示例

```cpp
#include <memory>
#include <iostream>

// unique_ptr 示例
void unique_ptr_demo() {
    std::unique_ptr<int> p1(new int(42));
    // std::unique_ptr<int> p2 = p1;  // 错误：不可拷贝
    
    std::unique_ptr<int> p2 = std::move(p1);  // 可以移动
    std::cout << *p2 << std::endl;  // 42
    
    // p1 现在是 nullptr
    if (!p1) {
        std::cout << "p1 is null" << std::endl;
    }
    
    // 自动释放内存
}

// shared_ptr 示例
void shared_ptr_demo() {
    std::shared_ptr<int> p1(new int(100));
    std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 1
    
    {
        std::shared_ptr<int> p2 = p1;
        std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 2
        std::cout << "p2 use_count: " << p2.use_count() << std::endl;  // 2
    }  // p2 析构，引用计数减 1
    
    std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 1
    // p1 析构时，引用计数为 0，释放内存
}

// weak_ptr 示例
void weak_ptr_demo() {
    std::shared_ptr<int> shared(new int(200));
    std::weak_ptr<int> weak = shared;
    
    std::cout << "shared use_count: " << shared.use_count() << std::endl;  // 1
    std::cout << "weak expired: " << weak.expired() << std::endl;  // false
    
    shared.reset();  // 释放对象
    
    std::cout << "weak expired: " << weak.expired() << std::endl;  // true
    
    if (auto locked = weak.lock()) {
        // 不会执行，因为对象已释放
        std::cout << *locked << std::endl;
    } else {
        std::cout << "Object expired" << std::endl;
    }
}
```

### 实现原理图示

```
unique_ptr 实现（简化）：
┌─────────────────────┐
│  unique_ptr<T>      │
├─────────────────────┤
│  T* ptr             │ ← 原始指针
└─────────────────────┘
析构时：delete ptr

shared_ptr 实现（简化）：
┌─────────────────────┐
│  shared_ptr<T>      │
├─────────────────────┤
│  T* ptr             │ ← 原始指针
│  ControlBlock* ctrl │ → 控制块
└─────────────────────┘
         │
         └─→ ┌──────────────────┐
             │  ControlBlock     │
             ├──────────────────┤
             │  ref_count: 2    │ ← 引用计数
             │  weak_count: 0   │ ← 弱引用计数
             │  deleter         │
             └──────────────────┘

循环引用问题：
┌──────────┐      shared_ptr      ┌──────────┐
│  Node A  │ ────────────────────→ │  Node B  │
│          │                        │          │
│  next ───┼────────────────────────┼── prev   │
└──────────┘      shared_ptr      └──────────┘
     ↑                                    │
     │                                    │
     └────────────────────────────────────┘
         引用计数永远不为 0，内存泄漏！

解决方案：使用 weak_ptr
┌──────────┐      shared_ptr      ┌──────────┐
│  Node A  │ ────────────────────→ │  Node B  │
│          │                        │          │
│  next ───┼────────────────────────┼── prev   │
└──────────┘      weak_ptr         └──────────┘
     ↑                                    │
     │                                    │
     └────────────────────────────────────┘
         可以打破循环，正确释放
```

### 面试官追问 1

**面试官**：请实现一个简化版的 `shared_ptr`。

**答案**：

```cpp
template<typename T>
class SimpleSharedPtr {
private:
    T* ptr;
    int* ref_count;
    
    void release() {
        if (ref_count) {
            --(*ref_count);
            if (*ref_count == 0) {
                delete ptr;
                delete ref_count;
                ptr = nullptr;
                ref_count = nullptr;
            }
        }
    }
    
public:
    // 构造函数
    explicit SimpleSharedPtr(T* p = nullptr)
        : ptr(p), ref_count(p ? new int(1) : nullptr) {}
    
    // 拷贝构造函数
    SimpleSharedPtr(const SimpleSharedPtr& other)
        : ptr(other.ptr), ref_count(other.ref_count) {
        if (ref_count) {
            ++(*ref_count);
        }
    }
    
    // 赋值运算符
    SimpleSharedPtr& operator=(const SimpleSharedPtr& other) {
        if (this != &other) {
            release();
            ptr = other.ptr;
            ref_count = other.ref_count;
            if (ref_count) {
                ++(*ref_count);
            }
        }
        return *this;
    }
    
    // 析构函数
    ~SimpleSharedPtr() {
        release();
    }
    
    // 解引用
    T& operator*() const { return *ptr; }
    T* operator->() const { return ptr; }
    T* get() const { return ptr; }
    
    // 引用计数
    int use_count() const {
        return ref_count ? *ref_count : 0;
    }
    
    // 移动语义（C++11）
    SimpleSharedPtr(SimpleSharedPtr&& other) noexcept
        : ptr(other.ptr), ref_count(other.ref_count) {
        other.ptr = nullptr;
        other.ref_count = nullptr;
    }
    
    SimpleSharedPtr& operator=(SimpleSharedPtr&& other) noexcept {
        if (this != &other) {
            release();
            ptr = other.ptr;
            ref_count = other.ref_count;
            other.ptr = nullptr;
            other.ref_count = nullptr;
        }
        return *this;
    }
};

// 使用示例
void test_simple_shared_ptr() {
    SimpleSharedPtr<int> p1(new int(42));
    std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 1
    
    {
        SimpleSharedPtr<int> p2 = p1;
        std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 2
        std::cout << "p2 use_count: " << p2.use_count() << std::endl;  // 2
    }
    
    std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 1
}
```

### 面试官追问 2

**面试官**：`make_shared` 和直接构造 `shared_ptr` 有什么区别？

**答案**：`make_shared` 更高效，只分配一次内存。

```cpp
// 方式 1：直接构造（两次内存分配）
std::shared_ptr<int> p1(new int(42));
// 1. 分配 int 的内存
// 2. 分配 ControlBlock 的内存
// 总开销：两次分配

// 方式 2：make_shared（一次内存分配）
auto p2 = std::make_shared<int>(42);
// 1. 一次性分配包含 int 和 ControlBlock 的内存块
// 总开销：一次分配

// 性能对比
void performance_comparison() {
    // 方式 1：可能内存不连续
    // [int对象] ... [ControlBlock]
    
    // 方式 2：内存连续
    // [ControlBlock + int对象]
    // 更好的缓存局部性
}

// 注意：make_shared 的异常安全
void func(std::shared_ptr<int> p, int value) {
    // ...
}

// 可能的内存泄漏
func(std::shared_ptr<int>(new int(42)), compute());  
// 如果 compute() 抛出异常，new int(42) 可能泄漏

// 安全的做法
func(std::make_shared<int>(42), compute());
// make_shared 是异常安全的
```

### 面试官追问 3

**面试官**：什么时候应该使用 `weak_ptr`？

**答案**：主要用于解决循环引用和观察者模式。

```cpp
// 场景 1：循环引用
class Node {
public:
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // 使用 weak_ptr 打破循环
    
    ~Node() {
        std::cout << "Node destroyed" << std::endl;
    }
};

void circular_reference_demo() {
    auto node1 = std::make_shared<Node>();
    auto node2 = std::make_shared<Node>();
    
    node1->next = node2;
    node2->prev = node1;  // weak_ptr，不会增加引用计数
    
    // node1 和 node2 可以正确释放
}

// 场景 2：缓存
class Cache {
    std::unordered_map<int, std::weak_ptr<Resource>> cache;
    
public:
    std::shared_ptr<Resource> get(int key) {
        auto it = cache.find(key);
        if (it != cache.end()) {
            if (auto res = it->second.lock()) {
                return res;  // 资源还在
            } else {
                cache.erase(it);  // 资源已释放
            }
        }
        // 创建新资源
        auto res = std::make_shared<Resource>(key);
        cache[key] = res;
        return res;
    }
};

// 场景 3：观察者模式
class Subject {
    std::vector<std::weak_ptr<Observer>> observers;
    
public:
    void notify() {
        // 移除已失效的观察者
        observers.erase(
            std::remove_if(observers.begin(), observers.end(),
                [](const auto& wp) { return wp.expired(); }),
            observers.end()
        );
        
        // 通知有效的观察者
        for (auto& wp : observers) {
            if (auto obs = wp.lock()) {
                obs->update();
            }
        }
    }
};
```

---

## 问题 4：RAII 是什么？如何应用？

**面试官**：请解释 RAII 的概念，并举例说明如何应用。

### 标准答案

**RAII**（Resource Acquisition Is Initialization）：资源获取即初始化。

核心思想：
- 在对象构造时获取资源
- 在对象析构时释放资源
- 利用 C++ 的自动析构机制管理资源生命周期

优势：
- 异常安全
- 自动资源管理
- 代码简洁

### 代码示例

```cpp
#include <fstream>
#include <memory>
#include <mutex>

// 示例 1：文件管理
class FileRAII {
    std::ofstream file;
    
public:
    FileRAII(const std::string& filename) 
        : file(filename) {
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file");
        }
    }
    
    ~FileRAII() {
        if (file.is_open()) {
            file.close();  // 自动关闭
        }
    }
    
    void write(const std::string& data) {
        file << data;
    }
    
    // 禁止拷贝
    FileRAII(const FileRAII&) = delete;
    FileRAII& operator=(const FileRAII&) = delete;
};

// 使用
void file_demo() {
    FileRAII file("test.txt");
    file.write("Hello RAII");
    // 函数结束时自动关闭文件，即使抛出异常
}

// 示例 2：锁管理（标准库已实现）
void mutex_demo() {
    std::mutex mtx;
    
    {
        std::lock_guard<std::mutex> lock(mtx);
        // 临界区代码
        // lock 析构时自动解锁
    }  // 自动解锁
    
    // 即使抛出异常也会解锁
}

// 示例 3：自定义资源管理
class DatabaseConnection {
    // 假设的数据库连接句柄
    void* handle;
    
public:
    DatabaseConnection() {
        handle = connect_to_database();  // 获取资源
        if (!handle) {
            throw std::runtime_error("Connection failed");
        }
    }
    
    ~DatabaseConnection() {
        if (handle) {
            disconnect_from_database(handle);  // 释放资源
        }
    }
    
    void execute_query(const std::string& query) {
        // 使用连接
    }
    
    // 禁止拷贝
    DatabaseConnection(const DatabaseConnection&) = delete;
    DatabaseConnection& operator=(const DatabaseConnection&) = delete;
    
    // 允许移动
    DatabaseConnection(DatabaseConnection&& other) noexcept
        : handle(other.handle) {
        other.handle = nullptr;
    }
};

// 使用
void database_demo() {
    DatabaseConnection conn;
    conn.execute_query("SELECT * FROM users");
    // 自动断开连接
}
```

### RAII 原理图示

```
传统方式（容易泄漏）：
void bad_code() {
    FILE* f = fopen("file.txt", "r");
    if (some_condition) {
        return;  // 忘记关闭文件！
    }
    if (another_condition) {
        throw exception();  // 异常时文件未关闭！
    }
    fclose(f);
}

RAII 方式（自动管理）：
void good_code() {
    FileRAII file("file.txt");
    if (some_condition) {
        return;  // file 析构，自动关闭
    }
    if (another_condition) {
        throw exception();  // file 析构，自动关闭
    }
    // file 析构，自动关闭
}

资源生命周期：
┌─────────────────────────────────────┐
│  对象构造                            │
│  ┌───────────────────────────────┐   │
│  │  获取资源（文件、锁、内存等）  │   │
│  └───────────────────────────────┘   │
│                                      │
│  使用资源                            │
│  ┌───────────────────────────────┐   │
│  │  读写文件、持有锁、使用内存    │   │
│  └───────────────────────────────┘   │
│                                      │
│  对象析构（自动）                    │
│  ┌───────────────────────────────┐   │
│  │  释放资源（关闭文件、解锁等）  │   │
│  └───────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 面试官追问 1

**面试官**：如何实现一个通用的 RAII 包装器？

**答案**：使用模板和函数对象。

```cpp
template<typename Resource, typename Deleter>
class RAIIWrapper {
    Resource resource;
    Deleter deleter;
    bool valid;
    
public:
    template<typename... Args>
    RAIIWrapper(Deleter d, Args... args)
        : resource(std::forward<Args>(args)...), deleter(d), valid(true) {}
    
    ~RAIIWrapper() {
        if (valid) {
            deleter(resource);
        }
    }
    
    // 禁止拷贝
    RAIIWrapper(const RAIIWrapper&) = delete;
    RAIIWrapper& operator=(const RAIIWrapper&) = delete;
    
    // 允许移动
    RAIIWrapper(RAIIWrapper&& other) noexcept
        : resource(std::move(other.resource)),
          deleter(std::move(other.deleter)),
          valid(other.valid) {
        other.valid = false;
    }
    
    Resource& get() { return resource; }
    const Resource& get() const { return resource; }
    Resource* operator->() { return &resource; }
    Resource& operator*() { return resource; }
};

// 辅助函数
template<typename Resource, typename Deleter, typename... Args>
auto make_raii(Deleter deleter, Args... args) {
    return RAIIWrapper<Resource, Deleter>(deleter, std::forward<Args>(args)...);
}

// 使用示例
void generic_raii_demo() {
    // C 风格文件
    auto file = make_raii<FILE*>(
        [](FILE* f) { if (f) fclose(f); },
        fopen("test.txt", "r")
    );
    
    // 自定义资源
    auto handle = make_raii<void*>(
        [](void* h) { release_handle(h); },
        acquire_handle()
    );
}
```

### 面试官追问 2

**面试官**：RAII 和异常安全有什么关系？

**答案**：RAII 是实现异常安全的关键技术。

```cpp
// 异常安全级别

// 1. 基本保证：不泄漏资源
void basic_guarantee() {
    std::unique_ptr<int> p(new int(42));
    may_throw();  // 如果抛出异常，p 自动释放内存
}

// 2. 强保证：要么成功，要么回滚
class Transaction {
    std::vector<int> data;
    
public:
    void add(int value) {
        data.push_back(value);
        may_throw();  // 如果失败，data 自动回滚（vector 保证）
    }
    // vector 的 push_back 提供强保证
};

// 3. 不抛出保证：操作不会失败
void no_throw() noexcept {
    std::lock_guard<std::mutex> lock(mtx);
    // 操作不会抛出异常
}

// 示例：异常安全的资源管理
class ResourceManager {
    std::vector<std::unique_ptr<Resource>> resources;
    
public:
    void add_resource(std::unique_ptr<Resource> res) {
        // 如果 push_back 失败，res 会自动释放
        resources.push_back(std::move(res));
    }
    
    // 如果析构时抛出异常，其他资源仍会释放
    ~ResourceManager() {
        // 逐个释放，即使某个抛出异常
        for (auto it = resources.rbegin(); it != resources.rend(); ++it) {
            try {
                it->reset();
            } catch (...) {
                // 记录错误，继续释放其他资源
            }
        }
    }
};
```

### 面试官追问 3

**面试官**：智能指针是 RAII 的应用吗？

**答案**：是的，智能指针是 RAII 的典型应用。

```cpp
// unique_ptr 实现 RAII
{
    std::unique_ptr<int> p(new int(42));
    // 使用 p
}  // 自动 delete

// shared_ptr 实现 RAII
{
    auto p = std::make_shared<Resource>();
    // 多个 shared_ptr 共享资源
}  // 最后一个 shared_ptr 析构时自动释放

// 自定义删除器的 RAII
{
    std::unique_ptr<FILE, decltype(&fclose)> file(
        fopen("test.txt", "r"),
        fclose
    );
    // 使用文件
}  // 自动 fclose

// 数组的 RAII
{
    std::unique_ptr<int[]> arr(new int[100]);
    // 使用数组
}  // 自动 delete[]
```

---

## 问题 5：new/delete 和 malloc/free 的区别

**面试官**：请详细说明 `new/delete` 和 `malloc/free` 的区别。

### 标准答案

主要区别：

1. **类型安全**：new 返回类型化指针，malloc 返回 void*
2. **构造函数/析构函数**：new 调用构造函数，delete 调用析构函数
3. **内存大小**：new 自动计算大小，malloc 需要手动指定
4. **失败处理**：new 抛出异常，malloc 返回 nullptr
5. **重载**：new/delete 可以重载，malloc/free 不能
6. **内存对齐**：new 保证对齐，malloc 可能不保证

### 代码示例

```cpp
#include <cstdlib>
#include <new>
#include <iostream>

class MyClass {
    int value;
public:
    MyClass(int v) : value(v) {
        std::cout << "Constructor: " << value << std::endl;
    }
    
    ~MyClass() {
        std::cout << "Destructor: " << value << std::endl;
    }
};

void comparison_demo() {
    // malloc/free：不调用构造函数和析构函数
    void* raw_mem = malloc(sizeof(MyClass));
    MyClass* obj1 = static_cast<MyClass*>(raw_mem);
    // obj1->value 未初始化！
    free(obj1);  // 不调用析构函数
    
    // new/delete：调用构造函数和析构函数
    MyClass* obj2 = new MyClass(42);
    delete obj2;  // 自动调用析构函数
    
    // 数组版本
    int* arr1 = (int*)malloc(10 * sizeof(int));
    free(arr1);
    
    int* arr2 = new int[10];
    delete[] arr2;  // 注意：delete[] 不是 delete
}

// 异常处理
void exception_handling() {
    // malloc：返回 nullptr
    void* ptr = malloc(1000000000);
    if (ptr == nullptr) {
        std::cout << "malloc failed" << std::endl;
    }
    
    // new：抛出异常
    try {
        int* p = new int[1000000000];
        delete[] p;
    } catch (const std::bad_alloc& e) {
        std::cout << "new failed: " << e.what() << std::endl;
    }
    
    // C++11 no-throw new
    int* p = new(std::nothrow) int[1000000000];
    if (p == nullptr) {
        std::cout << "new(nothrow) failed" << std::endl;
    }
}

// 类型安全
void type_safety() {
    // malloc：需要类型转换
    int* p1 = (int*)malloc(sizeof(int));
    
    // new：类型安全
    int* p2 = new int;
    
    // 数组大小计算
    int arr[10];
    // malloc：需要手动计算
    int* p3 = (int*)malloc(10 * sizeof(int));
    // new：自动计算
    int* p4 = new int[10];
}
```

### 对比表格

| 特性 | new/delete | malloc/free |
|------|------------|-------------|
| 类型安全 | ✓ 返回类型化指针 | ✗ 返回 void* |
| 构造函数 | ✓ 自动调用 | ✗ 不调用 |
| 析构函数 | ✓ 自动调用 | ✗ 不调用 |
| 大小计算 | ✓ 自动计算 | ✗ 手动指定 |
| 失败处理 | 抛出异常 | 返回 nullptr |
| 重载 | ✓ 可以重载 | ✗ 不能重载 |
| 内存对齐 | ✓ 保证对齐 | ✗ 可能不对齐 |
| C++ 标准 | C++ 特性 | C 特性 |

### 面试官追问 1

**面试官**：可以混用 new 和 free，或者 malloc 和 delete 吗？

**答案**：**绝对不可以**！会导致未定义行为。

```cpp
// 错误示例 1：new + free
void wrong1() {
    int* p = new int(42);
    free(p);  // 未定义行为！
    // new 可能使用不同的内存管理机制
    // free 不知道如何正确释放
}

// 错误示例 2：malloc + delete
void wrong2() {
    int* p = (int*)malloc(sizeof(int));
    delete p;  // 未定义行为！
    // malloc 分配的内存，delete 可能无法正确释放
}

// 错误示例 3：new[] + delete（不是 delete[]）
void wrong3() {
    int* arr = new int[10];
    delete arr;  // 未定义行为！
    // 应该使用 delete[] arr;
}

// 正确配对
void correct() {
    // new ↔ delete
    int* p1 = new int;
    delete p1;
    
    // new[] ↔ delete[]
    int* arr = new int[10];
    delete[] arr;
    
    // malloc ↔ free
    void* p2 = malloc(sizeof(int));
    free(p2);
}
```

### 面试官追问 2

**面试官**：如何重载 new 和 delete？

**答案**：可以在类级别或全局级别重载。

```cpp
#include <cstdlib>
#include <new>
#include <iostream>

// 全局重载
void* operator new(size_t size) {
    std::cout << "Global new: " << size << " bytes" << std::endl;
    void* ptr = malloc(size);
    if (!ptr) {
        throw std::bad_alloc();
    }
    return ptr;
}

void operator delete(void* ptr) noexcept {
    std::cout << "Global delete" << std::endl;
    free(ptr);
}

// 类级别重载
class CustomAlloc {
public:
    // 普通 new
    void* operator new(size_t size) {
        std::cout << "CustomAlloc::new: " << size << std::endl;
        return ::operator new(size);
    }
    
    void operator delete(void* ptr) {
        std::cout << "CustomAlloc::delete" << std::endl;
        ::operator delete(ptr);
    }
    
    // 数组版本
    void* operator new[](size_t size) {
        std::cout << "CustomAlloc::new[]: " << size << std::endl;
        return ::operator new[](size);
    }
    
    void operator delete[](void* ptr) {
        std::cout << "CustomAlloc::delete[]" << std::endl;
        ::operator delete[](ptr);
    }
    
    // placement new（不分配内存，在指定位置构造）
    void* operator new(size_t size, void* place) {
        return place;
    }
};

// 使用
void overload_demo() {
    CustomAlloc* obj = new CustomAlloc;
    delete obj;
    
    CustomAlloc* arr = new CustomAlloc[5];
    delete[] arr;
    
    // placement new
    char buffer[sizeof(CustomAlloc)];
    CustomAlloc* placed = new(buffer) CustomAlloc;
    placed->~CustomAlloc();  // 手动调用析构函数
}
```

### 面试官追问 3

**面试官**：什么时候应该使用 malloc/free？

**答案**：主要在 C 兼容代码或特殊场景中使用。

```cpp
// 场景 1：C 接口
extern "C" {
    void c_function(void* data);
}

void c_interface_demo() {
    void* data = malloc(100);
    c_function(data);
    free(data);
}

// 场景 2：需要 realloc
void realloc_demo() {
    int* arr = (int*)malloc(10 * sizeof(int));
    // 需要扩展
    arr = (int*)realloc(arr, 20 * sizeof(int));
    // C++ 没有 realloc 的等价物
    free(arr);
}

// 场景 3：对齐分配（C++11 有更好的方法）
#include <cstdlib>
void* aligned_malloc(size_t size, size_t alignment) {
    void* ptr = nullptr;
    posix_memalign(&ptr, alignment, size);
    return ptr;
}

// C++11 推荐方式
#include <memory>
void cpp11_aligned() {
    alignas(64) int arr[100];  // 栈上对齐
    
    // 堆上对齐（C++17）
    auto ptr = std::aligned_storage<sizeof(int), 64>::type;
    // 或使用 aligned_alloc（C++17）
}
```

---

## 问题 6：placement new 是什么？如何使用？

**面试官**：请解释 placement new 的概念和使用场景。

### 标准答案

**placement new**：在已分配的内存上构造对象，不分配新内存。

特点：
- 不分配内存，只调用构造函数
- 需要手动调用析构函数
- 常用于内存池、缓冲区管理

语法：
```cpp
new(ptr) Type(args...)
```

### 代码示例

```cpp
#include <new>
#include <iostream>
#include <cstring>

class MyClass {
    int value;
public:
    MyClass(int v) : value(v) {
        std::cout << "Constructor: " << value << std::endl;
    }
    
    ~MyClass() {
        std::cout << "Destructor: " << value << std::endl;
    }
    
    int get() const { return value; }
};

void basic_placement_new() {
    // 分配原始内存
    char buffer[sizeof(MyClass)];
    
    // 在 buffer 上构造对象
    MyClass* obj = new(buffer) MyClass(42);
    std::cout << "Value: " << obj->get() << std::endl;
    
    // 手动调用析构函数
    obj->~MyClass();
    
    // buffer 可以重用
    MyClass* obj2 = new(buffer) MyClass(100);
    obj2->~MyClass();
}

// 内存池实现
class MemoryPool {
    char pool[1024];
    size_t offset;
    
public:
    MemoryPool() : offset(0) {}
    
    template<typename T, typename... Args>
    T* allocate(Args... args) {
        // 检查对齐
        size_t align = alignof(T);
        offset = (offset + align - 1) & ~(align - 1);
        
        if (offset + sizeof(T) > sizeof(pool)) {
            throw std::bad_alloc();
        }
        
        void* ptr = pool + offset;
        offset += sizeof(T);
        
        // placement new
        return new(ptr) T(std::forward<Args>(args)...);
    }
    
    void reset() {
        offset = 0;
    }
};

// 使用内存池
void memory_pool_demo() {
    MemoryPool pool;
    
    int* p1 = pool.allocate<int>(10);
    double* p2 = pool.allocate<double>(3.14);
    
    std::cout << *p1 << " " << *p2 << std::endl;
    
    // 手动析构
    p1->~int();
    p2->~double();
    
    pool.reset();  // 重置池，可以重用
}

// 缓冲区管理
template<typename T>
class Buffer {
    T* data;
    size_t capacity;
    size_t size;
    
public:
    Buffer(size_t cap) 
        : capacity(cap), size(0) {
        // 只分配内存，不构造对象
        data = static_cast<T*>(::operator new(capacity * sizeof(T)));
    }
    
    ~Buffer() {
        // 析构所有对象
        for (size_t i = 0; i < size; ++i) {
            data[i].~T();
        }
        // 释放内存
        ::operator delete(data);
    }
    
    template<typename... Args>
    void emplace_back(Args... args) {
        if (size >= capacity) {
            throw std::bad_alloc();
        }
        // placement new
        new(data + size) T(std::forward<Args>(args)...);
        ++size;
    }
    
    T& operator[](size_t index) {
        return data[index];
    }
};

void buffer_demo() {
    Buffer<MyClass> buf(10);
    buf.emplace_back(1);
    buf.emplace_back(2);
    buf.emplace_back(3);
    
    std::cout << buf[0].get() << std::endl;
}
```

### placement new 原理图示

```
普通 new：
┌─────────────────────────────────┐
│  1. 分配内存（operator new）     │
│  2. 调用构造函数                 │
│  3. 返回指针                     │
└─────────────────────────────────┘

placement new：
┌─────────────────────────────────┐
│  已有内存（buffer、内存池等）     │
│         ↓                        │
│  1. 跳过内存分配                 │
│  2. 在指定位置调用构造函数        │
│  3. 返回指针                     │
└─────────────────────────────────┘

内存布局示例：
┌─────────────────────────────────┐
│  char buffer[sizeof(MyClass)]   │ ← 原始内存
├─────────────────────────────────┤
│  new(buffer) MyClass(42)        │ ← placement new
├─────────────────────────────────┤
│  MyClass 对象                    │ ← 构造后的对象
│  ┌─────────────┐                │
│  │ value = 42  │                │
│  └─────────────┘                │
└─────────────────────────────────┘
```

### 面试官追问 1

**面试官**：placement new 和普通 new 在性能上有什么区别？

**答案**：placement new 避免了内存分配的开销。

```cpp
#include <chrono>
#include <vector>

// 性能对比
void performance_comparison() {
    const int N = 1000000;
    
    // 方式 1：普通 new
    auto start1 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < N; ++i) {
        MyClass* p = new MyClass(i);
        delete p;
    }
    auto end1 = std::chrono::high_resolution_clock::now();
    
    // 方式 2：placement new（预分配）
    char* pool = new char[N * sizeof(MyClass)];
    auto start2 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < N; ++i) {
        MyClass* p = new(pool + i * sizeof(MyClass)) MyClass(i);
        p->~MyClass();
    }
    auto end2 = std::chrono::high_resolution_clock::now();
    
    auto time1 = std::chrono::duration_cast<std::chrono::milliseconds>(
        end1 - start1).count();
    auto time2 = std::chrono::duration_cast<std::chrono::milliseconds>(
        end2 - start2).count();
    
    std::cout << "Normal new: " << time1 << "ms" << std::endl;
    std::cout << "Placement new: " << time2 << "ms" << std::endl;
    
    delete[] pool;
}

// 应用场景：高频对象创建
class ObjectPool {
    std::vector<char> pool;
    std::vector<bool> used;
    size_t object_size;
    
public:
    ObjectPool(size_t count, size_t obj_size)
        : pool(count * obj_size), used(count, false), object_size(obj_size) {}
    
    template<typename T, typename... Args>
    T* acquire(Args... args) {
        for (size_t i = 0; i < used.size(); ++i) {
            if (!used[i]) {
                used[i] = true;
                return new(pool.data() + i * object_size) T(
                    std::forward<Args>(args)...);
            }
        }
        return nullptr;  // 池已满
    }
    
    template<typename T>
    void release(T* obj) {
        obj->~T();
        size_t index = (reinterpret_cast<char*>(obj) - pool.data()) 
                       / object_size;
        used[index] = false;
    }
};
```

### 面试官追问 2

**面试官**：placement new 有什么注意事项？

**答案**：需要注意对齐、生命周期管理、异常安全。

```cpp
// 注意 1：内存对齐
void alignment_issue() {
    char buffer[sizeof(MyClass) + alignof(MyClass)];
    void* aligned = buffer;
    
    // 手动对齐
    std::size_t space = sizeof(buffer);
    std::align(alignof(MyClass), sizeof(MyClass), aligned, space);
    
    MyClass* obj = new(aligned) MyClass(42);
    obj->~MyClass();
}

// 注意 2：不要 delete placement new 的对象
void wrong_usage() {
    char buffer[sizeof(MyClass)];
    MyClass* obj = new(buffer) MyClass(42);
    
    // delete obj;  // 错误！buffer 不是堆内存
    // 正确做法：
    obj->~MyClass();
}

// 注意 3：异常安全
class ExceptionSafe {
    MyClass* obj;
    char* buffer;
    
public:
    ExceptionSafe() : obj(nullptr), buffer(new char[sizeof(MyClass)]) {
        try {
            obj = new(buffer) MyClass(42);
        } catch (...) {
            delete[] buffer;
            throw;
        }
    }
    
    ~ExceptionSafe() {
        if (obj) {
            obj->~MyClass();
        }
        delete[] buffer;
    }
};

// 注意 4：数组的 placement new
void array_placement_new() {
    const int N = 10;
    char* buffer = new char[N * sizeof(int)];
    
    int* arr = new(buffer) int[N];  // 构造数组
    
    // 使用数组
    for (int i = 0; i < N; ++i) {
        arr[i] = i;
    }
    
    // 析构数组（逆序）
    for (int i = N - 1; i >= 0; --i) {
        arr[i].~int();
    }
    
    delete[] buffer;
}
```

### 面试官追问 3

**面试官**：标准库中哪些地方使用了 placement new？

**答案**：`std::vector`、`std::optional`、`std::variant` 等都使用了 placement new。

```cpp
#include <vector>
#include <optional>
#include <variant>

// std::vector 的实现原理（简化）
template<typename T>
class SimpleVector {
    T* data;
    size_t size_;
    size_t capacity_;
    
public:
    void reserve(size_t new_cap) {
        if (new_cap > capacity_) {
            T* new_data = static_cast<T*>(
                ::operator new(new_cap * sizeof(T)));
            
            // 移动现有元素
            for (size_t i = 0; i < size_; ++i) {
                new(new_data + i) T(std::move(data[i]));
                data[i].~T();
            }
            
            ::operator delete(data);
            data = new_data;
            capacity_ = new_cap;
        }
    }
    
    template<typename... Args>
    void emplace_back(Args... args) {
        if (size_ >= capacity_) {
            reserve(capacity_ * 2);
        }
        new(data + size_) T(std::forward<Args>(args)...);
        ++size_;
    }
};

// std::optional 的实现（简化）
template<typename T>
class SimpleOptional {
    alignas(T) char storage[sizeof(T)];
    bool has_value;
    
public:
    template<typename... Args>
    void emplace(Args... args) {
        reset();
        new(storage) T(std::forward<Args>(args)...);
        has_value = true;
    }
    
    void reset() {
        if (has_value) {
            value().~T();
            has_value = false;
        }
    }
    
    T& value() {
        return *reinterpret_cast<T*>(storage);
    }
    
    ~SimpleOptional() {
        reset();
    }
};
```

---

## 问题 7：移动语义和完美转发

**面试官**：请解释 C++11 的移动语义和完美转发的概念和实现。

### 标准答案

**移动语义**：
- 避免不必要的拷贝，提高性能
- 通过右值引用（`&&`）实现
- `std::move` 将左值转换为右值

**完美转发**：
- 保持参数的值类别（左值/右值）
- 通过万能引用（`T&&`）和 `std::forward` 实现
- 用于泛型编程中的参数传递

### 代码示例

```cpp
#include <utility>
#include <iostream>
#include <vector>

// 移动语义示例
class Movable {
    int* data;
    size_t size;
    
public:
    Movable(size_t s) : size(s) {
        data = new int[size];
        std::cout << "Constructor" << std::endl;
    }
    
    // 拷贝构造函数
    Movable(const Movable& other) : size(other.size) {
        data = new int[size];
        std::copy(other.data, other.data + size, data);
        std::cout << "Copy constructor" << std::endl;
    }
    
    // 移动构造函数
    Movable(Movable&& other) noexcept 
        : data(other.data), size(other.size) {
        other.data = nullptr;
        other.size = 0;
        std::cout << "Move constructor" << std::endl;
    }
    
    // 拷贝赋值
    Movable& operator=(const Movable& other) {
        if (this != &other) {
            delete[] data;
            size = other.size;
            data = new int[size];
            std::copy(other.data, other.data + size, data);
            std::cout << "Copy assignment" << std::endl;
        }
        return *this;
    }
    
    // 移动赋值
    Movable& operator=(Movable&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = other.data;
            size = other.size;
            other.data = nullptr;
            other.size = 0;
            std::cout << "Move assignment" << std::endl;
        }
        return *this;
    }
    
    ~Movable() {
        delete[] data;
    }
};

void move_semantics_demo() {
    Movable m1(1000);
    Movable m2 = std::move(m1);  // 调用移动构造函数
    Movable m3(500);
    m3 = std::move(m2);  // 调用移动赋值
    
    // 临时对象自动移动
    Movable m4 = Movable(2000);  // 移动构造
}

// 完美转发示例
template<typename T>
void wrapper(T&& arg) {
    // arg 总是左值，但 T 保留了原始值类别信息
    target(std::forward<T>(arg));
}

void target(int& x) {
    std::cout << "lvalue: " << x << std::endl;
}

void target(int&& x) {
    std::cout << "rvalue: " << x << std::endl;
}

void perfect_forwarding_demo() {
    int x = 42;
    wrapper(x);      // 调用 target(int&)
    wrapper(100);    // 调用 target(int&&)
}

// 实际应用：emplace_back
void emplace_demo() {
    std::vector<std::string> vec;
    
    std::string s = "hello";
    vec.push_back(s);           // 拷贝
    vec.push_back(std::move(s)); // 移动
    vec.emplace_back("world");  // 直接构造，完美转发
}
```

### 移动语义原理图示

```
拷贝语义：
┌─────────────┐
│  Object A   │
│  data: [1,2,3]│
└─────────────┘
      │ 拷贝
      ↓
┌─────────────┐
│  Object B   │
│  data: [1,2,3]│ ← 新分配内存，复制数据
└─────────────┘

移动语义：
┌─────────────┐
│  Object A   │
│  data: [1,2,3]│
└─────────────┘
      │ 移动（转移所有权）
      ↓
┌─────────────┐      ┌─────────────┐
│  Object B   │      │  Object A   │
│  data: [1,2,3]│ ←── │  data: nullptr│（已清空）
└─────────────┘      └─────────────┘
```

### 面试官追问 1

**面试官**：`std::move` 做了什么？它移动了什么吗？

**答案**：`std::move` 只是类型转换，不移动任何东西。

```cpp
// std::move 的实现（简化）
template<typename T>
typename std::remove_reference<T>::type&& move(T&& arg) noexcept {
    return static_cast<typename std::remove_reference<T>::type&&>(arg);
}

// 示例
void move_explained() {
    int x = 42;
    
    // move 只是转换类型
    int&& rref = std::move(x);  // x 仍然是 42！
    
    // 真正的移动发生在移动构造函数/赋值中
    std::string s1 = "hello";
    std::string s2 = std::move(s1);  
    // move 转换类型 → 匹配移动构造函数 → 真正移动数据
    // s1 现在可能是空字符串（取决于实现）
}

// 常见误解
void misconception() {
    std::vector<int> vec1{1, 2, 3};
    std::vector<int> vec2 = std::move(vec1);
    
    // vec1 现在是未指定状态（通常是空的）
    // 但可以安全地重新赋值
    vec1 = {4, 5, 6};  // OK
}
```

### 面试官追问 2

**面试官**：引用折叠规则是什么？

**答案**：引用折叠是完美转发的基础。

```cpp
// 引用折叠规则
// T& &   → T&
// T& &&  → T&
// T&& &  → T&
// T&& && → T&&

template<typename T>
void func(T&& param) {
    // T 的推导：
    // 如果传入左值 int&，T = int&，T&& = int& && = int&
    // 如果传入右值 int，T = int，T&& = int&&
}

void reference_collapsing() {
    int x = 42;
    
    func(x);   // T = int&, param 类型是 int&
    func(100); // T = int, param 类型是 int&&
    
    // 万能引用（Universal Reference）
    // T&& 在模板推导中可能是左值引用或右值引用
}

// 完美转发的实现
template<typename T>
T&& forward(typename std::remove_reference<T>::type& arg) noexcept {
    return static_cast<T&&>(arg);
}

// 当 T = int&: 返回 int& && = int&（左值）
// 当 T = int:  返回 int &&     = int&&（右值）
```

### 面试官追问 3

**面试官**：什么时候应该使用移动语义？

**答案**：在需要转移所有权、避免拷贝的场景中使用。

```cpp
// 场景 1：容器操作
void container_move() {
    std::vector<std::string> vec;
    std::string large_string(10000, 'a');
    
    // 方式 1：拷贝（慢）
    vec.push_back(large_string);
    
    // 方式 2：移动（快）
    vec.push_back(std::move(large_string));
    
    // 方式 3：直接构造（最快）
    vec.emplace_back(10000, 'a');
}

// 场景 2：函数返回值优化（RVO/NRVO）
std::vector<int> create_vector() {
    std::vector<int> vec{1, 2, 3, 4, 5};
    return vec;  // 编译器可能优化，也可能移动
}

void return_value() {
    auto vec = create_vector();  // 可能移动，不拷贝
}

// 场景 3：交换操作
template<typename T>
void swap_move(T& a, T& b) {
    T temp = std::move(a);
    a = std::move(b);
    b = std::move(temp);
}

// 场景 4：资源管理类
class UniqueResource {
    void* resource;
    
public:
    UniqueResource(UniqueResource&& other) noexcept
        : resource(other.resource) {
        other.resource = nullptr;
    }
    
    UniqueResource& operator=(UniqueResource&& other) noexcept {
        if (this != &other) {
            release();
            resource = other.resource;
            other.resource = nullptr;
        }
        return *this;
    }
    
    // 禁止拷贝
    UniqueResource(const UniqueResource&) = delete;
    UniqueResource& operator=(const UniqueResource&) = delete;
};

// 场景 5：工厂函数
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}
```

---

## 高频考点总结

| 考点 | 频率 | 难度 | 关键知识 |
|------|------|------|----------|
| 对象内存布局 | ★★★ | ★★☆ | vptr、成员顺序、对齐 |
| 虚函数实现 | ★★★ | ★★★ | vtable、vptr、多重继承 |
| 智能指针 | ★★★ | ★★☆ | unique_ptr、shared_ptr、weak_ptr |
| RAII | ★★★ | ★★☆ | 资源管理、异常安全 |
| new/delete | ★★☆ | ★☆☆ | 与 malloc/free 区别 |
| placement new | ★★☆ | ★★☆ | 内存池、缓冲区管理 |
| 移动语义 | ★★★ | ★★★ | 右值引用、std::move |
| 完美转发 | ★★☆ | ★★★ | 万能引用、std::forward |

---

## 相关文章

- [上一篇：C++笔试题-模板元编程](/articles/cpp/cpp-42-C++笔试题-模板元编程/)
- [下一篇：C++面试题-并发与多线程](/articles/cpp/cpp-44-C++面试题-并发与多线程/)
