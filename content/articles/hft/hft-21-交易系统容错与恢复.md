+++
title = "21.交易系统容错与恢复"
date = 2026-01-21
description = "深入剖析交易系统容错与恢复，包括热备/温备/冷备、主从切换、状态同步和订单恢复"
[taxonomies]
tags = ["HFT", "容错", "高可用", "恢复", "交易系统"]
+++

## 概述

交易系统的高可用性至关重要。本文深入讲解容错与恢复机制。

---

## 一、备份策略

### 1.1 热备/温备/冷备

```
┌──────────────────────────────────────────────────────────────┐
│                        备份模式对比                           │
├─────────────────┬────────────┬────────────┬─────────────────┤
│                 │   热备     │   温备     │   冷备          │
├─────────────────┼────────────┼────────────┼─────────────────┤
│ 状态同步        │ 实时       │ 近实时     │ 定期/手动       │
│ 切换时间        │ 秒级       │ 分钟级     │ 小时级          │
│ 资源消耗        │ 高         │ 中         │ 低              │
│ 数据丢失风险    │ 极低       │ 低         │ 中              │
│ 成本            │ 高         │ 中         │ 低              │
│ 适用场景        │ 核心交易   │ 辅助系统   │ 灾难恢复        │
└─────────────────┴────────────┴────────────┴─────────────────┘
```

### 1.2 热备实现

```cpp
class HotStandby {
public:
    // 主节点：同步发送每个状态变更
    void on_state_change(const StateUpdate& update) {
        // 1. 本地应用
        apply_locally(update);
        
        // 2. 同步到备节点（同步或异步）
        if (sync_mode_) {
            if (!sync_to_standby(update)) {
                // 同步失败处理
                handle_sync_failure();
            }
        } else {
            async_queue_.push(update);
        }
    }
    
    // 备节点：接收并应用状态变更
    void on_receive_update(const StateUpdate& update) {
        // 验证序列号
        if (update.sequence != expected_seq_) {
            request_resync();
            return;
        }
        
        apply_locally(update);
        expected_seq_++;
        
        // 确认接收
        send_ack(update.sequence);
    }
    
private:
    bool sync_mode_ = true;  // true=同步复制
    uint64_t expected_seq_ = 0;
    LockFreeQueue<StateUpdate> async_queue_;
};
```

### 1.3 状态机复制

```cpp
// 基于状态机的复制
class ReplicatedStateMachine {
public:
    // 命令接口
    struct Command {
        uint64_t sequence;
        uint64_t timestamp;
        CommandType type;
        std::vector<uint8_t> payload;
    };
    
    // 主节点处理命令
    void submit_command(Command cmd) {
        // 分配序列号
        cmd.sequence = next_seq_++;
        
        // 持久化到日志
        wal_.append(cmd);
        
        // 复制到备节点
        replicate_to_standby(cmd);
        
        // 应用到状态机
        apply(cmd);
    }
    
    // 备节点应用命令
    void apply_replicated(const Command& cmd) {
        if (cmd.sequence != expected_seq_) {
            // Gap检测
            request_missing(expected_seq_, cmd.sequence - 1);
            buffer_command(cmd);
            return;
        }
        
        apply(cmd);
        expected_seq_++;
    }
    
private:
    void apply(const Command& cmd) {
        switch (cmd.type) {
            case NEW_ORDER:
                state_.add_order(deserialize<Order>(cmd.payload));
                break;
            case CANCEL_ORDER:
                state_.cancel_order(deserialize<uint64_t>(cmd.payload));
                break;
            // ...
        }
    }
    
    WriteAheadLog wal_;
    uint64_t next_seq_ = 1;
    uint64_t expected_seq_ = 1;
    TradingState state_;
};
```

---

## 二、主从切换

### 2.1 故障检测

