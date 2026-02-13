+++
title = "35. 数据库问题排查实战"
date = 2026-01-21
weight = 35000
description = "SRE数据库问题排查完整指南：MySQL/PostgreSQL慢查询、锁问题、连接问题的定位与解决"
[taxonomies]
tags = ["SRE", "数据库", "MySQL", "PostgreSQL", "排查", "实战"]
+++

## 概述

数据库是大多数应用的核心组件，数据库问题往往导致整个系统不可用。本文详细介绍MySQL和PostgreSQL常见问题的排查方法。

---

# 一、MySQL问题排查

## 1.1 连接问题

### 场景：无法连接数据库

**第一步：检查服务状态**

```bash
# 检查MySQL服务
systemctl status mysql
systemctl status mysqld  # CentOS

# 查看错误日志
tail -100 /var/log/mysql/error.log
# 或
tail -100 /var/log/mysqld.log
```

**第二步：检查监听**

```bash
# 检查端口监听
ss -tlnp | grep 3306

# 检查绑定地址
grep bind-address /etc/mysql/mysql.conf.d/mysqld.cnf
# 如果是127.0.0.1，只能本地连接

# 检查是否通过socket连接
ls -la /var/run/mysqld/mysqld.sock
```

**第三步：测试连接**

```bash
# 本地连接
mysql -u root -p

# 远程连接
mysql -h <host> -P 3306 -u <user> -p

# 指定socket
mysql -S /var/run/mysqld/mysqld.sock -u root -p
```

### 连接数过多

```sql
-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看最大连接数
SHOW VARIABLES LIKE 'max_connections';

-- 查看所有连接
SHOW PROCESSLIST;
SHOW FULL PROCESSLIST;

-- 查看各用户连接数
SELECT user, host, COUNT(*) as connections 
FROM information_schema.processlist 
GROUP BY user, host 
ORDER BY connections DESC;

-- 查看等待中的连接
SELECT * FROM information_schema.processlist WHERE command = 'Sleep';

-- 杀死空闲连接
-- 生成kill语句
SELECT CONCAT('KILL ', id, ';') 
FROM information_schema.processlist 
WHERE command = 'Sleep' 
AND time > 300;

-- 临时增加连接数
SET GLOBAL max_connections = 500;
```

---

## 1.2 慢查询排查

### 开启慢查询日志

```sql
-- 查看慢查询配置
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 临时开启
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- 超过1秒记录
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- 永久配置（my.cnf）
-- [mysqld]
-- slow_query_log = 1
-- slow_query_log_file = /var/log/mysql/slow.log
-- long_query_time = 1
-- log_queries_not_using_indexes = 1
```

### 分析慢查询日志

```bash
# 使用mysqldumpslow分析
mysqldumpslow -s t -t 10 /var/log/mysql/slow.log

# 参数详解：
# -s 排序方式：
#    t - 按查询时间排序
#    c - 按执行次数排序
#    l - 按锁等待时间排序
#    r - 按返回行数排序
# -t 10 显示前10条
# -g pattern 过滤匹配的查询

# 按次数排序
mysqldumpslow -s c -t 10 /var/log/mysql/slow.log

# 过滤特定表
mysqldumpslow -g "users" /var/log/mysql/slow.log

# 使用pt-query-digest（更强大）
apt install percona-toolkit
pt-query-digest /var/log/mysql/slow.log
```

### 分析执行计划

```sql
-- 使用EXPLAIN分析
EXPLAIN SELECT * FROM users WHERE name = 'test';

-- 输出列详解：
-- id            查询标识
-- select_type   查询类型（SIMPLE/PRIMARY/SUBQUERY等）
-- table         表名
-- type          访问类型（从好到差：const > eq_ref > ref > range > index > ALL）
-- possible_keys 可能使用的索引
-- key           实际使用的索引
-- key_len       索引长度
-- ref           索引比较的列
-- rows          预估扫描行数
-- Extra         额外信息
--   Using index      - 覆盖索引
--   Using where      - WHERE过滤
--   Using filesort   - 文件排序（需优化）
--   Using temporary  - 临时表（需优化）

-- EXPLAIN FORMAT=JSON（更详细）
EXPLAIN FORMAT=JSON SELECT * FROM users WHERE name = 'test';

-- 实际执行分析
EXPLAIN ANALYZE SELECT * FROM users WHERE name = 'test';
```

