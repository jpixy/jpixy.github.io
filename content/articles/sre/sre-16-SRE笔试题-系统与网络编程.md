+++
title = "16. SRE笔试题-系统与网络编程"
date = 2026-01-21
weight = 16000
description = "SRE面试笔试题精选：Linux系统编程、网络编程、进程管理、并发处理，Python3完整解答"
[taxonomies]
tags = ["SRE", "面试", "Python", "笔试", "系统编程", "网络"]
+++

## 概述

系统和网络编程是SRE的核心技能。本文收录了SRE笔试中常见的系统与网络相关题目，涵盖进程管理、文件操作、网络通信、并发编程等内容。

**难度标记**：⭐ 简单 | ⭐⭐ 中等 | ⭐⭐⭐ 困难

---

## 题目1：实现简单的端口扫描器 ⭐⭐

### 题目描述

实现一个TCP端口扫描器，检测指定主机的端口是否开放。

**输入**：
- `host`: str，目标主机
- `ports`: List[int]，要扫描的端口列表
- `timeout`: float，超时时间（秒）

**输出**：Dict[int, bool]，端口开放状态

### Python3 解答

```python
import socket
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    检测单个端口是否开放
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.error:
        return False


def scan_ports_sequential(host: str, ports: List[int], timeout: float = 1.0) -> Dict[int, bool]:
    """
    顺序扫描端口（简单但慢）
    """
    results = {}
    for port in ports:
        results[port] = scan_port(host, port, timeout)
    return results


def scan_ports_concurrent(
    host: str, 
    ports: List[int], 
    timeout: float = 1.0,
    max_workers: int = 100
) -> Dict[int, bool]:
    """
    并发扫描端口（推荐）
    使用线程池提高效率
    """
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_port = {
            executor.submit(scan_port, host, port, timeout): port 
            for port in ports
        }
        
        for future in as_completed(future_to_port):
            port = future_to_port[future]
            try:
                results[port] = future.result()
            except Exception:
                results[port] = False
    
    return results


def find_open_ports(host: str, port_range: range, timeout: float = 0.5) -> List[int]:
    """
    找出所有开放的端口
    """
    results = scan_ports_concurrent(host, list(port_range), timeout)
    return sorted([port for port, is_open in results.items() if is_open])


# 常见服务端口检测
COMMON_PORTS = {
    22: 'SSH',
    80: 'HTTP',
    443: 'HTTPS',
    3306: 'MySQL',
    5432: 'PostgreSQL',
    6379: 'Redis',
    27017: 'MongoDB',
    9200: 'Elasticsearch',
    8080: 'HTTP-Alt',
    8443: 'HTTPS-Alt',
}

def scan_common_services(host: str) -> Dict[str, bool]:
    """
    扫描常见服务端口
    """
    port_results = scan_ports_concurrent(host, list(COMMON_PORTS.keys()))
    return {
        COMMON_PORTS[port]: is_open 
        for port, is_open in port_results.items()
    }
```

### 考察点
- Socket编程基础
- 并发编程（ThreadPoolExecutor）
- 超时处理
- 网络知识（TCP连接）

---

## 题目2：实现进程监控工具 ⭐⭐

### 题目描述

实现一个监控指定进程资源使用情况的工具，获取CPU和内存使用率。

**输入**：pid或进程名
**输出**：进程的CPU、内存使用信息

### Python3 解答

**数据结构定义**

```python
from dataclasses import dataclass

@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    status: str
    threads: int
```

**方法一：直接读取 /proc 文件系统（无依赖）**

