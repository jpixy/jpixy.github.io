+++
title = "RDMA与InfiniBand详解"
description = "深入讲解RDMA技术：RDMA原语(send/recv/read/write)、Verbs API、QP与MR、延迟对比及RoCE配置"
date = 2026-01-21
draft = false
[taxonomies]
tags = ["RDMA", "InfiniBand", "低延迟", "HFT", "高性能网络"]
+++

# RDMA与InfiniBand详解

## 概述

RDMA（Remote Direct Memory Access）允许网络适配器直接访问远程主机内存，绕过CPU和操作系统，实现超低延迟和高吞吐量。在HFT领域，RDMA是连接交易服务器的重要技术。

## 一、RDMA基础

### 1.1 RDMA技术对比

| 技术 | 硬件要求 | 延迟 | 吞吐量 | 适用场景 |
|------|----------|------|--------|----------|
| TCP/IP | 普通网卡 | ~50µs | 10-100Gbps | 通用 |
| InfiniBand | IB网卡+交换机 | ~1µs | 100-400Gbps | HPC、数据中心 |
| RoCE v2 | RDMA网卡 | ~2µs | 25-100Gbps | 数据中心 |
| iWARP | iWARP网卡 | ~5µs | 10-100Gbps | 兼容TCP |

### 1.2 RDMA操作类型

```
RDMA操作分类:
├── 双边操作 (需要接收方参与)
│   ├── Send/Recv
│   └── Send with Immediate
└── 单边操作 (不需要接收方CPU)
    ├── RDMA Read
    ├── RDMA Write
    └── RDMA Write with Immediate

原子操作:
├── Fetch and Add
└── Compare and Swap
```

### 1.3 核心概念

```
RDMA关键组件:
├── QP (Queue Pair) - 通信端点
│   ├── SQ (Send Queue) - 发送队列
│   └── RQ (Receive Queue) - 接收队列
├── CQ (Completion Queue) - 完成队列
├── MR (Memory Region) - 注册的内存区域
├── PD (Protection Domain) - 保护域
└── AH (Address Handle) - 地址句柄
```

## 二、Verbs API

### 2.1 初始化

```c
#include <infiniband/verbs.h>

/* RDMA上下文 */
typedef struct {
    struct ibv_context *ctx;
    struct ibv_pd *pd;
    struct ibv_cq *cq;
    struct ibv_qp *qp;
    struct ibv_mr *mr;
    char *buffer;
    size_t buffer_size;
} RdmaContext;

int init_rdma(RdmaContext *rctx, const char *device_name) {
    struct ibv_device **dev_list;
    struct ibv_device *dev = NULL;
    int num_devices;
    
    /* 获取设备列表 */
    dev_list = ibv_get_device_list(&num_devices);
    if (!dev_list) {
        fprintf(stderr, "Failed to get IB devices\n");
        return -1;
    }
    
    /* 查找指定设备 */
    for (int i = 0; i < num_devices; i++) {
        if (!strcmp(ibv_get_device_name(dev_list[i]), device_name)) {
            dev = dev_list[i];
            break;
        }
    }
    
    if (!dev) {
        fprintf(stderr, "Device %s not found\n", device_name);
        ibv_free_device_list(dev_list);
        return -1;
    }
    
    /* 打开设备 */
    rctx->ctx = ibv_open_device(dev);
    ibv_free_device_list(dev_list);
    
    if (!rctx->ctx) {
        fprintf(stderr, "Failed to open device\n");
        return -1;
    }
    
    /* 创建Protection Domain */
    rctx->pd = ibv_alloc_pd(rctx->ctx);
    if (!rctx->pd) {
        fprintf(stderr, "Failed to allocate PD\n");
        return -1;
    }
    
    return 0;
}
```

### 2.2 创建完成队列和队列对

