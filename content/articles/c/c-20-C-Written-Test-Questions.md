+++
title = "20. C Written Test Questions"
date = 2026-01-30
weight = 20000
description = "C语言笔试真题：选择题、填空题、编程题、调试题"
[taxonomies]
tags = ["C", "笔试", "真题"]
+++

## 选择题

### 题目1
以下代码的输出是？

```c
int a = 5, b = 7;
printf("%d\n", a+++b);
```

- A) 11
- B) 12
- C) 13
- D) 编译错误

**答案**: B

**解析**: `a+++b` 解析为 `(a++) + b`，先取a的值5，加上b的值7，结果12。a之后变成6。

---

### 题目2
以下声明中，p是？

```c
int (*p)[10];
```

- A) 10个int指针的数组
- B) 指向10个int数组的指针
- C) 指向int的指针
- D) 指向10个指针的数组

**答案**: B

---

### 题目3
sizeof运算符，在64位系统下输出？

```c
char *p = "hello";
printf("%zu %zu\n", sizeof(p), sizeof(*p));
```

- A) 5 1
- B) 6 1
- C) 8 1
- D) 8 8

**答案**: C

**解析**: p是指针(8字节)，*p是char(1字节)

---

### 题目4
以下程序的输出？

```c
int arr[] = {1, 2, 3, 4, 5};
int *p = arr + 2;
printf("%d\n", p[-1]);
```

- A) 1
- B) 2
- C) 3
- D) 编译错误

**答案**: B

**解析**: `p[-1]` 等价于 `*(p-1)`，即 arr[1] = 2

---

### 题目5
关于static变量，错误的是？

- A) static局部变量在函数调用间保持值
- B) static全局变量只在当前文件可见
- C) static变量默认初始化为0
- D) static变量存储在栈上

**答案**: D

**解析**: static变量存储在数据段(BSS或Data)，不是栈

---

### 题目6
以下代码有什么问题？

```c
char *get_string(void) {
    char str[] = "hello";
    return str;
}
```

- A) 没有问题
- B) 返回局部数组的地址
- C) 字符串太短
- D) 缺少分号

**答案**: B

**解析**: str是局部数组，函数返回后栈空间释放，指针悬空

---

### 题目7
下列表达式的值？

```c
int x = 10;
x = x++ + ++x;
```

- A) 21
- B) 22
- C) 23
- D) 未定义行为

**答案**: D

**解析**: 在同一表达式中多次修改同一变量是未定义行为

---

### 题目8
关于malloc和calloc的区别，正确的是？

- A) calloc分配的内存会被清零
- B) malloc比calloc更快
- C) calloc接受两个参数
- D) 以上都正确

**答案**: D

---

### 题目9
结构体对齐，以下结构体的大小？

```c
struct S {
    char a;
    int b;
    char c;
};
```

(假设int为4字节，默认对齐)

- A) 6
- B) 8
- C) 9
- D) 12

**答案**: D

**解析**: 1 + 3(padding) + 4 + 1 + 3(padding) = 12

---

### 题目10
以下代码输出？

```c
#define DOUBLE(x) x + x
int a = 3 * DOUBLE(5);
printf("%d\n", a);
```

- A) 30
- B) 20
- C) 10
- D) 15

**答案**: B

**解析**: 展开为 `3 * 5 + 5 = 15 + 5 = 20`

---

## 填空题

### 题目11
写出以下代码的输出：

```c
int a[] = {1, 2, 3, 4, 5};
printf("%d\n", *a + 3);
printf("%d\n", *(a + 3));
```

**答案**: 
- 4 (取a[0]的值1，加3)
- 4 (取a[3]的值)

---

### 题目12
填写代码，实现字符串长度计算：

```c
size_t strlen(const char *s) {
    const char *p = s;
    while (______) p++;
    return p - s;
}
```

**答案**: `*p` 或 `*p != '\0'`

---

### 题目13
填写代码，实现两数交换：

```c
void swap(int *a, int *b) {
    int temp = *a;
    ______ = *b;
    *b = ______;
}
```

**答案**: `*a`, `temp`

---

### 题目14
以下代码编译后，变量存储在哪个区域？

```c
int global;                  // ______
static int file_static;      // ______
const char *str = "hello";   // str在______，"hello"在______

void func(void) {
    int local;               // ______
    static int func_static;  // ______
    char *heap = malloc(10); // heap在______，指向的内存在______
}
```

**答案**:
- global: BSS
- file_static: BSS (未初始化) 或 Data (初始化)
- str: Data，"hello": Text/RODATA
- local: Stack
- func_static: BSS/Data
- heap: Stack，指向: Heap

