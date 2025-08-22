# PRISM-Orch

자율 제조 구현을 위한 AI 에이전트 오케스트레이션 모듈

## 개요

PRISM-Orch는 PRISM-Core의 LLM 서비스와 Vector DB를 활용하여 사용자의 자연어 질의를 분석하고, 적절한 도구들을 조합하여 지능적인 응답을 제공하는 오케스트레이션 시스템입니다.

## 주요 기능

- **작업 분해**: 사용자 요청을 분석하여 실행 가능한 하위 작업으로 분해
- **지식 검색**: 연구/기술 문헌, 과거 수행 내역, 안전 규정 등 다양한 도메인에서 관련 정보 검색
- **규정 준수 검증**: 제안된 조치가 안전 규정 및 사내 규정을 준수하는지 검증
- **자동 임베딩 검증**: Vector DB의 문서 임베딩 상태를 자동으로 검증하고 재생성

## 시스템 요구사항

- Python 3.10+
- PRISM-Core 서비스 (Vector DB, LLM 서비스)
- vLLM 서비스
- Weaviate Vector Database

## 설치 및 실행

### 1. 의존성 설치

```bash
# uv를 사용한 설치
uv sync

# 또는 pip를 사용한 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 설정을 추가하세요:

```env
# PRISM-Core API 주소
PRISM_CORE_BASE_URL=http://localhost:8000

# vLLM 서비스 주소
OPENAI_BASE_URL=http://localhost:8001/v1
OPENAI_API_KEY=EMPTY
VLLM_MODEL=Qwen/Qwen3-0.6B

# Vector DB 설정
VECTOR_ENCODER_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIM=384

# 서버 설정
APP_HOST=0.0.0.0
APP_PORT=8100
RELOAD=true
```

### 3. 서비스 실행

```bash
# PRISM-Core 서비스 시작 (별도 터미널에서)
cd ../prism-core
docker-compose up -d

# PRISM-Orch 서버 시작
uv run python -m src.main
```

## API 사용법

### 오케스트레이션 API

```bash
curl -X POST "http://localhost:8100/api/v1/orchestrate/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "A-1 라인 압력에 이상이 생긴 것 같은데, 원인이 뭐야?",
    "user_id": "user123"
  }'
```

### 응답 형식

```json
{
  "session_id": "session_xxx",
  "final_answer": "# 오케스트레이션 결과 요약\n\n**요청**: ...",
  "final_markdown": "...",
  "supporting_documents": ["0.861 | 제조 공정 최적화 기술 문서 1: ..."],
  "tools_used": ["rag_search", "memory_search"],
  "tool_results": [...],
  "compliance_checked": true,
  "compliance_evidence": [...],
  "compliance_verdict": null
}
```

## 테스트

### 종합 테스트 실행

모든 기능을 한 번에 테스트하려면 종합 테스트 스크립트를 실행하세요:

```bash
uv run python test_comprehensive.py
```

이 테스트는 다음 항목들을 검증합니다:

1. **서비스 연결 상태**: Weaviate, PRISM-Core, PRISM-Orch, vLLM 연결 확인
2. **Vector DB 스키마**: 클래스 및 문서 수 확인
3. **검색 기능**: 각 도메인별 벡터 검색 성능 테스트
4. **오케스트레이션 API**: 다양한 쿼리에 대한 응답 테스트
5. **임베딩 검증**: 문서 임베딩 상태 확인
6. **전체 워크플로우**: 복합 쿼리에 대한 전체 처리 과정 테스트

### 테스트 결과

테스트 실행 후 다음과 같은 정보를 확인할 수 있습니다:

- 각 서비스의 연결 상태
- Vector DB의 클래스별 문서 수
- 검색 성능 (결과 수, 유사도 점수)
- 오케스트레이션 성능 (답변 길이, 지원 문서 수)
- 임베딩 완료율
- 전체 성공률

테스트 결과는 `test_report_YYYYMMDD_HHMMSS.json` 파일로 저장됩니다.

## 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PRISM-Orch    │    │   PRISM-Core    │    │     Weaviate    │
│                 │    │                 │    │   Vector DB     │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │                 │
│ │Orchestrator │◄┼────┼►│ LLM Service │ │    │ ┌─────────────┐ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │OrchResearch │ │
│                 │    │                 │    │ │OrchHistory  │ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ │OrchCompliance│ │
│ │RAG Search   │◄┼────┼►│Vector DB API│◄┼────┼►└─────────────┘ │
│ └─────────────┘ │    │ └─────────────┘ │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│     vLLM        │    │   PostgreSQL    │
│   (LLM API)     │    │   (Metadata)    │
└─────────────────┘    └─────────────────┘
```

## 주요 컴포넌트

### PrismOrchestrator
- 사용자 요청을 분석하고 작업을 분해
- 적절한 도구들을 조합하여 응답 생성
- 규정 준수 검증 수행

### RAGSearchTool
- Vector DB에서 관련 문서 검색
- 자동 임베딩 검증 및 재생성
- 도메인별 검색 (Research, History, Compliance)

### MemorySearchTool
- 사용자의 과거 상호작용 기록 검색
- 개인화된 응답 제공

## 개발 가이드

### 새로운 도구 추가

1. `BaseTool`을 상속받는 새로운 도구 클래스 생성
2. `register_default_tools()` 메서드에 도구 등록
3. 에이전트의 `tools` 리스트에 도구명 추가

### 임베딩 검증 로직

`_validate_and_regenerate_embeddings()` 메서드는 다음을 수행합니다:

1. 각 클래스의 문서들을 조회
2. `vectorWeights`가 `null`인 문서들을 감지
3. 문제가 있는 문서들을 삭제
4. 올바른 임베딩과 함께 문서들을 재생성

## 문제 해결

### "0개 문서 반환" 문제

이 문제는 주로 Vector DB의 문서들이 벡터 임베딩 없이 저장되어 있을 때 발생합니다. 

**해결 방법:**
1. PRISM-Orch 서버를 재시작하여 자동 임베딩 검증 실행
2. 또는 수동으로 `test_comprehensive.py` 실행하여 임베딩 상태 확인

### 서비스 연결 실패

각 서비스가 정상적으로 실행 중인지 확인하세요:

```bash
# Weaviate 상태 확인
curl http://localhost:8080/v1/meta

# PRISM-Core 상태 확인
curl http://localhost:8000/

# PRISM-Orch 상태 확인
curl http://localhost:8100/

# vLLM 상태 확인
curl http://localhost:8001/v1/models
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.