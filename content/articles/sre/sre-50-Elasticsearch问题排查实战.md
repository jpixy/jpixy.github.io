+++
title = "50.Elasticsearch问题排查实战"
date = 2026-01-21
description = "SRE Elasticsearch问题排查完整指南：集群健康、分片问题、索引性能、查询优化"
[taxonomies]
tags = ["SRE", "Elasticsearch", "搜索", "排查", "实战"]
+++

## 概述

Elasticsearch是分布式搜索和分析引擎，问题排查需要理解其分布式特性。本文详细介绍ES集群的常见问题排查方法。

---

# 一、集群健康检查

## 1.1 集群状态

### 基础健康检查

```bash
# 集群健康状态
curl -X GET "localhost:9200/_cluster/health?pretty"

# 输出示例：
# {
#   "cluster_name": "my-cluster",
#   "status": "green",              ← 集群状态（关键！）
#   "timed_out": false,
#   "number_of_nodes": 3,           ← 节点数
#   "number_of_data_nodes": 3,      ← 数据节点数
#   "active_primary_shards": 10,    ← 活跃主分片
#   "active_shards": 20,            ← 活跃分片总数
#   "relocating_shards": 0,         ← 迁移中的分片
#   "initializing_shards": 0,       ← 初始化中的分片
#   "unassigned_shards": 0,         ← 未分配的分片（重要！）
#   "delayed_unassigned_shards": 0,
#   "number_of_pending_tasks": 0,
#   "active_shards_percent_as_number": 100.0
# }

# 状态说明：
# green  - 所有分片都已分配
# yellow - 主分片已分配，部分副本未分配
# red    - 部分主分片未分配（数据可能丢失）

# 等待集群达到特定状态
curl -X GET "localhost:9200/_cluster/health?wait_for_status=yellow&timeout=50s"

# 查看各索引健康状态
curl -X GET "localhost:9200/_cluster/health?level=indices&pretty"

# 查看各分片健康状态
curl -X GET "localhost:9200/_cluster/health?level=shards&pretty"
```

### 节点信息

```bash
# 查看所有节点
curl -X GET "localhost:9200/_cat/nodes?v"

# 输出列说明：
# ip           节点IP
# heap.percent 堆内存使用率
# ram.percent  系统内存使用率
# cpu          CPU使用率
# load_1m      1分钟负载
# node.role    节点角色（m=master, d=data, i=ingest）
# master       是否是当前master（*表示是）
# name         节点名称

# 详细节点信息
curl -X GET "localhost:9200/_nodes?pretty"

# 节点统计
curl -X GET "localhost:9200/_nodes/stats?pretty"

# 特定节点统计
curl -X GET "localhost:9200/_nodes/node-1/stats?pretty"

# 只看JVM统计
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty"

# 只看线程池统计
curl -X GET "localhost:9200/_nodes/stats/thread_pool?pretty"
```

---

## 1.2 常见集群问题

### 问题1：集群状态Red

```bash
# 查找未分配的分片
curl -X GET "localhost:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason" | grep UNASSIGNED

# 输出示例：
# my-index 0 p UNASSIGNED NODE_LEFT
# my-index 0 r UNASSIGNED REPLICA_ADDED

# 查看未分配原因详情
curl -X GET "localhost:9200/_cluster/allocation/explain?pretty"

# 常见未分配原因：
# NODE_LEFT           - 节点离开集群
# CLUSTER_RECOVERED   - 集群恢复中
# INDEX_CREATED       - 新建索引
# ALLOCATION_FAILED   - 分配失败
# REPLICA_ADDED       - 添加副本
# REROUTE_CANCELLED   - 重路由取消
# PRIMARY_FAILED      - 主分片失败
# FORCED_EMPTY_PRIMARY - 强制空主分片

# 解决方案：

# 1. 如果是节点临时离开，等待节点恢复
# 检查节点状态
curl -X GET "localhost:9200/_cat/nodes?v"

# 2. 如果节点永久丢失，需要手动处理

# 对于副本分片，可以等待或手动分配
curl -X POST "localhost:9200/_cluster/reroute?retry_failed=true"

# 对于主分片丢失（数据丢失风险），可以分配空主分片
curl -X POST "localhost:9200/_cluster/reroute" -H 'Content-Type: application/json' -d'
{
  "commands": [{
    "allocate_empty_primary": {
      "index": "my-index",
      "shard": 0,
      "node": "node-1",
      "accept_data_loss": true
    }
  }]
}'

# 3. 磁盘空间不足导致的分配失败
# 检查磁盘使用
curl -X GET "localhost:9200/_cat/allocation?v"

# 调整磁盘水位线
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.disk.watermark.low": "85%",
    "cluster.routing.allocation.disk.watermark.high": "90%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "95%"
  }
}'
```

