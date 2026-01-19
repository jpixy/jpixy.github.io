+++
title = "07.LangChain实践指南"
date = 2026-01-13
description = "LangChain框架深度实践：核心概念、链式调用、RAG实现、Agent开发与生产部署"
[taxonomies]
tags = ["ai", "langchain", "llm", "rag", "agent"]
+++

# LangChain实践指南

LangChain 是构建 LLM 应用的主流框架，本文系统性地介绍 LangChain 的核心概念与实践技巧。

---

## 一、LangChain 概述

### 1.1 框架定位

| 定位 | 说明 |
|-----|------|
| 开发框架 | 简化 LLM 应用开发 |
| 抽象层 | 统一不同 LLM 接口 |
| 组件库 | 提供常用组件 |
| 编排工具 | 组合复杂工作流 |

### 1.2 生态系统

```
┌─────────────────────────────────────────────────┐
│                LangChain 生态                    │
├─────────────────────────────────────────────────┤
│  langchain-core    核心抽象和接口                │
│  langchain         主框架                        │
│  langchain-community 社区集成                   │
│  langchain-openai  OpenAI 集成                  │
│  langgraph         图工作流                      │
│  langserve         API 部署                      │
│  langsmith         可观测性平台                  │
└─────────────────────────────────────────────────┘
```

### 1.3 核心抽象

| 抽象 | 说明 |
|-----|------|
| Runnable | 可执行组件基类 |
| Chain | 链式调用 |
| Agent | 智能体 |
| Tool | 工具 |
| Memory | 记忆 |
| Retriever | 检索器 |

---

## 二、核心组件

### 2.1 模型（Models）

**Chat Models**：

| 属性 | 说明 |
|-----|------|
| 输入 | 消息列表 |
| 输出 | AI 消息 |
| 流式 | 支持流式输出 |
| 工具调用 | 支持函数调用 |

**消息类型**：

| 类型 | 说明 |
|-----|------|
| SystemMessage | 系统提示 |
| HumanMessage | 用户消息 |
| AIMessage | AI 回复 |
| ToolMessage | 工具结果 |

### 2.2 提示模板（Prompts）

**PromptTemplate**：

```
模板: "请将{text}翻译成{language}"

变量: text, language

实例化: "请将Hello翻译成中文"
```

**ChatPromptTemplate**：

```
消息列表模板:
- SystemMessage: 你是翻译助手
- HumanMessage: 请翻译{text}
```

### 2.3 输出解析（Output Parsers）

| 解析器 | 输出格式 |
|-------|---------|
| StrOutputParser | 纯文本 |
| JsonOutputParser | JSON |
| PydanticOutputParser | Pydantic 对象 |
| CommaSeparatedListOutputParser | 列表 |

### 2.4 检索器（Retrievers）

| 类型 | 说明 |
|-----|------|
| VectorStoreRetriever | 向量检索 |
| BM25Retriever | 关键词检索 |
| EnsembleRetriever | 混合检索 |
| SelfQueryRetriever | 自查询 |
| MultiQueryRetriever | 多查询 |
| ContextualCompressionRetriever | 压缩检索 |

---

## 三、LCEL 表达式语言

### 3.1 什么是 LCEL

**LangChain Expression Language**：

| 特点 | 说明 |
|-----|------|
| 声明式 | 声明组件组合方式 |
| 流式原生 | 自动支持流式 |
| 并行支持 | 自动并行执行 |
| 可组合 | 任意组件可组合 |

### 3.2 基本语法

**管道操作符 `|`**：

```
chain = prompt | model | output_parser

# 等价于
def chain(input):
    x = prompt.invoke(input)
    x = model.invoke(x)
    x = output_parser.invoke(x)
    return x
```

### 3.3 常用方法

| 方法 | 说明 |
|-----|------|
| invoke | 单次调用 |
| batch | 批量调用 |
| stream | 流式调用 |
| ainvoke | 异步调用 |
| astream | 异步流式 |

### 3.4 组合模式

**顺序链**：
```
chain = step1 | step2 | step3
```

**并行执行**：
```
from langchain_core.runnables import RunnableParallel

chain = RunnableParallel(
    summary=summary_chain,
    translation=translation_chain
)
```

