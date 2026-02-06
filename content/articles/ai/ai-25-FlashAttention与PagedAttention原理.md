+++
title = "25.FlashAttention与PagedAttention原理"
date = 2026-02-06
description = "LLM推理优化核心：FlashAttention分块算法、在线Softmax、PagedAttention内存管理、vLLM实现详解"
[taxonomies]
tags = ["attention", "flash-attention", "paged-attention", "vllm", "llm", "inference"]
+++

## 概述

FlashAttention 和 PagedAttention 是 LLM 推理优化的两大核心技术。FlashAttention 解决了 Attention 计算的内存瓶颈，PagedAttention 解决了 KV Cache 的内存管理问题。本文深入剖析这两种技术的原理和实现。

---

## 一、Attention 计算瓶颈

### 1.1 标准 Attention

```
标准 Self-Attention：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  输入：Q, K, V ∈ R^{N × d}                                          │
│  输出：O = softmax(QK^T / √d) V                                     │
│                                                                      │
│  计算步骤：                                                          │
│  ━━━━━━━━━━                                                         │
│  1. S = QK^T / √d           # 计算注意力分数，O(N²d)                │
│  2. P = softmax(S)          # 行级 Softmax                          │
│  3. O = PV                  # 加权求和                              │
│                                                                      │
│  内存访问：                                                          │
│  ━━━━━━━━━                                                          │
│                                                                      │
│  ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐                  │
│  │   Q   │ ×  │  K^T  │ =  │   S   │ →  │   P   │                  │
│  │ N × d │    │ d × N │    │ N × N │    │ N × N │                  │
│  └───────┘    └───────┘    └───────┘    └───────┘                  │
│       ↓                                       ↓                      │
│     HBM                                     HBM                      │
│   (读 Q)                              (写 S，读回算 softmax)         │
│                                                                      │
│  问题：                                                              │
│  • S 和 P 矩阵大小为 N × N                                          │
│  • N = 序列长度（可达 128K+）                                       │
│  • 128K × 128K × FP16 = 32GB！                                      │
│  • 大量 HBM 读写，成为瓶颈                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 内存带宽瓶颈

```
Attention 的 IO 复杂度：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  标准 Attention：                                                    │
│  ━━━━━━━━━━━━━━                                                     │
│  • 计算复杂度：O(N²d)                                               │
│  • 内存复杂度：O(N²)（存储 S 和 P）                                 │
│  • IO 复杂度：O(N²)（多次读写 HBM）                                 │
│                                                                      │
│  内存访问模式：                                                      │
│  ━━━━━━━━━━━━━━                                                     │
│  Step 1: 读 Q, K 从 HBM，计算 S，写 S 到 HBM                        │
│  Step 2: 读 S 从 HBM，计算 softmax(S)，写 P 到 HBM                  │
│  Step 3: 读 P, V 从 HBM，计算 O，写 O 到 HBM                        │
│                                                                      │
│  总 IO：Θ(N²) 读写                                                  │
│                                                                      │
│  实际问题（A100，序列长度 2048）：                                  │
│  • S 矩阵大小：2048 × 2048 × 4B = 16MB                              │
│  • HBM 带宽：2 TB/s                                                 │
│  • 传输时间：~8μs                                                   │
│  • 计算时间：~1μs（Tensor Core 很快）                               │
│  • 瓶颈：内存，不是计算！                                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 注意力变体：MHA、MQA、GQA

