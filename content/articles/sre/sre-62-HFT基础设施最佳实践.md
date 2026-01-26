+++
title = "HFT基础设施最佳实践"
description = "深入讲解高频交易基础设施设计：机房选址、网络架构、交换机配置、时间同步(PTP)、电源冗余与环境控制"
date = 2026-01-21
draft = false
[taxonomies]
categories = ["SRE"]
tags = ["SRE", "HFT", "基础设施", "数据中心", "PTP"]
+++

# HFT基础设施最佳实践

## 概述

高频交易的成功高度依赖于基础设施的设计与实施。从机房选址到网络架构，每一个决策都直接影响交易延迟和系统可靠性。本文详细介绍HFT基础设施的设计原则和最佳实践。

## 一、机房选址与Co-location

### 1.1 选址原则

```
Co-location选址决策因素
==========================

1. 延迟因素（权重: 50%）
   ├── 到交易所匹配引擎的物理距离
   ├── 网络跳数
   ├── 交换机延迟
   └── 可获得的最低延迟套餐

2. 成本因素（权重: 25%）
   ├── 机柜租赁费用
   ├── 电力费用（$/kW）
   ├── 带宽费用
   ├── 交叉连接费用
   └── 人员进出费用

3. 可靠性因素（权重: 15%）
   ├── 电力冗余（N+1, 2N）
   ├── 冷却冗余
   ├── 网络冗余
   └── 历史故障率

4. 运营因素（权重: 10%）
   ├── 7x24远程手服务
   ├── 物流便利性
   ├── 扩展能力
   └── 安全认证
```

### 1.2 主要交易所Co-location设施

| 交易所 | 数据中心位置 | 典型延迟 | 特点 |
|--------|-------------|----------|------|
| CME | Aurora, IL (Cermak) | <1µs | 最大期货交易所 |
| NYSE | Mahwah, NJ | <1µs | 股票主要市场 |
| NASDAQ | Carteret, NJ | <1µs | 技术领先 |
| ICE | Basildon, UK | <10µs | 能源/商品 |
| LSE | Slough, UK | <5µs | 欧洲股票 |
| SGX | Singapore | <10µs | 亚洲衍生品 |
| 上交所 | 上海外高桥 | <50µs | A股市场 |
| 深交所 | 深圳南山 | <50µs | A股市场 |

### 1.3 机柜部署规划

```yaml
# HFT机柜配置示例
cabinet_layout:
  type: "42U Standard Rack"
  power: "20kW per cabinet"
  cooling: "In-row cooling, N+1"
  
  equipment:
    # 网络层 (Top of Rack)
    - position: "U42-U40"
      devices:
        - name: "Primary Switch"
          model: "Arista 7130"
          ports: 48x25G + 6x100G
        - name: "Secondary Switch"
          model: "Arista 7130"
          ports: 48x25G + 6x100G
    
    # 计算层 (Middle)
    - position: "U39-U20"
      devices:
        - name: "Trading Server Primary"
          count: 4
          model: "Dell R750xa"
          specs:
            cpu: "Intel Xeon Gold 6348 x2"
            memory: "512GB DDR4-3200"
            nic: "Solarflare X2522"
            storage: "Intel Optane 960GB x2"
        
        - name: "Market Data Server"
          count: 2
          model: "Dell R750xa"
          specs:
            cpu: "Intel Xeon Gold 6348 x2"
            memory: "1TB DDR4-3200"
            nic: "Solarflare X2522 x2"
    
    # 存储/辅助层 (Bottom)
    - position: "U19-U1"
      devices:
        - name: "Log/Audit Server"
          count: 2
          storage: "NVMe 8TB x4 RAID10"
        
        - name: "Management Server"
          count: 1
          purpose: "IPMI/iDRAC aggregation"
        
        - name: "PTP Grandmaster"
          count: 1
          model: "Meinberg M1000"
          accuracy: "<100ns to GPS"
```

## 二、网络架构设计

### 2.1 低延迟网络拓扑

