# PRISM-Orch

**PRISM-Core 기반 AI 에이전트 오케스트레이션 시스템**

PRISM-Orch는 PRISM-Core의 LLM 서비스와 Vector DB를 활용하여 복잡한 제조 업무를 수행하는 AI 에이전트들을 오케스트레이션하는 시스템입니다. 사용자의 자연어 질의를 받아 적절한 에이전트들을 선택하고, 작업을 분해하여 순차적으로 실행한 후 최종 결과를 종합하여 제공합니다.

## 🚀 주요 기능

- **자연어 기반 작업 분해**: 사용자 질의를 분석하여 세부 작업으로 분해
- **에이전트 오케스트레이션**: 여러 AI 에이전트의 협업을 통한 복합 작업 수행
- **RAG 기반 지식 검색**: 연구 문서, 사용자 이력, 규정 준수 정보 검색
- **규정 준수 검증**: 안전 규정 및 법규 준수 여부 자동 검증
- **실시간 모니터링**: 작업 진행 상황 및 결과 추적

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   사용자 질의    │    │   PRISM-Orch    │    │   PRISM-Core    │
│                 │    │                 │    │                 │
│ 자연어 입력     │───►│ 오케스트레이터   │───►│ LLM 서비스      │
│                 │    │                 │    │   Vector DB     │
│                 │    │                 │    │   Tool 시스템   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   에이전트 풀   │
                       │                 │
                       │ • 분석 에이전트  │
                       │ • 모니터링 에이전트│
                       │ • 제어 에이전트  │
                       │ • 보고서 에이전트│
                       └─────────────────┘
```

## 📁 프로젝트 구조

```
PRISM-Orch/
├── src/
│   ├── main.py                    # FastAPI 애플리케이션 진입점
│   ├── api/
│   │   ├── endpoints/
│   │   │   └── orchestration.py   # 오케스트레이션 API 엔드포인트
│   │   └── schemas.py             # API 요청/응답 스키마
│   ├── core/
│   │   └── config.py              # 애플리케이션 설정 관리
│   ├── orchestration/
│   │   └── prism_orchestrator.py  # 핵심 오케스트레이터 클래스
│   └── utils/                     # 유틸리티 함수들
├── data/                          # 데이터 저장소
├── logs/                          # 로그 파일
├── test_comprehensive.py          # 종합 테스트 스크립트
├── requirements.txt               # Python 의존성
├── docker-compose.yml             # Docker 설정
└── README.md                      # 프로젝트 문서
```

## 🔧 핵심 구성 요소

### 1. PrismOrchestrator 클래스

`src/orchestration/prism_orchestrator.py`에 위치한 핵심 오케스트레이터입니다.

```python
class PrismOrchestrator:
    """
    PRISM-Core의 PrismLLMService를 활용한 고수준 오케스트레이터
    
    주요 역할:
    - PrismLLMService 초기화 (OpenAI 호환 vLLM 클라이언트 + PRISM-Core API 클라이언트)
    - 기본 도구들과 메인 오케스트레이션 에이전트 등록
    - 작업 분해를 첫 단계로 수행 (에이전트 측), 그 후 도구들과 함께 실행
    """
```

#### 주요 메서드:

- **`__init__()`**: 오케스트레이터 초기화 및 기본 도구 등록
- **`invoke()`**: 사용자 질의를 받아 오케스트레이션 실행
- **`register_default_tools()`**: RAG 검색, 규정 준수 등 기본 도구 등록

### 2. RAGSearchTool

지식 베이스에서 관련 정보를 검색하는 도구입니다.

```python
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
                    "domain": {"type": "string", "enum": ["research", "history"], 
                              "description": "검색 도메인", "default": "research"}
                },
                "required": ["query"]
            }
        )
```

#### 지원하는 검색 도메인:

- **OrchResearch**: 연구/기술 문서 (논문, 매뉴얼 등)
- **OrchHistory**: 사용자 수행 이력 (과거 작업 기록)
- **OrchCompliance**: 안전 규정 및 법규 (LOTO, 보호구 등)

### 3. API 엔드포인트

`src/api/endpoints/orchestration.py`에 정의된 REST API입니다.

```python
@router.post("/", response_model=OrchestrationResponse)
async def run_orchestration(query: UserQueryInput) -> OrchestrationResponse:
    """
    사용자 질의 기반 오케스트레이션 실행
    
    입력: 자연어 질의
    출력: 오케스트레이션 결과 (답변, 근거 문서, 규정 준수 정보 등)
    """
