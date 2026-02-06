+++
title = "23.AI底层开发路线图"
date = 2026-02-06
description = "不做调参侠：如何深入AI底层原理，从框架源码到Kernel开发，成为真正的AI系统工程师"
[taxonomies]
tags = ["cuda", "ai-infra", "deep-learning", "kernel", "career"]
+++

## 概述

很多人学 AI 停留在调用 API、写 Prompt、调参数的层面。如果你不想只做"AI 应用层"的工作，而是希望深入底层原理、理解训练和推理的本质、甚至能优化框架和写 Kernel，本文将为你提供一条系统的学习路线。

---

## 一、AI 技术栈全景

### 1.1 从应用到硬件

```
AI 技术栈层次：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  应用层（你不想只停在这里）                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━                                         │
│  • Prompt Engineering                                               │
│  • LangChain / LlamaIndex                                           │
│  • RAG 应用                                                         │
│  • 微调 API 调用                                                    │
│                                                                      │
│  ════════════════════════════════════════════════════════════════   │
│                                                                      │
│  框架层（开始深入）                                                  │
│  ━━━━━━━━━━━━━━━━━                                                  │
│  • PyTorch / TensorFlow 使用                                        │
│  • 模型训练与微调                                                   │
│  • 分布式训练配置                                                   │
│                                                                      │
│  ════════════════════════════════════════════════════════════════   │
│                                                                      │
│  框架内核层（真正的深入）                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━                                            │
│  • PyTorch 源码理解                                                 │
│  • 自动微分机制                                                     │
│  • 算子调度系统                                                     │
│  • 编译优化（TorchScript, torch.compile）                           │
│                                                                      │
│  ════════════════════════════════════════════════════════════════   │
│                                                                      │
│  运行时层（AI Infra 核心）                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━                                           │
│  • CUDA Runtime                                                     │
│  • cuDNN / cuBLAS                                                   │
│  • TensorRT / vLLM                                                  │
│  • NCCL（分布式通信）                                               │
│                                                                      │
│  ════════════════════════════════════════════════════════════════   │
│                                                                      │
│  Kernel 层（最底层开发）                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━                                             │
│  • CUDA Kernel 开发                                                 │
│  • Tensor Core 编程                                                 │
│  • 内存优化                                                         │
│  • FlashAttention / CUTLASS                                         │
│                                                                      │
│  ════════════════════════════════════════════════════════════════   │
│                                                                      │
│  硬件层                                                              │
│  ━━━━━━                                                             │
│  • GPU 架构（SM, Warp, Memory Hierarchy）                           │
│  • Tensor Core / RT Core                                            │
│  • NVLink / PCIe                                                    │
│  • 多 GPU / 多节点                                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 不同层次的技能要求

```
各层次技能对比：

┌──────────────┬─────────────────────────────────────────────────────┐
│ 层次         │ 核心技能                                            │
├──────────────┼─────────────────────────────────────────────────────┤
│ 应用层       │ Python, API 调用, Prompt 设计                       │
├──────────────┼─────────────────────────────────────────────────────┤
│ 框架使用层   │ PyTorch/TF, 模型设计, 训练技巧                      │
├──────────────┼─────────────────────────────────────────────────────┤
│ 框架内核层   │ C++, PyTorch internals, 编译器, 自动微分            │
├──────────────┼─────────────────────────────────────────────────────┤
│ 运行时层     │ CUDA, cuDNN API, 分布式系统, 性能分析               │
├──────────────┼─────────────────────────────────────────────────────┤
│ Kernel 层    │ CUDA Kernel, 汇编, GPU 架构, 性能优化               │
├──────────────┼─────────────────────────────────────────────────────┤
│ 硬件层       │ 计算机体系结构, 芯片设计                            │
└──────────────┴─────────────────────────────────────────────────────┘

