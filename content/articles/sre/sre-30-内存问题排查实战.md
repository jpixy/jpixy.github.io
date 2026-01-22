+++
title = "30.内存问题排查实战"
date = 2026-01-21
description = "SRE内存问题排查完整指南：内存泄漏、OOM、Swap使用过高的定位与解决"
[taxonomies]
tags = ["SRE", "内存", "排查", "实战", "OOM", "Linux"]
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

## 总结

| 问题 | 快速命令 | 深入分析 |
|------|----------|----------|
| 内存使用高 | `free -h`, `ps aux --sort=-%mem` | `smem`, `/proc/<PID>/smaps` |
| 内存泄漏 | `pidstat -r` | `jmap`, `valgrind`, `pprof` |
| OOM | `dmesg \| grep oom` | 分析OOM日志 |
| Swap高 | `vmstat`, `smem -rs swap` | `sar -W` |
| Slab高 | `slabtop` | `/proc/slabinfo` |

**排查三板斧**：
1. **free/top** - 快速确认整体状态
2. **ps/smem** - 定位高内存进程
3. **专用工具** - jmap/valgrind/pprof深入分析

**关键理解**：
1. `available` 才是真正可用内存，`free` 小是正常的
2. 内存泄漏需要观察趋势，单次采样不够
3. OOM不一定是坏事，是系统保护机制
