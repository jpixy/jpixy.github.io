+++
title = "CUDA实战应用场景详解"
date = 2026-02-06
weight = 22000
description = "CUDA能做什么：从图像处理到深度学习，从科学计算到量化交易，详解GPU加速的实际应用领域"
[taxonomies]
tags = ["cuda", "gpu", "deep-learning", "hpc", "image-processing"]
+++

## 概述

学会 CUDA 后具体能做什么？本文详细介绍 CUDA 的实际应用场景，从基础的图像处理、科学计算，到深度学习训练/推理、量化交易、密码学破解等领域，并提供每个场景的代码示例和优化思路。

---

## 一、应用场景全景

**CUDA 应用领域分布：**

| 领域 | 应用场景 |
|------|----------|
| **深度学习/AI（60%+ GPU 使用量）** | 模型训练（PyTorch/TensorFlow 底层）；模型推理加速；自定义算子开发；LLM 推理优化（FlashAttention, vLLM） |
| **科学计算与仿真** | 分子动力学（GROMACS, AMBER）；流体动力学（CFD）；天气预报；粒子物理模拟 |
| **图像与视频处理** | 图像滤波与增强；视频编解码；计算机视觉；医学图像处理 |
| **金融与量化** | 蒙特卡洛模拟；期权定价；风险计算（VaR）；高频交易信号计算 |
| **密码学与安全** | 哈希计算/密码破解；加密货币挖矿；区块链验证 |
| **图形渲染** | 光线追踪；实时渲染；VR/AR |

---

## 二、图像处理

### 2.1 图像卷积滤波

```cpp
/*
 * 图像卷积：模糊、锐化、边缘检测
 * 每个像素的计算独立 -> 天然并行
 */

#include <cuda_runtime.h>

// 高斯模糊 Kernel（5x5）
__constant__ float gaussianKernel[25] = {
    1/273.f,  4/273.f,  7/273.f,  4/273.f, 1/273.f,
    4/273.f, 16/273.f, 26/273.f, 16/273.f, 4/273.f,
    7/273.f, 26/273.f, 41/273.f, 26/273.f, 7/273.f,
    4/273.f, 16/273.f, 26/273.f, 16/273.f, 4/273.f,
    1/273.f,  4/273.f,  7/273.f,  4/273.f, 1/273.f
};

__global__ void gaussianBlur(unsigned char* input, unsigned char* output,
                             int width, int height) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (x >= width || y >= height) return;
    
    float sum = 0.0f;
    int kernelRadius = 2;
    
    for (int ky = -kernelRadius; ky <= kernelRadius; ky++) {
        for (int kx = -kernelRadius; kx <= kernelRadius; kx++) {
            int px = min(max(x + kx, 0), width - 1);
            int py = min(max(y + ky, 0), height - 1);
            
            int kernelIdx = (ky + kernelRadius) * 5 + (kx + kernelRadius);
            sum += input[py * width + px] * gaussianKernel[kernelIdx];
        }
    }
    
    output[y * width + x] = (unsigned char)sum;
}

// 使用共享内存优化版本
__global__ void gaussianBlurShared(unsigned char* input, unsigned char* output,
                                   int width, int height) {
    __shared__ unsigned char tile[20][20];  // 16x16 + 4 边界
    
    int tx = threadIdx.x;
    int ty = threadIdx.y;
    int x = blockIdx.x * blockDim.x + tx;
    int y = blockIdx.y * blockDim.y + ty;
    
    // 加载到共享内存（包括边界）
    int loadX = x - 2;
    int loadY = y - 2;
    
    for (int dy = ty; dy < 20; dy += blockDim.y) {
        for (int dx = tx; dx < 20; dx += blockDim.x) {
            int gx = min(max(blockIdx.x * blockDim.x + dx - 2, 0), width - 1);
            int gy = min(max(blockIdx.y * blockDim.y + dy - 2, 0), height - 1);
            tile[dy][dx] = input[gy * width + gx];
        }
    }
    
    __syncthreads();
    
    if (x >= width || y >= height) return;
    
    float sum = 0.0f;
    for (int ky = 0; ky < 5; ky++) {
        for (int kx = 0; kx < 5; kx++) {
            sum += tile[ty + ky][tx + kx] * gaussianKernel[ky * 5 + kx];
        }
    }
    
    output[y * width + x] = (unsigned char)sum;
}

/*
 * 性能对比（1920x1080 图像）：
 * CPU 单线程：~50ms
 * GPU 基础版：~0.5ms
 * GPU 共享内存：~0.2ms
 * 加速比：100-250x
 */
```

