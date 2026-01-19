+++
title = "05.Linux系统诊断工具深度指南"
date = 2026-01-12
description = "strace、lsof、perf、bpftrace的深度剖析与实战技巧"
[taxonomies]
tags = ["linux", "debugging", "performance", "tracing"]
+++

# Linux系统诊断工具深度指南

本文深入剖析 Linux 系统诊断的四大利器：strace、lsof、perf、bpftrace，掌握从系统调用到性能分析的全链路诊断能力。

---

## 一、strace 系统调用跟踪

### 1.1 strace 工作原理

```
strace 使用 ptrace() 系统调用：
1. 附加到目标进程
2. 在每个系统调用入口/出口暂停
3. 读取系统调用参数和返回值
4. 恢复进程执行

注意：ptrace 有性能开销，生产环境慎用
```

### 1.2 基本用法

```bash
# 跟踪新进程
strace ./my_app

# 跟踪运行中的进程
strace -p <pid>

# 跟踪所有子进程
strace -f ./my_app

# 只跟踪特定类型的系统调用
strace -e trace=file ./my_app
strace -e trace=network ./my_app
strace -e trace=process ./my_app
strace -e trace=signal ./my_app
strace -e trace=ipc ./my_app
strace -e trace=memory ./my_app

# 跟踪特定系统调用
strace -e open,read,write ./my_app

# 排除特定调用
strace -e trace=!brk,mmap ./my_app
```

### 1.3 输出控制

```bash
# 显示时间戳
strace -t ./my_app      # 秒
strace -tt ./my_app     # 微秒
strace -ttt ./my_app    # UNIX 时间戳

# 显示调用耗时
strace -T ./my_app

# 显示相对时间
strace -r ./my_app

# 详细输出
strace -v ./my_app

# 输出到文件
strace -o trace.log ./my_app

# 按进程分离输出
strace -ff -o trace ./my_app
# 生成 trace.<pid> 文件
```

### 1.4 字符串和数据控制

```bash
# 增加字符串显示长度（默认 32）
strace -s 1024 ./my_app

# 显示路径解析结果
strace -y ./my_app

# 显示文件描述符对应的路径
strace -yy ./my_app

# 十六进制显示
strace -x ./my_app
strace -xx ./my_app  # 所有字符串
```

### 1.5 统计分析

```bash
# 系统调用统计
strace -c ./my_app
# % time     seconds  usecs/call     calls    errors syscall
# ------ ----------- ----------- --------- --------- ----------------
#  45.00    0.045000          45      1000           read
#  30.00    0.030000          30      1000           write
#  25.00    0.025000          25      1000           open
# ------ ----------- ----------- --------- --------- ----------------
# 100.00    0.100000                  3000           total

# 统计同时显示调用
strace -C ./my_app

# 按调用排序
strace -c -S time ./my_app
strace -c -S calls ./my_app
strace -c -S errors ./my_app
```

### 1.6 实战场景

**场景1：程序启动失败**
```bash
# 查找缺失的库或配置文件
strace -f -e trace=file ./failing_app 2>&1 | grep -E "(ENOENT|EACCES)"
# open("/lib/libmissing.so", O_RDONLY) = -1 ENOENT (No such file or directory)
```

**场景2：程序卡住**
```bash
# 查看进程在等待什么
strace -p <pid>
# 可能看到：
# read(3, <unfinished ...>    # 等待网络/文件 I/O
# futex(0x7f..., FUTEX_WAIT)  # 等待锁
# poll([{fd=3, events=POLLIN}], 1, -1) # 等待事件
```

**场景3：性能问题**
```bash
# 统计系统调用耗时
strace -c -f -p <pid>

# 找出慢调用
strace -T -e trace=network -p <pid> 2>&1 | awk '$NF > 0.1 {print}'
```

**场景4：文件访问审计**
```bash
# 查看程序访问了哪些文件
strace -f -e trace=openat,open,access -o file_access.log ./my_app
grep -E "open(at)?\(" file_access.log | sort -u
```

