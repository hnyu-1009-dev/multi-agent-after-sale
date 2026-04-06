import re
# re: Python 正则表达式模块。
#
# 这里主要用于在最终结果落库前，对模型输出做一次简单清洗：
# - 把多个连续换行压缩成单个换行
#
# 这样可以避免最终保存的 assistant 回复里出现过多空行。

import traceback
# traceback: 用于获取完整异常堆栈信息。
#
# 和 str(e) 只拿到异常简短描述不同，
# traceback.format_exc() 能拿到更完整的报错链路，
# 对排查问题很有帮助。

from collections.abc import AsyncGenerator
# AsyncGenerator: 异步生成器类型。
#
# 这个类型说明当前函数不是一次性 return 一个结果，
# 而是会在执行过程中持续 yield 多个分片结果。
#
# 这非常适合流式输出场景，例如 SSE / 流式聊天响应。

from agents.run import Runner, RunConfig
# Runner: Agent 运行器，负责真正执行 Agent。
# RunConfig: 一次运行时的配置，例如是否关闭 tracing。

from app.multi_agent.orchestrator_agent import orchestrator_agent
# orchestrator_agent: 主调度智能体。
#
# 它是整个多 Agent 系统的总控入口：
# - 负责理解用户问题
# - 负责做任务路由
# - 负责选择调用哪个专家工具
#
# 当前 MultiAgentService 真正驱动执行的就是它。

from app.schemas.request import ChatMessageRequest
# ChatMessageRequest: 请求体的数据模型。
#
# 通常会封装：
# - request.query：用户当前问题
# - request.context.user_id：当前用户 ID
# - request.context.session_id：当前会话 ID
#
# 这样业务层拿到的不是一堆零散参数，而是结构化请求对象。

from app.services.session_service import session_service
# session_service: 会话历史服务。
#
# 负责：
# - 读取历史对话
# - 追加当前用户输入
# - 裁剪上下文
# - 保存 assistant 回复
#
# 这样当前 MultiAgentService 不需要自己操作文件或 JSON。

from app.services.stream_response_service import process_stream_response
# process_stream_response: 流式响应处理器。
#
# 它接收 Runner.run_streamed(...) 返回的流式结果对象，
# 然后把 Agent 执行过程中的事件转换成前端可消费的 chunk。
#
# 也就是说：
# Agent 内部事件流 --> 业务层 chunk --> SSE / 前端流式展示

from app.utils.response_util import ResponseFactory
# ResponseFactory: 响应构造工具。
#
# 这里主要用于在异常场景下构造统一格式的输出消息，
# 例如：
# - 系统错误提示
# - 自动重试提示

from app.infrastructure.logging.logger import logger
# logger: 项目日志对象。
#
# 用于记录：
# - 处理流程中的异常
# - 详细堆栈信息


from app.schemas.response import ContentKind
# ContentKind: 响应内容类型枚举/定义。
#
# 这里在异常提示和重试提示里用到 ContentKind.PROCESS，
# 表示这是“过程信息”，不是最终正文回答。


