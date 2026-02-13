+++
title = "iostat IO统计深度解析"
date = 2026-01-31
weight = 52000
description = "iostat深度解析：磁盘性能监控、IOPS分析、延迟指标、瓶颈诊断"
[taxonomies]
tags = ["Linux", "iostat", "IO", "性能", "监控"]
+++

# iostat IO 统计深度解析

本文深入解析 iostat 工具的工作原理，包括磁盘性能监控、IOPS 分析、延迟指标等核心技术。

---

## 一、iostat 概述

### 1.1 什么是 iostat

**iostat** 是 sysstat 套件中的工具，用于：
- 监控磁盘 IO 性能
- 统计 CPU 使用率
- 分析存储瓶颈

### 1.2 数据来源

```mermaid
graph TB
    A[/proc/diskstats]
    B[/proc/stat]
    C[iostat]

    A --> C
    B --> C
    C --> D[设备统计]
    C --> E[CPU 统计]
```

---

## 二、基本使用

### 2.1 安装

```bash
# Debian/Ubuntu
sudo apt install sysstat

# CentOS/RHEL
sudo yum install sysstat
```

### 2.2 基本命令

```bash
# 默认输出
iostat

# 每 2 秒刷新，共 5 次
iostat 2 5

# 显示扩展统计
iostat -x

# 只显示设备统计
iostat -d

# 只显示 CPU 统计
iostat -c

# 以 MB 为单位
iostat -m

# 以 KB 为单位
iostat -k

# 指定设备
iostat -x sda sdb

# JSON 输出
iostat -x -o JSON
```

### 2.3 常用选项

| 选项 | 说明 |
|------|------|
| `-x` | 扩展统计信息 |
| `-d` | 只显示设备 |
| `-c` | 只显示 CPU |
| `-k` | KB 单位 |
| `-m` | MB 单位 |
| `-p` | 包含分区 |
| `-t` | 显示时间戳 |
| `-z` | 忽略无活动设备 |
| `-N` | 显示 LVM 名称 |
| `-h` | 人类可读 |

---

## 三、输出解读

### 3.1 基本输出

```bash
$ iostat
Linux 5.4.0-89-generic    01/31/26    _x86_64_

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           5.23    0.10    2.15    1.50    0.00   91.02

Device             tps    kB_read/s    kB_wrtn/s    kB_read    kB_wrtn
sda             125.50      2048.00      1024.00   10240000    5120000
sdb              50.25       512.00       256.00    2560000    1280000
```

| 字段 | 说明 |
|------|------|
| tps | 每秒事务数（IOPS） |
| kB_read/s | 每秒读取 KB |
| kB_wrtn/s | 每秒写入 KB |
| kB_read | 总读取 KB |
| kB_wrtn | 总写入 KB |

### 3.2 扩展输出 (-x)

```bash
$ iostat -x 1
Device         r/s     w/s    rkB/s    wkB/s avgrq-sz avgqu-sz   await r_await w_await  svctm  %util
sda          50.00   75.50  2048.00  1024.00    49.04     2.50   20.00   15.00   23.33   5.00  62.69
sdb          25.00   25.25   512.00   256.00    30.72     0.50   10.00    8.00   12.00   3.00  15.08
```

**关键指标**：

| 字段 | 说明 | 健康值 |
|------|------|--------|
| r/s | 每秒读次数 | - |
| w/s | 每秒写次数 | - |
| rkB/s | 每秒读 KB | - |
| wkB/s | 每秒写 KB | - |
| avgrq-sz | 平均请求大小（扇区） | - |
| avgqu-sz | 平均队列长度 | <2 理想 |
| await | 平均等待时间（ms） | SSD <1ms, HDD <10ms |
| r_await | 读等待时间 | - |
| w_await | 写等待时间 | - |
| svctm | 平均服务时间（已弃用） | - |
| %util | 设备利用率 | <70% 健康 |

### 3.3 指标详解

```
await = 队列等待时间 + 设备服务时间
      = avgqu-sz / (r/s + w/s) * 1000 + 设备服务时间

%util = (r/s + w/s) * svctm / 1000 * 100

注意：
- SSD 的 %util 可能 100% 但仍有余量（因为并发）
- HDD 的 %util 接近 100% 通常意味着饱和
```

---

## 四、性能分析

### 4.1 识别瓶颈

```bash
# 高利用率
%util > 70%  →  设备可能饱和

# 高队列长度
avgqu-sz > 2  →  请求积压

# 高延迟
await > 10ms (HDD) 或 > 1ms (SSD)  →  响应慢

# 高 iowait
%iowait > 10%  →  CPU 等待 IO
```

