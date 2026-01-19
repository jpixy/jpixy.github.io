+++
title = "05.并发编程"
date = 2026-01-19
description = "Rust并发：线程、消息传递、共享状态、Sync和Send、无畏并发"
[taxonomies]
tags = ["Rust", "并发", "多线程"]
+++

## 线程基础

### 创建线程

```rust
use std::thread;
use std::time::Duration;

fn main() {
    let handle = thread::spawn(|| {
        for i in 1..10 {
            println!("spawned thread: {}", i);
            thread::sleep(Duration::from_millis(1));
        }
    });
    
    for i in 1..5 {
        println!("main thread: {}", i);
        thread::sleep(Duration::from_millis(1));
    }
    
    handle.join().unwrap();  // 等待线程结束
}
```

### move闭包

```rust
let v = vec![1, 2, 3];

// move强制闭包获取所有权
let handle = thread::spawn(move || {
    println!("Here's a vector: {:?}", v);
});

// v已移动，不能再使用
// println!("{:?}", v);  // 错误！

handle.join().unwrap();
```

### 线程Builder

```rust
use std::thread;

let builder = thread::Builder::new()
    .name("worker".into())
    .stack_size(32 * 1024);

let handle = builder.spawn(|| {
    println!("Thread name: {:?}", thread::current().name());
}).unwrap();

handle.join().unwrap();
```

---

## 消息传递

### Channel

```rust
use std::sync::mpsc;  // multiple producer, single consumer
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();
    
    thread::spawn(move || {
        let val = String::from("hello");
        tx.send(val).unwrap();
        // val已移动，不能再使用
    });
    
    let received = rx.recv().unwrap();  // 阻塞等待
    println!("Got: {}", received);
}
```

### 多个发送者

```rust
let (tx, rx) = mpsc::channel();

let tx1 = tx.clone();
thread::spawn(move || {
    tx1.send("from thread 1").unwrap();
});

thread::spawn(move || {
    tx.send("from thread 2").unwrap();
});

for received in rx {
    println!("Got: {}", received);
}
```

### 同步Channel

```rust
// 缓冲区大小为0，发送会阻塞直到接收
let (tx, rx) = mpsc::sync_channel(0);

// 缓冲区大小为5
let (tx, rx) = mpsc::sync_channel(5);
```

### 非阻塞接收

```rust
match rx.try_recv() {
    Ok(msg) => println!("Got: {}", msg),
    Err(mpsc::TryRecvError::Empty) => println!("No message"),
    Err(mpsc::TryRecvError::Disconnected) => break,
}

// 带超时
match rx.recv_timeout(Duration::from_secs(1)) {
    Ok(msg) => println!("Got: {}", msg),
    Err(_) => println!("Timeout"),
}
```

---

## 共享状态

### Mutex

```rust
use std::sync::Mutex;

fn main() {
    let m = Mutex::new(5);
    
    {
        let mut num = m.lock().unwrap();  // 获取锁
        *num = 6;
    }  // 锁自动释放
    
    println!("m = {:?}", m);
}
```

### 多线程共享Mutex

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Result: {}", *counter.lock().unwrap());
}
```

### RwLock

```rust
use std::sync::RwLock;

let lock = RwLock::new(5);

// 多个读取者
{
    let r1 = lock.read().unwrap();
    let r2 = lock.read().unwrap();
    println!("{} {}", r1, r2);
}

// 单个写入者
{
    let mut w = lock.write().unwrap();
    *w += 1;
}
```

### 死锁避免

```rust
// 错误：可能死锁
let a = Arc::new(Mutex::new(1));
let b = Arc::new(Mutex::new(2));

// 线程1
let _ga = a.lock().unwrap();
let _gb = b.lock().unwrap();

// 线程2
let _gb = b.lock().unwrap();
let _ga = a.lock().unwrap();

// 解决：统一加锁顺序
// 总是先锁a再锁b
```

---

## 原子类型

### 基本原子操作

```rust
use std::sync::atomic::{AtomicUsize, Ordering};

let counter = AtomicUsize::new(0);

// 原子增加
counter.fetch_add(1, Ordering::SeqCst);

// 原子读取
let value = counter.load(Ordering::SeqCst);

// 原子存储
counter.store(10, Ordering::SeqCst);

