+++
title = "56.Python异步编程详解"
slug = "py-56-Python异步编程详解"
date = 2026-01-21
description = "深入剖析Python异步编程，包括asyncio深入、事件循环原理、协程vs回调、aiohttp、uvloop、异步陷阱和并发模式"
[taxonomies]
tags = ["Python", "asyncio", "异步编程", "并发", "性能优化"]
+++

## 概述

异步编程是处理高并发IO的关键技术。本文深入讲解Python asyncio及其在高性能系统中的应用。

---

## 一、asyncio基础

### 1.1 协程定义

```python
import asyncio

# 定义协程
async def hello():
    print("Hello")
    await asyncio.sleep(1)  # 异步等待
    print("World")
    return "Done"

# 运行协程
result = asyncio.run(hello())
print(result)  # "Done"

# 协程对象
coro = hello()  # 返回协程对象，不执行
print(type(coro))  # <class 'coroutine'>
# 必须await或run才会执行
```

### 1.2 并发执行

```python
async def fetch_data(name, delay):
    print(f"Fetching {name}...")
    await asyncio.sleep(delay)
    print(f"Got {name}")
    return f"Data from {name}"

async def main():
    # 方式1：await逐个执行（串行）
    result1 = await fetch_data("A", 1)
    result2 = await fetch_data("B", 1)
    # 总时间：2秒
    
    # 方式2：asyncio.gather（并发）
    results = await asyncio.gather(
        fetch_data("A", 1),
        fetch_data("B", 1),
        fetch_data("C", 1)
    )
    # 总时间：1秒
    print(results)  # ["Data from A", "Data from B", "Data from C"]

asyncio.run(main())
```

### 1.3 任务创建

```python
async def background_task(name):
    while True:
        print(f"{name} working...")
        await asyncio.sleep(1)

async def main():
    # 创建任务（立即调度）
    task = asyncio.create_task(background_task("Worker"))
    
    # 主逻辑
    await asyncio.sleep(3)
    
    # 取消任务
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Task cancelled")

asyncio.run(main())
```

---

## 二、事件循环

### 2.1 事件循环原理

```python
"""
事件循环核心概念：
1. 维护一个任务队列
2. 每次迭代：
   - 检查就绪的IO事件
   - 执行可运行的协程
   - 处理定时器
3. 当协程await时，控制权返回事件循环
"""

import asyncio

async def demo():
    print("Start")
    await asyncio.sleep(0)  # 让出控制权
    print("End")

# 手动操作事件循环
loop = asyncio.new_event_loop()
try:
    loop.run_until_complete(demo())
finally:
    loop.close()
```

### 2.2 事件循环方法

```python
async def main():
    loop = asyncio.get_running_loop()
    
    # 调度回调
    loop.call_soon(print, "Called soon")
    
    # 延迟调度
    loop.call_later(1.0, print, "Called after 1s")
    
    # 在指定时间调度
    loop.call_at(loop.time() + 2.0, print, "Called at specific time")
    
    # 在线程池中运行阻塞函数
    result = await loop.run_in_executor(None, blocking_function)
    
    await asyncio.sleep(3)

def blocking_function():
    import time
    time.sleep(1)
    return "Blocking done"

asyncio.run(main())
```

### 2.3 自定义事件循环

```python
# 使用uvloop（更快的事件循环）
import uvloop

# 方式1：设置为默认
uvloop.install()
asyncio.run(main())

# 方式2：显式创建
loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)

# uvloop性能提升：
# - 基于libuv（Node.js使用的同一库）
# - 比默认事件循环快2-4倍
# - 完全兼容asyncio API
```

---

## 三、并发原语

### 3.1 锁和信号量

```python
import asyncio

# 锁
lock = asyncio.Lock()

async def protected_access(name):
    async with lock:
        print(f"{name} acquired lock")
        await asyncio.sleep(1)
        print(f"{name} releasing lock")

# 信号量（限制并发数）
semaphore = asyncio.Semaphore(3)  # 最多3个并发

async def limited_access(name):
    async with semaphore:
        print(f"{name} working")
        await asyncio.sleep(1)

async def main():
    # 10个任务，但只有3个并发执行
    tasks = [limited_access(f"Task-{i}") for i in range(10)]
    await asyncio.gather(*tasks)

asyncio.run(main())
```

