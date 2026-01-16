+++
title = "Helm包管理详解"
description = "Helm架构、Chart开发、模板语法与生产环境最佳实践"
date = 2025-01-16
[taxonomies]
tags = ["kubernetes", "container", "helm", "devops", "package"]
+++

# Helm包管理详解

## 一、Helm概述

### 1.1 什么是Helm

Helm是Kubernetes的包管理工具，类似于apt/yum之于Linux。

**核心概念**：

```
Chart：Helm包，包含K8s资源定义
Repository：Chart仓库
Release：Chart的一次部署实例
Values：Chart的配置参数
```

### 1.2 Helm架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Helm Client                            │
│  (helm install/upgrade/rollback/uninstall)                  │
├─────────────────────────────────────────────────────────────┤
│                     Kubernetes API                          │
├─────────────────────────────────────────────────────────────┤
│                    Kubernetes Cluster                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Release                           │   │
│  │  (Deployment, Service, ConfigMap, Secret, ...)      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、Helm基础操作

### 2.1 安装与配置

```bash
# 安装Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 验证安装
helm version

# 添加仓库
helm repo add stable https://charts.helm.sh/stable
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# 搜索Chart
helm search repo nginx
helm search hub nginx  # 搜索Artifact Hub
```

### 2.2 Chart操作

```bash
# 查看Chart信息
helm show chart bitnami/nginx
helm show values bitnami/nginx
helm show readme bitnami/nginx
helm show all bitnami/nginx

# 安装Chart
helm install my-nginx bitnami/nginx

# 带自定义值安装
helm install my-nginx bitnami/nginx \
  --set service.type=NodePort \
  --set replicaCount=2

# 使用values文件
helm install my-nginx bitnami/nginx -f values.yaml

# 查看安装的Release
helm list
helm list -A  # 所有namespace

# 查看Release状态
helm status my-nginx

# 升级Release
helm upgrade my-nginx bitnami/nginx -f values.yaml

# 回滚
helm rollback my-nginx 1

# 卸载
helm uninstall my-nginx
```

### 2.3 调试与测试

```bash
# 模拟安装（不实际执行）
helm install my-nginx bitnami/nginx --dry-run

# 渲染模板查看
helm template my-nginx bitnami/nginx

# 调试模式
helm install my-nginx bitnami/nginx --debug --dry-run

# 验证Chart
helm lint ./my-chart

# 运行测试
helm test my-nginx
```

---

## 三、Chart结构

### 3.1 目录结构

```
my-chart/
├── Chart.yaml          # Chart元数据
├── Chart.lock          # 依赖锁定文件
├── values.yaml         # 默认配置值
├── values.schema.json  # values的JSON Schema（可选）
├── charts/             # 依赖的子Chart
├── crds/               # CRD定义
├── templates/          # 模板文件
│   ├── NOTES.txt       # 安装后显示的说明
│   ├── _helpers.tpl    # 模板辅助函数
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   └── tests/          # 测试文件
│       └── test-connection.yaml
└── .helmignore         # 打包时忽略的文件
```

### 3.2 Chart.yaml

```yaml
apiVersion: v2           # Helm 3使用v2
name: my-app
version: 1.0.0           # Chart版本
appVersion: "2.0.0"      # 应用版本
description: A Helm chart for my application
type: application        # application或library
keywords:
- app
- web
home: https://example.com
sources:
- https://github.com/example/my-app
maintainers:
- name: John Doe
  email: john@example.com

# 依赖
dependencies:
- name: postgresql
  version: "12.x.x"
  repository: https://charts.bitnami.com/bitnami
  condition: postgresql.enabled
  tags:
  - database
- name: redis
  version: "17.x.x"
  repository: https://charts.bitnami.com/bitnami
  condition: redis.enabled
```

### 3.3 values.yaml

```yaml
# 副本数
replicaCount: 1

# 镜像配置
image:
  repository: myapp
  tag: "1.0.0"
  pullPolicy: IfNotPresent

# 镜像拉取密钥
imagePullSecrets: []

# Service配置
service:
  type: ClusterIP
  port: 80

# Ingress配置
ingress:
  enabled: false
  className: nginx
  annotations: {}
  hosts:
  - host: myapp.example.com
    paths:
    - path: /
      pathType: Prefix
  tls: []

# 资源配置
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

# 自动扩缩容
autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

# 节点选择器
nodeSelector: {}

# 容忍度
tolerations: []

# 亲和性
affinity: {}

# 环境变量
env: []

# ConfigMap数据
config: {}

# 数据库配置（子Chart）
postgresql:
  enabled: true
  auth:
    postgresPassword: secret
    database: myapp
```

---

## 四、模板语法

### 4.1 基础语法

```yaml
# 访问values
image: {{ .Values.image.repository }}:{{ .Values.image.tag }}

# 内置对象
# .Release - Release信息
# .Chart - Chart.yaml内容
# .Values - values.yaml内容
# .Files - 文件访问
# .Capabilities - K8s能力
# .Template - 模板信息

# Release对象
metadata:
  name: {{ .Release.Name }}
  namespace: {{ .Release.Namespace }}
  labels:
    helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
```

### 4.2 控制结构

```yaml
# if/else
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
# ...
{{- end }}

# if-else
{{- if eq .Values.service.type "ClusterIP" }}
  clusterIP: None
{{- else if eq .Values.service.type "NodePort" }}
  type: NodePort
{{- else }}
  type: {{ .Values.service.type }}
{{- end }}

# with - 设置当前作用域
{{- with .Values.nodeSelector }}
nodeSelector:
  {{- toYaml . | nindent 2 }}
{{- end }}

# range - 循环
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}

# range with index
{{- range $index, $host := .Values.ingress.hosts }}
- host: {{ $host.host }}
{{- end }}
```

