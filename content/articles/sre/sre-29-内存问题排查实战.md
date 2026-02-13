+++
title = "内存问题排查实战"
date = 2026-01-21
weight = 29000
description = "SRE内存问题排查完整指南：内存泄漏、OOM、Swap深度分析、Slab缓存问题的定位与解决"
[taxonomies]
tags = ["SRE", "内存", "排查", "实战", "OOM", "Slab", "Swap", "Linux"]
+++

## 概述

内存问题往往比CPU问题更隐蔽，可能缓慢积累直到OOM。本文详细介绍内存相关问题的排查思路和解决方案。

---

# 一、内存基础概念

## 1.1 Linux内存分类

```bash
# 查看内存使用
free -h

# 输出解读：
#               total        used        free      shared  buff/cache   available
# Mem:            15G        5.2G        1.3G        234M        8.5G        9.4G
# Swap:           2G        123M        1.9G
```

| 指标 | 含义 | 说明 |
|------|------|------|
| total | 总内存 | 物理内存总量 |
| used | 已使用 | 进程实际使用 |
| free | 空闲 | 完全未使用（可能很小是正常的）|
| shared | 共享内存 | tmpfs等 |
| buff/cache | 缓冲/缓存 | 可回收的内存 |
| available | 可用 | **真正可用的内存**（含可回收部分）|

**关键理解**：`available` 才是真正可用的内存，`free` 小不代表内存紧张。

## 1.2 进程内存指标

```bash
# ps查看进程内存
ps aux --sort=-%mem | head -10

# 关键列：
# %MEM - 内存使用百分比
# VSZ - 虚拟内存大小（申请的）
# RSS - 常驻内存大小（实际使用的物理内存）
```

| 指标 | 含义 | 关注点 |
|------|------|--------|
| VSZ | 虚拟内存 | 申请但不一定使用 |
| RSS | 常驻内存 | 实际占用的物理内存 |
| PSS | 比例内存 | 共享内存按比例分摊 |
| USS | 独占内存 | 进程独占的内存 |

---

# 二、内存使用过高

## 2.1 快速定位高内存进程

### 第一步：查看整体内存状态

```bash
# 简洁视图
free -h

# 详细视图
cat /proc/meminfo

# 关键指标
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree"
```

### 第二步：找出内存大户

```bash
# 按RSS排序
ps aux --sort=-%mem | head -20

# 更精确的smem工具
sudo apt install smem
smem -rs pss | head -20

# 按进程汇总
smem -t -k -c "pid user command pss" | tail -20

# 查看特定进程的详细内存
cat /proc/<PID>/status | grep -E "VmSize|VmRSS|VmSwap|VmData|VmStk"
```

### 第三步：分析内存组成

```bash
# 查看进程内存映射
cat /proc/<PID>/maps

# 更详细的smaps
cat /proc/<PID>/smaps

# 汇总统计
cat /proc/<PID>/smaps | grep -E "^(Size|Rss|Pss|Swap):" | awk '{
    if($1=="Size:") size+=$2
    if($1=="Rss:") rss+=$2
    if($1=="Pss:") pss+=$2
    if($1=="Swap:") swap+=$2
} END {
    print "Size:", size/1024, "MB"
    print "RSS:", rss/1024, "MB"
    print "PSS:", pss/1024, "MB"
    print "Swap:", swap/1024, "MB"
}'
```

---

## 2.2 内存泄漏排查

### 场景：进程内存持续增长

**确认是否泄漏**

```bash
# 监控进程内存变化
while true; do
    echo "$(date '+%H:%M:%S') $(ps -o rss= -p <PID>) KB"
    sleep 60
done | tee memory_trend.log

# 或使用pidstat
pidstat -r -p <PID> 60

# 绘制趋势
# 如果RSS持续增长不下降，很可能是泄漏
```

### Java内存泄漏

```bash
# 查看堆内存使用
jstat -gc <PID> 1000

# 输出列含义：
# S0C/S1C - Survivor区容量
# S0U/S1U - Survivor区使用
# EC/EU - Eden区容量/使用
# OC/OU - Old区容量/使用
# MC/MU - Metaspace容量/使用

# 如果OU持续增长且不下降 → 可能泄漏

# 生成堆转储
jmap -dump:format=b,file=heap.hprof <PID>

# 分析工具
# Eclipse MAT: https://www.eclipse.org/mat/
# VisualVM: visualvm
# JProfiler（商业）

# 快速查看大对象
jmap -histo <PID> | head -30
```