```python
import os
import time
from typing import List, Optional

def get_process_info_from_proc(pid: int) -> Optional[ProcessInfo]:
    """
    直接从/proc文件系统读取进程信息
    适用于Linux系统，不依赖第三方库
    """
    try:
        # 读取进程状态
        with open(f'/proc/{pid}/stat', 'r') as f:
            stat = f.read().split()
        
        name = stat[1].strip('()')
        status_map = {'R': 'running', 'S': 'sleeping', 'D': 'disk-sleep', 
                      'Z': 'zombie', 'T': 'stopped'}
        status = status_map.get(stat[2], 'unknown')
        threads = int(stat[19])
        
        # 读取内存信息
        with open(f'/proc/{pid}/statm', 'r') as f:
            statm = f.read().split()
        page_size = os.sysconf('SC_PAGE_SIZE')
        memory_mb = int(statm[1]) * page_size / (1024 * 1024)
        
        # CPU使用率需要两次采样
        utime1, stime1 = int(stat[13]), int(stat[14])
        time.sleep(0.1)
        
        with open(f'/proc/{pid}/stat', 'r') as f:
            stat2 = f.read().split()
        utime2, stime2 = int(stat2[13]), int(stat2[14])
        
        clk_tck = os.sysconf('SC_CLK_TCK')
        cpu_time_diff = (utime2 + stime2 - utime1 - stime1) / clk_tck
        cpu_percent = cpu_time_diff / 0.1 * 100
        
        return ProcessInfo(
            pid=pid, name=name, cpu_percent=round(cpu_percent, 2),
            memory_mb=round(memory_mb, 2), status=status, threads=threads
        )
    except (FileNotFoundError, PermissionError, IndexError):
        return None


def find_process_by_name(name: str) -> List[int]:
    """根据进程名查找PID"""
    pids = []
    for entry in os.listdir('/proc'):
        if entry.isdigit():
            try:
                with open(f'/proc/{entry}/comm', 'r') as f:
                    comm = f.read().strip()
                if name in comm:
                    pids.append(int(entry))
            except (FileNotFoundError, PermissionError):
                continue
    return pids


def monitor_process(pid: int, interval: float = 1.0, count: int = 10) -> List[ProcessInfo]:
    """持续监控进程，收集多次采样"""
    samples = []
    for _ in range(count):
        info = get_process_info_from_proc(pid)
        if info:
            samples.append(info)
        time.sleep(interval)
    return samples
```

**方法二：使用 psutil 库（更简洁）**

```python
from typing import List, Optional

def get_process_info_psutil(pid: int) -> Optional[ProcessInfo]:
    """
    使用psutil库获取进程信息
    需要: pip install psutil
    """
    try:
        import psutil
        proc = psutil.Process(pid)
        
        return ProcessInfo(
            pid=pid,
            name=proc.name(),
            cpu_percent=proc.cpu_percent(interval=0.1),
            memory_mb=round(proc.memory_info().rss / (1024 * 1024), 2),
            status=proc.status(),
            threads=proc.num_threads()
        )
    except Exception:
        return None


def get_top_processes(n: int = 10, sort_by: str = 'cpu') -> List[ProcessInfo]:
    """获取资源占用Top N的进程"""
    import psutil
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'num_threads']):
        try:
            info = proc.info
            processes.append(ProcessInfo(
                pid=info['pid'],
                name=info['name'],
                cpu_percent=info['cpu_percent'] or 0,
                memory_mb=round(info['memory_info'].rss / (1024 * 1024), 2) if info['memory_info'] else 0,
                status=info['status'],
                threads=info['num_threads'] or 0
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if sort_by == 'cpu':
        processes.sort(key=lambda x: x.cpu_percent, reverse=True)
    else:
        processes.sort(key=lambda x: x.memory_mb, reverse=True)
    
    return processes[:n]
```

### 考察点
- Linux /proc 文件系统
- 进程状态理解
- CPU使用率计算原理
- 系统调用

---

## 题目3：实现HTTP健康检查 ⭐⭐

### 题目描述

实现一个HTTP健康检查器，支持：
1. 检查URL是否可访问
2. 验证响应状态码
3. 检查响应时间
4. 支持超时设置

### Python3 解答

