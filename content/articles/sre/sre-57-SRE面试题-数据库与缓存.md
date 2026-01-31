+++
title = "57.SRE面试题-数据库与缓存"
date = 2026-01-21
description = "SRE面试必备：MySQL索引优化、事务隔离级别、Redis数据结构、缓存问题等核心问题详解"
[taxonomies]
tags = ["SRE", "面试", "MySQL", "Redis", "数据库", "缓存"]
+++

## 概述

数据库和缓存是后端系统的核心组件。本文详细解答MySQL、Redis等高频面试问题。

---

# 一、MySQL基础

## 1.1 MySQL索引的原理？

**标准答案**：

```
B+树索引（InnoDB默认）：

特点：
1. 所有数据存储在叶子节点
2. 叶子节点通过指针连接（范围查询高效）
3. 非叶子节点只存储索引键
4. 树高度通常3-4层

结构示意：
            [10|20|30]              ← 根节点
           /    |    \
    [1|5|8] [11|15|18] [21|25|28]   ← 非叶子节点
       |        |         |
    [data]   [data]    [data]       ← 叶子节点（存数据）
       ↔        ↔         ↔         ← 双向链表

为什么用B+树而不是B树？
1. B+树叶子节点连成链表，范围查询更高效
2. B+树非叶子节点不存数据，能存更多索引，树更矮
3. B+树查询稳定，都是到叶子节点

为什么不用Hash索引？
1. Hash不支持范围查询
2. Hash不支持排序
3. Hash不支持部分索引匹配
4. Hash存在哈希冲突

索引类型：
- 主键索引（聚簇索引）：叶子节点存完整数据
- 二级索引（非聚簇索引）：叶子节点存主键值
- 回表：二级索引查到主键后，再查主键索引获取数据
```

---

## 1.2 什么是覆盖索引？

**标准答案**：

```
覆盖索引（Covering Index）：
- 查询的字段都在索引中
- 不需要回表查询
- 执行计划显示 Using index

示例：
-- 创建联合索引
CREATE INDEX idx_name_age ON users(name, age);

-- 覆盖索引查询（只查索引中的列）
SELECT name, age FROM users WHERE name = 'Tom';
-- 不需要回表

-- 非覆盖索引（需要其他列）
SELECT name, age, email FROM users WHERE name = 'Tom';
-- 需要回表查email

优化建议：
1. 将高频查询的列加入索引
2. 避免SELECT *
3. 使用EXPLAIN检查是否Using index
```

---

## 1.3 联合索引的最左前缀原则？

**标准答案**：

```
最左前缀原则：
- 联合索引按照字段顺序组织
- 查询必须从最左列开始才能使用索引

示例：
CREATE INDEX idx_abc ON table(a, b, c);

-- 能使用索引的查询
WHERE a = 1                      ✓ 使用a
WHERE a = 1 AND b = 2            ✓ 使用a,b
WHERE a = 1 AND b = 2 AND c = 3  ✓ 使用a,b,c
WHERE a = 1 AND c = 3            ✓ 只使用a

-- 不能使用索引的查询
WHERE b = 2                      ✗ 缺少a
WHERE c = 3                      ✗ 缺少a
WHERE b = 2 AND c = 3            ✗ 缺少a

-- 范围查询后的列不能使用索引
WHERE a > 1 AND b = 2            只使用a
WHERE a = 1 AND b > 2 AND c = 3  使用a,b，c无法使用

设计建议：
1. 最常用的列放前面
2. 区分度高的列放前面
3. 尽量避免范围查询在中间
```

---

## 1.4 事务的ACID特性？

**标准答案**：

```
ACID：

A - Atomicity（原子性）
- 事务是不可分割的工作单位
- 要么全部执行，要么全部不执行
- 通过undo log实现回滚

C - Consistency（一致性）
- 事务前后数据库保持一致状态
- 业务层面的完整性约束
- 由其他三个特性共同保证

I - Isolation（隔离性）
- 事务之间互不干扰
- 通过锁和MVCC实现
- 有不同隔离级别

D - Durability（持久性）
- 事务提交后永久保存
- 通过redo log实现
- 崩溃恢复

实现机制：
- 原子性：undo log（回滚日志）
- 隔离性：锁 + MVCC
- 持久性：redo log（重做日志）
- 一致性：由上述三者保证
```

