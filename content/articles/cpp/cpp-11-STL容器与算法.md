+++
title = "11.STL容器与算法"
date = 2026-01-19
description = "STL详解：序列容器、关联容器、容器适配器、迭代器、常用算法"
[taxonomies]
tags = ["C++", "STL", "容器"]
+++

## 序列容器

### vector

**动态数组，连续存储**：

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

v.push_back(6);      // 尾部插入 O(1)摊还
v.pop_back();        // 尾部删除 O(1)
v[0] = 10;           // 随机访问 O(1)
v.insert(v.begin(), 0);  // 头部插入 O(n)
v.erase(v.begin());      // 头部删除 O(n)

v.reserve(100);      // 预分配容量
v.resize(50);        // 改变大小
v.shrink_to_fit();   // 释放多余容量
```

**适用场景**：随机访问多、尾部增删多

### deque

**双端队列，分段连续**：

```cpp
std::deque<int> d = {1, 2, 3};

d.push_front(0);     // 头部插入 O(1)
d.push_back(4);      // 尾部插入 O(1)
d.pop_front();       // 头部删除 O(1)
d.pop_back();        // 尾部删除 O(1)
d[1] = 10;           // 随机访问 O(1)
```

**适用场景**：两端频繁增删

### list

**双向链表**：

```cpp
std::list<int> l = {1, 2, 3};

l.push_front(0);     // 头部插入 O(1)
l.push_back(4);      // 尾部插入 O(1)
l.insert(it, 5);     // 中间插入 O(1)
l.erase(it);         // 删除 O(1)
l.splice(pos, other);  // 拼接 O(1)
l.sort();            // 排序
l.merge(other);      // 合并有序链表
```

**适用场景**：频繁中间插入删除、需要稳定迭代器

### array

**固定大小数组**：

```cpp
std::array<int, 5> arr = {1, 2, 3, 4, 5};

arr[0] = 10;         // 随机访问 O(1)
arr.size();          // 5
arr.data();          // 底层指针
```

**适用场景**：编译期确定大小

### forward_list

**单向链表**：

```cpp
std::forward_list<int> fl = {1, 2, 3};

fl.push_front(0);    // 头部插入 O(1)
fl.insert_after(it, 5);  // 在it后插入
fl.erase_after(it);      // 删除it后的元素
```

**适用场景**：内存受限、只需单向遍历

---

## 关联容器

### set/multiset

**红黑树，有序**：

```cpp
std::set<int> s = {3, 1, 4, 1, 5};  // {1, 3, 4, 5} 自动去重排序

s.insert(2);         // 插入 O(log n)
s.erase(3);          // 删除 O(log n)
s.find(4);           // 查找 O(log n)
s.count(1);          // 计数 O(log n)

// multiset 允许重复
std::multiset<int> ms = {1, 1, 2, 2};
```

### map/multimap

**红黑树，键值对**：

```cpp
std::map<std::string, int> m = {{"a", 1}, {"b", 2}};

m["c"] = 3;          // 插入或更新 O(log n)
m.insert({"d", 4});  // 插入
m.at("a");           // 访问（不存在抛异常）
m.find("b");         // 查找 O(log n)
m.erase("a");        // 删除 O(log n)

// 遍历按键有序
for (const auto& [key, value] : m) {
    std::cout << key << ": " << value << std::endl;
}
```

### unordered_set/unordered_map

**哈希表，无序**：

```cpp
std::unordered_set<int> us = {3, 1, 4};

us.insert(2);        // 插入 O(1)平均
us.find(3);          // 查找 O(1)平均
us.erase(1);         // 删除 O(1)平均

std::unordered_map<std::string, int> um;
um["key"] = 123;     // O(1)平均

// 自定义哈希
struct MyHash {
    size_t operator()(const MyType& obj) const {
        return std::hash<int>{}(obj.id);
    }
};
std::unordered_set<MyType, MyHash> custom_set;
```

**选择指南**：

| 需求 | 选择 |
|------|------|
| 有序、范围查询 | set/map |
| 无序、最快查找 | unordered_set/unordered_map |

---

## 容器适配器

### stack

```cpp
std::stack<int> s;

s.push(1);           // 入栈
s.pop();             // 出栈（不返回值）
s.top();             // 栈顶
s.empty();           // 是否为空
```

### queue

```cpp
std::queue<int> q;

q.push(1);           // 入队
q.pop();             // 出队
q.front();           // 队首
q.back();            // 队尾
```

### priority_queue

```cpp
std::priority_queue<int> pq;  // 最大堆

pq.push(3);
pq.push(1);
pq.push(4);
pq.top();            // 4（最大值）
pq.pop();

