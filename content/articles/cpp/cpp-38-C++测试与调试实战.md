+++
title = "38.C++测试与调试实战"
date = 2026-01-21
description = "深入剖析C++测试框架和调试工具，包括GTest/GMock、Sanitizers、Valgrind、GDB高级技巧等"
[taxonomies]
tags = ["C++", "测试", "调试", "GTest", "Sanitizers", "Valgrind"]
+++

## 概述

高质量的测试和高效的调试是保证HFT系统可靠性的关键。本文详细介绍C++测试框架和调试工具的使用。

---

## 一、Google Test（GTest）

### 1.1 基本用法

```cpp
#include <gtest/gtest.h>

// 基本测试
TEST(MathTest, Addition) {
    EXPECT_EQ(2 + 2, 4);
    EXPECT_NE(2 + 2, 5);
    EXPECT_LT(1, 2);
    EXPECT_LE(1, 1);
    EXPECT_GT(2, 1);
    EXPECT_GE(2, 2);
}

// 浮点比较
TEST(MathTest, FloatingPoint) {
    EXPECT_FLOAT_EQ(1.0f, 1.0f);
    EXPECT_DOUBLE_EQ(1.0, 1.0);
    EXPECT_NEAR(1.0, 1.001, 0.01);
}

// 字符串比较
TEST(StringTest, Comparison) {
    std::string s = "Hello";
    EXPECT_EQ(s, "Hello");
    EXPECT_STREQ("Hello", "Hello");    // C字符串
    EXPECT_STRNE("Hello", "World");
}

// 异常测试
TEST(ExceptionTest, ThrowsException) {
    EXPECT_THROW(throwFunction(), std::runtime_error);
    EXPECT_ANY_THROW(throwFunction());
    EXPECT_NO_THROW(safeFunction());
}

// 布尔断言
TEST(BoolTest, Boolean) {
    EXPECT_TRUE(isValid());
    EXPECT_FALSE(isEmpty());
}
```

### 1.2 测试夹具（Test Fixture）

```cpp
class OrderBookTest : public ::testing::Test {
protected:
    OrderBook book;
    
    void SetUp() override {
        // 每个测试前调用
        book.addOrder({1, 100, 10, Side::BUY});
        book.addOrder({2, 101, 20, Side::SELL});
    }
    
    void TearDown() override {
        // 每个测试后调用
        book.clear();
    }
    
    // 辅助方法
    Order createOrder(int price, int qty) {
        return {nextId++, price, qty, Side::BUY};
    }
    
    int nextId = 100;
};

TEST_F(OrderBookTest, AddOrder) {
    EXPECT_EQ(book.bidCount(), 1);
    EXPECT_EQ(book.askCount(), 1);
}

TEST_F(OrderBookTest, MatchOrder) {
    auto match = book.match({3, 100, 5, Side::SELL});
    EXPECT_TRUE(match.has_value());
    EXPECT_EQ(match->quantity, 5);
}
```

### 1.3 参数化测试

```cpp
// 值参数化
class PrimeTest : public ::testing::TestWithParam<int> {};

TEST_P(PrimeTest, IsPrime) {
    int n = GetParam();
    EXPECT_TRUE(isPrime(n));
}

INSTANTIATE_TEST_SUITE_P(Primes, PrimeTest, 
    ::testing::Values(2, 3, 5, 7, 11, 13));

// 类型参数化
template<typename T>
class ContainerTest : public ::testing::Test {
protected:
    T container;
};

using ContainerTypes = ::testing::Types<std::vector<int>, std::deque<int>>;
TYPED_TEST_SUITE(ContainerTest, ContainerTypes);

TYPED_TEST(ContainerTest, IsEmptyInitially) {
    EXPECT_TRUE(this->container.empty());
}
```

---

## 二、Google Mock（GMock）

### 2.1 基本Mock

```cpp
#include <gmock/gmock.h>

// 接口定义
class IDatabase {
public:
    virtual ~IDatabase() = default;
    virtual bool connect(const std::string& host) = 0;
    virtual int query(const std::string& sql) = 0;
    virtual void disconnect() = 0;
};

// Mock类
class MockDatabase : public IDatabase {
public:
    MOCK_METHOD(bool, connect, (const std::string& host), (override));
    MOCK_METHOD(int, query, (const std::string& sql), (override));
    MOCK_METHOD(void, disconnect, (), (override));
};

// 使用Mock
TEST(ServiceTest, QueryData) {
    MockDatabase db;
    
    // 设置期望
    EXPECT_CALL(db, connect("localhost"))
        .WillOnce(::testing::Return(true));
    
    EXPECT_CALL(db, query("SELECT * FROM orders"))
        .WillOnce(::testing::Return(42));
    
    EXPECT_CALL(db, disconnect())
        .Times(1);
    
    // 测试代码
    Service service(&db);
    int result = service.fetchOrders();
    
    EXPECT_EQ(result, 42);
}
```

