+++
title = "20. 高性能序列化技术"
date = 2026-01-21
weight = 20000
description = "深入剖析高性能序列化技术，包括SBE、FlatBuffers、Cap'n Proto、零拷贝解析和性能对比"
[taxonomies]
tags = ["HFT", "序列化", "SBE", "FlatBuffers", "低延迟"]
+++

## 概述

序列化是HFT系统中的关键路径。本文对比各种高性能序列化方案。

---

## 一、序列化方案对比

### 1.1 方案概览

| 方案 | 延迟 | 编码大小 | 零拷贝 | Schema | 语言支持 |
|------|------|----------|--------|--------|----------|
| JSON | 高 | 大 | 否 | 否 | 全 |
| Protobuf | 中 | 小 | 否 | 是 | 广 |
| SBE | 极低 | 最小 | 是 | 是 | 中 |
| FlatBuffers | 低 | 小 | 是 | 是 | 广 |
| Cap'n Proto | 低 | 小 | 是 | 是 | 中 |

### 1.2 HFT选择标准

```
1. 零拷贝解析（最重要）
   - 不需要反序列化整个消息
   - 直接读取字段

2. 固定大小消息（对于热路径）
   - 避免长度解析
   - 可预测的内存访问

3. 低开销编码
   - 避免复杂的VarInt
   - 直接内存映射

4. Schema演进
   - 向后兼容
   - 向前兼容（可选）

推荐：SBE用于极致延迟，FlatBuffers用于灵活性
```

---

## 二、SBE (Simple Binary Encoding)

### 2.1 基本概念

```xml
<!-- SBE Schema示例 -->
<?xml version="1.0" encoding="UTF-8"?>
<sbe:messageSchema package="trading"
    id="1" version="1" byteOrder="littleEndian">
    
    <types>
        <type name="Price" primitiveType="int64"/>
        <type name="Qty" primitiveType="uint32"/>
        
        <enum name="Side" encodingType="uint8">
            <validValue name="Buy">0</validValue>
            <validValue name="Sell">1</validValue>
        </enum>
        
        <composite name="Symbol">
            <type name="value" primitiveType="char" length="8"/>
        </composite>
    </types>
    
    <message name="NewOrder" id="1">
        <field name="orderId" id="1" type="uint64"/>
        <field name="symbol" id="2" type="Symbol"/>
        <field name="side" id="3" type="Side"/>
        <field name="price" id="4" type="Price"/>
        <field name="quantity" id="5" type="Qty"/>
    </message>
</sbe:messageSchema>
```

### 2.2 生成的代码使用

```cpp
// 编码
char buffer[256];
NewOrder order;
order.wrapForEncode(buffer, 0, sizeof(buffer))
    .orderId(12345)
    .symbol("AAPL    ")
    .side(Side::Buy)
    .price(15000)      // 定点数，150.00
    .quantity(100);

size_t encodedLength = order.encodedLength();

// 解码（零拷贝）
NewOrder decoded;
decoded.wrapForDecode(buffer, 0, 
    NewOrder::sbeBlockLength(),
    NewOrder::sbeSchemaVersion(),
    sizeof(buffer));

uint64_t orderId = decoded.orderId();  // 直接读取，无拷贝
auto side = decoded.side();
int64_t price = decoded.price();
```

### 2.3 SBE优化技巧

```cpp
// 1. 使用固定大小消息
// SBE消息头 + 固定字段 = 可预测的大小

// 2. 对齐访问
struct alignas(8) OrderMessage {
    // SBE生成的结构自动对齐
};

// 3. 批量处理
void process_batch(const char* buffer, size_t len) {
    size_t offset = 0;
    while (offset < len) {
        NewOrder msg;
        msg.wrapForDecode(buffer, offset, ...);
        
        process_order(msg);
        
        offset += msg.encodedLength();
    }
}

// 4. 预分配缓冲区
class OrderEncoder {
    alignas(64) char buffer_[256];  // 缓存行对齐
    NewOrder encoder_;
    
public:
    const char* encode(const OrderData& data) {
        encoder_.wrapForEncode(buffer_, 0, sizeof(buffer_));
        // ... 填充字段
        return buffer_;
    }
};
```

