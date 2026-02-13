+++
title = "19. Rust面试指南"
date = 2026-01-19
weight = 19000
description = "Rust面试高频问题：所有权、生命周期、并发、智能指针、性能"
[taxonomies]
tags = ["Rust", "面试", "指南"]
+++

## 所有权相关

### 解释Rust的所有权规则？

**三条核心规则**：
1. 每个值有且仅有一个所有者
2. 同一时刻只能有一个所有者
3. 所有者离开作用域时，值被丢弃

```rust
let s1 = String::from("hello");
let s2 = s1;  // s1移动到s2
// s1不再有效
```

### Move和Copy的区别？

**Move**：
- 转移所有权，原变量失效
- 默认行为
- 适用于堆分配类型

**Copy**：
- 按位复制，原变量仍有效
- 需实现Copy trait
- 仅适用于栈上简单类型（整数、浮点、布尔等）

```rust
// Copy
let x = 5;
let y = x;  // x仍有效

// Move
let s1 = String::from("hello");
let s2 = s1;  // s1失效
```

### Clone和Copy的区别？

| | Copy | Clone |
|---|------|-------|
| 隐式 | 是 | 否 |
| 开销 | 低（按位复制） | 可能高（深拷贝） |
| 要求 | 类型和所有字段都是Copy | 实现Clone trait |

### 什么是借用？

**借用**：通过引用访问数据，不转移所有权。

```rust
fn calculate_length(s: &String) -> usize {  // 借用
    s.len()
}

let s = String::from("hello");
let len = calculate_length(&s);  // s仍有效
```

### 借用规则是什么？

在同一作用域内：
- 可以有多个不可变引用
- 只能有一个可变引用
- 不能同时有可变和不可变引用

```rust
let mut s = String::from("hello");

let r1 = &s;      // OK
let r2 = &s;      // OK
// let r3 = &mut s;  // 错误！

println!("{} {}", r1, r2);
// r1, r2作用域结束

let r3 = &mut s;  // OK
```

---

## 生命周期相关

### 什么是生命周期？

生命周期是引用有效的作用域。编译器通过生命周期确保引用不会悬垂。

### 为什么需要生命周期标注？

当函数有多个引用参数且返回引用时，编译器需要知道返回引用的生命周期。

```rust
// 编译器无法推断
fn longest(x: &str, y: &str) -> &str {  // 错误！
    if x.len() > y.len() { x } else { y }
}

// 需要标注
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

### 生命周期省略规则？

1. 每个引用参数获得独立生命周期
2. 如果只有一个输入生命周期，赋给所有输出
3. 如果有&self，self的生命周期赋给输出

### 'static生命周期是什么？

表示整个程序运行期间有效。

```rust
let s: &'static str = "hello";  // 字符串字面量
```

---

## 并发相关

### Send和Sync trait？

**Send**：可以跨线程转移所有权
**Sync**：可以被多线程安全访问（&T是Send）

```rust
// 大多数类型自动实现
// Rc不是Send（非原子引用计数）
// RefCell不是Sync（运行时借用检查非线程安全）
```

### Arc和Rc的区别？

| | Rc | Arc |
|---|-----|-----|
| 引用计数 | 非原子 | 原子 |
| 线程安全 | 否 | 是 |
| 性能 | 更快 | 略慢 |
| 用途 | 单线程共享 | 多线程共享 |

### Mutex和RwLock？

**Mutex**：互斥锁，同时只有一个访问者

**RwLock**：读写锁，多读或单写

```rust
use std::sync::{Arc, Mutex, RwLock};

let data = Arc::new(Mutex::new(0));
let data = Arc::new(RwLock::new(0));
```

### async/await如何工作？

- async函数返回实现Future的类型
- await挂起当前任务，等待Future完成
- 需要运行时（tokio/async-std）执行

```rust
async fn fetch() -> String {
    "data".to_string()
}

async fn process() {
    let data = fetch().await;
}
```

---

## 智能指针

### Box、Rc、Arc的用途？

| 类型 | 用途 |
|------|------|
| Box | 堆分配、递归类型 |
| Rc | 单线程共享所有权 |
| Arc | 多线程共享所有权 |

### RefCell的作用？

内部可变性：在不可变引用下修改数据。

```rust
use std::cell::RefCell;

let data = RefCell::new(5);
*data.borrow_mut() += 1;  // 运行时借用检查
```

### Cow是什么？

Clone on Write：延迟克隆，只在需要修改时克隆。

```rust
use std::borrow::Cow;

