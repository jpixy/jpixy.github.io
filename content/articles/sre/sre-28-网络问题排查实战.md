+++
title = "28.网络问题排查实战"
date = 2026-01-21
description = "SRE网络问题排查完整指南：连接失败、延迟高、丢包、带宽问题的定位与解决"
[taxonomies]
tags = ["SRE", "网络", "排查", "实战", "TCP", "DNS"]
+++

## 概述

网络问题是SRE最常遇到的故障类型之一。本文系统介绍网络问题的排查思路、常用工具和解决方案。

---

# 一、网络排查思路

## 1.1 分层排查法

```
应用层    → 应用日志、连接配置
传输层    → TCP/UDP连接状态、端口
网络层    → IP路由、防火墙、MTU
数据链路层 → 网卡状态、ARP
物理层    → 网线、交换机
```

## 1.2 排查流程图

```
问题现象
    ↓
能ping通目标吗？
    ├─ 否 → 检查路由、防火墙、目标是否在线
    ↓ 是
能telnet/nc到端口吗？
    ├─ 否 → 目标服务未启动或端口被封
    ↓ 是
延迟/丢包正常吗？
    ├─ 否 → 检查网络质量、链路问题
    ↓ 是
应用层连接正常吗？
    └─ 否 → 检查应用配置、协议问题
```

---

# 二、连接失败排查

## 2.1 基础连通性检查

### 场景：无法访问远程服务

**第一步：检查目标是否可达**

```bash
# ICMP检测
ping -c 5 target_host

# 如果ping不通，检查路由
traceroute target_host
# 或使用mtr（更好的traceroute）
mtr -r -c 10 target_host
```

**第二步：检查端口是否开放**

```bash
# 使用nc（netcat）
nc -zv target_host 80
nc -zv target_host 443

# 使用telnet
telnet target_host 80

# 批量检查端口
for port in 22 80 443 3306 6379; do
    nc -zv -w 3 target_host $port 2>&1 | grep -E "(open|succeeded|refused)"
done
```

**第三步：检查本地出口**

```bash
# 检查本机是否能访问外网
curl -I https://www.google.com

# 检查DNS解析
nslookup target_host
dig target_host

# 检查路由表
ip route
# 或
route -n

# 检查默认网关
ip route | grep default
```

---

## 2.2 防火墙问题

### 场景：端口被防火墙拦截

**检查本地防火墙**

```bash
# iptables规则
sudo iptables -L -n -v
sudo iptables -L -n -v -t nat

# 检查特定端口的规则
sudo iptables -L -n -v | grep 8080

# firewalld（CentOS 7+）
sudo firewall-cmd --list-all
sudo firewall-cmd --list-ports

# ufw（Ubuntu）
sudo ufw status verbose
```

**临时开放端口测试**

```bash
# iptables临时开放
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT

# firewalld临时开放
sudo firewall-cmd --add-port=8080/tcp

# ufw临时开放
sudo ufw allow 8080/tcp
```

**检查云安全组**

```bash
# AWS CLI检查安全组
aws ec2 describe-security-groups --group-ids sg-xxxxx

# 阿里云CLI
aliyun ecs DescribeSecurityGroupAttribute --SecurityGroupId sg-xxxxx
```

---

## 2.3 DNS问题

### 场景：域名解析失败或解析错误

**诊断DNS问题**

```bash
# 基础解析测试
nslookup example.com
dig example.com

# 指定DNS服务器
dig @8.8.8.8 example.com
dig @114.114.114.114 example.com

# 查看完整解析链
dig +trace example.com

# 查看TTL
dig example.com | grep -A1 "ANSWER SECTION"

# 反向解析
dig -x 1.2.3.4
```

**常见DNS问题**

```bash
# 问题1：DNS服务器不可达
# 检查/etc/resolv.conf
cat /etc/resolv.conf

# 测试DNS服务器
dig @$(head -1 /etc/resolv.conf | awk '/nameserver/{print $2}') example.com

# 问题2：DNS缓存污染
# 清除本地DNS缓存（systemd-resolved）
sudo systemd-resolve --flush-caches
sudo systemd-resolve --statistics

# 问题3：hosts文件覆盖
cat /etc/hosts | grep example.com

# 问题4：解析顺序问题
cat /etc/nsswitch.conf | grep hosts
```

**修复DNS问题**