**场景5：网络问题**
```bash
# 跟踪网络连接
strace -f -e trace=connect,accept,sendto,recvfrom -p <pid>

# 查看 DNS 查询
strace -f -e trace=sendto,recvfrom -p <pid> 2>&1 | grep -i dns
```

### 1.7 strace 输出解读

```bash
# 典型输出
openat(AT_FDCWD, "/etc/passwd", O_RDONLY) = 3
   │       │           │           │        └─ 返回值（fd=3）
   │       │           │           └─ 标志
   │       │           └─ 路径参数
   │       └─ 目录文件描述符（当前目录）
   └─ 系统调用名

# 带时间的输出
16:32:45.123456 read(3, "data", 1024) = 100 <0.000123>
      │                                         └─ 调用耗时
      └─ 时间戳

# 错误输出
open("/not/exist", O_RDONLY) = -1 ENOENT (No such file or directory)
                                    │           └─ 错误描述
                                    └─ 错误码
```

### 1.8 常见系统调用参考

| 类别 | 系统调用 | 用途 |
|-----|---------|------|
| 文件 | open, openat, read, write, close, stat | 文件操作 |
| 网络 | socket, connect, accept, send, recv | 网络操作 |
| 进程 | fork, execve, exit, wait | 进程管理 |
| 内存 | mmap, munmap, brk, mprotect | 内存管理 |
| 信号 | kill, sigaction, signal | 信号处理 |
| 同步 | futex, semop, flock | 锁和同步 |

---

## 二、lsof 文件和网络资源

### 2.1 lsof 基础

lsof = List Open Files

Linux 中一切皆文件：
- 普通文件
- 目录
- 设备
- 网络连接（socket）
- 管道
- 共享内存

### 2.2 基本用法

```bash
# 列出所有打开的文件
lsof

# 列出特定进程的文件
lsof -p <pid>

# 列出用户打开的文件
lsof -u username

# 列出特定命令的文件
lsof -c nginx

# 列出多个条件（OR）
lsof -c nginx -c mysql

# 列出多个条件（AND）
lsof -c nginx -u www-data -a
```

### 2.3 输出字段解读

```bash
lsof -p 1234
# COMMAND    PID   USER   FD      TYPE     DEVICE  SIZE/OFF    NODE NAME
#   │        │      │      │        │         │        │        │    │
#   │        │      │      │        │         │        │        │    └─ 文件名/路径/地址
#   │        │      │      │        │         │        │        └─ inode 号
#   │        │      │      │        │         │        └─ 大小/偏移
#   │        │      │      │        │         └─ 设备号
#   │        │      │      │        └─ 文件类型
#   │        │      │      └─ 文件描述符
#   │        │      └─ 用户
#   │        └─ 进程 ID
#   └─ 命令名
```

**FD 字段含义**：
| FD | 说明 |
|---|------|
| cwd | 当前目录 |
| rtd | 根目录 |
| txt | 程序代码 |
| mem | 内存映射文件 |
| 0u, 1u, 2u | stdin, stdout, stderr |
| 3r | fd=3, 只读 |
| 4w | fd=4, 只写 |
| 5u | fd=5, 读写 |

**TYPE 字段含义**：
| TYPE | 说明 |
|-----|------|
| REG | 普通文件 |
| DIR | 目录 |
| CHR | 字符设备 |
| BLK | 块设备 |
| FIFO | 管道 |
| unix | UNIX socket |
| IPv4/IPv6 | 网络 socket |

### 2.4 文件查询

```bash
# 查看谁打开了特定文件
lsof /var/log/syslog

# 查看谁打开了目录下的文件
lsof +D /var/log/

# 递归查看目录
lsof +D /var/log/ -r

# 查看删除但未释放的文件
lsof +L1
lsof | grep deleted

# 恢复已删除但未关闭的文件
# 1. 找到进程和 fd
lsof | grep deleted
# nginx 1234 root 5u REG 8,1 1000000 123456 /var/log/nginx.log (deleted)

# 2. 从 /proc 恢复
cp /proc/1234/fd/5 /var/log/nginx.log.recovered
```