```python
import urllib.request
import urllib.error
import time
import ssl
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class HealthCheckResult:
    url: str
    status: HealthStatus
    status_code: Optional[int]
    response_time_ms: float
    error_message: Optional[str] = None


def check_http_health(
    url: str, 
    timeout: float = 5.0,
    expected_status: int = 200,
    verify_ssl: bool = True
) -> HealthCheckResult:
    """
    检查单个URL的健康状态
    """
    start_time = time.time()
    
    try:
        # SSL上下文
        if not verify_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        else:
            context = None
        
        request = urllib.request.Request(url, method='GET')
        request.add_header('User-Agent', 'HealthCheck/1.0')
        
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            status_code = response.getcode()
            response_time = (time.time() - start_time) * 1000
            
            if status_code == expected_status:
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.UNHEALTHY
            
            return HealthCheckResult(
                url=url,
                status=status,
                status_code=status_code,
                response_time_ms=round(response_time, 2)
            )
    
    except urllib.error.HTTPError as e:
        response_time = (time.time() - start_time) * 1000
        return HealthCheckResult(
            url=url,
            status=HealthStatus.UNHEALTHY,
            status_code=e.code,
            response_time_ms=round(response_time, 2),
            error_message=str(e)
        )
    
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError):
            return HealthCheckResult(
                url=url,
                status=HealthStatus.TIMEOUT,
                status_code=None,
                response_time_ms=timeout * 1000,
                error_message="Connection timeout"
            )
        return HealthCheckResult(
            url=url,
            status=HealthStatus.ERROR,
            status_code=None,
            response_time_ms=(time.time() - start_time) * 1000,
            error_message=str(e.reason)
        )
    
    except Exception as e:
        return HealthCheckResult(
            url=url,
            status=HealthStatus.ERROR,
            status_code=None,
            response_time_ms=(time.time() - start_time) * 1000,
            error_message=str(e)
        )


def batch_health_check(
    urls: List[str],
    timeout: float = 5.0,
    max_workers: int = 10
) -> List[HealthCheckResult]:
    """
    批量健康检查
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_http_health, url, timeout): url 
            for url in urls
        }
        
        for future in futures:
            results.append(future.result())
    
    return results


class HealthChecker:
    """
    持续健康检查器
    支持连续失败阈值告警
    """
    
    def __init__(
        self, 
        url: str, 
        timeout: float = 5.0,
        failure_threshold: int = 3
    ):
        self.url = url
        self.timeout = timeout
        self.failure_threshold = failure_threshold
        self.consecutive_failures = 0
        self.is_healthy = True
        self.history: List[HealthCheckResult] = []
    
    def check(self) -> HealthCheckResult:
        result = check_http_health(self.url, self.timeout)
        self.history.append(result)
        
        # 保留最近100条记录
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        if result.status == HealthStatus.HEALTHY:
            self.consecutive_failures = 0
            self.is_healthy = True
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.failure_threshold:
                self.is_healthy = False
        
        return result
    
    def get_availability(self) -> float:
        """计算可用性百分比"""
        if not self.history:
            return 100.0
        
        healthy_count = sum(
            1 for r in self.history 
            if r.status == HealthStatus.HEALTHY
        )
        return round(healthy_count / len(self.history) * 100, 2)
    
    def get_avg_response_time(self) -> float:
        """计算平均响应时间"""
        if not self.history:
            return 0.0
        
        times = [r.response_time_ms for r in self.history if r.status == HealthStatus.HEALTHY]
        return round(sum(times) / len(times), 2) if times else 0.0
```

### 考察点
- HTTP协议理解
- urllib库使用
- 错误处理
- 状态管理

---

## 题目4：实现简单的负载均衡器 ⭐⭐⭐

### 题目描述

实现一个支持多种策略的负载均衡器：
1. 轮询（Round Robin）
2. 加权轮询（Weighted Round Robin）
3. 最少连接（Least Connections）
4. 一致性哈希（Consistent Hashing）

### Python3 解答

