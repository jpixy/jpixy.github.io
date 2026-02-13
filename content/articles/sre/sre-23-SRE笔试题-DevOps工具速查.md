+++
title = "23. SRE笔试题-DevOps工具速查"
date = 2026-01-21
weight = 23000
description = "SRE面试DevOps工具速查：Docker容器、Terraform基础设施、Git版本控制，核心命令与考点"
[taxonomies]
tags = ["SRE", "面试", "Docker", "Terraform", "Git", "DevOps"]
+++

## 概述

本文汇总 Docker、Terraform、Git 三个 DevOps 工具的常见面试考点，以速查形式呈现。

---

# 一、Docker（重点）

## 基础命令

| 需求 | 命令 |
|------|------|
| 运行容器 | `docker run -d --name myapp -p 8080:80 nginx` |
| 查看运行中容器 | `docker ps` |
| 查看所有容器 | `docker ps -a` |
| 停止容器 | `docker stop <container>` |
| 删除容器 | `docker rm <container>` |
| 强制删除运行中容器 | `docker rm -f <container>` |
| 查看日志 | `docker logs -f --tail 100 <container>` |
| 进入容器 | `docker exec -it <container> /bin/sh` |
| 查看镜像 | `docker images` |
| 删除镜像 | `docker rmi <image>` |
| 构建镜像 | `docker build -t myapp:v1 .` |
| 推送镜像 | `docker push myrepo/myapp:v1` |

---

## Dockerfile 编写

### 基础模板

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
```

### 常见考点

| 指令 | 作用 | 考点 |
|------|------|------|
| `FROM` | 基础镜像 | 选择slim/alpine减小体积 |
| `RUN` | 执行命令 | 合并多个RUN减少层数 |
| `COPY` vs `ADD` | 复制文件 | COPY更明确，ADD支持解压URL |
| `CMD` vs `ENTRYPOINT` | 启动命令 | CMD可被覆盖，ENTRYPOINT固定 |
| `ENV` | 环境变量 | 配置应用参数 |
| `EXPOSE` | 声明端口 | 仅文档作用，不实际暴露 |
| `VOLUME` | 挂载点 | 持久化数据 |
| `USER` | 运行用户 | 安全：避免root运行 |

### 多阶段构建（考点）

```dockerfile
# 构建阶段
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go build -o myapp

# 运行阶段
FROM alpine:3.18
COPY --from=builder /app/myapp /myapp
CMD ["/myapp"]
```

**考点**：减小镜像体积，分离构建环境和运行环境

---

## 故障排查

### 容器无法启动

```bash
# 查看日志
docker logs <container>

# 查看详情
docker inspect <container>

# 以交互模式排查
docker run -it --entrypoint /bin/sh <image>
```

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `exited (1)` | 应用错误 | 查看logs |
| `exited (137)` | OOM被杀 | 增加内存限制 |
| `exited (139)` | 段错误 | 检查应用bug |
| 容器秒退 | 无前台进程 | 确保CMD是前台进程 |
| 端口冲突 | 端口已占用 | 改用其他端口 |

### 资源限制

```bash
# 限制内存和CPU
docker run -d --memory=512m --cpus=1 myapp
```

---

## 网络

```bash
# 查看网络
docker network ls

# 创建网络
docker network create mynet

# 容器加入网络
docker run -d --network mynet --name app1 myapp
docker run -d --network mynet --name app2 myapp
# app1可通过hostname "app2" 访问app2
```

| 网络类型 | 说明 |
|----------|------|
| bridge | 默认，容器间通过IP通信 |
| host | 共享宿主机网络 |
| none | 无网络 |
| overlay | 跨主机通信(Swarm) |

---

## 数据持久化

```bash
# 挂载目录
docker run -v /host/path:/container/path myapp

# 命名卷
docker volume create mydata
docker run -v mydata:/app/data myapp
```

**考点**：容器删除后数据保留

---

## 清理命令

```bash
# 清理停止的容器
docker container prune

# 清理无用镜像
docker image prune

# 清理所有（谨慎）
docker system prune -a
```

---

## 高频面试题

**Q: Docker和虚拟机的区别？**
- Docker：共享宿主机内核，轻量，秒级启动
- VM：完整OS，隔离性更强，分钟级启动

**Q: 如何减小镜像体积？**
- 使用alpine/slim基础镜像
- 多阶段构建
- 合并RUN指令
- 清理缓存和临时文件

**Q: CMD和ENTRYPOINT区别？**
- CMD：默认命令，可被`docker run`参数覆盖
- ENTRYPOINT：固定入口，`docker run`参数作为其参数
- 最佳实践：ENTRYPOINT定义命令，CMD定义默认参数

---

# 二、Terraform（基础）

## 核心概念

| 概念 | 说明 |
|------|------|
| Provider | 云厂商插件（AWS/GCP/Azure）|
| Resource | 基础设施资源（EC2/VPC等）|
| State | 状态文件，记录当前资源状态 |
| Module | 可复用的配置模块 |
| Variable | 输入变量 |
| Output | 输出值 |

---

## 基础命令

```bash
# 初始化（下载provider）
terraform init

