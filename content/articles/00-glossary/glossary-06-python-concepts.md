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

### 5.3 Shallow Copy vs Deep Copy (浅拷贝与深拷贝)

**定义**：
- **浅拷贝 (Shallow Copy)**：创建新对象，但内部的可变对象仍然共享引用
- **深拷贝 (Deep Copy)**：递归复制所有对象，完全独立

**核心理解：Python 变量是引用**

```python
# Python 中赋值是引用绑定，不是复制！
a = [1, 2, [3, 4]]
b = a           # b 和 a 指向同一个对象
b[0] = 100
print(a)        # [100, 2, [3, 4]] — a 也变了！
print(a is b)   # True — 同一个对象
```

**三种复制方式对比**：

```python
import copy

original = [1, 2, [3, 4]]

# 方式1：赋值 — 不复制，只是别名
alias = original
alias is original  # True

# 方式2：浅拷贝 — 只复制外层容器
shallow = copy.copy(original)
# 或者：shallow = original[:]
# 或者：shallow = list(original)
shallow is original              # False — 外层是新对象
shallow[2] is original[2]        # True — 内层仍共享！

# 方式3：深拷贝 — 递归复制所有层
deep = copy.deepcopy(original)
deep is original                 # False
deep[2] is original[2]           # False — 内层也是新对象
```

**浅拷贝的陷阱**：

```python
import copy

matrix = [[0] * 3 for _ in range(3)]
matrix_shallow = copy.copy(matrix)

matrix_shallow[0][0] = 999
print(matrix[0][0])  # 999 — 原矩阵也被修改了！

# 正确做法：深拷贝
matrix_deep = copy.deepcopy(matrix)
matrix_deep[0][0] = 888
print(matrix[0][0])  # 999 — 原矩阵不受影响
```

**常见浅拷贝方法**：

| 方法 | 适用类型 | 示例 |
|------|----------|------|
| `copy.copy(x)` | 任意类型 | `copy.copy(obj)` |
| 切片 `[:]` | 序列 | `lst[:]`, `s[:]` |
| 构造函数 | 容器 | `list(lst)`, `dict(d)`, `set(s)` |
| `.copy()` 方法 | list/dict/set | `lst.copy()`, `d.copy()` |
| `dict(**d)` | dict | `{**d}` |
| `[*lst]` | list | `[*lst]` |

**深拷贝注意事项**：

```python
import copy

# 1. 深拷贝比浅拷贝慢很多
%timeit copy.copy(large_list)      # ~1μs
%timeit copy.deepcopy(large_list)  # ~100μs

# 2. 深拷贝处理循环引用
a = [1, 2]
a.append(a)  # 自引用
b = copy.deepcopy(a)  # 正确处理，不会无限递归

# 3. 不可变对象不会被复制
t = (1, 2, 3)
copy.deepcopy(t) is t  # True — 元组是不可变的，直接返回原对象

# 4. 自定义深拷贝行为
class MyClass:
    def __deepcopy__(self, memo):
        # 自定义复制逻辑
        return MyClass(copy.deepcopy(self.data, memo))
```

---

### 5.4 Python vs C++ 深浅拷贝对比

**本质区别**：Python 变量是引用，C++ 变量默认是值。

| 概念 | Python | C++ |
|------|--------|-----|
| **变量本质** | 引用（指向对象） | 值（存储数据本身） |
| **赋值语义** | 引用绑定（不复制） | 值复制（调用拷贝构造） |
| **浅拷贝** | 新容器，内部引用共享 | 按位复制，指针成员指向同一地址 |
| **深拷贝** | 递归复制所有对象 | 手动实现，复制指针指向的内容 |

**Python 赋值 vs C++ 赋值**：

```python
# Python: 赋值 = 引用绑定
a = [1, 2, 3]
b = a           # b 和 a 指向同一对象
b[0] = 100      # a 也变了
```

```cpp
// C++: 赋值 = 值复制
std::vector<int> a = {1, 2, 3};
std::vector<int> b = a;  // 复制构造，b 是独立副本
b[0] = 100;              // a 不受影响！
```

**C++ 的浅拷贝问题**：

```cpp
// C++ 浅拷贝：指针成员指向同一地址
class Shallow {
    int* data;
public:
    Shallow(int val) : data(new int(val)) {}
    // 默认拷贝构造：浅拷贝
    // Shallow(const Shallow& other) : data(other.data) {}
    ~Shallow() { delete data; }  // 危险！double free
};

Shallow a(42);
Shallow b = a;  // 浅拷贝：b.data 指向 a.data 同一地址
// 析构时 double free！
```

