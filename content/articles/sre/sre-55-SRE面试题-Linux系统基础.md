+++
title = "55.SRE面试题-Linux系统基础"
date = 2026-01-21
description = "SRE面试必备：Linux进程线程、内存管理、文件系统、信号处理等核心问题详解"
[taxonomies]
tags = ["SRE", "面试", "Linux", "进程", "内存", "文件系统"]
+++

## 概述

Linux系统知识是SRE面试的核心考察点。本文详细解答进程线程、内存管理、文件系统等高频面试问题。

---

# 一、进程与线程

## 1.1 进程和线程的区别？

**标准答案**：

```
进程（Process）：
- 操作系统资源分配的基本单位
- 拥有独立的地址空间、文件描述符、信号处理等
- 进程间通信需要IPC机制（管道、共享内存、消息队列等）
- 创建和销毁开销较大
- 一个进程崩溃不会直接影响其他进程

线程（Thread）：
- CPU调度的基本单位
- 共享进程的地址空间、文件描述符等资源
- 线程间通信可直接读写共享内存
- 创建和切换开销较小
- 一个线程崩溃可能导致整个进程崩溃

关键区别：
| 维度 | 进程 | 线程 |
|------|------|------|
| 地址空间 | 独立 | 共享 |
| 资源开销 | 大 | 小 |
| 通信方式 | IPC | 共享内存 |
| 切换开销 | 大（需切换页表） | 小 |
| 安全性 | 高（隔离） | 低（共享） |
```

**深入追问：为什么线程切换比进程切换快？**

```
1. 不需要切换页表（地址空间相同）
2. 不需要刷新TLB（Translation Lookaside Buffer）
3. 缓存命中率更高（共享代码和数据）

进程切换需要：
- 保存/恢复所有寄存器
- 切换页表基址寄存器
- 刷新TLB
- 可能导致缓存失效

线程切换只需要：
- 保存/恢复部分寄存器（PC、SP等）
- 栈指针切换
```

**实战命令**：

```bash
# 查看进程
ps aux

# 查看进程的线程
ps -T -p <PID>
# 或
ls /proc/<PID>/task/

# 查看线程数
cat /proc/<PID>/status | grep Threads

# top显示线程
top -H -p <PID>
```

---

## 1.2 僵尸进程是什么？如何处理？

**标准答案**：

```
僵尸进程（Zombie Process）：
- 子进程已终止，但父进程未调用wait()回收其退出状态
- 进程表中保留一条记录（PCB），占用PID
- 不占用内存、CPU等其他资源
- 状态显示为Z（Zombie）或<defunct>

产生原因：
1. 父进程忙于其他任务，未及时调用wait()
2. 父进程代码bug，忘记回收子进程
3. 父进程故意不回收（某些场景）

危害：
- 占用进程表项（PID资源有限）
- 大量僵尸进程会导致无法创建新进程
```

**如何处理**：

```bash
# 1. 找出僵尸进程
ps aux | awk '$8=="Z" {print}'
ps aux | grep defunct

# 2. 找到其父进程
ps -o ppid= -p <zombie_pid>

# 3. 向父进程发送SIGCHLD信号
kill -SIGCHLD <parent_pid>

# 4. 如果无效，杀死父进程（僵尸会被init接管并清理）
kill <parent_pid>
# 或
kill -9 <parent_pid>

# 注意：不能直接kill僵尸进程，因为它已经死了
```

**代码层面预防**：

```c
// 方法1：显式调用wait()
wait(NULL);

// 方法2：注册SIGCHLD处理函数
void sigchld_handler(int sig) {
    while (waitpid(-1, NULL, WNOHANG) > 0);
}
signal(SIGCHLD, sigchld_handler);

// 方法3：忽略SIGCHLD（子进程不会变僵尸）
signal(SIGCHLD, SIG_IGN);
```

---

## 1.3 如何查看系统负载？load average意味着什么？

**标准答案**：

```bash
# 查看负载
uptime
# 输出：10:30:00 up 5 days, load average: 1.50, 2.00, 1.80
#                                          1分钟  5分钟  15分钟

# 其他命令
w
top
cat /proc/loadavg
```

**Load Average含义**：

