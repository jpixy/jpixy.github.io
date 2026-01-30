+++
title = "23. SIMD Programming (HFT)"
date = 2026-01-21
description = "深入剖析SIMD向量化编程，包括SSE、AVX、AVX-512指令集，intrinsics使用，HFT低延迟优化核心技术"
[taxonomies]
tags = ["C++", "SIMD", "AVX", "性能优化", "HFT", "向量化"]
+++

## 概述

SIMD（Single Instruction Multiple Data）允许一条指令同时处理多个数据，是HFT系统性能优化的利器。通过SIMD，可以将计算密集型操作的性能提升4-16倍。

---

## 一、SIMD基础

### 1.1 向量寄存器

```cpp
// x86 SIMD寄存器演进
// SSE:    128位寄存器 (xmm0-xmm15) - 4个float或2个double
// AVX:    256位寄存器 (ymm0-ymm15) - 8个float或4个double
// AVX-512: 512位寄存器 (zmm0-zmm31) - 16个float或8个double

#include <immintrin.h>

void showRegisterSizes() {
    __m128 sse_reg;    // 128位 = 4 x float
    __m256 avx_reg;    // 256位 = 8 x float
    __m512 avx512_reg; // 512位 = 16 x float
    
    __m128d sse_double;   // 128位 = 2 x double
    __m256d avx_double;   // 256位 = 4 x double
    __m512d avx512_double;// 512位 = 8 x double
    
    __m128i sse_int;      // 128位整数
    __m256i avx_int;      // 256位整数
}
```

### 1.2 基本操作

```cpp
#include <immintrin.h>

void basicSIMD() {
    // 加载数据
    float data[8] = {1, 2, 3, 4, 5, 6, 7, 8};
    __m256 vec = _mm256_loadu_ps(data);  // 无对齐要求
    // 或
    alignas(32) float aligned_data[8];
    __m256 vec2 = _mm256_load_ps(aligned_data);  // 需要32字节对齐
    
    // 算术运算
    __m256 a = _mm256_set1_ps(2.0f);  // 所有元素设为2.0
    __m256 result = _mm256_mul_ps(vec, a);  // 向量乘法
    
    // 存储结果
    _mm256_storeu_ps(data, result);
}
```

---

## 二、常用Intrinsics

### 2.1 数据加载/存储

```cpp
// 加载
__m256 _mm256_load_ps(float const* mem_addr);     // 对齐加载
__m256 _mm256_loadu_ps(float const* mem_addr);    // 非对齐加载
__m256 _mm256_set1_ps(float a);                   // 广播单个值
__m256 _mm256_set_ps(f7,f6,f5,f4,f3,f2,f1,f0);   // 设置每个值
__m256 _mm256_setzero_ps();                       // 全零

// 存储
void _mm256_store_ps(float* mem_addr, __m256 a);  // 对齐存储
void _mm256_storeu_ps(float* mem_addr, __m256 a); // 非对齐存储
```

### 2.2 算术运算

```cpp
// 基本算术
__m256 _mm256_add_ps(__m256 a, __m256 b);   // 加法
__m256 _mm256_sub_ps(__m256 a, __m256 b);   // 减法
__m256 _mm256_mul_ps(__m256 a, __m256 b);   // 乘法
__m256 _mm256_div_ps(__m256 a, __m256 b);   // 除法

// 融合乘加 (FMA) - 更高精度和性能
__m256 _mm256_fmadd_ps(__m256 a, __m256 b, __m256 c);  // a*b + c
__m256 _mm256_fmsub_ps(__m256 a, __m256 b, __m256 c);  // a*b - c

// 比较
__m256 _mm256_cmp_ps(__m256 a, __m256 b, int imm8);
// imm8: _CMP_EQ_OQ, _CMP_LT_OS, _CMP_LE_OS, _CMP_GT_OS, _CMP_GE_OS

// 最大/最小
__m256 _mm256_max_ps(__m256 a, __m256 b);
__m256 _mm256_min_ps(__m256 a, __m256 b);
```

