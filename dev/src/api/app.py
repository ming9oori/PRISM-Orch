"""
FastAPI 애플리케이션 설정
"""

import logging
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core import VLLMManager
from .routes import router

logger = logging.getLogger(__name__)

# 전역 변수
vllm_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global vllm_manager
    
    # 시작 시 vLLM 엔진 초기화
    vllm_manager = VLLMManager(
        model_name="microsoft/DialoGPT-large",  # 필요에 따라 변경
        tensor_parallel_size=torch.cuda.device_count() if torch.cuda.is_available() else 1,
        max_model_len=4096,
        gpu_memory_utilization=0.9
    )
    
    await vllm_manager.initialize()
    logger.info("vLLM Inference Server started successfully")
    
    # 앱에 매니저 등록
    app.state.vllm_manager = vllm_manager
    
    yield
    
    # 종료 시 정리
    logger.info("Shutting down vLLM Inference Server")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    app = FastAPI(
        title="vLLM High-Performance Inference Server",
        description="제조업 Multi-Agent 시스템용 고성능 vLLM 추론 서버",
        version="1.0.0",
        lifespan=lifespan
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 라우터 등록
    app.include_router(router)

    return app 