+++
title = "备份恢复实战"
date = 2026-01-21
weight = 47000
description = "SRE备份恢复完整指南：数据备份策略、灾难恢复演练、数据一致性验证"
[taxonomies]
tags = ["SRE", "备份", "恢复", "灾难恢复", "实战"]
+++

## 概述

备份恢复是数据安全的最后防线。本文详细介绍各类系统的备份恢复方法和灾难恢复演练流程。

---

# 一、备份策略基础

## 1.1 备份类型

```
备份类型：

1. 全量备份（Full Backup）
   - 备份所有数据
   - 恢复简单快速
   - 占用空间大，耗时长

2. 增量备份（Incremental Backup）
   - 只备份上次备份后变化的数据
   - 占用空间小，速度快
   - 恢复需要全量+所有增量

3. 差异备份（Differential Backup）
   - 备份上次全量备份后变化的数据
   - 恢复需要全量+最近差异
   - 空间介于全量和增量之间

常见策略：
- 每周全量 + 每日增量
- 每月全量 + 每周差异 + 每日增量
- 实时复制 + 定期快照
```

## 1.2 3-2-1原则

```
3-2-1 备份原则：

3 - 至少3份数据副本
    ├── 1份生产数据
    ├── 1份本地备份
    └── 1份异地备份

2 - 存储在2种不同介质
    ├── 磁盘
    └── 磁带/云存储

1 - 至少1份异地存储
    └── 不同地理位置
```

---

# 二、文件系统备份

## 2.1 tar备份

```bash
# 基础备份
tar -czvf backup.tar.gz /path/to/data

# 参数详解：
# -c  创建归档
# -z  gzip压缩
# -v  详细输出
# -f  指定文件名
# -p  保留权限
# -x  解压
# -t  列出内容

# 完整备份（保留权限和属性）
tar -cvpzf backup-$(date +%Y%m%d).tar.gz \
    --exclude=/proc \
    --exclude=/sys \
    --exclude=/dev \
    --exclude=/tmp \
    --exclude=/backup \
    /

# 增量备份
# 首次备份（记录快照）
tar -cvpzf backup-full.tar.gz \
    --listed-incremental=/backup/snapshot.snar \
    /data

# 增量备份（使用相同快照文件）
tar -cvpzf backup-incr-$(date +%Y%m%d).tar.gz \
    --listed-incremental=/backup/snapshot.snar \
    /data

# 恢复
tar -xvpzf backup.tar.gz -C /restore/path

# 列出备份内容
tar -tzvf backup.tar.gz
```

## 2.2 rsync同步

```bash
# 基础同步
rsync -avz /source/ /destination/

# 参数详解：
# -a  归档模式（保留权限、时间等）
# -v  详细输出
# -z  压缩传输
# -r  递归
# -P  显示进度
# --delete  删除目标中源不存在的文件
# --exclude  排除文件

# 完整备份
rsync -avzP --delete \
    --exclude '.cache' \
    --exclude '*.tmp' \
    /data/ /backup/data/

# 远程备份
rsync -avzP -e "ssh -p 22" \
    /data/ user@remote:/backup/data/

# 带宽限制
rsync -avzP --bwlimit=10000 /data/ /backup/data/
# 限制10MB/s

# 增量备份（使用硬链接）
rsync -avzP --delete \
    --link-dest=/backup/yesterday \
    /data/ /backup/today/

# 验证备份
rsync -avzn /data/ /backup/data/
# -n 只检查不执行

# 恢复
rsync -avzP /backup/data/ /data/
```

## 2.3 备份脚本示例

```bash
#!/bin/bash
# file_backup.sh - 文件备份脚本

# 配置
SOURCE_DIR="/data"
BACKUP_DIR="/backup"
REMOTE_HOST="backup-server"
REMOTE_DIR="/remote-backup"
RETENTION_DAYS=30

DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/backup/backup_${DATE}.log"

# 创建日志目录
mkdir -p $(dirname $LOG_FILE)

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 开始备份
log "开始备份..."

# 本地备份
log "执行本地备份..."
BACKUP_FILE="${BACKUP_DIR}/backup_${DATE}.tar.gz"

tar -cvpzf $BACKUP_FILE \
    --exclude='*.tmp' \
    --exclude='*.log' \
    $SOURCE_DIR >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    log "本地备份完成: $BACKUP_FILE"
    SIZE=$(du -h $BACKUP_FILE | cut -f1)
    log "备份大小: $SIZE"
else
    log "错误: 本地备份失败"
    exit 1
fi

# 远程同步
log "同步到远程服务器..."
rsync -avzP $BACKUP_FILE ${REMOTE_HOST}:${REMOTE_DIR}/ >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    log "远程同步完成"
else
    log "警告: 远程同步失败"
fi

# 清理旧备份
log "清理${RETENTION_DAYS}天前的备份..."
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS -exec rm {} \;

log "备份完成"

# 验证备份
log "验证备份文件..."
tar -tzf $BACKUP_FILE > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log "备份验证通过"
else
    log "错误: 备份文件损坏"
    exit 1
fi
```

