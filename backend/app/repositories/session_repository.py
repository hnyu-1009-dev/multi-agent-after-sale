import json

# json: Python 标准库，用于在“Python对象”和“JSON文本”之间做转换。
#
# 这里主要用于：
# 1. 读取会话文件中的 JSON 内容 -> 转成 Python 数据结构
# 2. 把 Python 中的会话数据 -> 序列化成 JSON 文件保存到磁盘

from datetime import datetime

# datetime: 用于处理日期和时间。
#
# 在这里主要用于：
# - 把文件的创建时间戳转换成“人类可读”的时间字符串
#   例如：2026-04-05 20:30:18

from pathlib import Path

# Path: pathlib 提供的现代路径对象。
#
# 相比传统的字符串拼接路径：
#   os.path.join(...)
# Path 的优势是：
# 1. 可读性更好
# 2. 面向对象风格更清晰
# 3. 跨平台路径处理更自然
#
# 例如：
#   self._storage_root / user_id / f"{session_id}.json"
# 比字符串拼接更直观。

from typing import Any, Dict, List, Optional, Tuple, Union

# 这些都是类型标注工具：
#
# Any:
#   表示任意类型
#
# Dict[str, Any]:
#   表示键为字符串、值为任意类型的字典
#
# List[Dict[str, Any]]:
#   表示一个列表，列表中每个元素都是字典
#
# Optional[T]:
#   表示这个值可能是 T，也可能是 None
#
# Tuple[A, B, C]:
#   表示一个固定结构的元组
#
# Union[A, B]:
#   表示这个值可能是 A，也可能是 B

from app.infrastructure.logging.logger import logger

# logger: 项目的日志对象。
#
# 这里用于：
# - 记录用户目录不存在
# - 记录某个会话文件读取失败
# - 记录遍历目录失败
#
# 这样做的意义是：
# 出问题时不仅返回结果，还能在日志中留下排查线索。


