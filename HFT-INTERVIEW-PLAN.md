# HFT面试准备 - 文章补充实施计划

> 创建日期：2026-01-21
> 最后更新：2026-01-21
> 目标：针对HFT（高频交易）公司SRE、C++、Rust、Python职位的笔试和面试准备
> 预计新增：~87篇文章

---

## 一、现有覆盖情况

| 类别 | 现有篇数 | HFT相关度 | 缺口评估 |
|------|----------|-----------|----------|
| C/C++ (ccpp) | 13篇 | 中 | **严重缺乏HFT深度话题** |
| Rust (rust) | 8篇 | 中 | **缺乏HFT专项与底层细节** |
| Python (python) | 47篇 | 高(算法) | 缺乏性能优化与量化专项 |
| HFT (hft) | 11篇 | 高 | 缺乏面试题与实战 |
| SRE (sre) | 60篇 | 高 | 缺乏低延迟专项 |
| 网络 (networking) | 17篇 | 中 | 缺乏Kernel Bypass深入 |

---

## 二、C++ HFT面试专项（新增30篇）

### 2.1 C++语言核心深度（8篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| cpp-14 | 深浅拷贝与移动语义详解 | 拷贝构造vs移动构造、std::move原理、RVO/NRVO、Copy Elision、Rule of 0/3/5、Perfect Forwarding | ⭐⭐⭐ | ⬜ |
| cpp-15 | 内存模型与缓存优化 | Cache Line (64B)、False Sharing、Memory Ordering (acquire/release/seq_cst)、Memory Barrier、CPU缓存层次、Prefetch | ⭐⭐⭐ | ⬜ |
| cpp-16 | 虚函数与多态底层实现 | vtable/vptr布局、虚函数调用开销、devirtualization、CRTP静态多态、final优化 | ⭐⭐⭐ | ⬜ |
| cpp-17 | 编译期计算与constexpr | constexpr函数、consteval (C++20)、编译期字符串、编译期容器、模板元编程vs constexpr | ⭐⭐ | ⬜ |
| cpp-18 | 类型萃取与SFINAE详解 | std::enable_if、std::void_t、Concepts (C++20)、if constexpr、类型特性检测 | ⭐⭐ | ⬜ |
| cpp-19 | 异常处理机制与性能开销 | 异常表、栈展开、noexcept优化、HFT中的异常策略、Error Code vs Exception | ⭐⭐ | ⬜ |
| cpp-20 | 自定义内存分配器设计 | std::allocator接口、Arena Allocator、Pool Allocator、Slab Allocator、jemalloc/tcmalloc原理 | ⭐⭐⭐ | ⬜ |
| cpp-21 | 智能指针底层与陷阱 | shared_ptr原子操作开销、make_shared优化、weak_ptr用途、unique_ptr零开销、自定义Deleter | ⭐⭐ | ⬜ |

### 2.2 C++ HFT高性能专项（7篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| cpp-22 | Lock-Free数据结构详解 | CAS原语、ABA问题、Lock-Free Queue (SPSC/MPSC/MPMC)、Hazard Pointer、RCU、Memory Reclamation | ⭐⭐⭐ | ⬜ |
| cpp-23 | SIMD编程详解 | SSE/AVX/AVX-512、intrinsics、自动向量化、SIMD数据结构、案例：快速解析、校验计算 | ⭐⭐⭐ | ⬜ |
| cpp-24 | 分支预测与热路径优化 | likely/unlikely、PGO、Branch-Free编程、Lookup Table替代分支、Branchless算法 | ⭐⭐⭐ | ⬜ |
| cpp-25 | 缓存友好数据结构设计 | SOA vs AOS、Data-Oriented Design、Cache-Oblivious算法、Hot/Cold Splitting、Struct Padding | ⭐⭐⭐ | ⬜ |
| cpp-26 | CPU亲和性与NUMA优化 | pthread_setaffinity_np、isolcpus、NUMA内存分配、numactl、CPU拓扑感知 | ⭐⭐ | ⬜ |
| cpp-27 | 高精度时间测量 | RDTSC/RDTSCP、clock_gettime、TSC校准、纳秒级计时、时间戳同步 | ⭐⭐ | ⬜ |
| cpp-28 | 编译器优化与Profile | -O3 vs -Ofast、LTO、PGO、Godbolt使用、perf分析、VTune/Instruments | ⭐⭐ | ⬜ |

