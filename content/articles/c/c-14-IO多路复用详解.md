+++
title = "14. IO Multiplexing (select/poll/epoll)"
slug = "c-IO多路复用的例子"
+++

# IO多路复用的例子
## select
`select` 是一种传统的I/O多路复用机制，它允许程序同时监视多个文件描述符（file descriptors），以确定哪些文件描述符已经准备好进行I/O操作（如读、写）。`select` 是较早的I/O多路复用技术，它在各种UNIX-like操作系统中广泛支持。

### 基本原理
`select` 函数通过监视文件描述符集合中的活动来工作。它允许程序等待直到某个文件描述符就绪，然后进行相应的读或写操作。`select` 会阻塞调用线程，直到以下情况发生：

+ 一个或多个监视的文件描述符就绪（可读、可写或有异常）。
+ 超时时间到达（如果没有文件描述符就绪）。
+ 被信号打断。

### 函数原型
```c
int select(int nfds, fd_set *readfds, fd_set *writefds, fd_set *exceptfds, struct timeval *timeout);
```

+ `nfds`：监视的文件描述符集合中最大文件描述符的值加1。
+ `readfds`：指向读文件描述符集合的指针，`select` 检查这些文件描述符是否有数据可读。
+ `writefds`：指向写文件描述符集合的指针，`select` 检查这些文件描述符是否可写。
+ `exceptfds`：指向异常条件文件描述符集合的指针，通常用于检查OOB（out-of-band）数据。
+ `timeout`：指定`select` 调用的最长阻塞时间。如果设置为NULL，`select` 将无限期阻塞。

### 返回值
+ 成功时，返回就绪文件描述符的数量。
+ 如果超时，返回0。
+ 如果出错，返回-1，并设置全局变量`errno`。

### 使用步骤
1. 初始化`fd_set`集合。
2. 使用`FD_SET`宏将感兴趣的文件描述符添加到集合中。
3. 调用`select`函数。
4. `select` 返回后，使用`FD_ISSET`宏检查哪些文件描述符就绪。
5. 根据就绪的文件描述符进行相应的读或写操作。
6. 循环步骤1-5。

### 示例代码
```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/select.h>

int main() {
    int sockfd, nfds;
    fd_set readfds;
    struct timeval tv;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    // 初始化文件描述符集合
    FD_ZERO(&readfds);
    FD_SET(sockfd, &readfds);

    // 设置监视的文件描述符数量
    nfds = sockfd + 1;

    // 设置超时时间
    tv.tv_sec = 5;
    tv.tv_usec = 0;

    // 调用select
    int retval = select(nfds, &readfds, NULL, NULL, &tv);
    if (retval == -1) {
        perror("select()");
        exit(EXIT_FAILURE);
    } else if (retval) {
        if (FD_ISSET(sockfd, &readfds)) {
            printf("Data is ready to be read\n");
            // 执行读取操作
        }
    } else {
        printf("Timeout!\n");
    }

    close(sockfd);
    return 0;
}
```

### 注意事项
+ `select` 每次调用时都会复制文件描述符集合，这可能会导致性能问题，尤其是在文件描述符数量较多的情况下。
+ `select` 有一个限制，即它不能处理大量的文件描述符。在大多数系统上，这个限制是1024，尽管这个值可以通过`getrlimit`和`setrlimit`调用来增加。
+ `select` 是阻塞调用，如果没有任何文件描述符就绪，它将一直阻塞，直到超时或有文件描述符就绪。

尽管`select`有这些局限性，但它仍然是一个简单且在某些情况下有效的I/O多路复用选择。在需要处理大量文件描述符或需要更高效I/O多路复用时，可以考虑使用`poll`或`epoll`（仅限于Linux）。

## poll
`poll` 是一种I/O多路复用技术，它允许程序同时监控多个文件描述符（FD），以确定哪些文件描述符已经准备好进行I/O操作。与 `select` 类似，`poll` 通过检查一个文件描述符列表来确定是否有文件描述符已经准备好进行非阻塞读或写。

### `poll` 函数原型
```c
int poll(struct pollfd *fds, nfds_t nfds, int timeout);
```