# 预览变更
terraform plan

# 应用变更
terraform apply

# 销毁资源
terraform destroy

# 格式化代码
terraform fmt

# 验证配置
terraform validate

# 查看状态
terraform state list
terraform state show <resource>
```

---

## 基础配置示例

```hcl
# provider.tf
provider "aws" {
  region = "us-west-2"
}

# variables.tf
variable "instance_type" {
  default = "t3.micro"
}

# main.tf
resource "aws_instance" "web" {
  ami           = "ami-12345678"
  instance_type = var.instance_type
  
  tags = {
    Name = "WebServer"
  }
}

# outputs.tf
output "instance_ip" {
  value = aws_instance.web.public_ip
}
```

---

## 常见考点

**Q: terraform plan 和 apply 的区别？**
- plan：预览变更，不实际执行
- apply：实际创建/修改资源

**Q: State文件的作用？**
- 记录当前基础设施状态
- 用于对比期望状态和实际状态
- 应存储在远程后端（S3+DynamoDB）

**Q: 如何处理敏感信息？**
- 使用`sensitive = true`标记变量
- 不要提交tfstate到Git
- 使用Vault或AWS Secrets Manager

**Q: count vs for_each？**
- count：基于数字，删除中间项会导致重建
- for_each：基于map/set，更稳定

---

# 三、Git（基础）

## 常用命令速查

| 需求 | 命令 |
|------|------|
| 克隆 | `git clone <url>` |
| 查看状态 | `git status` |
| 添加文件 | `git add .` |
| 提交 | `git commit -m "message"` |
| 推送 | `git push origin main` |
| 拉取 | `git pull origin main` |
| 查看分支 | `git branch -a` |
| 创建分支 | `git checkout -b feature` |
| 切换分支 | `git checkout main` |
| 合并分支 | `git merge feature` |
| 查看日志 | `git log --oneline` |
| 查看差异 | `git diff` |

---

## 撤销操作

```bash
# 撤销工作区修改
git checkout -- <file>

# 撤销暂存
git reset HEAD <file>

# 撤销最近一次提交（保留修改）
git reset --soft HEAD~1

# 撤销最近一次提交（丢弃修改）
git reset --hard HEAD~1

# 修改最近提交信息
git commit --amend -m "new message"
```

---

## 分支策略

| 策略 | 说明 |
|------|------|
| Git Flow | main + develop + feature/release/hotfix |
| GitHub Flow | main + feature branches，简单 |
| Trunk Based | 主干开发，短生命周期分支 |

---

## 常见考点

**Q: git merge 和 git rebase 区别？**
- merge：创建合并提交，保留分支历史
- rebase：变基，线性历史，更整洁

**Q: git reset 和 git revert 区别？**
- reset：移动HEAD，修改历史（未推送时用）
- revert：创建新提交来撤销，不改历史（已推送时用）

**Q: 如何解决冲突？**
1. 手动编辑冲突文件
2. `git add <file>`
3. `git commit`

**Q: git fetch 和 git pull 区别？**
- fetch：只下载，不合并
- pull：fetch + merge

---

## 快速修复命令

```bash
# 暂存当前修改
git stash
git stash pop

# 查找引入bug的提交
git bisect start
git bisect bad
git bisect good <commit>

# 挑选特定提交
git cherry-pick <commit>

# 清理未跟踪文件
git clean -fd
```

---

# 速查总结

## Docker 核心

```bash
docker run -d -p 8080:80 --name app nginx    # 运行
docker exec -it app sh                        # 进入
docker logs -f app                            # 日志
docker build -t myapp:v1 .                    # 构建
```

## Terraform 核心

```bash
terraform init      # 初始化
terraform plan      # 预览
terraform apply     # 应用
terraform destroy   # 销毁
```

## Git 核心

```bash
git add . && git commit -m "msg"    # 提交
git push origin main                 # 推送
git checkout -b feature              # 新分支
git merge feature                    # 合并
```

---

## 相关文章

- [上一篇：SRE笔试题-Kubernetes速查](@/articles/sre/sre-22-SRE笔试题-Kubernetes速查.md)
- [下一篇：SRE笔试题-概率与智力题](@/articles/sre/sre-24-SRE笔试题-概率与智力题.md)
