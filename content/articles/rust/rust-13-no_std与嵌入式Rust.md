+++
title = "13.no_std与嵌入式Rust"
date = 2026-01-21
description = "深入剖析Rust的no_std环境，包括alloc crate、全局分配器、panic handler、嵌入式HAL等"
[taxonomies]
tags = ["Rust", "no_std", "嵌入式", "分配器", "裸机"]
+++

## 概述

no_std环境允许Rust代码在没有标准库的情况下运行，适用于嵌入式系统、内核开发和某些对延迟敏感的HFT组件。

---

## 一、no_std基础

### 1.1 std vs core vs alloc

```rust
// std: 完整标准库
// - 需要操作系统支持
// - 包含文件IO、网络、线程等

// core: 核心库（无需OS）
// - 基础类型（Option、Result等）
// - 迭代器、切片
// - 原子操作
// - 无内存分配

// alloc: 分配库（需要分配器）
// - Vec、String、Box
// - 需要全局分配器
// - 不需要完整OS
```

### 1.2 声明no_std

```rust
// lib.rs 或 main.rs
#![no_std]

// 可选：使用alloc crate
extern crate alloc;

use core::option::Option;
use core::result::Result;

// 使用alloc中的类型
use alloc::vec::Vec;
use alloc::string::String;
use alloc::boxed::Box;

// 编译器内置类型仍可用
fn example() {
    let x: i32 = 42;
    let arr: [u8; 4] = [1, 2, 3, 4];
    let slice: &[u8] = &arr;
}
```

### 1.3 可用与不可用

```rust
#![no_std]

// ✓ 可用（来自core）
use core::mem::{size_of, align_of};
use core::ptr;
use core::sync::atomic::{AtomicU64, Ordering};
use core::cell::{Cell, RefCell};
use core::marker::PhantomData;

// ✓ 可用（来自alloc，需要分配器）
extern crate alloc;
use alloc::vec::Vec;
use alloc::collections::BTreeMap;

// ✗ 不可用（需要std）
// use std::collections::HashMap;  // 需要随机数
// use std::io::{Read, Write};     // 需要OS
// use std::thread;                 // 需要OS
// use std::net;                    // 需要OS
// use std::fs;                     // 需要OS
```

---

## 二、全局分配器

### 2.1 使用系统分配器

```rust
#![no_std]

extern crate alloc;

// 使用libc的malloc/free
use core::alloc::{GlobalAlloc, Layout};

struct LibcAllocator;

unsafe impl GlobalAlloc for LibcAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        libc::malloc(layout.size()) as *mut u8
    }
    
    unsafe fn dealloc(&self, ptr: *mut u8, _layout: Layout) {
        libc::free(ptr as *mut libc::c_void);
    }
    
    unsafe fn realloc(&self, ptr: *mut u8, _layout: Layout, new_size: usize) -> *mut u8 {
        libc::realloc(ptr as *mut libc::c_void, new_size) as *mut u8
    }
}

#[global_allocator]
static ALLOCATOR: LibcAllocator = LibcAllocator;
```

### 2.2 自定义分配器

```rust
#![no_std]

extern crate alloc;

use core::alloc::{GlobalAlloc, Layout};
use core::cell::UnsafeCell;
use core::ptr;

// 简单的bump allocator
struct BumpAllocator {
    heap_start: usize,
    heap_end: usize,
    next: UnsafeCell<usize>,
}

unsafe impl Sync for BumpAllocator {}

impl BumpAllocator {
    pub const fn new(heap_start: usize, heap_size: usize) -> Self {
        Self {
            heap_start,
            heap_end: heap_start + heap_size,
            next: UnsafeCell::new(heap_start),
        }
    }
}

unsafe impl GlobalAlloc for BumpAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let next = self.next.get();
        
        // 对齐
        let alloc_start = (*next + layout.align() - 1) & !(layout.align() - 1);
        let alloc_end = alloc_start + layout.size();
        
        if alloc_end > self.heap_end {
            return ptr::null_mut();  // OOM
        }
        
        *next = alloc_end;
        alloc_start as *mut u8
    }
    
    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {
        // Bump allocator不释放单个分配
    }
}

// 静态堆
static mut HEAP: [u8; 1024 * 1024] = [0; 1024 * 1024];

#[global_allocator]
static ALLOCATOR: BumpAllocator = unsafe {
    BumpAllocator::new(
        HEAP.as_ptr() as usize,
        HEAP.len(),
    )
};
```

### 2.3 Arena分配器