+ `fds`：指向 `pollfd` 结构体数组的指针，用于指定要监控的文件描述符和事件。
+ `nfds`：指定 `fds` 数组中元素的数量。
+ `timeout`：指定 `poll` 函数的超时时间，单位为毫秒。如果设置为 `-1`，`poll` 将阻塞直到至少一个文件描述符就绪；如果设置为 `0`，`poll` 将立即返回，不会阻塞。

### `pollfd` 结构体
```c
struct pollfd {
    int fd;        // 要监控的文件描述符
    short events;  // 要监控的事件
    short revents; // 已发生的事件
};
```

+ `fd`：要监控的文件描述符。
+ `events`：要监控的事件，可以是 `POLLIN`、`POLLOUT`、`POLLERR` 等。
+ `revents`：实际发生的事件，可以是 `events` 中指定的事件，也可以是 `POLLHUP`、`POLLNVAL` 等。

### C语言例子
下面是一个使用 `poll` 的简单示例，该示例创建了一个服务器，监听一个端口，并接受连接：

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <poll.h>

#define PORT 8080
#define MAX_CLIENTS 5

int main() {
    int server_fd, client_fd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t client_addr_len;
    struct pollfd fds[MAX_CLIENTS + 1];

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr*)&server_addr, sizeof(server_addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }

    if (listen(server_fd, MAX_CLIENTS) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    fds[0].fd = server_fd;
    fds[0].events = POLLIN;

    for (int i = 1; i <= MAX_CLIENTS; i++) {
        fds[i].fd = -1;
    }

    while (1) {
        int ret = poll(fds, MAX_CLIENTS + 1, -1);
        if (ret > 0) {
            if (fds[0].revents & POLLIN) {
                client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_addr_len);
                if (client_fd == -1) {
                    perror("accept");
                    continue;
                }
                for (int i = 1; i <= MAX_CLIENTS; i++) {
                    if (fds[i].fd == -1) {
                        fds[i].fd = client_fd;
                        fds[i].events = POLLIN;
                        break;
                    }
                }
            }

            for (int i = 1; i <= MAX_CLIENTS; i++) {
                if (fds[i].revents & POLLIN) {
                    char buffer[1024];
                    int bytes_read = read(fds[i].fd, buffer, sizeof(buffer));
                    if (bytes_read > 0) {
                        write(fds[i].fd, buffer, bytes_read);
                    } else {
                        close(fds[i].fd);
                        fds[i].fd = -1;
                    }
                }
            }
        }
    }

    close(server_fd);
    return 0;
}
```

在这个例子中，服务器使用 `poll` 来监控多个客户端连接。当有新的连接请求时，服务器接受连接并将新的文件描述符添加到 `pollfd` 数组中。然后，服务器继续监控所有连接以接收数据。如果接收到数据，服务器将其回显给客户端。如果客户端断开连接，服务器关闭该文件描述符并从 `pollfd` 数组中移除。

### 注意事项
+ `poll` 没有最大文件描述符数量的限制，但是文件描述符的数量过多可能会影响性能。
+ `poll` 函数的 `timeout` 参数可以控制函数的阻塞时间。设置为 `-1` 表示无限期阻塞，直到有文件描述符就绪；设置为 `0` 表示非阻塞调用，立即返回。
+ 在使用 `poll` 时，需要确保正确处理所有可能的错误情况，例如文件描述符无效或网络错误。

## epoll
`epoll` 是 Linux 系统下的一种高效的 I/O 多路复用技术，它在处理大量并发连接时相比于 `select` 和 `poll` 具有显著的性能优势。下面将详细介绍 `epoll` 的原理和使用方法，并提供一个 C 语言的使用示例。

### `epoll` 原理
`epoll` 是 Linux 提供的一种高效的 I/O 事件通知机制，它通过在内核中维护一个事件表来实现对多个文件描述符的监控。当文件描述符上发生事件时，`epoll` 能够将这些事件通知给用户空间的应用程序。

`epoll` 有两种工作模式：水平触发（Level Triggered, LT）和边缘触发（Edge Triggered, ET）。默认情况下，`epoll` 工作在 LT 模式，即只要文件描述符的状态没有被改变，`epoll` 会持续通知应用程序。而在 ET 模式下，文件描述符的状态发生变化时才会通知一次。

### `epoll` 函数
1. `epoll_create`：创建一个新的 `epoll` 实例。
2. `epoll_ctl`：向 `epoll` 实例中添加、修改或删除文件描述符。
3. `epoll_wait`：等待文件描述符就绪。

### C 语言示例
下面是一个简单的 `epoll` 使用示例，该示例创建了一个监听特定端口的服务器，使用 `epoll` 来处理客户端的连接和数据传输。

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/epoll.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define MAX_EVENTS 10
#define PORT 8080

int main() {
    int listen_sock, conn_sock, nfds, epollfd;
    struct sockaddr_in addr;
    struct epoll_event event, events[MAX_EVENTS];
    int yes = 1;

    // 创建监听套接字
    listen_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_sock == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    setsockopt(listen_sock, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes));

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(PORT);

    if (bind(listen_sock, (struct sockaddr *) &addr, sizeof(addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }

    if (listen(listen_sock, 5) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    // 创建epoll实例
    epollfd = epoll_create1(0);
    if (epollfd == -1) {
        perror("epoll_create1");
        exit(EXIT_FAILURE);
    }

    // 添加监听套接字到epoll监控
    event.data.fd = listen_sock;
    event.events = EPOLLIN | EPOLLET;
    if (epoll_ctl(epollfd, EPOLL_CTL_ADD, listen_sock, &event) == -1) {
        perror("epoll_ctl: listen_sock");
        exit(EXIT_FAILURE);
    }

    nfds = 0;
    while (1) {
        int n, i;

        n = epoll_wait(epollfd, events, MAX_EVENTS, -1);
        for (i = 0; i < n; i++) {
            if ((events[i].events & EPOLLERR) ||
                (events[i].events & EPOLLHUP) ||
                (!(events[i].events & EPOLLIN))) {
                // 出错则关闭文件描述符
                fprintf(stderr, "epoll error\n");
                close(events[i].data.fd);
                continue;
            } else if (listen_sock == events[i].data.fd) {
                // 接受新的连接
                while ((conn_sock = accept(listen_sock, NULL, NULL)) > 0) {
                    // 设置为非阻塞模式
                    fcntl(conn_sock, F_SETFL, O_NONBLOCK);
                    event.data.fd = conn_sock;
                    event.events = EPOLLIN | EPOLLET;
                    if (epoll_ctl(epollfd, EPOLL_CTL_ADD, conn_sock, &event) == -1) {
                        perror("epoll_ctl: conn_sock");
                        exit(EXIT_FAILURE);
                    }
                }
            } else {
                // 处理数据
                // 这里可以添加读取和发送数据的代码
            }
        }
    }

    close(listen_sock);
    return 0;
}
```

