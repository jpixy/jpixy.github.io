+++
title = "09.PV和PVC详解"
slug = "k8s-PV和PVC的详解"
+++

# Kubernetes PV 和 PVC 详解
## 一、核心概念
### 1. PV (PersistentVolume) - 持久卷
+ **定义**：集群级别的存储资源，由管理员预先配置或通过 StorageClass 动态供应
+ **特点**：
    - 独立于 Pod 生命周期
    - 可以是网络存储(NFS, iSCSI)、云存储(AWS EBS, GCE PD)或本地存储
    - 具有特定的容量、访问模式和其他特性

### 2. PVC (PersistentVolumeClaim) - 持久卷声明
+ **定义**：用户对存储资源的请求，类似于 Pod 消耗节点资源的方式
+ **特点**：
    - 绑定到特定的命名空间
    - 描述所需的存储大小、访问模式和其他特性
    - 通过 StorageClass 指定动态供应的要求

## 二、PV 和 PVC 的生命周期
1. **供应(Provisioning)**：
    - 静态供应：管理员手动创建 PV
    - 动态供应：通过 StorageClass 自动创建 PV
2. **绑定(Binding)**：
    - PVC 找到匹配的 PV 后形成绑定关系
    - 一对一绑定，绑定后 PV 不能被其他 PVC 使用
3. **使用(Using)**：
    - Pod 通过 PVC 使用 PV
    - 系统将 PV 挂载到 Pod 中指定的路径
4. **回收(Reclaiming)**：
    - 当 PVC 被删除后，PV 的回收策略决定后续操作：
        * Retain：保留数据(手动清理)
        * Delete：自动删除存储资源
        * Recycle：基本擦除后重新可用(已弃用)

## 三、关键配置详解
### 1. PV 配置示例
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs-example
spec:
  capacity:
    storage: 10Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs
  nfs:
    path: /data/nfs
    server: nfs-server.example.com
```

### 2. PVC 配置示例
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-example
  namespace: default
spec:
  storageClassName: nfs
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
```

### 3. 访问模式(Access Modes)
| 模式 | 描述 | 支持的存储类型 |
| --- | --- | --- |
| ReadWriteOnce(RWO) | 可被单个节点读写 | 大多数块存储 |
| ReadOnlyMany(ROX) | 可被多个节点只读 | NFS, 对象存储 |
| ReadWriteMany(RWX) | 可被多个节点读写 | NFS, CephFS |


## 四、静态供应 vs 动态供应
### 1. 静态供应流程
1. 管理员创建 PV
2. 用户创建 PVC
3. Kubernetes 绑定 PVC 到匹配的 PV
4. Pod 使用 PVC

### 2. 动态供应流程
1. 管理员创建 StorageClass
2. 用户创建 PVC (指定 StorageClass)
3. 动态供应器自动创建 PV
4. Kubernetes 绑定 PVC 到新 PV
5. Pod 使用 PVC

### 3. StorageClass 示例
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  fsType: ext4
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

## 五、常见问题及解决方案
### 1. PVC 处于 Pending 状态
**可能原因**：

+ 没有可用的 PV 满足 PVC 要求
+ StorageClass 不存在或配置错误
+ 动态供应器故障

**解决方案**：

```bash
# 检查 PVC 详情
kubectl describe pvc <pvc-name>

# 检查 PV 列表
kubectl get pv

# 检查 StorageClass
kubectl get storageclass
```

### 2. PV 处于 Released 状态
**原因**：PVC 被删除但 PV 回收策略为 Retain

**解决方案**：

```bash
# 手动回收 PV
kubectl patch pv <pv-name> -p '{"spec":{"claimRef": null}}'
```

### 3. 挂载失败
**可能原因**：

+ 节点无法访问存储后端
+ 文件系统不兼容
+ 权限问题

**解决方案**：

```bash
# 检查 Pod 事件
kubectl describe pod <pod-name>

# 检查节点存储状态
kubectl get nodes -o wide
```

## 六、最佳实践
1. **生产环境推荐使用动态供应**：
    - 减少管理开销
    - 自动按需创建存储
2. **合理设置回收策略**：
    - 重要数据使用 Retain
    - 临时数据使用 Delete
3. **使用 Volume Snapshot**：

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: my-snapshot
spec:
  volumeSnapshotClassName: csi-aws-vsc
  source:
    persistentVolumeClaimName: my-pvc
```

4. **考虑拓扑约束**：

```yaml
volumeBindingMode: WaitForFirstConsumer
```

5. **监控存储使用**：
    - 设置存储配额
    - 监控 PV/PVC 状态

PV 和 PVC 机制将存储的物理细节与使用需求分离，使应用能够以一致的方式使用各种存储资源，是 Kubernetes 存储管理的核心抽象。

