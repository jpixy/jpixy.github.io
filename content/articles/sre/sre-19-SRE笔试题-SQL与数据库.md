+++
title = "19. SRE笔试题-SQL与数据库"
date = 2026-01-21
weight = 19000
description = "SRE面试笔试题精选：SQL查询、日志分析、慢查询优化、索引设计、死锁检测，Python3完整解答"
[taxonomies]
tags = ["SRE", "面试", "Python", "笔试", "SQL", "数据库"]
+++

## 概述

数据库是SRE日常工作中的核心组件。本文收录SRE笔试中常见的SQL和数据库相关题目，涵盖日志查询、性能分析、索引优化、故障排查等场景。

**难度标记**：⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 困难

---

## 题目1：日志表Top N查询 ⭐

### 题目描述

给定一个请求日志表，查询响应时间最长的Top 10请求。

**表结构**：
```sql
CREATE TABLE request_logs (
    id BIGINT PRIMARY KEY,
    request_id VARCHAR(64),
    endpoint VARCHAR(256),
    method VARCHAR(10),
    status_code INT,
    response_time_ms INT,
    user_id VARCHAR(64),
    ip_address VARCHAR(45),
    created_at TIMESTAMP
);
```

### SQL 解答

```sql
-- 基础版：查询响应时间最长的Top 10
SELECT 
    request_id,
    endpoint,
    method,
    status_code,
    response_time_ms,
    created_at
FROM request_logs
ORDER BY response_time_ms DESC
LIMIT 10;

-- 进阶版：按端点分组，查询每个端点最慢的请求
SELECT 
    endpoint,
    MAX(response_time_ms) as max_response_time,
    AVG(response_time_ms) as avg_response_time,
    COUNT(*) as request_count
FROM request_logs
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY endpoint
ORDER BY max_response_time DESC
LIMIT 10;

-- 使用窗口函数：每个端点的Top 3慢请求
WITH ranked_requests AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY endpoint 
            ORDER BY response_time_ms DESC
        ) as rn
    FROM request_logs
    WHERE created_at >= NOW() - INTERVAL '1 hour'
)
SELECT * FROM ranked_requests WHERE rn <= 3;
```

### Python 实现

```python
import sqlite3
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SlowRequest:
    request_id: str
    endpoint: str
    response_time_ms: int
    created_at: str


def get_top_slow_requests(
    conn: sqlite3.Connection,
    limit: int = 10,
    hours: int = 1
) -> List[SlowRequest]:
    """
    获取最慢的N个请求
    """
    query = """
    SELECT request_id, endpoint, response_time_ms, created_at
    FROM request_logs
    WHERE created_at >= datetime('now', ?)
    ORDER BY response_time_ms DESC
    LIMIT ?
    """
    
    cursor = conn.execute(query, (f'-{hours} hours', limit))
    
    return [
        SlowRequest(
            request_id=row[0],
            endpoint=row[1],
            response_time_ms=row[2],
            created_at=row[3]
        )
        for row in cursor.fetchall()
    ]


def get_slow_endpoints_summary(
    conn: sqlite3.Connection,
    threshold_ms: int = 1000,
    hours: int = 1
) -> List[Dict[str, Any]]:
    """
    获取慢请求端点汇总
    """
    query = """
    SELECT 
        endpoint,
        COUNT(*) as total_requests,
        SUM(CASE WHEN response_time_ms > ? THEN 1 ELSE 0 END) as slow_requests,
        AVG(response_time_ms) as avg_response_time,
        MAX(response_time_ms) as max_response_time,
        ROUND(
            SUM(CASE WHEN response_time_ms > ? THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 
            2
        ) as slow_rate_percent
    FROM request_logs
    WHERE created_at >= datetime('now', ?)
    GROUP BY endpoint
    HAVING slow_requests > 0
    ORDER BY slow_rate_percent DESC
    """
    
    cursor = conn.execute(query, (threshold_ms, threshold_ms, f'-{hours} hours'))
    columns = [desc[0] for desc in cursor.description]
    
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
```

### 考察点
- 基础SQL查询
- ORDER BY和LIMIT
- 窗口函数
- 聚合函数

---

## 题目2：计算时间段内的错误率 ⭐⭐

### 题目描述

计算每5分钟时间窗口的错误率（5xx状态码占比）。

### SQL 解答

```sql
-- PostgreSQL版本
SELECT 
    date_trunc('minute', created_at) - 
    (EXTRACT(MINUTE FROM created_at)::int % 5) * INTERVAL '1 minute' as time_window,
    COUNT(*) as total_requests,
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as error_count,
    ROUND(
        SUM(CASE WHEN status_code >= 500 THEN 1.0 ELSE 0 END) / COUNT(*) * 100,
        2
    ) as error_rate_percent
FROM request_logs
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY time_window
ORDER BY time_window;

-- MySQL版本
SELECT 
    FROM_UNIXTIME(
        FLOOR(UNIX_TIMESTAMP(created_at) / 300) * 300
    ) as time_window,
    COUNT(*) as total_requests,
    SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as error_count,
    ROUND(
        SUM(CASE WHEN status_code >= 500 THEN 1.0 ELSE 0 END) / COUNT(*) * 100,
        2
    ) as error_rate_percent
FROM request_logs
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY time_window
ORDER BY time_window;

-- 检测错误率突增（与前一个窗口对比）
WITH window_stats AS (
    SELECT 
        date_trunc('minute', created_at) - 
        (EXTRACT(MINUTE FROM created_at)::int % 5) * INTERVAL '1 minute' as time_window,
        ROUND(
            SUM(CASE WHEN status_code >= 500 THEN 1.0 ELSE 0 END) / COUNT(*) * 100,
            2
        ) as error_rate
    FROM request_logs
    WHERE created_at >= NOW() - INTERVAL '1 hour'
    GROUP BY time_window
)
SELECT 
    time_window,
    error_rate,
    LAG(error_rate) OVER (ORDER BY time_window) as prev_error_rate,
    error_rate - LAG(error_rate) OVER (ORDER BY time_window) as rate_change
FROM window_stats
WHERE error_rate > 5  -- 只显示错误率超过5%的窗口
ORDER BY time_window;
```

