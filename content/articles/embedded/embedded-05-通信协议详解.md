+++
title = "05. 嵌入式通信协议详解"
date = 2026-01-19
weight = 5000
description = "嵌入式通信协议全面解析：UART、SPI、I2C、CAN、USB工作原理与实战应用"
[taxonomies]
tags = ["embedded", "uart", "spi", "i2c", "can", "protocol"]
+++

# 嵌入式通信协议详解

本文详解嵌入式系统中最常用的通信协议。

---

## 一、协议概览

| 协议 | 类型 | 速率 | 距离 | 典型应用 |
|-----|------|------|------|---------|
| UART | 异步串行 | ~1Mbps | 10m | 调试、GPS、蓝牙模块 |
| SPI | 同步串行 | ~50Mbps | 0.5m | Flash、LCD、传感器 |
| I2C | 同步串行 | ~3.4Mbps | 1m | EEPROM、RTC、传感器 |
| CAN | 差分总线 | 1Mbps | 1000m | 汽车、工业 |
| USB | 差分串行 | 480Mbps | 5m | PC通信、存储 |

---

## 二、UART

### 2.1 信号与时序

```
空闲 ─────┐     ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐     ┌─────
          │起始 │D0│D1│D2│D3│D4│D5│D6│D7│停止│
          └─────┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘     
          
帧格式: [起始位(1)] [数据位(5-9)] [校验位(可选)] [停止位(1-2)]
```

### 2.2 关键参数

| 参数 | 常用值 |
|-----|--------|
| 波特率 | 9600, 115200, 921600 |
| 数据位 | 8 |
| 停止位 | 1 |
| 校验 | None/Even/Odd |

### 2.3 代码示例

```c
// 初始化
void uart_init(uint32_t baudrate) {
    // 使能时钟
    RCC->APB2ENR |= RCC_APB2ENR_USART1EN | RCC_APB2ENR_IOPAEN;
    
    // PA9-TX, PA10-RX
    GPIOA->CRH = (GPIOA->CRH & ~0xFF0) | 0x4B0;
    
    // 配置波特率
    USART1->BRR = SystemCoreClock / baudrate;
    USART1->CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE;
}

// 发送
void uart_send(uint8_t data) {
    while (!(USART1->SR & USART_SR_TXE));
    USART1->DR = data;
}

// 接收
uint8_t uart_recv(void) {
    while (!(USART1->SR & USART_SR_RXNE));
    return USART1->DR;
}
```

---

## 三、SPI

### 3.1 信号线

| 信号 | 方向 | 作用 |
|-----|------|------|
| SCK | 主→从 | 时钟 |
| MOSI | 主→从 | 主发从收 |
| MISO | 从→主 | 从发主收 |
| CS/SS | 主→从 | 片选（低有效） |

### 3.2 时序模式

| 模式 | CPOL | CPHA | 说明 |
|-----|------|------|------|
| Mode 0 | 0 | 0 | 空闲低，第一沿采样 |
| Mode 1 | 0 | 1 | 空闲低，第二沿采样 |
| Mode 2 | 1 | 0 | 空闲高，第一沿采样 |
| Mode 3 | 1 | 1 | 空闲高，第二沿采样 |

### 3.3 代码示例

```c
// 初始化
void spi_init(void) {
    RCC->APB2ENR |= RCC_APB2ENR_SPI1EN;
    
    SPI1->CR1 = SPI_CR1_MSTR |       // 主模式
                SPI_CR1_BR_1 |        // 分频
                SPI_CR1_SSM |         // 软件CS
                SPI_CR1_SSI |
                SPI_CR1_SPE;          // 使能
}

// 传输一字节
uint8_t spi_transfer(uint8_t data) {
    while (!(SPI1->SR & SPI_SR_TXE));
    SPI1->DR = data;
    while (!(SPI1->SR & SPI_SR_RXNE));
    return SPI1->DR;
}

// 读取Flash ID
uint32_t flash_read_id(void) {
    CS_LOW();
    spi_transfer(0x9F);  // JEDEC ID命令
    uint8_t mf = spi_transfer(0xFF);
    uint8_t type = spi_transfer(0xFF);
    uint8_t cap = spi_transfer(0xFF);
    CS_HIGH();
    return (mf << 16) | (type << 8) | cap;
}
```

