+++
title = "02.Networking Concepts"
description = "网络核心概念速查：二层三层基础(MAC/ARP/VLAN/STP/VXLAN)、TCP/IP、Socket编程、高性能网络、数据中心架构(大二层/大三层/VXLAN/BGP EVPN/SDN)等关键概念详解"
date = 2026-01-27
draft = false
[taxonomies]
tags = ["Glossary", "Networking", "TCP", "UDP", "VLAN", "STP", "VXLAN", "EVPN", "SDN", "DataCenter", "Reference"]
+++

# Networking Concepts

本索引收录网络编程的核心概念，涵盖协议、Socket编程、高性能网络技术等。

---

## 零、二层三层网络基础

> 详细文章：[二层三层网络基础详解](/articles/networking/net-22-二层三层网络基础详解/)

### 0.1 MAC 地址

**定义**：Media Access Control 地址，网卡的唯一标识符，48位（6字节）。

```
格式: 00:1A:2B:3C:4D:5E
      └─OUI─┘└─设备ID─┘
      (厂商)  (唯一编号)

特殊地址:
● 广播 MAC: FF:FF:FF:FF:FF:FF (发给所有设备)
● 组播 MAC: 首字节最低位为 1
```

---

### 0.2 ARP (Address Resolution Protocol)

**定义**：地址解析协议，将 IP 地址解析为 MAC 地址。

```
场景: 主机A 想发数据给 192.168.1.100，但不知道 MAC

流程:
1. A 广播 ARP 请求: "谁是 192.168.1.100?"
2. 目标主机单播回复: "我是，MAC 是 xx:xx:xx:xx:xx:xx"
3. A 缓存结果，发送数据

关键点:
● ARP 只在同一二层网络内工作
● 跨网段时，ARP 解析的是网关的 MAC，不是目标的
```

---

### 0.3 广播域 vs 冲突域

| 概念 | 定义 | 隔离设备 |
|------|------|----------|
| **冲突域** | 共享传输介质，同时发送会冲突 | 交换机隔离 |
| **广播域** | 广播帧能到达的范围 | 路由器/VLAN 隔离 |

**广播域过大的问题**：广播风暴、安全隐患、性能下降

---

### 0.4 VLAN (Virtual LAN)

**定义**：虚拟局域网，在物理交换机上逻辑划分广播域。

```
802.1Q 标签: 4字节插入以太网帧
● VLAN ID: 12 bit = 4096 个 VLAN
● 这就是为什么传统 VLAN 最多 4096 个

端口类型:
● Access: 连终端，进出时处理标签
● Trunk:  连交换机，保持标签，多 VLAN 共用一条线
```

**局限**：4096 不够用、不能跨三层、STP 限制 → 催生 VXLAN

---

### 0.5 STP (Spanning Tree Protocol)

**定义**：生成树协议，通过阻塞冗余链路防止二层环路。

```
工作原理:
1. 选根桥 (Root Bridge)
2. 每交换机选根端口 (到根桥最近)
3. 每链路选指定端口，其他阻塞

STP 的致命问题:
┌─────────────────────────────────────────────────────────────┐
│  ● 阻塞链路 = 浪费带宽 (50% 浪费)                            │
│  ● 收敛慢 = 30-50 秒 (云服务不可接受)                        │
│  ● 规模限制 = 不建议超过 100 台交换机                        │
└─────────────────────────────────────────────────────────────┘

替代方案: Spine-Leaf + ECMP、MLAG、堆叠
```

