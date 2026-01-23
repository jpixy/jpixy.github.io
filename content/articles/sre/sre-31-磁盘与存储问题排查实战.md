+++
title = "31.磁盘与存储问题排查实战"
date = 2026-01-21
description = "SRE磁盘问题排查完整指南：磁盘满、inode耗尽、IO问题、IO调度器调优的定位与解决"
[taxonomies]
tags = ["SRE", "磁盘", "排查", "实战", "IO调度器", "块设备", "NFS", "Ceph"]
+++

## 概述

磁盘和存储问题是SRE最常遇到的问题之一，轻则服务异常，重则数据丢失。本文系统介绍各类磁盘问题的排查方法。

---

# 一、磁盘空间不足

## 1.1 快速定位

### 第一步：确认磁盘使用情况

```bash
# 查看所有挂载点使用情况
df -h

# 只看使用率超过80%的
df -h | awk '$5+0 > 80 {print}'

# 查看inode使用
df -i

# 查看特定目录
df -h /var
```

### 第二步：找出占用空间大的目录

```bash
# 方法1：du逐层查找（推荐）
du -sh /* 2>/dev/null | sort -hr | head -10
du -sh /var/* 2>/dev/null | sort -hr | head -10
du -sh /var/log/* 2>/dev/null | sort -hr | head -10

# 方法2：ncdu交互式查看
sudo apt install ncdu
ncdu /

# 方法3：一行命令找大目录
du -h --max-depth=2 / 2>/dev/null | sort -hr | head -20
```

### 第三步：找出大文件

```bash
# 找出大于1GB的文件
find / -type f -size +1G 2>/dev/null | head -20

# 带大小显示
find / -type f -size +1G -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}'

# 按大小排序
find / -type f -size +100M -exec ls -s {} \; 2>/dev/null | sort -rn | head -20

# 只在特定目录查找
find /var -type f -size +100M -exec ls -lh {} \; 2>/dev/null
```

---

## 1.2 常见磁盘空间问题

### 场景1：日志文件过大

```bash
# 查看日志目录大小
du -sh /var/log/*

# 找出大日志文件
find /var/log -type f -size +100M -exec ls -lh {} \;

# 清理方法1：truncate（保留文件描述符）
truncate -s 0 /var/log/large.log

# 清理方法2：logrotate强制轮转
logrotate -f /etc/logrotate.conf

# 清理方法3：删除旧日志
find /var/log -name "*.gz" -mtime +7 -delete
find /var/log -name "*.log.*" -mtime +7 -delete

# 检查日志配置
cat /etc/logrotate.d/rsyslog
```

### 场景2：/tmp目录满

```bash
# 查看/tmp使用情况
du -sh /tmp/*

# 找出大文件
find /tmp -type f -size +100M

# 找出老文件
find /tmp -type f -mtime +7

# 清理（谨慎操作）
find /tmp -type f -mtime +7 -delete

# 查看谁在使用/tmp
lsof +D /tmp
```

### 场景3：Docker占用空间

```bash
# 查看Docker磁盘使用
docker system df

# 详细信息
docker system df -v

# 清理未使用资源
docker system prune -a

# 只清理镜像
docker image prune -a

# 只清理容器
docker container prune

# 只清理卷
docker volume prune

# 查看容器日志大小
du -sh /var/lib/docker/containers/*/*.log

# 限制容器日志大小（docker-compose.yml）
# logging:
#   driver: "json-file"
#   options:
#     max-size: "100m"
#     max-file: "3"
```

### 场景4：包管理器缓存

```bash
# APT缓存
du -sh /var/cache/apt/archives/
sudo apt clean

# YUM缓存
du -sh /var/cache/yum/
sudo yum clean all

# pip缓存
du -sh ~/.cache/pip/
pip cache purge

# npm缓存
du -sh ~/.npm/
npm cache clean --force
```

---

# 二、df和du不一致

## 2.1 问题现象

```bash
# df显示磁盘已满
df -h /
# Filesystem      Size  Used  Avail Use% Mounted on
# /dev/sda1       100G   95G     0  100% /

# 但du显示只用了50G
du -sh /
# 50G   /

# 相差45GB！
```

## 2.2 原因分析

### 原因1：已删除但未释放的文件（最常见）

```bash
# 查找被删除但仍被进程占用的文件
lsof | grep deleted

# 或更精确地
lsof +L1

# 输出示例：
# nginx   12345   root  10w  REG  8,1  5000000000  0 /var/log/nginx/access.log (deleted)
# 表示这个5GB的文件被删除了，但nginx还在写入
```

