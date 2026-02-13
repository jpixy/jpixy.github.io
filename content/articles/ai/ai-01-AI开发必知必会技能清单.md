+++
title = "01. AI开发必知必会技能清单"
date = 2026-01-12
weight = 1000
description = "2024-2026年AI开发者需要掌握的核心知识与技能体系"
[taxonomies]
tags = ["ai", "machine-learning", "deep-learning", "llm"]
+++

# AI开发必知必会技能清单

本文系统梳理当前 AI 开发领域的核心知识体系，涵盖机器学习基础、深度学习、大语言模型、MLOps 等关键领域。

---

## 一、机器学习基础

### 1.1 核心概念

| 概念 | 说明 |
|-----|------|
| 监督学习 | 有标签数据，分类/回归任务 |
| 无监督学习 | 无标签，聚类/降维/异常检测 |
| 强化学习 | 智能体与环境交互，奖励驱动 |
| 半监督学习 | 少量标签 + 大量无标签数据 |
| 自监督学习 | 从数据本身构造监督信号 |

### 1.2 经典算法

```
分类：Logistic Regression, SVM, Decision Tree, Random Forest, XGBoost, LightGBM
回归：Linear Regression, Ridge, Lasso, ElasticNet
聚类：K-Means, DBSCAN, Hierarchical Clustering
降维：PCA, t-SNE, UMAP
```

### 1.3 模型评估

**分类指标**：
- Accuracy, Precision, Recall, F1-Score
- ROC-AUC, PR-AUC
- Confusion Matrix

**回归指标**：
- MSE, RMSE, MAE, R²

**交叉验证**：
```python
from sklearn.model_selection import cross_val_score, KFold
scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
```

### 1.4 特征工程

```python
# 特征缩放
from sklearn.preprocessing import StandardScaler, MinMaxScaler

# 类别编码
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

# 特征选择
from sklearn.feature_selection import SelectKBest, RFE

# 缺失值处理
from sklearn.impute import SimpleImputer, KNNImputer
```

---

## 二、深度学习基础

### 2.1 神经网络核心组件

| 组件 | 作用 |
|-----|------|
| 全连接层 (Dense) | 特征变换 |
| 激活函数 | ReLU, GELU, Sigmoid, Tanh, Softmax |
| 损失函数 | CrossEntropy, MSE, Focal Loss |
| 优化器 | SGD, Adam, AdamW, LAMB |
| 正则化 | Dropout, L1/L2, BatchNorm, LayerNorm |

### 2.2 网络架构

**CNN（卷积神经网络）**：
```
图像任务：ResNet, VGG, EfficientNet, ConvNeXt
目标检测：YOLO, Faster R-CNN, DETR
语义分割：U-Net, DeepLab, SegFormer
```

**RNN/LSTM/GRU**：
```
序列建模：时间序列、早期NLP
问题：梯度消失、长距离依赖
```

**Transformer**：
```
核心机制：Self-Attention, Multi-Head Attention
位置编码：Sinusoidal, RoPE, ALiBi
架构变体：Encoder-only, Decoder-only, Encoder-Decoder
```

### 2.3 训练技巧

```python
# 学习率调度
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=100)
scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=1e-3)

# 梯度裁剪
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

# 混合精度训练
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()
with autocast():
    output = model(input)
    loss = criterion(output, target)
```

### 2.4 框架对比

| 框架 | 特点 | 适用场景 |
|-----|------|---------|
| **PyTorch** | 动态图，调试友好，研究首选 | 研究、原型、LLM |
| **TensorFlow** | 静态图，生产部署成熟 | 大规模部署、移动端 |
| **JAX** | 函数式，XLA 编译，TPU 友好 | 研究、Google 生态 |
| **Keras** | 高级 API，快速原型 | 入门、快速实验 |

---

## 三、大语言模型（LLM）

### 3.1 Transformer 架构详解

```
输入 → Tokenization → Embedding + Position Encoding
    → [Multi-Head Attention → Add & Norm → FFN → Add & Norm] × N
    → Output Layer
```

**关键组件**：
- **Tokenizer**：BPE, WordPiece, SentencePiece, Unigram
- **Attention**：Scaled Dot-Product Attention
- **FFN**：通常 4x 隐藏层维度
- **Normalization**：Pre-LN vs Post-LN

