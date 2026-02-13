+++
title = "02. 并行计算基础"
description = "并行计算的核心概念、模型与性能分析"
date = 2025-02-06
weight = 2000
updated = 2025-02-06
draft = false
[taxonomies]
tags = ["并行计算", "HPC", "Amdahl定律", "并行模型"]
[extra]
toc = true
comments = true
+++

## 一、为什么需要并行计算

### 1.1 串行的极限

| 限制 | 描述 |
|------|------|
| 时钟频率 | 功耗墙限制 ~5GHz |
| 单核性能 | ILP 开发接近极限 |
| 内存带宽 | 内存墙 |

### 1.2 并行的必然

```mermaid
graph TB
    subgraph "性能提升方式"
        S1[提高频率] --> L1[功耗墙]
        S2[增加核心] --> L2[并行计算]
    end
```

---

## 二、并行计算分类

### 2.1 Flynn 分类法

```mermaid
graph TB
    subgraph "Flynn 分类"
        SISD[SISD<br>单指令单数据]
        SIMD[SIMD<br>单指令多数据]
        MISD[MISD<br>多指令单数据]
        MIMD[MIMD<br>多指令多数据]
    end
```

| 类型 | 例子 |
|------|------|
| SISD | 传统单核 CPU |
| SIMD | GPU、向量处理器 |
| MIMD | 多核 CPU、集群 |

### 2.2 并行层次

```mermaid
graph TB
    subgraph "并行层次"
        L1[指令级并行<br>ILP]
        L2[数据级并行<br>SIMD]
        L3[线程级并行<br>多线程]
        L4[进程级并行<br>多进程]
        L5[节点级并行<br>分布式]
    end
```

---

## 三、并行编程模型

### 3.1 共享内存模型

```mermaid
graph TB
    subgraph "共享内存"
        T1[线程1] --> MEM[共享内存]
        T2[线程2] --> MEM
        T3[线程3] --> MEM
    end
```

**特点**：
- 线程间共享地址空间
- 通过内存通信
- 需要同步机制

**实现**：OpenMP、Pthreads

### 3.2 分布式内存模型

```mermaid
graph TB
    subgraph "分布式内存"
        P1[进程1<br>内存1] <-->|消息| P2[进程2<br>内存2]
        P2 <-->|消息| P3[进程3<br>内存3]
    end
```

**特点**：
- 进程独立地址空间
- 通过消息传递通信
- 显式数据移动

**实现**：MPI

### 3.3 混合模型

```mermaid
graph TB
    subgraph "混合模型"
        subgraph Node1["节点1"]
            P1[进程1]
            P1 --> T1[线程1]
            P1 --> T2[线程2]
        end
        
        subgraph Node2["节点2"]
            P2[进程2]
            P2 --> T3[线程1]
            P2 --> T4[线程2]
        end
        
        P1 <-->|MPI| P2
    end
```

**实现**：MPI + OpenMP

---

## 四、并行算法设计

### 4.1 设计步骤

```mermaid
graph TB
    S1[分解] --> S2[通信]
    S2 --> S3[聚合]
    S3 --> S4[映射]
```

| 步骤 | 内容 |
|------|------|
| 分解 | 划分任务/数据 |
| 通信 | 确定依赖关系 |
| 聚合 | 合并小任务 |
| 映射 | 分配到处理器 |

### 4.2 分解策略

**数据并行**：

```mermaid
graph TB
    subgraph "数据并行"
        DATA[数据] --> D1[块1]
        DATA --> D2[块2]
        DATA --> D3[块3]
        
        D1 --> P1[处理器1]
        D2 --> P2[处理器2]
        D3 --> P3[处理器3]
    end
```

**任务并行**：

```mermaid
graph TB
    subgraph "任务并行"
        TASK[任务]
        
        TASK --> T1[子任务1] --> P1[处理器1]
        TASK --> T2[子任务2] --> P2[处理器2]
        TASK --> T3[子任务3] --> P3[处理器3]
    end
```

---

## 五、性能分析

### 5.1 Amdahl 定律

**加速比公式**：

```
S(n) = 1 / (f + (1-f)/n)

其中：
- S(n): n 个处理器的加速比
- f: 串行部分比例
- n: 处理器数量
```

```mermaid
graph TB
    subgraph "Amdahl 定律"
        A1[串行部分 f = 10%]
        A2[最大加速比 = 10x]
        A3[无论多少处理器]
    end
```

