+++
title = "46. 缓存问题排查实战"
date = 2026-01-21
weight = 46000
description = "SRE缓存问题排查完整指南：Redis、Memcached连接问题、内存淘汰、主从同步、性能问题排查"
[taxonomies]
tags = ["SRE", "缓存", "Redis", "Memcached", "排查", "实战"]
+++

## 概述

缓存是提升系统性能的关键组件。本文详细介绍Redis、Memcached等缓存系统的常见问题排查方法。

---

# 一、Redis问题排查

## 1.1 Redis基础命令

### 连接与状态

```bash
# 连接Redis
redis-cli -h <host> -p <port> -a <password>

# 测试连接
redis-cli PING
# 返回 PONG 表示正常

# 查看服务器信息
redis-cli INFO

# INFO输出分段：
# Server     - 服务器信息
# Clients    - 客户端连接
# Memory     - 内存使用
# Persistence - 持久化状态
# Stats      - 统计信息
# Replication - 复制状态
# CPU        - CPU使用
# Keyspace   - 键空间统计

# 查看特定段
redis-cli INFO memory
redis-cli INFO replication
redis-cli INFO stats

# 查看配置
redis-cli CONFIG GET maxmemory
redis-cli CONFIG GET "*"

# 慢查询日志
redis-cli SLOWLOG GET 10
redis-cli SLOWLOG LEN
redis-cli SLOWLOG RESET
```

### 内存分析

```bash
# 内存概览
redis-cli INFO memory

# 关键指标：
# used_memory_human      - 已用内存（可读格式）
# used_memory_rss_human  - RSS内存（操作系统视角）
# used_memory_peak_human - 峰值内存
# maxmemory_human        - 最大内存限制
# mem_fragmentation_ratio - 内存碎片率（>1.5需要关注）

# 内存使用统计
redis-cli MEMORY STATS

# 查看单个Key的内存
redis-cli MEMORY USAGE key_name

# 查找大Key
redis-cli --bigkeys

# 输出示例：
# [00.00%] Biggest string found so far 'user:123' with 1024 bytes
# [00.00%] Biggest list   found so far 'queue:tasks' with 10000 items
# [00.00%] Biggest hash   found so far 'session:abc' with 50 fields

# 扫描大Key（更详细）
redis-cli --memkeys

# 分析RDB文件
redis-rdb-tools /path/to/dump.rdb -c memory --bytes 1024 -f memory.csv
```

### 键操作

```bash
# 键数量
redis-cli DBSIZE

# 查找键
redis-cli KEYS "user:*"    # 生产环境避免使用KEYS！

# 使用SCAN（推荐）
redis-cli SCAN 0 MATCH "user:*" COUNT 100

# 查看键类型
redis-cli TYPE key_name

# 查看键TTL
redis-cli TTL key_name
# -1 无过期时间
# -2 键不存在
# >0 剩余秒数

# 查看键编码
redis-cli OBJECT ENCODING key_name

# 删除键
redis-cli DEL key_name
redis-cli UNLINK key_name  # 异步删除（推荐大Key使用）
```

---

## 1.2 常见问题排查

### 问题1：连接失败

```bash
# 症状
redis-cli -h 192.168.1.100 PING
# Could not connect to Redis

# 排查步骤：

# 1. 检查Redis进程
ps aux | grep redis
systemctl status redis

# 2. 检查端口监听
ss -tlnp | grep 6379
netstat -tlnp | grep 6379

# 3. 检查绑定地址
redis-cli CONFIG GET bind
# 如果是127.0.0.1，只能本地连接

# 4. 检查防火墙
iptables -L -n | grep 6379
ufw status | grep 6379

# 5. 检查密码
redis-cli -a wrong_password PING
# NOAUTH Authentication required.

# 6. 检查最大连接数
redis-cli CONFIG GET maxclients
redis-cli INFO clients | grep connected_clients

# 7. 检查保护模式
redis-cli CONFIG GET protected-mode
# 如果是yes且没有密码，外部无法连接

# 解决方案：
# 修改配置 redis.conf
# bind 0.0.0.0
# protected-mode no
# requirepass your_password
```

### 问题2：内存不足

