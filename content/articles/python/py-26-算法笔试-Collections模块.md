+++
title = "26.算法笔试-Collections模块"
date = 2026-01-21
description = "Python3算法笔试必备：Counter、defaultdict、deque、OrderedDict详解"
[taxonomies]
tags = ["Python", "算法", "笔试", "collections", "面试"]
+++

## 概述

`collections`模块提供了高效的专用容器数据类型，是算法笔试中的利器。本文详细介绍最常用的Counter、defaultdict、deque、OrderedDict。

```python
from collections import Counter, defaultdict, deque, OrderedDict, namedtuple
```

---

# 一、Counter计数器

## 1.1 基础用法

```python
from collections import Counter

# 创建Counter
c = Counter()                         # 空计数器
c = Counter([1, 2, 2, 3, 3, 3])       # 从列表创建
c = Counter("hello")                   # 从字符串创建
c = Counter({'a': 4, 'b': 2})          # 从字典创建
c = Counter(a=4, b=2)                  # 关键字参数

print(c)  # Counter({'l': 2, 'h': 1, 'e': 1, 'o': 1})

# 访问计数
c['l']            # 2
c['z']            # 0（不存在返回0，不报错！）

# 设置计数
c['l'] = 10
c['z'] = 5        # 可以添加新元素

# 删除元素
del c['z']
```

## 1.2 常用方法

```python
c = Counter("abracadabra")

# 获取最常见的n个元素
c.most_common()       # [('a', 5), ('b', 2), ('r', 2), ('c', 1), ('d', 1)]
c.most_common(2)      # [('a', 5), ('b', 2)] 前2个

# 获取所有元素（按计数重复）
list(c.elements())    # ['a', 'a', 'a', 'a', 'a', 'b', 'b', 'r', 'r', 'c', 'd']

# 总计数
sum(c.values())       # 11
c.total()             # Python 3.10+ 等价于sum(c.values())

# 获取唯一元素
list(c.keys())        # ['a', 'b', 'r', 'c', 'd']
len(c)                # 5 唯一元素个数

# 更新计数
c.update("aaa")       # 增加计数
c.update({'a': 10})   # 增加计数
c.subtract("aaa")     # 减少计数

# 清空
c.clear()
```

## 1.3 Counter运算

```python
c1 = Counter(a=3, b=1)
c2 = Counter(a=1, b=2)

# 加法（合并计数）
c1 + c2               # Counter({'a': 4, 'b': 3})

# 减法（差集，只保留正数）
c1 - c2               # Counter({'a': 2})

# 交集（取最小值）
c1 & c2               # Counter({'a': 1, 'b': 1})

# 并集（取最大值）
c1 | c2               # Counter({'a': 3, 'b': 2})

# 正数计数
+c1                   # Counter({'a': 3, 'b': 1}) 去掉0和负数
-c1                   # Counter() 去掉正数，保留负数的绝对值

# 相等判断
Counter('aab') == Counter('aba')  # True
```

## 1.4 算法题应用

```python
# 1. 判断异位词
def is_anagram(s1: str, s2: str) -> bool:
    return Counter(s1) == Counter(s2)

# 2. 找出出现次数最多的元素
def most_frequent(arr):
    return Counter(arr).most_common(1)[0][0]

# 3. 找出只出现一次的元素
def find_unique(arr):
    c = Counter(arr)
    return [x for x in arr if c[x] == 1]

# 4. 判断能否由另一个字符串构成
def can_construct(ransomNote: str, magazine: str) -> bool:
    return not (Counter(ransomNote) - Counter(magazine))
    # 如果差集为空，说明magazine包含所有需要的字符

# 5. 滑动窗口中的字符计数
def find_anagrams(s: str, p: str):
    """找出s中所有p的异位词起始位置"""
    result = []
    p_count = Counter(p)
    s_count = Counter()
    
    for i, char in enumerate(s):
        s_count[char] += 1
        if i >= len(p):
            left = s[i - len(p)]
            s_count[left] -= 1
            if s_count[left] == 0:
                del s_count[left]
        
        if s_count == p_count:
            result.append(i - len(p) + 1)
    
    return result

# 6. Top K 频繁元素
def top_k_frequent(nums, k):
    return [x for x, _ in Counter(nums).most_common(k)]

# 7. 最少删除使频率相同
def min_deletions(s: str) -> int:
    freq = Counter(Counter(s).values())  # 频率的频率
    deletions = 0
    used = set()
    for count in sorted(Counter(s).values(), reverse=True):
        while count > 0 and count in used:
            count -= 1
            deletions += 1
        used.add(count)
    return deletions
```

