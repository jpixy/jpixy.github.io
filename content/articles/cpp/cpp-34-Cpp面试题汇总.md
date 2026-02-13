+++
title = "C++ Interview Questions Summary"
date = 2026-01-21
weight = 34000
description = "C++面试题全面汇总，涵盖语言基础、模板、并发、STL、C++20/23新特性等200+高频题目"
[taxonomies]
tags = ["C++", "面试题", "汇总"]
+++

# 现代C++基础面试题
## 语言基础
1. **C++是什么类型的语言？**
    - C++是一种静态类型、编译型、多范式（面向对象、泛型、过程式）的编程语言。
2. **C++中的四种类型转换是什么？**
    - `static_cast`: 用于良性转换，如数值类型转换
    - `dynamic_cast`: 用于多态类型的向下转换，运行时检查
    - `const_cast`: 用于移除const/volatile属性
    - `reinterpret_cast`: 用于低级别的重新解释转换，不安全
3. **什么是RAII？**
    - RAII(Resource Acquisition Is Initialization)是一种利用对象生命周期管理资源的编程技术，资源在构造函数中获取，在析构函数中释放。
4. **什么是左值和右值？**
    - 左值(lvalue): 有持久状态的对象，可以取地址
    - 右值(rvalue): 临时对象，即将被销毁，不能取地址
5. **C++中的引用和指针有什么区别？**
    - 引用必须初始化且不能改变绑定对象，指针可以改变指向
    - 引用不能为null，指针可以为null
    - 引用使用更简洁，不需要解引用操作符

## 面向对象编程
6. **C++中的四种访问控制是什么？**
    - public: 任何地方都可访问
    - protected: 类和派生类可访问
    - private: 仅类内部可访问
    - (C++11新增)friend: 友元可访问
7. **什么是虚函数？如何实现多态？**
    - 虚函数是通过虚函数表(vtable)实现的，允许在运行时根据对象实际类型调用正确的函数实现。
    - 多态是通过基类指针/引用调用虚函数实现的。
8. **纯虚函数和抽象类是什么？**
    - 纯虚函数: `virtual void func() = 0;` 没有实现的虚函数
    - 抽象类: 包含至少一个纯虚函数的类，不能实例化
9. **构造函数和析构函数可以是虚函数吗？**
    - 构造函数不能是虚函数
    - 析构函数应该是虚函数(当类可能被继承时)
10. **什么是多重继承？菱形继承问题如何解决？**
    - 多重继承是一个类继承自多个基类
    - 菱形继承问题通过虚继承解决，使用`virtual`关键字继承共享的基类

## 现代C++特性
11. **auto关键字有什么用？**
    - auto用于自动类型推导，编译器根据初始化表达式推导变量类型
12. **什么是lambda表达式？**
    - lambda是匿名函数对象，语法: `[capture](params) -> ret { body }`
    - 可以捕获局部变量(值捕获或引用捕获)
13. **范围for循环是什么？**
    - 语法: `for(auto& item : container) { ... }`
    - 用于简化容器遍历
14. **nullptr和NULL有什么区别？**
    - nullptr是真正的空指针类型，有类型安全
    - NULL通常是0的宏定义，可能导致重载函数歧义
15. **什么是右值引用和移动语义？**
    - 右值引用: `T&&`，绑定到临时对象
    - 移动语义: 通过移动构造函数和移动赋值运算符高效转移资源
16. **完美转发是什么？**
    - 使用`std::forward`保持参数的值类别(lvalue/rvalue)
    - 通常与模板和引用折叠规则一起使用
17. **constexpr有什么用？**
    - 表示变量或函数可以在编译时求值
    - C++14放宽了constexpr函数的限制
18. **结构化绑定是什么？**
    - C++17特性，允许从元组或结构体解包多个变量
    - 语法: `auto [a, b] = getPair();`
19. **if和switch的初始化语句是什么？**
    - C++17允许在if和switch中使用初始化语句
    - 语法: `if(auto it = m.find(key); it != m.end()) { ... }`
20. **什么是三向比较运算符(太空船运算符)？**
    - C++20引入的`<=>`运算符
    - 自动生成比较操作(==, !=, <, <=, >, >=)

## 模板和泛型编程
21. **函数模板和类模板是什么？**
    - 函数模板: 生成函数的模板
    - 类模板: 生成类的模板
    - 使用`template<typename T>`语法定义
22. **模板特化和偏特化是什么？**
    - 特化: 为特定类型提供特殊实现
    - 偏特化: 为部分模板参数提供特殊实现
23. **什么是SFINAE？**
    - "Substitution Failure Is Not An Error"
    - 模板参数替换失败不会导致编译错误，而是从重载集中移除
24. **可变参数模板是什么？**
    - 接受任意数量模板参数的模板
    - 使用`...`语法定义和使用
25. **折叠表达式是什么？**
    - C++17特性，简化可变参数模板的展开
    - 语法: `(args op ...)`或`(... op args)`
26. **概念(Concepts)是什么？**
    - C++20特性，对模板参数的约束
    - 语法: `template<typename T> requires Concept<T>`

## 标准库
27. **智能指针有哪些？有什么区别？**
    - `unique_ptr`: 独占所有权，轻量级
    - `shared_ptr`: 共享所有权，引用计数
    - `weak_ptr`: 不增加引用计数的观察指针
28. **std::move和std::forward有什么区别？**
    - `std::move`无条件转换为右值
    - `std::forward`有条件转换(保持值类别)
