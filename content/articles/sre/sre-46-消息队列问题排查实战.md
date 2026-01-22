+++
title = "46.消息队列问题排查实战"
date = 2026-01-21
description = "SRE消息队列问题排查完整指南：Kafka、RabbitMQ、Redis队列的积压、延迟、故障排查"
[taxonomies]
tags = ["SRE", "消息队列", "Kafka", "RabbitMQ", "排查", "实战"]
+++

## 概述

消息队列是分布式系统的核心组件。本文详细介绍Kafka、RabbitMQ等消息队列的常见问题排查方法。

---

# 一、Kafka问题排查

## 1.1 Kafka基础命令

### 集群状态检查

```bash
# 查看Broker列表
kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# 查看集群元数据
kafka-metadata.sh --snapshot /path/to/metadata --print-contents

# 使用zookeeper查看broker（旧版本）
zookeeper-shell.sh localhost:2181 ls /brokers/ids

# 查看Controller
zookeeper-shell.sh localhost:2181 get /controller
# 或
kafka-metadata.sh --snapshot /path/to/metadata --print-contents | grep controller
```

### Topic管理

```bash
# 列出所有Topic
kafka-topics.sh --bootstrap-server localhost:9092 --list

# 查看Topic详情
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic my-topic

# 输出示例：
# Topic: my-topic  PartitionCount: 3  ReplicationFactor: 2  Configs:
#   Topic: my-topic  Partition: 0  Leader: 1  Replicas: 1,2  Isr: 1,2
#   Topic: my-topic  Partition: 1  Leader: 2  Replicas: 2,0  Isr: 2,0
#   Topic: my-topic  Partition: 2  Leader: 0  Replicas: 0,1  Isr: 0,1
#
# 字段说明：
# Leader      - 分区Leader所在Broker
# Replicas    - 副本分布
# Isr         - 同步副本（In-Sync Replicas）

# 创建Topic
kafka-topics.sh --bootstrap-server localhost:9092 \
    --create --topic my-topic \
    --partitions 3 \
    --replication-factor 2

# 删除Topic
kafka-topics.sh --bootstrap-server localhost:9092 \
    --delete --topic my-topic

# 修改分区数（只能增加）
kafka-topics.sh --bootstrap-server localhost:9092 \
    --alter --topic my-topic --partitions 6

# 查看Topic配置
kafka-configs.sh --bootstrap-server localhost:9092 \
    --entity-type topics --entity-name my-topic --describe
```

### 消费者组管理

```bash
# 列出所有消费者组
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# 查看消费者组详情
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe --group my-consumer-group

# 输出示例：
# GROUP           TOPIC      PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG     CONSUMER-ID
# my-group        my-topic   0          1000            1500            500     consumer-1
# my-group        my-topic   1          2000            2100            100     consumer-2
# my-group        my-topic   2          1500            1500            0       consumer-3
#
# 关键指标：
# LAG - 消息积压量（重要！）
# CURRENT-OFFSET - 当前消费位置
# LOG-END-OFFSET - 最新消息位置

# 查看消费者组成员
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe --group my-group --members

# 查看所有组的状态
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe --all-groups --state
```

---

## 1.2 常见问题排查

### 问题1：消息积压（Lag高）

```bash
# 检查消费者组Lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe --group my-group

# 计算总Lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe --group my-group 2>/dev/null | \
    awk 'NR>1 {sum+=$6} END {print "Total LAG:", sum}'

# 监控Lag变化
watch -n 5 'kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe --group my-group 2>/dev/null | tail -10'

# 原因分析：
# 1. 消费者处理慢
#    - 检查消费者日志
#    - 增加消费者数量
#    - 优化处理逻辑
#
# 2. 消费者数量不足
#    - 消费者数 < 分区数时无法并行
#    - 增加消费者实例
#
# 3. 分区不均衡
#    - 某些分区消息特别多
#    - 检查生产者分区策略

# 解决方案：

# 1. 增加消费者并行度
# 消费者数 = 分区数 时效率最高

# 2. 临时跳过积压消息（谨慎）
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --group my-group --reset-offsets --to-latest --execute --topic my-topic

# 3. 重置到特定时间
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --group my-group --reset-offsets \
    --to-datetime 2024-01-21T10:00:00.000 \
    --execute --topic my-topic
```