---

## 1.5 事务隔离级别有哪些？

**标准答案**：

```
四种隔离级别（从低到高）：

1. READ UNCOMMITTED（读未提交）
   - 可以读取未提交的数据
   - 存在脏读、不可重复读、幻读
   - 几乎不使用

2. READ COMMITTED（读已提交）
   - 只能读取已提交的数据
   - 解决脏读
   - 存在不可重复读、幻读
   - Oracle默认级别

3. REPEATABLE READ（可重复读）
   - 同一事务内读取结果一致
   - 解决脏读、不可重复读
   - InnoDB通过MVCC（快照读）+ 间隙锁（当前读）解决幻读
   - MySQL默认级别

4. SERIALIZABLE（串行化）
   - 完全串行执行
   - 解决所有问题
   - 性能最差

问题说明：
- 脏读：读取到未提交的数据
- 不可重复读：同一行数据，多次读取结果不同
- 幻读：范围查询，多次读取行数不同

MySQL查看和设置：
SELECT @@transaction_isolation;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

---

## 1.6 什么是MVCC？

**标准答案**：

```
MVCC（Multi-Version Concurrency Control）：
- 多版本并发控制
- 读操作不加锁，通过版本实现隔离
- 提高并发性能

InnoDB的MVCC实现：

1. 隐藏列
   - DB_TRX_ID: 最后修改的事务ID
   - DB_ROLL_PTR: 回滚指针，指向undo log

2. undo log
   - 保存数据的历史版本
   - 形成版本链

3. Read View
   - 事务开始时创建的快照
   - 包含当前活跃事务列表
   - 用于判断版本可见性

版本可见性规则：
- 如果row的trx_id < 最小活跃事务ID → 可见
- 如果row的trx_id > 最大事务ID → 不可见
- 如果row的trx_id在活跃列表中 → 不可见
- 如果row的trx_id是当前事务 → 可见

RC和RR的区别：
- RC：每次SELECT都创建新Read View
- RR：事务开始时创建一个Read View，一直使用
```

---

## 1.7 MySQL的锁有哪些？

**标准答案**：

```
按粒度分：

1. 表锁
   - 锁整个表
   - 开销小，加锁快
   - 并发低
   LOCK TABLES t READ/WRITE;

2. 行锁（InnoDB特有）
   - 锁单行
   - 开销大，加锁慢
   - 并发高

按类型分：

1. 共享锁（S锁，读锁）
   SELECT ... LOCK IN SHARE MODE;
   SELECT ... FOR SHARE;  -- MySQL 8.0

2. 排他锁（X锁，写锁）
   SELECT ... FOR UPDATE;
   UPDATE/DELETE自动加X锁

InnoDB行锁类型：

1. 记录锁（Record Lock）
   - 锁定单个行记录

2. 间隙锁（Gap Lock）
   - 锁定范围，不锁记录
   - 防止幻读

3. 临键锁（Next-Key Lock）
   - 记录锁 + 间隙锁
   - InnoDB默认锁类型

死锁：
- 两个事务互相等待对方的锁
- InnoDB自动检测并回滚一个事务
- 查看：SHOW ENGINE INNODB STATUS;
```

---

## 1.8 如何优化慢查询？

**标准答案**：

```bash
# 1. 开启慢查询日志
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;  -- 超过1秒记录

# 2. 使用EXPLAIN分析
EXPLAIN SELECT * FROM users WHERE name = 'Tom';

# EXPLAIN关键字段：
# type: 访问类型（性能从好到差）
#   system > const > eq_ref > ref > range > index > ALL
# key: 使用的索引
# rows: 扫描行数
# Extra: 额外信息
#   Using index: 覆盖索引
#   Using filesort: 需要排序
#   Using temporary: 使用临时表

