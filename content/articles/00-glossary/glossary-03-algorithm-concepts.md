+++
title = "03.Algorithm & Data Structure Concepts"
description = "算法与数据结构核心概念速查：复杂度分析、常用数据结构、并发数据结构等关键概念详解"
date = 2026-01-26
draft = false
[taxonomies]
tags = ["Glossary", "Algorithm", "Data Structure", "Reference"]
+++

# Algorithm & Data Structure Concepts

本索引收录算法与数据结构的核心概念，重点关注高性能系统中常用的技术。

---

## 一、复杂度分析

### 1.1 Time Complexity (时间复杂度)

**定义**：描述算法运行时间随输入规模增长的变化趋势，使用大O符号表示上界。

**常见复杂度对比**：

| 复杂度 | 名称 | n=1000时 | 示例 |
|--------|------|----------|------|
| O(1) | 常数 | 1 | 哈希表查找 |
| O(log n) | 对数 | 10 | 二分查找 |
| O(n) | 线性 | 1000 | 遍历数组 |
| O(n log n) | 线性对数 | 10000 | 快速排序 |
| O(n²) | 平方 | 1000000 | 冒泡排序 |
| O(2ⁿ) | 指数 | 10^301 | 子集枚举 |

**实际运行时间估算**（假设每操作1ns）：
```
n = 10^6 时:
O(1):       1ns
O(log n):   20ns
O(n):       1ms
O(n log n): 20ms
O(n²):      16分钟
O(2^n):     宇宙年龄的10^301000倍
```

**HFT中的应用**：
- Order Book操作必须O(1)或O(log n)
- 禁止O(n²)算法
- 常数因子也很重要（缓存友好性）

---

### 1.2 Amortized Complexity (均摊复杂度)

**定义**：考虑一系列操作的平均时间，而非单次操作的最坏情况。

**典型例子**：std::vector的push_back
- 单次最坏：O(n)（需要扩容）
- 均摊：O(1)（扩容次数有限）

**分析方法**：
```
每次扩容2倍，n次push_back的总开销：
1 + 2 + 4 + 8 + ... + n/2 + n ≈ 2n

均摊每次操作：2n/n = O(1)
```

**HFT注意**：
- 均摊O(1)不意味着每次都是O(1)
- 扩容发生在不可预测的时刻
- 解决方案：预分配（reserve）

---

## 二、基础数据结构

### 2.1 Hash Table (哈希表)

**定义**：通过哈希函数将键映射到数组索引，实现O(1)平均时间的查找、插入、删除。

**冲突解决**：
1. **链表法**：每个槽位是链表
2. **开放寻址**：冲突时查找下一个空位
3. **Robin Hood**：优化开放寻址的探测距离

**性能关键**：
```cpp
// 好的哈希函数特性
// 1. 计算快
// 2. 分布均匀
// 3. 雪崩效应（输入小变化→输出大变化）

// 示例：用于整数键的高效哈希
inline size_t hash_int(uint64_t x) {
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}
```

**HFT中的应用**：
- Order ID → Order对象的映射
- Symbol → OrderBook的映射

---

### 2.2 Binary Search Tree (二叉搜索树)

**定义**：每个节点的左子树所有值小于节点值，右子树所有值大于节点值。

**平衡树变体**：

| 类型 | 查找 | 插入/删除 | 特点 |
|------|------|-----------|------|
| 普通BST | O(h) | O(h) | h可能是n |
| AVL | O(log n) | O(log n) | 严格平衡 |
| 红黑树 | O(log n) | O(log n) | std::map |
| B树 | O(log n) | O(log n) | 磁盘友好 |

**std::map底层**：
```cpp
// 红黑树实现，有序键值对
std::map<Price, OrderList> orderBook;

// 找到第一个>=price的价格
auto it = orderBook.lower_bound(price);

// 遍历有序
for (auto& [price, orders] : orderBook) {
    // 按价格顺序
}
```

---

### 2.3 Tree (树)

**定义**：由节点和边组成的层次结构，有且仅有一个根节点，每个非根节点有且仅有一个父节点。

**基本术语**：
- **根节点 (Root)**：树的顶层节点，无父节点
- **叶节点 (Leaf)**：无子节点的节点
- **深度 (Depth)**：从根到该节点的边数
- **高度 (Height)**：从该节点到最深叶节点的边数
- **度 (Degree)**：节点的子节点数量

**树的表示**：
```cpp
// 方法1：指针表示（适合稀疏树）
struct TreeNode {
    int val;
    vector<TreeNode*> children;
};

// 方法2：父节点数组（适合固定结构）
int parent[N];  // parent[i] = i的父节点

// 方法3：邻接表（通用图/树）
vector<int> adj[N];
```

**树的遍历**：
```cpp
// 深度优先遍历 - 递归
void dfs(TreeNode* node) {
    if (!node) return;
    // 处理当前节点
    for (auto child : node->children) {
        dfs(child);
    }
}

// 广度优先遍历 - 层序
void bfs(TreeNode* root) {
    queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        TreeNode* node = q.front(); q.pop();
        // 处理当前节点
        for (auto child : node->children) {
            q.push(child);
        }
    }
}
```

---

### 2.4 Binary Tree (二叉树)

**定义**：每个节点最多有两个子节点（左子节点和右子节点）的树结构。

**二叉树的类型**：

| 类型 | 定义 | 特点 |
|------|------|------|
| **满二叉树** | 每层节点数达到最大 | 节点数 = 2^h - 1 |
| **完全二叉树** | 除最后一层外全满，最后一层左对齐 | 适合数组存储 |
| **二叉搜索树** | 左 < 根 < 右 | 支持有序操作 |
| **平衡二叉树** | 左右子树高度差≤1 | 保证O(log n) |

**三种遍历**：
```cpp
struct TreeNode {
    int val;
    TreeNode *left, *right;
};

// 前序遍历：根 → 左 → 右
void preorder(TreeNode* root) {
    if (!root) return;
    visit(root);           // 先处理根
    preorder(root->left);
    preorder(root->right);
}

// 中序遍历：左 → 根 → 右（BST得到有序序列）
void inorder(TreeNode* root) {
    if (!root) return;
    inorder(root->left);
    visit(root);           // 中间处理根
    inorder(root->right);
}

// 后序遍历：左 → 右 → 根
void postorder(TreeNode* root) {
    if (!root) return;
    postorder(root->left);
    postorder(root->right);
    visit(root);           // 最后处理根
}
```

**非递归遍历（面试常考）**：
```cpp
// 中序遍历非递归版
vector<int> inorderIterative(TreeNode* root) {
    vector<int> result;
    stack<TreeNode*> s;
    TreeNode* curr = root;
    
    while (curr || !s.empty()) {
        // 一直向左走到底
        while (curr) {
            s.push(curr);
            curr = curr->left;
        }
        // 回溯
        curr = s.top(); s.pop();
        result.push_back(curr->val);
        // 转向右子树
        curr = curr->right;
    }
    return result;
}
```

**数组表示完全二叉树**：
```
对于索引i（从0开始）：
- 父节点：(i - 1) / 2
- 左子节点：2*i + 1
- 右子节点：2*i + 2

对于索引i（从1开始）：
- 父节点：i / 2
- 左子节点：2*i
- 右子节点：2*i + 1
```

---

### 2.5 Binary Search Tree (二叉搜索树)

**定义**：每个节点的左子树所有值小于节点值，右子树所有值大于节点值。

**核心性质**：
1. 中序遍历得到有序序列
2. 查找、插入、删除平均O(log n)，最坏O(n)
3. 不保证平衡，可能退化为链表

**基本操作**：
```cpp
// 查找
TreeNode* search(TreeNode* root, int val) {
    if (!root || root->val == val) return root;
    if (val < root->val)
        return search(root->left, val);
    return search(root->right, val);
}

// 插入
TreeNode* insert(TreeNode* root, int val) {
    if (!root) return new TreeNode(val);
    if (val < root->val)
        root->left = insert(root->left, val);
    else
        root->right = insert(root->right, val);
    return root;
}

// 删除（三种情况）
TreeNode* remove(TreeNode* root, int val) {
    if (!root) return nullptr;
    
    if (val < root->val) {
        root->left = remove(root->left, val);
    } else if (val > root->val) {
        root->right = remove(root->right, val);
    } else {
        // 找到要删除的节点
        if (!root->left) return root->right;   // 情况1：无左子树
        if (!root->right) return root->left;   // 情况2：无右子树
        
        // 情况3：有两个子节点，用后继替换
        TreeNode* successor = root->right;
        while (successor->left) 
            successor = successor->left;
        root->val = successor->val;
        root->right = remove(root->right, successor->val);
    }
    return root;
}
```

**为什么需要平衡**：
```
插入序列 [1, 2, 3, 4, 5] 会退化为链表：
    1
     \
      2
       \
        3
         \
          4
           \
            5
查找复杂度从 O(log n) 退化为 O(n)
```

---

### 2.6 AVL Tree (AVL树)

**定义**：最早的自平衡二叉搜索树，任意节点的左右子树高度差不超过1。

**平衡因子**：左子树高度 - 右子树高度，取值必须是 {-1, 0, 1}

**四种旋转操作**：
```
LL型（左左）- 右旋：
    z                y
   / \             /   \
  y   T4   →     x       z
 / \            / \     / \
x   T3        T1   T2  T3  T4
/\
T1 T2

RR型（右右）- 左旋：
  z                     y
 / \                  /   \
T1   y       →       z       x
    / \             / \     / \
   T2   x         T1   T2  T3  T4
       / \
      T3  T4

LR型（左右）- 先左旋后右旋
RL型（右左）- 先右旋后左旋
```

**复杂度**：
- 查找：O(log n)
- 插入：O(log n)，最多2次旋转
- 删除：O(log n)，可能O(log n)次旋转

**优缺点**：
- ✅ 严格平衡，查找效率最高
- ❌ 旋转操作频繁，写入开销大
- 适用于读多写少的场景

---

### 2.7 Red-Black Tree (红黑树)

**定义**：一种弱平衡的二叉搜索树，通过节点着色和旋转维护近似平衡。

**五大性质**：
1. 每个节点是红色或黑色
2. 根节点是黑色
3. 叶节点（NIL）是黑色
4. 红色节点的子节点必须是黑色（不能连续红）
5. 从任一节点到其叶节点的所有路径包含相同数量的黑色节点

**为什么这五条性质保证平衡**：
```
由性质4和5可推导：
- 最长路径（红黑交替）最多是最短路径（全黑）的2倍
- 树高度最多是 2*log(n+1)
- 保证了 O(log n) 的操作复杂度
```

