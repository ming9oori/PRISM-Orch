from typing import List, Dict, Any, Optional
import requests
import json
from ..core.config import settings

class RAGSystem:
    """
    Retrieval-Augmented Generation (RAG) 시스템을 담당하는 클래스입니다.
    prism-core의 Vector DB를 활용하여 외부 지식 베이스와 에이전트 메모리로부터 관련 정보를 검색하여
    에이전트의 응답 생성을 보강합니다.
    """
    def __init__(self):
        """
        RAGSystem을 초기화합니다.
        prism-core Vector DB 클라이언트를 설정합니다.
        """
        self.research_vector_url = f"{settings.RESEARCH_WEAVIATE_URL}/vector-db"
        self.memory_vector_url = f"{settings.MEMORY_WEAVIATE_URL}/vector-db"
        
        # API 키 설정
        self.research_api_key = settings.RESEARCH_WEAVIATE_API_KEY
        self.memory_api_key = settings.MEMORY_WEAVIATE_API_KEY
        
        print(f"INFO:     RAGSystem initialized.")
        print(f"INFO:     Research Vector DB URL: {self.research_vector_url}")
        print(f"INFO:     Memory Vector DB URL: {self.memory_vector_url}")

    def _make_request(self, url: str, method: str = "GET", data: Dict = None, api_key: str = None) -> Dict:
        """Vector DB API 요청을 수행합니다."""
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"WARNING: Vector DB request failed: {e}")
            return {"success": False, "error": str(e)}

    def retrieve_knowledge(self, query: str, top_k: int = 3) -> List[str]:
        """
        주어진 질의와 관련된 외부 지식(문서)을 검색합니다.

        Args:
            query (str): 검색할 질의
            top_k (int): 검색할 문서의 수

        Returns:
            List[str]: 검색된 문서 내용 또는 ID 목록
        """
        print(f"INFO:     Retrieving knowledge for query: '{query}'")

        # prism-core Vector DB API를 통한 검색
        search_data = {
            "query": query,
            "top_k": top_k,
            "class_name": "research_documents"  # 기본 클래스명
        }
        
        result = self._make_request(
            f"{self.research_vector_url}/search",
            method="POST",
            data=search_data,
            api_key=self.research_api_key
        )
        
        if result.get("success", False) and "results" in result:
            documents = []
            for doc in result["results"]:
                if "content" in doc:
                    documents.append(doc["content"])
                elif "text" in doc:
                    documents.append(doc["text"])
                else:
                    documents.append(str(doc))
            return documents
        else:
            print(f"WARNING: Knowledge retrieval failed, using fallback")
            # 폴백: 목업 데이터 반환
            return [
                f"'{query}' 관련 문서 1: ...내용...",
                f"'{query}' 관련 문서 2: ...내용...",
                f"'{query}' 관련 문서 3: ...내용...",
            ][:top_k]

    def retrieve_from_memory(self, user_id: str, top_k: int = 3) -> List[str]:
        """
        과거 상호작용 기록(에이전트 메모리)을 검색합니다.

        Args:
            user_id (str): 사용자의 ID
            top_k (int): 검색할 기록의 수

        Returns:
            List[str]: 관련 과거 상호작용 기록 목록
        """
        print(f"INFO:     Retrieving memory for user: '{user_id}'")
        
        # prism-core Vector DB API를 통한 메모리 검색
        search_data = {
            "query": f"user:{user_id}",
            "top_k": top_k,
            "class_name": "agent_memory"
        }
        
        result = self._make_request(
            f"{self.memory_vector_url}/search",
            method="POST",
            data=search_data,
            api_key=self.memory_api_key
        )
        
        if result.get("success", False) and "results" in result:
            memories = []
            for memory in result["results"]:
                if "content" in memory:
                    memories.append(memory["content"])
                elif "text" in memory:
                    memories.append(memory["text"])
                else:
                    memories.append(str(memory))
            return memories
        else:
            print(f"WARNING: Memory retrieval failed, using fallback")
            # 폴백: 목업 데이터 반환
            return [
                f"'{user_id}'의 과거 상호작용 1",
                f"'{user_id}'의 과거 상호작용 2",
            ][:top_k]

    def store_knowledge(self, documents: List[Dict[str, Any]], class_name: str = "research_documents") -> bool:
        """
        외부 지식을 Vector DB에 저장합니다.

        Args:
            documents (List[Dict]): 저장할 문서 목록
            class_name (str): Vector DB 클래스명

        Returns:
            bool: 저장 성공 여부
        """
        print(f"INFO:     Storing {len(documents)} documents to knowledge base")
        
        # prism-core Vector DB API를 통한 문서 저장
        store_data = {
            "documents": documents,
            "class_name": class_name
        }
        
        result = self._make_request(
            f"{self.research_vector_url}/documents",
            method="POST",
            data=store_data,
            api_key=self.research_api_key
        )
        
        return result.get("success", False)

    def store_memory(self, user_id: str, memories: List[Dict[str, Any]]) -> bool:
        """
        에이전트 메모리를 Vector DB에 저장합니다.

        Args:
            user_id (str): 사용자 ID
            memories (List[Dict]): 저장할 메모리 목록

        Returns:
            bool: 저장 성공 여부
        """
        print(f"INFO:     Storing {len(memories)} memories for user: {user_id}")
        
        # 사용자 ID를 메모리에 추가
        for memory in memories:
            memory["user_id"] = user_id
        
        store_data = {
            "documents": memories,
            "class_name": "agent_memory"
        }
        
        result = self._make_request(
            f"{self.memory_vector_url}/documents",
            method="POST",
            data=store_data,
            api_key=self.memory_api_key
        )
        
        return result.get("success", False) 