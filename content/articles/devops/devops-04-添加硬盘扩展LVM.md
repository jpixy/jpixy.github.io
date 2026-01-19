+++
title = "04.如何添加新硬盘扩展LVM"
slug = "devops-如何添加新硬盘扩展LVM"
+++

# 如何添加新硬盘扩展LVM

## 查看当前磁盘状态

或直接使用整块磁盘（无分区）：

```plain
[14:23:30] johnny :: johnny-ThinkPad-X1-Extreme  ➜  ~ » df -lhT
Filesystem                        Type      Size  Used Avail Use% Mounted on
tmpfs                             tmpfs     3.1G  2.7M  3.1G   1% /run
/dev/mapper/ubuntu--vg-ubuntu--lv ext4      455G  119G  313G  28% /
tmpfs                             tmpfs      16G     0   16G   0% /dev/shm
tmpfs                             tmpfs     5.0M   16K  5.0M   1% /run/lock
efivarfs                          efivarfs  246K  124K  117K  52% /sys/firmware/efi/efivars
/dev/nvme1n1p2                    ext4      2.0G  206M  1.6G  12% /boot
/dev/nvme1n1p1                    vfat      1.1G  6.2M  1.1G   1% /boot/efi
tmpfs                             tmpfs     3.1G  140K  3.1G   1% /run/user/1000
[14:23:31] johnny :: johnny-ThinkPad-X1-Extreme  ➜  ~ » lsblk
NAME                        MAJ:MIN RM   SIZE RO TYPE  MOUNTPOINTS
loop0                         7:0    0     4K  1 loop  /snap/bare/5
loop1                         7:1    0  73.9M  1 loop  /snap/core22/1748
loop2                         7:2    0  73.9M  1 loop  /snap/core22/2010
loop3                         7:3    0   258M  1 loop  /snap/firefox/5751
loop4                         7:4    0  11.1M  1 loop  /snap/firmware-updater/167
loop5                         7:5    0   516M  1 loop  /snap/gnome-42-2204/202
loop6                         7:6    0  91.7M  1 loop  /snap/gtk-common-themes/1535
loop7                         7:7    0  10.8M  1 loop  /snap/snap-store/1248
loop8                         7:8    0  44.4M  1 loop  /snap/snapd/23545
loop9                         7:9    0  50.9M  1 loop  /snap/snapd/24718
loop10                        7:10   0   568K  1 loop  /snap/snapd-desktop-integration/253
loop11                        7:11   0  13.2M  1 loop  /snap/canonical-livepatch/333
sda                           8:0    1     0B  0 disk  
nvme0n1                     259:0    0 476.9G  0 disk  
└─nvme0n1p1                 259:2    0 476.9G  0 part  
nvme1n1                     259:1    0 465.8G  0 disk  
├─nvme1n1p1                 259:3    0     1G  0 part  /boot/efi
├─nvme1n1p2                 259:4    0     2G  0 part  /boot
└─nvme1n1p3                 259:5    0 462.7G  0 part  
  └─dm_crypt-1              252:0    0 462.7G  0 crypt 
    └─ubuntu--vg-ubuntu--lv 252:1    0 462.7G  0 lvm   /



```

我的nvme0n1 完全没有利用上，我现在需要将这块硬盘，扩展到ubuntu--vg-ubuntu--lv 里面去，形成一块1tb的分区。给出具体步骤和命令  
  
  
要将 `nvme0n1` 这块未使用的 476.9GB NVMe 硬盘添加到现有的 LVM 卷组 (`ubuntu--vg`) 中，并扩展逻辑卷 (`ubuntu--lv`) 以合并为约 1TB 的空间，请按照以下步骤操作：

---

### **步骤 1：检查当前 LVM 状态**
```bash
sudo vgdisplay
sudo lvdisplay
```

确认当前的卷组 (`ubuntu--vg`) 和逻辑卷 (`ubuntu--lv`) 信息。

---

### **步骤 2：在 **`nvme0n1`** 上创建 LVM 物理卷 (PV)**
1. **分区（可选）**：  
如果硬盘未分区（如 `nvme0n1` 显示为完整磁盘），可以直接将其作为物理卷使用。但建议先创建一个分区（更规范）：

```bash
sudo parted /dev/nvme0n1
```

在 `parted` 交互界面中执行：