```bash
# 临时使用其他DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# 持久化配置（Ubuntu with systemd-resolved）
# /etc/systemd/resolved.conf
[Resolve]
DNS=8.8.8.8 8.8.4.4
FallbackDNS=1.1.1.1

sudo systemctl restart systemd-resolved
```

---

## 2.4 连接超时问题

### 场景：连接建立慢或超时

**分析连接建立过程**

```bash
# 使用curl详细计时
curl -w "@curl-format.txt" -o /dev/null -s http://example.com

# curl-format.txt内容：
#     time_namelookup:  %{time_namelookup}s\n
#        time_connect:  %{time_connect}s\n
#     time_appconnect:  %{time_appconnect}s\n
#    time_pretransfer:  %{time_pretransfer}s\n
#       time_redirect:  %{time_redirect}s\n
#  time_starttransfer:  %{time_starttransfer}s\n
#          time_total:  %{time_total}s\n

# 一行命令版本
curl -o /dev/null -s -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nTotal: %{time_total}s\n" https://example.com
```

**结果解读**：

| 阶段 | 指标 | 慢的原因 |
|------|------|----------|
| DNS解析 | time_namelookup | DNS服务器慢或不可达 |
| TCP连接 | time_connect - time_namelookup | 网络延迟或服务端负载高 |
| TLS握手 | time_appconnect - time_connect | 证书验证或加密协商 |
| 首字节 | time_starttransfer - time_appconnect | 服务端处理慢 |

**检查TCP连接状态**

```bash
# 查看连接状态统计
ss -s

# 查看特定端口的连接
ss -ant | grep :8080

# 查看TIME_WAIT过多
ss -ant | awk '{print $1}' | sort | uniq -c | sort -rn

# 查看SYN_RECV（可能被SYN Flood）
ss -ant | grep SYN_RECV | wc -l
```

---

# 三、网络延迟排查

## 3.1 延迟测量

### 基础延迟测试

```bash
# ping测试RTT
ping -c 100 target_host

# 查看延迟统计
ping -c 100 target_host | tail -1
# 输出：rtt min/avg/max/mdev = 0.5/1.2/3.4/0.3 ms

# hping3 - TCP ping（绕过ICMP封锁）
sudo hping3 -S -p 80 -c 10 target_host
```

### MTR - 综合路径分析

```bash
# 文本报告
mtr -r -c 100 target_host

# 输出示例：
# HOST: source                 Loss%   Snt   Last   Avg  Best  Wrst StDev
# 1.|-- gateway                 0.0%   100    0.5   0.6   0.4   1.2   0.1
# 2.|-- isp-router              0.0%   100    5.2   5.5   4.8   8.3   0.5
# 3.|-- core-router             0.0%   100   10.1  10.5   9.8  15.2   1.2
# 4.|-- target_host             0.0%   100   15.2  15.8  14.5  22.1   1.8

# 实时监控
mtr target_host

# 指定发包间隔（更密集）
mtr -i 0.1 -c 1000 target_host
```

**MTR结果解读**：

| 指标 | 含义 | 异常判断 |
|------|------|----------|
| Loss% | 丢包率 | >1% 需关注 |
| Last | 最近一次延迟 | 参考值 |
| Avg | 平均延迟 | 主要参考 |
| Best | 最小延迟 | 理论最优 |
| Wrst | 最大延迟 | 反映抖动 |
| StDev | 标准差 | 越大越不稳定 |

---

## 3.2 延迟抖动分析

### 场景：延迟不稳定

```bash
# 收集延迟样本
ping -c 1000 target_host | grep "time=" | awk -F'time=' '{print $2}' | cut -d' ' -f1 > latency.txt

# 分析延迟分布
cat latency.txt | awk '{sum+=$1; sumsq+=$1*$1} END {print "Avg:", sum/NR, "StdDev:", sqrt(sumsq/NR - (sum/NR)^2)}'

# 查看百分位数
sort -n latency.txt | awk 'BEGIN{c=0} {a[c++]=$1} END{
    print "P50:", a[int(c*0.5)];
    print "P90:", a[int(c*0.9)];
    print "P99:", a[int(c*0.99)];
    print "Max:", a[c-1]
}'
```

### 延迟尖峰排查

```bash
# 抓取高延迟时的网络包
sudo tcpdump -i eth0 host target_host -w high_latency.pcap

# 配合ping监控
ping target_host | while read line; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') $line"
done | tee ping.log

# 查找延迟>100ms的时间点
grep "time=" ping.log | awk -F'time=' '{split($2,a," "); if(a[1]>100) print}'
```