### 3.2 事件和条件

```python
# 事件
event = asyncio.Event()

async def waiter():
    print("Waiting for event...")
    await event.wait()
    print("Event received!")

async def setter():
    await asyncio.sleep(2)
    print("Setting event")
    event.set()

async def main():
    await asyncio.gather(waiter(), setter())

# 条件变量
condition = asyncio.Condition()

async def consumer():
    async with condition:
        await condition.wait()
        print("Consumed")

async def producer():
    async with condition:
        print("Producing...")
        condition.notify_all()
```

### 3.3 队列

```python
import asyncio

async def producer(queue, n):
    for i in range(n):
        await queue.put(f"item-{i}")
        print(f"Produced item-{i}")
        await asyncio.sleep(0.1)
    await queue.put(None)  # 结束信号

async def consumer(queue, name):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        print(f"{name} consumed {item}")
        queue.task_done()
        await asyncio.sleep(0.2)

async def main():
    queue = asyncio.Queue(maxsize=5)
    
    await asyncio.gather(
        producer(queue, 10),
        consumer(queue, "Consumer-1"),
        consumer(queue, "Consumer-2")
    )

asyncio.run(main())
```

---

## 四、网络编程

### 4.1 aiohttp客户端

```python
import aiohttp
import asyncio

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        # 单个请求
        html = await fetch(session, 'https://example.com')
        
        # 并发多个请求
        urls = [
            'https://example.com',
            'https://python.org',
            'https://github.com',
        ]
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        for url, result in zip(urls, results):
            print(f"{url}: {len(result)} bytes")

asyncio.run(main())
```

### 4.2 aiohttp服务器

```python
from aiohttp import web

async def handle(request):
    name = request.match_info.get('name', 'World')
    text = f"Hello, {name}!"
    return web.Response(text=text)

async def handle_json(request):
    data = await request.json()
    return web.json_response({'received': data})

app = web.Application()
app.router.add_get('/', handle)
app.router.add_get('/{name}', handle)
app.router.add_post('/data', handle_json)

if __name__ == '__main__':
    web.run_app(app, port=8080)
```

### 4.3 低级网络

```python
import asyncio

async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    
    print(f'Send: {message}')
    writer.write(message.encode())
    await writer.drain()
    
    data = await reader.read(100)
    print(f'Received: {data.decode()}')
    
    writer.close()
    await writer.wait_closed()

async def tcp_echo_server(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    
    print(f"Received {message} from {addr}")
    
    writer.write(data)
    await writer.drain()
    
    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(tcp_echo_server, '127.0.0.1', 8888)
    
    async with server:
        await server.serve_forever()

asyncio.run(main())
```

---

## 五、高级模式

### 5.1 超时处理

```python
import asyncio

async def slow_operation():
    await asyncio.sleep(10)
    return "Done"

async def main():
    # 方式1：asyncio.timeout (Python 3.11+)
    try:
        async with asyncio.timeout(5):
            result = await slow_operation()
    except asyncio.TimeoutError:
        print("Operation timed out")
    
    # 方式2：asyncio.wait_for
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=5)
    except asyncio.TimeoutError:
        print("Operation timed out")
    
    # 方式3：shield（保护不被取消）
    try:
        result = await asyncio.wait_for(
            asyncio.shield(slow_operation()),
            timeout=5
        )
    except asyncio.TimeoutError:
        print("Timed out but operation continues")

asyncio.run(main())
```

### 5.2 任务组（Python 3.11+）

```python
async def fetch(url):
    await asyncio.sleep(1)
    return f"Data from {url}"

async def main():
    # TaskGroup自动等待所有任务完成
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch("url1"))
        task2 = tg.create_task(fetch("url2"))
        task3 = tg.create_task(fetch("url3"))
    
    # 所有任务完成后
    print(task1.result())
    print(task2.result())
    print(task3.result())

# 早期版本的替代
async def main_legacy():
    tasks = [
        asyncio.create_task(fetch("url1")),
        asyncio.create_task(fetch("url2")),
        asyncio.create_task(fetch("url3")),
    ]
    
    try:
        results = await asyncio.gather(*tasks)
    except Exception:
        for task in tasks:
            task.cancel()
        raise

asyncio.run(main())
```

