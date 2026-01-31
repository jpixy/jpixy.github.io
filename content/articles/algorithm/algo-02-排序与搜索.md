+++
title = "02.排序与搜索"
date = 2026-01-19
description = "排序算法：快排、归并、堆排序；搜索算法：二分查找及其变体"
[taxonomies]
tags = ["算法", "排序", "搜索"]
+++

## 排序算法对比

| 算法 | 平均 | 最差 | 空间 | 稳定 |
|------|------|------|------|------|
| 冒泡 | O(n²) | O(n²) | O(1) | 是 |
| 选择 | O(n²) | O(n²) | O(1) | 否 |
| 插入 | O(n²) | O(n²) | O(1) | 是 |
| 归并 | O(nlogn) | O(nlogn) | O(n) | 是 |
| 快排 | O(nlogn) | O(n²) | O(logn) | 否 |
| 堆排 | O(nlogn) | O(nlogn) | O(1) | 否 |
| 计数 | O(n+k) | O(n+k) | O(k) | 是 |
| 桶排 | O(n+k) | O(n²) | O(n) | 是 |
| 基数 | O(d(n+k)) | O(d(n+k)) | O(n+k) | 是 |

---

## 快速排序

### 核心思想

1. 选择基准元素（pivot）
2. 分区：小于pivot的放左边，大于的放右边
3. 递归排序左右部分

### 实现

```python
def quicksort(arr, left, right):
    if left < right:
        pivot_idx = partition(arr, left, right)
        quicksort(arr, left, pivot_idx - 1)
        quicksort(arr, pivot_idx + 1, right)

def partition(arr, left, right):
    pivot = arr[right]
    i = left - 1
    for j in range(left, right):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[right] = arr[right], arr[i + 1]
    return i + 1
```

### 优化

**随机化**：随机选择pivot，避免最差情况

**三数取中**：取首、中、尾的中位数作为pivot

**小数组切换插入排序**：小于阈值时用插入排序

---

## 归并排序

### 核心思想

1. 递归分割数组为两半
2. 分别排序
3. 合并两个有序数组

### 实现

```python
def mergesort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

### 应用

- 稳定排序场景
- 链表排序
- 外部排序
- 求逆序对

---

## 堆排序

### 核心思想

1. 建立最大堆
2. 交换堆顶和末尾
3. 堆大小减1，重新堆化
4. 重复直到堆为空

### 实现

```python
def heapsort(arr):
    n = len(arr)
    
    # 建堆
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # 排序
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)

def heapify(arr, n, i):
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2
    
    if left < n and arr[left] > arr[largest]:
        largest = left
    if right < n and arr[right] > arr[largest]:
        largest = right
    
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)
```

### 特点

- 原地排序，O(1)额外空间
- 不稳定
- 适合Top K问题

---

## 二分查找

### 标准模板

```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1
```

### 关键点

- `left + (right - left) // 2`：防止溢出
- `left <= right`：区间非空时继续
- 更新时不包含mid

---

## 二分变体

### 查找第一个等于target

```python
def find_first(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    if left < len(arr) and arr[left] == target:
        return left
    return -1
```

### 查找最后一个等于target

```python
def find_last(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] <= target:
            left = mid + 1
        else:
            right = mid - 1
    
    if right >= 0 and arr[right] == target:
        return right
    return -1
```

### 查找第一个大于等于target

```python
def lower_bound(arr, target):
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    
    return left
```

### 查找第一个大于target

```python
def upper_bound(arr, target):
    left, right = 0, len(arr)
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] <= target:
            left = mid + 1
        else:
            right = mid
    
    return left
```

---

## 二分应用

### 旋转数组搜索

```python
def search_rotated(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        
        # 左半部分有序
        if arr[left] <= arr[mid]:
            if arr[left] <= target < arr[mid]:
                right = mid - 1
            else:
                left = mid + 1
        # 右半部分有序
        else:
            if arr[mid] < target <= arr[right]:
                left = mid + 1
            else:
                right = mid - 1
    
    return -1
```

### 峰值元素

```python
def find_peak(arr):
    left, right = 0, len(arr) - 1
    
    while left < right:
        mid = left + (right - left) // 2
        
        if arr[mid] < arr[mid + 1]:
            left = mid + 1
        else:
            right = mid
    
    return left
```

### 搜索二维矩阵

```python
def search_matrix(matrix, target):
    if not matrix:
        return False
    
    m, n = len(matrix), len(matrix[0])
    left, right = 0, m * n - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        value = matrix[mid // n][mid % n]
        
        if value == target:
            return True
        elif value < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return False
```

### 二分答案

问题转化为：答案在[low, high]范围内，找满足条件的最小/最大值。

```python
def binary_answer(low, high):
    while left < right:
        mid = left + (right - left) // 2
        
        if check(mid):  # mid满足条件
            right = mid  # 找更小的
        else:
            left = mid + 1
    
    return left
```

---

## 非比较排序

### 计数排序

适用于：范围有限的整数

```python
def counting_sort(arr):
    if not arr:
        return arr
    
    min_val, max_val = min(arr), max(arr)
    count = [0] * (max_val - min_val + 1)
    
    for num in arr:
        count[num - min_val] += 1
    
    result = []
    for i, c in enumerate(count):
        result.extend([i + min_val] * c)
    
    return result
```

### 桶排序

适用于：均匀分布的数据

### 基数排序

适用于：整数或固定长度字符串

---

## 总结

| 场景 | 推荐算法 |
|------|----------|
| 通用排序 | 快排 |
| 稳定排序 | 归并 |
| 原地排序 | 堆排 |
| 小范围整数 | 计数排序 |
| 有序数组搜索 | 二分查找 |
| 答案单调性 | 二分答案 |

二分查找的关键是确定**搜索空间**和**收缩条件**。

---

## 相关文章

- [上一篇：数据结构基础](/articles/algorithm/algo-01-数据结构基础/)
- [下一篇：树与图](/articles/algorithm/algo-03-树与图/)