---

### 题目15
补充代码，实现链表节点插入：

```c
struct Node {
    int data;
    struct Node *next;
};

void insert_after(struct Node *node, int data) {
    struct Node *new_node = malloc(sizeof(struct Node));
    new_node->data = data;
    new_node->next = ______;
    ______ = new_node;
}
```

**答案**: `node->next`, `node->next`

---

## 编程题

### 题目16: 数组去重

给定有序数组，原地删除重复元素，返回新长度。

```c
int removeDuplicates(int *nums, int n) {
    if (n == 0) return 0;
    
    int j = 0;
    for (int i = 1; i < n; i++) {
        if (nums[i] != nums[j]) {
            nums[++j] = nums[i];
        }
    }
    return j + 1;
}
```

---

### 题目17: 反转链表

```c
struct Node *reverseList(struct Node *head) {
    struct Node *prev = NULL, *curr = head;
    while (curr) {
        struct Node *next = curr->next;
        curr->next = prev;
        prev = curr;
        curr = next;
    }
    return prev;
}
```

---

### 题目18: 判断回文字符串

```c
int isPalindrome(const char *s) {
    int left = 0, right = strlen(s) - 1;
    while (left < right) {
        if (s[left++] != s[right--]) return 0;
    }
    return 1;
}
```

---

### 题目19: 合并两个有序数组

```c
void merge(int *a, int m, int *b, int n, int *result) {
    int i = 0, j = 0, k = 0;
    while (i < m && j < n) {
        result[k++] = (a[i] < b[j]) ? a[i++] : b[j++];
    }
    while (i < m) result[k++] = a[i++];
    while (j < n) result[k++] = b[j++];
}
```

---

### 题目20: 二分查找

```c
int binarySearch(int *arr, int n, int target) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
```

---

## 调试题

### 题目21: 找出bug

```c
char *strdup(const char *s) {
    char *p = malloc(strlen(s));  // BUG!
    strcpy(p, s);
    return p;
}
```

**答案**: 应该是 `malloc(strlen(s) + 1)`，需要为 '\0' 分配空间

---

### 题目22: 找出bug

```c
void copy_string(char *dest, const char *src, size_t n) {
    for (int i = 0; i < n; i++) {  // BUG!
        dest[i] = src[i];
    }
}
```

**答案**: 
1. `i` 应该是 `size_t` 类型，避免有符号/无符号比较问题
2. 没有检查 src 是否提前结束
3. 没有添加终止符 '\0'

---

### 题目23: 找出bug

```c
int *create_array(int n) {
    int arr[n];
    for (int i = 0; i < n; i++) arr[i] = i;
    return arr;  // BUG!
}
```

**答案**: 返回局部数组的地址，函数返回后栈空间无效

---

### 题目24: 内存泄漏

```c
void process_file(const char *filename) {
    FILE *f = fopen(filename, "r");
    if (f == NULL) return;
    
    char *buffer = malloc(1024);
    if (buffer == NULL) return;  // BUG!
    
    // 处理...
    
    free(buffer);
    fclose(f);
}
```

**答案**: `buffer == NULL` 时返回，但 `f` 没有关闭，造成文件描述符泄漏

**修复**:
```c
if (buffer == NULL) {
    fclose(f);
    return;
}
```

---

### 题目25: 未定义行为

```c
void func(void) {
    int *p = malloc(sizeof(int));
    free(p);
    *p = 10;  // BUG!
}
```

**答案**: 使用已释放的内存，未定义行为

---

## 综合题

### 题目26: 实现atoi

```c
int my_atoi(const char *s) {
    // 跳过空白
    while (*s == ' ') s++;
    
    // 符号
    int sign = 1;
    if (*s == '-') { sign = -1; s++; }
    else if (*s == '+') s++;
    
    // 数字
    long result = 0;
    while (*s >= '0' && *s <= '9') {
        result = result * 10 + (*s - '0');
        // 溢出检查
        if (result * sign > INT_MAX) return INT_MAX;
        if (result * sign < INT_MIN) return INT_MIN;
        s++;
    }
    
    return (int)(result * sign);
}
```

---

### 题目27: 快速排序

