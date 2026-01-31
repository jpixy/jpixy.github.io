+++
title = "21.SRE笔试题-Shell脚本速查"
date = 2026-01-21
description = "SRE面试Shell脚本常见题目速查：日志分析、进程管理、文本处理、系统监控，核心命令与要点"
[taxonomies]
tags = ["SRE", "面试", "Shell", "笔试", "Bash"]
+++

## 概述

Shell脚本笔试通常考察：文本处理（awk/sed/grep）、日志分析、进程管理、系统监控。本文列出常见题目和核心解法。

---

## 一、日志分析类

### 1. 统计Top 10 IP

**题目**：从Nginx日志统计访问量最多的10个IP

**核心命令**：
```bash
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10
```

**要点**：
- `awk '{print $1}'` 提取第一列（IP）
- `sort | uniq -c` 排序后统计
- `sort -rn` 按数字逆序
- `head -10` 取前10

---

### 2. 统计HTTP状态码分布

**题目**：统计各状态码出现次数

**核心命令**：
```bash
awk '{print $9}' access.log | sort | uniq -c | sort -rn
```

**要点**：`$9` 是Nginx默认日志格式中状态码的位置

---

### 3. 统计指定时间段的请求

**题目**：统计10:00-11:00之间的请求数

**核心命令**：
```bash
awk '$4 >= "[21/Jan/2026:10:00" && $4 < "[21/Jan/2026:11:00"' access.log | wc -l
```

**或使用grep**：
```bash
grep "21/Jan/2026:10:" access.log | wc -l
```

---

### 4. 查找慢请求

**题目**：找出响应时间超过1秒的请求

**核心命令**（假设响应时间在最后一列）：
```bash
awk '$NF > 1' access.log
```

**要点**：`$NF` 表示最后一列

---

### 5. 统计每分钟请求数（QPS趋势）

**核心命令**：
```bash
awk '{print substr($4,2,17)}' access.log | uniq -c
```

**要点**：`substr($4,2,17)` 提取时间到分钟

---

## 二、文本处理类

### 6. 提取特定字段

**题目**：从CSV提取第2和第4列

```bash
cut -d',' -f2,4 file.csv
# 或
awk -F',' '{print $2,$4}' file.csv
```

---

### 7. 替换文件内容

**题目**：将所有`foo`替换为`bar`

```bash
# 原地替换
sed -i 's/foo/bar/g' file.txt

# macOS需要
sed -i '' 's/foo/bar/g' file.txt
```

**要点**：`g` 表示全局替换

---

### 8. 删除空行和注释行

```bash
grep -v '^#' file | grep -v '^$'
# 或
sed '/^#/d; /^$/d' file
```

---

### 9. 提取两个标记之间的内容

**题目**：提取`<start>`和`<end>`之间的内容

```bash
sed -n '/<start>/,/<end>/p' file
```

---

### 10. JSON字段提取（无jq时）

```bash
# 提取 "name": "value" 中的value
grep -o '"name":"[^"]*"' file | cut -d'"' -f4
```

**推荐用jq**：
```bash
jq -r '.name' file.json
```

---

## 三、进程管理类

### 11. 查找并杀死进程

```bash
# 按名称杀
pkill -f "process_name"

# 先查后杀（更安全）
ps aux | grep "process_name" | grep -v grep | awk '{print $2}' | xargs kill
```

---

### 12. 查找占用端口的进程

```bash
lsof -i :8080
# 或
netstat -tlnp | grep 8080
# 或
ss -tlnp | grep 8080
```

---

### 13. 查找高CPU/内存进程

```bash
# Top 5 CPU
ps aux --sort=-%cpu | head -6

# Top 5 内存
ps aux --sort=-%mem | head -6
```

---

### 14. 后台运行并记录日志

```bash
nohup ./script.sh > output.log 2>&1 &

# 或使用screen/tmux
screen -dmS myprocess ./script.sh
```

---

### 15. 检查进程是否存在

```bash
if pgrep -f "process_name" > /dev/null; then
    echo "Running"
else
    echo "Not running"
fi
```

---

## 四、系统监控类

### 16. 磁盘使用率告警

```bash
df -h | awk '$5+0 > 80 {print "Warning: "$6" is "$5" full"}'
```

**要点**：`$5+0` 强制转为数字

---

### 17. 检查服务状态

```bash
#!/bin/bash
services=("nginx" "mysql" "redis")
for svc in "${services[@]}"; do
    if systemctl is-active --quiet $svc; then
        echo "$svc: OK"
    else
        echo "$svc: FAILED"
    fi
done
```

---

### 18. 监控文件变化

