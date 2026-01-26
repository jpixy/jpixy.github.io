+++
title = "10.Rust与C/C++互操作"
date = 2026-01-21
description = "深入剖析Rust与C/C++的互操作技术，包括FFI声明、bindgen/cbindgen、内存传递、回调函数和ABI兼容"
[taxonomies]
tags = ["Rust", "FFI", "C++", "互操作", "HFT"]
+++

## 概述

在HFT系统中，Rust常需要与现有的C/C++代码库集成。本文详细介绍Rust与C/C++互操作的各种技术。

---

## 一、基础FFI

### 1.1 调用C函数

```rust
use std::ffi::{c_char, c_int, c_void, CStr, CString};

// 声明外部C函数
extern "C" {
    fn printf(format: *const c_char, ...) -> c_int;
    fn malloc(size: usize) -> *mut c_void;
    fn free(ptr: *mut c_void);
    fn memcpy(dest: *mut c_void, src: *const c_void, n: usize) -> *mut c_void;
}

fn main() {
    // 调用printf
    let msg = CString::new("Hello from Rust: %d\n").unwrap();
    unsafe {
        printf(msg.as_ptr(), 42);
    }
    
    // 使用malloc/free
    unsafe {
        let ptr = malloc(100) as *mut u8;
        if !ptr.is_null() {
            *ptr = 42;
            free(ptr as *mut c_void);
        }
    }
}
```

### 1.2 导出函数给C

```rust
// 导出给C调用
#[no_mangle]
pub extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[no_mangle]
pub extern "C" fn rust_strlen(s: *const c_char) -> usize {
    if s.is_null() {
        return 0;
    }
    unsafe { CStr::from_ptr(s).to_bytes().len() }
}

// 对应的C头文件：
// int32_t add(int32_t a, int32_t b);
// size_t rust_strlen(const char* s);
```

### 1.3 结构体传递

```rust
// 使用C布局
#[repr(C)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

#[repr(C)]
pub struct Rectangle {
    pub top_left: Point,
    pub bottom_right: Point,
}

#[no_mangle]
pub extern "C" fn create_rect(x1: f64, y1: f64, x2: f64, y2: f64) -> Rectangle {
    Rectangle {
        top_left: Point { x: x1, y: y1 },
        bottom_right: Point { x: x2, y: y2 },
    }
}

#[no_mangle]
pub extern "C" fn rect_area(rect: &Rectangle) -> f64 {
    let width = (rect.bottom_right.x - rect.top_left.x).abs();
    let height = (rect.bottom_right.y - rect.top_left.y).abs();
    width * height
}
```

---

## 二、bindgen

### 2.1 基本使用

```toml
# Cargo.toml
[build-dependencies]
bindgen = "0.69"

[dependencies]
libc = "0.2"
```

```rust
// build.rs
fn main() {
    // 告诉Cargo重新编译条件
    println!("cargo:rerun-if-changed=wrapper.h");
    
    // 生成绑定
    let bindings = bindgen::Builder::default()
        .header("wrapper.h")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks))
        .generate()
        .expect("Unable to generate bindings");
    
    // 写入文件
    let out_path = std::path::PathBuf::from(std::env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}
```

```c
// wrapper.h
#include <stdint.h>

typedef struct {
    int32_t id;
    double price;
    int64_t quantity;
} Order;

Order* create_order(int32_t id, double price, int64_t quantity);
void free_order(Order* order);
double get_order_value(const Order* order);
```

```rust
// src/lib.rs
#![allow(non_upper_case_globals)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]

include!(concat!(env!("OUT_DIR"), "/bindings.rs"));

// 使用生成的绑定
pub fn example() {
    unsafe {
        let order = create_order(1, 100.5, 1000);
        if !order.is_null() {
            let value = get_order_value(order);
            println!("Order value: {}", value);
            free_order(order);
        }
    }
}
```

### 2.2 高级配置

```rust
// build.rs
let bindings = bindgen::Builder::default()
    .header("wrapper.h")
    // 包含路径
    .clang_arg("-I/path/to/includes")
    // 只生成特定类型
    .allowlist_type("Order")
    .allowlist_function("create_order")
    // 生成Debug/Clone
    .derive_debug(true)
    .derive_copy(true)
    .derive_default(true)
    // 布局测试
    .layout_tests(true)
    // 使用core代替std
    .use_core()
    .generate()
    .expect("Unable to generate bindings");
```

---

## 三、cbindgen

### 3.1 生成C头文件

```toml
# Cargo.toml
[package]
name = "mylib"

[lib]
crate-type = ["cdylib", "staticlib"]

[build-dependencies]
cbindgen = "0.26"
```

```rust
// build.rs
fn main() {
    let crate_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    
    cbindgen::Builder::new()
        .with_crate(crate_dir)
        .with_language(cbindgen::Language::C)
        .generate()
        .expect("Unable to generate bindings")
        .write_to_file("include/mylib.h");
}
```

