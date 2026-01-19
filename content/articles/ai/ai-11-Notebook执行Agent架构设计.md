+++
title = "11.Notebook执行Agent架构设计"
date = 2025-01-13
description = "基于LangGraph设计一个AI Agent，自动将无法一键执行的Notebook改写为可自动化执行的版本"
[taxonomies]
tags = ["ai", "agent", "jupyter", "langchain", "langgraph", "automation"]
+++

# Notebook 优化 Agent 架构设计

---

## 一、问题背景

### 1.1 痛点场景

许多 Jupyter Notebook 无法通过 `papermill` 或 `nbclient` **一键执行到底**。

**根本原因**：开发者在 Notebook 中写入了需要人工介入的操作指令。

| 问题类型 | 示例 | 后果 |
|----------|------|------|
| 人工安装依赖 | "请执行 pip install torch" | 自动执行时缺包报错 |
| 人工创建文件 | "请创建 config.yaml" | 代码找不到文件 |
| 人工下载数据 | "请下载模型到 ./models/" | 路径不存在 |
| 人工配置环境 | "请设置 API_KEY 环境变量" | 环境变量缺失 |

### 1.2 问题本质

```
开发者视角：Notebook 是交互式文档，默认有人参与
自动化视角：Notebook 是可执行脚本，需要无人值守
                     ↓
               GAP：人工指令无法自动执行
```

### 1.3 我们的目标

**设计一个 AI Agent，自动改写 Notebook，消除人工介入依赖。**

```
┌──────────────────┐                    ┌──────────────────┐
│   原始 Notebook   │                    │  优化后 Notebook  │
│  (无法一键执行)    │  ═══ AI 改写 ═══▶  │  (可一键执行)      │
│                  │                    │                  │
│  [MD] 请执行...   │                    │  [Code] !pip...  │
│  [Code] import   │                    │  [Code] import   │
│  [MD] 请创建...   │                    │  [Code] 写文件... │
└──────────────────┘                    └──────────────────┘
                                               │
                                               ▼
                                        ┌──────────────────┐
                                        │   HTML 执行报告   │
                                        └──────────────────┘
```

**核心思路**：
- ❌ 不是让 AI 去执行人工操作
- ✅ 而是让 AI **改写代码**，将人工指令转换为等价的可执行 Cell

---

## 二、解决方案概述

### 2.1 转换示例

| 原始 (Markdown) | 转换后 (Code) |
|-----------------|---------------|
| "请执行 `pip install torch`" | `!pip install torch -q` |
| "请创建 config.yaml，内容：..." | `Path('config.yaml').write_text(...)` |
| "请下载模型到 ./models/" | `urllib.request.urlretrieve(url, path)` |
| "请设置环境变量 API_KEY=xxx" | `os.environ['API_KEY'] = 'xxx'` |

### 2.2 核心挑战

单次转换往往不够，因为：

| 挑战 | 说明 |
|------|------|
| **隐式依赖** | 代码依赖的包，原 Notebook 没提到 |
| **转换错误** | LLM 生成的代码可能有语法错误 |
| **遗漏指令** | 某些人工指令没被识别 |
| **执行失败** | 转换后执行仍然报错 |

**解决方案**：**迭代优化** —— 不断尝试、执行、分析错误、修复，直到成功。

---

## 三、核心设计：迭代优化循环

### 3.1 设计理念

```
不是一次转换就结束，而是：

    转换 → 执行 → 失败 → 分析 → 修复 → 再执行 → ... → 成功
    
这是一个 Agent Loop（智能体循环）
```

