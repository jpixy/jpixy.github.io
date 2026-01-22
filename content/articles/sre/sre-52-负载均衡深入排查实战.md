+++
title = "52.负载均衡深入排查实战"
date = 2026-01-21
description = "SRE负载均衡深入排查完整指南：Nginx、HAProxy、Envoy高级配置与问题排查"
[taxonomies]
tags = ["SRE", "负载均衡", "Nginx", "HAProxy", "Envoy", "排查", "实战"]
+++

## 概述

负载均衡是高可用架构的核心组件。本文深入介绍Nginx、HAProxy、Envoy的高级配置和问题排查方法。

---

# 一、Nginx负载均衡深入

## 1.1 Nginx状态监控

### 启用状态模块

```nginx
# nginx.conf

# 启用stub_status模块（基础状态）
server {
    listen 8080;
    location /nginx_status {
        stub_status on;
        allow 127.0.0.1;
        deny all;
    }
}

# 商业版Plus可用的详细状态
# location /api {
#     api;
#     allow 127.0.0.1;
#     deny all;
# }
```

```bash
# 查看状态
curl http://localhost:8080/nginx_status

# 输出示例：
# Active connections: 291
# server accepts handled requests
#  16630948 16630948 31070465
# Reading: 6 Writing: 179 Waiting: 106

# 字段说明：
# Active connections - 当前活跃连接数
# accepts           - 总接受连接数
# handled           - 总处理连接数（正常时等于accepts）
# requests          - 总请求数
# Reading           - 正在读取请求头的连接
# Writing           - 正在发送响应的连接
# Waiting           - Keep-alive等待中的连接
```

### 实时监控脚本

```bash
#!/bin/bash
# nginx_monitor.sh - Nginx实时监控

NGINX_STATUS="http://localhost:8080/nginx_status"

while true; do
    clear
    echo "===== Nginx状态监控 ====="
    echo "时间: $(date)"
    echo ""
    
    # 获取状态
    status=$(curl -s $NGINX_STATUS)
    
    # 解析数据
    active=$(echo "$status" | grep "Active" | awk '{print $3}')
    accepts=$(echo "$status" | sed -n '3p' | awk '{print $1}')
    handled=$(echo "$status" | sed -n '3p' | awk '{print $2}')
    requests=$(echo "$status" | sed -n '3p' | awk '{print $3}')
    reading=$(echo "$status" | grep "Reading" | awk '{print $2}')
    writing=$(echo "$status" | grep "Writing" | awk '{print $4}')
    waiting=$(echo "$status" | grep "Waiting" | awk '{print $6}')
    
    echo "活跃连接: $active"
    echo "总请求数: $requests"
    echo "Reading: $reading | Writing: $writing | Waiting: $waiting"
    echo ""
    
    # 连接状态
    echo "--- 连接统计 ---"
    ss -ant | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn
    echo ""
    
    # 错误日志最近5条
    echo "--- 最近错误 ---"
    tail -5 /var/log/nginx/error.log 2>/dev/null | cut -c1-100
    
    sleep 2
done
```

---

## 1.2 Nginx upstream高级配置

### 完整upstream配置

```nginx
upstream backend {
    # 负载均衡算法
    # 默认: 轮询
    # least_conn;     # 最少连接
    # ip_hash;        # IP哈希（会话保持）
    # hash $request_uri consistent;  # 一致性哈希
    # random two least_conn;  # 随机选两个，取连接最少的

    # 服务器配置
    server 10.0.0.1:8080 weight=5 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:8080 weight=3 max_fails=3 fail_timeout=30s;
    server 10.0.0.3:8080 backup;   # 备用服务器
    server 10.0.0.4:8080 down;     # 标记下线

    # 参数详解：
    # weight        权重（默认1）
    # max_fails     失败次数阈值（默认1）
    # fail_timeout  失败超时时间（默认10s），也是恢复检测间隔
    # backup        备用服务器（主服务器都不可用时启用）
    # down          标记永久不可用
    # max_conns     最大并发连接数（商业版）
    # slow_start    慢启动时间（商业版）

    # 连接保持
    keepalive 32;              # 保持的空闲连接数
    keepalive_timeout 60s;     # 空闲连接超时
    keepalive_requests 1000;   # 每个连接最大请求数
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend;
        
        # 代理设置
        proxy_http_version 1.1;
        proxy_set_header Connection "";  # 启用keepalive
        
        # 超时设置
        proxy_connect_timeout 5s;    # 连接超时
        proxy_send_timeout 60s;      # 发送超时
        proxy_read_timeout 60s;      # 读取超时
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 16k;
        proxy_busy_buffers_size 32k;
        
        # 失败重试
        proxy_next_upstream error timeout http_502 http_503 http_504;
        proxy_next_upstream_tries 3;      # 最多重试次数
        proxy_next_upstream_timeout 10s;  # 重试总超时
        
        # 传递真实IP
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 健康检查配置

```nginx
# 开源版：被动健康检查（基于max_fails）
upstream backend {
    server 10.0.0.1:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:8080 max_fails=3 fail_timeout=30s;
}

