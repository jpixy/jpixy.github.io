+++
title = "07.嵌入式调试与故障排查"
date = 2026-01-19
description = "嵌入式调试技巧：硬件调试、软件调试、常见问题排查、调试工具使用"
[taxonomies]
tags = ["embedded", "debugging", "oscilloscope", "logic-analyzer", "troubleshooting"]
+++

# 嵌入式调试与故障排查

本文详解嵌入式开发中的调试技巧与常见问题排查方法。

---

## 一、调试工具

### 1.1 硬件工具

| 工具 | 用途 | 价格 |
|-----|------|------|
| 万用表 | 电压、通断检测 | ¥50+ |
| 示波器 | 波形分析 | ¥300+ |
| 逻辑分析仪 | 数字信号、协议分析 | ¥50+ |
| USB转TTL | 串口调试 | ¥10 |
| J-Link/ST-Link | 程序调试 | ¥15+ |
| 热风枪 | 芯片温度测试 | ¥100+ |

### 1.2 软件工具

| 工具 | 用途 |
|-----|------|
| GDB | 断点调试 |
| OpenOCD | 调试服务器 |
| PulseView | 逻辑分析仪软件 |
| Wireshark | 网络/CAN分析 |
| Serial Monitor | 串口监控 |

---

## 二、软件调试

### 2.1 串口打印

```c
// 重定向printf
int _write(int file, char *ptr, int len) {
    HAL_UART_Transmit(&huart1, (uint8_t*)ptr, len, HAL_MAX_DELAY);
    return len;
}

// 分级日志
#define LOG_LEVEL_DEBUG  0
#define LOG_LEVEL_INFO   1
#define LOG_LEVEL_ERROR  2

#define LOG_LEVEL  LOG_LEVEL_DEBUG

#define LOG_DEBUG(fmt, ...) \
    if (LOG_LEVEL <= LOG_LEVEL_DEBUG) printf("[D] " fmt "\n", ##__VA_ARGS__)
#define LOG_INFO(fmt, ...) \
    if (LOG_LEVEL <= LOG_LEVEL_INFO) printf("[I] " fmt "\n", ##__VA_ARGS__)
#define LOG_ERROR(fmt, ...) \
    if (LOG_LEVEL <= LOG_LEVEL_ERROR) printf("[E] " fmt "\n", ##__VA_ARGS__)
```

### 2.2 断言

```c
#ifdef DEBUG
#define ASSERT(expr) do { \
    if (!(expr)) { \
        printf("ASSERT: %s @ %s:%d\n", #expr, __FILE__, __LINE__); \
        while(1) { __BKPT(0); } \
    } \
} while(0)
#else
#define ASSERT(expr) ((void)0)
#endif

// 使用
void spi_transfer(uint8_t *buf, uint16_t len) {
    ASSERT(buf != NULL);
    ASSERT(len > 0 && len <= MAX_LEN);
    // ...
}
```

### 2.3 HardFault分析

```c
// 获取故障寄存器
void HardFault_Handler(void) {
    __asm volatile (
        "TST LR, #4\n"
        "ITE EQ\n"
        "MRSEQ R0, MSP\n"
        "MRSNE R0, PSP\n"
        "B fault_handler\n"
    );
}

void fault_handler(uint32_t *stack) {
    printf("=== HardFault ===\n");
    printf("PC:  0x%08X\n", stack[6]);  // 故障位置
    printf("LR:  0x%08X\n", stack[5]);
    printf("R0:  0x%08X\n", stack[0]);
    printf("CFSR: 0x%08X\n", SCB->CFSR);
    
    // 分析CFSR
    if (SCB->CFSR & 0x8000) printf("  BFARVALID\n");
    if (SCB->CFSR & 0x0200) printf("  IMPRECISERR\n");
    if (SCB->CFSR & 0x0100) printf("  PRECISERR\n");
    
    while(1);
}
```

---

## 三、硬件调试

### 3.1 示波器使用

| 场景 | 测量方法 |
|-----|---------|
| 检查时钟 | 测量晶振/PLL输出 |
| PWM验证 | 测量占空比和频率 |
| 通信问题 | 抓取SPI/I2C波形 |
| 电源纹波 | AC耦合测量 |
| 启动时序 | 测量上电时序 |

### 3.2 逻辑分析仪

```
# PulseView使用
1. 连接探头到信号线
2. 设置采样率（≥10x信号频率）
3. 选择协议解码器（UART/SPI/I2C）
4. 配置协议参数
5. 触发采集
```

### 3.3 电源检查清单