**与AVL对比**：

| 特性 | AVL树 | 红黑树 |
|------|-------|--------|
| 平衡程度 | 严格（高度差≤1）| 宽松（最长≤2*最短）|
| 查找效率 | 略优 | 略低 |
| 插入旋转 | 最多2次 | 最多2次 |
| 删除旋转 | O(log n)次 | 最多3次 |
| 适用场景 | 读多写少 | 写操作频繁 |

**标准库实现**：
```cpp
// C++ STL中的std::map和std::set底层使用红黑树
std::map<int, string> m;    // 红黑树
std::set<int> s;            // 红黑树

// Java中的TreeMap、TreeSet也是红黑树
// Linux内核的进程调度CFS使用红黑树
```

**HFT应用**：
- Order Book按价格排序存储
- 需要快速的插入/删除/范围查询

---

### 2.8 B-Tree (B树)

**定义**：一种多路平衡搜索树，专为磁盘等外部存储设计，减少I/O次数。

**特点**（m阶B树）：
1. 每个节点最多有m个子节点
2. 非根节点至少有⌈m/2⌉个子节点
3. 根节点至少有2个子节点（除非是叶子）
4. 有k个子节点的节点包含k-1个键
5. 所有叶节点在同一层

**结构示例（3阶B树）**：
```
                [30]
              /      \
         [10,20]    [40,50]
        /  |  \     /  |  \
       5  15  25  35  45  55
```

**为什么适合磁盘**：
```
磁盘I/O特点：
- 寻道时间 ~10ms（非常慢）
- 顺序读取快
- 以块(Block)为单位读取（通常4KB）

B树优化：
- 节点大小 = 磁盘块大小
- 一次I/O读取整个节点
- 树高度低（logₘn），I/O次数少

对比二叉树（100万节点）：
- 二叉树高度：~20 → 20次I/O
- B树(m=100)高度：~3 → 3次I/O
```

**B+树**（数据库常用变体）：
```
与B树的区别：
1. 所有数据存储在叶节点
2. 叶节点通过指针连接成链表
3. 内部节点仅存储索引

优势：
- 范围查询高效（顺序遍历叶节点）
- 内部节点更小，可存更多索引
- MySQL InnoDB、PostgreSQL都使用B+树
```

**复杂度**：
- 查找：O(logₘ n)
- 插入：O(logₘ n)
- 删除：O(logₘ n)

---

### 2.9 B+ Tree (B+树)

**定义**：B树的变体，所有数据存储在叶节点，内部节点仅存索引，叶节点通过链表连接。

**与B树的关键区别**：

| 特性 | B树 | B+树 |
|------|-----|------|
| 数据存储 | 所有节点 | 仅叶节点 |
| 叶节点连接 | 无 | 双向链表 |
| 内部节点 | 存数据+索引 | 仅存索引 |
| 范围查询 | 需回溯 | 顺序遍历叶节点 |
| 内部节点扇出 | 较低 | 更高 |

**结构示例**：
```
           [30 | 60]                 ← 内部节点（仅索引）
          /    |    \
    [10|20] [40|50] [70|80]          ← 内部节点
      /|\     /|\     /|\
     叶节点...叶节点...叶节点
     ←→ ←→ ←→ ←→ ←→ ←→             ← 叶节点形成链表
```

**为什么数据库选择B+树**：

```
1. 范围查询高效
   SELECT * FROM users WHERE age BETWEEN 20 AND 30;
   → 定位到age=20的叶节点，沿链表扫描到age=30

2. 磁盘I/O优化
   - 内部节点不存数据 → 可存更多索引 → 树更矮
   - 例：4KB页，索引8字节，B+树可存500个索引
   - B树需要存完整数据，假设100字节，只能存40个

3. 全表扫描友好
   - 只需遍历叶节点链表，无需访问内部节点

4. 稳定的查询性能
   - 所有查询都需要到叶节点，路径长度一致
```

**MySQL InnoDB实现**：
```
主键索引（聚簇索引）：
- 叶节点存储完整行数据
- 按主键顺序组织

二级索引：
- 叶节点存储主键值
- 需要回表查询完整数据

索引页大小：16KB
树高度估算：
- 假设每条记录1KB，每页16条
- 假设索引8字节+指针8字节，内部节点约1000扇出
- 3层B+树可存储：1000 × 1000 × 16 = 1600万条记录
```

**使用场景**：
- ✅ 关系型数据库索引（MySQL、PostgreSQL）
- ✅ 文件系统（NTFS、ext4的目录）
- ✅ 需要频繁范围查询的场景
- ✅ 磁盘/SSD存储

---

### 2.10 树结构对比与选型

**完整对比表**：

| 数据结构 | 查找 | 插入 | 删除 | 有序遍历 | 内存/磁盘 | 适用场景 |
|----------|------|------|------|----------|-----------|----------|
| 数组 | O(n)/O(1) | O(n) | O(n) | O(n) | 内存 | 小规模、随机访问 |
| 哈希表 | O(1)* | O(1)* | O(1)* | O(n log n) | 内存 | 精确查找，无需有序 |
| BST | O(n)** | O(n)** | O(n)** | O(n) | 内存 | 教学用途 |
| AVL树 | O(log n) | O(log n) | O(log n) | O(n) | 内存 | 读多写少 |
| 红黑树 | O(log n) | O(log n) | O(log n) | O(n) | 内存 | 通用，写操作频繁 |
| 跳表 | O(log n)* | O(log n)* | O(log n)* | O(n) | 内存 | 并发场景、实现简单 |
| B树 | O(log n) | O(log n) | O(log n) | O(n) | 磁盘 | 数据库、少量范围查询 |
| B+树 | O(log n) | O(log n) | O(log n) | O(n) | 磁盘 | 数据库索引、范围查询 |

*平均情况 **最坏情况（退化为链表）

**如何选择**：

```
需要精确查找，无需排序？
  → 哈希表（O(1)无敌）

需要有序操作（范围查询、有序遍历）？
  ├── 数据在内存中？
  │     ├── 读多写少 → AVL树
  │     ├── 读写均衡 → 红黑树（std::map）
  │     └── 需要并发 → 跳表（lock-free更容易）
  └── 数据在磁盘上？
        ├── 主要点查询 → B树
        └── 范围查询多 → B+树

HFT场景：
  → 通常用哈希表（O(1)查找）
  → Order Book用红黑树/跳表（需要价格排序）
```

**各结构的实际应用**：

| 数据结构 | 实际应用 |
|----------|----------|
| 红黑树 | C++ std::map/set, Java TreeMap, Linux CFS调度器 |
| AVL树 | Windows内核、部分数据库 |
| 跳表 | Redis有序集合(ZSET), LevelDB/RocksDB |
| B+树 | MySQL InnoDB, PostgreSQL, SQLite |
| B树 | MongoDB, 某些文件系统 |

**性能实测参考**（100万元素，单线程）：

```
操作类型        std::map    std::unordered_map    跳表
随机插入        180ms       80ms                  200ms
随机查找        150ms       40ms                  170ms
范围查询[a,b]   5ms         不支持                8ms
有序遍历        20ms        排序后150ms           25ms
内存占用        ~64MB       ~80MB                 ~80MB
```

---

### 2.11 Heap (堆)

**定义**：完全二叉树，父节点总是大于（或小于）子节点。支持O(log n)插入和O(1)查找最大/最小值。

**操作复杂度**：
- 查找最大/小：O(1)
- 插入：O(log n)
- 删除最大/小：O(log n)
- 构建堆：O(n)

**应用**：
```cpp
// 优先队列
std::priority_queue<int> maxHeap;
std::priority_queue<int, vector<int>, greater<int>> minHeap;

// Top-K问题
// 找最大的K个数：维护大小为K的小顶堆
```

---

## 三、高性能数据结构

### 3.1 Lock-Free Queue (无锁队列)

**定义**：不使用互斥锁，通过原子操作实现线程安全的队列。

**SPSC队列**（单生产者单消费者）：
```cpp
template<typename T, size_t Size>
class SPSCQueue {
    static_assert((Size & (Size-1)) == 0);  // 2的幂
    
    alignas(64) std::atomic<size_t> head_{0};  // 消费者
    alignas(64) std::atomic<size_t> tail_{0};  // 生产者
    T buffer_[Size];
    
public:
    bool push(const T& item) {
        size_t tail = tail_.load(std::memory_order_relaxed);
        size_t next = (tail + 1) & (Size - 1);
        if (next == head_.load(std::memory_order_acquire))
            return false;  // 满
        buffer_[tail] = item;
        tail_.store(next, std::memory_order_release);
        return true;
    }
    
    bool pop(T& item) {
        size_t head = head_.load(std::memory_order_relaxed);
        if (head == tail_.load(std::memory_order_acquire))
            return false;  // 空
        item = buffer_[head];
        head_.store((head + 1) & (Size - 1), std::memory_order_release);
        return true;
    }
};
```

**关键点**：
- `alignas(64)`防止false sharing
- 正确的内存序保证可见性
- 2的幂大小用位与替代取模

**详细文章**：[HFT-Lock-Free数据结构详解](/articles/ccpp/cpp-22-HFT-Lock-Free数据结构详解/)

---

### 3.2 Skip List (跳表)

**定义**：多层链表，每层是下层的"快速通道"，提供O(log n)查找。

**结构**：
```
Level 3:  1 ─────────────────→ 9
Level 2:  1 ────→ 4 ─────────→ 9
Level 1:  1 ─→ 3 → 4 ─→ 6 ───→ 9
Level 0:  1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
```

**优势**：
- 实现比红黑树简单
- 范围查询友好
- 易于并发实现

**Redis的有序集合就使用跳表**

---

### 3.3 Bloom Filter (布隆过滤器)

**定义**：空间高效的概率数据结构，用于判断元素是否"可能在集合中"或"一定不在集合中"。

**特点**：
- **假阳性**：可能误报存在
- **无假阴性**：如果报不存在，一定不存在
- **不支持删除**

**工作原理**：
```
插入: 用k个哈希函数计算k个位置，置1
查询: 检查k个位置是否都是1

m位，n个元素，k个哈希函数
假阳性率 ≈ (1 - e^(-kn/m))^k
```

**应用**：
- 缓存穿透防护
- 去重
- HFT中：快速判断订单ID是否可能存在

