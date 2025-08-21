import uuid
from fastapi import APIRouter, Body
from typing import Dict, Any

from ..schemas import UserQueryInput, OrchestrationResponse, TaskInfo
from ...orchestration.main import OrchestrationAgent

router = APIRouter()
agent = OrchestrationAgent()

@router.post(
    "/",
    response_model=OrchestrationResponse,
    summary="사용자 질의 기반 오케스트레이션 실행",
    description="사용자의 자연어 질의를 받아 오케스트레이션 플로우를 실행하고 최종 결과를 반환합니다.",
    response_description="오케스트레이션의 최종 결과물",
)
async def run_orchestration(
    query: UserQueryInput = Body(
        ...,
        examples={
            "normal": {
                "summary": "일반적인 분석 요청",
                "value": {"query": "A-1 라인 압력에 이상이 생긴 것 같은데, 원인이 뭐야?"},
            }
        },
    )
) -> OrchestrationResponse:
    return agent.run(query) 