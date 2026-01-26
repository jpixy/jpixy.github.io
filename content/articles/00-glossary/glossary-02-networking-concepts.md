+++
title = "02.Networking Concepts"
description = "网络核心概念速查：TCP/IP、Socket编程、高性能网络、协议优化等关键概念详解"
date = 2026-01-26
draft = false
[taxonomies]
tags = ["Glossary", "Networking", "TCP", "UDP", "Reference"]
+++

# Networking Concepts

本索引收录网络编程的核心概念，涵盖协议、Socket编程、高性能网络技术等。

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

## 五、延伸阅读

- [Linux核心概念索引](/articles/00-glossary/glossary-01-linux-concepts/)
- [HFT核心概念索引](/articles/00-glossary/glossary-04-hft-concepts/)
- [TCP调优深入详解(HFT)](/articles/networking/net-18-TCP调优深入详解/)
- [io_uring详解(HFT)](/articles/networking/net-20-io_uring详解/)
