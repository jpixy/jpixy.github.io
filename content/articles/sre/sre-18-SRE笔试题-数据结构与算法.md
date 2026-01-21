+++
title = "18.SRE笔试题-数据结构与算法"
date = 2026-01-21
description = "SRE面试笔试题精选：LRU缓存、布隆过滤器、优先队列、滑动窗口、图算法等，Python3完整解答"
[taxonomies]
tags = ["SRE", "面试", "Python", "笔试", "算法", "数据结构"]
+++

## 概述

SRE笔试中的算法题通常与实际运维场景结合，如缓存淘汰、限流、调度、依赖分析等。本文收录SRE常见的数据结构与算法题目。

**难度标记**：⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 困难

---

## 题目1：实现LRU缓存 ⭐⭐⭐

### 题目描述

实现一个LRU（Least Recently Used）缓存，支持：
- `get(key)`: 获取缓存值，不存在返回-1
- `put(key, value)`: 设置缓存值，超过容量时淘汰最久未使用的

**要求**：get和put操作的时间复杂度都是O(1)

### 场景应用
- 本地缓存实现
- 数据库查询缓存
- DNS解析缓存

### Python3 解答

```python
from collections import OrderedDict
from typing import Optional, Any

class LRUCache:
    """
    使用OrderedDict实现LRU缓存
    时间复杂度: O(1)
    """
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key: str) -> Any:
        if key not in self.cache:
            return -1
        # 移动到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        
        if len(self.cache) > self.capacity:
            # 删除最久未使用的（开头）
            self.cache.popitem(last=False)


# 手动实现版本（面试常考）
class ListNode:
    def __init__(self, key: str = "", value: Any = None):
        self.key = key
        self.value = value
        self.prev: Optional['ListNode'] = None
        self.next: Optional['ListNode'] = None


class LRUCacheManual:
    """
    使用双向链表 + 哈希表实现
    """
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}  # key -> ListNode
        
        # 虚拟头尾节点
        self.head = ListNode()
        self.tail = ListNode()
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def _remove(self, node: ListNode):
        """从链表中移除节点"""
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _add_to_tail(self, node: ListNode):
        """添加节点到尾部（最近使用）"""
        node.prev = self.tail.prev
        node.next = self.tail
        self.tail.prev.next = node
        self.tail.prev = node
    
    def get(self, key: str) -> Any:
        if key not in self.cache:
            return -1
        
        node = self.cache[key]
        # 移动到尾部
        self._remove(node)
        self._add_to_tail(node)
        return node.value
    
    def put(self, key: str, value: Any):
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._remove(node)
            self._add_to_tail(node)
        else:
            node = ListNode(key, value)
            self.cache[key] = node
            self._add_to_tail(node)
            
            if len(self.cache) > self.capacity:
                # 删除头部节点（最久未使用）
                lru = self.head.next
                self._remove(lru)
                del self.cache[lru.key]


# 带TTL的LRU缓存
import time

class LRUCacheWithTTL:
    """
    支持过期时间的LRU缓存
    """
    
    def __init__(self, capacity: int, default_ttl: float = 300):
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.cache = OrderedDict()  # key -> (value, expire_time)
    
    def get(self, key: str) -> Any:
        if key not in self.cache:
            return -1
        
        value, expire_time = self.cache[key]
        
        # 检查是否过期
        if time.time() > expire_time:
            del self.cache[key]
            return -1
        
        self.cache.move_to_end(key)
        return value
    
    def put(self, key: str, value: Any, ttl: float = None):
        ttl = ttl or self.default_ttl
        expire_time = time.time() + ttl
        
        if key in self.cache:
            self.cache.move_to_end(key)
        
        self.cache[key] = (value, expire_time)
        
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def cleanup_expired(self):
        """清理过期条目"""
        now = time.time()
        expired_keys = [
            k for k, (_, exp) in self.cache.items() 
            if now > exp
        ]
        for key in expired_keys:
            del self.cache[key]
```

### 考察点
- 双向链表操作
- 哈希表与链表结合
- OrderedDict的使用
- 时间复杂度分析

---

## 题目2：实现布隆过滤器 ⭐⭐⭐

### 题目描述

实现一个布隆过滤器（Bloom Filter），用于快速判断元素是否可能存在于集合中。