29. **std::vector如何工作？**
    - 动态数组，连续内存存储
    - 自动扩容(通常2倍增长)
30. **std::map和std::unordered_map有什么区别？**
    - `std::map`: 红黑树实现，有序，O(log n)操作
    - `std::unordered_map`: 哈希表实现，无序，平均O(1)操作
31. **什么是迭代器失效？**
    - 容器修改导致迭代器指向无效内存
    - 常见于vector插入/删除，unordered容器rehash
32. **std::string_view是什么？**
    - C++17引入，字符串的非拥有视图
    - 轻量级，避免不必要的字符串拷贝
33. **std::optional是什么？**
    - C++17引入，表示可选值(可能有值或没有)
    - 比使用特殊值或指针更安全
34. **std::variant和std::any有什么区别？**
    - `std::variant`: 类型安全的联合体，已知类型集合
    - `std::any`: 可以存储任意类型，运行时类型检查
35. **std::function和lambda有什么区别？**
    - `std::function`是通用的函数包装器，可以存储任何可调用对象
    - lambda是匿名函数对象，有独特类型

## 内存管理
36. **new和malloc有什么区别？**
    - new是运算符，调用构造函数，返回类型指针
    - malloc是函数，只分配内存，返回void*
    - new失败抛出异常，malloc失败返回NULL
37. **堆和栈内存有什么区别？**
    - 栈: 自动管理，大小有限，快速分配
    - 堆: 手动管理，大小更大，分配较慢
38. **什么是内存对齐？为什么重要？**
    - 数据在内存中的起始地址是特定值的倍数
    - 重要原因: 某些架构要求对齐访问，否则性能下降或错误
39. **什么是placement new？**
    - 在已分配的内存上构造对象
    - 语法: `new (ptr) Type(args)`
40. **如何防止内存泄漏？**
    - 使用智能指针
    - RAII原则
    - 遵循谁分配谁释放的原则

## 并发和多线程
41. **std::thread如何使用？**
    - 创建线程: `std::thread t(func, args)`
    - 等待线程: `t.join()`
    - 分离线程: `t.detach()`
42. **互斥锁有哪些类型？**
    - `std::mutex`: 基本互斥锁
    - `std::recursive_mutex`: 可重入互斥锁
    - `std::timed_mutex`: 带超时的互斥锁
    - `std::shared_mutex`: 读写锁(C++17)
43. **什么是死锁？如何避免？**
    - 死锁: 多个线程互相等待对方释放资源
    - 避免方法: 固定锁获取顺序，使用RAII，避免嵌套锁
44. **std::atomic有什么用？**
    - 提供原子操作，无需显式锁
    - 保证操作的不可分割性
45. **什么是条件变量？**
    - 用于线程间通信，允许线程等待特定条件
    - 通常与互斥锁一起使用

## 异常处理
46. **C++异常处理机制是什么？**
    - `try`: 定义可能抛出异常的代码块
    - `catch`: 捕获和处理异常
    - `throw`: 抛出异常
47. **noexcept关键字有什么用？**
    - 指定函数不会抛出异常
    - 有助于编译器优化
48. **异常安全有哪几个级别？**
    - 基本保证: 异常发生后对象处于有效状态
    - 强保证: 操作要么完全成功，要么完全回滚
    - 不抛出保证: 操作保证不会抛出异常

## 其他
49. **inline关键字有什么用？**
    - 提示编译器将函数内联展开
    - 在头文件中定义函数时避免多重定义错误
50. **C++中的volatile关键字有什么用？**
    - 防止编译器优化对变量的访问
    - 常用于硬件寄存器和多线程共享变量(但不够，应使用原子操作)



## 语言特性深入
51. **什么是用户定义字面量(User-defined literals)？**
+ C++11允许定义自己的字面量后缀
+ 语法：`返回值类型 operator"" _后缀(参数)`
+ 示例：`auto size = 24_KB;`
52. **属性说明符(attribute)有哪些常见用法？**
+ `[[nodiscard]]`: 函数返回值不应被忽略
+ `[[deprecated]]`: 标记为已弃用
+ `[[fallthrough]]`: 允许switch case穿透
+ `[[maybe_unused]]`: 可能未使用的变量
53. **什么是constexpr if？**
+ C++17引入的编译时if语句
+ 语法：`if constexpr(条件)`
+ 在模板编程中特别有用，可以基于类型选择代码路径
54. **结构化绑定如何用于map遍历？**

```cpp
std::map<int, string> m;
for (const auto& [key, value] : m) {
    // 使用key和value
}
```

55. **什么是模板参数推导指南？**
+ C++17特性，指导编译器如何从构造函数推导模板参数
+ 示例：

```cpp
template<typename T> struct S { S(T) {} };
template<typename T> S(T) -> S<T>; // 推导指南
```

## 标准库深入
56. **std::span是什么？**
+ C++20引入，表示连续内存序列的视图
+ 轻量级，不拥有数据，比原始指针更安全
+ 可用于数组、vector等连续容器
57. **std::format有什么优势？**
+ C++20引入的类型安全字符串格式化
+ 比printf更安全，比stringstream更高效
+ 语法：`std::format("Hello {}!", "world")`
58. **std::jthread和std::thread有什么区别？**
+ C++20引入的`std::jthread`是"joining thread"
+ 析构时自动join，避免未join线程导致的程序终止
+ 支持协作式中断请求
59. **std::source_location是什么？**
+ C++20引入，获取源代码位置信息
+ 替代`__FILE__`和`__LINE__`宏的现代方式
+ 常用于日志系统
60. **std::expected是什么？**
+ C++23引入，表示可能包含值或错误的包装器
+ 比异常更轻量，比返回错误码更类型安全
+ 类似于Rust的Result类型