```
                          ┌─────────────┐
                          │  Exchange   │
                          │  Gateway    │
                          └──────┬──────┘
                                 │ Cross-connect
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼─────┐             ┌─────▼─────┐
              │  Primary  │             │ Secondary │
              │  Switch   │─────────────│  Switch   │
              │  (Arista) │   ISL Link  │  (Arista) │
              └─────┬─────┘             └─────┬─────┘
                    │                         │
        ┌───────────┼───────────┐             │
        │           │           │             │
   ┌────▼───┐  ┌────▼───┐  ┌────▼───┐   ┌────▼───┐
   │Trading │  │Trading │  │ Market │   │Backup  │
   │Server 1│  │Server 2│  │  Data  │   │Systems │
   └────────┘  └────────┘  └────────┘   └────────┘
```

### 2.2 交换机选型与配置

```
# 超低延迟交换机对比

Arista 7130 Series:
├── 延迟: 350ns (L2 cut-through)
├── 端口: 48x25G + 6x100G
├── 特点: FPGA可编程、纳秒级时间戳
└── 适用: 顶级HFT

Cisco Nexus 3548:
├── 延迟: 250ns (L2)
├── 端口: 48x10G
├── 特点: 成熟稳定
└── 适用: 通用低延迟

Mellanox SN2100:
├── 延迟: 300ns
├── 端口: 16x100G
├── 特点: 高带宽密度
└── 适用: 高吞吐场景
```

### 2.3 Arista交换机配置示例

```bash
! Arista 7130 低延迟配置

! 基础配置
hostname trading-switch-01
!
! 禁用不必要的服务
no ip routing
no spanning-tree mode
!
! VLAN配置
vlan 100
   name TRADING
!
vlan 200
   name MARKET_DATA
!
vlan 300
   name MANAGEMENT
!

! 端口配置 - 交易服务器
interface Ethernet1/1
   description Trading-Server-01
   switchport mode access
   switchport access vlan 100
   no shutdown
   ! 禁用所有可能增加延迟的功能
   no storm-control broadcast
   no storm-control multicast
   flowcontrol receive off
   flowcontrol send off
!

! 端口配置 - 交易所上行
interface Ethernet49/1
   description Exchange-Primary-Link
   switchport mode trunk
   switchport trunk allowed vlan 100,200
   mtu 9216
   no shutdown
!

! PTP配置
ptp mode boundary
ptp priority1 128
ptp priority2 128
ptp domain 0
!
interface Ethernet1/1
   ptp enable
   ptp transport ipv4
!

! 多播配置 (Market Data)
ip igmp snooping
ip igmp snooping vlan 200
!

! QoS配置 - 交易流量最高优先级
class-map type qos match-any TRADING
   match vlan 100
!
policy-map type qos TRADING_POLICY
   class TRADING
      set cos 7
      set dscp 46
!
interface Ethernet1/1
   service-policy input TRADING_POLICY
!

! 监控配置
monitor session 1 source Ethernet1/1 both
monitor session 1 destination Ethernet48/1
!

! 时间戳功能
hardware tcam profile match-copy
!
```

### 2.4 网络冗余设计

