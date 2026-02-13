+++
title = "压力测试实战指南"
date = 2026-01-21
weight = 26000
description = "SRE压力测试完整指南：HTTP压测、数据库压测、系统基准测试，工具使用与结果分析"
[taxonomies]
tags = ["SRE", "压力测试", "性能", "实战", "wrk", "ab", "sysbench"]
+++

## 概述

压力测试是SRE评估系统容量、发现性能瓶颈的核心手段。本文详细介绍各类压测场景、工具使用和结果分析方法。

---

# 一、HTTP服务压力测试

## 1.1 测试前准备

### 场景确认清单

```
□ 目标明确：测试QPS上限？延迟分布？并发能力？
□ 环境隔离：测试环境与生产隔离
□ 基准数据：记录当前系统指标作为对比
□ 监控就绪：确保能观察CPU/内存/网络/应用指标
□ 回滚方案：压测导致问题时如何恢复
```

### 被测服务信息收集

```bash
# 确认目标服务状态
curl -I http://target:8080/api/health

# 确认网络延迟
ping -c 10 target

# 确认带宽（iperf3需提前安装）
iperf3 -c target -t 10
```

---

## 1.2 wrk - 高性能HTTP压测工具

### 安装

```bash
# Ubuntu/Debian
sudo apt install wrk

# CentOS/RHEL
sudo yum install wrk

# macOS
brew install wrk

# 从源码编译
git clone https://github.com/wg/wrk.git
cd wrk && make
```

### 基础用法

```bash
# 基本压测：12线程，400并发连接，持续30秒
wrk -t12 -c400 -d30s http://localhost:8080/api/users

# 输出示例：
# Running 30s test @ http://localhost:8080/api/users
#   12 threads and 400 connections
#   Thread Stats   Avg      Stdev     Max   +/- Stdev
#     Latency    45.23ms   12.35ms 234.12ms   78.23%
#     Req/Sec     8.92k     1.23k   12.34k    72.15%
#   3201234 requests in 30.00s, 1.23GB read
# Requests/sec: 106707.80
# Transfer/sec:     42.01MB
```

### 结果解读

| 指标 | 含义 | 关注点 |
|------|------|--------|
| Latency Avg | 平均延迟 | 越低越好 |
| Latency Max | 最大延迟 | 反映尾延迟 |
| Latency Stdev | 延迟标准差 | 越小越稳定 |
| Req/Sec | 每线程每秒请求数 | 乘以线程数=总QPS |
| +/- Stdev | 落在一个标准差内的比例 | 越高越稳定 |

### 高级用法：Lua脚本

**POST请求压测**：

```lua
-- post.lua
wrk.method = "POST"
wrk.body   = '{"username": "test", "password": "123456"}'
wrk.headers["Content-Type"] = "application/json"
```

```bash
wrk -t12 -c400 -d30s -s post.lua http://localhost:8080/api/login
```

**动态参数**：

```lua
-- dynamic.lua
counter = 0

request = function()
    counter = counter + 1
    local path = "/api/users/" .. (counter % 10000)
    return wrk.format("GET", path)
end
```

**延迟分布统计**：

```lua
-- latency.lua
done = function(summary, latency, requests)
    io.write("------------------------------\n")
    io.write("Latency Distribution:\n")
    for _, p in pairs({ 50, 75, 90, 99, 99.9 }) do
        n = latency:percentile(p)
        io.write(string.format("%g%%: %.2fms\n", p, n/1000))
    end
end
```

```bash
wrk -t12 -c400 -d30s -s latency.lua http://localhost:8080/api/users
```

### 压测参数选择策略

```bash
# 阶梯式压测：逐步增加并发，观察拐点
for c in 100 200 400 800 1600; do
    echo "=== Connections: $c ==="
    wrk -t12 -c$c -d30s http://localhost:8080/api/users
    sleep 10  # 冷却时间
done
```

---

## 1.3 ab (Apache Bench) - 简单快速

### 基础用法

```bash
# 10000个请求，100并发
ab -n 10000 -c 100 http://localhost:8080/api/users

# 带Keep-Alive
ab -n 10000 -c 100 -k http://localhost:8080/api/users

# POST请求
ab -n 10000 -c 100 -p data.json -T application/json http://localhost:8080/api/login
```