## 并发和多线程深入
61. **std::atomic的memory_order参数有哪些？**
+ `memory_order_relaxed`: 最宽松，仅保证原子性
+ `memory_order_consume`: 依赖顺序
+ `memory_order_acquire`: 获取操作
+ `memory_order_release`: 释放操作
+ `memory_order_acq_rel`: 获取-释放
+ `memory_order_seq_cst`: 顺序一致性(默认)
62. **什么是线程局部存储(thread_local)？**
+ 每个线程拥有该变量的独立副本
+ 语法：`thread_local int x;`
+ 类似于全局变量，但每个线程有自己的一份
63. **std::latch和std::barrier有什么区别？**
+ 都是C++20引入的线程同步机制
+ `latch`: 一次性屏障，计数器递减到0
+ `barrier`: 可重复使用的屏障，每阶段同步
64. **std::counting_semaphore有什么用？**
+ C++20引入的信号量实现
+ 控制对共享资源的并发访问数量
+ 比互斥锁更灵活的同步机制
65. **std::stop_token和std::stop_source是什么？**
+ C++20引入的线程停止机制
+ `stop_source`产生停止请求
+ `stop_token`检查是否收到停止请求
+ 比强制终止线程更安全

## 移动语义和完美转发深入
66. **什么是万能引用(universal reference)？**
+ 模板参数中的`T&&`可以绑定到左值和右值
+ 必须涉及类型推导才会成为万能引用
+ 示例：

```cpp
template<typename T>
void foo(T&& arg); // arg是万能引用
```

67. **引用折叠规则是什么？**
+ `T& &` → `T&`
+ `T& &&` → `T&`
+ `T&& &` → `T&`
+ `T&& &&` → `T&&`
+ 解释了万能引用和完美转发的工作原理
68. **如何实现移动构造函数？**

```cpp
class MyClass {
public:
    MyClass(MyClass&& other) noexcept 
        : data(std::move(other.data)) {}
private:
    std::vector<int> data;
};
```

69. **std::move_if_noexcept有什么用？**
+ 在可能的情况下优先使用noexcept移动操作
+ 如果移动构造函数不是noexcept，则返回左值引用
+ 有助于提供强异常安全保证
70. **什么是小字符串优化(SSO)？**
+ 许多std::string实现对小字符串直接存储在对象内部
+ 避免堆分配，提高小字符串性能
+ 典型实现中，16字节以下的字符串可能使用SSO

## 模板元编程
71. **什么是类型特征(type traits)？**
+ `<type_traits>`头文件提供的模板
+ 在编译时查询或修改类型属性
+ 示例：`std::is_integral<T>`, `std::remove_reference<T>`
72. **如何检测类是否有特定成员函数？**
+ 使用SFINAE或C++20概念
+ C++11示例：

```cpp
template<typename T>
auto has_foo(int) -> decltype(std::declval<T>().foo(), std::true_type{});
```

73. **什么是CRTP(奇异递归模板模式)？**
+ 派生类作为模板参数传递给基类
+ 用于静态多态
+ 示例：

```cpp
template<typename Derived>
class Base { /*...*/ };
class Derived : public Base<Derived> { /*...*/ };
```

74. **std::void_t有什么用？**
+ 用于SFINAE场景的类型别名
+ 定义：`template<typename...> using void_t = void;`
+ 可以检测类型表达式的有效性
75. **如何实现编译时字符串操作？**
+ 使用constexpr函数和模板元编程
+ C++17后可以利用`std::string_view`和`constexpr`函数
+ 示例：编译时字符串哈希

## 现代C++设计模式
76. **什么是策略模式在现代C++中的实现？**
+ 使用函数对象、lambda或`std::function`
+ 示例：

```cpp
template<typename Strategy>
void algorithm(Strategy&& strategy) {
    strategy.execute();
}
```

77. **如何用C++实现观察者模式？**
+ 使用`std::function`作为回调
+ 或使用信号/槽库
+ 现代实现可能结合`std::variant`和`std::visit`
78. **什么是类型擦除(type erasure)？**
+ 隐藏具体类型，只暴露接口
+ 实现方式：`std::function`、`std::any`或自定义包装器
+ 示例：`std::function`擦除了可调用对象的实际类型
79. **如何实现pimpl惯用法？**
+ 将实现细节放在实现类中，接口类只包含指向实现的指针
+ 减少编译依赖，提高编译速度
+ 示例：

```cpp
// 头文件
class MyClass {
    struct Impl;
    std::unique_ptr<Impl> pImpl;
public:
    MyClass();
    ~MyClass();
};
```

80. **什么是标签分发(tag dispatching)？**
+ 使用空结构体作为标签在编译时分发不同实现
+ 示例：

```cpp
struct tag1 {};
struct tag2 {};

void foo(tag1) { /* 实现1 */ }
void foo(tag2) { /* 实现2 */ }
```

