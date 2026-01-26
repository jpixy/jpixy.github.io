+++
title = "49.Python性能优化-Numba详解"
date = 2026-01-21
description = "深入剖析Numba的使用方法，包括JIT编译、nopython模式、CUDA支持、向量化和性能对比"
[taxonomies]
tags = ["Python", "Numba", "JIT", "性能优化", "CUDA"]
+++

## 概述

Numba是一个JIT编译器，可以将Python/NumPy代码编译为机器码，无需修改代码结构即可获得巨大性能提升。

---

## 一、Numba基础

### 1.1 安装和基本使用

```bash
pip install numba
```

```python
from numba import jit
import numpy as np

# 最简单的使用方式
@jit
def add(a, b):
    return a + b

# 强制nopython模式（推荐）
@jit(nopython=True)
def fast_add(a, b):
    return a + b

# 等价的简写
from numba import njit

@njit
def faster_add(a, b):
    return a + b
```

### 1.2 nopython vs object模式

```python
from numba import jit, njit

# object模式：回退到Python对象，性能较差
@jit
def object_mode_func(x):
    return str(x)  # 无法在nopython模式编译

# nopython模式：完全编译为机器码
@njit
def nopython_func(x):
    return x * 2

# 显式禁止回退
@jit(nopython=True)
def strict_func(x):
    # 如果有不支持的操作会报错而非回退
    return x * 2
```

### 1.3 类型签名

```python
from numba import njit, int64, float64

# 显式指定类型签名
@njit(float64(float64, float64))
def typed_add(a, b):
    return a + b

# 多个签名
@njit([
    float64(float64, float64),
    int64(int64, int64),
])
def multi_typed_add(a, b):
    return a + b

# 数组类型
from numba import float64
@njit(float64[:](float64[:], float64[:]))
def add_arrays(a, b):
    return a + b
```

---

## 二、循环优化

### 2.1 基本循环

```python
import numpy as np
from numba import njit

# 纯Python版本
def python_sum(arr):
    total = 0.0
    for i in range(len(arr)):
        total += arr[i]
    return total

# Numba优化版本
@njit
def numba_sum(arr):
    total = 0.0
    for i in range(len(arr)):
        total += arr[i]
    return total

# 性能对比
arr = np.random.random(1000000)

# Python: ~100ms
# Numba: ~2ms (50x faster)
```

### 2.2 嵌套循环

```python
@njit
def matrix_multiply(A, B):
    m, k = A.shape
    k2, n = B.shape
    assert k == k2
    
    C = np.zeros((m, n))
    for i in range(m):
        for j in range(n):
            for l in range(k):
                C[i, j] += A[i, l] * B[l, j]
    return C

# 典型加速：100-1000x
```

### 2.3 并行循环

```python
from numba import njit, prange

@njit(parallel=True)
def parallel_sum(arr):
    total = 0.0
    for i in prange(len(arr)):  # prange启用并行
        total += arr[i]
    return total

@njit(parallel=True)
def parallel_matrix_op(A, B):
    m, n = A.shape
    C = np.empty_like(A)
    
    for i in prange(m):  # 外层循环并行
        for j in range(n):
            C[i, j] = A[i, j] * B[i, j] + A[i, j]
    return C
```

---

## 三、向量化

### 3.1 @vectorize

```python
from numba import vectorize, float64

# 创建numpy ufunc
@vectorize([float64(float64, float64)])
def fast_add(a, b):
    return a + b

# 使用
arr1 = np.array([1.0, 2.0, 3.0])
arr2 = np.array([4.0, 5.0, 6.0])
result = fast_add(arr1, arr2)  # [5.0, 7.0, 9.0]

# 复杂运算
@vectorize([float64(float64)])
def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))
```

### 3.2 @guvectorize

