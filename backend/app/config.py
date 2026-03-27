from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Anti-Fraud Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # LLM
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # Data paths
    data_dir: str = "./data"
    csv_dir: str = "./data/csv"
    chroma_dir: str = "./data/chroma"
    reports_dir: str = "./data/reports"
    blacklist_dir: str = "./data/blacklist"

    # RAG
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    def ensure_dirs(self):
        for d in [self.csv_dir, self.chroma_dir, self.reports_dir, self.blacklist_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
