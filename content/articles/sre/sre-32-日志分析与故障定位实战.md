+++
title = "日志分析与故障定位实战"
date = 2026-01-21
weight = 32000
description = "SRE日志分析完整指南：系统日志、应用日志、访问日志的分析方法与故障定位技巧"
[taxonomies]
tags = ["SRE", "日志", "排查", "实战", "grep", "awk"]
+++

## 概述

日志是SRE定位问题的核心依据。本文详细介绍各类日志的分析方法、常用命令和实战技巧。

---

# 一、日志分析基础

## 1.1 Linux日志体系

### 日志位置

```bash
# 系统日志
/var/log/syslog          # Debian/Ubuntu系统日志
/var/log/messages        # CentOS/RHEL系统日志
/var/log/dmesg           # 内核启动日志
/var/log/kern.log        # 内核日志
/var/log/auth.log        # 认证日志（Debian/Ubuntu）
/var/log/secure          # 认证日志（CentOS/RHEL）
/var/log/cron            # 定时任务日志
/var/log/boot.log        # 启动日志

# 应用日志
/var/log/nginx/          # Nginx日志
/var/log/apache2/        # Apache日志
/var/log/mysql/          # MySQL日志
/var/log/postgresql/     # PostgreSQL日志

# systemd日志
journalctl               # 查看systemd日志
```

### journalctl详解

```bash
# 查看所有日志
journalctl

# 实时跟踪
journalctl -f

# 参数详解：
# -f            实时跟踪（类似tail -f）
# -n 100        显示最近100行
# -r            逆序显示（最新的在前）
# -e            跳到日志末尾
# --no-pager    不使用分页器

# 按时间筛选
journalctl --since "2024-01-21 10:00:00"
journalctl --since "1 hour ago"
journalctl --since "today"
journalctl --since "yesterday" --until "today"

# 按单元筛选
journalctl -u nginx              # nginx服务
journalctl -u nginx -u mysql     # 多个服务

# 按优先级筛选
journalctl -p err                # error及以上
journalctl -p warning            # warning及以上
# 优先级：emerg(0) alert(1) crit(2) err(3) warning(4) notice(5) info(6) debug(7)

# 按进程筛选
journalctl _PID=1234
journalctl _UID=1000

# 内核日志
journalctl -k
journalctl -k -b              # 本次启动的内核日志
journalctl -k -b -1           # 上次启动的内核日志

# 输出格式
journalctl -o json            # JSON格式
journalctl -o json-pretty     # 格式化的JSON
journalctl -o verbose         # 详细格式
journalctl -o short-iso       # 带ISO时间戳

# 磁盘使用
journalctl --disk-usage

# 清理日志
journalctl --vacuum-time=7d   # 保留7天
journalctl --vacuum-size=1G   # 保留1GB
```

---

## 1.2 日志分析命令详解

### grep - 文本搜索

```bash
# 基础搜索
grep "error" /var/log/syslog

# 常用参数详解：
# -i    忽略大小写
# -v    反向匹配（不包含）
# -n    显示行号
# -c    只显示匹配行数
# -l    只显示匹配的文件名
# -L    显示不匹配的文件名
# -r    递归搜索目录
# -h    不显示文件名（多文件时）
# -o    只显示匹配的部分
# -A 3  显示匹配行及后3行（After）
# -B 3  显示匹配行及前3行（Before）
# -C 3  显示匹配行及前后各3行（Context）
# -E    扩展正则表达式（等同egrep）
# -P    Perl正则表达式
# -w    完整单词匹配
# -x    完整行匹配

# 实际示例
# 忽略大小写搜索error
grep -i "error" /var/log/syslog

# 搜索error并显示上下文
grep -C 5 "error" /var/log/syslog

# 排除某些内容
grep "error" /var/log/syslog | grep -v "expected error"

# 多个关键词（或）
grep -E "error|warning|critical" /var/log/syslog

# 多个关键词（与）- 管道组合
grep "error" /var/log/syslog | grep "connection"

# 统计匹配数量
grep -c "error" /var/log/syslog

# 只提取IP地址
grep -oE '\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b' access.log

# 搜索多个文件
grep -r "error" /var/log/

# 搜索时排除目录
grep -r "error" /var/log/ --exclude-dir=journal
```

