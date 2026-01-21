+++
title = "23.SRE笔试题-Kubernetes速查"
date = 2026-01-21
description = "SRE面试Kubernetes常见题目速查：kubectl命令、故障排查、资源管理、YAML配置要点"
[taxonomies]
tags = ["SRE", "面试", "Kubernetes", "笔试", "K8s"]
+++

## 概述

Kubernetes笔试通常考察：kubectl命令使用、故障排查、资源配置、常见问题诊断。本文列出常见题目和核心解法。

---

## 一、kubectl 基础命令

### 1. 查看资源

```bash
# 查看所有Pod
kubectl get pods -A

# 查看Pod详情
kubectl describe pod <pod-name>

# 查看Pod日志
kubectl logs <pod-name> -c <container-name> --tail=100

# 实时日志
kubectl logs -f <pod-name>

# 查看之前容器的日志（重启后）
kubectl logs <pod-name> --previous
```

---

### 2. 进入容器

```bash
kubectl exec -it <pod-name> -- /bin/sh

# 指定容器
kubectl exec -it <pod-name> -c <container> -- /bin/bash
```

---

### 3. 资源操作

```bash
# 创建
kubectl apply -f deployment.yaml

# 删除
kubectl delete -f deployment.yaml
kubectl delete pod <pod-name>

# 强制删除（卡住的Pod）
kubectl delete pod <pod-name> --force --grace-period=0

# 编辑
kubectl edit deployment <name>

# 扩缩容
kubectl scale deployment <name> --replicas=3
```

---

### 4. 调试命令

```bash
# 查看事件
kubectl get events --sort-by='.lastTimestamp'

# 查看节点状态
kubectl get nodes
kubectl describe node <node-name>

# 查看资源使用
kubectl top pods
kubectl top nodes
```

---

## 二、故障排查类

### 5. Pod一直Pending

**排查步骤**：
```bash
kubectl describe pod <pod-name>
# 查看Events部分
```

**常见原因**：
| 原因 | 解决方法 |
|------|----------|
| 资源不足 | 检查节点资源，扩容或调整requests |
| NodeSelector不匹配 | 检查节点标签 |
| PVC未绑定 | 检查PV/PVC状态 |
| 调度器问题 | 检查kube-scheduler状态 |

---

### 6. Pod一直CrashLoopBackOff

**排查步骤**：
```bash
# 1. 查看日志
kubectl logs <pod-name> --previous

# 2. 查看退出码
kubectl describe pod <pod-name> | grep -A5 "Last State"
```

**常见原因**：
| 退出码 | 含义 |
|--------|------|
| 0 | 正常退出（可能command配置错误）|
| 1 | 应用错误 |
| 137 | OOMKilled（内存不足）|
| 139 | 段错误 |
| 143 | SIGTERM |

---

### 7. Pod一直ImagePullBackOff

**排查步骤**：
```bash
kubectl describe pod <pod-name> | grep -A10 Events
```

**常见原因**：
- 镜像名/标签错误
- 私有仓库未配置imagePullSecrets
- 网络问题

**解决**：
```yaml
spec:
  imagePullSecrets:
    - name: my-registry-secret
```

---

### 8. Service无法访问

**排查步骤**：
```bash
# 1. 检查Service
kubectl get svc <name>
kubectl describe svc <name>

# 2. 检查Endpoints
kubectl get endpoints <name>

# 3. 检查Pod标签是否匹配
kubectl get pods --show-labels
```

**常见原因**：
- Selector与Pod标签不匹配
- Pod未Ready
- NetworkPolicy阻断

---

### 9. 节点NotReady

**排查步骤**：
```bash
# 1. 查看节点状态
kubectl describe node <node>

# 2. 检查kubelet
systemctl status kubelet
journalctl -u kubelet -n 100
```

**常见原因**：
- kubelet挂了
- 网络插件问题
- 磁盘/内存压力
- 证书过期

---

## 三、资源配置类

### 10. 资源限制配置

```yaml
resources:
  requests:       # 调度依据
    memory: "256Mi"
    cpu: "250m"   # 0.25核
  limits:         # 硬限制
    memory: "512Mi"
    cpu: "500m"
```

**要点**：
- `requests`: 调度器保证的最小资源
- `limits`: 容器使用上限
- 内存超限 → OOMKilled
- CPU超限 → 被限流（不会被杀）

---

### 11. 健康检查配置

```yaml
livenessProbe:      # 失败则重启容器
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3

readinessProbe:     # 失败则从Service摘除
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

**要点**：
- `livenessProbe`: 检测容器是否活着
- `readinessProbe`: 检测容器是否准备好接收流量
- `startupProbe`: 慢启动应用使用

---

### 12. 亲和性配置

```yaml
# 节点亲和性
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: disktype
              operator: In
              values: ["ssd"]

# Pod反亲和（分散部署）
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: myapp
        topologyKey: "kubernetes.io/hostname"
```

---

### 13. 污点和容忍

```bash
# 给节点打污点
kubectl taint nodes node1 key=value:NoSchedule

# 查看污点
kubectl describe node node1 | grep Taint
```

```yaml
# Pod容忍污点
tolerations:
  - key: "key"
    operator: "Equal"
    value: "value"
    effect: "NoSchedule"
```

---

### 14. ConfigMap和Secret

```bash
# 创建ConfigMap
kubectl create configmap myconfig --from-file=config.properties
kubectl create configmap myconfig --from-literal=key1=value1