### 结果关键指标

```
Requests per second:    5678.90 [#/sec] (mean)
Time per request:       17.609 [ms] (mean)
Time per request:       0.176 [ms] (mean, across all concurrent requests)

Percentage of the requests served within a certain time (ms)
  50%     15
  66%     18
  75%     20
  90%     28
  95%     35
  99%     52
 100%    234 (longest request)
```

---

## 1.4 hey - 现代HTTP压测工具

### 安装与使用

```bash
# 安装
go install github.com/rakyll/hey@latest

# 基本用法
hey -n 10000 -c 100 http://localhost:8080/api/users

# 指定QPS上限（限流压测）
hey -n 10000 -c 100 -q 1000 http://localhost:8080/api/users

# 持续时间模式
hey -z 30s -c 100 http://localhost:8080/api/users
```

### 优势

- 原生支持HTTP/2
- 输出延迟直方图
- Go编写，单文件部署

---

## 1.5 vegeta - 可编程压测

### 安装与使用

```bash
# 安装
go install github.com/tsenart/vegeta@latest

# 定义目标
echo "GET http://localhost:8080/api/users" | vegeta attack -rate=1000 -duration=30s | vegeta report

# 多目标
cat << EOF > targets.txt
GET http://localhost:8080/api/users
GET http://localhost:8080/api/orders
POST http://localhost:8080/api/login
Content-Type: application/json
@login.json
EOF

vegeta attack -targets=targets.txt -rate=500 -duration=60s | vegeta report
```

### 生成HTML报告

```bash
vegeta attack -rate=1000 -duration=30s | tee results.bin | vegeta report
vegeta plot results.bin > report.html
```

---

# 二、数据库压力测试

## 2.1 sysbench - 通用基准测试

### 安装

```bash
# Ubuntu/Debian
sudo apt install sysbench

# CentOS/RHEL
sudo yum install sysbench
```

### MySQL压测

**准备测试数据**：

```bash
sysbench oltp_read_write \
    --db-driver=mysql \
    --mysql-host=localhost \
    --mysql-user=root \
    --mysql-password=password \
    --mysql-db=test \
    --tables=10 \
    --table-size=1000000 \
    prepare
```

**执行测试**：

```bash
# 读写混合测试
sysbench oltp_read_write \
    --db-driver=mysql \
    --mysql-host=localhost \
    --mysql-user=root \
    --mysql-password=password \
    --mysql-db=test \
    --tables=10 \
    --table-size=1000000 \
    --threads=16 \
    --time=60 \
    --report-interval=10 \
    run

# 纯读测试
sysbench oltp_read_only \
    --db-driver=mysql \
    --mysql-host=localhost \
    --mysql-user=root \
    --mysql-password=password \
    --mysql-db=test \
    --tables=10 \
    --threads=32 \
    --time=60 \
    run

# 纯写测试
sysbench oltp_write_only \
    --db-driver=mysql \
    --mysql-host=localhost \
    --mysql-user=root \
    --mysql-password=password \
    --mysql-db=test \
    --tables=10 \
    --threads=16 \
    --time=60 \
    run
```

**结果解读**：

```
SQL statistics:
    queries performed:
        read:                            1234567
        write:                           345678
        other:                           123456
        total:                           1703701
    transactions:                        85185  (1419.75 per sec.)
    queries:                             1703701 (28395.01 per sec.)
    ignored errors:                      0      (0.00 per sec.)
    reconnects:                          0      (0.00 per sec.)

Latency (ms):
         min:                                  2.34
         avg:                                 11.27
         max:                                234.56
         95th percentile:                     23.45
```

### 清理数据

```bash
sysbench oltp_read_write \
    --db-driver=mysql \
    --mysql-host=localhost \
    --mysql-user=root \
    --mysql-password=password \
    --mysql-db=test \
    --tables=10 \
    cleanup
```

---

## 2.2 pgbench - PostgreSQL压测