### awk - 文本处理

```bash
# 基础语法
awk 'pattern {action}' file

# awk内置变量：
# $0    整行内容
# $1-$n 第1到第n个字段
# NF    字段数量
# NR    当前行号
# FS    字段分隔符（默认空白）
# RS    记录分隔符（默认换行）
# OFS   输出字段分隔符
# ORS   输出记录分隔符

# 打印特定列
awk '{print $1}' access.log          # 第1列
awk '{print $1, $4}' access.log      # 第1和第4列
awk '{print $NF}' access.log         # 最后一列
awk '{print $(NF-1)}' access.log     # 倒数第2列

# 指定分隔符
awk -F: '{print $1}' /etc/passwd     # 冒号分隔
awk -F'[,:]' '{print $1}' file       # 多分隔符

# 条件过滤
awk '$9 >= 500' access.log           # 状态码>=500
awk '$10 > 1000000' access.log       # 响应大小>1MB
awk 'NR > 10' file                   # 跳过前10行
awk '/error/' file                   # 包含error的行

# 统计计算
awk '{sum += $10} END {print sum}' access.log      # 求和
awk '{sum += $10} END {print sum/NR}' access.log   # 平均值
awk 'BEGIN {max=0} $10>max {max=$10} END {print max}' access.log  # 最大值

# 分组统计
awk '{count[$1]++} END {for(ip in count) print count[ip], ip}' access.log | sort -rn

# 多条件
awk '$9==500 && $7~/api/' access.log

# 格式化输出
awk '{printf "%-15s %s\n", $1, $7}' access.log
```

### sed - 流编辑器

```bash
# 基础语法
sed 's/old/new/' file        # 替换（每行第一个）
sed 's/old/new/g' file       # 替换（全局）

# 常用参数：
# -i    原地修改文件
# -n    静默模式
# -e    多个命令
# -r    扩展正则

# 删除行
sed '/pattern/d' file        # 删除匹配行
sed '1,10d' file             # 删除1-10行
sed '/^$/d' file             # 删除空行
sed '/^#/d' file             # 删除注释行

# 打印特定行
sed -n '10p' file            # 打印第10行
sed -n '10,20p' file         # 打印10-20行
sed -n '/error/p' file       # 打印匹配行

# 替换示例
sed 's/foo/bar/g' file                    # 全局替换
sed 's/[0-9]\+/NUMBER/g' file             # 正则替换
sed 's/\(.*\):\(.*\)/\2:\1/' file         # 反向引用

# 多命令
sed -e 's/foo/bar/g' -e 's/baz/qux/g' file
```

### sort和uniq - 排序去重

```bash
# sort参数详解：
# -n    按数字排序
# -r    逆序
# -k    按指定列排序
# -t    指定分隔符
# -u    去重
# -h    按人类可读数字排序（1K, 2M, 3G）
# -V    版本号排序

# 示例
sort -n file                 # 数字排序
sort -rn file                # 逆序数字排序
sort -t: -k3 -n /etc/passwd  # 按第3列数字排序，冒号分隔
sort -k1,1 -k2,2n file       # 先按第1列字符排序，再按第2列数字排序

# uniq参数详解：
# -c    计数
# -d    只显示重复行
# -u    只显示不重复行
# -i    忽略大小写

# 统计词频（经典组合）
sort file | uniq -c | sort -rn

# 统计IP访问次数
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10
```

---

# 二、Web服务器日志分析

## 2.1 Nginx日志分析

### 日志格式解读

