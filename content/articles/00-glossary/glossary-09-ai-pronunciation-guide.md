+++
title = "AI & ML Terminology Pronunciation Guide"
description = "AI与机器学习领域英文术语发音指南：业界标准读法、音标、简明概念释义"
date = 2026-02-13
weight = 9000
draft = false
[taxonomies]
tags = ["Glossary", "AI", "Pronunciation", "Reference"]
[extra]
toc = true
+++

# AI & ML Terminology Pronunciation Guide

业界标准发音指南。每个术语包含：**音标**（IPA 或近似注音）、**业界通行读法**、**一句话概念释义**。

> **配套文章**：[从模型诞生到 AI 应用：全链路认知](@/articles/ai/ai-34-从模型诞生到AI应用全链路认知.md)  
> **概念详解**：[AI & ML 术语表](@/articles/00-glossary/glossary-08-ai-ml-concepts.md)

> **发音约定**：音标采用简化 IPA + 中文近似读音辅助。重音用 **粗体** 标记。"业界常读"指英语技术圈最普遍的读法。

---

## 1. Activation Functions (激活函数)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **ReLU** | /ˈriːluː/（**瑞**-露） | "REE-loo" | Rectified Linear Unit，整流线性单元。负值归零，正值不变。最经典的激活函数。 |
| **GELU** | /ˈɡiːluː/（**基**-露） | "GEE-loo" | Gaussian Error Linear Unit。GPT/BERT 使用的平滑激活函数，保留部分负值信息。 |
| **SiLU** | /ˈsiːluː/（**希**-露） | "SEE-loo" | Sigmoid Linear Unit，也叫 Swish。LLaMA 等模型使用。 |
| **SwiGLU** | /ˈswɪɡluː/（**斯威**-格露） | "SWIG-loo" | Swish + Gated Linear Unit 的组合。当前主流 LLM（LLaMA 3 等）的 FFN 激活方式。 |
| **Sigmoid** | /ˈsɪɡmɔɪd/（**西格**-莫伊德） | "SIG-moyd" | S 形曲线函数，将任意值压缩到 0~1。经典但已少用于深层网络（梯度消失问题）。 |
| **Tanh** | /tæntʃ/ 或 /tænˈeɪtʃ/（**谈奇** 或 **谈-H**） | "tanch" 或 "tan-H" | 双曲正切函数，输出 -1~1。比 Sigmoid 好一些但同样有梯度消失问题。 |
| **Softmax** | /ˈsɒftmæks/（**索夫特**-麦克斯） | "SOFT-max" | 把一组数字转换成概率分布（和为 1）。分类任务最后一层常用。 |
| **Swish** | /swɪʃ/（**斯威什**） | "swish" | SiLU 的别名。Google 提出的自门控激活函数。 |
| **Leaky ReLU** | /ˈliːki ˈriːluː/（**利**-基 **瑞**-露） | "LEE-kee REE-loo" | "有泄漏的 ReLU"——负值不归零而是乘以一个小系数（如 0.01）。 |
| **GLU** | /ˌdʒiːelˈjuː/（G-L-U 逐字母读） | "G-L-U" | Gated Linear Unit，门控线性单元。SwiGLU 的组成部分。 |

---

