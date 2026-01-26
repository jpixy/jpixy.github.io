+++
title = "06.Python Concepts"
description = "Python核心概念速查：GIL、装饰器、生成器、元类、内存管理等关键概念详解"
date = 2026-01-26
draft = false
[taxonomies]
tags = ["Glossary", "Python", "Reference"]
+++

# Python Concepts

本索引收录Python的核心概念，涵盖语言特性、并发模型、性能优化等。

---

## 一、语言核心

### 1.1 GIL (Global Interpreter Lock)

**定义**：CPython解释器中的全局互斥锁，确保同一时刻只有一个线程执行Python字节码。

**影响**：
- CPU密集型任务无法通过多线程并行加速
- I/O密集型任务不受影响（I/O时释放GIL）

**绕过GIL的方法**：

| 方法 | 适用场景 | 复杂度 |
|------|----------|--------|
| multiprocessing | CPU密集 | 低 |
| C扩展(释放GIL) | 计算密集 | 高 |
| Cython | 计算密集 | 中 |
| Numba | 数值计算 | 低 |

```python
# 多进程绕过GIL
from multiprocessing import Pool

def cpu_intensive(x):
    return sum(i*i for i in range(x))

with Pool(4) as p:
    results = p.map(cpu_intensive, [10**6]*4)  # 4核并行
```

**C扩展释放GIL**：
```c
// 在C代码中
Py_BEGIN_ALLOW_THREADS
// 这里可以并行执行
Py_END_ALLOW_THREADS
```

**详细文章**：[Python性能优化-多进程与GIL](/articles/python/py-50-Python性能优化-多进程与GIL/)

---

### 1.2 Decorator (装饰器)

**定义**：修改或增强函数/类行为的语法糖。本质是接受函数并返回函数的高阶函数。

**基本原理**：
```python
@decorator
def func():
    pass

# 等价于
def func():
    pass
func = decorator(func)
```

**实现装饰器**：
```python
import functools

# 基础装饰器
def timer(func):
    @functools.wraps(func)  # 保留原函数元信息
    def wrapper(*args, **kwargs):
        import time
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {time.perf_counter()-start:.4f}s")
        return result
    return wrapper

# 带参数的装饰器
def retry(max_attempts=3, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise
        return wrapper
    return decorator

@timer
@retry(max_attempts=5, exceptions=(IOError,))
def fetch_data():
    ...
```

**类装饰器**：
```python
def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class Database:
    pass
```

**详细文章**：[Python装饰器详解](/articles/python/py-04-装饰器详解/)

---

### 1.3 Generator (生成器)

**定义**：使用`yield`关键字的函数，返回一个迭代器。按需产生值，而非一次性生成。

**优势**：
- 内存效率：处理大数据集无需全部加载
- 惰性求值：只在需要时计算
- 可以表示无限序列

```python
# 生成器函数
def count_up(start=0):
    while True:
        yield start
        start += 1

# 生成器表达式
squares = (x**2 for x in range(10))  # 不占用内存

# 处理大文件
def read_large_file(path):
    with open(path) as f:
        for line in f:
            yield line.strip()

# 内存对比
sum([x**2 for x in range(10**8)])  # 列表推导：占用GB内存
sum(x**2 for x in range(10**8))    # 生成器：O(1)内存
```

**yield from（委托生成器）**：
```python
def chain(*iterables):
    for it in iterables:
        yield from it

list(chain([1,2], [3,4]))  # [1, 2, 3, 4]
```

---

### 1.4 Context Manager (上下文管理器)

**定义**：实现`__enter__`和`__exit__`方法的对象，用于资源管理。

```python
# 类实现
class FileManager:
    def __init__(self, path, mode):
        self.path = path
        self.mode = mode
    
    def __enter__(self):
        self.file = open(self.path, self.mode)
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        return False  # 不吞掉异常

# 使用contextlib简化
from contextlib import contextmanager

@contextmanager
def file_manager(path, mode):
    f = open(path, mode)
    try:
        yield f
    finally:
        f.close()

# 使用
with file_manager('data.txt', 'r') as f:
    content = f.read()
```

**详细文章**：[Python上下文管理器](/articles/python/py-06-上下文管理器/)

