# Kubernetes (k8s) 架构与关键组件详解
Kubernetes 是一个开源的容器编排平台，用于自动化部署、扩展和管理容器化应用程序。下面我将详细介绍 Kubernetes 的架构及其关键组件。

## 一、Kubernetes 总体架构
Kubernetes 采用**主从架构(Master-Worker)**，主要由两部分组成：

+ **控制平面(Control Plane)**：即 Master 节点，负责集群管理
+ **工作节点(Worker Nodes)**：运行容器化应用的机器

![](https://d33wubrfki0l68.cloudfront.net/2475489eaf20163ec0f54ddc1d92aa8d4c87c96b/e7c81/images/docs/components-of-kubernetes.svg)

## 二、控制平面(Master)组件
### 1. kube-apiserver
+ **核心组件**：所有集群操作的唯一入口
+ **功能**：
    - 暴露 Kubernetes API
    - 处理 REST 操作
    - 验证和配置 API 对象
    - 协调集群状态
+ **特点**：
    - 水平可扩展(可部署多个实例)
    - 无状态(状态存储在 etcd 中)

### 2. etcd
+ **功能**：分布式键值存储，保存集群所有配置数据和状态
+ **特点**：
    - 高可用性(通常部署 3/5/7 个节点)
    - 强一致性
    - 快速响应(所有写操作需通过 leader)
+ **存储内容**：
    - 节点信息
    - Pod 信息
    - 配置信息
    - 状态信息

### 3. kube-scheduler
+ **功能**：决定 Pod 应该运行在哪个节点上
+ **调度策略**：
    - 资源需求(CPU/内存)
    - 软/硬亲和性和反亲和性
    - 数据局部性
    - 污点和容忍
    - 自定义策略
+ **工作流程**：
    1. 过滤(找出可调度的节点)
    2. 评分(给可调度节点打分)
    3. 绑定(将 Pod 绑定到最佳节点)

### 4. kube-controller-manager
+ **功能**：运行各种控制器，确保集群状态符合预期
+ **核心控制器**：
    - **Node Controller**：监控节点状态
    - **Replication Controller**：维护 Pod 副本数
    - **Deployment Controller**：管理 Deployment 对象
    - **Service Controller**：管理 Service 对象
    - **Endpoint Controller**：维护 Service 与 Pod 的映射
    - **Namespace Controller**：管理命名空间生命周期
    - **PersistentVolume Controller**：管理 PV 和 PVC

### 5. cloud-controller-manager (可选)
+ **功能**：与云提供商 API 交互
+ **包含控制器**：
    - Node Controller
    - Route Controller
    - Service Controller
    - Volume Controller

## 三、工作节点(Worker Node)组件
### 1. kubelet
+ **功能**：节点代理，管理 Pod 和容器
+ **职责**：
    - 向 API Server 注册节点
    - 监控 Pod 规范并确保容器运行
    - 定期报告节点和 Pod 状态
    - 执行容器健康检查
    - 挂载存储卷
    - 下载容器镜像

### 2. kube-proxy
+ **功能**：维护节点网络规则，实现服务抽象
+ **工作模式**：
    - **userspace** (已弃用)
    - **iptables** (默认)
    - **ipvs** (高性能)
+ **职责**：
    - 维护 Service 的虚拟 IP
    - 负载均衡流量到后端 Pod
    - 处理节点端口和外部流量

### 3. 容器运行时(Container Runtime)
+ **功能**：运行容器的软件
+ **支持运行时**：
    - Docker (已弃用)
    - containerd (推荐)
    - CRI-O
    - Mirantis Container Runtime

## 四、插件(Addons)组件
### 1. DNS
+ **CoreDNS**：集群 DNS 服务器，为服务和 Pod 提供 DNS 记录

### 2. Dashboard
+ **Web UI**：管理集群的可视化界面

### 3. 监控
+ **Metrics Server**：收集资源指标
+ **Prometheus**：监控和告警系统

### 4. 日志
+ **EFK Stack** (Elasticsearch, Fluentd, Kibana)：日志收集和分析

### 5. 网络插件
+ **CNI 实现**：
    - Calico
    - Flannel
    - Weave Net
    - Cilium
+ **功能**：提供 Pod 网络和网络策略

## 五、Kubernetes 对象模型
Kubernetes 使用声明式 API，主要对象包括：

1. **Pod**：最小部署单元，包含一个或多个容器
2. **Deployment**：管理 Pod 的副本和滚动更新
3. **Service**：定义一组 Pod 的访问策略
4. **Volume**：为容器提供持久化存储
5. **Namespace**：虚拟集群，用于资源隔离
6. **ConfigMap/Secret**：配置和敏感数据管理
7. **StatefulSet**：管理有状态应用
8. **DaemonSet**：确保所有(或部分)节点运行一个 Pod
9. **Job/CronJob**：运行一次性或定时任务

## 六、Kubernetes 工作流程示例
1. **用户提交部署请求**：`kubectl apply -f deployment.yaml`
2. **API Server 接收请求**：验证并存储到 etcd
3. **Controller Manager 检测变化**：创建 ReplicaSet
4. **Scheduler 分配节点**：将 Pod 分配到合适节点
5. **kubelet 创建 Pod**：通过容器运行时启动容器
6. **kube-proxy 配置网络**：设置 Service 的负载均衡规则
7. **持续监控和调整**：各控制器确保实际状态符合期望状态

## 七、高可用架构
生产环境 Kubernetes 集群通常部署为高可用模式：

1. **多 Master 节点**：防止单点故障
    - 至少 3 个 Master 节点
    - etcd 以集群模式运行
2. **负载均衡**：前置负载均衡器分发 API 请求
3. **多 Worker 节点**：应用实例分布在多个节点
4. **跨可用区部署**：提高容灾能力

## 八、Kubernetes 网络模型
Kubernetes 网络遵循以下基本原则：

1. 每个 Pod 拥有唯一 IP
2. Pod 间可以直接通信(无需 NAT)
3. 节点可以与所有 Pod 通信
4. Pod 内部容器共享网络命名空间

Kubernetes 的这种架构设计使其能够高效管理大规模容器化应用，同时保持灵活性和可扩展性。