```c
int create_qp(RdmaContext *rctx, int cq_size, int qp_depth) {
    /* 创建完成队列 */
    rctx->cq = ibv_create_cq(rctx->ctx, cq_size, NULL, NULL, 0);
    if (!rctx->cq) {
        fprintf(stderr, "Failed to create CQ\n");
        return -1;
    }
    
    /* QP初始化属性 */
    struct ibv_qp_init_attr qp_init_attr = {
        .send_cq = rctx->cq,
        .recv_cq = rctx->cq,
        .cap = {
            .max_send_wr = qp_depth,
            .max_recv_wr = qp_depth,
            .max_send_sge = 1,
            .max_recv_sge = 1,
        },
        .qp_type = IBV_QPT_RC,  /* 可靠连接 */
    };
    
    /* 创建QP */
    rctx->qp = ibv_create_qp(rctx->pd, &qp_init_attr);
    if (!rctx->qp) {
        fprintf(stderr, "Failed to create QP\n");
        return -1;
    }
    
    return 0;
}

/* QP状态转换: RESET -> INIT -> RTR -> RTS */
int modify_qp_to_init(struct ibv_qp *qp, int port) {
    struct ibv_qp_attr attr = {
        .qp_state = IBV_QPS_INIT,
        .pkey_index = 0,
        .port_num = port,
        .qp_access_flags = IBV_ACCESS_LOCAL_WRITE |
                           IBV_ACCESS_REMOTE_READ |
                           IBV_ACCESS_REMOTE_WRITE,
    };
    
    return ibv_modify_qp(qp, &attr,
                         IBV_QP_STATE |
                         IBV_QP_PKEY_INDEX |
                         IBV_QP_PORT |
                         IBV_QP_ACCESS_FLAGS);
}

int modify_qp_to_rtr(struct ibv_qp *qp, uint32_t remote_qpn,
                     uint16_t remote_lid, uint8_t *remote_gid) {
    struct ibv_qp_attr attr = {
        .qp_state = IBV_QPS_RTR,
        .path_mtu = IBV_MTU_4096,
        .dest_qp_num = remote_qpn,
        .rq_psn = 0,
        .max_dest_rd_atomic = 1,
        .min_rnr_timer = 12,
        .ah_attr = {
            .is_global = 1,
            .dlid = remote_lid,
            .sl = 0,
            .src_path_bits = 0,
            .port_num = 1,
            .grh = {
                .dgid = *(union ibv_gid *)remote_gid,
                .hop_limit = 1,
            },
        },
    };
    
    return ibv_modify_qp(qp, &attr,
                         IBV_QP_STATE |
                         IBV_QP_AV |
                         IBV_QP_PATH_MTU |
                         IBV_QP_DEST_QPN |
                         IBV_QP_RQ_PSN |
                         IBV_QP_MAX_DEST_RD_ATOMIC |
                         IBV_QP_MIN_RNR_TIMER);
}

int modify_qp_to_rts(struct ibv_qp *qp) {
    struct ibv_qp_attr attr = {
        .qp_state = IBV_QPS_RTS,
        .timeout = 14,
        .retry_cnt = 7,
        .rnr_retry = 7,
        .sq_psn = 0,
        .max_rd_atomic = 1,
    };
    
    return ibv_modify_qp(qp, &attr,
                         IBV_QP_STATE |
                         IBV_QP_TIMEOUT |
                         IBV_QP_RETRY_CNT |
                         IBV_QP_RNR_RETRY |
                         IBV_QP_SQ_PSN |
                         IBV_QP_MAX_QP_RD_ATOMIC);
}
```

### 2.3 内存注册

```c
int register_memory(RdmaContext *rctx, size_t size) {
    /* 分配对齐内存 */
    rctx->buffer_size = size;
    rctx->buffer = aligned_alloc(4096, size);
    if (!rctx->buffer) {
        return -1;
    }
    
    /* 注册内存区域 */
    rctx->mr = ibv_reg_mr(rctx->pd, rctx->buffer, size,
                          IBV_ACCESS_LOCAL_WRITE |
                          IBV_ACCESS_REMOTE_READ |
                          IBV_ACCESS_REMOTE_WRITE);
    
    if (!rctx->mr) {
        fprintf(stderr, "Failed to register MR\n");
        free(rctx->buffer);
        return -1;
    }
    
    printf("MR registered: addr=%p, lkey=0x%x, rkey=0x%x\n",
           rctx->buffer, rctx->mr->lkey, rctx->mr->rkey);
    
    return 0;
}
```

## 三、RDMA操作

### 3.1 Send/Recv

```c
/* 发布接收请求 */
int post_recv(RdmaContext *rctx, uint64_t wr_id) {
    struct ibv_sge sge = {
        .addr = (uintptr_t)rctx->buffer,
        .length = rctx->buffer_size,
        .lkey = rctx->mr->lkey,
    };
    
    struct ibv_recv_wr wr = {
        .wr_id = wr_id,
        .sg_list = &sge,
        .num_sge = 1,
    };
    
    struct ibv_recv_wr *bad_wr;
    return ibv_post_recv(rctx->qp, &wr, &bad_wr);
}

/* 发送数据 */
int post_send(RdmaContext *rctx, size_t length, uint64_t wr_id) {
    struct ibv_sge sge = {
        .addr = (uintptr_t)rctx->buffer,
        .length = length,
        .lkey = rctx->mr->lkey,
    };
    
    struct ibv_send_wr wr = {
        .wr_id = wr_id,
        .sg_list = &sge,
        .num_sge = 1,
        .opcode = IBV_WR_SEND,
        .send_flags = IBV_SEND_SIGNALED,
    };
    
    struct ibv_send_wr *bad_wr;
    return ibv_post_send(rctx->qp, &wr, &bad_wr);
}
```