### 2.3 C++ HFT面试题（5篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| cpp-29 | C++面试题-语言基础篇 | 指针vs引用、const语义、static语义、inline语义、类型转换、初始化列表、POD类型 | ⭐⭐⭐ | ⬜ |
| cpp-30 | C++面试题-内存与对象模型 | 对象内存布局、虚继承、空基类优化、对齐、new/delete重载、placement new | ⭐⭐⭐ | ⬜ |
| cpp-31 | C++面试题-并发与多线程 | std::atomic、memory_order、mutex/lock_guard、condition_variable、死锁预防、线程池 | ⭐⭐⭐ | ⬜ |
| cpp-32 | C++面试题-STL深度 | 容器实现原理、迭代器失效、allocator、算法复杂度、string SSO、vector扩容 | ⭐⭐ | ⬜ |
| cpp-33 | C++面试题-HFT系统设计 | Order Book实现、Market Data Handler、执行引擎设计、延迟测量、热路径分析 | ⭐⭐⭐ | ⬜ |

### 2.4 C++高级特性补充（4篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| cpp-34 | 模板高级技巧详解 | 变参模板(Variadic)、模板特化/偏特化、CRTP深入、Expression Templates、Tag Dispatch | ⭐⭐⭐ | ⬜ |
| cpp-35 | C++20/23新特性详解 | Concepts、Ranges、Coroutines、Modules、std::format、std::expected、std::span | ⭐⭐ | ⬜ |
| cpp-36 | Lambda与函数对象详解 | Lambda底层实现、捕获原理、generic lambda、mutable、constexpr lambda、std::function开销 | ⭐⭐ | ⬜ |
| cpp-37 | 字符串处理优化 | std::string_view、SSO详解、字符串解析优化、零拷贝字符串、固定长度字符串 | ⭐⭐ | ⬜ |

### 2.5 C++测试与工具链（3篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| cpp-38 | C++测试与调试实战 | GTest/GMock、Sanitizers(ASan/TSan/UBSan/MSan)、Valgrind、gdb高级技巧、core dump分析 | ⭐⭐⭐ | ⬜ |
| cpp-39 | 性能基准测试设计 | Google Benchmark、统计显著性、微基准陷阱、A/B测试、性能回归检测、perf stat | ⭐⭐ | ⬜ |
| cpp-40 | C++构建系统与工具链 | CMake高级用法、Bazel入门、ccache/sccache、编译优化、clang-tidy、include-what-you-use | ⭐⭐ | ⬜ |

### 2.6 硬件与微架构（3篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| cpp-41 | CPU微架构与性能优化 | CPU流水线、乱序执行、指令级并行(ILP)、µop缓存、分支预测器原理、前端/后端瓶颈、perf c2c | ⭐⭐⭐ | ⬜ |
| cpp-42 | 内存层次与带宽优化 | DRAM时序(CAS Latency)、内存通道、带宽计算、Memory-bound vs Compute-bound、内存预取策略、NUMA深入 | ⭐⭐ | ⬜ |
| cpp-43 | C++协程与用户态调度 | C++20 Coroutines、co_await/co_yield/co_return、协程vs线程开销、Fiber库(Boost.Fiber)、调度器设计 | ⭐⭐ | ⬜ |

---

## 三、Rust HFT面试专项（新增13篇）

### 3.1 Rust语言深度（6篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| rust-09 | unsafe Rust完全指南 | unsafe块、裸指针、unsafe trait、内存安全不变量、FFI边界、Miri检测 | ⭐⭐⭐ | ⬜ |
| rust-10 | Rust与C/C++互操作 | FFI声明、bindgen/cbindgen、内存传递、回调函数、异常安全、ABI兼容 | ⭐⭐⭐ | ⬜ |
| rust-11 | Rust内存布局与对齐 | repr(C)/repr(packed)/repr(align)、ZST、DST、内存布局可视化、union | ⭐⭐⭐ | ⬜ |
| rust-12 | Trait对象与动态分发 | vtable结构、dyn Trait开销、Object Safety、静态vs动态分发选择 | ⭐⭐ | ⬜ |
| rust-13 | Rust编译器优化详解 | LLVM优化、MIR、单态化开销、#[inline]、LTO/ThinLTO | ⭐⭐ | ⬜ |
| rust-14 | no_std与嵌入式Rust | no_std环境、alloc crate、全局分配器、panic handler、嵌入式HAL | ⭐⭐ | ⬜ |