## 2. Model Architectures & Names (模型架构与名称)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **Transformer** | /trænsˈfɔːrmər/（**纯斯福**-默） | "trans-FOR-mer" | 2017 年 Google 提出的注意力架构，取代 RNN，是当前几乎所有大模型的基础。 |
| **GPT** | /ˌdʒiːpiːˈtiː/（G-P-T 逐字母） | "G-P-T" | Generative Pre-trained Transformer。OpenAI 的生成式预训练模型系列。 |
| **BERT** | /bɜːrt/（**伯特**） | "BERT"（像人名） | Bidirectional Encoder Representations from Transformers。Google 的双向编码模型。 |
| **LLaMA** | /ˈlɑːmə/（**拉**-马） | "LAH-ma"（像动物羊驼） | Large Language Model Meta AI。Meta 开源的大语言模型系列。 |
| **ResNet** | /ˈreznet/（**瑞兹**-奈特） | "REZ-net" | Residual Network，残差网络。引入 Skip Connection，解决深层网络退化问题。 |
| **AlexNet** | /ˈæleksnet/（**阿列克斯**-奈特） | "ALEX-net" | 以 Alex Krizhevsky 命名，2012 年点燃深度学习革命的 CNN。 |
| **VGG** | /ˌviːdʒiːˈdʒiː/（V-G-G 逐字母） | "V-G-G" | Visual Geometry Group（牛津大学实验室名）。以极简"堆卷积"闻名的 CNN。 |
| **YOLO** | /ˈjoʊloʊ/（**优**-楼） | "YO-lo" | You Only Look Once。实时目标检测模型，一次前向即可输出所有检测框。 |
| **Mistral** | /mɪˈstrɑːl/（米**斯特拉**尔） | "mi-STRAHL" | 法国 AI 公司 Mistral AI 的模型系列。名字来自法国南部的季风。 |
| **Qwen** | /tʃwɛn/（**趣闻**） | "chwen" | 阿里云的大模型系列（通义千问）。中文名拼音。 |

---

## 3. Neural Network Components (神经网络组件)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **CNN** | /ˌsiːenˈen/（C-N-N 逐字母） | "C-N-N" | Convolutional Neural Network，卷积神经网络。图像处理的核心架构。 |
| **RNN** | /ˌɑːrenˈen/（R-N-N 逐字母） | "R-N-N" | Recurrent Neural Network，循环神经网络。处理序列数据，已被 Transformer 大部分取代。 |
| **LSTM** | /ˌelestiːˈem/（L-S-T-M 逐字母） | "L-S-T-M" | Long Short-Term Memory，长短期记忆网络。RNN 的改进版，缓解长程遗忘。 |
| **MLP** | /ˌemˈelˈpiː/（M-L-P 逐字母） | "M-L-P" | Multi-Layer Perceptron，多层感知机。最基础的全连接前馈网络。 |
| **FFN** | /ˌefˈefˈen/（F-F-N 逐字母） | "F-F-N" | Feed-Forward Network，前馈网络。Transformer 中每层的两个子层之一。 |
| **Attention** | /əˈtenʃən/（阿**腾**-션） | "uh-TEN-shun" | 注意力机制。让模型"关注"输入中与当前计算最相关的部分。Transformer 的核心。 |
| **Self-Attention** | /ˈself əˈtenʃən/ | "self uh-TEN-shun" | 自注意力。输入序列中的每个元素关注序列中的所有其他元素。 |
| **Embedding** | /ɪmˈbedɪŋ/（因**贝**-丁） | "em-BED-ding" | 嵌入。将离散符号（词、token）映射为连续向量空间中的稠密向量。 |
| **Token** | /ˈtoʊkən/（**托**-肯） | "TOE-ken" | 文本被分割成的最小单位（通常是子词）。LLM 处理的基本单元。 |
| **Tokenizer** | /ˈtoʊkənaɪzər/（**托**-肯-奈-泽） | "TOE-keh-nai-zer" | 分词器。将文本切分成 token 序列的工具。 |
| **Neuron** | /ˈnjʊərɒn/（**纽**-荣） | "NYOO-ron" | 神经元。网络中最小的计算单元：W·x + b → 激活 → 输出一个数字。 |
| **Backbone** | /ˈbækboʊn/（**拜克**-波恩） | "BACK-bone" | 骨干网络。模型中负责特征提取的主体部分（相对于分类头）。 |
| **Kernel** | /ˈkɜːrnəl/（**克**-诺） | "KER-nel" | 卷积核。在输入上滑动的小权重矩阵。也指 GPU 上运行的计算函数。 |

---