## 性能相关
81. **什么是返回值优化(RVO)？**
+ 编译器优化，避免临时对象的构造和拷贝
+ 直接在调用者的栈帧上构造返回值
+ C++17对纯右值强制RVO
82. **NRVO是什么？**
+ Named Return Value Optimization
+ 对命名变量的返回值优化
+ 比RVO更复杂，不是所有编译器都能实现
83. **如何避免false sharing？**
+ 让频繁访问的变量位于不同的缓存行
+ 使用填充或`alignas`控制内存布局
+ 示例：`alignas(64) int threadLocalData;`
84. **std::launder有什么用？**
+ C++17引入，用于处理对象生命周期和指针优化问题
+ 在特定内存重用场景下避免未定义行为
+ 高级用法，一般代码很少需要
85. **什么是严格别名规则？**
+ 禁止通过不兼容类型的指针访问同一内存
+ 例外：`char*`和`std::byte*`可以别名任何类型
+ 违反规则会导致未定义行为

## 错误处理和调试
86. **std::terminate和std::abort有什么区别？**
+ `std::terminate`: 调用terminate handler，默认调用`std::abort`
+ `std::abort`: 立即终止程序，不执行任何清理
+ `terminate`更"温和"，可以设置自定义handler
87. **如何自定义terminate handler？**
+ 使用`std::set_terminate`函数
+ 示例：

```cpp
void my_terminate() { /*...*/ }
std::set_terminate(my_terminate);
```

88. **什么是std::uncaught_exceptions？**
+ 返回当前未捕获异常的数量
+ 比C++11的`uncaught_exception`更精确
+ 可用于析构函数中判断是否因异常退出
89. **如何实现栈展开时的资源清理？**
+ 使用RAII对象
+ 确保析构函数不会抛出异常
+ 示例：`std::lock_guard`在异常时释放锁
90. **什么是契约编程(Contracts)？**
+ C++20计划引入但推迟的特性
+ 前置条件、后置条件和断言的高级形式
+ 目前可通过GSL或库模拟

## C++20/23新特性
91. **std::coroutine是什么？**
+ C++20引入的协程支持
+ 三种协程类型：生成器、异步任务、惰性计算
+ 需要手动编写promise_type等支持代码
92. **什么是三路比较运算符(<=>)？**
+ 返回`std::strong_ordering`等类型
+ 编译器可自动生成==, !=, <, <=, >, >=
+ 示例：

```cpp
auto operator<=>(const MyClass&) const = default;
```

93. **std::ranges有什么优势？**
+ 更简洁的范围操作语法
+ 惰性求值，组合性强
+ 示例：`auto even = std::views::filter(is_even);`
94. **std::format如何使用？**
+ 类型安全的格式化库
+ 示例：`std::format("{} {:02d}", "value", 5)`
+ 支持位置参数、格式说明符等
95. **什么是consteval函数？**
+ C++20引入，函数必须在编译时求值
+ 比`constexpr`更严格，不允许运行时调用
+ 用于强制编译时计算

## 跨语言交互
96. **如何从C++调用C代码？**
+ 使用`extern "C"`链接说明
+ 示例：

```cpp
extern "C" {
    #include "clib.h"
}
```

97. **C++如何与Python交互？**
+ 使用Python C API
+ 或使用pybind11等绑定库
+ 或通过C接口间接交互
98. **什么是ABI兼容性？**
+ 二进制接口兼容性
+ 影响不同编译器版本生成的代码能否互操作
+ C++的ABI稳定性较差，C更稳定
99. **如何导出C++接口供其他语言使用？**
+ 提供纯虚接口类
+ 或提供C风格包装函数
+ 或使用SWIG等工具自动生成绑定
100. **什么是PIMPL惯用法的跨语言优势？**  
- 隐藏C++实现细节  
- 保持ABI稳定性  
- 减少头文件依赖，便于跨语言调用









# 现代C++高级知识面试题
## 模板元编程与编译期计算
1. **什么是SFINAE？如何利用它进行模板特化？**
    - SFINAE(Substitution Failure Is Not An Error)指模板参数替换失败不会导致编译错误，而是从候选集中移除
    - 利用示例：

```cpp
template<typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
void foo(T t) { /*...*/ }
```

2. **如何实现编译期字符串哈希？**

```cpp
constexpr size_t hash_str(const char* s, size_t h = 0) {
    return *s ? hash_str(s+1, (h * 131) + *s) : h;
}
```

3. **什么是类型萃取(Type Traits)？实现一个判断类是否有特定成员的traits**

```cpp
template<typename T, typename = void>
struct has_foo : std::false_type {};

template<typename T>
struct has_foo<T, std::void_t<decltype(std::declval<T>().foo())>> 
    : std::true_type {};
```

4. **解释模板参数包展开的几种方式**
    - 直接展开：`func(args...)`
    - 折叠表达式(C++17)：`(args + ...)`
    - 递归展开：通过递归模板函数
    - 初始化列表展开：`{(func(args), 0)...}`
5. **如何实现编译期排序算法？**
    - 使用constexpr函数和模板元编程
    - 结合std::array和constexpr lambda(C++17)
    - 示例：编译期快速排序

## 移动语义与完美转发
6. **解释万能引用和完美转发的工作原理**
    - 万能引用：`T&&`在模板推导时可绑定到左/右值
    - 完美转发：`std::forward`保持参数原始值类别
    - 依赖引用折叠规则：
        * `T& &` → `T&`
        * `T&& &` → `T&`
        * `T& &&` → `T&`
        * `T&& &&` → `T&&`
