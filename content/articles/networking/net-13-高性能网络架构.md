+++
title = "13. 高性能网络架构"
date = 2026-01-19
weight = 13000
description = "高性能网络设计：负载均衡、CDN、网络加速、零拷贝、内核旁路技术"
[taxonomies]
tags = ["网络", "高性能", "架构"]
+++

## 负载均衡

### 负载均衡层次

| 层次 | 技术 | 特点 |
|------|------|------|
| L4 | LVS、F5 | 基于IP和端口，性能高 |
| L7 | Nginx、HAProxy | 基于应用层，功能丰富 |
| DNS | DNS轮询 | 简单，但不够智能 |

### LVS（Linux Virtual Server）

**工作模式**：

**NAT模式**：
```
客户端 → LVS(DNAT) → 后端服务器
         ↑ (SNAT)  ←
```
- 请求和响应都经过LVS
- 后端服务器网关指向LVS
- LVS容易成为瓶颈

**DR模式（Direct Routing）**：
```
客户端 → LVS → 后端服务器
         ↑       ↓
         +←------+ (直接响应)
```
- 请求经过LVS，响应直接返回
- 后端服务器需要配置VIP
- 性能最好，最常用

**TUN模式**：
```
客户端 → LVS → (IP隧道) → 后端服务器
         ↑                    ↓
         +←------------------+
```
- 通过IP隧道转发
- 可跨网段

### 负载均衡算法

| 算法 | 描述 | 适用场景 |
|------|------|----------|
| 轮询(RR) | 依次分配 | 后端性能相同 |
| 加权轮询(WRR) | 按权重分配 | 后端性能不同 |
| 最少连接(LC) | 分配给连接最少的 | 长连接场景 |
| 源地址哈希 | 同一源IP到同一后端 | 会话保持 |
| 一致性哈希 | 减少节点变化影响 | 缓存场景 |

### 健康检查

```
upstream backend {
    server 192.168.1.1:8080 weight=5;
    server 192.168.1.2:8080 weight=3;
    server 192.168.1.3:8080 backup;
    
    health_check interval=5s fails=3 passes=2;
}
```

---

## CDN

### CDN原理

**Content Delivery Network**：将内容缓存到离用户更近的节点

```
用户 → DNS解析 → CDN节点（就近）→ 命中缓存 → 返回
                      ↓ 未命中
                   回源 → 源站
```

### CDN调度

**DNS调度**：
```
用户DNS查询 → CDN DNS → 返回就近节点IP
```

**HTTP重定向**：
```
请求 → 调度服务器 → 302重定向到最优节点
```

**Anycast**：
```
多个节点使用同一IP，路由协议选择最近的
```

### 缓存策略

**缓存控制头**：
```
Cache-Control: max-age=86400
Cache-Control: no-cache
Cache-Control: private
```

**缓存键**：
```
URL + 查询参数 + Headers(Vary)
```

**缓存刷新**：
- 主动刷新（Purge）
- 预热（Prefetch）
- TTL过期

---

## 网络加速技术

### TCP加速

**问题**：高延迟网络TCP性能差

**解决方案**：

**BBR拥塞控制**：
- 基于带宽和RTT建模
- 不依赖丢包反馈
- 高延迟网络表现优异

```bash
sysctl -w net.ipv4.tcp_congestion_control=bbr
```

**TCP Fast Open**：
- 首次握手后保存Cookie
- 后续连接携带Cookie+数据
- 减少1个RTT

```bash
sysctl -w net.ipv4.tcp_fastopen=3
```

### QUIC协议

**优势**：
- 0-RTT连接建立
- 多路复用无队头阻塞
- 连接迁移
- 内置加密

**应用**：
- HTTP/3
- Google服务
- 国内CDN厂商

### WAN优化

**技术**：
- 数据去重
- 压缩
- 协议优化
- 缓存

**产品**：
- Riverbed
- Cisco WAAS
- Silver Peak

---

## 零拷贝技术

### 传统数据传输

