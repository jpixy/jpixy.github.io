+++
title = "35.安全事件排查实战"
date = 2026-01-21
description = "SRE安全事件排查完整指南：入侵检测、异常进程、后门排查、应急响应流程"
[taxonomies]
tags = ["SRE", "安全", "排查", "实战", "入侵检测", "应急响应"]
+++

## 概述

安全事件是SRE必须具备的排查能力。本文详细介绍安全事件的排查思路、常用命令和应急响应流程。

---

# 一、安全事件发现

## 1.1 常见入侵迹象

### 异常迹象清单

```
□ CPU/内存异常高（挖矿）
□ 网络流量异常（DDoS、数据外泄）
□ 未知进程或服务
□ 可疑的定时任务
□ 异常的登录记录
□ 文件被篡改
□ 系统命令被替换
□ 可疑的网络连接
```

### 快速检查脚本

```bash
#!/bin/bash
# security_check.sh - 安全快速检查

echo "===== 安全快速检查 ====="
echo "时间: $(date)"
echo ""

echo "--- 1. 可疑进程（CPU高）---"
ps aux --sort=-%cpu | head -10
echo ""

echo "--- 2. 异常网络连接 ---"
netstat -antup | grep ESTABLISHED | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
echo ""

echo "--- 3. 最近登录 ---"
last -10
echo ""

echo "--- 4. 登录失败 ---"
grep "Failed password" /var/log/auth.log 2>/dev/null | tail -5 || grep "Failed password" /var/log/secure 2>/dev/null | tail -5
echo ""

echo "--- 5. 定时任务 ---"
for user in $(cut -f1 -d: /etc/passwd); do
    crontab -u $user -l 2>/dev/null | grep -v "^#" | grep -v "^$" && echo "  (user: $user)"
done
echo ""

echo "--- 6. 可疑SUID文件 ---"
find / -perm -4000 -type f 2>/dev/null | head -20
echo ""

echo "--- 7. 最近修改的文件 ---"
find /etc /bin /sbin /usr/bin /usr/sbin -mtime -1 -type f 2>/dev/null
echo ""

echo "===== 检查完成 ====="
```

---

# 二、登录与认证排查

## 2.1 登录记录分析

### 查看登录历史

```bash
# 查看最近登录
last

# 输出解读：
# user     pts/0        192.168.1.100    Mon Jan 21 10:00   still logged in
# user     pts/0        192.168.1.100    Mon Jan 21 09:00 - 09:30  (00:30)
# reboot   system boot  5.4.0-xxx        Mon Jan 21 08:00   still running
#
# 字段：用户名、终端、来源IP、登录时间、登出时间（持续时间）

# 参数详解：
# -n 20      显示最近20条
# -f /var/log/wtmp.1  指定日志文件
# -x         显示系统关机和运行级别变化
# -a         在最后一列显示主机名
# -i         显示IP而非主机名

# 查看最近20条登录
last -n 20 -ai

# 查看特定用户
last <username>

# 查看重启记录
last reboot

# 查看仍在登录的用户
who
w

# w命令输出更详细：
# USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
# user     pts/0    192.168.1.100    10:00    0.00s  0.10s  0.01s w
```

### 查看失败登录

```bash
# 失败登录记录
lastb

# 或从日志分析
# Debian/Ubuntu
grep "Failed password" /var/log/auth.log

# CentOS/RHEL
grep "Failed password" /var/log/secure

# 统计失败登录的IP
grep "Failed password" /var/log/auth.log | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | sort | uniq -c | sort -rn | head -20

# 统计失败登录的用户
grep "Failed password" /var/log/auth.log | grep -oE 'for [^ ]+' | sort | uniq -c | sort -rn | head -20

# 统计每小时失败次数
grep "Failed password" /var/log/auth.log | awk '{print $1, $2, $3}' | uniq -c
```

### SSH特定检查

```bash
# 查看SSH配置
cat /etc/ssh/sshd_config | grep -v "^#" | grep -v "^$"

# 关注安全配置：
# PermitRootLogin       是否允许root登录
# PasswordAuthentication 是否允许密码登录
# AllowUsers/DenyUsers  用户白名单/黑名单
# MaxAuthTries          最大尝试次数

# 查看当前SSH连接
ss -tnp | grep :22
who

# 查看SSH密钥
ls -la ~/.ssh/
cat ~/.ssh/authorized_keys

# 检查所有用户的authorized_keys
for user in $(cut -d: -f1 /etc/passwd); do
    keyfile="/home/$user/.ssh/authorized_keys"
    if [ -f "$keyfile" ]; then
        echo "=== $user ==="
        cat "$keyfile"
    fi
done

# root的密钥
cat /root/.ssh/authorized_keys 2>/dev/null
```

---

## 2.2 用户账户检查

