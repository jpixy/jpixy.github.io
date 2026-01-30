+++
title = "51. Interview - Language Basics"
date = 2026-01-21
description = "C++语言基础面试题汇总，包括基本类型、引用与指针、const、类型转换、作用域等核心概念"
[taxonomies]
tags = ["C++", "面试题", "语言基础"]
+++

## 一、基本类型与大小

### Q1: 各种数据类型的大小是多少？

```cpp
// 32位和64位系统可能不同
sizeof(char)      // 1字节（保证）
sizeof(short)     // 至少2字节
sizeof(int)       // 至少2字节，通常4字节
sizeof(long)      // 至少4字节，64位Linux上8字节
sizeof(long long) // 至少8字节
sizeof(float)     // 通常4字节
sizeof(double)    // 通常8字节
sizeof(void*)     // 32位系统4字节，64位系统8字节

// 固定大小类型（推荐）
#include <cstdint>
int8_t, int16_t, int32_t, int64_t
uint8_t, uint16_t, uint32_t, uint64_t
```

### Q2: 什么是未定义行为（UB）？举例说明

```cpp
// 1. 有符号整数溢出
int x = INT_MAX;
x++;  // UB

// 2. 空指针解引用
int* p = nullptr;
*p = 42;  // UB

// 3. 数组越界
int arr[10];
arr[10] = 1;  // UB

// 4. 使用未初始化的变量
int x;
int y = x + 1;  // UB

// 5. 严格别名规则违反
float f = 1.0f;
int i = *(int*)&f;  // UB（某些情况）
```

---

## 二、引用与指针

### Q3: 引用和指针的区别？

| 特性 | 引用 | 指针 |
|------|------|------|
| 初始化 | 必须初始化 | 可以不初始化 |
| 空值 | 不能为空 | 可以为nullptr |
| 重新绑定 | 不能 | 可以 |
| 语法 | 使用`.` | 使用`->` |
| 大小 | sizeof不适用于引用* | 有大小(4/8字节) |
| 多级 | 没有多级引用 | 可以多级指针 |

*注：`sizeof(T&)` 返回 `sizeof(T)`，即被引用类型的大小。引用在底层通常实现为指针，但C++标准刻意隐藏了这个实现细节。

```cpp
int x = 10;
int& ref = x;    // 引用
int* ptr = &x;   // 指针

// 使用
ref = 20;        // x变为20
*ptr = 30;       // x变为30

// 引用本质上是const指针
// int& ref 类似于 int* const ptr
```

### Q4: 什么是悬垂引用/指针？

```cpp
// 悬垂指针
int* danglingPtr() {
    int local = 42;
    return &local;  // 返回局部变量地址
}  // local销毁，指针悬垂

// 悬垂引用
int& danglingRef() {
    int local = 42;
    return local;  // 返回局部变量引用
}  // local销毁，引用悬垂

// 使用后释放
int* p = new int(42);
delete p;
*p = 100;  // 悬垂指针使用，UB
```

---

## 三、const

### Q5: const的用法？

```cpp
// 1. 常量变量
const int x = 10;
// x = 20;  // 错误

// 2. 指针与const
const int* p1;      // 指向常量的指针（不能通过p1修改）
int const* p2;      // 同上
int* const p3 = &y; // 常量指针（不能修改p3本身）
const int* const p4 = &x;  // 两者都是常量

// 3. 引用与const
const int& ref = x;  // 常量引用
// ref = 20;  // 错误

// 4. 成员函数const
class MyClass {
    int getValue() const;  // 不修改成员变量
};

// 5. 返回值const
const std::string& getName() const;
```

### Q6: constexpr和const的区别？

```cpp
// const：运行时常量
const int runtime_const = getValue();  // 可以运行时确定

// constexpr：编译时常量
constexpr int compile_const = 42;  // 必须编译时确定

// constexpr函数
constexpr int square(int x) {
    return x * x;
}

constexpr int result = square(5);  // 编译时计算
int runtime_result = square(n);    // 运行时计算（如果n非constexpr）
```

---

## 四、类型转换

### Q7: C++的四种类型转换？