```bash
# 初始化测试数据（scale factor 100 = 约1.5GB数据）
pgbench -i -s 100 -h localhost -U postgres testdb

# 执行测试：10客户端，2线程，60秒
pgbench -c 10 -j 2 -T 60 -h localhost -U postgres testdb

# 只读测试
pgbench -c 10 -j 2 -T 60 -S -h localhost -U postgres testdb

# 自定义SQL脚本
cat << EOF > custom.sql
\set aid random(1, 100000 * :scale)
SELECT abalance FROM pgbench_accounts WHERE aid = :aid;
EOF
pgbench -c 10 -j 2 -T 60 -f custom.sql -h localhost -U postgres testdb
```

---

## 2.3 Redis压测

```bash
# 使用redis-benchmark
redis-benchmark -h localhost -p 6379 -c 100 -n 100000

# 指定命令
redis-benchmark -h localhost -p 6379 -c 100 -n 100000 -t get,set

# 指定数据大小
redis-benchmark -h localhost -p 6379 -c 100 -n 100000 -d 1024

# Pipeline模式
redis-benchmark -h localhost -p 6379 -c 100 -n 100000 -P 16
```

---

# 三、系统基准测试

## 3.1 CPU测试

```bash
# sysbench CPU测试
sysbench cpu --cpu-max-prime=20000 --threads=4 run

# stress-ng（更全面）
sudo apt install stress-ng
stress-ng --cpu 4 --timeout 60s --metrics-brief

# 特定CPU指令测试
stress-ng --cpu 4 --cpu-method matrixprod --timeout 60s
```

---

## 3.2 内存测试

```bash
# sysbench内存测试
sysbench memory --memory-block-size=1K --memory-total-size=10G --threads=4 run

# 大块内存测试
sysbench memory --memory-block-size=1M --memory-total-size=10G --threads=4 run

# stress-ng内存测试
stress-ng --vm 2 --vm-bytes 1G --timeout 60s --metrics-brief
```

---

## 3.3 磁盘IO测试

### fio - 专业IO测试

```bash
# 安装
sudo apt install fio

# 顺序写测试
fio --name=seq_write --ioengine=libaio --rw=write --bs=1M \
    --size=4G --numjobs=4 --runtime=60 --direct=1 \
    --filename=/data/testfile --group_reporting

# 顺序读测试
fio --name=seq_read --ioengine=libaio --rw=read --bs=1M \
    --size=4G --numjobs=4 --runtime=60 --direct=1 \
    --filename=/data/testfile --group_reporting

# 随机读写混合（模拟数据库）
fio --name=randrw --ioengine=libaio --rw=randrw --bs=4K \
    --size=4G --numjobs=8 --runtime=60 --direct=1 \
    --rwmixread=70 --filename=/data/testfile --group_reporting

# 4K随机读（IOPS测试）
fio --name=rand_read --ioengine=libaio --rw=randread --bs=4K \
    --size=4G --numjobs=16 --runtime=60 --direct=1 \
    --iodepth=64 --filename=/data/testfile --group_reporting
```

**结果关键指标**：

```
read: IOPS=45678, BW=178MiB/s
lat (usec): min=45, max=12345, avg=350.23, stdev=123.45
    clat percentiles (usec):
     |  1.00th=[  123],  5.00th=[  156], 10.00th=[  178],
     | 20.00th=[  212], 30.00th=[  245], 40.00th=[  278],
     | 50.00th=[  314], 60.00th=[  359], 70.00th=[  412],
     | 80.00th=[  482], 90.00th=[  594], 95.00th=[  717],
     | 99.00th=[ 1090], 99.50th=[ 1352], 99.90th=[ 2311],
```

---

## 3.4 网络测试

```bash
# iperf3 - 带宽测试
# 服务端
iperf3 -s

# 客户端
iperf3 -c server_ip -t 30

# 双向测试
iperf3 -c server_ip -t 30 -d

# UDP测试
iperf3 -c server_ip -u -b 1G -t 30

# 多流测试
iperf3 -c server_ip -P 4 -t 30
```

---

# 四、压测结果分析与调优

## 4.1 识别瓶颈

### 压测时监控命令

