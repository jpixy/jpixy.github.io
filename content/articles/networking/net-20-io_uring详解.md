+++
title = "20.io_uring详解(HFT)"
slug = "net-20-io_uring详解"
description = "深入讲解Linux io_uring：原理架构、liburing使用、SQE/CQE详解、性能对比、与epoll对比及HFT应用场景"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["io_uring", "异步IO", "Linux", "高性能", "HFT"]
+++

# io_uring详解(HFT)

## 概述

io_uring是Linux 5.1引入的革命性异步IO接口，通过共享内存的环形缓冲区实现高效的用户态与内核态通信，显著降低系统调用开销。

## 一、io_uring架构

### 1.1 核心概念

```
用户空间                              内核空间
┌──────────────────┐            ┌──────────────────┐
│   应用程序       │            │    io_uring      │
│                  │            │    内核处理       │
└────────┬─────────┘            └────────▲─────────┘
         │                               │
         ▼                               │
┌──────────────────────────────────────────────────┐
│           共享内存 (mmap)                         │
│  ┌─────────────────┐    ┌─────────────────┐     │
│  │ Submission Queue │    │ Completion Queue│     │
│  │      (SQ)        │    │      (CQ)       │     │
│  │ [SQE][SQE][SQE] │    │ [CQE][CQE][CQE]│     │
│  └─────────────────┘    └─────────────────┘     │
└──────────────────────────────────────────────────┘

SQE: Submission Queue Entry (提交条目)
CQE: Completion Queue Entry (完成条目)
```

### 1.2 优势

| 特性 | 传统IO | io_uring |
|------|--------|----------|
| 系统调用 | 每次IO一次 | 批量提交 |
| 数据拷贝 | 多次 | 可零拷贝 |
| 用户/内核切换 | 频繁 | 最小化 |
| 轮询模式 | 不支持 | 支持 |

## 二、liburing基础

### 2.1 初始化

```c
#include <liburing.h>

int init_io_uring(struct io_uring *ring, int queue_depth) {
    struct io_uring_params params;
    memset(&params, 0, sizeof(params));
    
    /* 可选参数 */
    // params.flags = IORING_SETUP_SQPOLL;  /* 内核轮询模式 */
    // params.sq_thread_idle = 2000;         /* 轮询空闲超时(ms) */
    
    int ret = io_uring_queue_init_params(queue_depth, ring, &params);
    if (ret < 0) {
        fprintf(stderr, "io_uring init failed: %s\n", strerror(-ret));
        return -1;
    }
    
    return 0;
}

void cleanup_io_uring(struct io_uring *ring) {
    io_uring_queue_exit(ring);
}
```

### 2.2 文件读写

```c
#include <liburing.h>
#include <fcntl.h>

/* 异步读取文件 */
int async_read(struct io_uring *ring, int fd, void *buf, 
               size_t len, off_t offset, void *user_data) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    if (!sqe) return -1;
    
    io_uring_prep_read(sqe, fd, buf, len, offset);
    io_uring_sqe_set_data(sqe, user_data);
    
    return 0;
}

/* 异步写入文件 */
int async_write(struct io_uring *ring, int fd, const void *buf,
                size_t len, off_t offset, void *user_data) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    if (!sqe) return -1;
    
    io_uring_prep_write(sqe, fd, buf, len, offset);
    io_uring_sqe_set_data(sqe, user_data);
    
    return 0;
}

/* 提交并等待完成 */
int submit_and_wait(struct io_uring *ring, int wait_nr) {
    int ret = io_uring_submit(ring);
    if (ret < 0) return ret;
    
    if (wait_nr > 0) {
        struct io_uring_cqe *cqe;
        ret = io_uring_wait_cqe(ring, &cqe);
        if (ret < 0) return ret;
        
        /* 处理完成 */
        void *user_data = io_uring_cqe_get_data(cqe);
        int result = cqe->res;
        
        io_uring_cqe_seen(ring, cqe);
        
        return result;
    }
    
    return ret;
}
```

### 2.3 批量操作

```c
/* 批量提交和处理 */
void batch_operations(struct io_uring *ring) {
    /* 准备多个操作 */
    for (int i = 0; i < 10; i++) {
        struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
        io_uring_prep_nop(sqe);
        sqe->user_data = i;
    }
    
    /* 一次提交所有操作 */
    io_uring_submit(ring);
    
    /* 批量获取完成 */
    struct io_uring_cqe *cqes[10];
    int count = io_uring_peek_batch_cqe(ring, cqes, 10);
    
    for (int i = 0; i < count; i++) {
        printf("Completed op %llu, result: %d\n", 
               cqes[i]->user_data, cqes[i]->res);
    }
    
    /* 标记已处理 */
    io_uring_cq_advance(ring, count);
}
```