### 5.2 Gustafson 定律

**弱扩展性**：

```
S(n) = n - f × (n - 1)

问题规模随处理器增加
```

### 5.3 效率

```
效率 E = S(n) / n

理想效率 = 1（100%）
```

### 5.4 扩展性

| 类型 | 定义 |
|------|------|
| 强扩展 | 问题固定，增加处理器 |
| 弱扩展 | 每处理器工作量固定 |

---

## 六、同步与通信

### 6.1 同步原语

| 原语 | 作用 |
|------|------|
| Barrier | 等待所有线程到达 |
| Lock/Mutex | 互斥访问 |
| Semaphore | 计数信号量 |
| Condition | 条件变量 |

### 6.2 通信模式

```mermaid
graph TB
    subgraph "通信模式"
        P2P[点对点]
        BCAST[广播]
        REDUCE[归约]
        ALLREDUCE[全归约]
        GATHER[收集]
        SCATTER[分发]
    end
```

### 6.3 通信开销

```
通信时间 = 延迟 + 数据量/带宽

T = α + n/β
```

---

## 七、常见并行模式

### 7.1 MapReduce

```mermaid
graph TB
    subgraph "MapReduce"
        INPUT[输入] --> MAP[Map]
        MAP --> SHUFFLE[Shuffle]
        SHUFFLE --> REDUCE[Reduce]
        REDUCE --> OUTPUT[输出]
    end
```

### 7.2 流水线

```mermaid
graph TB
    subgraph "流水线"
        S1[阶段1] --> S2[阶段2] --> S3[阶段3]
    end
```

### 7.3 分治

```mermaid
graph TB
    subgraph "分治"
        P[问题]
        P --> P1[子问题1]
        P --> P2[子问题2]
        
        P1 --> S1[解1]
        P2 --> S2[解2]
        
        S1 --> M[合并]
        S2 --> M
    end
```

---

## 八、AI 中的并行

### 8.1 数据并行

```mermaid
graph TB
    subgraph "数据并行训练"
        DATA[训练数据]
        
        DATA --> B1[Batch 1] --> GPU1[GPU 1]
        DATA --> B2[Batch 2] --> GPU2[GPU 2]
        
        GPU1 --> AR[AllReduce 梯度]
        GPU2 --> AR
    end
```

### 8.2 模型并行

```mermaid
graph TB
    subgraph "模型并行"
        GPU1[GPU 1<br>Layer 0-10]
        GPU2[GPU 2<br>Layer 11-20]
        GPU3[GPU 3<br>Layer 21-30]
        
        GPU1 --> GPU2 --> GPU3
    end
```

### 8.3 张量并行

```mermaid
graph TB
    subgraph "张量并行"
        INPUT[输入]
        
        INPUT --> G1[GPU 1<br>前半权重]
        INPUT --> G2[GPU 2<br>后半权重]
        
        G1 --> AR[AllReduce]
        G2 --> AR
    end
```

---

## 九、并行计算挑战

### 9.1 常见问题

| 问题 | 描述 |
|------|------|
| 负载不均 | 处理器工作量不均 |
| 通信开销 | 通信占比过高 |
| 同步开销 | 等待时间长 |
| 竞争条件 | 并发访问问题 |
| 死锁 | 循环等待 |

### 9.2 调优方向

```mermaid
graph TB
    subgraph "并行调优"
        O1[减少通信]
        O2[负载均衡]
        O3[重叠计算通信]
        O4[减少同步]
    end
```

---

## 十、总结

### 10.1 核心认知

1. **并行是必然趋势**
   - 串行性能增长放缓

2. **多种并行模型**
   - 共享内存、分布式、混合

3. **性能有理论上限**
   - Amdahl 定律

4. **AI 大量使用并行**
   - 数据并行、模型并行

### 10.2 学习建议

```mermaid
graph TB
    L1[理解概念] --> L2[学习 OpenMP]
    L2 --> L3[学习 MPI]
    L3 --> L4[学习 GPU 并行]
```

---

## 相关文章

- [上一篇：01 - HPC 概述与发展史](@/articles/hpc/hpc-01-HPC概述与发展史.md)
- [下一篇：03 - MPI 分布式编程](@/articles/hpc/hpc-03-MPI分布式编程.md)
- [21 - CUDA 入门与 GPU 编程基础](@/articles/ai/ai-21-CUDA入门与GPU编程基础.md)
