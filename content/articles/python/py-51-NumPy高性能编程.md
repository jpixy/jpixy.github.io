+++
title = "51.NumPy高性能编程"
slug = "py-52-NumPy高性能编程"
date = 2026-01-21
description = "深入剖析NumPy的高性能编程技术，包括向量化、广播、内存布局、ufunc、NumPy C API和numexpr"
[taxonomies]
tags = ["Python", "NumPy", "性能优化", "向量化", "量化"]
+++

## 概述

NumPy是Python科学计算的基础，其性能直接影响量化系统的效率。本文深入讲解NumPy高性能编程技巧。

---

## 一、向量化操作

### 1.1 避免Python循环

```python
import numpy as np
import time

n = 1000000
a = np.random.random(n)
b = np.random.random(n)

# 慢：Python循环
def slow_add(a, b):
    result = np.empty(len(a))
    for i in range(len(a)):
        result[i] = a[i] + b[i]
    return result

# 快：向量化
def fast_add(a, b):
    return a + b

# 性能对比
start = time.time()
slow_add(a, b)
print(f"Python loop: {time.time() - start:.4f}s")

start = time.time()
fast_add(a, b)
print(f"Vectorized: {time.time() - start:.4f}s")

# 典型加速：50-100x
```

### 1.2 向量化条件操作

```python
# 慢
def slow_clip(arr, min_val, max_val):
    result = np.empty_like(arr)
    for i in range(len(arr)):
        if arr[i] < min_val:
            result[i] = min_val
        elif arr[i] > max_val:
            result[i] = max_val
        else:
            result[i] = arr[i]
    return result

# 快：使用np.clip
result = np.clip(arr, min_val, max_val)

# 或使用np.where
result = np.where(arr < min_val, min_val, 
                  np.where(arr > max_val, max_val, arr))

# 布尔索引
arr[arr < 0] = 0  # 将负数替换为0
```

### 1.3 向量化数学运算

```python
# 组合运算
def calculate_returns(prices):
    # 慢
    # returns = []
    # for i in range(1, len(prices)):
    #     returns.append((prices[i] - prices[i-1]) / prices[i-1])
    
    # 快
    return np.diff(prices) / prices[:-1]

# 移动平均
def moving_average(arr, window):
    # 使用cumsum实现
    cumsum = np.cumsum(arr)
    cumsum[window:] = cumsum[window:] - cumsum[:-window]
    return cumsum[window - 1:] / window

# 指数移动平均
def ema(arr, alpha):
    result = np.empty_like(arr)
    result[0] = arr[0]
    for i in range(1, len(arr)):
        result[i] = alpha * arr[i] + (1 - alpha) * result[i-1]
    return result
```

---

## 二、广播机制

### 2.1 广播规则

```python
# 规则：从右向左对齐，维度为1可以广播

# 示例1：标量 + 数组
a = np.array([1, 2, 3])
b = 2
c = a + b  # [3, 4, 5]

# 示例2：行向量 + 列向量 = 矩阵
row = np.array([1, 2, 3])      # shape (3,)
col = np.array([[1], [2]])      # shape (2, 1)
result = row + col
# [[2, 3, 4],
#  [3, 4, 5]]

# 示例3：3D广播
a = np.ones((3, 4, 5))
b = np.ones((4, 5))
c = a + b  # shape (3, 4, 5)
```

### 2.2 高效利用广播

```python
# 计算欧几里得距离矩阵
def pairwise_distances(X, Y):
    """计算X中每个点到Y中每个点的距离"""
    # X: (m, d), Y: (n, d)
    # 结果: (m, n)
    
    # 利用广播
    # ||x - y||^2 = ||x||^2 + ||y||^2 - 2*x·y
    X_sq = np.sum(X**2, axis=1, keepdims=True)  # (m, 1)
    Y_sq = np.sum(Y**2, axis=1)                  # (n,)
    XY = np.dot(X, Y.T)                          # (m, n)
    
    return np.sqrt(X_sq + Y_sq - 2 * XY)

# 标准化：按列减均值除标准差
def standardize(X):
    mean = X.mean(axis=0)  # (d,)
    std = X.std(axis=0)    # (d,)
    return (X - mean) / std  # 广播

# 外积
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
outer = a[:, np.newaxis] * b  # [[4,5,6], [8,10,12], [12,15,18]]
```

---

## 三、内存布局

### 3.1 C顺序 vs Fortran顺序

