+++
title = "内核参数调优实战"
date = 2026-01-21
weight = 53000
description = "SRE内核参数调优完整指南：sysctl、ulimit、网络/内存/文件系统调优"
[taxonomies]
tags = ["SRE", "内核", "调优", "sysctl", "ulimit", "性能"]
+++

## 概述

Linux内核参数调优是SRE必备技能。合理的参数配置可以显著提升系统性能和稳定性。本文系统介绍sysctl和ulimit的使用方法及常见调优场景。

---

# 一、sysctl基础

## 1.1 sysctl命令

### 查看参数

```bash
# 查看所有参数
sysctl -a

# 查看特定参数
sysctl net.ipv4.tcp_max_syn_backlog
sysctl -n net.ipv4.tcp_max_syn_backlog  # 只输出值

# 按关键字搜索
sysctl -a | grep tcp
sysctl -a | grep mem

# 查看参数文档
# /proc/sys/对应的路径
cat /proc/sys/net/ipv4/tcp_max_syn_backlog
```

### 修改参数

```bash
# 临时修改（重启后失效）
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# 或直接写入/proc
echo 65535 > /proc/sys/net/ipv4/tcp_max_syn_backlog

# 永久修改
# 方法1：编辑/etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf

# 方法2：在/etc/sysctl.d/创建配置文件（推荐）
cat > /etc/sysctl.d/99-custom.conf << 'EOF'
# 网络优化
net.ipv4.tcp_max_syn_backlog = 65535
net.core.somaxconn = 65535
EOF

# 应用配置
sysctl -p                      # 加载/etc/sysctl.conf
sysctl -p /etc/sysctl.d/99-custom.conf  # 加载指定文件
sysctl --system                # 加载所有配置文件
```

---

## 1.2 参数路径说明

```bash
# /proc/sys/ 目录结构
/proc/sys/
├── kernel/     # 内核参数
├── net/        # 网络参数
│   ├── core/       # 核心网络
│   ├── ipv4/       # IPv4
│   ├── ipv6/       # IPv6
│   └── netfilter/  # 连接跟踪
├── vm/         # 内存管理
├── fs/         # 文件系统
└── debug/      # 调试

# sysctl名称与路径对应关系
# net.ipv4.tcp_syncookies → /proc/sys/net/ipv4/tcp_syncookies
# vm.swappiness → /proc/sys/vm/swappiness
```

---

# 二、网络参数调优

## 2.1 TCP连接优化

### 连接队列

```bash
# 半连接队列（SYN队列）
# 存放收到SYN但未完成三次握手的连接
net.ipv4.tcp_max_syn_backlog = 65535

# 全连接队列（Accept队列）
# 存放完成三次握手等待accept的连接
net.core.somaxconn = 65535

# 应用程序listen的backlog上限就是somaxconn

# 检查队列溢出
netstat -s | grep -i listen
# X times the listen queue of a socket overflowed
# X SYNs to LISTEN sockets dropped

# SYN Cookie防护
# 在SYN队列满时启用，防止SYN Flood
net.ipv4.tcp_syncookies = 1

# SYN重试次数
net.ipv4.tcp_syn_retries = 2      # 客户端SYN重试
net.ipv4.tcp_synack_retries = 2   # 服务端SYN+ACK重试
```

### TIME_WAIT优化

```bash
# TIME_WAIT状态是TCP正常关闭后的状态
# 持续2MSL（默认60秒），用于确保最后的ACK到达

# 查看TIME_WAIT数量
ss -ant | awk '{print $1}' | sort | uniq -c | sort -rn

# 允许TIME_WAIT socket复用（重要！）
net.ipv4.tcp_tw_reuse = 1

# 注意：tcp_tw_recycle已在4.12内核移除，不要使用

# TIME_WAIT bucket数量
net.ipv4.tcp_max_tw_buckets = 262144

# FIN_WAIT超时
net.ipv4.tcp_fin_timeout = 30

# 本地端口范围（增加可用端口）
net.ipv4.ip_local_port_range = 1024 65535
```

