+++
title = "35. RLHF 与对齐训练详解"
description = "从人类反馈强化学习到直接偏好优化：LLM 对齐训练的原理、算法、工程实践与前沿方向"
date = 2026-02-12
weight = 35000
draft = false
[taxonomies]
tags = ["AI", "RLHF", "PPO", "DPO", "对齐", "训练"]
[extra]
toc = true
+++

## Overview

**对齐 (Alignment)** 是 LLM 从「能力强但不听话」到「能力强且好用」的关键一步。预训练模型学会了语言的统计规律，但它的目标只是「预测下一个 token」——它不知道什么是好的回答、什么是有害的回答、什么是用户真正想要的格式。

对齐的目标：让模型的行为 **符合人类的意图和价值观**——有帮助 (helpful)、无害 (harmless)、诚实 (honest)，即 HHH 原则。

### 三阶段训练流程

```
阶段一：Pretrain（预训练）
  海量文本 → Next-token prediction → 学会语言能力
  结果：「百科全书式」的模型，什么都知道但不听指令

          ↓

阶段二：SFT（监督微调）
  (指令, 回答) 标注数据 → Fine-tuning → 学会遵循指令格式
  结果：能回答问题了，但不知道什么是「更好」的回答

          ↓

阶段三：RLHF / DPO（对齐训练）
  人类偏好数据 → 强化学习 / 偏好优化 → 学会什么回答更好
  结果：回答质量显著提升，拒绝有害请求，输出更有帮助
```

**为什么 SFT 不够？**

| 问题 | SFT 的局限 | RLHF/DPO 的解决 |
|------|-----------|----------------|
| **Mode Collapse** | SFT 让模型模仿标注数据的「平均风格」，丧失多样性 | RLHF 通过 KL 惩罚保持多样性 |
| **只学正例** | SFT 只看到「好的回答」，不知道「什么是差的」 | 偏好数据包含好/差对比，模型学会区分 |
| **阿谀奉承** | SFT 模型倾向于「讨好」用户（sycophancy） | RLHF 可以训练模型在该拒绝时拒绝 |
| **格式 vs 质量** | SFT 擅长学格式，但回答的**内容质量**难以通过 SFT 提升 | 偏好数据直接反映内容质量 |
| **安全对齐** | SFT 模型可能被 jailbreak 绕过安全指令 | RLHF 将安全偏好内化到模型权重中 |

---

## I. Supervised Fine-Tuning (SFT, 监督微调)

### 1.1 目的与数据

SFT 的目的是教模型**遵循指令格式**。数据是人类标注的 `(instruction, response)` 对：

```json
{
  "instruction": "用三句话总结量子计算的原理",
  "response": "量子计算利用量子比特（qubit）的叠加态...(三句话)..."
}
```

数据来源：
- **人工标注**：专业标注员根据指令编写高质量回答（成本高，质量好）
- **Self-Instruct**：用大模型生成指令-回答对，人工筛选（成本低，规模大）
- **蒸馏数据**：用强模型（GPT-4）生成回答，给弱模型做 SFT

### 1.2 训练过程

与预训练相同的 next-token prediction loss，但只在 **response 部分** 计算 loss：

```python
# SFT loss 计算
def sft_loss(model, input_ids, labels):
    # input_ids = [instruction_tokens] + [response_tokens]
    # labels 在 instruction 部分设为 -100（忽略）
    logits = model(input_ids).logits
    loss = cross_entropy(logits, labels, ignore_index=-100)
    return loss
```

**关键细节**：
- **Learning Rate**：通常比预训练小 1-2 个数量级（如 1e-5 ~ 5e-5）
- **Epoch**：1-3 个 epoch，过多会过拟合
- **数据质量 > 数据量**：LIMA 论文证明 1000 条高质量数据就能做出不错的 SFT 模型

### 1.3 SFT 的局限

