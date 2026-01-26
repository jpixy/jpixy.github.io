+++
title = "09.Linux内核网络栈详解(HFT)"
description = "深入讲解Linux内核网络栈：sk_buff结构、netfilter框架、conntrack连接跟踪、TCP状态机、软中断与NAPI机制"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["Linux", "网络栈", "内核", "sk_buff", "NAPI", "HFT"]
+++

# Linux内核网络栈详解(HFT)

## 概述

理解Linux内核网络栈是进行网络性能优化的基础。本文深入分析网络数据包在内核中的处理流程，以及影响性能的关键机制。

## 一、网络栈架构

### 1.1 分层结构

```
用户空间
─────────────────────────────────────
│  应用程序 (socket API)
─────────────────────────────────────
│  Socket层
│  ├── AF_INET (IPv4)
│  ├── AF_INET6 (IPv6)
│  └── AF_PACKET (原始包)
─────────────────────────────────────
│  传输层
│  ├── TCP (net/ipv4/tcp.c)
│  └── UDP (net/ipv4/udp.c)
─────────────────────────────────────
│  网络层
│  ├── IP路由 (net/ipv4/ip_*.c)
│  └── Netfilter框架
─────────────────────────────────────
│  链路层
│  ├── 设备抽象 (net/core/dev.c)
│  └── 排队规则 (net/sched/)
─────────────────────────────────────
│  驱动层
│  └── 网卡驱动 (drivers/net/)
─────────────────────────────────────
硬件
```

### 1.2 数据包接收流程

```
网卡接收数据包
     │
     ▼
1. 硬件中断 (IRQ)
     │
     ▼
2. 驱动中断处理 (Top Half)
   ├── 禁用中断
   └── 触发NAPI
     │
     ▼
3. 软中断处理 (NET_RX_SOFTIRQ)
   └── NAPI poll
     │
     ▼
4. netif_receive_skb()
   ├── 分发到协议处理器
   └── 经过netfilter
     │
     ▼
5. ip_rcv() → ip_local_deliver()
     │
     ▼
6. tcp_v4_rcv() / udp_rcv()
     │
     ▼
7. 复制到socket缓冲区
     │
     ▼
8. 唤醒等待的进程
```

## 二、sk_buff结构

### 2.1 sk_buff详解

`sk_buff`是内核中表示网络数据包的核心结构：

```c
/* 简化的sk_buff结构 */
struct sk_buff {
    /* 链表指针 */
    struct sk_buff *next;
    struct sk_buff *prev;
    
    /* 时间戳 */
    ktime_t tstamp;
    
    /* 关联的socket */
    struct sock *sk;
    
    /* 关联的网络设备 */
    struct net_device *dev;
    
    /* 协议头指针 */
    unsigned char *head;      /* 缓冲区起始 */
    unsigned char *data;      /* 数据起始 */
    unsigned char *tail;      /* 数据结束 */
    unsigned char *end;       /* 缓冲区结束 */
    
    /* 各层协议头 */
    union {
        struct tcphdr *th;
        struct udphdr *uh;
        struct icmphdr *icmph;
    } transport_header;
    
    union {
        struct iphdr *iph;
        struct ipv6hdr *ipv6h;
    } network_header;
    
    union {
        struct ethhdr *eth;
    } mac_header;
    
    /* 数据长度 */
    unsigned int len;         /* 数据总长度 */
    unsigned int data_len;    /* 分片数据长度 */
    
    /* 协议类型 */
    __be16 protocol;
    
    /* 各种标志 */
    __u8 ip_summed:2;
    __u8 nohdr:1;
    __u8 nfctinfo:3;
    /* ... 更多字段 */
};
```

### 2.2 sk_buff操作

```c
/* 常用的sk_buff操作函数 */

/* 分配sk_buff */
struct sk_buff *alloc_skb(unsigned int size, gfp_t priority);
struct sk_buff *netdev_alloc_skb(struct net_device *dev, unsigned int length);

/* 释放sk_buff */
void kfree_skb(struct sk_buff *skb);
void consume_skb(struct sk_buff *skb);

/* 数据操作 */
void *skb_put(struct sk_buff *skb, unsigned int len);  /* 在tail添加数据 */
void *skb_push(struct sk_buff *skb, unsigned int len); /* 在head添加数据 */
void *skb_pull(struct sk_buff *skb, unsigned int len); /* 从head移除数据 */
void skb_reserve(struct sk_buff *skb, int len);        /* 预留头部空间 */

/* 克隆和复制 */
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t priority);
struct sk_buff *skb_copy(struct sk_buff *skb, gfp_t priority);
```

