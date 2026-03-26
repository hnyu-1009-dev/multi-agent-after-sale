from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_ENV_FILE = KNOWLEDGE_ROOT / ".env"


class Settings(BaseSettings):
    # 这些字段交给 BaseSettings 在实例化时统一读取。
    # 不再在类定义阶段直接 os.environ.get(...)，避免导入模块时就把错误环境值固定下来。
    API_KEY: str
    BASE_URL: str
    MODEL: str
    EMBEDDING_MODEL: str

    KNOWLEDGE_BASE_URL: str

    VECTOR_STORE_PATH: str = str(KNOWLEDGE_ROOT / "chroma_kb")

    # Default directories
    CRAWL_OUTPUT_DIR: str = str(KNOWLEDGE_ROOT / "data" / "crawl")
    # Using 'data/crawl' as the default location for markdown files
    MD_FOLDER_PATH: str = str(KNOWLEDGE_ROOT / "data" / "crawl")
    TMP_MD_FOLDER_PATH: str = str(KNOWLEDGE_ROOT / "data" / "tmp")
    # Text splitting configuration
    CHUNK_SIZE: int = 3000
    CHUNK_OVERLAP: int = 200

    # Retrieval configuration
    TOP_ROUGH: int = 50
    TOP_FINAL: int = 5

    model_config = SettingsConfigDict(
        env_file=str(KNOWLEDGE_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        """
        knowledge 服务应优先读取 backend/knowledge/.env。
        这样即使同一台机器或同一个进程里已经存在 api 包写入的同名环境变量，
        当前服务实例化配置时仍然会以自己的 .env 为准。
        """
        return (
            init_settings,
            dotenv_settings,
            env_settings,
            file_secret_settings,
        )


settings = Settings()
