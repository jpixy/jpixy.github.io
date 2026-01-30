+++
title = "19. Bit Operations and Tricks"
date = 2026-01-30
description = "Essential bit manipulation techniques for systems programming and interviews"
[taxonomies]
tags = ["C", "Bit Operations", "Algorithms", "Interview"]
+++

## Fundamental Bit Operations

### Basic Operators

```c
& (AND)   - Both bits must be 1
| (OR)    - At least one bit is 1
^ (XOR)   - Exactly one bit is 1
~ (NOT)   - Flip all bits
<< (Left shift)   - Multiply by 2^n
>> (Right shift)  - Divide by 2^n (arithmetic for signed)
```

### Truth Table

```
A  B  | A&B  A|B  A^B  ~A
------+-------------------
0  0  |  0    0    0    1
0  1  |  0    1    1    1
1  0  |  0    1    1    0
1  1  |  1    1    0    0
```

---

## Essential Bit Tricks

### Set, Clear, Toggle, Check

```c
// Set bit at position n
x |= (1 << n);

// Clear bit at position n
x &= ~(1 << n);

// Toggle bit at position n
x ^= (1 << n);

// Check bit at position n
int bit = (x >> n) & 1;
// or
int bit = (x & (1 << n)) != 0;
```

### Multiple Bits

```c
// Set bits in range [low, high]
x |= ((1 << (high - low + 1)) - 1) << low;

// Clear bits in range [low, high]
x &= ~(((1 << (high - low + 1)) - 1) << low);

// Extract bits [low, high]
int bits = (x >> low) & ((1 << (high - low + 1)) - 1);
```

---

## Power of Two Operations

```c
// Check if n is power of 2
int is_power_of_2(unsigned int n) {
    return n && !(n & (n - 1));
}

// Round up to next power of 2
unsigned int next_power_of_2(unsigned int n) {
    n--;
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    return n + 1;
}

// Round down to previous power of 2
unsigned int prev_power_of_2(unsigned int n) {
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    return n - (n >> 1);
}
```

---

## Counting Bits

### Count Set Bits (Population Count)

```c
// Method 1: Loop
int popcount_loop(unsigned int n) {
    int count = 0;
    while (n) {
        count += n & 1;
        n >>= 1;
    }
    return count;
}

// Method 2: Brian Kernighan (faster for sparse bits)
int popcount_kernighan(unsigned int n) {
    int count = 0;
    while (n) {
        n &= (n - 1);  // Clear lowest set bit
        count++;
    }
    return count;
}

// Method 3: Lookup table
static const uint8_t popcount_table[256] = { /* precomputed */ };
int popcount_table(unsigned int n) {
    return popcount_table[n & 0xff] +
           popcount_table[(n >> 8) & 0xff] +
           popcount_table[(n >> 16) & 0xff] +
           popcount_table[(n >> 24) & 0xff];
}

// Method 4: GCC built-in (fastest)
int popcount_builtin(unsigned int n) {
    return __builtin_popcount(n);
}
```

### Find First/Last Set Bit

```c
// Find position of lowest set bit (1-indexed, 0 if none)
int ffs(unsigned int n) {
    return __builtin_ffs(n);  // GCC built-in
}

// Count trailing zeros
int ctz(unsigned int n) {
    return __builtin_ctz(n);  // GCC built-in
}

// Count leading zeros
int clz(unsigned int n) {
    return __builtin_clz(n);  // GCC built-in
}

// Find highest set bit position
int highest_bit(unsigned int n) {
    return n ? 31 - __builtin_clz(n) : -1;
}
```

---

## XOR Tricks

### Swap Without Temp

```c
void swap(int *a, int *b) {
    if (a != b) {  // Important check!
        *a ^= *b;
        *b ^= *a;
        *a ^= *b;
    }
}
```

### Find Missing Number

```c
// Array contains 0 to n except one missing
int find_missing(int arr[], int n) {
    int xor_all = 0;
    for (int i = 0; i <= n; i++) xor_all ^= i;
    for (int i = 0; i < n; i++) xor_all ^= arr[i];
    return xor_all;
}
```

### Find Single Number