# 商业版Plus：主动健康检查
upstream backend {
    zone backend 64k;  # 需要共享内存区
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
}

server {
    location / {
        proxy_pass http://backend;
        health_check interval=5s fails=3 passes=2 uri=/health;
        # interval  检查间隔
        # fails     连续失败次数标记为不健康
        # passes    连续成功次数标记为健康
        # uri       健康检查路径
    }
}

# 使用第三方模块：nginx_upstream_check_module
upstream backend {
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    
    check interval=3000 rise=2 fall=5 timeout=1000 type=http;
    check_http_send "HEAD /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx http_3xx;
}
```

---

## 1.3 Nginx常见问题深入

### 502 Bad Gateway详解

```bash
# 502错误原因分析

# 1. 后端服务不可用
# 检查后端服务
curl -v http://backend:8080/health

# 检查Nginx到后端的连接
telnet backend 8080

# 2. 后端响应超时
# 检查错误日志
grep "upstream timed out" /var/log/nginx/error.log

# 解决：增加超时时间
# proxy_read_timeout 120s;

# 3. 后端连接数满
# 检查后端连接数
ss -ant | grep 8080 | wc -l

# 检查Nginx连接
ss -ant | grep nginx

# 4. 后端提前关闭连接
# 错误日志：upstream prematurely closed connection
# 原因：后端keepalive设置不当

# 解决：确保Nginx和后端keepalive一致
# Nginx: keepalive_timeout 60s;
# 后端: keepalive-timeout >= 60s
```

### 504 Gateway Timeout详解

```bash
# 504错误分析

# 1. 后端处理慢
# 检查后端响应时间
curl -w "Time: %{time_total}s\n" -o /dev/null http://backend:8080/slow-api

# 2. 网络问题
# 检查网络延迟
ping backend
mtr backend

# 3. 超时设置太短
# 查看当前设置
nginx -T | grep -E "timeout|time"

# 调整超时
# proxy_connect_timeout 30s;
# proxy_send_timeout 300s;
# proxy_read_timeout 300s;

# 4. 大文件上传超时
# client_max_body_size 100m;
# client_body_timeout 300s;
```

### 连接数限制问题

```bash
# 检查worker连接数
nginx -T | grep worker_connections
# 默认512，生产建议4096-65535

# 检查系统限制
ulimit -n
cat /proc/$(pgrep nginx)/limits | grep "open files"

# 检查当前连接数
ss -ant | grep nginx | wc -l

# 优化配置
# nginx.conf
# worker_processes auto;
# worker_rlimit_nofile 65535;
# events {
#     worker_connections 65535;
#     use epoll;
#     multi_accept on;
# }
```

---

# 二、HAProxy深入排查

## 2.1 HAProxy状态监控

### 统计页面配置

```haproxy
# haproxy.cfg

global
    stats socket /var/run/haproxy.sock mode 660 level admin
    stats timeout 30s

listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s
    stats auth admin:password
    stats admin if TRUE  # 允许管理操作
```

### Socket命令

```bash
# 通过socket查询

# 查看所有统计
echo "show stat" | socat stdio /var/run/haproxy.sock

# CSV格式解析
echo "show stat" | socat stdio /var/run/haproxy.sock | \
    awk -F',' 'NR>1 {printf "%-20s %-10s %-10s %-10s\n", $1"/"$2, $18, $5, $8}'