### 场景应用
- 缓存穿透防护
- 爬虫URL去重
- 垃圾邮件过滤

### Python3 解答

```python
import hashlib
import math
from typing import List

class BloomFilter:
    """
    布隆过滤器
    - 判断不存在：100%准确
    - 判断存在：可能误判（假阳性）
    """
    
    def __init__(self, expected_items: int, false_positive_rate: float = 0.01):
        """
        expected_items: 预期存储的元素数量
        false_positive_rate: 允许的误判率
        """
        # 计算最优位数组大小
        self.size = self._optimal_size(expected_items, false_positive_rate)
        # 计算最优哈希函数数量
        self.hash_count = self._optimal_hash_count(self.size, expected_items)
        
        self.bit_array = [False] * self.size
        self.item_count = 0
    
    def _optimal_size(self, n: int, p: float) -> int:
        """计算最优位数组大小: m = -n*ln(p) / (ln2)^2"""
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m)
    
    def _optimal_hash_count(self, m: int, n: int) -> int:
        """计算最优哈希函数数量: k = (m/n) * ln2"""
        k = (m / n) * math.log(2)
        return int(k)
    
    def _hashes(self, item: str) -> List[int]:
        """生成多个哈希值"""
        hashes = []
        for i in range(self.hash_count):
            # 使用不同的种子生成不同的哈希
            data = f"{item}:{i}".encode()
            hash_value = int(hashlib.md5(data).hexdigest(), 16)
            hashes.append(hash_value % self.size)
        return hashes
    
    def add(self, item: str):
        """添加元素"""
        for pos in self._hashes(item):
            self.bit_array[pos] = True
        self.item_count += 1
    
    def might_contain(self, item: str) -> bool:
        """
        检查元素是否可能存在
        返回False: 一定不存在
        返回True: 可能存在（有误判概率）
        """
        return all(self.bit_array[pos] for pos in self._hashes(item))
    
    def estimated_false_positive_rate(self) -> float:
        """估算当前误判率"""
        # p = (1 - e^(-kn/m))^k
        x = -self.hash_count * self.item_count / self.size
        return (1 - math.exp(x)) ** self.hash_count


class CountingBloomFilter:
    """
    计数布隆过滤器
    支持删除操作
    """
    
    def __init__(self, expected_items: int, false_positive_rate: float = 0.01):
        bf = BloomFilter(expected_items, false_positive_rate)
        self.size = bf.size
        self.hash_count = bf.hash_count
        
        # 使用计数器代替位数组
        self.counters = [0] * self.size
    
    def _hashes(self, item: str) -> List[int]:
        hashes = []
        for i in range(self.hash_count):
            data = f"{item}:{i}".encode()
            hash_value = int(hashlib.md5(data).hexdigest(), 16)
            hashes.append(hash_value % self.size)
        return hashes
    
    def add(self, item: str):
        for pos in self._hashes(item):
            self.counters[pos] += 1
    
    def remove(self, item: str):
        """删除元素（只有之前添加过才能删除）"""
        if self.might_contain(item):
            for pos in self._hashes(item):
                if self.counters[pos] > 0:
                    self.counters[pos] -= 1
    
    def might_contain(self, item: str) -> bool:
        return all(self.counters[pos] > 0 for pos in self._hashes(item))


# 使用示例：缓存穿透防护
class CacheWithBloomFilter:
    """
    使用布隆过滤器防止缓存穿透
    """
    
    def __init__(self, expected_keys: int):
        self.bloom = BloomFilter(expected_keys)
        self.cache = {}
    
    def set(self, key: str, value):
        self.bloom.add(key)
        self.cache[key] = value
    
    def get(self, key: str):
        # 先用布隆过滤器判断
        if not self.bloom.might_contain(key):
            # 一定不存在，直接返回，不查数据库
            return None
        
        # 可能存在，查缓存
        if key in self.cache:
            return self.cache[key]
        
        # 缓存未命中，需要查数据库
        # value = db.get(key)
        # if value:
        #     self.cache[key] = value
        # return value
        return None
```

### 考察点
- 布隆过滤器原理
- 哈希函数设计
- 空间时间权衡
- 实际应用场景

---

## 题目3：滑动窗口最大值 ⭐⭐

### 题目描述

给定一个数组和窗口大小k，返回每个滑动窗口的最大值。