```bash
# 默认combined格式
# $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
# 示例：
# 192.168.1.1 - - [21/Jan/2024:10:00:00 +0800] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0..."

# 字段位置：
# $1  - IP地址
# $4  - 时间（带方括号）
# $6  - HTTP方法
# $7  - 请求路径
# $9  - 状态码
# $10 - 响应大小
# $11 - Referer
# $12+ - User-Agent
```

### 常见分析命令

```bash
# 1. 统计访问量最高的IP
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# 2. 统计状态码分布
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 3. 统计访问最多的URL
awk '{print $7}' access.log | sort | uniq -c | sort -rn | head -20

# 4. 统计每小时请求数
awk '{print substr($4, 14, 2)}' access.log | sort | uniq -c
# 解释：substr($4, 14, 2) 从时间字段提取小时

# 5. 统计5xx错误
awk '$9 >= 500' access.log | awk '{print $7}' | sort | uniq -c | sort -rn | head -10

# 6. 计算平均响应大小
awk '{sum += $10; count++} END {print sum/count}' access.log

# 7. 找出慢请求（假设最后一列是响应时间）
awk '$NF > 1' access.log | head -20

# 8. 按小时统计5xx错误
awk '$9 >= 500 {print substr($4, 14, 2)}' access.log | sort | uniq -c

# 9. 实时监控4xx/5xx错误
tail -f access.log | awk '$9 >= 400 {print}'

# 10. 统计特定时间段的访问
awk '$4 >= "[21/Jan/2024:10:00" && $4 < "[21/Jan/2024:11:00"' access.log | wc -l
```

### 高级分析

```bash
# 带宽统计（按小时）
awk '{
    hour = substr($4, 14, 2)
    bytes[hour] += $10
} END {
    for (h in bytes) printf "%s:00 - %.2f MB\n", h, bytes[h]/1024/1024
}' access.log | sort

# 响应时间百分位（假设响应时间在最后一列）
awk '{print $NF}' access.log | sort -n | awk '
    {a[NR]=$1}
    END {
        print "P50:", a[int(NR*0.5)]
        print "P90:", a[int(NR*0.9)]
        print "P99:", a[int(NR*0.99)]
    }
'

# 按IP和URL统计
awk '{key = $1" "$7; count[key]++} END {for(k in count) print count[k], k}' access.log | sort -rn | head -20

# 检测爬虫/攻击
awk '{print $1}' access.log | sort | uniq -c | sort -rn | awk '$1 > 1000'
```

---

## 2.2 错误日志分析

```bash
# Nginx错误日志格式
# 2024/01/21 10:00:00 [error] 1234#1234: *5678 message

# 按错误级别统计
grep -oE '\[(emerg|alert|crit|error|warn|notice|info)\]' error.log | sort | uniq -c

# 提取错误类型
awk -F'[][]' '{print $2}' error.log | sort | uniq -c | sort -rn

# 统计上游错误
grep "upstream" error.log | grep -oE 'upstream: "[^"]*"' | sort | uniq -c | sort -rn

# 最近的错误
tail -100 error.log | grep -E '\[error\]|\[crit\]'

# 按小时统计错误数
awk '{print $2}' error.log | cut -d: -f1 | sort | uniq -c
```

---

# 三、应用日志分析

## 3.1 JSON格式日志

```bash
# 使用jq解析JSON日志
cat app.log | jq '.'

# jq常用操作：
# .             整个对象
# .field        获取字段
# .field.sub    嵌套字段
# .[]           数组元素
# select(cond)  条件过滤
# keys          获取所有键
# length        长度/数量

# 提取特定字段
cat app.log | jq -r '.timestamp, .level, .message'

# 过滤特定级别
cat app.log | jq 'select(.level == "error")'

# 按条件过滤
cat app.log | jq 'select(.response_time > 1000)'

# 统计错误类型
cat app.log | jq -r 'select(.level == "error") | .error_type' | sort | uniq -c

# 实时监控错误
tail -f app.log | jq 'select(.level == "error")'

# 没有jq时的替代方案
grep '"level":"error"' app.log
grep -o '"message":"[^"]*"' app.log
```