### 常见慢查询原因

| 原因 | EXPLAIN特征 | 解决方法 |
|------|-------------|----------|
| 全表扫描 | type=ALL | 添加索引 |
| 索引失效 | key=NULL | 检查索引使用 |
| 文件排序 | Using filesort | 优化ORDER BY |
| 临时表 | Using temporary | 优化GROUP BY |
| 返回太多行 | rows很大 | 添加LIMIT |

---

## 1.3 锁问题排查

### 查看锁状态

```sql
-- 查看InnoDB锁状态
SHOW ENGINE INNODB STATUS\G

-- 关注TRANSACTIONS部分：
-- ---TRANSACTION xxx, ACTIVE 10 sec
-- LOCK WAIT
-- 表示有锁等待

-- 查看锁等待（MySQL 8.0+）
SELECT * FROM performance_schema.data_lock_waits;

-- 查看当前锁
SELECT * FROM performance_schema.data_locks;

-- MySQL 5.7
SELECT * FROM information_schema.innodb_lock_waits;
SELECT * FROM information_schema.innodb_locks;
SELECT * FROM information_schema.innodb_trx;

-- 查看锁等待的进程
SELECT 
    r.trx_id waiting_trx_id,
    r.trx_mysql_thread_id waiting_thread,
    r.trx_query waiting_query,
    b.trx_id blocking_trx_id,
    b.trx_mysql_thread_id blocking_thread,
    b.trx_query blocking_query
FROM information_schema.innodb_lock_waits w
JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id;
```

### 解决锁问题

```sql
-- 找到阻塞的事务并kill
-- 1. 找到blocking_thread
-- 2. 确认可以kill
SHOW PROCESSLIST;
KILL <thread_id>;

-- 设置锁等待超时
SET GLOBAL innodb_lock_wait_timeout = 10;  -- 默认50秒

-- 查看死锁日志
SHOW ENGINE INNODB STATUS\G
-- 查看LATEST DETECTED DEADLOCK部分
```

### 死锁分析

```sql
-- 开启死锁日志
SET GLOBAL innodb_print_all_deadlocks = ON;

-- 死锁日志位置
-- /var/log/mysql/error.log

-- 分析死锁原因：
-- 1. 事务顺序不一致
-- 2. 间隙锁冲突
-- 3. 热点行竞争

-- 解决方法：
-- 1. 保持事务获取锁的顺序一致
-- 2. 减小事务范围
-- 3. 添加合适的索引
```

---

## 1.4 性能监控

### 关键状态变量

```sql
-- 查询吞吐量
SHOW GLOBAL STATUS LIKE 'Questions';
SHOW GLOBAL STATUS LIKE 'Com_select';
SHOW GLOBAL STATUS LIKE 'Com_insert';
SHOW GLOBAL STATUS LIKE 'Com_update';
SHOW GLOBAL STATUS LIKE 'Com_delete';

-- 连接相关
SHOW GLOBAL STATUS LIKE 'Threads_connected';
SHOW GLOBAL STATUS LIKE 'Threads_running';
SHOW GLOBAL STATUS LIKE 'Connections';
SHOW GLOBAL STATUS LIKE 'Aborted_connects';

-- InnoDB缓冲池
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_read_requests';  -- 逻辑读
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_reads';          -- 物理读
-- 命中率 = (read_requests - reads) / read_requests * 100%

-- 临时表
SHOW GLOBAL STATUS LIKE 'Created_tmp_tables';
SHOW GLOBAL STATUS LIKE 'Created_tmp_disk_tables';
-- 磁盘临时表比例高需要优化

-- 慢查询
SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

### 实时监控脚本

```bash
#!/bin/bash
# mysql_monitor.sh

MYSQL_USER="root"
MYSQL_PASS="password"

