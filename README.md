# PRISM-Orch

PRISM-Core를 기반으로 한 AI 에이전트 오케스트레이션 시스템입니다.
[Mem0](https://github.com/mem0ai/mem0)를 통한 장기 기억과 개인화된 상호작용을 지원합니다.
LLM을 통한 지능형 규정 준수 분석을 제공합니다.

## 📋 목차

1. [개요](#개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [프로젝트 구조](#프로젝트-구조)
4. [주요 구성 요소](#주요-구성-요소)
5. [설치 및 실행](#설치-및-실행)
6. [사용법](#사용법)
7. [Mem0 통합](#mem0-통합)
8. [LLM 기반 규정 준수 분석](#llm-기반-규정-준수-분석)
9. [개발 가이드](#개발-가이드)
10. [API 문서](#api-문서)
11. [테스트](#테스트)
12. [기여하기](#기여하기)

## 🎯 개요

PRISM-Orch는 PRISM-Core의 강력한 기능들을 활용하여 복잡한 AI 에이전트 오케스트레이션을 수행하는 시스템입니다. 

### 주요 특징

- **모듈화된 아키텍처**: 기능별로 분리된 모듈 구조로 유지보수성 향상
- **PRISM-Core 기반**: 벡터 DB, LLM 서비스, Tool 시스템 등 PRISM-Core의 모든 기능 활용
- **Mem0 통합**: 장기 기억과 개인화된 상호작용을 위한 범용 메모리 레이어
- **LLM 기반 규정 준수**: 지능형 안전 규정 및 법규 준수 분석
- **다양한 Tool 지원**: RAG 검색, 규정 준수 검증, 사용자 이력 검색 등
- **워크플로우 관리**: 복잡한 작업을 단계별로 정의하고 실행
- **에이전트 생명주기 관리**: 에이전트 등록, 설정, 모니터링

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    PRISM-Orch                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Tools     │  │   Agents    │  │ Workflows   │        │
│  │   Module    │  │   Module    │  │   Module    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                 PrismOrchestrator                           │
│              (Main Coordinator)                             │
├─────────────────────────────────────────────────────────────┤
│                    PRISM-Core                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Vector DB   │  │ LLM Service │  │ Tool System │        │
│  │ (Weaviate)  │  │   (vLLM)    │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                      Mem0                                   │
│              (Memory Layer)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ User Memory │  │ Session     │  │ Agent       │        │
│  │             │  │ Memory      │  │ Memory      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                   LLM Analysis                             │
│              (Compliance & Safety)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Compliance  │  │ Risk        │  │ Safety      │        │
│  │ Analysis    │  │ Assessment  │  │ Guidelines  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 📁 프로젝트 구조

```
PRISM-Orch/
├── src/
│   ├── orchestration/           # 오케스트레이션 핵심 모듈
│   │   ├── __init__.py
│   │   ├── prism_orchestrator.py # 메인 오케스트레이터
│   │   ├── agent_manager.py     # 에이전트 관리
│   │   ├── workflow_manager.py  # 워크플로우 관리
│   │   └── tools/               # Tool 모듈들
│   │       ├── __init__.py
│   │       ├── rag_search_tool.py    # RAG 검색 Tool
│   │       ├── compliance_tool.py    # 규정 준수 Tool (LLM 기반)
│   │       └── memory_search_tool.py # 사용자 이력 Tool (Mem0 통합)
│   ├── api/                     # API 엔드포인트
│   ├── core/                    # 핵심 설정 및 유틸리티
│   └── main.py                  # 애플리케이션 진입점
├── tests/                       # 테스트 파일들
├── example_modular_usage.py     # 모듈화된 구조 사용 예제
├── example_mem0_integration.py  # Mem0 통합 예제
├── example_compliance_llm.py    # LLM 기반 규정 준수 분석 예제
├── test_comprehensive.py        # 종합 테스트
└── README.md
```

## 🔧 주요 구성 요소

### 1. PrismOrchestrator (메인 오케스트레이터)

PRISM-Orch의 핵심 클래스로, 모든 구성 요소를 통합 관리합니다.

```python
from src.orchestration import PrismOrchestrator

# 오케스트레이터 초기화
orchestrator = PrismOrchestrator()

# 개인화된 오케스트레이션 수행
response = await orchestrator.orchestrate(
    "A-1 라인에서 압력 이상이 발생했습니다. 어떻게 대응해야 할까요?",
    user_id="engineer_kim"  # 사용자별 개인화
)
```

**주요 기능:**
- PRISM-Core LLM 서비스 연동
- Mem0를 통한 장기 기억 관리
- LLM 기반 규정 준수 분석
- 기본 Tool 자동 등록
- 오케스트레이션 에이전트 관리
- 워크플로우 실행

### 2. Tools Module (도구 모듈)

#### RAGSearchTool
지식 베이스에서 관련 정보를 검색하는 Tool입니다.

```python
from src.orchestration.tools import RAGSearchTool

rag_tool = RAGSearchTool()
# 연구 문서, 사용자 이력, 규정 문서 검색 지원
```

**지원 도메인:**
- `research`: 연구/기술 문서
- `history`: 사용자 수행 이력  
- `compliance`: 안전 규정 및 법규

#### ComplianceTool (LLM 기반)
안전 규정 및 법규 준수 여부를 검증하는 Tool입니다.

```python
from src.orchestration.tools import ComplianceTool

compliance_tool = ComplianceTool()
# LLM을 통한 지능형 안전성 검증
```

**LLM 기반 기능:**
- 지능형 규정 준수 분석
- 위험 수준 자동 평가
- 맥락 기반 권장사항 생성
- 업계별 특화 규정 적용

#### MemorySearchTool (Mem0 통합)
사용자의 과거 상호작용 기록을 검색하는 Tool입니다.

```python
from src.orchestration.tools import MemorySearchTool

memory_tool = MemorySearchTool()
# Mem0를 통한 장기 기억과 개인화된 상호작용
```

**Mem0 기능:**
- 사용자별 장기 기억 관리
- 세션별 컨텍스트 유지
- 개인화된 응답 생성
- 적응형 학습 및 기억 강화

### 3. AgentManager (에이전트 관리자)

에이전트의 생명주기를 관리하는 클래스입니다.

```python
from src.orchestration import AgentManager

agent_manager = AgentManager()

# 에이전트 등록
agent_manager.register_agent(agent)

# Tool 할당
agent_manager.assign_tools_to_agent("agent_name", ["tool1", "tool2"])

# 상태 조회
status = agent_manager.get_agent_status("agent_name")
```

**주요 기능:**
- 에이전트 등록/삭제
- Tool 권한 관리
- 에이전트 상태 모니터링
- 설정 관리

### 4. WorkflowManager (워크플로우 관리자)

복잡한 작업을 단계별로 정의하고 실행하는 클래스입니다.

```python
from src.orchestration import WorkflowManager

workflow_manager = WorkflowManager()

# 워크플로우 정의
workflow_steps = [
    {
        "name": "데이터_검색",
        "type": "tool_call",
        "tool_name": "rag_search",
        "parameters": {"query": "{{search_query}}", "domain": "research"}
    },
    {
        "name": "규정_검증", 
        "type": "tool_call",
        "tool_name": "compliance_check",
        "parameters": {"action": "{{proposed_action}}"}
    }
]

workflow_manager.define_workflow("압력_이상_대응", workflow_steps)

# 워크플로우 실행
result = await workflow_manager.execute_workflow("압력_이상_대응", context)
```

**지원 단계 타입:**
- `tool_call`: Tool 호출
- `agent_call`: 에이전트 호출
- `condition`: 조건 평가

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/PRISM-System/PRISM-Orch.git
cd PRISM-Orch

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필요한 설정 수정
PRISM_CORE_BASE_URL=http://localhost:8000
OPENAI_BASE_URL=http://localhost:8001/v1
VLLM_MODEL=Qwen/Qwen3-0.6B
```

### 3. PRISM-Core 서버 시작

```bash
# PRISM-Core 서버가 실행 중인지 확인
curl http://localhost:8000/
```

### 4. PRISM-Orch 실행

```bash
# 개발 모드로 실행
uv run python -m src.main

# 또는 직접 실행
uv run python src/main.py
```

## 📖 사용법

### 1. 기본 오케스트레이션

```python
import asyncio
from src.orchestration import PrismOrchestrator

async def main():
    orchestrator = PrismOrchestrator()
    
    response = await orchestrator.orchestrate(
        "A-1 라인에서 압력 이상이 발생했습니다. 어떻게 대응해야 할까요?"
    )
    
    print(f"응답: {response.text}")
    print(f"사용된 Tools: {response.tools_used}")

asyncio.run(main())
```

### 2. 개인화된 오케스트레이션 (Mem0 활용)

```python
import asyncio
from src.orchestration import PrismOrchestrator

async def main():
    orchestrator = PrismOrchestrator()
    
    # 사용자별 개인화된 대화
    user_id = "engineer_kim"
    
    # 첫 번째 대화
    response1 = await orchestrator.orchestrate(
        "압력 이상 대응 방법을 알려주세요.",
        user_id=user_id
    )
    
    # 두 번째 대화 (이전 대화를 기억)
    response2 = await orchestrator.orchestrate(
        "이전에 말씀하신 대로 했는데, 다음 단계는 무엇인가요?",
        user_id=user_id
    )
    
    # 사용자 메모리 요약 조회
    summary = await orchestrator.get_user_memory_summary(user_id)
    print(f"사용자 메모리: {summary}")

asyncio.run(main())
```

### 3. LLM 기반 규정 준수 검증

```python
import asyncio
from src.orchestration.tools import ComplianceTool
from core.tools import ToolRequest

async def main():
    compliance_tool = ComplianceTool()
    
    # 규정 준수 검증
    request = ToolRequest(
        tool_name="compliance_check",
        parameters={
            "action": "고온 배관 점검",
            "context": "온도 300도 배관 시스템 점검 작업"
        }
    )
    
    response = await compliance_tool.execute(request)
    
    if response.success:
        result = response.result
        print(f"준수 상태: {result['compliance_status']}")
        print(f"위험 수준: {result['risk_level']}")
        print(f"권장사항: {result['recommendations']}")
        print(f"분석 근거: {result['reasoning']}")

asyncio.run(main())
```

### 4. 커스텀 에이전트 생성

```python
from src.orchestration import AgentManager
from core.llm.schemas import Agent

agent_manager = AgentManager()

# 에이전트 생성
custom_agent = Agent(
    name="data_analyst",
    description="데이터 분석 전문가",
    role_prompt="당신은 제조 공정 데이터를 분석하는 전문가입니다.",
    tools=["rag_search", "compliance_check"]
)

# 에이전트 등록
agent_manager.register_agent(custom_agent)
```

### 5. 워크플로우 정의 및 실행

```python
from src.orchestration import WorkflowManager

workflow_manager = WorkflowManager()

# 워크플로우 정의
steps = [
    {
        "name": "상황_분석",
        "type": "tool_call",
        "tool_name": "rag_search",
        "parameters": {"query": "{{user_query}}", "domain": "research"}
    },
    {
        "name": "안전성_검증",
        "type": "tool_call",
        "tool_name": "compliance_check", 
        "parameters": {"action": "{{proposed_action}}"}
    }
]

workflow_manager.define_workflow("종합_분석", steps)

# 워크플로우 실행
context = {"user_query": "압력 이상 대응", "proposed_action": "센서 교체"}
result = await workflow_manager.execute_workflow("종합_분석", context)
```

### 6. Tool 직접 사용

```python
from src.orchestration.tools import RAGSearchTool
from core.tools import ToolRequest

# Tool 인스턴스 생성
rag_tool = RAGSearchTool()

# Tool 실행
request = ToolRequest(
    tool_name="rag_search",
    parameters={
        "query": "압력 이상 대응 방법",
        "domain": "research",
        "top_k": 3
    }
)

response = await rag_tool.execute(request)
print(f"검색 결과: {response.result}")
```

## 🧠 Mem0 통합

PRISM-Orch는 [Mem0](https://github.com/mem0ai/mem0)를 통합하여 강력한 장기 기억과 개인화된 상호작용을 제공합니다.

### Mem0 설치

```bash
pip install mem0ai>=0.1.116
```

### Mem0 기능

#### 1. 장기 기억 관리
```python
# 사용자별 메모리 검색
memories = await orchestrator.search_user_memories(
    query="압력 이상 대응",
    user_id="engineer_kim",
    top_k=3
)
```

#### 2. 개인화된 응답
```python
# 사용자 선호도 학습
response = await orchestrator.orchestrate(
    "저는 항상 안전을 최우선으로 생각합니다.",
    user_id="engineer_kim"
)
```

#### 3. 메모리 요약
```python
# 사용자 메모리 요약 조회
summary = await orchestrator.get_user_memory_summary("engineer_kim")
print(f"총 메모리 수: {summary['total_memories']}")
```

#### 4. 다중 사용자 지원
```python
# 여러 사용자의 개인화된 대화
users = ["engineer_kim", "technician_lee", "supervisor_park"]

for user_id in users:
    response = await orchestrator.orchestrate(
        "압력 이상 대응 방법을 알려주세요.",
        user_id=user_id
    )
```

### Mem0 사용 예제

```python
# example_mem0_integration.py 실행
uv run python example_mem0_integration.py
```

## 🔍 LLM 기반 규정 준수 분석

PRISM-Orch는 LLM을 활용하여 지능형 규정 준수 분석을 제공합니다.

### LLM 기반 분석 기능

#### 1. 지능형 준수 상태 판단
```python
# LLM을 통한 규정 준수 분석
compliance_result = await compliance_tool.execute(ToolRequest(
    tool_name="compliance_check",
    parameters={
        "action": "고압 가스 배관 누출 수리",
        "context": "운영 중인 고압 가스 배관에서 누출이 발생하여 긴급 수리가 필요한 상황"
    }
))
```

#### 2. 위험 수준 자동 평가
- **Low**: 안전한 작업
- **Medium**: 주의가 필요한 작업
- **High**: 위험한 작업 (특별 승인 필요)

#### 3. 맥락 기반 권장사항
```python
# 분석 결과에서 권장사항 추출
recommendations = compliance_result.result['recommendations']
for rec in recommendations:
    print(f"권장사항: {rec}")
```

#### 4. 업계별 특화 규정
- 화학 공업: 독성 물질 취급 규정
- 전력 산업: 고전압 안전 규정
- 제철 산업: 고온 작업 안전 규정

### 준수 상태 분류

- **compliant**: 규정 준수
- **conditional**: 조건부 준수
- **requires_review**: 검토 필요
- **non_compliant**: 미준수

### LLM 기반 분석 예제

```python
# example_compliance_llm.py 실행
uv run python example_compliance_llm.py
```

### 분석 결과 예시

```json
{
    "compliance_status": "requires_review",
    "risk_level": "high",
    "recommendations": [
        "안전 관리자 승인 필요",
        "보호구 착용 필수",
        "작업 전 안전 점검 수행",
        "응급 대응 계획 수립"
    ],
    "reasoning": "고압 가스 배관 작업은 높은 위험도를 가지므로 특별한 안전 조치가 필요합니다..."
}
```

## 🛠️ 개발 가이드

### 1. 새로운 Tool 개발

```python
from core.tools import BaseTool, ToolRequest, ToolResponse

class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="커스텀 Tool 설명",
            parameters_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "매개변수 설명"}
                },
                "required": ["param1"]
            }
        )
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        # Tool 로직 구현
        params = request.parameters
        
        # 실제 작업 수행
        result = {"output": "작업 결과"}
        
        return ToolResponse(
            success=True,
            result=result
        )
```

### 2. 새로운 에이전트 타입 개발

```python
from src.orchestration import AgentManager
from core.llm.schemas import Agent

def create_specialized_agent():
    agent = Agent(
        name="specialized_agent",
        description="전문 에이전트",
        role_prompt="전문 역할 프롬프트",
        tools=["custom_tool", "rag_search"]
    )
    
    agent_manager = AgentManager()
    agent_manager.register_agent(agent)
    
    return agent
```

### 3. 워크플로우 확장

```python
def create_advanced_workflow():
    steps = [
        # 기존 단계들...
        {
            "name": "결과_검증",
            "type": "condition",
            "condition": "context.get('result_quality') > 0.8"
        },
        {
            "name": "보고서_생성",
            "type": "agent_call",
            "agent_name": "report_generator",
            "prompt_template": "{{analysis_result}}를 바탕으로 보고서를 작성하세요."
        }
    ]
    
    return steps
```

### 4. Mem0 확장

```python
from src.orchestration.tools import MemorySearchTool

class CustomMemoryTool(MemorySearchTool):
    async def custom_memory_analysis(self, user_id: str) -> Dict[str, Any]:
        """사용자 메모리 커스텀 분석"""
        # 커스텀 분석 로직 구현
        pass
```

### 5. LLM 기반 분석 확장

```python
from src.orchestration.tools import ComplianceTool

class CustomComplianceTool(ComplianceTool):
    async def industry_specific_analysis(self, action: str, industry: str) -> Dict[str, Any]:
        """업계별 특화 규정 준수 분석"""
        # 업계별 특화 분석 로직 구현
        pass
```

## 📚 API 문서

### 오케스트레이션 API

- `POST /api/v1/orchestrate/`: 메인 오케스트레이션 엔드포인트
- `GET /api/v1/agents/`: 등록된 에이전트 목록 조회
- `POST /api/v1/agents/`: 새 에이전트 등록
- `GET /api/v1/workflows/`: 워크플로우 목록 조회
- `POST /api/v1/workflows/`: 새 워크플로우 정의

### 메모리 API

- `GET /api/v1/memory/{user_id}/summary`: 사용자 메모리 요약
- `POST /api/v1/memory/{user_id}/search`: 메모리 검색
- `POST /api/v1/memory/{user_id}/add`: 메모리 추가

### 규정 준수 API

- `POST /api/v1/compliance/check`: 규정 준수 검증
- `GET /api/v1/compliance/rules`: 관련 규정 조회
- `POST /api/v1/compliance/analysis`: 상세 규정 준수 분석

### 요청 예시

```bash
# 오케스트레이션 요청
curl -X POST "http://localhost:8000/api/v1/orchestrate/" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A-1 라인 압력 이상 대응 방법",
    "user_id": "engineer_001"
  }'

# 메모리 검색 요청
curl -X POST "http://localhost:8000/api/v1/memory/engineer_001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "압력 이상 대응",
    "top_k": 3
  }'

# 규정 준수 검증 요청
curl -X POST "http://localhost:8000/api/v1/compliance/check" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "고온 배관 점검",
    "context": "온도 300도 배관 시스템 점검"
  }'
```

## 🧪 테스트

### 1. 종합 테스트 실행

```bash
# 종합 테스트 실행
uv run python test_comprehensive.py
```

### 2. 모듈화된 구조 테스트

```bash
# 모듈화된 구조 사용 예제 실행
uv run python example_modular_usage.py
```

### 3. Mem0 통합 테스트

```bash
# Mem0 통합 예제 실행
uv run python example_mem0_integration.py
```

### 4. LLM 기반 규정 준수 테스트

```bash
# LLM 기반 규정 준수 분석 예제 실행
uv run python example_compliance_llm.py
```

### 5. 개별 모듈 테스트

```bash
# Tool 테스트
uv run python -m pytest tests/test_tools.py

# 에이전트 관리 테스트
uv run python -m pytest tests/test_agent_manager.py

# 워크플로우 테스트
uv run python -m pytest tests/test_workflow_manager.py
```

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 개발 가이드라인

- **코드 스타일**: PEP 8 준수
- **문서화**: 모든 함수와 클래스에 docstring 작성
- **테스트**: 새로운 기능에 대한 테스트 코드 작성
- **타입 힌트**: Python 타입 힌트 사용

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🆘 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/PRISM-System/PRISM-Orch/issues)
- **문서**: [Wiki](https://github.com/PRISM-System/PRISM-Orch/wiki)
- **이메일**: support@prism-system.com

## 🙏 감사의 말

- [Mem0](https://github.com/mem0ai/mem0) - AI 에이전트를 위한 범용 메모리 레이어
- [PRISM-Core](https://github.com/PRISM-System/prism-core) - 핵심 AI 인프라

---

**PRISM-Orch** - AI 에이전트 오케스트레이션의 새로운 표준 🚀