+++
title = "CPU问题排查实战"
date = 2026-01-21
weight = 28000
description = "SRE CPU问题排查完整指南：CPU使用率高、软中断/硬中断、上下文切换、NUMA问题、Steal时间的定位与解决"
[taxonomies]
tags = ["SRE", "CPU", "排查", "实战", "软中断", "NUMA", "上下文切换", "Linux"]
+++

## 概述

CPU问题是最常见的性能瓶颈之一。本文详细介绍CPU相关问题的排查思路、常用工具和解决方案。

---

# 一、CPU基础概念

## 1.1 核心指标

| 指标 | 含义 | 正常范围 |
|------|------|----------|
| %user | 用户态CPU时间 | 取决于应用 |
| %system | 内核态CPU时间 | <30% |
| %iowait | 等待IO的时间 | <20% |
| %idle | 空闲时间 | >0即可 |
| %steal | 被虚拟化偷走的时间 | <5% |
| Load Average | 运行队列长度 | <CPU核数 |

## 1.2 Load与CPU使用率的区别

```
Load Average：等待运行的进程数（包括等待IO的）
CPU使用率：CPU实际工作的时间占比

场景1：高Load + 低CPU → IO等待问题
场景2：高Load + 高CPU → 真正的CPU瓶颈
场景3：低Load + 高CPU → 某个进程独占CPU
```

---

# 二、CPU使用率过高

## 2.1 快速定位高CPU进程

### 第一步：确认CPU整体状态

```bash
# 查看整体CPU使用率
top -bn1 | head -10

# 按CPU排序查看进程
top -bn1 -o %CPU | head -20

# 更好的工具：htop
htop

# mpstat查看每个CPU核心
mpstat -P ALL 1 5
```

### 第二步：定位高CPU进程

```bash
# 找出CPU最高的进程
ps aux --sort=-%cpu | head -10

# 持续监控
watch -n 1 'ps aux --sort=-%cpu | head -10'

# pidstat查看进程CPU使用详情
pidstat -u 1 5

# 查看特定进程
pidstat -u -p <PID> 1
```

---

## 2.2 分析进程CPU消耗

### 场景：Java进程CPU高

**定位高CPU线程**

```bash
# 方法1：top查看线程
top -H -p <PID>

# 方法2：ps查看线程
ps -mp <PID> -o THREAD,tid,time | sort -rn -k2 | head -20

# 记录高CPU的线程ID（TID）
```

**获取线程堆栈**

```bash
# 将TID转换为16进制（Java jstack需要）
printf "%x\n" <TID>
# 例如：TID 12345 → 0x3039

# 获取Java线程堆栈
jstack <PID> > thread_dump.txt

# 搜索对应线程
grep -A 30 "nid=0x3039" thread_dump.txt
```

**常见问题模式**

```
1. 死循环
   - 堆栈显示一直在某个方法
   - 解决：检查循环条件

2. 正则表达式回溯
   - 堆栈在Pattern.matcher
   - 解决：优化正则或设置超时

3. 序列化/反序列化
   - 堆栈在JSON/XML解析
   - 解决：优化数据结构或换库

4. GC问题
   - 看到很多GC线程
   - 解决：调优JVM参数
```

### 场景：Go进程CPU高

```bash
# 启用pprof
# 代码中添加：import _ "net/http/pprof"

# 获取CPU profile
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# 在pprof交互界面
(pprof) top 10
(pprof) list <function_name>
(pprof) web  # 生成火焰图

# 直接生成火焰图
go tool pprof -http=:8080 http://localhost:6060/debug/pprof/profile?seconds=30
```

### 场景：Python进程CPU高

```bash
# 使用py-spy（不需要修改代码）
pip install py-spy

# 实时top
py-spy top --pid <PID>

# 生成火焰图
py-spy record -o profile.svg --pid <PID> --duration 30

# 查看当前堆栈
py-spy dump --pid <PID>
```

### 场景：通用进程CPU高