# 字段说明（常用）：
# $1  pxname   前端/后端名
# $2  svname   服务器名
# $5  scur     当前会话数
# $8  bin      入站字节
# $9  bout     出站字节
# $18 status   状态（UP/DOWN）
# $34 hrsp_5xx 5xx响应数
# $78 lastsess 最后一次会话距今秒数

# 查看服务器状态
echo "show servers state" | socat stdio /var/run/haproxy.sock

# 查看后端状态
echo "show backend" | socat stdio /var/run/haproxy.sock

# 查看会话
echo "show sess" | socat stdio /var/run/haproxy.sock

# 查看错误
echo "show errors" | socat stdio /var/run/haproxy.sock

# 查看信息
echo "show info" | socat stdio /var/run/haproxy.sock
```

### 服务器管理

```bash
# 禁用服务器
echo "disable server backend/server1" | socat stdio /var/run/haproxy.sock

# 启用服务器
echo "enable server backend/server1" | socat stdio /var/run/haproxy.sock

# 设置维护模式（排空连接）
echo "set server backend/server1 state drain" | socat stdio /var/run/haproxy.sock

# 恢复正常
echo "set server backend/server1 state ready" | socat stdio /var/run/haproxy.sock

# 修改权重
echo "set server backend/server1 weight 50" | socat stdio /var/run/haproxy.sock
# weight 0 = 停止接受新连接

# 查看服务器状态
echo "show servers state backend" | socat stdio /var/run/haproxy.sock
```

---

## 2.2 HAProxy高级配置

### 完整配置示例

```haproxy
global
    log /dev/log local0
    log /dev/log local1 notice
    maxconn 100000
    tune.ssl.default-dh-param 2048
    
    # 性能优化
    nbproc 1
    nbthread 4
    cpu-map auto:1/1-4 0-3
    
    stats socket /var/run/haproxy.sock mode 660 level admin
    stats timeout 30s

defaults
    log global
    mode http
    option httplog
    option dontlognull
    option http-server-close
    option forwardfor except 127.0.0.0/8
    option redispatch
    
    # 超时设置
    timeout connect 5s
    timeout client 30s
    timeout server 30s
    timeout http-request 10s
    timeout http-keep-alive 10s
    timeout queue 60s
    timeout tunnel 3600s
    
    # 重试
    retries 3

frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/
    
    # HTTPS重定向
    redirect scheme https code 301 if !{ ssl_fc }
    
    # 请求限制
    stick-table type ip size 1m expire 10s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }
    
    # ACL规则
    acl is_api path_beg /api
    acl is_static path_end .jpg .png .css .js
    
    # 路由到不同后端
    use_backend api_servers if is_api
    use_backend static_servers if is_static
    default_backend web_servers

backend web_servers
    balance roundrobin
    option httpchk GET /health HTTP/1.1\r\nHost:\ localhost
    
    # 健康检查参数
    default-server inter 5s fall 3 rise 2
    
    # 会话保持
    cookie SERVERID insert indirect nocache
    
    server web1 10.0.0.1:8080 check cookie web1
    server web2 10.0.0.2:8080 check cookie web2
    server web3 10.0.0.3:8080 check backup

backend api_servers
    balance leastconn
    option httpchk GET /api/health
    
    # 连接限制
    default-server maxconn 1000
    
    server api1 10.0.0.11:8080 check
    server api2 10.0.0.12:8080 check

backend static_servers
    balance uri
    hash-type consistent
    
    server static1 10.0.0.21:80 check
    server static2 10.0.0.22:80 check
```

### 健康检查详解

```haproxy
# HTTP健康检查
backend web_servers
    option httpchk GET /health HTTP/1.1\r\nHost:\ localhost
    http-check expect status 200
    
    # 或检查响应内容
    http-check expect string "OK"
    
    server web1 10.0.0.1:8080 check inter 5s fall 3 rise 2

# TCP健康检查
backend tcp_servers
    option tcp-check
    tcp-check connect
    tcp-check send "PING\r\n"
    tcp-check expect string "+PONG"
    
    server redis1 10.0.0.1:6379 check

# MySQL健康检查
backend mysql_servers
    option mysql-check user haproxy
    server mysql1 10.0.0.1:3306 check