7. **为什么移动构造函数通常要标记为noexcept？**
    - STL容器在重新分配内存时，如果移动构造函数不是noexcept，会使用拷贝而非移动
    - 保证强异常安全的需要
    - 例如std::vector的push_back操作
8. **实现一个带有移动语义的资源管理类**

```cpp
class ResourceHolder {
    int* resource;
public:
    ResourceHolder(int* r) : resource(r) {}
    ~ResourceHolder() { delete resource; }
    
    // 移动构造函数
    ResourceHolder(ResourceHolder&& other) noexcept 
        : resource(other.resource) {
        other.resource = nullptr;
    }
    
    // 移动赋值运算符
    ResourceHolder& operator=(ResourceHolder&& other) noexcept {
        if(this != &other) {
            delete resource;
            resource = other.resource;
            other.resource = nullptr;
        }
        return *this;
    }
};
```

9. **std::forward和std::move的区别是什么？**
    - `std::move`无条件转换为右值
    - `std::forward`有条件转换，保持值类别
    - `std::move`用于转移语义，`std::forward`用于完美转发
10. **什么是小对象优化(Small Object Optimization)？如何实现？**
    - 小对象直接存储在容器内部，避免堆分配
    - 实现方式：使用union或直接缓冲区
    - 示例：std::string的小字符串优化

## 并发与多线程高级主题
11. **解释C++内存模型和原子操作的6种内存顺序**
    - memory_order_relaxed: 仅保证原子性
    - memory_order_consume: 数据依赖顺序
    - memory_order_acquire: 获取操作，防止后续读/写重排到前面
    - memory_order_release: 释放操作，防止前面读/写重排到后面
    - memory_order_acq_rel: 获取-释放
    - memory_order_seq_cst: 顺序一致性(默认)
12. **如何实现无锁队列？**
    - 使用原子操作和CAS(Compare-And-Swap)
    - 处理ABA问题(可通过标记指针或版本号)
    - 示例：基于链表的无锁队列实现
13. **什么是虚假唤醒(Spurious Wakeup)？如何避免？**

```cpp
std::unique_lock<std::mutex> lock(mtx);
while(!condition) {
    cv.wait(lock);
}
```

    - 线程可能在没有通知的情况下从条件变量等待中唤醒
    - 避免方式：始终在while循环中检查条件
14. **解释线程池的实现原理**
    - 预先创建一组工作线程
    - 任务队列存储待执行任务
    - 使用条件变量同步任务分配
    - 示例：基于std::function和std::future的线程池
15. **什么是RCU(Read-Copy-Update)模式？如何实现？**
    - 读写并发数据结构的一种方式
    - 读者无锁访问，写者复制修改后原子替换
    - 需要垃圾回收机制处理旧副本

## 异常安全与RAII
16. **解释三种异常安全保证**
    - 基本保证：异常发生后对象处于有效状态
    - 强保证：操作要么完全成功，要么完全回滚(事务性)
    - 不抛出保证：操作承诺不抛出异常
17. **如何实现强异常安全的swap操作？**

```cpp
class MyClass {
    int* data;
public:
    friend void swap(MyClass& a, MyClass& b) noexcept {
        using std::swap;
        swap(a.data, b.data); // 仅交换指针，不会失败
    }
};
```

18. **什么是RAII？给出5个标准库中的RAII例子**
    - 资源获取即初始化(Resource Acquisition Is Initialization)
    - 例子：
        1. std::unique_ptr
        2. std::lock_guard
        3. std::fstream
        4. std::thread(joinable资源)
        5. std::vector(内存资源)
19. **如何处理构造函数中的异常？**
    - 如果构造函数抛出异常，析构函数不会被调用
    - 需要在构造函数中捕获异常并清理已分配资源
    - 更好的方式：使用RAII成员管理资源
20. **实现一个作用域守卫(Scope Guard)**

```cpp
template<typename F>
class ScopeGuard {
    F f;
    bool active;
public:
    ScopeGuard(F f) : f(std::move(f)), active(true) {}
    ~ScopeGuard() { if(active) f(); }
    void dismiss() { active = false; }
};
```

## 标准库深入
21. **std::unordered_map的哈希冲突解决策略是什么？**
    - 标准未规定具体实现，但通常使用链地址法
    - 每个桶是一个链表或动态数组
    - C++11要求平均时间复杂度为O(1)
22. **如何自定义std::unordered_map的哈希函数？**

```cpp
struct MyHash {
    size_t operator()(const MyKey& k) const {
        return std::hash<int>()(k.id);
    }
};
std::unordered_map<MyKey, Value, MyHash> myMap;
```

23. **std::function的实现原理是什么？**
    - 使用类型擦除技术
    - 通常包含一个小对象优化缓冲区
    - 通过虚函数多态调用存储的可调用对象
24. **std::variant如何实现类型安全的联合？**
    - 存储当前活动类型的索引
    - 使用对齐存储(aligned_storage)保存可能的最大类型
    - 通过访问者模式或std::visit安全访问
25. **std::any的实现原理是什么？**
    - 类型擦除技术
    - 包含一个小对象优化缓冲区
    - 使用虚函数管理存储的对象

## 设计模式与惯用法
26. **如何用现代C++实现观察者模式？**

```cpp
class Observer {
public:
    virtual ~Observer() = default;
    virtual void update() = 0;
};

class Subject {
    std::vector<std::weak_ptr<Observer>> observers;
public:
    void attach(std::weak_ptr<Observer> obs) {
        observers.push_back(obs);
    }
    void notify() {
        for(auto& wobs : observers) {
            if(auto obs = wobs.lock()) {
                obs->update();
            }
        }
    }
};
```