```python
import hashlib
import bisect
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from dataclasses import dataclass
from collections import defaultdict
import threading

@dataclass
class Backend:
    host: str
    port: int
    weight: int = 1
    is_healthy: bool = True
    
    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


class LoadBalancer(ABC):
    """负载均衡器抽象基类"""
    
    @abstractmethod
    def get_backend(self, key: str = None) -> Optional[Backend]:
        pass
    
    @abstractmethod
    def add_backend(self, backend: Backend):
        pass
    
    @abstractmethod
    def remove_backend(self, backend: Backend):
        pass


class RoundRobinLB(LoadBalancer):
    """轮询负载均衡"""
    
    def __init__(self):
        self.backends: List[Backend] = []
        self.current_index = 0
        self.lock = threading.Lock()
    
    def get_backend(self, key: str = None) -> Optional[Backend]:
        with self.lock:
            healthy_backends = [b for b in self.backends if b.is_healthy]
            if not healthy_backends:
                return None
            
            backend = healthy_backends[self.current_index % len(healthy_backends)]
            self.current_index += 1
            return backend
    
    def add_backend(self, backend: Backend):
        with self.lock:
            self.backends.append(backend)
    
    def remove_backend(self, backend: Backend):
        with self.lock:
            self.backends = [b for b in self.backends if b.address != backend.address]


class WeightedRoundRobinLB(LoadBalancer):
    """加权轮询负载均衡"""
    
    def __init__(self):
        self.backends: List[Backend] = []
        self.current_weights: Dict[str, int] = {}
        self.lock = threading.Lock()
    
    def get_backend(self, key: str = None) -> Optional[Backend]:
        with self.lock:
            healthy_backends = [b for b in self.backends if b.is_healthy]
            if not healthy_backends:
                return None
            
            # 平滑加权轮询算法
            total_weight = sum(b.weight for b in healthy_backends)
            
            # 增加当前权重
            for b in healthy_backends:
                self.current_weights[b.address] = \
                    self.current_weights.get(b.address, 0) + b.weight
            
            # 选择当前权重最大的
            best = max(healthy_backends, 
                      key=lambda b: self.current_weights.get(b.address, 0))
            
            # 减去总权重
            self.current_weights[best.address] -= total_weight
            
            return best
    
    def add_backend(self, backend: Backend):
        with self.lock:
            self.backends.append(backend)
            self.current_weights[backend.address] = 0
    
    def remove_backend(self, backend: Backend):
        with self.lock:
            self.backends = [b for b in self.backends if b.address != backend.address]
            self.current_weights.pop(backend.address, None)


class LeastConnectionsLB(LoadBalancer):
    """最少连接负载均衡"""
    
    def __init__(self):
        self.backends: List[Backend] = []
        self.connections: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
    
    def get_backend(self, key: str = None) -> Optional[Backend]:
        with self.lock:
            healthy_backends = [b for b in self.backends if b.is_healthy]
            if not healthy_backends:
                return None
            
            # 选择连接数最少的
            best = min(healthy_backends, 
                      key=lambda b: self.connections[b.address])
            self.connections[best.address] += 1
            return best
    
    def release_connection(self, backend: Backend):
        """释放连接"""
        with self.lock:
            if self.connections[backend.address] > 0:
                self.connections[backend.address] -= 1
    
    def add_backend(self, backend: Backend):
        with self.lock:
            self.backends.append(backend)
    
    def remove_backend(self, backend: Backend):
        with self.lock:
            self.backends = [b for b in self.backends if b.address != backend.address]
            self.connections.pop(backend.address, None)


class ConsistentHashLB(LoadBalancer):
    """一致性哈希负载均衡"""
    
    def __init__(self, replicas: int = 100):
        self.replicas = replicas  # 虚拟节点数
        self.ring: Dict[int, Backend] = {}
        self.sorted_keys: List[int] = []
        self.backends: List[Backend] = []
        self.lock = threading.Lock()
    
    def _hash(self, key: str) -> int:
        """计算哈希值"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def get_backend(self, key: str = None) -> Optional[Backend]:
        with self.lock:
            if not self.ring:
                return None
            
            if key is None:
                key = str(id(self))
            
            hash_key = self._hash(key)
            
            # 二分查找第一个大于等于hash_key的节点
            idx = bisect.bisect(self.sorted_keys, hash_key)
            if idx == len(self.sorted_keys):
                idx = 0
            
            backend = self.ring[self.sorted_keys[idx]]
            
            # 如果不健康，顺时针找下一个
            attempts = 0
            while not backend.is_healthy and attempts < len(self.backends):
                idx = (idx + 1) % len(self.sorted_keys)
                backend = self.ring[self.sorted_keys[idx]]
                attempts += 1
            
            return backend if backend.is_healthy else None
    
    def add_backend(self, backend: Backend):
        with self.lock:
            self.backends.append(backend)
            for i in range(self.replicas):
                virtual_key = f"{backend.address}:{i}"
                hash_key = self._hash(virtual_key)
                self.ring[hash_key] = backend
                bisect.insort(self.sorted_keys, hash_key)
    
    def remove_backend(self, backend: Backend):
        with self.lock:
            self.backends = [b for b in self.backends if b.address != backend.address]
            for i in range(self.replicas):
                virtual_key = f"{backend.address}:{i}"
                hash_key = self._hash(virtual_key)
                self.ring.pop(hash_key, None)
                if hash_key in self.sorted_keys:
                    self.sorted_keys.remove(hash_key)


# 使用示例
def demo():
    backends = [
        Backend("server1", 8080, weight=3),
        Backend("server2", 8080, weight=2),
        Backend("server3", 8080, weight=1),
    ]
    
    # 一致性哈希示例
    lb = ConsistentHashLB()
    for b in backends:
        lb.add_backend(b)
    
    # 相同key总是路由到相同后端（适合缓存场景）
    for key in ["user:123", "user:456", "user:123"]:
        backend = lb.get_backend(key)
        print(f"{key} -> {backend.address}")
```