```
注意力机制变体对比：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  MHA (Multi-Head Attention) - 原始 Transformer                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                    │
│                                                                      │
│     Q Heads:  H1   H2   H3   H4   H5   H6   H7   H8                  │
│               ↓    ↓    ↓    ↓    ↓    ↓    ↓    ↓                  │
│     K Heads:  K1   K2   K3   K4   K5   K6   K7   K8                  │
│     V Heads:  V1   V2   V3   V4   V5   V6   V7   V8                  │
│                                                                      │
│     • 每个 Q head 有独立的 K, V head                                 │
│     • KV Cache 大小 = n_heads × d_head × 2 × seq_len                │
│     • 质量最好，但内存开销最大                                       │
│                                                                      │
│  MQA (Multi-Query Attention) - 共享 K, V                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                             │
│                                                                      │
│     Q Heads:  H1   H2   H3   H4   H5   H6   H7   H8                  │
│               ↓    ↓    ↓    ↓    ↓    ↓    ↓    ↓                  │
│     K Head:   ───────────────── K1 ─────────────────                 │
│     V Head:   ───────────────── V1 ─────────────────                 │
│                                                                      │
│     • 所有 Q head 共享同一个 K, V head                               │
│     • KV Cache 减少到 1/n_heads                                      │
│     • 推理速度快，但质量有损失                                       │
│     • 代表：PaLM, Falcon                                             │
│                                                                      │
│  GQA (Grouped Query Attention) - 折中方案                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                             │
│                                                                      │
│     Q Heads:  H1   H2   H3   H4   H5   H6   H7   H8                  │
│               ↓    ↓    ↓    ↓    ↓    ↓    ↓    ↓                  │
│     K Heads:  ─── K1 ───  ─── K2 ───  ─── K3 ───  ─── K4 ───        │
│     V Heads:  ─── V1 ───  ─── V2 ───  ─── V3 ───  ─── V4 ───        │
│                                                                      │
│     • 多个 Q head 共享一组 K, V head                                 │
│     • n_kv_heads = n_heads / group_size                              │
│     • 例：8 Q heads, 4 KV heads → 每 2 个 Q 共享 1 个 KV             │
│     • 平衡质量与效率                                                 │
│     • 代表：LLaMA-2, Mistral, DeepSeek                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

```
KV Cache 内存对比（以 LLaMA-2 70B 为例）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  模型配置：                                                          │
│  • n_layers = 80                                                    │
│  • n_heads = 64 (Q heads)                                           │
│  • d_head = 128                                                     │
│  • seq_len = 4096                                                   │
│                                                                      │
│  ┌────────────┬──────────────┬────────────┬─────────────┐           │
│  │   方案     │  n_kv_heads  │  KV Cache  │   相对MHA   │           │
│  ├────────────┼──────────────┼────────────┼─────────────┤           │
│  │ MHA        │     64       │   40 GB    │    100%     │           │
│  │ GQA-8      │      8       │    5 GB    │    12.5%    │           │
│  │ MQA        │      1       │  0.625 GB  │    1.56%    │           │
│  └────────────┴──────────────┴────────────┴─────────────┘           │
│                                                                      │
│  LLaMA-2 70B 使用 GQA-8：                                           │
│  • n_kv_heads = 8                                                   │
│  • 每 8 个 Q head 共享 1 组 KV                                       │
│  • KV Cache 节省 87.5%                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

