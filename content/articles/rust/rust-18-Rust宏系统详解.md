+++
title = "18.Rust宏系统详解"
date = 2026-01-21
description = "深入剖析Rust的宏系统，包括声明宏、过程宏、derive宏、属性宏以及编译期代码生成"
[taxonomies]
tags = ["Rust", "宏", "元编程", "过程宏", "代码生成"]
+++

## 概述

Rust的宏系统是其最强大的元编程工具。本文深入介绍声明宏和过程宏的使用。

---

## 一、声明宏（macro_rules!）

### 1.1 基本语法

```rust
// 简单的声明宏
macro_rules! say_hello {
    () => {
        println!("Hello!");
    };
}

// 带参数
macro_rules! say {
    ($msg:expr) => {
        println!("{}", $msg);
    };
}

// 多个模式
macro_rules! create_function {
    ($name:ident) => {
        fn $name() {
            println!("Function {} called", stringify!($name));
        }
    };
    ($name:ident, $body:expr) => {
        fn $name() -> i32 {
            $body
        }
    };
}

fn main() {
    say_hello!();
    say!("Hi there");
    
    create_function!(foo);
    create_function!(bar, 42);
    
    foo();  // "Function foo called"
    assert_eq!(bar(), 42);
}
```

### 1.2 匹配器类型

```rust
// 常用匹配器：
// $name:expr   - 表达式
// $name:ident  - 标识符
// $name:ty     - 类型
// $name:pat    - 模式
// $name:stmt   - 语句
// $name:block  - 代码块
// $name:item   - 项（函数、struct等）
// $name:path   - 路径（std::vec::Vec）
// $name:tt     - 单个token tree
// $name:literal - 字面量

macro_rules! example {
    // 表达式
    (expr: $e:expr) => { $e };
    
    // 标识符
    (ident: $i:ident) => { let $i = 42; };
    
    // 类型
    (ty: $t:ty) => { let _: $t = Default::default(); };
    
    // 模式
    (pat: $p:pat = $e:expr) => { let $p = $e; };
    
    // 代码块
    (block: $b:block) => { $b };
}

fn main() {
    example!(expr: 1 + 2);
    example!(ident: x);
    example!(ty: i32);
    example!(pat: (a, b) = (1, 2));
    example!(block: { println!("block"); });
}
```

### 1.3 重复

```rust
// 使用$(...)*表示重复

// 基本重复
macro_rules! vec_of_strings {
    ($($x:expr),*) => {
        vec![$($x.to_string()),*]
    };
}

// 带分隔符的重复
macro_rules! hashmap {
    ($($key:expr => $value:expr),* $(,)?) => {{
        let mut map = std::collections::HashMap::new();
        $(map.insert($key, $value);)*
        map
    }};
}

// 嵌套重复
macro_rules! matrix {
    ($([$($x:expr),*]),*) => {
        vec![$(vec![$($x),*]),*]
    };
}

fn main() {
    let v = vec_of_strings!["hello", "world"];
    
    let m = hashmap! {
        "a" => 1,
        "b" => 2,
    };
    
    let mat = matrix![
        [1, 2, 3],
        [4, 5, 6]
    ];
}
```

### 1.4 递归宏

```rust
// 实现类似Lisp的列表
macro_rules! list {
    () => { None };
    ($head:expr $(, $tail:expr)*) => {
        Some(($head, Box::new(list!($($tail),*))))
    };
}

// 计算参数数量
macro_rules! count {
    () => { 0 };
    ($head:tt $($tail:tt)*) => { 1 + count!($($tail)*) };
}

fn main() {
    let list = list![1, 2, 3];
    let n = count!(a b c d e);  // 5
    println!("Count: {}", n);
}
```

---

## 二、过程宏

### 2.1 项目结构

```toml
# Cargo.toml (过程宏crate)
[lib]
proc-macro = true

[dependencies]
syn = { version = "2.0", features = ["full"] }
quote = "1.0"
proc-macro2 = "1.0"
```

### 2.2 Derive宏