```cpp
// C++ 深拷贝：手动实现
class Deep {
    int* data;
public:
    Deep(int val) : data(new int(val)) {}
    
    // 深拷贝构造
    Deep(const Deep& other) : data(new int(*other.data)) {}
    
    // 深拷贝赋值
    Deep& operator=(const Deep& other) {
        if (this != &other) {
            delete data;
            data = new int(*other.data);
        }
        return *this;
    }
    
    ~Deep() { delete data; }
};
```

**Python 不存在 C++ 的 double free 问题**：

```python
# Python 通过引用计数自动管理内存
class Node:
    def __init__(self, data):
        self.data = data

a = Node([1, 2, 3])
b = copy.copy(a)  # 浅拷贝：b.data 和 a.data 指向同一列表

# 不会 double free！引用计数管理内存
del a  # 引用计数 -1
del b  # 引用计数变为0时才释放
```

**快速对照表**：

| 操作 | Python | C++ |
|------|--------|-----|
| `b = a` | 引用绑定（共享对象） | 值复制（独立副本） |
| 浅拷贝列表 | `copy.copy(a)` | 默认拷贝构造（危险） |
| 深拷贝列表 | `copy.deepcopy(a)` | 需手动实现 |
| 修改 `b` 是否影响 `a` | 赋值=影响，浅拷贝=可能影响 | 赋值=不影响 |
| 内存管理 | 自动（引用计数+GC） | 手动（或用智能指针） |

**实际应用建议**：

```python
# Python 开发者常犯的错误
def append_to_list(item, lst=[]):  # 默认参数是可变对象！
    lst.append(item)
    return lst

print(append_to_list(1))  # [1]
print(append_to_list(2))  # [1, 2] — 不是 [2]！

# 正确做法
def append_to_list(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

```python
# 何时使用深拷贝
# 1. 需要修改嵌套数据结构但不影响原数据
# 2. 传递可变对象作为参数，担心被意外修改
# 3. 缓存/备份嵌套数据

# 何时使用浅拷贝
# 1. 只需要新容器，内部元素是不可变的
# 2. 性能敏感场景（深拷贝慢很多）
# 3. 明确知道不会修改内部可变对象
```

---

## 六、模块与包

### 6.1 Dunder Variables (模块级双下划线变量)

**定义**：Python 模块自动拥有的特殊变量，用于模块元信息和行为控制。

**常用变量**：

| 变量 | 类型 | 描述 |
|------|------|------|
| `__name__` | str | 模块名，直接运行时为 `'__main__'` |
| `__file__` | str | 模块文件路径 |
| `__doc__` | str | 模块文档字符串 |
| `__all__` | list | 控制 `from x import *` 的导出列表 |
| `__dict__` | dict | 模块/对象的属性字典 |
| `__package__` | str | 所属包名 |

**入口点惯用法**：
```python
# 只有直接运行时执行，被import时不执行
if __name__ == '__main__':
    main()
```

**控制导出**：
```python
__all__ = ['public_func', 'PublicClass']  # 定义 * 导入的内容
```

**获取当前文件目录**：
```python
from pathlib import Path
BASE_DIR = Path(__file__).parent.resolve()
```

**详细文章**：[Python双下划线变量详解](/articles/python/py-57-Python双下划线变量详解/)

---

## 七、Python vs C++ 易混淆概念

以下概念在 Python 和 C++ 中名字相同，但含义或行为完全不同，是跨语言开发者最容易踩的坑。

---

### 7.1 引用 (Reference)

| 概念 | Python | C++ |
|------|--------|-----|
| **本质** | 变量就是引用，指向对象 | 引用是别名，绑定到变量 |
| **可重新绑定** | ✅ 可以 | ❌ 不可以 |
| **可为空** | ✅ 可以 (`None`) | ❌ 不可以（必须初始化） |
| **语法** | 隐式（所有变量） | 显式 (`T&`) |

```python
# Python: 变量是引用，可重新绑定
a = [1, 2, 3]
b = a           # b 和 a 指向同一对象
a = [4, 5, 6]   # a 重新绑定到新对象
print(b)        # [1, 2, 3] — b 仍指向原对象
```

```cpp
// C++: 引用是别名，不能重新绑定
std::vector<int> a = {1, 2, 3};
std::vector<int>& b = a;  // b 是 a 的别名
// b = other;  // 这不是重新绑定！是赋值操作
b[0] = 100;   // a 也变了
```

**易错点**：Python 开发者以为 C++ 引用可以像 Python 那样重新指向另一个对象。

---

### 7.2 静态 (Static)

| 用法 | Python | C++ |
|------|--------|-----|
| **类变量** | 类体内直接定义 | `static` 成员变量 |
| **静态方法** | `@staticmethod` | `static` 成员函数 |
| **局部静态** | ❌ 不支持 | ✅ 保持值跨调用 |
| **静态链接** | ❌ 无概念 | ✅ 内部链接 |

```python
# Python: 类变量 vs 实例变量
class Counter:
    count = 0  # 类变量（所有实例共享）
    
    def __init__(self):
        Counter.count += 1
        self.id = Counter.count  # 实例变量