### 5.3 上下文变量

```python
import asyncio
from contextvars import ContextVar

# 定义上下文变量
request_id: ContextVar[str] = ContextVar('request_id')

async def process_request(req_id):
    request_id.set(req_id)
    await do_work()

async def do_work():
    # 可以在任何深度获取上下文
    print(f"Processing request {request_id.get()}")
    await asyncio.sleep(1)
    print(f"Done with request {request_id.get()}")

async def main():
    await asyncio.gather(
        process_request("req-1"),
        process_request("req-2"),
        process_request("req-3")
    )

asyncio.run(main())
```

---

## 六、常见陷阱

### 6.1 阻塞调用

```python
import asyncio
import time

# 错误：阻塞整个事件循环
async def bad_example():
    time.sleep(5)  # 阻塞！
    return "Done"

# 正确：使用run_in_executor
async def good_example():
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, time.sleep, 5)
    return "Done"

# 或使用异步版本
async def best_example():
    await asyncio.sleep(5)  # 非阻塞
    return "Done"
```

### 6.2 忘记await

```python
async def fetch_data():
    await asyncio.sleep(1)
    return "Data"

async def main():
    # 错误：忘记await
    result = fetch_data()  # 返回协程对象，不执行
    print(result)  # <coroutine object ...>
    
    # 正确
    result = await fetch_data()
    print(result)  # "Data"

# RuntimeWarning: coroutine 'fetch_data' was never awaited
```

### 6.3 任务引用丢失

```python
async def background():
    await asyncio.sleep(10)
    print("Background done")

async def main():
    # 错误：任务可能被垃圾回收
    asyncio.create_task(background())  # 没有保存引用
    
    # 正确：保存任务引用
    task = asyncio.create_task(background())
    await asyncio.sleep(5)
    # task仍然存在

# 最佳实践：使用集合保存任务
background_tasks = set()

async def main_best():
    task = asyncio.create_task(background())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
```

### 6.4 异常处理

```python
async def might_fail():
    raise ValueError("Oops")

async def main():
    # 问题：gather默认不传播异常
    results = await asyncio.gather(
        might_fail(),
        asyncio.sleep(1),
        return_exceptions=True  # 异常作为结果返回
    )
    
    for result in results:
        if isinstance(result, Exception):
            print(f"Got exception: {result}")
    
    # 或让异常传播
    try:
        results = await asyncio.gather(
            might_fail(),
            asyncio.sleep(1),
            return_exceptions=False  # 默认
        )
    except ValueError as e:
        print(f"Caught: {e}")

asyncio.run(main())
```

---

## 七、性能优化

### 7.1 使用uvloop

```python
import uvloop
import asyncio

# 安装uvloop
uvloop.install()

# 性能对比
async def benchmark():
    for _ in range(10000):
        await asyncio.sleep(0)

# uvloop通常比默认循环快2-4倍
```

### 7.2 连接池

```python
import aiohttp

async def main():
    # 使用连接池
    connector = aiohttp.TCPConnector(
        limit=100,  # 最大连接数
        limit_per_host=30,  # 每主机最大连接
        keepalive_timeout=30,  # 保活时间
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch(session, url) for url in urls]
        await asyncio.gather(*tasks)
```

### 7.3 批量处理

```python
async def process_batch(items, batch_size=100):
    """分批处理，避免同时创建太多任务"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_item(item) for item in batch]
        )
        results.extend(batch_results)
    
    return results
```

---

## 总结

| 场景 | 推荐方案 |
|------|----------|
| HTTP客户端 | aiohttp |
| HTTP服务器 | aiohttp/FastAPI |
| 更快事件循环 | uvloop |
| 并发控制 | Semaphore |
| 任务管理 | TaskGroup |

**最佳实践**：
1. 永远不要在协程中使用阻塞调用
2. 使用uvloop提升性能
3. 正确处理任务引用
4. 使用Semaphore限制并发
5. 记得处理异常和取消