### Keepalive优化

```bash
# TCP Keepalive参数
# 连接空闲多久发送探测包
net.ipv4.tcp_keepalive_time = 600

# 探测包发送间隔
net.ipv4.tcp_keepalive_intvl = 60

# 探测包发送次数（无响应则断开）
net.ipv4.tcp_keepalive_probes = 3

# 总超时 = time + intvl * probes = 600 + 60*3 = 780秒
```

---

## 2.2 TCP缓冲区

```bash
# 读缓冲区（接收）
# 格式：min default max（字节）
net.ipv4.tcp_rmem = 4096 87380 16777216

# 写缓冲区（发送）
net.ipv4.tcp_wmem = 4096 87380 16777216

# 核心缓冲区
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# 高带宽延迟网络（BDP = 带宽 × RTT）
# 例如：1Gbps，RTT=100ms → BDP = 125MB × 0.1 = 12.5MB
# 缓冲区应该 >= BDP
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 87380 67108864
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864

# 内存压力阈值
net.ipv4.tcp_mem = 786432 1048576 1572864
# 格式：low pressure high（页数，通常4KB/页）
# low: 低于此值不回收
# pressure: 开始回收
# high: 高于此值拒绝分配
```

---

## 2.3 拥塞控制

```bash
# 查看可用拥塞控制算法
sysctl net.ipv4.tcp_available_congestion_control

# 查看当前算法
sysctl net.ipv4.tcp_congestion_control

# 设置BBR（推荐，需要内核4.9+）
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# 验证BBR是否启用
lsmod | grep bbr

# 如果没有bbr模块，加载它
modprobe tcp_bbr
echo "tcp_bbr" >> /etc/modules-load.d/bbr.conf

# BBR优势：
# - 基于带宽和RTT而非丢包
# - 在高延迟高丢包环境表现更好
# - 更好地利用带宽
```

---

## 2.4 连接跟踪

```bash
# 连接跟踪表大小
net.netfilter.nf_conntrack_max = 262144

# 查看当前连接数
cat /proc/sys/net/netfilter/nf_conntrack_count

# 连接跟踪超时
net.netfilter.nf_conntrack_tcp_timeout_established = 7200
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 120
net.netfilter.nf_conntrack_tcp_timeout_close_wait = 60
net.netfilter.nf_conntrack_tcp_timeout_fin_wait = 120

# 哈希表大小（只读，启动时设置）
# /sys/module/nf_conntrack/parameters/hashsize
# 建议 hashsize = nf_conntrack_max / 4

# 如果不需要连接跟踪（无NAT和状态防火墙）
# 可以在特定表中禁用
iptables -t raw -A PREROUTING -p tcp --dport 80 -j NOTRACK
iptables -t raw -A OUTPUT -p tcp --sport 80 -j NOTRACK
```

---

## 2.5 网络综合配置

```bash
# /etc/sysctl.d/99-network.conf
# 高性能网络服务器配置

# 连接队列
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 65535

# TIME_WAIT
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.ip_local_port_range = 1024 65535

# Keepalive
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 3

# 缓冲区
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 87380 16777216

# 拥塞控制
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# 安全
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_syn_retries = 2
net.ipv4.tcp_synack_retries = 2

# 连接跟踪（如果使用）
net.netfilter.nf_conntrack_max = 262144
```

---

# 三、内存参数调优

## 3.1 Swap管理

```bash
# swappiness控制使用Swap的倾向
# 0-100，越低越倾向使用物理内存
# 默认60，数据库服务器建议10-30
vm.swappiness = 10

# 查看当前值
sysctl vm.swappiness

# 对于Redis等内存敏感应用
vm.swappiness = 1

# 完全禁用Swap（不推荐，可能导致OOM）
# vm.swappiness = 0 并不会完全禁用
# 需要 swapoff -a

# VFS缓存压力
# 控制内核回收inode/dentry缓存的倾向
# 默认100，降低可保留更多缓存
vm.vfs_cache_pressure = 50
```

---

## 3.2 内存过量使用

