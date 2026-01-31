+++
title = "42.系统启动与引导问题排查实战"
date = 2026-01-21
description = "SRE系统启动问题排查完整指南：GRUB修复、启动失败、initramfs问题的定位与解决"
[taxonomies]
tags = ["SRE", "启动", "GRUB", "systemd", "排查", "实战"]
+++

## 概述

系统无法启动是最紧急的故障之一。本文详细介绍Linux系统启动问题的排查方法和修复技巧。

---

# 一、Linux启动流程

## 1.1 启动阶段概述

```
Linux启动流程：

1. BIOS/UEFI
   └─→ 硬件自检（POST）
       └─→ 找到启动设备

2. Boot Loader (GRUB)
   └─→ 加载内核和initramfs
       └─→ 传递启动参数

3. 内核启动
   └─→ 解压initramfs
       └─→ 执行init进程

4. Init系统 (systemd)
   └─→ 挂载文件系统
       └─→ 启动服务
           └─→ 到达目标运行级别

5. 登录界面
   └─→ tty/getty 或 Display Manager
```

## 1.2 各阶段常见问题

```
阶段           常见问题                      表现
─────────────────────────────────────────────────────
BIOS/UEFI     硬件故障、启动顺序错误        无任何显示
GRUB          配置错误、MBR损坏             GRUB rescue提示
内核          内核崩溃、驱动问题            Kernel panic
initramfs     缺少驱动、配置错误            无法挂载根文件系统
systemd       服务失败、依赖问题            卡在某个服务
文件系统      损坏、满了                    只读挂载、fsck提示
```

---

# 二、GRUB问题排查

## 2.1 GRUB救援模式

### 进入GRUB命令行

```bash
# 启动时按住Shift或连按Esc进入GRUB菜单
# 在菜单项上按'e'编辑启动参数
# 按'c'进入GRUB命令行

# GRUB命令行基本命令
grub> ls
# (hd0) (hd0,gpt1) (hd0,gpt2) ...
# 列出可用分区

grub> ls (hd0,gpt2)/
# 查看分区内容

grub> cat (hd0,gpt2)/etc/os-release
# 读取文件内容

grub> set
# 显示当前变量

grub> set root=(hd0,gpt2)
# 设置根分区

grub> linux /boot/vmlinuz-xxx root=/dev/sda2
# 加载内核

grub> initrd /boot/initrd.img-xxx
# 加载initramfs

grub> boot
# 启动系统
```

### GRUB救援模式修复

```bash
# 如果看到 "grub rescue>"

# 1. 找到boot分区
grub rescue> ls
grub rescue> ls (hd0,gpt2)/boot
# 找到包含vmlinuz的分区

# 2. 设置前缀和根
grub rescue> set prefix=(hd0,gpt2)/boot/grub
grub rescue> set root=(hd0,gpt2)

# 3. 加载normal模块
grub rescue> insmod normal
grub rescue> normal

# 这应该会回到正常GRUB菜单
# 然后进入系统后重新安装GRUB
```

## 2.2 重新安装GRUB

### 从Live CD修复

```bash
# 1. 从Live CD/USB启动

# 2. 挂载系统分区
mount /dev/sda2 /mnt          # 根分区
mount /dev/sda1 /mnt/boot/efi # EFI分区（UEFI系统）

# 3. 绑定挂载
mount --bind /dev /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
mount --bind /run /mnt/run

# 4. chroot
chroot /mnt

# 5. 重新安装GRUB
# BIOS系统
grub-install /dev/sda
update-grub

# UEFI系统
grub-install --target=x86_64-efi --efi-directory=/boot/efi
update-grub

# 6. 退出并重启
exit
umount -R /mnt
reboot
```

### 修复GRUB配置

```bash
# 重新生成GRUB配置
update-grub              # Debian/Ubuntu
grub2-mkconfig -o /boot/grub2/grub.cfg  # CentOS/RHEL

# 检查配置
cat /boot/grub/grub.cfg

# 修复常见问题
# 1. root UUID错误
blkid  # 查看分区UUID
# 编辑 /etc/default/grub 或直接编辑 grub.cfg

# 2. 内核参数问题
# /etc/default/grub
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
# 然后 update-grub
```

---

# 三、内核启动问题

## 3.1 Kernel Panic

### 分析Kernel Panic

```
常见Kernel Panic信息：

1. VFS: Unable to mount root fs
   原因：找不到根文件系统
   解决：检查root参数、initramfs

2. Kernel panic - not syncing: No init found
   原因：找不到init程序
   解决：检查init参数、文件系统

3. Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block
   原因：缺少驱动（如RAID、LVM、文件系统驱动）
   解决：重建initramfs

4. ACPI Error / Hardware Error
   原因：硬件问题或BIOS设置
   解决：更新BIOS、禁用ACPI
```

