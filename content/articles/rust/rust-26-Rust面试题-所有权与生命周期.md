+++
title = "19.Rust面试题-所有权与生命周期"
slug = "rust-19-Rust面试题-所有权与生命周期"
date = 2026-01-21
description = "Rust面试中关于所有权和生命周期的常见问题，包括借用规则、生命周期省略、NLL、self-referential struct和Pin"
[taxonomies]
tags = ["Rust", "面试", "所有权", "生命周期", "Pin"]
+++

## 概述

所有权和生命周期是Rust面试的核心考点。本文汇集常见问题和深入解答。

---

## 一、所有权基础

### Q1: 解释Rust的所有权规则

```rust
// Rust的三条所有权规则：

// 1. 每个值有且只有一个所有者
let s1 = String::from("hello");
let s2 = s1;  // 所有权转移给s2
// println!("{}", s1);  // 错误：s1不再有效

// 2. 当所有者离开作用域，值被丢弃
{
    let s = String::from("hello");
}  // s在这里被drop

// 3. 同一时间，要么有一个可变引用，要么有多个不可变引用
let mut s = String::from("hello");
let r1 = &s;      // OK
let r2 = &s;      // OK
// let r3 = &mut s;  // 错误：已存在不可变引用
println!("{}, {}", r1, r2);
let r3 = &mut s;  // OK：r1, r2不再使用
```

### Q2: Copy和Clone的区别

```rust
// Copy: 按位复制，隐式调用
// - 要求类型的所有字段都是Copy
// - 不能自定义复制行为
// - 典型：基本类型、不含堆数据的类型

#[derive(Copy, Clone)]
struct Point { x: i32, y: i32 }

let p1 = Point { x: 1, y: 2 };
let p2 = p1;  // 复制，p1仍有效
println!("{}", p1.x);  // OK

// Clone: 显式复制，可能昂贵
// - 可以自定义复制逻辑
// - 可能涉及堆分配

#[derive(Clone)]
struct Data { values: Vec<i32> }

let d1 = Data { values: vec![1, 2, 3] };
let d2 = d1.clone();  // 显式调用，深拷贝
// let d3 = d1;  // 移动，不是复制

// 重要：Copy是Clone的子trait
// Copy类型必须实现Clone
```

### Q3: 什么时候发生移动？

```rust
// 移动发生的场景：

// 1. 赋值
let s1 = String::from("hello");
let s2 = s1;  // 移动

// 2. 函数参数
fn takes_ownership(s: String) {}
takes_ownership(s2);  // 移动

// 3. 返回值（返回局部变量）
fn creates_string() -> String {
    String::from("hello")  // 移动给调用者
}

// 4. 结构体/元组字段赋值
struct Container { data: String }
let c = Container { data: String::from("hello") };
let data = c.data;  // 部分移动

// 不发生移动的情况：
// - Copy类型
// - 借用（&T, &mut T）
// - 解引用赋值（*ptr = ...）
```

---

## 二、借用规则

### Q4: 解释可变借用和不可变借用的规则

```rust
// 规则：同一时间内
// - 可以有多个不可变借用
// - 只能有一个可变借用
// - 不能同时存在可变和不可变借用

fn main() {
    let mut data = vec![1, 2, 3];
    
    // 多个不可变借用OK
    let r1 = &data;
    let r2 = &data;
    println!("{:?}, {:?}", r1, r2);
    
    // 可变借用（r1, r2不再使用）
    let r3 = &mut data;
    r3.push(4);
    
    // NLL：借用的生命周期在最后一次使用处结束
}
```

### Q5: 什么是NLL（Non-Lexical Lifetimes）？

```rust
// NLL之前：借用持续到作用域结束
fn old_behavior() {
    let mut data = vec![1, 2, 3];
    let r = &data[0];
    println!("{}", r);
    // 在旧版本中，r的借用持续到这里
    // data.push(4);  // 以前会报错
}

// NLL之后：借用在最后一次使用处结束
fn new_behavior() {
    let mut data = vec![1, 2, 3];
    let r = &data[0];
    println!("{}", r);
    // r的借用在这里结束
    data.push(4);  // 现在OK
}

// NLL更智能地跟踪借用
fn conditional_borrow(data: &mut Vec<i32>, flag: bool) {
    if flag {
        let r = &data[0];
        println!("{}", r);
        // r的借用只在这个分支内
    }
    data.push(4);  // OK，r不在这个作用域
}
```