```cpp
// 1. static_cast：编译时类型转换
double d = 3.14;
int i = static_cast<int>(d);  // 显式转换

Base* base = static_cast<Base*>(derived);  // 向上转换

// 2. dynamic_cast：运行时类型检查（需要多态）
Base* base = getDerived();
Derived* derived = dynamic_cast<Derived*>(base);
if (derived) {
    // 转换成功
}

// 3. const_cast：移除const/volatile
const int* cp = &x;
int* p = const_cast<int*>(cp);

// 4. reinterpret_cast：位模式重新解释
int* ip = new int(42);
char* cp = reinterpret_cast<char*>(ip);
```

### Q8: 为什么不用C风格强制转换？

```cpp
// C风格转换会尝试多种转换，难以控制
int x = (int)3.14;           // 可能是static_cast
char* p = (char*)ip;         // 可能是reinterpret_cast
int* q = (int*)const_ptr;    // 可能是const_cast

// 问题：
// 1. 不明确意图
// 2. 可能进行危险转换
// 3. 难以搜索代码中的转换

// C++风格转换更安全，更明确
```

---

## 五、作用域与生命周期

### Q9: 什么是RAII？

```cpp
// RAII = Resource Acquisition Is Initialization
// 资源获取即初始化

class FileHandle {
    FILE* file_;
public:
    FileHandle(const char* path) : file_(fopen(path, "r")) {
        if (!file_) throw std::runtime_error("Cannot open file");
    }
    
    ~FileHandle() {
        if (file_) fclose(file_);  // 自动释放资源
    }
    
    // 禁止拷贝
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    
    FILE* get() { return file_; }
};

void useFile() {
    FileHandle file("test.txt");
    // 使用file...
}  // 自动调用析构函数，释放文件

// 标准库RAII示例：
// std::unique_ptr, std::shared_ptr - 内存管理
// std::lock_guard, std::unique_lock - 锁管理
// std::fstream - 文件管理
```

### Q10: static变量的生命周期？

```cpp
// 1. 全局static：程序启动到结束
static int global_static = 0;

// 2. 局部static：首次执行到程序结束
void func() {
    static int local_static = 0;  // 只初始化一次
    local_static++;
}

// 3. 类static成员：程序启动到结束
class MyClass {
    static int class_static;
};
int MyClass::class_static = 0;  // 类外定义

// 线程安全的局部static初始化（C++11起）
Singleton& getInstance() {
    static Singleton instance;  // 线程安全
    return instance;
}
```

---

## 六、其他基础

### Q11: 头文件保护的方法？

```cpp
// 方法1：include guard
#ifndef MY_HEADER_H
#define MY_HEADER_H

// 头文件内容

#endif

// 方法2：#pragma once（非标准但广泛支持）
#pragma once

// 头文件内容
```

### Q12: inline函数的作用？

```cpp
// 1. 建议编译器内联（可以忽略）
inline int square(int x) {
    return x * x;
}

// 2. 允许在多个编译单元定义（ODR例外）
// 头文件中的函数通常需要inline

// 3. C++17 inline变量
inline int global_var = 42;  // 可以在头文件中定义

// 注意：现代编译器自动决定是否内联
// inline关键字主要用于ODR目的
```

### Q13: auto关键字的用法？

```cpp
// 1. 类型推导
auto x = 42;         // int
auto y = 3.14;       // double
auto s = "hello";    // const char*
auto v = std::vector<int>{1, 2, 3};

// 2. 避免冗长类型
auto it = container.begin();  // 迭代器类型
auto result = complexFunction();

// 3. 泛型lambda
auto lambda = [](auto x, auto y) { return x + y; };

// 4. 尾置返回类型
auto add(int a, int b) -> int {
    return a + b;
}

// 注意事项
auto& ref = x;        // 引用
const auto& cref = x; // const引用
auto* ptr = &x;       // 指针
```

### Q14: nullptr和NULL的区别？

```cpp
// NULL：通常是0或(void*)0
#define NULL 0      // C++中
#define NULL ((void*)0)  // C中

// 问题：歧义
void foo(int);
void foo(int*);
foo(NULL);  // 调用哪个？可能调用foo(int)

// nullptr：类型安全的空指针
foo(nullptr);  // 明确调用foo(int*)

// nullptr是std::nullptr_t类型
```

---

## 面试技巧

1. **基本类型**：记住各类型的典型大小，但强调"取决于平台"
2. **指针vs引用**：理解本质区别，引用是const指针
3. **const**：理解"东西const"规则（const在*左边vs右边）
4. **类型转换**：知道何时用哪种，为什么C++转换更安全
5. **RAII**：这是C++资源管理的核心思想