### 3.2 Rust HFT高性能专项（4篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| rust-15 | Rust Lock-Free编程 | std::sync::atomic、crossbeam、无锁队列、Arc开销、parking_lot | ⭐⭐⭐ | ⬜ |
| rust-16 | Rust SIMD编程 | std::simd (nightly)、packed_simd、portable_simd、向量化案例 | ⭐⭐⭐ | ⬜ |
| rust-17 | Rust高性能网络编程 | io_uring、tokio vs async-std vs smol、零拷贝、mio、网络优化模式 | ⭐⭐⭐ | ⬜ |
| rust-18 | Rust性能调优实战 | flamegraph、perf、criterion、内存分析、编译时间优化 | ⭐⭐ | ⬜ |

### 3.3 Rust HFT面试题（2篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| rust-19 | Rust面试题-所有权与生命周期 | 借用规则、生命周期省略、NLL、self-referential struct、Pin | ⭐⭐⭐ | ⬜ |
| rust-20 | Rust面试题-并发与性能 | Send/Sync、数据竞争预防、async深入、性能陷阱、Rust vs C++ | ⭐⭐⭐ | ⬜ |

### 3.4 Rust高级特性补充（1篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| rust-21 | Rust宏系统详解 | 声明宏(macro_rules!)、过程宏、derive宏、属性宏、编译期代码生成、常见宏模式 | ⭐⭐ | ⬜ |

---

## 四、Python HFT/Quant面试专项（新增9篇）

### 4.1 Python性能优化（4篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| py-48 | Python性能优化-Cython详解 | Cython语法、类型声明、与C交互、GIL释放、编译优化 | ⭐⭐⭐ | ⬜ |
| py-49 | Python性能优化-Numba详解 | JIT编译、nopython模式、CUDA支持、向量化、性能对比 | ⭐⭐⭐ | ⬜ |
| py-50 | Python性能优化-多进程与GIL | multiprocessing、共享内存、进程池、GIL绕过策略、异步IO | ⭐⭐ | ⬜ |
| py-51 | Python内存优化详解 | __slots__、memoryview、array模块、内存分析工具、对象大小 | ⭐⭐ | ⬜ |

### 4.2 Python量化专项（4篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| py-52 | NumPy高性能编程 | 向量化、广播、内存布局、ufunc、NumPy C API、numexpr | ⭐⭐⭐ | ⬜ |
| py-53 | Pandas性能优化 | 内存优化、向量化操作、apply陷阱、大数据处理、dtype优化 | ⭐⭐⭐ | ⬜ |
| py-54 | 时序数据处理专题 | 重采样、滑动窗口、时区处理、高频数据、tick数据处理 | ⭐⭐ | ⬜ |
| py-55 | Python量化面试题 | 策略实现、数据处理、性能优化、统计计算、Pandas/NumPy陷阱 | ⭐⭐⭐ | ⬜ |

### 4.3 Python高级编程（1篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| py-56 | Python异步编程详解 | asyncio深入、事件循环原理、协程vs回调、aiohttp、uvloop、异步陷阱、并发模式 | ⭐⭐ | ⬜ |

---

## 五、HFT专项深化（新增16篇）

### 5.1 HFT架构与原理（4篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| hft-12 | HFT系统延迟分析方法 | 延迟分解、测量点设计、百分位延迟、Tick-to-Trade、硬件时间戳 | ⭐⭐⭐ | ⬜ |
| hft-13 | Order Book实现详解 | 数据结构选择、价格级别管理、快速查找、增量更新、内存优化 | ⭐⭐⭐ | ⬜ |
| hft-14 | Market Making策略原理 | 做市商模型、库存管理、价差设置、风险控制、对冲策略 | ⭐⭐ | ⬜ |
| hft-15 | HFT风控系统设计 | 实时风控、限额管理、熔断机制、异常检测、合规要求 | ⭐⭐ | ⬜ |

### 5.2 HFT面试题（4篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| hft-16 | HFT面试题-系统设计 | 交易系统架构、延迟优化、容错设计、市场数据处理 | ⭐⭐⭐ | ⬜ |
| hft-17 | HFT面试题-算法与数据结构 | 时间序列、Order Book题、滑动窗口、概率统计 | ⭐⭐⭐ | ⬜ |
| hft-18 | HFT面试题-网络与协议 | FIX协议题、TCP优化、多播、延迟测量 | ⭐⭐⭐ | ⬜ |
| hft-19 | HFT面试题-智力与概率题 | 赌博问题、期望计算、概率推导、脑筋急转弯 | ⭐⭐ | ⬜ |