## 3.2 Java应用日志

### 日志格式

```bash
# 常见格式
# 2024-01-21 10:00:00.123 [thread-1] ERROR c.e.MyClass - Error message
# java.lang.NullPointerException: null
#     at com.example.MyClass.method(MyClass.java:123)
#     at com.example.OtherClass.call(OtherClass.java:456)
```

### 分析命令

```bash
# 按日志级别统计
grep -oE '\b(TRACE|DEBUG|INFO|WARN|ERROR|FATAL)\b' app.log | sort | uniq -c

# 提取异常堆栈
grep -A 20 "Exception" app.log | head -50

# 统计异常类型
grep -oE '[A-Za-z]+Exception' app.log | sort | uniq -c | sort -rn

# 查找特定异常
grep -B 5 -A 20 "NullPointerException" app.log

# 统计每分钟错误数
grep "ERROR" app.log | awk '{print $1, substr($2, 1, 5)}' | sort | uniq -c

# 查找GC日志
grep -E "GC|gc" app.log

# 查找OOM
grep -i "OutOfMemory" app.log
```

## 3.3 多行日志处理

```bash
# 合并多行（异常堆栈）
awk '/^[0-9]{4}-[0-9]{2}-[0-9]{2}/ {if(buf) print buf; buf=$0; next} {buf=buf" "$0} END {print buf}' app.log

# 使用sed合并
sed -N '/^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/!{H;d};x;s/\n/ /g;p' app.log

# 提取完整的异常（从Exception到空行）
awk '/Exception/{p=1} p; /^$/{p=0}' app.log
```

---

# 四、系统日志分析

## 4.1 认证日志

```bash
# 查看登录失败
grep "Failed password" /var/log/auth.log

# 统计失败登录的IP
grep "Failed password" /var/log/auth.log | grep -oE '\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b' | sort | uniq -c | sort -rn

# 统计失败登录的用户
grep "Failed password" /var/log/auth.log | grep -oE 'for [^ ]+' | sort | uniq -c | sort -rn

# 查看成功登录
grep "Accepted" /var/log/auth.log

# 查看sudo使用
grep "sudo" /var/log/auth.log

# 查看用户切换
grep "su:" /var/log/auth.log
```

## 4.2 内核日志

```bash
# 查看最近的内核日志
dmesg | tail -100

# dmesg参数：
# -T    显示人类可读时间戳
# -H    人类可读格式
# -w    实时跟踪
# -l    按级别过滤

# 按级别查看
dmesg -l err           # 错误
dmesg -l warn          # 警告
dmesg -l err,warn      # 多级别

# 搜索特定问题
dmesg | grep -i "error\|fail\|oom\|kill"

# 网络相关
dmesg | grep -i "eth\|network\|link"

# 磁盘相关
dmesg | grep -i "sda\|disk\|ata\|scsi"

# 内存相关
dmesg | grep -i "memory\|oom\|swap"

# 硬件错误
dmesg | grep -i "hardware error\|mce\|machine check"
```

## 4.3 Cron日志

```bash
# 查看cron执行日志
grep CRON /var/log/syslog

# CentOS/RHEL
cat /var/log/cron

# 查看特定任务
grep "my_script" /var/log/syslog

# 查看执行失败的任务
grep CRON /var/log/syslog | grep -v "CRON\[.*\]: (.*) CMD"

# 统计每个用户的cron执行次数
grep CRON /var/log/syslog | grep -oE '\(([^)]+)\)' | sort | uniq -c | sort -rn
```

---

# 五、日志故障排查实战

## 5.1 场景：服务异常，从日志定位问题

```bash
# 步骤1：确定问题发生时间
# 从监控告警获取时间点，例如 10:30

# 步骤2：查看该时间段的错误日志
journalctl --since "10:25" --until "10:35" -p err

# 步骤3：查看特定服务日志
journalctl -u nginx --since "10:25" --until "10:35"

# 步骤4：查看系统事件
dmesg -T | grep -E "$(date +%b\ %d\ 10:2)|$(date +%b\ %d\ 10:3)"

# 步骤5：关联分析多个日志
# 同时打开多个终端，或使用tmux

# 终端1
tail -f /var/log/nginx/error.log

# 终端2
journalctl -f -u nginx

# 终端3
dmesg -wT
```

