+++
title = "05. 回溯与贪心"
date = 2026-01-19
weight = 5000
description = "回溯算法：模板与剪枝；贪心算法：思想与经典问题"
[taxonomies]
tags = ["算法", "回溯", "贪心"]
+++

## 回溯算法

### 核心思想

通过穷举所有可能的解，并在发现不满足条件时"回溯"，撤销上一步选择。

### 适用问题

- 排列组合
- 子集
- 切割
- 棋盘问题
- 图搜索

### 基本模板

```python
def backtrack(path, choices):
    if 满足结束条件:
        result.append(path[:])
        return
    
    for choice in choices:
        if 不合法:
            continue
        
        # 做选择
        path.append(choice)
        
        # 递归
        backtrack(path, new_choices)
        
        # 撤销选择
        path.pop()
```

---

## 排列组合问题

### 全排列

```python
def permute(nums):
    result = []
    
    def backtrack(path, used):
        if len(path) == len(nums):
            result.append(path[:])
            return
        
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack(path, used)
            path.pop()
            used[i] = False
    
    backtrack([], [False] * len(nums))
    return result
```

### 全排列（有重复）

```python
def permute_unique(nums):
    result = []
    nums.sort()
    
    def backtrack(path, used):
        if len(path) == len(nums):
            result.append(path[:])
            return
        
        for i in range(len(nums)):
            if used[i]:
                continue
            # 剪枝：相同元素，只在第一个未使用时才选择
            if i > 0 and nums[i] == nums[i-1] and not used[i-1]:
                continue
            
            used[i] = True
            path.append(nums[i])
            backtrack(path, used)
            path.pop()
            used[i] = False
    
    backtrack([], [False] * len(nums))
    return result
```

### 组合

```python
def combine(n, k):
    result = []
    
    def backtrack(start, path):
        if len(path) == k:
            result.append(path[:])
            return
        
        # 剪枝：剩余元素不够
        if n - start + 1 < k - len(path):
            return
        
        for i in range(start, n + 1):
            path.append(i)
            backtrack(i + 1, path)
            path.pop()
    
    backtrack(1, [])
    return result
```

### 子集

```python
def subsets(nums):
    result = []
    
    def backtrack(start, path):
        result.append(path[:])
        
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()
    
    backtrack(0, [])
    return result
```

---

## 剪枝技巧

### 可行性剪枝

提前判断当前路径是否可能产生有效解。

```python
# 组合总和问题
def combination_sum(candidates, target):
    result = []
    candidates.sort()
    
    def backtrack(start, path, remain):
        if remain == 0:
            result.append(path[:])
            return
        
        for i in range(start, len(candidates)):
            # 剪枝：后面的元素更大，不可能满足
            if candidates[i] > remain:
                break
            
            path.append(candidates[i])
            backtrack(i, path, remain - candidates[i])
            path.pop()
    
    backtrack(0, [], target)
    return result
```

### 去重剪枝

对于有重复元素的情况，避免产生重复解。

```python
# 相同层级，相同元素只选一次
if i > start and candidates[i] == candidates[i-1]:
    continue
```

### 最优性剪枝

当前路径已经不可能优于已知最优解时剪枝。

---

## 经典回溯问题

### N皇后

```python
def solve_n_queens(n):
    result = []
    
    def is_valid(board, row, col):
        # 检查列
        for i in range(row):
            if board[i][col] == 'Q':
                return False
        # 检查左上对角线
        i, j = row - 1, col - 1
        while i >= 0 and j >= 0:
            if board[i][j] == 'Q':
                return False
            i, j = i - 1, j - 1
        # 检查右上对角线
        i, j = row - 1, col + 1
        while i >= 0 and j < n:
            if board[i][j] == 'Q':
                return False
            i, j = i - 1, j + 1
        return True
    
    def backtrack(board, row):
        if row == n:
            result.append([''.join(r) for r in board])
            return
        
        for col in range(n):
            if not is_valid(board, row, col):
                continue
            board[row][col] = 'Q'
            backtrack(board, row + 1)
            board[row][col] = '.'
    
    board = [['.' for _ in range(n)] for _ in range(n)]
    backtrack(board, 0)
    return result
```

