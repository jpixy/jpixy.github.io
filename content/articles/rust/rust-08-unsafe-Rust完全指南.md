+++
title = "08. unsafe Rust完全指南"
slug = "rust-09-unsafe-Rust完全指南"
date = 2026-01-21
weight = 8000
description = "深入剖析unsafe Rust的正确使用方式，包括裸指针、unsafe trait、内存安全不变量、FFI边界以及Miri检测工具"
[taxonomies]
tags = ["Rust", "unsafe", "FFI", "内存安全", "HFT"]
+++

## 概述

unsafe Rust是Rust的"逃生舱"，允许绕过编译器的安全检查。在HFT等高性能场景中，unsafe代码有时是必要的。本文深入讲解unsafe Rust的正确使用方式。

---

## 一、unsafe基础

### 1.1 unsafe能做什么

```rust
// unsafe解锁5种能力：
unsafe {
    // 1. 解引用裸指针
    let ptr: *const i32 = &42;
    let val = *ptr;
    
    // 2. 调用unsafe函数
    dangerous_function();
    
    // 3. 访问或修改可变静态变量
    COUNTER += 1;
    
    // 4. 实现unsafe trait
    // impl Send for MyType {}
    
    // 5. 访问union的字段
    let u = MyUnion { i: 42 };
    let f = u.f;
}

static mut COUNTER: i32 = 0;

union MyUnion {
    i: i32,
    f: f32,
}

unsafe fn dangerous_function() {
    // ...
}
```

### 1.2 unsafe不改变什么

```rust
// unsafe不会关闭借用检查器
unsafe {
    let mut x = 5;
    let r1 = &x;
    let r2 = &mut x;  // 错误！借用检查仍然有效
    println!("{}", r1);
}

// unsafe不会允许数据竞争
// 数据竞争始终是未定义行为

// unsafe不会关闭生命周期检查
// 生命周期仍然必须正确
```

---

## 二、裸指针

### 2.1 创建裸指针

```rust
fn main() {
    // 从引用创建（安全）
    let x = 42;
    let ptr: *const i32 = &x;
    let mut_ptr: *mut i32 = &x as *const i32 as *mut i32;
    
    // 从地址创建
    let address = 0x12345usize;
    let ptr = address as *const i32;
    
    // 空指针
    let null: *const i32 = std::ptr::null();
    let null_mut: *mut i32 = std::ptr::null_mut();
    
    // 裸指针可以在safe代码中创建
    // 但解引用必须在unsafe块中
}
```

### 2.2 解引用裸指针

```rust
fn main() {
    let mut x = 42;
    let ptr = &mut x as *mut i32;
    
    unsafe {
        *ptr = 100;
        println!("x = {}", *ptr);  // 100
    }
    
    // 指针算术
    let arr = [1, 2, 3, 4, 5];
    let ptr = arr.as_ptr();
    
    unsafe {
        println!("{}", *ptr);           // 1
        println!("{}", *ptr.add(2));    // 3
        println!("{}", *ptr.offset(4)); // 5
    }
}
```

### 2.3 安全封装

```rust
// 将unsafe操作封装在安全接口后面
pub fn split_at_mut(slice: &mut [i32], mid: usize) -> (&mut [i32], &mut [i32]) {
    let len = slice.len();
    let ptr = slice.as_mut_ptr();
    
    assert!(mid <= len);
    
    unsafe {
        (
            std::slice::from_raw_parts_mut(ptr, mid),
            std::slice::from_raw_parts_mut(ptr.add(mid), len - mid),
        )
    }
}

// 调用者不需要使用unsafe
fn main() {
    let mut arr = [1, 2, 3, 4, 5];
    let (left, right) = split_at_mut(&mut arr, 2);
    left[0] = 100;
    right[0] = 200;
    println!("{:?}", arr);  // [100, 2, 200, 4, 5]
}
```

---

## 三、内存安全不变量

### 3.1 必须遵守的规则