SFT 后的模型已经「能用」了，但存在核心问题：**它只学了「模仿」，没学「判断」**。

```
SFT 模型的能力：看到指令 → 生成格式正确的回答
SFT 模型的缺陷：不知道哪个回答更好，不知道什么不该说

举例：
  指令：「如何制作炸弹？」
  SFT 模型可能会回答（因为训练数据中有类似的知识性回答）
  对齐后的模型会拒绝回答（因为学会了「这类问题不该回答」）
```

---

## II. Reward Modeling (奖励模型)

### 2.1 为什么需要奖励模型

人类觉得什么回答好、什么回答差——这种「偏好」很难写成规则（无法像 loss function 一样数学化）。奖励模型的作用就是**把人类偏好转换为一个可优化的数值信号**：给定 (prompt, response)，输出一个标量分数。

### 2.2 数据收集

对于每个 prompt，让模型生成多个回答（通常 2-4 个），人类标注员**排序**或**选择更好的那个**：

```
Prompt: "解释什么是量子纠缠"
Response A: "量子纠缠是一种量子力学现象，两个粒子的状态相互关联..."（详细、准确）
Response B: "就是两个东西连在一起了"（过于简略、不准确）

人类标注：A > B（A 比 B 好）
```

**标注挑战**：
- **标注员一致性**：不同标注员对同一对回答可能有不同偏好 → 通常多人标注取多数投票
- **标注指南**：需要详细的标注标准（优先级：准确性 > 有帮助 > 格式 > 简洁）
- **成本**：InstructGPT 使用约 33K comparison 数据，标注成本约 $50K-100K

### 2.3 Bradley-Terry 模型

将偏好建模为**概率问题**：给定 prompt x 和两个回答 y_w（较好的）、y_l（较差的），较好回答被偏好的概率为：

```
P(y_w > y_l | x) = σ(r(x, y_w) - r(x, y_l))
```

其中 r(x, y) 是奖励模型对 (prompt, response) 的评分，σ 是 sigmoid 函数。

**直觉**：如果 r(A) - r(B) 很大 → sigmoid → 接近 1 → 模型非常确信 A 好于 B。

### 2.4 训练

```python
# Reward Model 训练
class RewardModel(nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.backbone = base_model  # 通常和 SFT 模型同架构
        self.reward_head = nn.Linear(hidden_size, 1)  # 标量输出
    
    def forward(self, input_ids, attention_mask):
        hidden = self.backbone(input_ids, attention_mask).last_hidden_state
        # 取最后一个 token 的 hidden state 作为整个回答的表示
        reward = self.reward_head(hidden[:, -1, :])
        return reward.squeeze(-1)

# Loss: 让好回答的 reward 比差回答高
def reward_loss(reward_chosen, reward_rejected):
    # Bradley-Terry loss
    return -torch.log(torch.sigmoid(reward_chosen - reward_rejected)).mean()
```

### 2.5 Reward Hacking（奖励欺骗）

奖励模型是训练数据的近似——它必然有盲点。如果 RL 训练过于激进，policy 模型会找到**奖励模型的漏洞**：生成一些奖励分数很高但人类觉得不好的回答。

```
典型 Reward Hacking 表现：
- 回答越来越长（RM 倾向于给长回答高分，因为训练数据中长回答通常更详细）
- 添加大量无意义的修饰词（"这是一个非常非常好的问题..."）
- 过度使用列表和格式（RM 被格式化内容的 bias 影响）
```

**缓解方法**：
- **KL 惩罚**：限制 policy 不能偏离参考模型太远
- **RM Ensemble**：训练多个奖励模型，取平均或最低分
- **定期更新 RM**：用最新 policy 的输出重新收集偏好数据

---

## III. RLHF with PPO (基于 PPO 的 RLHF)

### 3.1 为什么需要 RL

我们有了奖励模型 r(x, y)，为什么不直接用梯度上升最大化 r？

