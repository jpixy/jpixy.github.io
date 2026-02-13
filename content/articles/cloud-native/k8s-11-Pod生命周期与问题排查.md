+++
title = "Pod生命周期及Pending问题排查指南"
slug = "k8s-Pod生命周期及Pending问题排查指南"
weight = 13000
+++

# Kubernetes Pod 生命周期及 Pending 问题排查指南
## 一、Pod 生命周期详解
Pod 是 Kubernetes 的最小调度单元，其生命周期包含以下几个阶段：

1. **Pending（挂起）**：
    - Pod 已被 Kubernetes 系统接受，但有一个或多个容器尚未创建或运行
    - 此阶段包括调度和下载镜像的过程
2. **Running（运行中）**：
    - Pod 已经绑定到节点，所有容器已被创建
    - 至少有一个容器正在运行，或正在启动/重启
3. **Succeeded（成功）**：
    - Pod 中的所有容器已成功终止且不会重启
    - 常见于 Job/CronJob 类型的 Pod
4. **Failed（失败）**：
    - Pod 中至少有一个容器以非零状态终止
    - 或者容器因某种原因被系统终止
5. **Unknown（未知）**：
    - 通常是由于无法获取 Pod 状态导致的
    - 可能由于节点通信故障

## 二、Pod Pending 问题深度排查
### 1. 查看详细状态信息
```bash
kubectl describe pod <pod-name> -n <namespace>
```

重点关注 **Events** 部分的警告和错误信息

### 2. Pending 常见原因及解决方案
#### (1) 资源不足问题
**可能原因**：

+ 集群没有足够的 CPU/内存资源
+ 节点资源碎片化导致无法满足 Pod 请求
+ 资源配额(ResourceQuota)限制

**解决方案**：

```bash
# 检查节点资源情况
kubectl top nodes

# 检查 Pod 资源请求
kubectl get pod <pod-name> -o yaml | grep resources -A 5

# 检查资源配额
kubectl describe quota -n <namespace>

# 解决方法：
# 1. 增加节点或调整 Pod 资源请求
# 2. 清理不需要的 Pod 释放资源
# 3. 调整资源配额
```

#### (2) 镜像拉取问题
**可能原因**：

+ 镜像名称错误
+ 私有镜像仓库认证失败
+ 镜像仓库不可访问

**解决方案**：

```bash
# 查看镜像拉取错误
kubectl describe pod <pod-name> | grep -i image

# 手动测试镜像拉取
docker pull <image-name>

# 解决方法：
# 1. 检查镜像名称拼写
# 2. 创建正确的 Secret 用于私有仓库认证
kubectl create secret docker-registry my-secret \
  --docker-server=<registry> \
  --docker-username=<user> \
  --docker-password=<password>

# 3. 确保节点可以访问镜像仓库
```

#### (3) 调度问题
**可能原因**：

+ 节点选择器(nodeSelector)不匹配
+ 亲和性/反亲和性规则限制
+ 污点(Taint)和容忍(Toleration)不匹配
+ 节点标签缺失

**解决方案**：

```bash
# 检查调度失败原因
kubectl get events --field-selector involvedObject.name=<pod-name>

# 查看节点标签
kubectl get nodes --show-labels

# 查看 Pod 的调度约束
kubectl get pod <pod-name> -o yaml | grep -A 10 -E "nodeSelector|affinity|tolerations"

# 解决方法：
# 1. 调整 nodeSelector/affinity 规则
# 2. 添加适当的 tolerations
# 3. 为节点添加所需标签
kubectl label nodes <node-name> <label-key>=<label-value>
```

#### (4) 持久卷(PV)问题
**可能原因**：

+ 持久卷声明(PVC)无法绑定
+ StorageClass 配置问题
+ 动态供应失败

**解决方案**：

```bash
# 检查 PVC 状态
kubectl get pvc -n <namespace>

# 查看 PV 状态
kubectl get pv

# 查看 StorageClass
kubectl get storageclass

# 解决方法：
# 1. 确保有可用的 PV 或 StorageClass
# 2. 检查 PVC 和 PV 的 accessModes 匹配
# 3. 对于静态配置，检查容量和 selector 匹配
```

#### (5) 节点问题
**可能原因**：

+ 节点 NotReady
+ 节点资源压力(DiskPressure/MemoryPressure)
+ 节点已满(pod 数量达到上限)

**解决方案**：

```bash
# 检查节点状态
kubectl get nodes

# 查看节点详情
kubectl describe node <node-name>

# 解决方法：
# 1. 修复故障节点或添加新节点
# 2. 清理节点空间或增加资源
# 3. 调整 --max-pods 参数(默认为 110)
```

#### (6) 其他特殊原因
**可能原因**：

+ 命名空间处于 terminating 状态
+ 启用了 Pod 安全策略(PSP)且不满足
+ 网络插件未正常运行

**解决方案**：

```bash
# 检查命名空间状态
kubectl get ns <namespace>

# 检查 PSP 设置
kubectl get psp

# 检查网络插件状态
kubectl get pods -n kube-system | grep -E 'flannel|calico|cilium'

# 解决方法：
# 1. 修复卡住的命名空间
# 2. 调整 PSP 或使用合适的 ServiceAccount
# 3. 重启或重新配置网络插件
```

## 三、高级排查工具
### 1. 使用 -o wide 查看更详细的信息
```bash
kubectl get pods -o wide -n <namespace>
```

### 2. 检查调度器日志
```bash
# 查看调度器 Pod
kubectl get pods -n kube-system | grep scheduler

# 查看调度器日志
kubectl logs <scheduler-pod-name> -n kube-system
```

### 3. 使用集群状态检查工具
```bash
# 使用 kubectl cluster-info dump 导出集群状态
kubectl cluster-info dump > cluster-state.json

# 使用 kube-score 检查资源定义
kube-score score my-pod.yaml
```

## 四、预防 Pending 的最佳实践
1. **合理设置资源请求和限制**：

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "1Gi"
```

2. **使用优先级类(PriorityClass)**：

```yaml
priorityClassName: high-priority
```

3. **配置适当的 Pod 中断预算(PDB)**：

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: my-app
```

4. **定期维护集群**：
    - 监控节点健康状况
    - 及时升级集群版本
    - 清理未使用的资源
5. **使用 Pod 拓扑分布约束**：

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: kubernetes.io/hostname
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      app: my-app
```

通过系统性地排查这些潜在问题，可以有效地解决 Pod 处于 Pending 状态的问题，并提高 Kubernetes 集群的稳定性和可靠性。

---

## 相关文章

- [上一篇：K8S探针详解](@/articles/cloud-native/k8s-10-探针详解.md)
- [下一篇：kube-proxy详解](@/articles/cloud-native/k8s-12-kube-proxy详解.md)
