#!/usr/bin/env python3
"""
Weaviate Schema Initialization for PRISM Orchestration
자율제조 AI 에이전트 벡터 데이터베이스 스키마 초기화
"""

import weaviate
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_weaviate_schema():
    """Weaviate 스키마를 초기화합니다."""
    
    # Weaviate 클라이언트 연결
    client = weaviate.Client("http://localhost:18080")
    
    # 기존 스키마 삭제 (개발 환경에서만)
    try:
        client.schema.delete_all()
        logger.info("기존 스키마 삭제 완료")
    except Exception as e:
        logger.warning(f"스키마 삭제 중 오류: {e}")
    
    # 외부 지식 문서 클래스
    external_knowledge_class = {
        "class": "ExternalKnowledge",
        "description": "외부 지식 문서 및 자료",
        "vectorizer": "text2vec-openai",
        "properties": [
            {
                "name": "title",
                "dataType": ["text"],
                "description": "문서 제목"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "문서 내용"
            },
            {
                "name": "document_type",
                "dataType": ["text"],
                "description": "문서 유형 (RESEARCH_PAPER, MANUAL, GUIDELINE, FAQ)"
            },
            {
                "name": "metadata",
                "dataType": ["text"],
                "description": "문서 메타데이터 (JSON 문자열)"
            },
            {
                "name": "created_at",
                "dataType": ["date"],
                "description": "생성 시간"
            },
            {
                "name": "access_count",
                "dataType": ["int"],
                "description": "접근 횟수"
            }
        ]
    }
    
    # 에이전트 메모리 클래스
    agent_memory_class = {
        "class": "AgentMemory", 
        "description": "AI 에이전트의 메모리 저장소",
        "vectorizer": "text2vec-openai",
        "properties": [
            {
                "name": "agent_id",
                "dataType": ["text"],
                "description": "에이전트 식별자"
            },
            {
                "name": "memory_type",
                "dataType": ["text"], 
                "description": "메모리 유형 (SHORT_TERM, LONG_TERM, EPISODIC)"
            },
            {
                "name": "content",
                "dataType": ["text"],
                "description": "메모리 내용"
            },
            {
                "name": "context",
                "dataType": ["text"],
                "description": "컨텍스트 정보 (JSON 문자열)"
            },
            {
                "name": "importance_score",
                "dataType": ["number"],
                "description": "중요도 점수"
            },
            {
                "name": "created_at",
                "dataType": ["date"],
                "description": "생성 시간"
            },
            {
                "name": "last_accessed",
                "dataType": ["date"],
                "description": "최근 접근 시간"
            }
        ]
    }
    
    # 인스트럭션 저장소 클래스
    instruction_class = {
        "class": "Instruction",
        "description": "에이전트 실행 인스트럭션",
        "vectorizer": "text2vec-openai", 
        "properties": [
            {
                "name": "original_text",
                "dataType": ["text"],
                "description": "원본 인스트럭션 텍스트"
            },
            {
                "name": "rewritten_text", 
                "dataType": ["text"],
                "description": "재작성된 인스트럭션 텍스트"
            },
            {
                "name": "agent_type",
                "dataType": ["text"],
                "description": "대상 에이전트 유형"
            },
            {
                "name": "success_rate",
                "dataType": ["number"],
                "description": "성공률"
            },
            {
                "name": "created_at",
                "dataType": ["date"],
                "description": "생성 시간"
            }
        ]
    }
    
    # 제조 공정 지식 클래스
    manufacturing_knowledge_class = {
        "class": "ManufacturingKnowledge",
        "description": "제조 공정 관련 지식",
        "vectorizer": "text2vec-openai",
        "properties": [
            {
                "name": "process_name",
                "dataType": ["text"],
                "description": "공정명"
            },
            {
                "name": "description",
                "dataType": ["text"],
                "description": "공정 설명"
            },
            {
                "name": "parameters",
                "dataType": ["text"],
                "description": "공정 파라미터 (JSON 문자열)"
            },
            {
                "name": "constraints",
                "dataType": ["text"],
                "description": "제약 조건 (JSON 문자열)"
            },
            {
                "name": "best_practices",
                "dataType": ["text"],
                "description": "모범 사례"
            },
            {
                "name": "troubleshooting",
                "dataType": ["text"],
                "description": "문제 해결 방법"
            }
        ]
    }
    
    # 스키마 클래스들 생성
    classes = [
        external_knowledge_class,
        agent_memory_class, 
        instruction_class,
        manufacturing_knowledge_class
    ]
    
    for class_obj in classes:
        try:
            client.schema.create_class(class_obj)
            logger.info(f"클래스 '{class_obj['class']}' 생성 완료")
        except Exception as e:
            logger.error(f"클래스 '{class_obj['class']}' 생성 실패: {e}")
    
    # 샘플 데이터 추가
    try:
        # 샘플 제조 지식 추가
        sample_knowledge = {
            "process_name": "CNC 밀링",
            "description": "컴퓨터 수치 제어를 이용한 정밀 가공 공정",
            "parameters": json.dumps({
                "spindle_speed": "1000-8000 RPM",
                "feed_rate": "100-500 mm/min",
                "cutting_depth": "0.1-2.0 mm"
            }),
            "constraints": json.dumps({
                "temperature": "< 60°C",
                "vibration": "< 0.5 mm/s",
                "tool_wear": "< 0.1 mm"
            }),
            "best_practices": "적절한 절삭유 사용, 정기적인 공구 교체, 워크피스 고정 확인",
            "troubleshooting": "진동 발생 시 절삭 속도 조정, 표면 거칠기 불량 시 이송량 감소"
        }
        
        client.data_object.create(
            data_object=sample_knowledge,
            class_name="ManufacturingKnowledge"
        )
        logger.info("샘플 제조 지식 데이터 추가 완료")
        
    except Exception as e:
        logger.error(f"샘플 데이터 추가 실패: {e}")
    
    logger.info("Weaviate 스키마 초기화 완료")

if __name__ == "__main__":
    initialize_weaviate_schema()