### 考察点
- 负载均衡算法
- 一致性哈希原理
- 线程安全
- 抽象类设计

---

## 题目5：实现连接池 ⭐⭐⭐

### 题目描述

实现一个通用的连接池，支持：
1. 最大连接数限制
2. 连接超时获取
3. 连接健康检查
4. 自动回收过期连接

### Python3 解答

```python
import queue
import threading
import time
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager

T = TypeVar('T')

@dataclass
class PooledConnection(Generic[T]):
    """池化连接包装"""
    connection: T
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    
    def is_expired(self, max_lifetime: float) -> bool:
        return time.time() - self.created_at > max_lifetime
    
    def is_idle_expired(self, max_idle_time: float) -> bool:
        return time.time() - self.last_used_at > max_idle_time


class ConnectionFactory(ABC, Generic[T]):
    """连接工厂抽象类"""
    
    @abstractmethod
    def create(self) -> T:
        pass
    
    @abstractmethod
    def validate(self, connection: T) -> bool:
        pass
    
    @abstractmethod
    def close(self, connection: T):
        pass


class ConnectionPool(Generic[T]):
    """通用连接池"""
    
    def __init__(
        self,
        factory: ConnectionFactory[T],
        min_size: int = 1,
        max_size: int = 10,
        max_lifetime: float = 3600,
        max_idle_time: float = 600,
        acquire_timeout: float = 30
    ):
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size
        self.max_lifetime = max_lifetime
        self.max_idle_time = max_idle_time
        self.acquire_timeout = acquire_timeout
        
        self.pool: queue.Queue[PooledConnection[T]] = queue.Queue()
        self.size = 0
        self.lock = threading.Lock()
        self.closed = False
        
        # 初始化最小连接数
        self._init_pool()
        
        # 启动清理线程
        self._start_cleaner()
    
    def _init_pool(self):
        """初始化连接池"""
        for _ in range(self.min_size):
            self._create_connection()
    
    def _create_connection(self) -> Optional[PooledConnection[T]]:
        """创建新连接"""
        with self.lock:
            if self.size >= self.max_size:
                return None
            self.size += 1
        
        try:
            conn = self.factory.create()
            pooled = PooledConnection(connection=conn)
            return pooled
        except Exception:
            with self.lock:
                self.size -= 1
            raise
    
    def acquire(self, timeout: float = None) -> T:
        """获取连接"""
        if self.closed:
            raise RuntimeError("Pool is closed")
        
        timeout = timeout or self.acquire_timeout
        deadline = time.time() + timeout
        
        while True:
            # 尝试从池中获取
            try:
                pooled = self.pool.get(block=False)
                
                # 检查连接是否有效
                if pooled.is_expired(self.max_lifetime):
                    self._destroy_connection(pooled)
                    continue
                
                if not self.factory.validate(pooled.connection):
                    self._destroy_connection(pooled)
                    continue
                
                pooled.last_used_at = time.time()
                return pooled.connection
                
            except queue.Empty:
                # 尝试创建新连接
                pooled = self._create_connection()
                if pooled:
                    return pooled.connection
                
                # 等待连接可用
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError("Acquire connection timeout")
                
                try:
                    pooled = self.pool.get(timeout=min(remaining, 1.0))
                    if self.factory.validate(pooled.connection):
                        pooled.last_used_at = time.time()
                        return pooled.connection
                    self._destroy_connection(pooled)
                except queue.Empty:
                    continue
    
    def release(self, connection: T):
        """释放连接"""
        if self.closed:
            self.factory.close(connection)
            return
        
        pooled = PooledConnection(connection=connection)
        
        if pooled.is_expired(self.max_lifetime):
            self._destroy_connection(pooled)
        else:
            self.pool.put(pooled)
    
    def _destroy_connection(self, pooled: PooledConnection[T]):
        """销毁连接"""
        with self.lock:
            self.size -= 1
        try:
            self.factory.close(pooled.connection)
        except Exception:
            pass
    
    @contextmanager
    def connection(self):
        """上下文管理器获取连接"""
        conn = self.acquire()
        try:
            yield conn
        finally:
            self.release(conn)
    
    def _start_cleaner(self):
        """启动清理线程"""
        def cleaner():
            while not self.closed:
                time.sleep(60)
                self._cleanup_idle()
        
        thread = threading.Thread(target=cleaner, daemon=True)
        thread.start()
    
    def _cleanup_idle(self):
        """清理空闲连接"""
        to_check = []
        try:
            while True:
                pooled = self.pool.get(block=False)
                to_check.append(pooled)
        except queue.Empty:
            pass
        
        for pooled in to_check:
            if pooled.is_idle_expired(self.max_idle_time) and self.size > self.min_size:
                self._destroy_connection(pooled)
            else:
                self.pool.put(pooled)
    
    def close(self):
        """关闭连接池"""
        self.closed = True
        while True:
            try:
                pooled = self.pool.get(block=False)
                self._destroy_connection(pooled)
            except queue.Empty:
                break
    
    def stats(self) -> dict:
        """获取连接池统计"""
        return {
            'size': self.size,
            'available': self.pool.qsize(),
            'in_use': self.size - self.pool.qsize()
        }


# TCP连接工厂示例
import socket

class TCPConnectionFactory(ConnectionFactory[socket.socket]):
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
    
    def create(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        return sock
    
    def validate(self, connection: socket.socket) -> bool:
        try:
            # 尝试peek数据来验证连接
            connection.setblocking(False)
            try:
                connection.recv(1, socket.MSG_PEEK)
            except BlockingIOError:
                pass  # 没有数据可读，连接正常
            except Exception:
                return False
            finally:
                connection.setblocking(True)
            return True
        except Exception:
            return False
    
    def close(self, connection: socket.socket):
        try:
            connection.close()
        except Exception:
            pass
```