### 问题2：集群状态Yellow

```bash
# Yellow通常是副本未分配

# 检查原因
curl -X GET "localhost:9200/_cluster/allocation/explain?pretty" -H 'Content-Type: application/json' -d'
{
  "index": "my-index",
  "shard": 0,
  "primary": false
}'

# 常见原因：
# 1. 节点数少于副本数+1
#    解决：增加节点或减少副本数
curl -X PUT "localhost:9200/my-index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.number_of_replicas": 0
}'

# 2. 分片分配规则限制
#    检查分配设置
curl -X GET "localhost:9200/_cluster/settings?include_defaults=true&pretty" | grep allocation

# 3. 节点属性不匹配
#    检查索引的分配要求
curl -X GET "localhost:9200/my-index/_settings?pretty" | grep routing
```

### 问题3：节点离开集群

```bash
# 检查离开的节点
curl -X GET "localhost:9200/_cat/nodes?v"

# 查看集群日志
tail -f /var/log/elasticsearch/my-cluster.log

# 常见原因：

# 1. JVM OOM
grep -i "out of memory\|heap" /var/log/elasticsearch/*.log

# 2. 网络问题
# 检查节点间连通性
ping other-node
nc -zv other-node 9300

# 3. GC停顿过长
grep -i "gc" /var/log/elasticsearch/*.log | grep -i "old\|pause"

# 4. 磁盘满
df -h

# 检查节点设置
curl -X GET "localhost:9200/_nodes/settings?pretty"

# 恢复节点后，重新加入集群
# 通常自动完成，检查状态即可
```

---

## 1.3 Master节点问题

```bash
# 查看当前Master
curl -X GET "localhost:9200/_cat/master?v"

# 查看Master候选节点
curl -X GET "localhost:9200/_cat/nodes?v&h=name,node.role" | grep m

# Master选举问题排查

# 1. 检查minimum_master_nodes设置（7.x之前）
# 应该设置为 (master候选节点数 / 2) + 1

# 2. 检查discovery设置
curl -X GET "localhost:9200/_nodes/settings?pretty" | grep -A5 discovery

# 3. 查看pending tasks
curl -X GET "localhost:9200/_cluster/pending_tasks?pretty"
# 大量pending tasks表示Master压力大

# 4. 检查Master日志
grep -i "master\|election" /var/log/elasticsearch/*.log
```

---

# 二、分片问题排查

## 2.1 分片状态检查

```bash
# 查看所有分片
curl -X GET "localhost:9200/_cat/shards?v"

# 输出列：
# index   索引名
# shard   分片号
# prirep  p=主分片, r=副本分片
# state   状态（STARTED/INITIALIZING/RELOCATING/UNASSIGNED）
# docs    文档数
# store   存储大小
# ip      所在节点IP
# node    所在节点名

# 只看特定索引的分片
curl -X GET "localhost:9200/_cat/shards/my-index?v"

# 查看分片大小分布
curl -X GET "localhost:9200/_cat/shards?v&s=store:desc"

# 查看热点分片（按文档数排序）
curl -X GET "localhost:9200/_cat/shards?v&s=docs:desc" | head -20
```

## 2.2 分片分配问题

### 手动移动分片

```bash
# 将分片从一个节点移动到另一个
curl -X POST "localhost:9200/_cluster/reroute" -H 'Content-Type: application/json' -d'
{
  "commands": [{
    "move": {
      "index": "my-index",
      "shard": 0,
      "from_node": "node-1",
      "to_node": "node-2"
    }
  }]
}'

# 取消正在迁移的分片
curl -X POST "localhost:9200/_cluster/reroute" -H 'Content-Type: application/json' -d'
{
  "commands": [{
    "cancel": {
      "index": "my-index",
      "shard": 0,
      "node": "node-1"
    }
  }]
}'
```

### 禁用/启用分片分配

