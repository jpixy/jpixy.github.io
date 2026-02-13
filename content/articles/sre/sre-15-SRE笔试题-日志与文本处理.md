+++
title = "15. SRE笔试题-日志与文本处理"
date = 2026-01-21
weight = 15000
description = "SRE面试笔试题精选：日志分析、文本处理、正则表达式、数据统计，Python3完整解答"
[taxonomies]
tags = ["SRE", "面试", "Python", "笔试", "日志分析"]
+++

## 概述

日志分析和文本处理是SRE最常见的日常工作之一。本文收录了SRE笔试中常见的日志与文本处理题目，所有题目均使用Python3解答。

**难度标记**：⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 困难

---

## 题目1：Nginx日志Top K分析 ⭐⭐

### 题目描述

给定一个Nginx访问日志文件，每行格式如下：
```
192.168.1.1 - - [21/Jan/2026:10:00:00 +0800] "GET /api/users HTTP/1.1" 200 1234
```

请统计请求数最多的Top K个IP地址。

**输入**：
- `logs`: List[str]，日志行列表
- `k`: int，返回前k个

**输出**：
- List[Tuple[str, int]]，按请求数降序排列的(IP, 请求数)列表

### 示例

```python
logs = [
    '192.168.1.1 - - [21/Jan/2026:10:00:00 +0800] "GET /api HTTP/1.1" 200 100',
    '192.168.1.2 - - [21/Jan/2026:10:00:01 +0800] "GET /api HTTP/1.1" 200 100',
    '192.168.1.1 - - [21/Jan/2026:10:00:02 +0800] "POST /api HTTP/1.1" 201 50',
    '192.168.1.1 - - [21/Jan/2026:10:00:03 +0800] "GET /home HTTP/1.1" 200 200',
    '192.168.1.3 - - [21/Jan/2026:10:00:04 +0800] "GET /api HTTP/1.1" 500 0',
]
k = 2

# 输出: [('192.168.1.1', 3), ('192.168.1.2', 1)]
```

### Python3 解答

**方法一：使用Counter（简洁高效）**

```python
from collections import Counter
from typing import List, Tuple

def top_k_ips(logs: List[str], k: int) -> List[Tuple[str, int]]:
    """
    统计Top K IP地址
    时间复杂度: O(n + m*log(k))，n为日志数，m为不同IP数
    空间复杂度: O(m)
    """
    ip_counter = Counter()
    
    for line in logs:
        # IP地址是每行的第一个字段
        if line.strip():
            ip = line.split()[0]
            ip_counter[ip] += 1
    
    # 使用堆获取Top K，比完全排序更高效
    return ip_counter.most_common(k)
```

**方法二：使用最小堆（适合超大数据量）**

```python
import heapq
from collections import Counter
from typing import List, Tuple

def top_k_ips_heap(logs: List[str], k: int) -> List[Tuple[str, int]]:
    """
    使用最小堆实现Top K
    适合日志量极大、内存受限的场景
    """
    ip_counter = Counter()
    
    for line in logs:
        if line.strip():
            ip = line.split()[0]
            ip_counter[ip] += 1
    
    # 维护大小为k的最小堆
    min_heap = []
    for ip, count in ip_counter.items():
        if len(min_heap) < k:
            heapq.heappush(min_heap, (count, ip))
        elif count > min_heap[0][0]:
            heapq.heapreplace(min_heap, (count, ip))
    
    # 按count降序返回
    result = [(ip, count) for count, ip in min_heap]
    result.sort(key=lambda x: -x[1])
    return result
```

### 考察点
- 日志格式理解
- Counter的使用
- 堆数据结构（进阶）
- 复杂度分析

---

## 题目2：统计HTTP状态码分布 ⭐

### 题目描述

分析Nginx日志，统计各HTTP状态码的出现次数和百分比。

**输入**：logs: List[str]
**输出**：Dict[str, Dict]，包含count和percentage

### Python3 解答