### Python 实现

```python
from datetime import datetime, timedelta
from typing import List, Dict
import sqlite3

def calculate_error_rate_by_window(
    conn: sqlite3.Connection,
    window_minutes: int = 5,
    hours: int = 1
) -> List[Dict]:
    """
    按时间窗口计算错误率
    """
    query = """
    SELECT 
        strftime('%Y-%m-%d %H:', created_at) || 
        printf('%02d', (CAST(strftime('%M', created_at) AS INTEGER) / ?) * ?) || ':00' 
        as time_window,
        COUNT(*) as total_requests,
        SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as error_count
    FROM request_logs
    WHERE created_at >= datetime('now', ?)
    GROUP BY time_window
    ORDER BY time_window
    """
    
    cursor = conn.execute(query, (window_minutes, window_minutes, f'-{hours} hours'))
    
    results = []
    for row in cursor.fetchall():
        time_window, total, errors = row
        error_rate = (errors / total * 100) if total > 0 else 0
        results.append({
            'time_window': time_window,
            'total_requests': total,
            'error_count': errors,
            'error_rate_percent': round(error_rate, 2)
        })
    
    return results


def detect_error_spikes(
    conn: sqlite3.Connection,
    threshold_percent: float = 5.0,
    spike_multiplier: float = 2.0
) -> List[Dict]:
    """
    检测错误率突增
    当某窗口的错误率是前一个窗口的spike_multiplier倍以上时告警
    """
    windows = calculate_error_rate_by_window(conn)
    
    spikes = []
    for i in range(1, len(windows)):
        current = windows[i]
        previous = windows[i - 1]
        
        if current['error_rate_percent'] > threshold_percent:
            if previous['error_rate_percent'] > 0:
                ratio = current['error_rate_percent'] / previous['error_rate_percent']
                if ratio >= spike_multiplier:
                    spikes.append({
                        **current,
                        'previous_error_rate': previous['error_rate_percent'],
                        'spike_ratio': round(ratio, 2)
                    })
            elif current['error_rate_percent'] > threshold_percent:
                # 从0突增
                spikes.append({
                    **current,
                    'previous_error_rate': 0,
                    'spike_ratio': float('inf')
                })
    
    return spikes
```

### 考察点
- 时间窗口聚合
- CASE WHEN条件统计
- LAG窗口函数
- 异常检测逻辑

---

## 题目3：查找重复数据 ⭐⭐

### 题目描述

在用户表中找出可能重复的账户（相同邮箱或手机号）。

**表结构**：
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(64),
    email VARCHAR(128),
    phone VARCHAR(20),
    created_at TIMESTAMP,
    status VARCHAR(20)
);
```

### SQL 解答

```sql
-- 查找邮箱重复的用户
SELECT email, COUNT(*) as duplicate_count, 
       GROUP_CONCAT(id) as user_ids
FROM users
WHERE email IS NOT NULL AND email != ''
GROUP BY email
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- 查找邮箱或手机号重复的用户（更复杂的场景）
WITH duplicates AS (
    SELECT 
        u1.id as user1_id,
        u2.id as user2_id,
        CASE 
            WHEN u1.email = u2.email THEN 'email'
            WHEN u1.phone = u2.phone THEN 'phone'
        END as duplicate_type,
        COALESCE(u1.email, u1.phone) as duplicate_value
    FROM users u1
    JOIN users u2 ON u1.id < u2.id  -- 避免重复配对
    WHERE 
        (u1.email = u2.email AND u1.email IS NOT NULL AND u1.email != '')
        OR 
        (u1.phone = u2.phone AND u1.phone IS NOT NULL AND u1.phone != '')
)
SELECT * FROM duplicates;

-- 保留最早创建的账户，标记其他为重复
WITH ranked_users AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY email 
            ORDER BY created_at ASC
        ) as rn
    FROM users
    WHERE email IS NOT NULL AND email != ''
)
SELECT id, email, created_at, 
       CASE WHEN rn = 1 THEN 'keep' ELSE 'duplicate' END as action
FROM ranked_users
WHERE email IN (
    SELECT email FROM users 
    WHERE email IS NOT NULL AND email != ''
    GROUP BY email HAVING COUNT(*) > 1
);
```

### Python 实现

```python
from collections import defaultdict
from typing import List, Dict, Set, Tuple

def find_duplicates_by_field(
    conn,
    table: str,
    field: str
) -> Dict[str, List[int]]:
    """
    按字段查找重复记录
    返回: {field_value: [id1, id2, ...]}
    """
    query = f"""
    SELECT {field}, GROUP_CONCAT(id) as ids
    FROM {table}
    WHERE {field} IS NOT NULL AND {field} != ''
    GROUP BY {field}
    HAVING COUNT(*) > 1
    """
    
    cursor = conn.execute(query)
    
    duplicates = {}
    for row in cursor.fetchall():
        field_value = row[0]
        ids = [int(x) for x in row[1].split(',')]
        duplicates[field_value] = ids
    
    return duplicates


def find_similar_records(
    records: List[Dict],
    fields: List[str],
    similarity_threshold: float = 0.8
) -> List[Tuple[int, int, str, float]]:
    """
    使用编辑距离查找相似记录（模糊匹配）
    返回: [(id1, id2, field, similarity), ...]
    """
    def levenshtein_ratio(s1: str, s2: str) -> float:
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        if len1 < len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1
        
        distances = range(len2 + 1)
        for i, c1 in enumerate(s1):
            new_distances = [i + 1]
            for j, c2 in enumerate(s2):
                if c1 == c2:
                    new_distances.append(distances[j])
                else:
                    new_distances.append(1 + min(
                        distances[j], distances[j + 1], new_distances[-1]
                    ))
            distances = new_distances
        
        max_len = max(len1, len2)
        return 1 - distances[-1] / max_len
    
    similar_pairs = []
    
    for i, r1 in enumerate(records):
        for j, r2 in enumerate(records[i + 1:], i + 1):
            for field in fields:
                v1 = str(r1.get(field, ''))
                v2 = str(r2.get(field, ''))
                
                if v1 and v2:
                    similarity = levenshtein_ratio(v1.lower(), v2.lower())
                    if similarity >= similarity_threshold:
                        similar_pairs.append((
                            r1['id'], r2['id'], field, round(similarity, 3)
                        ))
    
    return similar_pairs