27. **解释CRTP(奇异递归模板模式)及其应用**
    - 派生类作为模板参数传递给基类
    - 用于静态多态
    - 示例：

```cpp
template<typename Derived>
class Base {
public:
    void interface() {
        static_cast<Derived*>(this)->implementation();
    }
};

class Derived : public Base<Derived> {
public:
    void implementation() { /*...*/ }
};
```

28. **如何实现类型擦除(Type Erasure)？**
    - 通过继承和模板组合
    - 示例：类似std::function的实现
    - 外部接口类持有内部模板化实现类的指针
29. **什么是策略模式在现代C++中的最佳实现？**
    - 使用模板策略参数
    - 或使用std::function作为运行时策略
    - 示例：

```cpp
template<typename Strategy>
class Context {
    Strategy strategy;
public:
    void execute() { strategy(); }
};
```

30. **解释PIMPL惯用法的优缺点**
    - 优点：
        1. 减少编译依赖
        2. 保持ABI稳定性
        3. 隐藏实现细节
    - 缺点：
        1. 额外的间接访问开销
        2. 需要额外的堆分配

## C++20/23新特性深入
31. **协程的工作原理是什么？**
    - 通过编译器变换实现挂起/恢复
    - 关键组件：
        1. promise_type
        2. coroutine_handle
        3. awaiter对象
    - 三种基本模式：生成器、异步任务、惰性计算
32. **概念(Concepts)如何约束模板参数？**

```cpp
template<typename T>
concept Integral = std::is_integral_v<T>;

template<Integral T>
void foo(T t) { /*...*/ }
```

33. **三路比较运算符(<=>)如何自动生成比较操作？**
    - 编译器根据<=>结果自动生成==, !=, <, <=, >, >=
    - 返回类型：
        * std::strong_ordering
        * std::weak_ordering
        * std::partial_ordering
34. **std::format相比传统格式化有哪些优势？**
    - 类型安全
    - 性能更好(编译期解析格式字符串)
    - 更灵活的格式控制
    - 本地化支持
35. **std::ranges如何改进算法使用？**
    - 更简洁的语法
    - 惰性求值
    - 可组合性
    - 示例：

```cpp
auto even = std::views::filter([](int i){return i%2==0;});
for(int i : vec | even) { /*...*/ }
```

## 性能优化
36. **什么是缓存友好(Cache-friendly)设计？**
    - 提高数据局部性
    - 顺序访问模式
    - 紧凑数据结构
    - 避免false sharing
37. **如何避免false sharing？**
    - 让频繁访问的变量位于不同缓存行
    - 使用填充或alignas
    - 示例：

```cpp
struct alignas(64) ThreadData {
    int counter;
    char padding[64 - sizeof(int)];
};
```

38. **解释热/冷代码分割原理**
    - 热代码：频繁执行的代码
    - 冷代码：很少执行的代码
    - 分割到不同编译单元帮助优化
    - 使用`__attribute__((hot))`和`__attribute__((cold))`
39. **什么是分支预测提示？如何使用？**
    - `__builtin_expect`或`[[likely]]`/`[[unlikely]]`(C++20)
    - 帮助编译器优化分支
    - 示例：

```cpp
if (error) [[unlikely]] {
    // 错误处理
}
```

40. **如何优化虚函数调用？**
    - 使用final类或方法
    - 使用CRTP替代动态多态
    - 虚函数内联(通过LTO或特定编译器优化)

## 高级模板技术
41. **如何检测一个类型是否可调用？**

```cpp
template<typename T, typename = void>
struct is_callable : std::false_type {};

template<typename T>
struct is_callable<T, std::void_t<decltype(std::declval<T>()())>> 
    : std::true_type {};
```

42. **实现一个编译期类型列表(Type List)**

```cpp
template<typename... Ts>
struct TypeList {};

template<typename List>
struct Front;

template<typename Head, typename... Tail>
struct Front<TypeList<Head, Tail...>> {
    using type = Head;
};
```

43. **什么是表达式模板(Expression Templates)？**
    - 延迟表达式求值的技术
    - 用于线性代数库等场景
    - 示例：`Matrix C = A + B`不产生临时对象
44. **如何实现编译期字符串操作？**
    - 结合constexpr和模板
    - C++17后可用std::string_view
    - 示例：编译期字符串连接
45. **解释标签分发(Tag Dispatching)技术**
    - 使用空结构体作为标签选择不同实现
    - 示例：

```cpp
struct parallel_tag {};
struct sequential_tag {};

template<typename Tag>
void algo_impl(Tag);

void algo() {
    algo_impl(std::conditional_t<use_parallel, parallel_tag, 
                                sequential_tag>{});
}
```

## 内存模型与低级操作
46. **什么是严格别名规则(Strict Aliasing)？**
    - 禁止通过不兼容类型的指针访问同一内存
    - 例外：char*, std::byte*和原类型可以别名
    - 违反会导致未定义行为
47. **std::launder在什么场景下使用？**
    - 对象生命周期和指针优化场景
    - 示例：在已存在对象的存储中重用内存
    - 高级用法，一般代码很少需要
48. **如何实现自定义内存分配器？**
    - 满足Allocator概念要求
    - 提供allocate/deallocate方法
    - 示例：内存池分配器
