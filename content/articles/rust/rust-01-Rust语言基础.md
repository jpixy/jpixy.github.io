+++
title = "Rust语言基础"
date = 2026-01-19
weight = 1000
description = "Rust入门：语法基础、数据类型、控制流、函数、模块系统"
[taxonomies]
tags = ["Rust", "基础", "入门"]
+++

## Rust特点

### 设计理念

- **内存安全**：无GC的内存安全
- **并发安全**：编译期防止数据竞争
- **零成本抽象**：高级特性无运行时开销
- **系统级性能**：与C/C++同级

### 适用场景

- 系统编程
- 嵌入式开发
- WebAssembly
- 命令行工具
- 网络服务
- 区块链

---

## 基本语法

### Hello World

```rust
fn main() {
    println!("Hello, World!");
}
```

### 变量

```rust
// 不可变变量（默认）
let x = 5;
// x = 6;  // 错误！不可变

// 可变变量
let mut y = 5;
y = 6;  // OK

// 常量
const MAX_POINTS: u32 = 100_000;

// 静态变量
static HELLO: &str = "Hello";

// 遮蔽（Shadowing）
let x = 5;
let x = x + 1;  // 新变量，可以改变类型
let x = "hello";  // OK
```

### 类型推断

```rust
let x = 5;           // i32
let y: i64 = 5;      // 显式指定
let z = 5i64;        // 后缀指定
```

---

## 数据类型

### 标量类型

```rust
// 整数
let a: i8 = -128;
let b: u8 = 255;
let c: i32 = 100;     // 默认
let d: i64 = 100;
let e: isize = 100;   // 架构相关

// 浮点
let f: f64 = 3.14;    // 默认
let g: f32 = 3.14;

// 布尔
let t: bool = true;

// 字符（Unicode）
let c: char = '中';
```

### 复合类型

```rust
// 元组
let tup: (i32, f64, u8) = (500, 6.4, 1);
let (x, y, z) = tup;  // 解构
let first = tup.0;     // 索引

// 数组
let arr: [i32; 5] = [1, 2, 3, 4, 5];
let first = arr[0];
let same = [3; 5];     // [3, 3, 3, 3, 3]

// 切片
let slice: &[i32] = &arr[1..3];
```

### 字符串

```rust
// 字符串字面量（&str）
let s1: &str = "hello";

// String（堆分配）
let s2: String = String::from("hello");
let s3 = "hello".to_string();

// 拼接
let s4 = s2 + " world";      // s2被移动
let s5 = format!("{} {}", s1, "world");
```

---

## 控制流

### if表达式

```rust
let number = 5;

if number < 5 {
    println!("less than 5");
} else if number > 5 {
    println!("greater than 5");
} else {
    println!("equal to 5");
}

// if是表达式，有返回值
let result = if number > 5 { "big" } else { "small" };
```

### 循环

```rust
// loop（无限循环）
let result = loop {
    counter += 1;
    if counter == 10 {
        break counter * 2;  // 返回值
    }
};

// while
while number != 0 {
    number -= 1;
}

// for
for i in 0..5 {
    println!("{}", i);
}

for element in arr.iter() {
    println!("{}", element);
}

for (index, value) in arr.iter().enumerate() {
    println!("{}: {}", index, value);
}
```

### match

```rust
let number = 3;

match number {
    1 => println!("one"),
    2 | 3 => println!("two or three"),
    4..=10 => println!("four to ten"),
    _ => println!("other"),
}

// match是表达式
let result = match number {
    1 => "one",
    _ => "other",
};
```

### if let

```rust
let some_value = Some(5);

if let Some(x) = some_value {
    println!("value is {}", x);
}

// 等价于
match some_value {
    Some(x) => println!("value is {}", x),
    _ => (),
}
```

---

## 函数

### 基本语法

