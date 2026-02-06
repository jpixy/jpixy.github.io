+++
title = "22 - C++ 个人量化交易实战"
date = 2025-01-20
description = "个人使用 C++ 进行量化交易的完整指南：何时需要 C++、开发环境搭建、常用库、实战代码、与 Python 混合开发"
[taxonomies]
tags = ["quant", "cpp", "trading", "performance", "personal-trading"]
+++

## 概述

虽然 Python 是个人量化的首选语言，但在某些场景下，C++ 仍然是必要的选择。本文探讨个人量化交易者何时需要 C++，以及如何实践。

**本文解答：**

- 个人什么情况下需要用 C++？
- C++ 量化开发环境如何搭建？
- 有哪些常用的 C++ 量化库？
- 如何实现一个简单的 C++ 交易系统？
- C++ 和 Python 如何混合使用？

---

## 一、个人何时需要 C++

### 1.1 需要 C++ 的场景

```
个人量化中需要 C++ 的典型场景：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   场景1：CTP 期货交易                                   │
│   ────────────────────                                  │
│   • CTP 官方 API 是 C++ 接口                            │
│   • Python 封装（如 vnpy）底层也是 C++                  │
│   • 需要极致延迟时，直接用 C++                          │
│                                                          │
│   场景2：高频/日内策略                                  │
│   ────────────────────                                  │
│   • 毫秒级延迟敏感                                      │
│   • 每天数百到数千次交易                                │
│   • Python 的 GIL 和解释开销成为瓶颈                    │
│                                                          │
│   场景3：复杂计算                                       │
│   ────────────────────                                  │
│   • 实时期权定价                                        │
│   • 大规模订单簿处理                                    │
│   • 高维因子计算                                        │
│                                                          │
│   场景4：学习目的                                       │
│   ────────────────────                                  │
│   • 想进入量化行业（C++ 是标配）                        │
│   • 深入理解系统底层                                    │
│   • 提升技术竞争力                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 不需要 C++ 的场景

```
继续使用 Python 的场景：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   ✓ 日/周级别策略                                       │
│   ✓ 策略研究和回测                                      │
│   ✓ 非期货市场（美股、加密货币）                        │
│   ✓ 延迟不敏感的策略                                    │
│   ✓ 小规模个人交易                                      │
│                                                          │
│   ──────────────────────────────────────────────────   │
│                                                          │
│   原则：能用 Python 就用 Python                         │
│   只在 Python 无法满足需求时才考虑 C++                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.3 性能对比

```
Python vs C++ 性能对比（典型场景）：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   操作                    Python      C++     提升      │
│   ──────────────────────────────────────────────────   │
│   订单簿更新              100μs       1μs     100x      │
│   策略信号计算            10ms        100μs   100x      │
│   行情解析                500μs       5μs     100x      │
│   下单到发送              1ms         10μs    100x      │
│                                                          │
│   ──────────────────────────────────────────────────   │
│                                                          │
│   说明：                                                │
│   • 数字为典型值，实际因实现而异                        │
│   • Python 使用 NumPy 可显著缩小差距                    │
│   • 对于日级策略，毫秒级差异无关紧要                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 二、C++ 量化开发环境

### 2.1 开发环境搭建

**Linux（推荐）**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install build-essential cmake git
sudo apt install libboost-all-dev libssl-dev

# 安装 vcpkg 包管理器
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg && ./bootstrap-vcpkg.sh
./vcpkg integrate install

# 安装常用库
./vcpkg install nlohmann-json fmt spdlog catch2
```

**macOS**

```bash
# 使用 Homebrew
brew install cmake boost openssl
brew install vcpkg

# 或使用 conan
pip install conan
```

**Windows**

```powershell
# 安装 Visual Studio 2022 (Community 版免费)
# 选择 "C++ 桌面开发" 工作负载

# 安装 vcpkg
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install
```

### 2.2 项目结构

```
quant_cpp/
├── CMakeLists.txt           # CMake 构建配置
├── vcpkg.json               # 依赖管理
├── include/                 # 头文件
│   ├── common/
│   │   ├── types.h          # 通用类型定义
│   │   └── utils.h          # 工具函数
│   ├── data/
│   │   ├── market_data.h    # 行情数据结构
│   │   └── order_book.h     # 订单簿
│   ├── strategy/
│   │   ├── base_strategy.h  # 策略基类
│   │   └── dual_ma.h        # 双均线策略
│   └── execution/
│       ├── order.h          # 订单定义
│       └── broker.h         # 交易接口
├── src/                     # 源文件
│   ├── main.cpp
│   ├── data/
│   ├── strategy/
│   └── execution/
├── tests/                   # 测试
└── scripts/                 # 辅助脚本
```

### 2.3 CMakeLists.txt 示例

```cmake
cmake_minimum_required(VERSION 3.20)
project(quant_cpp VERSION 1.0.0 LANGUAGES CXX)

# C++20 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 编译选项
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -flto")
endif()

# 查找依赖
find_package(Boost REQUIRED COMPONENTS system thread)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(spdlog CONFIG REQUIRED)
find_package(fmt CONFIG REQUIRED)

# 包含目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 源文件
file(GLOB_RECURSE SOURCES "src/*.cpp")

# 可执行文件
add_executable(${PROJECT_NAME} ${SOURCES})

# 链接库
target_link_libraries(${PROJECT_NAME} PRIVATE
    Boost::system
    Boost::thread
    nlohmann_json::nlohmann_json
    spdlog::spdlog
    fmt::fmt
)
```

---

## 三、常用 C++ 量化库

### 3.1 库选择指南