## 4. Training Concepts (训练概念)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **Epoch** | /ˈiːpɒk/ 或 /ˈepək/（**伊**-泼克） | "EE-pock" | 一个 epoch = 模型把所有训练数据看了一遍。通常需要训练多个 epoch。 |
| **Batch** | /bætʃ/（**拜奇**） | "batch" | 批次。每次训练更新时同时处理的样本数量。 |
| **Gradient** | /ˈɡreɪdiənt/（**格瑞**-迪恩特） | "GRAY-dee-ent" | 梯度。损失函数对参数的偏导数，指示"参数应该往哪个方向调、调多少"。 |
| **Backpropagation** | /ˌbækprɒpəˈɡeɪʃən/（拜克-普罗帕-**盖**-申） | "back-prop-uh-GAY-shun"，常缩写为 "backprop" | 反向传播。从输出到输入，逐层计算每个参数的梯度。 |
| **Loss** | /lɒs/（**洛斯**） | "loss" | 损失。衡量模型预测与正确答案之间差距的数值。训练目标 = 最小化 loss。 |
| **Overfitting** | /ˌoʊvərˈfɪtɪŋ/（欧弗-**菲**-听） | "OH-ver-fit-ting" | 过拟合。模型在训练数据上表现好但在新数据上差——"背答案"而非"学规律"。 |
| **Fine-tuning** | /ˈfaɪn tjuːnɪŋ/（**凡**-图宁） | "fine-TOON-ing" | 微调。在预训练模型基础上，用少量任务数据继续训练。 |
| **Pre-training** | /ˌpriːˈtreɪnɪŋ/（普瑞-**纯**-宁） | "pree-TRAIN-ing" | 预训练。在大规模无标签数据上训练模型的初始阶段。 |
| **Transfer Learning** | /ˈtrænsfɜːr ˈlɜːrnɪŋ/ | "TRANS-fer LER-ning" | 迁移学习。把在一个任务上训好的模型（特别是底层权重）复用到另一个任务上。 |
| **Dropout** | /ˈdrɒpaʊt/（**卓**-跑特） | "DROP-out" | 训练时随机"关掉"一部分神经元，防止过拟合和冗余。 |
| **Xavier** | /ˈzeɪviər/（**泽**-维尔） | "ZAY-vee-er" | Xavier Glorot 提出的权重初始化方法。适用于 Sigmoid/Tanh 激活。 |
| **Kaiming** | /ˈkaɪmɪŋ/（**凯**-明） | "KAI-ming" | 何恺明（Kaiming He）提出的权重初始化方法。适用于 ReLU 系列激活。 |
| **Adam** | /ˈædəm/（**亚**-当） | "ADD-um"（像人名 Adam） | Adaptive Moment Estimation。当前最流行的优化器，自适应学习率。 |
| **SGD** | /ˌesˌdʒiːˈdiː/（S-G-D 逐字母） | "S-G-D" | Stochastic Gradient Descent，随机梯度下降。最基础的优化器。 |

---