### 考察点
- 连接池设计模式
- 资源管理
- 线程安全
- 泛型编程
- 上下文管理器

---

## 题目6：实现简单的DNS解析缓存 ⭐⭐

### 题目描述

实现一个DNS解析结果的本地缓存，支持TTL过期。

### Python3 解答

```python
import socket
import time
import threading
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class DNSCacheEntry:
    addresses: List[str]
    created_at: float
    ttl: float  # seconds
    
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl


class DNSCache:
    """DNS解析结果缓存"""
    
    def __init__(self, default_ttl: float = 300, max_entries: int = 1000):
        self.default_ttl = default_ttl
        self.max_entries = max_entries
        self.cache: Dict[str, DNSCacheEntry] = {}
        self.lock = threading.RLock()
    
    def resolve(self, hostname: str, ttl: float = None) -> List[str]:
        """
        解析主机名，优先使用缓存
        """
        ttl = ttl or self.default_ttl
        
        with self.lock:
            # 检查缓存
            entry = self.cache.get(hostname)
            if entry and not entry.is_expired():
                return entry.addresses
        
        # 缓存未命中或已过期，执行解析
        try:
            result = socket.getaddrinfo(hostname, None, socket.AF_INET)
            addresses = list(set(r[4][0] for r in result))
        except socket.gaierror:
            addresses = []
        
        # 更新缓存
        with self.lock:
            self._evict_if_needed()
            self.cache[hostname] = DNSCacheEntry(
                addresses=addresses,
                created_at=time.time(),
                ttl=ttl
            )
        
        return addresses
    
    def _evict_if_needed(self):
        """如果缓存满了，删除过期条目"""
        if len(self.cache) >= self.max_entries:
            # 先删除过期的
            expired = [k for k, v in self.cache.items() if v.is_expired()]
            for k in expired:
                del self.cache[k]
            
            # 如果还是满，删除最旧的
            if len(self.cache) >= self.max_entries:
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k].created_at)
                del self.cache[oldest_key]
    
    def invalidate(self, hostname: str):
        """使某条目失效"""
        with self.lock:
            self.cache.pop(hostname, None)
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
    
    def stats(self) -> Dict:
        """获取缓存统计"""
        with self.lock:
            total = len(self.cache)
            expired = sum(1 for v in self.cache.values() if v.is_expired())
            return {
                'total_entries': total,
                'expired_entries': expired,
                'active_entries': total - expired
            }


class SmartDNSResolver:
    """
    智能DNS解析器
    支持多IP轮询和健康检查
    """
    
    def __init__(self, cache_ttl: float = 300):
        self.cache = DNSCache(default_ttl=cache_ttl)
        self.current_index: Dict[str, int] = {}
        self.unhealthy_ips: Dict[str, float] = {}  # ip -> unhealthy_until
        self.lock = threading.Lock()
    
    def resolve(self, hostname: str) -> Optional[str]:
        """
        解析主机名，返回单个健康的IP
        使用轮询策略
        """
        addresses = self.cache.resolve(hostname)
        if not addresses:
            return None
        
        with self.lock:
            # 过滤掉不健康的IP
            now = time.time()
            healthy = [
                ip for ip in addresses 
                if self.unhealthy_ips.get(ip, 0) < now
            ]
            
            if not healthy:
                # 所有IP都不健康，返回任意一个
                healthy = addresses
            
            # 轮询
            idx = self.current_index.get(hostname, 0)
            ip = healthy[idx % len(healthy)]
            self.current_index[hostname] = idx + 1
            
            return ip
    
    def mark_unhealthy(self, ip: str, duration: float = 60):
        """标记IP为不健康"""
        with self.lock:
            self.unhealthy_ips[ip] = time.time() + duration
    
    def mark_healthy(self, ip: str):
        """标记IP为健康"""
        with self.lock:
            self.unhealthy_ips.pop(ip, None)
```

