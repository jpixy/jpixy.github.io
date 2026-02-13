+++
title = "llama.cpp 源码解析"
description = "深入理解纯 C/C++ 实现的 LLM 推理引擎"
date = 2025-02-06
weight = 5000
updated = 2025-02-06
draft = false
[taxonomies]
tags = ["llama.cpp", "C++", "GGML", "端侧推理"]
[extra]
toc = true
comments = true
+++

## 一、llama.cpp 概述

### 1.1 什么是 llama.cpp

llama.cpp 是由 Georgi Gerganov 开发的纯 C/C++ LLM 推理库，以简洁高效著称。

**核心特点**：
- **纯 C/C++**：无 Python 依赖
- **跨平台**：支持 CPU、GPU、Apple Silicon
- **轻量级**：单文件即可运行
- **量化支持**：丰富的量化格式

### 1.2 为什么重要

```mermaid
graph TB
    subgraph "llama.cpp 价值"
        V1[端侧部署首选]
        V2[学习 LLM 推理最佳材料]
        V3[活跃的社区]
        V4[广泛的硬件支持]
    end
```

### 1.3 硬件支持

| 平台 | 后端 |
|------|------|
| CPU | AVX/AVX2/AVX512, ARM NEON |
| NVIDIA GPU | CUDA |
| AMD GPU | ROCm/HIP |
| Apple | Metal |
| Intel GPU | SYCL |
| Vulkan | 跨平台 GPU |

---

## 二、整体架构

### 2.1 项目结构

```
llama.cpp/
├── ggml/              # 张量库
│   ├── src/
│   │   ├── ggml.c           # 核心张量操作
│   │   ├── ggml-backend.c   # 后端抽象
│   │   ├── ggml-cuda.cu     # CUDA 后端
│   │   ├── ggml-metal.m     # Metal 后端
│   │   └── ggml-quants.c    # 量化实现
├── src/
│   ├── llama.cpp      # LLM 核心逻辑
│   └── llama-*.cpp    # 各模块实现
├── examples/          # 示例程序
│   ├── main/          # 命令行推理
│   └── server/        # HTTP 服务器
└── models/            # 模型存放
```

### 2.2 分层架构

```mermaid
graph TB
    subgraph "llama.cpp 分层"
        L1[应用层<br>main, server]
        L2[模型层<br>llama.cpp]
        L3[计算图层<br>ggml]
        L4[后端层<br>CPU/CUDA/Metal]
        
        L1 --> L2 --> L3 --> L4
    end
```

---

## 三、GGML 张量库

### 3.1 什么是 GGML

**GGML = Georgi Gerganov Machine Learning**

一个轻量级的张量计算库，是 llama.cpp 的基础。

### 3.2 核心概念

```mermaid
graph TB
    subgraph "GGML 核心概念"
        T[ggml_tensor<br>张量]
        C[ggml_context<br>内存上下文]
        G[ggml_cgraph<br>计算图]
        B[ggml_backend<br>后端]
        
        C --> T
        T --> G
        B --> G
    end
```

### 3.3 张量结构

**ggml_tensor 关键字段**：

| 字段 | 含义 |
|------|------|
| type | 数据类型（F32/F16/Q4_0 等） |
| ne[4] | 各维度大小 |
| nb[4] | 各维度步长（字节） |
| data | 数据指针 |
| op | 操作类型 |
| src[10] | 输入张量 |

### 3.4 计算图

```mermaid
graph TB
    subgraph "计算图示例"
        A[input] --> M[matmul]
        W[weight] --> M
        M --> R[relu]
        R --> O[output]
    end
```

**构建和执行**：

```mermaid
graph TB
    Build[构建计算图<br>ggml_build_forward] --> Schedule[调度执行<br>ggml_backend_sched] --> Execute[实际计算<br>后端执行]
```

### 3.5 后端系统

```mermaid
graph TB
    subgraph "后端抽象"
        SCHED[ggml_backend_sched<br>调度器]
        
        SCHED --> CPU[CPU Backend]
        SCHED --> CUDA[CUDA Backend]
        SCHED --> Metal[Metal Backend]
        SCHED --> Vulkan[Vulkan Backend]
    end
```

**后端选择逻辑**：
1. 检查可用后端
2. 优先使用 GPU
3. 部分操作可能 fallback 到 CPU

---

## 四、量化系统

### 4.1 GGUF 格式

**GGUF = GGML Unified Format**

统一的模型文件格式，包含模型权重和元数据。

