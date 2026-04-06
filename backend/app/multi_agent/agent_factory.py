import httpx

from agents import Agent, ModelSettings, function_tool, Runner
# function_tool:
# 用来把一个 Python 函数注册成 Agent 可调用的工具。
#
# 也就是说，被 @function_tool 修饰后的函数，不再只是普通业务函数，
# 而是可以被别的 Agent 识别、选择、调用的“工具”。
#
# Runner:
# Agent 的执行器。
# Agent 本身只是一个“角色定义 + 模型 + 工具配置”的对象，
# 真正负责执行 Agent 的是 Runner。

from agents.run import RunConfig
# RunConfig: Agent 运行时配置。
# 用来控制一次具体运行时的行为，比如：
# - 是否关闭 tracing
# - 是否启用某些执行选项
#
# 它和 Agent 自身的静态配置不同：
# - Agent：定义“这个智能体是谁、拥有什么能力”
# - RunConfig：定义“这一次怎么跑”


from app.multi_agent.technical_agent import technical_agent
from app.infrastructure.ai.openai_client import sub_model
# technical_agent: 技术专家智能体。
#
# 它通常负责：
# - 技术咨询
# - 故障分析
# - 使用指导
# - 某些实时资讯（如果它挂了联网工具）
#
# 这里导入它，是为了后续在工具函数里“转交给它处理”。

from app.multi_agent.service_agent import comprehensive_service_agent
# comprehensive_service_agent: 全能业务智能体 / 服务站业务智能体。
#
# 它通常负责：
# - 服务站查询
# - 线下门店查找
# - 导航 / 地图路径规划
# - 地理位置相关业务
#
# 这里同样不是直接自己处理，而是后面封装成工具调用入口。

from app.infrastructure.tools.mcp.mcp_servers import (
    search_mcp_client,
    baidu_mcp_client,
)
from app.config.settings import settings
# search_mcp_client / baidu_mcp_client:
# 这两个 MCP 客户端在这份代码里“当前没有直接使用”。
#
# 从导入关系看，它们大概率已经被 technical_agent 和
# comprehensive_service_agent 自己内部使用或依赖。
#
# 换句话说：
# 当前这个文件只是“做路由分发”，并不直接调这两个 MCP。
#
# 如果这两个变量后续确实没有在本文件里使用，
# 从代码整洁性来说可以删掉这个导入，避免误导阅读者。

from app.infrastructure.logging.logger import logger
# logger: 项目的日志对象。
#
# 这里主要用于记录：
# - 当前用户请求被路由给了哪个专家 Agent
# - 路由时带了什么 query
#
# 这种日志对多 Agent 架构特别重要，
# 因为后续排查问题时，你需要知道：
# - 问题到底被分给了谁
# - 分发路径是否正确

# 这组关键词用于把“强依赖当前时间/最新外部数据”的问题识别为实时资讯类，
# 避免这类问题先去查本地知识库。
REALTIME_QUERY_KEYWORDS = (
    "今天",
    "今日",
    "最新",
    "刚刚",
    "现在",
    "实时",
    "股价",
    "汇率",
    "天气",
    "气温",
    "新闻",
    "比分",
    "版本号",
    "发布会",
    "热搜",
    "股票",
    "price",
    "weather",
    "news",
    "score",
    "version",
)

KNOWLEDGE_MISS_MARKERS = (
    "未检索到任何相关的文档",
    "无法提供回复",
    "未找到",
    "没有相关",
    "无相关",
)

TECHNICAL_UNAVAILABLE_MARKERS = (
    "当前技术专家服务暂时不可用",
    "技术专家暂时无法回答",
    "请稍后再试",
)

technical_fallback_agent = Agent(
    name="通用技术回退专家",
    instructions="""
你是一名资深中文技术支持工程师。

你的职责：
1. 当知识库未命中，且联网/外部工具不可用时，直接基于通用技术常识回答常见电脑、系统、软件、硬件、安装、排障、操作类问题。
2. 优先给出清晰、可执行、分步骤的中文说明。
3. 不要说“当前服务不可用”“请稍后再试”“无法提供帮助”这类保守话术，除非问题本身确实缺少关键条件无法继续。
4. 如果问题属于通用技术操作，直接给出步骤；如果存在风险点，要简短提醒。
5. 如果你不确定某个强时效事实，就明确说“以下为通用做法”，不要伪造最新数据。

回答要求：
- 使用简洁、专业、面向中文用户的表述
- 操作步骤用有序列表
- 不要提及知识库、工具调用、MCP、模型或系统内部实现
""".strip(),
    model=sub_model,
    model_settings=ModelSettings(temperature=0),
)


