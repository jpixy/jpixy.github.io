+++
title = "10.Rust内存布局与对齐"
date = 2026-01-21
description = "深入剖析Rust的内存布局机制，包括repr属性、ZST、DST、内存对齐、union类型及其在HFT中的应用"
[taxonomies]
tags = ["Rust", "内存布局", "对齐", "HFT", "性能优化"]
+++

## 概述

理解Rust的内存布局对于编写高性能代码和FFI互操作至关重要。本文深入剖析Rust的内存表示机制。

---

## 一、默认布局

### 1.1 Rust默认布局规则

```rust
// Rust编译器可以自由重排字段以优化内存
struct DefaultLayout {
    a: u8,      // 1 byte
    b: u64,     // 8 bytes
    c: u16,     // 2 bytes
}

fn main() {
    // 编译器可能重排为: b(8) + c(2) + a(1) + padding(5) = 16
    // 或优化为: b(8) + c(2) + a(1) + padding(1) = 12
    println!("Size: {}", std::mem::size_of::<DefaultLayout>());
    
    // 无法假设字段顺序
    // 不同Rust版本可能不同
}
```

### 1.2 查看布局

```rust
use std::mem::{size_of, align_of};

fn inspect_layout<T>() {
    println!("Type: {}", std::any::type_name::<T>());
    println!("Size: {} bytes", size_of::<T>());
    println!("Align: {} bytes", align_of::<T>());
}

fn main() {
    inspect_layout::<u8>();    // Size: 1, Align: 1
    inspect_layout::<u32>();   // Size: 4, Align: 4
    inspect_layout::<u64>();   // Size: 8, Align: 8
    inspect_layout::<f64>();   // Size: 8, Align: 8
    inspect_layout::<*const u8>();  // Size: 8, Align: 8 (64位)
}
```

---

## 二、repr属性

### 2.1 repr(C)

```rust
// C兼容布局：字段按声明顺序排列
#[repr(C)]
struct CLayout {
    a: u8,      // offset 0, size 1
    // 7 bytes padding
    b: u64,     // offset 8, size 8
    c: u16,     // offset 16, size 2
    // 6 bytes padding
}
// 总大小: 24 bytes

fn main() {
    assert_eq!(std::mem::size_of::<CLayout>(), 24);
    
    // 使用offset_of宏检查偏移（nightly或memoffset crate）
    // assert_eq!(offset_of!(CLayout, a), 0);
    // assert_eq!(offset_of!(CLayout, b), 8);
    // assert_eq!(offset_of!(CLayout, c), 16);
}
```

### 2.2 repr(packed)

```rust
// 紧凑布局：无填充
#[repr(C, packed)]
struct PackedLayout {
    a: u8,      // offset 0
    b: u64,     // offset 1 (未对齐!)
    c: u16,     // offset 9
}
// 总大小: 11 bytes

fn main() {
    assert_eq!(std::mem::size_of::<PackedLayout>(), 11);
    
    // 注意：访问未对齐字段可能需要特殊处理
    let p = PackedLayout { a: 1, b: 2, c: 3 };
    
    // 直接访问可能在某些平台上出问题
    // let b_ref = &p.b;  // 这可能是UB!
    
    // 正确方式：使用read_unaligned
    let b = unsafe {
        std::ptr::read_unaligned(&p.b)
    };
}

// 也可以指定对齐
#[repr(C, packed(2))]  // 最大对齐为2
struct PackedAlign2 {
    a: u8,
    b: u64,  // 对齐到2而非8
    c: u16,
}
```

### 2.3 repr(align)

```rust
// 强制最小对齐
#[repr(C, align(64))]  // 缓存行对齐
struct CacheLineAligned {
    data: [u8; 32],
}

fn main() {
    assert_eq!(std::mem::align_of::<CacheLineAligned>(), 64);
    assert_eq!(std::mem::size_of::<CacheLineAligned>(), 64);
    
    // 用于避免False Sharing
    let arr: [CacheLineAligned; 4] = Default::default();
    // 每个元素都在独立的缓存行
}

// HFT应用：每个线程独占缓存行
#[repr(C, align(64))]
struct PerThreadData {
    counter: std::sync::atomic::AtomicU64,
    // padding to 64 bytes
}
```

### 2.4 repr(transparent)

