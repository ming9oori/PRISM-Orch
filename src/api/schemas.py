from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class UserQueryInput(BaseModel):
    """사용자의 자연어 질의를 처리하기 위한 입력 모델"""
    query: str = Field(
        ...,
        description="사용자의 자연어 질의 원문",
        example="A-1 라인 압력에 이상이 생긴 것 같은데, 원인이 뭐야?"
    )
    session_id: Optional[str] = Field(
        None,
        description="사용자 세션을 식별하기 위한 ID",
        example="user123_session456"
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="사용자 선호도 (예: {'mode': 'conservative'})"
    )

class AgentInfo(BaseModel):
    """시스템에 등록된 AI 에이전트 정보를 나타내는 모델"""
    id: str = Field(..., description="에이전트의 고유 ID", example="agent_monitor_001")
    name: str = Field(..., description="에이전트 이름", example="모니터링 에이전트")
    description: str = Field(..., description="에이전트의 기능 상세 설명")
    capabilities: List[str] = Field(
        ...,
        description="에이전트가 수행할 수 있는 작업(capability) 목록",
        example=["pressure_monitoring", "temperature_analysis"]
    )

class TaskInfo(BaseModel):
    """오케스트레이터에 의해 생성되고 관리되는 과업(Task)의 정보 모델"""
    id: str = Field(..., description="과업의 고유 ID", example="task_98765")
    name: str = Field(..., description="과업의 이름", example="A-1 라인 압력 이상 원인 분석")
    intent: str = Field(..., description="사용자 질의로부터 추론된 의도", example="root_cause_analysis")
    assigned_agent_id: Optional[str] = Field(None, description="과업에 할당된 에이전트의 ID")
    dependencies: List[str] = Field(
        default_factory=list,
        description="이 과업이 의존하는 다른 과업들의 ID 목록"
    )
    status: str = Field("pending", description="과업의 현재 상태 (pending, running, completed, failed)")

class OrchestrationResponse(BaseModel):
    """오케스트레이션 최종 결과를 사용자에게 반환하기 위한 모델"""
    session_id: str = Field(..., description="현재 대화의 세션 ID")
    final_answer: str = Field(
        ...,
        description="사용자에게 제공되는 최종 답변 (자연어)",
        example="A-1 라인 압력 이상은 밸브 B-3의 노후화 때문으로 분석됩니다."
    )
    flow_chart_data: Dict[str, Any] = Field(
        ...,
        description="에이전트 협업 과정을 시각화한 플로우 차트 데이터 (UI에서 렌더링)"
    )
    supporting_documents: List[str] = Field(
        default_factory=list,
        description="답변의 근거가 되는 외부 문헌/지식 출처 목록"
    )
    task_history: List[TaskInfo] = Field(..., description="이번 요청으로 수행된 과업들의 히스토리") 