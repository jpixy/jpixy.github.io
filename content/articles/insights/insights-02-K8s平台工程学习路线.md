+++
title = "02.Kubernetes平台工程与云原生应用管理学习路线"
slug = "insights-Kubernetes平台工程与云原生应用管理学习路线"
+++

# Kubernetes 平台工程与云原生应用管理学习路线

> 本文系统梳理构建企业级 Kubernetes 应用平台所需的核心知识体系，涵盖 API 机制、控制器开发、多集群管理、分布式系统原理及可观测性等关键领域。

---

## 一、Kubernetes API 机制与语义

### 1.1 Server-Side Apply (SSA)

**关键词**: `Server-Side Apply`, `SSA`, `Field Management`, `Managed Fields`, `Apply Configuration`, `Conflict Detection`

| 概念 | 说明 |
| :--- | :--- |
| **定义** | 服务器端应用，Kubernetes 1.18+ 的声明式资源管理方式，由 API Server 负责字段所有权管理 |
| **核心机制** | 通过 `managedFields` 追踪每个字段的所有者（manager），解决多控制器/用户修改同一资源的冲突问题 |
| **对比 SMP** | Strategic Merge Patch (SMP) 是客户端合并，无法感知字段所有权；SSA 支持冲突检测和强制覆盖 |
| **最佳实践** | 控制器应使用 SSA 而非 Update/Patch，设置唯一的 `fieldManager` 标识 |

**深入理解**：SSA 解决了传统 `kubectl apply` 的"最后写入者胜出"问题。每个控制器声明自己管理的字段，当发生冲突时 API Server 可以拒绝或强制覆盖。这是实现多控制器协作的基础。

### 1.2 Strategic Merge Patch (SMP)

**关键词**: `Strategic Merge Patch`, `JSON Merge Patch`, `Patch Strategy`, `patchStrategy`, `patchMergeKey`

| 类型 | 适用场景 | 特点 |
| :--- | :--- | :--- |
| **JSON Patch** | 精确操作 | 使用 JSON Pointer 指定操作路径 |
| **JSON Merge Patch** | 简单替换 | 整个字段替换，数组完全覆盖 |
| **Strategic Merge Patch** | K8s 原生 | 根据 schema 中的 `patchStrategy` 智能合并数组 |

### 1.3 Server-Side Dry Run

**关键词**: `Dry Run`, `dryRun=All`, `Validation`, `Admission Dry Run`

- 在不实际持久化的情况下验证请求是否合法
- 支持 `dryRun=All` 参数，经过完整的 Admission 链
- 用于 CI/CD 预验证、GitOps diff 展示

### 1.4 Watch / Informer / Lister

**关键词**: `Watch`, `Informer`, `SharedInformer`, `Lister`, `ResourceVersion`, `Reflector`, `DeltaFIFO`, `Indexer`, `Resync`

```
┌─────────────┐    Watch     ┌─────────────┐
│  API Server │ ───────────► │  Reflector  │
└─────────────┘              └──────┬──────┘
                                    │
                                    ▼
                            ┌─────────────┐
                            │  DeltaFIFO  │
                            └──────┬──────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              ┌─────────┐   ┌───────────┐   ┌──────────┐
              │ Indexer │   │ Event     │   │ Resync   │
              │ (Cache) │   │ Handler   │   │ (定期)   │
              └─────────┘   └───────────┘   └──────────┘
                    │
                    ▼
              ┌─────────┐
              │ Lister  │  ← 从本地缓存读取，不访问 API Server
              └─────────┘
```

| 组件 | 职责 |
| :--- | :--- |
| **Watch** | 与 API Server 建立长连接，接收增量事件流 |
| **Reflector** | 维护 Watch 连接，处理断连重连和 ResourceVersion |
| **DeltaFIFO** | 事件队列，保证事件顺序和去重 |
| **Indexer** | 本地缓存 + 索引，支持按 namespace、label 等快速查询 |
| **Lister** | 从 Indexer 读取数据，避免频繁访问 API Server |
| **SharedInformer** | 多个控制器共享同一个 Informer，减少 API Server 压力 |

**关键参数**：
- `ResourceVersion`：乐观并发控制，Watch 从指定版本开始
- `Resync Period`：定期触发全量同步，弥补事件丢失

### 1.5 Rate-Limited Work Queue

**关键词**: `Workqueue`, `RateLimiting`, `Exponential Backoff`, `ItemExponentialFailure`, `BucketRateLimiter`, `MaxOfRateLimiter`

| 队列类型 | 说明 |
| :--- | :--- |
| **FIFO Queue** | 基础队列，去重 |
| **Delaying Queue** | 支持延迟入队 |
| **RateLimiting Queue** | 支持限速和退避重试 |

