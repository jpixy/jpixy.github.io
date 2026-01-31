+++
title = "38.监控告警排查实战"
date = 2026-01-21
description = "SRE监控告警排查完整指南：Prometheus查询、Grafana排查、告警风暴处理、监控盲区发现"
[taxonomies]
tags = ["SRE", "监控", "告警", "Prometheus", "Grafana", "实战"]
+++

## 概述

监控告警是SRE的眼睛和耳朵。本文详细介绍监控系统本身的问题排查、告警规则调优和故障时的监控数据分析。

---

# 一、Prometheus排查

## 1.1 Prometheus状态检查

### 服务状态

```bash
# 检查Prometheus服务
systemctl status prometheus

# 查看日志
journalctl -u prometheus -n 100 -f

# 检查配置
promtool check config /etc/prometheus/prometheus.yml

# 检查规则文件
promtool check rules /etc/prometheus/rules/*.yml

# 检查端口
ss -tlnp | grep 9090

# 访问状态页面
curl http://localhost:9090/-/healthy
curl http://localhost:9090/-/ready
```

### Web UI状态页面

```
访问 http://localhost:9090/status

重要页面：
/targets      - 抓取目标状态
/config       - 当前配置
/rules        - 告警规则
/alerts       - 活跃告警
/graph        - 查询界面
/tsdb-status  - 存储状态
/flags        - 启动参数
```

### 常见问题排查

```bash
# 问题1：Target显示DOWN

# 在Prometheus UI查看 /targets
# 看到错误信息：
# - "connection refused" → 目标服务未启动
# - "context deadline exceeded" → 网络问题或超时
# - "server returned HTTP status 401" → 认证问题

# 手动测试抓取
curl http://target_host:9090/metrics

# 检查网络
ping target_host
telnet target_host 9090


# 问题2：指标数据缺失

# 检查target是否正常
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health!="up")'

# 检查指标是否存在
curl 'http://localhost:9090/api/v1/label/__name__/values' | jq '.data[]' | grep "metric_name"

# 查询最近数据点
curl 'http://localhost:9090/api/v1/query?query=metric_name' | jq


# 问题3：Prometheus OOM或重启

# 检查内存使用
curl http://localhost:9090/api/v1/status/runtimeinfo | jq

# 检查存储使用
curl http://localhost:9090/api/v1/status/tsdb | jq

# 常见原因：
# - 时间序列太多（cardinality explosion）
# - 查询太重
# - 存储配置不当

# 查看时间序列数量
curl http://localhost:9090/api/v1/status/tsdb | jq '.data.headStats.numSeries'
```

---

## 1.2 PromQL查询

### 基础查询

```promql
# 即时向量（最新值）
http_requests_total

# 带标签过滤
http_requests_total{job="api-server", status="200"}

# 正则匹配
http_requests_total{method=~"GET|POST"}
http_requests_total{path!~"/health.*"}

# 范围向量（时间范围）
http_requests_total[5m]    # 最近5分钟的所有数据点

# 时间偏移
http_requests_total offset 1h    # 1小时前的值
```

### 常用函数

```promql
# rate - 计算增长率（用于counter）
rate(http_requests_total[5m])
# 每秒请求数（QPS）

# irate - 瞬时增长率（更敏感）
irate(http_requests_total[5m])

# increase - 计算增量
increase(http_requests_total[1h])
# 最近1小时的请求总数

# sum - 求和
sum(rate(http_requests_total[5m]))
# 总QPS

# sum by - 按标签分组求和
sum by (status) (rate(http_requests_total[5m]))
# 按状态码分组的QPS

# avg - 平均值
avg(node_cpu_seconds_total)

# max/min
max(node_memory_MemTotal_bytes)

# count - 计数
count(up == 1)
# 存活的target数量

# topk/bottomk - 前N个/后N个
topk(5, rate(http_requests_total[5m]))

# histogram_quantile - 计算分位数
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
# P99延迟
```

### 故障排查查询

```promql
# 服务可用性
up{job="my-service"}
# 0=down, 1=up

# 错误率
sum(rate(http_requests_total{status=~"5.."}[5m])) 
/ 
sum(rate(http_requests_total[5m])) * 100
# 5xx错误百分比

# 延迟分位数
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # P50
histogram_quantile(0.90, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # P90
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))  # P99

# CPU使用率
100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 内存使用率
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# 磁盘使用率
(1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100

# 网络流量
rate(node_network_receive_bytes_total[5m]) * 8  # 入站bps
rate(node_network_transmit_bytes_total[5m]) * 8 # 出站bps

# 连接数变化
delta(node_netstat_Tcp_CurrEstab[5m])

# 进程重启检测
changes(process_start_time_seconds[1h])
# >0 表示有重启
```

