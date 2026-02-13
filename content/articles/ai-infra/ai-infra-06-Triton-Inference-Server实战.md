+++
title = "Triton Inference Server 实战"
description = "企业级 AI 模型服务化部署指南"
date = 2025-02-06
weight = 6000
updated = 2025-02-06
draft = false
[taxonomies]
tags = ["Triton", "模型服务", "推理部署", "NVIDIA"]
[extra]
toc = true
comments = true
+++

## 一、Triton Server 概述

### 1.1 什么是 Triton Inference Server

Triton 是 NVIDIA 开发的开源推理服务平台，支持多种推理后端和模型格式。

```mermaid
graph TB
    subgraph "Triton 定位"
        T1[统一推理服务]
        T2[多后端支持]
        T3[企业级特性]
        T4[高性能部署]
    end
```

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| 多后端 | TensorRT, ONNX, PyTorch, TensorFlow, vLLM |
| 动态 Batching | 自动组批提高吞吐 |
| 模型集成 | 多模型 Pipeline |
| 并发执行 | 多模型实例并行 |
| 监控指标 | Prometheus 集成 |
| gRPC/HTTP | 多协议支持 |

### 1.3 架构概览

```mermaid
graph TB
    subgraph Client["客户端"]
        C1[HTTP]
        C2[gRPC]
    end
    
    subgraph Triton["Triton Server"]
        API[API Layer]
        SCH[Scheduler]
        BATCH[Dynamic Batcher]
        
        subgraph Backends["后端"]
            TRT[TensorRT]
            ONNX[ONNX Runtime]
            PT[PyTorch]
            TF[TensorFlow]
            PY[Python]
            VLLM[vLLM]
        end
    end
    
    Client --> API --> SCH --> BATCH --> Backends
```

---

## 二、模型仓库

### 2.1 仓库结构

```
model_repository/
├── model_a/
│   ├── config.pbtxt       # 模型配置
│   ├── 1/                 # 版本 1
│   │   └── model.onnx
│   └── 2/                 # 版本 2
│       └── model.onnx
├── model_b/
│   ├── config.pbtxt
│   └── 1/
│       └── model.plan     # TensorRT 引擎
└── ensemble/
    └── config.pbtxt       # Pipeline 配置
```

### 2.2 配置文件

**config.pbtxt 关键字段**：

| 字段 | 含义 |
|------|------|
| name | 模型名称 |
| platform | 后端类型 |
| max_batch_size | 最大批次 |
| input/output | 输入输出定义 |
| instance_group | 实例配置 |
| dynamic_batching | 动态批处理配置 |

### 2.3 后端类型

| Platform | 模型格式 |
|----------|----------|
| tensorrt_plan | TensorRT .plan |
| onnxruntime_onnx | ONNX .onnx |
| pytorch_libtorch | TorchScript .pt |
| tensorflow_savedmodel | SavedModel |
| python | Python 脚本 |
| vllm | vLLM 模型 |

---

## 三、动态 Batching

### 3.1 工作原理

```mermaid
graph TB
    subgraph "动态 Batching"
        R1[请求 1] --> Q[队列]
        R2[请求 2] --> Q
        R3[请求 3] --> Q
        
        Q --> |等待/超时| B[形成 Batch]
        B --> INF[推理]
    end
```

### 3.2 配置选项

| 配置 | 含义 |
|------|------|
| preferred_batch_size | 优先批次大小 |
| max_queue_delay_microseconds | 最大等待时间 |
| preserve_ordering | 保持顺序 |

### 3.3 效果

```mermaid
graph TB
    subgraph "无 Batching"
        N1[请求] --> N2[推理]
        N3[请求] --> N4[推理]
    end
    
    subgraph "有 Batching"
        B1[请求] --> BQ[队列]
        B2[请求] --> BQ
        BQ --> BI[批量推理]
    end
```

---

## 四、模型集成

### 4.1 Ensemble 模式

**多模型 Pipeline**：

```mermaid
graph TB
    subgraph "Ensemble"
        INPUT[输入] --> PREPROCESS[预处理]
        PREPROCESS --> MODEL[主模型]
        MODEL --> POSTPROCESS[后处理]
        POSTPROCESS --> OUTPUT[输出]
    end
```

### 4.2 配置示例

```mermaid
graph TB
    subgraph "Ensemble 配置"
        E[Ensemble Model]
        
        E --> S1[Step 1: Preprocessor]
        S1 --> S2[Step 2: Inference]
        S2 --> S3[Step 3: Postprocessor]
    end
```

### 4.3 BLS（Business Logic Scripting）

使用 Python 编写复杂逻辑：

```mermaid
graph TB
    subgraph "BLS 模式"
        PY[Python 后端]
        PY --> |调用| M1[模型 1]
        PY --> |调用| M2[模型 2]
        PY --> |逻辑处理| OUT[输出]
    end
```

---

## 五、并发与实例

