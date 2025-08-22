"""
RAG Search Tool

지식 베이스에서 관련 정보를 검색하는 Tool입니다.
"""

import requests
from typing import Dict, Any, List
from core.tools import BaseTool, ToolRequest, ToolResponse
from ...core.config import settings


class RAGSearchTool(BaseTool):
    """
    지식 베이스에서 관련 정보를 검색하는 Tool
    
    지원하는 도메인:
    - research: 연구/기술 문서
    - history: 사용자 수행 이력
    - compliance: 안전 규정 및 법규
    """
    
    def __init__(self):
        super().__init__(
            name="rag_search",
            description="지식 베이스에서 관련 정보를 검색합니다",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 쿼리"},
                    "top_k": {"type": "integer", "description": "반환할 문서 수", "default": 3},
                    "domain": {
                        "type": "string", 
                        "enum": ["research", "history", "compliance"], 
                        "description": "검색 도메인 (연구/기술문서, 사용자 수행내역, 안전 규정)", 
                        "default": "research"
                    }
                },
                "required": ["query"]
            }
        )
        self._initialized = False
        self._class_research = "OrchResearch"
        self._class_history = "OrchHistory"
        self._class_compliance = "OrchCompliance"
        self._client_id = "orch"
        self._encoder = settings.VECTOR_ENCODER_MODEL
        self._vector_dim = settings.VECTOR_DIM
        self._base = settings.PRISM_CORE_BASE_URL

    def _ensure_index_and_seed(self) -> None:
        """인덱스 생성 및 초기 데이터 시딩"""
        if self._initialized:
            return
            
        try:
            # Research 인덱스 생성
            self._create_research_index()
            self._seed_research_data()
            
            # History 인덱스 생성
            self._create_history_index()
            self._seed_history_data()
            
            # Compliance 인덱스 생성
            self._create_compliance_index()
            self._seed_compliance_data()
            
            # 임베딩 검증 및 재생성
            self._validate_and_regenerate_embeddings()
            
            self._initialized = True
            
        except Exception as e:
            print(f"⚠️  인덱스 초기화 실패: {str(e)}")
            self._initialized = True  # 실패해도 계속 진행

    def _create_research_index(self) -> None:
        """연구 문서 인덱스 생성"""
        requests.post(
            f"{self._base}/api/vector-db/indices",
            json={
                "class_name": self._class_research,
                "description": "Papers/technical docs knowledge base",
                "vector_dimension": self._vector_dim,
                "encoder_model": self._encoder,
                "properties": []
            },
            params={"client_id": self._client_id},
            timeout=10,
        )

    def _seed_research_data(self) -> None:
        """연구 문서 데이터 시딩"""
        research_docs = [
            {
                "title": f"Paper {i+1}", 
                "content": f"제조 공정 최적화 기술 문서 {i+1}: 공정 제어, 안전 규정, 예지 정비, 데이터 기반 분석.", 
                "metadata": {}
            }
            for i in range(10)
        ]
        
        requests.post(
            f"{self._base}/api/vector-db/documents/{self._class_research}/batch",
            json=research_docs,
            params={"client_id": self._client_id, "encoder_model": self._encoder},
            timeout=15,
        )

    def _create_history_index(self) -> None:
        """사용자 이력 인덱스 생성"""
        requests.post(
            f"{self._base}/api/vector-db/indices",
            json={
                "class_name": self._class_history,
                "description": "All users' past execution logs",
                "vector_dimension": self._vector_dim,
                "encoder_model": self._encoder,
                "properties": []
            },
            params={"client_id": self._client_id},
            timeout=10,
        )

    def _seed_history_data(self) -> None:
        """사용자 이력 데이터 시딩"""
        history_docs = [
            {
                "title": f"History {i+1}", 
                "content": f"사용자 수행 내역 {i+1}: 압력 이상 대응, 점검 절차 수행, 원인 분석 리포트, 후속 조치 완료.", 
                "metadata": {}
            }
            for i in range(10)
        ]
        
        requests.post(
            f"{self._base}/api/vector-db/documents/{self._class_history}/batch",
            json=history_docs,
            params={"client_id": self._client_id, "encoder_model": self._encoder},
            timeout=15,
        )

    def _create_compliance_index(self) -> None:
        """규정 준수 인덱스 생성"""
        requests.post(
            f"{self._base}/api/vector-db/indices",
            json={
                "class_name": self._class_compliance,
                "description": "Safety/legal/company compliance rules",
                "vector_dimension": self._vector_dim,
                "encoder_model": self._encoder,
                "properties": []
            },
            params={"client_id": self._client_id},
            timeout=10,
        )

    def _seed_compliance_data(self) -> None:
        """규정 준수 데이터 시딩"""
        compliance_docs = [
            {
                "title": f"Rule {i+1}", 
                "content": f"안전 법규 및 사내 규정 {i+1}: 잠금/표시 절차(LOTO), 보호구 착용, 위험물 취급, 점검 기록 보관, 승인 절차 준수.", 
                "metadata": {}
            }
            for i in range(10)
        ]
        
        requests.post(
            f"{self._base}/api/vector-db/documents/{self._class_compliance}/batch",
            json=compliance_docs,
            params={"client_id": self._client_id, "encoder_model": self._encoder},
            timeout=15,
        )

    def _validate_and_regenerate_embeddings(self) -> None:
        """벡터 임베딩이 없는 문서들을 감지하고 재생성합니다."""
        try:
            classes_to_check = [self._class_research, self._class_history, self._class_compliance]
            
            for class_name in classes_to_check:
                # 문서 조회
                resp = requests.get(
                    f"{self._base}/api/vector-db/documents/{class_name}",
                    params={"client_id": self._client_id, "limit": 100},
                    timeout=10,
                )
                
                if resp.status_code == 200:
                    documents = resp.json()
                    documents_without_embeddings = []
                    
                    for doc in documents:
                        # 벡터 임베딩이 없는 문서 감지
                        if not doc.get("vectorWeights") or doc["vectorWeights"] is None:
                            documents_without_embeddings.append(doc)
                    
                    if documents_without_embeddings:
                        print(f"⚠️  {class_name}에서 임베딩이 없는 문서 {len(documents_without_embeddings)}개 발견")
                        
                        # 임베딩이 없는 문서 삭제
                        doc_ids = [doc["id"] for doc in documents_without_embeddings]
                        delete_resp = requests.post(
                            f"{self._base}/api/vector-db/documents/{class_name}/delete-batch",
                            json=doc_ids,
                            params={"client_id": self._client_id},
                            timeout=15,
                        )
                        
                        if delete_resp.status_code == 200:
                            print(f"✅ {class_name}에서 임베딩이 없는 문서 {len(doc_ids)}개 삭제 완료")
                            
                            # 올바른 임베딩과 함께 문서 재생성
                            docs_to_add = []
                            for doc in documents_without_embeddings:
                                docs_to_add.append({
                                    "title": doc["properties"].get("title", ""),
                                    "content": doc["properties"].get("content", ""),
                                    "metadata": doc["properties"].get("metadata", {})
                                })
                            
                            if docs_to_add:
                                add_resp = requests.post(
                                    f"{self._base}/api/vector-db/documents/{class_name}/batch",
                                    json=docs_to_add,
                                    params={"client_id": self._client_id, "encoder_model": self._encoder},
                                    timeout=15,
                                )
                                
                                if add_resp.status_code == 200:
                                    print(f"✅ {class_name}에 문서 {len(docs_to_add)}개 재생성 완료")
                                
        except Exception as e:
            print(f"⚠️  임베딩 검증 중 오류: {str(e)}")

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Tool 실행"""
        try:
            self._ensure_index_and_seed()
            
            params = request.parameters
            query = params["query"]
            top_k = params.get("top_k", 3)
            domain = params.get("domain", "research")
            
            # 도메인에 따른 클래스 선택
            class_mapping = {
                "research": self._class_research,
                "history": self._class_history,
                "compliance": self._class_compliance
            }
            
            class_name = class_mapping.get(domain, self._class_research)
            
            # PRISM-Core Vector DB API 호출
            response = requests.post(
                f"{self._base}/api/vector-db/search/{class_name}",
                json={"query": query, "limit": top_k},
                params={"client_id": self._client_id},
                timeout=10,
            )
            
            if response.status_code == 200:
                results = response.json()
                documents = []
                
                for result in results:
                    docs = f"{result.get('score', 0):.3f} | {result.get('content', '')}"
                    documents.append(docs)
                
                return ToolResponse(
                    success=True,
                    result={
                        "documents": documents,
                        "domain": domain,
                        "query": query,
                        "count": len(documents)
                    }
                )
            else:
                return ToolResponse(
                    success=False,
                    error_message=f"검색 실패: {response.status_code}"
                )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                error_message=f"RAG 검색 중 오류: {str(e)}"
            ) 