class DeduplicationStrategy:
    """
    数据去重策略
    """
    
    @staticmethod
    def keep_earliest(records: List[Dict]) -> Dict:
        """保留创建时间最早的记录"""
        return min(records, key=lambda x: x.get('created_at', ''))
    
    @staticmethod
    def keep_most_complete(records: List[Dict], fields: List[str]) -> Dict:
        """保留字段最完整的记录"""
        def completeness(record):
            return sum(1 for f in fields if record.get(f))
        
        return max(records, key=completeness)
    
    @staticmethod
    def keep_latest_active(records: List[Dict]) -> Dict:
        """保留最近活跃且状态为active的记录"""
        active_records = [r for r in records if r.get('status') == 'active']
        if active_records:
            return max(active_records, key=lambda x: x.get('last_login', ''))
        return max(records, key=lambda x: x.get('last_login', ''))
```

### 考察点
- GROUP BY和HAVING
- 自连接查找
- 窗口函数去重
- 模糊匹配算法

---

## 题目4：死锁检测与分析 ⭐⭐⭐

### 题目描述

给定数据库锁等待信息，检测是否存在死锁，如果存在，找出死锁链。

### Python 实现

```python
from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

@dataclass
class LockInfo:
    transaction_id: str
    lock_type: str  # 'HOLDING' or 'WAITING'
    resource_id: str
    timestamp: float


class DeadlockDetector:
    """
    死锁检测器
    使用有向图检测环
    """
    
    def __init__(self):
        # transaction_id -> set of resources it's holding
        self.holdings: Dict[str, Set[str]] = defaultdict(set)
        # transaction_id -> set of resources it's waiting for
        self.waitings: Dict[str, Set[str]] = defaultdict(set)
        # resource_id -> transaction_id holding it
        self.resource_holders: Dict[str, str] = {}
    
    def add_lock(self, lock: LockInfo):
        """添加锁信息"""
        if lock.lock_type == 'HOLDING':
            self.holdings[lock.transaction_id].add(lock.resource_id)
            self.resource_holders[lock.resource_id] = lock.transaction_id
        elif lock.lock_type == 'WAITING':
            self.waitings[lock.transaction_id].add(lock.resource_id)
    
    def build_wait_graph(self) -> Dict[str, Set[str]]:
        """
        构建等待图
        节点：事务ID
        边：事务A等待事务B持有的资源 => A -> B
        """
        graph = defaultdict(set)
        
        for txn, waiting_resources in self.waitings.items():
            for resource in waiting_resources:
                holder = self.resource_holders.get(resource)
                if holder and holder != txn:
                    graph[txn].add(holder)
        
        return graph
    
    def detect_deadlock(self) -> Optional[List[str]]:
        """
        检测死锁（环）
        使用DFS检测有向图中的环
        返回死锁链，如果没有返回None
        """
        graph = self.build_wait_graph()
        
        if not graph:
            return None
        
        # DFS检测环
        WHITE, GRAY, BLACK = 0, 1, 2
        color = defaultdict(int)
        parent = {}
        
        def dfs(node: str) -> Optional[List[str]]:
            color[node] = GRAY
            
            for neighbor in graph.get(node, []):
                if color[neighbor] == GRAY:
                    # 找到环，回溯构建死锁链
                    cycle = [neighbor]
                    current = node
                    while current != neighbor:
                        cycle.append(current)
                        current = parent.get(current)
                        if current is None:
                            break
                    cycle.append(neighbor)
                    return list(reversed(cycle))
                
                if color[neighbor] == WHITE:
                    parent[neighbor] = node
                    result = dfs(neighbor)
                    if result:
                        return result
            
            color[node] = BLACK
            return None
        
        # 对所有节点进行DFS
        all_nodes = set(graph.keys())
        for txn in self.waitings:
            all_nodes.add(txn)
        
        for node in all_nodes:
            if color[node] == WHITE:
                result = dfs(node)
                if result:
                    return result
        
        return None
    
    def get_deadlock_details(self) -> Optional[Dict]:
        """
        获取死锁详细信息
        """
        cycle = self.detect_deadlock()
        
        if not cycle:
            return None
        
        details = {
            'deadlock_detected': True,
            'transactions_involved': cycle,
            'wait_chain': []
        }
        
        for i in range(len(cycle) - 1):
            txn = cycle[i]
            next_txn = cycle[i + 1]
            
            # 找出txn等待的、被next_txn持有的资源
            waiting = self.waitings.get(txn, set())
            holding = self.holdings.get(next_txn, set())
            blocked_resource = waiting & holding
            
            details['wait_chain'].append({
                'transaction': txn,
                'waiting_for': list(blocked_resource),
                'blocked_by': next_txn
            })
        
        return details
    
    def suggest_victim(self) -> Optional[str]:
        """
        建议回滚哪个事务来解除死锁
        选择持有资源最少的事务
        """
        cycle = self.detect_deadlock()
        
        if not cycle:
            return None
        
        # 移除最后一个元素（与第一个重复）
        transactions = cycle[:-1]
        
        # 选择持有资源最少的事务
        return min(
            transactions,
            key=lambda txn: len(self.holdings.get(txn, set()))
        )


# 从数据库查询锁信息
def get_lock_info_mysql(conn) -> List[LockInfo]:
    """
    从MySQL获取锁信息
    """
    query = """
    SELECT 
        r.trx_id as waiting_trx,
        r.trx_mysql_thread_id as waiting_thread,
        b.trx_id as blocking_trx,
        b.trx_mysql_thread_id as blocking_thread,
        l.lock_table as locked_table,
        l.lock_index as locked_index
    FROM information_schema.innodb_lock_waits w
    JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
    JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id
    JOIN information_schema.innodb_locks l ON l.lock_id = w.requested_lock_id
    """
    # 解析并返回LockInfo列表
    pass