```cpp
class BloomFilter {
    std::vector<bool> bits_;
    size_t num_hashes_;
    
public:
    void insert(uint64_t key) {
        for (size_t i = 0; i < num_hashes_; i++) {
            size_t idx = hash(key, i) % bits_.size();
            bits_[idx] = true;
        }
    }
    
    bool maybe_contains(uint64_t key) {
        for (size_t i = 0; i < num_hashes_; i++) {
            size_t idx = hash(key, i) % bits_.size();
            if (!bits_[idx]) return false;
        }
        return true;  // 可能存在
    }
};
```

**详细文章**：[概率数据结构详解(HFT)](/articles/algorithm/algo-09-概率数据结构详解/)

---

### 3.4 Ring Buffer (环形缓冲区)

**定义**：固定大小的缓冲区，读写指针循环移动，无需移动数据。

**优势**：
- O(1)读写
- 无内存分配
- 缓存友好

**实现要点**：
```cpp
template<typename T, size_t N>
class RingBuffer {
    T data_[N];
    size_t head_ = 0;  // 下一个读取位置
    size_t tail_ = 0;  // 下一个写入位置
    
public:
    bool push(const T& item) {
        size_t next = (tail_ + 1) % N;
        if (next == head_) return false;  // 满
        data_[tail_] = item;
        tail_ = next;
        return true;
    }
    
    bool pop(T& item) {
        if (head_ == tail_) return false;  // 空
        item = data_[head_];
        head_ = (head_ + 1) % N;
        return true;
    }
};
```

---

### 3.5 Intrusive Data Structures (侵入式数据结构)

**定义**：将链表/树节点信息嵌入到数据对象本身，而非在外部容器中分配节点。

**为什么HFT使用侵入式结构**：
- 消除外部节点分配：无malloc开销
- 更好的缓存局部性：数据和链接信息在一起
- 对象可同时在多个容器中

**非侵入式 vs 侵入式**：
```cpp
// 非侵入式：std::list
std::list<Order> orders;
// list内部为每个元素分配节点：
// struct Node { Order data; Node* prev; Node* next; }
// 两次内存访问：Node → data

// 侵入式：节点信息在Order内部
struct Order {
    int id;
    double price;
    Order* prev;  // 链表指针内嵌
    Order* next;
};
// 一次内存访问直接获取数据
```

**HFT中的实现**：
```cpp
// 侵入式双向链表节点
template<typename T>
struct IntrusiveListNode {
    T* prev = nullptr;
    T* next = nullptr;
};

// Order继承节点
struct Order : IntrusiveListNode<Order> {
    uint64_t orderId;
    double price;
    int quantity;
};

// 侵入式链表
template<typename T>
class IntrusiveList {
    T* head_ = nullptr;
    T* tail_ = nullptr;
    
public:
    void push_back(T* node) {
        node->next = nullptr;
        node->prev = tail_;
        if (tail_) tail_->next = node;
        else head_ = node;
        tail_ = node;
    }
    
    void remove(T* node) {
        if (node->prev) node->prev->next = node->next;
        else head_ = node->next;
        if (node->next) node->next->prev = node->prev;
        else tail_ = node->prev;
    }
};

// 使用：对象池 + 侵入式链表 = 零分配
ObjectPool<Order> pool;
IntrusiveList<Order> orderList;

Order* order = pool.alloc();
orderList.push_back(order);
```

**详细文章**：[OrderBook实现详解](/articles/hft/hft-13-OrderBook实现详解/)

---

### 3.6 Object Pool (对象池)

**定义**：预分配固定数量的对象，需要时取出，不需要时归还，避免运行时内存分配。

**为什么HFT必须使用**：
- malloc延迟不确定（100ns - 100μs）
- 可能触发系统调用（mmap/sbrk）
- 内存碎片导致性能下降

**实现**：
```cpp
template<typename T, size_t PoolSize = 10000>
class ObjectPool {
    union Slot {
        T object;
        Slot* next;
        
        Slot() {}
        ~Slot() {}
    };
    
    alignas(T) char storage_[sizeof(Slot) * PoolSize];
    Slot* freeList_{nullptr};
    
public:
    ObjectPool() {
        // 构建空闲链表
        for (size_t i = 0; i < PoolSize; ++i) {
            Slot* slot = reinterpret_cast<Slot*>(&storage_[sizeof(Slot) * i]);
            slot->next = freeList_;
            freeList_ = slot;
        }
    }
    
    template<typename... Args>
    T* alloc(Args&&... args) {
        if (!freeList_) return nullptr;  // 池耗尽
        
        Slot* slot = freeList_;
        freeList_ = slot->next;
        
        // placement new构造对象
        return new (&slot->object) T(std::forward<Args>(args)...);
    }
    
    void free(T* ptr) {
        ptr->~T();  // 调用析构函数
        Slot* slot = reinterpret_cast<Slot*>(ptr);
        slot->next = freeList_;
        freeList_ = slot;
    }
};

// 使用
ObjectPool<Order> orderPool;
Order* order = orderPool.alloc(orderId, price, qty);
// ... 使用order ...
orderPool.free(order);
```

**详细文章**：[HFT自定义内存分配器设计](/articles/ccpp/cpp-20-HFT自定义内存分配器设计/)

---

### 3.7 LRU Cache (最近最少使用缓存)

**定义**：容量有限的缓存，当满时淘汰最近最少使用的元素。核心操作（get/put）都是O(1)。

**为什么重要**：
- 面试高频题目
- 操作系统页面置换
- 数据库Buffer Pool
- Web缓存

**实现：哈希表 + 双向链表**：
```
哈希表：O(1) 查找
双向链表：O(1) 移动/删除
    
     head ←→ node1 ←→ node2 ←→ node3 ←→ tail
              ↑                    ↑
         最近使用               最少使用（将被淘汰）
```

**C++实现**：
```cpp
class LRUCache {
    int capacity_;
    std::list<std::pair<int, int>> cache_;  // {key, value}
    std::unordered_map<int, std::list<std::pair<int, int>>::iterator> map_;
    
public:
    LRUCache(int capacity) : capacity_(capacity) {}
    
    int get(int key) {
        auto it = map_.find(key);
        if (it == map_.end()) return -1;
        
        // 移到链表头部（最近使用）
        cache_.splice(cache_.begin(), cache_, it->second);
        return it->second->second;
    }
    
    void put(int key, int value) {
        auto it = map_.find(key);
        if (it != map_.end()) {
            // 更新值并移到头部
            it->second->second = value;
            cache_.splice(cache_.begin(), cache_, it->second);
            return;
        }
        
        // 容量满，淘汰尾部
        if (cache_.size() == capacity_) {
            map_.erase(cache_.back().first);
            cache_.pop_back();
        }
        
        // 插入头部
        cache_.emplace_front(key, value);
        map_[key] = cache_.begin();
    }
};
```

**HFT应用**：
- Order缓存（最近活跃订单）
- 符号信息缓存
- 计算结果缓存

---

### 3.8 Space Complexity (空间复杂度)

**定义**：算法执行过程中所需额外内存空间随输入规模增长的变化趋势。

**与时间复杂度类似的分析**：
```
O(1)：常数空间，如原地排序
O(n)：线性空间，如复制数组
O(n²)：平方空间，如二维DP表
O(log n)：对数空间，如递归调用栈（平衡树）
```

**空间优化技巧**：
```cpp
// 原始：O(n)空间的DP
int fib_original(int n) {
    vector<int> dp(n + 1);
    dp[0] = 0; dp[1] = 1;
    for (int i = 2; i <= n; i++)
        dp[i] = dp[i-1] + dp[i-2];
    return dp[n];
}

// 优化：O(1)空间
int fib_optimized(int n) {
    if (n <= 1) return n;
    int prev2 = 0, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        int curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}
```

**HFT空间考量**：
- 内存带宽是瓶颈
- 更少内存 = 更好的缓存命中
- 预分配固定大小避免碎片

---

## 四、并发原语

### 4.1 CAS (Compare-And-Swap)

**定义**：原子操作，比较内存值与期望值，相等则更新为新值。

**伪代码**：
```
CAS(addr, expected, desired):
    原子地执行:
        if *addr == expected:
            *addr = desired
            return true
        else:
            expected = *addr
            return false
```

**C++实现**：
```cpp
std::atomic<int> value{0};

int expected = 0;
bool success = value.compare_exchange_strong(expected, 1);
// 如果value==0，设为1，返回true
// 否则，expected被更新为当前值，返回false
```

**应用**：无锁数据结构的基础操作

---

### 4.2 ABA Problem (ABA问题)

**定义**：CAS操作的陷阱——值从A变为B再变回A，CAS检测不到中间的变化。

**问题场景**：
```
线程1: 读取head=A，准备CAS
        (被抢占)
线程2: pop A, push B, pop B, push A
线程1: CAS成功（head仍是A），但A已经是新的A！
```

**解决方案**：

1. **Tagged Pointer（带版本号的指针）**
```cpp
struct TaggedPtr {
    Node* ptr;
    uint32_t tag;  // 每次修改递增
};
std::atomic<TaggedPtr> head;
```

2. **Hazard Pointer**：跟踪正在使用的指针

3. **RCU (Read-Copy-Update)**：延迟回收

**详细文章**：[HFT-Lock-Free数据结构详解](/articles/ccpp/cpp-22-HFT-Lock-Free数据结构详解/)

---

### 4.3 Memory Fence (内存屏障)

**定义**：阻止编译器和CPU重排序内存操作的指令。

**类型**：
- **Load Fence**：之前的读操作完成后，才执行之后的读
- **Store Fence**：之前的写操作完成后，才执行之后的写
- **Full Fence**：同时限制读和写

**C++内存序**：
```cpp
// acquire: 之后的读写不能重排到这之前
x.load(std::memory_order_acquire);

// release: 之前的读写不能重排到这之后
x.store(1, std::memory_order_release);

// seq_cst: 全局顺序一致（最强，最慢）
x.store(1, std::memory_order_seq_cst);
```

---

## 五、常用算法

### 5.1 Binary Search (二分查找)

**定义**：在有序数组中，通过比较中间元素不断缩小搜索范围。

**复杂度**：O(log n)

**实现变体**：
```cpp
// 找到第一个>=target的位置（lower_bound）
int lower_bound(vector<int>& arr, int target) {
    int lo = 0, hi = arr.size();
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] < target)
            lo = mid + 1;
        else
            hi = mid;
    }
    return lo;
}

// 找到第一个>target的位置（upper_bound）
int upper_bound(vector<int>& arr, int target) {
    int lo = 0, hi = arr.size();
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] <= target)
            lo = mid + 1;
        else
            hi = mid;
    }
    return lo;
}
```