**解决方法**

```bash
# 方法1：重启占用该文件的进程
systemctl restart nginx

# 方法2：不重启，清空文件描述符（需要root）
# 找到进程PID和文件描述符编号
lsof | grep deleted
# nginx   12345   root  10w  REG  ...

# 清空该文件描述符
echo > /proc/12345/fd/10

# 方法3：使用gdb（高级，谨慎使用）
gdb -p 12345
(gdb) call close(10)
(gdb) quit
```

### 原因2：挂载点覆盖

```bash
# 检查是否有挂载点覆盖了原有数据
mount | grep "on /"

# 例如：/mnt/data挂载到了已有数据的目录上
# 原目录的数据还在，但被遮挡了

# 解决：umount后查看原目录
umount /mnt/data
ls /mnt/data  # 现在能看到原来的数据
```

### 原因3：稀疏文件

```bash
# 稀疏文件的表观大小和实际占用不同
ls -lh sparse_file    # 显示10GB
du -h sparse_file     # 显示1GB

# 查看实际块使用
stat sparse_file
# Blocks: 262144（实际使用）
```

### 原因4：保留空间

```bash
# ext4默认保留5%给root
tune2fs -l /dev/sda1 | grep "Reserved"

# 减少保留空间（生产环境谨慎）
tune2fs -m 1 /dev/sda1  # 改为1%
```

---

## 2.3 排查脚本

```bash
#!/bin/bash
# disk_inconsistency.sh - 排查df/du不一致

echo "===== 磁盘不一致排查 ====="
echo ""

echo "--- 1. df显示 ---"
df -h /
echo ""

echo "--- 2. du显示 ---"
du -sh / 2>/dev/null
echo ""

echo "--- 3. 被删除但未释放的文件 ---"
lsof +L1 2>/dev/null | awk 'NR==1 || /deleted/'
echo ""

echo "--- 4. 按进程汇总未释放空间 ---"
lsof +L1 2>/dev/null | awk '/deleted/ {
    size=$7
    proc=$1
    sum[proc]+=size
} END {
    for(p in sum) printf "%s: %.2f GB\n", p, sum[p]/1024/1024/1024
}' | sort -t: -k2 -rn
echo ""

echo "--- 5. 挂载点 ---"
mount | grep "^/dev"
echo ""

echo "--- 6. 保留空间 ---"
tune2fs -l $(df / | awk 'NR==2{print $1}') 2>/dev/null | grep -E "Reserved|Block count"
echo ""

echo "===== 排查完成 ====="
```

---

# 三、inode耗尽

## 3.1 问题现象

```bash
# 磁盘空间有剩余，但无法创建文件
touch /tmp/test
# touch: cannot touch '/tmp/test': No space left on device

# df显示空间充足
df -h /tmp
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1       100G   50G   50G  50% /

# 但inode用完了
df -i /tmp
# Filesystem      Inodes  IUsed   IFree IUse% Mounted on
# /dev/sda1      6553600 6553600      0  100% /
```

## 3.2 找出inode大户

```bash
# 统计各目录的文件数量
for dir in /*; do
    echo "$(find "$dir" -xdev 2>/dev/null | wc -l) $dir"
done | sort -rn | head -10

# 更精确的统计
find / -xdev -printf '%h\n' 2>/dev/null | sort | uniq -c | sort -rn | head -20

# 统计目录下的文件数
find /var -xdev -type f 2>/dev/null | wc -l

# 查找小文件最多的目录
find / -xdev -type d -exec sh -c 'echo "$(find "$1" -maxdepth 1 -type f | wc -l) $1"' _ {} \; 2>/dev/null | sort -rn | head -20
```

## 3.3 常见inode消耗场景

### 场景1：大量小文件（邮件队列、Session文件等）

```bash
# 查找包含大量文件的目录
find /var/spool -type f | wc -l
find /tmp/sessions -type f | wc -l

# 清理老文件
find /var/spool/postfix/deferred -type f -mtime +7 -delete
find /tmp/sessions -type f -mtime +1 -delete
```

### 场景2：缓存文件

```bash
# 检查常见缓存目录
du -sh /var/cache/*
find /var/cache -type f | wc -l

# PHP session
find /var/lib/php/sessions -type f -mtime +1 -delete

# 代理缓存
find /var/cache/nginx -type f -mtime +7 -delete
```

### 场景3：日志轮转产生的碎片