```rust
// 1. 指针必须对齐
unsafe {
    let arr: [u8; 8] = [0; 8];
    let ptr = arr.as_ptr().add(1) as *const u32;
    // let val = *ptr;  // UB! 未对齐读取
}

// 2. 指针必须指向有效内存
unsafe {
    let ptr: *const i32 = std::ptr::null();
    // let val = *ptr;  // UB! 空指针解引用
}

// 3. 可变裸指针不能有别名
unsafe {
    let mut x = 42;
    let ptr1 = &mut x as *mut i32;
    let ptr2 = &mut x as *mut i32;
    
    // 同时使用ptr1和ptr2修改是UB
    *ptr1 = 1;
    *ptr2 = 2;  // UB! 违反别名规则
}

// 4. 不能创建无效引用
unsafe {
    let ptr: *const i32 = std::ptr::null();
    // let r: &i32 = &*ptr;  // UB! 引用不能为null
}
```

### 3.2 生命周期必须正确

```rust
// 危险：返回悬垂指针
fn dangling_ptr() -> *const i32 {
    let x = 42;
    &x as *const i32
    // x在这里被释放，返回的指针悬垂
}

// 正确：确保生命周期足够长
fn safe_usage() {
    let x = 42;
    let ptr = &x as *const i32;
    unsafe {
        println!("{}", *ptr);  // OK，x还活着
    }
}
```

---

## 四、unsafe trait

### 4.1 Send和Sync

```rust
// 标准库中的unsafe trait
// unsafe trait Send {}
// unsafe trait Sync {}

// 手动实现（需要确保安全性）
struct MyWrapper(*mut i32);

// 声明：MyWrapper可以安全地发送到其他线程
unsafe impl Send for MyWrapper {}

// 声明：&MyWrapper可以安全地在多个线程间共享
unsafe impl Sync for MyWrapper {}

// 错误示例：Rc不是Send的，因为引用计数非原子
// use std::rc::Rc;
// unsafe impl Send for Rc<i32> {}  // 这是错误的！
```

### 4.2 自定义unsafe trait

```rust
/// 表示类型可以安全地从任意字节模式初始化
/// 实现者必须确保所有位模式都是有效的
unsafe trait Pod: Copy {
    fn zeroed() -> Self {
        unsafe { std::mem::zeroed() }
    }
}

// 安全实现：所有位模式对u32都有效
unsafe impl Pod for u32 {}
unsafe impl Pod for i32 {}
unsafe impl Pod for f32 {}

// 不能为bool实现：只有0和1是有效的
// unsafe impl Pod for bool {}  // 错误！

fn read_from_bytes<T: Pod>(bytes: &[u8]) -> T {
    assert!(bytes.len() >= std::mem::size_of::<T>());
    unsafe {
        std::ptr::read(bytes.as_ptr() as *const T)
    }
}
```

---

## 五、FFI边界

### 5.1 声明外部函数

```rust
// 链接C标准库函数
extern "C" {
    fn abs(input: i32) -> i32;
    fn strlen(s: *const std::ffi::c_char) -> usize;
    fn memcpy(dest: *mut u8, src: *const u8, n: usize) -> *mut u8;
}

fn main() {
    unsafe {
        println!("abs(-5) = {}", abs(-5));
        
        let s = std::ffi::CString::new("hello").unwrap();
        println!("strlen = {}", strlen(s.as_ptr()));
    }
}
```

### 5.2 导出Rust函数

```rust
// 导出给C调用
#[no_mangle]
pub extern "C" fn rust_function(x: i32) -> i32 {
    x * 2
}

// 对应的C声明：
// int32_t rust_function(int32_t x);

// 处理复杂类型
#[repr(C)]
pub struct Point {
    x: f64,
    y: f64,
}

#[no_mangle]
pub extern "C" fn create_point(x: f64, y: f64) -> Point {
    Point { x, y }
}

#[no_mangle]
pub extern "C" fn distance(p1: &Point, p2: &Point) -> f64 {
    let dx = p1.x - p2.x;
    let dy = p1.y - p2.y;
    (dx * dx + dy * dy).sqrt()
}
```

### 5.3 回调函数

```rust
// C端调用Rust回调
type Callback = extern "C" fn(i32) -> i32;

#[no_mangle]
pub extern "C" fn register_callback(cb: Callback) {
    let result = cb(42);
    println!("Callback returned: {}", result);
}

// Rust调用C回调
extern "C" {
    fn c_function_with_callback(
        data: *const u8,
        len: usize,
        callback: extern "C" fn(*const u8, usize),
    );
}
```

---

## 六、Miri检测

### 6.1 安装和使用

