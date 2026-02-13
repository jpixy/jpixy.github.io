+++
title = "Memory Alignment and Struct Packing"
date = 2026-01-30
weight = 15000
description = "Deep dive into memory alignment, struct padding, and packing techniques in C"
[taxonomies]
tags = ["C", "Memory", "Alignment", "Performance"]
+++

## Why Memory Alignment Matters

Memory alignment is one of the most important low-level concepts in C programming. Proper alignment can significantly impact performance and even correctness on some architectures.

**Memory Access Pattern**:

| 类型 | Aligned Access | Unaligned Access |
|------|----------------|------------------|
| 访问模式 | `[  32-bit word  ]` | `[  32  ][bit ]` |
| 周期数 | 1 cycle | 2+ cycles |
| 读取次数 | Single read | Two reads required |

---

## Natural Alignment Rules

Every data type has a natural alignment requirement:

| Type | Size | Alignment | Notes |
|------|------|-----------|-------|
| char | 1 | 1 | No alignment required |
| short | 2 | 2 | 2-byte boundary |
| int | 4 | 4 | 4-byte boundary |
| long | 4/8 | 4/8 | Platform dependent |
| float | 4 | 4 | 4-byte boundary |
| double | 8 | 8 | 8-byte boundary |
| pointer | 4/8 | 4/8 | Platform dependent |

**Rule**: A variable's address should be divisible by its alignment.

---

## Struct Padding Examples

### Example 1: Naive Struct

```c
struct BadLayout {
    char a;      // 1 byte
    // 3 bytes padding
    int b;       // 4 bytes
    char c;      // 1 byte
    // 3 bytes padding
};
// Total: 12 bytes (not 6!)
```

### Example 2: Optimized Struct

```c
struct GoodLayout {
    int b;       // 4 bytes
    char a;      // 1 byte
    char c;      // 1 byte
    // 2 bytes padding
};
// Total: 8 bytes
```

### Example 3: With Double

```c
struct WithDouble {
    char a;      // 1 byte
    // 7 bytes padding (double needs 8-byte alignment)
    double b;    // 8 bytes
    char c;      // 1 byte
    // 7 bytes padding
};
// Total: 24 bytes

struct WithDoubleOptimized {
    double b;    // 8 bytes
    char a;      // 1 byte
    char c;      // 1 byte
    // 6 bytes padding
};
// Total: 16 bytes
```

---

## Calculating Struct Size

```c
#include <stddef.h>

// offsetof macro - get member offset
size_t offset = offsetof(struct MyStruct, member);

// Example
struct Example {
    char a;
    int b;
    char c;
};

printf("offsetof(a) = %zu\n", offsetof(struct Example, a)); // 0
printf("offsetof(b) = %zu\n", offsetof(struct Example, b)); // 4
printf("offsetof(c) = %zu\n", offsetof(struct Example, c)); // 8
printf("sizeof = %zu\n", sizeof(struct Example));           // 12
```

---

## Controlling Alignment

### GCC/Clang Attributes

```c
// Force alignment
struct __attribute__((aligned(64))) CacheLine {
    int data[16];
};

// Pack struct (no padding)
struct __attribute__((packed)) Packed {
    char a;
    int b;
    char c;
};
// sizeof = 6 (but unaligned access!)

// Align specific member
struct Mixed {
    char a;
    int b __attribute__((aligned(16)));
};
```

### Pragma Pack

```c
#pragma pack(push, 1)  // Set alignment to 1 byte
struct NetworkPacket {
    uint8_t type;
    uint32_t length;
    uint16_t checksum;
};
#pragma pack(pop)      // Restore default

// sizeof = 7 (no padding)
```

### C11 _Alignas

```c
#include <stdalign.h>

_Alignas(64) int cache_aligned_array[16];

struct AlignedStruct {
    _Alignas(16) float vector[4];
    int other_data;
};
```

---

## Alignment and Performance

### Cache Line Alignment

```c
#define CACHE_LINE_SIZE 64

struct __attribute__((aligned(CACHE_LINE_SIZE))) PerThreadData {
    int counter;
    char padding[CACHE_LINE_SIZE - sizeof(int)];
};

// Prevents false sharing between threads
struct PerThreadData thread_data[NUM_THREADS];
```