### 3.2 RDMA Read/Write

```c
/* RDMA写入远程内存 */
int rdma_write(RdmaContext *rctx, uint64_t remote_addr, 
               uint32_t remote_rkey, size_t length, uint64_t wr_id) {
    struct ibv_sge sge = {
        .addr = (uintptr_t)rctx->buffer,
        .length = length,
        .lkey = rctx->mr->lkey,
    };
    
    struct ibv_send_wr wr = {
        .wr_id = wr_id,
        .sg_list = &sge,
        .num_sge = 1,
        .opcode = IBV_WR_RDMA_WRITE,
        .send_flags = IBV_SEND_SIGNALED,
        .wr.rdma = {
            .remote_addr = remote_addr,
            .rkey = remote_rkey,
        },
    };
    
    struct ibv_send_wr *bad_wr;
    return ibv_post_send(rctx->qp, &wr, &bad_wr);
}

/* RDMA读取远程内存 */
int rdma_read(RdmaContext *rctx, uint64_t remote_addr,
              uint32_t remote_rkey, size_t length, uint64_t wr_id) {
    struct ibv_sge sge = {
        .addr = (uintptr_t)rctx->buffer,
        .length = length,
        .lkey = rctx->mr->lkey,
    };
    
    struct ibv_send_wr wr = {
        .wr_id = wr_id,
        .sg_list = &sge,
        .num_sge = 1,
        .opcode = IBV_WR_RDMA_READ,
        .send_flags = IBV_SEND_SIGNALED,
        .wr.rdma = {
            .remote_addr = remote_addr,
            .rkey = remote_rkey,
        },
    };
    
    struct ibv_send_wr *bad_wr;
    return ibv_post_send(rctx->qp, &wr, &bad_wr);
}
```

### 3.3 轮询完成

```c
/* 阻塞等待完成 */
int wait_completion(RdmaContext *rctx, struct ibv_wc *wc) {
    int ret;
    do {
        ret = ibv_poll_cq(rctx->cq, 1, wc);
    } while (ret == 0);
    
    if (ret < 0) {
        fprintf(stderr, "Poll CQ failed\n");
        return -1;
    }
    
    if (wc->status != IBV_WC_SUCCESS) {
        fprintf(stderr, "WC error: %s\n", ibv_wc_status_str(wc->status));
        return -1;
    }
    
    return 0;
}

/* 非阻塞轮询 */
int poll_completion(RdmaContext *rctx, struct ibv_wc *wc, int max_wc) {
    return ibv_poll_cq(rctx->cq, max_wc, wc);
}
```

## 四、RoCE配置

### 4.1 RoCE v2配置

```bash
# 查看RDMA设备
ibv_devices
ibv_devinfo

# RoCE网卡配置
# 1. 启用DCB/PFC (Priority Flow Control)
mlnx_qos -i eth0 --pfc 0,1,1,0,0,0,0,0

# 2. 设置DSCP映射
cma_roce_mode -d mlx5_0 -p 1 -m 2

# 3. 配置GID表
cat /sys/class/infiniband/mlx5_0/ports/1/gids/0

# 4. 配置MTU
ip link set eth0 mtu 4200
```

### 4.2 网络配置

```bash
# 配置网络
ip addr add 192.168.1.100/24 dev eth0
ip link set eth0 up

# 验证RDMA连接
rping -s -v  # 服务端
rping -c -a 192.168.1.100 -v  # 客户端

# 性能测试
ib_write_bw -d mlx5_0  # 服务端
ib_write_bw -d mlx5_0 192.168.1.100  # 客户端

ib_write_lat -d mlx5_0  # 延迟测试
```

## 五、性能优化

### 5.1 关键优化点

```c
/* 1. 内联发送 (Inline Send) - 小消息优化 */
struct ibv_send_wr wr = {
    .send_flags = IBV_SEND_SIGNALED | IBV_SEND_INLINE,
};

/* 2. 选择性信号 - 减少完成事件 */
/* 每N个请求才请求一次完成通知 */
if (request_count % 64 == 0) {
    wr.send_flags |= IBV_SEND_SIGNALED;
}

/* 3. 批量提交 */
struct ibv_send_wr wr[8];
/* 设置链表 */
for (int i = 0; i < 7; i++) {
    wr[i].next = &wr[i+1];
}
wr[7].next = NULL;
ibv_post_send(qp, &wr[0], &bad_wr);

/* 4. 使用SRQ (Shared Receive Queue) */
struct ibv_srq_init_attr srq_attr = {
    .attr = {
        .max_wr = 1024,
        .max_sge = 1,
    },
};
struct ibv_srq *srq = ibv_create_srq(pd, &srq_attr);
```