### 2.2 高级匹配器

```cpp
using ::testing::_;
using ::testing::Eq;
using ::testing::Ne;
using ::testing::Lt;
using ::testing::Gt;
using ::testing::HasSubstr;
using ::testing::StartsWith;
using ::testing::ElementsAre;

TEST(MatcherTest, Various) {
    MockDatabase db;
    
    // 任意参数
    EXPECT_CALL(db, query(_))
        .WillRepeatedly(::testing::Return(0));
    
    // 字符串匹配
    EXPECT_CALL(db, query(HasSubstr("SELECT")))
        .WillOnce(::testing::Return(10));
    
    // 组合匹配
    EXPECT_CALL(db, query(::testing::AllOf(
        StartsWith("SELECT"),
        HasSubstr("orders")
    ))).WillOnce(::testing::Return(5));
}
```

### 2.3 Action

```cpp
using ::testing::Return;
using ::testing::ReturnRef;
using ::testing::Invoke;
using ::testing::DoAll;
using ::testing::SetArgPointee;
using ::testing::SaveArg;

TEST(ActionTest, Various) {
    MockDatabase db;
    
    // 返回值序列
    EXPECT_CALL(db, query(_))
        .WillOnce(Return(1))
        .WillOnce(Return(2))
        .WillRepeatedly(Return(0));
    
    // 调用Lambda
    EXPECT_CALL(db, query(_))
        .WillOnce(Invoke([](const std::string& sql) {
            return static_cast<int>(sql.length());
        }));
    
    // 保存参数供后续验证
    std::string captured_sql;
    EXPECT_CALL(db, query(_))
        .WillOnce(DoAll(
            SaveArg<0>(&captured_sql),
            Return(1)
        ));
}

// SetArgPointee用于指针参数的Mock
class IService {
public:
    virtual bool getData(int id, std::string* output) = 0;
};

class MockService : public IService {
public:
    MOCK_METHOD(bool, getData, (int id, std::string* output), (override));
};

TEST(SetArgPointeeTest, Example) {
    MockService service;
    
    // 设置输出参数
    EXPECT_CALL(service, getData(1, _))
        .WillOnce(DoAll(
            SetArgPointee<1>("result_data"),
            Return(true)
        ));
}
```

---

## 三、Sanitizers

### 3.1 AddressSanitizer（ASan）

```bash
# 编译
g++ -fsanitize=address -g source.cpp -o app

# 检测问题：
# - 堆溢出
# - 栈溢出
# - 全局缓冲区溢出
# - 使用后释放
# - 双重释放
# - 内存泄漏
```

```cpp
// ASan能检测的问题示例
void heapOverflow() {
    int* arr = new int[10];
    arr[10] = 42;  // ASan报告：heap-buffer-overflow
    delete[] arr;
}

void useAfterFree() {
    int* p = new int(42);
    delete p;
    *p = 10;  // ASan报告：heap-use-after-free
}

void memoryLeak() {
    int* p = new int(42);
    // 忘记delete，ASan报告泄漏
}
```

### 3.2 ThreadSanitizer（TSan）

```bash
# 编译
g++ -fsanitize=thread -g source.cpp -o app -pthread

# 检测问题：
# - 数据竞争
# - 锁顺序问题
```

```cpp
// TSan能检测的问题
int counter = 0;

void dataRace() {
    std::thread t1([]{
        for (int i = 0; i < 1000; ++i) counter++;
    });
    std::thread t2([]{
        for (int i = 0; i < 1000; ++i) counter++;
    });
    t1.join();
    t2.join();
    // TSan报告：data race
}
```

### 3.3 UndefinedBehaviorSanitizer（UBSan）

```bash
# 编译
g++ -fsanitize=undefined -g source.cpp -o app

# 检测问题：
# - 有符号整数溢出
# - 空指针解引用
# - 数组越界
# - 未对齐访问
# - 除零
```

```cpp
// UBSan能检测的问题
void signedOverflow() {
    int x = INT_MAX;
    x++;  // UBSan报告：signed integer overflow
}

void nullDeref() {
    int* p = nullptr;
    *p = 42;  // UBSan报告：null pointer dereference
}
```

### 3.4 MemorySanitizer（MSan）

```bash
# 编译（仅Clang支持）
clang++ -fsanitize=memory -g source.cpp -o app

# 检测问题：
# - 读取未初始化内存
```

