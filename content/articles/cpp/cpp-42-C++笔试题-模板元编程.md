+++
title = "42.C++笔试题-模板元编程"
date = 2026-01-31
description = "C++模板元编程笔试题：模板特化、SFINAE、constexpr、类型萃取"
[taxonomies]
tags = ["C++", "笔试", "模板", "元编程", "SFINAE"]
+++

# C++ 笔试题 - 模板元编程

本文汇集 C++ 模板元编程相关的笔试题，覆盖模板特化、SFINAE、constexpr、类型萃取等核心概念。

**难度标注**：★☆☆ 基础 | ★★☆ 中级 | ★★★ 困难

---

## 一、选择题

### 题目 1 ★☆☆

以下代码输出什么？

```cpp
template<typename T>
void print(T) { cout << "generic"; }

template<>
void print(int) { cout << "int"; }

void print(double) { cout << "double"; }

int main() {
    print(1);
    print(1.0);
    print('a');
}
```

A. generic generic generic  
B. int double generic  
C. int double int  
D. generic double generic

<details>
<summary>查看答案与解析</summary>

**答案：B**

**重载决议规则**：
1. 普通函数优先于模板
2. 特化版本在模板选中后才考虑

```cpp
print(1);    // int 匹配特化版本 → "int"
print(1.0);  // double 匹配普通函数（优先）→ "double"
print('a');  // char 匹配泛型模板 → "generic"
```

**优先级**：
```
普通函数 > 模板特化 > 模板泛型
```

</details>

---

### 题目 2 ★★☆

SFINAE 的含义是：

A. Substitution Failure Is Not An Error  
B. Simple Function Is Not An Expression  
C. Static Function In Any Expression  
D. Substitution Failure In All Expressions

<details>
<summary>查看答案与解析</summary>

**答案：A**

**SFINAE**：Substitution Failure Is Not An Error
- 模板参数替换失败时，不报错，而是从候选中移除
- 是实现编译期条件选择的基础

```cpp
// 示例：检测是否有 size() 成员
template<typename T>
auto has_size_impl(int) -> decltype(std::declval<T>().size(), std::true_type{});

template<typename T>
std::false_type has_size_impl(...);

template<typename T>
using has_size = decltype(has_size_impl<T>(0));

// 使用
static_assert(has_size<std::vector<int>>::value);  // true
static_assert(!has_size<int>::value);              // false
```

</details>

---

### 题目 3 ★★☆

以下代码编译结果是什么？

```cpp
template<int N>
struct Factorial {
    static constexpr int value = N * Factorial<N-1>::value;
};

template<>
struct Factorial<0> {
    static constexpr int value = 1;
};

int main() {
    constexpr int x = Factorial<5>::value;
    return x;
}
```

A. 编译错误  
B. 运行时计算 120  
C. 编译期计算 120  
D. 无限递归

<details>
<summary>查看答案与解析</summary>

**答案：C**

**模板元编程**：编译期递归计算。

```
Factorial<5>::value
= 5 * Factorial<4>::value
= 5 * 4 * Factorial<3>::value
= 5 * 4 * 3 * Factorial<2>::value
= 5 * 4 * 3 * 2 * Factorial<1>::value
= 5 * 4 * 3 * 2 * 1 * Factorial<0>::value
= 5 * 4 * 3 * 2 * 1 * 1
= 120
```

编译后代码等价于：
```cpp
int main() {
    return 120;  // 编译期常量
}
```

</details>

---

### 题目 4 ★★★

以下代码的输出是什么？

```cpp
template<typename T, typename = void>
struct is_container : std::false_type {};

template<typename T>
struct is_container<T, std::void_t<
    typename T::iterator,
    decltype(std::declval<T>().begin()),
    decltype(std::declval<T>().end())
>> : std::true_type {};

int main() {
    cout << is_container<std::vector<int>>::value << " ";
    cout << is_container<int>::value;
}
```

A. 0 0  
B. 1 0  
C. 0 1  
D. 1 1

<details>
<summary>查看答案与解析</summary>

**答案：B**

**std::void_t 技巧**（C++17）：
- 如果所有类型有效，`void_t` 就是 `void`
- SFINAE 选择特化版本

```cpp
// std::vector<int> 检查：
// - 有 iterator 类型 ✓
// - 有 begin() 方法 ✓
// - 有 end() 方法 ✓
// → 选择特化版本，继承 true_type

// int 检查：
// - 没有 iterator 类型 ✗
// → 替换失败，选择主模板，继承 false_type
```

</details>

---

### 题目 5 ★★★

以下 `std::enable_if` 的正确用法是：

