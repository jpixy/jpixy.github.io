+++
title = "53.Pandas性能优化"
date = 2026-01-21
description = "深入剖析Pandas的性能优化技术，包括内存优化、向量化操作、apply陷阱、大数据处理和dtype优化"
[taxonomies]
tags = ["Python", "Pandas", "性能优化", "数据处理", "量化"]
+++

## 概述

Pandas是量化分析的核心工具，但默认使用往往效率不高。本文深入讲解Pandas性能优化技巧。

---

## 一、内存优化

### 1.1 dtype优化

```python
import pandas as pd
import numpy as np

# 读取数据并检查内存
df = pd.read_csv('data.csv')
print(df.info(memory_usage='deep'))

# 优化数值类型
def optimize_numeric(df):
    for col in df.select_dtypes(include=['int64']).columns:
        if df[col].min() >= 0:
            if df[col].max() < 256:
                df[col] = df[col].astype(np.uint8)
            elif df[col].max() < 65536:
                df[col] = df[col].astype(np.uint16)
            elif df[col].max() < 4294967296:
                df[col] = df[col].astype(np.uint32)
        else:
            if df[col].min() > -128 and df[col].max() < 128:
                df[col] = df[col].astype(np.int8)
            elif df[col].min() > -32768 and df[col].max() < 32768:
                df[col] = df[col].astype(np.int16)
            elif df[col].min() > -2147483648 and df[col].max() < 2147483648:
                df[col] = df[col].astype(np.int32)
    
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype(np.float32)
    
    return df

df = optimize_numeric(df)
print(df.info(memory_usage='deep'))
```

### 1.2 Category类型

```python
# 对于低基数字符串列，使用category
df = pd.DataFrame({
    'symbol': ['AAPL', 'GOOG', 'MSFT'] * 100000,
    'side': ['BUY', 'SELL'] * 150000,
    'price': np.random.random(300000)
})

print(f"Before: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

df['symbol'] = df['symbol'].astype('category')
df['side'] = df['side'].astype('category')

print(f"After: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
# 典型节省：50-90%字符串列内存
```

### 1.3 读取时指定dtype

```python
# 在读取时直接指定类型，避免后续转换
dtypes = {
    'order_id': np.int32,
    'symbol': 'category',
    'price': np.float32,
    'quantity': np.int32,
    'side': 'category',
}

df = pd.read_csv('orders.csv', dtype=dtypes)

# 使用parse_dates
df = pd.read_csv('trades.csv', 
                 dtype=dtypes,
                 parse_dates=['timestamp'])
```

---

## 二、向量化操作

### 2.1 避免apply

```python
import time

df = pd.DataFrame({
    'a': np.random.random(100000),
    'b': np.random.random(100000),
})

# 慢：使用apply
def slow_compute(row):
    return row['a'] * 2 + row['b'] * 3

start = time.time()
df['result'] = df.apply(slow_compute, axis=1)
print(f"apply: {time.time() - start:.4f}s")

# 快：向量化
start = time.time()
df['result'] = df['a'] * 2 + df['b'] * 3
print(f"vectorized: {time.time() - start:.4f}s")

# 典型加速：100-1000x
```

### 2.2 条件操作

```python
# 慢：使用apply
df['category'] = df.apply(
    lambda row: 'high' if row['value'] > 100 else 'low', axis=1
)

# 快：使用np.where
df['category'] = np.where(df['value'] > 100, 'high', 'low')

# 多条件：np.select
conditions = [
    df['value'] < 50,
    df['value'] < 100,
    df['value'] >= 100
]
choices = ['low', 'medium', 'high']
df['category'] = np.select(conditions, choices)

# 或使用pd.cut
df['category'] = pd.cut(df['value'], 
                        bins=[0, 50, 100, float('inf')],
                        labels=['low', 'medium', 'high'])
```

### 2.3 字符串操作

```python
# 慢：使用apply
df['upper'] = df['name'].apply(lambda x: x.upper())

# 快：使用str方法
df['upper'] = df['name'].str.upper()

# 其他str方法
df['first_char'] = df['name'].str[0]
df['length'] = df['name'].str.len()
df['contains_a'] = df['name'].str.contains('a')
df['split'] = df['name'].str.split('_')
```

---

## 三、分组操作

### 3.1 高效groupby

```python
# 预排序可以加速groupby
df = df.sort_values('symbol')

# 使用agg一次计算多个统计量
result = df.groupby('symbol').agg({
    'price': ['mean', 'std', 'min', 'max'],
    'quantity': 'sum'
})

# 自定义聚合函数（尽量使用内置）
# 慢
def custom_range(x):
    return x.max() - x.min()

# 快
result = df.groupby('symbol')['price'].agg(lambda x: x.max() - x.min())

# 最快：使用内置
result = df.groupby('symbol')['price'].agg(['max', 'min'])
result['range'] = result['max'] - result['min']
```

### 3.2 transform优化

```python
# 计算组内标准化
# 慢
df['normalized'] = df.groupby('symbol')['price'].transform(
    lambda x: (x - x.mean()) / x.std()
)

# 快：分步计算
means = df.groupby('symbol')['price'].transform('mean')
stds = df.groupby('symbol')['price'].transform('std')
df['normalized'] = (df['price'] - means) / stds
```

### 3.3 滚动窗口

