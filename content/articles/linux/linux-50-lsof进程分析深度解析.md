+++
title = "50. lsof进程分析深度解析"
date = 2026-01-31
weight = 50000
description = "lsof深度解析：文件描述符、进程打开文件、网络连接、故障排查"
[taxonomies]
tags = ["Linux", "lsof", "进程", "文件描述符", "调试"]
+++

# lsof 进程分析深度解析

本文深入解析 lsof（List Open Files）工具的工作原理，包括文件描述符分析、网络连接查看、故障排查等核心技术。

---

## 一、lsof 概述

### 1.1 什么是 lsof

**lsof**（List Open Files）用于显示系统中打开的文件，包括：
- 普通文件
- 目录
- 网络连接（套接字）
- 管道
- 设备文件
- 内存映射文件

### 1.2 核心概念

```
Unix 哲学：一切皆文件

lsof 可以查看：
- 进程打开的文件
- 文件被哪些进程使用
- 网络连接
- 端口占用
```

### 1.3 工作原理

```mermaid
graph TB
    A[lsof] --> B[读取 /proc]
    B --> C[/proc/PID/fd]
    B --> D[/proc/PID/maps]
    B --> E[/proc/net/*]
    C --> F[文件描述符]
    D --> G[内存映射]
    E --> H[网络连接]
```

---

## 二、基本使用

### 2.1 基本语法

```bash
lsof [选项] [文件/目录]
```

### 2.2 常用选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `-p PID` | 指定进程 | `lsof -p 1234` |
| `-u user` | 指定用户 | `lsof -u root` |
| `-c cmd` | 指定命令 | `lsof -c nginx` |
| `-i` | 网络连接 | `lsof -i` |
| `-i :port` | 指定端口 | `lsof -i :80` |
| `-t` | 只输出 PID | `lsof -t -i :80` |
| `-n` | 不解析主机名 | `lsof -n` |
| `-P` | 不解析端口名 | `lsof -P` |
| `+D dir` | 目录下所有文件 | `lsof +D /var/log` |
| `+L1` | 已删除文件 | `lsof +L1` |
| `-a` | AND 条件 | `lsof -u root -a -c nginx` |

### 2.3 输出字段

```bash
$ lsof -p 1234
COMMAND  PID USER   FD   TYPE DEVICE SIZE/OFF    NODE NAME
nginx   1234 root  cwd    DIR  253,1     4096       2 /
nginx   1234 root  rtd    DIR  253,1     4096       2 /
nginx   1234 root  txt    REG  253,1  1234567  123456 /usr/sbin/nginx
nginx   1234 root  mem    REG  253,1   234567  234567 /lib/x86_64-linux-gnu/libc.so.6
nginx   1234 root    0u   CHR    1,3      0t0       6 /dev/null
nginx   1234 root    1u   REG  253,1    12345  345678 /var/log/nginx/access.log
nginx   1234 root    6u  IPv4  56789      0t0     TCP *:80 (LISTEN)
```

| 字段 | 说明 |
|------|------|
| COMMAND | 命令名 |
| PID | 进程 ID |
| USER | 用户 |
| FD | 文件描述符 |
| TYPE | 文件类型 |
| DEVICE | 设备号 |
| SIZE/OFF | 大小/偏移 |
| NODE | inode 号 |
| NAME | 文件名 |

### 2.4 FD 字段说明

| FD | 说明 |
|-----|------|
| cwd | 当前工作目录 |
| rtd | 根目录 |
| txt | 程序代码 |
| mem | 内存映射文件 |
| 0u, 1u, 2u | stdin, stdout, stderr |
| 3u, 4r, 5w | 数字=fd，u=读写，r=只读，w=只写 |

---

## 三、文件分析

### 3.1 查看文件被谁使用

```bash
# 查看特定文件
lsof /var/log/syslog

# 查看多个文件
lsof /var/log/syslog /var/log/auth.log

# 查看目录下所有打开的文件
lsof +D /var/log

# 递归查看（更快）
lsof +d /var/log
```

