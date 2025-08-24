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

        # Set tool registry for managers
        self.agent_manager.set_tool_registry(self.tool_registry)
        self.workflow_manager.set_tool_registry(self.tool_registry)

        # Local cache for agent object
        self._agent: Optional[Agent] = None
        
        # Memory tool reference for direct access
        self._memory_tool = self.orch_tool_setup.get_memory_tool()
        
        # Print tool setup information
        self.orch_tool_setup.print_tool_info()

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

            # Register agent
            self.agent_manager.register_agent(agent)
            self._agent = agent
            
            print(f"✅ 오케스트레이션 에이전트 '{self.agent_name}' 등록 완료")

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
        메인 오케스트레이션 메서드
        
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
            # Ensure agent is registered
            if not self._agent:
                self.register_orchestration_agent()

            # Prepare context
            context = {
                "user_id": user_id,
                "prompt": prompt,
                "timestamp": self._get_timestamp()
            }

            # Create agent invoke request with all parameters
            request = AgentInvokeRequest(
                prompt=prompt,
                user_id=user_id,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                use_tools=use_tools,
                max_tool_calls=max_tool_calls,
                extra_body=extra_body
            )

            # Invoke agent with tools using the correct method
            response = await self.llm.invoke_agent(self._agent, request)
            
            # Add context information to metadata
            if response.metadata is None:
                response.metadata = {}
            response.metadata.update(context)
            
            # Save conversation to memory if user_id is provided
            if user_id and self._memory_tool:
                await self._save_conversation_to_memory(user_id, prompt, response.text)
            
            return response

        except Exception as e:
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