+++
title = "17.Rust性能调优实战"
date = 2026-01-21
description = "深入剖析Rust性能调优工具和技术，包括flamegraph、perf、criterion、内存分析和编译时间优化"
[taxonomies]
tags = ["Rust", "性能调优", "Profiling", "Benchmark", "优化"]
+++

## 概述

性能调优需要测量先行。本文介绍Rust生态中常用的性能分析和优化工具。

---

## 一、Criterion基准测试

### 1.1 基本使用

```rust
// benches/my_benchmark.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn fibonacci(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

fn criterion_benchmark(c: &mut Criterion) {
    c.bench_function("fib 20", |b| {
        b.iter(|| fibonacci(black_box(20)))
    });
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
```

```toml
# Cargo.toml
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "my_benchmark"
harness = false
```

### 1.2 对比测试

```rust
use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId};

fn compare_implementations(c: &mut Criterion) {
    let mut group = c.benchmark_group("Sort Algorithms");
    
    for size in [100, 1000, 10000].iter() {
        let data: Vec<i32> = (0..*size).rev().collect();
        
        group.bench_with_input(
            BenchmarkId::new("std::sort", size),
            &data,
            |b, data| {
                b.iter(|| {
                    let mut d = data.clone();
                    d.sort();
                    d
                })
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("std::sort_unstable", size),
            &data,
            |b, data| {
                b.iter(|| {
                    let mut d = data.clone();
                    d.sort_unstable();
                    d
                })
            },
        );
    }
    
    group.finish();
}

criterion_group!(benches, compare_implementations);
criterion_main!(benches);
```

### 1.3 吞吐量测试

```rust
use criterion::{criterion_group, criterion_main, Criterion, Throughput};

fn throughput_bench(c: &mut Criterion) {
    let data = vec![0u8; 1024 * 1024];  // 1MB
    
    let mut group = c.benchmark_group("Throughput");
    group.throughput(Throughput::Bytes(data.len() as u64));
    
    group.bench_function("checksum", |b| {
        b.iter(|| {
            let sum: u8 = data.iter().fold(0u8, |acc, &x| acc.wrapping_add(x));
            sum
        })
    });
    
    group.finish();
}

criterion_group!(benches, throughput_bench);
criterion_main!(benches);
```

---

## 二、Flamegraph

### 2.1 安装和使用

```bash
# 安装
cargo install flamegraph

# 生成火焰图（需要root或perf权限）
cargo flamegraph --bin my_app

# 或者
cargo flamegraph -- --my-arg value

# 输出: flamegraph.svg
```

### 2.2 理解火焰图

```
火焰图解读：
- X轴：函数占用的采样比例（不是时间顺序）
- Y轴：调用栈深度
- 宽度：该函数（包含子调用）的时间占比

关注点：
- 宽的平台：热点函数
- 窄的尖塔：深度调用但不耗时
- 相邻的窄条：频繁小调用

优化目标：
- 减少最宽平台的宽度
- 减少不必要的调用深度
```

### 2.3 差异火焰图

```bash
# 生成基线
cargo flamegraph --bin my_app -o baseline.svg

# 修改代码后生成新的
cargo flamegraph --bin my_app -o new.svg

# 使用inferno生成差异图
cargo install inferno
inferno-diff-folded baseline.folded new.folded | \
    inferno-flamegraph > diff.svg
```

---

## 三、perf分析

### 3.1 基本使用

```bash
# 编译带调试信息的release
cargo build --release
export CARGO_PROFILE_RELEASE_DEBUG=true

# CPU分析
perf record -g ./target/release/my_app
perf report

# 统计
perf stat ./target/release/my_app

# 缓存分析
perf stat -e cache-references,cache-misses,\
L1-dcache-load-misses,LLC-load-misses ./target/release/my_app
```

### 3.2 Rust特定技巧

```bash
# 保留符号名（防止名称修饰）
RUSTFLAGS="-C symbol-mangling-version=v0" cargo build --release

# 保留帧指针（更准确的栈回溯）
RUSTFLAGS="-C force-frame-pointers=yes" cargo build --release

# 组合使用
RUSTFLAGS="-C force-frame-pointers=yes -C symbol-mangling-version=v0" \
    cargo build --release
```

### 3.3 常用perf事件

```bash
# CPU周期和指令
perf stat -e cycles,instructions ./app

# 分支预测
perf stat -e branches,branch-misses ./app

# 缓存
perf stat -e L1-dcache-loads,L1-dcache-load-misses,\
LLC-loads,LLC-load-misses ./app

# 内存带宽相关
perf stat -e mem_load_retired.l3_miss,\
mem_load_retired.l3_hit ./app

# 前端/后端瓶颈
perf stat -e cpu-cycles,stalled-cycles-frontend,\
stalled-cycles-backend ./app
```

---

## 四、内存分析

### 4.1 heaptrack

```bash
# 安装
sudo apt install heaptrack

# 运行
heaptrack ./target/release/my_app

# 分析
heaptrack_gui heaptrack.my_app.*.gz
```

### 4.2 DHAT (Valgrind)

```bash
# 使用DHAT
valgrind --tool=dhat ./target/release/my_app

# 查看报告
dhat-viewer dhat.out.*
```

### 4.3 Rust内存分析器

```rust
// 使用dhat-rs进行运行时分析
use dhat::{Dhat, DhatAlloc};

#[global_allocator]
static ALLOC: DhatAlloc = DhatAlloc;

fn main() {
    let _dhat = Dhat::start_heap_profiling();
    
    // 你的代码
    let v: Vec<i32> = (0..1000).collect();
    
    // 程序结束时输出分析报告
}
```

