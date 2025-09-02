import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

# 이 파일의 위치가 .../PRISM-Orch/src/core/config.py 이므로,
# 프로젝트 루트 디렉토리는 3단계 상위 경로가 됩니다.
project_root = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    """
    PRISM-Orch 애플리케이션 설정을 담는 클래스입니다.
    .env 파일이나 환경 변수로부터 값을 불러옵니다.
    """
    # Server Configuration
    APP_BASE_URL: str = "http://localhost:8100"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8100
    RELOAD: bool = False

    # vLLM (OpenAI-Compatible) Configuration
    OPENAI_BASE_URL: str = "http://localhost:8001/v1"
    VLLM_MODEL: str = "Qwen/Qwen3-14B"
    OPENAI_API_KEY: str = "EMPTY"

    # PRISM-Core API Configuration (Orch → Core 호출용)
    PRISM_CORE_BASE_URL: str = "http://localhost:8000"

    # Vector DB Configuration (Weaviate) - Single instance for all tools
    WEAVIATE_URL: str = "http://localhost:18080"
    WEAVIATE_API_KEY: str = ""

    # Vector Encoder Configuration
    VECTOR_ENCODER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIM: int = 384

    # Hugging Face Token (for model downloads)
    HUGGING_FACE_TOKEN: str = "your_hugging_face_token_here"
    
    # Local storage paths
    VECTOR_DB_PATH: str = str(project_root / "data" / "vector_db")
    AGENT_MEMORY_DB_PATH: str = str(project_root / "data" / "agent_memory.db")
    LOG_FILE_PATH: str = str(project_root / "logs" / "orchestration.log")

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