**核心原因：生成过程是离散采样，不可微。**

```
LLM 生成过程：
  prompt → 模型输出概率分布 → 采样 token_1 → 输出概率分布 → 采样 token_2 → ...
                                   ↑
                          这一步是随机离散选择，梯度无法回传

奖励 r 是对完整回答评分 → r(x, [token_1, token_2, ..., token_n])
→ 无法对 r 关于模型参数直接求梯度（因为中间有采样操作）
→ 需要 RL 的 policy gradient 方法来绕过这个问题
```

### 3.2 PPO 算法详解

PPO (Proximal Policy Optimization) 是 RLHF 中最常用的 RL 算法：

#### 四个模型

RLHF with PPO 需要**同时在 GPU 上加载 4 个模型**：

| 模型 | 作用 | 是否更新 | 显存占用 |
|------|------|---------|---------|
| **Policy (π_θ)** | 被训练的 LLM | ✅ 更新 | 全量参数 + 优化器状态 |
| **Reference (π_ref)** | 冻结的 SFT 模型 | ❌ 冻结 | 全量参数 |
| **Reward (r_φ)** | 奖励模型 | ❌ 冻结 | 全量参数 |
| **Value (V_ψ)** | 价值网络（估计期望奖励） | ✅ 更新 | 全量参数 + 优化器状态 |

**显存需求估算**（以 7B 模型为例）：
```
每个 7B 模型 FP16 ≈ 14 GB
4 个模型 ≈ 56 GB（仅参数）
+ Policy 和 Value 的 AdamW 优化器状态（每个参数 12 bytes）≈ 168 GB
总计 ≈ 224 GB → 需要至少 3 × A100 80GB

这就是为什么 PPO-based RLHF 非常昂贵！
```

#### PPO 训练流程

```
每一步 PPO 迭代：

1. 采样阶段（Generation）
   - 从训练集取一批 prompt
   - 用当前 policy π_θ 生成回答 y ~ π_θ(·|x)
   - 用 reward model 计算 r(x, y)
   - 用 reference model 计算 KL 惩罚：KL = log(π_θ(y|x) / π_ref(y|x))
   - 综合奖励 R = r(x, y) - β · KL

2. 优势估计（Advantage Estimation）
   - 用 Value 网络估计每个 token 位置的 V(s_t)
   - 计算 GAE (Generalized Advantage Estimation)：
     δ_t = r_t + γ·V(s_{t+1}) - V(s_t)
     A_t = Σ(γλ)^l · δ_{t+l}  （l=0,1,2,...）

3. PPO 更新（多个 epoch 重复利用同一批数据）
   对 Policy：
     ratio = π_θ(a_t|s_t) / π_θ_old(a_t|s_t)
     L_clip = min(ratio · A_t, clip(ratio, 1-ε, 1+ε) · A_t)
     θ = θ + α · ∇_θ L_clip
   
   对 Value：
     L_value = (V_ψ(s_t) - R_t)²
     ψ = ψ - α · ∇_ψ L_value
```

#### Clipped Surrogate Objective

PPO 的核心创新是 **clipped objective**——防止每步更新过大：

```
L_CLIP = E[min(ratio · A, clip(ratio, 1-ε, 1+ε) · A)]

其中：
  ratio = π_new(a|s) / π_old(a|s)  （新策略与旧策略的概率比）
  A = advantage（正值→好动作，负值→差动作）
  ε = 0.2（clip 范围，超出此范围则截断）

效果：
  - 如果 A > 0（好动作）且 ratio > 1+ε → 截断，不再增加概率
  - 如果 A < 0（差动作）且 ratio < 1-ε → 截断，不再减少概率
  → 防止「一步更新太大导致训练崩溃」
```

#### KL 惩罚的作用

