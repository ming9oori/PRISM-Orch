"""
PRISM-Orch Orchestrator

PRISM-Core를 활용한 고수준 오케스트레이션 시스템입니다.
Mem0를 통한 장기 기억과 개인화된 상호작용을 지원합니다.
"""

from typing import Any, Dict, List, Optional
import json
import requests

from prism_core.core.llm.prism_llm_service import PrismLLMService
from prism_core.core.llm.schemas import Agent, AgentInvokeRequest, AgentResponse, LLMGenerationRequest
from prism_core.core.tools import BaseTool, ToolRequest, ToolResponse, ToolRegistry

from .tools.orch_tool_setup import OrchToolSetup
from prism_core.core.agents import AgentManager, WorkflowManager

from ..core.config import settings


class PrismOrchestrator:
    """
    High-level orchestrator for PRISM-Orch that uses prism-core's PrismLLMService.

    Responsibilities:
    - Initialize PrismLLMService (OpenAI-Compatible vLLM client + PRISM-Core API client)
    - Register default tools and the main orchestration agent
    - Perform task decomposition as the first step (agent-side), then invoke with tools
    - Manage long-term memory using Mem0 for personalized interactions
    """

    def __init__(self,
                 agent_name: str = "orchestration_agent",
                 openai_base_url: Optional[str] = None,
                 api_key: Optional[str] = None,
                 prism_core_api_base: Optional[str] = None) -> None:
        # Resolve endpoints from Orch settings or args
        self.agent_name = agent_name

        base_url = openai_base_url or settings.OPENAI_BASE_URL or "http://localhost:8001/v1"
        api_key = api_key or settings.OPENAI_API_KEY
        core_api = (prism_core_api_base or settings.PRISM_CORE_BASE_URL).rstrip('/')
        print(f"🔧 Core API: {core_api}")
        print(f"🔧 Base URL: {base_url}")
        print(f"🔧 API Key: {api_key}")

        # Initialize managers
        self.agent_manager = AgentManager()
        self.workflow_manager = WorkflowManager()
        
        # Initialize Orch tool setup
        self.orch_tool_setup = OrchToolSetup()
        self.tool_registry = self.orch_tool_setup.setup_tools()

        # Initialize LLM service with Orch tool registry
        self.llm = PrismLLMService(
            model_name=settings.VLLM_MODEL,
            simulate_delay=False,
            tool_registry=self.tool_registry,
            llm_service_url=core_api,
            agent_name=self.agent_name,
            openai_base_url=base_url,
            api_key=api_key,
        )

        # register tools to llm service
        for tool in self.tool_registry.list_tools():
            try:
                print(f"✅ 도구 '{tool.name}' 등록 시도")
                self.llm.register_tool(tool)
            except Exception as e:
                print(f"❌ 도구 '{tool.name}' 등록 실패: {str(e)}")
        

        # Set tool registry for managers
        self.agent_manager.set_tool_registry(self.tool_registry)
        self.workflow_manager.set_tool_registry(self.tool_registry)
        
        # Set LLM service and agent manager for workflow manager
        self.workflow_manager.set_llm_service(self.llm)
        self.workflow_manager.set_agent_manager(self.agent_manager)

        # Local cache for agent object
        self._agent: Optional[Agent] = None
        
        # Memory tool reference for direct access
        self._memory_tool = self.orch_tool_setup.get_memory_tool()
        
        # Print tool setup information
        self.orch_tool_setup.print_tool_info()
        
        # Print API configuration
        print(f"🔧 API 설정:")
        print(f"   - Prism-Core API: {core_api}")
        print(f"   - vLLM API: {base_url}")
        
        # Initialize orchestration pipeline
        self._setup_orchestration_pipeline()

    def _setup_orchestration_pipeline(self) -> None:
        """오케스트레이션 파이프라인을 설정합니다."""
        try:
            
            # 2. 하위 에이전트 초기화
            self._initialize_sub_agents()
            
            # 1. 메인 오케스트레이션 에이전트 등록
            self.register_orchestration_agent()

            # 3. 오케스트레이션 워크플로우 정의
            self._define_orchestration_workflow()
            
            print("✅ 오케스트레이션 파이프라인 설정 완료")
            
        except Exception as e:
            print(f"❌ 오케스트레이션 파이프라인 설정 실패: {str(e)}")

    def _initialize_sub_agents(self) -> None:
        """3가지 하위 에이전트를 초기화합니다."""
        try:
            # 모니터링 에이전트 초기화
            self._initialize_monitoring_agent()
            
            # 예측 에이전트 초기화
            self._initialize_prediction_agent()
            
            # 자율제어 에이전트 초기화
            self._initialize_autonomous_control_agent()
            
            print("✅ 하위 에이전트 초기화 완료")
            
        except Exception as e:
            print(f"❌ 하위 에이전트 초기화 실패: {str(e)}")



    def _initialize_monitoring_agent(self) -> None:
        """모니터링 에이전트를 초기화합니다."""
        try:
            # Pseudo method: 실제 API endpoint가 정해지면 여기서 초기화
            monitoring_config = {
                "agent_id": "monitoring_agent",
                "endpoint": "http://localhost:8002/api/monitoring",  # 예시 endpoint
                "capabilities": [
                    "anomaly_detection",
                    "future_anomaly_prediction", 
                    "sensor_data_analysis",
                    "process_monitoring"
                ],
                "status": "initialized"
            }
            
            # 에이전트 등록
            agent = Agent(
                name="monitoring_agent",
                description="사용자의 요청에 맞추어 특정 공정/기계/센서 등의 정보를 DB에서 산출하여 이상치 여부를 탐지하고, 미래 이상치 발생 가능성이 높은 부분을 알려줌",
                role_prompt="""당신은 산업 현장의 모니터링 전문가입니다.

**주요 역할:**
1. 특정 공정/기계/센서의 실시간 데이터 분석
2. 이상치 탐지 및 알림
3. 미래 이상치 발생 가능성 예측
4. 데이터베이스에서 관련 정보 산출

**처리 가능한 요청:**
- 특정 센서의 이상치 탐지
- 공정 상태 모니터링
- 미래 고장 가능성 분석
- 센서 데이터 품질 검증

**출력 형식:**
{
    "current_status": {
        "anomaly_detected": true/false,
        "anomaly_type": "sensor_failure/process_anomaly/etc",
        "severity": "low/medium/high/critical",
        "affected_components": ["component1", "component2"]
    },
    "future_prediction": {
        "anomaly_probability": 0.0-1.0,
        "predicted_time": "YYYY-MM-DD HH:MM:SS",
        "confidence": 0.0-1.0,
        "recommended_actions": ["action1", "action2"]
    },
    "data_summary": {
        "total_data_points": 1000,
        "anomaly_count": 5,
        "data_quality": "excellent/good/fair/poor"
    }
}""",
                tools=[]
            )
            
            # 에이전트 등록 (로컬 + 원격)
            self.agent_manager.register_agent(agent)
            
            # 원격 등록
            success = self.llm.register_agent(agent)
            if success:
                print(f"✅ 모니터링 에이전트 '{agent.name}' 원격 등록 완료")
            else:
                print(f"⚠️ 모니터링 에이전트 '{agent.name}' 원격 등록 실패")
            
            self._monitoring_agent_config = monitoring_config
            
            print(f"✅ 모니터링 에이전트 초기화 완료: {monitoring_config['agent_id']}")
            
        except Exception as e:
            print(f"❌ 모니터링 에이전트 초기화 실패: {str(e)}")

    def _initialize_prediction_agent(self) -> None:
        """예측 에이전트를 초기화합니다."""
        try:
            # Pseudo method: 실제 API endpoint가 정해지면 여기서 초기화
            prediction_config = {
                "agent_id": "prediction_agent",
                "endpoint": "http://localhost:8003/api/prediction",  # 예시 endpoint
                "capabilities": [
                    "time_series_prediction",
                    "anomaly_prediction",
                    "trend_analysis",
                    "forecasting"
                ],
                "status": "initialized"
            }
            
            # 에이전트 등록
            agent = Agent(
                name="prediction_agent",
                description="사용자의 요청에 맞추어 특정 공정/기계/센서의 미래 변화를 예측하고 이상치 발생 가능성이 높은 부분을 알려줌",
                role_prompt="""당신은 산업 현장의 예측 분석 전문가입니다.

**주요 역할:**
1. 특정 공정/기계/센서의 미래 변화 예측
2. 이상치 발생 가능성 분석
3. 시계열 데이터 분석 및 트렌드 예측
4. 예측 모델 기반 인사이트 제공

**처리 가능한 요청:**
- 센서 값 미래 예측
- 고장 시점 예측
- 성능 저하 예측
- 최적 운영 조건 예측

**출력 형식:**
{
    "prediction_results": {
        "target_variable": "sensor_name",
        "prediction_horizon": "24h/7d/30d",
        "predicted_values": [
            {"timestamp": "2024-01-01 12:00:00", "value": 25.5, "confidence": 0.95},
            {"timestamp": "2024-01-01 13:00:00", "value": 26.2, "confidence": 0.93}
        ],
        "anomaly_probability": 0.15,
        "trend": "increasing/decreasing/stable"
    },
    "model_info": {
        "model_type": "LSTM/Prophet/ARIMA",
        "accuracy": 0.92,
        "last_training": "2024-01-01 00:00:00"
    },
    "recommendations": [
        "예측 결과에 따른 권장사항 1",
        "예측 결과에 따른 권장사항 2"
    ]
}""",
                tools=[]
            )
            
            # 에이전트 등록 (로컬 + 원격)
            self.agent_manager.register_agent(agent)
            
            # 원격 등록
            success = self.llm.register_agent(agent)
            if success:
                print(f"✅ 예측 에이전트 '{agent.name}' 원격 등록 완료")
            else:
                print(f"⚠️ 예측 에이전트 '{agent.name}' 원격 등록 실패")
            
            self._prediction_agent_config = prediction_config
            
            print(f"✅ 예측 에이전트 초기화 완료: {prediction_config['agent_id']}")
            
        except Exception as e:
            print(f"❌ 예측 에이전트 초기화 실패: {str(e)}")

    def _initialize_autonomous_control_agent(self) -> None:
        """자율제어 에이전트를 초기화합니다."""
        try:
            # Pseudo method: 실제 API endpoint가 정해지면 여기서 초기화
            control_config = {
                "agent_id": "autonomous_control_agent",
                "endpoint": "http://localhost:8004/api/control",  # 예시 endpoint
                "capabilities": [
                    "parameter_optimization",
                    "control_recommendation",
                    "setpoint_adjustment",
                    "autonomous_decision"
                ],
                "status": "initialized"
            }
            
            # 에이전트 등록
            agent = Agent(
                name="autonomous_control_agent",
                description="사용자의 요청에 맞추어 이상치 발생이 가능하거나 출력을 조절하고 싶은 센서의 값을 예측 에이전트의 예측 모델들을 이용하여 최종 추천 파라미터 제공",
                role_prompt="""당신은 산업 현장의 자율제어 전문가입니다.

**주요 역할:**
1. 예측 모델 기반 최적 파라미터 추천
2. 이상치 방지를 위한 제어 파라미터 조정
3. 센서 출력 최적화
4. 자율적 의사결정 및 제어 권장

**처리 가능한 요청:**
- 센서 출력 조절 파라미터 추천
- 이상치 방지 제어 전략
- 최적 운영 조건 설정
- 자동 제어 파라미터 최적화

**출력 형식:**
{
    "control_recommendations": {
        "target_system": "system_name",
        "current_parameters": {
            "param1": 25.0,
            "param2": 60.0
        },
        "recommended_parameters": {
            "param1": 26.5,
            "param2": 58.0
        },
        "adjustment_reason": "anomaly_prevention/optimization",
        "expected_improvement": "15% reduction in anomaly probability"
    },
    "control_strategy": {
        "strategy_type": "preventive/corrective/optimization",
        "implementation_steps": [
            "Step 1: 현재 파라미터 백업",
            "Step 2: 새로운 파라미터 적용",
            "Step 3: 모니터링 시작"
        ],
        "safety_checks": ["check1", "check2"]
    },
    "risk_assessment": {
        "risk_level": "low/medium/high",
        "potential_issues": ["issue1", "issue2"],
        "mitigation_measures": ["measure1", "measure2"]
    }
}""",
                tools=[]
            )
            
            # 에이전트 등록 (로컬 + 원격)
            self.agent_manager.register_agent(agent)
            
            # 원격 등록
            success = self.llm.register_agent(agent)
            if success:
                print(f"✅ 자율제어 에이전트 '{agent.name}' 원격 등록 완료")
            else:
                print(f"⚠️ 자율제어 에이전트 '{agent.name}' 원격 등록 실패")
            
            self._autonomous_control_agent_config = control_config
            
            print(f"✅ 자율제어 에이전트 초기화 완료: {control_config['agent_id']}")
            
        except Exception as e:
            print(f"❌ 자율제어 에이전트 초기화 실패: {str(e)}")

    # Pseudo methods for sub-agent API calls
    async def _call_monitoring_agent(self, request_text: str) -> str:
        """모니터링 에이전트 API 호출 (Pseudo method)"""
        try:
            # 실제 구현에서는 HTTP 요청으로 변경
            # response = requests.post(self._monitoring_agent_config["endpoint"], 
            #                         json={"prompt": request_text, "user_id": "orchestrator"})
            
            # Pseudo response - 풍부한 텍스트 형태로 응답
            pseudo_response = f"""
# 모니터링 분석 결과

## 현재 상태 분석
현재 분석 대상 시스템의 상태를 종합적으로 점검한 결과, **이상치는 발견되지 않았습니다**. 모든 주요 센서들이 정상 범위 내에서 작동하고 있으며, 시스템 안정성이 확보된 상태입니다.

### 주요 센서 상태
- **온도 센서**: 24.5°C (정상 범위: 20-30°C)
- **압력 센서**: 2.1 bar (정상 범위: 1.8-2.5 bar)
- **유량 센서**: 150 L/min (정상 범위: 140-160 L/min)
- **진동 센서**: 0.8 mm/s (정상 범위: 0-1.2 mm/s)

### 데이터 품질 평가
- **총 데이터 포인트**: 1,000개
- **이상치 개수**: 2개 (0.2% - 매우 낮은 수준)
- **데이터 품질**: 우수 (신뢰도 95%)
- **마지막 업데이트**: {self._get_timestamp()}

## 미래 예측 분석
향후 24시간 동안의 시스템 상태를 예측한 결과, **이상치 발생 확률은 10%**로 낮은 수준입니다.

### 예측 상세 정보
- **예측 시점**: 2024-01-15 14:30:00
- **신뢰도**: 85%
- **주요 관찰사항**: 온도가 점진적으로 상승하는 추세가 관찰되나, 정상 범위 내에서의 변화입니다.

## 권장 조치사항
1. **정기 점검 수행**: 다음 정기 점검 일정을 준수하여 시스템 상태를 지속적으로 모니터링
2. **센서 교정 검토**: 온도 센서의 교정 상태를 다음 달에 재검토
3. **데이터 백업**: 현재 정상 상태의 데이터를 백업하여 향후 비교 분석에 활용

## 추가 모니터링 필요 사항
- 온도 상승 추세 지속 관찰
- 압력 변동 패턴 분석
- 주기적 진동 데이터 검토

---
*분석 수행: 모니터링 에이전트 | 생성 시간: {self._get_timestamp()}*
"""
            
            return pseudo_response
            
        except Exception as e:
            return f"모니터링 에이전트 호출 중 오류가 발생했습니다: {str(e)}"

    async def _call_prediction_agent(self, request_text: str) -> str:
        """예측 에이전트 API 호출 (Pseudo method)"""
        try:
            # 실제 구현에서는 HTTP 요청으로 변경
            # response = requests.post(self._prediction_agent_config["endpoint"], 
            #                         json={"prompt": request_text, "user_id": "orchestrator"})
            
            # Pseudo response - 풍부한 텍스트 형태로 응답
            pseudo_response = f"""
# 예측 분석 결과

## 예측 모델 정보
**모델 타입**: LSTM (Long Short-Term Memory)
**모델 정확도**: 92%
**마지막 학습**: 2024-01-01 00:00:00
**예측 기간**: 24시간

## 예측 대상 센서
**센서명**: 온도 센서 (TEMP-001)
**현재 값**: 25.5°C
**예측 단위**: 시간별

## 미래 예측 값
| 시간 | 예측값 | 신뢰도 | 상태 |
|------|--------|--------|------|
| 2024-01-02 12:00 | 25.5°C | 95% | 정상 |
| 2024-01-02 13:00 | 26.2°C | 93% | 정상 |
| 2024-01-02 14:00 | 26.8°C | 90% | 주의 |
| 2024-01-02 15:00 | 27.1°C | 88% | 주의 |
| 2024-01-02 16:00 | 27.3°C | 85% | 경계 |

## 트렌드 분석
**전체 트렌드**: 상승 추세
**변화율**: 시간당 평균 0.4°C 상승
**예상 최고값**: 27.5°C (2024-01-02 18:00)
**정상 범위**: 20-30°C

## 이상치 발생 가능성
**이상치 발생 확률**: 15%
**주요 위험 요소**:
- 온도 상승 속도가 평균보다 빠름
- 냉각 시스템 부하 증가 가능성
- 주변 환경 온도 상승 영향

## 모델 신뢰도 평가
- **데이터 품질**: 우수 (95%)
- **모델 성능**: 안정적 (92% 정확도)
- **예측 신뢰도**: 높음 (평균 90%)

## 권장사항
1. **냉각 시스템 점검**: 온도 상승 추세에 대비하여 냉각 시스템 상태 점검
2. **부하 분산**: 가능한 경우 일부 부하를 다른 시스템으로 분산
3. **모니터링 강화**: 2시간마다 온도 변화 추이 확인
4. **비상 대응 준비**: 온도가 28°C를 초과할 경우 비상 냉각 시스템 가동 준비

## 예측 한계 및 주의사항
- 외부 환경 변화(날씨, 전력 공급 등)에 따른 예측 정확도 변동 가능
- 급격한 시스템 변경 시 예측 모델 재학습 필요
- 예측 결과는 참고 자료이며, 실제 운영 결정은 종합적 판단 필요

---
*분석 수행: 예측 에이전트 | 생성 시간: {self._get_timestamp()}*
"""
            
            return pseudo_response
            
        except Exception as e:
            return f"예측 에이전트 호출 중 오류가 발생했습니다: {str(e)}"

    async def _call_autonomous_control_agent(self, request_text: str) -> str:
        """자율제어 에이전트 API 호출 (Pseudo method)"""
        try:
            # 실제 구현에서는 HTTP 요청으로 변경
            # response = requests.post(self._autonomous_control_agent_config["endpoint"], 
            #                         json={"prompt": request_text, "user_id": "orchestrator"})
            
            # Pseudo response - 풍부한 텍스트 형태로 응답
            pseudo_response = f"""
# 자율제어 권장사항

## 제어 대상 시스템
**시스템명**: 온도 제어 시스템 (TEMP-CTRL-001)
**현재 상태**: 정상 운영 중
**제어 모드**: 자동 제어

## 현재 제어 파라미터
| 파라미터 | 현재값 | 단위 | 범위 |
|----------|--------|------|------|
| Setpoint | 25.0°C | °C | 20-30°C |
| Deadband | 2.0°C | °C | 1.0-3.0°C |
| P Gain | 2.5 | - | 1.0-5.0 |
| I Time | 120s | s | 60-300s |
| D Time | 30s | s | 10-60s |

## 권장 제어 파라미터
| 파라미터 | 현재값 | 권장값 | 변경량 | 이유 |
|----------|--------|--------|--------|------|
| Setpoint | 25.0°C | 24.5°C | -0.5°C | 온도 상승 추세 대응 |
| Deadband | 2.0°C | 1.5°C | -0.5°C | 제어 정밀도 향상 |
| P Gain | 2.5 | 2.8 | +0.3 | 응답 속도 개선 |

## 제어 전략
**전략 유형**: 예방적 제어 (Preventive Control)
**적용 이유**: 온도 상승 추세 관찰 및 예측 모델 결과 반영
**예상 효과**: 온도 변동 20% 감소, 시스템 안정성 향상

## 구현 단계
### 1단계: 현재 상태 백업 (5분)
- 현재 제어 파라미터 전체 백업
- 시스템 상태 스냅샷 저장
- 롤백 계획 수립

### 2단계: 점진적 파라미터 적용 (15분)
- Setpoint를 25.0°C → 24.8°C → 24.5°C로 단계적 조정
- 각 단계마다 5분간 안정화 대기
- 시스템 응답 관찰 및 기록

### 3단계: 모니터링 및 검증 (30분)
- 온도 변화 추이 실시간 모니터링
- 제어 성능 지표 확인
- 안전성 검증 수행

## 안전성 검증 항목
- [ ] 온도 범위 검증 (20-30°C 내 유지)
- [ ] 압력 안전성 확인 (1.8-2.5 bar 유지)
- [ ] 시스템 응답성 검증
- [ ] 에너지 효율성 확인

## 위험도 평가
**전체 위험 수준**: 낮음 (Low Risk)
**주요 위험 요소**:
- 일시적 온도 변동 (예상 범위 내)
- 제어 시스템 부하 증가 (허용 범위 내)

**완화 조치**:
1. 점진적 파라미터 조정으로 급격한 변화 방지
2. 실시간 모니터링을 통한 즉시 대응
3. 자동 롤백 시스템 활성화

## 예상 개선 효과
- **온도 변동성**: 20% 감소 예상
- **에너지 효율성**: 5% 향상 예상
- **시스템 안정성**: 향상
- **예방 정비 효과**: 이상치 발생 가능성 15% 감소

## 추가 권장사항
1. **정기 점검**: 주 1회 제어 성능 평가
2. **모델 업데이트**: 월 1회 예측 모델 재학습
3. **문서화**: 파라미터 변경 이력 및 효과 분석 보고서 작성

## 비상 대응 계획
**긴급 상황 발생 시**:
1. 즉시 이전 파라미터로 롤백
2. 시스템 상태 긴급 점검
3. 운영팀에 즉시 보고
4. 원인 분석 및 대책 수립

---
*분석 수행: 자율제어 에이전트 | 생성 시간: {self._get_timestamp()}*
"""
            
            return pseudo_response
            
        except Exception as e:
            return f"자율제어 에이전트 호출 중 오류가 발생했습니다: {str(e)}"



    def _define_orchestration_workflow(self) -> None:
        """오케스트레이션 워크플로우를 정의합니다."""
        workflow_steps = [
            # 1단계: Query Refinement
            {
                "name": "query_refinement",
                "type": "agent_call",
                "agent_name": self.agent_name,
                "prompt_template": """당신은 PRISM-Orch의 오케스트레이션 에이전트입니다. 현재 단계에서는 사용자의 자연어 쿼리를 두 개의 벡터 데이터베이스에 최적화된 refined query로 변환하는 작업을 수행합니다.

**현재 작업: Query Refinement**
사용자 쿼리를 분석하여 기술적 내용과 규정 관련 내용을 분리하고, 각 도메인에 특화된 검색 쿼리를 생성합니다.

**출력 형식:**
반드시 다음 JSON 형식으로 응답하세요:
{
    "technical_query": "기술적 내용에 대한 refined query",
    "compliance_query": "규정/안전 관련 내용에 대한 refined query",
    "reasoning": "쿼리 분리 및 최적화 이유"
}

사용자 쿼리: {{user_query}}"""
            },
            # 2단계: RAG Search (Technical)
            {
                "name": "technical_search",
                "type": "tool_call",
                "tool_name": "rag_search",
                "parameters": {
                    "query": "{{query_refinement.output.technical_query}}",
                    "domain": "research",
                    "top_k": 5
                }
            },
            # 3단계: RAG Search (Compliance)
            {
                "name": "compliance_search",
                "type": "tool_call",
                "tool_name": "rag_search",
                "parameters": {
                    "query": "{{query_refinement.output.compliance_query}}",
                    "domain": "compliance",
                    "top_k": 5
                }
            },
            # 4단계: Plan Generation
            {
                "name": "plan_generation",
                "type": "agent_call",
                "agent_name": self.agent_name,
                "prompt_template": """당신은 PRISM-Orch의 오케스트레이션 에이전트입니다. 현재 단계에서는 검색 결과를 분석하여 3가지 하위 에이전트를 활용한 실행 계획을 수립하는 작업을 수행합니다.

**현재 작업: Plan Generation**
기술적 검색 결과와 규정 검색 결과를 종합 분석하여 3가지 하위 에이전트의 순차적 활용 계획을 수립합니다.

**3가지 하위 에이전트:**
1. **모니터링 에이전트**: 사용자의 요청에 맞추어 특정 공정/기계/센서 등의 정보를 DB에서 산출하여 이상치 여부를 탐지하고, 미래 이상치 발생 가능성이 높은 부분을 알려줌
2. **예측 에이전트**: 사용자의 요청에 맞추어 특정 공정/기계/센서의 미래 변화를 예측하고 이상치 발생 가능성이 높은 부분을 알려줌
3. **자율제어 에이전트**: 사용자의 요청에 맞추어 이상치 발생이 가능하거나 출력을 조절하고 싶은 센서의 값을 예측 에이전트의 예측 모델들을 이용하여 최종 추천 파라미터 제공

**출력 형식:**
반드시 다음 JSON 형식으로 응답하세요:
{
    "plan": {
        "step1": {
            "agent": "monitoring_agent",
            "role": "현재 상태 모니터링 및 이상치 탐지",
            "input": {
                "target_system": "시스템명",
                "sensors": ["센서1", "센서2"],
                "time_range": "24h"
            },
            "expected_output": "현재 이상치 상태 및 미래 예측"
        },
        "step2": {
            "agent": "prediction_agent",
            "role": "미래 변화 예측 및 이상치 발생 가능성 분석",
            "input": {
                "target_sensor": "예측 대상 센서",
                "prediction_horizon": "24h/7d/30d",
                "historical_data": "사용 가능한 과거 데이터"
            },
            "expected_output": "미래 예측 결과 및 이상치 발생 확률"
        },
        "step3": {
            "agent": "autonomous_control_agent",
            "role": "최적 제어 파라미터 추천",
            "input": {
                "target_system": "제어 대상 시스템",
                "current_parameters": "현재 파라미터",
                "prediction_results": "예측 에이전트 결과"
            },
            "expected_output": "추천 제어 파라미터 및 실행 전략"
        }
    },
    "reasoning": "계획 수립 근거 및 각 에이전트 선택 이유"
}

기술적 검색 결과: {{technical_search.output}}
규정 검색 결과: {{compliance_search.output}}"""
            },
            # 5단계: Plan Review
            {
                "name": "plan_review",
                "type": "agent_call",
                "agent_name": self.agent_name,
                "prompt_template": """당신은 PRISM-Orch의 오케스트레이션 에이전트입니다. 현재 단계에서는 수립된 실행 계획을 검토하고 최종 확정하는 작업을 수행합니다.

**현재 작업: Plan Review**
제안된 계획의 완성도와 실현 가능성을 검토하고, 필요한 경우 계획을 수정 및 보완합니다.

**검토 기준:**
- 계획의 논리적 흐름
- 각 단계의 명확성
- 실현 가능성
- 안전성 고려사항
- 효율성

**출력 형식:**
반드시 다음 JSON 형식으로 응답하세요:
{
    "review_result": {
        "is_approved": true/false,
        "confidence_score": 0.0-1.0,
        "feedback": "검토 의견"
    },
    "final_plan": {
        // 수정된 최종 계획 (기존 plan과 동일한 구조)
    },
    "modifications": [
        "수정 사항 1",
        "수정 사항 2"
    ]
}

계획: {{plan_generation.output}}"""
            },
            # 6단계: Execution Loop
            {
                "name": "execution_loop",
                "type": "agent_call",
                "agent_name": self.agent_name,
                "prompt_template": """당신은 PRISM-Orch의 오케스트레이션 에이전트입니다. 현재 단계에서는 확정된 계획에 따라 3가지 하위 에이전트들을 순차적으로 실행하는 작업을 수행합니다.

**현재 작업: Execution Loop**
확정된 계획의 각 단계를 순차적으로 실행하고, 각 하위 에이전트 API 호출 및 결과를 수집합니다.

**실행 프로세스:**
1. 모니터링 에이전트 호출 (현재 상태 분석)
2. 예측 에이전트 호출 (미래 예측)
3. 자율제어 에이전트 호출 (제어 파라미터 추천)
4. 각 단계 결과 수집 및 저장

**하위 에이전트 호출 방법:**
각 하위 에이전트는 텍스트 기반으로 소통합니다. 다음과 같은 형식으로 요청을 구성하세요:

**모니터링 에이전트 요청 예시:**
```
안녕하세요! 모니터링 에이전트입니다.
현재 [시스템명]의 상태를 분석해주세요.
분석 범위: [시간 범위]
특별히 확인할 센서: [센서 목록]
```

**예측 에이전트 요청 예시:**
```
안녕하세요! 예측 에이전트입니다.
[센서명]의 향후 [예측 기간] 변화를 예측해주세요.
현재 값: [현재 값]
예측 모델: [선호하는 모델 타입]
```

**자율제어 에이전트 요청 예시:**
```
안녕하세요! 자율제어 에이전트입니다.
[시스템명]의 제어 파라미터를 최적화해주세요.
현재 파라미터: [현재 파라미터]
예측 결과: [예측 에이전트 결과 요약]
목표: [개선 목표]
```

**출력 형식:**
각 에이전트 실행 후 다음 형식으로 응답하세요:

# 3단계 하위 에이전트 실행 결과

## 1단계: 모니터링 에이전트 실행
**상태**: 완료
**요청 내용**: [모니터링 요청 텍스트]
**응답 요약**: [모니터링 결과 핵심 내용]

## 2단계: 예측 에이전트 실행  
**상태**: 완료
**요청 내용**: [예측 요청 텍스트]
**응답 요약**: [예측 결과 핵심 내용]

## 3단계: 자율제어 에이전트 실행
**상태**: 완료
**요청 내용**: [자율제어 요청 텍스트]
**응답 요약**: [자율제어 결과 핵심 내용]

## 종합 실행 상태
**전체 상태**: 모든 단계 완료
**실행 시간**: [실행 완료 시간]
**주요 발견사항**: [3단계 통합 분석 결과]

확정된 계획: {{plan_review.output.final_plan}}"""
            },
            # 7단계: Plan Update (반복)
            {
                "name": "plan_update",
                "type": "agent_call",
                "agent_name": self.agent_name,
                "prompt_template": """당신은 PRISM-Orch의 오케스트레이션 에이전트입니다. 현재 단계에서는 3가지 하위 에이전트 실행 결과를 바탕으로 기존 계획을 검토하고 수정하는 작업을 수행합니다.

**현재 작업: Plan Update**
각 하위 에이전트(모니터링/예측/자율제어)의 실행 결과를 분석하고, 기존 계획과 실제 결과를 비교하여 필요시 계획을 수정 및 보완합니다.

**검토 기준:**
- 모니터링 결과의 이상치 탐지 정확도
- 예측 모델의 신뢰도 및 정확도
- 자율제어 추천의 실현 가능성
- 3단계 간 결과의 일관성

**출력 형식:**
반드시 다음 JSON 형식으로 응답하세요:
{
    "analysis": {
        "monitoring_results": {
            "anomaly_detected": true/false,
            "data_quality": "excellent/good/fair/poor",
            "confidence": 0.0-1.0
        },
        "prediction_results": {
            "model_accuracy": 0.0-1.0,
            "prediction_confidence": 0.0-1.0,
            "trend_reliability": "high/medium/low"
        },
        "control_results": {
            "recommendation_feasibility": "high/medium/low",
            "risk_level": "low/medium/high",
            "implementation_complexity": "simple/moderate/complex"
        },
        "overall_assessment": {
            "results_quality": "excellent/good/fair/poor",
            "unexpected_findings": ["예상치 못한 발견사항들"],
            "missing_information": ["부족한 정보들"]
        }
    },
    "plan_updates": {
        "modifications_needed": true/false,
        "updated_plan": {
            // 수정된 계획 (필요시)
        },
        "additional_steps": [
            // 추가 단계 (필요시)
        ]
    },
    "recommendations": [
        "권장사항 1",
        "권장사항 2"
    ]
}

실행 결과: {{execution_loop.output}}
원본 계획: {{plan_review.output.final_plan}}"""
            },
            # 8단계: Final Output
            {
                "name": "final_output",
                "type": "agent_call",
                "agent_name": self.agent_name,
                "prompt_template": """당신은 PRISM-Orch의 오케스트레이션 에이전트입니다. 현재 단계에서는 3가지 하위 에이전트(모니터링/예측/자율제어)의 실행 결과를 종합하여 사용자에게 전달하기 위한 Markdown 형태의 출력물을 구성하는 작업을 수행합니다.

**현재 작업: Final Output**
3가지 하위 에이전트의 결과를 종합 분석하고, 사용자 친화적인 Markdown 형태의 응답을 구성하여 핵심 정보를 명확하게 전달합니다.

**출력 형식:**
반드시 다음 Markdown 형식으로 응답하세요:

# 📊 산업 현장 분석 결과

## 🔍 현재 상태 모니터링
[모니터링 에이전트 결과 요약]
- **이상치 탐지**: [발견/미발견]
- **데이터 품질**: [우수/양호/보통/불량]
- **주요 발견사항**: [핵심 내용]

## 🔮 미래 예측 분석
[예측 에이전트 결과 요약]
- **예측 모델**: [모델 타입 및 정확도]
- **예측 기간**: [예측 기간]
- **주요 트렌드**: [증가/감소/안정]
- **이상치 발생 확률**: [확률]

## 🎛️ 자율제어 권장사항
[자율제어 에이전트 결과 요약]
- **제어 대상**: [시스템명]
- **현재 파라미터**: [현재 값]
- **권장 파라미터**: [권장 값]
- **예상 개선효과**: [개선 효과]

## ⚠️ 위험도 평가
[위험도 분석 결과]
- **위험 수준**: [낮음/보통/높음]
- **잠재적 문제**: [문제점들]
- **완화 조치**: [대응 방안]

## 🛠️ 실행 계획
[구체적인 실행 방안]
1. [단계 1]
2. [단계 2]
3. [단계 3]

## 📝 주의사항 및 권장사항
[실행 시 주의사항 및 권장사항]

**구성 원칙:**
- 명확하고 간결한 설명
- 실용적인 조언
- 안전성 우선 고려
- 실행 가능한 단계별 가이드
- 데이터 기반 의사결정 지원

사용자 쿼리: {{user_query}}
최종 실행 결과: {{execution_loop.output}}
계획 업데이트: {{plan_update.output}}"""
            }
        ]
        
        self.workflow_manager.define_workflow("orchestration_pipeline", workflow_steps)

    def register_orchestration_agent(self) -> None:
        """오케스트레이션 에이전트를 등록합니다."""
        try:
            # Create orchestration agent
            agent = Agent(
                name=self.agent_name,
                description="PRISM-Orch의 메인 오케스트레이션 에이전트",
                role_prompt="""당신은 PRISM-Orch의 메인 오케스트레이션 에이전트입니다.

**중요: 항상 사용 가능한 도구들을 적극적으로 활용하세요!**

주요 역할:
1. 사용자 요청을 분석하여 적절한 도구들을 선택하고 사용
2. 복잡한 작업을 단계별로 분해하여 실행
3. 지식 베이스 검색, 규정 준수 검증, 사용자 이력 참조 등을 통합
4. 안전하고 효율적인 작업 수행을 위한 가이드 제공
5. 사용자의 과거 상호작용을 기억하여 개인화된 응답 제공

**사용 가능한 도구들 (반드시 활용하세요):**

1. **rag_search**: 지식 베이스에서 관련 정보 검색
   - 기술 문서, 연구 자료, 사용자 이력, 규정 문서 검색
   - 사용 시: 기술적 질문, 문서 검색이 필요한 경우
   - 예시: "압력 센서 원리", "고온 배관 점검", "화학 물질 취급"

2. **compliance_check**: 안전 규정 및 법규 준수 여부 검증
   - 제안된 조치의 안전성 및 규정 준수 여부 검증
   - 사용 시: 안전 관련 질문, 규정 준수 확인이 필요한 경우
   - 예시: "고압 가스 배관 누출 대응", "독성 물질 취급", "방사성 물질 작업"

3. **memory_search**: 사용자의 과거 상호작용 기록 검색 (Mem0 기반)
   - 사용자별 개인화된 이력 및 경험 검색
   - 사용 시: 사용자 ID가 제공된 경우, 이전 대화 참조가 필요한 경우
   - 예시: "이전에 말씀하신...", "사용자 경험", "개인화된 조언"

**도구 사용 가이드라인:**
- 기술적 질문 → rag_search 사용
- 안전/규정 관련 질문 → compliance_check 사용
- 사용자별 개인화 → memory_search 사용
- 복합적 질문 → 여러 도구 조합 사용

**응답 형식:**
1. 도구를 사용하여 관련 정보 수집
2. 수집된 정보를 바탕으로 종합적인 답변 제공
3. 안전하고 실용적인 조언 제시

항상 안전하고 규정을 준수하는 방식으로 작업을 수행하세요.
사용자의 개인화된 경험을 위해 과거 상호작용을 적극적으로 활용하세요.""",
                tools=["rag_search", "compliance_check", "memory_search"]
            )

            # Register agent locally (로컬 agent_manager에 등록)
            self.agent_manager.register_agent(agent)
            self._agent = agent
            
            # Register agent remotely via PrismLLMService (PRISM-Core API 서버에 등록)
            success = self.llm.register_agent(agent)
            if success:
                print(f"✅ 오케스트레이션 에이전트 '{self.agent_name}' 원격 등록 완료")
            else:
                print(f"⚠️ 오케스트레이션 에이전트 '{self.agent_name}' 원격 등록 실패 (로컬 등록은 완료)")
            
            print(f"✅ 오케스트레이션 에이전트 '{self.agent_name}' 로컬 등록 완료")

        except Exception as e:
            print(f"❌ 에이전트 등록 실패: {str(e)}")

    async def orchestrate(
        self, 
        prompt: str, 
        user_id: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
        use_tools: bool = True,
        max_tool_calls: int = 3,
        extra_body: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        메인 오케스트레이션 메서드 - 워크플로우 기반 순차 실행
        
        Args:
            prompt: 사용자 요청
            user_id: 사용자 ID (선택사항)
            max_tokens: 최대 토큰 수 (기본값: 1024)
            temperature: 생성 온도 (기본값: 0.7)
            stop: 중단 시퀀스 (기본값: None)
            use_tools: 도구 사용 여부 (기본값: True)
            max_tool_calls: 최대 도구 호출 수 (기본값: 3)
            extra_body: 추가 OpenAI 호환 옵션 (기본값: None)
            
        Returns:
            AgentResponse: 오케스트레이션 결과
        """
        try:
            # Ensure agent is registered (already done in __init__, but double-check)
            if not self._agent:
                print("⚠️ 에이전트가 등록되지 않았습니다. 다시 등록을 시도합니다.")
                self.register_orchestration_agent()

            # Prepare context for workflow execution
            context = {
                "user_query": prompt,
                "user_id": user_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "timestamp": self._get_timestamp()
            }

            # Execute orchestration workflow
            workflow_result = await self.workflow_manager.execute_workflow("orchestration_pipeline", context)
            
            if workflow_result["status"] == "completed":
                # Extract final output from workflow result
                final_step = workflow_result["steps"][-1]
                final_output = final_step.get("output", {}).get("agent_response", "")
                
                # Create AgentResponse
                response = AgentResponse(
                    text=final_output,
                    tools_used=["orchestration_pipeline"],
                    tool_results=[workflow_result],
                    metadata={
                        "workflow_execution_id": workflow_result["execution_id"],
                        "user_id": user_id,
                        "prompt": prompt,
                        "timestamp": self._get_timestamp(),
                        "workflow_status": "completed"
                    }
                )
            else:
                # Handle workflow failure
                error_msg = workflow_result.get("error", "Unknown workflow error")
                response = AgentResponse(
                    text=f"오케스트레이션 워크플로우 실행 중 오류가 발생했습니다: {error_msg}",
                    tools_used=[],
                    tool_results=[],
                    metadata={
                        "error": error_msg,
                        "user_id": user_id,
                        "prompt": prompt,
                        "timestamp": self._get_timestamp(),
                        "workflow_status": "failed"
                    }
                )
            
            # Save conversation to memory if user_id is provided
            if user_id and self._memory_tool:
                await self._save_conversation_to_memory(user_id, prompt, response.text)
            
            return response

        except Exception as e:
            # find out which line of code is causing the error
            import traceback
            traceback.print_exc()
            # Create error response with proper AgentResponse structure
            return AgentResponse(
                text=f"오케스트레이션 중 오류가 발생했습니다: {str(e)}",
                tools_used=[],
                tool_results=[],
                metadata={
                    "error": str(e),
                    "user_id": user_id,
                    "prompt": prompt,
                    "timestamp": self._get_timestamp()
                }
            )

    async def _execute_agent_call(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        """에이전트 호출을 실행합니다."""
        try:
            # Get agent from agent manager
            agent = self.agent_manager.get_agent(agent_name)
            if not agent:
                return {"success": False, "error": f"Agent '{agent_name}' not found"}
            
            # Create agent invoke request
            request = AgentInvokeRequest(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.7,
                use_tools=False  # Agent calls don't use tools directly
            )
            
            # Invoke agent using LLM service
            response = await self.llm.invoke_agent(agent, request)
            
            return {
                "success": True,
                "output": response.text
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """도구 호출을 실행합니다."""
        try:
            # Get tool from tool registry
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return {"success": False, "error": f"Tool '{tool_name}' not found"}
            
            # Create tool request
            request = ToolRequest(tool_name=tool_name, parameters=parameters)
            
            # Execute tool
            response = await tool.execute(request)
            
            if response.success:
                return {
                    "success": True,
                    "output": response.result
                }
            else:
                return {
                    "success": False,
                    "error": response.error_message
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_execution_id(self) -> str:
        """실행 ID를 생성합니다."""
        import uuid
        return str(uuid.uuid4())

    async def _save_conversation_to_memory(self, user_id: str, user_prompt: str, assistant_response: str) -> None:
        """대화 내용을 Mem0에 저장"""
        try:
            if not self._memory_tool or not self._memory_tool.is_mem0_available():
                return
            
            # 대화 메시지 구성
            conversation_messages = [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_response}
            ]
            
            # Mem0에 저장
            success = await self._memory_tool.add_memory(user_id, conversation_messages)
            if success:
                print(f"✅ 사용자 '{user_id}'의 대화 내용이 메모리에 저장되었습니다")
            
        except Exception as e:
            print(f"⚠️  대화 내용 저장 실패: {str(e)}")

    async def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 메모리 요약 조회"""
        try:
            if not self._memory_tool:
                return {"error": "Memory tool not available"}
            
            return await self._memory_tool.get_user_memory_summary(user_id)
            
        except Exception as e:
            return {"error": f"메모리 요약 조회 실패: {str(e)}"}

    async def search_user_memories(self, query: str, user_id: str, top_k: int = 3) -> Dict[str, Any]:
        """사용자 메모리 검색"""
        try:
            if not self._memory_tool:
                return {"error": "Memory tool not available"}
            
            # Memory tool 직접 호출
            request = ToolRequest(
                tool_name="memory_search",
                parameters={
                    "query": query,
                    "user_id": user_id,
                    "top_k": top_k,
                    "memory_type": "user",
                    "include_context": True
                }
            )
            
            response = await self._memory_tool.execute(request)
            return response.result if response.success else {"error": response.error_message}
            
        except Exception as e:
            return {"error": f"메모리 검색 실패: {str(e)}"}

    def is_mem0_available(self) -> bool:
        """Mem0 사용 가능 여부 확인"""
        return self._memory_tool.is_mem0_available() if self._memory_tool else False

    def define_workflow(self, workflow_name: str, steps: List[Dict[str, Any]]) -> bool:
        """워크플로우 정의"""
        return self.workflow_manager.define_workflow(workflow_name, steps)

    async def execute_workflow(self, workflow_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 실행"""
        return self.workflow_manager.execute_workflow(workflow_name, context)

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        return self.agent_manager.get_agent_status(agent_name)

    def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        return self.workflow_manager.get_workflow_status(workflow_name)

    def list_agents(self) -> List[Agent]:
        """등록된 에이전트 목록 조회"""
        return self.agent_manager.list_agents()

    def list_tools(self) -> List[str]:
        """등록된 Tool 목록 조회"""
        return list(self.llm.tool_registry._tools.keys())

    def get_sub_agent_status(self) -> Dict[str, Any]:
        """하위 에이전트들의 상태를 조회합니다."""
        try:
            status = {
                "monitoring_agent": {
                    "status": getattr(self, '_monitoring_agent_config', {}).get('status', 'not_initialized'),
                    "endpoint": getattr(self, '_monitoring_agent_config', {}).get('endpoint', 'not_configured'),
                    "capabilities": getattr(self, '_monitoring_agent_config', {}).get('capabilities', [])
                },
                "prediction_agent": {
                    "status": getattr(self, '_prediction_agent_config', {}).get('status', 'not_initialized'),
                    "endpoint": getattr(self, '_prediction_agent_config', {}).get('endpoint', 'not_configured'),
                    "capabilities": getattr(self, '_prediction_agent_config', {}).get('capabilities', [])
                },
                "autonomous_control_agent": {
                    "status": getattr(self, '_autonomous_control_agent_config', {}).get('status', 'not_initialized'),
                    "endpoint": getattr(self, '_autonomous_control_agent_config', {}).get('endpoint', 'not_configured'),
                    "capabilities": getattr(self, '_autonomous_control_agent_config', {}).get('capabilities', [])
                }
            }
            return status
        except Exception as e:
            return {"error": f"하위 에이전트 상태 조회 실패: {str(e)}"}

    async def test_sub_agent_connection(self, agent_name: str) -> Dict[str, Any]:
        """하위 에이전트 연결을 테스트합니다."""
        try:
            test_prompt = f"""
안녕하세요! 오케스트레이션 에이전트에서 연결 테스트를 수행하고 있습니다.

**테스트 요청사항:**
- 현재 시간: {self._get_timestamp()}
- 테스트 유형: 연결 상태 확인
- 요청 내용: 간단한 상태 보고서 제공

위 요청사항에 대해 간단한 응답을 제공해주세요.
"""
            
            if agent_name == "monitoring_agent":
                result = await self._call_monitoring_agent(test_prompt)
            elif agent_name == "prediction_agent":
                result = await self._call_prediction_agent(test_prompt)
            elif agent_name == "autonomous_control_agent":
                result = await self._call_autonomous_control_agent(test_prompt)
            else:
                return {"error": f"알 수 없는 에이전트: {agent_name}"}
            
            # 텍스트 응답에서 성공 여부 판단
            is_success = "오류" not in result and len(result) > 50  # 간단한 응답 길이 체크
            
            return {
                "agent_name": agent_name,
                "connection_test": "success" if is_success else "failed",
                "response": result,
                "response_length": len(result),
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            return {
                "agent_name": agent_name,
                "connection_test": "failed",
                "error": str(e),
                "timestamp": self._get_timestamp()
            }

    def update_sub_agent_endpoint(self, agent_name: str, new_endpoint: str) -> bool:
        """하위 에이전트의 endpoint를 업데이트합니다."""
        try:
            if agent_name == "monitoring_agent" and hasattr(self, '_monitoring_agent_config'):
                self._monitoring_agent_config["endpoint"] = new_endpoint
                return True
            elif agent_name == "prediction_agent" and hasattr(self, '_prediction_agent_config'):
                self._prediction_agent_config["endpoint"] = new_endpoint
                return True
            elif agent_name == "autonomous_control_agent" and hasattr(self, '_autonomous_control_agent_config'):
                self._autonomous_control_agent_config["endpoint"] = new_endpoint
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ Endpoint 업데이트 실패: {str(e)}")
            return False

    def _get_timestamp(self) -> str:
        """타임스탬프 생성"""
        from datetime import datetime
        return datetime.now().isoformat()

    # Legacy methods for backward compatibility
    async def invoke_agent_with_tools(self, prompt: str) -> AgentResponse:
        """레거시 메서드: 에이전트 호출"""
        return await self.orchestrate(prompt)

    def register_default_tools_legacy(self) -> None:
        """레거시 메서드: 기본 Tool 등록"""
        self.register_default_tools() 