+++
title = "11.网络性能分析与调优"
date = 2026-01-19
description = "网络性能优化：性能指标、瓶颈分析、内核参数调优、工具使用、常见问题排查"
[taxonomies]
tags = ["网络", "性能", "调优"]
+++

## 网络性能指标

### 核心指标

| 指标 | 描述 | 单位 |
|------|------|------|
| 带宽(Bandwidth) | 链路最大传输能力 | bps |
| 吞吐量(Throughput) | 实际传输速率 | bps |
| 延迟(Latency) | 数据传输时间 | ms |
| 抖动(Jitter) | 延迟变化 | ms |
| 丢包率(Packet Loss) | 丢失包占比 | % |
| PPS | 每秒包数 | packets/s |

### 延迟构成

```
总延迟 = 传播延迟 + 传输延迟 + 处理延迟 + 排队延迟

传播延迟：信号在介质中传播（光速限制）
传输延迟：数据从发送端发出（带宽决定）
处理延迟：路由器/交换机处理
排队延迟：等待处理（最不确定）
```

### 带宽时延积

**BDP = 带宽 × RTT**

表示"在途数据量"，影响TCP窗口设置：
```
带宽：1Gbps
RTT：100ms
BDP = 1Gbps × 0.1s = 100Mbit = 12.5MB

TCP窗口至少需要12.5MB才能充分利用带宽
```

---

## 性能分析工具

### 网络状态查看

**ss/netstat**：
```bash
# 查看TCP连接统计
ss -s

# 查看监听端口
ss -tlnp

# 查看连接状态分布
ss -ant | awk '{print $1}' | sort | uniq -c

# 查看接收/发送队列
ss -tnp
```

**ip命令**：
```bash
# 查看网卡统计
ip -s link show eth0

# 查看路由表
ip route show
```

### 流量分析

**iftop**：实时流量监控
```bash
iftop -i eth0
```

**nethogs**：按进程查看流量
```bash
nethogs eth0
```

**sar**：历史流量统计
```bash
sar -n DEV 1 10  # 每秒统计，共10次
```

### 延迟测试

**ping**：
```bash
ping -c 100 target  # 发送100个包
```

**mtr**：traceroute + ping
```bash
mtr target
```

**hping3**：更灵活的探测
```bash
hping3 -S -p 80 target  # TCP SYN探测
```

### 带宽测试

**iperf3**：
```bash
# 服务端
iperf3 -s

# 客户端测试TCP
iperf3 -c server -t 30

# 测试UDP
iperf3 -c server -u -b 1G

# 反向测试
iperf3 -c server -R
```

### 抓包分析

**tcpdump**：
```bash
# 抓取特定主机
tcpdump -i eth0 host 192.168.1.1

# 抓取特定端口
tcpdump -i eth0 port 80

# 保存为pcap
tcpdump -i eth0 -w capture.pcap

# 显示详细信息
tcpdump -i eth0 -vvv
```

**Wireshark**：图形化分析工具
- TCP流分析
- 延迟分析
- 协议解析

---

## TCP性能分析

### TCP指标

```bash
# 查看TCP统计
netstat -st
ss -ti  # 显示TCP内部信息
```

**关键指标**：
- cwnd：拥塞窗口
- rwnd：接收窗口
- rtt：往返时间
- retrans：重传次数

### 重传分析

```bash
# 查看重传统计
netstat -st | grep -i retrans

# tcpdump抓取重传
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0'
```

**重传原因**：
- 网络丢包
- 拥塞
- 接收方处理慢

### TIME_WAIT分析

```bash
# 统计TIME_WAIT数量
ss -ant | grep TIME-WAIT | wc -l

# 如果过多，考虑调整
sysctl -w net.ipv4.tcp_tw_reuse=1
```

---

## 内核参数调优

### 连接相关

```bash
# 半连接队列大小
net.ipv4.tcp_max_syn_backlog = 65535

# 全连接队列大小
net.core.somaxconn = 65535

# SYN重试次数
net.ipv4.tcp_syn_retries = 2

# SYN+ACK重试次数
net.ipv4.tcp_synack_retries = 2
```

### 缓冲区相关

```bash
# 接收缓冲区（最小、默认、最大）
net.ipv4.tcp_rmem = 4096 87380 16777216
net.core.rmem_max = 16777216
net.core.rmem_default = 262144

# 发送缓冲区
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.wmem_max = 16777216
net.core.wmem_default = 262144

# 内存使用限制
net.ipv4.tcp_mem = 786432 1048576 1572864
```

### TIME_WAIT相关