```python
# 网络冗余配置验证脚本

import subprocess
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NetworkPath:
    name: str
    interface: str
    gateway: str
    exchange_ip: str
    priority: int

class NetworkRedundancy:
    def __init__(self):
        self.paths: List[NetworkPath] = [
            NetworkPath("Primary", "eth0", "10.1.1.1", "10.100.1.1", 1),
            NetworkPath("Secondary", "eth1", "10.2.1.1", "10.100.1.1", 2),
        ]
    
    def check_path_health(self, path: NetworkPath) -> bool:
        """检查网络路径健康状态"""
        # 1. 检查接口状态
        result = subprocess.run(
            ["ip", "link", "show", path.interface],
            capture_output=True, text=True
        )
        if "state UP" not in result.stdout:
            return False
        
        # 2. 检查网关可达性
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", path.gateway],
            capture_output=True
        )
        if result.returncode != 0:
            return False
        
        # 3. 检查交易所可达性
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", "-I", path.interface, 
             path.exchange_ip],
            capture_output=True
        )
        return result.returncode == 0
    
    def failover(self, from_path: NetworkPath, to_path: NetworkPath):
        """执行故障转移"""
        print(f"故障转移: {from_path.name} -> {to_path.name}")
        
        # 更新路由
        subprocess.run([
            "ip", "route", "replace", "default",
            "via", to_path.gateway,
            "dev", to_path.interface
        ])
        
        # 通知交易引擎
        self.notify_trading_engine(to_path)
    
    def notify_trading_engine(self, active_path: NetworkPath):
        """通知交易引擎当前活跃路径"""
        # 实际实现会通过IPC通知交易进程
        print(f"通知交易引擎使用 {active_path.name} 路径")
    
    def monitor_loop(self):
        """持续监控网络状态"""
        import time
        
        active_path = self.paths[0]
        
        while True:
            for path in self.paths:
                healthy = self.check_path_health(path)
                print(f"{path.name}: {'健康' if healthy else '故障'}")
                
                if path == active_path and not healthy:
                    # 当前路径故障，寻找备用
                    for backup in self.paths:
                        if backup != path and self.check_path_health(backup):
                            self.failover(active_path, backup)
                            active_path = backup
                            break
            
            time.sleep(1)  # 每秒检查一次
```

## 三、时间同步 (PTP)

### 3.1 PTP架构

```
                    ┌─────────────────────┐
                    │   GPS Antenna       │
                    │   (屋顶安装)         │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │   PTP Grandmaster   │
                    │   (Meinberg M1000)  │
                    │   Accuracy: <100ns  │
                    └─────────┬───────────┘
                              │ PTP Domain 0
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │ Boundary  │   │ Boundary  │   │ Boundary  │
        │ Clock 1   │   │ Clock 2   │   │ Clock 3   │
        │ (Switch)  │   │ (Switch)  │   │ (Switch)  │
        └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
              │               │               │
         ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
         │ Server  │     │ Server  │     │ Server  │
         │ (Slave) │     │ (Slave) │     │ (Slave) │
         └─────────┘     └─────────┘     └─────────┘
```

### 3.2 PTP配置

```ini
# /etc/linuxptp/ptp4l.conf - PTP Slave配置

[global]
# 基本设置
twoStepFlag             0
slaveOnly               1
priority1               128
priority2               128
domainNumber            0
clockClass              248
clockAccuracy           0xFE
offsetScaledLogVariance 0xFFFF

# 时钟伺服
clock_servo             pi
pi_proportional_const   0.0
pi_integral_const       0.0
pi_proportional_scale   0.0
pi_proportional_exponent -0.3
pi_proportional_norm_max 0.7
pi_integral_scale        0.0
pi_integral_exponent     0.4
pi_integral_norm_max     0.3
step_threshold           0.00002
first_step_threshold     0.00002

# 硬件时间戳
free_running            0
time_stamping           hardware
delay_mechanism         E2E
network_transport       L2

# 日志
logging_level           6
verbose                 0
use_syslog              1
summary_interval        0

[eth0]
# 网卡特定配置
logAnnounceInterval     0
logSyncInterval         -4
logMinDelayReqInterval  -4
announceReceiptTimeout  3
```

```ini
# /etc/linuxptp/phc2sys.conf - PHC同步配置

[global]
# 将网卡PHC同步到系统时钟
phc2sys_sync            1
domainNumber            0

# 伺服参数
pi_proportional_const   0.0
pi_integral_const       0.0
step_threshold          0.00002

# 监控
logging_level           6
```

### 3.3 PTP监控脚本

