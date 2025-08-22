"""
PRISM-Orch Mem0 통합 예제

Mem0를 활용한 장기 기억과 개인화된 상호작용을 보여주는 예제입니다.
"""

import asyncio
from src.orchestration import PrismOrchestrator
from src.orchestration.tools import MemorySearchTool


async def example_mem0_basic_usage():
    """Mem0 기본 사용 예제"""
    print("=== Mem0 기본 사용 예제 ===")
    
    # 오케스트레이터 초기화
    orchestrator = PrismOrchestrator()
    
    # Mem0 사용 가능 여부 확인
    mem0_available = orchestrator.is_mem0_available()
    print(f"Mem0 사용 가능: {mem0_available}")
    
    if not mem0_available:
        print("⚠️  Mem0가 설치되지 않았습니다. pip install mem0ai를 실행하세요.")
        return
    
    # 사용자별 개인화된 오케스트레이션
    user_id = "engineer_kim"
    
    # 첫 번째 대화
    print(f"\n--- {user_id}의 첫 번째 대화 ---")
    response1 = await orchestrator.orchestrate(
        "A-1 라인에서 압력 이상이 발생했습니다. 어떻게 대응해야 할까요?",
        user_id=user_id
    )
    print(f"응답: {response1.text[:200]}...")
    
    # 두 번째 대화 (이전 대화를 기억)
    print(f"\n--- {user_id}의 두 번째 대화 ---")
    response2 = await orchestrator.orchestrate(
        "이전에 말씀하신 대로 압력 센서를 점검했는데, 정상 범위 내에 있습니다. 다음 단계는 무엇인가요?",
        user_id=user_id
    )
    print(f"응답: {response2.text[:200]}...")
    
    # 세 번째 대화 (개인화된 경험)
    print(f"\n--- {user_id}의 세 번째 대화 ---")
    response3 = await orchestrator.orchestrate(
        "이전에 제가 선호하는 작업 방식이 있었나요?",
        user_id=user_id
    )
    print(f"응답: {response3.text[:200]}...")


async def example_memory_search():
    """메모리 검색 예제"""
    print("\n=== 메모리 검색 예제 ===")
    
    orchestrator = PrismOrchestrator()
    
    if not orchestrator.is_mem0_available():
        print("⚠️  Mem0를 사용할 수 없습니다.")
        return
    
    user_id = "engineer_kim"
    
    # 특정 주제에 대한 메모리 검색
    search_results = await orchestrator.search_user_memories(
        query="압력 이상 대응",
        user_id=user_id,
        top_k=3
    )
    
    print(f"메모리 검색 결과:")
    if "memories" in search_results:
        for i, memory in enumerate(search_results["memories"], 1):
            print(f"  {i}. {memory['content'][:100]}...")
            print(f"     점수: {memory['score']:.3f}")
    else:
        print(f"  오류: {search_results.get('error', '알 수 없는 오류')}")


async def example_memory_summary():
    """메모리 요약 예제"""
    print("\n=== 메모리 요약 예제 ===")
    
    orchestrator = PrismOrchestrator()
    
    if not orchestrator.is_mem0_available():
        print("⚠️  Mem0를 사용할 수 없습니다.")
        return
    
    user_id = "engineer_kim"
    
    # 사용자 메모리 요약 조회
    summary = await orchestrator.get_user_memory_summary(user_id)
    
    print(f"사용자 '{user_id}' 메모리 요약:")
    if "total_memories" in summary:
        print(f"  총 메모리 수: {summary['total_memories']}")
        print(f"  마지막 업데이트: {summary['last_updated']}")
        
        if "memory_summary" in summary:
            print("  메모리 요약:")
            for i, memory in enumerate(summary["memory_summary"][:3], 1):
                print(f"    {i}. {memory.get('memory', '')[:80]}...")
    else:
        print(f"  오류: {summary.get('error', '알 수 없는 오류')}")