```

```cpp
// C++: static 有多重含义
class Counter {
    static int count;  // 类静态变量（需要类外定义）
public:
    int id;
    Counter() : id(++count) {}
    static int getCount() { return count; }  // 静态方法
};
int Counter::count = 0;  // 类外定义

// 局部静态变量
int nextId() {
    static int id = 0;  // 只初始化一次，保持值
    return ++id;
}
```

**易错点**：Python 没有 C++ 的"局部静态变量"概念，需要用闭包或类来模拟。

---

### 7.3 私有 (Private)

| 概念 | Python | C++ |
|------|--------|-----|
| **强制程度** | 约定俗成（可绕过） | 编译时强制 |
| **语法** | `_` 或 `__` 前缀 | `private:` 关键字 |
| **继承可见性** | 都可见 | 子类不可见 |

```python
# Python: "私有"只是约定，不是强制
class Account:
    def __init__(self):
        self._balance = 0      # 约定私有（单下划线）
        self.__secret = 42     # 名称修饰（双下划线）

a = Account()
print(a._balance)              # 可以访问！只是不建议
print(a._Account__secret)      # 也可以访问！名称被修饰了
```

```cpp
// C++: private 是编译时强制的
class Account {
private:
    int balance = 0;
    int secret = 42;
public:
    int getBalance() { return balance; }
};

Account a;
// a.balance;  // 编译错误！无法访问
```

**易错点**：Python 的 `__` 不是真正私有，只是名称修饰防止意外覆盖。

---

### 7.4 虚函数 / 多态 (Virtual / Polymorphism)

| 概念 | Python | C++ |
|------|--------|-----|
| **默认行为** | 所有方法都是"虚"的 | 需显式声明 `virtual` |
| **性能开销** | 每次调用都动态查找 | 虚函数有 vtable 开销 |
| **纯虚函数** | `@abstractmethod` | `virtual f() = 0` |

```python
# Python: 所有方法默认动态分发
class Animal:
    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):  # 自动覆盖，无需声明
        return "Woof!"

def make_speak(animal):
    print(animal.speak())  # 动态分发

make_speak(Dog())  # Woof!
```

```cpp
// C++: 需要显式声明 virtual
class Animal {
public:
    virtual std::string speak() { return "..."; }  // 必须声明 virtual
};

class Dog : public Animal {
public:
    std::string speak() override { return "Woof!"; }
};

void makeSpeak(Animal& animal) {
    std::cout << animal.speak();  // 多态调用
}

// 如果 speak() 不是 virtual，将调用 Animal::speak()！
```

**易错点**：C++ 忘记写 `virtual`，导致多态失效，调用基类方法。

---

### 7.5 Lambda / 闭包 (Lambda / Closure)

| 概念 | Python | C++ |
|------|--------|-----|
| **语法** | `lambda x: expr` | `[captures](params) { body }` |
| **多行** | ❌ 只能单表达式 | ✅ 支持 |
| **捕获方式** | 自动捕获（引用） | 显式指定 `[=]` `[&]` `[x]` |
| **可变性** | 可修改捕获变量 | 需要 `mutable` |

```python
# Python: 自动捕获外部变量（引用）
def make_counter():
    count = 0
    def counter():
        nonlocal count  # 需要声明才能修改
        count += 1
        return count
    return counter