```cpp
class FailureDetector {
public:
    enum class NodeState {
        HEALTHY,
        SUSPECTED,
        FAILED
    };
    
    void receive_heartbeat(const Heartbeat& hb) {
        last_heartbeat_ = std::chrono::steady_clock::now();
        state_ = NodeState::HEALTHY;
        suspected_count_ = 0;
    }
    
    void check() {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = now - last_heartbeat_;
        
        if (elapsed > failure_threshold_) {
            state_ = NodeState::FAILED;
            on_failure_detected();
        } else if (elapsed > suspect_threshold_) {
            state_ = NodeState::SUSPECTED;
            suspected_count_++;
            
            if (suspected_count_ >= max_suspect_count_) {
                state_ = NodeState::FAILED;
                on_failure_detected();
            }
        }
    }
    
private:
    void on_failure_detected() {
        // 通知切换模块
        failover_manager_.trigger_failover();
    }
    
    std::chrono::steady_clock::time_point last_heartbeat_;
    NodeState state_ = NodeState::HEALTHY;
    int suspected_count_ = 0;
    int max_suspect_count_ = 3;
    
    std::chrono::milliseconds suspect_threshold_{100};
    std::chrono::milliseconds failure_threshold_{500};
};
```

### 2.2 Failover流程

```cpp
class FailoverManager {
public:
    void trigger_failover() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (failover_in_progress_) return;
        failover_in_progress_ = true;
        
        log_info("Starting failover...");
        
        // 1. 停止接收新请求
        pause_new_requests();
        
        // 2. 等待进行中的请求完成
        drain_in_flight_requests();
        
        // 3. 确保状态同步
        ensure_state_synchronized();
        
        // 4. 切换角色
        switch_role();
        
        // 5. 恢复服务
        resume_service();
        
        failover_in_progress_ = false;
        log_info("Failover completed");
    }
    
private:
    void switch_role() {
        if (current_role_ == Role::PRIMARY) {
            // 主变备
            current_role_ = Role::STANDBY;
            disconnect_from_exchange();
        } else {
            // 备变主
            current_role_ = Role::PRIMARY;
            connect_to_exchange();
            recover_pending_orders();
        }
    }
    
    void recover_pending_orders() {
        // 查询交易所获取当前订单状态
        auto exchange_orders = query_exchange_orders();
        
        // 与本地状态对比
        for (const auto& order : local_orders_) {
            auto it = exchange_orders.find(order.id);
            
            if (it == exchange_orders.end()) {
                // 订单可能未发送成功，需要重发
                resend_order(order);
            } else if (it->second != order) {
                // 状态不一致，更新本地
                update_local_order(it->second);
            }
        }
    }
    
    std::mutex mutex_;
    bool failover_in_progress_ = false;
    Role current_role_ = Role::STANDBY;
};
```

### 2.3 脑裂处理

```cpp
// 使用Fencing防止脑裂
class FencingToken {
public:
    // 获取token时必须提供更高的epoch
    bool acquire(uint64_t epoch) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (epoch > current_epoch_) {
            current_epoch_ = epoch;
            holder_ = node_id_;
            return true;
        }
        
        return false;
    }
    
    // 操作前验证token
    bool validate(uint64_t epoch) {
        return epoch == current_epoch_ && holder_ == node_id_;
    }
    
private:
    std::mutex mutex_;
    uint64_t current_epoch_ = 0;
    std::string holder_;
    std::string node_id_;
};

// 交易所连接时使用fencing
class FencedExchangeConnection {
public:
    void send_order(const Order& order, uint64_t epoch) {
        if (!fencing_token_.validate(epoch)) {
            throw std::runtime_error("Invalid fencing token - possible split brain");
        }
        
        // 安全发送
        connection_.send(order);
    }
};
```

---

## 三、状态同步

### 3.1 Checkpoint机制

```cpp
class CheckpointManager {
public:
    void create_checkpoint() {
        auto checkpoint_id = ++checkpoint_id_;
        
        log_info("Creating checkpoint {}", checkpoint_id);
        
        // 1. 暂停状态修改
        state_lock_.write_lock();
        
        // 2. 序列化当前状态
        std::vector<uint8_t> snapshot = serialize_state();
        
        // 3. 恢复状态修改
        state_lock_.write_unlock();
        
        // 4. 持久化快照
        save_snapshot(checkpoint_id, snapshot);
        
        // 5. 记录对应的WAL位置
        uint64_t wal_position = wal_.current_position();
        save_checkpoint_metadata(checkpoint_id, wal_position);
        
        // 6. 清理旧checkpoint
        cleanup_old_checkpoints();
    }
    
    void restore_from_checkpoint(uint64_t checkpoint_id) {
        // 1. 加载快照
        auto snapshot = load_snapshot(checkpoint_id);
        
        // 2. 反序列化状态
        deserialize_state(snapshot);
        
        // 3. 获取WAL位置
        auto wal_position = load_checkpoint_metadata(checkpoint_id);
        
        // 4. 重放WAL
        replay_wal_from(wal_position);
        
        log_info("Restored from checkpoint {}", checkpoint_id);
    }
    
private:
    std::vector<uint8_t> serialize_state() {
        // 序列化所有状态
        // - 订单状态
        // - 仓位
        // - 风控计数器
        // ...
    }
    
    uint64_t checkpoint_id_ = 0;
    WriteAheadLog wal_;
    ReadWriteLock state_lock_;
};
```

