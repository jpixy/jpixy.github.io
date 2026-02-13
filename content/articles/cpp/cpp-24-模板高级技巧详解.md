+++
title = "24. Advanced Template Techniques"
date = 2026-01-21
weight = 24000
description = "深入剖析C++模板高级技术，包括变参模板、模板特化、CRTP深入、Expression Templates、Tag Dispatch等核心技术"
[taxonomies]
tags = ["C++", "模板", "泛型编程", "元编程", "HFT"]
+++

## 概述

模板是C++最强大的特性之一，掌握高级模板技术对于编写高性能泛型代码至关重要。本文深入剖析模板的高级用法。

---

## 一、变参模板（Variadic Templates）

### 1.1 基本语法

```cpp
// 变参模板：接受任意数量的模板参数
template<typename... Args>
void print(Args... args) {
    // sizeof...(Args) 获取参数包中的参数数量
    // sizeof...(args) 同样可用
    std::cout << "参数数量: " << sizeof...(Args) << std::endl;
}

print(1, 2.0, "hello");  // 参数数量: 3
```

### 1.2 参数包展开

```cpp
// C++11: 递归展开
template<typename T>
void printImpl(T arg) {
    std::cout << arg << std::endl;
}

template<typename T, typename... Rest>
void printImpl(T first, Rest... rest) {
    std::cout << first << ", ";
    printImpl(rest...);  // 递归调用
}

// C++17: 折叠表达式
template<typename... Args>
void printFold(Args... args) {
    ((std::cout << args << " "), ...);  // 一元右折叠
    std::cout << std::endl;
}

// 折叠表达式类型：
// (pack op ...)     一元右折叠: (E1 op (E2 op (E3 op ...)))
// (... op pack)     一元左折叠: ((E1 op E2) op E3) op ...
// (pack op ... op init)  二元右折叠
// (init op ... op pack)  二元左折叠
```

### 1.3 完美转发变参

```cpp
// 结合完美转发
template<typename T, typename... Args>
std::unique_ptr<T> make_unique_impl(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

// emplace_back实现
template<typename... Args>
void emplace_back(Args&&... args) {
    // 在末尾位置直接构造对象
    new (end_ptr) T(std::forward<Args>(args)...);
    ++size_;
}
```

### 1.4 索引序列

```cpp
// std::index_sequence用于编译期索引
template<typename Tuple, size_t... Is>
void printTupleImpl(const Tuple& t, std::index_sequence<Is...>) {
    ((std::cout << (Is == 0 ? "" : ", ") << std::get<Is>(t)), ...);
}

template<typename... Args>
void printTuple(const std::tuple<Args...>& t) {
    printTupleImpl(t, std::make_index_sequence<sizeof...(Args)>{});
}

// 使用
auto t = std::make_tuple(1, "hello", 3.14);
printTuple(t);  // 输出: 1, hello, 3.14
```

---

## 二、模板特化

### 2.1 全特化

```cpp
// 主模板
template<typename T>
struct Serializer {
    static std::string serialize(const T& obj) {
        return obj.toString();  // 默认实现
    }
};

// 全特化：针对int
template<>
struct Serializer<int> {
    static std::string serialize(int value) {
        return std::to_string(value);
    }
};

// 全特化：针对std::string
template<>
struct Serializer<std::string> {
    static std::string serialize(const std::string& s) {
        return "\"" + s + "\"";
    }
};
```

### 2.2 偏特化

```cpp
// 主模板
template<typename T, typename Allocator = std::allocator<T>>
class Vector {
    // 通用实现
};

// 偏特化：针对指针类型
template<typename T, typename Allocator>
class Vector<T*, Allocator> {
    // 指针特化实现
};

// 偏特化：针对特定分配器
template<typename T>
class Vector<T, ArenaAllocator<T>> {
    // Arena分配器特化实现
};

// 偏特化：针对bool（位压缩）
template<typename Allocator>
class Vector<bool, Allocator> {
    // std::vector<bool>类似的位压缩实现
};
```

### 2.3 函数模板特化（不推荐）

```cpp
// 主模板
template<typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

// 函数模板全特化（不推荐）
template<>
const char* max(const char* a, const char* b) {
    return std::strcmp(a, b) > 0 ? a : b;
}

// 推荐：使用重载代替
const char* max(const char* a, const char* b) {
    return std::strcmp(a, b) > 0 ? a : b;
}

// 原因：函数模板特化不参与重载决议
// 可能导致意外的行为
```

---

## 三、CRTP深入

### 3.1 静态多态