```python
# 滚动统计
df['ma_20'] = df.groupby('symbol')['price'].transform(
    lambda x: x.rolling(20).mean()
)

# 使用numba加速
from numba import jit

@jit(nopython=True)
def rolling_mean_numba(arr, window):
    result = np.empty(len(arr))
    result[:window-1] = np.nan
    for i in range(window-1, len(arr)):
        result[i] = arr[i-window+1:i+1].mean()
    return result

# 应用
df['ma_20'] = df.groupby('symbol')['price'].transform(
    lambda x: rolling_mean_numba(x.values, 20)
)
```

---

## 四、大数据处理

### 4.1 分块读取

```python
# 分块处理大文件
chunks = pd.read_csv('large_file.csv', chunksize=100000)

results = []
for chunk in chunks:
    # 处理每个块
    processed = chunk.groupby('symbol')['price'].mean()
    results.append(processed)

# 合并结果
final_result = pd.concat(results).groupby(level=0).mean()
```

### 4.2 使用迭代器

```python
# 迭代处理，减少内存
def process_in_chunks(filepath, chunksize=100000):
    for chunk in pd.read_csv(filepath, chunksize=chunksize):
        # 只保留需要的列
        chunk = chunk[['symbol', 'price', 'quantity']]
        
        # 处理
        yield chunk.groupby('symbol').agg({
            'price': 'mean',
            'quantity': 'sum'
        })

# 使用
results = list(process_in_chunks('data.csv'))
final = pd.concat(results).groupby(level=0).agg({
    'price': 'mean',
    'quantity': 'sum'
})
```

### 4.3 使用Parquet格式

```python
# Parquet比CSV更快更小
df.to_parquet('data.parquet', engine='pyarrow', compression='snappy')

# 读取（支持列选择和谓词下推）
df = pd.read_parquet('data.parquet', 
                     columns=['symbol', 'price'],
                     filters=[('date', '>=', '2024-01-01')])

# 性能对比
import time

# CSV
start = time.time()
df = pd.read_csv('data.csv')
print(f"CSV read: {time.time() - start:.2f}s")

# Parquet
start = time.time()
df = pd.read_parquet('data.parquet')
print(f"Parquet read: {time.time() - start:.2f}s")

# 典型加速：5-10x
```

---

## 五、索引优化

### 5.1 设置合适的索引

```python
# 频繁查询的列设为索引
df = df.set_index('order_id')

# 多级索引
df = df.set_index(['symbol', 'date'])

# 查询优化
# 使用.loc比布尔索引快
df.loc['AAPL']  # 快
df[df['symbol'] == 'AAPL']  # 慢

# 范围查询
df.loc['AAPL':'MSFT']  # 需要排序的索引
```

### 5.2 索引查询

```python
# 确保索引排序
df = df.sort_index()

# 使用.xs进行多级索引查询
df.xs('AAPL', level='symbol')

# 使用IndexSlice
idx = pd.IndexSlice
df.loc[idx['AAPL', '2024-01-01':'2024-12-31'], :]
```

---

## 六、并行处理

### 6.1 使用swifter

```python
import swifter

# 自动选择最优执行方式
df['result'] = df['value'].swifter.apply(complex_function)
```

### 6.2 使用modin

```python
# 替换pandas
import modin.pandas as pd

# API完全兼容
df = pd.read_csv('large_file.csv')
result = df.groupby('symbol')['price'].mean()

# 自动并行化
```

### 6.3 手动并行

```python
from concurrent.futures import ProcessPoolExecutor
import pandas as pd

def process_group(group_data):
    symbol, data = group_data
    return symbol, data['price'].mean()

def parallel_groupby(df, column):
    groups = list(df.groupby(column))
    
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_group, groups))
    
    return dict(results)

result = parallel_groupby(df, 'symbol')
```

---

## 七、常见陷阱

### 7.1 链式操作警告

```python
# 不好：可能产生SettingWithCopyWarning
df[df['value'] > 0]['new_col'] = 1

# 好：使用.loc
df.loc[df['value'] > 0, 'new_col'] = 1

# 或使用copy
subset = df[df['value'] > 0].copy()
subset['new_col'] = 1
```

### 7.2 避免频繁追加

```python
# 不好：循环追加
result = pd.DataFrame()
for chunk in data_chunks:
    result = pd.concat([result, chunk])  # 每次复制

# 好：收集后一次concat
chunks = []
for chunk in data_chunks:
    chunks.append(chunk)
result = pd.concat(chunks, ignore_index=True)
```

### 7.3 inplace参数

```python
# inplace=True通常不会更快
# 而且不利于链式操作

# 不推荐
df.drop('col', axis=1, inplace=True)

# 推荐
df = df.drop('col', axis=1)
```

---

## 总结

| 优化技术 | 效果 | 适用场景 |
|----------|------|----------|
| dtype优化 | 节省50-80%内存 | 大数据集 |
| 向量化 | 100-1000x | 替代apply |
| Category | 节省90%内存 | 低基数字符串 |
| Parquet | 5-10x读取速度 | 数据存储 |
| 分块处理 | 处理超大文件 | 内存受限 |

**最佳实践**：
1. 读取时指定dtype
2. 避免使用apply
3. 使用Category存储字符串
4. 使用Parquet存储数据
5. 大文件分块处理