```c
void quick_sort(int *arr, int low, int high) {
    if (low >= high) return;
    
    int pivot = arr[high];
    int i = low - 1;
    
    for (int j = low; j < high; j++) {
        if (arr[j] < pivot) {
            i++;
            int temp = arr[i];
            arr[i] = arr[j];
            arr[j] = temp;
        }
    }
    
    int temp = arr[i + 1];
    arr[i + 1] = arr[high];
    arr[high] = temp;
    
    int pi = i + 1;
    quick_sort(arr, low, pi - 1);
    quick_sort(arr, pi + 1, high);
}
```

---

### 题目28: LRU Cache (简化版)

```c
#define CACHE_SIZE 100

struct CacheEntry {
    int key;
    int value;
    int timestamp;
};

struct LRUCache {
    struct CacheEntry entries[CACHE_SIZE];
    int count;
    int time;
};

int cache_get(struct LRUCache *cache, int key) {
    for (int i = 0; i < cache->count; i++) {
        if (cache->entries[i].key == key) {
            cache->entries[i].timestamp = ++cache->time;
            return cache->entries[i].value;
        }
    }
    return -1;  // not found
}

void cache_put(struct LRUCache *cache, int key, int value) {
    // 查找现有
    for (int i = 0; i < cache->count; i++) {
        if (cache->entries[i].key == key) {
            cache->entries[i].value = value;
            cache->entries[i].timestamp = ++cache->time;
            return;
        }
    }
    
    // 需要驱逐
    if (cache->count == CACHE_SIZE) {
        int lru_idx = 0;
        for (int i = 1; i < CACHE_SIZE; i++) {
            if (cache->entries[i].timestamp < cache->entries[lru_idx].timestamp) {
                lru_idx = i;
            }
        }
        cache->entries[lru_idx].key = key;
        cache->entries[lru_idx].value = value;
        cache->entries[lru_idx].timestamp = ++cache->time;
        return;
    }
    
    // 添加新条目
    cache->entries[cache->count].key = key;
    cache->entries[cache->count].value = value;
    cache->entries[cache->count].timestamp = ++cache->time;
    cache->count++;
}
```

---

## 进阶选择题

### 题目29
以下代码在小端机器上输出什么？

```c
union {
    int i;
    char c[4];
} u;
u.i = 0x12345678;
printf("%02x\n", u.c[0]);
```

- A) 12
- B) 78
- C) 56
- D) 34

**答案**: B

**解析**: 小端存储低字节在低地址，0x78 在 c[0] 位置。

---

### 题目30
关于 volatile 关键字，正确的是？

- A) volatile 变量可以被编译器优化
- B) volatile 保证原子性
- C) volatile 防止编译器优化，强制每次从内存读取
- D) volatile 等同于 const

**答案**: C

**解析**: volatile 告诉编译器变量可能被外部修改（硬件、中断、其他线程），不能缓存到寄存器。

---

### 题目31
以下代码的输出？

```c
int main(void) {
    int a[5] = {1, 2, 3, 4, 5};
    int *p = (int*)(&a + 1);
    printf("%d\n", *(p - 1));
    return 0;
}
```

- A) 1
- B) 2
- C) 4
- D) 5

**答案**: D

**解析**: `&a` 是整个数组的地址，`&a + 1` 跳过整个数组(20字节)，`p-1` 指向 a[4]。

---

### 题目32
以下结构体大小是多少？(64位系统，默认对齐)

```c
struct S {
    char a;
    double b;
    char c;
};
```

- A) 10
- B) 16
- C) 17
- D) 24

**答案**: D

**解析**: char(1) + padding(7) + double(8) + char(1) + padding(7) = 24

---

### 题目33
以下代码有什么问题？

```c
const int n = 10;
int arr[n];
```

- A) 没有问题
- B) C89 不支持变长数组
- C) const 变量不是编译时常量
- D) B 和 C 都对

**答案**: D

**解析**: C 语言中 const 只是只读变量，不是编译时常量。C89 不支持 VLA，C99 支持但 n 仍不是常量表达式。

---

### 题目34
以下表达式的值？

```c
int x = 3, y = 4;
int z = x---y;  // z = ?
```

- A) -1
- B) 0
- C) 1
- D) 编译错误

**答案**: A

**解析**: 解析为 `(x--) - y`，即 3 - 4 = -1，之后 x = 2。

---

### 题目35
以下代码输出什么？

```c
char *s = "hello";
char *t = "hello";
printf("%d\n", s == t);
```

- A) 0
- B) 1
- C) 未定义
- D) 编译错误

**答案**: B (通常情况)

**解析**: 大多数编译器会合并相同的字符串字面量（字符串池化），所以 s 和 t 指向同一地址。但标准不保证这一行为。

---

## 进阶编程题

### 题目36: 实现 memmove

