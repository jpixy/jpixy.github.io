+++
title = "32.进程与服务问题排查实战"
date = 2026-01-21
description = "SRE进程与服务问题排查完整指南：服务启动失败、进程hang住、端口占用、依赖问题的定位与解决"
[taxonomies]
tags = ["SRE", "进程", "服务", "排查", "实战", "systemd"]
+++

## 概述

进程和服务问题是SRE日常工作中最常见的问题类型。本文详细介绍各类进程服务问题的排查思路、命令详解和解决方案。

---

# 一、服务启动失败

## 1.1 systemd服务排查

### 场景：服务无法启动

**第一步：查看服务状态**

```bash
# 查看服务状态
systemctl status nginx

# 输出解读：
# ● nginx.service - A high performance web server
#    Loaded: loaded (/lib/systemd/system/nginx.service; enabled)  ← 配置文件位置和是否开机启动
#    Active: failed (Result: exit-code) since ...                 ← 当前状态
#   Process: 12345 ExecStart=/usr/sbin/nginx (code=exited, status=1/FAILURE)  ← 退出码
#  Main PID: 12345 (code=exited, status=1/FAILURE)
#
# 状态说明：
# - active (running)：正常运行
# - active (exited)：已执行完毕（oneshot类型）
# - inactive (dead)：未运行
# - failed：启动失败
# - activating：正在启动
```

**第二步：查看详细日志**

```bash
# 查看服务日志（最近50行）
journalctl -u nginx -n 50

# 参数详解：
# -u nginx      指定服务单元
# -n 50         显示最近50行
# --no-pager    不使用分页器，直接输出
# -f            实时跟踪日志（类似tail -f）
# -e            跳到日志末尾
# -b            只显示本次启动后的日志
# -b -1         显示上一次启动的日志
# --since "1 hour ago"   显示最近1小时
# --since "2024-01-21 10:00:00"  指定时间

# 实时跟踪服务日志
journalctl -u nginx -f

# 查看启动失败时的日志
journalctl -u nginx -b --no-pager | tail -100

# 查看所有相关日志（包括子进程）
journalctl -u nginx --no-pager -o verbose
```

**第三步：检查配置文件**

```bash
# 查看服务配置文件
systemctl cat nginx

# 验证配置文件语法（以nginx为例）
nginx -t

# 查看服务依赖
systemctl list-dependencies nginx

# 检查服务是否被mask
systemctl is-enabled nginx
# 如果显示 masked，需要unmask
systemctl unmask nginx
```

### 常见启动失败原因

#### 原因1：端口被占用

```bash
# 检查端口占用
ss -tlnp | grep :80

# 命令参数详解：
# -t    显示TCP连接
# -l    只显示监听状态
# -n    显示数字格式（不解析服务名）
# -p    显示进程信息

# 输出示例：
# LISTEN  0  128  0.0.0.0:80  0.0.0.0:*  users:(("apache2",pid=1234,fd=4))
# 说明端口80被apache2进程（PID 1234）占用

# 更详细的信息
lsof -i :80

# 参数详解：
# -i :80    显示使用80端口的进程
# -i TCP    只显示TCP连接
# -i @host  显示连接到指定主机的

# 杀死占用端口的进程
kill $(lsof -t -i :80)
# -t 参数只输出PID，便于管道使用
```

#### 原因2：权限问题

```bash
# 检查服务运行用户
grep -E "^User=|^Group=" /lib/systemd/system/nginx.service

# 检查文件权限
ls -la /var/log/nginx/
ls -la /etc/nginx/

# 检查目录是否可写
sudo -u www-data touch /var/log/nginx/test
# 如果失败，修复权限
chown -R www-data:www-data /var/log/nginx/

# 检查SELinux（CentOS/RHEL）
getenforce
# 如果是 Enforcing，可能是SELinux阻止
# 查看SELinux日志
ausearch -m avc -ts recent
# 临时禁用测试
setenforce 0
```

#### 原因3：依赖服务未启动

```bash
# 查看服务依赖
systemctl list-dependencies nginx

# 查看依赖的服务状态
systemctl list-dependencies nginx --all | xargs -I {} systemctl is-active {}

# 启动所有依赖
systemctl start nginx  # systemd会自动启动依赖

# 检查是否有循环依赖
systemd-analyze verify nginx.service
```

#### 原因4：资源限制