### 5.3 Kernel Bypass深入（2篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| hft-20 | DPDK深度实践 | 内存池、Ring缓冲区、PMD、多队列、性能调优 | ⭐⭐⭐ | ⬜ |
| hft-21 | Solarflare/Onload与FPGA网卡 | ef_vi、TCPDirect、硬件时间戳、FPGA加速、选型对比 | ⭐⭐ | ⬜ |

### 5.4 交易所与市场机制（2篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| hft-22 | 交易所撮合引擎原理 | 撮合算法(Price-Time/Pro-Rata)、订单类型(Limit/Market/IOC/FOK/GTC)、Queue Position、Exchange Fees、Maker/Taker | ⭐⭐⭐ | ⬜ |
| hft-23 | 全球主要交易所技术对比 | CME/ICE/NASDAQ/NYSE/LSE/SGX/HKEX/上交所/深交所技术栈、协议特点、延迟数据、Co-location | ⭐⭐ | ⬜ |

### 5.5 行为面试（1篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| hft-24 | HFT行为面试指南 | 为什么选择HFT、压力处理、团队协作、失败案例、道德困境、对监管的看法、职业规划 | ⭐⭐ | ⬜ |

### 5.6 高效序列化与数据处理（1篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| hft-25 | 高性能序列化技术 | SBE(Simple Binary Encoding)、FlatBuffers、Cap'n Proto、零拷贝解析、Schema演进、性能对比、协议设计原则 | ⭐⭐⭐ | ⬜ |

### 5.7 面试技巧与容错设计（2篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| hft-26 | HFT技术面试技巧 | 白板编程技巧、系统设计回答框架、如何展示低延迟经验、常见追问应对、代码风格要求、时间管理 | ⭐⭐ | ⬜ |
| hft-27 | 交易系统容错与恢复 | 热备/温备/冷备、主从切换、状态同步、Checkpoint/Recovery、订单恢复、Gap Fill、Sequence Number | ⭐⭐⭐ | ⬜ |

---

## 六、SRE HFT专项（新增5篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| sre-61 | 低延迟系统运维指南 | 延迟监控、抖动分析、内核参数、硬件配置、告警设计 | ⭐⭐⭐ | ⬜ |
| sre-62 | HFT基础设施最佳实践 | 机房选址、网络架构、交换机配置、时间同步(PTP)、电源冗余 | ⭐⭐⭐ | ⬜ |
| sre-63 | 金融系统合规与审计 | 日志要求、数据保留、灾备要求、MiFID II、SEC规则 | ⭐⭐ | ⬜ |
| sre-64 | 交易系统故障演练 | 混沌工程、故障注入、市场异常模拟、切换演练 | ⭐⭐ | ⬜ |
| sre-65 | SRE面试题-HFT专项 | 延迟排查、网络问题、系统调优、容量规划 | ⭐⭐⭐ | ⬜ |

---

## 七、金融数学与统计（新增5篇）⚠️ 重要补充

> HFT量化面试必考内容，Jane Street/Citadel/Two Sigma/Jump等公司高频考察

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| math-09 | 金融数学基础 | 随机过程、布朗运动、伊藤引理、几何布朗运动、鞅论基础、随机微分方程 | ⭐⭐⭐ | ⬜ |
| math-10 | 期权定价与Greeks详解 | Black-Scholes推导、Delta/Gamma/Vega/Theta/Rho、隐含波动率、波动率曲面、二叉树定价 | ⭐⭐⭐ | ⬜ |
| math-11 | 时间序列分析详解 | AR/MA/ARIMA/SARIMA、GARCH/EGARCH、协整检验、均值回归、Kalman滤波、状态空间模型 | ⭐⭐⭐ | ⬜ |
| math-12 | 统计套利与因子模型 | 配对交易数学、PCA/ICA、协方差估计、风险模型(Barra)、因子分析、组合优化 | ⭐⭐ | ⬜ |
| math-13 | 数值计算与浮点精度 | IEEE 754标准、浮点比较陷阱、数值稳定性算法、Kahan求和、定点数vs浮点数、decimal库、金融精度要求 | ⭐⭐⭐ | ⬜ |

