+++
title = "08. UDP与可靠UDP"
date = 2026-01-19
weight = 8000
description = "UDP协议详解：UDP特性与应用场景、可靠UDP实现方案、QUIC协议、KCP等"
[taxonomies]
tags = ["网络", "UDP", "QUIC"]
+++

## UDP概述

### UDP特性

**用户数据报协议（User Datagram Protocol）**：

| 特性 | 描述 |
|------|------|
| 无连接 | 无需建立连接，直接发送 |
| 不可靠 | 不保证到达、不保证顺序 |
| 无拥塞控制 | 不会降速，可能加剧网络拥塞 |
| 低开销 | 头部仅8字节 |
| 支持广播/多播 | TCP不支持 |

### UDP头部结构

```
 0      7 8     15 16    23 24    31
+--------+--------+--------+--------+
|     Source      |   Destination   |
|      Port       |      Port       |
+--------+--------+--------+--------+
|     Length      |    Checksum     |
+--------+--------+--------+--------+
|          Data octets ...          |
+-----------------------------------+
```

仅8字节头部，相比TCP的20字节极其精简。

### UDP适用场景

**适合UDP的场景**：
- 实时音视频（延迟敏感，丢包可容忍）
- 在线游戏（低延迟优先）
- DNS查询（简单请求响应）
- 物联网（资源受限设备）
- 广播/多播应用

**不适合UDP的场景**：
- 文件传输（需要完整性）
- 金融交易（需要可靠性）
- Web应用（除非使用QUIC）

---

## UDP编程

### 基本模型

**服务端**：
```
socket() → bind() → recvfrom() → sendto() → close()
```

**客户端**：
```
socket() → sendto() → recvfrom() → close()
```

### 关键注意点

**消息边界**：
- UDP保留消息边界
- 发送一次 = 接收一次
- 与TCP的字节流不同

**最大数据报大小**：
- 理论最大：65535 - 8(UDP头) - 20(IP头) = 65507字节
- 实际建议：不超过MTU（通常1500 - 28 = 1472字节）
- 超过MTU会IP分片，增加丢包概率

**校验和**：
- IPv4中可选，IPv6中必须
- 建议始终启用

---

## 为什么需要可靠UDP

### TCP的问题

**队头阻塞（Head-of-Line Blocking）**：
```
发送：包1、包2、包3
包2丢失
接收：必须等包2重传后才能处理包3
```

**连接建立开销**：
- 三次握手需要1.5 RTT
- TLS握手额外1-2 RTT

**移动网络问题**：
- IP变化导致连接中断
- 需要重新建立连接

### 可靠UDP的优势

- **无队头阻塞**：流之间独立
- **快速建立**：0-RTT或1-RTT
- **连接迁移**：IP变化不中断
- **自定义拥塞控制**：针对场景优化

---

## 可靠UDP实现方案

### 方案一：应用层实现

**核心机制**：
1. 序列号：标识每个包
2. 确认机制：ACK确认收到
3. 重传机制：超时或NACK重传
4. 排序：按序列号重组

**简化伪代码**：
```python
class ReliableUDP:
    def send(self, data):
        seq = self.next_seq()
        packet = Packet(seq, data)
        self.send_buffer[seq] = packet
        self.socket.sendto(packet.encode())
        self.start_timer(seq)
    
    def on_receive(self, packet):
        if packet.is_ack:
            self.handle_ack(packet.ack_seq)
        else:
            self.send_ack(packet.seq)
            self.deliver_in_order(packet)
    
    def on_timeout(self, seq):
        if seq in self.send_buffer:
            self.retransmit(seq)
```

### 方案二：KCP协议

**KCP特点**：
- 纯算法实现，不依赖底层协议
- 比TCP快30%-40%（牺牲10%-20%带宽）
- 可配置参数丰富

**核心优化**：
- **更快的重传**：RTO不翻倍增长
- **选择性重传**：只重传丢失的包
- **快速确认**：不等待延迟ACK
- **非退让流控**：可配置是否公平

**适用场景**：
- 游戏同步
- 实时对战
- 远程桌面