### 5.2 延迟优化

```c
/* 最低延迟配置 */
void optimize_for_latency(RdmaContext *rctx) {
    /* 1. 使用小缓冲区 */
    register_memory(rctx, 4096);
    
    /* 2. 启用内联 */
    /* 在创建QP时设置max_inline_data */
    
    /* 3. 使用轮询而非中断 */
    while (1) {
        struct ibv_wc wc;
        if (ibv_poll_cq(rctx->cq, 1, &wc) > 0) {
            process_completion(&wc);
        }
    }
    
    /* 4. CPU亲和性 */
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);
}
```

## 六、HFT应用示例

### 6.1 RDMA消息传递

```c
/* 低延迟消息发送 */
typedef struct {
    uint64_t timestamp;
    uint32_t msg_type;
    uint32_t payload_len;
    char payload[0];
} __attribute__((packed)) RdmaMessage;

int send_trading_message(RdmaContext *rctx, uint32_t msg_type,
                         const void *payload, size_t len) {
    RdmaMessage *msg = (RdmaMessage *)rctx->buffer;
    
    /* 填充消息 */
    msg->timestamp = rdtsc();
    msg->msg_type = msg_type;
    msg->payload_len = len;
    memcpy(msg->payload, payload, len);
    
    /* 发送 */
    return post_send(rctx, sizeof(RdmaMessage) + len, msg->timestamp);
}

/* 接收处理循环 */
void receive_loop(RdmaContext *rctx,
                  void (*handler)(const RdmaMessage *)) {
    struct ibv_wc wc;
    
    /* 预发布接收请求 */
    for (int i = 0; i < 64; i++) {
        post_recv(rctx, i);
    }
    
    while (1) {
        int n = ibv_poll_cq(rctx->cq, 1, &wc);
        if (n > 0 && wc.status == IBV_WC_SUCCESS) {
            if (wc.opcode == IBV_WC_RECV) {
                RdmaMessage *msg = (RdmaMessage *)rctx->buffer;
                handler(msg);
                
                /* 重新发布接收 */
                post_recv(rctx, wc.wr_id);
            }
        }
    }
}
```

### 6.2 RDMA共享状态

```c
/* 使用RDMA写直接更新远程状态 */
typedef struct {
    volatile uint64_t sequence;
    volatile double bid_price;
    volatile double ask_price;
    volatile int64_t bid_size;
    volatile int64_t ask_size;
} __attribute__((packed)) MarketQuote;

/* 发布行情更新 */
int publish_quote(RdmaContext *rctx, uint64_t remote_addr,
                  uint32_t remote_rkey, const MarketQuote *quote) {
    memcpy(rctx->buffer, quote, sizeof(MarketQuote));
    return rdma_write(rctx, remote_addr, remote_rkey, 
                      sizeof(MarketQuote), quote->sequence);
}

/* 读取远程行情 */
int read_quote(RdmaContext *rctx, uint64_t remote_addr,
               uint32_t remote_rkey, MarketQuote *quote) {
    int ret = rdma_read(rctx, remote_addr, remote_rkey,
                        sizeof(MarketQuote), 0);
    if (ret == 0) {
        struct ibv_wc wc;
        wait_completion(rctx, &wc);
        memcpy(quote, rctx->buffer, sizeof(MarketQuote));
    }
    return ret;
}
```

## 七、调试与监控

### 7.1 性能工具

```bash
# 带宽测试
ib_write_bw -d mlx5_0 -s 65536 -n 10000

# 延迟测试
ib_write_lat -d mlx5_0 -s 64 -n 10000

# 输出示例：
#  #bytes   #iterations   t_min[usec]   t_max[usec]   t_avg[usec]
#  64       10000         0.89          2.34          1.02

# 原子操作测试
ib_atomic_lat -d mlx5_0

# 读取测试
ib_read_bw -d mlx5_0
ib_read_lat -d mlx5_0
```

### 7.2 监控命令

```bash
# 设备状态
ibstat
ibstatus

# 端口计数器
perfquery -x

# 错误统计
ibdiagnet

# QP状态
ibv_devinfo -v
```

## 总结

RDMA的核心优势：

1. **超低延迟**：绕过操作系统，亚微秒级延迟
2. **零拷贝**：数据直接DMA到目标内存
3. **CPU卸载**：网卡完成传输，释放CPU
4. **高吞吐**：100Gbps+带宽

RDMA是HFT基础设施的重要组成部分，适用于交易服务器间的低延迟通信。
