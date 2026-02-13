+++
title = "进程与服务问题排查实战"
date = 2026-01-21
weight = 31000
description = "SRE进程与服务问题排查完整指南：服务启动失败、僵尸进程、D状态进程、进程信号处理的定位与解决"
[taxonomies]
tags = ["SRE", "进程", "服务", "排查", "僵尸进程", "D状态", "信号处理", "systemd"]
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

# 六、僵尸进程深度排查

## 6.1 僵尸进程原理

```bash
# 僵尸进程（Zombie Process）：
# - 进程已终止，但父进程未调用wait()收尸
# - 保留在进程表中，占用PID但不占用其他资源
# - 状态显示为 Z（Zombie）

# 进程生命周期：
# 1. fork() 创建子进程
# 2. 子进程执行任务
# 3. 子进程exit()退出，变成僵尸
# 4. 父进程wait()收尸，僵尸消失
# 5. 如果父进程不调用wait()，僵尸持续存在

# 检查僵尸进程
ps aux | awk '$8=="Z" {print}'

# 或者
ps aux | grep defunct

# 统计僵尸进程数
ps aux | awk '$8=="Z"' | wc -l

# 查看进程状态含义
# R - Running/Runnable
# S - Interruptible Sleep
# D - Uninterruptible Sleep（重要！）
# Z - Zombie
# T - Stopped
# t - Tracing stop
```

## 6.2 僵尸进程排查流程

### 步骤一：找出僵尸进程

```bash
# 列出所有僵尸进程
ps -eo pid,ppid,stat,cmd | awk '$3~/Z/ {print}'

# 输出：
# PID   PPID  STAT CMD
# 12345 23456 Z    [myapp] <defunct>

# 重点关注PPID（父进程ID）
```

### 步骤二：分析父进程

```bash
# 找出僵尸进程的父进程
ZOMBIE_PID=12345
PARENT_PID=$(ps -o ppid= -p $ZOMBIE_PID)
echo "父进程: $PARENT_PID"

# 查看父进程信息
ps -p $PARENT_PID -o pid,ppid,stat,cmd

# 查看父进程是否正常
cat /proc/$PARENT_PID/status | grep -E "Name|State|Pid"
```

### 步骤三：解决方案

```bash
# 方案1：让父进程收尸（推荐）
# 向父进程发送SIGCHLD信号，提醒它收尸
kill -SIGCHLD $PARENT_PID

# 方案2：杀死父进程（僵尸会被init接管并清理）
kill $PARENT_PID
# 如果父进程不响应
kill -9 $PARENT_PID

# 方案3：修复应用代码
# 父进程应该：
# - 调用wait()/waitpid()
# - 或设置SIGCHLD处理器
# - 或使用signal(SIGCHLD, SIG_IGN)忽略

# 注意：无法直接杀死僵尸进程
# kill -9 <zombie_pid> 无效
# 因为僵尸进程已经死了，只是没被收尸
```

## 6.3 僵尸进程代码示例

```bash
# 问题代码示例（C语言）
# 父进程不等待子进程
cat << 'EOF'
#include <unistd.h>
int main() {
    if (fork() == 0) {
        // 子进程立即退出
        _exit(0);
    }
    // 父进程不调用wait()，继续运行
    while(1) sleep(1);
}
EOF

# 正确代码示例
cat << 'EOF'
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>

// 方法1：在循环中wait
int main() {
    if (fork() == 0) {
        _exit(0);
    }
    wait(NULL);  // 等待子进程
    return 0;
}

// 方法2：SIGCHLD处理器
void sigchld_handler(int sig) {
    while (waitpid(-1, NULL, WNOHANG) > 0);
}
int main() {
    signal(SIGCHLD, sigchld_handler);
    // ...
}

// 方法3：忽略SIGCHLD（子进程不会变僵尸）
int main() {
    signal(SIGCHLD, SIG_IGN);
    // ...
}
EOF
```

## 6.4 批量清理僵尸进程