```bash
# 使用perf分析
sudo perf top -p <PID>

# 记录采样数据
sudo perf record -g -p <PID> -- sleep 30

# 生成报告
sudo perf report

# 生成火焰图
sudo perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg
```

---

## 2.3 系统态CPU高（%system）

### 排查思路

```
%system高通常意味着：
1. 大量系统调用
2. 内核处理（中断、软中断）
3. 内核bug或配置问题
```

### 定位系统调用

```bash
# strace查看系统调用
strace -cp <PID>

# 输出示例：
# % time     seconds  usecs/call     calls    errors syscall
# ------ ----------- ----------- --------- --------- ----------------
#  45.23    0.123456          12     10234           write
#  32.12    0.087654          23      3812           read
#  12.45    0.034567          34      1023           futex

# 追踪特定系统调用
strace -e write -p <PID>

# 查看系统调用耗时
strace -T -p <PID> 2>&1 | head -100
```

### 检查软中断

```bash
# 查看软中断
cat /proc/softirqs
watch -n 1 'cat /proc/softirqs'

# 常见软中断类型：
# NET_RX/NET_TX - 网络收发
# BLOCK - 块设备
# SCHED - 调度
# RCU - 内核同步

# 如果NET_RX过高，可能是网络流量大或网卡问题
# 检查网卡中断
cat /proc/interrupts | grep eth
```

### 检查上下文切换

```bash
# vmstat查看上下文切换
vmstat 1 5
# 关注cs列（context switch）

# pidstat查看进程上下文切换
pidstat -w 1 5
# cswch/s：自愿切换（等待IO等）
# nvcswch/s：非自愿切换（时间片用完）

# 高上下文切换可能原因：
# 1. 线程数过多
# 2. 锁竞争激烈
# 3. 频繁的IO等待
```

---

## 2.4 iowait高

### 排查思路

```
%iowait高意味着CPU在等待IO
常见原因：
1. 磁盘IO密集
2. 网络IO等待
3. 存储设备慢
```

### 定位IO问题

```bash
# iostat查看磁盘IO
iostat -x 1 5

# 关注指标：
# %util - 磁盘繁忙度
# await - IO平均等待时间
# r_await/w_await - 读写等待时间

# 找出IO高的进程
iotop -o

# pidstat查看进程IO
pidstat -d 1 5
```

### 详细IO分析

```bash
# 查看进程的IO详情
cat /proc/<PID>/io

# 使用perf追踪IO
sudo perf record -e block:block_rq_issue -a -- sleep 10
sudo perf report

# 使用biosnoop（bcc工具）
sudo biosnoop
```

---

# 三、Load Average过高

## 3.1 理解Load Average

```bash
# 查看Load Average
uptime
# 输出：load average: 2.34, 1.56, 1.23
# 含义：1分钟、5分钟、15分钟的平均负载

# 查看CPU核数
nproc
# 或
cat /proc/cpuinfo | grep processor | wc -l

# 判断标准：
# Load / CPU核数 < 1：正常
# Load / CPU核数 = 1-2：较高
# Load / CPU核数 > 2：过高
```

## 3.2 Load高但CPU使用率低

### 场景分析

```
Load高 + CPU低 = 进程在等待（通常是IO）
```

### 排查步骤

```bash
# 第一步：查看状态为D（不可中断睡眠）的进程
ps aux | awk '$8 ~ /D/'

# 或使用top，按状态排序
top -bn1 | grep " D "

# 第二步：确认是什么IO
# D状态通常是等待磁盘IO

# 第三步：检查磁盘状态
iostat -x 1 5

# 第四步：检查存储是否有问题
dmesg | tail -50
dmesg | grep -i error
```

### 常见原因

```
1. NFS/CIFS挂载卡住
   - 检查：mount | grep nfs
   - 解决：检查NFS服务器状态

2. 磁盘故障
   - 检查：dmesg | grep -i disk
   - 解决：更换磁盘

3. 存储阵列问题
   - 检查：存储管理界面
   - 解决：联系存储管理员

4. 虚拟机存储延迟
   - 检查：宿主机存储状态
   - 解决：优化存储配置
```