### 3.2 迭代流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                         START                                    │
│                    输入：原始 Notebook                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     STEP 1: ANALYZE                              │
│                     分析 Notebook                                │
│            扫描所有 Cell，识别人工介入指令                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│                    OPTIMIZATION LOOP                             │
│                      (迭代优化循环)                               │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  STEP 2: TRANSFORM                        │  │
│  │                  LLM 生成转换代码                          │  │
│  │         将人工指令转换为等价的 Code Cell                    │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  STEP 3: REBUILD                          │  │
│  │                  重构 Notebook                            │  │
│  │         插入/替换 Cell，生成新版 Notebook                   │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  STEP 4: EXECUTE                          │  │
│  │                  执行 Notebook                            │  │
│  │         使用 papermill 执行，捕获结果                       │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                   │
│                    ┌─────────┴─────────┐                        │
│                    ▼                   ▼                        │
│              ┌──────────┐        ┌──────────┐                   │
│              │ SUCCESS  │        │  ERROR   │                   │
│              └────┬─────┘        └────┬─────┘                   │
│                   │                   │                         │
│                   │                   ▼                         │
│                   │    ┌───────────────────────────────────┐    │
│                   │    │        STEP 5: DIAGNOSE           │    │
│                   │    │        LLM 分析错误原因            │    │
│                   │    │        生成修复方案                │    │
│                   │    └───────────────┬───────────────────┘    │
│                   │                    │                        │
│                   │                    ▼                        │
│                   │    ┌───────────────────────────────────┐    │
│                   │    │        STEP 6: FIX                │    │
│                   │    │        应用修复                    │    │
│                   │    │        更新 Notebook              │    │
│                   │    └───────────────┬───────────────────┘    │
│                   │                    │                        │
│                   │         ┌──────────┴──────────┐             │
│                   │         ▼                     ▼             │
│                   │   [retry < max]         [retry >= max]      │
│                   │         │                     │             │
│                   │         │                     ▼             │
│                   │         │              ┌──────────────┐     │
│                   │         │              │  GIVE UP     │     │
│                   │         │              │  输出错误报告  │     │
│                   │         │              └──────────────┘     │
│                   │         │                                   │
│                   │         └──────────────────┐                │
│                   │                            │                │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─┘
                   │                            │
                   │         ┌──────────────────┘
                   │         │ (loop back)
                   ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│                          END                                     │
│                       输出结果                                   │
│                                                                  │
│  成功：                         失败：                           │
│  - optimized.ipynb (优化版)     - error_report.md               │
│  - output.ipynb (执行结果)      - 最后尝试的 notebook            │
│  - report.html (HTML报告)       - 所有尝试记录                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 迭代示例

```
Round 1: 初始转换
├─ 识别到 3 条人工指令
├─ 转换为 Code Cell
├─ 执行...
└─ ❌ 失败: ModuleNotFoundError: No module named 'pandas'
        (原 Notebook 未提及，但代码实际使用了)

Round 2: 修复依赖
├─ LLM 分析: 代码 import pandas，但未安装
├─ 修复: 在开头插入 !pip install pandas
├─ 执行...
└─ ❌ 失败: FileNotFoundError: data/train.csv

Round 3: 修复文件
├─ LLM 分析: 代码读取 data/train.csv
├─ 检查 Markdown: 发现 "请从 xxx 下载数据"
├─ 修复: 添加下载代码
├─ 执行...
└─ ✅ 成功! 所有 Cell 执行完成

输出:
├─ notebook_optimized.ipynb
├─ notebook_output.ipynb  
└─ report.html
```

---

## 四、技术架构

### 4.1 为什么需要 LangGraph？

迭代优化需要以下能力：

| 需求 | 普通代码 | LangGraph |
|------|----------|-----------|
| 状态管理 | 手动维护变量 | 内置 State |
| 循环控制 | while/for | 图的边(Edge)自然支持 |
| 条件分支 | if/else | 条件路由 |
| 错误记忆 | 手动记录 | State 持久化 |
| LLM 调用 | 手写 API | 集成 LangChain |
| 工具调用 | 手写函数 | Tool 抽象 |

**LangGraph 是专为复杂 Agent 工作流设计的框架。**

### 4.2 LangGraph 状态机设计

