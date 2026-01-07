# Python并发与并行编程全面详解
## 一、核心概念区分
### 1. 并发(Concurrency) vs 并行(Parallelism)
+ **并发**：多个任务交替执行，看似同时（单核CPU）
+ **并行**：多个任务真正同时执行（多核CPU）

### 2. 线程 vs 进程 vs 协程
| 特性 | 线程 | 进程 | 协程 |
| --- | --- | --- | --- |
| 创建开销 | 较小 | 较大 | 极小 |
| 内存占用 | 共享进程内存 | 独立内存空间 | 共享线程内存 |
| 切换成本 | 中等 | 高 | 极低 |
| 数据安全 | 需同步 | 默认隔离 | 单线程内无需同步 |
| 适用场景 | I/O密集型 | CPU密集型 | 高并发I/O操作 |


## 二、多线程编程
### 1. threading模块基础
```python
import threading

def worker(num):
    print(f"Worker {num} starting")
    # 模拟I/O操作
    time.sleep(1)
    print(f"Worker {num} finishing")

threads = []
for i in range(5):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

### 2. 线程同步机制
#### 锁(Lock)
```python
lock = threading.Lock()
shared_data = 0

def safe_increment():
    global shared_data
    with lock:
        shared_data += 1
```

#### 其他同步原语
+ **RLock**：可重入锁
+ **Semaphore**：限制资源访问数量
+ **Event**：线程间事件通知
+ **Condition**：复杂条件同步

## 三、多进程编程
### 1. multiprocessing模块
```python
from multiprocessing import Process

def cpu_intensive_task(n):
    return sum(i*i for i in range(n))

if __name__ == '__main__':
    processes = []
    for _ in range(4):
        p = Process(target=cpu_intensive_task, args=(10**6,))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
```

### 2. 进程池(Pool)
```python
from multiprocessing import Pool

def square(x):
    return x*x

if __name__ == '__main__':
    with Pool(4) as p:
        results = p.map(square, range(10))
    print(results)
```

## 四、协程与异步编程
### 1. asyncio基础
```python
import asyncio

async def fetch_data(url):
    print(f"Fetching {url}")
    await asyncio.sleep(2)  # 模拟网络请求
    return f"Data from {url}"

async def main():
    tasks = [
        fetch_data("https://api1.com"),
        fetch_data("https://api2.com")
    ]
    results = await asyncio.gather(*tasks)
    print(results)

asyncio.run(main())
```

### 2. 协程优势
+ 轻量级：单线程内可运行数万个协程
+ 高效：无线程切换开销
+ 适合：高并发网络请求、Web服务等

## 五、通信方式
### 1. 队列(Queue)
#### 线程安全队列
```python
from queue import Queue

q = Queue()
q.put('item')
item = q.get()
```

#### 进程间队列
```python
from multiprocessing import Queue

q = Queue()
p = Process(target=worker, args=(q,))
p.start()
p.join()
```

### 2. 管道(Pipe)
```python
from multiprocessing import Pipe

parent_conn, child_conn = Pipe()
child_conn.send('message')
msg = parent_conn.recv()
```

### 3. 共享内存
```python
from multiprocessing import Value, Array

counter = Value('i', 0)  # 'i'表示整数
arr = Array('d', [0.0, 1.1, 2.2])  # 'd'表示双精度浮点数
```

## 六、线程池与进程池
### 1. ThreadPoolExecutor
```python
from concurrent.futures import ThreadPoolExecutor

def io_bound_task(n):
    time.sleep(1)
    return n*n

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(io_bound_task, i) for i in range(10)]
    results = [f.result() for f in futures]
```

### 2. ProcessPoolExecutor
```python
from concurrent.futures import ProcessPoolExecutor

def cpu_bound_task(n):
    return sum(i*i for i in range(n))

