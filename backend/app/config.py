from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Keys
    openrouter_api_key: str = "your_openrouter_api_key_here"
    
    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    
    # CORS
    allowed_origins: str = "http://localhost:3000"
    
    # OpenRouter
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "qwen/qwen-2.5-coder-32b-instruct:free"  # Best free model for code analysis
    
    # ML Models
    codebert_model: str = "microsoft/codebert-base"
    sentence_transformer_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Sandbox
    sandbox_timeout: int = 30
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: str = "1"
    
    class Config:
        env_file = ".env"          # BUG FIX: was "../.env" which breaks when running from backend/ dir
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
