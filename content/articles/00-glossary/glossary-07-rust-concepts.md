+++
title = "07. Rust Concepts"
description = "Rust核心概念速查：所有权、借用、生命周期、trait、unsafe等关键概念详解"
date = 2026-01-26
weight = 7000
draft = false
[taxonomies]
tags = ["Glossary", "Rust", "Memory Safety", "Reference"]
+++

# Rust Concepts

本索引收录Rust的核心概念，重点关注所有权系统和高性能编程。

---

## 一、所有权系统

### 1.1 Ownership (所有权)

**定义**：Rust的核心内存管理机制。每个值有且只有一个所有者，所有者离开作用域时值被释放。

**三条规则**：
1. 每个值有且只有一个所有者
2. 任一时刻只能有一个可变引用或多个不可变引用
3. 引用必须始终有效

```rust
fn main() {
    let s1 = String::from("hello");  // s1拥有字符串
    let s2 = s1;                      // 所有权转移给s2
    // println!("{}", s1);           // 错误：s1不再有效
    println!("{}", s2);              // OK
}  // s2离开作用域，字符串被释放
```

**移动(Move) vs 复制(Copy)**：
```rust
// 实现Copy trait的类型会复制
let x = 5;
let y = x;   // 复制，x仍有效
println!("{} {}", x, y);  // OK

// 堆分配类型会移动
let s1 = String::from("hello");
let s2 = s1;  // 移动，s1失效
```

**详细文章**：[所有权与借用](@/articles/rust/rust-02-所有权与借用.md)

---

### 1.2 Borrowing (借用)

**定义**：通过引用访问值而不获取所有权。

**两种借用**：
```rust
fn main() {
    let mut s = String::from("hello");
    
    // 不可变借用：可以有多个
    let r1 = &s;
    let r2 = &s;
    println!("{} {}", r1, r2);  // OK
    
    // 可变借用：只能有一个
    let r3 = &mut s;
    r3.push_str(" world");
    println!("{}", r3);  // OK
    
    // 不能同时存在可变和不可变借用
    // let r4 = &s;         // 错误
    // println!("{}", r4);
}
```

**借用检查器(Borrow Checker)**：
- 编译时验证借用规则
- 防止数据竞争、悬垂引用
- 零运行时开销

---

### 1.3 Lifetime (生命周期)

**定义**：引用有效的作用域。编译器通过生命周期确保引用不会悬垂。

**生命周期标注**：
```rust
// 函数签名中的生命周期
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// 含义：返回的引用与x、y中较短的生命周期相同
```

**生命周期省略规则**：
```rust
// 这些可以省略生命周期标注
fn first_word(s: &str) -> &str { ... }

// 编译器推断为
fn first_word<'a>(s: &'a str) -> &'a str { ... }
```

**结构体中的生命周期**：
```rust
struct ImportantExcerpt<'a> {
    part: &'a str,  // 结构体不能比part引用的数据活得长
}

fn main() {
    let novel = String::from("Call me Ishmael...");
    let first_sentence = novel.split('.').next().unwrap();
    let excerpt = ImportantExcerpt { part: first_sentence };
}  // excerpt和novel同时失效，OK
```

**详细文章**：[生命周期详解](@/articles/rust/rust-03-生命周期详解.md)

---

## 二、类型系统

### 2.1 Trait

**定义**：定义共享行为的接口，类似其他语言的interface。

```rust
// 定义trait
trait Summary {
    fn summarize(&self) -> String;
    
    // 可以有默认实现
    fn default_summary(&self) -> String {
        String::from("(Read more...)")
    }
}

// 实现trait
struct NewsArticle {
    headline: String,
    content: String,
}

impl Summary for NewsArticle {
    fn summarize(&self) -> String {
        format!("{}: {}", self.headline, &self.content[..50])
    }
}
```

**Trait Bound（约束）**：
```rust
// 参数必须实现Summary
fn notify(item: &impl Summary) {
    println!("Breaking! {}", item.summarize());
}

// 等价的泛型写法
fn notify<T: Summary>(item: &T) {
    println!("Breaking! {}", item.summarize());
}

// 多个约束
fn notify<T: Summary + Display>(item: &T) { ... }

// where子句（更清晰）
fn some_function<T, U>(t: &T, u: &U)
where
    T: Display + Clone,
    U: Clone + Debug,
{ ... }
```

---

### 2.2 Trait Object (Trait对象)

**定义**：动态分发的trait实现，通过`dyn Trait`表示。