## 5. LLM & NLP Specific (大语言模型与自然语言处理)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **LLM** | /ˌelˈelˈem/（L-L-M 逐字母） | "L-L-M" | Large Language Model，大语言模型。GPT、LLaMA 等都是 LLM。 |
| **NLP** | /ˌenˈelˈpiː/（N-L-P 逐字母） | "N-L-P" | Natural Language Processing，自然语言处理。 |
| **BPE** | /ˌbiːˈpiːˈiː/（B-P-E 逐字母） | "B-P-E" | Byte Pair Encoding，字节对编码。最主流的子词分词算法（GPT 系列使用）。 |
| **OOV** | /ˌoʊˈoʊˈviː/（O-O-V 逐字母） | "O-O-V" | Out-of-Vocabulary，词表外词。分词器词表里没有的词。 |
| **Autoregressive** | /ˌɔːtoʊrɪˈɡresɪv/（奥拖-瑞**格瑞**-西弗） | "aw-toe-ree-GRESS-iv" | 自回归。每步基于前面所有输出来预测下一个，逐个生成。GPT 的核心生成方式。 |
| **Prompt** | /prɒmpt/（**普朗普特**） | "prompt" | 提示词。给 LLM 的输入指令或上下文。 |
| **Few-shot** | /ˈfjuːʃɒt/（**菲尤**-肖特） | "FEW-shot" | 少样本学习。在 prompt 中给几个示例，让模型学会任务模式。 |
| **Chain-of-Thought** | — | "chain of thought"，常缩写 **CoT**（/ˌsiːoʊˈtiː/） | 思维链。让 LLM "一步步推理"而非直接给答案，提升推理准确度。 |
| **In-Context Learning** | — | "in-CON-text LER-ning"，常缩写 **ICL** | 上下文学习。模型通过 prompt 中的示例即时"学会"新任务，不改权重。 |
| **Temperature** | /ˈtemprətʃər/（**坦姆**-普瑞-彻） | "TEM-pruh-chur" | 温度。控制 LLM 输出的随机性：低温 → 确定性高，高温 → 更"创造性"。 |
| **Top-k** | — | "top K" | 只从概率最高的 k 个 token 中采样。 |
| **Top-p** | — | "top P"（也叫 Nucleus Sampling） | 从累积概率达到 p 的最小 token 集合中采样。 |
| **Argmax** | /ˈɑːrɡmæks/（**阿格**-麦克斯） | "ARG-max" | 返回概率最大的那个 token。贪心解码策略。 |
| **Perplexity** | /pərˈpleksɪti/（珀**普莱克**-西提） | "per-PLEX-ih-tee" | 困惑度。衡量语言模型好坏的指标——越低越好。 |
| **RLHF** | /ˌɑːrelˈeɪtʃˈef/（R-L-H-F 逐字母） | "R-L-H-F" | Reinforcement Learning from Human Feedback，人类反馈强化学习。让模型对齐人类偏好。 |
| **Hallucination** | /həˌluːsɪˈneɪʃən/（哈-露西-**内**-申） | "huh-loo-sih-NAY-shun" | 幻觉。LLM 生成看似合理但实际错误的内容。 |

---

## 6. Model Optimization & Compression (模型优化与压缩)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **LoRA** | /ˈlɔːrə/（**萝**-拉） | "LOR-uh"（像女名 Laura） | Low-Rank Adaptation。冻结原权重，在旁边加小参数矩阵做高效微调。 |
| **QLoRA** | /ˈkjuːlɔːrə/（**丘**-萝拉） | "Q-LOR-uh"（Q + Laura） | Quantized LoRA。4-bit 量化 + LoRA，单卡微调大模型。 |
| **Quantization** | /ˌkwɒntɪˈzeɪʃən/（宽提-**泽**-申） | "kwon-tih-ZAY-shun" | 量化。将高精度参数（FP32/FP16）压缩为低精度（INT8/INT4），减小模型体积。 |
| **Pruning** | /ˈpruːnɪŋ/（**普入**-宁） | "PROO-ning" | 剪枝。删除冗余的神经元或连接，让模型更小更快。 |
| **Distillation** | /ˌdɪstɪˈleɪʃən/（迪斯提-**雷**-申） | "dis-tih-LAY-shun"，常说 "Knowledge Distillation" | 知识蒸馏。用大模型（教师）教小模型（学生），保留大部分能力但体积更小。 |
| **FP16** | — | "F-P sixteen" 或 "half precision" | 16 位浮点数。模型训练和推理的常用精度。 |
| **FP32** | — | "F-P thirty-two" 或 "single precision" | 32 位浮点数。最高精度，训练时的默认精度。 |
| **INT8** | — | "int eight" | 8 位整数。推理时的常用量化精度。 |
| **INT4** | — | "int four" | 4 位整数。激进量化，显著减小模型体积。 |
| **VRAM** | /ˈviːræm/（**V**-RAM） | "V-RAM" | Video RAM，显存。GPU 上的内存，决定能加载多大的模型。 |
| **MoE** | /ˌemoʊˈiː/（M-O-E 逐字母）或 /moʊ/（**莫**） | "M-O-E" 或直接 "moe" | Mixture of Experts，混合专家。每次只激活部分参数，提升效率。 |
| **KV Cache** | — | "K-V cache" | Key-Value Cache。推理时缓存已计算的 Key 和 Value 矩阵，避免重复计算。 |
| **Speculative Decoding** | /ˈspekjulətɪv dɪˈkoʊdɪŋ/ | "SPECK-yoo-luh-tiv dee-CODE-ing" | 推测解码。用小模型快速"猜"多个 token，大模型一次验证，加速推理。 |
| **PagedAttention** | — | "paged uh-TEN-shun" | 分页注意力。vLLM 的核心技术，像操作系统管理虚拟内存一样管理 KV Cache。 |
| **Continuous Batching** | — | "con-TIN-yoo-us batch-ing" | 连续批处理。请求动态加入/退出批次，提升 GPU 利用率。 |