| 类别 | 库名 | 用途 | 推荐度 |
|------|------|------|--------|
| **数据结构** | Boost | 容器、智能指针、异步 | ★★★★★ |
| **JSON** | nlohmann/json | JSON 解析 | ★★★★★ |
| **日志** | spdlog | 高性能日志 | ★★★★★ |
| **格式化** | fmt | 字符串格式化 | ★★★★★ |
| **网络** | Boost.Asio | 异步网络 | ★★★★★ |
| **WebSocket** | websocketpp | WebSocket 客户端 | ★★★★ |
| **HTTP** | cpp-httplib | HTTP 客户端 | ★★★★ |
| **数学** | Eigen | 线性代数 | ★★★★★ |
| **统计** | QuantLib | 金融计算 | ★★★★ |
| **测试** | Catch2 | 单元测试 | ★★★★★ |
| **基准** | Google Benchmark | 性能测试 | ★★★★★ |

### 3.2 核心库详解

**spdlog - 高性能日志**

```cpp
#include <spdlog/spdlog.h>
#include <spdlog/sinks/rotating_file_sink.h>

// 初始化日志
void init_logger() {
    auto file_sink = std::make_shared<spdlog::sinks::rotating_file_sink_mt>(
        "logs/trading.log", 1024 * 1024 * 10, 3  // 10MB, 3 files
    );
    auto logger = std::make_shared<spdlog::logger>("trading", file_sink);
    logger->set_level(spdlog::level::info);
    spdlog::set_default_logger(logger);
}

// 使用
spdlog::info("Order submitted: {} {} @ {}", symbol, qty, price);
spdlog::warn("High latency detected: {}μs", latency);
spdlog::error("Connection lost: {}", error_msg);
```

**nlohmann/json - JSON 处理**

```cpp
#include <nlohmann/json.hpp>
using json = nlohmann::json;

// 解析行情数据
void parse_market_data(const std::string& raw) {
    auto data = json::parse(raw);
    
    std::string symbol = data["symbol"];
    double price = data["price"];
    int64_t volume = data["volume"];
    
    // 或使用结构化绑定
    auto [bid, ask] = std::make_pair(
        data["bid"].get<double>(),
        data["ask"].get<double>()
    );
}

// 生成订单 JSON
json create_order_json(const std::string& symbol, double price, int qty) {
    return {
        {"symbol", symbol},
        {"price", price},
        {"quantity", qty},
        {"timestamp", std::chrono::system_clock::now().time_since_epoch().count()}
    };
}
```

**Boost.Asio - 异步网络**

```cpp
#include <boost/asio.hpp>
#include <boost/asio/ssl.hpp>

namespace asio = boost::asio;
using tcp = asio::ip::tcp;

class MarketDataClient {
public:
    MarketDataClient(asio::io_context& io)
        : io_(io), socket_(io) {}
    
    void connect(const std::string& host, const std::string& port) {
        tcp::resolver resolver(io_);
        auto endpoints = resolver.resolve(host, port);
        asio::async_connect(socket_, endpoints,
            [this](auto ec, auto) {
                if (!ec) {
                    start_read();
                }
            });
    }
    
private:
    void start_read() {
        asio::async_read_until(socket_, buffer_, '\n',
            [this](auto ec, auto bytes) {
                if (!ec) {
                    handle_message(bytes);
                    start_read();
                }
            });
    }
    
    void handle_message(size_t bytes);
    
    asio::io_context& io_;
    tcp::socket socket_;
    asio::streambuf buffer_;
};
```

---

## 四、核心数据结构实现

### 4.1 行情数据结构

```cpp
#pragma once
#include <string>
#include <chrono>
#include <cstdint>

namespace quant {

// 使用 packed 结构减少内存
#pragma pack(push, 1)

struct Tick {
    char symbol[16];           // 合约代码
    int64_t timestamp;         // 时间戳（纳秒）
    double last_price;         // 最新价
    double bid_price;          // 买一价
    double ask_price;          // 卖一价
    int32_t bid_volume;        // 买一量
    int32_t ask_volume;        // 卖一量
    int64_t volume;            // 成交量
    double turnover;           // 成交额
    double open_interest;      // 持仓量
    
    // 便捷方法
    double mid_price() const {
        return (bid_price + ask_price) / 2.0;
    }
    
    double spread() const {
        return ask_price - bid_price;
    }
};

struct Bar {
    char symbol[16];
    int64_t timestamp;
    double open;
    double high;
    double low;
    double close;
    int64_t volume;
    double turnover;
};

#pragma pack(pop)

// 高精度时间戳
inline int64_t now_nanos() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch()
    ).count();
}

} // namespace quant
```

### 4.2 订单簿实现

```cpp
#pragma once
#include <map>
#include <unordered_map>
#include <vector>

namespace quant {

struct PriceLevel {
    double price;
    int64_t quantity;
    int32_t order_count;
};

class OrderBook {
public:
    // 更新订单簿
    void update(double price, int64_t qty, bool is_bid) {
        auto& book = is_bid ? bids_ : asks_;
        
        if (qty == 0) {
            book.erase(price);
        } else {
            book[price] = qty;
        }
    }
    
    // 获取最优价格
    double best_bid() const {
        return bids_.empty() ? 0 : bids_.rbegin()->first;
    }
    
    double best_ask() const {
        return asks_.empty() ? 0 : asks_.begin()->first;
    }
    
    // 获取买卖价差
    double spread() const {
        return best_ask() - best_bid();
    }
    
    // 获取中间价
    double mid_price() const {
        return (best_bid() + best_ask()) / 2.0;
    }
    
    // 获取深度
    std::vector<PriceLevel> get_bids(int depth = 5) const {
        std::vector<PriceLevel> result;
        int count = 0;
        for (auto it = bids_.rbegin(); it != bids_.rend() && count < depth; ++it, ++count) {
            result.push_back({it->first, it->second, 1});
        }
        return result;
    }
    
    std::vector<PriceLevel> get_asks(int depth = 5) const {
        std::vector<PriceLevel> result;
        int count = 0;
        for (auto it = asks_.begin(); it != asks_.end() && count < depth; ++it, ++count) {
            result.push_back({it->first, it->second, 1});
        }
        return result;
    }
    
    // 计算加权平均价格
    double vwap(bool is_bid, int64_t target_qty) const {
        const auto& book = is_bid ? bids_ : asks_;
        double total_value = 0;
        int64_t total_qty = 0;
        
        auto it = is_bid ? book.rbegin() : book.begin();
        auto end = is_bid ? book.rend() : book.end();
        
        while (it != end && total_qty < target_qty) {
            int64_t qty = std::min(it->second, target_qty - total_qty);
            total_value += it->first * qty;
            total_qty += qty;
            ++it;
        }
        
        return total_qty > 0 ? total_value / total_qty : 0;
    }
    
private:
    std::map<double, int64_t> bids_;  // 价格 -> 数量，降序
    std::map<double, int64_t> asks_;  // 价格 -> 数量，升序
};

} // namespace quant
```