## 三、网络操作

### 3.1 TCP服务器

```c
#include <liburing.h>
#include <netinet/in.h>
#include <string.h>

#define QUEUE_DEPTH 256
#define READ_SIZE 4096

typedef enum {
    EVENT_ACCEPT,
    EVENT_READ,
    EVENT_WRITE,
} EventType;

typedef struct {
    EventType type;
    int fd;
    char buffer[READ_SIZE];
} Connection;

void add_accept(struct io_uring *ring, int server_fd, 
                struct sockaddr_in *client_addr, socklen_t *addr_len) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    io_uring_prep_accept(sqe, server_fd, 
                         (struct sockaddr *)client_addr, addr_len, 0);
    
    Connection *conn = malloc(sizeof(Connection));
    conn->type = EVENT_ACCEPT;
    conn->fd = server_fd;
    io_uring_sqe_set_data(sqe, conn);
}

void add_read(struct io_uring *ring, int client_fd, Connection *conn) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    io_uring_prep_recv(sqe, client_fd, conn->buffer, READ_SIZE, 0);
    
    conn->type = EVENT_READ;
    conn->fd = client_fd;
    io_uring_sqe_set_data(sqe, conn);
}

void add_write(struct io_uring *ring, int client_fd, 
               Connection *conn, size_t len) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    io_uring_prep_send(sqe, client_fd, conn->buffer, len, 0);
    
    conn->type = EVENT_WRITE;
    io_uring_sqe_set_data(sqe, conn);
}

void run_server(int server_fd) {
    struct io_uring ring;
    io_uring_queue_init(QUEUE_DEPTH, &ring, 0);
    
    struct sockaddr_in client_addr;
    socklen_t addr_len = sizeof(client_addr);
    
    /* 初始accept */
    add_accept(&ring, server_fd, &client_addr, &addr_len);
    io_uring_submit(&ring);
    
    while (1) {
        struct io_uring_cqe *cqe;
        io_uring_wait_cqe(&ring, &cqe);
        
        Connection *conn = io_uring_cqe_get_data(cqe);
        int result = cqe->res;
        
        if (result < 0) {
            fprintf(stderr, "Error: %s\n", strerror(-result));
            if (conn->type != EVENT_ACCEPT) {
                close(conn->fd);
                free(conn);
            }
        } else {
            switch (conn->type) {
                case EVENT_ACCEPT:
                    /* 新连接 */
                    {
                        int client_fd = result;
                        Connection *new_conn = malloc(sizeof(Connection));
                        add_read(&ring, client_fd, new_conn);
                        
                        /* 继续accept */
                        add_accept(&ring, server_fd, &client_addr, &addr_len);
                    }
                    break;
                    
                case EVENT_READ:
                    if (result == 0) {
                        /* 连接关闭 */
                        close(conn->fd);
                        free(conn);
                    } else {
                        /* 回显数据 */
                        add_write(&ring, conn->fd, conn, result);
                    }
                    break;
                    
                case EVENT_WRITE:
                    /* 继续读取 */
                    add_read(&ring, conn->fd, conn);
                    break;
            }
        }
        
        io_uring_cqe_seen(&ring, cqe);
        io_uring_submit(&ring);
    }
    
    io_uring_queue_exit(&ring);
}
```

### 3.2 零拷贝发送

```c
/* 使用io_uring的零拷贝发送 */
void zero_copy_send(struct io_uring *ring, int sock_fd,
                    void *buf, size_t len) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    
    /* 使用SEND_ZC标志 */
    io_uring_prep_send_zc(sqe, sock_fd, buf, len, 0, 0);
    
    io_uring_submit(ring);
    
    /* 等待完成 */
    struct io_uring_cqe *cqe;
    io_uring_wait_cqe(ring, &cqe);
    
    /* 零拷贝发送可能有两个完成事件 */
    if (cqe->flags & IORING_CQE_F_MORE) {
        io_uring_cqe_seen(ring, cqe);
        io_uring_wait_cqe(ring, &cqe);
    }
    
    io_uring_cqe_seen(ring, cqe);
}
```

## 四、高级特性

### 4.1 固定缓冲区