```python
from numba import guvectorize, float64

# 广义向量化：支持任意维度
@guvectorize([(float64[:], float64[:], float64[:])], '(n),(n)->(n)')
def add_vectors(a, b, result):
    for i in range(a.shape[0]):
        result[i] = a[i] + b[i]

# 矩阵行求和
@guvectorize([(float64[:, :], float64[:])], '(m,n)->(m)')
def row_sum(arr, result):
    m, n = arr.shape
    for i in range(m):
        total = 0.0
        for j in range(n):
            total += arr[i, j]
        result[i] = total
```

---

## 四、CUDA支持

### 4.1 基本CUDA核函数

```python
from numba import cuda
import numpy as np

# CUDA核函数
@cuda.jit
def add_kernel(a, b, result):
    i = cuda.grid(1)  # 获取全局线程索引
    if i < result.size:
        result[i] = a[i] + b[i]

# 使用
n = 1000000
a = np.random.random(n).astype(np.float32)
b = np.random.random(n).astype(np.float32)
result = np.zeros(n, dtype=np.float32)

# 传输到GPU
d_a = cuda.to_device(a)
d_b = cuda.to_device(b)
d_result = cuda.to_device(result)

# 配置和启动
threads_per_block = 256
blocks_per_grid = (n + threads_per_block - 1) // threads_per_block
add_kernel[blocks_per_grid, threads_per_block](d_a, d_b, d_result)

# 取回结果
result = d_result.copy_to_host()
```

### 4.2 共享内存

```python
from numba import cuda, float32

@cuda.jit
def matmul_shared(A, B, C):
    """使用共享内存的矩阵乘法"""
    TPB = 16  # 每块线程数
    
    # 共享内存
    sA = cuda.shared.array(shape=(TPB, TPB), dtype=float32)
    sB = cuda.shared.array(shape=(TPB, TPB), dtype=float32)
    
    x, y = cuda.grid(2)
    tx, ty = cuda.threadIdx.x, cuda.threadIdx.y
    
    if x >= C.shape[0] or y >= C.shape[1]:
        return
    
    tmp = 0.0
    for i in range(A.shape[1] // TPB):
        # 加载到共享内存
        sA[tx, ty] = A[x, i * TPB + ty]
        sB[tx, ty] = B[i * TPB + tx, y]
        cuda.syncthreads()
        
        # 计算
        for j in range(TPB):
            tmp += sA[tx, j] * sB[j, ty]
        cuda.syncthreads()
    
    C[x, y] = tmp
```

### 4.3 设备函数

```python
from numba import cuda

# 设备函数（在GPU上调用）
@cuda.jit(device=True)
def device_add(a, b):
    return a + b

@cuda.jit(device=True)
def device_square(x):
    return x * x

# 在核函数中使用
@cuda.jit
def compute_kernel(arr, result):
    i = cuda.grid(1)
    if i < arr.size:
        temp = device_add(arr[i], 1.0)
        result[i] = device_square(temp)
```

---

## 五、高级特性

### 5.1 缓存编译

```python
# 缓存编译结果，避免重复编译
@njit(cache=True)
def cached_func(x):
    return x * 2

# 第一次调用会编译
# 后续调用使用缓存
```

### 5.2 提前编译（AOT）

```python
from numba.pycc import CC

cc = CC('my_module')
cc.verbose = True

@cc.export('add', 'f8(f8, f8)')
def add(a, b):
    return a + b

@cc.export('sum_array', 'f8(f8[:])')
def sum_array(arr):
    total = 0.0
    for i in range(len(arr)):
        total += arr[i]
    return total

if __name__ == '__main__':
    cc.compile()

# 生成的模块可以直接import使用
# import my_module
# my_module.add(1.0, 2.0)
```

### 5.3 JIT类

```python
from numba import jitclass
from numba import int64, float64

spec = [
    ('value', float64),
    ('count', int64),
]

@jitclass(spec)
class Accumulator:
    def __init__(self):
        self.value = 0.0
        self.count = 0
    
    def add(self, x):
        self.value += x
        self.count += 1
    
    def mean(self):
        if self.count == 0:
            return 0.0
        return self.value / self.count

# 使用
acc = Accumulator()
for i in range(1000):
    acc.add(float(i))
print(acc.mean())
```