```python
# GQA 实现示例
import torch
import torch.nn as nn
import torch.nn.functional as F

class GroupedQueryAttention(nn.Module):
    """
    Grouped Query Attention (GQA) 实现
    """
    def __init__(
        self,
        d_model: int,
        n_heads: int,       # Q heads 数量
        n_kv_heads: int,    # K, V heads 数量
        dropout: float = 0.0
    ):
        super().__init__()
        assert n_heads % n_kv_heads == 0
        
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.n_rep = n_heads // n_kv_heads  # 每组共享的 Q head 数
        self.d_head = d_model // n_heads
        
        # Q 有 n_heads 个 head
        self.wq = nn.Linear(d_model, n_heads * self.d_head, bias=False)
        # K, V 只有 n_kv_heads 个 head
        self.wk = nn.Linear(d_model, n_kv_heads * self.d_head, bias=False)
        self.wv = nn.Linear(d_model, n_kv_heads * self.d_head, bias=False)
        self.wo = nn.Linear(n_heads * self.d_head, d_model, bias=False)
        
        self.dropout = nn.Dropout(dropout)
        self.scale = self.d_head ** -0.5
    
    def repeat_kv(self, x: torch.Tensor) -> torch.Tensor:
        """
        将 KV heads 复制以匹配 Q heads 数量
        (B, n_kv_heads, S, d_head) -> (B, n_heads, S, d_head)
        """
        if self.n_rep == 1:
            return x
        B, n_kv, S, d = x.shape
        return (
            x[:, :, None, :, :]
            .expand(B, n_kv, self.n_rep, S, d)
            .reshape(B, n_kv * self.n_rep, S, d)
        )
    
    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor = None,
        kv_cache: tuple = None
    ):
        B, S, _ = x.shape
        
        # 计算 Q, K, V
        q = self.wq(x).view(B, S, self.n_heads, self.d_head).transpose(1, 2)
        k = self.wk(x).view(B, S, self.n_kv_heads, self.d_head).transpose(1, 2)
        v = self.wv(x).view(B, S, self.n_kv_heads, self.d_head).transpose(1, 2)
        
        # KV Cache 处理
        if kv_cache is not None:
            k_cache, v_cache = kv_cache
            k = torch.cat([k_cache, k], dim=2)
            v = torch.cat([v_cache, v], dim=2)
        
        # 复制 K, V 以匹配 Q heads
        k = self.repeat_kv(k)  # (B, n_heads, S, d_head)
        v = self.repeat_kv(v)  # (B, n_heads, S, d_head)
        
        # Attention 计算
        attn = torch.matmul(q, k.transpose(-2, -1)) * self.scale
        
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))
        
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)
        
        out = torch.matmul(attn, v)
        out = out.transpose(1, 2).contiguous().view(B, S, -1)
        
        return self.wo(out), (k, v)
```

---

## 二、FlashAttention 原理

### 2.1 核心思想

```
FlashAttention 核心思想：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  1. 分块计算（Tiling）                                              │
│  ━━━━━━━━━━━━━━━━━━━━━                                              │
│  • 将 Q, K, V 分成小块                                              │
│  • 小块可以放入 SRAM（共享内存）                                    │
│  • 在 SRAM 中完成计算，避免中间结果写回 HBM                         │
│                                                                      │
│  2. 在线 Softmax（Online Softmax）                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                    │
│  • 不需要完整的 S 矩阵来计算 softmax                                │
│  • 逐块计算，动态更新 max 和 sum                                    │
│  • 最终得到正确的 softmax 结果                                      │
│                                                                      │
│  3. 重计算（Recomputation）                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━                                          │
│  • 反向传播时重新计算 S 和 P                                        │
│  • 用计算换内存                                                     │
│  • 总体更快（减少 IO）                                              │
│                                                                      │
│  效果：                                                              │
│  • IO 复杂度：O(N²d / M)，M 是 SRAM 大小                            │
│  • 内存复杂度：O(N)，不存储完整 S/P                                 │
│  • 速度提升：2-4x                                                   │
│  • 支持更长序列                                                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 在线 Softmax 算法

```
在线 Softmax（核心数学）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  标准 Softmax：                                                      │
│  softmax(x)_i = exp(x_i - max(x)) / Σ exp(x_j - max(x))             │
│                                                                      │
│  问题：需要先遍历一次得到 max，再遍历一次计算                       │
│                                                                      │
│  在线算法（一次遍历）：                                              │
│  ━━━━━━━━━━━━━━━━━━━━━                                              │
│                                                                      │
│  初始化：m = -∞, l = 0                                              │
│                                                                      │
│  对每个新元素 x_i：                                                  │
│    m_new = max(m, x_i)                                              │
│    l_new = l * exp(m - m_new) + exp(x_i - m_new)                    │
│    m = m_new                                                        │
│    l = l_new                                                        │
│                                                                      │
│  最终：softmax(x)_i = exp(x_i - m) / l                              │
│                                                                      │
│  关键洞察：                                                          │
│  当 max 更新时，之前累积的 sum 需要乘以 exp(old_max - new_max)      │
│  来修正                                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