```
Load Average = 运行队列中的平均进程数
             = 正在运行(R) + 等待运行(R) + 不可中断睡眠(D) 的进程数

注意：不可中断睡眠(D状态)也计入Load！
这与其他Unix系统不同，Linux特有。

解读（假设4核CPU）：
| Load | 含义 |
|------|------|
| 1.0  | 单核满载，或4核各25% |
| 4.0  | 4核刚好满载 |
| 8.0  | 4核满载 + 4个进程等待 |
| 0.5  | 系统较空闲 |

经验法则：
- Load < CPU核数：系统正常
- Load = CPU核数：刚好饱和
- Load > CPU核数：过载，需排查
```

**高Load的排查思路**：

```bash
# 1. 确认CPU核数
nproc
# 或
cat /proc/cpuinfo | grep processor | wc -l

# 2. 区分CPU密集还是IO等待
top
# 看%us（用户态）、%sy（内核态）、%wa（IO等待）

# 场景1：高Load + 高CPU使用率 → CPU瓶颈
ps aux --sort=-%cpu | head

# 场景2：高Load + 高%wa → IO瓶颈
iostat -x 1 5
iotop

# 场景3：高Load + 低CPU + 低IO → D状态进程
ps aux | awk '$8~/D/'
```

---

## 1.4 孤儿进程是什么？

**标准答案**：

```
孤儿进程（Orphan Process）：
- 父进程先于子进程终止
- 子进程被init进程（PID=1）收养
- init会负责回收孤儿进程的退出状态

与僵尸进程的区别：
| 类型 | 父进程状态 | 子进程状态 | 危害 |
|------|------------|------------|------|
| 孤儿 | 已终止 | 运行中 | 无（被init收养） |
| 僵尸 | 运行中 | 已终止未回收 | 占用PID |

孤儿进程是正常现象，由系统自动处理。
```

---

## 1.5 什么是进程的D状态？

**标准答案**：

```
D状态（Uninterruptible Sleep）：
- 不可中断的睡眠状态
- 进程正在等待IO操作完成
- 不响应任何信号，包括SIGKILL
- kill -9 对D状态进程无效

常见原因：
1. 等待磁盘IO
2. NFS挂载点无响应
3. 硬件故障
4. 内核bug

特点：
- 会计入Load Average
- 大量D状态进程会导致系统看起来负载很高
```

**排查D状态进程**：

```bash
# 找出D状态进程
ps aux | awk '$8~/D/'

# 查看进程在等什么
cat /proc/<PID>/stack

# 常见的wait函数
# wait_on_page_bit - 等待页面IO
# blkdev_issue_flush - 等待块设备
# nfs4_wait_bit_killable - NFS等待
```

---

## 1.6 进程间通信（IPC）有哪些方式？

**标准答案**：

```
1. 管道（Pipe）
   - 匿名管道：只能用于父子进程
   - 命名管道（FIFO）：可用于任意进程
   - 半双工，数据单向流动

2. 消息队列（Message Queue）
   - 内核中的链表
   - 可发送有类型的消息
   - 支持消息优先级

3. 共享内存（Shared Memory）
   - 最快的IPC方式
   - 多个进程映射同一块物理内存
   - 需要配合信号量同步

4. 信号量（Semaphore）
   - 用于进程同步
   - 控制对共享资源的访问

5. 信号（Signal）
   - 异步通知机制
   - 如SIGTERM、SIGKILL、SIGHUP

6. Socket
   - 可用于不同主机间通信
   - 也可用于本机进程间（Unix Domain Socket）

7. 文件
   - 通过读写同一文件通信
   - 简单但效率低
```

**实战命令**：

```bash
# 查看IPC资源
ipcs -a

# 查看消息队列
ipcs -q

# 查看共享内存
ipcs -m

# 查看信号量
ipcs -s

# 删除IPC资源
ipcrm -m <shmid>
ipcrm -q <msgid>
ipcrm -s <semid>
```

---

# 二、内存管理

## 2.1 虚拟内存是什么？

**标准答案**：