### 2.2 直方图计算

```cpp
/*
 * 图像直方图：统计每个灰度值的出现次数
 * 使用原子操作处理竞争
 */

// 基础版本
__global__ void histogram_basic(unsigned char* image, int* hist, int N) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        atomicAdd(&hist[image[idx]], 1);
    }
}

// 优化版本：使用共享内存减少原子操作冲突
__global__ void histogram_shared(unsigned char* image, int* hist, int N) {
    __shared__ int localHist[256];
    
    // 初始化共享内存
    int tid = threadIdx.x;
    if (tid < 256) {
        localHist[tid] = 0;
    }
    __syncthreads();
    
    // 在共享内存中累加
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    int stride = blockDim.x * gridDim.x;
    
    while (idx < N) {
        atomicAdd(&localHist[image[idx]], 1);
        idx += stride;
    }
    __syncthreads();
    
    // 合并到全局内存
    if (tid < 256) {
        atomicAdd(&hist[tid], localHist[tid]);
    }
}

// 直方图均衡化
__global__ void histogramEqualize(unsigned char* input, unsigned char* output,
                                  float* cdf, int N) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        // 使用累积分布函数映射
        output[idx] = (unsigned char)(255.0f * cdf[input[idx]]);
    }
}
```

### 2.3 边缘检测

```cpp
/*
 * Sobel 边缘检测
 */

__constant__ int sobelX[9] = {-1, 0, 1, -2, 0, 2, -1, 0, 1};
__constant__ int sobelY[9] = {-1, -2, -1, 0, 0, 0, 1, 2, 1};

__global__ void sobelEdgeDetection(unsigned char* input, unsigned char* output,
                                   int width, int height) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    
    if (x == 0 || x >= width - 1 || y == 0 || y >= height - 1) {
        if (x < width && y < height)
            output[y * width + x] = 0;
        return;
    }
    
    int gx = 0, gy = 0;
    
    for (int ky = -1; ky <= 1; ky++) {
        for (int kx = -1; kx <= 1; kx++) {
            int px = x + kx;
            int py = y + ky;
            int pixel = input[py * width + px];
            int kidx = (ky + 1) * 3 + (kx + 1);
            gx += pixel * sobelX[kidx];
            gy += pixel * sobelY[kidx];
        }
    }
    
    int magnitude = (int)sqrtf((float)(gx * gx + gy * gy));
    output[y * width + x] = (unsigned char)min(magnitude, 255);
}
```

---

## 三、科学计算

### 3.1 矩阵运算