---

## 三、FlatBuffers

### 3.1 Schema定义

```flatbuffers
// trading.fbs
namespace Trading;

enum Side : byte { Buy = 0, Sell = 1 }

table Order {
    order_id: ulong;
    symbol: string;
    side: Side;
    price: long;
    quantity: uint;
    timestamp: ulong;
}

table MarketData {
    symbol: string;
    bid_price: long;
    ask_price: long;
    bid_size: uint;
    ask_size: uint;
    sequence: ulong;
}

root_type Order;
```

### 3.2 使用方法

```cpp
#include "trading_generated.h"

// 编码
flatbuffers::FlatBufferBuilder builder(256);

auto symbol = builder.CreateString("AAPL");
auto order = Trading::CreateOrder(builder,
    12345,          // order_id
    symbol,         // symbol
    Trading::Side_Buy,
    15000,          // price
    100,            // quantity
    get_timestamp()
);
builder.Finish(order);

// 获取编码后的数据
uint8_t* buf = builder.GetBufferPointer();
size_t size = builder.GetSize();

// 解码（零拷贝）
auto decoded = Trading::GetOrder(buf);
uint64_t orderId = decoded->order_id();
auto side = decoded->side();
const char* sym = decoded->symbol()->c_str();
```

### 3.3 FlatBuffers vs SBE

```cpp
// FlatBuffers优势：
// - 更灵活的schema（可变长字符串）
// - 更好的语言支持
// - 更易读的schema

// SBE优势：
// - 更低的编码延迟
// - 更小的编码大小
// - 更可预测的性能

// HFT选择：
// - 对外协议/存储：FlatBuffers
// - 内部热路径：SBE或自定义二进制
```

---

## 四、Cap'n Proto

### 4.1 Schema定义

```capnp
# trading.capnp
@0xdbb9ad1f14bf0b36;

enum Side {
    buy @0;
    sell @1;
}

struct Order {
    orderId @0 :UInt64;
    symbol @1 :Text;
    side @2 :Side;
    price @3 :Int64;
    quantity @4 :UInt32;
}

struct MarketData {
    symbol @0 :Text;
    bidPrice @1 :Int64;
    askPrice @2 :Int64;
    bidSize @3 :UInt32;
    askSize @4 :UInt32;
}
```

### 4.2 使用方法

```cpp
#include "trading.capnp.h"

// 编码
capnp::MallocMessageBuilder message;
auto order = message.initRoot<Order>();
order.setOrderId(12345);
order.setSymbol("AAPL");
order.setSide(Side::BUY);
order.setPrice(15000);
order.setQuantity(100);

auto serialized = capnp::messageToFlatArray(message);

// 解码
auto reader = capnp::FlatArrayMessageReader(serialized);
auto decoded = reader.getRoot<Order>();
uint64_t orderId = decoded.getOrderId();
```

---

## 五、零拷贝解析实现

### 5.1 自定义二进制协议

```cpp
// 最简单的零拷贝：固定布局结构体

#pragma pack(push, 1)
struct RawOrder {
    uint64_t order_id;
    char symbol[8];
    uint8_t side;
    int64_t price;
    uint32_t quantity;
    uint64_t timestamp;
};
#pragma pack(pop)

// 零拷贝解析
const RawOrder* parse(const char* buffer) {
    return reinterpret_cast<const RawOrder*>(buffer);
}

// 使用
void on_data(const char* buffer, size_t len) {
    const RawOrder* order = parse(buffer);
    
    // 直接访问字段，无任何拷贝
    process_order(order->order_id, 
                  order->price, 
                  order->quantity);
}
```

### 5.2 带消息头的协议