---

## 八、底层系统与网络深化（新增7篇）

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| linux-09 | Linux内核网络栈详解 | sk_buff、netfilter、conntrack、TCP状态机、软中断、NAPI | ⭐⭐ | ⬜ |
| linux-10 | Linux时间子系统 | 时钟源、TSC、HPET、PTP、时间精度、clocksource、nohz | ⭐⭐ | ⬜ |
| linux-11 | 内存映射与高效IO | mmap原理与陷阱、huge pages(2MB/1GB)、THP、直接IO(O_DIRECT)、AIO、零拷贝技术栈 | ⭐⭐ | ⬜ |
| net-18 | TCP调优深入详解 | 内核参数全解、拥塞控制算法(BBR/CUBIC)、快速路径、零拷贝(sendfile/splice) | ⭐⭐⭐ | ⬜ |
| net-19 | UDP组播最佳实践 | IGMP、组播路由、PIM、组播可靠性、Market Data分发、组播丢包处理 | ⭐⭐ | ⬜ |
| net-20 | io_uring详解 | io_uring原理、liburing、性能对比、SQE/CQE、应用场景、与epoll对比 | ⭐⭐ | ⬜ |
| net-21 | RDMA与InfiniBand详解 | RDMA原语(send/recv/read/write)、Verbs API、QP、MR、延迟对比、RoCE | ⭐⭐ | ⬜ |

---

## 九、算法专项补充（新增2篇）

> 实时数据处理与高效统计的核心算法

| 编号 | 文章标题 | 核心内容 | 优先级 | 状态 |
|------|----------|----------|--------|------|
| algo-09 | 概率数据结构详解 | Bloom Filter、Count-Min Sketch、HyperLogLog、Cuckoo Filter、Skip List、空间换时间的应用场景 | ⭐⭐ | ⬜ |
| algo-10 | 在线算法与流式计算 | 滑动窗口统计、在线均值/方差(Welford算法)、Reservoir Sampling、流式Top-K、指数移动平均(EMA)、VWAP计算 | ⭐⭐⭐ | ⬜ |

---

## 十、实施优先级排序

### Top 30 必做文章（按优先级）

| 排名 | 编号 | 文章标题 | 目标职位 | 理由 |
|------|------|----------|----------|------|
| 1 | cpp-14 | 深浅拷贝与移动语义详解 | C++ | **必考题**，面试必问 |
| 2 | cpp-15 | 内存模型与缓存优化 | C++ | HFT核心，性能关键 |
| 3 | cpp-22 | Lock-Free数据结构详解 | C++ | HFT必备技能 |
| 4 | cpp-41 | CPU微架构与性能优化 | C++ | **深度优化必备**，解释"为什么快" |
| 5 | cpp-23 | SIMD编程详解 | C++ | 性能提升利器 |
| 6 | cpp-24 | 分支预测与热路径优化 | C++ | 延迟优化核心 |
| 7 | math-09 | 金融数学基础 | 全部 | **量化必考**，随机过程/伊藤引理 |
| 8 | math-10 | 期权定价与Greeks详解 | 全部 | **量化必考**，衍生品定价 |
| 9 | math-13 | 数值计算与浮点精度 | 全部 | **金融精度必备**，浮点陷阱 |
| 10 | hft-25 | 高性能序列化技术 | 全部 | **热路径关键**，SBE/FlatBuffers |
| 11 | algo-10 | 在线算法与流式计算 | 全部 | **实时计算必备**，VWAP/EMA |
| 12 | rust-09 | unsafe Rust完全指南 | Rust | Rust高级面试必考 |
| 13 | rust-15 | Rust Lock-Free编程 | Rust | HFT Rust核心 |
| 14 | rust-10 | Rust与C/C++互操作 | Rust | 实际工程必备 |
| 15 | py-48 | Python性能优化-Cython详解 | Python | 量化Python必备 |
| 16 | py-52 | NumPy高性能编程 | Python | 量化基础 |
| 17 | hft-13 | Order Book实现详解 | 全部 | HFT核心数据结构 |
| 18 | hft-22 | 交易所撮合引擎原理 | 全部 | 理解市场机制 |
| 19 | hft-27 | 交易系统容错与恢复 | 全部 | **生产必备**，故障恢复 |
| 20 | hft-16 | HFT面试题-系统设计 | 全部 | 面试必备 |
| 21 | cpp-29 | C++面试题-语言基础篇 | C++ | 面试直接考察 |
| 22 | cpp-30 | C++面试题-内存与对象模型 | C++ | 面试直接考察 |
| 23 | cpp-31 | C++面试题-并发与多线程 | C++ | 面试直接考察 |
| 24 | cpp-34 | 模板高级技巧详解 | C++ | 变参模板高频考察 |
| 25 | cpp-38 | C++测试与调试实战 | C++ | Sanitizer必须掌握 |
| 26 | sre-61 | 低延迟系统运维指南 | SRE | HFT SRE核心 |
| 27 | cpp-20 | 自定义内存分配器设计 | C++ | 高级面试题 |
| 28 | rust-16 | Rust SIMD编程 | Rust | 性能优化 |
| 29 | hft-12 | HFT系统延迟分析方法 | 全部 | 面试常问 |
| 30 | net-18 | TCP调优深入详解 | SRE/C++ | 网络优化 |