```bash
#!/bin/bash
# ptp_monitor.sh - PTP同步状态监控

echo "=== PTP同步状态 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S.%N')"
echo

# 1. PTP4L状态
echo ">>> PTP4L状态:"
pmc -u -b 0 'GET CURRENT_DATA_SET' 2>/dev/null | grep -E "(stepsRemoved|offsetFromMaster|meanPathDelay)"

# 2. PHC2SYS状态
echo -e "\n>>> PHC2SYS状态:"
journalctl -u phc2sys --since "1 minute ago" -n 5 --no-pager 2>/dev/null | \
    grep -oP "offset\s+\K[-0-9]+" | tail -5 | \
    awk '{sum+=$1; count++} END {if(count>0) printf "平均偏移: %.0f ns\n", sum/count}'

# 3. 网卡PHC时间
echo -e "\n>>> 网卡PHC时间:"
for iface in eth0 eth1; do
    if ethtool -T $iface 2>/dev/null | grep -q "hardware-transmit"; then
        phc_time=$(phc_ctl $iface get 2>/dev/null | grep "clock time" | awk '{print $NF}')
        echo "  $iface PHC: $phc_time"
    fi
done

# 4. Grandmaster信息
echo -e "\n>>> Grandmaster信息:"
pmc -u -b 0 'GET PARENT_DATA_SET' 2>/dev/null | \
    grep -E "(parentPortIdentity|grandmasterClockQuality)"

# 5. 时间同步精度
echo -e "\n>>> 时间同步精度:"
current_offset=$(pmc -u -b 0 'GET CURRENT_DATA_SET' 2>/dev/null | \
    grep offsetFromMaster | awk '{print $2}')
if [ -n "$current_offset" ]; then
    offset_ns=$(echo "$current_offset" | awk '{printf "%.0f", $1}')
    if [ ${offset_ns#-} -lt 100 ]; then
        echo "  状态: 正常 (偏移: ${offset_ns}ns)"
    elif [ ${offset_ns#-} -lt 1000 ]; then
        echo "  状态: 警告 (偏移: ${offset_ns}ns)"
    else
        echo "  状态: 异常 (偏移: ${offset_ns}ns)"
    fi
fi
```

### 3.4 硬件时间戳配置

```c
/* 网卡硬件时间戳配置示例 */
#include <linux/net_tstamp.h>
#include <sys/ioctl.h>
#include <net/if.h>

int enable_hardware_timestamping(int sockfd, const char* ifname) {
    struct ifreq ifr;
    struct hwtstamp_config hwconfig;
    
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    
    // 配置硬件时间戳
    memset(&hwconfig, 0, sizeof(hwconfig));
    hwconfig.tx_type = HWTSTAMP_TX_ON;           // 启用TX时间戳
    hwconfig.rx_filter = HWTSTAMP_FILTER_ALL;    // 所有RX包时间戳
    
    ifr.ifr_data = (void*)&hwconfig;
    
    if (ioctl(sockfd, SIOCSHWTSTAMP, &ifr) < 0) {
        perror("SIOCSHWTSTAMP failed");
        return -1;
    }
    
    // 配置socket接收时间戳
    int flags = SOF_TIMESTAMPING_RX_HARDWARE |
                SOF_TIMESTAMPING_TX_HARDWARE |
                SOF_TIMESTAMPING_RAW_HARDWARE;
    
    if (setsockopt(sockfd, SOL_SOCKET, SO_TIMESTAMPING, 
                   &flags, sizeof(flags)) < 0) {
        perror("SO_TIMESTAMPING failed");
        return -1;
    }
    
    return 0;
}

/* 获取接收包的硬件时间戳 */
int64_t get_rx_timestamp(struct msghdr* msg) {
    struct cmsghdr* cmsg;
    
    for (cmsg = CMSG_FIRSTHDR(msg); cmsg != NULL; 
         cmsg = CMSG_NXTHDR(msg, cmsg)) {
        if (cmsg->cmsg_level == SOL_SOCKET &&
            cmsg->cmsg_type == SO_TIMESTAMPING) {
            struct timespec* stamps = (struct timespec*)CMSG_DATA(cmsg);
            // stamps[0]: software timestamp
            // stamps[1]: deprecated
            // stamps[2]: hardware timestamp
            return stamps[2].tv_sec * 1000000000LL + stamps[2].tv_nsec;
        }
    }
    return -1;
}
```

## 四、电源与冷却

### 4.1 电源架构