```bash
#!/bin/bash
# cleanup_zombies.sh - 清理僵尸进程

echo "===== 僵尸进程清理 ====="

# 统计僵尸进程
ZOMBIE_COUNT=$(ps aux | awk '$8=="Z"' | wc -l)
echo "发现僵尸进程: $ZOMBIE_COUNT 个"

if [ $ZOMBIE_COUNT -eq 0 ]; then
    echo "无需清理"
    exit 0
fi

# 按父进程分组
echo ""
echo "按父进程分组："
ps -eo ppid,stat | awk '$2~/Z/ {print $1}' | sort | uniq -c | sort -rn

echo ""
echo "尝试向父进程发送SIGCHLD..."

# 向所有有僵尸子进程的父进程发送SIGCHLD
for ppid in $(ps -eo ppid,stat | awk '$2~/Z/ {print $1}' | sort -u); do
    if [ -d "/proc/$ppid" ]; then
        echo "向父进程 $ppid 发送 SIGCHLD"
        kill -SIGCHLD $ppid 2>/dev/null
    fi
done

sleep 2

# 再次检查
NEW_COUNT=$(ps aux | awk '$8=="Z"' | wc -l)
echo ""
echo "清理后僵尸进程: $NEW_COUNT 个"

if [ $NEW_COUNT -gt 0 ]; then
    echo ""
    echo "剩余僵尸进程需要手动处理（杀死父进程或修复应用）"
    ps aux | awk '$8=="Z" {print}'
fi
```

---

# 七、D状态进程深度排查

## 7.1 D状态原理

```bash
# D状态（Uninterruptible Sleep）：
# - 进程在等待不可中断的IO操作
# - 不响应任何信号，包括SIGKILL
# - 通常是在等待磁盘IO

# D状态进程的影响：
# 1. 会增加Load Average
# 2. 可能导致系统hang
# 3. 无法杀死（kill -9 无效）

# 检查D状态进程
ps aux | awk '$8~/D/ {print}'

# 或使用ps的状态过滤
ps -eo pid,stat,wchan,cmd | grep "^[0-9]* D"

# 统计D状态进程数
ps aux | awk '$8~/D/' | wc -l
```

## 7.2 D状态进程排查

### 步骤一：识别D状态进程

```bash
# 列出D状态进程
ps aux | awk 'NR==1 || $8~/D/'

# 显示进程等待的内核函数
ps -eo pid,stat,wchan:32,cmd | awk '$2~/D/'

# wchan列显示进程在等待什么
# 常见wchan：
# wait_on_page_bit - 等待页面IO
# blkdev_issue_flush - 等待块设备刷新
# nfs4_wait_bit_killable - NFS等待
# io_schedule - 通用IO调度
```

### 步骤二：分析等待原因

```bash
# 查看进程内核栈
cat /proc/<PID>/stack

# 输出示例：
# [<ffffffff812345>] wait_on_page_bit+0x12/0x34
# [<ffffffff812346>] __lock_page+0x12/0x34
# [<ffffffff812347>] generic_file_read_iter+0x12/0x34
# ...

# 解读：
# 从底部到顶部是调用栈
# 顶部的函数是当前等待点

# 查看进程打开的文件
lsof -p <PID>
# 找到可能导致阻塞的文件

# 查看进程的系统调用
strace -p <PID>
# D状态进程通常不会有输出（被阻塞在内核中）
```

### 步骤三：分析IO问题

```bash
# 检查磁盘IO状态
iostat -xz 1 5
# 关注 %util 和 await
# util接近100%说明磁盘繁忙
# await高说明IO延迟大

# 查看块设备队列
cat /sys/block/sda/queue/nr_requests
cat /sys/block/sda/stat

# 检查是否是NFS问题
mount | grep nfs
df -h | grep nfs
# 如果是NFS挂载点，检查NFS服务器

# 检查存储设备健康
dmesg | grep -i -E "error|fail|timeout|reset" | tail -20
smartctl -a /dev/sda
```

## 7.3 常见D状态场景

### 场景一：磁盘故障

```bash
# 症状：大量D状态进程，IO完全卡住

# 排查：
# 1. 检查dmesg
dmesg | tail -50
# 看是否有IO错误、磁盘错误

# 2. 检查磁盘健康
smartctl -H /dev/sda
smartctl -a /dev/sda | grep -E "Reallocated|Pending|Uncorrectable"

# 3. 检查磁盘控制器
lspci | grep -i storage
dmesg | grep -i raid

# 解决：
# - 如果磁盘故障，需要更换磁盘
# - 如果是RAID，可能需要重建
```

### 场景二：NFS挂载问题