if __name__ == '__main__':
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(cpu_bound_task, range(1000, 1005)))
```

## 七、选择正确的并发模型
| 场景特征 | 推荐方案 | 原因 |
| --- | --- | --- |
| CPU密集型 | 多进程/ProcessPool | 绕过GIL限制 |
| I/O密集型 | 多线程/ThreadPool | I/O等待时释放GIL |
| 超高并发I/O | 协程/asyncio | 轻量级，无线程切换开销 |
| 需要数据隔离 | 多进程 | 进程间内存天然隔离 |
| 需要共享数据 | 多线程 | 共享内存方便但需同步 |


## 八、性能优化建议
1. **避免过度并发**：线程/进程数应与CPU核心数匹配
2. **减少锁竞争**：使用线程局部存储或不可变数据结构
3. **批量处理**：使用`map`而非循环提交单个任务
4. **异步I/O**：网络/磁盘操作优先考虑asyncio
5. **进程池预热**：避免频繁创建销毁进程的开销

## 九、常见问题解决方案
### 1. 死锁预防
+ 按固定顺序获取多个锁
+ 设置锁超时时间
+ 使用上下文管理器(`with lock`)

### 2. 进程间数据共享
+ 使用`multiprocessing.Manager`
+ 共享内存(Value/Array)
+ 消息传递(Queue/Pipe)

### 3. 协程异常处理
```python
async def safe_fetch(url):
    try:
        return await fetch(url)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
```

## 十、现代Python并发工具
1. **concurrent.futures**：高层线程/进程池接口
2. **asyncio**：异步I/O框架
3. **threading和multiprocessing**：底层控制
4. **queue和multiprocessing.Queue**：线程/进程安全队列
5. **aiohttp/httpx**：异步HTTP客户端

通过合理选择这些工具，可以构建高效、可扩展的并发应用程序，充分利用现代多核CPU的性能优势。  
  




# Python 中的共享内存：`shared_memory` 模块详解
是的，Python 3.8 及更高版本确实引入了专门的 `shared_memory` 模块，它提供了更现代、更灵活的共享内存实现方式，比传统的 `multiprocessing.Array` 和 `multiprocessing.Value` 更加强大。

## 一、`shared_memory` 模块基础
### 1. 主要组件
+ `SharedMemory`：创建和管理共享内存块
+ `ShareableList`：可在进程间共享的类似列表结构

### 2. 与传统方式的对比
| 特性 | `multiprocessing.Array/Value` | `shared_memory.SharedMemory` |
| --- | --- | --- |
| 创建方式 | 必须指定类型码 | 支持原始字节缓冲区 |
| 内存管理 | 自动管理 | 需要手动释放 |
| 灵活性 | 有限 | 更高，可配合多种库使用 |
| 跨进程共享 | 是 | 是 |
| Python 版本要求 | 所有版本 | Python 3.8+ |


## 二、`SharedMemory` 基本用法
### 1. 创建和访问共享内存
```python
from multiprocessing import shared_memory
import numpy as np

# 创建共享内存
shm = shared_memory.SharedMemory(name='example', create=True, size=1024)

# 写入数据
buffer = shm.buf
buffer[:12] = b'Hello World!'  # 写入字节数据

# 在另一个进程中访问
existing_shm = shared_memory.SharedMemory(name='example')
print(bytes(existing_shm.buf[:12]))  # 输出: b'Hello World!'

# 清理
shm.close()
existing_shm.close()
shm.unlink()  # 只有创建者需要调用unlink
```

### 2. 配合 NumPy 使用
```python
# 创建共享内存并作为NumPy数组使用
shm = shared_memory.SharedMemory(create=True, size=100*8)  # 100个float64
arr = np.ndarray((100,), dtype=np.float64, buffer=shm.buf)
arr[:] = np.random.randn(100)  # 填充随机数据

# 在另一个进程中访问
existing_shm = shared_memory.SharedMemory(name=shm.name)
arr2 = np.ndarray((100,), dtype=np.float64, buffer=existing_shm.buf)
print(arr2[:5])  # 查看前5个元素

# 清理
shm.close()
existing_shm.close()
shm.unlink()
```

## 三、`ShareableList` 用法
### 1. 基本操作
```python
from multiprocessing import shared_memory

# 创建可共享列表
sl = shared_memory.ShareableList([1, 2.5, 'text', True])

# 在另一个进程中访问
existing_sl = shared_memory.ShareableList(name=sl.shm.name)