### 2.3 整数操作

```cpp
// 整数加法
__m256i _mm256_add_epi32(__m256i a, __m256i b);  // 32位整数加法
__m256i _mm256_add_epi64(__m256i a, __m256i b);  // 64位整数加法

// 位操作
__m256i _mm256_and_si256(__m256i a, __m256i b);  // AND
__m256i _mm256_or_si256(__m256i a, __m256i b);   // OR
__m256i _mm256_xor_si256(__m256i a, __m256i b);  // XOR

// 移位
__m256i _mm256_slli_epi32(__m256i a, int imm8);  // 左移
__m256i _mm256_srli_epi32(__m256i a, int imm8);  // 逻辑右移
```

---

## 三、实战案例

### 3.1 向量点积

```cpp
float dotProduct(const float* a, const float* b, size_t n) {
    __m256 sum = _mm256_setzero_ps();
    
    size_t i = 0;
    for (; i + 8 <= n; i += 8) {
        __m256 va = _mm256_loadu_ps(a + i);
        __m256 vb = _mm256_loadu_ps(b + i);
        sum = _mm256_fmadd_ps(va, vb, sum);  // sum += va * vb
    }
    
    // 水平求和
    __m128 hi = _mm256_extractf128_ps(sum, 1);
    __m128 lo = _mm256_castps256_ps128(sum);
    __m128 sum128 = _mm_add_ps(hi, lo);
    sum128 = _mm_hadd_ps(sum128, sum128);
    sum128 = _mm_hadd_ps(sum128, sum128);
    
    float result = _mm_cvtss_f32(sum128);
    
    // 处理剩余元素
    for (; i < n; ++i) {
        result += a[i] * b[i];
    }
    
    return result;
}
```

### 3.2 快速校验和

```cpp
uint32_t checksumSIMD(const uint8_t* data, size_t len) {
    __m256i sum = _mm256_setzero_si256();
    
    size_t i = 0;
    for (; i + 32 <= len; i += 32) {
        __m256i chunk = _mm256_loadu_si256((__m256i*)(data + i));
        // 将字节扩展为32位整数并累加
        __m256i lo16 = _mm256_unpacklo_epi8(chunk, _mm256_setzero_si256());
        __m256i hi16 = _mm256_unpackhi_epi8(chunk, _mm256_setzero_si256());
        sum = _mm256_add_epi32(sum, _mm256_unpacklo_epi16(lo16, _mm256_setzero_si256()));
        sum = _mm256_add_epi32(sum, _mm256_unpackhi_epi16(lo16, _mm256_setzero_si256()));
        sum = _mm256_add_epi32(sum, _mm256_unpacklo_epi16(hi16, _mm256_setzero_si256()));
        sum = _mm256_add_epi32(sum, _mm256_unpackhi_epi16(hi16, _mm256_setzero_si256()));
    }
    
    // 水平求和
    __m128i sum128 = _mm_add_epi32(_mm256_extracti128_si256(sum, 0),
                                   _mm256_extracti128_si256(sum, 1));
    sum128 = _mm_hadd_epi32(sum128, sum128);
    sum128 = _mm_hadd_epi32(sum128, sum128);
    
    uint32_t result = _mm_cvtsi128_si32(sum128);
    
    for (; i < len; ++i) {
        result += data[i];
    }
    
    return result;
}
```

### 3.3 价格查找

```cpp
// HFT场景：在订单簿中查找价格
int findPriceSIMD(const int32_t* prices, size_t n, int32_t target) {
    __m256i target_vec = _mm256_set1_epi32(target);
    
    size_t i = 0;
    for (; i + 8 <= n; i += 8) {
        __m256i prices_vec = _mm256_loadu_si256((__m256i*)(prices + i));
        __m256i cmp = _mm256_cmpeq_epi32(prices_vec, target_vec);
        int mask = _mm256_movemask_epi8(cmp);
        
        if (mask != 0) {
            // 找到匹配，确定具体位置
            int pos = __builtin_ctz(mask) / 4;  // 每个int32是4字节
            return i + pos;
        }
    }
    
    // 处理剩余
    for (; i < n; ++i) {
        if (prices[i] == target) return i;
    }
    
    return -1;  // 未找到
}
```

