+++
title = "14. Copy and Move Semantics"
slug = "cpp-14-深浅拷贝与移动语义详解"
date = 2026-01-21
description = "深入剖析C++拷贝语义与移动语义的底层机制，包括拷贝构造、移动构造、RVO/NRVO、完美转发等核心概念，HFT系统性能优化必备知识"
[taxonomies]
tags = ["C++", "移动语义", "性能优化", "HFT", "面试"]
+++

## 概述

在C++中，对象的拷贝和移动是最基础也是最容易出错的领域之一。理解深浅拷贝的区别、移动语义的原理，对于编写高性能代码至关重要，尤其在HFT（高频交易）系统中，不必要的拷贝可能导致微秒级的延迟增加。

---

## 一、浅拷贝与深拷贝

### 1.1 浅拷贝（Shallow Copy）

浅拷贝只复制对象的成员变量的值，对于指针成员，只复制指针的值（地址），而不复制指针指向的内容。

```cpp
class ShallowCopy {
public:
    int* data;
    size_t size;
    
    ShallowCopy(size_t n) : size(n) {
        data = new int[n];
    }
    
    // 编译器生成的默认拷贝构造函数执行浅拷贝
    // ShallowCopy(const ShallowCopy& other) 
    //     : data(other.data), size(other.size) {}
    
    ~ShallowCopy() {
        delete[] data;  // 问题：两个对象会delete同一块内存！
    }
};

void problem() {
    ShallowCopy a(100);
    ShallowCopy b = a;  // 浅拷贝：b.data == a.data
    // 析构时：a和b都会delete同一块内存 → 未定义行为
}
```

**浅拷贝的问题**：
1. **Double Free**：多个对象析构时释放同一块内存
2. **悬垂指针**：一个对象释放后，其他对象的指针指向无效内存
3. **数据不一致**：一个对象修改数据，影响所有共享该内存的对象

### 1.2 深拷贝（Deep Copy）

深拷贝会复制指针指向的完整内容，每个对象拥有独立的资源。

```cpp
class DeepCopy {
public:
    int* data;
    size_t size;
    
    DeepCopy(size_t n) : size(n) {
        data = new int[n];
    }
    
    // 深拷贝构造函数
    DeepCopy(const DeepCopy& other) : size(other.size) {
        data = new int[size];                    // 分配新内存
        std::memcpy(data, other.data, size * sizeof(int));  // 复制内容
    }
    
    // 深拷贝赋值运算符
    DeepCopy& operator=(const DeepCopy& other) {
        if (this != &other) {  // 自赋值检查
            delete[] data;     // 释放旧资源
            size = other.size;
            data = new int[size];
            std::memcpy(data, other.data, size * sizeof(int));
        }
        return *this;
    }
    
    ~DeepCopy() {
        delete[] data;
    }
};
```

### 1.3 深拷贝的性能问题

深拷贝解决了资源管理问题，但引入了性能开销：

```cpp
std::vector<int> createLargeVector() {
    std::vector<int> v(1000000);  // 分配100万个int
    // ... 填充数据
    return v;  // 返回时如果发生深拷贝，需要复制400万字节！
}

void processData() {
    std::vector<int> data = createLargeVector();  // 拷贝开销
}
```

**在HFT系统中**，这种不必要的拷贝可能导致：
- 内存分配延迟（malloc可能需要系统调用）
- 缓存污染（大量数据复制占用cache）
- CPU时间浪费

---

## 二、移动语义（Move Semantics）

### 2.1 右值引用（Rvalue Reference）

C++11引入右值引用`T&&`，用于识别临时对象（即将销毁的对象）。

```cpp
// 左值（lvalue）：有名字、有地址、可以取地址
int x = 10;        // x是左值
int* p = &x;       // 可以取x的地址

// 右值（rvalue）：临时对象、字面量、表达式结果
int y = x + 5;     // (x + 5)是右值
int z = 42;        // 42是右值

// 右值引用
int&& rref = 10;           // OK：绑定到右值
int&& rref2 = x;           // 错误：不能绑定到左值
int&& rref3 = std::move(x); // OK：std::move将左值转为右值
```

### 2.2 std::move的本质

`std::move`不移动任何东西，它只是一个类型转换，将左值转换为右值引用。

```cpp
// std::move的简化实现
template<typename T>
typename std::remove_reference<T>::type&& move(T&& arg) noexcept {
    return static_cast<typename std::remove_reference<T>::type&&>(arg);
}

// 使用示例
std::string s1 = "Hello";
std::string s2 = std::move(s1);  // s1被转换为右值引用
// 此时s1处于"有效但未指定"状态，通常为空
```