### 场景应用
- 监控指标滑动窗口聚合
- 异常检测（最大延迟、最大CPU等）

### Python3 解答

```python
from collections import deque
from typing import List

def max_sliding_window(nums: List[int], k: int) -> List[int]:
    """
    使用单调递减队列
    时间复杂度: O(n)
    空间复杂度: O(k)
    """
    if not nums or k == 0:
        return []
    
    # 存储索引的双端队列，对应的值单调递减
    dq = deque()
    result = []
    
    for i, num in enumerate(nums):
        # 移除超出窗口的元素
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        # 移除所有小于当前元素的（它们不可能是最大值了）
        while dq and nums[dq[-1]] < num:
            dq.pop()
        
        dq.append(i)
        
        # 窗口形成后开始输出
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result


def min_sliding_window(nums: List[int], k: int) -> List[int]:
    """滑动窗口最小值"""
    if not nums or k == 0:
        return []
    
    dq = deque()  # 单调递增队列
    result = []
    
    for i, num in enumerate(nums):
        while dq and dq[0] <= i - k:
            dq.popleft()
        
        while dq and nums[dq[-1]] > num:
            dq.pop()
        
        dq.append(i)
        
        if i >= k - 1:
            result.append(nums[dq[0]])
    
    return result


class SlidingWindowStats:
    """
    滑动窗口统计器
    支持最大值、最小值、平均值
    """
    
    def __init__(self, window_size: int):
        self.window_size = window_size
        self.data = deque()
        self.max_dq = deque()  # 单调递减
        self.min_dq = deque()  # 单调递增
        self.total = 0
    
    def add(self, value: float) -> dict:
        """添加数据点，返回当前统计"""
        # 维护数据窗口
        self.data.append(value)
        self.total += value
        
        if len(self.data) > self.window_size:
            removed = self.data.popleft()
            self.total -= removed
            
            if self.max_dq and self.max_dq[0] == removed:
                self.max_dq.popleft()
            if self.min_dq and self.min_dq[0] == removed:
                self.min_dq.popleft()
        
        # 维护单调队列
        while self.max_dq and self.max_dq[-1] < value:
            self.max_dq.pop()
        self.max_dq.append(value)
        
        while self.min_dq and self.min_dq[-1] > value:
            self.min_dq.pop()
        self.min_dq.append(value)
        
        return self.stats()
    
    def stats(self) -> dict:
        if not self.data:
            return {'max': 0, 'min': 0, 'avg': 0, 'count': 0}
        
        return {
            'max': self.max_dq[0],
            'min': self.min_dq[0],
            'avg': round(self.total / len(self.data), 2),
            'count': len(self.data)
        }
```

### 考察点
- 单调队列
- 滑动窗口技巧
- 时间复杂度优化

---

## 题目4：合并K个有序列表 ⭐⭐

### 题目描述

合并K个有序的日志流，输出按时间排序的结果。

### 场景应用
- 多日志文件合并
- 分布式日志聚合

### Python3 解答

```python
import heapq
from typing import List, Iterator, Tuple

def merge_k_sorted_lists(lists: List[List[int]]) -> List[int]:
    """
    合并K个有序列表
    时间复杂度: O(N log K)
    空间复杂度: O(K)
    """
    result = []
    # 最小堆: (value, list_index, element_index)
    heap = []
    
    # 初始化：将每个列表的第一个元素加入堆
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))
    
    while heap:
        val, list_idx, elem_idx = heapq.heappop(heap)
        result.append(val)
        
        # 将该列表的下一个元素加入堆
        if elem_idx + 1 < len(lists[list_idx]):
            next_val = lists[list_idx][elem_idx + 1]
            heapq.heappush(heap, (next_val, list_idx, elem_idx + 1))
    
    return result


def merge_k_sorted_iterators(iterators: List[Iterator]) -> Iterator:
    """
    合并K个有序迭代器（内存高效版本）
    适合处理大文件流
    """
    heap = []
    
    for i, it in enumerate(iterators):
        try:
            val = next(it)
            heapq.heappush(heap, (val, i, it))
        except StopIteration:
            continue
    
    while heap:
        val, idx, it = heapq.heappop(heap)
        yield val
        
        try:
            next_val = next(it)
            heapq.heappush(heap, (next_val, idx, it))
        except StopIteration:
            continue


# 合并日志的实际应用
from dataclasses import dataclass

@dataclass
class LogEntry:
    timestamp: str
    content: str
    source: str
    
    def __lt__(self, other):
        return self.timestamp < other.timestamp


def merge_log_streams(log_streams: List[Iterator[LogEntry]]) -> Iterator[LogEntry]:
    """
    合并多个日志流
    """
    heap = []
    
    for i, stream in enumerate(log_streams):
        try:
            entry = next(stream)
            heapq.heappush(heap, (entry, i, stream))
        except StopIteration:
            continue
    
    while heap:
        entry, idx, stream = heapq.heappop(heap)
        yield entry
        
        try:
            next_entry = next(stream)
            heapq.heappush(heap, (next_entry, idx, stream))
        except StopIteration:
            continue
```