### 问题2：生产者发送失败

```bash
# 测试生产消息
echo "test message" | kafka-console-producer.sh \
    --bootstrap-server localhost:9092 \
    --topic my-topic

# 常见错误和解决：

# 1. "NotLeaderForPartition"
#    - Leader切换中
#    - 检查Broker状态
kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe --topic my-topic | grep Leader

# 2. "NetworkException" / "TimeoutException"
#    - 网络问题
#    - Broker负载高
telnet kafka-broker 9092
kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# 3. "RecordTooLargeException"
#    - 消息超过大小限制
#    - 检查配置
kafka-configs.sh --bootstrap-server localhost:9092 \
    --entity-type topics --entity-name my-topic --describe | grep max.message

# 4. "TopicAuthorizationException"
#    - 权限问题
#    - 检查ACL配置
kafka-acls.sh --bootstrap-server localhost:9092 \
    --list --topic my-topic
```

### 问题3：Broker异常

```bash
# 检查Broker日志
tail -100 /var/log/kafka/server.log
grep -i "error\|exception\|warn" /var/log/kafka/server.log | tail -50

# 检查Broker进程
ps aux | grep kafka
jps -l | grep kafka

# 检查JVM状态
jstat -gc <kafka_pid> 1000 5

# 检查磁盘使用
df -h /var/kafka-logs/
du -sh /var/kafka-logs/*

# 检查文件描述符
ls /proc/<kafka_pid>/fd | wc -l
cat /proc/<kafka_pid>/limits | grep "open files"

# 常见Broker问题：

# 1. 磁盘满
df -h
# 解决：清理老数据、扩容

# 2. OOM
dmesg | grep -i "killed process"
# 解决：增加内存、调整JVM参数

# 3. GC频繁
grep "GC" /var/log/kafka/server.log | tail -20
# 解决：调整GC参数

# 4. 网络问题
netstat -ant | grep 9092 | wc -l
# 检查连接数是否过多
```

### 问题4：副本同步问题

```bash
# 检查ISR状态
kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe --topic my-topic

# ISR数量 < Replicas数量 表示有副本不同步

# 查看Under-Replicated分区
kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe --under-replicated-partitions

# 查看离线分区
kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe --unavailable-partitions

# 原因分析：
# 1. Broker宕机
#    - 检查Broker状态
#
# 2. 网络延迟高
#    - 检查Broker间网络
#
# 3. Broker负载高
#    - 检查CPU、磁盘IO

# 手动触发Leader选举
kafka-leader-election.sh --bootstrap-server localhost:9092 \
    --election-type PREFERRED \
    --topic my-topic --partition 0

# 重新分配分区
kafka-reassign-partitions.sh --bootstrap-server localhost:9092 \
    --reassignment-json-file reassign.json --execute
```

---

## 1.3 Kafka监控指标

```bash
# 使用JMX获取指标
# 关键指标：

# 1. 消息速率
# kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec
# kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec
# kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec

# 2. 请求延迟
# kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Produce
# kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Fetch

# 3. 副本延迟
# kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions
# kafka.server:type=ReplicaFetcherManager,name=MaxLag

# 4. 控制器状态
# kafka.controller:type=KafkaController,name=ActiveControllerCount

# Prometheus + JMX Exporter配置
# 添加到Kafka启动参数：
# -javaagent:/path/to/jmx_prometheus_javaagent.jar=7071:/path/to/kafka.yml
```

---

# 二、RabbitMQ问题排查

## 2.1 RabbitMQ基础命令

### 集群状态

```bash
# 查看集群状态
rabbitmqctl cluster_status

# 输出关键信息：
# Nodes: 节点列表
# Running Nodes: 运行中的节点
# Cluster name: 集群名称
# Disk Nodes / Ram Nodes: 磁盘节点/内存节点

# 查看节点状态
rabbitmqctl status

# 健康检查
rabbitmqctl node_health_check

# 查看版本
rabbitmqctl version
```

### 队列管理

