+++
title = "06.网络编程"
date = 2026-01-19
description = "Linux网络编程：socket接口、TCP/UDP编程、高性能I/O"
[taxonomies]
tags = ["Linux", "网络", "socket"]
+++

## Socket基础

### 什么是Socket

Socket是网络通信的端点，提供进程间跨主机通信的能力。它是应用层与传输层的接口。

Socket抽象适用于多种协议族：IPv4、IPv6、Unix域（本地通信）。

### Socket类型

**SOCK_STREAM**：流式socket，面向连接，可靠有序。对应TCP。

**SOCK_DGRAM**：数据报socket，无连接，不可靠。对应UDP。

**SOCK_RAW**：原始socket，可以访问底层协议。

### 地址结构

**sockaddr_in**（IPv4）：
- sin_family：地址族（AF_INET）
- sin_port：端口号（网络字节序）
- sin_addr：IP地址

**sockaddr_in6**（IPv6）：类似结构但地址更长。

**sockaddr_un**（Unix域）：sun_path存储socket文件路径。

### 字节序

网络字节序是大端序。主机字节序取决于平台。

转换函数：htons/htonl（主机到网络），ntohs/ntohl（网络到主机）。

---

## TCP编程

### 服务端流程

**socket**：创建socket文件描述符。

**bind**：绑定本地地址和端口。

**listen**：将socket转为被动模式，开始监听连接。参数是backlog（等待队列长度）。

**accept**：接受客户端连接，返回新的socket用于与该客户端通信。阻塞等待或配合非阻塞/多路复用。

**read/write**：收发数据。

**close**：关闭连接。

### 客户端流程

**socket**：创建socket。

**connect**：连接到服务端地址。触发TCP三次握手。

**read/write**：收发数据。

**close**：关闭连接。

### 三次握手与四次挥手

**三次握手**建立连接：
1. 客户端发送SYN
2. 服务端回复SYN+ACK
3. 客户端发送ACK

**四次挥手**关闭连接：
1. 主动方发送FIN
2. 被动方回复ACK
3. 被动方发送FIN
4. 主动方回复ACK

TIME_WAIT状态：主动关闭方等待2MSL，确保最后的ACK送达。

### 常见选项

**SO_REUSEADDR**：允许重用处于TIME_WAIT的地址。服务器重启时必备。

**SO_KEEPALIVE**：TCP保活，检测死连接。

**TCP_NODELAY**：禁用Nagle算法，减少小包延迟。

**SO_RCVBUF/SO_SNDBUF**：接收/发送缓冲区大小。

---

## UDP编程

### 流程

**服务端**：socket → bind → recvfrom/sendto

**客户端**：socket → sendto/recvfrom（可选connect）

UDP无连接，每个recvfrom都知道发送方地址，每个sendto都指定目标地址。

### connect对UDP的作用

UDP的connect不建立连接，只是设定默认对端地址。

效果：可以使用send/recv代替sendto/recvfrom。只接收来自连接对端的数据。内核可以报告ICMP错误。

### 可靠UDP

应用层实现可靠性：确认、重传、序号、流量控制。

协议如QUIC在UDP上实现可靠传输。

---

## 高性能服务器模型

### 多进程模型

每个连接fork一个子进程处理。

优点：简单，隔离性好。
缺点：进程创建开销大，资源消耗高。

### 多线程模型

每个连接一个线程处理。

优点：比进程轻量。
缺点：线程数有限，大量连接时上下文切换开销大。

### 线程池

预创建固定数量线程，复用处理多个连接。

需要配合非阻塞I/O或I/O多路复用。

### I/O多路复用

单线程监控多个socket，有事件时处理。

**select/poll**：遍历所有文件描述符检查状态，O(n)复杂度。

**epoll**：内核维护就绪列表，只返回有事件的描述符，O(1)通知。

### epoll详解

**epoll_create**：创建epoll实例。

**epoll_ctl**：添加、修改、删除监控的文件描述符。

**epoll_wait**：等待事件，返回就绪的描述符列表。

**触发模式**：
- 水平触发（LT）：只要有数据就通知，默认模式。
- 边缘触发（ET）：状态变化时通知一次，必须配合非阻塞I/O。

**EPOLLONESHOT**：事件触发一次后自动移除，避免多线程竞争。

---

## Reactor模式

### 概念

Reactor是事件驱动的设计模式。核心是事件循环，等待事件发生并分发给对应处理器。

### 组件

**事件多路分用器**：epoll等待事件。

**事件分发器**：根据事件类型调用处理器。

**事件处理器**：处理具体的读写逻辑。

### 单Reactor单线程

所有操作在一个线程完成。适合简单场景。Redis采用此模型。

### 单Reactor多线程

主线程负责事件分发，工作线程池处理业务逻辑。适合计算密集场景。

### 多Reactor多线程

主Reactor负责accept，子Reactor负责连接的读写。每个Reactor一个线程。Netty采用此模型。

---

## 高级技术

### SO_REUSEPORT

多个socket可以绑定同一端口。内核在监听socket间分发连接，实现负载均衡。避免单一accept成为瓶颈。

### TCP_CORK与TCP_NODELAY

**TCP_NODELAY**：禁用Nagle，小包立即发送。

**TCP_CORK**：完全相反，积累数据直到缓冲区满或显式flush。适合sendfile前设置头部。

两者互斥，根据场景选择。

### sendfile

零拷贝发送文件。数据直接从文件缓冲区传到socket缓冲区，不经过用户空间。

适合静态文件服务器。

### splice与tee

splice在两个文件描述符间移动数据，不经过用户空间。

tee复制数据到另一个管道。

用于高性能代理等场景。

---

## Unix域Socket

### 特点

用于同一主机进程间通信，比TCP/UDP更高效。无网络协议栈开销。

支持传递文件描述符和凭证信息。

### 地址

使用文件系统路径或抽象命名空间（Linux特有，路径以\0开头）。

### 使用场景

数据库客户端连接（MySQL、PostgreSQL本地连接）。容器运行时与守护进程通信。X Window系统。

---

## 网络调试

### 工具

**netstat/ss**：查看socket状态、连接、监听端口。

**tcpdump/Wireshark**：抓包分析。

**nc（netcat）**：简单的网络测试工具。

**lsof**：查看进程打开的文件和网络连接。

### 常见问题

**TIME_WAIT积累**：调整内核参数或使用SO_REUSEADDR。

**连接拒绝**：服务未启动或端口错误。

**连接超时**：防火墙或网络不通。

**RST**：对端异常关闭。

---

## 总结

| 概念 | 要点 |
|------|------|
| socket | 网络通信端点 |
| TCP流程 | socket→bind→listen→accept |
| UDP流程 | socket→bind→recvfrom/sendto |
| epoll | 高效I/O多路复用 |
| Reactor | 事件驱动模式 |
| 零拷贝 | sendfile、splice |

网络编程是系统编程的重要组成部分。掌握socket接口和高性能I/O模型是构建可扩展服务的基础。
