+++
title = "01. Redis数据结构与典型应用"
description = "Redis核心数据结构：String、Hash、List、Set、ZSet的原理与应用场景"
date = 2025-01-16
weight = 1000
[taxonomies]
tags = ["interview", "database", "redis", "data-structure", "cache"]
+++

# Redis数据结构与典型应用

## 一、Redis数据结构概览

### 1.1 五大基本类型

| 类型 | 说明 | 常见应用 |
|------|------|----------|
| String | 字符串 | 缓存、计数器、分布式锁 |
| Hash | 哈希表 | 对象存储、购物车 |
| List | 列表 | 消息队列、时间线 |
| Set | 集合 | 去重、交并集运算 |
| ZSet | 有序集合 | 排行榜、延迟队列 |

### 1.2 高级数据类型

| 类型 | 说明 | 常见应用 |
|------|------|----------|
| Bitmap | 位图 | 签到、用户在线状态 |
| HyperLogLog | 基数统计 | UV统计 |
| Geo | 地理位置 | 附近的人 |
| Stream | 流 | 消息队列（Redis 5.0+） |

---

## 二、String（字符串）

### 2.1 内部编码

**int**：值为整数时使用

**embstr**：短字符串（≤44字节），一次内存分配

**raw**：长字符串，分开分配内存

### 2.2 常用命令

| 命令 | 说明 |
|------|------|
| SET key value | 设置值 |
| GET key | 获取值 |
| INCR key | 原子递增 |
| DECR key | 原子递减 |
| SETNX key value | 不存在时设置 |
| SETEX key seconds value | 设置值和过期时间 |

### 2.3 应用场景

**缓存**：
- 缓存对象的JSON序列化
- 缓存页面片段

**计数器**：
- 使用INCR原子递增
- 如：阅读量、点赞数

**分布式锁**：
- SET key value NX EX seconds
- 只有不存在时才能设置

**限流**：
- 使用INCR + EXPIRE
- 记录时间窗口内请求次数

---

## 三、Hash（哈希）

### 3.1 内部编码

**ziplist**：元素少且值小时使用，内存紧凑

**hashtable**：元素多或值大时使用

转换条件：
- 字段数 > hash-max-ziplist-entries（默认512）
- 值大小 > hash-max-ziplist-value（默认64字节）

### 3.2 常用命令

| 命令 | 说明 |
|------|------|
| HSET key field value | 设置字段 |
| HGET key field | 获取字段 |
| HMSET key f1 v1 f2 v2 | 批量设置 |
| HGETALL key | 获取所有字段 |
| HINCRBY key field n | 字段增加n |
| HDEL key field | 删除字段 |

### 3.3 应用场景

**对象存储**：
- 每个字段对应对象的一个属性
- 比JSON字符串更灵活（可单独修改字段）

**购物车**：
- key：cart:{user_id}
- field：商品ID
- value：数量

**计数统计**：
- 多个计数器用一个Hash
- HINCRBY原子递增

---

## 四、List（列表）

### 4.1 内部编码

**ziplist**：元素少时使用

**linkedlist**：元素多时使用

**quicklist**（Redis 3.2+）：ziplist组成的双向链表，兼顾两者优点

### 4.2 常用命令

| 命令 | 说明 |
|------|------|
| LPUSH key value | 左侧插入 |
| RPUSH key value | 右侧插入 |
| LPOP key | 左侧弹出 |
| RPOP key | 右侧弹出 |
| LRANGE key start stop | 获取范围元素 |
| BLPOP key timeout | 阻塞弹出 |

### 4.3 应用场景

**消息队列**：
- LPUSH生产消息
- BRPOP阻塞消费
- 简单场景可用，复杂场景建议Kafka/RabbitMQ

**时间线**：
- 新消息LPUSH
- LRANGE获取最新N条
- 如：微博Timeline

**栈**：
- LPUSH + LPOP

**队列**：
- LPUSH + RPOP

---

## 五、Set（集合）

### 5.1 内部编码

**intset**：元素都是整数且数量少

**hashtable**：其他情况

### 5.2 常用命令

