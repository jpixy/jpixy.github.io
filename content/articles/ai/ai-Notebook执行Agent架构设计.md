+++
title = "Notebook优化Agent架构设计"
date = 2025-01-13
description = "设计一个AI工具，将含有人工介入指令的Notebook优化为可一键执行的版本，并生成HTML报告"
[taxonomies]
tags = ["ai", "agent", "jupyter", "automation", "llm"]
+++

# Notebook 优化 Agent 架构设计

---

## 一、背景与痛点

### 1.1 问题场景

很多 Jupyter Notebook 无法通过 papermill 或 nbclient **一键执行到底**，原因是开发者在其中写入了需要人工介入的操作指令。

**典型问题 Notebook 示例：**

| Cell 类型 | 内容 | 问题 |
|-----------|------|------|
| Markdown | "请打开终端，执行 `pip install torch`" | 需要人工操作 |
| Code | `import torch` | 依赖上一步手动安装 |
| Markdown | "请在 config/ 目录下创建 settings.yaml" | 需要人工操作 |
| Code | `config = yaml.load(open('config/settings.yaml'))` | 依赖上一步手动创建 |

**执行结果**：即使使用 papermill，也会因为缺少依赖或文件而失败。

### 1.2 问题根源

| 根源 | 说明 |
|------|------|
| **指令与代码分离** | 操作写在 Markdown，代码在 Code Cell |
| **假设人工参与** | 开发者默认有人会按步骤操作 |
| **缺乏自动化意识** | 未考虑 CI/CD 或批量执行场景 |

### 1.3 我们的目标

设计一个 **AI 优化工具**，实现：

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  原始 Notebook   │  ────▶  │  优化后 Notebook │  ────▶  │   HTML 报告     │
│  (无法一键执行)   │   AI    │  (可一键执行)     │ 执行    │   (执行结果)    │
└─────────────────┘  优化    └─────────────────┘         └─────────────────┘
```

**核心思路**：不是让 AI 去执行人工操作，而是让 AI **改写 Notebook**，将人工指令转换为等价的可执行代码。

---

## 二、转换策略

### 2.1 转换规则

| 原始内容 | 转换后 | 说明 |
|----------|--------|------|
| Markdown: "请执行 `pip install torch`" | Code: `!pip install torch` | 终端命令转 magic command |
| Markdown: "请创建 config.yaml，内容如下..." | Code: Python 写文件代码 | 文件操作转代码 |
| Markdown: "请下载模型到 ./models/" | Code: `wget` 或 `requests` 下载 | 下载转代码 |
| Markdown: "请设置环境变量 API_KEY" | Code: `os.environ['API_KEY'] = ...` | 环境变量转代码 |

### 2.2 转换示例

**原始 Notebook：**

```
[Cell 1 - Markdown]
# 环境准备
请执行以下命令安装依赖：
pip install torch transformers

[Cell 2 - Code]
import torch
from transformers import AutoModel

[Cell 3 - Markdown]
请在 config/ 目录下创建 settings.yaml，内容如下：
model_name: bert-base
batch_size: 32

[Cell 4 - Code]
import yaml
config = yaml.safe_load(open('config/settings.yaml'))
```

**优化后 Notebook：**

```
[Cell 1 - Code]  ← 新增：自动安装依赖
!pip install torch transformers -q

[Cell 2 - Code]
import torch
from transformers import AutoModel

[Cell 3 - Code]  ← 改写：自动创建配置文件
import os
os.makedirs('config', exist_ok=True)
with open('config/settings.yaml', 'w') as f:
    f.write('''model_name: bert-base
batch_size: 32
''')

