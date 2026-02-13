+++
title = "动态规划"
date = 2026-01-19
weight = 4000
description = "动态规划：核心思想、状态设计、经典问题、优化技巧"
[taxonomies]
tags = ["算法", "动态规划", "DP"]
+++

## 核心思想

### 什么是动态规划

将复杂问题分解为重叠子问题，通过存储子问题的解避免重复计算。

### 适用条件

1. **最优子结构**：问题的最优解包含子问题的最优解
2. **重叠子问题**：子问题被重复计算

### 解题步骤

1. **定义状态**：明确dp[i]或dp[i][j]的含义
2. **状态转移**：找到状态之间的关系
3. **初始化**：确定边界条件
4. **遍历顺序**：确保计算时依赖的状态已计算
5. **返回结果**：确定答案位置

---

## 线性DP

### 爬楼梯

```
问题：每次爬1或2阶，到达第n阶有多少种方法

状态：dp[i] = 到达第i阶的方法数
转移：dp[i] = dp[i-1] + dp[i-2]
初始：dp[0] = 1, dp[1] = 1
```

```python
def climb_stairs(n):
    if n <= 1:
        return 1
    dp = [0] * (n + 1)
    dp[0] = dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    return dp[n]
```

### 打家劫舍

```
问题：不能抢相邻房屋，最大金额

状态：dp[i] = 前i个房屋的最大金额
转移：dp[i] = max(dp[i-1], dp[i-2] + nums[i])
```

```python
def rob(nums):
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    dp = [0] * len(nums)
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    
    for i in range(2, len(nums)):
        dp[i] = max(dp[i-1], dp[i-2] + nums[i])
    
    return dp[-1]
```

### 最长递增子序列

```
状态：dp[i] = 以nums[i]结尾的LIS长度
转移：dp[i] = max(dp[j] + 1) 对所有 j < i 且 nums[j] < nums[i]
```

```python
def length_of_lis(nums):
    n = len(nums)
    dp = [1] * n
    
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)
```

**优化**：使用二分搜索，O(n log n)

---

## 背包问题

### 0-1背包

```
问题：每个物品只能选一次，最大价值

状态：dp[i][j] = 前i个物品，容量j的最大价值
转移：dp[i][j] = max(dp[i-1][j], dp[i-1][j-w[i]] + v[i])
```

```python
def knapsack_01(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for j in range(capacity + 1):
            dp[i][j] = dp[i-1][j]
            if j >= weights[i-1]:
                dp[i][j] = max(dp[i][j], dp[i-1][j-weights[i-1]] + values[i-1])
    
    return dp[n][capacity]
```

**空间优化**：滚动数组，逆序遍历

```python
def knapsack_01_optimized(weights, values, capacity):
    dp = [0] * (capacity + 1)
    
    for i in range(len(weights)):
        for j in range(capacity, weights[i] - 1, -1):  # 逆序
            dp[j] = max(dp[j], dp[j - weights[i]] + values[i])
    
    return dp[capacity]
```

### 完全背包

每个物品可以选无限次，顺序遍历。

```python
def knapsack_complete(weights, values, capacity):
    dp = [0] * (capacity + 1)
    
    for i in range(len(weights)):
        for j in range(weights[i], capacity + 1):  # 顺序
            dp[j] = max(dp[j], dp[j - weights[i]] + values[i])
    
    return dp[capacity]
```

### 多重背包

每个物品有限制数量，可用二进制优化。

---

## 区间DP

### 矩阵链乘法

```
状态：dp[i][j] = 矩阵i到j相乘的最小次数
转移：dp[i][j] = min(dp[i][k] + dp[k+1][j] + cost(i,k,j))
```

### 最长回文子串

```python
def longest_palindrome(s):
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    start, max_len = 0, 1
    
    # 长度为1
    for i in range(n):
        dp[i][i] = True
    
    # 长度为2
    for i in range(n - 1):
        if s[i] == s[i + 1]:
            dp[i][i + 1] = True
            start, max_len = i, 2
    
    # 长度>2
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j] and dp[i + 1][j - 1]:
                dp[i][j] = True
                start, max_len = i, length
    
    return s[start:start + max_len]
```

---

## 序列DP

### 最长公共子序列

```
状态：dp[i][j] = s1前i个和s2前j个的LCS长度
转移：
  s1[i] == s2[j]: dp[i][j] = dp[i-1][j-1] + 1
  否则: dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

```python
def lcs(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]
```

### 编辑距离

```
状态：dp[i][j] = s1前i个转换到s2前j个的最小操作数
转移：
  s1[i] == s2[j]: dp[i][j] = dp[i-1][j-1]
  否则: dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
```

```python
def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    return dp[m][n]
```

---

## 状态压缩DP

### 旅行商问题

用位掩码表示访问过的城市集合。

```python
def tsp(dist):
    n = len(dist)
    dp = [[float('inf')] * n for _ in range(1 << n)]
    dp[1][0] = 0  # 从城市0出发
    
    for mask in range(1, 1 << n):
        for u in range(n):
            if not (mask & (1 << u)):
                continue
            for v in range(n):
                if mask & (1 << v):
                    continue
                new_mask = mask | (1 << v)
                dp[new_mask][v] = min(dp[new_mask][v], dp[mask][u] + dist[u][v])
    
    full_mask = (1 << n) - 1
    return min(dp[full_mask][i] + dist[i][0] for i in range(1, n))
```

---

## 优化技巧

### 空间优化

- 滚动数组：只保留必要的行/列
- 一维数组：适当调整遍历顺序

### 前缀和优化

预处理区间和，O(1)查询

### 单调队列优化

滑动窗口最值问题

### 决策单调性

利用决策单调性减少搜索范围

---

## 解题模板

### 判断是否是DP问题

- 求最值、方案数、可行性
- 有重叠子问题
- 有最优子结构

### 状态定义技巧

- 以第i个元素结尾
- 考虑前i个元素
- 区间[i, j]
- 剩余容量/资源为j

### 常见状态转移

```
线性：dp[i] = f(dp[i-1], dp[i-2], ...)
背包：dp[i][j] = max(dp[i-1][j], dp[i-1][j-w] + v)
区间：dp[i][j] = f(dp[i][k], dp[k+1][j])
序列：dp[i][j] = f(dp[i-1][j-1], dp[i-1][j], dp[i][j-1])
```

---

## 总结

| 类型 | 特点 | 例题 |
|------|------|------|
| 线性DP | 一维状态 | 爬楼梯、打家劫舍 |
| 背包DP | 容量限制 | 0-1背包、完全背包 |
| 区间DP | 区间划分 | 矩阵链、回文串 |
| 序列DP | 两个序列 | LCS、编辑距离 |
| 状压DP | 集合状态 | TSP |

动态规划的核心是**状态定义**和**状态转移**，多练习可以形成直觉。

---

## 相关文章

- [上一篇：树与图](@/articles/algorithm/algo-03-树与图.md)
- [下一篇：回溯与贪心](@/articles/algorithm/algo-05-回溯与贪心.md)
