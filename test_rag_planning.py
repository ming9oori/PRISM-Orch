#!/usr/bin/env python3
"""
RAG 기반 Task Planning 테스트 스크립트

이 스크립트는 PRISM-Orch의 RAG 시스템과 Task Planner를 테스트합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
# prism-core 경로를 먼저 추가
prism_core_path = project_root.parent / "prism-core"
if prism_core_path.exists():
    sys.path.insert(0, str(prism_core_path))
sys.path.insert(0, str(project_root / "src"))

from src.modules.rag_system import RAGSystem
from src.modules.task_planner import TaskPlanner
from src.api.schemas import UserQueryInput


def test_rag_system():
    """RAG 시스템 테스트"""
    print("=== RAG System Test ===")
    
    rag = RAGSystem()
    
    # 지식 검색 테스트
    query = "A-1 라인 압력 이상 분석"
    knowledge = rag.retrieve_knowledge(query, top_k=3)
    print(f"Knowledge retrieval for '{query}':")
    for i, doc in enumerate(knowledge, 1):
        print(f"  {i}. {doc}")
    
    # 메모리 검색 테스트
    user_id = "test_user_001"
    memory = rag.retrieve_from_memory(user_id, top_k=2)
    print(f"\nMemory retrieval for user '{user_id}':")
    for i, mem in enumerate(memory, 1):
        print(f"  {i}. {mem}")


def test_task_planner():
    """Task Planner 테스트"""
    print("\n=== Task Planner Test ===")
    
    planner = TaskPlanner()
    
    # 작업 분해 및 계획 수립 테스트
    test_queries = [
        "A-1 라인 압력에 이상이 생긴 것 같은데, 원인이 뭐야?",
        "온도 센서 데이터를 분석해서 이상 패턴을 찾아줘",
        "현재 시스템 상태를 점검하고 최적화 방안을 제시해줘"
    ]
    
    for query in test_queries:
        print(f"\n--- Planning for: '{query}' ---")
        try:
            tasks = planner.decompose_and_plan(query, user_id="test_user_001")
            print(f"Generated {len(tasks)} tasks:")
            
            for i, task in enumerate(tasks, 1):
                print(f"  {i}. {task.name}")
                print(f"     - Intent: {task.intent}")
                print(f"     - Agent: {task.assigned_agent_id}")
                print(f"     - Priority: {task.priority}")
                print(f"     - Dependencies: {task.dependencies}")
                print(f"     - Status: {task.status}")
                if task.description:
                    print(f"     - Description: {task.description}")
                print()
                
        except Exception as e:
            print(f"Error in task planning: {e}")


def test_integration():
    """통합 테스트"""
    print("\n=== Integration Test ===")
    
    # 사용자 입력 시뮬레이션
    user_input = UserQueryInput(
        query="A-1 라인 압력이 정상 범위를 벗어나고 있어. 원인 분석과 해결 방안을 제시해줘.",
        session_id="test_session_001",
        user_preferences={"mode": "detailed"}
    )
    
    print(f"User Query: {user_input.query}")
    print(f"Session ID: {user_input.session_id}")
    print(f"Preferences: {user_input.user_preferences}")
    
    # RAG 시스템을 통한 지식 검색
    rag = RAGSystem()
    knowledge = rag.retrieve_knowledge(user_input.query, top_k=3)
    memory = rag.retrieve_from_memory(user_input.session_id, top_k=2)
    
    print(f"\nRetrieved Knowledge: {len(knowledge)} documents")
    print(f"Retrieved Memory: {len(memory)} items")
    
    # Task Planner를 통한 작업 계획 수립
    planner = TaskPlanner()
    tasks = planner.decompose_and_plan(user_input.query, user_input.session_id)
    
    print(f"\nGenerated Tasks: {len(tasks)}")
    for task in tasks:
        print(f"  - {task.name} ({task.intent}) -> {task.assigned_agent_id}")


if __name__ == "__main__":
    print("PRISM-Orch RAG Planning Test")
    print("=" * 50)
    
    try:
        test_rag_system()
        test_task_planner()
        test_integration()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 