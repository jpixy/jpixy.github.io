+++
title = "53.stress-ng压力测试深度解析"
date = 2026-01-31
description = "stress-ng深度解析：CPU/内存/IO压力测试、系统稳定性验证"
[taxonomies]
tags = ["Linux", "stress-ng", "压力测试", "性能", "稳定性"]
+++

# stress-ng 压力测试深度解析

本文深入解析 stress-ng 工具的工作原理，包括 CPU、内存、IO 压力测试等核心技术。

---

## 一、stress-ng 概述

### 1.1 什么是 stress-ng

**stress-ng** 是一个系统压力测试工具，用于：
- CPU 压力测试
- 内存压力测试
- IO 压力测试
- 系统稳定性验证
- 性能基准测试

### 1.2 stress-ng vs stress

| 特性 | stress-ng | stress |
|------|-----------|--------|
| 压力源数量 | 300+ | 4 |
| 配置灵活性 | 高 | 低 |
| 统计输出 | 详细 | 无 |
| 验证功能 | ✅ | ❌ |
| 维护状态 | 活跃 | 停滞 |

---

## 二、基本使用

### 2.1 安装

```bash
# Debian/Ubuntu
sudo apt install stress-ng

# CentOS/RHEL
sudo yum install stress-ng

# 从源码编译
git clone https://github.com/ColinIanKing/stress-ng.git
cd stress-ng
make && sudo make install
```

### 2.2 基本语法

```bash
stress-ng [选项] [压力源...]
```

### 2.3 常用选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `--cpu N` | CPU 压力（N 个工作进程） | `--cpu 4` |
| `--vm N` | 内存压力 | `--vm 2` |
| `--io N` | IO 压力 | `--io 4` |
| `--hdd N` | 磁盘压力 | `--hdd 2` |
| `-t TIME` | 运行时长 | `-t 60s` |
| `--timeout` | 同 -t | `--timeout 1m` |
| `--metrics` | 显示指标 | `--metrics` |
| `--yaml FILE` | YAML 输出 | `--yaml result.yaml` |
| `-v` | 详细输出 | `-v` |

---

## 三、CPU 压力测试

### 3.1 基本 CPU 测试

```bash
# 使用所有 CPU 核心
stress-ng --cpu 0 -t 60s

# 指定核心数
stress-ng --cpu 4 -t 60s

# 指定 CPU 方法
stress-ng --cpu 4 --cpu-method matrixprod -t 60s

# 查看可用的 CPU 方法
stress-ng --cpu-method which
```

### 3.2 CPU 方法

| 方法 | 说明 |
|------|------|
| all | 所有方法 |
| ackermann | 阿克曼函数 |
| bitops | 位操作 |
| callfunc | 函数调用 |
| fft | 快速傅里叶变换 |
| fibonacci | 斐波那契 |
| matrixprod | 矩阵乘法 |
| prime | 素数计算 |
| queens | N 皇后问题 |
| tsc | 时间戳计数器 |

### 3.3 CPU 亲和性

```bash
# 绑定到特定 CPU
stress-ng --cpu 2 --taskset 0,1 -t 60s

# 使用 NUMA 节点
stress-ng --cpu 4 --numa 0 -t 60s
```

---

## 四、内存压力测试

### 4.1 基本内存测试

```bash
# 2 个 VM 工作进程
stress-ng --vm 2 -t 60s

# 指定每个工作进程使用的内存
stress-ng --vm 2 --vm-bytes 1G -t 60s

# 使用所有可用内存的百分比
stress-ng --vm 2 --vm-bytes 80% -t 60s
```

### 4.2 内存选项

| 选项 | 说明 |
|------|------|
| `--vm-bytes N` | 每个工作进程的内存大小 |
| `--vm-hang N` | 分配后挂起 N 秒 |
| `--vm-keep` | 保持内存分配 |
| `--vm-locked` | 使用 mlock 锁定内存 |
| `--vm-method` | 内存测试方法 |

### 4.3 内存方法

```bash
# 查看可用方法
stress-ng --vm-method which

# 常用方法
stress-ng --vm 2 --vm-bytes 1G --vm-method all -t 60s
stress-ng --vm 2 --vm-bytes 1G --vm-method rand-set -t 60s
stress-ng --vm 2 --vm-bytes 1G --vm-method swap -t 60s
```

---

## 五、IO 压力测试

### 5.1 磁盘 IO

```bash
# 磁盘写入压力
stress-ng --hdd 2 -t 60s

# 指定写入大小
stress-ng --hdd 2 --hdd-bytes 10G -t 60s

# 同步 IO
stress-ng --hdd 2 --hdd-opts sync -t 60s

# Direct IO
stress-ng --hdd 2 --hdd-opts direct -t 60s
```

### 5.2 IO 压力