### 数独

```python
def solve_sudoku(board):
    def is_valid(row, col, num):
        # 检查行
        if num in board[row]:
            return False
        # 检查列
        if num in [board[i][col] for i in range(9)]:
            return False
        # 检查3x3方格
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if board[i][j] == num:
                    return False
        return True
    
    def solve():
        for i in range(9):
            for j in range(9):
                if board[i][j] == '.':
                    for num in '123456789':
                        if is_valid(i, j, num):
                            board[i][j] = num
                            if solve():
                                return True
                            board[i][j] = '.'
                    return False
        return True
    
    solve()
```

---

## 贪心算法

### 核心思想

每一步都选择当前最优的选择，期望得到全局最优解。

### 适用条件

- **贪心选择性质**：局部最优能导致全局最优
- **最优子结构**：问题的最优解包含子问题的最优解

### 与动态规划的区别

| 贪心 | 动态规划 |
|------|----------|
| 每步只考虑当前最优 | 考虑所有可能 |
| 不回溯 | 可能需要比较多种方案 |
| 效率高 | 通常更慢 |
| 可能得不到最优解 | 保证最优解 |

---

## 经典贪心问题

### 活动选择

```
问题：选择最多的不重叠活动

贪心策略：按结束时间排序，优先选择最早结束的
```

```python
def activity_selection(activities):
    # 按结束时间排序
    activities.sort(key=lambda x: x[1])
    
    result = [activities[0]]
    last_end = activities[0][1]
    
    for start, end in activities[1:]:
        if start >= last_end:
            result.append((start, end))
            last_end = end
    
    return result
```

### 跳跃游戏

```
问题：能否跳到最后一个位置

贪心策略：维护能到达的最远位置
```

```python
def can_jump(nums):
    max_reach = 0
    
    for i in range(len(nums)):
        if i > max_reach:
            return False
        max_reach = max(max_reach, i + nums[i])
    
    return True
```

### 跳跃游戏II（最少跳跃次数）

```python
def jump(nums):
    jumps = 0
    current_end = 0
    farthest = 0
    
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == current_end:
            jumps += 1
            current_end = farthest
    
    return jumps
```

### 分发糖果

```
问题：相邻评分高的孩子要得到更多糖果

贪心策略：两次遍历，左到右和右到左
```

```python
def candy(ratings):
    n = len(ratings)
    candies = [1] * n
    
    # 从左到右
    for i in range(1, n):
        if ratings[i] > ratings[i-1]:
            candies[i] = candies[i-1] + 1
    
    # 从右到左
    for i in range(n-2, -1, -1):
        if ratings[i] > ratings[i+1]:
            candies[i] = max(candies[i], candies[i+1] + 1)
    
    return sum(candies)
```

### 加油站

```python
def can_complete_circuit(gas, cost):
    total = 0
    current = 0
    start = 0
    
    for i in range(len(gas)):
        diff = gas[i] - cost[i]
        total += diff
        current += diff
        
        if current < 0:
            start = i + 1
            current = 0
    
    return start if total >= 0 else -1
```

---

## 区间问题

### 合并区间

```python
def merge(intervals):
    intervals.sort(key=lambda x: x[0])
    result = [intervals[0]]
    
    for start, end in intervals[1:]:
        if start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    
    return result
```

### 无重叠区间（最少移除）

```python
def erase_overlap_intervals(intervals):
    intervals.sort(key=lambda x: x[1])
    count = 0
    end = float('-inf')
    
    for start, finish in intervals:
        if start >= end:
            end = finish
        else:
            count += 1
    
    return count
```

---

## 总结

| 算法 | 适用场景 | 特点 |
|------|----------|------|
| 回溯 | 排列组合、搜索 | 穷举+剪枝 |
| 贪心 | 最优选择问题 | 局部最优 |

**回溯**：当需要遍历所有可能解时使用
**贪心**：当能证明局部最优=全局最优时使用

两者都需要多做题培养直觉。

---

## 相关文章

- [上一篇：动态规划](@/articles/algorithm/algo-04-动态规划.md)
- [下一篇：常见算法技巧](@/articles/algorithm/algo-06-常见算法技巧.md)