49. **什么是placement new？使用场景？**
    - 在已分配内存上构造对象
    - 语法：`new (ptr) T(args)`
    - 使用场景：
        1. 自定义内存管理
        2. 对象池
        3. 非默认对齐内存
50. **解释std::pmr(Polymorphic Memory Resources)**
    - C++17引入的多态内存分配器框架
    - 提供多种内存资源：
        1. monotonic_buffer_resource
        2. synchronized_pool_resource
        3. unsynchronized_pool_resource

## 并发模式
51. **什么是双重检查锁定模式？现代C++如何实现？**
    - 传统方式：

```cpp
if(!ptr) {
    std::lock_guard<std::mutex> lock(mtx);
    if(!ptr) {
        ptr = new T;
    }
}
```

    - 现代方式：使用std::call_once或原子操作
52. **如何实现无锁栈？**
    - 基于链表的实现
    - 使用原子操作和CAS
    - 处理ABA问题
53. **什么是发布-消费(Release-Consume)内存顺序？**
    - 比acquire-release更宽松
    - 仅保证数据依赖顺序
    - C++17后不建议使用，应改用acquire-release
54. **解释读写锁的实现原理**
    - 多个读者或单个写者
    - 实现方式：
        1. 基于条件变量
        2. 基于原子操作的状态机
    - C++14提供std::shared_timed_mutex
    - C++17提供std::shared_mutex
55. **什么是顺序锁(Seqlock)？如何实现？**
    - 读者不阻塞写者
    - 基于版本计数器
    - 读者检查计数器是否变化
    - 适合读多写少且读者能容忍过时数据

## 异常处理高级主题
56. **std::exception_ptr有什么用？**
    - 跨线程传递异常
    - 捕获并存储异常供以后处理
    - 示例：

```cpp
std::exception_ptr eptr;
try { /*...*/ }
catch(...) { eptr = std::current_exception(); }
```

57. **如何实现异常安全的复制赋值运算符？**

```cpp
class MyClass {
    Data* data;
public:
    MyClass& operator=(const MyClass& other) {
        MyClass temp(other); // 可能抛出
        swap(*this, temp);   // 不会抛出
        return *this;
    }
};
```

    - 复制交换惯用法
58. **什么是异常中立(Exception Neutral)？**
    - 函数不直接处理异常，而是传播给调用者
    - 同时保证资源不泄漏
    - 通常通过RAII实现
59. **std::nested_exception有什么用？**
    - 嵌套异常处理
    - 捕获一个异常时抛出另一个异常
    - 保留原始异常信息
60. **如何实现异常安全的资源管理？**
    - RAII是核心原则
    - 确保资源类：
        1. 正确实现移动语义
        2. 析构函数不抛出异常
        3. 提供交换操作

## 元编程与反射
61. **C++20概念(Concepts)如何简化模板代码？**
    - 更清晰的错误消息
    - 减少SFINAE复杂度
    - 示例：

```cpp
template<typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::same_as<T>;
};
```

62. **如何检测类的成员变量？**

```cpp
template<typename T, typename = void>
struct has_member_x : std::false_type {};

template<typename T>
struct has_member_x<T, std::void_t<decltype(T::x)>> 
    : std::true_type {};
```

63. **什么是constexpr求值上下文？**
    - 编译期求值的表达式
    - constexpr函数中所有操作必须在编译期可求值
    - C++20放宽了constexpr函数中的限制
64. **如何实现编译期多态？**
    - 基于标签分发
    - 基于if constexpr
    - 基于concepts(C++20)
65. **解释std::is_detected惯用法**
    - 检测类型表达式的有效性
    - 实现：

```cpp
template<typename...> using void_t = void;

template<typename, template<typename> typename, typename = void_t<>>
struct is_detected : std::false_type {};

template<typename T, template<typename> typename Op>
struct is_detected<T, Op, void_t<Op<T>>> : std::true_type {};
```

## 高级标准库特性
66. **std::optional如何实现？**
    - 包含一个标志表示是否有值
    - 使用对齐存储保存可能的值
    - 手动管理对象生命周期
67. **std::variant的访问模式有哪些？**
    - std::get<Index/TYPE>
    - std::get_if
    - std::visit + 访问者模式
    - 结构化绑定(C++17)
68. **std::any的小对象优化如何工作？**
    - 小对象直接存储在any内部缓冲区
    - 大对象通过堆分配
    - 典型实现：3个指针大小的缓冲区
69. **std::string_view的危险点是什么？**
    - 不管理生命周期
    - 可能悬垂引用
    - 不保证空终止(与C字符串互操作需小心)
70. **std::function的类型擦除成本是什么？**
    - 动态内存分配(除非小对象优化)
    - 虚函数调用开销
    - 通常比直接调用慢2-3倍

## 系统编程
71. **如何实现跨平台的内存映射文件？**
    - Windows: CreateFileMapping/MapViewOfFile
    - POSIX: mmap/munmap
    - 封装为RAII类
72. **什么是VDSO(Virtual Dynamic Shared Object)？**
    - 内核提供的用户空间共享库
    - 加速系统调用(如clock_gettime)
    - 无需上下文切换
73. **如何实现高性能日志系统？**
    - 无锁队列缓冲日志消息
    - 后台线程处理I/O
    - 批量写入减少系统调用
    - 双缓冲技术
74. **解释零拷贝技术**
    - 避免数据在内核和用户空间之间复制
    - 技术：
        1. 内存映射文件
        2. sendfile
        3. splice
        4. DMA
