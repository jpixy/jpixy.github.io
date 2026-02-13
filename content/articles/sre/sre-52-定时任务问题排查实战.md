+++
title = "52. 定时任务问题排查实战"
date = 2026-01-21
weight = 52000
description = "SRE定时任务问题排查完整指南：cron、systemd timer故障排查与调试"
[taxonomies]
tags = ["SRE", "定时任务", "cron", "systemd", "排查", "实战"]
+++

## 概述

定时任务是自动化运维的基础。本文详细介绍cron和systemd timer的配置、排查和调试方法。

---

# 一、Cron定时任务

## 1.1 Cron基础

### Cron配置位置

```bash
# 用户crontab
crontab -e          # 编辑当前用户的crontab
crontab -l          # 查看当前用户的crontab
crontab -u user -l  # 查看指定用户的crontab

# 用户crontab文件位置
/var/spool/cron/crontabs/   # Debian/Ubuntu
/var/spool/cron/            # CentOS/RHEL

# 系统级crontab
/etc/crontab               # 系统crontab（包含用户字段）
/etc/cron.d/               # 系统cron配置目录
/etc/cron.hourly/          # 每小时执行
/etc/cron.daily/           # 每天执行
/etc/cron.weekly/          # 每周执行
/etc/cron.monthly/         # 每月执行
```

### Cron表达式详解

```bash
# 格式：分 时 日 月 周 命令
# ┌───────────── 分钟 (0-59)
# │ ┌───────────── 小时 (0-23)
# │ │ ┌───────────── 日 (1-31)
# │ │ │ ┌───────────── 月 (1-12)
# │ │ │ │ ┌───────────── 周几 (0-7，0和7都表示周日)
# │ │ │ │ │
# * * * * * command

# 特殊字符：
# *     任意值
# ,     列表（如 1,3,5）
# -     范围（如 1-5）
# /     步长（如 */5 表示每5单位）

# 示例：
# 每分钟执行
* * * * * /path/to/script.sh

# 每5分钟执行
*/5 * * * * /path/to/script.sh

# 每天凌晨2点执行
0 2 * * * /path/to/script.sh

# 每周一凌晨3点执行
0 3 * * 1 /path/to/script.sh

# 每月1号和15号的9点执行
0 9 1,15 * * /path/to/script.sh

# 工作日每小时执行
0 * * * 1-5 /path/to/script.sh

# 特殊字符串：
@reboot     # 启动时执行
@yearly     # 每年（0 0 1 1 *）
@monthly    # 每月（0 0 1 * *）
@weekly     # 每周（0 0 * * 0）
@daily      # 每天（0 0 * * *）
@hourly     # 每小时（0 * * * *）
```

### 系统crontab格式

```bash
# /etc/crontab 和 /etc/cron.d/* 有额外的用户字段
# 分 时 日 月 周 用户 命令

# 示例 /etc/crontab
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# 分 时 日 月 周 用户 命令
17 *    * * *   root    cd / && run-parts --report /etc/cron.hourly
25 6    * * *   root    test -x /usr/sbin/anacron || run-parts --report /etc/cron.daily
47 6    * * 7   root    test -x /usr/sbin/anacron || run-parts --report /etc/cron.weekly
52 6    1 * *   root    test -x /usr/sbin/anacron || run-parts --report /etc/cron.monthly

# 示例 /etc/cron.d/backup
0 2 * * * root /usr/local/bin/backup.sh
```

---

## 1.2 Cron日志查看

### 查看cron日志

```bash
# Debian/Ubuntu (rsyslog)
grep CRON /var/log/syslog
tail -f /var/log/syslog | grep CRON

# CentOS/RHEL
cat /var/log/cron
tail -f /var/log/cron

# systemd journal
journalctl -u cron
journalctl -u crond

# 查看特定时间段
journalctl -u cron --since "1 hour ago"
journalctl -u cron --since "2024-01-21 00:00" --until "2024-01-21 12:00"

# 查看特定用户的任务
grep "user" /var/log/syslog | grep CRON
```