在这个示例中，服务器使用 `epoll` 来监控监听套接字上的连接请求和已连接套接字上的数据事件。当有新的连接请求时，服务器接受连接并将新的套接字添加到 `epoll` 的监控列表中。对于已连接的套接字，服务器可以读取数据并进行处理。

### 注意事项
+ 在使用 `epoll` 时，需要注意正确处理所有可能的错误情况，例如文件描述符无效或网络错误。
+ 在实际应用中，可能需要根据具体的应用场景和需求进行调整，例如处理半关闭连接、设置超时等。
+ `epoll` 的性能优势在处理大量并发连接时尤为明显，但在连接数较少时，其优势可能不太明显。

## kqueue
`kqueue` 是一种高效的 I/O 多路复用机制，它在 FreeBSD 4.1 中首次引入，并被 NetBSD、OpenBSD、macOS 等操作系统支持。`kqueue` 通过在内核态维持状态提供了更高的性能，并且可以同时处理文件描述符事件、文件修改监视、信号、异步 I/O 事件、子进程状态事件等多种事件。

### `kqueue` 基本原理
`kqueue` 通过 `kevent` 系统调用来监控文件描述符上的事件。每个 `kevent` 由一个 `<ident, filter>` 对标识，其中 `ident` 可以是文件描述符、进程 ID 或信号量等，而 `filter` 指定了事件的类型，如 `EVFILT_READ` 或 `EVFILT_WRITE`。

