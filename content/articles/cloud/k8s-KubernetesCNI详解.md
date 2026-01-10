+++
title = "Kubernetes CNI (Container Network Interface) 详解"
slug = "k8s-KubernetesCNI详解"
+++

# Kubernetes CNI (Container Network Interface) 详解
CNI (Container Network Interface) 是 Kubernetes 网络模型的核心实现机制，下面我将全面介绍 CNI 的工作原理、组件和常见实现。

## 一、CNI 概述
### 基本概念
+ **定义**：CNI 是一个云原生计算基金会(CNCF)项目，提供容器网络配置的规范和库
+ **目的**：在容器运行时和网络实现之间提供标准化接口
+ **核心原则**：
    - 容器运行时无关性
    - 支持多种网络实现
    - 简单的插件机制

### CNI 在 Kubernetes 中的角色
1. 为每个 Pod 分配唯一的 IP 地址
2. 建立 Pod 间通信网络
3. 实现 Kubernetes 网络模型要求：
    - 所有 Pod 可以不经过 NAT 直接通信
    - 所有节点可以与所有 Pod 通信
    - Pod 看到的自己的 IP 与其他 Pod 看到的该 Pod 的 IP 一致

## 二、CNI 核心组件
### 1. CNI 插件类型
| 类型 | 职责 | 示例 |
| --- | --- | --- |
| **Main Plugin** | 创建网络接口 | bridge, macvlan, ipvlan |
| **IPAM Plugin** | IP 地址分配 | host-local, dhcp |
| **Meta Plugin** | 组合其他插件 | flannel, multus |


### 2. CNI 接口规范
CNI 插件必须实现的命令：

+ **ADD**：容器加入网络时调用
+ **DEL**：容器离开网络时调用
+ **CHECK**：检查网络配置是否有效
+ **VERSION**：报告插件版本

### 3. CNI 配置文件
位于 `/etc/cni/net.d/`，示例配置：

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

## 三、CNI 工作流程
### 1. Pod 创建时的网络配置流程
1. kubelet 调用 CRI (Container Runtime Interface) 创建容器
2. CRI 运行时(如 containerd)调用 CNI 插件
3. CNI 插件执行：
    - 创建网络接口(veth pair)
    - 分配 IP 地址(通过 IPAM)
    - 配置网络路由
4. 返回网络配置信息给运行时

### 2. Pod 删除时的网络清理流程
1. kubelet 调用 CRI 停止容器
2. CRI 运行时调用 CNI 插件
3. CNI 插件执行：
    - 释放 IP 地址
    - 删除网络接口
    - 清理路由规则

## 四、主流 CNI 插件实现
### 1. Flannel
+ **特点**：简单易用，适合初学者
+ **后端**：
    - VXLAN (默认)
    - host-gw (性能更好但要求二层连通)
    - UDP (遗留模式)
+ **配置示例**：

```yaml
net-conf.json: |
  {
    "Network": "10.244.0.0/16",
    "Backend": {
      "Type": "vxlan"
    }
  }
```

### 2. Calico
+ **特点**：高性能，支持网络策略
+ **模式**：
    - BGP (路由模式)
    - IP-in-IP (隧道模式)
+ **组件**：
    - Felix: 节点代理，配置路由和 ACL
    - BIRD: BGP 路由分发
    - confd: 配置管理

### 3. Cilium
+ **特点**：基于 eBPF 的高性能网络和安全
+ **能力**：
    - 服务网格加速
    - 网络策略执行
    - 可观测性
+ **架构**：  
![](https://cilium.io/static/a6b5f0e6d5e2c2e8f8f9e8f9e8f9e8f9/cilium-arch.png)

### 4. Weave Net
+ **特点**：简单可靠的覆盖网络
+ **技术**：
    - 使用 UDP 封装(可加密)
    - 自主路由算法
+ **优势**：对网络基础设施要求低

## 五、CNI 高级功能
### 1. 多网络接口(Multus)
+ **用途**：为 Pod 提供多个网络接口
+ **场景**：
    - 分离数据平面和控制平面
    - SR-IOV 高速网络
    - 专用管理网络
+ **配置示例**：

```json
{
  "name": "multus-cni-network",
  "type": "multus",
  "delegates": [
    {
      "name": "default-network",
      "cniVersion": "0.3.1",
      "type": "flannel"
    }
  ]
}
```

### 2. 网络策略
+ **实现插件**：Calico, Cilium, Weave 等
+ **示例策略**：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-policy
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
    ports:
    - protocol: TCP
      port: 6379
```

### 3. 服务网格集成
+ 现代 CNI 插件(如 Cilium)可直接提供服务网格功能
+ 替代或补充 Istio/Linkerd 的数据平面

## 六、CNI 性能考量
### 1. 网络模式对比
| 模式 | 性能 | 配置复杂度 | 基础设施要求 |
| --- | --- | --- | --- |
| **覆盖网络** (VXLAN等) | 中 | 低 | 无特殊要求 |
| **纯路由** (BGP) | 高 | 中 | 支持 BGP 的路由器 |
| **主机网关** (host-gw) | 很高 | 中 | 二层网络连通 |
| **eBPF** (Cilium) | 极高 | 高 | 较新内核 |


### 2. 性能优化技术
+ **eBPF 加速**：绕过 iptables 实现服务转发
+ **硬件卸载**：使用 SR-IOV, RDMA 等技术
+ **协议优化**：选择更高效的封装协议
+ **拓扑感知**：优化节点间通信路径

## 七、CNI 问题排查
### 1. 常见问题
+ **Pod 无网络**：
    - CNI 插件未正确安装
    - IP 地址耗尽
    - 网络策略阻止通信
+ **跨节点通信失败**：
    - 防火墙规则阻止
    - 路由配置错误
    - 封装协议不匹配

### 2. 诊断工具
+ **查看 CNI 配置**：

```bash
ls /etc/cni/net.d/
```

+ **检查网络接口**：

```bash
ip link show
ip addr show
```

+ **测试连通性**：

```bash
kubectl exec -it <pod> -- ping <target>
```

+ **查看日志**：

```bash
journalctl -u kubelet -f
```

## 八、CNI 选择指南
### 根据场景选择 CNI
| 使用场景 | 推荐 CNI |
| --- | --- |
| 简单测试/开发 | Flannel |
| 生产环境通用需求 | Calico |
| 高性能/安全需求 | Cilium |
| 多网络接口需求 | Multus + 其他插件 |
| 云服务集成 | 云厂商提供的 CNI (如 AWS VPC CNI) |


### 根据规模选择
+ **小型集群** (<50 节点)：任何 CNI 都适用
+ **中型集群** (50-500 节点)：Calico, Cilium
+ **大型集群** (>500 节点)：Cilium, 云厂商专用方案

CNI 作为 Kubernetes 网络的基础，对集群的性能、安全和可靠性有着至关重要的影响。理解 CNI 的工作原理和不同实现的特性，是设计和运维 Kubernetes 集群的关键能力。