### 启动参数调试

```bash
# 在GRUB菜单按'e'编辑启动项

# 添加调试参数
linux /boot/vmlinuz-xxx root=/dev/sda2 debug

# 禁用quiet以查看详细输出
# 删除 "quiet splash"

# 进入紧急模式
linux /boot/vmlinuz-xxx root=/dev/sda2 emergency

# 进入救援模式
linux /boot/vmlinuz-xxx root=/dev/sda2 rescue

# 单用户模式
linux /boot/vmlinuz-xxx root=/dev/sda2 single
# 或
linux /boot/vmlinuz-xxx root=/dev/sda2 init=/bin/bash

# 禁用图形界面
linux /boot/vmlinuz-xxx root=/dev/sda2 systemd.unit=multi-user.target

# 禁用某些模块
linux /boot/vmlinuz-xxx root=/dev/sda2 modprobe.blacklist=nouveau
```

## 3.2 重建initramfs

```bash
# Debian/Ubuntu
update-initramfs -u -k all

# CentOS/RHEL
dracut --force

# 查看initramfs内容
lsinitramfs /boot/initrd.img-xxx  # Debian
lsinitrd /boot/initramfs-xxx.img  # CentOS

# 指定包含的模块
# /etc/initramfs-tools/modules (Debian)
# 添加需要的模块名

# 解压initramfs查看
mkdir /tmp/initrd
cd /tmp/initrd
zcat /boot/initrd.img-xxx | cpio -idmv
```

---

# 四、systemd启动问题

## 4.1 查看启动日志

```bash
# 查看本次启动日志
journalctl -b

# 查看上次启动日志（如果本次启动失败）
journalctl -b -1

# 只看错误
journalctl -b -p err

# 查看特定服务
journalctl -b -u nginx

# 查看启动时序
systemd-analyze blame

# 查看启动关键链
systemd-analyze critical-chain

# 图形化启动时序
systemd-analyze plot > boot.svg
```

## 4.2 服务启动失败

```bash
# 查看失败的服务
systemctl --failed

# 查看服务状态
systemctl status <service>

# 查看服务日志
journalctl -u <service> -n 50

# 常见问题：

# 1. 依赖服务未启动
systemctl list-dependencies <service>

# 2. 配置文件错误
<service> --test-config
# 如 nginx -t

# 3. 端口被占用
ss -tlnp | grep <port>

# 4. 权限问题
ls -la /var/run/<service>
ls -la /var/log/<service>
```

## 4.3 启动目标（Target）

```bash
# 查看当前目标
systemctl get-default

# 常用目标：
# graphical.target    - 图形界面
# multi-user.target   - 多用户命令行
# rescue.target       - 救援模式
# emergency.target    - 紧急模式

# 临时切换目标
systemctl isolate multi-user.target

# 设置默认目标
systemctl set-default multi-user.target

# 如果卡在某个目标
# 在GRUB添加参数
systemd.unit=emergency.target
```

---

# 五、文件系统问题

## 5.1 文件系统检查

### 启动时fsck

```bash
# 强制下次启动时检查
touch /forcefsck
# 或
shutdown -rF now

# 在GRUB添加参数
linux /boot/vmlinuz-xxx root=/dev/sda2 fsck.mode=force

# 跳过文件系统检查
linux /boot/vmlinuz-xxx root=/dev/sda2 fsck.mode=skip
```

### 手动fsck

```bash
# 必须在文件系统未挂载时执行
umount /dev/sda2
fsck -y /dev/sda2

# 参数说明：
# -y    自动回答yes
# -n    只检查不修复
# -f    强制检查
# -v    详细输出

# 从Live CD修复
fsck -y /dev/sda2

# 检查LVM
vgchange -ay  # 激活卷组
fsck -y /dev/mapper/vg-lv

# 修复后重新挂载
mount -o remount,rw /
```

## 5.2 只读文件系统

```bash
# 症状
touch /tmp/test
# Read-only file system

# 原因：
# 1. 检测到错误自动设为只读
# 2. fstab配置问题
# 3. 硬件故障

# 查看挂载状态
mount | grep " / "

# 尝试重新挂载为读写
mount -o remount,rw /

# 如果失败，检查错误
dmesg | tail -50
journalctl -b | grep -i error

# 可能需要fsck
# 先进入单用户模式
systemctl rescue
# 或从GRUB进入emergency模式
```

## 5.3 磁盘空间问题