---

## 3.3 TCP延迟分析

### 使用tcptrace分析

```bash
# 抓包
sudo tcpdump -i eth0 -w capture.pcap host target_host and port 80

# 使用tcptrace分析
tcptrace -l capture.pcap

# 使用Wireshark的tshark
tshark -r capture.pcap -q -z io,stat,1,"tcp.analysis.ack_rtt"
```

### ss查看RTT

```bash
# 查看TCP连接的RTT信息
ss -ti dst target_host

# 输出包含：
# rtt:1.234/0.567  # 当前RTT / RTT方差
# rto:234          # 重传超时
# cwnd:10          # 拥塞窗口
```

---

# 四、丢包问题排查

## 4.1 丢包检测

### 基础检测

```bash
# ping检测丢包
ping -c 1000 -i 0.1 target_host
# 查看最后的统计：packet loss

# MTR检测路径丢包
mtr -r -c 200 target_host

# iperf3检测UDP丢包
# 服务端
iperf3 -s
# 客户端
iperf3 -c target_host -u -b 100M -t 30
# 查看Lost/Total
```

### 区分丢包位置

```bash
# MTR可以看到每一跳的丢包
mtr -r -c 500 target_host

# 关键点：
# 1. 如果某一跳开始丢包且后续都丢包 → 该跳是问题点
# 2. 如果只有中间某跳丢包但最终不丢包 → 可能是ICMP限速，忽略
# 3. 如果最后一跳丢包 → 目标服务器问题
```

---

## 4.2 本地网卡丢包

### 检查网卡统计

```bash
# 查看网卡错误和丢包
ip -s link show eth0

# 输出关键字段：
#    RX:  bytes  packets  errors  dropped  missed  mcast
#    TX:  bytes  packets  errors  dropped carrier collsns

# 更详细的统计
ethtool -S eth0 | grep -i drop
ethtool -S eth0 | grep -i error

# 实时监控
watch -n 1 'ip -s link show eth0'
```

### 常见丢包原因

```bash
# 1. Ring Buffer满
ethtool -g eth0
# 查看当前和最大Ring Buffer大小

# 增大Ring Buffer
sudo ethtool -G eth0 rx 4096 tx 4096

# 2. 软中断处理不过来
cat /proc/net/softnet_stat
# 第二列是drop，第三列是time_squeeze

# 调整软中断预算
sysctl -w net.core.netdev_budget=600
sysctl -w net.core.netdev_budget_usecs=8000

# 3. Socket Buffer满
ss -lntp | grep LISTEN
# 检查Recv-Q是否接近设置值

# 增大Socket Buffer
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216
sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sysctl -w net.ipv4.tcp_wmem="4096 87380 16777216"
```

---

## 4.3 内核丢包分析

### 使用dropwatch

```bash
# 安装
sudo apt install dropwatch

# 运行
sudo dropwatch -l kas

# 输出会显示丢包发生在内核的哪个函数
# 例如：drop at: nf_hook_slow (gillter规则丢弃)
```

### 使用perf

```bash
# 追踪kfree_skb（内核丢包函数）
sudo perf record -g -a -e skb:kfree_skb -- sleep 10
sudo perf report

# 或使用ftrace
echo 1 | sudo tee /sys/kernel/debug/tracing/events/skb/kfree_skb/enable
cat /sys/kernel/debug/tracing/trace_pipe
```

---

# 五、带宽问题排查

## 5.1 带宽测量

### iperf3测速

```bash
# 服务端
iperf3 -s

# 客户端 - TCP测速
iperf3 -c server_ip -t 30

# 反向测试（服务端发送）
iperf3 -c server_ip -t 30 -R

# 双向测试
iperf3 -c server_ip -t 30 -d

# 多流测试
iperf3 -c server_ip -t 30 -P 4

# UDP测速
iperf3 -c server_ip -u -b 1G -t 30
```

### 实时带宽监控

```bash
# iftop - 实时流量
sudo iftop -i eth0

# nload - 简洁带宽图
sudo nload eth0

# sar - 历史数据
sar -n DEV 1 10

# nethogs - 按进程查看
sudo nethogs eth0

# bmon - 带宽监控
bmon -p eth0
```

---