### `kqueue` 函数
1. `kqueue()`：创建一个新的 `kqueue` 实例，返回一个文件描述符。
2. `kevent()`：用于注册感兴趣的事件和获取发生的事件。

### C语言示例
下面是一个使用 `kqueue` 的简单示例，该示例创建了一个监听特定端口的服务器，使用 `kqueue` 来处理客户端的连接和数据传输。

```c
#include <sys/types.h>
#include <sys/event.h>
#include <sys/time.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT 8080
#define LISTENQ 1024

int main() {
    int kq, nfds, fd, flags;
    struct sockaddr_in addr;
    struct kevent event;

    kq = kqueue();
    if (kq == -1) {
        perror("kqueue");
        exit(EXIT_FAILURE);
    }

    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd == -1) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) {
        perror("fcntl F_GETFL");
        exit(EXIT_FAILURE);
    }

    if (fcntl(fd, F_SETFL, flags | O_NONBLOCK) == -1) {
        perror("fcntl F_SETFL");
        exit(EXIT_FAILURE);
    }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_ANY);
    addr.sin_port = htons(PORT);

    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
        perror("bind");
        exit(EXIT_FAILURE);
    }

    if (listen(fd, LISTENQ) == -1) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    EV_SET(&event, fd, EVFILT_READ, EV_ADD, 0, 0, NULL);

    if (kevent(kq, &event, 1, NULL, 0, NULL) == -1) {
        perror("kevent");
        exit(EXIT_FAILURE);
    }

    nfds = kevent(kq, NULL, 0, &event, 1, NULL);
    if (nfds == -1) {
        perror("kevent");
        exit(EXIT_FAILURE);
    }

    if (nfds > 0) {
        if (event.flags & EV_ERROR) {
            perror("kevent error");
            exit(EXIT_FAILURE);
        }
        printf("Data ready to be read\n");
    }

    close(fd);
    close(kq);
    return 0;
}
```

在这个示例中，服务器使用 `kqueue` 来监控监听套接字上的连接请求。当有新的连接请求时，服务器接受连接并处理数据。这个示例展示了 `kqueue` 的基本用法，包括创建 `kqueue` 实例、注册事件、等待事件和处理事件。

### 注意事项
+ `kqueue` 没有最大文件描述符数量的限制，但是需要注意正确处理所有可能的错误情况，例如文件描述符无效或网络错误。
+ 在实际应用中，可能需要根据具体的应用场景和需求进行调整，例如处理半关闭连接、设置超时等。

## /dev/poll (Linux)
`/dev/poll`，也被称为 `poll` 或 `/dev/pollselect`，是一种高效的 I/O 多路复用机制，它在 Linux 内核中提供。与 `select` 和 `poll` 相比，`/dev/poll` 能够更高效地处理大量的并发连接，因为它不需要在每次调用时重复传递和检查整个文件描述符集合。

### `/dev/poll` 基本原理
`/dev/poll` 通过一个字符设备接口来实现 I/O 多路复用。它使用一组独立的系统调用，包括 `poll`、`select` 和 `epoll`，来监控文件描述符上的事件。`/dev/poll` 通过维护一个高效的内部数据结构来跟踪感兴趣的事件，并在事件发生时立即通知应用程序。

### `/dev/poll` 函数
1. `poll`：与标准的 `poll` 函数类似，但通常与 `/dev/poll` 设备一起使用以提高效率。
2. `select`：与标准的 `select` 函数类似，但也可以与 `/dev/poll` 一起使用。
3. `epoll`：是 `/dev/poll` 的现代替代品，提供了更高的性能和更丰富的功能。

### C语言示例
下面是一个使用 `/dev/poll` 的简单示例，该示例创建了一个监听特定端口的服务器，并使用 `/dev/poll` 来处理客户端的连接和数据传输。

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/poll.h>

#define PORT 8080
#define QUEUE 5