---

### 1.5 Walrus Operator := (海象运算符)

**定义**：Python 3.8引入的赋值表达式，允许在表达式中同时赋值和求值。

**为什么有用**：
- 减少重复计算
- 代码更简洁
- 在条件表达式中特别有用

```python
# 传统方式：计算两次或额外变量
data = get_data()
if data:
    process(data)

# 海象运算符：一次赋值
if (data := get_data()):
    process(data)

# 在循环中
while (line := file.readline()):
    process(line)

# 在推导式中
results = [y for x in data if (y := expensive_func(x)) > threshold]

# 在匹配模式中（Python 3.10+）
match get_status():
    case status if (code := status.code) > 400:
        handle_error(code)
```

**注意**：需要括号包围赋值表达式

---

### 1.6 Dataclass (数据类)

**定义**：Python 3.7引入的装饰器，自动生成`__init__`、`__repr__`、`__eq__`等方法。

**为什么使用**：
- 减少样板代码
- 类型注解清晰
- 支持不可变、排序等特性

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Order:
    order_id: int
    symbol: str
    price: float
    quantity: int
    side: str = "BUY"  # 默认值
    
# 自动生成的方法
order = Order(1, "AAPL", 150.0, 100)
print(order)  # Order(order_id=1, symbol='AAPL', price=150.0, quantity=100, side='BUY')
order2 = Order(1, "AAPL", 150.0, 100)
print(order == order2)  # True
```

**高级特性**：
```python
@dataclass(frozen=True)  # 不可变
class ImmutableOrder:
    order_id: int
    price: float

@dataclass(order=True)  # 支持比较运算符
class PricedItem:
    price: float
    name: str = field(compare=False)  # 不参与比较

# 带默认工厂的字段
@dataclass
class Portfolio:
    holdings: List[str] = field(default_factory=list)

# __post_init__后处理
@dataclass
class Trade:
    price: float
    quantity: int
    value: float = field(init=False)
    
    def __post_init__(self):
        self.value = self.price * self.quantity
```

**与NamedTuple对比**：
| 特性 | dataclass | NamedTuple |
|------|-----------|------------|
| 可变 | 默认可变 | 不可变 |
| 继承 | 支持 | 有限 |
| 内存 | 正常 | 更少 |
| 解包 | 不支持 | 支持 |

---

## 二、面向对象

### 2.1 Metaclass (元类)

**定义**：类的类。控制类的创建过程。

**类创建过程**：
```
定义class语句
    ↓
收集类属性到字典
    ↓
确定元类（默认type）
    ↓
调用元类创建类对象
    ↓
MyClass = type('MyClass', (bases,), attrs)
```

**自定义元类**：
```python
class SingletonMeta(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    pass

db1 = Database()
db2 = Database()
assert db1 is db2  # 同一实例
```

**详细文章**：[Python元类与元编程](/articles/python/py-19-元类与元编程/)

---

### 2.2 Descriptor (描述符)

**定义**：实现`__get__`、`__set__`或`__delete__`方法的对象，可以控制属性访问。

```python
class Validator:
    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name)
    
    def __set__(self, obj, value):
        if not self.min_value <= value <= self.max_value:
            raise ValueError(f"{self.name} must be between {self.min_value} and {self.max_value}")
        obj.__dict__[self.name] = value

class Order:
    price = Validator(0, 10000)
    quantity = Validator(1, 1000)
    
order = Order()
order.price = 100      # OK
order.price = -1       # ValueError
```

**property也是描述符**：
```python
class Circle:
    def __init__(self, radius):
        self._radius = radius
    
    @property
    def radius(self):
        return self._radius
    
    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("Radius must be positive")
        self._radius = value
```

---

### 2.3 __slots__

**定义**：限制实例属性，避免使用`__dict__`，节省内存。

```python
class Point:
    __slots__ = ('x', 'y')
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
p.z = 3  # AttributeError: 'Point' object has no attribute 'z'

# 内存节省
import sys
class WithDict:
    def __init__(self):
        self.x = 1

class WithSlots:
    __slots__ = ('x',)
    def __init__(self):
        self.x = 1