```rust
// 静态分发（编译期确定类型）
fn static_dispatch<T: Summary>(item: &T) {
    println!("{}", item.summarize());
}

// 动态分发（运行时确定类型）
fn dynamic_dispatch(item: &dyn Summary) {
    println!("{}", item.summarize());
}

// 存储不同类型的集合
let items: Vec<Box<dyn Summary>> = vec![
    Box::new(NewsArticle { ... }),
    Box::new(Tweet { ... }),
];
```

**性能考虑**：
- 静态分发：零开销，可内联
- 动态分发：虚表查找（~1-2ns），无法内联

**详细文章**：[Trait对象与动态分发](@/articles/rust/rust-12-Rust编译器优化详解.md)

---

### 2.3 Option & Result

**定义**：Rust处理可能缺失的值(Option)和可能失败的操作(Result)的方式，替代null和异常。

**Option**：
```rust
enum Option<T> {
    Some(T),
    None,
}

fn find_user(id: u32) -> Option<User> {
    if id == 1 {
        Some(User { name: "Alice".into() })
    } else {
        None
    }
}

// 使用
match find_user(1) {
    Some(user) => println!("Found: {}", user.name),
    None => println!("Not found"),
}

// 简洁写法
let name = find_user(1).map(|u| u.name).unwrap_or("Unknown".into());
```

**Result**：
```rust
enum Result<T, E> {
    Ok(T),
    Err(E),
}

fn read_file(path: &str) -> Result<String, io::Error> {
    fs::read_to_string(path)
}

// ?运算符自动传播错误
fn process_file(path: &str) -> Result<(), io::Error> {
    let content = read_file(path)?;  // 错误时提前返回
    println!("{}", content);
    Ok(())
}
```

---

## 三、并发

### 3.1 Send & Sync

**定义**：标记类型是否可以安全地跨线程使用。

- **Send**：类型可以安全地转移到另一个线程
- **Sync**：类型可以被多个线程通过引用安全地访问

```rust
// 大多数类型是Send + Sync
let s = String::from("hello");  // Send + Sync

// Rc不是Send（引用计数非原子）
use std::rc::Rc;
let rc = Rc::new(5);
// std::thread::spawn(move || { ... rc ... });  // 编译错误

// Arc是Send + Sync
use std::sync::Arc;
let arc = Arc::new(5);
std::thread::spawn(move || {
    println!("{}", arc);  // OK
});
```

---

### 3.2 Mutex & RwLock

**定义**：Rust的互斥量和读写锁，通过类型系统保证正确使用。

```rust
use std::sync::{Mutex, Arc};
use std::thread;

let counter = Arc::new(Mutex::new(0));
let mut handles = vec![];

for _ in 0..10 {
    let counter = Arc::clone(&counter);
    let handle = thread::spawn(move || {
        let mut num = counter.lock().unwrap();
        *num += 1;
    });  // MutexGuard在这里释放锁
    handles.push(handle);
}

for handle in handles {
    handle.join().unwrap();
}

println!("Result: {}", *counter.lock().unwrap());  // 10
```

**RwLock**：
```rust
use std::sync::RwLock;

let lock = RwLock::new(5);

// 多个读者可以并发
{
    let r1 = lock.read().unwrap();
    let r2 = lock.read().unwrap();
    println!("{} {}", r1, r2);
}

// 写者独占
{
    let mut w = lock.write().unwrap();
    *w += 1;
}
```

---

### 3.3 Channel

**定义**：线程间通信的消息传递机制。

```rust
use std::sync::mpsc;  // multi-producer, single-consumer

let (tx, rx) = mpsc::channel();

// 发送者可以克隆
let tx1 = tx.clone();

thread::spawn(move || {
    tx.send("hello from thread 1").unwrap();
});

thread::spawn(move || {
    tx1.send("hello from thread 2").unwrap();
});

// 接收
for received in rx {
    println!("Got: {}", received);
}
```

**同步channel（有界）**：
```rust
let (tx, rx) = mpsc::sync_channel(3);  // 缓冲区大小3
// send会在缓冲区满时阻塞
```

---

### 3.4 async/await (异步编程)

**定义**：Rust的零成本异步抽象。`async fn`返回一个实现`Future` trait的状态机，`await`用于等待Future完成。

**与其他语言的区别**：
- **零成本**：async/await编译为状态机，无堆分配（除非显式Box）
- **惰性执行**：Future只有被poll时才执行
- **需要运行时**：如tokio、async-std