// 比较并交换
counter.compare_exchange(10, 20, Ordering::SeqCst, Ordering::SeqCst);
```

### Ordering

| Ordering | 说明 |
|----------|------|
| Relaxed | 最弱，只保证原子性 |
| Acquire | 读屏障 |
| Release | 写屏障 |
| AcqRel | 读写屏障 |
| SeqCst | 顺序一致，最强 |

### 原子标志

```rust
use std::sync::atomic::{AtomicBool, Ordering};

let running = AtomicBool::new(true);

// 工作线程
while running.load(Ordering::Relaxed) {
    // 工作
}

// 停止
running.store(false, Ordering::Relaxed);
```

---

## Send和Sync

### Send trait

实现Send的类型可以跨线程转移所有权。

大多数类型是Send，例外：
- `Rc<T>`（非原子引用计数）
- `*const T`、`*mut T`（裸指针）

### Sync trait

实现Sync的类型可以被多线程安全访问（&T是Send）。

大多数类型是Sync，例外：
- `RefCell<T>`（运行时借用检查非线程安全）
- `Rc<T>`

### 关系

```
T: Sync  ⟺  &T: Send
```

### 自定义类型

```rust
// 如果所有字段都是Send，结构体自动是Send
struct MyStruct {
    data: String,  // String是Send
}
// MyStruct自动实现Send

// 手动标记
unsafe impl Send for MyType {}
unsafe impl Sync for MyType {}
```

---

## 并发工具

### Barrier

```rust
use std::sync::{Arc, Barrier};
use std::thread;

let barrier = Arc::new(Barrier::new(3));

for _ in 0..3 {
    let b = Arc::clone(&barrier);
    thread::spawn(move || {
        println!("before wait");
        b.wait();  // 等待所有线程到达
        println!("after wait");
    });
}
```

### Condvar

```rust
use std::sync::{Arc, Mutex, Condvar};

let pair = Arc::new((Mutex::new(false), Condvar::new()));

// 等待方
let (lock, cvar) = &*pair;
let mut started = lock.lock().unwrap();
while !*started {
    started = cvar.wait(started).unwrap();
}

// 通知方
let (lock, cvar) = &*pair;
let mut started = lock.lock().unwrap();
*started = true;
cvar.notify_one();
```

### Once

```rust
use std::sync::Once;

static INIT: Once = Once::new();

fn initialize() {
    INIT.call_once(|| {
        // 只执行一次
        println!("Initializing...");
    });
}
```

---

## 作用域线程

### crossbeam

```rust
use crossbeam::scope;

let data = vec![1, 2, 3];

scope(|s| {
    s.spawn(|_| {
        println!("{:?}", data);  // 可以借用外部数据
    });
}).unwrap();

// data仍然有效
println!("{:?}", data);
```

### std::thread::scope（Rust 1.63+）

```rust
let data = vec![1, 2, 3];

std::thread::scope(|s| {
    s.spawn(|| {
        println!("{:?}", data);
    });
});
```

---

## Rayon并行

```rust
use rayon::prelude::*;

// 并行迭代
let sum: i32 = (0..1000).into_par_iter()
    .map(|x| x * x)
    .sum();

// 并行排序
let mut data = vec![5, 2, 8, 1, 9];
data.par_sort();

// 并行for_each
data.par_iter().for_each(|x| {
    println!("{}", x);
});
```

---

## 最佳实践

### 优先消息传递

```rust
// 优先
let (tx, rx) = mpsc::channel();
thread::spawn(move || {
    tx.send(result).unwrap();
});
let result = rx.recv().unwrap();

// 其次
let data = Arc::new(Mutex::new(0));
```

### 减少锁粒度

```rust
// 不好：锁持有时间长
let guard = data.lock().unwrap();
expensive_computation(&guard);
drop(guard);

// 好：锁持有时间短
let value = {
    let guard = data.lock().unwrap();
    guard.clone()
};
expensive_computation(&value);
```

### 使用无锁数据结构

```rust
use crossbeam::queue::ArrayQueue;

let queue = ArrayQueue::new(100);
queue.push(1).unwrap();
let value = queue.pop();
```

---

## 总结

| 机制 | 用途 |
|------|------|
| thread::spawn | 创建线程 |
| mpsc::channel | 消息传递 |
| Mutex | 互斥访问 |
| RwLock | 读写锁 |
| Atomic | 无锁原子操作 |
| Arc | 线程安全引用计数 |
| Send/Sync | 并发安全标记 |

Rust的"无畏并发"来自编译器对Send和Sync的检查，让并发错误在编译期暴露。