### 考察点
- 堆的应用
- 归并算法
- 迭代器使用

---

## 题目5：服务依赖拓扑排序 ⭐⭐

### 题目描述

给定服务之间的依赖关系，返回正确的启动顺序。如果存在循环依赖，返回空列表。

### 场景应用
- 服务启动顺序
- 构建系统依赖
- 任务调度

### Python3 解答

```python
from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple

def topological_sort(
    services: List[str], 
    dependencies: List[Tuple[str, str]]
) -> List[str]:
    """
    拓扑排序（Kahn算法）
    dependencies: [(A, B)] 表示A依赖B，B需要先启动
    返回启动顺序，如果有循环依赖返回空列表
    """
    # 构建图
    graph = defaultdict(list)  # 被依赖 -> 依赖者
    in_degree = defaultdict(int)
    
    # 初始化所有服务
    for s in services:
        in_degree[s] = 0
    
    for dependent, dependency in dependencies:
        graph[dependency].append(dependent)
        in_degree[dependent] += 1
    
    # 入度为0的服务可以首先启动
    queue = deque([s for s in services if in_degree[s] == 0])
    result = []
    
    while queue:
        service = queue.popleft()
        result.append(service)
        
        for dependent in graph[service]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    # 如果结果数量不等于服务数，说明有循环依赖
    if len(result) != len(services):
        return []
    
    return result


def detect_circular_dependency(
    services: List[str], 
    dependencies: List[Tuple[str, str]]
) -> List[str]:
    """
    检测循环依赖，返回循环路径
    使用DFS
    """
    graph = defaultdict(list)
    for dependent, dependency in dependencies:
        graph[dependent].append(dependency)
    
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {s: WHITE for s in services}
    parent = {}
    cycle = []
    
    def dfs(node: str) -> bool:
        color[node] = GRAY
        
        for neighbor in graph[node]:
            if color[neighbor] == GRAY:
                # 找到循环，回溯路径
                cycle.append(neighbor)
                current = node
                while current != neighbor:
                    cycle.append(current)
                    current = parent.get(current)
                cycle.append(neighbor)
                cycle.reverse()
                return True
            
            if color[neighbor] == WHITE:
                parent[neighbor] = node
                if dfs(neighbor):
                    return True
        
        color[node] = BLACK
        return False
    
    for service in services:
        if color[service] == WHITE:
            if dfs(service):
                return cycle
    
    return []


class DependencyGraph:
    """
    服务依赖图
    支持依赖分析、启动顺序、循环检测
    """
    
    def __init__(self):
        self.services: Set[str] = set()
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
    
    def add_service(self, name: str):
        self.services.add(name)
    
    def add_dependency(self, service: str, depends_on: str):
        """service 依赖 depends_on"""
        self.services.add(service)
        self.services.add(depends_on)
        self.dependencies[service].add(depends_on)
        self.dependents[depends_on].add(service)
    
    def get_start_order(self) -> List[str]:
        """获取启动顺序"""
        deps = [(s, d) for s in self.dependencies for d in self.dependencies[s]]
        return topological_sort(list(self.services), deps)
    
    def get_stop_order(self) -> List[str]:
        """获取停止顺序（启动顺序的逆序）"""
        return list(reversed(self.get_start_order()))
    
    def get_affected_services(self, service: str) -> Set[str]:
        """获取某服务故障会影响的所有服务"""
        affected = set()
        queue = deque([service])
        
        while queue:
            current = queue.popleft()
            for dependent in self.dependents[current]:
                if dependent not in affected:
                    affected.add(dependent)
                    queue.append(dependent)
        
        return affected
    
    def get_all_dependencies(self, service: str) -> Set[str]:
        """获取某服务的所有直接和间接依赖"""
        deps = set()
        queue = deque([service])
        
        while queue:
            current = queue.popleft()
            for dependency in self.dependencies[current]:
                if dependency not in deps:
                    deps.add(dependency)
                    queue.append(dependency)
        
        return deps


# 使用示例
graph = DependencyGraph()
graph.add_dependency("api", "database")
graph.add_dependency("api", "cache")
graph.add_dependency("worker", "database")
graph.add_dependency("scheduler", "worker")

print(graph.get_start_order())  # ['database', 'cache', 'api', 'worker', 'scheduler']
print(graph.get_affected_services("database"))  # {'api', 'worker', 'scheduler'}
```

