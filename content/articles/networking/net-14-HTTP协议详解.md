+++
title = "14. HTTP协议详解"
date = 2026-01-19
weight = 14000
description = "HTTP协议全解析：HTTP/1.1、HTTP/2、HTTP/3、HTTPS、缓存机制、性能优化"
[taxonomies]
tags = ["网络", "HTTP", "协议"]
+++

## HTTP基础

### HTTP概述

**HyperText Transfer Protocol**：应用层协议，Web通信的基础。

**特点**：
- 无状态（每次请求独立）
- 基于请求-响应模型
- 文本协议（HTTP/1.x）或二进制（HTTP/2+）
- 通常基于TCP（HTTP/3基于QUIC/UDP）

### 请求与响应

**请求格式**：
```
GET /api/users HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0
Accept: application/json
Authorization: Bearer token123

{请求体}
```

**响应格式**：
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 123
Cache-Control: max-age=3600

{"users": [...]}
```

### HTTP方法

| 方法 | 语义 | 幂等 | 安全 |
|------|------|------|------|
| GET | 获取资源 | ✓ | ✓ |
| HEAD | 获取头部 | ✓ | ✓ |
| POST | 创建资源 | ✗ | ✗ |
| PUT | 替换资源 | ✓ | ✗ |
| PATCH | 部分更新 | ✗ | ✗ |
| DELETE | 删除资源 | ✓ | ✗ |
| OPTIONS | 查询支持的方法 | ✓ | ✓ |

### 状态码

| 范围 | 类别 | 常见状态码 |
|------|------|-----------|
| 1xx | 信息 | 100 Continue, 101 Switching Protocols |
| 2xx | 成功 | 200 OK, 201 Created, 204 No Content |
| 3xx | 重定向 | 301 永久, 302 临时, 304 Not Modified |
| 4xx | 客户端错误 | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| 5xx | 服务端错误 | 500 Internal Error, 502 Bad Gateway, 503 Service Unavailable |

---

## HTTP/1.1

### 持久连接

**HTTP/1.0**：每个请求新建连接
**HTTP/1.1**：默认Keep-Alive，连接复用

```
Connection: keep-alive
Keep-Alive: timeout=5, max=100
```

### 管道化（Pipelining）

多个请求无需等待响应即可发送：
```
请求1 → 请求2 → 请求3 →
                        ← 响应1 ← 响应2 ← 响应3
```

**问题**：队头阻塞（响应必须按序返回）

### 分块传输

动态内容，不知道Content-Length时使用：
```
Transfer-Encoding: chunked

7\r\n
Mozilla\r\n
9\r\n
Developer\r\n
0\r\n
\r\n
```

### HTTP/1.1局限

- **队头阻塞**：前一个请求阻塞后续请求
- **头部冗余**：每次请求重复发送相同头部
- **单向请求**：服务端无法主动推送
- **明文传输**：头部未压缩

---

## HTTP/2

### 核心改进

**二进制分帧**：
```
HTTP/1.1: 文本协议
HTTP/2:   二进制帧
```

**多路复用**：
```
单一连接内多个并行流
Stream 1: 请求A
Stream 2: 请求B  ← 不再队头阻塞
Stream 3: 请求C
```

**头部压缩（HPACK）**：
- 静态表：常见头部字段
- 动态表：连接内复用的头部
- 霍夫曼编码

**服务端推送**：
```
客户端请求index.html
服务端推送style.css和script.js
```

### HTTP/2帧类型

| 帧类型 | 功能 |
|--------|------|
| DATA | 传输请求/响应体 |
| HEADERS | 传输头部 |
| PRIORITY | 设置流优先级 |
| RST_STREAM | 终止流 |
| SETTINGS | 连接设置 |
| PUSH_PROMISE | 服务端推送预告 |
| PING | 心跳检测 |
| GOAWAY | 关闭连接 |

### HTTP/2局限

- **TCP队头阻塞**：底层TCP丢包仍会阻塞
- **握手延迟**：TCP+TLS握手开销
- **连接中断**：IP变化需重建连接

---

## HTTP/3与QUIC

### HTTP/3特点

**基于QUIC（UDP）**：
- 无TCP队头阻塞
- 0-RTT连接建立
- 连接迁移
- 内置TLS 1.3

### HTTP/3 vs HTTP/2

| 特性 | HTTP/2 | HTTP/3 |
|------|--------|--------|
| 传输层 | TCP | QUIC(UDP) |
| 队头阻塞 | TCP层存在 | 无 |
| 握手延迟 | 2-3 RTT | 0-1 RTT |
| 连接迁移 | 不支持 | 支持 |
| 加密 | 可选TLS | 强制TLS 1.3 |

### 部署现状

- Google服务：全面支持
- CDN厂商：Cloudflare、Fastly等支持
- 浏览器：Chrome、Firefox、Safari支持
- 服务器：nginx、Caddy等支持

---

## HTTPS

### TLS握手

**TLS 1.2（2-RTT）**：
```
客户端                          服务端
  |  -- ClientHello ---------->  |
  |  <-- ServerHello -----------  |
  |  <-- Certificate -----------  |
  |  <-- ServerHelloDone -------  |
  |  -- ClientKeyExchange ----->  |
  |  -- ChangeCipherSpec ------>  |
  |  -- Finished -------------->  |
  |  <-- ChangeCipherSpec ------  |
  |  <-- Finished --------------  |
  |  -- 加密通信 -------------->  |