### 4.3 订单管理

```cpp
#pragma once
#include <string>
#include <atomic>
#include <unordered_map>
#include <mutex>

namespace quant {

enum class OrderSide { Buy, Sell };
enum class OrderType { Market, Limit };
enum class OrderStatus { 
    Created, 
    Submitted, 
    Accepted,
    PartiallyFilled, 
    Filled, 
    Cancelled, 
    Rejected 
};

struct Order {
    std::string order_id;
    std::string symbol;
    OrderSide side;
    OrderType type;
    double price;
    int64_t quantity;
    int64_t filled_quantity = 0;
    double avg_price = 0;
    OrderStatus status = OrderStatus::Created;
    int64_t create_time;
    int64_t update_time;
    
    bool is_active() const {
        return status == OrderStatus::Submitted || 
               status == OrderStatus::Accepted ||
               status == OrderStatus::PartiallyFilled;
    }
    
    int64_t remaining() const {
        return quantity - filled_quantity;
    }
};

class OrderManager {
public:
    // 生成订单 ID
    std::string generate_order_id() {
        return "ORD_" + std::to_string(++order_id_counter_);
    }
    
    // 创建订单
    Order& create_order(const std::string& symbol, OrderSide side,
                        OrderType type, double price, int64_t qty) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        Order order;
        order.order_id = generate_order_id();
        order.symbol = symbol;
        order.side = side;
        order.type = type;
        order.price = price;
        order.quantity = qty;
        order.create_time = now_nanos();
        
        orders_[order.order_id] = order;
        return orders_[order.order_id];
    }
    
    // 更新订单状态
    void update_order(const std::string& order_id, OrderStatus status,
                      int64_t filled_qty = 0, double avg_price = 0) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        auto it = orders_.find(order_id);
        if (it != orders_.end()) {
            it->second.status = status;
            it->second.filled_quantity = filled_qty;
            it->second.avg_price = avg_price;
            it->second.update_time = now_nanos();
        }
    }
    
    // 获取订单
    const Order* get_order(const std::string& order_id) const {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = orders_.find(order_id);
        return it != orders_.end() ? &it->second : nullptr;
    }
    
    // 获取活跃订单
    std::vector<Order> get_active_orders() const {
        std::lock_guard<std::mutex> lock(mutex_);
        std::vector<Order> result;
        for (const auto& [id, order] : orders_) {
            if (order.is_active()) {
                result.push_back(order);
            }
        }
        return result;
    }
    
private:
    mutable std::mutex mutex_;
    std::unordered_map<std::string, Order> orders_;
    std::atomic<uint64_t> order_id_counter_{0};
};

} // namespace quant
```

---

## 五、策略框架实现

### 5.1 策略基类

```cpp
#pragma once
#include "market_data.h"
#include "order.h"
#include <memory>
#include <functional>

namespace quant {

// 策略信号
struct Signal {
    std::string symbol;
    double target_position;  // 目标仓位（正数多，负数空，0 平仓）
    double confidence;       // 信号置信度 [0, 1]
    std::string reason;      // 信号原因
};

// 策略基类
class Strategy {
public:
    virtual ~Strategy() = default;
    
    // 初始化
    virtual void on_init() {}
    
    // 行情回调
    virtual void on_tick(const Tick& tick) {}
    virtual void on_bar(const Bar& bar) {}
    
    // 订单回调
    virtual void on_order(const Order& order) {}
    virtual void on_trade(const Order& order, double price, int64_t qty) {}
    
    // 生成信号
    virtual std::vector<Signal> generate_signals() { return {}; }
    
    // 设置回调
    void set_order_callback(std::function<void(const Order&)> cb) {
        send_order_ = cb;
    }
    
protected:
    // 发送订单（由框架注入）
    void send_order(const std::string& symbol, OrderSide side,
                    double price, int64_t qty, OrderType type = OrderType::Limit) {
        Order order;
        order.symbol = symbol;
        order.side = side;
        order.price = price;
        order.quantity = qty;
        order.type = type;
        if (send_order_) send_order_(order);
    }
    
    void buy(const std::string& symbol, double price, int64_t qty) {
        send_order(symbol, OrderSide::Buy, price, qty);
    }
    
    void sell(const std::string& symbol, double price, int64_t qty) {
        send_order(symbol, OrderSide::Sell, price, qty);
    }
    
private:
    std::function<void(const Order&)> send_order_;
};

} // namespace quant
```

### 5.2 双均线策略实现