```bash
# 症状：访问NFS挂载点的进程进入D状态

# 排查：
# 1. 检查NFS挂载
mount | grep nfs
df -h  # 可能也会hang

# 2. 检查NFS服务器连通性
ping <nfs_server>
rpcinfo -p <nfs_server>

# 3. 检查NFS统计
nfsstat -c  # 客户端统计

# 解决：
# 方案1：修复NFS服务器
# 方案2：卸载问题挂载点（可能需要强制）
umount -f /mnt/nfs_mount
umount -l /mnt/nfs_mount  # lazy unmount

# 预防：使用soft挂载选项
# mount -o soft,timeo=30 server:/share /mnt
```

### 场景三：内核Bug或驱动问题

```bash
# 症状：特定操作导致D状态

# 排查：
# 1. 检查内核版本
uname -r

# 2. 搜索已知bug
# 搜索内核bug数据库

# 3. 检查驱动
lsmod
dmesg | grep -i driver

# 解决：
# - 升级内核
# - 更新驱动
# - 应用补丁
```

## 7.4 D状态进程处理

```bash
# 重要：D状态进程无法被杀死！
# kill -9 对D状态进程无效

# 唯一解决方法：
# 1. 修复导致阻塞的底层问题（磁盘、NFS等）
# 2. 等待IO操作完成（可能需要很长时间）
# 3. 重启系统（最后手段）

# 监控D状态进程
while true; do
    COUNT=$(ps aux | awk '$8~/D/' | wc -l)
    echo "$(date '+%H:%M:%S') D状态进程: $COUNT"
    [ $COUNT -gt 0 ] && ps aux | awk '$8~/D/ {print $2, $11}' | head -5
    sleep 10
done
```

---

# 八、进程信号处理问题

## 8.1 信号基础

```bash
# 常用信号
# SIGTERM (15) - 终止请求（可被捕获）
# SIGKILL (9)  - 强制终止（不可被捕获）
# SIGHUP (1)   - 挂起/重新加载配置
# SIGINT (2)   - 中断（Ctrl+C）
# SIGQUIT (3)  - 退出（生成core）
# SIGUSR1 (10) - 用户定义1
# SIGUSR2 (12) - 用户定义2
# SIGCHLD (17) - 子进程状态变化
# SIGSTOP (19) - 停止（不可被捕获）
# SIGCONT (18) - 继续

# 查看所有信号
kill -l

# 发送信号
kill -SIGTERM <PID>
kill -15 <PID>
kill -TERM <PID>
```

## 8.2 进程无法被杀死

### 场景一：进程忽略SIGTERM

```bash
# kill <PID> 无效，但 kill -9 有效

# 原因：进程忽略了SIGTERM

# 解决：
kill -9 <PID>

# 或者尝试其他信号
kill -SIGQUIT <PID>  # 产生core dump
kill -SIGABRT <PID>  # 中止
```

### 场景二：进程处于D状态

```bash
# kill -9 <PID> 也无效

# 原因：D状态进程不响应任何信号
# 参见上方"D状态进程"章节

# 解决：修复底层IO问题或重启
```

### 场景三：进程是僵尸

```bash
# kill <PID> 提示成功但进程还在

# 原因：僵尸进程已经死了
# 参见上方"僵尸进程"章节

# 解决：处理父进程
```

### 场景四：进程在等待锁

```bash
# 进程卡在某个操作上

# 查看进程在等什么
cat /proc/<PID>/wchan
cat /proc/<PID>/stack

# 使用gdb附加
gdb -p <PID>
(gdb) bt  # 查看调用栈
(gdb) info threads  # 查看所有线程

# 可能需要kill其他持有锁的进程
```

## 8.3 优雅停止进程

```bash
# 最佳实践：先SIGTERM，再SIGKILL

# 优雅停止脚本
graceful_stop() {
    PID=$1
    TIMEOUT=${2:-30}
    
    # 发送SIGTERM
    echo "发送SIGTERM到进程 $PID"
    kill -TERM $PID 2>/dev/null
    
    # 等待进程退出
    for i in $(seq 1 $TIMEOUT); do
        if ! kill -0 $PID 2>/dev/null; then
            echo "进程 $PID 已优雅退出"
            return 0
        fi
        sleep 1
    done
    
    # 超时，强制杀死
    echo "进程 $PID 未响应，发送SIGKILL"
    kill -9 $PID 2>/dev/null
    sleep 1
    
    if kill -0 $PID 2>/dev/null; then
        echo "警告：进程 $PID 无法被杀死（可能是D状态）"
        return 1
    else
        echo "进程 $PID 已强制终止"
        return 0
    fi
}

# 使用
graceful_stop 12345 30
```