```bash
# overcommit策略
# 0: 启发式（默认），允许适度overcommit
# 1: 总是允许overcommit
# 2: 严格不允许overcommit
vm.overcommit_memory = 0

# 当overcommit_memory=2时
# 可用内存 = Swap + RAM * overcommit_ratio/100
vm.overcommit_ratio = 50

# 查看内存提交状态
cat /proc/meminfo | grep -i commit
# CommitLimit: 允许的最大提交
# Committed_AS: 已提交的内存

# OOM Killer设置
# panic_on_oom: OOM时是否panic
vm.panic_on_oom = 0

# oom_kill_allocating_task: 是否杀死触发OOM的进程
vm.oom_kill_allocating_task = 0
```

---

## 3.3 脏页管理

```bash
# 脏页（dirty page）是已修改但未写入磁盘的内存页

# 触发后台刷新的脏页比例
vm.dirty_background_ratio = 5
# 或使用绝对值（字节）
vm.dirty_background_bytes = 0

# 触发同步刷新的脏页比例
# 超过此值，写入会阻塞等待刷新
vm.dirty_ratio = 20
# 或使用绝对值
vm.dirty_bytes = 0

# 脏页过期时间（百分之一秒）
# 超过此时间必须刷新
vm.dirty_expire_centisecs = 3000  # 30秒

# 刷新线程唤醒间隔
vm.dirty_writeback_centisecs = 500  # 5秒

# 数据库服务器（减少突发IO）
vm.dirty_background_ratio = 3
vm.dirty_ratio = 10

# 大内存服务器（使用绝对值更可控）
vm.dirty_background_bytes = 268435456  # 256MB
vm.dirty_bytes = 1073741824            # 1GB
```

---

## 3.4 大页内存

```bash
# 大页（HugePages）减少TLB压力，适合大内存应用

# 查看大页状态
cat /proc/meminfo | grep -i huge
grep -i huge /proc/meminfo

# 配置大页数量
# 先计算需要的大页数 = 需要的内存 / 大页大小
# 默认大页大小2MB
vm.nr_hugepages = 512  # 512 * 2MB = 1GB

# 或通过sysfs设置
echo 512 > /proc/sys/vm/nr_hugepages

# 透明大页（THP）
# 对于数据库（MongoDB, Redis, MySQL）建议禁用
# 因为可能导致延迟抖动
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# 永久禁用THP（grub配置）
# GRUB_CMDLINE_LINUX="transparent_hugepage=never"
```

---

## 3.5 内存配置示例

```bash
# /etc/sysctl.d/99-memory.conf
# 通用服务器内存优化

# Swap
vm.swappiness = 10

# 缓存
vm.vfs_cache_pressure = 50

# 脏页
vm.dirty_background_ratio = 5
vm.dirty_ratio = 20

# 过量使用（默认）
vm.overcommit_memory = 0

# OOM
vm.panic_on_oom = 0

# 大页（按需配置）
# vm.nr_hugepages = 512
```

---

# 四、文件系统参数

## 4.1 文件描述符

```bash
# 系统级文件描述符限制
fs.file-max = 6553560

# 查看当前使用
cat /proc/sys/fs/file-nr
# 格式：已分配 未使用 最大值

# inotify限制
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 1024
fs.inotify.max_queued_events = 16384

# AIO限制
fs.aio-max-nr = 1048576

# epoll限制
fs.epoll.max_user_watches = 1073741824
```

---

## 4.2 进程限制

```bash
# 最大进程数
kernel.pid_max = 4194304

# 最大线程数
kernel.threads-max = 4194304

# 查看当前进程数
ls /proc | grep -c "^[0-9]"
```

---

# 五、ulimit详解

## 5.1 ulimit基础

```bash
# 查看所有限制
ulimit -a

# 常用限制：
# -n  打开文件数（nofile）
# -u  用户进程数（nproc）
# -s  栈大小（stack）
# -c  core文件大小（core）
# -m  内存大小（不常用）
# -v  虚拟内存大小

# 查看软/硬限制
ulimit -Sn  # 软限制
ulimit -Hn  # 硬限制

# 软限制可以调到硬限制
# 硬限制只有root能调高
```