# lambda 只能单表达式
add = lambda x, y: x + y
```

```cpp
// C++: 显式指定捕获方式
auto make_counter() {
    int count = 0;
    return [count]() mutable {  // 值捕获 + mutable
        return ++count;
    };
}

// lambda 可以多行
auto process = [](int x) {
    int result = x * 2;
    result += 10;
    return result;
};
```

**易错点**：
1. Python lambda 不能有多条语句
2. C++ lambda 默认捕获的是值的副本，修改需要 `mutable`
3. Python 闭包捕获的是变量本身，不是值

```python
# Python 闭包陷阱
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])  # [2, 2, 2] 不是 [0, 1, 2]！

# 修复：默认参数捕获当前值
funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs])  # [0, 1, 2]
```

---

### 7.6 None vs nullptr

| 概念 | Python `None` | C++ `nullptr` |
|------|---------------|---------------|
| **本质** | 单例对象 | 空指针字面量 |
| **类型** | `NoneType` | `std::nullptr_t` |
| **比较方式** | `is None` | `== nullptr` |
| **可调用方法** | ❌ 报错 | ❌ 未定义行为/崩溃 |

```python
# Python: None 是对象
x = None
print(type(x))    # <class 'NoneType'>
print(x is None)  # True（用 is，不用 ==）

# None 调用方法会报错
# x.foo()  # AttributeError
```

```cpp
// C++: nullptr 是空指针
int* p = nullptr;
if (p == nullptr) { /* ... */ }

// nullptr 解引用是未定义行为
// *p = 42;  // 崩溃或更糟
```

**易错点**：Python 用 `is None`，不要用 `== None`。

---

### 7.7 迭代器 (Iterator)

| 概念 | Python | C++ |
|------|--------|-----|
| **协议** | `__iter__` + `__next__` | 5种迭代器类别 |
| **失效问题** | 一般不存在 | 容器修改导致失效 |
| **结束标志** | `StopIteration` 异常 | `it == end()` |

```python
# Python: 简单的迭代器协议
class Counter:
    def __init__(self, max):
        self.max = max
        self.n = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.n >= self.max:
            raise StopIteration
        self.n += 1
        return self.n

for i in Counter(3):
    print(i)  # 1, 2, 3
```

```cpp
// C++: 迭代器类别和失效
std::vector<int> v = {1, 2, 3, 4, 5};

for (auto it = v.begin(); it != v.end(); ) {
    if (*it % 2 == 0) {
        it = v.erase(it);  // 返回新的有效迭代器
    } else {
        ++it;
    }
}

// 错误：迭代器失效
for (auto it = v.begin(); it != v.end(); ++it) {
    if (*it % 2 == 0) {
        v.erase(it);  // 危险！it 已失效
    }
}
```

**易错点**：C++ 迭代器在容器修改后可能失效，Python 一般不存在这个问题。

---

### 7.8 异常处理 (Exception)

| 概念 | Python | C++ |
|------|--------|-----|
| **性能开销** | 较大（异常很慢） | 零开销异常（不抛出时无开销） |
| **常用程度** | 常用于控制流 | 仅用于异常情况 |
| **声明异常** | 不需要 | `noexcept` 优化 |
| **RAII** | 使用 `with` | 析构函数自动清理 |

```python
# Python: 异常常用于控制流（EAFP风格）
def get_value(d, key):
    try:
        return d[key]
    except KeyError:
        return None

# 或者
value = d.get(key)  # 推荐
```

```cpp
// C++: 异常仅用于异常情况（性能考虑）
// HFT 中通常禁用异常
std::optional<int> getValue(const std::map<std::string, int>& m, 
                            const std::string& key) {
    auto it = m.find(key);
    if (it != m.end()) {
        return it->second;
    }
    return std::nullopt;  // 不使用异常
}

// noexcept 优化
void fastFunction() noexcept {
    // 保证不抛异常，编译器可以优化
}
```

**易错点**：Python 开发者可能过度使用异常，在 C++/HFT 中会导致性能问题。

---

### 7.9 const / 不可变

| 概念 | Python | C++ |
|------|--------|-----|
| **常量** | 无真正常量（约定全大写） | `const` 编译时强制 |
| **不可变类型** | `int`, `str`, `tuple` | 无内置不可变类型 |
| **const 方法** | 无 | `const` 成员函数 |

```python
# Python: 没有真正的 const
MAX_SIZE = 100  # 约定常量（全大写）
MAX_SIZE = 200  # 可以修改！只是约定

