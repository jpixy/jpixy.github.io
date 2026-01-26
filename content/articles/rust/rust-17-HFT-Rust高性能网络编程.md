+++
title = "17.HFT-Rust高性能网络编程"
date = 2026-01-21
description = "深入剖析Rust的高性能网络编程技术，包括io_uring、tokio、mio、零拷贝以及网络优化模式"
[taxonomies]
tags = ["Rust", "网络编程", "io_uring", "tokio", "HFT"]
+++

## 概述

网络延迟是HFT系统的关键性能指标。本文探讨Rust中实现高性能网络通信的各种技术。

---

## 一、同步vs异步

### 1.1 同步阻塞IO

```rust
use std::net::{TcpListener, TcpStream};
use std::io::{Read, Write};

fn sync_server() -> std::io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:8080")?;
    
    for stream in listener.incoming() {
        let mut stream = stream?;
        
        // 每个连接阻塞处理
        let mut buffer = [0u8; 1024];
        let n = stream.read(&mut buffer)?;  // 阻塞
        stream.write_all(&buffer[..n])?;    // 阻塞
    }
    
    Ok(())
}

// 适用场景：
// - 连接数少
// - 延迟要求极高
// - 每个连接独占线程
```

### 1.2 异步IO

```rust
use tokio::net::TcpListener;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[tokio::main]
async fn async_server() -> std::io::Result<()> {
    let listener = TcpListener::bind("127.0.0.1:8080").await?;
    
    loop {
        let (mut socket, _) = listener.accept().await?;
        
        tokio::spawn(async move {
            let mut buffer = [0u8; 1024];
            
            loop {
                let n = socket.read(&mut buffer).await.unwrap();
                if n == 0 { break; }
                socket.write_all(&buffer[..n]).await.unwrap();
            }
        });
    }
}

// 适用场景：
// - 大量并发连接
// - IO密集型
// - 吞吐量优先
```

---

## 二、mio - 底层事件库

### 2.1 基本使用

```rust
use mio::{Events, Interest, Poll, Token};
use mio::net::TcpListener;
use std::collections::HashMap;
use std::io::{Read, Write};

const SERVER: Token = Token(0);

fn mio_server() -> std::io::Result<()> {
    let mut poll = Poll::new()?;
    let mut events = Events::with_capacity(1024);
    
    let addr = "127.0.0.1:8080".parse().unwrap();
    let mut listener = TcpListener::bind(addr)?;
    
    poll.registry().register(&mut listener, SERVER, Interest::READABLE)?;
    
    let mut connections: HashMap<Token, mio::net::TcpStream> = HashMap::new();
    let mut next_token = 1;
    
    loop {
        poll.poll(&mut events, None)?;
        
        for event in events.iter() {
            match event.token() {
                SERVER => {
                    // 新连接
                    let (mut stream, _) = listener.accept()?;
                    let token = Token(next_token);
                    next_token += 1;
                    
                    poll.registry().register(
                        &mut stream,
                        token,
                        Interest::READABLE | Interest::WRITABLE,
                    )?;
                    
                    connections.insert(token, stream);
                }
                token => {
                    // 已有连接的事件
                    if event.is_readable() {
                        if let Some(stream) = connections.get_mut(&token) {
                            let mut buffer = [0u8; 1024];
                            match stream.read(&mut buffer) {
                                Ok(0) => {
                                    connections.remove(&token);
                                }
                                Ok(n) => {
                                    stream.write_all(&buffer[..n])?;
                                }
                                Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {}
                                Err(e) => return Err(e),
                            }
                        }
                    }
                }
            }
        }
    }
}
```

### 2.2 mio的优势

```rust
// mio是零成本抽象的事件库
// - 直接映射到系统调用（epoll/kqueue/iocp）
// - 无运行时开销
// - tokio的底层

// 适用场景：
// - 需要完全控制事件循环
// - 极低延迟要求
// - 定制化调度
```

---

## 三、io_uring

### 3.1 io-uring crate

```rust
use io_uring::{opcode, types, IoUring};
use std::os::unix::io::AsRawFd;

fn io_uring_read(file: &std::fs::File, buffer: &mut [u8]) -> std::io::Result<usize> {
    let mut ring = IoUring::new(8)?;
    
    let fd = types::Fd(file.as_raw_fd());
    
    // 准备read操作
    let read_e = opcode::Read::new(fd, buffer.as_mut_ptr(), buffer.len() as _)
        .build()
        .user_data(0x42);
    
    // 提交
    unsafe {
        ring.submission()
            .push(&read_e)
            .expect("submission queue is full");
    }
    ring.submit_and_wait(1)?;
    
    // 获取结果
    let cqe = ring.completion().next().expect("completion queue is empty");
    
    if cqe.result() < 0 {
        return Err(std::io::Error::from_raw_os_error(-cqe.result()));
    }
    
    Ok(cqe.result() as usize)
}
```