## 5.2 带宽瓶颈分析

### 场景：带宽跑不满

**检查网卡配置**

```bash
# 查看网卡速率
ethtool eth0 | grep Speed

# 查看是否支持更高速率
ethtool eth0 | grep -i supported

# 检查是否自动协商
ethtool eth0 | grep -i auto

# 手动设置速率（如果需要）
sudo ethtool -s eth0 speed 10000 duplex full autoneg off
```

**检查TCP参数**

```bash
# 查看TCP窗口大小
cat /proc/sys/net/ipv4/tcp_window_scaling
cat /proc/sys/net/core/rmem_max
cat /proc/sys/net/core/wmem_max

# 高带宽优化
sysctl -w net.core.rmem_max=67108864
sysctl -w net.core.wmem_max=67108864
sysctl -w net.ipv4.tcp_rmem="4096 87380 67108864"
sysctl -w net.ipv4.tcp_wmem="4096 87380 67108864"

# 启用BBR拥塞控制
sysctl -w net.core.default_qdisc=fq
sysctl -w net.ipv4.tcp_congestion_control=bbr
```

**检查中断和CPU**

```bash
# 查看网卡中断
cat /proc/interrupts | grep eth0

# 检查中断是否均匀分布到多个CPU
cat /proc/interrupts | grep eth0 | awk '{for(i=2;i<=NF;i++) printf "%s ", $i; print ""}'

# 启用RSS（接收端缩放）
ethtool -l eth0  # 查看队列数
ethtool -L eth0 combined 4  # 设置队列数

# 设置中断亲和性
# 通常由irqbalance服务处理
systemctl status irqbalance
```

---

# 六、常见网络问题速查

## 6.1 问题速查表

| 现象 | 可能原因 | 排查命令 |
|------|----------|----------|
| 无法ping通 | 路由/防火墙/目标down | `traceroute`, `iptables -L` |
| 端口连不上 | 服务未启动/端口封锁 | `ss -lntp`, `nc -zv` |
| 延迟高 | 网络拥塞/路由绕行 | `mtr`, `traceroute` |
| 延迟抖动 | 链路不稳定/队列满 | `ping`, `mtr` |
| 丢包 | 网络拥塞/设备问题 | `mtr`, `ethtool -S` |
| 带宽低 | 配置问题/拥塞 | `iperf3`, `ethtool` |
| DNS慢 | DNS服务器问题 | `dig +trace` |
| SSL失败 | 证书/协议问题 | `openssl s_client` |

---

## 6.2 一键诊断脚本

```bash
#!/bin/bash
# network_diagnose.sh - 网络诊断脚本

TARGET=${1:-"8.8.8.8"}
PORT=${2:-"443"}

echo "===== 网络诊断报告 ====="
echo "目标: $TARGET:$PORT"
echo "时间: $(date)"
echo ""

echo "--- 1. 基本连通性 ---"
ping -c 5 $TARGET

echo ""
echo "--- 2. 端口检测 ---"
nc -zv -w 5 $TARGET $PORT 2>&1

echo ""
echo "--- 3. 路由追踪 ---"
traceroute -n -m 15 $TARGET 2>/dev/null || tracepath $TARGET

echo ""
echo "--- 4. DNS解析 ---"
dig +short $TARGET 2>/dev/null || nslookup $TARGET

echo ""
echo "--- 5. 本地网卡状态 ---"
ip -s link show | head -20

echo ""
echo "--- 6. 连接状态统计 ---"
ss -s

echo ""
echo "--- 7. 路由表 ---"
ip route

echo ""
echo "===== 诊断完成 ====="
```

---

## 6.3 常用网络调优参数

```bash
# /etc/sysctl.conf 网络优化参数

# 基础优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# 连接复用
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.ip_local_port_range = 1024 65535

# 缓冲区
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 87380 16777216

# 拥塞控制
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# Keepalive
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 3

# 应用配置
sysctl -p
```

---

# 七、防火墙深入排查

## 7.1 iptables详解

### 查看规则

```bash
# 查看所有规则（详细）
iptables -L -n -v

# 查看带行号（便于删除）
iptables -L -n -v --line-numbers

# 查看特定链
iptables -L INPUT -n -v
iptables -L OUTPUT -n -v
iptables -L FORWARD -n -v

# 查看NAT表
iptables -t nat -L -n -v

# 查看mangle表
iptables -t mangle -L -n -v

# 查看raw表
iptables -t raw -L -n -v

# 导出所有规则（便于分析）
iptables-save > iptables_backup.txt

# 统计每条规则命中次数
iptables -L -n -v | awk 'NR>2 {print $1, $2, $NF}'
```