```c
void *my_memmove(void *dest, const void *src, size_t n) {
    char *d = (char *)dest;
    const char *s = (const char *)src;
    
    if (d < s) {
        // 正向拷贝
        while (n--) {
            *d++ = *s++;
        }
    } else {
        // 反向拷贝 (处理重叠)
        d += n;
        s += n;
        while (n--) {
            *--d = *--s;
        }
    }
    return dest;
}
```

**考点**: 处理内存重叠的情况，这是 memmove 和 memcpy 的关键区别。

---

### 题目37: 实现 itoa (整数转字符串)

```c
char *my_itoa(int value, char *str, int base) {
    char *p = str;
    char *q = str;
    unsigned int uvalue;
    
    // 处理负数
    if (value < 0 && base == 10) {
        *p++ = '-';
        q = p;
        uvalue = (unsigned int)(-(value + 1)) + 1;  // 处理 INT_MIN
    } else {
        uvalue = (unsigned int)value;
    }
    
    // 转换
    do {
        int digit = uvalue % base;
        *p++ = (digit < 10) ? ('0' + digit) : ('a' + digit - 10);
        uvalue /= base;
    } while (uvalue);
    
    *p = '\0';
    
    // 反转
    p--;
    while (q < p) {
        char t = *q;
        *q++ = *p;
        *p-- = t;
    }
    
    return str;
}
```

**考点**: 处理负数、INT_MIN 边界、进制转换、字符串反转。

---

### 题目38: 实现位图 (Bitmap)

```c
#include <stdint.h>
#include <string.h>

#define BITMAP_BITS 1024

typedef struct {
    uint32_t data[BITMAP_BITS / 32];
} Bitmap;

void bitmap_init(Bitmap *bm) {
    memset(bm->data, 0, sizeof(bm->data));
}

void bitmap_set(Bitmap *bm, int pos) {
    bm->data[pos / 32] |= (1U << (pos % 32));
}

void bitmap_clear(Bitmap *bm, int pos) {
    bm->data[pos / 32] &= ~(1U << (pos % 32));
}

int bitmap_test(Bitmap *bm, int pos) {
    return (bm->data[pos / 32] >> (pos % 32)) & 1;
}

// 找到第一个为0的位
int bitmap_find_first_zero(Bitmap *bm) {
    for (int i = 0; i < BITMAP_BITS / 32; i++) {
        if (bm->data[i] != 0xFFFFFFFF) {
            uint32_t val = ~bm->data[i];
            // 找最低位的1
            int pos = __builtin_ctz(val);  // GCC内置
            return i * 32 + pos;
        }
    }
    return -1;
}
```

---

### 题目39: 环形缓冲区

```c
#define RING_SIZE 256  // 必须是2的幂

typedef struct {
    char buffer[RING_SIZE];
    volatile size_t head;  // 写位置
    volatile size_t tail;  // 读位置
} RingBuffer;

void ring_init(RingBuffer *rb) {
    rb->head = rb->tail = 0;
}

int ring_is_empty(RingBuffer *rb) {
    return rb->head == rb->tail;
}

int ring_is_full(RingBuffer *rb) {
    return ((rb->head + 1) & (RING_SIZE - 1)) == rb->tail;
}

int ring_write(RingBuffer *rb, char c) {
    if (ring_is_full(rb)) return -1;
    rb->buffer[rb->head] = c;
    rb->head = (rb->head + 1) & (RING_SIZE - 1);
    return 0;
}

int ring_read(RingBuffer *rb, char *c) {
    if (ring_is_empty(rb)) return -1;
    *c = rb->buffer[rb->tail];
    rb->tail = (rb->tail + 1) & (RING_SIZE - 1);
    return 0;
}
```

**考点**: 无锁环形缓冲区，用于生产者-消费者模式。

---

### 题目40: 判断系统大小端

```c
int is_little_endian(void) {
    // 方法1: 联合体
    union {
        uint16_t i;
        uint8_t c[2];
    } u = {0x0102};
    return u.c[0] == 0x02;
}

int is_little_endian_v2(void) {
    // 方法2: 指针
    uint32_t i = 1;
    return *((uint8_t *)&i) == 1;
}
```

---

### 题目41: 不使用 +/-/* 实现两数相加

```c
int add(int a, int b) {
    while (b != 0) {
        int carry = (unsigned)(a & b) << 1;  // 进位
        a = a ^ b;      // 无进位加法
        b = carry;
    }
    return a;
}
```

---

### 题目42: 实现简单的内存对齐分配