```bash
# 检查是否有大量碎片日志
ls -la /var/log/*.log.* | wc -l

# 清理
find /var/log -name "*.log.*" -mtime +30 -delete
```

## 3.4 预防措施

```bash
# 创建文件系统时指定更多inode
mkfs.ext4 -N 20000000 /dev/sdb1

# 监控inode使用
cat << 'EOF' > /etc/cron.daily/check-inode
#!/bin/bash
THRESHOLD=80
df -i | awk -v t=$THRESHOLD 'NR>1 && $5+0 > t {print "WARNING: "$6" inode usage "$5}'
EOF
chmod +x /etc/cron.daily/check-inode
```

---

# 四、磁盘IO问题

## 4.1 IO性能监控

### 基础监控

```bash
# iostat - IO统计
iostat -x 1 5

# 关键指标：
# %util    - 设备繁忙程度（>70%需关注）
# await    - 平均IO等待时间（SSD<1ms，HDD<10ms）
# r_await  - 读等待时间
# w_await  - 写等待时间
# avgqu-sz - 平均队列长度
# r/s, w/s - 每秒读写次数
```

### 进程级IO监控

```bash
# iotop - 进程IO排行
sudo iotop -o  # 只显示有IO的进程

# pidstat - 进程IO统计
pidstat -d 1 5

# 查看特定进程IO
cat /proc/<PID>/io
```

## 4.2 IO问题排查

### 场景1：IO等待高

```bash
# 确认是IO问题
top
# 查看wa%（iowait）

# 找出IO高的进程
iotop -oP

# 确认是哪个磁盘
iostat -x 1

# 分析IO模式
# 如果%util高但IOPS低 → 大块顺序IO或磁盘慢
# 如果IOPS高 → 随机IO，考虑SSD
```

### 场景2：磁盘延迟高

```bash
# 使用ioping测试磁盘延迟
ioping -c 10 /dev/sda

# 使用fio测试
fio --name=latency --rw=randread --bs=4k --size=1G \
    --runtime=30 --filename=/data/testfile --direct=1

# 检查是否有坏块
sudo badblocks -v /dev/sda

# 检查SMART信息
sudo smartctl -a /dev/sda
```

### 场景3：特定进程IO过高

```bash
# 找出进程
iotop -oP

# 查看进程在读写什么文件
lsof -p <PID>

# 使用strace追踪IO
strace -e read,write -p <PID>

# 使用perf分析
sudo perf record -e block:block_rq_issue -a -- sleep 10
sudo perf report
```

---

# 五、文件系统问题

## 5.1 只读文件系统

### 场景：突然无法写入

```bash
# 确认文件系统状态
mount | grep "on / "
# 如果显示 ro 说明只读

# 查看原因
dmesg | tail -50
dmesg | grep -i "error\|read-only\|ext4"

# 常见原因：
# 1. 磁盘错误
# 2. 文件系统损坏
# 3. 磁盘空间满
```

### 解决方法

```bash
# 方法1：重新挂载为读写（如果是临时问题）
mount -o remount,rw /

# 方法2：检查并修复文件系统（需要umount或单用户模式）
umount /dev/sda1
fsck -y /dev/sda1
mount /dev/sda1 /

# 方法3：如果是磁盘硬件问题
# 检查SMART
smartctl -a /dev/sda
# 如果有错误，尽快备份数据更换磁盘
```

## 5.2 文件系统损坏

### 排查

```bash
# 检查日志
dmesg | grep -i "ext4\|error\|corrupt"
journalctl -k | grep -i error

# 检查文件系统
# 在线检查（不修复）
sudo e2fsck -n /dev/sda1

# 强制检查（需要umount）
umount /dev/sda1
e2fsck -f -y /dev/sda1
```

### 修复

```bash
# 基本修复
fsck -y /dev/sda1

# 如果无法umount，使用单用户模式
# 1. 重启进入单用户模式
# 2. mount -o remount,ro /
# 3. fsck -y /dev/sda1
# 4. mount -o remount,rw /
# 5. reboot
```

---

# 六、LVM和RAID问题

## 6.1 LVM空间扩展

```bash
# 查看LVM状态
pvs  # 物理卷
vgs  # 卷组
lvs  # 逻辑卷

# 扩展逻辑卷
lvextend -L +10G /dev/vg0/lv0
# 或使用所有剩余空间
lvextend -l +100%FREE /dev/vg0/lv0

# 扩展文件系统
# ext4
resize2fs /dev/vg0/lv0

# xfs
xfs_growfs /dev/vg0/lv0
```

