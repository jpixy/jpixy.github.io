+++
title = "生命周期详解"
slug = "rust-03-生命周期详解"
date = 2026-01-19
weight = 3000
description = "Rust生命周期：生命周期标注、省略规则、结构体生命周期、静态生命周期"
[taxonomies]
tags = ["Rust", "生命周期", "借用"]
+++

## 生命周期概念

### 什么是生命周期

生命周期是引用有效的作用域。编译器使用生命周期确保引用始终有效。

```rust
{
    let r;                // ------+-- 'a
    {                     //       |
        let x = 5;        // -+-- 'b
        r = &x;           //  |
    }                     // -+    x离开作用域
    // println!("{}", r); // 错误！r引用的x已无效
}                         // ------+
```

### 悬垂引用

```rust
fn main() {
    let r = dangle();
}

fn dangle() -> &String {  // 错误！
    let s = String::from("hello");
    &s  // s将被释放，返回悬垂引用
}
```

---

## 生命周期标注

### 为什么需要标注

当函数有多个引用参数时，编译器无法推断返回引用的生命周期：

```rust
// 编译器不知道返回值的生命周期
fn longest(x: &str, y: &str) -> &str {  // 错误！
    if x.len() > y.len() { x } else { y }
}
```

### 标注语法

```rust
&i32        // 引用
&'a i32     // 带生命周期的引用
&'a mut i32 // 带生命周期的可变引用
```

### 函数中的生命周期

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

fn main() {
    let s1 = String::from("long string");
    let s2 = String::from("short");
    
    let result = longest(&s1, &s2);
    println!("{}", result);
}
```

**含义**：返回值的生命周期等于x和y中较短的那个。

### 生命周期约束

```rust
fn main() {
    let s1 = String::from("long string");
    let result;
    {
        let s2 = String::from("short");
        result = longest(&s1, &s2);  // result的生命周期被s2限制
    }
    // println!("{}", result);  // 错误！s2已离开作用域
}
```

---

## 结构体中的生命周期

### 结构体持有引用

```rust
struct ImportantExcerpt<'a> {
    part: &'a str,
}

fn main() {
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first_sentence = novel.split('.').next().unwrap();
    
    let excerpt = ImportantExcerpt {
        part: first_sentence,
    };
    
    println!("{}", excerpt.part);
}
```

### 含义

结构体实例的生命周期不能超过其引用字段所引用数据的生命周期。

### 方法中的生命周期

```rust
impl<'a> ImportantExcerpt<'a> {
    fn level(&self) -> i32 {
        3
    }
    
    fn announce_and_return_part(&self, announcement: &str) -> &str {
        println!("Attention: {}", announcement);
        self.part
    }
}
```

---

## 生命周期省略规则

编译器使用三条规则自动推断生命周期：

### 规则1：输入生命周期

每个引用参数获得独立的生命周期：

```rust
fn foo(x: &i32)                // fn foo<'a>(x: &'a i32)
fn foo(x: &i32, y: &i32)       // fn foo<'a, 'b>(x: &'a i32, y: &'b i32)
```

### 规则2：单输入生命周期

如果只有一个输入生命周期，它被赋给所有输出生命周期：

```rust
fn foo(x: &i32) -> &i32        // fn foo<'a>(x: &'a i32) -> &'a i32
```

### 规则3：方法的&self

如果有&self或&mut self，self的生命周期赋给所有输出：

```rust
impl Foo {
    fn method(&self, x: &str) -> &str  // 返回值生命周期 = &self
}
```

### 何时需要显式标注

当省略规则无法推断时：

```rust
// 无法推断：两个输入，不知道返回哪个的生命周期
fn longest(x: &str, y: &str) -> &str

// 必须显式标注
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str
```

---

## 静态生命周期

### 'static

'static生命周期表示整个程序运行期间有效：

```rust
// 字符串字面量是'static
let s: &'static str = "I have a static lifetime.";

// 全局常量
static GREETING: &str = "Hello";
```

### 谨慎使用

'static通常不是正确的解决方案：

```rust
// 不要这样做
fn longest<'a>(x: &'a str, y: &'a str) -> &'static str {
    // 错误地尝试用'static解决生命周期问题
}

// 正确做法
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

### 泄漏内存获得'static

```rust
fn leak_string() -> &'static str {
    let s = String::from("hello");
    Box::leak(s.into_boxed_str())  // 故意泄漏，获得'static
}
```

---

## 高级生命周期

### 多个生命周期

```rust
fn longest_with_announcement<'a, 'b>(
    x: &'a str,
    y: &'a str,
    ann: &'b str,
) -> &'a str {
    println!("Announcement: {}", ann);
    if x.len() > y.len() { x } else { y }
}
```

### 生命周期子类型

```rust
fn longest<'a, 'b: 'a>(x: &'a str, y: &'b str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
// 'b: 'a 表示 'b 至少和 'a 一样长
```

### 泛型类型中的生命周期

```rust
use std::fmt::Display;

fn longest_with_announcement<'a, T>(
    x: &'a str,
    y: &'a str,
    ann: T,
) -> &'a str
where
    T: Display,
{
    println!("Announcement: {}", ann);
    if x.len() > y.len() { x } else { y }
}
```

---

## 常见模式

### 返回输入引用

```rust
fn first_word(s: &str) -> &str {
    &s[..s.find(' ').unwrap_or(s.len())]
}
```

### 返回新创建的String

当无法返回输入引用时，返回拥有的数据：

```rust
fn make_greeting(name: &str) -> String {
    format!("Hello, {}!", name)
}
```

### 结构体持有引用或拥有数据

```rust
// 持有引用，需要生命周期
struct RefHolder<'a> {
    data: &'a str,
}

// 拥有数据，无需生命周期
struct Owner {
    data: String,
}
```

### 使用Cow避免选择

```rust
use std::borrow::Cow;

fn maybe_modify(s: &str, should_modify: bool) -> Cow<str> {
    if should_modify {
        Cow::Owned(s.to_uppercase())
    } else {
        Cow::Borrowed(s)
    }
}
```

---

## 常见错误

### 返回局部变量引用

```rust
fn create_string() -> &String {  // 错误！
    let s = String::from("hello");
    &s
}

// 正确：返回拥有的值
fn create_string() -> String {
    String::from("hello")
}
```

### 生命周期不匹配

```rust
fn main() {
    let r;
    {
        let x = 5;
        r = &x;
    }  // x离开作用域
    println!("{}", r);  // 错误！
}
```

### 结构体字段生命周期

```rust
struct Holder<'a> {
    value: &'a i32,
}

fn main() {
    let h;
    {
        let x = 5;
        h = Holder { value: &x };
    }  // x离开作用域
    println!("{}", h.value);  // 错误！
}
```

---

## 总结

| 概念 | 说明 |
|------|------|
| 生命周期 | 引用有效的作用域 |
| 标注语法 | 'a, 'b等 |
| 省略规则 | 编译器自动推断 |
| 'static | 整个程序期间有效 |
| 子类型 | 'b: 'a表示'b >= 'a |

生命周期是Rust保证内存安全的关键机制。大多数情况下省略规则可以推断，复杂场景需要显式标注。

---

## 相关文章

- [上一篇：所有权与借用](@/articles/rust/rust-02-所有权与借用.md)
- [下一篇：错误处理](@/articles/rust/rust-04-错误处理.md)