```rust
// async函数返回impl Future
async fn fetch_data(url: &str) -> Result<String, Error> {
    let response = reqwest::get(url).await?;
    let body = response.text().await?;
    Ok(body)
}

// 编译器将其转换为类似这样的状态机
enum FetchDataFuture {
    Start { url: String },
    WaitingForResponse { fut: RequestFuture },
    WaitingForBody { fut: BodyFuture },
    Done,
}

impl Future for FetchDataFuture {
    type Output = Result<String, Error>;
    
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        // 状态机转换逻辑
    }
}
```

**tokio运行时**：
```rust
#[tokio::main]
async fn main() {
    // 并发执行多个任务
    let (a, b, c) = tokio::join!(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3"),
    );
    
    // 或spawn独立任务
    let handle = tokio::spawn(async {
        fetch_data("url4").await
    });
}
```

**详细文章**：[Rust异步编程](@/articles/rust/rust-06-异步编程.md)

---

### 3.5 Pin (固定)

**定义**：保证值在内存中的位置不会移动。这对于自引用结构（如async状态机）是必需的。

**为什么需要Pin**：
```rust
// async块可能产生自引用结构
async {
    let data = vec![1, 2, 3];
    let reference = &data[0];  // reference指向data
    some_async_op().await;      // 可能暂停
    println!("{}", reference);  // 需要data还在原位置
}

// 如果在await期间data被移动，reference就悬垂了！
```

**Pin的工作原理**：
```rust
// Pin<P>包装一个指针P，保证指向的值不会移动

// 创建Pin
let mut data = Box::new(5);
let pinned: Pin<Box<i32>> = Box::pin(5);

// Pin在栈上
let mut data = 5;
let pinned: Pin<&mut i32> = Pin::new(&mut data);

// 通过unsafe手动固定
let pinned = unsafe { Pin::new_unchecked(&mut data) };
```

**Unpin trait**：
```rust
// 大多数类型实现Unpin，表示可以安全移动
// 自引用类型应该是!Unpin

// 如果T: Unpin，Pin<&mut T>就像&mut T
fn takes_pin<T: Unpin>(pin: Pin<&mut T>) {
    let inner: &mut T = Pin::into_inner(pin);  // 可以解除Pin
}

// 如果T: !Unpin，Pin提供真正的保证
// 不能安全地获取&mut T
```

**实际应用**：
```rust
use std::pin::Pin;
use std::future::Future;

// Future trait需要Pin
trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}

// 手动实现Future
struct MyFuture { /* ... */ }

impl Future for MyFuture {
    type Output = i32;
    
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        // self是Pin<&mut Self>，保证不会移动
        Poll::Ready(42)
    }
}
```

---

## 四、Unsafe Rust

### 4.1 unsafe关键字

**定义**：允许执行编译器无法验证安全性的操作。

**五种unsafe超能力**：
1. 解引用裸指针
2. 调用unsafe函数
3. 访问/修改可变静态变量
4. 实现unsafe trait
5. 访问union字段

```rust
let mut num = 5;

// 裸指针
let r1 = &num as *const i32;
let r2 = &mut num as *mut i32;

unsafe {
    println!("r1: {}", *r1);
    *r2 = 10;
}

// unsafe函数
unsafe fn dangerous() {
    // 可以做不安全操作
}

unsafe {
    dangerous();
}
```

**详细文章**：[unsafe-Rust完全指南](@/articles/rust/rust-09-Rust与C-C++互操作.md)

---

### 4.2 FFI (Foreign Function Interface)

**定义**：Rust与其他语言（主要是C）的互操作。

```rust
// 调用C函数
extern "C" {
    fn abs(input: i32) -> i32;
}

fn main() {
    unsafe {
        println!("abs(-3) = {}", abs(-3));
    }
}

// 暴露Rust函数给C
#[no_mangle]
pub extern "C" fn call_from_c() {
    println!("Called from C!");
}
```

**详细文章**：[Rust与C/C++互操作](@/articles/rust/rust-10-Rust内存布局与对齐.md)

---

### 4.3 Interior Mutability (内部可变性)

**定义**：在拥有不可变引用的情况下修改数据的能力。通过`Cell`、`RefCell`、`Mutex`等类型实现。

**为什么需要**：
- 借用规则有时过于严格
- 某些模式需要共享可变状态
- 实现缓存、惰性初始化等

**Cell\<T\>**：适用于Copy类型
```rust
use std::cell::Cell;

struct Counter {
    value: Cell<i32>,
}

impl Counter {
    fn increment(&self) {  // 注意：&self，不是&mut self
        self.value.set(self.value.get() + 1);
    }
}

let counter = Counter { value: Cell::new(0) };
counter.increment();  // 可以通过不可变引用修改
println!("{}", counter.value.get());  // 1
```

