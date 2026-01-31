+++
title = "13.数据库可靠性工程"
date = 2026-01-19
description = "DBRE实践：数据库高可用、备份恢复、主从切换、性能优化、变更管理"
[taxonomies]
tags = ["SRE", "数据库", "DBRE"]
+++

## DBRE概述

### 什么是DBRE

**Database Reliability Engineering（数据库可靠性工程）**：将SRE原则应用于数据库管理。

### DBRE职责

- 数据库高可用架构设计
- 备份恢复策略
- 性能监控与优化
- 变更管理与发布
- 容量规划
- 故障响应与恢复

---

## 高可用架构

### 主从复制

```
写请求 → 主库(Master)
              ↓ 复制
读请求 → 从库(Slave) × N
```

**复制方式**：

| 方式 | 描述 | 延迟 | 一致性 |
|------|------|------|--------|
| 异步复制 | 主库不等待从库确认 | 低 | 可能丢数据 |
| 半同步复制 | 至少一个从库确认 | 中 | 较好 |
| 同步复制 | 所有从库确认 | 高 | 强一致 |

### 主从切换

**自动切换（Failover）**：
```
主库故障 → 检测（MHA/Orchestrator）→ 选举新主 → 切换
```

**切换步骤**：
1. 检测主库故障
2. 选择数据最新的从库
3. 提升为新主库
4. 其他从库指向新主
5. 更新应用连接

**脑裂问题**：
- 两个节点都认为自己是主库
- 解决：Fencing（隔离旧主）、Quorum机制

### 多活架构

**单元化部署**：
```
用户A → 单元1（完整数据库）
用户B → 单元2（完整数据库）
```

**双写/多写**：
- 冲突处理复杂
- 需要全局唯一ID
- 适合特定场景

---

## 备份与恢复

### 备份类型

| 类型 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| 全量备份 | 完整数据副本 | 恢复简单 | 耗时长、占空间 |
| 增量备份 | 自上次备份的变化 | 速度快 | 恢复需要全量+增量 |
| Binlog备份 | 数据库变更日志 | 可恢复到任意时间点 | 需配合全量使用 |

### 备份策略

**3-2-1原则**：
- 3份数据副本
- 2种存储介质
- 1份异地备份

**备份周期示例**：
```
每日：增量备份（保留7天）
每周：全量备份（保留4周）
每月：全量备份（保留12个月）
Binlog：持续备份（保留7天）
```

### 恢复测试

**定期验证**：
- 每月执行恢复演练
- 验证备份完整性
- 记录恢复时间（RTO）

**恢复步骤**：
1. 恢复最近的全量备份
2. 应用增量备份
3. 应用Binlog到目标时间点
4. 验证数据完整性

### RTO与RPO

- **RTO（Recovery Time Objective）**：恢复时间目标
- **RPO（Recovery Point Objective）**：数据丢失容忍度

| 级别 | RTO | RPO | 方案 |
|------|-----|-----|------|
| 高 | 分钟级 | 秒级 | 同步复制+自动切换 |
| 中 | 小时级 | 分钟级 | 异步复制+备份 |
| 低 | 天级 | 小时级 | 定期备份 |

---

## 性能监控

### 关键指标

**连接指标**：
- 活跃连接数
- 连接池使用率
- 等待连接数

**查询指标**：
- QPS/TPS
- 查询延迟（P50/P95/P99）
- 慢查询数量

**资源指标**：
- CPU使用率
- 内存使用率
- 磁盘IO
- 网络流量

**复制指标**：
- 复制延迟（Seconds_Behind_Master）
- 复制状态（IO/SQL线程）

### 慢查询分析

**开启慢查询日志**：
```sql
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;  -- 超过1秒记录
```

**分析工具**：
```bash
# pt-query-digest分析
pt-query-digest slow.log > report.txt
```

**优化步骤**：
1. 识别慢查询
2. EXPLAIN分析执行计划
3. 添加索引或优化SQL
4. 验证效果

### 锁监控

```sql
-- 查看当前锁等待
SELECT * FROM information_schema.INNODB_LOCK_WAITS;

-- 查看锁信息
SELECT * FROM information_schema.INNODB_LOCKS;

-- 查看事务
SELECT * FROM information_schema.INNODB_TRX;
```

---

## 性能优化

### 索引优化

**索引原则**：
- 高选择性列
- 查询条件列
- 排序和分组列
- 避免过多索引

**复合索引**：
```sql
-- 遵循最左前缀原则
INDEX idx_abc (a, b, c)

-- 可用于
WHERE a = 1
WHERE a = 1 AND b = 2
WHERE a = 1 AND b = 2 AND c = 3

-- 不可用于
WHERE b = 2
WHERE c = 3
```