### 3.2 批量IO

```rust
use io_uring::{opcode, types, IoUring, squeue};
use std::os::unix::io::AsRawFd;

fn batch_send(socket: &std::net::UdpSocket, messages: &[&[u8]]) -> std::io::Result<()> {
    let mut ring = IoUring::new(256)?;
    let fd = types::Fd(socket.as_raw_fd());
    
    // 批量提交所有发送操作
    for (i, msg) in messages.iter().enumerate() {
        let send_e = opcode::Send::new(fd, msg.as_ptr(), msg.len() as _)
            .build()
            .user_data(i as u64);
        
        unsafe {
            ring.submission()
                .push(&send_e)
                .expect("queue full");
        }
    }
    
    // 一次系统调用提交所有
    ring.submit_and_wait(messages.len())?;
    
    // 处理完成
    for cqe in ring.completion() {
        if cqe.result() < 0 {
            eprintln!("Send {} failed", cqe.user_data());
        }
    }
    
    Ok(())
}
```

### 3.3 io_uring优势

```rust
// io_uring相比epoll的优势：
// 1. 减少系统调用次数
// 2. 真正的异步IO（不只是通知）
// 3. 支持批量操作
// 4. 零拷贝支持

// 典型延迟对比：
// epoll + read: ~1-2µs
// io_uring: ~0.3-0.5µs

// 适用场景：
// - Linux 5.1+
// - 高吞吐低延迟
// - 大量小消息
```

---

## 四、tokio运行时

### 4.1 运行时配置

```rust
use tokio::runtime::Builder;

fn custom_runtime() {
    // 多线程运行时（默认）
    let rt = Builder::new_multi_thread()
        .worker_threads(4)
        .thread_name("hft-worker")
        .enable_all()
        .build()
        .unwrap();
    
    // 当前线程运行时（低开销）
    let rt_single = Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();
    
    rt.block_on(async {
        // 异步代码
    });
}
```

### 4.2 低延迟配置

```rust
use tokio::runtime::Builder;

fn low_latency_runtime() {
    // HFT优化配置
    let rt = Builder::new_multi_thread()
        .worker_threads(1)           // 单线程避免调度开销
        .max_blocking_threads(1)     // 最少阻塞线程
        .enable_io()
        .enable_time()
        .build()
        .unwrap();
}

// 或使用current_thread运行时
#[tokio::main(flavor = "current_thread")]
async fn main() {
    // 单线程，无调度开销
}
```

### 4.3 tokio vs async-std vs smol

```rust
// tokio: 功能最全，生态最大
// - 多线程运行时
// - 完善的工具（channels, sync primitives）
// - 最广泛使用

// async-std: 类似std的API
// - 学习曲线平缓
// - 较小的生态

// smol: 极简设计
// - 最小的运行时
// - 可组合

// HFT推荐：
// - 高吞吐：tokio多线程
// - 低延迟：tokio current_thread 或 mio
// - 极低延迟：io_uring
```

---

## 五、零拷贝技术

### 5.1 sendfile

```rust
use std::os::unix::io::{AsRawFd, RawFd};
use std::fs::File;
use std::net::TcpStream;

#[cfg(target_os = "linux")]
fn sendfile(socket: &TcpStream, file: &File, count: usize) -> std::io::Result<usize> {
    use libc::{sendfile as sys_sendfile, off_t};
    
    let out_fd = socket.as_raw_fd();
    let in_fd = file.as_raw_fd();
    let mut offset: off_t = 0;
    
    let result = unsafe {
        sys_sendfile(out_fd, in_fd, &mut offset, count)
    };
    
    if result < 0 {
        Err(std::io::Error::last_os_error())
    } else {
        Ok(result as usize)
    }
}
```

### 5.2 MSG_ZEROCOPY