### 2.3 零拷贝技术

```c
/* 零拷贝发送示例 */
ssize_t sendfile(int out_fd, int in_fd, off_t *offset, size_t count);

/* splice系统调用 */
ssize_t splice(int fd_in, loff_t *off_in, int fd_out, 
               loff_t *off_out, size_t len, unsigned int flags);

/* 内核中的零拷贝：使用skb_shinfo存储分片信息 */
struct skb_shared_info {
    __u8 nr_frags;
    skb_frag_t frags[MAX_SKB_FRAGS];
    struct sk_buff *frag_list;
    /* ... */
};
```

## 三、NAPI机制

### 3.1 NAPI原理

NAPI（New API）通过中断和轮询结合，减少高负载下的中断开销：

```
传统中断模式:
每个包 → 中断 → 处理 → 中断 → 处理 → ...
(高负载下中断风暴)

NAPI模式:
第一个包 → 中断 → 禁用中断 → 轮询处理多个包 → 重新启用中断
(批量处理，减少中断)
```

### 3.2 NAPI驱动实现

```c
/* NAPI结构 */
struct napi_struct {
    struct list_head poll_list;
    unsigned long state;
    int weight;
    int (*poll)(struct napi_struct *, int);
    /* ... */
};

/* 驱动中的NAPI使用 */
static int my_driver_probe(struct pci_dev *pdev)
{
    struct net_device *netdev;
    struct my_private *priv;
    
    netdev = alloc_etherdev(sizeof(struct my_private));
    priv = netdev_priv(netdev);
    
    /* 初始化NAPI */
    netif_napi_add(netdev, &priv->napi, my_poll, NAPI_POLL_WEIGHT);
    
    return 0;
}

/* 中断处理函数 */
static irqreturn_t my_interrupt(int irq, void *dev_id)
{
    struct net_device *netdev = dev_id;
    struct my_private *priv = netdev_priv(netdev);
    
    /* 禁用网卡中断 */
    disable_irq_nosync(irq);
    
    /* 调度NAPI */
    if (napi_schedule_prep(&priv->napi)) {
        __napi_schedule(&priv->napi);
    }
    
    return IRQ_HANDLED;
}

/* NAPI poll函数 */
static int my_poll(struct napi_struct *napi, int budget)
{
    struct my_private *priv = container_of(napi, struct my_private, napi);
    int work_done = 0;
    
    while (work_done < budget) {
        struct sk_buff *skb = get_next_rx_packet(priv);
        if (!skb)
            break;
        
        /* 处理数据包 */
        skb->protocol = eth_type_trans(skb, priv->netdev);
        napi_gro_receive(napi, skb);  /* GRO处理 */
        
        work_done++;
    }
    
    if (work_done < budget) {
        /* 完成轮询，退出NAPI模式 */
        napi_complete(napi);
        /* 重新启用中断 */
        enable_irq(priv->irq);
    }
    
    return work_done;
}
```

### 3.3 软中断处理

```c
/* 软中断类型 */
enum {
    HI_SOFTIRQ=0,
    TIMER_SOFTIRQ,
    NET_TX_SOFTIRQ,
    NET_RX_SOFTIRQ,
    BLOCK_SOFTIRQ,
    IRQ_POLL_SOFTIRQ,
    TASKLET_SOFTIRQ,
    SCHED_SOFTIRQ,
    HRTIMER_SOFTIRQ,
    RCU_SOFTIRQ,
    NR_SOFTIRQS
};

/* 网络接收软中断处理 */
static void net_rx_action(struct softirq_action *h)
{
    struct softnet_data *sd = this_cpu_ptr(&softnet_data);
    unsigned long time_limit = jiffies + 2 * HZ / 100;
    int budget = netdev_budget;  /* 默认300 */
    
    for (;;) {
        struct napi_struct *n;
        
        n = list_first_entry(&sd->poll_list, struct napi_struct, poll_list);
        
        /* 执行NAPI poll */
        int work = n->poll(n, budget);
        
        budget -= work;
        
        if (budget <= 0 || time_after_eq(jiffies, time_limit))
            break;
    }
}
```