### 复杂查询示例

```promql
# 请求延迟突增检测
(
  histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
  /
  histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m] offset 1h)) by (le))
) > 2
# 延迟比1小时前增加2倍

# 流量异常检测
abs(
  sum(rate(http_requests_total[5m])) 
  - 
  sum(rate(http_requests_total[5m] offset 1d))
) 
/ sum(rate(http_requests_total[5m] offset 1d)) > 0.5
# 流量与昨天同期偏差超过50%

# SLO计算 - 99.9%可用性
(
  sum(rate(http_requests_total{status!~"5.."}[30d]))
  /
  sum(rate(http_requests_total[30d]))
) * 100

# 错误预算消耗速度
(
  sum(rate(http_requests_total{status=~"5.."}[1h]))
  /
  sum(rate(http_requests_total[1h]))
) / 0.001  # 假设SLO是99.9%
# >1 表示正在消耗错误预算
```

---

## 1.3 Prometheus API使用

### 查询API

```bash
# 即时查询
curl 'http://localhost:9090/api/v1/query?query=up'

# 带时间参数
curl 'http://localhost:9090/api/v1/query?query=up&time=2024-01-21T10:00:00Z'

# 范围查询
curl 'http://localhost:9090/api/v1/query_range?query=up&start=2024-01-21T00:00:00Z&end=2024-01-21T12:00:00Z&step=1h'

# 响应格式：
# {
#   "status": "success",
#   "data": {
#     "resultType": "vector",
#     "result": [
#       {"metric": {"job": "api"}, "value": [1705834800, "1"]}
#     ]
#   }
# }

# 使用jq解析
curl -s 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result[] | {job: .metric.job, value: .value[1]}'
```

### 元数据API

```bash
# 获取所有指标名
curl 'http://localhost:9090/api/v1/label/__name__/values'

# 获取标签值
curl 'http://localhost:9090/api/v1/label/job/values'

# 获取指标的所有标签
curl 'http://localhost:9090/api/v1/targets/metadata?metric=http_requests_total'

# 获取时间序列元数据
curl 'http://localhost:9090/api/v1/series?match[]=http_requests_total'
```

### 管理API

```bash
# 重新加载配置
curl -X POST http://localhost:9090/-/reload

# 健康检查
curl http://localhost:9090/-/healthy

# 就绪检查
curl http://localhost:9090/-/ready

# 停止Prometheus（需要启用）
curl -X POST http://localhost:9090/-/quit
```

---

# 二、Grafana排查

## 2.1 Grafana状态检查

```bash
# 检查服务
systemctl status grafana-server

# 查看日志
journalctl -u grafana-server -n 100

# 检查配置
cat /etc/grafana/grafana.ini

# 检查端口
ss -tlnp | grep 3000

# 健康检查
curl http://localhost:3000/api/health
# {"commit":"...","database":"ok","version":"..."}
```

## 2.2 常见问题

### 数据源问题

```bash
# 测试数据源连接
curl -H "Authorization: Bearer <api_key>" \
     http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up

# 数据源配置API
curl -H "Authorization: Bearer <api_key>" \
     http://localhost:3000/api/datasources

# 常见错误：
# "Bad Gateway" - Prometheus不可达
# "Unauthorized" - 认证问题
# "no data" - 查询返回空

# 排查步骤：
# 1. 直接访问Prometheus验证
curl http://prometheus:9090/api/v1/query?query=up

# 2. 检查Grafana数据源配置
# Settings → Data Sources → 编辑 → Save & Test
```

### 面板无数据

```
排查步骤：

1. 检查时间范围
   - 是否选择了正确的时间范围
   - 数据可能在选择时间之外

2. 检查查询
   - 点击面板 → Edit → 查看Query
   - 复制查询到Prometheus直接执行

3. 检查变量
   - Dashboard Settings → Variables
   - 确保变量有值

4. 检查数据源
   - 面板是否选择了正确的数据源
   - 数据源是否正常

5. 查看Query Inspector
   - 面板 → Query Inspector
   - 查看实际发送的请求和响应
```

---

## 2.3 Grafana API