### 考察点
- 图的表示
- 拓扑排序
- 循环依赖检测
- BFS/DFS遍历

---

## 题目6：实现优先队列调度器 ⭐⭐

### 题目描述

实现一个支持优先级的任务调度器，高优先级任务先执行。

### Python3 解答

```python
import heapq
import time
import threading
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from enum import IntEnum

class Priority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass(order=True)
class Task:
    priority: int
    created_at: float = field(compare=False)
    task_id: str = field(compare=False)
    func: Callable = field(compare=False)
    args: tuple = field(compare=False, default=())
    kwargs: dict = field(compare=False, default_factory=dict)


class PriorityScheduler:
    """
    优先级任务调度器
    """
    
    def __init__(self, workers: int = 4):
        self.queue = []  # 最小堆
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.workers = workers
        self.running = False
        self.threads = []
        self.task_counter = 0
    
    def submit(
        self, 
        func: Callable, 
        priority: Priority = Priority.NORMAL,
        *args, 
        **kwargs
    ) -> str:
        """提交任务"""
        with self.lock:
            self.task_counter += 1
            task_id = f"task_{self.task_counter}"
            
            task = Task(
                priority=priority,
                created_at=time.time(),
                task_id=task_id,
                func=func,
                args=args,
                kwargs=kwargs
            )
            
            heapq.heappush(self.queue, task)
            self.condition.notify()
            
            return task_id
    
    def _worker(self):
        """工作线程"""
        while self.running:
            task = None
            
            with self.condition:
                while self.running and not self.queue:
                    self.condition.wait(timeout=1)
                
                if self.queue:
                    task = heapq.heappop(self.queue)
            
            if task:
                try:
                    task.func(*task.args, **task.kwargs)
                except Exception as e:
                    print(f"Task {task.task_id} failed: {e}")
    
    def start(self):
        """启动调度器"""
        self.running = True
        for _ in range(self.workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.threads.append(t)
    
    def stop(self):
        """停止调度器"""
        self.running = False
        with self.condition:
            self.condition.notify_all()
        
        for t in self.threads:
            t.join(timeout=5)
    
    def pending_count(self) -> int:
        """待处理任务数"""
        with self.lock:
            return len(self.queue)


class DelayedTaskScheduler:
    """
    延迟任务调度器
    支持在指定时间执行任务
    """
    
    def __init__(self):
        self.queue = []  # (execute_at, task_id, func, args, kwargs)
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.running = False
        self.task_counter = 0
    
    def schedule(
        self, 
        func: Callable, 
        delay_seconds: float,
        *args, 
        **kwargs
    ) -> str:
        """延迟执行任务"""
        with self.lock:
            self.task_counter += 1
            task_id = f"delayed_{self.task_counter}"
            execute_at = time.time() + delay_seconds
            
            heapq.heappush(self.queue, (execute_at, task_id, func, args, kwargs))
            self.condition.notify()
            
            return task_id
    
    def schedule_at(
        self, 
        func: Callable, 
        execute_at: float,
        *args, 
        **kwargs
    ) -> str:
        """在指定时间执行任务"""
        with self.lock:
            self.task_counter += 1
            task_id = f"scheduled_{self.task_counter}"
            
            heapq.heappush(self.queue, (execute_at, task_id, func, args, kwargs))
            self.condition.notify()
            
            return task_id
    
    def _worker(self):
        while self.running:
            with self.condition:
                while self.running:
                    if not self.queue:
                        self.condition.wait(timeout=1)
                        continue
                    
                    execute_at = self.queue[0][0]
                    now = time.time()
                    
                    if execute_at <= now:
                        _, task_id, func, args, kwargs = heapq.heappop(self.queue)
                        break
                    else:
                        # 等待到执行时间
                        self.condition.wait(timeout=execute_at - now)
                else:
                    return
            
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Task {task_id} failed: {e}")
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        with self.condition:
            self.condition.notify_all()
```