**限速器类型**：
- `BucketRateLimiter`：令牌桶，控制整体速率
- `ItemExponentialFailure`：指数退避，单个 key 失败后延迟增长
- `MaxOfRateLimiter`：组合多个限速器，取最大延迟

### 1.6 Finalizer（终结器）

**关键词**: `Finalizer`, `DeletionTimestamp`, `Foreground Deletion`, `Background Deletion`, `Orphan`, `Graceful Deletion`

**核心机制**：
1. 资源被删除时，如果有 Finalizer，只设置 `DeletionTimestamp`，不真正删除
2. 控制器观察到 `DeletionTimestamp` 后执行清理逻辑
3. 清理完成后移除 Finalizer
4. 所有 Finalizer 移除后，资源才被真正删除

**典型用途**：
- 删除 PV 前确保数据已备份
- 删除 Namespace 前清理所有子资源
- 外部资源（云资源、数据库）的级联删除

### 1.7 Owner Reference（所有者引用）

**关键词**: `OwnerReference`, `Controller Reference`, `Garbage Collection`, `Cascade Delete`, `BlockOwnerDeletion`

| 字段 | 说明 |
| :--- | :--- |
| `controller` | 是否是控制器所有者（只能有一个） |
| `blockOwnerDeletion` | 是否阻止所有者删除直到自己被删除 |

**垃圾回收策略**：
- **Foreground**：先删子资源，再删父资源
- **Background**：先删父资源，后台异步删子资源
- **Orphan**：只删父资源，子资源变成孤儿

### 1.8 Leader Election（领导者选举）

**关键词**: `Leader Election`, `Lease`, `Endpoints`, `ConfigMap`, `LeaseDuration`, `RenewDeadline`, `RetryPeriod`

| 参数 | 说明 | 典型值 |
| :--- | :--- | :--- |
| `LeaseDuration` | 锁的有效期 | 15s |
| `RenewDeadline` | Leader 续约超时 | 10s |
| `RetryPeriod` | 非 Leader 尝试获取锁的间隔 | 2s |

**锁资源选择**：
- **Lease**（推荐）：轻量，1.14+ 专用资源
- **ConfigMap/Endpoints**：旧方案，兼容性好但有副作用

### 1.9 API Priority and Fairness (APF)

**关键词**: `API Priority and Fairness`, `APF`, `FlowSchema`, `PriorityLevelConfiguration`, `Request Queue`, `Fair Queuing`, `Shuffle Sharding`

**解决的问题**：防止某类请求（如 List 全量）耗尽 API Server 资源，影响其他请求

| 组件 | 说明 |
| :--- | :--- |
| **FlowSchema** | 将请求分类（按 user、namespace、verb 等） |
| **PriorityLevelConfiguration** | 定义优先级和并发限制 |
| **Shuffle Sharding** | 随机分配队列，隔离故障域 |
| **Fair Queuing** | 公平调度，防止饥饿 |

**内置优先级**（从高到低）：
1. `system`：system:masters 等
2. `leader-election`：控制器选举
3. `workload-high`：重要工作负载
4. `workload-low`：普通工作负载
5. `global-default`：默认

---

## 二、Go 语言控制器与 Operator 开发

### 2.1 client-go 核心组件

**关键词**: `client-go`, `ClientSet`, `DynamicClient`, `RESTClient`, `DiscoveryClient`, `Scheme`, `RESTMapper`

| 客户端类型 | 适用场景 |
| :--- | :--- |
| **ClientSet** | 强类型，内置资源 |
| **DynamicClient** | 动态类型，任意资源 |
| **RESTClient** | 底层 REST 调用 |
| **DiscoveryClient** | API 发现 |

### 2.2 controller-runtime 框架

**关键词**: `controller-runtime`, `Manager`, `Controller`, `Reconciler`, `Builder`, `Predicate`, `Source`, `EventHandler`

```
┌─────────────────────────────────────────────────────────┐
│                       Manager                            │
├─────────────┬─────────────┬─────────────┬───────────────┤
│ Controller  │ Controller  │  Webhook    │  Health/Ready │
│     A       │     B       │  Server     │    Probes     │
└──────┬──────┴──────┬──────┴─────────────┴───────────────┘
       │             │
       ▼             ▼
  ┌─────────┐   ┌─────────┐
  │Reconciler│   │Reconciler│  ← 用户实现的业务逻辑
  └─────────┘   └─────────┘
```

**核心抽象**：
- **Manager**：管理所有控制器的生命周期、共享缓存、领导者选举
- **Controller**：监听事件，将 key 入队
- **Reconciler**：用户实现的协调逻辑，接收 `Request{Namespace, Name}`
- **Predicate**：过滤事件，减少不必要的协调
- **EventHandler**：将事件转换为 Reconcile 请求

### 2.3 Reconcile 模式