```bash
# 症状
# OOM command not allowed when used memory > 'maxmemory'

# 检查内存使用
redis-cli INFO memory | grep -E "used_memory|maxmemory"

# 检查内存策略
redis-cli CONFIG GET maxmemory-policy

# 策略说明：
# noeviction      - 不淘汰，写入报错
# volatile-lru    - 淘汰有TTL的键（LRU）
# volatile-ttl    - 淘汰TTL最短的
# volatile-random - 随机淘汰有TTL的
# allkeys-lru     - 淘汰所有键（LRU）
# allkeys-random  - 随机淘汰所有键
# allkeys-lfu     - 淘汰所有键（LFU）

# 解决方案：

# 1. 增加maxmemory
redis-cli CONFIG SET maxmemory 4gb

# 2. 修改淘汰策略
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 3. 清理不需要的键
redis-cli --scan --pattern "temp:*" | xargs redis-cli DEL

# 4. 找出大Key并处理
redis-cli --bigkeys

# 5. 设置键过期时间
redis-cli EXPIRE key_name 3600
```

### 问题3：性能问题

```bash
# 检查延迟
redis-cli --latency
# 持续测试延迟

redis-cli --latency-history
# 带历史记录

# 检查慢查询
redis-cli SLOWLOG GET 20

# 输出示例：
# 1) 1) (integer) 1              ← 日志ID
#    2) (integer) 1705831200     ← 时间戳
#    3) (integer) 15000          ← 耗时（微秒）
#    4) 1) "KEYS"                ← 命令
#       2) "*"
#    5) "192.168.1.100:12345"    ← 客户端

# 设置慢查询阈值（微秒）
redis-cli CONFIG SET slowlog-log-slower-than 10000

# 实时监控命令
redis-cli MONITOR
# 生产环境谨慎使用，会影响性能！

# 检查阻塞操作
redis-cli INFO stats | grep blocked

# 常见性能问题原因：

# 1. 使用了KEYS命令
#    解决：使用SCAN

# 2. 大Key操作
#    解决：拆分大Key、使用UNLINK

# 3. 持久化阻塞
redis-cli INFO persistence
#    检查rdb_last_bgsave_status、aof_last_write_status

# 4. 内存碎片
redis-cli INFO memory | grep mem_fragmentation_ratio
#    >1.5需要关注，可以重启或使用MEMORY PURGE

# 5. 网络问题
#    检查网络延迟
```

### 问题4：主从同步问题

```bash
# 检查复制状态
redis-cli INFO replication

# 主库输出：
# role:master
# connected_slaves:2
# slave0:ip=10.0.0.2,port=6379,state=online,offset=12345,lag=0
# slave1:ip=10.0.0.3,port=6379,state=online,offset=12345,lag=0
#
# 关键指标：
# connected_slaves - 连接的从库数
# state           - 状态（online/wait_bgsave）
# offset          - 复制偏移量
# lag             - 延迟（秒）

# 从库输出：
# role:slave
# master_host:10.0.0.1
# master_port:6379
# master_link_status:up          ← 连接状态
# master_last_io_seconds_ago:0   ← 最后通信时间
# master_sync_in_progress:0      ← 是否正在同步
# slave_repl_offset:12345        ← 复制偏移量

# 常见问题：

# 1. master_link_status:down
#    - 检查网络连接
#    - 检查主库状态
#    - 检查密码配置

# 2. 复制延迟大
#    - 检查网络带宽
#    - 检查主库写入量
redis-cli INFO stats | grep instantaneous_ops_per_sec

# 3. 全量同步频繁
#    - 增加repl-backlog-size
redis-cli CONFIG SET repl-backlog-size 256mb

# 重新建立复制
redis-cli SLAVEOF <master_host> <master_port>
redis-cli CONFIG SET masterauth <password>
```

### 问题5：持久化问题

```bash
# 检查持久化状态
redis-cli INFO persistence

# 关键指标：
# rdb_last_save_time     - 最后RDB保存时间
# rdb_last_bgsave_status - 最后BGSAVE状态
# rdb_last_bgsave_time_sec - 最后BGSAVE耗时
# aof_enabled            - AOF是否启用
# aof_last_write_status  - 最后AOF写入状态
# aof_last_rewrite_time_sec - 最后重写耗时

# RDB问题：

# 1. BGSAVE失败
#    检查磁盘空间
df -h
#    检查内存（fork需要）
free -h

# 2. 手动触发
redis-cli BGSAVE

# AOF问题：

# 1. AOF文件损坏
redis-check-aof --fix appendonly.aof

# 2. AOF文件过大
redis-cli BGREWRITEAOF

# 3. 检查AOF配置
redis-cli CONFIG GET appendfsync
# always   - 每次写入都同步
# everysec - 每秒同步（推荐）
# no       - 操作系统决定
```

---

## 1.3 Redis Cluster问题