```bash
# 禁用分片分配（维护前）
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.enable": "none"
  }
}'

# 重新启用分片分配
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.enable": "all"
  }
}'

# 分配选项：
# all        - 允许所有分片分配（默认）
# primaries  - 只允许主分片分配
# new_primaries - 只允许新索引的主分片分配
# none       - 禁止所有分片分配
```

### 分片不均衡

```bash
# 查看各节点分片数
curl -X GET "localhost:9200/_cat/allocation?v"

# 输出列：
# shards  分片数
# disk.indices 索引占用磁盘
# disk.used   磁盘已用
# disk.avail  磁盘可用
# disk.percent 磁盘使用率
# node    节点名

# 触发重平衡
curl -X POST "localhost:9200/_cluster/reroute?retry_failed=true"

# 调整平衡阈值
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.balance.shard": 0.45,
    "cluster.routing.allocation.balance.index": 0.55
  }
}'
```

---

# 三、索引性能问题

## 3.1 索引统计

```bash
# 查看所有索引
curl -X GET "localhost:9200/_cat/indices?v"

# 输出列：
# health  健康状态
# status  开启/关闭
# index   索引名
# pri     主分片数
# rep     副本数
# docs.count  文档数
# docs.deleted 已删除文档
# store.size  总大小
# pri.store.size 主分片大小

# 按大小排序
curl -X GET "localhost:9200/_cat/indices?v&s=store.size:desc"

# 查看特定索引统计
curl -X GET "localhost:9200/my-index/_stats?pretty"

# 查看索引详细信息
curl -X GET "localhost:9200/my-index?pretty"

# 查看索引映射
curl -X GET "localhost:9200/my-index/_mapping?pretty"

# 查看索引设置
curl -X GET "localhost:9200/my-index/_settings?pretty"
```

## 3.2 写入性能问题

```bash
# 检查写入拒绝
curl -X GET "localhost:9200/_nodes/stats/thread_pool?pretty" | grep -A10 write

# 关键指标：
# queue    队列中的任务
# rejected 拒绝的任务（重要！）

# 检查bulk队列
curl -X GET "localhost:9200/_cat/thread_pool/write?v"

# 输出：
# node_name name  active queue rejected
# node-1    write 5      0     0

# rejected > 0 表示写入压力过大

# 解决方案：

# 1. 增加写入线程池大小
# elasticsearch.yml
# thread_pool.write.queue_size: 1000

# 2. 减少刷新频率
curl -X PUT "localhost:9200/my-index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.refresh_interval": "30s"
}'

# 3. 增加索引缓冲区
# elasticsearch.yml
# indices.memory.index_buffer_size: 20%

# 4. 使用bulk批量写入
# 建议每批 5-15MB

# 5. 临时禁用副本（大量导入时）
curl -X PUT "localhost:9200/my-index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.number_of_replicas": 0
}'
```

## 3.3 查询性能问题

```bash
# 查看慢查询日志
# elasticsearch.yml配置：
# index.search.slowlog.threshold.query.warn: 10s
# index.search.slowlog.threshold.query.info: 5s
# index.search.slowlog.threshold.fetch.warn: 1s

# 动态设置慢查询阈值
curl -X PUT "localhost:9200/my-index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.search.slowlog.threshold.query.warn": "5s",
  "index.search.slowlog.threshold.query.info": "2s"
}'

# 查看查询缓存统计
curl -X GET "localhost:9200/_nodes/stats/indices/query_cache?pretty"

# 查看fielddata缓存
curl -X GET "localhost:9200/_nodes/stats/indices/fielddata?pretty"

# 清理缓存
curl -X POST "localhost:9200/_cache/clear"

# 分析查询性能
curl -X GET "localhost:9200/my-index/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "profile": true,
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}'
```

### 查询优化建议

```bash
# 1. 使用filter而不是query（可缓存）
curl -X GET "localhost:9200/my-index/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"status": "published"}},
        {"range": {"date": {"gte": "2024-01-01"}}}
      ]
    }
  }
}'

# 2. 只返回需要的字段
curl -X GET "localhost:9200/my-index/_search" -H 'Content-Type: application/json' -d'
{
  "_source": ["title", "date"],
  "query": {"match_all": {}}
}'

# 3. 使用routing减少分片扫描
curl -X GET "localhost:9200/my-index/_search?routing=user123" -H 'Content-Type: application/json' -d'
{
  "query": {"term": {"user_id": "user123"}}
}'

# 4. 避免深度分页，使用search_after
curl -X GET "localhost:9200/my-index/_search" -H 'Content-Type: application/json' -d'
{
  "size": 100,
  "sort": [{"date": "desc"}, {"_id": "asc"}],
  "search_after": ["2024-01-20", "doc123"]
}'
```

