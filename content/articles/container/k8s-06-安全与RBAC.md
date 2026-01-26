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

```
┌─────────────────────────────────────────────────────────────┐
│                      应用安全                                │
│  (代码安全、依赖安全、容器镜像安全)                         │
├─────────────────────────────────────────────────────────────┤
│                      运行时安全                              │
│  (Pod安全策略、容器运行时安全)                              │
├─────────────────────────────────────────────────────────────┤
│                      访问控制                                │
│  (认证、授权RBAC、准入控制)                                 │
├─────────────────────────────────────────────────────────────┤
│                      网络安全                                │
│  (NetworkPolicy、TLS、服务网格)                             │
├─────────────────────────────────────────────────────────────┤
│                      数据安全                                │
│  (Secret加密、etcd加密、存储加密)                           │
├─────────────────────────────────────────────────────────────┤
│                      基础设施安全                            │
│  (节点安全、网络隔离、审计日志)                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 API请求流程

```
         客户端请求
              │
              ▼
    ┌─────────────────┐
    │    认证         │ ←── 你是谁？
    │ Authentication  │     (证书、Token、OIDC)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │    授权         │ ←── 你能做什么？
    │ Authorization   │     (RBAC、ABAC、Webhook)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   准入控制      │ ←── 请求是否合规？
    │ Admission Ctrl  │     (Webhook、Policy)
    └────────┬────────┘
             │
             ▼
       请求被处理
```

---

## 二、认证 (Authentication)

### 2.1 认证方式

```
客户端证书：
├── kubeconfig中的client-certificate
├── 用于用户和组件认证
└── CN=用户名，O=组

ServiceAccount Token：
├── Pod自动挂载
├── /var/run/secrets/kubernetes.io/serviceaccount/token
└── 用于Pod访问API

Bearer Token：
├── 静态Token文件（不推荐）
└── Bootstrap Token

OpenID Connect：
├── 集成企业SSO
├── Dex、Keycloak等
└── 生产环境推荐

Webhook Token：
├── 外部认证服务
└── 自定义认证逻辑
```

### 2.2 ServiceAccount

```yaml
# 创建ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: default
automountServiceAccountToken: true  # 是否自动挂载Token

---
# Pod使用ServiceAccount
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  serviceAccountName: app-sa
  automountServiceAccountToken: true
  containers:
  - name: app
    image: myapp:v1
```

**Token投射（推荐）**：

```yaml
# K8s 1.21+ 推荐使用投射Token
spec:
  containers:
  - name: app
    volumeMounts:
    - name: token
      mountPath: /var/run/secrets/tokens
  volumes:
  - name: token
    projected:
      sources:
      - serviceAccountToken:
          path: token
          expirationSeconds: 3600
          audience: api
```

---

## 三、RBAC授权

### 3.1 RBAC概念

```
RBAC四个核心对象：

Role/ClusterRole：
├── 定义权限规则
├── Role：命名空间级别
└── ClusterRole：集群级别

RoleBinding/ClusterRoleBinding：
├── 将Role绑定到主体
├── RoleBinding：命名空间级别
└── ClusterRoleBinding：集群级别

Subject（主体）：
├── User：用户
├── Group：组
└── ServiceAccount：服务账户
```

### 3.2 Role和ClusterRole

```yaml
# Role（命名空间级别）
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
- apiGroups: [""]  # 核心API组
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]

---
# ClusterRole（集群级别）
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
  # 可选：限制具体资源名称
  resourceNames: ["my-secret"]
```

**常用verbs**：

```
get：获取单个资源
list：列出资源
watch：监听资源变化
create：创建资源
update：更新资源
patch：部分更新资源
delete：删除资源
deletecollection：批量删除
```

### 3.3 RoleBinding和ClusterRoleBinding

```yaml
# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
# 绑定到用户
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
# 绑定到组
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
# 绑定到ServiceAccount
- kind: ServiceAccount
  name: app-sa
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io

---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-secrets-global
subjects:
- kind: Group
  name: auditors
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

### 3.4 预定义ClusterRole

```
cluster-admin：超级管理员
admin：命名空间管理员
edit：读写权限（无RBAC）
view：只读权限
```

### 3.5 聚合ClusterRole

```yaml
# 聚合规则
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-endpoints
  labels:
    rbac.example.com/aggregate-to-monitoring: "true"
rules:
- apiGroups: [""]
  resources: ["services", "endpoints", "pods"]
  verbs: ["get", "list", "watch"]

---
# 聚合ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring
aggregationRule:
  clusterRoleSelectors:
  - matchLabels:
      rbac.example.com/aggregate-to-monitoring: "true"
rules: []  # 规则由聚合自动填充
```

---

## 四、Pod安全