分块版本（FlashAttention 核心）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  对 Q 的第 i 块：                                                    │
│                                                                      │
│  初始化：                                                            │
│    O_i = 0           # 输出累加器                                   │
│    m_i = -∞          # 当前最大值                                   │
│    l_i = 0           # 当前 exp sum                                 │
│                                                                      │
│  对 K, V 的第 j 块：                                                 │
│    S_ij = Q_i @ K_j^T / √d                                          │
│    m_ij = rowmax(S_ij)                                              │
│    P_ij = exp(S_ij - m_ij)                                          │
│    l_ij = rowsum(P_ij)                                              │
│                                                                      │
│    # 更新全局统计                                                    │
│    m_new = max(m_i, m_ij)                                           │
│    l_new = l_i * exp(m_i - m_new) + l_ij * exp(m_ij - m_new)        │
│                                                                      │
│    # 更新输出（关键！）                                              │
│    O_i = O_i * (l_i * exp(m_i - m_new) / l_new)                     │
│        + P_ij * exp(m_ij - m_new) / l_new @ V_j                     │
│                                                                      │
│    m_i = m_new                                                      │
│    l_i = l_new                                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 FlashAttention 实现

```cpp
/*
 * FlashAttention 简化实现
 * 展示核心算法，省略优化细节
 */

__global__ void flash_attention_forward(
    const float* Q,  // [N, d]
    const float* K,  // [N, d]
    const float* V,  // [N, d]
    float* O,        // [N, d]
    int N,           // 序列长度
    int d,           // 头维度
    int Bc,          // K/V 块大小
    int Br           // Q 块大小
) {
    extern __shared__ float smem[];
    
    // 共享内存布局
    float* Qi = smem;                           // [Br, d]
    float* Kj = smem + Br * d;                  // [Bc, d]
    float* Vj = smem + Br * d + Bc * d;         // [Bc, d]
    float* Sij = smem + Br * d + 2 * Bc * d;    // [Br, Bc]
    
    int block_row = blockIdx.x;  // Q 块索引
    int num_k_blocks = (N + Bc - 1) / Bc;
    
    // 加载 Q 块到共享内存
    load_to_smem(Qi, Q + block_row * Br * d, Br, d);
    
    // 初始化
    float mi[Br];      // 每行的 max
    float li[Br];      // 每行的 sum
    float Oi[Br][d];   // 输出累加器
    
    for (int i = 0; i < Br; i++) {
        mi[i] = -INFINITY;
        li[i] = 0.0f;
        for (int j = 0; j < d; j++) {
            Oi[i][j] = 0.0f;
        }
    }
    
    // 遍历 K/V 块
    for (int j = 0; j < num_k_blocks; j++) {
        // 加载 K, V 块
        load_to_smem(Kj, K + j * Bc * d, Bc, d);
        load_to_smem(Vj, V + j * Bc * d, Bc, d);
        __syncthreads();
        
        // 计算 S_ij = Q_i @ K_j^T
        matmul(Sij, Qi, Kj, Br, Bc, d);
        
        // 缩放
        for (int i = 0; i < Br; i++) {
            for (int k = 0; k < Bc; k++) {
                Sij[i * Bc + k] /= sqrtf((float)d);
            }
        }
        
        // Causal mask（可选）
        if (causal) {
            int q_start = block_row * Br;
            int k_start = j * Bc;
            for (int i = 0; i < Br; i++) {
                for (int k = 0; k < Bc; k++) {
                    if (q_start + i < k_start + k) {
                        Sij[i * Bc + k] = -INFINITY;
                    }
                }
            }
        }
        
        // 计算块内 max 和 exp
        float mij[Br];
        float lij[Br];
        float Pij[Br][Bc];
        
        for (int i = 0; i < Br; i++) {
            mij[i] = -INFINITY;
            for (int k = 0; k < Bc; k++) {
                mij[i] = fmaxf(mij[i], Sij[i * Bc + k]);
            }
            
            lij[i] = 0.0f;
            for (int k = 0; k < Bc; k++) {
                Pij[i][k] = expf(Sij[i * Bc + k] - mij[i]);
                lij[i] += Pij[i][k];
            }
        }
        
        // 更新全局统计和输出
        for (int i = 0; i < Br; i++) {
            float mi_new = fmaxf(mi[i], mij[i]);
            float li_new = li[i] * expf(mi[i] - mi_new) + 
                           lij[i] * expf(mij[i] - mi_new);
            
            // 修正之前的输出
            float scale_old = li[i] * expf(mi[i] - mi_new) / li_new;
            float scale_new = expf(mij[i] - mi_new) / li_new;
            
            for (int k = 0; k < d; k++) {
                Oi[i][k] = Oi[i][k] * scale_old;
            }
            
            // 累加新的贡献
            for (int k = 0; k < d; k++) {
                for (int c = 0; c < Bc; c++) {
                    Oi[i][k] += Pij[i][c] * scale_new * Vj[c * d + k];
                }
            }
            
            mi[i] = mi_new;
            li[i] = li_new;
        }
        
        __syncthreads();
    }
    
    // 写回输出
    store_from_reg(O + block_row * Br * d, Oi, Br, d);
}
```