```cpp
// CRTP基类
template<typename Derived>
class Comparable {
public:
    bool operator!=(const Derived& other) const {
        return !static_cast<const Derived*>(this)->operator==(other);
    }
    
    bool operator>(const Derived& other) const {
        return other < static_cast<const Derived&>(*this);
    }
    
    bool operator<=(const Derived& other) const {
        return !(static_cast<const Derived&>(*this) > other);
    }
    
    bool operator>=(const Derived& other) const {
        return !(*this < other);
    }
};

// 派生类只需实现==和<
class Point : public Comparable<Point> {
    int x, y;
public:
    bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }
    
    bool operator<(const Point& other) const {
        return x < other.x || (x == other.x && y < other.y);
    }
};
```

### 3.2 静态接口强制

```cpp
// 强制派生类实现特定接口
template<typename Derived>
class MessageHandler {
public:
    void handle(const Message& msg) {
        // 调用派生类的实现
        static_cast<Derived*>(this)->handleImpl(msg);
    }
    
    // C++20: 使用requires子句约束
    // 注意：在基类模板中直接static_assert会失败
    // 因为Derived在此时可能还不完整
};

// 使用Concepts约束派生类（C++20）
template<typename T>
concept HasHandleImpl = requires(T t, const Message& m) {
    t.handleImpl(m);
};

template<HasHandleImpl Derived>
class MessageHandlerChecked : public MessageHandler<Derived> {
    // 只有实现了handleImpl的类才能继承
};

class MyHandler : public MessageHandler<MyHandler> {
public:
    void handleImpl(const Message& msg) {
        // 实现
    }
};
```

### 3.3 对象计数器

```cpp
template<typename T>
class ObjectCounter {
    static inline std::atomic<size_t> count_{0};
    
protected:
    ObjectCounter() { ++count_; }
    ObjectCounter(const ObjectCounter&) { ++count_; }
    ~ObjectCounter() { --count_; }
    
public:
    static size_t getCount() { return count_; }
};

class Widget : public ObjectCounter<Widget> {
    // Widget特定的计数器
};

class Gadget : public ObjectCounter<Gadget> {
    // Gadget特定的计数器（独立于Widget）
};

// 使用
Widget w1, w2, w3;
Gadget g1, g2;

std::cout << Widget::getCount() << std::endl;  // 3
std::cout << Gadget::getCount() << std::endl;  // 2
```

---

## 四、Expression Templates

### 4.1 问题背景

```cpp
// 传统向量加法：产生临时对象
Vector operator+(const Vector& a, const Vector& b) {
    Vector result(a.size());
    for (size_t i = 0; i < a.size(); ++i) {
        result[i] = a[i] + b[i];
    }
    return result;
}

// 连续运算产生多个临时对象
Vector d = a + b + c;
// 等价于：
// Vector temp1 = a + b;
// Vector temp2 = temp1 + c;
// Vector d = temp2;
// 3次内存分配，3次完整遍历！
```

### 4.2 Expression Templates解决方案

```cpp
// 表达式模板：延迟求值
template<typename E>
class VecExpression {
public:
    double operator[](size_t i) const {
        return static_cast<const E&>(*this)[i];
    }
    
    size_t size() const {
        return static_cast<const E&>(*this).size();
    }
};

// 实际的向量类
class Vec : public VecExpression<Vec> {
    std::vector<double> data_;
public:
    Vec(size_t n) : data_(n) {}
    
    // 从表达式构造
    template<typename E>
    Vec(const VecExpression<E>& expr) : data_(expr.size()) {
        for (size_t i = 0; i < expr.size(); ++i) {
            data_[i] = expr[i];  // 一次遍历完成所有计算
        }
    }
    
    double operator[](size_t i) const { return data_[i]; }
    double& operator[](size_t i) { return data_[i]; }
    size_t size() const { return data_.size(); }
};

// 加法表达式
template<typename E1, typename E2>
class VecSum : public VecExpression<VecSum<E1, E2>> {
    const E1& u_;
    const E2& v_;
public:
    VecSum(const E1& u, const E2& v) : u_(u), v_(v) {}
    
    double operator[](size_t i) const {
        return u_[i] + v_[i];  // 延迟计算
    }
    
    size_t size() const { return u_.size(); }
};

// 运算符重载
template<typename E1, typename E2>
VecSum<E1, E2> operator+(const VecExpression<E1>& u, 
                          const VecExpression<E2>& v) {
    return VecSum<E1, E2>(static_cast<const E1&>(u), 
                          static_cast<const E2&>(v));
}

// 使用
Vec a(1000), b(1000), c(1000);
Vec d = a + b + c;  // 只有一次内存分配，一次遍历！
```

