+++
title = "08.C++模板与泛型编程"
date = 2026-01-19
description = "C++模板详解：函数模板、类模板、模板特化、SFINAE、可变参数模板"
[taxonomies]
tags = ["C++", "模板", "泛型"]
+++

## 函数模板

### 基本语法

```cpp
template<typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

// 使用
int m1 = max(3, 5);         // T = int
double m2 = max(3.14, 2.7); // T = double
max<int>(3, 5);             // 显式指定类型
```

### 多类型参数

```cpp
template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}

// C++14 简化
template<typename T, typename U>
auto add(T a, U b) {
    return a + b;
}
```

### 非类型模板参数

```cpp
template<typename T, int N>
class Array {
    T data[N];
public:
    int size() const { return N; }
};

Array<int, 10> arr;  // 编译期确定大小
```

---

## 类模板

### 基本语法

```cpp
template<typename T>
class Stack {
    std::vector<T> elements;
public:
    void push(const T& elem) {
        elements.push_back(elem);
    }
    
    T pop() {
        T elem = elements.back();
        elements.pop_back();
        return elem;
    }
    
    bool empty() const {
        return elements.empty();
    }
};

Stack<int> intStack;
Stack<std::string> strStack;
```

### 成员函数模板

```cpp
template<typename T>
class Container {
public:
    template<typename U>
    void copyFrom(const Container<U>& other) {
        // 从其他类型容器复制
    }
};
```

### 默认模板参数

```cpp
template<typename T, typename Container = std::vector<T>>
class Stack {
    Container elements;
    // ...
};

Stack<int> s1;                    // 使用vector
Stack<int, std::deque<int>> s2;   // 使用deque
```

---

## 模板特化

### 全特化

```cpp
// 主模板
template<typename T>
class Printer {
public:
    void print(const T& value) {
        std::cout << value << std::endl;
    }
};

// 全特化：针对bool类型
template<>
class Printer<bool> {
public:
    void print(const bool& value) {
        std::cout << (value ? "true" : "false") << std::endl;
    }
};
```

### 偏特化

```cpp
// 主模板
template<typename T, typename U>
class Pair {
    T first;
    U second;
};

// 偏特化：当两个类型相同时
template<typename T>
class Pair<T, T> {
    T first;
    T second;
    // 可以有不同实现
};

// 偏特化：当第一个是指针时
template<typename T, typename U>
class Pair<T*, U> {
    // 指针特殊处理
};
```

### 函数模板特化

```cpp
template<typename T>
bool compare(T a, T b) {
    return a < b;
}

// 特化：C字符串比较
template<>
bool compare<const char*>(const char* a, const char* b) {
    return strcmp(a, b) < 0;
}
```

---

## SFINAE

### 概念

**Substitution Failure Is Not An Error**：模板参数替换失败不是错误，只是该重载不参与候选。

### std::enable_if

```cpp
// 只对整数类型启用
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
process(T value) {
    return value * 2;
}

// C++14 简化
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
process(T value) {
    return value * 2;
}
```

### if constexpr（C++17）

```cpp
template<typename T>
auto process(T value) {
    if constexpr (std::is_integral_v<T>) {
        return value * 2;
    } else if constexpr (std::is_floating_point_v<T>) {
        return value * 2.0;
    } else {
        return value;
    }
}
```

### 类型萃取

```cpp
// 移除引用
std::remove_reference<int&>::type  // int

// 移除const
std::remove_const<const int>::type  // int

// 添加指针
std::add_pointer<int>::type  // int*

// 判断类型
std::is_same<T, int>::value
std::is_pointer<T>::value
std::is_class<T>::value
```

---

## 可变参数模板

### 基本语法

```cpp
template<typename... Args>
void print(Args... args) {
    // args是参数包
}

print(1, 2.5, "hello");  // Args = int, double, const char*
```

### 递归展开

```cpp
// 终止条件
void print() {}

// 递归展开
template<typename T, typename... Args>
void print(T first, Args... rest) {
    std::cout << first << " ";
    print(rest...);  // 递归调用
}

print(1, 2.5, "hello");  // 输出: 1 2.5 hello
```

### 折叠表达式（C++17）

```cpp
template<typename... Args>
auto sum(Args... args) {
    return (... + args);  // 左折叠
    // (args + ...) 右折叠
}

sum(1, 2, 3, 4, 5);  // 15
```

### 应用示例

```cpp
// make_unique实现
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

// 类型安全的printf
template<typename... Args>
void log(const char* fmt, Args... args) {
    printf(fmt, args...);
}
```

---

## 模板元编程

### 编译期计算

```cpp
// 编译期阶乘
template<int N>
struct Factorial {
    static constexpr int value = N * Factorial<N-1>::value;
};

template<>
struct Factorial<0> {
    static constexpr int value = 1;
};

constexpr int result = Factorial<5>::value;  // 120
```

### 类型列表

```cpp
template<typename... Types>
struct TypeList {};

using MyTypes = TypeList<int, double, std::string>;
```

### 编译期条件

```cpp
template<bool Condition, typename Then, typename Else>
struct If;

template<typename Then, typename Else>
struct If<true, Then, Else> {
    using type = Then;
};

template<typename Then, typename Else>
struct If<false, Then, Else> {
    using type = Else;
};

using Result = If<sizeof(int) == 4, int, long>::type;
```

---

## Concepts（C++20）

### 定义概念

```cpp
template<typename T>
concept Arithmetic = std::is_arithmetic_v<T>;

template<typename T>
concept Printable = requires(T t) {
    std::cout << t;
};

template<typename T>
concept Container = requires(T t) {
    t.begin();
    t.end();
    t.size();
};
```

### 使用概念

```cpp
// 方式1：requires子句
template<typename T>
    requires Arithmetic<T>
T add(T a, T b) {
    return a + b;
}

// 方式2：概念作为类型约束
template<Arithmetic T>
T multiply(T a, T b) {
    return a * b;
}

// 方式3：简写
auto divide(Arithmetic auto a, Arithmetic auto b) {
    return a / b;
}
```

### 错误信息改进

```cpp
// 没有concepts：模板错误信息冗长难懂
// 有concepts：清晰说明哪个约束不满足

template<Container C>
void process(C& c) { }

process(42);  // 错误：int不满足Container概念
```

---

## 总结

| 特性 | 用途 | 版本 |
|------|------|------|
| 函数模板 | 泛型函数 | C++98 |
| 类模板 | 泛型类 | C++98 |
| 模板特化 | 特定类型优化 | C++98 |
| SFINAE | 条件启用 | C++98 |
| 可变参数模板 | 任意参数 | C++11 |
| if constexpr | 编译期分支 | C++17 |
| 折叠表达式 | 展开参数包 | C++17 |
| Concepts | 类型约束 | C++20 |

模板是C++最强大的特性之一，理解模板对于阅读标准库源码和编写高性能泛型代码至关重要。