```
虚拟内存（Virtual Memory）：
- 操作系统提供的内存抽象
- 每个进程拥有独立的虚拟地址空间
- 虚拟地址通过页表映射到物理地址

核心组件：
1. 虚拟地址空间：进程看到的内存
2. 页表（Page Table）：虚拟→物理地址映射
3. MMU：硬件地址转换单元
4. 页面（Page）：内存管理的基本单位（通常4KB）

优点：
1. 进程隔离：每个进程独立地址空间
2. 内存保护：访问越界会触发段错误
3. 内存共享：不同进程可映射同一物理页
4. 按需分配：只在访问时分配物理内存
5. 支持Swap：物理内存不足时换出到磁盘
```

**虚拟地址空间布局（64位Linux）**：

```
高地址
+------------------+
| 内核空间         |  (用户不可访问)
+------------------+  0xFFFF...
|       ↓          |
| 栈（Stack）      |  向下增长
+------------------+
|                  |
| 未使用           |
|                  |
+------------------+
| 内存映射区       |  mmap, 共享库
+------------------+
|       ↑          |
| 堆（Heap）       |  向上增长
+------------------+
| BSS段            |  未初始化全局变量
+------------------+
| 数据段           |  已初始化全局变量
+------------------+
| 代码段           |  只读
+------------------+  0x0000...
低地址
```

**实战命令**：

```bash
# 查看进程内存映射
cat /proc/<PID>/maps
pmap <PID>

# 查看内存统计
cat /proc/meminfo

# 查看进程内存使用
cat /proc/<PID>/status | grep -E "VmSize|VmRSS|VmSwap"
```

---

## 2.2 OOM Killer的工作原理？

**标准答案**：

```
OOM Killer（Out Of Memory Killer）：
- 当系统内存严重不足时，内核触发的保护机制
- 选择并杀死某些进程以释放内存
- 防止系统完全卡死

触发条件：
1. 物理内存和Swap都耗尽
2. 无法回收更多内存
3. 无法满足内存分配请求

选择牺牲进程的算法：
- 每个进程有一个oom_score（0-1000）
- oom_score越高，越可能被杀
- 计算因素：
  - 进程及子进程的内存使用量
  - 进程运行时间（越短分数越高）
  - 进程优先级
  - 是否是root进程

可以通过oom_score_adj调整：
- 范围：-1000 到 1000
- -1000：永不被OOM杀死
- 0：默认
- 1000：优先被杀
```

**查看和调整OOM分数**：

```bash
# 查看进程的OOM分数
cat /proc/<PID>/oom_score

# 查看OOM调整值
cat /proc/<PID>/oom_score_adj

# 设置OOM调整值（保护关键进程）
echo -500 > /proc/<PID>/oom_score_adj

# 永不被OOM杀死（危险！）
echo -1000 > /proc/<PID>/oom_score_adj

# 查看OOM日志
dmesg | grep -i oom
journalctl -k | grep -i oom
```

**OOM发生时的日志**：

```
[  123.456789] Out of memory: Kill process 12345 (java) score 850 or sacrifice child
[  123.456790] Killed process 12345 (java) total-vm:8192000kB, anon-rss:4096000kB, file-rss:0kB
```

---

## 2.3 如何排查内存泄漏？

**标准答案**：

```bash
# 1. 确认内存持续增长
# 监控进程RSS变化
watch -n 5 'ps -o pid,rss,command -p <PID>'

# 或使用pidstat
pidstat -r -p <PID> 5

# 2. 查看进程内存详情
cat /proc/<PID>/status | grep -E "VmSize|VmRSS|VmData|VmSwap"
# VmRSS持续增长是泄漏的信号

# 3. 使用smaps查看内存分布
cat /proc/<PID>/smaps | grep -E "Size|Rss|Pss" | head -30

# 4. 工具排查
# Java
jmap -heap <PID>
jmap -histo <PID> | head -20
jcmd <PID> GC.heap_info

# Python
# 使用tracemalloc模块

# C/C++
# valgrind --leak-check=full ./program

# Go
# pprof heap profile
```

**内存泄漏的常见原因**：

```
1. 申请内存未释放（C/C++）
2. 对象引用未清理（Java/Python）
3. 连接/文件句柄未关闭
4. 缓存无限增长
5. 线程未正确销毁
6. 事件监听器未移除
```