---

### 5.2 Sliding Window (滑动窗口)

**定义**：维护一个大小可变或固定的窗口在数组上滑动，常用于子数组问题。

**典型应用**：
```cpp
// 最长无重复字符子串
int lengthOfLongestSubstring(string s) {
    unordered_set<char> window;
    int left = 0, maxLen = 0;
    
    for (int right = 0; right < s.size(); right++) {
        while (window.count(s[right])) {
            window.erase(s[left]);
            left++;
        }
        window.insert(s[right]);
        maxLen = max(maxLen, right - left + 1);
    }
    return maxLen;
}
```

**HFT应用**：滑动窗口统计（VWAP、滚动均值等）

**详细文章**：[在线算法与流式计算(HFT)](/articles/algorithm/algo-10-在线算法与流式计算/)

---

### 5.3 Two Pointers (双指针)

**定义**：使用两个指针遍历数据结构，常用于有序数组和链表问题。

**典型模式**：

1. **对撞指针**：
```cpp
// 有序数组两数之和
bool twoSum(vector<int>& nums, int target) {
    int left = 0, right = nums.size() - 1;
    while (left < right) {
        int sum = nums[left] + nums[right];
        if (sum == target) return true;
        else if (sum < target) left++;
        else right--;
    }
    return false;
}
```

2. **快慢指针**：
```cpp
// 链表找环
bool hasCycle(ListNode* head) {
    ListNode *slow = head, *fast = head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return true;
    }
    return false;
}
```

---

### 5.4 Greedy Algorithm (贪心算法)

**定义**：每一步都选择当前最优解，期望最终得到全局最优解的算法策略。

**核心思想**：
```
贪心选择性质：局部最优 → 全局最优
无后效性：当前选择不影响后续子问题的结构
```

**与动态规划的区别**：

| 特性 | 贪心 | 动态规划 |
|------|------|----------|
| 选择策略 | 每步取当前最优 | 考虑所有子问题 |
| 是否回溯 | 不回溯 | 可比较多个方案 |
| 最优保证 | 不一定全局最优 | 保证全局最优 |
| 时间复杂度 | 通常更低 | 通常更高 |
| 适用场景 | 满足贪心性质 | 有重叠子问题 |

**经典贪心问题**：

**1. 区间调度（Activity Selection）**：
```cpp
// 问题：选择最多的互不重叠区间
// 贪心策略：按结束时间排序，优先选择结束早的

int maxNonOverlapping(vector<vector<int>>& intervals) {
    if (intervals.empty()) return 0;
    
    // 按结束时间排序
    sort(intervals.begin(), intervals.end(), 
         [](auto& a, auto& b) { return a[1] < b[1]; });
    
    int count = 1;
    int end = intervals[0][1];
    
    for (int i = 1; i < intervals.size(); i++) {
        if (intervals[i][0] >= end) {  // 不重叠
            count++;
            end = intervals[i][1];
        }
    }
    return count;
}
```

**2. 分数背包（Fractional Knapsack）**：
```cpp
// 问题：物品可以分割，求最大价值
// 贪心策略：按价值/重量比排序，优先装性价比高的

double fractionalKnapsack(vector<pair<int,int>>& items, int W) {
    // items: {value, weight}
    sort(items.begin(), items.end(), [](auto& a, auto& b) {
        return (double)a.first / a.second > (double)b.first / b.second;
    });
    
    double totalValue = 0;
    for (auto& [v, w] : items) {
        if (W >= w) {
            totalValue += v;
            W -= w;
        } else {
            totalValue += v * ((double)W / w);  // 装部分
            break;
        }
    }
    return totalValue;
}
```

**3. Huffman编码**：
```cpp
// 问题：构建最优前缀编码
// 贪心策略：每次合并频率最小的两个节点

struct HuffmanNode {
    char ch;
    int freq;
    HuffmanNode *left, *right;
};

HuffmanNode* buildHuffmanTree(unordered_map<char, int>& freq) {
    auto cmp = [](HuffmanNode* a, HuffmanNode* b) {
        return a->freq > b->freq;
    };
    priority_queue<HuffmanNode*, vector<HuffmanNode*>, decltype(cmp)> pq(cmp);
    
    for (auto& [ch, f] : freq) {
        pq.push(new HuffmanNode{ch, f, nullptr, nullptr});
    }
    
    while (pq.size() > 1) {
        HuffmanNode* left = pq.top(); pq.pop();
        HuffmanNode* right = pq.top(); pq.pop();
        
        HuffmanNode* parent = new HuffmanNode{
            '\0', left->freq + right->freq, left, right
        };
        pq.push(parent);
    }
    return pq.top();
}
```

**贪心算法的证明方法**：
1. **交换论证**：证明将最优解中的任意选择换成贪心选择不会更差
2. **归纳法**：证明每步贪心选择都保持最优解的可能性
3. **反证法**：假设贪心不是最优，推导矛盾

**常见贪心问题列表**：

| 问题 | 贪心策略 | 复杂度 |
|------|----------|--------|
| 区间调度 | 按结束时间排序 | O(n log n) |
| 区间覆盖 | 按起点排序 | O(n log n) |
| 跳跃游戏 | 维护最远可达位置 | O(n) |
| 分发糖果 | 两次遍历（左右） | O(n) |
| 加油站 | 累计油量差 | O(n) |
| 任务调度 | 最短作业优先 | O(n log n) |
| Dijkstra | 选最近未访问节点 | O((V+E) log V) |
| Prim/Kruskal | 选最小边 | O(E log E) |

**HFT中的应用**：
- 订单路由：选择最优执行venue
- 资源分配：分配计算资源到策略
- 网络优化：选择最低延迟路径

---

### 5.5 Dynamic Programming (动态规划)

**定义**：将复杂问题分解为重叠子问题，通过存储子问题的解避免重复计算。

**核心要素**：
1. **最优子结构**：问题的最优解包含子问题的最优解
2. **重叠子问题**：同一子问题被多次求解
3. **状态定义**：用变量描述问题的状态
4. **状态转移方程**：状态之间的递推关系

**实现方式**：

```cpp
// 以斐波那契为例

// 方式1：自顶向下（记忆化递归）
unordered_map<int, int> memo;
int fib_topdown(int n) {
    if (n <= 1) return n;
    if (memo.count(n)) return memo[n];
    return memo[n] = fib_topdown(n-1) + fib_topdown(n-2);
}

// 方式2：自底向上（迭代）
int fib_bottomup(int n) {
    if (n <= 1) return n;
    vector<int> dp(n + 1);
    dp[0] = 0; dp[1] = 1;
    for (int i = 2; i <= n; i++) {
        dp[i] = dp[i-1] + dp[i-2];
    }
    return dp[n];
}

// 方式3：空间优化
int fib_optimized(int n) {
    if (n <= 1) return n;
    int prev2 = 0, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        int curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}
```

**经典DP问题**：

**1. 0-1背包**：
```cpp
// 问题：物品不可分割，求最大价值
// 状态：dp[i][w] = 前i个物品，容量w的最大价值
// 转移：dp[i][w] = max(不选第i个, 选第i个)

int knapsack(vector<int>& weights, vector<int>& values, int W) {
    int n = weights.size();
    vector<vector<int>> dp(n + 1, vector<int>(W + 1, 0));
    
    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= W; w++) {
            dp[i][w] = dp[i-1][w];  // 不选
            if (w >= weights[i-1]) {
                dp[i][w] = max(dp[i][w], 
                    dp[i-1][w - weights[i-1]] + values[i-1]);  // 选
            }
        }
    }
    return dp[n][W];
}

// 空间优化（一维数组）
int knapsack_optimized(vector<int>& weights, vector<int>& values, int W) {
    int n = weights.size();
    vector<int> dp(W + 1, 0);
    
    for (int i = 0; i < n; i++) {
        for (int w = W; w >= weights[i]; w--) {  // 逆序！
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i]);
        }
    }
    return dp[W];
}
```

**2. 最长公共子序列（LCS）**：
```cpp
// 状态：dp[i][j] = text1[0..i-1]和text2[0..j-1]的LCS长度
// 转移：相等则+1，否则取max

int longestCommonSubsequence(string& text1, string& text2) {
    int m = text1.size(), n = text2.size();
    vector<vector<int>> dp(m + 1, vector<int>(n + 1, 0));
    
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (text1[i-1] == text2[j-1]) {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = max(dp[i-1][j], dp[i][j-1]);
            }
        }
    }
    return dp[m][n];
}
```

**3. 最长递增子序列（LIS）**：
```cpp
// O(n²)解法
int lengthOfLIS(vector<int>& nums) {
    int n = nums.size();
    vector<int> dp(n, 1);  // dp[i] = 以nums[i]结尾的LIS长度
    
    for (int i = 1; i < n; i++) {
        for (int j = 0; j < i; j++) {
            if (nums[j] < nums[i]) {
                dp[i] = max(dp[i], dp[j] + 1);
            }
        }
    }
    return *max_element(dp.begin(), dp.end());
}

// O(n log n)解法（二分优化）
int lengthOfLIS_fast(vector<int>& nums) {
    vector<int> tails;  // tails[i] = 长度为i+1的LIS的最小结尾
    
    for (int num : nums) {
        auto it = lower_bound(tails.begin(), tails.end(), num);
        if (it == tails.end()) {
            tails.push_back(num);
        } else {
            *it = num;
        }
    }
    return tails.size();
}
```

**DP问题分类**：

| 类型 | 示例 | 状态定义 |
|------|------|----------|
| 线性DP | LIS, 打家劫舍 | dp[i] = 前i个元素的结果 |
| 区间DP | 矩阵链乘法, 戳气球 | dp[i][j] = 区间[i,j]的结果 |
| 背包DP | 0-1背包, 完全背包 | dp[i][w] = 前i个物品容量w |
| 树形DP | 树的最大独立集 | dp[u] = 以u为根的子树结果 |
| 状态压缩DP | 旅行商问题 | dp[mask] = 状态集合mask的结果 |
| 数位DP | 统计数字问题 | 按数位构建状态 |

**DP优化技巧**：
1. **滚动数组**：空间从O(n²)降到O(n)
2. **单调队列**：某些区间最值问题O(n)
3. **斜率优化**：凸包优化转移
4. **四边形不等式**：区间DP优化

---

### 5.6 Divide and Conquer (分治算法)

**定义**：将问题分解为规模更小的相同子问题，递归解决后合并结果。

**步骤**：
1. **Divide**：分解问题
2. **Conquer**：递归解决子问题
3. **Combine**：合并子问题的解