### 规则调试

```bash
# 添加日志规则（调试用）
iptables -I INPUT -p tcp --dport 8080 -j LOG --log-prefix "IPT-8080: " --log-level 4

# 查看日志
tail -f /var/log/kern.log | grep "IPT-8080"
# 或
journalctl -k -f | grep "IPT-8080"

# 添加规则并测试
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT

# 删除规则（按行号）
iptables -D INPUT 3

# 删除规则（按内容）
iptables -D INPUT -p tcp --dport 8080 -j ACCEPT

# 清空规则（危险，先备份）
iptables -F  # 清空所有链
iptables -X  # 删除自定义链
iptables -Z  # 清零计数器
```

### 常见场景规则

```bash
# 允许已建立的连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 允许特定端口
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 允许特定IP
iptables -A INPUT -s 192.168.1.0/24 -j ACCEPT

# 限制连接速率（防DDoS）
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# 端口转发
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080

# SNAT/MASQUERADE
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# 禁止ping
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# 默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT
```

### iptables问题排查

```bash
# 问题：端口无法访问

# 1. 检查是否有DROP规则
iptables -L -n -v | grep -E "DROP|REJECT"

# 2. 检查默认策略
iptables -L | head -3
# 如果默认是DROP，需要有明确的ACCEPT规则

# 3. 检查规则顺序
iptables -L INPUT -n -v --line-numbers
# 规则按顺序匹配，先匹配到就停止

# 4. 临时放行测试
iptables -I INPUT 1 -p tcp --dport 8080 -j ACCEPT
# 测试完成后删除
iptables -D INPUT 1

# 5. 检查连接跟踪
cat /proc/net/nf_conntrack | grep 8080

# 连接跟踪表满
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max
# 如果count接近max，需要增大
sysctl -w net.netfilter.nf_conntrack_max=262144
```

---

## 7.2 nftables详解

### 基础命令

```bash
# nftables是iptables的继任者（CentOS 8+, Debian 10+）

# 查看所有规则
nft list ruleset

# 查看特定表
nft list table inet filter

# 查看特定链
nft list chain inet filter input

# 导出规则
nft list ruleset > nftables_backup.nft

# 导入规则
nft -f nftables_backup.nft
```

### nftables规则示例

```bash
# /etc/nftables.conf 示例
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        
        # 允许本地回环
        iif lo accept
        
        # 允许已建立连接
        ct state established,related accept
        
        # 允许ICMP
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept
        
        # 允许SSH
        tcp dport 22 accept
        
        # 允许HTTP/HTTPS
        tcp dport { 80, 443 } accept
        
        # 允许特定IP段
        ip saddr 192.168.1.0/24 accept
        
        # 记录并丢弃其他
        log prefix "nft-drop: " drop
    }
    
    chain forward {
        type filter hook forward priority 0; policy drop;
    }
    
    chain output {
        type filter hook output priority 0; policy accept;
    }
}

# 应用配置
nft -f /etc/nftables.conf
systemctl enable nftables
```

---

## 7.3 firewalld详解

### 基础命令

```bash
# 查看状态
firewall-cmd --state
systemctl status firewalld

# 查看当前zone
firewall-cmd --get-active-zones

# 查看所有配置
firewall-cmd --list-all

# 查看特定zone
firewall-cmd --zone=public --list-all

# 查看所有zones
firewall-cmd --get-zones
firewall-cmd --list-all-zones
```

### 规则管理

```bash
# 添加端口（临时）
firewall-cmd --add-port=8080/tcp

# 添加端口（永久）
firewall-cmd --permanent --add-port=8080/tcp
firewall-cmd --reload

# 移除端口
firewall-cmd --permanent --remove-port=8080/tcp
firewall-cmd --reload

# 添加服务
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https

# 添加富规则（高级）
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="3306" protocol="tcp" accept'

# 端口转发
firewall-cmd --permanent --add-forward-port=port=80:proto=tcp:toport=8080
firewall-cmd --permanent --add-masquerade

# 查看所有服务
firewall-cmd --get-services

# 查看服务端口
firewall-cmd --info-service=ssh
```

