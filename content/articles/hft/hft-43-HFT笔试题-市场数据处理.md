+++
title = "43. HFT笔试题-市场数据处理"
date = 2026-02-02
weight = 43000
description = "HFT笔试：市场数据解析、增量更新、FAST解码、多源聚合"
[taxonomies]
tags = ["HFT", "笔试", "市场数据", "解析", "FAST"]
+++

# HFT 笔试题 - 市场数据处理

本文汇总 HFT 笔试中关于市场数据处理的编程题目。

---

## 题目 1：ITCH 消息解析

**题目**：实现 NASDAQ ITCH 协议的 Add Order 消息解析。

**解答**：

```cpp
#include <cstdint>
#include <cstring>
#include <arpa/inet.h>

// ITCH Add Order 消息结构
#pragma pack(push, 1)
struct ITCHAddOrder {
    char message_type;         // 'A'
    uint16_t stock_locate;
    uint16_t tracking_number;
    uint8_t timestamp[6];      // 纳秒时间戳
    uint64_t order_ref;
    char buy_sell;             // 'B' or 'S'
    uint32_t shares;
    char stock[8];
    uint32_t price;            // 价格 × 10000
};
#pragma pack(pop)

class ITCHParser {
public:
    struct ParsedOrder {
        uint64_t timestamp_ns;
        uint64_t order_ref;
        bool is_buy;
        uint32_t quantity;
        std::string symbol;
        double price;
    };
    
    ParsedOrder parse_add_order(const uint8_t* data, size_t len) {
        if (len < sizeof(ITCHAddOrder)) {
            throw std::runtime_error("Invalid message length");
        }
        
        const auto* msg = reinterpret_cast<const ITCHAddOrder*>(data);
        
        if (msg->message_type != 'A') {
            throw std::runtime_error("Not an Add Order message");
        }
        
        ParsedOrder order;
        
        // 解析 6 字节时间戳
        order.timestamp_ns = parse_timestamp(msg->timestamp);
        
        // 网络字节序转换
        order.order_ref = be64toh(msg->order_ref);
        order.is_buy = (msg->buy_sell == 'B');
        order.quantity = ntohl(msg->shares);
        
        // 股票代码（去除尾部空格）
        order.symbol = std::string(msg->stock, 8);
        order.symbol.erase(order.symbol.find_last_not_of(' ') + 1);
        
        // 价格转换
        order.price = ntohl(msg->price) / 10000.0;
        
        return order;
    }
    
private:
    uint64_t parse_timestamp(const uint8_t* ts) {
        uint64_t result = 0;
        for (int i = 0; i < 6; i++) {
            result = (result << 8) | ts[i];
        }
        return result;
    }
};

// 高性能解析：避免分支
class ITCHParserFast {
public:
    // 使用查表法确定消息类型和长度
    static constexpr uint8_t MSG_LENGTHS[256] = {
        ['A'] = 36,   // Add Order
        ['F'] = 40,   // Add Order MPID
        ['E'] = 31,   // Order Executed
        ['C'] = 36,   // Order Executed with Price
        ['X'] = 23,   // Order Cancel
        ['D'] = 19,   // Order Delete
        ['U'] = 35,   // Order Replace
        ['P'] = 44,   // Trade
        // ... 其他消息类型
    };
    
    size_t get_message_length(uint8_t type) const {
        return MSG_LENGTHS[type];
    }
    
    // 批量解析
    size_t parse_batch(const uint8_t* data, size_t len,
                       std::vector<ParsedOrder>& orders) {
        size_t offset = 0;
        
        while (offset < len) {
            uint8_t msg_type = data[offset];
            size_t msg_len = MSG_LENGTHS[msg_type];
            
            if (msg_len == 0 || offset + msg_len > len) {
                break;
            }
            
            if (msg_type == 'A' || msg_type == 'F') {
                orders.push_back(parse_add_order_fast(data + offset));
            }
            
            offset += msg_len;
        }
        
        return offset;
    }
};
```

---

## 题目 2：增量更新处理

**题目**：实现订单簿的增量更新处理，包括序列号检查和丢包恢复。

**解答**：