## 3.3 Load高且CPU也高

### 排查步骤

```bash
# 第一步：确认是真正的CPU瓶颈
mpstat -P ALL 1 5

# 第二步：找出消耗CPU的进程
ps aux --sort=-%cpu | head -10

# 第三步：确认是否是进程数过多
ps aux | wc -l
# 对比正常时的进程数

# 第四步：检查是否有异常进程
ps aux | grep -v "\[" | awk '$3>10 {print}'

# 第五步：检查是否是突发流量
# 查看网络连接数
ss -s
netstat -an | wc -l
```

---

# 四、进程CPU状态分析

## 4.1 进程状态解读

```bash
# ps输出的STAT列含义
# R - Running/Runnable
# S - Sleeping（可中断睡眠）
# D - Disk sleep（不可中断睡眠，等待IO）
# Z - Zombie（僵尸进程）
# T - Stopped（停止/暂停）
# t - Tracing stop（被调试器暂停）

# 附加标记：
# < - 高优先级
# N - 低优先级
# L - 有内存锁定
# s - session leader
# l - 多线程
# + - 前台进程
```

## 4.2 僵尸进程（Zombie）

### 排查

```bash
# 查找僵尸进程
ps aux | awk '$8=="Z" {print}'

# 查看僵尸进程数量
ps aux | awk '$8=="Z"' | wc -l

# 找到僵尸进程的父进程
ps -eo pid,ppid,stat,cmd | awk '$3=="Z" {print}'
# 然后查看PPID对应的进程
ps -p <PPID> -o pid,cmd
```

### 解决

```bash
# 僵尸进程无法直接kill，需要处理父进程

# 方法1：让父进程回收
kill -SIGCHLD <PPID>

# 方法2：如果父进程有问题，重启父进程
kill <PPID>

# 方法3：如果父进程是init(1)，重启系统（最后手段）

# 预防：确保程序正确调用wait()回收子进程
```

## 4.3 D状态进程

### 排查

```bash
# 找出D状态进程
ps aux | awk '$8 ~ /D/ {print}'

# 查看D状态进程的调用栈
cat /proc/<PID>/stack

# 查看进程在等待什么
cat /proc/<PID>/wchan

# 使用perf查看调用栈
sudo perf record -g -p <PID> -- sleep 5
sudo perf report
```

### 常见原因

```
1. 磁盘IO等待
2. NFS/网络存储等待
3. 内核bug
4. 设备驱动问题
```

---

# 五、CPU性能调优

## 5.1 CPU亲和性设置

```bash
# 查看进程CPU亲和性
taskset -p <PID>

# 设置进程绑定到特定CPU
taskset -pc 0,1 <PID>

# 启动时绑定CPU
taskset -c 0-3 ./my_program

# 使用numactl
numactl --cpunodebind=0 --membind=0 ./my_program
```

## 5.2 进程优先级调整

```bash
# 查看进程优先级
ps -eo pid,ni,pri,cmd | head

# 调整nice值（-20最高优先级，19最低）
renice -n -5 -p <PID>

# 启动时设置nice
nice -n -5 ./my_program

# 实时进程优先级
chrt -f -p 50 <PID>  # FIFO调度
chrt -r -p 50 <PID>  # RR调度
```

## 5.3 CPU频率管理

```bash
# 查看当前频率
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq

# 查看调速器
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 设置性能模式
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance | sudo tee $cpu
done

# 使用cpupower
cpupower frequency-info
cpupower frequency-set -g performance
```

## 5.4 关键进程CPU隔离

```bash
# 内核启动参数隔离CPU
# /etc/default/grub
# GRUB_CMDLINE_LINUX="isolcpus=2,3 nohz_full=2,3 rcu_nocbs=2,3"

# 查看隔离的CPU
cat /sys/devices/system/cpu/isolated

# 将关键进程绑定到隔离的CPU
taskset -c 2,3 ./critical_process
```

---

# 六、实用诊断脚本

## 6.1 CPU诊断一键脚本