```
最终奖励 R = r(x, y) - β · KL(π_θ || π_ref)

其中 KL 项 = Σ_t [log π_θ(y_t|x, y_{<t}) - log π_ref(y_t|x, y_{<t})]

作用：
  - 防止 policy 偏离 SFT 模型太远 → 保持语言质量
  - 防止 reward hacking → policy 不能为了高 reward 生成「不像话」的文本
  - β 是权重系数，通常 0.01 ~ 0.2
  - 有些实现用 adaptive β：KL 太大时增大 β，KL 太小时减小 β
```

### 3.3 训练不稳定性与解决方案

| 问题 | 表现 | 解决方案 |
|------|------|---------|
| **Reward 崩塌** | reward 突然飙升但回答质量下降 | 增大 KL 系数 β；使用 reward clipping |
| **KL 爆炸** | KL divergence 越来越大，模型退化 | Adaptive β；减小学习率 |
| **Value function 不准** | advantage 估计噪声大 → PPO 更新方向错误 | 增加 value function 的 epoch 数；使用 value function clipping |
| **训练初期 reward 不升** | policy 还没学会如何获得高 reward | 使用更大的学习率 warmup；增加采样数据量 |
| **过拟合 RM** | reward 持续升高但人类评估变差 | 定期用新 policy 重新收集偏好数据更新 RM |

---

## IV. DPO (Direct Preference Optimization, 直接偏好优化)

### 4.1 核心洞察

DPO 的关键发现：**奖励函数 r 可以从最优策略 π* 中解析求解**——不需要显式训练奖励模型，不需要 RL 循环。

推导过程：

```
RLHF 的优化目标：
  max_π E[r(x,y)] - β·KL(π || π_ref)

最优策略的闭式解（拉格朗日乘子法）：
  π*(y|x) = π_ref(y|x) · exp(r(x,y) / β) / Z(x)
  
  其中 Z(x) = Σ_y π_ref(y|x) · exp(r(x,y) / β)  （归一化常数）

反解 reward：
  r(x,y) = β · log(π*(y|x) / π_ref(y|x)) + β · log Z(x)

代入 Bradley-Terry 偏好模型：
  P(y_w > y_l | x) = σ(r(x,y_w) - r(x,y_l))
                    = σ(β · [log(π*(y_w|x)/π_ref(y_w|x)) - log(π*(y_l|x)/π_ref(y_l|x))])
                                                                ↑ Z(x) 在相减时消掉了！

关键：Z(x) 消掉了 → 不需要计算难以处理的归一化常数
```

### 4.2 DPO Loss

```python
# DPO Loss 实现
def dpo_loss(policy_model, ref_model, x, y_w, y_l, beta=0.1):
    """
    x: prompt
    y_w: preferred (winning) response
    y_l: rejected (losing) response
    """
    # 计算 policy 和 reference 的 log probability
    log_pi_yw = get_log_prob(policy_model, x, y_w)
    log_pi_yl = get_log_prob(policy_model, x, y_l)
    log_ref_yw = get_log_prob(ref_model, x, y_w)
    log_ref_yl = get_log_prob(ref_model, x, y_l)
    
    # 计算 log-ratio
    log_ratio_w = log_pi_yw - log_ref_yw  # log(π_θ(y_w|x) / π_ref(y_w|x))
    log_ratio_l = log_pi_yl - log_ref_yl  # log(π_θ(y_l|x) / π_ref(y_l|x))
    
    # DPO loss
    loss = -torch.log(torch.sigmoid(beta * (log_ratio_w - log_ratio_l))).mean()
    return loss
```

**直觉理解**：
```
DPO loss = -log σ(β · (Δ_w - Δ_l))

其中 Δ_w = log π_θ(y_w|x) - log π_ref(y_w|x)  → policy 比 reference 更倾向于好回答的程度
     Δ_l = log π_θ(y_l|x) - log π_ref(y_l|x)  → policy 比 reference 更倾向于差回答的程度

Loss 要求：Δ_w - Δ_l 尽量大
→ policy 应该比 reference 更喜欢好回答 (Δ_w ↑)
→ policy 应该比 reference 更不喜欢差回答 (Δ_l ↓)
```