### 4.3 函数

```yaml
# 字符串函数
{{ .Values.name | upper }}
{{ .Values.name | lower }}
{{ .Values.name | title }}
{{ .Values.name | quote }}
{{ .Values.name | trim }}
{{ printf "%s-%s" .Release.Name .Chart.Name }}

# 默认值
{{ .Values.timeout | default "30s" }}
{{ .Values.env | default dict }}

# 必填值
{{ required "image.repository is required" .Values.image.repository }}

# 类型转换
{{ .Values.port | int }}
{{ .Values.enabled | toString }}

# YAML处理
{{- toYaml .Values.resources | nindent 12 }}

# 缩进
{{ include "my-chart.labels" . | indent 4 }}
{{ include "my-chart.labels" . | nindent 4 }}

# 条件
{{ ternary "yes" "no" .Values.enabled }}
{{ empty .Values.list }}
{{ and .Values.a .Values.b }}
{{ or .Values.a .Values.b }}
{{ not .Values.disabled }}
```

### 4.4 辅助模板 (_helpers.tpl)

```yaml
{{/*
Chart名称
*/}}
{{- define "my-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
完整名称
*/}}
{{- define "my-chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
通用标签
*/}}
{{- define "my-chart.labels" -}}
helm.sh/chart: {{ include "my-chart.chart" . }}
{{ include "my-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
选择器标签
*/}}
{{- define "my-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "my-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

---

## 五、完整Chart示例

### 5.1 deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-chart.fullname" . }}
  labels:
    {{- include "my-chart.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "my-chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        {{- include "my-chart.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "my-chart.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
      - name: {{ .Chart.Name }}
        securityContext:
          {{- toYaml .Values.securityContext | nindent 12 }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.containerPort | default 8080 }}
          protocol: TCP
        {{- if .Values.env }}
        env:
          {{- toYaml .Values.env | nindent 10 }}
        {{- end }}
        {{- if .Values.envFrom }}
        envFrom:
          {{- toYaml .Values.envFrom | nindent 10 }}
        {{- end }}
        livenessProbe:
          {{- toYaml .Values.livenessProbe | nindent 10 }}
        readinessProbe:
          {{- toYaml .Values.readinessProbe | nindent 10 }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        {{- with .Values.volumeMounts }}
        volumeMounts:
          {{- toYaml . | nindent 10 }}
        {{- end }}
      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

### 5.2 service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "my-chart.fullname" . }}
  labels:
    {{- include "my-chart.labels" . | nindent 4 }}
  {{- with .Values.service.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  type: {{ .Values.service.type }}
  ports:
  - port: {{ .Values.service.port }}
    targetPort: http
    protocol: TCP
    name: http
    {{- if and (eq .Values.service.type "NodePort") .Values.service.nodePort }}
    nodePort: {{ .Values.service.nodePort }}
    {{- end }}
  selector:
    {{- include "my-chart.selectorLabels" . | nindent 4 }}
```

---

## 六、Chart最佳实践

### 6.1 命名规范

```yaml
# 资源名称不超过63字符
{{- define "my-chart.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}

# 使用统一的标签
app.kubernetes.io/name: {{ include "my-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
```

### 6.2 values.yaml最佳实践

```yaml
# 1. 提供合理默认值
replicaCount: 1

# 2. 使用嵌套结构
image:
  repository: myapp
  tag: ""  # 默认使用appVersion
  pullPolicy: IfNotPresent

# 3. 布尔值用于可选功能
ingress:
  enabled: false

# 4. 文档化每个值
# -- Number of replicas
replicaCount: 1

# 5. 使用数组时提供空数组默认值
nodeSelector: {}
tolerations: []
affinity: {}
```

### 6.3 安全实践

```yaml
# 1. 不在values中存储敏感信息
# 使用外部Secret或SecretRef

# 2. 设置安全上下文
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL

# 3. 设置资源限制
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

---

## 七、Helm生态

### 7.1 Helmfile

```yaml
# helmfile.yaml
repositories:
- name: bitnami
  url: https://charts.bitnami.com/bitnami

releases:
- name: nginx
  namespace: web
  chart: bitnami/nginx
  version: 15.0.0
  values:
  - values/nginx.yaml
  set:
  - name: replicaCount
    value: 3

- name: redis
  namespace: cache
  chart: bitnami/redis
  version: 17.0.0
  values:
  - values/redis.yaml
```

```bash
# 使用helmfile
helmfile sync
helmfile diff
helmfile apply
```

### 7.2 Chart仓库

```bash
# 创建本地仓库
helm package ./my-chart
helm repo index . --url https://charts.example.com

# 推送到OCI仓库
helm push my-chart-1.0.0.tgz oci://registry.example.com/charts

# 从OCI拉取
helm pull oci://registry.example.com/charts/my-chart --version 1.0.0
```

---

## 八、总结

### 8.1 Helm核心

```
基本概念：
├── Chart = 包
├── Release = 部署实例
├── Repository = 仓库
└── Values = 配置

常用命令：
├── helm install
├── helm upgrade
├── helm rollback
├── helm uninstall
└── helm template

开发要点：
├── 合理的目录结构
├── 使用辅助模板
├── 提供合理默认值
├── 支持自定义配置
└── 测试和文档
```

### 8.2 开发清单

```
Chart开发清单：
□ Chart.yaml完整
□ values.yaml有文档
□ 模板语法正确
□ helm lint通过
□ helm template正确
□ 测试通过
□ NOTES.txt有用
□ 安全配置到位
```