```bash
# 集群状态
redis-cli -c CLUSTER INFO

# 关键指标：
# cluster_state:ok           ← 集群状态
# cluster_slots_assigned:16384
# cluster_slots_ok:16384
# cluster_slots_fail:0
# cluster_known_nodes:6

# 节点列表
redis-cli -c CLUSTER NODES

# 输出格式：
# <node_id> <ip:port> <flags> <master_id> <ping-sent> <pong-recv> <epoch> <link-state> <slot>
# flags说明：
# master   - 主节点
# slave    - 从节点
# fail     - 故障
# fail?    - 疑似故障

# 检查槽分配
redis-cli -c CLUSTER SLOTS

# 常见问题：

# 1. cluster_state:fail
#    - 有节点故障
#    - 有槽未分配
redis-cli -c CLUSTER NODES | grep fail

# 2. 重新分片
redis-cli --cluster reshard <host>:<port>

# 3. 修复集群
redis-cli --cluster fix <host>:<port>

# 4. 添加节点
redis-cli --cluster add-node <new_host>:<port> <existing_host>:<port>

# 5. 故障转移
redis-cli -c CLUSTER FAILOVER
```

---

# 二、Memcached问题排查

## 2.1 Memcached基础命令

```bash
# 连接Memcached
telnet localhost 11211
# 或
nc localhost 11211

# 查看状态
echo "stats" | nc localhost 11211

# 关键指标：
# curr_connections   - 当前连接数
# total_connections  - 总连接数
# cmd_get            - GET命令数
# cmd_set            - SET命令数
# get_hits           - 命中次数
# get_misses         - 未命中次数
# bytes              - 已用内存
# limit_maxbytes     - 最大内存
# evictions          - 淘汰次数
# curr_items         - 当前项目数

# 计算命中率
# hit_rate = get_hits / (get_hits + get_misses) * 100%

# 查看slab统计
echo "stats slabs" | nc localhost 11211

# 查看items统计
echo "stats items" | nc localhost 11211

# 查看所有设置
echo "stats settings" | nc localhost 11211
```

## 2.2 常见问题

### 连接问题

```bash
# 检查进程
ps aux | grep memcached

# 检查端口
ss -tlnp | grep 11211

# 检查连接数
echo "stats" | nc localhost 11211 | grep curr_connections

# 检查最大连接
echo "stats settings" | nc localhost 11211 | grep maxconns

# 连接数过多时
# 修改启动参数 -c <max_connections>
```

### 内存问题

```bash
# 检查内存使用
echo "stats" | nc localhost 11211 | grep -E "bytes|limit_maxbytes|evictions"

# 计算使用率
# usage = bytes / limit_maxbytes * 100%

# evictions过多说明内存不足

# 解决方案：
# 1. 增加内存限制
#    启动参数 -m <megabytes>
# 2. 优化存储的数据大小
# 3. 设置合理的过期时间
```

### 性能问题

```bash
# 检查命中率
echo "stats" | nc localhost 11211 | grep -E "get_hits|get_misses"

# 命中率低的原因：
# 1. 过期时间太短
# 2. 内存太小导致淘汰
# 3. Key设计不合理

# 检查slab分配
echo "stats slabs" | nc localhost 11211

# slab chunk浪费问题
# 使用memcached-tool分析
memcached-tool localhost:11211 display
```

---

# 三、缓存架构问题

## 3.1 缓存穿透

```
问题：查询不存在的数据，请求直接到数据库

特征：
- 大量请求查询不存在的Key
- 数据库压力增大

解决方案：
1. 布隆过滤器
   - 在缓存前加布隆过滤器
   - 过滤掉不存在的Key

2. 缓存空值
   - 不存在的Key也缓存（短TTL）
   SET key "" EX 60

3. 参数校验
   - 过滤明显非法的请求
```

## 3.2 缓存击穿

```
问题：热点Key过期瞬间，大量请求打到数据库

特征：
- 某个热点Key突然失效
- 瞬时数据库压力飙升

解决方案：
1. 互斥锁
   - 只允许一个请求重建缓存
   SETNX lock:key 1 EX 10

2. 逻辑过期
   - Key永不过期，存储逻辑过期时间
   - 异步更新缓存

3. 热点数据永不过期
   - 通过后台任务更新
```

## 3.3 缓存雪崩

```
问题：大量Key同时过期或缓存服务宕机

特征：
- 大量请求直接打到数据库
- 可能导致数据库宕机

解决方案：
1. 过期时间随机化
   TTL = base_ttl + random(0, 300)

2. 多级缓存
   本地缓存 → 分布式缓存 → 数据库

3. 缓存高可用
   - Redis Cluster
   - Redis Sentinel

4. 限流降级
   - 限制数据库请求量
   - 返回降级响应
```