---

## 7. Formats & Frameworks (格式与框架)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **PyTorch** | /ˈpaɪtɔːrtʃ/（**派**-拖奇） | "PIE-torch" | Meta 开源的深度学习框架。当前学术界和工业界最主流。 |
| **TensorFlow** | /ˈtensərfloʊ/（**腾**-瑟-弗楼） | "TEN-ser-flow" | Google 开源的深度学习框架。 |
| **JAX** | /dʒæks/（**杰克斯**） | "jacks" | Google 的高性能数值计算库。以函数式编程和 XLA 编译著称。 |
| **ONNX** | /ˈɒnɪks/（**昂**-尼克斯） | "ON-ix"（像 onyx 宝石） | Open Neural Network Exchange。跨框架的模型中间格式，同时保存计算图+权重。 |
| **GGUF** | /ˌdʒiːdʒiːjuːˈef/（G-G-U-F 逐字母） | "G-G-U-F" | GPT-Generated Unified Format。llama.cpp 使用的量化模型格式。 |
| **GGML** | /ˌdʒiːdʒiːemˈel/（G-G-M-L 逐字母） | "G-G-M-L" | GGUF 的前身格式。 |
| **SafeTensors** | — | "safe-TEN-sors" | HuggingFace 推出的安全模型存储格式，防止代码注入。 |
| **TensorRT** | /ˈtensərɑːrtiː/（腾瑟-**阿尔**-T） | "TEN-ser-R-T" | NVIDIA 的推理优化引擎。将模型编译为高度优化的推理计划。 |
| **vLLM** | /ˌviːˈelelˈem/（V-L-L-M） | "V-L-L-M" | 高效 LLM 推理引擎。PagedAttention 和 Continuous Batching 的参考实现。 |
| **llama.cpp** | — | "llama C-P-P" 或 "llama C plus plus" | 纯 C/C++ 实现的 LLM 推理工具，支持 CPU 和量化推理。 |
| **HuggingFace** | /ˈhʌɡɪŋfeɪs/（**哈**-ging-费斯） | "HUG-ing-face" | AI 社区平台和开源工具集（transformers 库、模型仓库等）。 |
| **DeepSpeed** | /ˈdiːpspiːd/（**迪普**-斯必德） | "DEEP-speed" | 微软开源的分布式训练和推理优化库。 |
| **Megatron** | /ˈmeɡətrɒn/（**梅嘎**-纯） | "MEG-uh-tron" | NVIDIA 的大规模分布式训练框架。名字来自变形金刚。 |
| **LangChain** | /ˈlæŋtʃeɪn/（**兰**-纯） | "LANG-chain" | 构建 LLM 应用的开源框架（RAG、Agent 等）。 |
| **LangGraph** | /ˈlæŋɡræf/（**兰**-格拉夫） | "LANG-graph" | LangChain 团队推出的有状态 Agent 编排框架。 |
| **LlamaIndex** | /ˈlɑːmə ˈɪndeks/ | "LAH-ma IN-dex" | 构建 RAG 应用的开源框架，专注数据索引和检索。 |
| **Faiss** | /feɪs/（**费斯**） | "face"（和"脸"同音） | Facebook AI Similarity Search。Meta 开源的高效向量检索库。 |
| **Milvus** | /ˈmɪlvəs/（**米尔**-弗斯） | "MIL-vus" | 开源向量数据库。名字来自拉丁语（鸢鹰属）。 |
| **Qdrant** | /ˈkwɒdrənt/（**夸**-准特） | "KWOD-rant" | 开源向量数据库。名字来自 "quadrant"（象限）。 |
| **Pinecone** | /ˈpaɪnkoʊn/（**派恩**-孔） | "PINE-cone" | 商业向量数据库服务。名字就是"松果"。 |