```bash
# 查看服务的资源限制
systemctl show nginx | grep -E "Limit|Memory|CPU"

# 查看进程限制
cat /proc/$(pgrep -f nginx)/limits

# 修改systemd服务限制
# 创建override配置
systemctl edit nginx
# 添加：
# [Service]
# LimitNOFILE=65535
# LimitNPROC=65535
# MemoryMax=2G

# 或直接编辑
mkdir -p /etc/systemd/system/nginx.service.d/
cat > /etc/systemd/system/nginx.service.d/limits.conf << EOF
[Service]
LimitNOFILE=65535
LimitNPROC=65535
EOF

# 重新加载配置
systemctl daemon-reload
systemctl restart nginx
```

---

## 1.2 传统init服务排查

```bash
# SysVinit服务
service nginx status
service nginx start

# 查看启动脚本
cat /etc/init.d/nginx

# 手动运行启动脚本调试
bash -x /etc/init.d/nginx start

# 检查运行级别
runlevel
chkconfig --list nginx  # CentOS 6
update-rc.d nginx defaults  # Debian/Ubuntu
```

---

# 二、进程问题排查

## 2.1 进程无响应（Hang）

### 场景：进程存在但不响应请求

**第一步：确认进程状态**

```bash
# 查看进程基本信息
ps aux | grep nginx

# 输出列详解：
# USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
# root      1234  0.0  0.1  12345  6789 ?        Ss   10:00   0:00 nginx: master
#
# STAT列含义：
# S - 睡眠（可中断）
# R - 运行中
# D - 不可中断睡眠（通常是IO等待）← 进程可能卡住
# Z - 僵尸进程
# T - 停止
# s - session leader
# + - 前台进程组

# 查看进程详细状态
cat /proc/<PID>/status

# 关键字段：
# State: S (sleeping)   ← 进程状态
# Threads: 10           ← 线程数
# voluntary_ctxt_switches: 1234     ← 自愿上下文切换
# nonvoluntary_ctxt_switches: 56    ← 非自愿上下文切换
```

**第二步：查看进程在做什么**

```bash
# 查看进程调用栈（内核态）
cat /proc/<PID>/stack

# 输出示例：
# [<ffffffff812345>] do_wait+0x123/0x456
# [<ffffffff812346>] sys_wait4+0x78/0x90
# 可以看出进程卡在哪个系统调用

# 查看进程等待的通道
cat /proc/<PID>/wchan
# 输出如 "poll_schedule_timeout" 表示在等待IO

# 使用strace附加到进程
strace -p <PID>

# strace常用参数：
# -p <PID>     附加到进程
# -f           跟踪fork的子进程
# -e trace=network  只跟踪网络相关调用
# -e trace=file     只跟踪文件相关调用
# -e trace=process  只跟踪进程相关调用
# -t           显示时间戳
# -T           显示每个调用耗时
# -c           统计每个调用的次数和时间
# -o file      输出到文件

# 示例：查看进程在等待什么
strace -p <PID> -e trace=network -T

# 输出示例：
# recvfrom(5, ...) = -1 EAGAIN  <0.000012>
# poll([{fd=5, events=POLLIN}], 1, 30000 <-- 卡在这里等待30秒超时
```

**第三步：分析进程资源**

```bash
# 查看进程打开的文件
lsof -p <PID>

# lsof输出列详解：
# COMMAND  PID  USER   FD   TYPE  DEVICE  SIZE/OFF  NODE  NAME
# nginx   1234  root  cwd    DIR   8,1      4096   123   /var/www
# nginx   1234  root  txt    REG   8,1    123456   456   /usr/sbin/nginx
# nginx   1234  root    3u  IPv4  12345     0t0    TCP  *:80 (LISTEN)
#
# FD列：
# cwd - 当前工作目录
# txt - 程序代码
# mem - 内存映射文件
# 数字+r/w/u - 文件描述符（r读/w写/u读写）

# 统计进程打开的文件数
lsof -p <PID> | wc -l

# 查看网络连接
lsof -p <PID> -i

# 查看进程连接的远程主机
ss -tp | grep <PID>
```

### 进程hang常见原因

| 原因 | 特征 | 解决方法 |
|------|------|----------|
| 等待锁 | strace显示futex等待 | 分析死锁或等待超时 |
| 等待IO | 状态为D，栈显示IO函数 | 检查磁盘/网络 |
| 等待网络 | strace显示recv/connect卡住 | 检查目标服务 |
| 死循环 | CPU高但无响应 | 分析代码逻辑 |