### 检查可疑账户

```bash
# 查看所有用户
cat /etc/passwd

# 字段解读：
# username:x:UID:GID:comment:home:shell
# UID 0 是root
# 检查是否有其他UID为0的用户（后门账户）
awk -F: '$3==0 {print}' /etc/passwd

# 查看有登录shell的用户
grep -v "nologin\|false" /etc/passwd

# 查看sudo权限用户
cat /etc/sudoers
cat /etc/sudoers.d/*
grep -v "^#" /etc/sudoers | grep -v "^$"

# 查看wheel/sudo组成员
grep -E "^(wheel|sudo)" /etc/group

# 最近创建的用户（检查/etc/passwd修改时间）
ls -la /etc/passwd
stat /etc/passwd

# 比较passwd和shadow
awk -F: '{print $1}' /etc/passwd | sort > /tmp/passwd_users
awk -F: '{print $1}' /etc/shadow | sort > /tmp/shadow_users
diff /tmp/passwd_users /tmp/shadow_users
```

### 密码安全检查

```bash
# 检查空密码账户
awk -F: '$2=="" {print $1}' /etc/shadow

# 检查密码状态
passwd -S <username>
# 输出：username PS 2024-01-01 0 99999 7 -1 (Password set, SHA512 crypt.)
# PS=密码已设置, LK=锁定, NP=无密码

# 检查所有账户状态
for user in $(awk -F: '{print $1}' /etc/shadow); do
    passwd -S $user 2>/dev/null
done
```

---

# 三、进程排查

## 3.1 异常进程检测

### 进程检查

```bash
# 查看所有进程
ps auxf

# 按CPU排序（挖矿常见）
ps aux --sort=-%cpu | head -20

# 按内存排序
ps aux --sort=-%mem | head -20

# 查看进程树
pstree -p

# 查看特定用户的进程
ps -u <username>

# 查看没有对应可执行文件的进程（可疑）
ls -l /proc/*/exe 2>/dev/null | grep deleted

# 查看隐藏进程（进程名以.开头或很长的随机字符串）
ps aux | awk '$11 ~ /^\./ || length($11) > 50'
```

### 进程详细分析

```bash
# 查看进程详细信息
cat /proc/<PID>/status

# 查看进程命令行
cat /proc/<PID>/cmdline | tr '\0' ' '

# 查看进程可执行文件路径
ls -l /proc/<PID>/exe

# 查看进程工作目录
ls -l /proc/<PID>/cwd

# 查看进程打开的文件
ls -l /proc/<PID>/fd
lsof -p <PID>

# 查看进程网络连接
lsof -i -p <PID>
ss -tp | grep <PID>

# 查看进程环境变量
cat /proc/<PID>/environ | tr '\0' '\n'

# 查看进程内存映射
cat /proc/<PID>/maps
```

### 隐藏进程检测

```bash
# 比较ps和/proc
ps aux | awk '{print $2}' | sort -n > /tmp/ps_pids
ls /proc | grep -E '^[0-9]+$' | sort -n > /tmp/proc_pids
diff /tmp/ps_pids /tmp/proc_pids

# 使用unhide工具
apt install unhide
unhide proc
unhide sys
```

---

## 3.2 挖矿程序检测

### 特征识别

```bash
# 挖矿特征：
# 1. 高CPU使用率
# 2. 连接矿池端口（3333, 4444, 5555, 14444等）
# 3. 进程名常见：xmrig, minerd, kworker伪装等

# 检查高CPU进程
ps aux --sort=-%cpu | head -10

# 检查矿池连接
netstat -antp | grep -E "3333|4444|5555|14444|45700"
ss -tp | grep -E "3333|4444|5555|14444"

# 检查可疑进程名
ps aux | grep -iE "miner|xmr|monero|crypto|kwork"

# 检查/tmp下的可疑文件
ls -la /tmp/
ls -la /var/tmp/
ls -la /dev/shm/

# 使用lsof查找异常进程
lsof -i | grep -E "3333|4444|5555"
```

### 清除挖矿程序

```bash
# 1. 记录证据
ps aux > /tmp/ps_evidence.txt
netstat -antp > /tmp/netstat_evidence.txt
crontab -l > /tmp/cron_evidence.txt

# 2. 杀死进程
kill -9 <PID>

# 3. 清理文件
rm -f /tmp/suspicious_file
rm -f /var/tmp/suspicious_file

# 4. 清理定时任务
crontab -e  # 删除可疑条目
vim /etc/crontab
ls /etc/cron.d/  # 检查并删除可疑文件

# 5. 检查启动项
systemctl list-unit-files | grep enabled
ls /etc/systemd/system/
ls /etc/init.d/
```

---

# 四、文件系统排查

## 4.1 可疑文件检测

### 检查系统文件完整性