# 不可变类型
t = (1, 2, 3)
# t[0] = 10  # TypeError

# 但不可变类型内的可变对象可以修改
t = ([1, 2], [3, 4])
t[0].append(5)  # 可以！
print(t)  # ([1, 2, 5], [3, 4])
```

```cpp
// C++: const 是编译时强制的
const int MAX_SIZE = 100;
// MAX_SIZE = 200;  // 编译错误

// const 成员函数
class Point {
    int x, y;
public:
    int getX() const { return x; }  // 不修改对象
    void setX(int val) { x = val; } // 修改对象
};

const Point p{1, 2};
p.getX();   // OK
// p.setX(3);  // 编译错误
```

**易错点**：Python 的 `tuple` 不可变指的是元组本身，不是元素。

---

### 7.10 继承 (Inheritance)

| 概念 | Python | C++ |
|------|--------|-----|
| **多重继承** | MRO (C3 线性化) | 菱形继承问题 |
| **虚继承** | 无需关心 | `virtual` 继承 |
| **调用父类** | `super()` | `Base::method()` |
| **私有继承** | 无 | `private` / `protected` 继承 |

```python
# Python: MRO 自动解决菱形继承
class A:
    def greet(self):
        return "A"

class B(A):
    def greet(self):
        return "B"

class C(A):
    def greet(self):
        return "C"

class D(B, C):
    pass

print(D().greet())  # B
print(D.__mro__)    # D -> B -> C -> A -> object
```

```cpp
// C++: 菱形继承需要虚继承
class A {
public:
    int value = 0;
};

class B : virtual public A {};  // 虚继承
class C : virtual public A {};  // 虚继承

class D : public B, public C {};

D d;
d.value = 42;  // 只有一份 A::value
```

**易错点**：C++ 不用虚继承的菱形继承会导致多份基类副本。

---

### 7.11 完整对照表

| 概念 | Python | C++ |
|------|--------|-----|
| 变量本质 | 引用 | 值 |
| 赋值语义 | 引用绑定 | 值复制 |
| 引用 | 隐式，可重绑定 | 显式，不可重绑定 |
| 私有 | 约定（`_`/`__`） | 强制（`private:`） |
| 多态 | 默认动态分发 | 需要 `virtual` |
| Lambda 捕获 | 自动（引用） | 显式（`[=]`/`[&]`） |
| 迭代器失效 | 一般不存在 | 常见问题 |
| 异常使用 | 控制流 | 仅异常情况 |
| 常量 | 约定（全大写） | 强制（`const`） |
| 多重继承 | MRO 自动解决 | 需虚继承 |
| 内存管理 | 自动（GC） | 手动/智能指针 |
| 类型检查 | 运行时 | 编译时 |

---

### 7.12 类型系统 (Type System)

| 概念 | Python | C++ |
|------|--------|-----|
| **类型检查时机** | 运行时 | 编译时 |
| **类型声明** | 可选（Type Hints） | 必须 |
| **鸭子类型** | ✅ 原生支持 | 模板（编译时鸭子类型） |
| **类型转换** | 隐式/显式 | 隐式/显式/强制 |

```python
# Python: 运行时类型检查，鸭子类型
def process(obj):
    return obj.read()  # 只要有 read() 方法就行

# Type Hints（可选，不强制）
def greet(name: str) -> str:
    return f"Hello, {name}"

greet(42)  # 运行时不报错！Type Hints 只是提示
```

```cpp
// C++: 编译时类型检查
void greet(const std::string& name) {
    std::cout << "Hello, " << name;
}

// greet(42);  // 编译错误！

// 模板：编译时鸭子类型
template<typename T>
auto process(T& obj) {
    return obj.read();  // 编译时检查 T 是否有 read()
}
```

**易错点**：Python Type Hints 不是强制的，mypy 等工具才会检查。

---

### 7.13 资源管理 (with vs RAII)

| 概念 | Python `with` | C++ RAII |
|------|---------------|----------|
| **机制** | 显式使用 `with` | 自动（析构函数） |
| **忘记用** | 资源泄漏 | 不会泄漏 |
| **适用范围** | 代码块内 | 作用域内 |

```python
# Python: 需要显式使用 with
# 正确
with open('file.txt') as f:
    data = f.read()
# f 自动关闭