---

## 2.2 进程异常退出

### 场景：进程突然消失

**第一步：查看退出信息**

```bash
# 查看系统日志
dmesg | tail -50
journalctl -k | tail -50

# 检查是否被OOM杀死
dmesg | grep -i "oom\|killed"
journalctl -k | grep -i oom

# 检查是否收到信号
# 如果有core dump
ls -la /var/crash/
ls -la /tmp/core.*

# 查看core dump配置
cat /proc/sys/kernel/core_pattern
ulimit -c
```

**第二步：分析退出码**

```bash
# 查看最后退出码
echo $?

# systemd服务查看
systemctl status nginx
# 查看 "status=N" 部分

# 退出码含义：
# 0   - 正常退出
# 1   - 一般错误
# 2   - 命令使用错误
# 126 - 权限问题或不是可执行文件
# 127 - 命令找不到
# 128+N - 收到信号N
#   137 (128+9)  - SIGKILL，被强制杀死
#   143 (128+15) - SIGTERM，正常终止信号
#   139 (128+11) - SIGSEGV，段错误
#   134 (128+6)  - SIGABRT，程序abort
```

**第三步：分析core dump**

```bash
# 启用core dump
ulimit -c unlimited

# 设置core文件位置
echo "/var/crash/core.%e.%p.%t" > /proc/sys/kernel/core_pattern

# 使用gdb分析
gdb /path/to/program /path/to/core

# gdb常用命令：
(gdb) bt          # 查看调用栈
(gdb) bt full     # 查看完整调用栈（含局部变量）
(gdb) info threads  # 查看所有线程
(gdb) thread 2    # 切换到线程2
(gdb) frame 3     # 切换到栈帧3
(gdb) print var   # 打印变量值
(gdb) quit        # 退出
```

---

## 2.3 僵尸进程

### 场景：系统中存在大量僵尸进程

**定位僵尸进程**

```bash
# 查找僵尸进程
ps aux | awk '$8=="Z" {print}'

# 或使用状态过滤
ps -eo pid,ppid,stat,cmd | awk '$3~/Z/'

# 统计僵尸进程数量
ps aux | awk '$8=="Z"' | wc -l

# 查看僵尸进程的父进程
ps -eo pid,ppid,stat,cmd | awk '$3~/Z/ {print "Zombie:", $1, "Parent:", $2}'

# 找出产生最多僵尸的父进程
ps -eo ppid,stat | awk '$2~/Z/ {print $1}' | sort | uniq -c | sort -rn
```

**解决僵尸进程**

```bash
# 僵尸进程无法直接kill，需要处理父进程

# 方法1：让父进程回收
# 发送SIGCHLD信号提醒父进程
kill -SIGCHLD <PPID>

# 方法2：杀死父进程（僵尸会被init收养并回收）
kill <PPID>

# 方法3：如果父进程是重要服务，重启它
systemctl restart <service>

# 预防：检查程序是否正确调用wait()
# 程序示例：
# while ((pid = waitpid(-1, &status, WNOHANG)) > 0) {
#     // 处理子进程退出
# }
```

---

## 2.4 进程资源泄漏

### 文件描述符泄漏

```bash
# 查看进程打开的文件数
ls /proc/<PID>/fd | wc -l

# 或使用lsof
lsof -p <PID> | wc -l

# 查看限制
cat /proc/<PID>/limits | grep "open files"

# 持续监控文件描述符增长
while true; do
    count=$(ls /proc/<PID>/fd 2>/dev/null | wc -l)
    echo "$(date '+%H:%M:%S') FD count: $count"
    sleep 5
done

# 查看打开的是什么类型的文件
lsof -p <PID> | awk '{print $5}' | sort | uniq -c | sort -rn
# 常见类型：REG(普通文件), IPv4(网络), unix(socket), FIFO(管道)

# 找出大量相同的文件描述符（可能泄漏）
lsof -p <PID> | awk '{print $9}' | sort | uniq -c | sort -rn | head -20
```

### 内存泄漏

```bash
# 监控进程内存增长
while true; do
    rss=$(ps -o rss= -p <PID>)
    echo "$(date '+%H:%M:%S') RSS: ${rss} KB"
    sleep 60
done

# 使用pidstat监控
pidstat -r -p <PID> 60

# 参数详解：
# -r   显示内存统计
# -p   指定PID
# 60   每60秒采样一次

# 输出列：
# minflt/s - 每秒minor fault（不需要磁盘IO的页错误）
# majflt/s - 每秒major fault（需要磁盘IO的页错误）
# VSZ      - 虚拟内存大小
# RSS      - 常驻内存大小
# %MEM     - 内存使用百分比
```