print(sys.getsizeof(WithDict()))   # ~56 bytes
print(sys.getsizeof(WithSlots()))  # ~48 bytes
# 大量实例时差异明显
```

**详细文章**：[Python内存优化详解](/articles/python/py-51-Python内存优化详解/)

---

## 三、并发模型

### 3.1 Threading vs Multiprocessing

**对比**：

| 特性 | threading | multiprocessing |
|------|-----------|-----------------|
| 内存 | 共享 | 独立 |
| GIL | 受限 | 不受限 |
| 开销 | 低 | 高 |
| 通信 | 直接访问 | 需要序列化 |
| 适用 | I/O密集 | CPU密集 |

```python
# 多线程（I/O密集）
from concurrent.futures import ThreadPoolExecutor

def download(url):
    # I/O操作，GIL会释放
    return requests.get(url)

with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(download, urls)

# 多进程（CPU密集）
from concurrent.futures import ProcessPoolExecutor

def compute(data):
    # CPU计算，需要绕过GIL
    return heavy_computation(data)

with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(compute, data_list)
```

---

### 3.2 asyncio (异步IO)

**定义**：Python的异步编程框架，使用协程处理并发I/O。

**核心概念**：
- **coroutine**：async def定义的协程函数
- **await**：暂停协程，等待结果
- **event loop**：调度协程执行

```python
import asyncio

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def main():
    # 并发执行多个协程
    tasks = [fetch(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

# 运行
results = asyncio.run(main())
```

**与多线程对比**：
- asyncio：单线程，协程切换开销极低
- 多线程：线程切换有系统开销
- asyncio更适合大量并发连接

**详细文章**：[Python异步编程详解](/articles/python/py-56-Python异步编程详解/)

---

## 四、性能优化

### 4.1 NumPy Vectorization (向量化)

**定义**：使用NumPy的数组操作替代Python循环，利用底层C实现获得高性能。

```python
import numpy as np

# 慢：Python循环
def slow_sum(arr):
    total = 0
    for x in arr:
        total += x * x
    return total

# 快：向量化
def fast_sum(arr):
    return np.sum(arr ** 2)

# 性能对比（n=10^6）
# slow_sum: ~500ms
# fast_sum: ~5ms（100倍加速）
```

**向量化技巧**：
```python
# 条件操作
result = np.where(arr > 0, arr, 0)  # 替代if-else

# 布尔索引
positive = arr[arr > 0]  # 替代filter

# 广播
# (1000, 1) + (1, 1000) → (1000, 1000)
row = np.arange(1000).reshape(-1, 1)
col = np.arange(1000).reshape(1, -1)
matrix = row + col  # 无需循环
```

**详细文章**：[NumPy高性能编程](/articles/python/py-52-NumPy高性能编程/)

---

### 4.2 Cython

**定义**：Python的超集，可以编译为C代码，获得接近C的性能。

```python
# pure_python.py
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

# cython_version.pyx
cpdef int fib(int n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

# 性能对比
# Python: fib(35) ≈ 5s
# Cython: fib(35) ≈ 0.1s
```

**类型声明加速**：
```cython
import numpy as np
cimport numpy as cnp

def fast_sum(cnp.ndarray[cnp.float64_t, ndim=1] arr):
    cdef int i
    cdef int n = arr.shape[0]
    cdef double total = 0.0
    
    for i in range(n):
        total += arr[i] * arr[i]
    
    return total
```

**详细文章**：[Python性能优化-Cython详解](/articles/python/py-48-Python性能优化-Cython详解/)

---

### 4.3 Numba

**定义**：JIT编译器，使用LLVM将Python函数编译为机器码。

```python
from numba import jit

@jit(nopython=True)
def fast_sum(arr):
    total = 0.0
    for i in range(len(arr)):
        total += arr[i] * arr[i]
    return total

# 第一次调用时编译，之后接近C速度
result = fast_sum(np.random.randn(10**6))
```

**并行加速**：
```python
from numba import jit, prange

@jit(nopython=True, parallel=True)
def parallel_sum(arr):
    total = 0.0
    for i in prange(len(arr)):  # 并行循环
        total += arr[i] * arr[i]
    return total
```

**详细文章**：[Python性能优化-Numba详解](/articles/python/py-49-Python性能优化-Numba详解/)

---

### 4.4 functools.lru_cache (缓存装饰器)

**定义**：标准库提供的记忆化装饰器，缓存函数返回值避免重复计算。

**为什么重要**：
- 零成本优化重复计算
- 动态规划的简洁实现
- 数据库查询缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)  # 最多缓存128个结果
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# 无缓存：O(2^n)
# 有缓存：O(n)

# 查看缓存统计
print(fibonacci.cache_info())
# CacheInfo(hits=96, misses=100, maxsize=128, currsize=100)

# 清除缓存
fibonacci.cache_clear()
```

**Python 3.9+ 的改进**：
```python
from functools import cache  # 无大小限制的lru_cache

@cache
def expensive_computation(x, y):
    return x ** y
```

**缓存要求**：
- 参数必须是可哈希的（hashable）
- 函数必须是纯函数（相同输入产生相同输出）

```python
# 错误：列表不可哈希
@lru_cache
def bad_function(data: list):  # TypeError
    return sum(data)

# 正确：转换为元组
@lru_cache
def good_function(data: tuple):
    return sum(data)
```

---

### 4.5 Type Hints (类型注解)

**定义**：Python 3.5+引入的类型标注系统，提供静态类型检查能力。

**为什么重要**：
- IDE智能提示
- 静态分析捕获错误
- 代码文档化
- 量化项目必须使用

```python
from typing import List, Dict, Optional, Union, Callable, TypeVar

# 基本类型
def greet(name: str) -> str:
    return f"Hello, {name}"

# 容器类型
def process_orders(orders: List[Dict[str, float]]) -> float:
    return sum(o['price'] for o in orders)

# 可选类型（可能为None）
def find_order(order_id: int) -> Optional[Order]:
    return orders.get(order_id)

# 联合类型
def parse_value(v: Union[int, str]) -> int:
    return int(v)

# Python 3.10+ 简化语法
def parse_value(v: int | str) -> int:
    return int(v)

# 可调用类型
def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

# 泛型
T = TypeVar('T')
def first(items: List[T]) -> T:
    return items[0]
```

**dataclass与类型注解**：
```python
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class Order:
    symbol: str
    price: float
    quantity: int
    side: str = "BUY"
    
    # 类变量（不是实例字段）
    counter: ClassVar[int] = 0
```

**运行时类型检查**：
```python
# pydantic库提供运行时验证
from pydantic import BaseModel

class Order(BaseModel):
    symbol: str
    price: float
    quantity: int

order = Order(symbol="AAPL", price="150.5", quantity=100)
# price自动转换为float
print(order.price)  # 150.5
```

---

## 五、内存管理

### 5.1 Reference Counting (引用计数)

**定义**：Python主要的内存管理机制。每个对象维护引用计数，计数为0时立即释放。

```python
import sys

a = [1, 2, 3]
print(sys.getrefcount(a))  # 2 (a + getrefcount参数)

b = a
print(sys.getrefcount(a))  # 3

del b
print(sys.getrefcount(a))  # 2
```

**循环引用问题**：
```python
class Node:
    def __init__(self):
        self.ref = None

a = Node()
b = Node()
a.ref = b
b.ref = a  # 循环引用

del a, b  # 引用计数不为0，需要GC处理
```

---

### 5.2 Garbage Collection (垃圾回收)

**定义**：处理引用计数无法回收的循环引用。

**分代回收**：
- **0代**：新对象，频繁检查
- **1代**：存活过一次GC
- **2代**：长寿对象，很少检查

```python
import gc

# 手动触发GC
gc.collect()

# 查看GC统计
print(gc.get_stats())

# 禁用GC（HFT场景）
gc.disable()
```

**详细文章**：[Python垃圾回收机制与内存泄漏防范](/articles/python/py-18-垃圾回收与内存/)

---

## 六、延伸阅读

- [C++核心概念索引](/articles/00-glossary/glossary-05-cpp-concepts/)
- [Rust核心概念索引](/articles/00-glossary/glossary-07-rust-concepts/)
- [Python高难度面试问题](/articles/python/py-21-高难度面试问题/)
- [Python量化面试题](/articles/python/py-55-Python量化面试题/)