```bash
# 开启多个终端，同时观察

# 终端1：整体资源
top -d 1

# 终端2：IO
iostat -xz 1

# 终端3：网络
sar -n DEV 1

# 终端4：应用日志
tail -f /var/log/app/app.log

# 终端5：连接数
watch -n 1 'ss -s'
```

### 瓶颈判断表

| 现象 | 可能瓶颈 | 验证方法 |
|------|----------|----------|
| QPS不增长，CPU未满 | 应用锁/等待 | 查看应用线程状态 |
| QPS不增长，CPU满 | CPU瓶颈 | 增加CPU或优化代码 |
| 延迟高，IO util高 | 磁盘IO | 优化查询或加缓存 |
| 延迟高，网络丢包 | 网络瓶颈 | 检查带宽和MTU |
| QPS不增长，连接数满 | 连接池耗尽 | 增加连接池或优化 |

---

## 4.2 压测报告模板

```markdown
# 压力测试报告

## 测试概述
- 测试目标：评估API服务在高并发下的性能表现
- 测试时间：2026-01-21 14:00-16:00
- 测试环境：4C8G云服务器 x 3

## 测试结果摘要

| 场景 | 并发 | QPS | 平均延迟 | P99延迟 | 错误率 |
|------|------|-----|----------|---------|--------|
| 读取用户 | 100 | 5,234 | 19ms | 45ms | 0% |
| 读取用户 | 400 | 12,456 | 32ms | 89ms | 0.1% |
| 读取用户 | 800 | 15,678 | 51ms | 156ms | 0.5% |
| 创建订单 | 100 | 1,234 | 81ms | 234ms | 0% |

## 资源使用情况

| 指标 | 空闲时 | 100并发 | 400并发 | 800并发 |
|------|--------|---------|---------|---------|
| CPU | 5% | 35% | 72% | 95% |
| 内存 | 2GB | 3.2GB | 4.1GB | 5.5GB |
| 网络出 | 1Mbps | 45Mbps | 120Mbps | 180Mbps |

## 瓶颈分析
1. 800并发时CPU接近饱和，成为主要瓶颈
2. 数据库连接池在高并发时出现等待

## 优化建议
1. 增加应用服务器节点
2. 数据库连接池从50增加到100
3. 热点查询添加Redis缓存
```

---

## 4.3 常见问题排查

### 压测端问题

```bash
# 问题：Too many open files
ulimit -n 65535

# 问题：端口耗尽
sysctl -w net.ipv4.ip_local_port_range="1024 65535"
sysctl -w net.ipv4.tcp_tw_reuse=1

# 问题：压测机CPU满
# 使用分布式压测或更强机器
```

### 被测端问题

```bash
# 连接数限制
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# 文件描述符限制
# /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535

# 应用连接池配置
# 确保连接池大小 >= 压测并发数
```

---

## 4.4 自动化压测脚本

