+++
title = "07.嵌入式Rust"
date = 2026-01-19
description = "嵌入式Rust：no_std开发、裸机编程、HAL抽象、常用外设、RTOS集成"
[taxonomies]
tags = ["Rust", "嵌入式", "裸机"]
+++

## 嵌入式Rust概述

### 优势

- **内存安全**：无GC的内存安全
- **零成本抽象**：高级特性无运行时开销
- **并发安全**：编译期防止数据竞争
- **现代工具链**：Cargo、文档、测试

### 目标平台

| 目标 | 说明 |
|------|------|
| thumbv6m-none-eabi | Cortex-M0/M0+ |
| thumbv7m-none-eabi | Cortex-M3 |
| thumbv7em-none-eabi | Cortex-M4/M7（无FPU） |
| thumbv7em-none-eabihf | Cortex-M4/M7（有FPU） |
| riscv32imac-unknown-none-elf | RISC-V 32位 |

### 工具安装

```bash
# 安装目标
rustup target add thumbv7em-none-eabihf

# 安装工具
cargo install cargo-binutils
rustup component add llvm-tools-preview

# 调试工具
cargo install probe-rs
```

---

## no_std环境

### 禁用标准库

```rust
#![no_std]  // 不使用std
#![no_main] // 不使用标准main入口

use core::panic::PanicInfo;

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}
```

### core和alloc

| 库 | 内容 |
|----|------|
| core | 语言基础，无OS依赖 |
| alloc | 堆分配相关，需要实现allocator |

```rust
#![no_std]

extern crate alloc;
use alloc::vec::Vec;

// 需要提供全局分配器
use embedded_alloc::Heap;

#[global_allocator]
static HEAP: Heap = Heap::empty();
```

### 入口点

```rust
#![no_std]
#![no_main]

use cortex_m_rt::entry;

#[entry]
fn main() -> ! {
    // 初始化
    loop {
        // 主循环
    }
}
```

---

## 裸机编程

### 内存映射

```rust
// 直接访问寄存器
const GPIOA_BASE: u32 = 0x4002_0000;
const GPIOA_ODR: *mut u32 = (GPIOA_BASE + 0x14) as *mut u32;

unsafe {
    // 设置输出
    core::ptr::write_volatile(GPIOA_ODR, 1 << 5);
    
    // 读取
    let value = core::ptr::read_volatile(GPIOA_ODR);
}
```

### volatile访问

```rust
use volatile_register::{RO, RW, WO};

#[repr(C)]
struct GpioRegs {
    moder: RW<u32>,   // 读写
    otyper: RW<u32>,
    ospeedr: RW<u32>,
    pupdr: RW<u32>,
    idr: RO<u32>,     // 只读
    odr: RW<u32>,
    bsrr: WO<u32>,    // 只写
}

unsafe {
    let gpio = &*(0x4002_0000 as *const GpioRegs);
    gpio.odr.write(0x1);
}
```

### 中断

```rust
use cortex_m::interrupt;

// 禁用中断
interrupt::free(|_cs| {
    // 临界区代码
});

// 中断处理程序
#[interrupt]
fn TIM2() {
    // 定时器中断处理
}
```

---

## HAL抽象

### embedded-hal

定义通用硬件抽象接口：

```rust
// GPIO
pub trait OutputPin {
    fn set_high(&mut self) -> Result<(), Self::Error>;
    fn set_low(&mut self) -> Result<(), Self::Error>;
}

pub trait InputPin {
    fn is_high(&self) -> Result<bool, Self::Error>;
    fn is_low(&self) -> Result<bool, Self::Error>;
}

// 延时
pub trait DelayMs<UXX> {
    fn delay_ms(&mut self, ms: UXX);
}
```

### 使用HAL

```rust
use stm32f4xx_hal::{
    gpio::GpioExt,
    prelude::*,
    stm32,
};

#[entry]
fn main() -> ! {
    let dp = stm32::Peripherals::take().unwrap();
    let gpioa = dp.GPIOA.split();
    
    let mut led = gpioa.pa5.into_push_pull_output();
    
    loop {
        led.set_high();
        delay.delay_ms(500u32);
        led.set_low();
        delay.delay_ms(500u32);
    }
}
```

---

## 常用外设

### GPIO

```rust
use stm32f4xx_hal::gpio::{Edge, Input, Output, PullUp, PushPull};

// 输出
let mut led: PA5<Output<PushPull>> = gpioa.pa5.into_push_pull_output();
led.set_high();
led.toggle();

// 输入
let button: PA0<Input<PullUp>> = gpioa.pa0.into_pull_up_input();
if button.is_low() {
    // 按钮按下
}
```

### UART

```rust
use stm32f4xx_hal::serial::{Config, Serial};

let tx = gpioa.pa2.into_alternate();
let rx = gpioa.pa3.into_alternate();

let mut serial = Serial::new(
    dp.USART2,
    (tx, rx),
    Config::default().baudrate(115200.bps()),
    &clocks,
).unwrap();

// 发送
serial.write(b'H').unwrap();
serial.write_str("Hello\r\n").unwrap();

// 接收
if let Ok(byte) = serial.read() {
    // 处理接收的字节
}
```

