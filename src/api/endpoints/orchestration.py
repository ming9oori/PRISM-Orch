import uuid
from fastapi import APIRouter, Body
from typing import Dict, Any

from ..schemas import UserQueryInput, OrchestrationResponse, TaskInfo

router = APIRouter()

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
    """
    오케스트레이션 메인 로직입니다. 이 엔드포인트는 다음과 같은 작업을 수행합니다.
    (현재는 전체 플로우를 모방한 목업 데이터를 반환합니다)

    1.  **사용자 질의 분석 (NLP)**: 사용자의 의도와 주요 개체를 파악합니다.
    2.  **과업 계획 수립 (Planning)**: 의도를 달성하기 위한 구체적인 과업(Task)들을 정의하고 순서를 정합니다.
    3.  **에이전트 할당 및 실행**: 각 과업에 가장 적합한 에이전트를 할당하고 실행을 요청합니다.
    4.  **결과 종합 및 반환**: 에이전트들의 결과를 종합하여 사용자에게 최종 답변을 생성하고 반환합니다.

    - **query**: 사용자의 질의와 세션 정보가 담긴 입력 모델.
    - **return**: 최종 답변, 플로우 차트, 근거 데이터 등이 포함된 오케스트레이션 결과 모델.
    """
    session_id = query.session_id or f"session_{uuid.uuid4()}"

    # --- 목업 데이터 생성 ---
    # 실제 시스템에서는 이 부분이 각 모듈(NLP, Orchestrator, RAG 등)을
    # 순차적/병렬적으로 호출하는 복잡한 로직으로 대체됩니다.
    task1_id = f"task_{uuid.uuid4()}"
    task1 = TaskInfo(
        id=task1_id,
        name="압력 센서 데이터 조회 (과거 24시간)",
        intent="data_retrieval",
        assigned_agent_id="agent_monitor_001",
        status="completed"
    )

    task2_id = f"task_{uuid.uuid4()}"
    task2 = TaskInfo(
        id=task2_id,
        name="조회된 데이터 기반 고장 원인 분석",
        intent="root_cause_analysis",
        assigned_agent_id="agent_analysis_002",
        dependencies=[task1_id],
        status="completed"
    )

    flow_chart_data: Dict[str, Any] = {
        "nodes": [
            {"id": task1.id, "label": task1.name, "agent": task1.assigned_agent_id, "status": "completed"},
            {"id": task2.id, "label": task2.name, "agent": task2.assigned_agent_id, "status": "completed"},
        ],
        "edges": [
            {"from": task1.id, "to": task2.id}
        ]
    }

    mock_response = OrchestrationResponse(
        session_id=session_id,
        final_answer="모의 분석 결과: A-1 라인의 압력 이상은 밸브 B-3의 노후화 때문으로 분석됩니다. 관련 유지보수 매뉴얼을 함께 확인하세요.",
        flow_chart_data=flow_chart_data,
        supporting_documents=[
            "doc_id_1234: 밸브 B-3 유지보수 매뉴얼.pdf",
            "log_id_5678: 과거 밸브 B-3 교체 이력.csv"
        ],
        task_history=[task1, task2],
    )

    return mock_response 