```

## 🚀 사용 방법

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/PRISM-System/PRISM-Orch.git
cd PRISM-Orch

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 PRISM-Core URL 등 설정 수정

# 의존성 설치
pip install -r requirements.txt
```

### 2. PRISM-Core 서버 시작

```bash
# PRISM-Core 디렉토리로 이동
cd ../prism-core

# Docker 서비스 시작
docker-compose up -d

# 서비스 상태 확인
curl http://localhost:8000/
```

### 3. PRISM-Orch 서버 시작

```bash
# PRISM-Orch 디렉토리로 돌아가기
cd ../PRISM-Orch

# 서버 시작
python -m src.main
```

### 4. API 호출 예시

```python
import requests

# 오케스트레이션 API 호출
response = requests.post(
    "http://localhost:8000/api/v1/orchestrate/",
    json={
        "query": "A-1 라인 압력에 이상이 생긴 것 같은데, 원인이 뭐야?",
        "user_id": "engineer_kim",
        "session_id": "session_123"
    }
)

result = response.json()
print(f"답변: {result['final_answer']}")
print(f"근거 문서: {result['supporting_documents']}")
print(f"규정 준수: {result['compliance_checked']}")
```

## 🔧 새로운 에이전트 개발 가이드

PRISM-Core를 활용하여 새로운 에이전트를 개발하는 방법을 설명합니다.

### 1. 기본 에이전트 구조

```python
from core.llm.prism_llm_service import PrismLLMService
from core.tools import BaseTool, ToolRegistry

class CustomAgent:
    def __init__(self, agent_name: str = "custom_agent"):
        self.agent_name = agent_name
        
        # PRISM-Core LLM 서비스 초기화
        self.llm = PrismLLMService(
            model_name="Qwen/Qwen3-0.6B",
            tool_registry=ToolRegistry(),
            llm_service_url="http://localhost:8000",
            agent_name=self.agent_name,
            openai_base_url="http://localhost:8001/v1"
        )
        
        # 커스텀 도구 등록
        self.register_custom_tools()
    
    def register_custom_tools(self):
        """커스텀 도구들을 등록합니다."""
        # 예: 데이터베이스 조회 도구
        db_tool = DatabaseQueryTool()
        self.llm.tool_registry.register_tool(db_tool)
        
        # 예: 외부 API 호출 도구
        api_tool = ExternalAPITool()
        self.llm.tool_registry.register_tool(api_tool)
    
    async def process_request(self, query: str):
        """사용자 요청을 처리합니다."""
        response = await self.llm.invoke(
            prompt=query,
            max_tokens=1000,
            temperature=0.3
        )
        return response
```

### 2. 커스텀 도구 개발

```python
class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="커스텀 기능을 수행하는 도구",
            parameters_schema={
                "type": "object",
                "properties": {
                    "parameter1": {
                        "type": "string",
                        "description": "첫 번째 매개변수"
                    },
                    "parameter2": {
                        "type": "integer",
                        "description": "두 번째 매개변수"
                    }
                },
                "required": ["parameter1"]
            }
        )
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """도구 실행 로직"""
        params = request.parameters
        
        # 실제 작업 수행
        result = self._perform_custom_operation(params)
        
        return ToolResponse(
            success=True,
            result=result,
            metadata={"execution_time": "1.2s"}
        )
    
    def _perform_custom_operation(self, params):
        """실제 커스텀 작업 수행"""
        # 여기에 실제 비즈니스 로직 구현
        return {"status": "success", "data": "작업 완료"}
```

### 3. Vector DB 활용

