+++
title = "17.C++编译期计算与constexpr详解"
date = 2026-01-21
description = "深入剖析C++编译期计算、constexpr函数、consteval、编译期容器等核心概念，将运行时开销转移到编译期"
[taxonomies]
tags = ["C++", "constexpr", "编译期计算", "模板元编程", "性能优化"]
+++

## 概述

编译期计算是C++的强大特性，可以将运行时开销转移到编译期。在HFT系统中，预计算查找表、编译期字符串处理等技术可以消除运行时开销。

---

## 一、constexpr基础

### 1.1 constexpr变量

```cpp
// 编译期常量
constexpr int max_size = 1024;
constexpr double pi = 3.14159265358979;

// 编译期数组
constexpr int primes[] = {2, 3, 5, 7, 11, 13, 17, 19};

// 使用
static_assert(max_size == 1024, "max_size should be 1024");
```

### 1.2 constexpr函数

```cpp
// C++11: 函数体必须是单个return语句
constexpr int square_cpp11(int x) {
    return x * x;
}

// C++14: 允许复杂的函数体
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

// 编译期求值
constexpr int fact5 = factorial(5);  // 编译期计算：120
static_assert(fact5 == 120);

// 运行时也可调用
int runtime_value = 6;
int fact6 = factorial(runtime_value);  // 运行时计算
```

### 1.3 constexpr与模板

```cpp
// 编译期条件
template<typename T>
constexpr bool is_power_of_two(T n) {
    return n > 0 && (n & (n - 1)) == 0;
}

static_assert(is_power_of_two(64));
static_assert(!is_power_of_two(100));

// 用于模板参数
template<size_t N>
class FixedBuffer {
    static_assert(is_power_of_two(N), "N must be power of 2");
    char data_[N];
};

FixedBuffer<1024> buffer;  // OK
// FixedBuffer<1000> bad;  // 编译错误
```

---

## 二、C++17增强

### 2.1 constexpr if

```cpp
template<typename T>
auto process(T value) {
    if constexpr (std::is_integral_v<T>) {
        // 只对整数类型编译
        return value * 2;
    } else if constexpr (std::is_floating_point_v<T>) {
        // 只对浮点类型编译
        return value * 2.5;
    } else {
        // 其他类型
        return value;
    }
}

// 在编译期选择分支，未选择的分支不会被编译
```

### 2.2 constexpr lambda

```cpp
// C++17起lambda可以是constexpr
constexpr auto square = [](int x) { return x * x; };
static_assert(square(5) == 25);

// 显式标记
constexpr auto add = [](int a, int b) constexpr { return a + b; };
```

---

## 三、C++20增强

### 3.1 consteval：立即函数

```cpp
// consteval函数必须在编译期求值
consteval int compile_time_only(int x) {
    return x * x;
}

constexpr int a = compile_time_only(5);  // OK：编译期

int runtime_x = 5;
// int b = compile_time_only(runtime_x);  // 错误：必须编译期
```

### 3.2 constinit

```cpp
// 保证变量在编译期初始化，避免静态初始化顺序问题
constinit int global_value = 42;

// 可以修改，但必须静态初始化
void modify() {
    global_value = 100;  // OK
}
```

### 3.3 constexpr容器（C++20）

```cpp
#include <vector>
#include <string>

// C++20起std::vector可以在constexpr上下文使用
consteval std::vector<int> make_primes(int n) {
    std::vector<int> primes;
    for (int i = 2; i <= n; ++i) {
        bool is_prime = true;
        for (int p : primes) {
            if (p * p > i) break;
            if (i % p == 0) {
                is_prime = false;
                break;
            }
        }
        if (is_prime) primes.push_back(i);
    }
    return primes;
}

// C++20起std::string也支持
consteval std::string make_greeting(std::string_view name) {
    return "Hello, " + std::string(name) + "!";
}
```

---

## 四、编译期查找表

### 4.1 CRC表生成

```cpp
// 编译期生成CRC32表
constexpr uint32_t crc32_table_entry(uint8_t index) {
    uint32_t crc = index;
    for (int i = 0; i < 8; ++i) {
        crc = (crc >> 1) ^ (0xEDB88320 & (-(crc & 1)));
    }
    return crc;
}

template<size_t... I>
constexpr auto make_crc32_table(std::index_sequence<I...>) {
    return std::array<uint32_t, sizeof...(I)>{crc32_table_entry(I)...};
}

constexpr auto CRC32_TABLE = make_crc32_table(std::make_index_sequence<256>{});

// 使用编译期生成的表
constexpr uint32_t crc32(const char* data, size_t len) {
    uint32_t crc = 0xFFFFFFFF;
    for (size_t i = 0; i < len; ++i) {
        crc = CRC32_TABLE[(crc ^ data[i]) & 0xFF] ^ (crc >> 8);
    }
    return crc ^ 0xFFFFFFFF;
}

// 编译期计算CRC
constexpr uint32_t hash = crc32("Hello", 5);
```

### 4.2 数学函数表