### 2.5 网络查询

```bash
# 所有网络连接
lsof -i

# 指定协议
lsof -i tcp
lsof -i udp

# 指定端口
lsof -i :80
lsof -i :80,:443

# 指定端口范围
lsof -i :1-1024

# 指定地址
lsof -i @192.168.1.1
lsof -i @192.168.1.1:22

# 指定状态
lsof -i -s TCP:LISTEN
lsof -i -s TCP:ESTABLISHED

# IPv4/IPv6
lsof -i 4
lsof -i 6

# 不解析主机名和端口
lsof -i -n -P
```

### 2.6 高级用法

**找出占用端口的进程**：
```bash
lsof -i :8080
# 或
fuser 8080/tcp
```

**监控文件系统卸载失败**：
```bash
# 查看谁在使用挂载点
lsof +D /mnt/data
fuser -vm /mnt/data
```

**查看共享库使用**：
```bash
lsof | grep libssl
```

**查看 socket 连接详情**：
```bash
lsof -i -n -P | grep ESTABLISHED | awk '{print $9}' | sort | uniq -c | sort -rn
```

**找出打开文件最多的进程**：
```bash
lsof | awk '{print $1}' | sort | uniq -c | sort -rn | head
```

### 2.7 实战场景

**场景1：磁盘空间不释放**
```bash
# 文件已删除但空间未释放
df -h  # 显示满
du -sh /  # 计算的比 df 小

# 找到已删除但未关闭的文件
lsof +L1 | grep deleted | sort -k7 -n -r | head
# 重启相关进程释放空间
```

**场景2：端口被占用**
```bash
# 查看端口占用
lsof -i :8080
# nginx   1234  root    6u  IPv4  12345      0t0  TCP *:8080 (LISTEN)

# 杀死进程
kill $(lsof -t -i :8080)
```

**场景3：文件被谁修改**
```bash
# 查看正在写入文件的进程
lsof /var/log/app.log
# 或实时监控
inotifywait -m /var/log/app.log
```

---

## 三、perf 性能分析

### 3.1 perf 简介

perf 是 Linux 官方的性能分析工具，利用硬件性能计数器（PMU）进行精确测量。

```
能力：
- CPU 性能事件采样
- 调用栈分析
- 缓存命中/缺失分析
- 分支预测分析
- 调度延迟分析
- 锁竞争分析
```

### 3.2 perf stat - 统计计数

```bash
# 基本统计
perf stat ./my_app
# Performance counter stats for './my_app':
#          1,234.56 msec task-clock                #    0.999 CPUs utilized
#                12      context-switches          #    0.010 K/sec
#                 3      cpu-migrations            #    0.002 K/sec
#             1,234      page-faults               #    0.999 K/sec
#     1,234,567,890      cycles                    #    1.000 GHz
#       987,654,321      instructions              #    0.80  insn per cycle
#       123,456,789      branches                  #  100.000 M/sec
#         1,234,567      branch-misses             #    1.00% of all branches

# 指定事件
perf stat -e cycles,instructions,cache-references,cache-misses ./my_app

# 详细事件
perf stat -e L1-dcache-loads,L1-dcache-load-misses ./my_app

# 多进程
perf stat -a sleep 10  # 系统级
perf stat -p <pid> sleep 10  # 指定进程

# 重复测量
perf stat -r 5 ./my_app
```

**常用事件**：

| 事件 | 说明 |
|-----|------|
| cycles | CPU 周期 |
| instructions | 指令数 |
| cache-references | 缓存访问 |
| cache-misses | 缓存缺失 |
| branches | 分支指令 |
| branch-misses | 分支预测失败 |
| L1-dcache-loads | L1 数据缓存读取 |
| L1-dcache-load-misses | L1 数据缓存读取缺失 |
| LLC-loads | 末级缓存读取 |
| LLC-load-misses | 末级缓存读取缺失 |