### Q6: reborrow是什么？

```rust
fn main() {
    let mut data = String::from("hello");
    let r1 = &mut data;
    
    // 隐式reborrow
    takes_ref(r1);  // r1被reborrow为&mut String
    r1.push_str("!");  // r1仍然有效
    
    // 显式reborrow
    let r2 = &mut *r1;  // 从r1创建新的可变借用
    // r1暂时不能使用
    r2.push_str(" world");
    // r2结束后r1恢复
}

fn takes_ref(s: &mut String) {
    s.push_str(" from fn");
}
```

---

## 三、生命周期

### Q7: 生命周期省略规则

```rust
// 编译器自动添加生命周期的三条规则：

// 规则1：每个引用参数获得独立的生命周期
fn foo(x: &i32, y: &i32) {}
// 等价于：
fn foo_explicit<'a, 'b>(x: &'a i32, y: &'b i32) {}

// 规则2：如果只有一个输入生命周期，它被赋给所有输出
fn bar(x: &i32) -> &i32 { x }
// 等价于：
fn bar_explicit<'a>(x: &'a i32) -> &'a i32 { x }

// 规则3：如果是方法且有&self或&mut self，self的生命周期赋给输出
impl MyStruct {
    fn method(&self, x: &str) -> &str { &self.data }
    // 等价于：
    fn method_explicit<'a, 'b>(&'a self, x: &'b str) -> &'a str { &self.data }
}

struct MyStruct { data: String }

// 当规则不适用时必须显式标注
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

### Q8: 'static生命周期

```rust
// 'static表示整个程序运行期间都有效

// 字符串字面量是'static
let s: &'static str = "hello";

// 常量是'static
static CONFIG: &str = "config";

// Box::leak创建'static引用
let leaked: &'static String = Box::leak(Box::new(String::from("hello")));

// 泛型约束中的'static
fn spawn_thread<F>(f: F)
where
    F: FnOnce() + Send + 'static
{
    std::thread::spawn(f);
}

// 注意：'static不一定是编译时常量
// 它只是表示生命周期足够长
```

### Q9: 生命周期协变和逆变

```rust
// 协变（Covariant）：如果 'long: 'short，则 &'long T 可以用于 &'short T
fn covariant<'a>(long: &'a str) {
    let short: &str = long;  // OK：更长的生命周期可以缩短
}

// 逆变（Contravariant）：函数参数位置
// fn(&'short T) 可以用于 fn(&'long T)

// 不变（Invariant）：&mut T 对 T 是不变的
fn invariant<'a>(data: &mut &'a str) {
    // 不能将 &'short str 赋值给 &mut &'long str
}

// Cell<T> 对 T 也是不变的
use std::cell::Cell;

fn cell_invariant<'a>(cell: Cell<&'a str>) {
    // Cell的内容不能改变生命周期
}
```

---

## 四、Self-Referential Struct

### Q10: 为什么自引用结构体困难？

```rust
// 尝试创建自引用结构体
struct SelfRef {
    data: String,
    ptr: *const String,  // 指向data
}

impl SelfRef {
    fn new(data: String) -> Self {
        let mut s = Self {
            data,
            ptr: std::ptr::null(),
        };
        s.ptr = &s.data;
        s  // 问题：返回时s会移动，ptr失效！
    }
}

// 问题：Rust的移动语义
// 当SelfRef被移动时，data的地址改变，但ptr仍指向旧地址

// 解决方案：
// 1. 使用索引而非指针
// 2. 使用Pin固定内存位置
// 3. 使用rental/ouroboros等库
```

### Q11: Pin如何解决自引用问题？

```rust
use std::pin::Pin;
use std::marker::PhantomPinned;

struct SelfRefPinned {
    data: String,
    ptr: *const String,
    _marker: PhantomPinned,  // 使类型!Unpin
}

