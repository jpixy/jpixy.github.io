+++
title = "Notebook执行Agent架构设计"
date = 2025-01-13
description = "设计一个基于LLM的智能Agent，利用nbclient/papermill实现Jupyter Notebook的一键执行并生成HTML报告"
[taxonomies]
tags = ["ai", "agent", "jupyter", "automation", "llm"]
+++

# Notebook 执行 Agent 架构设计

本文介绍如何设计一个 AI Agent，实现 Jupyter Notebook 的智能化"一键执行"，自动处理执行过程中的错误，并生成 HTML 格式的结果报告。

---

## 一、项目目标与价值

### 1.1 解决的痛点

| 传统方式 | Agent 方式 |
|----------|-----------|
| 手动逐单元格执行 | 一键全流程执行 |
| 执行失败需人工排查 | Agent 自动诊断修复 |
| 结果分享需手动导出 | 自动生成 HTML 报告 |
| 参数修改需进入 Notebook | 外部传参，无需打开 |
| 依赖环境问题难以发现 | 预检查环境依赖 |

### 1.2 核心能力

```
┌─────────────────────────────────────────────────────────┐
│                  Notebook 执行 Agent                      │
├─────────────────────────────────────────────────────────┤
│  ✓ 参数化执行（Parameterized Execution）                  │
│  ✓ 错误自动修复（Auto Error Recovery）                    │
│  ✓ 执行进度追踪（Progress Tracking）                      │
│  ✓ HTML 报告生成（Report Generation）                     │
│  ✓ 执行日志记录（Execution Logging）                      │
│  ✓ 超时与资源控制（Timeout & Resource Control）           │
└─────────────────────────────────────────────────────────┘
```

---

## 二、技术选型

### 2.1 Notebook 执行引擎对比

| 工具 | 特点 | 适用场景 |
|------|------|----------|
| **nbclient** | 轻量级、底层 API | 需要精细控制 |
| **papermill** | 参数化、易用 | 批量执行、参数注入 |
| **nbconvert** | 格式转换为主 | 导出 HTML/PDF |
| **jupyter_client** | 最底层 | 自定义内核管理 |

### 2.2 推荐组合

```
papermill（参数化执行）
    ↓
nbclient（底层执行控制）
    ↓
nbconvert（HTML 导出）
    ↓
LLM（错误分析与修复建议）
```

### 2.3 LLM 选择

| 场景 | 推荐模型 |
|------|----------|
| 本地部署 | Ollama + CodeLlama/DeepSeek |
| 云端 API | GPT-4 / Claude / 通义千问 |
| 代码理解 | CodeLlama / StarCoder |

---

## 三、整体架构设计

### 3.1 系统架构图

```
                    ┌──────────────────┐
                    │   用户请求入口     │
                    │ (CLI / API / UI)  │
                    └────────┬─────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│                    Agent Controller                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 任务解析器    │  │  状态管理器   │  │  结果聚合器   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────────┬───────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  预检查模块       │ │  执行引擎模块     │ │  后处理模块       │
│  - 依赖检查      │ │  - nbclient      │ │  - HTML 导出     │
│  - 参数验证      │ │  - papermill     │ │  - 日志归档      │
│  - 环境准备      │ │  - 超时控制      │ │  - 结果通知      │
└──────────────────┘ └────────┬─────────┘ └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   错误处理模块    │
                    │  ┌────────────┐  │
                    │  │  LLM 分析   │  │
                    │  │  错误诊断   │  │
                    │  │  修复建议   │  │
                    │  │  自动重试   │  │
                    │  └────────────┘  │
                    └──────────────────┘
```

### 3.2 核心流程

```
1. 接收执行请求（Notebook 路径 + 参数）
       ↓
2. 预检查（依赖、参数、环境）
       ↓
3. 参数注入（papermill 注入参数单元格）
       ↓
4. 逐单元格执行（nbclient）
       ↓
   ┌─ 成功 → 继续下一个单元格
   │
   └─ 失败 → 错误处理模块
              ├─ LLM 分析错误原因
              ├─ 生成修复建议
              ├─ 自动修复（可选）
              └─ 重试或终止
       ↓
5. 执行完成
       ↓
6. 生成 HTML 报告
       ↓
7. 返回结果（成功/失败 + 报告路径）
```

---

## 四、核心模块详解

### 4.1 预检查模块（Pre-flight Checker）

#### 职责

| 检查项 | 描述 |
|--------|------|
| **依赖检查** | 解析 import 语句，检查包是否安装 |
| **参数验证** | 校验传入参数与 Notebook 参数单元格匹配 |
| **资源预估** | 估算内存/GPU 需求 |
| **内核检查** | 确认对应 kernel 可用 |

#### 关键实现思路