---

## 5.2 修改ulimit

### 临时修改

```bash
# 修改当前shell
ulimit -n 65535

# 只能改软限制到硬限制
# root可以改硬限制
ulimit -Hn 100000
```

### 永久修改

```bash
# /etc/security/limits.conf
# 格式：<domain> <type> <item> <value>

# 所有用户
*         soft    nofile    65535
*         hard    nofile    65535
*         soft    nproc     65535
*         hard    nproc     65535

# 特定用户
nginx     soft    nofile    100000
nginx     hard    nofile    100000

# 特定组
@developers soft  nofile    65535
@developers hard  nofile    65535

# root用户（需要单独配置）
root      soft    nofile    65535
root      hard    nofile    65535
```

### systemd服务限制

```bash
# systemd服务不读取limits.conf
# 需要在service文件中配置

# /etc/systemd/system/myapp.service
[Service]
LimitNOFILE=65535
LimitNPROC=65535
LimitCORE=infinity
LimitMEMLOCK=infinity

# 重载并重启
systemctl daemon-reload
systemctl restart myapp

# 查看服务限制
cat /proc/$(pidof myapp)/limits

# 全局默认（/etc/systemd/system.conf）
[Manager]
DefaultLimitNOFILE=65535
DefaultLimitNPROC=65535
```

---

## 5.3 常见场景配置

### Web服务器（Nginx/Apache）

```bash
# /etc/security/limits.d/nginx.conf
nginx    soft    nofile    100000
nginx    hard    nofile    100000
www-data soft    nofile    100000
www-data hard    nofile    100000

# Nginx配置也需要调整
# nginx.conf
worker_rlimit_nofile 100000;
events {
    worker_connections 65535;
}
```

### 数据库（MySQL/PostgreSQL）

```bash
# /etc/security/limits.d/mysql.conf
mysql    soft    nofile    65535
mysql    hard    nofile    65535
mysql    soft    nproc     65535
mysql    hard    nproc     65535

# systemd service
# /etc/systemd/system/mysql.service.d/limits.conf
[Service]
LimitNOFILE=65535
LimitNPROC=65535
```

### 消息队列（Kafka/RabbitMQ）

```bash
# /etc/security/limits.d/kafka.conf
kafka    soft    nofile    100000
kafka    hard    nofile    100000
kafka    soft    nproc     65535
kafka    hard    nproc     65535
```

---

# 六、内核参数调优检查脚本

```bash
#!/bin/bash
# kernel_tuning_check.sh - 内核参数检查

echo "===== 内核参数检查 ====="
echo "时间: $(date)"
echo ""

echo "=== 1. 网络参数 ==="
echo "--- 连接队列 ---"
echo "somaxconn: $(sysctl -n net.core.somaxconn)"
echo "tcp_max_syn_backlog: $(sysctl -n net.ipv4.tcp_max_syn_backlog)"

echo ""
echo "--- TIME_WAIT ---"
echo "tcp_tw_reuse: $(sysctl -n net.ipv4.tcp_tw_reuse)"
echo "tcp_fin_timeout: $(sysctl -n net.ipv4.tcp_fin_timeout)"
echo "ip_local_port_range: $(sysctl -n net.ipv4.ip_local_port_range)"

echo ""
echo "--- 缓冲区 ---"
echo "rmem_max: $(sysctl -n net.core.rmem_max)"
echo "wmem_max: $(sysctl -n net.core.wmem_max)"
echo "tcp_rmem: $(sysctl -n net.ipv4.tcp_rmem)"
echo "tcp_wmem: $(sysctl -n net.ipv4.tcp_wmem)"

echo ""
echo "--- 拥塞控制 ---"
echo "tcp_congestion_control: $(sysctl -n net.ipv4.tcp_congestion_control)"

echo ""
echo "--- 连接跟踪 ---"
if [ -f /proc/sys/net/netfilter/nf_conntrack_count ]; then
    echo "conntrack_count: $(cat /proc/sys/net/netfilter/nf_conntrack_count)"
    echo "conntrack_max: $(sysctl -n net.netfilter.nf_conntrack_max)"
fi

echo ""
echo "=== 2. 内存参数 ==="
echo "swappiness: $(sysctl -n vm.swappiness)"
echo "vfs_cache_pressure: $(sysctl -n vm.vfs_cache_pressure)"
echo "dirty_background_ratio: $(sysctl -n vm.dirty_background_ratio)"
echo "dirty_ratio: $(sysctl -n vm.dirty_ratio)"
echo "overcommit_memory: $(sysctl -n vm.overcommit_memory)"

echo ""
echo "=== 3. 文件系统参数 ==="
echo "file-max: $(sysctl -n fs.file-max)"
echo "file-nr: $(cat /proc/sys/fs/file-nr)"
echo "inotify.max_user_watches: $(sysctl -n fs.inotify.max_user_watches)"

echo ""
echo "=== 4. 进程限制 ==="
echo "pid_max: $(sysctl -n kernel.pid_max)"
echo "threads-max: $(sysctl -n kernel.threads-max)"

echo ""
echo "=== 5. ulimit（当前shell）==="
ulimit -a

echo ""
echo "===== 检查完成 ====="
```