```python
from collections import Counter
from typing import List, Dict
import re

def analyze_status_codes(logs: List[str]) -> Dict[str, Dict]:
    """
    统计HTTP状态码分布
    """
    # 匹配状态码：" 200 " 这样的模式
    pattern = r'" (\d{3}) '
    status_counter = Counter()
    
    for line in logs:
        match = re.search(pattern, line)
        if match:
            status_code = match.group(1)
            status_counter[status_code] += 1
    
    total = sum(status_counter.values())
    result = {}
    
    for code, count in sorted(status_counter.items()):
        result[code] = {
            'count': count,
            'percentage': round(count / total * 100, 2) if total > 0 else 0
        }
    
    return result


def analyze_status_by_category(logs: List[str]) -> Dict[str, int]:
    """
    按类别统计：2xx成功，4xx客户端错误，5xx服务端错误
    """
    pattern = r'" (\d{3}) '
    categories = {'2xx': 0, '3xx': 0, '4xx': 0, '5xx': 0, 'other': 0}
    
    for line in logs:
        match = re.search(pattern, line)
        if match:
            code = match.group(1)
            if code.startswith('2'):
                categories['2xx'] += 1
            elif code.startswith('3'):
                categories['3xx'] += 1
            elif code.startswith('4'):
                categories['4xx'] += 1
            elif code.startswith('5'):
                categories['5xx'] += 1
            else:
                categories['other'] += 1
    
    return categories
```

### 考察点
- 正则表达式
- 数据聚合统计
- 百分比计算

---

## 题目3：计算请求延迟百分位数 ⭐⭐

### 题目描述

给定一个包含请求延迟的日志列表，计算P50、P90、P99延迟。

**输入**：latencies: List[float]，延迟列表（单位：毫秒）
**输出**：Dict[str, float]，包含p50, p90, p99

### Python3 解答

**方法一：手动实现（理解原理）**

```python
from typing import List, Dict

def calculate_percentiles(latencies: List[float]) -> Dict[str, float]:
    """
    计算延迟百分位数
    时间复杂度: O(n log n) 排序
    """
    if not latencies:
        return {'p50': 0, 'p90': 0, 'p99': 0}
    
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    def percentile(p: float) -> float:
        """计算第p百分位数"""
        idx = (n - 1) * p / 100
        lower = int(idx)
        upper = lower + 1
        
        if upper >= n:
            return sorted_latencies[-1]
        
        # 线性插值
        weight = idx - lower
        return sorted_latencies[lower] * (1 - weight) + sorted_latencies[upper] * weight
    
    return {
        'p50': round(percentile(50), 2),
        'p90': round(percentile(90), 2),
        'p99': round(percentile(99), 2)
    }
```

**方法二：使用标准库（Python 3.8+）**

```python
import statistics
from typing import List, Dict

def calculate_percentiles_stdlib(latencies: List[float]) -> Dict[str, float]:
    """使用statistics库计算百分位数"""
    if not latencies:
        return {'p50': 0, 'p90': 0, 'p99': 0}
    
    return {
        'p50': round(statistics.quantiles(latencies, n=100)[49], 2),
        'p90': round(statistics.quantiles(latencies, n=100)[89], 2),
        'p99': round(statistics.quantiles(latencies, n=100)[98], 2)
    }
```

### 考察点
- 百分位数概念（SRE核心指标）
- 排序算法应用
- 边界条件处理

---

## 题目4：日志时间窗口聚合 ⭐⭐

### 题目描述

给定带时间戳的日志，按指定时间窗口（如1分钟）聚合请求数量。

**输入**：
- logs: List[Tuple[int, str]]，(timestamp, log_line)列表
- window_seconds: int，时间窗口大小（秒）

**输出**：Dict[int, int]，{窗口起始时间戳: 请求数}

### Python3 解答

```python
from collections import defaultdict
from typing import List, Tuple, Dict
from datetime import datetime

def aggregate_by_window(
    logs: List[Tuple[int, str]], 
    window_seconds: int
) -> Dict[int, int]:
    """
    按时间窗口聚合日志
    """
    window_counts = defaultdict(int)
    
    for timestamp, _ in logs:
        # 计算窗口起始时间
        window_start = (timestamp // window_seconds) * window_seconds
        window_counts[window_start] += 1
    
    # 返回按时间排序的结果
    return dict(sorted(window_counts.items()))


def detect_traffic_spike(
    logs: List[Tuple[int, str]], 
    window_seconds: int,
    threshold_multiplier: float = 2.0
) -> List[int]:
    """
    检测流量突增的时间窗口
    如果某窗口的请求数超过平均值的threshold_multiplier倍，则认为是突增
    """
    window_counts = aggregate_by_window(logs, window_seconds)
    
    if not window_counts:
        return []
    
    values = list(window_counts.values())
    avg = sum(values) / len(values)
    threshold = avg * threshold_multiplier
    
    spikes = [
        window_start 
        for window_start, count in window_counts.items() 
        if count > threshold
    ]
    
    return spikes


# 示例：解析Nginx日志时间戳
def parse_nginx_timestamp(log_line: str) -> int:
    """
    从Nginx日志行解析时间戳
    格式: [21/Jan/2026:10:00:00 +0800]
    """
    import re
    pattern = r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})'
    match = re.search(pattern, log_line)
    
    if match:
        time_str = match.group(1)
        dt = datetime.strptime(time_str, '%d/%b/%Y:%H:%M:%S')
        return int(dt.timestamp())
    
    return 0
```

