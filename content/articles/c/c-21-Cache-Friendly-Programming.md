+++
title = "21. Cache-Friendly C Programming (HFT)"
date = 2026-01-30
description = "Optimizing C code for CPU cache performance in low-latency systems"
[taxonomies]
tags = ["C", "HFT", "Cache", "Performance", "Low-Latency"]
+++

## Cache Hierarchy Overview

```
CPU Cache Hierarchy:
┌──────────────────────────────────────────────────────┐
│  CPU Core                                            │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Registers (< 1 cycle)                          │ │
│  ├─────────────────────────────────────────────────┤ │
│  │  L1 Cache (32-64KB, ~4 cycles)                  │ │
│  ├─────────────────────────────────────────────────┤ │
│  │  L2 Cache (256KB-1MB, ~12 cycles)               │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  L3 Cache (shared, 8-64MB, ~40 cycles)          │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Main Memory (DDR4/DDR5, ~100-300 cycles)       │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**Key insight**: A cache miss can cost 100x more than a cache hit.

---

## Data Layout Optimization

### Array of Structs vs Struct of Arrays

```c
// Array of Structs (AoS) - Poor cache locality for single field access
struct ParticleAoS {
    float x, y, z;
    float vx, vy, vz;
    float mass;
    int id;
};
struct ParticleAoS particles[10000];

// Accessing only x coordinates touches 32 bytes per particle
for (int i = 0; i < 10000; i++) {
    process(particles[i].x);  // Cache misses!
}

// Struct of Arrays (SoA) - Better cache locality
struct ParticlesSoA {
    float x[10000];
    float y[10000];
    float z[10000];
    float vx[10000];
    float vy[10000];
    float vz[10000];
    float mass[10000];
    int id[10000];
};
struct ParticlesSoA particles;

// Accessing x coordinates is sequential
for (int i = 0; i < 10000; i++) {
    process(particles.x[i]);  // Cache friendly!
}
```

### Hot/Cold Data Splitting

```c
// Before: Mixed hot and cold data
struct Order {
    uint64_t order_id;      // Hot: accessed every tick
    double price;           // Hot
    int quantity;           // Hot
    char symbol[16];        // Warm
    char trader_id[32];     // Cold: rarely accessed
    char notes[256];        // Cold
    time_t created_at;      // Cold
};

// After: Split into hot and cold
struct OrderHot {
    uint64_t order_id;
    double price;
    int quantity;
    struct OrderCold *cold;  // Pointer to cold data
};

struct OrderCold {
    char symbol[16];
    char trader_id[32];
    char notes[256];
    time_t created_at;
};
```

---

## Loop Optimization

### Sequential Access

```c
// Row-major order (C default) - cache friendly
int matrix[1000][1000];

// Good: Sequential access
for (int i = 0; i < 1000; i++) {
    for (int j = 0; j < 1000; j++) {
        matrix[i][j] = 0;
    }
}

// Bad: Strided access (cache unfriendly)
for (int j = 0; j < 1000; j++) {
    for (int i = 0; i < 1000; i++) {
        matrix[i][j] = 0;  // Jumps 1000 elements each time!
    }
}
```

### Loop Tiling (Blocking)

```c
#define BLOCK_SIZE 64

// Matrix multiplication with cache blocking
void matmul_blocked(double *A, double *B, double *C, int N) {
    for (int ii = 0; ii < N; ii += BLOCK_SIZE) {
        for (int jj = 0; jj < N; jj += BLOCK_SIZE) {
            for (int kk = 0; kk < N; kk += BLOCK_SIZE) {
                // Process block
                for (int i = ii; i < ii + BLOCK_SIZE && i < N; i++) {
                    for (int j = jj; j < jj + BLOCK_SIZE && j < N; j++) {
                        double sum = C[i*N + j];
                        for (int k = kk; k < kk + BLOCK_SIZE && k < N; k++) {
                            sum += A[i*N + k] * B[k*N + j];
                        }
                        C[i*N + j] = sum;
                    }
                }
            }
        }
    }
}
```

---

## Prefetching

### Software Prefetch

```c
#include <xmmintrin.h>  // For _mm_prefetch

void process_array(int *data, int n) {
    for (int i = 0; i < n; i++) {
        // Prefetch data 8 elements ahead
        _mm_prefetch((char*)&data[i + 8], _MM_HINT_T0);
        
        process(data[i]);
    }
}

