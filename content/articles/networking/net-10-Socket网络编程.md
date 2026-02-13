+++
title = "10. Socket网络编程"
date = 2026-01-19
weight = 10000
description = "Socket编程详解：TCP/UDP编程模型、IO模型对比、高性能服务器设计、常见问题"
[taxonomies]
tags = ["网络", "Socket", "编程"]
+++

## Socket基础

### 什么是Socket

Socket是**操作系统提供的网络通信抽象接口**，屏蔽了底层协议的复杂性。

**Socket五元组**：
```
(源IP, 源端口, 目的IP, 目的端口, 协议)
```
唯一标识一个网络连接。

### Socket类型

| 类型 | 协议 | 特点 |
|------|------|------|
| SOCK_STREAM | TCP | 可靠、面向连接、字节流 |
| SOCK_DGRAM | UDP | 不可靠、无连接、数据报 |
| SOCK_RAW | 原始IP | 直接访问IP层 |

---

## TCP编程模型

### 服务端流程

```
socket()    创建Socket
    ↓
bind()      绑定地址和端口
    ↓
listen()    开始监听
    ↓
accept()    接受连接（阻塞）
    ↓
recv/send() 收发数据
    ↓
close()     关闭连接
```

### 客户端流程

```
socket()    创建Socket
    ↓
connect()   连接服务端（阻塞）
    ↓
recv/send() 收发数据
    ↓
close()     关闭连接
```

### 关键API

**socket()**：
```c
int socket(int domain, int type, int protocol);
// domain: AF_INET(IPv4), AF_INET6(IPv6)
// type: SOCK_STREAM, SOCK_DGRAM
// protocol: 通常为0
```

**bind()**：
```c
int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
// 绑定本地地址和端口
// 服务端必须调用，客户端可选
```

**listen()**：
```c
int listen(int sockfd, int backlog);
// backlog: 未完成连接队列大小
// 全连接队列大小 = min(backlog, somaxconn)
```

**accept()**：
```c
int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen);
// 从全连接队列取出连接
// 返回新的Socket用于通信
```

**connect()**：
```c
int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
// 发起TCP三次握手
// 阻塞直到连接建立或失败
```

---

## UDP编程模型

### 服务端

```
socket()    创建Socket
    ↓
bind()      绑定地址和端口
    ↓
recvfrom()  接收数据（含发送方地址）
    ↓
sendto()    发送数据（指定目标地址）
```

### 客户端

```
socket()    创建Socket
    ↓
sendto()    发送数据
    ↓
recvfrom()  接收响应
```

### UDP vs TCP编程差异

| 方面 | TCP | UDP |
|------|-----|-----|
| 连接 | 需要connect/accept | 无需连接 |
| 发送 | send() | sendto() |
| 接收 | recv() | recvfrom() |
| 边界 | 无，字节流 | 有，数据报 |
| 多客户端 | 每客户端一个socket | 一个socket处理所有 |

---

## IO模型

### 阻塞IO

```
应用程序          内核
    |               |
    |-- recvfrom -->|
    |               | 等待数据
    |   (阻塞等待)  | 数据准备好
    |               | 复制数据
    |<-- 返回数据 --|
```

**特点**：简单，但无法同时处理多个连接。

### 非阻塞IO

```
应用程序          内核
    |               |
    |-- recvfrom -->|
    |<-- EAGAIN ----|  数据未就绪
    |-- recvfrom -->|
    |<-- EAGAIN ----|  继续轮询
    |-- recvfrom -->|
    |<-- 返回数据 --|  数据就绪
```

**特点**：需要不断轮询，CPU消耗大。

### IO多路复用

```
应用程序          内核
    |               |
    |-- select ---->|  监控多个fd
    |   (阻塞)      |
    |<-- 就绪通知 --|  有fd就绪
    |-- recvfrom -->|
    |<-- 返回数据 --|
```

**特点**：单线程处理多连接，高效。

### 异步IO

```
应用程序          内核
    |               |
    |-- aio_read -->|  发起异步读
    |<-- 返回 ------|  立即返回
    |               |  内核处理
    |  (做其他事)   |
    |<-- 信号/回调 -|  数据复制完成
```

**特点**：完全异步，Linux支持有限（io_uring改进）。

---

## IO多路复用详解

### select

```c
int select(int nfds, fd_set *readfds, fd_set *writefds,
           fd_set *exceptfds, struct timeval *timeout);
```

**限制**：
- fd数量限制（通常1024）
- 每次调用需要传递全部fd
- 返回后需要遍历找就绪fd
- O(n)复杂度

### poll

```c
int poll(struct pollfd *fds, nfds_t nfds, int timeout);

struct pollfd {
    int fd;
    short events;   // 关注的事件
    short revents;  // 发生的事件
};
```

**改进**：
- 无fd数量限制
- 使用数组而非位图

**仍存在问题**：
- 每次传递全部fd
- O(n)遍历

### epoll

