"""
PRISM-Orch 모듈화된 구조 사용 예제

이 예제는 분리된 모듈들을 사용하여 오케스트레이션을 수행하는 방법을 보여줍니다.
"""

import asyncio
from src.orchestration import PrismOrchestrator, AgentManager, WorkflowManager
from src.orchestration.tools import RAGSearchTool, ComplianceTool, MemorySearchTool


async def example_basic_orchestration():
    """기본 오케스트레이션 예제"""
    print("=== 기본 오케스트레이션 예제 ===")
    
    # 오케스트레이터 초기화
    orchestrator = PrismOrchestrator()
    
    # 오케스트레이션 수행
    response = await orchestrator.orchestrate(
        "A-1 라인에서 압력 이상이 발생했습니다. 어떻게 대응해야 할까요?"
    )
    
    print(f"응답: {response.text}")
    print(f"사용된 Tools: {response.tools_used}")
    print(f"성공 여부: {response.success}")


def example_agent_management():
    """에이전트 관리 예제"""
    print("\n=== 에이전트 관리 예제 ===")
    
    # AgentManager 직접 사용
    agent_manager = AgentManager()
    
    # 에이전트 등록
    from core.llm.schemas import Agent
    
    analysis_agent = Agent(
        name="data_analyst",
        description="데이터 분석 전문가",
        role_prompt="당신은 제조 공정 데이터를 분석하는 전문가입니다.",
        tools=["rag_search", "compliance_check"]
    )
    
    success = agent_manager.register_agent(analysis_agent)
    print(f"에이전트 등록: {'성공' if success else '실패'}")
    
    # 에이전트 상태 조회
    status = agent_manager.get_agent_status("data_analyst")
    print(f"에이전트 상태: {status}")
    
    # 에이전트 목록 조회
    agents = agent_manager.list_agents()
    print(f"등록된 에이전트 수: {len(agents)}")


def example_workflow_management():
    """워크플로우 관리 예제"""
    print("\n=== 워크플로우 관리 예제 ===")
    
    # WorkflowManager 직접 사용
    workflow_manager = WorkflowManager()
    
    # 워크플로우 정의
    workflow_steps = [
        {
            "name": "데이터_검색",
            "type": "tool_call",
            "tool_name": "rag_search",
            "parameters": {
                "query": "{{search_query}}",
                "domain": "research",
                "top_k": 3
            }
        },
        {
            "name": "규정_검증",
            "type": "tool_call", 
            "tool_name": "compliance_check",
            "parameters": {
                "action": "{{proposed_action}}",
                "context": "{{context}}"
            }
        },
        {
            "name": "조건_확인",
            "type": "condition",
            "condition": "context.get('compliance_status') == 'compliant'"
        }
    ]
    
    success = workflow_manager.define_workflow("압력_이상_대응", workflow_steps)
    print(f"워크플로우 정의: {'성공' if success else '실패'}")
    
    # 워크플로우 상태 조회
    status = workflow_manager.get_workflow_status("압력_이상_대응")
    print(f"워크플로우 상태: {status}")


async def example_tool_usage():
    """Tool 직접 사용 예제"""
    print("\n=== Tool 직접 사용 예제 ===")
    
    # Tool 인스턴스 생성
    rag_tool = RAGSearchTool()
    compliance_tool = ComplianceTool()
    memory_tool = MemorySearchTool()
    
    # RAG 검색 실행
    from core.tools import ToolRequest
    
    rag_request = ToolRequest(
        tool_name="rag_search",
        parameters={
            "query": "압력 이상 대응 방법",
            "domain": "research",
            "top_k": 2
        }
    )
    
    rag_response = await rag_tool.execute(rag_request)
    print(f"RAG 검색 결과: {rag_response.success}")
    if rag_response.success:
        print(f"문서 수: {rag_response.result.get('count', 0)}")
    
    # 규정 준수 검증
    compliance_request = ToolRequest(
        tool_name="compliance_check",
        parameters={
            "action": "압력 센서 교체 작업",
            "context": "A-1 라인 압력 이상 상황"
        }
    )
    
    compliance_response = await compliance_tool.execute(compliance_request)
    print(f"규정 준수 검증: {compliance_response.success}")
    if compliance_response.success:
        print(f"준수 상태: {compliance_response.result.get('compliance_status')}")


async def example_custom_workflow():
    """커스텀 워크플로우 실행 예제"""
    print("\n=== 커스텀 워크플로우 실행 예제 ===")
    
    orchestrator = PrismOrchestrator()
    
    # 워크플로우 정의
    workflow_steps = [
        {
            "name": "상황_분석",
            "type": "tool_call",
            "tool_name": "rag_search",
            "parameters": {
                "query": "{{user_query}}",
                "domain": "research",
                "top_k": 3
            }
        },
        {
            "name": "사용자_이력_확인",
            "type": "tool_call",
            "tool_name": "memory_search",
            "parameters": {
                "query": "{{user_query}}",
                "user_id": "{{user_id}}",
                "top_k": 2
            }
        },
        {
            "name": "안전성_검증",
            "type": "tool_call",
            "tool_name": "compliance_check",
            "parameters": {
                "action": "제안된 조치",
                "context": "{{user_query}}"
            }
        }
    ]
    
    # 워크플로우 등록
    orchestrator.define_workflow("종합_분석", workflow_steps)
    
    # 워크플로우 실행
    context = {
        "user_query": "A-1 라인 압력 이상 대응",
        "user_id": "engineer_001"
    }
    
    result = await orchestrator.execute_workflow("종합_분석", context)
    print(f"워크플로우 실행 결과: {result['status']}")
    print(f"실행된 단계 수: {len(result['steps'])}")


async def main():
    """메인 실행 함수"""
    print("🚀 PRISM-Orch 모듈화된 구조 사용 예제")
    print("=" * 50)
    
    # 1. 기본 오케스트레이션
    await example_basic_orchestration()
    
    # 2. 에이전트 관리
    example_agent_management()
    
    # 3. 워크플로우 관리
    example_workflow_management()
    
    # 4. Tool 직접 사용
    await example_tool_usage()
    
    # 5. 커스텀 워크플로우
    await example_custom_workflow()
    
    print("\n✅ 모든 예제 실행 완료!")


if __name__ == "__main__":
    asyncio.run(main()) 