```rust
#![no_std]

extern crate alloc;

use core::alloc::{GlobalAlloc, Layout};
use core::cell::UnsafeCell;
use core::sync::atomic::{AtomicUsize, Ordering};

// 线程安全的Arena分配器
pub struct ArenaAllocator {
    buffer: UnsafeCell<[u8; Self::SIZE]>,
    offset: AtomicUsize,
}

impl ArenaAllocator {
    const SIZE: usize = 16 * 1024 * 1024;  // 16MB
    
    pub const fn new() -> Self {
        Self {
            buffer: UnsafeCell::new([0; Self::SIZE]),
            offset: AtomicUsize::new(0),
        }
    }
    
    pub fn reset(&self) {
        self.offset.store(0, Ordering::SeqCst);
    }
}

unsafe impl Sync for ArenaAllocator {}

unsafe impl GlobalAlloc for ArenaAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        loop {
            let current = self.offset.load(Ordering::Relaxed);
            let aligned = (current + layout.align() - 1) & !(layout.align() - 1);
            let new_offset = aligned + layout.size();
            
            if new_offset > Self::SIZE {
                return core::ptr::null_mut();
            }
            
            if self.offset.compare_exchange_weak(
                current, new_offset, Ordering::SeqCst, Ordering::Relaxed
            ).is_ok() {
                let buffer = self.buffer.get();
                return (*buffer).as_mut_ptr().add(aligned);
            }
        }
    }
    
    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {
        // Arena不释放单个分配
    }
}
```

---

## 三、Panic处理

### 3.1 panic_handler

```rust
#![no_std]
#![no_main]

use core::panic::PanicInfo;

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    // 选项1：无限循环
    loop {}
    
    // 选项2：abort
    // unsafe { core::hint::unreachable_unchecked() }
}

// 带调试信息的panic handler
#[panic_handler]
fn panic_debug(info: &PanicInfo) -> ! {
    // 如果有调试输出能力
    #[cfg(feature = "debug")]
    {
        if let Some(location) = info.location() {
            // 输出到串口或调试器
            // debug_print!("Panic at {}:{}", location.file(), location.line());
        }
    }
    
    loop {}
}
```

### 3.2 panic = "abort"

```toml
# Cargo.toml
[profile.release]
panic = "abort"  # 无栈展开，更小的二进制

[profile.dev]
panic = "abort"
```

### 3.3 自定义OOM处理

```rust
#![no_std]
#![feature(alloc_error_handler)]

extern crate alloc;

#[alloc_error_handler]
fn oom_handler(layout: core::alloc::Layout) -> ! {
    // 记录OOM事件
    // log_oom(layout.size(), layout.align());
    
    loop {}
}
```

---

## 四、no_std在HFT中的应用

### 4.1 确定性内存分配

```rust
#![no_std]

extern crate alloc;

use core::mem::MaybeUninit;

// 预分配固定大小缓冲区
pub struct FixedBuffer<T, const N: usize> {
    data: [MaybeUninit<T>; N],
    len: usize,
}

impl<T, const N: usize> FixedBuffer<T, N> {
    pub const fn new() -> Self {
        Self {
            data: unsafe { MaybeUninit::uninit().assume_init() },
            len: 0,
        }
    }
    
    pub fn push(&mut self, value: T) -> Result<(), T> {
        if self.len >= N {
            return Err(value);
        }
        self.data[self.len].write(value);
        self.len += 1;
        Ok(())
    }
    
    pub fn pop(&mut self) -> Option<T> {
        if self.len == 0 {
            return None;
        }
        self.len -= 1;
        Some(unsafe { self.data[self.len].assume_init_read() })
    }
    
    pub fn clear(&mut self) {
        for i in 0..self.len {
            unsafe { self.data[i].assume_init_drop(); }
        }
        self.len = 0;
    }
}

impl<T, const N: usize> Drop for FixedBuffer<T, N> {
    fn drop(&mut self) {
        self.clear();
    }
}
```

### 4.2 无分配消息解析

```rust
#![no_std]

#[repr(C, packed)]
pub struct RawMessage {
    msg_type: u8,
    length: u16,
    timestamp: u64,
    // 后续是可变长度数据
}

impl RawMessage {
    /// 零拷贝解析
    pub fn from_bytes(bytes: &[u8]) -> Option<&Self> {
        if bytes.len() < core::mem::size_of::<Self>() {
            return None;
        }
        
        let msg = unsafe {
            &*(bytes.as_ptr() as *const RawMessage)
        };
        
        // 验证长度
        let total_len = core::mem::size_of::<Self>() + msg.length as usize;
        if bytes.len() < total_len {
            return None;
        }
        
        Some(msg)
    }
    
    pub fn payload(&self) -> &[u8] {
        let header_size = core::mem::size_of::<Self>();
        unsafe {
            core::slice::from_raw_parts(
                (self as *const Self as *const u8).add(header_size),
                self.length as usize,
            )
        }
    }
}
```

