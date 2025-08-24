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
    user_id: Optional[str] = Field(
        None,
        description="사용자 식별자(메모리 검색 등 개인화에 사용)",
        example="engineer_kim"
    )
    user_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="사용자 선호도 (예: {'mode': 'conservative'})"
    )
    # LLM 생성 파라미터들
    max_tokens: Optional[int] = Field(
        default=1024,
        description="최대 토큰 수",
        example=1024
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="생성 온도 (0.0 ~ 2.0)",
        example=0.7
    )
    stop: Optional[List[str]] = Field(
        default=None,
        description="중단 시퀀스 목록",
        example=["\n\n", "END"]
    )
    use_tools: Optional[bool] = Field(
        default=True,
        description="도구 사용 여부",
        example=True
    )
    max_tool_calls: Optional[int] = Field(
        default=3,
        description="최대 도구 호출 수",
        example=3
    )
    extra_body: Optional[Dict[str, Any]] = Field(
        default=None,
        description="추가 OpenAI 호환 옵션 (예: tool_choice, repetition_penalty)",
        example={"tool_choice": "auto"}
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
    description: Optional[str] = Field(None, description="과업의 상세 설명")
    intent: str = Field(..., description="사용자 질의로부터 추론된 의도", example="root_cause_analysis")
    assigned_agent_id: Optional[str] = Field(None, description="과업에 할당된 에이전트의 ID")
    dependencies: List[str] = Field(
        default_factory=list,
        description="이 과업이 의존하는 다른 과업들의 ID 목록"
    )
    priority: str = Field("medium", description="과업의 우선순위 (high, medium, low)")
    status: str = Field("pending", description="과업의 현재 상태 (pending, running, completed, failed)")
    estimated_duration: Optional[str] = Field(None, description="예상 소요 시간")
    estimated_time: Optional[str] = Field(None, description="예상 소요 시간(LLM 분해 결과 호환용 필드)")
    original_query: Optional[str] = Field(None, description="원본 사용자 쿼리")

class OrchestrationResponse(BaseModel):
    """오케스트레이션 최종 결과를 사용자에게 반환하기 위한 모델"""
    session_id: str = Field(..., description="현재 대화의 세션 ID")
    final_answer: str = Field(
        ...,
        description="사용자에게 제공되는 최종 답변 (자연어)",
        example="A-1 라인 압력 이상은 밸브 B-3의 노후화 때문으로 분석됩니다."
    )
    # 선택적으로 마크다운 형태의 종합 리포트를 함께 반환할 수 있음
    final_markdown: Optional[str] = Field(
        default=None,
        description="마크다운 형태의 종합 리포트(선택)"
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

    # 도구 사용 내역(선택)
    tools_used: List[str] = Field(default_factory=list, description="이번 응답 생성에 사용된 도구 목록")
    tool_results: List[Dict[str, Any]] = Field(default_factory=list, description="도구 실행 결과(요약)")

    # 규정 준수 결과(선택)
    compliance_checked: bool = Field(default=False, description="규정 준수 사전검토 수행 여부")
    compliance_evidence: List[str] = Field(default_factory=list, description="규정 준수 매칭 근거(요약) 목록")
    compliance_verdict: Optional[Dict[str, Any]] = Field(
        default=None,
        description="규정 준수 판단 상세(JSON): {pass: bool, reasons:[], required_actions:[]}"
    )

    # 참고용 분해 요약(선택)
    decomposition: Optional[Dict[str, Any]] = Field(
        default=None,
        description="작업 분해 결과 요약(JSON): {tasks: [...], analysis: {...}}"
    ) 