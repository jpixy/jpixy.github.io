+++
title = "02.所有权与借用"
date = 2026-01-19
description = "Rust核心：所有权规则、移动语义、借用规则、引用、生命周期入门"
[taxonomies]
tags = ["Rust", "所有权", "借用"]
+++

## 所有权规则

### 三条规则

1. Rust中每个值都有一个**所有者**（owner）
2. 同一时刻只能有**一个所有者**
3. 当所有者离开作用域，值被**丢弃**（drop）

### 作用域

```rust
{
    let s = String::from("hello");  // s有效
    // 使用s
}  // s离开作用域，内存被释放
```

### 移动（Move）

```rust
let s1 = String::from("hello");
let s2 = s1;  // s1移动到s2

// println!("{}", s1);  // 错误！s1已失效

println!("{}", s2);  // OK
```

**移动发生在**：
- 赋值
- 函数传参
- 函数返回

### 克隆（Clone）

```rust
let s1 = String::from("hello");
let s2 = s1.clone();  // 深拷贝

println!("{}", s1);  // OK
println!("{}", s2);  // OK
```

### Copy trait

实现Copy的类型，赋值时自动复制而非移动：

```rust
let x = 5;
let y = x;  // x被复制

println!("{}", x);  // OK
println!("{}", y);  // OK
```

**实现Copy的类型**：
- 所有整数、浮点、布尔、字符
- 仅包含Copy类型的元组
- 不可变引用

---

## 引用与借用

### 不可变引用

```rust
fn main() {
    let s = String::from("hello");
    let len = calculate_length(&s);  // 借用，不转移所有权
    println!("Length of '{}' is {}", s, len);  // s仍然有效
}

fn calculate_length(s: &String) -> usize {
    s.len()
}
```

### 可变引用

```rust
fn main() {
    let mut s = String::from("hello");
    change(&mut s);
    println!("{}", s);  // "hello, world"
}

fn change(s: &mut String) {
    s.push_str(", world");
}
```

### 借用规则

在同一作用域内：
- 可以有多个**不可变引用**
- 只能有一个**可变引用**
- 不能同时有可变和不可变引用

```rust
let mut s = String::from("hello");

let r1 = &s;      // OK
let r2 = &s;      // OK
// let r3 = &mut s;  // 错误！已有不可变引用

println!("{} {}", r1, r2);
// r1, r2作用域结束

let r3 = &mut s;  // OK
```

### NLL（Non-Lexical Lifetimes）

引用的作用域到最后一次使用为止，而非到块结束：

```rust
let mut s = String::from("hello");

let r1 = &s;
let r2 = &s;
println!("{} {}", r1, r2);  // r1, r2最后使用

let r3 = &mut s;  // OK，r1, r2已结束
println!("{}", r3);
```

---

## 悬垂引用

Rust编译器防止悬垂引用：

```rust
fn dangle() -> &String {
    let s = String::from("hello");
    &s  // 错误！s在函数结束时被释放
}

// 正确做法：返回所有权
fn no_dangle() -> String {
    let s = String::from("hello");
    s
}
```

---

## 切片

切片是对集合部分元素的引用：

```rust
let s = String::from("hello world");

let hello = &s[0..5];   // "hello"
let world = &s[6..11];  // "world"

// 简写
let hello = &s[..5];    // 从0开始
let world = &s[6..];    // 到结尾
let whole = &s[..];     // 整个

// 字符串字面量是切片
let s: &str = "hello";

// 数组切片
let arr = [1, 2, 3, 4, 5];
let slice = &arr[1..3];  // [2, 3]
```

### 字符串切片作为参数

```rust
fn first_word(s: &str) -> &str {
    let bytes = s.as_bytes();
    for (i, &item) in bytes.iter().enumerate() {
        if item == b' ' {
            return &s[0..i];
        }
    }
    &s[..]
}

// 可以接受String和&str
first_word(&my_string);
first_word("hello world");
```

---

## 所有权与函数

### 传入函数

```rust
fn main() {
    let s = String::from("hello");
    takes_ownership(s);     // s移动
    // s不再有效
    
    let x = 5;
    makes_copy(x);          // x被复制
    // x仍然有效
}

fn takes_ownership(s: String) {
    println!("{}", s);
}  // s被释放

fn makes_copy(x: i32) {
    println!("{}", x);
}
```

### 从函数返回

```rust
fn main() {
    let s1 = gives_ownership();
    
    let s2 = String::from("hello");
    let s3 = takes_and_gives_back(s2);  // s2移动，返回到s3
}

fn gives_ownership() -> String {
    String::from("hello")
}

fn takes_and_gives_back(s: String) -> String {
    s
}
```

### 使用引用避免转移

```rust
fn main() {
    let s = String::from("hello");
    let len = calculate_length(&s);  // 借用
    println!("Length of '{}' is {}", s, len);  // s仍有效
}

fn calculate_length(s: &String) -> usize {
    s.len()
}
```

---

## 结构体中的所有权

### 拥有数据

```rust
struct User {
    username: String,  // 拥有String
    email: String,
}

let user = User {
    username: String::from("alice"),
    email: String::from("alice@example.com"),
};
```

### 引用数据（需要生命周期）

```rust
struct User<'a> {
    username: &'a str,  // 借用字符串
    email: &'a str,
}

let username = String::from("alice");
let user = User {
    username: &username,
    email: "alice@example.com",
};
```

---

## 智能指针

### Box<T>

堆分配：

```rust
let b = Box::new(5);
println!("{}", b);

// 递归类型
enum List {
    Cons(i32, Box<List>),
    Nil,
}
```

### Rc<T>

引用计数（单线程）：

```rust
use std::rc::Rc;

let a = Rc::new(5);
let b = Rc::clone(&a);  // 增加引用计数

println!("{}", Rc::strong_count(&a));  // 2
```

### RefCell<T>

内部可变性：

```rust
use std::cell::RefCell;

let data = RefCell::new(5);

*data.borrow_mut() += 1;  // 运行时借用检查
println!("{}", data.borrow());
```

---

## 常见模式

### 返回多个值

```rust
fn calculate(s: &String) -> (usize, usize) {
    (s.len(), s.capacity())
}
```

### 链式调用

```rust
let s = String::from("hello")
    .to_uppercase()
    .replace("L", "1");
```

### 条件所有权转移

```rust
fn process(s: Option<String>) -> String {
    match s {
        Some(string) => string.to_uppercase(),
        None => String::from("default"),
    }
}
```

---

## 总结

| 概念 | 说明 |
|------|------|
| 所有权 | 每个值有且仅有一个所有者 |
| 移动 | 赋值/传参转移所有权 |
| 克隆 | 深拷贝，保留原值 |
| 借用 | 不转移所有权的引用 |
| 可变引用 | 同一时间只能有一个 |
| 切片 | 对部分数据的引用 |

所有权系统是Rust的核心，理解它是掌握Rust的关键。编译器会帮助你遵守这些规则。