**关键词**: `Reconcile Loop`, `Level-Triggered`, `Edge-Triggered`, `Desired State`, `Current State`, `Drift Detection`

**核心原则**：
```
Reconcile = 比较 (期望状态, 当前状态) → 执行动作 → 趋向一致
```

| 模式 | 说明 |
| :--- | :--- |
| **Level-Triggered** | 基于当前状态，无论如何触发都收敛到期望状态（推荐） |
| **Edge-Triggered** | 基于事件，依赖事件顺序 |

**Reconcile 返回值**：
- `Result{}, nil`：成功，不再重试
- `Result{Requeue: true}, nil`：立即重新入队
- `Result{RequeueAfter: time}, nil`：延迟后重新入队
- `Result{}, err`：失败，使用限速器重试

### 2.4 Backoff 与 Retry

**关键词**: `Exponential Backoff`, `Jitter`, `MaxRetries`, `Retry Budget`, `Circuit Breaker`

| 策略 | 公式 | 说明 |
| :--- | :--- | :--- |
| **固定间隔** | `delay = constant` | 简单但不优雅 |
| **线性退避** | `delay = attempt * base` | 线性增长 |
| **指数退避** | `delay = base * 2^attempt` | 指数增长 |
| **带抖动** | `delay = random(0, base * 2^attempt)` | 避免惊群效应 |

**client-go 默认退避**：
- 初始: 5ms
- 最大: 1000s
- 因子: 2.0

### 2.5 幂等性设计

**关键词**: `Idempotency`, `Idempotent Reconcile`, `Generation`, `ObservedGeneration`, `ResourceVersion`

**确保幂等的技巧**：
1. 使用 `GenerateName` 而非固定 Name 创建资源时，先查询是否存在
2. 使用 `OwnerReference` 让 GC 自动清理，避免重复创建
3. 使用 `Generation/ObservedGeneration` 跳过已处理的版本
4. 更新前比较 `ResourceVersion`，处理乐观锁冲突
5. 外部操作使用幂等 API（如 S3 PutObject）

### 2.6 分区/分片控制器

**关键词**: `Sharding`, `Partitioning`, `Consistent Hashing`, `Hash Ring`, `Leader Per Shard`, `Lease-based Sharding`

**分片策略**：

| 策略 | 说明 | 适用场景 |
| :--- | :--- | :--- |
| **Namespace 分片** | 按 namespace 哈希分配 | 简单，但不均匀 |
| **一致性哈希** | 按资源 key 哈希到环上 | 均匀，扩缩容影响小 |
| **Lease 分片** | 每个分片一个 Lease，竞争获取 | 动态分配，HA 友好 |

**实现要点**：
- 每个实例只 Watch 自己负责的分片
- 使用 Label Selector 或 Field Selector 过滤
- 考虑分片再平衡时的短暂重复处理

### 2.7 高可用与故障转移

**关键词**: `High Availability`, `HA`, `Active-Passive`, `Active-Active`, `Failover`, `Split Brain`, `Fencing`

| 模式 | 说明 | 复杂度 |
| :--- | :--- | :--- |
| **Active-Passive** | 一个 Leader，其余 Standby | 低 |
| **Active-Active (分片)** | 每个实例处理不同分片 | 中 |
| **Active-Active (全量)** | 所有实例都处理，幂等保证 | 高 |

**故障检测与转移**：
- Lease 超时触发重新选举
- 健康检查失败触发 Pod 重启
- 使用 PodDisruptionBudget 保证滚动更新时可用性

---

## 三、CRD 与 Webhooks

### 3.1 CRD 版本管理

**关键词**: `CRD Versioning`, `Storage Version`, `Served Version`, `Deprecated Version`, `API Lifecycle`

| 阶段 | 说明 |
| :--- | :--- |
| `v1alpha1` | 实验性，可能随时删除 |
| `v1beta1` | 功能基本稳定，API 可能变化 |
| `v1` | 稳定版，长期支持 |

**多版本共存**：
```yaml
versions:
  - name: v1
    served: true
    storage: true  # 只能有一个 storage version
  - name: v1beta1
    served: true
    storage: false
    deprecated: true
```

### 3.2 Conversion Webhook

**关键词**: `Conversion Webhook`, `Hub Version`, `Spoke Version`, `ConversionReview`, `Lossless Conversion`

**Hub-and-Spoke 模式**：
- 选择一个版本作为 Hub（通常是最新版）
- 所有版本转换都通过 Hub 中转
- `v1beta1 → Hub → v1`

**转换要求**：
- 必须是无损的（Lossless）
- 使用 Annotation 保存无法表示的字段

### 3.3 Validating Admission Webhook

**关键词**: `Validating Webhook`, `AdmissionReview`, `AdmissionResponse`, `Allowed`, `Denied`, `Warnings`

