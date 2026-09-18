from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Study Companion"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173", # Vite default
        "http://localhost:5174", # Vite fallback (if 5173 is in use)
        "http://localhost:3000", # React default backup
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://study-pulse-murex.vercel.app", # Deployed Vercel Frontend
        "https://studypulse-1-wkfc.onrender.com", # Deployed Render Backend
    ]
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "ai_study_companion"
    
    # JWT Configuration
    JWT_SECRET: str = "super_secret_placeholder_do_not_use_in_prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Phase 3 PDF & Embedding Configuration
    MAX_PDF_SIZE_MB: int = 25
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "prototype-64d"
    STORAGE_DIR: str = "storage/materials"
    
    # Phase 5 AI Tutor & LLM Configuration
    GROQ_API_KEY: str = ""
    HF_API_KEY: str = ""
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "qwen/qwen3.8-27b"
    TUTOR_RETRIEVAL_TOP_K: int = 5
    TUTOR_RETRIEVAL_THRESHOLD: float = 0.0
    
    # Phase 6 Assessment Configuration
    QUIZ_DEFAULT_QUESTION_COUNT: int = 5
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