### 3.2 增量同步

```cpp
class IncrementalSync {
public:
    // 主节点发送增量
    void send_incremental(const StateUpdate& update) {
        // 序列化更新
        auto serialized = serialize(update);
        
        // 发送给所有备节点
        for (auto& standby : standbys_) {
            standby.send(serialized);
        }
        
        // 记录发送位置
        last_sent_seq_ = update.sequence;
    }
    
    // 备节点接收增量
    void receive_incremental(const std::vector<uint8_t>& data) {
        auto update = deserialize<StateUpdate>(data);
        
        // 检查连续性
        if (update.sequence != expected_seq_) {
            if (update.sequence > expected_seq_) {
                // Gap，请求缺失的更新
                request_gap_fill(expected_seq_, update.sequence - 1);
                buffer_.push(update);
            }
            // else: 重复，忽略
            return;
        }
        
        apply_update(update);
        expected_seq_++;
        
        // 处理缓冲的更新
        drain_buffer();
    }
    
private:
    void request_gap_fill(uint64_t from, uint64_t to) {
        // 请求主节点重发缺失的更新
        primary_.request_resend(from, to);
    }
    
    uint64_t expected_seq_ = 1;
    uint64_t last_sent_seq_ = 0;
    std::priority_queue<StateUpdate> buffer_;
};
```

---

## 四、订单恢复

### 4.1 订单状态追踪

```cpp
class OrderStateTracker {
public:
    enum class OrderState {
        PENDING_SUBMIT,    // 待发送
        SUBMITTED,         // 已发送，等待确认
        ACKNOWLEDGED,      // 已确认
        PARTIALLY_FILLED,  // 部分成交
        FILLED,            // 完全成交
        PENDING_CANCEL,    // 待撤销
        CANCELLED,         // 已撤销
        REJECTED           // 被拒绝
    };
    
    struct OrderRecord {
        uint64_t order_id;
        uint64_t client_order_id;
        OrderState state;
        uint64_t submit_time;
        uint64_t ack_time;
        int64_t original_qty;
        int64_t filled_qty;
        int64_t remaining_qty;
    };
    
    void on_order_submit(const Order& order) {
        OrderRecord record;
        record.order_id = 0;  // 还没有交易所ID
        record.client_order_id = order.client_id;
        record.state = OrderState::PENDING_SUBMIT;
        record.submit_time = get_timestamp();
        record.original_qty = order.quantity;
        record.remaining_qty = order.quantity;
        
        pending_orders_[order.client_id] = record;
        persist(record);
    }
    
    void on_order_ack(uint64_t client_id, uint64_t exchange_id) {
        auto& record = pending_orders_[client_id];
        record.order_id = exchange_id;
        record.state = OrderState::ACKNOWLEDGED;
        record.ack_time = get_timestamp();
        
        active_orders_[exchange_id] = record;
        persist(record);
    }
    
    void on_fill(uint64_t exchange_id, int64_t fill_qty) {
        auto& record = active_orders_[exchange_id];
        record.filled_qty += fill_qty;
        record.remaining_qty -= fill_qty;
        
        if (record.remaining_qty == 0) {
            record.state = OrderState::FILLED;
            completed_orders_[exchange_id] = record;
            active_orders_.erase(exchange_id);
        } else {
            record.state = OrderState::PARTIALLY_FILLED;
        }
        
        persist(record);
    }
    
private:
    std::unordered_map<uint64_t, OrderRecord> pending_orders_;
    std::unordered_map<uint64_t, OrderRecord> active_orders_;
    std::unordered_map<uint64_t, OrderRecord> completed_orders_;
};
```

### 4.2 恢复流程

