+++
title = "14. HFT-Rust Lock-Free编程"
slug = "rust-15-HFT-Rust-Lock-Free编程"
date = 2026-01-21
weight = 14000
description = "深入剖析Rust的Lock-Free编程技术，包括std::sync::atomic、crossbeam、无锁队列、Arc开销和parking_lot"
[taxonomies]
tags = ["Rust", "Lock-Free", "并发", "原子操作", "HFT"]
+++

## 概述

在HFT系统中，锁竞争是延迟的主要来源之一。Lock-Free编程通过原子操作实现无锁并发，避免线程阻塞。

---

## 一、原子操作基础

### 1.1 std::sync::atomic

```rust
use std::sync::atomic::{AtomicU64, AtomicBool, AtomicPtr, Ordering};

fn main() {
    // 基本原子类型
    let counter = AtomicU64::new(0);
    
    // load和store
    counter.store(42, Ordering::SeqCst);
    let val = counter.load(Ordering::SeqCst);
    
    // 原子加法
    let old = counter.fetch_add(1, Ordering::SeqCst);
    
    // 比较并交换
    let result = counter.compare_exchange(
        43,              // expected
        100,             // new value
        Ordering::SeqCst, // success ordering
        Ordering::SeqCst, // failure ordering
    );
    
    match result {
        Ok(prev) => println!("Swapped from {}", prev),
        Err(actual) => println!("Failed, actual value: {}", actual),
    }
}
```

### 1.2 内存顺序

```rust
use std::sync::atomic::{AtomicU64, AtomicBool, Ordering};
use std::thread;

// Relaxed: 只保证原子性，不保证顺序
fn relaxed_example() {
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    
    // 适用于简单计数器，不需要同步其他数据
    COUNTER.fetch_add(1, Ordering::Relaxed);
}

// Release-Acquire: 建立happens-before关系
fn release_acquire() {
    static DATA: AtomicU64 = AtomicU64::new(0);
    static READY: AtomicBool = AtomicBool::new(false);
    
    // 生产者
    let producer = thread::spawn(|| {
        DATA.store(42, Ordering::Relaxed);
        READY.store(true, Ordering::Release);  // 确保DATA先写入
    });
    
    // 消费者
    let consumer = thread::spawn(|| {
        while !READY.load(Ordering::Acquire) {
            std::hint::spin_loop();
        }
        // Acquire保证看到Release之前的所有写入
        assert_eq!(DATA.load(Ordering::Relaxed), 42);
    });
    
    producer.join().unwrap();
    consumer.join().unwrap();
}

// SeqCst: 全局顺序一致
fn seqcst_example() {
    static X: AtomicBool = AtomicBool::new(false);
    static Y: AtomicBool = AtomicBool::new(false);
    static Z: AtomicU64 = AtomicU64::new(0);
    
    // SeqCst确保所有线程看到相同的操作顺序
    // 性能开销最大，但最容易理解
}
```

### 1.3 compare_exchange_weak

```rust
use std::sync::atomic::{AtomicU64, Ordering};

fn increment_weak(counter: &AtomicU64) -> u64 {
    loop {
        let current = counter.load(Ordering::Relaxed);
        
        // weak版本可能会假失败，但在循环中更高效
        match counter.compare_exchange_weak(
            current,
            current + 1,
            Ordering::Release,
            Ordering::Relaxed,
        ) {
            Ok(prev) => return prev,
            Err(_) => continue,  // 重试
        }
    }
}

// 使用场景：
// - compare_exchange: 需要一次成功的情况
// - compare_exchange_weak: 在循环中重试的情况（性能更好）
```

---

## 二、无锁数据结构

### 2.1 SPSC队列

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::cell::UnsafeCell;
use std::mem::MaybeUninit;

pub struct SpscQueue<T, const N: usize> {
    buffer: [UnsafeCell<MaybeUninit<T>>; N],
    head: AtomicUsize,  // 写入位置
    tail: AtomicUsize,  // 读取位置
    cached_head: UnsafeCell<usize>,  // 消费者缓存
    cached_tail: UnsafeCell<usize>,  // 生产者缓存
}

unsafe impl<T: Send, const N: usize> Send for SpscQueue<T, N> {}
unsafe impl<T: Send, const N: usize> Sync for SpscQueue<T, N> {}

impl<T, const N: usize> SpscQueue<T, N> {
    pub fn new() -> Self {
        Self {
            buffer: unsafe { MaybeUninit::uninit().assume_init() },
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
            cached_head: UnsafeCell::new(0),
            cached_tail: UnsafeCell::new(0),
        }
    }
    
    /// 生产者调用
    pub fn push(&self, value: T) -> Result<(), T> {
        let head = self.head.load(Ordering::Relaxed);
        let next_head = (head + 1) % N;
        
        // 使用缓存的tail减少原子load
        let cached_tail = unsafe { *self.cached_tail.get() };
        if next_head == cached_tail {
            // 缓存可能过期，重新加载
            let tail = self.tail.load(Ordering::Acquire);
            unsafe { *self.cached_tail.get() = tail; }
            
            if next_head == tail {
                return Err(value);  // 真的满了
            }
        }
        
        unsafe {
            (*self.buffer[head].get()).write(value);
        }
        self.head.store(next_head, Ordering::Release);
        Ok(())
    }
    
