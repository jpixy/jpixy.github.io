+++
title = "Ethernet相关"
slug = "net-Ethernet相关"
+++

# Ethernet相关
## Ethernet帧结构
Ethernet帧结构是网络通信中非常基础且重要的一部分，它定义了数据在网络中的传输格式。一个典型的Ethernet帧包含以下几个部分：

1. **帧前序（Preamble）**：7字节（56位），由交替的1和0组成，用于通知接收端一个新帧的到来。
2. **帧起始符（Start of Frame Delimiter, SOF）**：1字节（8位），固定值为10101011，标志着帧的开始。
3. **目的MAC地址（Destination MAC Address）**：6字节，标识帧的接收者。
4. **源MAC地址（Source MAC Address）**：6字节，标识帧的发送者。
5. **帧长度/类型（Length/Type）**：2字节，指示数据字段的长度或者上层协议类型。
6. **数据（Data）**：46-1500字节，帧的有效载荷。
7. **填充（Padding）**：如果数据字段少于46字节，则使用填充字节，确保整个帧至少有64字节。
8. **帧校验序列（Frame Check Sequence, FCS）**：4字节，用于错误检测。

## VLAN技术和Ethernet关联
当涉及到VLAN（Virtual Local Area Network）时，帧结构会有所扩展。VLAN技术通过在以太网帧中插入一个标签（Tag）来实现逻辑上的网络分割。这个标签通常包含以下信息：

1. **TPID（Tag Protocol Identifier）**：2字节，固定值为0x8100，用于标识这是一个VLAN标签。
2. **TCI（Tag Control Information）**：2字节，包含以下字段：
    - **PCP（Priority Code Point）**：3位，用于指定帧的优先级。
    - **DEI/CFI（Drop Eligible Indicator/Canonical Format Indicator）**：1位，用于指示帧的丢弃资格或者是否为规范格式。
    - **VID（VLAN Identifier）**：12位，用于指定帧所属的VLAN编号。

加入VLAN标签后，Ethernet帧的最大长度会从1518字节增加到1522字节。VLAN技术的优点包括限制广播域、增强安全性、提高网络健壮性以及灵活构建虚拟工作组。VLAN ID的有效取值范围是1到4094，其中0和4095为协议保留值。

在实际应用中，VLAN技术可以用于创建逻辑上的网络分割，使得不同VLAN间的通信需要通过路由器或者三层交换机来实现，从而增强了网络的安全性和管理的灵活性。同时，VLAN技术也支持跨交换机的部署，允许在多个交换机上使用相同的VLAN ID来实现更大范围内的网络分割。

