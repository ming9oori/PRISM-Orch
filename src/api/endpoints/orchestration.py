import uuid
from fastapi import APIRouter, Body
from typing import Dict, Any, List

from ..schemas import UserQueryInput, OrchestrationResponse
from ...orchestration.prism_orchestrator import PrismOrchestrator

router = APIRouter()
orchestrator = PrismOrchestrator()

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
    session_id = query.session_id or f"session_{uuid.uuid4()}"

    # Invoke high-level orchestrator (includes LLM-based decomposition, tool calls, RAG + compliance)
    agent_resp = await orchestrator.orchestrat(
        prompt=query.query,
        user_id=query.user_id,
        max_tokens=1000,
        temperature=0.3,
        extra_body={"tool_choice": "auto"},
    )

    # Supporting docs (extract from tool_results best-effort)
    supporting_docs: List[str] = []
    for tr in agent_resp.tool_results:
        result = tr.get("result") if isinstance(tr, dict) else None
        if isinstance(result, dict):
            docs = result.get("documents") or result.get("memories")
            if isinstance(docs, list):
                supporting_docs.extend([str(d) for d in docs])

    # Compliance evidence (best-effort from tool_results domain=compliance)
    compliance_evidence: List[str] = []
    for tr in agent_resp.tool_results:
        if isinstance(tr, dict):
            result = tr.get("result")
            if result:
                domain = result.get("domain") if isinstance(result, dict) else None
                if domain == "compliance":
                    docs = result.get("documents")
                    if isinstance(docs, list):
                        compliance_evidence.extend([str(d) for d in docs])

    return OrchestrationResponse(
        session_id=session_id,
        final_answer=agent_resp.text,
        final_markdown=agent_resp.text,
        flow_chart_data={"nodes": [], "edges": []},
        supporting_documents=supporting_docs,
        task_history=[],
        tools_used=list(agent_resp.tools_used or []),
        tool_results=list(agent_resp.tool_results or []),
        compliance_checked=bool((agent_resp.metadata or {}).get("compliance_checked", False)),
        compliance_evidence=compliance_evidence,
        compliance_verdict=None,
        decomposition=None,
    ) 