# 错误（可能忘记关闭）
f = open('file.txt')
data = f.read()
# 忘记 f.close() → 资源泄漏
```

```cpp
// C++: RAII 自动管理
void readFile() {
    std::ifstream f("file.txt");  // 打开
    std::string data;
    f >> data;
}  // 离开作用域，自动关闭

// 智能指针同理
void process() {
    auto ptr = std::make_unique<Resource>();
    ptr->use();
}  // 自动释放，无需 delete
```

**易错点**：Python 必须记住用 `with`，C++ RAII 自动处理。

---

### 7.14 生成器 (Generator)

| 概念 | Python | C++ |
|------|--------|-----|
| **语法** | `yield` | C++20 coroutine |
| **易用性** | 非常简单 | 复杂 |
| **普及度** | 广泛使用 | 较少使用 |

```python
# Python: 生成器非常简单
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

for num in fibonacci(10):
    print(num)

# 生成器表达式
squares = (x*x for x in range(10))
```

```cpp
// C++20: 协程复杂得多
#include <coroutine>
#include <generator>  // C++23

std::generator<int> fibonacci(int n) {
    int a = 0, b = 1;
    for (int i = 0; i < n; ++i) {
        co_yield a;
        auto tmp = a;
        a = b;
        b = tmp + b;
    }
}

// 使用
for (int num : fibonacci(10)) {
    std::cout << num << "\n";
}
```

**易错点**：C++ 协程需要 C++20+，且样板代码多。

---

### 7.15 默认参数 (Default Arguments)

| 概念 | Python | C++ |
|------|--------|-----|
| **求值时机** | 函数定义时（一次） | 每次调用时 |
| **可变默认值** | 危险！共享同一对象 | 安全 |

```python
# Python 经典陷阱：可变默认参数
def append(item, lst=[]):  # lst 在定义时创建一次
    lst.append(item)
    return lst

print(append(1))  # [1]
print(append(2))  # [1, 2] — 不是 [2]！

