+++
title = "异步编程"
slug = "rust-06-异步编程"
date = 2026-01-19
weight = 6000
description = "Rust异步：async/await、Future、tokio运行时、异步模式"
[taxonomies]
tags = ["Rust", "异步", "tokio"]
+++

## 异步基础

### 同步vs异步

```rust
// 同步：阻塞等待
let data = std::fs::read_to_string("file.txt")?;

// 异步：不阻塞，可以做其他事
let data = tokio::fs::read_to_string("file.txt").await?;
```

### async/await

```rust
async fn hello() -> String {
    "Hello".to_string()
}

async fn greet() {
    let greeting = hello().await;  // 等待异步函数完成
    println!("{}", greeting);
}
```

### Future trait

```rust
trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}

enum Poll<T> {
    Ready(T),
    Pending,
}
```

async函数返回实现Future的类型。

---

## Tokio运行时

### 添加依赖

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
```

### 基本使用

```rust
#[tokio::main]
async fn main() {
    println!("Hello from async!");
    
    let result = some_async_function().await;
    println!("{}", result);
}

async fn some_async_function() -> i32 {
    42
}
```

### 手动创建运行时

```rust
fn main() {
    let rt = tokio::runtime::Runtime::new().unwrap();
    
    rt.block_on(async {
        println!("Hello from runtime!");
    });
}
```

### 多线程运行时

```rust
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() {
    // 使用4个工作线程
}

// 单线程
#[tokio::main(flavor = "current_thread")]
async fn main() {
    // 单线程运行
}
```

---

## 异步任务

### spawn

```rust
#[tokio::main]
async fn main() {
    let handle = tokio::spawn(async {
        // 在新任务中执行
        42
    });
    
    let result = handle.await.unwrap();
    println!("{}", result);
}
```

### 并发执行

```rust
use tokio::join;

async fn fetch_data() -> String {
    "data".to_string()
}

async fn process() -> i32 {
    42
}

#[tokio::main]
async fn main() {
    // 并发执行，等待两者完成
    let (data, result) = join!(fetch_data(), process());
    println!("{} {}", data, result);
}
```

### select

```rust
use tokio::select;
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    select! {
        _ = sleep(Duration::from_secs(1)) => {
            println!("1 second passed");
        }
        _ = sleep(Duration::from_secs(2)) => {
            println!("2 seconds passed");
        }
    }
    // 只执行先完成的分支
}
```

---

## 异步IO

### 读写文件

```rust
use tokio::fs::File;
use tokio::io::{self, AsyncReadExt, AsyncWriteExt};

async fn read_file() -> io::Result<String> {
    let mut file = File::open("hello.txt").await?;
    let mut contents = String::new();
    file.read_to_string(&mut contents).await?;
    Ok(contents)
}

async fn write_file(data: &[u8]) -> io::Result<()> {
    let mut file = File::create("output.txt").await?;
    file.write_all(data).await?;
    Ok(())
}
```

### TCP

```rust
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

async fn server() -> io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:8080").await?;
    
    loop {
        let (mut socket, _) = listener.accept().await?;
        
        tokio::spawn(async move {
            let mut buf = [0; 1024];
            loop {
                let n = socket.read(&mut buf).await.unwrap();
                if n == 0 { return; }
                socket.write_all(&buf[0..n]).await.unwrap();
            }
        });
    }
}

async fn client() -> io::Result<()> {
    let mut stream = TcpStream::connect("127.0.0.1:8080").await?;
    stream.write_all(b"hello").await?;
    
    let mut buf = [0; 1024];
    let n = stream.read(&mut buf).await?;
    println!("Received: {}", String::from_utf8_lossy(&buf[..n]));
    
    Ok(())
}
```

---

## 异步同步原语

### Mutex

```rust
use tokio::sync::Mutex;
use std::sync::Arc;

#[tokio::main]
async fn main() {
    let data = Arc::new(Mutex::new(0));
    
    let data_clone = data.clone();
    let handle = tokio::spawn(async move {
        let mut lock = data_clone.lock().await;
        *lock += 1;
    });
    
    handle.await.unwrap();
    println!("{}", *data.lock().await);
}
```

### RwLock

```rust
use tokio::sync::RwLock;

let lock = RwLock::new(5);

// 读锁
{
    let r = lock.read().await;
    println!("{}", *r);
}