## 6.2 RAID状态检查

```bash
# 软RAID检查
cat /proc/mdstat

# 正常状态：[UU] 所有磁盘正常
# 异常状态：[U_] 有磁盘故障

# 查看详情
mdadm --detail /dev/md0

# 硬件RAID（以MegaRAID为例）
megacli -LDInfo -Lall -aALL
megacli -PDList -aALL
```

---

# 七、诊断脚本

## 7.1 磁盘综合诊断

```bash
#!/bin/bash
# disk_diagnose.sh - 磁盘综合诊断

echo "===== 磁盘诊断报告 ====="
echo "时间: $(date)"
echo ""

echo "--- 1. 磁盘使用率 ---"
df -h | awk 'NR==1 || $5+0>70'
echo ""

echo "--- 2. inode使用率 ---"
df -i | awk 'NR==1 || $5+0>70'
echo ""

echo "--- 3. 大目录 Top 10 ---"
du -sh /* 2>/dev/null | sort -hr | head -10
echo ""

echo "--- 4. 大文件 Top 10 ---"
find / -xdev -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -10
echo ""

echo "--- 5. 已删除未释放文件 ---"
lsof +L1 2>/dev/null | head -10
echo ""

echo "--- 6. IO统计 ---"
iostat -x 1 3 | tail -20
echo ""

echo "--- 7. 文件系统错误 ---"
dmesg | grep -i "error\|fail\|readonly" | tail -10
echo ""

echo "--- 8. SMART状态 ---"
for disk in /dev/sd?; do
    echo "=== $disk ==="
    smartctl -H $disk 2>/dev/null | grep -E "result|Status"
done
echo ""

echo "===== 诊断完成 ====="
```

## 7.2 磁盘空间告警脚本

```bash
#!/bin/bash
# disk_alert.sh - 磁盘空间告警

THRESHOLD=85
INODE_THRESHOLD=80
EMAIL="admin@example.com"

# 检查磁盘空间
df -h | awk -v t=$THRESHOLD 'NR>1 && $5+0 > t {
    print "DISK WARNING: " $6 " usage " $5
}'

# 检查inode
df -i | awk -v t=$INODE_THRESHOLD 'NR>1 && $5+0 > t {
    print "INODE WARNING: " $6 " usage " $5
}'

# 检查已删除未释放
DELETED_SIZE=$(lsof +L1 2>/dev/null | awk '/deleted/{sum+=$7} END{print sum/1024/1024/1024}')
if (( $(echo "$DELETED_SIZE > 1" | bc -l) )); then
    echo "DELETED FILES WARNING: ${DELETED_SIZE}GB not released"
fi
```

---

# 七、NFS存储问题排查

## 7.1 NFS挂载失败

### 诊断步骤

```bash
# 1. 检查NFS服务器是否可达
ping nfs-server
telnet nfs-server 2049

# 2. 检查NFS服务端口
rpcinfo -p nfs-server

# 输出示例：
#    program vers proto   port  service
#    100000    4   tcp    111  portmapper
#    100003    3   tcp   2049  nfs
#    100005    3   tcp  20048  mountd
#    100021    4   tcp  32769  nlockmgr

# 3. 查看NFS服务器导出列表
showmount -e nfs-server

# 4. 检查本地NFS客户端服务
systemctl status nfs-client.target
systemctl status rpcbind

# 5. 尝试手动挂载并查看详细错误
mount -v -t nfs nfs-server:/export/share /mnt/nfs

# 常见错误及解决：
# "mount.nfs: access denied" - 检查服务端exports权限
# "mount.nfs: Connection timed out" - 防火墙或网络问题
# "mount.nfs: No route to host" - 路由问题
```

### 服务端排查

```bash
# 检查exports配置
cat /etc/exports
# 格式：/export/share  client_ip(rw,sync,no_subtree_check)

# 重新导出
exportfs -ra

# 查看当前导出
exportfs -v

# 检查NFS服务
systemctl status nfs-server
systemctl status nfs-kernel-server  # Ubuntu

# 检查防火墙
firewall-cmd --list-all | grep -E "nfs|mountd|rpc"
# 需要开放：nfs(2049), mountd, rpcbind(111)
```

---

## 7.2 NFS性能问题

### 性能诊断