### 3.2 主流模型架构

| 类型 | 代表模型 | 特点 |
|-----|---------|------|
| Encoder-only | BERT, RoBERTa | 双向，适合理解任务 |
| Decoder-only | GPT, LLaMA, Qwen | 自回归，适合生成 |
| Encoder-Decoder | T5, BART | 序列到序列 |

### 3.3 模型规模与参数

```
参数量 = 12 × L × d² (近似，Transformer)

L = 层数
d = 隐藏维度

示例：
- GPT-3: 175B 参数
- LLaMA-2 70B: 70B 参数
- Qwen-72B: 72B 参数
```

### 3.4 注意力优化

| 技术 | 原理 | 复杂度 |
|-----|------|--------|
| 标准 Attention | 全量计算 | O(n²) |
| Flash Attention | 分块计算，IO 优化 | O(n²) 但更快 |
| Multi-Query Attention | 共享 KV | 减少显存 |
| Grouped-Query Attention | 分组共享 KV | 平衡性能与质量 |
| Sliding Window | 局部注意力 | O(n × w) |

### 3.5 位置编码

```python
# RoPE (Rotary Position Embedding)
# 旋转位置编码，支持外推

# ALiBi (Attention with Linear Biases)
# 线性偏置，无需训练位置参数
```

---

## 四、LLM 训练与微调

### 4.1 预训练

```
数据规模：万亿 Token
任务：Next Token Prediction (CLM) / Masked LM (MLM)
资源：数千 GPU，数月训练
```

### 4.2 微调方法

| 方法 | 参数量 | 显存需求 | 适用场景 |
|-----|-------|---------|---------|
| Full Fine-tuning | 100% | 最高 | 资源充足 |
| LoRA | ~0.1% | 低 | 主流方案 |
| QLoRA | ~0.1% + 量化 | 最低 | 消费级 GPU |
| Prefix Tuning | ~0.1% | 低 | 特定任务 |
| P-Tuning v2 | ~0.1% | 低 | 中文任务 |
| Adapter | ~1-5% | 中 | 多任务 |

**LoRA 实现**：
```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=8,                    # 秩
    lora_alpha=32,          # 缩放因子
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)
```

### 4.3 RLHF（人类反馈强化学习）

```
流程：
1. SFT (Supervised Fine-Tuning) - 监督微调
2. RM (Reward Model) - 训练奖励模型
3. PPO/DPO - 强化学习优化

DPO (Direct Preference Optimization)：
- 无需单独训练 RM
- 直接优化偏好数据
- 更稳定，更高效
```

### 4.4 量化

```python
# 常见量化精度
FP32 → FP16/BF16 → INT8 → INT4

# GPTQ 量化
from auto_gptq import AutoGPTQForCausalLM

# AWQ 量化
from awq import AutoAWQForCausalLM

# bitsandbytes
import bitsandbytes as bnb
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)
```

---

## 五、Prompt Engineering

### 5.1 基础技巧

```
Zero-shot：直接提问
Few-shot：提供示例
Chain-of-Thought (CoT)：逐步推理
Self-Consistency：多次采样投票
Tree-of-Thought：树状探索
ReAct：推理 + 行动
```

### 5.2 Prompt 模板

```python
# System Prompt
system_prompt = """You are a helpful assistant. 
Follow these rules:
1. Be concise and accurate
2. Cite sources when possible
3. Admit uncertainty"""

# Few-shot Template
few_shot_prompt = """
Example 1:
Input: {example_input_1}
Output: {example_output_1}

Example 2:
Input: {example_input_2}
Output: {example_output_2}

Now solve:
Input: {user_input}
Output:"""
```

### 5.3 提示词注入防护

```python
# 输入过滤
def sanitize_input(text):
    # 移除潜在注入指令
    dangerous_patterns = ["ignore previous", "disregard", "new instructions"]
    for pattern in dangerous_patterns:
        text = text.replace(pattern, "")
    return text

# 输出检验
def validate_output(response):
    # 检查是否泄露系统提示
    # 检查是否执行了非预期操作
    pass
```

---

## 六、RAG（检索增强生成）

### 6.1 基本架构

```
Query → Embedding → Vector Search → Top-K Retrieval → Context Augmentation → LLM → Response
```

### 6.2 核心组件