**MAT分析步骤**：
1. 打开heap.hprof
2. 运行Leak Suspects Report
3. 查看Dominator Tree找大对象
4. 查看GC Roots引用链

### Go内存泄漏

```bash
# pprof获取堆profile
go tool pprof http://localhost:6060/debug/pprof/heap

# 在pprof中
(pprof) top 20
(pprof) list <function>
(pprof) web  # 可视化

# 对比两个时间点的heap
go tool pprof -base heap1.pb.gz heap2.pb.gz

# 查看goroutine泄漏
go tool pprof http://localhost:6060/debug/pprof/goroutine
```

### Python内存泄漏

```bash
# 使用memory_profiler
pip install memory_profiler

# 代码中添加装饰器
# @profile
# def my_function():

# 运行
python -m memory_profiler script.py

# 使用objgraph查看对象
pip install objgraph

# 在代码中
import objgraph
objgraph.show_most_common_types(limit=20)
objgraph.show_growth()
```

### C/C++内存泄漏

```bash
# Valgrind检测
valgrind --leak-check=full --show-leak-kinds=all ./program

# AddressSanitizer（编译时加入）
gcc -fsanitize=address -g program.c -o program
./program

# Massif堆分析
valgrind --tool=massif ./program
ms_print massif.out.*
```

---

## 2.3 Slab缓存问题

### 场景：用户进程内存不高，但系统内存被占满

```bash
# 查看Slab使用
cat /proc/meminfo | grep Slab
# Slab:            1234567 kB

# 详细的slab信息
sudo slabtop -o

# 或
cat /proc/slabinfo | sort -k3 -n -r | head -20
```

**常见Slab内存大户**

| Slab名 | 用途 | 可能原因 |
|--------|------|----------|
| dentry | 目录项缓存 | 大量小文件 |
| inode_cache | inode缓存 | 大量文件 |
| buffer_head | 缓冲头 | 频繁IO |
| ext4_inode_cache | ext4 inode | ext4大量文件 |

**清理Slab缓存**

```bash
# 清理pagecache
echo 1 > /proc/sys/vm/drop_caches

# 清理dentries和inodes
echo 2 > /proc/sys/vm/drop_caches

# 清理所有
echo 3 > /proc/sys/vm/drop_caches

# 注意：生产环境谨慎操作
sync  # 先同步
echo 3 > /proc/sys/vm/drop_caches
```

---

# 三、OOM问题

## 3.1 OOM发生时的分析

### 查看OOM日志

```bash
# dmesg查看OOM信息
dmesg | grep -i "out of memory"
dmesg | grep -i "oom"

# 查看详细OOM日志
dmesg | grep -A 50 "Out of memory"

# journalctl查看
journalctl -k | grep -i oom
```

### OOM日志解读

```
Out of memory: Kill process 12345 (java) score 850 or sacrifice child
Killed process 12345 (java), UID 1000, total-vm:8234567kB, anon-rss:4567890kB, file-rss:12345kB, shmem-rss:0kB

关键信息：
- score 850: OOM score，越高越容易被杀
- total-vm: 虚拟内存大小
- anon-rss: 匿名页RSS（主要内存）
- file-rss: 文件映射RSS
```

### 查看OOM Score

```bash
# 查看进程的OOM Score
cat /proc/<PID>/oom_score

# 查看OOM Score调整值
cat /proc/<PID>/oom_score_adj

# 查看所有进程的OOM Score
for proc in /proc/[0-9]*; do
    pid=$(basename $proc)
    score=$(cat $proc/oom_score 2>/dev/null)
    name=$(cat $proc/comm 2>/dev/null)
    [ -n "$score" ] && echo "$score $pid $name"
done | sort -rn | head -20
```

## 3.2 预防OOM

### 调整OOM Score

```bash
# 降低重要进程被杀的概率
# -1000到1000，-1000表示永不被杀
echo -500 > /proc/<PID>/oom_score_adj

# 或使用systemd
# /etc/systemd/system/myservice.service.d/override.conf
[Service]
OOMScoreAdjust=-500

# 完全禁止被OOM杀死（谨慎使用）
echo -1000 > /proc/<PID>/oom_score_adj
```

### 设置内存限制