```c
/* 注册固定缓冲区，避免每次IO的内存映射 */
#define BUFFER_COUNT 64
#define BUFFER_SIZE 4096

char buffers[BUFFER_COUNT][BUFFER_SIZE];
struct iovec iovecs[BUFFER_COUNT];

void register_buffers(struct io_uring *ring) {
    for (int i = 0; i < BUFFER_COUNT; i++) {
        iovecs[i].iov_base = buffers[i];
        iovecs[i].iov_len = BUFFER_SIZE;
    }
    
    io_uring_register_buffers(ring, iovecs, BUFFER_COUNT);
}

/* 使用固定缓冲区读取 */
void read_fixed(struct io_uring *ring, int fd, int buf_index, off_t offset) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    io_uring_prep_read_fixed(sqe, fd, buffers[buf_index], 
                             BUFFER_SIZE, offset, buf_index);
}

void unregister_buffers(struct io_uring *ring) {
    io_uring_unregister_buffers(ring);
}
```

### 4.2 固定文件描述符

```c
/* 注册文件描述符，减少内核查找开销 */
int fds[16];

void register_files(struct io_uring *ring) {
    /* 打开文件并注册 */
    for (int i = 0; i < 16; i++) {
        fds[i] = open("data.dat", O_RDONLY);
    }
    
    io_uring_register_files(ring, fds, 16);
}

/* 使用固定文件描述符 */
void read_with_fixed_fd(struct io_uring *ring, int fd_index) {
    struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
    io_uring_prep_read(sqe, fd_index, buffer, size, 0);
    sqe->flags |= IOSQE_FIXED_FILE;  /* 标记使用固定fd */
}
```

### 4.3 轮询模式

```c
/* 内核轮询模式 (SQPOLL) */
int init_sqpoll(struct io_uring *ring) {
    struct io_uring_params params;
    memset(&params, 0, sizeof(params));
    
    params.flags = IORING_SETUP_SQPOLL;
    params.sq_thread_idle = 2000;  /* 空闲2秒后休眠 */
    
    return io_uring_queue_init_params(256, ring, &params);
}

/* 用户轮询模式 (IOPOLL) */
int init_iopoll(struct io_uring *ring) {
    struct io_uring_params params;
    memset(&params, 0, sizeof(params));
    
    params.flags = IORING_SETUP_IOPOLL;
    
    return io_uring_queue_init_params(256, ring, &params);
}

/* 非阻塞获取完成事件 */
int poll_completions(struct io_uring *ring) {
    struct io_uring_cqe *cqe;
    int count = 0;
    
    while (io_uring_peek_cqe(ring, &cqe) == 0) {
        /* 处理完成事件 */
        process_cqe(cqe);
        io_uring_cqe_seen(ring, cqe);
        count++;
    }
    
    return count;
}
```

### 4.4 链式操作

```c
/* 链式操作：前一个完成后才执行下一个 */
void chained_operations(struct io_uring *ring, int fd) {
    struct io_uring_sqe *sqe;
    char buf[4096];
    
    /* 第一个操作：读取 */
    sqe = io_uring_get_sqe(ring);
    io_uring_prep_read(sqe, fd, buf, sizeof(buf), 0);
    sqe->flags |= IOSQE_IO_LINK;  /* 链接到下一个 */
    
    /* 第二个操作：写入（在读取完成后执行） */
    sqe = io_uring_get_sqe(ring);
    io_uring_prep_write(sqe, STDOUT_FILENO, buf, sizeof(buf), 0);
    
    io_uring_submit(ring);
}
```

## 五、性能对比

### 5.1 与epoll对比

```c
/* epoll实现 */
void epoll_echo_server(int server_fd) {
    int epfd = epoll_create1(0);
    struct epoll_event ev, events[64];
    
    ev.events = EPOLLIN;
    ev.data.fd = server_fd;
    epoll_ctl(epfd, EPOLL_CTL_ADD, server_fd, &ev);
    
    while (1) {
        int n = epoll_wait(epfd, events, 64, -1);
        for (int i = 0; i < n; i++) {
            if (events[i].data.fd == server_fd) {
                int client = accept(server_fd, NULL, NULL);
                ev.events = EPOLLIN;
                ev.data.fd = client;
                epoll_ctl(epfd, EPOLL_CTL_ADD, client, &ev);
            } else {
                char buf[4096];
                ssize_t len = read(events[i].data.fd, buf, sizeof(buf));
                if (len <= 0) {
                    close(events[i].data.fd);
                } else {
                    write(events[i].data.fd, buf, len);
                }
            }
        }
    }
}

/* 性能对比表 */
/*
| 指标          | epoll      | io_uring   |
|---------------|------------|------------|
| 系统调用/op   | 2-3        | 0-1        |
| 上下文切换    | 每次IO     | 批量       |
| 零拷贝        | 需额外配置 | 原生支持   |
| 批量处理      | 有限       | 完善       |
*/
```