**经典分治算法**：

**1. 归并排序**：
```cpp
void mergeSort(vector<int>& arr, int left, int right) {
    if (left >= right) return;
    
    int mid = left + (right - left) / 2;
    mergeSort(arr, left, mid);      // 分
    mergeSort(arr, mid + 1, right); // 分
    merge(arr, left, mid, right);   // 合
}

void merge(vector<int>& arr, int left, int mid, int right) {
    vector<int> temp(right - left + 1);
    int i = left, j = mid + 1, k = 0;
    
    while (i <= mid && j <= right) {
        temp[k++] = (arr[i] <= arr[j]) ? arr[i++] : arr[j++];
    }
    while (i <= mid) temp[k++] = arr[i++];
    while (j <= right) temp[k++] = arr[j++];
    
    for (int i = 0; i < temp.size(); i++) {
        arr[left + i] = temp[i];
    }
}
```

**2. 快速排序**：
```cpp
void quickSort(vector<int>& arr, int left, int right) {
    if (left >= right) return;
    
    int pivot = partition(arr, left, right);
    quickSort(arr, left, pivot - 1);
    quickSort(arr, pivot + 1, right);
}

int partition(vector<int>& arr, int left, int right) {
    int pivot = arr[right];  // 选最后一个为pivot
    int i = left;
    
    for (int j = left; j < right; j++) {
        if (arr[j] < pivot) {
            swap(arr[i++], arr[j]);
        }
    }
    swap(arr[i], arr[right]);
    return i;
}
```

**3. 第K大元素（快速选择）**：
```cpp
// 平均O(n)，最坏O(n²)
int quickSelect(vector<int>& arr, int left, int right, int k) {
    if (left == right) return arr[left];
    
    int pivot = partition(arr, left, right);
    
    if (pivot == k) return arr[k];
    else if (pivot > k) return quickSelect(arr, left, pivot - 1, k);
    else return quickSelect(arr, pivot + 1, right, k);
}
```

**分治的时间复杂度分析（主定理）**：
```
T(n) = aT(n/b) + O(n^d)

其中：a = 子问题个数，b = 规模缩小倍数，d = 合并复杂度指数

结论：
- 若 d < log_b(a): T(n) = O(n^(log_b a))
- 若 d = log_b(a): T(n) = O(n^d log n)
- 若 d > log_b(a): T(n) = O(n^d)

示例：
- 归并排序: a=2, b=2, d=1 → T(n) = O(n log n)
- 二分查找: a=1, b=2, d=0 → T(n) = O(log n)
- Karatsuba乘法: a=3, b=2, d=1 → T(n) = O(n^1.585)
```

---

## 六、图论基础

### 6.1 Graph (图)

**定义**：由顶点(Vertex)集合和边(Edge)集合组成的数据结构，用于表示对象之间的关系。

**图的分类**：

| 类型 | 描述 | 示例 |
|------|------|------|
| **有向图** | 边有方向 | 网页链接、依赖关系 |
| **无向图** | 边无方向 | 社交网络好友关系 |
| **加权图** | 边有权重 | 路网（距离）、网络（带宽）|
| **稀疏图** | 边数远小于n² | 社交网络 |
| **稠密图** | 边数接近n² | 小型全连接网络 |

**存储方式**：
```cpp
// 方法1：邻接矩阵 - 适合稠密图，O(1)查边
int adj[N][N];  // adj[i][j] = 边权，0表示无边

// 方法2：邻接表 - 适合稀疏图，省空间
vector<pair<int, int>> adj[N];  // adj[i] = {(邻居, 权重), ...}

// 方法3：边列表 - 适合某些算法（Kruskal）
struct Edge { int u, v, w; };
vector<Edge> edges;
```

**基本术语**：
- **度(Degree)**：与节点相连的边数
- **入度/出度**：有向图中指向该节点/从该节点出发的边数
- **路径(Path)**：顶点序列，相邻顶点间有边
- **环(Cycle)**：起点和终点相同的路径
- **连通图**：任意两点间存在路径
- **DAG**：有向无环图(Directed Acyclic Graph)

---

### 6.2 DFS (深度优先搜索)

**定义**：沿着一条路径尽可能深入，直到无法继续才回溯的遍历策略。

**实现**：
```cpp
vector<int> adj[N];
bool visited[N];

// 递归版
void dfs(int u) {
    visited[u] = true;
    // 处理节点u
    for (int v : adj[u]) {
        if (!visited[v]) {
            dfs(v);
        }
    }
}

// 非递归版（用栈模拟）
void dfs_iterative(int start) {
    stack<int> s;
    s.push(start);
    
    while (!s.empty()) {
        int u = s.top(); s.pop();
        if (visited[u]) continue;
        visited[u] = true;
        
        // 处理节点u
        for (int v : adj[u]) {
            if (!visited[v]) {
                s.push(v);
            }
        }
    }
}
```

**应用**：
- 连通分量检测
- 拓扑排序
- 环检测
- 路径查找

**复杂度**：O(V + E)，V是顶点数，E是边数

---

### 6.3 BFS (广度优先搜索)

**定义**：逐层遍历图，先访问距离起点近的节点。

**实现**：
```cpp
void bfs(int start) {
    queue<int> q;
    q.push(start);
    visited[start] = true;
    int level = 0;
    
    while (!q.empty()) {
        int size = q.size();  // 当前层节点数
        for (int i = 0; i < size; i++) {
            int u = q.front(); q.pop();
            
            // 处理节点u（在第level层）
            for (int v : adj[u]) {
                if (!visited[v]) {
                    visited[v] = true;
                    q.push(v);
                }
            }
        }
        level++;
    }
}
```

**核心性质**：BFS保证找到的路径是**最短路径**（无权图）

**应用**：
- 无权图最短路径
- 层序遍历
- 状态空间搜索（如八数码问题）

**复杂度**：O(V + E)

---

### 6.4 Shortest Path (最短路径)

**问题分类**：

| 算法 | 适用场景 | 复杂度 |
|------|----------|--------|
| **BFS** | 无权图 | O(V + E) |
| **Dijkstra** | 非负权图 | O((V+E) log V) |
| **Bellman-Ford** | 可有负权 | O(VE) |
| **Floyd-Warshall** | 所有点对 | O(V³) |

**Dijkstra算法**（最常用）：
```cpp
// 单源最短路径，非负权重
vector<int> dijkstra(int n, vector<vector<pair<int,int>>>& adj, int start) {
    vector<int> dist(n, INT_MAX);
    // 小顶堆：{距离, 节点}
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    
    dist[start] = 0;
    pq.push({0, start});
    
    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        
        // 已经找到更短路径，跳过
        if (d > dist[u]) continue;
        
        for (auto [v, w] : adj[u]) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                pq.push({dist[v], v});
            }
        }
    }
    return dist;
}
```

**为什么Dijkstra不能处理负权**：
```
贪心策略假设：已确定最短距离的节点不会被更新
负权边破坏这个假设：
    A ---1--→ B
    ↘        ↗
     ---3-→ C (C→B 权重 -5)

Dijkstra会先确定B的距离为1
但实际 A→C→B = 3 + (-5) = -2 更短
```

---

### 6.5 Topological Sort (拓扑排序)

**定义**：将DAG的所有顶点排成线性序列，使得对于每条边(u, v)，u在序列中出现在v之前。

**应用**：
- 任务调度（先修课程）
- 编译依赖
- 构建系统

**实现方法**：

```cpp
// 方法1：Kahn算法（BFS）
vector<int> topologicalSort(int n, vector<vector<int>>& adj) {
    vector<int> inDegree(n, 0);
    for (int u = 0; u < n; u++) {
        for (int v : adj[u]) {
            inDegree[v]++;
        }
    }
    
    queue<int> q;
    for (int i = 0; i < n; i++) {
        if (inDegree[i] == 0) q.push(i);
    }
    
    vector<int> order;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        order.push_back(u);
        
        for (int v : adj[u]) {
            if (--inDegree[v] == 0) {
                q.push(v);
            }
        }
    }
    
    // 如果order.size() < n，说明有环
    return order.size() == n ? order : vector<int>();
}

// 方法2：DFS（后序遍历逆序）
vector<int> result;
bool hasCycle = false;

void dfs(int u, vector<int>& state, vector<vector<int>>& adj) {
    state[u] = 1;  // 正在访问
    
    for (int v : adj[u]) {
        if (state[v] == 1) {
            hasCycle = true;  // 有环
            return;
        }
        if (state[v] == 0) {
            dfs(v, state, adj);
        }
    }
    
    state[u] = 2;  // 已完成
    result.push_back(u);  // 后序
}

vector<int> topologicalSortDFS(int n, vector<vector<int>>& adj) {
    vector<int> state(n, 0);  // 0:未访问 1:访问中 2:已完成
    
    for (int i = 0; i < n; i++) {
        if (state[i] == 0) dfs(i, state, adj);
    }
    
    reverse(result.begin(), result.end());
    return hasCycle ? vector<int>() : result;
}
```

---

### 6.6 Union-Find (并查集)

**定义**：一种数据结构，支持快速合并集合和查询两个元素是否属于同一集合。

**核心操作**：
- `find(x)`：找到x所属集合的代表元素
- `union(x, y)`：合并x和y所在的集合

**优化实现**：
```cpp
class UnionFind {
    vector<int> parent, rank_;
    int components;  // 连通分量数
    
public:
    UnionFind(int n) : parent(n), rank_(n, 0), components(n) {
        for (int i = 0; i < n; i++) parent[i] = i;
    }
    
    // 路径压缩
    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // 递归压缩
        }
        return parent[x];
    }
    
    // 按秩合并
    bool unite(int x, int y) {
        int px = find(x), py = find(y);
        if (px == py) return false;  // 已在同一集合
        
        // 小树接到大树下面
        if (rank_[px] < rank_[py]) swap(px, py);
        parent[py] = px;
        if (rank_[px] == rank_[py]) rank_[px]++;
        
        components--;
        return true;
    }
    
    bool connected(int x, int y) {
        return find(x) == find(y);
    }
    
    int count() { return components; }
};
```

**复杂度**：近乎O(1)（准确说是O(α(n))，α是反阿克曼函数）

**应用**：
- 检测图中是否有环
- Kruskal最小生成树
- 连通分量计数
- 社交网络朋友圈

---

### 6.7 Minimum Spanning Tree (最小生成树)

**定义**：连接图中所有顶点的边权和最小的树。

