from joblib.testing import raises
from langsmith import expect

from backend.knowledge.config.settings import settings
from http.client import HTTPException

import requests


class KnowledgeApiClient:
    """
    主要提供一个方法 获取网络知识
    """

    @staticmethod
    def fetch_knowledge_content(knowledge_no: int) -> str:
        """
        根据知识库编号 获取联想知识库内容
        :return:
        """
        try:
            # 1.定义URL
            # https://iknow.lenovo.com.cn/knowledgeapi/api/knowledge/knowledgeDetails?knowledgeNo=1
            knowledge_base_url=f"{settings.KNOWLEDGE_BASE_URL}/knowledgeapi/api/knowledge/knowledgeDetails"

            # 2.定义param
            params = {"knowledgeNo": knowledge_no}

            # 3.发送请求
            response = requests.get(url=knowledge_base_url, params=params, timeout=10)
            response.raise_for_status()
            # 4.得到结果(知识库内容)
            response_dict = response.json()

            # 获取data
            return response_dict['data']

        except HTTPException as e:
            raise HTTPException(f"发送知识库请求失败：{e}")


if __name__ == "__main__":
    knowledge_content = KnowledgeApiClient.fetch_knowledge_content(knowledge_no=1)
    print(f"知识库数据内容：\n{knowledge_content}")