def _looks_like_realtime_query(query: str) -> bool:
    normalized_query = (query or "").lower()
    return any(keyword.lower() in normalized_query for keyword in REALTIME_QUERY_KEYWORDS)


async def _query_knowledge_base(query: str) -> dict:
    async with httpx.AsyncClient(trust_env=False) as client:
        response = await client.post(
            url=f"{settings.KNOWLEDGE_BASE_URL}/query",
            json={"question": query},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()


def _extract_knowledge_answer(payload: dict) -> str | None:
    if not isinstance(payload, dict):
        return None

    answer = (payload.get("answer") or "").strip()
    if not answer:
        return None

    if any(marker in answer for marker in KNOWLEDGE_MISS_MARKERS):
        return None

    return answer


def _looks_like_unavailable_answer(answer: str) -> bool:
    normalized_answer = (answer or "").strip()
    if not normalized_answer:
        return True
    return any(marker in normalized_answer for marker in TECHNICAL_UNAVAILABLE_MARKERS)


async def _run_general_technical_fallback(query: str) -> str:
    logger.info("[Route] 启用通用技术回退专家")
    result = await Runner.run(
        technical_fallback_agent,
        input=query,
        run_config=RunConfig(tracing_disabled=True),
    )
    return result.final_output


# ==============================================================================
# 1. 定义技术专家智能体工具
# ==============================================================================
@function_tool
async def consult_technical_expert(
    query: str,
) -> str:
    """
    【咨询与技术专家】处理技术咨询、设备故障、维修建议以及实时资讯（如股价、新闻、天气）。
    当用户询问：
    1. "怎么修"、"为什么坏了"、"如何操作"等技术问题。
    2. "今天股价"、"现在天气"等实时信息。
    请调用此工具。

    Args:
        query: 用户的原始问题或完整指令。
    """
    # 这个函数的本质不是“自己处理技术问题”，
    # 而是把技术问题转交给 technical_agent 去处理。
    #
    # 所以它更像一个“路由型工具 / 委派型工具”。
    #
    # 为什么要这么设计？
    # 因为上层总控 Agent 不一定自己具备所有领域知识和工具，
    # 它可以通过 function_tool 调用这个函数，
    # 再由这个函数去运行一个更专业的子 Agent。
    #
    # 这就是典型的：
    # Agent -> Tool -> Another Agent
    #
    # 也叫：
    # “把专家智能体包装成总控智能体可调用的工具”。

    try:
        logger.info(f"[Route] 转交技术专家: {query[:30]}...")
        # 记录一条日志，说明当前请求被路由给了技术专家。
        #
        # query[:30] 的意思是只截取用户问题前 30 个字符，
        # 这样做通常是为了：
        # - 日志更简洁
        # - 避免整段超长 query 撑爆日志
        # - 保留足够的上下文线索用于排查
        #
        # 例如用户问：
        # “我电脑开机蓝屏，出现 xxx 错误怎么办”
        # 日志里可能只记录前 30 个字符。

        # 技术类问题先确定性查询知识库，避免完全依赖模型是否主动调用工具。
        if not _looks_like_realtime_query(query):
            try:
                logger.info("[Route] 技术问题先查询知识库")
                knowledge_payload = await _query_knowledge_base(query)
                knowledge_answer = _extract_knowledge_answer(knowledge_payload)
                if knowledge_answer:
                    logger.info("[Route] 知识库命中，直接返回知识库结果")
                    return knowledge_answer
                logger.info("[Route] 知识库未命中，回退技术专家智能体")
            except Exception as knowledge_error:
                logger.warning(
                    f"[Route] 知识库预查询失败，继续回退技术专家智能体: {knowledge_error}"
                )
        else:
            logger.info("[Route] 识别为实时资讯问题，跳过知识库预查询")

        # 直接透传用户指令，不要做任何加工
        result = await Runner.run(
            technical_agent,
            input=query,
            run_config=RunConfig(tracing_disabled=True),
        )
        # Runner.run(...):
        # 真正执行 technical_agent。
        #
        # 参数解释：
        # 1. technical_agent
        #    指定用“技术专家智能体”来处理这次请求。
        #
        # 2. input=query
        #    把当前工具接收到的 query 原样透传给 technical_agent。
        #
        #    这里注释“不要做任何加工”非常关键。
        #    说明你的设计原则是：
        #    - 路由层只负责转发
        #    - 不篡改用户原始意图
        #    - 不在中间做二次改写
        #
        #    这样做的好处：
        #    - 避免路由层误伤语义
        #    - 保留原始上下文
        #    - 降低中间层引入偏差的风险
        #
        # 3. run_config=RunConfig(tracing_disabled=True)
        #    表示本次运行关闭 tracing。
        #
        #    这样可以减少链路追踪开销或避免输出过多调试信息。

        final_output = result.final_output
        if not _looks_like_realtime_query(query) and _looks_like_unavailable_answer(
            final_output
        ):
            logger.warning("[Route] 技术专家返回保守兜底话术，改走通用技术回退专家")
            return await _run_general_technical_fallback(query)

        return final_output
        # final_output: 技术专家智能体执行后的最终输出。
        #
        # 当前这个工具函数最终返回的不是一个复杂对象，
        # 而是一个字符串结果，方便上层 Agent 继续消费。

    except Exception as e:
        # 如果 technical_agent 在执行过程中失败，
        # 例如：
        # - 模型调用失败
        # - 工具调用失败
        # - MCP 连接失败
        # - 参数异常
        # 就进入这里。
        logger.error(f"[Route] 技术专家执行异常: {e}")
        if not _looks_like_realtime_query(query):
            try:
                return await _run_general_technical_fallback(query)
            except Exception as fallback_error:
                logger.error(f"[Route] 通用技术回退专家执行失败: {fallback_error}")
        return f"技术专家暂时无法回答: {str(e)}"
        # 返回兜底文案，而不是把异常继续往外抛。
        #
        # 这样做的目的通常是：
        # - 保证上层 Agent 工具调用不会因为一个子 Agent 报错而直接崩掉
        # - 用自然语言把失败信息包起来，便于上层继续处理
        #
        # 不过要注意：
        # 当前是把原始异常字符串直接暴露给最终结果，
        # 在生产环境里有时会泄露内部实现细节。
        # 更稳妥的做法通常是：
        # - 日志里记录详细异常
        # - 返回给用户更通用的错误提示


# ==============================================================================
# 2. 定义全能业务智能体工具
# ==============================================================================
@function_tool
async def query_service_station_and_navigate(
    query: str,
) -> str:
    """
    【服务站专家】处理线下服务站查询、位置查找和地图导航需求。
    当用户询问：
    1. "附近的维修点"、"找小米之家"（服务站查询）。
    2. "怎么去XX"、"导航到XX"（路径规划）。
    3. 任何涉及地理位置和线下门店的请求。
    请调用此工具。

    Args:
        query: 用户的原始问题（包含隐含的位置信息）。
    """
    # 这个工具与 consult_technical_expert 的结构几乎一致，
    # 区别只是：
    # - 它转交的对象不是技术专家
    # - 而是业务/服务站/地图方向的专家 Agent
    #
    # 所以这里也是一个“代理型工具”：
    # 不自己完成业务，而是委派给 comprehensive_service_agent。

    try:
        logger.info(f"[Route] 转交业务专家: {query[:30]}...")
        # 记录一条“路由到业务专家”的日志。
        #
        # 多 Agent 场景里这类日志特别重要，
        # 因为用户问题是否被正确分派，往往决定最终回答质量。

        result = await Runner.run(
            comprehensive_service_agent,
            input=query,
            run_config=RunConfig(tracing_disabled=True),
        )
        # Runner.run(...):
        # 用 comprehensive_service_agent 去处理这个 query。
        #
        # 也就是说：
        # - 当前函数只是一个上层暴露给总控 Agent 的工具入口
        # - 真正干活的是 comprehensive_service_agent
        #
        # 该 Agent 可能在内部进一步：
        # - 调本地服务站查询工具
        # - 调地图 MCP
        # - 做路线规划
        # - 做 POI 检索
        #
        # 这一层相当于把复杂业务能力封装起来，对外只暴露一个统一入口。

        return result.final_output
        # 返回业务专家智能体最终生成的结果字符串。

    except Exception as e:
        # 业务智能体执行失败时的兜底逻辑。
        return f"业务专家暂时无法回答: {str(e)}"
        # 和技术专家类似，这里把异常包装成自然语言字符串返回。
        #
        # 好处是上层不会直接崩。
        # 风险是异常信息可能过于技术化，不够适合直接暴露给最终用户。


# ==============================================================================
# 3. 将两个工具暴露出去
# ==============================================================================
AGENT_TOOLS = [
    consult_technical_expert,
    query_service_station_and_navigate,
]
# AGENT_TOOLS: 对外暴露的工具列表。
#
# 这个列表的意义通常是：
# 让上层“总控 Agent / 路由 Agent / 协调 Agent”统一拿到这些工具。
#
# 例如某个更高层的总控 Agent 可以这样注册：
# tools=AGENT_TOOLS
#
# 然后总控 Agent 在处理用户请求时，就能根据语义决定：
# - 调 consult_technical_expert
# - 还是调 query_service_station_and_navigate
#
# 所以这份代码的角色，不是具体做业务，而是：
# “把多个专家 Agent 封装成统一可调用的工具集合”。
