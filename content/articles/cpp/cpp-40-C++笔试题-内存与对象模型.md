+++
title = "40.C++笔试题-内存与对象模型"
date = 2026-01-31
description = "C++内存与对象模型笔试题：虚函数表、内存布局、RAII、智能指针"
[taxonomies]
tags = ["C++", "笔试", "内存模型", "对象模型", "虚函数"]
+++

# C++ 笔试题 - 内存与对象模型

本文汇集 C++ 内存与对象模型相关的笔试题，覆盖虚函数表、内存布局、RAII、智能指针等核心概念。

**难度标注**：★☆☆ 基础 | ★★☆ 中级 | ★★★ 困难

---

## 一、选择题

### 题目 1 ★☆☆

以下代码输出什么？

```cpp
class Base {
public:
    virtual void foo() { cout << "Base"; }
};

class Derived : public Base {
public:
    void foo() override { cout << "Derived"; }
};

int main() {
    Base *p = new Derived();
    p->foo();
    delete p;
}
```

A. Base  
B. Derived  
C. 编译错误  
D. 未定义行为

<details>
<summary>查看答案与解析</summary>

**答案：B**

**解析**：
- `foo()` 是虚函数
- 通过基类指针调用虚函数时，发生动态绑定
- 运行时根据对象实际类型调用 `Derived::foo()`

```
内存布局：
Base* p → [vptr][...]
              ↓
          vtable:
          [&Derived::foo]  ← 实际调用这个
```

**注意**：这里有个潜在问题——Base 没有虚析构函数，delete p 是未定义行为。

</details>

---

### 题目 2 ★★☆

以下类的 sizeof 是多少？（64位系统）

```cpp
class A {
    char a;
    int b;
    char c;
};
```

A. 6  
B. 9  
C. 12  
D. 16

<details>
<summary>查看答案与解析</summary>

**答案：C**

**内存布局分析**：

```
偏移  成员  大小  对齐
0     a     1    1
1-3   pad   3    -  (int 需要 4 字节对齐)
4-7   b     4    4
8     c     1    1
9-11  pad   3    -  (结构体按最大对齐 4)
总计: 12 字节
```

**优化后**：
```cpp
class A_optimized {
    int b;    // 4
    char a;   // 1
    char c;   // 1
    // pad 2
};  // sizeof = 8
```

</details>

---

### 题目 3 ★★☆

以下代码有什么问题？

```cpp
class Widget {
public:
    Widget() { init(); }
    virtual void init() { cout << "Widget::init"; }
};

class Button : public Widget {
public:
    void init() override { cout << "Button::init"; }
};

int main() {
    Button b;  // 输出什么？
}
```

A. Button::init  
B. Widget::init  
C. 编译错误  
D. 未定义行为

<details>
<summary>查看答案与解析</summary>

**答案：B**

**解析**：
- 构造函数中调用虚函数不会发生多态
- 构造 Button 时，先调用 Widget 构造函数
- 此时 vptr 指向 Widget 的 vtable
- 所以调用 Widget::init()

```
构造顺序：
1. Widget::Widget() 开始
2. vptr = &Widget::vtable
3. init() → Widget::init()  // 此时是 Widget
4. Widget::Widget() 结束
5. Button 部分构造
6. vptr = &Button::vtable
7. Button::Button() 结束
```

**最佳实践**：避免在构造/析构函数中调用虚函数。

</details>

---

### 题目 4 ★★★

以下代码输出什么？

```cpp
class A { public: int a; };
class B { public: int b; };
class C : public A, public B { public: int c; };

int main() {
    C obj;
    A *pa = &obj;
    B *pb = &obj;
    C *pc = &obj;
    
    cout << (pa == pc) << " ";
    cout << (pb == pc) << " ";
    cout << ((void*)pa == (void*)pc) << " ";
    cout << ((void*)pb == (void*)pc);
}
```

A. 1 1 1 1  
B. 1 1 1 0  
C. 1 1 0 0  
D. 0 0 0 0

