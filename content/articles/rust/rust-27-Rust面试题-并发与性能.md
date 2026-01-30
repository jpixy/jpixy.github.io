+++
title = "20.Rust面试题-并发与性能"
date = 2026-01-21
description = "Rust面试中关于并发和性能的常见问题，包括Send/Sync、数据竞争预防、async深入、性能陷阱等"
[taxonomies]
tags = ["Rust", "面试", "并发", "性能", "async"]
+++

## 概述

Rust的并发安全和性能优势是其核心卖点。本文汇集相关面试问题和深入解答。

---

## 一、Send和Sync

### Q1: 解释Send和Sync trait

```rust
// Send: 类型可以安全地跨线程转移所有权
// "可以发送到另一个线程"
unsafe trait Send {}

// Sync: 类型可以安全地被多个线程共享引用
// "引用可以在多个线程间共享"
// 等价于：&T: Send
unsafe trait Sync {}

// 关系：如果T: Sync，则&T: Send

// 常见类型：
// i32, String: Send + Sync
// Rc<T>: 既不是Send也不是Sync（非原子引用计数）
// Arc<T>: Send + Sync（如果T: Send + Sync）
// Cell<T>, RefCell<T>: Send但不是Sync（内部可变）
// Mutex<T>: Send + Sync（如果T: Send）
// MutexGuard<'_, T>: Sync但不是Send

use std::rc::Rc;
use std::sync::Arc;
use std::cell::Cell;

fn check_send<T: Send>() {}
fn check_sync<T: Sync>() {}

fn main() {
    check_send::<i32>();
    check_sync::<i32>();
    
    check_send::<Arc<i32>>();
    check_sync::<Arc<i32>>();
    
    // check_send::<Rc<i32>>();  // 错误
    // check_sync::<Rc<i32>>();  // 错误
    
    check_send::<Cell<i32>>();
    // check_sync::<Cell<i32>>();  // 错误
}
```

### Q2: 为什么Rc不是Send/Sync？

```rust
use std::rc::Rc;

// Rc使用非原子引用计数
fn why_rc_not_send() {
    let rc = Rc::new(42);
    
    // 如果Rc是Send：
    // Thread 1: rc.clone()  // count: 1 -> 2
    // Thread 2: drop(rc)    // count: 2 -> 1
    // 同时执行可能导致：count错误地变成0或其他值
    
    // 引用计数操作不是原子的：
    // 1. 读取当前count
    // 2. 加1或减1
    // 3. 写回count
    // 多线程同时执行会产生数据竞争
}

// Arc使用原子引用计数
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};

// Arc内部大致实现
struct ArcInner<T> {
    count: AtomicUsize,  // 原子计数
    data: T,
}

fn why_arc_is_send() {
    let arc = Arc::new(42);
    
    // 原子操作保证线程安全
    // count.fetch_add(1, Ordering::Relaxed)
    // count.fetch_sub(1, Ordering::Release)
}
```

### Q3: 如何使非Send类型跨线程？

```rust
use std::rc::Rc;

// 方法1：确保只在一个线程使用
fn single_thread_spawn() {
    let rc = Rc::new(42);
    
    // 使用thread_local
    thread_local! {
        static LOCAL_RC: std::cell::RefCell<Option<Rc<i32>>> = 
            std::cell::RefCell::new(None);
    }
    
    LOCAL_RC.with(|cell| {
        *cell.borrow_mut() = Some(rc);
    });
}

// 方法2：unsafe手动实现（需要非常小心）
struct SendWrapper<T>(T);
unsafe impl<T> Send for SendWrapper<T> {}

// 方法3：使用Arc替代Rc
fn use_arc_instead() {
    use std::sync::Arc;
    let arc = Arc::new(42);
    std::thread::spawn(move || {
        println!("{}", arc);
    });
}
```

---

## 二、数据竞争预防

### Q4: Rust如何预防数据竞争？

```rust
// 数据竞争定义：
// 1. 两个或更多线程访问同一内存
// 2. 至少一个是写操作
// 3. 没有同步

// Rust通过类型系统预防：

// 1. 所有权规则：同一时间只有一个可变引用
fn ownership_prevents_race() {
    let mut data = vec![1, 2, 3];
    
    // 不能同时有两个可变引用
    let r1 = &mut data;
    // let r2 = &mut data;  // 编译错误
}

// 2. Send/Sync：控制跨线程共享
fn send_sync_prevents_race() {
    use std::cell::Cell;
    
    // Cell不是Sync，不能跨线程共享引用
    let cell = Cell::new(42);
    // std::thread::spawn(|| {
    //     cell.set(100);  // 编译错误：Cell不是Sync
    // });
}

// 3. Mutex/RwLock：运行时互斥
use std::sync::Mutex;

fn mutex_prevents_race() {
    let data = Mutex::new(vec![1, 2, 3]);
    
    std::thread::scope(|s| {
        s.spawn(|| {
            data.lock().unwrap().push(4);
        });
        s.spawn(|| {
            data.lock().unwrap().push(5);
        });
    });
}
```