# 正确做法
def append(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

```cpp
// C++: 默认参数每次调用求值（安全）
std::vector<int> append(int item, std::vector<int> lst = {}) {
    lst.push_back(item);
    return lst;
}

std::cout << append(1).size();  // 1
std::cout << append(2).size();  // 1 — 每次都是新 vector
```

**易错点**：Python 可变默认参数是最常见的 bug 来源之一。

---

### 7.16 字符串 (String)

| 概念 | Python `str` | C++ `std::string` |
|------|--------------|-------------------|
| **可变性** | 不可变 | 可变 |
| **编码** | Unicode (UTF-8/16/32) | 字节序列 |
| **拼接效率** | 低（每次创建新对象） | 高（原地修改） |

```python
# Python: 字符串不可变
s = "hello"
# s[0] = 'H'  # TypeError

s = s.upper()  # 创建新字符串

# 拼接效率问题
result = ""
for i in range(10000):
    result += str(i)  # 每次创建新对象！O(n²)

# 正确做法
result = "".join(str(i) for i in range(10000))  # O(n)
```

```cpp
// C++: 字符串可变
std::string s = "hello";
s[0] = 'H';  // OK

// 拼接效率高
std::string result;
result.reserve(50000);  // 预分配
for (int i = 0; i < 10000; ++i) {
    result += std::to_string(i);  // 原地追加
}
```

**易错点**：Python 字符串拼接用 `+` 效率低，应该用 `join()` 或 f-string。

---

### 7.17 列表/数组 (List vs Vector)

| 概念 | Python `list` | C++ `std::vector` |
|------|---------------|-------------------|
| **元素类型** | 可混合 | 必须同类型 |
| **内存布局** | 指针数组 | 连续内存 |
| **性能** | 较慢 | 快 |
| **切片** | `lst[1:3]` | 无原生支持 |

```python
# Python: 异构列表
lst = [1, "hello", 3.14, [1, 2]]  # 不同类型混合

# 切片（创建新列表）
sub = lst[1:3]  # ['hello', 3.14]

# 列表推导式
squares = [x*x for x in range(10)]
```

```cpp
// C++: 同构 vector
std::vector<int> v = {1, 2, 3, 4};
// std::vector<???> mixed = {1, "hello"};  // 不行

// 无原生切片，需要用迭代器
std::vector<int> sub(v.begin() + 1, v.begin() + 3);

// 范围 for
for (int x : v) { /* ... */ }

// C++20 ranges
auto squares = std::views::iota(0, 10) 
             | std::views::transform([](int x) { return x*x; });
```

**易错点**：Python 切片创建新列表（浅拷贝），不是视图。

---

### 7.18 字典/哈希表 (dict vs unordered_map)

| 概念 | Python `dict` | C++ `std::unordered_map` |
|------|---------------|--------------------------|
| **有序性** | 保持插入顺序 (3.7+) | 无序 |
| **键类型** | 必须可哈希 | 需要 `std::hash` |
| **默认值** | `.get()` / `defaultdict` | `[]` 会插入默认值！ |

```python
# Python: dict 保持插入顺序
d = {'b': 2, 'a': 1}
list(d.keys())  # ['b', 'a']

# 安全获取
val = d.get('c', 0)  # 不存在返回 0

# defaultdict
from collections import defaultdict
dd = defaultdict(list)
dd['key'].append(1)  # 自动创建空列表
```

```cpp
// C++: unordered_map 无序
std::unordered_map<std::string, int> m = {{"b", 2}, {"a", 1}};
// 遍历顺序不确定

// 危险：[] 会插入默认值！
int val = m["c"];  // 不存在？插入 {"c": 0}！

// 安全获取
auto it = m.find("c");
if (it != m.end()) {
    val = it->second;
}

// C++17
if (auto it = m.find("c"); it != m.end()) {
    val = it->second;
}
```

**易错点**：C++ `map["key"]` 会自动插入，检查存在性要用 `find()` 或 `count()`。

---

### 7.19 函数重载 (Function Overloading)

| 概念 | Python | C++ |
|------|--------|-----|
| **支持** | ❌ 不支持 | ✅ 支持 |
| **替代方案** | 默认参数/可变参数 | - |
| **运算符重载** | 魔术方法 | `operator` 关键字 |

```python
# Python: 不支持函数重载
def add(a, b):
    return a + b

def add(a, b, c):  # 覆盖上面的定义！
    return a + b + c

add(1, 2)  # TypeError: missing argument 'c'

# 替代方案
def add(*args):
    return sum(args)

# 或使用 singledispatch
from functools import singledispatch

@singledispatch
def process(arg):
    raise NotImplementedError

@process.register(int)
def _(arg):
    return arg * 2

@process.register(str)
def _(arg):
    return arg.upper()
```

```cpp
// C++: 支持函数重载
int add(int a, int b) { return a + b; }
int add(int a, int b, int c) { return a + b + c; }
double add(double a, double b) { return a + b; }

add(1, 2);      // 调用第一个
add(1, 2, 3);   // 调用第二个
add(1.0, 2.0);  // 调用第三个
```

**易错点**：Python 后定义的函数会覆盖前面的同名函数。

---

### 7.20 作用域 (Scope)

| 概念 | Python | C++ |
|------|--------|-----|
| **变量声明** | 赋值即声明 | 需要类型声明 |
| **块作用域** | ❌ 只有函数/类/模块 | ✅ `{}` 创建作用域 |
| **捕获外部变量** | 需要 `nonlocal`/`global` | 自动可见 |

```python
# Python: 没有块作用域
if True:
    x = 10
print(x)  # 10 — x 在 if 外仍可见！

for i in range(5):
    pass
print(i)  # 4 — i 在循环外仍可见！

# 修改外部变量需要声明
def outer():
    x = 10
    def inner():
        nonlocal x  # 需要声明
        x = 20
    inner()
    print(x)  # 20
```

```cpp
// C++: 块作用域
if (true) {
    int x = 10;
}
// std::cout << x;  // 编译错误：x 不可见

for (int i = 0; i < 5; ++i) {
    // ...
}
// std::cout << i;  // 编译错误：i 不可见

// 可以直接访问外部变量
void outer() {
    int x = 10;
    auto inner = [&x]() {
        x = 20;  // 直接修改
    };
    inner();
    std::cout << x;  // 20
}
```

**易错点**：Python 循环变量在循环外仍然可见，C++ 不会。

---

## 八、延伸阅读

- [C++核心概念索引](/articles/00-glossary/glossary-05-cpp-concepts/)
- [Rust核心概念索引](/articles/00-glossary/glossary-07-rust-concepts/)
- [Python高难度面试问题](/articles/python/py-21-高难度面试问题/)
- [Python量化面试题](/articles/python/py-55-Python量化面试题/)
- [Python双下划线变量详解](/articles/python/py-57-Python双下划线变量详解/)