### 3.3 perf record/report - 采样分析

```bash
# 记录性能数据
perf record ./my_app

# 带调用栈
perf record -g ./my_app
perf record --call-graph dwarf ./my_app  # 更准确

# 指定频率
perf record -F 99 ./my_app  # 每秒 99 次采样

# 分析现有进程
perf record -p <pid> -g sleep 30

# 系统级采样
perf record -a -g sleep 10

# 分析结果
perf report
perf report --stdio  # 文本输出
perf report -n  # 显示样本数

# 火焰图生成
perf script > out.perf
./stackcollapse-perf.pl out.perf > out.folded
./flamegraph.pl out.folded > flamegraph.svg
```

### 3.4 perf top - 实时分析

```bash
# 实时 CPU 热点
perf top

# 指定进程
perf top -p <pid>

# 显示调用栈
perf top -g

# 指定事件
perf top -e cache-misses
```

### 3.5 perf trace - 系统调用跟踪

```bash
# 类似 strace 但开销更低
perf trace ./my_app

# 只跟踪特定调用
perf trace -e open,read,write ./my_app

# 统计模式
perf trace -s ./my_app
```

### 3.6 perf sched - 调度分析

```bash
# 记录调度事件
perf sched record sleep 10

# 查看调度延迟
perf sched latency
#  Task                  |   Runtime ms  | Switches | Average delay ms | Maximum delay ms |
#  ----------------------|---------------|----------|------------------|------------------|
#  my_app:1234           |      100.123  |      50  |            0.050 |            1.234 |

# 调度地图
perf sched map

# 回放
perf sched replay
```

### 3.7 perf lock - 锁分析

```bash
# 记录锁事件
perf lock record ./my_app

# 分析结果
perf lock report
```

### 3.8 perf mem - 内存访问分析

```bash
# 记录内存访问
perf mem record ./my_app

# 分析结果
perf mem report
```

### 3.9 实战场景

**场景1：CPU 热点分析**
```bash
# 采样 30 秒
perf record -F 99 -g -p <pid> sleep 30

# 查看热点函数
perf report --stdio | head -30
```

**场景2：缓存分析**
```bash
perf stat -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses ./my_app

# 如果 cache-misses/cache-references > 10%，需要优化数据局部性
```

**场景3：分支预测**
```bash
perf stat -e branches,branch-misses ./my_app

# 如果 branch-misses > 5%，考虑优化分支预测
# - 使用 likely/unlikely
# - 减少条件分支
```

**场景4：调度延迟**
```bash
perf sched record -a sleep 10
perf sched latency

# 找出高延迟任务
```

### 3.10 生成火焰图

```bash
# 安装火焰图工具
git clone https://github.com/brendangregg/FlameGraph

# 采样
perf record -F 99 -g -p <pid> sleep 30

# 生成火焰图
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flame.svg

# 查看
firefox flame.svg
```

---

## 四、bpftrace 高级跟踪

### 4.1 bpftrace 简介

bpftrace 是基于 eBPF 的高级跟踪语言，类似 AWK/DTrace。

```
优势：
- 低开销（比 strace 低很多）
- 安全（eBPF 验证器保证）
- 强大（可跟踪几乎所有内核事件）
- 灵活（支持聚合、直方图等）
```

### 4.2 安装

```bash
# Ubuntu/Debian
apt install bpftrace

# CentOS/RHEL
yum install bpftrace

# 验证
bpftrace --version
```

### 4.3 探针类型

| 探针类型 | 语法 | 说明 |
|---------|------|------|
| kprobe | kprobe:函数名 | 内核函数入口 |
| kretprobe | kretprobe:函数名 | 内核函数返回 |
| uprobe | uprobe:路径:函数名 | 用户态函数入口 |
| uretprobe | uretprobe:路径:函数名 | 用户态函数返回 |
| tracepoint | tracepoint:类别:事件 | 静态跟踪点 |
| usdt | usdt:路径:探针名 | 用户态静态探针 |
| profile | profile:hz:频率 | 定时采样 |
| interval | interval:s:秒数 | 定时触发 |
| software | software:事件:计数 | 软件事件 |
| hardware | hardware:事件:计数 | 硬件事件 |