### 4.2 分析脚本

```bash
#!/bin/bash
# io_analysis.sh

DEVICE=${1:-sda}
INTERVAL=${2:-1}
COUNT=${3:-10}

echo "Analyzing $DEVICE for $COUNT samples..."

iostat -x $DEVICE $INTERVAL $COUNT | awk '
    /^'$DEVICE'/ {
        util_sum += $NF
        await_sum += $(NF-4)
        count++
    }
    END {
        if (count > 0) {
            print "Average %util:", util_sum/count
            print "Average await:", await_sum/count, "ms"

            if (util_sum/count > 70)
                print "WARNING: High utilization"
            if (await_sum/count > 10)
                print "WARNING: High latency"
        }
    }
'
```

### 4.3 SSD vs HDD 分析

```bash
# SSD 特点
# - %util 不太可靠（并发 IO）
# - 关注 await 更重要
# - avgqu-sz 可以更高

# HDD 特点
# - %util 是好的饱和指标
# - await 受寻道影响
# - 顺序 IO 性能更好

# 区分方法
cat /sys/block/sda/queue/rotational
# 0 = SSD, 1 = HDD
```

---

## 五、高级用法

### 5.1 持续监控

```bash
# 每秒采样，输出到文件
iostat -x 1 >> iostat.log &

# 带时间戳
iostat -x -t 1 >> iostat.log &

# 监控特定时间
timeout 3600 iostat -x 1 > iostat_1hour.log
```

### 5.2 JSON 输出

```bash
# JSON 格式
iostat -x -o JSON 1 1

# 解析 JSON
iostat -x -o JSON 1 1 | jq '.sysstat.hosts[0].statistics[0].disk[]'
```

### 5.3 与其他工具结合

```bash
# 与 pidstat 结合
pidstat -d 1    # 进程级 IO

# 与 iotop 结合
iotop -o        # 实时进程 IO

# 与 blktrace 结合
# iostat 发现问题后用 blktrace 深入分析
```

---

## 六、实战场景

### 6.1 数据库性能诊断

```bash
# MySQL 服务器 IO 分析
iostat -x 1 | while read line; do
    echo "$line" | grep -E 'sda|sdb' | awk '{
        if ($NF > 80 || $(NF-4) > 5) {
            print strftime("%Y-%m-%d %H:%M:%S"), "ALERT:", $0
        }
    }'
done
```

### 6.2 监控报警脚本

```bash
#!/bin/bash
# io_alert.sh

THRESHOLD_UTIL=80
THRESHOLD_AWAIT=20
DEVICE=$1

while true; do
    result=$(iostat -x $DEVICE 1 2 | tail -1)
    util=$(echo $result | awk '{print $NF}' | cut -d. -f1)
    await=$(echo $result | awk '{print $(NF-4)}' | cut -d. -f1)

    if [ "$util" -gt "$THRESHOLD_UTIL" ]; then
        echo "ALERT: $DEVICE util=${util}% > ${THRESHOLD_UTIL}%"
    fi

    if [ "$await" -gt "$THRESHOLD_AWAIT" ]; then
        echo "ALERT: $DEVICE await=${await}ms > ${THRESHOLD_AWAIT}ms"
    fi

    sleep 5
done
```

---

## 七、与同类工具对比

| 特性 | iostat | iotop | dstat | sar |
|------|--------|-------|-------|-----|
| 设备级统计 | ✅ | ❌ | ✅ | ✅ |
| 进程级统计 | ❌ | ✅ | ❌ | ❌ |
| 实时刷新 | ✅ | ✅ | ✅ | ❌ |
| 历史数据 | ❌ | ❌ | ❌ | ✅ |
| 延迟指标 | ✅ | ❌ | ❌ | ✅ |

---

## 八、高频考点总结

| 考点 | 频率 | 关键知识 |
|------|------|----------|
| 关键指标 | ★★★ | await、%util、avgqu-sz |
| 瓶颈识别 | ★★★ | 利用率、队列、延迟判断 |
| 基本用法 | ★★☆ | -x、-d、间隔、次数 |
| SSD vs HDD | ★★☆ | %util 对 SSD 不可靠 |
| 与其他工具配合 | ★★☆ | pidstat、iotop、blktrace |

---

## 相关文章

- [上一篇：blktrace块设备追踪深度解析](@/articles/linux/linux-51-blktrace块设备追踪深度解析.md)
- [fio磁盘IO性能测试深度解析](@/articles/linux/linux-42-fio磁盘IO性能测试深度解析.md)