```plain
mklabel gpt
mkpart primary 0% 100%
set 1 lvm on
quit
```

然后刷新分区表：

```bash
sudo partprobe /dev/nvme0n1
```

2. **创建物理卷**：

```bash
sudo pvcreate /dev/nvme0n1p1  # 如果已分区
# 或直接使用整块磁盘（无分区）：
sudo pvcreate /dev/nvme0n1
```

---

### **步骤 3：将物理卷添加到现有卷组 (**`ubuntu--vg`**)**
```bash
sudo vgextend ubuntu--vg /dev/nvme0n1p1  # 或 /dev/nvme0n1
```

验证扩展后的卷组空间：

```bash
sudo vgdisplay
```

应看到 `Free PE / Size` 增加了约 476GB。

---

### **步骤 4：扩展逻辑卷 (**`ubuntu--lv`**)**
1. **扩展逻辑卷**：

```bash
sudo lvextend -l +100%FREE /dev/ubuntu--vg/ubuntu--lv
```

（`-l +100%FREE` 表示占用所有剩余空间）

2. **调整文件系统**（扩展 `ext4` 文件系统）：

```bash
sudo resize2fs /dev/ubuntu--vg/ubuntu--lv
```

---

### **步骤 5：验证结果**
```bash
df -hT
```

应看到 `/` 挂载点的可用空间已增加（原 313GB + 476GB ≈ 789GB）。  
同时检查 LVM 状态：

```bash
sudo pvs
sudo vgs
sudo lvs
```

---

### **关键命令总结**
| 操作 | 命令 |
| --- | --- |
| **创建物理卷** | `sudo pvcreate /dev/nvme0n1p1` |
| **扩展卷组** | `sudo vgextend ubuntu--vg /dev/nvme0n1p1` |
| **扩展逻辑卷** | `sudo lvextend -l +100%FREE /dev/ubuntu--vg/ubuntu--lv` |
| **调整文件系统** | `sudo resize2fs /dev/ubuntu--vg/ubuntu--lv` |


---

### **注意事项**
1. **数据安全**：操作前建议备份重要数据（尽管 LVM 扩展通常安全）。
2. **分区对齐**：若使用 `parted`，确保分区对齐（`align-check optimal 1`）。
3. **其他文件系统**：如果是 `xfs`，需用 `xfs_growfs` 替代 `resize2fs`。

完成后，你的系统将拥有一个约 1TB 的合并存储空间！   
  


### **为什么 **`df`** 显示 **`/`** 只有 455G，而 **`lvs`** 显示 939.63G？**
从您的输出可以看到矛盾点：

+ `sudo lvs` 显示逻辑卷 (`ubuntu-lv`) 总大小是 **939.63GB**（≈ 462.7GB + 476.9GB）。
+ `df -h` 却显示 `/` 挂载的文件系统只有 **455GB**（已用 121G，剩余 311G）。

---

### **原因分析**
1. `resize2fs`** 未完全扩展文件系统**  
    - 虽然 LVM 逻辑卷 (`ubuntu-lv`) 已扩展到 939.63GB，但文件系统 (`ext4`) **未被正确扩展到整个空间**。
    - 您可能只调整了 LVM 逻辑卷，但忘记执行 `resize2fs` 或执行时未生效。
2. **文件系统挂载时的大小限制**  
    - 某些情况下，如果文件系统在挂载时未正确识别新空间，`df` 可能显示旧的大小。

---

### **解决方案**
#### **1. 检查文件系统当前大小**
```bash
sudo dumpe2fs -h /dev/mapper/ubuntu--vg-ubuntu--lv | grep "Block count"
```

+ 如果输出的 `Block count` 远小于 `939.63GB`（如接近 455GB），说明文件系统未扩展。

#### **2. 扩展 **`ext4`** 文件系统**
```bash
sudo resize2fs /dev/mapper/ubuntu--vg-ubuntu--lv
```

+ 此命令会让 `ext4` 占用逻辑卷的全部空间。

#### **3. 重新检查 **`df`
```bash
df -hT /
```

+ 现在应该显示总容量 ≈ 939.63GB。

---

### **验证步骤**
1. **确认逻辑卷大小**：

```bash
sudo lvdisplay /dev/ubuntu-vg/ubuntu-lv | grep "LV Size"
```

    - 应显示 `LV Size 939.63 GiB`。