### 3.2 查找删除但未释放的文件

```bash
# 显示已删除但仍被打开的文件
lsof +L1

# 输出示例
COMMAND  PID USER   FD   TYPE DEVICE SIZE/OFF NLINK    NODE NAME
nginx   1234 root    5w   REG  253,1 1234567890     0  123456 /var/log/nginx/access.log (deleted)

# 这些文件空间不会释放，直到进程关闭
# 重启进程或 truncate 可以释放空间
```

### 3.3 查看进程打开的文件

```bash
# 按 PID
lsof -p 1234

# 按命令名
lsof -c nginx

# 按用户
lsof -u www-data

# 组合条件（AND）
lsof -u www-data -a -c nginx

# 组合条件（OR，默认）
lsof -u www-data -c nginx
```

---

## 四、网络分析

### 4.1 查看网络连接

```bash
# 所有网络连接
lsof -i

# IPv4 连接
lsof -i4

# IPv6 连接
lsof -i6

# TCP 连接
lsof -i TCP

# UDP 连接
lsof -i UDP
```

### 4.2 端口分析

```bash
# 查看端口占用
lsof -i :80
lsof -i :443
lsof -i :22

# 端口范围
lsof -i :1-1024

# 只显示 LISTEN
lsof -i -sTCP:LISTEN

# 只显示 ESTABLISHED
lsof -i -sTCP:ESTABLISHED

# 不解析（更快）
lsof -i :80 -n -P
```

### 4.3 连接分析

```bash
# 特定协议和端口
lsof -i TCP:80
lsof -i UDP:53

# 特定主机
lsof -i @192.168.1.1
lsof -i @192.168.1.1:80

# 查看与某主机的所有连接
lsof -i @remote.server.com

# 组合
lsof -i TCP@192.168.1.1:80
```

### 4.4 实用网络查询

```bash
# 查看谁在监听 80 端口
lsof -i :80 -sTCP:LISTEN

# 查看某进程的网络连接
lsof -i -a -p 1234

# 查看某用户的网络连接
lsof -i -a -u nginx

# 只输出 PID（用于脚本）
lsof -t -i :80
```

---

## 五、故障排查

### 5.1 磁盘空间问题

```bash
# 场景：df 显示磁盘满，但 du 找不到大文件

# 查找已删除但未释放的文件
lsof +L1 | sort -k7 -rn | head

# 查看大文件
lsof +L1 | awk '$7 > 1000000000 {print}'

# 解决方案
# 1. 重启占用进程
# 2. 或清空文件（不删除）
# echo > /proc/PID/fd/FD
```

### 5.2 端口占用问题

```bash
# 场景：启动服务报端口已占用

# 查看端口占用
lsof -i :8080

# 获取 PID
lsof -t -i :8080

# 查看进程详情
lsof -i :8080 | xargs ps -p

# 强制释放（谨慎）
kill $(lsof -t -i :8080)
```

### 5.3 文件锁问题

```bash
# 查看文件被谁锁定
lsof /path/to/file

# 查看某进程持有的锁
lsof -p 1234 | grep -E 'REG.*w'
```

### 5.4 文件描述符泄漏

```bash
# 查看进程打开文件数
lsof -p 1234 | wc -l

# 按类型统计
lsof -p 1234 | awk '{print $5}' | sort | uniq -c | sort -rn

# 对比限制
cat /proc/1234/limits | grep "open files"

# 系统级统计
lsof | wc -l
cat /proc/sys/fs/file-nr
```

### 5.5 连接问题

```bash
# 查看 CLOSE_WAIT 连接
lsof -i -sTCP:CLOSE_WAIT

# 查看 TIME_WAIT
lsof -i -sTCP:TIME_WAIT

# 统计连接状态
lsof -i | awk '/TCP/ {print $10}' | sort | uniq -c
```