class MultiAgentService:
    """
    多智能体业务服务类

    这个类的职责不是定义某个 Agent，
    而是把一次“用户请求处理流程”完整串起来。

    核心流程包括：
    1. 从请求中提取用户上下文
    2. 准备历史会话
    3. 运行主调度 Agent
    4. 把 Agent 的流式事件转成前端可消费的数据
    5. 在结束后保存历史消息
    6. 异常时输出统一错误提示，并支持一次自动重试

    todo:
        process_task 方法前面加上 async 以及返回值类型一定是 AsyncGenerator
    """

    @classmethod
    async def process_task(
        cls, request: ChatMessageRequest, flag: bool
    ) -> AsyncGenerator:
        """
        多智能体处理任务入口

        Args:
            request: 请求上下文对象，包含用户信息、会话信息和当前问题
            flag: 是否允许失败后自动重试一次

        Yields:
            AsyncGenerator:
                异步生成器对象，持续产出流式响应分片

        这个方法不是普通 return 结果，
        而是在执行过程中不断 yield 数据给上游。
        所以它特别适合：
        - SSE
        - 流式聊天
        - 前端边收边显示
        """
        try:
            # ------------------------------------------------------------------
            # 1. 获取请求上下文的信息
            # ------------------------------------------------------------------
            user_id = request.context.user_id
            # 当前用户 ID，用于区分不同用户的会话历史。

            session_id = request.context.session_id
            # 当前会话 ID，用于区分同一用户下的不同聊天会话。

            user_query = request.query
            # 当前用户这一次输入的问题文本。
            #
            # 例如：
            # - “电脑蓝屏了怎么办？”
            # - “附近有维修点吗？”
            # - “从回龙观到天安门怎么走？”

            # ------------------------------------------------------------------
            # 2. 准备历史对话
            # ------------------------------------------------------------------
            chat_history = session_service.prepare_history(
                user_id, session_id, user_query
            )
            # prepare_history(...) 会做三件事：
            # 1. 加载这个用户、这个会话已有的历史消息
            # 2. 把当前 user_query 追加到历史中
            # 3. 按最大轮数裁剪上下文
            #
            # 最终得到的是一份“适合发给 Agent / LLM 的上下文消息列表”。
            #
            # 注意：
            # 当前返回的 chat_history 已经包含了本次用户输入。

            # ------------------------------------------------------------------
            # 3. 运行 Agent
            # ------------------------------------------------------------------
            streaming_result = Runner.run_streamed(
                starting_agent=orchestrator_agent,
                input=chat_history,   # 列表形式的历史上下文
                context=user_query,   # 当前问题文本
                max_turns=5,          # 最多允许 Agent 内部进行 5 次迭代
                run_config=RunConfig(tracing_disabled=True),
            )
            # Runner.run_streamed(...):
            # 使用“流式模式”运行主调度智能体。
            #
            # 参数解释：
            #
            # 1. starting_agent=orchestrator_agent
            #    指定从哪个 Agent 开始执行。
            #    当前就是你的总控 Agent。
            #
            # 2. input=chat_history
            #    传给 Agent 的主输入是一个“消息列表”。
            #    也就是类似：
            #    [
            #      {"role": "system", "content": "..."},
            #      {"role": "user", "content": "..."},
            #      {"role": "assistant", "content": "..."},
            #      {"role": "user", "content": "当前问题"}
            #    ]
            #
            #    这意味着 Agent 是基于完整对话上下文来工作的。
            #
            # 3. context=user_query
            #    这里又额外传了当前问题文本。
            #
            #    这通常用于：
            #    - 作为额外上下文透传给工具
            #    - 或者在某些框架场景下作为运行上下文信息
            #
            #    简单理解就是：
            #    input 更偏“对话消息”
            #    context 更偏“当前任务上下文”
            #
            # 4. max_turns=5
            #    这里不是“异常重试次数”，而是 Agent 内部最大推理/行动迭代次数。
            #
            #    你注释写得很对：
            #    COT(思考 -> 行动 -> 观察) 最多循环多少轮
            #
            #    例如一轮可能是：
            #    - 模型先思考
            #    - 决定调用一个工具
            #    - 观察工具结果
            #    - 再继续下一轮
            #
            #    设成 5 的目的是防止 Agent 无限循环。
            #
            # 5. run_config=RunConfig(tracing_disabled=True)
            #    本次运行关闭 tracing，减少追踪链路记录。

            # ------------------------------------------------------------------
            # 4. 处理 Agent 的事件流（流式输出）
            # ------------------------------------------------------------------
            async for chunk in process_stream_response(streaming_result):
                yield chunk
            # 这里是整个“流式返回”最关键的一步。
            #
            # process_stream_response(streaming_result) 会：
            # - 监听 Agent 执行过程中的事件
            # - 把这些事件转成前端能消费的流式片段
            #
            # 然后 MultiAgentService 再把这些 chunk 原样 yield 出去。
            #
            # 这样最终上层（例如 SSE 接口）就可以边生成边返回。

            # ------------------------------------------------------------------
            # 5. 获取 Agent 的最终结果
            # ------------------------------------------------------------------
            agent_result = streaming_result.final_output
            # 当整个 Agent 流式执行结束后，
            # final_output 才会包含它最终整理好的完整回答。

            format_agent_result = re.sub(r"\n+", "\n", agent_result)
            # 使用正则把多个连续换行压缩成一个换行。
            #
            # 例如：
            # "\n\n\n你好\n\n世界"
            # 会被整理成：
            # "\n你好\n世界"
            #
            # 这么做的目的是让最终落库存储的 assistant 回复更干净。

            # ------------------------------------------------------------------
            # 6. 存储历史对话
            # ------------------------------------------------------------------
            chat_history.append({"role": "assistant", "content": format_agent_result})
            # 在原有 chat_history 尾部追加一条 assistant 回复。
            #
            # 注意：
            # chat_history 在前面 prepare_history(...) 时已经包含了当前 user 消息，
            # 所以这里再补上 assistant 消息后，
            # 这一轮对话就完整了。

            session_service.save_history(user_id, session_id, chat_history)
            # 把更新后的完整会话历史保存起来。
            #
            # 这样下次同一用户、同一会话再来时，
            # 历史上下文就能被正确加载。

        except Exception as e:
            # ------------------------------------------------------------------
            # 异常处理
            # ------------------------------------------------------------------
            logger.error(f"AgentService.process_query执行出错: {str(e)}")
            # 记录简要错误日志。

            logger.debug(f"异常详情: {traceback.format_exc()}")
            # 记录完整异常堆栈。
            #
            # 这样排查时不仅知道“出错了”，还知道：
            # - 错在哪一层
            # - 是模型调用错了
            # - 还是工具调用错了
            # - 还是会话处理错了

            text = f"❌ 系统错误: {str(e)}"
            yield (
                "data: "
                + ResponseFactory.build_text(
                    text, ContentKind.PROCESS
                ).model_dump_json()
                + "\n\n"
            )
            # 向前端流式输出一条“系统错误提示”。
            #
            # 这里输出格式看起来是 SSE 风格：
            # "data: <json>\n\n"
            #
            # ResponseFactory.build_text(...):
            # 构造一个统一格式的文本响应对象
            #
            # ContentKind.PROCESS:
            # 表示这条消息属于“过程提示信息”，不是最终业务答案。

            # 如果允许重试，则启动重试流程
            if flag:
                text = f"🔄 正在尝试自动重试..."
                yield (
                    "data: "
                    + ResponseFactory.build_text(
                        text, ContentKind.PROCESS
                    ).model_dump_json()
                    + "\n\n"
                )
                # 先向前端发一条“正在自动重试”的过程提示，
                # 让用户知道系统没有直接结束，而是在尝试恢复。

                # 递归调用进行重试
                async for item in MultiAgentService.process_task(request, flag=False):
                    yield item
                # 这里通过递归再次调用 process_task(...) 进行重试。
                #
                # 为什么传 flag=False？
                # 因为你只想自动重试一次。
                #
                # 第一次失败：
                # - flag=True
                # - 触发一次重试
                #
                # 第二次如果还失败：
                # - flag=False
                # - 不再继续无限递归重试
                #
                # 这是一个非常实用的“最多自动补救一次”的设计。