```cpp
struct MessageHeader {
    uint16_t msg_type;
    uint16_t msg_length;
    uint32_t sequence;
};

struct OrderMessage {
    MessageHeader header;
    uint64_t order_id;
    // ... 其他字段
};

class ZeroCopyParser {
public:
    void parse(const char* buffer, size_t len) {
        size_t offset = 0;
        
        while (offset + sizeof(MessageHeader) <= len) {
            auto* header = reinterpret_cast<const MessageHeader*>(
                buffer + offset);
            
            if (offset + header->msg_length > len) {
                // 不完整的消息
                break;
            }
            
            dispatch_message(header->msg_type, 
                           buffer + offset, 
                           header->msg_length);
            
            offset += header->msg_length;
        }
    }
    
private:
    void dispatch_message(uint16_t type, const char* data, size_t len) {
        switch (type) {
            case MSG_ORDER:
                handle_order(reinterpret_cast<const OrderMessage*>(data));
                break;
            // ...
        }
    }
};
```

---

## 六、性能对比

### 6.1 基准测试

```cpp
void benchmark() {
    const int iterations = 1000000;
    
    // 准备数据
    OrderData data = generate_order_data();
    
    // JSON
    auto start = rdtsc();
    for (int i = 0; i < iterations; i++) {
        std::string json = to_json(data);
        OrderData decoded = from_json(json);
    }
    auto json_cycles = rdtsc() - start;
    
    // Protobuf
    start = rdtsc();
    for (int i = 0; i < iterations; i++) {
        std::string proto;
        data.SerializeToString(&proto);
        OrderData decoded;
        decoded.ParseFromString(proto);
    }
    auto proto_cycles = rdtsc() - start;
    
    // SBE
    char buffer[256];
    start = rdtsc();
    for (int i = 0; i < iterations; i++) {
        encode_sbe(buffer, data);
        decode_sbe(buffer);
    }
    auto sbe_cycles = rdtsc() - start;
    
    printf("JSON:     %lu cycles/op\n", json_cycles / iterations);
    printf("Protobuf: %lu cycles/op\n", proto_cycles / iterations);
    printf("SBE:      %lu cycles/op\n", sbe_cycles / iterations);
}

// 典型结果：
// JSON:     50000 cycles/op (15μs)
// Protobuf: 1000 cycles/op (300ns)
// SBE:      100 cycles/op (30ns)
```

### 6.2 消息大小对比

```
相同的Order消息：

JSON:
{"orderId":12345,"symbol":"AAPL","side":"buy","price":15000,"quantity":100}
大小：75 bytes

Protobuf:
紧凑二进制
大小：30 bytes

SBE:
固定布局二进制
大小：32 bytes（包含填充）

FlatBuffers:
带元数据的二进制
大小：48 bytes
```

---

## 七、Schema演进

### 7.1 SBE版本控制

```xml
<!-- 版本1 -->
<message name="Order" id="1">
    <field name="orderId" id="1" type="uint64"/>
    <field name="price" id="2" type="int64"/>
</message>

<!-- 版本2：添加新字段 -->
<message name="Order" id="1">
    <field name="orderId" id="1" type="uint64"/>
    <field name="price" id="2" type="int64"/>
    <field name="quantity" id="3" type="uint32"/>  <!-- 新增 -->
</message>

<!-- 规则：
1. 只能在末尾添加字段
2. 不能修改现有字段
3. 使用sinceVersion标记新字段
-->
```

### 7.2 FlatBuffers兼容性

```flatbuffers
table Order {
    order_id: ulong;
    price: long;
    quantity: uint;      // 可以新增
    // 旧版本的reader会忽略新字段
    // 新版本的reader会给缺失字段默认值
}
```

---

## 总结

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| 极致延迟 | SBE/自定义 | 最低开销 |
| 灵活需求 | FlatBuffers | 平衡性能和灵活 |
| RPC通信 | Cap'n Proto | 内置RPC支持 |
| 存储/日志 | Protobuf | 压缩好，兼容性好 |

**最佳实践**：
1. 热路径使用零拷贝解析
2. 固定大小消息减少分支
3. 预分配缓冲区
4. 考虑缓存行对齐
5. 版本兼容性设计

---

## 相关文章

- [上一篇：全球主要交易所技术对比](@/articles/hft/hft-19-全球主要交易所技术对比.md)
- [下一篇：交易系统容错与恢复](@/articles/hft/hft-21-交易系统容错与恢复.md)