---

## 8. Techniques & Methods (技术与方法)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **RAG** | /ræɡ/（**瑞格**） | "rag"（像"破布"） | Retrieval-Augmented Generation，检索增强生成。外挂知识库补充 LLM 知识盲区。 |
| **Agent** | /ˈeɪdʒənt/（**诶**-琴特） | "AY-jent" | 智能体。LLM 驱动的自主规划 + 工具调用系统。 |
| **ReAct** | /riːˈækt/（瑞-**艾克特**） | "ree-ACT" | Reasoning + Acting。让 LLM 交替"思考"和"行动"的 Agent 框架。 |
| **Scaling Laws** | — | "SCALE-ing laws" | 缩放定律。模型性能与参数量/数据量/算力的幂律关系。 |
| **Chinchilla** | /tʃɪnˈtʃɪlə/（琴-**奇拉**） | "chin-CHILL-uh"（像动物栗鼠） | DeepMind 的研究，给出训练 compute-optimal 模型的最佳参数/数据比。 |
| **Emergence** | /ɪˈmɜːrdʒəns/（伊-**默**-琴斯） | "ee-MER-junce" | 涌现。模型规模超过某个阈值后突然出现"没教过"的新能力。 |
| **NAS** | /næs/（**纳斯**） | "nass" | Neural Architecture Search，神经架构搜索。用算法自动搜索最优网络结构。 |
| **Grad-CAM** | /ˌɡrædˈkæm/（格拉德-**凯姆**） | "grad-CAM" | Gradient-weighted Class Activation Mapping。可视化 CNN "看"了图片的哪些区域。 |
| **Gabor** | /ˈɡɑːbɔːr/（**嘎**-博尔） | "GAH-bor" | Gabor 滤波器。一种数学上定义的边缘/频率检测核，和 CNN 第一层学到的卷积核高度相似。 |

---

## 9. Distributed Training & Hardware (分布式训练与硬件)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **GPU** | /ˌdʒiːpiːˈjuː/（G-P-U 逐字母） | "G-P-U" | Graphics Processing Unit。深度学习的核心算力硬件。 |
| **TPU** | /ˌtiːpiːˈjuː/（T-P-U 逐字母） | "T-P-U" | Tensor Processing Unit。Google 自研的 AI 专用芯片。 |
| **CUDA** | /ˈkuːdə/（**库**-达） | "KOO-dah" | Compute Unified Device Architecture。NVIDIA 的 GPU 编程平台。 |
| **A100** | — | "A one hundred" | NVIDIA 数据中心 GPU（Ampere 架构）。AI 训练的主力卡。 |
| **FSDP** | /ˌefesdiːˈpiː/（F-S-D-P 逐字母） | "F-S-D-P" | Fully Sharded Data Parallel。PyTorch 原生的分布式训练策略。 |
| **NCCL** | /ˈnɪkəl/（**尼**-克尔） | "nickel"（像"镍币"） | NVIDIA Collective Communication Library。GPU 间通信的标准库。 |

---

## 10. AI Philosophy & Research (AI 哲学与研究)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **Alignment** | /əˈlaɪnmənt/（阿**赖恩**-门特） | "uh-LINE-ment" | 对齐。确保 AI 系统的行为与人类意图和价值观一致。 |
| **Neuro-Symbolic** | /ˈnjʊəroʊ sɪmˈbɒlɪk/ | "NYOO-ro sim-BOL-ik" | 神经符号融合。将神经网络（感知）与符号推理（逻辑）结合的研究方向。 |
| **Catastrophic Forgetting** | — | "cat-uh-STROF-ik for-GET-ting" | 灾难性遗忘。模型学新知识时覆盖旧知识的问题。 |
| **Reward Hacking** | — | "ree-WARD HACK-ing" | 奖励黑客。AI 系统找到最大化奖励的"作弊捷径"而非真正完成任务。 |
| **Goal Drift** | — | "goal drift" | 目标漂移。自我改进的 AI 系统目标逐渐偏离人类初始设定。 |

