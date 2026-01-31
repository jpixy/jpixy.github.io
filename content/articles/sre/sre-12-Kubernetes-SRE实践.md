+++
title = "12.Kubernetes SRE实践"
date = 2026-01-19
description = "K8s可靠性运维：资源管理、健康检查、故障排查、高可用部署、运维自动化"
[taxonomies]
tags = ["SRE", "Kubernetes", "云原生"]
+++

## K8s资源管理

### 资源请求与限制

```yaml
resources:
  requests:
    cpu: "100m"      # 0.1 CPU核心
    memory: "256Mi"  # 256 MiB内存
  limits:
    cpu: "500m"      # 0.5 CPU核心
    memory: "512Mi"  # 512 MiB内存
```

**Requests**：调度依据，保证能获得的资源
**Limits**：上限，超过会被限制或OOMKill

### 资源配置策略

| 场景 | Request | Limit | 说明 |
|------|---------|-------|------|
| 生产核心服务 | 较高 | 略高于Request | 保证资源，限制爆发 |
| 批处理作业 | 较低 | 较高 | 允许超卖，利用空闲资源 |
| 开发测试 | 较低 | 较低 | 节约资源 |

### QoS等级

根据资源配置自动划分：

| QoS | 条件 | 优先级 |
|-----|------|--------|
| Guaranteed | Request = Limit（全部容器） | 最高 |
| Burstable | 至少一个容器设置了Request | 中 |
| BestEffort | 未设置任何Request/Limit | 最低（先被驱逐） |

**建议**：生产服务至少配置为Burstable，核心服务配置为Guaranteed。

### LimitRange与ResourceQuota

**LimitRange**：限制单个Pod/容器的资源
```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
spec:
  limits:
    - type: Container
      default:
        cpu: "500m"
        memory: "512Mi"
      defaultRequest:
        cpu: "100m"
        memory: "128Mi"
      max:
        cpu: "2"
        memory: "2Gi"
```

**ResourceQuota**：限制Namespace总资源
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: namespace-quota
spec:
  hard:
    pods: "100"
    requests.cpu: "20"
    requests.memory: "40Gi"
    limits.cpu: "40"
    limits.memory: "80Gi"
```

---

## 健康检查

### 三种探针

**Liveness Probe**：存活探针
- 失败 → 重启容器
- 检测死锁、无响应

**Readiness Probe**：就绪探针
- 失败 → 从Service移除
- 检测服务是否准备好

**Startup Probe**：启动探针
- 启动期间不执行Liveness检查
- 适合启动慢的应用

### 探针配置

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30    # 启动后等待时间
  periodSeconds: 10          # 检查间隔
  timeoutSeconds: 5          # 超时时间
  failureThreshold: 3        # 失败次数阈值
  successThreshold: 1        # 成功次数阈值

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
```

### 健康检查最佳实践

**Liveness设计**：
- 检查进程是否能响应
- 不要检查依赖服务
- 避免复杂逻辑

**Readiness设计**：
- 可以检查依赖连接
- 预热完成后返回成功
- 配合优雅停机

**常见错误**：
- initialDelaySeconds太短 → 容器反复重启
- timeoutSeconds太短 → 高负载时误判
- Liveness检查依赖 → 依赖故障导致全部重启

---

## Pod生命周期

### Pod阶段

```
Pending → Running → Succeeded/Failed
              ↓
         (异常情况)
              ↓
          Unknown
```

### 优雅停机

```yaml
spec:
  terminationGracePeriodSeconds: 60  # 最长等待时间
  containers:
    - name: app
      lifecycle:
        preStop:
          exec:
            command: ["/bin/sh", "-c", "sleep 10"]
```

**停机流程**：
1. Pod标记为Terminating
2. 从Service Endpoint移除
3. 执行preStop Hook
4. 发送SIGTERM信号
5. 等待terminationGracePeriodSeconds
6. 发送SIGKILL强制终止

**应用侧处理**：
- 捕获SIGTERM信号
- 停止接收新请求
- 完成正在处理的请求
- 关闭连接、释放资源

---

## 故障排查

### Pod状态诊断