### 考察点
- 时间窗口概念（监控核心）
- 时间戳处理
- 异常检测基础

---

## 题目5：解析结构化日志 ⭐⭐

### 题目描述

解析JSON格式的应用日志，提取错误信息并按错误类型统计。

**输入**：logs: List[str]，每行是一个JSON格式的日志

**日志格式**：
```json
{"timestamp": "2026-01-21T10:00:00Z", "level": "ERROR", "service": "auth", "message": "connection timeout", "error_code": "E001"}
```

**输出**：按error_code统计的错误分布

### Python3 解答

```python
import json
from collections import Counter, defaultdict
from typing import List, Dict, Any
from datetime import datetime

def parse_json_logs(logs: List[str]) -> List[Dict[str, Any]]:
    """
    安全解析JSON日志
    """
    parsed = []
    for line in logs:
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # 跳过格式错误的行
    return parsed


def count_errors_by_code(logs: List[str]) -> Dict[str, int]:
    """
    按错误码统计错误
    """
    error_counter = Counter()
    
    for line in logs:
        try:
            log_entry = json.loads(line)
            if log_entry.get('level') == 'ERROR':
                error_code = log_entry.get('error_code', 'UNKNOWN')
                error_counter[error_code] += 1
        except json.JSONDecodeError:
            continue
    
    return dict(error_counter.most_common())


def analyze_errors_by_service(logs: List[str]) -> Dict[str, Dict[str, int]]:
    """
    按服务分组统计错误
    返回: {service: {error_code: count}}
    """
    service_errors = defaultdict(Counter)
    
    for line in logs:
        try:
            log_entry = json.loads(line)
            if log_entry.get('level') == 'ERROR':
                service = log_entry.get('service', 'unknown')
                error_code = log_entry.get('error_code', 'UNKNOWN')
                service_errors[service][error_code] += 1
        except json.JSONDecodeError:
            continue
    
    return {
        service: dict(errors) 
        for service, errors in service_errors.items()
    }


def find_error_patterns(logs: List[str], time_window_minutes: int = 5) -> Dict[str, List[str]]:
    """
    查找在短时间内多次出现的错误模式
    返回: {error_code: [timestamps]}
    """
    error_timeline = defaultdict(list)
    
    for line in logs:
        try:
            log_entry = json.loads(line)
            if log_entry.get('level') == 'ERROR':
                error_code = log_entry.get('error_code', 'UNKNOWN')
                timestamp = log_entry.get('timestamp', '')
                error_timeline[error_code].append(timestamp)
        except json.JSONDecodeError:
            continue
    
    # 只返回出现多次的错误
    return {
        code: times 
        for code, times in error_timeline.items() 
        if len(times) > 1
    }
```

### 考察点
- JSON解析
- 异常处理
- 多维度数据聚合

---

## 题目6：日志正则提取 ⭐⭐⭐

### 题目描述

从非结构化日志中提取关键信息。

**日志示例**：
```
2026-01-21 10:00:00.123 [INFO] [RequestID:abc123] User user@example.com logged in from 192.168.1.100 in 150ms
2026-01-21 10:00:01.456 [ERROR] [RequestID:def456] Failed to process payment for order #12345: timeout after 30000ms
```

**要求**：提取以下字段
- timestamp
- level
- request_id
- 关键业务信息

### Python3 解答