```
读文件发送网络：
1. read(): 磁盘 → 内核缓冲区 → 用户缓冲区
2. write(): 用户缓冲区 → 内核缓冲区 → 网卡

4次拷贝，4次上下文切换
```

### sendfile

```c
sendfile(socket_fd, file_fd, offset, count);
```

```
1. 磁盘 → 内核缓冲区
2. 内核缓冲区 → Socket缓冲区
3. Socket缓冲区 → 网卡

3次拷贝（支持DMA则2次），2次上下文切换
```

### mmap

```c
addr = mmap(file_fd, ...);
write(socket_fd, addr, len);
```

```
1. 磁盘 → 内核缓冲区（用户态可访问）
2. 内核缓冲区 → Socket缓冲区
3. Socket缓冲区 → 网卡

共享内存，减少拷贝
```

### splice

```c
splice(file_fd, pipe_fd, ...);
splice(pipe_fd, socket_fd, ...);
```

纯内核态数据移动，适用于代理场景。

---

## 内核旁路技术

### 为什么需要内核旁路

**传统网络栈开销**：
- 系统调用开销
- 数据拷贝
- 协议栈处理
- 中断处理

**高性能场景需求**：
- 10Gbps、100Gbps网络
- 低延迟要求（微秒级）
- 高PPS要求（百万级）

### DPDK

**Data Plane Development Kit**：
- 用户态网络驱动
- 轮询模式（无中断）
- 大页内存
- CPU亲和性

```
传统：网卡 → 内核 → 用户态应用
DPDK：网卡 → DPDK PMD → 用户态应用
```

**应用场景**：
- 软件路由器
- 防火墙
- 负载均衡器
- 网络功能虚拟化（NFV）

### XDP/eBPF

**eXpress Data Path**：
- 在网卡驱动层执行BPF程序
- 比iptables快10倍
- 可编程性强

**处理位置**：
```
网卡 → XDP(丢弃/转发/传递) → 内核协议栈 → 应用
```

**应用场景**：
- DDoS防护
- 负载均衡
- 流量采样

### AF_XDP

**XDP与用户态的高性能接口**：
- 比DPDK更灵活
- 可与内核协同
- 零拷贝

### RDMA

**Remote Direct Memory Access**：
- 绕过CPU，网卡直接访问内存
- 超低延迟（微秒级）
- 高带宽

**技术**：
- InfiniBand
- RoCE（RDMA over Converged Ethernet）
- iWARP

**应用**：
- 高性能计算
- 分布式存储
- 高频交易

---

## 高性能网络实践

### 高并发服务器

**架构**：
```
客户端 → LVS(DR) → Nginx集群 → 应用服务器
              ↓
           健康检查
```

**优化点**：
- epoll事件驱动
- 连接池复用
- 异步非阻塞IO
- 零拷贝发送

### 低延迟交易系统

**架构**：
```
行情源 → 多播 → 策略引擎 → 交易网关
              (DPDK)     (RDMA)
```

**优化点**：
- 内核旁路
- CPU绑定
- 网卡调优
- 时间同步

### CDN边缘节点

**架构**：
```
用户 → Anycast → 边缘节点(Nginx+缓存) → 回源
                     (sendfile)
```

**优化点**：
- 就近接入
- 内存缓存
- 零拷贝
- HTTP/3

---

## 总结

| 技术 | 层次 | 收益 |
|------|------|------|
| 负载均衡 | L4/L7 | 水平扩展 |
| CDN | 应用 | 降低延迟 |
| TCP优化 | 传输 | 提升吞吐 |
| 零拷贝 | 内核 | 减少CPU |
| DPDK | 驱动 | 极致性能 |
| XDP/eBPF | 驱动 | 可编程高性能 |
| RDMA | 硬件 | 超低延迟 |

**选择原则**：
- 大部分场景：优化内核参数 + 应用优化即可
- 高性能要求：考虑零拷贝、XDP
- 极致性能：DPDK、RDMA

---

## 相关文章

- [上一篇：网络虚拟化技术](@/articles/networking/net-12-网络虚拟化技术.md)
- [下一篇：HTTP协议详解](@/articles/networking/net-14-HTTP协议详解.md)