# 修改元素
existing_sl[0] = 100
print(sl[0])  # 输出: 100

# 清理
sl.shm.close()
existing_sl.shm.close()
sl.shm.unlink()
```

### 2. 支持的数据类型
+ 基本类型：int, float, bool
+ 字符串（ASCII）
+ None
+ bytes（长度受限）

## 四、实际应用场景
### 1. 高性能数值计算
```python
import numpy as np
from multiprocessing import Process, shared_memory

def worker(shm_name, shape, dtype):
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    arr = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
    arr *= 2  # 就地修改数组
    existing_shm.close()

if __name__ == '__main__':
    # 主进程创建共享数组
    shm = shared_memory.SharedMemory(create=True, size=1000*8)
    arr = np.ndarray((1000,), dtype=np.float64, buffer=shm.buf)
    arr[:] = np.random.randn(1000)
    
    # 启动工作进程
    p = Process(target=worker, args=(shm.name, arr.shape, arr.dtype))
    p.start()
    p.join()
    
    print(arr[:5])  # 查看修改后的数据
    shm.close()
    shm.unlink()
```

### 2. 进程间通信
```python
from multiprocessing import Process, shared_memory
import time

def producer(shm_name):
    shm = shared_memory.SharedMemory(name=shm_name)
    for i in range(10):
        shm.buf[i] = i
        time.sleep(0.1)
    shm.buf[10] = 255  # 结束标志
    shm.close()

def consumer(shm_name):
    shm = shared_memory.SharedMemory(name=shm_name)
    while True:
        if shm.buf[10] == 255:
            break
        print(list(shm.buf[:10]))
        time.sleep(0.2)
    shm.close()

if __name__ == '__main__':
    shm = shared_memory.SharedMemory(create=True, size=11)
    shm.buf[10] = 0  # 初始化结束标志
    
    p1 = Process(target=producer, args=(shm.name,))
    p2 = Process(target=consumer, args=(shm.name,))
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
    
    shm.close()
    shm.unlink()
```

## 五、注意事项
1. **内存管理**：
    - 必须手动调用 `close()` 和 `unlink()`
    - `unlink()` 应由创建者调用，删除系统层面的共享内存
2. **安全性**：
    - 共享内存没有内置同步机制，需要额外加锁
    - 命名共享内存可能冲突，建议使用唯一名称
3. **平台差异**：
    - Unix 系统使用 POSIX 共享内存
    - Windows 使用内存映射文件
4. **性能考量**：
    - 适合大量数据的频繁访问
    - 小数据可能不如 Queue 或 Pipe 高效

## 六、与传统方式的对比示例
### 传统方式 (`multiprocessing.Array`)
```python
from multiprocessing import Process, Array

def worker(arr):
    arr[0] = 100

if __name__ == '__main__':
    arr = Array('i', range(10))  # 类型码'i'表示有符号整数
    p = Process(target=worker, args=(arr,))
    p.start()
    p.join()
    print(arr[:])  # 输出: [100, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### 现代方式 (`shared_memory`)
```python
from multiprocessing import Process, shared_memory

def worker(shm_name):
    shm = shared_memory.SharedMemory(name=shm_name)
    arr = shm.buf
    arr[0] = 100
    shm.close()

if __name__ == '__main__':
    shm = shared_memory.SharedMemory(create=True, size=10)
    shm.buf[:] = bytearray(range(10))
    
    p = Process(target=worker, args=(shm.name,))
    p.start()
    p.join()
    
    print(list(shm.buf[:]))  # 输出: [100, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    shm.close()
    shm.unlink()
```

## 七、最佳实践建议
1. **命名规范**：
    - 使用唯一、描述性的共享内存名称
    - 考虑使用 `uuid` 模块生成唯一名称
2. **资源清理**：

```python
shm = None
try:
    shm = shared_memory.SharedMemory(create=True, size=100)
    # 使用共享内存
finally:
    if shm:
        shm.close()
        shm.unlink()
```

    - 使用 `try/finally` 确保资源释放
3. **数据序列化**：
    - 对于复杂对象，可以结合 `pickle` 使用
    - 但要注意性能开销