```bash
#!/bin/bash
# cpu_diagnose.sh - CPU问题诊断脚本

echo "===== CPU诊断报告 ====="
echo "时间: $(date)"
echo ""

echo "--- 1. 系统概览 ---"
uptime
echo ""

echo "--- 2. CPU核心数 ---"
echo "物理CPU: $(cat /proc/cpuinfo | grep "physical id" | sort -u | wc -l)"
echo "核心数: $(nproc)"
echo ""

echo "--- 3. CPU使用率 ---"
mpstat 1 3
echo ""

echo "--- 4. 每核CPU使用率 ---"
mpstat -P ALL 1 1
echo ""

echo "--- 5. Top 10 CPU进程 ---"
ps aux --sort=-%cpu | head -11
echo ""

echo "--- 6. D状态进程 ---"
ps aux | awk '$8 ~ /D/ {print}' || echo "无D状态进程"
echo ""

echo "--- 7. 僵尸进程 ---"
ps aux | awk '$8=="Z" {print}' || echo "无僵尸进程"
echo ""

echo "--- 8. 上下文切换 ---"
vmstat 1 3
echo ""

echo "--- 9. 中断情况 ---"
cat /proc/interrupts | head -20
echo ""

echo "===== 诊断完成 ====="
```

## 6.2 持续CPU监控脚本

```bash
#!/bin/bash
# cpu_monitor.sh - CPU持续监控

LOG_FILE="/var/log/cpu_monitor.log"
THRESHOLD=80

while true; do
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8}')
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "$TIMESTAMP CPU: ${CPU_USAGE}%" >> $LOG_FILE
    
    if (( $(echo "$CPU_USAGE > $THRESHOLD" | bc -l) )); then
        echo "$TIMESTAMP WARNING: CPU使用率超过${THRESHOLD}%" >> $LOG_FILE
        echo "Top 5 CPU进程:" >> $LOG_FILE
        ps aux --sort=-%cpu | head -6 >> $LOG_FILE
        echo "" >> $LOG_FILE
    fi
    
    sleep 5
done
```

---

# 七、软中断与硬中断问题

## 7.1 中断基础概念

```bash
# 硬中断(hi)：硬件触发，由CPU立即处理
# 软中断(si)：内核触发，延迟处理（如网络包处理）

# 查看中断分布
cat /proc/interrupts

# 输出示例：
#            CPU0       CPU1       CPU2       CPU3
#   0:         45          0          0          0  IR-IO-APIC   2-edge   timer
#   8:          1          0          0          0  IR-IO-APIC   8-edge   rtc0
# LOC:    1234567    2345678    3456789    4567890  Local timer interrupts
# NET_RX:   12345      23456      34567      45678  Network RX
# NET_TX:    1234       2345       3456       4567  Network TX

# 查看软中断统计
cat /proc/softirqs

# 输出示例：
#                     CPU0       CPU1       CPU2       CPU3
#           HI:          0          0          0          0
#        TIMER:    1234567    2345678    3456789    4567890
#       NET_TX:      12345      23456      34567      45678
#       NET_RX:     123456     234567     345678     456789
#        BLOCK:      12345      23456      34567      45678
#     TASKLET:       1234       2345       3456       4567
#        SCHED:     123456     234567     345678     456789
#      RCU:         12345      23456      34567      45678
```

## 7.2 软中断CPU占用高排查

### 场景：si（软中断）占用高

```bash
# 1. 确认软中断CPU占用
mpstat -P ALL 1 5
# 关注 %soft 列（或 %si）

# 2. 查看是哪种软中断
watch -d cat /proc/softirqs
# 观察哪种类型增长最快

# 常见软中断类型：
# NET_RX - 网络接收（最常见）
# NET_TX - 网络发送
# BLOCK  - 块设备
# TIMER  - 定时器
# SCHED  - 调度
# RCU    - Read-Copy-Update

# 3. 网络软中断排查（最常见场景）
# 查看网卡中断分布
cat /proc/interrupts | grep eth0

# 查看软中断处理是否均衡
cat /proc/softirqs | grep NET
```

### 网络软中断优化

