+++
title = "07. Modern C++ Features"
date = 2026-01-19
description = "C++11/14/17/20核心特性：auto、智能指针、lambda、移动语义、并发"
[taxonomies]
tags = ["C++", "C++11", "现代C++"]
+++

## 自动类型推导

### auto关键字

```cpp
// 基本用法
auto i = 42;           // int
auto d = 3.14;         // double
auto s = "hello";      // const char*
auto v = std::vector<int>{1, 2, 3};  // std::vector<int>

// 迭代器简化
std::map<std::string, int> m;
auto it = m.begin();   // 代替 std::map<std::string, int>::iterator
```

### decltype

```cpp
int x = 0;
decltype(x) y = 1;     // int

// 与auto结合
auto func() -> decltype(x + y);  // 尾置返回类型

// C++14 decltype(auto)
decltype(auto) func() {
    return x;  // 返回类型与x一致
}
```

### 推导规则

```cpp
auto x = expr;          // 忽略引用和const
auto& x = expr;         // 保留引用
const auto& x = expr;   // 添加const引用
auto&& x = expr;        // 转发引用
```

---

## 智能指针

### unique_ptr

**独占所有权**：

```cpp
// 创建
std::unique_ptr<int> p1 = std::make_unique<int>(42);

// 不能复制
// std::unique_ptr<int> p2 = p1;  // 错误

// 可以移动
std::unique_ptr<int> p2 = std::move(p1);  // p1变为nullptr

// 自定义删除器
auto deleter = [](FILE* f) { fclose(f); };
std::unique_ptr<FILE, decltype(deleter)> file(fopen("test.txt", "r"), deleter);
```

### shared_ptr

**共享所有权**：

```cpp
// 创建
std::shared_ptr<int> p1 = std::make_shared<int>(42);

// 可以复制，引用计数+1
std::shared_ptr<int> p2 = p1;  // use_count = 2

// 引用计数
std::cout << p1.use_count();  // 2

// 离开作用域，引用计数-1，为0时释放
```

### weak_ptr

**不增加引用计数，解决循环引用**：

```cpp
std::shared_ptr<int> sp = std::make_shared<int>(42);
std::weak_ptr<int> wp = sp;

// 使用前需要lock
if (auto locked = wp.lock()) {
    // locked是shared_ptr
    std::cout << *locked;
}

// 检查是否过期
if (wp.expired()) {
    // 对象已销毁
}
```

### 循环引用问题

```cpp
struct Node {
    std::shared_ptr<Node> next;  // 改用weak_ptr解决
    std::shared_ptr<Node> prev;
};

// A->B, B->A 导致循环引用，永远不会释放
```

---

## Lambda表达式

### 基本语法

```cpp
[捕获列表](参数列表) -> 返回类型 { 函数体 }

// 简单示例
auto add = [](int a, int b) { return a + b; };
int result = add(3, 4);  // 7
```

### 捕获方式

```cpp
int x = 10, y = 20;

[x]      // 值捕获x
[&x]     // 引用捕获x
[=]      // 值捕获所有外部变量
[&]      // 引用捕获所有外部变量
[=, &x]  // 默认值捕获，x引用捕获
[&, x]   // 默认引用捕获，x值捕获
[this]   // 捕获this指针
[*this]  // C++17，值捕获*this
```

### mutable

```cpp
int x = 10;
auto f = [x]() mutable {
    x++;  // 允许修改值捕获的变量（不影响外部）
    return x;
};
```

### 泛型Lambda（C++14）

```cpp
auto add = [](auto a, auto b) {
    return a + b;
};
add(1, 2);      // int
add(1.5, 2.5);  // double
```

---

## 移动语义

### 左值与右值

```cpp
int x = 10;     // x是左值
int y = x + 5;  // x+5是右值

int& lref = x;      // 左值引用
int&& rref = 10;    // 右值引用
// int&& rref = x;  // 错误，x是左值
```

### 移动构造与移动赋值

```cpp
class String {
    char* data;
    size_t len;
public:
    // 移动构造
    String(String&& other) noexcept
        : data(other.data), len(other.len) {
        other.data = nullptr;
        other.len = 0;
    }
    
    // 移动赋值
    String& operator=(String&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = other.data;
            len = other.len;
            other.data = nullptr;
            other.len = 0;
        }
        return *this;
    }
};
```

### std::move

```cpp
std::vector<int> v1 = {1, 2, 3};
std::vector<int> v2 = std::move(v1);  // v1变为空
```

**std::move本身不移动任何东西，只是将左值转换为右值引用**。

### 完美转发

```cpp
template<typename T, typename... Args>
std::unique_ptr<T> make_unique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}
```

---

## 并发编程

### std::thread

```cpp
#include <thread>

void task(int id) {
    std::cout << "Thread " << id << std::endl;
}

std::thread t1(task, 1);
std::thread t2(task, 2);

t1.join();  // 等待完成
t2.join();
// 或 t1.detach();  // 分离
```

### std::mutex

```cpp
#include <mutex>

std::mutex mtx;
int counter = 0;

void increment() {
    std::lock_guard<std::mutex> lock(mtx);  // RAII锁
    counter++;
}

// C++17 更简洁
void increment() {
    std::scoped_lock lock(mtx);
    counter++;
}
```

### std::atomic

```cpp
#include <atomic>

std::atomic<int> counter{0};

void increment() {
    counter++;  // 原子操作
    counter.fetch_add(1);  // 等价
}
```

### std::async与std::future

```cpp
#include <future>

int compute() {
    return 42;
}

std::future<int> fut = std::async(std::launch::async, compute);
int result = fut.get();  // 阻塞等待结果
```

### std::condition_variable

```cpp
std::mutex mtx;
std::condition_variable cv;
bool ready = false;

// 生产者
{
    std::lock_guard<std::mutex> lock(mtx);
    ready = true;
}
cv.notify_one();

// 消费者
{
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock, []{ return ready; });
    // ready为true时继续
}
```

---

## 其他重要特性

### 范围for循环

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

for (int x : v) { }           // 值拷贝
for (int& x : v) { x *= 2; }  // 引用修改
for (const auto& x : v) { }   // 常量引用（推荐读取）
```

### nullptr

```cpp
int* p = nullptr;  // 代替NULL和0
```

### constexpr

```cpp
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

constexpr int result = factorial(5);  // 编译期计算
```

### 结构化绑定（C++17）

```cpp
std::map<std::string, int> m = {{"a", 1}, {"b", 2}};

for (const auto& [key, value] : m) {
    std::cout << key << ": " << value << std::endl;
}

auto [x, y] = std::make_pair(1, 2);
```

### std::optional（C++17）

```cpp
std::optional<int> find(int id) {
    if (found) return value;
    return std::nullopt;
}

auto result = find(42);
if (result) {
    std::cout << *result;
}
```

### std::variant（C++17）

```cpp
std::variant<int, double, std::string> v;
v = 42;
v = "hello";

std::visit([](auto&& arg) {
    std::cout << arg << std::endl;
}, v);
```

---

## 总结

| 特性 | 版本 | 用途 |
|------|------|------|
| auto/decltype | C++11 | 类型推导 |
| 智能指针 | C++11 | 自动内存管理 |
| Lambda | C++11 | 匿名函数 |
| 移动语义 | C++11 | 避免拷贝 |
| 线程库 | C++11 | 并发编程 |
| constexpr | C++11/14 | 编译期计算 |
| 结构化绑定 | C++17 | 解构赋值 |
| optional/variant | C++17 | 类型安全 |

现代C++让代码更安全、更高效、更简洁，是C++开发的必备知识。