```bash
# 通用 IO 压力
stress-ng --io 4 -t 60s

# 异步 IO
stress-ng --aio 4 -t 60s

# io_uring
stress-ng --io-uring 4 -t 60s
```

### 5.3 文件系统压力

```bash
# 文件系统操作
stress-ng --dentry 4 -t 60s     # 目录项
stress-ng --dir 4 -t 60s        # 目录操作
stress-ng --open 4 -t 60s       # 文件打开
stress-ng --rename 4 -t 60s     # 文件重命名
```

---

## 六、网络压力测试

### 6.1 Socket 压力

```bash
# TCP Socket
stress-ng --sock 4 -t 60s

# UDP Socket
stress-ng --udp 4 -t 60s

# Unix Socket
stress-ng --sockpair 4 -t 60s
```

### 6.2 网络选项

```bash
# 指定端口
stress-ng --sock 4 --sock-port 12345 -t 60s

# 多个连接
stress-ng --sock 4 --sock-ops 10000 -t 60s
```

---

## 七、综合测试

### 7.1 组合压力

```bash
# CPU + 内存
stress-ng --cpu 4 --vm 2 --vm-bytes 1G -t 60s

# CPU + 内存 + IO
stress-ng --cpu 4 --vm 2 --hdd 2 -t 60s

# 全面压力测试
stress-ng --cpu 4 --vm 2 --io 4 --hdd 2 --fork 4 -t 5m
```

### 7.2 典型场景

```bash
# 服务器烤机测试
stress-ng --cpu 0 --vm 4 --vm-bytes 2G --hdd 4 \
    --timeout 24h --metrics --yaml stress_report.yaml

# 内存泄漏检测环境
stress-ng --vm 2 --vm-bytes 90% --vm-keep -t 1h

# 系统调用压力
stress-ng --syscall 4 -t 60s
```

---

## 八、输出和统计

### 8.1 基本输出

```bash
$ stress-ng --cpu 4 -t 10s --metrics
stress-ng: info:  [1234] setting to a 10 second run per stressor
stress-ng: info:  [1234] dispatching hogs: 4 cpu
stress-ng: info:  [1234] successful run completed in 10.01s
stress-ng: info:  [1234] stressor       bogo ops real time  usr time  sys time   bogo ops/s     bogo ops/s
stress-ng: info:  [1234]                           (secs)    (secs)    (secs)   (real time) (usr+sys time)
stress-ng: info:  [1234] cpu              234567     10.00     39.92      0.08     23456.70        5871.47
```

### 8.2 YAML 输出

```bash
# 生成 YAML 报告
stress-ng --cpu 4 -t 60s --yaml stress.yaml

# 查看报告
cat stress.yaml
```

### 8.3 JSON 输出

```bash
# 生成 JSON 报告
stress-ng --cpu 4 -t 60s --json stress.json
```

---

## 九、实用脚本

### 9.1 系统稳定性测试

```bash
#!/bin/bash
# stability_test.sh

DURATION=${1:-3600}  # 默认 1 小时

echo "Starting stability test for ${DURATION}s..."

stress-ng \
    --cpu 0 \
    --vm 4 --vm-bytes 2G \
    --hdd 2 --hdd-bytes 10G \
    --io 4 \
    --timeout ${DURATION}s \
    --metrics \
    --yaml stability_report.yaml \
    --log-file stress.log

echo "Test completed. Report: stability_report.yaml"
```

### 9.2 渐进式压力测试

```bash
#!/bin/bash
# progressive_stress.sh

for load in 25 50 75 100; do
    echo "Testing at ${load}% load..."
    cpus=$(($(nproc) * load / 100))
    stress-ng --cpu $cpus -t 60s --metrics
    sleep 10
done
```

---

## 十、与同类工具对比

| 特性 | stress-ng | stress | sysbench | prime95 |
|------|-----------|--------|----------|---------|
| 压力源 | 300+ | 4 | 多种 | CPU |
| 可配置性 | 高 | 低 | 中 | 低 |
| 基准测试 | ✅ | ❌ | ✅ | ❌ |
| 验证功能 | ✅ | ❌ | ❌ | ✅ |
| 适用场景 | 通用 | 简单测试 | 数据库 | CPU |

---

## 十一、高频考点总结

| 考点 | 频率 | 关键知识 |
|------|------|----------|
| 基本用法 | ★★★ | --cpu、--vm、--hdd、-t |
| CPU 测试 | ★★☆ | --cpu-method、核心数 |
| 内存测试 | ★★☆ | --vm-bytes、--vm-method |
| IO 测试 | ★★☆ | --hdd、--io |
| 组合测试 | ★★☆ | 多种压力源组合 |

---

## 相关文章

- [上一篇：iostat IO统计深度解析](/articles/linux/linux-52-iostat-IO统计深度解析/)
- [性能分析与调试](/articles/linux/linux-08-性能分析与调试/)
