+++
title = "现代C++进阶-模板元编程"
date = 2026-02-02
weight = 51000
description = "模板元编程：SFINAE、类型萃取、编译期计算、变参模板"
[taxonomies]
tags = ["HFT", "C++", "模板", "元编程", "SFINAE"]
+++

# 现代 C++ 进阶 - 模板元编程

本文深入讲解 C++ 模板元编程技术，包括 SFINAE、类型萃取、编译期计算和变参模板。

---

## 一、模板基础

### 1.1 函数模板

```cpp
// 基本函数模板
template<typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

// 多类型参数
template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}

// C++14: 自动返回类型推导
template<typename T, typename U>
auto add_v2(T a, U b) {
    return a + b;
}

// 非类型模板参数
template<typename T, int N>
class Array {
    T data[N];
public:
    constexpr int size() const { return N; }
};

// C++17: 自动推导非类型参数类型
template<auto N>
struct Constant {
    static constexpr auto value = N;
};

Constant<42> int_const;
Constant<'a'> char_const;
```

### 1.2 类模板

```cpp
// 主模板
template<typename T>
class Container {
public:
    void add(const T& item);
    T get(size_t index);
};

// 全特化
template<>
class Container<bool> {
    // 特殊的 bool 实现（位压缩）
};

// 偏特化
template<typename T>
class Container<T*> {
    // 指针类型的特殊实现
};

template<typename T, typename U>
class Pair;

template<typename T>
class Pair<T, T> {
    // 两个相同类型的特化
};
```

### 1.3 变参模板

```cpp
// 变参函数模板
template<typename... Args>
void print(Args... args) {
    (std::cout << ... << args) << '\n';  // C++17 折叠表达式
}

// 递归展开（C++11/14 方式）
template<typename T>
void print_recursive(T t) {
    std::cout << t << '\n';
}

template<typename T, typename... Rest>
void print_recursive(T first, Rest... rest) {
    std::cout << first << ", ";
    print_recursive(rest...);
}

// sizeof...
template<typename... Args>
constexpr size_t count_args() {
    return sizeof...(Args);
}

// 变参类模板
template<typename... Types>
class Tuple;

template<>
class Tuple<> {};

template<typename Head, typename... Tail>
class Tuple<Head, Tail...> : public Tuple<Tail...> {
public:
    Head head;
};

// 获取类型
template<size_t I, typename T>
struct tuple_element;

template<typename Head, typename... Tail>
struct tuple_element<0, Tuple<Head, Tail...>> {
    using type = Head;
};

template<size_t I, typename Head, typename... Tail>
struct tuple_element<I, Tuple<Head, Tail...>> {
    using type = typename tuple_element<I - 1, Tuple<Tail...>>::type;
};
```

---

## 二、SFINAE

### 2.1 基本概念

**SFINAE**（Substitution Failure Is Not An Error）：模板参数替换失败不是错误，只是将该重载从候选集中排除。

```cpp
// 基本 SFINAE
template<typename T>
typename T::value_type get_value(T& container) {
    return container.front();
}

// 如果 T 没有 value_type，这个重载被排除，而不是报错
// 编译器会尝试其他重载

// enable_if
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
double_value(T x) {
    return x * 2;
}

template<typename T>
typename std::enable_if<std::is_floating_point<T>::value, T>::type
double_value(T x) {
    return x * 2.0;
}
```

### 2.2 检测表达式有效性

```cpp
// void_t 技巧（C++17 标准，C++11 可实现）
template<typename...>
using void_t = void;

// 检测类型是否有 size() 方法
template<typename T, typename = void>
struct has_size : std::false_type {};

template<typename T>
struct has_size<T, void_t<decltype(std::declval<T>().size())>> 
    : std::true_type {};

// 使用
static_assert(has_size<std::vector<int>>::value);
static_assert(!has_size<int>::value);

// 检测是否可调用
template<typename F, typename... Args, typename = void>
struct is_callable : std::false_type {};

template<typename F, typename... Args>
struct is_callable<F, Args..., 
    void_t<decltype(std::declval<F>()(std::declval<Args>()...))>>
    : std::true_type {};

// C++17 检测惯用法
template<typename Default, typename AlwaysVoid, template<typename...> class Op, typename... Args>
struct detector {
    using value_t = std::false_type;
    using type = Default;
};

template<typename Default, template<typename...> class Op, typename... Args>
struct detector<Default, void_t<Op<Args...>>, Op, Args...> {
    using value_t = std::true_type;
    using type = Op<Args...>;
};

// 定义检测器
struct nonesuch {
    nonesuch() = delete;
    ~nonesuch() = delete;
    nonesuch(const nonesuch&) = delete;
    void operator=(const nonesuch&) = delete;
};

template<template<typename...> class Op, typename... Args>
using is_detected = typename detector<nonesuch, void, Op, Args...>::value_t;

template<template<typename...> class Op, typename... Args>
using detected_t = typename detector<nonesuch, void, Op, Args...>::type;

// 使用检测器
template<typename T>
using size_type_t = decltype(std::declval<T>().size());

template<typename T>
constexpr bool has_size_v = is_detected<size_type_t, T>::value;
```

