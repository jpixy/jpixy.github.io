+++
title = "09.LangGraph实践指南"
date = 2025-01-13
description = "通过实战案例学习LangGraph，掌握状态机设计、循环控制、条件分支等核心技能"
[taxonomies]
tags = ["ai", "langgraph", "agent", "llm", "workflow", "practice"]
+++

# LangGraph 实践指南：从零构建复杂 Agent 工作流

---

## 一、环境准备

### 1.1 安装依赖

```bash
pip install langgraph langchain langchain-openai
```

### 1.2 配置 API Key

```bash
export OPENAI_API_KEY="your-api-key"
```

---

## 二、第一个 LangGraph 应用

### 2.1 最简示例

**目标**：构建一个简单的问答流程

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  START  │ ──▶ │  chat   │ ──▶ │   END   │
└─────────┘     └─────────┘     └─────────┘
```

**代码**：

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# 1. 定义状态
class State(TypedDict):
    messages: list
    response: str

# 2. 定义节点
def chat_node(state: State) -> dict:
    llm = ChatOpenAI()
    response = llm.invoke(state["messages"])
    return {"response": response.content}

# 3. 构建图
graph = StateGraph(State)
graph.add_node("chat", chat_node)
graph.set_entry_point("chat")
graph.add_edge("chat", END)

# 4. 编译
app = graph.compile()

# 5. 运行
result = app.invoke({
    "messages": [{"role": "user", "content": "你好"}],
    "response": ""
})
print(result["response"])
```

### 2.2 核心概念解析

```
┌─────────────────────────────────────────────────────────────────┐
│                    代码解析                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. State（状态）                                                │
│     - TypedDict 定义状态结构                                     │
│     - 状态在节点间传递和更新                                      │
│                                                                  │
│  2. Node（节点）                                                 │
│     - 一个普通函数                                               │
│     - 接收 state，返回 state 更新                                │
│     - 返回值自动合并到 state                                     │
│                                                                  │
│  3. Graph（图）                                                  │
│     - add_node: 添加节点                                        │
│     - set_entry_point: 设置入口                                 │
│     - add_edge: 连接节点                                        │
│                                                                  │
│  4. Compile & Invoke                                            │
│     - compile(): 编译成可执行的 app                             │
│     - invoke(): 运行图                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、条件分支

### 3.1 场景

根据用户输入决定不同处理路径：

```
                    ┌─────────────┐
                    │   router    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  search  │ │calculate │ │   chat   │
        └──────────┘ └──────────┘ └──────────┘
              │            │            │
              └────────────┼────────────┘
                           ▼
                    ┌─────────────┐
                    │     END     │
                    └─────────────┘
```

### 3.2 代码实现

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

class State(TypedDict):
    query: str
    query_type: str
    result: str

# 路由节点：判断查询类型
def router(state: State) -> dict:
    query = state["query"].lower()
    if "搜索" in query or "查找" in query:
        return {"query_type": "search"}
    elif "计算" in query or "+" in query or "-" in query:
        return {"query_type": "calculate"}
    else:
        return {"query_type": "chat"}

# 搜索节点
def search_node(state: State) -> dict:
    return {"result": f"搜索结果：{state['query']}"}

# 计算节点
def calculate_node(state: State) -> dict:
    return {"result": f"计算结果：42"}

# 聊天节点
def chat_node(state: State) -> dict:
    return {"result": f"回答：{state['query']}"}

# 路由函数
def route_query(state: State) -> Literal["search", "calculate", "chat"]:
    return state["query_type"]

# 构建图
graph = StateGraph(State)

graph.add_node("router", router)
graph.add_node("search", search_node)
graph.add_node("calculate", calculate_node)
graph.add_node("chat", chat_node)

graph.set_entry_point("router")

# 条件边
graph.add_conditional_edges(
    "router",
    route_query,
    {
        "search": "search",
        "calculate": "calculate",
        "chat": "chat"
    }
)

graph.add_edge("search", END)
graph.add_edge("calculate", END)
graph.add_edge("chat", END)

app = graph.compile()

# 测试
print(app.invoke({"query": "搜索天气", "query_type": "", "result": ""}))
print(app.invoke({"query": "计算 1+1", "query_type": "", "result": ""}))
print(app.invoke({"query": "你好", "query_type": "", "result": ""}))
```