```
电源冗余设计 (2N架构)
========================

主电源路径 (Feed A)
├── 市电输入 A
├── UPS A (在线双转换)
│   ├── 电池后备: 15分钟
│   └── 效率: >96%
├── PDU A (智能PDU)
│   ├── 每路监控
│   └── 远程控制
└── 服务器 PSU A

备用电源路径 (Feed B)
├── 市电输入 B (独立变电站)
├── UPS B (在线双转换)
│   ├── 电池后备: 15分钟
│   └── 效率: >96%
├── PDU B (智能PDU)
│   ├── 每路监控
│   └── 远程控制
└── 服务器 PSU B

柴油发电机
├── 容量: 覆盖100%负载
├── 启动时间: <10秒
├── 燃料储备: 48小时
└── 每月测试
```

### 4.2 电源监控

```python
#!/usr/bin/env python3
"""PDU电源监控"""

import snmplib
from dataclasses import dataclass
from typing import List
import time

@dataclass
class PDUOutlet:
    id: int
    name: str
    current_amps: float
    voltage: float
    power_watts: float
    status: str

class PDUMonitor:
    def __init__(self, pdu_ip: str, community: str = "public"):
        self.pdu_ip = pdu_ip
        self.community = community
    
    def get_outlets(self) -> List[PDUOutlet]:
        """获取所有插座状态"""
        outlets = []
        # 实际实现使用SNMP查询PDU
        # OIDs取决于PDU厂商（如APC、Raritan等）
        return outlets
    
    def get_total_power(self) -> float:
        """获取总功率"""
        outlets = self.get_outlets()
        return sum(o.power_watts for o in outlets)
    
    def check_power_balance(self, pdu_a: 'PDUMonitor', pdu_b: 'PDUMonitor') -> dict:
        """检查A/B路电源平衡"""
        power_a = pdu_a.get_total_power()
        power_b = pdu_b.get_total_power()
        
        total = power_a + power_b
        imbalance = abs(power_a - power_b) / total * 100 if total > 0 else 0
        
        return {
            "power_a_kw": power_a / 1000,
            "power_b_kw": power_b / 1000,
            "total_kw": total / 1000,
            "imbalance_pct": imbalance,
            "status": "balanced" if imbalance < 10 else "unbalanced"
        }

# 告警规则
def power_alerts(metrics: dict):
    alerts = []
    
    if metrics["imbalance_pct"] > 20:
        alerts.append({
            "severity": "warning",
            "message": f"电源不平衡: {metrics['imbalance_pct']:.1f}%"
        })
    
    if metrics["total_kw"] > 18:  # 假设20kW上限
        alerts.append({
            "severity": "critical",
            "message": f"电力使用接近上限: {metrics['total_kw']:.1f}kW"
        })
    
    return alerts
```

### 4.3 冷却设计

```yaml
# 冷却系统配置

cooling_design:
  type: "In-row cooling"
  redundancy: "N+1"
  capacity: "30kW per cabinet"
  
  temperature_targets:
    inlet: 18-27°C (ASHRAE A1)
    outlet: <35°C
    delta_t: 10-15°C
    
  humidity_targets:
    relative_humidity: 40-60%
    dew_point: 5.5-15°C

  hot_aisle_containment:
    enabled: true
    pressure_differential: "positive cold aisle"
    
  monitoring:
    sensors_per_cabinet: 6
    polling_interval: 10s
    alerts:
      - condition: "inlet_temp > 27"
        severity: warning
      - condition: "inlet_temp > 30"
        severity: critical
      - condition: "humidity < 30 or humidity > 70"
        severity: warning
```

## 五、物理安全与访问控制

### 5.1 安全分层

```
物理安全层级
=============

第1层: 建筑外围
├── 围栏/围墙
├── CCTV监控
├── 车辆检查
└── 访客登记

第2层: 建筑入口
├── 门禁卡
├── 生物识别（可选）
├── 安保人员
└── 金属探测器

第3层: 数据中心大厅
├── 双因素认证
├── 人员陪同制度
├── CCTV全覆盖
└── 防尾随门

第4层: 机柜/笼位
├── 独立机柜锁
├── 智能门锁（审计日志）
├── 运动传感器
└── 机柜内监控
```