### 日志输出解读

```bash
# 正常执行日志
# Jan 21 02:00:01 hostname CRON[12345]: (root) CMD (/path/to/script.sh)

# 字段说明：
# Jan 21 02:00:01  时间戳
# hostname         主机名
# CRON[12345]      进程PID
# (root)           执行用户
# CMD              执行的命令

# 常见问题日志：
# (CRON) info (No MTA installed, discarding output)
# 说明：没有邮件系统，任务输出被丢弃

# (root) FAILED to open PAM security session
# 说明：PAM配置问题

# cron[XXX]: /etc/crontab: Permission denied
# 说明：权限问题
```

---

## 1.3 Cron问题排查

### 问题1：任务不执行

```bash
# 排查步骤：

# 1. 检查cron服务状态
systemctl status cron      # Debian/Ubuntu
systemctl status crond     # CentOS/RHEL

# 2. 检查crontab语法
crontab -l
# 确认格式正确

# 3. 检查日志是否有执行记录
grep CRON /var/log/syslog | grep "script_name"

# 4. 检查脚本权限
ls -la /path/to/script.sh
# 需要可执行权限
chmod +x /path/to/script.sh

# 5. 检查脚本路径
# cron中使用绝对路径
which python   # 获取完整路径
/usr/bin/python /path/to/script.py

# 6. 检查环境变量
# cron环境变量很少，需要在脚本中设置或在crontab中定义
# 在crontab开头添加：
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
SHELL=/bin/bash

# 7. 手动测试脚本
/path/to/script.sh
echo $?  # 检查退出码

# 8. 模拟cron环境测试
env -i /bin/bash --noprofile --norc -c '/path/to/script.sh'
```

### 问题2：任务执行但失败

```bash
# 1. 捕获输出和错误
* * * * * /path/to/script.sh >> /var/log/script.log 2>&1

# 2. 查看输出日志
tail -f /var/log/script.log

# 3. 添加调试信息
#!/bin/bash
set -x  # 打印执行的命令
echo "Start: $(date)"
echo "User: $(whoami)"
echo "PWD: $(pwd)"
echo "PATH: $PATH"

# 执行实际命令
/path/to/command

echo "Exit code: $?"
echo "End: $(date)"

# 4. 检查依赖
# 确保脚本依赖的命令在PATH中
which required_command

# 5. 检查工作目录
# cron默认从用户home目录执行
cd /correct/working/directory && ./script.sh
```

### 问题3：任务重复执行

```bash
# 可能原因：

# 1. 多个地方配置了同一任务
# 检查所有位置
crontab -l
cat /etc/crontab
ls /etc/cron.d/
ls /etc/cron.*/

# 2. 使用文件锁防止重复
#!/bin/bash
LOCKFILE=/tmp/script.lock

if [ -f "$LOCKFILE" ]; then
    echo "Already running"
    exit 0
fi

trap "rm -f $LOCKFILE" EXIT
touch $LOCKFILE

# 执行任务
/path/to/actual/command

# 3. 使用flock
* * * * * /usr/bin/flock -n /tmp/script.lock /path/to/script.sh

# flock参数：
# -n  非阻塞（获取不到锁立即退出）
# -w  等待超时
# -x  排他锁（默认）
# -s  共享锁
```

### 问题4：邮件问题

```bash
# cron默认会将输出发送邮件

# 1. 检查邮件
mail
cat /var/mail/root
cat /var/spool/mail/root

# 2. 设置邮件接收者
MAILTO=admin@example.com
* * * * * /path/to/script.sh

# 3. 禁用邮件
MAILTO=""
* * * * * /path/to/script.sh

# 4. 丢弃输出
* * * * * /path/to/script.sh > /dev/null 2>&1

# 5. 只在失败时发邮件
* * * * * /path/to/script.sh || echo "Failed" | mail -s "Cron Failed" admin@example.com
```