### 4.3 Lock-free结构

```rust
#![no_std]

use core::sync::atomic::{AtomicUsize, Ordering};
use core::cell::UnsafeCell;
use core::mem::MaybeUninit;

// 无分配的SPSC队列
pub struct SpscQueue<T, const N: usize> {
    buffer: UnsafeCell<[MaybeUninit<T>; N]>,
    head: AtomicUsize,
    tail: AtomicUsize,
}

unsafe impl<T: Send, const N: usize> Send for SpscQueue<T, N> {}
unsafe impl<T: Send, const N: usize> Sync for SpscQueue<T, N> {}

impl<T, const N: usize> SpscQueue<T, N> {
    pub const fn new() -> Self {
        Self {
            buffer: UnsafeCell::new(unsafe { MaybeUninit::uninit().assume_init() }),
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
        }
    }
    
    pub fn push(&self, value: T) -> Result<(), T> {
        let head = self.head.load(Ordering::Relaxed);
        let next_head = (head + 1) % N;
        
        if next_head == self.tail.load(Ordering::Acquire) {
            return Err(value);  // 满
        }
        
        unsafe {
            (*self.buffer.get())[head].write(value);
        }
        self.head.store(next_head, Ordering::Release);
        Ok(())
    }
    
    pub fn pop(&self) -> Option<T> {
        let tail = self.tail.load(Ordering::Relaxed);
        
        if tail == self.head.load(Ordering::Acquire) {
            return None;  // 空
        }
        
        let value = unsafe {
            (*self.buffer.get())[tail].assume_init_read()
        };
        self.tail.store((tail + 1) % N, Ordering::Release);
        Some(value)
    }
}
```

---

## 五、嵌入式HAL

### 5.1 embedded-hal trait

```rust
#![no_std]

// embedded-hal定义了硬件抽象接口
use embedded_hal::digital::v2::{OutputPin, InputPin};
use embedded_hal::blocking::delay::DelayMs;

// 通用的LED闪烁
pub fn blink<P: OutputPin, D: DelayMs<u32>>(
    led: &mut P,
    delay: &mut D,
    times: u32,
) -> Result<(), P::Error> {
    for _ in 0..times {
        led.set_high()?;
        delay.delay_ms(500);
        led.set_low()?;
        delay.delay_ms(500);
    }
    Ok(())
}
```

### 5.2 实现HAL trait

```rust
#![no_std]

use embedded_hal::digital::v2::OutputPin;

// 假设的GPIO寄存器
struct GpioPin {
    port: u8,
    pin: u8,
}

impl OutputPin for GpioPin {
    type Error = core::convert::Infallible;
    
    fn set_high(&mut self) -> Result<(), Self::Error> {
        unsafe {
            // 写入硬件寄存器
            let reg = (0x4000_0000 + self.port as usize * 0x100) as *mut u32;
            *reg |= 1 << self.pin;
        }
        Ok(())
    }
    
    fn set_low(&mut self) -> Result<(), Self::Error> {
        unsafe {
            let reg = (0x4000_0000 + self.port as usize * 0x100) as *mut u32;
            *reg &= !(1 << self.pin);
        }
        Ok(())
    }
}
```

---

## 总结

| 功能 | std | core | alloc |
|------|-----|------|-------|
| 基础类型 | ✓ | ✓ | ✓ |
| Vec/String | ✓ | ✗ | ✓ |
| 文件IO | ✓ | ✗ | ✗ |
| 网络 | ✓ | ✗ | ✗ |
| 线程 | ✓ | ✗ | ✗ |
| 原子操作 | ✓ | ✓ | ✓ |

**HFT no_std应用场景**：
1. 确定性内存分配
2. 避免系统调用开销
3. 精确控制内存布局
4. 裸机/内核旁路网络
5. FPGA协处理器接口

---

## 相关文章

- [上一篇：Rust编译器优化详解](/articles/rust/rust-12-Rust编译器优化详解/)
- [下一篇：HFT-Rust Lock-Free编程](/articles/rust/rust-14-HFT-Rust-Lock-Free编程/)
