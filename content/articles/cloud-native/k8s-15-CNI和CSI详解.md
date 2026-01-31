+++
title = "15.Kubernetes CNI和CSI详解"
slug = "k8s-KubernetesCNI和CSI详解"
+++

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

## 相关文章

- [上一篇：Kubernetes CSI详解](/articles/cloud-native/k8s-14-CSI详解/)
- [下一篇：PV和PVC详解](/articles/cloud-native/k8s-16-PV和PVC详解/)