async def example_multi_user_memory():
    """다중 사용자 메모리 예제"""
    print("\n=== 다중 사용자 메모리 예제 ===")
    
    orchestrator = PrismOrchestrator()
    
    if not orchestrator.is_mem0_available():
        print("⚠️  Mem0를 사용할 수 없습니다.")
        return
    
    # 여러 사용자의 개인화된 대화
    users = [
        ("engineer_kim", "압력 이상 대응"),
        ("technician_lee", "온도 센서 교체"),
        ("supervisor_park", "안전 점검 절차")
    ]
    
    for user_id, topic in users:
        print(f"\n--- {user_id}의 {topic} 관련 대화 ---")
        
        response = await orchestrator.orchestrate(
            f"{topic}에 대해 알려주세요.",
            user_id=user_id
        )
        print(f"응답: {response.text[:150]}...")
        
        # 각 사용자의 메모리 요약
        summary = await orchestrator.get_user_memory_summary(user_id)
        if "total_memories" in summary:
            print(f"  {user_id}의 메모리 수: {summary['total_memories']}")


async def example_memory_tool_direct():
    """Memory Tool 직접 사용 예제"""
    print("\n=== Memory Tool 직접 사용 예제 ===")
    
    # Memory Tool 직접 사용
    memory_tool = MemorySearchTool()
    
    if not memory_tool.is_mem0_available():
        print("⚠️  Mem0를 사용할 수 없습니다.")
        return
    
    from core.tools import ToolRequest
    
    # 메모리 검색
    request = ToolRequest(
        tool_name="memory_search",
        parameters={
            "query": "압력 이상 대응 방법",
            "user_id": "engineer_kim",
            "top_k": 2,
            "memory_type": "user",
            "include_context": True
        }
    )
    
    response = await memory_tool.execute(request)
    
    if response.success:
        result = response.result
        print(f"메모리 검색 성공:")
        print(f"  메모리 수: {result['count']}")
        print(f"  Mem0 활성화: {result['mem0_enabled']}")
        print(f"  컨텍스트: {result.get('context', {})}")
        
        for i, memory in enumerate(result["memories"], 1):
            print(f"  {i}. {memory['content'][:80]}...")
    else:
        print(f"메모리 검색 실패: {response.error_message}")


async def example_memory_learning():
    """메모리 학습 예제"""
    print("\n=== 메모리 학습 예제 ===")
    
    orchestrator = PrismOrchestrator()
    
    if not orchestrator.is_mem0_available():
        print("⚠️  Mem0를 사용할 수 없습니다.")
        return
    
    user_id = "engineer_kim"
    
    # 학습 시나리오: 사용자 선호도 학습
    learning_conversations = [
        ("저는 항상 안전을 최우선으로 생각합니다.", "안전 우선 접근 방식을 기억하겠습니다."),
        ("단계별로 설명해주시면 좋겠습니다.", "단계별 상세 설명을 선호하시는군요."),
        ("실제 사례를 들어서 설명해주세요.", "구체적인 사례 중심 설명을 선호하시는군요.")
    ]
    
    print(f"--- {user_id}의 선호도 학습 ---")
    for user_input, expected_response in learning_conversations:
        response = await orchestrator.orchestrate(user_input, user_id=user_id)
        print(f"사용자: {user_input}")
        print(f"AI: {response.text[:100]}...")
        print()
    
    # 학습된 선호도 확인
    print("--- 학습된 선호도 확인 ---")
    preference_check = await orchestrator.orchestrate(
        "제가 어떤 방식의 설명을 선호하는지 기억하시나요?",
        user_id=user_id
    )
    print(f"AI: {preference_check.text}")


async def main():
    """메인 실행 함수"""
    print("🚀 PRISM-Orch Mem0 통합 예제")
    print("=" * 50)
    
    try:
        # 1. Mem0 기본 사용
        await example_mem0_basic_usage()
        
        # 2. 메모리 검색
        await example_memory_search()
        
        # 3. 메모리 요약
        await example_memory_summary()
        
        # 4. 다중 사용자 메모리
        await example_multi_user_memory()
        
        # 5. Memory Tool 직접 사용
        await example_memory_tool_direct()
        
        # 6. 메모리 학습
        await example_memory_learning()
        
        print("\n✅ 모든 Mem0 통합 예제 실행 완료!")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {str(e)}")
        print("Mem0 설치 여부를 확인하세요: pip install mem0ai")


if __name__ == "__main__":
    asyncio.run(main()) 