---

## 四、I2C

### 4.1 信号线

| 信号 | 类型 | 作用 |
|-----|------|------|
| SCL | 开漏 | 时钟（主控制） |
| SDA | 开漏 | 双向数据 |

### 4.2 通信时序

```
起始    地址(7bit)+R/W  ACK    数据     ACK    停止
  S    [A6 A5 A4 A3 A2 A1 A0 RW] [A] [D7...D0] [A]  P
      └────────────────────────┘   └─────────┘
```

### 4.3 代码示例

```c
// 写一字节
void i2c_write_byte(uint8_t addr, uint8_t reg, uint8_t data) {
    I2C1->CR1 |= I2C_CR1_START;
    while (!(I2C1->SR1 & I2C_SR1_SB));
    
    I2C1->DR = (addr << 1);  // 写地址
    while (!(I2C1->SR1 & I2C_SR1_ADDR));
    (void)I2C1->SR2;
    
    I2C1->DR = reg;  // 寄存器
    while (!(I2C1->SR1 & I2C_SR1_TXE));
    
    I2C1->DR = data;  // 数据
    while (!(I2C1->SR1 & I2C_SR1_BTF));
    
    I2C1->CR1 |= I2C_CR1_STOP;
}

// HAL版本
HAL_I2C_Mem_Write(&hi2c1, addr<<1, reg, I2C_MEMADD_SIZE_8BIT, 
                  &data, 1, 100);
```

---

## 五、CAN

### 5.1 特点

| 特性 | 说明 |
|-----|------|
| 差分信号 | 抗干扰强 |
| 多主仲裁 | 非破坏性仲裁 |
| 错误检测 | CRC、位填充、ACK |
| 优先级 | ID越小优先级越高 |

### 5.2 帧格式

```
标准帧: [SOF][11bit ID][RTR][控制][0-8字节数据][CRC][ACK][EOF]
扩展帧: [SOF][29bit ID][RTR][控制][0-8字节数据][CRC][ACK][EOF]
```

### 5.3 代码示例

```c
// 发送CAN消息
void can_send(uint32_t id, uint8_t *data, uint8_t len) {
    CAN_TxHeaderTypeDef header = {
        .StdId = id,
        .IDE = CAN_ID_STD,
        .RTR = CAN_RTR_DATA,
        .DLC = len,
    };
    uint32_t mailbox;
    HAL_CAN_AddTxMessage(&hcan, &header, data, &mailbox);
}

// 接收回调
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan) {
    CAN_RxHeaderTypeDef header;
    uint8_t data[8];
    HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &header, data);
    process_can_message(header.StdId, data, header.DLC);
}
```

---

## 六、协议选择指南

| 场景 | 推荐协议 | 原因 |
|-----|---------|------|
| 调试输出 | UART | 简单，一对一 |
| 高速外设 | SPI | 速度快，全双工 |
| 多传感器 | I2C | 省引脚，地址寻址 |
| 汽车/工业 | CAN | 可靠，长距离 |
| PC连接 | USB | 通用，速度快 |

---

## 总结

- **UART**: 最简单，异步通信，调试首选
- **SPI**: 速度最快，适合Flash/LCD
- **I2C**: 最省引脚，适合多传感器
- **CAN**: 最可靠，适合汽车/工业

根据应用需求选择合适的协议是嵌入式设计的关键决策。

---

## 相关文章

- [上一篇：嵌入式开发环境与工具链](@/articles/embedded/embedded-04-开发环境与工具链.md)
- [下一篇：RTOS实时操作系统详解](@/articles/embedded/embedded-06-RTOS实时操作系统.md)