```bash
# 使用rpm验证（CentOS/RHEL）
rpm -Va
# 输出含义：
# S - 大小变化
# M - 权限变化
# 5 - MD5校验和变化
# T - 修改时间变化
# L - 链接变化

# 使用debsums验证（Debian/Ubuntu）
apt install debsums
debsums -c  # 只显示变化的文件

# 检查常用命令是否被替换
which ps ls netstat ss
file /bin/ps /bin/ls /bin/netstat

# 检查文件hash
md5sum /bin/ps /bin/ls /bin/netstat
sha256sum /bin/ps /bin/ls /bin/netstat
```

### 查找最近修改的文件

```bash
# 最近24小时修改的文件
find / -mtime -1 -type f 2>/dev/null

# 最近1小时修改的系统目录文件
find /etc /bin /sbin /usr/bin /usr/sbin -mmin -60 -type f 2>/dev/null

# 查找隐藏文件
find / -name ".*" -type f 2>/dev/null | head -50

# 查找大的隐藏文件
find / -name ".*" -type f -size +1M 2>/dev/null

# 查找异常权限文件
find / -perm -4000 -type f 2>/dev/null  # SUID
find / -perm -2000 -type f 2>/dev/null  # SGID
find / -perm -o+w -type f 2>/dev/null   # 全局可写（危险）
```

### 检查启动项

```bash
# systemd服务
systemctl list-unit-files --state=enabled
ls -la /etc/systemd/system/
ls -la /lib/systemd/system/

# 传统init
ls -la /etc/init.d/
ls -la /etc/rc.local

# 用户登录脚本
cat /etc/profile
cat /etc/bash.bashrc
ls -la /etc/profile.d/
cat ~/.bashrc
cat ~/.bash_profile

# 检查所有用户的bashrc
for user in $(cut -d: -f1 /etc/passwd); do
    home=$(eval echo ~$user)
    if [ -f "$home/.bashrc" ]; then
        echo "=== $user/.bashrc ==="
        tail -20 "$home/.bashrc"
    fi
done
```

---

## 4.2 后门检测

### 常见后门位置

```bash
# SSH后门
cat ~/.ssh/authorized_keys
cat /root/.ssh/authorized_keys
# 检查是否有陌生公钥

# 定时任务后门
crontab -l
cat /etc/crontab
ls -la /etc/cron.d/
ls -la /etc/cron.daily/
ls -la /etc/cron.hourly/
cat /var/spool/cron/*

# 服务后门
systemctl list-units --type=service
# 查找可疑服务

# 内核模块后门
lsmod
# 查找可疑模块

# LD_PRELOAD后门
cat /etc/ld.so.preload
echo $LD_PRELOAD
cat /etc/environment | grep LD

# PAM后门
ls -la /lib/security/
ls -la /lib64/security/
# 检查pam配置
cat /etc/pam.d/sshd
```

### Webshell检测

```bash
# 查找PHP webshell特征
find /var/www -name "*.php" -exec grep -l "eval\|base64_decode\|system\|exec\|passthru\|shell_exec" {} \;

# 查找最近上传的文件
find /var/www -mtime -7 -type f -name "*.php"

# 检查隐藏的PHP文件
find /var/www -name "*.php" | xargs ls -la | grep "^\."

# 查找异常权限
find /var/www -perm -o+w -type f

# 检查图片伪装
find /var/www -name "*.jpg" -exec file {} \; | grep -v "image"
```

---

# 五、网络排查

## 5.1 异常连接检测

### 查看网络连接

```bash
# 查看所有连接
netstat -antup
ss -antup

# 参数详解：
# -a  所有连接
# -n  数字格式
# -t  TCP
# -u  UDP
# -p  显示进程

# 查看监听端口
ss -tlnp

# 查看建立的连接
ss -tnp state established

# 按连接数统计IP
ss -tn | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20

# 查看连接到异常端口的
# 常见矿池端口：3333, 4444, 5555, 14444, 45700
ss -tn | grep -E ":3333|:4444|:5555|:14444"

# 查看外连（非本地发起的）
ss -tnp | grep -v "127.0.0.1\|::1"
```

### 查找可疑外连

```bash
# 查看对外连接的进程
lsof -i -nP | grep ESTABLISHED | grep -v "127.0.0.1\|::1"

# 按目标IP分组
lsof -i -nP | grep ESTABLISHED | awk '{print $9}' | cut -d'>' -f2 | cut -d: -f1 | sort | uniq -c | sort -rn

# 检查IRC连接（常见C2通道）
ss -tnp | grep ":6667\|:6668\|:6669"

# 检查反向shell常用端口
ss -tnp | grep -E ":4444|:5555|:1234|:31337"
```

---

## 5.2 网络流量分析

### 使用tcpdump