```python
# C顺序（行优先）：默认
c_arr = np.array([[1, 2, 3], [4, 5, 6]], order='C')
print(c_arr.flags['C_CONTIGUOUS'])  # True

# Fortran顺序（列优先）
f_arr = np.array([[1, 2, 3], [4, 5, 6]], order='F')
print(f_arr.flags['F_CONTIGUOUS'])  # True

# 性能影响
import time

n = 1000
arr_c = np.random.random((n, n))
arr_f = np.asfortranarray(arr_c)

# 行遍历 - C顺序快
start = time.time()
for _ in range(100):
    _ = arr_c.sum(axis=1)
print(f"C-order row sum: {time.time() - start:.4f}s")

start = time.time()
for _ in range(100):
    _ = arr_f.sum(axis=1)
print(f"F-order row sum: {time.time() - start:.4f}s")
```

### 3.2 连续性检查

```python
arr = np.random.random((100, 100))

# 切片可能破坏连续性
slice1 = arr[::2, :]  # 步长2，不连续
print(slice1.flags['C_CONTIGUOUS'])  # False

# 转置改变顺序
transposed = arr.T
print(transposed.flags['C_CONTIGUOUS'])  # False
print(transposed.flags['F_CONTIGUOUS'])  # True

# 使用np.ascontiguousarray恢复
contiguous = np.ascontiguousarray(slice1)
print(contiguous.flags['C_CONTIGUOUS'])  # True
```

### 3.3 数据类型优化

```python
# 选择合适的dtype
# float64 (8 bytes) vs float32 (4 bytes)
arr64 = np.random.random(1000000)  # float64
arr32 = arr64.astype(np.float32)

print(f"float64: {arr64.nbytes / 1e6:.1f} MB")
print(f"float32: {arr32.nbytes / 1e6:.1f} MB")

# 整数类型
# int64 (8 bytes) vs int32 (4 bytes) vs int16 (2 bytes)
prices = np.array([10050, 10051, 10052], dtype=np.int32)

# 使用最小够用的类型
ids = np.arange(1000, dtype=np.int16)  # 0-32767
flags = np.array([True, False, True], dtype=np.bool_)  # 1 byte each
```

---

## 四、高级索引

### 4.1 花式索引

```python
arr = np.arange(10)

# 整数数组索引
indices = np.array([1, 3, 5, 7])
result = arr[indices]  # [1, 3, 5, 7]

# 2D花式索引
matrix = np.arange(12).reshape(3, 4)
rows = np.array([0, 2])
cols = np.array([1, 3])
result = matrix[rows, cols]  # [1, 11]

# 布尔索引
arr = np.array([1, -2, 3, -4, 5])
positive = arr[arr > 0]  # [1, 3, 5]
```

### 4.2 高效选择

```python
# np.take vs 花式索引
arr = np.random.random(1000000)
indices = np.random.randint(0, 1000000, 10000)

# 花式索引
%timeit arr[indices]

# np.take（可能更快）
%timeit np.take(arr, indices)

# np.choose：多数组选择
arrays = [np.array([1, 2, 3]), np.array([4, 5, 6]), np.array([7, 8, 9])]
choices = np.array([0, 1, 2])
result = np.choose(choices, arrays)  # [1, 5, 9]
```

---

## 五、ufunc详解

### 5.1 ufunc属性

```python
# ufunc是通用函数，操作数组元素
add_ufunc = np.add

print(add_ufunc.nin)   # 输入数量: 2
print(add_ufunc.nout)  # 输出数量: 1
print(add_ufunc.types) # 支持的类型签名

# reduce
arr = np.array([1, 2, 3, 4, 5])
print(np.add.reduce(arr))  # 15 (sum)
print(np.multiply.reduce(arr))  # 120 (product)

# accumulate
print(np.add.accumulate(arr))  # [1, 3, 6, 10, 15]

# outer
a = np.array([1, 2, 3])
b = np.array([4, 5])
print(np.multiply.outer(a, b))
# [[4, 5],
#  [8, 10],
#  [12, 15]]
```

### 5.2 自定义ufunc

```python
# 使用np.frompyfunc
def my_add(x, y):
    return x + y

ufunc_add = np.frompyfunc(my_add, 2, 1)
result = ufunc_add(np.array([1, 2, 3]), np.array([4, 5, 6]))

# 使用np.vectorize（更灵活但不快）
@np.vectorize
def custom_func(x, y):
    if x > y:
        return x - y
    else:
        return x + y

result = custom_func(np.array([1, 5, 3]), np.array([2, 2, 2]))
# 注意：np.vectorize只是便利，不是真正的向量化
```