def get_lock_info_postgres(conn) -> List[LockInfo]:
    """
    从PostgreSQL获取锁信息
    """
    query = """
    SELECT 
        blocked_locks.pid AS blocked_pid,
        blocked_activity.usename AS blocked_user,
        blocking_locks.pid AS blocking_pid,
        blocking_activity.usename AS blocking_user,
        blocked_activity.query AS blocked_query
    FROM pg_catalog.pg_locks blocked_locks
    JOIN pg_catalog.pg_stat_activity blocked_activity 
        ON blocked_activity.pid = blocked_locks.pid
    JOIN pg_catalog.pg_locks blocking_locks 
        ON blocking_locks.locktype = blocked_locks.locktype
        AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
        AND blocking_locks.pid != blocked_locks.pid
    JOIN pg_catalog.pg_stat_activity blocking_activity 
        ON blocking_activity.pid = blocking_locks.pid
    WHERE NOT blocked_locks.granted
    """
    # 解析并返回LockInfo列表
    pass
```

### 考察点
- 图论（环检测）
- DFS算法
- 数据库锁机制
- 系统表查询

---

## 题目5：慢查询分析 ⭐⭐

### 题目描述

分析慢查询日志，找出需要优化的查询。

**慢查询日志表**：
```sql
CREATE TABLE slow_query_log (
    id BIGINT PRIMARY KEY,
    query_text TEXT,
    query_hash VARCHAR(64),
    execution_time_ms INT,
    rows_examined BIGINT,
    rows_sent BIGINT,
    created_at TIMESTAMP,
    user VARCHAR(64),
    db_name VARCHAR(64)
);
```

### SQL 解答

```sql
-- 按查询模式分组统计
SELECT 
    query_hash,
    SUBSTRING(query_text, 1, 100) as query_sample,
    COUNT(*) as execution_count,
    AVG(execution_time_ms) as avg_time_ms,
    MAX(execution_time_ms) as max_time_ms,
    SUM(execution_time_ms) as total_time_ms,
    AVG(rows_examined) as avg_rows_examined,
    AVG(rows_sent) as avg_rows_sent,
    -- 效率指标：检查行数/返回行数
    ROUND(AVG(rows_examined * 1.0 / NULLIF(rows_sent, 0)), 2) as scan_ratio
FROM slow_query_log
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY query_hash, query_sample
ORDER BY total_time_ms DESC
LIMIT 20;

-- 找出全表扫描的查询（检查行数远大于返回行数）
SELECT 
    query_hash,
    query_text,
    execution_time_ms,
    rows_examined,
    rows_sent,
    ROUND(rows_examined * 1.0 / NULLIF(rows_sent, 0), 2) as scan_ratio
FROM slow_query_log
WHERE rows_examined > 10000
  AND rows_sent < 100
  AND rows_examined > rows_sent * 100
ORDER BY rows_examined DESC
LIMIT 20;

-- 识别最近变慢的查询（对比今天和昨天）
WITH today_stats AS (
    SELECT 
        query_hash,
        AVG(execution_time_ms) as avg_time
    FROM slow_query_log
    WHERE created_at >= CURRENT_DATE
    GROUP BY query_hash
),
yesterday_stats AS (
    SELECT 
        query_hash,
        AVG(execution_time_ms) as avg_time
    FROM slow_query_log
    WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
      AND created_at < CURRENT_DATE
    GROUP BY query_hash
)
SELECT 
    t.query_hash,
    y.avg_time as yesterday_avg_ms,
    t.avg_time as today_avg_ms,
    ROUND((t.avg_time - y.avg_time) / y.avg_time * 100, 2) as increase_percent
FROM today_stats t
JOIN yesterday_stats y ON t.query_hash = y.query_hash
WHERE t.avg_time > y.avg_time * 1.5  -- 慢了50%以上
ORDER BY increase_percent DESC;
```

### Python 实现

```python
import re
from collections import defaultdict
from typing import List, Dict, Tuple
from dataclasses import dataclass
import hashlib

@dataclass
class SlowQuery:
    query_text: str
    execution_time_ms: int
    rows_examined: int
    rows_sent: int
    timestamp: str