```bash
# 1. 检查NFS统计
nfsstat -c  # 客户端统计
nfsstat -s  # 服务端统计

# 关注指标：
# retrans   - 重传次数（高说明网络问题）
# badcalls  - 错误调用
# jukebox   - 服务器繁忙延迟

# 2. 检查RPC统计
nfsstat -r

# 3. 实时监控NFS IO
nfsiostat 1

# 输出：
# ops/s     rpc bklog
# 1000.0    0.00
#
# read:     ops/s  kB/s   avg RTT (ms)  avg exe (ms)
#           500.0  25000  1.5           2.0
# write:    ops/s  kB/s   avg RTT (ms)  avg exe (ms)
#           500.0  20000  2.0           3.0

# 4. 使用iostat查看NFS设备
iostat -x 1 | grep nfs
```

### 性能优化

```bash
# 挂载参数优化
mount -t nfs -o rw,hard,intr,rsize=1048576,wsize=1048576,timeo=600 \
    nfs-server:/export /mnt/nfs

# 参数说明：
# rsize/wsize  读写块大小（字节），建议1MB
# hard         硬挂载（推荐），服务器无响应时一直重试
# soft         软挂载，超时后返回错误
# intr         允许中断
# timeo        超时时间（0.1秒为单位）
# retrans      重试次数
# async        异步写入（性能好但有数据丢失风险）
# sync         同步写入（安全但性能差）
# noatime      不更新访问时间

# /etc/fstab 持久化配置
# nfs-server:/export /mnt/nfs nfs rw,hard,intr,rsize=1048576,wsize=1048576 0 0

# 服务端优化
# 增加NFS线程数
# /etc/nfs.conf 或 /etc/default/nfs-kernel-server
# RPCNFSDCOUNT=32
```

---

## 7.3 NFS Stale File Handle

### 问题现象

```bash
# 访问NFS文件时报错
ls /mnt/nfs/
# ls: cannot access '/mnt/nfs/': Stale file handle

cat /mnt/nfs/file
# cat: /mnt/nfs/file: Stale file handle
```

### 原因与解决

```bash
# 常见原因：
# 1. 服务端重启或重新导出
# 2. 服务端文件/目录被删除重建
# 3. 服务端导出路径变化

# 解决方法1：重新挂载
umount -f /mnt/nfs
mount -t nfs nfs-server:/export /mnt/nfs

# 如果umount失败（设备忙）
umount -l /mnt/nfs  # 懒卸载
# 或
fuser -km /mnt/nfs  # 杀死使用该挂载点的进程
umount /mnt/nfs

# 解决方法2：服务端重新导出
exportfs -ra

# 预防措施：
# 使用autofs自动挂载
apt install autofs
# /etc/auto.master
# /mnt/nfs  /etc/auto.nfs
# /etc/auto.nfs
# share  -rw,hard,intr  nfs-server:/export/share
```

---

# 八、Ceph存储问题排查

## 8.1 Ceph集群健康检查

### 基础状态检查

```bash
# 集群状态概览
ceph status
# 或
ceph -s

# 输出示例：
#   cluster:
#     id:     xxxx-xxxx-xxxx
#     health: HEALTH_WARN
#             1 osds down
#
#   services:
#     mon: 3 daemons, quorum a,b,c
#     mgr: a(active)
#     osd: 12 osds: 11 up, 12 in
#
#   data:
#     pools:   3 pools, 128 pgs
#     objects: 10k objects, 100 GiB
#     usage:   300 GiB used, 1 TiB / 1.3 TiB avail
#     pgs:     128 active+clean

# 健康状态详情
ceph health detail

# 集群日志
ceph log last 50
```

### 状态说明

```bash
# 健康状态：
# HEALTH_OK    - 集群健康
# HEALTH_WARN  - 有警告（需关注）
# HEALTH_ERR   - 有错误（需立即处理）

# 常见警告：
# "X osds down"              - OSD宕机
# "X pgs degraded"           - PG降级（副本不足）
# "X pgs undersized"         - PG副本数不足
# "X pgs stuck unclean"      - PG无法清理
# "X nearfull osd(s)"        - OSD接近满
# "clock skew detected"      - 时钟不同步
```

---

## 8.2 OSD问题排查

### OSD状态检查