    /// 消费者调用
    pub fn pop(&self) -> Option<T> {
        let tail = self.tail.load(Ordering::Relaxed);
        
        // 使用缓存的head
        let cached_head = unsafe { *self.cached_head.get() };
        if tail == cached_head {
            let head = self.head.load(Ordering::Acquire);
            unsafe { *self.cached_head.get() = head; }
            
            if tail == head {
                return None;  // 真的空
            }
        }
        
        let value = unsafe {
            (*self.buffer[tail].get()).assume_init_read()
        };
        self.tail.store((tail + 1) % N, Ordering::Release);
        Some(value)
    }
}
```

### 2.2 MPMC队列（基于crossbeam）

```rust
use crossbeam_channel::{bounded, unbounded, Sender, Receiver};

fn mpmc_example() {
    // 有界通道（背压）
    let (tx, rx) = bounded::<i32>(1000);
    
    // 生产者
    for i in 0..10 {
        let tx = tx.clone();
        std::thread::spawn(move || {
            for j in 0..100 {
                tx.send(i * 100 + j).unwrap();
            }
        });
    }
    
    // 消费者
    for _ in 0..4 {
        let rx = rx.clone();
        std::thread::spawn(move || {
            while let Ok(msg) = rx.recv() {
                process(msg);
            }
        });
    }
}

fn process(_msg: i32) {}
```

### 2.3 无锁栈

```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

struct Node<T> {
    data: T,
    next: *mut Node<T>,
}

pub struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

impl<T> LockFreeStack<T> {
    pub fn new() -> Self {
        Self {
            head: AtomicPtr::new(ptr::null_mut()),
        }
    }
    
    pub fn push(&self, data: T) {
        let new_node = Box::into_raw(Box::new(Node {
            data,
            next: ptr::null_mut(),
        }));
        
        loop {
            let head = self.head.load(Ordering::Relaxed);
            unsafe { (*new_node).next = head; }
            
            if self.head.compare_exchange_weak(
                head, new_node,
                Ordering::Release,
                Ordering::Relaxed,
            ).is_ok() {
                break;
            }
        }
    }
    
    pub fn pop(&self) -> Option<T> {
        loop {
            let head = self.head.load(Ordering::Acquire);
            if head.is_null() {
                return None;
            }
            
            let next = unsafe { (*head).next };
            
            if self.head.compare_exchange_weak(
                head, next,
                Ordering::Release,
                Ordering::Relaxed,
            ).is_ok() {
                let data = unsafe { Box::from_raw(head).data };
                return Some(data);
            }
        }
    }
}

impl<T> Drop for LockFreeStack<T> {
    fn drop(&mut self) {
        while self.pop().is_some() {}
    }
}
```

---

## 三、crossbeam库

### 3.1 crossbeam-epoch

```rust
use crossbeam_epoch::{self as epoch, Atomic, Owned, Shared};
use std::sync::atomic::Ordering;

struct Node {
    data: i32,
    next: Atomic<Node>,
}

fn epoch_example() {
    // Epoch-based内存回收
    let head: Atomic<Node> = Atomic::null();
    
    // 进入epoch
    let guard = epoch::pin();
    
    // 安全地访问共享数据
    let node = head.load(Ordering::Acquire, &guard);
    
    if let Some(n) = unsafe { node.as_ref() } {
        println!("Data: {}", n.data);
    }
    
    // guard离开作用域时，表示不再使用共享数据
    // 可以安全回收被标记为删除的节点
}
```

### 3.2 crossbeam-utils

```rust
use crossbeam_utils::CachePadded;
use std::sync::atomic::AtomicU64;

// 避免False Sharing
struct Counters {
    read_count: CachePadded<AtomicU64>,
    write_count: CachePadded<AtomicU64>,
}

// 每个计数器独占一个缓存行
impl Counters {
    fn new() -> Self {
        Self {
            read_count: CachePadded::new(AtomicU64::new(0)),
            write_count: CachePadded::new(AtomicU64::new(0)),
        }
    }
}
```

### 3.3 crossbeam-deque

```rust
use crossbeam_deque::{Worker, Stealer, Steal};

fn work_stealing() {
    // 工作窃取队列
    let worker = Worker::new_fifo();
    let stealer = worker.stealer();
    
    // 工作线程推入任务
    worker.push(1);
    worker.push(2);
    worker.push(3);
    
    // 窃取线程获取任务
    std::thread::spawn(move || {
        loop {
            match stealer.steal() {
                Steal::Success(task) => process_task(task),
                Steal::Empty => break,
                Steal::Retry => continue,
            }
        }
    });
    
    // 工作线程也处理自己的任务
    while let Some(task) = worker.pop() {
        process_task(task);
    }
}

fn process_task(_task: i32) {}
```

---

## 四、Arc开销分析

### 4.1 Arc内部结构

```rust
use std::sync::Arc;