# 创建Secret
kubectl create secret generic mysecret --from-literal=password=123456
```

```yaml
# 使用方式
env:
  - name: CONFIG_KEY
    valueFrom:
      configMapKeyRef:
        name: myconfig
        key: key1

volumeMounts:
  - name: config-volume
    mountPath: /etc/config
volumes:
  - name: config-volume
    configMap:
      name: myconfig
```

---

## 四、常见操作场景

### 15. 滚动更新

```bash
# 更新镜像
kubectl set image deployment/myapp myapp=myapp:v2

# 查看更新状态
kubectl rollout status deployment/myapp

# 回滚
kubectl rollout undo deployment/myapp
kubectl rollout undo deployment/myapp --to-revision=2

# 查看历史
kubectl rollout history deployment/myapp
```

---

### 16. 水平扩缩容（HPA）

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
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

```bash
# 快速创建
kubectl autoscale deployment myapp --min=2 --max=10 --cpu-percent=70
```

---

### 17. 网络策略

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}      # 选择所有Pod
  policyTypes:
    - Ingress
    - Egress
  ingress: []          # 拒绝所有入站
  egress: []           # 拒绝所有出站
```

```yaml
# 只允许特定来源
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - port: 8080
```

---

### 18. PV/PVC

```yaml
# PersistentVolumeClaim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

```yaml
# 使用PVC
volumes:
  - name: data
    persistentVolumeClaim:
      claimName: my-pvc
```

---

## 五、运维脚本

### 19. 批量重启所有Pod

```bash
# 重启Deployment
kubectl rollout restart deployment/<name>

# 批量重启namespace下所有deployment
kubectl get deployment -n <ns> -o name | xargs -I {} kubectl rollout restart {} -n <ns>
```

---

### 20. 导出所有资源

```bash
# 导出deployment
kubectl get deployment <name> -o yaml > deployment.yaml

# 导出时去除状态信息
kubectl get deployment <name> -o yaml | kubectl neat > deployment.yaml
```

---

### 21. 查找资源消耗大的Pod

```bash
# 按CPU排序
kubectl top pods --sort-by=cpu

# 按内存排序
kubectl top pods --sort-by=memory

# 所有namespace
kubectl top pods -A --sort-by=memory | head -20
```

---

### 22. 清理Evicted Pod

```bash
kubectl get pods --all-namespaces -o json | \
  jq -r '.items[] | select(.status.reason=="Evicted") | 
  .metadata.namespace + " " + .metadata.name' | \
  xargs -L1 kubectl delete pod -n
```

---

### 23. 快速端口转发

```bash
# 转发Pod端口
kubectl port-forward pod/<name> 8080:80

# 转发Service端口
kubectl port-forward svc/<name> 8080:80
```

---

## 六、面试高频问题

### 24. Pod的生命周期

```
Pending → Running → Succeeded/Failed
              ↓
          CrashLoopBackOff
```

**状态含义**：
- `Pending`: 等待调度或拉取镜像
- `Running`: 至少一个容器运行中
- `Succeeded`: 所有容器正常退出
- `Failed`: 容器非正常退出
- `Unknown`: 无法获取状态

---

### 25. Deployment vs StatefulSet vs DaemonSet

| 类型 | 场景 | 特点 |
|------|------|------|
| Deployment | 无状态应用 | 可随意扩缩容，Pod可替换 |
| StatefulSet | 有状态应用 | 固定网络标识，有序部署/删除 |
| DaemonSet | 每节点一个 | 日志采集、监控agent |

---

### 26. Service类型

| 类型 | 说明 |
|------|------|
| ClusterIP | 集群内部访问（默认）|
| NodePort | 节点端口暴露（30000-32767）|
| LoadBalancer | 云厂商LB |
| ExternalName | DNS别名 |

---

### 27. 优雅终止流程

```
1. Pod标记为Terminating
2. 从Service Endpoints移除
3. 执行preStop Hook
4. 发送SIGTERM
5. 等待terminationGracePeriodSeconds（默认30s）
6. 发送SIGKILL
```

**配置**：
```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
    - lifecycle:
        preStop:
          exec:
            command: ["/bin/sh", "-c", "sleep 10"]
```

---

## 速查表

| 需求 | 命令 |
|------|------|
| 查看所有Pod | `kubectl get pods -A` |
| Pod详情 | `kubectl describe pod <name>` |
| Pod日志 | `kubectl logs <pod> -f --tail=100` |
| 进入容器 | `kubectl exec -it <pod> -- sh` |
| 事件 | `kubectl get events --sort-by='.lastTimestamp'` |
| 扩容 | `kubectl scale deploy <name> --replicas=N` |
| 更新镜像 | `kubectl set image deploy/<name> <container>=<image>` |
| 回滚 | `kubectl rollout undo deploy/<name>` |
| 重启 | `kubectl rollout restart deploy/<name>` |
| 资源使用 | `kubectl top pods` |
| 端口转发 | `kubectl port-forward pod/<name> 8080:80` |
| 强制删除 | `kubectl delete pod <name> --force --grace-period=0` |

---

## 常见问题快速定位

| 现象 | 检查命令 | 可能原因 |
|------|----------|----------|
| Pending | `describe pod` | 资源不足/调度问题 |
| CrashLoopBackOff | `logs --previous` | 应用错误/OOM |
| ImagePullBackOff | `describe pod` | 镜像/仓库问题 |
| Service不通 | `get endpoints` | 标签不匹配/Pod未Ready |
| 节点NotReady | `describe node` | kubelet/网络/磁盘问题 |
