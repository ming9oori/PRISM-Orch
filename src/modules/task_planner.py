from typing import List, Dict, Any, Optional
import json
from ..modules.openai_llm_service import OpenAIChatLLMService
from ..modules.rag_system import RAGSystem
from ..api.schemas import TaskInfo
from ..core.config import settings


class TaskPlanner:
    """
    RAG 기반의 Task Decomposition and Planning을 담당하는 클래스입니다.
    외부 LLM을 활용하여 사용자 요청을 분석하고, 관련 지식을 검색하여
    체계적인 작업 계획을 수립합니다.
    """
    
    def __init__(self):
        """
        TaskPlanner를 초기화합니다.
        LLM 서비스와 RAG 시스템을 설정합니다.
        """
        self.llm_service = OpenAIChatLLMService(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini"  # 또는 다른 모델
        )
        self.rag_system = RAGSystem()
        
        print(f"INFO:     TaskPlanner initialized with LLM service")

    def decompose_and_plan(self, user_query: str, user_id: Optional[str] = None) -> List[TaskInfo]:
        """
        사용자 쿼리를 분석하고 작업을 분해하여 계획을 수립합니다.

        Args:
            user_query (str): 사용자 요청
            user_id (Optional[str]): 사용자 ID

        Returns:
            List[TaskInfo]: 작업 계획 목록
        """
        print(f"INFO:     Starting task decomposition for query: '{user_query}'")
        
        # 1단계: RAG를 통한 관련 지식 검색
        knowledge_context = self._retrieve_relevant_knowledge(user_query, user_id)
        
        # 2단계: LLM을 통한 작업 분해 및 계획 수립
        task_plan = self._generate_task_plan(user_query, knowledge_context)
        
        # 3단계: TaskInfo 객체로 변환
        tasks = self._convert_to_task_info(task_plan, user_query)
        
        print(f"INFO:     Generated {len(tasks)} tasks from decomposition")
        return tasks

    def _retrieve_relevant_knowledge(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        쿼리와 관련된 지식을 검색합니다.
        """
        # 외부 지식 검색
        research_docs = self.rag_system.retrieve_knowledge(query, top_k=5)
        
        # 사용자 메모리 검색 (사용자 ID가 있는 경우)
        memory_docs = []
        if user_id:
            memory_docs = self.rag_system.retrieve_from_memory(user_id, top_k=3)
        
        return {
            "research_documents": research_docs,
            "user_memory": memory_docs,
            "query": query
        }

    def _generate_task_plan(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM을 사용하여 작업 계획을 생성합니다.
        """
        # 프롬프트 구성
        prompt = self._build_planning_prompt(query, context)
        
        # LLM 호출
        try:
            from core.llm.schemas import LLMGenerationRequest
            
            request = LLMGenerationRequest(
                prompt=prompt,
                temperature=0.3,  # 창의성과 일관성의 균형
                max_tokens=2000,
                stop=None
            )
            
            response = self.llm_service.generate(request)
            
            # JSON 응답 파싱
            try:
                plan = json.loads(response)
                return plan
            except json.JSONDecodeError:
                print(f"WARNING: Failed to parse LLM response as JSON: {response}")
                # 폴백: 기본 계획 반환
                return self._generate_fallback_plan(query)
                
        except Exception as e:
            print(f"ERROR: LLM generation failed: {e}")
            return self._generate_fallback_plan(query)

    def _build_planning_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """
        작업 계획 생성을 위한 프롬프트를 구성합니다.
        """
        research_docs = context.get("research_documents", [])
        user_memory = context.get("user_memory", [])
        
        prompt = f"""
당신은 작업 분해 및 계획 수립 전문가입니다. 사용자의 요청을 분석하고 체계적인 작업 계획을 수립해주세요.

사용자 요청: {query}

관련 연구 문서:
{chr(10).join([f"- {doc}" for doc in research_docs]) if research_docs else "- 관련 문서 없음"}

사용자 과거 상호작용:
{chr(10).join([f"- {memory}" for memory in user_memory]) if user_memory else "- 과거 상호작용 없음"}

다음 JSON 형식으로 작업 계획을 반환해주세요:
{{
    "analysis": {{
        "intent": "사용자 의도 분석",
        "complexity": "작업 복잡도 (low/medium/high)",
        "estimated_duration": "예상 소요 시간"
    }},
    "tasks": [
        {{
            "id": "고유 작업 ID",
            "name": "작업명",
            "description": "상세 설명",
            "intent": "작업 의도",
            "assigned_agent_id": "담당 에이전트 ID",
            "dependencies": ["의존하는 작업 ID들"],
            "priority": "우선순위 (high/medium/low)",
            "estimated_duration": "예상 소요 시간"
        }}
    ],
    "recommendations": [
        "추가 권장사항들"
    ]
}}

JSON만 반환하고 다른 텍스트는 포함하지 마세요.
"""
        return prompt

    def _generate_fallback_plan(self, query: str) -> Dict[str, Any]:
        """
        LLM 실패 시 사용할 기본 계획을 생성합니다.
        """
        return {
            "analysis": {
                "intent": "general_analysis",
                "complexity": "medium",
                "estimated_duration": "30 minutes"
            },
            "tasks": [
                {
                    "id": "task_001",
                    "name": f"기본 분석: {query}",
                    "description": "사용자 요청에 대한 기본 분석 수행",
                    "intent": "data_retrieval",
                    "assigned_agent_id": "agent_monitor_001",
                    "dependencies": [],
                    "priority": "high",
                    "estimated_duration": "15 minutes"
                }
            ],
            "recommendations": [
                "LLM 서비스 연결을 확인하세요",
                "기본 분석을 수행합니다"
            ]
        }

    def _convert_to_task_info(self, plan: Dict[str, Any], original_query: str) -> List[TaskInfo]:
        """
        LLM 응답을 TaskInfo 객체로 변환합니다.
        """
        tasks = []
        
        for task_data in plan.get("tasks", []):
            task = TaskInfo(
                id=task_data.get("id", f"task_{len(tasks)+1:03d}"),
                name=task_data.get("name", "Unknown Task"),
                description=task_data.get("description", ""),
                intent=task_data.get("intent", "general"),
                assigned_agent_id=task_data.get("assigned_agent_id", "agent_monitor_001"),
                dependencies=task_data.get("dependencies", []),
                priority=task_data.get("priority", "medium"),
                status="pending",
                estimated_duration=task_data.get("estimated_duration", "15 minutes"),
                original_query=original_query
            )
            tasks.append(task)
        
        return tasks

    def refine_plan(self, current_tasks: List[TaskInfo], agent_results: Dict[str, Any]) -> List[TaskInfo]:
        """
        에이전트 결과를 바탕으로 작업 계획을 수정합니다.
        """
        print(f"INFO:     Refining plan based on agent results")
        
        # 에이전트 결과를 분석하여 계획 수정
        refined_tasks = []
        
        for task in current_tasks:
            agent_id = task.assigned_agent_id
            if agent_id in agent_results:
                result = agent_results[agent_id]
                
                # 결과에 따라 작업 상태 업데이트
                if result.get("success", False):
                    task.status = "completed"
                elif result.get("partial_success", False):
                    task.status = "in_progress"
                    # 필요시 하위 작업 추가
                    if result.get("requires_followup", False):
                        followup_task = TaskInfo(
                            id=f"{task.id}_followup",
                            name=f"{task.name} - 후속 작업",
                            description="이전 작업의 후속 처리",
                            intent=task.intent,
                            assigned_agent_id=agent_id,
                            dependencies=[task.id],
                            priority="high",
                            status="pending"
                        )
                        refined_tasks.append(followup_task)
                else:
                    task.status = "failed"
                    # 실패 시 대안 작업 추가
                    alternative_task = TaskInfo(
                        id=f"{task.id}_alternative",
                        name=f"{task.name} - 대안 접근",
                        description="실패한 작업의 대안적 접근",
                        intent=task.intent,
                        assigned_agent_id=agent_id,
                        dependencies=[task.id],
                        priority="high",
                        status="pending"
                    )
                    refined_tasks.append(alternative_task)
            
            refined_tasks.append(task)
        
        return refined_tasks 