```cpp
// 编译期sin表
constexpr double compile_time_sin(double x) {
    // 泰勒展开
    double result = x;
    double term = x;
    for (int i = 1; i < 20; ++i) {
        term *= -x * x / ((2 * i) * (2 * i + 1));
        result += term;
    }
    return result;
}

template<size_t N>
constexpr auto make_sin_table() {
    std::array<double, N> table{};
    for (size_t i = 0; i < N; ++i) {
        double angle = 2.0 * 3.14159265358979 * i / N;
        table[i] = compile_time_sin(angle);
    }
    return table;
}

constexpr auto SIN_TABLE = make_sin_table<1024>();

// 运行时快速查表
inline double fast_sin(double x) {
    // 归一化到[0, 2π)
    x = std::fmod(x, 2.0 * 3.14159265358979);
    if (x < 0) x += 2.0 * 3.14159265358979;
    
    size_t index = static_cast<size_t>(x * 1024 / (2.0 * 3.14159265358979));
    return SIN_TABLE[index % 1024];
}
```

---

## 五、编译期字符串

### 5.1 固定长度字符串

```cpp
template<size_t N>
struct FixedString {
    char data[N]{};
    
    constexpr FixedString(const char (&str)[N]) {
        for (size_t i = 0; i < N; ++i) {
            data[i] = str[i];
        }
    }
    
    constexpr size_t size() const { return N - 1; }
    constexpr char operator[](size_t i) const { return data[i]; }
};

// C++20起可以作为模板参数
template<FixedString S>
struct StringWrapper {
    static constexpr auto value = S;
};

// 编译期字符串处理
constexpr auto str = FixedString("Hello");
static_assert(str.size() == 5);
static_assert(str[0] == 'H');
```

### 5.2 编译期字符串哈希

```cpp
// FNV-1a哈希
constexpr uint64_t fnv1a_hash(const char* str, size_t len) {
    uint64_t hash = 14695981039346656037ULL;
    for (size_t i = 0; i < len; ++i) {
        hash ^= static_cast<uint64_t>(str[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

constexpr uint64_t operator""_hash(const char* str, size_t len) {
    return fnv1a_hash(str, len);
}

// 使用
constexpr uint64_t symbol_hash = "AAPL"_hash;

// 编译期switch
void processSymbol(uint64_t hash) {
    switch (hash) {
        case "AAPL"_hash: handleAAPL(); break;
        case "GOOG"_hash: handleGOOG(); break;
        case "MSFT"_hash: handleMSFT(); break;
    }
}
```

---

## 六、HFT应用场景

### 6.1 编译期协议解析

```cpp
// FIX协议标签映射
constexpr int FIX_TAG_SYMBOL = 55;
constexpr int FIX_TAG_PRICE = 44;
constexpr int FIX_TAG_QUANTITY = 38;

// 编译期标签到偏移量的映射
template<int Tag>
struct FixFieldOffset;

template<>
struct FixFieldOffset<FIX_TAG_SYMBOL> {
    static constexpr size_t offset = 0;
    static constexpr size_t size = 8;
};

template<>
struct FixFieldOffset<FIX_TAG_PRICE> {
    static constexpr size_t offset = 8;
    static constexpr size_t size = 8;
};

// 使用
template<int Tag>
const char* getField(const char* msg) {
    return msg + FixFieldOffset<Tag>::offset;
}
```

### 6.2 编译期配置

```cpp
// 编译期配置验证
struct TradingConfig {
    int max_orders_per_second;
    int max_position;
    double risk_limit;
    
    constexpr bool isValid() const {
        return max_orders_per_second > 0 &&
               max_orders_per_second <= 10000 &&
               max_position > 0 &&
               risk_limit > 0.0;
    }
};

constexpr TradingConfig config{1000, 100000, 0.02};
static_assert(config.isValid(), "Invalid trading config");
```

---

## 七、constexpr vs 模板元编程

### 7.1 对比

```cpp
// 模板元编程（C++98风格）
template<int N>
struct Factorial_TMP {
    static constexpr int value = N * Factorial_TMP<N - 1>::value;
};

template<>
struct Factorial_TMP<0> {
    static constexpr int value = 1;
};

// constexpr（现代C++）
constexpr int factorial_constexpr(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

// constexpr更易读、易调试
static_assert(Factorial_TMP<5>::value == 120);
static_assert(factorial_constexpr(5) == 120);
```

### 7.2 何时使用哪种

| 特性 | 模板元编程 | constexpr |
|------|------------|-----------|
| 可读性 | 低 | 高 |
| 调试 | 困难 | 容易 |
| 编译时间 | 可能更长 | 通常更短 |
| 适用场景 | 类型计算 | 值计算 |

---

## 总结

| 技术 | 版本 | 用途 |
|------|------|------|
| constexpr变量 | C++11 | 编译期常量 |
| constexpr函数 | C++11/14 | 编译期计算 |
| constexpr if | C++17 | 编译期条件分支 |
| consteval | C++20 | 强制编译期求值 |
| constinit | C++20 | 静态初始化保证 |

**HFT应用**：
1. 预计算查找表（CRC、数学函数）
2. 编译期字符串哈希
3. 配置验证
4. 协议字段映射
