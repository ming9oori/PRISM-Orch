from typing import Any, Dict, List, Optional
import json
import requests

from core.llm.prism_llm_service import PrismLLMService
from core.llm.schemas import Agent, AgentInvokeRequest, AgentResponse, LLMGenerationRequest
from core.tools import BaseTool, ToolRequest, ToolResponse, ToolRegistry

from ..core.config import settings


class PrismOrchestrator:
    """
    High-level orchestrator for PRISM-Orch that uses prism-core's PrismLLMService.

    Responsibilities:
    - Initialize PrismLLMService (OpenAI-Compatible vLLM client + PRISM-Core API client)
    - Register default tools and the main orchestration agent
    - Perform task decomposition as the first step (agent-side), then invoke with tools
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

        self.llm = PrismLLMService(
            model_name=settings.VLLM_MODEL,
            simulate_delay=False,
            tool_registry=ToolRegistry(),
            llm_service_url=core_api,
            agent_name=self.agent_name,
            openai_base_url=base_url,
            api_key=api_key,
        )

        # Auto-register default tools for orchestration
        self.register_default_tools()

        # Local cache for agent object
        self._agent: Optional[Agent] = None

    # ------------------------ Tool definitions ------------------------
    class RAGSearchTool(BaseTool):
        def __init__(self):
            super().__init__(
                name="rag_search",
                description="지식 베이스에서 관련 정보를 검색합니다",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "검색할 쿼리"},
                        "top_k": {"type": "integer", "description": "반환할 문서 수", "default": 3},
                        "domain": {"type": "string", "enum": ["research", "history"], "description": "검색 도메인 (연구/기술문서 or 사용자 수행내역)", "default": "research"}
                    },
                    "required": ["query"]
                }
            )
            self._initialized = False
            self._class_research = "OrchResearch"
            self._class_history = "OrchHistory"
            self._class_compliance = "OrchCompliance"
            self._client_id = "orch"
            self._encoder = settings.VECTOR_ENCODER_MODEL
            self._vector_dim = settings.VECTOR_DIM
            self._base = settings.PRISM_CORE_BASE_URL

        def _ensure_index_and_seed(self) -> None:
            if self._initialized:
                return
            # Create index
            try:
                # Research index
                requests.post(
                    f"{self._base}/api/vector-db/indices",
                    json={
                        "class_name": self._class_research,
                        "description": "Papers/technical docs knowledge base",
                        "vector_dimension": self._vector_dim,
                        "encoder_model": self._encoder,
                        "properties": []
                    },
                    params={"client_id": self._client_id},
                    timeout=10,
                )
                research_docs = [
                    {"title": f"Paper {i+1}", "content": f"제조 공정 최적화 기술 문서 {i+1}: 공정 제어, 안전 규정, 예지 정비, 데이터 기반 분석.", "metadata": {}}
                    for i in range(10)
                ]
                requests.post(
                    f"{self._base}/api/vector-db/documents/{self._class_research}/batch",
                    json=research_docs,
                    params={"client_id": self._client_id, "encoder_model": self._encoder},
                    timeout=15,
                )
                # History index
                requests.post(
                    f"{self._base}/api/vector-db/indices",
                    json={
                        "class_name": self._class_history,
                        "description": "All users' past execution logs",
                        "vector_dimension": self._vector_dim,
                        "encoder_model": self._encoder,
                        "properties": []
                    },
                    params={"client_id": self._client_id},
                    timeout=10,
                )
                history_docs = [
                    {"title": f"History {i+1}", "content": f"사용자 수행 내역 {i+1}: 압력 이상 대응, 점검 절차 수행, 원인 분석 리포트, 후속 조치 완료.", "metadata": {}}
                    for i in range(10)
                ]
                requests.post(
                    f"{self._base}/api/vector-db/documents/{self._class_history}/batch",
                    json=history_docs,
                    params={"client_id": self._client_id, "encoder_model": self._encoder},
                    timeout=15,
                )
                # Compliance index
                requests.post(
                    f"{self._base}/api/vector-db/indices",
                    json={
                        "class_name": self._class_compliance,
                        "description": "Safety/legal/company compliance rules",
                        "vector_dimension": self._vector_dim,
                        "encoder_model": self._encoder,
                        "properties": []
                    },
                    params={"client_id": self._client_id},
                    timeout=10,
                )
                compliance_docs = [
                    {"title": f"Rule {i+1}", "content": f"안전 법규 및 사내 규정 {i+1}: 잠금/표시 절차(LOTO), 보호구 착용, 위험물 취급, 점검 기록 보관, 승인 절차 준수.", "metadata": {}}
                    for i in range(10)
                ]
                requests.post(
                    f"{self._base}/api/vector-db/documents/{self._class_compliance}/batch",
                    json=compliance_docs,
                    params={"client_id": self._client_id, "encoder_model": self._encoder},
                    timeout=15,
                )
                
                # Validate and regenerate embeddings if needed
                self._validate_and_regenerate_embeddings()
                
                self._initialized = True
            except Exception:
                # Best-effort; keep going even if seeding fails
                self._initialized = True

        def _validate_and_regenerate_embeddings(self) -> None:
            """벡터 임베딩이 없는 문서들을 감지하고 재생성합니다."""
            try:
                # Check each class for documents without embeddings
                classes_to_check = [self._class_research, self._class_history, self._class_compliance]
                
                for class_name in classes_to_check:
                    # Get all documents from the class using prism-core API
                    resp = requests.get(
                        f"{self._base}/api/vector-db/documents/{class_name}",
                        params={"client_id": self._client_id, "limit": 100},
                        timeout=10,
                    )
                    
                    if resp.status_code == 200:
                        documents = resp.json()
                        documents_without_embeddings = []
                        
                        for doc in documents:
                            # Check if document has vector weights (embeddings)
                            if not doc.get("vectorWeights") or doc["vectorWeights"] is None:
                                documents_without_embeddings.append(doc)
                        
                        if documents_without_embeddings:
                            print(f"⚠️  Found {len(documents_without_embeddings)} documents without embeddings in {class_name}")
                            
                            # Delete documents without embeddings
                            doc_ids = [doc["id"] for doc in documents_without_embeddings]
                            delete_resp = requests.post(
                                f"{self._base}/api/vector-db/documents/{class_name}/delete-batch",
                                json=doc_ids,
                                params={"client_id": self._client_id},
                                timeout=15,
                            )
                            
                            if delete_resp.status_code == 200:
                                print(f"✅ Deleted {len(doc_ids)} documents without embeddings from {class_name}")
                                
                                # Re-add documents with proper embeddings
                                docs_to_add = []
                                for doc in documents_without_embeddings:
                                    docs_to_add.append({
                                        "title": doc["properties"].get("title", ""),
                                        "content": doc["properties"].get("content", ""),
                                        "metadata": doc["properties"].get("metadata", {})
                                    })
                                
                                add_resp = requests.post(
                                    f"{self._base}/api/vector-db/documents/{class_name}/batch",
                                    json=docs_to_add,
                                    params={"client_id": self._client_id, "encoder_model": self._encoder},
                                    timeout=15,
                                )
                                
                                if add_resp.status_code == 200:
                                    print(f"✅ Regenerated embeddings for {len(docs_to_add)} documents in {class_name}")
                                else:
                                    print(f"❌ Failed to regenerate embeddings for {class_name}: {add_resp.status_code}")
                            else:
                                print(f"❌ Failed to delete documents without embeddings from {class_name}: {delete_resp.status_code}")
                        else:
                            print(f"✅ All documents in {class_name} have proper embeddings")
                            
            except Exception as e:
                print(f"⚠️  Error during embedding validation: {str(e)}")
                # Continue execution even if validation fails

        async def execute(self, request: ToolRequest) -> ToolResponse:
            query = request.parameters.get("query", "")
            top_k = int(request.parameters.get("top_k", 3))
            domain = request.parameters.get("domain", "research")
            self._ensure_index_and_seed()
            
            # Validate embeddings before search (safely)
            try:
                self._validate_and_regenerate_embeddings()
            except Exception as e:
                print(f"⚠️  Embedding validation failed, continuing with search: {str(e)}")
            
            try:
                class_name = (
                    self._class_research if domain == "research"
                    else self._class_history if domain == "history"
                    else self._class_compliance
                )
                resp = requests.post(
                    f"{self._base}/api/vector-db/search/{class_name}",
                    json={"query": query, "limit": top_k},
                    params={"client_id": self._client_id, "encoder_model": self._encoder},
                    timeout=10,
                )
                if resp.status_code == 200:
                    results = resp.json()
                    docs = [f"{r.get('score', 0):.3f} | {r.get('content', '')}" for r in results]
                    return ToolResponse(
                        tool_name=self.name,
                        success=True,
                        result={"documents": docs},
                        message=f"검색 완료: {domain}에서 {len(docs)}개 문서 반환",
                    )
                else:
                    return ToolResponse(
                        tool_name=self.name,
                        success=False,
                        result={},
                        message=f"검색 실패({domain}): HTTP {resp.status_code}",
                    )
            except Exception as e:
                return ToolResponse(
                    tool_name=self.name,
                    success=False,
                    result={},
                    message=f"검색 예외({domain}): {str(e)[:80]}",
                )

    class MemorySearchTool(BaseTool):
        def __init__(self):
            super().__init__(
                name="memory_search",
                description="사용자의 과거 상호작용 기록을 검색합니다",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "사용자 ID"},
                        "top_k": {"type": "integer", "description": "반환할 메모리 수", "default": 2}
                    },
                    "required": ["user_id"]
                }
            )
        async def execute(self, request: ToolRequest) -> ToolResponse:
            user_id = request.parameters.get("user_id", "")
            top_k = request.parameters.get("top_k", 2)
            mock_memories = [
                f"{user_id}의 과거 경험 1: 지난주 A-1 라인 압력 문제 해결 경험",
                f"{user_id}의 과거 경험 2: 압력 센서 교체 작업 수행 이력",
            ]
            return ToolResponse(
                tool_name=self.name,
                success=True,
                result={"memories": mock_memories[:top_k]},
                message=f"메모리 검색 완료: {len(mock_memories[:top_k])}개 기록 반환",
            )

    # ------------------------ Setup methods ------------------------
    def register_default_tools(self) -> None:
        # Task decomposition is handled agent-side (first step), so we only register external-context tools here.
        for tool_cls in (self.RAGSearchTool, self.MemorySearchTool):
            tool = tool_cls()
            self.llm.register_tool(tool)

    def ensure_agent(self) -> Agent:
        if self._agent is None:
            self._agent = Agent(
                name=self.agent_name,
                description="사용자 요청을 분석하고 적절한 작업을 분해하여 오케스트레이션하는 에이전트",
                role_prompt=(
                    "당신은 제조업 전문 오케스트레이션 에이전트입니다.\n"
                    "1) 사용자 요청을 먼저 작업 단위로 분해합니다(도구 없이).\n"
                    "2) 관련 지식과 사용자 기록을 검색하고 요약합니다(필요시 도구 사용).\n"
                    "3) 작업 우선순위 및 의존성을 설정하고 실행계획을 제시합니다.\n"
                    "4) 명확하고 실행가능한 대응 방안을 제시합니다.\n"
                ),
                tools=["rag_search", "memory_search"],
            )
            # Register to PRISM-Core for visibility (best-effort)
            self.llm.register_agent(self._agent)
            self.llm.assign_tools_to_agent(self._agent.name, self._agent.tools)
        return self._agent

    # ------------------------ Agent-side task decomposition ------------------------
    def _decompose_tasks_llm(self, user_query: str, *, temperature: float = 0.2, max_tokens: int = 600) -> Dict[str, Any]:
        """
        Perform initial task decomposition using LLM (no predefined categories, no tools).
        Returns a dict with keys: {"tasks": [...], "analysis": {...}}. Falls back safely.
        """
        system_prompt = (
            "당신은 전문 오케스트레이션 플래너입니다. 사용자 요청을 도메인에 상관없이\n"
            "도구를 사용하지 않고 먼저 작업 단위로 분해하세요. JSON만 출력하세요.\n"
            "형식은 다음과 같습니다:\n"
            "{\n  \"tasks\": [ {\"id\": \"task_001\", \"name\": \"...\", \"description\": \"...\", \"priority\": \"high|medium|low\", \"estimated_time\": \"10분\"}, ... ],\n"
            "  \"analysis\": { \"intent\": \"...\", \"estimated_total_time\": \"NN분\" }\n}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"요청: {user_query}"},
        ]
        try:
            text = self.llm.generate(
                LLMGenerationRequest(
                    messages=messages,
                    extra_body={"tool_choice": "none"},
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
            data = json.loads(text)
            tasks = data.get("tasks", [])
            analysis = data.get("analysis", {})
            if not isinstance(tasks, list) or not isinstance(analysis, dict):
                raise ValueError("invalid schema")
            return {"tasks": tasks, "analysis": analysis}
        except Exception:
            # Safe fallback: single generic task
            fallback_tasks = [
                {"id": "task_001", "name": "요청 분석 및 계획 수립", "description": "사용자 요청을 분석하고 실행 가능한 하위 작업으로 분해", "priority": "medium", "estimated_time": "15분"}
            ]
            return {"tasks": fallback_tasks, "analysis": {"intent": "general", "estimated_total_time": "15분"}}

    # ------------------------ Invoke ------------------------
    async def invoke(self, prompt: str, *, user_id: Optional[str] = None, max_tokens: int = 800, temperature: float = 0.3, extra_body: Optional[Dict[str, Any]] = None) -> AgentResponse:
        agent = self.ensure_agent()
        # 1) LLM-based task decomposition (first step, no tools, no predefined categories)
        decomp = self._decompose_tasks_llm(prompt, temperature=0.2, max_tokens=600)
        # 2) Inject decomposition as context into the user prompt
        enriched_prompt = (
            f"{prompt}\n\n[사전 작업 분해 결과]\n"
            f"의도: {decomp['analysis']['intent']} / 총 예상 시간: {decomp['analysis']['estimated_total_time']}\n"
            f"작업목록: "
            + "; ".join(f"{t['id']}:{t['name']}({t['priority']},{t['estimated_time']})" for t in decomp["tasks"])
            + "\n이 분해 결과를 참고하여 지식/메모리 검색과 최종 대응안을 제시하세요."
        )
        # Ensure tool usage is enabled by default
        if extra_body is None:
            extra_body = {"tool_choice": "auto"}
        else:
            extra_body = {"tool_choice": "auto", **extra_body}
        req = AgentInvokeRequest(
            prompt=enriched_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=None,
            use_tools=True,
            max_tool_calls=3,
            extra_body=extra_body,
            user_id=user_id,
        )
        base_resp = await self.llm.invoke_agent(agent, req)

        # 3) Explicit RAG pulls for research/history (to be included in final report)
        research_docs, research_tr = await self._run_rag("research", prompt, top_k=5)
        history_docs, history_tr = await self._run_rag("history", prompt, top_k=5)

        # 4) Render final markdown consolidation
        final_md = self._render_markdown_summary(
            user_query=prompt,
            decomp=decomp,
            research_docs=research_docs,
            history_docs=history_docs,
            llm_answer=base_resp.text or "",
        )

        # 5) Compliance search and assessment
        compliance_docs, compliance_tr = await self._run_rag("compliance", final_md, top_k=5)
        assessment = self._assess_compliance(final_md, compliance_docs)
        verdict_block = (
            "\n\n## 규정 준수 판단\n"
            f"- 결과: {'만족' if assessment.get('pass') else '미흡'}\n"
            + ("- 사유: " + "; ".join(assessment.get('reasons', [])) + "\n" if assessment.get('reasons') else "")
            + ("- 보완조치: " + "; ".join(assessment.get('required_actions', [])) + "\n" if assessment.get('required_actions') else "")
        )
        final_text = final_md + verdict_block

        # 6) Assemble final AgentResponse
        tools_used = list(base_resp.tools_used)
        tool_results = list(base_resp.tool_results)
        # Append explicit rag executions
        tools_used += ["rag_search", "rag_search", "rag_search"]
        if research_tr:
            tool_results.append({"tool": "rag_search", "result": {"domain": "research", "documents": research_docs}, "message": research_tr.message if hasattr(research_tr, 'message') else ""})
        if history_tr:
            tool_results.append({"tool": "rag_search", "result": {"domain": "history", "documents": history_docs}, "message": history_tr.message if hasattr(history_tr, 'message') else ""})
        if compliance_tr:
            tool_results.append({"tool": "rag_search", "result": {"domain": "compliance", "documents": compliance_docs}, "message": compliance_tr.message if hasattr(compliance_tr, 'message') else ""})

        metadata = {**(base_resp.metadata or {}), "compliance_checked": bool(assessment.get('pass') is not None)}
        return AgentResponse(
            text=final_text,
            tools_used=tools_used,
            tool_results=tool_results,
            metadata=metadata,
        )

    # ------------------------ Helpers ------------------------
    async def _run_rag(self, domain: str, query: str, *, top_k: int = 5) -> tuple[list[str], Optional[ToolResponse]]:
        """Execute rag_search for the given domain and return (documents, ToolResponse)."""
        try:
            rag_tool = self.llm.tool_registry.get_tool("rag_search")
            if rag_tool is None:
                return [], None
            tr = ToolRequest(tool_name="rag_search", parameters={"query": query, "top_k": top_k, "domain": domain})
            resp = await rag_tool.execute(tr)
            docs = []
            if resp.success and isinstance(resp.result, dict):
                docs = list(resp.result.get("documents", []))
            return docs, resp
        except Exception:
            return [], None

    def _render_markdown_summary(self, *, user_query: str, decomp: Dict[str, Any], research_docs: List[str], history_docs: List[str], llm_answer: str) -> str:
        lines: List[str] = []
        lines.append(f"# 오케스트레이션 결과 요약\n")
        lines.append(f"**요청**: {user_query}\n")
        # Decomposition
        lines.append("\n## 작업 분해 결과")
        lines.append(f"- 의도: {decomp.get('analysis',{}).get('intent','N/A')}")
        lines.append(f"- 총 예상 시간: {decomp.get('analysis',{}).get('estimated_total_time','N/A')}")
        tasks = decomp.get("tasks", [])
        if tasks:
            for t in tasks:
                lines.append(f"  - {t.get('id')}: {t.get('name')} ({t.get('priority','-')}, {t.get('estimated_time','-')})")
        # Research
        lines.append("\n## 연구/기술 문헌 근거")
        if research_docs:
            for d in research_docs:
                lines.append(f"- {d}")
        else:
            lines.append("- (검색 결과 없음)")
        # History
        lines.append("\n## 과거 수행 내역 참조")
        if history_docs:
            for d in history_docs:
                lines.append(f"- {d}")
        else:
            lines.append("- (검색 결과 없음)")
        # Final Answer
        lines.append("\n## 최종 제안/대응 방안")
        lines.append(llm_answer or "(응답 없음)")
        return "\n".join(lines)

    def _assess_compliance(self, final_md: str, compliance_docs: List[str]) -> Dict[str, Any]:
        """Use LLM to judge compliance based on compliance docs. Returns dict with pass, reasons, required_actions."""
        system = (
            "너는 안전/법규/사내 규정 준수 감사자이다. 제공된 규정 스니펫과 최종 계획을 검토하여\n"
            "규정 준수 여부를 JSON으로만 답하라. 형식: {\"pass\": true|false, \"reasons\":[], \"required_actions\":[]}"
        )
        user = (
            "[규정 스니펫]\n" + "\n".join(f"- {c}" for c in compliance_docs[:10]) +
            "\n\n[최종 계획]\n" + final_md
        )
        try:
            text = self.llm.generate(
                LLMGenerationRequest(
                    messages=[{"role":"system","content":system},{"role":"user","content":user}],
                    extra_body={"tool_choice":"none"},
                    temperature=0.0,
                    max_tokens=400,
                )
            )
            data = json.loads(text)
            return {
                "pass": bool(data.get("pass")),
                "reasons": data.get("reasons", []),
                "required_actions": data.get("required_actions", []),
            }
        except Exception:
            return {"pass": None, "reasons": [], "required_actions": []} 