---

# 四、JVM和资源问题

## 4.1 JVM问题

```bash
# 查看JVM统计
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty"

# 关键指标：
# heap_used_percent        堆使用率（>85%需要关注）
# heap_max_in_bytes        最大堆
# gc.collectors.young      年轻代GC统计
# gc.collectors.old        老年代GC统计

# 检查GC情况
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty" | grep -A5 '"gc"'

# GC问题排查
grep -i "gc\|pause" /var/log/elasticsearch/*.log

# 常见JVM问题：

# 1. 堆内存不足
# 检查heap使用率
curl -X GET "localhost:9200/_cat/nodes?v&h=name,heap.percent,heap.max"

# 建议：
# - 堆设置为物理内存的50%，不超过32GB
# - Xms和Xmx设置相同

# 2. GC压力大
# 检查GC时间占比
# old gc time / uptime > 5% 需要关注

# 3. 堆外内存问题
# 检查进程总内存
ps -o pid,rss,vsz,comm -p $(pgrep -f elasticsearch)
```

## 4.2 磁盘问题

```bash
# 查看磁盘使用
curl -X GET "localhost:9200/_cat/allocation?v"

# 查看各索引磁盘占用
curl -X GET "localhost:9200/_cat/indices?v&s=store.size:desc" | head -20

# 磁盘水位线检查
curl -X GET "localhost:9200/_cluster/settings?include_defaults=true&pretty" | grep watermark

# 默认水位线：
# low: 85%   - 不再分配新分片到此节点
# high: 90%  - 尝试将分片迁移出此节点
# flood_stage: 95% - 索引变为只读

# 清理已删除文档
curl -X POST "localhost:9200/my-index/_forcemerge?max_num_segments=1"
# 注意：forcemerge消耗资源，建议在低峰期执行

# 删除旧索引
curl -X DELETE "localhost:9200/logs-2023-01-*"

# 关闭不用的索引（节省资源）
curl -X POST "localhost:9200/old-index/_close"
```

## 4.3 线程池问题

```bash
# 查看所有线程池状态
curl -X GET "localhost:9200/_cat/thread_pool?v"

# 主要线程池：
# search   - 搜索请求
# write    - 索引/删除/更新请求
# get      - get请求
# analyze  - 分析请求
# generic  - 通用操作

# 查看特定线程池
curl -X GET "localhost:9200/_cat/thread_pool/search,write?v&h=node_name,name,active,queue,rejected"

# rejected > 0 需要关注

# 解决方案：
# 1. 减少并发请求
# 2. 增加队列大小（临时）
# 3. 扩展集群节点
# 4. 优化请求（批量操作）
```

---

# 五、监控与诊断脚本

## 5.1 健康检查脚本

```bash
#!/bin/bash
# es_health_check.sh - Elasticsearch健康检查

ES_HOST=${1:-"localhost:9200"}

echo "===== Elasticsearch健康检查 ====="
echo "目标: $ES_HOST"
echo "时间: $(date)"
echo ""

# 1. 集群状态
echo "--- 1. 集群状态 ---"
status=$(curl -s "$ES_HOST/_cluster/health" | jq -r '.status')
echo "集群状态: $status"
case $status in
    green)  echo "✓ 集群健康" ;;
    yellow) echo "⚠ 集群警告（副本问题）" ;;
    red)    echo "✗ 集群异常（数据可能丢失）" ;;
esac
echo ""

# 2. 节点状态
echo "--- 2. 节点状态 ---"
curl -s "$ES_HOST/_cat/nodes?v&h=name,heap.percent,ram.percent,cpu,load_1m,node.role,master"
echo ""

# 3. 未分配分片
echo "--- 3. 未分配分片 ---"
unassigned=$(curl -s "$ES_HOST/_cluster/health" | jq '.unassigned_shards')
if [ "$unassigned" -gt 0 ]; then
    echo "未分配分片数: $unassigned"
    curl -s "$ES_HOST/_cat/shards?v" | grep UNASSIGNED | head -10
else
    echo "✓ 没有未分配分片"
fi
echo ""

# 4. 磁盘使用
echo "--- 4. 磁盘使用 ---"
curl -s "$ES_HOST/_cat/allocation?v&h=node,disk.percent,disk.used,disk.avail"
echo ""

# 5. 索引统计
echo "--- 5. 索引统计 ---"
echo "索引数: $(curl -s "$ES_HOST/_cat/indices" | wc -l)"
echo "Top 5 大索引:"
curl -s "$ES_HOST/_cat/indices?s=store.size:desc&h=index,docs.count,store.size" | head -5
echo ""

# 6. 线程池拒绝
echo "--- 6. 线程池拒绝 ---"
curl -s "$ES_HOST/_cat/thread_pool/search,write?v&h=node_name,name,rejected" | grep -v "^node_name" | awk '$3>0 {print "⚠", $0}'
rejected_count=$(curl -s "$ES_HOST/_cat/thread_pool/search,write?h=rejected" | awk '{sum+=$1} END {print sum}')
if [ "$rejected_count" -eq 0 ]; then
    echo "✓ 没有请求被拒绝"
fi
echo ""

# 7. Pending Tasks
echo "--- 7. Pending Tasks ---"
pending=$(curl -s "$ES_HOST/_cluster/pending_tasks" | jq '.tasks | length')
echo "待处理任务: $pending"
echo ""

echo "===== 检查完成 ====="
```