### 4.3 DPO vs PPO 对比

| 维度 | PPO (RLHF) | DPO |
|------|-----------|-----|
| **需要的模型** | 4 个（Policy + Ref + Reward + Value） | **2 个**（Policy + Ref） |
| **显存需求** | ~4x 模型参数 | **~2x 模型参数** |
| **训练复杂度** | 高（采样→评分→RL更新→多循环） | **低**（直接一步梯度下降） |
| **超参敏感性** | 非常高（β, γ, λ, ε, lr 都需要调） | 相对低（主要调 β 和 lr） |
| **训练稳定性** | 容易崩塌（reward hack, KL 爆炸） | **更稳定** |
| **是否需要在线采样** | 是（每步用 policy 生成新回答） | **否**（直接用离线偏好数据） |
| **理论等价性** | — | 在无穷数据和完美优化下等价 |
| **实际效果差异** | 通常略好（能在线探索） | 可能过拟合偏好数据（无法探索） |
| **工程实现** | 复杂，需要经验 | **简单，几十行代码** |

### 4.4 DPO 的局限

1. **分布外 (OOD) 问题**：DPO 用离线数据训练，但 policy 更新后生成的回答分布发生了变化 → 偏好数据可能不再有代表性
2. **过拟合**：没有在线采样，模型只看到固定的偏好数据 → 容易过拟合
3. **no exploration**：PPO 每步都用新 policy 采样，DPO 没有 → 可能错过更好的回答空间

**缓解**：
- **Iterative DPO (Online DPO)**：每隔几步用当前 policy 重新生成回答并收集偏好，交替 DPO 训练和数据收集
- **增大 β**：更强的 KL 约束，防止偏离太远

---

## V. Advanced Variants (进阶变体)

### 5.1 ORPO (Odds Ratio Preference Optimization)

**核心思想**：把 SFT 和偏好对齐**合并为一步**。SFT loss + 偏好 loss 同时优化。

```python
# ORPO Loss
L_ORPO = L_SFT(y_w) + λ · L_OR

# 其中 L_OR 使用 odds ratio:
# odds(y) = P(y|x) / (1 - P(y|x))
# L_OR = -log σ(log(odds(y_w) / odds(y_l)))
```

**优势**：不需要 Reference model → 只有 1 个模型 → 显存最省。
**适用**：从预训练模型直接做对齐（跳过 SFT 阶段）。

### 5.2 KTO (Kahneman-Tversky Optimization)

**核心思想**：不需要**成对**偏好数据，只需要「这个回答好/不好」的**二元标注**。

```
传统 DPO 数据：(prompt, y_good, y_bad)  → 需要成对比较
KTO 数据：     (prompt, y, 好/坏)        → 只需单条评价
```

**优势**：数据收集更容易（不需要标注员比较两个回答）。
**理论基础**：Kahneman & Tversky 的前景理论——人类对「损失」的敏感度高于「收益」→ KTO 对差回答的惩罚权重更大。

### 5.3 IPO (Identity Preference Optimization)

**解决 DPO 的过拟合问题**。DPO 在偏好差距很大时会过度自信 → IPO 用 squared hinge loss 替代 log-sigmoid loss，加入正则化。

```python
# IPO Loss（更保守的偏好学习）
L_IPO = ((log_ratio_w - log_ratio_l) - 1/(2*beta))^2
```

### 5.4 SimPO (Simple Preference Optimization)

**核心简化**：去掉 Reference model，直接用回答的**平均 log probability** 作为隐式奖励。

```python
# SimPO: 不需要 reference model
reward = (1/|y|) * sum(log π_θ(y_t | x, y_{<t}))  # 平均 token log-prob
L_SimPO = -log σ(β · (reward_w - reward_l) - γ)  # γ 是 margin
```

