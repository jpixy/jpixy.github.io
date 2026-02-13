+++
title = "50. Python内存优化详解"
slug = "py-51-Python内存优化详解"
date = 2026-01-21
weight = 50000
description = "深入剖析Python的内存优化技术，包括__slots__、memoryview、array模块、内存分析工具和对象大小"
[taxonomies]
tags = ["Python", "内存优化", "性能", "__slots__", "memoryview"]
+++

## 概述

Python的动态特性带来便利的同时也带来内存开销。在HFT等内存敏感场景中，优化内存使用至关重要。

---

## 一、对象内存分析

### 1.1 查看对象大小

```python
import sys

# 基本类型大小
print(f"int: {sys.getsizeof(0)} bytes")        # 28
print(f"int(100): {sys.getsizeof(100)} bytes")  # 28
print(f"int(10**100): {sys.getsizeof(10**100)} bytes")  # 72

print(f"float: {sys.getsizeof(0.0)} bytes")     # 24
print(f"str(''): {sys.getsizeof('')} bytes")    # 49
print(f"str('hello'): {sys.getsizeof('hello')} bytes")  # 54

print(f"list[]: {sys.getsizeof([])} bytes")     # 56
print(f"dict{{}}: {sys.getsizeof({})} bytes")   # 64
print(f"set(): {sys.getsizeof(set())} bytes")   # 216

# 注意：sys.getsizeof不递归计算
lst = [[1, 2, 3], [4, 5, 6]]
print(f"嵌套list浅层: {sys.getsizeof(lst)} bytes")  # 不包含内部列表
```

### 1.2 递归计算大小

```python
import sys
from collections.abc import Mapping, Iterable

def deep_getsizeof(obj, seen=None):
    """递归计算对象总大小"""
    if seen is None:
        seen = set()
    
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    
    size = sys.getsizeof(obj)
    
    if isinstance(obj, str):
        pass
    elif isinstance(obj, Mapping):
        size += sum(deep_getsizeof(k, seen) + deep_getsizeof(v, seen) 
                    for k, v in obj.items())
    elif isinstance(obj, Iterable):
        size += sum(deep_getsizeof(i, seen) for i in obj)
    elif hasattr(obj, '__dict__'):
        size += deep_getsizeof(obj.__dict__, seen)
    elif hasattr(obj, '__slots__'):
        size += sum(deep_getsizeof(getattr(obj, slot), seen) 
                    for slot in obj.__slots__ if hasattr(obj, slot))
    
    return size

# 使用
data = {'a': [1, 2, 3], 'b': {'nested': 'dict'}}
print(f"Deep size: {deep_getsizeof(data)} bytes")
```

### 1.3 使用pympler

```python
from pympler import asizeof, tracker

# 更准确的大小计算
data = {'a': [1, 2, 3], 'b': [4, 5, 6]}
print(f"asizeof: {asizeof.asizeof(data)} bytes")

# 追踪内存变化
tr = tracker.SummaryTracker()

# ... 执行一些操作 ...
large_list = [i for i in range(100000)]

tr.print_diff()  # 显示内存变化
```

---

## 二、__slots__优化

### 2.1 基本使用

```python
import sys

# 普通类：每个实例有__dict__
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# slots类：固定属性，无__dict__
class SlotPoint:
    __slots__ = ('x', 'y')
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

# 比较内存
p1 = Point(1, 2)
p2 = SlotPoint(1, 2)

print(f"Point: {sys.getsizeof(p1)} + {sys.getsizeof(p1.__dict__)} bytes")
print(f"SlotPoint: {sys.getsizeof(p2)} bytes")

# 典型结果：
# Point: 48 + 104 = 152 bytes
# SlotPoint: 48 bytes
```

### 2.2 继承中的slots

```python
class Base:
    __slots__ = ('x',)
    
    def __init__(self, x):
        self.x = x

class Derived(Base):
    __slots__ = ('y',)  # 只需声明新增属性
    
    def __init__(self, x, y):
        super().__init__(x)
        self.y = y

# 如果需要__dict__
class FlexibleDerived(Base):
    __slots__ = ('y', '__dict__')  # 显式添加__dict__
```

### 2.3 slots注意事项

