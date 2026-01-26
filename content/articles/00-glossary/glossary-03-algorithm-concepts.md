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

### 2.3 Heap (堆)

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

## 六、延伸阅读

- [Linux核心概念索引](/articles/00-glossary/glossary-01-linux-concepts/)
- [HFT核心概念索引](/articles/00-glossary/glossary-04-hft-concepts/)
- [概率数据结构详解(HFT)](/articles/algorithm/algo-09-概率数据结构详解/)
- [在线算法与流式计算(HFT)](/articles/algorithm/algo-10-在线算法与流式计算/)