**典型用途**：
- 校验资源配置的合法性
- 强制执行组织策略
- 检查外部依赖是否满足

**最佳实践**：
- 设置合理的 `failurePolicy`（Fail/Ignore）
- 使用 `namespaceSelector` 排除系统命名空间
- 返回清晰的错误信息

### 3.4 Mutating Admission Webhook

**关键词**: `Mutating Webhook`, `JSON Patch`, `Sidecar Injection`, `Default Values`, `Label Injection`

**典型用途**：
- 注入 Sidecar 容器（如 Istio）
- 设置默认值
- 添加标准 Label/Annotation

**执行顺序**：Mutating → Validating → Persist

### 3.5 策略框架

**关键词**: `Policy Framework`, `Kyverno`, `OPA Gatekeeper`, `CEL Validation`, `ValidatingAdmissionPolicy`

| 框架 | 特点 |
| :--- | :--- |
| **OPA/Gatekeeper** | Rego 语言，表达力强，学习曲线陡 |
| **Kyverno** | YAML 原生，简单直观 |
| **CEL (K8s 原生)** | 1.25+ 内置，无需外部组件 |

**ValidatingAdmissionPolicy (KEP-3488)**：
- K8s 1.26+ 原生支持
- 使用 CEL 表达式
- 无需 Webhook，性能更好

---

## 四、Pod 与运行时语义

### 4.1 容器类型

**关键词**: `Init Container`, `Sidecar Container`, `Ephemeral Container`, `App Container`, `Native Sidecar`

| 类型 | 执行时机 | 典型用途 |
| :--- | :--- | :--- |
| **Init Container** | 主容器前，顺序执行 | 初始化配置、等待依赖 |
| **Sidecar Container** | 与主容器并行（1.28+原生支持） | 日志收集、代理 |
| **App Container** | 主业务容器 | 业务逻辑 |
| **Ephemeral Container** | 运行时注入 | 调试 |

**Native Sidecar (KEP-753)**：
- K8s 1.28+ 支持 `restartPolicy: Always` 的 Init Container
- 先于主容器启动，后于主容器终止
- 解决了传统 Sidecar 的启动/终止顺序问题

### 4.2 探针详解

**关键词**: `Probe`, `Liveness Probe`, `Readiness Probe`, `Startup Probe`, `HTTP Probe`, `TCP Probe`, `Exec Probe`, `gRPC Probe`

| 探针 | 失败后果 | 典型场景 |
| :--- | :--- | :--- |
| **Startup** | 等待，超时则重启 | 慢启动应用 |
| **Liveness** | 重启容器 | 死锁检测 |
| **Readiness** | 从 Service 摘除 | 负载控制 |

**关键参数**：
- `initialDelaySeconds`：首次探测延迟
- `periodSeconds`：探测间隔
- `timeoutSeconds`：超时时间
- `failureThreshold`：连续失败次数
- `successThreshold`：连续成功次数

### 4.3 生命周期钩子

**关键词**: `Lifecycle Hooks`, `PostStart`, `PreStop`, `SIGTERM`, `Graceful Shutdown`

```
Pod 创建                                         Pod 终止
    │                                                │
    ▼                                                ▼
┌─────────┐                                    ┌───────────┐
│PostStart│                                    │ PreStop   │
│  Hook   │                                    │   Hook    │
└────┬────┘                                    └─────┬─────┘
     │                                               │
     ▼                                               ▼
┌─────────┐                                    ┌───────────┐
│Container│         ◄─── 运行中 ───►           │  SIGTERM  │
│  Run    │                                    │   发送    │
└─────────┘                                    └─────┬─────┘
                                                     │
                                               terminationGracePeriodSeconds
                                                     │
                                                     ▼
                                               ┌───────────┐
                                               │  SIGKILL  │
                                               └───────────┘
```

### 4.4 终止行为

**关键词**: `Termination`, `terminationGracePeriodSeconds`, `SIGTERM`, `SIGKILL`, `Preemption`

**优雅终止流程**：
1. Pod 被标记为 Terminating
2. 从 Service Endpoints 移除
3. 执行 PreStop Hook
4. 发送 SIGTERM
5. 等待 `terminationGracePeriodSeconds`（默认 30s）
6. 发送 SIGKILL

### 4.5 PodDisruptionBudget (PDB)

**关键词**: `PDB`, `PodDisruptionBudget`, `minAvailable`, `maxUnavailable`, `Voluntary Disruption`, `Involuntary Disruption`

| 参数 | 说明 |
| :--- | :--- |
| `minAvailable` | 最少可用 Pod 数（数字或百分比） |
| `maxUnavailable` | 最多不可用 Pod 数 |

**适用场景**：自愿中断（Voluntary Disruption）
- 节点维护/升级
- 集群自动缩容
- 滚动更新

### 4.6 QoS 等级