薪资与稀缺度：
• 应用层：供给充足，竞争激烈
• 框架使用层：中等需求
• 框架内核/运行时：稀缺，高薪
• Kernel 层：极度稀缺，顶薪
```

---

## 二、底层开发学习路线

### 2.1 阶段规划

```
AI 底层开发学习路线（1-2 年）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  阶段 1：基础巩固（1-2 个月）                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                        │
│  目标：确保编程基础扎实                                             │
│                                                                      │
│  □ C++ 进阶（模板、内存管理、性能优化）                            │
│  □ 线性代数复习（矩阵运算、特征值、SVD）                           │
│  □ 计算机体系结构（缓存、流水线、SIMD）                            │
│  □ PyTorch 熟练使用（不只是调 API）                                │
│                                                                      │
│  阶段 2：CUDA 入门（2-3 个月）                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                        │
│  目标：能写基础 CUDA Kernel                                         │
│                                                                      │
│  □ GPU 架构理解（SM、Warp、内存层次）                              │
│  □ CUDA 编程模型（Grid/Block/Thread）                              │
│  □ 内存管理（Global、Shared、Constant）                            │
│  □ 同步与原子操作                                                  │
│  □ 实现：向量加法、矩阵乘法、归约                                  │
│                                                                      │
│  阶段 3：深度学习原理（2-3 个月）                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                    │
│  目标：从底层理解训练过程                                           │
│                                                                      │
│  □ 反向传播手动推导与实现                                          │
│  □ 自动微分原理与实现                                              │
│  □ 优化器实现（SGD、Adam 从头写）                                  │
│  □ 各类层的前向/反向实现                                           │
│  □ 不使用框架训练 MNIST                                            │
│                                                                      │
│  阶段 4：PyTorch 源码（3-4 个月）                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                      │
│  目标：理解框架如何工作                                             │
│                                                                      │
│  □ PyTorch 架构总览（Python/C++/CUDA 层）                          │
│  □ Tensor 实现（Storage、Stride、View）                            │
│  □ Autograd 引擎                                                   │
│  □ 算子分发机制（Dispatcher）                                      │
│  □ 自定义 C++/CUDA Extension                                       │
│                                                                      │
│  阶段 5：Kernel 优化（3-4 个月）                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                       │
│  目标：写出高性能 Kernel                                            │
│                                                                      │
│  □ 性能分析工具（Nsight, roofline）                                │
│  □ 内存访问优化（合并、Bank Conflict）                             │
│  □ 指令级优化（ILP、循环展开）                                     │
│  □ Tensor Core 编程                                                │
│  □ 学习 CUTLASS / FlashAttention 源码                              │
│                                                                      │
│  阶段 6：推理优化（2-3 个月）                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                        │
│  目标：掌握 LLM 推理优化                                            │
│                                                                      │
│  □ 量化原理与实现                                                  │
│  □ KV Cache 优化                                                   │
│  □ FlashAttention 原理与实现                                       │
│  □ PagedAttention / vLLM 源码                                      │
│  □ TensorRT / ONNX Runtime                                         │
│                                                                      │
│  阶段 7：分布式训练（2-3 个月）                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                      │
│  目标：理解大规模训练                                               │
│                                                                      │
│  □ 数据并行、模型并行、流水线并行                                  │
│  □ NCCL 通信原语                                                   │
│  □ ZeRO 优化                                                       │
│  □ Megatron-LM / DeepSpeed 源码                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 具体学习任务

```
每个阶段的具体任务：

阶段 2 - CUDA 入门任务：
━━━━━━━━━━━━━━━━━━━━━━━━
1. 从头实现向量加法 Kernel
2. 实现矩阵乘法（基础版 → 共享内存版 → 分块版）
3. 实现并行归约（求和、求最大值）
4. 实现直方图（使用原子操作）
5. 使用 Nsight 分析自己的 Kernel

阶段 3 - 深度学习原理任务：
━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 手动实现计算图和自动微分
2. 从头实现全连接层（前向 + 反向）
3. 从头实现卷积层（im2col 方法）
4. 从头实现 BatchNorm
5. 从头实现 Attention
6. 不用框架训练 MNIST 到 98%+

阶段 4 - PyTorch 源码任务：
━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 阅读 Tensor 类源码
2. 追踪一个算子的完整调用链
3. 实现一个自定义算子（Python → C++ → CUDA）
4. 理解 torch.compile 的工作原理
5. 给 PyTorch 提交一个 PR（文档或小 bug fix）

阶段 5 - Kernel 优化任务：
━━━━━━━━━━━━━━━━━━━━━━━━━
1. 用 CUTLASS 实现矩阵乘法
2. 实现 Softmax Kernel（数值稳定版）
3. 实现 LayerNorm Kernel
4. 阅读 FlashAttention 论文和源码
5. 尝试复现 FlashAttention 的简化版本
```