### 4.4 基本语法

```
探针 /过滤条件/ {
    动作
}
```

### 4.5 内置变量

| 变量 | 说明 |
|-----|------|
| pid | 进程 ID |
| tid | 线程 ID |
| uid | 用户 ID |
| comm | 进程名 |
| nsecs | 纳秒时间戳 |
| kstack | 内核栈 |
| ustack | 用户栈 |
| arg0-argN | 函数参数 |
| retval | 返回值 |
| func | 函数名 |
| probe | 探针名 |
| curtask | 当前任务结构体 |

### 4.6 内置函数

```
输出：
- printf("format", args)  格式化输出
- print(value)            打印值
- str(ptr)                指针转字符串
- ksym(addr)              内核地址转符号
- usym(addr)              用户地址转符号
- kstack()                内核栈
- ustack()                用户栈

聚合：
- count()                 计数
- sum(value)              求和
- avg(value)              平均值
- min(value)              最小值
- max(value)              最大值
- hist(value)             直方图
- lhist(value, min, max, step)  线性直方图

时间：
- nsecs                   纳秒
- elapsed                 从启动经过的时间
```

### 4.7 单行命令示例

```bash
# 跟踪系统调用
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'

# 统计进程系统调用
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'

# 跟踪进程启动
bpftrace -e 'tracepoint:sched:sched_process_exec { printf("%s executed %s\n", comm, str(args->filename)); }'

# 读取延迟直方图
bpftrace -e 'kprobe:vfs_read { @start[tid] = nsecs; } kretprobe:vfs_read /@start[tid]/ { @ns = hist(nsecs - @start[tid]); delete(@start[tid]); }'

# 磁盘 I/O 延迟
bpftrace -e 'kprobe:blk_account_io_start { @start[arg0] = nsecs; } kprobe:blk_account_io_done /@start[arg0]/ { @usecs = hist((nsecs - @start[arg0]) / 1000); delete(@start[arg0]); }'

# TCP 连接跟踪
bpftrace -e 'kprobe:tcp_connect { @[comm] = count(); }'

# 每秒系统调用数
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @count = count(); } interval:s:1 { print(@count); clear(@count); }'
```

### 4.8 完整脚本示例

**syscall_count.bt - 系统调用统计**：
```c
#!/usr/bin/env bpftrace

BEGIN
{
    printf("Tracing syscalls... Hit Ctrl-C to end.\n");
}

tracepoint:raw_syscalls:sys_enter
{
    @syscall[comm, args->id] = count();
}

END
{
    printf("\n");
}
```

**fileopen.bt - 文件打开跟踪**：
```c
#!/usr/bin/env bpftrace

tracepoint:syscalls:sys_enter_openat
{
    printf("%-8d %-16s %s\n", pid, comm, str(args->filename));
}
```

**tcplife.bt - TCP 连接生命周期**：
```c
#!/usr/bin/env bpftrace

#include <net/sock.h>

kprobe:tcp_set_state
{
    $sk = (struct sock *)arg0;
    $newstate = arg1;
    
    if ($newstate == 1) {  // TCP_ESTABLISHED
        @birth[$sk] = nsecs;
    }
    
    if ($newstate == 7) {  // TCP_CLOSE
        $delta = nsecs - @birth[$sk];
        printf("%-16s lived for %d ms\n", comm, $delta / 1000000);
        delete(@birth[$sk]);
    }
}
```

**oomkill.bt - OOM 跟踪**：
```c
#!/usr/bin/env bpftrace

kprobe:oom_kill_process
{
    printf("OOM kill triggered: ");
    printf("pid=%d, comm=%s\n", pid, comm);
    printf("Stack:\n%s\n", kstack);
}
```

### 4.9 实战场景