```cpp
/*
 * 矩阵乘法：深度学习的核心运算
 * C = A * B
 */

// 基础版本
__global__ void matmul_basic(float* A, float* B, float* C, int M, int N, int K) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (row < M && col < N) {
        float sum = 0.0f;
        for (int k = 0; k < K; k++) {
            sum += A[row * K + k] * B[k * N + col];
        }
        C[row * N + col] = sum;
    }
}

// 分块优化版本（Tiled GEMM）
#define TILE_SIZE 32

__global__ void matmul_tiled(float* A, float* B, float* C, int M, int N, int K) {
    __shared__ float As[TILE_SIZE][TILE_SIZE];
    __shared__ float Bs[TILE_SIZE][TILE_SIZE];
    
    int bx = blockIdx.x, by = blockIdx.y;
    int tx = threadIdx.x, ty = threadIdx.y;
    
    int row = by * TILE_SIZE + ty;
    int col = bx * TILE_SIZE + tx;
    
    float sum = 0.0f;
    
    for (int t = 0; t < (K + TILE_SIZE - 1) / TILE_SIZE; t++) {
        // 加载 A 的一块
        if (row < M && t * TILE_SIZE + tx < K)
            As[ty][tx] = A[row * K + t * TILE_SIZE + tx];
        else
            As[ty][tx] = 0.0f;
        
        // 加载 B 的一块
        if (t * TILE_SIZE + ty < K && col < N)
            Bs[ty][tx] = B[(t * TILE_SIZE + ty) * N + col];
        else
            Bs[ty][tx] = 0.0f;
        
        __syncthreads();
        
        // 计算
        for (int k = 0; k < TILE_SIZE; k++) {
            sum += As[ty][k] * Bs[k][tx];
        }
        
        __syncthreads();
    }
    
    if (row < M && col < N) {
        C[row * N + col] = sum;
    }
}

/*
 * 性能（4096x4096 矩阵，RTX 4090）：
 * cuBLAS:        ~5ms (~26 TFLOPS)
 * 分块优化:      ~20ms (~6 TFLOPS)
 * 基础版本:      ~500ms (~0.3 TFLOPS)
 * CPU (OpenBLAS): ~2000ms
 */
```

### 3.2 蒙特卡洛模拟

```cpp
/*
 * 蒙特卡洛圆周率估算
 * 随机撒点，统计落在圆内的比例
 */

#include <curand_kernel.h>

__global__ void monteCarloPi(int* count, int samplesPerThread, 
                              unsigned long long seed) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    
    // 初始化随机数生成器
    curandState state;
    curand_init(seed, tid, 0, &state);
    
    int localCount = 0;
    
    for (int i = 0; i < samplesPerThread; i++) {
        float x = curand_uniform(&state);
        float y = curand_uniform(&state);
        
        if (x * x + y * y <= 1.0f) {
            localCount++;
        }
    }
    
    atomicAdd(count, localCount);
}

/*
 * 蒙特卡洛期权定价（Black-Scholes）
 */
__global__ void monteCarloOptionPricing(
    float S0,           // 初始股价
    float K,            // 行权价
    float r,            // 无风险利率
    float sigma,        // 波动率
    float T,            // 到期时间
    int numPaths,       // 模拟路径数
    float* payoffs,     // 输出：每条路径的收益
    unsigned long long seed
) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= numPaths) return;
    
    curandState state;
    curand_init(seed, tid, 0, &state);
    
    // 生成正态分布随机数
    float Z = curand_normal(&state);
    
    // GBM 模型：S_T = S_0 * exp((r - 0.5*sigma^2)*T + sigma*sqrt(T)*Z)
    float drift = (r - 0.5f * sigma * sigma) * T;
    float diffusion = sigma * sqrtf(T) * Z;
    float S_T = S0 * expf(drift + diffusion);
    
    // 欧式看涨期权收益
    payoffs[tid] = fmaxf(S_T - K, 0.0f);
}

// 期权价格 = exp(-r*T) * mean(payoffs)
```

### 3.3 N 体模拟

```cpp
/*
 * N 体引力模拟
 * 计算 N 个粒子之间的引力相互作用
 * 复杂度：O(N^2)，天然并行
 */

struct Body {
    float3 pos;
    float3 vel;
    float mass;
};

__global__ void nbodyForces(Body* bodies, float3* forces, int N, float dt) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= N) return;
    
    float3 force = make_float3(0.0f, 0.0f, 0.0f);
    float3 pos_i = bodies[i].pos;
    
    for (int j = 0; j < N; j++) {
        if (i == j) continue;
        
        float3 pos_j = bodies[j].pos;
        float3 r;
        r.x = pos_j.x - pos_i.x;
        r.y = pos_j.y - pos_i.y;
        r.z = pos_j.z - pos_i.z;
        
        float distSqr = r.x*r.x + r.y*r.y + r.z*r.z + 1e-9f;  // 软化因子
        float invDist = rsqrtf(distSqr);
        float invDist3 = invDist * invDist * invDist;
        
        float f = bodies[j].mass * invDist3;
        force.x += f * r.x;
        force.y += f * r.y;
        force.z += f * r.z;
    }
    
    forces[i] = force;
}

// 使用共享内存优化
__global__ void nbodyForcesShared(Body* bodies, float3* forces, int N) {
    extern __shared__ Body sharedBodies[];
    
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    float3 force = make_float3(0.0f, 0.0f, 0.0f);
    float3 pos_i = (i < N) ? bodies[i].pos : make_float3(0, 0, 0);
    
    // 分块处理
    for (int tile = 0; tile < gridDim.x; tile++) {
        int idx = tile * blockDim.x + threadIdx.x;
        if (idx < N) {
            sharedBodies[threadIdx.x] = bodies[idx];
        }
        __syncthreads();
        
        // 计算与这一块的相互作用
        for (int j = 0; j < blockDim.x && tile * blockDim.x + j < N; j++) {
            // ... 计算引力
        }
        __syncthreads();
    }
    
    if (i < N) forces[i] = force;
}
```