**条件分支**：
```
from langchain_core.runnables import RunnableBranch

chain = RunnableBranch(
    (condition1, chain1),
    (condition2, chain2),
    default_chain
)
```

### 3.5 变量传递

```
from langchain_core.runnables import RunnablePassthrough

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
)
```

---

## 四、RAG 实现

### 4.1 文档加载

**常用加载器**：

| 加载器 | 文件类型 |
|-------|---------|
| PyPDFLoader | PDF |
| Docx2txtLoader | Word |
| UnstructuredHTMLLoader | HTML |
| CSVLoader | CSV |
| DirectoryLoader | 目录批量 |
| WebBaseLoader | 网页 |

### 4.2 文本分割

**RecursiveCharacterTextSplitter**：

```
分隔符优先级:
1. "\n\n" (段落)
2. "\n" (换行)
3. " " (空格)
4. "" (字符)
```

**参数设置**：

| 参数 | 建议值 | 说明 |
|-----|-------|------|
| chunk_size | 500-1000 | 块大小 |
| chunk_overlap | 50-200 | 重叠大小 |
| length_function | len | 长度计算 |

### 4.3 向量存储

**常用向量库**：

| 向量库 | 集成方式 |
|-------|---------|
| Chroma | langchain-chroma |
| FAISS | langchain-community |
| Pinecone | langchain-pinecone |
| Milvus | langchain-milvus |
| Qdrant | langchain-qdrant |

**基本操作**：

| 操作 | 说明 |
|-----|------|
| from_documents | 从文档创建 |
| add_documents | 添加文档 |
| similarity_search | 相似搜索 |
| as_retriever | 转为检索器 |

### 4.4 检索链

**基础 RAG 链**：

```
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

prompt = ChatPromptTemplate.from_template("""
根据以下上下文回答问题：

上下文：{context}

问题：{question}
""")

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
```

### 4.5 高级检索

**多查询检索**：

```
from langchain.retrievers.multi_query import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)
```

**上下文压缩**：

```
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)
```

---

## 五、Agent 开发

### 5.1 工具定义

**使用装饰器**：

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """搜索网络获取信息
    
    Args:
        query: 搜索关键词
    """
    # 实现搜索逻辑
    return results
```

**使用 StructuredTool**：

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str
    num_results: int = 5

def search(query: str, num_results: int) -> str:
    ...

search_tool = StructuredTool.from_function(
    func=search,
    name="search",
    description="搜索网络",
    args_schema=SearchInput
)
```

### 5.2 创建 Agent

**使用 create_react_agent**：

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

# 获取 ReAct 提示模板
prompt = hub.pull("hwchase17/react")

# 创建 Agent
agent = create_react_agent(llm, tools, prompt)

# 创建执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10
)

# 执行
result = agent_executor.invoke({"input": "查询北京天气"})
```

### 5.3 OpenAI Functions Agent

```python
from langchain.agents import create_openai_functions_agent

agent = create_openai_functions_agent(llm, tools, prompt)
```

### 5.4 Agent 配置

| 参数 | 说明 |
|-----|------|
| max_iterations | 最大迭代次数 |
| max_execution_time | 最大执行时间 |
| early_stopping_method | 提前终止方式 |
| handle_parsing_errors | 解析错误处理 |
| return_intermediate_steps | 返回中间步骤 |

---

## 六、记忆管理

### 6.1 会话记忆

**ConversationBufferMemory**：

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    return_messages=True,
    memory_key="chat_history"
)
```

**ConversationBufferWindowMemory**：

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(
    k=5,  # 保留最近 5 轮
    return_messages=True
)
```

### 6.2 摘要记忆

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(
    llm=llm,
    return_messages=True
)
```

### 6.3 向量记忆

```python
from langchain.memory import VectorStoreRetrieverMemory

memory = VectorStoreRetrieverMemory(
    retriever=vectorstore.as_retriever()
)
```

