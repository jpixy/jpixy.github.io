+++
title = "13. Type Traits and SFINAE"
slug = "cpp-18-类型萃取与SFINAE详解"
date = 2026-01-21
description = "深入剖析C++类型萃取、SFINAE、std::enable_if、Concepts等模板元编程核心技术"
[taxonomies]
tags = ["C++", "模板", "SFINAE", "类型萃取", "Concepts", "泛型编程"]
+++

## 概述

类型萃取和SFINAE是C++模板元编程的核心技术，用于在编译期进行类型检测和条件编译。C++20的Concepts进一步简化了这些技术的使用。

---

## 一、类型萃取（Type Traits）

### 1.1 基本类型检测

```cpp
#include <type_traits>

// 检测是否是整数类型
static_assert(std::is_integral_v<int>);
static_assert(!std::is_integral_v<double>);

// 检测是否是指针
static_assert(std::is_pointer_v<int*>);
static_assert(!std::is_pointer_v<int>);

// 检测是否是类
static_assert(std::is_class_v<std::string>);
static_assert(!std::is_class_v<int>);
```

### 1.2 类型修改

```cpp
// 移除const/volatile
using T1 = std::remove_const_t<const int>;  // int
using T2 = std::remove_cv_t<const volatile int>;  // int

// 移除引用
using T3 = std::remove_reference_t<int&>;  // int
using T4 = std::remove_reference_t<int&&>;  // int

// 添加指针
using T5 = std::add_pointer_t<int>;  // int*

// 衰减（模拟按值传递）
using T6 = std::decay_t<int[10]>;  // int*
using T7 = std::decay_t<int(int)>;  // int(*)(int)
```

### 1.3 自定义类型萃取

```cpp
// 检测是否有size()方法
template<typename T, typename = void>
struct has_size : std::false_type {};

template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> 
    : std::true_type {};

template<typename T>
constexpr bool has_size_v = has_size<T>::value;

static_assert(has_size_v<std::vector<int>>);
static_assert(!has_size_v<int>);
```

---

## 二、SFINAE

### 2.1 基本概念

SFINAE = Substitution Failure Is Not An Error（替换失败不是错误）

```cpp
// 当模板参数替换失败时，不产生编译错误，而是从重载集中移除该模板

template<typename T>
typename T::value_type get_value(const T& container) {
    return container.front();
}

// 对于没有value_type的类型，上面的模板会被SFINAE排除
// int x = get_value(42);  // 编译错误（没有其他可用重载）
```

### 2.2 std::enable_if

```cpp
// std::enable_if：条件满足时启用模板
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
double_value(T x) {
    return x * 2;
}

template<typename T>
std::enable_if_t<std::is_floating_point_v<T>, T>
double_value(T x) {
    return x * 2.0;
}

// 使用
auto a = double_value(5);    // 调用整数版本
auto b = double_value(3.14); // 调用浮点版本
```

### 2.3 SFINAE实战

```cpp
// 检测类型是否可以输出到ostream
template<typename T, typename = void>
struct is_printable : std::false_type {};

template<typename T>
struct is_printable<T, 
    std::void_t<decltype(std::declval<std::ostream&>() << std::declval<T>())>>
    : std::true_type {};

// 只对可打印类型启用
template<typename T>
std::enable_if_t<is_printable<T>::value>
print(const T& value) {
    std::cout << value << "\n";
}
```

---

## 三、C++17改进

### 3.1 if constexpr替代SFINAE

```cpp
// C++17之前：需要两个重载
template<typename T>
std::enable_if_t<std::is_integral_v<T>>
process(T x) {
    std::cout << "Integer: " << x << "\n";
}

template<typename T>
std::enable_if_t<!std::is_integral_v<T>>
process(T x) {
    std::cout << "Non-integer: " << x << "\n";
}

// C++17：一个函数
template<typename T>
void process(T x) {
    if constexpr (std::is_integral_v<T>) {
        std::cout << "Integer: " << x << "\n";
    } else {
        std::cout << "Non-integer: " << x << "\n";
    }
}
```

### 3.2 std::void_t

```cpp
// 检测成员类型
template<typename T, typename = void>
struct has_iterator : std::false_type {};

template<typename T>
struct has_iterator<T, std::void_t<typename T::iterator>> 
    : std::true_type {};

static_assert(has_iterator<std::vector<int>>::value);
static_assert(!has_iterator<int>::value);
```

---

## 四、C++20 Concepts

### 4.1 定义Concept

```cpp
// 基本Concept
template<typename T>
concept Integral = std::is_integral_v<T>;

template<typename T>
concept FloatingPoint = std::is_floating_point_v<T>;

// 复合Concept
template<typename T>
concept Numeric = Integral<T> || FloatingPoint<T>;

// 带约束的Concept
template<typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::same_as<T>;
};
```

### 4.2 使用Concept

```cpp
// 方式1：requires子句
template<typename T>
requires Integral<T>
T double_value(T x) {
    return x * 2;
}

// 方式2：直接约束
template<Integral T>
T triple_value(T x) {
    return x * 3;
}

// 方式3：简化语法
auto quad_value(Integral auto x) {
    return x * 4;
}
```

### 4.3 requires表达式

```cpp
template<typename T>
concept Container = requires(T c) {
    typename T::value_type;
    typename T::iterator;
    { c.begin() } -> std::same_as<typename T::iterator>;
    { c.end() } -> std::same_as<typename T::iterator>;
    { c.size() } -> std::convertible_to<std::size_t>;
};

template<Container C>
void printContainer(const C& c) {
    for (const auto& item : c) {
        std::cout << item << " ";
    }
    std::cout << "\n";
}
```

---

## 五、HFT应用

### 5.1 消息类型检测

```cpp
template<typename T>
concept MarketDataMessage = requires(T msg) {
    { msg.symbol() } -> std::convertible_to<std::string_view>;
    { msg.price() } -> std::convertible_to<double>;
    { msg.quantity() } -> std::convertible_to<int64_t>;
    { msg.timestamp() } -> std::convertible_to<uint64_t>;
};

template<MarketDataMessage Msg>
void processMarketData(const Msg& msg) {
    // 类型安全的处理
}
```

### 5.2 序列化约束

```cpp
template<typename T>
concept Serializable = requires(T t, char* buffer) {
    { t.serialize(buffer) } -> std::same_as<size_t>;
    { T::deserialize(buffer) } -> std::same_as<T>;
    { T::serialized_size() } -> std::convertible_to<size_t>;
};

template<Serializable T>
void sendMessage(const T& msg) {
    char buffer[T::serialized_size()];
    msg.serialize(buffer);
    // 发送...
}
```

---

## 总结

| 技术 | 版本 | 可读性 | 推荐程度 |
|------|------|--------|----------|
| SFINAE + enable_if | C++11 | 低 | 遗留代码 |
| if constexpr | C++17 | 中 | 推荐 |
| Concepts | C++20 | 高 | **强烈推荐** |

**最佳实践**：
1. 新代码优先使用Concepts
2. C++17代码使用if constexpr
3. SFINAE仅用于向后兼容

---

## 相关文章

- [上一篇：Compile-Time Computation and constexpr](/articles/cpp/cpp-12-编译期计算与constexpr/)
- [下一篇：Exception Handling and Performance](/articles/cpp/cpp-14-异常处理机制与性能开销/)