### 3.3 条件边要点

```
┌─────────────────────────────────────────────────────────────────┐
│                    条件边 (Conditional Edges)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  graph.add_conditional_edges(                                   │
│      source_node,      # 起始节点                                │
│      route_function,   # 路由函数，返回下一节点的 key             │
│      path_map          # 映射：{返回值: 目标节点}                 │
│  )                                                               │
│                                                                  │
│  路由函数签名：                                                   │
│  def route_function(state: State) -> str:                       │
│      return "next_node_key"                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、循环与重试

### 4.1 场景

执行任务，失败则重试，最多 3 次：

```
┌─────────┐     ┌─────────┐
│  START  │ ──▶ │ execute │ ◀──┐
└─────────┘     └────┬────┘    │
                     │         │
              ┌──────┴──────┐  │
              ▼             ▼  │
         [success]      [error]│
              │             │  │
              ▼             ▼  │
         ┌─────────┐   ┌──────┴───┐
         │   END   │   │  retry?  │
         └─────────┘   └──────────┘
```

### 4.2 代码实现

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
import random

class State(TypedDict):
    task: str
    attempts: int
    max_attempts: int
    result: str
    status: str

def execute(state: State) -> dict:
    attempts = state["attempts"] + 1
    
    # 模拟：30% 成功率
    if random.random() > 0.7:
        return {
            "attempts": attempts,
            "result": "任务完成！",
            "status": "success"
        }
    else:
        return {
            "attempts": attempts,
            "result": f"第 {attempts} 次尝试失败",
            "status": "error"
        }

def should_retry(state: State) -> Literal["retry", "end", "give_up"]:
    if state["status"] == "success":
        return "end"
    elif state["attempts"] < state["max_attempts"]:
        return "retry"
    else:
        return "give_up"

# 构建图
graph = StateGraph(State)

graph.add_node("execute", execute)

graph.set_entry_point("execute")

graph.add_conditional_edges(
    "execute",
    should_retry,
    {
        "retry": "execute",  # 循环回 execute
        "end": END,
        "give_up": END
    }
)

app = graph.compile()

# 运行
result = app.invoke({
    "task": "完成任务",
    "attempts": 0,
    "max_attempts": 3,
    "result": "",
    "status": ""
})

print(f"最终状态: {result['status']}")
print(f"尝试次数: {result['attempts']}")
print(f"结果: {result['result']}")
```

### 4.3 循环要点

```
┌─────────────────────────────────────────────────────────────────┐
│                        循环实现                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  关键：条件边指向已存在的节点                                     │
│                                                                  │
│  graph.add_conditional_edges(                                   │
│      "execute",                                                 │
│      should_retry,                                              │
│      {                                                          │
│          "retry": "execute",  # ← 指回自己，形成循环              │
│          "end": END                                              │
│      }                                                          │
│  )                                                               │
│                                                                  │
│  注意事项：                                                       │
│  1. 必须有终止条件，否则无限循环                                   │
│  2. 在 state 中记录尝试次数                                       │
│  3. 设置最大重试次数                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、ReAct Agent 实战

### 5.1 ReAct 模式

```
┌─────────────────────────────────────────────────────────────────┐
│                     ReAct Agent                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ReAct = Reasoning (推理) + Acting (行动)                        │
│                                                                  │
│  循环：                                                          │
│  1. 思考：我需要做什么？                                          │
│  2. 行动：调用工具 / 直接回答                                     │
│  3. 观察：工具返回了什么？                                        │
│  4. 重复，直到得出最终答案                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 代码实现

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
import operator

# 定义工具
@tool
def search(query: str) -> str:
    """搜索互联网获取信息"""
    return f"搜索 '{query}' 的结果：这是一些相关信息..."

@tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression)
        return f"计算结果：{result}"
    except:
        return "计算错误"

tools = [search, calculator]

# 状态定义
class State(TypedDict):
    messages: Annotated[list, operator.add]  # 消息累加

# LLM 配置
llm = ChatOpenAI(model="gpt-4").bind_tools(tools)

# Agent 节点
def agent(state: State) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# 路由函数
def should_continue(state: State) -> Literal["tools", "end"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"

# 构建图
graph = StateGraph(State)

graph.add_node("agent", agent)
graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("agent")

graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)