[Cell 4 - Code]
import yaml
config = yaml.safe_load(open('config/settings.yaml'))
```

**转换后效果**：可以通过 `papermill notebook.ipynb output.ipynb` 一键执行！

---

## 三、整体架构

### 3.1 系统流程图

```
┌─────────────────────────────────────────────────────────────┐
│                        INPUT                                 │
│                  原始 Notebook (.ipynb)                      │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 1: Analysis                          │
│                    分析 Notebook 结构                        │
│         识别所有 Markdown Cell 中的人工介入指令                │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 2: Transform                         │
│                    LLM 生成转换方案                          │
│         将人工指令转换为等价的可执行 Code Cell                 │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 3: Reconstruct                       │
│                    重构 Notebook                             │
│         插入/替换 Cell，生成优化后的 Notebook                  │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 4: Validate                          │
│                    验证优化结果                              │
│         尝试执行，检查是否能一键跑通                           │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 5: Execute & Export                  │
│                    执行并导出                                │
│         使用 papermill 执行，nbconvert 导出 HTML             │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        OUTPUT                                │
│         1. 优化后的 Notebook (.ipynb)                        │
│         2. 执行结果 HTML (.html)                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 模块架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Notebook Optimizer                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Analyzer   │  │ Transformer │  │    Reconstructor    │  │
│  │  (分析器)    │  │  (转换器)   │  │      (重构器)       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         ▼                ▼                     ▼             │
│    识别人工指令      LLM 生成代码         重构 Notebook        │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Validator  │  │  Executor   │  │      Exporter       │  │
│  │  (验证器)    │  │  (执行器)   │  │      (导出器)       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         ▼                ▼                     ▼             │
│    验证可执行性       执行 Notebook         导出 HTML         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 技术选型

| 模块 | 技术 | 说明 |
|------|------|------|
| **Notebook 解析** | nbformat | 读写 .ipynb 文件 |
| **指令识别** | 正则 + LLM | 双层检测 |
| **代码生成** | LLM (GPT-4/Claude) | 生成等价代码 |
| **Notebook 执行** | papermill | 参数化执行 |
| **HTML 导出** | nbconvert | 格式转换 |

---

## 四、核心模块详解

### 4.1 分析器 (Analyzer)

**职责**：扫描 Notebook，识别所有需要转换的人工指令。

#### 4.1.1 识别流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Notebook                             │
│                    加载 .ipynb 文件                          │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               For Each Cell in Notebook:                     │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
                    ┌─────────┴─────────┐
                    ▼                   ▼
              [Code Cell]         [Markdown Cell]
                    │                   │
                    ▼                   ▼
                  Skip            ┌───────────────┐
                                  │ Pattern Match │
                                  │ (快速筛选)     │
                                  └───────┬───────┘
                                          │
                                  ┌───────┴───────┐
                                  ▼               ▼
                            [Has Pattern]    [No Pattern]
                                  │               │
                                  ▼               ▼
                          ┌───────────────┐     Skip
                          │  LLM Confirm  │
                          │  (精确判断)    │
                          └───────┬───────┘
                                  ▼
                          ┌───────────────┐
                          │ Extract Info  │
                          │ 提取指令详情   │
                          └───────────────┘
```

#### 4.1.2 识别模式

| 模式 | 正则示例 | 匹配内容 |
|------|----------|----------|
| 终端命令 | `请(执行\|运行).*命令` | pip install, wget 等 |
| 文件创建 | `(创建\|新建).*文件` | 配置文件、数据文件 |
| 目录创建 | `(创建\|新建).*(目录\|文件夹)` | mkdir 操作 |
| 下载操作 | `(下载\|获取).*到` | 模型、数据下载 |
| 环境变量 | `(设置\|配置).*环境变量` | export 操作 |

#### 4.1.3 分析结果结构

```
{
  "cell_index": 3,
  "cell_type": "markdown",
  "instruction_type": "terminal_command",
  "original_content": "请执行以下命令安装依赖：\npip install torch",
  "extracted_command": "pip install torch",
  "suggested_action": "insert_code_cell_before"
}
```

---

### 4.2 转换器 (Transformer)

**职责**：将人工指令转换为等价的可执行代码。

#### 4.2.1 转换流程

```
┌─────────────────────────────────────────────────────────────┐
│                 Instruction from Analyzer                    │
│         {type: "file_create", path: "config.yaml", ...}     │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Determine Strategy                        │
│                    根据指令类型选择转换策略                    │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │  Terminal   │   │    File     │   │  Download   │
    │  Command    │   │  Operation  │   │  Operation  │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ !command    │   │ Python I/O  │   │ wget/urllib │
    │ or          │   │ Code        │   │ Code        │
    │ subprocess  │   │             │   │             │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Generate Code                         │
