+++
title = "15.DNS详解"
date = 2026-01-19
description = "DNS深入解析：解析原理、记录类型、DNS架构、性能优化、安全防护"
[taxonomies]
tags = ["网络", "DNS", "协议"]
+++

## DNS基础

### DNS的作用

**Domain Name System**：将人类可读的域名转换为IP地址。

```
www.example.com → 93.184.216.34
```

**为什么需要DNS**：
- IP地址难以记忆
- IP可能变化，域名保持不变
- 支持负载均衡、故障转移

### DNS查询过程

**递归查询**：
```
客户端 → 本地DNS → 根DNS → 顶级域DNS → 权威DNS
                                            ↓
客户端 ← 本地DNS ←←←←←←←←←←←←←←←←←←←←←←←←← 结果
```

**详细步骤**：
1. 客户端查询本地DNS服务器
2. 本地DNS查询根服务器（返回顶级域服务器）
3. 本地DNS查询顶级域服务器（返回权威服务器）
4. 本地DNS查询权威服务器（返回IP地址）
5. 本地DNS缓存并返回给客户端

### DNS缓存层次

```
浏览器缓存
    ↓ 未命中
操作系统缓存
    ↓ 未命中
本地DNS服务器缓存
    ↓ 未命中
递归查询
```

---

## DNS记录类型

### 常见记录

| 类型 | 功能 | 示例 |
|------|------|------|
| A | 域名→IPv4 | example.com → 93.184.216.34 |
| AAAA | 域名→IPv6 | example.com → 2606:2800:220:1:... |
| CNAME | 别名 | www.example.com → example.com |
| MX | 邮件服务器 | example.com → mail.example.com |
| NS | 域名服务器 | example.com → ns1.example.com |
| TXT | 文本记录 | 用于SPF、DKIM等验证 |
| SOA | 起始授权 | 区域元数据 |
| PTR | IP→域名（反向解析） | 34.216.184.93 → example.com |
| SRV | 服务定位 | _http._tcp.example.com |
| CAA | 证书授权 | 限制可签发证书的CA |

### 记录示例

**A记录**：
```
example.com.    300    IN    A    93.184.216.34
```

**CNAME记录**：
```
www.example.com.    300    IN    CNAME    example.com.
```

**MX记录**：
```
example.com.    300    IN    MX    10    mail1.example.com.
example.com.    300    IN    MX    20    mail2.example.com.
```
数字越小优先级越高。

**TXT记录**：
```
example.com.    300    IN    TXT    "v=spf1 include:_spf.google.com ~all"
```

---

## DNS架构

### 域名层次

```
根域 (.)
  ├── com
  │   ├── example
  │   │   ├── www
  │   │   └── mail
  │   └── google
  ├── org
  ├── net
  └── cn
      └── com
          └── example
```

### DNS服务器类型

**根服务器**：
- 全球13组（A-M）
- 使用Anycast分布在数百个节点
- 返回顶级域服务器地址

**顶级域服务器（TLD）**：
- 管理.com、.org、.cn等
- 返回权威服务器地址

**权威服务器**：
- 管理具体域名
- 返回最终记录

**递归解析器**：
- 代理客户端查询
- 缓存结果
- 如：8.8.8.8、114.114.114.114

### 区域与区域传送

**区域（Zone）**：DNS管理的单位

**区域传送（Zone Transfer）**：
- AXFR：全量传送
- IXFR：增量传送
- 主DNS → 从DNS同步数据

---

## DNS高可用

### 多DNS服务器

```
主DNS服务器 (Master)
    ↓ 区域传送
从DNS服务器1 (Slave)
从DNS服务器2 (Slave)
```

**配置多个NS记录**：
```
example.com.    IN    NS    ns1.example.com.
example.com.    IN    NS    ns2.example.com.
```

### Anycast

**同一IP地址部署在多个地点**：
- 路由协议自动选择最近节点
- 根服务器和大型DNS使用
- 天然的DDoS防护

### 智能DNS

**根据用户位置返回不同IP**：
```
北京用户 → 北京服务器IP
上海用户 → 上海服务器IP
```