```cpp
void uninitializedRead() {
    int x;
    if (x > 0) {  // MSan报告：use of uninitialized value
        // ...
    }
}
```

---

## 四、Valgrind

### 4.1 Memcheck

```bash
# 运行
valgrind --leak-check=full --show-leak-kinds=all ./app

# 输出示例
# ==12345== 40 bytes in 1 blocks are definitely lost
# ==12345==    at 0x4C2E0EF: operator new(unsigned long)
# ==12345==    by 0x400A15: createObject() (main.cpp:10)
```

### 4.2 Callgrind（性能分析）

```bash
# 运行
valgrind --tool=callgrind ./app

# 生成文件：callgrind.out.<pid>

# 分析
callgrind_annotate callgrind.out.12345

# 可视化
kcachegrind callgrind.out.12345
```

### 4.3 Cachegrind（缓存分析）

```bash
# 运行
valgrind --tool=cachegrind ./app

# 输出
# D1  miss rate: 2.1%
# LLd miss rate: 0.3%

# 详细分析
cg_annotate cachegrind.out.12345
```

### 4.4 Helgrind（线程分析）

```bash
# 运行
valgrind --tool=helgrind ./app

# 检测：
# - 数据竞争
# - 死锁
# - 锁顺序问题
```

---

## 五、GDB高级技巧

### 5.1 基本命令

```bash
# 启动
gdb ./app
gdb --args ./app arg1 arg2

# 断点
break main                  # 函数
break file.cpp:42          # 文件行号
break *0x400a15            # 地址
break func if x > 10       # 条件断点

# 运行控制
run                        # 开始
continue (c)               # 继续
next (n)                   # 下一行
step (s)                   # 进入函数
finish                     # 完成当前函数
until 50                   # 运行到第50行

# 查看
print x                    # 打印变量
print/x x                  # 十六进制
print arr[0]@10           # 数组元素
info locals               # 局部变量
info args                 # 函数参数
backtrace (bt)            # 调用栈
```

### 5.2 高级功能

```bash
# 观察点
watch x                   # x改变时断下
rwatch x                  # x被读取时
awatch x                  # 读或写时

# 反向调试（需要record）
record
reverse-continue
reverse-step

# 多线程调试
info threads             # 列出线程
thread 2                 # 切换到线程2
set scheduler-locking on # 只运行当前线程

# 内存检查
x/10xb addr              # 10字节，十六进制
x/s addr                 # 字符串
x/i addr                 # 反汇编

# 修改内存
set x = 10
set *addr = 42
```

### 5.3 Core Dump分析

```bash
# 启用core dump
ulimit -c unlimited

# 分析
gdb ./app core
bt                       # 查看崩溃时的调用栈
frame 2                  # 切换到第2帧
info locals             # 查看局部变量
```

---

## 六、HFT调试策略

### 6.1 生产环境日志

```cpp
// 高性能日志
class FastLogger {
    char buffer_[BUFFER_SIZE];
    std::atomic<size_t> offset_{0};
    
public:
    template<typename... Args>
    void log(const char* fmt, Args... args) {
        // 无锁追加
        size_t pos = offset_.fetch_add(estimate_size(fmt, args...));
        size_t written = snprintf(buffer_ + pos, BUFFER_SIZE - pos, 
                                   fmt, args...);
        // 异步写入磁盘
    }
};
```

### 6.2 延迟注入

```cpp
// 调试模式下注入延迟点
#ifdef DEBUG
#define LATENCY_CHECKPOINT(name) \
    latencyTracker.checkpoint(name, rdtsc())
#else
#define LATENCY_CHECKPOINT(name)
#endif

void processOrder(const Order& order) {
    LATENCY_CHECKPOINT("parse_start");
    parse(order);
    LATENCY_CHECKPOINT("parse_end");
    
    LATENCY_CHECKPOINT("validate_start");
    validate(order);
    LATENCY_CHECKPOINT("validate_end");
}
```

---

## 总结

| 工具 | 用途 | 开销 | 推荐场景 |
|------|------|------|----------|
| GTest | 单元测试 | 无 | 所有项目 |
| GMock | Mock测试 | 无 | 接口测试 |
| ASan | 内存错误 | 2-3x | 开发/CI |
| TSan | 数据竞争 | 5-15x | 并发代码 |
| UBSan | 未定义行为 | 1.5x | 开发/CI |
| Valgrind | 内存分析 | 10-50x | 深度分析 |
| GDB | 调试 | 无 | 所有场景 |

**最佳实践**：
1. 所有代码必须有单元测试
2. CI中启用ASan/UBSan
3. 定期运行TSan检查并发问题
4. 使用Mock隔离测试外部依赖