```bash
# 安装Miri
rustup +nightly component add miri

# 运行Miri检测
cargo +nightly miri run

# 测试
cargo +nightly miri test
```

### 6.2 Miri能检测的问题

```rust
// 1. 内存泄漏
fn memory_leak() {
    let x = Box::new(42);
    Box::into_raw(x);
    // Miri警告：内存未释放
}

// 2. 使用后释放
fn use_after_free() {
    let ptr = {
        let x = Box::new(42);
        Box::into_raw(x)
    };
    // Box已释放
    unsafe {
        // let _ = *ptr;  // Miri报错
    }
}

// 3. 未初始化内存
fn uninitialized() {
    let x: i32;
    unsafe {
        // let _ = std::ptr::read(&x);  // Miri报错
    }
}

// 4. 数据竞争（需要-Zmiri-check-races）
// Miri可以检测并发程序中的数据竞争
```

---

## 七、HFT中的unsafe应用

### 7.1 高性能缓冲区

```rust
use std::alloc::{alloc, dealloc, Layout};

pub struct RingBuffer<T> {
    ptr: *mut T,
    capacity: usize,
    head: usize,
    tail: usize,
}

impl<T> RingBuffer<T> {
    pub fn new(capacity: usize) -> Self {
        let layout = Layout::array::<T>(capacity).unwrap();
        let ptr = unsafe { alloc(layout) as *mut T };
        
        if ptr.is_null() {
            std::alloc::handle_alloc_error(layout);
        }
        
        Self {
            ptr,
            capacity,
            head: 0,
            tail: 0,
        }
    }
    
    pub fn push(&mut self, value: T) -> bool {
        let next_head = (self.head + 1) % self.capacity;
        if next_head == self.tail {
            return false; // 满了
        }
        
        unsafe {
            self.ptr.add(self.head).write(value);
        }
        self.head = next_head;
        true
    }
    
    pub fn pop(&mut self) -> Option<T> {
        if self.head == self.tail {
            return None; // 空
        }
        
        let value = unsafe { self.ptr.add(self.tail).read() };
        self.tail = (self.tail + 1) % self.capacity;
        Some(value)
    }
}

impl<T> Drop for RingBuffer<T> {
    fn drop(&mut self) {
        // 释放所有未消费的元素
        while let Some(_) = self.pop() {}
        
        let layout = Layout::array::<T>(self.capacity).unwrap();
        unsafe {
            dealloc(self.ptr as *mut u8, layout);
        }
    }
}
```

### 7.2 零拷贝解析

```rust
#[repr(C, packed)]
struct MarketDataHeader {
    msg_type: u8,
    msg_len: u16,
    timestamp: u64,
}

impl MarketDataHeader {
    /// 零拷贝解析
    /// # Safety
    /// - buffer必须包含至少size_of::<MarketDataHeader>()字节
    /// - buffer必须正确对齐
    pub unsafe fn from_bytes(buffer: &[u8]) -> &Self {
        &*(buffer.as_ptr() as *const MarketDataHeader)
    }
}

// 安全封装
pub fn parse_header(buffer: &[u8]) -> Option<&MarketDataHeader> {
    if buffer.len() < std::mem::size_of::<MarketDataHeader>() {
        return None;
    }
    
    // packed结构体不需要对齐检查
    Some(unsafe { MarketDataHeader::from_bytes(buffer) })
}
```

---

## 总结

| unsafe操作 | 风险 | 使用场景 |
|------------|------|----------|
| 裸指针解引用 | 悬垂/空指针 | FFI、自定义容器 |
| 可变静态变量 | 数据竞争 | 全局配置（谨慎） |
| unsafe trait实现 | 违反trait契约 | Send/Sync |
| FFI调用 | ABI不匹配 | C/C++互操作 |
| union访问 | 类型混淆 | 类型双关 |

**最佳实践**：
1. 最小化unsafe块范围
2. 封装unsafe于安全API后
3. 使用Miri验证正确性
4. 详细文档说明Safety要求
5. 编写充分的测试

---

## 相关文章

- [上一篇：嵌入式Rust](@/articles/rust/rust-07-嵌入式Rust.md)
- [下一篇：Rust与C/C++互操作](@/articles/rust/rust-09-Rust与C-C++互操作.md)
