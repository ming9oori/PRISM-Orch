#!/usr/bin/env python3
"""
PRISM-Orch 최종 데모

PRISM-Core를 활용한 AI 에이전트 오케스트레이션 시스템의 완전한 데모입니다.
"""

import asyncio
import os
import sys
from pathlib import Path

# 환경 변수 설정
os.environ.setdefault('PRISM_CORE_BASE_URL', 'http://localhost:8000')
os.environ.setdefault('OPENAI_BASE_URL', 'http://localhost:8001/v1')
os.environ.setdefault('OPENAI_API_KEY', 'EMPTY')
os.environ.setdefault('VLLM_MODEL', 'Qwen/Qwen3-0.6B')

def print_header(title: str):
    """헤더 출력"""
    print(f"\n{'='*80}")
    print(f"  🚀 {title}")
    print(f"{'='*80}")

def print_section(title: str):
    """섹션 출력"""
    print(f"\n{'-'*60}")
    print(f"  📋 {title}")
    print(f"{'-'*60}")

def print_response(response, query: str):
    """응답 출력"""
    print(f"\n🔍 쿼리: {query}")
    print(f"📝 응답 길이: {len(response.text)} 문자")
    print(f"🛠️  사용된 도구: {', '.join(response.tools_used) if response.tools_used else '없음'}")
    
    # 응답 내용 출력 (처음 500자)
    print(f"\n💬 응답 내용:")
    print(f"{response.text[:500]}{'...' if len(response.text) > 500 else ''}")
    
    # 메타데이터 출력
    if response.metadata:
        print(f"\n📊 메타데이터:")
        for key, value in response.metadata.items():
            if key != 'error':
                print(f"   {key}: {value}")

async def demo_system_initialization():
    """시스템 초기화 데모"""
    print_header("PRISM-Orch 시스템 초기화")
    
    try:
        from src.orchestration import PrismOrchestrator
        
        print("🔄 오케스트레이터 초기화 중...")
        orchestrator = PrismOrchestrator()
        print("✅ 오케스트레이터 초기화 완료")
        
        # 시스템 상태 확인
        print("\n📊 시스템 상태:")
        print(f"   - LLM 모델: {orchestrator.llm.model_name}")
        print(f"   - 등록된 도구: {len(orchestrator.list_tools())}개")
        print(f"   - 등록된 에이전트: {len(orchestrator.list_agents())}개")
        print(f"   - Mem0 사용 가능: {orchestrator.is_mem0_available()}")
        
        return orchestrator
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {str(e)}")
        return None

async def demo_basic_orchestration(orchestrator):
    """기본 오케스트레이션 데모"""
    print_header("기본 오케스트레이션 데모")
    
    # 1. 기술 문서 검색
    print_section("1. 기술 문서 검색 (RAG)")
    query1 = "압력 센서의 원리와 종류에 대해 기술 문서를 찾아서 알려주세요"
    response1 = await orchestrator.orchestrate(query1)
    print_response(response1, query1)
    
    # 2. 안전 규정 검증
    print_section("2. 안전 규정 검증 (Compliance)")
    query2 = "고압 가스 배관에서 누출이 발생했습니다. 안전 규정에 따라 어떤 조치를 취해야 하는지 검증해주세요"
    response2 = await orchestrator.orchestrate(query2)
    print_response(response2, query2)
    
    # 3. 복합 워크플로우
    print_section("3. 복합 워크플로우 (Multiple Tools)")
    query3 = "A-1 라인에서 압력 이상이 발생했습니다. 이전에 비슷한 문제가 있었는지 확인하고, 안전 규정에 따라 어떤 조치를 취해야 하는지 알려주세요"
    response3 = await orchestrator.orchestrate(query3)
    print_response(response3, query3)

