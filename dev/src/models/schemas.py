"""
데이터 모델 및 스키마 정의
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    """추론 요청 모델"""
    agent_type: str = Field(..., description="에이전트 타입")
    prompt: str = Field(..., description="입력 프롬프트")
    context: Dict[str, Any] = Field(default={}, description="컨텍스트")
    max_tokens: int = Field(default=2048, description="최대 토큰 수")
    temperature: float = Field(default=0.1, description="생성 온도")
    top_p: float = Field(default=0.9, description="Top-p")
    top_k: int = Field(default=50, description="Top-k")
    stop: Optional[List[str]] = Field(default=None, description="중지 토큰")


class InferenceResponse(BaseModel):
    """추론 응답 모델"""
    request_id: str
    agent_type: str
    response: str
    tokens_generated: int
    response_time: float
    timestamp: datetime
    model_name: str


class BatchRequest(BaseModel):
    """배치 요청 모델"""
    requests: List[InferenceRequest]
    batch_size: int = Field(default=10, description="배치 크기")


class SystemStatus(BaseModel):
    """시스템 상태 모델"""
    status: str
    model_loaded: bool
    gpu_count: int
    memory_usage: Dict[str, float]
    active_requests: int
    total_requests: int
    uptime: float
    throughput: float  # tokens/sec 