## 5.2 场景：找出错误原因

```bash
# 方法1：时间线分析
# 找到第一个错误
grep -m1 "error" /var/log/app.log

# 查看这个错误之前发生了什么
grep -B 50 -m1 "error" /var/log/app.log

# 方法2：关联ID追踪（如trace_id）
grep "trace_id=abc123" /var/log/*.log

# 方法3：进程ID追踪
grep "pid=1234" /var/log/*.log

# 方法4：用户追踪
grep "user_id=5678" /var/log/*.log
```

## 5.3 实时监控脚本

```bash
#!/bin/bash
# log_monitor.sh - 日志实时监控

LOG_FILE=${1:-"/var/log/syslog"}
PATTERNS="error|fail|critical|exception|oom|killed"

echo "Monitoring $LOG_FILE for: $PATTERNS"
echo "Press Ctrl+C to stop"
echo "---"

tail -f "$LOG_FILE" | while read line; do
    if echo "$line" | grep -qiE "$PATTERNS"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT:"
        echo "$line"
        echo "---"
    fi
done
```

---

# 六、日志管理

## 6.1 日志轮转

```bash
# logrotate配置
cat /etc/logrotate.d/nginx

# 示例配置
/var/log/nginx/*.log {
    daily              # 每天轮转
    rotate 14          # 保留14份
    compress           # 压缩
    delaycompress      # 延迟一个周期压缩
    missingok          # 文件不存在不报错
    notifempty         # 空文件不轮转
    create 0640 www-data adm    # 新文件权限
    sharedscripts      # 所有日志轮转后执行一次脚本
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
    endscript
}

# 手动执行轮转
logrotate -f /etc/logrotate.d/nginx

# 调试模式
logrotate -d /etc/logrotate.d/nginx
```

## 6.2 日志清理

```bash
# 清理老日志
find /var/log -name "*.log.*" -mtime +30 -delete
find /var/log -name "*.gz" -mtime +30 -delete

# 清空但不删除（保持文件描述符）
truncate -s 0 /var/log/large.log
# 或
cat /dev/null > /var/log/large.log

# 定时清理脚本
cat > /etc/cron.daily/log-cleanup << 'EOF'
#!/bin/bash
find /var/log -name "*.log.*" -mtime +30 -delete
find /var/log -name "*.gz" -mtime +30 -delete
journalctl --vacuum-time=7d
EOF
chmod +x /etc/cron.daily/log-cleanup
```

---

## 总结

| 任务 | 常用命令 |
|------|----------|
| 搜索关键词 | `grep -i "error" file` |
| 显示上下文 | `grep -C 5 "error" file` |
| 统计次数 | `grep -c "error" file` |
| 提取字段 | `awk '{print $1}' file` |
| 统计TOP N | `awk '{print $1}' file \| sort \| uniq -c \| sort -rn \| head` |
| 时间筛选 | `journalctl --since "1 hour ago"` |
| 实时跟踪 | `tail -f file` 或 `journalctl -f` |
| JSON解析 | `jq '.field' file` |

**排查三板斧**：
1. **grep** - 快速定位关键词
2. **awk** - 字段提取和统计
3. **journalctl** - systemd日志查询

**日志分析原则**：
1. 先确定时间范围，缩小搜索范围
2. 找到第一个错误，向前追溯原因
3. 使用trace_id/request_id关联多个日志
4. 多个日志源交叉验证

---

## 相关文章

- [上一篇：进程与服务问题排查实战](@/articles/sre/sre-31-进程与服务问题排查实战.md)
- [下一篇：容器问题排查实战](@/articles/sre/sre-33-容器问题排查实战.md)