---

# 二、defaultdict默认字典

## 2.1 基础用法

```python
from collections import defaultdict

# 创建defaultdict，参数是默认值的工厂函数
d = defaultdict(int)      # 默认值0
d = defaultdict(list)     # 默认值[]
d = defaultdict(set)      # 默认值set()
d = defaultdict(str)      # 默认值''
d = defaultdict(lambda: 'default')  # 自定义默认值

# 使用
d = defaultdict(int)
d['a'] += 1               # 不需要先检查是否存在
d['b'] += 2
print(d)                  # defaultdict(<class 'int'>, {'a': 1, 'b': 2})

# 对比普通dict
normal_dict = {}
# normal_dict['a'] += 1   # KeyError!
normal_dict['a'] = normal_dict.get('a', 0) + 1  # 需要这样写
```

## 2.2 常见用法

```python
# 1. 计数（等价于Counter）
count = defaultdict(int)
for item in items:
    count[item] += 1

# 2. 分组
groups = defaultdict(list)
for item in items:
    groups[item.category].append(item)

# 3. 集合操作
seen = defaultdict(set)
for u, v in edges:
    seen[u].add(v)
    seen[v].add(u)

# 4. 嵌套defaultdict
matrix = defaultdict(lambda: defaultdict(int))
matrix[0][0] = 1
matrix[1][2] = 5
# 访问不存在的键不会报错
print(matrix[99][99])  # 0

# 5. 邻接表（图）
graph = defaultdict(list)
for u, v in edges:
    graph[u].append(v)
    graph[v].append(u)  # 无向图
```

## 2.3 算法题应用

```python
# 1. 字母异位词分组
def group_anagrams(strs):
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())

# 2. 图的表示
def build_graph(edges):
    graph = defaultdict(list)
    for u, v, weight in edges:
        graph[u].append((v, weight))
        graph[v].append((u, weight))
    return graph

# 3. 拓扑排序
def topological_sort(n, edges):
    graph = defaultdict(list)
    indegree = defaultdict(int)
    
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1
    
    queue = deque([i for i in range(n) if indegree[i] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    
    return result if len(result) == n else []

# 4. 单词阶梯
def ladder_length(begin, end, word_list):
    # 预处理：构建通配符到单词的映射
    patterns = defaultdict(list)
    for word in word_list:
        for i in range(len(word)):
            pattern = word[:i] + '*' + word[i+1:]
            patterns[pattern].append(word)
    
    # BFS
    queue = deque([(begin, 1)])
    visited = {begin}
    
    while queue:
        word, length = queue.popleft()
        if word == end:
            return length
        
        for i in range(len(word)):
            pattern = word[:i] + '*' + word[i+1:]
            for next_word in patterns[pattern]:
                if next_word not in visited:
                    visited.add(next_word)
                    queue.append((next_word, length + 1))
    
    return 0
```

---

# 三、deque双端队列

## 3.1 基础操作

```python
from collections import deque

# 创建
d = deque()                      # 空队列
d = deque([1, 2, 3])             # 从列表创建
d = deque([1, 2, 3], maxlen=5)   # 限制最大长度

# 添加元素
d.append(4)           # 右端添加 O(1)
d.appendleft(0)       # 左端添加 O(1)
d.extend([5, 6])      # 右端扩展
d.extendleft([−1])    # 左端扩展（注意顺序会反转）

# 弹出元素
d.pop()               # 右端弹出 O(1)
d.popleft()           # 左端弹出 O(1)  ← 这是deque相比list的优势！

# 访问元素
d[0]                  # 左端元素 O(1)
d[-1]                 # 右端元素 O(1)
d[5]                  # 中间元素 O(n)（慢！）
```

