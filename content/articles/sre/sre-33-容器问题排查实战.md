+++
title = "33.容器问题排查实战"
date = 2026-01-21
description = "SRE容器问题排查完整指南：Docker容器故障、Kubernetes Pod问题的定位与解决"
[taxonomies]
tags = ["SRE", "Docker", "Kubernetes", "容器", "排查", "实战"]
+++

## 概述

容器化环境的问题排查与传统环境有所不同。本文详细介绍Docker和Kubernetes环境下的问题排查方法和常用命令。

---

# 一、Docker容器排查

## 1.1 容器无法启动

### 场景：容器启动后立即退出

**第一步：查看容器状态**

```bash
# 查看所有容器（包括已停止的）
docker ps -a

# 输出列解读：
# CONTAINER ID  IMAGE      COMMAND     CREATED      STATUS                    PORTS  NAMES
# abc123        nginx      "nginx"     1 min ago    Exited (1) 30 sec ago            myapp
#
# STATUS说明：
# Up X minutes        - 运行中
# Exited (0)          - 正常退出
# Exited (1)          - 错误退出
# Exited (137)        - 被SIGKILL杀死（通常是OOM）
# Exited (139)        - 段错误
# Created             - 创建但未启动

# 查看容器详细信息
docker inspect <container_id>

# 提取特定信息
docker inspect -f '{{.State.Status}}' <container_id>
docker inspect -f '{{.State.ExitCode}}' <container_id>
docker inspect -f '{{.State.Error}}' <container_id>
docker inspect -f '{{.State.OOMKilled}}' <container_id>
```

**第二步：查看容器日志**

```bash
# 查看日志
docker logs <container_id>

# 常用参数详解：
# --tail 100     最后100行
# -f             实时跟踪
# --since 1h     最近1小时
# --until 30m    30分钟前的
# -t             显示时间戳
# --details      显示额外信息

# 实时跟踪最后100行
docker logs -f --tail 100 <container_id>

# 查看特定时间段
docker logs --since "2024-01-21T10:00:00" --until "2024-01-21T11:00:00" <container_id>

# 输出到文件分析
docker logs <container_id> > container.log 2>&1
```

**第三步：检查容器配置**

```bash
# 查看启动命令
docker inspect -f '{{.Config.Cmd}}' <container_id>
docker inspect -f '{{.Config.Entrypoint}}' <container_id>

# 查看环境变量
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' <container_id>

# 查看挂载点
docker inspect -f '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' <container_id>

# 查看网络配置
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container_id>
```

### 常见启动失败原因

#### 原因1：镜像问题

```bash
# 镜像不存在
docker images | grep <image_name>

# 拉取镜像
docker pull <image_name>

# 检查镜像层
docker history <image_name>

# 镜像大小
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

#### 原因2：端口冲突

```bash
# 检查端口是否被占用
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep 8080
ss -tlnp | grep :8080

# 查看容器端口映射
docker port <container_id>
```

#### 原因3：资源限制

```bash
# 查看容器资源限制
docker stats <container_id> --no-stream

# 输出列解读：
# CONTAINER ID  NAME   CPU %  MEM USAGE / LIMIT     MEM %   NET I/O        BLOCK I/O
# abc123        myapp  0.50%  100MiB / 512MiB       19.53%  1.2kB / 0B     0B / 0B

# 查看资源限制配置
docker inspect -f '{{.HostConfig.Memory}}' <container_id>      # 内存限制（字节）
docker inspect -f '{{.HostConfig.NanoCpus}}' <container_id>    # CPU限制（纳秒）
docker inspect -f '{{.HostConfig.CpuShares}}' <container_id>   # CPU份额

# 运行时修改资源限制
docker update --memory 1g --cpus 2 <container_id>
```

#### 原因4：挂载卷问题

```bash
# 检查挂载点是否存在
docker inspect -f '{{range .Mounts}}{{.Source}}{{println}}{{end}}' <container_id> | xargs -I {} ls -la {}

# 检查权限
docker inspect -f '{{range .Mounts}}{{.Source}} ({{.Mode}}){{println}}{{end}}' <container_id>

# 进入容器检查（如果能启动）
docker run -it --entrypoint /bin/sh <image_name>
ls -la /path/to/mount
```

---

## 1.2 容器运行时问题

### 进入容器调试

```bash
# 进入运行中的容器
docker exec -it <container_id> /bin/bash
# 或
docker exec -it <container_id> /bin/sh