**详细文章**：[二层三层网络基础详解](/articles/networking/net-22-二层三层网络基础详解/#六stp-生成树协议)

---

### 0.6 VLAN vs VXLAN

| 特性 | VLAN | VXLAN |
|------|------|-------|
| **标识位数** | 12 bit (4096) | 24 bit (1600万) |
| **封装** | 802.1Q 二层标签 | MAC-in-UDP 隧道 |
| **跨三层** | 不支持 | 支持 (只需 IP 可达) |
| **STP** | 需要 | 不需要 (底层是三层) |
| **适用场景** | 传统企业 | 云计算/数据中心 |

```
关系:
● VLAN = 物理二层网络的逻辑划分
● VXLAN = 在三层网络上虚拟出来的二层网络

VXLAN 可以看作 "VLAN 的升级版"，解决了 VLAN 的所有局限
```

**详细文章**：[二层三层网络基础详解](/articles/networking/net-22-二层三层网络基础详解/#七vxlan-virtual-extensible-lan)

---

### 0.7 MTU 与 MSS

| 概念 | 全称 | 说明 |
|------|------|------|
| **MTU** | Maximum Transmission Unit | 链路层最大传输单元，以太网默认 1500 |
| **MSS** | Maximum Segment Size | TCP 最大段大小，= MTU - 40 (IP+TCP头) |

```
VXLAN 的 MTU 问题:
原始帧 1500 + VXLAN封装 50 = 1550 → 超过物理 MTU

解决方案:
● 物理网络 MTU 调大 (推荐 9000 Jumbo Frame)
● 或 VM 内 MTU 调小 (1450)
```

---

### 0.8 链路聚合 (LAG/LACP)

**定义**：将多条物理链路捆绑成一条逻辑链路。

| 术语 | 说明 |
|------|------|
| **LAG** | Link Aggregation Group，链路聚合组 |
| **LACP** | Link Aggregation Control Protocol (802.3ad)，动态协商协议 |
| **Bond** | Linux 的链路聚合实现 |

```bash
# Linux Bonding (LACP 模式)
ip link add bond0 type bond mode 802.3ad
ip link set eth0 master bond0
ip link set eth1 master bond0
```

---

### 0.9 路由协议简介

| 协议 | 类型 | 适用场景 |
|------|------|----------|
| **OSPF** | IGP (链路状态) | 中大型企业网络 |
| **IS-IS** | IGP (链路状态) | 运营商、大型数据中心 |
| **BGP** | EGP (路径向量) | AS 间互联、数据中心 |

```
为什么数据中心用 BGP?
● 互联网验证的可扩展性 (百万路由)
● 可承载 EVPN (VXLAN 控制面)
● 丰富的策略控制能力
```

---

## 一、TCP/IP 基础

### 1.1 TCP Three-Way Handshake (三次握手)

**定义**：TCP建立连接的过程，通过三次报文交换确认双方的发送和接收能力。

**过程**：
```
客户端                    服务器
   │                        │
   │──── SYN (seq=x) ──────→│  1. 客户端发起
   │                        │
   │←── SYN+ACK (seq=y,     │  2. 服务器响应
   │     ack=x+1) ──────────│
   │                        │
   │──── ACK (ack=y+1) ────→│  3. 客户端确认
   │                        │
   │    连接建立，可传输数据   │
```

**为什么是三次而非两次**：
- 防止历史连接请求被误接受
- 确认双方的初始序列号
- 同步双方的接收窗口

**HFT优化**：
```c
// 开启TCP Fast Open，减少握手延迟
int qlen = 5;
setsockopt(listen_fd, SOL_TCP, TCP_FASTOPEN, &qlen, sizeof(qlen));
```

---

### 1.2 TCP Four-Way Handshake (四次挥手)

**定义**：TCP关闭连接的过程，需要四次报文交换确保双方都完成数据传输。

**过程**：
```
客户端                    服务器
   │                        │
   │──── FIN ──────────────→│  1. 客户端请求关闭
   │                        │
   │←── ACK ────────────────│  2. 服务器确认
   │                        │
   │    [服务器可能还有数据]   │
   │                        │
   │←── FIN ────────────────│  3. 服务器请求关闭
   │                        │
   │──── ACK ──────────────→│  4. 客户端确认
   │                        │
   │    进入TIME_WAIT       │
```

**为什么是四次而非三次**：
- TCP是全双工的，每个方向需要独立关闭
- 服务器收到FIN后可能还有数据要发送
- 必须等服务器发完数据才能发送FIN

**HFT关注点**：
- 连接关闭会进入TIME_WAIT状态
- 大量短连接会消耗端口资源
- 解决方案：连接复用、连接池

---

### 1.3 TIME_WAIT State

**定义**：主动关闭连接的一方在发送最后一个ACK后进入的状态，持续2MSL（Maximum Segment Lifetime，通常60秒-2分钟）。

**为什么需要TIME_WAIT**：
1. **确保ACK到达**：如果最后的ACK丢失，对端会重发FIN，需要能够响应
2. **防止旧报文干扰**：确保旧连接的延迟报文在网络中消失

**TIME_WAIT对HFT的影响**：
```bash
# 查看TIME_WAIT连接数量
netstat -an | grep TIME_WAIT | wc -l
ss -s | grep TIME-WAIT
```

**问题**：大量短连接导致端口耗尽
```
高频创建/关闭连接
    ↓
大量socket进入TIME_WAIT（持续60秒）
    ↓
可用端口耗尽
    ↓
新连接失败
```

**解决方案**：
```bash
# 1. 启用端口复用（允许复用TIME_WAIT的端口）
sysctl -w net.ipv4.tcp_tw_reuse=1

# 2. 减少TIME_WAIT时间（不推荐，可能导致问题）
# sysctl -w net.ipv4.tcp_fin_timeout=15

# 3. 增加端口范围
sysctl -w net.ipv4.ip_local_port_range="1024 65535"
```

**代码层面**：
```cpp
// 使用SO_REUSEADDR
int reuse = 1;
setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

// 更好的方案：连接复用，避免频繁创建关闭
```

---

### 1.4 TCP Keep-Alive

**定义**：TCP层的心跳机制，用于检测死连接（对端崩溃、网络中断等）。

**工作原理**：
```
如果连接空闲超过一定时间：
    发送探测包
    如果收到ACK：连接正常
    如果多次无响应：判定连接死亡
```

**默认参数（通常太长）**：
```bash
# 查看当前设置
sysctl net.ipv4.tcp_keepalive_time   # 7200秒（2小时）
sysctl net.ipv4.tcp_keepalive_intvl  # 75秒
sysctl net.ipv4.tcp_keepalive_probes # 9次

# 即：空闲2小时后，每75秒发一次探测，9次无响应判定死亡
# 总计约2小时11分钟才能发现死连接！
```

**HFT调优**：
```bash
# 系统级别
sysctl -w net.ipv4.tcp_keepalive_time=60
sysctl -w net.ipv4.tcp_keepalive_intvl=10
sysctl -w net.ipv4.tcp_keepalive_probes=3
# 空闲60秒后，每10秒探测一次，3次无响应判定死亡（共90秒）
```

**Per-Socket设置**：
```cpp
int enable = 1;
setsockopt(sock, SOL_SOCKET, SO_KEEPALIVE, &enable, sizeof(enable));

// Linux特有：设置具体参数
int idle = 60;      // 空闲60秒后开始探测
int intvl = 10;     // 每10秒探测一次
int cnt = 3;        // 3次无响应判定死亡
setsockopt(sock, IPPROTO_TCP, TCP_KEEPIDLE, &idle, sizeof(idle));
setsockopt(sock, IPPROTO_TCP, TCP_KEEPINTVL, &intvl, sizeof(intvl));
setsockopt(sock, IPPROTO_TCP, TCP_KEEPCNT, &cnt, sizeof(cnt));
```

**注意**：应用层心跳通常更可靠（可以检测应用层死锁）

---

### 1.6 TCP Congestion Control (拥塞控制)

**定义**：TCP动态调整发送速率以适应网络容量，避免网络拥塞。

**主要算法**：

| 算法 | 特点 | 适用场景 |
|------|------|----------|
| Reno | 经典AIMD | 传统网络 |
| CUBIC | Linux默认 | 高带宽网络 |
| BBR | 基于带宽估计 | 长肥网络、HFT |

**BBR优势**：
- 不依赖丢包判断拥塞
- 更好的带宽利用率
- 更低的队列延迟

```bash
# 启用BBR
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p

# 验证
sysctl net.ipv4.tcp_congestion_control
# net.ipv4.tcp_congestion_control = bbr
```

**详细文章**：[TCP调优深入详解(HFT)](/articles/networking/net-18-TCP调优深入详解/)

---

### 1.7 TCP_NODELAY vs Nagle Algorithm

**定义**：Nagle算法合并小包减少网络拥塞；TCP_NODELAY禁用Nagle，数据立即发送。

**Nagle算法逻辑**：
```
如果有未确认的数据：
    等待ACK或累积到MSS再发送
否则：
    立即发送
```

**问题**：与Delayed ACK配合时可能产生200ms延迟

**HFT必须禁用Nagle**：
```cpp
int flag = 1;
setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));
```

**何时保留Nagle**：
- 大量小包写入（如telnet键盘输入）
- 不关心延迟的批量传输

---

### 1.8 UDP Multicast (UDP组播)

**定义**：一对多通信，发送方发送一份数据，多个接收方同时收到。

**为什么HFT使用组播**：
- 交易所使用组播分发市场数据
- 带宽效率高（一份数据多人接收）
- 低延迟（无需维护多个连接）

**接收组播**：
```cpp
int sock = socket(AF_INET, SOCK_DGRAM, 0);

// 允许端口复用
int reuse = 1;
setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

// 绑定到组播端口
struct sockaddr_in addr = {};
addr.sin_family = AF_INET;
addr.sin_port = htons(MCAST_PORT);
addr.sin_addr.s_addr = htonl(INADDR_ANY);
bind(sock, (struct sockaddr*)&addr, sizeof(addr));

// 加入组播组
struct ip_mreq mreq;
mreq.imr_multiaddr.s_addr = inet_addr("239.1.1.1");
mreq.imr_interface.s_addr = htonl(INADDR_ANY);
setsockopt(sock, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq));
```

**详细文章**：[UDP组播最佳实践(HFT)](/articles/networking/net-19-UDP组播最佳实践/)

---

## 二、Socket 编程

### 2.1 Blocking vs Non-blocking I/O

**定义**：
- **阻塞I/O**：操作完成前线程挂起
- **非阻塞I/O**：操作立即返回，可能返回EAGAIN

**对比**：
```cpp
// 阻塞模式
int n = recv(sock, buf, size, 0);  // 无数据时阻塞

// 非阻塞模式
fcntl(sock, F_SETFL, O_NONBLOCK);
int n = recv(sock, buf, size, 0);
if (n < 0 && errno == EAGAIN) {
    // 无数据可读，可以做其他事
}
```

**HFT选择**：
- 忙等待轮询（最低延迟）
- 配合epoll/io_uring的非阻塞

---

### 2.2 Socket Buffer (套接字缓冲区)

**定义**：内核为每个Socket维护的发送和接收缓冲区。

**调优参数**：
```bash
# 增大缓冲区
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"
```

**代码设置**：
```cpp
int bufsize = 16 * 1024 * 1024;  // 16MB
setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));
```

**注意**：实际分配是设置值的2倍（内核内部结构开销）

---

### 2.3 SO_REUSEADDR vs SO_REUSEPORT

**SO_REUSEADDR**：
- 允许绑定到TIME_WAIT状态的地址
- 允许绑定到0.0.0.0和具体IP

**SO_REUSEPORT**（Linux 3.9+）：
- 允许多个进程绑定到完全相同的地址和端口
- 内核自动负载均衡

```cpp
// 快速重启服务
int reuse = 1;
setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

// 多进程负载均衡
setsockopt(sock, SOL_SOCKET, SO_REUSEPORT, &reuse, sizeof(reuse));
```

---

## 三、高性能网络

### 3.1 Kernel Bypass (内核旁路)

**定义**：绕过操作系统内核网络栈，用户态程序直接与网卡交互。

**为什么需要**：
```
传统路径延迟分解：
- 中断处理：2-10μs
- 协议栈：2-5μs  
- 数据拷贝：1-2μs
- 系统调用：0.5-1μs
总计：5-20μs

Kernel Bypass：
- 轮询接收：10-50ns
- 用户态协议：100-500ns
总计：< 1μs
```

**技术对比**：

| 技术 | 延迟 | 生态 | 复杂度 |
|------|------|------|--------|
| DPDK | 1-2μs | 丰富 | 高 |
| Solarflare Onload | <1μs | 商业 | 中 |
| XDP/eBPF | 2-5μs | 新兴 | 中 |
| RDMA | <1μs | 专用 | 高 |

**详细文章**：[DPDK深度实践](/articles/hft/hft-20-DPDK深度实践/)

---

### 3.2 DPDK (Data Plane Development Kit)

**定义**：Intel开源的用户态网络开发框架，实现高性能数据包处理。

**核心组件**：
- **PMD (Poll Mode Driver)**：用户态网卡驱动
- **rte_ring**：无锁环形队列
- **rte_mbuf**：报文缓冲区管理
- **Huge Pages**：减少TLB miss

**基本使用**：
```cpp
#include <rte_ethdev.h>
#include <rte_mbuf.h>

// 初始化后，轮询接收
while (running) {
    struct rte_mbuf* bufs[BURST_SIZE];
    uint16_t nb_rx = rte_eth_rx_burst(port, queue, bufs, BURST_SIZE);
    
    for (int i = 0; i < nb_rx; i++) {
        process_packet(bufs[i]);
        rte_pktmbuf_free(bufs[i]);
    }
}
```

**详细文章**：[DPDK深度实践](/articles/hft/hft-20-DPDK深度实践/)

---

### 3.3 RDMA (Remote Direct Memory Access)

**定义**：绕过CPU直接在两台机器的内存间传输数据的技术。

**工作模式**：
- **Send/Recv**：类似传统Socket
- **Read/Write**：直接读写远程内存，对端不感知

**关键概念**：
- **QP (Queue Pair)**：发送/接收队列对
- **MR (Memory Region)**：注册的内存区域
- **CQ (Completion Queue)**：完成通知队列

**延迟对比**：
```
TCP/IP Socket：10-50μs
RDMA：1-2μs
```

**详细文章**：[RDMA与InfiniBand详解(HFT)](/articles/networking/net-21-RDMA与InfiniBand详解/)

---

### 3.4 RSS (Receive Side Scaling)

**定义**：网卡将接收的数据包分发到多个队列，由多个CPU核心并行处理。

**工作原理**：
```
网卡接收 → 计算哈希(IP+Port) → 选择队列 → 对应CPU处理
```

**配置**：
```bash
# 查看当前队列数
ethtool -l eth0

# 设置队列数
ethtool -L eth0 combined 8

# 查看哈希配置
ethtool -n eth0 rx-flow-hash tcp4
```

**HFT注意**：
- 确保同一连接的包始终到同一CPU
- 可能需要绑定中断到特定CPU

---

### 3.5 XDP/eBPF (eXpress Data Path)

**定义**：Linux内核中的高性能数据包处理框架。XDP在网卡驱动层处理数据包，eBPF提供安全的内核可编程能力。

**为什么重要**：
- 比传统内核网络栈快5-10倍
- 可编程而无需修改内核
- 比DPDK更容易部署（不需要接管网卡）

**XDP处理点**：
```
网卡收包
    ↓
┌─────────────┐
│ XDP程序     │ ← 最早处理点，驱动层
│ - XDP_DROP │     丢弃包
│ - XDP_PASS │     继续内核处理
│ - XDP_TX   │     直接发回
│ - XDP_REDIRECT │ 重定向到其他接口/CPU
└─────────────┘
    ↓
内核网络栈
```

**简单XDP程序**：
```c
// xdp_filter.c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int xdp_drop_all(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    // 解析以太网头
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;
    
    // 只允许IP包
    if (eth->h_proto == htons(ETH_P_IP))
        return XDP_PASS;
    
    return XDP_DROP;
}

char _license[] SEC("license") = "GPL";
```

**加载XDP程序**：
```bash
# 编译
clang -O2 -target bpf -c xdp_filter.c -o xdp_filter.o

# 加载到网卡
ip link set dev eth0 xdp obj xdp_filter.o sec xdp

# 卸载
ip link set dev eth0 xdp off
```

**XDP vs DPDK**：
| 特性 | XDP | DPDK |
|------|-----|------|
| 延迟 | ~2-5μs | ~1-2μs |
| 复杂度 | 低 | 高 |
| 网卡兼容 | 大多数 | 特定驱动 |
| 内核集成 | 完全 | 独立 |
| 适用 | 过滤/DDoS防护 | 顶级HFT |

---

## 四、网络调优

### 4.1 Interrupt Coalescing (中断合并)

**定义**：网卡积累多个数据包后再触发一次中断，减少中断开销。

**权衡**：
- 更多合并 → 更低CPU开销，更高延迟
- 更少合并 → 更低延迟，更高CPU开销

**配置**：
```bash
# 查看当前设置
ethtool -c eth0

# 设置最小中断延迟（HFT）
ethtool -C eth0 rx-usecs 0 tx-usecs 0

# 或完全禁用合并，使用轮询
ethtool -C eth0 adaptive-rx off adaptive-tx off
```

---

### 4.2 TCP Timestamps

**定义**：TCP选项，用于RTT测量和PAWS（防止序列号回绕）。

**开销**：每个包增加12字节

**HFT考量**：
```bash
# 在超低延迟场景可考虑关闭
sysctl -w net.ipv4.tcp_timestamps=0

# 但可能影响RTT测量和PAWS
# 通常保持开启更安全
```

---

### 4.3 Busy Polling (忙等待轮询)

**定义**：在Socket层面进行轮询，避免进入睡眠和唤醒的开销。

**内核支持**：
```bash
# 启用忙轮询
sysctl -w net.core.busy_poll=50        # 轮询50μs
sysctl -w net.core.busy_read=50
```

**每个Socket设置**：
```cpp
int busy_poll = 50;  // 微秒
setsockopt(sock, SOL_SOCKET, SO_BUSY_POLL, &busy_poll, sizeof(busy_poll));
```

---

## 五、数据中心网络架构

### 5.1 大二层 (Large Layer 2)

**一句话**：让整个数据中心像一个巨大的交换机，VM 可以随意迁移而不改 IP。

**为什么需要？**
```
传统问题:
┌─────────────────────────────────────────────────────────────┐
│ 1. VLAN 只有 4096 个 → 云计算百万租户不够用                  │
│    原因: 802.1Q 只分配了 12bit 给 VLAN ID (2^12=4096)       │
│                                                             │
│ 2. VM 热迁移必须同一二层 → 传统网络跨机房很难                │
│    原因: 改 IP = 连接断开 + DNS更新 + 防火墙改配置           │
│                                                             │
│ 3. STP 阻塞冗余链路 → 带宽浪费 50%                          │
│    原因: 生成树防环，但代价是阻塞备份链路                    │
└─────────────────────────────────────────────────────────────┘
```

**实现技术**：VXLAN（主流）、NVGRE、TRILL、SPB

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#二大二层网络-large-layer-2)

---

### 5.2 大三层 / Spine-Leaf

**一句话**：用纯路由替代交换，消除 STP，所有链路同时工作。

```
传统三层 (STP阻塞):         Spine-Leaf (全部Active):

    Core                      Spine  Spine
      │                         ╲ ╱  ╲ ╱
   STP阻塞                       ╳    ╳   ← ECMP，负载均衡
   部分链路                     ╱ ╲  ╱ ╲
      │                      Leaf Leaf Leaf
    Agg                         │    │    │
      │                       服务器群
    Acc
```

**为什么更好**：无 STP、链路 100% 利用、任意两点最多 2 跳、水平扩展

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#三大三层网络-routed-layer-3)

---

### 5.3 VXLAN

**一句话**：在三层网络上"虚拟"出二层网络，支持 1600 万个隔离网络。

**解决什么问题**：
| 问题 | 传统方案 | VXLAN |
|------|----------|-------|
| VLAN 数量 | 12位=4096 | 24位=1600万 |
| 跨机房二层 | 需要直连 | 三层可达即可 |
| STP 限制 | 扩展性差 | 底层是三层，无 STP |

**关键概念**：
- **VNI**：24位网络 ID（相当于超级 VLAN 号）
- **VTEP**：隧道端点（负责封装/解封装）
- **Underlay**：底层物理 IP 网络（高速公路）
- **Overlay**：上层虚拟二层网络（公路上的专线）

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#23-vxlan-深入剖析)

---

### 5.4 BGP EVPN

**一句话**：VXLAN 的"大脑"，让 VTEP 自动知道"谁在哪里"，避免广播风暴。

**为什么需要？**
```
没有 EVPN (数据面学习):       有 EVPN (控制面分发):

VM1 问 "VM2 在哪?"           VM2 启动时，BGP 通告:
      ↓                       "我的 MAC/IP 在 VTEP2"
广播到所有 VTEP                     ↓
(规模大了是灾难)              所有 VTEP 都知道了
      ↓                             ↓
只有 VTEP2 回复               VM1 问时，本地直接回答
                              (无需广播)
```

**路由类型**：Type-2(MAC/IP)、Type-3(组播)、Type-5(子网前缀)

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#四bgp-evpn)

---

### 5.5 Underlay vs Overlay

**一句话**：分层解耦，底层只管 IP 可达，上层虚拟网络随便折腾。

```
┌─────────────────────────────────────────────┐
│  Overlay (虚拟网络)                          │
│  - 租户看到的网络                            │
│  - 可以 IP 地址重叠（不同租户用相同 10.x）   │
│  - 变化频繁（VM 创建/删除/迁移）             │
└─────────────────────────────────────────────┘
              ↑ 封装/解封装 (VXLAN)
┌─────────────────────────────────────────────┐
│  Underlay (物理网络)                         │
│  - 只需保证 VTEP 之间 IP 可达                │
│  - 配置简单稳定，很少变动                    │
│  - 纯三层路由 (BGP/OSPF)                    │
└─────────────────────────────────────────────┘

好处: 上层变化不影响底层，运维职责分离
```

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#五underlay-与-overlay)

---

### 5.6 SDN (Software Defined Networking)

**一句话**：把网络设备的"大脑"抽出来集中管理，设备只负责转发。

**解决什么问题**：
- 传统：每台设备独立配置，变更慢，易出错
- SDN：控制器统一下发策略，一处修改全网生效

**典型方案**：VMware NSX、Cisco ACI、OpenStack Neutron、Calico、Cilium

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#八sdn-与数据中心网络)

---

### 5.7 SR-IOV

**一句话**：网卡硬件虚拟化，让 VM 直接访问网卡，跳过软件 vSwitch。

**为什么需要**：
```
传统虚拟网络:              SR-IOV:
VM → vSwitch → NIC         VM → VF → NIC (直通)
   ↑                          ↑
CPU处理，延迟高             硬件处理，接近裸机性能
```

**适用场景**：对延迟敏感的 HFT、NFV、RDMA 应用

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#103-sr-iov)

---

### 5.8 ECMP

**一句话**：多条等价路径同时用，告别 STP 浪费带宽。

**原理**：基于五元组 Hash，同一流走同一路径（避免乱序），不同流负载均衡

**注意**：大象流（单个大流量连接）无法分散，需要应用层多连接

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#61-ecmp-equal-cost-multi-path)

---

### 5.9 MLAG / VPC

**一句话**：两台交换机假装是一台，服务器双上行双活。

**解决什么问题**：
```
单上行: 线断了就断网
双上行+STP: 一条被阻塞，还是单活
MLAG: 两条线同时用，任一交换机挂了另一台接管
```

**厂商名称**：Cisco vPC、Arista MLAG、华为 M-LAG、Juniper MC-LAG

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#62-mlag--vpc-多机箱链路聚合)

---

### 5.10 Anycast Gateway

**一句话**：每个 Leaf 都是网关，VM 本地路由，不用绕到集中网关。

**解决什么问题**：
```
集中式网关: 所有跨子网流量都绕到网关 → 瓶颈 + 延迟
分布式网关: 每个 Leaf 都能路由 → 最短路径 + 高可用
```

**实现**：所有 Leaf 配置相同的网关 IP 和 MAC

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#63-anycast-gateway-分布式网关)

---

### 5.11 DCI (Data Center Interconnect)

**一句话**：把多个物理机房连成一个逻辑网络。

**使用场景**：
- 灾备：主机房挂了切到备机房
- 扩容：单机房容量不够
- 就近服务：用户访问最近的机房

**技术选型**：VXLAN+EVPN（主流）、OTV（Cisco）、SD-WAN（分支互联）

**详细文章**：[数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/#72-dci-data-center-interconnect)

---

## 六、延伸阅读

- [Linux核心概念索引](/articles/00-glossary/glossary-01-linux-concepts/)
- [HFT核心概念索引](/articles/00-glossary/glossary-04-hft-concepts/)
- [TCP调优深入详解(HFT)](/articles/networking/net-18-TCP调优深入详解/)
- [io_uring详解(HFT)](/articles/networking/net-20-io_uring详解/)
- [数据中心网络架构详解](/articles/networking/net-23-数据中心网络架构详解/)
- [RDMA与InfiniBand详解](/articles/networking/net-21-RDMA与InfiniBand详解/)
