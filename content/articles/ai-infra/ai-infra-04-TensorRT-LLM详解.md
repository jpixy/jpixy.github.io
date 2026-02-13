+++
title = "04. TensorRT-LLM 详解"
description = "深入理解 NVIDIA 官方 LLM 推理引擎的架构与使用"
date = 2025-02-06
weight = 4000
updated = 2025-02-06
draft = false
[taxonomies]
tags = ["TensorRT-LLM", "NVIDIA", "推理优化", "LLM"]
[extra]
toc = true
comments = true
+++

## 一、TensorRT-LLM 概述

### 1.1 什么是 TensorRT-LLM

TensorRT-LLM 是 NVIDIA 官方推出的 LLM 推理优化库，基于 TensorRT 构建，专门针对 LLM 场景优化。

```mermaid
graph TB
    subgraph "TensorRT 生态"
        TRT[TensorRT<br>通用推理优化]
        TRTLLM[TensorRT-LLM<br>LLM 专用优化]
        TRITON[Triton Server<br>模型服务化]
        
        TRT --> TRTLLM
        TRTLLM --> TRITON
    end
```

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| 高性能 | NVIDIA GPU 最优性能 |
| 量化支持 | FP8/INT8/INT4/AWQ/GPTQ |
| 多 GPU | Tensor Parallel + Pipeline Parallel |
| In-flight Batching | 类似 Continuous Batching |
| Paged KV Cache | 高效显存管理 |
| 自定义算子 | Plugin 机制扩展 |

### 1.3 与 TensorRT 的关系

```mermaid
graph TB
    subgraph "TensorRT 基础"
        B1[图优化]
        B2[算子融合]
        B3[精度校准]
        B4[Kernel 自动调优]
    end
    
    subgraph "TensorRT-LLM 扩展"
        E1[LLM 专用算子]
        E2[KV Cache 管理]
        E3[自回归生成]
        E4[分布式推理]
    end
    
    B1 & B2 & B3 & B4 --> E1 & E2 & E3 & E4
```

---

## 二、整体架构

### 2.1 架构概览

```mermaid
graph TB
    subgraph Python["Python 层"]
        PY1[模型定义]
        PY2[构建脚本]
        PY3[运行脚本]
    end
    
    subgraph CPP["C++ 层"]
        CPP1[Runtime]
        CPP2[Executor]
        CPP3[Session]
    end
    
    subgraph Engine["引擎层"]
        ENG1[TensorRT Engine]
        ENG2[Custom Plugins]
        ENG3[CUDA Kernels]
    end
    
    Python --> CPP --> Engine
```

### 2.2 工作流程

```mermaid
graph TB
    subgraph "TensorRT-LLM 工作流"
        S1[模型转换<br>HuggingFace → TRT-LLM]
        S2[引擎构建<br>build]
        S3[推理服务<br>run]
        
        S1 --> S2 --> S3
    end
```

---

## 三、模型构建

### 3.1 构建流程

```mermaid
graph TB
    subgraph "构建流程"
        HF[HuggingFace 模型]
        Convert[转换权重]
        Define[定义网络]
        Build[构建引擎]
        Engine[TRT Engine]
        
        HF --> Convert --> Define --> Build --> Engine
    end
```

### 3.2 支持的模型

| 模型系列 | 支持版本 |
|----------|----------|
| LLaMA | LLaMA 1/2/3, Code Llama |
| GPT | GPT-2, GPT-J, GPT-NeoX |
| Falcon | Falcon 7B/40B/180B |
| Mistral | Mistral 7B, Mixtral |
| Qwen | Qwen 1/1.5/2 |
| ChatGLM | ChatGLM 1/2/3/4 |

### 3.3 构建配置

**关键参数**：

| 参数 | 作用 |
|------|------|
| `--dtype` | 数据类型 (float16/bfloat16) |
| `--use_gpt_attention_plugin` | 使用优化的 Attention |
| `--use_gemm_plugin` | 使用优化的 GEMM |
| `--enable_context_fmha` | 启用 Flash Attention |
| `--paged_kv_cache` | 启用分页 KV Cache |
| `--max_batch_size` | 最大批次大小 |
| `--max_input_len` | 最大输入长度 |
| `--max_output_len` | 最大输出长度 |

---

## 四、核心组件

### 4.1 Plugin 系统

**什么是 Plugin**：自定义的高性能算子

```mermaid
graph TB
    subgraph "Plugin 类型"
        P1[GPT Attention Plugin]
        P2[GEMM Plugin]
        P3[LayerNorm Plugin]
        P4[RoPE Plugin]
        P5[Quantization Plugin]
    end
```

**GPT Attention Plugin**：

| 特性 | 支持 |
|------|------|
| Flash Attention | ✓ |
| Multi-Query Attention | ✓ |
| Grouped-Query Attention | ✓ |
| Paged KV Cache | ✓ |
| FP8 | ✓ |

### 4.2 量化支持

```mermaid
graph TB
    subgraph "量化方法"
        Q1[FP8<br>H100 原生支持]
        Q2[INT8 SmoothQuant<br>权重+激活量化]
        Q3[INT4 AWQ<br>权重量化]
        Q4[INT4 GPTQ<br>权重量化]
    end
```

**量化效果**：

| 方法 | 显存 | 速度 | 精度 |
|------|------|------|------|
| FP16 | 100% | 1x | 基准 |
| FP8 | 50% | 1.5-2x | 接近 FP16 |
| INT8 | 50% | 1.5-2x | 略有下降 |
| INT4 | 25% | 2-3x | 明显下降 |

### 4.3 分布式推理