### 5.2 变更管理流程

```
HFT机房变更流程
================

1. 变更申请
   ├── 提交变更请求
   ├── 描述变更内容
   ├── 风险评估
   └── 回滚计划

2. 变更审批
   ├── 技术评审
   ├── 安全评审
   └── 管理层批准

3. 变更窗口
   ├── 首选: 非交易时段
   ├── 通知相关方
   └── 准备回滚

4. 变更执行
   ├── 双人操作原则
   ├── 实时记录
   └── 测试验证

5. 变更完成
   ├── 功能验证
   ├── 性能验证
   ├── 文档更新
   └── 变更关闭
```

## 六、灾难恢复

### 6.1 DR架构

```
主站点 (Primary Site)                    DR站点 (Secondary Site)
=====================                    ======================

┌─────────────────┐                      ┌─────────────────┐
│ Trading Engine  │───── 实时同步 ─────►│ Trading Engine  │
│ (Active)        │      (延迟<1ms)      │ (Standby)       │
└─────────────────┘                      └─────────────────┘
        │                                         │
        ▼                                         ▼
┌─────────────────┐                      ┌─────────────────┐
│ Market Data     │───── 实时同步 ─────►│ Market Data     │
│ (Active)        │                      │ (Standby)       │
└─────────────────┘                      └─────────────────┘
        │                                         │
        ▼                                         ▼
┌─────────────────┐                      ┌─────────────────┐
│ Order State     │───── 实时复制 ─────►│ Order State     │
│ (Primary)       │     (WAL shipping)   │ (Replica)       │
└─────────────────┘                      └─────────────────┘

RTO目标: <5分钟
RPO目标: 0（零数据丢失）
```

### 6.2 故障切换自动化

```python
#!/usr/bin/env python3
"""自动故障切换控制器"""

import time
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class SiteRole(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DEGRADED = "degraded"

@dataclass
class SiteStatus:
    name: str
    role: SiteRole
    healthy: bool
    last_heartbeat: float
    replication_lag_ms: float

class FailoverController:
    def __init__(self, primary_site: str, secondary_site: str):
        self.sites = {
            primary_site: SiteStatus(
                name=primary_site,
                role=SiteRole.PRIMARY,
                healthy=True,
                last_heartbeat=time.time(),
                replication_lag_ms=0
            ),
            secondary_site: SiteStatus(
                name=secondary_site,
                role=SiteRole.SECONDARY,
                healthy=True,
                last_heartbeat=time.time(),
                replication_lag_ms=0
            )
        }
        self.failover_in_progress = False
        self.logger = logging.getLogger(__name__)
    
    def check_site_health(self, site_name: str) -> bool:
        """检查站点健康状态"""
        site = self.sites[site_name]
        
        # 检查心跳
        if time.time() - site.last_heartbeat > 5:  # 5秒超时
            return False
        
        # 检查复制延迟
        if site.role == SiteRole.SECONDARY and site.replication_lag_ms > 1000:
            return False
        
        return True
    
    def initiate_failover(self, reason: str):
        """发起故障切换"""
        if self.failover_in_progress:
            self.logger.warning("故障切换已在进行中")
            return
        
        self.failover_in_progress = True
        self.logger.critical(f"发起故障切换: {reason}")
        
        try:
            # 1. 停止主站点交易
            self._stop_trading_primary()
            
            # 2. 等待复制追平
            self._wait_replication_sync()
            
            # 3. 提升备站点
            self._promote_secondary()
            
            # 4. 更新路由/DNS
            self._update_routing()
            
            # 5. 通知交易所
            self._notify_exchange()
            
            # 6. 恢复交易
            self._resume_trading()
            
            self.logger.info("故障切换完成")
            
        except Exception as e:
            self.logger.error(f"故障切换失败: {e}")
            self._rollback_failover()
        finally:
            self.failover_in_progress = False
    
    def _stop_trading_primary(self):
        """停止主站点交易"""
        self.logger.info("停止主站点交易...")
        # 发送停止命令到交易引擎
    
    def _wait_replication_sync(self, timeout_s: float = 30):
        """等待复制同步"""
        self.logger.info("等待复制同步...")
        start = time.time()
        while time.time() - start < timeout_s:
            secondary = [s for s in self.sites.values() 
                        if s.role == SiteRole.SECONDARY][0]
            if secondary.replication_lag_ms < 10:
                return
            time.sleep(0.1)
        raise TimeoutError("复制同步超时")
    
    def _promote_secondary(self):
        """提升备站点为主站点"""
        self.logger.info("提升备站点...")
        for site in self.sites.values():
            if site.role == SiteRole.SECONDARY:
                site.role = SiteRole.PRIMARY
            elif site.role == SiteRole.PRIMARY:
                site.role = SiteRole.DEGRADED
    
    def _update_routing(self):
        """更新网络路由"""
        self.logger.info("更新路由配置...")
        # 更新BGP、DNS等
    
    def _notify_exchange(self):
        """通知交易所新的连接信息"""
        self.logger.info("通知交易所...")
    
    def _resume_trading(self):
        """恢复交易"""
        self.logger.info("恢复交易...")
    
    def _rollback_failover(self):
        """回滚故障切换"""
        self.logger.warning("回滚故障切换...")
```