**关键词**: `QoS Class`, `Guaranteed`, `Burstable`, `BestEffort`, `OOM Score`, `Eviction`

| QoS 等级 | 条件 | OOM 优先级 |
| :--- | :--- | :--- |
| **Guaranteed** | 所有容器都设置相等的 requests 和 limits | 最低（最后被杀） |
| **Burstable** | 至少一个容器设置了 requests | 中 |
| **BestEffort** | 没有设置任何 requests/limits | 最高（最先被杀） |

### 4.7 ResourceQuota 与 LimitRange

**关键词**: `ResourceQuota`, `LimitRange`, `Namespace Quota`, `Default Limits`, `Min/Max Constraints`

| 资源 | 作用域 | 用途 |
| :--- | :--- | :--- |
| **ResourceQuota** | Namespace | 限制资源总量 |
| **LimitRange** | Namespace | 设置默认值和范围约束 |

### 4.8 拓扑分布与亲和性

**关键词**: `TopologySpreadConstraints`, `Pod Affinity`, `Pod Anti-Affinity`, `Node Affinity`, `Taints`, `Tolerations`, `topologyKey`

**TopologySpreadConstraints（推荐）**：
```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: my-app
```

| 参数 | 说明 |
| :--- | :--- |
| `maxSkew` | 拓扑域间 Pod 数最大差值 |
| `topologyKey` | 拓扑域标签（zone、node 等） |
| `whenUnsatisfiable` | 不满足时策略（DoNotSchedule/ScheduleAnyway） |

---

## 五、扩缩容系统

### 5.1 Horizontal Pod Autoscaler (HPA)

**关键词**: `HPA`, `Horizontal Pod Autoscaler`, `Resource Metrics`, `Custom Metrics`, `External Metrics`, `Scaling Policy`, `Behavior`

**指标类型**：

| 类型 | 来源 | 示例 |
| :--- | :--- | :--- |
| **Resource** | metrics-server | CPU、Memory |
| **Custom** | custom.metrics.k8s.io | requests_per_second |
| **External** | external.metrics.k8s.io | 队列长度、云监控指标 |

