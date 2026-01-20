+++
title = "17.模型部署与Serving详解"
date = 2025-01-15
description = "AI 模型生产部署全流程：模型格式、容器化、服务框架、监控运维"
[taxonomies]
tags = ["ai", "deployment", "serving", "mlops", "docker", "kubernetes"]
+++

## 概述

训练好的模型如何真正服务用户？本文介绍从模型导出到生产部署的完整流程和最佳实践。

---

## 一、模型格式

### 1.1 常见模型格式

```
模型保存格式：

┌─────────────────┬────────────────────────────────────┐
│      格式       │              特点                   │
├─────────────────┼────────────────────────────────────┤
│ PyTorch (.pt)  │ PyTorch 原生，灵活                  │
│                │ 包含代码依赖                        │
├─────────────────┼────────────────────────────────────┤
│ ONNX (.onnx)   │ 开放标准，跨框架                    │
│                │ 推理优化友好                        │
├─────────────────┼────────────────────────────────────┤
│ TensorRT       │ NVIDIA GPU 极致优化                 │
│ (.engine)      │ 硬件绑定                            │
├─────────────────┼────────────────────────────────────┤
│ SavedModel     │ TensorFlow 标准格式                 │
│                │ TF Serving 直接使用                 │
├─────────────────┼────────────────────────────────────┤
│ GGUF           │ llama.cpp 专用                      │
│                │ 量化友好，CPU 部署                  │
├─────────────────┼────────────────────────────────────┤
│ SafeTensors    │ HuggingFace 安全格式                │
│                │ 加载快，安全                        │
└─────────────────┴────────────────────────────────────┘
```

### 1.2 模型导出

```python
import torch

# PyTorch 保存
torch.save(model.state_dict(), "model.pt")

# ONNX 导出
dummy_input = torch.randn(1, 3, 224, 224)
torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    opset_version=17,
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'}
    }
)

# HuggingFace 保存
model.save_pretrained("./model_dir")
tokenizer.save_pretrained("./model_dir")
```

---

## 二、服务框架

### 2.1 框架选择

```
推理服务框架：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   通用框架                                              │
│   ────────                                              │
│   • Triton Inference Server：多框架支持，高性能         │
│   • TorchServe：PyTorch 官方，易用                      │
│   • TensorFlow Serving：TF 专用                         │
│   • ONNX Runtime Server：ONNX 模型服务                  │
│                                                          │
│   LLM 专用                                              │
│   ────────                                              │
│   • vLLM：高吞吐量 LLM 服务                             │
│   • TGI：HuggingFace 官方                               │
│   • Ollama：本地 LLM 简易部署                           │
│                                                          │
│   轻量级                                                │
│   ────────                                              │
│   • FastAPI：自定义服务                                 │
│   • Ray Serve：分布式服务                               │
│   • BentoML：模型打包部署                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 FastAPI 部署

```python
from fastapi import FastAPI
from pydantic import BaseModel
import torch

app = FastAPI()

# 加载模型（启动时加载一次）
model = load_model()
model.eval()

class PredictRequest(BaseModel):
    text: str
    max_length: int = 100

class PredictResponse(BaseModel):
    result: str
    latency_ms: float

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    import time
    start = time.time()
    
    with torch.no_grad():
        result = model.generate(request.text, max_length=request.max_length)
    
    latency = (time.time() - start) * 1000
    
    return PredictResponse(result=result, latency_ms=latency)

@app.get("/health")
async def health():
    return {"status": "healthy"}

# 启动: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

### 2.3 Triton 部署

