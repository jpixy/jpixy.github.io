+++
title = "05.Raft算法详解"
date = 2026-01-20
description = "Raft共识算法：Leader选举、日志复制、安全性保证"
[taxonomies]
tags = ["分布式", "Raft", "共识"]
+++

## Raft概述

### 设计目标

**可理解性**：比Paxos更容易理解和实现。

**完整性**：提供完整的实用系统构建指南。

**正确性**：经过形式化证明。

### 核心分解

Raft将共识问题分解为三个相对独立的子问题：

1. **Leader选举**：选择一个节点作为Leader
2. **日志复制**：Leader复制日志到Follower
3. **安全性**：保证状态机安全

---

## 节点状态

### 三种角色

**Leader**：处理所有客户端请求，复制日志到Follower。同一时刻最多一个Leader。

**Follower**：被动响应Leader和Candidate的请求。

**Candidate**：选举期间的中间状态，尝试成为Leader。

### 任期（Term）

时间被划分为任期，每个任期从选举开始。

任期编号单调递增。

每个任期最多一个Leader。

任期用于检测过期信息，高任期的信息更权威。

### 状态转换

Follower超时未收到心跳 → Candidate

Candidate收到多数票 → Leader

Candidate发现更高任期Leader → Follower

Leader发现更高任期 → Follower

---

## Leader选举

### 选举触发

Follower在选举超时内未收到Leader心跳，发起选举。

超时时间随机化（如150-300ms），避免多个节点同时选举。

### 选举过程

1. Candidate增加当前任期
2. 投票给自己
3. 发送RequestVote给所有节点
4. 等待结果

### 投票规则

每个节点每个任期只投一票。

只投给日志至少和自己一样新的候选人。

**日志比较**：最后日志条目的任期更大者更新；任期相同则索引更大者更新。

### 选举结果

**获得多数票**：成为Leader，开始发送心跳。

**发现Leader**：收到更高任期Leader的消息，转为Follower。

**超时无结果**：增加任期，重新选举。

---

## 日志复制

### 日志结构

日志由条目组成，每个条目包含：

- 任期号
- 索引
- 命令

### 复制过程

1. Leader收到客户端命令
2. 追加到本地日志
3. 发送AppendEntries给所有Follower
4. 多数Follower确认后，提交该条目
5. 下次心跳通知Follower提交

### AppendEntries RPC

包含：Leader任期、Leader ID、prevLogIndex、prevLogTerm、entries[]、leaderCommit

Follower检查prevLogIndex处条目的任期是否匹配。

匹配则追加新条目，不匹配则拒绝。

### 一致性检查

Leader为每个Follower维护nextIndex。

AppendEntries失败时，Leader减小nextIndex重试。

最终找到日志匹配的点，从那里开始复制。

### 日志匹配属性

如果两个日志在同一索引有相同任期，则：

- 该条目相同
- 之前所有条目都相同

通过AppendEntries的一致性检查保证。

---

## 安全性

### 选举限制

Candidate的日志必须至少和多数派一样新才能赢得选举。

保证Leader拥有所有已提交的条目。

### 提交规则

Leader只能提交当前任期的条目。

之前任期的条目通过复制当前任期条目间接提交。

避免已提交条目被覆盖的边角情况。

### 安全性证明

Leader Completeness：如果某条目在某任期被提交，则后续所有任期的Leader都包含该条目。

State Machine Safety：如果某节点应用了某索引的条目，其他节点不会在该索引应用不同条目。

---

## 成员变更

### 问题

直接切换成员配置可能导致两个Leader。

旧配置和新配置的多数派可能不相交。

### 单节点变更

每次只增加或减少一个节点。

单节点变更时，旧新配置的多数派必有交集。

安全且简单，推荐使用。

### 联合共识

允许任意变更，通过过渡配置。

先提交(C-old, C-new)联合配置，再提交C-new。

过渡期间需要新旧配置都达成多数。

---

## 日志压缩

### 问题

日志无限增长，重启恢复慢。

### 快照

将状态机状态保存为快照。

快照包含：最后包含的索引和任期、状态机状态。

丢弃快照点之前的日志。

### 快照传输

Leader发送InstallSnapshot给落后太多的Follower。

比一条条复制日志更高效。

---

## 客户端交互

### 幂等性

客户端重试可能导致命令重复执行。

为每个命令分配唯一ID，服务端去重。

### 只读优化

只读请求可以不写日志。

但需要确保读到最新数据：

- 确认自己还是Leader（心跳多数确认）
- 等待之前的日志都已提交

linearizable read需要额外保证。

---

## 生产实现

### etcd

Kubernetes使用的分布式KV存储。

基于Raft实现高可用。

### Consul

服务发现和配置管理。

使用Raft保证一致性。

### TiKV

分布式事务KV存储。

使用Multi-Raft，每个Region一个Raft组。

---

## 总结

| 概念 | 要点 |
|------|------|
| 角色 | Leader、Follower、Candidate |
| 任期 | 逻辑时钟，检测过期 |
| 选举 | 随机超时，多数票 |
| 日志复制 | AppendEntries，一致性检查 |
| 安全性 | 选举限制，提交规则 |
| 成员变更 | 单节点变更最简单 |

Raft是工程中最常用的共识算法。理解其设计可以帮助正确使用基于Raft的系统，以及调试分布式问题。