### firewalld问题排查

```bash
# 问题：服务无法访问

# 1. 检查firewalld是否运行
systemctl status firewalld

# 2. 检查当前zone的规则
firewall-cmd --list-all

# 3. 检查端口是否开放
firewall-cmd --query-port=8080/tcp

# 4. 检查是否有拒绝规则
firewall-cmd --list-rich-rules

# 5. 临时关闭防火墙测试
systemctl stop firewalld
# 测试完成后恢复
systemctl start firewalld

# 6. 查看日志
journalctl -u firewalld -n 50
```

---

# 八、VPN问题排查

## 8.1 OpenVPN排查

### 服务端检查

```bash
# 检查服务状态
systemctl status openvpn-server@server
systemctl status openvpn@server

# 查看日志
journalctl -u openvpn-server@server -n 100
tail -f /var/log/openvpn/openvpn.log

# 检查监听端口
ss -ulnp | grep 1194
ss -tlnp | grep 1194

# 检查tun设备
ip link show tun0
ip addr show tun0

# 检查路由
ip route | grep tun

# 检查连接的客户端
cat /var/log/openvpn/openvpn-status.log
```

### 客户端检查

```bash
# 测试连接
openvpn --config client.ovpn

# 常见错误：
# "TLS Error: TLS handshake failed" - 证书问题
# "Connection refused" - 服务端未启动或端口被封
# "No route to host" - 网络不通

# 检查VPN连接后的路由
ip route
# 确认流量走VPN

# 检查DNS
cat /etc/resolv.conf
# VPN可能推送DNS

# 测试VPN隧道
ping <vpn_server_internal_ip>
```

### 常见问题

```bash
# 问题1：连接成功但无法访问内网

# 检查服务端IP转发
cat /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1

# 检查服务端NAT规则
iptables -t nat -L POSTROUTING -n -v

# 添加MASQUERADE
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE

# 问题2：只有部分流量走VPN

# 检查客户端配置是否有redirect-gateway
grep redirect-gateway client.ovpn

# 问题3：DNS泄露

# 检查DNS配置
cat /etc/resolv.conf
# 应该使用VPN推送的DNS
```

---

## 8.2 WireGuard排查

### 状态检查

```bash
# 查看接口状态
wg show

# 输出示例：
# interface: wg0
#   public key: xxx
#   private key: (hidden)
#   listening port: 51820
#
# peer: xxx
#   endpoint: 1.2.3.4:51820
#   allowed ips: 10.0.0.2/32
#   latest handshake: 5 seconds ago
#   transfer: 100 MiB received, 50 MiB sent

# 详细状态
wg showconf wg0

# 检查接口
ip addr show wg0
ip route | grep wg0
```

### 问题排查

```bash
# 问题1：Peer无法连接

# 检查端口是否开放
ss -ulnp | grep 51820

# 检查防火墙
iptables -L -n | grep 51820
firewall-cmd --list-ports | grep 51820

# 检查公钥配置
wg show wg0 | grep peer
# 确认peer的公钥正确

# 问题2：握手失败

# 查看最后握手时间
wg show wg0 | grep handshake
# 如果是"(none)"，说明握手未成功

# 可能原因：
# - 端口不通
# - 公钥配置错误
# - AllowedIPs配置错误
# - 时钟不同步

# 问题3：可以握手但无法通信

# 检查AllowedIPs
wg show wg0 allowed-ips
# 确保目标IP在AllowedIPs范围内

# 检查路由
ip route get 10.0.0.2
# 应该走wg0接口

# 检查IP转发
sysctl net.ipv4.ip_forward
```

---

# 九、云安全组排查

## 9.1 AWS安全组

```bash
# 查看安全组规则
aws ec2 describe-security-groups --group-ids sg-xxxxx

# 格式化输出
aws ec2 describe-security-groups --group-ids sg-xxxxx \
    --query 'SecurityGroups[*].[GroupId,GroupName,IpPermissions]' \
    --output table

# 查看入站规则
aws ec2 describe-security-groups --group-ids sg-xxxxx \
    --query 'SecurityGroups[*].IpPermissions[*].[IpProtocol,FromPort,ToPort,IpRanges]'

# 添加入站规则
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 8080 \
    --cidr 0.0.0.0/0

# 删除入站规则
aws ec2 revoke-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 8080 \
    --cidr 0.0.0.0/0

# 检查NACL（网络ACL）
aws ec2 describe-network-acls --filters "Name=vpc-id,Values=vpc-xxxxx"
```