```rust
// my_derive/src/lib.rs
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(HelloMacro)]
pub fn hello_macro_derive(input: TokenStream) -> TokenStream {
    let ast = parse_macro_input!(input as DeriveInput);
    let name = &ast.ident;
    
    let gen = quote! {
        impl HelloMacro for #name {
            fn hello_macro() {
                println!("Hello, I'm {}!", stringify!(#name));
            }
        }
    };
    
    gen.into()
}

// 使用
// use my_derive::HelloMacro;
//
// trait HelloMacro {
//     fn hello_macro();
// }
//
// #[derive(HelloMacro)]
// struct Pancakes;
//
// fn main() {
//     Pancakes::hello_macro();  // "Hello, I'm Pancakes!"
// }
```

### 2.3 带属性的Derive宏

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput, Data, Fields};

#[proc_macro_derive(Builder, attributes(builder))]
pub fn builder_derive(input: TokenStream) -> TokenStream {
    let ast = parse_macro_input!(input as DeriveInput);
    let name = &ast.ident;
    let builder_name = syn::Ident::new(&format!("{}Builder", name), name.span());
    
    let fields = match &ast.data {
        Data::Struct(data) => match &data.fields {
            Fields::Named(fields) => &fields.named,
            _ => panic!("Only named fields supported"),
        },
        _ => panic!("Only structs supported"),
    };
    
    let field_names: Vec<_> = fields.iter().map(|f| &f.ident).collect();
    let field_types: Vec<_> = fields.iter().map(|f| &f.ty).collect();
    
    let gen = quote! {
        #[derive(Default)]
        pub struct #builder_name {
            #(#field_names: Option<#field_types>),*
        }
        
        impl #builder_name {
            #(
                pub fn #field_names(mut self, value: #field_types) -> Self {
                    self.#field_names = Some(value);
                    self
                }
            )*
            
            pub fn build(self) -> Result<#name, &'static str> {
                Ok(#name {
                    #(#field_names: self.#field_names.ok_or(concat!(stringify!(#field_names), " is required"))?),*
                })
            }
        }
        
        impl #name {
            pub fn builder() -> #builder_name {
                #builder_name::default()
            }
        }
    };
    
    gen.into()
}
```

### 2.4 属性宏

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, ItemFn};

#[proc_macro_attribute]
pub fn log_call(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as ItemFn);
    let name = &input.sig.ident;
    let block = &input.block;
    let sig = &input.sig;
    let vis = &input.vis;
    
    let gen = quote! {
        #vis #sig {
            println!("Calling {}", stringify!(#name));
            let start = std::time::Instant::now();
            let result = (|| #block)();
            println!("{} took {:?}", stringify!(#name), start.elapsed());
            result
        }
    };
    
    gen.into()
}

// 使用
// #[log_call]
// fn expensive_operation() -> i32 {
//     std::thread::sleep(std::time::Duration::from_millis(100));
//     42
// }
```

### 2.5 函数式宏

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, LitStr};

#[proc_macro]
pub fn sql(input: TokenStream) -> TokenStream {
    let sql_str = parse_macro_input!(input as LitStr);
    let value = sql_str.value();
    
    // 编译期SQL验证（简化）
    if !value.to_uppercase().starts_with("SELECT") 
        && !value.to_uppercase().starts_with("INSERT")
        && !value.to_uppercase().starts_with("UPDATE") 
    {
        return syn::Error::new(sql_str.span(), "Invalid SQL")
            .to_compile_error()
            .into();
    }
    
    let gen = quote! {
        #sql_str
    };
    
    gen.into()
}

// 使用
// let query = sql!("SELECT * FROM users");
// let invalid = sql!("DROP TABLE users");  // 编译错误
```

---

## 三、常见宏模式

### 3.1 延迟计算

```rust
macro_rules! lazy_static {
    ($name:ident : $ty:ty = $init:expr) => {
        static $name: std::sync::LazyLock<$ty> = std::sync::LazyLock::new(|| $init);
    };
}

lazy_static!(CONFIG: String = {
    println!("Initializing config...");
    String::from("default config")
});