---

## 十一、统计汇总

| 分类 | 新增篇数 | 状态 |
|------|----------|------|
| C++ HFT专项 | 30篇 | ⬜ 待实施 |
| Rust HFT专项 | 13篇 | ⬜ 待实施 |
| Python HFT/Quant专项 | 9篇 | ⬜ 待实施 |
| HFT专项深化 | 16篇 | ⬜ 待实施 |
| SRE HFT专项 | 5篇 | ⬜ 待实施 |
| 金融数学与统计 | 5篇 | ⬜ 待实施 |
| 底层系统与网络 | 7篇 | ⬜ 待实施 |
| 算法专项补充 | 2篇 | ⬜ 待实施 |
| **总计** | **87篇** | |

---

## 十二、内容风格要求

- 由浅入深的顺序组织
- 文字描述要深刻、详细、准确
- 核心概念必须配代码示例
- 面试题类文章采用Q&A格式
- 包含实战案例和性能数据
- 提供常见陷阱和最佳实践
- 金融数学部分需包含公式推导
- 硬件相关文章需包含性能数据和测量方法

---

## 十三、进度记录

| 日期 | 完成内容 | 篇数 |
|------|----------|------|
| 2026-01-21 | 创建实施计划 | 60篇 |
| 2026-01-21 | 第一轮补充：金融数学、C++高级、测试调试、交易所机制等 | +16篇 |
| 2026-01-21 | 第二轮补充：CPU微架构、序列化、数值计算、在线算法、容错设计等 | +11篇 |
| 2026-01-21 | ✅ 完成2.1-2.3：C++语言核心深度(8篇)、HFT高性能专项(7篇)、HFT面试题(5篇) | 20篇 |
| 2026-01-21 | ✅ 完成2.4-2.6：C++高级特性(4篇)、测试与工具链(3篇)、硬件与微架构(3篇) | 10篇 |
| 2026-01-21 | ✅ 完成3.1-3.4：Rust语言深度(6篇)、HFT高性能专项(4篇)、HFT面试题(2篇)、高级特性(1篇) | 13篇 |
| 2026-01-21 | ✅ 完成4.1-4.3：Python性能优化(4篇)、量化专项(4篇)、高级编程(1篇) | 9篇 |
| 2026-01-21 | ✅ 完成5.1-5.7：HFT架构与原理(4篇)、HFT面试题(4篇)、Kernel Bypass(2篇)、交易所机制(2篇)、行为面试(1篇)、序列化(1篇)、面试技巧与容错(2篇) | 16篇 |
| 2026-01-21 | ✅ 完成6.1-6.3：SRE HFT专项(5篇) - 低延迟运维、基础设施、合规审计、故障演练、面试题 | 5篇 |
| 2026-01-21 | ✅ 完成7.1-7.5：金融数学与统计(5篇) - 金融数学基础、期权定价Greeks、时间序列、统计套利因子、数值计算精度 | 5篇 |
| 2026-01-21 | ✅ 完成8.1-8.7：底层系统与网络(7篇) - Linux网络栈、时间子系统、内存映射IO、TCP调优、UDP组播、io_uring、RDMA | 7篇 |
| 2026-01-21 | ✅ 完成9.1-9.2：算法专项(2篇) - 概率数据结构、在线算法流式计算 | 2篇 |
| | | |

---

## 十四、状态说明

- ⬜ 待实施
- 🔄 进行中
- ✅ 已完成
- ⏸️ 暂停