```bash
# 列出所有队列
rabbitmqctl list_queues

# 详细信息
rabbitmqctl list_queues name messages consumers memory state

# 输出示例：
# name           messages  consumers  memory    state
# my-queue       1500      2          1048576   running
#
# 关键指标：
# messages   - 队列中消息数（重要！）
# consumers  - 消费者数量
# memory     - 占用内存

# 列出特定vhost的队列
rabbitmqctl list_queues -p /my-vhost

# 查看队列详情
rabbitmqctl list_queues name messages_ready messages_unacknowledged

# messages_ready        - 待消费消息
# messages_unacknowledged - 已投递未确认消息

# 清空队列
rabbitmqctl purge_queue my-queue

# 删除队列
rabbitmqctl delete_queue my-queue
```

### 连接和通道

```bash
# 列出连接
rabbitmqctl list_connections name state channels

# 列出通道
rabbitmqctl list_channels connection name consumer_count messages_unacknowledged

# 关闭连接
rabbitmqctl close_connection "<connection_name>" "reason"

# 列出消费者
rabbitmqctl list_consumers
```

### Exchange和Binding

```bash
# 列出Exchange
rabbitmqctl list_exchanges name type

# 列出Binding
rabbitmqctl list_bindings source_name destination_name routing_key
```

---

## 2.2 常见问题排查

### 问题1：队列消息积压

```bash
# 检查队列积压
rabbitmqctl list_queues name messages consumers

# 实时监控
watch -n 5 'rabbitmqctl list_queues name messages consumers 2>/dev/null'

# 原因分析：

# 1. 消费者不足
rabbitmqctl list_queues name messages consumers | awk '$3==0 {print "No consumer:", $1}'

# 2. 消费者处理慢
# 检查unacked消息
rabbitmqctl list_queues name messages_unacknowledged
# unacked过多说明消费者处理慢或prefetch设置过大

# 3. 消费者断开
rabbitmqctl list_consumers

# 解决方案：

# 1. 增加消费者
# 2. 优化消费者处理逻辑
# 3. 调整prefetch count
#    channel.basic_qos(prefetch_count=10)

# 4. 临时清空队列（谨慎！）
rabbitmqctl purge_queue my-queue
```

### 问题2：内存告警

```bash
# 检查内存使用
rabbitmqctl status | grep -A 10 "Memory"

# 或
rabbitmqctl eval 'rabbit_vm:memory().'

# 查看各部分内存占用
rabbitmqctl status | grep -E "connection_|queue_|msg_"

# 内存告警阈值
# 默认：物理内存的40%

# 查看告警状态
rabbitmqctl list_queues name state | grep -v running

# 常见原因：

# 1. 队列消息积压
rabbitmqctl list_queues name messages memory --sort-by-memory

# 2. 连接过多
rabbitmqctl list_connections | wc -l

# 3. 未确认消息过多
rabbitmqctl list_channels messages_unacknowledged

# 解决方案：

# 1. 处理积压消息
# 2. 关闭闲置连接
# 3. 设置队列TTL
# 4. 启用lazy queue
# 5. 增加内存或调整阈值
rabbitmqctl set_vm_memory_high_watermark 0.5
```

### 问题3：节点宕机/网络分区

```bash
# 检查集群状态
rabbitmqctl cluster_status

# 检查网络分区
rabbitmqctl cluster_status | grep -A 5 "Network Partitions"

# 处理网络分区：

# 1. 自动处理策略（推荐在配置中设置）
# cluster_partition_handling = autoheal
# cluster_partition_handling = pause_minority
# cluster_partition_handling = pause_if_all_down

# 2. 手动处理
# 停止一个分区的节点
rabbitmqctl stop_app
# 重新加入集群
rabbitmqctl join_cluster rabbit@node1
rabbitmqctl start_app

# 强制重置（数据会丢失）
rabbitmqctl stop_app
rabbitmqctl force_reset
rabbitmqctl start_app
```

### 问题4：连接问题

```bash
# 检查连接数
rabbitmqctl list_connections | wc -l

# 查看连接详情
rabbitmqctl list_connections name peer_host peer_port state channels

# 连接状态：
# running   - 正常
# blocking  - 被流控阻塞
# blocked   - 被阻塞

# 检查被阻塞的连接
rabbitmqctl list_connections name state | grep -v running

# 连接超时问题
# 检查heartbeat设置
rabbitmqctl list_connections name timeout

# 测试连接
python3 -c "
import pika
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
print('Connected!')
connection.close()
"
```

