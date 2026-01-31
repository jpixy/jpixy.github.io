+++
title = "03.树与图"
date = 2026-01-19
description = "树结构：二叉树、BST、AVL、红黑树；图算法：遍历、最短路径、拓扑排序"
[taxonomies]
tags = ["算法", "树", "图"]
+++

## 二叉树基础

### 遍历方式

| 方式 | 顺序 | 应用 |
|------|------|------|
| 前序 | 根-左-右 | 复制树 |
| 中序 | 左-根-右 | BST有序输出 |
| 后序 | 左-右-根 | 删除树 |
| 层序 | 逐层 | 广度优先 |

### 递归遍历

```python
def preorder(root):
    if not root:
        return
    visit(root)
    preorder(root.left)
    preorder(root.right)

def inorder(root):
    if not root:
        return
    inorder(root.left)
    visit(root)
    inorder(root.right)

def postorder(root):
    if not root:
        return
    postorder(root.left)
    postorder(root.right)
    visit(root)
```

### 迭代遍历

```python
# 前序
def preorder_iterative(root):
    if not root:
        return []
    result, stack = [], [root]
    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return result

# 中序
def inorder_iterative(root):
    result, stack = [], []
    curr = root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()
        result.append(curr.val)
        curr = curr.right
    return result
```

### 层序遍历

```python
from collections import deque

def level_order(root):
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result
```

---

## 二叉搜索树

### 性质

- 左子树所有节点 < 根节点
- 右子树所有节点 > 根节点
- 中序遍历有序

### 复杂度

| 操作 | 平均 | 最差 |
|------|------|------|
| 搜索 | O(log n) | O(n) |
| 插入 | O(log n) | O(n) |
| 删除 | O(log n) | O(n) |

### 搜索

```python
def search(root, target):
    if not root or root.val == target:
        return root
    if target < root.val:
        return search(root.left, target)
    return search(root.right, target)
```

### 插入

```python
def insert(root, val):
    if not root:
        return TreeNode(val)
    if val < root.val:
        root.left = insert(root.left, val)
    else:
        root.right = insert(root.right, val)
    return root
```

### 删除

```python
def delete(root, key):
    if not root:
        return None
    
    if key < root.val:
        root.left = delete(root.left, key)
    elif key > root.val:
        root.right = delete(root.right, key)
    else:
        # 叶节点或只有一个子节点
        if not root.left:
            return root.right
        if not root.right:
            return root.left
        # 两个子节点：用右子树最小值替换
        min_node = find_min(root.right)
        root.val = min_node.val
        root.right = delete(root.right, min_node.val)
    
    return root
```

---

## 平衡二叉树

### AVL树

- 任意节点左右子树高度差 ≤ 1
- 通过旋转维护平衡

**旋转**：
- 左旋：右子节点上升
- 右旋：左子节点上升
- 左右旋：先左旋后右旋
- 右左旋：先右旋后左旋

### 红黑树

**性质**：
1. 节点是红色或黑色
2. 根是黑色
3. 叶子（NIL）是黑色
4. 红色节点的子节点是黑色
5. 任意节点到叶子的黑色节点数相同

**优势**：插入删除调整次数少于AVL

---

## 图的表示

### 邻接矩阵

```python
# n个节点
graph = [[0] * n for _ in range(n)]
graph[u][v] = 1  # 边 u -> v
```

空间：O(V²)
适用：稠密图、需要快速判断边

### 邻接表

```python
from collections import defaultdict

graph = defaultdict(list)
graph[u].append(v)  # 边 u -> v
```

空间：O(V + E)
适用：稀疏图

---

## 图的遍历

### DFS

```python
def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    
    visited.add(start)
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited)
```

### BFS

```python
from collections import deque

def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
```

---

## 最短路径

### Dijkstra算法

适用：非负权重

```python
import heapq

def dijkstra(graph, start):
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    heap = [(0, start)]
    
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, weight in graph[u]:
            if dist[u] + weight < dist[v]:
                dist[v] = dist[u] + weight
                heapq.heappush(heap, (dist[v], v))
    
    return dist
```

复杂度：O((V+E) log V)

### Bellman-Ford算法

适用：有负权重，可检测负环

```python
def bellman_ford(n, edges, start):
    dist = [float('inf')] * n
    dist[start] = 0
    
    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    
    # 检测负环
    for u, v, w in edges:
        if dist[u] + w < dist[v]:
            return None  # 存在负环
    
    return dist
```

复杂度：O(VE)

### Floyd-Warshall算法

适用：所有点对最短路径

```python
def floyd_warshall(n, graph):
    dist = [[float('inf')] * n for _ in range(n)]
    
    for i in range(n):
        dist[i][i] = 0
    
    for u in graph:
        for v, w in graph[u]:
            dist[u][v] = w
    
    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    
    return dist
```

复杂度：O(V³)

---

## 拓扑排序

### 适用

有向无环图（DAG），如任务依赖、课程安排

### Kahn算法（BFS）

```python
from collections import deque

def topological_sort(n, edges):
    graph = defaultdict(list)
    indegree = [0] * n
    
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1
    
    queue = deque([i for i in range(n) if indegree[i] == 0])
    result = []
    
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    
    return result if len(result) == n else []  # 有环返回空
```

### DFS后序

```python
def topological_sort_dfs(n, graph):
    visited = [0] * n  # 0: 未访问, 1: 访问中, 2: 已完成
    result = []
    
    def dfs(u):
        if visited[u] == 1:
            return False  # 发现环
        if visited[u] == 2:
            return True
        
        visited[u] = 1
        for v in graph[u]:
            if not dfs(v):
                return False
        visited[u] = 2
        result.append(u)
        return True
    
    for i in range(n):
        if visited[i] == 0:
            if not dfs(i):
                return []
    
    return result[::-1]
```

---

## 最小生成树

### Kruskal算法

贪心选择最小边，用并查集检测环

```python
def kruskal(n, edges):
    edges.sort(key=lambda x: x[2])  # 按权重排序
    parent = list(range(n))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    mst = []
    for u, v, w in edges:
        pu, pv = find(u), find(v)
        if pu != pv:
            parent[pu] = pv
            mst.append((u, v, w))
            if len(mst) == n - 1:
                break
    
    return mst
```

### Prim算法

从一个点开始，每次选择最小的跨边

```python
def prim(n, graph):
    visited = [False] * n
    heap = [(0, 0)]  # (权重, 节点)
    total = 0
    
    while heap:
        w, u = heapq.heappop(heap)
        if visited[u]:
            continue
        visited[u] = True
        total += w
        for v, weight in graph[u]:
            if not visited[v]:
                heapq.heappush(heap, (weight, v))
    
    return total
```

---

## 总结

| 问题 | 算法 | 复杂度 |
|------|------|--------|
| 树遍历 | 递归/迭代 | O(n) |
| 最短路径（非负） | Dijkstra | O((V+E)logV) |
| 最短路径（负权） | Bellman-Ford | O(VE) |
| 所有点对最短路径 | Floyd-Warshall | O(V³) |
| 拓扑排序 | Kahn/DFS | O(V+E) |
| 最小生成树 | Kruskal/Prim | O(ElogE) |

---

## 相关文章

- [上一篇：排序与搜索](/articles/algorithm/algo-02-排序与搜索/)
- [下一篇：动态规划](/articles/algorithm/algo-04-动态规划/)