# 优化策略：

# 1. 添加合适的索引
CREATE INDEX idx_name ON users(name);

# 2. 避免SELECT *
SELECT id, name FROM users;  -- 只查需要的列

# 3. 避免在索引列上使用函数
-- 不好
WHERE YEAR(create_time) = 2024
-- 好
WHERE create_time >= '2024-01-01' AND create_time < '2025-01-01'

# 4. 避免类型转换
-- 不好（字符串字段用数字查询）
WHERE phone = 13800138000
-- 好
WHERE phone = '13800138000'

# 5. 使用LIMIT限制返回行数

# 6. 分页优化
-- 不好
SELECT * FROM users LIMIT 100000, 10;
-- 好（延迟关联）
SELECT * FROM users 
WHERE id > (SELECT id FROM users LIMIT 100000, 1)
LIMIT 10;
```

---

# 二、Redis基础

## 2.1 Redis的数据结构有哪些？

**标准答案**：

```
5种基础数据结构：

1. String（字符串）
   - 最基本的类型
   - 可存储字符串、整数、浮点数
   - 应用：缓存、计数器、分布式锁
   SET key value
   GET key
   INCR key
   SETNX key value  # 不存在时设置

2. Hash（哈希）
   - 键值对集合
   - 适合存储对象
   - 应用：用户信息、商品信息
   HSET user:1 name "Tom" age 20
   HGET user:1 name
   HGETALL user:1

3. List（列表）
   - 双向链表
   - 支持两端操作
   - 应用：消息队列、最新动态
   LPUSH list value
   RPUSH list value
   LPOP list
   LRANGE list 0 -1

4. Set（集合）
   - 无序不重复
   - 支持集合运算
   - 应用：标签、共同好友
   SADD set value
   SMEMBERS set
   SINTER set1 set2  # 交集

5. Sorted Set（有序集合）
   - 有序不重复
   - 每个元素有分数
   - 应用：排行榜、延时队列
   ZADD zset 100 member
   ZRANGE zset 0 -1
   ZRANK zset member

高级数据结构：
- Bitmap：位图，用于签到、在线状态
- HyperLogLog：基数统计，用于UV统计
- Geo：地理位置
- Stream：消息队列（Redis 5.0+）
```

---

## 2.2 Redis为什么这么快？

**标准答案**：

```
1. 纯内存操作
   - 数据存储在内存中
   - 内存读写速度远超磁盘

2. 单线程模型（核心处理）
   - 避免线程切换开销
   - 避免锁竞争
   - 简化实现

3. IO多路复用
   - 使用epoll/kqueue
   - 单线程处理大量连接
   - 非阻塞IO

4. 高效的数据结构
   - 专门优化的数据结构
   - 如SDS、跳表、压缩列表

5. 优化的协议
   - RESP协议简单高效
   - 减少解析开销

关于单线程：
- Redis 6.0引入多线程IO
- 命令执行仍是单线程
- 多线程用于网络IO
```

---

## 2.3 Redis持久化方式？

**标准答案**：

```
两种持久化方式：

1. RDB（Redis Database）
   - 定期生成数据快照
   - fork子进程生成快照文件
   - 恢复速度快

   优点：
   - 文件紧凑，适合备份
   - 恢复速度快
   - 对性能影响小

   缺点：
   - 可能丢失最后一次快照后的数据
   - fork大数据时可能阻塞

   配置：
   save 900 1      # 900秒内有1次修改
   save 300 10     # 300秒内有10次修改
   save 60 10000   # 60秒内有10000次修改

2. AOF（Append Only File）
   - 记录每个写操作
   - 追加写入日志文件
   - 数据安全性更高

   优点：
   - 数据安全性高（最多丢失1秒）
   - 可读性好，易于恢复

   缺点：
   - 文件比RDB大
   - 恢复速度慢

   配置：
   appendonly yes
   appendfsync always    # 每次写入同步（最安全）
   appendfsync everysec  # 每秒同步（推荐）
   appendfsync no        # 系统决定

