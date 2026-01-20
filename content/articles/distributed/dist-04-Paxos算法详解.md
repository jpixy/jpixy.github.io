+++
title = "04.Paxos算法详解"
date = 2026-01-20
description = "Paxos共识算法：基本Paxos、Multi-Paxos、实现挑战"
[taxonomies]
tags = ["分布式", "Paxos", "共识"]
+++

## 共识问题

### 定义

多个节点就某个值达成一致。

**安全性**：
- 只有被提议的值才能被选定
- 只能选定一个值
- 只有值被选定后节点才能获知

**活性**：
- 如果有值被提议，最终会有值被选定
- 如果有值被选定，节点最终能获知

### 难点

异步环境下，无法区分节点故障和网络延迟。

FLP不可能定理：完全异步系统中，即使只有一个节点可能故障，也不存在确定性共识算法。

实践中通过随机化或部分同步假设规避。

---

## 基本Paxos

### 角色

**Proposer**：提议者，发起提案。

**Acceptor**：接受者，投票决定是否接受提案。

**Learner**：学习者，获知选定的值。

一个节点可以同时扮演多个角色。

### 提案编号

每个提案有唯一编号，用于区分不同提案。

编号必须全局唯一且可比较。

通常使用(轮次, 节点ID)组合。

### 两阶段协议

**Phase 1：准备阶段**

1a. Proposer选择提案编号n，发送Prepare(n)给多数Acceptor

1b. Acceptor收到Prepare(n)：
- 如果n大于之前响应的任何Prepare，承诺不再接受编号小于n的提案
- 返回之前接受的最高编号提案（如果有）

**Phase 2：接受阶段**

2a. Proposer收到多数Acceptor的响应：
- 如果响应中有已接受的提案，使用最高编号提案的值
- 否则可以使用自己的值
- 发送Accept(n, value)给多数Acceptor

2b. Acceptor收到Accept(n, value)：
- 如果没有承诺过更高编号，接受提案
- 返回确认

### 选定

当多数Acceptor接受同一提案时，该值被选定。

### 正确性

**安全性**：通过编号机制和多数派保证。两个多数派必有交集，确保不会选定不同值。

**活性问题**：多个Proposer可能活锁（不断用更高编号打断对方）。

---

## Paxos示例

### 正常流程

1. Proposer P1发送Prepare(1)
2. 多数Acceptor返回Promise(1, null)
3. P1发送Accept(1, "value A")
4. 多数Acceptor接受，返回Accepted(1)
5. 值"value A"被选定

### 竞争场景

1. P1发送Prepare(1)，收到多数Promise
2. P2发送Prepare(2)，收到多数Promise（包含Prepare(1)的信息）
3. P1发送Accept(1, "A")，被拒绝（Acceptor已承诺不接受<2的提案）
4. P2发送Accept(2, "B")（或之前的值），被接受

### 值继承

如果Acceptor已接受过值，后续Proposer必须继承该值。

保证一旦值被选定，后续提案只能选定相同值。

---

## Multi-Paxos

### 基本Paxos的问题

每个共识都需要两阶段，延迟高。

没有Leader，多个Proposer竞争效率低。

### Multi-Paxos优化

选举一个Leader，所有提案通过Leader提交。

Leader的Phase 1只需执行一次，后续只需Phase 2。

显著减少延迟和消息数量。

### 日志复制

为每个日志槽位运行Paxos实例。

Leader连续提交日志条目。

类似于Raft的日志复制，但Raft做了更多简化。

---

## 实现挑战

### 持久化

Acceptor承诺和接受的提案必须持久化。

崩溃恢复后需要保持一致性。

### 成员变更

节点加入或离开，多数派定义改变。

需要特殊协议处理，避免出现两个不相交的多数派。

### 活锁

多个Proposer竞争可能导致活锁。

解决：随机退避，或选举Leader。

### 性能

基本Paxos：2轮消息延迟，4f+1消息（f个故障容忍）

Multi-Paxos：稳态下1轮消息延迟

---

## Paxos变种

### Fast Paxos

正常情况下一轮消息完成共识。

需要更大的法定人数。

冲突时退回到经典Paxos。

### Cheap Paxos

使用少量活跃节点+备用节点。

故障时激活备用节点。

适合成本敏感场景。

### Flexible Paxos

放松多数派约束，Phase 1和Phase 2可以使用不同法定人数。

只要求Phase 1法定人数和Phase 2法定人数有交集。

### EPaxos

无Leader的优化Paxos。

并行提交非冲突命令。

更好的负载均衡和延迟。

---

## Paxos与Raft

### 相似点

都是解决共识问题的算法。

都能容忍少数节点故障。

都保证安全性。

### Raft的简化

强调可理解性。

明确的Leader选举。

日志连续，不允许空洞。

成员变更有清晰的协议。

### 选择

Raft更易理解和实现。

Paxos更灵活，适合特殊需求。

生产系统多用Raft或类Raft（etcd、Consul）。

---

## 总结

| 概念 | 要点 |
|------|------|
| 共识 | 多节点就值达成一致 |
| Phase 1 | Prepare，获取承诺 |
| Phase 2 | Accept，提交值 |
| 多数派 | 保证安全性 |
| Multi-Paxos | Leader优化，减少延迟 |

Paxos是分布式共识的奠基性算法。理解其原理对于理解所有共识算法都有帮助，尽管实践中通常使用更易理解的Raft。