### 6.4 在 LCEL 中使用记忆

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
```

---

## 七、LangGraph 工作流

### 7.1 什么是 LangGraph

| 特点 | 说明 |
|-----|------|
| 图结构 | 节点和边定义工作流 |
| 状态管理 | 内置状态机制 |
| 循环支持 | 支持循环和条件 |
| 持久化 | 支持状态持久化 |

### 7.2 基本概念

| 概念 | 说明 |
|-----|------|
| State | 共享状态 |
| Node | 处理节点 |
| Edge | 连接边 |
| ConditionalEdge | 条件边 |
| Checkpointer | 状态持久化 |

### 7.3 创建图

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]
    next_step: str

# 创建图
graph = StateGraph(State)

# 添加节点
graph.add_node("agent", agent_node)
graph.add_node("tool", tool_node)

# 添加边
graph.add_edge("tool", "agent")

# 条件边
graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tool",
        "end": END
    }
)

# 设置入口
graph.set_entry_point("agent")

# 编译
app = graph.compile()
```

### 7.4 状态管理

```python
# 状态更新
def agent_node(state: State):
    result = agent.invoke(state["messages"])
    return {
        "messages": [result],
        "next_step": "tool" if result.tool_calls else "end"
    }
```

### 7.5 持久化

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string(":memory:")

app = graph.compile(checkpointer=checkpointer)

# 带线程 ID 调用
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke(input, config)
```

---

## 八、可观测性

### 8.1 LangSmith 集成

```python
import os

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "my-project"
```

### 8.2 追踪内容

| 内容 | 说明 |
|-----|------|
| 调用链 | 完整调用过程 |
| 输入输出 | 每步的输入输出 |
| 延迟 | 各步骤耗时 |
| Token 用量 | LLM token 消耗 |
| 错误 | 错误信息和堆栈 |

### 8.3 回调处理

```python
from langchain.callbacks import StdOutCallbackHandler

handler = StdOutCallbackHandler()

result = chain.invoke(
    {"input": "hello"},
    config={"callbacks": [handler]}
)
```

### 8.4 自定义回调

```python
from langchain.callbacks.base import BaseCallbackHandler

class MyHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"LLM 开始: {prompts}")
    
    def on_llm_end(self, response, **kwargs):
        print(f"LLM 结束: {response}")
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"工具开始: {input_str}")
```

---

## 九、部署上线

### 9.1 LangServe

```python
from fastapi import FastAPI
from langserve import add_routes

app = FastAPI()

add_routes(app, chain, path="/chat")

# 启动: uvicorn main:app --reload
```

### 9.2 API 端点

| 端点 | 方法 | 说明 |
|-----|------|------|
| /invoke | POST | 单次调用 |
| /batch | POST | 批量调用 |
| /stream | POST | 流式调用 |
| /input_schema | GET | 输入 Schema |
| /output_schema | GET | 输出 Schema |

### 9.3 客户端调用

```python
from langserve import RemoteRunnable

chain = RemoteRunnable("http://localhost:8000/chat")
result = chain.invoke({"input": "hello"})
```

### 9.4 生产考虑

| 方面 | 建议 |
|-----|------|
| 认证 | 添加 API Key 验证 |
| 限流 | 请求频率限制 |
| 缓存 | 结果缓存 |
| 监控 | 接入监控系统 |
| 日志 | 完整日志记录 |

---

## 十、最佳实践

### 10.1 代码组织

```
project/
├── chains/
│   ├── rag_chain.py
│   └── agent_chain.py
├── tools/
│   ├── search.py
│   └── calculator.py
├── prompts/
│   └── templates.py
├── config/
│   └── settings.py
└── main.py
```

### 10.2 配置管理

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    model_name: str = "gpt-4"
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 10.3 错误处理

```python
from langchain_core.runnables import RunnableConfig

def with_retry(chain, max_retries=3):
    for i in range(max_retries):
        try:
            return chain.invoke(input)
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(2 ** i)
```

### 10.4 测试策略

| 测试类型 | 说明 |
|---------|------|
| 单元测试 | 测试单个组件 |
| 集成测试 | 测试链的组合 |
| E2E 测试 | 完整流程测试 |
| 评估测试 | 质量评估 |

---

## 参考资料

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith](https://smith.langchain.com/)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
