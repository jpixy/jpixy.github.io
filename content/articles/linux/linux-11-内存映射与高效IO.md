+++
title = "11.内存映射与高效IO(HFT)"
description = "深入讲解Linux高效IO：mmap原理与陷阱、Huge Pages、THP透明大页、O_DIRECT直接IO、AIO与零拷贝技术"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["Linux", "mmap", "Huge Pages", "IO", "零拷贝", "HFT"]
+++

# 内存映射与高效IO(HFT)

## 概述

高效的内存和IO管理是低延迟系统的关键。本文深入介绍mmap、Huge Pages、直接IO和零拷贝等技术，帮助优化HFT系统性能。

## 一、mmap内存映射

### 1.1 mmap原理

```c
#include <sys/mman.h>

void *mmap(void *addr, size_t length, int prot, int flags,
           int fd, off_t offset);

/* 参数说明:
 * addr   - 期望映射地址（通常为NULL让内核选择）
 * length - 映射长度
 * prot   - 保护模式（PROT_READ, PROT_WRITE, PROT_EXEC）
 * flags  - 映射类型（MAP_SHARED, MAP_PRIVATE, MAP_ANONYMOUS等）
 * fd     - 文件描述符（匿名映射为-1）
 * offset - 文件偏移
 */
```

### 1.2 mmap使用示例

```c
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

/* 文件映射 */
void *map_file(const char *path, size_t *size) {
    int fd = open(path, O_RDONLY);
    if (fd < 0) return NULL;
    
    /* 获取文件大小 */
    *size = lseek(fd, 0, SEEK_END);
    
    /* 映射文件 */
    void *addr = mmap(NULL, *size, PROT_READ, MAP_PRIVATE, fd, 0);
    
    close(fd);  /* 映射后可以关闭fd */
    
    if (addr == MAP_FAILED) return NULL;
    return addr;
}

/* 匿名映射（分配内存） */
void *alloc_anonymous(size_t size) {
    void *addr = mmap(NULL, size, 
                      PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS,
                      -1, 0);
    
    if (addr == MAP_FAILED) return NULL;
    return addr;
}

/* 共享内存 */
void *create_shared_memory(const char *name, size_t size) {
    int fd = shm_open(name, O_CREAT | O_RDWR, 0666);
    if (fd < 0) return NULL;
    
    ftruncate(fd, size);
    
    void *addr = mmap(NULL, size,
                      PROT_READ | PROT_WRITE,
                      MAP_SHARED, fd, 0);
    
    close(fd);
    return addr;
}

/* 使用大页映射 */
void *alloc_huge_pages(size_t size) {
    void *addr = mmap(NULL, size,
                      PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                      -1, 0);
    
    if (addr == MAP_FAILED) {
        perror("mmap with MAP_HUGETLB");
        return NULL;
    }
    return addr;
}
```

### 1.3 mmap陷阱与最佳实践

```c
/* 陷阱1: 页面缺页故障延迟 */
void *addr = mmap(NULL, size, PROT_READ | PROT_WRITE, 
                  MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

/* 解决：使用MAP_POPULATE预填充页表 */
void *addr = mmap(NULL, size, PROT_READ | PROT_WRITE,
                  MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE,
                  -1, 0);

/* 或者手动预热 */
void prefault_memory(void *addr, size_t size) {
    volatile char *p = (volatile char *)addr;
    for (size_t i = 0; i < size; i += 4096) {
        p[i] = p[i];  /* 触发页面故障 */
    }
}

/* 陷阱2: 未对齐导致性能问题 */
/* 确保映射地址和大小对齐到页面边界 */
size_t aligned_size = (size + 4095) & ~4095;

/* 陷阱3: 映射后立即修改可能触发COW */
/* 使用madvise提示内核 */
madvise(addr, size, MADV_WILLNEED);  /* 预读 */
madvise(addr, size, MADV_SEQUENTIAL); /* 顺序访问 */
madvise(addr, size, MADV_RANDOM);     /* 随机访问 */

/* 锁定内存防止换出 */
mlock(addr, size);
```

## 二、Huge Pages

### 2.1 Huge Pages类型

| 类型 | 大小 | 配置方式 | 适用场景 |
|------|------|----------|----------|
| 标准页 | 4KB | 默认 | 通用 |
| 大页 | 2MB | 显式配置 | 数据库、JVM |
| 巨页 | 1GB | 显式配置 | HFT、大内存应用 |
| THP | 2MB | 自动 | 透明优化（有争议）|

