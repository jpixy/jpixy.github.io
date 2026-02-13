+++
title = "Interview - STL Deep Dive"
date = 2026-01-21
weight = 38000
description = "C++ STL深度面试题汇总，包括容器、迭代器、算法、函数对象等核心概念"
[taxonomies]
tags = ["C++", "面试题", "STL", "容器", "算法"]
+++

## 一、容器

### Q1: vector和deque的区别？

| 特性 | vector | deque |
|------|--------|-------|
| 内存布局 | 连续 | 分段连续 |
| 前端插入 | O(n) | O(1) |
| 后端插入 | 摊还O(1) | O(1) |
| 随机访问 | O(1) | O(1) |
| 缓存友好性 | 好 | 较差 |

```cpp
std::vector<int> v;
v.push_back(1);    // O(1) 摊还
v.insert(v.begin(), 2);  // O(n)

std::deque<int> d;
d.push_back(1);    // O(1)
d.push_front(2);   // O(1)
```

### Q2: vector的capacity和size？

```cpp
std::vector<int> v;
v.size();      // 元素数量
v.capacity();  // 分配的容量

v.reserve(100);    // 预分配，不改变size
v.resize(100);     // 改变size，可能填充默认值
v.shrink_to_fit(); // 释放多余容量

// 内存增长策略：通常是2倍（GCC）或1.5倍（MSVC）
```

### Q3: map和unordered_map的区别？

| 特性 | map | unordered_map |
|------|-----|---------------|
| 实现 | 红黑树 | 哈希表 |
| 查找 | O(log n) | O(1) 平均 |
| 插入 | O(log n) | O(1) 平均 |
| 有序性 | 有序 | 无序 |
| 迭代顺序 | 按key排序 | 不确定 |

```cpp
std::map<std::string, int> m;         // 有序
std::unordered_map<std::string, int> um;  // 无序

// 自定义类型作为key
struct MyKey {
    int id;
    bool operator<(const MyKey& other) const {  // map需要
        return id < other.id;
    }
};

// unordered_map需要hash和==
namespace std {
    template<>
    struct hash<MyKey> {
        size_t operator()(const MyKey& k) const {
            return std::hash<int>{}(k.id);
        }
    };
}
```

### Q4: list和forward_list的区别？

```cpp
std::list<int> l;          // 双向链表
std::forward_list<int> fl; // 单向链表

// list可以双向遍历
auto it = l.end();
--it;  // OK

// forward_list只能前向遍历
// 没有size()成员函数（O(1) vs O(n)设计决策）
size_t sz = std::distance(fl.begin(), fl.end());  // O(n)
```

---

## 二、迭代器

### Q5: 迭代器类别？

```cpp
// 从弱到强：
// 1. Input Iterator: 只读，单遍
// 2. Output Iterator: 只写，单遍
// 3. Forward Iterator: 读写，多遍
// 4. Bidirectional Iterator: 双向移动
// 5. Random Access Iterator: 随机访问

// 容器的迭代器类型：
std::vector<int>::iterator;       // Random Access
std::list<int>::iterator;         // Bidirectional
std::forward_list<int>::iterator; // Forward
std::istream_iterator<int>;       // Input
std::ostream_iterator<int>;       // Output

// 迭代器操作
std::advance(it, n);       // 移动n步
std::distance(first, last);  // 距离
std::next(it, n);          // 返回移动后的迭代器
std::prev(it, n);          // 返回后退后的迭代器
```

### Q6: 迭代器失效？

```cpp
// vector
std::vector<int> v = {1, 2, 3, 4, 5};
auto it = v.begin() + 2;  // 指向3

v.push_back(6);  // 可能导致重新分配，所有迭代器失效
v.erase(v.begin());  // 被删除及之后的迭代器失效

// 正确删除方式
for (auto it = v.begin(); it != v.end(); ) {
    if (*it == 3) {
        it = v.erase(it);  // erase返回下一个有效迭代器
    } else {
        ++it;
    }
}

// map/set
std::map<int, int> m;
m.erase(it);  // 只有被删除的迭代器失效

// list
std::list<int> l;
l.erase(it);  // 只有被删除的迭代器失效
```

---

## 三、算法

### Q7: sort vs stable_sort？

```cpp
std::vector<std::pair<int, char>> v = {{1, 'a'}, {2, 'b'}, {1, 'c'}};

// sort: 不保证相等元素的相对顺序
std::sort(v.begin(), v.end(), [](auto& a, auto& b) {
    return a.first < b.first;
});
// 可能是 {1,'a'}, {1,'c'}, {2,'b'} 或 {1,'c'}, {1,'a'}, {2,'b'}

// stable_sort: 保证相等元素的相对顺序
std::stable_sort(v.begin(), v.end(), [](auto& a, auto& b) {
    return a.first < b.first;
});
// 一定是 {1,'a'}, {1,'c'}, {2,'b'}

// 复杂度：
// sort: O(n log n) 平均
// stable_sort: O(n log² n) 或 O(n log n) 如果有额外内存
```

### Q8: find vs binary_search？

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

// find: 线性查找，O(n)
auto it = std::find(v.begin(), v.end(), 3);