---

## 五、Tag Dispatch

### 5.1 基本模式

```cpp
// 使用类型标签进行函数分发
struct RandomAccessTag {};
struct ForwardTag {};
struct InputTag {};

// 针对不同迭代器类别的实现
template<typename Iter>
void advanceImpl(Iter& it, int n, RandomAccessTag) {
    it += n;  // O(1)
}

template<typename Iter>
void advanceImpl(Iter& it, int n, ForwardTag) {
    for (int i = 0; i < n; ++i) ++it;  // O(n)
}

// 主函数：根据迭代器类别分发
template<typename Iter>
void advance(Iter& it, int n) {
    using Category = typename std::iterator_traits<Iter>::iterator_category;
    
    if constexpr (std::is_same_v<Category, std::random_access_iterator_tag>) {
        advanceImpl(it, n, RandomAccessTag{});
    } else {
        advanceImpl(it, n, ForwardTag{});
    }
}
```

### 5.2 HFT应用：消息处理

```cpp
// 消息类型标签
struct MarketDataTag {};
struct OrderTag {};
struct TradeTag {};

template<typename MsgType>
struct MessageTraits;

template<>
struct MessageTraits<MarketData> {
    using Tag = MarketDataTag;
};

template<>
struct MessageTraits<Order> {
    using Tag = OrderTag;
};

// 处理函数
template<typename Msg>
void processImpl(const Msg& msg, MarketDataTag) {
    updateOrderBook(msg);
}

template<typename Msg>
void processImpl(const Msg& msg, OrderTag) {
    validateAndSend(msg);
}

template<typename Msg>
void process(const Msg& msg) {
    using Tag = typename MessageTraits<Msg>::Tag;
    processImpl(msg, Tag{});  // 编译期分发
}
```

---

## 六、其他高级技巧

### 6.1 模板模板参数

```cpp
// 接受模板作为参数
template<typename T, template<typename> class Container>
class Stack {
    Container<T> data_;
public:
    void push(const T& value) { data_.push_back(value); }
    T pop() {
        T top = data_.back();
        data_.pop_back();
        return top;
    }
};

// 使用不同容器实现
Stack<int, std::vector> vectorStack;
Stack<int, std::deque> dequeStack;
```

### 6.2 类型擦除模板

```cpp
// 简单的Any实现
class Any {
    struct Concept {
        virtual ~Concept() = default;
        virtual std::unique_ptr<Concept> clone() const = 0;
    };
    
    template<typename T>
    struct Model : Concept {
        T data;
        Model(T d) : data(std::move(d)) {}
        std::unique_ptr<Concept> clone() const override {
            return std::make_unique<Model>(*this);
        }
    };
    
    std::unique_ptr<Concept> ptr_;
    
public:
    template<typename T>
    Any(T value) : ptr_(std::make_unique<Model<T>>(std::move(value))) {}
    
    template<typename T>
    T& get() {
        return dynamic_cast<Model<T>&>(*ptr_).data;
    }
};
```

### 6.3 检测惯用法（Detection Idiom）

```cpp
// C++17: std::void_t实现检测
template<typename, typename = void>
struct has_serialize : std::false_type {};

template<typename T>
struct has_serialize<T, std::void_t<decltype(std::declval<T>().serialize())>> 
    : std::true_type {};

// 使用
template<typename T>
void save(const T& obj) {
    if constexpr (has_serialize<T>::value) {
        obj.serialize();
    } else {
        defaultSerialize(obj);
    }
}
```

---

## 总结

| 技术 | 用途 | HFT应用 |
|------|------|---------|
| 变参模板 | 可变参数泛型 | 日志、工厂函数 |
| 模板特化 | 类型特定优化 | 消息解析 |
| CRTP | 静态多态 | 策略模式 |
| Expression Templates | 消除临时对象 | 向量/矩阵计算 |
| Tag Dispatch | 编译期分发 | 消息路由 |

**最佳实践**：
1. 优先使用模板而非虚函数（HFT热路径）
2. Expression Templates消除临时对象
3. CRTP实现零成本抽象
4. 使用if constexpr简化条件编译

---

## 相关文章

- [上一篇：Compiler Optimization and Profiling (HFT)](@/articles/cpp/cpp-23-HFT编译器优化与Profile.md)
- [下一篇：C++20/23 New Features](@/articles/cpp/cpp-25-C++20-23新特性详解.md)