**关键理解**：
- `std::move`只是cast，不执行任何移动
- 实际的移动发生在移动构造函数或移动赋值运算符中
- 移动后的对象处于"有效但未指定"状态

### 2.3 移动构造函数与移动赋值运算符

```cpp
class Buffer {
private:
    char* data_;
    size_t size_;
    
public:
    // 普通构造函数
    explicit Buffer(size_t size) : size_(size), data_(new char[size]) {}
    
    // 拷贝构造函数（深拷贝）
    Buffer(const Buffer& other) : size_(other.size_), data_(new char[other.size_]) {
        std::memcpy(data_, other.data_, size_);
    }
    
    // 移动构造函数
    Buffer(Buffer&& other) noexcept 
        : data_(other.data_), size_(other.size_) {
        // 窃取资源
        other.data_ = nullptr;
        other.size_ = 0;
    }
    
    // 拷贝赋值运算符
    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            delete[] data_;
            size_ = other.size_;
            data_ = new char[size_];
            std::memcpy(data_, other.data_, size_);
        }
        return *this;
    }
    
    // 移动赋值运算符
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;      // 释放自己的资源
            data_ = other.data_; // 窃取对方资源
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }
    
    ~Buffer() {
        delete[] data_;
    }
};
```

### 2.4 移动语义的性能优势

```cpp
// 对比测试
void benchmark() {
    Buffer large(100 * 1024 * 1024);  // 100MB
    
    // 拷贝：需要分配内存 + 复制100MB数据
    auto start1 = std::chrono::high_resolution_clock::now();
    Buffer copy = large;  // 拷贝构造
    auto end1 = std::chrono::high_resolution_clock::now();
    
    // 移动：只需要复制几个指针/整数
    auto start2 = std::chrono::high_resolution_clock::now();
    Buffer moved = std::move(large);  // 移动构造
    auto end2 = std::chrono::high_resolution_clock::now();
    
    // 拷贝：~50ms（取决于内存带宽）
    // 移动：~10ns（几乎可以忽略）
}
```

---

## 三、Rule of Zero/Three/Five

### 3.1 Rule of Three（C++98）

如果类需要自定义以下任意一个，通常需要自定义全部三个：
1. 析构函数
2. 拷贝构造函数
3. 拷贝赋值运算符

### 3.2 Rule of Five（C++11）

C++11后扩展为五个：
1. 析构函数
2. 拷贝构造函数
3. 拷贝赋值运算符
4. **移动构造函数**
5. **移动赋值运算符**

```cpp
class ResourceOwner {
public:
    ResourceOwner();                                      // 默认构造
    ~ResourceOwner();                                     // 1. 析构
    ResourceOwner(const ResourceOwner&);                  // 2. 拷贝构造
    ResourceOwner& operator=(const ResourceOwner&);       // 3. 拷贝赋值
    ResourceOwner(ResourceOwner&&) noexcept;              // 4. 移动构造
    ResourceOwner& operator=(ResourceOwner&&) noexcept;   // 5. 移动赋值
};
```

### 3.3 Rule of Zero（推荐）

最佳实践：让类不需要自定义任何特殊成员函数，通过组合使用RAII类型来管理资源。

```cpp
// 不推荐：手动管理资源
class BadDesign {
    int* data;
    // 需要实现析构、拷贝、移动...
};

// 推荐：使用智能指针
class GoodDesign {
    std::unique_ptr<int[]> data;
    // 编译器自动生成正确的特殊成员函数
};

// 推荐：使用标准容器
class BetterDesign {
    std::vector<int> data;
    // 完全不需要自定义特殊成员函数
};
```

---

## 四、RVO与NRVO（返回值优化）

### 4.1 返回值优化（RVO）

编译器可以省略临时对象的拷贝/移动，直接在调用者的内存位置构造对象。

```cpp
std::string createString() {
    return std::string("Hello, World!");  // RVO：直接在调用者位置构造
}

void caller() {
    std::string s = createString();
    // 理想情况：没有任何拷贝或移动发生
    // 字符串直接在s的位置构造
}
```

### 4.2 具名返回值优化（NRVO）

对于具名的局部变量，编译器也可能进行优化。

```cpp
std::vector<int> createVector() {
    std::vector<int> result;  // 具名变量
    result.reserve(1000);
    for (int i = 0; i < 1000; ++i) {
        result.push_back(i);
    }
    return result;  // NRVO：可能省略拷贝/移动
}
```

### 4.3 何时RVO/NRVO失效