---

## 六、高级用法

### 6.1 输出格式

```bash
# 只输出 PID
lsof -t -i :80

# 显示字段偏移
lsof -o -p 1234

# 显示实际大小
lsof -s -p 1234

# 重复模式（每 N 秒刷新）
lsof -r 2 -i :80
```

### 6.2 组合条件

```bash
# AND 条件（-a）
lsof -u root -a -c nginx

# OR 条件（默认）
lsof -u root -u www-data

# 复杂条件
lsof -u root -a -c nginx -a -i :80
```

### 6.3 排除过滤

```bash
# 排除某用户
lsof -u ^root

# 排除某命令
lsof -c ^systemd

# 排除多个
lsof -u ^root -u ^www-data
```

---

## 七、实用脚本

### 7.1 监控打开文件数

```bash
#!/bin/bash
# fd_monitor.sh

PID=$1
INTERVAL=${2:-5}

echo "Monitoring file descriptors for PID $PID"

while true; do
    COUNT=$(lsof -p $PID 2>/dev/null | wc -l)
    LIMIT=$(cat /proc/$PID/limits 2>/dev/null | grep "open files" | awk '{print $4}')
    echo "$(date '+%H:%M:%S') FDs: $COUNT / $LIMIT"
    sleep $INTERVAL
done
```

### 7.2 端口监控

```bash
#!/bin/bash
# port_monitor.sh

PORTS="80 443 22 3306"

for port in $PORTS; do
    result=$(lsof -i :$port -sTCP:LISTEN 2>/dev/null)
    if [ -n "$result" ]; then
        echo "Port $port: $(echo "$result" | awk 'NR==2 {print $1, $2}')"
    else
        echo "Port $port: NOT LISTENING"
    fi
done
```

### 7.3 清理已删除文件

```bash
#!/bin/bash
# cleanup_deleted.sh

echo "Finding deleted files still open..."

lsof +L1 2>/dev/null | while read line; do
    if echo "$line" | grep -q "(deleted)"; then
        pid=$(echo "$line" | awk '{print $2}')
        fd=$(echo "$line" | awk '{print $4}' | tr -d 'rwu')
        size=$(echo "$line" | awk '{print $7}')
        name=$(echo "$line" | awk '{print $9}')

        echo "PID: $pid, FD: $fd, Size: $size bytes, File: $name"

        # 可以选择清空文件
        # echo > /proc/$pid/fd/$fd
    fi
done
```

---

## 八、与同类工具对比

| 特性 | lsof | fuser | /proc | ss |
|------|------|-------|-------|-----|
| 文件查看 | ✅ | ✅ | ✅ | ❌ |
| 网络查看 | ✅ | 有限 | ✅ | ✅ |
| 进程信息 | 详细 | 简单 | 详细 | 有限 |
| 速度 | 慢 | 快 | 快 | 快 |
| 过滤能力 | 强 | 弱 | 无 | 强 |

### 8.1 fuser 比较

```bash
# lsof 查看文件使用
lsof /var/log/syslog

# fuser 等效
fuser -v /var/log/syslog

# fuser 终止进程
fuser -k /var/log/syslog
```

---

## 九、高频考点总结

| 考点 | 频率 | 关键知识 |
|------|------|----------|
| 基本用法 | ★★★ | -p、-c、-u、-i |
| 网络分析 | ★★★ | -i :port、-sTCP |
| 文件分析 | ★★☆ | +D、+L1 |
| 故障排查 | ★★★ | 端口占用、文件泄漏 |
| FD 字段 | ★★☆ | cwd、txt、mem、数字 |
| 输出解读 | ★★☆ | TYPE、SIZE、NODE |

---

## 相关文章

- [上一篇：ftrace内核追踪深度解析](@/articles/linux/linux-49-ftrace内核追踪深度解析.md)
- [性能分析与调试](@/articles/linux/linux-08-性能分析与调试.md)