---

## 四、深度学习

### 4.1 自定义算子

```cpp
/*
 * PyTorch CUDA Extension 示例
 * 实现自定义激活函数
 */

// my_activation.cu
#include <torch/extension.h>
#include <cuda_runtime.h>

// CUDA Kernel
__global__ void swish_forward_kernel(
    const float* __restrict__ input,
    float* __restrict__ output,
    int size
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float x = input[idx];
        output[idx] = x / (1.0f + expf(-x));  // Swish: x * sigmoid(x)
    }
}

__global__ void swish_backward_kernel(
    const float* __restrict__ input,
    const float* __restrict__ grad_output,
    float* __restrict__ grad_input,
    int size
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        float x = input[idx];
        float sigmoid_x = 1.0f / (1.0f + expf(-x));
        float swish = x * sigmoid_x;
        // d(swish)/dx = sigmoid(x) + swish * (1 - sigmoid(x))
        grad_input[idx] = grad_output[idx] * 
                          (sigmoid_x + swish * (1.0f - sigmoid_x));
    }
}

// C++ 接口
torch::Tensor swish_forward(torch::Tensor input) {
    auto output = torch::empty_like(input);
    int size = input.numel();
    int threads = 256;
    int blocks = (size + threads - 1) / threads;
    
    swish_forward_kernel<<<blocks, threads>>>(
        input.data_ptr<float>(),
        output.data_ptr<float>(),
        size
    );
    
    return output;
}

torch::Tensor swish_backward(torch::Tensor input, torch::Tensor grad_output) {
    auto grad_input = torch::empty_like(input);
    int size = input.numel();
    int threads = 256;
    int blocks = (size + threads - 1) / threads;
    
    swish_backward_kernel<<<blocks, threads>>>(
        input.data_ptr<float>(),
        grad_output.data_ptr<float>(),
        grad_input.data_ptr<float>(),
        size
    );
    
    return grad_input;
}

// 绑定到 Python
PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("forward", &swish_forward, "Swish forward");
    m.def("backward", &swish_backward, "Swish backward");
}
```

```python
# setup.py
from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

setup(
    name='my_activation',
    ext_modules=[
        CUDAExtension('my_activation', [
            'my_activation.cu',
        ])
    ],
    cmdclass={'build_ext': BuildExtension}
)

# 使用
import torch
import my_activation

class SwishFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, input):
        ctx.save_for_backward(input)
        return my_activation.forward(input)
    
    @staticmethod
    def backward(ctx, grad_output):
        input, = ctx.saved_tensors
        return my_activation.backward(input, grad_output)

swish = SwishFunction.apply
```

### 4.2 卷积实现

