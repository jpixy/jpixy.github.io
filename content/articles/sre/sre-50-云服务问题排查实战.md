+++
title = "50.云服务问题排查实战"
date = 2026-01-21
description = "SRE云服务问题排查完整指南：AWS、阿里云、GCP常见问题的定位与解决"
[taxonomies]
tags = ["SRE", "云服务", "AWS", "阿里云", "GCP", "排查", "实战"]
+++

## 概述

云服务问题排查与传统IDC有所不同。本文详细介绍主流云平台的常见问题排查方法。

---

# 一、AWS问题排查

## 1.1 EC2实例问题

### 实例状态检查

```bash
# 安装AWS CLI
pip install awscli
aws configure

# 查看实例状态
aws ec2 describe-instances --instance-ids i-1234567890abcdef0

# 查看实例状态检查
aws ec2 describe-instance-status --instance-ids i-1234567890abcdef0

# 输出关键信息：
# InstanceState: running/stopped/terminated
# SystemStatus: ok/impaired/initializing
# InstanceStatus: ok/impaired/initializing

# 查看系统日志（启动问题排查）
aws ec2 get-console-output --instance-id i-1234567890abcdef0

# 查看截图（GUI实例）
aws ec2 get-console-screenshot --instance-id i-1234567890abcdef0
```

### 常见问题

```bash
# 问题1：实例无法启动

# 检查状态
aws ec2 describe-instance-status --instance-ids i-xxx

# 常见原因：
# - InsufficientInstanceCapacity: 可用区资源不足
# - InstanceLimitExceeded: 超出实例配额
# - InvalidSnapshot.NotFound: 快照不存在
# - Client.VolumeLimitExceeded: EBS卷数量超限

# 解决：
# - 尝试其他可用区
# - 申请提升配额
# - 检查关联资源


# 问题2：实例无法连接

# 检查安全组
aws ec2 describe-security-groups --group-ids sg-xxx

# 检查网络ACL
aws ec2 describe-network-acls --network-acl-ids acl-xxx

# 检查路由表
aws ec2 describe-route-tables --route-table-ids rtb-xxx

# 检查实例公网IP
aws ec2 describe-instances --instance-ids i-xxx \
    --query 'Reservations[].Instances[].PublicIpAddress'

# 通过Systems Manager连接（无需SSH）
aws ssm start-session --target i-xxx


# 问题3：实例性能问题

# 获取CloudWatch指标
aws cloudwatch get-metric-statistics \
    --namespace AWS/EC2 \
    --metric-name CPUUtilization \
    --dimensions Name=InstanceId,Value=i-xxx \
    --start-time 2024-01-21T00:00:00Z \
    --end-time 2024-01-21T12:00:00Z \
    --period 300 \
    --statistics Average

# 检查是否被限制（CPU Credit）
aws cloudwatch get-metric-statistics \
    --namespace AWS/EC2 \
    --metric-name CPUCreditBalance \
    --dimensions Name=InstanceId,Value=i-xxx \
    --start-time 2024-01-21T00:00:00Z \
    --end-time 2024-01-21T12:00:00Z \
    --period 300 \
    --statistics Average
# T系列实例CPU积分耗尽会被限制
```

---

## 1.2 EBS存储问题

```bash
# 查看卷状态
aws ec2 describe-volumes --volume-ids vol-xxx

# 状态说明：
# available - 可用（未挂载）
# in-use    - 使用中
# creating  - 创建中
# deleting  - 删除中
# error     - 错误

# 查看卷性能指标
aws cloudwatch get-metric-statistics \
    --namespace AWS/EBS \
    --metric-name VolumeReadOps \
    --dimensions Name=VolumeId,Value=vol-xxx \
    --start-time 2024-01-21T00:00:00Z \
    --end-time 2024-01-21T12:00:00Z \
    --period 300 \
    --statistics Sum

# 检查IOPS是否达到限制
# VolumeQueueLength > 0 表示有IO排队

# 问题：EBS卷性能差
# 原因：
# 1. IOPS达到限制
# 2. 吞吐量达到限制
# 3. 实例EBS带宽限制

# 解决：
# 1. 升级卷类型（gp2 -> gp3 -> io1）
# 2. 增加卷大小（gp2 IOPS与大小相关）
# 3. 使用更大实例类型
```

---

## 1.3 RDS数据库问题

