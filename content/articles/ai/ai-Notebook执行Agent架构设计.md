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
| **Markdown 中的人工指令需手动执行** | **Agent 自动识别并执行** |

### 1.2 核心难题：人工介入指令

很多开发者在 Notebook 中会写入需要**人工介入**的操作指令，例如：

```markdown
# 准备工作
请打开终端，执行以下命令安装依赖：
```bash
pip install torch transformers
```

# 数据准备
请到 `/data/raw/` 目录下新建 `config.yaml` 文件，内容如下：
...

# 模型下载
请手动从 HuggingFace 下载模型到 `./models/` 目录
```

**这些指令阻碍了 Notebook 的自动化执行！**

| 指令类型 | 示例 | 传统处理 |
|----------|------|----------|
| 终端命令 | "请执行 `pip install xxx`" | 手动复制到终端 |
| 文件操作 | "请创建 config.yaml" | 手动创建文件 |
| 目录操作 | "请新建 data 目录" | 手动创建目录 |
| 下载操作 | "请下载模型到 xxx" | 手动下载 |
| 环境配置 | "请设置环境变量 API_KEY" | 手动 export |

**本 Agent 的核心目标之一：自动识别并执行这些人工指令，实现真正的"一键到底"！**

### 1.3 核心能力

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
│  ✓ 人工指令自动识别（Human Instruction Detection）  🆕   │
│  ✓ 人工指令自动执行（Human Instruction Execution）  🆕   │
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
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  预检查模块   │    │   执行引擎模块    │    │  后处理模块   │
│  - 依赖检查  │    │  - nbclient      │    │  - HTML 导出 │
│  - 参数验证  │    │  - papermill     │    │  - 日志归档  │
│  - 环境准备  │    │  - 超时控制      │    │  - 结果通知  │
└──────────────┘    └────────┬─────────┘    └──────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                                 ▼
┌────────────────────────┐        ┌────────────────────────┐
│   人工指令处理模块 🆕   │        │     错误处理模块        │
│  ┌──────────────────┐  │        │  ┌──────────────────┐  │
│  │  指令检测器       │  │        │  │  LLM 错误分析     │  │
│  │  (LLM 解析)      │  │        │  │  错误诊断         │  │
│  ├──────────────────┤  │        │  │  修复建议         │  │
│  │  指令执行器       │  │        │  │  自动重试         │  │
│  │  - 终端命令      │  │        │  └──────────────────┘  │
│  │  - 文件操作      │  │        └────────────────────────┘
│  │  - 目录操作      │  │
│  │  - 下载任务      │  │
│  │  - 环境变量      │  │
│  └──────────────────┘  │
└────────────────────────┘
```

### 3.2 核心流程

```
1. 接收执行请求（Notebook 路径 + 参数）
       ↓
2. 预检查（依赖、参数、环境）
       ↓
3. 预扫描：人工指令检测 🆕
       ↓
   ┌─ 发现人工指令 → 提取并预执行
   │     ├─ 终端命令：自动执行
   │     ├─ 文件创建：自动创建
   │     ├─ 下载任务：自动下载
   │     └─ 环境配置：自动设置
   │
   └─ 无人工指令 → 继续
       ↓
4. 参数注入（papermill 注入参数单元格）
       ↓
5. 逐单元格执行（nbclient）
       ↓
   ┌─ Code Cell → 执行代码
   │     ├─ 成功 → 继续
   │     └─ 失败 → 错误处理模块
   │
   └─ Markdown Cell → 检查是否含人工指令 🆕
         ├─ 有指令 → 解析并执行
         └─ 无指令 → 跳过
       ↓
6. 执行完成
       ↓
7. 生成 HTML 报告（含指令执行记录）
       ↓
8. 返回结果（成功/失败 + 报告路径 + 指令执行摘要）
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

### 4.4 人工指令处理模块（Human Instruction Handler）🆕

这是本 Agent 的**核心创新模块**，解决 Notebook 中人工介入指令的自动化执行问题。

#### 4.4.1 问题场景分析

开发者常在 Markdown 单元格中写入需要手动执行的指令：

| 指令类型 | 典型表述 | 需要的操作 |
|----------|----------|------------|
| **终端命令** | "请执行"、"运行以下命令"、"在终端中输入" | 执行 shell 命令 |
| **文件创建** | "请创建文件"、"新建配置文件"、"将以下内容保存到" | 写入文件 |
| **目录操作** | "请创建目录"、"新建文件夹" | 创建目录 |
| **下载任务** | "请下载"、"从 xxx 下载到" | wget/curl 下载 |
| **环境变量** | "请设置环境变量"、"export XXX" | 设置 env |
| **权限操作** | "请修改权限"、"chmod" | 权限变更 |