### 2.2 配置Huge Pages

```bash
# 查看当前大页配置
cat /proc/meminfo | grep -i huge

# 配置2MB大页
echo 1024 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# 配置1GB大页（需要内核启动参数）
# GRUB: hugepagesz=1G hugepages=32

# 挂载hugetlbfs
mkdir -p /mnt/huge
mount -t hugetlbfs nodev /mnt/huge

# 持久化配置 (/etc/sysctl.conf)
vm.nr_hugepages = 1024

# 查看大页使用情况
cat /sys/kernel/mm/hugepages/hugepages-2048kB/free_hugepages
```

### 2.3 使用Huge Pages

```c
#include <sys/mman.h>
#include <fcntl.h>

/* 方法1: 通过hugetlbfs */
void *alloc_via_hugetlbfs(size_t size) {
    int fd = open("/mnt/huge/myfile", O_CREAT | O_RDWR, 0666);
    if (fd < 0) return NULL;
    
    void *addr = mmap(NULL, size,
                      PROT_READ | PROT_WRITE,
                      MAP_SHARED, fd, 0);
    close(fd);
    return addr;
}

/* 方法2: MAP_HUGETLB (推荐) */
void *alloc_huge(size_t size, int huge_size_log2) {
    int flags = MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB;
    
    /* 指定大页大小 */
    if (huge_size_log2 == 21) {
        flags |= MAP_HUGE_2MB;
    } else if (huge_size_log2 == 30) {
        flags |= MAP_HUGE_1GB;
    }
    
    void *addr = mmap(NULL, size, 
                      PROT_READ | PROT_WRITE,
                      flags, -1, 0);
    
    if (addr == MAP_FAILED) {
        perror("mmap hugepage");
        return NULL;
    }
    
    /* 锁定内存 */
    mlock(addr, size);
    
    return addr;
}

/* 使用示例 */
int main() {
    size_t size = 1UL << 30;  /* 1GB */
    
    void *huge_mem = alloc_huge(size, 30);  /* 1GB大页 */
    if (!huge_mem) {
        /* 降级到2MB大页 */
        huge_mem = alloc_huge(size, 21);
    }
    if (!huge_mem) {
        /* 再次降级到普通内存 */
        huge_mem = mmap(NULL, size, PROT_READ | PROT_WRITE,
                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    }
    
    return 0;
}
```

### 2.4 THP（透明大页）

```bash
# 查看THP状态
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never

# 禁用THP（HFT推荐）
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# 或通过GRUB
GRUB_CMDLINE_LINUX="transparent_hugepage=never"

# 为什么HFT要禁用THP？
# 1. khugepaged后台整理导致延迟抖动
# 2. 页面分裂/合并导致不可预测的延迟
# 3. 显式大页更可控
```

## 三、直接IO（O_DIRECT）

### 3.1 直接IO原理

```
普通IO:
应用 → 用户缓冲区 → 页缓存 → 磁盘

直接IO:
应用 → 用户缓冲区 → 磁盘（绕过页缓存）
```

### 3.2 直接IO使用

```c
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>

/* 直接IO的对齐要求 */
#define BLOCK_SIZE 4096

/* 分配对齐的缓冲区 */
void *aligned_alloc_buffer(size_t size) {
    void *buf;
    if (posix_memalign(&buf, BLOCK_SIZE, size) != 0) {
        return NULL;
    }
    return buf;
}

/* 直接IO读取 */
ssize_t direct_read(const char *path, void *buf, size_t count, off_t offset) {
    int fd = open(path, O_RDONLY | O_DIRECT);
    if (fd < 0) return -1;
    
    /* 确保offset和count对齐 */
    if (offset % BLOCK_SIZE != 0 || count % BLOCK_SIZE != 0) {
        close(fd);
        return -1;
    }
    
    ssize_t ret = pread(fd, buf, count, offset);
    close(fd);
    return ret;
}

/* 直接IO写入 */
ssize_t direct_write(const char *path, const void *buf, size_t count, off_t offset) {
    int fd = open(path, O_WRONLY | O_DIRECT | O_CREAT, 0644);
    if (fd < 0) return -1;
    
    ssize_t ret = pwrite(fd, buf, count, offset);
    
    /* 确保数据落盘 */
    fsync(fd);
    
    close(fd);
    return ret;
}
```

### 3.3 何时使用直接IO