```cpp
class IncrementalBookBuilder {
public:
    enum class UpdateResult {
        Applied,
        OutOfSequence,
        Duplicate,
        GapDetected
    };
    
    struct BookUpdate {
        uint64_t sequence;
        enum Action { Add, Modify, Delete } action;
        Side side;
        double price;
        int quantity;
    };
    
    UpdateResult apply_update(const BookUpdate& update) {
        // 检查序列号
        if (update.sequence < expected_sequence_) {
            return UpdateResult::Duplicate;
        }
        
        if (update.sequence > expected_sequence_) {
            // 检测到丢包
            pending_updates_[update.sequence] = update;
            
            if (!recovery_in_progress_) {
                request_recovery(expected_sequence_, update.sequence);
            }
            
            return UpdateResult::GapDetected;
        }
        
        // 正常处理
        apply_to_book(update);
        expected_sequence_++;
        
        // 尝试应用缓存的更新
        apply_pending_updates();
        
        return UpdateResult::Applied;
    }
    
    void apply_snapshot(const BookSnapshot& snapshot) {
        // 重置订单簿
        book_.clear();
        
        for (const auto& level : snapshot.bids) {
            book_.set_bid_level(level.price, level.quantity);
        }
        for (const auto& level : snapshot.asks) {
            book_.set_ask_level(level.price, level.quantity);
        }
        
        expected_sequence_ = snapshot.sequence + 1;
        recovery_in_progress_ = false;
        
        apply_pending_updates();
    }
    
private:
    void apply_to_book(const BookUpdate& update) {
        if (update.side == Side::Buy) {
            switch (update.action) {
                case BookUpdate::Add:
                case BookUpdate::Modify:
                    book_.set_bid_level(update.price, update.quantity);
                    break;
                case BookUpdate::Delete:
                    book_.remove_bid_level(update.price);
                    break;
            }
        } else {
            // 类似处理卖盘
        }
    }
    
    void apply_pending_updates() {
        while (!pending_updates_.empty()) {
            auto it = pending_updates_.find(expected_sequence_);
            if (it == pending_updates_.end()) break;
            
            apply_to_book(it->second);
            pending_updates_.erase(it);
            expected_sequence_++;
        }
    }
    
    void request_recovery(uint64_t from, uint64_t to) {
        recovery_in_progress_ = true;
        // 发起快照请求或重传请求
        recovery_callback_(from, to);
    }
    
    OrderBook book_;
    uint64_t expected_sequence_ = 1;
    std::map<uint64_t, BookUpdate> pending_updates_;
    bool recovery_in_progress_ = false;
    std::function<void(uint64_t, uint64_t)> recovery_callback_;
};
```

---

## 题目 3：多源数据聚合

**题目**：实现多交易所行情数据的聚合，计算 NBBO。

**解答**：

```cpp
class NBBOAggregator {
public:
    struct VenueQuote {
        double bid;
        double ask;
        int bid_size;
        int ask_size;
        uint64_t timestamp;
        bool valid;
    };
    
    struct NBBO {
        double best_bid;
        double best_ask;
        int best_bid_size;
        int best_ask_size;
        std::string bid_venue;
        std::string ask_venue;
        uint64_t timestamp;
    };
    
    void update_venue(const std::string& venue, const VenueQuote& quote) {
        quotes_[venue] = quote;
        recalculate_nbbo();
    }
    
    void remove_venue(const std::string& venue) {
        quotes_.erase(venue);
        recalculate_nbbo();
    }
    
    const NBBO& get_nbbo() const {
        return nbbo_;
    }
    
    // 检查报价是否优于 NBBO
    bool is_better_bid(double price) const {
        return price > nbbo_.best_bid;
    }
    
    bool is_better_ask(double price) const {
        return price < nbbo_.best_ask;
    }
    
private:
    void recalculate_nbbo() {
        nbbo_.best_bid = 0;
        nbbo_.best_ask = std::numeric_limits<double>::max();
        nbbo_.best_bid_size = 0;
        nbbo_.best_ask_size = 0;
        nbbo_.bid_venue.clear();
        nbbo_.ask_venue.clear();
        
        uint64_t latest_ts = 0;
        
        for (const auto& [venue, quote] : quotes_) {
            if (!quote.valid) continue;
            
            // 更新最优买价
            if (quote.bid > nbbo_.best_bid) {
                nbbo_.best_bid = quote.bid;
                nbbo_.best_bid_size = quote.bid_size;
                nbbo_.bid_venue = venue;
            } else if (quote.bid == nbbo_.best_bid) {
                nbbo_.best_bid_size += quote.bid_size;
            }
            
            // 更新最优卖价
            if (quote.ask < nbbo_.best_ask) {
                nbbo_.best_ask = quote.ask;
                nbbo_.best_ask_size = quote.ask_size;
                nbbo_.ask_venue = venue;
            } else if (quote.ask == nbbo_.best_ask) {
                nbbo_.best_ask_size += quote.ask_size;
            }
            
            latest_ts = std::max(latest_ts, quote.timestamp);
        }
        
        nbbo_.timestamp = latest_ts;
    }
    
    std::unordered_map<std::string, VenueQuote> quotes_;
    NBBO nbbo_;
};
```