```
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph Workflow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  State (状态对象):                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  {                                                       │    │
│  │    "notebook": NotebookObject,    // 当前 Notebook       │    │
│  │    "version": 1,                  // 版本号              │    │
│  │    "instructions": [...],         // 识别到的人工指令     │    │
│  │    "errors": [],                  // 错误历史            │    │
│  │    "attempts": [],                // 修复尝试记录        │    │
│  │    "status": "pending"            // 状态               │    │
│  │  }                                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Nodes (节点):                                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ analyze │ │transform│ │ rebuild │ │ execute │ │   fix   │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│                                                                  │
│  Edges (边):                                                     │
│  analyze ─────────────────────────────────▶ transform           │
│  transform ───────────────────────────────▶ rebuild             │
│  rebuild ─────────────────────────────────▶ execute             │
│  execute ──── [success] ──────────────────▶ END                 │
│  execute ──── [error] ────────────────────▶ fix                 │
│  fix ──────── [retry < max] ──────────────▶ transform           │
│  fix ──────── [retry >= max] ─────────────▶ END                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 核心 Tools 设计

| Tool | 功能 | 输入 | 输出 |
|------|------|------|------|
| `analyze_notebook` | 扫描识别人工指令 | notebook | instructions[] |
| `transform_instruction` | 将指令转换为代码 | instruction, context | code_cell |
| `rebuild_notebook` | 重构 Notebook 结构 | notebook, changes | new_notebook |
| `execute_notebook` | 执行 Notebook | notebook_path | result / error |
| `diagnose_error` | 分析错误原因 | error, notebook | diagnosis |
| `generate_fix` | 生成修复方案 | diagnosis, attempts | fix_plan |
| `apply_fix` | 应用修复 | notebook, fix_plan | new_notebook |

### 4.4 记忆机制

**关键：让 LLM 知道之前尝试过什么，避免重复失败。**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Memory Context                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  传递给 LLM 的上下文：                                           │
│                                                                  │
│  1. 当前错误信息                                                 │
│     └─ Error: ModuleNotFoundError: pandas                       │
│                                                                  │
│  2. 相关代码片段                                                 │
│     └─ Cell[5]: import pandas as pd                             │
│                                                                  │
│  3. 已尝试的修复（避免重复）                                      │
│     └─ Attempt 1: 添加 !pip install numpy  → 仍然失败            │
│     └─ Attempt 2: 添加 !pip install np     → 仍然失败            │
│                                                                  │
│  4. Notebook 上下文                                              │
│     └─ 其他 Cell 的 import 语句                                  │
│     └─ Markdown 中提到的相关信息                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、模块详解

### 5.1 分析模块 (Analyzer)

**职责**：识别 Notebook 中所有需要转换的人工指令。

**识别流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│                   Analyze Notebook                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               For each Markdown Cell:                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            Layer 1: Pattern Matching (快速筛选)                   │
│                                                                  │
│  Patterns:                                                       │
│  - "请(执行|运行|输入|创建|下载|设置)..."                         │
│  - "pip install|wget|curl|mkdir|chmod..."                       │
│  - "```bash" or "```shell"                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   ▼                   ▼
             [匹配成功]            [未匹配]
                   │                   │
                   ▼                   ▼
┌──────────────────────────┐         Skip
│  Layer 2: LLM Confirm    │
│  LLM 确认是否为人工指令   │
│  提取具体操作内容         │
└──────────────────────────┘
```

**输出示例**：

```json
{
  "instructions": [
    {
      "cell_index": 2,
      "type": "terminal_command",
      "content": "pip install torch transformers",
      "action": "insert_before"
    },
    {
      "cell_index": 5,
      "type": "file_create",
      "path": "config/settings.yaml",
      "content": "model: bert\nbatch_size: 32",
      "action": "replace"
    }
  ]
}
```

### 5.2 转换模块 (Transformer)

**职责**：将人工指令转换为等价的可执行代码。

**转换规则**：

| 指令类型 | 转换策略 | 示例输出 |
|----------|----------|----------|
| pip install | Magic command | `!pip install torch -q` |
| 系统命令 | subprocess | `subprocess.run([...])` |
| 创建文件 | pathlib | `Path(p).write_text(c)` |
| 创建目录 | os | `os.makedirs(p, exist_ok=True)` |
| 下载文件 | urllib | `urllib.request.urlretrieve(u,p)` |
| 环境变量 | os.environ | `os.environ['K'] = 'V'` |

**LLM Prompt 设计**：

```
你是 Notebook 优化专家。

任务：将人工操作指令转换为可执行的 Python 代码。

输入：
- 指令类型：{type}
- 原始内容：{content}
- 上下文：{context}

要求：
1. 代码可直接在 Jupyter Cell 中执行
2. 包含必要的 import
3. 包含错误处理
4. 执行后打印状态

输出：完整的 Python 代码
```

### 5.3 诊断与修复模块 (Diagnoser & Fixer)

**职责**：分析执行错误，生成修复方案。