```bash
# 启动失败可能因为磁盘满

# 从Live CD或救援模式
mount /dev/sda2 /mnt
df -h /mnt

# 找大文件
find /mnt -type f -size +100M -exec ls -lh {} \;

# 清理日志
rm /mnt/var/log/*.gz
journalctl --vacuum-size=100M

# 清理包缓存
rm -rf /mnt/var/cache/apt/archives/*.deb
rm -rf /mnt/var/cache/yum/*
```

---

# 六、紧急修复操作

## 6.1 救援模式操作

```bash
# 从GRUB进入救援模式
# 编辑启动项，添加：
systemd.unit=rescue.target
# 或
init=/bin/bash

# 在rescue shell中

# 1. 重新挂载根分区为读写
mount -o remount,rw /

# 2. 挂载其他分区
mount -a

# 3. 修复问题（如重置密码）
passwd root

# 4. 修复服务配置
systemctl disable problematic.service

# 5. 修复fstab
vim /etc/fstab

# 6. 同步并重启
sync
reboot -f
```

## 6.2 Live CD修复清单

```bash
# 从Live CD启动后

# 1. 识别分区
fdisk -l
lsblk
blkid

# 2. 挂载系统
mount /dev/sda2 /mnt
mount /dev/sda1 /mnt/boot
mount /dev/sda3 /mnt/boot/efi  # UEFI

# 3. 挂载虚拟文件系统
for i in dev proc sys run; do mount --bind /$i /mnt/$i; done

# 4. chroot
chroot /mnt

# 5. 现在可以执行修复操作
# - 重装GRUB
# - 重建initramfs
# - 修改配置
# - 重置密码

# 6. 退出并清理
exit
umount -R /mnt
reboot
```

## 6.3 常见修复命令速查

```bash
# 重置root密码
passwd root

# 修复GRUB
grub-install /dev/sda
update-grub

# 重建initramfs
update-initramfs -u  # Debian
dracut --force       # CentOS

# 修复软件包
apt --fix-broken install
dpkg --configure -a
yum-complete-transaction

# 重置SELinux标签
touch /.autorelabel

# 重新生成机器ID
rm /etc/machine-id
systemd-machine-id-setup
```

---

# 七、诊断脚本

## 7.1 启动诊断脚本

```bash
#!/bin/bash
# boot_diagnose.sh - 启动问题诊断

echo "===== 系统启动诊断 ====="
echo ""

echo "--- 1. 启动信息 ---"
uptime
who -b
echo ""

echo "--- 2. 启动时间分析 ---"
systemd-analyze 2>/dev/null || echo "systemd-analyze不可用"
echo ""

echo "--- 3. 失败的服务 ---"
systemctl --failed
echo ""

echo "--- 4. 启动关键链 ---"
systemd-analyze critical-chain 2>/dev/null | head -20
echo ""

echo "--- 5. 启动错误日志 ---"
journalctl -b -p err --no-pager | head -30
echo ""

echo "--- 6. 内核消息 ---"
dmesg | grep -iE "error|fail|warn" | tail -20
echo ""

echo "--- 7. 文件系统状态 ---"
mount | grep -E "^/dev"
echo ""
df -h | grep -E "^/dev|^Filesystem"
echo ""

echo "--- 8. GRUB配置 ---"
if [ -f /boot/grub/grub.cfg ]; then
    grep -E "^menuentry|linux\s" /boot/grub/grub.cfg | head -10
elif [ -f /boot/grub2/grub.cfg ]; then
    grep -E "^menuentry|linux\s" /boot/grub2/grub.cfg | head -10
fi
echo ""

echo "===== 诊断完成 ====="
```

---

## 总结

| 问题 | 表现 | 解决方法 |
|------|------|----------|
| GRUB损坏 | GRUB rescue提示 | Live CD重装GRUB |
| 内核panic | Kernel panic消息 | 重建initramfs或换内核 |
| 服务失败 | 卡在启动 | emergency模式禁用服务 |
| 文件系统损坏 | 只读挂载 | fsck修复 |
| 磁盘满 | 无法写入 | 清理空间 |
| 密码丢失 | 无法登录 | rescue模式重置 |

**启动修复三板斧**：
1. **GRUB菜单** - 修改启动参数
2. **救援模式** - systemd.unit=rescue.target
3. **Live CD** - chroot修复

**关键记忆**：
1. 按Shift/Esc进入GRUB菜单
2. emergency.target是最小启动
3. init=/bin/bash直接进shell
4. fsck前必须umount

---

## 相关文章

- [上一篇：时间同步与NTP问题排查实战](/articles/sre/sre-41-时间同步与NTP问题排查实战/)
- [下一篇：软件包与依赖问题排查实战](/articles/sre/sre-43-软件包与依赖问题排查实战/)