---

# 三、数据库备份

## 3.1 MySQL备份

### mysqldump

```bash
# 完整备份
mysqldump -u root -p \
    --all-databases \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    > backup_$(date +%Y%m%d).sql

# 参数详解：
# --all-databases       所有数据库
# --single-transaction  一致性备份（InnoDB）
# --routines            包含存储过程
# --triggers            包含触发器
# --events              包含事件
# --master-data=2       记录binlog位置（主从复制）
# --flush-logs          刷新日志

# 备份单个数据库
mysqldump -u root -p mydb > mydb_backup.sql

# 备份特定表
mysqldump -u root -p mydb table1 table2 > tables_backup.sql

# 只备份结构
mysqldump -u root -p --no-data mydb > schema_backup.sql

# 压缩备份
mysqldump -u root -p mydb | gzip > mydb_$(date +%Y%m%d).sql.gz

# 恢复
mysql -u root -p mydb < backup.sql
gunzip < backup.sql.gz | mysql -u root -p mydb

# 查看备份内容
head -100 backup.sql
zcat backup.sql.gz | head -100
```

### xtrabackup（物理备份）

```bash
# 安装
apt install percona-xtrabackup-80

# 全量备份
xtrabackup --backup --target-dir=/backup/full \
    --user=root --password=xxx

# 增量备份
xtrabackup --backup --target-dir=/backup/incr1 \
    --incremental-basedir=/backup/full \
    --user=root --password=xxx

# 准备恢复（全量）
xtrabackup --prepare --target-dir=/backup/full

# 准备恢复（增量）
xtrabackup --prepare --apply-log-only --target-dir=/backup/full
xtrabackup --prepare --target-dir=/backup/full \
    --incremental-dir=/backup/incr1

# 恢复
systemctl stop mysql
rm -rf /var/lib/mysql/*
xtrabackup --copy-back --target-dir=/backup/full
chown -R mysql:mysql /var/lib/mysql
systemctl start mysql
```

### Binlog增量恢复

```bash
# 查看binlog
mysqlbinlog mysql-bin.000001 | head -100

# 按时间恢复
mysqlbinlog --start-datetime="2024-01-21 10:00:00" \
            --stop-datetime="2024-01-21 12:00:00" \
            mysql-bin.000001 | mysql -u root -p

# 按位置恢复
mysqlbinlog --start-position=1000 \
            --stop-position=5000 \
            mysql-bin.000001 | mysql -u root -p

# 跳过错误事务
mysqlbinlog --start-position=1000 \
            --stop-position=2000 \
            mysql-bin.000001 > partial.sql
# 编辑partial.sql删除错误语句
mysql -u root -p < partial.sql
```

---

## 3.2 PostgreSQL备份

### pg_dump

```bash
# 完整备份
pg_dump -U postgres -Fc mydb > mydb_backup.dump

# 格式说明：
# -Fc  自定义格式（推荐，可并行恢复）
# -Ft  tar格式
# -Fp  纯文本SQL
# -Fd  目录格式（可并行）

# 备份所有数据库
pg_dumpall -U postgres > all_backup.sql

# 并行备份（目录格式）
pg_dump -U postgres -Fd -j 4 -f /backup/mydb mydb

# 恢复
pg_restore -U postgres -d mydb mydb_backup.dump

# 并行恢复
pg_restore -U postgres -d mydb -j 4 /backup/mydb

# 创建新数据库并恢复
createdb -U postgres newdb
pg_restore -U postgres -d newdb mydb_backup.dump

# 只恢复数据
pg_restore -U postgres -d mydb --data-only mydb_backup.dump

# 只恢复结构
pg_restore -U postgres -d mydb --schema-only mydb_backup.dump
```

### pg_basebackup（物理备份）

