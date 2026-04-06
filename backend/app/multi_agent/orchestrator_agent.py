import asyncio
from agents import Agent, ModelSettings, Runner
from app.infrastructure.ai.openai_client import sub_model
from app.infrastructure.ai.openai_client import main_model
from app.infrastructure.ai.prompt_loader import load_prompt
from app.multi_agent.agent_factory import AGENT_TOOLS
from app.infrastructure.tools.mcp.mcp_servers import (
    search_mcp_client,
    baidu_mcp_client,
)
from contextlib import AsyncExitStack

# 1. 创建主调度智能体
orchestrator_agent = Agent(
    name="主调度智能体",
    # name: 当前这个 Agent 的名称。
    #
    # 这个名字的作用主要是：
    # 1. 标识它在整个多 Agent 系统中的角色
    # 2. 方便日志、调试、观察链路时快速识别
    #
    # 从命名上也能看出来，它不是具体干活的专家，
    # 而是“负责统一调度和分发任务”的总控角色。

    instructions=load_prompt("orchestrator_v1"),
    # instructions: 主调度智能体的系统提示词（prompt）。
    #
    # 这里通过 load_prompt("orchestrator_v1") 加载一份专门给总控 Agent 用的提示词。
    #
    # 这份 prompt 一般会定义：
    # - 这个 Agent 的职责是什么
    # - 它应该如何理解用户问题
    # - 它什么时候该自己回答，什么时候该调用工具
    # - 它如何在多个专家 Agent 工具之间做路由
    #
    # 由于它是“主调度智能体”，
    # 所以这份 prompt 的重点通常不是领域知识本身，
    # 而是：
    # 1. 意图识别
    # 2. 任务分类
    # 3. 专家选择
    # 4. 路由策略
    #
    # 也就是说：
    # 主调度 Agent 的核心能力，不在于它自己懂多少，
    # 而在于它能不能把问题正确分配给合适的子 Agent。

    # model=main_model,   # 推理模型（ds_r1[1.科学 2.计算 3.需求拆解]） (已推理为主，干活其次【funcation_call】)
    # 这行被注释掉了，说明你原本考虑过用 main_model 作为主调度模型。
    #
    # 从注释看，你对 main_model 的定位是：
    # - 更偏推理
    # - 更适合需求拆解
    # - 更擅长做“判断”和“决策”
    # - 不一定擅长高频工具执行
    #
    # 这其实非常符合“总控 Agent”的典型设计思路：
    # 总控 Agent 负责分析问题、拆解需求、做路由决策，
    # 不一定亲自下场执行所有任务。
    #
    # 你注释里写的“干活其次【function_call】”，意思可以理解为：
    # 它更适合负责上层策略和判断，
    # 而不是频繁进行工具调用和业务执行。

    model=sub_model,
    # model: 当前真正生效的底层模型。
    #
    # 这里你没有使用上面的 main_model，
    # 而是改成了 sub_model。
    #
    # 你自己的注释也已经点出了它的特点：
    # - 更偏“干活”
    # - 更偏实际执行
    # - 推理能力可能有，但不一定像推理模型那样强
    #
    # 这意味着你当前做了一个架构上的取舍：
    # 不是用一个“更强的推理模型”来做调度，
    # 而是直接用一个“更务实的通用执行模型”来做总控。
    #
    # 这种选择的潜在优点：
    # 1. 成本可能更低
    # 2. 工具调用更直接
    # 3. 执行效率可能更高
    #
    # 潜在风险：
    # 1. 复杂问题的路由判断不一定最优
    # 2. 需求拆解能力可能不如专门的推理模型
    #
    # 也就是说，这里本质上是在平衡：
    # - “推理和决策能力”
    # - “实际工具执行能力”
    #
    # 如果后续你发现总控 Agent 容易路由错，
    # 一个优化方向就是重新切回 main_model 试验。

    model_settings=ModelSettings(
        temperature=0,
    ),
    # model_settings: 模型运行参数。
    #
    # temperature=0 的作用是：
    # - 尽量减少模型随机发挥
    # - 让输出更稳定
    # - 让同类输入更容易得到一致决策
    #
    # 对主调度 Agent 来说，这个设置非常合理。
    #
    # 因为调度 Agent 最重要的是：
    # - 稳定判断
    # - 稳定分类
    # - 稳定路由
    #
    # 如果 temperature 太高，可能会出现：
    # - 同一个问题有时路由给技术专家
    # - 有时又路由给业务专家
    #
    # 这种不稳定在多 Agent 系统里是比较危险的，
    # 所以主调度层通常更适合低温甚至 0 温度。

    # 直接使用Agent Tools
    tools=AGENT_TOOLS,
    # tools: 当前主调度智能体可调用的工具列表。
    #
    # 这里传入的不是普通业务函数，而是你前面封装好的“专家智能体工具”集合。
    #
    # 也就是说：
    # AGENT_TOOLS 里的每一个工具，背后其实都对应一个专家 Agent。
    #
    # 例如：
    # - consult_technical_expert
    #   -> 内部会转交 technical_agent
    #
    # - query_service_station_and_navigate
    #   -> 内部会转交 comprehensive_service_agent
    #
    # 所以对 orchestrator_agent 来说，
    # 它并不是直接操作底层地图、知识库、维修站查询逻辑，
    # 而是通过这些“工具化的专家入口”进行调度。
    #
    # 这其实就是典型的多 Agent 分层架构：
    #
    # 用户问题
    #   -> 主调度智能体 orchestrator_agent
    #       -> 选择一个专家工具
    #           -> 专家工具内部运行对应的子 Agent
    #               -> 子 Agent 再调自己的模型 / 本地工具 / MCP 工具
    #
    # 这种设计的核心优势是：
    # 1. 主调度层只做意图识别和任务分发
    # 2. 领域能力沉淀在各自专家 Agent 内部
    # 3. 系统更容易扩展和维护
)