```rust
// src/lib.rs

/// 订单结构体
#[repr(C)]
pub struct Order {
    pub id: i32,
    pub price: f64,
    pub quantity: i64,
}

/// 创建新订单
#[no_mangle]
pub extern "C" fn order_new(id: i32, price: f64, quantity: i64) -> *mut Order {
    Box::into_raw(Box::new(Order { id, price, quantity }))
}

/// 释放订单
/// # Safety
/// ptr必须是order_new返回的有效指针
#[no_mangle]
pub unsafe extern "C" fn order_free(ptr: *mut Order) {
    if !ptr.is_null() {
        drop(Box::from_raw(ptr));
    }
}

/// 计算订单价值
/// # Safety
/// ptr必须指向有效的Order
#[no_mangle]
pub unsafe extern "C" fn order_value(ptr: *const Order) -> f64 {
    if ptr.is_null() {
        return 0.0;
    }
    (*ptr).price * (*ptr).quantity as f64
}
```

生成的头文件：

```c
// include/mylib.h
#include <stdint.h>

typedef struct Order {
    int32_t id;
    double price;
    int64_t quantity;
} Order;

struct Order *order_new(int32_t id, double price, int64_t quantity);
void order_free(struct Order *ptr);
double order_value(const struct Order *ptr);
```

---

## 四、内存管理

### 4.1 所有权传递

```rust
// Rust分配，C释放 - 不推荐
// C分配，Rust释放 - 不推荐

// 推荐：谁分配谁释放

// Rust分配，Rust释放
#[no_mangle]
pub extern "C" fn create_buffer(size: usize) -> *mut u8 {
    let mut buf = Vec::with_capacity(size);
    buf.resize(size, 0);
    let ptr = buf.as_mut_ptr();
    std::mem::forget(buf);  // 防止drop
    ptr
}

#[no_mangle]
pub unsafe extern "C" fn free_buffer(ptr: *mut u8, size: usize) {
    if !ptr.is_null() {
        // 重建Vec让它drop
        drop(Vec::from_raw_parts(ptr, size, size));
    }
}
```

### 4.2 借用语义

```rust
// 传递引用（借用）
#[no_mangle]
pub extern "C" fn process_data(data: *const u8, len: usize) -> i32 {
    if data.is_null() || len == 0 {
        return -1;
    }
    
    let slice = unsafe { std::slice::from_raw_parts(data, len) };
    
    // 处理数据，不获取所有权
    slice.iter().map(|&x| x as i32).sum()
}

// 可变借用
#[no_mangle]
pub unsafe extern "C" fn modify_data(data: *mut u8, len: usize) {
    if data.is_null() || len == 0 {
        return;
    }
    
    let slice = std::slice::from_raw_parts_mut(data, len);
    for byte in slice.iter_mut() {
        *byte = byte.wrapping_add(1);
    }
}
```

### 4.3 字符串处理

```rust
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

// 接收C字符串（借用）
#[no_mangle]
pub unsafe extern "C" fn process_string(s: *const c_char) -> i32 {
    if s.is_null() {
        return -1;
    }
    
    let cstr = CStr::from_ptr(s);
    match cstr.to_str() {
        Ok(s) => s.len() as i32,
        Err(_) => -1,
    }
}

// 返回C字符串（Rust分配）
#[no_mangle]
pub extern "C" fn create_greeting(name: *const c_char) -> *mut c_char {
    let name = if name.is_null() {
        "World"
    } else {
        unsafe {
            CStr::from_ptr(name)
                .to_str()
                .unwrap_or("World")
        }
    };
    
    let greeting = format!("Hello, {}!", name);
    CString::new(greeting)
        .map(|s| s.into_raw())
        .unwrap_or(std::ptr::null_mut())
}

#[no_mangle]
pub unsafe extern "C" fn free_string(s: *mut c_char) {
    if !s.is_null() {
        drop(CString::from_raw(s));
    }
}
```

---

## 五、回调函数

### 5.1 C回调Rust

```rust
// 定义回调类型
pub type Callback = extern "C" fn(i32) -> i32;
pub type CallbackWithData = extern "C" fn(*mut std::ffi::c_void, i32) -> i32;

#[no_mangle]
pub extern "C" fn call_with_callback(value: i32, cb: Callback) -> i32 {
    cb(value)
}

// 带用户数据的回调
#[no_mangle]
pub extern "C" fn call_with_data(
    value: i32,
    cb: CallbackWithData,
    user_data: *mut std::ffi::c_void,
) -> i32 {
    cb(user_data, value)
}
```

### 5.2 Rust回调C