### Q5: Mutex中毒（Poisoning）是什么？

```rust
use std::sync::Mutex;

fn mutex_poisoning() {
    let mutex = Mutex::new(42);
    
    let handle = std::thread::spawn({
        let mutex = &mutex;
        move || {
            let mut guard = mutex.lock().unwrap();
            *guard = 100;
            panic!("Thread panicked while holding lock");
        }
    });
    
    let _ = handle.join();  // 线程panic
    
    // Mutex现在被"中毒"
    match mutex.lock() {
        Ok(guard) => println!("Value: {}", *guard),
        Err(poisoned) => {
            // 可以选择恢复
            let guard = poisoned.into_inner();
            println!("Recovered value: {}", *guard);
        }
    }
}

// parking_lot::Mutex没有中毒机制
use parking_lot::Mutex as ParkingMutex;

fn no_poisoning() {
    let mutex = ParkingMutex::new(42);
    let guard = mutex.lock();  // 直接返回MutexGuard
}
```

### Q6: 什么是死锁？Rust如何处理？

```rust
use std::sync::Mutex;

fn deadlock_example() {
    let a = Mutex::new(1);
    let b = Mutex::new(2);
    
    // 线程1: 锁a，然后锁b
    // 线程2: 锁b，然后锁a
    // 可能死锁！
    
    std::thread::scope(|s| {
        s.spawn(|| {
            let _a = a.lock().unwrap();
            std::thread::sleep(std::time::Duration::from_millis(10));
            let _b = b.lock().unwrap();  // 等待b
        });
        s.spawn(|| {
            let _b = b.lock().unwrap();
            std::thread::sleep(std::time::Duration::from_millis(10));
            let _a = a.lock().unwrap();  // 等待a
        });
    });
}

// Rust不在编译期预防死锁
// 解决方案：
// 1. 总是按相同顺序获取锁
// 2. 使用try_lock避免无限等待
// 3. 使用parking_lot的超时锁
// 4. 使用无锁数据结构
```

---

## 三、async/await深入

### Q7: async函数返回什么？

```rust
// async函数返回实现Future的匿名类型

async fn example() -> i32 {
    42
}

// 大致等价于：
fn example_desugared() -> impl std::future::Future<Output = i32> {
    async { 42 }
}

// Future trait
trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}

enum Poll<T> {
    Ready(T),
    Pending,
}

// async块生成的类型包含：
// - 捕获的变量
// - 状态机状态
// - 每个await点的局部变量
```

### Q8: async函数的生命周期问题

```rust
// 问题：async函数返回的Future包含对参数的引用

async fn process(data: &str) -> usize {
    data.len()
}

// 等价于（简化）：
// fn process<'a>(data: &'a str) -> impl Future<Output = usize> + 'a

fn lifetime_issue() {
    let data = String::from("hello");
    let future = process(&data);
    // drop(data);  // 错误：future持有对data的引用
    // 必须在await future之前保持data有效
}

// 解决方案1：使用'static数据
async fn process_static(data: &'static str) -> usize {
    data.len()
}

// 解决方案2：在async块内创建数据
async fn process_owned(data: String) -> usize {
    data.len()
}
```

### Q9: tokio::spawn的Send约束

```rust
use tokio::task;

async fn spawn_issue() {
    let data = std::rc::Rc::new(42);  // Rc不是Send
    
    // 错误：future不是Send
    // task::spawn(async move {
    //     println!("{}", data);
    // });
    
    // 解决：使用Arc
    let data = std::sync::Arc::new(42);
    task::spawn(async move {
        println!("{}", data);
    });
}

// 为什么需要Send？
// tokio多线程运行时可能在不同线程执行Future
// Future在await点可能被挂起并在另一个线程恢复

// spawn_local不需要Send（单线程运行时）
#[tokio::main(flavor = "current_thread")]
async fn local_spawn() {
    let data = std::rc::Rc::new(42);
    
    tokio::task::spawn_local(async move {
        println!("{}", data);
    });
}
```

### Q10: async与阻塞操作

```rust
use tokio::task;

async fn blocking_issue() {
    // 不好：在async中执行阻塞操作
    // 这会阻塞整个运行时线程
    // std::thread::sleep(std::time::Duration::from_secs(1));
    // std::fs::read_to_string("file.txt");
    
    // 好：使用tokio的异步版本
    tokio::time::sleep(std::time::Duration::from_secs(1)).await;
    tokio::fs::read_to_string("file.txt").await.ok();
    
    // 对于无法避免的阻塞操作
    let result = task::spawn_blocking(|| {
        // 在专门的阻塞线程池执行
        std::thread::sleep(std::time::Duration::from_secs(1));
        42
    }).await.unwrap();
}
```

---