```bash
# 问题：NET_RX软中断集中在单个CPU

# 原因1：网卡只有单队列
# 检查网卡队列数
ethtool -l eth0
# 如果combined为1，网卡只有单队列

# 解决：增加队列数（如果网卡支持）
ethtool -L eth0 combined 4

# 原因2：RSS（接收端缩放）未启用或配置不当
# 查看RSS配置
ethtool -x eth0

# 原因3：中断亲和性设置不当
# 查看中断亲和性
cat /proc/irq/<IRQ_NUM>/smp_affinity

# 使用irqbalance自动均衡
systemctl status irqbalance
systemctl start irqbalance

# 原因4：RPS/RFS未启用（软件层面分散负载）
# 启用RPS
echo "f" > /sys/class/net/eth0/queues/rx-0/rps_cpus
# "f" = 1111二进制 = 使用CPU 0-3

# 启用RFS
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries
echo 4096 > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt
```

### 软中断监控脚本

```bash
#!/bin/bash
# softirq_monitor.sh - 软中断监控

echo "时间 NET_RX NET_TX TIMER SCHED"
while true; do
    TIMESTAMP=$(date '+%H:%M:%S')
    NET_RX=$(awk '/NET_RX/{sum=0; for(i=2;i<=NF;i++) sum+=$i; print sum}' /proc/softirqs)
    NET_TX=$(awk '/NET_TX/{sum=0; for(i=2;i<=NF;i++) sum+=$i; print sum}' /proc/softirqs)
    TIMER=$(awk '/TIMER/{sum=0; for(i=2;i<=NF;i++) sum+=$i; print sum}' /proc/softirqs)
    SCHED=$(awk '/SCHED/{sum=0; for(i=2;i<=NF;i++) sum+=$i; print sum}' /proc/softirqs)
    echo "$TIMESTAMP $NET_RX $NET_TX $TIMER $SCHED"
    sleep 1
done
```

## 7.3 硬中断问题

```bash
# 硬中断(hi)高通常是硬件问题

# 检查硬中断分布
cat /proc/interrupts

# 常见问题：
# 1. 某个设备产生大量中断
# 2. 中断风暴（某设备故障）

# 找出中断最多的设备
cat /proc/interrupts | awk 'NR>1 {
    sum=0; for(i=2; i<=NF-3; i++) sum+=$i;
    if(sum>0) print sum, $NF
}' | sort -rn | head -10

# 如果某设备中断异常高，检查：
# 1. 硬件是否故障
# 2. 驱动是否有问题
# 3. 是否需要开启中断合并（interrupt coalescing）

# 网卡中断合并
ethtool -C eth0 rx-usecs 100 rx-frames 25
# rx-usecs: 延迟微秒数
# rx-frames: 合并的包数
```

---

# 八、上下文切换深度分析

## 8.1 上下文切换类型

```bash
# 自愿切换（voluntary）：进程主动让出CPU
#   - 等待IO
#   - 等待锁
#   - sleep

# 非自愿切换（nonvoluntary）：被调度器强制切换
#   - 时间片用完
#   - 被更高优先级进程抢占

# 查看系统上下文切换
vmstat 1 5
# cs列是每秒上下文切换次数

# 查看进程级别上下文切换
pidstat -w 1 5
# cswch/s  - 自愿切换
# nvcswch/s - 非自愿切换

# 查看特定进程
pidstat -w -p <PID> 1
```

## 8.2 上下文切换过高排查

### 判断标准

```bash
# 上下文切换次数没有绝对标准，需要结合场景

# 参考值（仅供参考）：
# - 单核几千到几万次/秒通常正常
# - 超过10万次/秒可能有问题
# - 关键是观察变化趋势

# 查看历史数据
sar -w 1 10
# proc/s   - 每秒创建的进程数
# cswch/s  - 每秒上下文切换数
```

### 场景一：非自愿切换高