```rust
// 与内部类型具有相同的布局
#[repr(transparent)]
struct Wrapper(u64);

#[repr(transparent)]
struct NewType<T>(T);

fn main() {
    // Wrapper和u64具有完全相同的ABI
    assert_eq!(std::mem::size_of::<Wrapper>(), std::mem::size_of::<u64>());
    
    // 可以安全地进行FFI传递
    extern "C" fn takes_u64(_: u64) {}
    // takes_u64(Wrapper(42));  // ABI兼容
}

// 常用于newtype模式
#[repr(transparent)]
struct OrderId(u64);

#[repr(transparent)]
struct Price(f64);
```

---

## 三、ZST（零大小类型）

### 3.1 基本ZST

```rust
// 单元类型
let unit: () = ();
assert_eq!(std::mem::size_of::<()>(), 0);

// 空结构体
struct Empty;
assert_eq!(std::mem::size_of::<Empty>(), 0);

// 空枚举变体
enum Never {}  // 不可实例化

// PhantomData
use std::marker::PhantomData;
struct Phantom<T> {
    marker: PhantomData<T>,
}
assert_eq!(std::mem::size_of::<Phantom<u64>>(), 0);
```

### 3.2 ZST优化

```rust
// Vec<ZST>不分配内存
let v: Vec<()> = vec![(); 1000000];
assert_eq!(v.len(), 1000000);
// 但实际不使用堆内存

// Box<ZST>
let b: Box<()> = Box::new(());
// 不分配堆内存，使用特殊的非空悬垂指针

// ZST用于标记类型
struct Marker;

struct Container<T, M> {
    data: T,
    _marker: M,  // 不占空间
}
```

### 3.3 PhantomData用途

```rust
use std::marker::PhantomData;

// 1. 表示逻辑所有权
struct Iter<'a, T> {
    ptr: *const T,
    end: *const T,
    _marker: PhantomData<&'a T>,  // 表示生命周期约束
}

// 2. 类型参数
struct Id<T> {
    id: u64,
    _marker: PhantomData<T>,
}

type UserId = Id<User>;
type OrderId = Id<Order>;

struct User;
struct Order;

// 3. 协变/逆变标记
struct Invariant<T> {
    _marker: PhantomData<fn(T) -> T>,
}
```

---

## 四、DST（动态大小类型）

### 4.1 常见DST

```rust
// str是DST
// let s: str = ...;  // 错误！大小未知

// [T]是DST
// let arr: [i32] = ...;  // 错误！

// dyn Trait是DST
trait Animal {}
// let a: dyn Animal = ...;  // 错误！

// 必须通过引用或智能指针使用
let s: &str = "hello";
let arr: &[i32] = &[1, 2, 3];
let boxed: Box<dyn Animal> = Box::new(Cat {});
```

### 4.2 胖指针

```rust
fn main() {
    // 普通引用：单指针
    let x: i32 = 42;
    let r: &i32 = &x;
    assert_eq!(std::mem::size_of_val(&r), 8);  // 8 bytes
    
    // 切片引用：双指针（ptr + len）
    let arr = [1, 2, 3, 4, 5];
    let slice: &[i32] = &arr;
    assert_eq!(std::mem::size_of_val(&slice), 16);  // 16 bytes
    
    // trait对象：双指针（ptr + vtable）
    trait Animal {
        fn speak(&self);
    }
    struct Dog;
    impl Animal for Dog {
        fn speak(&self) { println!("Woof!"); }
    }
    
    let dog = Dog;
    let animal: &dyn Animal = &dog;
    assert_eq!(std::mem::size_of_val(&animal), 16);  // 16 bytes
}
```

### 4.3 自定义DST

```rust
// 尾部切片模式
#[repr(C)]
struct Header {
    len: usize,
}

#[repr(C)]
struct Message {
    header: Header,
    data: [u8],  // DST尾部
}

impl Message {
    fn new(data: &[u8]) -> Box<Message> {
        let layout = std::alloc::Layout::from_size_align(
            std::mem::size_of::<Header>() + data.len(),
            std::mem::align_of::<Header>(),
        ).unwrap();
        
        unsafe {
            let ptr = std::alloc::alloc(layout) as *mut Header;
            (*ptr).len = data.len();
            
            let data_ptr = ptr.add(1) as *mut u8;
            std::ptr::copy_nonoverlapping(data.as_ptr(), data_ptr, data.len());
            
            Box::from_raw(std::ptr::slice_from_raw_parts_mut(ptr, data.len()) as *mut Message)
        }
    }
}
```

---

## 五、Union类型

### 5.1 基本Union

```rust
#[repr(C)]
union IntOrFloat {
    i: i32,
    f: f32,
}

fn main() {
    let mut u = IntOrFloat { i: 42 };
    
    // 访问union字段是unsafe的
    unsafe {
        println!("As int: {}", u.i);
        
        u.f = 3.14;
        println!("As float: {}", u.f);
        
        // 类型双关：将float位模式解释为int
        let bits: i32 = u.i;
        println!("Float bits: {:#010x}", bits);
    }
}
```

