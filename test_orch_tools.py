#!/usr/bin/env python3
"""
PRISM-Orch Tool Setup Test

PRISM-Core의 도구들을 사용한 Orch 도구 설정을 테스트합니다.
"""

import sys
import os
from pathlib import Path

# PRISM-Orch 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_orch_tool_setup():
    """Orch 도구 설정을 테스트합니다."""
    print("🧪 PRISM-Orch Tool Setup 테스트")
    print("="*50)
    
    try:
        # Orch 도구 설정 테스트
        from src.orchestration.tools.orch_tool_setup import OrchToolSetup
        
        print("1️⃣ OrchToolSetup 인스턴스 생성...")
        orch_setup = OrchToolSetup()
        print("✅ OrchToolSetup 생성 성공")
        
        print("\n2️⃣ 도구 설정...")
        tool_registry = orch_setup.setup_tools()
        print("✅ 도구 설정 성공")
        
        print("\n3️⃣ 도구 정보 출력...")
        orch_setup.print_tool_info()
        
        print("\n4️⃣ 개별 도구 접근 테스트...")
        rag_tool = orch_setup.get_rag_tool()
        compliance_tool = orch_setup.get_compliance_tool()
        memory_tool = orch_setup.get_memory_tool()
        
        print(f"✅ RAG Tool: {rag_tool.__class__.__name__}")
        print(f"✅ Compliance Tool: {compliance_tool.__class__.__name__}")
        print(f"✅ Memory Tool: {memory_tool.__class__.__name__}")
        
        print("\n5️⃣ 도구 레지스트리 확인...")
        tools = list(tool_registry._tools.keys())
        print(f"등록된 도구들: {tools}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        print("💡 PRISM-Core가 설치되어 있는지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def test_orchestrator_integration():
    """Orchestrator와의 통합을 테스트합니다."""
    print("\n🧪 Orchestrator 통합 테스트")
    print("="*50)
    
    try:
        from src.orchestration.prism_orchestrator import PrismOrchestrator
        
        print("1️⃣ PrismOrchestrator 인스턴스 생성...")
        orchestrator = PrismOrchestrator()
        print("✅ PrismOrchestrator 생성 성공")
        
        print("\n2️⃣ 도구 레지스트리 확인...")
        tools = list(orchestrator.tool_registry._tools.keys())
        print(f"Orchestrator의 도구들: {tools}")
        
        print("\n3️⃣ LLM 서비스 확인...")
        print(f"LLM 모델: {orchestrator.llm.model_name}")
        print(f"도구 레지스트리 연결: {orchestrator.llm.tool_registry is orchestrator.tool_registry}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator 통합 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 PRISM-Orch Tool Setup 테스트 시작")
    print("="*60)
    
    # 환경 확인
    print("📋 환경 확인:")
    print(f"Python 경로: {sys.executable}")
    print(f"프로젝트 루트: {project_root}")
    print(f"PRISM-Core 경로: {project_root.parent / 'prism-core'}")
    
    # 테스트 실행
    success1 = test_orch_tool_setup()
    success2 = test_orchestrator_integration()
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    print(f"Orch Tool Setup: {'✅ 성공' if success1 else '❌ 실패'}")
    print(f"Orchestrator 통합: {'✅ 성공' if success2 else '❌ 실패'}")
    
    if success1 and success2:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("PRISM-Orch가 PRISM-Core의 도구들을 성공적으로 사용할 수 있습니다.")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        print("설정을 확인하고 다시 시도해주세요.")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 