A. 
```cpp
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
func(T t) { return t * 2; }
```

B.
```cpp
template<typename T, std::enable_if_t<std::is_integral_v<T>, int> = 0>
T func(T t) { return t * 2; }
```

C.
```cpp
template<typename T>
T func(T t) requires std::is_integral_v<T> { return t * 2; }
```

D. 以上都正确

<details>
<summary>查看答案与解析</summary>

**答案：D**

**三种 SFINAE 方式**：

```cpp
// 方式 A：返回类型 SFINAE（C++11）
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
func(T t) { return t * 2; }

// 方式 B：模板参数 SFINAE（C++14/17，推荐）
template<typename T, std::enable_if_t<std::is_integral_v<T>, int> = 0>
T func(T t) { return t * 2; }

// 方式 C：概念 requires（C++20，最推荐）
template<typename T>
T func(T t) requires std::is_integral_v<T> { return t * 2; }

// 或使用概念
template<std::integral T>
T func(T t) { return t * 2; }
```

</details>

---

## 二、填空题

### 题目 6 ★☆☆

C++ 模板的两种主要特化方式是 ______ 和 ______ 。

<details>
<summary>查看答案</summary>

**答案**：全特化（完全特化）、偏特化（部分特化）

```cpp
// 主模板
template<typename T, typename U>
struct Pair { /* ... */ };

// 全特化：所有参数都指定
template<>
struct Pair<int, int> { /* ... */ };

// 偏特化：部分参数指定或添加约束
template<typename T>
struct Pair<T, T> { /* ... */ };  // 两个相同类型

template<typename T>
struct Pair<T*, T*> { /* ... */ };  // 两个指针

template<typename T, typename U>
struct Pair<T*, U> { /* ... */ };  // 第一个是指针
```

**注意**：函数模板只能全特化，不能偏特化。

</details>

---

### 题目 7 ★★☆

`std::integral_constant<bool, true>` 的别名是 ______ ，常用于实现 ______ 。

<details>
<summary>查看答案</summary>

**答案**：`std::true_type`、类型萃取（type traits）

```cpp
// 标准库定义
using true_type = integral_constant<bool, true>;
using false_type = integral_constant<bool, false>;

// 使用示例
template<typename T>
struct is_pointer : std::false_type {};

template<typename T>
struct is_pointer<T*> : std::true_type {};

// 检查
static_assert(is_pointer<int*>::value);
static_assert(!is_pointer<int>::value);

// 值访问
constexpr bool b = is_pointer<int*>::value;  // true
// 或 C++17
constexpr bool b = is_pointer_v<int*>;  // true
```

</details>

---

### 题目 8 ★★★

C++17 引入的折叠表达式支持四种形式：______ 、______ 、______ 、______ 。

<details>
<summary>查看答案</summary>

**答案**：一元左折叠、一元右折叠、二元左折叠、二元右折叠

```cpp
// (... op pack) - 一元左折叠
// (pack op ...) - 一元右折叠
// (init op ... op pack) - 二元左折叠
// (pack op ... op init) - 二元右折叠

template<typename... Args>
auto sum(Args... args) {
    return (... + args);  // 一元左折叠
    // ((arg1 + arg2) + arg3) + ...
}

template<typename... Args>
auto sum_right(Args... args) {
    return (args + ...);  // 一元右折叠
    // arg1 + (arg2 + (arg3 + ...))
}

template<typename... Args>
auto sum_with_init(Args... args) {
    return (0 + ... + args);  // 二元左折叠
    // ((0 + arg1) + arg2) + ...
}

// 使用
sum(1, 2, 3, 4);  // 10
```

</details>

---

## 三、简答题

### 题目 9 ★★☆

解释 `std::decay` 的作用。

<details>
<summary>参考答案</summary>

**std::decay 的转换规则**：

1. 移除引用
2. 对于数组类型，转换为指针
3. 对于函数类型，转换为函数指针
4. 移除 cv 限定符（const/volatile）

```cpp
#include <type_traits>

// 示例
static_assert(std::is_same_v<std::decay_t<int&>, int>);
static_assert(std::is_same_v<std::decay_t<int&&>, int>);
static_assert(std::is_same_v<std::decay_t<const int&>, int>);
static_assert(std::is_same_v<std::decay_t<int[10]>, int*>);
static_assert(std::is_same_v<std::decay_t<int(int)>, int(*)(int)>);

// 实际应用：存储参数
template<typename T>
class Holder {
    std::decay_t<T> value;  // 存储值，不是引用
public:
    Holder(T&& v) : value(std::forward<T>(v)) {}
};

// auto 推导也类似
auto x = expr;  // 类似 decay
```