```python
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    request_id: str
    message: str
    extracted_data: Dict[str, Any]


def parse_log_line(line: str) -> Optional[LogEntry]:
    """
    解析单行日志，提取结构化信息
    """
    # 基础模式：时间戳、级别、RequestID
    base_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[(\w+)\] \[RequestID:(\w+)\] (.+)$'
    
    match = re.match(base_pattern, line)
    if not match:
        return None
    
    timestamp_str, level, request_id, message = match.groups()
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
    
    # 提取额外数据
    extracted = {}
    
    # 提取邮箱
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', message)
    if email_match:
        extracted['email'] = email_match.group()
    
    # 提取IP地址
    ip_match = re.search(r'\b(\d{1,3}\.){3}\d{1,3}\b', message)
    if ip_match:
        extracted['ip'] = ip_match.group()
    
    # 提取耗时
    duration_match = re.search(r'(\d+)ms', message)
    if duration_match:
        extracted['duration_ms'] = int(duration_match.group(1))
    
    # 提取订单号
    order_match = re.search(r'order #(\d+)', message)
    if order_match:
        extracted['order_id'] = order_match.group(1)
    
    return LogEntry(
        timestamp=timestamp,
        level=level,
        request_id=request_id,
        message=message,
        extracted_data=extracted
    )


def extract_slow_requests(logs: List[str], threshold_ms: int = 1000) -> List[LogEntry]:
    """
    提取慢请求日志
    """
    slow_requests = []
    
    for line in logs:
        entry = parse_log_line(line)
        if entry and entry.extracted_data.get('duration_ms', 0) > threshold_ms:
            slow_requests.append(entry)
    
    return slow_requests


def trace_request(logs: List[str], request_id: str) -> List[LogEntry]:
    """
    追踪特定请求的所有日志
    """
    traces = []
    
    for line in logs:
        entry = parse_log_line(line)
        if entry and entry.request_id == request_id:
            traces.append(entry)
    
    return sorted(traces, key=lambda x: x.timestamp)


class LogParser:
    """
    可扩展的日志解析器
    支持注册自定义提取规则
    """
    
    def __init__(self):
        self.extractors = {}
    
    def register_extractor(self, name: str, pattern: str, group: int = 0):
        """注册自定义提取规则"""
        self.extractors[name] = (re.compile(pattern), group)
    
    def extract(self, text: str) -> Dict[str, str]:
        """提取所有已注册的字段"""
        result = {}
        for name, (pattern, group) in self.extractors.items():
            match = pattern.search(text)
            if match:
                result[name] = match.group(group) if group else match.group()
        return result


# 使用示例
parser = LogParser()
parser.register_extractor('email', r'[\w.+-]+@[\w-]+\.[\w.-]+')
parser.register_extractor('ip', r'\b(\d{1,3}\.){3}\d{1,3}\b')
parser.register_extractor('user_id', r'user_id[=:](\w+)', 1)
```

### 考察点
- 复杂正则表达式
- 数据结构设计
- 可扩展性考虑
- dataclass使用

---

## 题目7：日志去重与采样 ⭐⭐

### 题目描述

在日志量巨大时，需要进行去重和采样：
1. 对相同的错误信息去重，只保留第一次出现的时间和总计数
2. 实现按比例采样

### Python3 解答

```python
from collections import defaultdict
from typing import List, Dict, Tuple
import random
import hashlib

def deduplicate_errors(logs: List[Dict]) -> List[Dict]:
    """
    错误日志去重
    相同message的错误只保留首次出现，附加计数
    """
    error_groups = defaultdict(list)
    
    for log in logs:
        if log.get('level') == 'ERROR':
            message = log.get('message', '')
            error_groups[message].append(log)
    
    result = []
    for message, group in error_groups.items():
        first_occurrence = min(group, key=lambda x: x.get('timestamp', ''))
        result.append({
            **first_occurrence,
            'occurrence_count': len(group),
            'is_deduplicated': len(group) > 1
        })
    
    return result


def sample_logs(logs: List[str], sample_rate: float = 0.1, seed: int = None) -> List[str]:
    """
    随机采样日志
    sample_rate: 采样比例，0.1表示10%
    """
    if seed is not None:
        random.seed(seed)
    
    return [log for log in logs if random.random() < sample_rate]


def consistent_sample(logs: List[Dict], sample_rate: float, key_field: str = 'request_id') -> List[Dict]:
    """
    一致性采样：相同key的请求要么都采样，要么都不采样
    适用于分布式追踪场景
    """
    sampled = []
    
    for log in logs:
        key = log.get(key_field, str(log))
        # 使用hash确保相同key的采样决策一致
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        if (hash_value % 100) < (sample_rate * 100):
            sampled.append(log)
    
    return sampled


def reservoir_sampling(log_stream, k: int) -> List[str]:
    """
    水塘采样：从未知大小的流中均匀采样k条
    适用于日志流处理场景
    """
    reservoir = []
    
    for i, log in enumerate(log_stream):
        if i < k:
            reservoir.append(log)
        else:
            # 以k/(i+1)的概率替换
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = log
    
    return reservoir


class RateLimitedLogger:
    """
    限流日志记录器
    相同key的日志在指定时间窗口内只记录一次
    """
    
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self.last_logged = {}  # key -> timestamp
    
    def should_log(self, key: str, current_time: float) -> bool:
        last_time = self.last_logged.get(key, 0)
        if current_time - last_time >= self.window_seconds:
            self.last_logged[key] = current_time
            return True
        return False
```