## 3.2 常用方法

```python
d = deque([1, 2, 3, 4, 5])

# 旋转
d.rotate(2)           # 右旋转 [4, 5, 1, 2, 3]
d.rotate(-2)          # 左旋转 [1, 2, 3, 4, 5]

# 反转
d.reverse()           # 原地反转

# 计数
d.count(3)            # 统计3出现次数

# 查找
d.index(3)            # 返回3的索引

# 删除
d.remove(3)           # 删除第一个3

# 清空
d.clear()

# 复制
d2 = d.copy()
```

## 3.3 maxlen限制

```python
# 限制长度的deque，超出时自动删除另一端
d = deque(maxlen=3)
d.append(1)           # [1]
d.append(2)           # [1, 2]
d.append(3)           # [1, 2, 3]
d.append(4)           # [2, 3, 4]  自动删除左端

# 应用：保留最近N个元素
def last_n_lines(filename, n):
    return deque(open(filename), maxlen=n)

# 应用：滑动窗口最大值
def sliding_window_max(nums, k):
    result = []
    window = deque()  # 存储索引
    
    for i, num in enumerate(nums):
        # 移除超出窗口的元素
        while window and window[0] < i - k + 1:
            window.popleft()
        # 移除比当前元素小的元素（它们不可能成为最大值）
        while window and nums[window[-1]] < num:
            window.pop()
        window.append(i)
        
        if i >= k - 1:
            result.append(nums[window[0]])
    
    return result
```

## 3.4 算法题应用

```python
# 1. BFS广度优先搜索（最重要的应用！）
def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    
    while queue:
        node = queue.popleft()  # O(1) 这就是用deque的原因
        print(node)
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

# 2. 层序遍历二叉树
def level_order(root):
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        level = []
        for _ in range(len(queue)):  # 处理当前层
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    
    return result

# 3. 最短路径（BFS）
def shortest_path(graph, start, end):
    queue = deque([(start, 0)])  # (节点, 距离)
    visited = {start}
    
    while queue:
        node, dist = queue.popleft()
        if node == end:
            return dist
        
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    
    return -1

# 4. 滑动窗口最小值（单调队列）
def min_sliding_window(nums, k):
    result = []
    q = deque()  # 单调递增队列，存索引
    
    for i, num in enumerate(nums):
        # 移除超出窗口的
        while q and q[0] < i - k + 1:
            q.popleft()
        # 保持单调性
        while q and nums[q[-1]] >= num:
            q.pop()
        q.append(i)
        
        if i >= k - 1:
            result.append(nums[q[0]])
    
    return result

# 5. 双端BFS（优化）
def bidirectional_bfs(graph, start, end):
    if start == end:
        return 0
    
    front = {start}
    back = {end}
    visited = {start, end}
    dist = 0
    
    while front and back:
        dist += 1
        # 总是扩展较小的集合
        if len(front) > len(back):
            front, back = back, front
        
        next_front = set()
        for node in front:
            for neighbor in graph[node]:
                if neighbor in back:
                    return dist
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_front.add(neighbor)
        
        front = next_front
    
    return -1

# 6. 用deque实现栈和队列
# 栈：append + pop
# 队列：append + popleft
```

---

# 四、OrderedDict有序字典

## 4.1 基础用法

```python
from collections import OrderedDict

# 创建
od = OrderedDict()
od['a'] = 1
od['b'] = 2
od['c'] = 3

# 保持插入顺序（Python 3.7+ dict也保持顺序，但OrderedDict有额外方法）
list(od.keys())    # ['a', 'b', 'c']

# 移动元素到末尾
od.move_to_end('a')        # ['b', 'c', 'a']
od.move_to_end('a', last=False)  # 移到开头 ['a', 'b', 'c']

# 弹出元素
od.popitem(last=True)      # 弹出最后一个 ('c', 3)
od.popitem(last=False)     # 弹出第一个
```