## 七、运维自动化

### 7.1 基础设施即代码

```yaml
# Ansible playbook: deploy_trading_server.yml

---
- name: 部署HFT交易服务器
  hosts: trading_servers
  become: yes
  
  vars:
    trading_cpus: "2-15"
    hugepages_1g: 32
    
  tasks:
    - name: 配置GRUB参数
      lineinfile:
        path: /etc/default/grub
        regexp: '^GRUB_CMDLINE_LINUX='
        line: 'GRUB_CMDLINE_LINUX="isolcpus={{ trading_cpus }} nohz_full={{ trading_cpus }} rcu_nocbs={{ trading_cpus }} default_hugepagesz=1G hugepagesz=1G hugepages={{ hugepages_1g }} transparent_hugepage=never intel_pstate=disable"'
      notify: Update GRUB
    
    - name: 配置sysctl参数
      sysctl:
        name: "{{ item.name }}"
        value: "{{ item.value }}"
        state: present
        sysctl_file: /etc/sysctl.d/99-trading.conf
      loop:
        - { name: "vm.swappiness", value: "0" }
        - { name: "kernel.numa_balancing", value: "0" }
        - { name: "net.core.rmem_max", value: "134217728" }
        - { name: "net.core.wmem_max", value: "134217728" }
        - { name: "net.ipv4.tcp_low_latency", value: "1" }
    
    - name: 配置CPU频率
      copy:
        content: "performance"
        dest: "/sys/devices/system/cpu/cpu{{ item }}/cpufreq/scaling_governor"
      loop: "{{ range(0, ansible_processor_vcpus) | list }}"
      when: ansible_virtualization_type == "NA"
    
    - name: 配置网卡
      shell: |
        ethtool -C {{ item }} rx-usecs 0 tx-usecs 0
        ethtool -C {{ item }} adaptive-rx off adaptive-tx off
        ethtool -K {{ item }} gro off lro off tso off gso off
      loop: "{{ ansible_interfaces | select('match', '^eth|^ens|^enp') | list }}"
    
    - name: 安装PTP
      package:
        name: linuxptp
        state: present
    
    - name: 配置PTP
      template:
        src: ptp4l.conf.j2
        dest: /etc/linuxptp/ptp4l.conf
      notify: Restart PTP
    
    - name: 部署交易软件
      include_role:
        name: trading_engine
    
  handlers:
    - name: Update GRUB
      command: update-grub
      
    - name: Restart PTP
      service:
        name: ptp4l
        state: restarted
```

### 7.2 配置管理