## 四、Netfilter框架

### 4.1 Netfilter钩子点

```
数据包接收                           数据包发送
     │                                    ▲
     ▼                                    │
┌────────────┐                     ┌────────────┐
│ PREROUTING │                     │ POSTROUTING│
└─────┬──────┘                     └─────▲──────┘
      │                                   │
      ▼                                   │
   路由决策 ────────────────────────► 本地处理?
      │                                   ▲
      │ 是                                │
      ▼                                   │
┌────────────┐                     ┌────────────┐
│   INPUT    │ ──────────────────► │   OUTPUT   │
└────────────┘       本地进程       └────────────┘
      │
      │ 否(转发)
      ▼
┌────────────┐
│  FORWARD   │
└────────────┘
```

### 4.2 Netfilter钩子注册

```c
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>

/* 钩子函数 */
static unsigned int my_hook(void *priv,
                            struct sk_buff *skb,
                            const struct nf_hook_state *state)
{
    struct iphdr *iph;
    
    if (!skb)
        return NF_ACCEPT;
    
    iph = ip_hdr(skb);
    
    /* 打印源IP */
    pr_info("Packet from %pI4\n", &iph->saddr);
    
    /* 返回值：
     * NF_ACCEPT - 接受数据包
     * NF_DROP   - 丢弃数据包
     * NF_STOLEN - 接管数据包
     * NF_QUEUE  - 排队到用户空间
     */
    return NF_ACCEPT;
}

/* 钩子操作结构 */
static struct nf_hook_ops my_nf_ops = {
    .hook     = my_hook,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,
};

/* 模块初始化 */
static int __init my_init(void)
{
    return nf_register_net_hook(&init_net, &my_nf_ops);
}

/* 模块卸载 */
static void __exit my_exit(void)
{
    nf_unregister_net_hook(&init_net, &my_nf_ops);
}
```

## 五、连接跟踪（conntrack）

### 5.1 conntrack原理

```
                    ┌─────────────────┐
                    │  conntrack表     │
                    │  (哈希表)        │
                    └────────┬────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
┌───▼───┐              ┌─────▼─────┐              ┌───▼───┐
│ Tuple │              │  Tuple    │              │ Tuple │
│ (src) │              │  (src)    │              │ (src) │
│ (dst) │              │  (dst)    │              │ (dst) │
│ proto │              │  proto    │              │ proto │
│ state │              │  state    │              │ state │
└───────┘              └───────────┘              └───────┘
```

### 5.2 查看conntrack表

```bash
# 查看连接跟踪表
conntrack -L

# 输出示例：
# tcp  6 431999 ESTABLISHED src=192.168.1.100 dst=10.0.0.1 sport=45678 dport=80 
# src=10.0.0.1 dst=192.168.1.100 sport=80 dport=45678 [ASSURED] mark=0 use=1

# 统计信息
conntrack -S

# conntrack表大小
cat /proc/sys/net/netfilter/nf_conntrack_max

# 当前连接数
cat /proc/sys/net/netfilter/nf_conntrack_count
```

### 5.3 conntrack性能调优

```bash
# 增加conntrack表大小
sysctl -w net.netfilter.nf_conntrack_max=2097152

# 调整哈希表大小（需要模块参数）
# /etc/modprobe.d/conntrack.conf
options nf_conntrack hashsize=524288

# 减少超时时间
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=1800
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=60
```

## 六、TCP状态机

### 6.1 TCP连接状态

```
客户端                                          服务端
   │                                              │
   │ ─────── SYN ─────────────────────────────►  │ LISTEN
   │                                              │
CONNECTING                                        │
   │                                              │
   │ ◄────── SYN+ACK ─────────────────────────── │ SYN_RCVD
   │                                              │
   │ ─────── ACK ─────────────────────────────►  │
   │                                              │
ESTABLISHED ◄──────────────────────────────────► ESTABLISHED
   │                                              │
   │ ─────── FIN ─────────────────────────────►  │
   │                                              │
FIN_WAIT_1                                        │
   │ ◄────── ACK ─────────────────────────────── │ CLOSE_WAIT
   │                                              │
FIN_WAIT_2                                        │
   │                                              │
   │ ◄────── FIN ─────────────────────────────── │ LAST_ACK
   │                                              │
   │ ─────── ACK ─────────────────────────────►  │
   │                                              │
TIME_WAIT ──────────────────────────────────────► CLOSED
   │
   │ (2MSL timeout)
   │
CLOSED
```

