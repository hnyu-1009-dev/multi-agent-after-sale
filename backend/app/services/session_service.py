from json import JSONDecodeError

# JSONDecodeError:
# 当 json 文件内容损坏、格式不合法时，json.load(...) 会抛出这个异常。
# 这里单独导入它，是为了在读取历史会话时做更精确的异常捕获。

from typing import List, Dict, Any

# 类型标注工具：
# - List[Dict[str, Any]] 表示“消息列表”，其中每一条消息都是一个字典
# - 这种结构通常对应：
#   {"role": "user", "content": "你好"}
#   {"role": "assistant", "content": "你好，请问有什么可以帮您？"}

from app.repositories.session_repository import session_repository

# session_repository:
# 底层会话仓储对象，负责真正的文件读写。
#
# SessionService 不直接操作文件系统，而是调用这个仓储层。
# 这是一种典型的“分层设计”：
# - Repository 管数据存取
# - Service 管业务逻辑

from app.infrastructure.logging.logger import logger

# logger: 项目日志对象。
# 用于记录：
# - 会话读取失败
# - 会话保存失败
# - 会话列表中某个文件损坏等情况


class SessionService:
    """
    会话业务管理服务类

    主要负责对用户历史会话的管理，包括：
    1. 准备加载历史对话
    2. 读取历史对话
    3. 存储历史对话
    4. 查询会话列表
    """

    DEFAULT_SESSION_ID = "default_session"
    # DEFAULT_SESSION_ID: 默认会话 ID。
    #
    # 当上层没有传 session_id，或者传了空值时，
    # 系统会自动使用这个默认会话 ID。
    #
    # 这样做的好处是：
    # - 避免 session_id 为空时底层路径拼接出错
    # - 给“未显式指定会话”的场景一个稳定兜底

    def __init__(self):
        """
        初始化会话操作的工具
        """
        self._repo = session_repository
        # 把底层仓储对象挂到当前 Service 上。
        #
        # 这样当前 SessionService 的所有读写操作，
        # 都统一通过 self._repo 来完成。
        #
        # 这样设计的好处：
        # 1. Service 不直接依赖文件细节
        # 2. 后续如果想把 Repository 换成数据库实现，改动范围更小
        # 3. 结构更清晰，职责更单一

    def prepare_history(
        self, user_id: str, session_id: str, user_input: str, max_turn: int = 3
    ) -> List[Dict[str, Any]]:
        """
        准备历史会话：
        加载历史会话 --> 拼接当前用户输入 --> 裁减历史会话 --> 返回最终上下文

        调用时机：
            发送请求给 LLM 之前（Agent 运行之前）

        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            user_input: 当前用户输入
            max_turn: 保留的最大轮数

        Returns:
            List[Dict[str, Any]]: 处理好的上下文消息列表
        """

        # 1. 加载历史会话
        chat_history = self.load_history(user_id, session_id)
        # 这里会去读取当前用户、当前会话已有的历史消息。
        #
        # 如果这是一个新会话，load_history(...) 不会返回空列表，
        # 而是返回一个初始化好的 system 消息结构。

        # 2. 拼接当前用户消息
        chat_history.append({"role": "user", "content": user_input})
        # 这里把“本次最新的用户输入”加到历史消息尾部。
        #
        # 为什么要在发送给 LLM 之前做这一步？
        # 因为模型需要看到：
        # - 之前说过什么
        # - 当前用户又问了什么
        #
        # 只有这样，模型才能基于完整上下文回答。

        # 3. 裁减历史会话
        truncate_history = self._truncate_history(chat_history, max_turn)
        # 这里做上下文裁剪，避免历史消息无限增长。
        #
        # 例如 max_turn=3，通常表示只保留最近 3 轮对话，
        # 再加上 system 消息。
        #
        # 这样做的主要原因：
        # 1. 控制 token 消耗
        # 2. 避免上下文过长
        # 3. 保留“最近最相关”的对话信息

        # 4. 返回历史会话
        return truncate_history
        # 返回的是“即将送给 LLM 的上下文消息列表”，
        # 不是原始完整历史。
        #
        # 也就是说，这个函数更像一个：
        # “构造模型输入上下文”的方法。

    def load_history(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """
        主要负责：加载历史会话（从文件中读取）

        Args:
            user_id: 用户 ID
            session_id: 会话 ID

        Returns:
            List[Dict[str, Any]]: 历史消息列表
        """
        # 1. 判断 session_id 是否为空
        target_session_id = session_id if session_id else self.DEFAULT_SESSION_ID
        # 如果 session_id 为空，就使用默认会话 ID。
        #
        # 这样可以避免：
        # - None
        # - ""
        # - 缺失 session_id
        # 导致底层读取路径异常。

        # 2. 加载
        try:
            session_history = self._repo.load_session(user_id, target_session_id)
            # 调用底层 Repository 读取会话文件。
            #
            # 这里的返回值语义通常是：
            # - 文件不存在 -> None
            # - 文件存在且正常 -> 历史消息列表
            # - 文件损坏 -> 抛 JSONDecodeError

            if session_history is None:
                # 构建一个新的结构（系统指令）
                return self._init_system_msg_instruct(target_session_id)
                # 如果文件不存在，说明这是一个新会话。
                #
                # 这里并没有返回空列表，而是主动初始化一条 system 消息。
                #
                # 这么做的原因是：
                # 后续给 LLM 的消息结构通常希望从一条 system 指令开始，
                # 这样模型一开始就知道：
                # “你是一个带记忆的助手，需要基于当前会话上下文回答。”

            return session_history
            # 如果读取成功，就直接返回完整历史。

        except JSONDecodeError as e:
            logger.error(f"用户 {user_id} 会话 {session_id} 文件读取失败，原因: {e}")
            return [{"role": "system", "content": "用户会话文件读取失败"}]
            # 如果 JSON 文件损坏，说明底层存储已经不可信。
            #
            # 这里的处理策略是：
            # 1. 记录错误日志
            # 2. 返回一条兜底 system 消息
            #
            # 这样不会让整个上层流程直接崩掉。
            #
            # 注意：
            # 这里返回的 system 提示语属于“异常兜底上下文”，
            # 后续模型会在这个基础上继续工作。

    def save_history(
        self, user_id: str, session_id: str, chat_history: List[Dict[str, Any]]
    ):
        """
        保存历史会话

        调用时机：
            调用完 LLM（Agent）之后

        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            chat_history: 要保存的历史消息
                          （角色通常包括：system / user / assistant）
        """

        # 1. 历史会话是否存在
        if chat_history is None:
            return
        # 如果传入的 chat_history 本身就是 None，
        # 说明上游没有准备好可保存的数据。
        #
        # 这里直接返回，相当于“空操作保护”。

        # 2. 处理 session_id
        target_session_id = session_id if session_id else self.DEFAULT_SESSION_ID
        # 和 load_history 中一样，统一处理空 session_id 的情况。

        try:
            self._repo.save_session(user_id, target_session_id, chat_history)
            # 调用底层 Repository 落盘保存。
            #
            # 这里通常会把整个 chat_history 以 JSON 的形式覆盖写入文件。

        except Exception as e:
            logger.error(f"保存用户 {user_id} 会话 {session_id} 文件失败: {str(e)}")
            return
            # 保存失败时：
            # 1. 打日志
            # 2. 不抛异常
            #
            # 这样做的风格是“业务流程优先不中断”。
            #
            # 也就是说，即使保存失败，也不一定让整个接口直接报错。
            # 但缺点是：上层如果不看日志，可能感知不到保存失败。

    def get_all_sessions_memory(self, user_id: str) -> List[Dict[str, Any]]:
        """获取并格式化用户的所有会话列表（用于前端侧边栏展示）。

        Args:
            user_id: 用户唯一标识

        Returns:
            List[Dict]: 按创建时间倒序排列的会话列表

            格式示例:
            [
                {
                    "session_id": "...",
                    "create_time": "...",
                    "memory": [...],
                    "total_messages": 5
                },

            ]
        """

        # 1. 从 Repo 获取原始元数据
        # 类型大致为: List[Tuple[session_id, create_time, data_or_error]]
        raw_sessions = self._repo.get_all_sessions_metadata(user_id)
        # 这里调用底层仓储，把指定用户目录下的所有会话文件都取出来。
        #
        # 注意：
        # 这个返回值不是前端能直接用的格式，
        # 而是底层偏“原始”的数据结构。

        formatted_sessions = []
        # 用来存放整理后的结果，供前端直接使用。

        for session_id, create_time, data_or_error in raw_sessions:
            # 遍历每一个会话文件对应的数据。
            #
            # data_or_error 这个名字很重要，
            # 它说明这个位置拿到的值可能是：
            # - 正常消息列表
            # - 也可能是异常对象

            session_item = {
                "session_id": session_id,
                "create_time": create_time,
            }
            # 先构造一个基础会话项，
            # 把所有会话都必定拥有的字段放进去。

            # 2. 处理可能的读取错误
            #    (隔离异常，防止一个文件损坏导致整个列表挂掉)
            if isinstance(data_or_error, Exception):
                logger.error(f"读取会话 {session_id} 失败: {str(data_or_error)}")
                session_item.update(
                    {
                        "memory": [],
                        "total_messages": 0,
                        "error": "无法读取会话数据",
                    }
                )
                # 如果这个会话文件有问题：
                # - memory 给空列表
                # - total_messages 给 0
                # - 补一个 error 字段
                #
                # 这样前端依然能拿到一条“这个 session 存在但不可读”的信息，
                # 而不是整个列表都失败。

            else:
                # 3. 正常数据处理：过滤 System 消息，只展示用户可见内容
                memory = data_or_error
                # 此时 memory 就是正常的消息列表。

                user_visible_memory = [
                    msg for msg in memory if msg.get("role") != "system"
                ]
                # 过滤掉 system 消息。
                #
                # 为什么要过滤？
                # 因为 system 消息通常是给模型看的，不是给用户看的。
                #
                # 前端侧边栏展示历史时，一般只需要展示：
                # - user
                # - assistant
                #
                # 不希望把内部系统提示词也暴露出去。

                session_item.update(
                    {
                        "memory": user_visible_memory,
                        "total_messages": len(user_visible_memory),
                    }
                )
                # 给当前会话项补上：
                # - 用户可见消息
                # - 消息总数

            formatted_sessions.append(session_item)
            # 把处理好的当前会话加到结果列表。

        # 4. 排序：按时间倒序（最新的在最前）
        formatted_sessions.sort(key=lambda x: x.get("create_time") or "", reverse=True)
        # 这里的目标是让前端侧边栏优先看到最近的会话。
        #
        # reverse=True 表示降序排序：
        # 时间越新，排得越前。
        #
        # 注意：
        # 当前 create_time 是字符串格式，
        # 在 "%Y-%m-%d %H:%M:%S" 这种格式下，字符串排序通常是可行的。

        return formatted_sessions
        # 返回最终格式化好的会话列表，
        # 这是一个更贴近前端需求的输出结构。

    def _init_system_msg_instruct(self, session_id) -> List[Dict[str, Any]]:
        """
        初始化一个带 system 角色的消息结构

        Args:
            session_id: 会话 ID

        Returns:
            List[Dict[str, Any]]
        """
        return [
            {
                "role": "system",
                "content": f"你是一个有记忆的智能体助手，请基于上下文历史会话用户问题（会话ID {session_id}）进行回答。",
            }
        ]
        # 这是一个“新会话初始化器”。
        #
        # 当用户第一次进入一个会话，或者这个 session 对应文件不存在时，
        # 系统会返回这一条初始化 system 消息。
        #
        # 它的作用是：
        # 1. 给模型设定身份
        # 2. 告诉模型这是一个有记忆能力的助手
        # 3. 强化“要结合历史上下文回答”的约束
        #
        # 注意：
        # 这里会把 session_id 也写进 system 提示语中，
        # 相当于把“当前会话标识”显式注入给模型。

    def _truncate_history(
        self, chat_history: List[Dict[str, Any]], max_turn: int = 3
    ) -> List[Dict[str, Any]]:
        """
        裁减指定轮数的消息

        Args:
            chat_history: 当前完整历史消息
            max_turn: 指定最大轮数

        Returns:
            List[Dict[str, Any]]: 最近指定轮数的历史消息
        """

        # 1. 获取 system 角色的消息
        #    无论如何都要保留，通常来说就一条
        system_msg = [msg for msg in chat_history if msg.get("role") == "system"]
        # system 消息是模型的“全局行为约束”，
        # 一般不应该因为上下文裁剪而被丢掉。

        # 2. 获取非 system 角色的消息（user & assistant）
        no_system_msg = [msg for msg in chat_history if msg.get("role") != "system"]
        # 这里把普通对话消息单独拿出来裁剪。
        #
        # 因为真正增长很快的通常是 user / assistant 对话，
        # 而不是 system 消息。

        msg_limit = max_turn * 2
        # 一轮对话通常由两条消息组成：
        # - user 一条
        # - assistant 一条
        #
        # 所以如果 max_turn=3，
        # 理论上最多保留最近 6 条非 system 消息。

        # 3. 裁减非 system 消息列表
        truncate_msg = no_system_msg[-msg_limit:]
        # 从后往前取最近的 msg_limit 条消息。
        #
        # 这意味着：
        # 越新的消息优先保留，
        # 越久远的消息优先被裁掉。

        # 4. 拼接上 system 消息
        final_msg = system_msg + truncate_msg
        # 最终上下文 = system 消息 + 最近若干轮用户/助手对话。
        #
        # 这种拼接方式非常常见，
        # 因为 system 消息通常需要放在最前面。

        # 5. 返回指定轮数的消息
        return final_msg


# 全局单例
session_service = SessionService()
# 创建一个全局唯一的 SessionService 实例。
#
# 好处是：
# - 其他模块可以直接导入使用
# - 不需要到处手动实例化
# - 会话服务入口统一


if __name__ == "__main__":
    # 这里是一个简单的本地测试入口。
    #
    # 直接运行这个文件时，会执行下面的示例代码。

    result1 = session_service.prepare_history("hzk", "666", "你好!")
    # 注意：
    # 这里 prepare_history 的正确调用应当包含 user_input。
    #
    # 原逻辑表示：
    # 1. 加载用户 hzk 在会话 666 中的历史
    # 2. 把“你好!”当作当前用户输入追加进去
    # 3. 返回裁剪后的上下文

    result1.append({"role": "assistant", "content": "您好，请问有什么可以帮助您吗？"})
    # 模拟 Agent 回答完成后，把 assistant 的回复拼到历史里。
    #
    # 这一步通常发生在：
    # - LLM / Agent 返回 final_output 之后

    session_service.save_history("hzk", "666", result1)
    # 把更新后的完整会话历史保存到文件中。