fn main() {
    println!("Before accessing CONFIG");
    println!("{}", *CONFIG);  // 这时才初始化
    println!("{}", *CONFIG);  // 使用缓存
}
```

### 3.2 枚举dispatch

```rust
macro_rules! enum_dispatch {
    (
        enum $enum_name:ident {
            $($variant:ident($inner:ty)),* $(,)?
        }
        
        trait $trait_name:ident {
            $(fn $method:ident(&self $(, $arg:ident: $arg_ty:ty)*) -> $ret:ty;)*
        }
    ) => {
        enum $enum_name {
            $($variant($inner)),*
        }
        
        impl $trait_name for $enum_name {
            $(
                fn $method(&self $(, $arg: $arg_ty)*) -> $ret {
                    match self {
                        $($enum_name::$variant(inner) => inner.$method($($arg),*)),*
                    }
                }
            )*
        }
    };
}

trait Animal {
    fn speak(&self) -> &str;
}

struct Dog;
impl Animal for Dog {
    fn speak(&self) -> &str { "Woof!" }
}

struct Cat;
impl Animal for Cat {
    fn speak(&self) -> &str { "Meow!" }
}

enum_dispatch! {
    enum AnyAnimal {
        Dog(Dog),
        Cat(Cat),
    }
    
    trait Animal {
        fn speak(&self) -> &str;
    }
}
```

### 3.3 测试生成

```rust
macro_rules! test_cases {
    ($($name:ident: $input:expr => $expected:expr),* $(,)?) => {
        $(
            #[test]
            fn $name() {
                assert_eq!(process($input), $expected);
            }
        )*
    };
}

fn process(x: i32) -> i32 {
    x * 2
}

test_cases! {
    test_zero: 0 => 0,
    test_positive: 5 => 10,
    test_negative: -3 => -6,
}
```

---

## 四、HFT宏应用

### 4.1 消息序列化

```rust
macro_rules! define_message {
    (
        $name:ident {
            $($field:ident: $ty:ty),* $(,)?
        }
    ) => {
        #[repr(C, packed)]
        pub struct $name {
            $(pub $field: $ty),*
        }
        
        impl $name {
            pub const SIZE: usize = std::mem::size_of::<Self>();
            
            pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> &Self {
                unsafe { &*(bytes.as_ptr() as *const Self) }
            }
            
            pub fn to_bytes(&self) -> [u8; Self::SIZE] {
                unsafe { std::ptr::read_unaligned(self as *const Self as *const [u8; Self::SIZE]) }
            }
        }
    };
}

define_message! {
    MarketData {
        symbol_id: u32,
        price: u64,
        quantity: u32,
        timestamp: u64,
    }
}
```

### 4.2 性能计时

```rust
macro_rules! timed {
    ($name:expr, $block:expr) => {{
        let __start = std::time::Instant::now();
        let __result = $block;
        let __elapsed = __start.elapsed();
        
        #[cfg(feature = "timing")]
        println!("{}: {:?}", $name, __elapsed);
        
        __result
    }};
}

fn main() {
    let result = timed!("computation", {
        let mut sum = 0;
        for i in 0..1000000 {
            sum += i;
        }
        sum
    });
}
```

---

## 五、调试宏

### 5.1 展开查看

```bash
# 使用cargo-expand
cargo install cargo-expand
cargo expand

# 只展开特定模块
cargo expand module_name

# 展开特定项
cargo expand --item function_name
```

### 5.2 调试技巧

```rust
// 使用compile_error!显示信息
macro_rules! debug_macro {
    ($($tt:tt)*) => {
        compile_error!(stringify!($($tt)*));
    };
}

// 使用trace_macros（nightly）
#![feature(trace_macros)]
trace_macros!(true);
my_macro!(something);
trace_macros!(false);
```

---

## 总结

| 宏类型 | 语法 | 用途 |
|--------|------|------|
| 声明宏 | macro_rules! | 简单代码生成 |
| Derive宏 | #[derive()] | 自动实现trait |
| 属性宏 | #[attr] | 修改项 |
| 函数式宏 | name!() | 自定义语法 |

**最佳实践**：
1. 优先使用声明宏（更简单）
2. 过程宏用于复杂场景
3. 使用cargo-expand调试
4. 提供清晰的错误消息
5. 编写文档和示例

---

## 相关文章

- [上一篇：Rust性能调优实战](/articles/rust/rust-17-Rust性能调优实战/)
- [下一篇：Rust面试指南](/articles/rust/rust-19-Rust面试指南/)