```mermaid
graph TB
    subgraph "分布式策略"
        TP[Tensor Parallel<br>模型切分到多 GPU]
        PP[Pipeline Parallel<br>层切分到多 GPU]
        
        TP --> TP1[适合：单节点多卡]
        PP --> PP1[适合：多节点]
    end
```

**Tensor Parallel 实现**：

```mermaid
graph TB
    subgraph "TP=4 示例"
        Input --> Split
        Split --> GPU0[GPU 0: 1/4 权重]
        Split --> GPU1[GPU 1: 1/4 权重]
        Split --> GPU2[GPU 2: 1/4 权重]
        Split --> GPU3[GPU 3: 1/4 权重]
        GPU0 & GPU1 & GPU2 & GPU3 --> AllReduce
        AllReduce --> Output
    end
```

---

## 五、In-flight Batching

### 5.1 概念

类似 vLLM 的 Continuous Batching，允许请求动态加入和退出。

```mermaid
graph TB
    subgraph "In-flight Batching"
        R1[请求可随时加入]
        R2[完成后立即退出]
        R3[不等待整个 batch]
        R4[最大化 GPU 利用率]
    end
```

### 5.2 Executor API

```mermaid
graph TB
    subgraph "Executor 模式"
        E1[提交请求]
        E2[异步执行]
        E3[回调返回]
        
        E1 --> E2 --> E3
    end
```

### 5.3 调度策略

| 策略 | 描述 |
|------|------|
| Max Utilization | 最大化 GPU 利用率 |
| Guaranteed No Evict | 保证不换出 |
| Static Batching | 传统静态批处理 |

---

## 六、性能优化

### 6.1 Kernel 优化

```mermaid
graph TB
    subgraph "Kernel 优化"
        K1[Flash Attention<br>减少内存访问]
        K2[Fused Kernels<br>算子融合]
        K3[Tensor Core<br>利用硬件特性]
        K4[Quantized Kernels<br>低精度计算]
    end
```

### 6.2 内存优化

| 优化 | 方法 |
|------|------|
| Paged KV Cache | 按需分配 |
| Weight Streaming | 权重流式加载 |
| Activation Recomputation | 减少激活存储 |

### 6.3 通信优化

```mermaid
graph TB
    subgraph "通信优化"
        C1[NCCL 集合通信]
        C2[NVLink 高速互联]
        C3[通信计算重叠]
    end
```

---

## 七、与 Triton Server 集成

### 7.1 部署架构

```mermaid
graph TB
    subgraph "Triton + TRT-LLM"
        Client[客户端]
        Triton[Triton Server]
        Backend[TRT-LLM Backend]
        Engine[TRT Engine]
        
        Client --> Triton --> Backend --> Engine
    end
```

### 7.2 配置示例

**模型仓库结构**：

```
model_repository/
└── llama/
    ├── config.pbtxt
    └── 1/
        └── (TRT engines)
```

### 7.3 动态 Batching 配置

```mermaid
graph TB
    subgraph "Triton Batching"
        DB[Dynamic Batching]
        IFB[In-flight Batching]
        
        DB --> DB1[传统模型]
        IFB --> IFB1[LLM 模型]
    end
```

---

## 八、性能对比

### 8.1 与其他框架对比

| 场景 | TensorRT-LLM | vLLM | llama.cpp |
|------|--------------|------|-----------|
| 延迟 | 最低 | 低 | 中 |
| 吞吐 | 最高 | 高 | 中 |
| 易用性 | 中 | 高 | 高 |
| 硬件支持 | NVIDIA only | NVIDIA + AMD | 多平台 |

### 8.2 性能数据（参考）

| 模型 | 配置 | 吞吐量 |
|------|------|--------|
| LLaMA-7B | 1×A100-80G, FP16 | ~4000 tokens/s |
| LLaMA-70B | 8×A100-80G, TP8 | ~2000 tokens/s |
| LLaMA-70B | 8×H100, FP8, TP8 | ~4000 tokens/s |

---

## 九、使用建议

### 9.1 适用场景

```mermaid
graph TB
    subgraph "适用场景"
        S1[生产环境部署]
        S2[追求极致性能]
        S3[NVIDIA GPU 环境]
        S4[需要企业支持]
    end
```

### 9.2 不适用场景

| 场景 | 原因 |
|------|------|
| 快速原型 | 构建流程复杂 |
| AMD GPU | 不支持 |
| 频繁更换模型 | 需要重新构建 |

### 9.3 最佳实践

| 实践 | 建议 |
|------|------|
| 量化选择 | H100 用 FP8，其他用 INT8 |
| 并行策略 | 优先 TP，大模型加 PP |
| 批处理 | 启用 In-flight Batching |
| 监控 | 使用 Triton 的监控指标 |

---

## 十、总结

### 10.1 核心认知

1. **官方优化，性能最佳**
   - NVIDIA 深度优化
   - 最新硬件特性支持（FP8）

2. **生产级就绪**
   - 与 Triton 集成
   - 企业级支持

3. **复杂度较高**
   - 需要理解 TensorRT
   - 构建流程复杂

4. **适合特定场景**
   - NVIDIA GPU + 追求极致性能
   - 生产环境长期部署

### 10.2 学习建议

```mermaid
graph TB
    L1[理解 TensorRT 基础] --> L2[学习构建流程]
    L2 --> L3[实践模型部署]
    L3 --> L4[性能调优]
```

---

## 相关文章

- [上一篇：03 - vLLM 架构与源码解析](@/articles/ai-infra/ai-infra-03-vLLM架构与源码解析.md)
- [下一篇：05 - llama.cpp 源码解析](@/articles/ai-infra/ai-infra-05-llama.cpp源码解析.md)
- [02 - LLM 推理优化全景](@/articles/ai-infra/ai-infra-02-LLM推理优化全景.md)