```bash
# 原因：进程竞争CPU激烈

# 排查步骤：
# 1. 确认是哪些进程
pidstat -w 1 5 | sort -k5 -rn | head -20
# nvcswch/s高的进程

# 2. 检查CPU是否饱和
mpstat -P ALL 1 5
# 如果idle接近0，说明CPU不够用

# 3. 检查是否有CPU密集型进程
ps aux --sort=-%cpu | head -10

# 解决方案：
# 1. 减少并发进程/线程数
# 2. 增加CPU资源
# 3. 优化应用，减少CPU使用
```

### 场景二：自愿切换高

```bash
# 原因：进程频繁等待资源

# 常见原因：
# 1. IO等待
# 2. 锁竞争
# 3. 频繁sleep

# 排查步骤：
# 1. 检查IO等待
iostat -x 1 5
# await高说明IO慢

# 2. 使用perf分析等待原因
perf record -g -p <PID> sleep 10
perf report

# 3. 使用strace查看系统调用
strace -c -p <PID>
# 看哪些系统调用占用时间多
```

### 场景三：进程创建频繁

```bash
# 现象：vmstat中proc/s很高

# 原因：频繁fork/exec

# 排查：
# 1. 找出创建进程的父进程
ps -ef | awk '{print $3}' | sort | uniq -c | sort -rn | head -10
# 找出PPID最多的

# 2. 使用perf追踪
perf record -e sched:sched_process_fork -a sleep 10
perf script

# 解决方案：
# 1. 使用进程池/线程池
# 2. 使用长连接替代短连接
# 3. 优化脚本，减少外部命令调用
```

## 8.3 上下文切换延迟分析

```bash
# 使用perf分析调度延迟
perf sched record sleep 10
perf sched latency

# 输出示例：
# Task                  |   Runtime ms  | Switches | Avg delay ms |
# -------------------------------------------------------------------
# java:12345           |    5234.567   |   12345  |    0.123     |
# nginx:23456          |    1234.567   |    2345  |    0.456     |

# Avg delay 高说明进程等待CPU时间长

# 查看调度统计
perf sched timehist
```

---

# 九、NUMA与CPU亲和性问题

## 9.1 NUMA基础

```bash
# NUMA（Non-Uniform Memory Access）
# 多路服务器上，CPU访问本地内存快，远程内存慢

# 检查是否是NUMA架构
numactl --hardware

# 输出示例：
# available: 2 nodes (0-1)
# node 0 cpus: 0 1 2 3 4 5 6 7
# node 0 size: 65536 MB
# node 0 free: 32768 MB
# node 1 cpus: 8 9 10 11 12 13 14 15
# node 1 size: 65536 MB
# node 1 free: 32768 MB
# node distances:
# node   0   1
#   0:  10  21
#   1:  21  10
# 距离21 > 10，说明跨节点访问更慢

# 查看NUMA统计
numastat

# 关键指标：
# numa_miss  - 本地分配失败次数
# numa_foreign - 远程分配次数
# 如果这两个值很高，说明有NUMA问题
```

## 9.2 NUMA问题排查

### 场景：CPU使用不均衡

```bash
# 现象：某些CPU核心很忙，其他很闲

# 检查每核CPU使用率
mpstat -P ALL 1 5

# 检查进程分布在哪些CPU
ps -eo pid,comm,psr | grep <process_name>
# psr列是进程运行的CPU号

# 检查NUMA内存分配
numastat -p <PID>
```

### 场景：内存访问延迟高

```bash
# 原因：进程频繁访问远程NUMA节点内存

# 使用perf检测
perf stat -e node-loads,node-load-misses,node-stores,node-store-misses -p <PID> sleep 10

# 如果miss比例高，说明跨NUMA访问多

# 使用numactl绑定进程到特定节点
numactl --cpunodebind=0 --membind=0 ./myapp
# --cpunodebind=0: 只使用node 0的CPU
# --membind=0: 只使用node 0的内存
```

## 9.3 CPU亲和性优化