```bash
# cgroups v1
mkdir /sys/fs/cgroup/memory/mygroup
echo 1073741824 > /sys/fs/cgroup/memory/mygroup/memory.limit_in_bytes  # 1GB
echo <PID> > /sys/fs/cgroup/memory/mygroup/cgroup.procs

# cgroups v2 (systemd)
systemctl set-property myservice.service MemoryMax=1G

# 或在unit文件中
[Service]
MemoryMax=1G
MemoryHigh=800M
```

### 配置Overcommit策略

```bash
# 查看当前策略
cat /proc/sys/vm/overcommit_memory
# 0 - 启发式（默认）
# 1 - 总是允许
# 2 - 不允许超过限制

# 设置为不过度分配
sysctl -w vm.overcommit_memory=2
sysctl -w vm.overcommit_ratio=80  # 允许使用swap+80%物理内存
```

---

# 四、Swap问题

## 4.1 Swap使用分析

### 查看Swap状态

```bash
# 查看Swap使用
free -h
swapon -s

# 查看哪些进程使用了Swap
for proc in /proc/[0-9]*; do
    pid=$(basename $proc)
    swap=$(awk '/VmSwap/{print $2}' $proc/status 2>/dev/null)
    name=$(cat $proc/comm 2>/dev/null)
    [ -n "$swap" ] && [ "$swap" != "0" ] && echo "$swap $pid $name"
done | sort -rn | head -20

# 或使用smem
smem -rs swap | head -20
```

### Swap IO分析

```bash
# 查看Swap IO
vmstat 1 10
# 关注si（swap in）和so（swap out）

# iostat查看swap设备
iostat -x 1 5

# sar历史数据
sar -W 1 10
```

## 4.2 Swap使用过高问题

### 场景：系统响应慢，Swap使用高

**排查步骤**

```bash
# 1. 确认是否在频繁换页
vmstat 1 10
# si/so持续大于0说明在换页

# 2. 找出使用Swap的进程
smem -rs swap | head -10

# 3. 分析是否是内存不足
cat /proc/meminfo | grep -E "MemTotal|MemAvailable|SwapTotal|SwapFree"

# 4. 检查是否是swappiness设置问题
cat /proc/sys/vm/swappiness
# 默认60，越高越倾向使用swap
```

**解决方案**

```bash
# 临时减少swap使用倾向
sysctl -w vm.swappiness=10

# 永久设置
echo "vm.swappiness=10" >> /etc/sysctl.conf
sysctl -p

# 清空swap（谨慎操作，需要足够内存）
swapoff -a && swapon -a

# 增加内存或扩大Swap（如果确实内存不足）
# 创建swapfile
dd if=/dev/zero of=/swapfile bs=1G count=4
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

# 五、内存泄漏场景实战

## 5.1 场景：文件描述符泄漏导致内存增长

```bash
# 检查进程打开的文件数
ls /proc/<PID>/fd | wc -l
lsof -p <PID> | wc -l

# 对比文件描述符限制
cat /proc/<PID>/limits | grep "open files"

# 查看打开的是什么
lsof -p <PID> | head -50

# 常见问题：
# - socket连接未关闭
# - 文件未close
# - pipe未关闭
```

## 5.2 场景：共享内存泄漏

```bash
# 查看共享内存
ipcs -m

# 查看共享内存详情
ipcs -m -p  # 显示创建者PID

# 删除孤儿共享内存
ipcrm -m <shmid>

# 查看tmpfs使用（/dev/shm）
df -h /dev/shm
ls -la /dev/shm
```

## 5.3 场景：内存碎片

```bash
# 查看内存碎片情况
cat /proc/buddyinfo

# 输出解读：
# Node 0, zone   Normal   1234   567   234   123   56   23   12   5   2   1   0
# 数字表示各order（2^order个页）的空闲块数量
# 高order数量少说明碎片化严重

# 尝试内存压缩
echo 1 > /proc/sys/vm/compact_memory

# 查看Transparent HugePages
cat /sys/kernel/mm/transparent_hugepage/enabled
```

---

# 六、内存调优

## 6.1 关键参数调优

```bash
# /etc/sysctl.conf

# Swap使用倾向（0-100，默认60）
vm.swappiness = 10

# 脏页写回阈值
vm.dirty_ratio = 20
vm.dirty_background_ratio = 5

# OOM相关
vm.panic_on_oom = 0
vm.oom_kill_allocating_task = 1