**优势**：只需 1 个模型在 GPU 上 → 进一步降低显存。
**劣势**：没有 reference 约束，可能偏移更远。

### 5.5 GRPO (Group Relative Policy Optimization)

**DeepSeek-R1 使用的方法**，是 PPO 的简化版本：

```
GRPO 核心改进：
1. 去掉 Value 网络 → 3 个模型变 3 个（Policy + Ref + Reward）
   或 2 个（Policy + Ref，用 rule-based reward）
2. 不需要 per-token advantage → 用 group-level reward

流程：
  对每个 prompt，用 policy 生成 G 个回答 {y_1, ..., y_G}
  计算每个回答的 reward r_i
  将 reward 在 group 内归一化：ā_i = (r_i - mean(r)) / std(r)
  用归一化后的 ā_i 作为 advantage，做 PPO-style 更新
```

```python
# GRPO 伪代码
for prompt in batch:
    # 生成 G 个回答
    responses = [policy.generate(prompt) for _ in range(G)]
    rewards = [reward_fn(prompt, r) for r in responses]
    
    # Group-level normalization
    mean_r = np.mean(rewards)
    std_r = np.std(rewards)
    advantages = [(r - mean_r) / (std_r + 1e-8) for r in rewards]
    
    # PPO clipped update with group advantages
    for resp, adv in zip(responses, advantages):
        ratio = policy.log_prob(resp) - old_policy.log_prob(resp)
        loss = -min(ratio * adv, clip(ratio, 1-eps, 1+eps) * adv)
```

**关键创新**：用 **group 内的相对排名** 替代 value function 的 advantage 估计 → 更简单、更稳定。

### 5.6 方法对比总览

| 方法 | 需要 RM? | 在线采样? | 模型数量 | 数据格式 | 训练复杂度 | 代表作 |
|------|---------|----------|---------|---------|-----------|--------|
| **PPO** | ✅ | ✅ | 4 | pairwise | 高 | InstructGPT |
| **DPO** | ❌ | ❌ | 2 | pairwise | **低** | Zephyr |
| **ORPO** | ❌ | ❌ | **1** | pairwise | 很低 | — |
| **KTO** | ❌ | ❌ | 2 | binary | 低 | — |
| **IPO** | ❌ | ❌ | 2 | pairwise | 低 | — |
| **SimPO** | ❌ | ❌ | **1** | pairwise | 很低 | — |
| **GRPO** | ✅/规则 | ✅ | 2-3 | none (自采样) | 中 | **DeepSeek-R1** |

---

## VI. Engineering Practice (工程实践)

### 6.1 框架选择

| 框架 | 支持算法 | 特点 |
|------|---------|------|
| **TRL (Hugging Face)** | PPO, DPO, ORPO, KTO, SFT | 与 HF Transformers 深度集成，最成熟 |
| **OpenRLHF** | PPO, DPO, GRPO | Ray 分布式架构，支持 70B+ 模型 |
| **DeepSpeed-Chat** | PPO | 深度集成 DeepSpeed ZeRO，适合大规模 |
| **LLaMA-Factory** | SFT, DPO, PPO, ORPO | 中文友好，配置文件驱动 |

### 6.2 数据准备

**偏好数据格式（HF 标准）**：
```json
{
  "prompt": "什么是量子纠缠？",
  "chosen": "量子纠缠是量子力学中的一种现象，...(详细准确回答)",
  "rejected": "就是两个粒子连在一起（不准确简略回答）"
}
```

**数据质量检查**：
- 标注一致性：同一对数据多人标注的一致率应 > 70%
- 偏好清晰度：好/差回答的质量差距应显著
- 多样性：涵盖不同任务类型（对话、写作、代码、推理、安全拒绝）

### 6.3 超参数指南