```cpp
/*
 * 直接卷积 Kernel（教学用，实际用 cuDNN）
 */

__global__ void conv2d_direct(
    const float* input,   // [N, C_in, H, W]
    const float* weight,  // [C_out, C_in, KH, KW]
    float* output,        // [N, C_out, H_out, W_out]
    int N, int C_in, int H, int W,
    int C_out, int KH, int KW,
    int stride, int padding
) {
    int n = blockIdx.z;
    int c_out = blockIdx.y;
    int h_out = blockIdx.x * blockDim.y + threadIdx.y;
    int w_out = threadIdx.x;
    
    int H_out = (H + 2 * padding - KH) / stride + 1;
    int W_out = (W + 2 * padding - KW) / stride + 1;
    
    if (h_out >= H_out || w_out >= W_out) return;
    
    float sum = 0.0f;
    
    for (int c_in = 0; c_in < C_in; c_in++) {
        for (int kh = 0; kh < KH; kh++) {
            for (int kw = 0; kw < KW; kw++) {
                int h_in = h_out * stride + kh - padding;
                int w_in = w_out * stride + kw - padding;
                
                if (h_in >= 0 && h_in < H && w_in >= 0 && w_in < W) {
                    int input_idx = n * C_in * H * W + c_in * H * W + 
                                   h_in * W + w_in;
                    int weight_idx = c_out * C_in * KH * KW + 
                                    c_in * KH * KW + kh * KW + kw;
                    sum += input[input_idx] * weight[weight_idx];
                }
            }
        }
    }
    
    int output_idx = n * C_out * H_out * W_out + 
                     c_out * H_out * W_out + h_out * W_out + w_out;
    output[output_idx] = sum;
}

/*
 * 实际应用中使用 cuDNN
 */
#include <cudnn.h>

// cuDNN 卷积设置（伪代码）
cudnnConvolutionForward(
    cudnnHandle,
    &alpha,
    inputDesc, inputData,
    filterDesc, filterData,
    convDesc,
    algo,  // 自动选择最快算法
    workspace, workspaceSize,
    &beta,
    outputDesc, outputData
);
```

### 4.3 Softmax 实现

```cpp
/*
 * Softmax 实现
 * softmax(x_i) = exp(x_i) / sum(exp(x_j))
 */

// 数值稳定版本：先减最大值
__global__ void softmax(float* input, float* output, int N, int D) {
    extern __shared__ float shared[];
    
    int row = blockIdx.x;
    int tid = threadIdx.x;
    
    float* row_data = input + row * D;
    float* row_out = output + row * D;
    
    // 1. 找最大值（归约）
    float max_val = -INFINITY;
    for (int i = tid; i < D; i += blockDim.x) {
        max_val = fmaxf(max_val, row_data[i]);
    }
    shared[tid] = max_val;
    __syncthreads();
    
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            shared[tid] = fmaxf(shared[tid], shared[tid + s]);
        }
        __syncthreads();
    }
    max_val = shared[0];
    
    // 2. 计算 exp 和 sum
    float sum = 0.0f;
    for (int i = tid; i < D; i += blockDim.x) {
        float exp_val = expf(row_data[i] - max_val);
        row_out[i] = exp_val;
        sum += exp_val;
    }
    shared[tid] = sum;
    __syncthreads();
    
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            shared[tid] += shared[tid + s];
        }
        __syncthreads();
    }
    sum = shared[0];
    
    // 3. 归一化
    for (int i = tid; i < D; i += blockDim.x) {
        row_out[i] /= sum;
    }
}
```

---

## 五、金融量化

### 5.1 期权定价

```cpp
/*
 * Black-Scholes 欧式期权定价
 * 批量计算大量期权
 */

__device__ float normalCDF(float x) {
    return 0.5f * erfcf(-x * M_SQRT1_2);
}

__global__ void blackScholes(
    float* callPrices,
    float* putPrices,
    const float* S,      // 股价
    const float* K,      // 行权价
    const float* T,      // 到期时间
    const float* r,      // 利率
    const float* sigma,  // 波动率
    int N
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N) return;
    
    float s = S[idx];
    float k = K[idx];
    float t = T[idx];
    float rate = r[idx];
    float vol = sigma[idx];
    
    float sqrtT = sqrtf(t);
    float d1 = (logf(s / k) + (rate + 0.5f * vol * vol) * t) / (vol * sqrtT);
    float d2 = d1 - vol * sqrtT;
    
    float Nd1 = normalCDF(d1);
    float Nd2 = normalCDF(d2);
    float Nmd1 = normalCDF(-d1);
    float Nmd2 = normalCDF(-d2);
    
    float discount = expf(-rate * t);
    
    callPrices[idx] = s * Nd1 - k * discount * Nd2;
    putPrices[idx] = k * discount * Nmd2 - s * Nmd1;
}

/*
 * 性能：可同时计算数百万个期权价格
 * GPU：~1ms for 1M options
 * CPU：~100ms for 1M options
 */
```