```bash
# 获取所有Dashboard
curl -H "Authorization: Bearer <api_key>" \
     http://localhost:3000/api/search

# 获取特定Dashboard
curl -H "Authorization: Bearer <api_key>" \
     http://localhost:3000/api/dashboards/uid/<dashboard_uid>

# 创建告警静默
curl -X POST \
     -H "Authorization: Bearer <api_key>" \
     -H "Content-Type: application/json" \
     http://localhost:3000/api/alertmanager/grafana/api/v2/silences \
     -d '{
       "matchers": [{"name": "alertname", "value": "HighCPU", "isRegex": false}],
       "startsAt": "2024-01-21T10:00:00Z",
       "endsAt": "2024-01-21T12:00:00Z",
       "createdBy": "admin",
       "comment": "Planned maintenance"
     }'

# 导出Dashboard
curl -H "Authorization: Bearer <api_key>" \
     http://localhost:3000/api/dashboards/uid/<uid> | jq '.dashboard' > dashboard.json
```

---

# 三、告警管理

## 3.1 Alertmanager配置

### 配置文件详解

```yaml
# /etc/alertmanager/alertmanager.yml

global:
  # 全局SMTP配置
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'alertmanager@example.com'
  smtp_auth_password: 'password'
  
  # 全局Slack配置
  slack_api_url: 'https://hooks.slack.com/services/xxx'

# 路由规则
route:
  # 分组依据
  group_by: ['alertname', 'cluster', 'service']
  
  # 分组等待时间（收集同组告警）
  group_wait: 30s
  
  # 分组间隔（同组告警再次发送的间隔）
  group_interval: 5m
  
  # 重复间隔（未解决告警的重复发送间隔）
  repeat_interval: 4h
  
  # 默认接收器
  receiver: 'default-receiver'
  
  # 子路由
  routes:
    # 严重告警发送到PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      repeat_interval: 1h
    
    # 测试环境告警发送到Slack
    - match:
        environment: test
      receiver: 'slack-test'
      repeat_interval: 24h
    
    # 正则匹配
    - match_re:
        service: ^(api|web)$
      receiver: 'team-frontend'

# 接收器配置
receivers:
  - name: 'default-receiver'
    email_configs:
      - to: 'oncall@example.com'
        send_resolved: true
  
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<service_key>'
        severity: critical
  
  - name: 'slack-test'
    slack_configs:
      - channel: '#alerts-test'
        send_resolved: true
        title: '{{ .Status | toUpper }}: {{ .CommonLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'team-frontend'
    slack_configs:
      - channel: '#team-frontend'
    email_configs:
      - to: 'frontend-team@example.com'

# 抑制规则
inhibit_rules:
  # 当存在critical告警时，抑制warning告警
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
```

### 检查配置

```bash
# 检查配置语法
amtool check-config /etc/alertmanager/alertmanager.yml

# 测试路由
amtool config routes test --config.file=/etc/alertmanager/alertmanager.yml \
    alertname=HighCPU severity=critical environment=prod
# 输出匹配的receiver

# 查看当前告警
amtool alert --alertmanager.url=http://localhost:9093

# 查看静默
amtool silence query --alertmanager.url=http://localhost:9093

# 创建静默
amtool silence add alertname=HighCPU --comment="Maintenance" --duration=2h
```

---

## 3.2 告警规则编写

### 告警规则示例

```yaml
# /etc/prometheus/rules/alerts.yml

groups:
  - name: service_alerts
    rules:
      # 服务宕机
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务 {{ $labels.instance }} 宕机"
          description: "{{ $labels.job }} 的 {{ $labels.instance }} 已经宕机超过1分钟"

      # 高错误率
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
            /
            sum(rate(http_requests_total[5m])) by (job)
          ) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.job }} 错误率过高"
          description: "{{ $labels.job }} 的5xx错误率为 {{ $value | humanizePercentage }}"

      # 高延迟
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.job }} P99延迟过高"
          description: "{{ $labels.job }} 的P99延迟为 {{ $value | humanizeDuration }}"

  - name: infrastructure_alerts
    rules:
      # CPU高
      - alert: HighCPUUsage
        expr: |
          100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.instance }} CPU使用率高"
          description: "CPU使用率为 {{ $value | printf \"%.1f\" }}%"

      # 内存高
      - alert: HighMemoryUsage
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.instance }} 内存使用率高"
          description: "内存使用率为 {{ $value | printf \"%.1f\" }}%"

      # 磁盘空间低
      - alert: LowDiskSpace
        expr: |
          (1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.instance }} 磁盘空间不足"
          description: "{{ $labels.mountpoint }} 使用率为 {{ $value | printf \"%.1f\" }}%"

      # 磁盘即将满
      - alert: DiskWillFillIn24Hours
        expr: |
          predict_linear(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}[6h], 24*60*60) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.instance }} 磁盘预计24小时内将满"
          description: "{{ $labels.mountpoint }} 按当前趋势将在24小时内用完"
```