---

## 1.4 Cron调试技巧

### 模拟cron环境

```bash
#!/bin/bash
# cron_debug.sh - 模拟cron环境执行脚本

SCRIPT=$1

if [ -z "$SCRIPT" ]; then
    echo "Usage: $0 <script_path>"
    exit 1
fi

# 模拟cron的最小环境
env -i \
    HOME=$HOME \
    LOGNAME=$USER \
    PATH=/usr/bin:/bin \
    SHELL=/bin/sh \
    /bin/bash "$SCRIPT"

echo "Exit code: $?"
```

### Cron执行记录脚本

```bash
#!/bin/bash
# cron_wrapper.sh - Cron任务包装器

SCRIPT=$1
LOGDIR=/var/log/cron_jobs
LOGFILE=$LOGDIR/$(basename "$SCRIPT")_$(date +%Y%m%d_%H%M%S).log

mkdir -p $LOGDIR

{
    echo "=== Cron Job Start ==="
    echo "Time: $(date)"
    echo "User: $(whoami)"
    echo "PWD: $(pwd)"
    echo "Script: $SCRIPT"
    echo "=== Output ==="
    
    # 执行脚本
    "$SCRIPT"
    exit_code=$?
    
    echo "=== End ==="
    echo "Exit code: $exit_code"
    echo "Time: $(date)"
    
} >> "$LOGFILE" 2>&1

# 保留最近100个日志
ls -t $LOGDIR/$(basename "$SCRIPT")_* | tail -n +101 | xargs -r rm

exit $exit_code
```

使用方法：
```bash
* * * * * /path/to/cron_wrapper.sh /path/to/actual_script.sh
```

---

# 二、Systemd Timer

## 2.1 Systemd Timer基础

### Timer配置

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Daily backup timer

[Timer]
# 基于日历时间
OnCalendar=*-*-* 02:00:00
# 或使用预定义时间
# OnCalendar=daily

# 基于系统启动时间
# OnBootSec=5min
# OnUnitActiveSec=1h

# 准确度（随机延迟，避免同时执行）
AccuracySec=1min

# 持久化（错过的执行会在启动后补上）
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Backup service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=root

# 日志
StandardOutput=journal
StandardError=journal

# 超时
TimeoutStartSec=3600
```

### OnCalendar语法

```bash
# OnCalendar格式：周 年-月-日 时:分:秒

# 示例：
OnCalendar=*-*-* 02:00:00     # 每天02:00
OnCalendar=Mon *-*-* 03:00:00 # 每周一03:00
OnCalendar=*-*-01 04:00:00    # 每月1号04:00
OnCalendar=*-01-01 00:00:00   # 每年1月1日
OnCalendar=hourly             # 每小时
OnCalendar=daily              # 每天
OnCalendar=weekly             # 每周
OnCalendar=monthly            # 每月

# 验证OnCalendar表达式
systemd-analyze calendar "*-*-* 02:00:00"
systemd-analyze calendar "Mon *-*-* 03:00:00"

# 查看未来触发时间
systemd-analyze calendar --iterations=5 "*-*-* 02:00:00"
```

### 管理Timer

```bash
# 列出所有timer
systemctl list-timers
systemctl list-timers --all

# 输出列：
# NEXT          下次触发时间
# LEFT          距离下次触发
# LAST          上次触发时间
# PASSED        距离上次触发
# UNIT          timer单元名
# ACTIVATES     触发的服务

# 启用timer
systemctl enable backup.timer
systemctl start backup.timer

# 停止timer
systemctl stop backup.timer
systemctl disable backup.timer

# 查看timer状态
systemctl status backup.timer

# 手动触发关联的服务（测试）
systemctl start backup.service

# 重载配置
systemctl daemon-reload
```

---

## 2.2 Timer日志查看

```bash
# 查看timer日志
journalctl -u backup.timer