### 5.1 实例组

```mermaid
graph TB
    subgraph "实例配置"
        M[模型]
        
        M --> G1[GPU 0: 2 实例]
        M --> G2[GPU 1: 2 实例]
    end
```

### 5.2 配置选项

| 配置 | 含义 |
|------|------|
| count | 实例数量 |
| kind | GPU/CPU |
| gpus | 指定 GPU |

### 5.3 并发策略

```mermaid
graph TB
    subgraph "并发执行"
        R[请求] --> LB[负载均衡]
        LB --> I1[实例 1]
        LB --> I2[实例 2]
        LB --> I3[实例 3]
    end
```

---

## 六、LLM 部署

### 6.1 vLLM 后端

```mermaid
graph TB
    subgraph "Triton + vLLM"
        Triton[Triton Server]
        VLLM[vLLM Backend]
        Model[LLM Model]
        
        Triton --> VLLM --> Model
    end
```

### 6.2 TensorRT-LLM 后端

```mermaid
graph TB
    subgraph "Triton + TRT-LLM"
        Triton[Triton Server]
        TRTLLM[TensorRT-LLM Backend]
        Engine[TRT Engine]
        
        Triton --> TRTLLM --> Engine
    end
```

### 6.3 In-flight Batching

专为 LLM 设计的批处理：

| 特性 | 描述 |
|------|------|
| 动态加入 | 请求随时加入 |
| 动态退出 | 完成即退出 |
| 流式输出 | 逐 token 返回 |

---

## 七、监控与运维

### 7.1 健康检查

```mermaid
graph TB
    subgraph "健康检查端点"
        LIVE[/v2/health/live]
        READY[/v2/health/ready]
        MODEL[/v2/models/{name}/ready]
    end
```

### 7.2 指标监控

**Prometheus 指标**：

| 指标 | 含义 |
|------|------|
| nv_inference_request_success | 成功请求数 |
| nv_inference_request_failure | 失败请求数 |
| nv_inference_exec_count | 执行次数 |
| nv_inference_queue_duration | 队列等待时间 |
| nv_gpu_utilization | GPU 利用率 |

### 7.3 日志配置

| 日志级别 | 用途 |
|----------|------|
| INFO | 基本信息 |
| WARNING | 警告 |
| ERROR | 错误 |
| VERBOSE | 调试 |

---

## 八、性能调优

### 8.1 Batching 调优

| 参数 | 调优建议 |
|------|----------|
| max_queue_delay | 延迟敏感降低，吞吐优先提高 |
| preferred_batch_size | 与 GPU 并行度匹配 |
| max_batch_size | 根据显存调整 |

### 8.2 实例调优

```mermaid
graph TB
    subgraph "实例数调优"
        LOW[实例太少] --> UTIL[GPU 利用率低]
        HIGH[实例太多] --> MEM[显存不足]
        OPT[合适实例数] --> BEST[最佳性能]
    end
```

### 8.3 内存调优

| 配置 | 作用 |
|------|------|
| pinned_memory_pool | 固定内存池 |
| cuda_memory_pool | CUDA 内存池 |
| response_cache | 响应缓存 |

---

## 九、生产部署

### 9.1 容器化部署

```mermaid
graph TB
    subgraph "Kubernetes 部署"
        ING[Ingress]
        SVC[Service]
        POD[Triton Pod]
        PV[模型存储]
        
        ING --> SVC --> POD --> PV
    end
```

### 9.2 高可用

```mermaid
graph TB
    subgraph "高可用架构"
        LB[负载均衡]
        
        LB --> T1[Triton 1]
        LB --> T2[Triton 2]
        LB --> T3[Triton 3]
        
        T1 & T2 & T3 --> STORE[共享存储]
    end
```

### 9.3 模型更新

| 策略 | 描述 |
|------|------|
| 热加载 | 不重启更新模型 |
| 版本切换 | 切换到新版本 |
| 金丝雀 | 逐步切换流量 |

---

## 十、总结

### 10.1 核心认知

1. **统一服务平台**
   - 支持多种后端
   - 标准化接口

2. **企业级特性**
   - 动态 Batching
   - 监控指标
   - 高可用

3. **LLM 友好**
   - vLLM/TRT-LLM 集成
   - In-flight Batching

### 10.2 适用场景

| 场景 | 适合度 |
|------|--------|
| 生产部署 | ★★★ |
| 多模型服务 | ★★★ |
| 快速原型 | ★★ |
| 单模型简单部署 | ★★ |

---

## 相关文章

- [上一篇：05 - llama.cpp 源码解析](@/articles/ai-infra/ai-infra-05-llama.cpp源码解析.md)
- [下一篇：07 - 推理调度与 Batching 策略](@/articles/ai-infra/ai-infra-07-推理调度与Batching策略.md)
- [03 - vLLM 架构与源码解析](@/articles/ai-infra/ai-infra-03-vLLM架构与源码解析.md)