### SPI

```rust
use stm32f4xx_hal::spi::{Mode, Phase, Polarity, Spi};

let sck = gpioa.pa5.into_alternate();
let miso = gpioa.pa6.into_alternate();
let mosi = gpioa.pa7.into_alternate();

let mut spi = Spi::new(
    dp.SPI1,
    (sck, miso, mosi),
    Mode {
        polarity: Polarity::IdleLow,
        phase: Phase::CaptureOnFirstTransition,
    },
    1.MHz(),
    &clocks,
);

// 传输
let mut buf = [0u8; 4];
spi.transfer(&mut buf).unwrap();
```

### I2C

```rust
use stm32f4xx_hal::i2c::I2c;

let scl = gpiob.pb6.into_alternate_open_drain();
let sda = gpiob.pb7.into_alternate_open_drain();

let mut i2c = I2c::new(
    dp.I2C1,
    (scl, sda),
    400.kHz(),
    &clocks,
);

// 写入
i2c.write(0x50, &[0x00, 0x01, 0x02]).unwrap();

// 读取
let mut buf = [0u8; 4];
i2c.read(0x50, &mut buf).unwrap();
```

### 定时器

```rust
use stm32f4xx_hal::timer::Timer;

let mut timer = Timer::new(dp.TIM2, &clocks).counter_hz();
timer.start(1.Hz()).unwrap();

loop {
    nb::block!(timer.wait()).unwrap();
    // 每秒执行一次
}
```

### PWM

```rust
let pwm = Timer::new(dp.TIM3, &clocks).pwm_hz(
    gpioa.pa6.into_alternate(),
    1.kHz(),
);

let mut channel = pwm.split();
channel.set_duty(channel.get_max_duty() / 2);  // 50%占空比
channel.enable();
```

---

## RTOS集成

### RTIC框架

```rust
#[rtic::app(device = stm32f4xx_hal::stm32, peripherals = true)]
mod app {
    use stm32f4xx_hal::prelude::*;
    
    #[shared]
    struct Shared {
        counter: u32,
    }
    
    #[local]
    struct Local {
        led: PA5<Output<PushPull>>,
    }
    
    #[init]
    fn init(ctx: init::Context) -> (Shared, Local, init::Monotonics) {
        let gpioa = ctx.device.GPIOA.split();
        let led = gpioa.pa5.into_push_pull_output();
        
        (
            Shared { counter: 0 },
            Local { led },
            init::Monotonics(),
        )
    }
    
    #[task(binds = TIM2, shared = [counter], local = [led])]
    fn timer_tick(ctx: timer_tick::Context) {
        ctx.local.led.toggle();
        
        ctx.shared.counter.lock(|counter| {
            *counter += 1;
        });
    }
}
```

### Embassy异步

```rust
#![no_std]
#![no_main]
#![feature(type_alias_impl_trait)]

use embassy_executor::Spawner;
use embassy_stm32::gpio::{Level, Output, Speed};
use embassy_time::{Duration, Timer};

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    let p = embassy_stm32::init(Default::default());
    let mut led = Output::new(p.PA5, Level::Low, Speed::Low);
    
    loop {
        led.set_high();
        Timer::after(Duration::from_millis(500)).await;
        led.set_low();
        Timer::after(Duration::from_millis(500)).await;
    }
}
```

---

## 调试

### probe-rs

```bash
# 烧录
cargo flash --chip STM32F411CEUx

# 运行并打印RTT输出
cargo embed

# GDB调试
cargo embed --gdb
```

### defmt日志

```rust
use defmt::info;
use defmt_rtt as _;

info!("Hello, world!");
info!("Value: {}", 42);
```

### panic处理

```rust
use panic_probe as _;

// 或自定义
#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    defmt::error!("Panic: {:?}", defmt::Debug2Format(info));
    loop {}
}
```

---

## 项目结构

```
project/
├── Cargo.toml
├── memory.x           # 链接脚本
├── .cargo/config.toml # Cargo配置
└── src/
    └── main.rs
```

### Cargo.toml

```toml
[package]
name = "my-embedded-app"
version = "0.1.0"
edition = "2021"

[dependencies]
cortex-m = "0.7"
cortex-m-rt = "0.7"
stm32f4xx-hal = { version = "0.18", features = ["stm32f411"] }
panic-probe = { version = "0.3", features = ["print-defmt"] }
defmt = "0.3"
defmt-rtt = "0.4"

[profile.release]
opt-level = "z"
lto = true
```

### .cargo/config.toml

```toml
[target.thumbv7em-none-eabihf]
runner = "probe-rs run --chip STM32F411CEUx"

[build]
target = "thumbv7em-none-eabihf"
```

---

## 总结

| 概念 | 说明 |
|------|------|
| no_std | 无标准库环境 |
| embedded-hal | 硬件抽象层 |
| PAC | 外设访问crate |
| HAL | 高级硬件抽象 |
| RTIC | 实时中断并发 |
| Embassy | 异步嵌入式 |

嵌入式Rust提供了C/C++级别的性能和控制，同时具有内存安全保证，是嵌入式开发的新选择。