---

## 三、核心知识详解

### 3.1 自动微分实现

```python
"""
从头实现自动微分引擎
理解 PyTorch Autograd 的本质
"""

import numpy as np

class Tensor:
    def __init__(self, data, requires_grad=False, _children=(), _op=''):
        self.data = np.array(data, dtype=np.float32)
        self.requires_grad = requires_grad
        self.grad = None
        self._backward = lambda: None
        self._prev = set(_children)
        self._op = _op
    
    def __repr__(self):
        return f"Tensor({self.data}, requires_grad={self.requires_grad})"
    
    def __add__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data + other.data, 
                     requires_grad=self.requires_grad or other.requires_grad,
                     _children=(self, other), _op='+')
        
        def _backward():
            if self.requires_grad:
                self.grad = (self.grad or 0) + out.grad
            if other.requires_grad:
                other.grad = (other.grad or 0) + out.grad
        out._backward = _backward
        
        return out
    
    def __mul__(self, other):
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data * other.data,
                     requires_grad=self.requires_grad or other.requires_grad,
                     _children=(self, other), _op='*')
        
        def _backward():
            if self.requires_grad:
                self.grad = (self.grad or 0) + other.data * out.grad
            if other.requires_grad:
                other.grad = (other.grad or 0) + self.data * out.grad
        out._backward = _backward
        
        return out
    
    def __matmul__(self, other):
        """矩阵乘法"""
        out = Tensor(self.data @ other.data,
                     requires_grad=self.requires_grad or other.requires_grad,
                     _children=(self, other), _op='@')
        
        def _backward():
            if self.requires_grad:
                self.grad = (self.grad or 0) + out.grad @ other.data.T
            if other.requires_grad:
                other.grad = (other.grad or 0) + self.data.T @ out.grad
        out._backward = _backward
        
        return out
    
    def relu(self):
        out = Tensor(np.maximum(0, self.data),
                     requires_grad=self.requires_grad,
                     _children=(self,), _op='relu')
        
        def _backward():
            if self.requires_grad:
                self.grad = (self.grad or 0) + (self.data > 0) * out.grad
        out._backward = _backward
        
        return out
    
    def sum(self):
        out = Tensor(self.data.sum(),
                     requires_grad=self.requires_grad,
                     _children=(self,), _op='sum')
        
        def _backward():
            if self.requires_grad:
                self.grad = (self.grad or 0) + np.ones_like(self.data) * out.grad
        out._backward = _backward
        
        return out
    
    def backward(self):
        """反向传播"""
        # 拓扑排序
        topo = []
        visited = set()
        
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)
        
        build_topo(self)
        
        # 反向传播
        self.grad = np.ones_like(self.data)
        for node in reversed(topo):
            node._backward()


# 使用示例
x = Tensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
w = Tensor([[0.1, 0.2], [0.3, 0.4]], requires_grad=True)

y = x @ w
z = y.relu()
loss = z.sum()

loss.backward()

print("x.grad:", x.grad)
print("w.grad:", w.grad)
```

### 3.2 从头实现神经网络层