// Arc内部使用两个原子计数器
// - strong_count: 强引用计数
// - weak_count: 弱引用计数 + 1

fn arc_overhead() {
    let data = Arc::new(vec![1, 2, 3]);
    
    // clone增加强引用计数（原子操作）
    let data2 = Arc::clone(&data);
    
    // 每次clone都是fetch_add
    // 开销：约10-20纳秒
}
```

### 4.2 避免Arc克隆

```rust
use std::sync::Arc;

// 不好：频繁克隆Arc
fn bad_pattern(data: Arc<Vec<i32>>) {
    for _ in 0..1000 {
        process(Arc::clone(&data));  // 1000次原子操作
    }
}

fn process(_data: Arc<Vec<i32>>) {}

// 好：传递引用
fn good_pattern(data: &[i32]) {
    for _ in 0..1000 {
        process_ref(data);  // 无原子操作
    }
}

fn process_ref(_data: &[i32]) {}

// HFT模式：启动时克隆，运行时使用引用
struct Handler {
    config: Arc<Config>,
}

impl Handler {
    fn new(config: Arc<Config>) -> Self {
        Self { config }
    }
    
    fn handle(&self, msg: &Message) {
        // 使用&self.config，无克隆
        let _ = &self.config;
    }
}

struct Config;
struct Message;
```

---

## 五、parking_lot

### 5.1 Mutex对比

```rust
use parking_lot::Mutex;
// vs std::sync::Mutex

fn parking_lot_advantages() {
    // parking_lot优势：
    // 1. 更小的Mutex大小（1 word vs 5 words）
    // 2. 无中毒(poisoning)
    // 3. 自旋等待优化
    // 4. 公平性选项
    
    let mutex = Mutex::new(42);
    
    // 简洁的API
    *mutex.lock() += 1;
    
    // try_lock
    if let Some(guard) = mutex.try_lock() {
        // 获得锁
        let _ = *guard;
    }
}
```

### 5.2 RwLock

```rust
use parking_lot::RwLock;

fn rwlock_example() {
    let data = RwLock::new(vec![1, 2, 3]);
    
    // 多个读者
    let read_guard1 = data.read();
    let read_guard2 = data.read();
    println!("{:?}", *read_guard1);
    drop(read_guard1);
    drop(read_guard2);
    
    // 单个写者
    let mut write_guard = data.write();
    write_guard.push(4);
}
```

### 5.3 Condvar

```rust
use parking_lot::{Mutex, Condvar};

struct Queue<T> {
    data: Mutex<Vec<T>>,
    not_empty: Condvar,
}

impl<T> Queue<T> {
    fn new() -> Self {
        Self {
            data: Mutex::new(Vec::new()),
            not_empty: Condvar::new(),
        }
    }
    
    fn push(&self, value: T) {
        let mut data = self.data.lock();
        data.push(value);
        self.not_empty.notify_one();
    }
    
    fn pop(&self) -> T {
        let mut data = self.data.lock();
        while data.is_empty() {
            self.not_empty.wait(&mut data);
        }
        data.remove(0)
    }
}
```

---

## 六、HFT最佳实践

### 6.1 选择合适的工具

```rust
// 场景 -> 工具

// 单生产者单消费者 -> SPSC队列
// 多生产者多消费者 -> crossbeam-channel
// 读多写少 -> RwLock或无锁读
// 写多 -> 分片锁或per-thread数据
// 计数器 -> AtomicU64 + Relaxed
// 状态标志 -> AtomicBool + Acquire/Release
```

### 6.2 减少原子操作

```rust
use std::sync::atomic::{AtomicU64, Ordering};
use std::cell::UnsafeCell;

// 批量更新
struct BatchCounter {
    local: UnsafeCell<u64>,
    global: AtomicU64,
}

impl BatchCounter {
    fn increment(&self) {
        unsafe {
            *self.local.get() += 1;
            if *self.local.get() >= 100 {
                self.flush();
            }
        }
    }
    
    fn flush(&self) {
        unsafe {
            let local = *self.local.get();
            self.global.fetch_add(local, Ordering::Relaxed);
            *self.local.get() = 0;
        }
    }
}
```

---

## 总结

| 工具 | 适用场景 | 开销 |
|------|----------|------|
| Relaxed原子 | 计数器 | 最小 |
| Acquire/Release | 同步标志 | 小 |
| SeqCst | 复杂同步 | 中等 |
| SPSC队列 | 单生产者消费者 | 小 |
| crossbeam-channel | MPMC通信 | 中等 |
| parking_lot::Mutex | 短临界区 | 取决于竞争 |

**HFT原则**：
1. 能无锁就无锁
2. 优先SPSC队列
3. 批量处理减少原子操作
4. 避免频繁Arc克隆
5. 使用CachePadded防止False Sharing

---

## 相关文章

- [上一篇：no_std与嵌入式Rust](@/articles/rust/rust-13-no_std与嵌入式Rust.md)
- [下一篇：HFT-Rust SIMD编程](@/articles/rust/rust-15-HFT-Rust-SIMD编程.md)
