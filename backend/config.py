from pydantic_settings import BaseSettings
from typing import Optional

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_URL = f"sqlite:///{(BASE_DIR / 'healthcare.db').as_posix()}"

class Settings(BaseSettings):
    DATABASE_URL: str = DEFAULT_DATABASE_URL
    OPENAI_API_KEY: Optional[str] = None
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    class Config:
        env_file = ".env"


settings = Settings()
