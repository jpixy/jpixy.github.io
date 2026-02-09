+++
title = "06.Kubernetes安全与RBAC"
description = "RBAC权限管理、Pod安全策略、网络安全与安全最佳实践"
date = 2025-01-16
[taxonomies]
tags = ["kubernetes", "container", "security", "rbac", "devops"]
+++

# Kubernetes安全与RBAC

## 一、K8s安全模型

### 1.1 安全层次

```mermaid
graph TB
    A1["应用安全<br>(代码安全、依赖安全、容器镜像安全)"]
    A2["运行时安全<br>(Pod安全策略、容器运行时安全)"]
    A3["访问控制<br>(认证、授权RBAC、准入控制)"]
    A4["网络安全<br>(NetworkPolicy、TLS、服务网格)"]
    A5["数据安全<br>(Secret加密、etcd加密、存储加密)"]
    A6["基础设施安全<br>(节点安全、网络隔离、审计日志)"]
    
    A1 --> A2 --> A3 --> A4 --> A5 --> A6
```

### 1.2 API请求流程

```mermaid
graph TB
    REQ[客户端请求]
    AUTH["认证 (Authentication)<br>你是谁？<br>(证书、Token、OIDC)"]
    AUTHZ["授权 (Authorization)<br>你能做什么？<br>(RBAC、ABAC、Webhook)"]
    ADM["准入控制 (Admission Ctrl)<br>请求是否合规？<br>(Webhook、Policy)"]
    PROC[请求被处理]
    
    REQ --> AUTH --> AUTHZ --> ADM --> PROC
```

---

## 相关文章

- [上一篇：Kubernetes配置与密钥管理](/articles/cloud-native/k8s-05-配置与密钥管理/)
- [下一篇：Kubernetes运维与故障排查](/articles/cloud-native/k8s-07-运维与故障排查/)