```bash
# 查看所有OSD状态
ceph osd tree

# 输出示例：
# ID  CLASS  WEIGHT   TYPE NAME       STATUS  REWEIGHT  PRI-AFF
# -1         12.00000 root default
# -3          4.00000     host node1
#  0    hdd   1.00000         osd.0       up   1.00000  1.00000
#  1    hdd   1.00000         osd.1     down   1.00000  1.00000  ← 问题OSD
#  2    hdd   1.00000         osd.2       up   1.00000  1.00000

# 查看特定OSD状态
ceph osd status

# 查看OSD详细信息
ceph osd dump | grep osd.1

# 查看OSD使用率
ceph osd df

# 输出：
# ID  CLASS  WEIGHT   REWEIGHT  SIZE    RAW USE  DATA     OMAP    META     AVAIL   %USE
#  0    hdd  1.00000   1.00000  1.0 TiB  100 GiB   90 GiB    1 GiB   9 GiB  900 GiB  10.00
```

### OSD故障处理

```bash
# OSD down的排查

# 1. 检查OSD进程
systemctl status ceph-osd@1
journalctl -u ceph-osd@1 -n 50

# 2. 检查磁盘
lsblk
smartctl -a /dev/sdX

# 3. 尝试启动OSD
systemctl start ceph-osd@1

# 4. 如果OSD磁盘故障，需要替换

# 标记OSD为out（开始数据迁移）
ceph osd out osd.1

# 停止OSD
systemctl stop ceph-osd@1

# 从集群移除
ceph osd purge osd.1 --yes-i-really-mean-it

# 添加新OSD
ceph-volume lvm create --data /dev/sdX
```

---

## 8.3 PG问题排查

### PG状态检查

```bash
# 查看PG状态统计
ceph pg stat

# 输出：128 pgs: 128 active+clean; 100 GiB data, 300 GiB used, 1 TiB / 1.3 TiB avail

# 查看异常PG
ceph pg dump_stuck

# 类型：
# inactive  - 不活跃
# unclean   - 不干净
# stale     - 过期
# undersized - 副本不足
# degraded  - 降级

# 查看特定PG详情
ceph pg 1.a query

# 查看PG分布
ceph pg ls-by-osd osd.0
```

### PG问题处理

```bash
# PG degraded（降级）
# 通常是OSD down导致，恢复OSD后自动修复

# 检查恢复进度
ceph -w
# 或
ceph pg stat

# PG stuck（卡住）
# 查看原因
ceph health detail

# 强制恢复（谨慎使用）
ceph pg repair <pg_id>

# PG不均衡
# 查看分布
ceph osd df tree

# 手动rebalance
ceph osd reweight-by-utilization
```

---

## 8.4 Ceph性能问题

### 性能监控

```bash
# 查看集群IO
ceph -s | grep io

# 查看OSD性能
ceph osd perf

# 输出：
# osd  commit_latency(ms)  apply_latency(ms)
#  0                    1                  2
#  1                   50                 55  ← 延迟高

# 查看Pool IO
ceph osd pool stats

# 实时监控
ceph daemon osd.0 perf dump
```

### 性能优化

```bash
# 1. 检查网络
# Ceph需要两个网络：public和cluster
ceph config get osd.0 public_network
ceph config get osd.0 cluster_network

# 2. 检查OSD日志是否在SSD
# 建议：数据盘HDD，日志盘SSD

# 3. 调整PG数量
# 计算公式：PGs = (OSDs * 100) / 副本数，向上取2的幂
ceph osd pool set <pool> pg_num 256
ceph osd pool set <pool> pgp_num 256

# 4. 启用缓存池
ceph osd tier add <base-pool> <cache-pool>
ceph osd tier cache-mode <cache-pool> writeback
```

---

## 8.5 Ceph诊断脚本

```bash
#!/bin/bash
# ceph_diagnose.sh - Ceph集群诊断

echo "===== Ceph集群诊断 ====="
echo "时间: $(date)"
echo ""

echo "--- 1. 集群状态 ---"
ceph -s
echo ""

echo "--- 2. 健康详情 ---"
ceph health detail 2>/dev/null | head -20
echo ""

echo "--- 3. OSD状态 ---"
ceph osd tree | head -30
echo ""

echo "--- 4. OSD使用率 ---"
ceph osd df | awk 'NR<=1 || $8+0>70'
echo ""

echo "--- 5. 异常PG ---"
ceph pg dump_stuck 2>/dev/null | head -10
echo ""

echo "--- 6. OSD延迟 ---"
ceph osd perf | awk 'NR<=1 || $2>10 || $3>10'
echo ""

echo "--- 7. 最近日志 ---"
ceph log last 10
echo ""

echo "===== 诊断完成 ====="
```

---

# 九、分布式存储通用排查

## 9.1 常见分布式存储对比