**场景1：慢查询分析**
```bash
# MySQL 查询延迟
bpftrace -e '
uprobe:/usr/sbin/mysqld:dispatch_command {
    @start[tid] = nsecs;
}
uretprobe:/usr/sbin/mysqld:dispatch_command /@start[tid]/ {
    @ms = hist((nsecs - @start[tid]) / 1000000);
    delete(@start[tid]);
}'
```

**场景2：网络延迟**
```bash
# TCP 重传
bpftrace -e 'kprobe:tcp_retransmit_skb { @[comm, pid] = count(); }'

# DNS 延迟
bpftrace -e '
tracepoint:syscalls:sys_enter_sendto /comm == "dig"/ {
    @start[tid] = nsecs;
}
tracepoint:syscalls:sys_exit_recvfrom /comm == "dig" && @start[tid]/ {
    @dns_latency_us = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}'
```

**场景3：内存分析**
```bash
# 内存分配跟踪
bpftrace -e 'tracepoint:kmem:kmalloc { @bytes[comm] = sum(args->bytes_alloc); }'

# 页面错误
bpftrace -e 'software:page-faults:1 { @[comm] = count(); }'
```

**场景4：CPU 调度**
```bash
# 调度延迟
bpftrace -e '
tracepoint:sched:sched_wakeup {
    @qtime[args->pid] = nsecs;
}
tracepoint:sched:sched_switch {
    if (@qtime[args->next_pid]) {
        @usecs = hist((nsecs - @qtime[args->next_pid]) / 1000);
        delete(@qtime[args->next_pid]);
    }
}'
```

### 4.10 bpftrace vs 其他工具

| 工具 | 开销 | 灵活性 | 适用场景 |
|-----|------|--------|---------|
| strace | 高 | 低 | 调试，少量进程 |
| perf | 中 | 中 | 性能采样 |
| bpftrace | 低 | 高 | 生产环境跟踪 |
| SystemTap | 中 | 高 | 复杂脚本 |

---

## 五、综合诊断流程

### 5.1 性能问题诊断流程

```
1. 确认症状
   - top/htop：CPU、内存概览
   - vmstat 1：系统级统计
   
2. 快速定位
   - perf top：CPU 热点
   - iostat -x 1：I/O 问题
   - ss -tuln：网络问题

3. 深入分析
   - perf record/report：详细 CPU 分析
   - strace -c：系统调用统计
   - lsof：资源使用

4. 精确跟踪
   - bpftrace：低开销精确跟踪
   - perf trace：系统调用跟踪
```

### 5.2 常用命令速查

```bash
# CPU
perf top                           # 实时热点
perf record -g -p <pid> sleep 30   # 采样
perf report                        # 分析

# 系统调用
strace -c ./app                    # 统计
strace -tt -T -f -p <pid>         # 详细

# 文件/网络
lsof -p <pid>                      # 进程资源
lsof -i :port                      # 端口占用
lsof +L1                           # 已删除文件

# 高级跟踪
bpftrace -e 'tracepoint:...'      # eBPF 跟踪
```

### 5.3 工具选择指南

| 问题类型 | 首选工具 | 备选工具 |
|---------|---------|---------|
| CPU 热点 | perf top/record | bpftrace profile |
| 系统调用 | strace -c | perf trace |
| 文件访问 | lsof | bpftrace |
| 网络问题 | ss, lsof -i | bpftrace, tcpdump |
| 内存问题 | perf mem | bpftrace |
| 调度延迟 | perf sched | bpftrace |
| 锁竞争 | perf lock | bpftrace |

---

## 参考资料

- [strace man page](https://man7.org/linux/man-pages/man1/strace.1.html)
- [lsof manual](https://linux.die.net/man/8/lsof)
- [perf wiki](https://perf.wiki.kernel.org/)
- [bpftrace Reference Guide](https://github.com/iovisor/bpftrace/blob/master/docs/reference_guide.md)
- [Brendan Gregg's Blog](http://www.brendangregg.com/blog/index.html)
- [Linux Performance Tools](http://www.brendangregg.com/linuxperf.html)