**Kruskal算法**（适合稀疏图）：
```cpp
// 贪心：按边权排序，依次加入不形成环的边
int kruskal(int n, vector<Edge>& edges) {
    sort(edges.begin(), edges.end(), 
         [](auto& a, auto& b) { return a.w < b.w; });
    
    UnionFind uf(n);
    int totalWeight = 0;
    int edgeCount = 0;
    
    for (auto& [u, v, w] : edges) {
        if (uf.unite(u, v)) {  // 不形成环
            totalWeight += w;
            if (++edgeCount == n - 1) break;  // 已经n-1条边
        }
    }
    
    return edgeCount == n - 1 ? totalWeight : -1;  // -1表示不连通
}
```

**Prim算法**（适合稠密图）：
```cpp
// 贪心：每次选择连接已选节点和未选节点的最小边
int prim(int n, vector<vector<pair<int,int>>>& adj) {
    vector<bool> inMST(n, false);
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    
    pq.push({0, 0});  // {权重, 节点}
    int totalWeight = 0;
    int count = 0;
    
    while (!pq.empty() && count < n) {
        auto [w, u] = pq.top(); pq.pop();
        
        if (inMST[u]) continue;
        inMST[u] = true;
        totalWeight += w;
        count++;
        
        for (auto [v, weight] : adj[u]) {
            if (!inMST[v]) {
                pq.push({weight, v});
            }
        }
    }
    
    return count == n ? totalWeight : -1;
}
```

**复杂度对比**：
- Kruskal: O(E log E)
- Prim (堆优化): O((V + E) log V)

---

## 七、LeetCode 常见算法 (Python3)

本节收录 LeetCode 面试笔试中高频出现的简单到中级难度题目，提供 Python3 解题模板和详细解析。

---

### 7.1 数组与哈希表

#### 7.1.1 两数之和 (Easy) - LeetCode 1

**题目**：给定数组和目标值，找到两个数使得它们的和等于目标值，返回下标。

**思路**：哈希表存储 `{值: 下标}`，遍历时查找 `target - num` 是否存在。

```python
def twoSum(nums: list[int], target: int) -> list[int]:
    seen = {}  # 值 -> 下标
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# 示例
# twoSum([2, 7, 11, 15], 9) → [0, 1]
```

**复杂度**：时间 O(n)，空间 O(n)

---

#### 7.1.2 三数之和 (Medium) - LeetCode 15

**题目**：找出数组中所有和为0的不重复三元组。

**思路**：排序 + 固定第一个数 + 双指针。

```python
def threeSum(nums: list[int]) -> list[list[int]]:
    nums.sort()
    result = []
    n = len(nums)
    
    for i in range(n - 2):
        # 跳过重复的第一个数
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        
        # 双指针
        left, right = i + 1, n - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            
            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                # 跳过重复
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    
    return result

# 示例
# threeSum([-1, 0, 1, 2, -1, -4]) → [[-1, -1, 2], [-1, 0, 1]]
```

**复杂度**：时间 O(n²)，空间 O(1)（不计输出）

---

#### 7.1.3 最大子数组和 (Medium) - LeetCode 53

**题目**：找到具有最大和的连续子数组。

**思路**：Kadane算法 - 动态规划思想，维护当前最大和。

```python
def maxSubArray(nums: list[int]) -> int:
    max_sum = nums[0]
    current_sum = nums[0]
    
    for num in nums[1:]:
        # 要么加入当前子数组，要么重新开始
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)
    
    return max_sum

# 示例
# maxSubArray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) → 6 (子数组[4,-1,2,1])
```

**复杂度**：时间 O(n)，空间 O(1)

---

#### 7.1.4 合并区间 (Medium) - LeetCode 56

**题目**：合并所有重叠的区间。

**思路**：按起点排序，依次合并。

```python
def merge(intervals: list[list[int]]) -> list[list[int]]:
    if not intervals:
        return []
    
    # 按起点排序
    intervals.sort(key=lambda x: x[0])
    result = [intervals[0]]
    
    for start, end in intervals[1:]:
        # 如果当前区间与上一个重叠
        if start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    
    return result

# 示例
# merge([[1,3],[2,6],[8,10],[15,18]]) → [[1,6],[8,10],[15,18]]
```

**复杂度**：时间 O(n log n)，空间 O(n)

---

#### 7.1.5 除自身以外数组的乘积 (Medium) - LeetCode 238

**题目**：返回数组，其中每个元素是除自身外所有元素的乘积，不能用除法。

**思路**：左右两次遍历，分别计算左侧和右侧乘积。

```python
def productExceptSelf(nums: list[int]) -> list[int]:
    n = len(nums)
    result = [1] * n
    
    # 左侧乘积
    left_product = 1
    for i in range(n):
        result[i] = left_product
        left_product *= nums[i]
    
    # 右侧乘积
    right_product = 1
    for i in range(n - 1, -1, -1):
        result[i] *= right_product
        right_product *= nums[i]
    
    return result

# 示例
# productExceptSelf([1,2,3,4]) → [24,12,8,6]
```

**复杂度**：时间 O(n)，空间 O(1)（不计输出）

---

#### 7.1.6 字母异位词分组 (Medium) - LeetCode 49

**题目**：将字母异位词（anagram）分组。

**思路**：排序后的字符串作为哈希表的键。

```python
from collections import defaultdict

def groupAnagrams(strs: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    
    for s in strs:
        # 排序作为键
        key = ''.join(sorted(s))
        groups[key].append(s)
    
    return list(groups.values())

# 更快的方法：使用字符计数作为键
def groupAnagrams_v2(strs: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    
    for s in strs:
        # 字符计数作为键
        count = [0] * 26
        for c in s:
            count[ord(c) - ord('a')] += 1
        key = tuple(count)
        groups[key].append(s)
    
    return list(groups.values())

# 示例
# groupAnagrams(["eat","tea","tan","ate","nat","bat"]) 
# → [["eat","tea","ate"],["tan","nat"],["bat"]]
```

**复杂度**：时间 O(n × k log k) 或 O(n × k)，空间 O(n × k)

---

### 7.2 链表操作

#### 7.2.1 反转链表 (Easy) - LeetCode 206

**题目**：反转单链表。

**思路**：迭代法 - 三指针逐个翻转。

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverseList(head: ListNode) -> ListNode:
    prev = None
    curr = head
    
    while curr:
        next_temp = curr.next  # 保存下一个
        curr.next = prev       # 反转指针
        prev = curr            # 前进
        curr = next_temp
    
    return prev

# 递归版本
def reverseList_recursive(head: ListNode) -> ListNode:
    if not head or not head.next:
        return head
    
    new_head = reverseList_recursive(head.next)
    head.next.next = head
    head.next = None
    
    return new_head
```

**复杂度**：时间 O(n)，空间 O(1) / O(n) 递归

---

#### 7.2.2 合并两个有序链表 (Easy) - LeetCode 21

**题目**：合并两个升序链表为一个升序链表。

**思路**：双指针 + 哨兵节点。

```python
def mergeTwoLists(l1: ListNode, l2: ListNode) -> ListNode:
    dummy = ListNode(0)  # 哨兵节点
    curr = dummy
    
    while l1 and l2:
        if l1.val <= l2.val:
            curr.next = l1
            l1 = l1.next
        else:
            curr.next = l2
            l2 = l2.next
        curr = curr.next
    
    # 连接剩余部分
    curr.next = l1 if l1 else l2
    
    return dummy.next
```

**复杂度**：时间 O(n + m)，空间 O(1)

---

#### 7.2.3 环形链表 II (Medium) - LeetCode 142

**题目**：如果链表有环，返回环的入口节点。

**思路**：快慢指针相遇后，从头和相遇点同时出发。

```python
def detectCycle(head: ListNode) -> ListNode:
    slow = fast = head
    
    # 快慢指针找相遇点
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            break
    else:
        return None  # 无环
    
    # 从头和相遇点同时出发
    ptr = head
    while ptr != slow:
        ptr = ptr.next
        slow = slow.next
    
    return ptr

# 数学证明：
# 设头到入口距离a，入口到相遇点b，相遇点到入口c
# 慢指针走了 a + b
# 快指针走了 a + b + n(b + c)，n是快指针多绕的圈数
# 2(a + b) = a + b + n(b + c)
# a = (n-1)(b + c) + c
# 所以从头和相遇点同时走，会在入口相遇
```

**复杂度**：时间 O(n)，空间 O(1)

---

#### 7.2.4 删除链表的倒数第 N 个节点 (Medium) - LeetCode 19

**题目**：删除链表的倒数第 N 个节点。

**思路**：快慢指针，快指针先走N步。

```python
def removeNthFromEnd(head: ListNode, n: int) -> ListNode:
    dummy = ListNode(0, head)  # 哨兵处理删除头节点
    fast = slow = dummy
    
    # 快指针先走 n+1 步
    for _ in range(n + 1):
        fast = fast.next
    
    # 同时前进，直到快指针到末尾
    while fast:
        fast = fast.next
        slow = slow.next
    
    # 删除节点
    slow.next = slow.next.next
    
    return dummy.next
```

**复杂度**：时间 O(n)，空间 O(1)

---

#### 7.2.5 LRU 缓存 (Medium) - LeetCode 146

**题目**：实现 LRU（最近最少使用）缓存。

**思路**：哈希表 + 双向链表。

```python
class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}  # key -> node
        # 双向链表：head <-> ... <-> tail
        self.head = DLinkedNode()
        self.tail = DLinkedNode()
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._move_to_head(node)
        return node.value
    
    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._move_to_head(node)
        else:
            node = DLinkedNode(key, value)
            self.cache[key] = node
            self._add_to_head(node)
            
            if len(self.cache) > self.capacity:
                removed = self._remove_tail()
                del self.cache[removed.key]
    
    def _add_to_head(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
    
    def _remove_node(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _move_to_head(self, node):
        self._remove_node(node)
        self._add_to_head(node)
    
    def _remove_tail(self):
        node = self.tail.prev
        self._remove_node(node)
        return node

class DLinkedNode:
    def __init__(self, key=0, value=0):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

# 使用 Python OrderedDict 的简洁实现
from collections import OrderedDict

class LRUCache_Simple:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)  # 移到末尾（最近使用）
        return self.cache[key]
    
    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)  # 删除最久未使用