### 5.2 基准测试

```c
#include <time.h>

void benchmark_io_uring(struct io_uring *ring, int fd, int ops) {
    struct timespec start, end;
    char buf[4096];
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (int i = 0; i < ops; i++) {
        struct io_uring_sqe *sqe = io_uring_get_sqe(ring);
        io_uring_prep_read(sqe, fd, buf, sizeof(buf), 0);
        sqe->user_data = i;
    }
    
    io_uring_submit(ring);
    
    int completed = 0;
    while (completed < ops) {
        struct io_uring_cqe *cqe;
        io_uring_wait_cqe(ring, &cqe);
        completed++;
        io_uring_cqe_seen(ring, cqe);
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    double elapsed = (end.tv_sec - start.tv_sec) + 
                    (end.tv_nsec - start.tv_nsec) / 1e9;
    
    printf("io_uring: %d ops in %.3f s = %.0f ops/s\n", 
           ops, elapsed, ops / elapsed);
}
```

## 六、HFT应用

### 6.1 低延迟网络接收

```c
/* 使用io_uring进行低延迟Market Data接收 */
typedef struct {
    struct io_uring ring;
    int sock;
    char *buffers;
    int buffer_count;
    int buffer_size;
} MarketDataReceiver;

int init_md_receiver(MarketDataReceiver *mdr, const char *addr, int port) {
    /* 创建UDP socket */
    mdr->sock = socket(AF_INET, SOCK_DGRAM, 0);
    
    /* 绑定地址 */
    struct sockaddr_in sa;
    sa.sin_family = AF_INET;
    sa.sin_addr.s_addr = inet_addr(addr);
    sa.sin_port = htons(port);
    bind(mdr->sock, (struct sockaddr *)&sa, sizeof(sa));
    
    /* 初始化io_uring */
    struct io_uring_params params = {0};
    params.flags = IORING_SETUP_SQPOLL;  /* 内核轮询 */
    io_uring_queue_init_params(256, &mdr->ring, &params);
    
    /* 分配并注册缓冲区 */
    mdr->buffer_count = 256;
    mdr->buffer_size = 2048;
    mdr->buffers = aligned_alloc(4096, mdr->buffer_count * mdr->buffer_size);
    
    struct iovec *iovs = malloc(mdr->buffer_count * sizeof(struct iovec));
    for (int i = 0; i < mdr->buffer_count; i++) {
        iovs[i].iov_base = mdr->buffers + i * mdr->buffer_size;
        iovs[i].iov_len = mdr->buffer_size;
    }
    io_uring_register_buffers(&mdr->ring, iovs, mdr->buffer_count);
    free(iovs);
    
    /* 预提交接收请求 */
    for (int i = 0; i < 64; i++) {
        struct io_uring_sqe *sqe = io_uring_get_sqe(&mdr->ring);
        io_uring_prep_recv(sqe, mdr->sock, 
                           mdr->buffers + i * mdr->buffer_size,
                           mdr->buffer_size, 0);
        sqe->user_data = i;
    }
    io_uring_submit(&mdr->ring);
    
    return 0;
}

void receive_market_data(MarketDataReceiver *mdr,
                         void (*handler)(const char*, size_t)) {
    while (1) {
        struct io_uring_cqe *cqe;
        
        /* 非阻塞获取完成 */
        if (io_uring_peek_cqe(&mdr->ring, &cqe) == 0) {
            int buf_idx = cqe->user_data;
            int len = cqe->res;
            
            if (len > 0) {
                handler(mdr->buffers + buf_idx * mdr->buffer_size, len);
            }
            
            /* 重新提交接收请求 */
            struct io_uring_sqe *sqe = io_uring_get_sqe(&mdr->ring);
            io_uring_prep_recv(sqe, mdr->sock,
                               mdr->buffers + buf_idx * mdr->buffer_size,
                               mdr->buffer_size, 0);
            sqe->user_data = buf_idx;
            io_uring_submit(&mdr->ring);
            
            io_uring_cqe_seen(&mdr->ring, cqe);
        }
    }
}
```

## 总结

io_uring的核心优势：

1. **减少系统调用**：批量提交和获取结果
2. **零拷贝**：减少数据复制开销
3. **轮询模式**：消除中断延迟
4. **固定资源**：注册缓冲区和文件描述符
5. **链式操作**：依赖操作的原子执行

io_uring是现代Linux高性能IO的首选方案，特别适合HFT等低延迟场景。