# 内存过度分配
vm.overcommit_memory = 0
vm.overcommit_ratio = 50

# 最小空闲内存
vm.min_free_kbytes = 65536

# 应用配置
sysctl -p
```

## 6.2 大页内存配置

```bash
# 查看大页状态
cat /proc/meminfo | grep Huge

# 配置大页
# 永久配置
echo "vm.nr_hugepages = 1024" >> /etc/sysctl.conf
sysctl -p

# 挂载hugetlbfs
mkdir /mnt/hugepages
mount -t hugetlbfs nodev /mnt/hugepages

# 应用使用（如MySQL、Redis等配置）
```

---

# 七、诊断脚本

## 7.1 内存诊断脚本

```bash
#!/bin/bash
# memory_diagnose.sh - 内存诊断脚本

echo "===== 内存诊断报告 ====="
echo "时间: $(date)"
echo ""

echo "--- 1. 内存概览 ---"
free -h
echo ""

echo "--- 2. 详细内存信息 ---"
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree|Slab|SReclaimable"
echo ""

echo "--- 3. Top 10 内存进程 (RSS) ---"
ps aux --sort=-%mem | head -11
echo ""

echo "--- 4. Swap使用进程 ---"
echo "Swap(KB) PID Command"
for proc in /proc/[0-9]*; do
    pid=$(basename $proc)
    swap=$(awk '/VmSwap/{print $2}' $proc/status 2>/dev/null)
    name=$(cat $proc/comm 2>/dev/null)
    [ -n "$swap" ] && [ "$swap" != "0" ] && echo "$swap $pid $name"
done | sort -rn | head -10
echo ""

echo "--- 5. Slab Top 10 ---"
cat /proc/slabinfo | awk 'NR>2 {print $3*$4, $1}' | sort -rn | head -10
echo ""

echo "--- 6. 内存碎片 ---"
cat /proc/buddyinfo
echo ""

echo "--- 7. 最近OOM事件 ---"
dmesg | grep -i "out of memory" | tail -5 || echo "无OOM记录"
echo ""

echo "--- 8. Swap IO ---"
vmstat 1 3
echo ""

echo "===== 诊断完成 ====="
```

## 7.2 内存监控脚本

```bash
#!/bin/bash
# memory_monitor.sh - 内存持续监控

LOG_FILE="/var/log/memory_monitor.log"
THRESHOLD=90  # 内存使用率告警阈值

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 获取内存使用率
    MEM_TOTAL=$(awk '/MemTotal/{print $2}' /proc/meminfo)
    MEM_AVAILABLE=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
    MEM_USED=$((MEM_TOTAL - MEM_AVAILABLE))
    MEM_PERCENT=$((MEM_USED * 100 / MEM_TOTAL))
    
    echo "$TIMESTAMP Memory: ${MEM_PERCENT}% (Used: $((MEM_USED/1024))MB / Total: $((MEM_TOTAL/1024))MB)" >> $LOG_FILE
    
    if [ $MEM_PERCENT -gt $THRESHOLD ]; then
        echo "$TIMESTAMP WARNING: 内存使用率超过${THRESHOLD}%" >> $LOG_FILE
        echo "Top 5 内存进程:" >> $LOG_FILE
        ps aux --sort=-%mem | head -6 >> $LOG_FILE
        echo "" >> $LOG_FILE
    fi
    
    sleep 60
done
```

---

# 八、Slab深度排查

## 8.1 Slab内存机制详解

### 什么是Slab

```bash
# Slab是Linux内核的内存分配器
# 用于高效分配小块内存（内核对象）

# Slab的三层结构：
# 1. Cache - 特定类型对象的缓存池
# 2. Slab - 由一个或多个连续物理页组成
# 3. Object - 实际的内核对象

# 查看Slab总体使用
cat /proc/meminfo | grep -i slab
# Slab:            1234567 kB  # Slab总使用
# SReclaimable:     987654 kB  # 可回收部分（缓存）
# SUnreclaim:       246913 kB  # 不可回收部分（活跃对象）

# 关键理解：
# SReclaimable 是缓存，内存紧张时可自动回收
# SUnreclaim 是活跃内核对象，无法回收
```

### Slab统计命令

```bash
# slabtop - 实时监控Slab使用（类似top）
sudo slabtop