### 2.3 现代替代：C++20 Concepts

```cpp
// SFINAE 方式
template<typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
T square_sfinae(T x) {
    return x * x;
}

// Concepts 方式（更清晰）
template<std::integral T>
T square_concept(T x) {
    return x * x;
}

// 复杂约束
template<typename T>
concept Sortable = requires(T& t) {
    std::begin(t);
    std::end(t);
    requires std::random_access_iterator<decltype(std::begin(t))>;
    requires std::totally_ordered<decltype(*std::begin(t))>;
};

template<Sortable T>
void my_sort(T& container) {
    std::sort(std::begin(container), std::end(container));
}
```

---

## 三、类型萃取

### 3.1 标准类型萃取

```cpp
#include <type_traits>

// 类型判断
static_assert(std::is_integral_v<int>);
static_assert(std::is_floating_point_v<double>);
static_assert(std::is_pointer_v<int*>);
static_assert(std::is_reference_v<int&>);
static_assert(std::is_class_v<std::string>);
static_assert(std::is_enum_v<Color>);

// 类型关系
static_assert(std::is_same_v<int, int>);
static_assert(std::is_base_of_v<Base, Derived>);
static_assert(std::is_convertible_v<Derived*, Base*>);

// 类型修改
using NoConst = std::remove_const_t<const int>;      // int
using NoRef = std::remove_reference_t<int&>;          // int
using AddPtr = std::add_pointer_t<int>;               // int*
using Decay = std::decay_t<const int&>;               // int

// 条件类型
using Type = std::conditional_t<true, int, double>;   // int

// 常见陷阱
using T1 = std::remove_const_t<const int*>;  // const int* （不变！）
using T2 = std::remove_const_t<int* const>;  // int*
// remove_const 只移除顶层 const
```

### 3.2 自定义类型萃取

```cpp
// 获取函数返回类型
template<typename F>
struct function_traits;

template<typename R, typename... Args>
struct function_traits<R(Args...)> {
    using return_type = R;
    using args_tuple = std::tuple<Args...>;
    static constexpr size_t arity = sizeof...(Args);
    
    template<size_t N>
    using arg = std::tuple_element_t<N, args_tuple>;
};

// 成员函数
template<typename R, typename C, typename... Args>
struct function_traits<R(C::*)(Args...)> {
    using return_type = R;
    using class_type = C;
    using args_tuple = std::tuple<Args...>;
    static constexpr size_t arity = sizeof...(Args);
};

// const 成员函数
template<typename R, typename C, typename... Args>
struct function_traits<R(C::*)(Args...) const> 
    : function_traits<R(C::*)(Args...)> {};

// Lambda / 可调用对象
template<typename T>
struct function_traits : function_traits<decltype(&T::operator())> {};

// 使用
auto lambda = [](int x, double y) { return x + y; };
using Traits = function_traits<decltype(lambda)>;
static_assert(Traits::arity == 2);
static_assert(std::is_same_v<Traits::return_type, double>);
static_assert(std::is_same_v<Traits::arg<0>, int>);
```

### 3.3 类型列表操作

```cpp
// 类型列表
template<typename... Ts>
struct type_list {};

// 获取第一个类型
template<typename List>
struct front;

template<typename Head, typename... Tail>
struct front<type_list<Head, Tail...>> {
    using type = Head;
};

template<typename List>
using front_t = typename front<List>::type;

// 获取大小
template<typename List>
struct size;

template<typename... Ts>
struct size<type_list<Ts...>> {
    static constexpr size_t value = sizeof...(Ts);
};

template<typename List>
constexpr size_t size_v = size<List>::value;

// 追加类型
template<typename List, typename T>
struct push_back;

template<typename... Ts, typename T>
struct push_back<type_list<Ts...>, T> {
    using type = type_list<Ts..., T>;
};

template<typename List, typename T>
using push_back_t = typename push_back<List, T>::type;

// 类型过滤
template<typename List, template<typename> class Pred>
struct filter;

template<template<typename> class Pred>
struct filter<type_list<>, Pred> {
    using type = type_list<>;
};

template<typename Head, typename... Tail, template<typename> class Pred>
struct filter<type_list<Head, Tail...>, Pred> {
    using rest = typename filter<type_list<Tail...>, Pred>::type;
    using type = std::conditional_t<
        Pred<Head>::value,
        typename push_front<rest, Head>::type,
        rest
    >;
};

// 使用
using List = type_list<int, double, char, float>;
using IntegralTypes = typename filter<List, std::is_integral>::type;
// IntegralTypes = type_list<int, char>
```