3. 混合持久化（Redis 4.0+）
   - 结合RDB和AOF优点
   - 快照 + 增量AOF
   
   配置：
   aof-use-rdb-preamble yes
```

---

## 2.4 缓存穿透、击穿、雪崩？

**标准答案**：

```
1. 缓存穿透
   定义：查询不存在的数据，缓存和数据库都没有
   危害：每次请求都打到数据库
   
   解决方案：
   a. 缓存空值（设置较短过期时间）
   b. 布隆过滤器（快速判断数据是否存在）
   c. 参数校验（过滤非法请求）

2. 缓存击穿
   定义：热点key过期，大量请求同时打到数据库
   危害：数据库瞬间压力巨大
   
   解决方案：
   a. 热点数据永不过期
   b. 加互斥锁（只允许一个请求重建缓存）
   c. 逻辑过期（后台异步更新）

3. 缓存雪崩
   定义：大量key同时过期，或Redis宕机
   危害：请求全部打到数据库
   
   解决方案：
   a. 过期时间加随机值
   b. 多级缓存（本地缓存 + Redis）
   c. 熔断限流
   d. Redis高可用（集群/哨兵）

伪代码示例（缓存击穿 - 互斥锁）：
def get_data(key):
    data = cache.get(key)
    if data:
        return data
    
    # 获取分布式锁
    if acquire_lock(key):
        try:
            # 再次检查缓存
            data = cache.get(key)
            if data:
                return data
            
            # 查询数据库
            data = db.query(key)
            cache.set(key, data, ttl)
            return data
        finally:
            release_lock(key)
    else:
        # 等待重试
        sleep(100ms)
        return get_data(key)
```

---

## 2.5 Redis如何实现分布式锁？

**标准答案**：

```
基本实现：

# 加锁
SET lock_key unique_value NX EX 30
# NX: 不存在时设置
# EX: 设置过期时间

# 解锁（需要判断是自己的锁）
# 使用Lua脚本保证原子性
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end

问题和解决：

1. 锁过期但业务未完成
   解决：续期机制（看门狗）
   Redisson自动实现

2. Redis主从复制时锁丢失
   解决：RedLock算法（多节点）
   向N/2+1个节点加锁成功才算成功

3. 可重入
   解决：使用Hash记录加锁次数

Redisson分布式锁（推荐）：
RLock lock = redisson.getLock("lock_key");
try {
    lock.lock();
    // 业务逻辑
} finally {
    lock.unlock();
}
```

---

## 2.6 Redis集群方案？

**标准答案**：

```
1. 主从复制
   - 一主多从
   - 主节点写，从节点读
   - 不支持自动故障转移

2. 哨兵模式（Sentinel）
   - 监控主从节点
   - 自动故障转移
   - 不支持数据分片
   
   工作原理：
   - 监控：定期检查节点状态
   - 通知：发现异常通知管理员
   - 自动故障转移：主节点故障时选举新主

3. Cluster集群
   - 数据分片（16384个槽）
   - 支持水平扩展
   - 自动故障转移
   
   特点：
   - 每个节点负责部分槽
   - 节点间通过Gossip协议通信
   - 客户端可连接任意节点

   限制：
   - 不支持跨槽的多key操作
   - 不支持SELECT切换数据库

选择建议：
- 数据量小，高可用：哨兵模式
- 数据量大，需要分片：Cluster
- 读多写少：主从复制 + 读写分离
```

---

## 2.7 Redis内存淘汰策略？

**标准答案**：

```
8种淘汰策略：

1. noeviction（默认）
   - 不淘汰，内存满时拒绝写入
   
2. allkeys-lru
   - 所有key中淘汰最近最少使用的
   
3. allkeys-lfu
   - 所有key中淘汰最不经常使用的（Redis 4.0+）
   
4. allkeys-random
   - 所有key中随机淘汰
   
5. volatile-lru
   - 有过期时间的key中淘汰LRU
   