```
Triton 模型仓库结构：

model_repository/
├── my_model/
│   ├── config.pbtxt         # 模型配置
│   ├── 1/                   # 版本 1
│   │   └── model.onnx       # 模型文件
│   └── 2/                   # 版本 2
│       └── model.onnx

config.pbtxt 示例：
```
```
name: "my_model"
platform: "onnxruntime_onnx"
max_batch_size: 32
input [
  {
    name: "input"
    data_type: TYPE_FP32
    dims: [ 3, 224, 224 ]
  }
]
output [
  {
    name: "output"
    data_type: TYPE_FP32
    dims: [ 1000 ]
  }
]
instance_group [
  {
    count: 2
    kind: KIND_GPU
    gpus: [ 0 ]
  }
]
```

```bash
# 启动 Triton 服务
docker run --gpus all -p 8000:8000 -p 8001:8001 -p 8002:8002 \
  -v /path/to/model_repository:/models \
  nvcr.io/nvidia/tritonserver:23.12-py3 \
  tritonserver --model-repository=/models
```

---

## 三、容器化部署

### 3.1 Dockerfile

```dockerfile
# GPU 推理 Dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

# 安装 Python
RUN apt-get update && apt-get install -y python3 python3-pip

# 安装依赖
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# 复制代码和模型
COPY app/ /app/
COPY models/ /models/

WORKDIR /app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 Docker Compose

```yaml
version: '3.8'

services:
  inference:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./models:/models
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3.3 Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: model-server
  template:
    metadata:
      labels:
        app: model-server
    spec:
      containers:
      - name: inference
        image: myregistry/model-server:v1
        ports:
        - containerPort: 8000
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
          requests:
            nvidia.com/gpu: 1
            memory: "8Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: model-service
spec:
  selector:
    app: model-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 四、监控与运维

### 4.1 监控指标

```
关键监控指标：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   延迟指标                                              │
│   ────────                                              │
│   • P50/P95/P99 延迟                                    │
│   • 平均延迟                                            │
│   • 预处理/推理/后处理 分段延迟                         │
│                                                          │
│   吞吐量指标                                            │
│   ────────                                              │
│   • QPS（每秒请求数）                                   │
│   • 批处理大小                                          │
│   • 队列长度                                            │
│                                                          │
│   资源指标                                              │
│   ────────                                              │
│   • GPU 利用率                                          │
│   • GPU 显存使用                                        │
│   • CPU/内存使用                                        │
│                                                          │
│   业务指标                                              │
│   ────────                                              │
│   • 成功率                                              │
│   • 错误分类                                            │
│   • token 使用量（LLM）                                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Prometheus 集成

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# 定义指标
REQUEST_COUNT = Counter(
    'inference_requests_total',
    'Total inference requests',
    ['status']
)

REQUEST_LATENCY = Histogram(
    'inference_latency_seconds',
    'Inference latency',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

GPU_MEMORY = Gauge(
    'gpu_memory_usage_bytes',
    'GPU memory usage'
)

@app.middleware("http")
async def add_metrics(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    REQUEST_LATENCY.observe(duration)
    REQUEST_COUNT.labels(status=response.status_code).inc()
    
    return response

# 启动指标服务
start_http_server(9090)
```

---

## 五、最佳实践

```
模型部署最佳实践：

┌─────────────────────────────────────────────────────────┐
│                                                          │
│   模型准备                                              │
│   ────────                                              │
│   • 导出优化后的格式                                    │
│   • 版本化管理                                          │
│   • 性能基准测试                                        │
│                                                          │
│   服务设计                                              │
│   ────────                                              │
│   • 健康检查端点                                        │
│   • 优雅关闭                                            │
│   • 超时处理                                            │
│   • 请求验证                                            │
│                                                          │
│   部署策略                                              │
│   ────────                                              │
│   • 蓝绿部署                                            │
│   • 金丝雀发布                                          │
│   • 回滚机制                                            │
│                                                          │
│   运维保障                                              │
│   ────────                                              │
│   • 全面监控                                            │
│   • 告警配置                                            │
│   • 日志收集                                            │
│   • 自动扩缩容                                          │
│                                                          │
│   ──────────────────────────────────────────────────   │
│                                                          │
│   "部署不是结束，而是服务的开始。"                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```
