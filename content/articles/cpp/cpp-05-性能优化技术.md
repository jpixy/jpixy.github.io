+++
title = "05. Performance Optimization"
date = 2026-01-19
weight = 5000
description = "C++性能优化：编译器优化、内存优化、缓存友好、SIMD、性能分析工具"
[taxonomies]
tags = ["C++", "性能", "优化"]
+++

## 编译器优化

### 优化级别

```bash
g++ -O0 program.cpp  # 无优化（调试用）
g++ -O1 program.cpp  # 基本优化
g++ -O2 program.cpp  # 推荐优化级别
g++ -O3 program.cpp  # 激进优化（可能增加代码大小）
g++ -Os program.cpp  # 优化大小
g++ -Ofast program.cpp  # O3 + 不严格遵守标准的优化
```

### 帮助编译器优化

**内联**：
```cpp
inline int add(int a, int b) {
    return a + b;
}

// 强制内联（编译器可能忽略）
__attribute__((always_inline)) inline int add(int a, int b);
```

**const和constexpr**：
```cpp
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}
constexpr int result = factorial(10);  // 编译期计算
```

**restrict（C99/编译器扩展）**：
```cpp
void add(float* __restrict a, float* __restrict b, float* __restrict c, int n) {
    for (int i = 0; i < n; i++) {
        c[i] = a[i] + b[i];  // 编译器可以假设a,b,c不重叠
    }
}
```

**likely/unlikely（C++20）**：
```cpp
if (condition) [[likely]] {
    // 常见路径
} else [[unlikely]] {
    // 罕见路径
}
```

---

## 内存优化

### 避免不必要的拷贝

```cpp
// 差：拷贝
void process(std::vector<int> v);

// 好：常量引用
void process(const std::vector<int>& v);

// 好：移动语义
void consume(std::vector<int>&& v);
std::vector<int> data = ...;
consume(std::move(data));
```

### 预留容量

```cpp
std::vector<int> v;
v.reserve(1000);  // 预分配，避免多次扩容

for (int i = 0; i < 1000; i++) {
    v.push_back(i);  // 无需重新分配
}
```

### 小对象优化

**std::string SSO**：
```cpp
// 短字符串存储在栈上（通常<15字符）
std::string s = "hello";  // 无堆分配

// 长字符串才堆分配
std::string s = "very long string...";
```

### 内存池

```cpp
#include <memory_resource>

// 使用内存池
char buffer[10000];
std::pmr::monotonic_buffer_resource pool{buffer, sizeof(buffer)};
std::pmr::vector<int> v{&pool};

// 分配快速，无碎片
```

### 对齐

```cpp
alignas(64) int data[16];  // 缓存行对齐

struct alignas(64) CacheLinePadded {
    int value;
    char padding[60];  // 避免伪共享
};
```

---

## 缓存优化

### 缓存层次

```
L1 Cache: ~1-3 cycles, ~32KB
L2 Cache: ~10 cycles, ~256KB
L3 Cache: ~40 cycles, ~8MB
主内存:   ~200 cycles
```

### 数据局部性

**空间局部性**：
```cpp
// 好：连续访问
for (int i = 0; i < n; i++) {
    sum += arr[i];
}

// 差：跳跃访问
for (int i = 0; i < n; i += 16) {
    sum += arr[i];
}
```

**时间局部性**：
```cpp
// 差：多次遍历
for (int i = 0; i < n; i++) sum1 += arr[i];
for (int i = 0; i < n; i++) sum2 += arr[i] * 2;

// 好：单次遍历
for (int i = 0; i < n; i++) {
    sum1 += arr[i];
    sum2 += arr[i] * 2;
}
```

### 矩阵遍历

```cpp
// 差：列优先（C/C++是行优先存储）
for (int j = 0; j < cols; j++)
    for (int i = 0; i < rows; i++)
        matrix[i][j] = 0;

// 好：行优先
for (int i = 0; i < rows; i++)
    for (int j = 0; j < cols; j++)
        matrix[i][j] = 0;
```

### 避免伪共享

```cpp
// 差：不同核心写相邻变量，缓存行来回失效
struct {
    int counter1;  // 核心1写
    int counter2;  // 核心2写
} data;

// 好：填充到不同缓存行
struct {
    alignas(64) int counter1;
    alignas(64) int counter2;
} data;
```

---

## SIMD优化

