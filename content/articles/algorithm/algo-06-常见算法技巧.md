+++
title = "06. 常见算法技巧"
date = 2026-01-19
weight = 6000
description = "算法技巧：双指针、滑动窗口、前缀和、位运算、分治"
[taxonomies]
tags = ["算法", "技巧", "模板"]
+++

## 双指针

### 对撞指针

两个指针从两端向中间移动。

**两数之和（有序数组）**：

```python
def two_sum(nums, target):
    left, right = 0, len(nums) - 1
    
    while left < right:
        total = nums[left] + nums[right]
        if total == target:
            return [left, right]
        elif total < target:
            left += 1
        else:
            right -= 1
    
    return []
```

**接雨水**：

```python
def trap(height):
    left, right = 0, len(height) - 1
    left_max = right_max = 0
    result = 0
    
    while left < right:
        if height[left] < height[right]:
            if height[left] >= left_max:
                left_max = height[left]
            else:
                result += left_max - height[left]
            left += 1
        else:
            if height[right] >= right_max:
                right_max = height[right]
            else:
                result += right_max - height[right]
            right -= 1
    
    return result
```

### 快慢指针

两个指针速度不同。

**链表中点**：

```python
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow
```

**环检测**：

```python
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False
```

**环入口**：

```python
def detect_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            slow = head
            while slow != fast:
                slow = slow.next
                fast = fast.next
            return slow
    return None
```

---

## 滑动窗口

### 固定窗口

```python
def fixed_window(arr, k):
    window_sum = sum(arr[:k])
    result = window_sum
    
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        result = max(result, window_sum)
    
    return result
```

### 可变窗口模板

```python
def sliding_window(s):
    left = 0
    window = {}
    result = 0
    
    for right in range(len(s)):
        # 扩展窗口
        char = s[right]
        window[char] = window.get(char, 0) + 1
        
        # 收缩窗口
        while 需要收缩:
            left_char = s[left]
            window[left_char] -= 1
            if window[left_char] == 0:
                del window[left_char]
            left += 1
        
        # 更新结果
        result = max(result, right - left + 1)
    
    return result
```

### 最长无重复子串

```python
def length_of_longest_substring(s):
    left = 0
    seen = {}
    result = 0
    
    for right, char in enumerate(s):
        if char in seen and seen[char] >= left:
            left = seen[char] + 1
        seen[char] = right
        result = max(result, right - left + 1)
    
    return result
```

### 最小覆盖子串

```python
def min_window(s, t):
    from collections import Counter
    
    need = Counter(t)
    window = {}
    left = 0
    valid = 0
    start, length = 0, float('inf')
    
    for right, char in enumerate(s):
        if char in need:
            window[char] = window.get(char, 0) + 1
            if window[char] == need[char]:
                valid += 1
        
        while valid == len(need):
            if right - left + 1 < length:
                start, length = left, right - left + 1
            
            left_char = s[left]
            if left_char in need:
                if window[left_char] == need[left_char]:
                    valid -= 1
                window[left_char] -= 1
            left += 1
    
    return s[start:start + length] if length != float('inf') else ""
```

---

## 前缀和

### 一维前缀和

```python
def prefix_sum(nums):
    n = len(nums)
    prefix = [0] * (n + 1)
    
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]
    
    return prefix

# 区间和 [i, j]
# sum = prefix[j + 1] - prefix[i]
```

### 二维前缀和

```python
def prefix_sum_2d(matrix):
    m, n = len(matrix), len(matrix[0])
    prefix = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m):
        for j in range(n):
            prefix[i+1][j+1] = (prefix[i][j+1] + prefix[i+1][j] 
                               - prefix[i][j] + matrix[i][j])
    
    return prefix

# 区域和 (r1, c1) 到 (r2, c2)
# sum = prefix[r2+1][c2+1] - prefix[r1][c2+1] - prefix[r2+1][c1] + prefix[r1][c1]
```

### 差分数组

用于区间更新。

```python
def difference_array(nums, updates):
    n = len(nums)
    diff = [0] * (n + 1)
    
    for start, end, val in updates:
        diff[start] += val
        diff[end + 1] -= val
    
    # 还原
    result = [0] * n
    result[0] = diff[0]
    for i in range(1, n):
        result[i] = result[i-1] + diff[i]
    
    return [a + b for a, b in zip(nums, result)]
```

---

## 位运算

### 常用操作

```python
# 获取第i位
(n >> i) & 1

# 设置第i位为1
n | (1 << i)

# 清除第i位
n & ~(1 << i)

# 翻转第i位
n ^ (1 << i)

# 获取最低位的1
n & (-n)

# 清除最低位的1
n & (n - 1)

# 判断是否是2的幂
n > 0 and (n & (n - 1)) == 0
```

### 统计1的个数

```python
def count_ones(n):
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count
```

### 只出现一次的数字

```python
def single_number(nums):
    result = 0
    for num in nums:
        result ^= num
    return result
```

### 位运算实现加法

```python
def add(a, b):
    mask = 0xFFFFFFFF
    
    while b & mask:
        carry = (a & b) << 1
        a = a ^ b
        b = carry
    
    return a if b == 0 else ~(a ^ mask)
```

---

## 分治

### 核心思想

1. **分解**：将问题分解为子问题
2. **解决**：递归解决子问题
3. **合并**：合并子问题的解

### 归并排序

```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)
```

### 快速幂

```python
def power(base, exp):
    result = 1
    while exp > 0:
        if exp & 1:
            result *= base
        base *= base
        exp >>= 1
    return result
```

### 最大子数组（分治）

```python
def max_subarray(nums, left, right):
    if left == right:
        return nums[left]
    
    mid = (left + right) // 2
    
    left_max = max_subarray(nums, left, mid)
    right_max = max_subarray(nums, mid + 1, right)
    cross_max = max_crossing(nums, left, mid, right)
    
    return max(left_max, right_max, cross_max)
```

---

## 数学技巧

### GCD

```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
```

### LCM

```python
def lcm(a, b):
    return a * b // gcd(a, b)
```

### 质数判断

```python
def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True
```

### 埃氏筛

```python
def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    
    return [i for i in range(n + 1) if is_prime[i]]
```

---

## 总结

| 技巧 | 适用场景 |
|------|----------|
| 对撞指针 | 有序数组、回文 |
| 快慢指针 | 链表、环检测 |
| 滑动窗口 | 连续子数组/子串 |
| 前缀和 | 区间查询 |
| 差分 | 区间更新 |
| 位运算 | 位操作、状态压缩 |
| 分治 | 可分解问题 |

掌握这些技巧可以解决大部分算法问题。

---

## 相关文章

- [上一篇：回溯与贪心](@/articles/algorithm/algo-05-回溯与贪心.md)
- [下一篇：高级数据结构](@/articles/algorithm/algo-07-高级数据结构.md)
