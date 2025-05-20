# Kubernetes CNI 和 CSI 详解
## 一、CNI (Container Network Interface) 容器网络接口
### 1. CNI 基本概念
CNI 是 Kubernetes 中用于配置容器网络的插件接口规范，它定义了：

+ 容器运行时与网络插件之间的接口
+ 网络配置的 JSON 格式
+ 插件必须实现的命令（ADD/DEL/CHECK/VERSION）

### 2. CNI 核心组件
| 组件 | 说明 |
| --- | --- |
| CNI 插件 | 实现网络功能的可执行文件 |
| CNI 配置文件 | JSON 格式的网络配置 |
| CNI 二进制目录 | 通常为 `/opt/cni/bin` |
| CNI 配置目录 | 通常为 `/etc/cni/net.d` |


### 3. CNI 工作流程
1. **创建 Pod 时**：
    - kubelet 调用 CNI 插件（通过 `ADD` 操作）
    - 插件为容器创建网络接口
    - 插件配置 IP 地址和路由
2. **删除 Pod 时**：
    - kubelet 调用 CNI 插件（通过 `DEL` 操作）
    - 插件清理网络资源

### 4. 常见 CNI 插件
| 插件 | 特点 | 适用场景 |
| --- | --- | --- |
| Flannel | 简单易用，基于 VXLAN | 中小规模集群 |
| Calico | BGP 路由，支持网络策略 | 需要高性能和策略控制的场景 |
| Cilium | eBPF 技术，高性能 | 大规模集群，安全敏感场景 |
| Weave | 自组网，简单部署 | 开发测试环境 |
| Antrea | 基于 OVS，VM 友好 | 混合云/虚拟化环境 |


### 5. CNI 配置示例
```json
{
  "cniVersion": "0.4.0",
  "name": "mynet",
  "type": "bridge",
  "bridge": "cni0",
  "isGateway": true,
  "ipMasq": true,
  "ipam": {
    "type": "host-local",
    "subnet": "10.22.0.0/16",
    "routes": [
      { "dst": "0.0.0.0/0" }
    ]
  }
}
```

## 二、CSI (Container Storage Interface) 容器存储接口
### 1. CSI 基本概念
CSI 是 Kubernetes 中用于暴露任意存储系统的标准接口，它：

+ 定义了容器编排系统与存储插件之间的 RPC 接口
+ 支持块存储和文件存储
+ 允许第三方存储提供商开发插件而不需要修改 Kubernetes 核心代码

### 2. CSI 架构组件
| 组件 | 说明 |
| --- | --- |
| CSI Driver | 存储提供商实现的插件 |
| External Provisioner | 负责创建/删除存储卷 |
| External Attacher | 负责将存储卷挂载到节点 |
| External Resizer | 负责调整存储卷大小 |
| Node Driver Registrar | 向 kubelet 注册 CSI 驱动 |
| CSI Identity | 提供驱动信息 |
| CSI Controller | 提供存储管理功能 |
| CSI Node | 提供节点级别的存储操作 |


### 3. CSI 工作流程
1. **动态配置**：
    - 用户创建 PVC
    - External Provisioner 调用 CSI CreateVolume
    - 存储系统创建卷并返回 PV
2. **卷挂载**：
    - Pod 调度到节点
    - External Attacher 调用 CSI ControllerPublishVolume
    - Kubelet 调用 CSI NodePublishVolume
3. **卷卸载**：
    - Pod 删除时反向操作

### 4. 常见 CSI 驱动
| 驱动 | 存储系统 | 特点 |
| --- | --- | --- |
| AWS EBS CSI | Amazon EBS | AWS 官方支持 |
| GCE PD CSI | Google Persistent Disk | GCP 官方支持 |
| Azure Disk CSI | Azure Disk | Azure 官方支持 |
| Ceph CSI | Ceph RBD/CephFS | 开源分布式存储 |
| NFS CSI | NFS 服务器 | 通用文件存储 |
| Rook CSI | 多种后端 | 云原生存储编排 |


### 5. CSI 部署示例
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: csi-sc
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: csi-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: csi-sc
```

## 三、CNI 与 CSI 对比
| 特性 | CNI | CSI |
| --- | --- | --- |
| 作用领域 | 容器网络 | 容器存储 |
| 接口类型 | 可执行文件 | gRPC 接口 |
| 主要操作 | ADD/DEL | Create/Delete/Attach/Detach |
| 插件目录 | /opt/cni/bin | /var/lib/kubelet/plugins/[driver] |
| 配置方式 | JSON 文件 | Kubernetes 资源对象 |
| 扩展性 | 网络功能扩展 | 存储功能扩展 |


## 四、最佳实践
### CNI 最佳实践
1. **网络策略规划**：
    - 提前规划 Pod CIDR 和服务 CIDR
    - 确保与现有网络不冲突
2. **插件选择**：
    - 小规模集群：Flannel
    - 生产环境：Calico 或 Cilium
    - 特殊需求：根据性能/安全需求选择
3. **性能调优**：

```bash
# 检查网络延迟
kubectl run -it --rm --restart=Never nettest --image=busybox -- ping <目标IP>

# 检查网络带宽
kubectl run -it --rm --restart=Never iperf --image=networkstatic/iperf3 -- iperf3 -s
```

4. **多网络接口**：
    - 使用 Multus CNI 实现多网卡
    - 分离数据平面和控制平面流量

### CSI 最佳实践
1. **存储类设计**：

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: ebs.csi.aws.com
parameters:
  type: io1
  iopsPerGB: "50"
  fsType: ext4
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
```

2. **卷拓扑感知**：
    - 使用 `WaitForFirstConsumer` 绑定模式
    - 确保存储与 Pod 在同一可用区
3. **扩展与快照**：

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete
```

4. **监控与告警**：
    - 监控 PV/PVC 状态
    - 设置存储容量告警
    - 监控 CSI 驱动健康状态

## 五、常见问题解决
### CNI 问题
1. **Pod 无法获取 IP**：
    - 检查 CNI 插件日志：`journalctl -u kubelet -f`
    - 验证网络配置：`ip addr show` 和 `route -n`
    - 检查 CNI 二进制文件权限
2. **网络性能差**：
    - 考虑使用 host-gw 代替 VXLAN（Flannel）
    - 调整 MTU 大小
    - 使用支持 eBPF 的插件（Cilium）

### CSI 问题
1. **卷无法挂载**：
    - 检查 kubelet 日志：`journalctl -u kubelet -f`
    - 验证节点插件是否运行：`kubectl get pods -n kube-system`
    - 检查存储提供商限制（如 AWS EBS 跨 AZ 限制）
2. **卷扩展失败**：
    - 确保存储系统支持在线扩展
    - 验证 StorageClass 允许扩展
    - 检查文件系统是否支持调整大小

## 六、未来发展趋势
1. **CNI 方向**：
    - eBPF 技术的更广泛应用
    - 服务网格与 CNI 的深度集成
    - 更智能的网络策略管理
2. **CSI 方向**：
    - 本地存储的更好支持
    - 跨集群存储管理
    - 存储 QoS 精细控制

CNI 和 CSI 作为 Kubernetes 网络和存储的扩展接口，是构建生产级集群的关键组件。理解其工作原理和最佳实践，可以帮助您构建更稳定、高效的 Kubernetes 环境。

