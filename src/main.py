from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from .core.config import settings
from .api.endpoints import orchestration # 라우터 임포트
from .api.endpoints import vector_db as vector_db_endpoints

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션의 시작과 종료 시 수행될 작업을 관리합니다.
    (예: DB 연결, 모델 로딩 등)
    """
    print("INFO:     Application startup...")
    # --- 시작 시 수행할 작업 ---
    # 예: `app.state.db_connection = await connect_to_db()`
    # 예: `app.state.ml_model = load_model()`
    yield
    # --- 종료 시 수행할 작업 ---
    # 예: `await app.state.db_connection.close()`
    print("INFO:     Application shutdown...")


app = FastAPI(
    title="PRISM-Orch",
    description="자율 제조 구현을 위한 AI 에이전트 오케스트레이션 모듈",
    version="1.0",
    lifespan=lifespan
)

# --- 라우터 포함 ---
app.include_router(orchestration.router, prefix="/api/v1/orchestrate", tags=["Orchestration"])
app.include_router(vector_db_endpoints.research_router, prefix="/api/v1/research", tags=["Research Vector DB"]) 
app.include_router(vector_db_endpoints.memory_router, prefix="/api/v1/memory", tags=["Memory Vector DB"]) 
from .api.endpoints import vector_db_tools as vector_db_tools_endpoints
app.include_router(vector_db_tools_endpoints.router, prefix="/api/v1/tools", tags=["Vector DB Tools"]) 
from .api.endpoints import fc_search as fc_search_endpoints
app.include_router(fc_search_endpoints.router, prefix="/api/v1", tags=["Function Calling Search"])
# app.include_router(agent_management.router, prefix="/api/v1/agents", tags=["Agent Management"])


@app.get("/", tags=["Health Check"])
async def read_root():
    """
    시스템의 상태를 확인하기 위한 기본 엔드포인트입니다.
    """
    return {"status": "ok", "message": "Welcome to PRISM-Orch!"}


if __name__ == "__main__":
    """
    개발 환경에서 uvicorn을 사용하여 서버를 직접 실행합니다.
    이 스크립트는 'python -m src.main' 명령어로 실행되어야 합니다.
    """
    uvicorn.run(
        "src.main:app",  # 애플리케이션 경로를 명확하게 지정
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.RELOAD
    ) 