**诊断流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│                     Execution Error                              │
│         ModuleNotFoundError: No module named 'pandas'           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Error Classification                          │
│                                                                  │
│  - ModuleNotFoundError  → 缺少依赖                               │
│  - FileNotFoundError    → 缺少文件                               │
│  - SyntaxError          → 代码语法错误                           │
│  - KeyError             → 缺少配置                               │
│  - NameError            → 变量未定义                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Diagnosis                                 │
│                                                                  │
│  Input:                                                          │
│  - 错误类型 + traceback                                          │
│  - 相关代码片段                                                  │
│  - 已尝试的修复（避免重复）                                       │
│                                                                  │
│  Output:                                                         │
│  - 错误原因分析                                                  │
│  - 修复方案                                                      │
│  - 修复代码                                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Apply Fix                                     │
│                                                                  │
│  修复类型：                                                      │
│  - INSERT: 在某位置插入新 Cell                                   │
│  - MODIFY: 修改现有 Cell 代码                                    │
│  - DELETE: 删除有问题的 Cell                                     │
└─────────────────────────────────────────────────────────────────┘
```

**修复示例**：

| 错误 | 诊断 | 修复 |
|------|------|------|
| `ModuleNotFoundError: pandas` | 缺少 pandas 包 | 插入 `!pip install pandas` |
| `FileNotFoundError: data.csv` | 文件不存在 | 检查是否有下载指令，添加下载代码 |
| `SyntaxError` in Cell 5 | 生成代码有语法错误 | 重新让 LLM 生成 |

---

## 六、技术选型

| 组件 | 技术 | 说明 |
|------|------|------|
| **Agent 框架** | LangGraph | 状态机 + 循环 + 条件路由 |
| **LLM 接口** | LangChain | 统一的模型调用接口 |
| **LLM 模型** | GPT-4 / Claude | 代码生成和错误分析 |
| **Notebook 解析** | nbformat | 读写 .ipynb 文件 |
| **Notebook 执行** | papermill | 参数化批量执行 |
| **HTML 导出** | nbconvert | 转换为 HTML 报告 |

---

## 七、使用方式

### 7.1 CLI

```bash
# 优化并执行，输出 HTML
nb-optimizer run notebook.ipynb --output report.html

# 仅优化，不执行
nb-optimizer optimize notebook.ipynb

# 预览模式，显示将要做的修改
nb-optimizer preview notebook.ipynb

# 指定最大重试次数
nb-optimizer run notebook.ipynb --max-retries 10

# 使用本地 LLM
nb-optimizer run notebook.ipynb --llm ollama:codellama
```

### 7.2 Python API

```python
from nb_optimizer import NotebookOptimizer

optimizer = NotebookOptimizer(
    llm="openai:gpt-4",
    max_retries=5
)

result = optimizer.run("analysis.ipynb")

if result.success:
    print(f"优化成功！")
    print(f"优化版: {result.optimized_notebook}")
    print(f"HTML: {result.html_report}")
    print(f"尝试次数: {result.attempts}")
else:
    print(f"优化失败")
    print(f"最后错误: {result.last_error}")
    print(f"尝试记录: {result.attempt_log}")
```

### 7.3 配置

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `max_retries` | 5 | 最大重试次数 |
| `llm` | openai:gpt-4 | LLM 模型 |
| `timeout_per_cell` | 300s | 单元格执行超时 |
| `preserve_markdown` | true | 保留原 Markdown 作为注释 |

---

## 八、输出产物

### 8.1 成功时

| 文件 | 说明 |
|------|------|
| `xxx_optimized.ipynb` | 优化后的 Notebook，可一键执行 |
| `xxx_executed.ipynb` | 执行后的 Notebook（含输出） |
| `xxx_report.html` | HTML 格式的执行报告 |
| `optimization_log.json` | 优化过程日志 |

### 8.2 失败时

| 文件 | 说明 |
|------|------|
| `xxx_last_attempt.ipynb` | 最后一次尝试的 Notebook |
| `error_report.md` | 错误报告和建议 |
| `optimization_log.json` | 所有尝试的详细记录 |

---

## 九、总结

### 9.1 核心设计要点

| 要点 | 说明 |
|------|------|
| **改写而非执行** | 将人工指令转换为代码，而不是代替人执行 |
| **迭代优化** | 不断尝试，直到成功或达到上限 |
| **LangGraph 驱动** | 利用状态机实现复杂的循环和分支 |
| **记忆机制** | 记录失败尝试，避免重复 |

### 9.2 价值

```
输入：无法自动执行的 Notebook
          │
          │ (AI 迭代优化)
          ▼
输出：可一键执行的 Notebook + HTML 报告
```

### 9.3 适用场景

- 遗留 Notebook 自动化改造
- CI/CD 流水线集成
- 批量执行历史 Notebook
- 自动化报告生成