---

## 2.4 free命令的输出如何解读？

**标准答案**：

```bash
$ free -h
              total        used        free      shared  buff/cache   available
Mem:           15Gi       8.0Gi       1.0Gi       500Mi        6.0Gi       6.5Gi
Swap:          4.0Gi       500Mi       3.5Gi

各列含义：
- total: 总物理内存
- used: 已使用内存
- free: 完全空闲的内存
- shared: tmpfs等共享内存
- buff/cache: 缓冲区和缓存
- available: 可用于新程序的内存（重要！）

关键理解：
1. free很小是正常的（Linux会尽量利用内存做缓存）
2. available才是真正可用的内存
3. available = free + 可回收的buff/cache

判断内存是否紧张：
- 看available，而不是free
- 如果available很小且Swap使用高，则内存紧张
```

---

## 2.5 Buffer和Cache的区别？

**标准答案**：

```
Buffer（缓冲区）：
- 用于块设备的写缓冲
- 数据写入磁盘前的暂存区
- 减少磁盘写入次数

Cache（缓存）：
- 用于文件数据的读缓存
- 加速文件访问
- 包括Page Cache和Dentry Cache

现代Linux中两者界限模糊：
- Buffer主要用于元数据（目录、inode等）
- Cache用于文件数据

查看详情：
cat /proc/meminfo | grep -E "^Buffers|^Cached|^SwapCached"

手动释放Cache（生产环境慎用）：
sync  # 先同步
echo 1 > /proc/sys/vm/drop_caches  # 释放PageCache
echo 2 > /proc/sys/vm/drop_caches  # 释放dentries和inodes
echo 3 > /proc/sys/vm/drop_caches  # 释放所有
```

---

## 2.6 什么是内存映射（mmap）？

**标准答案**：

```
mmap（Memory Mapping）：
- 将文件或设备映射到进程地址空间
- 通过内存操作来读写文件
- 比read/write更高效（减少数据拷贝）

应用场景：
1. 大文件处理
2. 进程间共享内存
3. 加载动态库
4. 数据库文件访问

优点：
- 减少系统调用
- 减少内存拷贝
- 支持按需加载
- 进程间共享

示例：
# 查看进程的内存映射
cat /proc/<PID>/maps
```

---

# 三、文件系统

## 3.1 inode是什么？

**标准答案**：

```
inode（Index Node）：
- 文件系统中存储文件元信息的数据结构
- 每个文件/目录都有一个唯一的inode
- inode不包含文件名！

inode包含的信息：
- 文件类型（普通文件、目录、链接等）
- 权限（rwx）
- 所有者（UID、GID）
- 大小
- 时间戳（atime、mtime、ctime）
- 链接计数
- 数据块指针

文件名存储在哪？
- 文件名存储在目录文件中
- 目录是一个映射表：文件名 → inode号
```

**实战命令**：

```bash
# 查看文件的inode号
ls -i file.txt
stat file.txt

# 查看inode使用情况
df -i

# 查看文件系统inode总数
tune2fs -l /dev/sda1 | grep -i inode

# 根据inode号查找文件
find / -inum 12345678
```

**inode耗尽问题**：

```bash
# 症状：df -h显示有空间，但无法创建文件
# 报错：No space left on device

# 排查
df -i
# 如果IUse%接近100%，说明inode耗尽

# 找出小文件多的目录
find / -xdev -type d | while read dir; do
    count=$(ls -a "$dir" 2>/dev/null | wc -l)
    echo "$count $dir"
done | sort -rn | head -20
```

---

## 3.2 硬链接和软链接的区别？

**标准答案**：

```
硬链接（Hard Link）：
- 直接指向inode
- 多个文件名指向同一个inode
- 删除一个链接，文件仍存在（直到链接计数为0）
- 不能跨文件系统
- 不能链接目录（防止循环）
- 文件大小显示相同

软链接（Symbolic Link / Soft Link）：
- 指向文件路径（另一个文件名）
- 类似Windows快捷方式
- 可以跨文件系统
- 可以链接目录
- 原文件删除后，软链接失效（悬空链接）
- 有自己的inode

关键区别：
| 特性 | 硬链接 | 软链接 |
|------|--------|--------|
| 指向 | inode | 路径名 |
| 跨文件系统 | 否 | 是 |
| 链接目录 | 否 | 是 |
| 原文件删除 | 仍可访问 | 失效 |
| inode | 相同 | 不同 |
```