```c
// 创建epoll实例
int epoll_create(int size);

// 添加/修改/删除监控
int epoll_ctl(int epfd, int op, int fd, struct epoll_event *event);

// 等待事件
int epoll_wait(int epfd, struct epoll_event *events,
               int maxevents, int timeout);
```

**优势**：
- 无fd数量限制
- 内核维护fd集合，无需每次传递
- 只返回就绪的fd
- O(1)复杂度（对于就绪fd）

### epoll触发模式

**水平触发（LT）**：
- 默认模式
- 只要缓冲区有数据就通知
- 不读完会持续通知

**边缘触发（ET）**：
- 状态变化时通知一次
- 必须一次读完所有数据
- 效率更高，但编程复杂

### IO多路复用对比

| 特性 | select | poll | epoll |
|------|--------|------|-------|
| fd数量 | 1024 | 无限制 | 无限制 |
| 数据结构 | 位图 | 数组 | 红黑树+链表 |
| 内核复制 | 每次全量 | 每次全量 | 只复制就绪 |
| 复杂度 | O(n) | O(n) | O(1) |
| 跨平台 | 是 | 是 | Linux only |

---

## 高性能服务器模型

### 多进程模型

```
主进程: accept()
    ↓
fork() → 子进程处理连接
fork() → 子进程处理连接
```

**优点**：简单，进程隔离
**缺点**：开销大，进程间通信复杂

### 多线程模型

```
主线程: accept()
    ↓
创建线程 → 工作线程处理连接
创建线程 → 工作线程处理连接
```

**优点**：开销比进程小
**缺点**：线程安全问题，线程数受限

### 线程池模型

```
主线程: accept()
    ↓
任务队列 ← 新连接
    ↓
线程池 → 工作线程1处理
       → 工作线程2处理
```

**优点**：线程复用，资源可控
**缺点**：仍受线程数限制

### Reactor模型

**单Reactor单线程**：
```
Reactor: epoll_wait()
    ↓ 就绪
Handler处理事件
```
适用：Redis

**单Reactor多线程**：
```
Reactor: epoll_wait()
    ↓ 就绪
线程池处理事件
```

**主从Reactor**：
```
主Reactor: accept()
    ↓ 新连接
分配给从Reactor
    ↓
从Reactor: epoll_wait() + 处理
```
适用：Netty

### Proactor模型

```
应用发起异步操作
    ↓
内核完成IO
    ↓
通知完成处理器
    ↓
处理器处理完成事件
```

适用：Windows IOCP，Linux io_uring

---

## 常见问题

### 粘包与拆包

**TCP字节流问题**：
```
发送：包1(100字节) + 包2(100字节)
可能收到：
- 一次收到200字节（粘包）
- 第一次50字节，第二次150字节（拆包）
```

**解决方案**：
1. 固定长度消息
2. 分隔符（如换行）
3. 长度前缀（推荐）

```
[4字节长度][消息内容]
```

### 心跳机制

**问题**：TCP连接可能"假死"

**解决**：定期发送心跳包

```python
# 应用层心跳
while True:
    send(heartbeat_packet)
    sleep(30)
    if no_response:
        reconnect()
```

### 优雅关闭

```c
// 不推荐：直接close
close(sockfd);

// 推荐：优雅关闭
shutdown(sockfd, SHUT_WR);  // 关闭写，发送FIN
// 继续读取对方数据
while(recv(...) > 0);
close(sockfd);
```

### 端口复用

```c
int opt = 1;
setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
```

**SO_REUSEADDR**：
- 允许重用TIME_WAIT状态的端口
- 服务重启时不用等待

**SO_REUSEPORT**：
- 多个进程绑定同一端口
- 内核负载均衡

---

## 性能调优

### 缓冲区大小

```c
// 接收缓冲区
setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size));

// 发送缓冲区
setsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &size, sizeof(size));
```

### TCP选项

```c
// 禁用Nagle（低延迟）
int flag = 1;
setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));

// 启用TCP_CORK（批量发送）
setsockopt(sockfd, IPPROTO_TCP, TCP_CORK, &flag, sizeof(flag));
```

### 系统参数

```bash
# 增大文件描述符限制
ulimit -n 1000000

# 增大端口范围
sysctl -w net.ipv4.ip_local_port_range="1024 65535"

# 增大连接队列
sysctl -w net.core.somaxconn=65535
```

---

## 总结

| 模型 | 特点 | 适用场景 |
|------|------|----------|
| 阻塞IO | 简单 | 学习、简单应用 |
| 非阻塞IO | CPU占用高 | 很少单独使用 |
| select/poll | 跨平台 | 连接数较少 |
| epoll | 高性能 | Linux高并发 |
| Reactor | 事件驱动 | 大部分服务端 |
| Proactor | 完全异步 | Windows、io_uring |

掌握Socket编程是理解网络应用的基础，高性能服务器开发需要深入理解IO模型和事件驱动架构。

---

## 相关文章

- [上一篇：多播与组播技术](@/articles/networking/net-09-多播与组播技术.md)
- [下一篇：网络性能分析与调优](@/articles/networking/net-11-网络性能分析与调优.md)