6. volatile-lfu
   - 有过期时间的key中淘汰LFU
   
7. volatile-random
   - 有过期时间的key中随机淘汰
   
8. volatile-ttl
   - 淘汰最快过期的key

LRU vs LFU：
- LRU：最近最少使用（时间维度）
- LFU：最不经常使用（频率维度）

配置：
maxmemory 4gb
maxmemory-policy allkeys-lru

推荐：
- 通用场景：allkeys-lru
- 热点数据明显：allkeys-lfu
- 有明确过期需求：volatile-ttl
```

---

# 三、高可用与性能

## 3.1 主从同步原理？

**标准答案**：

```
MySQL主从复制：

1. 主库写binlog
2. 从库IO线程拉取binlog
3. 从库写relay log
4. 从库SQL线程执行relay log

同步方式：
- 异步复制：主库不等从库
- 半同步复制：至少一个从库确认
- 全同步复制：所有从库确认

Redis主从复制：

1. 全量同步
   - 从节点发送PSYNC
   - 主节点生成RDB发送
   - 主节点发送缓冲区命令

2. 增量同步
   - 使用复制偏移量
   - 主节点发送增量命令
   - 断线重连时增量同步

关键参数：
repl-backlog-size  # 复制积压缓冲区
repl-timeout       # 复制超时时间
```

---

## 3.2 读写分离的问题和解决？

**标准答案**：

```
主从延迟问题：
- 从库数据可能落后于主库
- 写后立即读可能读不到

解决方案：

1. 强制走主库
   - 关键业务读主库
   - 如：支付后查询订单

2. 延迟读
   - 写入后等待一定时间再读
   - 适用于非实时场景

3. 会话一致性
   - 同一会话写后读走主库
   - 记录最后写入时间

4. 监控延迟
   - 延迟过大时自动切主
   - SHOW SLAVE STATUS中的Seconds_Behind_Master

5. 半同步复制
   - 确保至少一个从库已同步
```

---

## 3.3 如何设计热点key解决方案？

**标准答案**：

```
热点key问题：
- 某个key访问量极高
- 导致单节点压力大
- 可能导致节点宕机

解决方案：

1. 本地缓存
   - 应用层缓存热点数据
   - 减少Redis访问
   - 注意本地缓存失效

2. 读写分离
   - 热点key多个从节点
   - 读请求分散到多个从节点

3. 热点key拆分
   - 将热点key拆成多个子key
   - key_1, key_2, key_3...
   - 随机或轮询访问

4. 限流降级
   - 对热点key限流
   - 超过阈值返回缓存或降级

5. 提前预热
   - 大促前加载热点数据
   - 避免活动开始瞬间击穿

检测热点key：
# Redis 4.0+
redis-cli --hotkeys
# 或使用代理层统计
```

---

## 总结

### 高频考点速查

| 主题 | 核心概念 | 关键命令/配置 |
|------|----------|---------------|
| MySQL索引 | B+树、最左前缀 | EXPLAIN |
| 事务隔离 | ACID、MVCC | SET TRANSACTION |
| MySQL锁 | 行锁、间隙锁 | FOR UPDATE |
| 慢查询优化 | 索引、EXPLAIN | slow_query_log |
| Redis数据结构 | String/Hash/List/Set/ZSet | - |
| Redis持久化 | RDB/AOF | save/appendfsync |
| 缓存问题 | 穿透/击穿/雪崩 | - |
| 分布式锁 | SETNX/Redisson | SET NX EX |
| Redis集群 | 主从/哨兵/Cluster | - |

### 面试回答技巧

1. **先说原理**：为什么这样设计
2. **再说问题**：有什么问题
3. **给出方案**：如何解决
4. **讲实践**：实际怎么用

---

## 相关文章

- [上一篇：SRE面试题-容器与Kubernetes](/articles/sre/sre-56-SRE面试题-容器与Kubernetes/)
- [下一篇：SRE面试题-监控与故障排查](/articles/sre/sre-58-SRE面试题-监控与故障排查/)