```bash
# 查看RDS实例状态
aws rds describe-db-instances --db-instance-identifier mydb

# 关键状态：
# available       - 正常
# backing-up      - 备份中
# creating        - 创建中
# failed          - 失败
# storage-full    - 存储满

# 查看RDS事件
aws rds describe-events \
    --source-identifier mydb \
    --source-type db-instance \
    --duration 1440

# 查看慢查询日志
aws rds download-db-log-file-portion \
    --db-instance-identifier mydb \
    --log-file-name slowquery/mysql-slowquery.log \
    --output text

# 查看错误日志
aws rds download-db-log-file-portion \
    --db-instance-identifier mydb \
    --log-file-name error/mysql-error.log \
    --output text

# 性能诊断
# 使用Performance Insights
aws pi get-resource-metrics \
    --service-type RDS \
    --identifier db-xxx \
    --metric-queries '{"Metric":"db.load.avg"}' \
    --start-time 2024-01-21T00:00:00Z \
    --end-time 2024-01-21T12:00:00Z \
    --period-in-seconds 60
```

---

## 1.4 网络问题

```bash
# VPC Flow Logs分析
# 首先确保启用了Flow Logs

# 查询被拒绝的流量
aws logs filter-log-events \
    --log-group-name /vpc/flow-logs \
    --filter-pattern "REJECT"

# 检查NAT网关
aws ec2 describe-nat-gateways --nat-gateway-ids nat-xxx

# 检查Internet Gateway
aws ec2 describe-internet-gateways --internet-gateway-ids igw-xxx

# 检查VPC Endpoints
aws ec2 describe-vpc-endpoints

# 连通性测试（Reachability Analyzer）
aws ec2 create-network-insights-path \
    --source i-source \
    --destination i-dest \
    --protocol tcp \
    --destination-port 443

# 检查DNS解析（Route 53）
aws route53 test-dns-answer \
    --hosted-zone-id Z1234567890 \
    --record-name www.example.com \
    --record-type A
```

---

## 1.5 AWS服务配额与限制

```bash
# 查看服务配额
aws service-quotas list-service-quotas --service-code ec2

# 查看EC2实例限制
aws ec2 describe-account-attributes --attribute-names max-instances

# 常见限制：
# EC2:
# - 每区域实例数限制
# - 每实例EBS卷数限制（28个）
# - Elastic IP限制（5个）
#
# RDS:
# - 每区域实例数限制
# - 存储大小限制
#
# Lambda:
# - 并发执行限制（1000）
# - 函数超时限制（15分钟）
# - 部署包大小限制

# 申请提升配额
aws service-quotas request-service-quota-increase \
    --service-code ec2 \
    --quota-code L-1216C47A \
    --desired-value 100
```

---

# 二、阿里云问题排查

## 2.1 ECS实例问题

```bash
# 安装阿里云CLI
pip install aliyun-python-sdk-core
pip install aliyun-cli
aliyun configure

# 查看实例状态
aliyun ecs DescribeInstances --InstanceIds '["i-xxx"]'

# 实例状态：
# Pending   - 创建中
# Running   - 运行中
# Starting  - 启动中
# Stopping  - 停止中
# Stopped   - 已停止

# 查看实例监控
aliyun cms DescribeMetricList \
    --Namespace acs_ecs_dashboard \
    --MetricName CPUUtilization \
    --Dimensions '[{"instanceId":"i-xxx"}]'

# 查看系统事件
aliyun ecs DescribeInstancesFullStatus --InstanceId.1 i-xxx

# 查看控制台日志
aliyun ecs GetInstanceConsoleOutput --InstanceId i-xxx
```

### 常见问题

```bash
# 问题1：ECS连接失败

# 检查安全组
aliyun ecs DescribeSecurityGroupAttribute --SecurityGroupId sg-xxx

# 检查实例公网IP
aliyun ecs DescribeInstances --InstanceIds '["i-xxx"]' \
    --query 'Instances.Instance[0].PublicIpAddress'

# 使用VNC连接（控制台）
# 通过阿里云控制台的VNC连接功能


# 问题2：磁盘问题

# 查看云盘状态
aliyun ecs DescribeDisks --DiskIds '["d-xxx"]'

# 云盘状态：
# In_use     - 使用中
# Available  - 可用
# Attaching  - 挂载中
# Detaching  - 卸载中

# 查看云盘性能
aliyun cms DescribeMetricList \
    --Namespace acs_ecs_dashboard \
    --MetricName DiskReadIOPS \
    --Dimensions '[{"instanceId":"i-xxx","diskId":"d-xxx"}]'
```

---

## 2.2 RDS问题

```bash
# 查看RDS实例
aliyun rds DescribeDBInstances --DBInstanceId rm-xxx

# 实例状态：
# Running    - 运行中
# Creating   - 创建中
# Deleting   - 删除中
# Rebooting  - 重启中

# 查看慢日志
aliyun rds DescribeSlowLogs \
    --DBInstanceId rm-xxx \
    --StartTime 2024-01-21T00:00Z \
    --EndTime 2024-01-21T12:00Z

# 查看性能指标
aliyun cms DescribeMetricList \
    --Namespace acs_rds_dashboard \
    --MetricName CpuUsage \
    --Dimensions '[{"instanceId":"rm-xxx"}]'

# 查看连接数
aliyun rds DescribeDBInstancePerformance \
    --DBInstanceId rm-xxx \
    --Key MySQL_NetworkTraffic
```