# 查看关联服务日志
journalctl -u backup.service

# 实时查看
journalctl -u backup.service -f

# 查看最近执行
journalctl -u backup.service -n 50

# 查看特定时间
journalctl -u backup.service --since "1 hour ago"

# 查看失败的执行
journalctl -u backup.service -p err

# 组合查看timer和service
journalctl -u backup.timer -u backup.service
```

---

## 2.3 Timer问题排查

### 问题1：Timer不触发

```bash
# 1. 检查timer状态
systemctl status backup.timer

# 查看是否enabled和active
# Active: active (waiting)  正常
# Active: inactive          未启动

# 2. 检查timer列表
systemctl list-timers | grep backup

# 如果不在列表中，可能：
# - 未启动：systemctl start backup.timer
# - 未启用：systemctl enable backup.timer

# 3. 检查timer配置
systemctl cat backup.timer
systemd-analyze verify backup.timer

# 4. 检查OnCalendar是否正确
systemd-analyze calendar "你的OnCalendar表达式"

# 5. 检查日志
journalctl -u backup.timer -n 20
```

### 问题2：Service执行失败

```bash
# 1. 查看服务状态
systemctl status backup.service

# 关注：
# Active: failed (Result: exit-code)
# Main PID: 12345 (code=exited, status=1/FAILURE)

# 2. 查看详细日志
journalctl -u backup.service -n 50

# 3. 手动测试服务
systemctl start backup.service
systemctl status backup.service

# 4. 检查服务配置
systemctl cat backup.service
systemd-analyze verify backup.service

# 5. 检查ExecStart命令
# 确保路径正确、权限正确
ls -la /usr/local/bin/backup.sh
```

### 问题3：Timer延迟执行

```bash
# 原因：AccuracySec导致的随机延迟

# 查看配置
systemctl cat backup.timer | grep AccuracySec

# 默认AccuracySec=1min，会有最多1分钟的随机延迟

# 设置更精确
[Timer]
AccuracySec=1s   # 1秒精度
# 或
AccuracySec=1us  # 微秒精度（最高精度）
```

### 问题4：错过的执行

```bash
# 使用Persistent=true确保错过的执行会补上

[Timer]
OnCalendar=daily
Persistent=true

# 如果系统在计划时间关机，下次启动后会立即执行一次

# 检查是否配置了Persistent
systemctl cat backup.timer | grep Persistent
```

---

## 2.4 Timer调试技巧

### 验证配置

```bash
# 验证timer文件
systemd-analyze verify /etc/systemd/system/backup.timer

# 验证service文件
systemd-analyze verify /etc/systemd/system/backup.service

# 检查依赖
systemctl list-dependencies backup.timer
```

### 创建完整示例

```bash
# 创建服务文件
cat > /etc/systemd/system/myjob.service << 'EOF'
[Unit]
Description=My scheduled job

[Service]
Type=oneshot
ExecStart=/usr/local/bin/myjob.sh
User=root
StandardOutput=journal
StandardError=journal
EOF

# 创建timer文件
cat > /etc/systemd/system/myjob.timer << 'EOF'
[Unit]
Description=Run myjob every hour

[Timer]
OnCalendar=*:00
AccuracySec=1min
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 创建脚本
cat > /usr/local/bin/myjob.sh << 'EOF'
#!/bin/bash
echo "Job started at $(date)"
# 执行任务
echo "Job finished at $(date)"
EOF
chmod +x /usr/local/bin/myjob.sh

# 启用timer
systemctl daemon-reload
systemctl enable myjob.timer
systemctl start myjob.timer

# 验证
systemctl list-timers | grep myjob
```

---

# 三、定时任务最佳实践

## 3.1 任务监控

```bash
#!/bin/bash
# job_monitor.sh - 定时任务监控

echo "===== 定时任务监控 ====="
echo "时间: $(date)"
echo ""