│              LLM 生成完整、可执行的代码片段                    │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Validate Syntax                          │
│                  验证生成代码的语法正确性                      │
└─────────────────────────────────────────────────────────────┘
```

#### 4.2.2 转换规则表

| 指令类型 | 转换策略 | 生成代码示例 |
|----------|----------|--------------|
| **pip install** | Magic command | `!pip install torch -q` |
| **系统命令** | subprocess | `subprocess.run(['wget', url])` |
| **创建文件** | Python I/O | `Path(path).write_text(content)` |
| **创建目录** | os/pathlib | `os.makedirs(path, exist_ok=True)` |
| **下载文件** | urllib/requests | `urllib.request.urlretrieve(url, path)` |
| **环境变量** | os.environ | `os.environ['KEY'] = 'value'` |

#### 4.2.3 LLM Prompt 设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Transformation Prompt                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Role: 你是一个 Notebook 优化专家                            │
│                                                              │
│  Task: 将以下人工操作指令转换为等价的 Python 代码             │
│                                                              │
│  Input:                                                      │
│  - 指令类型: {type}                                          │
│  - 原始内容: {content}                                       │
│  - 上下文: {context}                                         │
│                                                              │
│  Requirements:                                               │
│  1. 代码必须可直接执行                                        │
│  2. 包含必要的 import 语句                                    │
│  3. 添加错误处理                                             │
│  4. 添加执行状态输出                                          │
│                                                              │
│  Output: 可直接放入 Code Cell 的完整代码                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.3 重构器 (Reconstructor)

**职责**：根据转换结果，重构 Notebook 结构。

#### 4.3.1 重构策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| **Insert Before** | 在原 Cell 前插入新 Code Cell | 依赖安装、环境准备 |
| **Replace** | 替换原 Markdown Cell 为 Code Cell | 文件创建、配置生成 |
| **Merge** | 合并相邻的操作 Cell | 多个连续操作 |
| **Keep** | 保留原 Markdown（作为注释） | 说明性文字 |

#### 4.3.2 重构流程

```
┌─────────────────────────────────────────────────────────────┐
│                  Original Notebook Cells                     │
│              [Cell0, Cell1, Cell2, Cell3, ...]              │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Apply Transformations                       │
│                  应用所有转换操作                             │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Rebuild Cell List                           │
│                                                              │
│  Original: [MD, Code, MD, Code]                             │
│                ↓                                             │
│  Result:   [Code(new), Code, Code(converted), Code]         │
│                                                              │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Write New Notebook                          │
│             保存为 xxx_optimized.ipynb                       │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.4 验证器 (Validator)

**职责**：验证优化后的 Notebook 是否能成功执行。

#### 4.4.1 验证流程

```
┌─────────────────────────────────────────────────────────────┐
│               Optimized Notebook                             │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              STEP 1: Static Analysis                         │
│              静态检查：语法、import、依赖                      │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              STEP 2: Dry Run (Optional)                      │
│              试运行：在隔离环境中执行                          │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
                    ┌─────────┴─────────┐
                    ▼                   ▼
              [All Passed]         [Has Errors]
                    │                   │
                    ▼                   ▼
              ┌──────────┐        ┌──────────────┐
              │ Proceed  │        │ Report Error │
              │ to Exec  │        │ & Suggest    │
              └──────────┘        └──────────────┘
```

---

### 4.5 执行器与导出器

**执行器**：使用 papermill 执行优化后的 Notebook

**导出器**：使用 nbconvert 生成 HTML 报告