---

## 2.3 网络问题

```bash
# 查看VPC
aliyun vpc DescribeVpcs --VpcId vpc-xxx

# 查看路由表
aliyun vpc DescribeRouteTables --RouteTableId vtb-xxx

# 查看NAT网关
aliyun vpc DescribeNatGateways --NatGatewayId ngw-xxx

# 检查EIP
aliyun vpc DescribeEipAddresses --AllocationId eip-xxx

# 检查SLB健康状态
aliyun slb DescribeHealthStatus --LoadBalancerId lb-xxx
```

---

## 2.4 常用排查命令

```bash
# 资源概览
aliyun ecs DescribeInstances --PageSize 100
aliyun rds DescribeDBInstances --PageSize 100
aliyun slb DescribeLoadBalancers --PageSize 100

# 事件查询
aliyun ecs DescribeInstanceHistoryEvents \
    --InstanceId i-xxx \
    --EventType.1 SystemMaintenance.Reboot

# 操作日志
aliyun actiontrail LookupEvents \
    --StartTime 2024-01-21T00:00:00Z \
    --EndTime 2024-01-21T12:00:00Z
```

---

# 三、GCP问题排查

## 3.1 Compute Engine问题

```bash
# 安装gcloud
# curl https://sdk.cloud.google.com | bash
gcloud init

# 查看实例状态
gcloud compute instances describe my-instance --zone=us-central1-a

# 实例状态：
# RUNNING    - 运行中
# STOPPED    - 已停止
# TERMINATED - 已终止
# STAGING    - 创建中
# SUSPENDED  - 已挂起

# 查看串口日志（启动问题）
gcloud compute instances get-serial-port-output my-instance --zone=us-central1-a

# 查看实例组健康状态
gcloud compute instance-groups managed list-instances my-group --zone=us-central1-a

# SSH连接问题排查
gcloud compute ssh my-instance --zone=us-central1-a --troubleshoot

# 防火墙规则检查
gcloud compute firewall-rules list
gcloud compute firewall-rules describe allow-ssh
```

## 3.2 监控与日志

```bash
# 查看指标
gcloud monitoring metrics list --filter="metric.type=compute.googleapis.com/instance/cpu/utilization"

# 查询日志
gcloud logging read "resource.type=gce_instance AND severity>=ERROR" --limit=50

# 查看特定实例日志
gcloud logging read 'resource.type="gce_instance" AND resource.labels.instance_id="123456"'

# 创建日志过滤
gcloud logging read 'textPayload:"error" OR textPayload:"fail"' --limit=100
```

## 3.3 网络问题

```bash
# 查看VPC网络
gcloud compute networks list
gcloud compute networks describe my-vpc

# 查看子网
gcloud compute networks subnets list

# 查看路由
gcloud compute routes list

# 查看防火墙规则
gcloud compute firewall-rules list --filter="network=my-vpc"

# 连通性测试
gcloud compute network-connectivity tests create my-test \
    --source-instance=projects/my-project/zones/us-central1-a/instances/source-vm \
    --destination-ip=10.0.0.5 \
    --destination-port=443 \
    --protocol=TCP
```

---

# 四、云服务通用排查

## 4.1 API限流问题

```bash
# AWS限流
# 错误：Throttling / Rate exceeded

# 查看API调用量
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventSource,AttributeValue=ec2.amazonaws.com \
    --start-time 2024-01-21T00:00:00Z

# 解决方案：
# 1. 使用指数退避重试
# 2. 批量操作减少API调用
# 3. 申请限制提升


# 阿里云限流
# 错误：Throttling.User

# 解决方案类似


# 重试策略示例（Python）
import time
import random

def retry_with_backoff(func, max_retries=5):
    for i in range(max_retries):
        try:
            return func()
        except ThrottlingException:
            wait = (2 ** i) + random.uniform(0, 1)
            time.sleep(wait)
    raise Exception("Max retries exceeded")
```

## 4.2 成本异常排查

```bash
# AWS成本分析
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity DAILY \
    --metrics "BlendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE

# 找出高消费资源
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics "BlendedCost" \
    --group-by Type=DIMENSION,Key=RESOURCE_ID

# 常见成本问题：
# 1. 未使用的EBS卷
aws ec2 describe-volumes --filters Name=status,Values=available

# 2. 未关联的Elastic IP
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null]'

# 3. 闲置的RDS实例
# 检查连接数为0的实例

# 4. 过大的实例类型
# 检查CPU利用率持续低于20%的实例
```

## 4.3 云服务诊断脚本

