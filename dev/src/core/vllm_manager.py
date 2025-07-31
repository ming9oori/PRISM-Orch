"""
vLLM 엔진 관리 클래스
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import List

from vllm import SamplingParams
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
import torch
import psutil
import GPUtil
from fastapi import HTTPException

from ..models.schemas import InferenceRequest, InferenceResponse, BatchRequest, SystemStatus

logger = logging.getLogger(__name__)


class VLLMManager:
    """vLLM 엔진 관리 클래스"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-large", 
                 tensor_parallel_size: int = 1,
                 max_model_len: int = 4096,
                 gpu_memory_utilization: float = 0.9):
        
        self.model_name = model_name
        self.tensor_parallel_size = tensor_parallel_size
        self.max_model_len = max_model_len
        self.gpu_memory_utilization = gpu_memory_utilization
        
        self.engine = None
        self.is_loaded = False
        self.request_count = 0
        self.active_requests = 0
        self.total_tokens_generated = 0
        self.start_time = time.time()
        
        # 에이전트별 시스템 프롬프트
        self.system_prompts = {
            "orchestration": """당신은 제조업 현장의 AI 오케스트레이션 시스템입니다.
사용자의 자연어 질의를 분석하여 적절한 에이전트 조합과 실행 계획을 수립하세요.
응답은 JSON 형식으로 구조화하여 제공하세요.""",

            "monitoring": """당신은 제조 공정 모니터링 전문가입니다.
센서 데이터와 이상 탐지 결과를 분석하여 현장 작업자가 이해하기 쉬운 
명확한 설명, 원인 분석, 위험도 평가, 권장 조치를 제공하세요.""",

            "prediction": """당신은 제조 공정 예측 분석 전문가입니다.
예측 모델의 결과를 해석하여 신뢰도, 불확실성, 위험 시나리오, 
권장 제어 액션을 현장에서 이해하기 쉬운 언어로 설명하세요.""",

            "control": """당신은 제조 공정 자율제어 전문가입니다.
제어 의사결정의 근거, 예상 효과, 잠재적 부작용, 대안을 설명하고
안전성을 최우선으로 고려한 제어 액션을 추천하세요."""
        }
    
    async def initialize(self):
        """vLLM 엔진 초기화"""
        try:
            logger.info(f"Initializing vLLM engine with model: {self.model_name}")
            
            # 엔진 설정
            engine_args = AsyncEngineArgs(
                model=self.model_name,
                tensor_parallel_size=self.tensor_parallel_size,
                max_model_len=self.max_model_len,
                gpu_memory_utilization=self.gpu_memory_utilization,
                disable_log_stats=True,
                enforce_eager=False,  # CUDA 그래프 사용으로 성능 향상
                max_num_seqs=256,     # 높은 동시성 지원
                max_num_batched_tokens=8192,  # 배치 처리 최적화
            )
            
            # 비동기 엔진 생성
            self.engine = AsyncLLMEngine.from_engine_args(engine_args)
            self.is_loaded = True
            
            logger.info("vLLM engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vLLM engine: {e}")
            raise
    
    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        """텍스트 생성"""
        if not self.is_loaded:
            raise HTTPException(status_code=500, detail="Model not loaded")
        
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            self.active_requests += 1
            self.request_count += 1
            
            # 시스템 프롬프트와 사용자 프롬프트 결합
            system_prompt = self.system_prompts.get(request.agent_type, "")
            
            if request.context:
                context_str = "\n".join([f"{k}: {v}" for k, v in request.context.items()])
                full_prompt = f"{system_prompt}\n\n컨텍스트:\n{context_str}\n\n사용자: {request.prompt}\n\n응답:"
            else:
                full_prompt = f"{system_prompt}\n\n사용자: {request.prompt}\n\n응답:"
            
            # 샘플링 파라미터 설정
            sampling_params = SamplingParams(
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                max_tokens=request.max_tokens,
                stop=request.stop or ["사용자:", "\n\n사용자:"],
                skip_special_tokens=True,
            )
            
            # 생성 요청
            results = []
            async for output in self.engine.generate(
                full_prompt, 
                sampling_params, 
                request_id
            ):
                results.append(output)
            
            # 마지막 결과 추출
            final_output = results[-1]
            generated_text = final_output.outputs[0].text.strip()
            tokens_generated = len(final_output.outputs[0].token_ids)
            
            # 통계 업데이트
            self.total_tokens_generated += tokens_generated
            response_time = time.time() - start_time
            
            return InferenceResponse(
                request_id=request_id,
                agent_type=request.agent_type,
                response=generated_text,
                tokens_generated=tokens_generated,
                response_time=response_time,
                timestamp=datetime.now(),
                model_name=self.model_name
            )
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        
        finally:
            self.active_requests -= 1
    
    async def batch_generate(self, batch_request: BatchRequest) -> List[InferenceResponse]:
        """배치 생성"""
        if len(batch_request.requests) > batch_request.batch_size:
            raise HTTPException(
                status_code=400, 
                detail=f"Batch size too large (max {batch_request.batch_size})"
            )
        
        # 병렬로 모든 요청 처리
        tasks = [self.generate(req) for req in batch_request.requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 성공한 결과만 반환
        successful_results = []
        for result in results:
            if isinstance(result, InferenceResponse):
                successful_results.append(result)
            else:
                logger.error(f"Batch generation error: {result}")
        
        return successful_results
    
    def get_system_status(self) -> SystemStatus:
        """시스템 상태 조회"""
        memory_info = psutil.virtual_memory()
        gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
        
        # GPU 메모리 정보
        gpu_memory = {}
        if gpu_count > 0:
            try:
                gpus = GPUtil.getGPUs()
                for i, gpu in enumerate(gpus):
                    gpu_memory[f"gpu_{i}_memory_used"] = gpu.memoryUsed
                    gpu_memory[f"gpu_{i}_memory_total"] = gpu.memoryTotal
                    gpu_memory[f"gpu_{i}_utilization"] = gpu.load * 100
            except:
                pass
        
        # 처리량 계산 (tokens/sec)
        uptime = time.time() - self.start_time
        throughput = self.total_tokens_generated / uptime if uptime > 0 else 0
        
        return SystemStatus(
            status="healthy" if self.is_loaded else "loading",
            model_loaded=self.is_loaded,
            gpu_count=gpu_count,
            memory_usage={
                "ram_used_gb": memory_info.used / (1024**3),
                "ram_total_gb": memory_info.total / (1024**3),
                "ram_percent": memory_info.percent,
                **gpu_memory
            },
            active_requests=self.active_requests,
            total_requests=self.request_count,
            uptime=uptime,
            throughput=throughput
        ) 