### 考察点
- 优先队列/堆
- 线程同步
- 条件变量
- 调度器设计

---

## 题目7：实现跳表 ⭐⭐⭐

### 题目描述

实现跳表（Skip List），支持O(log n)的查找、插入、删除。

### 场景应用
- Redis有序集合底层实现
- 内存索引

### Python3 解答

```python
import random
from typing import Optional, List, Any

class SkipListNode:
    def __init__(self, key: float, value: Any, level: int):
        self.key = key
        self.value = value
        # forward[i] 是第i层的下一个节点
        self.forward: List[Optional['SkipListNode']] = [None] * (level + 1)


class SkipList:
    """
    跳表实现
    平均时间复杂度: O(log n)
    空间复杂度: O(n)
    """
    
    MAX_LEVEL = 16
    P = 0.5  # 节点升级概率
    
    def __init__(self):
        self.header = SkipListNode(float('-inf'), None, self.MAX_LEVEL)
        self.level = 0
        self.size = 0
    
    def _random_level(self) -> int:
        """随机生成层数"""
        level = 0
        while random.random() < self.P and level < self.MAX_LEVEL:
            level += 1
        return level
    
    def search(self, key: float) -> Optional[Any]:
        """查找键对应的值"""
        current = self.header
        
        # 从最高层开始向下查找
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        
        # 移动到第0层的下一个节点
        current = current.forward[0]
        
        if current and current.key == key:
            return current.value
        return None
    
    def insert(self, key: float, value: Any):
        """插入键值对"""
        # 记录每层需要更新的节点
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        # 如果键已存在，更新值
        if current and current.key == key:
            current.value = value
            return
        
        # 生成新节点的层数
        new_level = self._random_level()
        
        # 如果新层数大于当前最高层，更新头节点
        if new_level > self.level:
            for i in range(self.level + 1, new_level + 1):
                update[i] = self.header
            self.level = new_level
        
        # 创建新节点
        new_node = SkipListNode(key, value, new_level)
        
        # 更新每层的链接
        for i in range(new_level + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        
        self.size += 1
    
    def delete(self, key: float) -> bool:
        """删除键"""
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if not current or current.key != key:
            return False
        
        # 更新每层的链接
        for i in range(self.level + 1):
            if update[i].forward[i] != current:
                break
            update[i].forward[i] = current.forward[i]
        
        # 更新最高层
        while self.level > 0 and not self.header.forward[self.level]:
            self.level -= 1
        
        self.size -= 1
        return True
    
    def range_query(self, start: float, end: float) -> List[tuple]:
        """范围查询"""
        result = []
        current = self.header
        
        # 找到起始位置
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < start:
                current = current.forward[i]
        
        current = current.forward[0]
        
        # 收集范围内的所有元素
        while current and current.key <= end:
            result.append((current.key, current.value))
            current = current.forward[0]
        
        return result
    
    def __len__(self):
        return self.size
    
    def __contains__(self, key: float):
        return self.search(key) is not None
```

### 考察点
- 跳表原理
- 概率数据结构
- 多层链表

---

## 题目8：实现一致性哈希 ⭐⭐⭐

### 题目描述

实现一致性哈希，用于分布式系统的负载均衡。

### Python3 解答