4. **性能监控**：
    - 监控共享内存使用情况
    - 避免过度使用导致系统内存不足

`shared_memory` 模块为 Python 提供了更现代、更灵活的共享内存实现，特别适合需要高性能进程间通信的场景，如数值计算、大数据处理等。正确使用时可以显著提升多进程应用的性能。

  


# Python并发编程深度详解：队列、管道与应用场景全解析
## 一、队列(Queue)的深度解析与应用场景
### 1. 队列类型与特性对比
| 队列类型 | 模块 | 线程安全 | 进程安全 | 适用场景 |
| --- | --- | --- | --- | --- |
| Queue.Queue | queue | ✅ | ❌ | 多线程间通信 |
| multiprocessing.Queue | multiprocessing | ✅ | ✅ | 多进程间通信 |
| asyncio.Queue | asyncio | ✅ | ❌ | 协程间通信 |
| PriorityQueue | queue/multiprocessing | ✅ | ✅ | 需要优先级调度的任务 |
| LifoQueue | queue/multiprocessing | ✅ | ✅ | 需要后进先出(LIFO)的场景 |


### 2. 队列的典型应用场景
#### 生产者-消费者模型
```python
from queue import Queue
from threading import Thread
import random
import time

def producer(q, name):
    for i in range(5):
        item = f"产品-{name}-{i}"
        q.put(item)
        print(f"生产者 {name} 生产了 {item}")
        time.sleep(random.random())

def consumer(q):
    while True:
        item = q.get()
        if item is None:  # 终止信号
            break
        print(f"消费者 消费了 {item}")
        time.sleep(random.random() * 2)
        q.task_done()

q = Queue()
producers = [Thread(target=producer, args=(q, f"P{i}")) for i in range(3)]
consumer_thread = Thread(target=consumer, args=(q,))

for p in producers:
    p.start()
consumer_thread.start()

for p in producers:
    p.join()

q.put(None)  # 发送终止信号
consumer_thread.join()
```

**应用场景**：

+ 日志处理系统（生产者生成日志，消费者处理日志）
+ 图片处理系统（生产者获取图片URL，消费者下载处理）
+ 数据采集系统（生产者爬取数据，消费者存储数据）

#### 任务调度系统
```python
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue

q = PriorityQueue()

def worker():
    while True:
        priority, task = q.get()
        print(f"执行优先级 {priority} 的任务: {task}")
        q.task_done()

# 添加任务（优先级，任务描述）
q.put((3, "低优先级任务"))
q.put((1, "高优先级任务"))
q.put((2, "中优先级任务"))

with ThreadPoolExecutor(max_workers=2) as executor:
    executor.submit(worker)
    executor.submit(worker)
    q.join()
```

**应用场景**：

+ 医院急诊分诊系统
+ 订单处理系统（VIP订单优先）
+ 实时交易系统（高价订单优先）

### 3. 队列的高级用法
#### 批量处理模式
```python
from queue import Queue
import threading

batch_size = 10
timeout = 5  # 秒

def batch_processor(q):
    batch = []
    while True:
        try:
            item = q.get(timeout=timeout)
            batch.append(item)
            if len(batch) >= batch_size:
                process_batch(batch)
                batch = []
                q.task_done()
        except queue.Empty:
            if batch:  # 处理剩余不足batch_size的项
                process_batch(batch)
                batch = []
            break

def process_batch(items):
    print(f"处理批量数据: {items}")

q = Queue()
for i in range(25):
    q.put(f"item-{i}")

worker = threading.Thread(target=batch_processor, args=(q,))
worker.start()
worker.join()
```

## 二、管道(Pipe)的深度解析与应用场景
### 1. 管道基础与高级用法
#### 基本双向管道
```python
from multiprocessing import Pipe, Process

def worker(conn):
    conn.send("子进程发送的消息")
    print(f"子进程收到: {conn.recv()}")
    conn.close()

parent_conn, child_conn = Pipe()
p = Process(target=worker, args=(child_conn,))
p.start()

print(f"主进程收到: {parent_conn.recv()}")
parent_conn.send("主进程发送的消息")
p.join()
```