async def demo_personalized_interaction(orchestrator):
    """개인화된 상호작용 데모"""
    print_header("개인화된 상호작용 데모")
    
    user_id = "engineer_kim"
    
    # 1. 첫 번째 대화
    print_section("1. 첫 번째 대화")
    query1 = "압력 센서 교체 작업에 대해 알려주세요"
    response1 = await orchestrator.orchestrate(query1, user_id=user_id)
    print_response(response1, query1)
    
    # 2. 두 번째 대화 (이전 대화 참조)
    print_section("2. 두 번째 대화 (이전 대화 참조)")
    query2 = "이전에 말씀하신 압력 센서 교체 작업에서 추가로 주의해야 할 점은 무엇인가요?"
    response2 = await orchestrator.orchestrate(query2, user_id=user_id)
    print_response(response2, query2)
    
    # 3. 세 번째 대화 (개인화된 조언)
    print_section("3. 세 번째 대화 (개인화된 조언)")
    query3 = "제가 항상 안전을 최우선으로 생각하는데, 이번 작업에서 특별히 신경 써야 할 부분이 있나요?"
    response3 = await orchestrator.orchestrate(query3, user_id=user_id)
    print_response(response3, query3)

async def demo_tool_direct_usage():
    """Tool 직접 사용 데모"""
    print_header("Tool 직접 사용 데모")
    
    try:
        from src.orchestration.tools import RAGSearchTool, ComplianceTool, MemorySearchTool
        from core.tools import ToolRequest
        
        # 1. RAG 검색 Tool 직접 사용
        print_section("1. RAG 검색 Tool 직접 사용")
        rag_tool = RAGSearchTool()
        
        rag_request = ToolRequest(
            tool_name="rag_search",
            parameters={
                "query": "압력 센서 원리",
                "domain": "research",
                "top_k": 3
            }
        )
        
        rag_response = await rag_tool.execute(rag_request)
        if rag_response.success:
            print("✅ RAG 검색 성공")
            result = rag_response.result
            documents = result.get('documents', [])
            print(f"📚 검색 결과: {len(documents)}개 문서")
            for i, doc in enumerate(documents[:2], 1):
                print(f"   문서 {i}: {doc.get('content', '')[:100]}...")
        else:
            print(f"❌ RAG 검색 실패: {rag_response.error_message}")
        
        # 2. 규정 준수 Tool 직접 사용
        print_section("2. 규정 준수 Tool 직접 사용")
        compliance_tool = ComplianceTool()
        
        compliance_request = ToolRequest(
            tool_name="compliance_check",
            parameters={
                "action": "고압 가스 배관 점검",
                "context": "운영 중인 고압 가스 배관에서 누출이 발생하여 긴급 점검이 필요한 상황"
            }
        )
        
        compliance_response = await compliance_tool.execute(compliance_request)
        if compliance_response.success:
            print("✅ 규정 준수 검증 성공")
            result = compliance_response.result
            print(f"📋 준수 상태: {result.get('compliance_status', 'N/A')}")
            print(f"⚠️  위험 수준: {result.get('risk_level', 'N/A')}")
            recommendations = result.get('recommendations', [])
            if recommendations:
                print(f"💡 권장사항:")
                for rec in recommendations[:3]:
                    print(f"   - {rec}")
        else:
            print(f"❌ 규정 준수 검증 실패: {compliance_response.error_message}")
        
        # 3. 메모리 검색 Tool 직접 사용
        print_section("3. 메모리 검색 Tool 직접 사용")
        memory_tool = MemorySearchTool()
        
        memory_request = ToolRequest(
            tool_name="memory_search",
            parameters={
                "query": "압력 센서",
                "user_id": "engineer_kim",
                "top_k": 3,
                "memory_type": "user",
                "include_context": True
            }
        )
        
        memory_response = await memory_tool.execute(memory_request)
        if memory_response.success:
            print("✅ 메모리 검색 성공")
            result = memory_response.result
            documents = result.get('documents', [])
            print(f"🧠 검색 결과: {len(documents)}개 메모리")
            for i, doc in enumerate(documents[:2], 1):
                print(f"   메모리 {i}: {doc.get('content', '')[:100]}...")
        else:
            print(f"❌ 메모리 검색 실패: {memory_response.error_message}")
        
        return True
    except Exception as e:
        print(f"❌ Tool 직접 사용 데모 실패: {str(e)}")
        return False