| 参数 | PPO 典型值 | DPO 典型值 | 说明 |
|------|-----------|-----------|------|
| **β (KL 系数)** | 0.01 ~ 0.2 | 0.1 ~ 0.5 | 越大越保守，越小偏移越大 |
| **Learning Rate** | 1e-6 ~ 5e-6 | 1e-6 ~ 5e-6 | 比 SFT 再低一个数量级 |
| **Batch Size** | 64 ~ 512 | 32 ~ 128 | PPO 需要更大 batch 稳定训练 |
| **Epochs** | 1 (通常只跑 1 pass) | 1 ~ 3 | DPO 过多 epoch 容易过拟合 |
| **ε (clip range)** | 0.2 | — | PPO 专用 |
| **γ (discount)** | 1.0 | — | LLM RLHF 通常不做折扣 |
| **GAE λ** | 0.95 | — | PPO advantage estimation |

### 6.4 分布式训练

```
PPO 分布式训练（70B 模型 + A100 集群）：

方案一：模型分离部署
  Node 1-2: Policy (70B, ZeRO-3)
  Node 3:   Reference (70B, 推理模式)
  Node 4:   Reward + Value (推理 + ZeRO-3)
  
  通信开销：Policy 生成的回答需要发送给 Reward/Reference 评分
  → 使用 vLLM 做高效推理 + Ray 做跨节点通信

方案二：全模型统一部署（OpenRLHF 方式）
  每个 Node 同时加载 4 个模型的分片
  ZeRO-3 + offload 减少每节点显存
  → 通信少，但每节点显存要求高
```

**DPO 分布式**：与普通 fine-tuning 相同（只有 2 个模型），使用标准 DeepSpeed ZeRO 即可。

### 6.5 评估

| 评估方式 | 说明 | 工具 |
|---------|------|------|
| **MT-Bench** | GPT-4 自动评分 1-10 分，覆盖 8 个类别 | lm-evaluation-harness |
| **Arena (Chatbot Arena)** | 真人盲评两模型对战 (ELO rating) | LMSYS Arena |
| **AlpacaEval** | GPT-4 对模型回答 vs GPT-4 回答的胜率 | alpaca_eval |
| **人工评估** | 专业标注员按标准打分 | 自建 |
| **安全评估** | Red-teaming (人工/自动 jailbreak 测试) | Harmbench, StrongReject |

---

## VII. The Full Pipeline (完整训练流程)

### 7.1 端到端步骤

```
Step 1: 选择基座模型
  └─ 开源预训练模型：LLaMA 3 70B / Qwen 2.5 72B / Mistral
  
Step 2: SFT（监督微调）
  └─ 数据：10K~100K (instruction, response) 对
  └─ 训练：1-3 epoch, lr=2e-5, 8×A100 约 1-3 天
  └─ 输出：SFT 模型 → 作为后续的 π_ref

Step 3a: 如果用 PPO
  └─ 收集偏好数据 → 训练 Reward Model
  └─ PPO 训练：Policy + Ref + RM + Value，16×A100 约 3-7 天
  
Step 3b: 如果用 DPO
  └─ 收集偏好数据（或复用 RM 的数据）
  └─ DPO 训练：Policy + Ref，8×A100 约 1-2 天

Step 4: 评估
  └─ MT-Bench / Arena / 人工评估
  └─ 安全测试（Red-teaming）
  └─ 如果不满意 → 回到 Step 3 调参或换方法

Step 5: 部署
  └─ 量化（INT8/INT4） → vLLM/TRT-LLM 部署
  └─ 设置 system prompt、safety filter
  └─ 持续监控 + 收集反馈 → Iterative 更新
```

### 7.2 真实案例

**InstructGPT (OpenAI, 2022)**：
- 基座：GPT-3 175B
- SFT：13K 标注数据
- RM：33K comparison 数据
- PPO 训练
- 结果：InstructGPT 1.3B 的用户偏好度超过 GPT-3 175B