```bash
# 使用inotifywait
inotifywait -m /var/log/syslog -e modify |
while read path action file; do
    echo "File changed: $file"
done
```

---

### 19. 定时检查URL可用性

```bash
#!/bin/bash
url="http://example.com/health"
status=$(curl -s -o /dev/null -w "%{http_code}" $url)
if [ "$status" != "200" ]; then
    echo "Alert: $url returned $status"
fi
```

---

### 20. 获取系统负载

```bash
# 提取1分钟负载
uptime | awk -F'load average:' '{print $2}' | cut -d',' -f1

# 或直接读/proc
cat /proc/loadavg | awk '{print $1}'
```

---

## 五、文件操作类

### 21. 查找大文件

```bash
find / -type f -size +100M 2>/dev/null | head -20
```

---

### 22. 查找最近修改的文件

```bash
# 最近24小时修改的文件
find /var/log -type f -mtime -1

# 最近1小时
find /var/log -type f -mmin -60
```

---

### 23. 批量重命名

```bash
# 将 .txt 改为 .bak
for f in *.txt; do mv "$f" "${f%.txt}.bak"; done
```

---

### 24. 统计目录大小

```bash
du -sh /var/* | sort -rh | head -10
```

---

### 25. 比较两个文件差异

```bash
diff file1 file2
# 并排显示
diff -y file1 file2
# 只显示不同的行
comm -3 <(sort file1) <(sort file2)
```

---

## 六、网络类

### 26. 测试端口连通性

```bash
# 使用nc
nc -zv host 80

# 使用timeout限制
timeout 3 bash -c "</dev/tcp/host/80" && echo "OK" || echo "FAIL"
```

---

### 27. 抓取网页内容

```bash
curl -s http://example.com | grep "pattern"

# 带超时和重试
curl -s --connect-timeout 5 --retry 3 http://example.com
```

---

### 28. 统计TCP连接状态

```bash
ss -ant | awk 'NR>1 {print $1}' | sort | uniq -c
# 或
netstat -ant | awk 'NR>2 {print $6}' | sort | uniq -c
```

---

### 29. 查找ESTABLISHED连接最多的IP

```bash
ss -ant | grep ESTAB | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head
```

---

## 七、综合脚本

### 30. 日志轮转脚本

```bash
#!/bin/bash
log_dir="/var/log/myapp"
max_days=7

find $log_dir -name "*.log" -mtime +$max_days -delete
find $log_dir -name "*.log" -size +100M -exec gzip {} \;
```

---

### 31. 服务重启脚本（带重试）

```bash
#!/bin/bash
service=$1
max_retries=3
retry=0

while [ $retry -lt $max_retries ]; do
    systemctl restart $service
    sleep 2
    if systemctl is-active --quiet $service; then
        echo "Service $service started successfully"
        exit 0
    fi
    ((retry++))
done

echo "Failed to start $service after $max_retries attempts"
exit 1
```

---

### 32. 批量SSH执行

```bash
#!/bin/bash
hosts="host1 host2 host3"
cmd=$1

for host in $hosts; do
    echo "=== $host ==="
    ssh -o ConnectTimeout=5 $host "$cmd"
done
```

---

## 速查表

| 需求 | 核心命令 |
|------|----------|
| 统计行数 | `wc -l` |
| 去重统计 | `sort \| uniq -c` |
| 取前N行 | `head -N` |
| 取后N行 | `tail -N` |
| 按列提取 | `awk '{print $N}'` 或 `cut -dX -fN` |
| 文本替换 | `sed 's/old/new/g'` |
| 正则过滤 | `grep -E 'pattern'` |
| 反向过滤 | `grep -v 'pattern'` |
| 数值排序 | `sort -n`（升序） `sort -rn`（降序）|
| 进程查找 | `ps aux \| grep` 或 `pgrep` |
| 端口查看 | `ss -tlnp` 或 `netstat -tlnp` |

---

## 常见陷阱

1. **变量引号**：`"$var"` 保留空格，`$var` 会被分词
2. **命令替换**：用 `$(cmd)` 而非反引号
3. **整数比较**：用 `-eq -gt -lt`，不是 `== > <`
4. **字符串比较**：用 `=` 或 `==`（在 `[[ ]]` 中）
5. **文件存在**：`-f`（文件）`-d`（目录）`-e`（存在）
6. **管道状态**：`${PIPESTATUS[@]}` 获取管道中各命令状态

---

## 相关文章

- [上一篇：SRE笔试题-综合实战题](/articles/sre/sre-20-SRE笔试题-综合实战题/)
- [下一篇：SRE笔试题-Kubernetes速查](/articles/sre/sre-22-SRE笔试题-Kubernetes速查/)