```bash
#!/bin/bash
# cloud_diagnose.sh - 云服务诊断

CLOUD=$1  # aws / aliyun / gcp

case $CLOUD in
    aws)
        echo "===== AWS诊断 ====="
        echo ""
        
        echo "--- EC2实例 ---"
        aws ec2 describe-instances \
            --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType]' \
            --output table
        echo ""
        
        echo "--- 不健康的目标组 ---"
        for tg in $(aws elbv2 describe-target-groups --query 'TargetGroups[].TargetGroupArn' --output text); do
            unhealthy=$(aws elbv2 describe-target-health --target-group-arn $tg \
                --query 'TargetHealthDescriptions[?TargetHealth.State!=`healthy`]' --output json)
            if [ "$unhealthy" != "[]" ]; then
                echo "Target Group: $tg"
                echo "$unhealthy"
            fi
        done
        echo ""
        
        echo "--- 最近CloudWatch告警 ---"
        aws cloudwatch describe-alarms --state-value ALARM \
            --query 'MetricAlarms[].[AlarmName,StateValue]' --output table
        echo ""
        ;;
        
    aliyun)
        echo "===== 阿里云诊断 ====="
        echo ""
        
        echo "--- ECS实例 ---"
        aliyun ecs DescribeInstances \
            --query 'Instances.Instance[].[InstanceId,Status,InstanceType]' \
            --output cols
        echo ""
        
        echo "--- SLB健康状态 ---"
        for lb in $(aliyun slb DescribeLoadBalancers --query 'LoadBalancers.LoadBalancer[].LoadBalancerId' --output cols); do
            aliyun slb DescribeHealthStatus --LoadBalancerId $lb
        done
        echo ""
        ;;
        
    gcp)
        echo "===== GCP诊断 ====="
        echo ""
        
        echo "--- Compute实例 ---"
        gcloud compute instances list
        echo ""
        
        echo "--- 错误日志 ---"
        gcloud logging read "severity>=ERROR" --limit=10 --format="table(timestamp,severity,textPayload)"
        echo ""
        ;;
        
    *)
        echo "Usage: $0 <aws|aliyun|gcp>"
        exit 1
        ;;
esac

echo "===== 诊断完成 ====="
```

---

# 五、云服务最佳实践

## 5.1 可观测性

```markdown
## 云服务监控检查清单

### 基础监控
- [ ] CPU/内存/磁盘/网络监控
- [ ] 实例健康检查
- [ ] 负载均衡健康检查
- [ ] 数据库监控

### 日志管理
- [ ] 应用日志收集
- [ ] 系统日志收集
- [ ] 访问日志收集
- [ ] 日志告警配置

### 告警配置
- [ ] 资源使用率告警
- [ ] 服务可用性告警
- [ ] 成本告警
- [ ] 安全告警

### 追踪
- [ ] 分布式追踪
- [ ] 请求链路追踪
- [ ] 性能分析
```

## 5.2 高可用设计

```markdown
## 云服务高可用检查清单

### 多可用区
- [ ] 计算实例跨可用区
- [ ] 数据库多可用区
- [ ] 负载均衡跨可用区

### 自动伸缩
- [ ] 配置Auto Scaling组
- [ ] 设置伸缩策略
- [ ] 健康检查配置

### 数据备份
- [ ] 数据库自动备份
- [ ] 快照策略配置
- [ ] 跨区域复制（重要数据）

### 灾难恢复
- [ ] DR站点准备
- [ ] RTO/RPO定义
- [ ] 恢复演练计划
```

---

## 总结

### AWS命令速查

| 任务 | 命令 |
|------|------|
| 实例状态 | `aws ec2 describe-instances` |
| 系统日志 | `aws ec2 get-console-output` |
| 安全组 | `aws ec2 describe-security-groups` |
| CloudWatch | `aws cloudwatch get-metric-statistics` |
| 服务配额 | `aws service-quotas list-service-quotas` |

### 阿里云命令速查

| 任务 | 命令 |
|------|------|
| 实例状态 | `aliyun ecs DescribeInstances` |
| 监控数据 | `aliyun cms DescribeMetricList` |
| 安全组 | `aliyun ecs DescribeSecurityGroupAttribute` |
| 事件查询 | `aliyun ecs DescribeInstancesFullStatus` |

### GCP命令速查

| 任务 | 命令 |
|------|------|
| 实例状态 | `gcloud compute instances describe` |
| 串口日志 | `gcloud compute instances get-serial-port-output` |
| 防火墙 | `gcloud compute firewall-rules list` |
| 日志查询 | `gcloud logging read` |

### 云服务排查三板斧

1. **查状态** - 实例/服务是否正常运行
2. **查日志** - 系统日志、应用日志、审计日志
3. **查配额** - 是否达到服务限制

### 关键记忆

1. 实例连接问题先查安全组
2. 性能问题查CloudWatch/监控指标
3. API限流用指数退避重试
4. 定期检查未使用资源避免浪费
