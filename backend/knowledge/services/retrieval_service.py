import logging
import jieba
import re

# 配置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from typing import List, Dict, Any
from langchain_core.documents import Document
from backend.knowledge.repositories.vector_store_repository import (
    VectorStoreRepository,
)
from backend.knowledge.services.ingestion.ingestion_processor import (
    IngestionProcessor,
)
from backend.knowledge.utils.markdown_utils import MarkDownUtils
from backend.knowledge.config.settings import settings
from sklearn.metrics.pairwise import cosine_similarity


class RetrievalService:
    """
    检索服务类（检索器）

    这个类是整个 RAG 检索阶段的核心组件，主要负责：
    1. 根据用户问题，从知识库里找出候选文档
    2. 通过多路召回的方式提高召回率
    3. 对候选文档重新排序，提高最终返回结果的准确率

    当前设计采用的是“两路召回 + 去重 + 重排”的思路：

    第一路：
        基于向量相似度的语义检索
        - 优点：能理解“意思相近”的问法
        - 缺点：有时标题明确匹配但语义向量不一定能稳定召回

    第二路：
        基于标题关键词匹配的检索
        - 优点：对于标题命中非常强，比如“联想手机K900常见问题汇总”
        - 缺点：只靠词匹配，可能缺少语义泛化能力

    为什么要两路召回？
        因为单一路检索容易漏召回：
        - 纯向量检索可能会“语义被稀释”
        - 纯关键词检索可能无法理解同义表达
        所以这里把两种方法结合起来，提升召回效果。

    注释中提到的“父子块”思想：
        - 小块：适合做 embedding，语义更聚焦
        - 大块：适合给大模型看，信息更完整
        实际上就是一种“检索精度”和“上下文完整度”的平衡策略。
    """

    def __init__(self):
        """
        初始化检索服务

        self.chroma_vector:
            向量库仓储对象，负责：
            - 文本向量化
            - 向量检索

        self.spliter:
            文档处理器对象，这里主要复用其中的文本切分器，
            用于对长文档做 chunk 切分
        """
        self.chroma_vector = VectorStoreRepository()
        self.spliter = IngestionProcessor()
    # 在 Python 里，函数名前面加 _，通常是在告诉别人：这个函数是内部用的，不建议在类外部或模块外部直接调用。
    def rough_ranking(
        self, user_query, mds_metadata: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        对 Markdown 文件标题进行“粗排”

        粗排的目标：
            先快速从所有文档标题中筛出一批“看起来比较相关”的候选文档，
            作为下一步精排的输入。

        这里采用两种匹配方式：
        1. 字符级匹配
        2. 词项级匹配（jieba 分词）

        最终分数 = 词项分数 * 权重 + 字符分数 * 权重

        为什么这样设计？
        - 字符级匹配：对中文很有用，哪怕分词效果一般，也能有一定鲁棒性
        - 词项级匹配：能够更好反映关键词层面的重合度
        - 两者结合：兼顾稳定性和语义粒度

        Args:
            user_query: 用户输入的问题
            mds_metadata: 所有 md 文件的元数据列表
                每个元素通常包含：
                {
                    "title": 文档标题,
                    "path": 文档路径
                }

        Returns:
            List[Dict[str, Any]]:
                返回加上粗排得分后的元数据列表，并按分数倒序取前 50 个
        """

        # 1. 如果用户问题为空，直接返回空列表
        if not user_query:
            return []

        # 词项级匹配在最终分数中的权重
        # 因为相对于字符级，词项级更能反映真实关键词语义
        ROUGHIN_WORD_WEIGHT = 0.7

        # 2. 遍历所有 markdown 文件元数据，给每个标题打一个粗排分数
        for md_metadata in mds_metadata:
            # 2.1 获取当前文档标题
            md_metadata_title = md_metadata["title"]

            # 2.2 如果标题不存在或为空白，则跳过
            # 这里理论上应该写成：
            # if not md_metadata_title or not md_metadata_title.strip():
            # 你的原代码逻辑我保留不动，只做讲解
            if not md_metadata_title and not md_metadata_title.strip():
                continue

            # ==========================
            # 2.3.1 字符级匹配
            # ==========================
            # 将用户问题和标题都转为字符集合
            # 比如：
            # “电脑开机黑屏” -> {'电','脑','开','机','黑','屏'}
            user_query_char = set(user_query)
            md_metadata_title_char = set(md_metadata_title)

            # 并集：所有出现过的字符
            unique_char = user_query_char | md_metadata_title_char

            # 使用 Jaccard 相似度：
            # 交集大小 / 并集大小
            char_score = (
                len(user_query_char & md_metadata_title_char) / len(unique_char)
                if len(unique_char) > 0
                else 0
            )

            # ==========================
            # 2.3.2 词项级匹配
            # ==========================
            # 使用 jieba 进行中文分词
            user_query_word = set(jieba.lcut(user_query))
            md_metadata_title_word = set(jieba.lcut(md_metadata_title))

            # 词项并集
            unique_word = user_query_word | md_metadata_title_word

            # 同样使用 Jaccard 相似度
            word_score = (
                len(user_query_word & md_metadata_title_word) / len(unique_word)
                if len(unique_word) > 0
                else 0
            )

            # ==========================
            # 2.3.3 合成粗排分数
            # ==========================
            # 更偏向词项级匹配，因此词项分数权重更高
            roughing_score = word_score * ROUGHIN_WORD_WEIGHT + char_score * (
                1 - ROUGHIN_WORD_WEIGHT
            )

            # 将粗排分数写回当前文档元数据
            md_metadata["roughing_score"] = float(roughing_score)

        # 3. 按粗排分数倒序排序，只保留前 50 个候选标题
        # 这样可以减少后续精排的计算开销
        return sorted(mds_metadata, key=lambda x: x["roughing_score"], reverse=True)[
            :50
        ]

    def fine_ranking(
        self, user_query: str, rough_mds_metadata: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        对粗排后的标题进行“精排”

        精排阶段比粗排更重，因为要调用 embedding 模型进行向量化，
        然后再用 cosine_similarity 计算问题和标题之间的语义相似度。

        最终精排分数 = 粗排分数 * 0.3 + 语义相似度 * 0.7

        为什么还要保留粗排分数？
        - 粗排分数反映“标题表面命中程度”
        - 语义分数反映“标题语义接近程度”
        两者结合，排序更稳

        Args:
            user_query: 用户当前问题
            rough_mds_metadata: 粗排后的 md 元数据列表

        Returns:
            List[Dict[str, Any]]:
                带精排分数的元数据列表，最终取前 5 个
        """

        # 1. 如果粗排后没有候选文档，直接返回空
        if not rough_mds_metadata:
            return []

        # 2. 对用户问题做向量化
        # 结果通常是一维向量，例如 [0.12, 0.03, ...]
        query_embedding = self.chroma_vector.embedd_document(user_query)

        # 3. 提取粗排标题列表
        roughing_title = [md_metadata["title"] for md_metadata in rough_mds_metadata]

        # 4. 对所有候选标题做批量向量化
        roughing_title_embeddings = self.chroma_vector.embedd_documents(roughing_title)

        # 5. 计算“用户问题向量” 和 “候选标题向量” 的余弦相似度
        # cosine_similarity 返回二维矩阵，这里 flatten() 转为一维数组
        # 比如：[0.1, 0.4, 0.01, 0.6, 0.3]
        similarity = cosine_similarity(
            [query_embedding],
            roughing_title_embeddings,
        ).flatten()

        # 粗排分数权重
        ROUGH_HEIGHT = 0.3
        # 语义相似度权重
        SIM_HEIGHT = 0.7

        # 6. 遍历每一个粗排候选文档，计算最终精排分数
        for index, md_metadata in enumerate(rough_mds_metadata):

            # a. 获取当前标题与问题的语义相似度
            sim = similarity[index]

            # 理论上余弦相似度可能为负值，这里负值直接归 0
            if sim < 0:
                sim = 0

            # b. 获取粗排分数
            roughing_score = md_metadata["roughing_score"]

            # c. 计算最终分数
            final_score = roughing_score * ROUGH_HEIGHT + sim * SIM_HEIGHT

            # d. 写回元数据
            md_metadata["sim_score"] = sim
            md_metadata["final_score"] = final_score

        # 7. 按最终得分倒序排序，只保留前 5 个
        sim_mds_metadata = sorted(
            rough_mds_metadata, key=lambda x: x["final_score"], reverse=True
        )[:5]

        # 8. 返回精排结果
        return sim_mds_metadata

    def retrieval(self, user_question: str) -> List[Document]:
        """
        核心检索入口方法

        这是整个检索流程的统一入口，完整步骤如下：

        1. 第一路召回：向量检索
           - 从向量库中根据语义找到相似文档

        2. 第二路召回：标题检索
           - 根据文件标题做关键词和语义匹配，再读取对应文件内容

        3. 合并两路召回结果

        4. 去重
           - 防止同一文档从不同召回路径重复出现

        5. 重排
           - 按与用户问题的相关度重新排序

        6. 返回最终 Top-N 文档

        Args:
            user_question: 用户输入的问题

        Returns:
            List[Document]:
                最终返回给后续问答模块的候选文档列表
        """

        # 1. 第一路检索：基于向量库的语义检索
        # 优点：能理解语义相近的问题表达
        based_vector_candidates = self._search_based_vector(user_question)

        # 2. 第二路检索：基于标题匹配的检索
        # 优点：对标题命中的问题更敏感
        based_title_candidates = self._search_based_title(user_question)

        # 3. 合并两路召回结果
        total_candidates = based_vector_candidates + based_title_candidates

        # 4. 去重，避免同一文档重复进入最终排序
        unique_candidates = self._deduplicate(total_candidates)

        # 5. 对去重后的候选文档重新计算相关度并排序
        top_documents = self._reranking(unique_candidates, user_question)

        # 6. 返回最终结果
        return top_documents

    def _search_based_vector(self, user_question: str) -> List[Document]:
        """
        第一路检索：基于向量相似度的语义检索

        流程：
        1. 对用户问题做向量化
        2. 在向量数据库中查找相似文档
        3. 返回召回的文档对象列表

        Args:
            user_question: 用户输入的问题

        Returns:
            List[Document]:
                基于向量相似度召回的文档列表
        """

        # 1. 调用向量库查询，返回（文档, 分数）列表
        documents_with_score = self.chroma_vector.search_similarity_with_score(
            user_question
        )

        # 2. 当前逻辑中暂时不使用向量库原始得分，只取文档对象
        # 因为后面还会统一做 reranking
        based_vector_candidates = []
        for document, _ in documents_with_score:
            based_vector_candidates.append(document)

        return based_vector_candidates

    def _search_based_title(self, user_query: str) -> List[Document]:
        """
        第二路检索：基于标题的关键词/语义匹配检索

        处理流程：
        1. 收集 crawl 输出目录中的所有 markdown 文件元数据
        2. 对标题做粗排（分词 + 字符匹配）
        3. 对粗排结果做精排（embedding + cosine similarity）
        4. 根据筛出的标题读取对应文档内容
        5. 如果文档较短，直接封装成 Document
        6. 如果文档较长，则切分后再选择相似 chunk

        Args:
            user_query: 用户输入的问题

        Returns:
            List[Document]:
                基于标题匹配召回出来的文档列表
        """

        # 1. 收集指定目录下所有 markdown 文件的元数据
        # 一般会包含 title / path 等字段
        mds_metadata = MarkDownUtils.collect_md_metadata(settings.CRAWL_OUTPUT_DIR)

        # 2. 标题匹配
        # 2.1 先粗排：快速过滤明显不相关的标题
        rough_mds_metadata = self.rough_ranking(user_query, mds_metadata)

        # 2.2 再精排：基于向量语义进一步筛选最相关标题
        fine_mds_metadata = self.fine_ranking(user_query, rough_mds_metadata)

        # 3. 读取精排后对应的 markdown 文件内容，构建候选 Document
        based_title_candidates = []
        for fine_md_metadata in fine_mds_metadata:
            try:
                # 3.1 打开文件并读取内容
                with open(fine_md_metadata["path"], "r", encoding="utf-8") as f:
                    content = f.read().strip()

                # 3.2 判断文档长度
                # a. 文档较短：直接作为一个整体 Document
                if len(content) < 3000:
                    doc = Document(
                        page_content=content,
                        metadata={
                            "path": fine_md_metadata["path"],
                            "title": fine_md_metadata["title"],
                        },
                    )
                    based_title_candidates.append(doc)

                # b. 文档较长：进行切分，再从切分后的 chunk 中选出最相关的几个
                else:
                    doc_chunks = self._deal_long_title_content(
                        content, fine_md_metadata, user_query
                    )

                    # extend 表示把 doc_chunks 中的多个元素逐个加入列表
                    based_title_candidates.extend(doc_chunks)

            except Exception as e:
                logger.error(f"打开文件失败:{e}")
                return []

        # 4. 返回标题检索得到的候选文档列表
        return based_title_candidates

    def _deduplicate(self, total_candidates: List[Document]) -> List[Document]:
        """
        对合并后的候选文档列表进行去重

        为什么需要去重？
        - 同一个文档可能会被“向量检索”和“标题检索”同时召回
        - 如果不去重，会影响后续重排质量，甚至导致重复内容被返回给模型

        当前去重策略：
        使用一个 key 来判断是否重复：
            (title, 内容前100个字符)

        为什么不用整篇内容？
        - 整篇内容太长，去重成本高
        - 前100个字符通常已经足够作为“近似唯一标识”

        另外，这里会先清理掉开头注入的“文档来源:xxx”前缀，
        避免影响重复判断。

        Args:
            total_candidates: 两路召回合并后的 Document 列表

        Returns:
            List[Document]:
                去重后的唯一文档列表
        """

        # 1. 没有候选文档则直接返回
        if not total_candidates:
            return []

        # 2. seen 用来记录已经出现过的文档 key
        seen = set()
        unique_candidates = []

        # 3. 遍历每一个候选文档
        for document in total_candidates:
            # 清理掉文档开头的“文档来源:xxx”标记
            # 这样做是为了避免仅仅因为注入了标题信息而影响去重逻辑
            clean_content = re.sub(
                r"^文档来源:.*?(?=(\n|#))", "", document.page_content, flags=re.DOTALL
            ).strip()

            # 以（标题 + 内容前100个字符）作为去重 key
            key = (document.metadata["title"], clean_content[:100])

            # 如果没见过，则加入结果集
            if key not in seen:
                seen.add(key)
                unique_candidates.append(document)

        # 4. 返回去重后的文档列表
        return unique_candidates

    def _reranking(
        self, unique_candidates: List[Document], user_question: str
    ) -> List[Document]:
        """
        对去重后的候选文档进行重排（reranking）

        注意这里的逻辑：
        - 第二路“长文档切分召回”的 chunk，在 _deal_long_title_content 中已经算过 similarity
          所以这里可以直接使用它的已有分数
        - 第一路向量检索得到的文档、第二路的短文档，还没有统一分数
          所以这里再统一计算一次与用户问题的相似度

        这样做的目的：
        - 不重复计算已经有分数的长文档 chunk
        - 对其他文档统一打分，保证排序公平

        Args:
            unique_candidates: 去重后的候选文档列表
            user_question: 用户输入的问题

        Returns:
            List[Document]:
                最终按相关度排序后的 Top-N 文档
        """

        # 1. 如果候选文档为空，直接返回空列表
        if not unique_candidates:
            return []

        # 需要重新做 embedding 打分的文档
        need_embedding_docs = []

        # 对应文档在 unique_candidates 中的索引
        need_embedding_candidates_indices = []

        # 最终的（文档, 分数）列表
        score_doc = []

        # 2. 遍历候选文档，分两类处理
        for candidate_index, unique_candidate in enumerate(unique_candidates):
            # 2.1 如果当前文档本身就是第二路长文档切分出来的 chunk，
            # 并且已经带有 similarity 分数，那么直接使用它
            if (
                "chunk_index" in unique_candidate.metadata
                and "similarity" in unique_candidate.metadata
            ):
                score_doc.append(
                    (unique_candidate, unique_candidate.metadata["similarity"])
                )

            # 2.2 否则说明它还没有最终可比较的相关度，需要重新计算
            else:
                need_embedding_docs.append(unique_candidate)
                need_embedding_candidates_indices.append(candidate_index)

        # 3. 对需要重新算分的文档进行统一打分
        if need_embedding_docs:
            # 3.1 先把用户问题向量化
            query_embedding = self.chroma_vector.embedd_document(user_question)

            # 3.2 准备要向量化的文档内容
            # 这里把“文档来源:标题”拼接进去，是为了让标题信息也参与语义表示
            # 这样在计算相似度时，文档标题的语义能辅助排序
            embedding_docs_content = [
                "文档来源:" + doc.metadata["title"] + doc.page_content
                for doc in need_embedding_docs
            ]

            # 3.3 批量生成这些文档的向量
            doc_embeddings = self.chroma_vector.embedd_documents(embedding_docs_content)

            # 3.4 计算用户问题与这些文档的余弦相似度
            similarity = cosine_similarity([query_embedding], doc_embeddings).flatten()

            # 3.5 组装为（文档, 分数）列表
            for idx, candidate_index in enumerate(need_embedding_candidates_indices):
                score_doc.append((unique_candidates[candidate_index], similarity[idx]))

        # 4. 按分数倒序排序
        sorted_docs = sorted(score_doc, key=lambda x: x[1], reverse=True)

        # 5. 只返回前 2 个最相关文档
        # 这里相当于最终 Top-N = 2
        return [doc for doc, _ in sorted_docs[:2]]

    def _deal_long_title_content(
        self, content: str, fine_md_metadata: Dict[str, Any], user_query: str
    ) -> List[Document]:
        """
        处理“标题匹配召回的长文档”

        当某个 markdown 文件很长时，不适合把整篇文档直接作为一个候选：
        - 文档太长，向量表示容易稀释语义
        - 后续给 LLM 也会占用太多上下文窗口

        所以这里采用：
        1. 先对长文档切分成多个 chunk
        2. 给每个 chunk 注入标题信息
        3. 对每个 chunk 向量化
        4. 计算 chunk 与用户问题的相似度
        5. 取最相关的 3 个 chunk 作为最终候选

        这是一个很典型的“长文档细粒度召回”策略。

        Args:
            content: 长文档全文内容
            fine_md_metadata: 该文档对应的元数据（title/path 等）
            user_query: 用户问题

        Returns:
            List[Document]:
                从长文档中筛出的高相关 chunk 列表
        """

        # 1. 使用切分器对长文档进行 chunk 切分
        # 切分策略通常由 IngestionProcessor 中的 document_spliter 决定
        chunks = self.spliter.document_spliter.split_text(content)

        # 2. 获取当前长文档的标题
        doc_chunks_title = fine_md_metadata["title"]

        # 3. 将标题注入每个 chunk 的内容前面
        # 这样做的原因：
        # - chunk 本身可能缺乏全局语义
        # - 加上标题后，能补充 chunk 的主题信息
        # 注意：这里与后面 reranking 的拼接格式最好保持一致
        doc_chunks_inject_title = [
            f"文档来源:{doc_chunks_title}" + doc_chunk for doc_chunk in chunks
        ]

        # 4. 对用户问题向量化
        query_embedding = self.chroma_vector.embedd_document(user_query)

        # 5. 对每个注入标题后的 chunk 批量向量化
        doc_chunk_embeddings = self.chroma_vector.embedd_documents(
            doc_chunks_inject_title
        )

        # 6. 计算每个 chunk 与用户问题之间的余弦相似度
        doc_chunks_similarity = cosine_similarity(
            [query_embedding], doc_chunk_embeddings
        ).flatten()

        # 7. 取相似度最高的 3 个 chunk 索引
        # argsort() 是升序，所以先取最后 3 个，再逆序变成从高到低
        # 如果按从小到大排序，原来这些值的索引顺序是什么
        top_doc_chunks_indices = doc_chunks_similarity.argsort()[-3:][::-1]

        # 8. 构造最终 Document 对象列表
        docs = []
        for i, chunk_idx in enumerate(top_doc_chunks_indices):
            doc = Document(
                # page_content 保留注入标题后的内容，方便后续统一语义理解
                page_content=doc_chunks_inject_title[chunk_idx],
                metadata={
                    "path": fine_md_metadata["path"],
                    "title": fine_md_metadata["title"],
                    # 这里标记 chunk 在原文中的索引位置
                    # 注意：你原代码里 key 写成了 "chunk_index:" 带冒号
                    "chunk_index:": int(chunk_idx),
                    # 记录当前 chunk 与用户问题的相似度
                    "similarity": float(doc_chunks_similarity[chunk_idx]),
                },
            )
            docs.append(doc)

        return docs


if __name__ == "__main__":
    # 测试入口
    # 直接运行该文件时，会实例化一个检索服务对象，并执行一次检索测试
    retrival_service = RetrievalService()
    #
    # # 下面这些是不同测试问题示例，你可以按需打开
    # rough_ranking_result = retrival_service.rough_ranking(
    #     "我的电脑开机之后没有任何的反应",
    #     MarkDownUtils.collect_md_metadata(settings.CRAWL_OUTPUT_DIR),
    # )
    # for roughing_result in rough_ranking_result[:10]:
    #     print(f"粗排---{roughing_result}")
    #
    # sim_ranking_result = retrival_service.fine_ranking(
    #     "我的电脑开机之后没有任何的反应",
    #     rough_ranking_result[:10],
    # )
    #
    # for sim_result in sim_ranking_result:
    #     print(f"精排---{sim_result}")
    #
    result = retrival_service.retrieval("我的电脑开机之后没有任何的反应")
    # result = retrival_service.retrieval("如何安装联想的一件影音")
    # result = retrival_service.retrieval("联想手机K900常见问题汇总有哪些")
    # result = retrival_service.retrieval("如何使用U盘安装Windows 7操作系统.")
    # result = retrival_service.retrieval("开机屏幕黑屏或蓝屏报错,无法正常进入系统怎么办")
    # result = retrival_service.retrieval("我的电脑经常死机该如何解决")

    # # 当前测试问题
    # result = retrival_service.retrieval("手机、平板上的画面能无线传输到电视上播放吗")
    #
    # 打印最终检索结果
    for r in result:
        print(r)