```mermaid
graph TB
    subgraph "GGUF 文件结构"
        H[Header<br>魔数、版本]
        M[Metadata<br>模型配置]
        T[Tensors<br>量化权重]
        
        H --> M --> T
    end
```

### 4.2 量化类型

| 类型 | 位数 | 块大小 | 特点 |
|------|------|--------|------|
| F32 | 32 | - | 原始精度 |
| F16 | 16 | - | 半精度 |
| Q8_0 | 8 | 32 | 简单量化 |
| Q4_0 | 4 | 32 | 基础 4 位 |
| Q4_K_M | 4 | 256 | K-quants，精度更好 |
| Q2_K | 2 | 256 | 极致压缩 |
| IQ4_XS | 4 | 256 | 重要性量化 |

### 4.3 量化原理

**块量化**：

```mermaid
graph TB
    subgraph "Q4_0 量化流程"
        A["原始数据 (32 个 FP32)<br/>[x0, x1, ..., x31]"]
        B["找到最大绝对值<br/>d = max(|xi|)"]
        C["计算量化因子<br/>scale = d / 7"]
        D["量化每个值<br/>qi = round(xi / scale)"]
        E["打包存储<br/>[scale (FP16)] + [q0q1, q2q3, ...]<br/>每两个 4 位打包"]
        
        A --> B --> C --> D --> E
    end
```

### 4.4 K-quants

**分层量化**：不同层使用不同精度

```mermaid
graph TB
    subgraph "K-quants 策略"
        L1[重要层<br>Q6_K / Q8_0]
        L2[次重要层<br>Q4_K]
        L3[一般层<br>Q3_K / Q2_K]
    end
```

---

## 五、模型推理流程

### 5.1 整体流程

```mermaid
graph TB
    subgraph "推理流程"
        LOAD[加载模型]
        CTX[创建上下文]
        TOK[Tokenize]
        EVAL[推理计算]
        SAMP[采样]
        DETOK[Detokenize]
        
        LOAD --> CTX --> TOK --> EVAL --> SAMP --> DETOK
    end
```

### 5.2 模型加载

```mermaid
graph TB
    subgraph "模型加载流程"
        OPEN[打开 GGUF 文件]
        META[解析 Metadata]
        ALLOC[分配显存/内存]
        COPY[复制权重]
        
        OPEN --> META --> ALLOC --> COPY
    end
```

### 5.3 推理计算

**Prefill 阶段**：

```mermaid
graph TB
    P1[输入全部 tokens]
    P2[构建计算图]
    P3[一次前向计算]
    P4[生成 KV Cache]
    
    P1 --> P2 --> P3 --> P4
```

**Decode 阶段**：

```mermaid
graph TB
    D1[输入上一个 token]
    D2[使用 KV Cache]
    D3[计算下一个 logits]
    D4[采样]
    
    D1 --> D2 --> D3 --> D4
```

### 5.4 KV Cache

```mermaid
graph TB
    subgraph "KV Cache 管理"
        SLOT[Cache Slots]
        SEQ[Sequence ID]
        POS[Position]
        
        SEQ --> SLOT
        POS --> SLOT
    end
```

---

## 六、核心代码解析

### 6.1 主要函数

| 函数 | 作用 |
|------|------|
| llama_load_model_from_file | 加载模型 |
| llama_new_context_with_model | 创建推理上下文 |
| llama_decode | 执行一次推理 |
| llama_get_logits | 获取输出 logits |
| llama_sample_* | 各种采样方法 |

### 6.2 推理上下文

**llama_context 关键字段**：

| 字段 | 含义 |
|------|------|
| model | 关联的模型 |
| kv_cache | KV Cache |
| backend | 计算后端 |
| n_ctx | 上下文长度 |
| logits | 输出 logits |

### 6.3 计算图构建

**Transformer 层计算**：

```mermaid
graph TB
    subgraph "单层 Transformer"
        IN[Input]
        LN1[LayerNorm]
        ATT[Attention]
        RES1[Residual]
        LN2[LayerNorm]
        FFN[FFN]
        RES2[Residual]
        OUT[Output]
        
        IN --> LN1 --> ATT --> RES1
        IN --> RES1
        RES1 --> LN2 --> FFN --> RES2
        RES1 --> RES2
        RES2 --> OUT
    end
```

### 6.4 Attention 实现

