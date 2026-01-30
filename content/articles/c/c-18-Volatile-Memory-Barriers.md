+++
title = "18. Volatile and Memory Barriers (HFT)"
date = 2026-01-30
description = "Understanding volatile, memory barriers, and compiler/CPU reordering in high-performance C code"
[taxonomies]
tags = ["C", "HFT", "Memory", "Concurrency", "Low-Latency"]
+++

## Overview

In high-frequency trading and low-latency systems, understanding memory ordering is critical. This article covers volatile, memory barriers, and how to correctly synchronize memory access.

---

## The volatile Keyword

### What volatile Does

```c
volatile int flag = 0;

// Without volatile: compiler may optimize away the loop
while (flag == 0) {
    // Compiler might read flag once and cache it
}

// With volatile: forces memory read each iteration
volatile int *vflag = &flag;
while (*vflag == 0) {
    // Compiler reads from memory each time
}
```

### volatile Use Cases

```c
// 1. Hardware registers
volatile uint32_t *status_reg = (uint32_t *)0x40000000;
while (*status_reg & BUSY_FLAG) {
    // Wait for hardware
}

// 2. Signal handlers
volatile sig_atomic_t signal_received = 0;

void handler(int sig) {
    signal_received = 1;
}

// 3. Memory-mapped I/O
volatile uint8_t *uart_data = (uint8_t *)UART_BASE;
*uart_data = 'A';  // Must write to hardware
```

### What volatile Does NOT Do

```c
volatile int counter = 0;

// WRONG: volatile does NOT guarantee atomicity
void increment(void) {
    counter++;  // This is NOT atomic!
    // Read -> Modify -> Write can be interrupted
}

// WRONG: volatile does NOT prevent CPU reordering
volatile int ready = 0;
int data = 0;

void producer(void) {
    data = 42;    // May be reordered after ready = 1
    ready = 1;
}
```

---

## Memory Barriers

### Why We Need Memory Barriers

```
CPU Reordering Problem:
┌──────────────────────────────────────────────────┐
│ Code:              Executed as:                  │
│   data = 42;         ready = 1;   // Reordered!  │
│   ready = 1;         data = 42;                  │
│                                                  │
│ Consumer sees ready=1 but data is still 0!      │
└──────────────────────────────────────────────────┘
```

### Compiler Barriers

```c
// GCC/Clang compiler barrier
#define compiler_barrier() asm volatile("" ::: "memory")

// Prevents compiler from reordering across this point
data = 42;
compiler_barrier();
ready = 1;

// Alternative using volatile
*(volatile int *)&data = 42;
*(volatile int *)&ready = 1;
```

### CPU Memory Barriers

```c
// Full memory barrier (all CPUs see all prior writes)
#define mb()    asm volatile("mfence" ::: "memory")

// Write barrier (all prior writes complete)
#define wmb()   asm volatile("sfence" ::: "memory")

// Read barrier (all prior reads complete)
#define rmb()   asm volatile("lfence" ::: "memory")

// Usage
void producer(void) {
    data = 42;
    wmb();      // Ensure data is visible before ready
    ready = 1;
}

void consumer(void) {
    while (!ready) { /* spin */ }
    rmb();      // Ensure we see data after ready
    use(data);
}
```

### GCC Built-in Barriers

```c
// Full barrier
__sync_synchronize();

// Atomic with implicit barrier
__sync_fetch_and_add(&counter, 1);
__sync_bool_compare_and_swap(&flag, 0, 1);

// C11 atomics (preferred)
#include <stdatomic.h>
atomic_thread_fence(memory_order_seq_cst);
```

---

## Memory Ordering in C11

### atomic_thread_fence

```c
#include <stdatomic.h>

// Memory orders (weakest to strongest):
// memory_order_relaxed  - No ordering guarantees
// memory_order_consume  - Data dependency ordering (deprecated)
// memory_order_acquire  - No reads/writes reordered before
// memory_order_release  - No reads/writes reordered after
// memory_order_acq_rel  - Both acquire and release
// memory_order_seq_cst  - Sequential consistency (default)

_Atomic int data;
_Atomic int ready;

void producer(void) {
    atomic_store_explicit(&data, 42, memory_order_relaxed);
    atomic_thread_fence(memory_order_release);
    atomic_store_explicit(&ready, 1, memory_order_relaxed);
}

void consumer(void) {
    while (!atomic_load_explicit(&ready, memory_order_relaxed)) {}
    atomic_thread_fence(memory_order_acquire);
    int val = atomic_load_explicit(&data, memory_order_relaxed);
}
```

### Acquire-Release Pattern