```bash
# 全量备份
pg_basebackup -U postgres -D /backup/base \
    -Fp -Xs -P

# 参数：
# -Fp  plain格式
# -Ft  tar格式
# -Xs  流式WAL
# -P   显示进度

# 带WAL归档
pg_basebackup -U postgres -D /backup/base \
    -Ft -z -Xs -P

# 恢复
# 1. 停止PostgreSQL
systemctl stop postgresql

# 2. 清理数据目录
rm -rf /var/lib/postgresql/data/*

# 3. 恢复备份
tar -xvf base.tar -C /var/lib/postgresql/data/

# 4. 创建恢复配置
touch /var/lib/postgresql/data/recovery.signal

# 5. 配置恢复参数（postgresql.conf）
# restore_command = 'cp /backup/wal/%f %p'
# recovery_target_time = '2024-01-21 12:00:00'

# 6. 启动PostgreSQL
chown -R postgres:postgres /var/lib/postgresql/data
systemctl start postgresql
```

---

## 3.3 Redis备份

```bash
# RDB备份
# 触发备份
redis-cli BGSAVE

# 查看备份状态
redis-cli LASTSAVE

# 复制RDB文件
cp /var/lib/redis/dump.rdb /backup/redis/dump_$(date +%Y%m%d).rdb

# 恢复
systemctl stop redis
cp /backup/redis/dump.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb
systemctl start redis

# AOF备份
cp /var/lib/redis/appendonly.aof /backup/redis/

# 重写AOF（压缩）
redis-cli BGREWRITEAOF

# 验证AOF
redis-check-aof /var/lib/redis/appendonly.aof

# 修复损坏的AOF
redis-check-aof --fix /var/lib/redis/appendonly.aof
```

---

# 四、灾难恢复

## 4.1 恢复流程

```
灾难恢复流程：

1. 评估损失
   ├── 确定故障范围
   ├── 评估数据丢失
   └── 确定恢复目标（RPO/RTO）

2. 准备恢复环境
   ├── 准备硬件/云资源
   ├── 安装操作系统
   └── 安装必要软件

3. 恢复数据
   ├── 获取备份文件
   ├── 验证备份完整性
   └── 执行恢复

4. 验证恢复
   ├── 数据一致性检查
   ├── 应用功能测试
   └── 性能测试

5. 切换服务
   ├── 更新DNS/负载均衡
   ├── 通知相关方
   └── 监控服务状态
```

## 4.2 恢复演练

### 演练计划模板

```markdown
## 灾难恢复演练计划

### 基本信息
- 演练日期：YYYY-MM-DD
- 演练时间：HH:MM - HH:MM
- 参与人员：XXX
- 演练场景：数据库主库故障

### 演练目标
- 验证备份可恢复性
- 验证恢复流程
- 测量RTO（恢复时间目标）

### 演练步骤

1. [ ] 准备阶段（10分钟）
   - 确认备份文件存在
   - 准备恢复环境
   - 记录开始时间

2. [ ] 恢复阶段（30分钟）
   - 执行恢复操作
   - 记录每步耗时

3. [ ] 验证阶段（20分钟）
   - 数据一致性检查
   - 应用连接测试
   - 功能测试

4. [ ] 总结阶段（10分钟）
   - 记录总耗时
   - 记录问题
   - 改进建议

### 成功标准
- 数据完整恢复
- 应用正常运行
- RTO < 1小时
```

### 恢复验证脚本

```bash
#!/bin/bash
# recovery_verify.sh - 恢复验证脚本

echo "===== 数据库恢复验证 ====="
echo "时间: $(date)"
echo ""

# MySQL验证
verify_mysql() {
    echo "--- MySQL验证 ---"
    
    # 连接测试
    mysql -u root -p$MYSQL_PASS -e "SELECT 1" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ 连接正常"
    else
        echo "✗ 连接失败"
        return 1
    fi
    
    # 数据库列表
    DBS=$(mysql -u root -p$MYSQL_PASS -e "SHOW DATABASES" 2>/dev/null | tail -n+2)
    echo "数据库: $DBS"
    
    # 表数量
    for db in $DBS; do
        if [[ "$db" != "information_schema" && "$db" != "performance_schema" && "$db" != "mysql" && "$db" != "sys" ]]; then
            COUNT=$(mysql -u root -p$MYSQL_PASS -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$db'" 2>/dev/null | tail -1)
            echo "  $db: $COUNT 张表"
        fi
    done
    
    # 数据校验（示例）
    CHECKSUM=$(mysql -u root -p$MYSQL_PASS -e "CHECKSUM TABLE mydb.users" 2>/dev/null | tail -1 | awk '{print $2}')
    echo "users表校验和: $CHECKSUM"
}

# PostgreSQL验证
verify_postgresql() {
    echo "--- PostgreSQL验证 ---"
    
    # 连接测试
    psql -U postgres -c "SELECT 1" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ 连接正常"
    else
        echo "✗ 连接失败"
        return 1
    fi
    
    # 数据库列表
    psql -U postgres -c "\l"
    
    # 表数量
    psql -U postgres -d mydb -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'"
}

# 文件系统验证
verify_files() {
    echo "--- 文件系统验证 ---"
    
    # 文件数量
    FILE_COUNT=$(find /data -type f | wc -l)
    echo "文件数量: $FILE_COUNT"
    
    # 目录大小
    DIR_SIZE=$(du -sh /data | cut -f1)
    echo "目录大小: $DIR_SIZE"
    
    # 关键文件检查
    for file in /data/config.yaml /data/important.dat; do
        if [ -f "$file" ]; then
            echo "✓ $file 存在"
        else
            echo "✗ $file 缺失"
        fi
    done
}

# 执行验证
verify_mysql
echo ""
verify_files
echo ""

echo "===== 验证完成 ====="
```