</details>

---

### 题目 10 ★★★

解释完美转发（Perfect Forwarding）的原理。

<details>
<summary>参考答案</summary>

**完美转发**：保持参数的值类别（左值/右值）。

**核心组件**：
1. 万能引用（Universal Reference）
2. std::forward

```cpp
// 万能引用：T&& 在模板推导中
template<typename T>
void wrapper(T&& arg) {
    // arg 总是左值（有名字）
    // 但 T 的推导保留了原始值类别信息
    
    target(std::forward<T>(arg));
}

// 引用折叠规则
// T& & → T&
// T& && → T&
// T&& & → T&
// T&& && → T&&
```

**推导过程**：

```cpp
void target(int& x);   // 左值版本
void target(int&& x);  // 右值版本

template<typename T>
void wrapper(T&& arg) {
    target(std::forward<T>(arg));
}

int x = 1;
wrapper(x);    // T = int&, T&& = int& && = int&
               // forward<int&>(arg) 返回 int&
               // 调用 target(int&)

wrapper(1);    // T = int, T&& = int&&
               // forward<int>(arg) 返回 int&&
               // 调用 target(int&&)
```

**std::forward 实现**：

```cpp
template<typename T>
T&& forward(std::remove_reference_t<T>& arg) noexcept {
    return static_cast<T&&>(arg);
}

// 当 T = int&: 返回 int& && = int&（左值）
// 当 T = int:  返回 int &&     = int&&（右值）
```

</details>

---

## 四、编程题

### 题目 11 ★★☆

实现一个编译期计算斐波那契数列的模板。

<details>
<summary>参考答案</summary>

```cpp
#include <iostream>
#include <type_traits>

// 方法 1：模板递归（C++11）
template<size_t N>
struct Fibonacci {
    static constexpr size_t value = 
        Fibonacci<N-1>::value + Fibonacci<N-2>::value;
};

template<>
struct Fibonacci<0> {
    static constexpr size_t value = 0;
};

template<>
struct Fibonacci<1> {
    static constexpr size_t value = 1;
};

// 方法 2：constexpr 函数（C++14）
constexpr size_t fibonacci(size_t n) {
    if (n <= 1) return n;
    
    size_t a = 0, b = 1;
    for (size_t i = 2; i <= n; i++) {
        size_t tmp = a + b;
        a = b;
        b = tmp;
    }
    return b;
}

// 方法 3：变量模板（C++14）
template<size_t N>
constexpr size_t fib_v = fib_v<N-1> + fib_v<N-2>;

template<>
constexpr size_t fib_v<0> = 0;

template<>
constexpr size_t fib_v<1> = 1;

// 测试
int main() {
    // 编译期计算
    static_assert(Fibonacci<10>::value == 55);
    static_assert(fibonacci(10) == 55);
    static_assert(fib_v<10> == 55);
    
    // 打印前 20 个
    constexpr size_t N = 20;
    std::cout << "Fibonacci sequence:\n";
    
    // 使用折叠表达式打印（C++17）
    []<size_t... Is>(std::index_sequence<Is...>) {
        ((std::cout << Fibonacci<Is>::value << " "), ...);
    }(std::make_index_sequence<N>{});
    
    std::cout << std::endl;
    
    return 0;
}
```

</details>

---

### 题目 12 ★★★

实现一个类型萃取：检测类型是否可迭代（有 begin/end）。

<details>
<summary>参考答案</summary>