// binary_search: 二分查找，O(log n)，需要有序
bool found = std::binary_search(v.begin(), v.end(), 3);

// lower_bound/upper_bound: 找位置
auto lb = std::lower_bound(v.begin(), v.end(), 3);  // >=3的第一个
auto ub = std::upper_bound(v.begin(), v.end(), 3);  // >3的第一个
auto range = std::equal_range(v.begin(), v.end(), 3);  // 返回pair
```

### Q9: remove vs erase？

```cpp
std::vector<int> v = {1, 2, 3, 2, 4, 2, 5};

// remove: 移动元素，不改变容器大小
auto new_end = std::remove(v.begin(), v.end(), 2);
// v现在是 {1, 3, 4, 5, ?, ?, ?}，?是未指定值
// new_end指向逻辑结尾

// erase: 实际删除元素
v.erase(new_end, v.end());
// v现在是 {1, 3, 4, 5}

// Erase-Remove惯用法
v.erase(std::remove(v.begin(), v.end(), 2), v.end());

// C++20: std::erase
std::erase(v, 2);  // 直接删除所有2
```

---

## 四、函数对象

### Q10: 函数对象vs lambda？

```cpp
// 函数对象（functor）
struct IsEven {
    bool operator()(int x) const {
        return x % 2 == 0;
    }
};

auto count1 = std::count_if(v.begin(), v.end(), IsEven{});

// Lambda
auto count2 = std::count_if(v.begin(), v.end(), 
    [](int x) { return x % 2 == 0; });

// Lambda捕获
int threshold = 10;
auto count3 = std::count_if(v.begin(), v.end(),
    [threshold](int x) { return x > threshold; });

// Lambda是编译器生成的匿名函数对象
```

### Q11: std::function的开销？

```cpp
#include <functional>

// std::function有类型擦除开销
std::function<int(int)> f = [](int x) { return x * 2; };
f(42);  // 可能有间接调用开销

// 小对象优化（SOO）：小lambda可能不需要堆分配
// 但虚函数调用开销仍然存在

// 性能敏感代码使用模板
template<typename F>
void process(F&& f) {
    f(42);  // 可以内联
}
```

---

## 五、容器适配器

### Q12: stack、queue、priority_queue？

```cpp
// 容器适配器使用底层容器实现
std::stack<int> s;              // 默认用deque
std::stack<int, std::vector<int>> sv;  // 用vector

std::queue<int> q;              // 默认用deque
std::priority_queue<int> pq;    // 默认用vector，最大堆

// priority_queue使用
std::priority_queue<int, std::vector<int>, std::greater<int>> min_heap;

pq.push(3);
pq.push(1);
pq.push(4);
pq.top();   // 4（最大元素）
pq.pop();   // 移除4
```

---

## 六、智能指针

### Q13: shared_ptr的循环引用？

```cpp
class Node {
public:
    std::shared_ptr<Node> next;
    std::shared_ptr<Node> prev;  // 循环引用！
};

auto n1 = std::make_shared<Node>();
auto n2 = std::make_shared<Node>();
n1->next = n2;
n2->prev = n1;
// n1和n2永远不会被释放！

// 解决：使用weak_ptr
class Node {
public:
    std::shared_ptr<Node> next;
    std::weak_ptr<Node> prev;  // 不增加引用计数
};

// 使用weak_ptr
if (auto p = prev.lock()) {
    // p是shared_ptr，对象还存在
}
```

### Q14: make_shared vs new？

```cpp
// 推荐make_shared
auto p1 = std::make_shared<Widget>();
// 一次分配：对象和控制块在一起

// 不推荐
auto p2 = std::shared_ptr<Widget>(new Widget());
// 两次分配：对象和控制块分开

// make_shared的额外好处：
// 1. 更高效（单次分配）
// 2. 异常安全
// 3. 更好的缓存局部性

// make_shared的缺点：
// 1. 不能使用自定义deleter
// 2. weak_ptr持有时内存不释放
```

---

## 七、其他

### Q15: emplace vs push/insert？

```cpp
std::vector<std::pair<int, std::string>> v;

// push_back: 需要先构造pair
v.push_back(std::make_pair(1, "one"));  // 可能有移动

// emplace_back: 直接在容器内构造
v.emplace_back(1, "one");  // 无临时对象

// map的emplace
std::map<int, std::string> m;
m.emplace(1, "one");  // 直接构造键值对

// 完美转发
template<typename... Args>
void emplace_back(Args&&... args) {
    new (end_ptr) T(std::forward<Args>(args)...);
}
```

---

## 面试技巧

1. **容器选择**：根据操作特征选择容器
2. **迭代器失效**：这是高频考点，记住各容器规则
3. **算法复杂度**：了解常用算法的时间复杂度
4. **智能指针**：理解循环引用问题
5. **emplace**：解释完美转发优化

---

## 相关文章

- [上一篇：Interview - Concurrency and Multithreading](@/articles/cpp/cpp-37-C++面试题-并发与多线程.md)
- [下一篇：Interview - System Design (HFT)](@/articles/cpp/cpp-39-HFT-C++面试题-系统设计篇.md)