---

# 九、进程资源限制问题

## 9.1 常见资源限制

```bash
# 查看进程资源限制
cat /proc/<PID>/limits

# 或使用ulimit（当前shell）
ulimit -a

# 常见限制：
# Max open files        - 最大文件描述符数
# Max processes         - 最大进程数
# Max locked memory     - 最大锁定内存
# Max stack size        - 最大栈大小
```

## 9.2 文件描述符耗尽

```bash
# 症状：程序报错"Too many open files"

# 检查进程打开的文件数
ls /proc/<PID>/fd | wc -l

# 检查限制
cat /proc/<PID>/limits | grep "open files"

# 解决方案：

# 1. 临时提高限制
prlimit --pid <PID> --nofile=65535:65535

# 2. 修改systemd服务
# /etc/systemd/system/myapp.service
[Service]
LimitNOFILE=65535

# 3. 修改全局限制
# /etc/security/limits.conf
*         soft    nofile    65535
*         hard    nofile    65535

# 4. 检查是否有文件描述符泄漏
lsof -p <PID> | head -50
# 看是否有大量重复的连接或文件
```

## 9.3 内存限制问题

```bash
# 症状：进程被OOM杀死或无法分配内存

# 检查cgroup内存限制
cat /sys/fs/cgroup/memory/system.slice/myapp.service/memory.limit_in_bytes

# 检查进程内存使用
cat /proc/<PID>/status | grep -E "VmSize|VmRSS|VmSwap"

# 解决方案：

# 1. 调整cgroup限制
echo 2147483648 > /sys/fs/cgroup/memory/.../memory.limit_in_bytes

# 2. systemd服务配置
[Service]
MemoryMax=2G
MemoryHigh=1.5G

# 3. 检查OOM Score
cat /proc/<PID>/oom_score
cat /proc/<PID>/oom_score_adj
```

---

## 总结

| 问题 | 快速命令 | 深入分析 |
|------|----------|----------|
| 服务启动失败 | `systemctl status`, `journalctl -u` | 检查日志、配置、权限 |
| 进程hang | `ps aux`, `cat /proc/PID/stack` | `strace -p`, `gdb` |
| 进程消失 | `dmesg`, `journalctl -k` | core dump分析 |
| 僵尸进程 | `ps aux \| awk '$8=="Z"'` | `kill -SIGCHLD`父进程 |
| D状态进程 | `ps aux \| awk '$8~/D/'` | 检查IO/NFS/磁盘 |
| 无法杀死进程 | `cat /proc/PID/stack` | 判断D状态/僵尸/锁 |
| 端口占用 | `ss -tlnp`, `lsof -i` | `fuser` |
| 资源泄漏 | `lsof -p`, `ls /proc/PID/fd` | 持续监控 |
| 文件描述符耗尽 | `ls /proc/PID/fd \| wc -l` | `prlimit`, `lsof` |

**僵尸进程处理要点**：
1. 僵尸进程已经死了，无法直接杀死
2. 向父进程发送SIGCHLD或杀死父进程
3. 根本解决：修复应用代码

**D状态进程处理要点**：
1. D状态进程无法被杀死（包括kill -9）
2. 需要解决底层IO问题
3. 常见原因：磁盘故障、NFS问题、内核bug

**信号处理要点**：
1. 先SIGTERM，等待超时再SIGKILL
2. 检查进程为何不响应信号
3. D状态和僵尸进程需要特殊处理

**排查三板斧**：
1. **systemctl status + journalctl** - 服务问题首选
2. **ps + lsof** - 进程状态和资源
3. **strace** - 深入分析进程行为

---

## 相关文章

- [上一篇：磁盘与存储问题排查实战](@/articles/sre/sre-30-磁盘与存储问题排查实战.md)
- [下一篇：日志分析与故障定位实战](@/articles/sre/sre-32-日志分析与故障定位实战.md)
