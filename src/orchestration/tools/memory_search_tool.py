"""
Memory Search Tool

사용자의 과거 상호작용 기록을 검색하는 Tool입니다.
Mem0를 활용하여 장기 기억과 개인화된 상호작용을 제공합니다.
"""

import requests
from typing import Dict, Any, List, Optional
from core.tools import BaseTool, ToolRequest, ToolResponse
from ...core.config import settings

try:
    from mem0 import Memory
    from openai import OpenAI
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    print("⚠️  Mem0 라이브러리가 설치되지 않았습니다. 기본 메모리 검색만 사용 가능합니다.")


class MemorySearchTool(BaseTool):
    """
    사용자의 과거 상호작용 기록을 검색하는 Tool
    
    Mem0를 활용한 기능:
    - 사용자별 장기 기억 관리
    - 세션별 컨텍스트 유지
    - 개인화된 응답 생성
    - 적응형 학습 및 기억 강화
    """
    
    def __init__(self):
        super().__init__(
            name="memory_search",
            description="사용자의 과거 상호작용 기록을 검색하여 개인화된 응답을 제공합니다",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 쿼리"},
                    "user_id": {"type": "string", "description": "사용자 ID"},
                    "top_k": {"type": "integer", "description": "반환할 기록 수", "default": 3},
                    "memory_type": {
                        "type": "string", 
                        "enum": ["user", "session", "agent"], 
                        "description": "메모리 타입 (사용자별, 세션별, 에이전트별)", 
                        "default": "user"
                    },
                    "include_context": {
                        "type": "boolean", 
                        "description": "컨텍스트 정보 포함 여부", 
                        "default": True
                    }
                },
                "required": ["query", "user_id"]
            }
        )
        self._base = settings.PRISM_CORE_BASE_URL
        self._client_id = "orch"
        
        # Mem0 초기화
        self._mem0_initialized = False
        self._memory: Optional[Memory] = None
        self._openai_client: Optional[OpenAI] = None
        
        if MEM0_AVAILABLE:
            self._initialize_mem0()

    def _initialize_mem0(self) -> None:
        """Mem0 초기화"""
        try:
            # OpenAI 클라이언트 초기화 (Mem0에서 사용)
            # self._openai_client = OpenAI(
            #     base_url=settings.OPENAI_BASE_URL or "http://localhost:8001/v1",
            #     api_key=settings.OPENAI_API_KEY
            # )
            
            # Mem0 메모리 인스턴스 생성
            self._memory = Memory()
            self._mem0_initialized = True
            
            print("✅ Mem0 메모리 시스템 초기화 완료")
            
        except Exception as e:
            print(f"⚠️  Mem0 초기화 실패: {str(e)}")
            self._mem0_initialized = False

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Tool 실행"""
        try:
            params = request.parameters
            query = params["query"]
            user_id = params["user_id"]
            top_k = params.get("top_k", 3)
            memory_type = params.get("memory_type", "user")
            include_context = params.get("include_context", True)
            
            # Mem0가 사용 가능한 경우 우선 사용
            if self._mem0_initialized and self._memory:
                memories = await self._search_with_mem0(query, user_id, top_k, memory_type)
            else:
                # Fallback: 기존 Vector DB 검색
                memories = await self._search_with_vector_db(query, user_id, top_k)
            
            # 컨텍스트 정보 추가
            context_info = {}
            if include_context and self._mem0_initialized:
                context_info = await self._get_user_context(user_id)
            
            return ToolResponse(
                success=True,
                result={
                    "memories": memories,
                    "user_id": user_id,
                    "query": query,
                    "count": len(memories),
                    "memory_type": memory_type,
                    "context": context_info,
                    "mem0_enabled": self._mem0_initialized,
                    "domain": "memory"
                }
            )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                error_message=f"메모리 검색 중 오류: {str(e)}"
            )

    async def _search_with_mem0(self, query: str, user_id: str, top_k: int, memory_type: str) -> List[Dict[str, Any]]:
        """Mem0를 사용한 메모리 검색"""
        try:
            # Mem0 검색 실행
            search_result = self._memory.search(
                query=query,
                user_id=user_id,
                limit=top_k
            )
            
            memories = []
            for entry in search_result.get("results", []):
                memory_entry = {
                    "content": entry.get("memory", ""),
                    "score": entry.get("score", 0.0),
                    "timestamp": entry.get("timestamp", ""),
                    "memory_type": memory_type,
                    "source": "mem0"
                }
                memories.append(memory_entry)
            
            return memories
            
        except Exception as e:
            print(f"⚠️  Mem0 검색 실패: {str(e)}")
            return []

    async def _search_with_vector_db(self, query: str, user_id: str, top_k: int) -> List[Dict[str, Any]]:
        """Vector DB를 사용한 메모리 검색 (Fallback)"""
        try:
            # PRISM-Core Vector DB에서 사용자 이력 검색
            search_query = f"{query} user:{user_id}"
            
            response = requests.post(
                f"{self._base}/api/vector-db/search/OrchHistory",
                json={
                    "query": search_query,
                    "limit": top_k
                },
                params={"client_id": self._client_id},
                timeout=10,
            )
            
            memories = []
            if response.status_code == 200:
                results = response.json()
                
                for result in results:
                    memory_entry = {
                        "content": result.get("content", ""),
                        "score": result.get("score", 0.0),
                        "timestamp": result.get("timestamp", ""),
                        "memory_type": "vector_db",
                        "source": "prism_core"
                    }
                    memories.append(memory_entry)
            
            return memories
                
        except Exception as e:
            print(f"⚠️  Vector DB 검색 실패: {str(e)}")
            return []

    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """사용자 컨텍스트 정보 조회"""
        try:
            if not self._memory:
                return {}
            
            # 사용자별 메모리 통계
            user_stats = {
                "total_memories": 0,
                "recent_activity": "",
                "preferences": {},
                "interaction_patterns": []
            }
            
            # 최근 상호작용 패턴 분석
            recent_memories = self._memory.search(
                query="recent interactions",
                user_id=user_id,
                limit=5
            )
            
            if recent_memories.get("results"):
                user_stats["total_memories"] = len(recent_memories["results"])
                user_stats["recent_activity"] = "최근 상호작용이 있습니다"
            
            return user_stats
            
        except Exception as e:
            print(f"⚠️  사용자 컨텍스트 조회 실패: {str(e)}")
            return {}

    async def add_memory(self, user_id: str, conversation_messages: List[Dict[str, str]]) -> bool:
        """새로운 메모리 추가"""
        try:
            if not self._mem0_initialized or not self._memory:
                return False
            
            # Mem0에 대화 내용 추가
            self._memory.add(
                messages=conversation_messages,
                user_id=user_id
            )
            
            print(f"✅ 사용자 '{user_id}'의 메모리 추가 완료")
            return True
            
        except Exception as e:
            print(f"❌ 메모리 추가 실패: {str(e)}")
            return False

    async def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 메모리 요약 정보"""
        try:
            if not self._mem0_initialized or not self._memory:
                return {"error": "Mem0 not available"}
            
            # 사용자별 메모리 요약 생성
            summary_query = f"사용자 {user_id}의 과거 상호작용 요약"
            summary_memories = self._memory.search(
                query=summary_query,
                user_id=user_id,
                limit=10
            )
            
            return {
                "user_id": user_id,
                "total_memories": len(summary_memories.get("results", [])),
                "memory_summary": summary_memories.get("results", []),
                "last_updated": "현재 시간"
            }
            
        except Exception as e:
            return {"error": f"메모리 요약 생성 실패: {str(e)}"}

    def is_mem0_available(self) -> bool:
        """Mem0 사용 가능 여부 확인"""
        return self._mem0_initialized and self._memory is not None 