#### 执行导出流程

```
┌─────────────────────────────────────────────────────────────┐
│              Optimized Notebook (validated)                  │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    papermill execute                         │
│        papermill input.ipynb output.ipynb -p key value      │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
                    ┌─────────┴─────────┐
                    ▼                   ▼
              [Success]            [Failed]
                    │                   │
                    ▼                   ▼
┌─────────────────────────────┐  ┌─────────────────────────┐
│     nbconvert to HTML       │  │   Error Report          │
│  jupyter nbconvert --to html│  │   Include traceback     │
└─────────────────────────────┘  └─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                        OUTPUT                                │
│         1. xxx_optimized.ipynb (优化后的 Notebook)           │
│         2. xxx_output.ipynb (执行结果)                       │
│         3. xxx_report.html (HTML 报告)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 五、使用方式

### 5.1 CLI 接口

```bash
# 优化 Notebook（仅转换，不执行）
nb-optimizer optimize notebook.ipynb

# 优化并执行
nb-optimizer run notebook.ipynb

# 优化、执行并生成 HTML
nb-optimizer run notebook.ipynb --html output.html

# 指定输出文件名
nb-optimizer run notebook.ipynb -o notebook_optimized.ipynb

# 预览模式（显示将要做的更改，不实际修改）
nb-optimizer preview notebook.ipynb
```

### 5.2 Python API

```python
from nb_optimizer import NotebookOptimizer

optimizer = NotebookOptimizer(llm_provider="openai")

# 优化 Notebook
result = optimizer.optimize("analysis.ipynb")
print(f"Optimized: {result.output_notebook}")
print(f"Changes: {result.changes_count}")

# 优化并执行
result = optimizer.run(
    "analysis.ipynb",
    output_html="report.html",
    parameters={"epochs": 10}
)

print(f"Status: {result.status}")
print(f"HTML: {result.html_path}")
```

### 5.3 配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `llm_provider` | openai | LLM 提供商 |
| `preserve_markdown` | true | 保留原 Markdown 作为注释 |
| `auto_install_deps` | true | 自动添加依赖安装代码 |
| `validate_before_run` | true | 执行前验证 |
| `output_suffix` | _optimized | 输出文件名后缀 |

---

## 六、输出示例

### 6.1 优化报告

执行 `nb-optimizer preview notebook.ipynb` 输出：

| Cell | 原内容 | 操作 | 新内容 |
|------|--------|------|--------|
| #2 (MD) | "请执行 pip install torch" | INSERT_BEFORE | `!pip install torch -q` |
| #4 (MD) | "请创建 config.yaml..." | REPLACE | Python 写文件代码 |
| #6 (MD) | "请下载模型到..." | REPLACE | urllib 下载代码 |

**统计：**
- 检测到人工指令：3 处
- 插入新 Cell：1 个
- 替换 Cell：2 个

### 6.2 最终产出

| 文件 | 说明 |
|------|------|
| `notebook_optimized.ipynb` | 优化后的 Notebook，可一键执行 |
| `notebook_output.ipynb` | 执行后的 Notebook（含输出） |
| `notebook_report.html` | HTML 格式的执行报告 |

---

## 七、总结

### 7.1 核心价值

| 输入 | 处理 | 输出 |
|------|------|------|
| 无法一键执行的 Notebook | AI 识别 + 代码转换 | 可一键执行的 Notebook + HTML |

**本质**：**代码改写工具**，不是运行时执行工具。

### 7.2 技术路线

```
原始 Notebook
     │
     ▼ (分析)
识别人工指令
     │
     ▼ (转换)
LLM 生成等价代码
     │
     ▼ (重构)
生成优化后 Notebook
     │
     ▼ (执行)
papermill 一键执行
     │
     ▼ (导出)
nbconvert 生成 HTML
```

### 7.3 适用场景

- 遗留 Notebook 的自动化改造
- CI/CD 流水线集成
- 批量执行历史 Notebook
- 生成可复现的分析报告