```c
void *aligned_malloc(size_t size, size_t alignment) {
    // alignment 必须是2的幂
    void *p1;
    void **p2;
    size_t offset = alignment - 1 + sizeof(void*);
    
    p1 = malloc(size + offset);
    if (p1 == NULL) return NULL;
    
    // 计算对齐地址
    p2 = (void**)(((size_t)p1 + offset) & ~(alignment - 1));
    // 存储原始指针
    p2[-1] = p1;
    
    return p2;
}

void aligned_free(void *p) {
    if (p) {
        free(((void**)p)[-1]);
    }
}
```

---

## 陷阱与调试题 (进阶)

### 题目43: 找出所有问题

```c
char *dangerous_function(void) {
    char buffer[100];
    sprintf(buffer, "Hello, World!");
    return buffer;
}
```

**问题**:
1. 返回局部数组地址 (悬空指针)
2. 栈上数据在函数返回后无效

**修复**: 使用 malloc 或 static。

---

### 题目44: 找出内存问题

```c
void process(void) {
    int *p = malloc(10 * sizeof(int));
    
    for (int i = 0; i <= 10; i++) {  // BUG!
        p[i] = i;
    }
    
    free(p);
    printf("%d\n", p[0]);  // BUG!
}
```

**问题**:
1. 越界写入: `i <= 10` 应该是 `i < 10`
2. Use-after-free: free 后访问 p[0]

---

### 题目45: 多线程问题

```c
int counter = 0;

void *thread_func(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        counter++;  // BUG!
    }
    return NULL;
}
```

**问题**: 非原子操作，存在竞态条件。

**修复**: 使用 `__sync_fetch_and_add(&counter, 1)` 或互斥锁。

---

## 高级概念题

### 题目46: 函数指针数组实现状态机

```c
typedef enum { STATE_INIT, STATE_RUN, STATE_STOP, STATE_COUNT } State;
typedef State (*StateHandler)(void);

State handle_init(void) { 
    printf("Init\n"); 
    return STATE_RUN; 
}

State handle_run(void) { 
    printf("Running\n"); 
    return STATE_STOP; 
}

State handle_stop(void) { 
    printf("Stopped\n"); 
    return STATE_INIT; 
}

StateHandler handlers[STATE_COUNT] = {
    handle_init, handle_run, handle_stop
};

void run_state_machine(void) {
    State current = STATE_INIT;
    for (int i = 0; i < 10; i++) {
        current = handlers[current]();
    }
}
```

---

### 题目47: 实现泛型容器 (void* 技巧)

```c
typedef struct {
    void *data;
    size_t elem_size;
    size_t count;
    size_t capacity;
} Vector;

Vector *vector_create(size_t elem_size, size_t initial_cap) {
    Vector *v = malloc(sizeof(Vector));
    v->data = malloc(elem_size * initial_cap);
    v->elem_size = elem_size;
    v->count = 0;
    v->capacity = initial_cap;
    return v;
}

void *vector_at(Vector *v, size_t index) {
    return (char*)v->data + index * v->elem_size;
}

void vector_push(Vector *v, const void *elem) {
    if (v->count == v->capacity) {
        v->capacity *= 2;
        v->data = realloc(v->data, v->elem_size * v->capacity);
    }
    memcpy((char*)v->data + v->count * v->elem_size, elem, v->elem_size);
    v->count++;
}
```

---

### 题目48: 宏实现泛型 MAX

```c
// 基本版本 (有副作用问题)
#define MAX_BASIC(a, b) ((a) > (b) ? (a) : (b))

// GCC 扩展版本 (无副作用)
#define MAX_SAFE(a, b) ({      \
    typeof(a) _a = (a);        \
    typeof(b) _b = (b);        \
    _a > _b ? _a : _b;         \
})

// C11 泛型版本
#define MAX_C11(a, b) _Generic((a) + (b), \
    int: max_int,                         \
    long: max_long,                       \
    double: max_double                    \
)((a), (b))
```

---

## 相关链接

- [C Interview Questions](@/articles/c/c-21-C-Interview-Questions.md)
- [12.纯C实现常见的数据结构](@/articles/c/c-12-纯C实现常见的数据结构.md)
- [09.动态内存管理](@/articles/c/c-09-动态内存管理.md)
- [算法专题](@/articles/algorithm/_index.md)

---

## 相关文章

- [上一篇：Cache-Friendly C Programming (HFT)](@/articles/c/c-19-Cache-Friendly-Programming.md)
- [下一篇：C Interview Questions](@/articles/c/c-21-C-Interview-Questions.md)