# 输出列说明：
# OBJS    - 对象数量
# ACTIVE  - 活跃对象数量
# USE     - 使用率
# OBJ SIZE - 单个对象大小
# SLABS   - slab数量
# OBJ/SLAB - 每个slab的对象数
# CACHE SIZE - 缓存总大小
# NAME    - 缓存名称

# 按缓存大小排序
sudo slabtop -s c

# 一次性输出（非交互）
sudo slabtop -o

# 指定刷新间隔
sudo slabtop -d 2

# 使用slabinfo查看详细信息
cat /proc/slabinfo

# 格式化输出Slab Top 20
cat /proc/slabinfo | awk 'NR>2 {
    size=$3*$4
    if(size>0) print size, $1
}' | sort -rn | head -20

# 计算总Slab内存
cat /proc/slabinfo | awk 'NR>2 {sum+=$3*$4} END {print sum/1024/1024, "MB"}'
```

## 8.2 常见Slab问题场景

### 场景一：dentry/inode缓存过大

```bash
# 症状：Slab占用大量内存，主要是dentry和inode_cache
# 原因：大量文件/目录操作，缓存了目录项和inode

# 检查dentry和inode使用
cat /proc/slabinfo | grep -E "dentry|inode" | head -10

# 输出示例：
# dentry              1234567 1234567    192   21    1 : ...
# inode_cache          567890  567890    600    6    1 : ...

# 计算dentry占用
cat /proc/slabinfo | awk '/^dentry/{print $3*$4/1024/1024, "MB"}'

# 常见原因：
# 1. 大量小文件（如日志切割、临时文件）
# 2. 频繁遍历大目录（如find、ls -R）
# 3. 监控程序频繁扫描文件系统

# 排查步骤：

# 1. 找出哪个文件系统产生最多缓存
cat /proc/sys/fs/dentry-state
# 输出：nr_dentry nr_unused age_limit want_pages

# 2. 查看文件系统使用情况
df -i  # 查看inode使用

# 3. 找出大目录
find / -type d 2>/dev/null | while read d; do
    count=$(ls -1 "$d" 2>/dev/null | wc -l)
    [ $count -gt 10000 ] && echo "$count $d"
done | sort -rn | head -10

# 4. 检查是否有程序频繁扫描文件
# 使用fatrace监控文件访问
sudo fatrace 2>/dev/null | head -100

# 解决方案：
# 1. 清理不必要的小文件
# 2. 调整vfs_cache_pressure
echo 200 > /proc/sys/vm/vfs_cache_pressure  # 加速回收

# 3. 手动触发回收
sync
echo 2 > /proc/sys/vm/drop_caches  # 释放dentries和inodes
```

### 场景二：特定Slab异常增长

```bash
# 症状：某个特定slab持续增长，可能是内核内存泄漏

# 监控Slab变化
while true; do
    echo "=== $(date) ==="
    cat /proc/slabinfo | awk 'NR>2 {print $3*$4, $1}' | sort -rn | head -10
    sleep 60
done | tee slab_monitor.log

# 分析增长趋势
# 如果某个slab持续增长不下降，可能有问题

# 常见问题slab：
# 1. kmalloc-* - 通用内存分配，可能是驱动/模块泄漏
# 2. task_struct - 进程结构，僵尸进程过多
# 3. sock_inode_cache - socket结构，连接泄漏
# 4. TCP/UDP - 网络连接相关
# 5. buffer_head - 块设备缓冲

# 排查kmalloc泄漏
cat /proc/slabinfo | grep kmalloc | sort -t' ' -k3 -rn | head -10

# 检查是否是内核模块问题
lsmod | head -20
# 尝试卸载可疑模块测试

# 检查网络相关slab
cat /proc/slabinfo | grep -E "sock|tcp|udp|skb"
```

### 场景三：buffer_head过大

```bash
# 症状：buffer_head slab占用大量内存
# 原因：频繁的块设备I/O

cat /proc/slabinfo | grep buffer_head

# 排查步骤：

# 1. 检查I/O活动
iostat -x 1 5

# 2. 找出高I/O进程
iotop -o

# 3. 检查是否有大量小文件读写
# buffer_head通常与元数据操作相关

# 解决方案：
# 1. 减少不必要的I/O
# 2. 使用更大的块大小
# 3. 清理缓存
sync
echo 1 > /proc/sys/vm/drop_caches
```

## 8.3 Slab内存泄漏排查

### 使用kmemleak检测

```bash
# kmemleak是内核内存泄漏检测工具
# 需要内核编译时开启 CONFIG_DEBUG_KMEMLEAK