---

## 2.3 RabbitMQ管理API

```bash
# 启用管理插件
rabbitmq-plugins enable rabbitmq_management

# 访问Web UI
# http://localhost:15672
# 默认用户：guest/guest

# API查询示例

# 获取概览
curl -u guest:guest http://localhost:15672/api/overview

# 获取所有队列
curl -u guest:guest http://localhost:15672/api/queues

# 获取特定队列
curl -u guest:guest http://localhost:15672/api/queues/%2F/my-queue
# 注意：vhost中的/需要编码为%2F

# 获取队列消息数
curl -s -u guest:guest http://localhost:15672/api/queues | \
    jq '.[] | {name: .name, messages: .messages}'

# 发送消息（测试）
curl -u guest:guest -X POST \
    http://localhost:15672/api/exchanges/%2F/amq.default/publish \
    -H "Content-Type: application/json" \
    -d '{"properties":{},"routing_key":"my-queue","payload":"test","payload_encoding":"string"}'
```

---

# 三、Redis队列问题排查

## 3.1 Redis List作为队列

```bash
# 查看队列长度
redis-cli LLEN my-queue

# 查看队列内容（不消费）
redis-cli LRANGE my-queue 0 9

# 队列积压监控
watch -n 1 'redis-cli LLEN my-queue'

# 多个队列长度
redis-cli --scan --pattern "*queue*" | while read key; do
    len=$(redis-cli LLEN "$key" 2>/dev/null)
    [ -n "$len" ] && echo "$key: $len"
done

# 清空队列
redis-cli DEL my-queue
```

## 3.2 Redis Stream

```bash
# 查看Stream信息
redis-cli XINFO STREAM my-stream

# 输出关键信息：
# length          - 消息数量
# first-entry     - 第一条消息
# last-entry      - 最后一条消息
# groups          - 消费者组数量

# 查看消费者组
redis-cli XINFO GROUPS my-stream

# 输出：
# name            - 组名
# consumers       - 消费者数量
# pending         - 待确认消息数（重要！）
# last-delivered-id - 最后投递的消息ID

# 查看Pending消息（未确认）
redis-cli XPENDING my-stream my-group

# 详细Pending
redis-cli XPENDING my-stream my-group - + 10

# 查看消费者
redis-cli XINFO CONSUMERS my-stream my-group

# 确认消息
redis-cli XACK my-stream my-group message-id

# 清理已消费消息
redis-cli XTRIM my-stream MAXLEN 10000
```

## 3.3 常见问题

```bash
# 问题1：队列积压

# 检查队列长度
redis-cli LLEN my-queue
# 或Stream
redis-cli XLEN my-stream

# 检查消费者状态
redis-cli CLIENT LIST | grep consumer

# 解决：
# 1. 增加消费者
# 2. 优化消费逻辑
# 3. 临时清理（谨慎）


# 问题2：Pending消息过多

# 检查Pending
redis-cli XPENDING my-stream my-group

# 查看长时间未确认的消息
redis-cli XPENDING my-stream my-group - + 10 consumer-name

# 转移超时消息
redis-cli XCLAIM my-stream my-group new-consumer 60000 message-id

# 批量处理超时消息
redis-cli XAUTOCLAIM my-stream my-group new-consumer 60000 0-0 COUNT 10


# 问题3：内存问题

# 检查队列内存占用
redis-cli MEMORY USAGE my-queue

# Stream内存
redis-cli MEMORY USAGE my-stream

# 清理策略
redis-cli XTRIM my-stream MAXLEN ~ 100000
```

---

# 四、消息队列监控

## 4.1 关键监控指标

```markdown
## Kafka关键指标
- 消费者Lag
- 生产速率 (messages/sec)
- 消费速率 (messages/sec)
- Under-Replicated分区数
- ISR收缩/扩展频率
- 请求延迟

## RabbitMQ关键指标
- 队列消息数
- 消费者数量
- Unacked消息数
- 内存使用率
- 磁盘使用率
- 连接数
- 通道数

## Redis队列关键指标
- 队列长度 (LLEN/XLEN)
- Pending消息数
- 内存使用
- 消费者连接数
```