### 6.2 内核TCP参数

```bash
# TCP连接参数
cat /proc/sys/net/ipv4/tcp_syn_retries       # SYN重试次数
cat /proc/sys/net/ipv4/tcp_synack_retries    # SYN-ACK重试次数
cat /proc/sys/net/ipv4/tcp_fin_timeout       # FIN超时时间
cat /proc/sys/net/ipv4/tcp_keepalive_time    # 保活时间
cat /proc/sys/net/ipv4/tcp_keepalive_probes  # 保活探测次数
cat /proc/sys/net/ipv4/tcp_keepalive_intvl   # 保活间隔

# 缓冲区参数
cat /proc/sys/net/ipv4/tcp_rmem  # 接收缓冲区 [min default max]
cat /proc/sys/net/ipv4/tcp_wmem  # 发送缓冲区 [min default max]

# 拥塞控制
cat /proc/sys/net/ipv4/tcp_congestion_control

# 可用拥塞控制算法
cat /proc/sys/net/ipv4/tcp_available_congestion_control
```

### 6.3 TCP性能分析

```bash
#!/bin/bash
# tcp_analysis.sh - TCP性能分析

echo "=== TCP连接统计 ==="

# 按状态统计
echo -e "\n>>> 连接状态分布:"
ss -s

echo -e "\n>>> 各状态详细统计:"
ss -tan | awk 'NR>1 {states[$1]++} END {for(s in states) print s, states[s]}' | sort -k2 -rn

echo -e "\n>>> TIME_WAIT连接数:"
ss -tan state time-wait | wc -l

echo -e "\n>>> SYN_RECV队列:"
ss -tan state syn-recv | wc -l

echo -e "\n>>> TCP内存使用:"
cat /proc/net/sockstat | grep TCP

echo -e "\n>>> 重传统计:"
netstat -s | grep -E "(retransmit|timeout)"

echo -e "\n>>> 快速路径统计:"
cat /proc/net/snmp | grep Tcp
```

## 七、性能优化要点

### 7.1 关键性能参数

```bash
# 低延迟优化配置
cat > /etc/sysctl.d/99-network-performance.conf << 'EOF'
# 增大缓冲区
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 16777216
net.core.wmem_default = 16777216
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728

# 增大backlog
net.core.netdev_max_backlog = 300000
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# 开启TCP优化
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_low_latency = 1

# 禁用TCP时间戳（减少延迟）
net.ipv4.tcp_timestamps = 0

# 调整orphan和TIME_WAIT
net.ipv4.tcp_max_orphans = 262144
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_tw_reuse = 1

# Busy polling
net.core.busy_read = 50
net.core.busy_poll = 50
EOF

sysctl -p /etc/sysctl.d/99-network-performance.conf
```

### 7.2 中断亲和性配置

```bash
#!/bin/bash
# set_irq_affinity.sh - 配置网卡中断亲和性

IFACE=${1:-eth0}
START_CPU=${2:-0}

# 获取网卡的IRQ
irqs=$(grep $IFACE /proc/interrupts | awk '{print $1}' | tr -d ':')

cpu=$START_CPU
for irq in $irqs; do
    echo "Setting IRQ $irq to CPU $cpu"
    echo $cpu > /proc/irq/$irq/smp_affinity_list
    cpu=$((cpu + 1))
done

# 验证配置
echo -e "\n当前IRQ配置:"
for irq in $irqs; do
    affinity=$(cat /proc/irq/$irq/smp_affinity_list)
    echo "  IRQ $irq -> CPU $affinity"
done
```

## 总结

Linux网络栈的核心要点：

1. **sk_buff**：理解数据包在内核中的表示
2. **NAPI**：高负载下的中断优化机制
3. **Netfilter**：数据包过滤和处理框架
4. **conntrack**：连接状态跟踪，影响NAT和防火墙性能
5. **TCP状态机**：理解连接生命周期，优化参数

深入理解这些机制是进行网络性能优化的基础。
