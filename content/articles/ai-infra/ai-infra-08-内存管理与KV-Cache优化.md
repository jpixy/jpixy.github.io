+++
title = "08. 内存管理与 KV Cache 优化"
description = "深入理解 LLM 推理中的显存管理和 KV Cache 优化技术"
date = 2025-02-06
weight = 8000
updated = 2025-02-06
draft = false
[taxonomies]
tags = ["内存管理", "KV Cache", "PagedAttention", "显存优化"]
[extra]
toc = true
comments = true
+++

## 一、显存管理的重要性

### 1.1 LLM 显存构成

```mermaid
pie title LLM 推理显存分布
    "模型权重" : 40
    "KV Cache" : 45
    "激活值" : 10
    "其他" : 5
```

### 1.2 KV Cache 的问题

| 问题 | 描述 |
|------|------|
| 动态增长 | 每个 token 增加显存 |
| 预分配浪费 | 传统方式预分配最大长度 |
| 碎片化 | 请求完成后留下空洞 |
| 无法预知长度 | 不知道生成多少 token |

### 1.3 显存计算

**KV Cache 大小公式**：

```
单个 token KV Cache:
= 2 × n_layers × n_heads × d_head × dtype_size

LLaMA-70B (FP16):
= 2 × 80 × 8 × 128 × 2 bytes
= 327,680 bytes per token

4096 tokens:
= 327,680 × 4096 = 1.34 GB per sequence
```

---

## 二、传统内存管理

### 2.1 预分配方式

```mermaid
graph TB
    subgraph "传统预分配"
        SEQ1[序列1: 预分配 4096 tokens]
        SEQ2[序列2: 预分配 4096 tokens]
        
        SEQ1 --> USED1[实际使用: 100 tokens]
        SEQ2 --> USED2[实际使用: 500 tokens]
        
        WASTE[大量浪费]
    end
```

### 2.2 问题分析

| 问题 | 影响 |
|------|------|
| 内存利用率低 | ~50% 或更低 |
| 并发受限 | 无法支持更多请求 |
| 碎片化 | 无法充分利用 |

---

## 三、PagedAttention

### 3.1 核心思想

**像操作系统管理内存一样管理 KV Cache**

```mermaid
graph TB
    subgraph "PagedAttention 思想"
        OS[操作系统分页]
        PA[PagedAttention]
        
        OS --> |借鉴| PA
        
        OS --> VIRT[虚拟地址 → 物理地址]
        PA --> LOGIC[逻辑块 → 物理块]
    end
```

### 3.2 Block 设计

```mermaid
graph TB
    subgraph "Block 结构"
        BLOCK[Physical Block]
        BLOCK --> TOKENS[固定 token 数<br>如 16 tokens]
        BLOCK --> K[K Cache]
        BLOCK --> V[V Cache]
    end
```

### 3.3 Block Table

```mermaid
graph TB
    subgraph "Block Table 映射"
        SEQ[序列]
        
        SEQ --> LB0[逻辑块 0]
        SEQ --> LB1[逻辑块 1]
        SEQ --> LB2[逻辑块 2]
        
        LB0 --> |映射| PB5[物理块 5]
        LB1 --> |映射| PB2[物理块 2]
        LB2 --> |映射| PB8[物理块 8]
    end
```

### 3.4 优势

| 优势 | 效果 |
|------|------|
| 按需分配 | 用多少分多少 |
| 消除碎片 | 块可以不连续 |
| 利用率高 | 接近 100% |
| 支持共享 | Copy-on-Write |

---

## 四、内存池设计

### 4.1 Block 池

```mermaid
graph TB
    subgraph "Block 池管理"
        POOL[Block Pool]
        
        FREE[Free List<br>空闲块列表]
        ALLOC[Allocated<br>已分配块]
        
        POOL --> FREE
        POOL --> ALLOC
    end
```

### 4.2 分配流程

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant BM as BlockManager
    participant POOL as Block Pool
    
    S->>BM: allocate(num_blocks)
    BM->>POOL: get_free_blocks()
    POOL-->>BM: blocks
    BM->>BM: update block_table
    BM-->>S: success
```

### 4.3 释放流程

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant BM as BlockManager
    participant POOL as Block Pool
    
    S->>BM: free(seq_id)
    BM->>BM: get blocks from table
    BM->>POOL: return_blocks()
    BM->>BM: clear block_table
    BM-->>S: success
```

---

## 五、高级优化技术

### 5.1 Prefix Caching

**共享公共前缀的 KV Cache**

```mermaid
graph TB
    subgraph "Prefix Caching"
        PREFIX[系统提示词<br>共享 KV Cache]
        
        REQ1[请求1: 前缀 + 问题A]
        REQ2[请求2: 前缀 + 问题B]
        
        REQ1 --> PREFIX
        REQ2 --> PREFIX
    end
```