```rust
fn add(a: i32, b: i32) -> i32 {
    a + b  // 无分号，作为返回值
}

fn print_value(x: i32) {
    println!("{}", x);
}

// 显式return
fn abs(x: i32) -> i32 {
    if x < 0 {
        return -x;
    }
    x
}
```

### 方法

```rust
struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    // 关联函数（无self）
    fn new(width: u32, height: u32) -> Self {
        Rectangle { width, height }
    }
    
    // 方法（&self）
    fn area(&self) -> u32 {
        self.width * self.height
    }
    
    // 可变引用
    fn scale(&mut self, factor: u32) {
        self.width *= factor;
        self.height *= factor;
    }
}

let rect = Rectangle::new(10, 20);
let area = rect.area();
```

### 闭包

```rust
// 闭包语法
let add = |a, b| a + b;
let result = add(1, 2);

// 带类型
let add: fn(i32, i32) -> i32 = |a, b| a + b;

// 捕获环境
let x = 5;
let add_x = |y| x + y;
```

---

## 结构体与枚举

### 结构体

```rust
struct User {
    username: String,
    email: String,
    active: bool,
}

let user = User {
    username: String::from("alice"),
    email: String::from("alice@example.com"),
    active: true,
};

// 简写
fn create_user(username: String, email: String) -> User {
    User {
        username,  // 字段和变量同名
        email,
        active: true,
    }
}

// 更新语法
let user2 = User {
    username: String::from("bob"),
    ..user  // 其余字段从user复制
};

// 元组结构体
struct Point(i32, i32, i32);
let origin = Point(0, 0, 0);
```

### 枚举

```rust
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(i32, i32, i32),
}

let msg = Message::Move { x: 10, y: 20 };

match msg {
    Message::Quit => println!("quit"),
    Message::Move { x, y } => println!("move to {}, {}", x, y),
    Message::Write(text) => println!("write: {}", text),
    Message::ChangeColor(r, g, b) => println!("color: {}, {}, {}", r, g, b),
}
```

### Option和Result

```rust
// Option
let some_number: Option<i32> = Some(5);
let no_number: Option<i32> = None;

match some_number {
    Some(n) => println!("{}", n),
    None => println!("no value"),
}

// Result
fn divide(a: i32, b: i32) -> Result<i32, String> {
    if b == 0 {
        Err(String::from("division by zero"))
    } else {
        Ok(a / b)
    }
}

match divide(10, 2) {
    Ok(result) => println!("{}", result),
    Err(e) => println!("error: {}", e),
}

// ?操作符
fn try_divide(a: i32, b: i32) -> Result<i32, String> {
    let result = divide(a, b)?;
    Ok(result * 2)
}
```

---

## 模块系统

### 模块定义

```rust
// 在同一文件
mod my_module {
    pub fn public_function() {
        println!("public");
    }
    
    fn private_function() {
        println!("private");
    }
}

my_module::public_function();
```

### 文件组织

```
src/
├── main.rs
├── lib.rs
└── module/
    ├── mod.rs
    └── submodule.rs
```

### use语句

```rust
use std::collections::HashMap;
use std::io::{self, Read, Write};
use crate::my_module::public_function;

// 别名
use std::collections::HashMap as Map;
```

### Cargo.toml

```toml
[package]
name = "my_project"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = "1.0"
tokio = { version = "1", features = ["full"] }
```

---

## 总结

| 概念 | 说明 |
|------|------|
| 变量 | 默认不可变，mut可变 |
| 类型 | 强类型，编译期检查 |
| 控制流 | if/match都是表达式 |
| 函数 | 无分号表达式作为返回值 |
| 枚举 | 可携带数据 |
| Option/Result | 显式处理空值和错误 |
| 模块 | 明确的可见性控制 |

Rust的语法设计强调安全和明确，虽然学习曲线陡峭，但能帮助写出更安全可靠的代码。

---

## 相关文章

- [下一篇：所有权与借用](@/articles/rust/rust-02-所有权与借用.md)