### 告警规则最佳实践

```yaml
# 好的告警规则特点：

# 1. 有意义的for持续时间
- alert: ServiceDown
  expr: up == 0
  for: 1m    # 避免瞬时抖动

# 2. 分层严重级别
  labels:
    severity: critical|warning|info

# 3. 有用的注解
  annotations:
    summary: "简短描述 {{ $labels.instance }}"
    description: "详细描述，包含当前值 {{ $value }}"
    runbook_url: "https://wiki/runbook/service-down"

# 4. 避免告警风暴
# 使用聚合而不是每个实例单独告警
- alert: HighErrorRate
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m])) by (job) > 100
  # 而不是按instance分组

# 5. 使用抑制规则
inhibit_rules:
  - source_match:
      alertname: 'ClusterDown'
    target_match:
      alertname: 'ServiceDown'
    equal: ['cluster']
```

---

## 3.3 告警风暴处理

### 识别告警风暴

```bash
# 查看活跃告警数量
curl http://localhost:9093/api/v2/alerts | jq '. | length'

# 按alertname分组统计
curl http://localhost:9093/api/v2/alerts | jq 'group_by(.labels.alertname) | map({alertname: .[0].labels.alertname, count: length})'

# 查看告警发送历史
# 在Alertmanager日志中
journalctl -u alertmanager | grep "Sending notification"
```

### 处理告警风暴

```bash
# 1. 临时创建静默
amtool silence add alertname=~".*" --comment="Alert storm" --duration=30m

# 2. 针对性静默
amtool silence add alertname="HighCPU" instance=~".*" --comment="Known issue" --duration=2h

# 3. 使用Alertmanager API创建静默
curl -X POST http://localhost:9093/api/v2/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [{"name": "alertname", "value": "HighCPU", "isRegex": false}],
    "startsAt": "2024-01-21T10:00:00.000Z",
    "endsAt": "2024-01-21T12:00:00.000Z",
    "createdBy": "admin",
    "comment": "Known issue during maintenance"
  }'

# 4. 查看和删除静默
amtool silence query
amtool silence expire <silence_id>
```

### 预防告警风暴

```yaml
# 1. 合理的分组配置
route:
  group_by: ['alertname', 'cluster']
  group_wait: 30s        # 等待收集同组告警
  group_interval: 5m     # 同组告警发送间隔

# 2. 聚合告警
# 不要为每个实例创建单独告警
- alert: HighErrorRate
  expr: sum(rate(...)) > threshold  # 聚合

# 3. 使用抑制规则
inhibit_rules:
  - source_match:
      alertname: 'NodeDown'
    target_match_re:
      alertname: '.*'
    equal: ['instance']

# 4. 设置合理的阈值和持续时间
- alert: HighCPU
  expr: cpu_usage > 90
  for: 10m  # 持续10分钟才告警
```

---

# 四、监控诊断实战

## 4.1 故障时的监控分析

### 分析流程

```
1. 确定时间范围
   - 从告警或报告获取故障时间
   - 在Grafana中选择对应时间范围

2. 查看关键指标
   - 错误率
   - 延迟
   - 流量
   - 资源使用

3. 关联分析
   - 对比多个指标的时间线
   - 找出因果关系

4. 下钻分析
   - 从全局到具体服务
   - 从服务到实例
   - 从实例到具体指标

5. 对比分析
   - 与正常时段对比
   - 与之前故障对比
```

### 常用分析查询

```promql
# 故障期间的错误率变化
sum(rate(http_requests_total{status=~"5.."}[1m])) by (job)

# 与昨天同期对比
sum(rate(http_requests_total[5m])) / sum(rate(http_requests_total[5m] offset 1d))

# 各服务延迟对比
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))

# 依赖服务状态
up{job=~"mysql|redis|kafka"}

# 资源变化
rate(node_cpu_seconds_total{mode!="idle"}[5m])
node_memory_MemAvailable_bytes

# 网络错误
rate(node_network_receive_errs_total[5m])
rate(node_network_transmit_errs_total[5m])
```

## 4.2 发现监控盲区

### 检查清单