# 外部脚本检查
backend custom_servers
    option external-check
    external-check command /usr/local/bin/check_server.sh
    server app1 10.0.0.1:8080 check
```

---

## 2.3 HAProxy问题排查

```bash
# 问题1：后端频繁DOWN/UP

# 查看日志
grep "Server.*is DOWN\|Server.*is UP" /var/log/haproxy.log | tail -20

# 可能原因：
# 1. 健康检查太敏感
#    解决：增加fall值，增加inter间隔
# 2. 后端响应不稳定
#    解决：检查后端服务
# 3. 网络问题
#    解决：检查网络连接

# 问题2：连接队列满

# 检查队列
echo "show stat" | socat stdio /var/run/haproxy.sock | \
    awk -F',' '{print $1,$2,$5,$36}'
# $36 = qcur 当前队列长度

# 解决：
# 1. 增加maxconn
# 2. 增加后端服务器
# 3. 优化后端处理速度

# 问题3：会话保持失效

# 检查cookie
curl -v http://example.com 2>&1 | grep -i cookie

# 检查配置
haproxy -c -f /etc/haproxy/haproxy.cfg

# 问题4：SSL问题

# 测试SSL
openssl s_client -connect localhost:443 -servername example.com

# 检查证书
echo "show ssl cert /etc/haproxy/certs/example.pem" | \
    socat stdio /var/run/haproxy.sock
```

---

# 三、Envoy深入排查

## 3.1 Envoy管理接口

```bash
# Envoy管理端口（默认9901）

# 查看服务器信息
curl http://localhost:9901/server_info

# 查看统计
curl http://localhost:9901/stats

# 按前缀过滤统计
curl http://localhost:9901/stats?filter=cluster

# Prometheus格式
curl http://localhost:9901/stats/prometheus

# 查看集群健康
curl http://localhost:9901/clusters

# 查看监听器
curl http://localhost:9901/listeners

# 查看配置
curl http://localhost:9901/config_dump

# 日志级别
curl -X POST "http://localhost:9901/logging?level=debug"
curl -X POST "http://localhost:9901/logging?level=info"

# 热重启
curl -X POST http://localhost:9901/hot_restart_version

# 排空连接（优雅关闭）
curl -X POST http://localhost:9901/drain_listeners
```

## 3.2 Envoy配置详解

```yaml
# envoy.yaml

admin:
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 9901

static_resources:
  listeners:
    - name: listener_http
      address:
        socket_address:
          address: 0.0.0.0
          port_value: 80
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: ingress_http
                codec_type: AUTO
                route_config:
                  name: local_route
                  virtual_hosts:
                    - name: backend
                      domains: ["*"]
                      routes:
                        - match:
                            prefix: "/api"
                          route:
                            cluster: api_service
                            timeout: 30s
                            retry_policy:
                              retry_on: "5xx,reset,connect-failure"
                              num_retries: 3
                        - match:
                            prefix: "/"
                          route:
                            cluster: web_service
                http_filters:
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router

  clusters:
    - name: web_service
      type: STRICT_DNS
      lb_policy: ROUND_ROBIN
      connect_timeout: 5s
      load_assignment:
        cluster_name: web_service
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: web1
                      port_value: 8080
              - endpoint:
                  address:
                    socket_address:
                      address: web2
                      port_value: 8080
      health_checks:
        - timeout: 5s
          interval: 10s
          unhealthy_threshold: 3
          healthy_threshold: 2
          http_health_check:
            path: "/health"
      
    - name: api_service
      type: STRICT_DNS
      lb_policy: LEAST_REQUEST
      connect_timeout: 5s
      load_assignment:
        cluster_name: api_service
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: api1
                      port_value: 8080
              - endpoint:
                  address:
                    socket_address:
                      address: api2
                      port_value: 8080
      circuit_breakers:
        thresholds:
          - max_connections: 1000
            max_pending_requests: 1000
            max_requests: 1000
            max_retries: 3
```

## 3.3 Envoy问题排查

```bash
# 检查集群健康状态
curl -s http://localhost:9901/clusters | grep health_flags

# 输出解读：
# /health_flags::healthy    - 健康
# /health_flags::failed_active_hc - 主动健康检查失败
# /health_flags::failed_outlier_check - 异常检测失败