**实现**：
- 计算前缀 hash
- 查找已缓存的 KV
- 命中则复用

### 5.2 Copy-on-Write

**多序列共享 Block**

```mermaid
graph TB
    subgraph "Copy-on-Write"
        S1[序列1] --> B[共享 Block<br>ref_count=2]
        S2[序列2] --> B
        
        S2 -->|写入| B2[新 Block]
    end
```

**应用场景**：
- Beam Search
- 并行采样
- 前缀共享

### 5.3 KV Cache 量化

**压缩 KV Cache 占用**

| 方法 | 压缩比 | 精度影响 |
|------|--------|----------|
| FP16 → INT8 | 2x | 小 |
| FP16 → INT4 | 4x | 中等 |
| 选择性量化 | 可变 | 可控 |

### 5.4 KV Cache 压缩

**Token 级别压缩**

```mermaid
graph TB
    subgraph "KV Cache 压缩"
        FULL[完整 KV Cache]
        
        FULL --> MERGE[合并相似 token]
        FULL --> DROP[丢弃不重要 token]
        FULL --> EVICT[淘汰旧 token]
    end
```

---

## 六、Offloading

### 6.1 CPU Offload

**将 KV Cache 换出到 CPU**

```mermaid
graph TB
    subgraph "CPU Offload"
        GPU[GPU Cache<br>热数据]
        CPU[CPU Cache<br>冷数据]
        
        GPU <-->|Swap| CPU
    end
```

### 6.2 NVMe Offload

**换出到 SSD**

```mermaid
graph TB
    GPU[GPU] <--> CPU[CPU]
    CPU <--> NVME[NVMe SSD]
```

### 6.3 Offload 策略

| 策略 | 描述 |
|------|------|
| LRU | 最近最少使用 |
| 优先级 | 低优先级先换出 |
| 预测 | 预测可能不需要的 |

---

## 七、多 GPU 内存管理

### 7.1 Tensor Parallel KV Cache

```mermaid
graph TB
    subgraph "TP KV Cache 分布"
        KV[KV Cache]
        
        KV --> GPU0[GPU 0: Head 0-7]
        KV --> GPU1[GPU 1: Head 8-15]
        KV --> GPU2[GPU 2: Head 16-23]
        KV --> GPU3[GPU 3: Head 24-31]
    end
```

### 7.2 跨 GPU 通信

```mermaid
graph TB
    subgraph "AllReduce"
        G0[GPU 0] <--> G1[GPU 1]
        G1 <--> G2[GPU 2]
        G2 <--> G3[GPU 3]
        G3 <--> G0
    end
```

---

## 八、实现细节

### 8.1 Block 大小选择

| Block Size | 优点 | 缺点 |
|------------|------|------|
| 小（8） | 灵活 | 管理开销大 |
| 中（16） | 平衡 | - |
| 大（32） | 开销小 | 可能浪费 |

### 8.2 内存对齐

| 要求 | 原因 |
|------|------|
| 256 字节对齐 | CUDA 内存访问效率 |
| 缓存行对齐 | CPU 访问效率 |

### 8.3 错误处理

| 错误 | 处理 |
|------|------|
| OOM | 触发换出或拒绝 |
| 分配失败 | 重试或降级 |
| 损坏检测 | 校验和验证 |

---

## 九、性能分析

### 9.1 关键指标

| 指标 | 含义 |
|------|------|
| 内存利用率 | 使用/总量 |
| 碎片率 | 不可用块比例 |
| 分配延迟 | 分配耗时 |
| 换出频率 | Swap 次数 |

### 9.2 优化效果

| 技术 | 利用率提升 |
|------|------------|
| PagedAttention | 50% → 95% |
| Prefix Caching | 节省重复计算 |
| KV Quantization | 2-4x 压缩 |

---

## 十、总结

### 10.1 核心认知

1. **KV Cache 是显存主要消耗**
   - 动态增长
   - 传统方式浪费严重

2. **PagedAttention 是突破**
   - 分页思想
   - 显存利用率接近 100%

3. **多种优化可叠加**
   - 量化
   - 压缩
   - Offload
   - 共享

### 10.2 设计原则

```mermaid
graph TB
    P1[按需分配] --> P2[消除碎片]
    P2 --> P3[支持共享]
    P3 --> P4[弹性扩展]
```

---

## 相关文章

- [上一篇：07 - 推理调度与 Batching 策略](@/articles/ai-infra/ai-infra-07-推理调度与Batching策略.md)
- [下一篇：09 - 推理引擎性能调优](@/articles/ai-infra/ai-infra-09-推理引擎性能调优.md)
- [25 - FlashAttention 与 PagedAttention 原理](@/articles/ai/ai-25-FlashAttention与PagedAttention原理.md)