---

## 六、HFT应用

### 6.1 快速移动平均

```python
@njit
def ema(prices, alpha):
    """指数移动平均"""
    n = len(prices)
    result = np.empty(n)
    result[0] = prices[0]
    
    for i in range(1, n):
        result[i] = alpha * prices[i] + (1 - alpha) * result[i-1]
    
    return result

@njit(parallel=True)
def batch_ema(all_prices, alpha):
    """批量计算多个序列的EMA"""
    n_series, n_points = all_prices.shape
    result = np.empty_like(all_prices)
    
    for s in prange(n_series):
        result[s, 0] = all_prices[s, 0]
        for i in range(1, n_points):
            result[s, i] = alpha * all_prices[s, i] + (1 - alpha) * result[s, i-1]
    
    return result
```

### 6.2 快速排序和搜索

```python
@njit
def binary_search(arr, target):
    """二分搜索"""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

@njit
def find_price_level(prices, target_price):
    """在排序的价格数组中查找价格级别"""
    n = len(prices)
    if n == 0:
        return -1
    
    left, right = 0, n - 1
    while left < right:
        mid = (left + right) // 2
        if prices[mid] < target_price:
            left = mid + 1
        else:
            right = mid
    
    if prices[left] == target_price:
        return left
    return -1
```

### 6.3 统计计算

```python
@njit
def rolling_stats(arr, window):
    """滚动统计：均值和标准差"""
    n = len(arr)
    means = np.empty(n - window + 1)
    stds = np.empty(n - window + 1)
    
    for i in range(n - window + 1):
        window_data = arr[i:i + window]
        means[i] = np.mean(window_data)
        stds[i] = np.std(window_data)
    
    return means, stds

@njit
def rolling_correlation(x, y, window):
    """滚动相关系数"""
    n = len(x)
    result = np.empty(n - window + 1)
    
    for i in range(n - window + 1):
        x_win = x[i:i + window]
        y_win = y[i:i + window]
        
        x_mean = np.mean(x_win)
        y_mean = np.mean(y_win)
        
        cov = 0.0
        x_var = 0.0
        y_var = 0.0
        
        for j in range(window):
            dx = x_win[j] - x_mean
            dy = y_win[j] - y_mean
            cov += dx * dy
            x_var += dx * dx
            y_var += dy * dy
        
        if x_var > 0 and y_var > 0:
            result[i] = cov / np.sqrt(x_var * y_var)
        else:
            result[i] = 0.0
    
    return result
```

---

## 七、调试和优化

### 7.1 检查编译类型

```python
from numba import njit

@njit
def my_func(x):
    return x * 2

# 查看编译后的类型
my_func(1.0)  # 触发编译
print(my_func.signatures)  # 查看签名
print(my_func.inspect_types())  # 详细类型信息
```

### 7.2 性能分析

```python
import timeit

def benchmark():
    arr = np.random.random(1000000)
    
    # 预热
    numba_func(arr)
    
    # 测量
    python_time = timeit.timeit(lambda: python_func(arr), number=10)
    numba_time = timeit.timeit(lambda: numba_func(arr), number=10)
    numpy_time = timeit.timeit(lambda: np.sum(arr), number=10)
    
    print(f"Python: {python_time:.4f}s")
    print(f"Numba:  {numba_time:.4f}s")
    print(f"NumPy:  {numpy_time:.4f}s")
```

---

## 总结

| 特性 | 加速比 | 适用场景 |
|------|--------|----------|
| @njit | 10-100x | 数值循环 |
| @njit(parallel=True) | 额外Nx | 可并行循环 |
| @vectorize | 10-50x | 元素级操作 |
| CUDA | 100-1000x | GPU计算 |

**最佳实践**：
1. 始终使用nopython模式
2. 循环内使用NumPy数组，非Python列表
3. 避免在JIT函数中创建Python对象
4. 使用cache=True减少启动时间
5. 用prange实现并行化