---

# 七、场景化配置模板

## 7.1 高并发Web服务器

```bash
# /etc/sysctl.d/99-web-server.conf

# 网络连接
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_syncookies = 1

# TIME_WAIT
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.ip_local_port_range = 1024 65535

# 缓冲区
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 87380 16777216

# BBR
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# 文件描述符
fs.file-max = 6553560
fs.inotify.max_user_watches = 524288
```

## 7.2 数据库服务器

```bash
# /etc/sysctl.d/99-database.conf

# 减少Swap使用
vm.swappiness = 10

# 脏页设置（减少突发IO）
vm.dirty_background_ratio = 3
vm.dirty_ratio = 10

# 网络
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# 大页（按需）
# vm.nr_hugepages = 512

# 文件描述符
fs.file-max = 6553560
```

## 7.3 消息队列服务器

```bash
# /etc/sysctl.d/99-mq-server.conf

# 网络（高吞吐）
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 87380 67108864

# 内存
vm.swappiness = 1
vm.dirty_background_ratio = 5
vm.dirty_ratio = 80

# 文件
fs.file-max = 6553560
```

---

## 总结

### 参数速查

| 分类 | 参数 | 建议值 | 说明 |
|------|------|--------|------|
| 连接 | `somaxconn` | 65535 | Accept队列 |
| 连接 | `tcp_max_syn_backlog` | 65535 | SYN队列 |
| TIME_WAIT | `tcp_tw_reuse` | 1 | 允许复用 |
| 缓冲 | `rmem_max` | 16MB+ | 最大接收缓冲 |
| 拥塞 | `tcp_congestion_control` | bbr | 推荐BBR |
| 内存 | `swappiness` | 10-30 | 降低Swap使用 |
| 文件 | `file-max` | 6553560 | 系统文件描述符 |

### ulimit速查

| 限制 | 参数 | 建议值 |
|------|------|--------|
| 打开文件 | nofile | 65535+ |
| 进程数 | nproc | 65535 |
| 栈大小 | stack | 默认或增大 |

### 调优三原则

1. **先测量后调优** - 使用基准测试确认效果
2. **逐个参数调整** - 便于定位问题
3. **记录变更** - 便于回滚和复现

### 关键记忆

1. sysctl改的是内核参数，ulimit改的是进程资源限制
2. systemd服务需要在service文件中配置LimitXXX
3. BBR需要内核4.9+，推荐使用
4. 数据库服务器降低swappiness，禁用THP

---

## 相关文章

- [上一篇：定时任务问题排查实战](@/articles/sre/sre-52-定时任务问题排查实战.md)
- [下一篇：SRE面试题-Linux系统基础](@/articles/sre/sre-54-SRE面试题-Linux系统基础.md)