**实战命令**：

```bash
# 创建硬链接
ln original.txt hardlink.txt

# 创建软链接
ln -s original.txt softlink.txt

# 查看区别
ls -li original.txt hardlink.txt softlink.txt
# 硬链接inode相同，软链接不同

# 查看链接计数
stat original.txt | grep Links

# 找出所有软链接
find /path -type l

# 找出悬空链接
find /path -xtype l
```

---

## 3.3 磁盘满了如何排查？

**标准答案**：

```bash
# 1. 确认磁盘使用情况
df -h

# 2. 找出大目录
du -sh /* 2>/dev/null | sort -hr | head -10
du -sh /var/* 2>/dev/null | sort -hr | head -10

# 3. 找出大文件
find / -type f -size +1G 2>/dev/null
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -20

# 4. 常见占用空间的位置
du -sh /var/log
du -sh /tmp
du -sh /home
du -sh /var/lib/docker  # Docker

# 5. 检查已删除但未释放的文件（df和du不一致时）
lsof +L1
# 这些文件已删除但仍被进程占用

# 处理方法：
# 重启占用进程，或
# truncate清空文件（不删除）
```

**df和du结果不一致的原因**：

```
1. 已删除但仍被进程打开的文件
   - lsof +L1 查看
   - 重启进程释放

2. 挂载点覆盖
   - 目录下有文件后被挂载覆盖
   - umount后可见

3. 稀疏文件
   - 逻辑大小和实际占用不同
   - du显示实际占用
```

---

## 3.4 什么是文件描述符？

**标准答案**：

```
文件描述符（File Descriptor, FD）：
- 非负整数，标识打开的文件
- 每个进程有自己的文件描述符表
- 是内核文件表的索引

标准文件描述符：
- 0: stdin（标准输入）
- 1: stdout（标准输出）
- 2: stderr（标准错误）

文件描述符限制：
- 每个进程有最大FD数限制
- 系统也有全局限制
```

**查看和调整**：

```bash
# 查看进程打开的文件
ls -l /proc/<PID>/fd
lsof -p <PID>

# 查看打开文件数
ls /proc/<PID>/fd | wc -l

# 查看限制
ulimit -n  # 当前shell
cat /proc/<PID>/limits | grep "open files"

# 临时调整
ulimit -n 65535

# 永久调整
# /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535

# 系统级限制
cat /proc/sys/fs/file-nr  # 已分配/未使用/最大
cat /proc/sys/fs/file-max # 最大值
```

---

## 3.5 atime、mtime、ctime的区别？

**标准答案**：

```
三个时间戳：
- atime (Access Time): 最后访问时间（读取）
- mtime (Modify Time): 最后修改时间（内容变化）
- ctime (Change Time): 最后状态变化时间（元数据变化）

触发条件：
| 操作 | atime | mtime | ctime |
|------|-------|-------|-------|
| 读取文件 | ✓ | | |
| 修改内容 | | ✓ | ✓ |
| 修改权限 | | | ✓ |
| 重命名 | | | ✓ |
| 创建硬链接 | | | ✓ |

查看：
stat file.txt
ls -l file.txt   # 默认显示mtime
ls -lu file.txt  # 显示atime
ls -lc file.txt  # 显示ctime

注意：现代Linux默认使用relatime挂载选项
atime只在mtime/ctime更新时才更新，减少IO
```

---

# 四、信号处理

## 4.1 常用信号有哪些？

**标准答案**：

