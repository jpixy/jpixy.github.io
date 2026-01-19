+++
title = "17.网络故障排查"
date = 2026-01-19
description = "网络故障诊断：排查思路、常用工具、典型问题分析、实战案例"
[taxonomies]
tags = ["网络", "故障排查", "运维"]
+++

## 排查思路

### 分层排查法

**按OSI/TCP模型从下往上**：

```
物理层 → 链路层 → 网络层 → 传输层 → 应用层

1. 网线/光纤是否连接？
2. 网卡是否UP？MAC地址学习？
3. IP配置正确？路由可达？
4. 端口是否监听？防火墙？
5. 应用是否正常响应？
```

### 二分排查法

**缩小问题范围**：

```
客户端 ←→ 网络 ←→ 服务端

1. 先确定问题在哪一侧
2. 再细分定位
```

### 对比排查法

**与正常环境对比**：

- 同一服务的其他实例
- 同一机器的其他服务
- 之前正常的配置

---

## 常用诊断命令

### 连通性测试

**ping**：
```bash
# 基本测试
ping 192.168.1.1

# 指定次数
ping -c 5 192.168.1.1

# 指定包大小
ping -s 1472 192.168.1.1  # 测试MTU

# 指定源IP
ping -I eth0 192.168.1.1
```

**traceroute/mtr**：
```bash
# 追踪路由
traceroute 8.8.8.8

# mtr（持续监测）
mtr 8.8.8.8

# TCP模式（穿透防火墙）
traceroute -T -p 80 example.com
```

### DNS诊断

**dig**：
```bash
# 查询A记录
dig example.com

# 查询指定类型
dig example.com MX

# 追踪解析过程
dig +trace example.com

# 指定DNS服务器
dig @8.8.8.8 example.com
```

**nslookup**：
```bash
nslookup example.com
nslookup -type=MX example.com
```

### 端口与连接

**ss/netstat**：
```bash
# 查看监听端口
ss -tlnp
netstat -tlnp

# 查看所有连接
ss -anp

# 查看连接状态统计
ss -s

# 查看特定端口
ss -tlnp | grep :80
```

**telnet/nc**：
```bash
# 测试端口连通
telnet 192.168.1.1 80
nc -zv 192.168.1.1 80

# 端口扫描
nc -zv 192.168.1.1 1-1000
```

### 网络配置

**ip命令**：
```bash
# 查看IP地址
ip addr show

# 查看路由表
ip route show

# 查看ARP表
ip neigh show

# 查看网卡状态
ip link show
```

**route**：
```bash
route -n
```

### 抓包分析

**tcpdump**：
```bash
# 抓取指定接口
tcpdump -i eth0

# 抓取指定主机
tcpdump -i eth0 host 192.168.1.1

# 抓取指定端口
tcpdump -i eth0 port 80

# 抓取并保存
tcpdump -i eth0 -w capture.pcap

# 读取pcap文件
tcpdump -r capture.pcap

# 详细显示
tcpdump -i eth0 -vvv -X
```

**常用过滤表达式**：
```bash
# 组合条件
tcpdump -i eth0 'host 192.168.1.1 and port 80'
tcpdump -i eth0 'src host 192.168.1.1 or dst host 192.168.1.2'

# TCP标志
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'
tcpdump -i eth0 'tcp[tcpflags] & tcp-rst != 0'
```

---

## 典型问题分析

### 网络不通

**排查步骤**：

1. **检查本机配置**
```bash
ip addr show      # IP地址正确？
ip route show     # 默认路由存在？
```

2. **检查本地网络**
```bash
ping 网关IP       # 网关可达？
arping 网关IP     # ARP正常？
```

3. **检查远程网络**
```bash
ping 目标IP       # 目标可达？
traceroute 目标IP # 哪一跳断开？
```

4. **检查DNS**
```bash
dig example.com   # DNS解析正常？
```

5. **检查防火墙**
```bash
iptables -L -n    # 本机防火墙
# 检查云安全组
```

### 连接超时

**可能原因**：
- 防火墙阻断
- 服务未监听
- 网络延迟高
- 路由不可达

**排查**：
```bash
# 检查服务监听
ss -tlnp | grep :端口

# 检查防火墙
iptables -L -n | grep 端口

# 测试连通
telnet IP 端口
nc -zv IP 端口

# 抓包确认
tcpdump -i eth0 port 端口
```

### 连接被拒绝

**Connection refused**：
- 服务未运行
- 端口未监听
- 绑定地址错误

```bash
# 检查服务状态
systemctl status 服务名

# 检查监听
ss -tlnp | grep 端口

# 检查绑定地址（127.0.0.1 vs 0.0.0.0）
```

### 间歇性丢包

