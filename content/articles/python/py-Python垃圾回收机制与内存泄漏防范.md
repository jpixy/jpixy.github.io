+++
title = "创建循环引用"
slug = "py-Python垃圾回收机制与内存泄漏防范"
+++

# 创建循环引用

### **Python 的垃圾回收机制与内存泄漏防范**
---

#### **1. Python 的垃圾回收（Garbage Collection, GC）核心机制**
Python 通过 **引用计数（Reference Counting）** 为主，**分代回收（Generational GC）** 为辅的机制管理内存。

##### **（1）引用计数（Reference Counting）**
+ **原理**：每个对象维护一个引用计数器，记录被引用的次数。

```python
import sys

a = []  # 对象引用计数=1
b = a   # 引用计数+1 → 变为2
print(sys.getrefcount(a))  # 输出3（临时引用+1）
```

+ **触发回收**：当引用计数归零时，立即释放内存。
+ **优点**：实时性高，无停顿。
+ **缺点**：无法处理循环引用。

##### **（2）分代回收（Generational GC）**
+ **分代策略**：
    - **第0代**：新创建的对象。
    - **第1代**：经历过一次GC后存活的对象。
    - **第2代**：经历过多次GC仍存活的对象。
+ **触发条件**：
    - 当分配的对象数量减去释放的数量超过阈值时。
    - 手动调用 `gc.collect()`。
+ **算法**：标记-清除（Mark-and-Sweep）解决循环引用。

##### **（3）标记-清除（Mark-and-Sweep）**
1. **标记阶段**：从根对象（全局变量、栈变量等）出发，标记所有可达对象。
2. **清除阶段**：回收未被标记的对象（即不可达的循环引用）。

---

#### **2. 避免内存泄漏的实践方法**
##### **（1）识别循环引用**
```python
import gc

class Node:
    def __init__(self):
        self.parent = None

# 创建循环引用
a = Node()
b = Node()
a.parent = b
b.parent = a

# 手动触发GC
gc.collect()  # 会回收a和b
```

##### **（2）弱引用（WeakRef）**
```python
import weakref

class Data:
    pass

d = Data()
w = weakref.ref(d)  # 弱引用不计入引用计数
print(w())  # 输出<__main__.Data object>
del d
print(w())  # 输出None（对象已回收）
```

##### **（3）上下文管理器（**`with`**语句）**
```python
with open('file.txt') as f:
    data = f.read()
# 文件句柄自动关闭，避免资源泄漏
```

##### **（4）监控工具**
+ `tracemalloc`：

```python
import tracemalloc

tracemalloc.start()
x = [1] * 1000000
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics('lineno')[:3]:
    print(stat)
```

---

#### **3. 主流垃圾回收算法对比**
| **算法** | **原理** | **优点** | **缺点** | **应用场景** |
| --- | --- | --- | --- | --- |
| **引用计数** | 对象被引用时计数+1，归零时回收 | 实时性高，无停顿 | 无法处理循环引用 | Python、Swift |
| **标记-清除** | 从根对象出发标记可达对象，清除未标记对象 | 可处理循环引用 | 需要暂停程序（Stop-The-World） | Python、Go |
| **分代回收** | 按对象存活时间分代，年轻代更频繁回收 | 减少全局扫描开销 | 实现复杂 | Python、Java |
| **复制算法** | 将内存分为两块，存活对象复制到另一块 | 无碎片，高效 | 内存利用率50% | Java新生代 |
| **增量回收** | 将GC过程分解为多个小步骤执行 | 减少停顿时间 | 吞吐量降低 | 实时系统 |


---

#### **4. Python 内存管理最佳实践**
1. **避免全局变量**：长时间持有对象引用。
2. **及时释放资源**：对文件、网络连接等使用 `with` 语句。
3. **谨慎使用 **`__del__`：析构函数可能干扰GC。
4. **监控内存使用**：

```python
import objgraph

objgraph.show_most_common_types(limit=10)  # 显示前10类对象
```

5. **禁用GC的极端优化**（仅特定场景）：

```python
import gc
gc.disable()  # 高实时性场景使用
```

---

### **总结**
+ **Python 以引用计数为主**，辅以分代回收解决循环引用。
+ **内存泄漏主因**：循环引用、全局变量、未释放资源。
+ **诊断工具**：`gc`、`tracemalloc`、`objgraph`。
+ **优化方向**：减少对象创建、使用弱引用、合理分代。