// 最小堆
std::priority_queue<int, std::vector<int>, std::greater<int>> min_pq;
```

---

## 迭代器

### 迭代器类别

| 类别 | 能力 | 容器 |
|------|------|------|
| 输入迭代器 | 读取、前进 | istream_iterator |
| 输出迭代器 | 写入、前进 | ostream_iterator |
| 前向迭代器 | 读写、前进 | forward_list |
| 双向迭代器 | 读写、前进后退 | list, set, map |
| 随机访问迭代器 | 读写、随机跳转 | vector, deque, array |

### 迭代器操作

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

auto it = v.begin();
std::advance(it, 2);       // 移动2步
std::next(it);             // 返回下一个位置
std::prev(it);             // 返回上一个位置
std::distance(v.begin(), it);  // 计算距离
```

### 迭代器失效

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

// 插入可能导致所有迭代器失效
v.push_back(6);

// 删除导致被删除及之后的迭代器失效
v.erase(v.begin() + 2);

// 安全删除模式
for (auto it = v.begin(); it != v.end(); ) {
    if (*it == 3) {
        it = v.erase(it);  // erase返回下一个有效迭代器
    } else {
        ++it;
    }
}
```

---

## 常用算法

### 查找

```cpp
#include <algorithm>

std::vector<int> v = {1, 2, 3, 4, 5};

std::find(v.begin(), v.end(), 3);         // 查找值
std::find_if(v.begin(), v.end(), pred);   // 查找满足条件的
std::binary_search(v.begin(), v.end(), 3);  // 二分查找（需有序）
std::lower_bound(v.begin(), v.end(), 3);  // 第一个>=的位置
std::upper_bound(v.begin(), v.end(), 3);  // 第一个>的位置
```

### 排序

```cpp
std::sort(v.begin(), v.end());            // 排序
std::sort(v.begin(), v.end(), std::greater<int>());  // 降序
std::partial_sort(v.begin(), v.begin()+3, v.end());  // 部分排序
std::nth_element(v.begin(), v.begin()+n, v.end());   // 第n大元素
std::stable_sort(v.begin(), v.end());     // 稳定排序
```

### 变换

```cpp
std::transform(v.begin(), v.end(), v.begin(), [](int x) { return x * 2; });

std::copy(v.begin(), v.end(), result.begin());
std::copy_if(v.begin(), v.end(), result.begin(), pred);

std::replace(v.begin(), v.end(), 3, 10);  // 将3替换为10
std::replace_if(v.begin(), v.end(), pred, 10);

std::remove(v.begin(), v.end(), 3);       // 移除（配合erase使用）
v.erase(std::remove(v.begin(), v.end(), 3), v.end());

std::unique(v.begin(), v.end());          // 去重（需先排序）
```

### 聚合

```cpp
std::accumulate(v.begin(), v.end(), 0);   // 求和
std::accumulate(v.begin(), v.end(), 1, std::multiplies<int>());  // 求积

std::count(v.begin(), v.end(), 3);        // 计数
std::count_if(v.begin(), v.end(), pred);

std::min_element(v.begin(), v.end());     // 最小值迭代器
std::max_element(v.begin(), v.end());     // 最大值迭代器
std::minmax_element(v.begin(), v.end());  // 同时获取
```

### 其他

```cpp
std::reverse(v.begin(), v.end());         // 反转
std::rotate(v.begin(), v.begin()+2, v.end());  // 旋转
std::shuffle(v.begin(), v.end(), gen);    // 随机打乱
std::next_permutation(v.begin(), v.end());  // 下一个排列

std::all_of(v.begin(), v.end(), pred);    // 全部满足
std::any_of(v.begin(), v.end(), pred);    // 存在满足
std::none_of(v.begin(), v.end(), pred);   // 全不满足

std::for_each(v.begin(), v.end(), [](int x) { std::cout << x; });
```

---

## 容器选择指南

| 操作 | vector | deque | list | set | unordered_set |
|------|--------|-------|------|-----|---------------|
| 随机访问 | O(1) | O(1) | O(n) | O(log n) | O(1) |
| 头部插入 | O(n) | O(1) | O(1) | - | - |
| 尾部插入 | O(1) | O(1) | O(1) | - | - |
| 中间插入 | O(n) | O(n) | O(1) | O(log n) | O(1) |
| 查找 | O(n) | O(n) | O(n) | O(log n) | O(1) |
| 有序 | 否 | 否 | 否 | 是 | 否 |

**默认选择vector**，除非有特殊需求。

---

## 总结

| 类别 | 容器 | 特点 |
|------|------|------|
| 序列容器 | vector | 连续存储、随机访问 |
| 序列容器 | deque | 双端操作 |
| 序列容器 | list | 任意位置插入删除 |
| 关联容器 | set/map | 有序、红黑树 |
| 关联容器 | unordered_* | 无序、哈希表 |
| 适配器 | stack/queue/priority_queue | 特定访问模式 |

STL是C++的核心库，熟练使用可以大大提高开发效率和代码质量。