```cpp
#pragma once
#include "base_strategy.h"
#include <deque>
#include <numeric>

namespace quant {

class DualMAStrategy : public Strategy {
public:
    DualMAStrategy(int short_period, int long_period)
        : short_period_(short_period)
        , long_period_(long_period) {}
    
    void on_init() override {
        spdlog::info("DualMA Strategy initialized: short={}, long={}",
                     short_period_, long_period_);
    }
    
    void on_bar(const Bar& bar) override {
        symbol_ = bar.symbol;
        prices_.push_back(bar.close);
        
        // 保持足够的历史数据
        if (prices_.size() > static_cast<size_t>(long_period_ * 2)) {
            prices_.pop_front();
        }
        
        // 数据不足，不计算
        if (prices_.size() < static_cast<size_t>(long_period_)) {
            return;
        }
        
        // 计算均线
        double short_ma = calculate_ma(short_period_);
        double long_ma = calculate_ma(long_period_);
        
        // 生成信号
        bool golden_cross = prev_short_ma_ <= prev_long_ma_ && short_ma > long_ma;
        bool death_cross = prev_short_ma_ >= prev_long_ma_ && short_ma < long_ma;
        
        if (golden_cross && position_ <= 0) {
            // 金叉买入
            buy(symbol_, bar.close, 1);
            position_ = 1;
            spdlog::info("Golden cross: BUY at {}", bar.close);
        } else if (death_cross && position_ >= 0) {
            // 死叉卖出
            sell(symbol_, bar.close, 1);
            position_ = -1;
            spdlog::info("Death cross: SELL at {}", bar.close);
        }
        
        prev_short_ma_ = short_ma;
        prev_long_ma_ = long_ma;
    }
    
    void on_order(const Order& order) override {
        spdlog::info("Order update: {} {} @ {} - {}",
                     order.order_id,
                     order.side == OrderSide::Buy ? "BUY" : "SELL",
                     order.price,
                     static_cast<int>(order.status));
    }
    
private:
    double calculate_ma(int period) const {
        if (prices_.size() < static_cast<size_t>(period)) return 0;
        
        auto begin = prices_.end() - period;
        auto end = prices_.end();
        return std::accumulate(begin, end, 0.0) / period;
    }
    
    int short_period_;
    int long_period_;
    std::string symbol_;
    std::deque<double> prices_;
    double prev_short_ma_ = 0;
    double prev_long_ma_ = 0;
    int position_ = 0;
};

} // namespace quant
```

### 5.3 动量策略实现

```cpp
#pragma once
#include "base_strategy.h"
#include <deque>
#include <cmath>

namespace quant {

class MomentumStrategy : public Strategy {
public:
    MomentumStrategy(int lookback, double threshold)
        : lookback_(lookback)
        , threshold_(threshold) {}
    
    void on_bar(const Bar& bar) override {
        symbol_ = bar.symbol;
        prices_.push_back(bar.close);
        
        if (prices_.size() > static_cast<size_t>(lookback_ + 1)) {
            prices_.pop_front();
        }
        
        if (prices_.size() < static_cast<size_t>(lookback_ + 1)) {
            return;
        }
        
        // 计算动量（收益率）
        double momentum = (prices_.back() - prices_.front()) / prices_.front();
        
        // 动量交易信号
        if (momentum > threshold_ && position_ <= 0) {
            // 正动量，做多
            if (position_ < 0) {
                // 先平空仓
                buy(symbol_, bar.close, std::abs(position_));
            }
            buy(symbol_, bar.close, 1);
            position_ = 1;
            spdlog::info("Momentum BUY: return={:.2%}", momentum);
        } else if (momentum < -threshold_ && position_ >= 0) {
            // 负动量，做空
            if (position_ > 0) {
                // 先平多仓
                sell(symbol_, bar.close, position_);
            }
            sell(symbol_, bar.close, 1);
            position_ = -1;
            spdlog::info("Momentum SELL: return={:.2%}", momentum);
        }
    }
    
private:
    int lookback_;
    double threshold_;
    std::string symbol_;
    std::deque<double> prices_;
    int position_ = 0;
};

} // namespace quant
```

---

## 六、CTP 接口封装

### 6.1 CTP 回调封装

```cpp
#pragma once
#include "ThostFtdcMdApi.h"
#include "ThostFtdcTraderApi.h"
#include <functional>
#include <string>
#include <atomic>

namespace quant {

// CTP 行情回调封装
class MdSpi : public CThostFtdcMdSpi {
public:
    using TickCallback = std::function<void(const Tick&)>;
    
    void set_tick_callback(TickCallback cb) { tick_callback_ = cb; }
    
    void OnRtnDepthMarketData(CThostFtdcDepthMarketDataField* data) override {
        if (!data || !tick_callback_) return;
        
        Tick tick{};
        std::strncpy(tick.symbol, data->InstrumentID, sizeof(tick.symbol));
        tick.timestamp = now_nanos();
        tick.last_price = data->LastPrice;
        tick.bid_price = data->BidPrice1;
        tick.ask_price = data->AskPrice1;
        tick.bid_volume = data->BidVolume1;
        tick.ask_volume = data->AskVolume1;
        tick.volume = data->Volume;
        tick.turnover = data->Turnover;
        tick.open_interest = data->OpenInterest;
        
        tick_callback_(tick);
    }
    
    void OnFrontConnected() override {
        spdlog::info("MD: Front connected");
        connected_ = true;
    }
    
    void OnFrontDisconnected(int reason) override {
        spdlog::warn("MD: Front disconnected, reason={}", reason);
        connected_ = false;
    }
    
    bool is_connected() const { return connected_; }
    
private:
    TickCallback tick_callback_;
    std::atomic<bool> connected_{false};
};

// CTP 交易回调封装
class TraderSpi : public CThostFtdcTraderSpi {
public:
    using OrderCallback = std::function<void(const Order&)>;
    
    void set_order_callback(OrderCallback cb) { order_callback_ = cb; }
    
    void OnRtnOrder(CThostFtdcOrderField* data) override {
        if (!data || !order_callback_) return;
        
        Order order;
        order.order_id = data->OrderSysID;
        order.symbol = data->InstrumentID;
        order.side = (data->Direction == THOST_FTDC_D_Buy) 
                     ? OrderSide::Buy : OrderSide::Sell;
        order.price = data->LimitPrice;
        order.quantity = data->VolumeTotalOriginal;
        order.filled_quantity = data->VolumeTraded;
        
        // 状态转换
        switch (data->OrderStatus) {
            case THOST_FTDC_OST_AllTraded:
                order.status = OrderStatus::Filled;
                break;
            case THOST_FTDC_OST_PartTradedQueueing:
                order.status = OrderStatus::PartiallyFilled;
                break;
            case THOST_FTDC_OST_Canceled:
                order.status = OrderStatus::Cancelled;
                break;
            default:
                order.status = OrderStatus::Accepted;
        }
        
        order_callback_(order);
    }
    
    void OnFrontConnected() override {
        spdlog::info("Trader: Front connected");
        connected_ = true;
    }
    
private:
    OrderCallback order_callback_;
    std::atomic<bool> connected_{false};
};

} // namespace quant
```