**扩缩容行为控制 (HPA v2)**：
```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300  # 缩容稳定窗口
    policies:
      - type: Percent
        value: 10
        periodSeconds: 60
  scaleUp:
    stabilizationWindowSeconds: 0
    policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### 5.2 Vertical Pod Autoscaler (VPA)

**关键词**: `VPA`, `Vertical Pod Autoscaler`, `Recommender`, `Updater`, `Admission Controller`, `UpdateMode`

| 组件 | 职责 |
| :--- | :--- |
| **Recommender** | 基于历史数据推荐资源配置 |
| **Updater** | 驱逐 Pod 以应用新配置 |
| **Admission Controller** | 注入推荐的资源配置 |

**UpdateMode**：
- `Off`：只推荐，不自动应用
- `Initial`：仅在 Pod 创建时应用
- `Auto`：自动驱逐并重建 Pod

### 5.3 Cluster Autoscaler

**关键词**: `Cluster Autoscaler`, `Node Group`, `Scale Up`, `Scale Down`, `Expander`, `Priority Expander`

**扩容触发**：Pod 处于 Pending 且原因是资源不足

**缩容条件**：
1. 节点利用率低于阈值（默认 50%）
2. 所有 Pod 可调度到其他节点
3. 没有 PDB 阻止
4. 没有 local storage
5. 没有不可驱逐的 Pod

### 5.4 多维扩缩容

**关键词**: `Multidimensional Autoscaling`, `KEDA`, `ScaledObject`, `ScaledJob`, `Autopilot`

**KEDA (Kubernetes Event-driven Autoscaling)**：
- 支持 50+ 种事件源（Kafka、RabbitMQ、Prometheus 等）
- 可缩容到 0
- 与 HPA 集成

### 5.5 基于 SLO 的扩缩容

**关键词**: `SLO-based Scaling`, `Error Budget`, `Latency Target`, `Predictive Scaling`, `Proactive Scaling`

**实现思路**：
1. 定义 SLO（如 P99 延迟 < 100ms）
2. 监控 SLI（实际延迟）
3. 当 Error Budget 消耗过快时触发扩容
4. 结合预测算法提前扩容

---

## 六、联合与多集群管理

### 6.1 多集群架构模式

**关键词**: `Multi-Cluster`, `Federation`, `Hub-Spoke`, `Mesh`, `Fleet Management`

| 模式 | 特点 | 适用场景 |
| :--- | :--- | :--- |
| **Hub-Spoke** | 中心管理集群 + 成员集群 | 集中管控 |
| **Mesh** | 对等互联 | 去中心化 |
| **Hierarchical** | 多层级管理 | 大规模组织 |

### 6.2 Placement & Propagation

**关键词**: `Placement`, `Propagation`, `Scheduling`, `Cluster Selector`, `Spread Policy`

**放置策略**：
- **ClusterSelector**：按标签选择目标集群
- **ClusterAffinity**：亲和性规则
- **SpreadPolicy**：跨集群分布策略

**传播策略**：
- **推送模式**：Hub 主动推送到成员集群
- **拉取模式**：成员集群从 Hub 拉取

### 6.3 Failover & Drift Detection

**关键词**: `Failover`, `Drift Detection`, `Remediation`, `Self-Healing`, `Reconciliation`

**故障转移**：
1. 检测集群/应用健康状态
2. 触发工作负载迁移
3. 更新流量路由

**漂移检测**：
- 定期比较期望状态与实际状态
- 检测人工修改或配置漂移
- 自动或手动修复

### 6.4 主流多集群方案

**关键词**: `Karmada`, `Clusternet`, `KubeAdmiral`, `Liqo`, `Skupper`, `Submariner`

| 项目 | 特点 |
| :--- | :--- |
| **Karmada** | CNCF 项目，兼容 K8s API |
| **Clusternet** | 轻量级，支持 Pull/Push |
| **KubeAdmiral** | 字节跳动开源，大规模验证 |
| **Liqo** | 虚拟节点方式，资源共享 |

---

## 七、分布式系统基础

### 7.1 CRDT 与最终一致性

**关键词**: `CRDT`, `Conflict-free Replicated Data Types`, `Eventual Consistency`, `Strong Consistency`, `CAP Theorem`

**CRDT 类型**：
- **G-Counter**：只增计数器
- **PN-Counter**：可增可减计数器
- **LWW-Register**：Last-Write-Wins 寄存器
- **OR-Set**：可观察删除集合

**应用场景**：
- 分布式缓存状态同步
- 多集群配置合并
- 离线优先应用

### 7.2 共识算法

**关键词**: `Raft`, `Paxos`, `Memberlist`, `Gossip`, `SWIM`, `Serf`

| 算法 | 特点 | 应用 |
| :--- | :--- | :--- |
| **Raft** | 强一致性，易理解 | etcd, Consul |
| **Paxos** | 强一致性，理论严谨 | Chubby |
| **Gossip** | 最终一致性，高可用 | Consul Serf, Cassandra |
| **SWIM** | 成员探测 + Gossip | HashiCorp memberlist |

### 7.3 etcd 深入

**关键词**: `etcd`, `MVCC`, `Revision`, `Compact`, `Defrag`, `Snapshot`, `Learner`, `Watch Progress`

| 操作 | 说明 |
| :--- | :--- |
| **Compaction** | 删除历史版本，释放空间 |
| **Defrag** | 回收碎片空间，需要停顿 |
| **Snapshot** | 全量备份，用于恢复 |

**关键参数**：
- `--quota-backend-bytes`：数据库大小限制（默认 2GB）
- `--auto-compaction-retention`：自动压缩保留时间
- `--snapshot-count`：触发快照的事务数

**运维要点**：
- 监控 `db_size` 和 `db_size_in_use`
- 定期检查 Leader 选举频率
- 关注慢查询和 Watch 数量

### 7.4 Kafka 深入

**关键词**: `Kafka`, `Partition`, `Consumer Group`, `Offset`, `Backpressure`, `Retention`, `Compaction`, `ISR`

| 概念 | 说明 |
| :--- | :--- |
| **ISR** | In-Sync Replicas，同步副本集 |
| **HW** | High Watermark，消费者可见的最大 offset |
| **LEO** | Log End Offset，分区最新 offset |

**背压处理**：
- `max.poll.records`：单次拉取记录数
- `max.poll.interval.ms`：最大处理间隔
- Consumer Pause/Resume

### 7.5 Redis 深入

**关键词**: `Redis`, `Cluster`, `Sentinel`, `Persistence`, `RDB`, `AOF`, `Eviction`, `Memory Fragmentation`

**集群模式**：

| 模式 | 特点 |
| :--- | :--- |
| **Standalone** | 单节点，简单 |
| **Sentinel** | 主从 + 自动故障转移 |
| **Cluster** | 分片 + 高可用 |

**持久化**：
- **RDB**：定时快照，恢复快
- **AOF**：追加日志，数据完整
- **混合模式**：RDB + 增量 AOF

---

## 八、可观测性与数据工程

### 8.1 Prometheus 深入

**关键词**: `Prometheus`, `PromQL`, `Cardinality`, `Recording Rules`, `Alerting Rules`, `Federation`, `Remote Write`, `Thanos`, `Cortex`, `Mimir`

**基数控制（Cardinality）**：
- 避免高基数标签（如 user_id、request_id）
- 使用 Recording Rules 预聚合
- 监控 `prometheus_tsdb_head_series`

**Recording Rules 最佳实践**：
```yaml
groups:
  - name: slo
    rules:
      - record: job:request_latency:p99_5m
        expr: histogram_quantile(0.99, sum(rate(request_latency_bucket[5m])) by (job, le))