### 5.2 风险计算 (VaR)

```cpp
/*
 * Value at Risk 蒙特卡洛计算
 */

__global__ void simulatePortfolioReturns(
    float* returns,          // 输出：模拟的收益
    const float* weights,    // 资产权重
    const float* mean,       // 资产收益均值
    const float* cholL,      // 协方差矩阵的 Cholesky 分解
    int numAssets,
    int numSimulations,
    unsigned long long seed
) {
    int simIdx = blockIdx.x * blockDim.x + threadIdx.x;
    if (simIdx >= numSimulations) return;
    
    curandState state;
    curand_init(seed, simIdx, 0, &state);
    
    // 生成相关的正态随机数
    float* z = (float*)malloc(numAssets * sizeof(float));
    float* correlated = (float*)malloc(numAssets * sizeof(float));
    
    for (int i = 0; i < numAssets; i++) {
        z[i] = curand_normal(&state);
    }
    
    // 使用 Cholesky 分解生成相关变量
    for (int i = 0; i < numAssets; i++) {
        correlated[i] = mean[i];
        for (int j = 0; j <= i; j++) {
            correlated[i] += cholL[i * numAssets + j] * z[j];
        }
    }
    
    // 计算组合收益
    float portfolioReturn = 0.0f;
    for (int i = 0; i < numAssets; i++) {
        portfolioReturn += weights[i] * correlated[i];
    }
    
    returns[simIdx] = portfolioReturn;
    
    free(z);
    free(correlated);
}

// 排序后取分位数得到 VaR
```

---

## 六、密码学

### 6.1 并行哈希计算

```cpp
/*
 * SHA-256 并行计算
 * 用于密码破解、区块链挖矿等
 */

// SHA-256 常量
__constant__ uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    // ... (省略其他常量)
};

__device__ uint32_t rotr(uint32_t x, int n) {
    return (x >> n) | (x << (32 - n));
}

__device__ void sha256_transform(uint32_t* state, const uint32_t* block) {
    uint32_t W[64];
    
    // 消息扩展
    for (int i = 0; i < 16; i++) {
        W[i] = block[i];
    }
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = rotr(W[i-15], 7) ^ rotr(W[i-15], 18) ^ (W[i-15] >> 3);
        uint32_t s1 = rotr(W[i-2], 17) ^ rotr(W[i-2], 19) ^ (W[i-2] >> 10);
        W[i] = W[i-16] + s0 + W[i-7] + s1;
    }
    
    // 压缩函数
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3];
    uint32_t e = state[4], f = state[5], g = state[6], h = state[7];
    
    for (int i = 0; i < 64; i++) {
        uint32_t S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + S1 + ch + K[i] + W[i];
        uint32_t S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = S0 + maj;
        
        h = g; g = f; f = e; e = d + temp1;
        d = c; c = b; b = a; a = temp1 + temp2;
    }
    
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

// 密码暴力破解
__global__ void bruteForcePassword(
    const uint32_t* targetHash,
    char* foundPassword,
    int* found,
    uint64_t startIdx,
    uint64_t endIdx
) {
    uint64_t idx = startIdx + blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= endIdx || *found) return;
    
    // 生成候选密码
    char password[8];
    // ... 根据 idx 生成密码
    
    // 计算 SHA-256
    uint32_t hash[8];
    sha256(password, hash);
    
    // 比较
    bool match = true;
    for (int i = 0; i < 8; i++) {
        if (hash[i] != targetHash[i]) {
            match = false;
            break;
        }
    }
    
    if (match) {
        atomicExch(found, 1);
        memcpy(foundPassword, password, 8);
    }
}
```

---

## 七、视频处理

### 7.1 视频帧处理