int main() {
    int listenfd, connfd, nfds;
    struct sockaddr_in servaddr, cliaddr;
    socklen_t clilen;
    struct pollfd *fds;
    int i, maxfdp1;
    char buf[512];
    char *hello = "Hello, you are connected to the server\n";

    listenfd = socket(AF_INET, SOCK_STREAM, 0);
    if (listenfd < 0) {
        perror("socket error");
        exit(1);
    }

    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
    servaddr.sin_port = htons(PORT);

    if (bind(listenfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("bind error");
        exit(1);
    }

    if (listen(listenfd, QUEUE) < 0) {
        perror("listen error");
        exit(1);
    }

    nfds = listenfd + 1;
    fds = malloc(nfds * sizeof(struct pollfd));
    if (fds == NULL) {
        perror("malloc error");
        exit(1);
    }

    for (i = 0; i < nfds; i++) {
        fds[i].events = 0;
    }

    for (;;) {
        maxfdp1 = poll(fds, nfds, 5000);
        if (maxfdp1 < 0) {
            perror("poll error");
            exit(1);
        }

        for (i = 0; i < nfds; i++) {
            if (fds[i].revents & POLLIN) {
                if (i == 0) {  // listen socket
                    clilen = sizeof(cliaddr);
                    connfd = accept(listenfd, (struct sockaddr *)&cliaddr, &clilen);
                    if (connfd < 0) {
                        perror("accept error");
                        exit(1);
                    }
                    printf("New connection from %s:%d\n", inet_ntoa(cliaddr.sin_addr), ntohs(cliaddr.sin_port));
                    fds[connfd].events = POLLIN;
                } else {  // client socket
                    int readlen = read(i, buf, sizeof(buf));
                    if (readlen > 0) {
                        printf("Received: %s", buf);
                        write(i, hello, strlen(hello));
                    } else {
                        close(i);
                        fds[i].fd = -1;
                        fds[i].events = 0;
                    }
                }
            }
        }
    }

    close(listenfd);
    free(fds);
    return 0;
}
```

在这个示例中，服务器使用 `/dev/poll` 来监控监听套接字上的连接请求。当有新的连接请求时，服务器接受连接并将新的套接字添加到 `pollfd` 数组中。然后，服务器继续监控所有连接以接收数据。如果接收到数据，服务器将其回显给客户端。

### 注意事项
+ `/dev/poll` 是特定于 Linux 的，因此在编写跨平台代码时需要注意。
+ 在实际应用中，可能需要根据具体的应用场景和需求进行调整，例如处理半关闭连接、设置超时等。
+ `/dev/poll` 的性能优势在处理大量并发连接时尤为明显，但在连接数较少时，其优势可能不太明显。

`/dev/poll` 和 `poll` 不是一回事，它们之间有以下区别：

1. `poll`** 系统调用**：
    - `poll` 是一个 POSIX 标准的系统调用，它提供了一种机制，允许应用程序同时监视多个文件描述符（FD），以确定哪些文件描述符已经准备好进行 I/O 操作（如读、写）。
    - `poll` 通过使用 `pollfd` 结构体数组来监控文件描述符上的事件。每个 `pollfd` 结构体指定了一个文件描述符和要监控的事件类型。
    - `poll` 函数在所有主流的类 Unix 操作系统中都有实现，包括 Linux、FreeBSD、macOS 等。
2. `/dev/poll`：
    - `/dev/poll` 是 Linux 特有的一种 I/O 多路复用机制，它通过一个特殊的字符设备文件（`/dev/poll`）来实现。
    - 使用 `/dev/poll` 时，应用程序首先通过 `open` 系统调用打开 `/dev/poll` 设备文件，然后使用相关的ioctl调用来注册要监控的文件描述符和事件。
    - `/dev/poll` 通常与 `poll` 系统调用一起使用，以提高大量文件描述符监控的效率。它允许内核直接向应用程序传递发生的事件，而不需要像标准 `poll` 那样每次都检查所有文件描述符。
    - `/dev/poll` 是较早的实现，后来被 `epoll` 取代，因为 `epoll` 提供了更高的性能和更好的扩展性。

总结来说，`poll` 是一个通用的系统调用，而 `/dev/poll` 是 Linux 系统上的一个特定实现，用于提高 `poll` 系统调用的效率。在 Linux 系统中，`/dev/poll` 通常作为 `poll` 的后端实现，但在现代 Linux 系统中，`epoll` 是更常用的高性能 I/O 多路复用机制。

## libuv
`libuv` 是一个跨平台的异步 I/O 库，它提供了事件循环、文件系统操作、网络和其他系统相关的功能。`libuv` 被设计为易于使用，同时提供了高性能的异步 I/O 功能。它主要用于 Node.js，但也被其他项目如 Luvit 和 Julia 等使用。

### `libuv` 的特点包括
+ 基于不同操作系统的后端，如 Linux 的 `epoll`、BSD 的 `kqueue`、Windows 的 `IOCP`。
+ 异步 TCP 和 UDP 套接字。
+ 异步 DNS 解析。
+ 异步文件系统操作。
+ 文件系统事件。
+ 子进程处理。
+ 信号处理。
+ 高分辨率时钟。
+ 线程和同步原语。

### C语言示例
下面是一个使用 `libuv` 的简单示例，该示例创建了一个简单的回显服务器：

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <uv.h>

void on_read(uv_stream_t* tcp, ssize_t nread, const uv_buf_t* buf) {
    if (nread > 0) {
        uv_write_t* write_req = malloc(sizeof(uv_write_t));
        uv_buf_t write_buf = uv_buf_init(buf->base, nread);
        uv_write(write_req, tcp, &write_buf, 1, -1, free);
    } else if (nread < 0) {
        uv_close((uv_handle_t*)tcp, free);
    }
}

int main() {
    uv_loop_t* loop = uv_default_loop();
    uv_tcp_t server;
    uv_tcp_init(loop, &server);

    struct sockaddr_in addr;
    uv_ip4_addr("0.0.0.0", 8080, &addr);

    uv_tcp_bind(&server, (const struct sockaddr*)&addr, 0);
    uv_listen((uv_stream_t*)&server, 128, (uv_connection_cb)uv_accept);

    uv_run(loop, UV_RUN_DEFAULT);
    return 0;
}
```

在这个示例中，我们创建了一个 `uv_tcp_t` 服务器，绑定到 `0.0.0.0` 的 `8080` 端口，并开始监听连接。当有数据可读时，`on_read` 回调函数会被调用，并将读取的数据写回客户端。

### 注意事项
+ `libuv` 的事件循环是异步和非阻塞的，这意味着你的程序可以在不等待 I/O 操作完成的情况下继续执行其他任务。
+ `libuv` 提供了丰富的 API 来处理各种类型的事件，包括定时器、文件系统事件、网络事件等。
+ 在使用 `libuv` 时，你需要确保正确地管理内存，例如在异步请求完成后释放分配的内存。

`libuv` 是一个强大的库，它为开发高性能的异步 I/O 应用程序提供了必要的工具和抽象。通过使用 `libuv`，开发者可以编写出既高效又可读的系统级代码。

## libevent
`libevent` 是一个用C语言编写的轻量级开源高性能事件通知库，它提供了一种机制来执行事件通知，允许程序在单个线程中高效地处理多个事件源，包括IO事件、定时事件和信号事件。这使得开发者能够构建出响应迅速且易于扩展的网络应用程序，特别是在需要处理大量并发连接的场景中。`libevent` 支持多种平台，包括 Linux、Unix 和 Windows，并且提供了跨平台的事件处理机制。

### C语言示例
下面是一个使用 `libevent` 的简单示例，该示例创建了一个简单的回显服务器：

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <event2/event.h>
#include <event2/bufferevent.h>
#include <event2/listener.h>

void read_cb(struct bufferevent *bev, void *ctx) {
    char buf[1024];
    size_t len = bufferevent_read(bev, buf, sizeof(buf) - 1);
    if (len > 0) {
        buf[len] = '\0';
        printf("Received: %s\n", buf);
        bufferevent_write(bev, buf, len);
    }
}

void event_cb(struct bufferevent *bev, short events, void *ctx) {
    if (events & BEV_EVENT_EOF) {
        printf("Connection closed.\n");
    } else if (events & BEV_EVENT_ERROR) {
        printf("Got an error on the connection.\n");
    }
    bufferevent_free(bev);
}

int main(int argc, char **argv) {
    struct event_base *base = event_base_new();
    struct evconnlistener *listener;
    struct sockaddr_in sin;
    int port = 9999;

    memset(&sin, 0, sizeof(sin));
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = htonl(INADDR_ANY);
    sin.sin_port = htons(port);

    listener = evconnlistener_new_bind(base, NULL, -1,
                                      LEV_OPT_REUSEABLE | LEV_OPT_CLOSE_ON_FREE,
                                      16, (struct sockaddr *)&sin, sizeof(sin));

    evconnlistener_set_cb(listener, read_cb, event_cb, NULL);

    event_base_dispatch(base);

    evconnlistener_free(listener);
    event_base_free(base);

    return 0;
}
```

在这个示例中，我们创建了一个 `event_base`，然后创建了一个 `evconnlistener` 来监听指定端口的连接请求。当有新的连接请求时，`libevent` 会调用我们设置的回调函数 `read_cb` 来处理读事件。在这个回调函数中，我们读取数据并将其回显给客户端。同时，我们设置了 `event_cb` 来处理可能发生的事件，如连接关闭或错误。

### 注意事项
+ `libevent` 的事件操作只能在事件循环的同一个线程中执行，这意味着如果你需要在多线程环境中使用 `libevent`，你需要确保每个线程都有自己的 `event_base`。
+ 在实际应用中，可能需要根据具体的应用场景和需求进行调整，例如处理半关闭连接、设置超时等。
+ `libevent` 提供了丰富的 API 来处理各种类型的事件，包括定时器、文件系统事件、网络事件等。

这个简单的示例展示了 `libevent` 的基本用法，包括创建事件循环、监听端口、处理连接和读写事件。在实际应用中，你可能需要更复杂的逻辑来处理不同的事件和业务需求。

## Boost.Asio
`Boost.Asio` 是一个跨平台的 C++ 网络和 I/O 库，它使用现代 C++ 语言和一致的异步模型进行程序开发。它提供了管理耗时操作的工具，而不需要开发人员使用基于传统线程和显式锁的并发模型。`Boost.Asio` 可以用来执行同步和异步操作，如 socket 上的 I/O 操作。它的核心作用是异步输入/输出，并且它的核心概念和功能包括 `io_service`、`ip::tcp::socket`、`deadline_timer` 等。

### C语言示例
下面是一个使用 `Boost.Asio` 的简单示例，该示例创建了一个异步的 TCP 回显客户端：

```c
#include <boost/asio.hpp>
#include <iostream>

using boost::asio::ip::tcp;

void read_handler(const boost::system::error_code& ec, std::size_t bytes_transferred) {
    if (!ec) {
        std::cout << "Received: " << bytes_transferred << " bytes." << std::endl;
    }
}

void write_handler(const boost::system::error_code& ec, std::size_t bytes_transferred) {
    if (!ec) {
        std::cout << "Sent: " << bytes_transferred << " bytes." << std::endl;
    }
}

int main() {
    boost::asio::io_service io_service;
    tcp::socket socket(io_service);
    tcp::resolver resolver(io_service);
    boost::asio::connect(socket, resolver.resolve("localhost", "12345"));

    std::string message = "Hello, Boost.Asio!";
    boost::asio::async_write(socket, boost::asio::buffer(message), write_handler);

    char buffer[1024];
    boost::asio::async_read(socket, boost::asio::buffer(buffer), read_handler);

    io_service.run();

    return 0;
}
```

在这个示例中，我们创建了一个 `io_service` 实例，然后创建了一个 `tcp::socket` 对象。我们使用 `tcp::resolver` 来解析服务器的地址和端口。然后，我们使用 `async_write` 函数异步发送数据，使用 `async_read` 函数异步接收数据。最后，我们调用 `io_service.run()` 来启动事件循环。

请注意，`Boost.Asio` 是 C++ 库，而不是 C 语言库，因此上面的示例是用 C++ 编写的。C 语言没有直接使用 `Boost.Asio` 的能力，但 C++ 代码可以作为 C 语言项目的组成部分。如果你需要在 C 项目中使用类似的异步网络功能，你可能需要寻找或编写一个 C 语言的网络库，或者考虑将你的项目迁移到 C++。

