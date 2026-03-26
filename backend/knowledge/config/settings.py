from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):



    # Default directories
    # Using 'data/crawl' as the default location for markdown files
    # Text splitting configuration
    CHUNK_SIZE: int = 3000
    CHUNK_OVERLAP: int = 200

    # Retrieval configuration
    TOP_ROUGH: int = 50
    TOP_FINAL: int = 5

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