### 6.2 CTP 客户端

```cpp
#pragma once
#include "ctp_spi.h"
#include <memory>
#include <thread>

namespace quant {

class CtpClient {
public:
    CtpClient(const std::string& md_front, const std::string& trader_front,
              const std::string& broker_id, const std::string& user_id,
              const std::string& password)
        : md_front_(md_front)
        , trader_front_(trader_front)
        , broker_id_(broker_id)
        , user_id_(user_id)
        , password_(password) {}
    
    ~CtpClient() {
        stop();
    }
    
    void start() {
        // 创建行情 API
        md_api_ = CThostFtdcMdApi::CreateFtdcMdApi("./md_flow/");
        md_spi_ = std::make_unique<MdSpi>();
        md_api_->RegisterSpi(md_spi_.get());
        md_api_->RegisterFront(const_cast<char*>(md_front_.c_str()));
        md_api_->Init();
        
        // 创建交易 API
        trader_api_ = CThostFtdcTraderApi::CreateFtdcTraderApi("./trader_flow/");
        trader_spi_ = std::make_unique<TraderSpi>();
        trader_api_->RegisterSpi(trader_spi_.get());
        trader_api_->RegisterFront(const_cast<char*>(trader_front_.c_str()));
        trader_api_->Init();
        
        // 等待连接
        while (!md_spi_->is_connected()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
        spdlog::info("CTP client started");
    }
    
    void stop() {
        if (md_api_) {
            md_api_->Release();
            md_api_ = nullptr;
        }
        if (trader_api_) {
            trader_api_->Release();
            trader_api_ = nullptr;
        }
    }
    
    // 订阅行情
    void subscribe(const std::vector<std::string>& symbols) {
        std::vector<char*> instruments;
        for (const auto& s : symbols) {
            instruments.push_back(const_cast<char*>(s.c_str()));
        }
        md_api_->SubscribeMarketData(instruments.data(), instruments.size());
    }
    
    // 设置回调
    void set_tick_callback(MdSpi::TickCallback cb) {
        md_spi_->set_tick_callback(cb);
    }
    
    void set_order_callback(TraderSpi::OrderCallback cb) {
        trader_spi_->set_order_callback(cb);
    }
    
    // 下单
    void send_order(const Order& order) {
        CThostFtdcInputOrderField req{};
        std::strncpy(req.BrokerID, broker_id_.c_str(), sizeof(req.BrokerID));
        std::strncpy(req.InvestorID, user_id_.c_str(), sizeof(req.InvestorID));
        std::strncpy(req.InstrumentID, order.symbol.c_str(), sizeof(req.InstrumentID));
        
        req.Direction = (order.side == OrderSide::Buy) 
                        ? THOST_FTDC_D_Buy : THOST_FTDC_D_Sell;
        req.LimitPrice = order.price;
        req.VolumeTotalOriginal = order.quantity;
        req.OrderPriceType = THOST_FTDC_OPT_LimitPrice;
        req.TimeCondition = THOST_FTDC_TC_GFD;
        req.VolumeCondition = THOST_FTDC_VC_AV;
        req.ContingentCondition = THOST_FTDC_CC_Immediately;
        req.CombOffsetFlag[0] = THOST_FTDC_OF_Open;
        req.CombHedgeFlag[0] = THOST_FTDC_HF_Speculation;
        
        trader_api_->ReqOrderInsert(&req, ++request_id_);
    }
    
private:
    std::string md_front_;
    std::string trader_front_;
    std::string broker_id_;
    std::string user_id_;
    std::string password_;
    
    CThostFtdcMdApi* md_api_ = nullptr;
    CThostFtdcTraderApi* trader_api_ = nullptr;
    std::unique_ptr<MdSpi> md_spi_;
    std::unique_ptr<TraderSpi> trader_spi_;
    int request_id_ = 0;
};

} // namespace quant
```

---

## 七、国内 vs 国际 C++ 交易平台

### 7.1 C++ 交易平台对比