**Pending**：
```bash
# 查看事件
kubectl describe pod <pod-name>

# 常见原因
- 资源不足（CPU/内存/GPU）
- Node选择器不匹配
- PV未绑定
- 镜像拉取失败
```

**CrashLoopBackOff**：
```bash
# 查看日志
kubectl logs <pod-name> --previous

# 常见原因
- 应用启动失败
- 配置错误
- 依赖不可用
- OOMKilled
```

**ImagePullBackOff**：
```bash
# 检查镜像名和Tag
# 检查镜像仓库凭证
kubectl get secret
kubectl describe secret <secret-name>
```

### 网络排查

```bash
# 检查Service
kubectl get svc
kubectl describe svc <svc-name>

# 检查Endpoints
kubectl get endpoints <svc-name>

# Pod内部测试
kubectl exec -it <pod> -- curl http://service-name:port

# DNS检查
kubectl exec -it <pod> -- nslookup service-name
```

### 资源问题

```bash
# 查看资源使用
kubectl top pods
kubectl top nodes

# 查看OOM事件
kubectl describe pod <pod-name> | grep -A5 "Last State"

# 查看节点资源
kubectl describe node <node-name> | grep -A10 "Allocated resources"
```

---

## 高可用部署

### Pod反亲和

确保Pod分布在不同节点：

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: myapp
        topologyKey: kubernetes.io/hostname
```

### 跨可用区部署

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: myapp
          topologyKey: topology.kubernetes.io/zone
```

### Pod Disruption Budget

限制同时不可用的Pod数量：

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
spec:
  minAvailable: 2          # 至少保持2个可用
  # 或 maxUnavailable: 1   # 最多1个不可用
  selector:
    matchLabels:
      app: myapp
```

### 拓扑分布约束

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: myapp
```

---

## 自动扩缩容

### HPA（Horizontal Pod Autoscaler）

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 3
  maxReplicas: 100
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### 自定义指标扩容

```yaml
metrics:
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

### VPA（Vertical Pod Autoscaler）

自动调整资源请求：

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: myapp-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  updatePolicy:
    updateMode: "Auto"  # Off, Initial, Auto
```

---

## 监控与告警

### 关键指标

**Pod级别**：
- CPU/内存使用率
- 重启次数
- 容器状态

**Node级别**：
- CPU/内存/磁盘使用率
- Pod数量
- 网络流量

**集群级别**：
- API Server延迟
- etcd健康状态
- 调度器队列

### Prometheus监控

```yaml
# ServiceMonitor配置
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
    - port: metrics
      interval: 30s
```

### 告警规则示例

```yaml
groups:
  - name: kubernetes
    rules:
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pod {{ $labels.pod }} is crash looping"
          
      - alert: PodNotReady
        expr: kube_pod_status_ready{condition="false"} == 1
        for: 10m
        labels:
          severity: warning
```

---

## 运维自动化

### GitOps

```
Git仓库 → ArgoCD/Flux → Kubernetes集群
  (声明式配置)    (同步)      (实际状态)
```

**ArgoCD Application**：
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo
    targetRevision: HEAD
    path: manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Operator模式

用代码管理复杂应用：

```
CRD（自定义资源）→ Operator（控制器）→ 管理实际资源
```

例如：
- MySQL Operator：自动化MySQL集群管理
- Prometheus Operator：自动化监控配置

---

## 总结

| 维度 | 关键实践 |
|------|----------|
| 资源管理 | Request/Limit合理配置，QoS等级规划 |
| 健康检查 | 三种探针配合，参数合理设置 |
| 高可用 | 反亲和、跨AZ、PDB |
| 扩缩容 | HPA基于指标自动扩缩 |
| 监控 | 多层次指标，关键告警 |
| 自动化 | GitOps、Operator |

K8s SRE的核心：**让Kubernetes自动化地保证服务可靠性**，而不是手动运维容器。

---

## 相关文章

- [上一篇：分布式系统可靠性设计](/articles/sre/sre-11-分布式系统可靠性设计/)
- [下一篇：数据库可靠性工程](/articles/sre/sre-13-数据库可靠性工程/)