fn process(s: Cow<str>) -> Cow<str> {
    if needs_modification(&s) {
        Cow::Owned(s.into_owned().to_uppercase())
    } else {
        s
    }
}
```

---

## 类型系统

### trait和interface的区别？

| Rust Trait | 接口 |
|------------|------|
| 可以有默认实现 | 通常不能 |
| 可以为现有类型实现 | 不能 |
| 支持关联类型 | 通常不支持 |
| 编译期分派（泛型）或运行时（trait对象） | 通常运行时 |

### 泛型和trait对象的区别？

| 泛型 | Trait对象 |
|------|-----------|
| 静态分派 | 动态分派 |
| 编译期确定类型 | 运行期确定类型 |
| 无运行时开销 | 有vtable开销 |
| 代码膨胀 | 代码更小 |

```rust
// 泛型（静态分派）
fn process<T: Display>(item: T) {}

// trait对象（动态分派）
fn process(item: &dyn Display) {}
```

### 什么是关联类型？

trait中定义的占位类型，实现时确定。

```rust
trait Iterator {
    type Item;  // 关联类型
    fn next(&mut self) -> Option<Self::Item>;
}

impl Iterator for Counter {
    type Item = u32;
    fn next(&mut self) -> Option<Self::Item> {
        // ...
    }
}
```

---

## 错误处理

### panic和Result的区别？

| panic | Result |
|-------|--------|
| 不可恢复错误 | 可恢复错误 |
| 终止程序 | 返回值 |
| 用于bug | 用于预期错误 |

### ?操作符做什么？

提前返回Err或解包Ok。

```rust
fn read_file() -> Result<String, io::Error> {
    let content = std::fs::read_to_string("file.txt")?;
    Ok(content)
}

// 等价于
fn read_file() -> Result<String, io::Error> {
    let content = match std::fs::read_to_string("file.txt") {
        Ok(c) => c,
        Err(e) => return Err(e),
    };
    Ok(content)
}
```

---

## 性能相关

### 零成本抽象是什么意思？

高级抽象不引入运行时开销，编译后与手写底层代码一样高效。

例如：
- 迭代器和for循环一样快
- trait的泛型实现零开销

### 如何避免不必要的克隆？

1. 使用引用而非所有权
2. 使用Cow延迟克隆
3. 使用迭代器而非collect
4. 考虑Arc共享而非克隆

### 什么是内联？

将函数体直接插入调用处，避免函数调用开销。

```rust
#[inline]
fn small_function() {}

#[inline(always)]
fn always_inline() {}
```

---

## 代码示例

### 实现一个简单的智能指针

```rust
use std::ops::Deref;

struct MyBox<T>(T);

impl<T> MyBox<T> {
    fn new(x: T) -> MyBox<T> {
        MyBox(x)
    }
}

impl<T> Deref for MyBox<T> {
    type Target = T;
    
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}
```

### 实现迭代器

```rust
struct Counter {
    count: u32,
}

impl Iterator for Counter {
    type Item = u32;
    
    fn next(&mut self) -> Option<Self::Item> {
        if self.count < 5 {
            self.count += 1;
            Some(self.count)
        } else {
            None
        }
    }
}
```

### 使用闭包和高阶函数

```rust
let numbers: Vec<i32> = (1..=10).collect();

let sum: i32 = numbers.iter()
    .filter(|&&x| x % 2 == 0)
    .map(|&x| x * x)
    .sum();
```

---

## 面试技巧

### 展示理解

- 解释为什么Rust这样设计
- 讨论权衡
- 举例说明

### 常见陷阱

- 不要混淆&str和String
- 理解move闭包的含义
- 注意生命周期约束

### 准备建议

1. 完成The Rust Book
2. 做Rustlings练习
3. 阅读标准库源码
4. 写一个小项目

---

## 总结

| 领域 | 重点 |
|------|------|
| 所有权 | 移动、借用、生命周期 |
| 并发 | Send/Sync、Arc/Mutex |
| 智能指针 | Box/Rc/Arc/RefCell |
| 类型系统 | 泛型、trait、关联类型 |
| 错误处理 | Result、?操作符 |
| 性能 | 零成本抽象、内联 |

Rust面试重点考察对所有权和生命周期的理解，以及如何利用类型系统保证安全。

---

## 相关文章

- [上一篇：Rust宏系统详解](@/articles/rust/rust-18-Rust宏系统详解.md)
- [下一篇：Rust面试题-所有权与生命周期](@/articles/rust/rust-20-Rust面试题-所有权与生命周期.md)