```mermaid
graph TB
    subgraph "Attention 计算"
        Q[Query]
        K[Key]
        V[Value]
        
        Q --> QK[Q × K^T]
        K --> QK
        QK --> Scale[Scale]
        Scale --> Mask[+ Mask]
        Mask --> Softmax
        Softmax --> AV[× V]
        V --> AV
        AV --> Out[Output]
    end
```

---

## 七、后端实现

### 7.1 CPU 后端

**优化手段**：

| 优化 | 技术 |
|------|------|
| SIMD | AVX2/AVX512/NEON |
| 多线程 | OpenMP |
| 缓存优化 | 分块计算 |
| 量化 | 专门的量化内积 |

### 7.2 CUDA 后端

**关键 Kernel**：

| Kernel | 作用 |
|--------|------|
| dequantize | 反量化 |
| mul_mat | 矩阵乘法 |
| flash_attn | Flash Attention |
| rope | 位置编码 |
| softmax | Softmax |

### 7.3 Metal 后端

**Apple Silicon 优化**：
- 统一内存架构
- Metal Shader
- ANE（神经引擎）部分支持

---

## 八、服务器模式

### 8.1 架构

```mermaid
graph TB
    subgraph "Server 架构"
        HTTP[HTTP Server]
        SLOT[Slot Manager]
        QUEUE[Request Queue]
        INF[Inference Engine]
        
        HTTP --> SLOT
        SLOT --> QUEUE
        QUEUE --> INF
    end
```

### 8.2 Slot 机制

```mermaid
graph TB
    subgraph "Slot 管理"
        S1[Slot 0] --> |请求1| R1[Request 1]
        S2[Slot 1] --> |请求2| R2[Request 2]
        S3[Slot 2] --> |空闲| IDLE
    end
```

**并发处理**：
- 每个 Slot 独立的 KV Cache
- 支持多请求并发
- 类似简化版 Continuous Batching

### 8.3 API 兼容

兼容 OpenAI API 格式：
- `/v1/chat/completions`
- `/v1/completions`
- `/v1/embeddings`

---

## 九、性能调优

### 9.1 关键参数

| 参数 | 作用 | 建议 |
|------|------|------|
| -ngl | GPU 层数 | 尽量全部放 GPU |
| -c | 上下文长度 | 按需设置 |
| -b | 批处理大小 | Prefill 用大值 |
| -t | CPU 线程数 | 物理核心数 |
| --mlock | 锁定内存 | 避免交换 |

### 9.2 量化选择

| 场景 | 推荐量化 |
|------|----------|
| 最高质量 | Q8_0 |
| 平衡 | Q4_K_M |
| 最小体积 | Q2_K / IQ2_XXS |
| 速度优先 | Q4_0 |

### 9.3 硬件优化

| 硬件 | 优化建议 |
|------|----------|
| NVIDIA GPU | 使用 CUDA，-ngl 99 |
| Apple M 系列 | 使用 Metal，-ngl 99 |
| CPU only | 启用 AVX2/AVX512，多线程 |

---

## 十、扩展与贡献

### 10.1 添加新模型

```mermaid
graph TB
    subgraph "添加模型步骤"
        S1[分析模型架构]
        S2[添加模型类型]
        S3[实现前向计算]
        S4[编写转换脚本]
        
        S1 --> S2 --> S3 --> S4
    end
```

### 10.2 添加新后端

| 步骤 | 内容 |
|------|------|
| 1 | 实现 ggml_backend 接口 |
| 2 | 实现核心算子 |
| 3 | 注册后端 |
| 4 | 测试验证 |

---

## 十一、总结

### 11.1 核心认知

1. **简洁而强大**
   - 纯 C/C++ 实现
   - 代码可读性高

2. **量化是核心**
   - 丰富的量化格式
   - 精度与性能平衡

3. **端侧首选**
   - 跨平台支持
   - 资源占用小

4. **学习价值高**
   - 理解 LLM 推理细节
   - 代码质量高

### 11.2 学习建议

```mermaid
graph TB
    L1[编译运行] --> L2[阅读 ggml.c]
    L2 --> L3[阅读 llama.cpp]
    L3 --> L4[尝试修改]
```

---

## 相关文章

- [上一篇：04 - TensorRT-LLM 详解](@/articles/ai-infra/ai-infra-04-TensorRT-LLM详解.md)
- [下一篇：06 - Triton Inference Server 实战](@/articles/ai-infra/ai-infra-06-Triton-Inference-Server实战.md)
- [21 - CUDA 入门与 GPU 编程基础](@/articles/ai/ai-21-CUDA入门与GPU编程基础.md)