### 2.4 FlashAttention-2 改进

```
FlashAttention-2 优化：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  1. 减少非 GEMM 计算                                                │
│  ━━━━━━━━━━━━━━━━━━━━                                               │
│  • 将 softmax 缩放推迟到最后                                        │
│  • 减少 exp 和 div 计算次数                                         │
│                                                                      │
│  2. 并行化改进                                                       │
│  ━━━━━━━━━━━━━━                                                     │
│  • V1：沿 batch 和 head 并行                                        │
│  • V2：增加沿序列长度并行                                           │
│  • 更好的 GPU 利用率                                                │
│                                                                      │
│  3. 工作分配优化                                                     │
│  ━━━━━━━━━━━━━━━━                                                   │
│  • 减少通信开销                                                     │
│  • 更好的 Warp 内工作划分                                           │
│                                                                      │
│  4. 内存访问优化                                                     │
│  ━━━━━━━━━━━━━━━━                                                   │
│  • 交换循环顺序（外层 Q，内层 K/V）                                 │
│  • 减少 HBM 访问次数                                                │
│                                                                      │
│  性能提升：比 V1 快 2x                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、PagedAttention 原理

### 3.1 KV Cache 问题

```
KV Cache 内存问题：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  LLM 推理流程：                                                      │
│  ━━━━━━━━━━━━━━                                                     │
│  1. Prefill：处理输入 prompt，计算所有 token 的 K, V               │
│  2. Decode：逐个生成 token，复用之前的 K, V                        │
│                                                                      │
│  KV Cache 作用：                                                     │
│  ━━━━━━━━━━━━━━                                                     │
│  • 缓存已计算的 K, V，避免重复计算                                  │
│  • 每生成一个 token 只需计算新 token 的 K, V                       │
│                                                                      │
│  内存开销（以 LLaMA-13B 为例）：                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                      │
│  • 40 layers × 40 heads × 128 dim × 2 (K+V)                        │
│  • = 409,600 bytes per token                                       │
│  • 2048 序列长度 → 800MB per sequence                              │
│  • batch_size=16 → 12.8GB 仅 KV Cache！                            │
│                                                                      │
│  传统方法的问题：                                                    │
│  ━━━━━━━━━━━━━━━━                                                   │
│  • 预分配最大序列长度的内存                                         │
│  • 大量内存浪费（短序列也占满）                                     │
│  • 内存碎片化                                                       │
│  • 无法动态调整 batch size                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 PagedAttention 核心思想