```
适合使用O_DIRECT:
├── 应用自己管理缓存（如数据库）
├── 大块顺序IO
├── 避免双重缓冲
└── 需要精确控制数据落盘

不适合使用O_DIRECT:
├── 小块随机IO
├── 需要OS缓存优化
└── 共享文件访问
```

## 四、异步IO（AIO）

### 4.1 POSIX AIO

```c
#include <aio.h>

void posix_aio_example(void) {
    struct aiocb cb;
    char buf[4096];
    
    int fd = open("file.dat", O_RDONLY);
    
    memset(&cb, 0, sizeof(cb));
    cb.aio_fildes = fd;
    cb.aio_buf = buf;
    cb.aio_nbytes = sizeof(buf);
    cb.aio_offset = 0;
    
    /* 发起异步读取 */
    aio_read(&cb);
    
    /* 等待完成 */
    while (aio_error(&cb) == EINPROGRESS) {
        /* 可以做其他事情 */
    }
    
    /* 获取结果 */
    ssize_t ret = aio_return(&cb);
    
    close(fd);
}
```

### 4.2 Linux原生AIO

```c
#include <linux/aio_abi.h>
#include <sys/syscall.h>

/* 系统调用封装 */
int io_setup(unsigned nr, aio_context_t *ctxp) {
    return syscall(SYS_io_setup, nr, ctxp);
}

int io_destroy(aio_context_t ctx) {
    return syscall(SYS_io_destroy, ctx);
}

int io_submit(aio_context_t ctx, long nr, struct iocb **iocbpp) {
    return syscall(SYS_io_submit, ctx, nr, iocbpp);
}

int io_getevents(aio_context_t ctx, long min_nr, long nr,
                 struct io_event *events, struct timespec *timeout) {
    return syscall(SYS_io_getevents, ctx, min_nr, nr, events, timeout);
}

/* 使用示例 */
void linux_aio_example(void) {
    aio_context_t ctx = 0;
    struct iocb cb;
    struct iocb *cbs[1] = {&cb};
    struct io_event events[1];
    char *buf;
    
    /* 初始化上下文 */
    io_setup(128, &ctx);
    
    /* 分配对齐缓冲区 */
    posix_memalign((void**)&buf, 4096, 4096);
    
    int fd = open("file.dat", O_RDONLY | O_DIRECT);
    
    /* 设置IO控制块 */
    memset(&cb, 0, sizeof(cb));
    cb.aio_fildes = fd;
    cb.aio_lio_opcode = IOCB_CMD_PREAD;
    cb.aio_buf = (uint64_t)buf;
    cb.aio_nbytes = 4096;
    cb.aio_offset = 0;
    
    /* 提交IO */
    io_submit(ctx, 1, cbs);
    
    /* 等待完成 */
    io_getevents(ctx, 1, 1, events, NULL);
    
    /* 处理结果 */
    ssize_t ret = events[0].res;
    
    close(fd);
    free(buf);
    io_destroy(ctx);
}
```

## 五、零拷贝技术

### 5.1 零拷贝方法对比

| 方法 | 内核版本 | 适用场景 | 拷贝次数 |
|------|----------|----------|----------|
| read/write | 所有 | 通用 | 4次 |
| mmap + write | 所有 | 大文件 | 3次 |
| sendfile | 2.2+ | 文件→socket | 2次 |
| splice | 2.6+ | 管道传输 | 0次 |
| io_uring | 5.1+ | 通用异步 | 0-1次 |

### 5.2 sendfile

```c
#include <sys/sendfile.h>

ssize_t send_file_to_socket(int out_fd, int in_fd, size_t count) {
    off_t offset = 0;
    return sendfile(out_fd, in_fd, &offset, count);
}

/* 简单的静态文件服务器 */
void serve_file(int client_sock, const char *path) {
    int fd = open(path, O_RDONLY);
    struct stat st;
    fstat(fd, &st);
    
    /* 发送HTTP头 */
    char header[256];
    snprintf(header, sizeof(header),
             "HTTP/1.1 200 OK\r\n"
             "Content-Length: %ld\r\n"
             "\r\n", st.st_size);
    write(client_sock, header, strlen(header));
    
    /* 零拷贝发送文件内容 */
    sendfile(client_sock, fd, NULL, st.st_size);
    
    close(fd);
}
```

### 5.3 splice