---

# 三、端口和网络问题

## 3.1 端口排查

### 查看监听端口

```bash
# ss命令（推荐，更快）
ss -tlnp

# 参数详解：
# -t   TCP
# -u   UDP
# -l   只显示监听状态
# -n   不解析服务名
# -p   显示进程信息
# -a   显示所有（包括非监听）
# -e   显示扩展信息
# -m   显示内存使用
# -i   显示TCP内部信息

# 只看特定端口
ss -tlnp | grep :8080

# 统计各状态连接数
ss -ant | awk '{print $1}' | sort | uniq -c

# netstat命令（传统，较慢）
netstat -tlnp

# 参数基本相同：
# -t   TCP
# -u   UDP
# -l   监听
# -n   数字格式
# -p   显示进程
# -a   所有连接
# -e   扩展信息
# -s   统计信息
```

### 端口被占用

```bash
# 方法1：使用ss
ss -tlnp | grep :80

# 方法2：使用lsof
lsof -i :80

# 参数详解：
# -i :80          端口80
# -i TCP:80       TCP端口80
# -i @hostname    连接到hostname
# -i TCP@host:80  TCP连接到host的80

# 方法3：使用fuser
fuser 80/tcp

# 显示详细信息
fuser -v 80/tcp

# 直接杀死占用进程（谨慎使用）
fuser -k 80/tcp
```

---

## 3.2 连接问题

### 连接数过多

```bash
# 查看总连接数
ss -s

# 输出解读：
# TCP:   1234 (estab 567, closed 234, orphaned 12, timewait 345)
# estab    - 建立的连接
# closed   - 关闭的连接
# orphaned - 孤儿连接（无进程关联）
# timewait - TIME_WAIT状态

# 查看各状态连接数
ss -ant | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn

# 查看连接到特定端口的客户端IP统计
ss -ant | grep :80 | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20

# 查看ESTABLISHED连接最多的IP
ss -ant state established | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10

# 查看TIME_WAIT连接
ss -ant state time-wait | wc -l
```

### 连接超时问题

```bash
# 查看TCP超时设置
sysctl net.ipv4.tcp_keepalive_time
sysctl net.ipv4.tcp_keepalive_intvl
sysctl net.ipv4.tcp_keepalive_probes

# 参数含义：
# tcp_keepalive_time  - 多久开始发送keepalive探测（默认7200秒）
# tcp_keepalive_intvl - 探测间隔（默认75秒）
# tcp_keepalive_probes - 探测次数（默认9次）

# 查看TCP重传设置
sysctl net.ipv4.tcp_retries1
sysctl net.ipv4.tcp_retries2

# 优化设置
sysctl -w net.ipv4.tcp_keepalive_time=600
sysctl -w net.ipv4.tcp_keepalive_intvl=60
sysctl -w net.ipv4.tcp_keepalive_probes=3
```

---

# 四、服务依赖问题

## 4.1 依赖检查

```bash
# 检查服务依赖
systemctl list-dependencies nginx

# 反向依赖（谁依赖这个服务）
systemctl list-dependencies nginx --reverse

# 检查依赖服务状态
for dep in $(systemctl list-dependencies nginx --plain); do
    status=$(systemctl is-active $dep)
    echo "$dep: $status"
done

# 检查端口依赖
# 比如应用依赖MySQL 3306
nc -zv localhost 3306
# 如果失败，检查MySQL状态
systemctl status mysql
```

## 4.2 启动顺序问题

```bash
# 查看服务启动顺序配置
grep -E "After=|Before=|Requires=|Wants=" /lib/systemd/system/nginx.service

# 配置解释：
# After=network.target    - 在network.target之后启动
# Before=xxx              - 在xxx之前启动
# Requires=xxx            - 强依赖，xxx失败则本服务也失败
# Wants=xxx               - 弱依赖，xxx失败不影响本服务

# 分析启动时间
systemd-analyze blame | head -20

# 查看启动时间线
systemd-analyze plot > boot.svg

# 查看关键链
systemd-analyze critical-chain nginx.service
```

---

# 五、诊断工具详解

## 5.1 ps命令详解