```python
#!/usr/bin/env python3
"""基础设施配置验证"""

import subprocess
import json
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ConfigCheck:
    name: str
    expected: str
    actual: str
    passed: bool

class InfraValidator:
    def __init__(self):
        self.checks: List[ConfigCheck] = []
    
    def run_all_checks(self) -> List[ConfigCheck]:
        """运行所有配置检查"""
        self.checks = []
        
        # CPU检查
        self.checks.extend(self._check_cpu_config())
        
        # 内存检查
        self.checks.extend(self._check_memory_config())
        
        # 网络检查
        self.checks.extend(self._check_network_config())
        
        # PTP检查
        self.checks.extend(self._check_ptp_config())
        
        return self.checks
    
    def _check_cpu_config(self) -> List[ConfigCheck]:
        checks = []
        
        # CPU governor
        result = subprocess.run(
            ["cat", "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"],
            capture_output=True, text=True
        )
        actual = result.stdout.strip()
        checks.append(ConfigCheck(
            name="CPU Governor",
            expected="performance",
            actual=actual,
            passed=(actual == "performance")
        ))
        
        # isolcpus
        result = subprocess.run(
            ["cat", "/sys/devices/system/cpu/isolated"],
            capture_output=True, text=True
        )
        actual = result.stdout.strip()
        checks.append(ConfigCheck(
            name="Isolated CPUs",
            expected="2-15",
            actual=actual,
            passed=(actual == "2-15")
        ))
        
        return checks
    
    def _check_memory_config(self) -> List[ConfigCheck]:
        checks = []
        
        # Hugepages
        result = subprocess.run(
            ["cat", "/sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages"],
            capture_output=True, text=True
        )
        actual = result.stdout.strip()
        checks.append(ConfigCheck(
            name="1GB Hugepages",
            expected="32",
            actual=actual,
            passed=(int(actual) >= 32)
        ))
        
        # THP
        result = subprocess.run(
            ["cat", "/sys/kernel/mm/transparent_hugepage/enabled"],
            capture_output=True, text=True
        )
        actual = result.stdout.strip()
        checks.append(ConfigCheck(
            name="THP Disabled",
            expected="[never]",
            actual=actual,
            passed=("[never]" in actual)
        ))
        
        return checks
    
    def _check_network_config(self) -> List[ConfigCheck]:
        checks = []
        
        # 检查网卡设置（以eth0为例）
        result = subprocess.run(
            ["ethtool", "-c", "eth0"],
            capture_output=True, text=True
        )
        if "rx-usecs: 0" in result.stdout:
            checks.append(ConfigCheck(
                name="NIC Interrupt Coalescing",
                expected="rx-usecs: 0",
                actual="rx-usecs: 0",
                passed=True
            ))
        else:
            checks.append(ConfigCheck(
                name="NIC Interrupt Coalescing",
                expected="rx-usecs: 0",
                actual="enabled",
                passed=False
            ))
        
        return checks
    
    def _check_ptp_config(self) -> List[ConfigCheck]:
        checks = []
        
        # PTP服务状态
        result = subprocess.run(
            ["systemctl", "is-active", "ptp4l"],
            capture_output=True, text=True
        )
        actual = result.stdout.strip()
        checks.append(ConfigCheck(
            name="PTP4L Service",
            expected="active",
            actual=actual,
            passed=(actual == "active")
        ))
        
        return checks
    
    def print_report(self):
        """打印验证报告"""
        print("=" * 60)
        print("基础设施配置验证报告")
        print("=" * 60)
        
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        
        for check in self.checks:
            status = "✓" if check.passed else "✗"
            print(f"{status} {check.name}")
            print(f"    期望: {check.expected}")
            print(f"    实际: {check.actual}")
        
        print("=" * 60)
        print(f"结果: {passed}/{total} 项通过")
        
        return passed == total

if __name__ == "__main__":
    validator = InfraValidator()
    validator.run_all_checks()
    success = validator.print_report()
    exit(0 if success else 1)
```

## 总结

HFT基础设施的核心要点：

1. **选址优先**：Co-location决定了延迟下限
2. **网络为王**：超低延迟交换机、优化的网络拓扑
3. **时间精准**：PTP同步精度达到亚微秒级
4. **高可用**：2N电源、N+1冷却、完善的DR
5. **自动化运维**：基础设施即代码、配置验证

每一个环节都直接影响交易系统的性能和可靠性，需要系统性规划和持续优化。