```rust
extern "C" {
    fn register_handler(
        handler: extern "C" fn(i32, *mut std::ffi::c_void),
        user_data: *mut std::ffi::c_void,
    );
}

// Rust函数作为回调
extern "C" fn my_handler(value: i32, user_data: *mut std::ffi::c_void) {
    println!("Received: {}", value);
    
    if !user_data.is_null() {
        let data = unsafe { &*(user_data as *const String) };
        println!("User data: {}", data);
    }
}

fn setup_callback() {
    let my_string = Box::new(String::from("Hello"));
    let ptr = Box::into_raw(my_string);
    
    unsafe {
        register_handler(my_handler, ptr as *mut std::ffi::c_void);
    }
    
    // 注意：需要在适当时机释放my_string
}
```

### 5.3 闭包作为回调

```rust
// 闭包不能直接作为extern "C"函数
// 需要使用trampoline模式

struct CallbackWrapper<F> {
    callback: F,
}

extern "C" fn trampoline<F>(user_data: *mut std::ffi::c_void, value: i32) -> i32
where
    F: FnMut(i32) -> i32,
{
    let wrapper = unsafe { &mut *(user_data as *mut CallbackWrapper<F>) };
    (wrapper.callback)(value)
}

fn with_closure<F>(mut f: F)
where
    F: FnMut(i32) -> i32,
{
    let mut wrapper = CallbackWrapper { callback: f };
    let ptr = &mut wrapper as *mut _ as *mut std::ffi::c_void;
    
    // 调用需要回调的C函数
    // call_c_function(trampoline::<F>, ptr);
}
```

---

## 六、异常安全

### 6.1 panic边界

```rust
use std::panic::{catch_unwind, AssertUnwindSafe};

// 不要让panic跨越FFI边界！

// 错误做法
#[no_mangle]
pub extern "C" fn bad_function() {
    panic!("This will abort or cause UB!");
}

// 正确做法
#[no_mangle]
pub extern "C" fn safe_function() -> i32 {
    let result = catch_unwind(|| {
        // 可能panic的代码
        risky_operation()
    });
    
    match result {
        Ok(value) => value,
        Err(_) => -1,  // 返回错误码
    }
}

fn risky_operation() -> i32 {
    42
}
```

### 6.2 错误处理模式

```rust
#[repr(C)]
pub struct Result {
    pub success: bool,
    pub value: i32,
    pub error_message: *mut c_char,
}

impl Result {
    fn ok(value: i32) -> Self {
        Self {
            success: true,
            value,
            error_message: std::ptr::null_mut(),
        }
    }
    
    fn err(msg: &str) -> Self {
        let c_msg = CString::new(msg)
            .map(|s| s.into_raw())
            .unwrap_or(std::ptr::null_mut());
        
        Self {
            success: false,
            value: 0,
            error_message: c_msg,
        }
    }
}

#[no_mangle]
pub extern "C" fn divide(a: i32, b: i32) -> Result {
    if b == 0 {
        return Result::err("Division by zero");
    }
    Result::ok(a / b)
}

#[no_mangle]
pub unsafe extern "C" fn free_result(result: *mut Result) {
    if !result.is_null() && !(*result).error_message.is_null() {
        drop(CString::from_raw((*result).error_message));
    }
}
```

---

## 七、C++互操作

### 7.1 使用cxx

```toml
# Cargo.toml
[dependencies]
cxx = "1.0"

[build-dependencies]
cxx-build = "1.0"
```

```rust
// src/main.rs
#[cxx::bridge]
mod ffi {
    // 共享结构体
    struct Order {
        id: i32,
        price: f64,
        quantity: i64,
    }
    
    // C++提供的函数
    unsafe extern "C++" {
        include!("mylib/include/order_book.h");
        
        type OrderBook;
        
        fn new_order_book() -> UniquePtr<OrderBook>;
        fn add_order(self: Pin<&mut OrderBook>, order: &Order) -> bool;
        fn get_best_bid(self: &OrderBook) -> f64;
    }
    
    // Rust提供给C++的函数
    extern "Rust" {
        fn validate_order(order: &Order) -> bool;
    }
}

fn validate_order(order: &ffi::Order) -> bool {
    order.price > 0.0 && order.quantity > 0
}

fn main() {
    let mut book = ffi::new_order_book();
    let order = ffi::Order {
        id: 1,
        price: 100.5,
        quantity: 1000,
    };
    
    book.pin_mut().add_order(&order);
    println!("Best bid: {}", book.get_best_bid());
}
```

---

## 总结

| 工具 | 用途 | 适用场景 |
|------|------|----------|
| 手写extern "C" | 简单接口 | 少量函数 |
| bindgen | 生成Rust绑定 | 使用C库 |
| cbindgen | 生成C头文件 | 暴露Rust API |
| cxx | C++互操作 | C++集成 |

**最佳实践**：
1. 使用#[repr(C)]确保ABI兼容
2. 谁分配谁释放
3. 不要让panic跨越FFI边界
4. 提供配套的free函数
5. 使用Miri验证内存安全
