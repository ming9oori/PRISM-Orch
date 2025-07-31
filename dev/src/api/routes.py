"""
API 라우터 및 엔드포인트
"""

import logging
import uuid
from datetime import datetime

import torch
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request

from ..models.schemas import InferenceRequest, InferenceResponse, BatchRequest, SystemStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root(request: Request):
    """루트 엔드포인트"""
    vllm_manager = getattr(request.app.state, 'vllm_manager', None)
    return {
        "message": "vLLM High-Performance Inference Server", 
        "status": "running",
        "model": vllm_manager.model_name if vllm_manager else "loading"
    }


@router.get("/health", response_model=SystemStatus)
async def health_check(request: Request):
    """헬스 체크"""
    vllm_manager = getattr(request.app.state, 'vllm_manager', None)
    if not vllm_manager:
        raise HTTPException(status_code=503, detail="Server not ready")
    
    return vllm_manager.get_system_status()


@router.post("/api/v1/generate", response_model=InferenceResponse)
async def generate_text(
    inference_request: InferenceRequest,
    background_tasks: BackgroundTasks,
    request: Request
):
    """단일 텍스트 생성"""
    vllm_manager = getattr(request.app.state, 'vllm_manager', None)
    if not vllm_manager:
        raise HTTPException(status_code=503, detail="Server not ready")
    
    try:
        response = await vllm_manager.generate(inference_request)
        
        # 백그라운드 로깅
        background_tasks.add_task(log_request, inference_request, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/batch_generate")
async def batch_generate_text(batch_request: BatchRequest, request: Request):
    """배치 텍스트 생성"""
    vllm_manager = getattr(request.app.state, 'vllm_manager', None)
    if not vllm_manager:
        raise HTTPException(status_code=503, detail="Server not ready")
    
    try:
        responses = await vllm_manager.batch_generate(batch_request)
        
        return {
            "batch_id": str(uuid.uuid4()),
            "total_requests": len(batch_request.requests),
            "successful": len(responses),
            "failed": len(batch_request.requests) - len(responses),
            "results": responses
        }
        
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/models")
async def get_model_info(request: Request):
    """모델 정보"""
    vllm_manager = getattr(request.app.state, 'vllm_manager', None)
    if not vllm_manager:
        raise HTTPException(status_code=503, detail="Server not ready")
    
    return {
        "current_model": vllm_manager.model_name,
        "tensor_parallel_size": vllm_manager.tensor_parallel_size,
        "max_model_len": vllm_manager.max_model_len,
        "supported_agents": list(vllm_manager.system_prompts.keys()),
        "gpu_count": torch.cuda.device_count(),
        "is_loaded": vllm_manager.is_loaded
    }


@router.get("/api/v1/stats")
async def get_statistics(request: Request):
    """성능 통계"""
    vllm_manager = getattr(request.app.state, 'vllm_manager', None)
    if not vllm_manager:
        raise HTTPException(status_code=503, detail="Server not ready")
    
    status = vllm_manager.get_system_status()
    
    return {
        "requests": {
            "total": vllm_manager.request_count,
            "active": vllm_manager.active_requests,
            "completed": vllm_manager.request_count - vllm_manager.active_requests
        },
        "performance": {
            "throughput_tokens_per_sec": status.throughput,
            "total_tokens_generated": vllm_manager.total_tokens_generated,
            "uptime_seconds": status.uptime,
            "average_tokens_per_request": (
                vllm_manager.total_tokens_generated / vllm_manager.request_count 
                if vllm_manager.request_count > 0 else 0
            )
        },
        "system": {
            "gpu_count": status.gpu_count,
            "memory_usage": status.memory_usage
        }
    }


async def log_request(request: InferenceRequest, response: InferenceResponse):
    """요청 로깅"""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "request_id": response.request_id,
        "agent_type": request.agent_type,
        "prompt_length": len(request.prompt),
        "response_length": len(response.response),
        "tokens_generated": response.tokens_generated,
        "response_time": response.response_time,
        "model_name": response.model_name
    }
    
    logger.info(f"Request processed: {log_data}") 