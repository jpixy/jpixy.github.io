+++
title = "04. 错误处理"
date = 2026-01-19
weight = 4000
description = "Rust错误处理：Result、Option、?操作符、自定义错误、错误传播"
[taxonomies]
tags = ["Rust", "错误处理", "Result"]
+++

## 错误分类

### 可恢复错误

使用`Result<T, E>`：

```rust
use std::fs::File;

fn main() {
    let f = File::open("hello.txt");
    
    let f = match f {
        Ok(file) => file,
        Err(error) => panic!("Problem opening file: {:?}", error),
    };
}
```

### 不可恢复错误

使用`panic!`：

```rust
fn main() {
    panic!("crash and burn");
}
```

**何时使用panic**：
- 程序处于无效状态
- 不可能恢复
- 示例、原型代码
- 测试

---

## Result枚举

### 定义

```rust
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

### 基本用法

```rust
use std::fs::File;
use std::io::ErrorKind;

fn main() {
    let f = File::open("hello.txt");
    
    let f = match f {
        Ok(file) => file,
        Err(error) => match error.kind() {
            ErrorKind::NotFound => match File::create("hello.txt") {
                Ok(fc) => fc,
                Err(e) => panic!("Problem creating file: {:?}", e),
            },
            other_error => panic!("Problem opening file: {:?}", other_error),
        },
    };
}
```

### unwrap和expect

```rust
// unwrap：Ok返回值，Err则panic
let f = File::open("hello.txt").unwrap();

// expect：同unwrap，但可自定义错误信息
let f = File::open("hello.txt")
    .expect("Failed to open hello.txt");
```

### unwrap_or系列

```rust
// unwrap_or：提供默认值
let value = result.unwrap_or(0);

// unwrap_or_else：提供默认值计算函数
let value = result.unwrap_or_else(|_| calculate_default());

// unwrap_or_default：使用Default trait
let value: String = result.unwrap_or_default();
```

---

## Option枚举

### 定义

```rust
enum Option<T> {
    Some(T),
    None,
}
```

### 基本用法

```rust
fn find_user(id: u32) -> Option<User> {
    if id == 1 {
        Some(User { name: "Alice".into() })
    } else {
        None
    }
}

let user = find_user(1);
match user {
    Some(u) => println!("Found: {}", u.name),
    None => println!("Not found"),
}
```

### 常用方法

```rust
let x: Option<i32> = Some(5);

// is_some / is_none
if x.is_some() { }

// map：转换Some中的值
let y = x.map(|v| v * 2);  // Some(10)

// and_then：链式调用返回Option的函数
let z = x.and_then(|v| if v > 0 { Some(v) } else { None });

// or：如果None，使用备选
let a = x.or(Some(0));

// filter：满足条件保留Some
let b = x.filter(|v| *v > 10);  // None

// take：取出值，原变量变None
let mut x = Some(5);
let y = x.take();  // x = None, y = Some(5)
```

### Option转Result

```rust
let x: Option<i32> = Some(5);

// ok_or：None转为指定Err
let result: Result<i32, &str> = x.ok_or("not found");

// ok_or_else：None转为计算的Err
let result = x.ok_or_else(|| "not found".to_string());
```

---

## ?操作符

### 错误传播

```rust
use std::fs::File;
use std::io::{self, Read};

fn read_username_from_file() -> Result<String, io::Error> {
    let mut f = File::open("hello.txt")?;  // 如果Err，提前返回
    let mut s = String::new();
    f.read_to_string(&mut s)?;
    Ok(s)
}
```

### ?的行为

```rust
// ? 等价于
match result {
    Ok(v) => v,
    Err(e) => return Err(e.into()),
}
```

### 链式调用

```rust
fn read_username_from_file() -> Result<String, io::Error> {
    let mut s = String::new();
    File::open("hello.txt")?.read_to_string(&mut s)?;
    Ok(s)
}
```

### Option中使用?

```rust
fn first_char(s: &str) -> Option<char> {
    s.lines().next()?.chars().next()
}
```

### main中使用?

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let f = File::open("hello.txt")?;
    Ok(())
}
```