```cpp
std::string getString(bool condition) {
    std::string a = "Hello";
    std::string b = "World";
    
    if (condition) {
        return a;  // NRVO可能失效：多个可能的返回值
    } else {
        return b;
    }
}

std::string getString2(std::string s) {
    return s;  // 返回参数：RVO不适用
}
```

### 4.4 C++17强制RVO（Copy Elision）

C++17规定在某些情况下RVO是**强制的**（不是优化）：

```cpp
// C++17起，这里保证没有拷贝/移动
std::string s = std::string("Hello");  // 只有一次构造

// 即使删除拷贝/移动构造函数也能编译
class NonCopyable {
public:
    NonCopyable() = default;
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable(NonCopyable&&) = delete;
};

NonCopyable create() {
    return NonCopyable{};  // C++17起合法
}

NonCopyable obj = create();  // C++17起合法
```

---

## 五、完美转发（Perfect Forwarding）

### 5.1 问题背景

如何编写一个包装函数，将参数原封不动地转发给另一个函数？

```cpp
template<typename T>
void wrapper(T arg) {
    target(arg);  // 问题：总是传左值，即使调用wrapper时传入右值
}

template<typename T>
void wrapper2(T& arg) {
    target(arg);  // 问题：不能接受右值
}

template<typename T>
void wrapper3(const T& arg) {
    target(arg);  // 问题：丢失可修改性，总是传const左值
}
```

### 5.2 万能引用（Universal Reference）

```cpp
template<typename T>
void wrapper(T&& arg) {  // T&&在模板中是万能引用
    // 如果传入左值，T被推导为T&，arg类型为T& &&折叠为T&
    // 如果传入右值，T被推导为T，arg类型为T&&
}
```

**引用折叠规则**：
- `T& &` → `T&`
- `T& &&` → `T&`
- `T&& &` → `T&`
- `T&& &&` → `T&&`

### 5.3 std::forward

```cpp
template<typename T>
void wrapper(T&& arg) {
    target(std::forward<T>(arg));  // 完美转发
    // 如果arg是左值引用，转发为左值
    // 如果arg是右值引用，转发为右值
}

// std::forward的简化实现
template<typename T>
T&& forward(typename std::remove_reference<T>::type& arg) noexcept {
    return static_cast<T&&>(arg);
}
```

### 5.4 实际应用：emplace系列函数

```cpp
template<typename... Args>
void Vector::emplace_back(Args&&... args) {
    // 在容器内部直接构造对象，避免临时对象
    new (end_ptr) T(std::forward<Args>(args)...);
}

// 使用示例
std::vector<std::string> v;
v.emplace_back("Hello");  // 直接用const char*构造string，无临时对象
v.push_back("Hello");     // 先构造临时string，再移动到容器

std::vector<std::pair<int, std::string>> pairs;
pairs.emplace_back(1, "one");  // 直接构造pair
pairs.push_back({1, "one"});   // 先构造临时pair
```

---

## 六、HFT中的移动语义最佳实践

### 6.1 避免不必要的拷贝

```cpp
// HFT订单簿更新
class OrderBook {
    std::map<Price, Level> levels_;
    
public:
    // 不好：按值返回可能导致拷贝
    std::vector<Order> getOrders(Price price) {
        return levels_[price].orders;
    }
    
    // 好：返回引用避免拷贝
    const std::vector<Order>& getOrdersRef(Price price) const {
        static const std::vector<Order> empty;
        auto it = levels_.find(price);
        return it != levels_.end() ? it->second.orders : empty;
    }
    
    // 好：使用span（C++20）表示视图
    std::span<const Order> getOrdersView(Price price) const;
};
```

### 6.2 noexcept的重要性

```cpp
class HFTBuffer {
public:
    // 移动构造必须标记noexcept
    // 否则std::vector等容器会选择拷贝而非移动
    HFTBuffer(HFTBuffer&& other) noexcept 
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }
};

// 验证：vector重新分配时是否使用移动
std::vector<HFTBuffer> buffers;
buffers.reserve(10);
for (int i = 0; i < 20; ++i) {
    buffers.emplace_back(1024);  // 超过容量时重新分配
    // 如果移动构造是noexcept，使用移动
    // 否则使用拷贝（为了异常安全）
}
```

### 6.3 对象池与移动语义

```cpp
// HFT系统中常用对象池避免动态分配
template<typename T>
class ObjectPool {
    std::vector<T> pool_;
    std::vector<T*> free_list_;
    
public:
    T* acquire() {
        if (free_list_.empty()) {
            pool_.emplace_back();
            return &pool_.back();
        }
        T* obj = free_list_.back();
        free_list_.pop_back();
        return obj;
    }
    
    void release(T* obj) {
        // 重置对象状态而非销毁
        *obj = T{};  // 使用移动赋值
        free_list_.push_back(obj);
    }
};
```