---

## 六、numexpr加速

### 6.1 基本使用

```python
import numexpr as ne
import numpy as np

a = np.random.random(1000000)
b = np.random.random(1000000)
c = np.random.random(1000000)

# NumPy：创建中间数组
result_numpy = a * b + c * 2

# numexpr：无中间数组，多线程
result_ne = ne.evaluate('a * b + c * 2')

# 验证
print(np.allclose(result_numpy, result_ne))  # True
```

### 6.2 性能对比

```python
import time

n = 10000000
a = np.random.random(n)
b = np.random.random(n)
c = np.random.random(n)

# 复杂表达式
expr = 'a**2 + b**2 + 2*a*b + np.sin(c)'

# NumPy
start = time.time()
for _ in range(10):
    result = a**2 + b**2 + 2*a*b + np.sin(c)
print(f"NumPy: {time.time() - start:.3f}s")

# numexpr
start = time.time()
for _ in range(10):
    result = ne.evaluate('a**2 + b**2 + 2*a*b + sin(c)')
print(f"numexpr: {time.time() - start:.3f}s")

# 典型加速：2-10x
```

### 6.3 numexpr优势场景

```python
# 优势场景：
# 1. 复杂表达式（减少中间数组）
# 2. 大数组（多线程）
# 3. 内存受限（就地计算）

# 设置线程数
ne.set_num_threads(4)

# 就地计算
out = np.empty_like(a)
ne.evaluate('a + b', out=out)
```

---

## 七、HFT应用

### 7.1 高性能时间序列计算

```python
def fast_returns(prices):
    """计算收益率"""
    return np.diff(prices) / prices[:-1]

def fast_volatility(returns, window):
    """滚动波动率"""
    # 使用stride_tricks实现滚动窗口
    shape = (len(returns) - window + 1, window)
    strides = (returns.strides[0], returns.strides[0])
    windows = np.lib.stride_tricks.as_strided(returns, shape=shape, strides=strides)
    return np.std(windows, axis=1)

def fast_correlation(x, y, window):
    """滚动相关系数"""
    n = len(x)
    
    # 滚动均值
    x_mean = np.convolve(x, np.ones(window)/window, mode='valid')
    y_mean = np.convolve(y, np.ones(window)/window, mode='valid')
    
    # 滚动协方差和方差
    xy = x[:n-window+1] * y[:n-window+1]  # 简化，实际需要窗口版本
    
    return xy  # 完整实现略
```

### 7.2 订单簿操作

```python
class FastOrderBook:
    def __init__(self, max_levels=100):
        self.bid_prices = np.zeros(max_levels)
        self.bid_quantities = np.zeros(max_levels, dtype=np.int64)
        self.ask_prices = np.zeros(max_levels)
        self.ask_quantities = np.zeros(max_levels, dtype=np.int64)
        self.bid_count = 0
        self.ask_count = 0
    
    def get_mid_price(self):
        if self.bid_count == 0 or self.ask_count == 0:
            return np.nan
        return (self.bid_prices[0] + self.ask_prices[0]) / 2
    
    def get_spread(self):
        if self.bid_count == 0 or self.ask_count == 0:
            return np.nan
        return self.ask_prices[0] - self.bid_prices[0]
    
    def get_weighted_mid(self):
        """加权中间价"""
        if self.bid_count == 0 or self.ask_count == 0:
            return np.nan
        bid_weight = self.bid_quantities[0]
        ask_weight = self.ask_quantities[0]
        total = bid_weight + ask_weight
        return (self.bid_prices[0] * ask_weight + 
                self.ask_prices[0] * bid_weight) / total
```

---

## 总结

| 技术 | 效果 | 适用场景 |
|------|------|----------|
| 向量化 | 50-100x | 替代Python循环 |
| 广播 | 减少拷贝 | 维度扩展运算 |
| 内存布局 | 2-5x | 大矩阵操作 |
| numexpr | 2-10x | 复杂表达式 |
| 合适dtype | 节省内存 | 大数据集 |

**最佳实践**：
1. 尽可能使用向量化操作
2. 利用广播避免显式循环
3. 注意数组连续性
4. 复杂表达式使用numexpr
5. 选择合适的数据类型

---

## 相关文章

- [上一篇：Python内存优化详解](/articles/python/py-50-Python内存优化详解/)
- [下一篇：Pandas性能优化](/articles/python/py-52-Pandas性能优化/)