75. **什么是io_uring？如何利用它提高I/O性能？**
    - Linux 5.1引入的异步I/O接口
    - 减少系统调用和上下文切换
    - 提交和完成队列分离
    - 支持轮询模式

## 调试与性能分析
76. **如何检测内存泄漏？**
    - 工具：
        1. Valgrind
        2. AddressSanitizer
        3. 重载new/delete
    - 智能指针减少泄漏风险
77. **什么是ASAN(AddressSanitizer)？**
    - 内存错误检测工具
    - 检测：
        1. 越界访问
        2. 使用释放内存
        3. 内存泄漏
    - 运行时开销约2x
78. **如何分析C++程序性能瓶颈？**
    - 工具：
        1. perf
        2. VTune
        3. gprof
    - 关注：
        1. 热点函数
        2. 缓存命中率
        3. 分支预测失败
79. **什么是RVO和NRVO？如何确保它们生效？**
    - 返回值优化(Return Value Optimization)
    - 命名返回值优化(Named RVO)
    - 确保方式：
        1. 返回局部对象
        2. 避免复杂控制流
        3. C++17强制RVO
80. **如何调试多线程问题？**
    - 工具：
        1. ThreadSanitizer
        2. gdb多线程支持
        3. 日志记录
    - 技术：
        1. 死锁检测
        2. 数据竞争检测
        3. 条件变量调试

## 高级语言特性
81. **什么是依赖注入？现代C++如何实现？**
    - 通过构造函数或模板参数注入依赖
    - 现代实现：
        1. 基于模板的策略模式
        2. 使用std::function
        3. 基于concepts的接口
82. **解释基于策略的设计**
    - 通过模板组合行为
    - 示例：

```cpp
template<typename StoragePolicy, typename LockingPolicy>
class Container : private StoragePolicy, private LockingPolicy {
    // 使用策略提供的方法
};
```

83. **什么是表达式模板(Expression Templates)？**
    - 延迟表达式求值
    - 用于线性代数库等
    - 示例：`Matrix C = A + B`不产生临时对象
84. **如何实现编译期反射？**
    - C++缺乏原生反射支持
    - 替代方案：
        1. 代码生成
        2. 基于宏的注册
        3. 模板元编程技巧
85. **什么是契约式设计(Design by Contract)？**
    - 前置条件、后置条件和不变式
    - C++20 Contracts提案(未纳入标准)
    - 可通过断言或库模拟

## 跨语言交互
86. **如何设计C++与Python的高效接口？**
    - 使用pybind11
    - 避免频繁跨语言调用
    - 批量数据传输
    - 类型转换优化
87. **什么是C++/CLI？使用场景？**
    - Microsoft的.NET互操作语言
    - 使用场景：托管/非托管代码桥接
    - 语法混合C++和C#
88. **如何实现C++与JavaScript的交互？**
    - WebAssembly编译
    - Emscripten工具链
    - JavaScript绑定生成
89. **解释C++与Rust的FFI交互**
    - extern "C"接口
    - 手动管理生命周期
    - 注意ABI兼容性
    - 使用cbindgen生成绑定
90. **如何设计稳定的C ABI接口？**
    - 使用PIMPL隐藏实现
    - 仅暴露C风格函数
    - 版本化接口
    - 谨慎处理内存所有权

## 编译器与工具链
91. **解释C++模块(Modules)的优势**
    - 替代头文件
    - 优点：
        1. 更快编译
        2. 更好的隔离
        3. 不再需要包含保护
    - 语法：`import module;`
92. **什么是LTO(Link Time Optimization)？**
    - 链接时优化
    - 跨编译单元内联
    - 全局代码分析
    - 增加编译时间但提升性能
93. **如何减少C++项目的编译时间？**
    - 前向声明替代包含
    - PIMPL惯用法
    - 预编译头文件
    - 模块(C++20)
    - 并行编译
94. **解释C++的ODR(One Definition Rule)**
    - 任何变量、函数、类等在程序中必须有且只有一个定义
    - 例外：内联函数/变量、模板、类定义可多次出现但必须相同
95. **什么是ABI兼容性？如何维护？**
    - 二进制接口兼容性
    - 维护方式：
        1. 避免破坏现有布局
        2. PIMPL惯用法
        3. 版本化接口

## 未来C++特性
96. **C++26可能引入哪些新特性？**
    - 反射提案
    - 模式匹配
    - 协程改进
    - 更多标准库模块
97. **什么是C++的静态反射？**
    - 编译期获取类型信息
    - 可能基于`std::meta::info`
    - 用例：序列化、调试、绑定生成
98. **解释模式匹配提案**
    - 类似Rust/Switch的匹配语法
    - 匹配类型和值
    - 示例：

```cpp
inspect(x) {
    i as int: cout << "int " << i;
    s as string: cout << "string " << s;
    _: cout << "unknown";
}
```

99. **什么是契约(Contracts)？为什么被推迟？**
    - 前置/后置条件和断言
    - 推迟原因：语法设计争议
    - 可能以简化形式加入
100. **C++的长期演进方向是什么？**  
- 提高安全性  
- 简化并发编程  
- 更好的抽象能力  
- 保持零开销抽象原则

---

## 相关文章

- [上一篇：Coroutines and User-Space Scheduling](@/articles/cpp/cpp-33-C++协程与用户态调度.md)
- [下一篇：Interview - Language Basics](@/articles/cpp/cpp-35-C++面试题-语言基础篇.md)