### 考察点
- DNS解析
- 缓存设计
- TTL概念
- 线程安全

---

## 题目7：实现限流器 ⭐⭐⭐

### 题目描述

实现多种限流算法：
1. 固定窗口计数器
2. 滑动窗口计数器
3. 令牌桶
4. 漏桶

### Python3 解答

```python
import time
import threading
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque

class RateLimiter(ABC):
    """限流器抽象基类"""
    
    @abstractmethod
    def allow(self) -> bool:
        """是否允许请求通过"""
        pass


class FixedWindowLimiter(RateLimiter):
    """
    固定窗口计数器
    简单但存在边界突发问题
    """
    
    def __init__(self, limit: int, window_seconds: int = 1):
        self.limit = limit
        self.window_seconds = window_seconds
        self.count = 0
        self.window_start = time.time()
        self.lock = threading.Lock()
    
    def allow(self) -> bool:
        with self.lock:
            now = time.time()
            
            # 检查是否进入新窗口
            if now - self.window_start >= self.window_seconds:
                self.window_start = now
                self.count = 0
            
            if self.count < self.limit:
                self.count += 1
                return True
            return False


class SlidingWindowLimiter(RateLimiter):
    """
    滑动窗口计数器
    更精确的限流
    """
    
    def __init__(self, limit: int, window_seconds: int = 1):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: Deque[float] = deque()
        self.lock = threading.Lock()
    
    def allow(self) -> bool:
        with self.lock:
            now = time.time()
            window_start = now - self.window_seconds
            
            # 移除过期的请求记录
            while self.requests and self.requests[0] < window_start:
                self.requests.popleft()
            
            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True
            return False


class TokenBucketLimiter(RateLimiter):
    """
    令牌桶算法
    允许突发流量，长期保持平均速率
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        rate: 每秒生成的令牌数
        capacity: 桶的最大容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def allow(self, tokens: int = 1) -> bool:
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_time(self, tokens: int = 1) -> float:
        """计算需要等待多长时间才能获取令牌"""
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                return 0
            return (tokens - self.tokens) / self.rate


class LeakyBucketLimiter(RateLimiter):
    """
    漏桶算法
    平滑输出，不允许突发
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        rate: 每秒处理的请求数（漏出速率）
        capacity: 桶的最大容量
        """
        self.rate = rate
        self.capacity = capacity
        self.water = 0
        self.last_leak = time.time()
        self.lock = threading.Lock()
    
    def _leak(self):
        """漏出水（处理请求）"""
        now = time.time()
        elapsed = now - self.last_leak
        leaked = elapsed * self.rate
        self.water = max(0, self.water - leaked)
        self.last_leak = now
    
    def allow(self) -> bool:
        with self.lock:
            self._leak()
            
            if self.water < self.capacity:
                self.water += 1
                return True
            return False


class SlidingWindowLogLimiter(RateLimiter):
    """
    滑动窗口日志算法
    精确但内存占用较大
    """
    
    def __init__(self, limit: int, window_seconds: int = 1, precision: int = 10):
        """
        precision: 子窗口数量，越大越精确
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self.precision = precision
        self.sub_window = window_seconds / precision
        self.counters: Deque[tuple] = deque()  # (sub_window_id, count)
        self.current_count = 0
        self.lock = threading.Lock()
    
    def allow(self) -> bool:
        with self.lock:
            now = time.time()
            current_window = int(now / self.sub_window)
            window_start = current_window - self.precision + 1
            
            # 清理过期的子窗口
            while self.counters and self.counters[0][0] < window_start:
                _, count = self.counters.popleft()
                self.current_count -= count
            
            if self.current_count < self.limit:
                # 更新当前子窗口的计数
                if self.counters and self.counters[-1][0] == current_window:
                    window_id, count = self.counters.pop()
                    self.counters.append((window_id, count + 1))
                else:
                    self.counters.append((current_window, 1))
                self.current_count += 1
                return True
            return False


# 使用装饰器
def rate_limit(limiter: RateLimiter):
    """限流装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if limiter.allow():
                return func(*args, **kwargs)
            raise Exception("Rate limit exceeded")
        return wrapper
    return decorator


# 使用示例
limiter = TokenBucketLimiter(rate=10, capacity=100)

@rate_limit(limiter)
def api_call():
    return "success"
```

### 考察点
- 限流算法原理
- 各算法优缺点对比
- 线程安全
- 装饰器模式

---

## 总结

| 题目 | 难度 | 核心考点 |
|------|------|----------|
| 端口扫描器 | ⭐⭐ | Socket、并发 |
| 进程监控 | ⭐⭐ | /proc文件系统、系统调用 |
| HTTP健康检查 | ⭐⭐ | HTTP协议、超时处理 |
| 负载均衡器 | ⭐⭐⭐ | 负载均衡算法、一致性哈希 |
| 连接池 | ⭐⭐⭐ | 资源管理、线程安全 |
| DNS缓存 | ⭐⭐ | DNS、缓存设计 |
| 限流器 | ⭐⭐⭐ | 限流算法、令牌桶/漏桶 |

**SRE面试关键**：
1. 理解底层原理比背API更重要
2. 线程安全是必考点
3. 熟悉各种算法的优缺点和适用场景
4. 能够根据需求选择合适的方案

---

## 相关文章

- [上一篇：SRE笔试题-日志与文本处理](@/articles/sre/sre-15-SRE笔试题-日志与文本处理.md)
- [下一篇：SRE笔试题-数据结构与算法](@/articles/sre/sre-17-SRE笔试题-数据结构与算法.md)