---

## 自定义错误

### 简单错误

```rust
#[derive(Debug)]
struct MyError {
    message: String,
}

impl std::fmt::Display for MyError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl std::error::Error for MyError {}
```

### 错误枚举

```rust
#[derive(Debug)]
enum AppError {
    IoError(std::io::Error),
    ParseError(std::num::ParseIntError),
    NotFound(String),
}

impl std::fmt::Display for AppError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            AppError::IoError(e) => write!(f, "IO error: {}", e),
            AppError::ParseError(e) => write!(f, "Parse error: {}", e),
            AppError::NotFound(s) => write!(f, "Not found: {}", s),
        }
    }
}

impl std::error::Error for AppError {}

impl From<std::io::Error> for AppError {
    fn from(error: std::io::Error) -> Self {
        AppError::IoError(error)
    }
}
```

### thiserror库

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum AppError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Parse error: {0}")]
    Parse(#[from] std::num::ParseIntError),
    
    #[error("Not found: {0}")]
    NotFound(String),
}
```

### anyhow库

```rust
use anyhow::{Context, Result};

fn read_config() -> Result<Config> {
    let content = std::fs::read_to_string("config.toml")
        .context("Failed to read config file")?;
    
    let config: Config = toml::from_str(&content)
        .context("Failed to parse config")?;
    
    Ok(config)
}
```

---

## 错误处理模式

### 向上传播

```rust
fn process() -> Result<(), AppError> {
    let data = read_file()?;
    let parsed = parse_data(&data)?;
    save_result(&parsed)?;
    Ok(())
}
```

### 本地处理

```rust
fn process() {
    match read_file() {
        Ok(data) => {
            // 处理数据
        }
        Err(e) => {
            log::error!("Failed to read file: {}", e);
            // 使用默认值或跳过
        }
    }
}
```

### 组合处理

```rust
fn process() -> Result<(), AppError> {
    let data = read_file().unwrap_or_else(|e| {
        log::warn!("Using default: {}", e);
        default_data()
    });
    
    process_data(&data)?;
    Ok(())
}
```

### 收集结果

```rust
let results: Vec<Result<i32, Error>> = items.iter()
    .map(|item| process(item))
    .collect();

// 收集所有Ok或第一个Err
let collected: Result<Vec<i32>, Error> = results.into_iter().collect();

// 只收集Ok，忽略Err
let successes: Vec<i32> = items.iter()
    .filter_map(|item| process(item).ok())
    .collect();
```

---

## 最佳实践

### 库vs应用

**库**：
- 定义具体错误类型
- 使用thiserror
- 不要panic（除非不变量被破坏）

**应用**：
- 使用anyhow简化
- 在边界处理错误
- 可以在main中panic

### 错误上下文

```rust
use anyhow::{Context, Result};

fn read_user(id: u32) -> Result<User> {
    let path = format!("users/{}.json", id);
    let content = std::fs::read_to_string(&path)
        .with_context(|| format!("Failed to read user file: {}", path))?;
    
    let user: User = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse user {}", id))?;
    
    Ok(user)
}
```

### 不要过度使用unwrap

```rust
// 不好
let value = some_option.unwrap();

// 好
let value = some_option.expect("should have a value because...");

// 更好
let value = match some_option {
    Some(v) => v,
    None => return Err(MyError::NotFound),
};
```

---

## 总结

| 概念 | 用途 |
|------|------|
| Result | 可恢复错误 |
| Option | 可能为空的值 |
| panic! | 不可恢复错误 |
| ? | 错误传播 |
| thiserror | 定义错误类型 |
| anyhow | 应用级错误处理 |

Rust的错误处理强调显式和类型安全，强制你思考和处理可能的错误情况。

---

## 相关文章

- [上一篇：生命周期详解](@/articles/rust/rust-03-生命周期详解.md)
- [下一篇：并发编程](@/articles/rust/rust-05-并发编程.md)