#### 4.4.2 技术架构

```
┌─────────────────────────────────────────────────────────┐
│               Human Instruction Handler                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ 指令检测器   │ →  │ 指令解析器   │ →  │ 指令执行器   │  │
│  │ (Detector)  │    │ (Parser)    │    │ (Executor)  │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│        ↓                  ↓                  ↓          │
│   扫描 Markdown      LLM 结构化提取      安全执行指令      │
│   识别指令模式        生成执行计划        记录执行结果      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 4.4.3 指令检测器（Instruction Detector）

**目标**：识别 Markdown 单元格中是否包含需要人工执行的指令。

**检测策略**：规则 + LLM 双层检测

```python
# 第一层：规则快速筛选
INSTRUCTION_PATTERNS = [
    r'请(执行|运行|输入|创建|新建|下载|设置)',
    r'(打开|进入)(终端|命令行|shell)',
    r'(复制|粘贴)(以下|下面)(命令|代码)',
    r'```(bash|shell|sh)\n',
    r'(mkdir|cd|pip|npm|wget|curl|chmod|export)\s+',
    r'请.*到.*目录',
    r'请.*保存(到|为)',
]

def quick_detect(markdown_text):
    """快速规则检测"""
    for pattern in INSTRUCTION_PATTERNS:
        if re.search(pattern, markdown_text, re.IGNORECASE):
            return True
    return False
```

**第二层**：LLM 精确判断

```python
DETECTION_PROMPT = """
分析以下 Markdown 内容，判断是否包含需要用户手动执行的操作指令。

## Markdown 内容
{markdown_content}

## 判断标准
- 需要在终端执行的命令
- 需要创建/修改文件的操作
- 需要下载资源的操作
- 需要配置环境的操作

## 输出格式（JSON）
{{
  "has_instruction": true/false,
  "instruction_types": ["terminal", "file", "download", ...],
  "confidence": 0.0-1.0
}}
"""
```

#### 4.4.4 指令解析器（Instruction Parser）

**目标**：将自然语言指令转换为结构化的可执行动作。

**LLM 解析 Prompt**：

```python
PARSING_PROMPT = """
你是一个专业的指令解析器。请将以下 Markdown 中的人工操作指令提取为结构化的执行计划。

## Markdown 内容
{markdown_content}

## 上下文信息
- 工作目录：{working_dir}
- 当前环境：{environment}
- Notebook 路径：{notebook_path}

## 输出格式（JSON 数组）
[
  {{
    "type": "terminal|file_create|file_write|directory|download|env_var|permission",
    "description": "操作描述",
    "command": "具体命令（如适用）",
    "path": "文件/目录路径（如适用）",
    "content": "文件内容（如适用）",
    "url": "下载链接（如适用）",
    "env_name": "环境变量名（如适用）",
    "env_value": "环境变量值（如适用）",
    "risk_level": "low|medium|high",
    "requires_confirmation": true/false
  }}
]

## 注意事项
1. 相对路径基于工作目录解析
2. 识别代码块中的具体命令
3. 提取文件内容时保持格式
4. 评估操作风险等级
"""
```

**解析结果示例**：

```python
# 输入 Markdown：
"""
# 环境准备
请执行以下命令安装依赖：
```bash
pip install torch transformers datasets
```

然后在 `config/` 目录下创建 `settings.yaml`，内容如下：
```yaml
model_name: bert-base-chinese
batch_size: 32
```
"""

