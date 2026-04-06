from agents import set_tracing_disabled

# 关闭 tracing（链路追踪/调试追踪）。
# tracing 一般用于记录 Agent 的完整执行过程，例如：
# - 模型调用过程
# - 工具调用链路
# - 中间步骤信息
#
# 这里在模块最开始就关闭 tracing，表示后续这个文件里的 Agent 运行时，
# 不希望额外记录追踪信息。
#
# 这样做的常见原因：
# 1. 本地调试时不想看到过多追踪日志
# 2. 不希望把运行链路上报到 tracing 后端
# 3. 减少调试噪音
set_tracing_disabled(True)

from agents import Agent, ModelSettings

# Agent: 定义一个智能体对象
# ModelSettings: 定义模型参数，例如 temperature、max_tokens 等

from app.infrastructure.ai.openai_client import sub_model

# sub_model: 你项目里封装好的“子模型”对象。
# 这里它会作为当前这个业务智能体背后的 LLM。
#
# 注意：
# Agent 本身不是模型，它只是“角色 + 配置 + 工具 + 模型”的组合体。
# 真正负责理解用户输入、决定是否调用工具、生成答案的，还是这个 sub_model。

from app.infrastructure.tools.local.service_station import (
    resolve_user_location_from_text,
    query_nearest_repair_shops_by_coords,
)

# 这里导入了两个本地工具：
#
# 1. resolve_user_location_from_text
#    作用通常是：从用户自然语言里解析出位置或地理线索
#    例如：
#    - “我在回龙观附近”
#    - “从昌平区回龙观到……”
#    它可能会把文本中的地点抽取出来，变成结构化位置信息。
#
# 2. query_nearest_repair_shops_by_coords
#    作用通常是：根据坐标查询最近的维修服务站
#    这说明你的业务智能体并不是纯聊天，
#    而是要围绕“服务站推荐/维修点查询”这类业务来做工具调用。

from app.infrastructure.tools.mcp.mcp_servers import baidu_mcp_servers

# baidu_mcp_client: 百度地图 MCP 客户端。
#
# 这是一个远程 MCP 工具服务入口，通常用于访问地图能力，例如：
# - 路线规划
# - 地图页面拉起
# - 地理位置查询
# - POI 检索
#
# 本地工具和 MCP 工具的区别大致可以这样理解：
# - 本地工具：你项目内部直接注册的 Python 函数
# - MCP 工具：通过 MCP 协议接入的远程工具服务

from app.infrastructure.ai.prompt_loader import load_prompt

# load_prompt: 按名称加载 prompt 模板。
# 这里加载的是 comprehensive_service_agent 对应的系统提示词，
# 用来规定这个智能体的角色、职责边界、回答策略和工具使用原则。


# ==============================================================================
# 1. 定义“全能业务智能体”
# ==============================================================================
comprehensive_service_agent = Agent(
    name="全能业务智能体",
    # name: 这个 Agent 的名字。
    # 主要用于角色标识、日志显示、调试观察。
    #
    # 它不直接决定模型能力，
    # 但能帮助你在多 Agent 场景下区分“现在到底是谁在处理请求”。
    instructions=load_prompt("comprehensive_service_agent"),
    # instructions: 智能体的系统提示词。
    #
    # 这是整个 Agent 行为的核心约束之一。
    # 它通常会告诉模型：
    # - 你是谁
    # - 你的业务范围是什么
    # - 什么问题该回答，什么问题该拒绝
    # - 遇到服务站、路线、地图类需求时如何调用工具
    #
    # 也就是说：
    # Agent 的“行为边界”，很大程度上由这里决定。
    model=sub_model,
    # model: 指定当前 Agent 使用的底层模型。
    #
    # 当用户输入来了之后：
    # 1. 模型先理解问题
    # 2. 判断需不需要调用工具
    # 3. 如果需要，就调用本地工具或 MCP 工具
    # 4. 最后再由模型整合结果输出给用户
    model_settings=ModelSettings(
        temperature=0,
        max_tokens=2048,
    ),
    # model_settings: 模型运行参数配置。
    #
    # temperature=0:
    # - 让模型输出更稳定、更收敛
    # - 减少自由发挥
    # - 更适合业务问答、工具调用、规则型场景
    #
    # max_tokens=2048:
    # - 控制单次生成输出的最大 token 数
    # - 防止回答过长
    # - 对业务型 Agent 来说，这个值通常足够了
    # 本地工具：只有服务站查询相关
    tools=[
        resolve_user_location_from_text,
        query_nearest_repair_shops_by_coords,
    ],
    # tools: 注册给 Agent 的本地工具列表。
    #
    # 模型在推理过程中，如果判断“需要查位置 / 需要查最近服务站”，
    # 就可以调用这里注册的函数。
    #
    # 这意味着：
    # 当前 Agent 的本地工具能力集中在“服务站相关业务”。
    # 远程MCP工具：地图
    mcp_servers=baidu_mcp_servers,
    # mcp_servers: 注册给 Agent 的远程 MCP 工具服务。
    #
    # 这里提供的是百度地图能力。
    # 所以这个 Agent 既能：
    # - 用本地工具做服务站查询
    # - 用 MCP 做地图/路线类能力扩展
)