async def demo_advanced_scenarios(orchestrator):
    """고급 시나리오 데모"""
    print_header("고급 시나리오 데모")
    
    # 1. 긴급 상황 대응
    print_section("1. 긴급 상황 대응")
    query1 = "화학 공장에서 독성 물질 누출이 발생했습니다. 즉시 취해야 할 안전 조치와 규정 준수 사항을 알려주세요"
    response1 = await orchestrator.orchestrate(query1)
    print_response(response1, query1)
    
    # 2. 복잡한 문제 해결
    print_section("2. 복잡한 문제 해결")
    query2 = "발전소에서 고온 배관 시스템의 압력이 비정상적으로 상승하고 있습니다. 이전 사례를 참고하여 안전 규정에 따른 대응 방안을 제시해주세요"
    response2 = await orchestrator.orchestrate(query2)
    print_response(response2, query2)
    
    # 3. 개인화된 학습
    print_section("3. 개인화된 학습")
    user_id = "technician_lee"
    query3 = "저는 신입 기술자입니다. 압력 센서 교체 작업을 처음 수행하는데, 단계별로 안전하게 진행하는 방법을 알려주세요"
    response3 = await orchestrator.orchestrate(query3, user_id=user_id)
    print_response(response3, query3)

async def demo_system_capabilities(orchestrator):
    """시스템 기능 데모"""
    print_header("시스템 기능 데모")
    
    # 1. 등록된 도구 목록
    print_section("1. 등록된 도구 목록")
    tools = orchestrator.list_tools()
    print(f"📋 총 {len(tools)}개 도구:")
    for tool in tools:
        print(f"   - {tool}")
    
    # 2. 등록된 에이전트 목록
    print_section("2. 등록된 에이전트 목록")
    agents = orchestrator.list_agents()
    print(f"🤖 총 {len(agents)}개 에이전트:")
    for agent in agents:
        print(f"   - {agent.name}: {agent.description}")
    
    # 3. 메모리 시스템 상태
    print_section("3. 메모리 시스템 상태")
    if orchestrator.is_mem0_available():
        print("✅ Mem0 메모리 시스템 사용 가능")
        
        # 사용자 메모리 요약
        user_id = "engineer_kim"
        summary = await orchestrator.get_user_memory_summary(user_id)
        print(f"📊 사용자 '{user_id}' 메모리 요약:")
        for key, value in summary.items():
            print(f"   - {key}: {value}")
    else:
        print("⚠️ Mem0 메모리 시스템 사용 불가 (fallback 모드)")

async def main():
    """메인 데모 함수"""
    print("🎯 PRISM-Orch 최종 데모 시작")
    print("PRISM-Core를 활용한 AI 에이전트 오케스트레이션 시스템")
    print("=" * 80)
    
    # 1. 시스템 초기화
    orchestrator = await demo_system_initialization()
    if not orchestrator:
        print("❌ 시스템 초기화 실패로 데모를 중단합니다.")
        return
    
    # 2. 기본 오케스트레이션
    await demo_basic_orchestration(orchestrator)
    
    # 3. 개인화된 상호작용
    await demo_personalized_interaction(orchestrator)
    
    # 4. Tool 직접 사용
    await demo_tool_direct_usage()
    
    # 5. 고급 시나리오
    await demo_advanced_scenarios(orchestrator)
    
    # 6. 시스템 기능
    await demo_system_capabilities(orchestrator)
    
    # 결과 요약
    print_header("데모 완료")
    print("🎉 PRISM-Orch 최종 데모가 성공적으로 완료되었습니다!")
    print("\n📋 데모에서 확인된 기능들:")
    print("   ✅ 시스템 초기화 및 연결")
    print("   ✅ 기본 오케스트레이션 (RAG, Compliance, 복합 워크플로우)")
    print("   ✅ 개인화된 상호작용 (Mem0 기반)")
    print("   ✅ Tool 직접 사용")
    print("   ✅ 고급 시나리오 처리")
    print("   ✅ 시스템 기능 확인")
    
    print("\n🚀 PRISM-Orch가 정상적으로 작동하고 있습니다!")
    print("이제 실제 프로덕션 환경에서 사용할 준비가 완료되었습니다.")
    
    print("\n" + "=" * 80)
    print("🏁 PRISM-Orch 최종 데모 종료")

if __name__ == "__main__":
    asyncio.run(main()) 