<details>
<summary>查看答案与解析</summary>

**答案：B**

**内存布局**：

```
C 对象布局：
偏移 0:  [A 部分: int a]  ← pa, pc 指向这里
偏移 4:  [B 部分: int b]  ← pb 指向这里
偏移 8:  [C 部分: int c]
```

**分析**：
```cpp
pa == pc  // 比较时 C* 转换为 A*，地址相同，结果 1
pb == pc  // 比较时 C* 转换为 B*，编译器调整地址使逻辑相等，结果 1
(void*)pa == (void*)pc  // 转为 void* 不调整，地址相同，结果 1
(void*)pb == (void*)pc  // 转为 void* 不调整，pb 实际偏移 4，结果 0
```

</details>

---

### 题目 5 ★★★

以下代码的问题是什么？

```cpp
class Base {
public:
    ~Base() { cout << "~Base"; }
};

class Derived : public Base {
    int *data;
public:
    Derived() : data(new int[100]) {}
    ~Derived() { delete[] data; cout << "~Derived"; }
};

int main() {
    Base *p = new Derived();
    delete p;
}
```

A. 编译错误  
B. 运行正常  
C. 内存泄漏  
D. 双重释放

<details>
<summary>查看答案与解析</summary>

**答案：C**

**问题**：Base 析构函数不是虚函数。

```
delete p 时：
1. p 是 Base* 类型
2. 析构函数非虚，静态绑定
3. 只调用 ~Base()
4. ~Derived() 未被调用
5. data 未被释放 → 内存泄漏
```

**修复**：

```cpp
class Base {
public:
    virtual ~Base() { cout << "~Base"; }  // 虚析构
};
```

**规则**：
- 有虚函数的类应该有虚析构函数
- 作为基类的类应该有虚析构函数
- 不打算继承的类可以用 final 标记

</details>

---

## 二、填空题

### 题目 6 ★☆☆

C++ 对象的内存布局通常包含：______ 指针（如果有虚函数）、______ 成员变量、______ 信息（如果有虚基类）。

<details>
<summary>查看答案</summary>

**答案**：vptr（虚函数表）、非静态成员变量、虚基类偏移

**典型布局**：

| 偏移 | 内容 | 说明 |
|------|------|------|
| 0 | vptr | → vtable |
| +8 | 基类成员 | |
| +X | 派生类成员 | |
| +Y | 虚基类指针/偏移 | (如果有虚继承) |

**验证**：
```cpp
class A {
    virtual void f() {}
    int x;
};

cout << sizeof(A);  // 16（8字节vptr + 4字节x + 4字节对齐）
```

</details>

---

### 题目 7 ★★☆

智能指针 `unique_ptr` 和 `shared_ptr` 的主要区别是：`unique_ptr` 使用 ______ 语义，`shared_ptr` 使用 ______ 计数，`shared_ptr` 的循环引用需要用 ______ 打破。

<details>
<summary>查看答案</summary>

**答案**：移动（独占所有权）、引用计数、`weak_ptr`

```cpp
// unique_ptr：独占所有权
unique_ptr<int> p1(new int(42));
unique_ptr<int> p2 = move(p1);  // 所有权转移
// p1 现在为空

// shared_ptr：共享所有权
shared_ptr<int> s1(new int(42));
shared_ptr<int> s2 = s1;  // 引用计数 +1
cout << s1.use_count();   // 2

// weak_ptr：打破循环引用
struct Node {
    shared_ptr<Node> next;
    weak_ptr<Node> prev;  // 使用 weak_ptr
};
```

</details>

---

### 题目 8 ★★★

虚函数调用的开销包括：通过 ______ 间接跳转、可能的 ______ 未命中、阻止编译器 ______ 优化。

<details>
<summary>查看答案</summary>

**答案**：vptr/vtable（虚函数表）、缓存/分支预测、内联