```python
class VectorDBTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="vector_search",
            description="Vector DB에서 관련 정보 검색",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색 쿼리"},
                    "class_name": {"type": "string", "description": "검색할 클래스명"},
                    "limit": {"type": "integer", "description": "반환할 문서 수"}
                },
                "required": ["query", "class_name"]
            }
        )
        self.base_url = "http://localhost:8000"
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        params = request.parameters
        
        # PRISM-Core Vector DB API 호출
        response = requests.post(
            f"{self.base_url}/api/vector-db/search/{params['class_name']}",
            json={
                "query": params["query"],
                "limit": params.get("limit", 5)
            }
        )
        
        if response.status_code == 200:
            documents = response.json()
            return ToolResponse(
                success=True,
                result={"documents": documents}
            )
        else:
            return ToolResponse(
                success=False,
                error=f"검색 실패: {response.status_code}"
            )
```

### 4. 에이전트 통합

```python
# 새로운 에이전트를 오케스트레이터에 통합
class ExtendedPrismOrchestrator(PrismOrchestrator):
    def __init__(self):
        super().__init__()
        self.register_custom_agents()
    
    def register_custom_agents(self):
        """커스텀 에이전트들을 등록합니다."""
        # 분석 에이전트 등록
        analysis_agent = AnalysisAgent()
        self.llm.tool_registry.register_tool(analysis_agent.get_tool())
        
        # 모니터링 에이전트 등록
        monitoring_agent = MonitoringAgent()
        self.llm.tool_registry.register_tool(monitoring_agent.get_tool())
```

## 🧪 테스트

### 종합 테스트 실행

```bash
# 종합 테스트 스크립트 실행
python test_comprehensive.py

# 테스트 결과 확인
cat test_report_*.json
```

### 개별 기능 테스트

```python
# 오케스트레이션 테스트
import requests

# 기본 오케스트레이션 테스트
response = requests.post(
    "http://localhost:8000/api/v1/orchestrate/",
    json={"query": "테스트 질의입니다."}
)
print(response.json())

# Vector DB 검색 테스트
response = requests.post(
    "http://localhost:8000/api/vector-db/search/OrchResearch",
    json={"query": "압력 이상", "limit": 3}
)
print(response.json())
```

## 📊 API 스키마

### 요청 스키마 (UserQueryInput)

```python
{
    "query": "사용자의 자연어 질의",
    "session_id": "세션 식별자 (선택사항)",
    "user_id": "사용자 식별자 (선택사항)",
    "user_preferences": {
        "mode": "conservative"  # 사용자 선호도
    }
}
```

### 응답 스키마 (OrchestrationResponse)

```python
{
    "session_id": "세션 ID",
    "final_answer": "최종 답변",
    "final_markdown": "마크다운 형태 리포트",
    "supporting_documents": ["근거 문서 1", "근거 문서 2"],
    "tools_used": ["rag_search", "compliance_check"],
    "tool_results": [{"tool": "rag_search", "result": {...}}],
    "compliance_checked": true,
    "compliance_evidence": ["규정 준수 근거"],
    "task_history": [...]
}
```

## 🔧 설정 옵션

### 환경 변수 (.env)

```env
# PRISM-Core 연결 설정
PRISM_CORE_BASE_URL=http://localhost:8000

# LLM 서비스 설정
OPENAI_BASE_URL=http://localhost:8001/v1
VLLM_MODEL=Qwen/Qwen3-0.6B

# Vector DB 설정
VECTOR_ENCODER_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIM=384

# 애플리케이션 설정
APP_HOST=0.0.0.0
APP_PORT=8000
```

## 📚 개발 가이드

### 1. 새로운 도구 추가

1. `BaseTool`을 상속하는 새 도구 클래스 생성
2. `parameters_schema` 정의
3. `execute` 메서드 구현
4. 오케스트레이터에 등록

### 2. 새로운 에이전트 추가

1. `PrismLLMService`를 활용하는 에이전트 클래스 생성
2. 필요한 도구들을 등록
3. `invoke` 메서드로 요청 처리
4. 오케스트레이터에 통합

### 3. Vector DB 활용

1. PRISM-Core의 Vector DB API 활용
2. 문서 인덱싱 및 검색
3. 임베딩 자동 생성 및 검증

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🆘 지원

- **Issues**: [GitHub Issues](https://github.com/PRISM-System/PRISM-Orch/issues)
- **문서**: [PRISM-Core Client Guide](../prism-core/client.md)
- **API 문서**: http://localhost:8000/docs

---

**PRISM-Orch** - 지능형 제조를 위한 AI 에이전트 오케스트레이션 플랫폼 🚀