---

## 四、编译期计算

### 4.1 constexpr 函数

```cpp
// C++14 constexpr 函数
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

static_assert(factorial(5) == 120);

// C++17 constexpr lambda
constexpr auto square = [](int x) { return x * x; };
static_assert(square(5) == 25);

// C++20 constexpr std::vector
constexpr int sum_of_squares() {
    std::vector<int> v = {1, 2, 3, 4, 5};
    int sum = 0;
    for (int x : v) {
        sum += x * x;
    }
    return sum;
}

static_assert(sum_of_squares() == 55);

// consteval（C++20）：必须编译期求值
consteval int must_be_compile_time(int x) {
    return x * 2;
}

int a = must_be_compile_time(5);  // OK
int b = 10;
// int c = must_be_compile_time(b);  // 错误：b 不是编译期常量
```

### 4.2 编译期字符串

```cpp
// 固定大小字符串
template<size_t N>
struct FixedString {
    char data[N]{};
    
    constexpr FixedString(const char (&str)[N]) {
        for (size_t i = 0; i < N; i++) {
            data[i] = str[i];
        }
    }
    
    constexpr char operator[](size_t i) const { return data[i]; }
    constexpr size_t size() const { return N - 1; }
    constexpr const char* c_str() const { return data; }
};

template<size_t N>
FixedString(const char (&)[N]) -> FixedString<N>;

// 编译期字符串操作
template<FixedString S>
constexpr auto string_length() {
    return S.size();
}

static_assert(string_length<"hello">() == 5);

// 编译期字符串拼接
template<FixedString A, FixedString B>
constexpr auto concat() {
    constexpr size_t N = A.size() + B.size() + 1;
    char result[N]{};
    for (size_t i = 0; i < A.size(); i++) {
        result[i] = A[i];
    }
    for (size_t i = 0; i < B.size(); i++) {
        result[A.size() + i] = B[i];
    }
    return FixedString<N>(result);
}
```

### 4.3 编译期哈希

```cpp
// FNV-1a 哈希（编译期）
constexpr uint64_t fnv1a_hash(const char* str, size_t len) {
    uint64_t hash = 14695981039346656037ULL;
    for (size_t i = 0; i < len; i++) {
        hash ^= static_cast<uint64_t>(str[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

constexpr uint64_t operator""_hash(const char* str, size_t len) {
    return fnv1a_hash(str, len);
}

// 使用
switch (command_hash) {
    case "buy"_hash:
        process_buy();
        break;
    case "sell"_hash:
        process_sell();
        break;
    case "cancel"_hash:
        process_cancel();
        break;
}

// 编译期查找表
template<typename K, typename V, size_t N>
class ConstexprMap {
public:
    constexpr ConstexprMap(std::pair<K, V> (&&pairs)[N]) {
        for (size_t i = 0; i < N; i++) {
            data_[i] = pairs[i];
        }
    }
    
    constexpr V at(const K& key) const {
        for (const auto& [k, v] : data_) {
            if (k == key) return v;
        }
        throw std::out_of_range("Key not found");
    }
    
private:
    std::pair<K, V> data_[N];
};

constexpr ConstexprMap<std::string_view, int, 3> message_types = {{
    {"quote", 1},
    {"trade", 2},
    {"order", 3}
}};

static_assert(message_types.at("quote") == 1);
```

---

## 五、高级技巧

### 5.1 CRTP（奇异递归模板模式）

```cpp
// 静态多态
template<typename Derived>
class Base {
public:
    void interface() {
        static_cast<Derived*>(this)->implementation();
    }
    
    void default_impl() {
        std::cout << "Default\n";
    }
};

class Derived1 : public Base<Derived1> {
public:
    void implementation() {
        std::cout << "Derived1\n";
    }
};

class Derived2 : public Base<Derived2> {
public:
    void implementation() {
        std::cout << "Derived2\n";
    }
};

// 零开销抽象
template<typename T>
void process(Base<T>& obj) {
    obj.interface();  // 静态分发，无虚函数开销
}

// HFT 应用：消息处理器
template<typename Derived>
class MessageHandler {
public:
    void handle(const Message& msg) {
        static_cast<Derived*>(this)->on_message(msg);
    }
    
protected:
    void log_message(const Message& msg) {
        // 公共日志逻辑
    }
};

class QuoteHandler : public MessageHandler<QuoteHandler> {
public:
    void on_message(const Message& msg) {
        log_message(msg);
        // 具体处理逻辑
    }
};
```