```c
// All elements appear twice except one
int find_single(int arr[], int n) {
    int result = 0;
    for (int i = 0; i < n; i++) {
        result ^= arr[i];
    }
    return result;
}
```

---

## Sign and Absolute Value

```c
// Get sign (-1, 0, or 1)
int sign(int n) {
    return (n > 0) - (n < 0);
}

// Absolute value without branching
int abs_nobranch(int n) {
    int mask = n >> 31;  // All 1s if negative, 0 if positive
    return (n + mask) ^ mask;
}

// Negate without minus
int negate(int n) {
    return ~n + 1;
}
```

---

## Min/Max Without Branching

```c
// Min of two integers
int min(int a, int b) {
    return b ^ ((a ^ b) & -(a < b));
}

// Max of two integers
int max(int a, int b) {
    return a ^ ((a ^ b) & -(a < b));
}

// Note: Modern compilers often generate branchless code
// for simple ternary operators anyway
```

---

## Bit Manipulation for Flags

```c
#define FLAG_READ   (1 << 0)  // 0x01
#define FLAG_WRITE  (1 << 1)  // 0x02
#define FLAG_EXEC   (1 << 2)  // 0x04
#define FLAG_HIDDEN (1 << 3)  // 0x08

unsigned int permissions = 0;

// Set permissions
permissions |= FLAG_READ | FLAG_WRITE;

// Check permission
if (permissions & FLAG_EXEC) {
    // Has execute permission
}

// Remove permission
permissions &= ~FLAG_WRITE;

// Toggle permission
permissions ^= FLAG_HIDDEN;
```

---

## Endianness Operations

```c
// Check endianness at runtime
int is_little_endian(void) {
    uint32_t x = 1;
    return *(uint8_t *)&x == 1;
}

// Byte swap (little <-> big endian)
uint16_t bswap16(uint16_t x) {
    return (x << 8) | (x >> 8);
}

uint32_t bswap32(uint32_t x) {
    return ((x >> 24) & 0xff) |
           ((x >> 8) & 0xff00) |
           ((x << 8) & 0xff0000) |
           ((x << 24) & 0xff000000);
}

// Or use GCC built-ins
uint32_t bswap32_builtin(uint32_t x) {
    return __builtin_bswap32(x);
}
```

---

## Bitmap Implementation

```c
#include <stdint.h>
#include <string.h>

#define BITMAP_BITS 1024
#define WORD_BITS 32

typedef struct {
    uint32_t data[BITMAP_BITS / WORD_BITS];
} Bitmap;

void bitmap_set(Bitmap *bm, int pos) {
    bm->data[pos / WORD_BITS] |= (1U << (pos % WORD_BITS));
}

void bitmap_clear(Bitmap *bm, int pos) {
    bm->data[pos / WORD_BITS] &= ~(1U << (pos % WORD_BITS));
}

int bitmap_test(Bitmap *bm, int pos) {
    return (bm->data[pos / WORD_BITS] >> (pos % WORD_BITS)) & 1;
}

int bitmap_find_first_zero(Bitmap *bm) {
    for (int i = 0; i < BITMAP_BITS / WORD_BITS; i++) {
        if (bm->data[i] != 0xFFFFFFFF) {
            return i * WORD_BITS + __builtin_ctz(~bm->data[i]);
        }
    }
    return -1;
}
```

---

## Interview Classic: Reverse Bits

```c
uint32_t reverse_bits(uint32_t n) {
    n = ((n >> 1) & 0x55555555) | ((n & 0x55555555) << 1);
    n = ((n >> 2) & 0x33333333) | ((n & 0x33333333) << 2);
    n = ((n >> 4) & 0x0F0F0F0F) | ((n & 0x0F0F0F0F) << 4);
    n = ((n >> 8) & 0x00FF00FF) | ((n & 0x00FF00FF) << 8);
    n = (n >> 16) | (n << 16);
    return n;
}
```

---

## Related Topics

- [03. Operators and Expressions](@/articles/c/c-03-运算符与表达式.md)
- [40. C Written Test Questions](@/articles/c/c-40-C-Written-Test-Questions.md)
- [17. Memory Alignment](@/articles/c/c-17-Memory-Alignment.md)