graph.add_edge("tools", "agent")  # 工具执行后回到 agent

app = graph.compile()

# 运行
result = app.invoke({
    "messages": [HumanMessage("今天北京天气怎么样？")]
})

for msg in result["messages"]:
    print(f"{type(msg).__name__}: {msg.content}")
```

### 5.3 执行流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    执行流程示例                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  用户: "北京天气怎么样？"                                         │
│        │                                                         │
│        ▼                                                         │
│  Agent: 我需要搜索北京天气                                        │
│         → 调用 search("北京天气")                                │
│        │                                                         │
│        ▼                                                         │
│  Tools: 执行搜索，返回结果                                        │
│        │                                                         │
│        ▼                                                         │
│  Agent: 根据搜索结果，北京今天晴，25度...                         │
│         → 不需要更多工具，直接回答                                │
│        │                                                         │
│        ▼                                                         │
│  END:  返回最终答案                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 六、状态管理进阶

### 6.1 复杂状态设计

```python
from typing import TypedDict, Optional, List
from dataclasses import dataclass
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class State(TypedDict):
    # 任务信息
    task_id: str
    task_description: str
    
    # 执行状态
    status: TaskStatus
    current_step: str
    
    # 历史记录
    steps_completed: List[str]
    errors: List[str]
    
    # 结果
    result: Optional[str]
    
    # 元数据
    created_at: str
    updated_at: str
```

### 6.2 状态更新模式

```
┌─────────────────────────────────────────────────────────────────┐
│                    状态更新方式                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 覆盖更新（默认）                                             │
│     def node(state):                                            │
│         return {"result": "new_value"}  # 覆盖 result           │
│                                                                  │
│  2. 累加更新（使用 operator.add）                                │
│     from typing import Annotated                                │
│     import operator                                             │
│                                                                  │
│     class State(TypedDict):                                     │
│         messages: Annotated[list, operator.add]                 │
│                                                                  │
│     def node(state):                                            │
│         return {"messages": [new_msg]}  # 追加到列表             │
│                                                                  │
│  3. 自定义 Reducer                                              │
│     def my_reducer(current, update):                            │
│         return custom_merge(current, update)                    │
│                                                                  │
│     class State(TypedDict):                                     │
│         data: Annotated[dict, my_reducer]                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 七、Checkpointing（状态持久化）

### 7.1 场景

长时间运行的工作流，需要断点续传。

### 7.2 使用 MemorySaver

```python
from langgraph.checkpoint.memory import MemorySaver

# 创建 checkpointer
memory = MemorySaver()

# 编译时传入
app = graph.compile(checkpointer=memory)

# 运行时指定 thread_id
config = {"configurable": {"thread_id": "my-thread-1"}}

# 第一次运行
result1 = app.invoke(initial_state, config)

# 后续运行会从上次状态继续
result2 = app.invoke(new_input, config)
```

### 7.3 持久化存储

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# SQLite 持久化
with SqliteSaver.from_conn_string(":memory:") as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
    
    # 运行后状态会保存到 SQLite
    result = app.invoke(state, config)
```

---

## 八、Human-in-the-Loop

### 8.1 场景

某些步骤需要人工审批或确认。

### 8.2 实现方式

```python
# 在编译时设置中断点
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["sensitive_action"]  # 在这个节点前暂停
)

# 运行到中断点会自动暂停
result = app.invoke(initial_state, config)

# 查看当前状态
current_state = app.get_state(config)
print(f"等待审批: {current_state.values}")

# 人工确认后继续
# 方式1: 直接继续
app.invoke(None, config)

# 方式2: 修改状态后继续
app.update_state(config, {"approved": True})
app.invoke(None, config)
```

### 8.3 流程示意

```
┌─────────┐     ┌─────────┐     ┌─────────────────┐     ┌─────────┐
│  START  │ ──▶ │ prepare │ ──▶ │ sensitive_action│ ──▶ │   END   │
└─────────┘     └─────────┘     └────────┬────────┘     └─────────┘
                                         │
                                    [暂停等待]
                                         │
                                         ▼
                                   ┌──────────┐
                                   │ 人工审批  │
                                   └──────────┘