### SIMD Alignment

```c
// SSE requires 16-byte alignment
// AVX requires 32-byte alignment

float __attribute__((aligned(32))) avx_data[8];

// Or use aligned_alloc (C11)
float *data = aligned_alloc(32, 8 * sizeof(float));
```

---

## Custom Aligned Allocation

```c
void *aligned_malloc(size_t size, size_t alignment) {
    // alignment must be power of 2
    void *p1;
    void **p2;
    size_t offset = alignment - 1 + sizeof(void*);
    
    p1 = malloc(size + offset);
    if (p1 == NULL) return NULL;
    
    // Calculate aligned address
    p2 = (void**)(((size_t)p1 + offset) & ~(alignment - 1));
    // Store original pointer
    p2[-1] = p1;
    
    return p2;
}

void aligned_free(void *p) {
    if (p) {
        free(((void**)p)[-1]);
    }
}

// Usage
int *data = aligned_malloc(100 * sizeof(int), 64);
aligned_free(data);
```

---

## Detecting Alignment Issues

### Runtime Check

```c
int is_aligned(void *ptr, size_t alignment) {
    return ((uintptr_t)ptr % alignment) == 0;
}

void *ptr = get_pointer();
if (!is_aligned(ptr, 16)) {
    // Handle unaligned pointer
}
```

### Compile-Time Check

```c
#define STATIC_ASSERT_ALIGNED(type, align) \
    _Static_assert(_Alignof(type) >= align, #type " not aligned to " #align)

STATIC_ASSERT_ALIGNED(struct CacheLine, 64);
```

---

## Network Protocol Structures

```c
// Network packet - must be packed for correct byte layout
#pragma pack(push, 1)
struct IPHeader {
    uint8_t  version_ihl;
    uint8_t  tos;
    uint16_t total_length;
    uint16_t identification;
    uint16_t flags_fragment;
    uint8_t  ttl;
    uint8_t  protocol;
    uint16_t checksum;
    uint32_t src_addr;
    uint32_t dst_addr;
};
#pragma pack(pop)

// Always use network byte order functions
header.total_length = htons(packet_size);
header.src_addr = htonl(src_ip);
```

---

## Common Pitfalls

### 1. Pointer Casting Issues

```c
char buffer[100];
int *ip = (int*)(buffer + 1);  // Unaligned!
*ip = 42;  // May crash on some architectures

// Safe version
int value = 42;
memcpy(buffer + 1, &value, sizeof(int));
```

### 2. Struct Size Assumptions

```c
// WRONG: Assuming contiguous layout
struct Data { char a; int b; };
struct Data arr[10];
char *p = (char*)arr;
// p + 5 does NOT point to arr[0].b

// CORRECT: Use offsetof
char *b_ptr = (char*)arr + offsetof(struct Data, b);
```

### 3. Packed Struct Performance

```c
#pragma pack(push, 1)
struct Packed { char a; int b; };
#pragma pack(pop)

struct Packed p;
p.b = 42;  // May generate slow unaligned access

// Better: Copy to aligned variable for processing
int aligned_b;
memcpy(&aligned_b, &p.b, sizeof(int));
```

---

## Best Practices

1. **Order struct members by size** (largest first)
2. **Use packed only for serialization** (network, file I/O)
3. **Align for cache lines** in multithreaded code
4. **Use SIMD alignment** for vectorized operations
5. **Verify assumptions** with sizeof and offsetof
6. **Use C11 aligned_alloc** when available

---

## Related Topics

- [06. Pointers and Memory Model](@/articles/c/c-06-指针基础与内存模型.md)
- [08. Structs and Unions](@/articles/c/c-08-结构体与联合体.md)
- [16. Volatile and Memory Barriers (HFT)](@/articles/c/c-16-Volatile-Memory-Barriers.md)


---

## 相关文章

- [上一篇：IO Multiplexing (select/poll/epoll)](@/articles/c/c-14-IO多路复用详解.md)
- [下一篇：Volatile and Memory Barriers (HFT)](@/articles/c/c-16-Volatile-Memory-Barriers.md)