```python
"""
不使用 PyTorch 实现神经网络层
"""

class Linear:
    """全连接层"""
    def __init__(self, in_features, out_features):
        # Xavier 初始化
        self.weight = Tensor(
            np.random.randn(in_features, out_features) * np.sqrt(2.0 / in_features),
            requires_grad=True
        )
        self.bias = Tensor(np.zeros(out_features), requires_grad=True)
    
    def __call__(self, x):
        return x @ self.weight + self.bias
    
    def parameters(self):
        return [self.weight, self.bias]


class BatchNorm:
    """批归一化"""
    def __init__(self, num_features, eps=1e-5, momentum=0.1):
        self.gamma = Tensor(np.ones(num_features), requires_grad=True)
        self.beta = Tensor(np.zeros(num_features), requires_grad=True)
        self.eps = eps
        self.momentum = momentum
        self.running_mean = np.zeros(num_features)
        self.running_var = np.ones(num_features)
    
    def __call__(self, x, training=True):
        if training:
            mean = x.data.mean(axis=0)
            var = x.data.var(axis=0)
            
            # 更新 running statistics
            self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * mean
            self.running_var = (1 - self.momentum) * self.running_var + self.momentum * var
        else:
            mean = self.running_mean
            var = self.running_var
        
        # 归一化
        x_norm = (x.data - mean) / np.sqrt(var + self.eps)
        out = Tensor(self.gamma.data * x_norm + self.beta.data, requires_grad=True)
        
        # 需要手动实现反向传播...
        return out


class Softmax:
    """数值稳定的 Softmax"""
    def __call__(self, x):
        # 减去最大值避免数值溢出
        exp_x = np.exp(x.data - x.data.max(axis=-1, keepdims=True))
        return Tensor(exp_x / exp_x.sum(axis=-1, keepdims=True))


class CrossEntropyLoss:
    """交叉熵损失"""
    def __call__(self, logits, targets):
        # Softmax + NLLLoss
        probs = np.exp(logits.data - logits.data.max(axis=-1, keepdims=True))
        probs /= probs.sum(axis=-1, keepdims=True)
        
        n = logits.data.shape[0]
        loss = -np.log(probs[np.arange(n), targets] + 1e-9).mean()
        
        # 梯度: probs - one_hot(targets)
        out = Tensor(loss, requires_grad=True, _children=(logits,))
        
        def _backward():
            grad = probs.copy()
            grad[np.arange(n), targets] -= 1
            grad /= n
            logits.grad = (logits.grad or 0) + grad * out.grad
        out._backward = _backward
        
        return out
```

### 3.3 理解 PyTorch 算子调度

```cpp
/*
 * PyTorch 算子调度机制简化示例
 * 理解如何从 Python 调用到 CUDA Kernel
 */

// 1. Python 层
// torch.add(a, b) 
// ↓

// 2. Python 绑定层 (torch/csrc/autograd/generated/python_variable_methods.cpp)
static PyObject* THPVariable_add(PyObject* self, PyObject* args) {
    // 解析参数
    // 调用 C++ 函数
    return wrap(torch::add(tensor1, tensor2));
}

// 3. C++ 算子层 (aten/src/ATen/native/BinaryOps.cpp)
Tensor add(const Tensor& self, const Tensor& other) {
    // 类型检查、广播处理
    Tensor result = empty_like(self);
    add_stub(kCPU, result, self, other);  // 分发
    return result;
}

// 4. 分发器 (aten/src/ATen/native/DispatchStub.h)
// 根据设备类型选择具体实现
DECLARE_DISPATCH(add_fn, add_stub);
REGISTER_DISPATCH(add_stub, &add_kernel);  // CPU
REGISTER_CUDA_DISPATCH(add_stub, &add_kernel_cuda);  // CUDA

// 5. CUDA Kernel 层 (aten/src/ATen/native/cuda/BinaryAddSubKernel.cu)
void add_kernel_cuda(Tensor& result, const Tensor& self, const Tensor& other) {
    // 调用实际的 CUDA Kernel
    AT_DISPATCH_ALL_TYPES(self.scalar_type(), "add_cuda", [&] {
        add_kernel<scalar_t><<<blocks, threads>>>(
            result.data_ptr<scalar_t>(),
            self.data_ptr<scalar_t>(),
            other.data_ptr<scalar_t>(),
            self.numel()
        );
    });
}

// 6. CUDA Kernel
template <typename T>
__global__ void add_kernel(T* result, const T* a, const T* b, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        result[idx] = a[idx] + b[idx];
    }
}
```