---

## 四、自动向量化

### 4.1 编译器自动向量化

```cpp
// 编译器可能自动向量化的代码
void addArrays(float* a, const float* b, const float* c, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        a[i] = b[i] + c[i];  // 编译器可能自动使用SIMD
    }
}

// 帮助编译器向量化
void addArraysOptimized(float* __restrict a, 
                        const float* __restrict b,
                        const float* __restrict c, 
                        size_t n) {
    // __restrict告诉编译器指针不会别名
    #pragma omp simd  // OpenMP SIMD指令
    for (size_t i = 0; i < n; ++i) {
        a[i] = b[i] + c[i];
    }
}
```

### 4.2 编译选项

```bash
# GCC/Clang
g++ -O3 -march=native -ftree-vectorize -ffast-math source.cpp

# 查看向量化报告
g++ -O3 -march=native -fopt-info-vec-all source.cpp 2>&1 | grep vectorized

# 特定指令集
g++ -mavx2 -mfma source.cpp
g++ -mavx512f source.cpp
```

---

## 五、性能测试

```cpp
#include <chrono>

void benchmarkSIMD() {
    constexpr size_t N = 1000000;
    alignas(32) float a[N], b[N], c[N];
    
    // 初始化
    for (size_t i = 0; i < N; ++i) {
        a[i] = i * 0.1f;
        b[i] = i * 0.2f;
    }
    
    // 标量版本
    {
        auto start = std::chrono::high_resolution_clock::now();
        for (size_t i = 0; i < N; ++i) {
            c[i] = a[i] * b[i] + 1.0f;
        }
        auto end = std::chrono::high_resolution_clock::now();
        std::cout << "Scalar: " << /* ... */ << " ns\n";
    }
    
    // SIMD版本
    {
        __m256 one = _mm256_set1_ps(1.0f);
        auto start = std::chrono::high_resolution_clock::now();
        for (size_t i = 0; i < N; i += 8) {
            __m256 va = _mm256_load_ps(a + i);
            __m256 vb = _mm256_load_ps(b + i);
            __m256 vc = _mm256_fmadd_ps(va, vb, one);
            _mm256_store_ps(c + i, vc);
        }
        auto end = std::chrono::high_resolution_clock::now();
        std::cout << "AVX: " << /* ... */ << " ns\n";
    }
}

// 典型结果（100万元素）：
// Scalar: 2000 µs
// AVX: 250 µs (8x speedup)
```

---

## 六、注意事项

### 6.1 对齐

```cpp
// 对齐分配
alignas(32) float data[1024];  // 32字节对齐（AVX）
alignas(64) float data512[1024];  // 64字节对齐（AVX-512）

// 动态对齐分配
float* ptr = static_cast<float*>(std::aligned_alloc(32, 1024 * sizeof(float)));
```

### 6.2 CPU特性检测

```cpp
#include <cpuid.h>

bool hasAVX2() {
    unsigned int eax, ebx, ecx, edx;
    if (__get_cpuid(7, &eax, &ebx, &ecx, &edx)) {
        return (ebx & (1 << 5)) != 0;  // AVX2位
    }
    return false;
}

bool hasAVX512() {
    unsigned int eax, ebx, ecx, edx;
    if (__get_cpuid(7, &eax, &ebx, &ecx, &edx)) {
        return (ebx & (1 << 16)) != 0;  // AVX-512F位
    }
    return false;
}
```

---

## 总结

| 指令集 | 寄存器宽度 | float数量 | 适用场景 |
|--------|------------|-----------|----------|
| SSE | 128位 | 4 | 兼容性好 |
| AVX | 256位 | 8 | **HFT推荐** |
| AVX-512 | 512位 | 16 | 最高性能 |

**HFT应用**：
1. 校验和计算
2. 数据解析
3. 价格搜索
4. 统计计算
5. 向量运算