class SlowQueryAnalyzer:
    """
    慢查询分析器
    """
    
    def __init__(self):
        self.queries: List[SlowQuery] = []
    
    def add_query(self, query: SlowQuery):
        self.queries.append(query)
    
    def normalize_query(self, query: str) -> str:
        """
        标准化查询（去除具体值，保留结构）
        用于相似查询分组
        """
        # 替换数字
        normalized = re.sub(r'\b\d+\b', '?', query)
        # 替换字符串
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        normalized = re.sub(r'"[^"]*"', '"?"', normalized)
        # 替换IN列表
        normalized = re.sub(r'IN\s*\([^)]+\)', 'IN (?)', normalized, flags=re.IGNORECASE)
        # 压缩空白
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def get_query_hash(self, query: str) -> str:
        """计算查询哈希"""
        normalized = self.normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def analyze(self) -> Dict:
        """
        分析慢查询
        """
        # 按查询模式分组
        grouped = defaultdict(list)
        for q in self.queries:
            query_hash = self.get_query_hash(q.query_text)
            grouped[query_hash].append(q)
        
        # 计算统计信息
        analysis = []
        for query_hash, queries in grouped.items():
            times = [q.execution_time_ms for q in queries]
            rows_examined = [q.rows_examined for q in queries]
            rows_sent = [q.rows_sent for q in queries]
            
            avg_scan_ratio = sum(
                e / s if s > 0 else e 
                for e, s in zip(rows_examined, rows_sent)
            ) / len(queries)
            
            analysis.append({
                'query_hash': query_hash,
                'query_sample': self.normalize_query(queries[0].query_text)[:200],
                'count': len(queries),
                'avg_time_ms': sum(times) / len(times),
                'max_time_ms': max(times),
                'total_time_ms': sum(times),
                'avg_rows_examined': sum(rows_examined) / len(rows_examined),
                'avg_rows_sent': sum(rows_sent) / len(rows_sent),
                'avg_scan_ratio': round(avg_scan_ratio, 2),
                'optimization_priority': self._calculate_priority(
                    len(queries), sum(times), avg_scan_ratio
                )
            })
        
        # 按优先级排序
        analysis.sort(key=lambda x: x['optimization_priority'], reverse=True)
        
        return {
            'total_slow_queries': len(self.queries),
            'unique_patterns': len(grouped),
            'top_queries': analysis[:20],
            'recommendations': self._generate_recommendations(analysis[:10])
        }
    
    def _calculate_priority(
        self, 
        count: int, 
        total_time: int, 
        scan_ratio: float
    ) -> float:
        """
        计算优化优先级
        考虑：执行次数、总耗时、扫描比率
        """
        # 加权计算
        count_score = min(count / 100, 1.0) * 30
        time_score = min(total_time / 100000, 1.0) * 40
        scan_score = min(scan_ratio / 1000, 1.0) * 30
        
        return count_score + time_score + scan_score
    
    def _generate_recommendations(self, top_queries: List[Dict]) -> List[Dict]:
        """
        生成优化建议
        """
        recommendations = []
        
        for q in top_queries:
            query_sample = q['query_sample'].upper()
            recs = []
            
            # 高扫描比率 -> 可能需要索引
            if q['avg_scan_ratio'] > 100:
                recs.append({
                    'type': 'index',
                    'message': f"高扫描比率({q['avg_scan_ratio']})，考虑添加索引"
                })
            
            # 检查常见问题模式
            if 'SELECT *' in query_sample:
                recs.append({
                    'type': 'select_star',
                    'message': "避免SELECT *，只查询需要的列"
                })
            
            if 'LIKE' in query_sample and "'%" in query_sample:
                recs.append({
                    'type': 'leading_wildcard',
                    'message': "LIKE以%开头无法使用索引"
                })
            
            if 'ORDER BY' in query_sample and 'LIMIT' not in query_sample:
                recs.append({
                    'type': 'unbounded_sort',
                    'message': "ORDER BY没有LIMIT可能导致大量排序"
                })
            
            if q['count'] > 100 and q['avg_time_ms'] > 100:
                recs.append({
                    'type': 'high_impact',
                    'message': f"高频慢查询，优化收益大"
                })
            
            if recs:
                recommendations.append({
                    'query_hash': q['query_hash'],
                    'query_sample': q['query_sample'][:100],
                    'recommendations': recs
                })
        
        return recommendations


def explain_query_analysis(explain_output: str) -> Dict:
    """
    分析EXPLAIN输出
    """
    issues = []
    
    if 'full table scan' in explain_output.lower() or 'ALL' in explain_output:
        issues.append({
            'type': 'full_scan',
            'severity': 'high',
            'message': '全表扫描，考虑添加索引'
        })
    
    if 'filesort' in explain_output.lower():
        issues.append({
            'type': 'filesort',
            'severity': 'medium',
            'message': '使用了文件排序，考虑优化ORDER BY'
        })
    
    if 'temporary' in explain_output.lower():
        issues.append({
            'type': 'temp_table',
            'severity': 'medium',
            'message': '使用了临时表，考虑优化GROUP BY'
        })
    
    if 'using index' in explain_output.lower():
        issues.append({
            'type': 'covering_index',
            'severity': 'info',
            'message': '使用了覆盖索引，性能较好'
        })
    
    return {
        'issues': issues,
        'needs_optimization': any(i['severity'] == 'high' for i in issues)
    }
```

### 考察点
- 查询性能分析
- 统计聚合
- 模式识别
- 优化建议生成

---

## 题目6：索引设计与分析 ⭐⭐⭐

### 题目描述

给定一组查询模式，设计最优的索引方案。

### Python 实现

```python
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
from collections import defaultdict
import re

@dataclass
class QueryPattern:
    query: str
    frequency: int  # 每天执行次数
    avg_time_ms: float


@dataclass
class IndexSuggestion:
    table: str
    columns: List[str]
    index_type: str  # 'btree', 'hash', 'fulltext'
    estimated_improvement: float
    reason: str