### 5.2 ManuallyDrop

```rust
use std::mem::ManuallyDrop;

// Union中存储需要drop的类型
union MaybeString {
    nothing: (),
    string: ManuallyDrop<String>,
}

impl MaybeString {
    fn new_string(s: String) -> Self {
        MaybeString {
            string: ManuallyDrop::new(s),
        }
    }
    
    fn new_empty() -> Self {
        MaybeString { nothing: () }
    }
    
    unsafe fn take_string(&mut self) -> String {
        ManuallyDrop::take(&mut self.string)
    }
}

fn main() {
    let mut u = MaybeString::new_string("Hello".to_string());
    unsafe {
        let s = u.take_string();
        println!("{}", s);
    }
}
```

### 5.3 类型双关

```rust
// 安全的类型双关使用transmute
fn float_bits(f: f32) -> u32 {
    unsafe { std::mem::transmute(f) }
}

fn bits_to_float(bits: u32) -> f32 {
    unsafe { std::mem::transmute(bits) }
}

// 使用union实现
#[repr(C)]
union FloatBits {
    f: f32,
    bits: u32,
}

fn float_bits_union(f: f32) -> u32 {
    let u = FloatBits { f };
    unsafe { u.bits }
}

// 标准库提供的方法
fn float_bits_std(f: f32) -> u32 {
    f.to_bits()
}
```

---

## 六、HFT内存布局优化

### 6.1 缓存友好布局

```rust
// 不好：冷热数据混合
struct BadOrder {
    id: u64,
    price: f64,
    quantity: i64,
    created_at: u64,      // 冷数据
    last_modified: u64,   // 冷数据
    user_id: u64,         // 冷数据
    notes: String,        // 冷数据
}

// 好：分离冷热数据
#[repr(C, align(64))]  // 缓存行对齐
struct HotOrderData {
    id: u64,
    price: f64,
    quantity: i64,
    _padding: [u8; 40],  // 填满缓存行
}

struct ColdOrderData {
    id: u64,
    created_at: u64,
    last_modified: u64,
    user_id: u64,
    notes: String,
}
```

### 6.2 紧凑消息格式

```rust
#[repr(C, packed)]
struct MarketDataMessage {
    msg_type: u8,
    symbol_id: u32,
    price: u64,      // 定点数，如价格 * 10000
    quantity: u32,
    timestamp_ns: u64,
}

impl MarketDataMessage {
    const SIZE: usize = std::mem::size_of::<Self>();
    
    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        unsafe {
            std::ptr::read_unaligned(bytes.as_ptr() as *const Self)
        }
    }
    
    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        unsafe {
            let mut bytes = [0u8; Self::SIZE];
            std::ptr::write_unaligned(
                bytes.as_mut_ptr() as *mut Self,
                std::ptr::read_unaligned(self),
            );
            bytes
        }
    }
}
```

### 6.3 使用数组代替指针

```rust
// 避免：间接访问
struct OrderBookBad {
    bids: Vec<Order>,  // 堆分配，间接访问
    asks: Vec<Order>,
}

// 优化：固定大小数组
const MAX_LEVELS: usize = 10;

#[repr(C)]
struct OrderBookGood {
    bid_prices: [f64; MAX_LEVELS],
    bid_quantities: [i64; MAX_LEVELS],
    ask_prices: [f64; MAX_LEVELS],
    ask_quantities: [i64; MAX_LEVELS],
    bid_count: u8,
    ask_count: u8,
}

// 数据连续存储，缓存友好
```

---

## 总结

| repr属性 | 效果 | 使用场景 |
|----------|------|----------|
| 默认 | 编译器优化布局 | 纯Rust代码 |
| repr(C) | C兼容布局 | FFI |
| repr(packed) | 无填充 | 网络协议 |
| repr(align(N)) | 强制对齐 | 缓存优化 |
| repr(transparent) | 与内部类型相同 | newtype |

**HFT最佳实践**：
1. 热路径数据使用缓存行对齐
2. 协议消息使用packed+C布局
3. 分离冷热数据
4. 使用ZST进行类型标记
5. 优先使用固定大小数组

---

## 相关文章

- [上一篇：Rust与C/C++互操作](/articles/rust/rust-09-Rust与C-C++互操作/)
- [下一篇：Trait对象与动态分发](/articles/rust/rust-11-Trait对象与动态分发/)