## 4.2 LRU Cache实现

```python
class LRUCache:
    """最近最少使用缓存"""
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        # 移到末尾表示最近使用
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            # 弹出最久未使用的（第一个）
            self.cache.popitem(last=False)

# 使用示例
cache = LRUCache(2)
cache.put(1, 1)  # {1: 1}
cache.put(2, 2)  # {1: 1, 2: 2}
cache.get(1)     # 返回1，{2: 2, 1: 1}
cache.put(3, 3)  # 淘汰key=2，{1: 1, 3: 3}
cache.get(2)     # 返回-1
```

## 4.3 LFU Cache实现

```python
class LFUCache:
    """最不经常使用缓存"""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}  # key -> value
        self.freq = {}   # key -> frequency
        self.freq_to_keys = defaultdict(OrderedDict)  # freq -> OrderedDict of keys
        self.min_freq = 0
    
    def _update_freq(self, key):
        f = self.freq[key]
        self.freq[key] = f + 1
        del self.freq_to_keys[f][key]
        
        if not self.freq_to_keys[f]:
            del self.freq_to_keys[f]
            if self.min_freq == f:
                self.min_freq = f + 1
        
        self.freq_to_keys[f + 1][key] = None
    
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self._update_freq(key)
        return self.cache[key]
    
    def put(self, key: int, value: int) -> None:
        if self.capacity <= 0:
            return
        
        if key in self.cache:
            self.cache[key] = value
            self._update_freq(key)
            return
        
        if len(self.cache) >= self.capacity:
            # 淘汰最不常用的
            evict_key, _ = self.freq_to_keys[self.min_freq].popitem(last=False)
            del self.cache[evict_key]
            del self.freq[evict_key]
        
        self.cache[key] = value
        self.freq[key] = 1
        self.freq_to_keys[1][key] = None
        self.min_freq = 1
```

---

# 五、其他有用的collections类

## 5.1 namedtuple命名元组

```python
from collections import namedtuple

# 创建类型
Point = namedtuple('Point', ['x', 'y'])
Person = namedtuple('Person', 'name age city')

# 使用
p = Point(1, 2)
print(p.x, p.y)     # 1 2
print(p[0], p[1])   # 1 2

# 解包
x, y = p

# 转换
p._asdict()         # {'x': 1, 'y': 2}
p._replace(x=10)    # Point(x=10, y=2)

# 算法题中用于表示状态
State = namedtuple('State', ['position', 'steps', 'keys'])
```

## 5.2 ChainMap链式映射

```python
from collections import ChainMap

# 多个字典链式查找
defaults = {'color': 'red', 'size': 'medium'}
user = {'color': 'blue'}
combined = ChainMap(user, defaults)

combined['color']   # 'blue' (从user找到)
combined['size']    # 'medium' (从defaults找到)

# 用于配置覆盖
```

---

## 总结

### 模块速查

| 类型 | 用途 | 关键方法 |
|------|------|----------|
| Counter | 计数 | `most_common()`, `update()`, `subtract()` |
| defaultdict | 默认值字典 | 工厂函数: `int`, `list`, `set` |
| deque | 双端队列 | `append()`, `popleft()`, `rotate()` |
| OrderedDict | 有序字典 | `move_to_end()`, `popitem()` |
| namedtuple | 命名元组 | `_asdict()`, `_replace()` |

### 使用场景

| 场景 | 推荐 |
|------|------|
| 频率统计 | Counter |
| 分组/邻接表 | defaultdict(list) |
| BFS队列 | deque |
| LRU缓存 | OrderedDict |
| 滑动窗口 | deque(maxlen=k) |
| 单调栈/队列 | deque |

### 关键记忆

1. Counter可以直接比较：`Counter(s1) == Counter(s2)`
2. defaultdict访问不存在的键会创建默认值
3. deque.popleft()是O(1)，list.pop(0)是O(n)
4. OrderedDict.move_to_end()用于LRU
5. BFS一定用deque，不要用list