### 方案三：QUIC协议

**QUIC（Quick UDP Internet Connections）**：
- Google开发，现为HTTP/3基础
- 基于UDP实现可靠传输

**主要特性**：
- **0-RTT连接**：首次1-RTT，后续0-RTT
- **多路复用**：无队头阻塞
- **连接迁移**：基于Connection ID
- **内置加密**：TLS 1.3集成
- **改进的拥塞控制**：可插拔算法

---

## QUIC协议详解

### QUIC vs TCP+TLS

| 特性 | TCP+TLS | QUIC |
|------|---------|------|
| 握手延迟 | 2-3 RTT | 0-1 RTT |
| 队头阻塞 | 有 | 无（流级别） |
| 连接迁移 | 不支持 | 支持 |
| 加密 | 可选 | 强制 |
| 协议更新 | 需内核升级 | 用户态实现 |

### QUIC连接建立

**首次连接（1-RTT）**：
```
客户端                          服务端
  |                               |
  |  -- Initial(ClientHello) ---> |
  |                               |
  |  <-- Initial(ServerHello) --- |
  |  <-- Handshake(Cert...) ----- |
  |                               |
  |  -- Handshake(Finished) ----> |
  |  -- 1-RTT(Application) -----> |
```

**后续连接（0-RTT）**：
```
客户端                          服务端
  |                               |
  |  -- Initial + 0-RTT(Data) --> |  直接发送数据
  |                               |
  |  <-- Initial + 1-RTT(Data) -- |
```

### 多路复用

```
QUIC连接
  ├── Stream 1: HTTP请求1
  ├── Stream 2: HTTP请求2
  └── Stream 3: HTTP请求3
  
Stream 2丢包只阻塞Stream 2
Stream 1和3正常处理
```

### 连接迁移

传统TCP：
```
WiFi(IP-A) → 4G(IP-B) = 连接断开，重新建立
```

QUIC：
```
WiFi(IP-A) → 4G(IP-B) = 连接继续（Connection ID不变）
```

---

## 可靠UDP选型

### 选型对比

| 方案 | 复杂度 | 性能 | 功能 | 适用场景 |
|------|--------|------|------|----------|
| 自研 | 高 | 可控 | 自定义 | 特殊需求 |
| KCP | 中 | 高 | 基础可靠 | 游戏、实时应用 |
| QUIC | 低 | 高 | 完整 | Web、通用应用 |
| UDT | 中 | 高 | 大文件传输 | 科学数据传输 |

### 选型建议

**选择QUIC**：
- Web应用（HTTP/3）
- 需要TLS加密
- 希望标准化方案

**选择KCP**：
- 游戏开发
- 需要极致低延迟
- 可以牺牲带宽换延迟

**自研**：
- 非常特殊的需求
- 有足够的开发资源
- 需要完全控制

---

## 实现注意事项

### 拥塞控制

即使是UDP，也应该实现拥塞控制：
- 避免网络拥塞
- 公平共享带宽
- 很多网络会限制不友好流量

### 安全考虑

**放大攻击防护**：
- 首包不能太小（验证源IP）
- 响应不能比请求大太多

**连接验证**：
- Address Validation
- Retry Token

### MTU发现

**PMTUD（Path MTU Discovery）**：
- 发现路径最大MTU
- 避免IP分片
- 提高传输效率

---

## 总结

| 协议 | 可靠性 | 延迟 | 开销 | 复杂度 |
|------|--------|------|------|--------|
| TCP | 可靠 | 较高 | 较高 | 低 |
| UDP | 不可靠 | 低 | 低 | 低 |
| KCP | 可靠 | 低 | 中 | 中 |
| QUIC | 可靠 | 低 | 中 | 低（用库） |

**选择原则**：
- 大部分场景：TCP或QUIC
- 实时性要求高：KCP或QUIC
- 简单广播：纯UDP
- 特殊需求：自研可靠UDP

---

## 相关文章

- [上一篇：TCP协议详解](@/articles/networking/net-07-TCP协议详解.md)
- [下一篇：多播与组播技术](@/articles/networking/net-09-多播与组播技术.md)