**虚函数调用过程**：
```asm
; obj->virtual_func()
mov rax, [rdi]          ; 加载 vptr
mov rax, [rax + offset] ; 加载函数地址
call rax                ; 间接调用
```

**开销分析**：

| 开销 | 原因 |
|------|------|
| 间接跳转 | 通过 vtable 查找 |
| 缓存未命中 | vtable 可能不在缓存 |
| 分支预测失败 | 间接调用难预测 |
| 无法内联 | 编译时不知道目标函数 |

**优化策略**：
```cpp
// 1. final 阻止重写，允许去虚化
class Derived final : public Base {
    void func() final override { }
};

// 2. 已知类型时直接调用
Derived d;
d.func();  // 可能被优化为直接调用
```

</details>

---

## 三、简答题

### 题目 9 ★★☆

解释 RAII（Resource Acquisition Is Initialization）的原理和应用。

<details>
<summary>参考答案</summary>

**原理**：
- 资源获取即初始化
- 在构造函数中获取资源
- 在析构函数中释放资源
- 利用栈展开保证资源释放

**优点**：
1. 异常安全
2. 避免资源泄漏
3. 代码简洁

**应用示例**：

```cpp
// 1. 智能指针
{
    unique_ptr<int> p(new int(42));
    // 使用 p
}  // 自动 delete

// 2. 锁管理
{
    lock_guard<mutex> lock(mtx);
    // 临界区
}  // 自动解锁

// 3. 文件句柄
class File {
    FILE *fp;
public:
    File(const char *name) : fp(fopen(name, "r")) {
        if (!fp) throw runtime_error("open failed");
    }
    ~File() { if (fp) fclose(fp); }
    
    // 禁止拷贝
    File(const File&) = delete;
    File& operator=(const File&) = delete;
    
    // 允许移动
    File(File&& other) : fp(other.fp) { other.fp = nullptr; }
};

// 4. 自定义 scope guard
template<typename F>
class ScopeGuard {
    F func;
    bool active;
public:
    ScopeGuard(F f) : func(move(f)), active(true) {}
    ~ScopeGuard() { if (active) func(); }
    void dismiss() { active = false; }
};

// 使用
void example() {
    void *p = malloc(100);
    auto guard = ScopeGuard([p]{ free(p); });
    
    // 如果这里抛异常，guard 析构会释放 p
    risky_operation();
    
    guard.dismiss();  // 成功后取消自动释放
    return p;
}
```

</details>

---

### 题目 10 ★★★

解释 C++ 虚函数的实现机制。

<details>
<summary>参考答案</summary>

**vtable（虚函数表）实现**：

```cpp
class Base {
public:
    virtual void func1() { }
    virtual void func2() { }
    int data;
};

class Derived : public Base {
public:
    void func1() override { }  // 重写
    virtual void func3() { }   // 新增
};
```

**内存布局**：

**Base 对象**：

| 成员 | 指向 |
|------|------|
| vptr | → Base vtable |
| data | |

**Base vtable**：`&Base::func1`, `&Base::func2`, `&Base::~Base`

**Derived 对象**：

| 成员 | 指向 |
|------|------|
| vptr | → Derived vtable |
| data (从 Base) | |

**Derived vtable**：`&Derived::func1` (重写), `&Base::func2` (继承), `&Derived::~Derived`, `&Derived::func3` (新增)

**调用过程**：

```cpp
Base *p = new Derived();
p->func1();

// 编译器生成的代码：
// 1. 获取 vptr：vptr = p->vptr
// 2. 查表：func_addr = vptr[0]  // func1 在偏移 0
// 3. 调用：call func_addr
```

**汇编示例**：
```asm
; p->func1()
mov rax, [rdi]          ; rax = vptr
mov rax, [rax]          ; rax = vptr[0] = &func1
call rax                ; 调用 func1
```

</details>

---

## 四、编程题

### 题目 11 ★★☆

实现一个简单的 `unique_ptr`。

<details>
<summary>参考答案</summary>