```
PagedAttention（来自 vLLM）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  灵感来源：操作系统的虚拟内存分页                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                   │
│                                                                      │
│  传统 KV Cache：                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Seq 1: [K1 V1][K2 V2][K3 V3][─────空白浪费──────]           │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ Seq 2: [K1 V1][K2 V2][K3 V3][K4 V4][K5 V5][───空白───]     │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ Seq 3: [K1 V1][K2 V2][────────────空白浪费─────────]        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  问题：每个序列预分配 max_seq_len，大量浪费                         │
│                                                                      │
│  PagedAttention：                                                    │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  物理 Block Pool                                           │     │
│  │  ┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐┌────┐...           │     │
│  │  │ B0 ││ B1 ││ B2 ││ B3 ││ B4 ││ B5 ││Free│              │     │
│  │  └────┘└────┘└────┘└────┘└────┘└────┘└────┘               │     │
│  │    ↑      ↑      ↑      ↑      ↑      ↑                   │     │
│  │    │      │      │      │      │      │                   │     │
│  │  Seq1   Seq2   Seq1   Seq3   Seq2   Seq3                  │     │
│  │  [0:16] [0:16] [16:32] [0:16] [16:32] [16:32]             │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  Block Table（逻辑到物理映射）：                                    │
│  ┌──────────────────────────────────────────┐                       │
│  │ Seq 1: logical [0,1] → physical [B0, B2] │                       │
│  │ Seq 2: logical [0,1] → physical [B1, B4] │                       │
│  │ Seq 3: logical [0,1] → physical [B3, B5] │                       │
│  └──────────────────────────────────────────┘                       │
│                                                                      │
│  优点：                                                              │
│  • 按需分配，无内存浪费                                             │
│  • 利用率接近 100%                                                  │
│  • 支持动态 batch                                                   │
│  • 支持序列间共享 (copy-on-write)                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 PagedAttention Kernel

```cpp
/*
 * PagedAttention Kernel 简化实现
 */

// Block 结构
struct KVBlock {
    half k[BLOCK_SIZE][HEAD_DIM];  // Key cache
    half v[BLOCK_SIZE][HEAD_DIM];  // Value cache
};

// Block Table
// block_table[seq_id][logical_block_id] = physical_block_id

__global__ void paged_attention_kernel(
    const float* __restrict__ q,           // [num_seqs, num_heads, head_dim]
    const KVBlock* __restrict__ kv_cache,  // 物理 block pool
    const int* __restrict__ block_tables,  // [num_seqs, max_blocks]
    const int* __restrict__ context_lens,  // [num_seqs]
    float* __restrict__ output,            // [num_seqs, num_heads, head_dim]
    int num_seqs,
    int num_heads,
    int head_dim,
    int max_blocks,
    float scale
) {
    int seq_idx = blockIdx.x;
    int head_idx = blockIdx.y;
    int tid = threadIdx.x;
    
    extern __shared__ float smem[];
    float* q_smem = smem;
    float* logits = smem + head_dim;
    
    // 加载 Query
    if (tid < head_dim) {
        q_smem[tid] = q[seq_idx * num_heads * head_dim + 
                        head_idx * head_dim + tid];
    }
    __syncthreads();
    
    int context_len = context_lens[seq_idx];
    int num_blocks = (context_len + BLOCK_SIZE - 1) / BLOCK_SIZE;
    
    // 遍历所有 block
    float max_logit = -INFINITY;
    float sum_exp = 0.0f;
    float output_acc[HEAD_DIM] = {0.0f};
    
    for (int b = 0; b < num_blocks; b++) {
        // 查找物理 block
        int physical_block = block_tables[seq_idx * max_blocks + b];
        const KVBlock* block = &kv_cache[physical_block];
        
        // 计算这个 block 中的有效 token 数
        int block_start = b * BLOCK_SIZE;
        int block_end = min(block_start + BLOCK_SIZE, context_len);
        int num_tokens = block_end - block_start;
        
        // 计算 attention scores
        for (int t = tid; t < num_tokens; t += blockDim.x) {
            float score = 0.0f;
            for (int d = 0; d < head_dim; d++) {
                score += q_smem[d] * __half2float(block->k[t][d]);
            }
            logits[t] = score * scale;
            max_logit = fmaxf(max_logit, logits[t]);
        }
        __syncthreads();
        
        // Warp 归约 max
        max_logit = warp_reduce_max(max_logit);
        
        // 计算 exp 和 sum
        for (int t = tid; t < num_tokens; t += blockDim.x) {
            float exp_val = expf(logits[t] - max_logit);
            sum_exp += exp_val;
            
            // 累加到输出
            for (int d = 0; d < head_dim; d++) {
                output_acc[d] += exp_val * __half2float(block->v[t][d]);
            }
        }
        __syncthreads();
    }
    
    // 归一化
    sum_exp = warp_reduce_sum(sum_exp);
    
    // 写回
    if (tid < head_dim) {
        output[seq_idx * num_heads * head_dim + head_idx * head_dim + tid] = 
            output_acc[tid] / sum_exp;
    }
}
```

### 3.4 Continuous Batching

```
Continuous Batching（连续批处理）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  传统 Static Batching：                                             │
│  ━━━━━━━━━━━━━━━━━━━━━━                                             │
│                                                                      │
│  Time →                                                              │
│  Seq1: ████████████████████████████████ (长)                        │
│  Seq2: ████████████ (短，等待)         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓               │
│  Seq3: █████████████████ (中，等待)    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓               │
│  Seq4: ██████████████████████ (等待)   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓               │
│                                                                      │
│  问题：短序列完成后空转，等待最长序列                               │
│                                                                      │
│  ────────────────────────────────────────────────────────────────   │
│                                                                      │
│  Continuous Batching：                                               │
│  ━━━━━━━━━━━━━━━━━━━━━                                              │
│                                                                      │
│  Time →                                                              │
│  Seq1: ████████████████████████████████                             │
│  Seq2: ████████████ → Seq5: ████████████ → Seq8: ████               │
│  Seq3: █████████████████ → Seq6: ███████████████ → ...              │
│  Seq4: ██████████████████████ → Seq7: ██████████████ → ...          │
│                                                                      │
│  优点：                                                              │
│  • 序列完成后立即加入新序列                                         │
│  • GPU 利用率最大化                                                 │
│  • 吞吐量提升 2-3x                                                  │
│                                                                      │
│  实现要点：                                                          │
│  • PagedAttention 支持动态内存                                      │
│  • Scheduler 管理序列调度                                           │
│  • 每个 iteration 重新组装 batch                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、vLLM 架构

