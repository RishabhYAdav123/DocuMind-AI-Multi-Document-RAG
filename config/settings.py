from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    llm_provider: Literal["gemini"] = "gemini"
    google_api_key: SecretStr = SecretStr("")
    llm_model: str = "gemini-3.5-flash-lite"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = Field(5, ge=1, le=20)
    chunk_size: int = Field(1000, ge=100, le=4000)
    chunk_overlap: int = Field(200, ge=0)
    min_similarity: float = Field(0.30, ge=-1, le=1)
    max_file_mb: int = Field(20, ge=1, le=100)
    max_documents: int = Field(20, ge=1, le=100)
    max_pages: int = Field(500, ge=1, le=2000)
    max_chunks: int = Field(10000, ge=1, le=50000)
    history_turns: int = Field(6, ge=1, le=20)
    timeout_seconds: int = Field(45, ge=1, le=120)
    llm_min_interval_seconds: float = Field(0, ge=0, le=60)

    @model_validator(mode="after")
    def validate_overlap(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self