### 6.4 消息传递中的移动语义

```cpp
// HFT系统中的消息队列
class Message {
    std::unique_ptr<char[]> payload_;
    size_t size_;
    
public:
    // 消息应该移动而非拷贝
    Message(Message&&) noexcept = default;
    Message& operator=(Message&&) noexcept = default;
    
    // 禁止拷贝
    Message(const Message&) = delete;
    Message& operator=(const Message&) = delete;
};

// 无锁队列使用移动语义
template<typename T>
class SPSCQueue {
public:
    bool push(T&& item) {
        // 移动语义避免拷贝
        buffer_[write_pos_] = std::move(item);
        // ...
    }
    
    bool pop(T& item) {
        item = std::move(buffer_[read_pos_]);
        // ...
    }
};
```

---

## 七、常见陷阱与面试题

### 7.1 移动后使用（Use After Move）

```cpp
std::string s = "Hello";
std::string s2 = std::move(s);
std::cout << s << std::endl;  // 不是UB，但输出不确定

// 重要澄清：移动后使用不是未定义行为
// s处于"有效但未指定"（valid but unspecified）状态
// 可以安全调用不依赖内部状态的操作（如clear()、empty()）
// 对于std::string，移动后通常是空字符串
// 但不应该依赖具体值，应该重新赋值后再使用

// 正确的做法
s = "New value";  // 重新赋值
std::cout << s << std::endl;  // 现在安全
```

### 7.2 const对象不能移动

```cpp
const std::string s = "Hello";
std::string s2 = std::move(s);  // 实际执行拷贝！

// std::move(s)返回const std::string&&
// 匹配拷贝构造函数（const std::string&）而非移动构造函数
```

### 7.3 成员变量的移动

```cpp
class Wrapper {
    std::string name_;
    
public:
    // 移动构造函数中，成员变量仍是左值！
    Wrapper(Wrapper&& other) 
        : name_(other.name_) {}  // 错误：执行拷贝
    
    Wrapper(Wrapper&& other) 
        : name_(std::move(other.name_)) {}  // 正确：执行移动
};
```

### 7.4 面试题：实现一个支持移动语义的String类

```cpp
class String {
private:
    char* data_;
    size_t size_;
    size_t capacity_;
    
public:
    // 默认构造
    String() : data_(nullptr), size_(0), capacity_(0) {}
    
    // 从C字符串构造
    explicit String(const char* s) {
        size_ = std::strlen(s);
        capacity_ = size_ + 1;
        data_ = new char[capacity_];
        std::memcpy(data_, s, capacity_);
    }
    
    // 拷贝构造
    String(const String& other) 
        : size_(other.size_), capacity_(other.capacity_) {
        data_ = new char[capacity_];
        std::memcpy(data_, other.data_, size_ + 1);
    }
    
    // 移动构造
    String(String&& other) noexcept
        : data_(other.data_), size_(other.size_), capacity_(other.capacity_) {
        other.data_ = nullptr;
        other.size_ = 0;
        other.capacity_ = 0;
    }
    
    // 统一赋值运算符（Copy-and-Swap idiom）
    String& operator=(String other) noexcept {
        swap(*this, other);
        return *this;
    }
    
    // swap函数
    friend void swap(String& a, String& b) noexcept {
        using std::swap;
        swap(a.data_, b.data_);
        swap(a.size_, b.size_);
        swap(a.capacity_, b.capacity_);
    }
    
    // 析构
    ~String() {
        delete[] data_;
    }
};
```

---

## 总结

| 概念 | 说明 | HFT重要性 |
|------|------|-----------|
| 浅拷贝 | 只复制指针值，共享资源 | 危险，避免使用 |
| 深拷贝 | 复制完整资源 | 安全但有性能开销 |
| 移动语义 | 转移资源所有权 | **关键优化手段** |
| RVO/NRVO | 编译器省略拷贝 | 依赖但不可控 |
| 完美转发 | 保持值类别转发 | 泛型代码必备 |
| noexcept | 保证不抛异常 | **移动必须标记** |
| Rule of Zero | 避免手动资源管理 | 最佳实践 |

在HFT系统中，移动语义是减少延迟的关键技术之一。正确使用移动语义可以：
- 避免内存分配（malloc延迟不可预测）
- 减少数据复制（节省CPU和带宽）
- 降低缓存污染（保持热数据在cache中）
