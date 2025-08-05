# core/config.py

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    QDRANT_URL: str = Field("http://localhost:6333", env="QDRANT_URL")
    QDRANT_COLLECTION: str = Field("docs", env="QDRANT_COLLECTION")
    EMBEDDING_SIZE: int = Field(384, env="EMBEDDING_SIZE")
    CONTEXT_STORE_BACKEND: str = Field("memory", env="CONTEXT_STORE_BACKEND")
    CONTEXT_STORE_URL: str = Field("sqlite:///context.db", env="CONTEXT_STORE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