```

---

## 九、子图（Subgraph）

### 9.1 场景

将复杂流程拆分为可复用的子流程。

### 9.2 定义子图

```python
# 定义子图
def create_validation_subgraph():
    subgraph = StateGraph(State)
    
    subgraph.add_node("validate_format", validate_format)
    subgraph.add_node("validate_content", validate_content)
    
    subgraph.set_entry_point("validate_format")
    subgraph.add_edge("validate_format", "validate_content")
    subgraph.add_edge("validate_content", END)
    
    return subgraph.compile()

# 在主图中使用
main_graph = StateGraph(State)

main_graph.add_node("prepare", prepare)
main_graph.add_node("validate", create_validation_subgraph())  # 嵌入子图
main_graph.add_node("process", process)

main_graph.set_entry_point("prepare")
main_graph.add_edge("prepare", "validate")
main_graph.add_edge("validate", "process")
main_graph.add_edge("process", END)
```

---

## 十、调试技巧

### 10.1 打印执行过程

```python
# 方式1: 流式输出
for chunk in app.stream(state):
    print(chunk)

# 方式2: 使用回调
from langchain_core.callbacks import StdOutCallbackHandler

result = app.invoke(state, config={
    "callbacks": [StdOutCallbackHandler()]
})
```

### 10.2 可视化图结构

```python
# 生成 Mermaid 图
print(app.get_graph().draw_mermaid())

# 保存为 PNG (需要安装 graphviz)
app.get_graph().draw_png("graph.png")
```

### 10.3 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 无限循环 | 条件边没有终止条件 | 检查路由函数逻辑 |
| 状态丢失 | 节点返回覆盖了状态 | 只返回需要更新的字段 |
| 类型错误 | State 定义与返回不匹配 | 检查 TypedDict 定义 |
| 边缺失 | 有节点没连接到图 | 确保所有节点都有入边和出边 |

---

## 十一、实战项目：自动代码审查

### 11.1 需求

```
输入：代码文件
流程：
  1. 分析代码结构
  2. 检查代码规范
  3. 发现问题则尝试修复
  4. 生成审查报告
```

### 11.2 状态设计

```python
class ReviewState(TypedDict):
    code: str
    language: str
    analysis: dict
    issues: list
    fixes: list
    attempts: int
    report: str
    status: str
```

### 11.3 图结构

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  START  │ ──▶ │ analyze │ ──▶ │  check  │
└─────────┘     └─────────┘     └────┬────┘
                                     │
                              ┌──────┴──────┐
                              ▼             ▼
                         [有问题]       [无问题]
                              │             │
                              ▼             │
                         ┌─────────┐        │
                         │   fix   │ ◀──┐   │
                         └────┬────┘    │   │
                              │         │   │
                         ┌────┴────┐    │   │
                         ▼         ▼    │   │
                    [已修复]   [未修复]  │   │
                         │         │    │   │
                         │    ┌────┴────┴───┼───┐
                         │    ▼             ▼   │
                         │ [重试<3]      [放弃] │
                         │    │             │   │
                         │    └─────────────┘   │
                         │                      │
                         └───────────┬──────────┘
                                     ▼
                              ┌─────────────┐
                              │   report    │
                              └──────┬──────┘
                                     ▼
                              ┌─────────────┐
                              │     END     │
                              └─────────────┘
```

---

## 十二、总结

### 12.1 核心要点

| 概念 | 要点 |
|------|------|
| **State** | TypedDict 定义，贯穿全流程 |
| **Node** | 普通函数，接收和返回 state |
| **Edge** | add_edge 普通边，add_conditional_edges 条件边 |
| **循环** | 条件边指向已存在节点 |
| **持久化** | compile 时传入 checkpointer |

### 12.2 设计原则

```
1. 状态先行：先设计好 State 结构
2. 节点单一职责：每个节点做一件事
3. 条件明确：路由函数返回明确的下一步
4. 终止保证：确保有终止条件
5. 错误处理：在状态中记录错误
```

### 12.3 从简到繁

```
简单问答     → 单节点
条件分支     → add_conditional_edges
循环重试     → 条件边指回
Agent        → tools + 循环
复杂工作流   → 子图 + 持久化 + 人工介入
```

---

## 相关文章

- [上一篇：LangGraph详解](/articles/ai/ai-08-LangGraph详解/)
- [下一篇：AI Agent智能体架构详解](/articles/ai/ai-10-Agent智能体架构详解/)