class IndexAdvisor:
    """
    索引优化建议器
    """
    
    def __init__(self):
        self.queries: List[QueryPattern] = []
        self.existing_indexes: Dict[str, List[List[str]]] = defaultdict(list)
    
    def add_query(self, pattern: QueryPattern):
        self.queries.append(pattern)
    
    def add_existing_index(self, table: str, columns: List[str]):
        self.existing_indexes[table].append(columns)
    
    def parse_query(self, query: str) -> Dict:
        """
        解析查询，提取表名和使用的列
        """
        query = query.upper()
        
        result = {
            'tables': [],
            'where_columns': [],
            'join_columns': [],
            'order_columns': [],
            'group_columns': []
        }
        
        # 提取表名（简化版）
        from_match = re.search(r'FROM\s+(\w+)', query)
        if from_match:
            result['tables'].append(from_match.group(1).lower())
        
        join_matches = re.findall(r'JOIN\s+(\w+)', query)
        result['tables'].extend([t.lower() for t in join_matches])
        
        # 提取WHERE条件中的列
        where_match = re.search(r'WHERE\s+(.+?)(?:ORDER|GROUP|LIMIT|$)', query, re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            # 提取列名（简化：只匹配 column = 或 column > 等模式）
            columns = re.findall(r'(\w+)\s*[=<>!]', where_clause)
            result['where_columns'] = [c.lower() for c in columns]
        
        # 提取ORDER BY列
        order_match = re.search(r'ORDER\s+BY\s+([\w\s,]+)', query)
        if order_match:
            columns = re.findall(r'(\w+)', order_match.group(1))
            result['order_columns'] = [c.lower() for c in columns]
        
        # 提取GROUP BY列
        group_match = re.search(r'GROUP\s+BY\s+([\w\s,]+)', query)
        if group_match:
            columns = re.findall(r'(\w+)', group_match.group(1))
            result['group_columns'] = [c.lower() for c in columns]
        
        return result
    
    def is_index_covered(self, table: str, columns: List[str]) -> bool:
        """
        检查是否已有索引覆盖这些列
        """
        for existing in self.existing_indexes.get(table, []):
            # 前缀匹配
            if columns == existing[:len(columns)]:
                return True
        return False
    
    def analyze(self) -> List[IndexSuggestion]:
        """
        分析所有查询，生成索引建议
        """
        # 收集所有查询使用的列
        column_usage = defaultdict(lambda: defaultdict(int))
        
        for pattern in self.queries:
            parsed = self.parse_query(pattern.query)
            
            for table in parsed['tables']:
                # WHERE条件列最重要
                for col in parsed['where_columns']:
                    column_usage[table][col] += pattern.frequency * 3
                
                # ORDER BY列
                for col in parsed['order_columns']:
                    column_usage[table][col] += pattern.frequency * 2
                
                # GROUP BY列
                for col in parsed['group_columns']:
                    column_usage[table][col] += pattern.frequency * 2
        
        # 生成建议
        suggestions = []
        
        for table, columns in column_usage.items():
            # 按使用频率排序
            sorted_columns = sorted(
                columns.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # 取前3个最常用的列作为复合索引
            top_columns = [col for col, _ in sorted_columns[:3]]
            
            if not self.is_index_covered(table, top_columns):
                suggestions.append(IndexSuggestion(
                    table=table,
                    columns=top_columns,
                    index_type='btree',
                    estimated_improvement=self._estimate_improvement(
                        table, top_columns
                    ),
                    reason=f"高频使用的列: {', '.join(top_columns)}"
                ))
            
            # 单列索引建议（针对选择性高的列）
            for col, freq in sorted_columns:
                if freq > 100 and not self.is_index_covered(table, [col]):
                    suggestions.append(IndexSuggestion(
                        table=table,
                        columns=[col],
                        index_type='btree',
                        estimated_improvement=self._estimate_improvement(
                            table, [col]
                        ),
                        reason=f"高频过滤列，使用频率: {freq}"
                    ))
        
        # 按预期收益排序
        suggestions.sort(key=lambda x: x.estimated_improvement, reverse=True)
        
        return suggestions
    
    def _estimate_improvement(self, table: str, columns: List[str]) -> float:
        """
        估算索引带来的性能提升
        """
        # 简化的估算逻辑
        # 实际应该根据表大小、数据分布等计算
        total_impact = 0
        
        for pattern in self.queries:
            parsed = self.parse_query(pattern.query)
            
            if table.upper() in [t.upper() for t in parsed['tables']]:
                # 检查索引列是否被查询使用
                query_columns = set(
                    parsed['where_columns'] + 
                    parsed['order_columns'] + 
                    parsed['group_columns']
                )
                
                coverage = len(set(columns) & query_columns) / len(columns)
                impact = pattern.frequency * pattern.avg_time_ms * coverage * 0.5
                total_impact += impact
        
        return round(total_impact, 2)
    
    def generate_ddl(self, suggestions: List[IndexSuggestion]) -> List[str]:
        """
        生成创建索引的DDL语句
        """
        ddl_statements = []
        
        for i, suggestion in enumerate(suggestions):
            index_name = f"idx_{suggestion.table}_{'_'.join(suggestion.columns[:2])}"
            columns_str = ', '.join(suggestion.columns)
            
            ddl = f"CREATE INDEX {index_name} ON {suggestion.table} ({columns_str});"
            ddl_statements.append(ddl)
        
        return ddl_statements


# 使用示例
advisor = IndexAdvisor()

# 添加现有索引
advisor.add_existing_index('orders', ['user_id'])
advisor.add_existing_index('orders', ['created_at'])

# 添加查询模式
advisor.add_query(QueryPattern(
    query="SELECT * FROM orders WHERE user_id = ? AND status = ? ORDER BY created_at",
    frequency=10000,
    avg_time_ms=50
))
advisor.add_query(QueryPattern(
    query="SELECT * FROM orders WHERE created_at >= ? AND created_at < ?",
    frequency=500,
    avg_time_ms=200
))

# 分析并生成建议
suggestions = advisor.analyze()
ddl = advisor.generate_ddl(suggestions)
```

### 考察点
- 索引原理
- 查询解析
- 复合索引设计
- 成本估算

---

## 题目7：数据库容量预测 ⭐⭐

### 题目描述

根据历史数据增长趋势，预测数据库何时会达到容量限制。

### Python 实现

```python
from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import math

@dataclass
class StorageDataPoint:
    timestamp: datetime
    used_bytes: int
    total_bytes: int


class CapacityPredictor:
    """
    数据库容量预测器
    """
    
    def __init__(self, data_points: List[StorageDataPoint]):
        self.data_points = sorted(data_points, key=lambda x: x.timestamp)
    
    def linear_regression(self) -> Tuple[float, float]:
        """
        线性回归计算增长趋势
        返回: (斜率, 截距)
        """
        n = len(self.data_points)
        if n < 2:
            return 0, 0
        
        # 使用时间戳作为x
        base_time = self.data_points[0].timestamp.timestamp()
        x = [(p.timestamp.timestamp() - base_time) / 86400 for p in self.data_points]  # 天数
        y = [p.used_bytes for p in self.data_points]
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        # 斜率 (bytes per day)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2 + 1e-10)
        # 截距
        intercept = (sum_y - slope * sum_x) / n
        
        return slope, intercept
    
    def predict_usage(self, days_ahead: int) -> int:
        """
        预测未来某天的使用量
        """
        slope, intercept = self.linear_regression()
        
        # 当前天数
        base_time = self.data_points[0].timestamp.timestamp()
        current_days = (self.data_points[-1].timestamp.timestamp() - base_time) / 86400
        
        future_days = current_days + days_ahead
        predicted = intercept + slope * future_days
        
        return max(0, int(predicted))
    
    def days_until_full(self, threshold_percent: float = 90) -> Optional[int]:
        """
        预测多少天后达到阈值
        """
        if not self.data_points:
            return None
        
        slope, intercept = self.linear_regression()
        
        if slope <= 0:
            return None  # 没有增长或在减少
        
        total_bytes = self.data_points[-1].total_bytes
        threshold_bytes = total_bytes * threshold_percent / 100
        
        # 当前天数
        base_time = self.data_points[0].timestamp.timestamp()
        current_days = (self.data_points[-1].timestamp.timestamp() - base_time) / 86400
        
        # 解方程: threshold = intercept + slope * x
        days_to_threshold = (threshold_bytes - intercept) / slope
        remaining_days = days_to_threshold - current_days
        
        return max(0, int(remaining_days))
    
    def growth_rate(self) -> Dict:
        """
        计算增长率统计
        """
        slope, _ = self.linear_regression()
        
        current_usage = self.data_points[-1].used_bytes
        total = self.data_points[-1].total_bytes
        
        return {
            'daily_growth_bytes': int(slope),
            'daily_growth_gb': round(slope / (1024 ** 3), 3),
            'weekly_growth_gb': round(slope * 7 / (1024 ** 3), 2),
            'monthly_growth_gb': round(slope * 30 / (1024 ** 3), 2),
            'current_usage_percent': round(current_usage / total * 100, 2),
            'growth_rate_percent_per_day': round(slope / current_usage * 100, 4) if current_usage > 0 else 0
        }
    
    def generate_report(self) -> Dict:
        """
        生成完整的容量报告
        """
        current = self.data_points[-1]
        growth = self.growth_rate()
        
        return {
            'current_status': {
                'used_gb': round(current.used_bytes / (1024 ** 3), 2),
                'total_gb': round(current.total_bytes / (1024 ** 3), 2),
                'usage_percent': round(current.used_bytes / current.total_bytes * 100, 2),
                'free_gb': round((current.total_bytes - current.used_bytes) / (1024 ** 3), 2)
            },
            'growth_trend': growth,
            'predictions': {
                'usage_7_days': self.predict_usage(7) / (1024 ** 3),
                'usage_30_days': self.predict_usage(30) / (1024 ** 3),
                'usage_90_days': self.predict_usage(90) / (1024 ** 3),
                'days_until_80_percent': self.days_until_full(80),
                'days_until_90_percent': self.days_until_full(90),
                'days_until_95_percent': self.days_until_full(95)
            },
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """
        生成容量管理建议
        """
        recommendations = []
        
        current = self.data_points[-1]
        usage_percent = current.used_bytes / current.total_bytes * 100
        days_to_90 = self.days_until_full(90)
        
        if usage_percent > 85:
            recommendations.append("紧急：当前使用率超过85%，建议立即扩容")
        elif usage_percent > 75:
            recommendations.append("警告：当前使用率超过75%，计划扩容")
        
        if days_to_90 is not None:
            if days_to_90 < 30:
                recommendations.append(f"预计{days_to_90}天后达到90%容量，需要尽快扩容")
            elif days_to_90 < 90:
                recommendations.append(f"预计{days_to_90}天后达到90%容量，建议规划扩容")
        
        growth = self.growth_rate()
        if growth['growth_rate_percent_per_day'] > 1:
            recommendations.append("数据增长较快，考虑数据归档或清理策略")
        
        return recommendations


# SQL查询获取历史存储数据
def get_storage_history_postgres(conn, days: int = 30) -> List[StorageDataPoint]:
    """
    从PostgreSQL获取存储历史
    """
    query = """
    SELECT 
        date_trunc('day', snapshot_time) as day,
        MAX(pg_database_size(current_database())) as used_bytes,
        -- 假设总容量从配置表获取
        (SELECT setting::bigint FROM pg_settings WHERE name = 'data_directory_size_limit') as total_bytes
    FROM storage_snapshots
    WHERE snapshot_time >= NOW() - INTERVAL '%s days'
    GROUP BY day
    ORDER BY day
    """
    # 解析并返回数据点
    pass


def get_storage_history_mysql(conn, days: int = 30) -> List[StorageDataPoint]:
    """
    从MySQL获取存储历史
    """
    query = """
    SELECT 
        DATE(created_at) as day,
        SUM(data_length + index_length) as used_bytes
    FROM information_schema.tables
    WHERE table_schema = DATABASE()
    GROUP BY day
    ORDER BY day
    """
    # 解析并返回数据点
    pass
```

### 考察点
- 线性回归
- 容量规划
- 趋势预测
- 报告生成

---

## 题目8：数据一致性检查 ⭐⭐⭐

### 题目描述

检查主从数据库之间的数据一致性。

### Python 实现

```python
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
import hashlib
from concurrent.futures import ThreadPoolExecutor

@dataclass
class ConsistencyCheckResult:
    table: str
    is_consistent: bool
    master_count: int
    slave_count: int
    missing_in_slave: List[str]  # primary keys
    missing_in_master: List[str]
    different_rows: List[str]
    check_duration_ms: float


class DataConsistencyChecker:
    """
    主从数据一致性检查器
    """
    
    def __init__(self, master_conn, slave_conn):
        self.master = master_conn
        self.slave = slave_conn
    
    def get_table_checksum(self, conn, table: str) -> str:
        """
        计算表的校验和
        """
        # MySQL
        query = f"CHECKSUM TABLE {table}"
        cursor = conn.execute(query)
        result = cursor.fetchone()
        return str(result[1]) if result else ""
    
    def quick_check(self, table: str) -> bool:
        """
        快速检查：比较行数和校验和
        """
        # 比较行数
        master_count = self._get_row_count(self.master, table)
        slave_count = self._get_row_count(self.slave, table)
        
        if master_count != slave_count:
            return False
        
        # 比较校验和
        master_checksum = self.get_table_checksum(self.master, table)
        slave_checksum = self.get_table_checksum(self.slave, table)
        
        return master_checksum == slave_checksum
    
    def _get_row_count(self, conn, table: str) -> int:
        query = f"SELECT COUNT(*) FROM {table}"
        cursor = conn.execute(query)
        return cursor.fetchone()[0]
    
    def detailed_check(
        self, 
        table: str, 
        primary_key: str,
        columns: List[str] = None,
        batch_size: int = 10000
    ) -> ConsistencyCheckResult:
        """
        详细检查：逐行比较
        """
        import time
        start_time = time.time()
        
        # 获取所有主键
        master_keys = self._get_all_keys(self.master, table, primary_key)
        slave_keys = self._get_all_keys(self.slave, table, primary_key)
        
        # 找出差异
        missing_in_slave = list(master_keys - slave_keys)
        missing_in_master = list(slave_keys - master_keys)
        
        # 比较共有行的数据
        common_keys = master_keys & slave_keys
        different_rows = []
        
        # 分批比较
        common_keys_list = list(common_keys)
        for i in range(0, len(common_keys_list), batch_size):
            batch = common_keys_list[i:i + batch_size]
            diff = self._compare_rows(table, primary_key, batch, columns)
            different_rows.extend(diff)
        
        duration = (time.time() - start_time) * 1000
        
        return ConsistencyCheckResult(
            table=table,
            is_consistent=(
                len(missing_in_slave) == 0 and 
                len(missing_in_master) == 0 and 
                len(different_rows) == 0
            ),
            master_count=len(master_keys),
            slave_count=len(slave_keys),
            missing_in_slave=missing_in_slave[:100],  # 限制返回数量
            missing_in_master=missing_in_master[:100],
            different_rows=different_rows[:100],
            check_duration_ms=duration
        )
    
    def _get_all_keys(self, conn, table: str, primary_key: str) -> Set[str]:
        query = f"SELECT {primary_key} FROM {table}"
        cursor = conn.execute(query)
        return {str(row[0]) for row in cursor.fetchall()}
    
    def _compare_rows(
        self, 
        table: str, 
        primary_key: str,
        keys: List[str],
        columns: List[str] = None
    ) -> List[str]:
        """
        比较指定行的数据
        返回不一致的主键列表
        """
        if not keys:
            return []
        
        columns_str = ', '.join(columns) if columns else '*'
        keys_str = ', '.join(f"'{k}'" for k in keys)
        
        query = f"""
        SELECT {primary_key}, MD5(CONCAT_WS(',', {columns_str})) as row_hash
        FROM {table}
        WHERE {primary_key} IN ({keys_str})
        """
        
        # 获取主库哈希
        master_hashes = {}
        cursor = self.master.execute(query)
        for row in cursor.fetchall():
            master_hashes[str(row[0])] = row[1]
        
        # 获取从库哈希
        slave_hashes = {}
        cursor = self.slave.execute(query)
        for row in cursor.fetchall():
            slave_hashes[str(row[0])] = row[1]
        
        # 找出不一致的行
        different = []
        for key in keys:
            if master_hashes.get(key) != slave_hashes.get(key):
                different.append(key)
        
        return different
    
    def check_all_tables(self, tables: List[str] = None) -> Dict[str, ConsistencyCheckResult]:
        """
        检查所有表
        """
        if tables is None:
            # 获取所有表
            query = "SHOW TABLES"
            cursor = self.master.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
        
        results = {}
        for table in tables:
            # 先快速检查
            if self.quick_check(table):
                results[table] = ConsistencyCheckResult(
                    table=table,
                    is_consistent=True,
                    master_count=self._get_row_count(self.master, table),
                    slave_count=self._get_row_count(self.slave, table),
                    missing_in_slave=[],
                    missing_in_master=[],
                    different_rows=[],
                    check_duration_ms=0
                )
            else:
                # 详细检查
                # 需要获取主键信息
                pk = self._get_primary_key(table)
                results[table] = self.detailed_check(table, pk)
        
        return results
    
    def _get_primary_key(self, table: str) -> str:
        """获取表的主键"""
        query = f"""
        SELECT COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_NAME = '{table}'
          AND CONSTRAINT_NAME = 'PRIMARY'
        """
        cursor = self.master.execute(query)
        result = cursor.fetchone()
        return result[0] if result else 'id'
    
    def generate_repair_sql(
        self, 
        result: ConsistencyCheckResult,
        primary_key: str
    ) -> List[str]:
        """
        生成修复SQL
        """
        repair_statements = []
        
        # 从主库同步缺失的数据到从库
        for pk in result.missing_in_slave:
            repair_statements.append(
                f"-- 从主库复制到从库: {result.table} WHERE {primary_key} = '{pk}'"
            )
        
        # 删除从库多余的数据
        for pk in result.missing_in_master:
            repair_statements.append(
                f"DELETE FROM {result.table} WHERE {primary_key} = '{pk}';"
            )
        
        # 更新不一致的行
        for pk in result.different_rows:
            repair_statements.append(
                f"-- 更新从库: {result.table} WHERE {primary_key} = '{pk}' 使用主库数据"
            )
        
        return repair_statements
```

### 考察点
- 数据一致性概念
- 校验和比较
- 分批处理大数据
- 修复策略

---

## 总结

| 题目 | 难度 | 核心考点 | 实际应用 |
|------|------|----------|----------|
| Top N查询 | ⭐ | ORDER BY、窗口函数 | 慢查询分析 |
| 时间窗口错误率 | ⭐⭐ | 时间聚合、CASE WHEN | 监控Dashboard |
| 重复数据检测 | ⭐⭐ | GROUP BY、自连接 | 数据治理 |
| 死锁检测 | ⭐⭐⭐ | 图论、系统表 | 故障排查 |
| 慢查询分析 | ⭐⭐ | 查询解析、统计 | 性能优化 |
| 索引设计 | ⭐⭐⭐ | 索引原理、成本估算 | 数据库调优 |
| 容量预测 | ⭐⭐ | 线性回归、预测 | 容量规划 |
| 一致性检查 | ⭐⭐⭐ | 校验和、分批比较 | 主从同步 |

**SRE数据库核心能力**：
1. 熟练编写复杂SQL查询
2. 理解执行计划和索引原理
3. 掌握性能分析和优化方法
4. 了解复制和一致性机制

---

## 相关文章

- [上一篇：SRE笔试题-监控与运维自动化](@/articles/sre/sre-18-SRE笔试题-监控与运维自动化.md)
- [下一篇：SRE笔试题-综合实战题](@/articles/sre/sre-20-SRE笔试题-综合实战题.md)