# exec参数详解：
# -i    交互模式（保持STDIN开放）
# -t    分配伪终端
# -u    指定用户
# -w    指定工作目录
# -e    设置环境变量

# 以root进入
docker exec -u root -it <container_id> /bin/bash

# 在容器中执行单条命令
docker exec <container_id> ps aux
docker exec <container_id> cat /etc/hosts
```

### 容器内排查

```bash
# 进入容器后

# 查看进程
ps aux

# 查看网络
cat /etc/resolv.conf
cat /etc/hosts
ip addr    # 或 ifconfig

# 测试网络连通性
ping <host>
curl -v <url>
nc -zv <host> <port>

# 查看文件系统
df -h
ls -la /

# 查看环境变量
env

# 查看日志（如果有）
tail -f /var/log/*.log
```

### 容器网络问题

```bash
# 查看容器网络
docker network ls

# 查看网络详情
docker network inspect bridge

# 查看容器使用的网络
docker inspect -f '{{json .NetworkSettings.Networks}}' <container_id> | jq

# 容器间通信测试
# 从一个容器ping另一个
docker exec container1 ping container2

# 检查DNS解析
docker exec <container_id> cat /etc/resolv.conf
docker exec <container_id> nslookup <hostname>

# 创建网络并连接容器
docker network create mynet
docker network connect mynet <container_id>
```

---

## 1.3 容器资源问题

### 监控容器资源

```bash
# 实时监控所有容器
docker stats

# 只看一次
docker stats --no-stream

# 自定义格式
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 特定容器
docker stats <container_id>
```

### 容器内存问题

```bash
# 查看内存限制和使用
docker stats --no-stream --format "{{.Name}}: {{.MemUsage}} / {{.MemPerc}}"

# 检查是否OOM
docker inspect -f '{{.State.OOMKilled}}' <container_id>

# 查看cgroup内存限制
cat /sys/fs/cgroup/memory/docker/<container_id>/memory.limit_in_bytes
cat /sys/fs/cgroup/memory/docker/<container_id>/memory.usage_in_bytes

# 调整内存限制
docker update --memory 2g <container_id>
```

### 容器CPU问题

```bash
# 进入容器查看进程CPU
docker exec <container_id> top -bn1

# 宿主机上查看容器进程
# 找到容器的PID
docker inspect -f '{{.State.Pid}}' <container_id>

# 然后用top/htop查看这个PID及其子进程
top -p <pid>

# 限制CPU
docker update --cpus 1.5 <container_id>
```

---

## 1.4 Docker Compose问题

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f <service_name>
docker-compose logs --tail 100

# 重启服务
docker-compose restart <service_name>

# 重新构建并启动
docker-compose up -d --build <service_name>

# 查看配置
docker-compose config

# 进入服务容器
docker-compose exec <service_name> /bin/bash
```

---

# 二、Kubernetes排查

## 2.1 Pod无法启动

### 排查流程

```bash
# 第一步：查看Pod状态
kubectl get pods

# 输出解读：
# NAME      READY   STATUS             RESTARTS   AGE
# myapp     0/1     Pending            0          5m     ← 等待调度
# myapp     0/1     ContainerCreating  0          5m     ← 正在创建
# myapp     0/1     ImagePullBackOff   0          5m     ← 拉取镜像失败
# myapp     0/1     CrashLoopBackOff   5          5m     ← 反复崩溃
# myapp     0/1     Error              0          5m     ← 错误
# myapp     1/1     Running            0          5m     ← 正常运行

# 第二步：查看详细信息
kubectl describe pod <pod_name>

# 重点关注：
# Events 部分 - 显示发生了什么
# Conditions 部分 - Pod状态条件
# State 部分 - 容器状态

# 第三步：查看日志
kubectl logs <pod_name>

# 常用参数：
# -c <container>    指定容器（多容器Pod）
# -f                实时跟踪
# --tail 100        最后100行
# --previous        查看上一个容器的日志（崩溃后）
# --since 1h        最近1小时
# --timestamps      显示时间戳

# 查看崩溃前的日志
kubectl logs <pod_name> --previous
```

### 状态：Pending

```bash
# Pending通常是调度问题

# 检查事件
kubectl describe pod <pod_name> | grep -A 20 Events

# 常见原因：
# 1. 资源不足
kubectl describe nodes | grep -A 5 "Allocated resources"

# 2. NodeSelector不匹配
kubectl get nodes --show-labels
kubectl describe pod <pod_name> | grep -A 5 "Node-Selectors"

# 3. 污点和容忍
kubectl describe nodes | grep Taints
kubectl describe pod <pod_name> | grep -A 5 Tolerations

# 4. PVC未绑定
kubectl get pvc
kubectl describe pvc <pvc_name>
```

### 状态：ImagePullBackOff

```bash
# 镜像拉取失败

# 查看详细错误
kubectl describe pod <pod_name> | grep -A 10 "Events"

# 常见原因和解决：

# 1. 镜像名称/标签错误
kubectl get pod <pod_name> -o jsonpath='{.spec.containers[*].image}'

# 2. 私有仓库未配置认证
kubectl get secrets
kubectl describe pod <pod_name> | grep -A 3 "Image Pull Secrets"

# 创建镜像拉取凭证
kubectl create secret docker-registry regcred \
    --docker-server=<registry> \
    --docker-username=<user> \
    --docker-password=<password>

# 3. 网络问题
# 在节点上手动测试
docker pull <image_name>
```

### 状态：CrashLoopBackOff

```bash
# 容器反复崩溃

# 查看日志
kubectl logs <pod_name> --previous

# 查看退出码
kubectl describe pod <pod_name> | grep -A 5 "Last State"

# 退出码含义：
# 0   - 正常退出（可能是command配置问题）
# 1   - 应用错误
# 137 - OOMKilled
# 139 - 段错误
# 143 - SIGTERM

# 如果是OOM
kubectl describe pod <pod_name> | grep -i oom
kubectl top pod <pod_name>

# 临时排查：用sleep保持容器运行
# 修改command为: ["sleep", "infinity"]
# 然后exec进去排查
kubectl exec -it <pod_name> -- /bin/sh
```

---

## 2.2 Pod运行时问题

### 进入Pod调试

```bash
# 进入Pod
kubectl exec -it <pod_name> -- /bin/bash

# 多容器Pod，指定容器
kubectl exec -it <pod_name> -c <container_name> -- /bin/bash

# 执行单条命令
kubectl exec <pod_name> -- cat /etc/hosts
kubectl exec <pod_name> -- ps aux

# 如果容器没有shell，使用临时调试容器
kubectl debug -it <pod_name> --image=busybox --target=<container_name>
```

### Pod网络问题

```bash
# 查看Pod IP
kubectl get pod <pod_name> -o wide

# 查看Service
kubectl get svc
kubectl describe svc <service_name>

# 检查Endpoints
kubectl get endpoints <service_name>
# 如果endpoints为空，说明没有匹配的Pod

# 检查标签匹配
kubectl get pods --show-labels
kubectl describe svc <service_name> | grep Selector

# Pod内测试DNS
kubectl exec <pod_name> -- nslookup <service_name>
kubectl exec <pod_name> -- cat /etc/resolv.conf

# Pod间连通性测试
kubectl exec <pod1> -- ping <pod2_ip>
kubectl exec <pod1> -- curl <service_name>:<port>

# 检查NetworkPolicy
kubectl get networkpolicy
kubectl describe networkpolicy <policy_name>
```

### Pod存储问题

```bash
# 查看PVC状态
kubectl get pvc

# 状态说明：
# Pending  - 等待绑定
# Bound    - 已绑定
# Lost     - PV丢失

# 查看PVC详情
kubectl describe pvc <pvc_name>

# 查看PV
kubectl get pv
kubectl describe pv <pv_name>

# Pod内检查挂载
kubectl exec <pod_name> -- df -h
kubectl exec <pod_name> -- ls -la /path/to/mount
```

---

## 2.3 资源问题

### 资源使用监控

```bash
# 查看Pod资源使用（需要metrics-server）
kubectl top pods
kubectl top pods --containers

# 查看节点资源
kubectl top nodes

# 查看Pod资源配置
kubectl describe pod <pod_name> | grep -A 10 "Limits\|Requests"

# 或使用jsonpath
kubectl get pod <pod_name> -o jsonpath='{.spec.containers[*].resources}'
```

### 节点资源问题

```bash
# 查看节点状态
kubectl get nodes

# 状态说明：
# Ready       - 正常
# NotReady    - 异常
# SchedulingDisabled - 禁止调度

# 查看节点详情
kubectl describe node <node_name>

# 关注：
# Conditions    - 节点状态条件
# Allocatable   - 可分配资源
# Allocated     - 已分配资源
# Events        - 事件

# 检查节点上的Pod
kubectl get pods --all-namespaces -o wide --field-selector spec.nodeName=<node_name>

# 节点压力排查
kubectl describe node <node_name> | grep -A 5 Conditions
# MemoryPressure, DiskPressure, PIDPressure
```

---

## 2.4 常用排查命令

### 快速诊断命令

```bash
# 按状态筛选Pod
kubectl get pods --field-selector=status.phase=Failed
kubectl get pods --field-selector=status.phase!=Running

# 按标签筛选
kubectl get pods -l app=myapp

# 查看所有namespace
kubectl get pods --all-namespaces

# 宽输出（显示节点、IP）
kubectl get pods -o wide

# 排序
kubectl get pods --sort-by='.status.containerStatuses[0].restartCount'
kubectl get pods --sort-by='.metadata.creationTimestamp'

# 查看事件
kubectl get events --sort-by='.lastTimestamp'
kubectl get events --field-selector type=Warning

# 查看资源YAML
kubectl get pod <pod_name> -o yaml
```

### 批量操作

```bash
# 删除所有Failed的Pod
kubectl delete pods --field-selector=status.phase=Failed

# 删除所有Evicted的Pod
kubectl get pods --all-namespaces -o json | jq -r '.items[] | select(.status.reason=="Evicted") | .metadata.name' | xargs kubectl delete pod

# 重启所有Pod（通过rollout）
kubectl rollout restart deployment/<deployment_name>

# 强制删除卡住的Pod
kubectl delete pod <pod_name> --force --grace-period=0
```

---

## 2.5 K8s诊断脚本

```bash
#!/bin/bash
# k8s_diagnose.sh - Kubernetes诊断脚本

NAMESPACE=${1:-"default"}

echo "===== K8s诊断报告 ====="
echo "Namespace: $NAMESPACE"
echo "时间: $(date)"
echo ""

echo "--- 1. Pod状态 ---"
kubectl get pods -n $NAMESPACE -o wide
echo ""

echo "--- 2. 非Running的Pod ---"
kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running 2>/dev/null || echo "全部Running"
echo ""

echo "--- 3. 高重启Pod ---"
kubectl get pods -n $NAMESPACE --sort-by='.status.containerStatuses[0].restartCount' | tail -5
echo ""

echo "--- 4. 最近事件 ---"
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10
echo ""

echo "--- 5. 警告事件 ---"
kubectl get events -n $NAMESPACE --field-selector type=Warning | tail -10
echo ""

echo "--- 6. Service和Endpoints ---"
kubectl get svc,endpoints -n $NAMESPACE
echo ""

echo "--- 7. 资源使用 ---"
kubectl top pods -n $NAMESPACE 2>/dev/null || echo "metrics-server未安装"
echo ""

echo "===== 诊断完成 ====="
```

---

## 总结

### Docker常用命令

| 任务 | 命令 |
|------|------|
| 查看容器 | `docker ps -a` |
| 查看日志 | `docker logs -f --tail 100 <id>` |
| 进入容器 | `docker exec -it <id> /bin/sh` |
| 查看详情 | `docker inspect <id>` |
| 资源监控 | `docker stats` |
| 网络查看 | `docker network ls` |

### Kubernetes常用命令

| 任务 | 命令 |
|------|------|
| 查看Pod | `kubectl get pods -o wide` |
| 查看详情 | `kubectl describe pod <name>` |
| 查看日志 | `kubectl logs <name> --previous` |
| 进入Pod | `kubectl exec -it <name> -- /bin/sh` |
| 查看事件 | `kubectl get events --sort-by='.lastTimestamp'` |
| 资源使用 | `kubectl top pods` |

**排查三板斧**：
1. **get/describe** - 查看状态和事件
2. **logs --previous** - 查看崩溃前日志
3. **exec** - 进入容器调试

**关键记忆**：
1. 容器秒退先看日志和退出码
2. Pending查调度，ImagePull查镜像/认证
3. CrashLoop查日志和资源限制
4. 网络问题先检查Service和Endpoints

---

## 相关文章

- [上一篇：日志分析与故障定位实战](/articles/sre/sre-32-日志分析与故障定位实战/)
- [下一篇：安全事件排查实战](/articles/sre/sre-34-安全事件排查实战/)