```bash
# 抓取特定接口流量
tcpdump -i eth0

# 常用参数：
# -i eth0      指定接口
# -n           不解析主机名
# -nn          不解析主机名和端口名
# -c 100       抓100个包
# -w file.pcap 保存到文件
# -r file.pcap 读取文件

# 抓取特定主机流量
tcpdump -i eth0 host 192.168.1.100

# 抓取特定端口
tcpdump -i eth0 port 80

# 抓取并保存
tcpdump -i eth0 -w capture.pcap -c 10000

# 抓取可疑外连
tcpdump -i eth0 'dst port 3333 or dst port 4444 or dst port 5555'
```

### 使用iftop

```bash
# 实时流量监控
iftop -i eth0

# 显示端口
iftop -i eth0 -P

# 不解析主机名
iftop -i eth0 -n
```

---

# 六、应急响应流程

## 6.1 标准响应流程

```
1. 确认事件
   - 收集初步证据
   - 确定影响范围

2. 遏制
   - 隔离受影响系统
   - 阻断攻击者访问

3. 根除
   - 清除恶意程序
   - 修补漏洞

4. 恢复
   - 恢复业务
   - 监控确认

5. 总结
   - 编写报告
   - 改进措施
```

## 6.2 应急响应操作

### 证据保全

```bash
# 创建证据目录
mkdir -p /evidence/$(date +%Y%m%d)
cd /evidence/$(date +%Y%m%d)

# 系统信息
uname -a > system_info.txt
date >> system_info.txt

# 进程快照
ps auxf > ps_full.txt

# 网络连接
netstat -antup > netstat.txt
ss -antup > ss.txt

# 登录记录
last > last.txt
lastb > lastb.txt 2>/dev/null
who > who.txt

# 定时任务
crontab -l > crontab_root.txt 2>/dev/null
cat /etc/crontab > etc_crontab.txt
ls -la /etc/cron.* > cron_dirs.txt

# 用户信息
cp /etc/passwd passwd.txt
cp /etc/shadow shadow.txt
cp /etc/group group.txt

# 日志保存
tar -czf logs.tar.gz /var/log/

# 内存快照（如果需要）
# dd if=/dev/mem of=memory.dump bs=1M
```

### 遏制措施

```bash
# 断网隔离（最极端）
ifconfig eth0 down

# 或只阻断特定IP
iptables -A INPUT -s <attacker_ip> -j DROP
iptables -A OUTPUT -d <attacker_ip> -j DROP

# 禁用可疑账户
usermod -L <username>
passwd -l <username>

# 杀死可疑进程
kill -9 <PID>

# 禁用可疑服务
systemctl stop <service>
systemctl disable <service>
```

### 清除与修复

```bash
# 删除后门文件
rm -f /path/to/backdoor

# 清理定时任务
crontab -r  # 删除所有（谨慎）
# 或手动编辑
crontab -e

# 删除可疑账户
userdel -r <username>

# 清理SSH密钥
> ~/.ssh/authorized_keys
> /root/.ssh/authorized_keys

# 修改所有密码
passwd root
passwd <other_users>

# 更新系统
apt update && apt upgrade -y

# 重启服务
systemctl restart sshd
systemctl restart <affected_services>
```

---

## 6.3 安全加固清单

```bash
# SSH加固
# /etc/ssh/sshd_config
PermitRootLogin no              # 禁止root登录
PasswordAuthentication no        # 禁用密码登录
MaxAuthTries 3                  # 最大尝试次数
AllowUsers user1 user2          # 白名单

# 防火墙配置
ufw enable
ufw default deny incoming
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp

# 安装fail2ban
apt install fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# 文件权限
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 644 /etc/passwd
chmod 640 /etc/shadow

# 关闭不需要的服务
systemctl disable <unnecessary_service>
```

---

## 总结

| 检查项 | 命令 |
|--------|------|
| 登录记录 | `last`, `lastb`, `who` |
| 失败登录 | `grep "Failed password" /var/log/auth.log` |
| 可疑用户 | `awk -F: '$3==0' /etc/passwd` |
| 异常进程 | `ps aux --sort=-%cpu` |
| 网络连接 | `ss -antup`, `netstat -antup` |
| 定时任务 | `crontab -l`, `cat /etc/crontab` |
| 启动项 | `systemctl list-unit-files` |
| 文件变化 | `find / -mtime -1 -type f` |
| SUID文件 | `find / -perm -4000` |

**应急三板斧**：
1. **保留证据** - 先取证再操作
2. **遏制隔离** - 阻止进一步损害
3. **清除恢复** - 消除威胁并恢复

**关键记忆**：
1. 发现异常先保留证据
2. UID=0的非root用户是后门
3. 检查authorized_keys、crontab、启动项
4. 矿机特征：高CPU + 矿池端口连接