```
中国大陆 vs 国际 C++ 量化平台对比：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   中国大陆（选择有限）                                  │
│   ──────────────────                                    │
│   唯一选择：CTP（及其衍生系统）                         │
│                                                          │
│   平台          说明                适合人群            │
│   ─────────────────────────────────────────────────    │
│   CTP           期货公司标配        个人/机构           │
│   飞马(Femas)   高速版本            机构                │
│   飞创(X-Speed) 高速版本            机构                │
│   恒生 UFT     统一接入            机构                │
│                                                          │
│   限制：                                                │
│   • A 股没有官方 C++ API                               │
│   • 高速通道需要机构资质                                │
│   • 个人只能用普通 CTP                                  │
│                                                          │
│   ──────────────────────────────────────────────────   │
│                                                          │
│   国际市场（选择丰富）                                  │
│   ──────────────────                                    │
│                                                          │
│   平台              市场          个人可用   延迟       │
│   ─────────────────────────────────────────────────    │
│   IB TWS API       全球          ✓          毫秒       │
│   CME Globex       美国期货      ✓*         微秒       │
│   Nasdaq ITCH      美股          ✗          微秒       │
│   Eurex            欧洲          ✓*         微秒       │
│   SGX              新加坡        ✓*         微秒       │
│   Binance C++ SDK  加密货币      ✓          毫秒       │
│                                                          │
│   * 需要通过经纪商，有资金/合规门槛                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 7.2 个人首选：Interactive Brokers

```
为什么 IB 是个人 C++ 量化的最佳国际选择：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   优势                                                  │
│   ────                                                  │
│   ✓ 个人可开户（中国大陆居民可开）                      │
│   ✓ 官方原生 C++ API                                   │
│   ✓ 覆盖 150+ 全球市场                                  │
│   ✓ 股票/期货/期权/外汇/债券                            │
│   ✓ 完善的文档和示例代码                                │
│   ✓ 免费模拟交易环境                                    │
│   ✓ 佣金低廉                                            │
│                                                          │
│   劣势                                                  │
│   ────                                                  │
│   ✗ 延迟在毫秒级（非 HFT 级别）                         │
│   ✗ 需要运行 TWS 或 IB Gateway                          │
│   ✗ 出入金需要外汇（中国有限额）                        │
│                                                          │
│   适合的策略                                            │
│   ────────────                                          │
│   • 日级/周级策略                                       │
│   • ETF 轮动                                            │
│   • 全球资产配置                                        │
│   • 期货日内（非高频）                                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 7.3 IB C++ API 完整示例

```cpp
// 完整的 IB C++ 交易示例
#include "EClientSocket.h"
#include "EWrapper.h"
#include "EReader.h"
#include "EReaderOSSignal.h"
#include "Contract.h"
#include "Order.h"
#include <iostream>
#include <thread>
#include <atomic>

class IBClient : public EWrapper {
public:
    IBClient() : signal_(2000), client_(this, &signal_) {}
    
    // 连接
    bool connect(const std::string& host, int port, int clientId) {
        bool connected = client_.eConnect(host.c_str(), port, clientId);
        if (connected) {
            reader_ = std::make_unique<EReader>(&client_, &signal_);
            reader_->start();
            
            // 启动消息处理线程
            msg_thread_ = std::thread([this]() {
                while (client_.isConnected()) {
                    signal_.waitForSignal();
                    reader_->processMsgs();
                }
            });
        }
        return connected;
    }
    
    void disconnect() {
        client_.eDisconnect();
        if (msg_thread_.joinable()) {
            msg_thread_.join();
        }
    }
    
    // 订阅行情
    void subscribeMarketData(int reqId, const std::string& symbol) {
        Contract contract;
        contract.symbol = symbol;
        contract.secType = "STK";
        contract.exchange = "SMART";
        contract.currency = "USD";
        
        client_.reqMktData(reqId, contract, "", false, false, {});
        std::cout << "Subscribed to " << symbol << std::endl;
    }
    
    // 下单
    void placeOrder(int orderId, const std::string& symbol,
                    const std::string& action, int qty, double price) {
        Contract contract;
        contract.symbol = symbol;
        contract.secType = "STK";
        contract.exchange = "SMART";
        contract.currency = "USD";
        
        Order order;
        order.action = action;  // "BUY" or "SELL"
        order.orderType = "LMT";
        order.totalQuantity = qty;
        order.lmtPrice = price;
        
        client_.placeOrder(orderId, contract, order);
        std::cout << "Order placed: " << action << " " << qty 
                  << " " << symbol << " @ " << price << std::endl;
    }
    
    // ===== EWrapper 回调 =====
    
    void tickPrice(TickerId tickerId, TickType field, 
                   double price, const TickAttrib& attrib) override {
        const char* fieldName = field == 1 ? "BID" : 
                                field == 2 ? "ASK" : 
                                field == 4 ? "LAST" : "OTHER";
        std::cout << "Price [" << tickerId << "] " 
                  << fieldName << ": " << price << std::endl;
    }
    
    void orderStatus(OrderId orderId, const std::string& status,
                     Decimal filled, Decimal remaining,
                     double avgFillPrice, int permId, int parentId,
                     double lastFillPrice, int clientId,
                     const std::string& whyHeld, double mktCapPrice) override {
        std::cout << "Order " << orderId << ": " << status 
                  << " filled=" << decimalToDouble(filled)
                  << " avg=" << avgFillPrice << std::endl;
    }
    
    void error(int id, int errorCode, const std::string& msg,
               const std::string& advancedOrderRejectJson) override {
        std::cerr << "Error [" << id << "] " << errorCode 
                  << ": " << msg << std::endl;
    }
    
    void connectAck() override {
        std::cout << "Connected to IB" << std::endl;
        client_.reqMarketDataType(1);  // 实时数据
    }
    
    // 必须实现的其他回调（简化版）
    void nextValidId(OrderId orderId) override {
        next_order_id_ = orderId;
        std::cout << "Next valid order ID: " << orderId << std::endl;
    }
    
    int getNextOrderId() { return next_order_id_++; }
    
private:
    EReaderOSSignal signal_;
    EClientSocket client_;
    std::unique_ptr<EReader> reader_;
    std::thread msg_thread_;
    std::atomic<int> next_order_id_{0};
};

// 使用示例
int main() {
    IBClient client;
    
    // 连接 TWS（端口 7497）或 IB Gateway（端口 4001）
    if (!client.connect("127.0.0.1", 7497, 0)) {
        std::cerr << "Failed to connect" << std::endl;
        return 1;
    }
    
    std::this_thread::sleep_for(std::chrono::seconds(2));
    
    // 订阅苹果股票行情
    client.subscribeMarketData(1, "AAPL");
    
    // 等待行情
    std::this_thread::sleep_for(std::chrono::seconds(5));
    
    // 下单（买入 10 股，限价 150）
    client.placeOrder(client.getNextOrderId(), "AAPL", "BUY", 10, 150.0);
    
    // 保持运行
    std::this_thread::sleep_for(std::chrono::seconds(30));
    
    client.disconnect();
    return 0;
}
```