```bash
# 查看进程CPU亲和性
taskset -p <PID>
# 输出是十六进制掩码

# 设置CPU亲和性
taskset -pc 0,1,2,3 <PID>  # 使用CPU 0-3
taskset -c 0-3 ./myapp     # 启动时绑定

# 系统服务设置亲和性
# /etc/systemd/system/myapp.service
[Service]
CPUAffinity=0 1 2 3

# 隔离CPU（用于实时任务）
# 启动参数：isolcpus=2,3
# 被隔离的CPU不参与普通调度
# 需要用taskset手动绑定进程

# 检查CPU隔离
cat /sys/devices/system/cpu/isolated
```

---

# 十、Steal时间与虚拟化问题

## 10.1 Steal时间解释

```bash
# Steal时间：虚拟机被宿主机偷走的CPU时间
# 只在虚拟化环境（AWS、GCP、VMware等）有意义

# 查看steal时间
top
# 看 st% 或 %steal

mpstat 1 5
# %steal 列

# steal > 5% 需要关注
# steal > 10% 有严重问题
```

## 10.2 Steal高排查

```bash
# 原因：
# 1. 宿主机CPU过载（超卖严重）
# 2. 其他虚拟机抢占资源
# 3. CPU限制（云厂商限流）

# 排查步骤：

# 1. 确认是持续性还是偶发
mpstat 1 60 | tee cpu_monitor.log
# 观察%steal变化

# 2. 检查是否有CPU限制（云环境）
# AWS: 检查CPU Credit（T系列实例）
# 阿里云: 检查CPU积分/限制

# 3. 联系云厂商或虚拟化管理员
# 可能需要迁移到负载较低的宿主机

# 4. 应对措施
# - 升级到更大规格实例
# - 使用独占型实例（Dedicated）
# - 分散负载到多个实例
```

## 10.3 虚拟化环境CPU优化

```bash
# 1. 选择合适的实例类型
# - 计算密集: C系列实例
# - 通用型: M系列实例
# - 避免突发型(T系列)用于生产

# 2. CPU亲和性设置（在虚拟机内部）
# 虚拟机内的CPU亲和性优化效果有限

# 3. 监控关键指标
# - %steal: CPU被偷走的时间
# - CPU Credit Balance (云厂商仪表盘)

# 4. 设置告警
# steal > 5% 告警
```

---

## 总结

| 问题 | 快速定位命令 | 深入分析工具 |
|------|--------------|--------------|
| CPU高 | `top`, `ps aux --sort=-%cpu` | `perf`, `strace` |
| Load高 | `uptime`, `vmstat` | `iostat`, `iotop` |
| 系统态高 | `mpstat`, `vmstat` | `perf`, `strace -c` |
| 上下文切换多 | `vmstat`, `pidstat -w` | `perf sched` |
| 软中断高 | `mpstat` (%soft), `/proc/softirqs` | `ethtool`, RPS/RFS |
| 硬中断高 | `/proc/interrupts` | 检查硬件/驱动 |
| NUMA问题 | `numastat`, `numactl --hardware` | `perf stat`, `numactl` |
| Steal高 | `mpstat` (%steal) | 联系云厂商 |
| 进程卡住 | `ps aux`, `/proc/<PID>/stack` | `strace`, `gdb` |

**软中断优化要点**：
1. 启用网卡多队列（RSS）
2. 使用irqbalance均衡中断
3. 必要时启用RPS/RFS软件分散

**上下文切换优化要点**：
1. 非自愿切换高 → 减少CPU竞争
2. 自愿切换高 → 减少IO/锁等待
3. 进程创建频繁 → 使用进程池

**NUMA优化要点**：
1. 绑定进程到特定NUMA节点
2. 使用numactl控制内存分配
3. 监控numa_miss指标

**排查三板斧**：
1. **top/htop** - 快速定位问题进程
2. **perf** - 深入分析CPU消耗点
3. **strace** - 追踪系统调用

**性能优化原则**：
1. 先定位瓶颈，再优化
2. 关注尾延迟，不只看平均值
3. 避免过度优化

---

## 相关文章

- [上一篇：网络问题排查实战](@/articles/sre/sre-27-网络问题排查实战.md)
- [下一篇：内存问题排查实战](@/articles/sre/sre-29-内存问题排查实战.md)
