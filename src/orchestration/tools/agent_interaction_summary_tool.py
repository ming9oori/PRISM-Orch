"""
Agent Interaction Summary Tool

에이전트 간 상호작용 결과를 요약하고 분석하는 Tool입니다.
LLM을 통한 지능형 에이전트 상호작용 요약 및 워크플로우 분석을 제공합니다.
PRISM Core의 공통 설정을 사용합니다.
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

try:
    from prism_core.core.tools.base import BaseTool
    from prism_core.core.tools.schemas import ToolRequest, ToolResponse
    from prism_core.core.config import settings
    PRISM_CORE_AVAILABLE = True
except ImportError:
    # Fallback for when prism-core is not available
    PRISM_CORE_AVAILABLE = False
    print("⚠️  PRISM Core 라이브러리가 설치되지 않았습니다. 기본 구현을 사용합니다.")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI 라이브러리가 설치되지 않았습니다. 기본 요약 분석만 사용 가능합니다.")


# Fallback base classes when prism-core is not available
if not PRISM_CORE_AVAILABLE:
    class BaseTool:
        def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
            self.name = name
            self.description = description
            self.parameters_schema = parameters_schema
    
    class ToolRequest:
        def __init__(self, parameters: Dict[str, Any]):
            self.parameters = parameters
    
    class ToolResponse:
        def __init__(self, success: bool, data: Dict[str, Any] = None, error: str = None):
            self.success = success
            self.data = data or {}
            self.error = error


class AgentInteractionSummaryTool(BaseTool):
    """
    에이전트 상호작용 결과를 요약하고 분석하는 Tool
    
    기능:
    - 에이전트 간 요청/응답 메시지 요약
    - 워크플로우 실행 결과 분석
    - LLM을 통한 지능형 상호작용 요약
    - 성능 메트릭 및 통계 정보 생성
    """
    
    def __init__(self, 
                 weaviate_url: Optional[str] = None,
                 openai_base_url: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 model_name: Optional[str] = None,
                 client_id: str = "default",
                 class_prefix: str = "Default"):
        super().__init__(
            name="agent_interaction_summary",
            description="에이전트 간 상호작용 결과를 요약하고 워크플로우를 분석합니다",
            parameters_schema={
                "type": "object",
                "properties": {
                    "agent_interactions": {
                        "type": "array",
                        "description": "분석할 에이전트 상호작용 리스트",
                        "items": {
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "string", "description": "태스크 ID"},
                                "requester": {"type": "string", "description": "요청 에이전트"},
                                "target": {"type": "string", "description": "대상 에이전트"},
                                "request_type": {"type": "string", "description": "요청 타입"},
                                "request_message": {"type": "object", "description": "요청 메시지"},
                                "response_message": {"type": "object", "description": "응답 메시지"},
                                "execution_time_ms": {"type": "number", "description": "실행 시간 (ms)"}
                            }
                        }
                    },
                    "incident_id": {"type": "string", "description": "인시던트 ID (선택사항)"},
                    "context": {"type": "string", "description": "워크플로우 맥락 정보"},
                    "user_id": {"type": "string", "description": "사용자 ID (선택사항)"}
                },
                "required": ["agent_interactions"]
            },
            tool_type="api"
        )
        
        # 설정 값들 - prism-core가 있으면 사용하고, 없으면 기본값 사용
        if PRISM_CORE_AVAILABLE:
            self._weaviate_url = weaviate_url or settings.WEAVIATE_URL
            self._openai_base_url = openai_base_url or settings.VLLM_OPENAI_BASE_URL
            self._openai_api_key = openai_api_key or settings.OPENAI_API_KEY
            self._model_name = model_name or settings.DEFAULT_MODEL
        else:
            self._weaviate_url = weaviate_url or "http://weaviate:8080"
            self._openai_base_url = openai_base_url or "http://localhost:8000/v1"
            self._openai_api_key = openai_api_key or "dummy-key"
            self._model_name = model_name or "gpt-3.5-turbo"
        
        self._client_id = client_id
        
        # 에이전트별 클래스명 설정
        self._class_history = f"{class_prefix}History"
        
        # OpenAI 클라이언트 초기화
        self._openai_client = None
        if OPENAI_AVAILABLE:
            self._initialize_openai()

    def _initialize_openai(self) -> None:
        """OpenAI 클라이언트 초기화"""
        try:
            self._openai_client = OpenAI(
                base_url=self._openai_base_url,
                api_key=self._openai_api_key
            )
            print("✅ OpenAI 클라이언트 초기화 완료")
        except Exception as e:
            print(f"⚠️  OpenAI 클라이언트 초기화 실패: {str(e)}")
            self._openai_client = None

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Tool 실행"""
        try:
            params = request.parameters
            agent_interactions = params["agent_interactions"]
            incident_id = params.get("incident_id", "")
            context = params.get("context", "")
            user_id = params.get("user_id", "")
            
            # 1. 에이전트 상호작용 기본 분석
            basic_analysis = self._analyze_basic_metrics(agent_interactions)
            
            # 2. LLM을 통한 지능형 요약
            intelligent_summary = await self._generate_intelligent_summary(
                agent_interactions, incident_id, context
            )
            
            # 3. 워크플로우 패턴 분석
            workflow_patterns = self._analyze_workflow_patterns(agent_interactions)
            
            # 4. 성능 및 효율성 분석
            performance_analysis = self._analyze_performance(agent_interactions)
            
            # 5. 결과 통합
            summary_result = {
                "incident_id": incident_id,
                "summary_generated_at": datetime.now(timezone.utc).isoformat(),
                "basic_metrics": basic_analysis,
                "intelligent_summary": intelligent_summary,
                "workflow_patterns": workflow_patterns,
                "performance_analysis": performance_analysis,
                "total_interactions": len(agent_interactions),
                "domain": "agent_interaction_summary"
            }
            
            return ToolResponse(
                success=True,
                data=summary_result
            )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                error=f"에이전트 상호작용 요약 실패: {str(e)}"
            )

    def _analyze_basic_metrics(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """기본 메트릭 분석"""
        if not interactions:
            return {}
        
        # 에이전트별 통계
        agent_stats = {}
        request_types = {}
        total_execution_time = 0
        
        for interaction in interactions:
            # 요청자/대상 에이전트 통계
            requester = interaction.get("requester", "unknown")
            target = interaction.get("target", "unknown")
            
            if requester not in agent_stats:
                agent_stats[requester] = {"sent_requests": 0, "avg_response_time": []}
            if target not in agent_stats:
                agent_stats[target] = {"received_requests": 0, "avg_response_time": []}
            
            agent_stats[requester]["sent_requests"] += 1
            agent_stats[target]["received_requests"] += 1
            
            # 요청 타입 통계
            request_type = interaction.get("request_type", "unknown")
            request_types[request_type] = request_types.get(request_type, 0) + 1
            
            # 실행 시간 통계
            exec_time = interaction.get("execution_time_ms", 0)
            total_execution_time += exec_time
            agent_stats[target]["avg_response_time"].append(exec_time)
        
        # 평균 응답 시간 계산
        for agent, stats in agent_stats.items():
            if stats.get("avg_response_time"):
                stats["avg_response_time"] = sum(stats["avg_response_time"]) / len(stats["avg_response_time"])
            else:
                stats["avg_response_time"] = 0
        
        return {
            "agent_statistics": agent_stats,
            "request_type_distribution": request_types,
            "total_execution_time_ms": total_execution_time,
            "average_execution_time_ms": total_execution_time / len(interactions) if interactions else 0
        }

    async def _generate_intelligent_summary(self, interactions: List[Dict[str, Any]], 
                                          incident_id: str, context: str) -> Dict[str, Any]:
        """LLM을 통한 지능형 요약 생성"""
        if not self._openai_client:
            # OpenAI가 없는 경우 기본 요약
            return self._basic_summary_analysis(interactions, incident_id, context)
        
        try:
            # 상호작용 데이터 구성
            interactions_text = ""
            for i, interaction in enumerate(interactions, 1):
                interactions_text += f"""
### 상호작용 {i}: {interaction.get('task_id', 'Unknown')}
- **요청자**: {interaction.get('requester', 'unknown')}
- **대상**: {interaction.get('target', 'unknown')}  
- **요청 타입**: {interaction.get('request_type', 'unknown')}
- **실행 시간**: {interaction.get('execution_time_ms', 0)}ms

**요청 내용**:
{json.dumps(interaction.get('request_message', {}), indent=2, ensure_ascii=False)}

**응답 내용**:
{json.dumps(interaction.get('response_message', {}), indent=2, ensure_ascii=False)}

**기존 요약**: {interaction.get('summary', '요약 없음')}

---
"""
            
            # LLM 프롬프트 구성
            prompt = f"""
다음 에이전트 상호작용 워크플로우를 분석하고 종합적인 요약을 생성해주세요:

**인시던트 ID**: {incident_id}
**맥락 정보**: {context}

**에이전트 상호작용 상세**:
{interactions_text}

다음 JSON 형식으로 종합 분석을 제공해주세요:
{{
    "workflow_summary": "전체 워크플로우의 핵심 요약 (2-3문장)",
    "key_findings": ["주요 발견사항1", "주요 발견사항2", "주요 발견사항3"],
    "agent_collaboration_effectiveness": "에이전트 간 협업 효과성 평가",
    "decision_quality": "의사결정 품질 평가",
    "process_efficiency": "프로세스 효율성 평가", 
    "recommendations": ["개선 권고사항1", "개선 권고사항2"],
    "success_indicators": ["성공 지표1", "성공 지표2"],
    "risk_factors": ["위험 요소1", "위험 요소2"],
    "overall_assessment": "전반적 평가 및 결론"
}}
"""
            
            # LLM 호출
            response = self._openai_client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": "당신은 에이전트 워크플로우 분석 전문가입니다. 다중 에이전트 시스템의 상호작용을 객관적이고 통찰력 있게 분석해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # 응답 파싱
            result_text = response.choices[0].message.content
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본 분석 반환
                return self._basic_summary_analysis(interactions, incident_id, context)
                
        except Exception as e:
            print(f"⚠️  LLM 요약 생성 실패: {str(e)}")
            return self._basic_summary_analysis(interactions, incident_id, context)

    def _basic_summary_analysis(self, interactions: List[Dict[str, Any]], 
                               incident_id: str, context: str) -> Dict[str, Any]:
        """기본 요약 분석 (LLM 없이)"""
        if not interactions:
            return {"workflow_summary": "상호작용 데이터가 없습니다."}
        
        # 기본 통계 기반 요약
        agent_types = set()
        request_types = set()
        total_time = 0
        
        for interaction in interactions:
            agent_types.add(interaction.get("requester", "unknown"))
            agent_types.add(interaction.get("target", "unknown"))
            request_types.add(interaction.get("request_type", "unknown"))
            total_time += interaction.get("execution_time_ms", 0)
        
        return {
            "workflow_summary": f"총 {len(interactions)}개의 에이전트 상호작용이 {len(agent_types)}개 에이전트 간에 발생했습니다.",
            "key_findings": [
                f"참여 에이전트: {', '.join(agent_types)}",
                f"요청 타입: {', '.join(request_types)}",
                f"총 실행 시간: {total_time}ms"
            ],
            "agent_collaboration_effectiveness": "기본 분석 - 추가 정보 필요",
            "decision_quality": "기본 분석 - 추가 정보 필요", 
            "process_efficiency": f"평균 {total_time/len(interactions):.1f}ms per interaction",
            "recommendations": ["상세한 분석을 위해 LLM 모듈을 활성화하세요"],
            "success_indicators": ["모든 상호작용이 완료됨"],
            "risk_factors": ["분석 제한으로 인한 위험 평가 불가"],
            "overall_assessment": "기본 워크플로우 완료, 상세 분석 필요"
        }

    def _analyze_workflow_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """워크플로우 패턴 분석"""
        if not interactions:
            return {}
        
        # 요청 체인 분석
        request_chain = []
        agent_sequence = []
        
        for interaction in interactions:
            requester = interaction.get("requester", "unknown")
            target = interaction.get("target", "unknown")
            request_type = interaction.get("request_type", "unknown")
            
            request_chain.append(f"{requester} → {target} ({request_type})")
            agent_sequence.extend([requester, target])
        
        # 에이전트 네트워크 분석
        agent_connections = {}
        for interaction in interactions:
            requester = interaction.get("requester", "unknown")
            target = interaction.get("target", "unknown")
            
            if requester not in agent_connections:
                agent_connections[requester] = set()
            agent_connections[requester].add(target)
        
        # 패턴 통계
        unique_agents = set(agent_sequence)
        orchestration_requests = sum(1 for i in interactions if i.get("requester") == "orchestration")
        
        return {
            "request_chain": request_chain,
            "unique_agents_count": len(unique_agents),
            "agent_network": {k: list(v) for k, v in agent_connections.items()},
            "orchestration_dominance": orchestration_requests / len(interactions) if interactions else 0,
            "workflow_complexity": len(request_chain) / len(unique_agents) if unique_agents else 0
        }

    def _analyze_performance(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """성능 및 효율성 분석"""
        if not interactions:
            return {}
        
        execution_times = [i.get("execution_time_ms", 0) for i in interactions]
        execution_times.sort()
        
        # 성능 통계
        total_time = sum(execution_times)
        avg_time = total_time / len(execution_times)
        median_time = execution_times[len(execution_times) // 2]
        
        # 이상치 탐지 (평균의 2배 이상)
        outliers = [t for t in execution_times if t > avg_time * 2]
        
        # 효율성 등급
        if avg_time < 1000:  # 1초 미만
            efficiency_grade = "Excellent"
        elif avg_time < 5000:  # 5초 미만
            efficiency_grade = "Good"
        elif avg_time < 10000:  # 10초 미만
            efficiency_grade = "Average"
        else:
            efficiency_grade = "Needs Improvement"
        
        return {
            "total_execution_time_ms": total_time,
            "average_execution_time_ms": avg_time,
            "median_execution_time_ms": median_time,
            "min_execution_time_ms": min(execution_times),
            "max_execution_time_ms": max(execution_times),
            "performance_outliers": len(outliers),
            "efficiency_grade": efficiency_grade,
            "parallelization_potential": len(interactions) - sum(1 for i in interactions if i.get("requester") == "orchestration")
        }