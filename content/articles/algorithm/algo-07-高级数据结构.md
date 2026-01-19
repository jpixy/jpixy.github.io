+++
title = "07.高级数据结构"
date = 2026-01-19
description = "高级数据结构：线段树、树状数组、字典树、跳表、布隆过滤器"
[taxonomies]
tags = ["算法", "数据结构", "高级"]
+++

## 线段树

### 适用场景

- 区间查询：区间和、区间最值
- 区间更新：单点更新、区间更新
- 时间复杂度：O(log n)

### 基本实现

```python
class SegmentTree:
    def __init__(self, nums):
        self.n = len(nums)
        self.tree = [0] * (4 * self.n)
        self.build(nums, 0, 0, self.n - 1)
    
    def build(self, nums, node, start, end):
        if start == end:
            self.tree[node] = nums[start]
        else:
            mid = (start + end) // 2
            left, right = 2 * node + 1, 2 * node + 2
            self.build(nums, left, start, mid)
            self.build(nums, right, mid + 1, end)
            self.tree[node] = self.tree[left] + self.tree[right]
    
    def update(self, idx, val, node=0, start=0, end=None):
        if end is None:
            end = self.n - 1
        
        if start == end:
            self.tree[node] = val
        else:
            mid = (start + end) // 2
            left, right = 2 * node + 1, 2 * node + 2
            if idx <= mid:
                self.update(idx, val, left, start, mid)
            else:
                self.update(idx, val, right, mid + 1, end)
            self.tree[node] = self.tree[left] + self.tree[right]
    
    def query(self, l, r, node=0, start=0, end=None):
        if end is None:
            end = self.n - 1
        
        if r < start or l > end:
            return 0
        if l <= start and end <= r:
            return self.tree[node]
        
        mid = (start + end) // 2
        left_sum = self.query(l, r, 2 * node + 1, start, mid)
        right_sum = self.query(l, r, 2 * node + 2, mid + 1, end)
        return left_sum + right_sum
```

### 懒惰传播

区间更新时延迟下推。

```python
def range_update(self, l, r, val, node, start, end):
    if self.lazy[node] != 0:
        self.push_down(node, start, end)
    
    if r < start or l > end:
        return
    if l <= start and end <= r:
        self.tree[node] += val * (end - start + 1)
        if start != end:
            self.lazy[2*node+1] += val
            self.lazy[2*node+2] += val
        return
    
    mid = (start + end) // 2
    self.range_update(l, r, val, 2*node+1, start, mid)
    self.range_update(l, r, val, 2*node+2, mid+1, end)
    self.tree[node] = self.tree[2*node+1] + self.tree[2*node+2]
```

---

## 树状数组

### 特点

- 实现简单，常数小
- 单点更新：O(log n)
- 前缀查询：O(log n)
- 不如线段树灵活

### 实现

```python
class BinaryIndexedTree:
    def __init__(self, n):
        self.n = n
        self.tree = [0] * (n + 1)
    
    def lowbit(self, x):
        return x & (-x)
    
    def update(self, i, delta):
        while i <= self.n:
            self.tree[i] += delta
            i += self.lowbit(i)
    
    def query(self, i):
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= self.lowbit(i)
        return total
    
    def range_query(self, l, r):
        return self.query(r) - self.query(l - 1)
```

### 应用

- 区间和查询
- 逆序对计数
- 动态排名

---

## 字典树（Trie）

### 特点

- 前缀匹配：O(m)，m为字符串长度
- 空间换时间
- 适合字符串集合

### 实现

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
    
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
```

### 应用

- 自动补全
- 拼写检查
- IP路由
- 词频统计

---

## 并查集

### 特点

- 集合合并：O(α(n)) ≈ O(1)
- 集合查询：O(α(n)) ≈ O(1)

### 实现

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.count = n
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # 路径压缩
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        
        # 按秩合并
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        
        self.count -= 1
        return True
    
    def connected(self, x, y):
        return self.find(x) == self.find(y)
```

### 应用

- 连通分量
- 最小生成树
- 判断环
- 动态连通性

---

## 跳表

### 特点

- 有序链表的加速结构
- 期望O(log n)的查找、插入、删除
- 实现比红黑树简单
- Redis有序集合使用跳表

### 结构

```
Level 3:  1 ----------------> 9
Level 2:  1 -----> 4 -------> 9
Level 1:  1 -> 3 -> 4 -> 6 -> 9
Level 0:  1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9
```

### 实现

```python
import random

class SkipListNode:
    def __init__(self, val, level):
        self.val = val
        self.forward = [None] * level

class SkipList:
    def __init__(self, max_level=16, p=0.5):
        self.max_level = max_level
        self.p = p
        self.level = 1
        self.head = SkipListNode(float('-inf'), max_level)
    
    def random_level(self):
        level = 1
        while random.random() < self.p and level < self.max_level:
            level += 1
        return level
    
    def search(self, target):
        curr = self.head
        for i in range(self.level - 1, -1, -1):
            while curr.forward[i] and curr.forward[i].val < target:
                curr = curr.forward[i]
        curr = curr.forward[0]
        return curr and curr.val == target
    
    def insert(self, val):
        update = [None] * self.max_level
        curr = self.head
        
        for i in range(self.level - 1, -1, -1):
            while curr.forward[i] and curr.forward[i].val < val:
                curr = curr.forward[i]
            update[i] = curr
        
        level = self.random_level()
        if level > self.level:
            for i in range(self.level, level):
                update[i] = self.head
            self.level = level
        
        new_node = SkipListNode(val, level)
        for i in range(level):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
```

---

## 布隆过滤器

### 特点

- 空间效率高
- 判断元素是否**可能存在**
- 有假阳性，无假阴性
- 不支持删除

### 实现

```python
import mmh3
from bitarray import bitarray

class BloomFilter:
    def __init__(self, size, hash_count):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)
    
    def add(self, item):
        for i in range(self.hash_count):
            index = mmh3.hash(item, i) % self.size
            self.bit_array[index] = 1
    
    def contains(self, item):
        for i in range(self.hash_count):
            index = mmh3.hash(item, i) % self.size
            if not self.bit_array[index]:
                return False
        return True
```

### 应用

- 缓存穿透防护
- 垃圾邮件过滤
- URL去重
- 推荐系统去重

---

## LRU缓存

### 实现

```python
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}  # key -> node
        self.head = DLinkedNode()  # 哑头
        self.tail = DLinkedNode()  # 哑尾
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def get(self, key):
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self.move_to_head(node)
        return node.val
    
    def put(self, key, val):
        if key in self.cache:
            node = self.cache[key]
            node.val = val
            self.move_to_head(node)
        else:
            if len(self.cache) >= self.capacity:
                tail = self.remove_tail()
                del self.cache[tail.key]
            node = DLinkedNode(key, val)
            self.cache[key] = node
            self.add_to_head(node)
```

---

## 总结

| 数据结构 | 操作复杂度 | 应用 |
|----------|------------|------|
| 线段树 | O(log n) | 区间查询/更新 |
| 树状数组 | O(log n) | 前缀和、逆序对 |
| 字典树 | O(m) | 前缀匹配 |
| 并查集 | O(α(n)) | 连通性 |
| 跳表 | O(log n) | 有序集合 |
| 布隆过滤器 | O(k) | 存在性判断 |
| LRU缓存 | O(1) | 缓存淘汰 |

这些高级数据结构在特定场景下可以大幅提升性能。