```
| 信号 | 编号 | 默认行为 | 说明 |
|------|------|----------|------|
| SIGHUP | 1 | 终止 | 终端挂断，常用于重载配置 |
| SIGINT | 2 | 终止 | Ctrl+C中断 |
| SIGQUIT | 3 | 终止+core | Ctrl+\退出 |
| SIGKILL | 9 | 终止 | 强制杀死，不可捕获 |
| SIGTERM | 15 | 终止 | 优雅终止，可捕获 |
| SIGSTOP | 19 | 暂停 | 暂停进程，不可捕获 |
| SIGCONT | 18 | 继续 | 恢复暂停的进程 |
| SIGCHLD | 17 | 忽略 | 子进程状态变化 |
| SIGUSR1 | 10 | 终止 | 用户自定义1 |
| SIGUSR2 | 12 | 终止 | 用户自定义2 |

不可捕获的信号：
- SIGKILL (9): 强制终止
- SIGSTOP (19): 强制暂停
```

**实战命令**：

```bash
# 发送信号
kill -15 <PID>  # SIGTERM
kill -9 <PID>   # SIGKILL
kill -HUP <PID> # SIGHUP，重载配置

# 查看所有信号
kill -l

# 向进程组发送信号
kill -TERM -<PGID>

# 按名称杀进程
pkill -TERM nginx
killall -TERM nginx
```

---

## 4.2 kill -9 和 kill -15 的区别？

**标准答案**：

```
kill -15 (SIGTERM)：
- 请求进程优雅退出
- 进程可以捕获并处理
- 进程可以清理资源、保存状态
- 推荐首先使用

kill -9 (SIGKILL)：
- 强制终止进程
- 进程无法捕获或忽略
- 立即终止，无清理机会
- 可能导致数据丢失
- 最后手段

最佳实践：
1. 先发SIGTERM
2. 等待几秒
3. 如果进程未退出，再发SIGKILL

# 示例脚本
kill -15 $PID
sleep 5
if kill -0 $PID 2>/dev/null; then
    kill -9 $PID
fi
```

---

# 五、系统启动

## 5.1 Linux启动流程是什么？

**标准答案**：

```
1. BIOS/UEFI
   - 硬件自检（POST）
   - 加载引导程序

2. Bootloader (GRUB)
   - 加载内核和initramfs
   - 传递启动参数

3. 内核初始化
   - 解压内核
   - 初始化硬件
   - 挂载initramfs作为临时根文件系统
   - 启动init进程

4. initramfs
   - 加载必要驱动
   - 挂载真正的根文件系统
   - 切换根目录

5. init进程 (systemd)
   - PID=1
   - 启动系统服务
   - 启动登录界面

systemd启动顺序：
default.target → 依赖的target → 各服务unit
```

---

## 5.2 如何查看开机启动项？

**标准答案**：

```bash
# systemd服务
systemctl list-unit-files --type=service | grep enabled

# 查看启动目标
systemctl get-default

# 查看启动链
systemd-analyze critical-chain

# 查看启动时间
systemd-analyze
systemd-analyze blame | head -20

# 传统init.d（兼容）
ls /etc/init.d/

# crontab @reboot
crontab -l | grep @reboot
```

---

## 总结

### 高频考点速查

| 主题 | 核心命令 | 关键概念 |
|------|----------|----------|
| 进程线程 | `ps`, `top -H` | 资源分配 vs 调度单位 |
| 僵尸进程 | `ps aux \| grep Z` | wait()回收 |
| 系统负载 | `uptime`, `top` | Load = R + D状态进程 |
| 虚拟内存 | `pmap`, `/proc/PID/maps` | 页表映射 |
| OOM | `dmesg \| grep oom` | oom_score选择牺牲者 |
| 内存泄漏 | `pidstat -r`, `jmap` | RSS持续增长 |
| inode | `df -i`, `stat` | 文件元信息 |
| 硬/软链接 | `ln`, `ln -s` | inode vs 路径名 |
| 磁盘排查 | `df`, `du`, `lsof +L1` | 已删除未释放文件 |
| 信号 | `kill -15`, `kill -9` | SIGTERM vs SIGKILL |

### 面试回答技巧

1. **先说概念**：一句话解释是什么
2. **再说原理**：为什么会这样
3. **给出命令**：实际怎么查看/处理
4. **举例说明**：结合实际场景

### 常见追问

- "能详细说说吗？" → 深入原理
- "遇到过什么问题？" → 讲实际案例
- "如何排查？" → 给出具体步骤
- "有什么坑？" → 分享踩坑经验