**LLaMA 2 Chat (Meta, 2023)**：
- 基座：LLaMA 2 70B
- SFT：27.5K 标注数据
- RLHF：两轮 PPO（Rejection Sampling + PPO）
- 创新：Rejection Sampling = 从 policy 生成 K 个回答，RM 选最好的做 SFT

**DeepSeek-R1 (DeepSeek, 2025)**：
- 基座：DeepSeek-V3
- 方法：**GRPO**（不用 RM，用 rule-based reward）
- 创新：reward = 格式正确性 + 答案正确性（可验证的数学/代码任务）
- 结果：推理能力与 OpenAI o1 相当

---

## VIII. Interview FAQ (面试高频问题)

### Q1: 为什么不直接做更多 SFT 来替代 RLHF？

> SFT 和 RLHF 解决的是**不同层面**的问题。SFT 教模型「怎么回答」（格式、风格），RLHF 教模型「回答什么更好」（质量、安全性）。举个例子：SFT 能让模型学会用列表格式回答，但无法让模型学会「同样格式下哪个回答更准确、更深入」。此外，RLHF 能教模型「什么不该说」——这种否定信号是 SFT（纯正例学习）天然缺失的。

### Q2: DPO vs PPO 如何选择？

> **优先 DPO**——实现简单、训练稳定、显存需求低。在大多数场景下 DPO 与 PPO 效果接近。
> **考虑 PPO** 的场景：1) 偏好数据有限，需要在线探索补充；2) 任务需要 reward shaping（如代码正确性可以用编译器验证）；3) 训练预算充足且追求极致效果。
> **考虑 GRPO**：如果任务有可验证的 reward（数学、代码）→ GRPO 不需要 RM，更简洁。

### Q3: 什么是 Reward Hacking？

> 模型学会了利用奖励模型的漏洞来获得高分，而非真正提升回答质量。例如：RM 可能给长回答打高分 → policy 学会生成冗长但无意义的回答。缓解方法：KL 惩罚、RM ensemble、定期更新 RM。

### Q4: RLHF 为什么需要 KL 惩罚？

> 两个原因：1) **防止 reward hacking**——如果不限制 policy 的偏移范围，它会走到 RM 的盲区去骗分；2) **保持语言质量**——SFT 模型已经有不错的语言能力，RL 更新不应该破坏它。KL 惩罚就是说「你可以变好，但不能变得面目全非」。

### Q5: GRPO 与 PPO 的核心区别？

> 1) **去掉 Value 网络**：GRPO 不需要估计每个 token 的 value → 简化训练；2) **Group-level advantage**：对每个 prompt 生成一组回答，用组内 reward 的相对排名作为 advantage → 不依赖 value function 的准确性；3) **可以用 rule-based reward**：对数学/代码任务，reward = 答案正确性，不需要训练 RM → 进一步简化。

### Q6: RLHF 训练中最常见的坑？

> 1) **Reward 崩塌**：KL 系数太小 → reward 飙升但回答变差 → 增大 β
> 2) **训练不动**：lr 太小 or batch 太小 → PPO 的梯度估计方差太大 → 增大 batch、调 lr
> 3) **Value function 拟合差**：Value 网络学不好 → advantage 估计噪声大 → PPO 更新方向随机 → 增加 value function 的训练 epoch
> 4) **忽略 reference model**：reference 必须是**冻结的 SFT 模型**，不能随 policy 更新
> 5) **DPO 过拟合**：偏好数据太少或 epoch 太多 → loss 降到零但效果变差 → 控制 epoch ≤ 3

---

## 相关文章

- [34 - 从模型诞生到AI应用全链路认知](@/articles/ai/ai-34-从模型诞生到AI应用全链路认知.md)
- [14 - 分布式训练优化详解](@/articles/ai/ai-14-分布式训练优化详解.md)
- [Glossary: AI/ML Concepts](@/articles/00-glossary/glossary-08-ai-ml-concepts.md)