### 4.1 整体架构

```
vLLM 系统架构：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      LLMEngine                               │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │    │
│  │  │  Scheduler  │  │   Tokenizer │  │  Sampler            │  │    │
│  │  │             │  │             │  │  (temperature,top_p)│  │    │
│  │  └──────┬──────┘  └─────────────┘  └─────────────────────┘  │    │
│  │         │                                                    │    │
│  │         ▼                                                    │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │                  Block Manager                       │    │    │
│  │  │  ┌───────────────┐  ┌───────────────────────────┐   │    │    │
│  │  │  │ Block Table   │  │ Physical Block Pool       │   │    │    │
│  │  │  │ Management    │  │ (GPU KV Cache Memory)     │   │    │    │
│  │  │  └───────────────┘  └───────────────────────────┘   │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  │         │                                                    │    │
│  │         ▼                                                    │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │                    Worker                            │    │    │
│  │  │  ┌─────────────┐  ┌─────────────────────────────┐   │    │    │
│  │  │  │   Model     │  │  PagedAttention Kernel      │   │    │    │
│  │  │  │  (HuggingFace)│  │                             │   │    │    │
│  │  │  └─────────────┘  └─────────────────────────────┘   │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 调度策略

```python
"""
vLLM Scheduler 简化逻辑
"""

class Scheduler:
    def __init__(self, block_manager):
        self.waiting = []     # 等待处理的请求
        self.running = []     # 正在执行的请求
        self.swapped = []     # 被换出的请求
        self.block_manager = block_manager
    
    def schedule(self):
        """决定本次迭代处理哪些序列"""
        scheduled = []
        
        # 1. 优先处理 running 中的序列（decode）
        for seq in self.running:
            if self.block_manager.can_allocate(seq):
                self.block_manager.allocate(seq)
                scheduled.append(seq)
            else:
                # 内存不足，需要 preempt
                self.preempt(seq)
        
        # 2. 加入新的 waiting 序列（prefill）
        while self.waiting and self.block_manager.has_free_blocks():
            seq = self.waiting.pop(0)
            if self.block_manager.can_allocate(seq):
                self.block_manager.allocate(seq)
                scheduled.append(seq)
                self.running.append(seq)
            else:
                self.waiting.insert(0, seq)
                break
        
        # 3. 恢复 swapped 序列
        while self.swapped and self.block_manager.has_free_blocks():
            seq = self.swapped.pop(0)
            if self.block_manager.can_swap_in(seq):
                self.block_manager.swap_in(seq)
                scheduled.append(seq)
                self.running.append(seq)
        
        return scheduled
    
    def preempt(self, seq):
        """内存不足时的抢占策略"""
        # 策略 1: Recompute - 释放 KV cache，之后重新计算
        # 策略 2: Swap - 换出到 CPU 内存
        if self.should_swap(seq):
            self.block_manager.swap_out(seq)
            self.swapped.append(seq)
        else:
            self.block_manager.free(seq)
            self.waiting.insert(0, seq)