```

**复杂度**：get/put 都是 O(1)

---

### 7.3 二叉树

#### 7.3.1 二叉树遍历模板 (Easy)

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

# 前序遍历 (根-左-右)
def preorderTraversal(root: TreeNode) -> list[int]:
    result = []
    def dfs(node):
        if not node:
            return
        result.append(node.val)  # 根
        dfs(node.left)           # 左
        dfs(node.right)          # 右
    dfs(root)
    return result

# 中序遍历 (左-根-右) - BST得到有序序列
def inorderTraversal(root: TreeNode) -> list[int]:
    result = []
    def dfs(node):
        if not node:
            return
        dfs(node.left)           # 左
        result.append(node.val)  # 根
        dfs(node.right)          # 右
    dfs(root)
    return result

# 后序遍历 (左-右-根)
def postorderTraversal(root: TreeNode) -> list[int]:
    result = []
    def dfs(node):
        if not node:
            return
        dfs(node.left)           # 左
        dfs(node.right)          # 右
        result.append(node.val)  # 根
    dfs(root)
    return result

# 层序遍历 (BFS)
from collections import deque

def levelOrder(root: TreeNode) -> list[list[int]]:
    if not root:
        return []
    
    result = []
    queue = deque([root])
    
    while queue:
        level = []
        for _ in range(len(queue)):  # 当前层的节点数
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

#### 7.3.2 二叉树最大深度 (Easy) - LeetCode 104

```python
def maxDepth(root: TreeNode) -> int:
    if not root:
        return 0
    return 1 + max(maxDepth(root.left), maxDepth(root.right))

# 迭代版本 (BFS)
def maxDepth_bfs(root: TreeNode) -> int:
    if not root:
        return 0
    
    depth = 0
    queue = deque([root])
    
    while queue:
        depth += 1
        for _ in range(len(queue)):
            node = queue.popleft()
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
    
    return depth
```

**复杂度**：时间 O(n)，空间 O(h)，h是树高

---

#### 7.3.3 验证二叉搜索树 (Medium) - LeetCode 98

**题目**：验证是否为有效的二叉搜索树。

**思路**：递归传递有效范围，或中序遍历检查有序。

```python
def isValidBST(root: TreeNode) -> bool:
    def validate(node, min_val, max_val):
        if not node:
            return True
        
        if not (min_val < node.val < max_val):
            return False
        
        return (validate(node.left, min_val, node.val) and
                validate(node.right, node.val, max_val))
    
    return validate(root, float('-inf'), float('inf'))

# 中序遍历版本
def isValidBST_inorder(root: TreeNode) -> bool:
    prev = float('-inf')
    
    def inorder(node):
        nonlocal prev
        if not node:
            return True
        
        if not inorder(node.left):
            return False
        
        if node.val <= prev:
            return False
        prev = node.val
        
        return inorder(node.right)
    
    return inorder(root)
```

**复杂度**：时间 O(n)，空间 O(h)

---

#### 7.3.4 二叉树的最近公共祖先 (Medium) - LeetCode 236

**题目**：找到两个节点的最近公共祖先（LCA）。

**思路**：后序遍历，自底向上返回找到的节点。

```python
def lowestCommonAncestor(root: TreeNode, p: TreeNode, q: TreeNode) -> TreeNode:
    if not root or root == p or root == q:
        return root
    
    left = lowestCommonAncestor(root.left, p, q)
    right = lowestCommonAncestor(root.right, p, q)
    
    # 如果左右都找到了，当前节点就是LCA
    if left and right:
        return root
    
    # 否则返回找到的那个
    return left if left else right
```

**复杂度**：时间 O(n)，空间 O(h)

---

#### 7.3.5 二叉树的直径 (Easy) - LeetCode 543

**题目**：求二叉树中任意两节点路径长度的最大值。

**思路**：对每个节点，计算左子树深度 + 右子树深度。

```python
def diameterOfBinaryTree(root: TreeNode) -> int:
    diameter = 0
    
    def depth(node):
        nonlocal diameter
        if not node:
            return 0
        
        left = depth(node.left)
        right = depth(node.right)
        
        # 更新直径
        diameter = max(diameter, left + right)
        
        return 1 + max(left, right)
    
    depth(root)
    return diameter
```

**复杂度**：时间 O(n)，空间 O(h)

---

### 7.4 回溯算法

回溯算法的核心模板：

```python
def backtrack(路径, 选择列表):
    if 满足结束条件:
        result.append(路径[:])  # 注意要复制
        return
    
    for 选择 in 选择列表:
        做选择
        backtrack(路径, 选择列表)
        撤销选择
```

---

#### 7.4.1 全排列 (Medium) - LeetCode 46

**题目**：返回数组的所有排列。

```python
def permute(nums: list[int]) -> list[list[int]]:
    result = []
    
    def backtrack(path, remaining):
        if not remaining:
            result.append(path[:])
            return
        
        for i in range(len(remaining)):
            # 选择
            path.append(remaining[i])
            # 递归（排除当前元素）
            backtrack(path, remaining[:i] + remaining[i+1:])
            # 撤销
            path.pop()
    
    backtrack([], nums)
    return result

# 使用交换的版本（更高效）
def permute_swap(nums: list[int]) -> list[list[int]]:
    result = []
    
    def backtrack(start):
        if start == len(nums):
            result.append(nums[:])
            return
        
        for i in range(start, len(nums)):
            nums[start], nums[i] = nums[i], nums[start]
            backtrack(start + 1)
            nums[start], nums[i] = nums[i], nums[start]
    
    backtrack(0)
    return result

# 示例
# permute([1,2,3]) → [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
```

**复杂度**：时间 O(n! × n)，空间 O(n)

---

#### 7.4.2 子集 (Medium) - LeetCode 78

**题目**：返回数组的所有子集（幂集）。

```python
def subsets(nums: list[int]) -> list[list[int]]:
    result = []
    
    def backtrack(start, path):
        result.append(path[:])  # 每个路径都是一个子集
        
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)  # 从i+1开始，避免重复
            path.pop()
    
    backtrack(0, [])
    return result

# 迭代版本
def subsets_iterative(nums: list[int]) -> list[list[int]]:
    result = [[]]
    for num in nums:
        # 在现有子集基础上，加入新元素形成新子集
        result += [subset + [num] for subset in result]
    return result

# 位运算版本
def subsets_bit(nums: list[int]) -> list[list[int]]:
    n = len(nums)
    result = []
    for mask in range(1 << n):  # 0 到 2^n - 1
        subset = [nums[i] for i in range(n) if mask & (1 << i)]
        result.append(subset)
    return result

# 示例
# subsets([1,2,3]) → [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]
```

**复杂度**：时间 O(2^n × n)，空间 O(n)

---

#### 7.4.3 组合总和 (Medium) - LeetCode 39

**题目**：找出所有和为target的组合，数字可以重复使用。

```python
def combinationSum(candidates: list[int], target: int) -> list[list[int]]:
    result = []
    
    def backtrack(start, path, remaining):
        if remaining == 0:
            result.append(path[:])
            return
        if remaining < 0:
            return
        
        for i in range(start, len(candidates)):
            path.append(candidates[i])
            # 可以重复使用，所以还是从i开始
            backtrack(i, path, remaining - candidates[i])
            path.pop()
    
    backtrack(0, [], target)
    return result

# 示例
# combinationSum([2,3,6,7], 7) → [[2,2,3],[7]]
```

**复杂度**：取决于解的数量

---

#### 7.4.4 电话号码的字母组合 (Medium) - LeetCode 17

**题目**：返回电话号码数字所能表示的所有字母组合。

```python
def letterCombinations(digits: str) -> list[str]:
    if not digits:
        return []
    
    phone = {
        '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
        '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'
    }
    
    result = []
    
    def backtrack(index, path):
        if index == len(digits):
            result.append(''.join(path))
            return
        
        for char in phone[digits[index]]:
            path.append(char)
            backtrack(index + 1, path)
            path.pop()
    
    backtrack(0, [])
    return result

# 示例
# letterCombinations("23") → ["ad","ae","af","bd","be","bf","cd","ce","cf"]
```

**复杂度**：时间 O(4^n × n)，空间 O(n)

---

#### 7.4.5 单词搜索 (Medium) - LeetCode 79

**题目**：在二维网格中搜索单词，可以上下左右移动。

```python
def exist(board: list[list[str]], word: str) -> bool:
    rows, cols = len(board), len(board[0])
    
    def backtrack(r, c, index):
        if index == len(word):
            return True
        
        if (r < 0 or r >= rows or c < 0 or c >= cols or
            board[r][c] != word[index]):
            return False
        
        # 标记已访问
        temp = board[r][c]
        board[r][c] = '#'
        
        # 四个方向
        found = (backtrack(r + 1, c, index + 1) or
                 backtrack(r - 1, c, index + 1) or
                 backtrack(r, c + 1, index + 1) or
                 backtrack(r, c - 1, index + 1))
        
        # 恢复
        board[r][c] = temp
        
        return found
    
    for i in range(rows):
        for j in range(cols):
            if backtrack(i, j, 0):
                return True
    return False
```

**复杂度**：时间 O(m × n × 4^L)，L是单词长度

---

### 7.5 动态规划经典题

#### 7.5.1 爬楼梯 (Easy) - LeetCode 70

**题目**：每次可以爬1或2阶，求爬n阶楼梯的方法数。

```python
def climbStairs(n: int) -> int:
    if n <= 2:
        return n
    
    # dp[i] = dp[i-1] + dp[i-2]
    prev2, prev1 = 1, 2
    for _ in range(3, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    
    return prev1
```

**复杂度**：时间 O(n)，空间 O(1)

---

#### 7.5.2 打家劫舍 (Medium) - LeetCode 198

**题目**：不能偷相邻房屋，求最大金额。

```python
def rob(nums: list[int]) -> int:
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    # dp[i] = max(不偷i, 偷i)
    prev2 = nums[0]
    prev1 = max(nums[0], nums[1])
    
    for i in range(2, len(nums)):
        curr = max(prev1, prev2 + nums[i])
        prev2, prev1 = prev1, curr
    
    return prev1

# 示例
# rob([2,7,9,3,1]) → 12 (偷2+9+1)
```

**复杂度**：时间 O(n)，空间 O(1)

---

#### 7.5.3 零钱兑换 (Medium) - LeetCode 322

**题目**：用最少硬币凑成目标金额。

```python
def coinChange(coins: list[int], amount: int) -> int:
    # dp[i] = 凑成金额i的最少硬币数
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i and dp[i - coin] != float('inf'):
                dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

# 示例
# coinChange([1,2,5], 11) → 3 (5+5+1)
```

**复杂度**：时间 O(amount × n)，空间 O(amount)

---

#### 7.5.4 最长递增子序列 (Medium) - LeetCode 300

**题目**：找到最长严格递增子序列的长度。

```python
# O(n²) 解法
def lengthOfLIS(nums: list[int]) -> int:
    n = len(nums)
    dp = [1] * n  # dp[i] = 以nums[i]结尾的LIS长度
    
    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)