---

## 11. Concepts from Training & Architecture Design (训练与架构设计概念)

| 术语 | 音标 / 近似读音 | 业界常读 | 概念释义 |
|------|----------------|---------|---------|
| **Skip Connection** | — | "skip connection" | 跳跃连接（残差连接）。让信息绕过某些层直接传递。ResNet 的核心创新。 |
| **Residual** | /rɪˈzɪdjuəl/（瑞-**兹都**-额尔） | "ree-ZID-yoo-ul" | 残差。Skip Connection 中"多学到的增量部分"。 |
| **Degradation Problem** | — | "deg-ruh-DAY-shun PROB-lem" | 退化问题。层数增多但性能反而下降（非过拟合）。ResNet 之前的核心难题。 |
| **Feature Map** | — | "FEE-chur map" | 特征图。卷积核扫过图像后输出的二维数组，表示每个位置的特征强度。 |
| **Affine Transformation** | /ˈæfaɪn/ | "AFF-ine trans-for-MAY-shun" | 仿射变换。W·x + b 这种"线性变换+平移"的统称。 |
| **Inference** | /ˈɪnfərəns/（**因**-弗-润斯） | "IN-fur-ence" | 推理。用训练好的模型对新输入做预测。 |
| **Forward Pass** | — | "FOR-werd pass" | 前向传播/前向计算。输入沿计算图从第一层流到最后一层，得到输出。 |
| **Warmup** | /ˈwɔːrmʌp/（**沃姆**-阿普） | "WARM-up" | 学习率预热。训练初期从极小学习率逐渐增大，避免初始阶段梯度爆炸。 |
| **Cosine Decay** | — | "CO-sine dee-KAY" | 余弦衰减。学习率按余弦曲线逐渐降低的调度策略。 |
| **Weight Decay** | — | "weight dee-KAY" | 权重衰减。正则化方法，每步让权重略微缩小，防止过拟合。 |

---

## Quick Phonetic Cheat Sheet (速查发音表)

最容易读错的术语：

| 术语 | 错误读法 | 正确读法 |
|------|---------|---------|
| **ReLU** | "R-E-L-U"（逐字母） | **"REE-loo"**（瑞露） |
| **GELU** | "G-E-L-U"（逐字母） | **"GEE-loo"**（基露） |
| **LoRA** | "LOR-A"（逐字母 A） | **"LOR-uh"**（萝拉，像 Laura） |
| **ONNX** | "O-N-N-X"（逐字母） | **"ON-ix"**（昂尼克斯，像 onyx） |
| **Epoch** | "ee-POCH"（重音错） | **"EE-pock"**（伊泼克） |
| **BERT** | "B-E-R-T"（逐字母） | **"BERT"**（伯特，像人名） |
| **LLaMA** | "L-L-A-M-A"（逐字母） | **"LAH-ma"**（拉马，像羊驼） |
| **Faiss** | "FAI-ss" | **"face"**（费斯，和"脸"同音） |
| **NCCL** | "N-C-C-L"（逐字母） | **"nickel"**（尼克尔，像"镍币"） |
| **CUDA** | "C-U-D-A"（逐字母） | **"KOO-dah"**（库达） |
| **PyTorch** | "py-TORCH"（重音错） | **"PIE-torch"**（派拖奇） |
| **JAX** | "J-A-X"（逐字母） | **"jacks"**（杰克斯） |
| **Qwen** | "Q-wen" | **"chwen"**（趣闻） |
| **Tanh** | "tan-H"（只读字母） | **"tanch"**（谈奇） |
| **SwiGLU** | "SWI-G-L-U" | **"SWIG-loo"**（斯威格露） |
| **GGUF** | 试图拼读 | **逐字母 "G-G-U-F"** |
| **RAG** | "R-A-G"（逐字母） | **"rag"**（瑞格，像"破布"） |
| **NAS** | "N-A-S"（逐字母） | **"nass"**（纳斯） |
| **Chinchilla** | "CHIN-chilla" | **"chin-CHILL-uh"**（琴奇拉，像栗鼠） |