```

### 4.3 使用 vLLM

```python
# vLLM 使用示例

from vllm import LLM, SamplingParams

# 初始化
llm = LLM(
    model="meta-llama/Llama-2-7b-chat-hf",
    tensor_parallel_size=1,  # 使用 1 个 GPU
    gpu_memory_utilization=0.9,  # GPU 内存利用率
)

# 采样参数
sampling_params = SamplingParams(
    temperature=0.8,
    top_p=0.95,
    max_tokens=512,
)

# 批量推理
prompts = [
    "What is machine learning?",
    "Explain quantum computing.",
    "How does a neural network work?",
]

outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    print(f"Prompt: {output.prompt}")
    print(f"Generated: {output.outputs[0].text}")
    print()

# 流式输出
from vllm import AsyncLLMEngine

engine = AsyncLLMEngine.from_engine_args(engine_args)

async def generate_stream(prompt):
    async for output in engine.generate(prompt, sampling_params, request_id):
        yield output.outputs[0].text
```

---

## 五、性能对比

```
Attention 优化性能对比（A100，序列长度 2048）：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  方法                    │ 速度      │ 内存      │ 备注             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  PyTorch 标准            │ 1x        │ 16GB      │ 基线             │
│  PyTorch SDPA           │ 2x        │ 8GB       │ 内置优化         │
│  FlashAttention-1       │ 3x        │ 线性      │                  │
│  FlashAttention-2       │ 5x        │ 线性      │ 当前最优         │
│                                                                      │
│  LLM 推理吞吐量（LLaMA-7B，A100）：                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                      │
│  方法                    │ 吞吐量    │ 延迟      │                  │
│  HuggingFace             │ 20 tok/s  │ 高        │                  │
│  TGI                     │ 100 tok/s │ 中        │                  │
│  vLLM                    │ 200 tok/s │ 低        │ PagedAttention   │
│  vLLM + FlashAttention   │ 250 tok/s │ 最低      │ 组合使用         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 六、实践建议

```
FlashAttention / PagedAttention 使用建议：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  何时使用 FlashAttention：                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━                                           │
│  • 长序列训练/推理                                                  │
│  • 内存受限场景                                                     │
│  • 需要支持更大 batch size                                          │
│  • PyTorch 2.0+ 已内置 (torch.nn.functional.scaled_dot_product_attention)│
│                                                                      │
│  何时使用 PagedAttention：                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━                                          │
│  • LLM 推理服务                                                     │
│  • 高并发场景                                                       │
│  • 动态 batch 需求                                                  │
│  • 使用 vLLM 框架                                                   │
│                                                                      │
│  注意事项：                                                          │
│  ━━━━━━━━━                                                          │
│  • FlashAttention 需要特定 GPU 架构（Ampere+）                      │
│  • 头维度需要是 32 的倍数                                           │
│  • 某些变体（如 cross attention）支持有限                           │
│  • 调试更困难（融合 Kernel）                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 相关文章

- [上一篇：24 - GPU Kernel 开发详解](/articles/ai/ai-24-GPU-Kernel开发详解/)
- [下一篇：26 - ROCm 与 AMD GPU 开发](/articles/ai/ai-26-ROCm与AMD-GPU开发/)
- [16 - 推理框架优化技术详解](/articles/ai/ai-16-推理框架优化技术详解/)
- [19 - DeepSeek 推理优化技术详解](/articles/ai/ai-19-DeepSeek推理优化技术详解/)