---

## 题目 4：FAST 解码优化

**题目**：实现 FAST 协议的 Presence Map 和字段解码。

**解答**：

```cpp
class FASTDecoder {
public:
    // Presence Map 解码
    class PresenceMap {
    public:
        void decode(const uint8_t*& data) {
            bits_ = 0;
            bit_count_ = 0;
            
            // FAST 使用停止位编码
            do {
                uint8_t byte = *data++;
                bits_ = (bits_ << 7) | (byte & 0x7F);
                bit_count_ += 7;
            } while ((*((data) - 1) & 0x80) == 0);
            
            current_bit_ = bit_count_ - 1;
        }
        
        bool next_bit() {
            if (current_bit_ < 0) return false;
            bool result = (bits_ >> current_bit_) & 1;
            current_bit_--;
            return result;
        }
        
    private:
        uint64_t bits_ = 0;
        int bit_count_ = 0;
        int current_bit_ = 0;
    };
    
    // 解码无符号整数
    uint64_t decode_uint(const uint8_t*& data) {
        uint64_t result = 0;
        
        while (true) {
            uint8_t byte = *data++;
            result = (result << 7) | (byte & 0x7F);
            
            if (byte & 0x80) {
                break;  // 停止位
            }
        }
        
        return result;
    }
    
    // 解码有符号整数
    int64_t decode_int(const uint8_t*& data) {
        int64_t result = 0;
        bool negative = false;
        bool first = true;
        
        while (true) {
            uint8_t byte = *data++;
            
            if (first) {
                negative = (byte & 0x40) != 0;
                result = negative ? -1 : 0;
                result = (result << 7) | (byte & 0x7F);
                first = false;
            } else {
                result = (result << 7) | (byte & 0x7F);
            }
            
            if (byte & 0x80) {
                break;
            }
        }
        
        return result;
    }
    
    // 解码 ASCII 字符串
    std::string decode_ascii(const uint8_t*& data) {
        std::string result;
        
        while (true) {
            uint8_t byte = *data++;
            result += (byte & 0x7F);
            
            if (byte & 0x80) {
                break;
            }
        }
        
        return result;
    }
    
    // 解码定点小数（Decimal）
    struct Decimal {
        int64_t mantissa;
        int8_t exponent;
        
        double to_double() const {
            return mantissa * std::pow(10.0, exponent);
        }
    };
    
    Decimal decode_decimal(const uint8_t*& data) {
        Decimal result;
        result.exponent = decode_int(data);
        result.mantissa = decode_int(data);
        return result;
    }
};

// 带模板的增量解码
template<typename T>
class IncrementalField {
public:
    void set_previous(T value) { previous_ = value; has_previous_ = true; }
    
    T decode_copy(const uint8_t*& data, bool present) {
        if (!present) {
            return previous_;  // 使用前值
        }
        T value = decode<T>(data);
        previous_ = value;
        return value;
    }
    
    T decode_delta(const uint8_t*& data, bool present) {
        if (!present) {
            return previous_;
        }
        T delta = decode<T>(data);
        T value = previous_ + delta;
        previous_ = value;
        return value;
    }
    
private:
    T previous_ = T{};
    bool has_previous_ = false;
};
```

---

## 题目 5：时间戳对齐

**题目**：实现不同交易所时间戳的对齐和校准。

**解答**：