impl SelfRefPinned {
    fn new(data: String) -> Pin<Box<Self>> {
        let s = Self {
            data,
            ptr: std::ptr::null(),
            _marker: PhantomPinned,
        };
        
        let mut boxed = Box::pin(s);
        
        // 安全地设置自引用
        let ptr = &boxed.data as *const String;
        unsafe {
            let mut_ref = Pin::as_mut(&mut boxed);
            Pin::get_unchecked_mut(mut_ref).ptr = ptr;
        }
        
        boxed
    }
    
    fn data(self: Pin<&Self>) -> &str {
        &self.get_ref().data
    }
    
    fn ptr_data(self: Pin<&Self>) -> &str {
        unsafe { &*self.ptr }
    }
}

fn main() {
    let s = SelfRefPinned::new(String::from("hello"));
    println!("{}", s.as_ref().data());
    println!("{}", s.as_ref().ptr_data());
}
```

### Q12: Unpin trait是什么？

```rust
use std::pin::Pin;

// Unpin: 类型可以安全地从Pin中移出
// 大多数类型都是Unpin

struct Normal {
    data: i32,
}

fn unpin_example() {
    let mut pinned = Box::pin(Normal { data: 42 });
    
    // 因为Normal: Unpin，可以获取&mut
    let mut_ref: &mut Normal = &mut *pinned;
    mut_ref.data = 100;
    
    // 甚至可以移动
    let moved = *Pin::into_inner(pinned);
}

// !Unpin: 类型不能从Pin中移出
// - 自引用类型
// - Future（异步）

use std::marker::PhantomPinned;

struct NotUnpin {
    _marker: PhantomPinned,
}

fn not_unpin_example() {
    let pinned = Box::pin(NotUnpin { _marker: PhantomPinned });
    
    // 不能获取&mut（除非unsafe）
    // let mut_ref: &mut NotUnpin = &mut *pinned;  // 错误
}
```

---

## 五、高级问题

### Q13: HRTB（Higher-Ranked Trait Bounds）

```rust
// for<'a> 表示"对于任意生命周期'a"

// 普通约束：F必须接受特定生命周期的引用
fn call_with_ref<'a, F>(f: F, s: &'a str)
where
    F: Fn(&'a str)
{
    f(s);
}

// HRTB：F必须接受任意生命周期的引用
fn call_with_any_ref<F>(f: F, s: &str)
where
    F: for<'a> Fn(&'a str)  // HRTB
{
    f(s);
}

// 常见场景：闭包参数
fn process<F>(f: F)
where
    F: for<'a> Fn(&'a str) -> &'a str
{
    let s = String::from("hello");
    let result = f(&s);
    println!("{}", result);
}

fn main() {
    // 闭包自动满足HRTB
    process(|s| s);
}
```

### Q14: GAT（Generic Associated Types）

```rust
// GAT允许关联类型带有生命周期参数

trait LendingIterator {
    type Item<'a> where Self: 'a;
    
    fn next(&mut self) -> Option<Self::Item<'_>>;
}

// 实现
struct WindowsMut<'a, T> {
    data: &'a mut [T],
    pos: usize,
    size: usize,
}

impl<'a, T> LendingIterator for WindowsMut<'a, T> {
    type Item<'b> = &'b mut [T] where Self: 'b;
    
    fn next(&mut self) -> Option<Self::Item<'_>> {
        if self.pos + self.size > self.data.len() {
            return None;
        }
        let window = &mut self.data[self.pos..self.pos + self.size];
        self.pos += 1;
        Some(window)
    }
}
```

---

## 总结

| 概念 | 要点 |
|------|------|
| 所有权 | 单一所有者，移动语义 |
| 借用 | 可变/不可变互斥 |
| NLL | 借用在最后使用处结束 |
| 生命周期 | 确保引用有效 |
| Pin | 固定内存位置 |
| HRTB | 任意生命周期约束 |

**面试技巧**：
1. 能解释编译器错误信息
2. 理解为什么规则存在
3. 知道如何解决常见问题
4. 了解高级特性的用途