class SessionRepository:
    """会话数据仓储类。

    负责处理底层的会话文件存储、读取和文件系统操作。
    使用 pathlib 进行现代化的路径管理。
    """

    # 存储目录名称常量
    STORAGE_DIR_NAME = "user_memories"
    # STORAGE_DIR_NAME: 存储根目录名常量。
    #
    # 这里定义成类常量，而不是在代码里到处写 "user_memories"，
    # 好处是：
    # 1. 避免魔法字符串
    # 2. 后续如果要改目录名，只需要改一个地方
    # 3. 语义更清晰

    def __init__(self):
        """初始化 SessionRepository。

        自动定位并创建存储根目录。
        """

        current_file = Path(__file__).resolve()
        # Path(__file__): 当前这个 Python 文件的路径
        # .resolve(): 解析成绝对路径，避免相对路径歧义
        #
        # 例如可能得到：
        # D:/WorkSystem/xxx/backend/app/.../session_repository.py

        self._base_dir = current_file.parent.parent
        # current_file.parent: 当前文件所在目录
        # current_file.parent.parent: 当前文件上两级目录
        #
        # 这里你的设计意图是：
        # 把“仓储文件位置”往上回溯，定位到一个统一的基础目录。
        #
        # 为什么这么做？
        # 因为你不想把存储目录写成依赖“从哪里启动 Python”的相对路径，
        # 而是基于当前代码文件的位置动态计算。
        #
        # 这样更稳，不容易因为工作目录变化而找错路径。

        # 拼接存储路径: backend/app/user_memories
        self._storage_root = self._base_dir / self.STORAGE_DIR_NAME
        # _storage_root: 所有用户会话文件的根目录。
        #
        # 最终结构大致会是：
        # backend/app/user_memories/
        #   ├─ user_001/
        #   │   ├─ session_a.json
        #   │   └─ session_b.json
        #   └─ user_002/
        #       └─ session_c.json
        #
        # 也就是说：
        # - 第一层按用户分目录
        # - 第二层按 session_id 存 json 文件

        # 确保存储根目录存在
        self._storage_root.mkdir(parents=True, exist_ok=True)
        # mkdir(...):
        # 创建目录。
        #
        # parents=True:
        #   如果父目录不存在，就连父目录一起创建
        #
        # exist_ok=True:
        #   如果目录已经存在，也不要报错
        #
        # 这一步的意义是：
        # 在 SessionRepository 初始化时，先把总存储根目录准备好，
        # 避免后面第一次写文件时才发现根目录不存在。

    def load_session(
        self, user_id: str, session_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """从文件加载会话数据。

        Args:
            user_id: 用户ID。
            session_id: 会话ID。

        Returns:
            List[Dict]: 解析后的会话数据。
            None: 如果文件不存在。

        Raises:
            json.JSONDecodeError: 如果文件内容损坏。
        """
        file_path = self._get_file_path(user_id, session_id)
        # 先通过 user_id + session_id 计算出对应会话文件的完整路径。
        #
        # 例如：
        # user_id = "u123"
        # session_id = "s001"
        #
        # 最终路径可能是：
        # backend/app/user_memories/u123/s001.json

        if not file_path.exists():
            return None
        # 如果文件不存在，直接返回 None。
        #
        # 这里的设计语义是：
        # “没有这个会话文件” 不算异常，而是一种正常情况。
        #
        # 所以这里没有抛错，而是返回 None，
        # 由上层自己判断这是“首次会话”还是“会话丢失”。

        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
        # 以只读模式打开文件，并按 utf-8 编码读取。
        #
        # json.load(f):
        # 直接把文件中的 JSON 内容解析成 Python 对象。
        #
        # 如果文件内容是一个 JSON 数组，例如：
        # [
        #   {"role": "user", "content": "你好"},
        #   {"role": "assistant", "content": "你好，请问有什么可以帮你？"}
        # ]
        #
        # 那返回值就会是一个 Python list。
        #
        # 注意：
        # 如果文件存在，但 JSON 内容损坏，
        # json.load(f) 会抛出 json.JSONDecodeError。
        # 当前函数没有捕获这个异常，而是交给上层处理。
        #
        # 这意味着：
        # - “文件不存在” -> 返回 None
        # - “文件存在但内容坏了” -> 抛异常

    def save_session(
        self, user_id: str, session_id: str, data: List[Dict[str, Any]]
    ) -> None:
        """保存会话数据到文件。

        Args:
            user_id: 用户ID。
            session_id: 会话ID。
            data: 要保存的数据列表。
        """
        file_path = self._get_file_path(user_id, session_id)
        # 根据 user_id 和 session_id 生成目标文件路径。

        # 确保用户的个人目录存在 (懒加载模式)
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
        # file_path.parent: 当前会话文件所在的用户目录。
        #
        # 例如：
        # file_path = .../user_memories/u123/s001.json
        # file_path.parent = .../user_memories/u123
        #
        # 这里采用的是“懒加载模式”：
        # - 不在一开始就为所有用户创建目录
        # - 而是在真正要写某个用户会话时，才创建该用户目录
        #
        # 这样更省资源，也更符合实际使用场景。

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 以写入模式打开目标文件。
        #
        # json.dump(...):
        # 把 Python 对象写成 JSON 文本到文件中。
        #
        # ensure_ascii=False:
        #   让中文直接以中文写入，而不是变成 \u4f60\u597d 这种转义形式
        #
        # indent=2:
        #   使用 2 个空格做缩进，让 JSON 文件更易读
        #
        # 这意味着落盘后的 JSON 不只是“机器能读”，人也比较容易直接打开查看。

    def get_all_sessions_metadata(
        self, user_id: str
    ) -> List[Tuple[str, str, Union[List, Exception]]]:
        """获取用户所有会话的元数据和内容。

        Args:
            user_id: 用户ID。

        Returns:
            List[Tuple]: 包含 (session_id, create_time, data_or_error) 的列表。
        """
        user_dir = self._get_user_directory(user_id)
        # 先拿到该用户对应的目录路径。
        #
        # 例如：
        # backend/app/user_memories/u123

        if not user_dir.exists():
            logger.warning(f"用户目录不存在: {user_id}")
            return []
        # 如果用户目录都不存在，说明这个用户还没有任何会话文件。
        #
        # 这里记录一条 warning 日志，然后返回空列表。
        #
        # 返回空列表而不是抛异常的原因是：
        # “该用户暂时没有会话”通常不是系统错误，而是正常业务情况。

        results = []
        # results: 用来收集所有会话文件的元信息和内容。
        #
        # 最终每个元素的结构是：
        # (session_id, create_time, data_or_error)

        try:
            # 遍历目录下所有 .json 文件
            for file_path in user_dir.glob("*.json"):
                # user_dir.glob("*.json"):
                # 遍历用户目录下所有扩展名为 .json 的文件。
                #
                # 例如：
                # s001.json
                # s002.json
                # s003.json

                session_id = file_path.stem  # 获取文件名不带后缀部分
                # file_path.stem:
                # 取文件名主体，不带扩展名。
                #
                # 例如：
                # s001.json -> s001

                # 获取文件创建时间
                stat = file_path.stat()
                # stat(): 获取文件的元信息，例如：
                # - 创建时间
                # - 修改时间
                # - 文件大小
                # 等等

                create_time = datetime.fromtimestamp(stat.st_ctime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                # stat.st_ctime:
                # 文件创建时间（或某些系统下的元数据变更时间）
                #
                # datetime.fromtimestamp(...):
                # 把时间戳转成 datetime 对象
                #
                # .strftime("%Y-%m-%d %H:%M:%S"):
                # 格式化成字符串，例如：
                # 2026-04-05 21:10:25
                #
                # 这样上层拿到后可以直接展示，而不用再自己格式化。

                try:
                    with file_path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    # 尝试读取并解析当前会话文件。

                    results.append((session_id, create_time, data))
                    # 如果成功，就把：
                    # - session_id
                    # - create_time
                    # - 解析出来的数据
                    # 打包成一个元组放进 results

                except Exception as e:
                    # 读取或解析失败，返回异常对象
                    logger.error(f"读取会话文件 {file_path.name} 失败: {e}")
                    results.append((session_id, create_time, e))
                    # 这里的设计很有意思，也很实用。
                    #
                    # 它没有因为“一个文件坏了”就让整个遍历失败，
                    # 而是：
                    # 1. 记录日志
                    # 2. 把异常对象也放进结果里
                    #
                    # 这样做的好处是：
                    # - 其他正常文件仍然能继续返回
                    # - 上层可以知道“哪一个 session 出问题了”
                    # - 不会因为一条坏数据拖垮整个用户会话列表

        except Exception as e:
            logger.error(f"遍历用户 {user_id} 会话目录失败: {e}")
            return []
        # 这是更外层的一层保护。
        #
        # 如果不是单个文件读取失败，而是整个目录遍历过程都失败了，
        # 比如：
        # - 权限问题
        # - 路径异常
        # - 文件系统异常
        # 就会走到这里。
        #
        # 此时直接记录错误并返回空列表。

        return results
        # 返回所有会话的元信息与内容。
        #
        # 返回结果示意：
        # [
        #   ("s001", "2026-04-05 20:10:00", [...]),
        #   ("s002", "2026-04-05 20:20:00", [...]),
        #   ("s003", "2026-04-05 20:30:00", JSONDecodeError(...)),
        # ]
        #
        # 也就是说：
        # 第三个元素并不一定永远是正常数据，
        # 也可能是异常对象。

    def _get_user_directory(self, user_id: str) -> Path:
        """获取用户的记忆文件夹路径对象。"""
        return self._storage_root / user_id
        # 这是一个内部辅助方法。
        #
        # 输入 user_id，返回该用户目录路径。
        #
        # 例如：
        # _storage_root = backend/app/user_memories
        # user_id = "u123"
        #
        # 返回：
        # backend/app/user_memories/u123
        #
        # 之所以单独抽成方法，是为了：
        # 1. 复用路径拼接逻辑
        # 2. 避免到处写同样的路径规则
        # 3. 后续如果目录结构变了，只需要改一个地方

    def _get_file_path(self, user_id: str, session_id: str) -> Path:
        """获取具体会话文件的路径对象。"""
        return self._get_user_directory(user_id) / f"{session_id}.json"
        # 这是另一个内部辅助方法。
        #
        # 它在“用户目录”的基础上，再拼接出具体的会话文件路径。
        #
        # 例如：
        # user_id = "u123"
        # session_id = "s001"
        #
        # 返回：
        # backend/app/user_memories/u123/s001.json
        #
        # 这个方法让 load/save 等函数不需要自己关心具体路径格式。


# 全局单例
session_repository = SessionRepository()
# 在模块导入时直接创建一个全局唯一实例。
#
# 这样其他模块可以直接：
# from xxx import session_repository
#
# 然后调用：
# session_repository.load_session(...)
# session_repository.save_session(...)
#
# 这种写法的好处是：
# 1. 使用方便
# 2. 避免到处重复实例化
# 3. 存储根目录初始化逻辑只执行一次
#
# 这其实是一种轻量级单例用法。