### 考察点
- 采样算法
- 一致性哈希思想
- 水塘采样（流处理）
- 限流器设计

---

## 题目8：多文件日志合并 ⭐⭐⭐

### 题目描述

多个日志文件需要按时间戳合并排序（类似K路归并）。

**输入**：多个已按时间排序的日志文件
**输出**：按时间顺序合并的日志流

### Python3 解答

**核心算法：K路归并**

```python
import heapq
from typing import List, Iterator
from dataclasses import dataclass, field

@dataclass(order=True)
class LogItem:
    """可比较的日志项，用于堆排序"""
    timestamp: str
    content: str = field(compare=False)
    source_idx: int = field(compare=False)


def extract_timestamp(line: str) -> str:
    """从日志行提取时间戳（假设时间戳在行首）"""
    # 格式: 2026-01-21 10:00:00.123
    return line[:23] if len(line) >= 23 else line


def merge_sorted_logs(log_files: List[List[str]]) -> Iterator[str]:
    """
    K路归并多个已排序的日志文件
    时间复杂度: O(N log K)，N为总日志数，K为文件数
    空间复杂度: O(K)
    """
    heap = []
    iterators = [iter(f) for f in log_files]
    
    # 初始化：从每个文件取第一条
    for idx, it in enumerate(iterators):
        try:
            line = next(it)
            timestamp = extract_timestamp(line)
            heapq.heappush(heap, LogItem(timestamp, line, idx))
        except StopIteration:
            continue
    
    # 归并
    while heap:
        item = heapq.heappop(heap)
        yield item.content
        
        try:
            line = next(iterators[item.source_idx])
            timestamp = extract_timestamp(line)
            heapq.heappush(heap, LogItem(timestamp, line, item.source_idx))
        except StopIteration:
            continue
```

**实际文件处理版本**

```python
from typing import List, Iterator

def merge_log_files(file_paths: List[str], output_path: str):
    """
    合并多个日志文件到一个输出文件
    使用生成器避免内存问题
    """
    def file_line_generator(path: str) -> Iterator[str]:
        with open(path, 'r') as f:
            for line in f:
                yield line.rstrip('\n')
    
    generators = [file_line_generator(p) for p in file_paths]
    
    with open(output_path, 'w') as out:
        for line in merge_sorted_logs(generators):
            out.write(line + '\n')
```

**支持时间范围过滤的合并**

```python
from typing import List, Iterator, Optional

def merge_logs_with_filter(
    log_files: List[List[str]], 
    start_time: Optional[str] = None, 
    end_time: Optional[str] = None
) -> Iterator[str]:
    """合并日志并按时间范围过滤"""
    for line in merge_sorted_logs(log_files):
        ts = extract_timestamp(line)
        if start_time and ts < start_time:
            continue
        if end_time and ts > end_time:
            break
        yield line
```

### 考察点
- K路归并算法
- 堆的应用
- 生成器和迭代器
- 大文件处理

---

## 总结

| 题目 | 难度 | 核心考点 |
|------|------|----------|
| Top K IP分析 | ⭐⭐ | Counter、堆 |
| 状态码统计 | ⭐ | 正则、聚合 |
| 延迟百分位数 | ⭐⭐ | 排序、SRE指标 |
| 时间窗口聚合 | ⭐⭐ | 时间处理、监控思维 |
| JSON日志解析 | ⭐⭐ | JSON、异常处理 |
| 正则提取 | ⭐⭐⭐ | 复杂正则、设计模式 |
| 日志去重采样 | ⭐⭐ | 采样算法、限流 |
| 多文件合并 | ⭐⭐⭐ | K路归并、生成器 |

**面试技巧**：
1. 先写出正确解法，再优化
2. 注意边界条件（空输入、格式错误）
3. 讨论时间和空间复杂度
4. 提及实际场景的考虑（大文件、流处理）

---

## 相关文章

- [上一篇：SRE组织与文化](@/articles/sre/sre-14-SRE组织与文化.md)
- [下一篇：SRE笔试题-系统与网络编程](@/articles/sre/sre-16-SRE笔试题-系统与网络编程.md)