```bash
# 允许重用TIME_WAIT
net.ipv4.tcp_tw_reuse = 1

# FIN_WAIT2超时时间
net.ipv4.tcp_fin_timeout = 30

# 最大TIME_WAIT数量
net.ipv4.tcp_max_tw_buckets = 1000000
```

### 拥塞控制

```bash
# 使用BBR
net.ipv4.tcp_congestion_control = bbr

# 启用窗口缩放
net.ipv4.tcp_window_scaling = 1

# 启用SACK
net.ipv4.tcp_sack = 1

# 启用时间戳
net.ipv4.tcp_timestamps = 1
```

### Keepalive

```bash
# 空闲多久开始探测
net.ipv4.tcp_keepalive_time = 600

# 探测间隔
net.ipv4.tcp_keepalive_intvl = 15

# 探测次数
net.ipv4.tcp_keepalive_probes = 5
```

### 快速路径

```bash
# 增大backlog
net.core.netdev_max_backlog = 65535

# 增大最大文件描述符
fs.file-max = 1000000
```

---

## 网卡调优

### 中断亲和性

将网卡中断绑定到特定CPU：
```bash
# 查看中断
cat /proc/interrupts | grep eth0

# 设置中断亲和性
echo 1 > /proc/irq/24/smp_affinity  # CPU 0
echo 2 > /proc/irq/25/smp_affinity  # CPU 1
```

### RSS/RPS

**RSS（Receive Side Scaling）**：
- 硬件多队列
- 将不同流分到不同CPU

**RPS（Receive Packet Steering）**：
- 软件实现的RSS
- 适用于不支持RSS的网卡

```bash
# 启用RPS
echo ff > /sys/class/net/eth0/queues/rx-0/rps_cpus
```

### 网卡参数

```bash
# 查看网卡参数
ethtool eth0

# 查看网卡统计
ethtool -S eth0

# 调整ring buffer
ethtool -G eth0 rx 4096 tx 4096

# 查看offload状态
ethtool -k eth0
```

### Offload特性

```bash
# TSO：TCP Segmentation Offload
ethtool -K eth0 tso on

# GRO：Generic Receive Offload
ethtool -K eth0 gro on

# LRO：Large Receive Offload
ethtool -K eth0 lro on
```

---

## 常见问题排查

### 高延迟

**排查步骤**：
1. ping测试基础延迟
2. mtr查看每跳延迟
3. 检查网络是否拥塞
4. 检查应用处理时间

**可能原因**：
- 网络拥塞
- 路由绕路
- 应用处理慢
- CPU过载

### 丢包

**排查步骤**：
```bash
# 查看网卡丢包
ip -s link show eth0

# 查看协议层丢包
netstat -st | grep -i drop

# 查看conntrack丢包
dmesg | grep conntrack
```

**可能原因**：
- ring buffer满
- 内核缓冲区满
- conntrack表满
- iptables丢弃

### 带宽未充分利用

**检查项**：
- TCP窗口是否足够大（BDP）
- 是否有丢包导致降速
- 拥塞控制算法是否合适
- 网卡配置是否正确

### 连接建立慢

**排查**：
```bash
# 检查SYN队列
ss -ltn

# 检查是否有SYN丢弃
netstat -st | grep -i syn
```

**可能原因**：
- backlog太小
- SYN Flood攻击
- 服务端处理慢

---

## 性能基准测试

### 网络基准

```bash
# 带宽测试
iperf3 -c server -t 60

# 延迟测试
ping -c 1000 server

# PPS测试
iperf3 -c server -u -l 64 -b 0
```

### 应用基准

```bash
# HTTP压测
wrk -t12 -c400 -d30s http://server/

# 并发连接测试
ab -n 100000 -c 1000 http://server/
```

### 结果分析

记录并对比：
- 吞吐量
- 延迟分布（P50、P99）
- 错误率
- 资源使用（CPU、内存）

---

## 总结

| 层面 | 调优点 |
|------|--------|
| 应用层 | 连接池、异步IO、批量处理 |
| TCP | 拥塞控制、窗口大小、Keepalive |
| 内核 | 缓冲区、队列、conntrack |
| 网卡 | 中断亲和、RSS、Offload |
| 网络 | 带宽、延迟、路由 |

**调优原则**：
1. 先测量，后调优
2. 一次改一个参数
3. 对比调优前后效果
4. 理解参数含义，避免盲目复制

---

## 相关文章

- [上一篇：Socket网络编程](/articles/networking/net-10-Socket网络编程/)
- [下一篇：网络虚拟化技术](/articles/networking/net-12-网络虚拟化技术/)