### 4.1 Pod Security Standards

```
三个安全级别：

Privileged（特权）：
├── 不受限制
└── 用于系统组件

Baseline（基线）：
├── 防止已知提权
├── 适合大多数应用
└── 禁止hostNetwork、hostPID等

Restricted（受限）：
├── 最严格安全
├── 遵循最佳实践
└── 非root运行、只读根文件系统等
```

### 4.2 Pod Security Admission

```yaml
# 在命名空间上启用
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # 强制执行
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    # 警告
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
    # 审计
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

### 4.3 SecurityContext

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  # Pod级别安全上下文
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  
  containers:
  - name: app
    image: myapp:v1
    # 容器级别安全上下文
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
      privileged: false
    
    # 只读根文件系统需要的临时目录
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  
  volumes:
  - name: tmp
    emptyDir: {}
```

### 4.4 安全容器配置清单

```yaml
# 生产环境安全Pod模板
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10000
    runAsGroup: 10000
    fsGroup: 10000
    seccompProfile:
      type: RuntimeDefault
  
  containers:
  - name: app
    image: myapp:v1
    imagePullPolicy: Always
    
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
    
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
    
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
```

---

## 五、准入控制

### 5.1 准入控制器

```
内置准入控制器：

必须启用：
├── NodeRestriction
├── PodSecurity
└── ServiceAccount

推荐启用：
├── LimitRanger
├── ResourceQuota
├── NamespaceLifecycle
├── ValidatingAdmissionWebhook
└── MutatingAdmissionWebhook
```

### 5.2 ValidatingWebhook

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-policy
webhooks:
- name: pod-policy.example.com
  clientConfig:
    service:
      name: pod-policy
      namespace: kube-system
      path: "/validate"
    caBundle: <base64-encoded-ca>
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
```

### 5.3 Policy Engines

**Kyverno示例**：

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
spec:
  validationFailureAction: enforce
  rules:
  - name: check-team-label
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Label 'team' is required"
      pattern:
        metadata:
          labels:
            team: "?*"
```

**OPA Gatekeeper示例**：

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-team-label
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    labels:
    - key: team
```

---

## 六、网络安全

### 6.1 NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  # 无ingress/egress规则 = 拒绝所有

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-specific
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
      podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### 6.2 TLS证书管理

**使用cert-manager**：

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx

---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: myapp-tls
  namespace: default
spec:
  secretName: myapp-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - myapp.example.com
```

---

## 七、审计与合规

### 7.1 审计日志

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# 不记录的请求
- level: None
  resources:
  - group: ""
    resources: ["endpoints", "services", "services/status"]

# 记录元数据
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]

# 记录请求体
- level: Request
  resources:
  - group: ""
    resources: ["pods"]
  verbs: ["create", "update", "patch"]

# 记录请求和响应体
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods/exec", "pods/portforward"]
```

### 7.2 安全扫描

```bash
# kube-bench：CIS基准检查
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# trivy：镜像漏洞扫描
trivy image myapp:v1

# kubesec：部署配置安全检查
kubesec scan deployment.yaml
```

---

## 八、最佳实践

### 8.1 安全检查清单

```
RBAC：
□ 最小权限原则
□ 避免使用cluster-admin
□ 定期审查权限
□ 使用命名空间隔离

Pod安全：
□ 使用非root用户运行
□ 只读根文件系统
□ 禁止特权容器
□ 删除不需要的capabilities
□ 启用seccomp

镜像安全：
□ 使用可信镜像仓库
□ 定期扫描漏洞
□ 使用签名镜像
□ 避免使用latest标签

网络安全：
□ 启用NetworkPolicy
□ 默认拒绝入站流量
□ 使用TLS加密
□ 隔离敏感工作负载

Secret管理：
□ 启用etcd加密
□ 使用外部密钥管理
□ 定期轮换凭证
□ 限制Secret访问
```

### 8.2 快速检查命令

```bash
# 检查RBAC
kubectl auth can-i --list --as=system:serviceaccount:default:app-sa
kubectl auth can-i create pods --as=jane

# 检查Pod安全
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}'

# 检查NetworkPolicy
kubectl get networkpolicy -A

# 审计事件
kubectl get events --field-selector type=Warning
```

---

## 九、总结

### 9.1 安全层次

```
深度防御策略：
├── 认证：验证身份
├── 授权：控制权限（RBAC）
├── 准入控制：验证请求
├── Pod安全：运行时保护
├── 网络安全：流量控制
└── 审计：事后追踪
```

### 9.2 核心原则

```
最小权限：只授予必要的权限
纵深防御：多层安全控制
默认安全：默认拒绝，显式允许
持续监控：审计、告警、响应
定期审查：权限、配置、漏洞
```