```cpp
#include <utility>
#include <iostream>

template<typename T>
class UniquePtr {
    T *ptr;
    
public:
    // 构造函数
    explicit UniquePtr(T *p = nullptr) : ptr(p) {}
    
    // 析构函数
    ~UniquePtr() {
        delete ptr;
    }
    
    // 禁止拷贝
    UniquePtr(const UniquePtr&) = delete;
    UniquePtr& operator=(const UniquePtr&) = delete;
    
    // 移动构造
    UniquePtr(UniquePtr&& other) noexcept : ptr(other.ptr) {
        other.ptr = nullptr;
    }
    
    // 移动赋值
    UniquePtr& operator=(UniquePtr&& other) noexcept {
        if (this != &other) {
            delete ptr;
            ptr = other.ptr;
            other.ptr = nullptr;
        }
        return *this;
    }
    
    // 解引用
    T& operator*() const { return *ptr; }
    T* operator->() const { return ptr; }
    
    // 获取原始指针
    T* get() const { return ptr; }
    
    // 释放所有权
    T* release() {
        T *tmp = ptr;
        ptr = nullptr;
        return tmp;
    }
    
    // 重置
    void reset(T *p = nullptr) {
        delete ptr;
        ptr = p;
    }
    
    // bool 转换
    explicit operator bool() const { return ptr != nullptr; }
};

// 工厂函数
template<typename T, typename... Args>
UniquePtr<T> makeUnique(Args&&... args) {
    return UniquePtr<T>(new T(std::forward<Args>(args)...));
}

// 测试
int main() {
    auto p1 = makeUnique<int>(42);
    std::cout << *p1 << std::endl;  // 42
    
    auto p2 = std::move(p1);
    std::cout << (p1 ? "p1 valid" : "p1 null") << std::endl;  // p1 null
    std::cout << *p2 << std::endl;  // 42
    
    return 0;
}
```

</details>

---

### 题目 12 ★★★

实现一个简单的 `shared_ptr`。

<details>
<summary>参考答案</summary>

```cpp
#include <atomic>
#include <iostream>

template<typename T>
class SharedPtr {
    T *ptr;
    std::atomic<int> *ref_count;
    
    void release() {
        if (ref_count && --(*ref_count) == 0) {
            delete ptr;
            delete ref_count;
        }
    }
    
public:
    // 构造函数
    explicit SharedPtr(T *p = nullptr) 
        : ptr(p), ref_count(p ? new std::atomic<int>(1) : nullptr) {}
    
    // 拷贝构造
    SharedPtr(const SharedPtr& other) 
        : ptr(other.ptr), ref_count(other.ref_count) {
        if (ref_count) {
            ++(*ref_count);
        }
    }
    
    // 移动构造
    SharedPtr(SharedPtr&& other) noexcept 
        : ptr(other.ptr), ref_count(other.ref_count) {
        other.ptr = nullptr;
        other.ref_count = nullptr;
    }
    
    // 析构函数
    ~SharedPtr() {
        release();
    }
    
    // 拷贝赋值
    SharedPtr& operator=(const SharedPtr& other) {
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
    
    // 移动赋值
    SharedPtr& operator=(SharedPtr&& other) noexcept {
        if (this != &other) {
            release();
            ptr = other.ptr;
            ref_count = other.ref_count;
            other.ptr = nullptr;
            other.ref_count = nullptr;
        }
        return *this;
    }
    
    // 解引用
    T& operator*() const { return *ptr; }
    T* operator->() const { return ptr; }
    
    // 获取原始指针
    T* get() const { return ptr; }
    
    // 引用计数
    int use_count() const {
        return ref_count ? ref_count->load() : 0;
    }
    
    // 重置
    void reset(T *p = nullptr) {
        release();
        ptr = p;
        ref_count = p ? new std::atomic<int>(1) : nullptr;
    }
    
    // bool 转换
    explicit operator bool() const { return ptr != nullptr; }
};

// 工厂函数
template<typename T, typename... Args>
SharedPtr<T> makeShared(Args&&... args) {
    return SharedPtr<T>(new T(std::forward<Args>(args)...));
}

// 测试
int main() {
    auto p1 = makeShared<int>(42);
    std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 1
    
    {
        auto p2 = p1;
        std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 2
    }
    
    std::cout << "p1 use_count: " << p1.use_count() << std::endl;  // 1
    std::cout << *p1 << std::endl;  // 42
    
    return 0;
}
```

