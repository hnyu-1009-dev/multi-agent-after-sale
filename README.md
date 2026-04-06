# multi-agent-after-sale

基于多智能体和知识库检索的售后问答系统。项目由前端页面和两个后端服务组成，后端分别负责对话编排与知识检索。

## 项目结构

```text
multi-agent-after-sale
├─ front/                  # 前端界面
└─ backend/
   ├─ app/                 # 主业务服务，多智能体编排与对话入口
   └─ knowledge/           # 知识库服务，负责入库、检索与答案生成
```

## 后端结构

### `backend/app`

主业务服务，负责接收用户问题、组织多智能体协作、管理会话记忆，并将结果以流式形式返回给前端。

目录职责：

```text
backend/app
├─ api/                    # FastAPI 入口与路由
├─ config/                 # 配置读取
├─ infrastructure/
│  ├─ ai/                  # LLM 客户端与 prompt 加载
│  ├─ database/            # 数据库连接池
│  ├─ logging/             # 日志能力
│  └─ tools/               # 本地工具与 MCP 工具
├─ multi_agent/            # 编排器、技术专家、服务专家
├─ prompts/                # Agent 提示词
├─ repositories/           # 会话持久化
├─ schemas/                # 请求与响应模型
├─ services/               # 会话、Agent、流式响应服务
└─ user_memories/          # 用户会话历史存储
```

核心职责：

- 统一承接前端对话请求
- 管理 `user_id/session_id` 维度的会话记忆
- 通过编排 Agent 将问题分发给技术专家或服务专家
- 调用知识库工具、服务站工具、MCP 工具等外部能力
- 输出 SSE 流式响应

### `backend/knowledge`

知识库服务，负责文档处理、向量化存储、检索与基于上下文的答案生成。

目录职责：

```text
backend/knowledge
├─ api/                    # FastAPI 入口与路由
├─ config/                 # 配置读取
├─ data/
│  ├─ crawl/               # Markdown 知识文档
│  └─ tmp/                 # 临时文件
├─ repositories/           # 文件与向量库操作
├─ services/
│  ├─ crawler/             # 爬取相关能力
│  ├─ ingestion/           # 文档切分与入库
│  ├─ retrieval_service.py # 检索与重排
│  └─ query_service.py     # 基于上下文生成答案
├─ schemas/                # 接口模型
└─ chroma_kb/              # Chroma 本地向量库
```

核心职责：

- 接收并处理 Markdown 文档
- 将文档切分为适合检索的 chunk
- 使用 embedding 写入 Chroma 向量库
- 通过召回、粗排、精排完成 RAG 检索
- 基于检索上下文生成最终答案

## 后端调用关系

```text
front
  -> backend/app
      -> orchestrator agent
          -> technical agent
              -> backend/knowledge
          -> service agent
              -> local tools / MCP tools / database
```

## 核心技术

### 主服务 `backend/app`

- FastAPI
- Uvicorn
- Pydantic / pydantic-settings
- OpenAI SDK
- `openai-agents`
- httpx
- PyMySQL
- DBUtils

### 知识库服务 `backend/knowledge`

- FastAPI
- Uvicorn
- LangChain Core
- LangChain Community
- langchain-openai
- langchain-chroma
- Chroma
- scikit-learn
- jieba
- markdownify
- unstructured

## 关键设计

### 多智能体协作

- 编排 Agent 负责识别意图和任务路由
- 技术专家 Agent 负责技术类问答，优先走知识库检索
- 服务专家 Agent 负责维修站、导航和位置类问题

### RAG 检索链路

- 文档进入知识库后先进行切分与清洗
- 文档 chunk 被向量化并存入 Chroma
- 查询时同时利用向量召回和标题匹配
- 通过 embedding 与 cosine similarity 做进一步精排
- 将最终上下文交给大模型生成答案

### 会话记忆

- 主服务将会话历史按用户和会话维度持久化
- 查询时自动拼接最近上下文
- 历史消息用于增强连续对话能力

### 流式返回

- 主服务基于 SSE 返回处理过程和结果
- 便于前端展示思考过程、工具调用过程和最终答案