**RefCell\<T\>**：运行时借用检查
```rust
use std::cell::RefCell;

let data = RefCell::new(vec![1, 2, 3]);

// 运行时借用检查
{
    let mut borrowed = data.borrow_mut();
    borrowed.push(4);
}  // borrowed在这里释放

// 可以再次借用
println!("{:?}", data.borrow());

// 运行时panic：同时存在多个可变借用
// let a = data.borrow_mut();
// let b = data.borrow_mut();  // panic!
```

**Rc\<RefCell\<T\>\>模式**：共享可变状态
```rust
use std::rc::Rc;
use std::cell::RefCell;

let shared = Rc::new(RefCell::new(0));

let a = Rc::clone(&shared);
let b = Rc::clone(&shared);

*a.borrow_mut() += 1;
*b.borrow_mut() += 1;

println!("{}", shared.borrow());  // 2
```

**线程安全版本**：`Mutex`和`RwLock`
```rust
use std::sync::{Arc, Mutex};

let shared = Arc::new(Mutex::new(0));
// 多线程安全修改
```

---

### 4.4 Drop Trait (析构)

**定义**：当值离开作用域时自动调用的trait，用于资源清理。类似C++的析构函数。

**自动Drop**：
```rust
struct FileHandle {
    name: String,
}

impl Drop for FileHandle {
    fn drop(&mut self) {
        println!("Closing file: {}", self.name);
        // 释放资源
    }
}

fn main() {
    let f = FileHandle { name: "data.txt".into() };
    // 使用f
}  // 自动调用drop

// 输出: Closing file: data.txt
```

**Drop顺序**：
```rust
struct Outer {
    inner: Inner,
}

struct Inner;

impl Drop for Outer {
    fn drop(&mut self) { println!("Outer dropped"); }
}

impl Drop for Inner {
    fn drop(&mut self) { println!("Inner dropped"); }
}

fn main() {
    let _ = Outer { inner: Inner };
}
// 输出顺序：
// Outer dropped  ← 先drop外部
// Inner dropped  ← 后drop字段
```

**手动Drop**：
```rust
let x = String::from("hello");
drop(x);  // 提前释放
// println!("{}", x);  // 错误：x已移动
```

**防止Drop**：`std::mem::forget`
```rust
let v = vec![1, 2, 3];
std::mem::forget(v);  // 不调用drop，内存泄漏！
// 用于FFI场景，将所有权转移给C代码
```

---

## 五、性能优化

### 5.1 Zero-Cost Abstractions (零成本抽象)

**定义**：Rust的抽象不会带来运行时开销。迭代器、闭包等编译后与手写代码一样高效。

```rust
// 这个抽象链
let sum: i32 = (0..1000)
    .filter(|x| x % 2 == 0)
    .map(|x| x * x)
    .sum();

// 编译后与这个手写代码一样高效
let mut sum = 0;
for x in 0..1000 {
    if x % 2 == 0 {
        sum += x * x;
    }
}
```

---

### 5.2 #[inline] 提示

**定义**：建议编译器内联函数。

```rust
#[inline]
fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[inline(always)]  // 强制内联
fn critical_path(x: i32) -> i32 {
    x * 2
}

#[inline(never)]  // 禁止内联
fn cold_path(x: i32) -> i32 {
    // 错误处理等冷路径
    panic!("error: {}", x);
}
```

---

### 5.3 std::mem 工具

**定义**：内存操作工具函数。

```rust
use std::mem;

// 大小和对齐
println!("size: {}", mem::size_of::<i64>());      // 8
println!("align: {}", mem::align_of::<i64>());    // 8

// 交换值
let mut a = 1;
let mut b = 2;
mem::swap(&mut a, &mut b);

// 替换值
let old = mem::replace(&mut a, 10);

// 取走值（留下默认值）
let taken = mem::take(&mut a);  // a变成0

// 忘记值（不调用析构函数）
let v = vec![1, 2, 3];
mem::forget(v);  // 内存泄漏！小心使用
```

---

## 六、延伸阅读

- [C++核心概念索引](@/articles/00-glossary/glossary-05-cpp-concepts.md)
- [HFT核心概念索引](@/articles/00-glossary/glossary-04-hft-concepts.md)
- [Rust面试题-所有权与生命周期](@/articles/rust/rust-19-Rust面试指南.md)
- [HFT-Rust-Lock-Free编程](@/articles/rust/rust-15-HFT-Rust-SIMD编程.md)

---

## 相关文章

- [上一篇：Python Concepts](@/articles/00-glossary/glossary-06-python-concepts.md)