```python
# 依赖提取（简化示意）
def extract_imports(notebook_path):
    """从 Notebook 提取所有 import 语句"""
    nb = nbformat.read(notebook_path, as_version=4)
    imports = set()
    
    for cell in nb.cells:
        if cell.cell_type == 'code':
            # 使用 AST 解析 import 语句
            tree = ast.parse(cell.source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.add(node.module.split('.')[0])
    
    return imports
```

---

### 4.2 执行引擎模块（Execution Engine）

#### 4.2.1 基于 papermill 的参数化执行

papermill 的核心能力是**参数注入**：

```python
# 参数化执行核心流程
import papermill as pm

def execute_with_params(input_nb, output_nb, params):
    """
    input_nb: 输入 Notebook 路径
    output_nb: 输出 Notebook 路径（包含执行结果）
    params: 参数字典，注入到 parameters 标签的单元格
    """
    pm.execute_notebook(
        input_path=input_nb,
        output_path=output_nb,
        parameters=params,
        kernel_name='python3',
        progress_bar=True,
        request_save_on_cell_execute=True,  # 每个单元格执行后保存
    )
```

#### 4.2.2 基于 nbclient 的精细控制

当需要更细粒度控制时，使用 nbclient：

```python
from nbclient import NotebookClient
import nbformat

def execute_with_control(notebook_path, timeout_per_cell=300):
    """带超时和进度回调的执行"""
    nb = nbformat.read(notebook_path, as_version=4)
    
    client = NotebookClient(
        nb,
        timeout=timeout_per_cell,
        kernel_name='python3',
        resources={'metadata': {'path': '.'}},
    )
    
    # 逐单元格执行，支持进度追踪
    with client.setup_kernel():
        for index, cell in enumerate(nb.cells):
            if cell.cell_type == 'code':
                try:
                    client.execute_cell(cell, index)
                    print(f"✓ Cell {index} executed")
                except Exception as e:
                    print(f"✗ Cell {index} failed: {e}")
                    raise
    
    return nb
```

#### 4.2.3 超时与资源控制策略

| 控制维度 | 实现方式 |
|----------|----------|
| **单元格超时** | `nbclient.timeout` 参数 |
| **总体超时** | 外层 `asyncio.wait_for` 包装 |
| **内存限制** | Docker/cgroup 隔离执行 |
| **GPU 限制** | `CUDA_VISIBLE_DEVICES` 环境变量 |

---

### 4.3 错误处理模块（Error Handler）

这是 Agent 的**核心智能模块**，利用 LLM 实现错误的自动诊断与修复。

#### 4.3.1 错误分类

| 错误类型 | 示例 | 可自动修复 |
|----------|------|------------|
| **依赖缺失** | `ModuleNotFoundError` | ✓ pip install |
| **变量未定义** | `NameError` | △ 需分析上下文 |
| **类型错误** | `TypeError` | △ LLM 建议修复 |
| **超时** | `TimeoutError` | ✓ 增加超时 |
| **内存不足** | `MemoryError` | ✗ 需人工优化 |

#### 4.3.2 LLM 错误分析 Prompt 设计

```python
ERROR_ANALYSIS_PROMPT = """
你是一个 Python 和 Jupyter Notebook 专家。请分析以下执行错误：

## 执行的代码
```python
{cell_source}
```

## 错误信息
```
{error_traceback}
```

## Notebook 上下文
- 文件名：{notebook_name}
- 单元格序号：{cell_index}
- 已定义变量：{defined_variables}

请提供：
1. 错误原因（一句话）
2. 修复方案
3. 修复后的代码（如果需要修改）
4. 是否可以自动修复（是/否）

输出 JSON 格式：
{{"reason": "", "solution": "", "fixed_code": "", "auto_fixable": true/false}}
"""
```

#### 4.3.3 自动修复流程

```
错误发生
    ↓
提取错误上下文（代码 + traceback + 变量）
    ↓
调用 LLM 分析
    ↓
解析 LLM 响应
    ↓
┌─ auto_fixable = true
│      ↓
│   应用修复代码
│      ↓
│   重新执行该单元格
│      ↓
│   ┌─ 成功 → 继续
│   └─ 失败 → 记录，进入人工处理
│
└─ auto_fixable = false
       ↓
    记录错误与建议
       ↓
    生成错误报告
       ↓
    终止或跳过（根据配置）
```

---

### 4.4 报告生成模块（Report Generator）

#### 4.4.1 HTML 导出

```python
from nbconvert import HTMLExporter
from nbconvert.preprocessors import TagRemovePreprocessor

def generate_html_report(notebook, output_path, hide_code=False):
    """生成 HTML 报告"""
    html_exporter = HTMLExporter()
    html_exporter.template_name = 'classic'  # 或 'lab'
    
    if hide_code:
        # 隐藏代码，只显示输出
        html_exporter.exclude_input = True
    
    body, resources = html_exporter.from_notebook_node(notebook)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(body)
    
    return output_path
```

#### 4.4.2 报告增强