---

## 四、必读论文与源码

### 4.1 必读论文

```
AI 底层必读论文：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  基础算法                                                            │
│  ━━━━━━━━                                                           │
│  □ Attention Is All You Need (Transformer)                         │
│  □ BERT / GPT 系列论文                                              │
│  □ Adam 优化器论文                                                  │
│  □ Batch Normalization / Layer Normalization                        │
│                                                                      │
│  推理优化                                                            │
│  ━━━━━━━━                                                           │
│  □ FlashAttention (1 & 2)                                           │
│  □ PagedAttention (vLLM)                                            │
│  □ Quantization 相关论文 (GPTQ, AWQ, SmoothQuant)                   │
│  □ Speculative Decoding                                             │
│                                                                      │
│  分布式训练                                                          │
│  ━━━━━━━━━━                                                         │
│  □ Data Parallelism 经典论文                                        │
│  □ Megatron-LM (模型并行)                                           │
│  □ ZeRO (DeepSpeed)                                                 │
│  □ GPipe / PipeDream (流水线并行)                                   │
│                                                                      │
│  Kernel 优化                                                         │
│  ━━━━━━━━━━━                                                        │
│  □ CUTLASS 文档                                                     │
│  □ Roofline Model                                                   │
│  □ Tensor Core 相关资料                                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 必读源码

```
源码阅读优先级：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ★★★★★ 最高优先级                                                   │
│  ━━━━━━━━━━━━━━━━━                                                  │
│  • PyTorch (pytorch/pytorch)                                        │
│    - torch/csrc/autograd/        # 自动微分                         │
│    - aten/src/ATen/native/       # 算子实现                         │
│    - aten/src/ATen/native/cuda/  # CUDA 算子                        │
│                                                                      │
│  • FlashAttention (Dao-AILab/flash-attention)                       │
│    - csrc/flash_attn/            # 核心 Kernel                      │
│                                                                      │
│  ★★★★ 高优先级                                                      │
│  ━━━━━━━━━━━━━━━                                                    │
│  • vLLM (vllm-project/vllm)                                         │
│    - vllm/attention/             # PagedAttention                   │
│    - csrc/                       # CUDA Kernel                      │
│                                                                      │
│  • CUTLASS (NVIDIA/cutlass)                                         │
│    - include/cutlass/gemm/       # GEMM 实现                        │
│                                                                      │
│  ★★★ 中优先级                                                       │
│  ━━━━━━━━━━━━━━                                                     │
│  • DeepSpeed (microsoft/DeepSpeed)                                  │
│    - deepspeed/runtime/          # ZeRO 实现                        │
│                                                                      │
│  • Megatron-LM (NVIDIA/Megatron-LM)                                 │
│    - megatron/core/              # 模型并行                         │
│                                                                      │
│  • llama.cpp (ggerganov/llama.cpp)                                  │
│    - ggml-cuda.cu                # CPU/GPU 推理                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 五、实战项目建议

### 5.1 入门项目