while true; do
    echo "=== $(date) ==="
    mysql -u$MYSQL_USER -p$MYSQL_PASS -e "
        SELECT 
            NOW() as time,
            (SELECT variable_value FROM performance_schema.global_status WHERE variable_name='Threads_connected') as connections,
            (SELECT variable_value FROM performance_schema.global_status WHERE variable_name='Threads_running') as running,
            (SELECT variable_value FROM performance_schema.global_status WHERE variable_name='Slow_queries') as slow
    " 2>/dev/null
    
    # 显示当前运行的查询
    mysql -u$MYSQL_USER -p$MYSQL_PASS -e "
        SELECT id, user, host, db, time, state, LEFT(info, 50) as query 
        FROM information_schema.processlist 
        WHERE command != 'Sleep' 
        AND time > 1
        ORDER BY time DESC
    " 2>/dev/null
    
    sleep 5
done
```

---

# 二、PostgreSQL问题排查

## 2.1 连接问题

### 检查服务状态

```bash
# 检查服务
systemctl status postgresql

# 查看日志
tail -100 /var/log/postgresql/postgresql-*-main.log

# 检查监听
ss -tlnp | grep 5432

# 检查配置
cat /etc/postgresql/*/main/postgresql.conf | grep listen_addresses
cat /etc/postgresql/*/main/pg_hba.conf
```

### 连接数问题

```sql
-- 查看最大连接数
SHOW max_connections;

-- 查看当前连接数
SELECT count(*) FROM pg_stat_activity;

-- 按数据库统计
SELECT datname, count(*) 
FROM pg_stat_activity 
GROUP BY datname;

-- 按用户统计
SELECT usename, count(*) 
FROM pg_stat_activity 
GROUP BY usename;

-- 按状态统计
SELECT state, count(*) 
FROM pg_stat_activity 
GROUP BY state;

-- 查看空闲连接
SELECT * FROM pg_stat_activity WHERE state = 'idle';

-- 终止空闲连接
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND state_change < NOW() - INTERVAL '10 minutes';
```

---

## 2.2 慢查询排查

### 开启慢查询日志

```sql
-- 查看当前配置
SHOW log_min_duration_statement;

-- 临时设置（记录超过1秒的查询）
SET log_min_duration_statement = 1000;  -- 毫秒

-- 永久配置（postgresql.conf）
-- log_min_duration_statement = 1000
-- log_statement = 'all'  # 或 'ddl', 'mod', 'none'

-- 重载配置
SELECT pg_reload_conf();
```

### 查看当前运行的查询

```sql
-- 查看活动查询
SELECT 
    pid,
    usename,
    datname,
    state,
    query_start,
    NOW() - query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- 查看长时间运行的查询
SELECT 
    pid,
    NOW() - query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
AND NOW() - query_start > INTERVAL '30 seconds';

-- 取消长查询
SELECT pg_cancel_backend(<pid>);

-- 强制终止
SELECT pg_terminate_backend(<pid>);
```

### 分析执行计划

```sql
-- 使用EXPLAIN
EXPLAIN SELECT * FROM users WHERE id = 1;

-- 带实际执行信息
EXPLAIN ANALYZE SELECT * FROM users WHERE id = 1;

-- 更详细的格式
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT * FROM users WHERE id = 1;

-- 输出关键信息：
-- Seq Scan     - 顺序扫描（可能需要索引）
-- Index Scan   - 索引扫描（好）
-- Bitmap Scan  - 位图扫描
-- Hash Join    - 哈希连接
-- Nested Loop  - 嵌套循环
-- Sort         - 排序
-- Aggregate    - 聚合

-- 关注指标：
-- cost         - 预估成本
-- rows         - 预估行数
-- actual time  - 实际时间
-- Buffers      - 缓冲区使用
```

### 索引分析

```sql
-- 查看表的索引
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'users';

-- 查看索引使用情况
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 查找未使用的索引
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND schemaname NOT IN ('pg_catalog', 'pg_toast');

-- 查看表扫描情况
SELECT
    relname,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables
ORDER BY seq_scan DESC;
```

---

## 2.3 锁问题排查

### 查看锁状态

```sql
-- 查看当前锁
SELECT 
    l.locktype,
    l.relation::regclass,
    l.mode,
    l.granted,
    a.usename,
    a.query,
    a.query_start
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE NOT l.granted;

-- 查看锁等待
SELECT 
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_locks blocked_locks ON blocked.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.relation = blocked_locks.relation
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_stat_activity blocking ON blocking_locks.pid = blocking.pid
WHERE NOT blocked_locks.granted;

-- 简化版锁等待查询（PostgreSQL 9.6+）
SELECT * FROM pg_stat_activity WHERE wait_event_type = 'Lock';
```

### 解决锁问题

```sql
-- 找到阻塞进程并终止
SELECT pg_terminate_backend(<blocking_pid>);

-- 设置锁超时
SET lock_timeout = '10s';

-- 设置语句超时
SET statement_timeout = '30s';

-- 全局设置（postgresql.conf）
-- lock_timeout = 10000
-- statement_timeout = 30000
```

---

## 2.4 性能监控

### 关键视图

```sql
-- 数据库统计
SELECT * FROM pg_stat_database WHERE datname = current_database();

-- 表统计
SELECT * FROM pg_stat_user_tables;

-- 索引统计
SELECT * FROM pg_stat_user_indexes;

-- 缓存命中率
SELECT 
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit)  as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
-- ratio应该>99%

-- 索引缓存命中率
SELECT 
    sum(idx_blks_read) as idx_read,
    sum(idx_blks_hit)  as idx_hit,
    CASE WHEN sum(idx_blks_hit) + sum(idx_blks_read) = 0 THEN 0
         ELSE sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read))
    END as ratio
FROM pg_statio_user_indexes;
```

### 查看表膨胀

```sql
-- 查看表膨胀情况
SELECT
    schemaname,
    relname,
    n_live_tup,
    n_dead_tup,
    ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;

-- 手动VACUUM
VACUUM ANALYZE tablename;

-- VACUUM FULL（会锁表）
VACUUM FULL tablename;
```

---

# 三、通用数据库排查

## 3.1 连接池问题

```bash
# 检查应用端连接池配置
# 常见问题：
# 1. 连接池太小导致等待
# 2. 连接泄漏导致耗尽
# 3. 连接超时配置不当

# 检查应用日志中的连接错误
grep -i "connection\|pool\|timeout" /var/log/app/app.log
```

## 3.2 复制延迟

### MySQL主从延迟

```sql
-- 在从库执行
SHOW SLAVE STATUS\G

-- 关注字段：
-- Slave_IO_Running: Yes
-- Slave_SQL_Running: Yes
-- Seconds_Behind_Master: 0  -- 延迟秒数

-- 查看延迟详情
-- Read_Master_Log_Pos   - 主库日志位置
-- Exec_Master_Log_Pos   - 从库执行位置
```

### PostgreSQL流复制延迟

```sql
-- 主库查看
SELECT * FROM pg_stat_replication;

-- 关注字段：
-- sent_lsn      - 已发送位置
-- write_lsn     - 已写入位置
-- flush_lsn     - 已刷新位置
-- replay_lsn    - 已重放位置

-- 计算延迟
SELECT 
    client_addr,
    pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes,
    pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) / 1024 / 1024 AS lag_mb
FROM pg_stat_replication;
```

---

## 3.3 诊断脚本

### MySQL诊断脚本

```bash
#!/bin/bash
# mysql_diagnose.sh

MYSQL_USER="root"
MYSQL_PASS="password"

echo "===== MySQL诊断报告 ====="
echo "时间: $(date)"
echo ""

echo "--- 1. 服务状态 ---"
systemctl status mysql --no-pager | head -10
echo ""

echo "--- 2. 连接数 ---"
mysql -u$MYSQL_USER -p$MYSQL_PASS -e "
    SELECT 
        (SELECT variable_value FROM performance_schema.global_status WHERE variable_name='Threads_connected') as connected,
        (SELECT variable_value FROM performance_schema.global_variables WHERE variable_name='max_connections') as max_conn