| 增强项 | 描述 |
|--------|------|
| **执行摘要** | 总耗时、成功/失败单元格数 |
| **错误高亮** | 失败单元格红色标记 |
| **参数展示** | 显示本次执行的参数 |
| **执行时间** | 每个单元格的执行时间 |
| **资源使用** | 内存/CPU 使用峰值 |

---

## 五、Agent 编排设计

### 5.1 状态机模型

```
    ┌─────────┐
    │  INIT   │ ──────→ 初始化资源
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ PRECHECK│ ──────→ 预检查（失败则终止）
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │EXECUTING│ ◄─────┐ 执行中
    └────┬────┘       │
         │            │
    ┌────▼────┐       │
    │  ERROR  │ ──────┘ 错误修复后重试
    └────┬────┘
         │（无法修复）
         ▼
    ┌─────────┐
    │ FAILED  │ ──────→ 生成错误报告
    └─────────┘
         
    ┌─────────┐
    │COMPLETED│ ──────→ 生成成功报告
    └─────────┘
```

### 5.2 配置项设计

```python
@dataclass
class AgentConfig:
    # 执行配置
    timeout_per_cell: int = 300          # 单元格超时（秒）
    max_retries: int = 3                  # 最大重试次数
    continue_on_error: bool = False       # 错误时是否继续
    
    # LLM 配置
    llm_provider: str = "openai"          # openai / ollama / azure
    llm_model: str = "gpt-4"              # 模型名称
    enable_auto_fix: bool = True          # 是否启用自动修复
    
    # 输出配置
    output_dir: str = "./output"          # 输出目录
    generate_html: bool = True            # 是否生成 HTML
    hide_code_in_report: bool = False     # 报告中是否隐藏代码
    
    # 通知配置
    notify_on_complete: bool = False      # 完成后通知
    notify_webhook: str = None            # Webhook URL
```

---

## 六、使用方式设计

### 6.1 CLI 接口

```bash
# 基本执行
nb-agent run notebook.ipynb

# 带参数执行
nb-agent run notebook.ipynb \
  --param data_path=/data/train.csv \
  --param epochs=10

# 指定输出
nb-agent run notebook.ipynb \
  --output ./results/report.html \
  --hide-code

# 使用本地 LLM
nb-agent run notebook.ipynb \
  --llm-provider ollama \
  --llm-model codellama
```

### 6.2 Python API

```python
from nb_agent import NotebookAgent

agent = NotebookAgent(
    llm_provider="openai",
    enable_auto_fix=True,
)

result = agent.execute(
    notebook_path="analysis.ipynb",
    parameters={
        "data_path": "/data/train.csv",
        "epochs": 10,
    },
    output_html="report.html",
)

if result.success:
    print(f"Report: {result.html_path}")
else:
    print(f"Failed: {result.error_summary}")
```

### 6.3 API 服务

```
POST /api/execute
{
    "notebook_path": "analysis.ipynb",
    "parameters": {"epochs": 10},
    "options": {
        "generate_html": true,
        "enable_auto_fix": true
    }
}

Response:
{
    "task_id": "xxx-xxx",
    "status": "running"
}

GET /api/status/{task_id}
{
    "status": "completed",
    "html_url": "/reports/xxx.html",
    "execution_time": 120.5,
    "cells_executed": 15,
    "cells_failed": 0
}
```

---

## 七、扩展能力

### 7.1 批量执行

```python
# 参数网格搜索
param_grid = {
    "learning_rate": [0.001, 0.01, 0.1],
    "batch_size": [32, 64, 128],
}

agent.batch_execute(
    notebook_path="train.ipynb",
    param_grid=param_grid,
    parallel=4,  # 并行数
)
```

### 7.2 定时调度

```python
# 集成 APScheduler 或 Celery
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    agent.execute,
    'cron',
    hour=2,  # 每天凌晨 2 点执行
    kwargs={'notebook_path': 'daily_report.ipynb'}
)
```

### 7.3 执行沙箱

```python
# Docker 隔离执行
agent.execute(
    notebook_path="untrusted.ipynb",
    sandbox={
        "type": "docker",
        "image": "python:3.11",
        "memory_limit": "4g",
        "cpu_limit": 2,
    }
)
```

---

## 八、总结

### 8.1 架构优势

| 特性 | 描述 |
|------|------|
| **智能化** | LLM 驱动的错误分析与修复 |
| **自动化** | 一键执行，无需人工干预 |
| **可观测** | 完整的执行日志与报告 |
| **可扩展** | 支持批量、定时、API 调用 |
| **安全性** | 支持沙箱隔离执行 |

### 8.2 技术栈总结

```
执行层：papermill + nbclient + nbconvert
智能层：LLM (GPT-4 / CodeLlama)
接口层：CLI (Click) + API (FastAPI)
调度层：APScheduler / Celery（可选）
隔离层：Docker（可选）
```

### 8.3 适用场景

- 数据分析流水线自动化
- 机器学习实验批量运行
- 定时报告生成
- CI/CD 中的 Notebook 测试
- 教学环境的作业批改