| 存储 | 检查命令 | 常见问题 |
|------|----------|----------|
| NFS | `showmount -e`, `nfsstat` | Stale handle, 性能 |
| Ceph | `ceph -s`, `ceph health` | OSD down, PG异常 |
| GlusterFS | `gluster volume status` | Brick offline, Split-brain |
| MinIO | `mc admin info` | 节点离线, 纠删码问题 |

## 9.2 分布式存储排查要点

```bash
# 1. 集群成员状态
# - 节点是否在线
# - 服务是否正常

# 2. 数据一致性
# - 副本是否完整
# - 是否有数据修复进行中

# 3. 网络连通性
# - 节点间网络
# - 客户端到存储网络

# 4. 性能瓶颈
# - 磁盘IO
# - 网络带宽
# - CPU/内存

# 5. 容量规划
# - 当前使用率
# - 增长趋势
```

---

# 十、IO调度器与块设备调优

## 10.1 IO调度器介绍

```bash
# Linux IO调度器（单队列，已过时）
# - CFQ (Completely Fair Queuing) - 公平调度，适合桌面
# - Deadline - 保证延迟，适合数据库
# - Noop - 无调度，适合SSD/虚拟机

# Linux IO调度器（多队列，现代内核）
# - mq-deadline - 多队列版deadline，通用推荐
# - bfq (Budget Fair Queueing) - 低延迟，适合桌面/交互应用
# - kyber - 低延迟，适合快速设备（NVMe）
# - none - 无调度，适合NVMe/虚拟机

# 查看当前IO调度器
cat /sys/block/sda/queue/scheduler
# 输出示例：[mq-deadline] kyber bfq none

# 查看所有块设备的调度器
for disk in /sys/block/sd* /sys/block/nvme*; do
    [ -d "$disk" ] && echo "$(basename $disk): $(cat $disk/queue/scheduler 2>/dev/null)"
done
```

## 10.2 选择IO调度器

```bash
# 推荐配置：

# HDD机械硬盘：mq-deadline 或 bfq
# - mq-deadline: 数据库、服务器负载
# - bfq: 桌面、混合负载

# SSD固态硬盘：mq-deadline 或 none
# - mq-deadline: 需要一些公平性
# - none: 追求极致性能

# NVMe：none 或 kyber
# - none: 设备足够快，调度开销反而有害
# - kyber: 需要低延迟保证

# 虚拟机：none
# - 宿主机已经做了调度

# 临时修改（重启失效）
echo mq-deadline > /sys/block/sda/queue/scheduler

# 永久修改（udev规则）
# /etc/udev/rules.d/60-io-scheduler.rules
# HDD使用mq-deadline
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="mq-deadline"
# SSD使用none
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="none"
# NVMe使用none
ACTION=="add|change", KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="none"

# 应用udev规则
udevadm control --reload-rules
udevadm trigger
```

## 10.3 块设备队列参数

```bash
# 查看队列参数
cat /sys/block/sda/queue/nr_requests      # 请求队列深度
cat /sys/block/sda/queue/read_ahead_kb    # 预读大小
cat /sys/block/sda/queue/max_sectors_kb   # 单次IO最大扇区数
cat /sys/block/sda/queue/rotational       # 0=SSD, 1=HDD

# 调整队列深度
# 默认128，对于高IOPS设备可以增加
echo 256 > /sys/block/sda/queue/nr_requests

# 调整预读大小
# 顺序读取场景增大，随机读取场景减小
echo 4096 > /sys/block/sda/queue/read_ahead_kb  # 4MB

# 数据库场景优化
echo 128 > /sys/block/sda/queue/nr_requests
echo 256 > /sys/block/sda/queue/read_ahead_kb

# 流媒体/大文件场景
echo 256 > /sys/block/sda/queue/nr_requests
echo 8192 > /sys/block/sda/queue/read_ahead_kb
```

## 10.4 高级IO调优