```python
class SlotClass:
    __slots__ = ('value', '__weakref__')  # 支持弱引用
    
    def __init__(self, value):
        self.value = value

# 限制：
# 1. 不能动态添加属性
obj = SlotClass(10)
# obj.new_attr = 20  # AttributeError

# 2. 不能有默认值（Python 3.6前）
# class Bad:
#     __slots__ = ('x',)
#     x = 10  # 错误

# 3. 多重继承复杂
# 如果父类都有非空__slots__，需要小心处理
```

### 2.4 HFT应用：大量对象

```python
import sys
from dataclasses import dataclass

# 场景：存储100万个订单

# 方案1：普通dataclass
@dataclass
class Order:
    order_id: int
    price: float
    quantity: int
    side: str

# 方案2：slots
class SlotOrder:
    __slots__ = ('order_id', 'price', 'quantity', 'side')
    
    def __init__(self, order_id, price, quantity, side):
        self.order_id = order_id
        self.price = price
        self.quantity = quantity
        self.side = side

# 内存对比
n = 1000000
orders1 = [Order(i, 100.0, 100, 'BUY') for i in range(n)]
orders2 = [SlotOrder(i, 100.0, 100, 'BUY') for i in range(n)]

from pympler import asizeof
print(f"普通类: {asizeof.asizeof(orders1) / 1e6:.1f} MB")
print(f"slots类: {asizeof.asizeof(orders2) / 1e6:.1f} MB")

# 典型结果：
# 普通类: ~400 MB
# slots类: ~150 MB
```

---

## 三、memoryview

### 3.1 零拷贝访问

```python
# 创建bytes
data = b'Hello, World!'

# 普通切片会创建拷贝
slice1 = data[0:5]  # 新的bytes对象

# memoryview零拷贝
view = memoryview(data)
slice2 = view[0:5]  # 视图，不拷贝

# 修改可变buffer
arr = bytearray(b'Hello, World!')
view = memoryview(arr)
view[0:5] = b'HELLO'
print(arr)  # bytearray(b'HELLO, World!')
```

### 3.2 结构化访问

```python
import struct

# 二进制数据
data = struct.pack('3i', 1, 2, 3)  # 3个int

# 使用memoryview按不同类型访问
view = memoryview(data)
int_view = view.cast('i')  # 作为int数组

print(list(int_view))  # [1, 2, 3]

# 修改
arr = bytearray(12)
view = memoryview(arr).cast('i')
view[0] = 100
view[1] = 200
view[2] = 300
print(list(view))  # [100, 200, 300]
```

### 3.3 与NumPy集成

```python
import numpy as np

# NumPy数组到memoryview
arr = np.array([1, 2, 3, 4, 5], dtype=np.int32)
view = memoryview(arr)

print(view.format)  # 'i'
print(view.itemsize)  # 4
print(view.shape)  # (5,)

# 修改会反映到原数组
view[0] = 100
print(arr)  # [100, 2, 3, 4, 5]

# memoryview到NumPy
data = bytearray(20)
view = memoryview(data).cast('i')
np_arr = np.asarray(view)
```

---

## 四、array模块

### 4.1 基本使用

```python
import array
import sys

# 创建类型化数组
int_arr = array.array('i', [1, 2, 3, 4, 5])  # 'i' = signed int
float_arr = array.array('d', [1.0, 2.0, 3.0])  # 'd' = double

# 类型码
# 'b' = signed char (1 byte)
# 'h' = signed short (2 bytes)
# 'i' = signed int (4 bytes)
# 'l' = signed long (4/8 bytes)
# 'q' = signed long long (8 bytes)
# 'f' = float (4 bytes)
# 'd' = double (8 bytes)

# 内存对比
list_int = [1, 2, 3, 4, 5]
arr_int = array.array('i', [1, 2, 3, 4, 5])

print(f"list: {sys.getsizeof(list_int) + sum(sys.getsizeof(x) for x in list_int)} bytes")
print(f"array: {sys.getsizeof(arr_int)} bytes")
```

### 4.2 性能对比

```python
import array
import time

n = 1000000

# list of ints
start = time.time()
lst = [0] * n
for i in range(n):
    lst[i] = i
print(f"list: {time.time() - start:.3f}s")

# array
start = time.time()
arr = array.array('i', [0] * n)
for i in range(n):
    arr[i] = i
print(f"array: {time.time() - start:.3f}s")

# 内存
import sys
print(f"list memory: {sys.getsizeof(lst) / 1e6:.1f} MB (不含元素)")
print(f"array memory: {sys.getsizeof(arr) / 1e6:.1f} MB")
```