// Prefetch hints:
// _MM_HINT_T0  - L1 cache
// _MM_HINT_T1  - L2 cache
// _MM_HINT_T2  - L3 cache
// _MM_HINT_NTA - Non-temporal (bypass cache)
```

### GCC Built-in

```c
void process_array(int *data, int n) {
    for (int i = 0; i < n; i++) {
        // __builtin_prefetch(addr, rw, locality)
        // rw: 0=read, 1=write
        // locality: 0=NTA, 1=T2, 2=T1, 3=T0
        __builtin_prefetch(&data[i + 8], 0, 3);
        
        process(data[i]);
    }
}
```

---

## False Sharing Prevention

```c
#include <pthread.h>
#include <stdalign.h>

#define CACHE_LINE_SIZE 64

// Bad: False sharing between threads
struct SharedCounters {
    int counter1;
    int counter2;
};

// Good: Cache-line aligned to prevent false sharing
struct AlignedCounters {
    alignas(CACHE_LINE_SIZE) int counter1;
    alignas(CACHE_LINE_SIZE) int counter2;
};

// Alternative: Manual padding
struct PaddedCounters {
    int counter1;
    char pad1[CACHE_LINE_SIZE - sizeof(int)];
    int counter2;
    char pad2[CACHE_LINE_SIZE - sizeof(int)];
};
```

---

## Memory Pool for Cache Efficiency

```c
#include <stdint.h>
#include <string.h>

#define POOL_SIZE (1024 * 1024)  // 1MB pool
#define OBJECT_SIZE 64          // Cache-line sized objects

typedef struct {
    alignas(64) char pool[POOL_SIZE];
    size_t next_free;
    uint32_t free_list[POOL_SIZE / OBJECT_SIZE];
    size_t free_count;
} MemoryPool;

void pool_init(MemoryPool *mp) {
    mp->next_free = 0;
    mp->free_count = 0;
}

void *pool_alloc(MemoryPool *mp) {
    // Check free list first
    if (mp->free_count > 0) {
        uint32_t idx = mp->free_list[--mp->free_count];
        return &mp->pool[idx * OBJECT_SIZE];
    }
    
    // Allocate from pool
    if (mp->next_free + OBJECT_SIZE <= POOL_SIZE) {
        void *ptr = &mp->pool[mp->next_free];
        mp->next_free += OBJECT_SIZE;
        return ptr;
    }
    
    return NULL;  // Pool exhausted
}

void pool_free(MemoryPool *mp, void *ptr) {
    size_t offset = (char*)ptr - mp->pool;
    mp->free_list[mp->free_count++] = offset / OBJECT_SIZE;
}
```

---

## Measuring Cache Performance

### Using perf

```bash
# Count cache misses
perf stat -e cache-references,cache-misses,L1-dcache-loads,L1-dcache-load-misses ./program

# Record cache events
perf record -e cache-misses ./program
perf report
```

### Using Cachegrind

```bash
valgrind --tool=cachegrind ./program
cg_annotate cachegrind.out.*
```

### Inline Measurement

```c
#include <x86intrin.h>

uint64_t start = __rdtsc();
// Code to measure
uint64_t end = __rdtsc();
printf("Cycles: %lu\n", end - start);
```

---

## Practical Example: Order Book

```c
#include <stdint.h>
#include <stdalign.h>

#define MAX_LEVELS 10
#define CACHE_LINE 64

// Cache-optimized price level
typedef struct {
    double price;
    int64_t quantity;
} PriceLevel;

// Cache-aligned order book side
typedef struct {
    alignas(CACHE_LINE) PriceLevel levels[MAX_LEVELS];
    alignas(CACHE_LINE) int count;
} OrderBookSide;

// Full order book fits in cache
typedef struct {
    OrderBookSide bids;
    OrderBookSide asks;
} OrderBook;

// Hot path: Get best bid/ask
static inline double get_best_bid(const OrderBook *ob) {
    return ob->bids.count > 0 ? ob->bids.levels[0].price : 0.0;
}

static inline double get_best_ask(const OrderBook *ob) {
    return ob->asks.count > 0 ? ob->asks.levels[0].price : 0.0;
}
```

---

## Summary

| Technique | Impact | Use Case |
|-----------|--------|----------|
| SoA layout | High | SIMD, bulk processing |
| Hot/cold split | High | Mixed access patterns |
| Sequential access | High | Array traversal |
| Loop tiling | High | Matrix operations |
| Prefetching | Medium | Predictable access |
| Alignment | Medium | Multi-threaded code |
| Memory pools | Medium | Frequent alloc/free |

---

## Related Topics

- [17. Memory Alignment](@/articles/c/c-17-Memory-Alignment.md)
- [20. Lock-Free Ring Buffer (HFT)](@/articles/c/c-20-Ring-Buffer.md)
- [Cache-Friendly Data Structures (HFT)](@/articles/cpp/cpp-25-HFT缓存友好数据结构设计.md)
