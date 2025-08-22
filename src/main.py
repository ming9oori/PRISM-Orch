from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from .core.config import settings
from .api.endpoints import orchestration

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Application startup...")
    yield
    print("INFO:     Application shutdown...")


app = FastAPI(
    title="PRISM-Orch",
    description="자율 제조 구현을 위한 AI 에이전트 오케스트레이션 모듈",
    version="1.0",
    lifespan=lifespan
)

# Routers
app.include_router(orchestration.router, prefix="/api/v1/orchestrate", tags=["Orchestration"])


@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "ok", "message": "Welcome to PRISM-Orch!"}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.RELOAD
    ) 