---

## 3.4 缓存诊断脚本

```bash
#!/bin/bash
# cache_diagnose.sh - 缓存诊断脚本

CACHE_TYPE=$1
HOST=${2:-localhost}
PORT=${3:-6379}

case $CACHE_TYPE in
    redis)
        echo "===== Redis诊断 ====="
        echo ""
        
        echo "--- 1. 连接测试 ---"
        redis-cli -h $HOST -p $PORT PING
        echo ""
        
        echo "--- 2. 内存状态 ---"
        redis-cli -h $HOST -p $PORT INFO memory | grep -E "used_memory_human|maxmemory_human|mem_fragmentation"
        echo ""
        
        echo "--- 3. 连接状态 ---"
        redis-cli -h $HOST -p $PORT INFO clients | grep -E "connected_clients|blocked_clients"
        echo ""
        
        echo "--- 4. 复制状态 ---"
        redis-cli -h $HOST -p $PORT INFO replication | head -10
        echo ""
        
        echo "--- 5. 慢查询 ---"
        redis-cli -h $HOST -p $PORT SLOWLOG GET 5
        echo ""
        
        echo "--- 6. 键统计 ---"
        redis-cli -h $HOST -p $PORT INFO keyspace
        echo ""
        
        echo "--- 7. 命令统计 ---"
        redis-cli -h $HOST -p $PORT INFO stats | grep -E "instantaneous_ops|total_commands"
        echo ""
        ;;
        
    memcached)
        PORT=${3:-11211}
        echo "===== Memcached诊断 ====="
        echo ""
        
        echo "--- 1. 连接测试 ---"
        echo "version" | nc -q1 $HOST $PORT
        echo ""
        
        echo "--- 2. 基本状态 ---"
        echo "stats" | nc -q1 $HOST $PORT | grep -E "curr_connections|bytes|limit_maxbytes|curr_items|evictions"
        echo ""
        
        echo "--- 3. 命中率 ---"
        stats=$(echo "stats" | nc -q1 $HOST $PORT)
        hits=$(echo "$stats" | grep "get_hits" | awk '{print $3}')
        misses=$(echo "$stats" | grep "get_misses" | awk '{print $3}')
        if [ -n "$hits" ] && [ -n "$misses" ]; then
            total=$((hits + misses))
            if [ $total -gt 0 ]; then
                rate=$(echo "scale=2; $hits * 100 / $total" | bc)
                echo "Hit Rate: $rate%"
            fi
        fi
        echo ""
        ;;
        
    *)
        echo "Usage: $0 <redis|memcached> [host] [port]"
        exit 1
        ;;
esac

echo "===== 诊断完成 ====="
```

---

## 总结

### Redis命令速查

| 任务 | 命令 |
|------|------|
| 连接测试 | `redis-cli PING` |
| 内存状态 | `INFO memory` |
| 复制状态 | `INFO replication` |
| 慢查询 | `SLOWLOG GET 10` |
| 大Key | `--bigkeys` |
| 延迟测试 | `--latency` |
| 集群状态 | `CLUSTER INFO` |

### Memcached速查

| 任务 | 命令 |
|------|------|
| 状态查看 | `stats` |
| 详细统计 | `stats slabs` |
| 项目统计 | `stats items` |
| 刷新缓存 | `flush_all` |

### 缓存问题排查三板斧

1. **查连接** - 连接数、连接状态
2. **查内存** - 使用率、淘汰数、碎片率
3. **查性能** - 命中率、慢查询、延迟

### 关键指标阈值

| 指标 | 警告阈值 | 说明 |
|------|----------|------|
| 内存使用率 | >80% | 可能触发淘汰 |
| 内存碎片率 | >1.5 | 考虑重启或MEMORY PURGE |
| 命中率 | <90% | 检查缓存策略 |
| 复制延迟 | >1s | 检查网络和负载 |
| 慢查询 | >10ms | 优化命令 |

**关键记忆**：
1. 避免使用KEYS命令，用SCAN
2. 大Key用UNLINK异步删除
3. 碎片率>1.5需要关注
4. master_link_status:down是复制故障

---

## 相关文章

- [上一篇：消息队列问题排查实战](@/articles/sre/sre-45-消息队列问题排查实战.md)
- [下一篇：备份恢复实战](@/articles/sre/sre-47-备份恢复实战.md)
