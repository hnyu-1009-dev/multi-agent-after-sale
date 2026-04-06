import os
import re
from typing import List, Dict, Any


class MarkDownUtils:
    """
    Markdown 文档处理工具类

    这个工具类主要负责处理 Markdown 文件相关的通用逻辑，例如：
    1. 扫描指定目录，收集所有 Markdown 文件的基础元数据
    2. 从文件路径或文件名中提取文档标题
    3. 对 Markdown 文本做简单清洗，例如提取图片链接

    这类工具方法通常不依赖实例状态，因此适合定义为静态方法。
    """

    @staticmethod
    def collect_md_metadata(folder_path: str) -> List[Dict[str, Any]]:
        """
        收集指定目录下所有 Markdown 文件的元数据

        功能说明：
        - 遍历 folder_path 目录
        - 找出所有以 .md 结尾的文件
        - 从文件名中提取标题
        - 组装为统一的元数据列表返回

        为什么需要这个方法？
        在知识库检索场景中，很多时候我们需要先拿到所有文档的基础信息，
        比如：
        - 文档路径（后面读取文件内容要用）
        - 文档标题（后面做标题匹配、粗排、精排要用）

        返回的数据结构通常类似这样：
        [
            {
                "path": "D:/docs/0430-联想手机K900常见问题汇总.md",
                "title": "联想手机K900常见问题汇总"
            },
            {
                "path": "D:/docs/0440-如何安装Windows7.md",
                "title": "如何安装Windows7"
            }
        ]

        标题提取规则：
        1. 如果文件名符合 “编号-标题.md” 格式
           例如：
               0430-联想手机K900常见问题汇总.md
           则提取 “联想手机K900常见问题汇总” 作为标题

        2. 如果文件名不符合上述规则
           则直接使用去掉扩展名后的文件名作为标题

        Args:
            folder_path: Markdown 文件所在目录路径

        Returns:
            List[Dict[str, Any]]:
                每个元素都是一个字典，包含：
                - path: 文件完整路径
                - title: 文件标题
        """

        # 用于存放最终收集到的 Markdown 文件元数据
        md_metadata = []

        # 如果目录不存在，直接返回空列表
        # 这样可以避免 os.listdir(folder_path) 报错
        if not os.path.exists(folder_path):
            return md_metadata

        # 正则表达式：匹配“编号-标题.md”这类文件名
        #
        # 解释：
        # ^           -> 匹配字符串开始
        # (.+?)       -> 非贪婪匹配前半段（一般当作编号部分）
        # -           -> 中间的连接符 "-"
        # (.*?)       -> 非贪婪匹配后半段（作为标题部分）
        # \.md$       -> 以 .md 结尾
        #
        # 例如：
        #   0430-联想手机K900常见问题汇总.md
        # 会匹配出：
        #   group(1) = 0430
        #   group(2) = 联想手机K900常见问题汇总
        filename_pattern = re.compile(r"^(.+?)-(.*?)\.md$")

        # 遍历目录下所有文件名
        for filename in os.listdir(folder_path):
            # 只处理 Markdown 文件
            if filename.endswith(".md"):

                # 使用正则判断文件名是否符合“编号-标题.md”格式
                match = filename_pattern.match(filename)

                if match:
                    # 如果匹配成功，则取第 2 组作为标题
                    # 第 2 组即 "-" 后面 ".md" 前面的那部分内容
                    title = match.group(2).strip()
                else:
                    # 如果不符合该格式，则直接使用文件名（去掉 .md 后缀）作为标题
                    title = os.path.splitext(filename)[0].strip()

                # 将当前文件的路径和标题作为一个字典加入结果列表
                md_metadata.append(
                    {"path": os.path.join(folder_path, filename), "title": title}
                )

        # 返回收集到的所有 Markdown 文件元数据
        return md_metadata

    @staticmethod
    def extract_title(file_path: str) -> str:
        """
        从文件路径中提取 Markdown 文件标题

        功能说明：
        该方法的逻辑与 collect_md_metadata 中的标题提取逻辑保持一致，
        只是这里是针对“单个文件路径”进行处理。

        使用场景：
        - 已经拿到某个文件路径，想单独提取它的标题
        - 避免重复写“文件名解析逻辑”

        标题提取规则：
        1. 文件名如果符合 “编号-标题.md” 格式，
           则返回 “标题” 部分
        2. 否则返回去掉后缀后的文件名

        例如：
            file_path = "D:/docs/0430-联想手机K900常见问题汇总.md"
            返回：联想手机K900常见问题汇总

            file_path = "D:/docs/说明文档.md"
            返回：说明文档

        Args:
            file_path: 文件完整路径

        Returns:
            str: 提取出的标题字符串
        """

        # 从完整路径中取出文件名
        # 例如：
        # D:/docs/0430-联想手机K900常见问题汇总.md
        # -> 0430-联想手机K900常见问题汇总.md
        filename = os.path.basename(file_path)

        # 定义与 collect_md_metadata 相同的文件名匹配规则
        filename_pattern = re.compile(r"^(.+?)-(.*?)\.md$")

        # 尝试匹配“编号-标题.md”格式
        match = filename_pattern.match(filename)

        if match:
            # 如果匹配成功，则提取正则分组中的第 2 部分作为标题
            return match.group(2).strip()
        else:
            # 如果匹配失败，则直接返回去掉后缀的文件名
            return os.path.splitext(filename)[0].strip()

    def clean_markdown_images(text: str) -> str:
        """
        清理 Markdown 文本中的图片语法，将其替换为纯图片链接

        原始 Markdown 图片语法通常是：
            ![图片描述](https://example.com/abc.png)

        这个方法的目标是将它替换成：
            https://example.com/abc.png

        并且让每张图片链接单独占一行，便于后续：
        - 文本清洗
        - 文档切分
        - 向量化处理
        - 检索时保留图片资源地址

        为什么需要这样做？
        因为 Markdown 图片语法本身对 embedding 模型意义不大，
        但图片 URL 有时候可以作为附加信息保留下来。

        处理示例：

        输入：
            这是一个图片 ![示例图](https://xxx.com/a.png) 后面还有文字

        输出：
            这是一个图片
            https://xxx.com/a.png
            后面还有文字

        Args:
            text: 原始 Markdown 文本内容

        Returns:
            str: 清洗后的文本
        """

        # 匹配 Markdown 图片语法
        #
        # 正常 Markdown 图片格式是：
        # ![描述](url)
        #
        # 这里的目标是捕获其中的 URL 部分：
        # match.group(1) -> 图片链接
        #
        # 注意：
        # 你这里的正则写法比较特殊：
        # r'!\$$[^$$]*\]\((https?://[^\s\)]+)\)'
        # 从意图上看，是想匹配 Markdown 图片并抓取 URL。
        # 如果后续你发现图片没有正常替换，很可能需要检查这个正则是否符合你的实际文本格式。
        pattern = r"!\$$[^$$]*\]\((https?://[^\s\)]+)\)"

        def replace_func(match):
            """
            re.sub 的替换函数

            每次匹配到一个 Markdown 图片时，会调用这个函数。
            这里我们只保留图片 URL，并在前后加换行，
            目的是让每张图片链接单独占一行。
            """
            url = match.group(1)
            return f"\n{url}\n"

        # 用替换函数对所有 Markdown 图片进行替换
        cleaned = re.sub(pattern, replace_func, text)

        # 将连续 3 个及以上换行压缩为 2 个换行
        # 避免替换后文本出现过多空行，影响阅读和后续切分
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # 去掉首尾空白字符并返回
        return cleaned.strip()