## 9.2 阿里云安全组

```bash
# 查看安全组规则
aliyun ecs DescribeSecurityGroupAttribute --SecurityGroupId sg-xxxxx

# 添加入站规则
aliyun ecs AuthorizeSecurityGroup \
    --SecurityGroupId sg-xxxxx \
    --IpProtocol tcp \
    --PortRange 8080/8080 \
    --SourceCidrIp 0.0.0.0/0

# 删除规则
aliyun ecs RevokeSecurityGroup \
    --SecurityGroupId sg-xxxxx \
    --IpProtocol tcp \
    --PortRange 8080/8080 \
    --SourceCidrIp 0.0.0.0/0
```

## 9.3 云安全组排查要点

```bash
# 常见问题：

# 1. 入站规则未开放
# - 检查是否有对应端口的ALLOW规则
# - 检查源IP范围是否正确

# 2. 出站规则限制
# - 默认通常允许所有出站
# - 但有些场景会限制

# 3. NACL优先级高于安全组
# - AWS: 检查子网关联的NACL
# - NACL是有状态的，入站出站都要配置

# 4. 安全组规则数量限制
# - AWS默认60条入站+60条出站
# - 可能需要申请提升

# 排查步骤：
# 1. 确认实例关联的安全组
# 2. 检查安全组入站规则
# 3. 检查安全组出站规则
# 4. 检查NACL（如适用）
# 5. 检查路由表
# 6. 检查实例内部防火墙
```

---

# 十、网络诊断综合脚本

```bash
#!/bin/bash
# network_full_diagnose.sh - 网络完整诊断

TARGET=${1:-"8.8.8.8"}
PORT=${2:-"443"}

echo "===== 网络完整诊断 ====="
echo "目标: $TARGET:$PORT"
echo "时间: $(date)"
echo ""

echo "=== 1. 基础连通性 ==="
ping -c 5 $TARGET
echo ""

echo "=== 2. 端口检测 ==="
nc -zv -w 5 $TARGET $PORT 2>&1
echo ""

echo "=== 3. 路由追踪 ==="
traceroute -n -m 15 $TARGET 2>/dev/null | head -20
echo ""

echo "=== 4. DNS解析 ==="
dig +short $TARGET 2>/dev/null || nslookup $TARGET 2>/dev/null
echo ""

echo "=== 5. 本地网卡状态 ==="
ip -s link show | head -30
echo ""

echo "=== 6. 路由表 ==="
ip route
echo ""

echo "=== 7. 防火墙规则 ==="
echo "--- iptables ---"
iptables -L -n 2>/dev/null | head -30
echo ""
echo "--- firewalld ---"
firewall-cmd --list-all 2>/dev/null || echo "firewalld未运行"
echo ""

echo "=== 8. 连接状态统计 ==="
ss -s
echo ""

echo "=== 9. 监听端口 ==="
ss -tlnp | head -20
echo ""

echo "=== 10. 连接跟踪 ==="
cat /proc/sys/net/netfilter/nf_conntrack_count 2>/dev/null
cat /proc/sys/net/netfilter/nf_conntrack_max 2>/dev/null
echo ""

echo "===== 诊断完成 ====="
```

---

## 总结

**排查三板斧**：
1. **ping/traceroute/mtr** - 确认连通性和路径
2. **ss/netstat** - 确认本地连接状态
3. **tcpdump/Wireshark** - 深入分析报文

**防火墙速查**：
| 工具 | 查看规则 | 添加规则 |
|------|----------|----------|
| iptables | `iptables -L -n -v` | `iptables -A INPUT -p tcp --dport 80 -j ACCEPT` |
| nftables | `nft list ruleset` | `nft add rule inet filter input tcp dport 80 accept` |
| firewalld | `firewall-cmd --list-all` | `firewall-cmd --add-port=80/tcp` |

**VPN排查要点**：
1. 检查服务端口是否监听
2. 检查防火墙是否放行
3. 检查IP转发是否开启
4. 检查路由是否正确

**记住层次**：
- 物理层 → 网线、网口指示灯
- 数据链路层 → 网卡状态、ARP
- 网络层 → 路由、防火墙、IP
- 传输层 → 端口、TCP状态
- 应用层 → 协议、配置