```

**长期存储方案**：

| 方案 | 特点 |
| :--- | :--- |
| **Thanos** | 对象存储，全局查询 |
| **Cortex/Mimir** | 多租户，水平扩展 |
| **VictoriaMetrics** | 高压缩比，兼容 PromQL |

### 8.2 分布式追踪

**关键词**: `Tracing`, `OpenTelemetry`, `Jaeger`, `Zipkin`, `Span`, `Trace`, `Baggage`, `Context Propagation`, `Sampling`

**采样策略**：
- **Head-based**：入口决定是否采样
- **Tail-based**：完成后根据特征决定
- **Adaptive**：动态调整采样率

**OpenTelemetry 集成**：
- 统一 Traces、Metrics、Logs
- 自动 instrumentation
- Collector 管道处理

### 8.3 向量数据库应用

**关键词**: `Vector Database`, `Embedding`, `Similarity Search`, `ANN`, `HNSW`, `Pinecone`, `Weaviate`, `Milvus`, `Qdrant`

**运维诊断应用**：
- 日志语义搜索
- 异常模式匹配
- 相似故障检索
- 知识库问答

### 8.4 时序预测

**关键词**: `Time Series Forecasting`, `ARIMA`, `Prophet`, `LSTM`, `Transformer`, `Anomaly Detection`, `Trend Analysis`

| 方法 | 适用场景 |
| :--- | :--- |
| **ARIMA** | 平稳序列，短期预测 |
| **Prophet** | 有季节性的业务指标 |
| **LSTM/Transformer** | 复杂模式，长期依赖 |

**主动优化应用**：
- 预测性扩容
- 容量规划
- 成本优化
- 异常预警

---

## 九、平台工程最佳实践

### 9.1 应用生命周期管理

**关键词**: `Application Lifecycle`, `GitOps`, `ArgoCD`, `Flux`, `Progressive Delivery`, `Canary`, `Blue-Green`, `A/B Testing`

**发布策略**：

| 策略 | 风险 | 复杂度 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **Rolling Update** | 中 | 低 | 通用 |
| **Blue-Green** | 低 | 中 | 需要快速回滚 |
| **Canary** | 低 | 高 | 需要验证新版本 |
| **A/B Testing** | 低 | 高 | 功能实验 |

### 9.2 多租户控制平面

**关键词**: `Multi-tenancy`, `Namespace Isolation`, `Virtual Cluster`, `vCluster`, `Control Plane Isolation`, `Data Plane Isolation`

**隔离级别**：
1. **软多租户**：Namespace 隔离 + RBAC + ResourceQuota
2. **硬多租户**：独立控制平面 / Virtual Cluster
3. **完全隔离**：独立集群

### 9.3 安全与治理

**关键词**: `Security`, `Governance`, `Policy as Code`, `Admission Control`, `Network Policy`, `Pod Security Standards`, `Runtime Security`

**安全层次**：

| 层次 | 控制点 |
| :--- | :--- |
| **构建时** | 镜像扫描、SBOM |
| **部署时** | Admission Policy |
| **运行时** | Runtime Security (Falco) |
| **网络** | Network Policy, Service Mesh |

### 9.4 成本优化

**关键词**: `Cost Optimization`, `FinOps`, `Resource Right-sizing`, `Spot Instance`, `Reserved Instance`, `Kubecost`, `OpenCost`

**优化策略**：
1. **Right-sizing**：VPA 推荐 + 手动调整
2. **Spot/Preemptible**：无状态工作负载
3. **Bin Packing**：提高节点利用率
4. **Auto-scaling**：缩容到合理水平
5. **Multi-cloud Arbitrage**：跨云价格优化

### 9.5 开发者体验

**关键词**: `Developer Experience`, `DX`, `Platform Engineering`, `Internal Developer Platform`, `IDP`, `Self-Service`, `Golden Path`

**平台能力构建**：
1. **抽象复杂性**：应用模型（如 OAM）屏蔽 K8s 细节
2. **Self-Service**：开发者自助创建环境
3. **Golden Path**：提供最佳实践模板
4. **可观测性**：一键查看应用状态

---

## 十、业界新技术与趋势

### 10.1 平台工程工具链

**关键词**: `Backstage`, `Crossplane`, `Kratix`, `Score`, `Dapr`, `Radius`

| 工具 | 定位 |
| :--- | :--- |
| **Backstage** | 开发者门户 |
| **Crossplane** | 基础设施即代码，K8s 原生 |
| **Kratix** | 平台即产品框架 |
| **Dapr** | 分布式应用运行时 |
| **Radius** | 微软开源，应用图模型 |

### 10.2 Gateway API

**关键词**: `Gateway API`, `GatewayClass`, `HTTPRoute`, `GRPCRoute`, `TCPRoute`, `ReferenceGrant`

- Ingress 的继任者
- 更强的表达能力
- 支持多租户
- 与 Service Mesh 统一

### 10.3 Wasm 与 K8s

**关键词**: `WebAssembly`, `Wasm`, `WASI`, `Spin`, `WasmEdge`, `Fermyon`, `runwasi`

**应用场景**：
- 轻量级函数
- 边缘计算
- 插件系统
- Sidecar 替代

### 10.4 eBPF 在 K8s 中的应用

**关键词**: `eBPF`, `Cilium`, `Tetragon`, `Pixie`, `Hubble`, `Service Mesh without Sidecar`

| 项目 | 应用 |
| :--- | :--- |
| **Cilium** | CNI、Network Policy、Service Mesh |
| **Tetragon** | 运行时安全 |
| **Pixie** | 自动可观测性 |
| **Hubble** | 网络可视化 |

### 10.5 AI/ML 工作负载编排

**关键词**: `MLOps`, `KubeFlow`, `Ray`, `Volcano`, `Kueue`, `GPU Scheduling`, `Multi-Instance GPU`, `MIG`

**调度挑战**：
- GPU 资源调度
- 分布式训练
- 模型服务
- 批处理队列

**相关项目**：
- **Kueue**：作业队列管理
- **Volcano**：批处理调度器
- **Ray**：分布式计算框架

---

## 附录：关键词索引

### API 与控制器
`Server-Side Apply`, `SSA`, `Strategic Merge Patch`, `SMP`, `Dry Run`, `Watch`, `Informer`, `Lister`, `SharedInformer`, `Reflector`, `DeltaFIFO`, `Indexer`, `ResourceVersion`, `Workqueue`, `RateLimiting`, `Exponential Backoff`, `Finalizer`, `OwnerReference`, `Garbage Collection`, `Leader Election`, `Lease`, `API Priority and Fairness`, `APF`, `FlowSchema`

### 控制器开发
`client-go`, `controller-runtime`, `Reconciler`, `Manager`, `Predicate`, `Idempotency`, `Generation`, `ObservedGeneration`, `Sharding`, `Consistent Hashing`, `High Availability`, `Failover`

### CRD 与准入控制
`CRD`, `Versioning`, `Conversion Webhook`, `Validating Webhook`, `Mutating Webhook`, `CEL`, `ValidatingAdmissionPolicy`, `Kyverno`, `OPA Gatekeeper`

### Pod 语义
`Init Container`, `Sidecar Container`, `Native Sidecar`, `Ephemeral Container`, `Probe`, `Liveness`, `Readiness`, `Startup`, `Lifecycle Hooks`, `PreStop`, `PostStart`, `terminationGracePeriodSeconds`, `PDB`, `QoS`, `Guaranteed`, `Burstable`, `BestEffort`, `ResourceQuota`, `LimitRange`, `TopologySpreadConstraints`, `Affinity`, `Anti-Affinity`, `Taints`, `Tolerations`

### 扩缩容
`HPA`, `VPA`, `Cluster Autoscaler`, `KEDA`, `Custom Metrics`, `External Metrics`, `Predictive Scaling`, `SLO-based Scaling`

### 多集群
`Federation`, `Karmada`, `Clusternet`, `Placement`, `Propagation`, `Failover`, `Drift Detection`

### 分布式系统
`CRDT`, `Eventual Consistency`, `Raft`, `Gossip`, `Memberlist`, `etcd`, `Compaction`, `Kafka`, `Backpressure`, `Redis`, `Sentinel`, `Cluster`

### 可观测性
`Prometheus`, `PromQL`, `Cardinality`, `Recording Rules`, `Thanos`, `Cortex`, `Mimir`, `VictoriaMetrics`, `OpenTelemetry`, `Jaeger`, `Tracing`, `Sampling`, `Vector Database`, `Time Series Forecasting`

### 平台工程
`GitOps`, `ArgoCD`, `Flux`, `Progressive Delivery`, `Canary`, `Blue-Green`, `Multi-tenancy`, `vCluster`, `FinOps`, `Cost Optimization`, `Developer Experience`, `Platform Engineering`

### 新技术
`Backstage`, `Crossplane`, `Gateway API`, `WebAssembly`, `eBPF`, `Cilium`, `KubeFlow`, `Kueue`, `Volcano`

---

## 相关文章

- [上一篇：AI应用技术栈全景与实践指南](/articles/insights/insights-01-AI应用技术栈全景/)
- [下一篇：Staff级别面试项目选择与技术亮点分析](/articles/insights/insights-03-Staff面试项目分析/)