```cpp
/*
 * 视频处理流水线
 * 解码 -> GPU 处理 -> 编码
 */

#include <npp.h>  // NVIDIA Performance Primitives

// 使用 NPP 进行颜色空间转换
void processVideoFrame(
    Npp8u* d_inputNV12,    // NV12 格式输入
    Npp8u* d_outputRGB,    // RGB 输出
    int width, int height
) {
    NppiSize roi = {width, height};
    
    // NV12 -> RGB
    nppiNV12ToRGB_8u_P2C3R(
        d_inputNV12,
        d_inputNV12 + width * height,
        width,
        d_outputRGB,
        width * 3,
        roi
    );
}

// 视频缩放
void scaleVideo(
    Npp8u* d_src, int srcWidth, int srcHeight,
    Npp8u* d_dst, int dstWidth, int dstHeight
) {
    NppiSize srcSize = {srcWidth, srcHeight};
    NppiRect srcRoi = {0, 0, srcWidth, srcHeight};
    NppiSize dstSize = {dstWidth, dstHeight};
    NppiRect dstRoi = {0, 0, dstWidth, dstHeight};
    
    nppiResize_8u_C3R(
        d_src, srcWidth * 3, srcSize, srcRoi,
        d_dst, dstWidth * 3, dstSize, dstRoi,
        NPPI_INTER_LINEAR
    );
}
```

---

## 八、数据库与搜索

### 8.1 GPU 加速查询

```cpp
/*
 * 并行过滤与聚合
 */

// WHERE 条件过滤
__global__ void filterKernel(
    const int* column,
    const int threshold,
    int* mask,
    int N
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < N) {
        mask[idx] = (column[idx] > threshold) ? 1 : 0;
    }
}

// SUM 聚合
__global__ void sumReduction(
    const float* data,
    const int* mask,
    float* result,
    int N
) {
    extern __shared__ float sdata[];
    
    int tid = threadIdx.x;
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    sdata[tid] = (idx < N && mask[idx]) ? data[idx] : 0.0f;
    __syncthreads();
    
    // 树形归约
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            sdata[tid] += sdata[tid + s];
        }
        __syncthreads();
    }
    
    if (tid == 0) {
        atomicAdd(result, sdata[0]);
    }
}

/*
 * 实际应用：
 * - RAPIDS cuDF（GPU DataFrame）
 * - BlazingSQL（GPU SQL 引擎）
 * - 百亿级数据秒级查询
 */
```

---

## 九、应用选择指南

**CUDA 应用场景适用性评估：**

| 适用程度 | 加速比 | 场景 |
|----------|--------|------|
| **非常适合** | 10x-1000x | 矩阵运算（大规模线性代数）；图像/视频（像素级独立处理）；蒙特卡洛（大量独立随机模拟）；深度学习（训练和推理）；信号处理（FFT、滤波） |
| **适合** | 2x-10x | 图遍历（有一定并行度）；排序（并行排序算法）；压缩/解压（某些算法可并行） |
| **不太适合** | - | 串行依赖强的算法；小数据量任务（传输开销大于计算收益）；大量分支的控制流；频繁的 CPU-GPU 数据交换 |

**判断标准：**
- 计算密集 vs 内存密集？
- 数据并行度如何？
- 数据量是否足够大？
- 算法是否有大量分支？

---

## 十、下一步学习

掌握 CUDA 应用后，继续深入：

1. **AI 底层开发路线** - 不做调参，深入原理
2. **GPU Kernel 开发进阶** - 高性能 Kernel 编写
3. **FlashAttention 原理** - LLM 推理核心优化

---

## 相关文章

- [上一篇：21 - CUDA 入门与 GPU 编程基础](@/articles/ai/ai-21-CUDA入门与GPU编程基础.md)
- [下一篇：23 - AI 底层开发路线图](@/articles/ai/ai-23-AI底层开发路线图.md)
- [16 - 推理框架优化技术详解](@/articles/ai/ai-16-推理框架优化技术详解.md)
- [14 - 分布式训练优化详解](@/articles/ai/ai-14-分布式训练优化详解.md)