```cpp
class OrderRecovery {
public:
    void recover() {
        log_info("Starting order recovery...");
        
        // 1. 加载本地订单状态
        load_local_orders();
        
        // 2. 查询交易所订单状态
        auto exchange_orders = query_exchange_orders();
        
        // 3. 对比和修复
        reconcile(exchange_orders);
        
        // 4. 处理未确认的订单
        handle_unconfirmed_orders();
        
        log_info("Order recovery completed");
    }
    
private:
    void reconcile(const std::map<uint64_t, ExchangeOrder>& exchange_orders) {
        // 检查本地有但交易所没有的订单
        for (const auto& [id, local] : local_active_orders_) {
            auto it = exchange_orders.find(id);
            
            if (it == exchange_orders.end()) {
                // 订单可能已被撤销或成交
                log_warning("Order {} missing from exchange", id);
                mark_for_verification(id);
            } else {
                // 验证状态一致性
                verify_consistency(local, it->second);
            }
        }
        
        // 检查交易所有但本地没有的订单
        for (const auto& [id, exchange] : exchange_orders) {
            if (local_active_orders_.find(id) == local_active_orders_.end()) {
                log_warning("Unknown order {} from exchange", id);
                // 可能是failover期间发送的
                add_to_local(exchange);
            }
        }
    }
    
    void handle_unconfirmed_orders() {
        for (const auto& [client_id, order] : pending_orders_) {
            if (order.state == OrderState::PENDING_SUBMIT) {
                auto age = get_timestamp() - order.submit_time;
                
                if (age > confirmation_timeout_) {
                    // 超时未确认，需要决定是重发还是放弃
                    if (should_resend(order)) {
                        resend_order(order);
                    } else {
                        mark_as_failed(order);
                    }
                }
            }
        }
    }
    
    std::chrono::milliseconds confirmation_timeout_{5000};
};
```

---

## 五、序列号管理

### 5.1 Gap检测与填补

```cpp
class SequenceManager {
public:
    enum class GapAction {
        WAIT,       // 等待一段时间
        REQUEST,    // 请求重传
        RESET       // 请求完整快照
    };
    
    GapAction on_message(uint64_t sequence) {
        if (sequence == expected_seq_) {
            expected_seq_++;
            consecutive_gaps_ = 0;
            return GapAction::WAIT;  // 不需要任何动作
        }
        
        if (sequence < expected_seq_) {
            // 重复消息，忽略
            return GapAction::WAIT;
        }
        
        // Gap检测
        uint64_t gap_size = sequence - expected_seq_;
        consecutive_gaps_++;
        
        log_warning("Gap detected: expected {}, got {}, size {}",
                    expected_seq_, sequence, gap_size);
        
        // 决定处理策略
        if (gap_size > max_gap_size_ || consecutive_gaps_ > max_consecutive_gaps_) {
            return GapAction::RESET;
        }
        
        return GapAction::REQUEST;
    }
    
    void request_gap_fill(uint64_t from, uint64_t to) {
        GapRequest request;
        request.from_seq = from;
        request.to_seq = to;
        request.request_time = get_timestamp();
        
        pending_gaps_.push(request);
        send_gap_request(request);
    }
    
    void on_gap_filled(uint64_t sequence, const Message& msg) {
        if (sequence == expected_seq_) {
            process_message(msg);
            expected_seq_++;
            
            // 处理缓冲的消息
            drain_buffer();
        } else {
            buffer_[sequence] = msg;
        }
    }
    
private:
    uint64_t expected_seq_ = 1;
    uint64_t max_gap_size_ = 1000;
    int consecutive_gaps_ = 0;
    int max_consecutive_gaps_ = 10;
    std::map<uint64_t, Message> buffer_;
    std::queue<GapRequest> pending_gaps_;
};
```

---

## 总结

| 组件 | 目标 | 实现方式 |
|------|------|----------|
| 热备 | 秒级切换 | 同步复制 |
| 状态同步 | 数据一致 | WAL + Checkpoint |
| 故障检测 | 快速发现 | 心跳 + 超时 |
| 订单恢复 | 无丢失 | 查询 + 对账 |
| Gap填补 | 完整性 | 请求 + 缓冲 |

**最佳实践**：
1. 使用Write-Ahead Log确保持久性
2. 定期创建Checkpoint加速恢复
3. 实现多层故障检测
4. 自动化恢复流程
5. 定期进行灾难恢复演练

---

## 相关文章

- [上一篇：高性能序列化技术](/articles/hft/hft-20-高性能序列化技术/)
- [下一篇：HFT面试题-系统设计](/articles/hft/hft-22-HFT面试题-系统设计/)