```cpp
class TimestampAligner {
public:
    struct ClockOffset {
        int64_t offset_ns;        // 偏移量
        int64_t uncertainty_ns;    // 不确定性
        uint64_t last_update;
    };
    
    void calibrate(const std::string& venue, 
                   uint64_t local_send_time,
                   uint64_t venue_time,
                   uint64_t local_recv_time) {
        // RTT / 2 估计单向延迟
        int64_t rtt = local_recv_time - local_send_time;
        int64_t one_way = rtt / 2;
        
        // 估计偏移 = venue_time - (local_send_time + one_way)
        int64_t offset = venue_time - (local_send_time + one_way);
        
        auto& clock = clock_offsets_[venue];
        
        // 指数移动平均平滑
        if (clock.last_update > 0) {
            clock.offset_ns = (clock.offset_ns * 9 + offset) / 10;
        } else {
            clock.offset_ns = offset;
        }
        
        clock.uncertainty_ns = rtt / 2;  // 不确定性 = RTT/2
        clock.last_update = local_recv_time;
    }
    
    // 将交易所时间戳转换为本地时间
    uint64_t to_local_time(const std::string& venue, uint64_t venue_time) {
        auto it = clock_offsets_.find(venue);
        if (it == clock_offsets_.end()) {
            return venue_time;  // 未校准
        }
        return venue_time - it->second.offset_ns;
    }
    
    // 将本地时间转换为交易所时间
    uint64_t to_venue_time(const std::string& venue, uint64_t local_time) {
        auto it = clock_offsets_.find(venue);
        if (it == clock_offsets_.end()) {
            return local_time;
        }
        return local_time + it->second.offset_ns;
    }
    
    // 比较两个交易所的时间戳
    int64_t compare_timestamps(const std::string& venue1, uint64_t ts1,
                               const std::string& venue2, uint64_t ts2) {
        uint64_t local1 = to_local_time(venue1, ts1);
        uint64_t local2 = to_local_time(venue2, ts2);
        return local1 - local2;
    }
    
private:
    std::unordered_map<std::string, ClockOffset> clock_offsets_;
};
```

---

## 题目 6：行情压缩存储

**题目**：实现历史行情的压缩存储。

**解答**：

```cpp
class TickDataCompressor {
public:
    struct Tick {
        uint64_t timestamp;
        double price;
        int quantity;
        Side side;
    };
    
    // Delta 编码压缩
    std::vector<uint8_t> compress(const std::vector<Tick>& ticks) {
        std::vector<uint8_t> output;
        
        if (ticks.empty()) return output;
        
        // 写入第一个完整 tick
        write_full_tick(output, ticks[0]);
        
        // Delta 编码后续 tick
        for (size_t i = 1; i < ticks.size(); i++) {
            write_delta_tick(output, ticks[i-1], ticks[i]);
        }
        
        return output;
    }
    
    std::vector<Tick> decompress(const std::vector<uint8_t>& data) {
        std::vector<Tick> ticks;
        const uint8_t* ptr = data.data();
        const uint8_t* end = ptr + data.size();
        
        if (ptr >= end) return ticks;
        
        // 读取第一个完整 tick
        ticks.push_back(read_full_tick(ptr));
        
        // 读取 delta tick
        while (ptr < end) {
            ticks.push_back(read_delta_tick(ptr, ticks.back()));
        }
        
        return ticks;
    }
    
private:
    void write_full_tick(std::vector<uint8_t>& out, const Tick& tick) {
        write_varint(out, tick.timestamp);
        write_fixed(out, tick.price);
        write_varint(out, tick.quantity);
        out.push_back(static_cast<uint8_t>(tick.side));
    }
    
    void write_delta_tick(std::vector<uint8_t>& out, 
                         const Tick& prev, const Tick& curr) {
        // 时间戳 delta（通常很小）
        write_varint(out, curr.timestamp - prev.timestamp);
        
        // 价格 delta（定点数）
        int64_t price_delta = static_cast<int64_t>(
            (curr.price - prev.price) * 10000);
        write_zigzag(out, price_delta);
        
        // 数量 delta
        write_zigzag(out, curr.quantity - prev.quantity);
        
        // Side（1 bit）
        out.push_back(static_cast<uint8_t>(curr.side));
    }
    
    // ZigZag 编码（将有符号数转为无符号）
    void write_zigzag(std::vector<uint8_t>& out, int64_t value) {
        uint64_t encoded = (value << 1) ^ (value >> 63);
        write_varint(out, encoded);
    }
    
    void write_varint(std::vector<uint8_t>& out, uint64_t value) {
        while (value > 0x7F) {
            out.push_back((value & 0x7F) | 0x80);
            value >>= 7;
        }
        out.push_back(value & 0x7F);
    }
    
    void write_fixed(std::vector<uint8_t>& out, double value) {
        const uint8_t* bytes = reinterpret_cast<const uint8_t*>(&value);
        out.insert(out.end(), bytes, bytes + sizeof(double));
    }
};
```

---

## 相关文章

- [FAST协议详解](@/articles/hft/hft-03-FAST协议详解.md)
- [ITCH与OUCH协议详解](@/articles/hft/hft-04-ITCH与OUCH协议详解.md)
- [数据采集层设计](@/articles/hft/hft-05-数据采集层设计.md)