| 检查项 | 正常值 |
|-------|--------|
| 3.3V电源 | 3.2~3.4V |
| 电源纹波 | <50mV |
| 启动时间 | <100ms达到稳定 |
| 负载能力 | 电流足够 |

---

## 四、常见问题排查

### 4.1 程序无法烧录

| 现象 | 原因 | 解决 |
|-----|------|------|
| 无法连接 | 线接错/虚焊 | 检查SWD连线 |
| ID读取失败 | 电源问题 | 检查3.3V电源 |
| 烧录超时 | Flash锁定 | 全片擦除 |
| 无法停止 | 看门狗运行 | 上电后立即连接 |

### 4.2 程序运行异常

| 现象 | 可能原因 |
|-----|---------|
| 启动即死机 | 栈指针错误，时钟配置错 |
| 随机死机 | 栈溢出，野指针 |
| 外设不工作 | 时钟未开，引脚复用错 |
| 中断不触发 | NVIC未配置，优先级问题 |
| 数据错误 | 大小端，对齐问题 |

### 4.3 通信故障

| 问题 | 检查项 |
|-----|--------|
| UART乱码 | 波特率、电平匹配 |
| I2C无应答 | 地址、上拉电阻 |
| SPI数据错 | 时钟极性、相位 |
| CAN离线 | 终端电阻、波特率 |

---

## 五、调试技巧

### 5.1 二分法定位

```c
// 在代码中插入检查点
void problematic_function(void) {
    LOG_DEBUG("CP1");  // 检查点1
    step1();
    
    LOG_DEBUG("CP2");  // 检查点2
    step2();
    
    LOG_DEBUG("CP3");  // 执行到这里？
    step3();
}
```

### 5.2 GPIO调试

```c
// 用GPIO指示程序状态
#define DEBUG_PIN_HIGH()  GPIOA->BSRR = GPIO_PIN_0
#define DEBUG_PIN_LOW()   GPIOA->BRR = GPIO_PIN_0
#define DEBUG_PIN_TOGGLE() GPIOA->ODR ^= GPIO_PIN_0

void isr_handler(void) {
    DEBUG_PIN_HIGH();  // 用示波器测量中断时间
    process();
    DEBUG_PIN_LOW();
}
```

### 5.3 内存检查

```c
// 检测栈使用
void fill_stack_pattern(void) {
    extern uint32_t _estack, _Min_Stack_Size;
    uint32_t *p = (uint32_t*)((uint32_t)&_estack - (uint32_t)&_Min_Stack_Size);
    while (p < &_estack) *p++ = 0xDEADBEEF;
}

uint32_t check_stack_usage(void) {
    extern uint32_t _estack, _Min_Stack_Size;
    uint32_t *p = (uint32_t*)((uint32_t)&_estack - (uint32_t)&_Min_Stack_Size);
    uint32_t used = 0;
    while (*p++ == 0xDEADBEEF);
    return (uint32_t)&_estack - (uint32_t)p;
}
```

---

## 六、生产问题调试

### 6.1 现场日志

```c
// 环形日志缓冲区
#define LOG_BUF_SIZE 4096
static char log_buffer[LOG_BUF_SIZE];
static uint16_t log_head = 0;

void log_write(const char *msg) {
    uint32_t ts = HAL_GetTick();
    int len = snprintf(&log_buffer[log_head], 128, 
                       "[%08lu] %s\n", ts, msg);
    log_head = (log_head + len) % LOG_BUF_SIZE;
}

// 故障时保存到Flash
void save_crash_log(void) {
    flash_write(CRASH_LOG_ADDR, log_buffer, LOG_BUF_SIZE);
}
```

### 6.2 远程诊断

```c
// 通过命令行接口诊断
typedef struct {
    const char *name;
    void (*handler)(int argc, char **argv);
} cli_cmd_t;

const cli_cmd_t commands[] = {
    {"status", cmd_status},     // 显示系统状态
    {"mem", cmd_memory},        // 显示内存使用
    {"regs", cmd_registers},    // 显示寄存器
    {"reset", cmd_reset},       // 复位系统
};
```

---

## 总结

调试能力是嵌入式工程师的核心竞争力：

| 能力 | 关键技能 |
|-----|---------|
| 硬件调试 | 示波器、逻辑分析仪使用 |
| 软件调试 | GDB、断言、日志 |
| 问题定位 | 二分法、现象分析 |
| 生产支持 | 日志系统、远程诊断 |

这些技能是AI无法替代的——因为需要与真实硬件交互。
