+++
title = "18. Lock-Free Ring Buffer (HFT)"
date = 2026-01-30
weight = 18000
description = "High-performance lock-free ring buffer implementation for low-latency systems"
[taxonomies]
tags = ["C", "HFT", "Lock-Free", "Data Structures", "Low-Latency"]
+++

## Overview

Ring buffers (circular buffers) are fundamental data structures in high-frequency trading systems. They provide O(1) push/pop operations and are ideal for producer-consumer patterns.

---

## Basic Ring Buffer

### Simple Implementation

```c
#include <stddef.h>
#include <string.h>

#define RING_SIZE 1024  // Must be power of 2

typedef struct {
    char buffer[RING_SIZE];
    size_t head;  // Write position
    size_t tail;  // Read position
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

size_t ring_size(RingBuffer *rb) {
    return (rb->head - rb->tail) & (RING_SIZE - 1);
}

int ring_push(RingBuffer *rb, char c) {
    if (ring_is_full(rb)) return -1;
    rb->buffer[rb->head] = c;
    rb->head = (rb->head + 1) & (RING_SIZE - 1);
    return 0;
}

int ring_pop(RingBuffer *rb, char *c) {
    if (ring_is_empty(rb)) return -1;
    *c = rb->buffer[rb->tail];
    rb->tail = (rb->tail + 1) & (RING_SIZE - 1);
    return 0;
}
```

---

## Lock-Free SPSC Ring Buffer

Single-Producer Single-Consumer (SPSC) ring buffer using atomics:

```c
#include <stdatomic.h>
#include <stddef.h>
#include <stdalign.h>

#define RING_SIZE 4096
#define CACHE_LINE 64

typedef struct {
    alignas(CACHE_LINE) _Atomic size_t head;
    alignas(CACHE_LINE) _Atomic size_t tail;
    alignas(CACHE_LINE) int data[RING_SIZE];
} SPSCRing;

void spsc_init(SPSCRing *ring) {
    atomic_store(&ring->head, 0);
    atomic_store(&ring->tail, 0);
}

int spsc_push(SPSCRing *ring, int value) {
    size_t head = atomic_load_explicit(&ring->head, memory_order_relaxed);
    size_t next = (head + 1) & (RING_SIZE - 1);
    
    // Check if full
    if (next == atomic_load_explicit(&ring->tail, memory_order_acquire)) {
        return -1;
    }
    
    ring->data[head] = value;
    atomic_store_explicit(&ring->head, next, memory_order_release);
    return 0;
}

int spsc_pop(SPSCRing *ring, int *value) {
    size_t tail = atomic_load_explicit(&ring->tail, memory_order_relaxed);
    
    // Check if empty
    if (tail == atomic_load_explicit(&ring->head, memory_order_acquire)) {
        return -1;
    }
    
    *value = ring->data[tail];
    atomic_store_explicit(&ring->tail, (tail + 1) & (RING_SIZE - 1), 
                          memory_order_release);
    return 0;
}
```

---

## Batch Operations for HFT

```c
// Push multiple items at once
size_t spsc_push_batch(SPSCRing *ring, const int *values, size_t count) {
    size_t head = atomic_load_explicit(&ring->head, memory_order_relaxed);
    size_t tail = atomic_load_explicit(&ring->tail, memory_order_acquire);
    
    size_t available = (tail - head - 1) & (RING_SIZE - 1);
    if (count > available) count = available;
    if (count == 0) return 0;
    
    // Copy data
    size_t first_chunk = RING_SIZE - head;
    if (first_chunk >= count) {
        memcpy(&ring->data[head], values, count * sizeof(int));
    } else {
        memcpy(&ring->data[head], values, first_chunk * sizeof(int));
        memcpy(&ring->data[0], values + first_chunk, 
               (count - first_chunk) * sizeof(int));
    }
    
    atomic_store_explicit(&ring->head, (head + count) & (RING_SIZE - 1), 
                          memory_order_release);
    return count;
}

// Pop multiple items at once
size_t spsc_pop_batch(SPSCRing *ring, int *values, size_t max_count) {
    size_t tail = atomic_load_explicit(&ring->tail, memory_order_relaxed);
    size_t head = atomic_load_explicit(&ring->head, memory_order_acquire);
    
    size_t available = (head - tail) & (RING_SIZE - 1);
    size_t count = (max_count < available) ? max_count : available;
    if (count == 0) return 0;
    
    // Copy data
    size_t first_chunk = RING_SIZE - tail;
    if (first_chunk >= count) {
        memcpy(values, &ring->data[tail], count * sizeof(int));
    } else {
        memcpy(values, &ring->data[tail], first_chunk * sizeof(int));
        memcpy(values + first_chunk, &ring->data[0], 
               (count - first_chunk) * sizeof(int));
    }
    
    atomic_store_explicit(&ring->tail, (tail + count) & (RING_SIZE - 1), 
                          memory_order_release);
    return count;
}
```

---

## MPMC Ring Buffer

Multi-Producer Multi-Consumer requires more complex synchronization:

```c
#include <stdatomic.h>

#define RING_SIZE 4096
#define CACHE_LINE 64

typedef struct {
    _Atomic size_t sequence;
    int data;
} Cell;

typedef struct {
    alignas(CACHE_LINE) Cell cells[RING_SIZE];
    alignas(CACHE_LINE) _Atomic size_t head;
    alignas(CACHE_LINE) _Atomic size_t tail;
} MPMCRing;

void mpmc_init(MPMCRing *ring) {
    atomic_store(&ring->head, 0);
    atomic_store(&ring->tail, 0);
    for (size_t i = 0; i < RING_SIZE; i++) {
        atomic_store(&ring->cells[i].sequence, i);
    }
}

int mpmc_push(MPMCRing *ring, int value) {
    Cell *cell;
    size_t pos;
    
    for (;;) {
        pos = atomic_load_explicit(&ring->head, memory_order_relaxed);
        cell = &ring->cells[pos & (RING_SIZE - 1)];
        size_t seq = atomic_load_explicit(&cell->sequence, memory_order_acquire);
        
        intptr_t diff = (intptr_t)seq - (intptr_t)pos;
        
        if (diff == 0) {
            if (atomic_compare_exchange_weak_explicit(
                    &ring->head, &pos, pos + 1,
                    memory_order_relaxed, memory_order_relaxed)) {
                break;
            }
        } else if (diff < 0) {
            return -1;  // Full
        }
        // Otherwise, retry
    }
    
    cell->data = value;
    atomic_store_explicit(&cell->sequence, pos + 1, memory_order_release);
    return 0;
}

int mpmc_pop(MPMCRing *ring, int *value) {
    Cell *cell;
    size_t pos;
    
    for (;;) {
        pos = atomic_load_explicit(&ring->tail, memory_order_relaxed);
        cell = &ring->cells[pos & (RING_SIZE - 1)];
        size_t seq = atomic_load_explicit(&cell->sequence, memory_order_acquire);
        
        intptr_t diff = (intptr_t)seq - (intptr_t)(pos + 1);
        
        if (diff == 0) {
            if (atomic_compare_exchange_weak_explicit(
                    &ring->tail, &pos, pos + 1,
                    memory_order_relaxed, memory_order_relaxed)) {
                break;
            }
        } else if (diff < 0) {
            return -1;  // Empty
        }
        // Otherwise, retry
    }
    
    *value = cell->data;
    atomic_store_explicit(&cell->sequence, pos + RING_SIZE, memory_order_release);
    return 0;
}
```

---

## Performance Optimizations

### Cache-Line Padding

```c
// Prevent false sharing between head and tail
typedef struct {
    alignas(64) _Atomic size_t head;
    char pad1[64 - sizeof(_Atomic size_t)];
    
    alignas(64) _Atomic size_t tail;
    char pad2[64 - sizeof(_Atomic size_t)];
    
    alignas(64) int data[RING_SIZE];
} OptimizedRing;
```

### Prefetching

```c
int spsc_pop_prefetch(SPSCRing *ring, int *value) {
    size_t tail = atomic_load_explicit(&ring->tail, memory_order_relaxed);
    
    if (tail == atomic_load_explicit(&ring->head, memory_order_acquire)) {
        return -1;
    }
    
    // Prefetch next element
    __builtin_prefetch(&ring->data[(tail + 1) & (RING_SIZE - 1)], 0, 3);
    
    *value = ring->data[tail];
    atomic_store_explicit(&ring->tail, (tail + 1) & (RING_SIZE - 1), 
                          memory_order_release);
    return 0;
}
```

### Power-of-Two Size

```c
// Using power-of-two size allows bitwise AND instead of modulo
// (head + 1) & (SIZE - 1) is faster than (head + 1) % SIZE

// Compile-time check
_Static_assert((RING_SIZE & (RING_SIZE - 1)) == 0, 
               "RING_SIZE must be power of 2");
```

---

## Usage Example

```c
#include <pthread.h>
#include <stdio.h>

SPSCRing ring;

void *producer(void *arg) {
    for (int i = 0; i < 1000000; i++) {
        while (spsc_push(&ring, i) != 0) {
            // Busy wait or yield
        }
    }
    return NULL;
}

void *consumer(void *arg) {
    int value;
    for (int i = 0; i < 1000000; i++) {
        while (spsc_pop(&ring, &value) != 0) {
            // Busy wait or yield
        }
        // Process value
    }
    return NULL;
}

int main(void) {
    spsc_init(&ring);
    
    pthread_t prod, cons;
    pthread_create(&prod, NULL, producer, NULL);
    pthread_create(&cons, NULL, consumer, NULL);
    
    pthread_join(prod, NULL);
    pthread_join(cons, NULL);
    
    return 0;
}
```

---

## Related Topics

- [16. Volatile and Memory Barriers (HFT)](@/articles/c/c-16-Volatile-Memory-Barriers.md)
- [Lock-Free Data Structures (HFT)](@/articles/cpp/cpp-17-HFT-Lock-Free数据结构详解.md)
- [14. IO Multiplexing](@/articles/c/c-14-IO多路复用详解.md)


---

## 相关文章

- [上一篇：Bit Operations and Tricks](@/articles/c/c-17-Bit-Operations.md)
- [下一篇：Cache-Friendly C Programming (HFT)](@/articles/c/c-19-Cache-Friendly-Programming.md)