#### 单向管道优化
```python
from multiprocessing import Pipe

# 创建单向管道（parent只能recv，child只能send）
parent_conn, child_conn = Pipe(duplex=False)
```

### 2. 管道的典型应用场景
#### 实时数据流处理
```python
from multiprocessing import Pipe, Process
import time

def sensor(conn):
    for i in range(10):
        data = f"传感器数据-{i}"
        conn.send(data)
        time.sleep(0.5)
    conn.send(None)  # 结束信号

def processor(conn):
    while True:
        data = conn.recv()
        if data is None:
            break
        print(f"处理数据: {data.upper()}")
    print("处理完成")

parent_conn, child_conn = Pipe()
sensor_process = Process(target=sensor, args=(child_conn,))
processor_process = Process(target=processor, args=(parent_conn,))

sensor_process.start()
processor_process.start()

sensor_process.join()
processor_process.join()
```

**应用场景**：

+ 物联网设备数据采集
+ 实时监控系统
+ 音视频流处理

#### 进程间状态同步
```python
from multiprocessing import Pipe, Process
import time

def watchdog(conn):
    while True:
        if conn.poll(timeout=5):  # 5秒超时
            msg = conn.recv()
            if msg == "STOP":
                break
            print(f"收到心跳: {msg}")
        else:
            print("警告: 心跳丢失！")
    print("看门狗停止")

def monitored_process(conn):
    for i in range(6):
        conn.send(f"心跳-{i}")
        time.sleep(2 if i < 3 else 6)  # 模拟心跳异常
    conn.send("STOP")

parent_conn, child_conn = Pipe()
watchdog_process = Process(target=watchdog, args=(parent_conn,))
monitored_proc = Process(target=monitored_process, args=(child_conn,))

watchdog_process.start()
monitored_proc.start()

monitored_proc.join()
watchdog_process.join()
```

### 3. 管道 vs 队列选择指南
| 特性 | 管道(Pipe) | 队列(Queue) |
| --- | --- | --- |
| 连接方式 | 一对一 | 多对多 |
| 传输方向 | 默认双向/可设单向 | 总是单向 |
| 传输效率 | 更高(直接连接) | 略低(通过中间队列) |
| 数据序列化 | 需要pickle序列化 | 需要pickle序列化 |
| 适用场景 | 少量进程间直接通信 | 多生产者/消费者模型 |
| 复杂度 | 较低 | 较高 |


## 三、进程间通信综合方案
### 1. 共享内存高级用法
#### Value和Array的原子操作
```python
from multiprocessing import Process, Value, Array, RLock
import time

def increment_counter(counter, lock):
    for _ in range(1000):
        with lock:
            counter.value += 1

def modify_array(arr, lock):
    for i in range(len(arr)):
        with lock:
            arr[i] = arr[i] * 2

if __name__ == '__main__':
    counter = Value('i', 0)
    arr = Array('d', [1.0, 2.0, 3.0])
    lock = RLock()
    
    processes = [
        Process(target=increment_counter, args=(counter, lock)),
        Process(target=modify_array, args=(arr, lock))
    ]
    
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    
    print(f"最终计数器值: {counter.value}")
    print(f"最终数组内容: {list(arr)}")
```

### 2. Manager的高级应用
#### 创建共享字典和列表
```python
from multiprocessing import Manager, Process

def worker(d, l):
    d[os.getpid()] = os.getpid()
    l.append(os.getpid())

if __name__ == '__main__':
    with Manager() as manager:
        shared_dict = manager.dict()
        shared_list = manager.list()
        
        processes = [Process(target=worker, args=(shared_dict, shared_list))
                    for _ in range(5)]
        
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        
        print(f"共享字典: {shared_dict}")
        print(f"共享列表: {shared_list}")
```