</details>

---

### 题目 13 ★★★

实现一个对象池（Object Pool）。

<details>
<summary>参考答案</summary>

```cpp
#include <vector>
#include <memory>
#include <mutex>
#include <iostream>

template<typename T>
class ObjectPool {
    struct Node {
        T object;
        Node *next;
    };
    
    std::vector<std::unique_ptr<Node[]>> blocks;
    Node *free_list;
    std::mutex mutex;
    size_t block_size;
    
    void allocate_block() {
        auto block = std::make_unique<Node[]>(block_size);
        
        // 构建空闲链表
        for (size_t i = 0; i < block_size - 1; i++) {
            block[i].next = &block[i + 1];
        }
        block[block_size - 1].next = free_list;
        free_list = &block[0];
        
        blocks.push_back(std::move(block));
    }
    
public:
    explicit ObjectPool(size_t block_size = 64) 
        : free_list(nullptr), block_size(block_size) {
        allocate_block();
    }
    
    template<typename... Args>
    T* acquire(Args&&... args) {
        std::lock_guard<std::mutex> lock(mutex);
        
        if (!free_list) {
            allocate_block();
        }
        
        Node *node = free_list;
        free_list = node->next;
        
        // 原地构造
        return new (&node->object) T(std::forward<Args>(args)...);
    }
    
    void release(T *obj) {
        if (!obj) return;
        
        // 调用析构函数
        obj->~T();
        
        std::lock_guard<std::mutex> lock(mutex);
        
        // 放回空闲链表
        Node *node = reinterpret_cast<Node*>(
            reinterpret_cast<char*>(obj) - offsetof(Node, object));
        node->next = free_list;
        free_list = node;
    }
    
    // 智能指针返回
    struct Deleter {
        ObjectPool *pool;
        void operator()(T *obj) { pool->release(obj); }
    };
    
    template<typename... Args>
    std::unique_ptr<T, Deleter> acquire_unique(Args&&... args) {
        return std::unique_ptr<T, Deleter>(
            acquire(std::forward<Args>(args)...), 
            Deleter{this});
    }
};

// 测试
struct MyObject {
    int id;
    std::string name;
    
    MyObject(int i, const std::string& n) : id(i), name(n) {
        std::cout << "Construct: " << name << std::endl;
    }
    ~MyObject() {
        std::cout << "Destruct: " << name << std::endl;
    }
};

int main() {
    ObjectPool<MyObject> pool;
    
    auto obj1 = pool.acquire_unique(1, "Object1");
    auto obj2 = pool.acquire_unique(2, "Object2");
    
    std::cout << "obj1: " << obj1->name << std::endl;
    std::cout << "obj2: " << obj2->name << std::endl;
    
    // 自动释放回池
    return 0;
}
```

</details>

---

## 五、Bug 分析题

### 题目 14 ★★☆

以下代码有什么问题？

```cpp
class String {
    char *data;
    size_t length;
public:
    String(const char *s) {
        length = strlen(s);
        data = new char[length + 1];
        strcpy(data, s);
    }
    
    ~String() { delete[] data; }
};

int main() {
    String a("hello");
    String b = a;  // 问题！
}
```

<details>
<summary>查看答案与解析</summary>

**问题**：缺少拷贝构造函数，导致浅拷贝。

```
执行 String b = a 时：
a.data ──→ "hello"
b.data ──→ "hello"（同一块内存）

析构时：
~String() for b: delete[] data  ← 释放
~String() for a: delete[] data  ← 双重释放！
```

