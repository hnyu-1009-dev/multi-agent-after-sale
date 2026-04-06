from app.infrastructure.ai.prompt_loader import load_prompt

# load_prompt: 用来按名称加载提示词（prompt）模板。
# 这里会加载 technical_agent 这个智能体对应的系统提示词，
# 也就是告诉模型“你是谁、你擅长什么、应该如何回答”的那段规则文本。

from app.infrastructure.ai.openai_client import sub_model

# sub_model: 这里通常是已经初始化好的模型对象。
# 可以理解为“这个 Agent 背后真正调用的 LLM（大语言模型）实例”。

from app.infrastructure.tools.local.knowledge_base import query_knowledge

# query_knowledge: 本地知识库查询工具。
# Agent 在回答问题时，如果需要查本地资料，可以调用这个工具补充信息。

from app.infrastructure.tools.mcp.mcp_servers import search_mcp_servers

# search_mcp_client: MCP 客户端对象。
# 一般用于连接外部能力服务（例如搜索服务、第三方工具服务等）。
# Agent 可以通过它访问某些外部能力，而不是只依赖模型自身知识。

from agents import Agent, ModelSettings
from agents import Runner, RunConfig

# Agent: 定义一个智能体对象
# ModelSettings: 定义模型参数，例如 temperature
# Runner: 负责真正执行 Agent
# RunConfig: 定义运行时配置，例如是否开启 tracing


# ==============================
# 1. 定义技术智能体
# ==============================
# 这里是在“声明”一个智能体。
# 你可以把它理解成：
# - 给它一个名字
# - 给它一套系统规则（instructions）
# - 指定它使用哪个模型
# - 指定模型参数
# - 给它可调用的工具
# - 给它可连接的 MCP 服务
#
# 后面 Runner.run(...) 执行时，就是拿这个 technical_agent 去处理用户输入。
technical_agent = Agent(
    name="资讯与技术专家",
    # name: 智能体的名称。
    # 这个名称主要用于标识这个 Agent 的角色。
    # 比如日志、调试、追踪中，看到这个名字就知道这是“资讯与技术专家”这个角色。
    instructions=load_prompt("technical_agent"),
    # instructions: 智能体的系统提示词/角色说明。
    # load_prompt("technical_agent") 会去读取对应的 prompt 配置内容。
    #
    # 这一步非常关键，因为它决定了模型回答问题时的行为边界，例如：
    # - 擅长回答什么类型的问题
    # - 不应该回答什么问题
    # - 遇到闲聊、导航、实时问题时该如何处理
    #
    # 也就是说：
    # Agent 的“能力边界”和“说话方式”，很大程度由这里控制。
    model=sub_model,
    # model: 指定这个 Agent 使用的底层模型。
    # sub_model 一般是你项目里封装好的某个 LLM 客户端对象。
    model_settings=ModelSettings(temperature=0),
    # model_settings: 模型运行参数设置。
    #
    # temperature=0 的含义：
    # - 让模型尽量稳定、确定性地输出
    # - 减少“自由发挥”
    # - 更适合问答、知识检索、技术类场景
    #
    # 为什么这里设为 0？
    # 因为你的这个 Agent 看起来更偏“技术问答/知识问答”，
    # 希望它回答更稳、更一致，而不是发散式创作。
    #
    # 注释里说“不要发挥内容(软件层面限制模型的发挥)”非常准确，
    # 就是在尽量压制随机性。
    tools=[query_knowledge],
    # tools: 给 Agent 注册可调用工具。
    #
    # 这里注册了 query_knowledge，说明：
    # 当模型判断“仅靠自己记忆不够，需要查知识库”时，
    # 它可以调用这个工具去检索本地知识。
    #
    # 这属于典型的“模型 + 工具”架构，而不是纯模型裸答。
    mcp_servers=search_mcp_servers,
    # mcp_servers: 给 Agent 提供可连接的 MCP 服务端/客户端能力。
    #
    # MCP 可以理解成一种让模型接入外部工具生态的协议/机制。
    # 这里传入 search_mcp_client，意味着这个 Agent 在运行时
    # 还可以使用 MCP 提供的搜索能力或其他扩展能力。
    #
    # 注意：
    # tools 和 mcp_servers 虽然都能扩展能力，但通常不是同一个层次：
    # - tools 更像项目内直接注册的函数工具
    # - mcp_servers 更像通过 MCP 协议接入的外部能力服务
)