### 自动向量化

```cpp
// 编译器可能自动向量化
void add(float* a, float* b, float* c, int n) {
    for (int i = 0; i < n; i++) {
        c[i] = a[i] + b[i];
    }
}

// 编译选项
// g++ -O3 -march=native -ftree-vectorize
```

### 手动SIMD

```cpp
#include <immintrin.h>

void add_simd(float* a, float* b, float* c, int n) {
    int i;
    for (i = 0; i + 8 <= n; i += 8) {
        __m256 va = _mm256_loadu_ps(&a[i]);
        __m256 vb = _mm256_loadu_ps(&b[i]);
        __m256 vc = _mm256_add_ps(va, vb);
        _mm256_storeu_ps(&c[i], vc);
    }
    // 处理剩余元素
    for (; i < n; i++) {
        c[i] = a[i] + b[i];
    }
}
```

### SIMD库

```cpp
// Eigen：线性代数
Eigen::VectorXf a, b, c;
c = a + b;  // 自动SIMD

// Highway：Google的跨平台SIMD库
```

---

## 分支优化

### 分支预测

```cpp
// 差：随机分支，预测失败率高
if (rand() % 2) { ... }

// 好：可预测的分支
if (i < n/2) { ... }  // 前半段总是true
```

### 无分支编程

```cpp
// 有分支
int max = (a > b) ? a : b;

// 无分支（某些情况更快）
int max = a ^ ((a ^ b) & -(a < b));

// 或使用std::max，编译器可能优化
```

### 查表替代分支

```cpp
// 有分支
int result;
switch (type) {
    case 0: result = a; break;
    case 1: result = b; break;
    case 2: result = c; break;
}

// 查表
int table[] = {a, b, c};
int result = table[type];
```

---

## 性能分析工具

### 计时

```cpp
#include <chrono>

auto start = std::chrono::high_resolution_clock::now();
// 代码
auto end = std::chrono::high_resolution_clock::now();

auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
std::cout << duration.count() << " us" << std::endl;
```

### perf

```bash
# 统计
perf stat ./program

# 采样
perf record ./program
perf report

# 热点分析
perf annotate
```

### Valgrind

```bash
# 缓存分析
valgrind --tool=cachegrind ./program

# 内存泄漏
valgrind --leak-check=full ./program
```

### Google Benchmark

```cpp
#include <benchmark/benchmark.h>

static void BM_VectorPush(benchmark::State& state) {
    for (auto _ : state) {
        std::vector<int> v;
        for (int i = 0; i < 1000; i++) {
            v.push_back(i);
        }
    }
}
BENCHMARK(BM_VectorPush);

BENCHMARK_MAIN();
```

---

## 常见优化模式

### 循环展开

```cpp
// 原始
for (int i = 0; i < n; i++) {
    sum += arr[i];
}

// 展开
for (int i = 0; i + 4 <= n; i += 4) {
    sum += arr[i] + arr[i+1] + arr[i+2] + arr[i+3];
}
```

### 循环交换

```cpp
// 差：内层循环步长大
for (int i = 0; i < m; i++)
    for (int j = 0; j < n; j++)
        a[j][i] = ...;

// 好：内层循环步长小
for (int j = 0; j < n; j++)
    for (int i = 0; i < m; i++)
        a[j][i] = ...;
```

### 计算外提

```cpp
// 差：重复计算
for (int i = 0; i < n; i++) {
    result += arr[i] * expensive_function();
}

// 好：外提
int factor = expensive_function();
for (int i = 0; i < n; i++) {
    result += arr[i] * factor;
}
```

---

## 总结

| 层面 | 优化点 |
|------|--------|
| 编译器 | 优化级别、内联、const |
| 内存 | 避免拷贝、预分配、内存池 |
| 缓存 | 数据局部性、避免伪共享 |
| SIMD | 自动向量化、手动SIMD |
| 分支 | 可预测分支、无分支编程 |
| 工具 | perf、valgrind、benchmark |

**优化原则**：
1. 先测量，后优化
2. 优化瓶颈，而非猜测
3. 保持代码可读性
4. 验证优化效果

---

## 相关文章

- [上一篇：Concurrency and Multithreading](@/articles/cpp/cpp-04-并发编程详解.md)
- [下一篇：STL Containers and Algorithms](@/articles/cpp/cpp-06-STL容器与算法.md)