## 5.2 性能诊断脚本

```bash
#!/bin/bash
# es_perf_diagnose.sh - Elasticsearch性能诊断

ES_HOST=${1:-"localhost:9200"}

echo "===== Elasticsearch性能诊断 ====="
echo ""

# JVM堆使用
echo "--- JVM堆内存 ---"
curl -s "$ES_HOST/_nodes/stats/jvm?pretty" | \
    jq -r '.nodes | to_entries[] | "\(.value.name): \(.value.jvm.mem.heap_used_percent)%"'
echo ""

# GC统计
echo "--- GC统计 ---"
curl -s "$ES_HOST/_nodes/stats/jvm?pretty" | \
    jq -r '.nodes | to_entries[] | "\(.value.name): young=\(.value.jvm.gc.collectors.young.collection_count) old=\(.value.jvm.gc.collectors.old.collection_count)"'
echo ""

# 索引速率
echo "--- 索引速率 ---"
curl -s "$ES_HOST/_nodes/stats/indices/indexing?pretty" | \
    jq -r '.nodes | to_entries[] | "\(.value.name): \(.value.indices.indexing.index_total) docs"'
echo ""

# 搜索速率
echo "--- 搜索速率 ---"
curl -s "$ES_HOST/_nodes/stats/indices/search?pretty" | \
    jq -r '.nodes | to_entries[] | "\(.value.name): \(.value.indices.search.query_total) queries"'
echo ""

# 线程池队列
echo "--- 线程池队列 ---"
curl -s "$ES_HOST/_cat/thread_pool?v&h=node_name,name,active,queue,rejected" | \
    grep -E "search|write|get"
echo ""

echo "===== 诊断完成 ====="
```

---

## 总结

### ES命令速查

| 任务 | 命令 |
|------|------|
| 集群健康 | `_cluster/health` |
| 节点列表 | `_cat/nodes?v` |
| 分片状态 | `_cat/shards?v` |
| 索引列表 | `_cat/indices?v` |
| 分配解释 | `_cluster/allocation/explain` |
| 线程池 | `_cat/thread_pool?v` |
| JVM统计 | `_nodes/stats/jvm` |

### 状态速查

| 状态 | 含义 | 处理 |
|------|------|------|
| Green | 所有分片正常 | 无需处理 |
| Yellow | 副本未分配 | 检查节点数、分配规则 |
| Red | 主分片未分配 | 紧急处理，可能数据丢失 |

### ES问题排查三板斧

1. **看状态** - `_cluster/health` 确定严重程度
2. **看分片** - `_cat/shards` 找问题分片
3. **看原因** - `_cluster/allocation/explain` 查根因

### 关键记忆

1. Red状态优先处理，可能丢数据
2. rejected > 0 表示有请求被拒绝
3. heap > 85% 需要关注
4. unassigned_shards > 0 需要排查

---

## 相关文章

- [上一篇：云服务问题排查实战](/articles/sre/sre-49-云服务问题排查实战/)
- [下一篇：负载均衡深入排查实战](/articles/sre/sre-51-负载均衡深入排查实战/)