### 7.4 CMake 配置（IB API）

```cmake
# CMakeLists.txt for IB C++ API
cmake_minimum_required(VERSION 3.15)
project(ib_trading)

set(CMAKE_CXX_STANDARD 17)

# IB TWS API 路径（从 IB 官网下载）
set(IB_API_PATH "${CMAKE_SOURCE_DIR}/third_party/IBJts/source/cppclient/client")

# 包含 IB 头文件
include_directories(${IB_API_PATH})

# IB API 源文件
file(GLOB IB_SOURCES "${IB_API_PATH}/*.cpp")

add_executable(${PROJECT_NAME}
    main.cpp
    ${IB_SOURCES}
)

# Linux 需要链接 pthread
if(UNIX)
    target_link_libraries(${PROJECT_NAME} pthread)
endif()
```

### 7.5 国内外平台选择建议

```
根据你的情况选择平台：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   情况1：只做中国期货                                   │
│   ────────────────────                                  │
│   → 选择 CTP                                            │
│   → 本文第六章的 CTP 封装                               │
│   → 参考 quant-19、quant-20                             │
│                                                          │
│   情况2：想做全球市场                                   │
│   ────────────────────                                  │
│   → 选择 IB（Interactive Brokers）                      │
│   → 本章的 IB C++ API                                   │
│   → 参考 quant-21 第六章                                │
│                                                          │
│   情况3：两边都做                                       │
│   ────────────────────                                  │
│   → 分开两套系统                                        │
│   → CTP 用于国内期货                                    │
│   → IB 用于海外市场                                     │
│   → 统一的策略层，不同的执行层                          │
│                                                          │
│   情况4：想做加密货币                                   │
│   ────────────────────                                  │
│   → C++ 不是首选（推荐 Python/Rust）                    │
│   → 如必须用 C++，可用 Binance C++ SDK                  │
│   → 或自行封装 REST/WebSocket API                       │
│                                                          │
│   情况5：学习目的                                       │
│   ────────────────────                                  │
│   → 先学 IB（文档好、有模拟盘）                         │
│   → 再学 CTP（国内就业需要）                            │
│   → 两者 API 风格类似                                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 八、C++ 与 Python 混合开发

### 8.1 pybind11 封装

**安装**

```bash
pip install pybind11
# 或
vcpkg install pybind11
```

**封装示例**

```cpp
// bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "order_book.h"
#include "market_data.h"

namespace py = pybind11;

PYBIND11_MODULE(quant_cpp, m) {
    m.doc() = "C++ Quant Trading Library";
    
    // 绑定 Tick 结构
    py::class_<quant::Tick>(m, "Tick")
        .def(py::init<>())
        .def_readwrite("symbol", &quant::Tick::symbol)
        .def_readwrite("timestamp", &quant::Tick::timestamp)
        .def_readwrite("last_price", &quant::Tick::last_price)
        .def_readwrite("bid_price", &quant::Tick::bid_price)
        .def_readwrite("ask_price", &quant::Tick::ask_price)
        .def("mid_price", &quant::Tick::mid_price)
        .def("spread", &quant::Tick::spread);
    
    // 绑定 OrderBook 类
    py::class_<quant::OrderBook>(m, "OrderBook")
        .def(py::init<>())
        .def("update", &quant::OrderBook::update)
        .def("best_bid", &quant::OrderBook::best_bid)
        .def("best_ask", &quant::OrderBook::best_ask)
        .def("spread", &quant::OrderBook::spread)
        .def("mid_price", &quant::OrderBook::mid_price)
        .def("vwap", &quant::OrderBook::vwap);
    
    // 绑定高性能函数
    m.def("calculate_ema", [](const std::vector<double>& prices, int period) {
        // 高性能 EMA 计算
        std::vector<double> result(prices.size());
        double alpha = 2.0 / (period + 1);
        result[0] = prices[0];
        for (size_t i = 1; i < prices.size(); ++i) {
            result[i] = alpha * prices[i] + (1 - alpha) * result[i-1];
        }
        return result;
    }, "Calculate EMA with C++ performance");
}
```

**CMakeLists.txt 添加**

```cmake
find_package(pybind11 CONFIG REQUIRED)
pybind11_add_module(quant_cpp bindings.cpp)
```

**Python 中使用**

```python
import quant_cpp

# 使用 C++ 订单簿
book = quant_cpp.OrderBook()
book.update(100.0, 1000, True)   # bid
book.update(100.1, 500, False)   # ask

print(f"Spread: {book.spread()}")
print(f"Mid: {book.mid_price()}")