# 检查是否支持
cat /sys/kernel/debug/kmemleak 2>/dev/null

# 触发扫描
echo scan > /sys/kernel/debug/kmemleak

# 查看泄漏报告
cat /sys/kernel/debug/kmemleak

# 清除已知泄漏
echo clear > /sys/kernel/debug/kmemleak

# 注意：生产环境通常不开启kmemleak（性能影响）
```

### 使用ftrace追踪

```bash
# 追踪slab分配
echo 1 > /sys/kernel/debug/tracing/events/kmem/kmalloc/enable
echo 1 > /sys/kernel/debug/tracing/events/kmem/kfree/enable

# 查看追踪
cat /sys/kernel/debug/tracing/trace_pipe | head -100

# 关闭追踪
echo 0 > /sys/kernel/debug/tracing/events/kmem/kmalloc/enable
echo 0 > /sys/kernel/debug/tracing/events/kmem/kfree/enable
```

### Slab诊断脚本

```bash
#!/bin/bash
# slab_diagnose.sh - Slab深度诊断

echo "===== Slab诊断报告 ====="
echo "时间: $(date)"
echo ""

echo "--- 1. Slab概览 ---"
cat /proc/meminfo | grep -i slab
echo ""

echo "--- 2. 可回收 vs 不可回收 ---"
RECLAIMABLE=$(awk '/SReclaimable/{print $2}' /proc/meminfo)
UNRECLAIMABLE=$(awk '/SUnreclaim/{print $2}' /proc/meminfo)
echo "SReclaimable: $((RECLAIMABLE/1024)) MB"
echo "SUnreclaim: $((UNRECLAIMABLE/1024)) MB"
echo ""

echo "--- 3. Top 15 Slab缓存 ---"
printf "%-40s %15s %15s\n" "NAME" "SIZE(MB)" "OBJECTS"
cat /proc/slabinfo | awk 'NR>2 {
    size=$3*$4/1024/1024
    if(size>0.1) printf "%-40s %15.2f %15d\n", $1, size, $3
}' | sort -k2 -rn | head -15
echo ""

echo "--- 4. dentry/inode状态 ---"
echo "dentry-state: $(cat /proc/sys/fs/dentry-state)"
echo "inode-state: $(cat /proc/sys/fs/inode-state)"
echo ""

echo "--- 5. 文件系统缓存压力 ---"
echo "vfs_cache_pressure: $(cat /proc/sys/vm/vfs_cache_pressure)"
echo ""

echo "--- 6. 网络相关Slab ---"
cat /proc/slabinfo | grep -E "sock|tcp|udp|skb" | awk '{
    size=$3*$4/1024
    if(size>0) printf "%-30s %10.2f KB\n", $1, size
}'
echo ""

echo "===== 诊断完成 ====="
```

## 8.4 Slab调优参数

```bash
# /etc/sysctl.conf

# VFS缓存回收压力（默认100）
# 值越高，越倾向回收dentry/inode缓存
vm.vfs_cache_pressure = 100
# 内存紧张时设置为150-200加速回收
# 文件服务器可设置为50减少回收

# 最小空闲内存（防止Slab占用过多）
vm.min_free_kbytes = 65536

# 脏页阈值（影响buffer_head）
vm.dirty_ratio = 20
vm.dirty_background_ratio = 5

# 应用配置
sysctl -p
```

---

# 九、Swap深度分析

## 9.1 Swap机制详解

```bash
# Swap的作用：
# 1. 内存不足时，将不活跃页面换出到磁盘
# 2. 为应用提供更大的虚拟内存空间
# 3. 休眠时保存内存状态

# 查看Swap配置
swapon -s
# 或
cat /proc/swaps

# 输出：
# Filename                Type        Size    Used    Priority
# /dev/sda2               partition   2097148 123456  -2
# /swapfile               file        1048572 0       -3

# Priority说明：
# 数值越高优先使用
# 相同优先级会轮流使用（类似RAID0）
```

### Swap状态详细分析

```bash
# 查看详细Swap统计
cat /proc/meminfo | grep -i swap
# SwapCached:     12345 kB  # 在swap中但也在内存中
# SwapTotal:    2097148 kB  # 总Swap空间
# SwapFree:     1973692 kB  # 空闲Swap