---

## 4.3 备份监控

```bash
#!/bin/bash
# backup_monitor.sh - 备份监控脚本

BACKUP_DIR="/backup"
MAX_AGE_HOURS=25
MIN_SIZE_MB=100
ALERT_EMAIL="admin@example.com"

echo "===== 备份监控检查 ====="
echo "时间: $(date)"

# 检查最新备份
LATEST=$(ls -t $BACKUP_DIR/*.tar.gz 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "错误: 未找到备份文件"
    # 发送告警
    echo "备份告警: 未找到备份文件" | mail -s "备份告警" $ALERT_EMAIL
    exit 1
fi

echo "最新备份: $LATEST"

# 检查备份时间
FILE_AGE_HOURS=$(( ( $(date +%s) - $(stat -c %Y "$LATEST") ) / 3600 ))
echo "备份年龄: ${FILE_AGE_HOURS}小时"

if [ $FILE_AGE_HOURS -gt $MAX_AGE_HOURS ]; then
    echo "警告: 备份超过${MAX_AGE_HOURS}小时"
    echo "备份告警: 备份过期 ${FILE_AGE_HOURS}小时" | mail -s "备份告警" $ALERT_EMAIL
fi

# 检查备份大小
FILE_SIZE_MB=$(( $(stat -c %s "$LATEST") / 1024 / 1024 ))
echo "备份大小: ${FILE_SIZE_MB}MB"

if [ $FILE_SIZE_MB -lt $MIN_SIZE_MB ]; then
    echo "警告: 备份文件过小"
    echo "备份告警: 备份文件过小 ${FILE_SIZE_MB}MB" | mail -s "备份告警" $ALERT_EMAIL
fi

# 验证备份完整性
tar -tzf "$LATEST" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ 备份文件完整"
else
    echo "✗ 备份文件损坏"
    echo "备份告警: 备份文件损坏" | mail -s "备份告警" $ALERT_EMAIL
fi

echo "===== 检查完成 ====="
```

---

## 总结

### 备份命令速查

| 类型 | 备份 | 恢复 |
|------|------|------|
| 文件 | `tar -czvf` / `rsync -avz` | `tar -xzvf` / `rsync` |
| MySQL | `mysqldump` / `xtrabackup` | `mysql <` / `xtrabackup --copy-back` |
| PostgreSQL | `pg_dump` / `pg_basebackup` | `pg_restore` |
| Redis | `BGSAVE` | 复制dump.rdb |

### 关键指标

| 指标 | 说明 |
|------|------|
| RPO | Recovery Point Objective，可接受的数据丢失量 |
| RTO | Recovery Time Objective，恢复时间目标 |

### 备份检查清单

```markdown
□ 备份是否按计划执行
□ 备份文件大小是否正常
□ 备份文件是否可以解压/恢复
□ 异地备份是否同步
□ 定期恢复演练
□ 备份加密（敏感数据）
□ 备份保留策略执行
```

**备份三原则**：
1. **3-2-1原则** - 3份副本，2种介质，1份异地
2. **定期验证** - 备份不验证等于没备份
3. **演练恢复** - 只有演练过的流程才可靠

**关键记忆**：
1. mysqldump加--single-transaction保证一致性
2. xtrabackup需要prepare才能恢复
3. pg_dump -Fc格式支持并行恢复
4. 恢复前先验证备份完整性

---

## 相关文章

- [上一篇：缓存问题排查实战](@/articles/sre/sre-46-缓存问题排查实战.md)
- [下一篇：配置管理问题排查实战](@/articles/sre/sre-48-配置管理问题排查实战.md)