```
入门级项目（1-2 周）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  项目 1：CUDA 矩阵乘法优化                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━                                         │
│  • 实现基础版本                                                     │
│  • 添加共享内存优化                                                 │
│  • 实现分块算法                                                     │
│  • 与 cuBLAS 对比性能                                               │
│  • 使用 Nsight 分析优化                                             │
│                                                                      │
│  项目 2：从头实现 Autograd                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━                                          │
│  • 实现 Tensor 类                                                   │
│  • 实现计算图构建                                                   │
│  • 实现反向传播                                                     │
│  • 支持基本运算（加减乘除、矩阵乘）                                 │
│  • 训练一个简单网络                                                 │
│                                                                      │
│  项目 3：MNIST 从头训练                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━                                            │
│  • 不使用 PyTorch/TensorFlow                                        │
│  • 手动实现全连接层                                                 │
│  • 手动实现反向传播                                                 │
│  • 手动实现 SGD/Adam                                                │
│  • 达到 98%+ 准确率                                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 进阶项目

```
进阶项目（1-2 月）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  项目 4：PyTorch CUDA Extension                                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                      │
│  • 实现自定义激活函数                                               │
│  • 实现自定义 LayerNorm                                             │
│  • 前向 + 反向 CUDA Kernel                                          │
│  • 与 PyTorch 原生对比性能                                          │
│  • 发布到 PyPI                                                      │
│                                                                      │
│  项目 5：简化版 FlashAttention                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                       │
│  • 理解 FlashAttention 论文                                         │
│  • 实现分块 Attention 计算                                          │
│  • 实现 Online Softmax                                              │
│  • 处理 Causal Mask                                                 │
│  • 与 PyTorch Attention 对比                                        │
│                                                                      │
│  项目 6：LLM 推理引擎                                               │
│  ━━━━━━━━━━━━━━━━━━━━━━                                             │
│  • 实现 KV Cache                                                    │
│  • 实现 Continuous Batching                                         │
│  • 支持 INT8 量化推理                                               │
│  • 与 vLLM/TGI 对比性能                                             │
│                                                                      │
│  项目 7：分布式训练框架                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━                                           │
│  • 实现 Data Parallel                                               │
│  • 实现 AllReduce                                                   │
│  • 实现梯度累积                                                     │
│  • 多 GPU 训练 GPT-2                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 开源贡献

```
开源贡献路径：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  入门级（文档、测试）                                                │
│  ━━━━━━━━━━━━━━━━━━━                                                │
│  • 修复文档 typo                                                    │
│  • 补充测试用例                                                     │
│  • 改进错误信息                                                     │
│                                                                      │
│  中级（Bug 修复）                                                    │
│  ━━━━━━━━━━━━━━━━                                                   │
│  • 修复 GitHub Issues                                               │
│  • 性能小优化                                                       │
│  • 边界情况处理                                                     │
│                                                                      │
│  高级（新特性）                                                      │
│  ━━━━━━━━━━━━━━                                                     │
│  • 新算子实现                                                       │
│  • 性能优化 PR                                                      │
│  • 新功能开发                                                       │
│                                                                      │
│  推荐项目：                                                          │
│  • PyTorch (复杂但影响力大)                                         │
│  • vLLM (活跃，需求多)                                              │
│  • llama.cpp (代码量适中)                                           │
│  • Triton (编译器，有趣)                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 六、职业路径

### 6.1 岗位类型

```
AI 底层相关岗位：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  AI Infra Engineer                                                  │
│  ━━━━━━━━━━━━━━━━━━━                                                │
│  • 训练/推理平台搭建                                                │
│  • GPU 集群管理                                                     │
│  • 分布式训练优化                                                   │
│  • 模型部署上线                                                     │
│  薪资：50-100W+ RMB                                                 │
│                                                                      │
│  GPU Kernel Engineer                                                │
│  ━━━━━━━━━━━━━━━━━━━━━                                              │
│  • CUDA Kernel 开发                                                 │
│  • 性能优化                                                         │
│  • 底层库开发                                                       │
│  薪资：80-150W+ RMB                                                 │
│                                                                      │
│  ML Compiler Engineer                                               │
│  ━━━━━━━━━━━━━━━━━━━━━                                              │
│  • 编译器优化                                                       │
│  • 自动代码生成                                                     │
│  • 图优化                                                           │
│  薪资：100-200W+ RMB                                                │
│                                                                      │
│  Research Engineer                                                  │
│  ━━━━━━━━━━━━━━━━━━                                                 │
│  • 算法实现与优化                                                   │
│  • 论文复现                                                         │
│  • 系统研究                                                         │
│  薪资：80-150W+ RMB                                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 公司选择