# 查看具体统计
curl -s http://localhost:9901/stats | grep -E "upstream_cx|upstream_rq"

# 关键指标：
# cluster.*.upstream_cx_active        活跃连接
# cluster.*.upstream_cx_connect_fail  连接失败
# cluster.*.upstream_rq_total         总请求
# cluster.*.upstream_rq_5xx           5xx响应
# cluster.*.upstream_rq_retry         重试次数
# cluster.*.upstream_rq_timeout       超时次数

# 检查熔断状态
curl -s http://localhost:9901/stats | grep circuit_breakers

# 检查重试统计
curl -s http://localhost:9901/stats | grep retry

# 配置验证
envoy --mode validate -c /etc/envoy/envoy.yaml

# 调试日志
curl -X POST "http://localhost:9901/logging?upstream=debug"
curl -X POST "http://localhost:9901/logging?connection=debug"
```

---

# 四、负载均衡通用排查

## 4.1 诊断脚本

```bash
#!/bin/bash
# lb_diagnose.sh - 负载均衡诊断

LB_TYPE=$1  # nginx / haproxy / envoy

case $LB_TYPE in
    nginx)
        echo "===== Nginx负载均衡诊断 ====="
        
        echo "--- 配置检查 ---"
        nginx -t 2>&1
        
        echo "--- 状态 ---"
        curl -s http://localhost:8080/nginx_status 2>/dev/null || echo "状态页面未配置"
        
        echo "--- 错误日志 ---"
        tail -10 /var/log/nginx/error.log 2>/dev/null
        
        echo "--- Upstream配置 ---"
        nginx -T 2>/dev/null | grep -A20 "upstream"
        ;;
        
    haproxy)
        echo "===== HAProxy诊断 ====="
        
        echo "--- 配置检查 ---"
        haproxy -c -f /etc/haproxy/haproxy.cfg 2>&1
        
        echo "--- 后端状态 ---"
        echo "show stat" | socat stdio /var/run/haproxy.sock 2>/dev/null | \
            awk -F',' 'NR>1 {printf "%-30s %-10s %-10s\n", $1"/"$2, $18, $5}'
        
        echo "--- 错误 ---"
        echo "show errors" | socat stdio /var/run/haproxy.sock 2>/dev/null
        
        echo "--- 信息 ---"
        echo "show info" | socat stdio /var/run/haproxy.sock 2>/dev/null | grep -E "Curr|Max|Uptime"
        ;;
        
    envoy)
        echo "===== Envoy诊断 ====="
        
        echo "--- 服务器信息 ---"
        curl -s http://localhost:9901/server_info 2>/dev/null | head -20
        
        echo "--- 集群健康 ---"
        curl -s http://localhost:9901/clusters 2>/dev/null | grep -E "name|health"
        
        echo "--- 关键统计 ---"
        curl -s http://localhost:9901/stats 2>/dev/null | grep -E "upstream_cx_active|upstream_rq_5xx|upstream_rq_timeout"
        ;;
        
    *)
        echo "Usage: $0 <nginx|haproxy|envoy>"
        exit 1
        ;;
esac

echo ""
echo "===== 诊断完成 ====="
```

---

## 总结

### 命令速查

| LB | 状态检查 | 配置检查 |
|-----|----------|----------|
| Nginx | `curl /nginx_status` | `nginx -t` |
| HAProxy | `echo "show stat" \| socat` | `haproxy -c -f` |
| Envoy | `curl :9901/clusters` | `envoy --mode validate` |

### 常见问题速查

| 问题 | Nginx | HAProxy | Envoy |
|------|-------|---------|-------|
| 后端不健康 | 检查error.log | `show stat`看status | `/clusters`看health_flags |
| 连接超时 | 调整proxy_timeout | 调整timeout | 调整connect_timeout |
| 5xx错误 | proxy_next_upstream | option redispatch | retry_policy |

### 负载均衡排查三板斧

1. **看状态** - 后端服务器是否健康
2. **看连接** - 连接数、队列是否正常
3. **看日志** - 错误日志和访问日志

### 关键记忆

1. Nginx 502先查后端服务
2. HAProxy用socket命令管理
3. Envoy用admin接口调试
4. 健康检查参数要合理（避免抖动）