**实现方式**：
- 基于EDNS Client Subnet
- 基于请求来源IP

---

## DNS性能优化

### TTL优化

**TTL（Time To Live）**：记录缓存时间

| 场景 | 建议TTL |
|------|---------|
| 稳定服务 | 3600-86400秒 |
| 需要快速切换 | 60-300秒 |
| 故障切换 | 30-60秒 |

**权衡**：
- TTL长：减少查询，降低延迟
- TTL短：快速生效，但增加查询

### 预解析

**浏览器DNS预解析**：
```html
<link rel="dns-prefetch" href="//cdn.example.com">
<link rel="preconnect" href="https://api.example.com">
```

### 本地DNS选择

**选择快速的DNS**：
- 8.8.8.8（Google）
- 1.1.1.1（Cloudflare）
- 114.114.114.114（国内）
- 运营商DNS

**测试DNS性能**：
```bash
dig @8.8.8.8 example.com +stats
```

---

## DNS安全

### DNS劫持

**攻击方式**：
- 修改本地hosts
- 修改路由器DNS设置
- 运营商DNS劫持
- DNS服务器被入侵

**防护**：
- 使用可信DNS
- DNSSEC
- DoH/DoT

### DNS放大攻击

**原理**：
```
攻击者(伪造源IP为受害者) → DNS服务器
DNS服务器(大量响应) → 受害者
```

**防护**：
- 限制开放递归
- 响应速率限制（RRL）
- 禁用ANY查询

### DNSSEC

**DNS Security Extensions**：为DNS响应签名

```
区域签名：私钥签名DNS记录
验证：递归服务器用公钥验证
```

**记录类型**：
- DNSKEY：公钥
- RRSIG：签名
- DS：委派签名
- NSEC/NSEC3：否定响应

### DoH/DoT

**DNS over HTTPS (DoH)**：
- DNS查询封装在HTTPS中
- 端口443
- 隐私保护

**DNS over TLS (DoT)**：
- DNS查询使用TLS加密
- 端口853

---

## DNS工具

### dig

```bash
# 基本查询
dig example.com

# 指定类型
dig example.com MX
dig example.com AAAA

# 指定DNS服务器
dig @8.8.8.8 example.com

# 追踪解析过程
dig +trace example.com

# 反向解析
dig -x 8.8.8.8

# 简洁输出
dig +short example.com
```

### nslookup

```bash
nslookup example.com
nslookup -type=MX example.com
nslookup example.com 8.8.8.8
```

### host

```bash
host example.com
host -t MX example.com
```

### 本地DNS缓存

```bash
# Linux (systemd-resolved)
resolvectl flush-caches

# macOS
sudo dscacheutil -flushcache

# Windows
ipconfig /flushdns
```

---

## 企业DNS架构

### 内外网分离

```
外部DNS（公网）
  ├── www.example.com → 公网IP
  └── api.example.com → 公网IP

内部DNS（私网）
  ├── www.example.com → 内网IP
  ├── db.internal → 数据库IP
  └── *.internal → 内部服务
```

### 私有DNS

**Kubernetes CoreDNS**：
```
service.namespace.svc.cluster.local → ClusterIP
```

**云服务私有DNS**：
- AWS Route 53 Private Hosted Zone
- 阿里云PrivateZone

### DNS监控

**监控指标**：
- 查询量（QPS）
- 响应时间
- 解析成功率
- 缓存命中率

**告警项**：
- DNS解析失败
- 解析时间过长
- 异常查询模式

---

## 总结

| 要点 | 说明 |
|------|------|
| 解析流程 | 递归查询，多级缓存 |
| 记录类型 | A、AAAA、CNAME、MX、TXT等 |
| 高可用 | 多服务器、Anycast |
| 性能 | 合理TTL、预解析 |
| 安全 | DNSSEC、DoH/DoT |

DNS是互联网的基础设施，其可用性直接影响所有网络服务。理解DNS原理对于网络运维和故障排查非常重要。

---

## 相关文章

- [上一篇：HTTP协议详解](/articles/networking/net-14-HTTP协议详解/)
- [下一篇：网络安全基础](/articles/networking/net-16-网络安全基础/)