echo "--- Cron服务状态 ---"
systemctl is-active cron 2>/dev/null || systemctl is-active crond 2>/dev/null
echo ""

echo "--- Systemd Timers ---"
systemctl list-timers --all --no-pager | head -20
echo ""

echo "--- 最近失败的Timer服务 ---"
systemctl list-units --type=service --state=failed | grep -E "\.service" | head -10
echo ""

echo "--- 最近的Cron日志 ---"
journalctl -u cron -n 10 --no-pager 2>/dev/null || \
    journalctl -u crond -n 10 --no-pager 2>/dev/null || \
    tail -10 /var/log/cron 2>/dev/null
echo ""

echo "--- 用户Crontab ---"
for user in $(cut -d: -f1 /etc/passwd); do
    crontab -u $user -l 2>/dev/null | grep -v "^#" | grep -v "^$" > /dev/null && echo "User: $user has crontab"
done
echo ""

echo "===== 监控完成 ====="
```

## 3.2 任务告警

```bash
#!/bin/bash
# job_with_alert.sh - 带告警的定时任务

SCRIPT_NAME="backup"
LOG_FILE="/var/log/${SCRIPT_NAME}.log"
ALERT_EMAIL="admin@example.com"
WEBHOOK_URL="https://hooks.slack.com/services/xxx"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert() {
    local message="$1"
    
    # 邮件告警
    echo "$message" | mail -s "[$SCRIPT_NAME] Alert" "$ALERT_EMAIL" 2>/dev/null
    
    # Slack告警
    curl -s -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"[$SCRIPT_NAME] $message\"}" \
        "$WEBHOOK_URL" 2>/dev/null
}

# 主逻辑
main() {
    log "Job started"
    
    # 执行实际任务
    if /path/to/actual/command >> "$LOG_FILE" 2>&1; then
        log "Job completed successfully"
    else
        log "Job failed with exit code $?"
        send_alert "Job failed! Check log at $LOG_FILE"
        exit 1
    fi
}

# 使用flock防止重复执行
exec 200>/tmp/${SCRIPT_NAME}.lock
if ! flock -n 200; then
    log "Another instance is running"
    exit 0
fi

main
```

## 3.3 Cron vs Systemd Timer对比

| 特性 | Cron | Systemd Timer |
|------|------|---------------|
| 配置复杂度 | 简单 | 较复杂 |
| 日志 | syslog | journal（更强大） |
| 依赖管理 | 无 | 支持 |
| 资源限制 | 无 | 支持cgroup |
| 错过补执行 | 无 | Persistent=true |
| 随机延迟 | 无 | AccuracySec |
| 环境变量 | 需手动设置 | 从unit继承 |

---

## 总结

### Cron命令速查

| 任务 | 命令 |
|------|------|
| 编辑crontab | `crontab -e` |
| 查看crontab | `crontab -l` |
| 查看日志 | `grep CRON /var/log/syslog` |
| 服务状态 | `systemctl status cron` |

### Systemd Timer命令速查

| 任务 | 命令 |
|------|------|
| 列出timer | `systemctl list-timers` |
| 查看日志 | `journalctl -u xxx.service` |
| 验证配置 | `systemd-analyze verify` |
| 验证时间 | `systemd-analyze calendar` |

### 定时任务排查三板斧

1. **查服务** - cron/crond服务是否运行
2. **查日志** - 是否有执行记录和错误
3. **查脚本** - 路径、权限、环境变量

### 关键记忆

1. Cron环境变量很少，需要设置PATH
2. 使用绝对路径
3. 重定向输出便于调试
4. flock防止重复执行
5. Systemd timer用Persistent补执行

---

## 相关文章

- [上一篇：负载均衡深入排查实战](@/articles/sre/sre-51-负载均衡深入排查实战.md)
- [下一篇：内核参数调优实战](@/articles/sre/sre-53-内核参数调优实战.md)