# 使用 C++ 高性能计算
import numpy as np
prices = np.random.randn(10000).cumsum() + 100
ema = quant_cpp.calculate_ema(prices.tolist(), 20)  # C++ 计算
```

### 8.2 混合架构最佳实践

```
混合开发架构：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   Python 层（策略研究、高层逻辑）                       │
│   ──────────────────────────────                        │
│   • Jupyter 策略研究                                    │
│   • 回测框架                                            │
│   • 参数优化                                            │
│   • 可视化                                              │
│                     │                                   │
│                     ▼ pybind11                          │
│   C++ 层（性能敏感模块）                                │
│   ──────────────────────────────                        │
│   • 订单簿管理                                          │
│   • 行情解析                                            │
│   • 高频计算                                            │
│   • CTP/交易接口                                        │
│                                                          │
└─────────────────────────────────────────────────────────┘

推荐拆分方式：

┌────────────────────┬────────────────────────────────────┐
│      模块          │           语言选择                 │
├────────────────────┼────────────────────────────────────┤
│ 策略逻辑           │ Python（快速迭代）                 │
│ 回测系统           │ Python + C++ 计算核心              │
│ 订单簿             │ C++（性能敏感）                    │
│ 行情处理           │ C++（低延迟）                      │
│ 交易接口           │ C++（CTP 原生）                    │
│ 风控检查           │ C++（实时性）                      │
│ 数据分析           │ Python（pandas/numpy）             │
│ 可视化             │ Python（matplotlib/plotly）        │
└────────────────────┴────────────────────────────────────┘
```

---

## 九、性能优化技巧

### 9.1 编译优化

```cmake
# Release 编译优化
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -flto -DNDEBUG")

# 启用 PGO (Profile-Guided Optimization)
# 第一步：生成 profile
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-generate")
# 运行程序收集数据
# 第二步：使用 profile 优化
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-use")
```

### 9.2 内存优化

```cpp
// 使用对象池避免频繁分配
template<typename T, size_t PoolSize = 1024>
class ObjectPool {
public:
    T* acquire() {
        if (free_list_.empty()) {
            return new T();
        }
        T* obj = free_list_.back();
        free_list_.pop_back();
        return obj;
    }
    
    void release(T* obj) {
        if (free_list_.size() < PoolSize) {
            free_list_.push_back(obj);
        } else {
            delete obj;
        }
    }
    
private:
    std::vector<T*> free_list_;
};

// 使用示例
ObjectPool<Order> order_pool;
Order* order = order_pool.acquire();
// ... 使用 order
order_pool.release(order);
```

### 9.3 缓存友好

```cpp
// 结构体字段按访问频率和大小排列
struct alignas(64) HotData {  // 对齐到缓存行
    double last_price;    // 最常访问
    double bid_price;
    double ask_price;
    int64_t volume;
    // 填充到 64 字节
    char padding[24];
};

// 冷热数据分离
struct ColdData {
    std::string symbol;
    std::string exchange;
    // ... 不常访问的字段
};
```

---

## 十、实战建议

### 10.1 个人 C++ 量化路线

```
个人学习 C++ 量化的推荐路线：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   阶段1：基础（1-2个月）                                │
│   ────────────────────                                  │
│   • 掌握 C++17/20 核心特性                              │
│   • 熟悉 CMake、包管理                                  │
│   • 实现简单数据结构                                    │
│                                                          │
│   阶段2：量化基础（1-2个月）                            │
│   ────────────────────                                  │
│   • 实现 Tick/Bar/OrderBook                             │
│   • 实现简单策略框架                                    │
│   • 学习 CTP API                                        │
│                                                          │
│   阶段3：实战（2-3个月）                                │
│   ────────────────────                                  │
│   • 对接 CTP 模拟盘                                     │
│   • 实现完整交易系统                                    │
│   • 性能优化                                            │
│                                                          │
│   阶段4：进阶（持续）                                   │
│   ────────────────────                                  │
│   • 研究低延迟技术                                      │
│   • 混合语言开发                                        │
│   • 实盘交易                                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 10.2 常见错误

```
C++ 量化开发常见错误：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   ❌ 过早优化                                           │
│   ──────────                                            │
│   • 先让程序正确运行                                    │
│   • 用工具（perf, vtune）找到瓶颈再优化                 │
│                                                          │
│   ❌ 忽视内存安全                                       │
│   ──────────                                            │
│   • 使用智能指针                                        │
│   • 使用 AddressSanitizer 检测                          │
│                                                          │
│   ❌ 忽视测试                                           │
│   ──────────                                            │
│   • 单元测试是必须的                                    │
│   • 回测结果要与 Python 对比验证                        │
│                                                          │
│   ❌ 过度复杂                                           │
│   ──────────                                            │
│   • 不要过度设计                                        │
│   • 简单直接的代码更可靠                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 十一、总结

```
C++ 个人量化要点：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   何时使用                                              │
│   ────────                                              │
│   • CTP 期货交易                                        │
│   • 毫秒级延迟要求                                      │
│   • 复杂实时计算                                        │
│   • 职业发展需要                                        │
│                                                          │
│   技术栈                                                │
│   ────────                                              │
│   • C++17/20 + CMake + vcpkg                            │
│   • Boost + spdlog + nlohmann/json                      │
│   • pybind11（与 Python 混合）                          │
│                                                          │
│   最佳实践                                              │
│   ────────                                              │
│   • 先 Python 原型，再 C++ 优化                         │
│   • 核心模块用 C++，高层逻辑用 Python                   │
│   • 重视测试和代码质量                                  │
│                                                          │
│   ──────────────────────────────────────────────────   │
│                                                          │
│   "C++ 是量化交易的硬技能，                             │
│    掌握它能打开更多可能性。"                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 相关文章

- [上一篇：21 - 量化开发技术栈选择](/articles/quant/quant-21-量化开发技术栈选择/)
- [下一篇：23 - C++ 量化系统性能优化](/articles/quant/quant-23-Cpp量化系统性能优化/)