**文档处理**：
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", ".", " "]
)
chunks = splitter.split_documents(documents)
```

**Embedding 模型**：
```
开源：BGE, E5, GTE, Jina
商业：OpenAI text-embedding-3, Cohere
多语言：multilingual-e5, BGE-M3
```

**向量数据库**：
| 数据库 | 特点 |
|-------|------|
| Milvus | 分布式，高性能 |
| Pinecone | 托管服务，易用 |
| Weaviate | 混合搜索 |
| Qdrant | Rust 实现，高效 |
| Chroma | 轻量，适合原型 |
| FAISS | Facebook 开源，本地库 |

### 6.3 高级 RAG 技术

```
查询改写：Query Rewriting, HyDE
检索优化：Hybrid Search (BM25 + Vector)
重排序：Cross-encoder Reranking
迭代检索：Self-RAG, CRAG
知识图谱：Graph RAG
```

### 6.4 RAG 评估

```python
# 评估指标
- Retrieval Recall@K：检索召回率
- Context Relevance：上下文相关性
- Faithfulness：生成内容忠实度
- Answer Relevance：答案相关性

# 评估工具
- RAGAS
- TruLens
- DeepEval
```

---

## 七、AI Agent

### 7.1 Agent 架构

```
感知 → 规划 → 行动 → 观察 → 循环

核心组件：
- LLM（大脑）
- Memory（记忆）
- Tools（工具）
- Planning（规划）
```

### 7.2 工具调用

```python
# Function Calling (OpenAI 格式)
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)
```

### 7.3 Agent 框架

| 框架 | 特点 |
|-----|------|
| LangChain | 功能全面，生态丰富 |
| LlamaIndex | 数据索引专精 |
| AutoGen | 多 Agent 协作 |
| CrewAI | 团队协作 Agent |
| Semantic Kernel | 微软生态 |

### 7.4 记忆系统

```python
# 短期记忆：对话历史
conversation_history = []

# 长期记忆：向量存储
vector_store.add(memory_embedding)

# 工作记忆：当前任务上下文
working_memory = {"current_task": task, "intermediate_results": []}
```

---

## 八、多模态

### 8.1 视觉-语言模型

| 模型 | 能力 |
|-----|------|
| GPT-4V/4o | 图像理解、生成 |
| Claude 3 | 图像理解 |
| LLaVA | 开源 VLM |
| Qwen-VL | 开源多模态 |
| CLIP | 图文对齐 |
| BLIP-2 | 图像描述 |

### 8.2 图像生成

```
Diffusion Models：
- Stable Diffusion (SD 1.5, SDXL, SD3)
- DALL-E 3
- Midjourney

技术要点：
- Latent Diffusion：在潜空间扩散
- ControlNet：可控生成
- LoRA：风格/角色微调
- IP-Adapter：图像提示
```

### 8.3 语音模型

```
语音识别 (ASR)：Whisper, Paraformer
语音合成 (TTS)：VITS, ChatTTS, CosyVoice
语音克隆：XTTS, OpenVoice
端到端对话：GPT-4o Voice
```

---

## 九、MLOps 与部署

### 9.1 实验管理

```python
# MLflow
import mlflow

mlflow.set_experiment("my_experiment")
with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_metric("accuracy", 0.95)
    mlflow.pytorch.log_model(model, "model")

# Weights & Biases
import wandb
wandb.init(project="my_project")
wandb.log({"loss": loss, "accuracy": acc})
```

### 9.2 模型服务

| 框架 | 特点 |
|-----|------|
| vLLM | 高性能 LLM 推理 |
| TGI | HuggingFace 推理服务 |
| Triton | NVIDIA 推理服务器 |
| TorchServe | PyTorch 官方 |
| BentoML | 易用的模型打包 |
| Ray Serve | 分布式服务 |

**vLLM 部署**：
```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-2-7b-chat-hf")
sampling_params = SamplingParams(temperature=0.7, max_tokens=256)
outputs = llm.generate(prompts, sampling_params)
```

### 9.3 推理优化

```
技术栈：
- 量化：INT8, INT4, GPTQ, AWQ
- KV Cache：减少重复计算
- Continuous Batching：动态批处理
- Speculative Decoding：投机采样
- Flash Attention：高效注意力
- PagedAttention：vLLM 的内存管理
```

### 9.4 容器化部署

```dockerfile
# Dockerfile
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "serve.py"]
```

```yaml
# docker-compose.yml
services:
  model-server:
    build: .
    ports:
      - "8000:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 十、数据工程

