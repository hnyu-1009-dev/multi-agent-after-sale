import requests

from knowledge.config.settings import settings


class KnowledgeApiClient:
    """Simple HTTP client for remote knowledge content fetching."""

    @staticmethod
    def fetch_knowledge_content(knowledge_no: int) -> str:
        try:
            knowledge_base_url = (
                f"{settings.KNOWLEDGE_BASE_URL}/knowledgeapi/api/knowledge/knowledgeDetails"
            )
            response = requests.get(
                url=knowledge_base_url,
                params={"knowledgeNo": knowledge_no},
                timeout=10,
            )
            response.raise_for_status()
            response_dict = response.json()
            return response_dict["data"]
        except requests.RequestException as e:
            raise RuntimeError(f"知识库请求失败: {e}") from e


if __name__ == "__main__":
    knowledge_content = KnowledgeApiClient.fetch_knowledge_content(knowledge_no=1)
    print(f"知识内容:\n{knowledge_content}")