```cpp
#include <type_traits>
#include <iterator>
#include <vector>
#include <iostream>

// C++17 实现
template<typename T, typename = void>
struct is_iterable : std::false_type {};

template<typename T>
struct is_iterable<T, std::void_t<
    decltype(std::begin(std::declval<T&>())),
    decltype(std::end(std::declval<T&>()))
>> : std::true_type {};

template<typename T>
inline constexpr bool is_iterable_v = is_iterable<T>::value;

// 更完整的检测（包括迭代器要求）
template<typename T, typename = void>
struct is_range : std::false_type {};

template<typename T>
struct is_range<T, std::void_t<
    decltype(std::begin(std::declval<T&>())),
    decltype(std::end(std::declval<T&>())),
    decltype(++std::declval<decltype(std::begin(std::declval<T&>()))&>()),
    decltype(*std::begin(std::declval<T&>()))
>> : std::true_type {};

template<typename T>
inline constexpr bool is_range_v = is_range<T>::value;

// C++20 概念版本
#if __cplusplus >= 202002L
template<typename T>
concept Iterable = requires(T& t) {
    std::begin(t);
    std::end(t);
};

template<typename T>
concept Range = Iterable<T> && requires(T& t) {
    { ++std::begin(t) };
    { *std::begin(t) };
};
#endif

// 使用萃取的函数
template<typename T>
std::enable_if_t<is_iterable_v<T>>
print_all(const T& container) {
    for (const auto& item : container) {
        std::cout << item << " ";
    }
    std::cout << std::endl;
}

template<typename T>
std::enable_if_t<!is_iterable_v<T>>
print_all(const T& value) {
    std::cout << value << std::endl;
}

int main() {
    // 类型检测
    static_assert(is_iterable_v<std::vector<int>>);
    static_assert(is_iterable_v<int[10]>);
    static_assert(!is_iterable_v<int>);
    static_assert(!is_iterable_v<double>);
    
    // 使用
    std::vector<int> vec{1, 2, 3, 4, 5};
    int arr[] = {6, 7, 8, 9, 10};
    int x = 42;
    
    print_all(vec);  // 1 2 3 4 5
    print_all(arr);  // 6 7 8 9 10
    print_all(x);    // 42
    
    return 0;
}
```

</details>

---

### 题目 13 ★★★

实现一个编译期类型列表（Type List）和基本操作。

<details>
<summary>参考答案</summary>

```cpp
#include <type_traits>
#include <iostream>
#include <cxxabi.h>

// 类型列表
template<typename... Ts>
struct TypeList {};

// 获取大小
template<typename List>
struct Size;

template<typename... Ts>
struct Size<TypeList<Ts...>> {
    static constexpr size_t value = sizeof...(Ts);
};

template<typename List>
inline constexpr size_t Size_v = Size<List>::value;

// 获取第 N 个类型
template<typename List, size_t N>
struct At;

template<typename Head, typename... Tail>
struct At<TypeList<Head, Tail...>, 0> {
    using type = Head;
};

template<typename Head, typename... Tail, size_t N>
struct At<TypeList<Head, Tail...>, N> {
    using type = typename At<TypeList<Tail...>, N-1>::type;
};

template<typename List, size_t N>
using At_t = typename At<List, N>::type;

// 追加类型
template<typename List, typename T>
struct Append;

template<typename... Ts, typename T>
struct Append<TypeList<Ts...>, T> {
    using type = TypeList<Ts..., T>;
};

template<typename List, typename T>
using Append_t = typename Append<List, T>::type;

// 前置类型
template<typename List, typename T>
struct Prepend;

template<typename... Ts, typename T>
struct Prepend<TypeList<Ts...>, T> {
    using type = TypeList<T, Ts...>;
};

template<typename List, typename T>
using Prepend_t = typename Prepend<List, T>::type;

// 连接两个列表
template<typename List1, typename List2>
struct Concat;

template<typename... Ts, typename... Us>
struct Concat<TypeList<Ts...>, TypeList<Us...>> {
    using type = TypeList<Ts..., Us...>;
};

template<typename List1, typename List2>
using Concat_t = typename Concat<List1, List2>::type;

// 检查是否包含
template<typename List, typename T>
struct Contains;

template<typename T>
struct Contains<TypeList<>, T> : std::false_type {};

template<typename Head, typename... Tail, typename T>
struct Contains<TypeList<Head, Tail...>, T> 
    : std::conditional_t<
        std::is_same_v<Head, T>,
        std::true_type,
        Contains<TypeList<Tail...>, T>
    > {};

template<typename List, typename T>
inline constexpr bool Contains_v = Contains<List, T>::value;

// 变换（Map）
template<typename List, template<typename> class F>
struct Transform;

template<typename... Ts, template<typename> class F>
struct Transform<TypeList<Ts...>, F> {
    using type = TypeList<typename F<Ts>::type...>;
};

template<typename List, template<typename> class F>
using Transform_t = typename Transform<List, F>::type;

// 过滤（Filter）
template<typename List, template<typename> class Pred>
struct Filter;

template<template<typename> class Pred>
struct Filter<TypeList<>, Pred> {
    using type = TypeList<>;
};

template<typename Head, typename... Tail, template<typename> class Pred>
struct Filter<TypeList<Head, Tail...>, Pred> {
    using rest = typename Filter<TypeList<Tail...>, Pred>::type;
    using type = std::conditional_t<
        Pred<Head>::value,
        Prepend_t<rest, Head>,
        rest
    >;
};

template<typename List, template<typename> class Pred>
using Filter_t = typename Filter<List, Pred>::type;

// 辅助函数：打印类型名
template<typename T>
std::string type_name() {
    int status;
    char* demangled = abi::__cxa_demangle(typeid(T).name(), 0, 0, &status);
    std::string result(demangled);
    free(demangled);
    return result;
}

template<typename... Ts>
void print_types(TypeList<Ts...>) {
    ((std::cout << type_name<Ts>() << " "), ...);
    std::cout << std::endl;
}

int main() {
    using List = TypeList<int, double, char, float>;
    
    std::cout << "Size: " << Size_v<List> << std::endl;
    std::cout << "At<1>: " << type_name<At_t<List, 1>>() << std::endl;
    std::cout << "Contains<int>: " << Contains_v<List, int> << std::endl;
    std::cout << "Contains<long>: " << Contains_v<List, long> << std::endl;
    
    using Extended = Append_t<List, long>;
    std::cout << "Extended: ";
    print_types(Extended{});
    
    // 过滤整数类型
    using Integers = Filter_t<List, std::is_integral>;
    std::cout << "Integers: ";
    print_types(Integers{});  // int char
    
    return 0;
}
```