# 查看Swap IO统计
vmstat 1 5
# 关注 si (swap in) 和 so (swap out)
# si: 从swap读入内存的速率 (KB/s)
# so: 从内存写入swap的速率 (KB/s)

# 使用sar查看历史数据
sar -W 1 10
# pswpin/s  - swap in 每秒次数
# pswpout/s - swap out 每秒次数

# 详细的swap活动
cat /proc/vmstat | grep -i swap
# pswpin   - swap in 次数
# pswpout  - swap out 次数
```

## 9.2 Swap使用过高排查

### 定位使用Swap的进程

```bash
# 方法1：遍历/proc
for proc in /proc/[0-9]*; do
    pid=$(basename $proc)
    swap=$(awk '/VmSwap/{print $2}' $proc/status 2>/dev/null)
    name=$(cat $proc/comm 2>/dev/null)
    if [ -n "$swap" ] && [ "$swap" != "0" ]; then
        echo "$swap $pid $name"
    fi
done | sort -rn | head -20

# 方法2：使用smem
sudo smem -rs swap | head -20

# 方法3：使用脚本格式化输出
#!/bin/bash
printf "%-10s %-8s %-15s %s\n" "SWAP(KB)" "PID" "USER" "COMMAND"
for pid in $(ls /proc | grep '^[0-9]*$'); do
    swap=$(awk '/VmSwap/{print $2}' /proc/$pid/status 2>/dev/null)
    if [ -n "$swap" ] && [ "$swap" != "0" ] && [ "$swap" != "" ]; then
        user=$(stat -c '%U' /proc/$pid 2>/dev/null)
        cmd=$(cat /proc/$pid/comm 2>/dev/null)
        printf "%-10s %-8s %-15s %s\n" "$swap" "$pid" "$user" "$cmd"
    fi
done | sort -rn | head -20
```

### Swap风暴排查

```bash
# Swap风暴现象：
# 1. si/so持续很高
# 2. 系统响应极慢
# 3. CPU等待IO时间高（wa）

# 实时监控
vmstat 1
# 关注：
# si > 0 且持续 → 内存不足，频繁换入
# so > 0 且持续 → 内存压力大，频繁换出
# wa 很高 → IO等待，可能是swap导致

# 排查步骤：

# 1. 确认是否真的内存不足
free -h
cat /proc/meminfo | grep -E "MemTotal|MemAvailable|SwapTotal|SwapFree"

# 2. 检查swappiness设置
cat /proc/sys/vm/swappiness
# 默认60，值越高越倾向使用swap

# 3. 找出内存大户
ps aux --sort=-%mem | head -20

# 4. 检查是否有内存泄漏
# 观察进程RSS是否持续增长