```c
#include <fcntl.h>

/* 文件到socket的splice */
ssize_t splice_file_to_socket(int file_fd, int sock_fd, size_t len) {
    int pipefd[2];
    pipe(pipefd);
    
    /* 文件 → 管道 */
    ssize_t ret = splice(file_fd, NULL, pipefd[1], NULL, len,
                         SPLICE_F_MOVE | SPLICE_F_MORE);
    
    /* 管道 → socket */
    ret = splice(pipefd[0], NULL, sock_fd, NULL, ret,
                 SPLICE_F_MOVE | SPLICE_F_MORE);
    
    close(pipefd[0]);
    close(pipefd[1]);
    
    return ret;
}

/* socket到socket的splice */
ssize_t splice_sockets(int in_sock, int out_sock, size_t len) {
    int pipefd[2];
    pipe(pipefd);
    
    /* 设置非阻塞管道 */
    fcntl(pipefd[0], F_SETFL, O_NONBLOCK);
    fcntl(pipefd[1], F_SETFL, O_NONBLOCK);
    
    ssize_t ret = splice(in_sock, NULL, pipefd[1], NULL, len,
                         SPLICE_F_MOVE | SPLICE_F_NONBLOCK);
    if (ret > 0) {
        ret = splice(pipefd[0], NULL, out_sock, NULL, ret,
                     SPLICE_F_MOVE | SPLICE_F_NONBLOCK);
    }
    
    close(pipefd[0]);
    close(pipefd[1]);
    
    return ret;
}
```

### 5.4 vmsplice

```c
#include <fcntl.h>
#include <sys/uio.h>

/* 用户空间缓冲区直接映射到管道 */
ssize_t vmsplice_to_socket(int sock_fd, void *buf, size_t len) {
    int pipefd[2];
    pipe(pipefd);
    
    struct iovec iov = {
        .iov_base = buf,
        .iov_len = len
    };
    
    /* 将用户缓冲区映射到管道 */
    ssize_t ret = vmsplice(pipefd[1], &iov, 1, SPLICE_F_GIFT);
    
    /* 管道到socket */
    ret = splice(pipefd[0], NULL, sock_fd, NULL, ret, SPLICE_F_MOVE);
    
    close(pipefd[0]);
    close(pipefd[1]);
    
    return ret;
}
```

## 六、io_uring

### 6.1 io_uring基础

```c
#include <liburing.h>

void io_uring_example(void) {
    struct io_uring ring;
    struct io_uring_sqe *sqe;
    struct io_uring_cqe *cqe;
    
    /* 初始化ring */
    io_uring_queue_init(256, &ring, 0);
    
    /* 打开文件 */
    int fd = open("file.dat", O_RDONLY);
    char buf[4096];
    
    /* 获取SQE */
    sqe = io_uring_get_sqe(&ring);
    
    /* 准备读取操作 */
    io_uring_prep_read(sqe, fd, buf, sizeof(buf), 0);
    sqe->user_data = 1;  /* 标识这个操作 */
    
    /* 提交 */
    io_uring_submit(&ring);
    
    /* 等待完成 */
    io_uring_wait_cqe(&ring, &cqe);
    
    /* 处理结果 */
    if (cqe->res >= 0) {
        printf("Read %d bytes\n", cqe->res);
    }
    
    /* 标记CQE已处理 */
    io_uring_cqe_seen(&ring, cqe);
    
    close(fd);
    io_uring_queue_exit(&ring);
}
```

### 6.2 io_uring批量提交

```c
void io_uring_batch_example(void) {
    struct io_uring ring;
    io_uring_queue_init(256, &ring, 0);
    
    /* 批量准备多个操作 */
    for (int i = 0; i < 10; i++) {
        struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
        io_uring_prep_nop(sqe);
        sqe->user_data = i;
    }
    
    /* 一次提交所有操作 */
    io_uring_submit(&ring);
    
    /* 批量等待完成 */
    struct io_uring_cqe *cqes[10];
    int ret = io_uring_peek_batch_cqe(&ring, cqes, 10);
    
    for (int i = 0; i < ret; i++) {
        printf("Completed: %llu\n", cqes[i]->user_data);
    }
    
    io_uring_cq_advance(&ring, ret);
    io_uring_queue_exit(&ring);
}
```

## 总结

高效IO的核心要点：

1. **mmap**：适合大文件和共享内存，注意预热和对齐
2. **Huge Pages**：减少TLB miss，HFT必用
3. **THP**：HFT场景建议禁用，避免不可预测的延迟
4. **O_DIRECT**：绕过页缓存，适合自管理缓存的应用
5. **零拷贝**：sendfile/splice减少数据复制
6. **io_uring**：现代Linux最高效的异步IO

选择合适的IO策略可以显著提升系统性能和降低延迟。