# O(n log n) 解法 - 二分查找
import bisect

def lengthOfLIS_fast(nums: list[int]) -> int:
    tails = []  # tails[i] = 长度为i+1的LIS的最小结尾
    
    for num in nums:
        pos = bisect.bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num
    
    return len(tails)

# 示例
# lengthOfLIS([10,9,2,5,3,7,101,18]) → 4 ([2,3,7,101])
```

**复杂度**：O(n²) 或 O(n log n)

---

#### 7.5.5 最长公共子序列 (Medium) - LeetCode 1143

**题目**：找两个字符串的最长公共子序列。

```python
def longestCommonSubsequence(text1: str, text2: str) -> int:
    m, n = len(text1), len(text2)
    # dp[i][j] = text1[0..i-1]和text2[0..j-1]的LCS长度
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]

# 空间优化版本
def longestCommonSubsequence_optimized(text1: str, text2: str) -> int:
    m, n = len(text1), len(text2)
    dp = [0] * (n + 1)
    
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            temp = dp[j]
            if text1[i - 1] == text2[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = temp
    
    return dp[n]

# 示例
# longestCommonSubsequence("abcde", "ace") → 3 ("ace")
```

**复杂度**：时间 O(m × n)，空间 O(m × n) 或 O(n)

---

#### 7.5.6 编辑距离 (Medium) - LeetCode 72

**题目**：将word1转换为word2所需的最少操作数（插入、删除、替换）。

```python
def minDistance(word1: str, word2: str) -> int:
    m, n = len(word1), len(word2)
    # dp[i][j] = word1[0..i-1]转换到word2[0..j-1]的最小操作数
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # 初始化：空串的转换
    for i in range(m + 1):
        dp[i][0] = i  # 删除i次
    for j in range(n + 1):
        dp[0][j] = j  # 插入j次
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # 删除
                    dp[i][j - 1],      # 插入
                    dp[i - 1][j - 1]   # 替换
                )
    
    return dp[m][n]

# 示例
# minDistance("horse", "ros") → 3
```

**复杂度**：时间 O(m × n)，空间 O(m × n)

---

### 7.6 常用技巧与模板

#### 7.6.1 前缀和

用于快速计算区间和。

```python
# 一维前缀和
def prefix_sum_1d(nums):
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]
    
    # 区间[l, r]的和 = prefix[r+1] - prefix[l]
    return prefix

# 二维前缀和
def prefix_sum_2d(matrix):
    if not matrix:
        return []
    m, n = len(matrix), len(matrix[0])
    prefix = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m):
        for j in range(n):
            prefix[i + 1][j + 1] = (prefix[i][j + 1] + prefix[i + 1][j] 
                                    - prefix[i][j] + matrix[i][j])
    
    # 区域(r1,c1)到(r2,c2)的和
    # = prefix[r2+1][c2+1] - prefix[r1][c2+1] - prefix[r2+1][c1] + prefix[r1][c1]
    return prefix
```

---

#### 7.6.2 单调栈

用于寻找下一个更大/更小元素。

```python
# 下一个更大元素
def nextGreaterElement(nums: list[int]) -> list[int]:
    n = len(nums)
    result = [-1] * n
    stack = []  # 存储索引
    
    for i in range(n):
        # 当前元素比栈顶大，说明找到了栈顶的下一个更大元素
        while stack and nums[i] > nums[stack[-1]]:
            result[stack.pop()] = nums[i]
        stack.append(i)
    
    return result

# 示例
# nextGreaterElement([2,1,2,4,3]) → [4,2,4,-1,-1]

# 每日温度 - LeetCode 739
def dailyTemperatures(temperatures: list[int]) -> list[int]:
    n = len(temperatures)
    result = [0] * n
    stack = []
    
    for i in range(n):
        while stack and temperatures[i] > temperatures[stack[-1]]:
            prev_idx = stack.pop()
            result[prev_idx] = i - prev_idx
        stack.append(i)
    
    return result
```

---

#### 7.6.3 堆/优先队列

```python
import heapq

# Python的heapq是小顶堆

# 基本操作
heap = []
heapq.heappush(heap, 3)
heapq.heappush(heap, 1)
heapq.heappush(heap, 2)
min_val = heapq.heappop(heap)  # 1

# 大顶堆：取负数
max_heap = []
heapq.heappush(max_heap, -3)
heapq.heappush(max_heap, -1)
max_val = -heapq.heappop(max_heap)  # 3

# Top K 问题 - LeetCode 215
def findKthLargest(nums: list[int], k: int) -> int:
    # 维护大小为k的小顶堆
    heap = nums[:k]
    heapq.heapify(heap)
    
    for num in nums[k:]:
        if num > heap[0]:
            heapq.heapreplace(heap, num)
    
    return heap[0]

# 更简洁的方法
def findKthLargest_simple(nums: list[int], k: int) -> int:
    return heapq.nlargest(k, nums)[-1]
```

---

#### 7.6.4 二分查找模板

```python
# 模板1：找到目标值
def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# 模板2：找第一个>=target的位置（左边界）
def lower_bound(nums, target):
    left, right = 0, len(nums)
    while left < right:
        mid = left + (right - left) // 2
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid
    return left

# 模板3：找第一个>target的位置（右边界）
def upper_bound(nums, target):
    left, right = 0, len(nums)
    while left < right:
        mid = left + (right - left) // 2
        if nums[mid] <= target:
            left = mid + 1
        else:
            right = mid
    return left

# 使用 bisect 模块
import bisect
# bisect.bisect_left(a, x)  → lower_bound
# bisect.bisect_right(a, x) → upper_bound
```

---

#### 7.6.5 滑动窗口模板

```python
def sliding_window(s: str) -> int:
    from collections import defaultdict
    
    window = defaultdict(int)
    left = 0
    result = 0
    
    for right in range(len(s)):
        # 扩大窗口
        c = s[right]
        window[c] += 1
        
        # 收缩窗口（根据条件）
        while 需要收缩:
            d = s[left]
            window[d] -= 1
            if window[d] == 0:
                del window[d]
            left += 1
        
        # 更新结果
        result = max(result, right - left + 1)
    
    return result

# 最小覆盖子串 - LeetCode 76
def minWindow(s: str, t: str) -> str:
    from collections import Counter
    
    need = Counter(t)
    window = Counter()
    have, need_cnt = 0, len(need)
    result = ""
    min_len = float('inf')
    left = 0
    
    for right in range(len(s)):
        c = s[right]
        if c in need:
            window[c] += 1
            if window[c] == need[c]:
                have += 1
        
        while have == need_cnt:
            if right - left + 1 < min_len:
                min_len = right - left + 1
                result = s[left:right + 1]
            
            d = s[left]
            if d in need:
                if window[d] == need[d]:
                    have -= 1
                window[d] -= 1
            left += 1
    
    return result
```

---

#### 7.6.6 BFS 模板

```python
from collections import deque

def bfs(start):
    queue = deque([start])
    visited = {start}
    level = 0
    
    while queue:
        size = len(queue)
        for _ in range(size):
            node = queue.popleft()
            
            # 处理当前节点
            if 是目标:
                return level
            
            for neighbor in get_neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        level += 1
    
    return -1  # 未找到

# 岛屿数量 - LeetCode 200
def numIslands(grid: list[list[str]]) -> int:
    if not grid:
        return 0
    
    rows, cols = len(grid), len(grid[0])
    count = 0
    
    def bfs(r, c):
        queue = deque([(r, c)])
        grid[r][c] = '0'  # 标记已访问
        
        while queue:
            row, col = queue.popleft()
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == '1':
                    grid[nr][nc] = '0'
                    queue.append((nr, nc))
    
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == '1':
                bfs(i, j)
                count += 1
    
    return count
```

---

#### 7.6.7 并查集模板

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.count = n  # 连通分量数
    
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

---

### 7.7 Python 刷题常用技巧

```python
# 1. 无穷大
float('inf'), float('-inf')

# 2. 默认字典
from collections import defaultdict
d = defaultdict(list)  # 默认值为空列表
d = defaultdict(int)   # 默认值为0

# 3. 计数器
from collections import Counter
c = Counter("aabbbc")  # {'b': 3, 'a': 2, 'c': 1}
c.most_common(2)       # [('b', 3), ('a', 2)]

# 4. 双端队列
from collections import deque
dq = deque([1, 2, 3])
dq.appendleft(0)  # 左侧添加
dq.popleft()      # 左侧弹出

# 5. 堆
import heapq
heapq.heapify(lst)         # 原地转换为堆
heapq.heappush(heap, x)    # 添加
heapq.heappop(heap)        # 弹出最小
heapq.nlargest(k, lst)     # 最大的k个
heapq.nsmallest(k, lst)    # 最小的k个

# 6. 排序
lst.sort(key=lambda x: x[1])  # 按第二个元素排序
lst.sort(key=lambda x: (-x[0], x[1]))  # 先按第一个降序，再按第二个升序

# 7. 二分查找
import bisect
bisect.bisect_left(lst, x)   # 第一个>=x的位置
bisect.bisect_right(lst, x)  # 第一个>x的位置
bisect.insort(lst, x)        # 插入并保持有序

# 8. 组合/排列
from itertools import permutations, combinations
list(permutations([1,2,3]))      # 全排列
list(combinations([1,2,3], 2))   # C(3,2)组合

# 9. 字符串
s.isalnum()   # 是否字母数字
s.isalpha()   # 是否字母
s.isdigit()   # 是否数字
ord('a')      # 字符转ASCII: 97
chr(97)       # ASCII转字符: 'a'

# 10. 列表推导式技巧
matrix = [[0] * n for _ in range(m)]  # m×n矩阵
flat = [x for row in matrix for x in row]  # 展平

# 11. zip 技巧
list(zip(*matrix))  # 矩阵转置
```

---

## 八、延伸阅读

- [Linux核心概念索引](/articles/00-glossary/glossary-01-linux-concepts/)
- [C++核心概念索引](/articles/00-glossary/glossary-05-cpp-concepts/)
- [HFT核心概念索引](/articles/00-glossary/glossary-04-hft-concepts/)
- [概率数据结构详解(HFT)](/articles/algorithm/algo-09-概率数据结构详解/)
- [在线算法与流式计算(HFT)](/articles/algorithm/algo-10-在线算法与流式计算/)