# 5. 检查是否有cgroup内存限制
cat /sys/fs/cgroup/memory/*/memory.limit_in_bytes 2>/dev/null
```

### 解决Swap问题

```bash
# 临时方案：

# 1. 降低swappiness
sysctl -w vm.swappiness=10

# 2. 杀死高内存进程（谨慎）
# 先确认进程可以杀

# 3. 清空Swap（需要足够内存）
free -h  # 确认有足够可用内存
swapoff -a && swapon -a

# 4. 增加物理内存或增大Swap
# 创建swapfile
dd if=/dev/zero of=/swapfile2 bs=1G count=4
chmod 600 /swapfile2
mkswap /swapfile2
swapon /swapfile2

# 永久方案：

# 1. 调整swappiness
echo "vm.swappiness = 10" >> /etc/sysctl.conf
sysctl -p

# 2. 调整应用内存限制
# Java: -Xmx 限制堆大小
# 容器: memory.limit

# 3. 增加物理内存

# 4. 优化应用减少内存使用
```

## 9.3 Swap性能影响分析

```bash
# Swap对性能的影响

# 1. 延迟增加
# HDD Swap: 10-20ms 延迟
# SSD Swap: 0.1-1ms 延迟
# 内存访问: 100ns

# 测量Swap延迟
dd if=/dev/sda2 of=/dev/null bs=4k count=1000 iflag=direct 2>&1 | tail -1

# 2. 吞吐量受限
# Swap带宽远低于内存带宽

# 3. 随机IO问题
# Swap访问模式通常是随机的，对HDD影响大

# 优化建议：
# 1. 使用SSD作为Swap（如果必须用Swap）
# 2. 将Swap放在独立磁盘，避免与数据盘竞争
# 3. 对于延迟敏感应用，尽量避免使用Swap

# zram作为Swap替代
# 使用压缩内存作为swap，速度更快
modprobe zram
echo lz4 > /sys/block/zram0/comp_algorithm
echo 2G > /sys/block/zram0/disksize
mkswap /dev/zram0
swapon -p 100 /dev/zram0  # 高优先级
```

## 9.4 Swap监控脚本

```bash
#!/bin/bash
# swap_monitor.sh - Swap监控与告警

THRESHOLD=50  # Swap使用率告警阈值(%)
LOG_FILE="/var/log/swap_monitor.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 获取Swap使用率
    SWAP_TOTAL=$(awk '/SwapTotal/{print $2}' /proc/meminfo)
    SWAP_FREE=$(awk '/SwapFree/{print $2}' /proc/meminfo)
    
    if [ "$SWAP_TOTAL" -gt 0 ]; then
        SWAP_USED=$((SWAP_TOTAL - SWAP_FREE))
        SWAP_PERCENT=$((SWAP_USED * 100 / SWAP_TOTAL))
        
        # 获取swap IO
        SI=$(vmstat 1 2 | tail -1 | awk '{print $7}')
        SO=$(vmstat 1 2 | tail -1 | awk '{print $8}')
        
        echo "$TIMESTAMP Swap: ${SWAP_PERCENT}% (${SWAP_USED}/${SWAP_TOTAL}KB) SI:${SI} SO:${SO}" >> $LOG_FILE
        
        if [ $SWAP_PERCENT -gt $THRESHOLD ]; then
            echo "$TIMESTAMP WARNING: Swap使用率超过${THRESHOLD}%" >> $LOG_FILE
            echo "Top 5 Swap进程:" >> $LOG_FILE
            for pid in $(ls /proc | grep '^[0-9]*$'); do
                swap=$(awk '/VmSwap/{print $2}' /proc/$pid/status 2>/dev/null)
                if [ -n "$swap" ] && [ "$swap" != "0" ]; then
                    cmd=$(cat /proc/$pid/comm 2>/dev/null)
                    echo "$swap $pid $cmd"
                fi
            done | sort -rn | head -5 >> $LOG_FILE
            echo "" >> $LOG_FILE
        fi
    fi
    
    sleep 60
done
```

---

## 总结

| 问题 | 快速命令 | 深入分析 |
|------|----------|----------|
| 内存使用高 | `free -h`, `ps aux --sort=-%mem` | `smem`, `/proc/<PID>/smaps` |
| 内存泄漏 | `pidstat -r` | `jmap`, `valgrind`, `pprof` |
| OOM | `dmesg \| grep oom` | 分析OOM日志 |
| Swap高 | `vmstat`, `smem -rs swap` | `sar -W`, Swap进程分析 |
| Swap风暴 | `vmstat` (si/so持续高) | 降swappiness, 增内存 |
| Slab高 | `slabtop` | `/proc/slabinfo`, 分类分析 |
| dentry泄漏 | `slabtop \| grep dentry` | vfs_cache_pressure调优 |
| 内核内存泄漏 | `slabtop`监控趋势 | kmemleak, ftrace |

**Slab排查要点**：
1. 先区分SReclaimable（可回收）和SUnreclaim（不可回收）
2. dentry/inode过大通常是文件操作导致，可调整vfs_cache_pressure
3. 特定slab持续增长可能是内核模块问题

**Swap排查要点**：
1. swappiness控制使用Swap的倾向，数据库建议设10-30
2. si/so持续大于0说明内存压力大
3. 清空Swap前确保有足够可用内存

**排查三板斧**：
1. **free/top** - 快速确认整体状态
2. **ps/smem** - 定位高内存进程
3. **专用工具** - jmap/valgrind/pprof/slabtop深入分析

**关键理解**：
1. `available` 才是真正可用内存，`free` 小是正常的
2. 内存泄漏需要观察趋势，单次采样不够
3. OOM不一定是坏事，是系统保护机制
4. Slab的SReclaimable部分是正常缓存，不必担心

---

## 相关文章

- [上一篇：CPU问题排查实战](@/articles/sre/sre-28-CPU问题排查实战.md)
- [下一篇：磁盘与存储问题排查实战](@/articles/sre/sre-30-磁盘与存储问题排查实战.md)
