# Kubernetes 污点(Taints)详解与最佳实践
## 一、污点(Taints)基本概念
污点是Kubernetes中节点(Node)级别的属性，用于**排斥**某些Pod调度到该节点上，除非Pod明确声明能够容忍(Tolerate)这些污点。

### 污点的组成
每个污点由三部分组成：

```plain
key=value:effect
```

+ **key**：污点的名称
+ **value**：污点的值（可选）
+ **effect**：污点的效果，有三种类型：
    - `NoSchedule`：不能容忍此污点的Pod不会被调度到该节点
    - `PreferNoSchedule`：尽量不调度不能容忍此污点的Pod到该节点
    - `NoExecute`：不能容忍此污点的Pod不会被调度到该节点，且已运行但不容忍的Pod会被驱逐

## 二、污点的常见应用场景
1. **专用节点**：为特定工作负载保留节点（如GPU节点）
2. **问题节点**：标记有问题的节点（如磁盘故障）
3. **维护节点**：计划维护时标记节点
4. **特殊硬件**：标记具有特殊硬件的节点
5. **节点分组**：按业务或环境分组节点（如生产/测试环境）

## 三、污点操作命令
### 1. 查看节点污点
```bash
kubectl describe node <node-name> | grep Taints
# 或
kubectl get node <node-name> -o jsonpath='{.spec.taints}'
```

### 2. 添加污点
```bash
kubectl taint nodes <node-name> key=value:effect
# 示例：添加一个NoSchedule污点
kubectl taint nodes node1 app=monitoring:NoSchedule
```

### 3. 删除污点
```bash
# 删除指定key和effect的污点
kubectl taint nodes <node-name> key:effect-
# 删除所有指定key的污点
kubectl taint nodes <node-name> key-
# 示例：删除上面的污点
kubectl taint nodes node1 app:NoSchedule-
```

## 四、容忍(Tolerations)配置
Pod可以通过`tolerations`字段声明能够容忍哪些污点：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: nginx
    image: nginx
  tolerations:
  - key: "app"
    operator: "Equal"
    value: "monitoring"
    effect: "NoSchedule"
    tolerationSeconds: 3600  # 仅对NoExecute有效，表示被驱逐前等待的时间
```

### tolerations字段说明：
+ **operator**：
    - `Equal`：key和value都必须匹配
    - `Exists`：只需key存在，忽略value（此时不应指定value字段）
+ **effect**：需要匹配的污点效果，如果为空则匹配所有效果

## 五、污点问题解决方案
### 1. Pod无法调度到特定节点
**问题**：Pod因节点污点无法调度  
**解决**：

+ 检查节点污点：`kubectl describe node <node-name>`
+ 为Pod添加对应的容忍配置
+ 或者删除不必要的节点污点

### 2. Pod被意外驱逐
**问题**：Pod因NoExecute污点被驱逐  
**解决**：

+ 为关键Pod添加容忍配置
+ 设置适当的`tolerationSeconds`以允许优雅终止
+ 检查节点问题并修复

### 3. 专用节点被普通Pod占用
**问题**：专用节点（如GPU节点）被非专用Pod使用  
**解决**：

+ 为专用节点添加污点
+ 只为特定工作负载添加对应的容忍

## 六、污点最佳实践
1. **合理命名污点**：

```bash
# 好例子
kubectl taint nodes node1 dedicated=gpu:NoSchedule
# 坏例子
kubectl taint nodes node1 gpu=true:NoSchedule
```

2. **结合节点选择器使用**：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  nodeSelector:
    accelerator: gpu
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "gpu"
    effect: "NoSchedule"
```

3. **系统保留污点**：
    - Kubernetes会自动为节点添加一些系统污点：
        * `node.kubernetes.io/not-ready`：节点未就绪
        * `node.kubernetes.io/unreachable`：节点不可达
        * `node.kubernetes.io/memory-pressure`：节点内存压力
        * `node.kubernetes.io/disk-pressure`：节点磁盘压力
        * `node.kubernetes.io/pid-pressure`：节点PID压力
        * `node.kubernetes.io/network-unavailable`：节点网络不可用
    - 为关键Pod添加对这些污点的容忍（谨慎使用）：

```yaml
tolerations:
- key: "node.kubernetes.io/unreachable"
  operator: "Exists"
  effect: "NoExecute"
  tolerationSeconds: 6000  # 100分钟
```

4. **维护操作流程**：

```bash
# 1. 标记节点为不可调度（不驱逐现有Pod）
kubectl cordon <node-name>

# 2. 添加NoExecute污点开始驱逐Pod（可选）
kubectl taint nodes <node-name> maintenance=true:NoExecute

# 3. 执行维护操作...

# 4. 维护完成后移除污点
kubectl taint nodes <node-name> maintenance:NoExecute-

# 5. 标记节点为可调度
kubectl uncordon <node-name>
```

5. **多团队共享集群**：
    - 为不同团队分配专用节点组
    - 为每组节点添加团队专属污点
    - 各团队只为自己的Pod添加对应的容忍

## 七、高级使用技巧
1. **动态污点管理**：
    - 使用自定义控制器根据节点条件自动添加/删除污点
    - 例如：当GPU温度过高时自动添加污点
2. **污点与PodDisruptionBudget结合**：

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: zk-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: zookeeper
```

3. **污点与拓扑分布约束**：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: my-app
```

## 八、总结
污点是Kubernetes中强大的节点隔离机制，正确使用可以：

1. 确保关键工作负载获得专用资源
2. 提高集群资源利用率
3. 实现优雅的节点维护流程
4. 构建多租户共享集群环境

最佳实践的核心是：**明确标记节点用途，精确控制Pod调度**，同时注意不要过度使用污点导致调度复杂性增加。