2. **确认文件系统大小**：

```bash
sudo blockdev --getsize64 /dev/mapper/ubuntu--vg-ubuntu--lv
```

    - 输出应为 `939.63GB` 的字节数（如 1009317314560 字节）。
3. **如果 **`resize2fs`** 报错**：
    - 尝试卸载后操作（需进入救援模式）：

```bash
sudo umount /
sudo fsck -f /dev/mapper/ubuntu--vg-ubuntu--lv
sudo resize2fs /dev/mapper/ubuntu--vg-ubuntu--lv
sudo mount -a
```

---

### **关键点**
+ **LVM 逻辑卷 ≠ 文件系统**  
LVM 负责管理存储池，而 `ext4` 是文件系统，两者需分别扩展。
+ **加密层不影响大小**  
`dm_crypt-1`（LUKS）只是加密中间层，不占用额外空间。

---

### **最终预期**
| 命令 | 正确输出 |
| --- | --- |
| `sudo lvs` | `LV Size 939.63g` |
| `df -h /` | 大小 ≈ 939G |
| `lsblk` | `ubuntu--lv` 显示 `939.6G` |


如果仍有问题，可能是文件系统损坏或 LVM 配置异常，建议备份后进一步检查！







  
----------  
  
  
  
sudo pvs

  PV                     VG        Fmt  Attr PSize    PFree

  /dev/mapper/dm_crypt-1 ubuntu-vg lvm2 a--   462.69g    0 

  /dev/nvme0n1p1         ubuntu-vg lvm2 a--  <476.94g    0 



nvme0n1p1不应该有加密吗  
  
  
您的问题非常关键！从 `sudo pvs` 的输出可以看到：

+ `/dev/mapper/dm_crypt-1` 是加密的 LVM 物理卷（PV），属于 `ubuntu-vg` 卷组。
+ `/dev/nvme0n1p1` **没有加密**，直接作为物理卷加入了 `ubuntu-vg`。

这会导致 **安全不一致性**：新增的 NVMe 硬盘数据未加密，而原系统是加密的（LUKS/dm-crypt）。以下是修复步骤：

---

### **正确步骤：将新硬盘（nvme0n1）加密后加入 LVM**
#### **1. 从卷组中移除未加密的物理卷**
```bash
sudo vgreduce ubuntu-vg /dev/nvme0n1p1
sudo pvremove /dev/nvme0n1p1
```

#### **2. 在 **`nvme0n1`** 上创建加密层（LUKS）**
```bash
sudo cryptsetup luksFormat /dev/nvme0n1p1  # 会提示输入加密密码
sudo cryptsetup open /dev/nvme0n1p1 nvme0_crypt  # 打开加密设备
```

（如果未分区，用 `/dev/nvme0n1` 代替 `/dev/nvme0n1p1`）

#### **3. 将加密后的设备设为物理卷并加入卷组**
```bash
sudo pvcreate /dev/mapper/nvme0_crypt
sudo vgextend ubuntu-vg /dev/mapper/nvme0_crypt
```

#### **4. 扩展逻辑卷和文件系统**
```bash
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv  # 如果是 ext4
```

#### **5. 配置开机自动解密**
编辑 `/etc/crypttab`：

```bash
echo "nvme0_crypt /dev/nvme0n1p1 none luks,discard" | sudo tee -a /etc/crypttab
```

更新 initramfs：

```bash
sudo update-initramfs -u
```

---

### **验证加密状态**
```bash
sudo cryptsetup status nvme0_crypt  # 检查加密设备
sudo pvs                           # 应显示加密后的 PV
lsblk -f                           # 查看加密层和文件系统
```

---

### **为什么必须加密？**
1. **安全一致性**：原系统使用 LUKS 加密，新增硬盘不加密会导致数据泄露风险。
2. **透明解密**：通过 `/etc/crypttab` 配置后，开机时可自动解密（需输入密码或使用密钥文件）。

---

### **最终效果**
+ 两块 NVMe 硬盘（`nvme0n1` 和 `nvme1n1`）均通过 LUKS 加密。
+ 合并为一个逻辑卷 (`ubuntu-lv`)，总容量约 1TB。
+ 所有数据读写均经过加密层，安全性保持一致。

如果有其他疑问（如密钥管理或性能优化），请随时提出！ 🔐