## 四、性能陷阱

### Q11: 常见的性能陷阱

```rust
// 1. 过度克隆
fn over_cloning(data: String) {
    let cloned = data.clone();  // 不必要的clone
    process(&cloned);
    // 应该直接：process(&data);
}

fn process(_s: &str) {}

// 2. 不必要的分配
fn unnecessary_allocation() {
    let v: Vec<i32> = (0..1000).collect();  // 分配
    let sum: i32 = v.iter().sum();
    
    // 更好：迭代器链
    let sum: i32 = (0..1000).sum();  // 无分配
}

// 3. String vs &str
fn string_vs_str(s: String) {  // 获取所有权
    println!("{}", s);
}

fn string_vs_str_better(s: &str) {  // 借用更灵活
    println!("{}", s);
}

// 4. Vec resize
fn vec_resize() {
    let mut v = Vec::new();
    for i in 0..1000 {
        v.push(i);  // 多次重分配
    }
    
    // 更好：预分配
    let mut v = Vec::with_capacity(1000);
    for i in 0..1000 {
        v.push(i);  // 无重分配
    }
}

// 5. 锁的粒度
use std::sync::Mutex;

fn lock_granularity() {
    let data = Mutex::new(vec![0; 1000]);
    
    // 不好：长时间持有锁
    {
        let mut guard = data.lock().unwrap();
        for x in guard.iter_mut() {
            *x = expensive_computation(*x);
        }
    }
    
    // 更好：减少锁持有时间
    let snapshot = data.lock().unwrap().clone();
    let results: Vec<_> = snapshot.iter().map(|x| expensive_computation(*x)).collect();
    *data.lock().unwrap() = results;
}

fn expensive_computation(x: i32) -> i32 { x * 2 }
```

### Q12: Box vs Rc vs Arc的选择

```rust
// Box: 堆分配，单一所有者
fn use_box() {
    let data = Box::new(42);
    // 独占所有权
    // 无运行时开销
}

// Rc: 引用计数，单线程共享
use std::rc::Rc;
fn use_rc() {
    let data = Rc::new(42);
    let data2 = Rc::clone(&data);
    // 多个所有者
    // 只能单线程
    // clone开销：增加计数（非原子）
}

// Arc: 原子引用计数，多线程共享
use std::sync::Arc;
fn use_arc() {
    let data = Arc::new(42);
    let data2 = Arc::clone(&data);
    // 多个所有者
    // 可以多线程
    // clone开销：原子操作（~10-20ns）
}

// 选择指南：
// - 能用栈就用栈
// - 单一所有者用Box
// - 单线程共享用Rc
// - 多线程共享用Arc
```

---

## 五、Rust vs C++性能

### Q13: Rust和C++性能对比

```rust
// 相同之处：
// - 都编译为原生代码
// - 都使用LLVM后端（Rust）
// - 都支持零成本抽象

// Rust优势：
// 1. 默认move语义，减少拷贝
// 2. 更好的别名分析（noalias）
// 3. 强制内存对齐
// 4. 无数据竞争保证

// C++优势：
// 1. 更成熟的编译器优化
// 2. 更细粒度的控制
// 3. placement new等底层特性

// 实际对比：
// - 大多数场景性能相当
// - Rust在某些场景因为更好的别名信息更快
// - C++在特定低级操作可能更灵活
```

### Q14: 如何优化Rust代码达到C++性能？

```rust
// 1. 使用release构建
// cargo build --release

// 2. 启用LTO
// Cargo.toml: lto = "fat"

// 3. 目标CPU优化
// RUSTFLAGS="-C target-cpu=native"

// 4. 使用unsafe避免边界检查
fn unchecked_access(data: &[i32], index: usize) -> i32 {
    unsafe { *data.get_unchecked(index) }
}

// 5. 使用#[inline(always)]
#[inline(always)]
fn hot_function(x: i32) -> i32 {
    x * 2
}

// 6. 避免动态分发
// 使用泛型代替trait对象

// 7. 使用MaybeUninit避免初始化
use std::mem::MaybeUninit;
fn uninit_array<const N: usize>() -> [i32; N] {
    let mut arr: [MaybeUninit<i32>; N] = unsafe { MaybeUninit::uninit().assume_init() };
    for (i, elem) in arr.iter_mut().enumerate() {
        elem.write(i as i32);
    }
    unsafe { std::mem::transmute_copy(&arr) }
}
```

---

## 总结

| 概念 | 要点 |
|------|------|
| Send | 可跨线程转移 |
| Sync | 可跨线程共享引用 |
| 数据竞争 | 编译期通过类型系统预防 |
| async | 返回实现Future的状态机 |
| 性能 | 与C++相当，注意常见陷阱 |

**面试技巧**：
1. 理解Send/Sync的本质
2. 能解释为什么特定类型是/不是Send/Sync
3. 知道async的底层实现
4. 了解常见性能陷阱和优化方法