// 写锁
{
    let mut w = lock.write().await;
    *w += 1;
}
```

### Channel

```rust
use tokio::sync::mpsc;

#[tokio::main]
async fn main() {
    let (tx, mut rx) = mpsc::channel(32);
    
    tokio::spawn(async move {
        tx.send("hello").await.unwrap();
    });
    
    while let Some(message) = rx.recv().await {
        println!("Received: {}", message);
    }
}
```

### oneshot

```rust
use tokio::sync::oneshot;

#[tokio::main]
async fn main() {
    let (tx, rx) = oneshot::channel();
    
    tokio::spawn(async move {
        tx.send("result").unwrap();
    });
    
    let result = rx.await.unwrap();
    println!("{}", result);
}
```

### broadcast

```rust
use tokio::sync::broadcast;

#[tokio::main]
async fn main() {
    let (tx, mut rx1) = broadcast::channel(16);
    let mut rx2 = tx.subscribe();
    
    tokio::spawn(async move {
        println!("rx1: {}", rx1.recv().await.unwrap());
    });
    
    tokio::spawn(async move {
        println!("rx2: {}", rx2.recv().await.unwrap());
    });
    
    tx.send("hello").unwrap();
}
```

---

## 超时与取消

### 超时

```rust
use tokio::time::{timeout, Duration};

async fn slow_operation() -> i32 {
    tokio::time::sleep(Duration::from_secs(10)).await;
    42
}

#[tokio::main]
async fn main() {
    match timeout(Duration::from_secs(1), slow_operation()).await {
        Ok(result) => println!("Result: {}", result),
        Err(_) => println!("Timeout!"),
    }
}
```

### 取消

```rust
use tokio::select;
use tokio_util::sync::CancellationToken;

#[tokio::main]
async fn main() {
    let token = CancellationToken::new();
    let token_clone = token.clone();
    
    let handle = tokio::spawn(async move {
        select! {
            _ = token_clone.cancelled() => {
                println!("Cancelled!");
            }
            _ = async {
                // 长时间运行的任务
                loop {
                    tokio::time::sleep(Duration::from_secs(1)).await;
                }
            } => {}
        }
    });
    
    tokio::time::sleep(Duration::from_secs(2)).await;
    token.cancel();
    handle.await.unwrap();
}
```

---

## 流（Stream）

### 基本使用

```rust
use tokio_stream::{self as stream, StreamExt};

#[tokio::main]
async fn main() {
    let mut stream = stream::iter(vec![1, 2, 3]);
    
    while let Some(value) = stream.next().await {
        println!("{}", value);
    }
}
```

### 异步迭代

```rust
use async_stream::stream;

fn numbers() -> impl Stream<Item = i32> {
    stream! {
        for i in 0..10 {
            tokio::time::sleep(Duration::from_millis(100)).await;
            yield i;
        }
    }
}
```

---

## 常见模式

### 并发限制

```rust
use tokio::sync::Semaphore;

let semaphore = Arc::new(Semaphore::new(3));  // 最多3个并发

for i in 0..10 {
    let permit = semaphore.clone().acquire_owned().await.unwrap();
    tokio::spawn(async move {
        // 工作
        drop(permit);  // 释放许可
    });
}
```

### 优雅关闭

```rust
use tokio::signal;

#[tokio::main]
async fn main() {
    let (shutdown_tx, mut shutdown_rx) = tokio::sync::broadcast::channel(1);
    
    tokio::spawn(async move {
        loop {
            select! {
                _ = shutdown_rx.recv() => {
                    println!("Shutting down...");
                    break;
                }
                _ = do_work() => {}
            }
        }
    });
    
    signal::ctrl_c().await.unwrap();
    shutdown_tx.send(()).unwrap();
}
```

---

## 总结

| 概念 | 说明 |
|------|------|
| async/await | 异步语法 |
| Future | 异步计算 |
| tokio | 异步运行时 |
| spawn | 创建任务 |
| join!/select! | 并发/竞争 |
| Channel | 异步通信 |
| Stream | 异步迭代 |

Rust的异步编程需要理解Future和运行时的概念，tokio是最常用的异步运行时。

---

## 相关文章

- [上一篇：并发编程](@/articles/rust/rust-05-并发编程.md)
- [下一篇：嵌入式Rust](@/articles/rust/rust-07-嵌入式Rust.md)
