import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

# 이 파일의 위치가 .../PRISM-Orch/src/core/config.py 이므로,
# 프로젝트 루트 디렉토리는 3단계 상위 경로가 됩니다.
project_root = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    """
    애플리케이션 설정을 담는 클래스입니다.
    .env 파일이나 환경 변수로부터 값을 불러옵니다.
    """
    # API Keys
    OPENAI_API_KEY: str = "dummy-key-not-used-in-mock-mode"
    OPENAI_BASE_URL: Optional[str] = None
    VLLM_MODEL: Optional[str] = None
    MODEL_NAME: Optional[str] = None  # MODEL_NAME도 지원

    # PRISM-Core base URL (Orch -> Core HTTP API)
    PRISM_CORE_BASE_URL: str = "http://localhost:8000"

    # Vector DB endpoints (prism-core Weaviate)
    RESEARCH_WEAVIATE_URL: str = "http://localhost:8080"
    RESEARCH_WEAVIATE_API_KEY: str = ""
    MEMORY_WEAVIATE_URL: str = "http://localhost:8080"
    MEMORY_WEAVIATE_API_KEY: str = ""

    # Vector encoder configuration (used by RAGSearchTool and seeding)
    VECTOR_ENCODER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIM: int = 384
    
    # Local storage paths
    VECTOR_DB_PATH: str = str(project_root / "data" / "vector_db")
    AGENT_MEMORY_DB_PATH: str = str(project_root / "data" / "agent_memory.db")
    LOG_FILE_PATH: str = str(project_root / "logs" / "orchestration.log")

    # Application Settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    RELOAD: bool = True

    # Pydantic-settings 설정
    model_config = SettingsConfigDict(
        env_file=project_root / ".env",  # .env 파일 경로 지정
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # .env 파일에 정의되지 않은 필드는 무시
    )

# 설정 객체 생성
settings = Settings()

# 설정에 지정된 경로에 디렉토리가 없는 경우 생성
Path(settings.VECTOR_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(settings.AGENT_MEMORY_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
Path(settings.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True) 