## 4.2 诊断脚本

```bash
#!/bin/bash
# mq_diagnose.sh - 消息队列诊断

MQ_TYPE=$1  # kafka / rabbitmq / redis

case $MQ_TYPE in
    kafka)
        echo "===== Kafka诊断 ====="
        echo ""
        echo "--- Broker状态 ---"
        kafka-broker-api-versions.sh --bootstrap-server localhost:9092 2>/dev/null | head -5
        echo ""
        echo "--- Topic列表 ---"
        kafka-topics.sh --bootstrap-server localhost:9092 --list 2>/dev/null | head -10
        echo ""
        echo "--- 消费者组Lag ---"
        kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list 2>/dev/null | while read group; do
            echo "Group: $group"
            kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group "$group" 2>/dev/null | tail -5
        done | head -30
        echo ""
        echo "--- Under-Replicated分区 ---"
        kafka-topics.sh --bootstrap-server localhost:9092 --describe --under-replicated-partitions 2>/dev/null
        ;;
        
    rabbitmq)
        echo "===== RabbitMQ诊断 ====="
        echo ""
        echo "--- 集群状态 ---"
        rabbitmqctl cluster_status 2>/dev/null | head -20
        echo ""
        echo "--- 队列状态 ---"
        rabbitmqctl list_queues name messages consumers state 2>/dev/null | head -20
        echo ""
        echo "--- 内存状态 ---"
        rabbitmqctl status 2>/dev/null | grep -A 5 "Memory"
        echo ""
        echo "--- 连接数 ---"
        echo "Total: $(rabbitmqctl list_connections 2>/dev/null | wc -l)"
        ;;
        
    redis)
        echo "===== Redis队列诊断 ====="
        echo ""
        echo "--- 服务状态 ---"
        redis-cli ping
        echo ""
        echo "--- 队列长度 ---"
        redis-cli --scan --pattern "*queue*" 2>/dev/null | while read key; do
            type=$(redis-cli TYPE "$key" 2>/dev/null)
            case $type in
                list)
                    len=$(redis-cli LLEN "$key" 2>/dev/null)
                    echo "$key (list): $len"
                    ;;
                stream)
                    len=$(redis-cli XLEN "$key" 2>/dev/null)
                    echo "$key (stream): $len"
                    ;;
            esac
        done | head -20
        echo ""
        echo "--- 内存使用 ---"
        redis-cli INFO memory 2>/dev/null | grep -E "used_memory_human|maxmemory_human"
        ;;
        
    *)
        echo "Usage: $0 <kafka|rabbitmq|redis>"
        exit 1
        ;;
esac

echo ""
echo "===== 诊断完成 ====="
```

---

## 总结

### Kafka命令速查

| 任务 | 命令 |
|------|------|
| 查看Topic | `kafka-topics.sh --describe --topic xxx` |
| 查看Lag | `kafka-consumer-groups.sh --describe --group xxx` |
| 重置Offset | `kafka-consumer-groups.sh --reset-offsets` |
| 查看日志 | `/var/log/kafka/server.log` |

### RabbitMQ命令速查

| 任务 | 命令 |
|------|------|
| 队列状态 | `rabbitmqctl list_queues name messages consumers` |
| 集群状态 | `rabbitmqctl cluster_status` |
| 连接列表 | `rabbitmqctl list_connections` |
| 清空队列 | `rabbitmqctl purge_queue xxx` |

### Redis队列速查

| 任务 | 命令 |
|------|------|
| 队列长度 | `LLEN queue` / `XLEN stream` |
| Pending消息 | `XPENDING stream group` |
| 清理数据 | `DEL queue` / `XTRIM stream` |

**消息队列排查三板斧**：
1. **查积压** - Lag/messages数量
2. **查消费者** - 是否在线、处理速度
3. **查资源** - 内存、磁盘、连接数

**关键记忆**：
1. Kafka Lag是核心指标
2. RabbitMQ关注unacked消息
3. Redis Stream用XPENDING看待确认
4. 积压问题先加消费者