```bash
# 基础用法
ps aux          # BSD风格，显示所有进程
ps -ef          # Unix风格，显示所有进程

# 自定义输出列
ps -eo pid,ppid,user,%cpu,%mem,stat,start,time,command

# 可用列（常用）：
# pid     - 进程ID
# ppid    - 父进程ID
# pgid    - 进程组ID
# sid     - 会话ID
# user    - 用户名
# uid     - 用户ID
# %cpu    - CPU使用率
# %mem    - 内存使用率
# vsz     - 虚拟内存大小
# rss     - 常驻内存大小
# stat    - 进程状态
# start   - 启动时间
# time    - 累计CPU时间
# command - 完整命令
# args    - 命令参数
# wchan   - 等待通道
# nlwp    - 线程数

# 按CPU排序
ps aux --sort=-%cpu | head -10

# 按内存排序
ps aux --sort=-%mem | head -10

# 显示线程
ps -eLf | grep nginx
# -L 显示线程
# LWP列是线程ID

# 树形显示
ps auxf
pstree -p <PID>
```

## 5.2 top/htop详解

```bash
# top交互命令：
# 1   - 显示每个CPU核心
# M   - 按内存排序
# P   - 按CPU排序
# T   - 按时间排序
# H   - 显示线程
# c   - 显示完整命令
# k   - 杀死进程
# r   - 调整nice值
# f   - 选择显示列
# q   - 退出

# top批处理模式（用于脚本）
top -bn1 | head -20
# -b  批处理模式
# -n1 只刷新1次

# 只显示特定进程
top -p <PID>

# htop推荐设置
# F2进入设置：
# - Display options: 勾选 "Show program path"
# - Columns: 添加 NLWP(线程数), IO_RATE
```

## 5.3 进程诊断脚本

```bash
#!/bin/bash
# process_diagnose.sh - 进程诊断脚本

PID=$1

if [ -z "$PID" ]; then
    echo "Usage: $0 <PID>"
    exit 1
fi

if [ ! -d "/proc/$PID" ]; then
    echo "Process $PID does not exist"
    exit 1
fi

echo "===== 进程诊断报告: PID $PID ====="
echo "时间: $(date)"
echo ""

echo "--- 1. 基本信息 ---"
ps -p $PID -o pid,ppid,user,%cpu,%mem,stat,start,time,command
echo ""

echo "--- 2. 详细状态 ---"
cat /proc/$PID/status | grep -E "Name|State|Pid|PPid|Threads|VmSize|VmRSS|VmSwap"
echo ""

echo "--- 3. 命令行 ---"
cat /proc/$PID/cmdline | tr '\0' ' '
echo -e "\n"

echo "--- 4. 工作目录 ---"
ls -l /proc/$PID/cwd
echo ""

echo "--- 5. 打开文件数 ---"
echo "Count: $(ls /proc/$PID/fd | wc -l)"
echo "Limit: $(grep 'open files' /proc/$PID/limits | awk '{print $4}')"
echo ""

echo "--- 6. 文件类型统计 ---"
lsof -p $PID 2>/dev/null | awk 'NR>1 {print $5}' | sort | uniq -c | sort -rn
echo ""

echo "--- 7. 网络连接 ---"
ss -tp | grep "pid=$PID" | head -10
echo ""

echo "--- 8. 内核调用栈 ---"
cat /proc/$PID/stack 2>/dev/null || echo "无法读取（需要root权限）"
echo ""

echo "--- 9. 等待通道 ---"
cat /proc/$PID/wchan
echo ""

echo "===== 诊断完成 ====="
```

---

## 总结

| 问题 | 快速命令 | 深入分析 |
|------|----------|----------|
| 服务启动失败 | `systemctl status`, `journalctl -u` | 检查日志、配置、权限 |
| 进程hang | `ps aux`, `cat /proc/PID/stack` | `strace -p`, `gdb` |
| 进程消失 | `dmesg`, `journalctl -k` | core dump分析 |
| 僵尸进程 | `ps aux \| awk '$8=="Z"'` | 处理父进程 |
| 端口占用 | `ss -tlnp`, `lsof -i` | `fuser` |
| 资源泄漏 | `lsof -p`, `ls /proc/PID/fd` | 持续监控 |

**排查三板斧**：
1. **systemctl status + journalctl** - 服务问题首选
2. **ps + lsof** - 进程状态和资源
3. **strace** - 深入分析进程行为