**排查**：
```bash
# 持续ping
ping -c 1000 目标

# mtr查看每跳丢包
mtr 目标

# 检查网卡错误
ip -s link show eth0
ethtool -S eth0 | grep error
```

**可能原因**：
- 网络拥塞
- 设备过载
- 链路质量差
- MTU问题

### 延迟高

**排查**：
```bash
# 基础延迟
ping 目标

# 每跳延迟
mtr 目标

# 检查网络负载
sar -n DEV 1

# 检查CPU负载
top
```

**可能原因**：
- 网络拥塞
- 设备处理慢
- 路由绕路
- 应用处理慢

### DNS解析问题

**症状**：域名无法解析，但IP可访问

**排查**：
```bash
# 检查DNS配置
cat /etc/resolv.conf

# 测试DNS服务器
dig @DNS服务器 域名

# 检查本地缓存
# systemd-resolved
resolvectl status
```

### TCP连接问题

**TIME_WAIT过多**：
```bash
ss -ant | grep TIME-WAIT | wc -l

# 如果过多，考虑调整
sysctl -w net.ipv4.tcp_tw_reuse=1
```

**CLOSE_WAIT过多**：
```bash
ss -ant | grep CLOSE-WAIT | wc -l

# 通常是应用未正确关闭连接
# 需要检查应用代码
```

**SYN_RECV过多**：
```bash
ss -ant | grep SYN-RECV | wc -l

# 可能是SYN Flood攻击或连接队列满
netstat -st | grep -i syn
```

---

## 实战案例

### 案例一：Web服务无法访问

**现象**：用户报告网站打不开

**排查过程**：
```bash
# 1. 确认问题
curl http://example.com  # 超时

# 2. DNS检查
dig example.com  # 正常

# 3. ping检查
ping 服务器IP  # 正常

# 4. 端口检查
nc -zv 服务器IP 80  # 超时

# 5. 服务器上检查
ss -tlnp | grep 80  # 正常监听

# 6. 防火墙检查
iptables -L -n  # 发现80端口被DROP

# 7. 修复
iptables -I INPUT -p tcp --dport 80 -j ACCEPT
```

### 案例二：服务间调用超时

**现象**：服务A调用服务B超时

**排查过程**：
```bash
# 1. 确认问题范围
# 所有请求都超时？还是部分？

# 2. 服务B状态
curl http://服务B:端口/health  # 健康检查

# 3. 网络连通
ping 服务B的IP

# 4. 抓包分析
tcpdump -i eth0 host 服务B的IP and port 端口

# 发现：SYN发出，但没有SYN-ACK
# 原因：服务B的连接队列满

# 5. 服务B上检查
ss -ltn  # Recv-Q很高
dmesg | grep -i syn  # 有SYN flood警告

# 6. 修复
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
```

### 案例三：偶发性连接失败

**现象**：大约1%的连接失败

**排查过程**：
```bash
# 1. 收集数据
# 失败的请求特征？时间规律？

# 2. 网络层检查
mtr 目标  # 运行较长时间，观察丢包

# 3. 发现某一跳偶发丢包
# 联系网络团队

# 4. 或者是连接数问题
ss -s  # 检查连接数
sysctl net.ipv4.ip_local_port_range  # 检查可用端口

# 5. 如果端口不足
sysctl -w net.ipv4.ip_local_port_range="1024 65535"
```

---

## 排查清单

### 网络不通清单

- [ ] IP地址配置正确
- [ ] 子网掩码正确
- [ ] 默认网关配置
- [ ] DNS配置
- [ ] 路由表正确
- [ ] 防火墙规则
- [ ] 安全组规则
- [ ] 物理连接

### 服务不可达清单

- [ ] 服务进程运行
- [ ] 端口正常监听
- [ ] 绑定地址正确（0.0.0.0）
- [ ] 本机防火墙
- [ ] 网络防火墙
- [ ] 安全组

### 性能问题清单

- [ ] 网络带宽
- [ ] 网络延迟
- [ ] 丢包率
- [ ] 连接数
- [ ] 端口范围
- [ ] TCP参数
- [ ] 应用层问题

---

## 总结

| 问题类型 | 常用工具 | 关键检查点 |
|----------|----------|------------|
| 连通性 | ping, traceroute | 网关、路由、防火墙 |
| DNS | dig, nslookup | 配置、解析、缓存 |
| 端口 | ss, nc, telnet | 监听、防火墙 |
| 性能 | mtr, iperf, sar | 带宽、延迟、丢包 |
| 深度分析 | tcpdump, wireshark | 协议细节 |

**排查原则**：
1. 先确认问题，收集信息
2. 分层排查，缩小范围
3. 对比正常环境
4. 记录过程，便于复盘