### 4.4 追踪分配

```rust
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};

struct CountingAllocator;

static ALLOCATED: AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOCATED.fetch_add(layout.size(), Ordering::SeqCst);
        System.alloc(layout)
    }
    
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        ALLOCATED.fetch_sub(layout.size(), Ordering::SeqCst);
        System.dealloc(ptr, layout)
    }
}

#[global_allocator]
static ALLOCATOR: CountingAllocator = CountingAllocator;

fn main() {
    println!("Allocated: {} bytes", ALLOCATED.load(Ordering::SeqCst));
    
    let v: Vec<i32> = (0..1000).collect();
    println!("After Vec: {} bytes", ALLOCATED.load(Ordering::SeqCst));
    
    drop(v);
    println!("After drop: {} bytes", ALLOCATED.load(Ordering::SeqCst));
}
```

---

## 五、编译时间优化

### 5.1 测量编译时间

```bash
# 详细编译时间
cargo build --timings

# 生成 cargo-timing.html

# 或使用cargo-bloat查看crate大小影响
cargo install cargo-bloat
cargo bloat --release --crates
```

### 5.2 减少编译时间

```toml
# Cargo.toml

# 开发时使用更快的链接器
[target.x86_64-unknown-linux-gnu]
linker = "clang"
rustflags = ["-C", "link-arg=-fuse-ld=lld"]

# 分离编译
[profile.dev]
split-debuginfo = "unpacked"

# 增量编译
[profile.dev]
incremental = true

# release也启用增量（牺牲一点优化换速度）
[profile.release]
incremental = true
```

### 5.3 减少依赖

```bash
# 查看依赖树
cargo tree

# 查看重复依赖
cargo tree --duplicates

# 查看特性标志
cargo tree --features
```

```toml
# 禁用不需要的特性
[dependencies]
tokio = { version = "1", default-features = false, features = ["rt", "net"] }
serde = { version = "1", default-features = false, features = ["derive"] }
```

---

## 六、运行时分析

### 6.1 tracing

```rust
use tracing::{info, span, Level, instrument};
use tracing_subscriber;

#[instrument]
fn process_order(order_id: u64) {
    info!("Processing order");
    validate_order(order_id);
    execute_order(order_id);
}

#[instrument]
fn validate_order(order_id: u64) {
    // 验证逻辑
}

#[instrument]
fn execute_order(order_id: u64) {
    // 执行逻辑
}

fn main() {
    tracing_subscriber::fmt()
        .with_max_level(Level::TRACE)
        .init();
    
    process_order(12345);
}
```

### 6.2 自定义计时

```rust
use std::time::Instant;

macro_rules! timed {
    ($name:expr, $block:expr) => {{
        let start = Instant::now();
        let result = $block;
        let elapsed = start.elapsed();
        println!("{}: {:?}", $name, elapsed);
        result
    }};
}

fn main() {
    let result = timed!("sort", {
        let mut v: Vec<i32> = (0..10000).rev().collect();
        v.sort();
        v
    });
}
```

### 6.3 统计收集

```rust
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

struct Stats {
    count: AtomicU64,
    total_ns: AtomicU64,
    min_ns: AtomicU64,
    max_ns: AtomicU64,
}

impl Stats {
    const fn new() -> Self {
        Self {
            count: AtomicU64::new(0),
            total_ns: AtomicU64::new(0),
            min_ns: AtomicU64::new(u64::MAX),
            max_ns: AtomicU64::new(0),
        }
    }
    
    fn record(&self, duration_ns: u64) {
        self.count.fetch_add(1, Ordering::Relaxed);
        self.total_ns.fetch_add(duration_ns, Ordering::Relaxed);
        
        // 更新min/max（简化版，非完全原子）
        let mut current = self.min_ns.load(Ordering::Relaxed);
        while duration_ns < current {
            match self.min_ns.compare_exchange_weak(
                current, duration_ns, Ordering::Relaxed, Ordering::Relaxed
            ) {
                Ok(_) => break,
                Err(c) => current = c,
            }
        }
    }
    
    fn report(&self) {
        let count = self.count.load(Ordering::Relaxed);
        let total = self.total_ns.load(Ordering::Relaxed);
        let min = self.min_ns.load(Ordering::Relaxed);
        let max = self.max_ns.load(Ordering::Relaxed);
        
        println!("Count: {}", count);
        println!("Avg: {} ns", total / count.max(1));
        println!("Min: {} ns", min);
        println!("Max: {} ns", max);
    }
}

static ORDER_STATS: Stats = Stats::new();

fn process_order() {
    let start = Instant::now();
    // 处理订单
    let elapsed = start.elapsed().as_nanos() as u64;
    ORDER_STATS.record(elapsed);
}
```

---

## 总结

| 工具 | 用途 | 开销 |
|------|------|------|
| criterion | 微基准测试 | 无（测试时） |
| flamegraph | CPU热点 | 低 |
| perf | 系统级分析 | 低 |
| heaptrack | 内存分析 | 中 |
| tracing | 运行时追踪 | 可配置 |

**性能调优流程**：
1. 使用criterion建立基线
2. 使用flamegraph识别热点
3. 使用perf深入分析
4. 优化并重新测量
5. 自动化回归检测

---

## 相关文章

- [上一篇：HFT-Rust高性能网络编程](/articles/rust/rust-16-HFT-Rust高性能网络编程/)
- [下一篇：Rust宏系统详解](/articles/rust/rust-18-Rust宏系统详解/)