```c
#include <stdatomic.h>

_Atomic int lock = 0;

void acquire_lock(void) {
    while (atomic_exchange_explicit(&lock, 1, memory_order_acquire)) {
        // Spin
    }
    // All reads/writes after this see prior releases
}

void release_lock(void) {
    atomic_store_explicit(&lock, 0, memory_order_release);
    // All reads/writes before this are visible to acquirers
}
```

---

## HFT-Specific Patterns

### Lock-Free Flag

```c
#include <stdatomic.h>

typedef struct {
    _Alignas(64) _Atomic int flag;  // Cache-line aligned
} AlignedFlag;

AlignedFlag shutdown_flag = {0};

// Producer (signal shutdown)
void signal_shutdown(void) {
    atomic_store_explicit(&shutdown_flag.flag, 1, memory_order_release);
}

// Consumer (check shutdown)
int should_shutdown(void) {
    return atomic_load_explicit(&shutdown_flag.flag, memory_order_acquire);
}
```

### SPSC Ring Buffer (Lock-Free)

```c
#include <stdatomic.h>

#define RING_SIZE 1024  // Must be power of 2

typedef struct {
    _Alignas(64) _Atomic size_t head;
    _Alignas(64) _Atomic size_t tail;
    _Alignas(64) int buffer[RING_SIZE];
} SPSCRing;

int ring_push(SPSCRing *ring, int value) {
    size_t head = atomic_load_explicit(&ring->head, memory_order_relaxed);
    size_t next = (head + 1) & (RING_SIZE - 1);
    
    if (next == atomic_load_explicit(&ring->tail, memory_order_acquire)) {
        return -1;  // Full
    }
    
    ring->buffer[head] = value;
    atomic_store_explicit(&ring->head, next, memory_order_release);
    return 0;
}

int ring_pop(SPSCRing *ring, int *value) {
    size_t tail = atomic_load_explicit(&ring->tail, memory_order_relaxed);
    
    if (tail == atomic_load_explicit(&ring->head, memory_order_acquire)) {
        return -1;  // Empty
    }
    
    *value = ring->buffer[tail];
    atomic_store_explicit(&ring->tail, (tail + 1) & (RING_SIZE - 1), 
                          memory_order_release);
    return 0;
}
```

### Busy-Wait with Backoff

```c
#include <stdatomic.h>
#include <immintrin.h>  // For _mm_pause

_Atomic int ready = 0;

void wait_for_ready(void) {
    int spins = 0;
    
    while (!atomic_load_explicit(&ready, memory_order_acquire)) {
        if (++spins < 1000) {
            _mm_pause();  // Reduce power, improve spin-lock performance
        } else {
            // Yield or brief sleep for longer waits
            sched_yield();
            spins = 0;
        }
    }
}
```

---

## Common Mistakes

### 1. Assuming volatile is Enough

```c
// WRONG
volatile int counter = 0;
counter++;  // Not atomic!

// CORRECT
_Atomic int counter = 0;
atomic_fetch_add(&counter, 1);
```

### 2. Missing Barriers

```c
// WRONG - CPU can reorder
int data = 42;
int ready = 1;

// CORRECT
int data = 42;
atomic_thread_fence(memory_order_release);
atomic_store(&ready, 1);
```

### 3. Over-Synchronization

```c
// WRONG - Too conservative, hurts performance
atomic_store(&x, 1);  // Default: seq_cst
atomic_store(&y, 2);  // Default: seq_cst

// CORRECT - Use appropriate ordering
atomic_store_explicit(&x, 1, memory_order_relaxed);
atomic_store_explicit(&y, 2, memory_order_release);
```

---

## Testing Memory Ordering

```c
// Use ThreadSanitizer to detect data races
// Compile with: gcc -fsanitize=thread -g

// Use stress testing
void stress_test(void) {
    for (int i = 0; i < 1000000; i++) {
        // Reset
        atomic_store(&ready, 0);
        atomic_store(&data, 0);
        
        // Run producer and consumer concurrently
        // Check for anomalies
    }
}
```

---

## Platform-Specific Notes

### x86/x64

- Strong memory model (TSO)
- Most loads/stores implicitly ordered
- Still need barriers for specific patterns

### ARM

- Weak memory model
- Explicit barriers often required
- DMB, DSB, ISB instructions

### Compiler Flags

```bash
# GCC: Control memory model
gcc -mcx16              # Enable 16-byte CAS
gcc -march=native       # Use native atomics

# Clang: Similar options
clang -fsanitize=thread # Detect races
```

---

## Related Topics

- [17. Memory Alignment and Struct Packing](@/articles/c/c-17-Memory-Alignment.md)
- [19. Bit Operations and Tricks](@/articles/c/c-19-Bit-Operations.md)
- [Lock-Free Data Structures (HFT)](@/articles/cpp/cpp-22-HFT-Lock-Free数据结构详解.md)