```rust
use std::os::unix::io::AsRawFd;
use std::net::UdpSocket;

#[cfg(target_os = "linux")]
fn send_zerocopy(socket: &UdpSocket, data: &[u8]) -> std::io::Result<usize> {
    use libc::{sendto, MSG_ZEROCOPY, sockaddr, socklen_t};
    
    // 需要先设置socket选项
    // setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &1, sizeof(int))
    
    let result = unsafe {
        libc::send(
            socket.as_raw_fd(),
            data.as_ptr() as *const libc::c_void,
            data.len(),
            MSG_ZEROCOPY,
        )
    };
    
    if result < 0 {
        Err(std::io::Error::last_os_error())
    } else {
        Ok(result as usize)
    }
}
```

### 5.3 共享内存

```rust
use std::sync::atomic::{AtomicU64, Ordering};
use memmap2::MmapMut;

// 用于进程间通信的共享内存队列
struct SharedQueue {
    mmap: MmapMut,
}

#[repr(C)]
struct QueueHeader {
    head: AtomicU64,
    tail: AtomicU64,
    capacity: u64,
}

impl SharedQueue {
    fn new(path: &str, size: usize) -> std::io::Result<Self> {
        let file = std::fs::OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(path)?;
        
        file.set_len(size as u64)?;
        
        let mmap = unsafe { MmapMut::map_mut(&file)? };
        
        Ok(Self { mmap })
    }
    
    fn header(&self) -> &QueueHeader {
        unsafe { &*(self.mmap.as_ptr() as *const QueueHeader) }
    }
}
```

---

## 六、HFT网络优化

### 6.1 Socket调优

```rust
use std::net::TcpStream;
use std::os::unix::io::AsRawFd;

fn optimize_socket(stream: &TcpStream) -> std::io::Result<()> {
    let fd = stream.as_raw_fd();
    
    unsafe {
        // 禁用Nagle算法
        let flag: libc::c_int = 1;
        libc::setsockopt(
            fd,
            libc::IPPROTO_TCP,
            libc::TCP_NODELAY,
            &flag as *const _ as *const libc::c_void,
            std::mem::size_of_val(&flag) as libc::socklen_t,
        );
        
        // 设置接收缓冲区
        let rcvbuf: libc::c_int = 4 * 1024 * 1024;  // 4MB
        libc::setsockopt(
            fd,
            libc::SOL_SOCKET,
            libc::SO_RCVBUF,
            &rcvbuf as *const _ as *const libc::c_void,
            std::mem::size_of_val(&rcvbuf) as libc::socklen_t,
        );
        
        // 设置发送缓冲区
        let sndbuf: libc::c_int = 4 * 1024 * 1024;
        libc::setsockopt(
            fd,
            libc::SOL_SOCKET,
            libc::SO_SNDBUF,
            &sndbuf as *const _ as *const libc::c_void,
            std::mem::size_of_val(&sndbuf) as libc::socklen_t,
        );
        
        // 忙轮询
        let busy_poll: libc::c_int = 50;  // 50µs
        libc::setsockopt(
            fd,
            libc::SOL_SOCKET,
            libc::SO_BUSY_POLL,
            &busy_poll as *const _ as *const libc::c_void,
            std::mem::size_of_val(&busy_poll) as libc::socklen_t,
        );
    }
    
    Ok(())
}
```

### 6.2 CPU亲和性

```rust
use std::thread;

fn set_cpu_affinity(cpu: usize) {
    #[cfg(target_os = "linux")]
    {
        use libc::{cpu_set_t, sched_setaffinity, CPU_SET, CPU_ZERO};
        
        unsafe {
            let mut set: cpu_set_t = std::mem::zeroed();
            CPU_ZERO(&mut set);
            CPU_SET(cpu, &mut set);
            
            let result = sched_setaffinity(
                0,  // 当前线程
                std::mem::size_of::<cpu_set_t>(),
                &set,
            );
            
            if result != 0 {
                eprintln!("Failed to set CPU affinity");
            }
        }
    }
}

fn network_thread() {
    set_cpu_affinity(0);  // 绑定到CPU 0
    
    // 网络处理循环
    loop {
        // 处理网络事件
    }
}
```

---

## 总结

| 技术 | 延迟 | 吞吐量 | 复杂度 |
|------|------|--------|--------|
| 同步阻塞 | 最低 | 低 | 低 |
| mio | 低 | 高 | 中 |
| tokio | 中 | 最高 | 中 |
| io_uring | 最低 | 最高 | 高 |

**HFT网络优化原则**：
1. 禁用Nagle（TCP_NODELAY）
2. 使用忙轮询（busy polling）
3. 绑定CPU核心
4. 考虑内核旁路（DPDK）
5. 使用io_uring减少系统调用