```python
import hashlib
import bisect
from typing import List, Optional, Dict

class ConsistentHash:
    """
    一致性哈希
    用于分布式缓存、负载均衡等场景
    """
    
    def __init__(self, replicas: int = 100):
        """
        replicas: 每个物理节点的虚拟节点数量
        虚拟节点越多，负载越均衡
        """
        self.replicas = replicas
        self.ring: Dict[int, str] = {}  # hash -> node
        self.sorted_keys: List[int] = []
        self.nodes: set = set()
    
    def _hash(self, key: str) -> int:
        """计算哈希值"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str):
        """添加节点"""
        if node in self.nodes:
            return
        
        self.nodes.add(node)
        
        # 添加虚拟节点
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_val = self._hash(virtual_key)
            self.ring[hash_val] = node
            bisect.insort(self.sorted_keys, hash_val)
    
    def remove_node(self, node: str):
        """移除节点"""
        if node not in self.nodes:
            return
        
        self.nodes.discard(node)
        
        # 移除虚拟节点
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_val = self._hash(virtual_key)
            del self.ring[hash_val]
            self.sorted_keys.remove(hash_val)
    
    def get_node(self, key: str) -> Optional[str]:
        """获取key应该路由到的节点"""
        if not self.ring:
            return None
        
        hash_val = self._hash(key)
        
        # 二分查找第一个大于等于hash_val的位置
        idx = bisect.bisect(self.sorted_keys, hash_val)
        
        # 如果到达末尾，回到开头（环形）
        if idx == len(self.sorted_keys):
            idx = 0
        
        return self.ring[self.sorted_keys[idx]]
    
    def get_nodes(self, key: str, count: int = 3) -> List[str]:
        """
        获取key应该路由到的多个节点（用于复制）
        """
        if not self.ring:
            return []
        
        if count >= len(self.nodes):
            return list(self.nodes)
        
        hash_val = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, hash_val)
        
        result = []
        seen_nodes = set()
        
        while len(result) < count:
            if idx >= len(self.sorted_keys):
                idx = 0
            
            node = self.ring[self.sorted_keys[idx]]
            if node not in seen_nodes:
                result.append(node)
                seen_nodes.add(node)
            
            idx += 1
        
        return result


class ConsistentHashWithLoad:
    """
    带负载感知的一致性哈希
    避免热点问题
    """
    
    def __init__(self, replicas: int = 100, max_load: int = 100):
        self.ch = ConsistentHash(replicas)
        self.max_load = max_load
        self.loads: Dict[str, int] = {}  # node -> current load
    
    def add_node(self, node: str):
        self.ch.add_node(node)
        self.loads[node] = 0
    
    def remove_node(self, node: str):
        self.ch.remove_node(node)
        self.loads.pop(node, None)
    
    def get_node(self, key: str) -> Optional[str]:
        """获取负载最小的候选节点"""
        candidates = self.ch.get_nodes(key, count=len(self.ch.nodes))
        
        for node in candidates:
            if self.loads.get(node, 0) < self.max_load:
                self.loads[node] = self.loads.get(node, 0) + 1
                return node
        
        # 所有节点都满载，返回第一个
        if candidates:
            return candidates[0]
        return None
    
    def release(self, node: str):
        """释放节点负载"""
        if node in self.loads and self.loads[node] > 0:
            self.loads[node] -= 1


# 使用示例
ch = ConsistentHash(replicas=150)
ch.add_node("server1")
ch.add_node("server2")
ch.add_node("server3")

# 测试分布均匀性
distribution = {}
for i in range(10000):
    node = ch.get_node(f"key_{i}")
    distribution[node] = distribution.get(node, 0) + 1

print(distribution)  # 应该接近均匀分布
```

### 考察点
- 一致性哈希原理
- 虚拟节点作用
- 负载均衡

---

## 总结

| 题目 | 难度 | 核心考点 | 实际应用 |
|------|------|----------|----------|
| LRU缓存 | ⭐⭐⭐ | 双向链表+哈希表 | 本地缓存 |
| 布隆过滤器 | ⭐⭐⭐ | 位数组+多哈希 | 缓存穿透 |
| 滑动窗口最大值 | ⭐⭐ | 单调队列 | 监控指标 |
| 合并K个有序列表 | ⭐⭐ | 堆 | 日志合并 |
| 拓扑排序 | ⭐⭐ | 图、BFS | 服务依赖 |
| 优先队列调度 | ⭐⭐ | 堆、线程 | 任务调度 |
| 跳表 | ⭐⭐⭐ | 多层链表 | 有序索引 |
| 一致性哈希 | ⭐⭐⭐ | 环形哈希 | 负载均衡 |

**SRE算法面试要点**：
1. 理解算法的实际应用场景
2. 能够分析时间/空间复杂度
3. 考虑边界条件和异常处理
4. 代码简洁清晰