| 命令 | 说明 |
|------|------|
| SADD key member | 添加成员 |
| SREM key member | 移除成员 |
| SMEMBERS key | 所有成员 |
| SISMEMBER key member | 是否是成员 |
| SINTER key1 key2 | 交集 |
| SUNION key1 key2 | 并集 |
| SDIFF key1 key2 | 差集 |

### 5.3 应用场景

**去重**：
- 如：用户访问记录去重
- 文章点赞用户列表

**标签**：
- 每个对象的标签集合
- 可以求交集找相似

**共同好友**：
- 用户A的好友：SADD friends:A ...
- 用户B的好友：SADD friends:B ...
- 共同好友：SINTER friends:A friends:B

**抽奖**：
- 参与者：SADD lottery ...
- 随机抽取：SPOP或SRANDMEMBER

---

## 六、ZSet（有序集合）

### 6.1 内部编码

**ziplist**：元素少且值小时

**skiplist + hashtable**：
- skiplist保证有序
- hashtable保证O(1)查分数

### 6.2 常用命令

| 命令 | 说明 |
|------|------|
| ZADD key score member | 添加成员 |
| ZSCORE key member | 获取分数 |
| ZRANK key member | 获取排名 |
| ZRANGE key start stop | 按分数升序获取 |
| ZREVRANGE key start stop | 按分数降序获取 |
| ZINCRBY key increment member | 增加分数 |

### 6.3 应用场景

**排行榜**：
- score为分数
- 实时排行：ZREVRANGE获取TopN
- 用户排名：ZREVRANK

**延迟队列**：
- score为执行时间戳
- 定时轮询分数小于当前时间的任务

**限流滑动窗口**：
- score为请求时间戳
- 删除窗口外的请求
- 统计窗口内请求数

---

## 七、其他数据类型

### 7.1 Bitmap

**本质**：String类型，按位操作

**命令**：
- SETBIT key offset value
- GETBIT key offset
- BITCOUNT key

**应用**：
- 签到：一年只需46字节
- 在线状态：用户ID为偏移量
- 布隆过滤器

### 7.2 HyperLogLog

**特点**：
- 基数统计（不重复元素数量）
- 固定12KB内存
- 有0.81%误差

**命令**：
- PFADD key element
- PFCOUNT key

**应用**：UV统计（允许少量误差）

### 7.3 Geo

**命令**：
- GEOADD key longitude latitude member
- GEODIST key member1 member2
- GEORADIUS key longitude latitude radius

**应用**：附近的人、门店

---

## 八、数据结构选择

### 8.1 选择依据

| 需求 | 推荐类型 |
|------|----------|
| 简单键值 | String |
| 对象属性 | Hash |
| 有序列表 | List |
| 去重集合 | Set |
| 排名/评分 | ZSet |
| 二值状态 | Bitmap |
| 基数统计 | HyperLogLog |
| 地理位置 | Geo |

### 8.2 内存优化

- 使用Hash存储小对象，比String省空间
- 控制Key和Value大小
- 使用整数编码
- 合理设置过期时间

---

## 九、面试要点

### 9.1 常见追问

**Q：String和Hash存储对象的区别？**
A：String存整个JSON，适合整存整取；Hash每个字段单独存储，适合频繁读写部分字段。Hash更省空间（小对象时用ziplist）。

**Q：ZSet的底层实现？**
A：ziplist或skiplist+hashtable。skiplist保证有序和范围查询，hashtable保证O(1)查分数。

**Q：List做消息队列的局限？**
A：不支持多消费者组；没有消息确认机制；没有持久化保证。生产环境建议用Stream或专业消息队列。

**Q：如何用Redis实现排行榜？**
A：使用ZSet，score为分数，member为用户ID。ZINCRBY更新分数，ZREVRANGE获取TopN，ZREVRANK获取用户排名。

### 9.2 核心要点

1. **选择合适的数据结构**：根据操作需求选择
2. **理解内部编码**：影响性能和内存
3. **掌握典型应用**：每种类型的最佳实践
4. **注意边界情况**：大Key、热Key的处理

---

## 相关文章

- [下一篇：Redis为什么这么快](@/articles/interview/interview-02-Redis为什么这么快.md)