" 2>/dev/null
echo ""

echo "--- 3. 慢查询数 ---"
mysql -u$MYSQL_USER -p$MYSQL_PASS -e "SHOW GLOBAL STATUS LIKE 'Slow_queries'" 2>/dev/null
echo ""

echo "--- 4. 运行中的查询 ---"
mysql -u$MYSQL_USER -p$MYSQL_PASS -e "
    SELECT id, user, host, db, time, state, LEFT(info, 60) as query 
    FROM information_schema.processlist 
    WHERE command != 'Sleep' 
    ORDER BY time DESC 
    LIMIT 10
" 2>/dev/null
echo ""

echo "--- 5. 锁等待 ---"
mysql -u$MYSQL_USER -p$MYSQL_PASS -e "SELECT * FROM information_schema.innodb_lock_waits" 2>/dev/null || echo "无锁等待"
echo ""

echo "===== 诊断完成 ====="
```

### PostgreSQL诊断脚本

```bash
#!/bin/bash
# pg_diagnose.sh

export PGPASSWORD="password"
PGUSER="postgres"
PGHOST="localhost"

echo "===== PostgreSQL诊断报告 ====="
echo "时间: $(date)"
echo ""

echo "--- 1. 服务状态 ---"
systemctl status postgresql --no-pager | head -10
echo ""

echo "--- 2. 连接数 ---"
psql -U $PGUSER -h $PGHOST -c "
    SELECT 
        (SELECT count(*) FROM pg_stat_activity) as connected,
        (SELECT setting FROM pg_settings WHERE name='max_connections') as max_conn
"
echo ""

echo "--- 3. 活动查询 ---"
psql -U $PGUSER -h $PGHOST -c "
    SELECT pid, usename, datname, state, 
           NOW() - query_start AS duration,
           LEFT(query, 60) as query
    FROM pg_stat_activity 
    WHERE state = 'active'
    ORDER BY duration DESC
    LIMIT 10
"
echo ""

echo "--- 4. 锁等待 ---"
psql -U $PGUSER -h $PGHOST -c "
    SELECT pid, usename, query
    FROM pg_stat_activity 
    WHERE wait_event_type = 'Lock'
"
echo ""

echo "--- 5. 缓存命中率 ---"
psql -U $PGUSER -h $PGHOST -c "
    SELECT 
        ROUND(sum(heap_blks_hit) * 100.0 / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) as cache_hit_ratio
    FROM pg_statio_user_tables
"
echo ""

echo "===== 诊断完成 ====="
```

---

## 总结

### MySQL常用命令

| 任务 | 命令 |
|------|------|
| 查看连接 | `SHOW PROCESSLIST` |
| 查看状态 | `SHOW STATUS` |
| 慢查询分析 | `mysqldumpslow` |
| 执行计划 | `EXPLAIN` |
| 查看锁 | `SHOW ENGINE INNODB STATUS` |
| 杀进程 | `KILL <id>` |

### PostgreSQL常用命令

| 任务 | 命令 |
|------|------|
| 查看连接 | `SELECT * FROM pg_stat_activity` |
| 查看锁 | `SELECT * FROM pg_locks` |
| 执行计划 | `EXPLAIN ANALYZE` |
| 杀进程 | `pg_terminate_backend(pid)` |
| 表统计 | `SELECT * FROM pg_stat_user_tables` |

**排查三板斧**：
1. **连接状态** - 检查连接数和活动查询
2. **慢查询** - 分析执行计划和日志
3. **锁状态** - 检查锁等待和死锁

**关键记忆**：
1. 慢查询先看EXPLAIN
2. type=ALL说明全表扫描
3. 锁问题找blocking进程
4. 定期VACUUM/ANALYZE（PostgreSQL）

---

## 相关文章

- [上一篇：安全事件排查实战](@/articles/sre/sre-34-安全事件排查实战.md)
- [下一篇：高可用与故障切换实战](@/articles/sre/sre-36-高可用与故障切换实战.md)