</details>

---

## 五、Bug 分析题

### 题目 14 ★★☆

以下代码有什么问题？

```cpp
template<typename T>
class Container {
    T data;
public:
    template<typename U>
    Container(U&& value) : data(std::forward<U>(value)) {}
};

int main() {
    Container<int> c1(42);
    Container<int> c2 = c1;  // 错误！
}
```

<details>
<summary>查看答案与解析</summary>

**问题**：万能引用构造函数"吃掉"了拷贝构造。

```cpp
Container<int> c2 = c1;
// c1 是左值，U 推导为 Container<int>&
// 万能引用构造比拷贝构造更匹配
// 尝试用 Container<int>& 初始化 int → 错误
```

**修复**：使用 SFINAE 排除自身类型。

```cpp
template<typename T>
class Container {
    T data;
public:
    // 排除 Container 本身
    template<typename U,
             typename = std::enable_if_t<
                 !std::is_same_v<std::decay_t<U>, Container>
             >>
    Container(U&& value) : data(std::forward<U>(value)) {}
    
    // 显式默认拷贝/移动
    Container(const Container&) = default;
    Container(Container&&) = default;
    Container& operator=(const Container&) = default;
    Container& operator=(Container&&) = default;
};
```

或 C++20：
```cpp
template<typename U>
    requires (!std::same_as<std::decay_t<U>, Container>)
Container(U&& value) : data(std::forward<U>(value)) {}
```

</details>

---

### 题目 15 ★★★

以下代码为什么编译错误？

```cpp
template<typename T>
struct Base {
    void foo() {}
};

template<typename T>
struct Derived : Base<T> {
    void bar() {
        foo();  // 错误！
    }
};
```

<details>
<summary>查看答案与解析</summary>

**问题**：两阶段名称查找（Two-Phase Lookup）。

- 第一阶段：解析模板定义时查找非依赖名称
- 第二阶段：实例化时查找依赖名称

`foo()` 不依赖于 T，在第一阶段查找，但 `Base<T>` 还未实例化。

**修复**：使名称依赖于模板参数。

```cpp
template<typename T>
struct Derived : Base<T> {
    void bar() {
        // 方法 1：使用 this->
        this->foo();
        
        // 方法 2：使用作用域限定
        Base<T>::foo();
        
        // 方法 3：using 声明
        // using Base<T>::foo;  // 在类内声明
        // foo();
    }
};

// 完整示例
template<typename T>
struct Derived2 : Base<T> {
    using Base<T>::foo;  // 引入名称
    
    void bar() {
        foo();  // 现在可以了
    }
};
```

</details>

---

## 六、高频考点总结

| 考点 | 频率 | 难度 | 关键知识 |
|------|------|------|----------|
| 模板特化 | ★★★ | ★★☆ | 全特化、偏特化 |
| SFINAE | ★★★ | ★★★ | enable_if、void_t |
| constexpr | ★★★ | ★★☆ | 编译期计算 |
| 完美转发 | ★★★ | ★★★ | forward、引用折叠 |
| 类型萃取 | ★★☆ | ★★☆ | type_traits |
| 变参模板 | ★★☆ | ★★★ | 包展开、折叠表达式 |
| 两阶段查找 | ★★☆ | ★★★ | 依赖名称 |

---

## 相关文章

- [上一篇：C++笔试题-并发编程](/articles/cpp/cpp-41-C++笔试题-并发编程/)
- [下一篇：C++面试题-内存与对象模型](/articles/cpp/cpp-43-C++面试题-内存与对象模型/)
