from typing import List, Dict, Any, Optional, Tuple
import uuid

from ..api.schemas import (
    UserQueryInput,
    OrchestrationResponse,
    TaskInfo,
)
from ..modules.agent_manager import AgentManager
from ..modules.rag_system import RAGSystem
from ..modules.nlp_processor import NLPProcessor
from ..modules.constraint_manager import ConstraintManager
from ..modules.task_planner import TaskPlanner


class OrchestrationAgent:
    """
    End-to-end orchestration agent coordinating the full pipeline.

    Responsibilities:
    1) Manage information of 3 sub-agents (monitoring, prediction, autonomous control)
    2) Rewrite user request into task-friendly form
    3) Store and retrieve external research vectors and agent memory vectors
    4) Retrieve from vector DBs, derive task plan, and perform reflection
    5) Update plan based on agents' actual responses
    6) Generate final answer by summarizing all outputs
    """

    def __init__(self) -> None:
        self.agent_manager = AgentManager()
        self.rag_system = RAGSystem()
        self.nlp = NLPProcessor()
        self.constraints = ConstraintManager()
        self.task_planner = TaskPlanner()

        # Placeholders for future vector DB adapters (prism-core integration)
        # self.research_vector_client = WeaviateClient(...)
        # self.memory_vector_client = WeaviateClient(...)

    # --- Step 1: Agent information management ---
    def list_sub_agents(self) -> List[Dict[str, Any]]:
        return [agent.model_dump() for agent in self.agent_manager.list_agents()]

    # --- Step 2: User request rewriting ---
    def rewrite_user_request(self, query: str) -> Dict[str, Any]:
        analysis = self.nlp.analyze_query(query)
        task_friendly = {
            "original": query,
            "intent": analysis.get("intent", "unknown"),
            "entities": analysis.get("entities", {}),
        }
        return task_friendly

    # --- Step 3: Vector storage and retrieval (stubs, to be backed by prism-core) ---
    def store_research_snippets(self, session_id: str, snippets: List[str]) -> None:
        # TODO: persist to external research vector DB via prism-core
        _ = (session_id, snippets)

    def store_agent_memory(self, session_id: str, notes: List[str]) -> None:
        # TODO: persist to agent-memory vector DB via prism-core
        _ = (session_id, notes)

    def retrieve_context(self, query: str, user_id: Optional[str]) -> Tuple[List[str], List[str]]:
        research = self.rag_system.retrieve_knowledge(query, top_k=3)
        memory = self.rag_system.retrieve_from_memory(user_id or "anonymous", top_k=3)
        return research, memory

    # --- Step 4: Planning and reflection ---
    def build_initial_plan(self, task_friendly: Dict[str, Any]) -> List[TaskInfo]:
        """
        RAG 기반의 Task Decomposition and Planning을 수행합니다.
        """
        original_query = task_friendly.get("original", "")
        user_id = task_friendly.get("user_id")
        
        # TaskPlanner를 사용하여 RAG 기반 작업 계획 수립
        tasks = self.task_planner.decompose_and_plan(original_query, user_id)
        
        return tasks

    def reflect_and_adjust_plan(self, tasks: List[TaskInfo], agent_results: Dict[str, Any]) -> List[TaskInfo]:
        """
        에이전트 결과를 바탕으로 작업 계획을 반영하고 조정합니다.
        """
        # TaskPlanner의 refine_plan 메서드를 사용하여 계획 수정
        refined_tasks = self.task_planner.refine_plan(tasks, agent_results)
        return refined_tasks

    # --- Step 5: Incorporate agent responses into plan ---
    def update_plan_with_agent_result(self, tasks: List[TaskInfo], task_id: str, agent_output: str) -> None:
        for t in tasks:
            if t.id == task_id:
                t.status = "completed"
                # Optionally annotate task name with key result signal
                if agent_output:
                    t.name = f"{t.name} -> 결과 요약: {agent_output[:60]}..."
                break

    # --- Step 6: Final answer synthesis ---
    def synthesize_final_answer(
        self,
        original_query: str,
        research_docs: List[str],
        memory_docs: List[str],
        tasks: List[TaskInfo],
    ) -> str:
        lines: List[str] = []
        lines.append(f"요청: {original_query}")
        if research_docs:
            lines.append("외부 참고 요약: " + "; ".join(doc[:80] for doc in research_docs))
        if memory_docs:
            lines.append("과거 메모리 참조: " + "; ".join(mem[:80] for mem in memory_docs))
        lines.append("수행 계획 및 진행:")
        for idx, t in enumerate(tasks, start=1):
            dep = f" deps={t.dependencies}" if t.dependencies else ""
            lines.append(f"  {idx}. [{t.status}] {t.name} (agent={t.assigned_agent_id}){dep}")
        lines.append("최종 결론: 상기 단계의 결과를 종합하여 제어 방안과 후속 조치를 권고합니다.")
        return "\n".join(lines)

    # --- Public entrypoint ---
    def run(self, user_input: UserQueryInput) -> OrchestrationResponse:
        session_id = user_input.session_id or f"session_{uuid.uuid4()}"

        # 2) Rewrite request
        rewritten = self.rewrite_user_request(user_input.query)

        # 3) Retrieve from research + memory
        research_docs, memory_docs = self.retrieve_context(user_input.query, user_id=session_id)

        # Store stubs (future persistence)
        self.store_research_snippets(session_id, research_docs)
        self.store_agent_memory(session_id, [f"query: {user_input.query}"])

        # 4) Build plan and reflect
        tasks = self.build_initial_plan(rewritten)
        
        # 초기 계획 수립 후 에이전트 실행 시뮬레이션
        agent_results = {}
        for t in tasks:
            mock_agent_output = f"{t.intent} 결과"
            self.update_plan_with_agent_result(tasks, t.id, mock_agent_output)
            agent_results[t.assigned_agent_id] = {
                "success": True,
                "output": mock_agent_output
            }
        
        # 에이전트 결과를 바탕으로 계획 조정
        tasks = self.reflect_and_adjust_plan(tasks, agent_results)

        # Validate constraints (mocked always valid)
        _ = self.constraints.check_plan_is_valid([t.model_dump() for t in tasks])

        # 6) Final synthesis
        final_answer = self.synthesize_final_answer(
            original_query=user_input.query,
            research_docs=research_docs,
            memory_docs=memory_docs,
            tasks=tasks,
        )

        # Flow chart data assembly
        nodes = [
            {"id": t.id, "label": t.name, "agent": t.assigned_agent_id, "status": t.status}
            for t in tasks
        ]
        edges = []
        id_to_task = {t.id: t for t in tasks}
        for t in tasks:
            for dep in t.dependencies:
                if dep in id_to_task:
                    edges.append({"from": dep, "to": t.id})

        response = OrchestrationResponse(
            session_id=session_id,
            final_answer=final_answer,
            flow_chart_data={"nodes": nodes, "edges": edges},
            supporting_documents=research_docs,
            task_history=tasks,
        )
        return response 