### 查询优化

**避免**：
- SELECT *
- 大范围扫描
- 函数操作索引列
- 隐式类型转换

**优化技巧**：
```sql
-- 分页优化：避免大offset
-- 差的写法
SELECT * FROM table LIMIT 10000, 20;

-- 好的写法
SELECT * FROM table WHERE id > 10000 LIMIT 20;
```

### 连接池配置

```yaml
# HikariCP配置示例
hikari:
  minimumIdle: 10
  maximumPoolSize: 50
  connectionTimeout: 30000
  idleTimeout: 600000
  maxLifetime: 1800000
```

**配置原则**：
- 最大连接数 ≤ 数据库max_connections
- 考虑应用实例数量
- 留有余量给运维连接

---

## 数据库变更

### Schema变更风险

| 操作 | 风险 | 注意事项 |
|------|------|----------|
| ADD COLUMN | 低 | 可能锁表（老版本MySQL） |
| DROP COLUMN | 中 | 不可回滚，确保无引用 |
| ADD INDEX | 中 | 大表耗时长 |
| MODIFY COLUMN | 高 | 可能重建表 |
| RENAME TABLE | 高 | 应用需要同步更新 |

### Online DDL

**MySQL 8.0+ 支持大部分DDL在线执行**：
```sql
ALTER TABLE users ADD COLUMN age INT, ALGORITHM=INPLACE, LOCK=NONE;
```

**对于大表变更，使用工具**：
- pt-online-schema-change
- gh-ost

```bash
# gh-ost示例
gh-ost \
  --host=master \
  --database=mydb \
  --table=users \
  --alter="ADD COLUMN age INT" \
  --execute
```

### 变更流程

1. **开发阶段**
   - SQL Review
   - 测试环境验证

2. **发布阶段**
   - 评估影响时间
   - 选择低峰期
   - 准备回滚方案

3. **执行阶段**
   - 监控锁等待
   - 监控复制延迟
   - 验证应用正常

4. **收尾阶段**
   - 确认变更完成
   - 更新文档

---

## 分库分表

### 何时分库分表

**分表信号**：
- 单表数据量 > 1000万-5000万
- 查询性能下降
- 单表文件过大

**分库信号**：
- 单库QPS过高
- 单库连接数不足
- 需要跨地域部署

### 分片策略

**范围分片**：
```
user_id 1-1000000 → shard1
user_id 1000001-2000000 → shard2
```
优点：范围查询友好
缺点：热点问题

**Hash分片**：
```
shard = hash(user_id) % shard_count
```
优点：分布均匀
缺点：扩容麻烦

**时间分片**：
```
orders_202601 → 2026年1月数据
orders_202602 → 2026年2月数据
```
优点：适合时序数据
缺点：需要处理跨月查询

### 分片后的挑战

| 挑战 | 解决方案 |
|------|----------|
| 跨分片查询 | 中间件聚合、冗余数据 |
| 分布式事务 | 2PC、TCC、最终一致性 |
| 全局唯一ID | Snowflake、UUID |
| 扩容 | 预分片、一致性Hash |

---

## 故障响应

### 常见故障

**主库宕机**：
1. 确认故障
2. 触发自动/手动切换
3. 验证新主库
4. 更新应用配置
5. 排查原因

**磁盘满**：
1. 紧急清理（Binlog、临时文件）
2. 扩容磁盘
3. 排查增长原因
4. 完善监控告警

**复制延迟**：
1. 检查主库写入量
2. 检查从库资源
3. 检查大事务
4. 考虑并行复制

### 数据恢复

**误删数据**：
```bash
# 使用Binlog恢复
mysqlbinlog --start-datetime="2026-01-19 10:00:00" \
            --stop-datetime="2026-01-19 10:30:00" \
            binlog.000001 | mysql
```

**误删表**：
1. 立即停止写入
2. 从备份恢复
3. 应用Binlog到误操作前

---

## 总结

| 维度 | 关键实践 |
|------|----------|
| 高可用 | 主从复制、自动切换、多AZ部署 |
| 备份恢复 | 3-2-1原则、定期演练 |
| 监控 | 连接、查询、复制、资源 |
| 性能 | 索引优化、查询优化、连接池 |
| 变更 | Online DDL工具、Review流程 |
| 故障响应 | 预案准备、快速恢复 |

DBRE的核心：**像对待代码一样对待数据库——版本控制、自动化、可观测、可恢复**。

---

## 相关文章

- [上一篇：Kubernetes SRE实践](/articles/sre/sre-12-Kubernetes-SRE实践/)
- [下一篇：SRE组织与文化](/articles/sre/sre-14-SRE组织与文化/)