```

**TLS 1.3（1-RTT）**：
```
客户端                          服务端
  |  -- ClientHello+KeyShare -->  |
  |  <-- ServerHello+KeyShare --  |
  |  <-- EncryptedExtensions ---  |
  |  <-- Certificate -----------  |
  |  <-- Finished --------------  |
  |  -- Finished -------------->  |
  |  -- 加密通信 -------------->  |
```

### 证书验证

**证书链**：
```
根证书（CA）
  ↓ 签发
中间证书
  ↓ 签发
服务器证书
```

**验证过程**：
1. 检查证书是否过期
2. 检查证书域名是否匹配
3. 检查证书链是否可信
4. 检查是否被吊销（CRL/OCSP）

### HTTPS优化

**会话复用**：
- Session ID
- Session Ticket
- TLS 1.3 0-RTT

**证书优化**：
- OCSP Stapling（服务端缓存OCSP响应）
- 证书压缩

**协议优化**：
- 使用TLS 1.3
- 使用HTTP/2或HTTP/3
- HSTS预加载

---

## 缓存机制

### 缓存控制头

**Cache-Control**：
```
# 公共缓存，1小时
Cache-Control: public, max-age=3600

# 私有缓存，需验证
Cache-Control: private, no-cache

# 不缓存
Cache-Control: no-store
```

**常见指令**：

| 指令 | 含义 |
|------|------|
| public | 可被共享缓存存储 |
| private | 仅限私有缓存 |
| max-age=N | 缓存有效期（秒） |
| no-cache | 需要验证后使用 |
| no-store | 不允许缓存 |
| must-revalidate | 过期后必须验证 |

### 条件请求

**基于时间**：
```
# 响应
Last-Modified: Wed, 21 Oct 2025 07:28:00 GMT

# 请求
If-Modified-Since: Wed, 21 Oct 2025 07:28:00 GMT

# 未修改返回304
```

**基于内容**：
```
# 响应
ETag: "33a64df551425fcc55e4d42a148795d9"

# 请求
If-None-Match: "33a64df551425fcc55e4d42a148795d9"

# 未修改返回304
```

### 缓存策略

**静态资源**：
```
# 长期缓存 + 文件名带版本
Cache-Control: public, max-age=31536000, immutable
```

**动态内容**：
```
# 每次验证
Cache-Control: no-cache

# 或短期缓存
Cache-Control: private, max-age=60
```

---

## HTTP性能优化

### 减少请求

- **资源合并**：CSS/JS打包
- **雪碧图**：多图合一
- **内联小资源**：Data URI
- **按需加载**：懒加载

### 减少传输

- **压缩**：Gzip、Brotli
- **图片优化**：WebP、AVIF
- **代码精简**：Minify

### 加速传输

- **CDN**：就近访问
- **HTTP/2**：多路复用
- **HTTP/3**：0-RTT
- **预连接**：`<link rel="preconnect">`

### 优化缓存

- **合理的Cache-Control**
- **长期缓存 + 版本化文件名**
- **Service Worker缓存**

---

## 总结

| 版本 | 特点 | 适用场景 |
|------|------|----------|
| HTTP/1.1 | 持久连接 | 传统Web |
| HTTP/2 | 多路复用、头部压缩 | 现代Web |
| HTTP/3 | 基于QUIC、无队头阻塞 | 移动网络、高延迟 |
| HTTPS | 加密传输 | 必须使用 |

HTTP协议是Web开发的基础，理解其工作原理对于性能优化和问题排查至关重要。

---

## 相关文章

- [上一篇：高性能网络架构](@/articles/networking/net-13-高性能网络架构.md)
- [下一篇：DNS详解](@/articles/networking/net-15-DNS详解.md)