# 解析输出：
[
    {
        "type": "terminal",
        "description": "安装 Python 依赖包",
        "command": "pip install torch transformers datasets",
        "risk_level": "low",
        "requires_confirmation": False
    },
    {
        "type": "directory",
        "description": "创建配置目录",
        "path": "config/",
        "risk_level": "low",
        "requires_confirmation": False
    },
    {
        "type": "file_write",
        "description": "创建配置文件",
        "path": "config/settings.yaml",
        "content": "model_name: bert-base-chinese\nbatch_size: 32\n",
        "risk_level": "low",
        "requires_confirmation": False
    }
]
```

#### 4.4.5 指令执行器（Instruction Executor）

**执行器架构**：

```python
class InstructionExecutor:
    """指令执行器 - 负责安全执行各类操作"""
    
    def __init__(self, working_dir, config):
        self.working_dir = working_dir
        self.config = config
        self.execution_log = []
        
        # 注册执行器
        self.executors = {
            "terminal": self._execute_terminal,
            "file_write": self._execute_file_write,
            "file_create": self._execute_file_create,
            "directory": self._execute_directory,
            "download": self._execute_download,
            "env_var": self._execute_env_var,
            "permission": self._execute_permission,
        }
    
    def execute(self, instruction):
        """执行单条指令"""
        executor = self.executors.get(instruction["type"])
        if not executor:
            raise ValueError(f"Unknown instruction type: {instruction['type']}")
        
        # 安全检查
        if not self._safety_check(instruction):
            raise SecurityError(f"Instruction blocked: {instruction}")
        
        # 确认检查（高风险操作）
        if instruction.get("requires_confirmation") and self.config.require_confirmation:
            if not self._get_confirmation(instruction):
                return {"status": "skipped", "reason": "user_declined"}
        
        # 执行
        result = executor(instruction)
        self.execution_log.append({
            "instruction": instruction,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
```

**各类型执行器实现要点**：

| 类型 | 实现方式 | 安全考虑 |
|------|----------|----------|
| **terminal** | `subprocess.run()` | 命令白名单、超时、无 shell 注入 |
| **file_write** | `pathlib.Path.write_text()` | 路径校验、防止覆盖、备份原文件 |
| **directory** | `os.makedirs()` | 权限检查、路径规范化 |
| **download** | `httpx` / `aiohttp` | URL 白名单、大小限制、校验和 |
| **env_var** | `os.environ[]` | 敏感变量保护、作用域隔离 |
| **permission** | `os.chmod()` | 仅降权、禁止提权 |

#### 4.4.6 安全机制设计

**安全是人工指令自动执行的核心挑战！**

```
┌─────────────────────────────────────────────────────────┐
│                    安全防护层                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 命令白名单   │  │ 路径沙箱     │  │ 资源限制    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 危险模式检测 │  │ 人工确认     │  │ 回滚机制    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

**1. 命令白名单**

```python
SAFE_COMMANDS = {
    # 包管理
    "pip", "pip3", "conda", "npm", "yarn",
    # 文件操作
    "mkdir", "touch", "cp", "mv", "cat", "echo",
    # 下载
    "wget", "curl",
    # 环境
    "export", "source",
    # 版本控制
    "git",
}

DANGEROUS_PATTERNS = [
    r"rm\s+-rf",           # 危险删除
    r"sudo\s+",            # 提权
    r"chmod\s+777",        # 过度权限
    r">\s*/etc/",          # 系统文件覆盖
    r"\|\s*sh",            # 管道执行
    r"curl.*\|\s*bash",    # 远程脚本执行
]
```

**2. 路径沙箱**

```python
def validate_path(path, working_dir):
    """确保路径在工作目录内"""
    resolved = Path(path).resolve()
    sandbox = Path(working_dir).resolve()
    
    if not str(resolved).startswith(str(sandbox)):
        raise SecurityError(f"Path escapes sandbox: {path}")
    
    return resolved
```

**3. 风险分级与确认**

| 风险等级 | 操作类型 | 处理方式 |
|----------|----------|----------|
| **Low** | pip install、mkdir、文件创建 | 自动执行 |
| **Medium** | 文件覆盖、下载大文件 | 记录警告 |
| **High** | 删除操作、权限变更、系统配置 | 需人工确认 |
| **Blocked** | rm -rf、sudo、系统目录写入 | 拒绝执行 |

**4. 执行回滚**

```python
class ExecutionTransaction:
    """支持回滚的执行事务"""
    
    def __init__(self):
        self.rollback_actions = []
    
    def execute_with_rollback(self, instruction, executor):
        # 记录回滚动作
        if instruction["type"] == "file_write":
            original = self._backup_if_exists(instruction["path"])
            self.rollback_actions.append(
                ("restore_file", instruction["path"], original)
            )
        
        try:
            return executor(instruction)
        except Exception as e:
            self.rollback()
            raise
    
    def rollback(self):
        for action in reversed(self.rollback_actions):
            self._execute_rollback(action)
```

#### 4.4.7 执行报告增强

执行完成后，报告中包含指令执行摘要：

```
┌─────────────────────────────────────────────────────────┐
│              人工指令执行摘要                             │
├─────────────────────────────────────────────────────────┤
│  总计检测指令：5 条                                       │
│  成功执行：4 条                                          │
│  跳过执行：1 条（需人工确认）                              │
│  执行失败：0 条                                          │
├─────────────────────────────────────────────────────────┤
│  详细记录：                                              │
│  ✓ [terminal] pip install torch transformers (3.2s)     │
│  ✓ [directory] 创建 config/ 目录                        │
│  ✓ [file] 创建 config/settings.yaml                     │
│  ✓ [download] 下载 model.bin (125MB, 45s)              │
│  ⊘ [permission] chmod 755 - 需确认，已跳过               │
└─────────────────────────────────────────────────────────┘
```

---

### 4.5 报告生成模块（Report Generator）

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
    
    # 人工指令处理配置 🆕
    enable_instruction_execution: bool = True   # 是否启用人工指令自动执行
    instruction_safety_level: str = "medium"    # 安全级别：strict/medium/permissive
    require_confirmation_for_high_risk: bool = True  # 高风险操作是否需要确认
    allowed_commands: List[str] = None          # 命令白名单（None 表示使用默认）
    blocked_patterns: List[str] = None          # 阻止的命令模式
    max_download_size_mb: int = 500             # 最大下载文件大小
    sandbox_path: str = None                    # 沙箱路径（None 表示使用 Notebook 所在目录）
    
    # 输出配置
    output_dir: str = "./output"          # 输出目录
    generate_html: bool = True            # 是否生成 HTML
    hide_code_in_report: bool = False     # 报告中是否隐藏代码
    include_instruction_log: bool = True  # 报告中是否包含指令执行日志 🆕
    
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

# 启用人工指令自动执行 🆕
nb-agent run notebook.ipynb \
  --enable-instruction-execution \
  --safety-level medium \
  --confirm-high-risk

# 严格模式（仅执行白名单命令）🆕
nb-agent run notebook.ipynb \
  --enable-instruction-execution \
  --safety-level strict \
  --allowed-commands "pip,mkdir,wget"

# 预览模式（只检测不执行）🆕
nb-agent scan notebook.ipynb --show-instructions
```

### 6.2 Python API

```python
from nb_agent import NotebookAgent

agent = NotebookAgent(
    llm_provider="openai",
    enable_auto_fix=True,
    # 人工指令执行配置 🆕
    enable_instruction_execution=True,
    instruction_safety_level="medium",
    require_confirmation_for_high_risk=False,  # 自动化场景关闭确认
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
    # 查看指令执行摘要 🆕
    print(f"Instructions executed: {result.instruction_summary}")
else:
    print(f"Failed: {result.error_summary}")

# 仅扫描指令（不执行）🆕
instructions = agent.scan_instructions("notebook.ipynb")
for inst in instructions:
    print(f"[{inst['type']}] {inst['description']}")
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
| **人工指令自动化** | 🆕 自动识别并执行 Markdown 中的操作指令 |
| **可观测** | 完整的执行日志与报告 |
| **可扩展** | 支持批量、定时、API 调用 |
| **安全性** | 多层安全防护 + 沙箱隔离 |

### 8.2 技术栈总结

```
执行层：papermill + nbclient + nbconvert
智能层：LLM (GPT-4 / CodeLlama)
  └── 指令检测与解析
  └── 错误分析与修复
指令执行层：subprocess + pathlib + httpx  🆕
  └── 终端命令执行
  └── 文件/目录操作
  └── 下载任务处理
安全层：命令白名单 + 路径沙箱 + 风险分级  🆕
接口层：CLI (Click) + API (FastAPI)
调度层：APScheduler / Celery（可选）
隔离层：Docker（可选）
```

### 8.3 核心创新点

**解决 Notebook "无法一键执行" 的根本问题：**

| 传统痛点 | 本 Agent 解决方案 |
|----------|-------------------|
| Markdown 中的 "请执行 xxx" | LLM 识别 + 自动执行 |
| "请创建文件 xxx" | 自动创建文件并写入内容 |
| "请下载 xxx 到 yyy" | 自动下载到指定位置 |
| "请设置环境变量" | 自动设置 |
| 执行失败需人工排查 | LLM 自动诊断修复 |

### 8.4 适用场景

- 数据分析流水线自动化
- 机器学习实验批量运行
- 定时报告生成
- CI/CD 中的 Notebook 测试
- 教学环境的作业批改
- **🆕 复杂 Notebook 的全自动化执行**
- **🆕 遗留 Notebook 的自动化改造**