---

## 五、内存分析工具

### 5.1 memory_profiler

```python
# 安装：pip install memory_profiler

from memory_profiler import profile

@profile
def memory_heavy():
    a = [i for i in range(1000000)]
    b = [i * 2 for i in range(1000000)]
    del a
    return b

if __name__ == '__main__':
    result = memory_heavy()
```

```bash
# 运行
python -m memory_profiler script.py

# 输出示例：
# Line #    Mem usage    Increment   Line Contents
# ================================================
#      3     38.5 MiB     38.5 MiB   @profile
#      4                             def memory_heavy():
#      5     77.0 MiB     38.5 MiB       a = [i for i in range(1000000)]
#      6    115.4 MiB     38.4 MiB       b = [i * 2 for i in range(1000000)]
#      7     77.0 MiB    -38.4 MiB       del a
#      8     77.0 MiB      0.0 MiB       return b
```

### 5.2 tracemalloc

```python
import tracemalloc

# 开始追踪
tracemalloc.start()

# 执行代码
data = [i for i in range(100000)]
more_data = {i: str(i) for i in range(10000)}

# 获取快照
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 10 内存分配:")
for stat in top_stats[:10]:
    print(stat)

# 比较两个快照
snapshot1 = tracemalloc.take_snapshot()
# ... 更多操作 ...
snapshot2 = tracemalloc.take_snapshot()

top_stats = snapshot2.compare_to(snapshot1, 'lineno')
print("\n内存变化:")
for stat in top_stats[:5]:
    print(stat)
```

### 5.3 objgraph

```python
import objgraph

# 查看最常见的类型
objgraph.show_most_common_types()

# 查看增长的对象
objgraph.show_growth()

# 执行操作
data = [object() for _ in range(1000)]

# 再次查看增长
objgraph.show_growth()

# 查找特定类型
objgraph.show_refs(data, filename='refs.png')
```

---

## 六、优化技巧

### 6.1 使用生成器

```python
import sys

# 列表：一次性加载所有数据
def get_data_list(n):
    return [i * 2 for i in range(n)]

# 生成器：按需生成
def get_data_gen(n):
    for i in range(n):
        yield i * 2

n = 1000000
lst = get_data_list(n)
gen = get_data_gen(n)

print(f"List size: {sys.getsizeof(lst)} bytes")
print(f"Generator size: {sys.getsizeof(gen)} bytes")
```

### 6.2 字符串intern

```python
import sys

# 相同字符串共享内存
a = 'hello'
b = 'hello'
print(a is b)  # True

# 显式intern
s1 = 'hello world'
s2 = 'hello world'
print(s1 is s2)  # 可能False

s1 = sys.intern('hello world')
s2 = sys.intern('hello world')
print(s1 is s2)  # True

# 适用于大量重复字符串
symbols = [sys.intern('AAPL') for _ in range(10000)]
```

### 6.3 使用__slots__的dataclass

```python
from dataclasses import dataclass

@dataclass
class RegularOrder:
    order_id: int
    price: float
    quantity: int

# Python 3.10+
@dataclass(slots=True)
class SlotOrder:
    order_id: int
    price: float
    quantity: int

# 或手动
@dataclass
class ManualSlotOrder:
    __slots__ = ('order_id', 'price', 'quantity')
    order_id: int
    price: float
    quantity: int
```

---

## 总结

| 技术 | 内存节省 | 适用场景 |
|------|----------|----------|
| __slots__ | 40-60% | 大量对象 |
| array | 60-80% | 数值数组 |
| memoryview | 避免拷贝 | 二进制处理 |
| 生成器 | 接近100% | 迭代处理 |
| intern | 重复字符串 | 符号/标识符 |

**最佳实践**：
1. 大量对象使用__slots__
2. 数值数据使用NumPy或array
3. 二进制处理使用memoryview
4. 使用tracemalloc定位内存问题
5. 考虑使用生成器减少峰值内存

---

## 相关文章

- [上一篇：Python性能优化-多进程与GIL](@/articles/python/py-49-Python性能优化-多进程与GIL.md)
- [下一篇：NumPy高性能编程](@/articles/python/py-51-NumPy高性能编程.md)