```
目标公司类型：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  芯片公司（最底层）                                                  │
│  ━━━━━━━━━━━━━━━━━                                                  │
│  • NVIDIA, AMD, Intel                                               │
│  • 国内：华为海思、寒武纪、地平线                                   │
│  工作：驱动、编译器、SDK                                            │
│                                                                      │
│  AI 框架公司                                                         │
│  ━━━━━━━━━━━━━                                                      │
│  • Meta (PyTorch)                                                   │
│  • Google (TensorFlow, JAX)                                         │
│  • 国内：百度 (PaddlePaddle)、旷视 (MegEngine)                      │
│  工作：框架开发、算子优化                                           │
│                                                                      │
│  大模型公司                                                          │
│  ━━━━━━━━━━━                                                        │
│  • OpenAI, Anthropic, DeepMind                                      │
│  • 国内：智谱、月之暗面、DeepSeek、阶跃星辰                         │
│  工作：训练推理优化、Infra                                          │
│                                                                      │
│  云厂商                                                              │
│  ━━━━━━                                                             │
│  • AWS, Azure, GCP                                                  │
│  • 国内：阿里云、腾讯云、火山引擎                                   │
│  工作：AI 平台、推理服务                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 七、常见误区

```
学习 AI 底层的常见误区：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  误区 1：先学完所有理论再动手                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                      │
│  ✗ 看完所有 CUDA 书籍再写代码                                       │
│  ✓ 边学边写，从第一天就开始写 Kernel                               │
│                                                                      │
│  误区 2：追求一步到位                                                │
│  ━━━━━━━━━━━━━━━━━━━━━                                              │
│  ✗ 一上来就想写 FlashAttention                                      │
│  ✓ 从向量加法开始，循序渐进                                         │
│                                                                      │
│  误区 3：只看不写                                                    │
│  ━━━━━━━━━━━━━━━                                                    │
│  ✗ 看了很多源码但没自己实现过                                       │
│  ✓ 先自己实现一遍，再看别人怎么写                                   │
│                                                                      │
│  误区 4：忽视基础                                                    │
│  ━━━━━━━━━━━━━━                                                     │
│  ✗ C++ 不熟就开始看 PyTorch 源码                                    │
│  ✓ 确保 C++、线性代数、体系结构基础扎实                             │
│                                                                      │
│  误区 5：只关注代码不关注原理                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━                                        │
│  ✗ 会写 CUDA 但不理解 GPU 架构                                      │
│  ✓ 理解硬件才能写出高效代码                                         │
│                                                                      │
│  误区 6：闭门造车                                                    │
│  ━━━━━━━━━━━━━━                                                     │
│  ✗ 自己一个人学                                                     │
│  ✓ 参与开源社区，与他人交流                                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 八、总结

```
AI 底层开发核心要点：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  1. 明确目标：你想深入到哪一层？                                    │
│     - 框架使用 → 框架内核 → Kernel → 硬件                           │
│                                                                      │
│  2. 打好基础：C++、线性代数、体系结构                               │
│                                                                      │
│  3. 动手实践：从第一天就开始写代码                                  │
│                                                                      │
│  4. 循序渐进：                                                       │
│     向量加法 → 矩阵乘法 → Softmax → Attention → FlashAttention     │
│                                                                      │
│  5. 读源码：PyTorch → FlashAttention → vLLM                        │
│                                                                      │
│  6. 做项目：有作品才有说服力                                        │
│                                                                      │
│  7. 参与开源：最好的学习方式                                        │
│                                                                      │
│  8. 持续学习：这个领域发展极快                                      │
│                                                                      │
│  时间投入预期：                                                      │
│  • 入门（能写基础 Kernel）：3-6 个月                                │
│  • 进阶（能优化性能）：6-12 个月                                    │
│  • 专家（能设计新算法）：1-2 年                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 相关文章

- [上一篇：22 - CUDA 实战应用场景详解](/articles/ai/ai-22-CUDA实战应用场景详解/)
- [下一篇：24 - GPU Kernel 开发详解](/articles/ai/ai-24-GPU-Kernel开发详解/)
- [21 - CUDA 入门与 GPU 编程基础](/articles/ai/ai-21-CUDA入门与GPU编程基础/)
- [16 - 推理框架优化技术详解](/articles/ai/ai-16-推理框架优化技术详解/)