```markdown
## 监控覆盖检查

### 基础设施
- [ ] CPU使用率
- [ ] 内存使用率
- [ ] 磁盘使用率和IO
- [ ] 网络流量和错误
- [ ] 进程状态

### 应用层
- [ ] 请求量（QPS）
- [ ] 错误率
- [ ] 响应延迟（P50/P90/P99）
- [ ] 并发连接数
- [ ] 队列深度

### 依赖服务
- [ ] 数据库连接和延迟
- [ ] 缓存命中率
- [ ] 消息队列积压
- [ ] 外部API调用

### 业务指标
- [ ] 业务成功率
- [ ] 关键流程转化率
- [ ] 用户活跃度
```

### 发现缺失指标

```promql
# 检查是否有指标
count({__name__=~"http_requests_total"})

# 查看所有可用指标
count by(__name__)({__name__!=""})

# 查看特定job的指标
{job="my-service"} 

# 检查标签完整性
count by(job, instance) (up)
```

---

## 4.3 监控诊断脚本

```bash
#!/bin/bash
# monitoring_diagnose.sh - 监控系统诊断

PROMETHEUS_URL=${PROMETHEUS_URL:-"http://localhost:9090"}
ALERTMANAGER_URL=${ALERTMANAGER_URL:-"http://localhost:9093"}

echo "===== 监控系统诊断 ====="
echo "Prometheus: $PROMETHEUS_URL"
echo "Alertmanager: $ALERTMANAGER_URL"
echo ""

echo "--- 1. Prometheus状态 ---"
curl -s "$PROMETHEUS_URL/-/healthy" && echo " [Healthy]" || echo " [Unhealthy]"
curl -s "$PROMETHEUS_URL/-/ready" && echo " [Ready]" || echo " [Not Ready]"
echo ""

echo "--- 2. Target状态 ---"
echo "Total targets:"
curl -s "$PROMETHEUS_URL/api/v1/targets" | jq '.data.activeTargets | length'
echo "Unhealthy targets:"
curl -s "$PROMETHEUS_URL/api/v1/targets" | jq '[.data.activeTargets[] | select(.health!="up")] | length'
curl -s "$PROMETHEUS_URL/api/v1/targets" | jq '.data.activeTargets[] | select(.health!="up") | {job: .labels.job, instance: .labels.instance, error: .lastError}'
echo ""

echo "--- 3. 时间序列统计 ---"
curl -s "$PROMETHEUS_URL/api/v1/status/tsdb" | jq '{headSeries: .data.headStats.numSeries, headChunks: .data.headStats.numChunks}'
echo ""

echo "--- 4. Alertmanager状态 ---"
curl -s "$ALERTMANAGER_URL/-/healthy" && echo " [Healthy]" || echo " [Unhealthy]"
echo ""

echo "--- 5. 活跃告警 ---"
echo "Total alerts:"
curl -s "$ALERTMANAGER_URL/api/v2/alerts" | jq 'length'
echo "By alertname:"
curl -s "$ALERTMANAGER_URL/api/v2/alerts" | jq 'group_by(.labels.alertname) | map({alertname: .[0].labels.alertname, count: length}) | sort_by(-.count) | .[:10]'
echo ""

echo "--- 6. 活跃静默 ---"
curl -s "$ALERTMANAGER_URL/api/v2/silences" | jq '[.[] | select(.status.state=="active")] | length'
echo ""

echo "===== 诊断完成 ====="
```

---

## 总结

| 任务 | 工具/命令 |
|------|-----------|
| 检查Prometheus | `curl /-/healthy`, `/targets` |
| PromQL查询 | `rate()`, `histogram_quantile()`, `sum by()` |
| 检查告警 | `amtool alert`, Alertmanager API |
| 创建静默 | `amtool silence add` |
| 测试路由 | `amtool config routes test` |
| Grafana诊断 | Query Inspector, 数据源测试 |

**告警三原则**：
1. **可操作** - 收到告警知道该做什么
2. **有意义** - 告警代表真实问题
3. **不遗漏** - 覆盖关键场景

**排查三板斧**：
1. **看Targets** - 数据采集是否正常
2. **看Query** - 查询是否正确
3. **看路由** - 告警是否正确分发

**关键记忆**：
1. `up == 0` 是最基础的可用性告警
2. 告警风暴先静默，后分析
3. for持续时间避免抖动
4. 使用抑制规则减少噪音

---

## 相关文章

- [上一篇：应用性能分析实战](/articles/sre/sre-37-应用性能分析实战/)
- [下一篇：DNS与CDN问题排查实战](/articles/sre/sre-39-DNS与CDN问题排查实战/)