```bash
#!/bin/bash
# auto_benchmark.sh - 自动化压测脚本

set -e

# 配置
TARGET_URL="${1:-http://localhost:8080/api/health}"
DURATION="${2:-30s}"
OUTPUT_DIR="benchmark_$(date +%Y%m%d_%H%M%S)"

# 并发梯度
CONNECTIONS=(10 50 100 200 400 800)

echo "===== 自动化压测 ====="
echo "目标: $TARGET_URL"
echo "持续时间: $DURATION"
echo "输出目录: $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"

# 检查工具
check_tools() {
    for tool in wrk curl; do
        if ! command -v $tool &> /dev/null; then
            echo "错误: $tool 未安装"
            exit 1
        fi
    done
}

# 预热
warmup() {
    echo "--- 预热测试 ---"
    curl -s -o /dev/null -w "状态码: %{http_code}, 耗时: %{time_total}s\n" "$TARGET_URL"
    wrk -t2 -c10 -d5s "$TARGET_URL" > /dev/null 2>&1
    echo "预热完成"
    echo ""
}

# 运行测试
run_test() {
    local conn=$1
    echo "--- 并发: $conn ---"
    
    # 计算线程数（不超过CPU核数和连接数）
    local threads=$(( conn < $(nproc) ? conn : $(nproc) ))
    threads=$(( threads < 1 ? 1 : threads ))
    
    # 运行wrk
    wrk -t$threads -c$conn -d$DURATION --latency "$TARGET_URL" | tee "$OUTPUT_DIR/wrk_c${conn}.txt"
    
    echo ""
    sleep 5  # 冷却
}

# 生成报告
generate_report() {
    echo "--- 生成汇总报告 ---"
    
    REPORT="$OUTPUT_DIR/summary.txt"
    echo "压测汇总报告" > "$REPORT"
    echo "目标: $TARGET_URL" >> "$REPORT"
    echo "时间: $(date)" >> "$REPORT"
    echo "" >> "$REPORT"
    echo "并发数 | QPS | 平均延迟 | P99延迟" >> "$REPORT"
    echo "-------|-----|----------|--------" >> "$REPORT"
    
    for conn in "${CONNECTIONS[@]}"; do
        if [ -f "$OUTPUT_DIR/wrk_c${conn}.txt" ]; then
            QPS=$(grep "Requests/sec:" "$OUTPUT_DIR/wrk_c${conn}.txt" | awk '{print $2}')
            AVG_LAT=$(grep "Latency" "$OUTPUT_DIR/wrk_c${conn}.txt" | head -1 | awk '{print $2}')
            P99_LAT=$(grep "99%" "$OUTPUT_DIR/wrk_c${conn}.txt" | awk '{print $2}')
            echo "$conn | $QPS | $AVG_LAT | $P99_LAT" >> "$REPORT"
        fi
    done
    
    cat "$REPORT"
}

# 主流程
check_tools
warmup

for conn in "${CONNECTIONS[@]}"; do
    run_test $conn
done

generate_report

echo ""
echo "===== 压测完成 ====="
echo "详细结果: $OUTPUT_DIR/"
```

```bash
#!/bin/bash
# monitor_during_test.sh - 压测期间监控脚本

# 在另一个终端运行此脚本监控系统状态

INTERVAL=5
LOG_FILE="system_monitor_$(date +%Y%m%d_%H%M%S).log"

echo "开始监控，日志: $LOG_FILE"
echo "按 Ctrl+C 停止"

echo "时间,CPU%,MEM%,LOAD,CONN,DISK_IO" > "$LOG_FILE"

while true; do
    TIMESTAMP=$(date '+%H:%M:%S')
    
    # CPU使用率
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print 100-$8}')
    
    # 内存使用率
    MEM=$(free | grep Mem | awk '{print $3/$2 * 100}')
    
    # 负载
    LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk -F, '{print $1}' | tr -d ' ')
    
    # 连接数
    CONN=$(ss -ant | grep ESTAB | wc -l)
    
    # 磁盘IO
    DISK_IO=$(iostat -d 1 2 | tail -n +4 | head -1 | awk '{print $2}')
    
    echo "$TIMESTAMP,$CPU,$MEM,$LOAD,$CONN,$DISK_IO" >> "$LOG_FILE"
    
    # 实时显示
    printf "\r%s CPU:%.1f%% MEM:%.1f%% LOAD:%s CONN:%d" "$TIMESTAMP" "$CPU" "$MEM" "$LOAD" "$CONN"
    
    sleep $INTERVAL
done
```

---

## 总结

| 工具 | 适用场景 | 优势 |
|------|----------|------|
| wrk | HTTP压测 | 高性能，Lua脚本扩展 |
| ab | 快速HTTP测试 | 简单易用 |
| hey | 现代HTTP压测 | HTTP/2支持 |
| vegeta | 可编程压测 | 灵活，报告丰富 |
| sysbench | 数据库/系统 | 全面，标准化 |
| fio | 磁盘IO | 专业，参数丰富 |
| iperf3 | 网络带宽 | 准确可靠 |

**压测原则**：
1. 先小规模验证，再逐步加压
2. 记录每次测试的环境和参数
3. 同时监控客户端和服务端
4. 关注尾延迟（P99/P999），不只看平均值
5. 压测结束后清理测试数据

---

## 相关文章

- [上一篇：SRE笔试题-低延迟系统与C++](@/articles/sre/sre-25-SRE笔试题-低延迟系统与C++.md)
- [下一篇：网络问题排查实战](@/articles/sre/sre-27-网络问题排查实战.md)