## 四、实战案例分析
### 案例1：分布式网页爬虫
```python
from multiprocessing import Queue, Process
import requests
from bs4 import BeautifulSoup

def url_producer(queue, start_url):
    queue.put(start_url)
    visited = {start_url}
    
    while True:
        try:
            url = queue.get(timeout=30)
            print(f"正在抓取: {url}")
            
            try:
                response = requests.get(url, timeout=5)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 处理页面内容
                process_page(soup)
                
                # 发现新链接
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and href.startswith('http') and href not in visited:
                        visited.add(href)
                        queue.put(href)
            except Exception as e:
                print(f"抓取{url}失败: {e}")
                
            queue.task_done()
        except queue.Empty:
            break

def process_page(soup):
    # 实际的页面处理逻辑
    title = soup.title.string if soup.title else "无标题"
    print(f"处理页面: {title}")

if __name__ == '__main__':
    url_queue = Queue()
    num_workers = 4
    
    # 启动生产者
    producer = Process(target=url_producer, args=(url_queue, "http://example.com"))
    producer.start()
    
    # 启动消费者
    workers = []
    for _ in range(num_workers):
        p = Process(target=url_producer, args=(url_queue, "http://example.com"))
        p.start()
        workers.append(p)
    
    producer.join()
    for p in workers:
        p.join()
```

### 案例2：实时数据处理流水线
```python
from multiprocessing import Process, Pipe
import time
import random

def data_generator(conn):
    """模拟数据生成器"""
    while True:
        data = random.randint(1, 100)
        conn.send(data)
        time.sleep(0.1)
        if random.random() < 0.01:  # 1%概率停止
            conn.send(None)
            break

def data_filter(input_conn, output_conn):
    """过滤掉小于50的数据"""
    while True:
        data = input_conn.recv()
        if data is None:
            output_conn.send(None)
            break
        if data >= 50:
            output_conn.send(data)

def data_processor(conn):
    """数据处理单元"""
    while True:
        data = conn.recv()
        if data is None:
            break
        processed = data * 2
        print(f"处理结果: {processed}")

if __name__ == '__main__':
    # 创建管道连接
    gen_conn, filter_in_conn = Pipe()
    filter_out_conn, processor_conn = Pipe()
    
    # 创建进程
    processes = [
        Process(target=data_generator, args=(gen_conn,)),
        Process(target=data_filter, args=(filter_in_conn, filter_out_conn)),
        Process(target=data_processor, args=(processor_conn,))
    ]
    
    # 启动进程
    for p in processes:
        p.start()
    
    # 等待进程结束
    for p in processes:
        p.join()
```

## 五、性能优化与陷阱规避
### 1. 队列性能优化技巧
+ **批量操作**：使用`put_many/get_many`（如有）
+ **适当大小**：设置合理的`maxsize`避免内存溢出
+ **超时设置**：避免永久阻塞，设置合理timeout
+ **优先级**：对紧急任务使用PriorityQueue

### 2. 管道使用注意事项
+ **死锁风险**：双向管道要注意收发顺序
+ **数据量限制**：避免传输过大对象（>32MB）
+ **连接管理**：确保正确关闭所有连接
+ **异常处理**：处理管道断裂情况

### 3. 常见陷阱与解决方案
**问题1：队列阻塞导致程序挂起**

```python
# 错误示范
item = q.get()  # 如果队列为空，永久阻塞

# 正确做法
try:
    item = q.get(timeout=5.0)  # 设置超时
except queue.Empty:
    print("队列为空，超时返回")
```

**问题2：管道数据序列化失败**

```python
# 错误示范 - 尝试传递无法pickle的对象
class MyClass:
    def __init__(self):
        self.lock = threading.Lock()  # Lock对象不能被pickle

# 正确做法 - 只传递可序列化数据
def worker(conn):
    conn.send({"data": "value"})  # 基本类型和简单结构
```

**问题3：共享内存竞争条件**

```python
# 错误示范 - 无保护的共享内存访问
def unsafe_increment(counter):
    counter.value += 1  # 可能导致竞争条件

# 正确做法 - 使用锁保护
def safe_increment(counter, lock):
    with lock:
        counter.value += 1
```

## 六、现代Python并发工具推荐
1. **Celery**：分布式任务队列
2. **Dask**：并行计算库
3. **Ray**：分布式执行框架
4. **ZMQ**：高性能消息库
5. **Redis Queue**：基于Redis的任务队列

通过深入理解这些并发工具的特性和适用场景，您可以根据具体需求选择最合适的通信方式，构建高效可靠的并发应用程序。