**修复**：

```cpp
class String {
    char *data;
    size_t length;
public:
    String(const char *s) {
        length = strlen(s);
        data = new char[length + 1];
        strcpy(data, s);
    }
    
    // 拷贝构造函数
    String(const String& other) {
        length = other.length;
        data = new char[length + 1];
        strcpy(data, other.data);
    }
    
    // 拷贝赋值运算符
    String& operator=(const String& other) {
        if (this != &other) {
            delete[] data;
            length = other.length;
            data = new char[length + 1];
            strcpy(data, other.data);
        }
        return *this;
    }
    
    // 移动构造函数
    String(String&& other) noexcept 
        : data(other.data), length(other.length) {
        other.data = nullptr;
        other.length = 0;
    }
    
    // 移动赋值运算符
    String& operator=(String&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = other.data;
            length = other.length;
            other.data = nullptr;
            other.length = 0;
        }
        return *this;
    }
    
    ~String() { delete[] data; }
};
```

**Rule of Three/Five/Zero**：
- 如果定义了析构函数、拷贝构造、拷贝赋值中的任一个
- 通常需要定义全部三个（Rule of Three）
- C++11 后加上移动语义（Rule of Five）
- 或者全部使用默认（Rule of Zero）

</details>

---

### 题目 15 ★★★

以下代码有什么问题？

```cpp
#include <memory>
#include <vector>

class Node : public std::enable_shared_from_this<Node> {
public:
    std::shared_ptr<Node> parent;
    std::vector<std::shared_ptr<Node>> children;
    
    void addChild(std::shared_ptr<Node> child) {
        children.push_back(child);
        child->parent = shared_from_this();
    }
};

int main() {
    auto root = std::make_shared<Node>();
    auto child = std::make_shared<Node>();
    root->addChild(child);
}  // 内存泄漏！
```

<details>
<summary>查看答案与解析</summary>

**问题**：循环引用导致内存泄漏。

```
引用关系：
root ←── shared_ptr (1个)
  ↓
children[0] ──→ child
  ↑
  └──── parent ──┘

引用计数：
root: 1（来自 main 的 shared_ptr）
child: 2（来自 main 的 shared_ptr + root->children[0]）

main 结束时：
root 引用计数 -1 = 1（child->parent 还在引用）
child 引用计数 -1 = 1（root->children[0] 还在引用）

两个都不会被释放！
```

**修复**：使用 weak_ptr 打破循环。

```cpp
class Node : public std::enable_shared_from_this<Node> {
public:
    std::weak_ptr<Node> parent;  // 改为 weak_ptr
    std::vector<std::shared_ptr<Node>> children;
    
    void addChild(std::shared_ptr<Node> child) {
        children.push_back(child);
        child->parent = shared_from_this();
    }
    
    std::shared_ptr<Node> getParent() {
        return parent.lock();  // 尝试获取 shared_ptr
    }
};
```

</details>

---

## 六、高频考点总结

| 考点 | 频率 | 难度 | 关键知识 |
|------|------|------|----------|
| 虚函数机制 | ★★★ | ★★☆ | vptr、vtable、动态绑定 |
| 内存对齐 | ★★★ | ★★☆ | 成员排列、sizeof |
| 智能指针 | ★★★ | ★★☆ | unique_ptr、shared_ptr |
| RAII | ★★★ | ★★☆ | 资源管理、异常安全 |
| Rule of Three/Five | ★★☆ | ★★☆ | 拷贝控制成员 |
| 多重继承 | ★★☆ | ★★★ | 菱形继承、虚继承 |
| 构造函数虚调用 | ★★☆ | ★★☆ | 不会发生多态 |

---

## 相关文章

- [上一篇：C++面试题-性能优化](/articles/cpp/cpp-39-C++面试题-性能优化/)
- [下一篇：C++笔试题-并发编程](/articles/cpp/cpp-41-C++笔试题-并发编程/)