### 5.2 表达式模板

```cpp
// 延迟计算，避免临时对象
template<typename E>
class VectorExpr {
public:
    double operator[](size_t i) const {
        return static_cast<const E&>(*this)[i];
    }
    size_t size() const {
        return static_cast<const E&>(*this).size();
    }
};

class Vector : public VectorExpr<Vector> {
public:
    Vector(size_t n) : data_(n) {}
    
    double operator[](size_t i) const { return data_[i]; }
    double& operator[](size_t i) { return data_[i]; }
    size_t size() const { return data_.size(); }
    
    // 从表达式赋值
    template<typename E>
    Vector& operator=(const VectorExpr<E>& expr) {
        for (size_t i = 0; i < size(); i++) {
            data_[i] = expr[i];
        }
        return *this;
    }
    
private:
    std::vector<double> data_;
};

// 加法表达式
template<typename L, typename R>
class VectorAdd : public VectorExpr<VectorAdd<L, R>> {
public:
    VectorAdd(const L& l, const R& r) : left_(l), right_(r) {}
    
    double operator[](size_t i) const {
        return left_[i] + right_[i];
    }
    size_t size() const { return left_.size(); }
    
private:
    const L& left_;
    const R& right_;
};

template<typename L, typename R>
VectorAdd<L, R> operator+(const VectorExpr<L>& l, const VectorExpr<R>& r) {
    return VectorAdd<L, R>(static_cast<const L&>(l), static_cast<const R&>(r));
}

// 使用
Vector a(1000), b(1000), c(1000);
// 不创建临时 Vector，直接计算
c = a + b + a;  // 等价于 c[i] = a[i] + b[i] + a[i]
```

### 5.3 策略模式（编译期）

```cpp
// 分配策略
template<typename T>
struct DefaultAllocator {
    static T* allocate(size_t n) {
        return static_cast<T*>(::operator new(n * sizeof(T)));
    }
    static void deallocate(T* p) {
        ::operator delete(p);
    }
};

template<typename T>
struct PoolAllocator {
    static T* allocate(size_t n);
    static void deallocate(T* p);
};

// 锁策略
struct NoLock {
    void lock() {}
    void unlock() {}
};

struct SpinLock {
    void lock() { while (flag_.test_and_set(std::memory_order_acquire)); }
    void unlock() { flag_.clear(std::memory_order_release); }
private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;
};

// 组合策略
template<typename T,
         typename Allocator = DefaultAllocator<T>,
         typename Lock = NoLock>
class Container {
public:
    void add(const T& item) {
        lock_.lock();
        // 使用 Allocator 分配
        lock_.unlock();
    }
    
private:
    Lock lock_;
};

// 使用
Container<Order, PoolAllocator<Order>, SpinLock> thread_safe_container;
Container<Order> simple_container;  // 使用默认策略
```

---

## 六、面试常见问题

**Q: SFINAE 的工作原理？**

A: 当编译器实例化模板时，如果替换模板参数导致类型无效，该替换失败不会报错，而是将这个重载从候选集中移除。这允许基于类型特性选择不同的实现。

**Q: 何时使用 CRTP 而不是虚函数？**

| 考虑因素 | CRTP | 虚函数 |
|----------|------|--------|
| 性能 | 零开销 | 虚表查找 |
| 运行时多态 | 不支持 | 支持 |
| 代码大小 | 可能膨胀 | 较小 |
| 灵活性 | 编译期确定 | 运行时可变 |

**Q: 模板导致的代码膨胀如何处理？**

1. 将非类型相关代码提取到基类
2. 使用 `extern template` 减少实例化
3. 使用类型擦除（如 `std::function`）
4. 谨慎使用内联

---

## 相关文章

- [现代C++进阶-C++17与20特性](@/articles/hft/hft-50-现代C++进阶-C++17与20特性.md)
- [Cpp必知必会](@/articles/hft/hft-01-Cpp必知必会.md)
- [HFT笔试题-缓存友好编程](@/articles/hft/hft-30-HFT笔试题-缓存友好编程.md)