```bash
# 1. 合并IO请求（提高吞吐量）
cat /sys/block/sda/queue/nomerges
# 0=允许合并（默认），2=禁用合并
# 随机IO场景可考虑禁用
echo 2 > /sys/block/sda/queue/nomerges

# 2. 查看IO统计
cat /sys/block/sda/stat
# 字段说明（空格分隔）：
# 1 读完成次数
# 2 读合并次数
# 3 读扇区数
# 4 读花费毫秒数
# 5 写完成次数
# 6 写合并次数
# 7 写扇区数
# 8 写花费毫秒数
# 9 当前进行中的IO
# 10 花费在IO的毫秒数
# 11 加权IO毫秒数

# 3. 关闭NCQ（解决部分SSD问题）
# 有些SSD的NCQ实现有bug
echo 1 > /sys/block/sda/device/queue_depth

# 4. SSD TRIM配置
# 检查TRIM支持
lsblk --discard
# DISC-GRAN和DISC-MAX非0表示支持

# 启用discard（实时TRIM）- 可能影响性能
# /etc/fstab
/dev/sda1 / ext4 defaults,discard 0 1

# 或使用fstrim定期TRIM（推荐）
fstrim -v /
# 设置定时任务
systemctl enable fstrim.timer
```

## 10.5 IO调优诊断脚本

```bash
#!/bin/bash
# io_tuning_check.sh - IO调优检查脚本

echo "===== IO调优检查 ====="
echo "时间: $(date)"
echo ""

for disk in /sys/block/sd* /sys/block/nvme*; do
    [ ! -d "$disk" ] && continue
    NAME=$(basename $disk)
    
    echo "--- 设备: $NAME ---"
    
    # 设备类型
    ROTATIONAL=$(cat $disk/queue/rotational 2>/dev/null)
    if [ "$ROTATIONAL" == "1" ]; then
        echo "类型: HDD（机械硬盘）"
    else
        echo "类型: SSD/NVMe（固态）"
    fi
    
    # 调度器
    SCHEDULER=$(cat $disk/queue/scheduler 2>/dev/null)
    echo "调度器: $SCHEDULER"
    
    # 队列参数
    echo "队列深度: $(cat $disk/queue/nr_requests 2>/dev/null)"
    echo "预读大小: $(cat $disk/queue/read_ahead_kb 2>/dev/null) KB"
    
    # 建议
    if [ "$ROTATIONAL" == "1" ]; then
        if ! echo "$SCHEDULER" | grep -q "\[mq-deadline\]\|\[bfq\]"; then
            echo "建议: HDD建议使用mq-deadline或bfq调度器"
        fi
    else
        if ! echo "$SCHEDULER" | grep -q "\[none\]\|\[mq-deadline\]"; then
            echo "建议: SSD建议使用none或mq-deadline调度器"
        fi
    fi
    
    echo ""
done

echo "--- 系统级IO参数 ---"
echo "vm.dirty_ratio: $(sysctl -n vm.dirty_ratio)"
echo "vm.dirty_background_ratio: $(sysctl -n vm.dirty_background_ratio)"
echo "vm.dirty_expire_centisecs: $(sysctl -n vm.dirty_expire_centisecs)"
echo ""

echo "===== 检查完成 ====="
```

---

## 总结

| 问题 | 快速诊断 | 解决方法 |
|------|----------|----------|
| 磁盘满 | `df -h`, `du -sh /*` | 清理大文件/日志 |
| df/du不符 | `lsof +L1` | 重启进程释放文件 |
| inode耗尽 | `df -i`, `find \| wc -l` | 清理小文件 |
| IO高 | `iostat -x`, `iotop` | 优化IO/换SSD |
| IO延迟高 | `iostat`(await) | 调整调度器/队列深度 |
| 只读 | `dmesg`, `mount` | `fsck`修复 |
| NFS挂载失败 | `showmount -e`, `rpcinfo` | 检查exports和防火墙 |
| NFS Stale | `umount -f && mount` | 重新挂载 |
| Ceph OSD Down | `ceph osd tree` | 检查并恢复OSD |
| Ceph PG异常 | `ceph pg dump_stuck` | 等待恢复或手动修复 |

**IO调度器速查**：
| 设备类型 | 推荐调度器 | 适用场景 |
|----------|------------|----------|
| HDD | mq-deadline | 数据库、服务器 |
| HDD | bfq | 桌面、混合负载 |
| SSD | none/mq-deadline | 通用 |
| NVMe | none/kyber | 高性能 |
| 虚拟机 | none | 避免双重调度 |

**排查三板斧**：
1. **df/du** - 确认空间使用情况
2. **lsof** - 检查已删除未释放文件
3. **iostat/iotop** - 分析IO问题

**关键记忆**：
1. `df` 和 `du` 不一致首先查 `lsof +L1`
2. inode问题找小文件最多的目录
3. IO问题关注 `%util` 和 `await`
4. SSD建议使用none调度器，HDD用mq-deadline
5. NFS问题先查服务端exports和防火墙
6. Ceph问题先看 `ceph -s` 和 `ceph health detail`