### 10.1 数据收集与清洗

```python
# 数据去重
from datasketch import MinHash, MinHashLSH

# 质量过滤
- 语言检测：langdetect, fasttext
- 有害内容过滤：Perspective API
- 规则过滤：长度、特殊字符比例

# 数据增强
- 回译：Translation → Back-translation
- 同义词替换
- 随机删除/交换
```

### 10.2 标注工具

```
开源：Label Studio, Doccano, CVAT
商业：Scale AI, Labelbox, Amazon SageMaker Ground Truth
LLM 辅助标注：使用 GPT-4 预标注 + 人工审核
```

### 10.3 数据版本控制

```bash
# DVC (Data Version Control)
dvc init
dvc add data/training_data.csv
git add data/training_data.csv.dvc
git commit -m "Add training data"
dvc push
```

---

## 十一、安全与伦理

### 11.1 模型安全

```
对抗攻击：Prompt Injection, Jailbreak
防护措施：
- 输入过滤
- 输出检测
- 安全对齐（RLHF）
- 护栏模型（Guard Model）
```

### 11.2 隐私保护

```
技术：
- 差分隐私 (Differential Privacy)
- 联邦学习 (Federated Learning)
- 安全多方计算 (MPC)
- 数据脱敏
```

### 11.3 负责任的 AI

```
原则：
- 公平性：消除偏见
- 可解释性：模型决策透明
- 可追溯：数据来源可查
- 可控性：人类监督
```

---

## 十二、核心工具与库

### 12.1 Python 生态

| 类别 | 常用库 |
|-----|-------|
| 数据处理 | pandas, polars, numpy |
| 机器学习 | scikit-learn, xgboost, lightgbm |
| 深度学习 | PyTorch, TensorFlow, JAX |
| NLP | transformers, spaCy, nltk |
| CV | torchvision, OpenCV, albumentations |
| LLM | transformers, vllm, llama-cpp-python |
| RAG | langchain, llamaindex, haystack |
| 可视化 | matplotlib, seaborn, plotly |

### 12.2 Hugging Face 生态

```python
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, DPOTrainer
```

### 12.3 开发工具

```
IDE：VS Code, PyCharm, Cursor
Notebook：Jupyter, Colab, Kaggle
调试：pdb, ipdb, debugpy
性能：cProfile, line_profiler, py-spy
```

---

## 十三、学习资源

### 13.1 必读论文

```
Transformer：Attention Is All You Need
BERT：Pre-training of Deep Bidirectional Transformers
GPT：Language Models are Unsupervised Multitask Learners
LLaMA：Open and Efficient Foundation Language Models
RLHF：Training language models to follow instructions
LoRA：Low-Rank Adaptation of Large Language Models
RAG：Retrieval-Augmented Generation for Knowledge-Intensive NLP
```

### 13.2 推荐课程

```
- Stanford CS224N：NLP with Deep Learning
- Stanford CS231N：CNN for Visual Recognition
- Fast.ai：Practical Deep Learning
- Andrej Karpathy：Neural Networks: Zero to Hero
- DeepLearning.AI：LLM 相关课程
```

---

## 十四、技能清单速查

| 层级 | 必备技能 |
|-----|---------|
| **基础** | Python, 线性代数, 概率统计, ML 算法 |
| **深度学习** | PyTorch, CNN, RNN, Transformer |
| **LLM** | 预训练, 微调 (LoRA), RLHF/DPO, 量化 |
| **应用** | Prompt Engineering, RAG, Agent |
| **多模态** | VLM, Diffusion, TTS/ASR |
| **工程** | MLOps, 模型部署, 推理优化 |
| **数据** | 数据清洗, 标注, 版本控制 |
| **安全** | 对抗攻击防护, 隐私保护 |

---

## 参考资料

- [Hugging Face Documentation](https://huggingface.co/docs)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [LangChain Documentation](https://python.langchain.com/)
- [Papers With Code](https://paperswithcode.com/)
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)

---

## 相关文章

- [下一篇：大模型训练为什么GPU比CPU更合适](@/articles/ai/ai-02-大模型训练为什么GPU比CPU更合适.md)
